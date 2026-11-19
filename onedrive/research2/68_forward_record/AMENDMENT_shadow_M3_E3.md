# Amendment: two SHADOW lines, M3 (report 76) and E3 (report 73)

Status: **ADOPTED 17 Nov 2026** as a record-keeping addition (owner instruction, 17 Nov 2026). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before any shadow decision is computed**. PAPER ONLY. No real money, no broker orders. The AI never places trades.
Rules of the main line: v1.3 (`67_FINAL_RULES_v1.3.md`, SHA-256 b38abcd7…54b0) + `AMENDMENT_start_now.md` + `AMENDMENT_intraday_look.md` + `AMENDMENT_v1.4_traded_value.md`. None of them is changed by this amendment.

## 1. Status of the two lines
- **M3 v1.0 (ASX version)**, rules R1–R11 of report 76 §6, and **E3**, rules T1–T11 of report 73 §6, are **SHADOW lines: not adopted; tracked for information.** Neither is a paper rule of the Big Wins record and neither can replace H82 by this amendment. E3 stays "closed for promotion; no look before 36 months" (report 73 §6).
- The shadow lines never change the H82, momentum, random-control or comparator books. They keep their own state file (`bigwins_forward/out/paper_state/shadow_state.json`); the main state file is only read. If a shadow step fails, the H82 day is still booked and the failure is written to the log and the ledger entry; the shadow line resumes from its own last processed day on the next run.

## 2. Books
For each of M3 and E3, three books:
| Book | Start capital | Contributions |
|---|---|---|
| `SHADOW_<line>_25k` | A$25,000 | none |
| `SHADOW_<line>_100k` | A$100,000 | none |
| `SHADOW_<line>_lifecycle_5k` | A$5,000 | A$500 cash at each month-end after the start (first 31 Dec 2026), credited before that day's decision |

Small-account rule, as each report writes it:
- **M3 (R3):** while the account is below A$25,000 on a decision day and no shares are held, everything is in the index fund. On the first decision day at or above A$25,000 the fund is sold down to 50% and R4–R8 start. The A$25k book starts at exactly A$25,000 and so starts under R2–R8 (50% fund core) on day one; the A$100k book likewise.
- **E3 (T10):** a book that starts below A$25,000 holds the index fund only until NAV ≥ A$25,000 at a December month-end; then the fund is sold and T4 applies with n ≥ 10. The A$25k and A$100k books start under T4–T9 (no fund).
- While a book is fund-only, all free cash goes into the fund at each decision (as the J3 comparators do).

## 3. The index fund
The index fund (M3 R2/R3 core; E3 T10 small-account fund) is **A200** — booked from EODHD `A200.AU` closes plus distributions, **flagged as an EODHD proxy** as in J3. Fractional units, as for the J3 comparators. Distributions are paid to the book as cash on the ex-date (they go back into the fund through R2/R3/T10 at the next decision). Fund trades cost brokerage max(A$6.60, 0.088%) and a 0.03% half-spread (J3).

## 4. Clock, decisions and fills
- **Each line has its own clock.** First decision: **the month-end of Mon 30 Nov 2026**, after the close. Fills at the **close of the next ASX trading day (Tue 1 Dec 2026)**, per each design's own execution rule (M3 R1: next trading day's closing auction; E3 T9: next trading day's close). Later decisions: every month-end (last ASX trading day of the month); nothing is decided on any other day.
- An order that cannot fill at that close (no close that day; not enough cash for the minimum size) is not carried: it is recorded as dropped and the position is decided again at the next month-end (E3 T9; applied to M3 likewise).
- Order of fills on the fill day: sales and trims, fund sales, fund purchases, share purchases in decision order, top-ups. A purchase is A$ amount = min(decided amount, free cash at the fill); M3 and E3 stop the remaining purchases when that is below max(A$1,000, half the target) (R8 / T7); a top-up below A$1,000 is dropped. Whole shares for companies.
- **Costs per v1.3 E**: brokerage max(A$6.60, 0.088% of value) per trade; half-spread E2 (0.10% for traded-value ranks 1–100, 0.25% for 101–300, 0.50% otherwise, never below half a tick), tier read from the shadow line's own traded-value rank at the decision.
- Splits multiply share counts (Q7); company dividends are cash on the ex-date (I1). Takeover/delisting (M3 R10, v1.3 C1 for E3): a holding with no close for 20 trading days is taken as cash at its last close on the next decision day.
- If the Q4 data-block test stops the H82 decision at a month-end, the shadow lines make no decision that month either.

## 5. Data and traded value
- Same EODHD file and the same Q2 cut as the H82 decision of that month-end (the `bw13_prep.py` bundle: A4 ordinary-share filter, ETP exclusion, A7(b) duplicate codes, A8 code reuse). Nothing after the decision day is read.
- **Traded value follows Amendment v1.4 for both shadow lines from their first decision (30 Nov 2026):** traded value of a day = adjusted close P(d) × volume(d) (EODHD AU volume is split-adjusted). This replaces "close × volume, both unadjusted" in M3 R4 and is what E3 T1 already says. It governs the universes (M3 top 100; E3 top 300; ≥ 200 closes in 252 days; median of 252 days, no-row days = 0), the "left the 150 most traded" test (R7a), the liquidity tests (R8, T7: median ≥ 100 × target) and the spread tiers.
- Scores use the A3 adjusted close P of the same bundle (split- and consolidation-adjusted price series), which is the series the report-76 and report-73 snapshot code used; R5's "dividend-adjusted" is read as this series. M3: s1, s2, s3 with the 10-trading-day staleness limit, percentiles (average rank ÷ count) inside the top-100 universe, score = mean of the three (missing if any is missing), ties by traded-value rank. E3: OLS t-statistic of ln P (forward-filled) on day number over the 252 days, all 252 needed, ties by traded-value rank. Traded-value ties: lower ASX code first.
- M3 R9 (cash for tax): free cash = cash − tax owed on the financial year's realised gains (50% discount for parcels held 12 months or more) and dividends at 32%. E3 uses cash. NAV is after costs, before tax, as for H82.
- Snapshots: at each decision, `shadow/forward_M3_snapshot_<date>.csv` and `shadow/forward_E3_snapshot_<date>.csv` (every ranked company with rank, score parts, traded-value rank, median traded value, close, zone and test flags) and `shadow/orders_<date>.csv` are written in this folder and their SHA-256 go into that day's ledger entry.

## 6. Scoring
Both lines are scored on the same scorecard as H82 (`paper/SCORECARD.md`, `scorecard_latest.csv`, `scorecard_history.csv`), in rows marked **SHADOW**, against: A200 total return and the 40/60 plan (own-clock comparators `SHADOW_CMP_A200_<book>` and `SHADOW_CMP_4060_<book>`, started at the same decision with the same fill day, built exactly as J3), and the H82 random controls (200 seeds per size), whose returns are measured over the shadow line's own window (from the 30 Nov 2026 close). Returns are time-weighted (unit index), so contributions do not count as gains. These rows replace the "Improved challenger (report 73)" placeholder.

## 7. What is not changed
H82 rules, books, orders, decisions, comparators and controls; the daily job's order of work for them; the ledger format. The verdict stands for all lines: not shown to beat the index.
