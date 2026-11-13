"""Enumerations fixed by the spec (§4 run states and reason codes, §12 tables).

New reason codes need a spec update (§4).
"""

from __future__ import annotations

from enum import StrEnum


class RunState(StrEnum):
    """Run states (§4)."""

    SCHEDULED = "SCHEDULED"
    DATA_READY = "DATA_READY"
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    NONE = "NONE"
    RECONCILED = "RECONCILED"
    HALTED_FOR_DAY = "HALTED_FOR_DAY"
    HALTED = "HALTED"
    KILLED = "KILLED"


class ReasonCode(StrEnum):
    """Reason codes (§4). The list is closed."""

    DATA_STALE = "DATA_STALE"
    DATA_MISMATCH = "DATA_MISMATCH"
    DATA_JUMP = "DATA_JUMP"
    SYMBOL_HALTED = "SYMBOL_HALTED"
    RECON_BREAK = "RECON_BREAK"
    KILL = "KILL"
    GATEWAY_DOWN = "GATEWAY_DOWN"
    TWOFA_MISSED = "TWOFA_MISSED"
    PLAN_NOT_DELIVERED = "PLAN_NOT_DELIVERED"
    USER_VETO = "USER_VETO"
    BLACKOUT = "BLACKOUT"
    REGIME_OFF = "REGIME_OFF"
    CAP_PER_NAME = "CAP_PER_NAME"
    CAP_CLUSTER = "CAP_CLUSTER"
    CAP_PORTFOLIO_VOL = "CAP_PORTFOLIO_VOL"
    CAP_CSL_GAP = "CAP_CSL_GAP"
    MIN_ORDER = "MIN_ORDER"
    MIN_WEIGHT_CHANGE = "MIN_WEIGHT_CHANGE"
    CASH_SHORT = "CASH_SHORT"
    COLLAR = "COLLAR"
    ADV_LIMIT = "ADV_LIMIT"
    MAX_ORDER_VALUE = "MAX_ORDER_VALUE"
    MAX_ORDERS = "MAX_ORDERS"
    NO_SHORT = "NO_SHORT"
    CROSS_USER = "CROSS_USER"
    DAILY_LOSS = "DAILY_LOSS"
    SOFT_DRAWDOWN = "SOFT_DRAWDOWN"
    HARD_DRAWDOWN = "HARD_DRAWDOWN"
    IBKR_REJECT = "IBKR_REJECT"
    MISSED_AUCTION = "MISSED_AUCTION"
    NOT_SENT = "NOT_SENT"
    CORP_ACTION = "CORP_ACTION"
    PENDING_FLEX = "PENDING_FLEX"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class EventType(StrEnum):
    """Event kinds for the ``events`` table (§5)."""

    RESULTS = "RESULTS"
    QUARTERLY_REVIEW = "QUARTERLY_REVIEW"
    AGM = "AGM"
    EX_DIVIDEND = "EX_DIVIDEND"  # no blackout; 45-day rule and reference prices
    RBA_DECISION = "RBA_DECISION"  # flag only, no blackout


# Event types that create a buy blackout (§5).
BLACKOUT_EVENT_TYPES: frozenset[EventType] = frozenset(
    {EventType.RESULTS, EventType.QUARTERLY_REVIEW, EventType.AGM}
)


class ParcelSource(StrEnum):
    FILL = "fill"
    INIT = "init"
    CORP_ACTION = "corp_action"


class ParcelMethod(StrEnum):
    FIFO = "FIFO"
    HIFO = "HIFO"
    MIN_TAX = "MIN_TAX"


class IbkrMode(StrEnum):
    PAPER = "paper"
    LIVE = "live"
