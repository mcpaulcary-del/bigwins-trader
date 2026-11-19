"""L11 staged loss rule for the EMG2-18 slice (owner decision 19 Nov 2026, report 88
§4.2, "Fable's staged rule"; supersedes the A$6,000 "pause buys, owner resumes" rule
of BF-D14). Pure: the app (``trader.bf_app``) feeds it readings and acts on the result.

1. NAV < A$7,000: high-priority page and an **integrity check** (live holdings equal
   the simulated twin; fills and costs as modelled).
2. NAV < A$6,000: new buys pause (``HALTED_BUYS``) until the next month-end decision
   at the latest, then **resume automatically** unless (a) the integrity check fails,
   (b) the twin is below the 10th percentile of its 100 random twins since the start,
   (c) an L12 stop rule is met, or (d) the owner said stop. Sells continue normally.
3. NAV < A$5,000: the same test, and the owner must confirm in writing
   (``/continue <code>``) to continue; without it by the next decision the book is
   sold over two decisions (half of each holding, then the rest).

A failed test keeps buys paused and is re-run at each later decision. The owner's
``/resume <code>`` (2FA) ends an episode at any time, including a wind-down.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from trader.orders import CommissionModel, Side

PERCENTILE_FLOOR = Decimal(10)  # (b): below the 10th percentile of the random twins


def stage_of(
    value: Decimal,
    alert: Decimal = Decimal(7000),
    pause: Decimal = Decimal(6000),
    confirm: Decimal = Decimal(5000),
) -> int:
    """0 none, 1 alert (< A$7,000), 2 pause (< A$6,000), 3 confirm (< A$5,000)."""
    if value < confirm:
        return 3
    if value < pause:
        return 2
    if value < alert:
        return 1
    return 0


def percentile_rank(x: Decimal, others: Sequence[Decimal]) -> Decimal | None:
    """Share (0-100) of ``others`` (the random twins' returns since the start) below
    ``x``, ties counted half. None when there are no twins."""
    if not others:
        return None
    below = sum(1 for o in others if o < x)
    ties = sum(1 for o in others if o == x)
    return (Decimal(100) * (Decimal(below) + Decimal(ties) / 2) / len(others)).quantize(
        Decimal("0.1")
    )


@dataclass(frozen=True)
class ModelledFill:
    """A broker-book fill with the order it filled (for the "as modelled" check)."""

    order_ref: str  # the client order id: IBKR charges the minimum once per order
    entity: str
    side: Side
    qty: int
    price: Decimal
    commission: Decimal
    limit_price: Decimal


def integrity_breaks(
    sim_positions: Mapping[str, int],
    book_positions: Mapping[str, int],
    explained: Iterable[str],
    fills: Iterable[ModelledFill],
    commission: CommissionModel | None = None,
    tolerance: Decimal = Decimal("0.01"),
) -> tuple[str, ...]:
    """Stage-1 integrity check. Holdings: a name held by one book only, not explained
    by an order that did not fill or a recorded decision difference (L13). Fills: a
    buy above its limit, a sell below it, or a commission that differs from the IBKR
    model by a cent or more."""
    cm = commission or CommissionModel()
    ok = set(explained)
    held_sim = {e for e, q in sim_positions.items() if q}
    held_book = {e for e, q in book_positions.items() if q}
    out = [
        f"HOLDING {e}: only in the {'simulated' if e in held_sim else 'live'} book"
        for e in sorted(held_sim ^ held_book)
        if e not in ok
    ]
    orders: dict[str, list[ModelledFill]] = {}
    for f in fills:
        if f.side is Side.BUY and f.price > f.limit_price:
            out.append(f"FILL {f.entity}: buy at {f.price} above limit {f.limit_price}")
        if f.side is Side.SELL and f.price < f.limit_price:
            out.append(f"FILL {f.entity}: sell at {f.price} below limit {f.limit_price}")
        orders.setdefault(f.order_ref, []).append(f)
    for ref, fs in orders.items():
        paid = sum((f.commission for f in fs), Decimal(0))
        model = cm(sum((f.price * f.qty for f in fs), Decimal(0)))
        if (paid - model).copy_abs() >= tolerance:
            out.append(f"COST {fs[0].entity} ({ref}): commission {paid} vs model {model}")
    return tuple(out)


@dataclass(frozen=True)
class StagedTest:
    """The test run at the decision for stages 2 and 3."""

    integrity: tuple[str, ...]  # integrity breaks (empty = passed)
    twin_percentile: Decimal | None  # None: the 100 random twins are not available
    l12_stop: str | None  # the L12 stop rule met, if any
    owner_stop: bool

    def failures(self) -> tuple[str, ...]:
        out: list[str] = []
        if self.integrity:
            out.append("(a) integrity check failed: " + "; ".join(self.integrity[:3]))
        if self.twin_percentile is None:
            out.append("(b) twin percentile unknown: the 100 random twins are not available")
        elif self.twin_percentile < PERCENTILE_FLOOR:
            out.append(
                f"(b) twin at the {self.twin_percentile} percentile of its random twins "
                f"(< {PERCENTILE_FLOOR})"
            )
        if self.l12_stop:
            out.append(f"(c) L12 stop rule met: {self.l12_stop}")
        if self.owner_stop:
            out.append("(d) the owner said stop")
        return tuple(out)


class Outcome(StrEnum):
    RESUME = "RESUME"  # buys resume automatically
    STAY_PAUSED = "STAY_PAUSED"  # test failed (or stage 3 confirmed but failed): owner decides
    WIND_DOWN = "WIND_DOWN"  # stage 3 not confirmed: sell over two decisions


def at_decision(stage: int, test: StagedTest, confirmed: bool) -> tuple[Outcome, tuple[str, ...]]:
    """What the month-end decision does for an open stage-2/3 episode."""
    if stage < 2:
        raise ValueError("no paused episode below stage 2")
    fails = test.failures()
    if stage >= 3 and not confirmed:
        return Outcome.WIND_DOWN, (*fails, "stage 3: no written confirmation (/continue)")
    return (Outcome.STAY_PAUSED, fails) if fails else (Outcome.RESUME, ())


def wind_down_qty(held: int, step: int) -> int:
    """Units to sell at wind-down step 1 (half, rounded up) or step 2 (all left)."""
    if held <= 0:
        return 0
    return (held + 1) // 2 if step == 1 else held
