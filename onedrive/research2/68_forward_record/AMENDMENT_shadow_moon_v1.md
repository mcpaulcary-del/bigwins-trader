# Amendment: aggressive paper side lines EMG2_MOON_TOP5, EMG2_MOON_NOLOT5, MOON_LEG2, and false-discovery control across all side lines

Status: **REGISTERED 23 Nov 2026 — PAPER ONLY, information only**, by the record keeper. Hashed (SHA-256) and appended to `LEDGER.jsonl` **before any code of these lines is written** and before the first decision they govern (Mon 30 Nov 2026). The owner approved the lines on 23 Nov 2026, on the big-winner research (`research_big/REPORT.md` section 5(a), "Amendment draft" blocks; trials entry ledger seq 93). No real money, no broker orders. The AI never places trades.

**Nothing here changes the main strategy.** EMG2-18 + band-trend shield + C6 (the live trader `/home/user/asx-trader` and the paper line `EMG2_18_SIM_BT_C6`) is frozen until 1 Jan 2027 (owner decision, ledger seq 88). No rule, parameter, code path, state or reading of that line or of any other registered line is changed. The one exception is section 5: it **adds** a family-wide condition to the readings of the side lines registered at seq 91; their own rules and bars are unchanged. Every line below is strictly additive: own code, own state file, own twins, own output files. **Every line here is information only and is never evidence for or against EMG2.**

Below, "draft" means the text of `research_big/REPORT.md` 5(a). Where this amendment departs from the draft, it says so and gives the reason.

## 0. Common to the three books
- **Capital and timing.** A$10,000 each, cash only, no contributions. First decision Mon 30 Nov 2026; fills at the close of Tue 1 Dec 2026.
- **Base: `EMG2_18_SIM`.** Every rule is as the EMG2_18_REF / EMG2_18_SIM paper engine (`paper_emg2s.py`), except where a line below says otherwise:
  - the month-end table (`paper_emg2.table`, class rule v2) and the bundle;
  - fills at the next session's close: sells first, then buys cut to the cash (A$50 reserve);
  - costs: IBKR max(A$6.60, 0.088%), half-spread 0.50% a side;
  - **L1 cap:** sizing on min(account, A$10,000). The research replay ran without the cap; the cap is kept because the draft says "everything as `EMG2_18_SIM`";
  - orders under A$500 are not sent;
  - payout after 20 sessions without a close; A7 code changes; splits and dividends as cash;
  - `BID_PEG` sold at once;
  - data blocks: no decision when the H82 market-wide verdict fails or band C holds fewer than 150 names (rule 14). A data block keeps the holdings.
- **No shield.** None of the three lines uses the band-trend switch.
- **Slots.** n = min(NMAX, floor(min(account, A$10,000) ÷ 550)) and parcel = min(account, A$10,000) ÷ n. NMAX is 5 (TOP5, NOLOT5) or 10 (LEG2).
- **Liquidity cut (all three, twins too).**
  - Each buy is min(parcel, 4.5% × m20), where m20 is the median of the last 20 sessions' traded value. A session without a trade counts as zero once the share has a first price; at least 10 such sessions are required, otherwise the name is skipped. Traded value is computed as the EMG2 table computes it.
  - A cut parcel under A$520 is skipped, and the next candidate on the list is tried, as in the research code (`research_big/code/rules.py`).
  - If the chosen buys need more than the cash available (cash + estimated sale proceeds − A$50, within the cap), they are all scaled down in proportion. A scaled order under A$500 is not sent.
- **Month-end counter.** As in C6, every month-end session from 30 Nov 2026 counts, data blocks included. A holding bought at counter value m has age (counter − m).

