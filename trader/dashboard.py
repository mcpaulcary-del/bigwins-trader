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
import json
import math
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import pairwise
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, select

from trader import app_pages, webui
from trader.app_pages import Extras
from trader.app_sign import sign_proxy
from trader.approval import approved_seqs
from trader.constants import ASX_TZ
from trader.journal import Journal, Status, events, safety
from trader.orders import Side

CENT = Decimal("0.01")
MINUS = "\u2212"  # a typographic minus sign
REFRESH_SECONDS = 60
THEME = webui.THEME
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
    "Stage 1: value below ${review}, checked",
    "Stage 2: value below ${halt}, buys paused to the next decision",
    "Stage 3: value below ${line}, needs your /continue",
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
    live: bool = False  # BF-D50
    limits: Any = None  # BF-D62: the L11 thresholds (loss-rule meter)
    journal: Any = None  # BF-D62: read-only, for the chart's trade dots
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
    live: bool = False  # BF-D50: from the config's broker mode (always paper in this build)
    approval_deadline: str = "15:20"
    tax_params: Any = None  # trader.tax_report.TaxParams (BF-D44); None = the defaults
    marginal_rate: Decimal | None = None  # tax.marginal_rate (BF-D44), set on the server only
    prior_losses: Decimal = Decimal(0)  # BF-D51: tax.prior_losses_aud
    amit_csv: Path | None = None  # BF-D51: tax.amit_csv
    prices: Callable[[str], Sequence[tuple[date, float]]] | None = None  # BF-D66: closes
    tr_prices: Callable[[str], Sequence[tuple[date, float]]] | None = None  # BF-D72: TR level
    forecast_dir: Path | None = None  # BF-D66: where config/forecast_bands*.csv live
    # BF-D75..BF-D80: scoreboard, costs, research, Health, digest, announcements
    fixed_items: dict[str, Decimal] | None = None  # running_costs (server, data, other)
    fixed_total: Decimal = Decimal(600)  # costs.fixed_aud_per_year
    half_spread: Decimal = Decimal("0.005")  # data.sim_half_spread (the modelled spread)
    fund_half_spread: Decimal = Decimal("0.0005")  # band_trend.fund_half_spread
    commission: Callable[[Decimal], Decimal] | None = None  # the IBKR plan (A200's one buy)
    scorecard: Path | None = None  # the research record's scorecard_latest.csv (read-only)
    info_dir: Path | None = None  # the private info archive (read-only)
    info_enabled: bool = False
    eodhd_budget: int = 100000
    presence_days: int = 14  # BF-D82: app.presence_days
    presence_warn_days: int = 10


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
        index_note=src.index_note, demo=src.demo, live=src.live,
        limits=src.limits, journal=src.journal,
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


def store_prices(root: Path) -> Callable[[str], list[tuple[date, float]]]:
    """BF-D66: one share's closes from the price store (split-adjusted to the last row),
    read-only; the share screens' price history and actual path."""
    from trader.data.forward_store import (
        ForwardStore,
        adjusted_to_last,
        parse_split,
        symbol_returns,
    )

    memo: dict[tuple[str, str], list[tuple[date, float]]] = {}

    def prices(code: str) -> list[tuple[date, float]]:
        bulk = root / "raw" / "bulk_eod"
        stamp = max((p.name for p in bulk.glob("AU_*.json.gz")), default="")
        if (code, stamp) in memo:
            return memo[(code, stamp)]
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
        days, close, _, split, _ = symbol_returns(rows, spl, [])
        adj = adjusted_to_last(close, split)
        out = [(d, c) for d, c in zip(days, adj, strict=True) if math.isfinite(c) and c > 0]
        if len(memo) > 64:
            memo.clear()
        memo[(code, stamp)] = out
        return out

    return prices


def store_tr(root: Path) -> Callable[[str], list[tuple[date, float]]]:
    """BF-D72 (strategy review L2): one share's total-return level (dividends added back,
    splits neutral) from the price store, read-only."""
    level = store_index  # the same total-return chain, per code

    memo: dict[str, IndexProvider] = {}

    def tr(code: str) -> list[tuple[date, float]]:
        if code not in memo:
            if len(memo) > 64:
                memo.clear()
            memo[code] = level(root, code)
        return list(memo[code]())

    return tr


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


