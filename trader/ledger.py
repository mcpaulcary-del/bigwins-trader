"""Ledger: SQLAlchemy models for the §12 tables, plus mutability and audit rules.

Each user has their own PostgreSQL database (``ledger_a``, ``ledger_b``). Schema
changes are Alembic migrations (``migrations/``), forward-only.

Conventions
-----------
* Money is ``NUMERIC(18,4)`` AUD, mapped to ``Decimal``; floats are refused on
  bind (SYS-13).
* Timestamps are ``TIMESTAMP WITH TIME ZONE`` stored in UTC; naive datetimes are
  refused on bind (SYS-14). Date columns are ASX local dates.

Mutability (§12)
----------------
Only the columns in ``MUTABLE_COLUMNS`` may be updated; every update also writes
an ``audit_log`` row (use ``update_mutable``). All other tables are insert-only;
corrections are new rows. Deletes are never allowed. This is enforced three
ways:

1. ``install_mutability_guard`` - a ``before_flush`` hook that raises on any
   update outside the allow-list and on any delete;
2. Postgres column-level grants for the app role (migration 0002) - SELECT and
   INSERT on every table, UPDATE only on the allowed columns, no DELETE;
3. ``audit_log``: the app role has INSERT only, and a trigger rejects UPDATE,
   DELETE and TRUNCATE for every role (migration 0002).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any, Final

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Dialect,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    event,
    insert,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.types import TypeDecorator

from trader.constants import MONEY_PRECISION, MONEY_SCALE, PRICE_PRECISION, PRICE_SCALE
from trader.enums import EventType, ParcelSource, ReasonCode, RunState, Side
from trader.money import MoneyTypeError
from trader.timeutil import ensure_utc, utc_now

NAMING_CONVENTION: Final = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ---------------------------------------------------------------------------
# Column types
# ---------------------------------------------------------------------------


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-aware timestamp, always stored and returned in UTC (SYS-14)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:  # SQLite returns naive; we only ever stored UTC.
            return value.replace(tzinfo=UTC)
        return ensure_utc(value)


class MoneyType(TypeDecorator[Decimal]):
    """NUMERIC(18,4) AUD as ``Decimal``; floats are refused (SYS-13)."""

    impl = Numeric(MONEY_PRECISION, MONEY_SCALE, asdecimal=True)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, float | bool) or not isinstance(value, Decimal | int):
            raise MoneyTypeError(f"money column requires Decimal, got {type(value).__name__}")
        return Decimal(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Decimal | None:
        if value is None:
            return None
        return value if isinstance(value, Decimal) else Decimal(str(value))


class PriceType(MoneyType):
    """Unadjusted prices, same rules as money."""

    impl = Numeric(PRICE_PRECISION, PRICE_SCALE, asdecimal=True)
    cache_ok = True


JSONType = JSON().with_variant(JSONB(), "postgresql")
# Weights are stored exactly (not as float) so plans are reproducible.
WeightType = Numeric(20, 10, asdecimal=True)


def _enum(e: type[Any], name: str) -> SAEnum:
    return SAEnum(
        e,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda x: [m.value for m in x],
        validate_strings=True,
    )


class Base(DeclarativeBase):
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


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


class Instrument(Base):
    __tablename__ = "instruments"
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    con_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    exchange: Mapped[str] = mapped_column(String(12))
    currency: Mapped[str] = mapped_column(String(3))
    cluster: Mapped[str] = mapped_column(String(16))
    vol_floor: Mapped[float | None] = mapped_column(Float)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CalendarDay(Base):
    """One row per calendar date. Holidays and half-days come only from here (OPS-05)."""

    __tablename__ = "calendar"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    is_trading: Mapped[bool] = mapped_column(Boolean)
    close_time: Mapped[time | None] = mapped_column(Time)  # Australia/Sydney wall clock
    __table_args__ = (
        CheckConstraint(
            "(is_trading AND close_time IS NOT NULL) OR (NOT is_trading AND close_time IS NULL)",
            name="close_time_iff_trading",
        ),
    )


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str | None] = mapped_column(String(12))  # None for market-wide (RBA)
    type: Mapped[EventType] = mapped_column(_enum(EventType, "event_type"))
    date: Mapped[date] = mapped_column(Date)
    is_estimate: Mapped[bool] = mapped_column(Boolean)
    source: Mapped[str] = mapped_column(Text)
    __table_args__ = (Index("ix_events_symbol_date", "symbol", "date"),)


class CorporateAction(Base):
    __tablename__ = "corporate_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(12))
    type: Mapped[str] = mapped_column(String(32))
    ex_date: Mapped[date] = mapped_column(Date)
    ratio: Mapped[Decimal | None] = mapped_column(Numeric(20, 10, asdecimal=True))
    cash_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    applied_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    applied_by: Mapped[str | None] = mapped_column(String(64))


# ---------------------------------------------------------------------------
# Runs, signals, state, plans
# ---------------------------------------------------------------------------


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user: Mapped[str] = mapped_column(String(16))
    decision_date: Mapped[date] = mapped_column(Date)
    execution_date: Mapped[date] = mapped_column(Date)
    state: Mapped[RunState] = mapped_column(_enum(RunState, "run_state"))
    reason_code: Mapped[ReasonCode | None] = mapped_column(_enum(ReasonCode, "reason_code"))
    config_hash: Mapped[str] = mapped_column(String(64))  # OPS-10
    git_sha: Mapped[str] = mapped_column(String(40))
    data_hashes: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    __table_args__ = (
        UniqueConstraint("user", "decision_date", "execution_date", name="uq_runs_cycle"),
        CheckConstraint("execution_date > decision_date", name="e_after_d"),
    )


class SignalRow(Base):
    __tablename__ = "signals"
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    family: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONType)


class ShadowSignal(Base):
    __tablename__ = "shadow_signals"
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    module: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONType)


class StrategyState(Base):
    """Versioned by decision date, insert-only (SYS-17)."""

    __tablename__ = "strategy_state"
    decision_date: Mapped[date] = mapped_column(Date, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    trend_entry_date: Mapped[date | None] = mapped_column(Date)
    stop_until: Mapped[date | None] = mapped_column(Date)
    dip_open: Mapped[bool] = mapped_column(Boolean)
    dip_fill_date: Mapped[date | None] = mapped_column(Date)
    regime_on: Mapped[bool] = mapped_column(Boolean)
    csl_gap_cap_active: Mapped[bool] = mapped_column(Boolean)


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class PlanLine(Base):
    __tablename__ = "plan_lines"
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    target_weight: Mapped[Decimal] = mapped_column(WeightType)
    target_qty: Mapped[int] = mapped_column(BigInteger)
    reasons: Mapped[list[str]] = mapped_column(JSONType)


# ---------------------------------------------------------------------------
# Orders and fills
# ---------------------------------------------------------------------------


class OrderIntent(Base):
    __tablename__ = "order_intents"
    client_order_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    execution_date: Mapped[date] = mapped_column(Date)
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[Side] = mapped_column(_enum(Side, "side"))
    qty: Mapped[int] = mapped_column(BigInteger)
    ref_price: Mapped[Decimal] = mapped_column(PriceType())
    limit_price: Mapped[Decimal | None] = mapped_column(PriceType())  # VAS: set at 10:45
    ladder_step: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16))
    reason_code: Mapped[ReasonCode | None] = mapped_column(_enum(ReasonCode, "reason_code"))
    risk_decision: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    __table_args__ = (
        UniqueConstraint("execution_date", "symbol", "side", "ladder_step", name="uq_intent_slot"),
        CheckConstraint("qty > 0", name="qty_positive"),
    )


class BrokerOrder(Base):
    __tablename__ = "broker_orders"
    perm_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    client_order_id: Mapped[str] = mapped_column(ForeignKey("order_intents.client_order_id"))
    status: Mapped[str] = mapped_column(String(32))
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime())
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class FillRow(Base):
    __tablename__ = "fills"
    exec_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    perm_id: Mapped[str] = mapped_column(ForeignKey("broker_orders.perm_id"))
    client_order_id: Mapped[str] = mapped_column(String(80))
    symbol: Mapped[str] = mapped_column(String(12))
    side: Mapped[Side] = mapped_column(_enum(Side, "side"))
    qty: Mapped[int] = mapped_column(BigInteger)
    price: Mapped[Decimal] = mapped_column(PriceType())
    venue: Mapped[str] = mapped_column(String(16))
    commission: Mapped[Decimal] = mapped_column(MoneyType())
    gst: Mapped[Decimal] = mapped_column(MoneyType())
    executed_at: Mapped[datetime] = mapped_column(UTCDateTime())
    settle_date: Mapped[date] = mapped_column(Date)
    __table_args__ = (CheckConstraint("qty > 0", name="qty_positive"),)


# ---------------------------------------------------------------------------
# Tax parcels, disposals, dividends, cash
# ---------------------------------------------------------------------------


class Parcel(Base):
    __tablename__ = "parcels"
    parcel_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(12))
    acquired_at: Mapped[datetime] = mapped_column(UTCDateTime())
    qty_original: Mapped[int] = mapped_column(BigInteger)
    qty_open: Mapped[int] = mapped_column(BigInteger)
    cost_base: Mapped[Decimal] = mapped_column(MoneyType())  # incl. brokerage
    source: Mapped[ParcelSource] = mapped_column(_enum(ParcelSource, "parcel_source"))
    __table_args__ = (
        CheckConstraint("qty_open >= 0 AND qty_open <= qty_original", name="qty_open_range"),
    )


class Disposal(Base):
    __tablename__ = "disposals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.parcel_id"))
    exec_id: Mapped[str] = mapped_column(ForeignKey("fills.exec_id"))
    qty: Mapped[int] = mapped_column(BigInteger)
    proceeds: Mapped[Decimal] = mapped_column(MoneyType())
    cost_base: Mapped[Decimal] = mapped_column(MoneyType())
    gain: Mapped[Decimal] = mapped_column(MoneyType())
    held_days: Mapped[int] = mapped_column(Integer)
    tax_regime: Mapped[str] = mapped_column(String(32))


class Dividend(Base):
    __tablename__ = "dividends"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(12))
    ex_date: Mapped[date] = mapped_column(Date)
    pay_date: Mapped[date] = mapped_column(Date)
    shares: Mapped[int] = mapped_column(BigInteger)
    cash_aud: Mapped[Decimal] = mapped_column(MoneyType())
    franking_credit_aud: Mapped[Decimal] = mapped_column(MoneyType())
    withholding: Mapped[Decimal] = mapped_column(MoneyType())
    source: Mapped[str] = mapped_column(String(32))


class CashLedger(Base):
    __tablename__ = "cash_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True)  # IBKR txn id
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    type: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(MoneyType())
    settle_date: Mapped[date] = mapped_column(Date)
    ref: Mapped[str | None] = mapped_column(Text)


class PositionEod(Base):
    __tablename__ = "positions_eod"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    qty: Mapped[int] = mapped_column(BigInteger)
    close: Mapped[Decimal] = mapped_column(PriceType())
    value: Mapped[Decimal] = mapped_column(MoneyType())


class NavEod(Base):
    __tablename__ = "nav_eod"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    nav: Mapped[Decimal] = mapped_column(MoneyType())
    cash_total: Mapped[Decimal] = mapped_column(MoneyType())
    cash_settled: Mapped[Decimal] = mapped_column(MoneyType())
    net_flow: Mapped[Decimal] = mapped_column(MoneyType())
    units: Mapped[Decimal] = mapped_column(Numeric(24, 10, asdecimal=True))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(24, 10, asdecimal=True))
    peak_unit_price: Mapped[Decimal] = mapped_column(Numeric(24, 10, asdecimal=True))
    drawdown: Mapped[Decimal] = mapped_column(Numeric(20, 10, asdecimal=True))


class Recon(Base):
    __tablename__ = "recon"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    check: Mapped[str] = mapped_column(String(16), primary_key=True)
    item: Mapped[str] = mapped_column(String(64), primary_key=True)
    ledger_value: Mapped[str | None] = mapped_column(Text)
    broker_value: Mapped[str | None] = mapped_column(Text)
    ok: Mapped[bool] = mapped_column(Boolean)
    checked_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


# ---------------------------------------------------------------------------
# Users' controls, alerts
# ---------------------------------------------------------------------------


class Veto(Base):
    __tablename__ = "vetoes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_date: Mapped[date] = mapped_column(Date)
    symbol: Mapped[str] = mapped_column(String(12))  # or 'ALL'
    side: Mapped[Side] = mapped_column(_enum(Side, "side"))
    received_at: Mapped[datetime] = mapped_column(UTCDateTime())
    channel: Mapped[str] = mapped_column(String(16))
    actor: Mapped[str] = mapped_column(String(64))


class Flag(Base):
    """kill, halt, fallback, dip_sleeve, soft_drawdown - with actor and reason.
    All columns are mutable (§12 ``flags.*``); every change is audited."""

    __tablename__ = "flags"
    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[bool] = mapped_column(Boolean)
    actor: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    level: Mapped[str] = mapped_column(String(16))
    type: Mapped[str] = mapped_column(String(64))
    reason_code: Mapped[ReasonCode | None] = mapped_column(_enum(ReasonCode, "reason_code"))
    msg: Mapped[str] = mapped_column(Text)
    channel: Mapped[str | None] = mapped_column(String(16))


# ---------------------------------------------------------------------------
# Research, config, valuations, audit
# ---------------------------------------------------------------------------


class ClassifierOutput(Base):
    __tablename__ = "classifier_outputs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(12))
    received_at: Mapped[datetime] = mapped_column(UTCDateTime())
    model_id: Mapped[str] = mapped_column(String(128))
    prompt_hash: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[str] = mapped_column(String(64))
    score: Mapped[float] = mapped_column(Float)
    tags: Mapped[list[str]] = mapped_column(JSONType)


class Trial(Base):
    __tablename__ = "trials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_hash: Mapped[str] = mapped_column(String(64))
    period: Mapped[str] = mapped_column(String(32))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class ConfigVersion(Base):
    __tablename__ = "config_versions"
    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[str] = mapped_column(String(64))
    approved_at: Mapped[datetime] = mapped_column(UTCDateTime())


class Valuation2027(Base):
    __tablename__ = "valuations_2027"
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.parcel_id"), primary_key=True)
    value_30jun2027: Mapped[Decimal] = mapped_column(MoneyType())


class AuditLog(Base):
    """Permanent, append-only. The app role has INSERT only (migration 0002)."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True,
                                    autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType)
    # The app role cannot SELECT audit_log, so never use RETURNING on insert.
    __table_args__ = {"implicit_returning": False}  # noqa: RUF012


