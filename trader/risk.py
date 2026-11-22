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
L10 order value       buy value at limit <= ``order_value_max_aud`` (the L15     REJECT
                      fund order: ``fund_order_max_aud``, paged above the first)
BW-RSK-06 particip.   qty x ref <= ``participation_max`` x ``tv_med20``          CLIP
L5 min parcel         a clipped buy under A$500                                  REJECT
L10 orders a day      buys <= start/normal limit (sells never count); every order REJECT+PAGE
                      <= BW-RSK-09 hard 80 (only this one latches HALTED_BUYS)
L10 buys a day        value <= start/normal limit                                REJECT
BW-RSK-11 cash        buy cost (limit + commission) <= settled cash              CLIP/REJECT
L1 capital cap        holdings at cost + buys <= ``capital_cap_aud``             REJECT
====================  =========================================================  ===========

Book monitors (``evaluate_book``): L11 staged loss rule (owner, 19 Nov 2026; report 88
§4.2; ``trader.loss_rule``): below A$7,000 high-priority page and integrity check, below
A$6,000 ``HALTED_BUYS`` until the next month-end decision (automatic resume unless the
staged test fails), below A$5,000 the same plus the owner's written confirmation (else
wind-down over two decisions); BW-RSK-20 drawdown (30% WARN, 50% halt buys), BW-RSK-22 /
L11 one-day fall (7% WARN, 12% halt buys), BW-RSK-29 real money below 60% of capital.
A halt never sells by itself; sells continue under every book-monitor halt.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from enum import StrEnum

from trader.loss_rule import stage_of
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
    # L15 / BF-D28: the single fund order of the band-trend switch (flag ``FUND``) has its
    # own limit (the capital cap by default) and is paged above ``order_value_max_aud``
    fund_order_max_aud: Decimal = Decimal(10000)
    orders_per_day_start: int = 24
    orders_per_day_normal: int = 20  # review H6: buys only; 18 must fit
    orders_per_day_hard: int = 80  # BW-RSK-09
    buys_per_day_start_aud: Decimal = Decimal(10500)
    buys_per_day_normal_aud: Decimal = Decimal(10500)  # review H6: a whole book of buys
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
    # BF-D34: the fund's own cost; a FUND-flagged buy is capped on it (the shares still
    # held in FUND state are being sold); None = the whole book's cost as for any buy
    fund_cost: Decimal | None = None
    quotes: Mapping[str, Quote] = field(default_factory=dict)
    blocked: frozenset[str] = frozenset()
    orders_sent_today: int = 0
    buys_sent_today_aud: Decimal = Decimal(0)
    buy_orders_sent_today: int = 0  # review H6: only buys count against the L10 limit
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
        self.fund_cost = ctx.fund_cost
        self.sold: dict[str, int] = {}  # review L1: sells of each name so far in this plan
        self.buy_orders = ctx.buy_orders_sent_today  # review H6: only buys count (L10)


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
        return Verdict.REJECT, "NO_SHORT"  # (the running count per name: check_intents)
    max_value = lim.fund_order_max_aud if "FUND" in it.flags else lim.order_value_max_aud
    if buy and it.value_at_limit > max_value:
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
        # review L1: two sells of one name in a plan cannot oversell it
        if cur.side is Side.SELL and (
            day.sold.get(cur.entity, 0) + cur.qty > ctx.positions.get(cur.entity, 0)
        ):
            pages.append(f"NO_SHORT: sells of {cur.entity} in this batch exceed the position")
            out.append(RiskResult(it, Verdict.REJECT, ("NO_SHORT",)))
            continue
        if cur.side is Side.SELL and cur.value_at_limit > lim.order_value_max_aud:
            pages.append(f"sell {cur.entity} A${cur.value_at_limit} above the L10 order limit")
            reasons.append("SELL_ABOVE_ORDER_LIMIT")
        if "FUND" in cur.flags and cur.value_at_limit > lim.order_value_max_aud:
            pages.append(
                f"fund buy {cur.entity} A${cur.value_at_limit} above the L10 share-order limit "
                "(L15 band-trend switch, BF-D28)"
            )
            reasons.append("FUND_ABOVE_ORDER_LIMIT")
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
            base = day.cost
            if "FUND" in cur.flags and day.fund_cost is not None:
                base = day.fund_cost  # BF-D34
            if base + cur.value_at_limit > lim.capital_cap_aud:
                out.append(RiskResult(it, Verdict.REJECT, ("CAPITAL_CAP",)))
                continue
        # review H6: sells (C6 / L11 wind-down / forced) never count against the L10
        # orders limit and are never stopped by it; buys over it are rejected and paged,
        # without latching HALTED_BUYS (BW-RSK-09's hard limit still counts every order)
        over_hard = day.orders + 1 > lim.orders_per_day_hard
        if over_hard or (cur.side is Side.BUY and day.buy_orders + 1 > per_day):
            if "MAX_ORDERS" not in {r for res in out for r in res.reasons}:
                lab = lim.orders_per_day_hard if over_hard else per_day
                pages.append(f"orders-per-day limit {lab} reached; the rest of the buys rejected")
            if over_hard:
                latch = SafetyLevel.HALTED_BUYS if latch is None else latch  # BW-RSK-09
            out.append(RiskResult(it, Verdict.REJECT, ("MAX_ORDERS",)))
            continue
        day.orders += 1
        if cur.side is Side.SELL:
            day.sold[cur.entity] = day.sold.get(cur.entity, 0) + cur.qty
        if cur.side is Side.BUY:
            day.buy_orders += 1
            day.buys += cur.value_at_limit
            day.cash -= cur.value_at_limit + ctx.commission(cur.value_at_limit)
            day.cost += cur.value_at_limit
            if day.fund_cost is not None and "FUND" in cur.flags:
                day.fund_cost += cur.value_at_limit
        verdict = Verdict.CLIP if cur.qty != it.qty else Verdict.PASS
        out.append(RiskResult(cur, verdict, tuple(reasons)))
    return RiskReport(tuple(out), tuple(pages), latch)


