# 76. Round 5 — pooled learning across 20 market-sets, new fresh markets and a first fundamentals test

17 November 2026. Research and paper only. General information, not financial or tax advice. Nothing here can place an order.
Work folder: `scratchpad/improve5/` (`PREREG_76.md`, `PREREG_76F.md`, `code/`, `out/`, `data/`, `PROGRESS.md`). Trial ledger: `out/trials_76.csv` (cumulative count 1,197 → 1,543). Nothing was written to `68_forward_record/` or `bigwins_forward/`.

## 0. Plain-English verdict

**Question.** Rounds 1–4 each designed on one or two markets and lost on fresh ones. Does a design chosen because it works across all 18 market-sets seen so far beat a cheap local index fund, after costs and Australian tax, on markets it has never seen?

**Answer: closer than any earlier round, and still not adopted.** The pooled design (M3) led the local index fund in both valid fresh markets at both account sizes. It failed the two pre-registered tests that separate skill from luck, so the bar was not met. Real money stays in the 40/60 plan.

1. **What the pool taught.** With every earlier market treated as development, three things held across markets (section 2):
   - The best share-picking signal against an index fund is plain price momentum: 12-month return, 6-month return and nearness to the 52-week high. The trend-quality score of rounds 3–4 and H80 were in the bottom half. Low volatility, which H80 contains, hurts.
   - Structure hardly matters. Fund share, number of names, weighting, cadence, hold bands and tax rules each move the average lead by 0.3 point a year or less. The settings that are least bad: half the money in the index fund, 15 names from the 100 most-traded shares, equal weights, monthly decisions, never sell a gain before 12 months.
   - A random portfolio in that structure loses about 2 points a year to the fund. Costs are not the reason. A handful of equal-weighted large companies simply trails a cap-weighted index. The signal earns 2–3 points, which leaves little.
2. **The in-pool test said "small edge, coin toss per market".** A design fixed on data to 2022 led the fund by 0.7 points a year over 2023–26 on average, and was ahead in 9 of 18 markets.
3. **Only two unused markets were fit for an honest test.** Of 27 unused exchanges on the data plan, only Thailand and China have 100 liquid names, a usable local index fund, dead companies in the file and clean data.
4. **The one look (M3, frozen and hashed first).**

| | Thailand | China | Bar | Met? |
|---|---|---|---|---|
| Lead over the local fund after tax, points a year (A$25k / A$100k) | **+2.5 / +1.6** | **+2.9 / +2.3** | +1 or better at both sizes in both markets | yes |
| Worst cell | +1.6 | +2.3 | none below −2 | yes |
| Percentile among 100 random portfolios of the same shape | 92 / 94 | 79 / 79 | 90 or better in both markets | **no** |
| Top five positions' share of profit | 380% | 205% | under 50% | **no** |
| Deflated Sharpe ratio at about 1,450 trials | 0.00 | 0.02 | reported (usual line 0.95) | far below |

