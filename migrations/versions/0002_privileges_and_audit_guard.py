"""privileges for the app role (mutability rules) and audit_log append-only guard

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-13

Postgres only (no-op on SQLite, which has no roles).

* The app role (``-x app_role=...`` / ``TRADER_DB_APP_ROLE``, default
  ``trader_app``) gets SELECT + INSERT on every table, UPDATE only on the
  columns §12 allows to change, and no DELETE or TRUNCATE anywhere.
* ``audit_log``: the app role has INSERT only (§12). A trigger also rejects
  UPDATE, DELETE and TRUNCATE for every role, including the owner.

Any later migration that adds a table MUST add its grants the same way.
Forward-only (spec §12): downgrade is not supported.
"""

import os
import re
from collections.abc import Sequence

from alembic import context, op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Snapshot of the schema as of 0001 (migrations never import app code).
TABLES = (
    "alerts",
    "audit_log",
    "broker_orders",
    "calendar",
    "cash_ledger",
    "classifier_outputs",
    "config_versions",
    "corporate_actions",
    "disposals",
    "dividends",
    "events",
    "fills",
    "flags",
    "instruments",
    "nav_eod",
    "order_intents",
    "parcels",
    "plan_lines",
    "plans",
    "positions_eod",
    "recon",
    "runs",
    "shadow_signals",
    "signals",
    "strategy_state",
    "trials",
    "valuations_2027",
    "vetoes",
)
# §12: only these columns may be updated ("*" = every column).
MUTABLE = {
    "runs": ("state",),
    "order_intents": ("status",),
    "broker_orders": ("status",),
    "parcels": ("qty_open",),
    "flags": ("*",),
}
APPEND_ONLY_INSERT_ONLY = "audit_log"

_ROLE_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def _app_role() -> str:
    role: str = (
        context.get_x_argument(as_dictionary=True).get("app_role")
        or os.environ.get("TRADER_DB_APP_ROLE")
        or "trader_app"
    )
    if not _ROLE_RE.fullmatch(role):
        raise ValueError(f"invalid app role name {role!r}")
    return role


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    role = _app_role()
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                CREATE ROLE {role} NOLOGIN;
            END IF;
        END
        $$;
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
    for t in TABLES:
        op.execute(f'REVOKE ALL ON TABLE "{t}" FROM {role}')
        if t == APPEND_ONLY_INSERT_ONLY:
            op.execute(f'GRANT INSERT ON TABLE "{t}" TO {role}')
            continue
        op.execute(f'GRANT SELECT, INSERT ON TABLE "{t}" TO {role}')
        cols = MUTABLE.get(t)
        if cols == ("*",):
            op.execute(f'GRANT UPDATE ON TABLE "{t}" TO {role}')
        elif cols:
            collist = ", ".join(f'"{c}"' for c in cols)
            op.execute(f'GRANT UPDATE ({collist}) ON TABLE "{t}" TO {role}')
    op.execute(f"GRANT SELECT ON TABLE alembic_version TO {role}")
    op.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {role}")

    op.execute(
        """
        CREATE FUNCTION audit_log_append_only() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only (spec section 12): % refused', TG_OP;
        END
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER audit_log_no_update_delete BEFORE UPDATE OR DELETE ON audit_log "
        "FOR EACH ROW EXECUTE FUNCTION audit_log_append_only()"
    )
    op.execute(
        "CREATE TRIGGER audit_log_no_truncate BEFORE TRUNCATE ON audit_log "
        "FOR EACH STATEMENT EXECUTE FUNCTION audit_log_append_only()"
    )


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12): restore from backup instead")
