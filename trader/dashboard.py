"""The Big Wins phone dashboard: a private, READ-ONLY page of the paper book (BF-D37).

``trader-bf dashboard`` serves one server-rendered page (no JavaScript, no external
files, inline SVG chart, refreshes itself every 60 s) plus its web-app manifest and
icons, so the owner can add it to the phone's home screen. It is reached only through
Tailscale: the compose service publishes port 8080 on the host's loopback
(``127.0.0.1:8080``) and the owner runs ``tailscale serve --bg 8080`` on the host.

Read-only by construction:

* the journal is opened with ``Journal.read_only`` on ``read_only_engine`` (PostgreSQL
  ``default_transaction_read_only``; SQLite ``query_only``): the database refuses any
  write, and this module calls no write method;
* the server answers GET and HEAD only (every other method: 405); there is no form, no
  action and no route that changes anything; it never talks to the broker or Telegram;
* the container mounts the trader's output and the price store read-only and holds only
  the ``db_password`` secret.

Everything shown comes from what the trader already records (``trader/bf_app.py``):
``value:<book>:<day>`` (daily value, L11 stage), ``marks:<day>`` (last marks of held
names), ``rnd:<day>`` (twin percentile among the random twins), ``bt:<day>`` (L15 trend
shield), ``decide:``/``start:`` records, batches, intents and approvals, fills (cost,
days held), the safety rows, ``store-refresh:`` / ``recon:`` records and the scheduler's
job keys. The comparison line is the A200 fund's total return from the price store.
"""

from __future__ import annotations

import gzip
import html
import json
import math
import re
import shutil
import struct
import zlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from functools import cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import pairwise
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, select

from trader.approval import approved_seqs
from trader.constants import ASX_TZ
from trader.journal import Journal, Status, events, safety
from trader.orders import Side

CENT = Decimal("0.01")
MINUS = "\u2212"  # a typographic minus sign
REFRESH_SECONDS = 60
THEME = "#0f6b4f"
IndexProvider = Callable[[], list[tuple[date, float]]]  # (session, total-return level)

STATUS_WORDS = {
    Status.APPROVED: "approved",
    Status.SENDING: "sending",
    Status.SENT: "sent",
    Status.PARTIAL: "part filled",
    Status.FILLED: "filled",
    Status.LAPSED: "lapsed (not approved)",
    Status.VETOED: "vetoed",
    Status.RISK_REJECTED: "stopped by a limit",
    Status.EXPIRED: "not filled (expired)",
    Status.CANCELLED: "cancelled",
    Status.REJECTED: "rejected by the broker",
    Status.NEEDS_REVIEW: "needs review",
}
SAFETY_WORDS = {
    "NORMAL": "All normal",
    "PAUSED": "Paused: no new buys (sells go on)",
    "HALTED_BUYS": "Buys halted by a loss rule (sells go on)",
    "HALTED_LINE": "Halted: no new orders",
    "HALTED_INTEGRITY": "Halted: a check failed, no orders until re-armed",
    "KILLED": "Killed: no new orders",
}
L11_WORDS = (
    "Normal",
    "Stage 1: value below A${review}, checked",
    "Stage 2: value below A${halt}, buys paused to the next decision",
    "Stage 3: value below A${line}, needs your /continue",
)
SCHED_KEY = re.compile(r"^\d{4}-\d{2}-\d{2}:\d{2}:\d{2}:[a-z_]+$")


# ---------------------------------------------------------------- what the page shows


@dataclass(frozen=True)
class Holding:
    code: str
    qty: int
    cost: Decimal | None
    mark: Decimal | None
    mark_day: str | None
    stale: bool  # held but not marked on the latest report day (valued at its last mark)
    days_held: int | None

    @property
    def value(self) -> Decimal | None:
        return None if self.mark is None else (self.mark * self.qty).quantize(CENT)

    @property
    def gain(self) -> Decimal | None:
        v = self.value
        return None if v is None or self.cost is None else (v - self.cost).quantize(CENT)

    @property
    def gain_pct(self) -> float | None:
        g = self.gain
        return None if g is None or not self.cost else float(g / self.cost)


@dataclass(frozen=True)
class OrderRow:
    batch_id: str
    seq: int
    side: str
    qty: int
    code: str
    value: Decimal
    status: str


