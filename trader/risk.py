"""The breaker (FD v3.0 §10; EMG2-20 L10-L11; BF2). Pure and independent of every line.

It only blocks, clips or halts; it never creates or reshapes a portfolio (§10). It
runs at plan time and again at send time on the same intents (BW-RSK checks are
"plan time and send time").

Per-order checks, in this order, with running day counters (sells first):

====================  =========================================================  ===========
Check                 Limit                                                      Action
====================  =========================================================  ===========
BW-RSK-01 safety      ``KILLED``/``HALTED_INTEGRITY``/``HALTED_LINE``: all;        REJECT
                      ``PAUSED``/``HALTED_BUYS``: buys (sells proceed)
stale data            decision data older than the expected session; a quote     REJECT
                      older than ``quote_stale_minutes``
BW-RSK-02 eligible    entity blocked (verdict BLOCK, suspended, frozen)          REJECT
price sanity          ref > 0; last within ``absurd_move`` of the previous close  REJECT
BW-RSK-08 gap         last more than ``gap_hold`` from previous close            buy HOLD
BW-RSK-07 / L7 band   limit within ``price_band`` of the reference, valid step    REJECT
BW-RSK-03 no short    sell qty <= broker position                                REJECT+PAGE
L10 order value       buy value at limit <= ``order_value_max_aud``              REJECT
BW-RSK-06 particip.   qty x ref <= ``participation_max`` x ``tv_med20``          CLIP
L5 min parcel         a clipped buy under A$500                                  REJECT
L10 orders a day      <= start/normal limit and <= BW-RSK-09 hard 80             REJECT+PAGE
L10 buys a day        value <= start/normal limit                                REJECT
BW-RSK-11 cash        buy cost (limit + commission) <= settled cash              CLIP/REJECT
L1 capital cap        holdings at cost + buys <= ``capital_cap_aud``             REJECT
====================  =========================================================  ===========

Book monitors (``evaluate_book``): L11 value floors (A$7,000 review, A$6,000
``HALTED_BUYS``, A$5,000 line halt), BW-RSK-20 drawdown (30% WARN, 50% halt
buys), BW-RSK-22 / L11 one-day fall (7% WARN, 12% halt buys), BW-RSK-29 real money
below 60% of capital. A halt never sells by itself.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from enum import StrEnum

from trader.orders import CommissionModel, OrderIntent, Side, is_valid_step

CENT = Decimal("0.01")


class SafetyLevel(StrEnum):
    NORMAL = "NORMAL"
    PAUSED = "PAUSED"  # /pause: buys stop, registered sells proceed
    HALTED_BUYS = "HALTED_BUYS"
    HALTED_LINE = "HALTED_LINE"
    HALTED_INTEGRITY = "HALTED_INTEGRITY"
    KILLED = "KILLED"  # /kill: all new orders stop, open orders cancelled


BLOCKS_ALL = frozenset({SafetyLevel.KILLED, SafetyLevel.HALTED_INTEGRITY, SafetyLevel.HALTED_LINE})
BLOCKS_BUYS = BLOCKS_ALL | {SafetyLevel.PAUSED, SafetyLevel.HALTED_BUYS}
SEVERITY = {
    SafetyLevel.NORMAL: 0, SafetyLevel.PAUSED: 1, SafetyLevel.HALTED_BUYS: 2,
    SafetyLevel.HALTED_LINE: 3, SafetyLevel.HALTED_INTEGRITY: 4, SafetyLevel.KILLED: 5,
}  # fmt: skip


def worst(a: SafetyLevel, b: SafetyLevel) -> SafetyLevel:
    return a if SEVERITY[a] >= SEVERITY[b] else b


class Verdict(StrEnum):
    PASS = "PASS"  # noqa: S105 - a verdict, not a password
    CLIP = "CLIP"
    HOLD = "HOLD"  # not today; retry next session
    REJECT = "REJECT"


@dataclass(frozen=True)
class RiskLimits:
    """EMG2-20 live-book limits (config ``live_emg2_20``; FD §7.9 L10-L11, §10)."""

    order_value_max_aud: Decimal = Decimal(800)
    orders_per_day_start: int = 24
    orders_per_day_normal: int = 16
    orders_per_day_hard: int = 80  # BW-RSK-09
    buys_per_day_start_aud: Decimal = Decimal(10500)
    buys_per_day_normal_aud: Decimal = Decimal(4500)
    price_band: Decimal = Decimal("0.03")  # L7 band (BW-RSK-07 allows 5% for band C; L7 is tighter)
    gap_hold: Decimal = Decimal("0.15")
    absurd_move: Decimal = Decimal("0.60")
    participation_max: Decimal = Decimal("0.05")
    quote_stale_minutes: int = 40
    min_parcel_aud: Decimal = Decimal(500)
    capital_cap_aud: Decimal = Decimal(10000)
    # L11 / BW-RSK-20/22/29
    value_review_aud: Decimal = Decimal(7000)
    value_halt_buys_aud: Decimal = Decimal(6000)
    value_line_halt_aud: Decimal = Decimal(5000)
    drawdown_review: Decimal = Decimal("0.30")
    drawdown_halt: Decimal = Decimal("0.50")
    day_move_review: Decimal = Decimal("-0.07")
    day_move_halt: Decimal = Decimal("-0.12")
    real_money_floor: Decimal = Decimal("0.60")


@dataclass(frozen=True)
class Quote:
    last: Decimal
    prev_close: Decimal
    at: datetime  # UTC


@dataclass(frozen=True)
class RiskContext:
    now: datetime  # UTC
    session: date  # the execution session
    expected_data_date: date  # the decision session D whose closes the intents used
    data_as_of: date  # latest close the system holds
    safety: SafetyLevel
    start_day: bool  # L10 start-day limits (start decision and canary sessions)
    positions: Mapping[str, int]  # broker positions, units
    settled_cash: Decimal
    holdings_cost: Decimal = Decimal(0)  # at cost, for the capital cap
    quotes: Mapping[str, Quote] = field(default_factory=dict)
    blocked: frozenset[str] = frozenset()
    orders_sent_today: int = 0
    buys_sent_today_aud: Decimal = Decimal(0)
    commission: CommissionModel = field(default_factory=CommissionModel)


@dataclass(frozen=True)
class RiskResult:
    intent: OrderIntent  # possibly clipped
    verdict: Verdict
    reasons: tuple[str, ...]

    @property
    def sendable(self) -> bool:
        return self.verdict in (Verdict.PASS, Verdict.CLIP)


@dataclass(frozen=True)
class RiskReport:
    results: tuple[RiskResult, ...]
    pages: tuple[str, ...]
    latch: SafetyLevel | None  # a level the breaker asks the caller to persist

    @property
    def sendable(self) -> tuple[OrderIntent, ...]:
        return tuple(r.intent for r in self.results if r.sendable)


class _Day:
    def __init__(self, ctx: RiskContext) -> None:
        self.orders = ctx.orders_sent_today
        self.buys = ctx.buys_sent_today_aud
        self.cash = ctx.settled_cash
        self.cost = ctx.holdings_cost


def _pre_checks(  # noqa: PLR0911, PLR0912 - one return per breaker rule
    it: OrderIntent, ctx: RiskContext, lim: RiskLimits
) -> tuple[Verdict, str] | None:
    """Checks that do not depend on the running counters. None = passed."""
    buy = it.side is Side.BUY
    if ctx.safety in BLOCKS_ALL or (buy and ctx.safety in BLOCKS_BUYS):
        return Verdict.REJECT, f"SAFETY_{ctx.safety.value}"
    if ctx.data_as_of < ctx.expected_data_date:
        return Verdict.REJECT, "DATA_STALE"
    if it.entity in ctx.blocked:
        return Verdict.REJECT, "NOT_ELIGIBLE"
    q = ctx.quotes.get(it.entity)
    if q is not None:
        if ctx.now - q.at > timedelta(minutes=lim.quote_stale_minutes):
            return Verdict.REJECT, "QUOTE_STALE"
        if q.last <= 0 or q.prev_close <= 0:
            return Verdict.REJECT, "PRICE_SANITY"
        move = abs(q.last / q.prev_close - 1)
        if move > lim.absurd_move:
            return Verdict.REJECT, "PRICE_SANITY"
        if buy and move > lim.gap_hold:
            return Verdict.HOLD, "GAP_HOLD"
    prev = it.prev_close
    if prev is not None and prev > 0 and abs(it.ref_price / prev - 1) > lim.absurd_move:
        return Verdict.REJECT, "PRICE_SANITY"
    if abs(it.limit_price / it.ref_price - 1) > lim.price_band or not is_valid_step(it.limit_price):
        return Verdict.REJECT, "PRICE_BAND"
    if (buy and it.limit_price < it.ref_price) or (not buy and it.limit_price > it.ref_price):
        return Verdict.REJECT, "PRICE_BAND"
    if not buy and it.qty > ctx.positions.get(it.entity, 0):
        return Verdict.REJECT, "NO_SHORT"
    if buy and it.value_at_limit > lim.order_value_max_aud:
        return Verdict.REJECT, "MAX_ORDER_VALUE"
    return None


def _clip_qty(it: OrderIntent, qty: int) -> OrderIntent:
    return replace(it, qty=qty)


def check_intents(  # noqa: PLR0912, PLR0915 - one branch per breaker rule, kept flat for review
    intents: Sequence[OrderIntent], ctx: RiskContext, lim: RiskLimits | None = None
) -> RiskReport:
    """Apply every per-order check to a batch (sells first) with running counters."""
    lim = lim or RiskLimits()
    day = _Day(ctx)
    pages: list[str] = []
    latch: SafetyLevel | None = None
    out: list[RiskResult] = []
    per_day = min(
        lim.orders_per_day_start if ctx.start_day else lim.orders_per_day_normal,
        lim.orders_per_day_hard,
    )
    buy_cap = lim.buys_per_day_start_aud if ctx.start_day else lim.buys_per_day_normal_aud
    ordered = sorted(intents, key=lambda i: (i.side is Side.BUY, i.seq))
    for it in ordered:
        reasons: list[str] = []
        pre = _pre_checks(it, ctx, lim)
        if pre is not None:
            if pre[1] == "NO_SHORT":
                pages.append(f"NO_SHORT: sell {it.qty} {it.entity} > position")
            out.append(RiskResult(it, pre[0], (pre[1],)))
            continue
        cur = it
        if cur.side is Side.SELL and cur.value_at_limit > lim.order_value_max_aud:
            pages.append(f"sell {cur.entity} A${cur.value_at_limit} above the L10 order limit")
            reasons.append("SELL_ABOVE_ORDER_LIMIT")
        # BW-RSK-06 participation
        if cur.tv_med20 is None or cur.tv_med20 <= 0:
            if cur.side is Side.BUY:
                out.append(RiskResult(cur, Verdict.REJECT, ("NO_LIQUIDITY_DATA",)))
                continue
        else:
            cap_qty = int(
                (lim.participation_max * cur.tv_med20 / cur.ref_price).to_integral_value(ROUND_DOWN)
            )
            if cur.qty > cap_qty:
                cur = _clip_qty(cur, cap_qty) if cap_qty > 0 else cur
                reasons.append("PARTICIPATION")
                if cap_qty <= 0:
                    out.append(RiskResult(it, Verdict.REJECT, ("PARTICIPATION",)))
                    continue
        if cur.side is Side.BUY:
            cost = cur.value_at_limit + ctx.commission(cur.value_at_limit)
            if cost > day.cash:  # BW-RSK-11: scale down to settled cash
                budget = day.cash - ctx.commission(day.cash)
                q = (
                    int((budget / cur.limit_price).to_integral_value(ROUND_DOWN))
                    if budget > 0
                    else 0
                )
                if q <= 0:
                    out.append(RiskResult(it, Verdict.REJECT, ("CASH_SHORT",)))
                    continue
                cur = _clip_qty(cur, min(q, cur.qty))
                reasons.append("CASH_SHORT")
            if cur.value_at_ref < lim.min_parcel_aud:
                out.append(RiskResult(it, Verdict.REJECT, (*reasons, "MIN_PARCEL")))
                continue
            if day.buys + cur.value_at_limit > buy_cap:
                out.append(RiskResult(it, Verdict.REJECT, ("MAX_BUYS_PER_DAY",)))
                continue
            if day.cost + cur.value_at_limit > lim.capital_cap_aud:
                out.append(RiskResult(it, Verdict.REJECT, ("CAPITAL_CAP",)))
                continue
        if day.orders + 1 > per_day:
            if "MAX_ORDERS" not in {r for res in out for r in res.reasons}:
                pages.append(f"orders-per-day limit {per_day} reached; rest rejected")
            latch = SafetyLevel.HALTED_BUYS if latch is None else latch
            out.append(RiskResult(it, Verdict.REJECT, ("MAX_ORDERS",)))
            continue
        day.orders += 1
        if cur.side is Side.BUY:
            day.buys += cur.value_at_limit
            day.cash -= cur.value_at_limit + ctx.commission(cur.value_at_limit)
            day.cost += cur.value_at_limit
        verdict = Verdict.CLIP if cur.qty != it.qty else Verdict.PASS
        out.append(RiskResult(cur, verdict, tuple(reasons)))
    return RiskReport(tuple(out), tuple(pages), latch)


@dataclass(frozen=True)
class BookReading:
    level: SafetyLevel
    alerts: tuple[str, ...]


def evaluate_book(
    value: Decimal,
    peak: Decimal,
    previous_value: Decimal | None,
    capital_in: Decimal,
    lim: RiskLimits | None = None,
) -> BookReading:
    """L11 / BW-RSK-20, -22, -29 after each broker day. Returns the level to latch
    (never lower than NORMAL; the caller keeps the worse of this and the current)."""
    lim = lim or RiskLimits()
    alerts: list[str] = []
    level = SafetyLevel.NORMAL
    if value <= lim.value_line_halt_aud:
        level = SafetyLevel.HALTED_LINE
        alerts.append(f"PAGE: value A${value} <= A${lim.value_line_halt_aud}: line halted (L11)")
    elif value <= lim.value_halt_buys_aud:
        level = SafetyLevel.HALTED_BUYS
        alerts.append(f"PAGE: value A${value} <= A${lim.value_halt_buys_aud}: HALTED_BUYS (L11)")
    elif value <= lim.value_review_aud:
        alerts.append(f"PAGE: value A${value} <= A${lim.value_review_aud}: review (L11)")
    if capital_in > 0 and value < capital_in * lim.real_money_floor:
        level = worst(level, SafetyLevel.HALTED_BUYS)
        alerts.append("PAGE: value below 60% of capital put in (BW-RSK-29)")
    if peak > 0:
        dd = 1 - value / peak
        if dd >= lim.drawdown_halt:
            level = worst(level, SafetyLevel.HALTED_BUYS)
            alerts.append(f"PAGE: drawdown {dd:.1%} >= {lim.drawdown_halt:.0%} (BW-RSK-20)")
        elif dd >= lim.drawdown_review:
            alerts.append(f"WARN: drawdown {dd:.1%} >= {lim.drawdown_review:.0%} (BW-RSK-20)")
    if previous_value is not None and previous_value > 0:
        mv = value / previous_value - 1
        if mv <= lim.day_move_halt:
            level = worst(level, SafetyLevel.HALTED_BUYS)
            alerts.append(f"PAGE: one-day fall {mv:.1%} (L11)")
        elif mv <= lim.day_move_review:
            alerts.append(f"WARN: one-day fall {mv:.1%} (BW-RSK-22)")
    return BookReading(level, tuple(alerts))
