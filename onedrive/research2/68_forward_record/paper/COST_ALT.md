# Cheaper-broker re-scoring (INFORMATION ONLY) - as of 2026-11-19

**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. No real money; the AI never places trades.**

Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** (A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.

| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | 4 | 26.40 | -0.36% | -0.07% | +0.17% | -1.71% | +1.35% | +1.64% | +1.88% | -0.73% | +0.37% | +0.90% |
| H82_25k | 10 | 66.00 | -0.64% | -0.49% | -0.37% | -1.71% | +1.07% | +1.22% | +1.34% | -0.73% | +0.09% | +0.36% |
| H82_100k | 30 | 198.00 | -1.02% | -0.91% | -0.82% | -1.71% | +0.69% | +0.80% | +0.89% | -0.73% | -0.29% | -0.09% |

Generated 2026-11-19T09:28:12Z by paper_costalt.py; state.json sha256 a65bdab8e085c16d3c1da019f9e550f2f6c756735aa33ba62dd52a8a6c265ccc; score_state.json sha256 579b2e75d0238ddccfa70ff09e1d2e55abbd8c873b7ab197b18373bd098a7c9e.
History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.
