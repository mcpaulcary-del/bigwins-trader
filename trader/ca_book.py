"""Booking corporate actions into the journal (BF-D23). PAPER ONLY.

* ``ingest_flex``: a broker book's dividends, capital returns and corporate actions from
  IBKR's Activity Flex statements (idempotent; a code change IBKR reports is recorded as
  a PROPOSED identity change with its ratio, owner to confirm by ``/idmap``);
* ``book_calendar_day``: the simulated books' events of an ex-date from the calendar
  (vendor + the record's ``CORPORATE_ACTIONS.csv``), on the holding at the close before;
* ``pending_expectations``: the calendar events a broker book's Flex records have not
  yet settled, for reconciliation (``trader.reconcile.Expected``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from trader.corporate_actions import (
    Booking,
    CaCalendar,
    CaEvent,
    CaKind,
    book_event,
    bookings_from_flex,
    expectations,
)
from trader.data.flex import FlexStatement
from trader.journal import Journal
from trader.reconcile import Expected


@dataclass(frozen=True)
class IngestResult:
    booked: tuple[Booking, ...]
    identity: tuple[str, ...]  # code changes recorded from IBKR's records
    skipped: tuple[str, ...]

    def lines(self) -> list[str]:
        out = [describe(b) for b in self.booked]
        out += [f"code change from IBKR: {x}" for x in self.identity]
        return out


def describe(b: Booking) -> str:
    if b.kind in (CaKind.DEMERGER, CaKind.IN_SPECIE):
        s = f"{b.kind.value} {b.code}: {b.new_shares} {b.new_code} received"
        if b.cost_moved_pct is not None:
            s += f", {b.cost_moved_pct * 100:.2f}% of the cost base moved"
        if b.child_cost is not None:
            s += f", cost base A${b.child_cost}"
    elif b.kind is CaKind.CODE_CHANGE:
        s = f"CODE_CHANGE {b.code} -> {b.new_code} ratio {b.ratio}"
    elif b.kind in (CaKind.SPLIT, CaKind.DISPOSAL):
        s = f"{b.kind.value} {b.code}: {b.qty_change:+d} shares"
    else:
        s = f"{b.kind.value} {b.code}"
        if b.held:
            s += f" on {b.held}"
    if b.cash:
        s += f", cash A${b.cash.quantize(Decimal('0.01'))}"
    if b.kind in (CaKind.DIVIDEND, CaKind.SPECIAL):
        s += (
            f", {b.franked_pct.normalize():f}% franked"
            if b.franked_pct is not None
            else ", franking not known (not counted)"
        )
    if b.kind is CaKind.CAPITAL_RETURN:
        s += " (cost base reduced, not income)"
    if b.tax_class:
        s += f" [{b.tax_class}: owner/tax agent to confirm]"
    return s


def ingest_flex(
    j: Journal,
    book: str,
    statements: Iterable[FlexStatement],
    cal: CaCalendar,
    px: Mapping[str, Decimal] | None = None,
    now: datetime | None = None,
) -> IngestResult:
    """Book a broker book's corporate actions from IBKR's Flex records, once each."""
    fb = bookings_from_flex(statements, cal, lambda c, d: j.held_at(book, c, d), px)
    booked = tuple(b for b in fb.bookings if j.add_ca(book, b, now))
    ids: list[str] = []
    recs = j.identity_records()
    for h in fb.identity:
        r = recs.get(h.old)
        same = (
            r is not None
            and r["status"] in ("PROPOSED", "CONFIRMED")
            and r["new_code"] == h.new
            and Decimal(str(r["ratio"] or 1)) == h.ratio
        )
        if same:
            continue
        j.add_identity(
            h.old, h.new, "PROPOSED", "FLEX", None, "flex",
            f"IBKR corporate action {h.key}", now, ratio=h.ratio,
        )  # fmt: skip
        ids.append(f"{h.old} -> {h.new} ratio {h.ratio.normalize():f}")
    return IngestResult(booked, tuple(ids), fb.skipped)


def book_calendar_day(
    j: Journal,
    books: Sequence[str],
    events: Iterable[CaEvent],
    px: Mapping[str, Decimal] | None = None,
    now: datetime | None = None,
) -> list[tuple[str, Booking]]:
    """Simulated books: each event of the day on the holding at the close before."""
    out: list[tuple[str, Booking]] = []
    evs = list(events)
    for book in books:
        for ev in evs:
            b = book_event(ev, j.held_at(book, ev.code, ev.ex_date), px)
            if b is not None and j.add_ca(book, b, now):
                out.append((book, b))
    return out


def pending_expectations(j: Journal, book: str, cal: CaCalendar, today: date) -> list[Expected]:
    """Calendar events of the last months a broker book is entitled to and IBKR's Flex
    records have not yet settled."""
    evs = cal.between(today - timedelta(days=120), today)
    return expectations(evs, lambda c, d: j.held_at(book, c, d), j.ca_settled(book), today)
