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

import contextlib
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
    BrokerDisconnectedError,
    BrokerQuote,
    BrokerRejectedError,
    BrokerTimeoutError,
    Execution,
    LiveTradingRefusedError,
    OrderRequest,
    OrderState,
    assert_paper,
    exec_base,
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
    reconnect_tries: int = 3  # review H1: bounded reconnects before the trader exits
    reconnect_wait: float = 5.0


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
        wait: Callable[[float], None] = _time.sleep,
    ) -> None:
        self.s = settings
        self._guard()
        self.account_id = settings.account_id
        self.ib = ib_factory()
        self._clock = clock
        self._wait = wait
        self._contracts: dict[str, Any] = {}
        self.reconnects = 0  # review H1: how many times the session was re-opened

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

    # ------------------------------------------------------------- review H1 / H2
    def pump(self) -> None:
        """Let ib_async process what the gateway sent since the last call (order
        statuses, executions, account updates): without it a long-running process that
        only calls synchronous methods between jobs misses events (review H2)."""
        with contextlib.suppress(Exception):  # a closed socket: found by ensure_connected
            self.ib.sleep(0)

    def is_connected(self) -> bool:
        f = getattr(self.ib, "isConnected", None)
        return bool(f()) if callable(f) else True

    def ensure_connected(self) -> None:
        """Before every broker call or job: re-open the API session after the gateway's
        nightly restart or a 2FA time-out. The reconnect goes through ``connect()``, so
        the paper / managed-account guards run again. Bounded retries; then
        ``BrokerDisconnectedError`` (the trader pages and exits; Docker restarts it)."""
        self._guard()
        if self.is_connected():
            self.pump()
            return
        last: Exception | None = None
        for k in range(max(1, self.s.reconnect_tries)):
            try:
                with contextlib.suppress(Exception):  # a half-closed session
                    self.ib.disconnect()
                self.connect()
                self._contracts.clear()
                self.reconnects += 1
                self.pump()
                return
            except LiveTradingRefusedError:
                raise  # a live login on the paper port is never retried
            except Exception as e:
                last = e
                if k + 1 < self.s.reconnect_tries:
                    self._wait(self.s.reconnect_wait * (k + 1))
        raise BrokerDisconnectedError(
            f"gateway not reachable or not logged in after {self.s.reconnect_tries} tries: "
            f"{type(last).__name__ if last else '?'}: {last}"[:300]
        )

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
        self.ensure_connected()
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
        self.ensure_connected()
        t = self._by_ref(client_order_id)
        return self._state(t) if t is not None else None

    def cancel(self, client_order_id: str) -> bool:
        """Cancel reduces risk: allowed in any safety state (BW-EXE-10)."""
        self.ensure_connected()
        for t in self.ib.openTrades():
            if t.order.orderRef == client_order_id:
                self.ib.cancelOrder(t.order)
                return True
        return False

    def open_orders(self) -> list[OrderState]:
        self.ensure_connected()
        return [self._state(t) for t in self.ib.reqAllOpenOrders()]

    # ------------------------------------------------------------- account
    def positions(self) -> dict[str, int]:
        self.ensure_connected()  # also pumps the event loop (review H2)
        out: dict[str, int] = {}
        for p in self.ib.positions(self.s.account_id):
            q = int(Decimal(repr(p.position)))
            if q:
                out[p.contract.symbol] = out.get(p.contract.symbol, 0) + q
        return dict(sorted(out.items()))

    def account(self) -> AccountSnapshot:
        self.ensure_connected()
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
            self.s.account_id,
            settled,
            vals["AvailableFunds"],
            vals["NetLiquidation"],
            vals.get("TotalCashValue"),
        )

    def executions(self) -> list[Execution]:
        """This session's executions: ``reqExecutions()`` asks the gateway (so fills
        that arrived while the client was idle or reconnecting are not missed, review
        H2), merged with the client's ``fills()``. A corrected execution (same base id,
        a higher ``.NN`` suffix) replaces the earlier one (review L6)."""
        self.ensure_connected()
        seen: dict[str, Any] = {}
        req = getattr(self.ib, "reqExecutions", None)
        got = list(req()) if callable(req) else []
        for f in [*got, *self.ib.fills()]:
            eid = str(f.execution.execId)
            base = exec_base(eid)
            old = seen.get(base)
            if (
                old is None
                or str(old.execution.execId) < eid
                or (str(old.execution.execId) == eid and not old.commissionReport)
            ):
                seen[base] = f
        out: list[Execution] = []
        for f in seen.values():
            e = f.execution
            if e.acctNumber and e.acctNumber != self.s.account_id:
                continue
            cr = f.commissionReport
            # review L6: a missing commission report books 0 and is corrected from Flex
            comm = cr.commission if cr and cr.commission == cr.commission else 0.0
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
        self.ensure_connected()
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
