"""BF2: order builder and breaker (FD §7.9 L5-L11, §10, §11; §21.1 BF2)."""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from tests.bf_support import synthetic_panel
from trader.lines.emg2 import (
    BookState,
    BuyPlan,
    Emg2_20Decision,
    Emg2_20Params,
    SellPlan,
    decide_emg2_20,
)
from trader.orders import (
    CommissionModel,
    OrderIntent,
    OrderParams,
    OrderType,
    Side,
    build_orders,
    client_order_id,
    fallback_limit,
    is_valid_step,
    price_step,
    round_to_step,
)
from trader.risk import (
    Quote,
    RiskContext,
    RiskLimits,
    SafetyLevel,
    Verdict,
    check_intents,
    evaluate_book,
)

D = date(2026, 11, 30)
S = date(2026, 12, 1)
NOW = datetime(2026, 12, 1, 4, 30, tzinfo=UTC)


def _decision(
    buys: list[tuple[str, str, str]], sells: tuple[tuple[str, int, str], ...] = ()
) -> Emg2_20Decision:
    return Emg2_20Decision(
        "EMG2_20_PAPER",
        str(D),
        "x" * 64,
        None,
        Decimal(10000),
        20,
        Decimal(500),
        tuple(SellPlan(e, q, Decimal(p), "EMG2_OFF_LIST") for e, q, p in sells),
        tuple(BuyPlan(e, k + 1, Decimal(v), Decimal(p)) for k, (e, v, p) in enumerate(buys)),
        (),
        (),
    )


# ---------------------------------------------------------------- orders


def test_price_steps_and_rounding() -> None:
    assert price_step(Decimal("0.095")) == Decimal("0.001")
    assert price_step(Decimal("1.995")) == Decimal("0.005")
    assert price_step(Decimal("2.00")) == Decimal("0.01")
    assert round_to_step(Decimal("1.2378"), Side.BUY) == Decimal("1.235")
    assert round_to_step(Decimal("1.2378"), Side.SELL) == Decimal("1.24")
    assert is_valid_step(Decimal("1.235")) and not is_valid_step(Decimal("1.237"))


def test_commission_ibkr_fixed() -> None:
    c = CommissionModel()
    assert c(Decimal(500)) == Decimal("6.60") and c(Decimal(10000)) == Decimal("8.80")


def test_BW_EXE_06_client_order_id_deterministic() -> None:
    assert (
        client_order_id("EMG2_20_PAPER", D, "AVH", Side.BUY) == "EMG2_20_PAPER-2026-11-30-AVH-BUY-1"
    )
    with pytest.raises(ValueError):
        client_order_id("B", D, "X", Side.BUY, 0)


def test_L5_build_orders_whole_shares_sells_first_and_min_parcel() -> None:
    dec = _decision([("AAA", "560.00", "1.00"), ("BBB", "500.00", "2.50")], (("ZZZ", 300, "1.70"),))
    b = build_orders(dec, params=OrderParams(limit_band=Decimal("0.03")))
    assert [i.side for i in b.intents] == [Side.SELL, Side.BUY]
    sell, buy = b.intents
    assert sell.qty == 300 and sell.limit_price == Decimal("1.65") and sell.seq == 1
    # (560 - 6.60) / 1.03 -> 537 shares at limit 1.03; 537 x 1.00 >= 500
    assert buy.entity == "AAA" and buy.qty == 537 and buy.limit_price == Decimal("1.03")
    assert ("BBB", "MIN_PARCEL") in b.skipped  # 500 - 6.60 at 2.57 is under A$500 at the reference
    assert buy.order_type is OrderType.LOC and buy.client_order_id.endswith("AAA-BUY-1")
    assert b.digest == build_orders(dec, params=OrderParams(limit_band=Decimal("0.03"))).digest


def test_L5_orders_under_500_never_generated_property() -> None:
    rng = random.Random(5)
    for _ in range(300):
        buys = [
            (f"E{k}", f"{rng.uniform(400, 900):.2f}", f"{rng.uniform(0.1, 40):.3f}")
            for k in range(5)
        ]
        for it in build_orders(_decision(buys)).intents:
            assert it.value_at_ref >= 500 and it.qty >= 1 and is_valid_step(it.limit_price)


