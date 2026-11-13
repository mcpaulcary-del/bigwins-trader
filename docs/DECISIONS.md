# Build decisions and spec ambiguities

Baseline: **spec v2.10** (`FD_FINAL.md`, 13 Nov 2026, sha256
`c7f02185b4e8d1ad3c07e992e8d2d8da791d1121785bd614ce8ccdbab4d5bba9`, stored as
`spec_hash` in `config/common.yaml`), plus the verified corrections of research
report 37 that the coordinator passed on, marked **"v2.10 + R37 correction"**.
M0 was first built against v1.2 and the v1.3 amendment (git history up to
`9156c2d`); it was re-based on v2.10 as described in section R below. The
withdrawn v2.0 share-strategy archive was not read.

Where the spec is ambiguous, the safer reading was chosen and recorded here.
**[spec defect]** marks a gap or contradiction in v2.10 that the spec owner should
fix; **[needs spec owner]** marks a choice that should be confirmed.

## Environment

| # | Decision |
| --- | --- |
| E-01 | Python 3.12.3, `uv` 0.11.32. |
| E-02 | Exact pins in `pyproject.toml`; `uv.lock` pins the full transitive set with hashes. `[tool.uv] exclude-newer = 2026-10-29` keeps every locked version at least 14 days old (BP-10, `ops.dependency_min_age_days`); re-locking moved four packages (coverage, mypy-extensions, typing-inspection, python-dateutil) back to versions older than 14 days. New runtime dependencies: `pandas 2.3.3` and `numpy 2.3.4` (the `MarketSnapshot` interface uses `pd.Series`, §3) and `exchange_calendars 4.11.2` (OPS-05 date cross-check only). |
| E-03 | mypy `--strict` on the whole package, tests, scripts and migrations. |
| E-04 | Local Postgres 16 was started; every Postgres test (grants, triggers, both migration branches) ran and passed. Tests always also run the real migrations on SQLite. CI uses a `postgres:16` service and migrates both databases. |
| E-05 | GitHub Actions are pinned by tag; pin by SHA before the repo goes live. |

## R. Re-baseline of M0 from v1.x to v2.10

| # | Decision |
| --- | --- |
| R-01 | Everything from the withdrawn v1/v2.0 share strategy is removed: the six-share universe (BHP, RIO, FMG, CBA, CSL, WDS), event blackouts and the `events` table, chandelier stop, RSI dip-buy, commodity filter and baskets, regime/news/insider filters, shadow modules, the `small_account` block (v1.2/v1.3 amendments), `paper_universe`/`universe_rule`, the `fallback` and `validate` commands, and the stub modules `signals/*`, `backtest/*`, `data/{announcements,commodities,flows,ibkr_hist}.py`. `rules/l1.py`, `research/*`, `benchmarks.py` are the v2.10 stubs (§3 layout). |
| R-02 | `config/common.yaml` is the §18 v2.10 YAML verbatim, except `spec_hash` (filled, see header), `card_set_hash` (C-12) and `research.marginal_rates` (C-13). |
| R-03 | The coverage script carries the v2.10 M0 and M1 IDs and fails CI if code, tests, scripts or migrations refer to a withdrawn ID (CL-C, CL-F: the STR series, PRT-01..05, SYS-21/22/25..28, RSK-05/20/21/23, VAL-01..13, USR-02/06/12, ADP, FUT). The list is built from ranges so the script itself holds no withdrawn literal. |

## Config (§18)

