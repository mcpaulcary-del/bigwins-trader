"""Simulated broker (port of the kept ``trader_system`` SimBroker, Decimal money; FD §3.4).

Fills pending orders at the close of the session passed to ``advance()`` (closing
auction semantics): a buy fills if the close is at or under its limit, a sell if at or
over it; fill price = close x (1 +/- half spread); commission by ``CommissionModel``.
An order with no close that session expires (DAY). Used for the ``EMG2_20_SIM`` twin
(L13) and as the in-process broker of the execution tests. Never live.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from trader.broker.base import (
    AccountSnapshot,
    BrokerQuote,
    BrokerRejectedError,
    Execution,
    OrderRequest,
    OrderState,
    assert_paper,
)
from trader.orders import CommissionModel, Side

Q4 = Decimal("0.0001")


@dataclass
class _Pending:
    req: OrderRequest
    oid: str
    status: str = "Submitted"
    filled: int = 0


@dataclass
class SimBroker:
    account_id: str = "DUSIM0001"
    cash: Decimal = Decimal(0)
    half_spread: Decimal = Decimal(0)
    # per-symbol half-spread (BF-D28: the L15 fund's spread a side); others use half_spread
    half_spread_by: dict[str, Decimal] = field(default_factory=dict)
    commission: CommissionModel = field(default_factory=CommissionModel)
    is_paper: bool = True
    holdings: dict[str, int] = field(default_factory=dict)
    orders: dict[str, _Pending] = field(default_factory=dict)
    fills_: list[Execution] = field(default_factory=list)
    last_close: dict[str, Decimal] = field(default_factory=dict)
    place_calls: int = 0
    exec_prefix: str = "SIM"  # execution ids are "<prefix>-<day>-<oid>": unique per book

    def __post_init__(self) -> None:
        assert_paper(mode="paper", account_id=self.account_id, port=None)

    # -------------------------------------------------------------- Broker protocol
    def place(self, req: OrderRequest, timeout: float = 10.0) -> OrderState:
        assert_paper(mode="paper", account_id=req.account, port=None)
        self.place_calls += 1
        if req.client_order_id in self.orders:
            raise BrokerRejectedError(f"duplicate orderRef {req.client_order_id}")
        if req.qty <= 0:
            raise BrokerRejectedError("quantity must be positive")
        p = _Pending(req, f"S{len(self.orders) + 1}")
        self.orders[req.client_order_id] = p
        return self._state(p)

    def cancel(self, client_order_id: str) -> bool:
        p = self.orders.get(client_order_id)
        if p is None or p.status not in ("Submitted", "PreSubmitted"):
            return False
        p.status = "Cancelled"
        return True

    def find_order(self, client_order_id: str) -> OrderState | None:
        p = self.orders.get(client_order_id)
        return self._state(p) if p else None

    def open_orders(self) -> list[OrderState]:
        return [self._state(p) for p in self.orders.values() if p.status == "Submitted"]

    def positions(self) -> dict[str, int]:
        return {k: v for k, v in sorted(self.holdings.items()) if v}

    def account(self) -> AccountSnapshot:
        nav = self.cash + sum(
            (self.last_close.get(s, Decimal(0)) * q for s, q in self.holdings.items()), Decimal(0)
        )
        return AccountSnapshot(self.account_id, self.cash, self.cash, nav)

    def executions(self) -> list[Execution]:
        return list(self.fills_)

    def quote(self, symbol: str) -> BrokerQuote | None:
        c = self.last_close.get(symbol)
        if c is None:
            return None
        return BrokerQuote(symbol, c, c, c, c, datetime.now(UTC))

    @classmethod
    def from_journal(
        cls,
        journal: Any,
        book: str,
        half_spread: Decimal = Decimal(0),
        account_id: str = "DUSIM0001",
        exec_prefix: str = "SIM",
        half_spread_by: dict[str, Decimal] | None = None,
    ) -> SimBroker:
        """Rebuild the simulated book after a restart: cash and positions from the journal,
        and the orders the journal says were sent but not yet settled."""
        sb = cls(
            account_id=account_id,
            cash=journal.cash(book),
            half_spread=half_spread,
            half_spread_by=dict(half_spread_by or {}),
            holdings=dict(journal.positions(book)),
            exec_prefix=exec_prefix,
        )
        for it, _ in journal.intents_in(["SENT", "PARTIAL"], book):
            if it.book == book:
                sb.place(
                    OrderRequest(
                        it.client_order_id,
                        account_id,
                        it.entity,
                        it.side,
                        it.qty,
                        it.order_type,
                        it.limit_price,
                    )
                )
        sb.place_calls = 0
        return sb

    # -------------------------------------------------------------- simulation clock
    def advance(self, day: date, closes: dict[str, Decimal]) -> list[Execution]:
        """The closing auction of ``day``: sells first, then buys."""
        self.last_close.update(closes)
        out: list[Execution] = []
        live = [p for p in self.orders.values() if p.status == "Submitted"]
        for p in sorted(live, key=lambda p: p.req.side is Side.BUY):
            r = p.req
            c = closes.get(r.symbol)
            if c is None:
                p.status = "Cancelled"  # DAY order, no close: expires
                continue
            if (r.side is Side.BUY and c > r.limit_price) or (
                r.side is Side.SELL and c < r.limit_price
            ):
                p.status = "Cancelled"  # not filled in the auction
                continue
            hs = self.half_spread_by.get(r.symbol, self.half_spread)
            px = c * (1 + hs) if r.side is Side.BUY else c * (1 - hs)
            px = px.quantize(Q4, ROUND_HALF_EVEN)
            comm = self.commission(c * r.qty)
            if r.side is Side.BUY:
                cost = px * r.qty + comm
                if cost > self.cash:
                    p.status = "Inactive"  # rejected: insufficient funds
                    continue
                self.cash -= cost
                self.holdings[r.symbol] = self.holdings.get(r.symbol, 0) + r.qty
            else:
                held = self.holdings.get(r.symbol, 0)
                if r.qty > held:
                    p.status = "Inactive"
                    continue
                self.holdings[r.symbol] = held - r.qty
                self.cash += px * r.qty - comm
            p.status, p.filled = "Filled", r.qty
            ex = Execution(
                f"{self.exec_prefix}-{day.isoformat()}-{p.oid}",
                r.client_order_id,
                r.symbol,
                r.side,
                r.qty,
                px,
                comm,
                datetime.combine(day, time(6, 10), UTC),
            )
            self.fills_.append(ex)
            out.append(ex)
        return out

    @staticmethod
    def _state(p: _Pending) -> OrderState:
        return OrderState(
            p.req.client_order_id, p.oid, p.oid, p.status, p.filled, p.req.qty - p.filled
        )
