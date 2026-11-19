"""B-fast order journal baseline (``bf_*`` tables as built by pieces 1-2, BF-D9)

Revision ID: j0001
Revises:
Create Date: 2026-11-19

Third branch of this script directory: the B-fast order journal (``trader.journal``),
-> ``alembic -x db=journal upgrade journal@head``. The tables are those
``trader.journal`` created with ``create_all`` before BF-D16 (``bf_safety`` without
``scope``). A journal created by that code is brought under Alembic with
``alembic -x db=journal stamp j0001`` and then upgraded; tables that already exist are
left as they are. Moving these tables into the v3.0 ledger is B4. Forward-only (§12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = ("journal",)
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def _ts() -> sa.DateTime:
    return sa.DateTime(timezone=True)


def upgrade() -> None:
    _require_db("journal")
    have = set(sa.inspect(op.get_bind()).get_table_names())
    if "bf_intents" not in have:
        op.create_table(
            "bf_intents",
            sa.Column("client_order_id", sa.String(96), primary_key=True),
            sa.Column("batch_id", sa.String(80), nullable=False, index=True),
            sa.Column("seq", sa.Integer(), nullable=False),
            sa.Column("line", sa.String(32), nullable=False),
            sa.Column("book", sa.String(48), nullable=False),
            sa.Column("decision_date", sa.Date(), nullable=False),
            sa.Column("entity", sa.String(24), nullable=False),
            sa.Column("side", sa.String(4), nullable=False),
            sa.Column("qty", sa.Integer(), nullable=False),
            sa.Column("order_type", sa.String(8), nullable=False),
            sa.Column("ref_price", sa.Numeric(18, 4), nullable=False),
            sa.Column("limit_price", sa.Numeric(18, 4), nullable=False),
            sa.Column("reason", sa.String(48), nullable=False),
            sa.Column("attempt", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(24), nullable=False),
            sa.Column("tv_med20", sa.Numeric(20, 2)),
            sa.Column("prev_close", sa.Numeric(18, 4)),
            sa.Column("flags", sa.JSON(), nullable=False),
            sa.Column("created_at", _ts(), nullable=False),
        )
    if "bf_batches" not in have:
        op.create_table(
            "bf_batches",
            sa.Column("batch_id", sa.String(80), primary_key=True),
            sa.Column("book", sa.String(48), nullable=False),
            sa.Column("decision_date", sa.Date(), nullable=False),
            sa.Column("digest", sa.String(64), nullable=False),
            sa.Column("approval_mode", sa.String(16), nullable=False),
            sa.Column("execution_date", sa.Date()),
            sa.Column("created_at", _ts(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
        )
    if "bf_approvals" not in have:
        op.create_table(
            "bf_approvals",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("batch_id", sa.String(80), nullable=False, index=True),
            sa.Column("seq", sa.Integer()),
            sa.Column("action", sa.String(8), nullable=False),
            sa.Column("actor", sa.String(64), nullable=False),
            sa.Column("at", _ts(), nullable=False),
        )
    if "bf_broker_orders" not in have:
        op.create_table(
            "bf_broker_orders",
            sa.Column("client_order_id", sa.String(96), primary_key=True),
            sa.Column("broker_order_id", sa.String(32)),
            sa.Column("perm_id", sa.String(32)),
            sa.Column("account", sa.String(16), nullable=False),
            sa.Column("status", sa.String(24), nullable=False),
            sa.Column("at", _ts(), nullable=False),
        )
    if "bf_fills" not in have:
        op.create_table(
            "bf_fills",
            sa.Column("exec_id", sa.String(64), primary_key=True),
            sa.Column("client_order_id", sa.String(96), index=True),
            sa.Column("book", sa.String(48), nullable=False),
            sa.Column("entity", sa.String(24), nullable=False),
            sa.Column("side", sa.String(4), nullable=False),
            sa.Column("qty", sa.Integer(), nullable=False),
            sa.Column("price", sa.Numeric(18, 4), nullable=False),
            sa.Column("commission", sa.Numeric(18, 4), nullable=False),
            sa.Column("executed_at", _ts(), nullable=False),
        )
    if "bf_cash" not in have:
        op.create_table(
            "bf_cash",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("book", sa.String(48), nullable=False),
            sa.Column("kind", sa.String(16), nullable=False),
            sa.Column("amount", sa.Numeric(18, 4), nullable=False),
            sa.Column("at", _ts(), nullable=False),
            sa.Column("note", sa.String(200), nullable=False),
        )
    if "bf_safety" not in have:
        op.create_table(
            "bf_safety",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("level", sa.String(24), nullable=False),
            sa.Column("reason", sa.String(200), nullable=False),
            sa.Column("actor", sa.String(64), nullable=False),
            sa.Column("at", _ts(), nullable=False),
        )
    if "bf_events" not in have:
        op.create_table(
            "bf_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("at", _ts(), nullable=False),
            sa.Column("kind", sa.String(24), nullable=False),
            sa.Column("ref", sa.String(96), nullable=False),
            sa.Column("from_status", sa.String(24)),
            sa.Column("to_status", sa.String(24)),
            sa.Column("detail", sa.JSON(), nullable=False),
        )


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12)")