@dataclass
class View:
    now: datetime
    book: str
    started: bool  # the trader has written at least one daily value or decision
    capital_in: Decimal = Decimal(0)
    cash: Decimal = Decimal(0)
    series: list[tuple[date, Decimal]] = field(default_factory=list)
    index: list[tuple[date, float]] = field(default_factory=list)  # rebased to series start
    index_label: str = "A200"
    index_note: str = "with dividends"
    demo: bool = False
    holdings: list[Holding] = field(default_factory=list)
    next_decision: date | None = None
    last_decision: date | None = None
    orders: list[OrderRow] = field(default_factory=list)
    safety: str = "NORMAL"
    safety_reason: str = ""
    safety_at: datetime | None = None
    l11_stage: int = 0
    l11_text: str = ""
    trend: dict[str, Any] | None = None
    twin_pct: float | None = None
    twin_n: int = 0
    twin_day: str | None = None
    sim_value: Decimal | None = None
    store_day: date | None = None
    store_refreshed_at: datetime | None = None
    report_at: datetime | None = None
    last_job: tuple[str, datetime, str | None] | None = None
    job_errors: int = 0
    recon: tuple[str, bool] | None = None
    disk_free: tuple[int, int] | None = None  # free, total bytes
    notes: list[str] = field(default_factory=list)

    @property
    def value(self) -> Decimal | None:
        return self.series[-1][1] if self.series else None

    @property
    def change_today(self) -> Decimal | None:
        return self.series[-1][1] - self.series[-2][1] if len(self.series) > 1 else None

    @property
    def since_start(self) -> float | None:
        v = self.value
        return float(v / self.capital_in - 1) if v is not None and self.capital_in else None

    @property
    def index_return(self) -> float | None:
        return self.index[-1][1] / self.index[0][1] - 1 if len(self.index) > 1 else None

    @property
    def book_return(self) -> float | None:
        if len(self.series) < 2 or not self.series[0][1]:
            return None
        return float(self.series[-1][1] / self.series[0][1] - 1)


@dataclass(frozen=True)
class Limits:
    review: Decimal = Decimal(7000)
    halt: Decimal = Decimal(6000)
    line: Decimal = Decimal(5000)


@dataclass
class Sources:
    """Where the page reads from. Nothing here can write."""

    journal: Journal
    book: str = "EMG2_18_PAPER"
    sim_book: str = "EMG2_18_SIM"
    limits: Limits = field(default_factory=Limits)
    index: IndexProvider | None = None
    index_label: str = "A200"
    store_root: Path | None = None
    out_dir: Path | None = None
    sessions: Callable[[], Sequence[date]] | None = None
    today: Callable[[], date] = field(default=lambda: datetime.now(ASX_TZ).date())
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(ASX_TZ))
    index_note: str = "with dividends"
    demo: bool = False  # synthetic data (``--demo``): the page says so


def _jobs(j: Journal, prefix: str, newest: int | None = None) -> list[tuple[str, Any, datetime]]:
    """(key, detail, at) of job records with ``prefix``, oldest first."""
    q = (
        select(events.c.ref, events.c.detail, events.c.at)
        .where(events.c.kind == "job", events.c.ref.startswith(prefix, autoescape=True))
        .order_by(events.c.id.desc())
    )
    if newest is not None:
        q = q.limit(newest)
    with j.engine.connect() as c:
        rows = [(str(r[0]), r[1] or {}, _aware(r[2])) for r in c.execute(q)]
    return rows[::-1]


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def _has_journal(j: Journal) -> bool:
    try:
        names = set(inspect(j.engine).get_table_names())
    except Exception:
        return False
    return {"bf_events", "bf_safety", "bf_batches", "bf_fills", "bf_cash"} <= names


def collect(src: Sources) -> View:
    j = src.journal
    v = View(
        now=src.clock(), book=src.book, started=False, index_label=src.index_label,
        index_note=src.index_note, demo=src.demo,
    )  # fmt: skip
    if src.demo:
        v.notes.append("DEMO: synthetic prices from a short simulated run, not your book.")
    v.next_decision = _next_decision(src, j)
    _health_files(src, v)
    if not _has_journal(j):
        v.notes.append("The journal database is not set up yet.")
        return v
    book = src.book
    v.capital_in = sum(
        (Decimal(str(m["amount"])) for m in j.cash_moves_of(book) if m["kind"] == "DEPOSIT"),
        Decimal(0),
    )
    v.cash = j.cash(book)
    v.series = [
        (date.fromisoformat(k.rsplit(":", 1)[1]), Decimal(str(r["value"])))
        for k, r, _ in _jobs(j, f"value:{book}:")
    ]
    v.started = bool(v.series) or bool(j.batches_of(book))
    if v.series:
        last = _jobs(j, f"value:{book}:", 1)[-1]
        v.report_at = last[2]
        stage = int(last[1].get("stage", 0))
        v.l11_stage = stage
        lim = src.limits
        v.l11_text = L11_WORDS[min(stage, 3)].format(
            review=lim.review, halt=lim.halt, line=lim.line
        )
    _index(src, v)
    v.holdings = _holdings(j, book, src.today())
    _orders(j, book, v)
    _safety(j, v)
    _trend_and_twins(j, src, v)
    _health_journal(j, book, v)
    return v


