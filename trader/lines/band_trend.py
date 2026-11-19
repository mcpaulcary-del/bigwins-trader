"""Band-trend switch of the EMG2-18 book (rule L15; BF-D28). Pure.

Registered text: ``AMENDMENT_live_EMG2_18_BT.md`` (owner decision, report 96) with the
rules BT1-BT4 of ``AMENDMENT_shadow_EMG2_18_BT.md`` (its section R gives the index as
the paper record computes it; this module follows it):

* **BT1 band index.** At the decision session D take the last ``months`` month-ends of
  the panel (the last session of each calendar month, D included as the newest). At
  each month-end m, band C(m) = the EMG2 list's band C of the panel cut at m
  (``PricePanel.truncate``: the same data, universe, class and A7 rules as the
  decision engine). The level moves from m to the next month-end m' by the mean over
  C(m) of the names' total return from m to m' (equal weight at m, buy and hold inside
  the month; returns from ``panel.ret``, an invalid return counted as 0, as the
  momentum features). An empty band leaves the level unchanged. The first level is 1;
  the test is scale-free.
* **BT2 state.** ON ("state: EMG2") iff the newest level >= the mean of the levels
  (D included); fewer than ``months`` levels -> ON. OFF = "state: FUND".
* BT3 / BT4 (what a book does in each state) are in ``trader.lines.emg2.decide_emg2_18_bt``.

Deterministic: ``BandTrend.digest`` is the SHA-256 of its canonical JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

import numpy as np

from trader.canonical import sha256_json
from trader.lines.emg2 import Emg2Params, emg2_list
from trader.panel import PricePanel

State = Literal["EMG2", "FUND"]


@dataclass(frozen=True)
class BandTrendParams:
    """Config ``band_trend`` (``config/bfast.yaml``; BF-D28)."""

    enabled: bool = False
    fund: str = "A200"  # the ASX 200 fund of the record (Betashares Australia 200 ETF)
    months: int = 10  # BT2: the mean of the last 10 month-end levels
    top_up_fraction: float = 0.10  # BT3: a later OFF decision tops the fund up only above this
    fund_half_spread: float = 0.0005  # the twins' fund spread a side (report 96's fund model)


@dataclass(frozen=True)
class BandTrend:
    as_of: str
    state: State
    level: float
    mean: float
    levels: tuple[tuple[str, float, int], ...]  # (month-end, level, members of band C)

    @property
    def on(self) -> bool:
        return self.state == "EMG2"

    def payload(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of,
            "state": self.state,
            "level": round(self.level, 10),
            "mean": round(self.mean, 10),
            "levels": [[m, round(v, 10), n] for m, v, n in self.levels],
        }

    @property
    def digest(self) -> str:
        return sha256_json(self.payload())

    def describe(self) -> str:
        rel = "at or above" if self.on else "below"
        return (
            f"state: {self.state} (band 301-600 index {self.level:.4f} {rel} its "
            f"{len(self.levels)}-month average {self.mean:.4f}, {self.as_of})"
        )


def month_end_rows(dates: tuple[date, ...], months: int) -> list[int]:
    """Rows of the last ``months`` month-ends: the last session of each calendar month
    in the panel; the panel's last row (the decision) is the newest."""
    rows = [
        i
        for i in range(len(dates) - 1)
        if (dates[i + 1].year, dates[i + 1].month) != (dates[i].year, dates[i].month)
    ]
    rows.append(len(dates) - 1)
    return rows[-months:]


def band_trend(
    panel: PricePanel, params: BandTrendParams | None = None, list_params: Emg2Params | None = None
) -> BandTrend:
    """BT1/BT2 at the panel's session D."""
    p = params or BandTrendParams()
    rows = month_end_rows(panel.dates, p.months)
    r = panel.ret
    lg = np.cumsum(np.log1p(np.where(np.isnan(r), 0.0, r)), axis=0)
    col = {e: j for j, e in enumerate(panel.entities)}
    levels: list[tuple[str, float, int]] = []
    lev = 1.0
    for q, m in enumerate(rows):
        d = panel.dates[m]
        members = [col[x.entity] for x in emg2_list(panel.truncate(d), list_params).band_c]
        levels.append((d.isoformat(), lev, len(members)))
        if q + 1 < len(rows) and members:
            m1 = rows[q + 1]
            lev *= float(np.mean(np.exp(lg[m1, members] - lg[m, members])))
    vals = [v for _, v, _ in levels]
    mean = float(np.mean(vals))
    on = len(vals) < p.months or vals[-1] >= mean
    state: State = "EMG2" if on else "FUND"
    return BandTrend(panel.as_of.isoformat(), state, vals[-1], mean, tuple(levels))