## 1. EMG2_MOON_TOP5 — books `EMG2_MOON_TOP5`, twins `MOON_TOP5_RND_s001..s100`
- **Rule.** As `EMG2_18_SIM`, with **NMAX = 5**. The lottery filter is kept (`paper_emg2s.lottery`). Buyable names in T are bought best score first, with the liquidity cut. A holding is sold when it is off T (registered L4), when it is `BID_PEG`, or on a payout.
- **Twins.** Drawn as registered in `AMENDMENT_twins_buyable_set.md` s2: persistent seeded random scores over band C, redrawn with p = 0.2; the list is drawn by stratum so that it has len(T) names, of which exactly m are buyable (m = buyable names in the real T). Twins use the same n, the same cut, and L4 on their own list.
  - *Departure from the draft*, which says "candidates are the top fifth by random score of the buyable set": that would give a twin about len(T) buyable names against m for the real book. It would also give the twin a different keep set under L4. The registered stratified draw is the record's like-for-like null.
- **Seeds: 8830000 + i (i = 1..100).**
  - *Departure from the draft* (8810000 + i): the 8810000 twins belong to `EMG2_18_SIM_BT_C6`, which has the shield and the C6 sell rule, so pairing with them would not be like-for-like.
  - TOP5 and NOLOT5 instead share the base 8830000. Twin i of each draws the same random scores, and the two lines differ only in the lottery filter. The difference twin i of NOLOT5 − twin i of TOP5 is therefore reported as the filter effect on a random 5-name book. It is a fact, not a bar.

## 2. EMG2_MOON_NOLOT5 — books `EMG2_MOON_NOLOT5`, twins `MOON_NOLOT5_RND_s001..s100`
- **Rule.** As `EMG2_MOON_TOP5`, **without the lottery filter**: the candidates are all of T (which is already eligible: A$0.10, A$100k, valid scores, not `BID_PEG`).
- **Twins.** As section 1, with an empty lottery class. Each twin's list is then the len(T) best random scores among the non-peg band-C names.
- **Seeds: 8830000 + i** (shared with TOP5 on purpose, as above).
- With WIDE (seq 91) and MOON_TOP5 this completes a two-by-two of lottery filter × concentration.

