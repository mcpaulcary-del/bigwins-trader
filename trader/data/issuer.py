"""Issuer distribution entry and the missing-distribution rules (DAT-14, DAT-22).

Distribution amounts used for ``tr_net`` and tax come from issuer announcements,
entered by hand (``trader distribution enter``); the vendor's figures are only a
cross-check. Rows are insert-only and bitemporal: a later entry for the same
(instrument, ex-date) supersedes an earlier one (for example an ``estimated``
June distribution followed by the ``final`` figure). Each quarter the user also
enters the next expected ex-date of every live ETF as an ``expected`` row with
no amount, so the DAT-22 block does not depend on the vendor.

For ex-dates before ``trader init``, rows may be loaded from the vendor's
dividend history with source ``vendor_backfill`` and status ``final`` (DAT-14).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.data.instruments import require_instrument
from trader.data.models import Distribution, VendorDividend, write_market_audit
from trader.data.store import latest_bars
from trader.enums import DistributionSource, DistributionStatus, ReasonCode
from trader.timeutil import ensure_utc


class DistributionError(ValueError):
    pass


def enter_distribution(
    session: Session,
    symbol: str,
    ex_date: date,
    status: DistributionStatus,
    now: datetime,
    *,
    amount: Decimal | None = None,
    franking: Decimal | None = None,
    record_date: date | None = None,
    pay_date: date | None = None,
    period_end: date | None = None,
    components: Mapping[str, Any] | None = None,
    note: str = "",
    actor: str = "user",
    source: DistributionSource = DistributionSource.ISSUER,
) -> Distribution:
    """Insert one distribution row (DAT-14). Validates before writing."""
    inst = require_instrument(session, symbol)
    if status is DistributionStatus.EXPECTED:
        if amount is not None or franking is not None:
            raise DistributionError("an expected row has no amount (DAT-22)")
    else:
        if amount is None or not isinstance(amount, Decimal) or amount < 0:
            raise DistributionError("estimated and final rows need a non-negative Decimal amount")
        if franking is not None and (not isinstance(franking, Decimal) or franking < 0):
            raise DistributionError("franking credit must be a non-negative Decimal")
        if period_end is None and source is DistributionSource.ISSUER:
            raise DistributionError("an issuer amount needs its period_end (TAX-08)")
    if record_date is not None and record_date < ex_date:
        raise DistributionError("record date before ex-date")
    if pay_date is not None and pay_date < (record_date or ex_date):
        raise DistributionError("pay date before record/ex date")
    row = Distribution(
        instrument_id=inst.id,
        ex_date=ex_date,
        record_date=record_date,
        pay_date=pay_date,
        period_end=period_end,
        cash_amount=amount,
        franking_credit=franking,
        components=dict(components or {}),
        status=status,
        source=source,
        fetch_time=ensure_utc(now),
    )
    session.add(row)
    session.flush()
    write_market_audit(
        session,
        actor=actor,
        action="distribution.enter",
        payload={"symbol": symbol, "ex_date": ex_date, "status": status, "amount": amount,
                 "franking": franking, "source": source, "note": note},
    )  # fmt: skip
    return row


def effective_distributions(
    session: Session, instrument_id: int, as_of: datetime | None = None
) -> dict[date, Distribution]:
    """Latest-entered row per ex-date (bitemporal)."""
    q = select(Distribution).where(Distribution.instrument_id == instrument_id)
    if as_of is not None:
        q = q.where(Distribution.fetch_time <= ensure_utc(as_of))
    out: dict[date, Distribution] = {}
    for row in session.execute(
        q.order_by(Distribution.ex_date, Distribution.fetch_time, Distribution.id)
    ).scalars():
        out[row.ex_date] = row
    return out


def vendor_dividends(
    session: Session, instrument_id: int, as_of: datetime | None = None
) -> dict[date, VendorDividend]:
    q = select(VendorDividend).where(VendorDividend.instrument_id == instrument_id)
    if as_of is not None:
        q = q.where(VendorDividend.fetch_time <= ensure_utc(as_of))
    out: dict[date, VendorDividend] = {}
    for row in session.execute(
        q.order_by(VendorDividend.ex_date, VendorDividend.fetch_time)
    ).scalars():
        out[row.ex_date] = row
    return out


def load_vendor_backfill(
    session: Session, symbol: str, init_date: date, now: datetime
) -> list[Distribution]:
    """DAT-14: rows for ex-dates before ``trader init`` from the vendor's dividend history
    (source ``vendor_backfill``, status ``final``). Ex-dates that already have a row
    are left alone. The user then checks the latest eight per ETF (open item E2)."""
    inst = require_instrument(session, symbol)
    have = effective_distributions(session, inst.id)
    out: list[Distribution] = []
    for ex, vd in sorted(vendor_dividends(session, inst.id).items()):
        if ex >= init_date or ex in have:
            continue
        out.append(
            enter_distribution(
                session, symbol, ex, DistributionStatus.FINAL, now,
                amount=vd.unadjusted_value if vd.unadjusted_value is not None else vd.value,
                record_date=vd.record_date, pay_date=vd.payment_date,
                note=f"vendor backfill, file {vd.file_hash[:12]}", actor="system",
                source=DistributionSource.VENDOR_BACKFILL,
            )
        )  # fmt: skip
    return out


# ---------------------------------------------------------------------------
# DAT-22
# ---------------------------------------------------------------------------


def ratio_change_dates(session: Session, instrument_id: int, end: date) -> list[date]:
    """Dates on which the vendor's adjusted/raw ratio changed (a distribution or split)."""
    bars = latest_bars(session, instrument_id, "eodhd", end=end)
    out: list[date] = []
    prev: Decimal | None = None
    for d in sorted(bars):
        b = bars[d]
        if b.vendor_adjusted_close is None or b.close == 0:
            continue
        r = b.vendor_adjusted_close / b.close
        if prev is not None and abs(r / prev - 1) > Decimal("1e-6"):
            out.append(d)
        prev = r
    return out


