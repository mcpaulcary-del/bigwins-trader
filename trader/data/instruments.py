"""Instrument reference data (SYS-20, SYS-29, SYS-32).

* SYS-20: a contract is resolved once with ``qualifyContracts``; its ``conId``
  is stored in ``instrument`` and used for every order. ``ensure_instrument``
  calls the qualifier only for an instrument that has no ``con_id`` yet.
* SYS-29: tick sizes come from IBKR contract data (the market-rule price
  increments stored with the instrument), never from a hard-coded table.
* SYS-32: a closed or delisted ETF stays in ``instrument`` with its delist date,
  reason and final payout (a new version; rows are insert-only).

The broker side (``ib_async``) is M4; here the qualifier is a protocol, so no
network is touched.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from trader.data.models import Instrument, write_market_audit
from trader.timeutil import ensure_utc


class InstrumentError(LookupError):
    pass


@dataclass(frozen=True)
class QualifiedContract:
    """What ``qualifyContracts`` + ``reqMarketRule`` give for one contract."""

    con_id: int
    exchange: str
    currency: str
    tick_rules: tuple[tuple[Decimal, Decimal], ...]  # (low_edge, increment), ascending


class ContractQualifier(Protocol):
    def qualify(self, symbol: str, exchange: str, currency: str) -> QualifiedContract: ...


def current_instrument(session: Session, symbol: str) -> Instrument | None:
    """Latest version of the instrument whose current symbol is ``symbol``."""
    rows = session.execute(
        select(Instrument).order_by(Instrument.id, Instrument.version.desc())
    ).scalars()
    seen: set[int] = set()
    for row in rows:
        if row.id in seen:
            continue
        seen.add(row.id)
        if row.symbol == symbol:
            return row
    return None


def instrument_by_id(session: Session, instrument_id: int) -> Instrument:
    row = session.execute(
        select(Instrument)
        .where(Instrument.id == instrument_id)
        .order_by(Instrument.version.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None:
        raise InstrumentError(f"no instrument id {instrument_id}")
    return row


def require_instrument(session: Session, symbol: str) -> Instrument:
    inst = current_instrument(session, symbol)
    if inst is None:
        raise InstrumentError(f"instrument {symbol} is not registered")
    return inst


def _new_version(
    session: Session, base: Instrument, now: datetime, **changes: object
) -> Instrument:
    fields = {
        c.key: getattr(base, c.key)
        for c in Instrument.__mapper__.column_attrs
        if c.key not in {"version", "fetch_time"}
    }
    fields.update(changes)
    row = Instrument(version=base.version + 1, fetch_time=ensure_utc(now), **fields)
    session.add(row)
    return row


def ensure_instrument(
    session: Session,
    symbol: str,
    qualifier: ContractQualifier,
    now: datetime,
    *,
    exchange: str = "ASX",
    currency: str = "AUD",
    issuer: str | None = None,
    list_date: date | None = None,
) -> Instrument:
    """Register ``symbol`` once, resolving its contract with ``qualifyContracts`` (SYS-20)."""
    inst = current_instrument(session, symbol)
    if inst is not None and inst.con_id is not None:
        return inst  # resolved once; never re-resolved
    q = qualifier.qualify(symbol, exchange, currency)
    rules = [[str(lo), str(inc)] for lo, inc in sorted(q.tick_rules)]
    if inst is None:
        next_id = (session.execute(select(func.max(Instrument.id))).scalar_one_or_none() or 0) + 1
        inst = Instrument(
            id=next_id,
            version=1,
            symbol=symbol,
            symbol_history=[symbol],
            exchange=q.exchange,
            currency=q.currency,
            issuer=issuer,
            con_id=q.con_id,
            tick_rules=rules,
            list_date=list_date,
            source="ibkr qualifyContracts",
            fetch_time=ensure_utc(now),
        )
        session.add(inst)
    else:
        inst = _new_version(
            session, inst, now, con_id=q.con_id, tick_rules=rules, source="ibkr qualifyContracts"
        )
    session.flush()
    write_market_audit(
        session,
        actor="system",
        action="instrument.qualify",
        payload={"symbol": symbol, "con_id": q.con_id, "tick_rules": rules},
    )
    return inst


def register_unqualified(
    session: Session, symbol: str, now: datetime, *, exchange: str = "ASX", currency: str = "AUD"
) -> Instrument:
    """Register a data-only instrument (benchmark, index proxy) with no contract yet.

    Such an instrument can be fetched and validated but never ordered: orders
    need a ``con_id`` (SYS-20).
    """
    inst = current_instrument(session, symbol)
    if inst is not None:
        return inst
    next_id = (session.execute(select(func.max(Instrument.id))).scalar_one_or_none() or 0) + 1
    inst = Instrument(
        id=next_id,
        version=1,
        symbol=symbol,
        symbol_history=[symbol],
        exchange=exchange,
        currency=currency,
        source="data-only registration",
        fetch_time=ensure_utc(now),
    )
    session.add(inst)
    session.flush()
    return inst


def order_con_id(inst: Instrument) -> int:
    """The conId every order uses (SYS-20); refuses an unqualified instrument."""
    if inst.con_id is None:
        raise InstrumentError(f"{inst.symbol} has no conId: qualify it before any order (SYS-20)")
    return inst.con_id


def tick_size(inst: Instrument, price: Decimal) -> Decimal | None:
    """Price increment at ``price`` from the stored IBKR market rule (SYS-29).

    Returns ``None`` when no contract data is stored; callers must then use the
    stricter rule that does not rely on a tick (for example DAT-02 uses the
    percentage tolerance only).
    """
    if not inst.tick_rules:
        return None
    inc: Decimal | None = None
    for lo, step in sorted((Decimal(a), Decimal(b)) for a, b in inst.tick_rules):
        if price >= lo:
            inc = step
    return inc


def record_delisting(
    session: Session,
    symbol: str,
    delist_date: date,
    reason: str,
    final_payout: Decimal,
    now: datetime,
) -> Instrument:
    """SYS-32: keep the instrument with its delist date, reason and final payout."""
    if not isinstance(final_payout, Decimal) or final_payout < 0:
        raise ValueError("final_payout must be a non-negative Decimal per unit")
    inst = require_instrument(session, symbol)
    row = _new_version(
        session,
        inst,
        now,
        delist_date=delist_date,
        delist_reason=reason,
        final_payout=final_payout,
        source="delisting",
    )
    session.flush()
    write_market_audit(
        session,
        actor="user",
        action="instrument.delist",
        payload={"symbol": symbol, "delist_date": delist_date, "reason": reason,
                 "final_payout": final_payout},
    )  # fmt: skip
    return row
