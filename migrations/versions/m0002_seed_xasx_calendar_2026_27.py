"""seed the XASX calendar: 1 Nov 2026 - 31 Dec 2027 (spec v2.10 section 5)

Revision ID: m0002
Revises: m0001
Create Date: 2026-11-13

Session dates come only from the calendar table (OPS-05). Source: spec v2.10
section 5 "Trading calendar" (carried from v2.0, to be re-confirmed against the
ASX published calendar, open item P5). Mon 26 Apr 2027 is open: v2.10 marks it
[unverified]; the R37 primary-source check confirmed it is an ASX trading day.
Weekends are closed; listed closures are closed; listed early closes close at
14:10 (venue.XASX.early_close); every other weekday closes at 16:10, the start
of the closing single price auction (venue.XASX.closing_auction).

Rows carry their source and a fixed fetch time (bitemporal, DAT-18). Later
years are loaded with ``trader import calendar`` (insert-only, audited).
Forward-only (spec §12).
"""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

import sqlalchemy as sa
from alembic import context, op

revision: str = "m0002"
down_revision: str | None = "m0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VENUE = "XASX"
FETCH_TIME = datetime(2026, 11, 13, 0, 0, tzinfo=UTC)
SEED_START = date(2026, 11, 1)
SEED_END = date(2027, 12, 31)
NORMAL_CLOSE = time(16, 10)
EARLY_CLOSE = time(14, 10)
SOURCE = "spec v2.10 section 5 (from v2.0; re-confirm against the ASX published calendar, P5)"
SOURCE_0426 = SOURCE + "; 26 Apr 2027 open per R37 primary-source verification"

CLOSED = frozenset(
    {
        date(2026, 12, 25),  # Fri - Christmas Day
        date(2026, 12, 28),  # Mon - Boxing Day (substitute)
        date(2027, 1, 1),  # Fri - New Year's Day
        date(2027, 1, 26),  # Tue - Australia Day
        date(2027, 3, 26),  # Fri - Good Friday
        date(2027, 3, 29),  # Mon - Easter Monday
        date(2027, 6, 14),  # Mon - King's Birthday
        date(2027, 12, 27),  # Mon - Christmas Day (substitute)
        date(2027, 12, 28),  # Tue - Boxing Day (substitute)
    }
)
EARLY_CLOSE_DAYS = frozenset(
    {date(2026, 12, 24), date(2026, 12, 31), date(2027, 12, 24), date(2027, 12, 31)}
)


def rows() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    d = SEED_START
    while d <= SEED_END:
        src = SOURCE_0426 if d == date(2027, 4, 26) else SOURCE
        base = {"venue": VENUE, "date": d, "fetch_time": FETCH_TIME, "source": src}
        if d.weekday() >= 5 or d in CLOSED:
            out.append({**base, "is_trading": False, "close_time": None})
        else:
            close = EARLY_CLOSE if d in EARLY_CLOSE_DAYS else NORMAL_CLOSE
            out.append({**base, "is_trading": True, "close_time": close})
        d += timedelta(days=1)
    return out


def upgrade() -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != "market":
        raise RuntimeError(f"revision {revision} belongs to the market database, not {db!r}")
    calendar = sa.table(
        "calendar",
        sa.column("venue", sa.String()),
        sa.column("date", sa.Date()),
        sa.column("fetch_time", sa.DateTime(timezone=True)),
        sa.column("is_trading", sa.Boolean()),
        sa.column("close_time", sa.Time()),
        sa.column("source", sa.Text()),
    )
    op.bulk_insert(calendar, rows())


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12): restore from backup instead")
