"""ASX trading calendar and event blackouts (spec §5; OPS-05, SYS-14).

Holidays and half-days come **only** from the ``calendar`` table (OPS-05). This
module contains no holiday list, no weekday rule and no holiday library: a date
missing from the table is an error (``CalendarGapError``), never a guess. The
table is seeded by Alembic migration 0003 and reloaded yearly from the ASX
calendar (§17).

All dates are ASX local dates; close times are Australia/Sydney wall-clock
times and are converted to UTC for storage or comparison (SYS-14).
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.enums import BLACKOUT_EVENT_TYPES, EventType
from trader.timeutil import asx_local_to_utc


class CalendarGapError(LookupError):
    """The date is not in the ``calendar`` table; nothing is assumed (OPS-05)."""


@dataclass(frozen=True)
class CalendarEntry:
    date: date
    is_trading: bool
    close_time: time | None


@dataclass(frozen=True)
class EventEntry:
    symbol: str | None
    type: EventType
    date: date
    is_estimate: bool


class AsxCalendar:
    """Read-only view over ``calendar`` rows."""

    def __init__(self, entries: Iterable[CalendarEntry]) -> None:
        self._by_date: dict[date, CalendarEntry] = {}
        for e in entries:
            if e.date in self._by_date:
                raise ValueError(f"duplicate calendar date {e.date}")
            if e.is_trading != (e.close_time is not None):
                raise ValueError(f"{e.date}: trading days need a close_time, closed days none")
            self._by_date[e.date] = e
        if not self._by_date:
            raise CalendarGapError("calendar table is empty")
        self._dates = sorted(self._by_date)
        if (self._dates[-1] - self._dates[0]).days + 1 != len(self._dates):
            raise CalendarGapError("calendar table has gaps between its first and last date")
        self._trading = [d for d in self._dates if self._by_date[d].is_trading]
        self._normal_close = max(
            (e.close_time for e in self._by_date.values() if e.close_time is not None)
        )

    # -- construction -------------------------------------------------------
    @classmethod
    def from_session(cls, session: Session) -> AsxCalendar:
        from trader.ledger import CalendarDay

        rows = session.execute(select(CalendarDay)).scalars().all()
        return cls(CalendarEntry(r.date, r.is_trading, r.close_time) for r in rows)

    # -- lookups ------------------------------------------------------------
    @property
    def first_date(self) -> date:
        return self._dates[0]

    @property
    def last_date(self) -> date:
        return self._dates[-1]

    def entry(self, d: date) -> CalendarEntry:
        try:
            return self._by_date[d]
        except KeyError:
            raise CalendarGapError(
                f"{d} is not in the calendar table ({self.first_date}..{self.last_date}); "
                "load the ASX calendar for that year"
            ) from None

    def is_trading_day(self, d: date) -> bool:
        return self.entry(d).is_trading

    def close_time(self, d: date) -> time:
        """Australia/Sydney closing-auction time on trading day ``d``."""
        e = self.entry(d)
        if e.close_time is None:
            raise ValueError(f"{d} is not a trading day")
        return e.close_time

    def close_utc(self, d: date) -> datetime:
        return asx_local_to_utc(d, self.close_time(d))

    def is_half_day(self, d: date) -> bool:
        """Early close: close time earlier than the normal close in the table."""
        return self.close_time(d) < self._normal_close

    def next_trading_day(self, d: date) -> date:
        self.entry(d)
        i = bisect.bisect_right(self._trading, d)
        if i >= len(self._trading):
            raise CalendarGapError(f"no trading day after {d} in the calendar table")
        return self._trading[i]

    def prev_trading_day(self, d: date) -> date:
        self.entry(d)
        i = bisect.bisect_left(self._trading, d)
        if i == 0:
            raise CalendarGapError(f"no trading day before {d} in the calendar table")
        return self._trading[i - 1]

    def add_trading_days(self, d: date, n: int) -> date:
        """Move ``n`` trading days from trading day ``d`` (negative = back)."""
        if not self.is_trading_day(d):
            raise ValueError(f"{d} is not a trading day")
        i = bisect.bisect_left(self._trading, d) + n
        if not 0 <= i < len(self._trading):
            raise CalendarGapError(f"{d} {n:+d} trading days is outside the calendar table")
        return self._trading[i]

    def trading_days(self, start: date, end: date) -> list[date]:
        """Trading days in [start, end]; both ends must be in the table."""
        self.entry(start)
        self.entry(end)
        lo = bisect.bisect_left(self._trading, start)
        hi = bisect.bisect_right(self._trading, end)
        return self._trading[lo:hi]

    def __iter__(self) -> Iterator[CalendarEntry]:
        return (self._by_date[d] for d in self._dates)

    # -- blackouts (§5) -----------------------------------------------------
    def blackout_dates(
        self, event: EventEntry, offsets: tuple[int, int], estimate_widen: int
    ) -> list[date]:
        """Execution dates whose buys are blocked by ``event``.

        Window = trading days [V+lo, V+hi] counted in trading days, widened by
        ``estimate_widen`` trading days each side if the date is an estimate.
        V itself is always included. If V is not a trading day, the lower end is
        counted from the previous trading day and the upper end from the next
        one (wider, conservative). Events without blackout return [].
        """
        if event.type not in BLACKOUT_EVENT_TYPES:
            return []
        lo, hi = offsets
        if event.is_estimate:
            lo, hi = lo - estimate_widen, hi + estimate_widen
        v = event.date
        if self.is_trading_day(v):
            v_lo = v_hi = v
        else:
            v_lo, v_hi = self.prev_trading_day(v), self.next_trading_day(v)
        start = self.add_trading_days(v_lo, lo)
        end = self.add_trading_days(v_hi, hi)
        return self.trading_days(start, end)


def load_events(session: Session) -> list[EventEntry]:
    from trader.ledger import Event

    rows = session.execute(select(Event).order_by(Event.date, Event.id)).scalars().all()
    return [EventEntry(r.symbol, r.type, r.date, r.is_estimate) for r in rows]


def days_between(a: date, b: date) -> Iterator[date]:
    """Every calendar date in [a, b] (helper for seeding and tests)."""
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)
