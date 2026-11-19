# Amendment: adopt / stop rule v3 for high-swing lines

Status: **ADOPTED 19 Nov 2026** (owner decision D-3, `OWNER_DECISIONS_2026-11-19.md`). Adds to `AMENDMENT_adopt_rule_v2.md`, which is unchanged and stays in force for index-like lines. Hashed (SHA-256) and appended to `LEDGER.jsonl` by the record keeper on 19 Nov 2026, before any code for it is installed and before the first decision of any line it governs (Mon 30 Nov 2026). Text below is the research agent's (Fable) draft `deep85/AMENDMENT_adopt_rule_v3.md` (SHA-256 8231b3fc17062e96a9e93558a4e4893a3eaf218fbff7a380c0ba3e1d948bd750) unchanged except this status line and the title. The AI never places trades.
Adds to `AMENDMENT_adopt_rule_v2.md`; v2 is unchanged and stays in force for index-like lines (H82, SHADOW M3, E3, CXL, the multi-market lines). Source: report 85 section 6.3; FD v3.0 section 18.3.

## 1. Why
Adopt rule v2 needs a pooled monthly lead t ≥ 3.0 against the index fund. t = lead ÷ tracking error × √years. For a line with a tracking error of 20 points a year and a true lead of 5, t = 3 needs 144 years and t = 2 needs 64. V2 can therefore only ever pass a large edge in an index-like book, and reports 73–82 say no such thing exists. V3 asks questions that can be answered in years: does the line's signal still sort shares on forward data; does the book beat chance in its own pond; can it be traded at the modelled cost; is it not far behind the fund. It gives up statistical proof that the book beats the index, and caps the money at every step for that reason.

## 2. Lines it applies to
A line registered as **high-swing**: EMG2; the H100 June sleeve; any later line whose registration states an expected tracking error above 10 points a year. The class is fixed at registration. Each such line's registration names its **signal spread** (EMG2: BANDSPREAD band C TOP − ALL) and has 100 random twins. At most four high-swing lines may be eligible for money at one time.

## 3. Ladder (all conditions of a step required)
| Step | Evidence (all required) | Money |
|---|---|---|
| **P0 Paper** | Registered and hashed; twins and measurement line running | None |
| **P1 Pilot** | At least 12 months in `paper_auto` on the IBKR paper account; every decision executed and reconciled; realised cost per trade ≤ 1.5 × model over at least 100 fills; book ≥ 60th percentile of its twins; forward signal spread (EMG2: BANDSPREAD band C TOP−ALL) cumulative mean > 0; no halt outstanding; signed risk statement | One slice ≤ **A$10,000** and ≤ 5% of investable assets; 20 names |
| **P2 Scale** | At least 24 months from registration and 6 months of pilot; signal spread t ≥ 2.0; book ≥ 80th percentile of twins; after-tax (book sold, fund kept) not more than 5 points a year behind A200; pilot cost ≤ 1.5 × model | ≤ A$50,000; the full list |
| **P3 Full** | At least 48 months from registration; signal spread t ≥ 3.0; book ≥ 90th percentile of twins; after-tax lead over A200 (fund kept) > 0; owner signature | Owner's amount; halts of section 10 apply |
| **Stop** | At a December review from 13 months on: signal spread t ≤ −1.0; or book below the 20th percentile of twins; or, from 24 months on, after-tax more than 15 points a year behind A200 | Line closed and reported; not re-tuned; real money in it sold down over the next two decisions |

Definitions: "paper months" = months in which the line's A$100,000 book was mirrored on the IBKR paper account with every decision executed and reconciled. "Cost ratio" = realised cost per trade (commission plus fill price against the mid at order time, signed) ÷ the line's modelled cost. "Twins percentile" = share of the 100 twins of the A$100,000 book with a lower time-weighted return since the start. "After tax" = book on the sold basis, A200 fund (A$0 brokerage) on the kept basis (`AMENDMENT_scoring_v2.md` §4), in points a year since the start. t of the signal spread: monthly observations since registration, Newey-West lag 1.

## 4. Readings
P1 may be read at any month-end. P2 and P3 only at June and December month-ends. Stated plainly: reading a t ≥ 2 test twice a year for several years roughly doubles or triples its nominal 2% false-pass rate; accepted because the money at P2 is capped at A$50,000. The stop conditions are read each December.

## 5. What meeting a step allows
A written proposal only. The owner decides and signs; nothing is switched on by the record. A proposal states the edge in dollars against the running costs.

## 6. Owner override recorded with this amendment
On 19 Nov 2026 the owner waived the evidence conditions of step P1 for **one slice of A$10,000 in EMG2-20 from mid-December 2026** (`AMENDMENT_live_EMG2_20.md`). The conditions are recorded as "not met, waived". The cap, the stop rules, and steps P2 and P3 apply to that slice unchanged. The waiver covers no other line, amount or date.

## 7. Honest limits
A signal can keep sorting shares inside a band that as a whole keeps losing to the index; P2 and P3 carry an index condition for that reason, P1 does not. The twins test compares the book with chance in the same pond, not with the fund. V3 will let money into a line with no edge more often than v2 would (never); the price of that is bounded by the caps.

## 8. Trial count
A change of method, not a trial. No change to N.