def test_L6_canary_is_one_buy_and_no_sells() -> None:
    dec = _decision([("AAA", "700", "1.00"), ("BBB", "700", "1.00")], (("ZZZ", 10, "100"),))
    b = build_orders(dec, canary=True)
    assert len(b.intents) == 1 and b.intents[0].entity == "AAA" and "CANARY" in b.intents[0].flags
    assert b.batch_id.endswith("-C")


def test_L7_fallback_limit() -> None:
    ref = Decimal("1.00")
    assert fallback_limit(Side.BUY, bid=None, ask=Decimal("1.005"), ref=ref) == Decimal("1.01")
    assert fallback_limit(Side.BUY, bid=None, ask=Decimal("1.20"), ref=ref) == Decimal("1.03")
    assert fallback_limit(Side.SELL, bid=Decimal("0.995"), ask=None, ref=ref) == Decimal("0.99")
    assert fallback_limit(Side.SELL, bid=Decimal("0.50"), ask=None, ref=ref) == Decimal("0.97")
    assert fallback_limit(Side.BUY, bid=None, ask=None, ref=ref) is None


def test_build_orders_from_engine_decision() -> None:
    p = synthetic_panel()
    dec = decide_emg2_20(
        p,
        BookState("EMG2_20_PAPER", Decimal(10600)),
        Emg2_20Params(
            skip_lottery=False, cash_reserve_aud=Decimal(0), capital_cap_aud=Decimal(10600)
        ),
    )
    b = build_orders(dec)
    assert b.intents and all(i.value_at_ref >= 500 for i in b.intents)


# ---------------------------------------------------------------- breaker


def _it(
    entity: str = "AAA",
    side: Side = Side.BUY,
    qty: int = 500,
    ref: str = "1.00",
    lim: str | None = None,
    tv20: str | None = "1000000",
    seq: int = 1,
) -> OrderIntent:
    refd = Decimal(ref)
    limd = (
        Decimal(lim)
        if lim
        else round_to_step(refd * (Decimal("1.02") if side is Side.BUY else Decimal("0.98")), side)
    )
    return OrderIntent(
        client_order_id("B", D, entity, side),
        "B-R",
        seq,
        "EMG2_20",
        "B",
        D,
        entity,
        side,
        qty,
        OrderType.LOC,
        refd,
        limd,
        "T",
        tv_med20=Decimal(tv20) if tv20 else None,
        prev_close=refd,
    )


def _ctx(**kw: object) -> RiskContext:
    base: dict[str, object] = dict(
        now=NOW,
        session=S,
        expected_data_date=D,
        data_as_of=D,
        safety=SafetyLevel.NORMAL,
        start_day=False,
        positions={"SSS": 1000},
        settled_cash=Decimal(10000),
    )
    base.update(kw)
    return RiskContext(**base)  # type: ignore[arg-type]


def _one(it: OrderIntent, **kw: object) -> tuple[Verdict, tuple[str, ...]]:
    r = check_intents([it], _ctx(**kw)).results[0]
    return r.verdict, r.reasons


def test_BW_RSK_01_kill_and_halts() -> None:
    buy, sell = _it(), _it("SSS", Side.SELL, 100)
    assert _one(buy)[0] is Verdict.PASS
    for lvl in (SafetyLevel.KILLED, SafetyLevel.HALTED_INTEGRITY, SafetyLevel.HALTED_LINE):
        assert (
            _one(buy, safety=lvl)[0] is Verdict.REJECT
            and _one(sell, safety=lvl)[0] is Verdict.REJECT
        )
    for lvl in (SafetyLevel.PAUSED, SafetyLevel.HALTED_BUYS):
        assert (
            _one(buy, safety=lvl)[0] is Verdict.REJECT and _one(sell, safety=lvl)[0] is Verdict.PASS
        )


def test_stale_data_and_quotes() -> None:
    assert _one(_it(), data_as_of=date(2026, 11, 27)) == (Verdict.REJECT, ("DATA_STALE",))
    old = Quote(Decimal(1), Decimal(1), NOW - timedelta(minutes=41))
    assert _one(_it(), quotes={"AAA": old}) == (Verdict.REJECT, ("QUOTE_STALE",))
    fresh = Quote(Decimal(1), Decimal(1), NOW - timedelta(minutes=5))
    assert _one(_it(), quotes={"AAA": fresh})[0] is Verdict.PASS


