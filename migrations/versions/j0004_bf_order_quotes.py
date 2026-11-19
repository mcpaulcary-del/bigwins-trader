"""The broker's quote at each order: ``bf_order_quotes`` (BF-D22)

Revision ID: j0004
Revises: j0003
Create Date: 2026-11-19

Append-only rows: bid, ask, last and mid (``(bid + ask) / 2``, NULL without a usable
two-sided quote) taken from the broker just before each order is sent, so the realised
cost per trade can be measured against the mid at order time (AMENDMENT_adopt_rule_v3
"cost ratio"; report 94 s3.3 item 3). Orders sent before this revision have no row.
Forward-only (§12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0004"
down_revision: str | None = "j0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def upgrade() -> None:
    _require_db("journal")
    if "bf_order_quotes" in set(sa.inspect(op.get_bind()).get_table_names()):
        return  # created by trader.journal (stamped journal)
    op.create_table(
        "bf_order_quotes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_order_id", sa.String(96), nullable=False, index=True),
        sa.Column("book", sa.String(48), nullable=False),
        sa.Column("entity", sa.String(24), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("bid", sa.Numeric(18, 4)),
        sa.Column("ask", sa.Numeric(18, 4)),
        sa.Column("last", sa.Numeric(18, 4)),
        sa.Column("mid", sa.Numeric(18, 6)),
        sa.Column("quote_time", sa.DateTime(timezone=True)),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("note", sa.String(200), nullable=False),
    )


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12)")