| # | Decision |
| --- | --- |
| C-01 | Unknown keys anywhere are errors; duplicate YAML keys are errors; YAML floats parse as exact `Decimal`; base-60 integers are disabled. **Every non-integer config number is a `Decimal`** (v2.10 has no float-only signal parameters in M0/M1; M2 may convert inside signal maths). |
| C-02 | `approved_common_hash` = SHA-256 of the exact bytes of `common.yaml` (comments included). |
| C-03 | Deployed code SHA from `trader/_build_sha.txt` (image) or `git rev-parse HEAD` (`-dirty` never matches). |
| C-04 | Config hash (OPS-10) = SHA-256 over both files, framed with labels and lengths. `LoadedConfig.run_hashes` gives the config hash, `spec_hash` and `card_set_hash` that every run stores (`runs` has all three columns). |
| C-05 | Personal limits are tighter-only: `limits.max_orders_per_day <= risk_defaults.max_orders_per_day`. `exclude_symbols` must be live sleeves. |
| C-06 | Per-user config files must be owner-only (mode 600). |
| C-07 | Isolation (§19): `ibkr.live.gateway_host = gw-<user>-live`, `ibkr.paper.gateway_host = gw-<user>-paper`, ports 4003/4004, client id 11, live account ids `U…`, paper `DU…`. `eodhd.licensee` must equal `user` (USR-05, DAT-15). |
| C-08 | Values the spec says need a spec change to alter are fixed by the schema: `l1.cash_etf: null` (PRT-18), `execution.tif: DAY` (GTD only after I15), `data.eodhd.on_budget_exceeded: fail_closed`, `risk_defaults.backtest_max_drawdown: null` (USR-05), `hosting` in {owner_host, self_hosted} (USR-10), `tax.entity: individual`, `tax.residency: resident` (TAX-03). |
| C-09 | Cross-checks: sleeve base weights and each benchmark's weights sum to exactly 1; B2 holds exactly the sleeves; B1 is not a sleeve; `canary_units` covers exactly the sleeves; `data.eodhd.instruments` includes every sleeve and benchmark symbol; `tranche_offsets_by_n` defines N = 1 and N = `tranches_max` with N distinct offsets; votes thresholds ordered; venue times ordered; trading-day job times strictly increasing; `spread_warn < spread_exclude`. |
| C-10 | `tranche_offsets` in `<user>.yaml` must hold exactly one offset: USR-13 says the user's offsets override the default only with N = 1. |
| C-11 | Validation sizing NAV, when no live NAV exists (at `trader init`), is `capital_cap_aud` (the configured base); `--sizing-nav` overrides it. |
| C-12 | **[needs spec owner]** `card_set_hash` is `null` in the repo: no hypothesis card set is frozen yet (G0), and §18 shows only a placeholder. `null` is accepted, stored as NULL in `runs.card_set_hash`, and **`mode: L1` is refused while it is null** (OPS-12). `spec_hash` must be a real 64-hex hash. |
| C-13 | **v2.10 + R37 correction.** `research.marginal_rates` is keyed by income year: `2026-27: [0.00, 0.15, 0.30, 0.37, 0.45]`, `2027-28: [0.00, 0.14, 0.30, 0.37, 0.45]` (P9 answered; R37 gave only the lowest rate for 2027-28, so the other three are assumed unchanged **[needs spec owner]**). OPS-12 checks `tax.marginal_rate` against the list of the income year that contains the validation date; a year with no list fails validation. This changes the shape of a §18 key **[spec defect: v2.10 has one undated list with a P9 placeholder]**. |

## OPS-10 / OPS-11

| # | Decision |
| --- | --- |
| S-01 | Config files are scanned for secret-like key names and values (bot tokens, age/PEM private keys, GitHub/AWS/Slack tokens, JWTs, DSNs with passwords, `api_token=` in URLs). Public fields `age_public_key`, `snapshot_key_id` and `ops.flex_token_warn_days` are allowed. |
| S-02 | Secrets are read only from `/run/secrets/<name>` from a closed list (`eodhd_api_token`, `ibkr_flex_token`, `telegram_bot_token`, `smtp_password`, `db_password`, `healthchecks_url`, `object_store_token`, `rclone_config`, `totp_seed`, `tws_password`); never from environment variables; `SecretValue` hides its value. |
| S-03 | **[needs spec owner]** `TRADER_DATABASE_URL` (may carry a password) is accepted for local development and tests only; production builds the URL from `TRADER_DB_*` plus the `db_password` secret. |

