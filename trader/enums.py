"""Enumerations fixed by the spec (v2.10 §4 run states and reason codes, §6, §12).

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
    SKIPPED = "SKIPPED"
    HALTED_FOR_DAY = "HALTED_FOR_DAY"
    HALTED_INTEGRITY = "HALTED_INTEGRITY"
    HALTED_BUYS = "HALTED_BUYS"
    KILLED = "KILLED"


class ReasonCode(StrEnum):
    """Reason codes (§4). The list is closed."""

    DATA_STALE = "DATA_STALE"
    DATA_MISMATCH = "DATA_MISMATCH"
    DATA_SPIKE = "DATA_SPIKE"
    DATA_RESTATED = "DATA_RESTATED"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    TR_CHECK = "TR_CHECK"
    SYMBOL_HALTED = "SYMBOL_HALTED"
    RECON_BREAK = "RECON_BREAK"
    KILL = "KILL"
    GATEWAY_DOWN = "GATEWAY_DOWN"
    TWOFA_MISSED = "TWOFA_MISSED"
    PLAN_NOT_DELIVERED = "PLAN_NOT_DELIVERED"
    USER_VETO = "USER_VETO"
    MIN_ORDER = "MIN_ORDER"
    BAND = "BAND"
    CASH_SHORT = "CASH_SHORT"
    SNAPSHOT_GAP = "SNAPSHOT_GAP"
    SNAPSHOT_GAP_CONFIRMED = "SNAPSHOT_GAP_CONFIRMED"
    NO_QUOTE = "NO_QUOTE"
    ADV_LIMIT = "ADV_LIMIT"
    MAX_ORDER_VALUE = "MAX_ORDER_VALUE"
    MAX_ORDERS = "MAX_ORDERS"
    MAX_TURNOVER = "MAX_TURNOVER"
    NO_SHORT = "NO_SHORT"
    IBKR_REJECT = "IBKR_REJECT"
    NOT_SENT = "NOT_SENT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CORP_ACTION = "CORP_ACTION"
    PENDING_FLEX = "PENDING_FLEX"
    CALENDAR_MISMATCH = "CALENDAR_MISMATCH"
    CLOCK_SKEW = "CLOCK_SKEW"
    EARLY_CLOSE = "EARLY_CLOSE"
    LICENCE = "LICENCE"
    DRAWDOWN_HALT = "DRAWDOWN_HALT"
    TRACKING_HALT = "TRACKING_HALT"
    COST_HALT = "COST_HALT"
    DIST_MISSING = "DIST_MISSING"
    ACCOUNT_MODE_MISMATCH = "ACCOUNT_MODE_MISMATCH"
    CANCEL_UNCONFIRMED = "CANCEL_UNCONFIRMED"
    DATA_BUDGET = "DATA_BUDGET"
    WITHDRAWAL = "WITHDRAWAL"
    FOREIGN_ORDER = "FOREIGN_ORDER"
    IDLE_CASH = "IDLE_CASH"


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class PlanKind(StrEnum):
    """Plan line / intent kinds (§3, §12)."""

    TRANSITION = "transition"
    TOP_UP = "top-up"
    BAND = "band"
    WITHDRAWAL = "withdrawal"
    CANARY = "canary"


class ParcelSource(StrEnum):
    FILL = "fill"
    INIT = "init"
    CORP_ACTION = "corp_action"
    MANUAL = "manual"
    RECOVERED = "recovered"


class FillSource(StrEnum):
    API = "api"
    FLEX = "flex"
    MANUAL = "manual"
    RECOVERED = "recovered"


class ParcelMethod(StrEnum):
    FIFO = "FIFO"
    HIFO = "HIFO"


class IbkrMode(StrEnum):
    PAPER = "paper"
    LIVE = "live"


class Verdict(StrEnum):
    """Per-symbol validation verdict (§3 MarketSnapshot.verdict, §6)."""

    OK = "OK"
    WARN = "WARN"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    BLOCK = "BLOCK"


class AlertLevel(StrEnum):
    """DAT-17 levels: INFO to the log, WARN to the digest, BLOCK refuses the symbol."""

    INFO = "INFO"
    WARN = "WARN"
    BLOCK = "BLOCK"


class DistributionStatus(StrEnum):
    EXPECTED = "expected"
    ESTIMATED = "estimated"
    FINAL = "final"


class DistributionSource(StrEnum):
    ISSUER = "issuer"
    VENDOR_BACKFILL = "vendor_backfill"


class CashflowStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    LAPSED = "lapsed"


class DataSource(StrEnum):
    """Market-data sources (§6). Raw files live under data/raw/{source}/."""

    EODHD = "eodhd"
    FLEX = "flex"
    RBA = "rba"
    ISSUER = "issuer"
