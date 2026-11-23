# Cheaper-broker re-scoring (INFORMATION ONLY) - as of 2026-11-23

**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. No real money; the AI never places trades.**

Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** (A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.

| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | 4 | 26.40 | -1.02% | -0.73% | -0.49% | -3.61% | +2.59% | +2.88% | +3.12% | -3.39% | +2.37% | +2.90% |
| H82_25k | 10 | 66.00 | -1.63% | -1.49% | -1.37% | -3.60% | +1.97% | +2.12% | +2.24% | -3.39% | +1.76% | +2.02% |
| H82_100k | 30 | 198.00 | -2.27% | -2.16% | -2.07% | -3.60% | +1.34% | +1.45% | +1.54% | -3.39% | +1.12% | +1.32% |

Generated 2026-11-23T09:28:02Z by paper_costalt.py; state.json sha256 7b36e4e213b7c2a2d75e888644dec930dd59508e12aa478a49d47d118724f0bf; score_state.json sha256 abc89a2eda956151afc3b331df9d07e66438299169a89f872e99854431e98640.
History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.
