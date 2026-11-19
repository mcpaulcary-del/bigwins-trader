"""Daily report for the EMG2-20 book (FD v3.0 §17, EMG2-20 L14; BF4). Pure text.

Every report of this book carries the L14 banner; paper reports say PAPER first and
every report carries "Not shown to beat the index" (BW-SYS-06). Figures are labelled
paper or real; nothing states or implies a return advantage.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from trader.journal import FillRecord
from trader.orders import Side

L14_BANNER = (
    "Real money. Owner override of the 12-month paper step. Brokerage about 8-9% of capital "
    "a year. Expected result at this size is below the index even if the signal works."
)
PAPER_BANNER = "PAPER (IBKR paper account / simulation). No real money is at risk."
INDEX_BANNER = "Not shown to beat the index."
CENT = Decimal("0.01")


@dataclass(frozen=True)
class DailyInputs:
    book: str
    session: date
    real_money: bool
    cash: Decimal
    positions: Mapping[str, int]
    prices: Mapping[str, Decimal]
    capital_in: Decimal
    fills_today: Sequence[FillRecord]
    commission_to_date: Decimal
    orders_today: Sequence[tuple[str, str]]  # (client_order_id, status)
    safety: str
    flags: Sequence[str] = ()
    recon_breaks: Sequence[str] = ()
    sim_value: Decimal | None = None  # EMG2_20_SIM twin (L13)
    a200_value: Decimal | None = None  # the same money in A200 (L14 monthly)


def value_of(positions: Mapping[str, int], prices: Mapping[str, Decimal], cash: Decimal) -> Decimal:
    return (
        cash + sum((prices.get(e, Decimal(0)) * q for e, q in positions.items()), Decimal(0))
    ).quantize(CENT)


def daily_report(x: DailyInputs) -> str:
    value = value_of(x.positions, x.prices, x.cash)
    lines = [L14_BANNER if x.real_money else PAPER_BANNER, INDEX_BANNER, ""]
    lines.append(f"{x.book} - {x.session.isoformat()} - safety {x.safety}")
    pct = (value / x.capital_in - 1) if x.capital_in else Decimal(0)
    lines.append(
        f"Value A${value} (cash A${x.cash.quantize(CENT)}); capital in A${x.capital_in}; "
        f"result {pct:+.2%}"
    )
    share = (x.commission_to_date / x.capital_in) if x.capital_in else Decimal(0)
    lines.append(
        f"Brokerage to date A${x.commission_to_date.quantize(CENT)} ({share:.2%} of capital)"
    )
    if x.sim_value is not None:
        lines.append(
            f"Simulated twin EMG2_20_SIM A${x.sim_value.quantize(CENT)} "
            f"(difference A${(value - x.sim_value).quantize(CENT)})"
        )
    if x.a200_value is not None:
        lines.append(f"Same money in A200: A${x.a200_value.quantize(CENT)}")
    lines.append(f"Holdings ({len([q for q in x.positions.values() if q])}):")
    for e, q in sorted(x.positions.items()):
        px = x.prices.get(e)
        val = f"A${(px * q).quantize(CENT)}" if px is not None else "no price"
        lines.append(f"  {e:<8} {q:>8} @ {px if px is not None else '-'} = {val}")
    lines.append(f"Orders today ({len(x.orders_today)}):")
    lines += [f"  {c} {s}" for c, s in x.orders_today]
    lines.append(f"Fills today ({len(x.fills_today)}):")
    for f in x.fills_today:
        sign = "+" if f.side is Side.BUY else "-"
        lines.append(f"  {sign}{f.qty} {f.entity} @ {f.price} comm A${f.commission}")
    if x.recon_breaks:
        lines.append("RECONCILIATION BREAKS (HALTED_INTEGRITY):")
        lines += [f"  {b}" for b in x.recon_breaks]
    if x.flags:
        lines.append("Flags: " + "; ".join(x.flags))
    return "\n".join(lines)
