# NEXT — B-fast for the EMG2-18 slice (FD v3.0 §7.9, §21.1; AMENDMENT_live_EMG2_18), state on 19 Nov 2026 (after piece 3, corporate actions, splits, the Flex pull and the band-trend switch)

Branch: `bigwins-fast` (pieces 1-3 merged; `bigwins-fast-wip` merged fast-forward at
c07197c and deleted locally; **its remote copy could not be deleted from this session**
(the git proxy refuses branch deletion): delete `origin/bigwins-fast-wip` by hand, it
points at c07197c, already in `bigwins-fast`). **Paper only.** No code here can place a real order:
`LIVE_TRADING_ENABLED` is hard-coded `False`, `allow_live` is `Literal[False]` in the
config schema, and the adapter refuses live ports, non-`DU` accounts and a gateway
that manages any non-`DU` account. Live enablement is a separate owner step after the
go-live checklist, by a reviewed code change.

## Built and tested (ruff, mypy --strict, pytest, req_coverage `--milestone BF`)

| Step | Where | State |
| --- | --- | --- |
| BF1 EMG2 / EMG2-20 engine | `trader/panel.py`, `features.py`, `universe.py`, `lines/emg2.py`, `data/identity.py`, `data/forward_store.py` | Done. Golden vs T6: see DECISIONS BF-D7 |
| BF2 orders, breaker, approval | `trader/orders.py`, `risk.py`, `approval.py` | Done (Telegram behind an interface; mock + Bot API transport) |
| BF3 broker path | `trader/broker/{base,ibkr,paper_sim}.py`, `journal.py`, `execution.py` | Done against a mock gateway; **not yet run against a real paper gateway** |
| BF4 reconciliation, report | `trader/reconcile.py`, `report.py`, `runner.py` | Pieces done; scheduling not |
| Deploy | `deploy/docker-compose.yml`, `deploy/Dockerfile`, `docs/SETUP_SYDNEY.md` | Stub; images pinned by digest; `docker compose config` passes |

## Piece 1 (done on `bigwins-fast-wip`, 19 Nov 2026)

- WIP commits 4bcdf09/912e609 reviewed and kept (DECISIONS BF-D13): scheduler, `bf_app`
  jobs, dry-run harness, mock gateway. ruff, mypy --strict, pytest (435), BF gate green;
  record replay and T6 golden tests pass where the data are mounted.
- Owner decisions applied (BF-D14): EMG2-18 (18 / A$550, configurable; real 30 Oct list:
  18 orders >= A$500 after commission, band and reserve); A$10,000 cap on new buys;
  A$800 per buy, larger sells sent and paged; `config/lic_list.csv` = the record's
  frozen list, SHA-256 pinned (BF-D6 closed); loss rule: value < A$6,000 ->
  `HALTED_BUYS` once per breach, high-priority page, holdings kept, sells continue,
  only `/resume <code>` re-enables buying (superseded in piece 2 by BF-D15).
- Scheduler: `run_forever` tested on a fake clock over a month-end (each job once a
  session; decision at the month-end only; orders the next session; unapproved orders
  lapse, never sent; late `/ok` refused); the broker book cannot use `auto` approval.

## Piece 2 (done on `bigwins-fast-wip`, 19 Nov 2026)

