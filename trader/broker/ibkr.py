"""IBKR adapter via ``ib_async`` — PAPER ONLY in this build (FD v3.0 §11; BF3).

Guards (any one failing raises ``LiveTradingRefusedError``; nothing is sent):

1. ``LIVE_TRADING_ENABLED`` (hard-coded ``False``) and the config flag
   ``allow_live`` (schema ``Literal[False]``) — checked at construction, at connect
   and before every order;
2. mode must be ``paper``, the gateway port a paper port, the account id ``DU...``;
3. after connecting, every account the gateway manages must be a ``DU...`` account
   and the configured one must be among them (a live login on a "paper" port is
   caught here).

Order path: ``place()`` sends one DAY limit order (``orderType`` ``LOC`` or ``LMT``)
with ``orderRef = client_order_id`` and waits for the gateway's acknowledgement. On
timeout it raises ``BrokerTimeoutError`` and **never resends**; the execution layer
marks the intent ``NEEDS_REVIEW`` and later finds the order by ``orderRef``
(``find_order`` searches this session's trades and the gateway's completed orders,
so it works after a gateway restart — **[unverified, O-3]** for the paper gateway,
the reality spike checks it).

**[unverified, O-1]**: that IBKR accepts ``LOC`` for ASX shares via the API and its
cut-off. **[unverified]**: the account-value tags ``SettledCash`` / ``AvailableFunds``
for an IBKR Australia cash account, and delayed quotes (``reqMarketDataType(3)``)
without an ASX market-data subscription.

Credentials are never handled here: IB Gateway logs in by itself inside its own
container (Docker secrets); this adapter only opens the local API socket.
"""

from __future__ import annotations

import time as _time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from ib_async import IB, LimitOrder, Stock

from trader.broker.base import (
    LIVE_TRADING_ENABLED,
    AccountSnapshot,
    BrokerQuote,
    BrokerRejectedError,
    BrokerTimeoutError,
    Execution,
    LiveTradingRefusedError,
    OrderRequest,
    OrderState,
    assert_paper,
)
from trader.orders import OrderType, Side

ACKED = frozenset({"PreSubmitted", "Submitted", "Filled"})
DEAD = frozenset({"Cancelled", "ApiCancelled", "Inactive"})


@dataclass(frozen=True)
class IbkrSettings:
    host: str
    port: int
    client_id: int
    account_id: str
    mode: Literal["paper"] = "paper"
    allow_live: Literal[False] = False
    connect_timeout: float = 15.0
    exchange: str = "ASX"
    currency: str = "AUD"
    market_data_type: int = 3  # delayed [unverified]


def wire_price(d: Decimal) -> float:
    """Decimal -> the float ib_async sends; refuses a price that does not round-trip."""
    f = float(d)
    if Decimal(repr(f)).normalize() != d.normalize():
        raise BrokerRejectedError(f"price {d} does not round-trip through float")
    return f


def _dec(x: Any) -> Decimal | None:
    if x is None:
        return None
    d = Decimal(repr(x)) if not isinstance(x, Decimal) else x
    return None if d.is_nan() or d <= 0 else d


