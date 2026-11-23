"""The honest scoreboard, running costs, research lines, job freshness and the weekly
digest (BF-D75..BF-D80). Read-only computations over what the trader already records;
the phone app shows them and the trader's hooks (``trader.ops_hooks``) push the alerts
and file the digest.

Nothing here changes the strategy, a paper line, an order or a limit.
"""

from __future__ import annotations

import csv
import math
import re
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
# registered order (never ranked): (id, plain name, book-name patterns in the record's scorecard)
KEPT_LINES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("REF", "Reference book (EMG2-18, no shield)", (r"^EMG2_18_REF$", r"^EMG2_18_REF_")),
    ("EMG2", "EMG2 (the first challenger)", (r"^EMG2_\d+k",)),
    ("H82", "Large-Cap Core", (r"^H82_",)),
    ("MOM", "Plain momentum", (r"^MOM_",)),
    ("BLIND3", "Steady Momentum", (r"BLIND3",)),
    ("SWEEP", "Main line, one change: SWEEP", (r"_SWEEP$",)),
    ("WIDE", "Main line, one change: WIDE", (r"_WIDE$",)),
    ("FIP", "Main line, one change: FIP", (r"_FIP$",)),
    ("MOON_TOP5", "Aggressive: MOON TOP5", (r"MOON_TOP5",)),
    ("MOON_NOLOT5", "Aggressive: MOON NOLOT5", (r"MOON_NOLOT5",)),
    ("MOON_LEG2", "Aggressive: MOON LEG2", (r"MOON_LEG2",)),
)
RETIRED_LINES = ("H6", "COMBO", "SIM_BT", "PAIR", "EARLY", "ACC", "M3", "E3", "CXL")
RETIRED_ON = date(2026, 12, 31)
LUCK = "mostly luck at this stage"
# Research gap review (ledger seq 90): the 2018-26 replay with the live A$10k cap and rule 14
BACKTEST_NOTE = ("Backtest 2018–26 with the live $10,000 cap and rule 14: $21.0k against $18.6k "
                 "for the fund, before fixed costs (research gap review). An earlier, uncapped "
                 "figure of $34.5k is not what this book can do.")  # fmt: skip


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


# ---------------------------------------------------------------- running costs (BF-D76)

COST_KEYS = (("server", "Server (BinaryLane)"), ("data", "Price data (EODHD)"),
             ("other", "Other (tools, subscriptions)"))  # fmt: skip


@dataclass(frozen=True)
class FixedCosts:
    items: tuple[tuple[str, str, Decimal], ...]  # (key, label, A$ a year)
    source: str  # "app" (edited on the phone) | "config" | "total"

    @property
    def per_year(self) -> Decimal:
        return sum((a for _, _, a in self.items), Decimal(0))


def fixed_costs(j: Journal | None, cfg_items: Mapping[str, Decimal] | None,
                total: Decimal) -> FixedCosts:  # fmt: skip
    """The fixed running costs a year: the amounts edited in the app (state
    ``running-costs``), else ``running_costs`` of the config, else the single
    ``costs.fixed_aud_per_year``."""
    st = state(j, "running-costs") if j is not None else None
    if st and isinstance(st[0], Mapping) and st[0]:
        try:
            return FixedCosts(tuple((k, lab, Decimal(str(st[0].get(k, 0) or 0)))
                                    for k, lab in COST_KEYS), "app")  # fmt: skip
        except ArithmeticError:
            pass
    if cfg_items and any(Decimal(str(v)) > 0 for v in cfg_items.values()):
        return FixedCosts(tuple((k, lab, Decimal(str(cfg_items.get(k, 0))))
                                for k, lab in COST_KEYS), "config")  # fmt: skip
    return FixedCosts((("total", "Fixed costs (server, data, tools)", Decimal(total)),), "total")


@dataclass
class CostRow:
    label: str  # "Nov 2026", "This financial year"
    start: date
    end: date
    brokerage: Decimal = Decimal(0)
    spread: Decimal = Decimal(0)
    fixed: Decimal = Decimal(0)
    fixed_items: dict[str, Decimal] = field(default_factory=dict)
    account: Decimal | None = None  # account value at the end of the period

    @property
    def total(self) -> Decimal:
        return self.brokerage + self.spread + self.fixed

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
    annual_pct: float | None


