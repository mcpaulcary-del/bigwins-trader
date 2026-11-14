"""Own total-return series ``tr_net`` and ``tr_gross`` (§6, DAT-11, DAT-22, SYS-32).

    TR_t = TR_{t-1} x (P_t x s_t + D_t) / P_{t-1}

P is the validated raw close, D_t the cash distribution per unit on its
ex-date, s_t the unit ratio of a split or consolidation effective on t (1
otherwise). ``tr_gross`` adds franking credit x ``tax.franking_realisable_rate``
to D_t. TR on the first date is 1. Signals use ``tr_net`` only; the vendor's
adjusted close is never used for signals.

* ``tr_net`` is never built across an ex-date with a missing amount (DAT-22): the
  series stops on the day before the first such ex-date.
* A delisted ETF's wind-up payout is its last return (SYS-32).
* Every build is stamped with a build id (a hash of its inputs) and the as-of
  time of its inputs (DAT-18); rebuilding from the same inputs gives the same id.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, localcontext

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.data.instruments import current_instrument, require_instrument
from trader.data.issuer import effective_distributions, missing_distributions
from trader.data.models import CorpAction, TrSeries
from trader.data.store import validated_closes
from trader.timeutil import ensure_utc

SERIES_QUANTUM = Decimal("0.000000000001")  # NUMERIC(30,12)


class TrBuildError(ValueError):
    pass


@dataclass(frozen=True)
class TrPoint:
    date: date
    tr_net: Decimal
    tr_gross: Decimal


@dataclass(frozen=True)
class Payout:
    """Final wind-up payout per unit on the delist date (SYS-32)."""

    date: date
    amount: Decimal


def compute_tr(
    closes: Mapping[date, Decimal],
    distributions: Mapping[date, tuple[Decimal, Decimal]],
    ratios: Mapping[date, Decimal],
    franking_realisable_rate: Decimal,
    *,
    stop_before: date | None = None,
    final_payout: Payout | None = None,
) -> list[TrPoint]:
    """Pure series construction from validated closes (exact Decimal arithmetic).

    ``distributions``: ex-date -> (cash per unit, franking credit per unit).
    ``stop_before``: the first ex-date with a missing amount (DAT-22).
    A distribution or split whose date has no close is applied on the next close.
    """
    days = sorted(d for d in closes if stop_before is None or d < stop_before)
    out: list[TrPoint] = []
    if not days:
        return out
    with localcontext() as ctx:
        ctx.prec = 34
        tr_n = tr_g = Decimal(1)
        out.append(TrPoint(days[0], tr_n, tr_g))
        prev = days[0]
        for d in days[1:]:
            p_prev, p = closes[prev], closes[d]
            if p_prev <= 0 or p <= 0:
                raise TrBuildError(f"non-positive close near {d}")
            cash = sum((v[0] for k, v in distributions.items() if prev < k <= d), Decimal(0))
            frank = sum((v[1] for k, v in distributions.items() if prev < k <= d), Decimal(0))
            s = Decimal(1)
            for k, r in ratios.items():
                if prev < k <= d:
                    s *= r
            tr_n = tr_n * (p * s + cash) / p_prev
            tr_g = tr_g * (p * s + cash + frank * franking_realisable_rate) / p_prev
            out.append(TrPoint(d, tr_n, tr_g))
            prev = d
        if (
            final_payout is not None
            and final_payout.date > prev
            and (stop_before is None or final_payout.date < stop_before)
        ):
            p_prev = closes[prev]
            tr_n = tr_n * final_payout.amount / p_prev
            tr_g = tr_g * final_payout.amount / p_prev
            out.append(TrPoint(final_payout.date, tr_n, tr_g))
    return [
        TrPoint(t.date, t.tr_net.quantize(SERIES_QUANTUM), t.tr_gross.quantize(SERIES_QUANTUM))
        for t in out
    ]


@dataclass(frozen=True)
class TrBuild:
    build_id: str
    instrument_id: int
    points: list[TrPoint]
    inputs_as_of: datetime
    stopped_before: date | None


def _build_id(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:32]


def split_ratios(session: Session, instrument_id: int) -> dict[date, Decimal]:
    rows = session.execute(
        select(CorpAction).where(
            CorpAction.instrument_id == instrument_id, CorpAction.ratio.is_not(None)
        )
    ).scalars()
    return {r.ex_date: r.ratio for r in rows if r.ratio is not None}


def build_tr_series(
    session: Session,
    symbol: str,
    franking_realisable_rate: Decimal,
    now: datetime,
    *,
    end: date | None = None,
    store: bool = True,
) -> TrBuild:
    """Build ``tr_net``/``tr_gross`` from the validated set and issuer distributions."""
    inst = require_instrument(session, symbol)
    closes_rows = validated_closes(session, inst.id, end=end, signals_only=True)
    if not closes_rows:
        raise TrBuildError(f"{symbol}: no validated closes")
    closes = {d: r.close for d, r in closes_rows.items()}
    ratios = split_ratios(session, inst.id)
    last = max(closes)
    blocks = missing_distributions(session, inst.id, date.max, split_dates=set(ratios))
    stop = blocks[0].ex_date if blocks else None
    dists = {
        ex: (row.cash_amount, row.franking_credit or Decimal(0))
        for ex, row in effective_distributions(session, inst.id).items()
        if row.cash_amount is not None
    }
    cur = current_instrument(session, symbol)
    payout = None
    if cur is not None and cur.delist_date is not None and cur.final_payout is not None:
        payout = Payout(cur.delist_date, cur.final_payout)
    points = compute_tr(
        closes, dists, ratios, franking_realisable_rate, stop_before=stop, final_payout=payout
    )
    inputs_as_of = max(r.validated_at for r in closes_rows.values())
    bid = _build_id(
        {
            "instrument": inst.id,
            "closes": sorted((d.isoformat(), str(v)) for d, v in closes.items()),
            "dists": sorted((d.isoformat(), str(a), str(f)) for d, (a, f) in dists.items()),
            "ratios": sorted((d.isoformat(), str(r)) for d, r in ratios.items()),
            "stop": stop,
            "payout": payout,
            "franking_rate": str(franking_realisable_rate),
            "last": last,
        }
    )
    build = TrBuild(bid, inst.id, points, ensure_utc(inputs_as_of), stop)
    if store:
        exists = session.execute(
            select(TrSeries.build_id).where(TrSeries.build_id == bid).limit(1)
        ).scalar_one_or_none()
        if exists is None:
            for p in points:
                session.add(
                    TrSeries(
                        build_id=bid,
                        instrument_id=inst.id,
                        date=p.date,
                        tr_net=p.tr_net,
                        tr_gross=p.tr_gross,
                        inputs_as_of=build.inputs_as_of,
                    )
                )
            session.flush()
    return build


def monthly_series(points: list[TrPoint], evaluation_dates: list[date]) -> dict[date, Decimal]:
    """``tr_net`` at the tranche's evaluation dates (§9.1 notation); missing dates omitted."""
    by_date = {p.date: p.tr_net for p in points}
    return {d: by_date[d] for d in evaluation_dates if d in by_date}
