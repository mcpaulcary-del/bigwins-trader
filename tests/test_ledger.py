"""Ledger and market schemas, mutability rules and audit log (v2.10 §12), on SQLite
and Postgres."""

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

from tests.conftest import REPO, alembic_config, migrate
from trader.data.models import (
    EXTRA_MARKET_TABLES,
    MARKET_INSERT_ONLY_TABLES,
    MARKET_MUTABLE_COLUMNS,
    SPEC_MARKET_TABLES,
    Distribution,
    MarketAuditLog,
    MarketBase,
    RawBar,
    update_market_mutable,
)
from trader.enums import (
    CashflowStatus,
    DistributionSource,
    DistributionStatus,
    ParcelSource,
    RunState,
)
from trader.ledger import (
    INSERT_ONLY_TABLES,
    LEDGER_MUTABLE_COLUMNS,
    AuditLog,
    CashflowExpected,
    Flag,
    ImmutableRowError,
    LedgerBase,
    Parcel,
    Run,
    install_mutability_guard,
    update_mutable,
    write_audit,
)

Base = LedgerBase
SPEC_TABLES = {
    "runs", "tranche_state", "plans", "plan_lines", "order_intents", "broker_orders", "fills",
    "parcels", "disposals", "valuations_2027", "amit_adjustments", "distributions_received",
    "franking_ledger", "capital_losses", "cash_ledger", "positions_eod", "nav_eod",
    "benchmark_nav", "kill_criteria", "recon", "vetoes", "flags", "alerts", "overrides",
    "cashflow_expected", "acceptances", "config_versions", "audit_log",
}  # fmt: skip
WITHDRAWN_TABLES = {
    "signals", "shadow_signals", "strategy_state", "classifier_outputs", "events", "dividends",
    "instruments", "corporate_actions",
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
        date=date(2026, 11, 13),
        state=RunState.SCHEDULED,
        config_hash="c" * 64,
        git_sha="d" * 40,
        spec_hash="e" * 64,
        data_hashes={},
    )
    base.update(kw)
    return Run(**base)


def test_ledger_models_cover_every_spec_table() -> None:
    assert set(Base.metadata.tables) == SPEC_TABLES
    assert not WITHDRAWN_TABLES & set(Base.metadata.tables)


def test_market_models_cover_every_spec_table() -> None:
    assert set(MarketBase.metadata.tables) == SPEC_MARKET_TABLES | EXTRA_MARKET_TABLES


def test_migrations_create_every_table_sqlite(sqlite_engine, market_engine) -> None:  # type: ignore[no-untyped-def]
    names = set(inspect(sqlite_engine).get_table_names())
    assert names - {"alembic_version"} == SPEC_TABLES
    market = set(inspect(market_engine).get_table_names()) - {"alembic_version"}
    assert market == SPEC_MARKET_TABLES | EXTRA_MARKET_TABLES


@pytest.mark.parametrize(
    ("fixture", "base"), [("sqlite_engine", LedgerBase), ("market_engine", MarketBase)]
)
def test_migration_matches_models_no_autogen_diff(request, fixture, base) -> None:  # type: ignore[no-untyped-def]
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    engine = request.getfixturevalue(fixture)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), base.metadata)
    assert diff == []


def test_migrations_are_forward_only() -> None:
    for p in sorted((REPO / "migrations" / "versions").glob("*.py")):
        mod = _migration(p.name.split("_")[0])
        with pytest.raises(RuntimeError, match="forward-only"):
            mod.downgrade()


def test_history_is_not_rewritten() -> None:
    """The v1.x revisions 0001-0004 stay; v2.10 adds 0005 (ledger) and m0001/m0002
    (market); B-fast adds the journal branch j0001/j0002 (BF-D9, BF-D16)."""
    names = sorted(p.name.split("_")[0] for p in (REPO / "migrations" / "versions").glob("*.py"))
    assert names == ["0001", "0002", "0003", "0004", "0005", "j0001", "j0002", "m0001", "m0002"]
    assert _migration("0005").down_revision == "0004"
    assert _migration("m0001").down_revision is None


def test_branch_refuses_the_wrong_database(tmp_path: Path) -> None:
    eng = create_engine(f"sqlite:///{tmp_path / 'x.db'}")
    with pytest.raises(RuntimeError, match="belongs to the market database"), eng.begin() as conn:
        command.upgrade(alembic_config(conn, db="ledger"), "market@head")
    eng.dispose()


def test_rebaseline_refuses_to_drop_rows(tmp_path: Path) -> None:
    """0005 fails closed if a v1 table it drops holds a record."""
    eng = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with eng.begin() as conn:
        command.upgrade(alembic_config(conn), "0004")
        conn.execute(
            text(
                "INSERT INTO trials (config_hash, period, metrics, created_at) "
                "VALUES ('h', 'p', '{}', '2026-11-13 00:00:00')"
            )
        )
    with pytest.raises(RuntimeError, match="refuses to drop trials"), eng.begin() as conn:
        command.upgrade(alembic_config(conn), "ledger@head")
    eng.dispose()