def render(v: View, x: Extras | None = None) -> str:
    """The Home screen (BF-D43; ``--snapshot`` writes it)."""
    return app_pages.home(v, x or Extras())


# ---------------------------------------------------------------- app icon and manifest

# The app icon ("W" for Wins, midnight and mint). PNGs are pre-rendered from this SVG
# into trader/assets/ (anti-aliased; maskable and apple-touch variants are full-bleed).
ICON_BG = "#0f172a"
ASSETS = Path(__file__).resolve().parent / "assets"
ICON_SVG = (ASSETS / "icon.svg").read_text(encoding="utf-8")

MANIFEST = {
    "name": "Big Wins",
    "short_name": "Big Wins",
    "description": "The Big Wins paper book: view, approve, alerts",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "background_color": "#0b1220",  # BF-D73: the dark page background (splash)
    "theme_color": ICON_BG,
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {
            "src": "/icon-maskable-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable",
        },
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"},
    ],
}


@cache
def icon_png(size: int) -> bytes:
    """The app icon as a PNG at 192 or 512 px, pre-rendered from ``ICON_SVG``."""
    return (ASSETS / f"icon-{size}.png").read_bytes()


@cache
def asset_png(name: str) -> bytes:
    """A pre-rendered icon variant from trader/assets (maskable, apple-touch)."""
    return (ASSETS / name).read_bytes()


# ---------------------------------------------------------------- HTTP

READ_METHODS = frozenset({"GET", "HEAD"})
ActionsFn = Callable[[str, str, Mapping[str, str], bytes], tuple[int, dict[str, str], bytes]]
FORWARD_IN = ("tailscale-user-login", "tailscale-user-name", "cookie", "content-type",
              "origin", "sec-fetch-site", "sec-fetch-mode", "x-csrf-token")  # fmt: skip
FORWARD_OUT = ("content-type", "set-cookie", "cache-control", "content-security-policy")


def forward_headers(
    headers: Mapping[str, str], method: str, path: str, body: bytes, key: bytes | None
) -> dict[str, str]:
    """The headers passed on to the trader: the browser's cookie, content type and CSRF
    token; with ``key``, the log-in, Origin, Sec-Fetch-Site and the host the browser asked
    for (``X-Forwarded-Host`` from tailscale serve, else ``Host``), signed (BF-D46/D55)."""

    def hv(name: str) -> str:
        return next((v for k, v in headers.items() if k.lower() == name), "")

    fwd = {k: v for k, v in headers.items() if k.lower() in FORWARD_IN}
    if key is None:  # unsigned (development only): the host for the Origin check
        if hv("host"):
            fwd["X-Forwarded-Host"] = hv("host")
        return fwd
    fwd = {k: v for k, v in fwd.items() if k.lower() != "tailscale-user-login"}
    fwd.update(sign_proxy(key, hv("tailscale-user-login").strip().lower(), hv("origin"),
                          hv("sec-fetch-site"), method, path, body,
                          host=hv("x-forwarded-host") or hv("host")))  # fmt: skip
    return fwd


def signed_local(actions: ActionsFn, key: bytes) -> ActionsFn:
    """The demo: the same signed forwarding, to an in-process control server."""

    def forward(
        method: str, path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, str], bytes]:
        return actions(method, path, forward_headers(headers, method, path, body, key), body)

    return forward


