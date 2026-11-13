"""Ledger schema, mutability rules and audit log (§12), on SQLite and Postgres."""

from __future__ import annotations

import importlib.util
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from tests.conftest import REPO, alembic_config
from trader.enums import ParcelSource, RunState
from trader.ledger import (
    INSERT_ONLY_TABLES,
    MUTABLE_COLUMNS,
    AuditLog,
    Base,
    Flag,
    ImmutableRowError,
    Parcel,
    Run,
    install_mutability_guard,
    update_mutable,
    write_audit,
)

SPEC_TABLES = {
    "instruments", "calendar", "events", "corporate_actions", "runs", "signals",
    "shadow_signals", "strategy_state", "plans", "plan_lines", "order_intents", "broker_orders",
    "fills", "parcels", "disposals", "dividends", "cash_ledger", "positions_eod", "nav_eod",
    "recon", "vetoes", "flags", "alerts", "classifier_outputs", "trials", "config_versions",
    "valuations_2027", "audit_log",
}  # fmt: skip
TS = datetime(2026, 11, 13, 8, 0, tzinfo=UTC)


def _migration(name: str) -> ModuleType:
    path = next((REPO / "migrations" / "versions").glob(f"{name}_*.py"))
    spec = importlib.util.spec_from_file_location(f"mig_{name}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(**kw: object) -> Run:
    base: dict[str, object] = dict(
        user="a",
        decision_date=date(2026, 11, 13),
        execution_date=date(2026, 11, 16),
        state=RunState.SCHEDULED,
        config_hash="c" * 64,
        git_sha="d" * 40,
        data_hashes={},
    )
    base.update(kw)
    return Run(**base)


def test_models_cover_every_spec_table() -> None:
    assert set(Base.metadata.tables) == SPEC_TABLES


def test_migrations_create_every_table_sqlite(sqlite_engine) -> None:  # type: ignore[no-untyped-def]
    assert set(inspect(sqlite_engine).get_table_names()) >= SPEC_TABLES


def test_migration_matches_models_no_autogen_diff(sqlite_engine) -> None:  # type: ignore[no-untyped-def]
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    with sqlite_engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []


def test_migrations_are_forward_only() -> None:
    for p in sorted((REPO / "migrations" / "versions").glob("0*.py")):
        mod = _migration(p.name.split("_")[0])
        with pytest.raises(RuntimeError, match="forward-only"):
            mod.downgrade()


def test_grant_migration_matches_mutability_rules() -> None:
    m = _migration("0002")
    assert set(m.TABLES) == SPEC_TABLES
    assert {t: set(c) for t, c in m.MUTABLE.items()} == {
        t: set(c) for t, c in MUTABLE_COLUMNS.items()
    }
    assert set(MUTABLE_COLUMNS) | INSERT_ONLY_TABLES == SPEC_TABLES


class TestMutabilityGuard:
    def test_allowed_update_writes_audit(self, sqlite_engine) -> None:  # type: ignore[no-untyped-def]
        with Session(sqlite_engine) as s:
            install_mutability_guard(s)
            r = _run()
            s.add(r)
            s.flush()
            update_mutable(s, r, "state", RunState.DATA_READY, actor="runner", reason="data ok")
            s.commit()
            rows = s.execute(select(AuditLog)).scalars().all()
        assert len(rows) == 1
        assert rows[0].action == "update:runs.state"
        assert rows[0].payload["old"] == "SCHEDULED"
        assert rows[0].payload["new"] == "DATA_READY"

    def test_insert_only_column_update_refused(self, sqlite_engine) -> None:  # type: ignore[no-untyped-def]
        with Session(sqlite_engine) as s:
            install_mutability_guard(s)
            r = _run()
            s.add(r)
            s.commit()
            r.config_hash = "e" * 64
            with pytest.raises(ImmutableRowError, match="runs.config_hash"):
                s.flush()
            with pytest.raises(ImmutableRowError):
                update_mutable(s, r, "git_sha", "x", actor="t", reason="t")

    def test_delete_refused(self, sqlite_engine) -> None:  # type: ignore[no-untyped-def]
        with Session(sqlite_engine) as s:
            install_mutability_guard(s)
            f = Flag(name="kill", value=False, actor="init", reason="seed", updated_at=TS)
            s.add(f)
            s.commit()
            s.delete(f)
            with pytest.raises(ImmutableRowError, match="deletes"):
                s.flush()

    def test_flags_fully_mutable_parcels_qty_open_only(self, sqlite_engine) -> None:  # type: ignore[no-untyped-def]
        with Session(sqlite_engine) as s:
            install_mutability_guard(s)
            f = Flag(name="kill", value=False, actor="init", reason="seed", updated_at=TS)
            p = Parcel(
                symbol="BHP",
                acquired_at=TS,
                qty_original=100,
                qty_open=100,
                cost_base=Decimal("5961.0000"),
                source=ParcelSource.FILL,
            )
            s.add_all([f, p])
            s.commit()
            update_mutable(s, f, "value", True, actor="user-a", reason="/kill")
            update_mutable(s, f, "reason", "/kill", actor="user-a", reason="/kill")
            update_mutable(s, p, "qty_open", 40, actor="runner", reason="sale")
            s.commit()
            p.cost_base = Decimal(1)
            with pytest.raises(ImmutableRowError):
                s.flush()


# ---------------------------------------------------------------------------
# Postgres: real roles and grants (skipped without TRADER_TEST_PG_URL)
# ---------------------------------------------------------------------------


@pytest.mark.postgres
class TestPostgres:
    ROLE = "trader_test_app"

    def _migrate(self, url: str) -> None:
        eng = create_engine(url)
        with eng.begin() as conn:
            command.upgrade(alembic_config(conn, x=[f"app_role={self.ROLE}"]), "head")
        eng.dispose()

    def test_alembic_upgrade_head_postgres(self, pg_url: str) -> None:
        self._migrate(pg_url)
        eng = create_engine(pg_url)
        assert set(inspect(eng).get_table_names()) >= SPEC_TABLES
        with eng.connect() as c:
            assert c.execute(text("select version_num from alembic_version")).scalar() == "0004"
            assert c.execute(text("select count(*) from calendar")).scalar() == 426
        eng.dispose()

    def test_audit_log_insert_only_for_app_role(self, pg_url: str) -> None:
        self._migrate(pg_url)
        eng = create_engine(pg_url)
        with eng.connect() as c:
            c.execute(text(f"GRANT {self.ROLE} TO CURRENT_USER"))
            c.commit()
        with Session(eng) as s:
            s.execute(text(f"SET ROLE {self.ROLE}"))
            write_audit(s, actor="t", action="test", payload={"k": 1})  # INSERT works
            s.flush()
            with pytest.raises(DBAPIError, match="permission denied"):
                s.execute(text("SELECT * FROM audit_log"))
            s.rollback()
            s.execute(text(f"SET ROLE {self.ROLE}"))
            with pytest.raises(DBAPIError, match="permission denied"):
                s.execute(text("UPDATE audit_log SET actor = 'x'"))
        eng.dispose()

    def test_audit_log_append_only_even_for_owner(self, pg_url: str) -> None:
        self._migrate(pg_url)
        eng = create_engine(pg_url)
        with Session(eng) as s:
            write_audit(s, actor="t", action="test", payload={})
            s.commit()
            for stmt in (
                "UPDATE audit_log SET actor='x'",
                "DELETE FROM audit_log",
                "TRUNCATE audit_log",
            ):
                with pytest.raises(DBAPIError, match="append-only"):
                    s.execute(text(stmt))
                s.rollback()
        eng.dispose()

    def test_column_grants_enforce_mutability(self, pg_url: str) -> None:
        self._migrate(pg_url)
        eng = create_engine(pg_url)
        with eng.connect() as c:
            c.execute(text(f"GRANT {self.ROLE} TO CURRENT_USER"))
            c.commit()
        with Session(eng) as s:
            s.execute(text(f"SET ROLE {self.ROLE}"))
            s.add(_run())
            s.flush()
            s.execute(text("UPDATE runs SET state = 'DATA_READY'"))  # allowed column
            with pytest.raises(DBAPIError, match="permission denied"):
                s.execute(text("UPDATE runs SET config_hash = 'x'"))
            s.rollback()
            s.execute(text(f"SET ROLE {self.ROLE}"))
            with pytest.raises(DBAPIError, match="permission denied"):
                s.execute(text("DELETE FROM calendar"))
        eng.dispose()

    def test_SYS_13_SYS_14_numeric_and_timestamptz_types_postgres(self, pg_url: str) -> None:
        """SYS-13/SYS-14 on Postgres: money is NUMERIC(18,4), timestamps timestamptz."""
        self._migrate(pg_url)
        eng = create_engine(pg_url)
        with eng.connect() as c:
            rows = c.execute(
                text(
                    "select table_name, column_name, data_type, numeric_precision, numeric_scale "
                    "from information_schema.columns where table_schema='public'"
                )
            ).all()
        eng.dispose()
        types = {(r[0], r[1]): r[2:] for r in rows}
        assert types[("cash_ledger", "amount")] == ("numeric", 18, 4)
        assert types[("fills", "price")] == ("numeric", 18, 4)
        assert all(t[0] != "timestamp without time zone" for t in types.values())
        assert types[("audit_log", "ts")][0] == "timestamp with time zone"


def test_postgres_marker_documented() -> None:
    text_ = Path(REPO / "pyproject.toml").read_text()
    assert "postgres:" in text_
