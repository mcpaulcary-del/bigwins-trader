"""Reconciliation (FD v3.0 §13 LED-01..06 carried, BW-SYS-03, EMG2-20 L13; BF4). Pure.

* ``reconcile``: ledger positions must equal the broker's to the unit, ledger cash
  the broker's settled cash to the cent. Any break -> ``HALTED_INTEGRITY`` and a page
  (BW-RSK-27); a position the ledger does not know (a foreign order, BP-02) is a break.
* ``compare_books``: L13 side by side. A holdings difference between the simulated
  twin and the broker book that is not explained by an unapproved, vetoed or unfilled
  order is ``HALTED_INTEGRITY``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from trader.risk import SafetyLevel

CENT = Decimal("0.01")


@dataclass(frozen=True)
class ReconResult:
    breaks: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.breaks

    @property
    def level(self) -> SafetyLevel:
        return SafetyLevel.NORMAL if self.ok else SafetyLevel.HALTED_INTEGRITY


def reconcile(
    ledger_positions: Mapping[str, int],
    ledger_cash: Decimal,
    broker_positions: Mapping[str, int],
    broker_cash: Decimal,
    cash_tolerance: Decimal = CENT,
) -> ReconResult:
    out: list[str] = []
    for e in sorted(set(ledger_positions) | set(broker_positions)):
        a, b = ledger_positions.get(e, 0), broker_positions.get(e, 0)
        if a != b:
            out.append(f"POSITION {e}: ledger {a} broker {b}")
    diff = (ledger_cash - broker_cash).copy_abs()
    if diff >= cash_tolerance:
        out.append(f"CASH: ledger {ledger_cash.quantize(CENT)} broker {broker_cash.quantize(CENT)}")
    return ReconResult(tuple(out))


def compare_books(
    sim_positions: Mapping[str, int],
    broker_positions: Mapping[str, int],
    explained: Iterable[str] = (),
) -> ReconResult:
    """L13: names held by one book and not the other, unless explained."""
    ok = set(explained)
    held_sim = {e for e, q in sim_positions.items() if q}
    held_brk = {e for e, q in broker_positions.items() if q}
    out = [
        f"HOLDING {e}: only in the {'simulated' if e in held_sim else 'broker'} book"
        for e in sorted(held_sim ^ held_brk)
        if e not in ok
    ]
    return ReconResult(tuple(out))
