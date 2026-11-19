# Amendment: LIVE book EMG2-18 — staged loss rule (rule L11 v2)

Status: **REGISTERED 19 Nov 2026**, by the record keeper, on the owner's signed decision (`OWNER_DECISIONS_2026-11-19.md`, section "Loss rule REPLACED (after report 88 §4.2) — owner signs Fable's staged rule"). Amends rule L11 of `AMENDMENT_live_EMG2_20.md` (ledger seq 37) as amended by `AMENDMENT_live_EMG2_18.md` (seq 39). Supersedes L11's "≤ A$6,000: `HALTED_BUYS`; the owner decides in writing" and the interim owner rule "pause buys, keep holdings" of the same decisions file. Hashed (SHA-256) and appended to `LEDGER.jsonl` before the first live order. Registration of the rule text only: the implementation is the trading system's (`/home/user/asx-trader`, branch `bigwins-fast`, `docs/DECISIONS.md` BF-D15, `trader/loss_rule.py`); the go-live checklist remains the gate. The AI never places trades.

## 1. The rule (owner-signed text)
1. **A$7,000:** alert (page) + integrity check (live holdings = simulated twin; fills and costs as modelled).
2. **A$6,000:** buys pause until the next month-end decision at the latest, then **resume automatically** unless (a) the integrity check fails, (b) the live book's simulated twin is below the 10th percentile of its 100 random twins since the start, (c) an L12 stop rule is met, or (d) the owner says stop.
3. **A$5,000:** the same test, and the owner must confirm in writing to continue; if not within one decision, the book is sold over the next two decisions.

## 2. Which value is tested (settles report 90 section 4 item 4(a))
- **The steps are tested on the end-of-day account value of the live book (daily close NAV), every session — not on the month-end value.** Account value = cash + each holding × that session's closing mark; a held name with no mark that session is valued at its last recorded mark and flagged (BF-D17), so a data gap can neither trigger nor hide a stage. A step is reached when the value is **strictly below** the threshold (the owner's "falls below"). This is how the trading system implements it (BF-D15; `trader/loss_rule.stage_of`, fed by the daily report job's account value).
- The pause of step 2 starts on the session the end-of-day value is first below A$6,000; the test of step 2 (and step 3) is run at the **month-end decision** that follows, and again at each later decision while it fails.
- **Daily lows run deeper than month-end values (report 90 section 1.6), so the steps will be reached more often than the base rates of report 88 section 4.2 suggest.** Those base rates (random twins touching A$7,000 / A$6,000 / A$5,000 at a month-end in 2018–Oct 2026: 62% / 31% / 8%) are month-end figures. In the 2018–2026 replay of the registered rules the worst month-end fall was 48% and the worst daily fall 59%; the lowest daily value was **A$4,262 on 23 Mar 2020 against A$5,231 at the month-end** — that is, step 3 was reached on daily closes but not on month-end values. First-year base rates (report 90, month-end values, 76 starts): under A$8,000 within 12 months 17%, under A$7,000 8%, under A$6,000 3%; on daily closes these are higher. **The owner is told this here.**

## 3. Unchanged
L11's one-day fall of 12% (`HALTED_BUYS`) and `/kill` (stops everything in one step); BW-RSK-20 (50% drawdown); the stop rules of adopt rule v3 (L12); approval (L8); hard limits (L10); the capital cap; the simulated twin and its 100 random twins (L13, seeds 8550000 + i); the gate. A halt alone still never sells; only step 3 without the owner's confirmation sells, over two decisions.

## 4. Interpretations recorded from the implementation (BF-D15, read-only; for the owner to overrule if wanted)
1. The registered A$5,000 `HALTED_LINE` (which also stopped sells) is replaced by step 3: sells go on.
2. BW-RSK-29 (60% of capital = A$6,000) is the same threshold and is cleared with step 2.
3. Test (b) needs the 100 random twins of the simulated twin. Until they run, the rank is unknown and the test **fails safe** (buys stay paused, owner paged). This is a go-live blocker in the trading system.
4. L12 can stop the slice only at a December review from 13 months after EMG2's registration; none before then.
5. "Within one decision" = by the first month-end decision after the step-3 breach; the sale starts at that decision (half of each holding, then the rest at the next); wind-down sells still need per-order approval while L8 per-order approval applies.
6. The owner's `/resume <code>` (second factor) ends an episode at any time; the owner's `/stop` (or `/pause`, `/kill`) is answer (d).

## 5. Reading
The loss rule is a safety rule, not evidence. A fall to these levels is inside the normal range for these shares whether or not the signal works (reports 87, 88, 90). Report 88 section 4.2 item 4: if losing half of A$10,000 and continuing is not acceptable, the remedy is not a tighter limit but not to start, or to hold the fund.

## 6. Trial count
No back-test run for this amendment. Not a trial. N unchanged at 2,192.
