"""Broker protocol and the paper/live guard (FD v3.0 §11; BW-EXE-09; BF3).

**This build cannot place a real order.** ``LIVE_TRADING_ENABLED`` is a hard-coded
``False`` that every broker checks before it connects and before every order, and the
config flag ``bfast.broker.allow_live`` is typed ``Literal[False]`` (a ``true`` value
fails validation). ``assert_paper`` additionally requires a paper account id
(``DU...``) and a paper gateway port. Live enablement is a separate, later owner step
after the go-live checklist (FD §21.1): it needs a code change reviewed by the owner,
not a config edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Final, Protocol

from trader.orders import OrderType, Side

LIVE_TRADING_ENABLED: Final = False  # hard-coded; never read from config or environment

# Paper ports: IB Gateway 4002, gnzsnz/ib-gateway socat relay 4004, TWS 7497.
PAPER_PORTS: Final = frozenset({4002, 4004, 7497})
LIVE_PORTS: Final = frozenset({4001, 4003, 7496})


class LiveTradingRefusedError(RuntimeError):
    """Any attempt to reach a live account, port or mode."""


def assert_paper(
    *, mode: str, account_id: str | None, port: int | None, allow_live: bool = False
) -> None:
    """BW-EXE-09 / EXE-12 carried: refuse anything that is not provably paper."""
    if LIVE_TRADING_ENABLED or allow_live:
        raise LiveTradingRefusedError(
            "live trading is disabled in this build (separate owner step)"
        )
    if mode != "paper":
        raise LiveTradingRefusedError(f"broker mode {mode!r} refused: this build is paper only")
    if port is not None and (port in LIVE_PORTS or port not in PAPER_PORTS):
        raise LiveTradingRefusedError(
            f"port {port} is not a paper gateway port {sorted(PAPER_PORTS)}"
        )
    if account_id is not None and not account_id.startswith("DU"):
        raise LiveTradingRefusedError(f"account {account_id!r} is not a paper account (DU...)")


class BrokerTimeoutError(RuntimeError):
    """The broker did not acknowledge in time. The order is NOT resent (EXE-10 carried)."""


class BrokerRejectedError(RuntimeError):
    pass


def exec_base(exec_id: str) -> str:
    """IBKR execution ids end in ``.NN``; a correction keeps the base and raises the
    suffix (review L6), so fills are de-duplicated on the base."""
    head, _, tail = str(exec_id).rpartition(".")
    return head if head and tail.isdigit() and len(tail) <= 2 else str(exec_id)


class BrokerDisconnectedError(RuntimeError):
    """Review H1: the gateway is down or not logged in and a bounded reconnect failed.
    The scheduler pages and exits non-zero so Docker restarts the trader."""


@dataclass(frozen=True)
class OrderRequest:
    client_order_id: str  # sent as orderRef
    account: str
    symbol: str
    side: Side
    qty: int
    order_type: OrderType
    limit_price: Decimal
    tif: str = "DAY"


@dataclass(frozen=True)
class OrderState:
    client_order_id: str
    broker_order_id: str
    perm_id: str
    status: str  # broker status text (Submitted, PreSubmitted, Filled, Cancelled, Inactive...)
    filled: int
    remaining: int


@dataclass(frozen=True)
class Execution:
    exec_id: str
    client_order_id: str | None  # orderRef; None for an order this system did not send
    symbol: str
    side: Side
    qty: int
    price: Decimal
    commission: Decimal
    time: datetime


@dataclass(frozen=True)
class AccountSnapshot:
    account: str
    settled_cash: Decimal
    available_funds: Decimal
    net_liquidation: Decimal
    total_cash: Decimal | None = None  # settled + unsettled; reconciliation compares this

    @property
    def ledger_cash(self) -> Decimal:
        return self.total_cash if self.total_cash is not None else self.settled_cash


@dataclass(frozen=True)
class BrokerQuote:
    symbol: str
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    close: Decimal | None
    time: datetime


class Broker(Protocol):
    account_id: str
    is_paper: bool

    def place(self, req: OrderRequest, timeout: float = 10.0) -> OrderState: ...
    def cancel(self, client_order_id: str) -> bool: ...
    def find_order(self, client_order_id: str) -> OrderState | None: ...
    def open_orders(self) -> list[OrderState]: ...
    def positions(self) -> dict[str, int]: ...
    def account(self) -> AccountSnapshot: ...
    def executions(self) -> list[Execution]: ...
    def quote(self, symbol: str) -> BrokerQuote | None: ...
