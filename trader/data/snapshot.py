"""``MarketSnapshot`` and its builder (§3; SYS-12, DAT-05, DAT-21).

The snapshot is the only market input to ``decide()``. It refuses to exist with
a price dated after the evaluation date D, or with a symbol whose D close has no
validation verdict (SYS-12). The builder reads everything from the local store
(never from a vendor API, DAT-23 (3)) and waits for the verdict (DAT-21).

Field refinement (names may be refined, §3): ``dist_missing`` lists sleeves
whose evaluation is blocked by a missing distribution amount (DAT-22); it is
kept apart from ``blocked`` because their sells still proceed.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from trader.calendar import AsxCalendar
from trader.data.instruments import require_instrument
from trader.data.models import QcEvent
from trader.data.quality import latest_verdict
from trader.data.store import latest_bars, validated_closes
from trader.data.totalreturn import build_tr_series, monthly_series
from trader.enums import Verdict
from trader.timeutil import ensure_utc

_VERDICTS = frozenset(v.value for v in Verdict)


class SnapshotError(ValueError):
    """SYS-12: a price after D, or a symbol whose D close has no verdict."""


def _index_dates(s: pd.Series) -> list[date]:
    out: list[date] = []
    for k in s.index:
        if isinstance(k, pd.Timestamp | datetime):
            out.append(k.date())
        elif isinstance(k, date):
            out.append(k)
        else:
            raise SnapshotError(f"monthly_tr index must hold dates, got {type(k).__name__}")
    return out


@dataclass(frozen=True)
class MarketSnapshot:
    as_of: date  # evaluation date D
    verdict_at: datetime  # time the validation verdict was issued (UTC)
    monthly_tr: dict[
        str, pd.Series
    ]  # per symbol: tr_net at this tranche's evaluation dates, all <= D
    last_close: dict[str, Decimal]  # validated raw close at D
    verdict: dict[str, str]  # per symbol: 'OK', 'WARN', 'SINGLE_SOURCE' or 'BLOCK'
    adv20: dict[str, Decimal | None]  # 20-day average daily volume (units)
    blocked: frozenset[str]  # symbols with a BLOCK verdict or halted
    dist_missing: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        ensure_utc(self.verdict_at)
        for sym, v in self.verdict.items():
            if v not in _VERDICTS:
                raise SnapshotError(f"{sym}: unknown verdict {v!r}")
        symbols = set(self.monthly_tr) | set(self.last_close) | set(self.adv20)
        missing = sorted(symbols - set(self.verdict))
        if missing:
            raise SnapshotError(f"SYS-12: no validation verdict for the D close of {missing}")
        for sym, series in self.monthly_tr.items():
            late = [d for d in _index_dates(series) if d > self.as_of]
            if late:
                raise SnapshotError(f"SYS-12: {sym} has prices dated after D={self.as_of}: {late}")
        for sym, px in self.last_close.items():
            if not isinstance(px, Decimal):
                raise SnapshotError(f"{sym}: last_close must be Decimal (SYS-13)")
            if self.verdict[sym] == Verdict.BLOCK.value:
                raise SnapshotError(f"{sym}: a BLOCKed close is not a validated close")
        should_block = {s for s, v in self.verdict.items() if v == Verdict.BLOCK.value}
        if not should_block <= self.blocked:
            raise SnapshotError(f"BLOCK verdicts missing from blocked: {sorted(should_block)}")


def adv20(session: Session, instrument_id: int, day: date) -> Decimal | None:
    bars = latest_bars(session, instrument_id, "eodhd", day - timedelta(days=60), day)
    vols = [bars[d].volume for d in sorted(bars)][-20:]
    if len(vols) < 20 or any(v is None for v in vols):
        return None
    return Decimal(sum(v for v in vols if v is not None)) / 20


def build_snapshot(
    session: Session,
    symbols: Iterable[str],
    day: date,
    cal: AsxCalendar,
    tranche_offset: str | int,
    now: datetime,
    *,
    min_evaluation_closes: int,
    franking_realisable_rate: Decimal,
    halted: Iterable[str] = (),
) -> MarketSnapshot:
    """Build the snapshot for evaluation date D from the local store (DAT-21, DAT-23 (3)).

    Raises ``SnapshotError`` if any symbol's D close has no verdict yet: the 08:10
    decision waits for the 08:00 verdict (DAT-21). DAT-05: a symbol with fewer than
    ``min_evaluation_closes`` evaluation-date closes is BLOCKed for the evaluation.
    """
    verdicts: dict[str, str] = {}
    last_close: dict[str, Decimal] = {}
    monthly: dict[str, pd.Series] = {}
    advs: dict[str, Decimal | None] = {}
    blocked: set[str] = set(halted)
    dist_missing: set[str] = set()
    verdict_times: list[datetime] = []
    for sym in symbols:
        inst = require_instrument(session, sym)
        ev = latest_verdict(session, inst.id, day, as_of=now)
        if ev is None:
            raise SnapshotError(f"SYS-12/DAT-21: {sym} close for {day} has no verdict yet")
        level = ev.level if ev.check_id == "VERDICT" else Verdict.WARN.value  # DAT-17 override
        verdicts[sym] = level
        verdict_times.append(ev.ts)
        if level == Verdict.BLOCK.value:
            blocked.add(sym)
        if ev.detail.get("dist_missing"):
            dist_missing.add(sym)
        vc = validated_closes(session, inst.id, start=day, end=day, as_of=now).get(day)
        if vc is not None and level != Verdict.BLOCK.value:
            last_close[sym] = vc.close
        advs[sym] = adv20(session, inst.id, day)
        try:
            build = build_tr_series(session, sym, franking_realisable_rate, now, end=day)
        except ValueError:
            build = None
        points = [] if build is None else [p for p in build.points if p.date <= day]
        first = points[0].date if points else day
        eval_dates = cal.evaluation_dates(first, day, tranche_offset) if cal.covers(first) else []
        series = monthly_series(points, eval_dates)
        monthly[sym] = pd.Series(series, dtype=object)
        if len(series) < min_evaluation_closes:
            blocked.add(sym)
            session.add(
                QcEvent(
                    ts=ensure_utc(now), instrument_id=inst.id, trade_date=day, check_id="DAT-05",
                    level="BLOCK", detail={"evaluation_closes": len(series),
                                           "required": min_evaluation_closes},
                )
            )  # fmt: skip
    session.flush()
    return MarketSnapshot(
        as_of=day,
        verdict_at=max(verdict_times) if verdict_times else ensure_utc(now),
        monthly_tr=monthly,
        last_close=last_close,
        verdict=verdicts,
        adv20=advs,
        blocked=frozenset(blocked),
        dist_missing=frozenset(dist_missing),
    )
