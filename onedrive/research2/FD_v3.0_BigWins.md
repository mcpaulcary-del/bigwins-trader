# Big Wins — Functional Design v3.0

19 November 2026 · Author: research agent (Fable) · Status: **BUILD DOCUMENT.** The owner decided D-1 to D-7 on 19 Nov 2026 (`OWNER_DECISIONS_2026-11-19.md`; section 2). Supersedes FD v2.13 for the `asx-trader` repository; the v2.13 freeze is lifted.
Companion: `85_full_review_and_direction_fable.md` (the review, the six tests behind this design, and the gap register).
General information, not financial or tax advice. **Real money only as section 18 allows: by owner override of 19 Nov 2026, one A$10,000 slice in EMG2-20 from mid-December 2026 (sections 7.9, 18.4, 21.1); everything else is paper. No AI or model output may create, size, approve or modify an order.**

---

## 0. Document control and how to read

| Item | Value |
|---|---|
| Product | **Big Wins**: an ASX share-picking system that tries to hold big winners while they are still small, and learns from every forecast it makes |
| What it replaces | The two-ETF index-timing system of FD v2.13 (rule L1). L1, its sleeves, tranches, benchmarks B1–B3 and the sizing and multi-market chapters are **withdrawn** |
| What it reuses | The repository's M0 and M1 (config, calendar, two databases, raw store, EODHD connector, Flex parser, quality checks, logging) and v2.13's trade-path engineering, by reference (section 0.2) |
| Benchmark | The ASX 200 fund (A200, A$0 brokerage, never sold). Index funds are the yardstick only; they are not a product of this system |
| Honesty rule | No report states or implies a return advantage that the forward record has not shown. Every figure is labelled back-test, paper or real |
| Language and stack | Python 3.12, PostgreSQL 16, Alembic, APScheduler, Docker Compose, `ib_async` (as M0/M1) |
| Paths | `$B` = the research scratchpad; `$R` = `$B/onedrive/research2`; `$F` = `$R/68_forward_record`; repo = `/home/user/asx-trader` |

### 0.1 Requirement IDs

New requirements are `BW-<AREA>-<nn>`: SYS, UNI (universe), DAT, STR (strategy lines), NL (new listings), PRT (portfolio), RSK, EXE, APR (approval), LED, TAX, LRN (learning loop), RND (research), MON, GAT (gates), INF, OPS. Every requirement is MUST unless it says SHOULD. Each maps to at least one automated test named after its ID (v2.13 CA-14 carried: `requirements.csv`). A number marked **[design]** is an operating choice held in config; **[tested]** comes from a named report or test; **[unverified]** blocks the gate named beside it.

### 0.2 What carries over from v2.13 by reference

These v2.13 requirements stay in force with "sleeve" read as "symbol" and "tranche" deleted. A build agent implements them from v2.13's text.

| Kept | v2.13 IDs |
|---|---|
| Purity, determinism, same code in harness and live, Decimal money, UTC, audit record, truncation invariance, import walls | SYS-10 to SYS-18 |
| Idempotent jobs, advisory lock, restart rules, calendar table, no close read before 16:25 | OPS-01, OPS-02, OPS-05, OPS-08, CA-15 |
| Raw store, hashes, bitemporal tables, verdict levels, licence guard, dead-man | DAT-03, DAT-06, DAT-08, DAT-09, DAT-10, DAT-12, DAT-15 (amended in §6.5), DAT-17, DAT-18, DAT-21 |
| Breaker basics: kill and halt classes, no short, no buy and sell together, tick validity, cash check, pause and kill | RSK-01 to RSK-04, RSK-09, RSK-10, RSK-25, RSK-34 |
| Order plumbing: route ASX, whole units, persisted intent before send, idempotent on `client_order_id`, no resend on timeout, crash-injection tests, paper/live account guard, sells before buys, settled cash only | EXE-01, EXE-03, EXE-04, EXE-06, EXE-08, EXE-09, EXE-10, EXE-12, BP-01 to BP-04, BP-17 to BP-20, CA-01, CA-06 |
| Ledger checks against the broker | LED-01 to LED-06 |
| Parcels, 12-month dates, 45-day franking test, reason codes, retention, facts bundle | TAX-01, TAX-02, TAX-03, TAX-07 to TAX-09, TAX-11, TAX-18 |
| Digest, heartbeat, JSON logs, alert classes, fault-injection of every alert | MON-01, MON-03, MON-05, MON-06, MON-16, BP-12, BP-13 |
| Infrastructure and hardening | INF-01 to INF-03, INF-09, INF-10, BP-05 to BP-11, BP-16, CA-03, CA-07, CA-09, CA-10, CA-12 |
| Research discipline | RND-002 to RND-004, RND-006, RND-011, RND-016 |
| Learning whitelist mechanics | LRN-10, LRN-11, LRN-13, LRN-28 |

**Withdrawn:** everything else in v2.13, in particular sections 1.1, 9, 16, 17, 26, 27, 30, 31; EXE-02's ban is kept (no market orders) but **EXE-07 (no auction orders), RSK-11 (6 orders a day), DAT-23 (20 vendor calls a day), OPS-19 (freeze), OPS-20(c) (A$150 cost ceiling) and section 17.1 are replaced** by this document.

### 0.3 Precedence

For a registered strategy line, the **frozen rule file named in section 7 wins over this document**. This FD describes how lines are run, scored, compared and gated; it never changes a line's rules. If this FD and a frozen rule file disagree, the build agent raises it; it does not choose.

---

## 1. Scope, objective and success criteria

### 1.1 Objective

Find and hold ASX shares that become big winners, at a cost in risk the owner has accepted in writing, and prove or disprove on forward data that doing so beats holding the ASX 200 fund after costs and tax.

### 1.2 In scope

- Every ASX-listed ordinary share with usable liquidity (about 2,000 codes scanned daily; about 600 eligible), including delisted and renamed companies in history.
- A registry of strategy lines run side by side on paper: the registered baseline H82, the shadow lines M3, E3, ACC and CXL, the lead challenger EMG2, the new-listings line EARLY when registered, the June sleeve H100, and measurement lines.
- A prediction ledger: every registered forecaster's scores are written when made and scored when their horizon passes, every trading day and at four intraday ticks.
- Execution on the IBKR **paper** account first; real money only through section 18.
- An approval queue, tax engine, hash-chained ledger and pre-registration register.
- A research harness that counts every trial.

### 1.3 Out of scope

- Index-fund timing, asset allocation, the owner's external index account (the system holds no login for it and never trades it).
- Short selling, leverage, margin, options, CFDs, futures, crypto, foreign listings.
- Intraday trading decisions (section 15.2 says what the intraday ticks may and may not do).
- The 14-market forward record of report 78: it keeps running as scripts outside this system and is not ported (BW-STR-12).
- Anything that lets an AI agent or a learned model change a live rule, a limit or an order.

### 1.4 Success criteria

| ID | Criterion | Measured |
|---|---|---|
| BW-SYS-01 | The system runs every ASX trading day with no manual action other than approvals in `pilot`/`live` mode | Gate G2: 60 trading days |
| BW-SYS-02 | Every line's decisions equal an independent replay from stored data (same lists, same orders) | Daily replay job; parity tests B3 |
| BW-SYS-03 | Positions match the broker to the unit and cash to the cent after every broker day | LED checks |
| BW-SYS-04 | No order breaks a risk limit; no order exists without a persisted, risk-approved, (in real-money modes) owner-approved intent | Tests; audit |
| BW-SYS-05 | Every forecast is stored before its outcome exists and scored exactly once per horizon | Ledger tests; hash chain |
| BW-SYS-06 | **Product success** is defined only by the adopt rule in force (section 18.3): after costs and tax, against the A200 fund, on forward data. Until then every report carries the banner "Not shown to beat the index" | Scorecard |
| BW-SYS-07 | No AI or model output can create, size, approve or modify an order (v2.13 SYS-06 carried: import test, permissions, egress allow-list) | Tests |

### 1.5 Realistic expectations (planning figures; none is a promise)

| Item | Expectation | Source |
|---|---|---|
| H82, M3, E3, ACC, CXL | Level with the A200 fund within about 1.5 points a year; true edge about +0.2 | Reports 80–82 |
| EMG2 | Back-test, data previously seen: 13.3% a year after spreads and yearly tax against 8.5% for the index (2018–Oct 2026), 11.0% against 7.4% (2010–2017). With history halved and spreads doubled: about +1. Forward estimate +1 to +3 a year if it holds; zero is quite possible. Chance of a true edge of +1 or more: about 35–40% [judgement] | Report 85 T4–T6 |
| EMG2 ride | Tracking error 20–25 points a year; worst falls 38% and 57% in back-test; expect a year 25 points behind the index within any five | Report 85 T6 |
| New listings, unselected | Median −18% in 12 months; 36% halve; 18% double | Tracker baseline 2014–2025 |
| How fast evidence arrives | Signal level (band spread): t = 2 in about 21 months if history repeats, 7 years at half strength. Book against index: decades | Report 85 §0.3 |
| EMG2-20 live slice (A$10,000) | Brokerage about A$840–930 a year at IBKR's A$6.60 minimum (about 140 trades), i.e. 8–9% of the capital, before spreads and tax. Even if the back-test lead (+4.9 a year) held in full, the expected result at this size is **below the index**. The slice buys knowledge of real fills and costs, not expected profit | Section 7.9; T6 trade count |
| Cost of running | About A$700–900 a year all-in on paper (section 19; approved, D-7) | Section 19 |

---

## 2. Decision log

| # | Decision | Status |
|---|---|---|
| D-1 | FD v3.0 replaces v2.13; the freeze (OPS-19) and "no new card before November 2027" are lifted | **Owner: yes, 19 Nov 2026** |
| D-2 | EMG2 is the lead challenger, on paper from the 30 Nov 2026 decision; H82 is reported as "large-company control" | **Owner: yes** |
| D-3 | Adopt rule v3 (section 18.3) for lines with tracking error above 10 points; v2 stays for index-like lines | **Owner: yes** |
| D-4 | Pilot cap | **Owner: A$10,000** (and never more than 5% of investable assets, which the owner declares at gate G3) |
| D-5 | Broker | IBKR, paper first (standing choice). Real-money broker for small shares confirmed at gate G3 after open items O-1, O-2 |
| D-6 | A lawful source of ASX announcements | **Owner: yes if lawful and under about A$50 a month; the owner confirms before any purchase.** Until a feed is named, announcement forecasters stay unbuilt (open item O-5) |
| D-7 | Budget (section 19): about A$700–900 a year | **Owner: yes** |
| D-12 | **Owner override of adopt rule v3 step P1 (19 Nov 2026, later the same day): real money A$10,000 in EMG2, 20-company version, automated through IBKR, from mid-December 2026 after one paper month.** The owner was shown that IBKR brokerage is about A$840–930 a year at this size (8–9% of the capital, more than the estimated edge) and chose it. Safety defaults kept: approval of each order for the first months, hard loss limits, kill switch, paper and live side by side, v3 stop rules. The author's recommendation was 12 months of paper first; this document implements the owner's decision and states the cost plainly wherever the live slice appears | **Owner: decided** |
| D-8 | Closing-auction execution (limit-on-close) replaces v2.13's "never in an auction" | Decided here; follows every frozen rule file ("fills at the close") |
| D-9 | Approval is **required** for every real-money batch; paper is auto-approved | Decided here |
| D-10 | One engine of record inside the repository; the scripts in `$B/bigwins_forward/code` stay the engine of record for each line until that line passes its parity test (BW-STR-10) | Decided here |
| D-11 | Sells of a registered line are never blocked by a discretionary veto in paper; in real-money modes an unapproved batch lapses whole | Decided here |

---

## 3. Architecture

### 3.1 Pipeline

1. **Fetch** (evening): EODHD bulk end-of-day for the AU exchange, symbol list, splits and dividends; ASIC short-position file; analyst-estimate snapshots; new-listings tracker.
2. **Validate** (evening): data verdict per symbol (section 6.4). Corporate-action and identity maps (renames, `_old`, duplicates) rebuilt.
3. **Universe and features**: liquidity ranks, bands, security classes, the feature store (sections 5 and 6.3).
4. **Forecast**: every registered forecaster writes its scores to the prediction ledger (section 15.3).
5. **Resolve**: forecasts whose horizon ended today are scored; scoreboards updated.
6. **Decide**: each line whose clock says today is a decision day runs its pure `decide()` and writes targets and order intents.
7. **Risk**: the independent breaker approves, clips or rejects each intent.
8. **Approve**: paper: automatic. Pilot/live: the owner approves the batch (section 12).
9. **Execute** (next session): limit-on-close orders; fills recorded; reconciliation.
10. **Book**: parcels, cash, NAV, tax, twins and comparators marked; ledger entry hashed and chained.
11. **Report**: digest, scorecard, champion/challenger table, alerts.
12. **Intraday ticks** (four a session): quotes, alerts, intraday forecasts and resolutions, safety cancels. Never a new decision.

### 3.2 Package layout (additions to the M0/M1 tree; `rules/l1.py` and `benchmarks.py` B1–B3 are deleted)

```text
trader/
  config.py  calendar.py  ledger.py  db.py  jsonlog.py  money.py  secrets.py   # M0, extended
  data/
    eodhd.py           # M1 connector; DAT-23 budget replaced by BW-DAT-02
    eodhd_bulk.py      # NEW bulk EOD, symbol list, splits/dividends, delayed quotes, fundamentals, estimates
    asic.py            # NEW daily short-position files (shares on issue, short interest)
    identity.py        # NEW renames, _old codes, duplicate test A7(c), code re-use A8, security class
    store.py quality.py totalreturn.py flex.py snapshot.py    # M1, thresholds per §6.4
    intraday.py        # NEW tick snapshots
    newlist.py         # NEW new-listings tracker (port of newlist_tracker.py)
  universe.py          # NEW bands, eligibility, PIT universe tables
  features.py          # NEW feature store (pure functions of PIT data)
  forecast/
    registry.py        # forecaster definitions (frozen, hashed)
    pledger.py         # prediction ledger: write, resolve, score
    forecasters/       # one module per forecaster
  lines/
    base.py            # Line protocol: clock(), decide(), build_orders()
    h82.py m3.py e3.py acc.py cxl.py emg2.py early.py h100.py
    twins.py           # random twin books
    measure.py         # band-spread and avoid-list measurement lines
  books.py             # one book per (line, size, account): parcels, cash, NAV
  risk.py  orders.py  execution.py  reconcile.py  tax.py
  approval.py          # NEW approval queue
  hashchain.py         # NEW ledger hash chain and pre-registration register
  learn/
    scoreboard.py      # forecaster scoreboards
    challenger.py      # champion/challenger table, gate evaluation, proposal writer
    costs.py           # learned cost table (whitelist)
  broker/ base.py ibkr.py paper_sim.py
  research/ registry.py harness.py costs.py taxsim.py pack.py backlog.py
  monitor.py report.py runner.py cli.py
```

### 3.3 Core interfaces (behaviour binding; names may be refined)

