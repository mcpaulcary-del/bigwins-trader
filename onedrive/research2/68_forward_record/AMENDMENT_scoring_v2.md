# Amendment: paper scoring v2 (A$0 comparators, after-tax "kept" and "sold" lines, cost re-scoring against like costs)

Status: **ADOPTED 19 Nov 2026** (owner standing instruction "just do it, don't keep asking"; review 80 §0.3 item 2 and §1.2). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before any code is edited**. PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence.
**Scoring only.** No rule, book, order, fill, decision or random control of H82, the momentum books or the shadow lines' own books changes. The H82 state file (`out/paper_state/state.json`) is not written by anything in this amendment.

## 1. Defects (review 80 §1.2)
1. The J3 comparator books (A200 and the 40/60 plan, built in `paper_lib.run_cmp_day`) are charged brokerage max(A$6.60, 0.088%) **per fund on every purchase**, including the initial purchase and each A$500 monthly contribution (A$13.20 a month = 2.6% of each contribution for 40/60). The owner's real platform charges **A$0** on ASX ETFs (report 44 line 52). The comparator was therefore the owner's plan at a broker the owner does not use, which flatters every Big Wins book (by roughly 1–2 points a year for the lifecycle book in its first years).
2. `COST_ALT.md` (19 Nov) re-scored the H82 books at A$3 and A$0 brokerage but compared them with the A$6.60 comparator: the mirror-image mistake.
3. The scorecard was before tax only, and did not show the index fund's advantage of never being sold.

## 2. A$0 comparator books (primary benchmark from 19 Nov 2026)
- For each J3 comparator `CMP_<A200|4060>_<lifecycle_5k|25k|100k>` a twin **`<id>_b0`** is kept: same weights, same capital, same A$500 month-end contributions for the lifecycle size (bought at the next session's close), same EODHD-proxy prices and distributions, same 0.03% half-spread on purchases, **brokerage A$0**. Distributions are reinvested on the ex-date as in J3; each reinvestment is recorded as a tax parcel.
- They live in their own state file `out/paper_state/score_state.json`, written by `paper_score.py`. They were **re-computed from the account start** (decision 16 Nov 2026, first fills at the close of 17 Nov 2026) from the stored daily bulk files, and are brought forward by the daily job each day after the H82 day is saved.
- **The `_b0` books are the primary benchmark** for every H82 and momentum book (columns "A200 (A$0)", "vs A200", "40/60 (A$0)", "vs 40/60" in `SCORECARD.md`; `a200_b0_return`, `vs_a200_b0`, `plan4060_b0_return`, `vs_4060_b0` in the CSVs). The J3 books as frozen (A$6.60) are kept unchanged and shown in a second table for continuity (columns `a200_return`, `vs_a200`, `plan4060_return`, `vs_4060` keep their old meaning).
- `scorecard_history.csv`: for every day already booked (16–18 Nov 2026) the `_b0` columns and the `_b0` comparator rows are filled in from the re-computed books (the H82 NAV of those days is unchanged). The after-tax columns of §4 start on the first day scored with this code (they need holdings on the day, which earlier days did not store).
- **Shadow lines:** the own-clock comparators of SHADOW M3 / E3 (`SHADOW_CMP_*`) and of SHADOW ACC are built at A$0 from their first fill (1 Dec 2026). No shadow decision has been made yet, so nothing is re-stated.

## 3. Cost re-scoring (`paper_costalt.py`, information only)
`COST_ALT.md` now compares like with like: the H82 book at brokerage max(A$6.60, 0.088%) (actual), A$3 flat and A$0 — same trades, fills and half-spread — **each against the A$0 comparators** (A200 and 40/60). `cost_alt_history.csv` is regenerated in full on every run from the stored NAVs (one row per book per recorded day since 16 Nov 2026), so it is consistent with the corrected comparators; the earlier file is kept as `cost_alt_history_v1_frozen.csv`.

## 4. After-tax lines ("kept" and "sold")
For each H82 and momentum book, each `_b0` comparator, and the SHADOW ACC books, at each scored day (32% marginal rate, F3; regime A: 50% discount for parcels held 367 days or more; capital losses offset short-term gains first; cumulative from the start, not split by financial year — an approximation):
- **Kept** = NAV − tax on dividends/distributions received − tax on gains already realised. This is the value if nothing more is sold — how the owner actually holds the index fund.
- **Sold** = NAV − estimated sale costs − tax on dividends − tax on realised gains and on the gains of every holding if sold at the day's close. Sale costs: engine books v1.3 E1/E2 (brokerage and half-spread at the stored traded-value rank); comparators 0.03% half-spread, A$0 brokerage.
- After-tax returns use the book's unit index (contributions priced at the before-tax unit price): an approximation, labelled as such.
- Shown: book kept vs A200 (A$0) kept, and book sold vs A200 (A$0) sold (CSV: `ret_after_tax_kept`, `ret_after_tax_sold`, `a200_b0_ret_after_tax_kept`, `a200_b0_ret_after_tax_sold`, `vs_a200_b0_after_tax_kept`, `vs_a200_b0_after_tax_sold`, plus A$ values). The honest question for the owner is "engine sold" against "fund kept"; both are in the CSV.
- **Not yet included (pending):** franking credits on either side (review 80 §1.5); regime B (post-1 July 2027 rules); per-financial-year loss rules; after-tax lines for the SHADOW M3 / E3 books.

## 5. Flags added to the scorecard
- **31 Dec 2026 churn:** a note that rule C5 will sell, six weeks after the 17 Nov start, every holding not on the December list — an extra round trip (about 0.3–0.7% of the book) and short-term gains. That cost belongs to the start date, not to the engine's normal running (review 80 §1.5). Shown until 31 Jan 2027.
- The lifecycle A$5,000 book is labelled **"illustration only"** (review 80 §1.4; `AMENDMENT_adopt_rule_v2.md`).

## 6. What is not changed
J3 comparator books as stored, all engine and control books, every decision and order, the random-control percentile, the ledger format. Trial count: scoring, not a trial; **N stays 1,710.** The verdict stands: not shown to beat the index.
