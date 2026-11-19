# NEXT — B-fast for the EMG2-18 slice (FD v3.0 §7.9, §21.1; AMENDMENT_live_EMG2_18), state on 19 Nov 2026 (after piece 2)

Branches: `bigwins-fast` (tested baseline) and `bigwins-fast-wip` (this work: pieces 1
and 2 of 3 done, green; piece 3 = merge). **Paper only.** No code here can place a real order:
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

## Piece 3 — merge (next)

1. Merge `bigwins-fast-wip` into `bigwins-fast` (fast-forward or a merge commit; never
   force-push), re-run the full gate on `bigwins-fast` (ruff, ruff format --check, mypy
   --strict, pytest, `req_coverage --milestone BF`, both validate-config steps; and the
   record tests with `bfenv.sh` sourced, about 10 min), push, then delete
   `bigwins-fast-wip` locally and on origin. Update this file's header.
2. Existing journals (none in production) need
   `ALTER TABLE bf_safety ADD COLUMN scope VARCHAR(40) NOT NULL DEFAULT ''` (BF-D16).

## Owner / record keeper points still open

1. **Amendment for the staged L11 rule** (record keeper), with the interpretations of
   BF-D15: HALTED_LINE replaced by stage 3; BW-RSK-29 / 12% day fall / 50% drawdown
   cleared by an automatic resume inside an episode; "within one decision" = the first
   month-end decision after the stage-3 breach, sale starting at that decision; the
   wind-down sells still need per-order approval (L8). Owner: confirm or correct.
2. **100 random twins (seeds 8550000 + i) are not built.** Test (b) cannot pass until
   they run, so stage 2 does **not** resume automatically yet (fails safe, paged).
   Build before go-live (go-live blocker).
3. L12 stop input (`l12_stop`) is a hook only; none applies before the first December
   review 13 months after registration.
4. HGO missing from the record's EODHD feed on 16-18 Nov 2026 (consolidation in Aug
   2026; `HGODB` listed): record keeper to check the identity mapping / suspension.
5. Raise the IBKR precaution "max order value" above the largest expected sell before
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
4. **EMG2_18_SIM twin**: done (daily, own safety latch, L13 in the report). **100 random
   twins** (seeds 8550000 + i, AMENDMENT_shadow_EMG2 §12 method) and the A200
   comparator: still to build; they feed L11 test (b) via `BfApp.twin_rank`.
5. **Canary flow** (L6): done and replayed on record data (carry, stop, recon wait,
   restart); the paper-gateway run is part of dry runs 1-5.
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
| 3 | Every L10-L11 limit demonstrated on paper with a rejecting case | Unit-tested; L11 staged rule drilled on record data (BF-D15/17); paper log open |
| 4 | `/kill`, `/pause`, `/stop`, `/continue` drilled from the owner's phone; re-arm needs 2FA | Code + tests done; phone drill open |
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
| + | 100 random twins running (L11 test (b), staged-rule amendment registered) | **Open: blocks automatic resume** (BF-D15) |

## What the owner must provide (on the server, never in chat)

IBKR Pro cash account with ASX permission and the paper account enabled (paper
username/password typed into the server's Docker secret files; paper `DU` id into
config); the always-on Sydney server with Tailscale; a Telegram bot token and the
owner's chat id; the TOTP seed added to the owner's authenticator; later, the
A$10,000 deposit and the IBKR precautions. See `docs/SETUP_SYDNEY.md`. Owner decisions
still wanted: confirm the BF-D15 interpretations of the staged loss rule (open point 1).