@dataclass(frozen=True)
class BookReading:
    level: SafetyLevel
    alerts: tuple[str, ...]
    halts: tuple[str, ...] = ()  # the halt rules in breach (``L11_S2``, ``RSK20``, ...)
    stage: int = 0  # L11 staged loss rule: 0 none, 1 < A$7,000, 2 < A$6,000, 3 < A$5,000


def evaluate_book(
    value: Decimal,
    peak: Decimal,
    previous_value: Decimal | None,
    capital_in: Decimal,
    lim: RiskLimits | None = None,
) -> BookReading:
    """L11 / BW-RSK-20, -22, -29 after each broker day. Returns the level to latch
    (never lower than NORMAL; the caller keeps the worse of this and the current), the
    halt rules in breach (the caller latches each once per breach) and the L11 stage.
    The staged rule's resume / wind-down happens at the decision (``trader.loss_rule``);
    a halt never sells by itself."""
    lim = lim or RiskLimits()
    alerts: list[str] = []
    halts: list[str] = []
    level = SafetyLevel.NORMAL
    stage = stage_of(value, lim.value_review_aud, lim.value_halt_buys_aud, lim.value_line_halt_aud)
    if stage >= 2:
        level = SafetyLevel.HALTED_BUYS
        halts.append("L11_S2")
    if stage == 3:
        halts.append("L11_S3")
        alerts.append(
            f"PAGE: value A${value} < A${lim.value_line_halt_aud}: L11 stage 3, new buys "
            "paused; your written /continue <code> is needed before the next decision, "
            "else the book is sold over two decisions"
        )
    elif stage == 2:
        alerts.append(
            f"PAGE: value A${value} < A${lim.value_halt_buys_aud}: L11 stage 2, new buys "
            "paused until the next month-end decision (automatic resume unless the test "
            "fails); holdings kept, sells continue"
        )
    elif stage == 1:
        alerts.append(
            f"PAGE: value A${value} < A${lim.value_review_aud}: L11 stage 1, alert and "
            "integrity check"
        )
    if capital_in > 0 and value < capital_in * lim.real_money_floor:
        level = worst(level, SafetyLevel.HALTED_BUYS)
        halts.append("RSK29")
        alerts.append("PAGE: value below 60% of capital put in (BW-RSK-29)")
    if peak > 0:
        dd = 1 - value / peak
        if dd >= lim.drawdown_halt:
            level = worst(level, SafetyLevel.HALTED_BUYS)
            halts.append("RSK20")
            alerts.append(f"PAGE: drawdown {dd:.1%} >= {lim.drawdown_halt:.0%} (BW-RSK-20)")
        elif dd >= lim.drawdown_review:
            alerts.append(f"WARN: drawdown {dd:.1%} >= {lim.drawdown_review:.0%} (BW-RSK-20)")
    if previous_value is not None and previous_value > 0:
        mv = value / previous_value - 1
        if mv <= lim.day_move_halt:
            level = worst(level, SafetyLevel.HALTED_BUYS)
            halts.append("L11_DAY")
            alerts.append(f"PAGE: one-day fall {mv:.1%} (L11)")
        elif mv <= lim.day_move_review:
            alerts.append(f"WARN: one-day fall {mv:.1%} (BW-RSK-22)")
    return BookReading(level, tuple(alerts), tuple(halts), stage)
