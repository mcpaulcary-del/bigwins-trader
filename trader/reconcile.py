"""Reconciliation (FD v3.0 §13 LED-01..06 carried, BW-SYS-03, EMG2-20 L13; BF4). Pure.

* ``reconcile``: ledger positions must equal the broker's to the unit, ledger cash
  the broker's settled cash to the cent. Any break -> ``HALTED_INTEGRITY`` and a page
  (BW-RSK-27); a position the ledger does not know (a foreign order, BP-02) is a break.
* pending corporate actions (BF-D23): a difference that an expected, not yet booked
  event explains to the share and within the cash band (``Expected``; a dividend or a
  demerger IBKR has credited before its Flex statement arrives) is not a break; it is
  listed in ``explained``. Anything else still halts.
* ``compare_books``: L13 side by side. A holdings difference between the simulated
  twin and the broker book that is not explained by an unapproved, vetoed or unfilled
  order is ``HALTED_INTEGRITY``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import combinations

from trader.risk import SafetyLevel

CENT = Decimal("0.01")


CASH_BAND = Decimal("0.005")  # a pending cash event matches within 0.5% (at least a cent)
MAX_SUBSET = 6  # pending cash events tried together


@dataclass(frozen=True)
class Expected:
    """A corporate action the broker may already show and the ledger not yet (BF-D23):
    ``cash`` to the book, ``shares`` by code (new shares received). ``approx``: the share
    count is not known exactly (any positive count of the new code matches)."""

    key: str
    label: str
    cash: Decimal = Decimal(0)
    shares: Mapping[str, int] = field(default_factory=dict)
    approx: bool = False


@dataclass(frozen=True)
class ReconResult:
    breaks: tuple[str, ...]
    explained: tuple[str, ...] = ()

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
    pending: Sequence[Expected] = (),
) -> ReconResult:
    out: list[str] = []
    why: list[str] = []
    for e in sorted(set(ledger_positions) | set(broker_positions)):
        a, b = ledger_positions.get(e, 0), broker_positions.get(e, 0)
        if a != b:
            hit = _share_match(e, b - a, pending)
            if hit is None:
                out.append(f"POSITION {e}: ledger {a} broker {b}")
            else:
                why.append(f"POSITION {e}: ledger {a} broker {b}, pending {hit.label}")
    diff = broker_cash - ledger_cash
    if diff.copy_abs() >= cash_tolerance:
        hits = _cash_match(diff, pending, cash_tolerance)
        if hits is None:
            out.append(
                f"CASH: ledger {ledger_cash.quantize(CENT)} broker {broker_cash.quantize(CENT)}"
            )
        else:
            labels = ", ".join(h.label for h in hits)
            why.append(f"CASH: broker {diff.quantize(CENT):+} vs ledger, pending {labels}")
    return ReconResult(tuple(out), tuple(why))


def _share_match(code: str, diff: int, pending: Sequence[Expected]) -> Expected | None:
    """Broker has ``diff`` more shares of ``code`` than the ledger: a pending share
    receipt of that code explains it exactly (one share either way for rounding of a
    fraction), or any positive count when the ratio is not known."""
    for x in pending:
        want = x.shares.get(code)
        if want is None:
            continue
        if (x.approx and diff > 0) or abs(diff - want) <= 1:
            return x
    return None


def _cash_match(
    diff: Decimal, pending: Sequence[Expected], tol: Decimal
) -> tuple[Expected, ...] | None:
    cands = [x for x in pending if x.cash][:12]
    for n in range(1, min(MAX_SUBSET, len(cands)) + 1):
        for sub in combinations(cands, n):
            s = sum((x.cash for x in sub), Decimal(0))
            if (diff - s).copy_abs() <= max(tol, (s * CASH_BAND).copy_abs()):
                return sub
    return None


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