def proxy_to(base: str, key: bytes | None = None, timeout: float = 70.0) -> ActionsFn:
    """BF-D39 / BF-D46: forward ``/act/...`` to the trader's control server (which checks
    the log-in, the form token and the code itself). With ``key`` (``app_proxy_key``) the
    viewer's log-in, Origin and Sec-Fetch-Site are signed with the method, path and body;
    the trader accepts nothing unsigned. The log-in passed on is the one ``respond``
    accepted (from the trusted proxy address only)."""

    def forward(
        method: str, path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, str], bytes]:
        fwd = forward_headers(headers, method, path, body, key)
        req = urllib.request.Request(  # noqa: S310 - the fixed private control address
            base.rstrip("/") + path, data=body if method == "POST" else None, method=method,
            headers=fwd,
        )  # fmt: skip
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
                status, hdrs, out = r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            status, hdrs, out = e.code, dict(e.headers), e.read()
            e.close()
        except OSError:
            body_html = webui.page("Trader not reachable", webui.section(
                "Actions unavailable",
                "<p>The trader is not running or not reachable, so actions are unavailable "
                "right now. Viewing still works. If it persists, check the Server tab or "
                "run <code>bigwins</code> on the server.</p>",
            ), refresh=False)  # fmt: skip
            h = dict(webui.SECURITY_HEADERS)
            h["Content-Type"] = "text/html; charset=utf-8"
            return 502, h, body_html.encode()
        keep = {k: v for k, v in hdrs.items() if k.lower() in FORWARD_OUT}
        return int(status), {**webui.SECURITY_HEADERS, **keep}, out

    return forward


def _static(ctype: str, text: str) -> Callable[[], tuple[str, bytes]]:
    data = text.encode()
    return lambda: (ctype, data)


