# Amendment: SHADOW line M3 v1.1 (code brought into line with what report 76 tested)

Status: **ADOPTED 17 Nov 2026** (owner instruction, 17 Nov 2026), after that day's 09:27 UTC run. Hashed (SHA-256) and appended to `LEDGER.jsonl` **before `paper_shadow.py` is edited** and before any shadow decision is computed (the first M3 decision is the month-end of Mon 30 Nov 2026). PAPER ONLY. No real money, no broker orders. The AI never places trades.
Amends: `AMENDMENT_shadow_M3_E3.md` (SHA-256 5734270803…eabf38eca, ledger seq 9). Source: report 77 §2 ("Correction needed for the M3 paper shadow line").

## 1. Why
Report 77's blind replication read `paper_shadow.py` against the code that produced report 76's results (`improve5/code/sim5.py` with `look5.py`'s `M3` settings). The shadow code was built from report 76's rule text, and in four places it does not do what was tested. This amendment makes the M3 shadow line follow the tested behaviour. It does not change the tested design, and it does not change M3's status: **SHADOW, not adopted; tracked for information.**

## 2. Changes to the M3 shadow line
| Rule | From (paper_shadow.py v1.0) | To (v1.1, as tested) |
|---|---|---|
| **R2 fund first** | fund order = min(50% of account − fund value, free cash + the day's estimated sale proceeds) | fund order = min(50% of account − fund value, free cash **before that day's share sales**), if A$1,000 or more. Free cash = cash − tax owed (R9). Takeover and delisting payouts (R10) are already in cash and count. Proceeds of that day's sales go to shares and reach the fund at a later month-end |
| **R8 top-ups** | M3 topped up whether or not the book was full | top-ups only when the book is full after the day's purchases (names held ≥ n), as E3 T8 already does |
| **R3 fund-only phase** | fund orders of A$100 or more | fund orders of **A$1,000 or more**; the very first fund purchase of a book may be any size |
| **R7(a) hold zone** | `bad = no rank, or rank > 50, or traded-value rank > 150` | the "> 150" clause is deleted. It could never bind: only the 100 universe companies have a rank, so a holding outside the top 100 already has no rank. No change in behaviour |
| **R7(c) trim, parcel age** | parcels held 366 days or more sold first | **367 days or more**, as tested and as E3 T6 |

Kept as is (paper version, deliberately different from the back-test): **cash dividends and fund distributions** are paid to the book as cash on the ex-date (the back-test reinvested them at no cost; report 77 put that shortcut at about 0.3 point a year in M3's favour). Everything else in M3 (R7 gain deferral, R7(b) May rule, R8 purchase tests, R10 payout after 20 trading days, R9 tax reserve, 367-day discount) already matches the tested code and is unchanged.

## 3. Rule-text corrections (M3 v1.1; no change to the tested design)
- **R2** add: "The fund order is sized before the day's share sales, from cash already in the account."
- **R3** read: "… free cash goes to the fund in orders of A$1,000 or more (the very first purchase may be any size)."
- **R6** first sentence becomes: "Satellite = account value − fund value after the day's fund order (and after the sell-down to 50% on the day the small-account rule ends)."
- **R7(a)** replace "or that has no rank or has left the 150 most traded" with "or that has no rank (it is no longer among the 100 universe companies, or a score input is missing)". In `AMENDMENT_shadow_M3_E3.md` §5, the words "the 'left the 150 most traded' test (R7a)" no longer apply.
- **R7(c)** "held 12 months or more" means 367 days or more.
- **R8** add before the top-up sentence: "If the book is full (n names held) …".

## 4. What is not changed
E3 (report 73, T1–T11) and its books; H82 rules, books, orders, decisions, comparators and random controls; the shadow books, sizes, clock (first decision 30 Nov 2026, fills at the close of 1 Dec 2026), index fund, costs, data cut, traded value (v1.4), rankings and scorecard. No shadow decision has been made before this amendment, so no shadow book is re-stated. The code change is recorded in its own ledger entry with the SHA-256 of the new `paper_shadow.py`. The verdict stands for all lines: not shown to beat the index.
