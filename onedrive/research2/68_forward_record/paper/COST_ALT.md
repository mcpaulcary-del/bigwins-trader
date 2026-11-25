# Cheaper-broker re-scoring (INFORMATION ONLY) - as of 2026-11-25

**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. No real money; the AI never places trades.**

Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** (A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.

| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | 4 | 26.40 | +1.76% | +2.04% | +2.28% | -2.22% | +3.98% | +4.26% | +4.50% | -1.72% | +3.48% | +4.01% |
| H82_25k | 10 | 66.00 | +0.67% | +0.81% | +0.93% | -2.22% | +2.89% | +3.03% | +3.15% | -1.72% | +2.39% | +2.65% |
| H82_100k | 30 | 198.00 | -0.04% | +0.07% | +0.16% | -2.22% | +2.18% | +2.29% | +2.38% | -1.72% | +1.68% | +1.88% |

Generated 2026-11-25T09:28:03Z by paper_costalt.py; state.json sha256 9c81954522bbcf5f90a9fdee2b30c7f76525ba9b235a240a38b44af5307bd4d8; score_state.json sha256 1328764cdd1bd7abdeac0104db5a038f9e6c6e5ce787924ae9baabc9f01d1d72.
History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.