def _holdings(j: Journal, book: str, today: date) -> list[Holding]:
    pos = {e: q for e, q in j.positions(book).items() if q}
    if not pos:
        return []
    cost = j.cost_book(book).cost
    marks = _jobs(j, "marks:")
    latest_day = marks[-1][0].split(":", 1)[1] if marks else None
    last: dict[str, tuple[str, str]] = {}
    for key, rec, _ in marks:
        for e, px in rec.items():
            last[e] = (key.split(":", 1)[1], str(px))
    ids = j.identity_map()
    since: dict[str, date | None] = {}
    held: dict[str, int] = {}
    for f in sorted(j.fills(book), key=lambda f: _aware(f.executed_at)):
        e = ids.get(f.entity, f.entity)
        before = held.get(e, 0)
        held[e] = before + (f.qty if f.side is Side.BUY else -f.qty)
        if before <= 0 < held[e]:
            since[e] = _aware(f.executed_at).astimezone(ASX_TZ).date()
        elif held[e] <= 0:
            since[e] = None
    out = []
    for e, q in sorted(pos.items()):
        m = last.get(e)
        d0 = since.get(e)
        out.append(
            Holding(
                e,
                q,
                cost.get(e, Decimal(0)).quantize(CENT) if e in cost else None,
                Decimal(m[1]) if m else None,
                m[0] if m else None,
                m is None or m[0] != latest_day,
                (today - d0).days if d0 else None,
            )
        )
    return out


def _orders(j: Journal, book: str, v: View) -> None:
    bats = [(bid, j.batch(bid)) for bid, _ in j.batches_of(book)]
    dated = [(b["decision_date"], bid) for bid, b in bats if b is not None]
    # the latest decision proper; a carried re-plan (-X, L7) only when there is no other
    real = [x for x in dated if not x[1].endswith("-X")]
    dated = real or dated
    if not dated:
        return
    v.last_decision = max(d for d, _ in dated)
    for d, bid in sorted(dated):
        if d != v.last_decision:
            continue
        ok = approved_seqs(j, bid)
        for it, st in j.intents_of(bid):
            if st in (Status.PLANNED, Status.RISK_OK, Status.HELD):
                word = "approved" if it.seq in ok else "waiting for approval"
            else:
                word = STATUS_WORDS.get(st, st.lower())
            v.orders.append(
                OrderRow(
                    bid,
                    it.seq,
                    it.side.value,
                    it.qty,
                    it.entity,
                    Decimal(str(it.value_at_ref)).quantize(CENT),
                    word,
                )
            )


def _safety(j: Journal, v: View) -> None:
    q = select(safety).where(safety.c.scope == "").order_by(safety.c.id.desc()).limit(1)
    with j.engine.connect() as c:
        r = c.execute(q).first()
    if r is not None:
        v.safety, v.safety_reason, v.safety_at = str(r.level), str(r.reason), _aware(r.at)


def _trend_and_twins(j: Journal, src: Sources, v: View) -> None:
    bt = _jobs(j, "bt:", 1)
    if bt:
        v.trend = dict(bt[-1][1])
    rnd = _jobs(j, "rnd:", 1)
    if rnd and rnd[-1][0] != "rnd-origin":
        rec = rnd[-1][1]
        v.twin_day = rnd[-1][0].split(":", 1)[1]
        v.twin_pct = float(rec.get("percentile", "nan"))
        v.twin_n = len(rec.get("values", []))
        v.sim_value = Decimal(str(rec["sim"])).quantize(CENT) if "sim" in rec else None
    if v.sim_value is None:  # no random twins: the twin at the last marks
        pos = j.positions(src.sim_book)
        if pos or j.has_cash_moves(src.sim_book):
            last: dict[str, Decimal] = {}
            for _, rec, _ in _jobs(j, "marks:"):
                last.update({e: Decimal(str(px)) for e, px in rec.items()})
            val = j.cash(src.sim_book) + sum(
                (last.get(e, Decimal(0)) * q for e, q in pos.items()), Decimal(0)
            )
            v.sim_value = val.quantize(CENT)


def _health_journal(j: Journal, book: str, v: View) -> None:
    sr = _jobs(j, "store-refresh:", 1)
    if sr:
        v.store_refreshed_at = sr[-1][2]
    rc = _jobs(j, f"recon:{book}:", 1)
    if rc:
        v.recon = (rc[-1][0].rsplit(":", 1)[1], bool(rc[-1][1].get("ok")))
    q = (
        select(events.c.ref, events.c.detail, events.c.at)
        .where(events.c.kind == "job", events.c.ref.like("____-__-__:__:__:%"))
        .order_by(events.c.id.desc())
        .limit(200)
    )
    with j.engine.connect() as c:
        rows = [(str(r[0]), r[1] or {}, _aware(r[2])) for r in c.execute(q)]
    rows = [r for r in rows if SCHED_KEY.match(r[0])]
    if rows:
        key, det, at = rows[0]
        v.last_job = (key, at, det.get("error") if isinstance(det, dict) else None)
        week = v.now.astimezone(UTC).timestamp() - 7 * 86400
        v.job_errors = sum(
            1 for _, d, t in rows if isinstance(d, dict) and d.get("error") and t.timestamp() > week
        )


