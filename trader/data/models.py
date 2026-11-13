"""Market database models (spec v2.10 §12): ``market_<user>``.

All market tables are append-only and bitemporal (DAT-18): every row carries
the trade date (or as-of date) and the fetch time; nothing is updated in place,
and the reading "as known at time T" takes the latest fetch time <= T.
The only mutable columns are ``distribution.status`` and, in ``hypotheses``,
status, result, decision and approver (§12); each update writes a row to this
database's ``audit_log``.

Tables beyond the §12 list (docs/DECISIONS.md L-10 to L-14, each a reported
spec gap): ``audit_log`` (market updates and imports need an audit row in the
same database), ``validated_close`` (DAT-04/DAT-17 "validated set"),
``vendor_dividend`` (DAT-22 vendor-reported dividends), ``spread_report``
(SYS-30 monthly spreads, "kept per instrument and month in the market
database", §3).
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Final

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Integer,
    MetaData,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from trader.dbtypes import (
    MUTABLE_COLUMNS,
    NAMING_CONVENTION,
    JSONType,
    MoneyType,
    PriceType,
    RateType,
    SeriesType,
    UTCDateTime,
    str_enum,
)
from trader.dbtypes import update_mutable as _update_mutable
from trader.dbtypes import write_audit as _write_audit
from trader.enums import DistributionSource, DistributionStatus


class MarketBase(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {  # noqa: RUF012
        datetime: UTCDateTime(),
        Decimal: MoneyType(),
        date: Date(),
        time: Time(),
        str: String(),
        int: Integer(),
        bool: Boolean(),
    }


_SYM = 12


class Instrument(MarketBase):
    """Instrument reference data, versioned insert-only (docs/DECISIONS.md L-08).

    ``id`` is the stable internal id used by every other market table; a change
    (symbol, con_id re-qualification, tick rules, delisting) inserts a new
    ``version``. The current record is the highest version (SYS-20, SYS-29,
    SYS-32).
    """

    __tablename__ = "instrument"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(_SYM))
    symbol_history: Mapped[list[str]] = mapped_column(JSONType, default=list)
    exchange: Mapped[str] = mapped_column(String(12))
    currency: Mapped[str] = mapped_column(String(3))
    issuer: Mapped[str | None] = mapped_column(String(64))
    con_id: Mapped[int | None] = mapped_column(BigInteger)
    # IBKR market-rule price increments [[low_edge, increment], ...] as strings (SYS-29)
    tick_rules: Mapped[list[list[str]] | None] = mapped_column(JSONType)
    list_date: Mapped[date | None] = mapped_column(Date)
    delist_date: Mapped[date | None] = mapped_column(Date)
    delist_reason: Mapped[str | None] = mapped_column(Text)
    final_payout: Mapped[Decimal | None] = mapped_column(RateType())
    source: Mapped[str] = mapped_column(String(64))
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime())


class RawBar(MarketBase):
    """Raw daily bars as fetched (EODHD) and Flex marks (close only)."""

    __tablename__ = "raw_bar"
    instrument_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    source: Mapped[str] = mapped_column(String(16), primary_key=True)
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    open: Mapped[Decimal | None] = mapped_column(PriceType())
    high: Mapped[Decimal | None] = mapped_column(PriceType())
    low: Mapped[Decimal | None] = mapped_column(PriceType())
    close: Mapped[Decimal] = mapped_column(PriceType())
    volume: Mapped[int | None] = mapped_column(BigInteger)
    vendor_adjusted_close: Mapped[Decimal | None] = mapped_column(RateType())
    file_hash: Mapped[str] = mapped_column(String(64))
    licensee: Mapped[str] = mapped_column(String(16))


class Distribution(MarketBase):
    __tablename__ = "distribution"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(Integer)
    ex_date: Mapped[date] = mapped_column(Date)
    record_date: Mapped[date | None] = mapped_column(Date)
    pay_date: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    cash_amount: Mapped[Decimal | None] = mapped_column(RateType())  # per unit, AUD
    franking_credit: Mapped[Decimal | None] = mapped_column(RateType())  # per unit, AUD
    components: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    status: Mapped[DistributionStatus] = mapped_column(
        str_enum(DistributionStatus, "distribution_status")
    )
    source: Mapped[DistributionSource] = mapped_column(
        str_enum(DistributionSource, "distribution_source")
    )
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime())
    __table_args__ = (
        CheckConstraint(
            "(status = 'expected' AND cash_amount IS NULL) OR "
            "(status <> 'expected' AND cash_amount IS NOT NULL AND cash_amount >= 0)",
            name="amount_iff_not_expected",
        ),
    )


class CorpAction(MarketBase):
    __tablename__ = "corp_action"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(32))
    ex_date: Mapped[date] = mapped_column(Date)
    ratio: Mapped[Decimal | None] = mapped_column(RateType())  # unit ratio s_t (new / old)
    source: Mapped[str] = mapped_column(String(64))
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime())


class CalendarDay(MarketBase):
    """Session dates, loaded by hand from the ASX calendar (OPS-05).

    Bitemporal (DAT-18): key (venue, date, fetch_time); the latest fetch wins
    (docs/DECISIONS.md L-11).
    """

    __tablename__ = "calendar"
    venue: Mapped[str] = mapped_column(String(8), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    is_trading: Mapped[bool] = mapped_column(Boolean)
    close_time: Mapped[time | None] = mapped_column(Time)  # venue wall clock
    source: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint(
            "(is_trading AND close_time IS NOT NULL) OR (NOT is_trading AND close_time IS NULL)",
            name="close_time_iff_trading",
        ),
    )


class Fx(MarketBase):
    __tablename__ = "fx"
    series: Mapped[str] = mapped_column(String(16), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    value: Mapped[Decimal] = mapped_column(RateType())
    source: Mapped[str] = mapped_column(String(64))


class CashRate(MarketBase):
    __tablename__ = "cash_rate"
    series: Mapped[str] = mapped_column(String(16), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    value: Mapped[Decimal] = mapped_column(RateType())
    source: Mapped[str] = mapped_column(String(64))


class QcEvent(MarketBase):
    __tablename__ = "qc_event"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    instrument_id: Mapped[int | None] = mapped_column(Integer)  # None: whole-run check
    trade_date: Mapped[date | None] = mapped_column(Date)
    check_id: Mapped[str] = mapped_column(String(16))
    level: Mapped[str] = mapped_column(String(16))
    detail: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    override_by: Mapped[str | None] = mapped_column(String(64))
    override_reason: Mapped[str | None] = mapped_column(Text)


class ValidatedClose(MarketBase):
    """The validated set (DAT-04, DAT-17, DAT-21): one row per verdict issue.

    The latest ``validated_at`` per (instrument, trade date) is the record.
    """

    __tablename__ = "validated_close"
    instrument_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    validated_at: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    close: Mapped[Decimal] = mapped_column(PriceType())
    source: Mapped[str] = mapped_column(String(16))  # eodhd, flex or override
    verdict: Mapped[str] = mapped_column(String(16))
    backfill: Mapped[bool] = mapped_column(Boolean)
    signals_ok: Mapped[bool] = mapped_column(Boolean)  # False for a Flex-only close (DAT-02 c)
    override_id: Mapped[int | None] = mapped_column(Integer)  # qc_event id (DAT-17)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)


class VendorDividend(MarketBase):
    """Vendor-reported dividends, a cross-check only (DAT-14, DAT-22)."""

    __tablename__ = "vendor_dividend"
    instrument_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ex_date: Mapped[date] = mapped_column(Date, primary_key=True)
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    value: Mapped[Decimal] = mapped_column(RateType())
    unadjusted_value: Mapped[Decimal | None] = mapped_column(RateType())
    currency: Mapped[str | None] = mapped_column(String(3))
    record_date: Mapped[date | None] = mapped_column(Date)
    payment_date: Mapped[date | None] = mapped_column(Date)
    file_hash: Mapped[str] = mapped_column(String(64))
    licensee: Mapped[str] = mapped_column(String(16))


class SpreadReport(MarketBase):
    """Monthly reported spread per instrument (SYS-30), entered by hand."""

    __tablename__ = "spread_report"
    instrument_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), primary_key=True)  # YYYY-MM
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    spread: Mapped[Decimal] = mapped_column(RateType())  # fraction, 0.0002 = 0.02%
    source: Mapped[str] = mapped_column(Text)


class TrSeries(MarketBase):
    __tablename__ = "tr_series"
    build_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    tr_net: Mapped[Decimal] = mapped_column(SeriesType())
    tr_gross: Mapped[Decimal] = mapped_column(SeriesType())
    inputs_as_of: Mapped[datetime] = mapped_column(UTCDateTime())


class Hypothesis(MarketBase):
    __tablename__ = "hypotheses"
    card_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    version: Mapped[int] = mapped_column(Integer)
    card_hash: Mapped[str] = mapped_column(String(64))
    frozen_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    card_content: Mapped[str] = mapped_column(Text)
    family: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16))
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    decision: Mapped[str | None] = mapped_column(Text)
    approver: Mapped[str | None] = mapped_column(String(64))


class Trial(MarketBase):
    __tablename__ = "trials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    card_id: Mapped[str | None] = mapped_column(String(16))
    family: Mapped[str] = mapped_column(String(8))
    trial_spec_id: Mapped[str] = mapped_column(String(128))
    is_trial: Mapped[bool] = mapped_column(Boolean)
    replication_kind: Mapped[str] = mapped_column(String(32))
    card_hash: Mapped[str | None] = mapped_column(String(64))
    data_hash: Mapped[str] = mapped_column(String(64))
    config_hash: Mapped[str] = mapped_column(String(64))
    period: Mapped[str] = mapped_column(String(32))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONType)
    registered: Mapped[bool] = mapped_column(Boolean)


class Cpi(MarketBase):
    """CPI series for indexation (TAX-04, T9)."""

    __tablename__ = "cpi"
    quarter: Mapped[str] = mapped_column(String(7), primary_key=True)  # e.g. 2027Q3
    fetch_time: Mapped[datetime] = mapped_column(UTCDateTime(), primary_key=True)
    value: Mapped[Decimal] = mapped_column(RateType())
    source: Mapped[str] = mapped_column(Text)


class VendorCallLog(MarketBase):
    """The DAT-23 call counter: one row per vendor request (survives restarts)."""

    __tablename__ = "vendor_call_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    vendor: Mapped[str] = mapped_column(String(16))
    endpoint: Mapped[str] = mapped_column(String(64))
    gmt_date: Mapped[date] = mapped_column(Date, index=True)


class MarketAuditLog(MarketBase):
    """Append-only audit of market-database updates and hand-entered loads."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType)
    __table_args__ = {"implicit_returning": False}  # noqa: RUF012


MARKET_TABLES: Final = frozenset(MarketBase.metadata.tables)
MARKET_MUTABLE_COLUMNS: Final = {t: c for t, c in MUTABLE_COLUMNS.items() if t in MARKET_TABLES}
MARKET_INSERT_ONLY_TABLES: Final = frozenset(
    t for t in MARKET_TABLES if t not in MARKET_MUTABLE_COLUMNS
)
SPEC_MARKET_TABLES: Final = frozenset(
    {
        "instrument", "raw_bar", "distribution", "corp_action", "calendar", "fx", "cash_rate",
        "qc_event", "tr_series", "hypotheses", "trials", "cpi", "vendor_call_log",
    }
)  # fmt: skip
EXTRA_MARKET_TABLES: Final = frozenset(
    {"audit_log", "validated_close", "vendor_dividend", "spread_report"}
)


def write_market_audit(
    session: Session, *, actor: str, action: str, payload: dict[str, Any]
) -> None:
    _write_audit(session, MarketBase, actor=actor, action=action, payload=payload)


def update_market_mutable(
    session: Session, obj: MarketBase, column: str, value: Any, *, actor: str, reason: str
) -> None:
    _update_mutable(session, obj, column, value, actor=actor, reason=reason)