def _fixed_between(fc: FixedCosts, a: date, b: date) -> dict[str, Decimal]:
    days = Decimal(max(0, (b - a).days + 1))
    return {k: (amt * days / Decimal(365)).quantize(CENT) for k, _, amt in fc.items}


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
    for this financial year and since the start; each also as a share of the account."""
    if start is None:
        start = series[0][0] if series else None
    if start is None:
        return None
    end = max(today, start)

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
        r.fixed_items = _fixed_between(fc, a, b) if b >= a else {}
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
    ann = None
    if since.account:  # fixed costs a year, plus the trading costs scaled to a year only
        # after a full year (the first buys are not repeated every month)
        trading = since.brokerage + since.spread
        ann = float(fc.per_year / since.account) + float(trading / since.account) * 365 / max(
            days, 365
        )
    return CostReport(months[::-1], ytd, since, fc, half_spread, cost_verdict(ann, since, fc), ann)


def cost_verdict(annual: float | None, since: CostRow, fc: FixedCosts) -> str:
    if annual is None:
        return "No costs yet: the book has not started."
    fixed_share = float(since.fixed / since.total) if since.total else 0.0
    lead = ("Fixed costs are most of it" if fixed_share > 0.5
            else "Trading costs are most of it")  # fmt: skip
    if annual >= 0.05:
        return (f"High: about {annual * 100:.1f}% of the account a year. {lead}; the strategy "
                "has to beat the fund by more than this just to break even.")  # fmt: skip
    if annual >= 0.02:
        return f"Noticeable: about {annual * 100:.1f}% of the account a year. {lead}."
    return f"Low: about {annual * 100:.1f}% of the account a year."


# ---------------------------------------------------------------- the honest scoreboard (BF-D75)


@dataclass
class Scoreboard:
    start: date
    end: date
    capital: Decimal
    value: Decimal  # account value: brokerage and the real spread are already inside it
    fixed: Decimal  # fixed running costs since the start (pro rata)
    tax: Decimal | None  # estimated tax on gains already realised (None: not modelled)
    a200: Decimal | None  # the same money put into A200 on the first day, held
    a200_cost: Decimal  # A200's own one buy: brokerage + half the spread

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
    def sentence(self) -> str:
        g = self.gap
        if g is None:
            return "The A200 comparison is not available yet (no fund prices in the store)."
        if abs(g) < 1:
            return "Level with A200 after all costs."
        word = "Ahead of" if g > 0 else "Behind"
        return f"{word} A200 by {money(abs(g))} after all costs."


def scoreboard(
    series: Sequence[tuple[date, Decimal]],
    index: Sequence[tuple[date, float]],
    capital: Decimal,
    fixed_per_year: Decimal,
    a200_cost: Decimal = Decimal(0),
    tax: Decimal | None = None,
) -> Scoreboard | None:
    """The main line's account value after every cost against the same money in A200.
    ``index``: A200's total-return level over the same days (any base)."""
    if not series or not capital:
        return None
    d0, d1 = series[0][0], series[-1][0]
    fixed = (fixed_per_year * Decimal((d1 - d0).days + 1) / Decimal(365)).quantize(CENT)
    a200 = None
    pts = [(d, x) for d, x in index if d0 <= d <= d1 and x > 0]
    if len(pts) > 1:
        ratio = Decimal(repr(pts[-1][1] / pts[0][1]))
        a200 = ((capital - a200_cost) * ratio).quantize(CENT)
    elif len(pts) == 1:
        a200 = (capital - a200_cost).quantize(CENT)
    return Scoreboard(d0, d1, capital, series[-1][1], fixed, tax, a200, a200_cost)


# ---------------------------------------------------------------- research lines (BF-D75)


@dataclass(frozen=True)
class ResearchLine:
    id: str
    name: str
    book: str | None  # the record's book shown (closest to A$10,000)
    capital: float | None
    nav: float | None
    ret: float | None  # since start (the record's own costs; no fixed costs)
    vs_a200: float | None
    asof: str = ""


