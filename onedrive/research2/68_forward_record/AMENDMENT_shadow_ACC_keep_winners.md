# Amendment: SHADOW line ACC — "buy on the signal, keep the winners" (accumulation)

Status: **ADOPTED 19 Nov 2026** as a record-keeping addition (owner standing instruction "just do it, don't keep asking"; review 80 §0.3 item 6 and §3.3). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before the code is written and before any ACC decision is computed**. First decision **Mon 30 Nov 2026**. PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence.
None of the existing rules (v1.3 + amendments; SHADOW M3 v1.1 and E3) is changed by this amendment.

## 1. Status and purpose
**SHADOW: not adopted; tracked for information.** Every design so far re-ranks and replaces (turnover 0.8–0.9 a year). The owner's stated aim is to own the big winners and not sell them. ACC tests that form directly at the owner's real size: each month's money buys the best-ranked share not yet held, and nothing is sold. Honest expectation (review 80 §3.3): index-like return, tracking error falling as names accumulate, cost and tax drag near the index fund's; most likely "level with the index". It is a forward-only line: the review's suggested design stage on ASX 2001–2015 has **not** been done (no licensed total-return data for that period is held); no back-test of ACC has been run or looked at.
The book is A$5,000 + A$500 a month, so under `AMENDMENT_adopt_rule_v2.md` §3 it is **illustration only** and can never by itself lead to real money. If it meets the §6 bar, a larger book would need its own card and clock.

## 2. Books
| Book | Start | Contributions | Brokerage |
|---|---|---|---|
| `SHADOW_ACC_5k_b0` (primary) | A$5,000 cash at the 30 Nov 2026 decision | A$500 cash at each month-end after the start (first 31 Dec 2026), credited before that day's decision | **A$0** (owner's platform, report 44 line 52; not yet confirmed with the broker) |
| `SHADOW_ACC_5k_e1` (cost stress) | same | same | v1.3 E1: max(A$6.60, 0.088% of value) |
Both: half-spread v1.3 E2 (0.10% for traded-value ranks 1–100, 0.25% for 101–300, 0.50% otherwise, never below half a tick), tier from the traded-value rank in the M3 table of the decision. Whole shares.

## 3. Rules
- **K1 Clock.** Decisions at each ASX month-end after the close, from Mon 30 Nov 2026; fills at the **close of the next ASX trading day** (first: Tue 1 Dec 2026). Nothing is decided on other days.
- **K2 Ranking = the SHADOW M3 table of that month-end** (report 76 R4–R5 as coded in `paper_shadow.rankings`, v1.4 traded value, `_old` symbols admitted per Amendment v1.5): universe = the 100 companies with the highest median traded value over 252 trading days (≥ 200 closes); score = mean of the in-universe percentiles of 12-1 month momentum, 6-month momentum and closeness to the 52-week high (10-day staleness limit); ties by traded-value rank. ACC reads the file `shadow/forward_M3_snapshot_<date>.csv` that the M3 line writes at the same month-end. *Why M3 and not the H82 score:* the review's case for "buy on the signal, then hold" rests on momentum information lasting about a year; M3 is the pure momentum composite and the forward design with the best fresh-market result (+1.3 / +1.6 points, report 76, with the review's caveat that it is partly in-sample in time). The H82 score includes low volatility, which favours listed investment companies and defensive shares (review 80 §1.5) — not a "winner" signal.
- **K3 What to buy.** Free cash F = cash at the decision (after K2's contribution and any dividends and payouts). k = floor(F ÷ A$500). If k ≥ 1, walk the M3 table in rank order and take the first k companies that are (a) not already held, (b) traded on the decision day, (c) closed at A$0.50 or more, and (d) have a median traded value of at least 100 × the order amount. Each order is F ÷ k. If fewer than k companies qualify, the rest stays as cash. The first decision therefore buys 10 companies of A$500 each; later months usually buy one new company with the A$500 contribution. No top-ups.
- **K4 Fills.** At the fill-day close: amount = min(order, cash); shares = floor((amount − brokerage) ÷ (close × (1 + half-spread))). An order with no close that day, or 0 shares, is dropped and its cash waits for the next month-end.
- **K5 Never sold.** No sale for rank, weight, trim or rebalancing, ever. The only exits: (a) **payout** — a holding with no close for 20 trading days is taken as cash at its last close at the next decision (v1.3 C1 / M3 R10); (b) a code change in the A7 list carries the holding to the new code (v1.3 A7; ASX decision file of the month). No tax-loss sales: with nothing else sold, the book has almost no gains to offset, and a loss sale only defers tax (report 75 item 5; review 80 §3.2). Rule A9 of Amendment v1.5 applies to a held code that is renamed.
- **K6 Income and corporate actions.** Company dividends are cash on the ex-date (v1.3 I1) for shares held before that day; splits multiply share counts (Q7). Cash earns 0%.
- **K7 Data block.** If the M3 table for a month-end does not exist (Q4 data block, or the M3 step failed that day), ACC makes no decision that month; the cash waits.

## 4. Comparators
`SHADOW_ACC_CMP_A200_5k` (A200) and `SHADOW_ACC_CMP_4060_5k` (40% A200 / 60% BGBL): A$5,000 bought at the first fill close, A$500 at each month-end bought at the next session's close, **A$0 brokerage**, 0.03% half-spread, distributions reinvested on the ex-date (EODHD proxy, as `AMENDMENT_scoring_v2.md` §2).

## 5. Scoring
Rows marked SHADOW ACC on `SCORECARD.md` / `scorecard_latest.csv` / `scorecard_history.csv`: NAV, contributions, time-weighted return, vs A200 and vs 40/60 (A$0), names held, cash; after tax on the **kept** and **sold** bases (`AMENDMENT_scoring_v2.md` §4); tracking error against A200 from monthly unit-index returns once 12 monthly returns exist. State file `out/paper_state/accum_state.json`; orders `shadow/acc_orders_<date>.csv` (hashes in the daily ledger entry).

## 6. Bar (review 80 §0.3 item 6), information only
Read at 36 months (31 Dec 2029) and each December after: `SHADOW_ACC_5k_b0` after tax on the kept basis **not behind the A200 (A$0) comparator by more than 0.5 point a year**, with tracking error reported. Meeting it means "level with the index at lower tax and cost than H82"; it does not mean an edge.

## 7. Trial count
A new design registered for forward data: counted as one trial, **N 1,710 → 1,711**. The A$6.60 book is a cost stress (programme convention: not a trial). The verdict stands for all lines: not shown to beat the index.
