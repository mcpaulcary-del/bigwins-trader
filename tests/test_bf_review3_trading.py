"""Full review, trading core (22 Nov 2026; BF-D69): gateway reconnects (H1), the event
loop (H2), the latest send time (H3), early closes (H4), stale approvals (H5), the
orders-per-day limit (H6), commissions (M1), carries (M2), the breaker's quotes (M3),
shared cash (M4), no LMT yet (M5), the Flex backstop (M6), the L11 resume (M7) and
L1-L8. PAPER ONLY: nothing here weakens a live guard."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from tests.bf_support import real_config
from tests.test_bf_app import (
    CHAT,
    D0,
    DAYS,
    PANEL,
    SEED,
    _app,
    _closes,
    _loss_app,
    _Marks,
    _owner,
)
from trader.approval import Incoming, totp
from trader.bf_app import at, dry_run, mock_auction, owner_approves_all
from trader.broker.base import BrokerDisconnectedError, exec_base
from trader.journal import Journal, Status
from trader.orders import CommissionModel, OrderIntent, OrderType, Side, round_to_step
from trader.risk import Quote, RiskContext, SafetyLevel, Verdict, check_intents
from trader.scheduler import GATEWAY_EXIT, run_forever, run_once

X1, X2 = PANEL.dates[271], PANEL.dates[272]
BID = f"EMG2_18_PAPER-{D0}-C"


def _canary(approve: bool = True) -> tuple[Any, Any, Any]:
    app, gw, tr = _app(D0)
    run_once(app, at(D0, "23:45"))
    if approve:
        t = at(X1, "10:35")
        tr.inbox.append(Incoming(CHAT, f"/ok {BID} all {totp(SEED, t)}", t))
    return app, gw, tr


def _pages(tr: Any) -> list[str]:
    return [t for _, t in tr.outbox if "PAGE" in t]


# ------------------------------------------------------------------ H1
def test_H1_reconnects_after_the_nightly_gateway_restart_then_sends() -> None:
    app, gw, _ = _canary()
    gw.connected = False  # 23:59 restart: the API socket is gone
    run_once(app, at(X1, "15:46"))
    assert gw.connects >= 2 and app.broker.reconnects == 1
    assert {st for _, st in app.j.intents_of(BID)} == {Status.SENT}


def test_H1_gateway_not_logged_in_pages_and_the_trader_exits() -> None:
    app, gw, tr = _canary()
    app.broker._wait = lambda s: None
    gw.connected, gw.login_ok = False, False
    run_once(app, at(X1, "10:31"))  # the 10:30 check pages before the deadline
    assert any("gateway not logged in" in p for p in _pages(tr))
    with pytest.raises(BrokerDisconnectedError):
        run_once(app, at(X1, "15:46"))
    assert any("gateway down" in p for p in _pages(tr))
    clock = iter([at(X1, "15:47"), at(X1, "15:47"), at(X1, "15:48")])
    with pytest.raises(SystemExit) as ex:
        run_forever(app, clock=lambda: next(clock), sleep=lambda s: None)
    assert ex.value.code == GATEWAY_EXIT


def test_H1_a_live_login_after_a_reconnect_is_still_refused() -> None:
    from trader.broker.base import LiveTradingRefusedError

    app, gw, _ = _canary()
    gw.connected, gw.accounts = False, ("U7654321",)
    with pytest.raises(LiveTradingRefusedError):
        app.broker.positions()


# ------------------------------------------------------------------ H2
def test_H2_fills_that_arrive_only_when_the_loop_runs_are_collected() -> None:
    app, gw, _ = _canary()
    run_once(app, at(X1, "15:46"))
    gw.async_events = True
    mock_auction(gw, _closes)(X1)
    assert gw.pending and not gw.fills_  # nothing processed yet
    run_once(app, at(X1, "16:21"))
    assert {st for _, st in app.j.intents_of(BID)} == {Status.FILLED}


# ------------------------------------------------------------------ H3
def test_H3_no_send_after_the_latest_send_time() -> None:
    app, gw, tr = _canary()
    run_once(app, at(X1, "16:02"))  # the trader was down at 15:45
    assert not gw.placed
    assert {st for _, st in app.j.intents_of(BID)} == {Status.LAPSED}
    assert any("Nothing was sent late" in p for p in _pages(tr))


# ------------------------------------------------------------------ H4
@pytest.mark.parametrize("d", [date(2026, 12, 24), date(2026, 12, 31)])
def test_H4_early_close_days_are_not_order_days(d: date) -> None:
    from trader.bfast_cli import _early_closes

    ec = _early_closes(date(2026, 11, 1))
    assert ec[d] == "14:10"
    app, _, _ = _app(D0)
    app.s = replace(app.s, early_closes=ec, no_order_days=frozenset({date(2027, 1, 5)}))
    app.sessions = [date(2026, 12, 23), date(2026, 12, 24), date(2026, 12, 29), date(2026, 12, 30),
                    date(2026, 12, 31), date(2027, 1, 4), date(2027, 1, 5), date(2027, 1, 6)]  # fmt: skip
    prev = max(x for x in app.sessions if x < d)
    assert not app.is_order_day(d) and app.order_day(prev) > d
    assert app.order_day(date(2027, 1, 4)) == date(2027, 1, 6)  # the listed closure too
    assert app.latest_send_at(d) == at(d, "14:00") and app.latest_send_at(prev) == at(prev, "15:55")


# ------------------------------------------------------------------ H5
def test_H5_an_approval_does_not_carry_to_a_later_day() -> None:
    app, gw, _ = _canary()
    run_once(app, at(X2, "15:46"))  # X1 never ran (outage); its approved orders are stale
    assert not gw.placed
    assert {st for _, st in app.j.intents_of(BID)} == {Status.LAPSED}


# ------------------------------------------------------------------ H6
def _mk(i: int, side: Side, qty: int = 1000, ref: Decimal = Decimal("0.55")) -> OrderIntent:
    d = date(2027, 6, 30)
    lim = round_to_step(ref * (Decimal("1.03") if side is Side.BUY else Decimal("0.97")), side)
    return OrderIntent(f"B-{d}-E{i}-{side.value}-1", "b", i, "EMG2_18", "B", d, f"E{i}", side, qty,
                       OrderType.LOC, ref, lim, "x", tv_med20=Decimal(500000), prev_close=ref)  # fmt: skip


def _rctx(pos: dict[str, int], cash: int) -> RiskContext:
    d = date(2027, 6, 30)
    return RiskContext(now=datetime.now(UTC), session=d, expected_data_date=d, data_as_of=d,
                       safety=SafetyLevel.NORMAL, start_day=False, positions=pos,
                       settled_cash=Decimal(cash), holdings_cost=Decimal(4000))  # fmt: skip


def test_H6_sells_never_hit_the_orders_limit_and_nothing_latches() -> None:
    lim = real_config().risk_limits()
    s = [_mk(i, Side.SELL) for i in range(1, 19)]  # the L11 wind-down sells all 18
    r = check_intents(s, _rctx({f"E{i}": 1000 for i in range(1, 19)}, 50), lim)
    assert all(x.sendable for x in r.results) and r.latch is None
    its = [_mk(i, Side.SELL) for i in range(1, 11)] + [_mk(i, Side.BUY, 950) for i in range(11, 21)]
    r = check_intents(its, _rctx({f"E{i}": 1000 for i in range(1, 11)}, 6000), lim)
    assert all(x.sendable for x in r.results) and r.latch is None
    nine = [_mk(i, Side.BUY, 980) for i in range(1, 10)]  # 9 buys of ~A$555
    r = check_intents(nine, _rctx({}, 6000), lim)
    assert all(x.sendable for x in r.results)
    many = [_mk(i, Side.BUY, 950) for i in range(1, 23)]
    big = replace(lim, buys_per_day_normal_aud=Decimal(99999), capital_cap_aud=Decimal(99999))
    r = check_intents(many, _rctx({}, 20000), big)
    assert sum(not x.sendable for x in r.results) == 2 and r.latch is None and r.pages


def test_H6_config_limits_must_fit_a_whole_book() -> None:
    cfg = real_config()
    with pytest.raises(ValueError, match="buys_per_day"):
        type(cfg).model_validate({**cfg.model_dump(), "risk": {
            **cfg.risk.model_dump(), "buys_per_day_aud": {"start": 10500, "normal": 4500}}})  # fmt: skip


# ------------------------------------------------------------------ M1
def test_M1_tiered_commission_and_a_tolerance_band() -> None:
    from trader.loss_rule import ModelledFill, integrity_breaks

    cfg = real_config()
    cm = cfg.commission_model()
    assert cfg.broker.pricing == "tiered" and cm.pricing == "tiered"
    assert cm(Decimal(550)) == Decimal("5.54")  # (5.00 + 0.03 fees) x 1.1
    assert cm(Decimal(20000)) == Decimal("18.70")  # (16.00 + 1.00) x 1.1
    assert CommissionModel()(Decimal(550)) == Decimal("6.60")  # fixed, as before

    def f(c: str) -> ModelledFill:
        return ModelledFill(
            "o", "AAA", Side.BUY, 1000, Decimal("0.55"), Decimal(c), Decimal("0.57")
        )

    assert integrity_breaks({}, {}, (), [f("5.80")], cm) == ()  # inside the band
    assert integrity_breaks({}, {}, (), [f("9.00")], cm)  # outside it


def test_M1_flex_taxes_are_part_of_the_fill_cost() -> None:
    from trader.data.flex import parse_statements

    xml = _flex_xml(taxes="-0.66")
    (st,) = parse_statements(xml)
    assert st.trades[0].taxes == Decimal("-0.66")


# ------------------------------------------------------------------ M2
def test_M2_a_carry_is_priced_at_the_days_close_once_it_is_in() -> None:
    app, gw, _ = _canary()
    real = app.closes
    app.closes = lambda d: {} if app.now < at(d, "17:35") else real(d)
    run_once(app, at(X1, "15:46"))
    for t in list(gw.openTrades()):
        gw.cancelOrder(t.order)  # no auction fill
    run_once(app, at(X1, "16:21"))
    assert app.j.batch(f"EMG2_18_PAPER-{X1}-X") is None  # not at 16:20 on old prices
    run_once(app, at(X1, "22:17"))
    it0 = app.j.intents_of(BID)[0][0]
    (c, _), *_ = app.j.intents_of(f"EMG2_18_PAPER-{X1}-X")
    assert c.ref_price == _closes(X1)[it0.entity] != it0.ref_price


# ------------------------------------------------------------------ M3
@pytest.mark.parametrize(
    ("setup", "reason"),
    [
        ("stale", "QUOTE_STALE"),
        ("gap", "GAP_HOLD"),
        ("absurd", "PRICE_SANITY"),
        ("data", "DATA_STALE"),
    ],
)
def test_M3_the_breaker_sees_the_real_quote(setup: str, reason: str) -> None:
    app, gw, _ = _canary()
    it0 = app.j.intents_of(BID)[0][0]
    if setup == "stale":
        gw.quote_time = datetime(2020, 1, 1, tzinfo=UTC)
        gw.marks[it0.entity] = float(it0.prev_close)
    elif setup == "gap":
        gw.marks[it0.entity] = float(it0.prev_close) * 1.25
    elif setup == "absurd":
        gw.marks[it0.entity] = float(it0.prev_close) * 3
    else:
        app.closes = lambda d: {}
    run_once(app, at(X1, "15:46"))
    ev = [e for e in app.j.events_of(it0.client_order_id) if e.get("reasons")]
    assert any(reason in e["reasons"] for e in ev), ev
    assert not gw.placed


# ------------------------------------------------------------------ M4
def test_M4_cash_of_sent_unfilled_buys_is_reserved() -> None:
    app, gw, _ = _canary()
    run_once(app, at(X1, "15:46"))
    cm = app.s.order_params.commission
    res = app.j.open_buy_reserve(app.s.book, cm)
    it0 = app.j.intents_of(BID)[0][0]
    assert res == it0.limit_price * it0.qty + cm(it0.limit_price * it0.qty)
    ctx = app._ctx(app.s.book, app.broker, X1, D0, at(X1, "15:50"), True)
    assert ctx.settled_cash == app.broker.account().settled_cash - res


# ------------------------------------------------------------------ M5
def test_M5_lmt_is_refused_until_it_is_built() -> None:
    cfg = real_config()
    with pytest.raises(ValueError, match="LMT"):
        type(cfg).model_validate({**cfg.model_dump(), "execution": {
            **cfg.execution.model_dump(), "order_type": "LMT"}})  # fmt: skip


# ------------------------------------------------------------------ M6 / L6
def _flex_xml(exec_id: str = "0001.01", ref: str = "", taxes: str = "0", sym: str = "S001",
              qty: str = "100", side: str = "BUY", day: str = "20240118") -> bytes:  # fmt: skip
    return (
        '<FlexQueryResponse><FlexStatements count="1"><FlexStatement accountId="DU1234567" '
        f'fromDate="{day}" toDate="{day}"><Trades><Trade ibExecID="{exec_id}" tradeID="1" '
        f'symbol="{sym}" buySell="{side}" quantity="{qty}" tradePrice="1.5" ibCommission="-6.0" '
        f'taxes="{taxes}" tradeDate="{day}" orderReference="{ref}"/></Trades>'
        "</FlexStatement></FlexStatements></FlexQueryResponse>"
    ).encode()


def test_M6_flex_books_a_fill_the_gateway_session_missed() -> None:
    from trader.data.flex import parse_statements

    app, gw, tr = _canary()
    run_once(app, at(X1, "15:46"))
    it0 = app.j.intents_of(BID)[0][0]
    sts = parse_statements(_flex_xml("X9.01", it0.client_order_id, "-0.60", it0.entity,
                                     str(it0.qty), day=f"{X1:%Y%m%d}"))  # fmt: skip
    app._flex_fills(sts, at(X2, "16:30"))
    (f,) = app.j.fills(coid=it0.client_order_id)
    assert f.commission == Decimal("6.60")  # commission + GST from ``taxes``
    assert dict(app.j.intents_of(BID)[0:1])[it0] == Status.FILLED
    app._flex_fills(sts, at(X2, "16:31"))  # once only
    assert len(app.j.fills(coid=it0.client_order_id)) == 1


def test_L6_a_corrected_execution_is_not_booked_twice_and_fixes_the_commission() -> None:
    from trader.journal import FillRecord

    assert exec_base("0000e0d5.6578.01.02") == "0000e0d5.6578.01"
    app, gw, _ = _canary()
    run_once(app, at(X1, "15:46"))
    it0 = app.j.intents_of(BID)[0][0]
    app.j.add_fill(FillRecord("abc.01", it0.client_order_id, app.s.book, it0.entity, Side.BUY,
                              it0.qty, it0.limit_price, Decimal(0), at(X1, "16:10")))  # fmt: skip
    from trader.data.flex import parse_statements

    sts = parse_statements(_flex_xml("abc.02", it0.client_order_id, "-0.6", it0.entity))
    app._flex_fills(sts, at(X2, "16:30"))
    (f,) = app.j.fills(coid=it0.client_order_id)
    assert f.exec_id == "abc.01" and f.commission == Decimal("6.60")


# ------------------------------------------------------------------ M7
def test_M7_the_l11_resume_never_clears_another_halt() -> None:
    app, _, tr = _loss_app()
    m = _Marks(app)
    m.walk("9000", "8100", "7200", "6400", "5900")  # L11 stage 2: HALTED_BUYS
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    assert app._other_halts() == []
    app.j.set_safety(SafetyLevel.HALTED_BUYS, "breaker latch", "risk")
    assert app._other_halts() == ["'breaker latch'"]
    from tests.test_bf_app import M2

    app.job_decide(M2, at(M2, "22:20"))
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS  # not cleared by the L11 test
    assert any("not an L11 halt" in t for _, t in tr.outbox)


# ------------------------------------------------------------------ L1
def test_L1_two_sells_of_one_name_cannot_oversell() -> None:
    lim = real_config().risk_limits()
    a, b = _mk(1, Side.SELL, 600), replace(_mk(1, Side.SELL, 600), client_order_id="x", seq=2)
    r = check_intents([a, b], _rctx({"E1": 1000}, 50), lim)
    assert [x.verdict for x in r.results] == [Verdict.PASS, Verdict.REJECT]
    assert r.results[1].reasons == ("NO_SHORT",)


# ------------------------------------------------------------------ L2
def test_L2_a_crash_between_the_wind_down_plan_and_its_record_does_not_double_step() -> None:
    from tests.test_bf_app import M2

    app, _, _ = _loss_app()
    _Marks(app).walk("9000", "8100", "7200", "6400", "5700", "5050", "4990")
    real = app.j.mark_job

    def boom(key: str, *a: Any, **k: Any) -> None:
        if key.startswith("l11:wind"):
            raise RuntimeError("crash")
        real(key, *a, **k)

    app.j.mark_job = boom  # type: ignore[method-assign]
    with pytest.raises(RuntimeError):
        app.job_decide(M2, at(M2, "22:20"))
    app.j.mark_job = real  # type: ignore[method-assign]
    app.job_decide(M2, at(M2, "22:21"))
    assert app._l11_episode()["wind"] == 1  # type: ignore[index]
    w = app.j.intents_of(f"{app.s.book}-{M2}-W")
    assert w and all(it.reason == "L11_WIND_DOWN_1" for it, _ in w)


# ------------------------------------------------------------------ L3
def test_L3_jobs_are_claimed_once_and_status_changes_compare_and_set() -> None:
    j = Journal.sqlite()
    assert j.claim_job("k") is True and j.claim_job("k") is False
    app, _, _ = _canary(approve=False)
    it0 = app.j.intents_of(BID)[0][0]
    from sqlalchemy import update

    from trader.journal import intents

    with app.j.engine.begin() as c:  # another writer changes the status under us
        c.execute(update(intents).where(intents.c.client_order_id == it0.client_order_id)
                  .values(status=Status.APPROVED))  # fmt: skip
    from trader.journal import JournalError

    with pytest.raises(JournalError):
        app.j.set_status(it0.client_order_id, Status.LAPSED, expected=Status.RISK_OK)


# ------------------------------------------------------------------ L4
def test_L4_a_held_name_without_closes_pages_then_is_valued_as_the_decision_does() -> None:
    app, _, _ = _loss_app()
    held = sorted(app.j.positions(app.s.book))
    gone = held[0]
    marks = app.marks
    app.marks = lambda d: {e: p for e, p in marks(d).items() if e != gone}
    days = DAYS[4:30]
    flags6: list[str] = []
    for k, d in enumerate(days):
        px = dict(app.marks(d))
        fl = app._carry_marks(px, d, at(d, "22:45"))
        if k == 6:
            flags6 = fl
    assert any(f.startswith("PAGE") and gone in f for f in flags6)
    assert px[gone] == 0 and any("valued at zero" in f for f in fl)


# ------------------------------------------------------------------ L5
def test_L5_needs_review_is_rechecked_each_session() -> None:
    app, gw, _ = _canary()
    it0 = app.j.intents_of(BID)[0][0]
    run_once(app, at(X1, "15:46"))
    app.j.set_status(it0.client_order_id, Status.NEEDS_REVIEW, {"why": "test"})
    app.job_collect(X1, at(X1, "16:21"))  # the broker has the order: adopted again
    st = {it.client_order_id: s for it, s in app.j.intents_of(BID)}[it0.client_order_id]
    assert st in (Status.SENT, Status.EXPIRED)


# ------------------------------------------------------------------ L7
def test_L7_continue_only_inside_a_stage3_episode() -> None:
    app, _, tr = _loss_app()
    _owner(app, DAYS[5], "/continue <code>")
    assert "only to an open L11 stage-3" in tr.outbox[-1][1]
    m = _Marks(app)
    d = m.walk("9000", "8100", "6400", "5900")  # stage 2 only
    _owner(app, d, "/continue <code>")
    assert "only to an open L11 stage-3" in tr.outbox[-1][1]


# ------------------------------------------------------------------ L8
def test_L8_the_l11_evaluation_is_retried_once_then_paged() -> None:
    app, _, tr = _loss_app()
    calls = {"n": 0}
    real = app._report

    def flaky(day: date, now: datetime) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("db blip")
        real(day, now)

    app._report = flaky  # type: ignore[method-assign]
    app.job_report(DAYS[5], at(DAYS[5], "22:45"))
    assert calls["n"] == 2
    app._report = lambda d, n: (_ for _ in ()).throw(OSError("down"))  # type: ignore[method-assign,assignment]
    with pytest.raises(OSError):
        app.job_report(DAYS[6], at(DAYS[6], "22:45"))
    assert "evaluation of" in _pages(tr)[-1]


def test_review3_order_ids_and_dates_are_unchanged_for_normal_days() -> None:
    app, _, _ = _app(D0)
    assert app.order_day(D0) == app.next_session(D0)
    assert app.latest_send_at(D0) == at(D0, "15:55")
    assert timedelta(minutes=10) == at(D0, "15:55") - at(D0, "15:45")
    _ = dry_run, mock_auction, owner_approves_all, Quote
