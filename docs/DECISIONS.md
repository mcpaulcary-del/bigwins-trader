# Build decisions and spec ambiguities

Baseline: **spec v1.2 + §9.1 amendment, superseded by the v1.3 amendment**.
Both were received from the coordinator during M0 (see D-01 and D-02). Where
the spec was ambiguous or contradictory, the most conservative reading was
chosen and recorded here. Items marked **[needs spec owner]** should be
confirmed or the spec amended.

## Environment

| # | Decision |
| --- | --- |
| E-01 | Python **3.12.3** (`/usr/bin/python3.12`), matching the spec's stack. 3.13 was also installed and not used. |
| E-02 | Dependencies are exact pins in `pyproject.toml`; `uv.lock` pins the full transitive set with hashes (INF-04). Only M0 dependencies are present; `ib_async==2.1.0`, APScheduler and pandas are added in the milestones that use them. |
| E-03 | mypy `--strict` is applied to the whole `trader` package (and tests, scripts, migrations), which is stricter than "strict on the decision core". |
| E-04 | Local Postgres 16.15 was available: `alembic upgrade head` was run against it, and the Postgres-only tests (grants, append-only trigger, column types) ran and passed. Tests also always run the real migrations on SQLite. CI uses a `postgres:16` service. |
| E-05 | GitHub Actions are pinned by version tag (`actions/checkout@v4`, `astral-sh/setup-uv@v6`); their commit SHAs could not be verified offline. **Recommend pinning by SHA** before the repo goes live. |

## D-01 Spec v1.2 + §9.1 amendment: small-account mode (superseded by D-02)

* Added `small_account: {enabled: bool = true, asset: 'VAS' | 'BHP' = 'VAS'}` to `<user>.yaml`, and set the example `capital_cap_aud: 5000`.
* Registered `trader mode full --confirm` (not implemented in M0; PRT-10..PRT-17 belong to M2).
* The `asset` field was **removed** by the v1.3 amendment (D-02). A config that still has it is now rejected as an unknown key.

## D-02 Spec v1.3 amendment (M0 schema only, no behaviour)

* `<user>.yaml`: `small_account: {enabled: bool = true, universe: list = [VAS, VGS, CASH], switch_buffer: float = 0.02, momentum_months: list[int] = [6, 9, 12], cash_proxy: str | None = None}`. The whole block is optional and defaults to these values.
  * Validation: `universe` entries must come from {VAS, VGS, PMGOLD, CASH}; `switch_buffer` must be in [0, 0.1]. Conservative additions: `universe` must be non-empty with no duplicates; `momentum_months` must be positive, distinct and non-empty; `cash_proxy`, if given, must be a valid symbol.
  * `small_account.universe` is deliberately **not** checked against `common.universe`: VGS and PMGOLD are outside the six-share universe by design. `exclude_symbols` is still checked against `common.universe` only.
* `common.yaml`: optional `paper_universe: list[str]` (symbols, no duplicates) and optional `universe_rule: {source: ASX20, max_per_sector: int > 0, max_iron_ore_majors: int >= 0}`. `source` is restricted to `ASX20`, the only value given. The repo's `common.yaml` stays §18 v1.2 verbatim and has neither key, because no v1.3 values were supplied.
* `trader mode full --confirm` stays registered (not implemented in M0).
* **OPS-12 interaction [needs spec owner].** With `capital_cap_aud: 5000`, the OPS-12 check (median full-trend position x sizing NAV >= A$4,000) cannot pass, so a hard OPS-12 check would make the amended default config unusable. Chosen reading: while `small_account.enabled` is true, the full-trend sleeve is not traded, so OPS-12 is reported as a **warning only**. Leaving small-account mode (`trader mode full --confirm`) is a config change, so OPS-12 is **hard** again. The amended §9.1 text was not available to the build agent.

## Config (§18, §14)

