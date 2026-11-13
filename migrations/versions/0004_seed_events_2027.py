"""seed the events table with the known 2027 event dates (spec section 5)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-13

Conservative choices (see docs/DECISIONS.md):
* BHP half-year results: both 16 Feb and 23 Feb 2027 are seeded as estimates
  (sources disagree); more blackout days only block buys.
* CBA half-year results 10 Feb 2027: the spec says "No (verify)"; seeded as an
  estimate until confirmed, which widens the buy blackout.
* CSL results/AGM and RIO/FMG/WDS dates are "TBC" in the spec: not seeded.
* RBA decisions (day 2, 14:30): flag only, no blackout; symbol is NULL.
Forward-only (spec §12): downgrade is not supported.
"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SRC = "spec v1.2 section 5 (2026-11-13)"
EVENTS = [
    ("BHP", "QUARTERLY_REVIEW", date(2027, 1, 19), True, f"{SRC}: Dec-quarter operational review, about Tue 19 Jan 2027"),
    ("BHP", "RESULTS", date(2027, 2, 16), True, f"{SRC}: half-year results, about Tue 16 Feb 2027"),
    ("BHP", "RESULTS", date(2027, 2, 23), True, f"{SRC}: half-year results, alternative date 23 Feb 2027 (some sources)"),
    ("BHP", "EX_DIVIDEND", date(2027, 3, 4), True, f"{SRC}: interim ex-dividend, about Thu 4 Mar 2027 (no blackout)"),
    ("CBA", "RESULTS", date(2027, 2, 10), True, f"{SRC}: half-year results 10 Feb 2027 (spec: not estimate, but marked verify)"),
    (None, "RBA_DECISION", date(2027, 2, 9), True, f"{SRC}: RBA decision day 2 of 8-9 Feb 2027 (flag only)"),
    (None, "RBA_DECISION", date(2027, 3, 23), True, f"{SRC}: RBA decision day 2 of 22-23 Mar 2027 (flag only)"),
    (None, "RBA_DECISION", date(2027, 5, 4), True, f"{SRC}: RBA decision day 2 of 3-4 May 2027 (flag only)"),
]


def upgrade() -> None:
    events = sa.table(
        "events",
        sa.column("symbol", sa.String()),
        sa.column("type", sa.String()),
        sa.column("date", sa.Date()),
        sa.column("is_estimate", sa.Boolean()),
        sa.column("source", sa.Text()),
    )
    op.bulk_insert(
        events,
        [
            {"symbol": s, "type": t, "date": d, "is_estimate": e, "source": src}
            for s, t, d, e, src in EVENTS
        ],
    )


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12): restore from backup instead")
