"""BF-D90 (PROPOSED, effective only on owner approval on or after 1 Jan 2027): the sweep
sleeve of research_bw's E5, as a book holds it.

At each decision, after the rules' own orders, money above the A$10,000 capital cap buys
the fund (A200) into a sleeve the rules never count, size on or sell (``trader.lines.emg2
.add_sweep``). The sleeve's units are the same fund as the rules' own fund holding (one
broker position), so the journal tells them apart by the orders that bought them: every
filled buy of an intent flagged ``SLEEVE`` (coid tag ``SW``; a carried sleeve buy keeps
the flag). Nothing ever sells the sleeve except the owner's own wind-down (L11 stage 3 /
stop), which sells the whole book.

* ``sleeve_units``: units of the fund in the sleeve (never above the position held).
* ``rules_positions``: the positions the rules see (the fund less the sleeve).
* ``sleeve_cost``: the sleeve's share of the fund's average cost (for the capital cap of
  the rules' own buys, which leave the sleeve out).

The scoreboard, the book value, the twins' values and the tax screen count the whole
position, sleeve included.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from trader.journal import Journal
from trader.orders import SLEEVE, Side


def sleeve_units(j: Journal, book: str, held: int | None = None) -> int:
    """Units bought into the sweep sleeve (filled ``SLEEVE`` buys), at most ``held``."""
    coids = {it.client_order_id for it, _ in j.intents_of_book(book) if SLEEVE in it.flags}
    if not coids:
        return 0
    n = sum(f.qty for f in j.fills(book) if f.side is Side.BUY and f.client_order_id in coids)
    return n if held is None else max(0, min(n, held))


def sleeve_holding(j: Journal, book: str) -> tuple[str, int] | None:
    """(fund code, units) of ``book``'s sweep sleeve for the screens; None without one."""
    codes = {it.entity for it, _ in j.intents_of_book(book) if SLEEVE in it.flags}
    if len(codes) != 1:
        return None
    fund = next(iter(codes))
    units = sleeve_units(j, book, dict(j.positions(book)).get(fund, 0))
    return (fund, units) if units > 0 else None


def rules_positions(positions: Mapping[str, int], fund: str, units: int) -> dict[str, int]:
    """The book as the rules see it: the fund position less the sleeve's units."""
    out = dict(positions)
    if units and fund in out:
        rest = out[fund] - units
        if rest > 0:
            out[fund] = rest
        else:
            del out[fund]
    return out


def sleeve_cost(fund_cost: Decimal, fund_qty: Decimal, units: int) -> Decimal:
    """The sleeve's share of the fund's average cost (zero without a position)."""
    if units <= 0 or fund_qty <= 0:
        return Decimal(0)
    return (fund_cost * min(Decimal(units), fund_qty) / fund_qty).quantize(Decimal("0.01"))
