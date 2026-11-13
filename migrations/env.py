"""Alembic environment. Forward-only migrations (spec §12).

URL: ``-x url=...``, else ``trader.db.database_url()`` (``TRADER_DATABASE_URL`` for
dev, or ``TRADER_DB_*`` settings plus the ``db_password`` Docker secret).
App role for grants (Postgres only): ``-x app_role=...`` or
``TRADER_DB_APP_ROLE`` (default ``trader_app``).
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from trader.ledger import Base

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    url = context.get_x_argument(as_dictionary=True).get("url")
    if url:
        return url
    from trader.db import database_url  # TRADER_DATABASE_URL (dev) or env parts + secret

    built = database_url()
    return built if isinstance(built, str) else built.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    context.configure(
        url=_url(), target_metadata=target_metadata, literal_binds=True, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = config.attributes.get("connection")
    if connectable is not None:
        context.configure(
            connection=connectable, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = engine_from_config(
        {"sqlalchemy.url": _url()}, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
