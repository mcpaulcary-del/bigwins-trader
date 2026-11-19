"""Code changes in the order journal: ``bf_identity`` (BF-D19)

Revision ID: j0003
Revises: j0002
Create Date: 2026-11-19

A held code that stops trading and continues under another code (A7 duplicate rules,
e.g. HGO -> KAN in Nov 2026) is carried under the new code: append-only rows
``old_code -> new_code`` with status PROPOSED (applied, owner to confirm), CONFIRMED or
REJECTED; the latest row of an old code wins. Forward-only (§12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0003"
down_revision: str | None = "j0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def upgrade() -> None:
    _require_db("journal")
    if "bf_identity" in set(sa.inspect(op.get_bind()).get_table_names()):
        return  # created by trader.journal (stamped journal)
    op.create_table(
        "bf_identity",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("old_code", sa.String(24), nullable=False, index=True),
        sa.Column("new_code", sa.String(24), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("rule", sa.String(8), nullable=False),
        sa.Column("score", sa.Numeric(8, 6)),
        sa.Column("actor", sa.String(64), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(200), nullable=False),
    )


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12)")