@dataclass
class Dashboard:
    """The whole web app: ``respond`` maps a request to (status, headers, body).

    Its own screens are read-only (GET/HEAD; the journal session refuses writes).
    ``/act/...`` goes to ``actions``: the trader's control server (``proxy_to``) or, in
    ``--demo``, an in-process simulated one; None = actions unavailable."""

    sources: Sources
    allowed_logins: frozenset[str] = frozenset()  # Tailscale log-ins that may VIEW; empty = any
    actions: ActionsFn | None = None
    action_logins: frozenset[str] = frozenset()  # app.allowed_logins: may ACT (shown only)
    channel: str = "app"
    version: str = "paper"
    checklist: Callable[[], list[tuple[str, bool | None]]] = field(default=lambda: [])
    update_mode: str = "immediate"  # BF-D45 strategy.update_mode
    changelog: Callable[[], list[dict[str, Any]]] = field(default=lambda: [])
    # BF-D46: the only source address whose Tailscale-User-Login header is believed (the
    # gateway of the `dashboard` network, where the host's published port arrives from);
    # empty = believe any (tests, local development)
    trusted_peers: frozenset[str] = frozenset()
    live: bool = False  # BF-D50
    # BF-D63: read-only facts for the Setup & IBKR checklist (e.g. the account id's form)
    setup_facts: Callable[[], dict[str, Any]] = field(default=lambda: {})

    def routes(self) -> dict[str, Callable[[], tuple[str, bytes]]]:
        """The fixed routes (screens with a path argument are matched in ``respond``)."""
        out: dict[str, Callable[[], tuple[str, bytes]]] = {
            "/healthz": lambda: ("text/plain; charset=utf-8", b"ok\n"),
            "/manifest.webmanifest": lambda: (
                "application/manifest+json",
                json.dumps(MANIFEST).encode(),
            ),
            "/icon.svg": lambda: ("image/svg+xml", ICON_SVG.encode()),
            "/icon-192.png": lambda: ("image/png", icon_png(192)),
            "/icon-512.png": lambda: ("image/png", icon_png(512)),
            "/icon-maskable-512.png": lambda: ("image/png", asset_png("icon-maskable-512.png")),
            "/apple-touch-icon.png": lambda: ("image/png", asset_png("apple-touch-icon.png")),
        }
        for path, (ctype, text) in webui.STATIC.items():
            out[path] = _static(ctype, text)
        return out

    SCREENS = ("/", "/holdings", "/orders", "/inbox", "/server", "/settings", "/tax", "/tax.csv",
               "/strategy", "/setup", "/backups", "/accounts", "/shares",
               "/forecast-method", "/calendar", "/compare", "/search.json",
               "/health", "/costs", "/digest")  # fmt: skip

    def share_ctx(self, v: View) -> Any:
        """BF-D66: what the share screens read (read-only)."""
        from trader import forecast, share_pages

        src = self.sources
        return share_pages.ShareCtx(
            src.journal, src.book, v.now, src.sessions() if src.sessions else (),
            src.prices, src.index, src.index_label,  # type: ignore[arg-type]
            {k: forecast.load_bands(src.forecast_dir, k) for k in forecast.BENCH}, src.demo,
            src.tr_prices,  # type: ignore[arg-type]
            self.names(v), src.info_dir,
        )  # fmt: skip

    def names(self, v: View) -> dict[str, str]:
        """Company names: the price store's symbols.csv; in the demo, labelled made-up names."""
        src = self.sources
        if src.demo:
            codes = [h.code for h in v.holdings] + [f"S{i:03d}" for i in range(1000)]
            return app_pages.demo_names(codes)
        return app_pages.safe(lambda: app_pages.company_names(src.store_root), {})

    HEAVY = ("/search.json", "/compare", "/shares")  # security review L6: cached 60 s
    CACHE_S = 60.0

    def _cached(self, path: str, qs: Mapping[str, str], viewer: str) -> tuple[str, bytes] | None:
        """The heavy read-only screens are built at most once a minute per viewer and
        address (a refresh storm cannot load the server); everything else is live."""
        import time as _t

        if not path.startswith(self.HEAVY):
            return self._screen(path, qs, viewer)
        cache: dict[tuple[str, str, str], tuple[float, tuple[str, bytes] | None]]
        cache = self.__dict__.setdefault("_heavy", {})
        key = (path, urllib.parse.urlencode(sorted(qs.items())), viewer)
        hit = cache.get(key)
        now = _t.monotonic()
        if hit is not None and now - hit[0] < self.CACHE_S:
            return hit[1]
        res = self._screen(path, qs, viewer)
        if len(cache) > 256:
            cache.clear()
        cache[key] = (now, res)
        return res

    def _screen(  # noqa: PLR0911, PLR0912, PLR0915 - one return per screen
        self, path: str, qs: Mapping[str, str], viewer: str
    ) -> tuple[str, bytes] | None:
        src = self.sources
        v = collect(src)
        j = src.journal
        x = app_pages.collect_extras(
            j, src.book, v.now, viewer, self.action_logins, self.channel, src.approval_deadline
        ) if _has_journal(j) else Extras(viewer=viewer, action_logins=self.action_logins,
                                         channel=self.channel)  # fmt: skip
        x.update_mode = self.update_mode
        if x.presence is not None:  # BF-D82: the configured days
            from dataclasses import replace as _replace

            warn = min(src.presence_warn_days, src.presence_days - 1)
            x.presence = _replace(x.presence, days=src.presence_days, warn_days=warn)
        x.names = self.names(v)
        x.changelog = app_pages.safe(self.changelog, [])
        html_t = "text/html; charset=utf-8"
        sess: Sequence[date] = src.sessions() if src.sessions else []
        if path in ("/", "/health", "/costs", "/digest", "/server", "/strategy"):
            from trader import app_ops

            x.ops = app_ops.collect(src, v, _has_journal(j))
            if path == "/health":
                return html_t, app_ops.health(v, x, x.ops, self.version).encode()
            if path == "/costs":
                return html_t, app_ops.costs(v, x, x.ops).encode()
            if path == "/digest":
                return html_t, app_ops.digest_page(src, v, x, x.ops, dict(qs)).encode()
        if path == "/":
            return html_t, app_pages.home(v, x).encode()
        if path == "/holdings":
            return html_t, app_pages.holdings(v, x, j).encode()
        if path.startswith("/holdings/"):
            code = path.split("/", 2)[2].upper()
            out = app_pages.holding_detail(v, x, j, code, sess, self.share_ctx(v)) \
                if _has_journal(j) else None  # fmt: skip
            return None if out is None else (html_t, out.encode())
        if path in ("/calendar", "/compare", "/search.json") or path.startswith("/replay/"):
            return self._more(path, qs, v, x, sess)
        if path in ("/shares", "/forecast-method") or path.startswith("/shares/"):
            from trader import share_pages

            seg = ('<div class="seg"><a href="/holdings" data-nav>Holdings</a><a class="on" '
                   'href="/shares" data-nav>Shares</a><a href="/tax" data-nav>Tax</a>'
                   "</div>")  # fmt: skip
            if path == "/forecast-method":
                body = share_pages.method_page(src.forecast_dir)
                return html_t, app_pages.shell(v, x, "Forecast bands", body, "holdings").encode()
            if not _has_journal(j):
                return None
            ctx = self.share_ctx(v)
            if path == "/shares":
                body = seg + share_pages.shares_list(ctx, [h.code for h in v.holdings])
                return html_t, app_pages.shell(v, x, "Shares", body, "holdings").encode()
            code = urllib.parse.unquote(path.split("/", 2)[2]).upper()
            if any(h.code == code for h in v.holdings):
                out = app_pages.holding_detail(v, x, j, code, sess, ctx)
            else:
                d = share_pages.share_detail(ctx, code)
                out = None if d is None else app_pages.shell(v, x, code, d, "holdings")
            return None if out is None else (html_t, out.encode())
        if path == "/orders":
            body = app_pages.orders(v, x, j) if _has_journal(j) else app_pages.home(v, x)
            return html_t, body.encode()
        if path.startswith("/orders/"):
            bid = urllib.parse.unquote(path.split("/", 2)[2])
            out = app_pages.batch_detail(v, x, j, bid) if _has_journal(j) else None
            return None if out is None else (html_t, out.encode())
        if path == "/inbox":
            return html_t, app_pages.inbox(v, x, qs.get("kind", "all")).encode()
        if path == "/server":
            return html_t, app_pages.server(v, x).encode()
        if path == "/backups":
            return html_t, app_pages.backups(v, x).encode()
        if path == "/accounts":
            return html_t, app_pages.accounts(v, x).encode()
        if path == "/setup":
            return html_t, app_pages.setup(v, x, app_pages.safe(self.setup_facts, {}), j).encode()
        if path == "/strategy":
            return html_t, app_pages.strategy(v, x).encode()
        if path == "/settings":
            return html_t, app_pages.settings(v, x, self.version, self.checklist()).encode()
        if path in ("/tax", "/tax.csv"):
            from trader import tax_screen

            if path == "/tax.csv":
                return "text/csv; charset=utf-8", tax_screen.csv_export(src, qs).encode()
            return html_t, tax_screen.screen(v, x, src, qs).encode()
        return None

    def _more(  # noqa: PLR0911 - one return per screen
        self, path: str, qs: Mapping[str, str], v: View, x: Extras,
              sess: Sequence[date]) -> tuple[str, bytes] | None:  # fmt: skip
        """BF-D68: calendar, compare, month replay and the search index (GET, read-only)."""
        from trader import app_more

        src = self.sources
        j = src.journal
        html_t = "text/html; charset=utf-8"
        ok = _has_journal(j)
        today = v.now.astimezone(ASX_TZ).date()
        if path == "/calendar":
            try:
                m = date.fromisoformat(qs.get("m", "")[:7] + "-01")
            except ValueError:
                m = today.replace(day=1)
            a = m - timedelta(days=7)
            b = m + timedelta(days=45)
            codes = [h.code for h in v.holdings]
            empty: dict[str, list[tuple[date, date | None, float]]] = {}
            divs = app_pages.safe(lambda: app_more.store_divs(src.store_root, codes), empty)
            sc = self.share_ctx(v) if ok else None
            none: list[app_more.Ev] = []
            evs = app_pages.safe(lambda: app_more.calendar_events(
                v, j if ok else None, sess, sc, divs, a, b), none)  # fmt: skip
            seg = ('<div class="seg"><a href="/orders" data-nav>Decisions</a><a class="on" '
                   'href="/calendar" data-nav>Calendar</a></div>')  # fmt: skip
            body = seg + app_more.calendar(v, m, evs, today)
            return html_t, app_pages.shell(v, x, "Calendar", body, "orders").encode()
        if path == "/compare":
            if not ok:
                return None
            codes = [h.code for h in v.holdings]
            body = (webui.backlink("/holdings", "Holdings") + "<h1>Compare</h1>"
                    + app_more.compare(v, self.share_ctx(v), codes))  # fmt: skip
            return html_t, app_pages.shell(v, x, "Compare", body, "holdings").encode()
        if path.startswith("/replay/"):
            if not ok:
                return None
            try:
                d = date.fromisoformat(path.split("/", 2)[2])
            except ValueError:
                return None
            out = app_more.replay(v, j, d)
            return None if out is None else (
                html_t, app_pages.shell(v, x, "Replay", out, "orders").encode())  # fmt: skip
        if path == "/search.json":
            rows: list[Any] = []
            if ok:
                from trader import tax_screen

                for y in tax_screen.years(src, today)[-2:]:
                    try:
                        rows += list(tax_screen.report(src, y).cgt)
                    except Exception:  # noqa: S112 - the search works without the tax rows
                        continue
            idx = app_more.search_index(v, j if ok else None, self.share_ctx(v) if ok else None,
                                        x, rows)  # fmt: skip
            return "application/json", json.dumps(idx, default=str).encode()
        return None

    def respond(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes = b"",
        peer: str = "",
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs = dict(webui.SECURITY_HEADERS)
        if self.trusted_peers and peer not in self.trusted_peers:  # BF-D46: a forged log-in
            headers = {k: v for k, v in headers.items() if k.lower() != "tailscale-user-login"}
        url = urllib.parse.urlsplit(path)
        p = url.path.rstrip("/") or "/"
        who = next((v for k, v in headers.items() if k.lower() == "tailscale-user-login"), "")
        who = who.strip().lower()
        if self.allowed_logins and p != "/healthz" and who not in self.allowed_logins:
            return 403, hdrs, b"not allowed\n"
        if p == "/act" or p.startswith("/act/"):
            if self.actions is None:
                hdrs["Content-Type"] = "text/html; charset=utf-8"
                msg = webui.page("Actions", webui.section(
                    "Actions unavailable", "<p>This app was started without the trader's "
                    "actions (read-only).</p>"), refresh=False)  # fmt: skip
                return 503, hdrs, msg.encode()
            return self.actions(method, path, headers, body)
        if method not in READ_METHODS:
            hdrs["Allow"] = "GET, HEAD"
            return 405, hdrs, b"read-only\n"
        route = self.routes().get(p)
        if route is not None:
            ctype, out = route()
        else:
            qs = {k: v[-1] for k, v in urllib.parse.parse_qs(url.query).items()}
            known = p in self.SCREENS or p.startswith(
                ("/holdings/", "/orders/", "/shares/", "/replay/")
            )
            if p == "/search.json":
                hdrs["Cache-Control"] = "no-store"
            res = self._cached(p, qs, who) if known else None
            if res is None:
                return 404, hdrs, b"not found\n"
            ctype, out = res
            if p == "/tax.csv":
                hdrs["Content-Disposition"] = 'attachment; filename="bigwins_tax.csv"'
        hdrs["Content-Type"] = ctype
        if p == "/sw.js":
            hdrs["Service-Worker-Allowed"] = "/"
        return 200, hdrs, out


def make_handler(app: Dashboard) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "BigWins"
        sys_version = ""

        def _go(self) -> None:
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(min(n, 16385)) if n > 0 else b""
            status, hdrs, out = app.respond(
                self.command, self.path, dict(self.headers), body, self.client_address[0]
            )
            self.send_response(status)
            for k, val in hdrs.items():
                self.send_header(k, val)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(out)

        do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _go  # noqa: N815

        def log_message(self, format: str, *args: Any) -> None:
            return  # no request log (keeps the owner's tailnet log-ins out of docker logs)

    return Handler


def serve(app: Dashboard, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(app))
