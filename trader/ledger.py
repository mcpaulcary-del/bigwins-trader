"""Ledger database models (spec v2.10 §12): ``ledger_<user>_paper`` / ``ledger_<user>_live``.

Both ledger databases of a user have this schema. Market data lives in the
separate ``market_<user>`` database (``trader.data.models``). Schema changes are
Alembic migrations on the ``ledger`` branch, forward-only.

Mutability (§12): only ``runs.state``, ``order_intents.status``,
``broker_orders.status``, ``parcels.qty_open``, ``cashflow_expected.status``
and ``flags.*`` may be updated; every update writes an ``audit_log`` row
(``update_mutable``). Everything else is insert-only; nothing is deleted.
Enforced by the ORM guard (``install_mutability_guard``), Postgres column
grants (migration 0005) and, on ``audit_log``, an append-only trigger.
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
    ForeignKey,
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
    ImmutableRowError,
    JSONType,
    MoneyType,
    PriceType,
    RateType,
    SeriesType,
    UTCDateTime,
    install_mutability_guard,
    str_enum,
)
from trader.dbtypes import update_mutable as _update_mutable
from trader.dbtypes import write_audit as _write_audit
from trader.enums import (
    CashflowStatus,
    FillSource,
    ParcelSource,
    PlanKind,
    ReasonCode,
    RunState,
    Side,
)
from trader.timeutil import utc_now

__all__ = [
    "INSERT_ONLY_TABLES",
    "LEDGER_MUTABLE_COLUMNS",
    "ImmutableRowError",
    "LedgerBase",
    "install_mutability_guard",
    "update_mutable",
    "write_audit",
]


class LedgerBase(DeclarativeBase):
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


Base = LedgerBase  # short alias used by migrations/tests

_SYM = 12


class Run(LedgerBase):
    """One row per calendar trading day on which the jobs execute (§4)."""

    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True)
    state: Mapped[RunState] = mapped_column(str_enum(RunState, "run_state"))
    reason_code: Mapped[ReasonCode | None] = mapped_column(str_enum(ReasonCode, "reason_code"))
    config_hash: Mapped[str] = mapped_column(String(64))  # OPS-10
    git_sha: Mapped[str] = mapped_column(String(40))
    spec_hash: Mapped[str] = mapped_column(String(64))
    card_set_hash: Mapped[str | None] = mapped_column(String(64))
    data_hashes: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)  # DAT-09
    digest_sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class TrancheState(LedgerBase):
    """Versioned by evaluation date and revision, insert-only (SYS-17)."""

    __tablename__ = "tranche_state"
    tranche: Mapped[int] = mapped_column(Integer, primary_key=True)
    sleeve: Mapped[str] = mapped_column(String(_SYM), primary_key=True)
    evaluation_date: Mapped[date] = mapped_column(Date, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    on: Mapped[bool] = mapped_column(Boolean)
    votes: Mapped[int | None] = mapped_column(Integer)  # empty on a skipped month (OPS-13)
    verdict_level: Mapped[str] = mapped_column(String(16))
    drill: Mapped[bool] = mapped_column(Boolean, default=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    __table_args__ = (
        CheckConstraint("votes IS NULL OR (votes >= 0 AND votes <= 3)", name="votes_range"),
    )


class Plan(LedgerBase):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class PlanLine(LedgerBase):
    __tablename__ = "plan_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    symbol: Mapped[str] = mapped_column(String(_SYM))
    kind: Mapped[PlanKind] = mapped_column(str_enum(PlanKind, "plan_kind"))
    carried_from: Mapped[date | None] = mapped_column(Date)
    drill: Mapped[bool] = mapped_column(Boolean, default=False)
    target_weight: Mapped[Decimal] = mapped_column(RateType())
    target_qty: Mapped[int] = mapped_column(BigInteger)
    reasons: Mapped[list[str]] = mapped_column(JSONType)


class OrderIntent(LedgerBase):
    __tablename__ = "order_intents"
    client_order_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    symbol: Mapped[str] = mapped_column(String(_SYM))
    side: Mapped[Side] = mapped_column(str_enum(Side, "side"))
    qty: Mapped[int] = mapped_column(BigInteger)
    kind: Mapped[PlanKind] = mapped_column(str_enum(PlanKind, "plan_kind"))
    carried_from: Mapped[date | None] = mapped_column(Date)
    tranche_ids: Mapped[list[int]] = mapped_column(JSONType)
    ref_price: Mapped[Decimal] = mapped_column(PriceType())
    limit_price: Mapped[Decimal | None] = mapped_column(PriceType())
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32))
    reason_code: Mapped[ReasonCode | None] = mapped_column(str_enum(ReasonCode, "reason_code"))
    risk_decision: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    __table_args__ = (CheckConstraint("qty > 0", name="qty_positive"),)


class BrokerOrder(LedgerBase):
    __tablename__ = "broker_orders"
    perm_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    # None for a foreign order (BP-02)
    client_order_id: Mapped[str | None] = mapped_column(ForeignKey("order_intents.client_order_id"))
    broker_order_id: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class FillRow(LedgerBase):
    __tablename__ = "fills"
    exec_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    perm_id: Mapped[str | None] = mapped_column(ForeignKey("broker_orders.perm_id"))
    client_order_id: Mapped[str | None] = mapped_column(String(80))
    symbol: Mapped[str] = mapped_column(String(_SYM))
    side: Mapped[Side] = mapped_column(str_enum(Side, "side"))
    qty: Mapped[int] = mapped_column(BigInteger)
    price: Mapped[Decimal] = mapped_column(PriceType())
    commission: Mapped[Decimal] = mapped_column(MoneyType())
    gst: Mapped[Decimal | None] = mapped_column(MoneyType())  # from Flex; null until then
    executed_at: Mapped[datetime] = mapped_column(UTCDateTime())
    settle_date: Mapped[date] = mapped_column(Date)
    source: Mapped[FillSource] = mapped_column(str_enum(FillSource, "fill_source"))
    __table_args__ = (CheckConstraint("qty > 0", name="qty_positive"),)


class Parcel(LedgerBase):
    __tablename__ = "parcels"
    parcel_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(_SYM))
    acquired_at: Mapped[datetime] = mapped_column(UTCDateTime())
    qty_original: Mapped[int] = mapped_column(BigInteger)
    qty_open: Mapped[int] = mapped_column(BigInteger)
    cost_base: Mapped[Decimal] = mapped_column(MoneyType())  # incl. brokerage
    currency: Mapped[str] = mapped_column(String(3))
    aud_rate: Mapped[Decimal] = mapped_column(RateType())
    rate_source: Mapped[str] = mapped_column(String(64))
    managed: Mapped[bool] = mapped_column(Boolean)
    source: Mapped[ParcelSource] = mapped_column(str_enum(ParcelSource, "parcel_source"))
    __table_args__ = (
        CheckConstraint("qty_open >= 0 AND qty_open <= qty_original", name="qty_open_range"),
    )


class Disposal(LedgerBase):
    __tablename__ = "disposals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.parcel_id"))
    exec_id: Mapped[str | None] = mapped_column(ForeignKey("fills.exec_id"))
    qty: Mapped[int] = mapped_column(BigInteger)
    proceeds: Mapped[Decimal] = mapped_column(MoneyType())
    cost_base: Mapped[Decimal] = mapped_column(MoneyType())
    indexed_cost_base: Mapped[Decimal | None] = mapped_column(MoneyType())
    gain_pre_july_2027: Mapped[Decimal | None] = mapped_column(MoneyType())
    gain_post_july_2027: Mapped[Decimal | None] = mapped_column(MoneyType())
    discount_applied: Mapped[bool] = mapped_column(Boolean)
    held_days: Mapped[int] = mapped_column(Integer)
    tax_regime: Mapped[str] = mapped_column(String(32))


class Valuation2027(LedgerBase):
    __tablename__ = "valuations_2027"
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.parcel_id"), primary_key=True)
    close_30jun2027: Mapped[Decimal | None] = mapped_column(PriceType())
    eodhd_close: Mapped[Decimal | None] = mapped_column(PriceType())
    flex_mark: Mapped[Decimal | None] = mapped_column(PriceType())
    verdict: Mapped[str | None] = mapped_column(String(16))
    session_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(32))
    method: Mapped[str] = mapped_column(String(32))


class AmitAdjustment(LedgerBase):
    __tablename__ = "amit_adjustments"
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.parcel_id"), primary_key=True)
    income_year: Mapped[str] = mapped_column(String(7), primary_key=True)  # e.g. 2027-28
    cost_base_net_amount: Mapped[Decimal] = mapped_column(MoneyType())
    source_statement: Mapped[str] = mapped_column(Text)


class DistributionReceived(LedgerBase):
    __tablename__ = "distributions_received"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(_SYM))
    ex_date: Mapped[date] = mapped_column(Date)
    pay_date: Mapped[date] = mapped_column(Date)
    units: Mapped[int] = mapped_column(BigInteger)
    cash_aud: Mapped[Decimal] = mapped_column(MoneyType())
    franking_credit_aud: Mapped[Decimal] = mapped_column(MoneyType())
    components: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    withholding: Mapped[Decimal] = mapped_column(MoneyType())
    status: Mapped[str] = mapped_column(String(16))
    holding_period_ok: Mapped[bool | None] = mapped_column(Boolean)


class FrankingLedger(LedgerBase):
    __tablename__ = "franking_ledger"
    income_year: Mapped[str] = mapped_column(String(7), primary_key=True)
    distribution_id: Mapped[int] = mapped_column(
        ForeignKey("distributions_received.id"), primary_key=True
    )
    credit: Mapped[Decimal] = mapped_column(MoneyType())
    running_total: Mapped[Decimal] = mapped_column(MoneyType())
    exemption_status: Mapped[str] = mapped_column(String(32))


class CapitalLosses(LedgerBase):
    __tablename__ = "capital_losses"
    income_year: Mapped[str] = mapped_column(String(7), primary_key=True)
    opening_balance: Mapped[Decimal] = mapped_column(MoneyType())
    losses_in_year: Mapped[Decimal] = mapped_column(MoneyType())
    applied_in_year: Mapped[Decimal] = mapped_column(MoneyType())
    closing_balance: Mapped[Decimal] = mapped_column(MoneyType())
    source: Mapped[str] = mapped_column(String(64))


class CashLedger(LedgerBase):
    __tablename__ = "cash_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True)  # IBKR txn id
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    type: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(MoneyType())
    currency: Mapped[str] = mapped_column(String(3))
    settle_date: Mapped[date] = mapped_column(Date)
    ref: Mapped[str | None] = mapped_column(Text)


class PositionEod(LedgerBase):
    __tablename__ = "positions_eod"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(_SYM), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    qty: Mapped[int] = mapped_column(BigInteger)
    unmanaged_qty: Mapped[int] = mapped_column(BigInteger)
    close: Mapped[Decimal] = mapped_column(PriceType())
    value: Mapped[Decimal] = mapped_column(MoneyType())
    stale_price: Mapped[bool] = mapped_column(Boolean)


class NavEod(LedgerBase):
    __tablename__ = "nav_eod"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    nav: Mapped[Decimal] = mapped_column(MoneyType())
    unmanaged_value: Mapped[Decimal] = mapped_column(MoneyType())
    cash_total: Mapped[Decimal] = mapped_column(MoneyType())
    cash_settled: Mapped[Decimal] = mapped_column(MoneyType())
    distributions_receivable: Mapped[Decimal] = mapped_column(MoneyType())
    pending_surplus: Mapped[Decimal] = mapped_column(MoneyType())
    net_flow: Mapped[Decimal] = mapped_column(MoneyType())
    committed_capital: Mapped[Decimal] = mapped_column(MoneyType())
    sizing_nav: Mapped[Decimal] = mapped_column(MoneyType())
    units: Mapped[Decimal] = mapped_column(SeriesType())
    unit_price: Mapped[Decimal] = mapped_column(SeriesType())
    peak_unit_price: Mapped[Decimal] = mapped_column(SeriesType())
    drawdown: Mapped[Decimal] = mapped_column(SeriesType())


class BenchmarkNav(LedgerBase):
    __tablename__ = "benchmark_nav"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    benchmark: Mapped[str] = mapped_column(String(8), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    nav: Mapped[Decimal] = mapped_column(MoneyType())
    units: Mapped[Decimal] = mapped_column(SeriesType())
    unit_price: Mapped[Decimal] = mapped_column(SeriesType())
    drawdown: Mapped[Decimal] = mapped_column(SeriesType())


class KillCriterion(LedgerBase):
    __tablename__ = "kill_criteria"
    month: Mapped[str] = mapped_column(String(7), primary_key=True)  # YYYY-MM
    criterion: Mapped[str] = mapped_column(String(32), primary_key=True)
    value: Mapped[Decimal] = mapped_column(SeriesType())
    threshold: Mapped[Decimal] = mapped_column(SeriesType())
    tripped: Mapped[bool] = mapped_column(Boolean)
    owner_note: Mapped[str | None] = mapped_column(Text)


class Recon(LedgerBase):
    __tablename__ = "recon"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    check: Mapped[str] = mapped_column(String(16), primary_key=True)
    item: Mapped[str] = mapped_column(String(64), primary_key=True)
    ledger_value: Mapped[str | None] = mapped_column(Text)
    broker_value: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(8))  # flex or api
    ok: Mapped[bool] = mapped_column(Boolean)
    checked_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Veto(LedgerBase):
    __tablename__ = "vetoes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_date: Mapped[date] = mapped_column(Date)
    symbol: Mapped[str] = mapped_column(String(_SYM))  # or 'ALL'
    side: Mapped[Side] = mapped_column(str_enum(Side, "side"))
    received_at: Mapped[datetime] = mapped_column(UTCDateTime())  # Telegram stamp (OPS-04)
    channel: Mapped[str] = mapped_column(String(16))
    actor: Mapped[str] = mapped_column(String(64))


class Flag(LedgerBase):
    """killed, halt_integrity, halt_buys, mode, symbol freezes, account id, canary and
    go-live per account id (§12) - with actor and reason. All columns mutable."""

    __tablename__ = "flags"
    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Alert(LedgerBase):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    level: Mapped[str] = mapped_column(String(16))
    type: Mapped[str] = mapped_column(String(64))
    reason_code: Mapped[ReasonCode | None] = mapped_column(str_enum(ReasonCode, "reason_code"))
    msg: Mapped[str] = mapped_column(Text)
    channel: Mapped[str | None] = mapped_column(String(16))


class Override(LedgerBase):
    """Override history; the count feeds RSK-33."""

    __tablename__ = "overrides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    kind: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str | None] = mapped_column(String(_SYM))
    actor: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)


class CashflowExpected(LedgerBase):
    __tablename__ = "cashflow_expected"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    announced_at: Mapped[datetime] = mapped_column(UTCDateTime())
    amount: Mapped[Decimal] = mapped_column(MoneyType())  # deposit +, withdrawal -
    status: Mapped[CashflowStatus] = mapped_column(str_enum(CashflowStatus, "cashflow_status"))
    note: Mapped[str | None] = mapped_column(Text)


class Acceptance(LedgerBase):
    """USR-07 expectations acceptance and the dated "Before G4" records (OPS-06)."""

    __tablename__ = "acceptances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    check: Mapped[str] = mapped_column(String(32))
    account_id: Mapped[str | None] = mapped_column(String(16))
    recorded_by: Mapped[str] = mapped_column(String(16))  # system or user
    note: Mapped[str] = mapped_column(Text)


class ConfigVersion(LedgerBase):
    __tablename__ = "config_versions"
    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    approved_by: Mapped[str] = mapped_column(String(64))
    approved_at: Mapped[datetime] = mapped_column(UTCDateTime())


class AuditLog(LedgerBase):
    """Permanent, append-only. The app role has INSERT only."""

    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    ts: Mapped[datetime] = mapped_column(UTCDateTime())
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType)
    __table_args__ = {"implicit_returning": False}  # noqa: RUF012


LEDGER_TABLES: Final = frozenset(LedgerBase.metadata.tables)
LEDGER_MUTABLE_COLUMNS: Final = {t: c for t, c in MUTABLE_COLUMNS.items() if t in LEDGER_TABLES}
INSERT_ONLY_TABLES: Final = frozenset(t for t in LEDGER_TABLES if t not in LEDGER_MUTABLE_COLUMNS)
MUTABLE_COLUMNS_LEDGER = LEDGER_MUTABLE_COLUMNS  # backward-compatible name


def write_audit(session: Session, *, actor: str, action: str, payload: dict[str, Any]) -> None:
    """Append one row to the ledger ``audit_log``."""
    _write_audit(session, LedgerBase, actor=actor, action=action, payload=payload)


def update_mutable(
    session: Session, obj: LedgerBase, column: str, value: Any, *, actor: str, reason: str
) -> None:
    """Update one allowed ledger column and write the matching audit row (§12)."""
    _update_mutable(session, obj, column, value, actor=actor, reason=reason)