| # | Decision |
| --- | --- |
| C-01 | `config/common.yaml` is §18 verbatim. Unknown keys anywhere are errors (`extra="forbid"`). Duplicate YAML keys are errors. YAML floats are parsed as exact `Decimal`s, and YAML 1.1 base-60 integers are disabled (so `19:30` can never become `1170`). |
| C-02 | **`approved_common_hash` = SHA-256 of the exact bytes of `common.yaml`.** Any byte change, comments included, needs re-approval. This is the strictest reading. |
| C-03 | **Deployed code SHA** comes from `trader/_build_sha.txt`, which is baked into the image at build time (the image has no `.git`). Without that file it comes from `git rev-parse HEAD`, and a working tree with uncommitted tracked changes gives `<sha>-dirty`, which never matches a pin. If the SHA can't be determined, the trader refuses to run. Pins must be a full 40-hex SHA and a 64-hex hash. The spec's `"…"` placeholders are invalid on purpose. |
| C-04 | **Config hash (OPS-10)** = SHA-256 over both files' exact bytes, framed with labels and lengths. It is stored in `runs.config_hash`, and the `config_versions` table is ready to hold approved versions. |
| C-05 | **Personal limits are tighter-only.** A user value must be `<=` the matching `risk_defaults` value for `max_order_value_aud`, `max_orders_per_day`, `daily_loss_pct` and `hard_drawdown_pct`. A user `hard_drawdown_pct` must also stay above `soft_drawdown_pct`. `exclude_symbols` must be universe shares. Omitted limits fall back to the common defaults. |
| C-06 | Per-user config files must be owner-only (no group or other permission bits) or loading fails (§18 comment "owner-only permissions"). |
| C-07 | Isolation guards in `<user>.yaml`: `ibkr.gateway_host` must be `gw-<user>`, `client_id` must be 11 (§19: the trader uses 11), and `port` must match `mode` (paper 4004, live 4003). |
| C-08 | `filters.news.enabled: true` is rejected (decision D7: off in v1, and changing it needs a spec update). |
| C-09 | `sizing.n_names` must equal the size of the universe (N is fixed at 6). Every universe share must be in exactly one cluster. `vol_floors` must cover exactly the universe. Basket weights and family weights must each sum to 1. Hysteresis pairs must be ordered. Blackout windows must contain offset 0 ("V itself is always included"). |
| C-10 | Money in config is `Decimal`, and binary floats are refused (SYS-13). Ratios that multiply money in execution and risk (`collar`, ladder steps, `vas_band`, commission rate, `max_order_value_pct`) are `Decimal`. Ratios used in signal and sizing maths are floats. |

## OPS-11 secrets

| # | Decision |
| --- | --- |
| S-01 | Config files are scanned for secret-like key names (password, token, secret, api_key, passphrase, private_key, credential …). The public fields `age_public_key` and `snapshot_key_id` are allowed. Files are also scanned for secret-shaped values (Telegram bot token, `AGE-SECRET-KEY-1…`, PEM private keys, GitHub, AWS and Slack tokens, JWTs, DSNs with passwords). Any hit refuses the file. |
| S-02 | Secrets are read only from files in the Docker secrets directory (`/run/secrets/<name>`), from a closed list of names, and never from environment variables. `SecretValue` hides its value in `repr` and `str` and in logs. |
| S-03 | **[needs spec owner]** `TRADER_DATABASE_URL` (which can include a password) is accepted **for local development and tests only**. In production the URL is built from non-secret `TRADER_DB_*` settings plus the `db_password` Docker secret. `alembic.ini` carries no URL. |

## OPS-12 account-size check

