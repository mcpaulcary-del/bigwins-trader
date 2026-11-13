"""Time handling (SYS-14).

Timestamps are stored in UTC; dates are ASX local dates (Australia/Sydney);
schedules use Australia/Sydney. Naive datetimes are refused everywhere.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from trader.constants import ASX_TZ


class NaiveDatetimeError(ValueError):
    """Raised when a naive (timezone-less) datetime is used."""


def utc_now() -> datetime:
    """Current time as an aware UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(ts: datetime) -> datetime:
    """Return ``ts`` converted to UTC. Naive datetimes are rejected."""
    if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) is None:
        raise NaiveDatetimeError(f"naive datetime refused (SYS-14): {ts!r}")
    return ts.astimezone(UTC)


def asx_date(ts: datetime) -> date:
    """The ASX local (Australia/Sydney) calendar date of an instant."""
    return ensure_utc(ts).astimezone(ASX_TZ).date()


def asx_today() -> date:
    """Today's ASX local date."""
    return asx_date(utc_now())


def asx_local(d: date, t: time) -> datetime:
    """An Australia/Sydney wall-clock time on ASX date ``d``, as aware datetime."""
    if t.tzinfo is not None:
        raise NaiveDatetimeError("pass a wall-clock time without tzinfo; zone is Australia/Sydney")
    return datetime.combine(d, t, tzinfo=ASX_TZ)


def asx_local_to_utc(d: date, t: time) -> datetime:
    """Australia/Sydney wall-clock time on ``d`` converted to UTC (for storage)."""
    return asx_local(d, t).astimezone(UTC)


def parse_hhmm(text: str) -> time:
    """Parse ``HH:MM`` or ``HH:MM:SS`` (schedule times in Australia/Sydney)."""
    parts = text.split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() and len(p) == 2 for p in parts):
        raise ValueError(f"time must be HH:MM or HH:MM:SS, got {text!r}")
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    return time(h, m, s)
