"""seed the calendar table: 1 Nov 2026 - 31 Dec 2027 (spec section 5)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-13

Holidays and half-days come only from this table (OPS-05). Source: spec v1.2
section 5 ("Trading calendar", from ASX). Weekends are closed; listed closures
are closed; listed early closes close at 14:10; every other weekday closes at
16:10 (closing single price auction). All times Australia/Sydney.

The table must be reloaded every year from the ASX calendar and ASX Online
notices (section 17) with a new migration.
Forward-only (spec §12): downgrade is not supported.
"""

from collections.abc import Sequence
from datetime import date, time, timedelta

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_START = date(2026, 11, 1)
SEED_END = date(2027, 12, 31)
NORMAL_CLOSE = time(16, 10)
EARLY_CLOSE = time(14, 10)

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
    {
        date(2026, 12, 24),
        date(2026, 12, 31),
        date(2027, 12, 24),
        date(2027, 12, 31),
    }
)
# Explicitly open although near a public holiday: Mon 26 Apr 2027 (Anzac Day
# substitute is a trading day). It is an ordinary weekday below.


def rows() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    d = SEED_START
    while d <= SEED_END:
        if d.weekday() >= 5 or d in CLOSED:
            out.append({"date": d, "is_trading": False, "close_time": None})
        else:
            close = EARLY_CLOSE if d in EARLY_CLOSE_DAYS else NORMAL_CLOSE
            out.append({"date": d, "is_trading": True, "close_time": close})
        d += timedelta(days=1)
    return out


def upgrade() -> None:
    calendar = sa.table(
        "calendar",
        sa.column("date", sa.Date()),
        sa.column("is_trading", sa.Boolean()),
        sa.column("close_time", sa.Time()),
    )
    op.bulk_insert(calendar, rows())


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12): restore from backup instead")