## OPS-12 (v2.10)

| # | Decision |
| --- | --- |
| O-01 | The v1 "median full-trend position" check is gone. v2.10 OPS-12 is implemented as: tranche count N per PRT-14 (N = `tranches_max` only if min(base weight) x sizing NAV / `tranches_max` >= `tranche_min_order_mult` x `min_order_value_aud`, i.e. A$9,375 at the defaults); every sleeve's transition order (base weight x sizing NAV / N, rounded down to the cent) must be >= `min_order_value_aud`; tax flags and hosting (schema); `tax.marginal_rate` required for a live account and, when set, listed for the income year (C-13); `mode: L1` needs a frozen card set, H1 `passed` with an owner approval and H11 passed at the user's rate; a live L1 account needs `limits.backtest_max_drawdown`. |
| O-02 | OPS-12 is always **hard** (no warning-only mode): v2.10 says validation fails at `trader init` and on any config change. `trader validate-config` is the change-time check. |
| O-03 | Card evidence for `mode: L1` comes from the hypothesis registry (M3). Until M3, no evidence is available, so `mode: L1` always fails (fail closed). |
| O-04 | The check uses every sleeve, excluded or not (the stricter reading). |

## Calendar and venue (§4, §5, OPS-05)

| # | Decision |
| --- | --- |
| K-01 | The `calendar` table lives in the **market** database with key (venue, date, fetch_time) and a `source` column (L-11). Migration `m0002` seeds XASX 1 Nov 2026 - 31 Dec 2027 from the §5 table: weekends and listed closures closed; 24 and 31 Dec 2026 and 2027 close at 14:10; every other weekday closes at **16:10**, the start of the closing single price auction (`venue.XASX.closing_auction[0]`). |
| K-02 | **v2.10 + R37 correction:** Mon 26 Apr 2027 is a trading day (v2.10: [unverified], P5). Its row's source says so. |
| K-03 | The calendar module has no holiday list, weekday rule or literal date/time; a date outside the table raises `CalendarGapError`. Auction, close-availability (16:25) and early-close times come only from `venue.XASX`. |
| K-04 | OPS-05 cross-check: `library_cross_check` diffs session dates against the pinned `exchange_calendars` XASX calendar; times are never read from it. `coverage_warning` returns the OPS-05 WARN under `ops.calendar_min_days_ahead` (60). Later years (and the historical years DAT-05 needs, see D-15) are loaded with `trader import calendar` (insert-only, audited). |
| K-05 | Execution date E = next full trading day (`next_full_trading_day`): an early-close day is skipped (§4). Evaluation dates: `evaluation_date(year, month, offset)` with offset `last` or k. |

## Ledger and market data model (§12)