- **L11 staged loss rule** (owner, report 88 §4.2; BF-D15; replaces BF-D14's rule):
  < A$7,000 page + integrity check; < A$6,000 buys pause until the next month-end
  decision, then resume automatically unless (a) integrity fails, (b) twin < 10th
  percentile of its random twins, (c) L12 stop, (d) owner `/stop`; < A$5,000 also needs
  `/continue <code>`, else the book is sold over two decisions (`-W` batches). Sells
  continue in every stage; the registered A$5,000 `HALTED_LINE` is gone (old open point 1).
- **Per-book safety** (BF-D16): the twin `EMG2_18_SIM` has its own latch; `/pause`,
  `/kill`, `/stop` and L11 of the paper book never stop it.
- **Record-data dry run** (`tests/test_bf_record_replay.py`, BF-D17): 30 Oct start with
  canary (2 Nov), the 17 on 3 Nov, sessions to 18 Nov, forced 18 Nov decision; every
  buy >= A$500 / <= A$800, reconciled to the cent every session, L13 explained, one
  PAPER report a session. Canary unfilled / recon broken / restart between canary and
  the 17, and the L11 drill, all on record data.
- Found on the record: **HGO** (held) is missing from the feed on 16-18 Nov; a held name
  without a mark is now valued at its last mark and flagged (was valued at zero).

## Piece 3 (done on `bigwins-fast`, 19 Nov 2026)

- Gate after piece 3: ruff, format, mypy --strict, validate-config x2, pytest 479
  passed (7 skipped: Postgres), BF coverage gate; record replay 5/5 and T6 golden 3/3
  with the data mounted.
- **Merge**: `bigwins-fast-wip` fast-forwarded into `bigwins-fast`; full gate green on
  `bigwins-fast` (ruff, format, mypy --strict, both validate-config, pytest,
  `req_coverage --milestone BF`; record replay and T6 golden with the data mounted).
- **100 random twins** `EMG2_18_RND_s001...s100` (seeds 8550000 + i; BF-D18): the
  simulated twin's code path and costs with a persistent seeded random score per entity
  (redrawn p = 0.2 a month) in place of rule 3's order; daily percentile in the report
  and the journal; `BfApp.twin_rank` reads it, so **L11 test (b) runs and stage 2
  resumes automatically** (go-live blocker closed). Golden: a twin given rule 3's order
  equals `EMG2_18_SIM` to the cent; record replay 30 Oct-18 Nov pinned: on 18 Nov the
  twin (A$9,856.95 with HGO carried as KAN) is at the 41.0 percentile of its 100
  random twins (values digest `23843130ca83`); re-pinned for BF-D20 below.
- **Journal under Alembic** (branch `journal`: j0001 baseline, j0002 `bf_safety.scope`
  (BF-D16), j0003 `bf_identity`); test on SQLite (and Postgres where available); CI
  migrates `journal_ci`. Existing journals: `alembic -x db=journal stamp j0001`, then
  `upgrade journal@head`.
- **Code changes** (BF-D19): a held code that stops trading and that A7 maps to a
  trading code is carried under the new code (HGO -> KAN on 16 Nov 2026 in the
  record), never bought twice, reconciled against a broker still on the old code, owner
  paged to confirm `/idmap OLD NEW <code>` or undo `/idmap_reject OLD <code>`.

## Share-list fixes (BF-D20, 19 Nov 2026; owner decision, AMENDMENT_class_rule_fix.md)

- Class `LIC` by the frozen list only (`config/lic_list.csv` = record `LIC_list_frozen_v2.csv`,
  69 codes, pin `af441f28...`); no name words. Ranks among ORD + REIT (BW-UNI-11 amended);
  medians ignore sessions without a row, as the registered EMG2 table. The live T on
  30 Oct and 18 Nov 2026 equals the paper EMG2_18_REF list exactly (test with the record
  mounted). Record replay re-pinned: start buys RG1 instead of AMI; twin at the 49.0
  percentile on 18 Nov (digest `168fa642af30`). Run the data-mounted tests with
  `TRADER_BF_LIC_LIST` pointing at `LIC_list_frozen_v2.csv` (v1 is refused by the pin).

## Corporate actions (BF-D23..D25, 19 Nov 2026; review finding)

- Gate: ruff, format, mypy --strict, validate-config x2, pytest 507 passed (18 skipped),
  BF coverage gate; record replay 5/5 with the data mounted (pins unchanged: no
  calendar event of a held name in 30 Oct-18 Nov).
- **Journal**: `bf_corporate_actions` (Alembic j0005) and `bf_identity.ratio`; positions,
  cash, capital-cap cost and `Journal.tax_view` include dividends, specials, capital
  returns (cost base; G1 above it), demergers (cost apportioned), in-specie receipts,
  splits, disposals, cash in lieu. Existing journals: `upgrade journal@head`.
- **Paper (and later live) book: IBKR's own records only** - Activity Flex XML files in
  `data.flex_inbox` (`/data/flex/inbox`), read before each 16:30 reconciliation, booked
  once each. **Twin + random twins: the calendar** (vendor dividends + the record's
  `CORPORATE_ACTIONS.csv`, `data.corporate_actions_csv` / `$TRADER_BF_CA_CSV`; the CSV
  overrides the vendor) on the ex-date.
- **Reconciliation** tolerates a pending calendar event of the right size (until pay
  date + 10 days) and halts on everything else; L13 explains recent demerger codes.
- **BF-D24**: demerged / in-specie shares are sold at the next month-end decision
  unless the new company is on T (rule L4 unchanged).
- **BF-D25**: `/idmap OLD NEW [RATIO] <code>` confirms a code change with a ratio, or
  maps a rename the vendor does not link (e.g. Platinum -> L1 Group).
- Compose mounts two more paths: `RECORD_DIR` (the record's `68_forward_record`, read
  only) and `FLEX_INBOX` (Flex XML of the paper account).
- Still open: ~~the Flex Web Service pull into the inbox is not scheduled~~ (done,
  BF-D27 below; timing still to confirm in the reality spike, O-3); IBKR's
  exact ASX `CorporateAction` types/descriptions on paper are **unverified** (synthetic
  fixtures); ~~vendor split events are not yet applied to simulated holdings~~ (done,
  BF-D26 below).

## Splits and consolidations (BF-D26, 19 Nov 2026)

- Twin and random twins: vendor split rows (forward store) or a CSV `split` /
  `consolidation` row adjust holdings on the split date (count x ratio, cost per share /
  ratio, total cost kept). Paper book: from IBKR's Flex record; until it arrives the
  calendar split explains the broker's new count in reconciliation and the book is
  valued and sized at the expected count. Tests: 1-for-10 and 2-for-1, unit and app.

## Scheduled Flex download (BF-D27, 19 Nov 2026)

- Job `flex_pull` at 13:05, 14:05, 15:05, 16:05, 16:25 (before the 16:30 reconciliation):
  the paper account's Activity Flex statement to the previous session into `FLEX_INBOX`
  (`flex_<fd>_<td>.xml`, atomic, once a day), 2 tries a slot within 40 s; paged once a
  day if still missing at 16:25, or at once if the token/query secret is missing, IBKR
  refuses the token, or the statement is not of a `DU` account.
- Owner on the server: `deploy/secrets/ibkr_flex_token` and
  `deploy/secrets/ibkr_flex_query_id` (chmod 600; never in config or git); the paper
  Flex query with Cash Transactions (exDate/payDate) and Corporate Actions;
  `FLEX_INBOX` is now mounted writable; raw responses in `/app/out/flex_raw`.
- Gate after BF-D26/D27: ruff, format, mypy --strict, validate-config x2, pytest, BF
  coverage gate green; `docker compose config` passes.

## Band-trend switch L15 (BF-D28, owner decision after report 96; AMENDMENT_live_EMG2_18_BT.md, ledger seq 71)

- At each month-end (and the start) the equal-weight index of band C (ranks 301-600) is
  compared with its 10-month average: below = **state: FUND** (sell the EMG2 shares, one
  A200 order with the cash), at or above = **state: EMG2** (sell A200, buy the picks).
  Broker book, twin and the 100 random twins switch together; every report and decision
  message shows the state.
- **On the record's data the state is FUND on 30 Oct and 18 Nov 2026**: the paper month
  and very likely the live start begin in A200 (replay test, switch on). The older record
  replays run with the switch off to keep testing the EMG2-18 path.
- Config `band_trend` (on in `config/bfast.yaml`). The paper record runs the same rule as
  `EMG2_18_SIM_BT` (+100 twins) in `paper_emg2bt.py` (ledger seq 70/72).

## Tax report (BF-D29, 19 Nov 2026)

- `trader-bf tax-report --fy 2026-27` (`trader/tax_report.py`): parcels (FIFO default,
  `tax.parcel_method`), capital gains short-term v discount-eligible (367-day margin),
  losses and carry-forward, dividends with franking, capital returns, demergers, splits,
  code changes, A200 distributions (AMIT "from the annual tax statement - enter manually",
  `tax.amit_csv`), brokerage, and a reconciliation against the Flex inbox. General
  information, not tax advice. Owner: confirm FIFO (or specific identification) with the
  accountant; give the accountant the summary + CSVs after 30 June 2027.

## Owner go-live guide (19 Nov 2026)

- `docs/GO_LIVE_GUIDE.md`: IBKR (Pro cash, ASX, tiered, paper, precautions above
  A$10,000, market data, Flex token + Activity query with the sections the parser
  reads), BinaryLane + Tailscale + Docker + deploy key, `deploy/.env` (now lists
  `RECORD_DIR`, `FLEX_INBOX` in `.env.example`), the nine secret files, Telegram + chat
  id + TOTP seed, the FUND-start canary (one A200 order) with example messages, the
  commands as implemented, and the remaining checklist.
- Found while writing it (for the reality spike, before any paper order):
  (1) ~~`trader-bf deposit` / `kill` / `pause` / `status` use `--journal` or a local
  SQLite file~~ fixed (BF-D30): they use the running app's journal (config
  `journal.url_env`, Postgres + `db_password` secret); SQLite only when named explicitly. (2) The paper account's made-up starting balance must equal
  the journal deposit (cash is reconciled to the cent; L11 assumes A$10,000): reset
  the paper balance or decide another way. (3) Compose file secrets are bind mounts
  with host permissions; the trader runs as uid 10001, so `chmod 600` root files are
  unreadable: guide uses `444` files in a `700` folder; confirm each container reads
  its secrets. (4) ~~The daily refresh of `FORWARD_STORE` on the server is not built~~ built
  (BF-D31): job `store_refresh` 17:35..22:05, EODHD bulk AU closes + dividends + splits,
  counted budget in the journal, idempotent, no decision on a stale store (paged);
  timing against the real EODHD service to confirm in the spike.
  (5) In FUND state the book places one order and then none, so go-live item 2 (five
  paper sessions with orders) needs a plan in the spike.

