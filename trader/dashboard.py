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
import struct
import urllib.error
import urllib.parse
import urllib.request
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

from trader import app_pages, webui
from trader.app_pages import Extras
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
    approval_deadline: str = "15:20"
    tax_params: Any = None  # trader.tax_report.TaxParams (BF-D44); None = the defaults
    marginal_rate: Decimal | None = None  # tax.marginal_rate (BF-D44), set on the server only


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


def render(v: View, x: Extras | None = None) -> str:
    """The Home screen (BF-D43; ``--snapshot`` writes it)."""
    return app_pages.home(v, x or Extras())


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
    "description": "The Big Wins paper book: view, approve, alerts",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "background_color": THEME,
    "theme_color": THEME,
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"},
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


# ---------------------------------------------------------------- HTTP

READ_METHODS = frozenset({"GET", "HEAD"})
ActionsFn = Callable[[str, str, Mapping[str, str], bytes], tuple[int, dict[str, str], bytes]]
FORWARD_IN = ("tailscale-user-login", "tailscale-user-name", "cookie", "content-type",
              "origin", "sec-fetch-site", "sec-fetch-mode", "x-csrf-token")  # fmt: skip
FORWARD_OUT = ("content-type", "set-cookie", "cache-control", "content-security-policy")


def proxy_to(base: str, timeout: float = 70.0) -> ActionsFn:
    """BF-D39: forward ``/act/...`` unchanged to the trader's control server (which checks
    the log-in, the form token and the code itself). The dashboard adds nothing and
    keeps no state; a trader that is down gives a clear page, never a write elsewhere."""

    def forward(
        method: str, path: str, headers: Mapping[str, str], body: bytes
    ) -> tuple[int, dict[str, str], bytes]:
        fwd = {k: v for k, v in headers.items() if k.lower() in FORWARD_IN}
        host = next((v for k, v in headers.items() if k.lower() == "host"), "")
        if host:
            fwd["X-Forwarded-Host"] = host
            fwd["Host"] = host
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
        }
        for path, (ctype, text) in webui.STATIC.items():
            out[path] = _static(ctype, text)
        return out

    SCREENS = ("/", "/holdings", "/orders", "/inbox", "/server", "/settings", "/tax", "/tax.csv",
               "/strategy")  # fmt: skip

    def _screen(  # noqa: PLR0911 - one return per screen
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
        x.changelog = app_pages.safe(self.changelog, [])
        html_t = "text/html; charset=utf-8"
        sess: Sequence[date] = src.sessions() if src.sessions else []
        if path == "/":
            return html_t, app_pages.home(v, x).encode()
        if path == "/holdings":
            return html_t, app_pages.holdings(v, x, j).encode()
        if path.startswith("/holdings/"):
            code = path.split("/", 2)[2].upper()
            out = app_pages.holding_detail(v, x, j, code, sess) if _has_journal(j) else None
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

    def respond(
        self, method: str, path: str, headers: Mapping[str, str], body: bytes = b""
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs = dict(webui.SECURITY_HEADERS)
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
            known = p in self.SCREENS or p.startswith(("/holdings/", "/orders/"))
            res = self._screen(p, qs, who) if known else None
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
            status, hdrs, out = app.respond(self.command, self.path, dict(self.headers), body)
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