| # | Decision |
| --- | --- |
| L-01 | **Two databases, two Alembic branches** in one script directory: `ledger` (revisions 0001..0005) for `ledger_<user>_paper` / `ledger_<user>_live`, and `market` (m0001, m0002) for `market_<user>`. `-x db=ledger|market` is required and every v2.10 revision checks it. History is not rewritten: 0001-0004 stay; **0005** re-bases a v1.x database to the v2.10 ledger (drops the withdrawn and moved tables, recreates changed ledger tables, keeps `audit_log` with its trigger and `config_versions`). 0005 **fails closed**: it refuses to drop any table that holds a row other than the migration-seeded `calendar`/`events` (M0 was never deployed, so this never triggers in practice). |
| L-02 | Mutability (§12): ledger `runs.state`, `order_intents.status`, `broker_orders.status`, `parcels.qty_open`, `cashflow_expected.status`, `flags.*`; market `distribution.status` and `hypotheses.{status,result,decision,approver}`. Enforced three ways: ORM `before_flush` guard, Postgres column grants for the app role, and `audit_log` INSERT-only for the app role plus an append-only trigger for every role, in **both** databases. |
| L-03 | Columns added where §12 names a table but not every column: `runs.created_at`, `tranche_state.created_at`, `plans.created_at`, `plan_lines.id`, `recon.checked_at`, `flags (name, value text, actor, reason, updated_at)`, `vetoes (execution_date, symbol, side, received_at, channel, actor)`, `alerts (ts, level, type, reason_code, msg, channel)`, `overrides (ts, kind, symbol, actor, reason)`, `cashflow_expected (announced_at, amount, status, note)`, `acceptances (ts, check, account_id, recorded_by, note)`, `qc_event.trade_date`. `broker_orders.client_order_id` and `fills.perm_id` are nullable (foreign orders, BP-02; Flex-booked manual trades, BP-20). |
| L-04 | "The app role has INSERT only" on `audit_log` is read literally (no SELECT, no RETURNING). |
| L-05 | The app role is created `NOLOGIN` if missing; name from `-x app_role=` / `TRADER_DB_APP_ROLE`. |
| L-06 | `runs.date` is unique (one run per trading day, §4). |
| L-07 | **[needs spec owner]** carried from M0: `order_intents.limit_price` (set at send time, §3), `broker_orders.cancelled_at` and `runs.reason_code` are not in the §12 mutable list; M4/M5 must record them as new rows, or the spec must add them. |
| L-08 | `instrument` is versioned insert-only: key (id, version). `id` is the stable internal id used everywhere; a symbol change, re-qualification, tick-rule change or delisting inserts a new version; the current record is the highest version. **[spec defect]** §12 gives `instrument` an `id` PK but SYS-32 needs a delist date, reason and payout to be recorded later, and `instrument` is not in the mutable list. |
| L-09 | Per-unit rates (distribution cash and franking per unit, FX, unit ratios, vendor adjusted close, final payout) are exact `NUMERIC(24,10)`; money totals and prices stay `NUMERIC(18,4)`. **[spec defect]** "Money is NUMERIC(18,4)" would truncate issuer distribution amounts quoted in fractions of a cent per unit. |
| L-10 | The market database has its own `audit_log` (same guard). **[spec defect]** §12 lists `audit_log` only in the ledger, but market updates (`distribution.status`, `hypotheses`) and the import loads of §3 must each write an audit row, and a market row and its audit row should commit together. |
| L-11 | `calendar` key is (venue, date, fetch_time); the latest fetch per (venue, date) is the record. **[spec defect]** §12 gives (venue, date) PK, which makes a correction impossible under "insert-only, corrections are new rows" and DAT-18 (bitemporal). |

## Logging (MON-03)

| # | Decision |
| --- | --- |
| G-01 | Every line has exactly the 11 MON-03 keys in order; missing values are `null`; `ts` is UTC ISO-8601 with ms and `Z`; `Decimal` logs as a string. |
| G-02 | Account numbers masked to prefix + last 3 digits; secrets redacted by key name, `SecretValue` and value patterns (incl. `api_token=` query strings). |
| G-03 | Daily rotation at UTC midnight, 90 backups (`ops.log_retention_days`); the audit logs in the databases are permanent. |

## CLI (§3)

| # | Decision |
| --- | --- |
| X-01 | Every §3 command is registered with its v2.10 options (`resume --clear kill|integrity|buys|all`, `mode static --confirm`, `stage <n> --confirm`, `qc override`, `fetch`, `drill`, `canary`, `golive`, `hypothesis`, `holdout`, ...). Unimplemented commands print `trader <cmd>: not implemented yet (planned for Mx).` and exit 69. Exit codes: 0 OK, 1 failed, 2 invalid config, 3 approval-pin mismatch. |
| X-02 | `trader migrate --db market|ledger` upgrades `<db>@head`. |
| X-03 | The builder-named import sub-command of §3 is **`trader import <kind> <file.csv> --source <text>`**, kinds `calendar` and `spread` in M1 (`cpi`, `amma`, `capital-losses` follow in M3/M5). Each load is insert-only, stamps the fetch time and source on every row, and writes a market `audit_log` row. |
| X-04 | `trader secret set` will read the value from stdin, never argv (M5). |