def research_lines(scorecard: Path | None, today: date) -> list[ResearchLine] | None:
    """The kept research lines from the research record's ``paper/scorecard_latest.csv``
    (mounted read-only), in the registered order, never ranked. None: no record here."""
    if scorecard is None or not scorecard.is_file():
        return None
    try:
        with scorecard.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
    except (OSError, csv.Error):
        return None
    out = []
    for lid, name, pats in KEPT_LINES:
        hit = [r for r in rows if any(re.search(p, r.get("book", "")) for p in pats)
               and "random" not in r.get("kind", "").lower()
               and "comparator" not in r.get("kind", "").lower()]  # fmt: skip
        if not hit:
            out.append(ResearchLine(lid, name, None, None, None, None, None))
            continue
        best = min(hit, key=lambda r: abs((_fl(r.get("capital")) or 0) - 10000))
        out.append(ResearchLine(lid, name, best.get("book"), _fl(best.get("capital")),
                                _fl(best.get("nav")), _fl(best.get("return_since_start")),
                                _fl(best.get("vs_a200")), best.get("asof", "")))  # fmt: skip
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
    status: str  # ok | late | failed | off
    last: str  # plain words
    detail: str = ""
    incident: str = ""  # unique per incident (one push each); "" when ok / off

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


def freshness(  # noqa: PLR0912, PLR0915 - one block per job
    j: Journal, book: str, sessions: Sequence[date], now: datetime,
              info_enabled: bool = False) -> list[Fresh]:  # fmt: skip
    """Each scheduled job against its expected cadence: the trader's daily run, the
    price download, the nightly backup, the weekly restore test and (when switched on)
    the info archive and the previous-version twin."""
    out: list[Fresh] = []
    today = now.astimezone(ASX_TZ).date()
    sess = sorted(s for s in sessions if s <= today)
    # 1. the trader's daily run (the 22:45 report writes value:<book>:<day>)
    vals = job_rows(j, f"value:{book}:", 1)
    exp = _latest_session(sess, now, lambda s: _at(s, "23:30"))
    if not vals:
        out.append(Fresh("daily", "Trader daily run", "every ASX day by 22:45", "off",
                         "not started yet"))  # fmt: skip
    else:
        last = date.fromisoformat(vals[-1][0].rsplit(":", 1)[1])
        err = None
        if exp is not None:
            rep = job_rows(j, f"{exp}:22:45:report", 1)
            if rep and isinstance(rep[-1][1], dict) and rep[-1][1].get("error"):
                err = str(rep[-1][1]["error"])[:120]
        if err:
            out.append(Fresh("daily", "Trader daily run", "every ASX day by 22:45", "failed",
                             f"{last:%a %d %b}", f"the report of {exp:%a %d %b} failed: {err}",
                             f"daily:failed:{exp}"))  # fmt: skip
        elif exp is not None and last < exp:
            out.append(Fresh("daily", "Trader daily run", "every ASX day by 22:45", "late",
                             f"{last:%a %d %b}", f"no daily report for {exp:%a %d %b}",
                             f"daily:late:{exp}"))  # fmt: skip
        else:
            out.append(Fresh("daily", "Trader daily run", "every ASX day by 22:45", "ok",
                             f"{last:%a %d %b}"))  # fmt: skip
    # 2. the price download (store refresh, slots 17:35..22:05)
    sr = job_rows(j, "store-refresh:", 1)
    exp = _latest_session(sess, now, lambda s: _at(s, "22:35"))
    if not sr:
        out.append(Fresh("prices", "Price download (EODHD)", "every ASX day by 22:05", "off",
                         "none yet"))  # fmt: skip
    else:
        last = date.fromisoformat(sr[-1][0].split(":", 1)[1][:10])
        if exp is not None and last < exp:
            out.append(Fresh("prices", "Price download (EODHD)", "every ASX day by 22:05",
                             "late", f"{last:%a %d %b}", f"no prices for {exp:%a %d %b}",
                             f"prices:late:{exp}"))  # fmt: skip
        else:
            out.append(Fresh("prices", "Price download (EODHD)", "every ASX day by 22:05",
                             "ok", f"{last:%a %d %b}"))  # fmt: skip
    # 3. / 4. the nightly backup and the weekly restore test (BF-D64)
    for key, name, cadence, limit in (
        ("backup", "Nightly backup", "every night at 23:30", timedelta(hours=26)),
        ("restore", "Weekly restore test", "every Sunday 03:17", timedelta(days=8)),
    ):
        st = state(j, "backup-last" if key == "backup" else "restore-test-last")
        if not st or not isinstance(st[0], Mapping):
            out.append(Fresh(key, name, cadence, "off", "not run yet",
                             "starts once the server worker is installed"))  # fmt: skip
            continue
        rec, at = st
        if not rec.get("ok"):
            out.append(Fresh(key, name, cadence, "failed", _ago(at, now),
                             str(rec.get("error") or "see Backups")[:120],
                             f"{key}:failed:{at.isoformat()}"))  # fmt: skip
        elif now - at > limit:
            out.append(Fresh(key, name, cadence, "late", _ago(at, now),
                             f"none since {at.astimezone(ASX_TZ):%a %d %b %H:%M}",
                             f"{key}:late:{at.isoformat()}"))  # fmt: skip
        else:
            out.append(Fresh(key, name, cadence, "ok", _ago(at, now)))
    # 5. the private info archive (BF-D78), once switched on
    st = state(j, "info-archive-last")
    if not info_enabled:
        out.append(Fresh("info", "Info archive (announcements)", "every ASX day, next morning",
                         "off", "switched off", "switched on after the record moves "
                         "to the server (after 30 Nov)"))  # fmt: skip
    else:
        exp = _latest_session(sess, now, lambda s: _at(s + timedelta(days=1), "09:30"))
        rec = st[0] if st and isinstance(st[0], Mapping) else {}
        last_day = _day(rec.get("day"))
        if st and not rec.get("ok"):
            out.append(Fresh("info", "Info archive (announcements)", "every ASX day, next "
                             "morning", "failed", _ago(st[1], now),
                             str(rec.get("error") or "see Health")[:120],
                             f"info:failed:{st[1].isoformat()}"))  # fmt: skip
        elif exp is not None and (last_day is None or last_day < exp):
            out.append(Fresh("info", "Info archive (announcements)", "every ASX day, next "
                             "morning", "late", f"{last_day:%a %d %b}" if last_day else "none yet",
                             f"no announcements stored for {exp:%a %d %b}", f"info:late:{exp}"))  # fmt: skip
        else:
            out.append(Fresh("info", "Info archive (announcements)", "every ASX day, next "
                             "morning", "ok", f"{last_day:%a %d %b}" if last_day else "-"))  # fmt: skip
    # 6. the previous-version twin (BF-D80), only after a strategy update
    st = state(j, "prev-twin")
    if st and isinstance(st[0], Mapping) and st[0].get("since"):
        rec, at = st
        if not rec.get("ok", True):
            out.append(Fresh("twin", "Previous-version twin", "every night", "failed",
                             _ago(at, now), str(rec.get("error") or "")[:120],
                             f"twin:failed:{at.isoformat()}"))  # fmt: skip
        elif now - at > timedelta(hours=50):
            out.append(Fresh("twin", "Previous-version twin", "every night", "late",
                             _ago(at, now), "", f"twin:late:{at.isoformat()}"))  # fmt: skip
        else:
            out.append(Fresh("twin", "Previous-version twin", "every night", "ok", _ago(at, now)))
    return out


