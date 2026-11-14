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

## M1 data pipeline (§6, DAT-01 to DAT-23, SYS-12, SYS-20, SYS-29 to SYS-32)

| # | Decision |
| --- | --- |
| D-01 | **No live keys, no network in tests.** EODHD, Flex and RBA connectors take an injected transport; tests use synthetic recorded fixtures (`tests/fixtures/`), never licensed vendor data. Keys come only from Docker secrets (`eodhd_api_token`, `ibkr_flex_token`); a key is read before a call is counted, sent only to the vendor, and never appears in an error, a log or a stored file. |
| D-02 | **DAT-23 budget.** Each request is recorded in `vendor_call_log` in its own committed transaction **before** it is sent (a crash cannot under-count); a refused request is not recorded. Daily limit per GMT date, plus `calls_per_minute`. History older than `history_years` is refused without a call. The daily job is one range request per instrument from the day after the last stored bar to the latest close readable under the 16:25 rule; dividends only on the 19:30 run (retries fetch bars only). Jobs commit after each instrument so a rerun resumes (OPS-01). |
| D-03 | **Raw store.** `data/raw/{source}/{fetch_date}/{name}.{HHMMSSffffff}Z.{ext}.gz`, `fetch_date` = UTC date of the fetch. Flex XML and RBA CSV are stored with their own extension (`.xml.gz`, `.csv.gz`) rather than `.json.gz` **[spec defect: DAT-18 names only `json.gz`]**. Gzip without timestamp; files read-only, never overwritten; per-directory `MANIFEST.sha256`; `verify()` is the DAT-09 check (any problem = whole-run BLOCK). |
| D-04 | **Validated set.** Each verdict writes a `qc_event` (`VERDICT`) and, unless BLOCK/quarantined, a new `validated_close` row; the latest row per date is the record. A Flex-only close (DAT-02 case (c)) is stored with `signals_ok = false` so no signal or `tr_net` uses it. |
| D-05 | **DAT-02 / Flex timing (v2.10 + R37 correction).** Flex for D is normally published only in the Sydney afternoon of D+1, so at 08:00 a missing mark is the expected case: the verdict is `SINGLE_SOURCE` (case (a) not held: buys and sells; case (b) held: sells only, buys wait), the latest available mark is attached to the verdict with its date for information only (never used as the D cross-check), and the verdict is re-issued when the D mark arrives. `schedule.flex_pull` stays configurable (common.yaml keeps the §18 value 07:30; **[needs spec owner]** move it to the afternoon by change control, I3/I14). Benchmark-only and paper symbols are single source by design and log no WARN. |
| D-06 | **Flex Web Service (R37).** `SendRequest` with `fd`/`td` (never `p`), then `GetStatement` polling on the documented in-progress codes; `User-Agent` on every request; client-side limit 1 request/s and 10/min. `orderReference` is optional (absent without Audit Trail fields and on paper). Lot-level `OpenPosition` rows are skipped (the summary row is used). XML with a DTD or entity is refused. |
| D-07 | **[spec defect]** The Flex **query id** has no §18 key; it is read from the secrets directory as `ibkr_flex_query_id` (not sensitive, but adding a config key would change the §18 schema). |
| D-08 | **Mark mapping (§4).** The mark for trading day D is the mark dated D, else the mark in the first later statement with no ASX session in (D, statement date]; otherwise none. |
| D-09 | **DAT-04.** The 60-day mean uses up to the last 60 changes of validated closes; with fewer than 2 changes only the 15% rule applies. A spike with an agreeing mark (DAT-02 OK tolerance) and return <= 15% is WARN (`DATA_SPIKE`) and validated; otherwise quarantined (BLOCK) until `qc override`. A benchmark-only symbol never gets a mark, so its spikes always need an override (safer). |
| D-10 | **DAT-10 "more than 0.5%" [spec defect: ambiguous].** Read as any stored close that moved by more than 0.5%. The alternative reading (more than 0.5% of the compared rows) makes a single changed row a BLOCK in any window under 200 rows and leaves "more than five rows" with no effect. Restated bars are appended as new rows (never updated); the BLOCK stays until a `qc override` for that symbol. The weekly re-download is per instrument; instruments that do not fit the budget are retried on later days (`pending_redownloads`, week anchored on Sunday 00:00 Sydney). |
| D-11 | **DAT-11** is implemented as pure checks on aligned series: daily return gap (5 bp / 25 bp on ex or split dates), adjusted/raw ratio changing off an ex/split date or falling, implied dividend vs issuer amount (1%), distributions per year, yearly return (0.5%). BLOCK only for a gap or ratio change on a date with a missing amount (DAT-22) or a restated close (DAT-10). |
| D-12 | **[spec defect]** DAT-11's "issuer's published fund return" has no table or entry command; `dat11_yearly_return` takes it as an argument. The issuer's distribution schedule (count per year) is taken from the issuer rows entered under DAT-14. |
| D-13 | **DAT-14 / DAT-22.** An issuer `estimated`/`final` row needs `period_end` (TAX-08); an `expected` row has no amount (DB check constraint). Later entries supersede earlier ones per ex-date (bitemporal). Status changes in place are allowed only where the check constraint holds. Vendor dividends are stored in `vendor_dividend` (L-13). DAT-22 blocks an evaluation for: an `expected` row with ex-date <= D; a vendor dividend with no row; an adjusted/raw ratio change with no row that is not a recorded split. `tr_net` stops before the first such date. "No future expected row" accepts any future row (expected, estimated or final). |
| D-14 | **DAT-22 vs BLOCK.** DIST_MISSING does not turn the close verdict into BLOCK (BLOCK would also stop sells, which DAT-22 allows); it sets `evaluate_ok = buy_ok = false` and is exposed in `MarketSnapshot.dist_missing` (a refinement of the §3 fields). |
| D-15 | **DAT-05** needs the calendar for every month of the lookback: historical XASX calendar years must be loaded with `trader import calendar` before the first evaluation (the seed covers Nov 2026 onward only; no historical holidays were guessed). The snapshot BLOCKs a symbol with fewer than `min_evaluation_closes` evaluation-date `tr_net` values and records a `qc_event`. |
| D-16 | **History download.** `trader fetch ... --history` marks the bars as the history download: validated on DAT-03, DAT-04, DAT-10, DAT-11 alone (DAT-08 is not applied, so bars before the calendar table are accepted) and stored with `backfill = true`. A bar that arrives late (after the 08:00 deadline of its day) with no stored mark is `SINGLE_SOURCE` + `backfill`. |
| D-17 | **DAT-01.** Before 21:30 on D a missing bar issues no verdict (pending); WARN from 21:30; BLOCK from 08:00 on the next trading day, except case (c). |
| D-18 | **DAT-17 override.** Needs a non-empty typed reason and exactly one of `--use eodhd`, `--use flex`, `--price`; recorded as `qc_event` `DAT-17` with `override_by`/`override_reason`; the validated close carries the override id; the verdict after an override is WARN. The `MANUAL_PENDING` order-sheet line for a held sell is M4/M5 (no intents exist in M1). |
| D-19 | **SYS-20/29/32.** `instrument` is versioned (L-08). `ensure_instrument` calls the qualifier only when no `con_id` is stored; `order_con_id` refuses an unqualified (data-only) instrument such as DHHF. Tick sizes are the stored IBKR market-rule increments; without them DAT-02 uses the percentage tolerance only (stricter). Delisting inserts a version with date, reason and payout; the payout is the last `tr_net` return. |
| D-20 | **SYS-30/31.** Spreads are entered per instrument and month (`trader import spread`, table `spread_report`, L-14); > 0.04% WARN, >= 0.07% EXCLUDE; a sleeve with no figure for the month is a WARN. SYS-31 is enforced by the approval pin (any change to sleeves, weights or benchmarks changes `approved_common_hash`) plus `instrument_identity`, a fingerprint the M3 registry will compare with the frozen card set. |
| D-21 | **Total return.** Exact `Decimal` arithmetic (34 digits), stored at 12 dp; TR = 1 on the first validated date; a distribution or split on a date with no close is applied at the next close; build id = hash of all inputs (identical inputs give the same id and are stored once). |
| D-22 | **RBA.** Rows are appended only for new dates or changed values; DAT-07 compares consecutive published rates; `value_on` carries the last rate forward over RBA non-publication days. CPI (R37): table plus loader stub; factor rounded to 3 dp half-up; none when <= 1. |
| D-23 | **DAT-12, DAT-19, DAT-20** are building blocks used by later milestones: `DeadManMonitor` (check-in or `/fail`), `dat19_trial` (complete after 20 trading days), `orders.sentinel_floor` (to be called inside `build_orders()`, M2). |

Additional market tables (each a reported §12 gap): L-12 `validated_close` (the "validated set" of DAT-04/DAT-17), L-13 `vendor_dividend` (vendor dividends needed by DAT-14/DAT-22), L-14 `spread_report` (§3 says the SYS-30 figures are "kept per instrument and month in the market database" but §12 has no table).

## R37 corrections applied (coordinator, "v2.10 + R37 correction")

1. Flex timing: D-05. 2. Optional `orderReference`: D-06. 3. Flex Web Service fd/td, 1/s and 10/min, User-Agent: D-06 (token life is M5). 4. Year-keyed marginal rates: C-13. 5. CPI rule: D-22. 6. 26 Apr 2027 trading day: K-02. 7. Vanguard ex-dates first trading day of Jan/Apr/Jul/Oct: noted (O21); used in test fixtures, no code depends on it.
