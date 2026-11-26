"""The honest scoreboard, running costs, research lines, job freshness and the weekly
digest (BF-D75..BF-D80, review fixes BF-D81). Read-only computations over what the
trader already records; the phone app shows them and the trader's hooks
(``trader.ops_hooks``) push the alerts and file the digest.

Nothing here changes the strategy, a paper line, an order or a limit.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select

from trader.constants import ASX_TZ
from trader.journal import Journal, events

CENT = Decimal("0.01")
MINUS = "−"

# ---------------------------------------------------------------- the paper lines (ledger seq 96)

MAIN_LINE = (
    "BT_C6"  # the live trader's strategy: EMG2-18 + band-trend shield + C6 (frozen to 1 Jan 2027)
)
# The research lines kept by the owner's decision of 24 Nov 2026 (ledger seq 96), in the
# registered order (never ranked): (id, plain name, the record's exact book names in order of
# preference). Exact names only: a twin (``..._RND_...``), comparator or retired row can never
# match. Names from the record's scorecard and its paper_sidelines / paper_moon code.
KEPT_LINES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("REF", "Reference book (EMG2-18, no shield)", ("EMG2_18_REF",)),
    ("EMG2", "EMG2 (the first challenger)", ("EMG2_100k",)),  # the A$100k measurement line
    ("H82", "Large-Cap Core", ("H82_25k", "H82_lifecycle_5k", "H82_100k")),
    ("MOM", "Plain momentum", ("MOM_25k", "MOM_100k")),
    ("BLIND3", "Steady Momentum", ("BLIND3_10k", "BLIND3_100k")),
    ("SWEEP", "Main line, one change: SWEEP", ("EMG2_18_SIM_BT_C6_SWEEP",)),
    ("WIDE", "Main line, one change: WIDE", ("EMG2_18_SIM_BT_C6_WIDE",)),
    ("FIP", "Main line, one change: FIP", ("EMG2_18_SIM_BT_C6_FIP",)),
    ("MOON_TOP5", "Aggressive: MOON TOP5", ("EMG2_MOON_TOP5",)),
    ("MOON_NOLOT5", "Aggressive: MOON NOLOT5", ("EMG2_MOON_NOLOT5",)),
    ("MOON_LEG2", "Aggressive: MOON LEG2", ("MOON_LEG2",)),
)
RETIRED_LINES = ("H6", "COMBO", "SIM_BT", "PAIR", "EARLY", "ACC", "M3", "E3", "CXL")
RETIRED_ON = date(2026, 12, 31)
LUCK = "mostly luck at this stage"
# Research gap review (ledger seq 90): the 2018-26 replay with the live A$10k cap and rule 14
BACKTEST_NOTE = ("Backtest 2018–26 with the live $10,000 cap and rule 14: $21.0k against $18.6k "
                 "for the fund, before fixed costs (research gap review). An earlier, uncapped "
                 "figure of $34.5k is not what this book can do.")  # fmt: skip
EXIT_NOTE = ("Shares are valued at the last close: selling them would also cost about half "
             "the spread (around 0.5% for these small companies).")  # fmt: skip


# ---------------------------------------------------------------- small helpers


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def job_rows(j: Journal, prefix: str, newest: int | None = None) -> list[tuple[str, Any, datetime]]:
    """(key, detail, at) of job records with ``prefix``, oldest first (read-only)."""
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


def _last_day(j: Journal, prefix: str, scan: int = 50) -> date | None:
    """The newest valid date in the keys ``<prefix><YYYY-MM-DD>``; malformed keys are
    skipped (review S4: one bad key never stops the monitor)."""
    for k, _, _ in reversed(job_rows(j, prefix, scan)):
        d = _day(k[len(prefix) :])
        if d is not None:
            return d
    return None


def state(j: Journal, key: str) -> tuple[Any, datetime] | None:
    from trader.app_store import get_state

    try:
        return get_state(j, key)
    except Exception:
        return None


def fy_start(d: date) -> date:
    """1 July of the Australian financial year that holds ``d``."""
    return date(d.year if d.month >= 7 else d.year - 1, 7, 1)


def money(x: Decimal | float | None, sign: bool = False) -> str:
    if x is None:
        return "–"
    q = Decimal(str(x)).quantize(Decimal(1))
    s = f"{abs(q):,.0f}"
    if sign:
        return ("+" if q >= 0 else MINUS) + "$" + s
    return (MINUS if q < 0 else "") + "$" + s


def pct(x: float | None, sign: bool = True) -> str:
    if x is None or not math.isfinite(x):
        return "–"
    s = f"{abs(x) * 100:.1f}%"
    if s == "0.0%":
        return s
    return (("+" if x >= 0 else MINUS) + s) if sign else s


def plural(n: int, one: str, many: str = "") -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _day(x: object) -> date | None:
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------- running costs (BF-D76)

COST_KEYS = (("server", "Server (BinaryLane)"), ("data", "Price data (EODHD)"),
             ("other", "Other (tools, subscriptions)"))  # fmt: skip
MIN_FIXED_TOTAL = Decimal(50)  # BF-D81 (N1): an edited total under this (but not 0) is refused


@dataclass(frozen=True)
class FixedCosts:
    """The fixed running costs a year now (``items``) and, when they were edited in the
    app, from which day each set applies (``segments``: (from, {key: A$ a year})). Days
    before the first edit use ``base`` (the server settings)."""

    items: tuple[tuple[str, str, Decimal], ...]  # (key, label, A$ a year) now
    source: str  # "app" (edited on the phone) | "config" | "total"
    base: tuple[tuple[str, str, Decimal], ...] = ()
    segments: tuple[tuple[date, tuple[tuple[str, Decimal], ...]], ...] = ()
    since: date | None = None  # the current amounts apply from this day (app edits)

    @property
    def per_year(self) -> Decimal:
        return sum((a for _, _, a in self.items), Decimal(0))

    def between(self, a: date, b: date) -> dict[str, Decimal]:
        """The fixed costs of the days a..b (inclusive), by key, pro rata."""
        out: dict[str, Decimal] = {}
        if b < a:
            return out
        base = tuple((k, amt) for k, _, amt in (self.base or self.items))
        cuts = [(date.min, base), *self.segments]
        for i, (frm, amounts) in enumerate(cuts):
            nxt = cuts[i + 1][0] if i + 1 < len(cuts) else date.max
            lo, hi = max(a, frm), min(b, nxt - timedelta(days=1) if nxt != date.max else b)
            if hi < lo:
                continue
            days = Decimal((hi - lo).days + 1)
            for k, amt in amounts:
                out[k] = out.get(k, Decimal(0)) + amt * days / Decimal(365)
        return {k: v.quantize(CENT) for k, v in out.items()}


def _app_items(rec: Mapping[str, Any]) -> tuple[tuple[str, Decimal], ...]:
    return tuple((k, Decimal(str(rec.get(k, 0) or 0))) for k, _ in COST_KEYS)


def fixed_costs(j: Journal | None, cfg_items: Mapping[str, Decimal] | None,
                total: Decimal) -> FixedCosts:  # fmt: skip
    """The fixed running costs a year: the amounts edited in the app (state
    ``running-costs``, each set with the day it applies from), else ``running_costs`` of
    the config, else the single ``costs.fixed_aud_per_year``."""
    if cfg_items and any(Decimal(str(v)) > 0 for v in cfg_items.values()):
        base = FixedCosts(tuple((k, lab, Decimal(str(cfg_items.get(k, 0))))
                                for k, lab in COST_KEYS), "config")  # fmt: skip
    else:
        base = FixedCosts((("total", "Fixed costs (server, data, tools)", Decimal(total)),),
                          "total")  # fmt: skip
    st = state(j, "running-costs") if j is not None else None
    rec = st[0] if st and isinstance(st[0], Mapping) else {}
    hist = rec.get("history") if isinstance(rec.get("history"), list) else None
    if hist is None and rec and any(k in rec for k, _ in COST_KEYS):  # an older record
        hist = [{**rec, "from": "1970-01-01"}]
    segs: list[tuple[date, tuple[tuple[str, Decimal], ...]]] = []
    try:
        for h in hist or []:
            frm = _day(h.get("from")) if isinstance(h, Mapping) else None
            if frm is None:
                continue
            amounts = _app_items(h) if not h.get("cleared") else tuple(
                (k, a) for k, _, a in base.items)  # fmt: skip
            segs.append((frm, amounts))
    except (ArithmeticError, AttributeError):
        segs = []
    segs.sort(key=lambda s: s[0])
    if not segs:
        return base
    last = (hist or [{}])[-1]
    if isinstance(last, Mapping) and last.get("cleared"):
        return FixedCosts(base.items, base.source, base.items, tuple(segs), segs[-1][0])
    labels = dict(COST_KEYS)
    items = tuple((k, labels[k], a) for k, a in segs[-1][1])
    return FixedCosts(items, "app", base.items, tuple(segs), segs[-1][0])


@dataclass
class CostRow:
    label: str  # "Nov 26", "This financial year"
    start: date
    end: date
    brokerage: Decimal = Decimal(0)
    spread: Decimal = Decimal(0)
    fixed: Decimal = Decimal(0)
    fixed_items: dict[str, Decimal] = field(default_factory=dict)
    account: Decimal | None = None  # account value at the end of the period

    @property
    def trading(self) -> Decimal:
        return self.brokerage + self.spread

    @property
    def total(self) -> Decimal:
        return self.trading + self.fixed

    def share(self, x: Decimal) -> float | None:
        return float(x / self.account) if self.account else None


@dataclass
class CostReport:
    months: list[CostRow]
    ytd: CostRow
    since_start: CostRow
    fixed: FixedCosts
    half_spread: Decimal
    verdict: str
    annual_pct: float | None  # the yearly estimate: fixed a year + trading at the pace so far
    days: int = 0
    fixed_annual: float | None = None
    trading_annual: float | None = None
    so_far_pct: float | None = None


def cost_report(
    fills: Sequence[Any],
    series: Sequence[tuple[date, Decimal]],
    today: date,
    fc: FixedCosts,
    half_spread: Decimal,
    start: date | None = None,
) -> CostReport | None:
    """Brokerage and fees (the fills' commission), the modelled spread (half-spread a side
    of every fill's value, the L9 assumption) and the fixed costs pro rata, by month,
    for this financial year and since the start; each also as a share of the account.
    The period ends on the last daily value (the same day as the scoreboard)."""
    if start is None:
        start = series[0][0] if series else None
    if start is None:
        return None
    end = max(series[-1][0] if series else today, start)

    def val_at(d: date) -> Decimal | None:
        vs = [v for dd, v in series if dd <= d]
        return vs[-1] if vs else (series[0][1] if series else None)

    def row(label: str, a: date, b: date) -> CostRow:
        a = max(a, start)
        r = CostRow(label, a, b)
        for f in fills:
            d = _aware(f.executed_at).astimezone(ASX_TZ).date()
            if a <= d <= b:
                r.brokerage += Decimal(str(f.commission))
                r.spread += (Decimal(str(f.price)) * f.qty * half_spread).quantize(CENT)
        r.fixed_items = fc.between(a, b)
        r.fixed = sum(r.fixed_items.values(), Decimal(0))
        r.account = val_at(b)
        return r

    months = []
    m = date(start.year, start.month, 1)
    while m <= end:
        nxt = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        months.append(row(f"{m:%b %y}", m, min(nxt - timedelta(days=1), end)))
        m = nxt
    ytd = row("This financial year", fy_start(end), end)
    since = row("Since the start", start, end)
    days = max(1, (end - start).days + 1)
    rep = CostReport(months[::-1], ytd, since, fc, half_spread, "", None, days)
    if since.account:
        acc = since.account
        rep.fixed_annual = float(fc.per_year / acc)
        rep.trading_annual = float(since.trading / acc) * 365 / days
        rep.annual_pct = rep.fixed_annual + rep.trading_annual
        rep.so_far_pct = float(since.total / acc)
    rep.verdict = cost_verdict(rep)
    return rep


def cost_verdict(r: CostReport) -> str:
    """BF-D81 (review M3): the level, the share and the "most of it" wording all come from
    the same yearly components: fixed costs a year and trading costs at the pace so far.
    In the first year it also says what was spent so far, and that the first buys make
    the yearly trading figure an overestimate."""
    if r.annual_pct is None or r.fixed_annual is None or r.trading_annual is None:
        return "No costs yet: the book has not started."
    a = r.annual_pct
    level = "High" if a >= 0.05 else ("Noticeable" if a >= 0.02 else "Low")
    lead = ("fixed costs are most of it" if r.fixed_annual >= r.trading_annual
            else "trading costs are most of it")  # fmt: skip
    parts = (f"fixed {r.fixed_annual * 100:.1f}% a year, trading {r.trading_annual * 100:.1f}% "
             "a year")  # fmt: skip
    if r.days < 365:
        out = (f"{level}: so far {pct(r.so_far_pct, False)} of the account in "
               f"{plural(r.days, 'day')}. Estimated for a full year: about {a * 100:.1f}% "
               f"({parts}; {lead}). The first buys make the yearly trading figure too high.")  # fmt: skip
    else:
        out = f"{level}: about {a * 100:.1f}% of the account a year ({parts}; {lead})."
    if a >= 0.05:
        out += " The strategy has to beat the fund by more than this just to break even."
    return out


# ---------------------------------------------------------------- the honest scoreboard (BF-D75)

Flow = tuple[date, Decimal]  # (day, + deposit / - withdrawal)


@dataclass
class Scoreboard:
    start: date
    end: date
    capital: Decimal  # net money put in (deposits less withdrawals)
    value: Decimal  # account value: brokerage and the real spread are already inside it
    fixed: Decimal  # fixed running costs since the start (pro rata)
    tax: Decimal | None  # estimated tax on gains already realised (None: not modelled)
    a200: Decimal | None  # each deposit / withdrawal put into / taken out of A200 on its day
    a200_cost: Decimal  # A200's own buys: brokerage + half the spread
    flows: tuple[Flow, ...] = ()

    @property
    def after_costs(self) -> Decimal:
        return self.value - self.fixed - (self.tax or 0)

    @property
    def gap(self) -> Decimal | None:
        return None if self.a200 is None else (self.after_costs - self.a200).quantize(CENT)

    @property
    def mine_pct(self) -> float | None:
        return float(self.after_costs / self.capital - 1) if self.capital else None

    @property
    def a200_pct(self) -> float | None:
        return (
            float(self.a200 / self.capital - 1) if self.a200 is not None and self.capital else None
        )

    @property
    def basis(self) -> str:
        """BF-D81 (review M2): what "after costs" includes, said everywhere it is used."""
        return "after all costs" if self.tax is not None else "after running costs, before tax"

    @property
    def sentence(self) -> str:
        g = self.gap
        if g is None:
            return "The A200 comparison is not available yet (no fund prices in the store)."
        if abs(g) < 1:
            return f"Level with A200 {self.basis}."
        word = "Ahead of" if g > 0 else "Behind"
        return f"{word} A200 by {money(abs(g))} {self.basis}."


def _level_at(pts: Sequence[tuple[date, float]], d: date) -> float | None:
    """The index level on ``d``: the last point on or before it, else the first point."""
    best = None
    for dd, x in pts:
        if dd <= d:
            best = x
        else:
            break
    return best if best is not None else (pts[0][1] if pts else None)


def a200_value(flows: Sequence[Flow], index: Sequence[tuple[date, float]], on: date,
               entry_cost: Callable[[Decimal], Decimal] | None = None) -> Decimal | None:  # fmt: skip
    """BF-D81 (review S1): each deposit buys A200 on its own day (less its buy cost); each
    withdrawal sells A200 on its day; the holding is valued on ``on``."""
    pts = sorted((d, x) for d, x in index if x > 0)
    if not pts:
        return None
    end = _level_at(pts, on)
    if end is None:
        return None
    units = 0.0
    for d, amt in flows:
        if d > on:
            continue
        lvl = _level_at(pts, d)
        if lvl is None:
            continue
        put = amt - (entry_cost(amt) if entry_cost is not None and amt > 0 else Decimal(0))
        units += float(put) / lvl
    return Decimal(repr(units * end)).quantize(CENT)


def scoreboard(
    series: Sequence[tuple[date, Decimal]],
    index: Sequence[tuple[date, float]],
    flows: Decimal | Sequence[Flow],
    fixed: FixedCosts | Decimal,
    entry_cost: Callable[[Decimal], Decimal] | Decimal | None = None,
    tax: Decimal | None = None,
) -> Scoreboard | None:
    """The main line's account value after every cost against the same money in A200.
    ``index``: A200's total-return level (any base); ``flows``: the book's deposits and
    withdrawals (a single amount = one deposit on the first day)."""
    if not series:
        return None
    d0, d1 = series[0][0], series[-1][0]
    fl: list[Flow] = ([(d0, Decimal(flows))] if isinstance(flows, Decimal | int)
                      else [(min(max(d, d0), d1), Decimal(a)) for d, a in flows])  # fmt: skip
    capital = sum((a for _, a in fl), Decimal(0))
    if not capital:
        return None
    if isinstance(fixed, FixedCosts):
        fixed_amt = sum(fixed.between(d0, d1).values(), Decimal(0))
    else:
        fixed_amt = (fixed * Decimal((d1 - d0).days + 1) / Decimal(365)).quantize(CENT)
    win = [(d, x) for d, x in index if d <= d1 and x > 0]
    if isinstance(entry_cost, Decimal):  # one buy cost, on the first deposit
        a200_cost = entry_cost
        net = [(fl[0][0], fl[0][1] - entry_cost), *fl[1:]]
        a200 = a200_value(net, win, d1) if win else None
    else:
        cost = entry_cost
        a200 = a200_value(fl, win, d1, cost) if win else None
        a200_cost = sum((cost(a) for _, a in fl if a > 0), Decimal(0)) if cost else Decimal(0)
    a200_cost = Decimal(a200_cost).quantize(CENT)
    return Scoreboard(d0, d1, capital, series[-1][1], fixed_amt, tax, a200, a200_cost, tuple(fl))


def gap_series(sb: Scoreboard, series: Sequence[tuple[date, Decimal]],
               index: Sequence[tuple[date, float]], fc: FixedCosts | Decimal,
               entry_cost: Callable[[Decimal], Decimal] | None = None
               ) -> list[tuple[date, float]]:  # fmt: skip
    """Big Wins after running costs minus A200, day by day (the gap sparkline)."""
    out = []
    idx_days = {d for d, _ in index}
    for d, val in series:
        if d not in idx_days:
            continue
        a = a200_value([f for f in sb.flows if f[0] <= d], index, d, entry_cost)
        if a is None:
            continue
        if isinstance(fc, FixedCosts):
            fx = sum(fc.between(sb.start, d).values(), Decimal(0))
        else:
            fx = fc * Decimal((d - sb.start).days + 1) / Decimal(365)
        out.append((d, float(val - fx - a)))
    return out


def book_flows(j: Journal, book: str) -> list[Flow]:
    """Deposits (+) and withdrawals (-) of ``book``, by Sydney day."""
    out = []
    for m in j.cash_moves_of(book):
        kind = str(m.get("kind", "")).upper()
        if kind not in ("DEPOSIT", "WITHDRAWAL"):
            continue
        amt = abs(Decimal(str(m["amount"])))
        d = _aware(m["at"]).astimezone(ASX_TZ).date()
        out.append((d, amt if kind == "DEPOSIT" else -amt))
    return out


def tax_estimate(src: Any, today: date) -> tuple[Decimal | None, str]:
    """Tax already modelled (BF-D44): the estimated tax on the book's realised net
    capital gains since the start, at ``tax.marginal_rate``; none without the rate.
    ``src``: anything with journal, book, tax_params, amit_csv, prior_losses, live and
    marginal_rate (the dashboard's Sources or the trader's settings)."""
    rate = getattr(src, "marginal_rate", None)
    if rate is None:
        return None, "Tax: not included (your tax rate is not set on the server)."
    from trader import tax_screen

    total = Decimal(0)
    for y in tax_screen.years(src, today):
        r = tax_screen.report(src, y)
        total += max(Decimal(0), r.summary.net_gain) * Decimal(str(rate))
    return total.quantize(CENT), "Tax: estimated on gains already realised, at your tax rate."


@dataclass
class Score:
    """The one scoreboard both the app and the digest show (BF-D81, review M4)."""

    board: Scoreboard | None
    gap_series: list[tuple[date, float]]
    fixed: FixedCosts
    tax_note: str


def build_score(
    j: Journal,
    book: str,
    series: Sequence[tuple[date, Decimal]],
    index: Sequence[tuple[date, float]],
    fixed: FixedCosts,
    commission: Callable[[Decimal], Decimal] | None,
    fund_half_spread: Decimal,
    tax: tuple[Decimal | None, str] = (None, "Tax: not included (your tax rate is not set "
                                             "on the server)."),
) -> Score:  # fmt: skip
    def entry(amount: Decimal) -> Decimal:
        c = Decimal(str(commission(amount))) if commission is not None else Decimal(0)
        return (c + amount * fund_half_spread).quantize(CENT)

    flows = book_flows(j, book)
    sb = scoreboard(series, index, flows, fixed, entry, tax[0]) if flows else None
    gs = gap_series(sb, series, index, fixed, entry) if sb is not None and len(index) > 1 else []
    return Score(sb, gs, fixed, tax[1])


# ---------------------------------------------------------------- research lines (BF-D75)


@dataclass(frozen=True)
class ResearchLine:
    id: str
    name: str
    book: str | None  # the record's book shown
    capital: float | None
    nav: float | None
    ret: float | None  # since start (the record's own costs; no fixed costs)
    vs_a200: float | None
    asof: str = ""
    start: str = ""  # the first day the record shows a value for this book


def _rows(p: Path) -> list[dict[str, str]]:
    try:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            return list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return []


def research_lines(scorecard: Path | None, today: date) -> list[ResearchLine] | None:
    """The kept research lines from the research record's ``paper/scorecard_latest.csv``
    (mounted read-only), in the registered order, never ranked; the start day from
    ``scorecard_history.csv`` next to it. None: no record here."""
    if scorecard is None or not scorecard.is_file():
        return None
    rows = _rows(scorecard)
    by_book = {r.get("book", "").strip(): r for r in rows}
    starts: dict[str, str] = {}
    for r in _rows(scorecard.parent / "scorecard_history.csv"):
        b = r.get("book", "").strip()
        if b and _fl(r.get("nav")) is not None and b not in starts:
            starts[b] = str(r.get("asof", ""))[:10]
    out = []
    for lid, name, books in KEPT_LINES:
        hit = next((by_book[b] for b in books if b in by_book), None)
        if hit is None:
            out.append(ResearchLine(lid, name, None, None, None, None, None))
            continue
        b = hit.get("book", "").strip()
        nav = _fl(hit.get("nav"))
        out.append(ResearchLine(lid, name, b, _fl(hit.get("capital")), nav,
                                _fl(hit.get("return_since_start")) if nav is not None else None,
                                _fl(hit.get("vs_a200")), hit.get("asof", ""),
                                starts.get(b, "")))  # fmt: skip
    return out


def retired_shown(today: date) -> bool:
    return today > RETIRED_ON


def _fl(x: object) -> float | None:
    try:
        v = float(str(x))
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# ---------------------------------------------------------------- job freshness (BF-D77)


@dataclass(frozen=True)
class Fresh:
    key: str
    name: str
    cadence: str
    status: str  # ok | late | failed | off (switched off) | new (nothing yet)
    last: str  # plain words
    detail: str = ""
    incident: str = ""  # unique per incident; "" when ok / off / new

    @property
    def bad(self) -> bool:
        return self.status in ("late", "failed")


def _at(d: date, hhmm: str) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(d, time(h, m), ASX_TZ)


def _latest_session(sessions: Sequence[date], now: datetime, due: Callable[[date], datetime]
                    ) -> date | None:  # fmt: skip
    past = [s for s in sessions if due(s) <= now]
    return max(past) if past else None


def _ago(t: datetime, now: datetime) -> str:
    s = (now - t).total_seconds()
    if s < 5400:
        return f"{max(s, 0) / 60:.0f} min ago"
    if s < 2 * 86400:
        return f"{s / 3600:.0f} h ago"
    return f"{s / 86400:.0f} days ago"


DAILY = ("daily", "Trader daily run", "every ASX day by 22:45")
PRICES = ("prices", "Price download (EODHD)", "every ASX day by 22:05")
INFO = ("info", "Info archive (announcements)", "every ASX day, next morning")
TWIN = ("twin", "Previous-version twin", "nights after trading days")
TWIN_LATE = timedelta(hours=80)  # BF-D81 (review S3 d): Tue-Sat runs; Monday is not late


def _f(spec: tuple[str, str, str], status: str, last: str, detail: str = "",
       incident: str = "") -> Fresh:  # fmt: skip
    return Fresh(spec[0], spec[1], spec[2], status, last, detail, incident)


def _daily(j: Journal, book: str, sess: Sequence[date], now: datetime) -> Fresh:
    last = _last_day(j, f"value:{book}:")
    exp = _latest_session(sess, now, lambda s: _at(s, "23:30"))
    if last is None:
        return _f(DAILY, "new", "not started yet")
    if exp is not None:
        rep = job_rows(j, f"{exp}:22:45:report", 1)
        if rep and isinstance(rep[-1][1], Mapping) and rep[-1][1].get("error"):
            err = str(rep[-1][1]["error"])[:120]
            return _f(DAILY, "failed", f"{last:%a %d %b}",
                      f"the report of {exp:%a %d %b} failed: {err}", f"daily:failed:{exp}")  # fmt: skip
        if last < exp:
            return _f(DAILY, "late", f"{last:%a %d %b}", f"no daily report for {exp:%a %d %b}",
                      f"daily:late:{exp}")  # fmt: skip
    return _f(DAILY, "ok", f"{last:%a %d %b}")


def _prices(j: Journal, sess: Sequence[date], now: datetime) -> Fresh:
    last = _last_day(j, "store-refresh:")
    exp = _latest_session(sess, now, lambda s: _at(s, "22:35"))
    if last is None:
        return _f(PRICES, "new", "none yet")
    if exp is not None and last < exp:
        return _f(PRICES, "late", f"{last:%a %d %b}", f"no prices for {exp:%a %d %b}",
                  f"prices:late:{exp}")  # fmt: skip
    return _f(PRICES, "ok", f"{last:%a %d %b}")


def _backups(j: Journal, now: datetime) -> list[Fresh]:
    out = []
    for key, name, cadence, limit in (
        ("backup", "Nightly backup", "every night at 23:30", timedelta(hours=26)),
        ("restore", "Weekly restore test", "every Sunday 03:17", timedelta(days=8)),
    ):
        st = state(j, "backup-last" if key == "backup" else "restore-test-last")
        spec = (key, name, cadence)
        if not st or not isinstance(st[0], Mapping):
            out.append(_f(spec, "new", "not run yet", "starts once the server worker is installed"))
            continue
        rec, at = st
        if not rec.get("ok"):
            out.append(_f(spec, "failed", _ago(at, now), str(rec.get("error") or "see Backups")[:120],
                          f"{key}:failed:{at.isoformat()}"))  # fmt: skip
        elif now - at > limit:
            out.append(_f(spec, "late", _ago(at, now),
                          f"none since {at.astimezone(ASX_TZ):%a %d %b %H:%M}",
                          f"{key}:late:{at.isoformat()}"))  # fmt: skip
        else:
            out.append(_f(spec, "ok", _ago(at, now)))
    return out


def info_due(s: date) -> datetime:
    """The archive of session ``s`` is expected by 09:30 the next morning."""
    return _at(s + timedelta(days=1), "09:30")


def _info(j: Journal, sess: Sequence[date], now: datetime, enabled: bool) -> Fresh:
    if not enabled:
        return _f(INFO, "off", "switched off",
                  "switched on after the record moves to the server (after 30 Nov)")  # fmt: skip
    st = state(j, "info-archive-last")
    exp = _latest_session(sess, now, info_due)
    rec = st[0] if st and isinstance(st[0], Mapping) else {}
    last_day = _day(rec.get("day"))
    shown = f"{last_day:%a %d %b}" if last_day else "none yet"
    if st and not rec.get("ok"):
        return _f(INFO, "failed", _ago(st[1], now), str(rec.get("error") or "see Health")[:120],
                  f"info:failed:{st[1].isoformat()}")  # fmt: skip
    if exp is not None and (last_day is None or last_day < exp):
        return _f(INFO, "late", shown, f"no announcements stored for {exp:%a %d %b} (a missed "
                  "day cannot be collected later)", f"info:late:{exp}")  # fmt: skip
    return _f(INFO, "ok", shown)


def _twin(j: Journal, now: datetime) -> Fresh | None:
    st = state(j, "prev-twin")
    if not (st and isinstance(st[0], Mapping) and st[0].get("since")):
        return None
    rec, at = st
    if not rec.get("ok", True):
        return _f(TWIN, "failed", _ago(at, now), str(rec.get("error") or "")[:120],
                  f"twin:failed:{at.isoformat()}")  # fmt: skip
    if now - at > TWIN_LATE:
        return _f(TWIN, "late", _ago(at, now), "", f"twin:late:{at.isoformat()}")
    return _f(TWIN, "ok", _ago(at, now))


def freshness(j: Journal, book: str, sessions: Sequence[date], now: datetime,
              info_enabled: bool = False) -> list[Fresh]:  # fmt: skip
    """Each scheduled job against its expected cadence: the trader's daily run, the
    price download, the nightly backup, the weekly restore test and (when switched on)
    the info archive and the previous-version twin. Each job is checked on its own: if
    the monitor cannot read one, that job says so (failed, ``monitor:`` incident) and
    the others still run (BF-D81, review S4)."""
    today = now.astimezone(ASX_TZ).date()
    sess = sorted(s for s in sessions if s <= today)
    out: list[Fresh] = []
    checks: list[tuple[tuple[str, str, str], Callable[[], list[Fresh]]]] = [
        (DAILY, lambda: [_daily(j, book, sess, now)]),
        (PRICES, lambda: [_prices(j, sess, now)]),
        (("backup", "Backups", "nightly / weekly"), lambda: _backups(j, now)),
        (INFO, lambda: [_info(j, sess, now, info_enabled)]),
        (TWIN, lambda: [x for x in (_twin(j, now),) if x is not None]),
    ]
    for spec, fn in checks:
        try:
            out += fn()
        except Exception as e:  # one broken record never hides the other jobs
            out.append(_f(spec, "failed", "unknown", f"the monitor could not check it "
                          f"({type(e).__name__})", f"monitor:{spec[0]}:{today}"))  # fmt: skip
    return out


# ---------------------------------------------------------------- the weekly digest (BF-D79)


@dataclass
class Digest:
    week_end: date
    week_start: date
    main: list[str] = field(default_factory=list)
    research: list[str] = field(default_factory=list)
    data: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    sentence: str = ""
    # the same facts as the lines above, kept as figures for the Digest screen (display only)
    board: Scoreboard | None = None
    week: tuple[Decimal, Decimal] | None = None
    lines: list[ResearchLine] | None = None

    def text(self) -> str:
        parts = [f"Weekly digest: week to {self.week_end:%a %d %b %Y}"]
        if self.sentence:
            parts.append(self.sentence)
        for head, lines in (("Main strategy", self.main), ("Research lines (information only, "
                            "unranked; " + LUCK + ")", self.research), ("Data collected",
                            self.data), ("Alerts this week", self.alerts),
                            ("Needs you", self.needs or ["Nothing."])):  # fmt: skip
            if lines:
                parts.append("")
                parts.append(head)
                parts += [f"- {x}" for x in lines]
        return "\n".join(parts)


def week_of(d: date) -> tuple[date, date]:
    """Monday..Friday of the week that holds ``d`` (a weekend goes to the week before)."""
    mon = d - timedelta(days=d.weekday())
    return mon, mon + timedelta(days=4)


def week_change(series: Sequence[tuple[date, Decimal]], index: Sequence[tuple[date, float]],
                friday: date) -> tuple[Decimal, Decimal] | None:  # fmt: skip
    """The book's change over the week and A200's change on the same money (before
    running costs)."""
    mon, fri = week_of(friday)
    before = [(d, v) for d, v in series if d < mon][-1:]
    week = before + [(d, v) for d, v in series if mon <= d <= fri]
    if len(week) < 2:
        return None
    d0, v0 = week[0]
    d1, v1 = week[-1]
    pts = sorted((d, x) for d, x in index if x > 0)
    a, b = _level_at(pts, d0), _level_at(pts, d1)
    if a is None or b is None:
        return None
    return v1 - v0, (v0 * Decimal(repr(b / a)) - v0).quantize(CENT)


def digest(
    j: Journal,
    book: str,
    friday: date,
    sb: Scoreboard | None,
    week: tuple[Decimal, Decimal] | None,
    lines: list[ResearchLine] | None,
    fresh: Sequence[Fresh],
    info_days: Sequence[date] = (),
    store_days: Sequence[date] = (),
    needs: Sequence[str] = (),
) -> Digest:
    mon, fri = week_of(friday)
    dg = Digest(fri, mon, board=sb, week=week, lines=lines)
    if sb is None:
        dg.main.append("The main strategy has not started yet.")
    else:
        dg.sentence = sb.sentence
        dg.main.append(f"Account {money(sb.value)}; {sb.basis} {money(sb.after_costs)} "
                       f"({pct(sb.mine_pct)} since {sb.start:%d %b %Y}).")  # fmt: skip
        if sb.a200 is not None:
            dg.main.append(f"Same money in A200: {money(sb.a200)} ({pct(sb.a200_pct)}). "
                           + sb.sentence)  # fmt: skip
        if week is not None:
            dg.main.append(f"This week: {money(week[0], True)} for the book against "
                           f"{money(week[1], True)} for A200 (before running costs).")  # fmt: skip
    if lines is None:
        dg.research.append("The research record is not on this server yet.")
    else:
        for ln in lines:
            if ln.ret is None:
                dg.research.append(f"{ln.name}: not started")
            else:
                dg.research.append(f"{ln.name}: {pct(ln.ret)} since start, "
                                   f"{pct(ln.vs_a200)} against A200")  # fmt: skip
    wk = [d for d in store_days if mon <= d <= fri]
    dg.data.append(f"Prices: {plural(len(wk), 'trading day')} downloaded this week.")
    ia = [d for d in info_days if mon <= d <= fri]
    dg.data.append(f"Announcements archive: {plural(len(ia), 'day')} stored this week."
                   if info_days else "Announcements archive: not collecting yet.")  # fmt: skip
    from trader.app_store import inbox_rows

    try:
        rows = inbox_rows(j, 300, ("page",))
    except Exception:
        rows = []
    a = datetime.combine(mon, time(0, 0), ASX_TZ)
    b = datetime.combine(fri + timedelta(days=2), time(23, 59), ASX_TZ)
    pages = [r for r in rows if r["at"] is not None and a <= r["at"] <= b]
    dg.alerts = [f"{r['at'].astimezone(ASX_TZ):%a %H:%M}: {str(r['title'])[:100]}"
                 for r in pages[:8]]  # fmt: skip
    if len(pages) > 8:
        dg.alerts.append(f"... and {len(pages) - 8} more (Inbox)")
    dg.needs = [f"{f.name}: {f.status} ({f.detail or f.last})" for f in fresh if f.bad]
    dg.needs += list(needs)
    return dg