def test_BW_RSK_02_not_eligible() -> None:
    assert _one(_it(), blocked=frozenset({"AAA"})) == (Verdict.REJECT, ("NOT_ELIGIBLE",))


def test_price_sanity_and_BW_RSK_08_gap_hold() -> None:
    def q(last: str) -> dict[str, Quote]:
        return {"AAA": Quote(Decimal(last), Decimal(1), NOW)}

    assert _one(_it(), quotes=q("1.70")) == (Verdict.REJECT, ("PRICE_SANITY",))
    assert _one(_it(), quotes=q("1.16")) == (Verdict.HOLD, ("GAP_HOLD",))
    assert (
        _one(_it("SSS", Side.SELL, 10), quotes={"SSS": Quote(Decimal("1.16"), Decimal(1), NOW)})[0]
        is Verdict.PASS
    )
    assert _one(_it(), quotes=q("1.10"))[0] is Verdict.PASS


def test_BW_RSK_07_limit_band() -> None:
    assert _one(_it(lim="1.04")) == (Verdict.REJECT, ("PRICE_BAND",))
    assert _one(_it(lim="1.03"))[0] is Verdict.PASS
    assert _one(_it(lim="0.99")) == (Verdict.REJECT, ("PRICE_BAND",))  # buy limit under ref


def test_BW_RSK_03_no_short() -> None:
    rep = check_intents([_it("SSS", Side.SELL, 1001)], _ctx())
    assert rep.results[0].reasons == ("NO_SHORT",) and rep.pages
    assert _one(_it("SSS", Side.SELL, 1000))[0] is Verdict.PASS


def test_L10_order_value() -> None:
    assert _one(_it(qty=790)) == (Verdict.REJECT, ("MAX_ORDER_VALUE",))  # 790 x 1.02 > 800
    assert _one(_it(qty=780))[0] is Verdict.PASS


def test_BW_RSK_06_participation_clip() -> None:
    v, r = _one(_it(qty=700, tv20="12000"))  # 5% of 12,000 = 600 shares at A$1
    assert v is Verdict.CLIP and "PARTICIPATION" in r
    assert _one(_it(qty=700, tv20="8000")) == (Verdict.REJECT, ("PARTICIPATION", "MIN_PARCEL"))
    assert _one(_it(tv20=None)) == (Verdict.REJECT, ("NO_LIQUIDITY_DATA",))


def test_L10_orders_per_day_and_buys_per_day() -> None:
    many = [_it(f"E{k}", qty=500, seq=k) for k in range(20)]
    rep = check_intents(
        many, _ctx(settled_cash=Decimal(100000)), RiskLimits(buys_per_day_normal_aud=Decimal(10**6))
    )
    assert (
        sum(r.sendable for r in rep.results) == 16
        and rep.latch is SafetyLevel.HALTED_BUYS
        and rep.pages
    )
    rep2 = check_intents(
        many,
        _ctx(settled_cash=Decimal(100000), start_day=True),
        RiskLimits(buys_per_day_start_aud=Decimal(10**6), capital_cap_aud=Decimal(10**6)),
    )
    assert sum(r.sendable for r in rep2.results) == 20
    rep3 = check_intents(many, _ctx(settled_cash=Decimal(100000)))
    assert sum(r.sendable for r in rep3.results) == 8  # 8 x 510 <= 4,500 < 9 x 510
    assert {r.reasons for r in rep3.results if not r.sendable} == {("MAX_BUYS_PER_DAY",)}


def test_BW_RSK_11_cash_and_L1_capital_cap() -> None:
    v, r = _one(_it(qty=700), settled_cash=Decimal(600))
    assert v is Verdict.CLIP and r == ("CASH_SHORT",)
    assert _one(_it(qty=700), settled_cash=Decimal(400))[0] is Verdict.REJECT
    assert _one(_it(), holdings_cost=Decimal(9700)) == (Verdict.REJECT, ("CAPITAL_CAP",))


