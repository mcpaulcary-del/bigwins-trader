"""The phone app: ``bf_inbox``, ``bf_push_subs``, ``bf_app_state``, ``bf_server_jobs``
(BF-D39..BF-D42)

Revision ID: j0006
Revises: j0005
Create Date: 2026-11-22

``bf_inbox``: every message the trader sends to the owner's app (append-only; the app's
inbox and its Web Push record). ``bf_push_subs``: the Web Push subscriptions of the
owner's installed app (endpoint unique). ``bf_app_state``: small app state (alert
settings, the code lock-out, the host's status snapshot). ``bf_server_jobs``: server jobs
the owner asked for in the app (a fixed list of names), run by the host worker.
Skipped where the code already created them (a stamped journal). Forward-only (§12).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "j0006"
down_revision: str | None = "j0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def upgrade() -> None:
    _require_db("journal")
    have = set(sa.inspect(op.get_bind()).get_table_names())
    if "bf_inbox" not in have:
        op.create_table(
            "bf_inbox",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("kind", sa.String(16), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("link", sa.String(200), nullable=False),
            sa.Column("source", sa.String(64), nullable=False),
            sa.Column("push", sa.String(64), nullable=False),
        )
    if "bf_push_subs" not in have:
        op.create_table(
            "bf_push_subs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("endpoint", sa.String(512), nullable=False),
            sa.Column("p256dh", sa.String(200), nullable=False),
            sa.Column("auth", sa.String(64), nullable=False),
            sa.Column("login", sa.String(200), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("active", sa.Integer(), nullable=False),
            sa.Column("last_error", sa.String(200), nullable=False),
            sa.UniqueConstraint("endpoint", name="uq_bf_push_subs_endpoint"),
        )
    if "bf_app_state" not in have:
        op.create_table(
            "bf_app_state",
            sa.Column("key", sa.String(64), primary_key=True),
            sa.Column("value", sa.JSON(), nullable=False),
            sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        )
    if "bf_server_jobs" not in have:
        op.create_table(
            "bf_server_jobs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("action", sa.String(32), nullable=False),
            sa.Column("force", sa.Integer(), nullable=False),
            sa.Column("login", sa.String(200), nullable=False),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(16), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True)),
            sa.Column("finished_at", sa.DateTime(timezone=True)),
            sa.Column("result", sa.Text(), nullable=False),
        )


def downgrade() -> None:
    raise NotImplementedError("forward-only (section 12)")
