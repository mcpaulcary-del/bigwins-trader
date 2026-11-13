"""Shared fixtures. No test makes a network call; Postgres tests need
``TRADER_TEST_PG_URL`` (a local server) and are skipped otherwise."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from trader.config import sha256_bytes

REPO = Path(__file__).resolve().parent.parent
COMMON_PATH = REPO / "config" / "common.yaml"
USER_EXAMPLE = REPO / "config" / "examples" / "user.example.yaml"
FAKE_SHA = "1234567890abcdef1234567890abcdef12345678"


def alembic_config(
    connection: object | None = None, x: list[str] | None = None, db: str = "ledger"
) -> Config:
    cfg = Config(str(REPO / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO / "migrations"))
    cfg.attributes["configure_logger"] = False
    cfg.attributes["db"] = db
    if connection is not None:
        cfg.attributes["connection"] = connection
    import argparse

    cfg.cmd_opts = argparse.Namespace(x=x or [])
    return cfg


def migrate(engine: Engine, db: str, x: list[str] | None = None) -> None:
    with engine.begin() as conn:
        command.upgrade(alembic_config(conn, x=x, db=db), f"{db}@head")


def _no_floats(v: object) -> object:
    # PyYAML's safe_load builds binary floats; config refuses them (SYS-13), so the
    # test helper keeps them as their decimal text, exactly as the strict loader would.
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, dict):
        return {k: _no_floats(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_no_floats(x) for x in v]
    return v


def user_dict(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = _no_floats(yaml.safe_load(USER_EXAMPLE.read_text()))  # type: ignore[assignment]
    data["approved_git_sha"] = FAKE_SHA
    data["approved_common_hash"] = sha256_bytes(COMMON_PATH.read_bytes())
    data.update(overrides)
    return data


def write_config_dir(
    tmp: Path,
    *,
    user: dict[str, object] | None = None,
    common_text: str | None = None,
    name: str = "a",
    mode: int = 0o600,
) -> Path:
    d = tmp / "config"
    d.mkdir(exist_ok=True)
    (d / "common.yaml").write_text(common_text or COMMON_PATH.read_text())
    up = d / f"{name}.yaml"
    up.write_text(yaml.safe_dump(user if user is not None else user_dict(), sort_keys=False))
    up.chmod(mode)
    return d


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    return write_config_dir(tmp_path)


@pytest.fixture
def sqlite_engine(tmp_path: Path) -> Iterator[Engine]:
    """SQLite ledger database migrated to ledger@head with the real migrations."""
    engine = create_engine(f"sqlite:///{tmp_path / 'ledger.db'}")
    migrate(engine, "ledger")
    yield engine
    engine.dispose()


@pytest.fixture
def market_engine(tmp_path: Path) -> Iterator[Engine]:
    """SQLite market database migrated to market@head with the real migrations."""
    engine = create_engine(f"sqlite:///{tmp_path / 'market.db'}")
    migrate(engine, "market")
    yield engine
    engine.dispose()


@pytest.fixture
def pg_url() -> Iterator[str]:
    """A fresh, empty Postgres database (dropped afterwards)."""
    base = os.environ.get("TRADER_TEST_PG_URL")
    if not base:
        pytest.skip("TRADER_TEST_PG_URL not set")
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    name = f"t_{uuid.uuid4().hex[:12]}"
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{name}"'))
    url = admin.url.set(database=name).render_as_string(hide_password=False)
    try:
        yield url
    finally:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()
