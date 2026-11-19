# asx-trader

> **Branch `bigwins-fast` (19 Nov 2026): B-fast build of FD v3.0 for the EMG2-20
> slice — PAPER ONLY.** EMG2 / EMG2-20 decision engine (`trader/lines/emg2.py`),
> order builder, breaker, approval queue (Telegram), paper-only IBKR adapter
> (`ib_async`), journal, reconciliation, report, Docker Compose stub
> (`deploy/`). Commands: `trader-bf validate-config`, `trader-bf emg2-list --asof D`.
> State, blocking decisions and the go-live checklist: `NEXT.md`; readings and spec
> defects: `docs/DECISIONS.md` section BF; server: `docs/SETUP_SYDNEY.md`.
> Coverage gate: `uv run python scripts/req_coverage.py --milestone BF --junit junit.xml`.

An automated, long-only, monthly-evaluated trading system for two ASX-listed
index ETFs (VAS 40%, VGS 60%) through Interactive Brokers Australia, with rule
L1 or static mode. The binding specification is **FD v2.10** (13 Nov 2026), plus
the verified R37 corrections recorded in `docs/DECISIONS.md`. Nothing here is a
claim of higher returns; the system's value is drawdown control, discipline
and complete records.

**Status: milestones M0 (foundations) and M1 (data pipeline).** There is no
decision, broker or execution code yet; those modules are stubs.

## What is built

| Area | Where | Requirements |
| --- | --- | --- |
| Config schema (§18 v2.10), approval pins, secrets scan, OPS-12 | `trader/config.py`, `config/common.yaml`, `config/examples/user.example.yaml` | OPS-10, OPS-11, OPS-12 |
| Calendar from the market `calendar` table; venue times from config; `exchange_calendars` date cross-check | `trader/calendar.py`, migration `m0002` | OPS-05 |
| Two databases (§12): ledger models and market models, mutability guard, audit logs | `trader/ledger.py`, `trader/data/models.py`, `trader/dbtypes.py`, `migrations/` | SYS-13, SYS-14 |
| JSON-lines logging | `trader/jsonlog.py` | MON-03 |
| Raw store + sha256 manifest, rental tree, bitemporal reads | `trader/data/store.py` | DAT-09, DAT-16, DAT-18 |
| EODHD connector with the counted call budget, Sunday re-download diff | `trader/data/eodhd.py` | DAT-01, DAT-10, DAT-15, DAT-23 |
| IBKR Activity Flex parser, Web Service client, mark mapping | `trader/data/flex.py` | DAT-02 |
| RBA F11.1 / F1.1 loaders, CPI stub | `trader/data/rates.py` | DAT-07 |
| Issuer distributions, missing-distribution rules | `trader/data/issuer.py` | DAT-14, DAT-22 |
| `tr_net` / `tr_gross` | `trader/data/totalreturn.py` | DAT-11, SYS-32 |
| DAT checks, verdicts, overrides, DAT-13 reference, DAT-19 trial | `trader/data/quality.py` | DAT-01 to DAT-13, DAT-17, DAT-19 |
| `MarketSnapshot` and builder | `trader/data/snapshot.py` | SYS-12, DAT-05, DAT-21 |
| Instruments (conId once, tick rules, delisting), spreads | `trader/data/instruments.py`, `trader/data/spreads.py` | SYS-20, SYS-29 to SYS-32 |
| Dead-man check-ins, sentinel unit | `trader/monitor.py`, `trader/orders.py` | DAT-12, DAT-20 |
| CLI (every §3 command registered) | `trader/cli.py`, `trader/data/commands.py` | — |

## Development

```bash
uv sync --locked --python 3.12          # locked; no dependency younger than 14 days
uv run ruff check . && uv run ruff format --check .
uv run mypy                             # strict
uv run pytest                           # SQLite; add TRADER_TEST_PG_URL for Postgres tests
uv run python scripts/req_coverage.py --milestone M1 [--junit junit.xml]
```

Tests make no network calls; vendor responses are synthetic recorded fixtures
in `tests/fixtures/`, and `tests/golden/` holds golden files
(`UPDATE_GOLDEN=1` regenerates them). The Postgres tests create and drop a
scratch database; `TRADER_TEST_PG_URL` must name a role with `CREATEDB`.

### Databases (§12)

Each user has `market_<user>` and `ledger_<user>_paper` / `ledger_<user>_live`.
Migrations are forward-only and live on two Alembic branches:

```bash
trader migrate --db market --app-role trader_a   # alembic -x db=market upgrade market@head
trader migrate --db ledger --app-role trader_a   # alembic -x db=ledger upgrade ledger@head
```

The URL is never stored in a file: production builds it from `TRADER_DB_*`
settings plus the `db_password` Docker secret; `TRADER_DATABASE_URL` /
`TRADER_MARKET_DATABASE_URL` are for local development only.

### Config

```bash
trader validate-config --config-dir config                    # common.yaml only
cp config/examples/user.example.yaml config/a.yaml && chmod 600 config/a.yaml
trader validate-config --user a --print-hashes                # values to pin
trader validate-config --user a                               # full check incl. pins + OPS-12
```

### Data commands (M1)

```bash
trader fetch --symbol VAS --from 2026-01-02 --to 2026-11-12 --user a [--history]
trader distribution enter --symbol VAS --ex-date 2027-01-04 --status expected --source-note "..." --user a
trader qc override --symbol VAS --date 2026-11-12 --use eodhd --reason "..." --user a
trader import calendar asx_2028.csv --source "ASX trading calendar 2028" --user a
trader import spread spreads_2026-10.csv --source "ASX Investment Products Oct 2026" --user a
```

### Mutability (§12)

Ledger: only `runs.state`, `order_intents.status`, `broker_orders.status`,
`parcels.qty_open`, `cashflow_expected.status` and `flags.*` may change. Market:
only `distribution.status` and `hypotheses.{status,result,decision,approver}`.
Every update writes an `audit_log` row in the same database; nothing is deleted.
Enforced by an ORM guard, Postgres column grants and an append-only trigger.

See `docs/DECISIONS.md` for every reading of the spec and the gaps reported.