@dataclass(frozen=True)
class DistBlock:
    """Why a sleeve's evaluation is blocked and its buys are held (DIST_MISSING)."""

    ex_date: date
    cause: str  # 'expected_no_amount', 'vendor_dividend' or 'ratio_change'
    reason: ReasonCode = ReasonCode.DIST_MISSING


def missing_distributions(
    session: Session,
    instrument_id: int,
    on_or_before: date,
    *,
    split_dates: set[date] | None = None,
    as_of: datetime | None = None,
) -> list[DistBlock]:
    """DAT-22 blocks that apply to an evaluation dated ``on_or_before``.

    * an ``expected`` row (no amount) with ex-date <= D;
    * a vendor-reported dividend, or a change of the adjusted/raw ratio that is
      not a recorded split, on a date with no ``distribution`` row.
    """
    dists = effective_distributions(session, instrument_id, as_of)
    out: list[DistBlock] = []
    for ex, row in dists.items():
        if ex <= on_or_before and row.cash_amount is None:
            out.append(DistBlock(ex, "expected_no_amount"))
    for ex in vendor_dividends(session, instrument_id, as_of):
        if ex <= on_or_before and ex not in dists:
            out.append(DistBlock(ex, "vendor_dividend"))
    splits = split_dates or set()
    for d in ratio_change_dates(session, instrument_id, on_or_before):
        if d not in dists and d not in splits and not any(b.ex_date == d for b in out):
            out.append(DistBlock(d, "ratio_change"))
    return sorted(out, key=lambda b: b.ex_date)


def first_missing_amount(
    session: Session, instrument_id: int, as_of: datetime | None = None
) -> date | None:
    """Earliest ex-date whose row has no amount: ``tr_net`` is not built from it."""
    missing = [
        ex for ex, r in effective_distributions(session, instrument_id, as_of).items()
        if r.cash_amount is None
    ]  # fmt: skip
    return min(missing) if missing else None


def no_future_expected_warning(session: Session, symbol: str, today: date) -> str | None:
    """DAT-22: WARN when a live ETF has no distribution row with a future ex-date."""
    inst = require_instrument(session, symbol)
    if any(ex > today for ex in effective_distributions(session, inst.id)):
        return None
    return (
        f"WARN DIST_MISSING: {symbol} has no future expected ex-date; enter the next one "
        "(trader distribution enter --status expected)"
    )


def benchmark_dividend_warnings(session: Session, symbol: str) -> list[date]:
    """DAT-14: vendor-reported benchmark (DHHF) dividends with no row. Each is a WARN and
    marks B1 provisional; it never blocks a sleeve."""
    inst = require_instrument(session, symbol)
    have = effective_distributions(session, inst.id)
    return sorted(ex for ex in vendor_dividends(session, inst.id) if ex not in have)


def vendor_amount_mismatch(
    session: Session, instrument_id: int, tolerance: Decimal
) -> list[tuple[date, Decimal, Decimal]]:
    """Cross-check: issuer amounts vs vendor dividends (DAT-14). Returns mismatches."""
    out: list[tuple[date, Decimal, Decimal]] = []
    vend = vendor_dividends(session, instrument_id)
    for ex, row in effective_distributions(session, instrument_id).items():
        vd = vend.get(ex)
        if vd is None or row.cash_amount is None or row.source != DistributionSource.ISSUER:
            continue
        v = vd.unadjusted_value if vd.unadjusted_value is not None else vd.value
        if row.cash_amount and abs(v - row.cash_amount) / row.cash_amount > tolerance:
            out.append((ex, row.cash_amount, v))
    return out
