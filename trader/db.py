"""Database URL and engine helpers.

The password is a secret (OPS-11): it is read from the Docker secret
``db_password``, never from config files. Host, port, database and role are
non-secret settings from the environment (``TRADER_DB_HOST``, ``TRADER_DB_PORT``,
``TRADER_DB_NAME``, ``TRADER_DB_USER``). ``TRADER_DATABASE_URL`` is accepted
for local development and tests only.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine

from trader.constants import SECRETS_DIR_DEFAULT
from trader.secrets import read_secret


def database_url(secrets_dir: Path = SECRETS_DIR_DEFAULT) -> str | URL:
    dev = os.environ.get("TRADER_DATABASE_URL")
    if dev:
        return dev
    name = os.environ.get("TRADER_DB_NAME")
    user = os.environ.get("TRADER_DB_USER")
    if not name or not user:
        raise RuntimeError(
            "set TRADER_DB_NAME and TRADER_DB_USER (password: Docker secret db_password)"
        )
    return URL.create(
        "postgresql+psycopg",
        username=user,
        password=read_secret("db_password", secrets_dir).reveal(),
        host=os.environ.get("TRADER_DB_HOST", "postgres"),
        port=int(os.environ.get("TRADER_DB_PORT", "5432")),
        database=name,
    )


def make_engine(url: str | URL) -> Engine:
    return create_engine(url, future=True, pool_pre_ping=True)
