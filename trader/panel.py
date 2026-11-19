"""``PricePanel``: the point-in-time market data a pure line function may see (FD v3.0 §3.3).

B-fast reduction of ``PitData``: daily rows for every entity up to and including the
decision session D, nothing later (BW-SYS-12). The panel is built by a data adapter
(``trader.data.forward_store`` in B-fast, the B1 feature store later) and is the only
market input of ``trader.lines.emg2``.

Arrays are ``T x N`` float64 (rows = sessions, columns = entities):

* ``close``: raw close as traded (NaN = no row that session);
* ``ret``: split-neutral total return of the session (rules v1.3 A3; NaN = invalid);
* ``tv``: traded value = split-adjusted close x vendor volume (Amendment v1.4;
  NaN = no row).

The arrays are made read-only so that no consumer can mutate shared input.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]

SEC_CLASSES = frozenset({"ORD", "REIT", "LIC", "FUND", "OTHER", "DUAL"})


class PanelError(ValueError):
    """BW-SYS-12: a row dated after ``as_of``, or a malformed panel."""


def _frozen(a: npt.ArrayLike, name: str, shape: tuple[int, int]) -> FloatArray:
    arr = np.array(a, dtype=np.float64, copy=True)
    if arr.shape != shape:
        raise PanelError(f"{name}: shape {arr.shape} != {shape}")
    arr.setflags(write=False)
    return arr


@dataclass(frozen=True, eq=False)
class PricePanel:
    as_of: date
    dates: tuple[date, ...]
    entities: tuple[str, ...]
    close: FloatArray
    ret: FloatArray
    tv: FloatArray
    sec_class: Mapping[str, str] = field(default_factory=dict)
    # First price row of the entity (for age, FD §8.4); may precede the panel window.
    first_session: Mapping[str, date] = field(default_factory=dict)
    # Number of sessions in the full history before ``dates[0]`` (for ages that start
    # before the panel window). 0 when the panel holds the whole history.
    sessions_before: int = 0

    def __post_init__(self) -> None:
        if not self.dates:
            raise PanelError("empty panel")
        if any(b <= a for a, b in zip(self.dates, self.dates[1:], strict=False)):
            raise PanelError("dates must be strictly increasing")
        late = [d for d in self.dates if d > self.as_of]
        if late:
            raise PanelError(f"BW-SYS-12: rows dated after as_of={self.as_of}: {late[:3]}")
        if self.dates[-1] != self.as_of:
            raise PanelError(f"last row {self.dates[-1]} is not the decision session {self.as_of}")
        if len(set(self.entities)) != len(self.entities):
            raise PanelError("duplicate entity ids")
        shape = (len(self.dates), len(self.entities))
        object.__setattr__(self, "close", _frozen(self.close, "close", shape))
        object.__setattr__(self, "ret", _frozen(self.ret, "ret", shape))
        object.__setattr__(self, "tv", _frozen(self.tv, "tv", shape))
        bad = {c for c in self.sec_class.values() if c not in SEC_CLASSES}
        if bad:
            raise PanelError(f"unknown security classes {sorted(bad)}")
        object.__setattr__(self, "sec_class", MappingProxyType(dict(self.sec_class)))
        object.__setattr__(self, "first_session", MappingProxyType(dict(self.first_session)))

    @property
    def n_sessions(self) -> int:
        return len(self.dates)

    def col(self, entity: str) -> int:
        return self.entities.index(entity)

    def truncate(self, d: date) -> PricePanel:
        """The panel as it was known at the close of session ``d`` (truncation invariance)."""
        if d not in self.dates:
            raise PanelError(f"{d} is not a session of the panel")
        k = self.dates.index(d) + 1
        return PricePanel(
            as_of=d,
            dates=self.dates[:k],
            entities=self.entities,
            close=self.close[:k],
            ret=self.ret[:k],
            tv=self.tv[:k],
            sec_class=self.sec_class,
            first_session={e: s for e, s in self.first_session.items() if s <= d},
            sessions_before=self.sessions_before,
        )