def test_grant_migrations_match_mutability_rules() -> None:
    m = _migration("0005")
    assert set(m.TABLES) == SPEC_TABLES
    assert {t: set(c) for t, c in m.MUTABLE.items()} == {
        t: set(c) for t, c in LEDGER_MUTABLE_COLUMNS.items()
    }
    assert set(LEDGER_MUTABLE_COLUMNS) | INSERT_ONLY_TABLES == SPEC_TABLES
    mm = _migration("m0001")
    assert set(mm.TABLES) == set(MarketBase.metadata.tables)
    assert {t: set(c) for t, c in mm.MUTABLE.items()} == {
        t: set(c) for t, c in MARKET_MUTABLE_COLUMNS.items()
    }
    assert {
        "distribution": frozenset({"status"}),
        "hypotheses": frozenset({"status", "result", "decision", "approver"}),
    } == MARKET_MUTABLE_COLUMNS
    assert set(MARKET_MUTABLE_COLUMNS) | MARKET_INSERT_ONLY_TABLES == set(
        MarketBase.metadata.tables
    )


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
            f = Flag(name="killed", value="false", actor="init", reason="seed", updated_at=TS)
            s.add(f)
            s.commit()
            s.delete(f)
            with pytest.raises(ImmutableRowError, match="deletes"):
                s.flush()

    def test_flags_fully_mutable_parcels_qty_open_only(self, sqlite_engine) -> None:  # type: ignore[no-untyped-def]
        with Session(sqlite_engine) as s:
            install_mutability_guard(s)
            f = Flag(name="killed", value="false", actor="init", reason="seed", updated_at=TS)
            p = Parcel(
                symbol="VAS",
                acquired_at=TS,
                qty_original=10,
                qty_open=10,
                cost_base=Decimal("1006.6000"),
                currency="AUD",
                aud_rate=Decimal(1),
                rate_source="AUD",
                managed=True,
                source=ParcelSource.FILL,
            )
            cf = CashflowExpected(
                announced_at=TS, amount=Decimal("-500"), status=CashflowStatus.OPEN, note=None
            )
            s.add_all([f, p, cf])
            s.commit()
            update_mutable(s, cf, "status", CashflowStatus.CLOSED, actor="runner", reason="flex")
            with pytest.raises(ImmutableRowError):
                update_mutable(s, cf, "amount", Decimal(1), actor="t", reason="t")
            update_mutable(s, f, "value", "true", actor="user-a", reason="/kill")
            update_mutable(s, f, "reason", "/kill", actor="user-a", reason="/kill")
            update_mutable(s, p, "qty_open", 4, actor="runner", reason="sale")
            s.commit()
            p.cost_base = Decimal(1)
            with pytest.raises(ImmutableRowError):
                s.flush()


class TestMarketMutability:
    """DAT-18: market rows are append-only; only distribution.status may change (§12)."""

    def test_DAT_18_market_update_rules_and_audit(self, market_engine) -> None:  # type: ignore[no-untyped-def]
        with Session(market_engine) as s:
            install_mutability_guard(s)
            d = Distribution(
                instrument_id=1,
                ex_date=date(2027, 1, 4),
                cash_amount=Decimal("0.912345"),
                status=DistributionStatus.ESTIMATED,
                source=DistributionSource.ISSUER,
                fetch_time=TS,
                components={},
            )
            bar = RawBar(
                instrument_id=1,
                trade_date=date(2026, 11, 12),
                source="eodhd",
                fetch_time=TS,
                close=Decimal("100.10"),
                file_hash="f" * 64,
                licensee="a",
            )
            s.add_all([d, bar])
            s.commit()
            update_market_mutable(
                s, d, "status", DistributionStatus.FINAL, actor="a", reason="finalised"
            )
            s.commit()
            assert s.execute(select(MarketAuditLog)).scalars().one().action == (
                "update:distribution.status"
            )
            bar.close = Decimal("100.20")
            with pytest.raises(ImmutableRowError, match="raw_bar.close"):
                s.flush()
            s.rollback()
            s.delete(s.get(RawBar, (1, date(2026, 11, 12), "eodhd", TS)))
            with pytest.raises(ImmutableRowError, match="deletes"):
                s.flush()


# ---------------------------------------------------------------------------
# Postgres: real roles and grants (skipped without TRADER_TEST_PG_URL)
# ---------------------------------------------------------------------------


@pytest.mark.postgres
class TestPostgres:
    ROLE = "trader_test_app"

    def _migrate(self, url: str, db: str = "ledger") -> None:
        eng = create_engine(url)
        migrate(eng, db, x=[f"app_role={self.ROLE}"])
        eng.dispose()

    def test_alembic_upgrade_head_postgres(self, pg_url: str) -> None:
        self._migrate(pg_url)
        eng = create_engine(pg_url)
        assert set(inspect(eng).get_table_names()) - {"alembic_version"} == SPEC_TABLES
        with eng.connect() as c:
            assert c.execute(text("select version_num from alembic_version")).scalar() == "0005"
        eng.dispose()

    def test_market_upgrade_head_postgres(self, pg_url: str) -> None:
        self._migrate(pg_url, "market")
        eng = create_engine(pg_url)
        with eng.connect() as c:
            assert c.execute(text("select version_num from alembic_version")).scalar() == "m0002"
            assert c.execute(text("select count(*) from calendar")).scalar() == 426
            c.execute(text(f"GRANT {self.ROLE} TO CURRENT_USER"))
            c.commit()
        with Session(eng) as s:
            s.execute(text(f"SET ROLE {self.ROLE}"))
            s.execute(text("UPDATE distribution SET status = 'final'"))  # allowed column
            with pytest.raises(DBAPIError, match="permission denied"):
                s.execute(text("UPDATE raw_bar SET close = 1"))
            s.rollback()
            s.execute(text(f"SET ROLE {self.ROLE}"))
            with pytest.raises(DBAPIError, match="permission denied"):
                s.execute(text("DELETE FROM calendar"))
            s.rollback()
            s.execute(
                text(
                    "INSERT INTO audit_log (ts, actor, action, payload) "
                    "VALUES (now(), 'a', 'b', '{}')"
                )
            )
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
                s.execute(text("DELETE FROM flags"))
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
