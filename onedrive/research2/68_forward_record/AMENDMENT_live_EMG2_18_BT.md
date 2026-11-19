# Amendment: LIVE book EMG2-18 follows the band-trend switch into the ASX 200 fund (rule L15)

Status: **REGISTERED 19 Nov 2026 (UTC)**, by the record keeper, on the owner's decision (`OWNER_DECISIONS_2026-11-19.md`, section "Live start with the band-trend protection (after report 96)"). Amends `AMENDMENT_live_EMG2_20.md` (ledger seq 37) as amended by `AMENDMENT_live_EMG2_18.md` (seq 39), `AMENDMENT_live_EMG2_18_loss_rule_v2.md` and `AMENDMENT_class_rule_fix.md` (seq 62). Hashed (SHA-256) and appended to `LEDGER.jsonl` before any code for the switch exists and before the first decision it governs (the 30 Nov 2026 paper-month decision of the trading system; the first live decision mid-December 2026). The rule text is the paper line's, registered just before this file as `AMENDMENT_shadow_EMG2_18_BT.md` (rules BT1-BT4, section R for the band index as computed). Implementation: the trading system (`/home/user/asx-trader`, branch `bigwins-fast`, `docs/DECISIONS.md` BF-D28). The go-live checklist remains the gate. Paper only until the owner's separate live enablement; **the AI never places trades.**

## 1. Owner override, recorded with its caveats
Report 96's pre-set bar was **not met** and report 96 recommended no live change. The owner chose to run the real A$10,000 EMG2-18 book with the switch anyway. The owner was told, and this record states:
1. The rule did not pass report 96's bar: its whole lead over the registered rules comes from the 2026 fall; up to December 2025 it was about A$4,000 (12%) behind the registered rules on both data sets.
2. It was designed on only four overseas (Asian) markets, three of them losing ones for EMG2-18; the design chose the cash version, which failed on the ASX; the fund version is that rule's sibling, one of six rules judged on the ASX.
3. It is currently **OFF** (on report 96's replay it has held the fund since 1 Jun 2026), so the live book will likely start in the ASX 200 fund, not in EMG2 shares.
4. The live book is never evidence for or against EMG2 or the switch; the paper line `EMG2_18_SIM_BT` with its 100 twins stays the record's reading of it.

## 2. Rule L15 (band-trend switch), added; everything not listed here is unchanged
- **L15.1 (band index, BT1).** At each month-end decision (and at the L6 start decision) compute the equal-weight total-return index of band C: the eligible names of traded-value ranks 301-600 under the EMG2 rules in force at the decision (class rule v2: LICs/funds left out of the ranks), re-formed at each month-end, buy-and-hold inside the month; levels at the last 10 month-ends, the decision included, from the decision's own data (same store, same universe, class and A7 rules as the decision engine, the store cut at each month-end).
- **L15.2 (state, BT2).** ON if the index is at or above the mean of its last 10 month-end levels (this month-end included); otherwise OFF. With fewer than 10 levels, ON. Shown as **"state: EMG2" (ON) / "state: FUND" (OFF)**.
- **L15.3 (OFF, BT3).** Every EMG2 holding is sold (rule L4's orders, normal approval L8); no share is bought; the cash after the sales, less the A$50 reserve and within the A$10,000 capital cap (L1), is put in the ASX 200 fund **A200** (Betashares Australia 200 ETF, the record's benchmark fund) in one order (A$500 minimum; IBKR costs). At a later OFF decision the fund is topped up only if the cash less reserve is at least 10% of the account and at least A$500. A200 is bought for this purpose only; the class filter on band C (which leaves funds out) is not changed.
- **L15.4 (ON, BT4).** The fund is sold and the registered EMG2-18 rules (L2-L5) run with the proceeds, as for any sale.
- **L15.5 (books).** The simulated twin `EMG2_18_SIM` and the 100 random twins `EMG2_18_RND_s001...s100` follow the same switch at the same decisions (one state for all), so L13's comparison and L11's test (b) stay like for like.

## 3. Unchanged
The capital cap (L1, A$10,000), slots and parcels (L3), the A$500 minimum and A$50 reserve (L5), the canary (L6, which is the single fund order when the start state is FUND), the clock and carry (L7), owner approval of every broker-book order (L8), costs (L9), the hard limits (L10: A$800 per share buy, orders and buys per day, participation, price band), the staged loss rule (L11 v2), the v3 stop rules (L12), the twins (L13), reporting (L14, plus the state line), reconciliation and the gate. Mechanics the trading system applies inside L10 and records in BF-D28 for the owner to confirm or overrule: (a) the single fund order of L15.3 is exempt from the A$800 per-buy limit (paged like a sell above A$800; IBKR's precautionary order-value setting must be raised above A$10,000, already required for the largest sell, BF-D3); (b) a session whose orders come from a switch uses L10's start-day limits (24 orders, A$10,500 of buys), as the switch replaces the whole book like the start.

## 4. Reading
A safety rule chosen by the owner, not evidence. Reviewed with the paper line at the December 2027 review and after any fall of 20% or more of the registered paper book.

## 5. Trial count
No back-test run for this amendment (report 96's are counted, N 2,883). Not a trial.
