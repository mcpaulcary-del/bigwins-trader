"""Shared database column types and the §12 mutability guard.

Used by both databases of an instance (§12): ``market_<user>``
(``trader.data.models``) and ``ledger_<user>_paper`` / ``ledger_<user>_live``
(``trader.ledger``).

* Money is ``NUMERIC(18,4)`` mapped to ``Decimal``; floats are refused on bind
  (SYS-13).
* Timestamps are ``TIMESTAMP WITH TIME ZONE`` stored in UTC; naive datetimes are
  refused on bind (SYS-14). Date columns are ASX local dates.
* Only the columns in ``MUTABLE_COLUMNS`` may be updated, each update writes an
  ``audit_log`` row in the same database, and nothing is ever deleted (§12).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Final

from sqlalchemy import JSON, DateTime, Dialect, Numeric, event, insert
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.types import TypeDecorator

from trader.constants import MONEY_PRECISION, MONEY_SCALE, PRICE_PRECISION, PRICE_SCALE
from trader.money import MoneyTypeError
from trader.timeutil import ensure_utc, utc_now

NAMING_CONVENTION: Final = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


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
    """Unadjusted prices, same rules as money (NUMERIC(18,4))."""

    impl = Numeric(PRICE_PRECISION, PRICE_SCALE, asdecimal=True)
    cache_ok = True


class RateType(MoneyType):
    """Per-unit rates (distribution cents per unit, FX, ratios) as exact ``Decimal``.

    NUMERIC(24,10): issuer distribution amounts are quoted to more than 4
    decimal places of a dollar per unit (docs/DECISIONS.md L-09).
    """

    impl = Numeric(24, 10, asdecimal=True)
    cache_ok = True


class SeriesType(MoneyType):
    """Derived index values (tr_net, tr_gross, unit prices): NUMERIC(30,12)."""

    impl = Numeric(30, 12, asdecimal=True)
    cache_ok = True


JSONType = JSON().with_variant(JSONB(), "postgresql")


def str_enum(e: type[Any], name: str) -> SAEnum:
    """A string-backed enum column with a CHECK constraint (portable)."""
    return SAEnum(
        e,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda x: [m.value for m in x],
        validate_strings=True,
    )


# ---------------------------------------------------------------------------
# Mutability rules (§12)
# ---------------------------------------------------------------------------

ALL_COLUMNS: Final = "*"
MUTABLE_COLUMNS: Final[dict[str, frozenset[str]]] = {
    # ledger_<user>_{paper,live}
    "runs": frozenset({"state"}),
    "order_intents": frozenset({"status"}),
    "broker_orders": frozenset({"status"}),
    "parcels": frozenset({"qty_open"}),
    "cashflow_expected": frozenset({"status"}),
    "flags": frozenset({ALL_COLUMNS}),
    # market_<user>
    "distribution": frozenset({"status"}),
    "hypotheses": frozenset({"status", "result", "decision", "approver"}),
}


class ImmutableRowError(Exception):
    """An insert-only row or column was updated or a row was deleted (§12)."""


def is_mutable(table: str, column: str) -> bool:
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
            if hist.has_changes() and not is_mutable(table, attr.key):
                raise ImmutableRowError(f"{table}.{attr.key} is insert-only (§12)")


def install_mutability_guard(session_or_factory: Any) -> None:
    """Attach the §12 guard to a Session, sessionmaker or the Session class."""
    if not event.contains(session_or_factory, "before_flush", _check_flush):
        event.listen(session_or_factory, "before_flush", _check_flush)


def write_audit(
    session: Session,
    base: type[DeclarativeBase],
    *,
    actor: str,
    action: str,
    payload: dict[str, Any],
) -> None:
    """Append one audit row to ``audit_log`` of ``base``'s database.

    Core INSERT without RETURNING: the app role cannot read ``audit_log``.
    """
    from trader.jsonlog import scrub

    table = base.metadata.tables["audit_log"]
    session.execute(
        insert(table).values(ts=utc_now(), actor=actor, action=action, payload=scrub(payload))
    )


def update_mutable(
    session: Session, obj: DeclarativeBase, column: str, value: Any, *, actor: str, reason: str
) -> None:
    """Update one allowed column and write the matching audit row (§12)."""
    table = type(obj).__tablename__
    if not is_mutable(table, column):
        raise ImmutableRowError(f"{table}.{column} is insert-only (§12)")
    old = getattr(obj, column)
    setattr(obj, column, value)
    mapper = obj.__mapper__
    pk = {
        str(c.name): v
        for c, v in zip(mapper.primary_key, mapper.primary_key_from_instance(obj), strict=True)
    }
    base = next(b for b in type(obj).__mro__ if "registry" in b.__dict__)
    write_audit(
        session,
        base,
        actor=actor,
        action=f"update:{table}.{column}",
        payload={"pk": pk, "old": old, "new": value, "reason": reason},
    )