class IbkrPaperBroker:
    """``Broker`` implementation over an ``ib_async.IB`` (or a test double with the same API)."""

    is_paper = True

    def __init__(
        self,
        settings: IbkrSettings,
        ib_factory: Callable[[], Any] = IB,
        clock: Callable[[], float] = _time.monotonic,
    ) -> None:
        self.s = settings
        self._guard()
        self.account_id = settings.account_id
        self.ib = ib_factory()
        self._clock = clock
        self._contracts: dict[str, Any] = {}

    def _guard(self) -> None:
        if LIVE_TRADING_ENABLED:
            raise LiveTradingRefusedError("live trading is disabled in this build")
        assert_paper(
            mode=self.s.mode,
            account_id=self.s.account_id,
            port=self.s.port,
            allow_live=self.s.allow_live,
        )

    # ------------------------------------------------------------- session
    def connect(self) -> None:
        self._guard()
        self.ib.connect(
            self.s.host,
            self.s.port,
            clientId=self.s.client_id,
            timeout=self.s.connect_timeout,
            readonly=False,
            account=self.s.account_id,
        )
        accounts = list(self.ib.managedAccounts())
        bad = [a for a in accounts if not str(a).startswith("DU")]
        if bad or self.s.account_id not in accounts:
            self.ib.disconnect()
            raise LiveTradingRefusedError(
                f"gateway manages {accounts}: not only paper accounts with {self.s.account_id}"
            )
        self.ib.reqMarketDataType(self.s.market_data_type)

    def disconnect(self) -> None:
        self.ib.disconnect()

    def _contract(self, symbol: str) -> Any:
        c = self._contracts.get(symbol)
        if c is None:
            q = self.ib.qualifyContracts(Stock(symbol, self.s.exchange, self.s.currency))
            if not q:
                raise BrokerRejectedError(f"cannot qualify {symbol} on {self.s.exchange}")
            c = q[0]
            self._contracts[symbol] = c
        return c

    # ------------------------------------------------------------- orders
    def place(self, req: OrderRequest, timeout: float = 10.0) -> OrderState:
        self._guard()
        if req.account != self.s.account_id:
            raise LiveTradingRefusedError(f"order for account {req.account!r} refused")
        if req.order_type not in (OrderType.LOC, OrderType.LMT) or req.tif != "DAY":
            raise BrokerRejectedError("only DAY LOC / LMT orders are sent (no market orders)")
        if req.qty <= 0:
            raise BrokerRejectedError("quantity must be positive")
        order = LimitOrder(
            "BUY" if req.side is Side.BUY else "SELL", req.qty, wire_price(req.limit_price)
        )
        order.orderType = req.order_type.value
        order.tif = "DAY"
        order.orderRef = req.client_order_id
        order.account = req.account
        order.outsideRth = False
        order.transmit = True
        trade = self.ib.placeOrder(self._contract(req.symbol), order)
        deadline = self._clock() + timeout
        while trade.orderStatus.status not in ACKED | DEAD:
            if self._clock() >= deadline:
                raise BrokerTimeoutError(f"{req.client_order_id}: no acknowledgement in {timeout}s")
            self.ib.sleep(0.2)
        st = self._state(trade)
        if st.status in DEAD and st.filled == 0:
            msgs = "; ".join(
                str(e.message) for e in getattr(trade, "log", []) if getattr(e, "message", "")
            )
            raise BrokerRejectedError(f"{req.client_order_id}: {st.status} {msgs}".strip())
        return st

    def _trades(self) -> list[Any]:
        seen: dict[int, Any] = {}
        for t in [
            *self.ib.trades(),
            *self.ib.reqAllOpenOrders(),
            *self.ib.reqCompletedOrders(apiOnly=True),
        ]:
            seen[int(t.order.permId) or id(t)] = t
        return list(seen.values())

    def _by_ref(self, coid: str) -> Any | None:
        found = [t for t in self._trades() if t.order.orderRef == coid]
        if len(found) > 1:
            raise BrokerRejectedError(f"{coid}: {len(found)} broker orders carry this orderRef")
        return found[0] if found else None

    def find_order(self, client_order_id: str) -> OrderState | None:
        t = self._by_ref(client_order_id)
        return self._state(t) if t is not None else None

    def cancel(self, client_order_id: str) -> bool:
        """Cancel reduces risk: allowed in any safety state (BW-EXE-10)."""
        for t in self.ib.openTrades():
            if t.order.orderRef == client_order_id:
                self.ib.cancelOrder(t.order)
                return True
        return False

    def open_orders(self) -> list[OrderState]:
        return [self._state(t) for t in self.ib.reqAllOpenOrders()]

    # ------------------------------------------------------------- account
    def positions(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for p in self.ib.positions(self.s.account_id):
            q = int(Decimal(repr(p.position)))
            if q:
                out[p.contract.symbol] = out.get(p.contract.symbol, 0) + q
        return dict(sorted(out.items()))

    def account(self) -> AccountSnapshot:
        vals: dict[str, Decimal] = {}
        for v in self.ib.accountValues(self.s.account_id):
            if v.currency in (self.s.currency, "BASE") and v.tag in (
                "SettledCash",
                "AvailableFunds",
                "NetLiquidation",
                "TotalCashValue",
            ):
                vals.setdefault(v.tag, Decimal(str(v.value)))
        settled = vals.get("SettledCash", vals.get("TotalCashValue"))
        if settled is None or "AvailableFunds" not in vals or "NetLiquidation" not in vals:
            raise BrokerRejectedError(f"account values missing: {sorted(vals)}")
        return AccountSnapshot(
            self.s.account_id, settled, vals["AvailableFunds"], vals["NetLiquidation"]
        )

    def executions(self) -> list[Execution]:
        out: list[Execution] = []
        for f in self.ib.fills():
            e = f.execution
            if e.acctNumber and e.acctNumber != self.s.account_id:
                continue
            comm = f.commissionReport.commission if f.commissionReport else 0.0
            out.append(
                Execution(
                    exec_id=e.execId,
                    client_order_id=e.orderRef or None,
                    symbol=f.contract.symbol,
                    side=Side.BUY if e.side == "BOT" else Side.SELL,
                    qty=int(Decimal(repr(e.shares))),
                    price=Decimal(repr(e.price)),
                    commission=Decimal(repr(comm)),
                    time=e.time if isinstance(e.time, datetime) else datetime.now(UTC),
                )
            )
        return out

    def quote(self, symbol: str) -> BrokerQuote | None:
        tk = self.ib.reqTickers(self._contract(symbol))
        if not tk:
            return None
        t = tk[0]
        return BrokerQuote(
            symbol,
            _dec(t.bid),
            _dec(t.ask),
            _dec(t.last),
            _dec(t.close),
            t.time if isinstance(t.time, datetime) else datetime.now(UTC),
        )

    @staticmethod
    def _state(t: Any) -> OrderState:
        s = t.orderStatus
        return OrderState(
            client_order_id=t.order.orderRef,
            broker_order_id=str(t.order.orderId),
            perm_id=str(t.order.permId),
            status=s.status,
            filled=int(Decimal(repr(s.filled))),
            remaining=int(Decimal(repr(s.remaining))),
        )