# ---------------------------------------------------------------------------
# Mutability rules
# ---------------------------------------------------------------------------

ALL_COLUMNS: Final = "*"
MUTABLE_COLUMNS: Final[dict[str, frozenset[str]]] = {
    "runs": frozenset({"state"}),
    "order_intents": frozenset({"status"}),
    "broker_orders": frozenset({"status"}),
    "parcels": frozenset({"qty_open"}),
    "flags": frozenset({ALL_COLUMNS}),
}
INSERT_ONLY_TABLES: Final = frozenset(
    t for t in Base.metadata.tables if t not in MUTABLE_COLUMNS
)


class ImmutableRowError(Exception):
    """An insert-only row or column was updated or a row was deleted (§12)."""


def _mutable(table: str, column: str) -> bool:
    allowed = MUTABLE_COLUMNS.get(table, frozenset())
    return ALL_COLUMNS in allowed or column in allowed


def _check_flush(session: Session, _ctx: Any, _instances: Any) -> None:
    for obj in session.deleted:
        raise ImmutableRowError(f"deletes are not allowed (§12): {type(obj).__tablename__}")
    for obj in session.dirty:
        if not session.is_modified(obj, include_collections=False):
            continue
        table = type(obj).__tablename__
        for attr in obj.__mapper__.column_attrs:
            hist = get_history(obj, attr.key)
            if hist.has_changes() and not _mutable(table, attr.key):
                raise ImmutableRowError(f"{table}.{attr.key} is insert-only (§12)")


def install_mutability_guard(session_or_factory: Any) -> None:
    """Attach the §12 guard to a Session, sessionmaker or the Session class."""
    if not event.contains(session_or_factory, "before_flush", _check_flush):
        event.listen(session_or_factory, "before_flush", _check_flush)


def write_audit(session: Session, *, actor: str, action: str, payload: dict[str, Any]) -> None:
    """Append one audit row (Core INSERT without RETURNING; the app role cannot read it)."""
    from trader.jsonlog import scrub

    session.execute(
        insert(AuditLog).values(ts=utc_now(), actor=actor, action=action, payload=scrub(payload))
    )


def update_mutable(
    session: Session, obj: Base, column: str, value: Any, *, actor: str, reason: str
) -> None:
    """Update one allowed column and write the matching audit row (§12)."""
    table = type(obj).__tablename__
    if not _mutable(table, column):
        raise ImmutableRowError(f"{table}.{column} is insert-only (§12)")
    old = getattr(obj, column)
    setattr(obj, column, value)
    pk = {c.key: getattr(obj, c.key) for c in obj.__mapper__.primary_key}
    write_audit(
        session,
        actor=actor,
        action=f"update:{table}.{column}",
        payload={"pk": pk, "old": old, "new": value, "reason": reason},
    )