def _health_files(src: Sources, v: View) -> None:
    if src.store_root is not None:
        days = []
        for f in (src.store_root / "raw" / "bulk_eod").glob("AU_*.json.gz"):
            try:
                days.append(date.fromisoformat(f.name[3:13]))
            except ValueError:
                continue
        v.store_day = max(days, default=None)
    for d in (src.out_dir, src.store_root, Path("/")):
        if d is not None and d.exists():
            du = shutil.disk_usage(d)
            v.disk_free = (du.free, du.total)
            break


def _index(src: Sources, v: View) -> None:
    if src.index is None or not v.series:
        return
    try:
        lv = src.index()
    except Exception as e:
        v.notes.append(f"{src.index_label} line unavailable: {type(e).__name__}")
        return
    d0, d1 = v.series[0][0], v.series[-1][0]
    pts = [(d, x) for d, x in lv if d0 <= d <= d1 and x > 0]
    if len(pts) > 1:
        v.index = pts


def _next_decision(src: Sources, j: Journal) -> date | None:
    """The next month-end decision (the scheduler's 22:20 ``decide`` on an ASX session
    whose next session is in another month), today included until it is done."""
    if src.sessions is None:
        return None
    sess = sorted(src.sessions())
    today = src.today()
    done: set[str] = set()
    starts: list[date] = []
    if _has_journal(j):
        done = {k.rsplit(":", 1)[1] for k, _, _ in _jobs(j, f"decide:{src.book}:")}
        starts = [date.fromisoformat(k.rsplit(":", 1)[1]) for k, _, _ in _jobs(j, "start:")]
    for a, b in pairwise(sess):
        if a < today or b.month == a.month or str(a) in done:
            continue
        if any(s < a and (s.year, s.month) == (a.year, a.month) for s in starts):
            continue  # L6: the start month's month-end is skipped for the broker book
        return a
    return None


# ---------------------------------------------------------------- the A200 line


def store_index(root: Path, code: str) -> IndexProvider:
    """Total-return level of ``code`` (close plus dividends, splits neutral) from the
    price store, read-only; cached until a new bulk file arrives."""
    from trader.data.forward_store import ForwardStore, parse_split, symbol_returns

    memo: dict[str, list[tuple[date, float]]] = {}

    def level() -> list[tuple[date, float]]:
        bulk = root / "raw" / "bulk_eod"
        stamp = max((p.name for p in bulk.glob("AU_*.json.gz")), default="")
        if stamp in memo:
            return memo[stamp]
        fs = ForwardStore(root)
        sym = f"{code}.AU"
        rows: list[dict[str, Any]] = list(fs._events("eod", sym))
        last = str(rows[-1]["date"])[:10] if rows else ""
        for p in sorted(bulk.glob("AU_*.json.gz")):
            if p.name[3:13] > last:
                with gzip.open(p, "rt", encoding="utf-8") as f:
                    rows += [r for r in json.load(f) or [] if r.get("code") == code]
        rows.sort(key=lambda r: str(r["date"])[:10])
        spl = [(date.fromisoformat(x["date"][:10]), parse_split(x["split"]))
               for x in fs._events("splits", sym)]  # fmt: skip
        dv = []
        for x in fs._events("div", sym):
            try:
                dv.append((date.fromisoformat(x["date"][:10]), float(x.get("value") or 0)))
            except (TypeError, ValueError):
                continue
        days, _, _, _, ret = symbol_returns(rows, spl, dv)
        out: list[tuple[date, float]] = []
        lvl = 1.0
        for d, r in zip(days, ret, strict=True):
            if out and math.isfinite(r):
                lvl *= 1 + r
            out.append((d, lvl))
        memo.clear()
        memo[stamp] = out
        return out

    return level


# ---------------------------------------------------------------- rendering


def _e(x: object) -> str:
    return html.escape(str(x), quote=True)


def _aud(x: Decimal | None, sign: bool = False) -> str:
    if x is None:
        return "-"
    q = x.quantize(CENT)
    s = f"{abs(q):,.2f}"
    if sign:
        return ("+" if q >= 0 else MINUS) + "A$" + s
    return (MINUS if q < 0 else "") + "A$" + s


def _pct(x: float | None, sign: bool = True) -> str:
    if x is None or not math.isfinite(x):
        return "-"
    s = f"{abs(x) * 100:.1f}%"
    return (("+" if x >= 0 else MINUS) + s) if sign else s


def _tone(x: float | Decimal | None) -> str:
    if x is None:
        return ""
    return "up" if x > 0 else ("down" if x < 0 else "")


def _when(t: datetime | None) -> str:
    return "-" if t is None else t.astimezone(ASX_TZ).strftime("%a %d %b %H:%M")


