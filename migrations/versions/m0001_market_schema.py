"""market database schema (spec v2.10 §12, DAT-18)

Revision ID: m0001
Revises:
Create Date: 2026-11-13

Root of the ``market`` branch: ``market_<user>`` (one per user). Every table is
append-only and bitemporal; only ``distribution.status`` and, in
``hypotheses``, status / result / decision / approver may be updated (§12).
``audit_log`` is INSERT-only for the app role and append-only for every role.
Forward-only (§12).
"""

import os
import re
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

revision: str = "m0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = ("market",)
depends_on: str | Sequence[str] | None = None

TABLES = (
    "audit_log",
    "calendar",
    "cash_rate",
    "corp_action",
    "cpi",
    "distribution",
    "fx",
    "hypotheses",
    "instrument",
    "qc_event",
    "raw_bar",
    "spread_report",
    "tr_series",
    "trials",
    "validated_close",
    "vendor_call_log",
    "vendor_dividend",
)
MUTABLE = {
    "distribution": ("status",),
    "hypotheses": ("status", "result", "decision", "approver"),
}


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


def _require_db(expected: str) -> None:
    db = context.get_x_argument(as_dictionary=True).get("db") or context.config.attributes.get("db")
    if db != expected:
        raise RuntimeError(f"revision {revision} belongs to the {expected} database, not {db!r}")


def _grant(tables: tuple[str, ...]) -> None:
    """SELECT + INSERT for the app role, UPDATE only on §12 mutable columns,
    no DELETE/TRUNCATE; audit_log INSERT only."""
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
    for t in tables:
        op.execute(f'REVOKE ALL ON TABLE "{t}" FROM {role}')
        if t == "audit_log":
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


def upgrade() -> None:
    _require_db("market")
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_table(
        "calendar",
        sa.Column("venue", sa.String(length=8), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_trading", sa.Boolean(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "(is_trading AND close_time IS NOT NULL) OR (NOT is_trading AND close_time IS NULL)",
            name=op.f("ck_calendar_close_time_iff_trading"),
        ),
        sa.PrimaryKeyConstraint("venue", "date", "fetch_time", name=op.f("pk_calendar")),
    )
    op.create_table(
        "cash_rate",
        sa.Column("series", sa.String(length=16), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("series", "date", "fetch_time", name=op.f("pk_cash_rate")),
    )
    op.create_table(
        "corp_action",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("ratio", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_corp_action")),
    )
    op.create_table(
        "cpi",
        sa.Column("quarter", sa.String(length=7), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("quarter", "fetch_time", name=op.f("pk_cpi")),
    )
    op.create_table(
        "distribution",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("pay_date", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("cash_amount", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("franking_credit", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column(
            "components",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "expected",
                "estimated",
                "final",
                name="distribution_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.Enum(
                "issuer",
                "vendor_backfill",
                name="distribution_source",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'expected' AND cash_amount IS NULL) OR (status <> 'expected' AND cash_amount IS NOT NULL AND cash_amount >= 0)",
            name=op.f("ck_distribution_amount_iff_not_expected"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_distribution")),
    )
    op.create_table(
        "fx",
        sa.Column("series", sa.String(length=16), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("series", "date", "fetch_time", name=op.f("pk_fx")),
    )
    op.create_table(
        "hypotheses",
        sa.Column("card_id", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("card_hash", sa.String(length=64), nullable=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("card_content", sa.Text(), nullable=False),
        sa.Column("family", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "result",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("approver", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("card_id", name=op.f("pk_hypotheses")),
    )
    op.create_table(
        "instrument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column(
            "symbol_history",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("exchange", sa.String(length=12), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("issuer", sa.String(length=64), nullable=True),
        sa.Column("con_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "tick_rules",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("list_date", sa.Date(), nullable=True),
        sa.Column("delist_date", sa.Date(), nullable=True),
        sa.Column("delist_reason", sa.Text(), nullable=True),
        sa.Column("final_payout", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", "version", name=op.f("pk_instrument")),
    )
    op.create_table(
        "qc_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=True),
        sa.Column("trade_date", sa.Date(), nullable=True),
        sa.Column("check_id", sa.String(length=16), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column(
            "detail",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("override_by", sa.String(length=64), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_qc_event")),
    )
    op.create_table(
        "raw_bar",
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("high", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("low", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("close", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("vendor_adjusted_close", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("licensee", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint(
            "instrument_id", "trade_date", "source", "fetch_time", name=op.f("pk_raw_bar")
        ),
    )
    op.create_table(
        "spread_report",
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("spread", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint(
            "instrument_id", "month", "fetch_time", name=op.f("pk_spread_report")
        ),
    )
    op.create_table(
        "tr_series",
        sa.Column("build_id", sa.String(length=64), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tr_net", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("tr_gross", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("inputs_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("build_id", "instrument_id", "date", name=op.f("pk_tr_series")),
    )
    op.create_table(
        "trials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("card_id", sa.String(length=16), nullable=True),
        sa.Column("family", sa.String(length=8), nullable=False),
        sa.Column("trial_spec_id", sa.String(length=128), nullable=False),
        sa.Column("is_trial", sa.Boolean(), nullable=False),
        sa.Column("replication_kind", sa.String(length=32), nullable=False),
        sa.Column("card_hash", sa.String(length=64), nullable=True),
        sa.Column("data_hash", sa.String(length=64), nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("period", sa.String(length=32), nullable=False),
        sa.Column(
            "metrics",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("registered", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trials")),
    )
    op.create_table(
        "validated_close",
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("verdict", sa.String(length=16), nullable=False),
        sa.Column("backfill", sa.Boolean(), nullable=False),
        sa.Column("signals_ok", sa.Boolean(), nullable=False),
        sa.Column("override_id", sa.Integer(), nullable=True),
        sa.Column(
            "detail",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "instrument_id", "trade_date", "validated_at", name=op.f("pk_validated_close")
        ),
    )
    op.create_table(
        "vendor_call_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vendor", sa.String(length=16), nullable=False),
        sa.Column("endpoint", sa.String(length=64), nullable=False),
        sa.Column("gmt_date", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vendor_call_log")),
    )
    op.create_index(
        op.f("ix_vendor_call_log_gmt_date"), "vendor_call_log", ["gmt_date"], unique=False
    )
    op.create_table(
        "vendor_dividend",
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("fetch_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("unadjusted_value", sa.Numeric(precision=24, scale=10), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("licensee", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint(
            "instrument_id", "ex_date", "fetch_time", name=op.f("pk_vendor_dividend")
        ),
    )
    # ### end Alembic commands ###
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    _grant(TABLES)
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
