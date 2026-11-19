"""Per-book safety latch: ``bf_safety.scope`` (BF-D16)

Revision ID: j0002
Revises: j0001
Create Date: 2026-11-19

``ALTER TABLE bf_safety ADD COLUMN scope VARCHAR(40) NOT NULL DEFAULT ''``: every
existing row becomes the broker book's latch (``''``), which is what a journal without
the column meant (one journal-wide latch). Skipped when the column is already there
(a journal created by ``trader.journal`` after BF-D16). Forward-only (§12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0002"
down_revision: str | None = "j0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def upgrade() -> None:
    _require_db("journal")
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("bf_safety")}
    if "scope" in cols:
        return
    with op.batch_alter_table("bf_safety") as b:
        b.add_column(sa.Column("scope", sa.String(40), nullable=False, server_default=""))


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12)")
