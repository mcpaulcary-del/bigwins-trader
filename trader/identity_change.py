"""Code changes of held names (FD v3.0 §5.1 BW-UNI-02 identity; BF-D19). PAPER ONLY.

A company that changes its ASX code keeps trading under the new code with the same
prices; the vendor may carry the old history under both codes for a while and then
stop the old one (Nov 2026: HGO, Hillgrove Resources, stopped after 13 Nov; KAN,
Kantra Copper, has identical closes and volumes on every overlapping day and goes on).
The data adapter's A7 duplicate rules (A7(b) closes, A7(c) daily returns) already
find such pairs and drop the code that dies first; ``PricePanel.aliases`` keeps them.

Rule here: a code held by any book that has **no close on the session** and that A7
maps to a code that **does** trade that session has changed its code. The position is
carried under the new code (same shares, cost kept, valued at the new code's price);
the two codes are never two companies (the book cannot buy the new code as a second
name). The change is applied at once as PROPOSED and the owner is paged to confirm
(``/idmap OLD NEW <code>``) or undo it (``/idmap_reject OLD <code>``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from trader.panel import PricePanel


@dataclass(frozen=True)
class CodeChange:
    old: str
    new: str
    rule: str  # A7b | A7c
    score: float


def code_changes(
    held: Iterable[str],
    panel: PricePanel,
    traded: Iterable[str],
    known: Mapping[str, object] = {},
) -> list[CodeChange]:
    """Held codes without a close today that A7 maps to a code with one. ``known``:
    old codes already recorded (proposed, confirmed or rejected) are not raised again."""
    have = set(traded)
    out: list[CodeChange] = []
    for e in sorted(set(held)):
        if e in have or e in known:
            continue
        a = panel.aliases.get(e)
        if a is None:
            continue
        new, rule, score = a
        if new != e and new in have:
            out.append(CodeChange(e, new, rule, float(score)))
    return out