def _chart(v: View) -> str:
    """Account value vs the index, both rebased to 100 at the book's first value."""
    if len(v.series) < 2:
        return '<p class="muted">The chart starts after the second trading day.</p>'
    w, h, pl, pr, pt, pb = 340, 190, 34, 8, 10, 22
    base = float(v.series[0][1])
    book = [(d, float(x) / base * 100) for d, x in v.series]
    idx = [(d, x / v.index[0][1] * 100) for d, x in v.index] if v.index else []
    allv = [y for _, y in book + idx]
    lo, hi = min(allv), max(allv)
    pad = max((hi - lo) * 0.1, 0.5)
    lo, hi = lo - pad, hi + pad
    d0, d1 = book[0][0], book[-1][0]
    span = max((d1 - d0).days, 1)

    def x(d: date) -> float:
        return pl + (d - d0).days / span * (w - pl - pr)

    def y(val: float) -> float:
        return pt + (hi - val) / (hi - lo) * (h - pt - pb)

    def path(pts: list[tuple[date, float]]) -> str:
        return " ".join(f"{'M' if i == 0 else 'L'}{x(d):.1f},{y(val):.1f}"
                        for i, (d, val) in enumerate(pts))  # fmt: skip

    grid = []
    for k in range(4):
        val = lo + (hi - lo) * (k + 0.5) / 4
        grid.append(
            f'<line x1="{pl}" x2="{w - pr}" y1="{y(val):.1f}" y2="{y(val):.1f}" class="grid"/>'
            f'<text x="{pl - 4}" y="{y(val) + 3:.1f}" class="ax" text-anchor="end">'
            f"{val:.0f}</text>"
        )
    y100 = y(100.0)
    lines = [
        f'<line x1="{pl}" x2="{w - pr}" y1="{y100:.1f}" y2="{y100:.1f}" class="base"/>',
        f'<path d="{path(idx)}" class="s2"/>' if idx else "",
        f'<path d="{path(book)}" class="s1"/>',
        f'<circle cx="{x(book[-1][0]):.1f}" cy="{y(book[-1][1]):.1f}" r="4" class="d1"/>',
    ]
    labels = (
        f'<text x="{pl}" y="{h - 6}" class="ax">{d0:%d %b %y}</text>'
        f'<text x="{w - pr}" y="{h - 6}" class="ax" text-anchor="end">{d1:%d %b %y}</text>'
    )
    legend = '<span class="key k1"></span>Paper book'
    if idx:
        legend += f' <span class="key k2"></span>{_e(v.index_label)} ({_e(v.index_note)})'
    title = f"Paper book vs {v.index_label}, both = 100 at the start"
    return (
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{_e(title)}" class="chart">'
        f"<title>{_e(title)}</title>{''.join(grid)}{''.join(lines)}{labels}</svg>"
        f'<p class="legend">{legend}</p>'
    )


def _tile(label: str, value: str, sub: str = "", tone: str = "") -> str:
    return (
        f'<div class="tile"><div class="tl">{_e(label)}</div>'
        f'<div class="tv {tone}">{_e(value)}</div>'
        + (f'<div class="ts">{_e(sub)}</div>' if sub else "")
        + "</div>"
    )


def _section(title: str, body: str) -> str:
    return f"<section><h2>{_e(title)}</h2>{body}</section>"


def render(v: View) -> str:
    parts = [_header(v)]
    if not v.started:
        parts.append(
            _section(
                "Waiting for the first trading day",
                "<p>The trader has not made its first decision yet, so there is nothing to "
                "show. This page fills in by itself after the first trading evening "
                "(the daily report at 22:45 Sydney).</p>"
                + (
                    f"<p>Next decision: <b>{v.next_decision:%A %d %B %Y}</b> (22:20).</p>"
                    if v.next_decision
                    else ""
                ),
            )
        )
        parts += [_safety_html(v), _health_html(v)]
    else:
        parts += [_value_html(v), _holdings_html(v), _decision_html(v)]
        parts += [_safety_html(v), _health_html(v)]
    parts.append(
        "<footer>PAPER - no real money. Not shown to beat the index. Read-only page: "
        "approvals and commands are in Telegram.</footer>"
    )
    return _page("".join(parts))


def _header(v: View) -> str:
    return (
        '<header><div class="brand"><span class="logo">BW</span>Big Wins</div>'
        f'<div class="badge">{"DEMO" if v.demo else "PAPER"}</div></header>'
        f'<p class="muted small">{_e(v.book)} · '
        f"updated {_when(v.now)} · refreshes every minute</p>"
        + "".join(f'<p class="note">{_e(n)}</p>' for n in v.notes)
    )


def _value_html(v: View) -> str:
    val = v.value
    ct = v.change_today
    prev = v.series[-2][1] if len(v.series) > 1 else None
    ct_pct = float(ct / prev) if ct is not None and prev else None
    since = val - v.capital_in if val is not None and v.capital_in else None
    vs = (
        v.book_return - v.index_return
        if v.book_return is not None and v.index_return is not None
        else None
    )
    day = f"on {v.series[-1][0]:%d %b}" if v.series else ""
    tiles = (
        _tile("Account value", _aud(val), day)
        + _tile("Today", _aud(ct, True), _pct(ct_pct), _tone(ct))
        + _tile("Since start", _aud(since, True), _pct(v.since_start), _tone(since))
        + _tile(
            f"vs {v.index_label}",
            _pct(vs) if vs is not None else "-",
            f"{v.index_label} {_pct(v.index_return)} since the book's first day"
            if v.index_return is not None
            else "index line not available",
            _tone(vs),
        )
    )
    return _section(
        "Account",
        f'<div class="tiles">{tiles}</div>{_chart(v)}'
        f'<p class="muted small">Cash {_aud(v.cash)} · money in {_aud(v.capital_in)}</p>',
    )


