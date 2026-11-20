# Cheaper-broker re-scoring (INFORMATION ONLY) - as of 2026-11-20

**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. No real money; the AI never places trades.**

Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** (A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.

| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | 4 | 26.40 | -0.75% | -0.46% | -0.22% | -3.28% | +2.52% | +2.81% | +3.05% | -3.00% | +2.24% | +2.77% |
| H82_25k | 10 | 66.00 | -1.13% | -0.98% | -0.86% | -3.28% | +2.15% | +2.29% | +2.41% | -3.00% | +1.87% | +2.13% |
| H82_100k | 30 | 198.00 | -1.74% | -1.63% | -1.54% | -3.28% | +1.54% | +1.64% | +1.73% | -3.00% | +1.26% | +1.45% |

Generated 2026-11-20T09:27:44Z by paper_costalt.py; state.json sha256 0a355d0bd1f8385a386494a13db94c24d6a2a97ef65e3fb846a32c2e7f4b3c51; score_state.json sha256 74eb7ef372b3b50cfaee9ff0855c791071b65a840540cc1760253f7af5ccbd87.
History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.
