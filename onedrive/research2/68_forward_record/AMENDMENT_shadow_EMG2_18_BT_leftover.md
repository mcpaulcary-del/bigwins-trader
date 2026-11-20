# Amendment: paper line `EMG2_18_SIM_BT` — a share left unsold in FUND state is offered again every session, and its cash goes into the fund (aligned with trading-system BF-D34)

Status: **REGISTERED 20 Nov 2026 — PAPER ONLY, information only**, by the record keeper, hashed (SHA-256) and appended to `LEDGER.jsonl` **before the code change** and before the first decision it governs (Mon 30 Nov 2026, the line's first decision). No real money, no broker orders. The AI never places trades.
Amends `AMENDMENT_shadow_EMG2_18_BT.md` (ledger seq 70, SHA-256 d82cb680c22af7a737b4577a1c262043048238323dcff5e7445f1590f7af8e21), section R, bullet "BT3 (OFF)", its last sentence only. Rules BT1, BT2, BT4, the books, the twins, the costs and the reading are unchanged. Does not change `AMENDMENT_live_EMG2_18_BT.md` or the trading system.

## 1. Why
The owner's standing decision (`OWNER_DECISIONS_2026-11-19.md`, section "Share-list fixes", item 2): paper twins and the live book use identical rules. The record keeper found that section R of the paper line differs from the trading system's handling of a share that cannot be sold on a switch day (`/home/user/asx-trader` `docs/DECISIONS.md` BF-D34, owner decision "Protection re-confirmed on corrected figures (report 98)": "Build fix BF-D34 handles unsellable shares on a switch day"):

| In state FUND (latest decision OFF) | Paper line as registered (seq 70, s R) | Trading system (BF-D34) |
|---|---|---|
| A share sale not filled (no close) | decided again at the next month-end | offered again on every session the share has a close |
| Cash from such a sale | into the fund only at a later OFF month-end, and only if cash ≥ 10% of the account and ≥ A$500 | into the fund at the next session, if cash above the reserve ≥ A$500 (no 10% test) |

BF-D34 asks the record keeper to confirm it as an interpretation of BT3 ("put the account in the fund"). It is adopted here for the paper line, so the paper line, its random twins and the live book follow one rule.

## 2. Rule (replaces the last sentence of section R, "BT3 (OFF)": "A share sale not filled (no close) is decided again at the next month-end, as for every paper twin.")
**BT3a (leftover share, every session).** While the line's state is OFF, on every session that is not a month-end decision session of the line (a decision or a data block), after that session's fills: each share holding (not the fund) that has a close that session and no sell order open gets a sell order for the close of the next session (L9 costs). A share with no close that session (halted, no trade) gets no order that session and is offered again at the next session with a close.

**BT3b (fund sweep).** On the same sessions, when a share (not the fund) was sold on or after the line's latest month-end decision session, no buy order is open and the fund has a close that session: the cash less the A$50 reserve, within the cap (A$10,000 less the value of the fund held, as BT3), is one fund buy at the close of the next session, **whatever the 10% top-up band**, if it is at least A$500. Below A$500 nothing is bought and the cash accumulates: the sweep is tested again every session until the cash reaches A$500 or the next month-end decision. The fund order spends at most the cash planned for it (sales filling at the same close are swept at the next session), whole units, fund costs as BT3 (IBKR max(A$6.60, 0.088%), half-spread 0.05% a side), cut to the cash at the fill and dropped if then under A$500.

Unchanged: the month-end decisions (BT3 including the 10% top-up for other cash such as dividends, BT4, the payout after 20 sessions without a close), no sweep in state ON, no stops and no other intra-month action. Effective from the 30 Nov 2026 decision (the line's first), for `EMG2_18_SIM_BT` and all 100 random twins alike.

## 3. Mechanics (record keeper)
`paper_emg2bt.py`: a sweep step after the session's fills in `step()`; sweep orders are written to `shadow/emg2bt_sweep_<d>.csv` (book `EMG2_18_SIM_BT`) and listed in the ledger block `emg2bt`. Fills, costs, state file and everything else as section R. The capital cap is measured as in BT3 of the paper line (the fund's value; shares in FUND state are not counted).

## 4. Trial count
No back-test, no trial; N 2,909.
