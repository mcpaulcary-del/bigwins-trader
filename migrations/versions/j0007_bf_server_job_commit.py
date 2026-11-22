"""Server jobs carry the approved commit and the trader's signature (BF-D48)

Revision ID: j0007
Revises: j0006
Create Date: 2026-11-22

``bf_server_jobs.commit``: the exact 40-hex commit the owner approved (update) or the
commit the worker recorded before the last update (rollback); ``bf_server_jobs.sig``:
HMAC of (id, action, commit, force, requested-at) with the trader / host-worker key. The
root worker runs only signed jobs, and an update only to that exact commit. Existing
rows get NULL (never run: unsigned). Skipped where the code already created them.
Forward-only (section 12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0007"
down_revision: str | None = "j0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def upgrade() -> None:
    _require_db("journal")
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("bf_server_jobs")}
    with op.batch_alter_table("bf_server_jobs") as b:
        if "commit" not in cols:
            b.add_column(sa.Column("commit", sa.String(40)))
        if "sig" not in cols:
            b.add_column(sa.Column("sig", sa.String(64)))


def downgrade() -> None:
    raise NotImplementedError("forward-only (section 12)")
