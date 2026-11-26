# Cheaper-broker re-scoring (INFORMATION ONLY) - as of 2026-11-26

**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. No real money; the AI never places trades.**

Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** (A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.

| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | 4 | 26.40 | -0.95% | -0.66% | -0.42% | -1.36% | +0.41% | +0.70% | +0.94% | -1.24% | +0.29% | +0.82% |
| H82_25k | 10 | 66.00 | -0.52% | -0.38% | -0.26% | -1.36% | +0.84% | +0.98% | +1.10% | -1.24% | +0.72% | +0.98% |
| H82_100k | 30 | 198.00 | -0.70% | -0.59% | -0.50% | -1.36% | +0.67% | +0.77% | +0.86% | -1.24% | +0.54% | +0.74% |

Generated 2026-11-26T09:28:18Z by paper_costalt.py; state.json sha256 f8adec62a9af4853734c8d2d3496e8302bafedc6ea5b56921ef35be0ab9cf811; score_state.json sha256 c6cc0ccc5af7503fca1fb0a34c69a92d8a0fec596d7a35558fbdc5be4d51f03c.
History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.
