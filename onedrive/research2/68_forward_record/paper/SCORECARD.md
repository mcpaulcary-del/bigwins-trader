# Big Wins paper scorecard — 2026-11-19

**PAPER - Big Wins. Not shown to beat the index. No real money; no broker orders; the AI never places trades.**

## Lead challenger: EMG2 (SHADOW, paper only; H82 below is the large-company control)

| Line | NAV A$ | Return | Reading |
|---|---|---|---|
| **EMG2 (lead challenger; AMENDMENT_shadow_EMG2.md)** | — | — | SHADOW EMG2 v1.0 (report 85 T6): lead challenger; not adopted; tracked on paper; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$100k and A$25k, 100 random twins each, BANDSPREAD measurement line. Expectation: Back-test +4.9 a year after costs and yearly tax on seen data; forward estimate +1 to +3; zero is possible; falls of 40-60% are normal for this line. |

Start decision 2026-11-16, fills at the close of 2026-11-17. Rules v1.3 (SHA-256 b38abcd7…) + AMENDMENT_start_now.md (+ v1.4 and v1.5 from 31 Dec 2026). Fills at the close under v1.3 D/E (brokerage max(A$6.60, 0.088%), half-spread E2). After costs, before tax unless marked "after tax". Returns are time-weighted (unit index), so contributions do not count as gains. **Comparators: A200 and the 40/60 plan at A$0 brokerage (the owner's platform) are the benchmark** (AMENDMENT_scoring_v2.md); the frozen J3 comparators (A$6.60 per fund purchase) are in the second table.

| Book | NAV A$ | Contributed | Return | A200 (A$0) | vs A200 | 40/60 (A$0) | vs 40/60 | After tax, kept: vs A200 kept | After tax, sold: vs A200 sold | Holdings | Cash | % of random |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k (illustration only) | 4,981.99 | 0 | -0.36% | -1.71% | +1.35% | -0.73% | +0.37% | +1.35% | +0.75% | 4 | 63.53 |  |
| H82_25k | 24,840.58 | 0 | -0.64% | -1.71% | +1.07% | -0.73% | +0.09% | +1.07% | +0.69% | 10 | 172.12 | 0.93 |
| H82_100k | 98,983.84 | 0 | -1.02% | -1.71% | +0.69% | -0.73% | -0.29% | +0.69% | +0.36% | 30 | 430.65 | 0.94 |
| MOM_25k | 23,927.44 | 0 | -4.29% | -1.71% | -2.58% | -0.73% | -3.56% | -2.58% | -3.03% | 10 | 64.80 |  |
| MOM_100k | 95,874.24 | 0 | -4.13% | -1.71% | -2.42% | -0.73% | -3.40% | -2.42% | -2.69% | 10 | 41.02 |  |

After tax: 32% rate, 50% discount for parcels held 367+ days, cumulative from the start; "kept" = tax on income and on gains already realised; "sold" = as if every holding were sold at the day's close (sale costs included). Franking credits not yet counted on either side. The owner's real comparison is the engine "sold" against the fund "kept" (CSV column vs_a200_b0_engine_sold_fund_kept).

**Flag — 31 Dec 2026 review:** rule C5 will sell every holding not on the December list six weeks after the 17 Nov start: an extra round trip (about 0.3–0.7% of the book) and short-term gains. That cost belongs to the start date, not to the engine's normal running (review 80 §1.5).

| Frozen J3 comparator (A$6.60 per fund purchase) | Book | vs A200 (J3) | vs 40/60 (J3) |
|---|---|---|---|
| A200 -1.84%; 40/60 -0.99% | H82_lifecycle_5k | +1.48% | +0.63% |
| A200 -1.80%; 40/60 -0.82% | H82_25k | +1.16% | +0.18% |
| A200 -1.80%; 40/60 -0.82% | H82_100k | +0.78% | -0.20% |
| A200 -1.80%; 40/60 -0.82% | MOM_25k | -2.49% | -3.47% |
| A200 -1.80%; 40/60 -0.82% | MOM_100k | -2.33% | -3.31% |

| Comparator / control | NAV A$ | Return | Note |
|---|---|---|---|
| CMP_A200_lifecycle_5k_b0 | 4,914.50 | -1.71% | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |
| CMP_4060_lifecycle_5k_b0 | 4,963.52 | -0.73% | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |
| CMP_A200_25k_b0 | 24,572.52 | -1.71% | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |
| CMP_4060_25k_b0 | 24,817.59 | -0.73% | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |
| CMP_A200_100k_b0 | 98,290.07 | -1.71% | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |
| CMP_4060_100k_b0 | 99,270.36 | -0.73% | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |
| CMP_A200_lifecycle_5k (J3 as frozen) | 4,908.02 | -1.84% | A$6.60 per fund purchase; EODHD proxy |
| CMP_4060_lifecycle_5k (J3 as frozen) | 4,950.44 | -0.99% | A$6.60 per fund purchase; EODHD proxy |
| CMP_A200_25k (J3 as frozen) | 24,550.89 | -1.80% | A$6.60 per fund purchase; EODHD proxy |
| CMP_4060_25k (J3 as frozen) | 24,795.75 | -0.82% | A$6.60 per fund purchase; EODHD proxy |
| CMP_A200_100k (J3 as frozen) | 98,203.57 | -1.80% | A$6.60 per fund purchase; EODHD proxy |
| CMP_4060_100k (J3 as frozen) | 99,183.00 | -0.82% | A$6.60 per fund purchase; EODHD proxy |
| RND_25k (200 seeds) | | -2.53% | median; 5th-95th pct -0.0436 to -0.0029 |
| RND_100k (200 seeds) | | -2.56% | median; 5th-95th pct -0.0363 to -0.0078 |
| SHADOW M3 (report 76 §6, R1-R11) | — | — | SHADOW: not adopted; tracked for information; own clock: first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026 (AMENDMENT_shadow_M3_E3.md) |
| SHADOW E3 (report 73 §6, T1-T11) | — | — | SHADOW: not adopted; tracked for information; own clock: first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026 (AMENDMENT_shadow_M3_E3.md) |
| SHADOW ACC (keep winners; AMENDMENT_shadow_ACC_keep_winners.md) | — | — | SHADOW ACC: not adopted; tracked for information; illustration only (A$5k); first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026 |
| SHADOW CXL (report 81 D2; AMENDMENT_shadow_CXL_D2.md) | — | — | SHADOW CXL (report 81 D2): not adopted; tracked for information; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$25k and A$100k, 100 random-exclusion books and a no-screen twin each; read as CXL minus the median random book |
| SHADOW EARLY (report 84; AMENDMENT_shadow_EARLY.md) | — | — | SHADOW EARLY (report 84): INFORMATION ONLY, UNPROVEN; not shown to beat the index; first decision Mon 30 Nov 2026 (with start-up catch-up), fills Tue 1 Dec 2026; About level with the index fund, with a much bumpier ride; a small chance of one large winner. |

## Holdings (H82 books)

| Book | Code | Name | Shares | Cost A$ | Last | Value A$ | P&L A$ | P&L | Flags |
|---|---|---|---|---|---|---|---|---|---|
| H82_lifecycle_5k | CPU | Computershare Ltd | 27 | 1,234.44 | 45.68 (2026-11-19) | 1,233.36 | -1.08 | -0.09% |  |
| H82_lifecycle_5k | QBE | QBE Insurance Group Limited | 46 | 1,233.27 | 26.27 (2026-11-19) | 1,208.42 | -24.85 | -2.01% |  |
| H82_lifecycle_5k | RHC | Ramsay Health Care Ltd | 23 | 1,241.78 | 54.41 (2026-11-19) | 1,251.43 | 9.65 | +0.78% |  |
| H82_lifecycle_5k | WOW | Woolworths Group Ltd | 29 | 1,226.98 | 42.25 (2026-11-19) | 1,225.25 | -1.73 | -0.14% |  |
| H82_25k | ALL | Aristocrat Leisure Ltd | 38 | 2,495.05 | 64.79 (2026-11-19) | 2,462.02 | -33.03 | -1.32% |  |
| H82_25k | ANN | Ansell Ltd | 53 | 2,476.73 | 46.09 (2026-11-19) | 2,442.77 | -33.96 | -1.37% |  |
| H82_25k | APA | APA Group | 217 | 2,493.73 | 11.35 (2026-11-19) | 2,462.95 | -30.78 | -1.23% |  |
| H82_25k | ASX | ASX Ltd | 37 | 2,488.82 | 66.46 (2026-11-19) | 2,459.02 | -29.80 | -1.20% |  |
| H82_25k | CGF | Challenger Ltd | 206 | 2,497.17 | 11.74 (2026-11-19) | 2,418.44 | -78.73 | -3.15% |  |
| H82_25k | CPU | Computershare Ltd | 54 | 2,462.27 | 45.68 (2026-11-19) | 2,466.72 | 4.45 | +0.18% |  |
| H82_25k | FPH | Fisher & Paykel Healthcare C | 62 | 2,461.10 | 40.61 (2026-11-19) | 2,517.82 | 56.72 | +2.30% |  |
| H82_25k | QBE | QBE Insurance Group Limited | 93 | 2,486.60 | 26.27 (2026-11-19) | 2,443.11 | -43.49 | -1.75% |  |
| H82_25k | RHC | Ramsay Health Care Ltd | 46 | 2,476.97 | 54.41 (2026-11-19) | 2,502.86 | 25.89 | +1.05% |  |
| H82_25k | WOW | Woolworths Group Ltd | 59 | 2,489.44 | 42.25 (2026-11-19) | 2,492.75 | 3.31 | +0.13% |  |
| H82_100k | ALL | Aristocrat Leisure Ltd | 50 | 3,280.87 | 64.79 (2026-11-19) | 3,239.50 | -41.37 | -1.26% |  |
| H82_100k | ANN | Ansell Ltd | 71 | 3,315.64 | 46.09 (2026-11-19) | 3,272.39 | -43.25 | -1.30% |  |
| H82_100k | ANZ | ANZ Group Holdings Ltd | 84 | 3,327.08 | 39.0 (2026-11-19) | 3,276.00 | -51.08 | -1.54% |  |
| H82_100k | APA | APA Group | 290 | 3,330.42 | 11.35 (2026-11-19) | 3,291.50 | -38.92 | -1.17% |  |
| H82_100k | ARG | Argo Investments Ltd | 351 | 3,331.84 | 9.34 (2026-11-19) | 3,278.34 | -53.50 | -1.61% |  |
| H82_100k | ASX | ASX Ltd | 49 | 3,293.86 | 66.46 (2026-11-19) | 3,256.54 | -37.32 | -1.13% |  |
| H82_100k | BGA | Bega Cheese Ltd | 502 | 3,328.08 | 6.44 (2026-11-19) | 3,232.88 | -95.20 | -2.86% |  |
| H82_100k | BOQ | Bank of Queensland Ltd | 470 | 3,328.38 | 7.04 (2026-11-19) | 3,308.80 | -19.58 | -0.59% |  |
| H82_100k | CCP | Credit Corp Group Ltd | 211 | 3,323.35 | 15.38 (2026-11-19) | 3,245.18 | -78.17 | -2.35% |  |
| H82_100k | CGF | Challenger Ltd | 275 | 3,331.39 | 11.74 (2026-11-19) | 3,228.50 | -102.89 | -3.09% |  |
| H82_100k | CPU | Computershare Ltd | 73 | 3,326.31 | 45.68 (2026-11-19) | 3,334.64 | 8.33 | +0.25% |  |
| H82_100k | CSL | CSL Ltd | 16 | 3,202.59 | 199.85 (2026-11-19) | 3,197.60 | -4.99 | -0.16% |  |
| H82_100k | CWY | Cleanaway Waste Management L | 1,103 | 3,332.14 | 3.01 (2026-11-19) | 3,320.03 | -12.12 | -0.36% |  |
| H82_100k | DDR | Dicker Data Ltd | 240 | 3,319.66 | 13.55 (2026-11-19) | 3,252.00 | -67.66 | -2.04% |  |
| H82_100k | DTL | Data 3 Ltd | 230 | 3,326.88 | 14.1 (2026-11-19) | 3,243.00 | -83.88 | -2.52% |  |
| H82_100k | EVT | EVT Ltd | 214 | 3,321.17 | 15.4 (2026-11-19) | 3,295.60 | -25.57 | -0.77% |  |
| H82_100k | FPH | Fisher & Paykel Healthcare C | 84 | 3,332.05 | 40.61 (2026-11-19) | 3,411.24 | 79.19 | +2.38% |  |
| H82_100k | IAG | Insurance Australia Group Lt | 367 | 3,327.60 | 9.01 (2026-11-19) | 3,306.67 | -20.93 | -0.63% |  |
| H82_100k | MPL | Medibank Private Ltd | 620 | 3,333.12 | 5.25 (2026-11-19) | 3,255.00 | -78.12 | -2.34% |  |
| H82_100k | OML | Ooh!Media Ltd | 1,987 | 3,333.19 | 1.67 (2026-11-19) | 3,318.29 | -14.90 | -0.45% |  |
| H82_100k | ORG | Origin Energy Ltd | 264 | 3,325.76 | 12.47 (2026-11-19) | 3,292.08 | -33.68 | -1.01% |  |
| H82_100k | QBE | QBE Insurance Group Limited | 124 | 3,313.26 | 26.27 (2026-11-19) | 3,257.48 | -55.78 | -1.68% |  |
| H82_100k | REH | Reece Ltd | 175 | 3,315.35 | 18.67 (2026-11-19) | 3,267.25 | -48.10 | -1.45% |  |
| H82_100k | RHC | Ramsay Health Care Ltd | 61 | 3,282.52 | 54.41 (2026-11-19) | 3,319.01 | 36.49 | +1.11% |  |
| H82_100k | SDF | Steadfast Group Ltd | 574 | 3,332.61 | 5.8 (2026-11-19) | 3,329.20 | -3.41 | -0.10% |  |
| H82_100k | SOL | Washington H Soul Pattinson  | 70 | 3,332.82 | 47.14 (2026-11-19) | 3,299.80 | -33.02 | -0.99% |  |
| H82_100k | STO | Santos Ltd | 384 | 3,331.52 | 8.5 (2026-11-19) | 3,264.00 | -67.52 | -2.03% |  |
| H82_100k | SUN | Suncorp Group Ltd | 162 | 3,326.06 | 20.66 (2026-11-19) | 3,346.92 | 20.86 | +0.63% |  |
| H82_100k | TWE | Treasury Wine Estates Ltd | 520 | 3,332.72 | 6.3 (2026-11-19) | 3,276.00 | -56.72 | -1.70% |  |
| H82_100k | WOW | Woolworths Group Ltd | 79 | 3,331.08 | 42.25 (2026-11-19) | 3,337.75 | 6.67 | +0.20% |  |

## Data notes

- Q6 flags: none
- Data blocks: none
- Decisions so far: 2026-11-16