```python
@dataclass(frozen=True)
class PitData:                       # everything a pure function may see for session D
    as_of: date                      # session D; no row dated after D (BW-SYS-12 raises otherwise)
    px: PriceStore                   # raw close, volume, split-neutral returns r and rt (rules v1.3 A3), per entity
    universe: UniverseTable          # §5: entity, band, tv_rank, tv_med252, tv_med63, sec_class, listed_on, verdict
    shares: dict[str, int]           # ASIC total product in issue, latest file <= D (with file date)
    short_pct: dict[str, float]
    estimates: EstimateStore         # PIT snapshots <= D
    newlist: NewListTable            # §8
    code_map: dict[str, str]         # old code -> current code (A7, A9)

class Forecaster(Protocol):
    id: str; version_hash: str; cadence: str            # 'daily' | 'tick' | 'monthly' | 'yearly'
    horizons: tuple[str, ...]                           # e.g. ('5D','21D','63D')
    universe_tag: str                                   # e.g. 'BAND_C'
    def score(self, pit: PitData, tick: str | None) -> dict[str, float]: ...   # pure; entity -> score (higher = better)

class Line(Protocol):
    id: str; rules_file: str; rules_sha256: str
    def is_decision_day(self, d: date, cal: Calendar) -> bool: ...
    def decide(self, pit: PitData, book: Book, state: LineState) -> Decision: ...        # pure
    def build_orders(self, decision: Decision, book: Book, pit: PitData) -> list[OrderIntent]: ...  # pure

@dataclass(frozen=True)
class Decision:
    line: str; as_of: date; targets: dict[str, TargetRow]; sells: tuple[str, ...]; buys: tuple[str, ...]
    next_state: LineState; detail: dict            # full ranked table, reasons, hashes of inputs

@dataclass(frozen=True)
class OrderIntent:                   # v2.13 fields plus:
    line: str; book: str; order_type: str          # 'LOC' | 'LMT'
    ref_price: Decimal; limit_price: Decimal | None; max_participation: Decimal
    batch_id: str; reason: str                     # reason code, e.g. 'EMG2_OFF_LIST', 'EMG2_NEW_ENTRY'
```

| ID | Requirement |
|---|---|
| BW-SYS-10 | `score()`, `decide()` and `build_orders()` are pure and deterministic: the same `PitData`, book and state give byte-identical output (JSON, sorted keys, 10 significant digits) |
| BW-SYS-11 | The harness, the daily runner and the replay job call the same functions. There is one engine of record |
| BW-SYS-12 | `PitData` raises if any row is dated after `as_of` or has no data verdict. Truncation invariance is tested for every forecaster and line on 50 random historical dates |
| BW-SYS-13 | Modules under `forecast/`, `learn/`, `research/`, `data/`, `monitor.py`, `report.py` have no import path to `Broker.place` (import test) |
| BW-SYS-14 | Every line and every forecaster is identified by the SHA-256 of its rules file or definition. Config pins those hashes. The runner refuses to run a line whose code hash is not registered in the hash chain (section 13) |
| BW-SYS-15 | Random twins and comparators run in the same engine and the same daily job as the line they shadow |

### 3.4 Modes

| Mode | Broker | Fills | Approval | Real money | Opens at |
|---|---|---|---|---|---|
| `advisory` | None | Simulated at the next session's close with the line's own cost rule | Automatic | No | Gate G1 |
| `paper_auto` | IBKR paper (`DU…` account) for **one** book; all other books simulated | IBKR paper fills for that book; simulated for the rest | Automatic | No | Gate G2 |
| `pilot` | IBKR live (or the broker confirmed at G3), one book, capped | Real | **Required** | Yes, at most A$10,000 (D-4) | Gate G3 |
| `live` | Same | Real | **Required** | Yes | Gates G4, G5 |

BW-SYS-16: config validation refuses `pilot` or `live` unless the gate record for it exists in the ledger with the owner's second-factor signature, and refuses any `capital_cap_aud` above the amount on that record.

---

## 4. Schedules (Australia/Sydney; ASX trading days unless stated)

### 4.1 Intraday ticks

| Tick | Time | Job |
|---|---|---|
| I1 | 10:30 | `tick` (section 15.2) |
| I2 | 12:30 | `tick` |
| I3 | 14:30 | `tick`; pre-auction checks on today's pending orders (halts, price band); safety cancels |
| X1 | 15:45 | `submit_loc`: limit-on-close orders for today's execution batch (section 11) |
| I4 | 16:20 | `tick`; collect auction fills; `reconcile_broker` at 16:30 |

### 4.2 Daily

| Time | Job | Output |
|---|---|---|
| 16:30 | `reconcile_broker` (broker days) | LED-01 to LED-06 |
| 19:30, 21:30, 07:00 next day | `fetch_eod` (retry ladder) | Raw files, manifest |
| 19:40 | `fetch_asic`, `fetch_estimates`, `newlist_daily` | Raw files; `NEWLIST.md`; new-listing alert |
| 21:40 | `validate` | Verdicts; identity maps |
| 21:50 | `universe_features` | `universe`, `feature` tables for D |
| 22:00 | `forecast_daily` | Rows in `forecast` |
| 22:10 | `resolve_daily` | Rows in `forecast_outcome`; `forecaster_scorecard` |
| 22:20 | `decide` (lines whose clock fires) then `risk_plan` | `decision`, `order_intent` (status `PLANNED`), batch |
| 22:30 | `book_day` | Fills booked, NAV, twins, comparators, tax; `ledger_entry` hashed |
| 22:40 | `replay_check` | Independent replay equals today's decisions, or PAGE |
| 22:45 | `report_daily` | Digest (Telegram), `SCORECARD.md`, `LEARNING_DAILY.md`, approval request if a batch exists |
| 01:30 | `backup` | Encrypted off-site copy |
| 20:00 every calendar day | `heartbeat` | Dead-man check-in |

If the 21:30 fetch has no complete bar set, the chain from `validate` on is re-run after the 07:00 fetch (08:00–09:00) and the batch is planned then; the execution session does not change.

### 4.3 Weekly, monthly, quarterly, yearly

| When | Job | Output |
|---|---|---|
| Sunday 03:00 | `full_redownload` (restatement check, DAT-10) | Restatement report; automatic recompute of affected features, forecasts flagged `restated` (never rewritten) |
| Saturday 06:00 | `learn_weekly` | `LEARNING_WEEKLY.md` (section 15.4) |
| First Saturday of the month 06:00 | `learn_monthly`, `challenger_monthly`, `cost_learn` | `CHAMPION_CHALLENGER.md`; learned cost table version; research-cycle trigger |
| First Saturday 08:00 | `research_cycle` (agent, off the trade path) | Up to two pre-registered cards (section 16) |
| First Sunday of Jan, Apr, Jul, Oct | `learn_quarterly` | "What the system learned" report; forecaster retirements; backlog re-ranking |
| Last trading day of December, 22:20 chain | `gate_review` | Gate evaluation for every line (section 18); proposal documents if any bar is met |
| 30 June after the close | `tax_year_end` | Year report, facts bundle |

BW-OPS-01: every job is idempotent and holds the advisory lock of v2.13 OPS-01. BW-OPS-02: learning and research jobs never run within 2 hours of X1 and hold no broker handle (LRN-28 carried).

---

## 5. Universe and instruments

### 5.1 Identity and security class

| ID | Requirement |
|---|---|
| BW-UNI-01 | **Entities, not codes.** Every price row belongs to an entity. A code re-used after a gap of more than 200 calendar days is a new entity (rules v1.3 A8). Vendor codes `XXX_old`, `XXX_oldN` are admitted (Amendment v1.5). |
| BW-UNI-02 | **Duplicates.** Renamed companies carried under two codes are merged by the daily-return test A7(c) of Amendment v1.6 (Pearson ≥ 0.995 on days both traded that day and the day before; ≥ 120 common days; ≥ 100 non-zero), applied to **every** AU ordinary share, including `_old` against its base code. The pair list is written every run and is the code-change map. A holding under the old code continues under the new one with parcels unchanged (A9). |
| BW-UNI-03 | **Security class** per entity, stored with the fetch date: `ORD` (ordinary share or CDI of an operating company), `LIC` (listed investment company or trust; name and industry rules plus the manual list `config/lic_list.csv`), `REIT`, `FUND` (ETF, managed fund; the ETP list of rules v1.3 A4), `OTHER` (rights, options, notes, preference, deferred settlement), `DUAL` (first-seen market cap above A$1bn with a foreign primary listing; flagged, kept). Pick lists of every **new** line use `ORD` and `REIT` only. Frozen lines keep the class rule of their own rule file. |
| BW-UNI-04 | **Sector** and industry are stored with their fetch date. History before the first fetch is marked `as_known_at=<date>`; reports say so. |

### 5.2 Liquidity ranks and bands

| ID | Requirement |
|---|---|
| BW-UNI-10 | Traded value of a day = split-adjusted close × vendor volume (Amendment v1.4). `tv_med252` = median over the last 252 sessions with at least 120 valid days; `tv_med63` = median over 63 sessions with at least 30. Days without a row count as zero only inside a listed life. |
| BW-UNI-11 | `tv_rank` = rank of `tv_med252` among `ORD`, `REIT` and `LIC` entities that traded in the last 5 sessions. **Bands:** A 1–100, B 101–300, C 301–600, D 601 and below. The frozen lines keep their own universe definitions (top 300 with ≥ 200 closes in 252; top 100) from their rule files; the system computes both and tests that they agree with the forward record. |
| BW-UNI-12 | **Eligibility for new lines** (EMG2, EARLY, measurement): class per BW-UNI-03; raw close ≥ A$0.10; `tv_med63` ≥ A$100,000; traded in the last 5 sessions; data verdict not BLOCK; not suspended for more than 5 sessions. |
| BW-UNI-13 | The `universe` table is written once per session and never updated (bitemporal). A line reads the table of its decision day only. |

### 5.3 Corporate actions

| ID | Requirement |
|---|---|
| BW-UNI-20 | Split-neutral returns follow rules v1.3 A3 exactly (the nearest-row rule for vendor split dates). A unit-count anomaly between the vendor and the broker freezes the symbol (BP-06). |
| BW-UNI-21 | **Stopped trading.** A holding with no close for 20 sessions is paid out at its last close in simulated books (rules v1.3 C1) and flagged `PAYOUT_ASSUMED`. In a broker book it stays at the broker's value; for sizing it is valued at zero after 20 sessions. A delisting reason, when known, is stored. |
| BW-UNI-22 | **Takeover peg.** An entity whose closes over the last 10 sessions span less than 3% after a one-day rise of 15% or more is flagged `BID_PEG` (exact window: `AMENDMENT_shadow_EMG2.md` section 2). EMG2 uses the flag (section 7.6 rule 8); other lines ignore it. |
| BW-UNI-23 | Dividends: cash on the ex-date from the vendor's unadjusted value; franking percentage stored when the vendor supplies it, else `unknown`. |

---

## 6. Data

### 6.1 Sources

| Source | What | Access | Cadence | Credits a day (EODHD) |
|---|---|---|---|---|
| EODHD bulk EOD, AU | Open, high, low, close, volume for every AU symbol | `eod-bulk-last-day/AU` | Daily | about 100 |
| EODHD symbol list, AU, active and delisted | Codes, names, types, ISIN | `exchange-symbol-list/AU` (+ `delisted=1`) | Daily | 2 |
| EODHD splits and dividends bulk | Corporate actions | bulk `type=splits`, `type=dividends` | Daily | about 200 |
| EODHD per-symbol history | Full history for new, changed or restated symbols; Sunday re-download of the eligible set | `eod/<code>.AU` | Daily (deltas), weekly (about 700 symbols) | 20–100; Sunday about 2,100 |
| EODHD delayed quotes | Last, open, high, low, volume, previous close | `real-time/<code>.AU` multi-symbol | Four ticks | about 3,200 (800 symbols × 4) |
| EODHD fundamentals | General, highlights, shares, balance sheet, income statement | `fundamentals/<code>.AU` | New listings once, then at +126 and +252 sessions; band C best-fifth names monthly | 100–600 |
| EODHD analyst estimates | Earnings trend and estimates blocks | as `est_snapshot.py` | Daily for the 300-code set; weekly for band C | 300–3,000 |
| ASIC short-position reports | Reported short positions and **total product in issue** | Public daily CSV | Weekdays | 0 |
| IBKR | Quotes at order time, fills, positions, cash, Flex statements | API, Flex | Broker days | 0 |
| Announcements | Headline, release time, price-sensitive flag | **None until a licensed feed is named under D-6 (open item O-5)** | — | — |

Budget: about 5,000–8,000 credits a day against a plan limit of 100,000 **[unverified: plan name and price, open item O-4]**.

### 6.2 Requirements

| ID | Requirement |
|---|---|
| BW-DAT-01 | Every response is stored unchanged, gzip-compressed, with UTC time, endpoint, parameters without credentials, HTTP status, credits, bytes and SHA-256 in the manifest (M1 raw store). Nothing is fetched twice in a day unless the first response failed validation. |
| BW-DAT-02 | **Credit budget** replaces DAT-23: `data.eodhd.credits_per_day_max` = 20,000 [design]; the connector counts credits, refuses a job that would exceed the budget, and pages. A job that would leave fewer than 25,000 of the plan's daily credits aborts. |
| BW-DAT-03 | **Delisted and `_old`.** The symbol list is fetched with and without the delisted flag every day. A code that leaves the active list keeps its history; the first day it is missing from the bulk file starts the BW-UNI-21 clock. |
| BW-DAT-04 | **ASIC.** Each weekday the newest files are archived (name, position date, version, SHA-256). Shares on issue for a decision = the file with the latest position date on or before the decision day, not older than 45 days (CXL rule 3). Share-count change over 252 sessions is a feature. |
| BW-DAT-05 | **Estimates are point-in-time by construction.** The system never back-fills an estimate. An estimate feature for day D uses only snapshots taken on or before D. Vendor "actual" fields are not trusted for surprise calculations (report 79). |
| BW-DAT-06 | **Fundamentals are snapshots.** Each fetch is stored with its fetch date; features use the latest snapshot on or before D. No fundamentals feature may be back-tested on snapshots fetched after the test window. |
| BW-DAT-07 | **Intraday snapshots.** At each tick: delayed quotes for the watch set W = all holdings and pending orders of every book, every current target list, every eligible entity in bands A–C, every tracked new listing, A200 and BGBL. Stored in `tick_quote` (session, tick, entity, last, open, high, low, volume, prev_close, quote_time, fetched_at). A quote older than 40 minutes at fetch is marked stale. |
| BW-DAT-08 | **No ASX-website access** (DAT-15 carried) unless a licensed feed is named under D-6; then a connector `data/announce.py` with the same raw-store rules. A CI test fails if code requests `asx.com.au`. |
| BW-DAT-09 | **Durable storage.** The raw store, both databases and the forward record live on a persistent volume with a daily encrypted off-site copy and a restore test each quarter (BP-16). Nothing the record depends on may live only in a scratch or temp directory. Free disk below 15% pages. |
| BW-DAT-10 | **Migration of the existing record.** `trader import forward-record` loads, read-only and with hashes checked against `LEDGER.jsonl`: all 26+ ledger entries, the amendments, manifests, score files, paper state (`state.json`, `shadow_state.json`, `accum_state.json`, `cxl_state.json`, `score_state.json`), order files, the intraday archive, estimate snapshots, the ASIC archive and the new-listings store. The old hash chain is continued, not restarted. |

### 6.3 Feature store

Pure functions of `PitData`, stored per (session, entity, feature, version). Initial set, all with exact definitions in `trader/features.py` docstrings and unit tests against the frozen record's score files:

