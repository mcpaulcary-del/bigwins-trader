# Amendment: adopt / stop rule v2 for the forward record (replaces the deflated-Sharpe test)

Status: **ADOPTED 19 Nov 2026** (owner standing instruction "just do it, don't keep asking"; review 80 §0.3 items 4–5 and §2.2). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before any code is edited and before the first forward decision (30 Nov 2026)**. No forward return exists yet, so this change cannot have been chosen with knowledge of the results. PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence.
Replaces: `AMENDMENT_forward_multimarket.md` §8 "Adopt bar" (the stop bar and record-level stops are kept, §4 below); the words "that needs t ≥ 3.0 and DSR ≥ 0.95" in report 68 §2.7 for H82; and any reading of the SHADOW lines (M3, E3, ACC) as candidates. Report 68's promotion test for H82 (report 53) is kept as a reported statistic; it can no longer by itself lead to real money.

## 1. Why
The deflated Sharpe ratio at N ≈ 1,650–1,710 back-test trials answers "how good must the best of N tried strategies look?". A forward line was frozen and hashed before its data existed; nothing is selected after the fact. The only multiplicity is the number of forward lines that could trigger adoption — about a dozen. A Bonferroni correction for twelve one-sided tests at 5% needs t ≈ 2.6; t ≥ 3.0 covers it. The DSR condition needed t ≈ 5: about 30 years for a +2 point edge and a century for +1, i.e. a rule that can never say yes (review 80 §2.2). Scepticism from eight failed back-test rounds belongs in the size of a first real-money slice, not in an unreachable significance bar.

## 2. Adopt bar (all required)
For one design, at the **A$100,000 size only** (A$25,000 books are reported and never required: they are far noisier and would decide the outcome alone), formal only at a December month-end review after at least 36 months (first possible: 31 Dec 2029):
1. **pooled monthly lead t ≥ 3.0** against the local index fund (multi-market designs: equal-weight pool across markets; ASX-only lines: the line's own monthly lead against the A$0 A200 comparator);
2. **after-tax lead ≥ +1.0 point a year** on the record's after-tax basis; where a "kept" line exists (`AMENDMENT_scoring_v2.md` §4) the engine sold-basis value must also be not below the fund's kept-basis value;
3. **≥ 90th percentile** of the random-portfolio controls (pooled for multi-market designs);
4. multi-market designs: **more than half the markets ahead** of their fund after tax.
**No deflated Sharpe ratio and no back-test trial count** enters the bar. The DSR is still printed, labelled "information only".

**Controls are not adoptable.** CW (self-built cap-weighted book) has no picking in it: if it "passes", the finding is that it tracks its fund. It is reported as a **control** beside EI10I and M3 and can never meet the adopt bar. The same holds for the momentum and random books of the ASX record.

**Staged step (smaller, capped).** At a December review from **60 months** on (first possible 31 Dec 2031), a design at A$100,000 with pooled t ≥ 2.0 and after-tax lead ≥ +1.0 point a year (and conditions 3–4 above) allows a written proposal for **one capped trial slice of exactly A$50,000** with at least 25 names. The full bar must then be met before any larger amount.

**Meeting either bar allows a written real-money proposal only.** The owner decides; nothing is switched on by the record. Any proposal must state the edge in dollars against the data cost (about A$370 a year; review 80 §3.5).

## 3. Size limits (apply to any proposal)
- **No real money in a 4-share or 10-share book**, and **no real money below a A$50,000 slice** (with 25–30 names or more). Below about A$40,000 even a true +1 point edge does not pay for the data.
- The A$5,000 lifecycle book (H82 and SHADOW M3/E3/ACC lifecycle-size books) is **illustration only**: it measures cash drag and luck, not the engine (review 80 §1.4). It can never trigger adoption.
- Lines the bar can apply to: H82 A$100k; multi-market M3 and EI10I at A$100k; SHADOW M3 and E3 A$100k (ASX). The SHADOW lines become candidates only through this bar; they remain "not adopted; tracked for information" until then.

## 4. Stop rule (unchanged, with its error rates stated)
Per design and size, at a December review: from 13 months on, pooled t ≤ −2.0; or, from 60 months on, an after-tax lead of −1.0 point a year or worse. A stopped line is closed and reported; it is not re-tuned. Stated plainly: the 60-month after-tax condition will close a design with **no** edge 12–30% of the time and a **+1 point** design up to about one time in six (standard error at five years 0.85–2.1 points; review 80 §2.2). Acceptable for a retail record. Record-level stops of `AMENDMENT_forward_multimarket.md` §8 are unchanged.

## 5. Code
`paper_multi.py` computes the reading every month: `passes()` and `verdict()` are changed to this bar (A$100k only; no DSR; CW = control; staged step at 60 months), the scorecard text is updated, and N_TRIALS (printed with the information-only DSR) is set to the current count. The ASX scorecard (`paper_daily.py`) makes no formal reading and needs no change for this amendment beyond the "illustration only" label.

## 6. Trial count
A change of method, not a trial. **N stays 1,710** (1,711 after `AMENDMENT_shadow_ACC_keep_winners.md`). The verdict stands: not shown to beat the index.
