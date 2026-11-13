# asx-trader

An automated, long-only, end-of-day trading system for ASX shares, built for
two independent users. The binding specification is
*FD_ASX_Trading_System v1.2* (with the v1.3 small-account amendment, see
`docs/DECISIONS.md`).

**Status: milestone M0 (Foundations) only.** It contains no trading, broker or
data-vendor code; those modules are stubs.

## What M0 contains

| Area | Where |
| --- | --- |
| Package layout (§3) | `trader/` (stubs for M1–M7 modules) |
| Config schema and validation (§18, §14) | `trader/config.py`, `config/common.yaml`, `config/examples/user.example.yaml` |
| Approval pins, config hash (OPS-10) | `trader/config.py` (`load_config`, `check_approval_pins`) |
| Secrets only from Docker secrets (OPS-11) | `trader/secrets.py`, secret scan in `trader/config.py` |
| Account-size check (OPS-12) | `trader/config.py` (`ops12_check`, `ops12_mode`) |
| Calendar and events (OPS-05, §5) | `trader/calendar.py`, migrations `0003`, `0004` |
| Ledger models and mutability rules (§12) | `trader/ledger.py`, migrations `0001`, `0002` |
| Money as `Decimal` (SYS-13) | `trader/money.py`, `MoneyType` in `trader/ledger.py` |
| UTC timestamps, ASX dates (SYS-14) | `trader/timeutil.py`, `UTCDateTime` in `trader/ledger.py` |
| JSON-lines logging (MON-03) | `trader/jsonlog.py` |
| Operational constants | `trader/constants.py` |
| CLI skeleton | `trader/cli.py` (`trader --help`) |
| CI | `.github/workflows/ci.yml`, `scripts/req_coverage.py` |

## Development

```bash
uv sync --locked --python 3.12          # Python 3.12, locked dependencies
uv run ruff check . && uv run ruff format --check .
uv run mypy                             # strict
uv run pytest                           # SQLite; add TRADER_TEST_PG_URL for Postgres tests
uv run python scripts/req_coverage.py --milestone M0
```

The Postgres tests create and then drop a scratch database. To run them, set
`TRADER_TEST_PG_URL` to a role with `CREATEDB` and `CREATEROLE`, for example
`postgresql+psycopg://owner:pw@localhost/postgres`.

### Config

```bash
trader validate-config --config-dir config                    # common.yaml only
cp config/examples/user.example.yaml config/a.yaml && chmod 600 config/a.yaml
trader validate-config --user a --print-hashes                # values to pin
trader validate-config --user a                               # full check incl. pins + OPS-12
```

Per-user files `config/a.yaml` and `config/b.yaml` are git-ignored. They must
be mode 600 and must never contain secrets.

### Database

Migrations are forward-only. The database URL is never stored in a file.

```bash
TRADER_DATABASE_URL=postgresql+psycopg://owner:pw@localhost/ledger_a \
  trader migrate --app-role trader_a          # or: alembic -x app_role=trader_a upgrade head
```

In production the URL is built from `TRADER_DB_HOST`, `TRADER_DB_PORT`,
`TRADER_DB_NAME` and `TRADER_DB_USER`, plus the `db_password` Docker secret.

### Mutability rules (§12)

Only these columns may be updated: `runs.state`, `order_intents.status`,
`broker_orders.status`, `parcels.qty_open` and `flags.*`. Every update also
writes an `audit_log` row (use `trader.ledger.update_mutable`). All other tables
are insert-only, and nothing is ever deleted. Three layers enforce this:

1. an ORM guard (`install_mutability_guard`);
2. Postgres column-level grants for the app role;
3. on `audit_log`, INSERT-only for the app role plus an append-only trigger that
   applies to every role.

See `docs/DECISIONS.md` (L-01 to L-07).