| # | Decision |
| --- | --- |
| O-01 | Full-trend weight of share i = w_TR(i) / N x min(max_vol_scale, target_vol / max(sigma_i, floor_i)). w_TR is the **trend family weight** for that share's group (commodity names = symbols with a commodity basket). The median is taken over all six universe shares, excluded ones included ("median over the six shares"). |
| O-02 | If the dip-sleeve state is unknown (at init), the **dip-ON** family weights are used. They give the smaller trend weight, which is conservative. |
| O-03 | **[needs spec owner]** When no volatility estimate exists (M0 has no data), sigma_i = floor_i. That is the *largest* possible scale, so this check is a necessary but not sufficient test. The function takes live estimates (`vol_estimates`), and the runner must pass them once M1/M2 data exist. With the defaults, the result at A$50,000 is A$4,166.67, which passes (consistent with §9's "about A$50,000"). |
| O-04 | Sizing NAV for validation, when no live NAV is available, = min(`backtest.initial_nav`, `capital_cap_aud`). It can be overridden with `--sizing-nav`. |
| O-05 | **Hard** at `trader init` and whenever the config hash is not among the known hashes. `trader validate-config` is the change-time check, so it is always hard (warning only in small-account mode, D-02). Other startups give a **warning** string for the evening report. |

## Calendar and events (§5, OPS-05)

| # | Decision |
| --- | --- |
| K-01 | The `calendar` table is seeded **1 Nov 2026 – 31 Dec 2027** (migration 0003), one row per calendar day. Weekends and the listed closures are closed. Listed early closes close at 14:10. Every other weekday closes at **16:10** (closing single price auction; the spec gives only the half-day time). |
| K-02 | The calendar module has **no** holiday list, weekday rule or holiday library. A date outside the table raises `CalendarGapError` and is never guessed. The backtest (M1/M3) will need historical ASX calendars loaded into the table. |
| K-03 | Events seeded (migration 0004): BHP Dec-quarter review on 19 Jan 2027 (estimate). BHP half-year results on **both 16 Feb and 23 Feb 2027** as estimates, because sources disagree and extra blackout days only block buys. BHP interim ex-dividend on 4 Mar 2027 (estimate, no blackout). **CBA results on 10 Feb 2027 seeded as an estimate**: the spec says "No *(verify)*", so it stays an estimate until verified, which widens the blackout. RBA decisions are stored on day 2 (9 Feb, 23 Mar, 4 May 2027) with `symbol = NULL`, flag only. CSL, RIO, FMG and WDS dates are "TBC" and **not seeded**. |
| K-04 | Blackout offsets are counted in **trading days** on execution dates, widened by `estimate_widen` trading days each side for estimates. If V is not a trading day, the window runs from the previous trading day (lower end) to the next trading day (upper end). |

## Ledger and data model (§12)

| # | Decision |
| --- | --- |
| L-01 | All 28 §12 tables are created by migration 0001 and match the models exactly (a test diffs them). Migrations are **forward-only**: every `downgrade()` raises. |
| L-02 | **Mutability**: only `runs.state`, `order_intents.status`, `broker_orders.status`, `parcels.qty_open` and every column of `flags` can be updated, and each update writes an `audit_log` row (`update_mutable`). Deletes are never allowed. This is enforced three ways: an ORM `before_flush` guard; Postgres grants for the app role (SELECT and INSERT on every table, column-level UPDATE only on the columns above, no DELETE or TRUNCATE); and, for `audit_log`, INSERT-only for the app role plus a trigger that rejects UPDATE, DELETE and TRUNCATE for **every** role, the owner included. |
| L-03 | **[needs spec owner]** Strict reading of L-02 conflicts with later milestones. §9 says `execution.finalise_vas()` sets the VAS **limit price at 10:45**, but `order_intents.limit_price` is not mutable. `broker_orders.cancelled_at` and `runs.reason_code` are also not in the mutable list. M0 keeps them insert-only. M4/M5 must record these as new rows (or in `audit_log`), or the spec must add them to the mutable list. |
| L-04 | "The app role has INSERT only" on `audit_log` is read literally: **no SELECT**, so audit inserts never use `RETURNING`. Reading the audit log for reports will need a separate read-only role (M6). |
| L-05 | The migration creates the app role as `NOLOGIN` if it does not exist. The name comes from `-x app_role=` / `TRADER_DB_APP_ROLE`, default `trader_app` (e.g. `trader_a` per user). Login roles and passwords are provisioned by ops (M5). Any later migration that adds a table must add its grants the same way. |
| L-06 | Columns added beyond §12's lists, where the spec names a table but not all its columns or a key needs them: `order_intents.execution_date` (for the "unique per user, E, symbol, side, ladder step" key; each user has their own database, so `user` is implicit); `runs.created_at`, `plans.created_at`, `recon.checked_at`, `trials.created_at`; `flags (name, value, actor, reason, updated_at)`; `vetoes (execution_date, symbol, side, received_at, channel, actor)`; `alerts (ts, level, type, reason_code, msg, channel)`; `plans.run_id`. Weights and units are `NUMERIC` (exact, so stored plans reproduce exactly); signal values are double precision (signal maths). |
| L-07 | Not done in M0: the `shared_board` database and intent board (not in the §12 table list; USR-02, M5), and seeding `instruments` (needs `conId` from `qualifyContracts`, SYS-20, M1). |

## Logging (MON-03)

| # | Decision |
| --- | --- |
| G-01 | Every line has exactly the 11 MON-03 keys in order, with missing values as `null`. `ts` is UTC ISO-8601 with millisecond precision and a `Z` suffix. Unknown context fields are a programming error. `Decimal` is logged as a string. |
| G-02 | Account numbers are masked to the prefix plus the last 3 digits (`U1234567` → `U****567`). Secrets are redacted by key name, by `SecretValue`, and by value patterns in free text (tokens, DSN passwords, `key=value` pairs, bearer tokens). |
| G-03 | Retention: daily rotation at UTC midnight with 90 backups (`LOG_RETENTION_DAYS`). The audit log in the database is permanent. |

## CLI

| # | Decision |
| --- | --- |
| X-01 | All §3 commands plus `mode` (D-01, D-02) are registered. Implemented in M0: `validate-config`, `migrate`, and the config hard checks of `init`. Every other command prints `trader <cmd>: not implemented in M0 (planned for Mx).` and exits **69** (`EX_UNAVAILABLE`). Exit codes: 0 OK, 2 invalid config, 3 approval-pin mismatch. |
| X-02 | `trader secret set` will read the value from stdin, never from argv (M5). |