def _holdings_html(v: View) -> str:
    if not v.holdings:
        return _section("Holdings", '<p class="muted">No shares held (all cash).</p>')
    rows = []
    for h in v.holdings:
        flag = ' <span class="warn" title="no price today">⚠ old price</span>' if h.stale else ""
        mark = f"{h.mark}" if h.mark is not None else "no price"
        rows.append(
            f"<tr><td><b>{_e(h.code)}</b>{flag}<div class='sub'>{h.qty} @ {_e(mark)}"
            + (f" ({_e(h.mark_day)})" if h.stale and h.mark_day else "")
            + f"</div></td><td class='r'>{_aud(h.value)}<div class='sub'>cost {_aud(h.cost)}"
            f"</div></td><td class='r {_tone(h.gain)}'>{_aud(h.gain, True)}"
            f"<div class='sub'>{_pct(h.gain_pct)}</div></td>"
            f"<td class='r'>{h.days_held if h.days_held is not None else '-'}</td></tr>"
        )
    stale = sum(1 for h in v.holdings if h.stale)
    note = (
        f'<p class="warn small">⚠ {stale} share(s) had no price on the last report day; '
        "valued at their last price (the report flags them too).</p>"
        if stale
        else ""
    )
    return _section(
        f"Holdings ({len(v.holdings)})",
        '<table><thead><tr><th>Share</th><th class="r">Value</th><th class="r">Gain</th>'
        f'<th class="r">Days</th></tr></thead><tbody>{"".join(rows)}</tbody></table>{note}',
    )


def _decision_html(v: View) -> str:
    nd = (
        f"<p>Next decision: <b>{v.next_decision:%A %d %B %Y}</b>, 22:20 Sydney "
        "(orders go the next trading day, after your approval by 15:20).</p>"
        if v.next_decision
        else ""
    )
    if not v.orders:
        return _section("Decisions", nd + '<p class="muted">No orders yet.</p>')
    counts: dict[str, int] = {}
    for o in v.orders:
        counts[o.status] = counts.get(o.status, 0) + 1
    summary = ", ".join(f"{n} {s}" for s, n in sorted(counts.items()))
    rows = "".join(
        f"<tr><td>{o.seq}</td><td class='{'buy' if o.side == 'BUY' else 'sell'}'>"
        f"{_e(o.side.lower())}</td><td><b>{_e(o.code)}</b><div class='sub'>{o.qty} · "
        f"~{_aud(o.value)}</div></td><td>{_e(o.status)}</td></tr>"
        for o in v.orders
    )
    batches = sorted({o.batch_id for o in v.orders})
    return _section(
        "Decisions",
        nd + f"<p>Last decision <b>{v.last_decision:%d %b %Y}</b>: {_e(summary)}.</p>"
        f'<p class="muted small">{_e(", ".join(batches))}</p>'
        f"<table><tbody>{rows}</tbody></table>",
    )


def _safety_html(v: View) -> str:
    lvl = v.safety
    tone = (
        "ok" if lvl == "NORMAL" else ("bad" if lvl in ("KILLED", "HALTED_INTEGRITY") else "amber")
    )
    items = [
        f'<li><span class="pill {tone}">{_e(lvl)}</span> {_e(SAFETY_WORDS.get(lvl, lvl))}'
        + (
            f'<div class="sub">{_e(v.safety_reason)} · {_when(v.safety_at)}</div>'
            if v.safety_at
            else ""
        )
        + "</li>"
    ]
    if v.started:
        items.append(f"<li>Loss rule (L11): <b>{_e(v.l11_text or 'Normal')}</b></li>")
    t = v.trend
    if t:
        state = str(t.get("state", "?"))
        what = "shares (EMG2-18)" if state == "EMG2" else "the A200 fund"
        rel = "at or above" if state == "EMG2" else "below"
        forced = (
            f" - FORCED for the paper dry run (rule said {t['forced_from']})"
            if t.get("forced_from")
            else ""
        )
        try:
            detail = (
                f"band index {float(t['level']):.3f} {rel} its {len(t.get('levels', []))}-month "
                f"average {float(t['mean']):.3f} ({t.get('as_of', '')})"
            )
        except (KeyError, TypeError, ValueError):
            detail = str(t.get("as_of", ""))
        items.append(
            f"<li>Trend shield (L15): <b>{_e(state)}</b>, holding {what}{_e(forced)}"
            f'<div class="sub">{_e(detail)}</div></li>'
        )
    else:
        items.append("<li>Trend shield (L15): not decided yet</li>")
    if v.twin_pct is not None:
        warn = " ⚠ below 10" if v.twin_pct < 10 else ""
        items.append(
            f"<li>Twin vs {v.twin_n} random twins: <b>{v.twin_pct:.0f}th percentile</b>{warn}"
            f'<div class="sub">L11 test (b) needs ≥ 10 · {_e(v.twin_day)}</div></li>'
        )
    if v.sim_value is not None:
        items.append(f"<li>Simulated twin value: <b>{_aud(v.sim_value)}</b></li>")
    return _section("Safety", f'<ul class="list">{"".join(items)}</ul>')