## Owner / record keeper points still open

1. **Amendment for the staged L11 rule** (record keeper), with the interpretations of
   BF-D15: HALTED_LINE replaced by stage 3; BW-RSK-29 / 12% day fall / 50% drawdown
   cleared by an automatic resume inside an episode; "within one decision" = the first
   month-end decision after the stage-3 breach, sale starting at that decision; the
   wind-down sells still need per-order approval (L8). Owner: confirm or correct.
2. ~~100 random twins~~: built (BF-D18). Record keeper: confirm the counter-based
   score (BF-D18) as the registered method for `EMG2_18_RND_*`, or name another.
3. L12 stop input (`l12_stop`) is a hook only; none applies before the first December
   review 13 months after registration.
4. HGO -> KAN (BF-D19): handled as a code change (PROPOSED); record keeper / owner to
   confirm from the ASX announcement (`/idmap HGO KAN <code>`), and the record's own
   books to follow.
5. Raise the IBKR precaution "max order value" above the largest expected sell before
   go-live (BF-D3).
6. **Corporate actions** (BF-D23..D25): record keeper keeps `CORPORATE_ACTIONS.csv`
   current for held names (kind, ratio, and the class-ruling `cost_base_pct` /
   `capital_per_share` / `franked_pct` where known; a `PROVISIONAL` / `UNCLASSIFIED`
   report flag asks for them); owner confirms BF-D24 (sell demerged shares at the next
   month-end unless on T) and adds Cash Transactions (with exDate/payDate) and
   Corporate Actions to the paper Flex query.