def test_BW_SYS_04_property_no_intent_set_passes_with_a_limit_broken() -> None:
    lim = RiskLimits()
    rng = random.Random(42)
    for _ in range(400):
        n = rng.randint(1, 30)
        its = []
        for k in range(n):
            side = Side.BUY if rng.random() < 0.7 else Side.SELL
            ref = Decimal(f"{rng.uniform(0.05, 30):.3f}")
            band = Decimal(f"{rng.uniform(-0.06, 0.06):.3f}")
            limp = round_to_step(ref * (1 + band), side) if ref * (1 + band) > 0 else ref
            its.append(
                OrderIntent(
                    f"c{k}",
                    "b",
                    k + 1,
                    "L",
                    "B",
                    D,
                    f"E{k % 7}",
                    side,
                    rng.randint(1, 3000),
                    OrderType.LOC,
                    ref,
                    limp,
                    "T",
                    tv_med20=Decimal(rng.randint(0, 400000)),
                    prev_close=ref * Decimal(f"{rng.uniform(0.3, 1.8):.2f}"),
                )
            )
        ctx = _ctx(
            positions={f"E{k}": rng.randint(0, 2000) for k in range(7)},
            settled_cash=Decimal(rng.randint(0, 12000)),
            start_day=rng.random() < 0.3,
            safety=rng.choice(list(SafetyLevel)),
            holdings_cost=Decimal(rng.randint(0, 10000)),
        )
        rep = check_intents(its, ctx, lim)
        sent = [r.intent for r in rep.results if r.sendable]
        buys = [i for i in sent if i.side is Side.BUY]
        assert len(sent) <= (
            lim.orders_per_day_start if ctx.start_day else lim.orders_per_day_normal
        )
        assert sum(i.value_at_limit for i in buys) <= (
            lim.buys_per_day_start_aud if ctx.start_day else lim.buys_per_day_normal_aud
        )
        cost = sum(i.value_at_limit + ctx.commission(i.value_at_limit) for i in buys)
        assert cost <= ctx.settled_cash
        assert ctx.holdings_cost + sum(i.value_at_limit for i in buys) <= lim.capital_cap_aud
        if ctx.safety in (
            SafetyLevel.KILLED,
            SafetyLevel.HALTED_INTEGRITY,
            SafetyLevel.HALTED_LINE,
        ):
            assert not sent
        if ctx.safety in (SafetyLevel.PAUSED, SafetyLevel.HALTED_BUYS):
            assert not buys
        for i in sent:
            assert abs(i.limit_price / i.ref_price - 1) <= lim.price_band
            assert is_valid_step(i.limit_price)
            assert i.prev_close is None or abs(i.ref_price / i.prev_close - 1) <= lim.absurd_move
            assert (
                i.tv_med20 is not None and i.qty * i.ref_price <= lim.participation_max * i.tv_med20
            )
            if i.side is Side.BUY:
                assert (
                    lim.min_parcel_aud <= i.value_at_ref
                    and i.value_at_limit <= lim.order_value_max_aud
                )
            else:
                assert i.qty <= ctx.positions.get(i.entity, 0)


@pytest.mark.parametrize(
    ("value", "peak", "prev", "level"),
    [
        ("9000", "10000", "9100", SafetyLevel.NORMAL),
        ("6900", "10000", "7000", SafetyLevel.NORMAL),  # review page only
        ("6000", "10000", "6100", SafetyLevel.HALTED_BUYS),
        ("5000", "10000", "5100", SafetyLevel.HALTED_LINE),
        ("8700", "10000", "9900", SafetyLevel.HALTED_BUYS),  # one-day fall of 12%
        ("9000", "18000", "9100", SafetyLevel.HALTED_BUYS),  # drawdown 50%
    ],
)
def test_L11_BW_RSK_20_22_29_book_monitors(
    value: str, peak: str, prev: str, level: SafetyLevel
) -> None:
    """L11 value floors, BW-RSK-20 drawdown, BW-RSK-22 day move, BW-RSK-29 real-money floor."""
    r = evaluate_book(Decimal(value), Decimal(peak), Decimal(prev), Decimal(10000))
    assert r.level is level
    if Decimal(value) <= 7000:
        assert any("L11" in a for a in r.alerts)


def test_breaker_reruns_identically_at_send_time() -> None:
    its = [_it(f"E{k}", seq=k) for k in range(5)]
    a = check_intents(its, _ctx())
    b = check_intents([r.intent for r in a.results if r.sendable], _ctx())
    assert [r.intent for r in a.results] == [r.intent for r in b.results]
    assert replace(its[0], qty=1) != its[0]
