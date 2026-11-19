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

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from trader.corporate_actions import (
    Booking,
    CaCalendar,
    CaEvent,
    CaKind,
    book_event,
    bookings_from_flex,
    expectations,
    load_ca_csv,
    vendor_events,
    vendor_split_events,
)
from trader.data.flex import FlexError, FlexStatement, parse_statements
from trader.journal import Journal
from trader.reconcile import Expected

# (codes, start, end) -> the corporate-action calendar of those codes in [start, end]
CaSource = Callable[[frozenset[str], date, date], CaCalendar]
VendorRows = Callable[
    [frozenset[str], date, date], Sequence[tuple[str, date, Decimal, date | None]]
]
# (codes, start, end) -> vendor splits / consolidations (code, date, new per old share)
VendorSplits = Callable[[frozenset[str], date, date], Sequence[tuple[str, date, Decimal]]]


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
    elif b.kind is CaKind.SPLIT:
        r = f" (x{b.ratio.normalize():f})" if b.ratio is not None else ""
        s = f"SPLIT {b.code}: {b.held} -> {b.held + b.qty_change} shares{r}, cost base kept"
    elif b.kind is CaKind.DISPOSAL:
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


def calendar_source(
    vendor: VendorRows | None, csv_path: Path | None, splits: VendorSplits | None = None
) -> CaSource:
    """Vendor dividends (and, BF-D26, splits / consolidations) of the asked codes merged
    with the record's ``CORPORATE_ACTIONS.csv`` (re-read on every call, so an entry the
    record keeper adds is used the same day; a missing file is no events, a malformed one
    raises)."""

    def source(codes: frozenset[str], start: date, end: date) -> CaCalendar:
        own = []
        if csv_path is not None and csv_path.is_file():
            own = [e for e in load_ca_csv(csv_path) if start <= e.ex_date <= end]
        rows = vendor(codes, start, end) if vendor is not None and codes else []
        spl = splits(codes, start, end) if splits is not None and codes else []
        return CaCalendar.merged([*vendor_events(rows), *vendor_split_events(spl)], own)

    return source


def flex_inbox(directory: Path) -> Callable[[date], list[FlexStatement]]:
    """Activity Flex statements saved as XML files in ``directory`` (by the Flex Web
    Service pull or by hand). Every file is read on every call; booking is idempotent,
    so a statement read twice books nothing twice. A file that does not parse raises."""

    def read(day: date) -> list[FlexStatement]:
        if not directory.is_dir():
            return []
        out: list[FlexStatement] = []
        for p in sorted(directory.glob("*.xml")):
            try:
                out += parse_statements(p.read_bytes())
            except FlexError as e:
                raise FlexError(f"{p.name}: {e}") from e
        return out

    return read