def _health_html(v: View) -> str:
    def gb(n: int) -> str:
        return f"{n / 1e9:.1f} GB"

    items = []
    items.append(
        "<li>Price store: "
        + (f"<b>{v.store_day:%a %d %b}</b>" if v.store_day else "<b>-</b>")
        + (f" · refreshed {_when(v.store_refreshed_at)}" if v.store_refreshed_at else "")
        + "</li>"
    )
    items.append(f"<li>Last daily report: <b>{_when(v.report_at)}</b></li>")
    if v.recon:
        ok = "reconciled to the cent" if v.recon[1] else "BREAK - see Telegram"
        items.append(f"<li>Broker check {_e(v.recon[0])}: <b>{ok}</b></li>")
    if v.last_job:
        key, at, err = v.last_job
        name = key.rsplit(":", 1)[1]
        items.append(
            f"<li>Last scheduled job: <b>{_e(name)}</b> {_when(at)}"
            + (f' <span class="warn">failed: {_e(str(err)[:80])}</span>' if err else "")
            + "</li>"
        )
    if v.job_errors:
        items.append(f'<li class="warn">{v.job_errors} job error(s) in the last 7 days</li>')
    items.append("<li>Heartbeat: not journaled yet (dead-man check is a later step)</li>")
    if v.disk_free:
        free, total = v.disk_free
        tone = "warn" if free < 0.1 * total else ""
        items.append(f'<li class="{tone}">Disk free: <b>{gb(free)}</b> of {gb(total)}</li>')
    return _section("Health", f'<ul class="list">{"".join(items)}</ul>')


CSS = """
:root{color-scheme:light;--bg:#f6f6f3;--card:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;
--line:#e2e1dc;--s1:#2a78d6;--s2:#eb6834;--up:#0a7a3e;--down:#c0352f;--amber:#9a6500;
--ok-bg:#e3f3e8;--amber-bg:#fbeed3;--bad-bg:#fbe1df;--brand:#0f6b4f}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#111110;--card:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--line:#33332f;--s1:#3987e5;--s2:#d95926;--up:#4cc27a;
--down:#f07a72;--amber:#e0a63a;--ok-bg:#16301f;--amber-bg:#3a2c10;--bad-bg:#3d1714;
--brand:#2fa57c}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.4 system-ui,-apple-system,
"Segoe UI",Roboto,sans-serif;padding:12px 16px 32px;max-width:640px;margin-inline:auto}
header{display:flex;justify-content:space-between;align-items:center}
.brand{font-weight:700;font-size:20px;display:flex;align-items:center;gap:8px}
.logo{background:var(--brand);color:#fff;border-radius:8px;font-size:13px;padding:5px 6px}
.badge{border:1px solid var(--amber);color:var(--amber);border-radius:6px;font-size:12px;
font-weight:700;padding:2px 8px}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:12px 14px;margin:12px 0}
h2{font-size:15px;margin:0 0 8px;color:var(--ink2);font-weight:600}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px}
.tile{border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.tl{font-size:12px;color:var(--ink2)}.tv{font-size:20px;font-weight:700}
.ts{font-size:12px;color:var(--ink2)}
.up{color:var(--up)}.down{color:var(--down)}.warn{color:var(--amber)}
.muted{color:var(--ink2)}.small,.sub{font-size:12px}.sub{color:var(--ink2)}
.chart{width:100%;height:auto;display:block}
.grid{stroke:var(--line);stroke-width:1}.base{stroke:var(--ink2);stroke-width:1;
stroke-dasharray:3 3;opacity:.6}.ax{fill:var(--ink2);font-size:10px}
.s1{fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round}
.s2{fill:none;stroke:var(--s2);stroke-width:2;stroke-linejoin:round}
.d1{fill:var(--s1);stroke:var(--card);stroke-width:2}
.legend{font-size:12px;color:var(--ink2);margin:4px 0}
.key{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;
margin:0 4px 0 6px}.k1{background:var(--s1)}.k2{background:var(--s2)}
table{width:100%;border-collapse:collapse}td,th{padding:6px 4px;border-top:1px solid
var(--line);vertical-align:top;text-align:left}th{font-size:12px;color:var(--ink2);
font-weight:600;border-top:0}.r{text-align:right}
.buy{color:var(--up)}.sell{color:var(--down)}
.list{list-style:none;padding:0;margin:0}.list li{padding:6px 0;border-top:1px solid
var(--line)}.list li:first-child{border-top:0}
.pill{font-size:12px;font-weight:700;border-radius:6px;padding:1px 6px}
.ok{background:var(--ok-bg);color:var(--up)}.amber{background:var(--amber-bg);
color:var(--amber)}.bad{background:var(--bad-bg);color:var(--down)}
.note{background:var(--amber-bg);border-radius:8px;padding:6px 10px;font-size:13px}
footer{font-size:12px;color:var(--ink2);text-align:center;margin-top:16px}
"""


