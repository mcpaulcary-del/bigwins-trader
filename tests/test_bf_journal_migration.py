"""BF-D16 / BF-D9: the order journal's Alembic branch (``journal``) and the
``bf_safety.scope`` migration for journals created before the per-book latch."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from tests.conftest import alembic_config
from trader.journal import Journal, md
from trader.risk import SafetyLevel

T0 = datetime(2026, 11, 19, 5, 0, tzinfo=UTC)


def _upgrade(url: str, target: str) -> None:
    eng = create_engine(url)
    with eng.begin() as conn:
        command.upgrade(alembic_config(conn, db="journal"), target)
    eng.dispose()


def test_BF_D16_journal_head_matches_the_code_schema(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'j.db'}"
    _upgrade(url, "journal@head")
    eng = create_engine(url)
    with eng.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), md)
    assert diff == []
    eng.dispose()


def test_BF_D16_scope_migration_keeps_every_latch_as_the_broker_books(tmp_path: Path) -> None:
    """A journal from before BF-D16 (one journal-wide latch) gets ``scope`` = '' on every
    row: the latch it held stays the broker book's, and per-book latches then work."""
    url = f"sqlite:///{tmp_path / 'old.db'}"
    _upgrade(url, "j0001")
    eng = create_engine(url)
    assert "scope" not in {c["name"] for c in inspect(eng).get_columns("bf_safety")}
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO bf_safety (level, reason, actor, at) "
                "VALUES ('HALTED_BUYS', 'L11 stage 2', 'l11', '2026-11-18 11:00:00')"
            )
        )
    eng.dispose()
    _upgrade(url, "journal@head")
    eng = create_engine(url)
    cols = {c["name"]: c for c in inspect(eng).get_columns("bf_safety")}
    assert not cols["scope"]["nullable"]
    with eng.connect() as conn:
        assert [tuple(r) for r in conn.execute(text("SELECT scope, level FROM bf_safety"))] == [
            ("", "HALTED_BUYS")
        ]
    j = Journal(eng)
    assert j.safety_level() is SafetyLevel.HALTED_BUYS
    assert j.safety_level("EMG2_18_SIM") is SafetyLevel.NORMAL
    j.set_safety(SafetyLevel.KILLED, "own latch", "risk", T0, scope="EMG2_18_SIM")
    assert j.safety_level("EMG2_18_SIM") is SafetyLevel.KILLED
    assert j.safety_level() is SafetyLevel.HALTED_BUYS
    eng.dispose()


def test_BF_D16_journal_created_by_the_code_is_stamped_and_upgraded(tmp_path: Path) -> None:
    """A journal ``trader.journal`` created after BF-D16 already has the column:
    stamped at the baseline, the upgrade is a no-op and keeps its rows."""
    url = f"sqlite:///{tmp_path / 'new.db'}"
    eng = create_engine(url)
    j = Journal(eng)
    j.set_safety(SafetyLevel.PAUSED, "owner", "owner", T0)
    with eng.begin() as conn:
        command.stamp(alembic_config(conn, db="journal"), "j0001")
    eng.dispose()
    _upgrade(url, "journal@head")
    eng = create_engine(url)
    assert Journal(eng).safety_level() is SafetyLevel.PAUSED
    eng.dispose()


def test_BF_D16_journal_branch_refuses_the_ledger_database(tmp_path: Path) -> None:
    eng = create_engine(f"sqlite:///{tmp_path / 'x.db'}")
    with (
        pytest.raises(RuntimeError, match="belongs to the journal database"),
        eng.begin() as conn,
    ):
        command.upgrade(alembic_config(conn, db="ledger"), "journal@head")
    eng.dispose()


@pytest.mark.skipif(not os.environ.get("TRADER_TEST_PG_URL"), reason="TRADER_TEST_PG_URL not set")
def test_BF_D16_scope_migration_on_postgres() -> None:
    base = os.environ["TRADER_TEST_PG_URL"]
    name = f"bfj_{uuid.uuid4().hex[:8]}"
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f"CREATE DATABASE {name}"))
    url = base.rsplit("/", 1)[0] + "/" + name
    try:
        _upgrade(url, "j0001")
        eng = create_engine(url)
        with eng.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO bf_safety (level, reason, actor, at) "
                    "VALUES ('PAUSED', 'owner', 'owner', now())"
                )
            )
        eng.dispose()
        _upgrade(url, "journal@head")
        eng = create_engine(url)
        assert Journal(eng).safety_level() is SafetyLevel.PAUSED
        eng.dispose()
    finally:
        with admin.connect() as c:
            c.execute(text(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)"))
        admin.dispose()
