# Amendment (information-only forward reading): analyst-estimate revisions from the point-in-time snapshots (line EST)

Status: **REGISTERED 19 Nov 2026**, by the record keeper, on report 94 (section 3.3 item 1, section 6 item 5), **before any reading exists**: the first snapshot is dated 19 Nov 2026 and the first signal month is February 2027. **Information only.** No money, no paper book, no order, no decision of any line uses it; nothing is traded on it and nothing is tuned. It does not touch the trading system (`/home/user/asx-trader`) or any registered line. The AI never places trades. Report 94 marks the line "for the owner to decide": the owner may withdraw it before the first reading by a ledger entry; the trial stays counted.

## 1. Why
The point-in-time estimate snapshots (`bigwins_forward/data/estimates_pit/`, job `est_snapshot.py`, one file a day from 19 Nov 2026) are the only new kind of information being collected. The vendor's history of estimates was unusable (report 79), so there is no back-test and never will be. Writing the reading down now, with no return data in existence, makes it a blind design with no leak.

## 2. Data, exactly as read
- **Snapshot of a day**: `estimates_pit/est_YYYY-MM-DD.json.gz` as written by `est_snapshot.py` (SHA-256 in `est_manifest.csv`, checked on read; a file whose hash does not match is treated as missing). Files are never edited or back-filled; a day the job did not run has no snapshot.
- **Snapshot for a date D**: the file dated D, else the latest earlier file within 5 ASX sessions of D (`paper_lib.sessions()`); else none.
- **Universe at month-end M**: every code in the snapshot for M (the 300-company paper universe the job reads), excluding codes whose `trend` is not a dict.
- **Current-year estimate of a code in a snapshot**: among the entries of `trend` with `period == "0y"`, the one with the latest `date` (financial-year end). Its `date` is the **FY label**; the estimate is `earningsEstimateAvg` (A$ per share, as given; in the 19 Nov file identical to `epsTrendCurrent` for all 296 codes), and the count is `earningsEstimateNumberOfAnalysts`. Missing, empty or non-numeric fields = not available. The vendor's own `epsTrend90daysAgo` and `Highlights` fields are **not** used.
- **Prices and returns**: the paper record's daily bulk files (`bigwins_forward/data/bulk`, read through `paper_lib.load_day`), raw closes, dividend rows and confirmed `CORPORATE_ACTIONS.csv` rows, exactly as the paper books see them.

## 3. Signal, measure, readings
- **Month-end M**: the last ASX session of each calendar month, from **26 Feb 2027** to the last reading. Start date S = the session 63 sessions before M.
- **Signal** of code c at M: (estimate at M − estimate at S) ÷ raw close of c on the date of the start snapshot (snapshot for S). **Left out** when: either snapshot is missing; the estimate is not available at S or M; the count is below 2 at S or at M; the FY label differs between S and M; the start close is missing or ≤ 0.
- **Next-month return** of c: total return from the raw close on M to the raw close on the next month-end, with dividends (and confirmed corporate-action values) paid in the month added as cash, not reinvested. A code with no close on the next month-end is valued at its last close plus cash received (as the paper record values a suspended or delisted holding); a code with no close on M is left out.
- **Measures, one pair a month**: (a) **IC** = Spearman rank correlation between signal and next-month return over the codes with both; (b) **Q5 spread** = equal-weight mean next-month return of the top fifth by signal (round down; ties broken by code, ascending) **minus** the equal-weight mean next-month return of the whole universe at M (all codes with a next-month return, including those without a signal). A month with fewer than 50 codes with a signal is recorded as missing, not filled.
- **Readings** (statistics fixed now): number of months; mean IC, its standard deviation and t = mean ÷ (sd ÷ √n); share of months with IC > 0; mean Q5 spread and its t. Wording fixed now: "signal present (information only)" if mean IC > 0 and t ≥ 2.0; "not detected" otherwise; no other test, sub-period, sector cut or variant is read as evidence.
  - **Reading 1: December 2028** (signal months Feb 2027 – Nov 2028, 22 months). Can detect only a strong effect (monthly IC about 0.05 or more; report 94 s4).
  - **Reading 2: December 2030** (46 months).
- Each reading is a ledger entry (kind `reading`) with the code hash and the monthly table.

## 4. Implemented now, and not (TODO)
Nothing is computed now and no code reads the snapshots for returns. **TODO, before 26 Feb 2027**: a read-only script `est_reading.py` implementing sections 2–3, hashed in the ledger before its first run; tested on synthetic snapshots only. If it cannot be written before the first month-end, the monthly numbers are computed later from the stored files under this definition, unchanged.

## 5. Trial count
**One trial at registration.** N 2,788 → 2,789. Readings are not further trials.
