"""The 100 random twins of the simulated EMG2-18 book (AMENDMENT_live_EMG2_20 L13 and
book table; AMENDMENT_live_EMG2_18: ``EMG2_18_RND_s001...s100``, seeds 8550000 + i).
PAPER ONLY: simulated books, never a broker order.

Each random twin follows the EMG2-18 rules of the simulated twin ``EMG2_18_SIM`` at the
same costs, with one change (AMENDMENT_shadow_EMG2 rule 12, report 85's twin): the
order of rule 3 is replaced by a **persistent seeded random score per entity, redrawn
with probability 0.2 a month**; the twin's target list is the same count of names as T,
taken from band C (bid-pegged names excluded) by that random score, best first.

The score is counter-based (BF-D18): for twin seed ``s``, entity ``e`` and decision
month ``m`` (months counted from the twins' first decision month ``m0``), the score is
the uniform draw ``U(s, e, k, "score")`` of the latest month ``k`` in ``(m0, m]`` whose
redraw draw ``U(s, e, k, "redraw") < 0.2``, or of ``m0`` if there is none. Each ``U`` is
the first 8 bytes of a SHA-256 of ``(s, e, k, tag)`` read as a fraction of 2**64. The
result is a persistent score per entity, redrawn independently with probability 0.2 a
month, that needs no stored random-generator state, does not depend on the order of
band C or on a restart, and is the same on every platform.

BF-D36 (``AMENDMENT_twins_buyable_set.md``, record ledger seq 83, paper code seq 85): from
the 30 Nov 2026 decision (``BUYABLE_FROM``) the twin's list is drawn **by stratum** so that
it holds exactly as many buyable names as T: with m = the names of T that are not lottery
class, the m best random scores among the band-C names that are neither bid-pegged nor
lottery class plus the ``len(T) - m`` best among the band-C names that are not bid-pegged
and are lottery class, best first. The lottery class is the one the real book's buy step
uses at the same decision (a name without a flag counts as lottery class). Decisions
before that date keep the old draw (the top ``len(T)`` of band C without pegged names), as
the record's ``paper_emg2s.lists_for``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

import numpy as np

from trader.features import pct_rank
from trader.lines.emg2 import Emg2List

SEED_BASE = 8550000  # AMENDMENT_live_EMG2_20 book table: seeds 8550000 + i
N_TWINS = 100
REDRAW = 0.2  # probability a month that an entity's score is drawn again
_SCALE = float(2**64)
# BF-D36: first decision whose twin lists are drawn by buyable / lottery stratum
BUYABLE_FROM = date(2026, 11, 30)


def twin_books(
    prefix: str, n: int = N_TWINS, seed_base: int = SEED_BASE
) -> tuple[tuple[str, int], ...]:
    """``(book, seed)`` of the random twins: ``<prefix>_s001`` ... with seed base + i."""
    return tuple((f"{prefix}_s{i:03d}", seed_base + i) for i in range(1, n + 1))


def month_index(d: date) -> int:
    return d.year * 12 + d.month - 1


def uniform(seed: int, entity: str, month: int, tag: str) -> float:
    """A reproducible uniform draw in [0, 1) for (seed, entity, month, tag)."""
    h = hashlib.sha256(f"{seed}|{entity}|{month}|{tag}".encode()).digest()
    return int.from_bytes(h[:8], "big") / _SCALE


def random_score(seed: int, entity: str, month: int, origin: int) -> float:
    """The entity's persistent random score at decision month ``month`` (BF-D18)."""
    for k in range(month, origin, -1):
        if uniform(seed, entity, k, "redraw") < REDRAW:
            return uniform(seed, entity, k, "score")
    return uniform(seed, entity, origin, "score")


@dataclass(frozen=True)
class RandomOrder:
    """Target order of one random twin at one decision (``decide_emg2_20``'s
    ``target_order``): ``len(T)`` names of band C, bid-pegged names excluded, with the
    highest random score, best first; ties by entity code. From ``buyable_from`` (BF-D36)
    drawn by stratum: as many buyable (not lottery class) names as T has, the rest from
    the lottery class; ``lottery`` None (the buy step skips no lottery name): one draw."""

    seed: int
    origin: int  # month index of the twins' first decision
    month: int  # month index of this decision
    buyable_from: date = BUYABLE_FROM

    def __call__(
        self, lst: Emg2List, pegged: frozenset[str], lottery: Mapping[str, bool] | None = None
    ) -> tuple[str, ...]:
        pool = [r.entity for r in lst.band_c if r.entity not in pegged]
        scored = sorted(
            pool, key=lambda e: (-random_score(self.seed, e, self.month, self.origin), e)
        )
        n = len(lst.targets)
        if lottery is None or lst.as_of < self.buyable_from.isoformat():
            return tuple(scored[:n])
        m = sum(1 for e in lst.targets if not lottery.get(e, True))
        buy = [e for e in scored if not lottery.get(e, True)][:m]
        lot = [e for e in scored if lottery.get(e, True)][: n - m]
        chosen = set(buy) | set(lot)
        return tuple(e for e in scored if e in chosen)

    def keep_zone(self, lst: Emg2List, keep_fraction: float) -> frozenset[str]:
        """BF-D35 (rule C6 in a random twin): the keep zone is the members of band C whose
        percentile of this twin's random score (average rank / count over the whole band,
        as the EMG2 score's ``score_pct``) is above ``1 - keep_fraction``."""
        names = [r.entity for r in lst.band_c]
        if not names:
            return frozenset()
        x = np.array([random_score(self.seed, e, self.month, self.origin) for e in names])
        pct = pct_rank(x)
        return frozenset(e for e, v in zip(names, pct, strict=True) if v > 1.0 - keep_fraction)