def _day(x: object) -> date | None:
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


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

    def text(self) -> str:
        parts = [f"Weekly digest: week to {self.week_end:%a %d %b %Y}"]
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


def digest(
    j: Journal,
    book: str,
    friday: date,
    sb: Scoreboard | None,
    week_sb: Scoreboard | None,
    lines: list[ResearchLine] | None,
    fresh: Sequence[Fresh],
    info_days: Sequence[date] = (),
    store_days: Sequence[date] = (),
    needs: Sequence[str] = (),
) -> Digest:
    mon, fri = week_of(friday)
    dg = Digest(fri, mon)
    if sb is None:
        dg.main.append("The main strategy has not started yet.")
    else:
        dg.main.append(f"Account {money(sb.value)}; after all costs {money(sb.after_costs)} "
                       f"({pct(sb.mine_pct)} since {sb.start:%d %b %Y}).")  # fmt: skip
        if sb.a200 is not None:
            dg.main.append(f"Same money in A200: {money(sb.a200)} ({pct(sb.a200_pct)}). "
                           + sb.sentence)  # fmt: skip
        if week_sb is not None and week_sb.gap is not None and sb.gap is not None:
            dg.main.append(f"This week: {money(week_sb.value - week_sb.capital, True)} for the "
                           f"book against {money(week_sb.a200 - week_sb.capital, True)} for A200 "  # type: ignore[operator]
                           "(before fixed costs).")  # fmt: skip
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
    dg.data.append(f"Prices: {len(wk)} trading day(s) downloaded this week.")
    ia = [d for d in info_days if mon <= d <= fri]
    dg.data.append(f"Announcements archive: {len(ia)} day(s) stored this week." if info_days
                   else "Announcements archive: not collecting yet.")  # fmt: skip
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
    dg.needs = [f"{f.name}: {f.status} ({f.detail or f.last})" for f in fresh if f.bad] + list(
        needs
    )
    return dg
