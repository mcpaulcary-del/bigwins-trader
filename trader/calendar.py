"""ASX session calendar and venue timing (spec v2.10 §4, §5; OPS-05, SYS-14).

* Session **dates** come only from the ``calendar`` table of the market
  database (OPS-05), loaded by hand each year from the ASX published calendar.
  This module contains no holiday list and no weekday rule: a date missing from
  the table is an error (``CalendarGapError``), never a guess.
* Auction and close **times** come only from venue config (``venue.XASX``, §4)
  and the table's ``close_time``; they are never taken from a library.
* The pinned ``exchange_calendars`` library (XASX) is used only by
  ``library_cross_check`` to diff session dates (the yearly task of OPS-05).
* ``coverage_warning`` raises the OPS-05 WARN when the table covers fewer than
  ``ops.calendar_min_days_ahead`` days ahead.

All dates are ASX local dates; times are Australia/Sydney wall clock and are
converted to UTC for storage or comparison (SYS-14).
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from trader.constants import XASX
from trader.timeutil import asx_local_to_utc, ensure_utc


class CalendarGapError(LookupError):
    """The date is not in the ``calendar`` table; nothing is assumed (OPS-05)."""


@dataclass(frozen=True)
class CalendarEntry:
    date: date
    is_trading: bool
    close_time: time | None
    source: str = ""


@dataclass(frozen=True)
class VenueTimes:
    """Venue timing from ``venue.XASX`` (§4 table); never from a library."""

    opening_auction: time
    closing_auction: tuple[time, time]
    post_close_end: time
    close_available_after: time
    early_close: time

    @classmethod
    def from_config(cls, venue: object) -> VenueTimes:
        return cls(
            opening_auction=venue.opening_auction,  # type: ignore[attr-defined]
            closing_auction=venue.closing_auction,  # type: ignore[attr-defined]
            post_close_end=venue.post_close_end,  # type: ignore[attr-defined]
            close_available_after=venue.close_available_after,  # type: ignore[attr-defined]
            early_close=venue.early_close,  # type: ignore[attr-defined]
        )


class AsxCalendar:
    """Read-only view over the ``calendar`` rows of one venue."""

    def __init__(self, entries: Iterable[CalendarEntry], venue: VenueTimes | None = None) -> None:
        self.venue = venue
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
        if venue is not None:
            self._normal_close = venue.closing_auction[0]
        else:
            self._normal_close = max(
                e.close_time for e in self._by_date.values() if e.close_time is not None
            )

    # -- construction -------------------------------------------------------
    @classmethod
    def from_session(
        cls, session: Session, venue_times: VenueTimes | None = None, venue: str = XASX
    ) -> AsxCalendar:
        """Latest fetch per (venue, date) wins (bitemporal table, DAT-18)."""
        from trader.data.models import CalendarDay

        latest = (
            select(CalendarDay.date, func.max(CalendarDay.fetch_time).label("ft"))
            .where(CalendarDay.venue == venue)
            .group_by(CalendarDay.date)
            .subquery()
        )
        rows = session.execute(
            select(CalendarDay)
            .join(
                latest,
                (CalendarDay.date == latest.c.date) & (CalendarDay.fetch_time == latest.c.ft),
            )
            .where(CalendarDay.venue == venue)
        ).scalars()
        return cls(
            (CalendarEntry(r.date, r.is_trading, r.close_time, r.source) for r in rows),
            venue_times,
        )

    # -- lookups ------------------------------------------------------------
    @property
    def first_date(self) -> date:
        return self._dates[0]

    @property
    def last_date(self) -> date:
        return self._dates[-1]

    def covers(self, d: date) -> bool:
        return d in self._by_date

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
        """Venue wall-clock close (closing auction start) on trading day ``d``."""
        e = self.entry(d)
        if e.close_time is None:
            raise ValueError(f"{d} is not a trading day")
        return e.close_time

    def close_utc(self, d: date) -> datetime:
        return asx_local_to_utc(d, self.close_time(d))

    def is_early_close(self, d: date) -> bool:
        """Early close: close earlier than the venue's normal closing auction."""
        return self.close_time(d) < self._normal_close

    is_half_day = is_early_close

    def is_full_trading_day(self, d: date) -> bool:
        return self.is_trading_day(d) and not self.is_early_close(d)

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

    def next_full_trading_day(self, d: date) -> date:
        """Execution date E for evaluation date D: next full trading day (§4)."""
        e = self.next_trading_day(d)
        while self.is_early_close(e):
            e = self.next_trading_day(e)
        return e

    def add_trading_days(self, d: date, n: int) -> date:
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

    # -- evaluation dates (§4, §9.1) ---------------------------------------
    def evaluation_date(self, year: int, month: int, offset: str | int) -> date:
        """The k-th trading day of the month, or the last (``offset='last'``).

        The whole month must be in the table.
        """
        first = date(year, month, 1)
        nxt = date(year + (month == 12), month % 12 + 1, 1)
        days = self.trading_days(first, nxt - timedelta(days=1))
        if not days:
            raise CalendarGapError(f"no trading day in {year}-{month:02d}")
        if offset == "last":
            return days[-1]
        if not isinstance(offset, int) or offset < 1:
            raise ValueError(f"invalid evaluation offset {offset!r}")
        if offset > len(days):
            raise ValueError(f"{year}-{month:02d} has only {len(days)} trading days")
        return days[offset - 1]

    def evaluation_dates(self, start: date, end: date, offset: str | int) -> list[date]:
        """Evaluation dates of whole months covered by the table, in [start, end]."""
        out: list[date] = []
        y, m = start.year, start.month
        while date(y, m, 1) <= end:
            month_first = date(y, m, 1)
            month_last = date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)
            if self.covers(month_first) and self.covers(month_last):
                d = self.evaluation_date(y, m, offset)
                if start <= d <= end:
                    out.append(d)
            y, m = y + (m == 12), m % 12 + 1
        return out

    # -- venue timing (§4, OPS-08) ----------------------------------------
    def close_available_utc(self, d: date) -> datetime:
        """Earliest instant any job may read the close of trading day ``d`` (§4)."""
        if self.venue is None:
            raise ValueError("venue timing not configured")
        self.close_time(d)
        return asx_local_to_utc(d, self.venue.close_available_after)

    def latest_readable_close(self, now: datetime) -> date | None:
        """The latest trading day whose close may be read at ``now`` (OPS-08)."""
        now = ensure_utc(now)
        d = min(self.last_date, now.date() + timedelta(days=1))
        while d >= self.first_date:
            if self.is_trading_day(d) and self.close_available_utc(d) <= now:
                return d
            d -= timedelta(days=1)
        return None