5. **Why that is not a pass.** In China one random portfolio in five did better. In both markets the whole profit came from five shares. The lead arrived in two or three boom years and was negative in the years between. At A$25,000 the book is five or six shares, and one different purchase turned China from +2.6 to −1.8. The owner's account (A$5,000 plus A$500 a month) ended **behind** the fund in Thailand (A$62,000 against A$67,600) and level in China.
6. **Three more fresh markets, opened for the fundamentals test.** Plain M3 scored −0.8 / +0.1 in Finland, +1.6 / +2.3 in Poland and +0.3 / +1.6 in Belgium. Over all five fresh markets of this round M3 was ahead of the fund in every one at A$100,000 (mean +1.6) and in four at A$25,000 (mean +1.3). No earlier design met the +1 bar in more than one market of its look. All five are markets whose index fund did poorly (1–10% a year). In the pool, M3 trailed where a few giants drove the index (Taiwan, Switzerland, US large companies).
7. **Fundamentals did not help.** The owner's new EODHD fundamentals subscription was tested the same day (section 8). Quality scores (profitability, low accruals, low debt) added nothing to momentum to 2022 and cost 2–3 points a year in 2023–26. Value did the reverse. Only "low share issuance" did not hurt. In the pre-registered look at Finland, Poland and Belgium the issuance design scored +1.2 / +0.3, +7.3 / +1.6 and +2.0 / +1.9, but it beat plain M3 on the same shares at both sizes in only one of three markets. Not adopted either.
8. **Data errors were hunted before each look** (section 3). The worst: more than half of the vendor's Thai "common stocks" are depositary receipts of foreign shares or second lines of the same company; a large Thai company was missing after a rate-limit error; the vendor's fundamentals "filing date" is just the period end, so a four-month lag was imposed.
9. **Against the 40/60 plan.** Unchanged. M3's fresh-market returns after tax (2.6% and 4.0% a year at A$100,000) are far below what the plan's funds earned.
10. **What to do.** (a) Put M3 on the paper record beside H82 and E3. Zero-ambiguity rules and two ASX snapshots are ready (section 6); adding them to the record is the owner's call. (b) Use the paid fundamentals month for one ten-market look at low issuance, and to build the true cap-weighted reference that report 75 could not (section 8.6). (c) Do not fund any of it.
11. **Confidence.** High that nothing here meets the bar. Moderate that M3 is a real improvement on E3 and H80 as a share-picker (it was ahead in 5 of 5 fresh markets at A$100,000; E3 was behind in both of this round's main markets). Low that its lead over an index fund is large enough to survive tax, costs and a market led by giants. All fresh exchanges with 100 liquid names are now used. Only time adds clean evidence from here.

---

## 1. What was done

| Step | What | Counted trials |
|---|---|---|
| Engine | `code/sim5.py` = report 75's engine plus three switches: decision cadence, inverse-volatility weights, a fund share that rises with index concentration. `code/lib5.py` loads all 18 earlier market-sets with three windows each: design (to 30 Dec 2022), check (30 Dec 2022 – 30 Oct 2026) and whole | — |
| Pooled development | Signals (34), structure levers (111), structure drag and more signals (14), momentum blends × structures (60), in-pool check (11), sorting panels (10), one machinery test | 241 |
| Fresh markets | 27 unused exchanges screened; 17 downloaded (about 20,000 price series); packs built and checked for errors before any return (`out/qa2.log`, `out/mk_*.log`, `out/coverage_*.csv`) | 0 |
| Pre-registration | `PREREG_76.md`, hashed in `out/prereg76_hash.txt` at N = 1,446 | — |
| The look | M3 on Thailand and China, once; five descriptive designs beside it; two sorting panels | 12 + 16 |
| Fundamentals stage | section 8 | 69 |

Cumulative count for the deflated Sharpe ratio: 1,197 → **1,543**.

One change from report 75: start months are now the true quarter-end rows of each market's calendar. Report 75 used fixed dates (for example 29 Mar 2018), which fell one month early in markets that traded on 30 Mar 2018. Pooled figures for the old designs therefore differ from report 75 by a few tenths.

## 2. Pooled learning: what works across about 20 market-sets

All figures in this section are development. X = after-tax CAGR of the design minus the local fund's, points a year, mean of four start months, at A$25,000 and A$100,000. "Design windows" end on 30 Dec 2022 (22 set-windows: 18 market-sets plus the early eras of ASX and the three US size bands). "Check windows" run 30 Dec 2022 – 30 Oct 2026 (18 market-sets). Designs were compared on the design windows only; the check windows were opened once for the chosen design. A "cell" is one market-set at one account size.

### 2.1 Which signal

Structure held fixed: 50% index fund + the 15 best of the 100 most-traded shares, sold after two months below rank 50.

| Signal | Mean lead | Median | Market-sets ahead of the fund | At +1 or better at both sizes | Cells below −2 | Worst cell | Turnover a year |
|---|---|---|---|---|---|---|---|
| 6-month return (s2) | +0.79 | +0.55 | 12 of 22 | 7 of 22 | 9 of 44 | -6.0 | 0.64 |
| M3: s1+s2+s3 | +0.76 | +0.36 | 14 of 22 | 7 of 22 | 3 of 44 | -3.6 | 0.53 |
| s1+s3 | +0.15 | -0.07 | 11 of 22 | 4 of 22 | 8 of 44 | -4.4 | 0.49 |
| 12-month return (s1) | -0.00 | -0.27 | 11 of 22 | 6 of 22 | 13 of 44 | -7.6 | 0.50 |
| 52-week-high recency | -0.06 | -0.16 | 10 of 22 | 5 of 22 | 7 of 44 | -3.9 | 0.53 |
| Nearness to 52-week high (s3) | -0.09 | -0.20 | 10 of 22 | 6 of 22 | 4 of 44 | -3.7 | 0.53 |
| s3+recency | -0.20 | -0.41 | 9 of 22 | 3 of 22 | 3 of 44 | -3.6 | 0.49 |
| Residual momentum | -0.31 | -0.72 | 10 of 22 | 5 of 22 | 11 of 44 | -6.0 | 0.47 |
| Trend quality (E3) | -0.61 | -0.96 | 7 of 22 | 3 of 22 | 12 of 44 | -5.3 | 0.49 |
| H80 | -0.76 | -0.89 | 6 of 22 | 3 of 22 | 8 of 44 | -5.2 | 0.44 |
| Trend quality + recency | -0.84 | -1.03 | 7 of 22 | 4 of 22 | 14 of 44 | -4.7 | 0.48 |
| CH | -0.89 | -1.06 | 6 of 22 | 4 of 22 | 15 of 44 | -8.6 | 0.52 |
| H80 + residual momentum | -0.91 | -1.09 | 5 of 22 | 1 of 22 | 10 of 44 | -5.9 | 0.44 |
| s1+s3+s4+trend+recency | -1.09 | -1.39 | 5 of 22 | 1 of 22 | 12 of 44 | -4.3 | 0.41 |
| Low volatility (s4) | -1.40 | -1.40 | 4 of 22 | 1 of 22 | 11 of 44 | -7.8 | 0.21 |
| Path smoothness | -2.02 | -2.07 | 5 of 22 | 3 of 22 | 22 of 44 | -9.4 | 0.56 |
| Random scores, seed 1 | -2.00 | -2.35 | 3 of 22 | 1 of 22 | 25 of 44 | -5.6 | 0.97 |
| Random scores, seed 2 | -1.92 | -1.60 | 0 of 22 | 0 of 22 | 17 of 44 | -5.5 | 0.99 |
| Random scores, seed 3 | -1.73 | -1.77 | 3 of 22 | 0 of 22 | 19 of 44 | -7.6 | 0.99 |

- The trend-quality score of rounds 3–4 and H80 (behind H82) are in the bottom half: ahead of the fund in 7 and 6 of 22 set-windows.
- The best were plain price-momentum blends that include the 6-month return. **M3** (12-month return skipping the last month, 6-month return, nearness to the 52-week high; that is, H80 without its low-volatility term) was ahead in 14 of 22 with only 3 of 44 cells below −2.
- Low volatility hurts against a cap-weighted fund in large companies (ahead in 4 of 22). That is why H80 trails M3.
- Random scores in the same structure lose about 1.9 points a year. So the signal is worth roughly 2 to 2.7 points a year on the account, and the structure hands about 2 of them back.

Sorting power tells a different story from portfolio results (table T6 in `out/dev_tables.md`). 52-week-high recency sorts the 100 most-traded shares with a positive slope in 22 of 22 design set-windows and 18 of 18 check windows, trend quality in 19 and 17, M3 in 17 and 12. A signal can sort the whole list well, mostly by flagging losers, and still pick a weaker top 15. A long-only book uses only the top.

### 2.2 Which structure

One lever at a time around the same base; mean of three signals (recency, nearness to the high, 12-month return).

| Lever | Setting | Mean lead | Market-sets ahead (mean of 3 signals, of 22) | Cells below −2 (of 44) | Turnover |
|---|---|---|---|---|---|
| Fund share | 0% | -0.22 | 10.7 | 14.7 | 1.09 |
| Fund share | 30% | -0.19 | 10.0 | 13.0 | 0.73 |
| Fund share | 50% (base) | -0.05 | 10.3 | 8.0 | 0.52 |
| Fund share | 70% | -0.08 | 8.3 | 3.7 | 0.31 |
| Fund share | 85% | -0.37 | 5.0 | 0.0 | 0.14 |
| Size band / names | 50 most traded, buy top 8 | +0.09 | 11.3 | 6.3 | 0.49 |
| Size band / names | 100, buy top 15 (base) | -0.05 | 10.3 | 8.0 | 0.52 |
| Size band / names | 200, buy top 15 | -0.42 | 9.7 | 11.3 | 0.56 |
| Size band / names | 300, buy top 30, hold to 150 | -0.78 | 7.3 | 12.3 | 0.40 |
| Buy / hold band | top 5 / hold 30 | -0.28 | 9.3 | 10.0 | 0.53 |
| Buy / hold band | top 10 / 40 | -0.06 | 12.7 | 10.0 | 0.58 |
| Buy / hold band | top 15 / 30 | -0.11 | 10.3 | 9.0 | 0.77 |
| Buy / hold band | top 15 / 50 (base) | -0.05 | 10.3 | 8.0 | 0.52 |
| Buy / hold band | top 15 / 75 | -0.61 | 7.0 | 8.7 | 0.35 |
| Buy / hold band | top 15 / 100 | -1.17 | 5.0 | 13.0 | 0.24 |
| Buy / hold band | top 20 / 60 | -0.21 | 9.3 | 8.0 | 0.44 |
| Names | at most 10 | -0.11 | 10.0 | 10.3 | 0.53 |
| Names | at most 20 | -0.06 | 10.7 | 8.0 | 0.52 |
| Names | positions of A$1,250 | -0.19 | 9.3 | 7.3 | 0.49 |
| Names | positions of A$5,000 | -0.02 | 9.0 | 9.0 | 0.54 |
| Cadence | monthly, 2 confirmations (base) | -0.05 | 10.3 | 8.0 | 0.52 |
| Cadence | monthly, 1 | -0.19 | 11.3 | 9.7 | 0.66 |
| Cadence | monthly, 3 | -0.29 | 8.7 | 8.7 | 0.44 |
| Cadence | quarterly | -0.45 | 8.0 | 11.0 | 0.48 |
| Cadence | half-yearly | -0.80 | 4.7 | 12.0 | 0.36 |
| Cadence | yearly | -1.10 | 4.3 | 12.3 | 0.24 |
| Weighting | equal (base) | -0.05 | 10.3 | 8.0 | 0.52 |
| Weighting | inverse volatility | -0.27 | 9.7 | 7.7 | 0.51 |
| Weighting | score tilt | -0.06 | 9.0 | 8.3 | 0.53 |
| Weighting | traded value ^0.5 | -0.19 | 9.3 | 8.0 | 0.53 |
| Weighting | traded value | -0.29 | 9.3 | 9.3 | 0.54 |
| Tax rules | no gain sale before 12 months | +0.02 | 11.0 | 6.3 | 0.44 |
| Tax rules | + May loss harvest | +0.08 | 10.7 | 7.3 | 0.45 |
| Concentration | fund share + weight of top 3 | +0.06 | 8.7 | 2.3 | 0.30 |
| Concentration | fund share + 2x top 3 | -0.07 | 6.0 | 0.3 | 0.16 |
| Concentration | 30% fund + 2x top 3 | +0.04 | 7.7 | 1.7 | 0.24 |

- **No structure lever moves the pooled mean by more than about 0.3 point** in the good direction. The mean stays within ±0.3 of zero for every sensible setting with these three signals.
- **Fund share** trades reward for safety. At 0–30% fund, 13–15 of 44 cells are below −2; at 50%, 8; at 70%, 4; at 85%, none, but the design is then ahead in only 5 of 22.
- **Size band:** the 50–100 most-traded names are best. Going down to 200–300 names costs 0.4–0.7 points (wider spreads, more distance from the index).
- **Hold bands:** selling late (hold to rank 75–100) costs 0.6–1.1 points. Momentum decays, and the lower turnover did not pay for itself.
- **Cadence:** monthly is best. Quarterly −0.4, half-yearly −0.8, yearly −1.1.
- **Weighting:** equal weights are as good as any. Inverse-volatility −0.2, traded-value −0.1 to −0.2, score tilt 0.0.
- **Tax rules:** never selling a gain before 12 months adds about +0.1 and removes one or two bad cells. May loss-harvesting adds nothing more.
- **Number of names:** 10, 20 or 30 names, or A$1,250 / A$5,000 positions, all within 0.2.
- **Concentration:** raising the fund share by the weight of the three most-traded names cuts the cells below −2 from 8 to 2 of 44, and also cuts the market-sets ahead from 10 to 9. It is the same trade as a higher fixed fund share.
- **Turnover and cost:** the base design turns over about half the account a year. Costs are not what loses. Random picks held for ever (turnover 0.19) still trail by 1.0 point with a 50% fund and 2.2 points with no fund. The loss is structural: an equal-weighted handful of large companies against a cap-weighted index.

### 2.3 Momentum blends, and the design chosen on data to 2022

"defer" = no gain sale before 12 months; "core.3 / core.7" = 30% / 70% fund; "dyn" = fund share plus the weight of the top three; "B10 H40" = buy the top 10, hold to rank 40.

| Signal / structure | Mean lead | Median | Market-sets ahead of the fund | At +1 or better at both sizes | Cells below −2 | Worst cell | Turnover a year |
|---|---|---|---|---|---|---|---|
| M3: s1+s2+s3 / CSL | +0.76 | +0.36 | 14 of 22 | 7 of 22 | 3 of 44 | -3.6 | 0.53 |
| M3: s1+s2+s3 / defer | +0.79 | +0.42 | 14 of 22 | 7 of 22 | 3 of 44 | -4.0 | 0.47 |
| M3: s1+s2+s3 / core.3 | +0.82 | +0.56 | 11 of 22 | 7 of 22 | 7 of 44 | -4.6 | 0.74 |
| M3: s1+s2+s3 / core.7 | +0.36 | +0.28 | 12 of 22 | 6 of 22 | 2 of 44 | -2.3 | 0.32 |
| M3: s1+s2+s3 / dyn+defer | +0.48 | +0.03 | 12 of 22 | 5 of 22 | 2 of 44 | -2.3 | 0.29 |
| M3: s1+s2+s3 / B10 H40 | +1.03 | +0.95 | 14 of 22 | 9 of 22 | 6 of 44 | -2.6 | 0.57 |
| MS: s2+s3 / CSL | +0.90 | +0.79 | 12 of 22 | 8 of 22 | 2 of 44 | -3.4 | 0.59 |
| MS: s2+s3 / defer | +0.97 | +0.75 | 13 of 22 | 9 of 22 | 2 of 44 | -3.8 | 0.51 |
| MS: s2+s3 / core.3 | +1.19 | +0.94 | 13 of 22 | 10 of 22 | 5 of 44 | -4.2 | 0.82 |
| MS: s2+s3 / core.7 | +0.59 | +0.24 | 12 of 22 | 7 of 22 | 2 of 44 | -2.5 | 0.36 |
| MS: s2+s3 / dyn+defer | +0.59 | -0.09 | 10 of 22 | 7 of 22 | 4 of 44 | -2.6 | 0.31 |
| MS: s2+s3 / B10 H40 | +0.82 | +0.73 | 11 of 22 | 9 of 22 | 5 of 44 | -6.2 | 0.66 |
| 6-month return (s2) / CSL | +0.79 | +0.55 | 12 of 22 | 7 of 22 | 9 of 44 | -6.0 | 0.64 |
| 6-month return (s2) / defer | +0.91 | +0.40 | 12 of 22 | 7 of 22 | 8 of 44 | -5.3 | 0.55 |
| 6-month return (s2) / core.3 | +0.85 | +0.69 | 14 of 22 | 8 of 22 | 10 of 44 | -8.3 | 0.90 |
| 6-month return (s2) / core.7 | +0.53 | +0.28 | 12 of 22 | 6 of 22 | 6 of 44 | -4.3 | 0.39 |
| 6-month return (s2) / dyn+defer | +0.81 | -0.02 | 9 of 22 | 8 of 22 | 2 of 44 | -3.6 | 0.33 |
| 6-month return (s2) / B10 H40 | +0.80 | +0.37 | 10 of 22 | 7 of 22 | 8 of 44 | -4.8 | 0.65 |
| s1+s2 / CSL | +0.68 | +0.25 | 13 of 22 | 6 of 22 | 8 of 44 | -3.6 | 0.52 |
| s1+s2 / defer | +0.63 | +0.51 | 13 of 22 | 6 of 22 | 9 of 44 | -5.2 | 0.45 |
| s1+s2 / core.3 | +0.74 | +0.58 | 12 of 22 | 6 of 22 | 11 of 44 | -4.9 | 0.72 |
| s1+s2 / core.7 | +0.32 | -0.22 | 10 of 22 | 4 of 22 | 3 of 44 | -2.4 | 0.32 |
| s1+s2 / dyn+defer | +0.51 | +0.04 | 11 of 22 | 6 of 22 | 2 of 44 | -2.2 | 0.28 |
| s1+s2 / B10 H40 | +1.05 | +0.69 | 15 of 22 | 7 of 22 | 4 of 44 | -3.2 | 0.54 |
| M3+recency / CSL | +0.33 | +0.31 | 12 of 22 | 7 of 22 | 7 of 44 | -4.7 | 0.50 |
| M3+recency / defer | +0.58 | +0.12 | 11 of 22 | 8 of 22 | 4 of 44 | -4.2 | 0.45 |
| M3+recency / core.3 | +0.50 | +0.16 | 10 of 22 | 9 of 22 | 9 of 44 | -5.0 | 0.71 |
| M3+recency / core.7 | +0.19 | +0.03 | 11 of 22 | 6 of 22 | 1 of 44 | -2.7 | 0.31 |
| M3+recency / dyn+defer | +0.43 | -0.02 | 10 of 22 | 7 of 22 | 3 of 44 | -2.5 | 0.28 |
| M3+recency / B10 H40 | +0.66 | +0.30 | 12 of 22 | 7 of 22 | 3 of 44 | -4.5 | 0.56 |

Chosen on the design windows alone: **MS** = 6-month return + nearness to the 52-week high, 50% fund, 15 best of the 100 most traded, sold after two months below rank 50, no gain sale before 12 months (ahead in 13 of 22, at +1 or better at both sizes in 9 of 22, 2 of 44 cells below −2).

### 2.4 In-pool check, 2023–2026 (indicative only)

| Design | Mean lead | Median | Market-sets ahead of the fund | At +1 or better at both sizes | Cells below −2 | Worst cell | Turnover a year |
|---|---|---|---|---|---|---|---|
| MS (chosen): s2,s3 CSL+defer | +0.70 | +0.37 | 9 of 18 | 7 of 18 | 8 of 36 | -4.2 | 0.54 |
| M3 CSL+defer | +1.68 | +1.73 | 13 of 18 | 11 of 18 | 6 of 36 | -5.5 | 0.50 |
| MS core.3 | +0.84 | +0.51 | 9 of 18 | 6 of 18 | 8 of 36 | -5.2 | 0.74 |
| MS core.7 | +0.47 | -0.04 | 8 of 18 | 5 of 18 | 4 of 36 | -3.1 | 0.33 |
| MS dyn | +0.33 | +0.03 | 9 of 18 | 4 of 18 | 5 of 36 | -3.1 | 0.36 |
| CSL trendq (round 4) | +0.66 | +1.56 | 14 of 18 | 7 of 18 | 6 of 36 | -8.1 | 0.48 |
| hirec CSL+defer | +0.33 | +0.32 | 12 of 18 | 5 of 18 | 5 of 36 | -4.8 | 0.49 |
| H80 CSL+defer | +0.38 | +0.44 | 12 of 18 | 4 of 18 | 4 of 36 | -8.3 | 0.41 |
| rnd1 CSL+defer | -2.00 | -1.75 | 4 of 18 | 1 of 18 | 16 of 36 | -13.9 | 0.62 |
| rnd2 CSL+defer | -1.87 | -2.09 | 3 of 18 | 2 of 18 | 19 of 36 | -9.5 | 0.62 |
| rnd3 CSL+defer | -2.11 | -1.96 | 3 of 18 | 1 of 18 | 18 of 36 | -11.7 | 0.62 |

- MS, fixed on data to 2022, led the fund by **+0.7 points a year** over Dec 2022 – Oct 2026 on average. It was ahead in **9 of 18** market-sets and at +1 or better at both sizes in **7 of 18**, with 8 of 36 cells below −2. Random scores: −2.0.
- Read plainly: an average edge of under 1 point, and a coin toss in any one market.
- The sister blend M3 was level with MS on the design windows and better on the check windows (+1.7, ahead in 13 of 18). Because every pooled set is development, the final design was allowed to use all of it, and M3 was frozen. Its pooled numbers are in-sample.

### 2.5 By market

| Market-set | MS to Dec 2022 (design) | MS 2023–26 (check) | M3 to Dec 2022 | M3 2023–26 | M3 whole window | Random 2023–26 (mean of 3) |
|---|---|---|---|---|---|---|
| ASX 2001–15 | +2.4 / +1.3 | | -0.4 / +1.0 | | | |
| ASX | +3.6 / +1.3 | +2.7 / -0.2 | +6.5 / +2.6 | +1.7 / +0.4 | +3.6 / +1.5 | -1.6 / -1.0 |
| USL 2001–13 | -0.0 / +0.5 | | -0.9 / +1.1 | | | |
| USL | -0.8 / -0.2 | +4.2 / +2.0 | +0.6 / -0.4 | +3.5 / +2.0 | +1.0 / -0.5 | -1.0 / -0.4 |
| USM 2001–13 | +0.3 / -1.6 | | +0.2 / -2.0 | | | |
| USM | -1.2 / -0.8 | +7.5 / +6.7 | -1.1 / -1.0 | +7.5 / +5.9 | +1.1 / +0.0 | -2.1 / +0.5 |
| USS 2001–13 | -1.9 / -0.7 | | -1.7 / -1.9 | | | |
| USS | -0.7 / -1.2 | +4.2 / +4.7 | -1.6 / -2.0 | +5.8 / +6.5 | +0.4 / -0.6 | +0.9 / +1.2 |
| CA | +3.3 / +1.4 | -2.6 / -1.2 | +1.5 / +1.0 | -2.8 / -0.7 | -0.8 / -0.0 | -1.7 / -1.9 |
| UK | +0.0 / -0.4 | +3.4 / +1.1 | +1.5 / -0.5 | +6.3 / +1.5 | +1.4 / +0.0 | -1.3 / -0.6 |
| DE | +1.4 / +0.6 | +3.7 / +1.1 | -0.4 / +0.4 | +4.2 / +2.9 | +2.1 / +1.3 | -1.7 / -1.0 |
| FR | -1.0 / -1.4 | +0.4 / -0.6 | -0.2 / -0.4 | -1.8 / -0.5 | -1.0 / -0.6 | -3.3 / -2.2 |
| SE | +2.1 / +1.4 | -4.2 / -2.9 | +2.2 / +0.7 | -5.5 / -3.1 | -2.5 / -1.7 | -4.1 / -2.6 |
| AS | +0.0 / +0.9 | +1.7 / +3.1 | +0.9 / -0.1 | +5.2 / +3.7 | +2.3 / +0.9 | -1.8 / -3.0 |
| CO | +1.0 / +2.9 | +5.5 / +3.5 | +4.0 / +5.0 | +4.4 / +3.9 | +3.9 / +3.8 | +1.6 / +2.7 |
| JSE | +6.2 / +2.7 | -1.9 / +1.0 | +5.8 / +2.2 | +1.3 / +1.0 | +3.1 / +0.6 | +0.2 / -0.8 |
| KO | -3.0 / -1.6 | +0.1 / +0.4 | -1.6 / -0.8 | +4.5 / +5.6 | -0.1 / +1.6 | -9.4 / -5.8 |
| MC | +4.5 / +3.0 | -3.0 / -2.0 | +4.2 / +3.6 | -2.8 / -1.9 | -0.6 / +0.9 | -3.6 / -3.7 |
| OL | +7.8 / +3.5 | -2.0 / +0.4 | +1.6 / +2.9 | +3.2 / +1.8 | +2.1 / +2.7 | -3.5 / -0.1 |
| SA | +3.1 / +3.8 | -3.2 / -0.3 | +4.0 / +3.8 | +1.7 / +1.0 | +3.1 / +1.8 | -4.5 / -3.3 |
| SW | -3.8 / -1.8 | -0.6 / -1.3 | -4.0 / -2.1 | +1.5 / -1.0 | -3.2 / -2.2 | -2.2 / -1.2 |
| TW | +4.1 / +1.6 | -3.0 / -3.4 | +0.4 / +0.5 | -2.5 / -4.4 | -1.2 / -1.1 | -6.6 / -3.0 |

Markets where M3 was behind over the whole window: Switzerland, Sweden, Taiwan, France, and Canada and Spain at A$25,000. Markets where it was clearly ahead: Denmark, Brazil, ASX, Norway, Germany, Netherlands, South Africa. Nothing seen in the pool separates the two groups in advance.

## 3. New fresh markets: the screen

Every exchange on the data plan not used before was screened on data facts alone, before any engine return. "Liquid names" = median, over Dec 2017 – Oct 2026, of the number of companies with median daily traded value of at least A$250,000-equivalent and a price of at least A$0.50-equivalent. That is the design's own purchase test at A$25,000.

| Exchange | Liquid names | Local index fund on the plan | Dead companies a year, 2018–25 | Verdict |
|---|---|---|---|---|
| **Thailand** | 107 | ThaiDEX SET50 (TDEX): 9 distributions, monthly correlation 0.96 with the 30 most-traded shares | 1.4–5.1% | **valid** |
| **China A-shares** (Shanghai + Shenzhen as one market) | 299 | Huatai-PB CSI 300 (510300): 12 distributions, correlation 0.99 with the CSI 300 index file | 0.2–1.0%, which matches the real number of delistings | **valid, flagged** (see below) |
| Vietnam | 162 | none: the vendor's fund prices start in April 2025 | 0.8–43% | no benchmark |
| Malaysia | 98 | FTSE4Good Bursa Malaysia ETF: closing price unchanged on 49% of days, index changed mid-life, correlation 0.50 | 0.7–10% | stale fund, under 100 names |
| Finland, Poland, Belgium | 57, 57, 56 | usable (Seligson OMXH25; Beta WIG20TR from 2019; Lyxor BEL 20) | present | under 100 names. **Left unopened** for the fundamentals stage |
| Mexico | 46–50 | NAFTRAC | present | under 100 names, and local companies cannot be separated cleanly from foreign and duplicate lines (many lines have no ISIN; ADR and OTC codes of the same Mexican companies are listed again). Not used |
| Greece, Philippines, Chile, Indonesia, Pakistan, Egypt, Romania, Argentina | 29, 27, 20, 19, 18, 9, 5, 0 | Greece: fund has prices on half the days. Philippines, Indonesia, Pakistan, Egypt, Argentina: no local index fund | | not valid |
| Austria, Ireland, Portugal, Czech, Hungary, Peru, Croatia, Sri Lanka, Luxembourg | fewer than 100 companies in the vendor's list (85, 21, 36, 45, 43, 34, 45, 0, 2) | | | not valid, not downloaded |
| Canada Venture, German regional exchanges, Turkey, Israel, Saudi | no index fund / duplicates of XETRA / not on the plan | | | skipped |

Only two markets meet all four tests. A look at two markets is thin, and `PREREG_76.md` said so before the look.

**China flags.** A buyer cannot always buy at the next close (shares locked at the daily price limit; T+1 settlement). Foreign investors reach A-shares only through Stock Connect. Stamp duty on sales is not in the base case. The 100 most-traded Chinese shares are not the largest companies: a traded-value-weighted basket of the top 30 returned 9.7% a year against 1.0% for the CSI 300 fund, before any picking.

**Errors found and fixed before the look** (`PREREG_76.md` §4):

| Error | Size | Direction if left in | Fix |
|---|---|---|---|
| Thailand: 539 depositary receipts of foreign shares (AAPL80, AVGO23 …) and about 600 non-voting (`-R`) and foreign-board (`-F`) lines of the same companies, all typed "Common Stock" | more than half the vendor's list | either; a company counted two or three times | dropped by code rule |
| Thailand, Mexico: 24 and 12 series lost to rate-limit errors in the first download, among them Asset World Corp (a SET50 company) | 1–2% of lines | either | fetched again before the freeze |
| China: 232 unrecorded jumps beyond ×2 or ×0.5 in 1999–2026 (ex-rights after restructurings, resumptions after long halts) | none of the logged events since mid-2017 was in the 300 most traded | either | removed by the round-4 rule |
| Finland: the fund's price already tracks total return (9.3% a year against 9.2% for the 30 most-traded shares with dividends, 5.4% without) and the vendor lists no distributions | fund would pay no dividend tax | against the engine | to be treated as accumulating, with an imputed distribution (stage F) |
| China: a second CSI 300 fund (510310) shows 9.9% a year against 0.9% for 510300 and −0.1% for the index | 9 points a year | for the engine if 510300 were wrong | checked against the index file: 510300 is right, 510310 is a vendor fault and is not used |

## 4. The one look: M3 on Thailand and China

Window 29 Dec 2017 – 30 Oct 2026, four start months. The Thai fund earned 1.0% a year after tax and the Chinese fund 1.7%: two of the weakest index funds in the whole study.

| Design | Market | X after tax 25k | X after tax 100k | X, July-2027 tax design 25k / 100k | X before tax 25k / 100k | Design / fund, % a year after tax (100k) | Range of X over 4 start months (100k) | Random pct 25k / 100k | Top 5 share of profit | Tracking error | t | DSR | Worst fall, design / fund | Turnover | Names 25k / 100k | Owner account, design / fund |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M3* | Thailand | +2.5 | +1.6 | +2.8 / +1.6 | +4.1 / +2.5 | 2.6 / 1.0 | +0.9 to +2.7 | 92 / 94 | 380% | 7.7 | 0.7 | 0.00 | -36 / -33 | 0.40 | 5 / 18 | 62.0k / 67.6k |
| M3* | China | +2.9 | +2.3 | +2.4 / +2.0 | +3.3 / +2.9 | 4.0 / 1.7 | +1.6 to +3.3 | 79 / 79 | 205% | 14.7 | 1.2 | 0.02 | -49 / -38 | 0.46 | 6 / 20 | 58.4k / 58.2k |
| MS | Thailand | -0.6 | +2.1 | -0.6 / +2.0 | -0.7 / +2.9 | 3.1 / 1.0 | +1.2 to +2.8 | 83 / 97 | 200% | 7.6 | 1.1 | 0.01 | -32 / -33 | 0.43 | 4 / 20 | 62.4k / 67.6k |
| MS | China | +4.1 | +2.7 | +3.3 / +2.6 | +3.8 / +3.0 | 4.4 / 1.7 | +2.5 to +3.2 | 49 / 93 | 168% | 14.0 | 1.5 | 0.04 | -47 / -38 | 0.52 | 5 / 21 | 65.0k / 58.2k |
| M3c3 | Thailand | +3.6 | +2.1 | +3.6 / +2.2 | +3.7 / +2.2 | 3.1 / 1.0 | +1.8 to +2.4 | 97 / 100 | 544% | 9.2 | 0.6 | 0.00 | -34 / -33 | 0.53 | 7 / 22 | 56.0k / 67.6k |
| M3c3 | China | +3.0 | +3.9 | +1.7 / +3.3 | +3.9 / +4.3 | 5.5 / 1.7 | +2.8 to +4.4 | 80 / 91 | 131% | 18.1 | 1.5 | 0.03 | -52 / -38 | 0.59 | 8 / 24 | 59.0k / 58.2k |
| M3c7 | Thailand | -0.4 | +1.1 | -0.6 / +1.1 | -0.2 / +1.4 | 2.1 / 1.0 | +0.3 to +1.5 | 77 / 85 | n/a (profit near zero) | 4.8 | 0.3 | 0.00 | -35 / -33 | 0.25 | 4 / 10 | 66.6k / 67.6k |
| M3c7 | China | +2.5 | +0.7 | +1.5 / +0.5 | +2.7 / +1.1 | 2.4 / 1.7 | +0.5 to +1.0 | 54 / 76 | 267% | 10.4 | 1.1 | 0.02 | -46 / -38 | 0.30 | 4 / 12 | 63.9k / 58.2k |
| CSL | Thailand | -0.4 | +1.4 | -0.6 / +1.4 | +0.1 / +1.7 | 2.4 / 1.0 | +1.0 to +1.5 | 74 / 99 | 590% | 7.9 | 0.5 | 0.00 | -36 / -33 | 0.37 | 4 / 16 | 58.3k / 67.6k |
| CSL | China | +1.2 | +0.9 | -0.5 / +0.5 | -0.1 / +1.3 | 2.5 / 1.7 | +0.3 to +1.4 | 49 / 84 | 306% | 13.1 | 1.1 | 0.01 | -46 / -38 | 0.51 | 6 / 20 | 51.4k / 58.2k |
| E3 | Thailand | -0.3 | -1.2 | -0.3 / -1.2 | -0.1 / -0.2 | -0.2 / 1.0 | -3.2 to -0.2 | 54 / 67 | n/a (profit near zero) | 15.0 | -0.4 | 0.00 | -55 / -33 | 0.52 | 6 / 26 | 50.3k / 67.6k |
| E3 | China | -0.9 | -1.6 | -1.7 / -2.7 | -1.7 / -0.7 | 0.1 / 1.7 | -2.8 to -0.6 | 71 / 58 | n/a (profit near zero) | 21.8 | 1.0 | 0.01 | -47 / -38 | 0.69 | 13 / 27 | 42.3k / 58.2k |

M3 = the frozen design. MS = 6-month return + nearness to high. M3c3 / M3c7 = M3 with 30% / 70% in the fund. CSL = report 75 (trend quality). E3 = report 73. Owner account = A$5,000 + A$500 a month, A$57,500 paid in.

\* = the pre-registered design. X = after-tax return of the design minus the fund's, points a year. "Random pct" = percentile of the design's after-tax return among 100 runs of the same structure with random scores. t and DSR are for the monthly lead before tax, December start.

| Bar (all required) | Thailand | China | Met? |
|---|---|---|---|
| X ≥ +1.0 at both A$25,000 and A$100,000, in both markets | +2.5 / +1.6 | +2.9 / +2.3 | **yes** |
| X below −2.0 in no more than one market | none | none | **yes** |
| At or above the 90th percentile of random-score runs at both sizes, in both markets | 92 / 94 | 79 / 79 | **no** (one of two) |
| Top five positions under 50% of profit (A$100,000), in both markets | 380% | 205% | **no** |
| Deflated Sharpe ratio at N ≈ 1,450 (reported; usual line 0.95) | 0.00 | 0.02 | far below |
| **Verdict** | | | **not adopted** |

What the numbers say:

1. **M3 beat the local fund after costs and tax in both fresh markets at both sizes.** No earlier design did that in every market of a look (20 market tests in rounds 1–4; best was one of three).
2. **It is not distinguishable from luck.** The t-statistics of the monthly lead are 0.7 (Thailand) and 1.2 (China). In China, 21 of 100 random-score portfolios did better. With 1,450 trials behind it, the deflated Sharpe ratio is zero.
3. **The profit rests on a handful of names.** In Thailand the five best positions (Delta Electronics, JMT, Jaymart, Krungthai Bank, Com7) made A$32,000 between them and all 145 positions together made A$8,400. In China the five best made A$45,000 of A$21,900.
4. **The lead came in bursts.** Thailand: +16 and +24 points in 2020 and 2021, then behind the fund in 2022, 2023, 2024 and 2025. China: +23 and +20 in 2019 and 2020, −8 and −6 in 2022 and 2023, +10 and +14 in 2025 and 2026.
5. **The owner's account did not win.** A$5,000 plus A$500 a month (A$57,500 paid in) ended at A$62,000 against A$67,600 for the fund in Thailand, and A$58,400 against A$58,200 in China. The account only reaches A$25,000 around 2021, after the good years.
6. **At A$25,000 the result is fragile.** With five or six names, raising costs by half changed the China result from +2.6 to −1.8 points against the fund, only because a different share was bought on one date. At A$100,000 (18–20 names) the same stress moved it by 0.1–0.2.
7. **Risk was higher.** Worst fall −36% against −33% for the fund in Thailand, −49% against −38% in China. Tracking error 8 and 15 points a year.
8. **The other designs.** Report 75's CSL (trend quality) scored −0.4 / +1.4 and +1.2 / +0.9, short of the bar on its own. E3 (report 73) was behind the fund in both. A 30% fund share scored higher (+3.6 / +2.1 and +3.0 / +3.9) and a 70% share lower, as the pool predicted. The signal sorted shares in Thailand (t = 1.7 for M3, 2.3 for recency) and barely in China (0.8).

## 5. What came closest, all rounds

| Rank | Design | Fresh markets it was eligible in | Markets at +1 or better at both sizes | Cells below −2 | Mean lead on those markets |
|---|---|---|---|---|---|
| 1 | **M3** (round 5): 50% fund + 15 momentum names of the 100 most traded | Thailand, China | **2 of 2** | 0 of 4 | +2.3 |
| 2 | CSL (round 4): same structure, trend-quality score | Denmark, Spain, Switzerland (+ Thailand, China descriptive) | 1 of 3 (0 of 2) | 3 of 6 (0 of 4) | −0.5 (+0.8) |
| 3 | EI (round 4): enhanced index on a traded-value proxy | Netherlands, Korea, Brazil | 1 of 3 | 2 of 6 | −0.9 |
| 4 | E3 (round 3): 30 trend names of 300, no fund | US large, mid, small 2014–26 (+ 11 later markets descriptive) | 1 of 3 | 2 of 6 | −0.6 |
| 5 | E1 / E2 (rounds 1–2) | eight markets | 0 of 8 | most | negative |

The index fund is still rank 0. M3 is the first design that would have to be watched rather than dismissed.

## 6. M3 rules (zero ambiguity) and forward snapshots

M3 is **not adopted**. The rules are written out so that it can be tracked on paper beside H82 and E3 if the owner wants a forward record of it. That costs nothing and is the only way to add evidence that is not a backtest.

**M3 v1.0 (ASX version), all times Sydney.**

- **R1 Decision day.** The last ASX trading day of each calendar month, after the close. Orders are placed for the next trading day's closing auction. Nothing is done on any other day.
- **R2 Fund core.** 50% of the account's value is held in one ASX-listed broad Australian index fund (the same fund the paper record already uses as benchmark). If the fund is below 50% of the account on a decision day, free cash goes to the fund first, in orders of A$1,000 or more. The fund is never sold while the account is A$25,000 or more.
- **R3 Small account.** While the account is below A$25,000 on a decision day and no shares are held, everything is in the fund. On the first decision day at or above A$25,000 the fund is sold down to 50% and R4–R8 start.
- **R4 Universe.** Ordinary shares (no ETFs, LICs, warrants, options, stapled debt) with at least 200 closes in the last 252 trading days, ranked by the median over those 252 days of daily traded value (close × volume, both unadjusted). The top 100 are the universe. Ties go to the lower ASX code in alphabetical order.
- **R5 Score.** For each universe company, with split- and dividend-adjusted closes: s1 = close 21 trading days ago ÷ close 252 trading days ago − 1; s2 = last close ÷ close 126 trading days ago − 1; s3 = last close ÷ highest close of the last 252 trading days. A close "N days ago" is the most recent close on or before that day, at most 10 trading days stale; otherwise the score is missing and the company is unranked. Each of s1, s2, s3 is converted to its percentile among universe companies with that value (average rank ÷ count). Score = mean of the three percentiles. Rank 1 = highest score; ties go to the company with the higher traded-value rank.
- **R6 Positions.** Satellite = account value − fund value. n = min(30, max(4, floor(satellite ÷ 2,500))). Target per name = satellite ÷ n.
- **R7 Sell.** (a) A holding whose rank is worse than 50, or that has no rank or has left the 150 most traded, on two decision days in a row is sold, unless it shows a gain and its first parcel is less than 366 days old; in that case it is re-tested on each later decision day and sold on the first one on which it is 366 days old and still ranked worse than 50. (b) On the May decision day, a holding ranked worse than 50 on that day alone and showing a loss is sold. (c) A holding worth more than the larger of 15% of the satellite and twice its target is cut back to the larger of 10% of the satellite and 4/3 of its target, selling parcels held more than 12 months first, highest cost first.
- **R8 Buy.** After sales, while fewer than n names are held: buy the best-ranked company with rank ≤ 15 that is not held, traded on the decision day, closed at A$0.50 or more, and has median daily traded value of at least 100 × the target. Order size = the target, or the free cash if smaller, and at least the larger of A$1,000 and half the target; otherwise stop. Then top up any holding ranked 50 or better that is under 75% of its target, if the top-up is A$1,000 or more, smallest percentage of target first.
- **R9 Cash for tax.** Free cash = cash minus the tax already owed on the year's realised gains and dividends at 32%.
- **R10 Corporate actions.** Takeover or delisting: proceeds are taken as cash on the first decision day at least 20 trading days after the last close. Code changes carry the holding. Demerged shares are held and ranked like any holding.
- **R11 No discretion.** No overrides, no stops, no news.

**Forward-snapshot procedure.**
1. On each month-end decision day (and on the mid-month day the paper record already uses), build the ASX pack from the daily end-of-day file: `python3 code/mk_asx5.py eod M`.
2. `python3 code/snapshot_m3.py data/pack_ASXeod_M.npz <folder>` writes `forward_M3_snapshot_<date>.csv`: every universe company with its M3 rank, score, s1, s2, s3, traded-value rank, median traded value, close, and flags for the buy zone (rank ≤ 15), hold zone (≤ 50), price and liquidity tests. It computes no return.
3. Hash the CSV (SHA-256) on the day and store the hash with the record, as for H82 and E3.
4. Paper portfolio: apply R1–R11 to the snapshot ranks with the next day's closes.

Two snapshots were written to `improve5/out/` only: `forward_M3_snapshot_2026-10-30.csv` and `forward_M3_snapshot_2026-11-13.csv`. Rank 1–15 on 13 Nov 2026: RHC, WOW, JHX, CPU, ALL, CSL, CWY, SOL, QBE, TWE, AMP, PRU, BSL, STO, ASX. Nothing was written to `68_forward_record/` or `bigwins_forward/`; adding M3 there is the owner's call.

## 7. Against the 40/60 plan

Nothing changes. M3 did not meet the bar, and even its two good fresh results (2.6% and 4.0% a year after tax at A$100,000) are far below what the plan's index funds earned over the same years in Australia and the US. Real money stays in the plan.

## 8. Fundamentals: what the data are, what was tested today, and the plan for the paid month

The owner subscribed to EODHD fundamentals during this round. The endpoint was confirmed live, 2,407 company files were downloaded under a throttle (280 calls a minute), and a first pre-registered test was run. Every raw response is kept (section 11).

### 8.1 What EODHD fundamentals provide (a)

| Question | Finding |
|---|---|
| Fields | One file per company (about 0.7 MB): balance sheet, income statement and cash flow, each **yearly and quarterly**, 30–60 items a row, back to 1985–1995 for old companies. Also shares outstanding by year and quarter, an earnings history with report dates and EPS, sector and industry, and current-only valuation ratios (not point-in-time; not used) |
| Publication dates | `filing_date` equals the period end in most rows (ASX: 6,223 of 6,694 annual rows; UK: 4,540 of 4,667). It is **not** a publication date. `Earnings.History.reportDate` is a real announcement date where present (7,585 dates in 296 ASX files; for ASX annual results the median is 53 days after period end and none of 2,414 is later than 122 days) |
| Restatements | One value per period, with no vintage. Restated figures cannot be told from original ones |
| Dead companies | A file comes back for almost every symbol asked (2,404 of 2,407), but the statements inside are often empty for companies that left before about 2018 |
| Share counts | Within 30% of the current count in 86–96% of live files; wrong by a factor of 3 or more in 1–7% (Amaero shows 13.9 bn shares against about 0.6 bn real) |
| Currency | 5–46% of files report in a currency other than the quote currency (Canada 46%, UK 36%, ASX 18%). Ratios inside the statements are unaffected; price-based ratios need exchange rates |
| Markets | Answered for every exchange tried: ASX, London, XETRA, Paris, Stockholm, Amsterdam, Swiss, Toronto, Helsinki, Warsaw, Brussels |

Share of the 100 most-traded companies with a usable quality score (all companies / companies that later left the file):

| Market | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 |
|---|---|---|---|---|---|---|
| ASX | 88 / 56% | 97 / 93% | 98 / 96% | 99 / 92% | 98 / 77% | 99 / 65% |
| UK | 36 / 7% | 37 / 6% | 47 / 18% | 90 / 70% | 96 / 90% | 94 / 99% |
| Germany | 94 / 72% | 99 / 100% | 99 / 97% | 100 / 98% | 100 / 100% | 100 / 100% |
| France | 86 / 38% | 92 / 59% | 96 / 73% | 100 / 100% | 100 / 100% | 100 / 100% |
| Sweden | 93 / 75% | 97 / 93% | 100 / 100% | 100 / 97% | 100 / 100% | 100 / 100% |
| Netherlands | 75 / 48% | 88 / 74% | 97 / 92% | 97 / 92% | 98 / 92% | 97 / 78% |
| Switzerland | 95 / 67% | 98 / 80% | 100 / 95% | 100 / 100% | 99 / 86% | 100 / 100% |
| Canada | 74 / 40% | 78 / 47% | 93 / 81% | 99 / 100% | 99 / 99% | 99 / 100% |
| Finland | 92 / 80% | 95 / 92% | 97 / 96% | 96 / 93% | 98 / 90% | 100 / 85% |
| Poland | 79 / 18% | 84 / 43% | 91 / 65% | 98 / 93% | 100 / 100% | 100 / 100% |
| Belgium | 84 / 52% | 90 / 66% | 91 / 68% | 97 / 90% | 100 / 100% | 100 / 100% |

Usable from 2018 in most markets and from 2020 in the UK. Before that, dead companies are missing, and any test would be biased towards survivors.

### 8.2 Lookahead safeguards used (c)

1. **Annual statements only**, usable 122 days (four months) after the period end, or on the vendor's report date if that is later. ASX rules require the preliminary final report within two months and the annual report within three; the EU and UK require the annual report within four months; Canada 90 days. Four months is at or beyond every deadline.
2. A fiscal year expires 610 days after its period end if nothing newer has arrived.
3. Only figures in the file as stored; restatements cannot be removed and this is a stated weakness.
4. Scores are percentiles among the 100 most traded on the decision date.
5. A company with no usable figure cannot be bought by a fundamentals design. Because the missing files are mostly dead companies, each fundamentals design is compared with **M3 on the same covered names** (M3cov), not with plain M3.
6. Price-based value ratios use the statement share count times the price at period end, rolled forward with the price, and only where statement and quote currency match.

### 8.3 Development: quality, value and issuance added to M3 (eight markets)

Structure fixed at M3's. Lead over the local fund, points a year after tax, mean of both sizes; "ahead" = markets ahead of the fund. Budget of 12 configurations for the quality family, then 6 declared extras for value and issuance (`out/devF_D.log`, `devF_all.log`, `devF2.log`).

| Score added to M3 | To Dec 2022: mean / ahead | Dec 2022 – Oct 2026: mean / ahead |
|---|---|---|
| nothing (M3 on covered names) | +0.54 / 5 of 8 | +0.73 / 5 of 8 |
| Quality (gross profitability, return on equity, low accruals, low leverage) | +0.10 / 3 | **−2.11 / 1** |
| Profitability (gross profit ÷ assets, return on equity) | +0.03 / 3 | −1.72 / 1 |
| Gross profitability alone | +0.50 / 5 | −1.90 / 1 |
| Low accruals + low leverage (picked on the first window) | +0.81 / 6 | **−1.59 / 2** |
| M3 only among the top 60% by quality | +0.60 / 6 | −1.72 / 1 |
| Value (earnings yield, book-to-price) | **−1.61 / 1** | +1.04 / 5 |
| Cash-flow yield | −1.16 / 2 | +0.99 / 6 |
| **Low share issuance** | +0.54 / 5 | **+1.27 / 7** |
| Quality alone, no M3 | +0.10 / 4 | −2.06 / 0 |
| Value alone, no M3 | −1.73 / 1 | +0.16 / 4 |

- **Quality did not add to momentum, and in 2023–26 it cost 2 to 3 points a year.** The market leaders of those years in Europe and Canada were banks, insurers and defence companies, which score badly on leverage and gross profitability. ASX was the only market where the quality blends stayed ahead of the fund in 2023–26, and before 2022 they were behind plain M3 there too.
- **Value did the opposite:** −2 points to 2022, about level after.
- Quality and value each "worked" in one window and failed in the other. A design tuned on either window would have been wrong in the next.
- **Low share issuance** was the only score that did not hurt in either window (level, then +0.5).

### 8.4 One look at three held-out markets (`PREREG_76F.md`, frozen at N = 1,501)

Design: **M3I** = M3 with the score averaged with a low-issuance percentile. Markets: Finland, Poland, Belgium (no return of any kind had been computed on them; 56–57 liquid names each, below the 100-name line, which the pre-registration flagged).

| Design | Market | X after tax 25k | X after tax 100k | X, July-2027 tax design 25k / 100k | X before tax 25k / 100k | Design / fund, % a year after tax (100k) | Range of X over 4 start months (100k) | Random pct 25k / 100k | Top 5 share of profit | Tracking error | t | DSR | Worst fall, design / fund | Turnover | Names 25k / 100k | Owner account, design / fund |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M3I* | Finland | +1.2 | +0.3 | +0.9 / +0.0 | +1.8 / +0.5 | 7.7 / 7.4 | -0.3 to +1.1 | 99 / 100 | 76% | 3.4 | -0.2 | 0.00 | -22 / -21 | 0.27 | 6 / 20 | 89.6k / 85.7k |
| M3I* | Poland | +7.3 | +1.6 | +5.8 / +1.3 | +8.1 / +2.6 | 11.5 / 9.9 | +1.3 to +2.1 | 88 / 31 | 45% | 6.2 | 0.5 | 0.00 | -40 / -41 | 0.37 | 7 / 17 | 99.3k / 99.6k |
| M3I* | Belgium | +2.0 | +1.9 | +1.6 / +1.4 | +2.1 / +2.4 | 7.7 / 5.8 | +1.9 to +1.9 | 93 / 100 | 87% | 4.1 | 1.7 | 0.04 | -24 / -27 | 0.24 | 6 / 17 | 83.9k / 84.4k |
| M3cov | Finland | +0.2 | +0.2 | -0.1 / -0.3 | +0.7 / +0.4 | 7.6 / 7.4 | -0.3 to +0.7 | 95 / 100 | 71% | 4.3 | -0.1 | 0.00 | -28 / -21 | 0.33 | 6 / 20 | 82.1k / 85.7k |
| M3cov | Poland | +2.1 | +2.3 | +0.7 / +2.0 | +3.7 / +2.5 | 12.1 / 9.9 | +2.1 to +2.6 | 17 / 60 | 52% | 7.8 | 0.6 | 0.00 | -42 / -41 | 0.41 | 4 / 17 | 107.3k / 99.6k |
| M3cov | Belgium | +1.7 | +2.0 | +0.8 / +1.4 | +2.6 / +2.5 | 7.8 / 5.8 | +1.7 to +2.4 | 94 / 100 | 80% | 5.4 | 1.2 | 0.02 | -21 / -27 | 0.34 | 6 / 18 | 88.5k / 84.4k |
| M3 | Finland | -0.8 | +0.1 | -0.8 / -0.3 | +0.7 / +0.3 | 7.5 / 7.4 | -0.5 to +0.6 | 57 / 100 | 67% | 4.5 | -0.3 | 0.00 | -28 / -21 | 0.34 | 7 / 20 | 82.7k / 85.7k |
| M3 | Poland | +1.6 | +2.3 | +0.7 / +1.9 | +2.9 / +3.0 | 12.2 / 9.9 | +1.9 to +2.6 | 24 / 66 | 51% | 7.8 | 0.7 | 0.00 | -41 / -41 | 0.41 | 4 / 17 | 107.3k / 99.6k |
| M3 | Belgium | +0.3 | +1.6 | +0.2 / +1.1 | +1.7 / +2.1 | 7.4 / 5.8 | +1.3 to +1.8 | 66 / 100 | 84% | 5.1 | 1.2 | 0.01 | -20 / -27 | 0.35 | 5 / 18 | 88.5k / 84.4k |
| M3S | Finland | -2.4 | -1.1 | -3.0 / -1.4 | -2.6 / -1.0 | 6.3 / 7.4 | -1.2 to -1.0 | 84 / 90 | 164% | 4.6 | -0.7 | 0.00 | -25 / -21 | 0.26 | 6 / 19 | 71.2k / 85.7k |
| M3S | Poland | +0.0 | +0.6 | -0.6 / +0.3 | -0.4 / +0.8 | 10.5 / 9.9 | +0.2 to +0.9 | 37 / 24 | 72% | 9.3 | -0.0 | 0.00 | -31 / -41 | 0.27 | 4 / 19 | 81.8k / 99.6k |
| M3S | Belgium | +4.8 | +2.3 | +4.0 / +1.7 | +6.2 / +2.8 | 8.1 / 5.8 | +2.1 to +2.7 | 100 / 100 | 61% | 4.7 | 1.7 | 0.04 | -21 / -27 | 0.24 | 7 / 17 | 93.6k / 84.4k |
| M3Q | Finland | -1.3 | -0.3 | -1.4 / -0.6 | -0.5 / -0.2 | 7.1 / 7.4 | -0.7 to +0.2 | 89 / 97 | 114% | 5.1 | -0.5 | 0.00 | -29 / -21 | 0.19 | 6 / 18 | 81.8k / 85.7k |
| M3Q | Poland | +1.0 | +0.9 | +1.2 / +0.7 | +2.8 / +1.2 | 10.8 / 9.9 | +0.7 to +1.3 | 27 / 31 | 67% | 8.6 | 0.3 | 0.00 | -34 / -41 | 0.22 | 5 / 16 | 91.7k / 99.6k |
| M3Q | Belgium | -0.8 | +0.7 | -1.4 / +0.3 | -0.3 / +1.0 | 6.4 / 5.8 | +0.5 to +0.8 | 14 / 100 | 100% | 4.5 | 0.6 | 0.00 | -24 / -27 | 0.22 | 4 / 17 | 77.3k / 84.4k |
| M3V | Finland | -2.3 | -1.9 | -2.2 / -1.9 | -2.4 / -2.1 | 5.5 / 7.4 | -2.1 to -1.7 | 59 / 55 | 1813% | 3.4 | -1.8 | 0.00 | -25 / -21 | 0.16 | 4 / 19 | 72.9k / 85.7k |
| M3V | Poland | +1.2 | +1.3 | +1.0 / +1.0 | +2.2 / +1.8 | 11.2 / 9.9 | +1.0 to +1.5 | 50 / 25 | 65% | 5.2 | 0.5 | 0.00 | -37 / -41 | 0.22 | 5 / 15 | 84.8k / 99.6k |
| M3V | Belgium | +2.2 | +0.1 | +1.7 / +0.0 | +3.6 / +0.4 | 5.9 / 5.8 | -0.7 to +0.6 | 82 / 100 | 73% | 4.1 | 0.7 | 0.00 | -23 / -27 | 0.18 | 6 / 18 | 81.7k / 84.4k |

M3I = the frozen fundamentals design. M3cov = M3 on companies with accounts. M3S = M3 + low accruals and leverage. M3Q = M3 + quality. M3V = M3 + value. Owner account: A$57,500 paid in (Poland A$51,000, shorter window).

| Question | Finland | Poland | Belgium | Answer |
|---|---|---|---|---|
| A1. X ≥ +1.0 at both sizes in two of three | +1.2 / +0.3 | +7.3 / +1.6 | +2.0 / +1.9 | yes (2 of 3) |
| A2. Below −2.0 in at most one market | none | none | none | yes |
| A3. ≥ 90th percentile of random runs at both sizes in two of three | 99 / 100 | 88 / 31 | 93 / 100 | yes (2 of 3) |
| A4. Top five positions under 50% of profit in two of three | 76% | 45% | 87% | **no** (1 of 3) |
| A5. Deflated Sharpe at N ≈ 1,500 | 0.00 | 0.00 | 0.04 | far below 0.95 |
| **A. Adoption bar** | | | | **not met** (A4, A5) |
| B. M3I minus M3cov positive at both sizes in two of three | +1.0 / +0.1 | +5.2 / −0.6 | +0.3 / −0.1 | **no** (1 of 3) |

- **Fundamentals did not clearly add.** M3I beat M3 on the same names at both sizes only in Finland. The average gain of +1.0 is one cell (Poland at A$25,000, seven names).
- The quality design the first budget had picked (M3S) scored −2.4 / −1.1 in Finland, 0.0 / +0.6 in Poland and +4.8 / +2.3 in Belgium; quality (M3Q) was behind plain M3 in all three markets and value (M3V) in two. The fresh markets agree with the development result.
- **Plain M3 on these three markets** (descriptive; M3 had been frozen before they were opened): Finland −0.8 / +0.1, Poland +1.6 / +2.3, Belgium +0.3 / +1.6. On the names with accounts: +0.2 / +0.2, +2.1 / +2.3, +1.7 / +2.0.
- In Poland the design sat at the 31st percentile of random portfolios at A$100,000: random share-picks beat the WIG20 fund there, so the lead is the market's, not the signal's.
- The owner's account: Finland A$89,600 against A$85,700 for the fund; Poland A$99,300 against A$99,600; Belgium A$83,900 against A$84,400.

### 8.5 M3 across all five fresh markets of this round

| | Thailand | China | Finland | Poland | Belgium | Mean | At +1 or better at both sizes | Cells below −2 |
|---|---|---|---|---|---|---|---|---|
| M3, A$25k / A$100k | +2.5 / +1.6 | +2.9 / +2.3 | −0.8 / +0.1 | +1.6 / +2.3 | +0.3 / +1.6 | +1.4 | 3 of 5 | 0 of 10 |
| Random-score percentile | 92 / 94 | 79 / 79 | 57 / 100 | 24 / 66 | 66 / 100 | | | |
| Local fund after tax, % a year | 1.0 | 1.7 | 7.4 | 9.9 | 5.8 | | | |

M3 was ahead of the fund at A$100,000 in all five and at A$25,000 in four. That is a better record than any design in rounds 1–4. It is still five markets over the same nine years, all of them markets whose index fund did poorly, and the percentile row shows that in most of them a random portfolio of the same shape often did as well.

### 8.6 Plan for the paid month (b, d)

**What is left for an honest look (d).**

| Held-out set | Why it is clean | Size |
|---|---|---|
| Ten market-sets whose fundamentals have never been downloaded: US large, mid and small, Korea, Taiwan, Thailand, China, Brazil, Denmark, Spain, Norway, South Africa | Their prices are development data, but no fundamentals score has ever been computed on them. A fundamentals design frozen on today's eight development markets has never seen them | about 4,350 company files = 43,500 calls, under one day's quota with the 15,000 reserve, about 2.6 hours at 280 calls a minute |
| Forward months from December 2026 | Nothing has seen them | the paper record |
| Fresh exchanges | None left with 100 liquid names and a usable index fund. Finland, Poland and Belgium are now spent. Vietnam (no fund history), Malaysia (stale fund) and Mexico (unclean file) could be used only as weak, flagged extras |  |

**What to test (b), pre-registered, with a budget of five configurations on the eight development markets and then ONE look.**

| # | Score added to M3 (equal blend of percentiles unless stated) | Definition from annual statements |
|---|---|---|
| 1 | **Low issuance** (today's candidate; the look in 8.4 neither confirmed nor rejected it) | ln(shares at latest fiscal year end ÷ shares a year earlier); splits removed with the price file's split factors instead of today's ±50% filter |
| 2 | Net payout yield | (dividends paid + net share repurchases) ÷ market value |
| 3 | Gross profitability, sector-neutral | gross profit ÷ total assets, percentile inside the company's sector, so that banks are not ranked against retailers |
| 4 | Earnings yield with currency conversion | net income ÷ market value, statements converted at the period-end exchange rate (fixes the 5–46% of files dropped today) |
| 5 | "Avoid junk" screen | M3 unchanged, but never buy a company in the worst fifth on a mean of: loss-making, issuance, accruals, leverage |

Return on equity, accruals and leverage as direct blends are **dropped**: they failed in development and in the fresh look. Book-to-price is dropped as a stand-alone (it is the weakest value measure where intangibles dominate).

**Rules for that look:** the safeguards of 8.2 unchanged; comparison always against M3 on the same covered names; windows from Dec 2019 (so that dead-company coverage is above 90% everywhere); the bar of `PREREG_76.md` plus question B of 8.4; expected increment stated in advance (today's estimate: 0 to +0.5 point). Trial count continues from 1,543.

**Is the subscription worth it?** For beating the index: on today's evidence, probably not. Quality and value did not add to momentum across eight markets and three fresh ones. For other uses it is worth one month: (i) the ten-market look above settles the issuance question cheaply; (ii) real share counts give point-in-time market value, which allows a true cap-weighted reference book for the first time (report 75's enhanced-index test failed for lack of it); (iii) the raw files are now kept, so nothing needs to be bought twice.

## 9. Caveats and reasons this could be wrong

- **Two valid markets.** The main look had two markets. The bar's "majority" then means both, and one bad draw fails it. The same thinness means the two passes on return are weak evidence.
- **Weak index funds.** All five fresh markets had index funds that earned 1–10% a year. In the pool M3 was behind where a few giant companies drove the index (Taiwan, Switzerland, US large). The owner's real benchmarks are ASX and US funds; M3's record there is in-sample (ASX +3.6 / +1.5, US large +1.0 / −0.5 over the whole window).
- **China is not investable as modelled** (price limits, T+1, Stock Connect, stamp duty).
- **M3 was chosen with the whole pool in view,** including the check windows. Its pooled record is in-sample; only the five fresh markets count.
- **Selection.** 346 counted trials this round on top of 1,197. Deflated Sharpe ratios are at or near zero everywhere.
- **Small accounts.** At A$25,000 the book holds five to seven names and single purchases decide the result (China: +2.6 or −1.8 depending on one fill).
- **Thailand:** foreign investors usually hold non-voting depositary receipts (`-R`), which trade at the same price; the test used the ordinary line. **Poland:** the fund starts in January 2019. **Finland:** the fund is treated as accumulating on the evidence of its price path.
- **Fundamentals:** restated values cannot be excluded; coverage of dead companies is 65–96% in 2018 in the held-out markets; share counts are wrong in a few per cent of files.
- **Start dates** now follow each market's calendar; old designs' pooled figures differ slightly from report 75.
- **Local taxes, currency and franking** are not modelled outside Australia. Tax is the owner's Australian schedule applied to local returns.
- **Mexico** was listed as held-out in `PREREG_76.md` and dropped afterwards, before any return, because its file could not be cleaned by rule. One Canadian fundamentals file arrived after the development runs; they were not re-run.

## 10. What is left that could change the answer

1. **Time.** A forward paper record of M3 on ASX, beside H82 and E3. Twelve months of it will say more than another backtest.
2. **The ten-market fundamentals look** (8.6), for low issuance and net payout only.
3. **A true cap-weighted direct index** using the share counts that now come with the fundamentals subscription. This is the untested idea from report 75 and is now testable outside Australia.
4. **Nothing else on this data plan.** Every exchange with 100 liquid names and a usable local fund has now been used.

## 11. Files

| What | Where (under `scratchpad/improve5/`) |
|---|---|
| Pre-registrations and hashes | `PREREG_76.md`, `PREREG_76F.md`, `out/prereg76_hash.txt`, `out/prereg76F_hash.txt` |
| Trial ledger (1,198 → 1,543) | `out/trials_76.csv` |
| Progress log | `PROGRESS.md` |
| Development logs and tables | `out/dev1.log` … `dev5.log`, `out/dev_tables.md`, `out/res_*.json`, `out/devF_D.log`, `out/devF_all.log`, `out/devF2.log` |
| Looks | `out/look_*_{BK,CN}.json`, `out/lookf_*_{HE,WAR,BR}.json`, `out/summary_table.md`, `out/summary_table_F.md` |
| Data checks | `out/qa2.log`, `out/mk_*.log`, `out/coverage_*.csv`, `out/covF_dev.log`, `out/covF_held.log` |
| M3 snapshots (ASX) | `out/forward_M3_snapshot_2026-10-30.csv`, `out/forward_M3_snapshot_2026-11-13.csv` |
| Raw price downloads (kept) | `data/raw/<EXCHANGE>.pkl` + `_meta.csv` for 17 exchanges; index-fund files in `data/etf/` |
| Raw fundamentals (kept, gzip JSON, one file per symbol) | `data/fundamentals_raw/<EXCHANGE>/<SYMBOL>.<EXCHANGE>.json.gz`; index `data/fundamentals_raw/index.csv` (symbol, time, bytes); compact parse `data/fund/<EXCHANGE>.pkl` |
| Code | `code/sim5.py`, `lib5.py`, `pool5.py`, `look5.py`, `mk_fresh5.py`, `qa5.py`, `dlf.py`, `fbuild.py`, `fscores.py`, `snapshot_m3.py` |

API use this round: about 44,000 calls (price series 19,700; fundamentals 24,100; lists, funds and checks about 300). 51,697 of the day's 100,000 were used at 05:40 UTC on 17 Nov. The first price downloads ran above the per-minute limit and caused "Too Many Requests" for about ten minutes; everything since has run at 280 calls a minute.
