"""v2.10 re-baseline of the ledger database (spec v2.10 §12)

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-13

Spec v2.10 splits each instance into ``market_<user>`` and
``ledger_<user>_paper`` / ``ledger_<user>_live`` (§12). This revision turns a
database built by 0001-0004 (v1.x, one database per user) into a v2.10 ledger:

* drops the tables of the withdrawn v1/v2.0 share strategy and the market
  tables that now live in ``market_<user>`` (calendar, events, instruments,
  corporate actions, dividends, trials);
* drops and recreates every ledger table whose v2.10 columns differ;
* keeps ``audit_log`` (and its append-only trigger) and ``config_versions``.

Fail closed: it refuses to run if any dropped table other than the seeded
``calendar`` / ``events`` holds a row, so no record can be lost (M0 was never
deployed; docs/DECISIONS.md L-01). Forward-only (§12).
"""

import os
import re
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = ("ledger",)
depends_on: str | Sequence[str] | None = None

# Dropped in foreign-key order. calendar/events hold only migration seed rows.
OLD_TABLES = (
    "signals",
    "shadow_signals",
    "disposals",
    "valuations_2027",
    "fills",
    "broker_orders",
    "order_intents",
    "plan_lines",
    "plans",
    "strategy_state",
    "positions_eod",
    "nav_eod",
    "recon",
    "vetoes",
    "flags",
    "alerts",
    "classifier_outputs",
    "trials",
    "dividends",
    "cash_ledger",
    "parcels",
    "corporate_actions",
    "events",
    "instruments",
    "calendar",
    "runs",
)
SEED_ONLY = ("calendar", "events")
# Every v2.10 ledger table (snapshot; migrations never import app code).
TABLES = (
    "acceptances",
    "alerts",
    "amit_adjustments",
    "audit_log",
    "benchmark_nav",
    "broker_orders",
    "capital_losses",
    "cash_ledger",
    "cashflow_expected",
    "config_versions",
    "disposals",
    "distributions_received",
    "fills",
    "flags",
    "franking_ledger",
    "kill_criteria",
    "nav_eod",
    "order_intents",
    "overrides",
    "parcels",
    "plan_lines",
    "plans",
    "positions_eod",
    "recon",
    "runs",
    "tranche_state",
    "valuations_2027",
    "vetoes",
)
# §12 mutable columns in the ledger ("*" = every column).
MUTABLE = {
    "runs": ("state",),
    "order_intents": ("status",),
    "broker_orders": ("status",),
    "parcels": ("qty_open",),
    "cashflow_expected": ("status",),
    "flags": ("*",),
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
    _require_db("ledger")
    bind = op.get_bind()
    for t in OLD_TABLES:
        if t in SEED_ONLY:
            continue
        n = bind.execute(sa.text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
        if n:
            raise RuntimeError(f"0005 refuses to drop {t}: it holds {n} rows (fail closed)")
    for t in OLD_TABLES:
        op.drop_table(t)
    op.create_table(
        "acceptances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.String(length=16), nullable=True),
        sa.Column("recorded_by", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_acceptances")),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column(
            "reason_code",
            sa.Enum(
                "DATA_STALE",
                "DATA_MISMATCH",
                "DATA_SPIKE",
                "DATA_RESTATED",
                "SINGLE_SOURCE",
                "TR_CHECK",
                "SYMBOL_HALTED",
                "RECON_BREAK",
                "KILL",
                "GATEWAY_DOWN",
                "TWOFA_MISSED",
                "PLAN_NOT_DELIVERED",
                "USER_VETO",
                "MIN_ORDER",
                "BAND",
                "CASH_SHORT",
                "SNAPSHOT_GAP",
                "SNAPSHOT_GAP_CONFIRMED",
                "NO_QUOTE",
                "ADV_LIMIT",
                "MAX_ORDER_VALUE",
                "MAX_ORDERS",
                "MAX_TURNOVER",
                "NO_SHORT",
                "IBKR_REJECT",
                "NOT_SENT",
                "NEEDS_REVIEW",
                "CORP_ACTION",
                "PENDING_FLEX",
                "CALENDAR_MISMATCH",
                "CLOCK_SKEW",
                "EARLY_CLOSE",
                "LICENCE",
                "DRAWDOWN_HALT",
                "TRACKING_HALT",
                "COST_HALT",
                "DIST_MISSING",
                "ACCOUNT_MODE_MISMATCH",
                "CANCEL_UNCONFIRMED",
                "DATA_BUDGET",
                "WITHDRAWAL",
                "FOREIGN_ORDER",
                "IDLE_CASH",
                name="reason_code",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("msg", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_table(
        "benchmark_nav",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("benchmark", sa.String(length=8), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("nav", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("units", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("drawdown", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.PrimaryKeyConstraint("date", "benchmark", "revision", name=op.f("pk_benchmark_nav")),
    )
    op.create_table(
        "capital_losses",
        sa.Column("income_year", sa.String(length=7), nullable=False),
        sa.Column("opening_balance", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("losses_in_year", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("applied_in_year", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("closing_balance", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("income_year", name=op.f("pk_capital_losses")),
    )
    op.create_table(
        "cash_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("settle_date", sa.Date(), nullable=False),
        sa.Column("ref", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_ledger")),
        sa.UniqueConstraint("external_id", name=op.f("uq_cash_ledger_external_id")),
    )
    op.create_table(
        "cashflow_expected",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("announced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "closed",
                "lapsed",
                name="cashflow_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cashflow_expected")),
    )
    op.create_table(
        "distributions_received",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("pay_date", sa.Date(), nullable=False),
        sa.Column("units", sa.BigInteger(), nullable=False),
        sa.Column("cash_aud", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("franking_credit_aud", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column(
            "components",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("withholding", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("holding_period_ok", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_distributions_received")),
    )
    op.create_table(
        "flags",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("pk_flags")),
    )
    op.create_table(
        "kill_criteria",
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("criterion", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("tripped", sa.Boolean(), nullable=False),
        sa.Column("owner_note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("month", "criterion", name=op.f("pk_kill_criteria")),
    )
    op.create_table(
        "nav_eod",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("nav", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("unmanaged_value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("cash_total", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("cash_settled", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("distributions_receivable", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("pending_surplus", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("net_flow", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("committed_capital", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("sizing_nav", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("units", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("peak_unit_price", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.Column("drawdown", sa.Numeric(precision=30, scale=12), nullable=False),
        sa.PrimaryKeyConstraint("date", "revision", name=op.f("pk_nav_eod")),
    )
    op.create_table(
        "overrides",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=True),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_overrides")),
    )
    op.create_table(
        "parcels",
        sa.Column("parcel_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("qty_original", sa.BigInteger(), nullable=False),
        sa.Column("qty_open", sa.BigInteger(), nullable=False),
        sa.Column("cost_base", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("aud_rate", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("rate_source", sa.String(length=64), nullable=False),
        sa.Column("managed", sa.Boolean(), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "fill",
                "init",
                "corp_action",
                "manual",
                "recovered",
                name="parcel_source",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "qty_open >= 0 AND qty_open <= qty_original", name=op.f("ck_parcels_qty_open_range")
        ),
        sa.PrimaryKeyConstraint("parcel_id", name=op.f("pk_parcels")),
    )
    op.create_table(
        "positions_eod",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("qty", sa.BigInteger(), nullable=False),
        sa.Column("unmanaged_qty", sa.BigInteger(), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("stale_price", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("date", "symbol", "revision", name=op.f("pk_positions_eod")),
    )
    op.create_table(
        "recon",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("check", sa.String(length=16), nullable=False),
        sa.Column("item", sa.String(length=64), nullable=False),
        sa.Column("ledger_value", sa.Text(), nullable=True),
        sa.Column("broker_value", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=8), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("date", "check", "item", name=op.f("pk_recon")),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "SCHEDULED",
                "DATA_READY",
                "PLANNED",
                "APPROVED",
                "SUBMITTED",
                "FILLED",
                "PARTIAL",
                "NONE",
                "RECONCILED",
                "SKIPPED",
                "HALTED_FOR_DAY",
                "HALTED_INTEGRITY",
                "HALTED_BUYS",
                "KILLED",
                name="run_state",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "reason_code",
            sa.Enum(
                "DATA_STALE",
                "DATA_MISMATCH",
                "DATA_SPIKE",
                "DATA_RESTATED",
                "SINGLE_SOURCE",
                "TR_CHECK",
                "SYMBOL_HALTED",
                "RECON_BREAK",
                "KILL",
                "GATEWAY_DOWN",
                "TWOFA_MISSED",
                "PLAN_NOT_DELIVERED",
                "USER_VETO",
                "MIN_ORDER",
                "BAND",
                "CASH_SHORT",
                "SNAPSHOT_GAP",
                "SNAPSHOT_GAP_CONFIRMED",
                "NO_QUOTE",
                "ADV_LIMIT",
                "MAX_ORDER_VALUE",
                "MAX_ORDERS",
                "MAX_TURNOVER",
                "NO_SHORT",
                "IBKR_REJECT",
                "NOT_SENT",
                "NEEDS_REVIEW",
                "CORP_ACTION",
                "PENDING_FLEX",
                "CALENDAR_MISMATCH",
                "CLOCK_SKEW",
                "EARLY_CLOSE",
                "LICENCE",
                "DRAWDOWN_HALT",
                "TRACKING_HALT",
                "COST_HALT",
                "DIST_MISSING",
                "ACCOUNT_MODE_MISMATCH",
                "CANCEL_UNCONFIRMED",
                "DATA_BUDGET",
                "WITHDRAWAL",
                "FOREIGN_ORDER",
                "IDLE_CASH",
                name="reason_code",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("git_sha", sa.String(length=40), nullable=False),
        sa.Column("spec_hash", sa.String(length=64), nullable=False),
        sa.Column("card_set_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "data_hashes",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("digest_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runs")),
        sa.UniqueConstraint("date", name=op.f("uq_runs_date")),
    )
    op.create_table(
        "tranche_state",
        sa.Column("tranche", sa.Integer(), nullable=False),
        sa.Column("sleeve", sa.String(length=12), nullable=False),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("on", sa.Boolean(), nullable=False),
        sa.Column("votes", sa.Integer(), nullable=True),
        sa.Column("verdict_level", sa.String(length=16), nullable=False),
        sa.Column("drill", sa.Boolean(), nullable=False),
        sa.Column(
            "detail",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "votes IS NULL OR (votes >= 0 AND votes <= 3)",
            name=op.f("ck_tranche_state_votes_range"),
        ),
        sa.PrimaryKeyConstraint(
            "tranche", "sleeve", "evaluation_date", "revision", name=op.f("pk_tranche_state")
        ),
    )
    op.create_table(
        "vetoes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("execution_date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column(
            "side",
            sa.Enum(
                "BUY", "SELL", name="side", native_enum=False, create_constraint=True, length=32
            ),
            nullable=False,
        ),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vetoes")),
    )
    op.create_table(
        "amit_adjustments",
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("income_year", sa.String(length=7), nullable=False),
        sa.Column("cost_base_net_amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("source_statement", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parcel_id"], ["parcels.parcel_id"], name=op.f("fk_amit_adjustments_parcel_id_parcels")
        ),
        sa.PrimaryKeyConstraint("parcel_id", "income_year", name=op.f("pk_amit_adjustments")),
    )
    op.create_table(
        "franking_ledger",
        sa.Column("income_year", sa.String(length=7), nullable=False),
        sa.Column("distribution_id", sa.Integer(), nullable=False),
        sa.Column("credit", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("running_total", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("exemption_status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["distribution_id"],
            ["distributions_received.id"],
            name=op.f("fk_franking_ledger_distribution_id_distributions_received"),
        ),
        sa.PrimaryKeyConstraint("income_year", "distribution_id", name=op.f("pk_franking_ledger")),
    )
    op.create_table(
        "order_intents",
        sa.Column("client_order_id", sa.String(length=80), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column(
            "side",
            sa.Enum(
                "BUY", "SELL", name="side", native_enum=False, create_constraint=True, length=32
            ),
            nullable=False,
        ),
        sa.Column("qty", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "transition",
                "top-up",
                "band",
                "withdrawal",
                "canary",
                name="plan_kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("carried_from", sa.Date(), nullable=True),
        sa.Column(
            "tranche_ids",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("ref_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("limit_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "reason_code",
            sa.Enum(
                "DATA_STALE",
                "DATA_MISMATCH",
                "DATA_SPIKE",
                "DATA_RESTATED",
                "SINGLE_SOURCE",
                "TR_CHECK",
                "SYMBOL_HALTED",
                "RECON_BREAK",
                "KILL",
                "GATEWAY_DOWN",
                "TWOFA_MISSED",
                "PLAN_NOT_DELIVERED",
                "USER_VETO",
                "MIN_ORDER",
                "BAND",
                "CASH_SHORT",
                "SNAPSHOT_GAP",
                "SNAPSHOT_GAP_CONFIRMED",
                "NO_QUOTE",
                "ADV_LIMIT",
                "MAX_ORDER_VALUE",
                "MAX_ORDERS",
                "MAX_TURNOVER",
                "NO_SHORT",
                "IBKR_REJECT",
                "NOT_SENT",
                "NEEDS_REVIEW",
                "CORP_ACTION",
                "PENDING_FLEX",
                "CALENDAR_MISMATCH",
                "CLOCK_SKEW",
                "EARLY_CLOSE",
                "LICENCE",
                "DRAWDOWN_HALT",
                "TRACKING_HALT",
                "COST_HALT",
                "DIST_MISSING",
                "ACCOUNT_MODE_MISMATCH",
                "CANCEL_UNCONFIRMED",
                "DATA_BUDGET",
                "WITHDRAWAL",
                "FOREIGN_ORDER",
                "IDLE_CASH",
                name="reason_code",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column(
            "risk_decision",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("qty > 0", name=op.f("ck_order_intents_qty_positive")),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], name=op.f("fk_order_intents_run_id_runs")),
        sa.PrimaryKeyConstraint("client_order_id", name=op.f("pk_order_intents")),
    )
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], name=op.f("fk_plans_run_id_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plans")),
    )
    op.create_table(
        "valuations_2027",
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("close_30jun2027", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("eodhd_close", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("flex_mark", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("verdict", sa.String(length=16), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["parcel_id"], ["parcels.parcel_id"], name=op.f("fk_valuations_2027_parcel_id_parcels")
        ),
        sa.PrimaryKeyConstraint("parcel_id", name=op.f("pk_valuations_2027")),
    )
    op.create_table(
        "broker_orders",
        sa.Column("perm_id", sa.String(length=32), nullable=False),
        sa.Column("client_order_id", sa.String(length=80), nullable=True),
        sa.Column("broker_order_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_order_id"],
            ["order_intents.client_order_id"],
            name=op.f("fk_broker_orders_client_order_id_order_intents"),
        ),
        sa.PrimaryKeyConstraint("perm_id", name=op.f("pk_broker_orders")),
    )
    op.create_table(
        "plan_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "transition",
                "top-up",
                "band",
                "withdrawal",
                "canary",
                name="plan_kind",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("carried_from", sa.Date(), nullable=True),
        sa.Column("drill", sa.Boolean(), nullable=False),
        sa.Column("target_weight", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("target_qty", sa.BigInteger(), nullable=False),
        sa.Column(
            "reasons",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], name=op.f("fk_plan_lines_plan_id_plans")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_lines")),
    )
    op.create_table(
        "fills",
        sa.Column("exec_id", sa.String(length=64), nullable=False),
        sa.Column("perm_id", sa.String(length=32), nullable=True),
        sa.Column("client_order_id", sa.String(length=80), nullable=True),
        sa.Column("symbol", sa.String(length=12), nullable=False),
        sa.Column(
            "side",
            sa.Enum(
                "BUY", "SELL", name="side", native_enum=False, create_constraint=True, length=32
            ),
            nullable=False,
        ),
        sa.Column("qty", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("commission", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("gst", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settle_date", sa.Date(), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "api",
                "flex",
                "manual",
                "recovered",
                name="fill_source",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.CheckConstraint("qty > 0", name=op.f("ck_fills_qty_positive")),
        sa.ForeignKeyConstraint(
            ["perm_id"], ["broker_orders.perm_id"], name=op.f("fk_fills_perm_id_broker_orders")
        ),
        sa.PrimaryKeyConstraint("exec_id", name=op.f("pk_fills")),
    )
    op.create_table(
        "disposals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("exec_id", sa.String(length=64), nullable=True),
        sa.Column("qty", sa.BigInteger(), nullable=False),
        sa.Column("proceeds", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("cost_base", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("indexed_cost_base", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("gain_pre_july_2027", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("gain_post_july_2027", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("discount_applied", sa.Boolean(), nullable=False),
        sa.Column("held_days", sa.Integer(), nullable=False),
        sa.Column("tax_regime", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["exec_id"], ["fills.exec_id"], name=op.f("fk_disposals_exec_id_fills")
        ),
        sa.ForeignKeyConstraint(
            ["parcel_id"], ["parcels.parcel_id"], name=op.f("fk_disposals_parcel_id_parcels")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_disposals")),
    )
    # ### end Alembic commands ###
    if bind.dialect.name == "postgresql":
        _grant(TABLES)


def downgrade() -> None:
    raise RuntimeError("forward-only migrations (spec §12): restore from backup instead")