7. **BF-D28 (L15)**: confirm (a) the single A200 order is exempt from the A$800
   per-buy limit (paged) - IBKR's precautionary order value must then be above A$10,000;
   (b) a switch decision uses L10's start-day limits; (c) at a FUND start the canary is
   the fund order alone.

## Next build steps, in order

1. **Reality spike on the paper gateway** (needs the IBKR paper login on the server):
   run `tests` marked `integration` (to write) for: LOC accepted/cut-off (O-1),
   funds from auction sales (O-2), `orderRef` after restart, Flex timing (O-3),
   account-value tags, delayed quotes. Record results here; switch
   `execution.order_type` to `LMT` if LOC is refused.
2. **Book state from the journal + broker**: a `plan` job that builds `BookState`
   from journal positions/cash, runs `decide_emg2_20`, `build_orders`, `Executor.plan`,
   and sends `render_batch` to Telegram; a `submit` job (15:45 LOC / 15:30 LMT with
   `fallback_limit` from IBKR quotes); `collect_fills` at 16:20; `reconcile_and_page`
   at 16:30; L7 buy carry D+1..D+4 when funds are not yet available; sell carry 3 sessions.
3. **Runner**: APScheduler in the trader container (Australia/Sydney, ASX calendar,
   advisory lock, idempotent jobs), the Telegram polling loop (`ApprovalBot`), the
   `/kill` path wired to `Executor.kill` (must cancel within 60 s — BF2 test on paper).
4. **EMG2_18_SIM twin** and its **100 random twins**: done (BF-D18). The A200
   comparator (`EMG2_18_CMP_A200`, L14 monthly line) is still to build.
5. **Canary flow** (L6): done and replayed on record data (carry, stop, recon wait,
   restart); the paper-gateway run is part of dry runs 1-5.
6. **Heartbeat + backups**: healthchecks dead-man, nightly encrypted off-site copy,
   restore drill. One line a day to `LEDGER.jsonl` (FD §21.1; coordinate with the
   record keeper — this build does not touch `$B/bigwins_forward` or `$B/onedrive`).
7. **B4 ledger**: the `bf_*` tables are under Alembic (branch `journal`); still to do:
   move them into the v3.0 ledger database (grants, mutability guard).
