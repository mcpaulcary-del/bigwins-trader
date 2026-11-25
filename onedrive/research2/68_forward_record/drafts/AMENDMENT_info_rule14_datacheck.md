# DRAFT — NOT REGISTERED. Amendment (information-only forward reading): a data-completeness test DC as a proposed replacement for rule 14 (line R14-DC)

> **DRAFT, 25 Nov 2026.** Not hashed, not in `LEDGER.jsonl`, governs nothing. The record keeper registers it only after the owner approves, on or after 1 Jan 2027, and **before the first month-end it reads** (29 Jan 2027). Withdrawn unregistered if the owner declines.

Status (to be filled at registration): **REGISTERED <date>**, by the record keeper, on the owner's decision of <date> (decision sheet `jan2027/DECISION_SHEET.md`, question 2), on `research_grand` s6 item 1 and `research_bw` s5 ("Decision the owner still has to make on rule 14"). **Information only.** No money, no paper book, no order and no decision of any line uses it; nothing is traded on it and nothing is tuned on it. It changes no rule of the live book or of `EMG2_18_SIM_BT_C6`. It is a reading, not a paper line, so the line cap (`AMENDMENT_retirement_jan2027.md` s4) is not touched. The AI never places trades.

## 1. Why
- Rule 14 says "fewer than 150 names in band C (or the H82 market-wide verdict fails): no decision". A **count of 150 is not a data check.** Band C had under 150 names in 89 of 97 design month-ends (2010–2018) and blocked all trading in 42 of the last 95 month-ends, in real markets with complete data. It is the largest single term in the edge equation after tax (`research_grand` s3: D_r14 −2.2 points a year).
- The January amendment E5 (draft `AMENDMENT_live_EMG2_18_E5_jan2027.md`) keeps rule 14 as "thin band, stand aside from buying" and stops it blocking sales. Whether a thin band should block buying at all is open. Removing it outright gave about the same money with a much deeper 2020 fall (`research_bw` s2, M1: −47% / −53%).
- The honest replacement is a test of whether **the data are complete enough to decide**, not of how many companies happen to sit in ranks 301–600. Writing that test down now, read only forward, keeps it free of hindsight. Every ASX market year to Oct 2026 has been seen (`research_grand` s6), so no back-test of it is planned or allowed under this entry.

## 2. Definition (fixed now)
At each month-end decision of `EMG2_18_SIM_BT_C6` (the paper record's decision bundle and month-end table `paper_emg2.table`, exactly as that line reads them), compute:

1. **Q4 (market-wide verdict, unchanged).** The H82 Q4 test of the day (`paper_lib.build_decision`): passes when the AXJO index has a row on the decision day **and** at least 285 of the top-300 table have a raw close on that day.
2. **P (priced band).** Among the codes of traded-value ranks 301–600 by 252-day median traded value in the month-end table (class rule v2; LICs and funds left out of the ranks; **before** the eligibility filters of EMG2 rule 2), the share with a raw close on the decision day or within the previous 5 sessions (EMG2 rule 2's close test). **P passes when this share is at least 0.90.**
3. **E (enough eligible names to fill the book).** The number of eligible band-C names n_C (EMG2 rules 2–3 as in force, the same count rule 14 uses). **E passes when n_C ≥ 90**, because the target list T is the top fifth of band C and the book holds 18 slots: 90 × 0.2 = 18.

**DC passes when Q4, P and E all pass.** DC fails otherwise, with the failing parts named.

The thresholds are set now from the book's own arithmetic (E: 18 slots ÷ 0.2) and a convention (P: 90%), **not** from any data. They are not changed after the first reading; a different threshold is a new entry with a new name.

## 3. What is recorded, every month-end from 29 Jan 2027
A row in `shadow/r14dc_<d>.csv` and a block `r14dc` in that day's ledger entry:
- n_C, the band size before eligibility, the number and share priced (P), Q4's two numbers, and the verdicts **R14** (n_C ≥ 150 and Q4) and **DC**.
- **Agreement**: both pass; both fail; R14 fails and DC passes ("rule 14 stands aside, the data were complete"); R14 passes and DC fails ("rule 14 decides on incomplete data").
- **When they disagree only**: the order list the main line's rules would have produced at that decision under the other verdict (names, sides and parcel sizes from the same bundle and the line's own book). **No book is kept, no order is filled and no value or return is computed** for it.

## 4. Readings (fixed now)
- **Reading 1: the December 2028 review.** Counts only: months read; months in each agreement cell; for "R14 fails, DC passes" months, the number of buys and sales the main line skipped; for "R14 passes, DC fails" months, the failing parts. Wording fixed now: "rule 14 stood aside in k of n months in which the data were complete (DC)". No return, no performance and no t-statistic is read from this line; any figure of money is out of scope.
- What a reading can support: a **new, separate amendment** to change rule 14 in the live book and `EMG2_18_SIM_BT_C6`, with its own owner decision. This entry itself never changes a rule.

## 5. Implemented now, and not (TODO)
Nothing is computed now. **TODO before 29 Jan 2027**: a read-only function in `paper_emg2bt6.py` (or a separate `r14dc_reading.py` that reads the same bundle) implementing section 2–3, hashed in the ledger before its first run, tested on synthetic bundles only; it must leave every line's output byte-identical. If it is not ready by 29 Jan 2027, the monthly rows are computed later from the stored bundles under this definition, unchanged.

## 6. Trial count
One trial at registration, conservatively, as for the information line EST (`AMENDMENT_info_EST_revisions.md`): **N 3,332 → 3,333** (or the current N + 1). Readings are not further trials. No back-test is run.
