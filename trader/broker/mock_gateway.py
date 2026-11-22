"""Mock IB Gateway: the subset of ``ib_async.IB`` that ``IbkrPaperBroker`` uses (BF3).

Used by the test suite and by the B-fast dry-run harness (``trader.bf_app``); it never
opens a socket.

It uses real ``ib_async`` objects (``Trade``, ``OrderStatus``, ``Fill``...), keeps the
gateway's view of orders across a simulated gateway restart (``restart()`` clears the
client-side ``trades()`` like a reconnect does, while ``reqCompletedOrders`` and
``reqAllOpenOrders`` still return them) and records every ``placeOrder`` call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ib_async import (
    AccountValue,
    CommissionReport,
    Contract,
    Execution,
    Fill,
    Order,
    OrderStatus,
    Position,
    Ticker,
    Trade,
)


@dataclass
class MockGateway:
    accounts: tuple[str, ...] = ("DU1234567",)
    ack: str = "Submitted"  # "Submitted" | "never" (timeout) | "Inactive" (reject)
    cash: float = 10000.0
    connected: bool = False
    placed: list[tuple[Contract, Order]] = field(default_factory=list)
    gateway_trades: list[Trade] = field(default_factory=list)
    session_trades: list[Trade] = field(default_factory=list)
    fills_: list[Fill] = field(default_factory=list)
    pos: dict[str, float] = field(default_factory=dict)
    connect_args: dict[str, Any] = field(default_factory=dict)
    md_type: int = 0
    next_id: int = 1
    marks: dict[str, float] = field(default_factory=dict)
    unsettled: float = 0.0  # sale proceeds not yet settled (O-2 stand-in)
    clock: datetime = datetime(2026, 12, 1, 5, 10, tzinfo=UTC)  # execution time of fills
    # review H2: an async-style gateway: events wait here until the client's loop runs
    # (``sleep`` / ``waitOnUpdate``); False = they are applied at once (the default)
    async_events: bool = False
    pending: list[Any] = field(default_factory=list)
    quote_time: datetime | None = None  # review M3: None = a fresh quote
    login_ok: bool = True  # review H1: False = the gateway is up but not logged in
    connects: int = 0

    # session
    def connect(
        self,
        host: str,
        port: int,
        clientId: int,
        timeout: float,
        readonly: bool,
        account: str,
    ) -> None:
        if not self.login_ok:
            raise ConnectionRefusedError("gateway not logged in")
        self.connected = True
        self.connects += 1
        self.connect_args = {"host": host, "port": port, "clientId": clientId, "account": account}

    def disconnect(self) -> None:
        self.connected = False

    def managedAccounts(self) -> list[str]:
        return list(self.accounts)

    def reqMarketDataType(self, t: int) -> None:
        self.md_type = t

    def isConnected(self) -> bool:
        return self.connected

    def sleep(self, secs: float = 0.02) -> bool:
        self._run_pending()
        return True

    def waitOnUpdate(self, timeout: float = 0) -> bool:
        self._run_pending()
        return True

    def _run_pending(self) -> None:
        while self.pending:
            self.pending.pop(0)()

    def reqExecutions(self, execFilter: Any = None) -> list[Fill]:
        self._run_pending()
        return list(self.fills_)

    def restart(self) -> None:
        self.session_trades = []

    # contracts and orders
    def qualifyContracts(self, *cs: Contract) -> list[Contract]:
        out = []
        for c in cs:
            c.conId = abs(hash(c.symbol)) % 10**8
            out.append(c)
        return out

    def placeOrder(self, contract: Contract, order: Order) -> Trade:
        if not self.connected:
            raise ConnectionError("not connected")
        self.placed.append((contract, order))
        order.orderId = self.next_id
        order.permId = 9000 + self.next_id
        self.next_id += 1
        st = "PendingSubmit" if self.ack == "never" else self.ack
        t = Trade(
            contract=contract,
            order=order,
            orderStatus=OrderStatus(
                orderId=order.orderId,
                status=st,
                filled=0,
                remaining=order.totalQuantity,
                permId=order.permId,
            ),
        )
        self.gateway_trades.append(t)
        self.session_trades.append(t)
        return t

    def trades(self) -> list[Trade]:
        return list(self.session_trades)

    def openTrades(self) -> list[Trade]:
        return [
            t for t in self.session_trades if t.orderStatus.status in ("Submitted", "PreSubmitted")
        ]

    def reqAllOpenOrders(self) -> list[Trade]:
        return [
            t for t in self.gateway_trades if t.orderStatus.status in ("Submitted", "PreSubmitted")
        ]

    def reqCompletedOrders(self, apiOnly: bool) -> list[Trade]:
        return [
            t
            for t in self.gateway_trades
            if t.orderStatus.status not in ("Submitted", "PreSubmitted")
        ]

    def cancelOrder(self, order: Order) -> Trade | None:
        for t in self.gateway_trades:
            if t.order.permId == order.permId:
                t.orderStatus.status = "Cancelled"
                return t
        return None

    # broker-side events driven by the test
    def auction(self, closes: dict[str, float], when: datetime | None = None) -> int:
        """The closing auction: every open DAY order fills at the close if its limit
        allows, else it is cancelled (DAY). Commission max(A$6.60, 0.088%) to the cent."""
        if when is not None:
            self.clock = when.astimezone(UTC)
        n = 0
        for t in list(self.gateway_trades):
            if t.orderStatus.status not in ("Submitted", "PreSubmitted"):
                continue
            c = closes.get(t.contract.symbol)
            buy = t.order.action == "BUY"
            lim = float(t.order.lmtPrice or 0.0)
            if c is None or (buy and c > lim) or (not buy and c < lim):
                t.orderStatus.status = "Cancelled"
                continue
            q = t.order.totalQuantity - t.orderStatus.filled
            comm = max(660, -(-round(0.088 * c * q * 100) // 100)) / 100
            self.fill(t.order.orderRef, c, commission=comm)
            n += 1
        self.marks.update(closes)
        return n

    def fill(
        self, order_ref: str, price: float, qty: float | None = None, commission: float = 6.6
    ) -> None:
        if self.async_events:  # review H2: delivered only when the client's loop runs
            self.pending.append(lambda: self._fill(order_ref, price, qty, commission))
            return
        self._fill(order_ref, price, qty, commission)

    def _fill(self, order_ref: str, price: float, qty: float | None, commission: float) -> None:
        t = next(t for t in self.gateway_trades if t.order.orderRef == order_ref)
        q = qty if qty is not None else t.order.totalQuantity - t.orderStatus.filled
        t.orderStatus.filled += q
        t.orderStatus.remaining -= q
        t.orderStatus.status = "Filled" if t.orderStatus.remaining == 0 else "Submitted"
        side = "BOT" if t.order.action == "BUY" else "SLD"
        ex_id = f"E{len(self.fills_) + 1:04d}"
        ex = Execution(
            execId=ex_id,
            time=self.clock,
            acctNumber=t.order.account,
            side=side,
            shares=q,
            price=price,
            permId=t.order.permId,
            orderId=t.order.orderId,
            orderRef=order_ref,
        )
        self.fills_.append(
            Fill(t.contract, ex, CommissionReport(execId=ex_id, commission=commission), self.clock)
        )
        sym = t.contract.symbol
        self.pos[sym] = self.pos.get(sym, 0.0) + (q if side == "BOT" else -q)
        self.cash += (-q * price if side == "BOT" else q * price) - commission

    def fills(self) -> list[Fill]:
        return list(self.fills_)  # the client's cache: only what its loop has processed

    def positions(self, account: str = "") -> list[Position]:
        return [
            Position(
                account, Contract(symbol=s, secType="STK", exchange="ASX", currency="AUD"), q, 0.0
            )
            for s, q in self.pos.items()
        ]

    def accountValues(self, account: str = "") -> list[AccountValue]:
        nav = self.cash + sum(q * self.marks.get(s, 1.0) for s, q in self.pos.items())
        return [
            AccountValue(account, "SettledCash", str(self.cash - self.unsettled), "AUD", ""),
            AccountValue(account, "AvailableFunds", str(self.cash - self.unsettled), "AUD", ""),
            AccountValue(account, "TotalCashValue", str(self.cash), "AUD", ""),
            AccountValue(account, "NetLiquidation", str(nav), "AUD", ""),
        ]

    def reqTickers(self, *cs: Contract, regulatorySnapshot: bool = False) -> list[Ticker]:
        out = []
        for c in cs:
            t = Ticker(contract=c)
            m = self.marks.get(c.symbol)
            if m is None:  # no price yet (before the first auction): a quote of 1.00
                t.bid, t.ask, t.last, t.close = 0.995, 1.005, float("nan"), 0.99
            else:  # review M3: the last auction close, as a delayed quote would show it
                t.bid, t.ask, t.last, t.close = m * 0.995, m * 1.005, m, m
            t.time = self.quote_time or datetime.now(UTC)
            out.append(t)
        return out