def _page(body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f'<meta http-equiv="refresh" content="{REFRESH_SECONDS}">'
        f'<meta name="theme-color" content="{THEME}">'
        '<meta name="color-scheme" content="light dark">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-title" content="Big Wins">'
        '<link rel="manifest" href="manifest.webmanifest">'
        '<link rel="icon" href="icon.svg" type="image/svg+xml">'
        '<link rel="apple-touch-icon" href="icon-192.png">'
        f"<title>Big Wins</title><style>{CSS}</style></head><body>{body}</body></html>"
    )


# ---------------------------------------------------------------- app icon and manifest

ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
    f'<rect width="512" height="512" rx="96" fill="{THEME}"/>'
    '<polyline points="96,370 200,270 280,320 416,160" fill="none" stroke="#fff" '
    'stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="416" cy="160" r="34" fill="#f5c542"/></svg>'
)

MANIFEST = {
    "name": "Big Wins",
    "short_name": "Big Wins",
    "description": "The Big Wins paper book (read-only)",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": THEME,
    "theme_color": THEME,
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"},
    ],
}


def _seg_dist(px: float, py: float, a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


@cache
def icon_png(size: int) -> bytes:
    """The app icon as a PNG (drawn here, no image files in the repository): the
    brand square with a rising line, as ``ICON_SVG``."""
    s = size / 512
    pts = [(96 * s, 370 * s), (200 * s, 270 * s), (280 * s, 320 * s), (416 * s, 160 * s)]
    half = 22 * s
    dot, dot_r = (416 * s, 160 * s), 34 * s
    bg = bytes.fromhex(THEME[1:])
    raw = bytearray()
    for yy in range(size):
        raw.append(0)
        for xx in range(size):
            px, py = xx + 0.5, yy + 0.5
            if math.hypot(px - dot[0], py - dot[1]) <= dot_r:
                raw += b"\xf5\xc5\x42"
            elif min(_seg_dist(px, py, a, b) for a, b in pairwise(pts)) <= half:
                raw += b"\xff\xff\xff"
            else:
                raw += bg

    def chunk(kind: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


# ---------------------------------------------------------------- HTTP (GET/HEAD only)

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
        "manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
}
READ_METHODS = frozenset({"GET", "HEAD"})


@dataclass
class Dashboard:
    """The whole web app: ``respond`` maps a request to (status, headers, body)."""

    sources: Sources
    allowed_logins: frozenset[str] = frozenset()  # Tailscale log-ins; empty = any

    def routes(self) -> dict[str, Callable[[], tuple[str, bytes]]]:
        return {
            "/": lambda: ("text/html; charset=utf-8", render(collect(self.sources)).encode()),
            "/healthz": lambda: ("text/plain; charset=utf-8", b"ok\n"),
            "/manifest.webmanifest": lambda: (
                "application/manifest+json",
                json.dumps(MANIFEST).encode(),
            ),
            "/icon.svg": lambda: ("image/svg+xml", ICON_SVG.encode()),
            "/icon-192.png": lambda: ("image/png", icon_png(192)),
            "/icon-512.png": lambda: ("image/png", icon_png(512)),
        }

    def respond(
        self, method: str, path: str, headers: Mapping[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs = dict(SECURITY_HEADERS)
        if method not in READ_METHODS:
            hdrs["Allow"] = "GET, HEAD"
            return 405, hdrs, b"read-only\n"
        path = path.split("?", 1)[0].split("#", 1)[0] or "/"
        if self.allowed_logins and path != "/healthz":
            who = next((v for k, v in headers.items() if k.lower() == "tailscale-user-login"), "")
            if who.strip().lower() not in self.allowed_logins:
                return 403, hdrs, b"not allowed\n"
        route = self.routes().get(path)
        if route is None:
            return 404, hdrs, b"not found\n"
        ctype, body = route()
        hdrs["Content-Type"] = ctype
        return 200, hdrs, body


def make_handler(app: Dashboard) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "BigWins"
        sys_version = ""

        def _go(self) -> None:
            status, hdrs, body = app.respond(self.command, self.path, dict(self.headers))
            self.send_response(status)
            for k, val in hdrs.items():
                self.send_header(k, val)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _go  # noqa: N815

        def log_message(self, format: str, *args: Any) -> None:
            return  # no request log (keeps the owner's tailnet log-ins out of docker logs)

    return Handler


def serve(app: Dashboard, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(app))