8. **Paper dry runs 1-5** (BF3/BF4 acceptance) and the go-live evidence pack.

## Go-live checklist (FD §21.1) — status from this build

| # | Item | State |
| --- | --- | --- |
| 1 | Reality spike filed; LOC or 15:30 limit fallback decided | Open (needs paper login) |
| 2 | >= 5 paper sessions with orders, reconciled exactly | Open (runner + spike first) |
| 3 | Every L10-L11 limit demonstrated on paper with a rejecting case | Unit-tested; L11 staged rule drilled on record data (BF-D15/17); paper log open |
| 4 | `/kill`, `/pause`, `/stop`, `/continue` drilled from the owner's phone; re-arm needs 2FA | Code + tests done; phone drill open |
| 5 | Unapproved orders not sent; approval expiry | Code + tests done; paper log open |
| 6 | Paper/live guard both ways; live id pinned; API user without funding rights | Paper side tested; **live side is intentionally absent** in this build |
| 7 | IBKR precautions set and photographed; max order value above A$10,000 (largest sell, BF-D3, and the one A200 order of L15, BF-D28) | Owner |
| 8 | A$10,000 deposited and settled | Owner |
| 9 | Backups, restore, no inbound port (scan) | Open (compose has no published ports) |
| 10 | Dead-man heartbeat 5 days | Open |
| 11 | Amendments registered; code hashes pinned | Record keeper |
| 12 | A7(c) + class filter on band C; start list reviewed by the owner | Engine done; LIC list frozen and pinned (BF-D14, v2 BF-D20); a missing or changed list refuses every decision and order and pages (BF-D21, no fallback); owner review open |
| 13 | Risk statement signed; 5% of investable assets | Owner |
| 14 | Parcels for paper fills; short-term gains understood | Journal has fills and corporate actions (BF-D23); **FIFO parcel tax report** `trader-bf tax-report --fy 2026-27` (BF-D29: CSV + summary for the accountant, 367-day margin, losses carried forward, A200 AMIT entered by hand, reconciled to Flex); owner to confirm the parcel method with the accountant |
| 15 | Owner reachable by 15:20 through April 2027 | Owner |
| + | 100 random twins running (L11 test (b), staged-rule amendment registered) | Twins built and running (BF-D18); amendment registration with the record keeper |

## What remains before go-live (in order)

1. **Server**: BinaryLane Sydney server (owner orders it), Docker, Tailscale, no
   inbound port, `deploy/` compose up, `docs/SETUP_SYDNEY.md`.
2. **IBKR reality spike** on the paper gateway (item 1 above): LOC accepted / cut-off,
   auction-sale funds, `orderRef` after restart, Flex timing, account tags, quotes;
   and the Flex query's Corporate Actions / Cash Transactions rows for an ASX dividend
   (BF-D23 parser keys checked against a real statement); the scheduled Flex pull
   (BF-D27) run against the real Flex Web Service with the owner's token.
3. **Five reconciled paper dry runs** on a real IBKR paper gateway (sessions with
   orders, ledger = broker to the unit and the cent each day; go-live item 2).
4. **`/kill` drill from the owner's phone** (cancel within 60 s), plus `/pause`,
   `/stop`, `/continue`, `/idmap`; re-arm needs 2FA (item 4).
5. **Heartbeat and backups**: healthchecks dead-man 5 days, nightly encrypted
   off-site copy, a restore drill (items 9-10).
6. Runner on the server (APScheduler, Telegram polling) with the journal migrated
   (`alembic -x db=journal upgrade journal@head`) and the deposits recorded.

## What the owner must provide (on the server, never in chat)

- **IBKR**: IBKR Pro cash account with ASX permission and the paper account enabled;
  the paper username/password typed by the owner into the server's Docker secret
  files; the paper `DU` id into config. Later the A$10,000 deposit and the precautions.
  Pricing (report 91): IBKR **tiered** about A$710 a year at this book's turnover vs
  **fixed** about A$845 — choose tiered. Tiger / moomoo charge about A$3 an order but
  their APIs are unproven for this system (no paper-tested order path): not used.
- **BinaryLane** server in Sydney (always on), with Tailscale.
- **Telegram** bot token and the owner's chat id (secret file / config).
- **Authenticator**: the TOTP seed added to the owner's authenticator app (secret file).

Owner decisions still wanted: confirm the BF-D28 points (open point 7), the BF-D15
interpretations of the staged loss rule (open point 1), the HGO -> KAN code change (open point 4) and BF-D24 (sell
demerged shares at the next month-end unless on T; open point 6).
