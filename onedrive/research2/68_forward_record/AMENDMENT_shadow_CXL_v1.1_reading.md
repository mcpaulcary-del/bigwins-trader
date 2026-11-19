# Amendment: SHADOW CXL v1.1 — reading rule and no-screen twin; avoid-list measurement line registered (pending)

Status: **ADOPTED 19 Nov 2026** (owner standing instruction "just do it, don't keep asking"; report 82 §0 "What to do" (ii), §9 and §10, `82_round10_loser_filter_fable.md`). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before the CXL code is installed** and before any CXL decision exists (first decision Mon 30 Nov 2026). PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence.
Amends `AMENDMENT_shadow_CXL_D2.md` (CXL v1.0) in §4 (scoring) and §3 (books) only. The trading rules of CXL v1.0 are unchanged.

## 1. Why
Report 82 §5.1: D2's small lead over the fund in report 81 came from holding the largest companies, not from the momentum screen. Against the *same book with no screen* D2 was −0.50 (A$25k) / +0.19 (A$100k) a year after tax over 17 sets; on ASX 2018–2026 the screen subtracted 0.75–0.95. A CXL lead over the fund will therefore be misread as "the screen works" whenever large companies lead the index.

## 2. Reading rule (scorecard)
The CXL scorecard line **leads with "CXL minus the median random-exclusion book"** (time-weighted return since the start, same size), i.e. the screen's own contribution, with the CXL book's percentile among the 100 random books beside it. The expectation is about zero. The comparison with the A200 fund (A$0) and the after-tax figures follow on the same line, labelled as secondary. In `scorecard_latest.csv` the columns `vs_random_median` and `random_median_return` are added to the CXL rows.

## 3. No-screen twin (added book per size)
Report 82 §10 notes that a no-exclusion twin is cleaner still and costs one book per size ("the record keeper's call"). Added: `SHADOW_CXL_TWIN_25k`, `SHADOW_CXL_TWIN_100k` — CXL v1.0 rules exactly, except that rule 4 excludes nobody (every scored company of the M3 table with a cap is in the list). Same start, costs, clock and data blocks. Reported on the CXL line as "CXL minus twin" (secondary to §2: the twin is one path; the random median is the noise-floor reference). Information only.

## 4. Avoid-list measurement line v1.0 (`deep82/SPEC_avoid_list_measurement_line.md`, SHA-256 in the ledger entry): REGISTERED, IMPLEMENTATION PENDING
The spec is registered as an information-only forward measurement (no book, no decision, nothing can be bought; not adoptable under adopt rule v2). It needs monthly universes, traded-value ranks, M3 and residual-momentum scores and caps for the 19 non-US sets of the multi-market record plus ASX, with next-day-close returns, pooled monthly. That is not a small, testable addition to the daily ASX job before 30 Nov 2026: the multi-market line (`paper_multi.py`) builds its packs monthly on its own clock, and the non-ASX traded-value ranking is itself flagged for repair (report 82 §0 (v)). **Implementation is pending.** Because the measurement is computed from end-of-day closes, the readings from 30 Nov 2026 can be rebuilt exactly later from the stored data (EODHD history; ASIC files for W2 on ASX) provided the frozen code (`deep82/code/lib82.py`, `panel.py`, `rules.py`) is used and no reading is looked at before the code is frozen and hashed into this ledger. First month-end of the record: 30 Nov 2026.

## 5. Trial count
A reading rule, one control book per size and a registered measurement; no back-test return computed. Report 82 counted 30 trials: **N = 1,759** (1,729 + 30). This amendment adds none. The verdict stands for all lines: not shown to beat the index.