# ---------------------------------------------------------------------------
# OPS-05 checks
# ---------------------------------------------------------------------------


def coverage_warning(cal: AsxCalendar, today: date, min_days_ahead: int) -> str | None:
    """WARN when the table covers fewer than ``min_days_ahead`` days ahead (OPS-05)."""
    ahead = (cal.last_date - today).days
    if ahead < min_days_ahead:
        return (
            f"OPS-05 WARN: calendar covers only {ahead} days ahead (to {cal.last_date}); "
            f"load the next ASX calendar (needs >= {min_days_ahead})"
        )
    return None


@dataclass(frozen=True)
class LibraryDiff:
    """Session-date differences between the table and the library (OPS-05)."""

    only_in_table: tuple[date, ...]
    only_in_library: tuple[date, ...]

    @property
    def ok(self) -> bool:
        return not self.only_in_table and not self.only_in_library


def library_sessions(start: date, end: date, library_calendar: str = "XASX") -> set[date]:
    """Session dates from the pinned ``exchange_calendars`` (dates only)."""
    import exchange_calendars as xcals  # pinned; used only for this cross-check

    cal = xcals.get_calendar(library_calendar)
    lo = max(start, cal.first_session.date())
    hi = min(end, cal.last_session.date())
    if lo > hi:
        return set()
    return {ts.date() for ts in cal.sessions_in_range(lo.isoformat(), hi.isoformat())}


def library_cross_check(
    cal: AsxCalendar,
    start: date,
    end: date,
    sessions: set[date] | None = None,
    library_calendar: str = "XASX",
) -> LibraryDiff:
    """Diff the table's session dates against the library's (yearly task, OPS-05).

    Only dates are compared; close and auction times are never read from the
    library (it treats the ASX close as 16:00).
    """
    lib = sessions if sessions is not None else library_sessions(start, end, library_calendar)
    table = set(cal.trading_days(start, end))
    lib = {d for d in lib if start <= d <= end}
    return LibraryDiff(tuple(sorted(table - lib)), tuple(sorted(lib - table)))


def days_between(a: date, b: date) -> Iterator[date]:
    """Every calendar date in [a, b] (helper for seeding and tests)."""
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)
