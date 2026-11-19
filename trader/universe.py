"""Liquidity ranks and bands (FD v3.0 §5.2, BW-UNI-10 to BW-UNI-12). Pure.

``tv_rank`` = rank of ``tv_med252`` (largest = 1, ties averaged) among the rank
population. The FD population is entities of class ``ORD``, ``REIT`` or ``LIC`` that
traded in the last 5 sessions (BW-UNI-11). Report 85's T6 ranked every entity of its
file with a ``tv_med252`` (``rank_scope="all"``); the golden test uses that scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from trader.features import BoolArray, avg_rank, traded_within, tv_median
from trader.panel import FloatArray, PricePanel

RankScope = Literal["fd", "all"]
RANKED_CLASSES = frozenset({"ORD", "REIT", "LIC"})
BANDS: tuple[tuple[str, int, int], ...] = (("A", 1, 100), ("B", 101, 300), ("C", 301, 600))


@dataclass(frozen=True, eq=False)
class LiquidityTable:
    tv_med252: FloatArray
    tv_med63: FloatArray
    tv_med20: FloatArray
    tv_rank: FloatArray  # NaN = not ranked
    traded5: BoolArray

    def band(self, j: int) -> str | None:
        rk = self.tv_rank[j]
        if np.isnan(rk):
            return None
        for name, lo, hi in BANDS:
            if lo <= rk <= hi:
                return name
        return "D"


def liquidity_table(
    panel: PricePanel,
    *,
    rank_scope: RankScope = "fd",
    zero_fill_listed: bool = True,
    med252_min_days: int = 120,
    med63_min_days: int = 30,
    traded_within_sessions: int = 5,
) -> LiquidityTable:
    m252 = tv_median(panel, 252, med252_min_days, zero_fill_listed=zero_fill_listed)
    m63 = tv_median(panel, 63, med63_min_days, zero_fill_listed=zero_fill_listed)
    m20 = tv_median(panel, 20, 10, zero_fill_listed=zero_fill_listed)
    t5 = traded_within(panel, traded_within_sessions)
    pop = ~np.isnan(m252)
    if rank_scope == "fd":
        cls = np.array([panel.sec_class.get(e) in RANKED_CLASSES for e in panel.entities])
        pop &= cls & t5
    rank = np.full(len(panel.entities), np.nan)
    if pop.any():
        rank[pop] = avg_rank(-m252[pop])
    return LiquidityTable(tv_med252=m252, tv_med63=m63, tv_med20=m20, tv_rank=rank, traded5=t5)
