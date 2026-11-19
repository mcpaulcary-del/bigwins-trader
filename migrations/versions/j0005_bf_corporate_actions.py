"""Corporate actions in the journal: ``bf_corporate_actions``, ``bf_identity.ratio``
(BF-D23, BF-D25)

Revision ID: j0005
Revises: j0004
Create Date: 2026-11-19

``bf_corporate_actions``: append-only bookings of dividends, specials, capital returns,
demergers, in-specie distributions, splits, disposals and cash in lieu per book, from
IBKR's Activity Flex records (broker books) or the vendor + record calendar (simulated
books); unique on (book, key) so a re-read statement books nothing twice.
``bf_identity.ratio``: new shares per old share of a code change (NULL = 1, every
existing row). Skipped where the code already created them (a stamped journal).
Forward-only (§12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0005"
down_revision: str | None = "j0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def upgrade() -> None:
    _require_db("journal")
    insp = sa.inspect(op.get_bind())
    if "ratio" not in {c["name"] for c in insp.get_columns("bf_identity")}:
        with op.batch_alter_table("bf_identity") as b:
            b.add_column(sa.Column("ratio", sa.Numeric(18, 8)))
    if "bf_corporate_actions" in set(insp.get_table_names()):
        return
    op.create_table(
        "bf_corporate_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("book", sa.String(48), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("code", sa.String(24), nullable=False, index=True),
        sa.Column("ex_date", sa.Date()),
        sa.Column("pay_date", sa.Date()),
        sa.Column("held", sa.Integer(), nullable=False),
        sa.Column("cash", sa.Numeric(18, 4), nullable=False),
        sa.Column("income", sa.Numeric(18, 4), nullable=False),
        sa.Column("franked_pct", sa.Numeric(7, 4)),
        sa.Column("franking_credit", sa.Numeric(18, 4), nullable=False),
        sa.Column("cost_reduction", sa.Numeric(18, 4), nullable=False),
        sa.Column("qty_change", sa.Integer(), nullable=False),
        sa.Column("new_code", sa.String(24)),
        sa.Column("new_shares", sa.Integer(), nullable=False),
        sa.Column("child_cost", sa.Numeric(18, 4)),
        sa.Column("cost_moved_pct", sa.Numeric(9, 6)),
        sa.Column("ratio", sa.Numeric(18, 8)),
        sa.Column("source", sa.String(12), nullable=False),
        sa.Column("expected_key", sa.String(120)),
        sa.Column("tax_class", sa.String(16), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(200), nullable=False),
        sa.UniqueConstraint("book", "key", name="uq_bf_corporate_actions_book_key"),
    )


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12)")
