"""BF3: IBKR adapter (paper only) against a mock gateway; paper/live guard (BW-EXE-09)."""

from __future__ import annotations

import inspect
from decimal import Decimal

import pytest

import trader.broker.base as base
from tests.fake_ib import FakeIB
from trader.broker.base import (
    BrokerRejectedError,
    BrokerTimeoutError,
    LiveTradingRefusedError,
    OrderRequest,
    assert_paper,
)
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings, wire_price
from trader.broker.paper_sim import SimBroker
from trader.orders import OrderType, Side

ACC = "DU1234567"


def _broker(fake: FakeIB | None = None, **kw: object) -> tuple[IbkrPaperBroker, FakeIB]:
    f = fake or FakeIB()
    s = IbkrSettings(host="gw-paper", port=4004, client_id=11, account_id=ACC, **kw)  # type: ignore[arg-type]
    t = [0.0]

    def clock() -> float:
        t[0] += 1.0
        return t[0]

    b = IbkrPaperBroker(s, ib_factory=lambda: f, clock=clock)
    b.connect()
    return b, f


def _req(
    coid: str = "B-2026-11-30-AAA-BUY-1",
    side: Side = Side.BUY,
    account: str = ACC,
    ot: OrderType = OrderType.LOC,
) -> OrderRequest:
    return OrderRequest(coid, account, "AAA", side, 500, ot, Decimal("1.035"))


class TestPaperLiveGuard:
    """BW-EXE-09: the paper/live guard refuses every live path."""

    def test_hard_coded_flag_is_false_and_not_configurable(self) -> None:
        assert base.LIVE_TRADING_ENABLED is False
        src = inspect.getsource(base)
        assert (
            "LIVE_TRADING_ENABLED: Final = False" in src
            and "os.environ" not in src
            and "getenv" not in src
        )

    @pytest.mark.parametrize(
        ("mode", "acct", "port", "allow"),
        [
            ("live", ACC, 4004, False),
            ("paper", "U1234567", 4004, False),
            ("paper", ACC, 4003, False),
            ("paper", ACC, 4001, False),
            ("paper", ACC, 7496, False),
            ("paper", ACC, 5555, False),
            ("paper", ACC, 4004, True),
        ],
    )
    def test_refuses_anything_not_paper(self, mode: str, acct: str, port: int, allow: bool) -> None:
        with pytest.raises(LiveTradingRefusedError):
            assert_paper(mode=mode, account_id=acct, port=port, allow_live=allow)

    def test_paper_passes(self) -> None:
        assert_paper(mode="paper", account_id=ACC, port=4004)

    def test_adapter_refuses_live_port_at_construction(self) -> None:
        with pytest.raises(LiveTradingRefusedError):
            IbkrPaperBroker(IbkrSettings("gw", 4003, 11, ACC), ib_factory=FakeIB)
        with pytest.raises(LiveTradingRefusedError):
            IbkrPaperBroker(IbkrSettings("gw", 4004, 11, "U7654321"), ib_factory=FakeIB)

    def test_refuses_a_gateway_logged_into_a_live_account(self) -> None:
        f = FakeIB(accounts=("U7654321", ACC))
        with pytest.raises(LiveTradingRefusedError):
            _broker(f)
        assert not f.connected and not f.placed
        with pytest.raises(LiveTradingRefusedError):
            _broker(FakeIB(accounts=("DU0000001",)))  # configured account not managed

    def test_refuses_order_for_another_account(self) -> None:
        b, f = _broker()
        with pytest.raises(LiveTradingRefusedError):
            b.place(_req(account="U7654321"))
        assert not f.placed

    def test_sim_broker_is_paper_only(self) -> None:
        with pytest.raises(LiveTradingRefusedError):
            SimBroker(account_id="U1")


def test_place_sends_loc_day_limit_with_order_ref() -> None:
    b, f = _broker()
    st = b.place(_req())
    contract, order = f.placed[0]
    assert (contract.symbol, contract.exchange, contract.currency) == ("AAA", "ASX", "AUD")
    assert order.orderType == "LOC" and order.tif == "DAY" and order.action == "BUY"
    assert order.lmtPrice == 1.035 and order.totalQuantity == 500
    assert order.orderRef == "B-2026-11-30-AAA-BUY-1" and order.account == ACC
    assert st.status == "Submitted" and st.client_order_id == order.orderRef
    assert f.md_type == 3 and f.connect_args["port"] == 4004
    b.place(_req("B-2026-11-30-AAA-SELL-1", Side.SELL, ot=OrderType.LMT))
    assert f.placed[1][1].orderType == "LMT" and f.placed[1][1].action == "SELL"


def test_EXE_10_timeout_raises_and_never_resends() -> None:
    b, f = _broker(FakeIB(ack="never"))
    with pytest.raises(BrokerTimeoutError):
        b.place(_req(), timeout=3)
    assert len(f.placed) == 1


def test_rejection_is_reported() -> None:
    b, _ = _broker(FakeIB(ack="Inactive"))
    with pytest.raises(BrokerRejectedError):
        b.place(_req())


def test_O3_find_order_by_order_ref_after_gateway_restart() -> None:
    b, f = _broker()
    b.place(_req())
    f.restart()  # client-side trades gone; the gateway still has the order
    st = b.find_order("B-2026-11-30-AAA-BUY-1")
    assert st is not None and st.perm_id == "9001"
    f.fill("B-2026-11-30-AAA-BUY-1", 1.03)
    f.restart()
    st2 = b.find_order("B-2026-11-30-AAA-BUY-1")
    assert st2 is not None and st2.status == "Filled" and st2.filled == 500
    assert b.find_order("nope") is None


def test_cancel_open_order() -> None:
    b, f = _broker()
    b.place(_req())
    assert [o.client_order_id for o in b.open_orders()] == ["B-2026-11-30-AAA-BUY-1"]
    assert b.cancel("B-2026-11-30-AAA-BUY-1") and not b.open_orders()
    assert not b.cancel("B-2026-11-30-AAA-BUY-1")


def test_executions_positions_account_and_quote() -> None:
    b, f = _broker()
    b.place(_req())
    f.fill("B-2026-11-30-AAA-BUY-1", 1.03, qty=200)
    f.fill("B-2026-11-30-AAA-BUY-1", 1.02)
    ex = b.executions()
    assert [(e.qty, e.price, e.side, e.client_order_id) for e in ex] == [
        (200, Decimal("1.03"), Side.BUY, "B-2026-11-30-AAA-BUY-1"),
        (300, Decimal("1.02"), Side.BUY, "B-2026-11-30-AAA-BUY-1"),
    ]
    assert ex[0].commission == Decimal("6.6")
    assert b.positions() == {"AAA": 500}
    acct = b.account()
    assert acct.settled_cash == Decimal(str(10000 - 206 - 6.6 - 306 - 6.6))
    q = b.quote("AAA")
    assert q is not None and q.bid == Decimal("0.995") and q.ask == Decimal("1.005")


def test_wire_price_round_trip() -> None:
    assert wire_price(Decimal("1.035")) == 1.035
    with pytest.raises(BrokerRejectedError):
        wire_price(Decimal("0.1000000000000000000001"))