## 3. MOON_LEG2 (second leg after a doubling) — books `MOON_LEG2`, twins `MOON_LEG2_RND_s001..s100`
- **Pool at each month-end.** Taken from the same month-end table:
  - ranks 301–1000 by the 252-session median traded value (the table's `tv_rank`);
  - eligible: close (on the day or within the previous 5 sessions) ≥ A$0.10; 63-session median traded value ≥ A$100,000; traded in the last 5 sessions; valid s1, s2 and s3;
  - not lottery-lap: age ≥ 504 sessions and close ≥ A$0.20, the same test as WIDE's lottery class;
  - not `BID_PEG`.
- **Buy.** A pool name is a candidate if:
  - its 252-session total return is ≥ +100%, with at least 150 priced sessions in the window. This uses the table's total-return line (`paper_emg2bt.tr_log`, A3/A6): exp(L_i − L_{i−252}) − 1; and
  - the line is within 25% of its 252-session high: the table's s3 = exp(L_i − max L over the 252-session window) ≥ 0.75.

  Candidates are bought nearest the high first (s3 descending, ties by code), with NMAX = 10 and the liquidity cut.
- **Sell at a month-end decision** when any of these holds:
  - s3 < 0.70, or s3 not available. This is "more than 30% below the 252-session high", applied whether or not the name is still in the pool;
  - age ≥ 12 (the 12th month-end after the purchase decision);
  - the name is `BID_PEG`;
  - a payout.
- **Twins.**
  - Pool: the LEG2 pool above, in table rank order. Persistent seeded random scores, drawn in that order and redrawn with p = 0.2.
  - Candidates: the top floor(0.2 × pool size) by random score, best first. A twin holding is sold when it leaves that top fifth (or is `BID_PEG` or a payout).
  - There is no 12-month rule for the twins, as in the research code. Same n and liquidity cut.
- **Seeds: 8820000 + i** (not used elsewhere in the record).
- **Data.** Ranks 601–1000 are already in the forward store and the daily bulk file (whole-exchange EOD). On the 16 Nov 2026 table: 400 ranked names in 601–1000, of which 7 pass the A$100k eligibility; the bulk file of 23 Nov had closes for 651 of the 700 names ranked 301–1000. **No download is added; 0 extra credits a day.** Because only a handful of names beyond rank 600 pass the A$100k floor, LEG2 is in practice a band-C line plus a few.

## 4. Reading (all three; wording fixed now)
- **Reported monthly**, beside `EMG2_18_REF`.
- **Facts:** orders, brokerage and modelled spread; holdings; each holding's gain or loss; the count of holdings at +100% or better and at −50% or worse; worst fall.
- **Labelled mostly luck:** value; gap to `EMG2_18_REF` after costs; percentile among the line's own twins.
- **Never evidence for or against EMG2.**
- **No proposal before the December 2028 review.** A proposal then needs all of:
  1. ahead of at least 90 of its 100 twins;
  2. not behind `EMG2_18_REF` after costs over 24 months;
  3. worst fall not more than 10 points deeper than REF's;
  4. a blind rebuild that arrives at the same rule;
  5. an owner decision.

  The 12-month gap between such books has a standard deviation of about 25–30 points, so 24 months cannot prove anything on return alone.
- **`EMG2_18_REF` retirement.** If `EMG2_18_REF` is retired in January as the gap review suggests, these three lines need their comparison book. In that case a REF-equivalent book (the same engine at N = 18, without twins) must be kept, or registered again, before it is retired.

## 5. False-discovery control across the side-line family (adds to the readings of seq 91)
- **The family.** All side lines form one family of eight: SWEEP, WIDE, FIP, EST-C and DIL-C (seq 91), and MOON_TOP5, MOON_NOLOT5 and MOON_LEG2 (here).
- **One primary statistic per line, fixed now**, read at the December 2028 review on the closes of the last ASX session of November 2028. Each line gives a one-sided p-value:
  - **MOON lines:** p = (1 + number of own twins with a return ≥ the line's) ÷ 101.
  - **WIDE, FIP, SWEEP:** p = (1 + number of twin-pair differences ≥ D) ÷ 101, with D and the pairs as in seq 91 s0.
  - **EST-C:** the one-sided normal p of its t (top minus bottom third) over the measures that exist by then.
  - **DIL-C:** the one-sided normal p of its 6-month Newey–West t, with the sign reversed, since the expected effect is negative.
- **Benjamini–Hochberg at q = 10%** is applied to these eight p-values. With eight lines, about 0.8 would clear a raw 90th-percentile bar by luck.
  - A line that does not survive BH is "not shown", whatever its own bar says.
  - A line that survives must still meet its own bar (seq 91, or section 4 here).
- **FIP, EST-C and DIL-C** enter with their value at that date. Their own later readings (FIP at 36 months, EST-C at 24 measures, DIL-C at 36 months) are kept as registered, as information only.
- **No new aggressive side line before 2028** unless one is retired. Retiring the H6 / COMBO / REF overlap in January (gap review) is a separate owner decision; see section 4 for REF.

## 6. Mechanics (record keeper; written before the code)
- **New module** `bigwins_forward/code/paper_moon.py`:
  - own state files `moon_top5_state.json`, `moon_nolot5_state.json`, `moon_leg2_state.json`;
  - orders written to `shadow/moon_<line>_orders_<d>.csv`;
  - ledger blocks `moon_top5`, `moon_nolot5`, `moon_leg2`.
- **Built on the frozen functions, called and not changed:** `paper_emg2.table` / `get_bundle`, `paper_emg2s.lottery`, `lists_for`, `run_day` and the book helpers, `paper_emg2bt.tr_log`, and `paper_sidelines.lottery_wide`. Its own decide implements sections 0–3.
- **`paper_daily.py`:** imports the module; runs it after the seq 91 side lines and before the bundle is cleared, also in the catch-up call; adds rows to the "Side lines" section of `SCORECARD.md` and rows at the end of the scorecard CSVs, existing columns only. The old file is kept as `paper_daily_pre<seq>_frozen.py`.
- **Proof of no change:** the daily job is run on a scratch copy of the record with the old and the new code, from 24 Nov to 4 Dec 2026, with a forced 30 Nov decision. Every existing state file and every existing scorecard row (the seq 91 side lines included) must be byte-identical. The code ledger entry after this one records the hashes and the tests.

## 7. Trial count
Registering adds no trial: the replays are counted in research_big (71 trials, ledger seq 93). **N 3,046.**
