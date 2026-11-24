# Cheaper-broker re-scoring (INFORMATION ONLY) - as of 2026-11-24

**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. No real money; the AI never places trades.**

Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** (A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.

| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | 4 | 26.40 | +1.10% | +1.39% | +1.63% | -1.85% | +2.95% | +3.24% | +3.48% | -1.21% | +2.31% | +2.84% |
| H82_25k | 10 | 66.00 | +0.32% | +0.46% | +0.58% | -1.85% | +2.17% | +2.31% | +2.43% | -1.21% | +1.53% | +1.79% |
| H82_100k | 30 | 198.00 | -0.28% | -0.17% | -0.08% | -1.85% | +1.58% | +1.68% | +1.77% | -1.21% | +0.93% | +1.13% |

Generated 2026-11-24T09:28:52Z by paper_costalt.py; state.json sha256 d93dcd63269c0af7aec14b4f864c11ce6d3675ec67f5e19401a6d3b707cb1f76; score_state.json sha256 bef9ed81a6b32e2f7e1b19ed1ca3527cf3b2c9add9add487e93ce9242f90c1a4.
History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.