| Feature | Definition |
|---|---|
| `s1` | Total return from 252 to 21 sessions before D (at least 150 valid days) |
| `s2` | Total return over the last 126 sessions (at least 80 valid days) |
| `s3` | Total-return index ÷ its highest value of the last 252 sessions (at least 200) |
| `s4` | Minus the standard deviation of daily returns over 252 sessions (rules v1.3 form, for H82 only) |
| `m3_<set>` | Mean of the percentiles of `s1`, `s2`, `s3` inside the named set (`TOP100`, `BAND_B`, `BAND_C`, `ELIG600`) |
| `h82` | Rules v1.3 score (four percentiles, top 300) |
| `rm` | Residual momentum: sum of residuals of a 252-session regression of the entity's daily return on the A200 proxy's, over sessions −252 to −21, divided by the residual standard deviation |
| `tv_med63`, `tv_med252`, `tv_rank`, `band` | Section 5.2 |
| `shares_chg252` | ASIC shares on issue ÷ value 252 sessions earlier − 1 |
| `short_pct`, `short_chg20` | ASIC short % of issue and its 20-session change |
| `ret3y` | Total return over 756 sessions (at least 600 valid) |
| `cat_up`, `cat_dn` | Report 85 T2/T3 event flags |
| `bid_peg` | BW-UNI-22 |
| `age_sessions` | Sessions since the entity's first price row |
| `est_rev30` | Change in the vendor's next-year EPS estimate over 30 calendar days, from PIT snapshots (missing until two snapshots exist 30 days apart) |
| Tick features | `ret_from_prev_close`, `ret_from_open`, `vol_vs_med63` (tick volume ÷ `tv_med63` share-equivalent), `range_pos` (position of last in the day's range) |

### 6.4 Data verdicts

| Check | Rule | Verdict |
|---|---|---|
| Freshness | No bar for D by the 07:00 fetch while the entity is active and not flagged suspended | BLOCK for that entity |
| Sanity | Price > 0; high ≥ max(open, close); low ≤ min(open, close); volume ≥ 0 | BLOCK |
| Spike | Absolute daily return above 60% **and** no split, no `cat_up`/`cat_dn` volume confirmation (volume below the 63-session median) | WARN; BLOCK for buys |
| Split residual | A vendor split whose nearest-row test (A3) fails | BLOCK until `trader qc override` |
| Restatement | Sunday re-download changes a stored close by more than 0.5% on more than 5 rows of an entity, or changes a decision input of a past decision | WARN; decision-input changes are listed in the weekly report and trigger recompute (BW-RND-09) |
| Cross-source | For entities held in a broker book: vendor close vs Flex mark, 0.5% WARN, 2% BLOCK | as stated |
| Market-wide | Fewer than 90% of the eligible set have a bar | Whole run: no decision; retry |
| Calendar | D not a trading day in `calendar` | Whole run skipped |
| Tick quotes | Missing, stale, non-positive, or more than 60% from the previous close | Tick ignored for that entity |

BW-DAT-20: no forecast and no decision uses a close without a verdict (DAT-21 carried). BW-DAT-21: thresholds are config values; a change is logged with the reason.

### 6.5 Licence

DAT-15 as amended: EODHD data are used under the owner's personal, non-commercial licence; stored only on the owner's machines; never published. Reports that leave the machine carry derived figures only. Sending extracts to the research agent under the owner's account is allowed (EODHD help page read for report 52).

---

## 7. Strategy lines

### 7.1 Registry

| Line | Role | Frozen rules (hash in the ledger) | Books (paper) | Clock | Engine of record today |
|---|---|---|---|---|---|
| **H82** | **Registered baseline** ("large-company control") | `$R/67_FINAL_RULES_v1.3.md` (SHA-256 `b38abcd7…`) + `AMENDMENT_start_now`, `v1.4_traded_value`, `v1.5_old_symbols`, `v1.6_dup_returns` | A$5k lifecycle (illustration), A$25k, A$100k; MOM and 200 RND controls per size | 31 December review; vacancy rules; daily booking | `bigwins_forward/code/paper_daily.py` |
| **M3** | Shadow | `AMENDMENT_shadow_M3_E3.md` + `AMENDMENT_shadow_M3_v1.1.md` (report 76 §6) | A$5k, A$25k, A$100k | Month-end | `paper_shadow.py` |
| **E3** | Shadow | `AMENDMENT_shadow_M3_E3.md` (report 73 §6) | same | Month-end | `paper_shadow.py` |
| **ACC** | Shadow (keep winners, accumulation) | `AMENDMENT_shadow_ACC_keep_winners.md` | A$5k + A$500 a month at A$0 and at E1 brokerage | Month-end | `paper_accum.py` |
| **CXL** | Shadow (cap-weighted, losers excluded) | `AMENDMENT_shadow_CXL_D2.md` + `AMENDMENT_shadow_CXL_v1.1_reading.md` | A$25k, A$100k; no-screen twin; 100 random-exclusion books per size | Month-end | `paper_cxl.py` |
| **EMG2** | **Lead challenger** (D-2) | `AMENDMENT_shadow_EMG2.md` — draft in `$B/deep85/`, to be registered before 30 Nov 2026; text = section 7.6 | A$100k, A$25k; 100 random twins per size | Month-end | to be written (section 7.7) |
| **EARLY** | New-listings shadow line (unproven) | `$R/84_AMENDMENT_shadow_EARLY.DRAFT.md`, to be registered as `AMENDMENT_shadow_EARLY.md`; section 8.5 | A$100k (A200 core + up to 25 young companies at 4%), A$25k, cost-stress book; controls C1s, C2s | Month-end | `deep84/code/early_ref.py` (reference) |
| **H100** | Seasonal sleeve (June tax-loss rebound) | Report 59 card H100, report 63; `bw13_h100.py` | One A$20k sleeve book, June 2027 | Yearly | `bw13_h100.py` |
| **BANDSPREAD** | Measurement (no book) | Section 7.8; registered with EMG2 | — | Month-end | — |
| **AVOID** | Measurement (no book) | `deep82/SPEC_avoid_list_measurement_line.md` (registered, pending) | — | Month-end | pending |
| Multi-market M3/EI10I/CW | External record | `AMENDMENT_forward_multimarket.md` | 68 books | Monthly | `paper_multi.py`; **not ported** |

| ID | Requirement |
|---|---|
| BW-STR-01 | The system implements each line **from its frozen rule file**, not from this summary. The rule file's SHA-256 is pinned in config. |
| BW-STR-02 | Cost and tax conventions inside a line's own book are the line's (for example v1.3 E1/E2). The system adds, for every line, a second scoring at **owner costs** (A$0 brokerage, learned spread) and an after-tax "kept" and "sold" reading (Amendment scoring v2). |
| BW-STR-03 | A line's rules never change. A changed rule is a new line with a new ID, a new registration and a new clock (RND-016 carried). |
| BW-STR-10 | **Parity before take-over.** For each line the native implementation runs beside the script that is the engine of record. It becomes the engine of record only after it reproduces the script's ranked tables, target lists and orders exactly (same codes, same share counts, NAV within A$0.01) for three consecutive decision dates and every daily booking between them, and the change is registered as an amendment ("engine of record: asx-trader commit <sha>"). Until then the system imports the script's outputs read-only (`orders_*.csv`, `targets_*.csv`, state files) and books them. |
| BW-STR-11 | Every line with a book has random twins in the same engine: same clock, sizing, costs and exits; entry order replaced by a seeded random order of the same candidate set (seeds stored). Count: 100 per size (H82 keeps its registered 200). |
| BW-STR-12 | The multi-market record is read-only to this system: its scorecard is linked from the monthly report and nothing else. No further research is spent on it. |

### 7.2–7.5 H82, M3, E3, ACC, CXL

Implemented from the files in the registry. Nothing is restated here, to avoid a second text of the rules. Three implementation notes the rule files and reports 77, 80 and 81 require:

1. H82's traded value follows v1.3 (close × volume) for decisions before 31 Dec 2026 and v1.4 after; `_old` admission and A7(c) from the dates in Amendments v1.5 and v1.6.
2. M3 sells a holding when it leaves the **100** most traded (the tested behaviour), per Amendment M3 v1.1; not 150.
3. CXL leads its reading with "CXL minus the median random-exclusion book" (v1.1).

### 7.6 EMG2 v1.0 — exact rules (text for `AMENDMENT_shadow_EMG2.md`)

Status when registered: **SHADOW / lead challenger; paper only; not adopted.** Evidence: report 85 T4 and T6 (fails the pre-set t bar; largest lead found; data previously seen). Expectation to print on its scorecard: "Back-test +4.9 a year after costs and yearly tax on seen data; forward estimate +1 to +3; zero is possible; falls of 40–60% are normal for this line."

1. **Clock.** Decide at each ASX month-end after the close, first decision Mon 30 Nov 2026. Trade at the close of the next trading day: sells first, then buys.
2. **Eligible set E.** Entities of class `ORD` or `REIT` (BW-UNI-03), duplicates merged (A7(c)), with `tv_rank` ≤ 600, `tv_med63` ≥ A$100,000, raw close ≥ A$0.10 on the decision day (or within the previous 5 sessions), traded in the last 5 sessions, and `s1`, `s2`, `s3` all present.
3. **Band C list.** C = members of E with `tv_rank` 301–600. Score = mean of the three percentiles of `s1`, `s2`, `s3` computed inside C (rank ÷ count, average ranks for ties). **Target list T = the top fifth of C by score** (score percentile above 0.8), best first; ties by higher `tv_med252`.
4. **Sell.** Every holding not on T is sold in full. No waiting rule, no tax-holding rule, no trim.
5. **Buy.** Parcel = NAV at the decision close ÷ number of names on T. Names on T not held are bought best first; each order = min(parcel, free cash after the day's estimated sale proceeds); an order under half a parcel is skipped. A name with no close on the fill day is skipped and may be bought at a later decision.
6. **No top-ups, no trims** except rule 9.
7. **Payouts.** A holding with no close for 20 sessions is paid out at its last close (BW-UNI-21).
8. **Bid peg.** A holding flagged `BID_PEG` on a decision day is sold at that decision whether or not it is on T, and is not bought while flagged. *(Not in the T6 back-test; added on the evidence of report 81 §6.3; it only frees slots.)*
9. **Single-name cap.** A holding above 10% of NAV at a decision is trimmed to 7.5%. *(Not in T6; a safety rule; expected to bind rarely.)*
10. **Costs in the line's own book.** Brokerage A$0. Half-spread per side = max(0.50% if `tv_rank` > 300, 0.25% if 101–300, 0.10% if ≤ 100; half an ASX price step ÷ price), price steps A$0.001 below A$0.10, A$0.005 below A$2, A$0.01 from A$2. Whole shares. Cash earns 0%. A second book per size at IBKR brokerage max(A$6.60, 0.088%) is kept as a cost stress.
11. **Tax in the scorecard** (not in the book's cash): 32%, 50% discount for parcels held 367 days or more, losses carried forward, FIFO parcels, dividends taxed; "kept" and "sold" readings (scoring v2).
12. **Books.** `EMG2_100k` (A$100,000 cash at the first decision), `EMG2_25k` (A$25,000; holds up to 25 names: buys the best-ranked names of T not held while fewer than 25 are held, parcel = NAV ÷ 25, sells a holding only when it is off T; information only), each with 100 random twins `EMG2_RND_<size>_s001…s100` (rule 3's order replaced by a persistent seeded random score per entity, redrawn with probability 0.2 a month; same count of names; seeds 8530000 + i and 8540000 + i), and comparators `EMG2_CMP_A200_<size>` at A$0 brokerage.
13. **Reading.** The scorecard line leads with (a) the forward band spread (section 7.8) and its t, (b) the book's percentile among its twins, (c) the book against A200 after tax, in that order.
14. **Data block.** If the universe table of a month-end has fewer than 150 names in C or the market-wide verdict fails, there is no decision that month; holdings are kept.

Differences from the T6 code (`$B/deep85/code/t6.py`), all stated in the amendment: daily booking and the record's conventions instead of a monthly loop; duplicates merged; class filter; rules 8 and 9; tax in the scorecard instead of paid from cash.

### 7.7 EMG2 before the system exists

The first decision is 30 Nov 2026. Until milestone B3, EMG2 runs as a script `bigwins_forward/code/paper_emg2.py`, written from section 7.6 by the record keeper, hashed into the ledger before 30 Nov, hooked into `paper_daily.py` after the CXL step, with its own state file `out/paper_state/emg2_state.json`. It then passes BW-STR-10 like the others.

### 7.8 BANDSPREAD measurement line (registered with EMG2)

Each month-end, for bands B and C separately, eligible set as rule 2 restricted to the band: `TOP` = top fifth by in-band M3 score, `BOT` = bottom fifth, `ALL` = the band, equal weights, returns from the next session's close to the close of the session after the following month-end, no costs. Recorded monthly: `TOP − ALL`, `BOT − ALL`, `TOP − A200`. Cumulative mean and t (monthly, Newey-West lag 1). No book, no decision. This is the fast evidence for EMG2 (history: `TOP − ALL` band C +16.9 a year, t 4.5, 2018–Oct 2026).

### 7.9 EMG2-20: the real-money variant (owner decision D-12) — text for `AMENDMENT_live_EMG2_20.md`

**Status: LIVE, real money, capped at A$10,000, by owner override of adopt rule v3 step P1. Not adopted on evidence.** The signal, clock, eligible set, band-C list and score are EMG2 v1.0 rules 1–3 unchanged. What differs is the number of names, the order rules that A$500 parcels force, and the costs.

| # | Rule |
|---|---|
| L1 | **Capital.** A$10,000 deposited once. `capital_cap_aud: 10000`: cash above the cap is never invested. No contributions are planned; any later deposit needs a new owner decision. |
| L2 | **Candidates.** T = EMG2's target list of the decision (top fifth of band C, best first). **Lottery-class names (section 8.6: listed under 504 sessions, close under A$0.20, or `tv_med63` under A$250,000) are skipped** for buying. *(A safety filter for real money; not in the back-test.)* |
| L3 | **Slots.** n = min(20, floor(account value ÷ A$500)). Parcel = account value ÷ n. |
| L4 | **Sell.** A holding is sold in full when it is **not on T** at a month-end decision (the whole top fifth, about 45 names, not just the best 20). So a holding that slips from 5th to 30th is kept. Also sold: a holding flagged `BID_PEG`; a payout arrives as cash. No trims, no top-ups, no stop-loss. |
| L5 | **Buy.** After the decision's sells, while fewer than n names are held: buy the best-ranked names of T that are not held and not skipped by L2, one parcel each. Order value = min(parcel, cash available − A$50 reserve) ÷ (1 for a single buy; cash is shared equally when several buys compete for less cash than their parcels). **An order under A$500 is not sent** (ASX minimum marketable parcel for a first purchase); its cash waits for the next decision. Whole shares, rounded down. |
| L6 | **Clock.** Regular decisions at each ASX month-end after the close, orders on the next session. **Start:** a start decision on the first session from Mon 14 Dec 2026 on which the go-live checklist (section 21.1) is signed, using that day's universe table and scores; a one-parcel canary buy of the top name on the next session; the other 19 buys the session after the canary reconciles. If the checklist is not signed by Fri 18 Dec, the start moves to the 31 Dec 2026 month-end decision (orders Mon 4 Jan 2027). After a December start before the 31st, the **31 Dec decision is skipped** for this book (holdings two weeks old); the first regular decision is Fri 29 Jan 2027. |
| L7 | **Execution.** Sells on session D+1. Buys on the first session, from D+1 to D+4, on which IBKR reports enough available funds for them (O-2); after D+4 a buy lapses. Order type: limit-on-close if the reality spike proves it for these shares (O-1); otherwise a DAY limit order sent at 15:30: buy at the ask plus one price step, not above reference × 1.03; sell at the bid minus one price step, not below reference × 0.97; reference = last trade at the 14:30 tick; unfilled at 15:58 is cancelled and carried one session (sells up to 3 sessions, then paged). |
| L8 | **Approval.** For the start and the first three regular decisions (to the April 2027 decision), **each order** needs the owner's `/ok <batch> <n> <code>` or `/ok <batch> all <code>` by 15:20 on the execution session; an order not approved is not sent. After that, batch approval (section 12) unless the owner extends per-order approval. |
| L9 | **Costs.** IBKR fixed pricing: max(A$6.60, 0.088%) a trade, so A$6.60 on every A$500 order (1.3% a side). Expected: about 140 trades and **A$840–930 a year**. The start costs about A$132. Spread as the learned table (start: 0.50% a side with the half-step floor). |
| L10 | **Hard limits (breaker, live book).** Order value ≤ A$800. Orders a day ≤ 24 on the start days, ≤ 16 otherwise. Buys a day ≤ A$10,500 on the start days, ≤ A$4,500 otherwise. Limit price inside the L7 band; reference more than 15% from the previous close: buy held one session. Order ≤ 5% of `tv_med20`. IBKR account precautions set to: maximum order value A$1,000, daily A$12,000. |
| L11 | **Loss limits.** Account value ≤ A$7,000: PAGE and review. **≤ A$6,000: `HALTED_BUYS`** (BW-RSK-29); the owner decides in writing to continue or close. ≤ A$5,000: line halted (BW-RSK-20). One-day fall of 12%: `HALTED_BUYS`. `/kill` stops everything in one step. A halt never sells by itself. |
| L12 | **Stop rules of adopt rule v3 apply** to this slice exactly as to the paper line: at a December review from 13 months after EMG2's registration, signal spread t ≤ −1.0, or the A$100k paper book below the 20th percentile of its twins, or (from 24 months) after tax more than 15 points a year behind A200: the slice is sold down over the next two decisions and closed. Scale-up beyond A$10,000 only by step P2 as written. |
| L13 | **Side by side.** A simulated twin `EMG2_20_SIM` runs the same rules from the 30 Nov 2026 decision at the same costs (the paper month), with 100 random twins; the IBKR paper account mirrors it from the first day the order path works. From the live start, live and simulated books are compared daily: fills, costs, holdings, value. A difference in holdings that is not explained by an unapproved or unfilled order is `HALTED_INTEGRITY`. |
| L14 | **Reporting.** Every report of this book carries: "Real money. Owner override of the 12-month paper step. Brokerage about 8–9% of capital a year. Expected result at this size is below the index even if the signal works." Monthly: value, deposits, brokerage paid to date in dollars and as a share of capital, realised and unrealised result, the same money in A200. |

---

## 8. New-listings module

### 8.1 Purpose

Young companies are where some big winners start and where most losers are. The module (a) sees every genuine new listing on its first day, (b) records its path and facts point-in-time, (c) tells the owner, (d) controls how and when a young company may enter any line, and (e) hosts the research line EARLY.

### 8.2 Data: the tracker

| ID | Requirement |
|---|---|
| BW-NL-01 | `data/newlist.py` is a port of `$B/bigwins_forward/code/newlist_tracker.py` and keeps its store `$B/bigwins_forward/data/newlist/` (imported under BW-DAT-10): `registry.csv`, `newlist_tracker.csv`, `newlist_other.csv`, `paths.csv.gz`, `fund.jsonl`, `daily/`, `snapshots/`, `run_log.csv`, and the report `paper/NEWLIST.md`. Daily at 19:40; about 80–110 credits. |
| BW-NL-02 | **Classification** of each new code: `new_listing` (three-letter ordinary share, history starts recently, no predecessor), `likely_rename` (same ISIN, or name-token Jaccard ≥ 0.5, as a vanished code; or carried-over history), `old_history`, `etf_fund`, `other_security`, `pending_first_trade`. **Fix required before reliance:** the ISIN column of `registry.csv` currently holds a method name, not the ISIN; until repaired, renames after May 2024 are detected by name only. Acceptance test: 20 known renames of 2024–2026 are classified `likely_rename`. |
| BW-NL-03 | **Facts at first sight.** One fundamentals snapshot per listing on detection (sector, industry, shares, revenue, net income, cash, debt, description), stamped with `fund_days_after_listing`; repeated at 126 and 252 sessions of age. Known limits, printed in the report: no offer price and no IPO date from the vendor (returns start at the first close); debt mostly missing; the snapshot is "at first sight", not "at listing". |
| BW-NL-04 | **Path.** Daily close, volume, traded value from the first row; derived: return since first close, maximum gain, maximum drawdown, `tv_med20`, day-1 traded value, market cap at first close (shares × close). |
| BW-NL-05 | **Baseline table** (descriptive, refreshed monthly): by listing year, share that halved or doubled within 12 months, median 12-month return against the ASX 200. Reference values at 19 Nov 2026: 1,089 listings 2014–2025; 36.5% halved; 18.2% doubled; median −17.9% against +3.2%; 30% beat the index. |

### 8.3 Daily alert to the owner

BW-NL-10: when a code is first classified `new_listing` (or `pending_first_trade` becomes `new_listing` on its first trade), the 22:45 digest carries one line: code, name, sector, first close, day-1 traded value, market cap, and the flag `DUAL` or "large at listing" where it applies. Renames, funds and other securities are never alerted. A weekly table of the last 15 listings and the best and worst since listing is in `NEWLIST.md`. The alert is information; it creates no order and no forecast other than those of 8.4.

### 8.4 How a young company enters the universe

| Stage | Age (sessions since first price row) | May be held by |
|---|---|---|
| S0 Tracked | 0–125 | Nothing. Alerted and recorded only |
| S1 Seasoning | 126–251 | **EARLY only**, if registered and only through its rule |
| S2 Seasoned | 252 and above, with `s1`, `s2`, `s3` present and BW-UNI-12 met | Any line whose own rule admits it. H82 and M3 keep their rule (≥ 200 closes in 252) |

Reason for the wait (not just convenience): the scores need a year of prices; unselected young companies lose (8.2 baseline; report 85 T1: companies listed 2–5 years returned −10% over three years in the small bands against +18% for seasoned ones).

**Report 84 found no rule that passes** (section 8.5). Its unproven shadow line EARLY may buy S1 companies **on paper**; that is the only change. If a later early rule ever earns money, S1 companies become buyable by that line alone, under the caps of 8.6. S0 does not change. No other line's universe changes.

### 8.5 Research line EARLY (from report 84, which landed on 19 Nov 2026)

**Report 84's result** (`$R/84_early_stage_new_listings_fable.md`; 2,221 ordinary listings 2001–2022, dead companies included; 28 counted trials):

| Placeholder | Filled |
|---|---|
| **[R84-1] Indicators** | **None of the pre-registered indicators predicted average returns in both periods.** Signs of trouble were clear in 2013–2022 only: most volatile third in the first six months (61% later halved against 33%); close under A$0.20; shares on issue up more than 10% in the first year (72% halved against 25%); loss-making (57% against 30%). One sign held in both periods: above the first-day close and ahead of the index at six months (later five-fold winners 2–3 times as common: 6–8% against 2%) |
| **[R84-2] Rule** | **No rule met the adopt bar.** As a group, new listings bought at six months trailed the index fund by 2 to 10 points a year. The selected design ("EARLY": non-resources, A$100,000 a day or more, A$0.20 or more, above the first-day close and ahead of the index at six months; sell on a 35% fall from the best month-end or after three years) led by +1.4 to +2.9 a year on 2001–2012 listings and +1.7 to +3.3 on 2013–2022, t 0.6–1.4, 84th–96th percentile of random books; **with the best single company removed the lead is +0.3 to +0.7, with the best three removed it is negative.** Verdict: not passed; unproven |
| **[R84-3] Frozen rules** | `$R/84_AMENDMENT_shadow_EARLY.DRAFT.md` (rules Y1–Y9; books `SHADOW_EARLY_100k_b0`, `_25k_b0`, `_100k_e1`; unused money held in A200; controls C1s and C2s, 100 books each; reference code `$B/deep84/code/early_ref.py`, `early_live.py`, `early_hist.py`). The system implements EARLY **from that file** once registered (BW-STR-01) |
| **[R84-4] Ledger** | Not yet registered on 19 Nov 2026. If registered before 30 Nov, first decision 30 Nov 2026; the record keeper enters the hash here |

| ID | Requirement |
|---|---|
| BW-NL-20 | EARLY is a **shadow** line, labelled "unproven; lead depends on one to three companies" on every scorecard. Its draft places it under adopt rule v2 (its tracking error with the A200 core is 8–13 points) and says honestly that it is not expected ever to reach t ≥ 3. That stands unless the owner re-classes it as high-swing at registration; either way the caps of 8.6 apply to any real money. |
| BW-NL-21 | **Learning slot.** Section 7 of the EARLY amendment (the indicator scoreboard for **every** ordinary new listing, bought or not, recorded at its 126-session decision and scored at +12 and +24 months) is implemented as forecasters `F-NL-VOLA`, `F-NL-LOWPRICE`, `F-NL-ISS`, `F-NL-LOSS`, `F-NL-ABOVE-FIRST`, `F-NL-SIZE`, `F-NL-RES`, `F-NL-D1`, `F-NL-MOM6`, `F-NL-VOLTREND` in the prediction ledger (section 15.3), with horizons 63, 126, 252 and 504 sessions and the flags "halved" and "doubled" as extra outcomes. About 100 new cases a year; first formal reading 31 Dec 2028. The scoreboard informs a future card; it never alters EARLY (its rule Y9). |
| BW-NL-22 | **Champion/challenger path.** EARLY's champion is "buy no new listings" (the A200 comparator). Its scorecard leads with EARLY minus the median C2s book (random older companies, same exit), then EARLY minus A200. A changed early rule (for example one built on the trouble signs once the scoreboard confirms them) is a new line by a new card (section 15.6). |
| BW-NL-23 | **Known gaps to close when wiring EARLY** (from its section 8): the tracker lists some funds and trusts as `new_listing` (EARLY's name filter removes them; BW-UNI-03 must too); the ISIN field (BW-NL-02); the tracker's 2014–2025 baseline lacks most companies delisted before 2018, so its base rates are slightly too kind; held companies need prices from the main store after the tracker's 400-day window; no delisting reasons in the tracker. |
| BW-NL-24 | Optional forward-only facts for companies that pass EARLY's first three tests (about 15–25 a year), entered by hand: issue price, escrow release dates and size, prospectus forecast against the first result, cornerstone backing. Stored beside the scoreboard; no rule uses them. |

### 8.6 Caps for lottery-like names (all lines, all modes)

An entity is **lottery-class** on a decision day if any holds: age under 504 sessions; raw close under A$0.20; `tv_med63` under A$250,000.

| ID | Requirement |
|---|---|
| BW-NL-30 | In simulated shadow books a line's own rules decide. In any **broker** book (paper or real) the breaker enforces: a lottery-class position at cost ≤ 1.25% of the book; all lottery-class positions together ≤ 15% of the book; an EARLY sleeve inside a real-money account ≤ 10% of that account (report 84 §0 item 7 suggests 10% in total and 4% a company; the stricter 1.25% a position applies here). An intent above a cap is clipped and logged `LOTTERY_CAP`. The difference between the registered book and the capped broker book is reported monthly. |
| BW-NL-31 | **Spreads.** For S0–S1 companies and any entity with `tv_med63` under A$1m the cost table starts from report 84's bands: ≥ A$3m a day 0.25%; A$1–3m 0.50%; A$0.25–1m 0.75%; A$50–250k 1.25%; below 2.50%; never less than half a price step. The learned table (section 15.7) replaces these as fills accumulate. |

---

## 9. Portfolio construction and sizing

| ID | Requirement |
|---|---|
| BW-PRT-01 | **A book** is (line, size, account). Simulated books follow their rule file to the letter. One broker book exists per broker account. |
| BW-PRT-02 | **Which book goes to the broker.** In `paper_auto`: `EMG2_100k` (decision D-2). The IBKR paper account is set to A$100,000 [unverified O-3: whether the paper balance can be set] or the book is scaled to the paper balance by a recorded factor. |
| BW-PRT-03 | **Sizing in the broker book** = the line's targets × (broker book NAV ÷ registered book NAV), whole shares, rounded down; an order under A$500 is skipped (ASX minimum marketable parcel for a first purchase) and logged `MIN_PARCEL`. |
| BW-PRT-04 | **Pilot book** (D-3, D-4, D-12; capital at most A$10,000): EMG2-20 exactly as section 7.9 (20 slots, sell only when off T, A$500 minimum order); a lottery-class name (section 8.6) is skipped and the next name on T taken, because its 1.25% cap is below the A$500 minimum parcel; labelled "pilot: execution learning, not evidence". |
| BW-PRT-05 | **Cash.** New lines are fully invested by rule; residual cash above 2% of a broker book for more than one decision cycle raises a WARN. Cash is not swept into a fund automatically. |
| BW-PRT-06 | **No discretionary overrides** in registered books. In a real-money book the owner may veto a buy (section 12); each veto is recorded and the "as-registered" book continues unvetoed beside it. |
| BW-PRT-07 | **Account mix.** The Big Wins account holds lines only. How much of the owner's wealth it is, is the owner's decision recorded at gate G3; the system prints the Big Wins account as a share of the declared total each month. |

---

## 10. Risk controls and kill switches

The breaker (`RiskManager.apply`) is independent of every line and cannot be bypassed (BP-04 carried). It only blocks, clips or halts; it never creates or reshapes a portfolio. Limits that would change what a line holds belong in the line's registered rules, not here.

### 10.1 Per-order checks (plan time and send time)

| ID | Check | Limit [design unless stated] | Action |
|---|---|---|---|
| BW-RSK-01 | Kill or halt flag (v2.13 RSK-01) | — | Reject all; under `HALTED_BUYS` sells proceed |
| BW-RSK-02 | Entity eligible today: verdict not BLOCK, not suspended, not frozen for a corporate action | — | Reject |
| BW-RSK-03 | No short; sell quantity ≤ broker position (RSK-03) | Hard | Reject, PAGE |
| BW-RSK-04 | Order value | Buy ≤ the larger of 3% of book NAV and 1.5 ÷ (the book's target number of names) (pilot of 20 names: 7.5%); ≤ 1.25% if lottery-class (BW-NL-30) | Clip, log |
| BW-RSK-05 | Position after the buy, at cost | Same limit as BW-RSK-04 | Clip |
| BW-RSK-06 | Participation | Order quantity × price ≤ 5% of `tv_med20` (20-session median traded value) | Clip; remainder carried one session |
| BW-RSK-07 | Limit price band | Limit within 3% of the reference (last trade at the 14:30 tick, or the previous close if none) for bands A–B, 5% for band C and below | Reject (`PRICE_BAND`); retry next session |
| BW-RSK-08 | Price gap | Last trade at 14:30 more than 15% from the previous close | Buy: hold one session (`GAP_HOLD`). Sell: proceeds |
| BW-RSK-09 | Orders per day | ≤ 80 `placeOrder` calls per broker book | Reject the rest, latch, PAGE |
| BW-RSK-10 | Buys per day | ≤ 60% of book NAV, except the first build of a book (flag `INITIAL_BUILD`, owner-approved in real-money modes) | Reject the rest |
| BW-RSK-11 | Cash | Buys ≤ settled cash; confirmed by `what_if` (RSK-10) | Scale down |
| BW-RSK-12 | Lottery caps | BW-NL-30 | Clip |

### 10.2 Book-level monitors and halts

| ID | Monitor | Review (WARN) | Halt (`HALTED_BUYS`, PAGE; owner resumes with second factor) |
|---|---|---|---|
| BW-RSK-20 | Drawdown of a broker book from its peak NAV | 30% | **50%** for EMG2 and EARLY (back-test worst 38% and 57%); 35% for H82-class books |
| BW-RSK-21 | Book return minus A200 over a rolling 12 months | −25 points | −40 points |
| BW-RSK-22 | One-day book move | −7% | −12% |
| BW-RSK-23 | Realised cost per trade ÷ modelled cost, rolling 3 months and at least 30 trades | 1.5 | 2.5 |
| BW-RSK-24 | Single name as a share of book NAV | 10% (EMG2 rule 9 trims) | 20% |
| BW-RSK-25 | One sector as a share of book NAV | 50% | — (report only; a cap would change the registered rule) |
| BW-RSK-26 | Holdings suspended more than 5 sessions | Any | More than 15% of NAV |
| BW-RSK-27 | Reconciliation break (RSK-25) | — | `HALTED_INTEGRITY`: every order stops |
| BW-RSK-28 | Replay mismatch (BW-SYS-02) | — | `HALTED_INTEGRITY` for that line |
| BW-RSK-29 | Real money at risk: pilot or live account value below 60% of the capital put in | — | `HALTED_BUYS`, PAGE, written owner decision to continue or close |

A halt never forces a sale. Selling everything is the owner's act (`/kill` then a manual instruction), never the system's.

### 10.3 Kill switches

| ID | Requirement |
|---|---|
| BW-RSK-30 | `/pause` (buys stop, registered sells proceed), `/kill` (all new orders stop, open orders cancelled) in one step from Telegram or CLI (BP-05, RSK-34 carried). Re-arm needs the second factor. |
| BW-RSK-31 | Broker-side: in real-money modes the IBKR account has daily order-value precautions set to 60% of the capital cap, and the API user has no funding rights (BP-08, BP-21). |
| BW-RSK-32 | **Kill criteria, evaluated monthly and at each December review:** (1) a v3 stop condition (section 18.3) is met; (2) BW-RSK-20 halt reached twice in 24 months; (3) all-in running cost above 3% of real money a year from A$25,000 of real money; (4) two integrity incidents with money affected in 12 months. If any is true the line (1, 2) or the real-money stage (3, 4) is closed unless the owner records a reason to continue. |

---

## 11. Execution

### 11.1 Rules

| ID | Requirement |
|---|---|
| BW-EXE-01 | **Order type.** Registered lines trade "at the next session's close". The system sends **limit-on-close (`LOC`) orders on ASX** for the closing single-price auction. No market orders and no market-on-close (EXE-02 carried). |
| BW-EXE-02 | **Timing.** Batch decided on session D (22:20). Executed on session D+1: pre-checks at the 14:30 tick; orders submitted by the `submit_loc` job at **15:45** [design; cut-off unverified, open item O-1]; fills collected at 16:20. |
| BW-EXE-03 | **Limit price.** Buy: reference × (1 + b); sell: reference × (1 − b); reference = last trade at the 14:30 tick; b = 2% for bands A–B, 3% for band C and below [design]; rounded to a valid price step from IBKR contract data (never hard-coded; SYS-29 carried). |
| BW-EXE-04 | **Unfilled.** An intent not filled in the auction is carried to the next session's auction, for at most 3 sessions (`execution.carry_sessions`). Then: a **sell** is sent as a limit order in continuous trading between 11:30 and 15:00 at the best bid (re-priced once at 13:00); if still unfilled it is paged. A **buy** lapses (`BUY_LAPSED`) and the line's next decision deals with it. |
| BW-EXE-05 | Sells before buys; buys use settled cash only (EXE-08). In a book whose line sells and buys on the same day (EMG2), buys funded by that day's sales are sent on the session the proceeds are usable; whether auction-sale proceeds can fund a same-auction buy in an IBKR cash account is **[unverified O-2]**; default: buys one session after the sells, and the simulated book shows the difference. |
| BW-EXE-06 | **Intent lifecycle** CA-01 carried: `PLANNED → RISK_OK → APPROVED → SENT → FILLED / PARTIAL / EXPIRED / CANCELLED / REJECTED / NEEDS_REVIEW`. An intent is persisted with its deterministic `client_order_id` = `<book>-<D>-<entity>-<side>-<attempt>` before any send. |
| BW-EXE-07 | **Quote record.** At submit time one IBKR snapshot per order (bid, ask, last, sizes, time) is stored with the intent (LRN-18 carried). Snapshot count is logged; above the free allowance the fee is a running cost reported monthly (about US$0.03 each; about 30 a month for EMG2). |
| BW-EXE-08 | **Simulated books** fill at the D+1 close with the line's own cost rule. For the one broker book, the simulated twin of the same book keeps running; the difference (broker minus simulated, per trade and cumulative) is the implementation shortfall, reported daily. |
| BW-EXE-09 | **Paper/live guard** EXE-12 carried: `paper_auto` requires an account id starting `DU`; `pilot`/`live` require the id recorded at the gate. |
| BW-EXE-10 | **Safety cancels at ticks** (the only intraday order action): a pending **buy** is cancelled if the entity is halted, flagged `BID_PEG`, has moved more than 15% from the previous close, or its data are broken; a pending order of any side is cancelled on `/kill`. A cancel reduces risk and needs no approval. Nothing else may be changed intraday. |

### 11.2 Costs

| Item | Model [source] | Learned by |
|---|---|---|
| IBKR commission, ASX | max(A$6.60, 0.088%) including GST [v2.13 RND-021; GST treatment I1 unverified] | Monthly reconciliation to charged commission (EXE-09) |
| Spread and impact | Line's own rule in its book. Owner-cost scoring: closing-auction fills for bands A–B at zero spread [report 82 §7, top 100 only]; band C 0.50% a side with the half-step floor [design; report 85 doubles it as a stress] | Section 15.7: realised fill against the 14:30 mid and against the last continuous trade |
| A$0 platforms | The owner's index platform charges A$0 on about 550 ASX shares [report 44]; whether band-C shares are on its list and whether it can join the closing auction is unknown (O-6). **The system does not trade through it.** An "owner-cost A$0" scoring is shown beside the IBKR scoring for every line so the cost of the broker choice is visible (EMG2 back-test: 13.3% at A$0 against 12.1% at IBKR minimums) | — |

---

## 12. Approval queue

| ID | Requirement |
|---|---|
| BW-APR-01 | Every decision produces one **batch** per book: id, line, book, decision day, list of intents with side, quantity, reference price, value, reason code, the line's ranked table hash, risk result, estimated cost and estimated tax of each sale. Stored in `approval_batch` (insert-only; status changes audited). |
| BW-APR-02 | **Paper modes:** status goes `AUTO_APPROVED` at creation. The batch is still sent to the owner in the 22:45 digest. |
| BW-APR-03 | **Real-money modes: approval required, off by default.** The batch is delivered by Telegram (and email copy) by 22:45 on D. The owner replies `/approve <batch_id> <6-digit code>` (TOTP second factor) before **15:30 on D+1**. Without it, **no order of the batch is sent**: the batch is carried to D+2 and D+3 (re-priced, re-checked), then lapses (`LAPSED_NO_APPROVAL`) and is recorded as an override. |
| BW-APR-04 | The owner may remove single **buys** with `/veto <batch_id> <code>` before approving. Sells of a registered line cannot be vetoed one by one; the owner can refuse the whole batch. Every veto, refusal and lapse is written to the override ledger with the "as-registered" outcome tracked beside it (MON-17 idea carried). |
| BW-APR-05 | Approval expires at 15:40 on the execution day; a batch changed by risk clipping after approval by more than 5% of its value needs a new approval. |
| BW-APR-06 | The approval path is deterministic code. No AI component reads or writes `approval_batch` (import test). Telegram commands only from allow-listed ids (BP-11). |
| BW-APR-07 | The first build of a real-money book (`INITIAL_BUILD`) and any resume after a halt need approval with a typed sentence stating the amount. |

---

## 13. Ledger, hash chain and pre-registration

### 13.1 Databases

Two PostgreSQL databases as built in M0: `market_<user>` and `ledger_<user>_<paper|live>`; insert-only tables with the mutability guard and audit log (v2.13 section 12). New tables:

| Database | Table | Key columns |
|---|---|---|
| market | `entity`, `code_map`, `security_class` | Section 5.1 |
| market | `universe` | session, entity, tv_med252, tv_med63, tv_rank, band, eligible, verdict |
| market | `feature` | session, entity, feature, version, value |
| market | `tick_quote` | BW-DAT-07 |
| market | `asic_position`, `estimate_snapshot`, `fundamental_snapshot`, `newlist_registry`, `newlist_path` | Sections 6, 8 |
| market | `forecaster`, `forecast`, `forecast_outcome`, `forecaster_scorecard` | Section 15.3 |
| market | `hypotheses`, `trials`, `prereg` | Section 16 |
| ledger | `line`, `book`, `line_state`, `decision`, `target` | Section 7 |
| ledger | `order_intents`, `broker_orders`, `fills`, `parcels`, `cash_ledger`, `nav_eod`, `dividends` | v2.13, plus `line`, `book`, `batch_id` |
| ledger | `approval_batch`, `override` | Section 12 |
| ledger | `scorecard_daily`, `twin_nav`, `comparator_nav` | Section 17 |
| ledger | `chain_entry` | Section 13.2 |
| ledger | `gate_record`, `acceptances` | Section 18 |
| ledger | `learned_values`, `cost_table` | Section 15.7 |
| ledger | `incidents`, `flags`, `runs` | v2.13 |

### 13.2 Hash chain

| ID | Requirement |
|---|---|
| BW-LED-01 | `chain_entry` continues `$F/LEDGER.jsonl`: seq, kind, asof, event, payload hashes (files or table-row digests), `prev_entry_sha256`, `entry_sha256` = SHA-256 of the canonical JSON of the entry without that field. Entry 1's predecessor is 64 zeros; the imported entries keep their hashes. |
| BW-LED-02 | One `daily` entry per session after `book_day`, covering: data manifest hash; universe and feature digests; forecast-row digest of the day; every decision and batch; fills; NAV of every book, twin and comparator; scorecard files. One `tick` entry per tick covering the tick's quote file and forecast digest. |
| BW-LED-03 | Entry kinds: `daily`, `tick`, `amendment`, `code`, `prereg`, `gate`, `approval`, `override`, `incident`, `correction`. Nothing is ever edited; a correction is a new entry that names the entry it corrects. |
| BW-LED-04 | Each night the chain file is exported as JSON lines to the off-site copy and its head hash is sent in the digest. `trader chain verify` recomputes the whole chain; a break is `HALTED_INTEGRITY`. |

### 13.3 Pre-registration

| ID | Requirement |
|---|---|
| BW-LED-10 | **Nothing is scored that was not registered first.** A line, a forecaster, a measurement, a gate rule or a research card exists for the system only as a `prereg` or `amendment` chain entry whose payload is the SHA-256 of its rule text and (for code) of its source files. The entry's time must be earlier than the first data it is scored on; the scorer checks this and refuses otherwise. |
| BW-LED-11 | `trader register <file> --kind <line|forecaster|measurement|gate|card>` computes the hash, writes the chain entry and the config pin. In real-money stages it needs the owner's second factor; on paper the record keeper may register and the owner is told in the digest. |
| BW-LED-12 | Code of a registered line or forecaster is frozen: CI fails if a file listed in a registration changes without a new `code` entry naming the old and new hashes and the reason; a behaviour change is a new line (BW-STR-03). |

---

## 14. Tax engine

| ID | Requirement |
|---|---|
| BW-TAX-01 | Parcels per book; FIFO in every registered book (the frozen rule files use oldest-first). A real-money book may use `parcel_method: min_tax` (loss parcels first, then gains held over 12 months, then the highest-cost short-term parcel) only after the tax agent confirms specific identification is acceptable for this holding **[unverified, O-8]**. |
| BW-TAX-02 | Year-end 30 June. For each book: realised gains by short-term and long-term slice, losses carried forward, dividends, franking credits (counted when the vendor supplies the percentage; else shown as "not counted"), 45-day rule test per dividend (TAX-07). |
| BW-TAX-03 | **Scorecard tax readings** (Amendment scoring v2): rate 32% [the programme's planning rate; the owner's real marginal rate is a config value], 50% discount for parcels held 367 days or more; "kept" = tax on income and realised gains only; "sold" = as if all holdings were sold today. The owner's comparison is engine "sold" against fund "kept". |
| BW-TAX-04 | **Regime switch.** `tax.regime: A` (50% discount) is the default. `B` (no discount, used in reports 53–82 as a stand-in for rules said to start 1 July 2027) is **[unverified against legislation, O-7]**; the engine computes both and labels B "unconfirmed". |
| BW-TAX-05 | Every sale stores its rule reason code (TAX-09). EMG2's sales are nearly all short-term; the monthly report shows the tax each line has caused this year and the tax a buy-and-hold of the same money in A200 would have caused. |
| BW-TAX-06 | Tax is never a reason for the system to change a registered line's trade. Tax-aware variants are new lines. |

---

## 15. The learning loop

### 15.1 Principles

1. **The unit of learning is a forecast, not a book.** A book gives one number a month. A forecaster gives hundreds of scored predictions a day. Evidence about a signal therefore arrives 10 to 100 times faster than evidence about a book, and that is the only honest way to "learn every two hours or every day".
2. **Everything is written before its outcome exists** and scored exactly once (BW-LED-10).
3. **Learning never changes a live rule.** It changes knowledge (scoreboards, cost tables, alerts, the research backlog) and it raises proposals. Rules change only by a new registration and, where money is involved, the owner's signature.
4. **What can and cannot be learned fast.** Fast (weeks to months): data quality, real trading costs, whether a signal still sorts shares, which alerts carry information. Slow (years): whether a book beats the index after tax. The reports say which is which every time.

### 15.2 Every two hours: the tick job (10:30, 12:30, 14:30, 16:20)

**Inputs:** delayed quotes for the watch set W (BW-DAT-07); yesterday's universe, features, target lists, holdings and pending orders.

**Steps, in order:**

| # | Step | Output |
|---|---|---|
| 1 | Fetch and store quotes; mark stale or broken quotes | `tick_quote`; raw file `raw/tick/<date>/<tick>.csv.gz` |
| 2 | Compute tick features (section 6.3) | `feature` rows with tick tag |
| 3 | **Write intraday forecasts** for every tick-cadence forecaster (15.3) | `forecast` rows |
| 4 | **Resolve** forecasts made at earlier ticks whose horizon is this tick (`NT`) or, at 16:20, today's close (`CL`) | `forecast_outcome`; scoreboard deltas |
| 5 | Alerts (15.2.1) | `alerts.md` append; Telegram for PAGE and for owner-subscribed classes |
| 6 | Mark every book to the quotes, labelled "indicative, delayed" | `INTRADAY.md` |
| 7 | 14:30 only: pre-auction checks and safety cancels (BW-EXE-10) | Intent status changes, audited |
| 8 | 16:20 only: collect auction fills; write the tick's learning line | `LEARNING_TICKS.md`: per tick forecaster, today's count, hit rate, mean result, running t |
| 9 | Chain entry of kind `tick` | `chain_entry` |

#### 15.2.1 Alerts (information; never an order)

| Alert | Threshold [design] | Class |
|---|---|---|
| Holding moves | ±8% from the previous close | DIGEST; PAGE at ±20% |
| Possible halt | Held or pending name with no trade by 12:30 | DIGEST |
| Possible bid | +20% jump in a held, pending, target or band A–C name | DIGEST; cancels a pending buy (BW-EXE-10) |
| Volume surge | Tick volume above 3 × the usual full-day median by 12:30, any band A–C name | LOG; listed in the daily learning report with its later outcome |
| List crossing | A band-C name whose `s2`/`s3` recomputed on the latest quote would enter or leave EMG2's top fifth | LOG (indicative only) |
| New listing first trade | BW-NL-10 | DIGEST |
| Broken data | Missing, stale or absurd quotes for more than 10% of W | PAGE |

#### 15.2.2 What the tick job may NOT do

- It may not create a buy or a sell, change a target list, a size, a rank, a limit or a parameter, or re-run a line's `decide()`.
- It may not write to any book except to cancel a pending buy for the reasons in BW-EXE-10.
- No forecaster output is read by any order-path module (BW-SYS-13).
- An intraday rule that wants to trade must first exist as a tick forecaster, pass 15.6, and then be registered as a **new line** with its own clock.

Test BW-LRN-01: with the tick job's outputs replaced by random data, every decision, batch and order of the day is byte-identical except permitted cancels.

### 15.3 Forecasters and the prediction ledger

**Tables.** `forecaster` (id, version_hash, registered chain seq, cadence, universe_tag, horizons, direction, status). `forecast` (id, forecaster, made_at_utc, session, tick, entity, score, rank_pct, bucket ∈ {TOP, MID, BOT} for cross-sectional forecasters or {EVENT} for flags, universe size). `forecast_outcome` (forecast id, horizon, resolved_at, entity return, benchmark return, abnormal return). `forecaster_scorecard` (forecaster, horizon, date, n formations, n forecasts, rank IC of the formation, TOP−ALL, BOT−ALL, cumulative mean, Newey-West t with lag = horizon in formations − 1, CUSUM state, net-of-cost TOP−ALL).

**Conventions.** A daily forecast for session D is entered at the close of D+1 and held to the close of D+1+h (h = 5, 21, 63, 126, 252 sessions). A tick forecast is entered at the tick's last price and resolved at the next tick (`NT`), the day's close (`CL`), the next day's close (`1D`) and five sessions on (`5D`). Benchmark = the equal-weight mean return of the forecaster's universe set over the same window. TOP and BOT are the top and bottom fifths. A company that stops trading keeps its last value; the 20-session payout rule applies. Net-of-cost spread subtracts the learned round-trip cost of the bucket × the bucket's turnover.

**Initial register** (each a short pure function with a frozen definition; all registered in one `prereg` entry before first use):

| Forecaster | Universe | Cadence | What it says | Prior from history |
|---|---|---|---|---|
| `F-M3-A`, `F-M3-B`, `F-M3-C` | Bands A, B, C | Daily | In-band M3 score | C strong (t 4.5); B weak; A mostly loser-avoidance |
| `F-H82-300` | Top 300 | Daily | H82 score | Loser detector |
| `F-RM-C`, `F-MOM6-C` | Band C | Daily | Residual momentum; six-month return only | Untested in band C (gap S2) |
| `F-LOSER30-A/B/C` | Bands | Daily | Flag: bottom 30% by M3 | A: +1.75 to +1.9 a year on blunt weights |
| `F-ISS-C` | Band C | Daily | Flag: shares on issue up more than 20% in 252 sessions | Untested in band C (gap S6) |
| `F-SHORTCHG-B` | Bands A–B | Daily | 20-session change in short interest | Untested (gap S7) |
| `F-TRIPLED` | Bands B–D | Daily | Flag: three-year return of 200% or more | Negative (report 85 T1) |
| `F-CAT-UP`, `F-CAT-DN` | Bands A–C | Daily | Catalyst-day flags | **Negative controls**: no effect expected (T2, T3) |
| `F-REV` | Covered names | Daily, from 126 sessions of snapshots | 30-day estimate revision | Unknown; vendor data weak |
| `F-NL-<indicator>` × 10 | New listings at 126 sessions | Monthly (at each listing's decision) | Report 84's indicators (BW-NL-21) | Trouble signs clear in 2013–2022 only; "above first-day close" in both periods |
| `F-JUNE` | Small caps, June | Yearly | H100 list | +6% in five weeks unseen, t 2.2 |
| `F-I-MOM` | Bands A–C, at 12:30 | Tick | Rank of return since the previous close | Unknown |
| `F-I-REV` | Bands A–C, at 12:30 | Tick | Minus the rank of return since the open | Unknown |
| `F-I-VOL` | Bands A–C, at 12:30 | Tick | Flag: volume surge (15.2.1) | Probably none (T2) |
| `F-RANDOM` | Band C | Daily and tick | Seeded random score | **Placebo**: its t must stay inside ±2; if not, the scorer is wrong |

| ID | Requirement |
|---|---|
| BW-LRN-02 | A forecast row is inserted before its entry time and is never updated. A restated input (Sunday re-download) adds a `restated` flag row; the original stays and both are scored. |
| BW-LRN-03 | `resolve_daily` scores every forecast whose horizon ended that session, once. Re-running it changes nothing (idempotent). |
| BW-LRN-04 | The placebo `F-RANDOM` and the negative controls are scored and shown first on every scoreboard. A placebo t outside ±2.5 over more than 250 formations pages (scorer fault). |
| BW-LRN-05 | New forecasters are added only by `trader register --kind forecaster`, at most **two a month** [design], each from a research card (section 16). A forecaster is never edited; a changed definition is a new id. |

### 15.4 Every day, week, month and quarter

| When | Job | What is computed | Output file | Thresholds |
|---|---|---|---|---|
| **Daily 22:00–22:45** | `forecast_daily`, `resolve_daily`, `book_day`, `replay_check`, `report_daily` | New forecasts; outcomes for horizons ending today; every book, twin and comparator marked; each line's decision replayed; implementation shortfall of the broker book | `LEARNING_DAILY.md`: (1) data: missing bars, restatements, new codes, new listings; (2) forecasters: today's resolved count, hit rate and spread per forecaster and horizon, running t; (3) books: day and since-start return against A200, percentile among twins; (4) costs: today's fills against model; (5) alerts raised and what happened next to yesterday's alerts | PAGE on replay mismatch, placebo fault, reconciliation break |
| **Weekly, Saturday** | `learn_weekly` | 5-session scoreboards; alert-class usefulness (mean 5-session abnormal move after each alert class, with t); data-quality trend; cost trend; restatement recompute results | `LEARNING_WEEKLY.md` | An alert class with |t| under 1 after 200 alerts is demoted to LOG |
| **Monthly, first Saturday** | `learn_monthly`, `challenger_monthly`, `cost_learn` | Month-end forward evaluation of every line and shadow (15.5); BANDSPREAD and AVOID readings; forecaster status changes; learned cost table; tax-to-date per line | `CHAMPION_CHALLENGER.md`, `SCORECARD.md`, `COSTS.md` | Status rules below |
| **Quarterly** | `learn_quarterly` | "What the system learned": what changed in the scoreboards, which forecasters were retired or flagged, cost table versions, incidents and their causes, backlog re-ranked by evidence | `LEARNED_<yyyy>Q<n>.md` | — |
| **Yearly, last session of December** | `gate_review` | Formal gate readings (section 18); kill criteria; proposals | `GATE_REVIEW_<yyyy>.md`, `PROPOSAL_<line>_<date>.md` | Section 18 |

**Forecaster status rules** (automatic labels; none changes a line):

| Status | Rule |
|---|---|
| `young` | Fewer than 250 daily formations (or 60 monthly) resolved at the 21-session horizon |
| `informative` | t ≥ 2.0 on TOP−ALL (or the flag's abnormal return) at the 21- or 63-session horizon, **and** the net-of-cost spread is positive |
| `strong` | t ≥ 3.0 with at least 500 formations, net-of-cost positive |
| `dead` | At least 500 formations and |t| under 1.0 at every horizon: moved to the back page, still recorded |
| `decayed` | Was informative or strong; one-sided CUSUM on standardised monthly spreads (reference 0.5, limit 4; LRN-13) signals; flagged on the front page |
| `contrary` | t ≤ −2.0: flagged; if a registered line uses this forecaster's signal, the line's scorecard carries the flag |

### 15.5 Champion and challenger

`CHAMPION_CHALLENGER.md`, rebuilt every month-end and marked daily, one row per book at A$100,000:

| Column | Definition |
|---|---|
| Role | Champion (H82 until a promotion), challenger (EMG2), shadows, controls |
| Months since registration | — |
| Return since start; A200 (A$0, kept) since the same day; lead | Time-weighted |
| After tax: book "sold" minus fund "kept" | BW-TAX-03 |
| Percentile among its twins | Share of twins with a lower return |
| Tracking error; t of the monthly lead | From 12 months on |
| Signal spread and t | The line's registered measurement (EMG2: BANDSPREAD band C TOP−ALL) |
| Worst fall; turnover; cost paid; cost against model | — |
| Gate status | The step of section 18 the line is on, each condition shown met or not, and the earliest date the next step can be read |
| Flags | Halts, decayed signal, data blocks, overrides |

| ID | Requirement |
|---|---|
| BW-LRN-10 | The comparison is automatic and complete: every registered line appears; none can be hidden; controls (CW, MOM, random books, twins) are shown and marked "control: not adoptable". |
| BW-LRN-11 | **A challenger is "ahead" only in the words of the gate table.** No league table is printed without the twin percentile and the t beside it (v2.13's rule against bare league tables carried). |
| BW-LRN-12 | **Promotion.** When, at a gate review, a line meets every condition of its next step (section 18), `challenger.py` writes `PROPOSAL_<line>_<date>.md`: the evidence table, the money step it would unlock, the risks, the cost in dollars against the data bill, and the exact config change. **Nothing else happens.** The owner signs with `trader gate sign <proposal> <code>`; that writes a `gate` chain entry and a config pin; the change ships in a tagged release. The system cannot sign, merge or deploy. |
| BW-LRN-13 | "Champion" is a label for the line the owner has funded or, before any funding, the registered baseline. Changing the champion label is a gate signature. It changes reports and which book goes to the broker; it does not change any line's rules. |
| BW-LRN-14 | **No self-modification.** CI test: the set of (line id, rules hash, code hash) the runner will execute equals the set pinned in config and present in the chain; the learning and research packages have no write access to `config/`, `lines/`, `forecast/forecasters/` or the ledger's order tables (file permissions and an import test). |

### 15.6 From a forecaster to a line

A signal earns a book only by this path:

1. Registered forecaster reaches `informative` (t ≥ 2.0, net-of-cost positive) on forward data.
2. A research card (section 16) specifies one book rule built on it, with twins, costs and a bar, pre-registered.
3. One back-test on history is allowed as a sanity check and counted as a trial; it can stop the card (a clear fail) but cannot pass it.
4. The line is registered as a shadow, by amendment, with its own clock. At most **two new book lines a year** [design].
5. It then climbs section 18 like any other line.

For an intraday forecaster the extra condition is a net-of-cost result after twice the learned spread and full short-term tax; on the evidence so far (reports 70, 81; T2) expect none to pass.

### 15.7 What may update automatically (whitelist)

| Value | Update rule | Used by |
|---|---|---|
| Cost table: half-spread by liquidity band and price bucket, auction against continuous | (n₀ × prior + n × sample mean) ÷ (n₀ + n), n₀ = 30 fills; clamped to 0.5–3 × the prior; new version only if an entry moves by more than 20% (LRN-10, LRN-12 carried) | Owner-cost scoring, net-of-cost scoreboards, BW-RSK-23. **Not** used by any registered line's own book, whose cost rule is frozen |
| Commission schedule | From charged commissions | Reports |
| Alert thresholds' class (DIGEST or LOG) | 15.4 weekly rule | Alerts |
| Data-quality thresholds | Never automatic; proposals only | — |

**Never automatic** (LRN-09 carried and widened): any rule, parameter, universe, score, list length, clock, limit, cap, gate threshold, tax setting, the champion label, the set of registered lines or forecasters. Every automatic update writes a `learned_values` row and can be reverted (`trader learn revert`).

### 15.8 How new hypotheses are generated, registered and tested

See sections 16.3 and 16.4. In one line: the monthly research cycle takes the top items of the backlog (seeded with the gap register of report 85), writes at most two cards, registers each before any run, runs the harness, records the result as a trial whatever it is, and at most proposes a forecaster or a shadow line for registration.

---

## 16. Research harness and trial counting

### 16.1 Harness

| ID | Requirement |
|---|---|
| BW-RND-01 | The harness runs the production `score()`, `decide()`, `build_orders()` and breaker over stored point-in-time data, daily clock, the line's cost rule, the tax engine, with twins. It is the engine of record for back-tests. A faster monthly approximation may exist only if it reconciles to the harness within 0.3 points a year on three reference lines. |
| BW-RND-02 | **Two arms in one engine.** Every comparison is a line against its twin, its no-signal version or its comparator **in the same run**. Results from different engines are never compared (report 81: 1.5 points of engine noise). |
| BW-RND-03 | **A back-test never promotes.** All ASX history to 19 Nov 2026 is spent. A back-test may admit an idea to forward testing or kill it. The harness prints "seen data" on every back-test page. |
| BW-RND-04 | Reference packs: ASX EODHD 2010–present, all entities, built by the data layer (not by one-off scripts). The reference results of report 85 T4 and T6 and of report 81's H82 run are regression tests: a data-layer change that moves them is reported with the cause. |

### 16.2 Trial log

| ID | Requirement |
|---|---|
| BW-RND-05 | `trials` gets one row per harness run of a new specification, automatically, pass or fail: id, card, spec hash, data hash, date, result summary. Not counted: replications, twins and placebos, cost/tax/size stresses of a frozen spec (the programme's convention). |
| BW-RND-06 | The count continues the programme's: **1,761 after report 83; +28 for report 84; +6 for report 85 (T1–T6): 1,795.** The record keeper enters the final figure once when the system is seeded. The count is printed on every research output. |
| BW-RND-07 | Caps [design]: at most **24 counted back-test trials a quarter**; at most two new forecasters a month; at most two new book lines a year; at most four high-swing lines eligible for money at any time. The t thresholds of section 18 allow for up to 30 lines tested at once. |

### 16.3 Cards and the monthly research cycle

| ID | Requirement |
|---|---|
| BW-RND-08 | **Card** (`research/cards/<id>.md`): id; gap-register id; rationale written before data; exact rule; data and window; the single statistic and bar; what happens on pass and on fail; trials it will use. Registered (`prereg` chain entry) before the run. |
| BW-RND-09 | **Cycle**, first Saturday 08:00, run by the research agent off the trade path: (1) read `LEARNING_WEEKLY`, the scoreboards and incidents; (2) re-rank `research/backlog.yaml` by expected value; (3) draft at most two cards from the top; (4) register; (5) run; (6) write `research/results/<id>.md` with the verdict by the pre-set bar; (7) if a pass: draft the forecaster or shadow-line registration for the record keeper; (8) summarise in the monthly report. Any data fault found becomes an incident and a data-layer test first (LRN-20 carried). |
| BW-RND-10 | **Restatement recompute.** When a data fix or restatement changes an input of a registered result, the harness recomputes that result nightly and reports old and new figures side by side. No figure is silently replaced. |
| BW-RND-11 | The agent may read, research, write and propose. It may not register in real-money stages, merge, deploy, sign a gate or touch an order (RND-002 carried). |

### 16.4 Research backlog, seeded from report 85's gap register

Order = expected value. Each is one card unless marked.

| # | Gap | Card | Type |
|---|---|---|---|
| 1 | C1, C2, C4 | Reality spike: IBKR paper login, `LOC` acceptance and cut-off on ASX, fills in band-C names, Flex timing, `orderRef` after restart | Operational test (milestone B0) |
| 2 | U4 | Apply A7(c) to all AU ordinary shares; re-run T4 and T6 as corrections | Correction, not a trial |
| 3 | S6 | Dilution flag in band C: EMG2 with and without names whose shares on issue rose more than 20% in 252 sessions (ASIC, 2011+) | 1 trial + forecaster `F-ISS-C` |
| 4 | X4 | EMG2 hold band (sell below the best 40%) | 1 trial; pass = a new shadow line EMG2b |
| 5 | X5 | EMG2 graduates kept while in the top half of band B | 1 trial |
| 6 | S2 | Momentum form in band C | No back-test: three forecasters forward |
| 7 | T2g | Weekly refresh in band C with the hold band | 1 trial, only if #4 passes |
| 8 | N2 | New-listing indicators: report 84 found no passing rule; EARLY runs as an unproven shadow; the trouble signs are scored forward (BW-NL-21) | Forward only; first reading 31 Dec 2028 |
| 9 | S5 | Announcement events | Blocked on O-5 (feed) |
| 10 | S7 | Short-interest change | 1 trial + forecaster |
| 11 | S4, S10 | Estimate revisions; point-in-time fundamentals | Forward only; first reading 2027–2028 |
| 12 | S8 | June rebound sleeve | Paper, June 2027 |
| 13 | Z3 | Adding to winners | Only if #5 passes |

Closed and not to be reopened without new data: price rules in the top 300; breakout and stop rules; catalyst-day entry; bad-news-day exit; keep-winners in band C; accounts filters on top-300 momentum books.

---

## 17. Monitoring, alerts and reports

| Report | When | Content |
|---|---|---|
| Digest (Telegram, email copy) | 22:45 each session; heartbeat 20:00 daily | Status line; banner "Not shown to beat the index"; today's batch and approval request; new listings; PAGE-class alerts; chain head hash |
| `SCORECARD.md` | Daily | Every book: NAV, return, A200, lead, after-tax kept and sold, twins percentile, holdings, cash, flags. EMG2 first, then H82 ("large-company control"), shadows, controls |
| `INTRADAY.md`, `LEARNING_TICKS.md` | Each tick | Section 15.2 |
| `LEARNING_DAILY.md`, `LEARNING_WEEKLY.md`, `LEARNED_<q>.md` | Section 15.4 | — |
| `CHAMPION_CHALLENGER.md` | Monthly; marked daily | Section 15.5 |
| `NEWLIST.md` | Daily | Section 8 |
| `COSTS.md` | Monthly | Running costs against budget; cost per trade against model; credits used |
| `TAX_<fy>.md`, facts bundle | Yearly, and on request | Section 14 |
| `GATE_REVIEW_<yyyy>.md`, proposals | December | Section 18 |

| ID | Requirement |
|---|---|
| BW-MON-01 | Three alert classes only: PAGE, DIGEST, LOG; every PAGE links to a runbook; page budget about 2 a month, reviewed monthly (BP-13, MON-06). |
| BW-MON-02 | Every performance figure carries one label: `back-test (seen data)`, `paper (simulated fills)`, `paper (IBKR paper fills)`, `real`. Labels are never mixed in one number (MON-16). |
| BW-MON-03 | Dead-man monitor: a missing heartbeat or daily chain entry pages through the external monitor (DAT-12). |
| BW-MON-04 | The monthly report states, in dollars, what each line's lead or lag was on its book, what the data and running costs were, and the share of the owner's declared total that is in Big Wins. |

---

## 18. Go-live gates

### 18.1 Build and operating gates

| Gate | Opens | Conditions (all) |
|---|---|---|
| **G0 Foundations** | Build proceeds past B0 | Forward record moved to durable storage and verified against the chain; restore test done; reality spike report filed (open items O-1 to O-3 answered or marked blocking) |
| **G1 Advisory** | `advisory` mode | Milestones B1–B4 accepted; 20 consecutive sessions in which the system's universe, scores and decisions for H82, M3, E3, ACC, CXL and EMG2 match the scripts of record exactly; chain verifies; digest delivered every day |
| **G2 Paper** | `paper_auto` | B5–B6 accepted; `LOC` orders proven on the IBKR paper account for at least 10 band-C names; crash-injection and reconciliation tests pass; every alert fired once in testing |
| **G3 Pilot** | `pilot`, real money ≤ A$10,000 | **For EMG2-20: replaced by the B-fast go-live checklist of section 21.1 (owner override D-12).** For any other line or amount: adopt rule v3 step P1 (18.3) met; B8 accepted; broker confirmed (O-2, O-6); broker-account hardening (BP-21); owner signs the risk statement (18.5) with the second factor; the owner declares investable assets so the 5% limit can be checked |
| **G4 Scale** | `live`, ≤ A$50,000 | v3 step P2 |
| **G5 Full** | `live`, owner's amount | v3 step P3, or adopt rule v2 for an index-like line |

### 18.2 Adopt rule v2 (in force; index-like lines: H82, M3, E3, CXL, multi-market lines)

As `AMENDMENT_adopt_rule_v2.md`: A$100,000 book only; December review after at least 36 months; pooled monthly lead t ≥ 3.0; after-tax lead ≥ +1.0 point a year (engine sold-basis not below the fund's kept-basis value); ≥ 90th percentile of random controls; controls never adoptable; staged step at 60 months with t ≥ 2.0 for one A$50,000 slice of at least 25 names; no money in books of 4–10 shares or slices under A$50,000; stop rule unchanged. First possible pass 31 Dec 2029.

### 18.3 Adopt rule v3 (owner decision D-3; high-swing lines: EMG2, H100, and any line registered with expected tracking error above 10 points a year)

Why: t against the index = lead ÷ tracking error × √years. At a tracking error of 20 and a true lead of 5, t = 3 takes 144 years. V3 asks instead whether the signal still sorts shares, whether the book beats chance in its own pond, whether it can be traded at the modelled cost, and that it is not far behind the fund; and it caps the money at each step. Text for registration: `$B/deep85/AMENDMENT_adopt_rule_v3.md`.

| Step | Evidence (all required) | Money |
|---|---|---|
| **P0 Paper** | Registered and hashed; twins and measurement line running | None |
| **P1 Pilot** | At least 12 months in `paper_auto` on the IBKR paper account; every decision executed and reconciled; realised cost per trade ≤ 1.5 × model over at least 100 fills; book ≥ 60th percentile of its twins; forward signal spread (EMG2: BANDSPREAD band C TOP−ALL) cumulative mean > 0; no halt outstanding; signed risk statement | One slice ≤ **A$10,000** and ≤ 5% of investable assets; 20 names |
| **P2 Scale** | At least 24 months from registration and 6 months of pilot; signal spread t ≥ 2.0; book ≥ 80th percentile of twins; after-tax (book sold, fund kept) not more than 5 points a year behind A200; pilot cost ≤ 1.5 × model | ≤ A$50,000; the full list |
| **P3 Full** | At least 48 months from registration; signal spread t ≥ 3.0; book ≥ 90th percentile of twins; after-tax lead over A200 (fund kept) > 0; owner signature | Owner's amount; halts of section 10 apply |
| **Stop** | At a December review from 13 months on: signal spread t ≤ −1.0; or book below the 20th percentile of twins; or, from 24 months on, after-tax more than 15 points a year behind A200 | Line closed and reported; not re-tuned; real money in it sold down over the next two decisions |

Readings: P1 at any month-end; P2 and P3 only at June and December month-ends. Stated plainly: reading a t ≥ 2 test twice a year for several years roughly doubles or triples its nominal 2% false-pass rate; this is accepted because the money at P2 is capped. Passing any step allows a written proposal only (BW-LRN-12).

### 18.4 Owner override for EMG2-20 (D-12)

Step P1's evidence conditions (12 months of paper operation, cost test, twins percentile, positive forward spread) are **waived by the owner for one slice of A$10,000 in EMG2-20**; they are recorded as "not met, waived". Everything else in v3 stands for that slice: the cap, the stop rules, P2 and P3 for any larger amount. The P1 cost test is run on the slice's own first 100 live fills and reported; a ratio above 2.5 halts buys (BW-RSK-23). The override does not extend to any other line, amount or date.

### 18.5 Risk statement the owner signs before real money (text)

"Big Wins is a bet, not a proven edge. The line I am funding failed its pre-set statistical test. I am funding it before the paper record exists, by my own decision, and I know that brokerage alone is about 8–9% of this slice a year. I expect it to fall 40–60% at some point and to trail the index by 25 points in some years. I may lose most of this slice. I will not add money outside the steps of adopt rule v3. Nothing in the system is financial advice."

---

## 19. Costs and infrastructure

### 19.1 Running costs (planning; approved under D-7)

| Item | A$ a year | Note |
|---|---|---|
| EODHD data plan | about 370 | US$19.99 a month as report 68; **plan name and whether fundamentals and estimates are included at this price is [unverified, O-4]**: the tracker and report 81 fetched fundamentals at 10 credits, so the plan in use may be a higher tier |
| EODHD higher tier if needed for fundamentals | 0–560 | US$59.99 a month for two to six months a year, or all year |
| Server (one small VPS, 2 vCPU, 4 GB, 80 GB disk) | 130–300 | Or a machine the owner has |
| Off-site backup storage | 15–30 | — |
| IBKR | 0 on paper; **about 840–930 on the A$10,000 live slice** (A$6.60 a trade, about 140 trades) | Snapshot fees above the monthly waiver about US$0.03 each |
| Announcements feed | 0–600 | Only if D-6 is exercised; owner confirms before purchase |
| Telegram, dead-man monitor | 0 | — |
| **Total on paper** | **about 700–900** (without announcements, with a fundamentals tier part of the year) | Reported monthly against budget (BW-INF-04) |

In dollars: at a A$10,000 pilot a +3 point edge is A$300 a year, less than the running cost. The pilot is for learning costs and execution, not for profit; the monthly report says so (BW-MON-04).

### 19.2 Infrastructure

| ID | Requirement |
|---|---|
| BW-INF-01 | One machine, no inbound public ports, Tailscale and SSH keys only, Docker Compose, outbound allow-list (IBKR, EODHD, ASIC, Telegram, backup store, dead-man monitor) (INF-02, INF-03, BP-09). |
| BW-INF-02 | Persistent encrypted volume for databases, raw store and chain; daily encrypted off-site backup; quarterly restore drill to a clean machine; a fresh machine reaches a working system in under two hours (INF-01, BP-16, CA-03). |
| BW-INF-03 | Capacity: raw store grows by about 15–25 MB a day compressed; plan 20 GB a year; disk alert at 15% free (BW-DAT-09). Daily chain 22:00–22:45 must finish in under 30 minutes on the reference machine with 600 eligible entities, 30 forecasters, 12 books and 700 twins. |
| BW-INF-04 | Monthly cost report against the budget; WARN at 110% of the yearly plan pro rata. |
| BW-INF-05 | Secrets by Docker secrets only; none in files, logs or reports; the research agent has read access to derived data and no secret (CA-03, M0 `secrets.py`). |
| BW-INF-06 | Dependencies from a hash-verified lock file; no package younger than 14 days (BP-10; as M0). |

---

## 20. Configuration (`config/common.yaml`, schema v4)

```yaml
version: 4
spec_hash: "<sha256 of FD_v3.0_BigWins.md>"
execution:
  mode: advisory                      # advisory | paper_auto | pilot | live   (BW-SYS-16)
  broker_book: EMG2_100k
  order_type: LOC
  submit_loc: "15:45"
  limit_band: {A: 0.02, B: 0.02, C: 0.03, D: 0.03}
  carry_sessions: 3
  min_parcel_aud: 500
  commission: {model: asx_fixed, rate_incl_gst: 0.00088, min_incl_gst_aud: 6.60}
live_emg2_20: {enabled: false, capital_cap_aud: 10000, slots: 20, min_parcel_aud: 500, cash_reserve_aud: 50, skip_lottery: true,
               order_value_max_aud: 800, orders_per_day: {start: 24, normal: 16}, buys_per_day_aud: {start: 10500, normal: 4500},
               value_review_aud: 7000, value_halt_buys_aud: 6000, value_line_halt_aud: 5000, per_order_approval_until: "2027-04-30",
               fallback_limit: {send: "15:30", cancel: "15:58", band: 0.03}, buy_funds_wait_sessions: 4}   # section 7.9; enabled only by the signed checklist
capital: {paper_aud: 100000, pilot_cap_aud: 10000, scale_cap_aud: 50000, investable_assets_aud: null, pilot_max_share: 0.05}
schedule:                             # Australia/Sydney
  ticks: ["10:30", "12:30", "14:30", "16:20"]
  fetch_eod: ["19:30", "21:30", "07:00"]
  fetch_aux: "19:40"
  validate: "21:40"
  universe_features: "21:50"
  forecast_daily: "22:00"
  resolve_daily: "22:10"
  decide: "22:20"
  book_day: "22:30"
  replay_check: "22:40"
  report_daily: "22:45"
  heartbeat: "20:00"
  backup: "01:30"
  full_redownload: "Sun 03:00"
  learn_weekly: "Sat 06:00"
  learn_monthly: "first Sat 06:00"
  research_cycle: "first Sat 08:00"
  approval_deadline: "15:30"
universe:
  bands: {A: [1, 100], B: [101, 300], C: [301, 600]}
  tv_med252_min_days: 120
  tv_med63_min_days: 30
  eligible: {min_close: 0.10, min_tv_med63: 100000, traded_within_sessions: 5}
  duplicate_test: {min_common_days: 120, min_nonzero: 100, pearson: 0.995}
  code_reuse_gap_days: 200
  lottery: {max_age_sessions: 504, max_close: 0.20, max_tv_med63: 250000}
data:
  eodhd: {credits_per_day_max: 20000, min_left: 25000, exchange: AU}
  tick: {stale_minutes: 40, absurd_move: 0.60}
  asic: {max_age_days: 45}
  spike: {abs_return: 0.60}
  restatement: {block_rows: 5, block_pct: 0.005}
  disk_free_page: 0.15
lines:                                # each pinned by hash; runner refuses a mismatch (BW-SYS-14)
  H82:  {rules: "67_FINAL_RULES_v1.3.md", sha256: "b38abcd7...", amendments: [start_now, v1.4, v1.5, v1.6], role: control, gate_rule: v2}
  M3:   {rules: "AMENDMENT_shadow_M3_v1.1.md", sha256: "3ea15453...", role: shadow, gate_rule: v2}
  E3:   {rules: "AMENDMENT_shadow_M3_E3.md", sha256: "57342708...", role: shadow, gate_rule: v2}
  ACC:  {rules: "AMENDMENT_shadow_ACC_keep_winners.md", sha256: "428a9a00...", role: shadow, gate_rule: none}
  CXL:  {rules: "AMENDMENT_shadow_CXL_D2.md", sha256: "057c1e55...", reading: "AMENDMENT_shadow_CXL_v1.1_reading.md", role: shadow, gate_rule: none}
  EMG2: {rules: "AMENDMENT_shadow_EMG2.md", sha256: "<at registration>", role: challenger, gate_rule: v3,
         params: {top_fraction: 0.2, band: C, single_name_cap: 0.10, trim_to: 0.075, min_names: 150, twins: 100}}
  EARLY: {rules: "84_AMENDMENT_shadow_EARLY.DRAFT.md", sha256: "<at registration>", role: shadow, gate_rule: v2}   # section 8.5
twins: {seed_base: {EMG2_100k: 8530000, EMG2_25k: 8540000}, redraw_prob: 0.2}
risk:
  order_value_max: 0.03
  position_at_cost_max: 0.03
  lottery_position_max: 0.0125
  lottery_total_max: 0.15
  early_sleeve_max: 0.10
  participation_max: 0.05
  price_band: {A: 0.03, B: 0.03, C: 0.05, D: 0.05}
  gap_hold: 0.15
  max_orders_per_day: 80
  max_buy_turnover: 0.60
  drawdown: {review: 0.30, halt_high_swing: 0.50, halt_index_like: 0.35}
  rel_12m: {review: -0.25, halt: -0.40}
  day_move: {review: -0.07, halt: -0.12}
  cost_vs_model: {review: 1.5, halt: 2.5, min_trades: 30}
  single_name: {review: 0.10, halt: 0.20}
  sector_review: 0.50
  suspended: {halt_share: 0.15}
  real_money_floor: 0.60
alerts: {holding_move: 0.08, holding_page: 0.20, bid_jump: 0.20, volume_surge_mult: 3.0, broken_share: 0.10}
learning:
  horizons_daily: [5, 21, 63, 126, 252]
  horizons_tick: [NT, CL, 1D, 5D]
  status: {young_formations: 250, informative_t: 2.0, strong_t: 3.0, strong_formations: 500, dead_t: 1.0, dead_formations: 500}
  cusum: {reference: 0.5, limit: 4.0}
  placebo_t_page: 2.5
  cost_update: {n0: 30, clamp: [0.5, 3.0], new_version_move: 0.20}
  max_new_forecasters_per_month: 2
  max_new_lines_per_year: 2
research: {trials_start: null, trials_per_quarter_max: 24, cards_per_cycle_max: 2}   # trials_start set once by the record keeper
tax: {rate: 0.32, discount: 0.5, discount_days: 367, regime: A, parcel_method: FIFO, year_end: "06-30"}
gates:
  v2: {min_months: 36, t: 3.0, lead_after_tax: 0.01, random_pct: 0.90, staged: {months: 60, t: 2.0, slice_aud: 50000, min_names: 25}}
  v3:
    p1: {paper_months: 12, cost_ratio: 1.5, min_fills: 100, twins_pct: 0.60, spread_mean_gt: 0.0, cap_aud: 10000, names: 20}
    p2: {months: 24, pilot_months: 6, spread_t: 2.0, twins_pct: 0.80, after_tax_floor: -0.05, cap_aud: 50000}
    p3: {months: 48, spread_t: 3.0, twins_pct: 0.90, after_tax_lead_gt: 0.0}
    stop: {from_months: 13, spread_t: -1.0, twins_pct: 0.20, after_tax_from_months: 24, after_tax_floor: -0.15}
```

`config/<user>.yaml` holds account ids, Telegram ids, approval pins, `investable_assets_aud`, the tax rate, and nothing secret. Unknown keys are rejected (M0 strict YAML).

---

## 21. Milestones and acceptance tests

M0 and M1 of the repository are reused; the first task is to re-base them (drop L1, sleeves, benchmarks B1–B3, the 20-call budget; keep everything in section 0.2).

| Milestone | Deliverable | Acceptance tests (all automated unless marked) |
|---|---|---|
| **B0 Foundations and reality spike** (week 1) | Forward record on durable storage; `trader import forward-record`; chain verify; spike report | Imported chain head equals `$F/LEDGER.jsonl`'s; restore drill on a clean machine [manual, recorded]; spike report answers O-1 to O-3 with evidence or marks them blocking; repo re-based with no L1 remnant (grep test); `requirements.csv` lists every BW id |
| **B1 Data layer** | `eodhd_bulk`, `asic`, `identity`, `universe`, `features`, `intraday`, `newlist`; verdicts | Rebuilds the top-300 universe and H82/M3 score files of 30 Oct, 13 Nov and 16 Nov 2026 exactly (the three frozen snapshots); the ten duplicate pairs of report 81 §3.1 and the `_old` companies of report 80 §1.1 are merged or admitted (named-case tests); truncation invariance on 50 dates; credit budget fails closed; tracker classification test (BW-NL-02); tick snapshot stored for four ticks on three sessions |
| **B2 Prediction ledger** | `forecast/`, scoreboards, `LEARNING_*` reports, tick job | A seeded synthetic signal with known IC is recovered within its error band; the placebo's t stays inside ±2 on 2018–2026 history; forecasts cannot be inserted after their entry time (test); resolve is idempotent; BW-LRN-01 (random tick data changes no decision); replaying 2018–2026 reproduces report 85 T4's band-C TOP−ALL within 0.5 points a year before duplicate removal, and reports the corrected figure after |
| **B3 Lines and parity** | `lines/` for H82, M3, E3, ACC, CXL, EMG2; twins; measurement lines; `replay_check` | BW-STR-10 parity for each line over three decision dates; EMG2 native result on 2018–Oct 2026 within the stated tolerance of `t6.json` with rules 8–9 switched off, and reported with them on; twins reproducible from seeds |
| **B4 Books, tax, chain, registry** | `books`, `tax`, `hashchain`, `register` command | NAV of every imported book equals the record to A$0.01 on every day since 17 Nov 2026; tax readings equal scoring v2's; chain tamper test (one changed byte is detected); a result whose registration is later than its first data is refused |
| **B5 Risk, approval, alerts** | `risk`, `approval`, Telegram | Each BW-RSK check has a rejecting and a passing case; property test: no generated intent set can pass with a limit broken; approval lapse, veto, expiry and re-approval paths; every alert fired once and received [manual, recorded] |
| **B6 Broker and execution** | `broker/ibkr.py`, `LOC` path, reconciliation, shortfall report | Recorded-session replay tests; crash injection between persist, send and acknowledge gives exactly one order per intent; paper/live guard; 10 band-C `LOC` orders filled on the paper account and reconciled to the unit and the cent [manual, recorded]; then Gate G2 |
| **B7 Research harness** | `research/`, cards, backlog, trial log, monthly cycle, restatement recompute | Trial rows written automatically, pass or fail; a card cannot run unregistered; regression results of BW-RND-04; the agent's role cannot write to config, lines or order tables (permission test) |
| **B8 Pilot readiness** | Gate evaluation, proposal writer, runbooks, hardening | `gate_review` on a synthetic record produces the right step for each of 12 cases, including each stop; `pilot` and `live` refuse to validate without a signed gate record (every bypass attempt tested); BP-21 checklist recorded |

### 21.1 B-fast: the minimum safe path to real EMG2-20 orders by mid-December 2026 (D-12)

B-fast is built in the repository, in the modules the full build will keep (`lines/emg2.py`, `orders.py`, `risk.py`, `approval.py`, `broker/ibkr.py`, `execution.py`, `reconcile.py`, `report.py`). Until B1 exists it reads prices from the forward store the record's scripts already maintain (`$B/bigwins_forward/data/eodhd`, read-only adapter) and writes orders, fills and approvals to the M0 ledger tables and one line a day to `LEDGER.jsonl`. It does **not** include the prediction ledger, other lines, the research harness or the tax engine beyond parcels; those follow in B1–B8.

| Step | Dates | Deliverable | Acceptance tests |
|---|---|---|---|
| BF0 Accounts and machine | 20–27 Nov | Owner: IBKR Pro individual cash account (ASX permission), paper account enabled, always-on machine; operator: durable volume, backup, Tailscale, secrets; **reality spike** on the paper account | Paper login headless; one paper buy and sell of a band-C share; `LOC` accepted or refused with the cut-off recorded (O-1); order found by `orderRef` after a gateway restart (O-3); Flex or API executions readable; restore drill done |
| BF1 EMG2 decision engine | by 30 Nov | `lines/emg2.py` and the record script from section 7.6; registered; EMG2-20 selection (7.9 L2–L5) | Reproduces `$B/deep85/out/t6.json` holdings on 12 sampled month-ends from the same data with rules 8–9 off; pure and deterministic (BW-SYS-10); truncation invariance on 20 dates; the 30 Nov list and the EMG2-20 picks written and hashed before the 1 Dec open |
| BF2 Orders, breaker, approval | 1–4 Dec | `build_orders()` for 7.9; breaker with L10–L11 and BW-RSK-01 to 03, 06 to 09, 11; Telegram `/ok`, `/veto`, `/pause`, `/kill` | Property test: no intent set passes with a limit broken; each limit has a rejecting case; an unapproved order is never sent (test with the approval table empty); `/kill` cancels open orders within 60 seconds on paper; orders under A$500 never generated |
| BF3 Broker path | 1–9 Dec | `broker/ibkr.py` with the paper/live guard (`DU` prefix on paper; the live account id pinned in config), idempotent `client_order_id`, persist-before-send, no resend on timeout, quote record | Crash injection between persist, send and acknowledge: exactly one broker order per intent; guard refuses a live id in paper mode and a paper id in live mode; **paper dry run 1:** the 30 Nov EMG2-20 list bought on the paper account on the first ready session, every fill reconciled |
| BF4 Reconciliation and report | 7–11 Dec | Positions and cash against IBKR to the unit and the cent after every broker day; daily Telegram report (holdings, value, orders, fills, costs, flags); simulated twin `EMG2_20_SIM` | A planted position mismatch halts and pages within 5 minutes; **paper dry runs 2–5:** on four sessions a scripted sell-and-rebuy of two holdings exercises the monthly cycle, the approval flow, a carried order and a cancel; report received each day |
| BF5 Go-live checklist | Fri 11 Dec (re-read Mon 14 Dec) | Checklist below, each line with evidence, signed by the owner with the second factor | All lines true, or the start moves (7.9 L6) |
| BF6 Live start | from Mon 14 Dec | Start decision; canary (one A$500 parcel); remaining buys after the canary reconciles | Canary fill, commission and cash match the ledger to the cent before any further live order |

**Go-live checklist (every line must be true and evidenced before the first live order):**

1. Reality spike filed; order type for live decided (LOC or the 15:30 limit fallback) with evidence.
2. At least five paper sessions with orders, all reconciled exactly; no open incident.
3. Every breaker limit of 7.9 L10–L11 demonstrated on paper with a rejecting case in the log.
4. `/kill` and `/pause` drilled from the owner's phone on paper; re-arm needs the second factor.
5. Unapproved orders proven not to be sent; approval expiry proven.
6. Paper/live guard proven both ways; the live account id pinned; the API user has no funding rights or the limitation is recorded (BP-08).
7. IBKR account precautions set (L10) and photographed.
8. Deposit of A$10,000 arrived and settled; `capital_cap_aud` = 10,000.
9. Backups running; one restore done; machine has no inbound public port (scan).
10. Dead-man heartbeat received externally for five days.
11. `AMENDMENT_shadow_EMG2`, `AMENDMENT_adopt_rule_v3` and `AMENDMENT_live_EMG2_20` registered in the ledger; code hashes pinned.
12. The duplicate test A7(c) and the class filter applied to band C; the start list reviewed by the owner (names, prices, traded value), with any name the owner does not recognise as an ordinary operating company queried before approval.
13. The owner has signed the risk statement (18.5) and stated that A$10,000 is no more than 5% of investable assets, or has waived that limit in writing.
14. Tax records: parcels written for paper fills; the owner knows that nearly all gains will be short-term.
15. A named person (the owner) will be reachable to approve orders by 15:20 on execution days through April 2027.

If any line fails, the live start waits. **The date is a target; the checklist is the gate.** Honest schedule risk: three and a half weeks for BF0–BF5 is tight, and the IBKR account opening and the reality spike are outside the build agent's control.

Order and dependency (full build, in parallel with and after B-fast; B-fast code is kept, not thrown away): B0 → B1 → (B2, B3 in parallel) → B4 → B5 → B6 → B7 → B8. Gate G1 after B4; G2 after B6. The first forward decisions (30 Nov 2026) are taken by the scripts of record; nothing waits for the build.

---

## 22. Open items

| # | Item | Blocks | How it closes |
|---|---|---|---|
| O-1 | IBKR: `LOC` on ASX through the API, its entry and cancel cut-off, behaviour in the paper account for small shares (v2.13 I10, I18) | G2 | Reality spike |
| O-2 | IBKR cash account: when auction-sale proceeds can fund a buy (v2.13 I4); GST line on commission (I1) | G2, G3 | Spike; first statement |
| O-3 | IBKR paper: balance setting, Flex for paper accounts and its timing (I14, I22), `orderRef` after restart (I5) | G2 | Spike |
| O-4 | EODHD plan actually held: price, credits, which endpoints (fundamentals, estimates, delayed quotes) | Budget; B1 | Owner's invoice; one `user` endpoint call |
| O-5 | Announcements feed: a licensed source of headline, time and price-sensitive flag under about A$50 a month (D-6) | Backlog item 9 only | Research agent lists options with terms; owner confirms before purchase |
| O-6 | The owner's A$0 platform: share list (is band C on it?), order types, closing-auction access, custody model | Broker choice at G3 | Owner asks the platform |
| O-7 | Capital-gains rules from 1 July 2027 (regime B) | Tax readings labelled B | Tax agent or the legislation |
| O-8 | Parcel selection method acceptable for the real-money book | `parcel_method: min_tax` | Tax agent |
| O-9 | Real spreads and impact in band C (gap C1) | G3 evidence | Paper fills and quotes; pilot |
| O-10 | Reports 83 and 84 landed on 19 Nov 2026 and are reflected in section 8.5 and the backlog. Still open: registration of EARLY ([R84-4]) and of report 83's multi-market traded-value fix | [R84-4] | Record keeper, before 30 Nov |
| O-11 | New-listings tracker ISIN field | BW-NL-02 acceptance | One-line fix; re-run classification |
| O-12 | Duplicates not removed in report 85's T4–T6 | EMG2's reference figures | Backlog item 2 |
| O-13 | Whether the paper account's simulated auction fills resemble real ones | Meaning of P1's cost test | Compare paper fills with the official close and recorded quotes; if useless, P1's cost test moves to the pilot's first 100 fills and P1's money stays at A$10,000 until then |

---

## 23. What to register and implement first

| Order | Action | Owner of action | By |
|---|---|---|---|
| 0 | **B-fast (section 21.1) for the A$10,000 live slice: owner opens the IBKR account and provides the machine now; register `AMENDMENT_live_EMG2_20.md` (draft in `$B/deep85/`)** | Owner; build agent; record keeper | BF0 by 27 Nov; checklist 11 Dec |
| 1 | Ledger note for report 85: trials T1–T6 (+6), pre-registration hashes, verdicts | Record keeper | Now |
| 2 | Register `AMENDMENT_shadow_EMG2.md` (draft in `$B/deep85/`); write and hash `paper_emg2.py`; apply A7(c) to the band-C universe first | Record keeper | Before the 30 Nov 2026 decision |
| 3 | Register `AMENDMENT_adopt_rule_v3.md` (draft in `$B/deep85/`) | Record keeper (owner decided D-3) | Before 30 Nov 2026 |
| 4 | Move the forward record to durable storage; off-site copy; restore test | Operator | This week (disk at 98%) |
| 5 | Fix the tracker's ISIN field | Tracker owner | This week |
| 6 | B0 reality spike | Build agent | Week 1 |
| 7 | B1, then B2 and B3 | Build agent | Next |
| 8 | Register EARLY from `84_AMENDMENT_shadow_EARLY.DRAFT.md` (unproven shadow) and report 83's multi-market traded-value amendment | Record keeper | Before 30 Nov 2026 |

## 24. Sources

Reports 31–85 in `$R` (in particular 59, 62, 67, 68, 70, 72–82, 85); `$F` ledger and amendments; FD v2.13 (`$B/onedrive/FD_FINAL_LATEST.md`); repository `/home/user/asx-trader` (M0, M1) and `$B/trader_system/GAP_ANALYSIS.md`; `OWNER_DECISIONS_2026-11-19.md`; new-listings tracker code and store; `$B/deep84/PREREG_84.md`; `$B/deep85` (pre-registrations, code, results of T1–T6).
