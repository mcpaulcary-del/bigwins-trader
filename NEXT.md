# NEXT — B-fast for the EMG2-18 slice (FD v3.0 §7.9, §21.1; AMENDMENT_live_EMG2_18), state on 19 Nov 2026

Branches: `bigwins-fast` (tested baseline) and `bigwins-fast-wip` (this work: piece 1 of
3 done, green). **Paper only.** No code here can place a real order:
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
  only `/resume <code>` re-enables buying.
- Scheduler: `run_forever` tested on a fake clock over a month-end (each job once a
  session; decision at the month-end only; orders the next session; unapproved orders
  lapse, never sent; late `/ok` refused); the broker book cannot use `auto` approval.

## Piece 2 — full dry run, twin, canary (next)

1. **Replay 30 Oct and 18 Nov** end to end with `trader-bf dry-run` against the mock
   gateway (env as in the scratchpad `bfenv.sh`: `TRADER_FORWARD_STORE`,
   `TRADER_BF_LIC_LIST`, `TRADER_BF_ETP_LIST`): start decision 30 Oct with canary, the
   17 others after the canary reconciles, daily sessions to 18 Nov, an 18 Nov forced
   decision; check every order >= A$500, <= A$800 (buys), reconciliation to the cent
   every day, L13 notes explained, report banners. Store the summary (counts, digests)
   in DECISIONS; extend `test_BF_dry_run_replays_30_oct_and_18_nov_record_data`.
2. **Simulated twin per-book safety** (BF-D13 open point): the safety latch is
   journal-wide, so `/pause`, `/kill` and halts of the paper book also block the twin's
   buys. Give each book its own level (or exempt the twin from operational halts while
   it keeps L11), with a test that a paused paper book leaves `EMG2_18_SIM` buying.
3. **Canary flow (L6)** on replay: canary unfilled (carried once, then the start stops,
   paged), canary filled but reconciliation broken (the 17 wait), restart between canary
   and the 17 (journal-only state). Some exist on synthetic data; repeat on record data.
4. Loss-rule drill on the replay (marks scaled below A$6,000 mid-run): buys stop, sells
   continue, `/resume` re-enables; the daily report shows the halt.
5. Twin random books (100, seeds 8550000 + i) and the A200 comparator are not built yet.

## Piece 3 — merge

Merge `bigwins-fast-wip` into `bigwins-fast` (fast-forward or a merge commit; never
force-push), re-run the full gate on `bigwins-fast` (ruff, format, mypy --strict,
pytest, `req_coverage --milestone BF`, both validate-config steps), push, then delete
the `bigwins-fast-wip` branch locally and on origin. Update this file's header.

## Owner / record keeper points still open

1. A$5,000 `HALTED_LINE` (registered L11) also stops sells; the owner's loss rule talks
   only of A$6,000. Confirm whether the line halt should keep sells going (BF-D14).
2. Raise the IBKR precaution "max order value" above the largest expected sell before
   go-live (BF-D3).

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
4. **EMG2_18_SIM twin** booked daily with `SimBroker` from the 30 Nov decision and the
   L13 comparison (`compare_books`) in the daily report; 100 random twins (seeds
   8550000 + i) after that.
5. **Canary flow** (L6): start batch `-S`, canary `-C` (one buy), the other 19 after
   the canary reconciles to the cent.
6. **Heartbeat + backups**: healthchecks dead-man, nightly encrypted off-site copy,
   restore drill. One line a day to `LEDGER.jsonl` (FD §21.1; coordinate with the
   record keeper — this build does not touch `$B/bigwins_forward` or `$B/onedrive`).
7. **B4 ledger**: move `bf_*` tables into the v3.0 ledger (Alembic, grants, guard).
8. **Paper dry runs 1-5** (BF3/BF4 acceptance) and the go-live evidence pack.

## Go-live checklist (FD §21.1) — status from this build

| # | Item | State |
| --- | --- | --- |
| 1 | Reality spike filed; LOC or 15:30 limit fallback decided | Open (needs paper login) |
| 2 | >= 5 paper sessions with orders, reconciled exactly | Open (runner + spike first) |
| 3 | Every L10-L11 limit demonstrated on paper with a rejecting case | Unit-tested (`tests/test_bf_orders_risk.py`); paper log open |
| 4 | `/kill`, `/pause` drilled from the owner's phone; re-arm needs 2FA | Code + tests done; phone drill open |
| 5 | Unapproved orders not sent; approval expiry | Code + tests done; paper log open |
| 6 | Paper/live guard both ways; live id pinned; API user without funding rights | Paper side tested; **live side is intentionally absent** in this build |
| 7 | IBKR precautions set (A$1,000 / A$12,000) and photographed | Owner |
| 8 | A$10,000 deposited and settled | Owner |
| 9 | Backups, restore, no inbound port (scan) | Open (compose has no published ports) |
| 10 | Dead-man heartbeat 5 days | Open |
| 11 | Amendments registered; code hashes pinned | Record keeper |
| 12 | A7(c) + class filter on band C; start list reviewed by the owner | Engine done; LIC list frozen and pinned (BF-D14); owner review open |
| 13 | Risk statement signed; 5% of investable assets | Owner |
| 14 | Parcels for paper fills; short-term gains understood | Journal has fills; parcel/tax view open |
| 15 | Owner reachable by 15:20 through April 2027 | Owner |

## What the owner must provide (on the server, never in chat)

IBKR Pro cash account with ASX permission and the paper account enabled (paper
username/password typed into the server's Docker secret files; paper `DU` id into
config); the always-on Sydney server with Tailscale; a Telegram bot token and the
owner's chat id; the TOTP seed added to the owner's authenticator; later, the
A$10,000 deposit and the IBKR precautions. See `docs/SETUP_SYDNEY.md`.
