# 45 — Independent replication of report 36 (real-data backtests of rule L1)

Date: 2026-11-13. Subject: `research2/36_real_data_backtests.md` and `backtest_study/`.
Method: blind re-implementation. The rule, data sources and metrics were taken from a written brief only. Report 36, its code and its outputs were not opened until my own results were written to disk and copied to a frozen folder (`replication_36/out_frozen_before_step3/`, `results.json` SHA-256 `555e035a…a61577d`). Everything after that point is labelled "step 3" below.

## 1. Verdict

**Report 36 replicates.** No headline is NOT REPLICATED. No coding error was found in the original that changes a number by more than 0.03 points.

- My engine, fed the original's inputs and parameters, reproduces the unit-price headline table to within 0.03 points of CAGR and 0.1 point of drawdown, and reproduces the dollar-engine H1 figures to the rounding shown (19.2% / 39.5% / 28.9% / 27.5%, p = 0.067 and 0.185 against the report's 0.066 and 0.184).
- I rebuilt the original's two sleeve series, cash series and FX series from raw downloads with my own parser. All four match the original's `panel.csv` to the last printed digit (maximum absolute monthly difference 0.000000 over 588 months).
- My fully independent run (my own pre-1990 global blend, the brief's parameters) differs from the report by 0.36–0.47 points of CAGR on 1976–2023. All of it is explained by four documented choices (section 4). On 1990–2023 every figure is within tolerance.

| Headline in report 36 | Report 36 | My independent run | On the original's inputs, my engine | Class |
|---|---|---|---|---|
| L1 CAGR 1976–2023, cash at RBA rate | 11.87% | 12.30% | 11.84% | CLOSE (explained) |
| L1 CAGR 1976–2023, cash at 0 | 10.55% | 11.02% | 10.53% | CLOSE (explained) |
| Static 40/60 CAGR 1976–2023 | 11.84% | 12.20% | 11.81% | CLOSE (explained) |
| L1 − B2 CAGR 1976–2023, cash RBA / cash 0 | +0.02 / −1.29 pp | +0.10 / −1.18 pp | +0.03 / −1.28 pp | REPLICATED |
| Volatility L1 RBA / L1 0 / B2 | 11.1 / 11.2 / 12.9% | 11.2 / 11.3 / 12.9% | 11.1 / 11.2 / 12.9% | REPLICATED |
| Sharpe L1 RBA / L1 0 / B2 | 0.45 / 0.34 / 0.41 | 0.48 / 0.38 / 0.43 | 0.45 / 0.34 / 0.40 | CLOSE (explained; follows from CAGR) |
| Max drawdown 1976–2023, L1 RBA / L1 0 / B2 | 25.8 / 28.3 / 39.7% | 27.2 / 29.1 / 39.8% | 25.8 / 28.4 / 39.8% | REPLICATED (within 2 pp) |
| Ulcer L1 RBA / L1 0 / B2 | 6.7 / 8.8 / 11.1% | 6.4 / 8.5 / 10.9% | 6.7 / 8.9 / 11.2% | REPLICATED |
| Switches a year | 1.52 | 1.35 | 1.52 | CLOSE (explained: pre-1990 global series) |
| Time invested | 82.7% | 83.0% | 82.7% | REPLICATED |
| 1990–2023: L1 RBA / L1 0 / B2 CAGR | 8.71 / 7.60 / 8.39% | 8.81 / 7.76 / 8.64% | 8.69 / 7.58 / 8.37% | REPLICATED |
| **H1, 1990–2023, cash 0: max DD 19.2% against 39.5% (51%)** | 19.2 / 39.5% | 19.6 / 39.8% (50.8%) | 19.2 / 39.5% (51.3%) | **REPLICATED** |
| H1 p-value 1990–2023 | 0.066 | 0.080 | 0.067 | REPLICATED |
| **H1, 1976–2023, cash 0: 27% reduction** (28.9 / 39.5%) | 27% | 26.7% (29.1 / 39.8%) | 27.0% (28.85 / 39.53%) | **REPLICATED, but fragile** (see 5.2) |
| H1 p-value 1976–2023 | 0.184 | 0.231 | 0.185 | REPLICATED (not below 0.10 in any run) |
| Crash table, 2000–02 and 2008–09 rows | −33.8 → −3.7%; −39.7 → −2.7% | −33.0 → −3.3%; −39.7 → −2.4% | −33.8 → −3.8%; −39.8 → −2.7% | REPLICATED |
| Crash table, 1987 and 2020 rows (L1 = B2) | −25.1%; −19.4% | −27.1%; −19.6% | −25.1%; −19.4% | REPLICATED (2020); CLOSE (1987, 2.0 pp, pre-1990 global series) |
| Crash table, 1990 row | B2 −20.8%, L1 −9.0%, lag −11.4% | B2 −18.0%, L1 −10.6%, lag −18.0% | −20.8 / −9.0 / −11.4% | CLOSE (explained: episode straddles the 1990-07 splice) |
| Cost: gross to net, unit-price | 0.12 pp/yr at 0.138% | 0.07 pp/yr at 0.08%; 0.11 at 0.138% | 0.12 | REPLICATED |
| Cost table A$50,000 rows (dollar engine) | L1 10.39 / 11.76%, B2 11.68% | 10.99 / 12.26 / 12.08% | 10.39 / 11.76 / 11.67% | CLOSE (explained; same causes as row 1) |
| US 1926–2023: max DD 83.7% → 52.7% (cash 0), 50.4% (T-bill); −0.86 / −0.12 pp; 0.73 switches | as stated | 83.7 → 52.7 / 50.4%; −0.81 / −0.07 pp at 0.08%; 0.73 | −0.86 / −0.12 pp at 0.138% | REPLICATED |

Not attempted: tax tables (4.5), the 26-variant grid, DSR, PBO, momentum satellite, other-country panel, holdout, and the A$5,000 rows of the cost table (minimum commission; the brief excluded minimums).

## 2. What I built (steps 1 and 2, before opening report 36)

**Rule.** Per sleeve, at each month-end, on the total-return index: 6-month return > 0; 12-month return > 0; index above the mean of its last 10 month-end values. Zero votes → cash; two or three → invested; one → keep the previous state. The state decided at month-end t earns the return of month t+1 (base) or t+2 (extra lag). Weights 40% Australia, 60% global; an off sleeve's share sits in cash earning (a) the RBA cash rate or (b) zero. Rebalanced to target every month from drifted weights. Cost 0.08% of every dollar traded in a sleeve, including the small monthly rebalancing trades. No fund fees, no minimums. Benchmark: static 40/60 rebalanced monthly, same cost.

**Data** (downloaded 2026-11-13; parsed as text or spreadsheet; Python run with `-I`).

| Series | Construction |
|---|---|
| Australia | French `Austrlia.Dat`, "Value-Weight Local Returns, All 4 Data Items Not Reqd", column Mkt. 1975-01 on |
| Global, 1990-07 on | French `Developed_3_Factors`, Mkt-RF + RF, USD. Australia left in (base); removed at 2.5% as a sensitivity |
| Global, before 1990-07 | 50% US (French/CRSP Mkt-RF + RF) + 50% a fixed-weight basket of 13 French country files in USD (Japan 45, UK 18, Germany 8, France 6, Switzerland 5, Netherlands 4, Italy 4, Sweden 2, Spain 2, Hong Kong 2, Belgium 2, Singapore 1, Norway 1), rebalanced monthly. I did not know the French international index file existed |
| USD → AUD | (1 + USD return) × FX(t−1) ÷ FX(t) − 1, RBA F11 month-end A$1 = USD |
| Cash | RBA F1.1 interbank overnight cash rate, monthly average ÷ 12 |
| US 1926–2023 | French Mkt-RF + RF, cash = RF |

| File | Bytes | SHA-256 | URL |
|---|---|---|---|
| `F-F_International_Countries.zip` | 1,281,647 | `6041ff104726d6aadfea76c4ef25af35594e799b90064b76b6bb83bd4acb0091` | mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_International_Countries.zip |
| `Developed_3_Factors_CSV.zip` | 4,975 | `3f99cfdeddd1914e3d8f84ce51d775aeed3e98ed0c290957e88f4df9912f8a23` | …/ftp/Developed_3_Factors_CSV.zip |
| `Developed_ex_US_3_Factors_CSV.zip` | 4,999 | `689c242b62e430fecbb8b3cc98269761b38d1d3f7ca15a22c3fb79771c932aee` | …/ftp/Developed_ex_US_3_Factors_CSV.zip (used in step 3 only) |
| `F-F_Research_Data_Factors_CSV.zip` | 13,078 | `b03d39e4bb253dda0f14893db3b78e64b40b8d6549a0fc0fd4111dae84c98618` | …/ftp/F-F_Research_Data_Factors_CSV.zip |
| `F-F_International_Indices.zip` | 407,914 | `6292f7eadfbd7f7dbe9a3fd08d4181f59509973ee4a222040c34b0e4223a687b` | …/ftp/F-F_International_Indices.zip (downloaded and used in step 3 only) |
| `f11hist-1969-2009.xls` | 190,464 | `96d3219a9249a3949dcf02dc7e8044045a2437fa8e36121d4e3f8ccf6042cda6` | www.rba.gov.au/statistics/tables/xls-hist/f11hist-1969-2009.xls |
| `f11hist.xls` | 166,400 | `365a11640c984c603ac7bebb83a6e467ee1605fe765510be0816d2960679a920` | www.rba.gov.au/statistics/tables/xls-hist/f11hist.xls |
| `f1.1-data.csv` | 43,917 | `52de6eef28ba1008bdde43546944b270ef08dca4c9b6282bb34846820a490ce2` | www.rba.gov.au/statistics/tables/csv/f1.1-data.csv |
| `f13-data.csv` (not used) | 116,918 | `1aa9653ebc0f904e6134e564280602aba49729f6159137686081bba42628217c` | www.rba.gov.au/statistics/tables/csv/f13-data.csv |

Also downloaded and not used: `Asia_Pacific_ex_Japan_3_Factors_CSV.zip`, `f11-data.csv`, `f11.1-data.csv`.

The eight files above that both studies downloaded have identical hashes, so both worked from the same bytes.

## 3. My results (frozen before step 3)

Cost 0.08%, no fees, signal applied to the next month unless marked "+1 lag". Sharpe is mean excess return over the RBA cash rate ÷ volatility.

| Run | CAGR | Vol | Sharpe | Max DD | Ulcer | Switches / yr | Time invested | DD 2000–02 | DD 2007–09 | Oct 1987 | Feb–Mar 2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1976-07..2023-12** | | | | | | | | | | | |
| Static 40/60 | 12.20% | 12.86% | 0.43 | 39.8% | 10.9% | — | 100% | −28.3% | −39.8% | −24.9% | −19.6% |
| L1, cash RBA | 12.30% | 11.21% | 0.48 | 27.2% | 6.4% | 1.35 | 83.0% | −8.2% | −7.8% | −24.9% | −19.6% |
| L1, cash 0 | 11.02% | 11.28% | 0.38 | 29.1% | 8.5% | 1.35 | 83.0% | −10.1% | −8.8% | −24.9% | −19.6% |
| L1, cash RBA, +1 lag | 12.10% | 11.38% | 0.46 | 27.2% | 6.8% | 1.35 | 83.0% | −8.7% | −12.9% | −24.9% | −19.6% |
| L1, cash 0, +1 lag | 10.82% | 11.44% | 0.36 | 27.4% | 9.2% | 1.35 | 83.0% | −10.5% | −13.5% | −24.9% | −19.6% |
| L1 gross (no cost), cash RBA | 12.37% | 11.20% | 0.49 | 27.1% | 6.3% | 1.35 | 83.0% | −8.1% | −7.7% | −24.9% | −19.6% |
| **1990-01..2023-12** | | | | | | | | | | | |
| Static 40/60 | 8.64% | 11.69% | 0.38 | 39.8% | 12.0% | — | 100% | −28.3% | −39.8% | — | −19.6% |
| L1, cash RBA | 8.81% | 9.54% | 0.45 | 19.6% | 5.3% | 1.47 | 80.8% | −8.2% | −7.8% | — | −19.6% |
| L1, cash 0 | 7.76% | 9.59% | 0.35 | 19.6% | 6.5% | 1.47 | 80.8% | −10.1% | −8.8% | — | −19.6% |
| L1, cash RBA, +1 lag | 8.44% | 9.80% | 0.41 | 19.6% | 6.2% | 1.47 | 80.8% | −8.7% | −12.9% | — | −19.6% |
| L1, cash 0, +1 lag | 7.41% | 9.84% | 0.31 | 21.7% | 8.0% | 1.47 | 80.8% | −10.5% | −13.5% | — | −19.6% |
| **US, USD, cash = T-bill, 1927-07..2023-12** | | | | | | | | | | | |
| Buy and hold | 10.00% | 18.54% | 0.44 | 83.7% | 21.4% | — | 100% | −45.0% | −50.3% | −22.6% | −20.2% |
| L1, cash T-bill | 9.93% | 13.66% | 0.53 | 50.4% | 14.5% | 0.73 | 80.0% | −18.1% | −10.9% | −22.6% | −20.2% |
| L1, cash 0 | 9.19% | 13.69% | 0.48 | 52.7% | 15.5% | 0.73 | 80.0% | −21.9% | −10.9% | −22.6% | −20.2% |

Window drawdowns are peak-to-trough inside the calendar window (2000-01..2002-12, 2007-01..2009-12). October 1987 is the one-month return. February–March 2020 is the two-month return.

The rule did nothing in October 1987 or February–March 2020 in any run. All of the drawdown saving comes from 2000–02 and 2007–09. Maximum-drawdown reduction with cash at 0: 50.8% on 1990–2023 and 26.7% on 1976–2023.

Cost sensitivity (1976–2023, cash RBA; turnover is 0.82× the account a year): L1 CAGR 12.37% at no cost, 12.30% at 0.08%, 12.19% at 0.20%, 11.91% at 0.50%, 11.45% at 1.00%.

Sensitivity of my own data choices (1976–2023, L1 cash RBA / B2 CAGR; L1 cash-0 max DD): equal-weight international basket 12.14 / 12.09%, 31.8%; US weight 60% 12.24 / 12.09%, 29.9%; US weight 35% 12.56 / 12.36%, 26.0%; Australia stripped from Developed 12.38 / 12.18%, 29.1%. On 1990–2023 none of these moves a CAGR by more than 0.15 points or a maximum drawdown by more than 0.3 points.

## 4. Why my 1976–2023 CAGR is 0.4 points higher (step 3)

Ladder from my run to the original's specification, one change at a time (1976-07..2023-12, my engine):

| Step | L1 cash RBA | L1 cash 0 | B2 | L1 max DD (RBA / 0) | Switches / yr |
|---|---|---|---|---|---|
| A. My run | 12.30% | 11.02% | 12.20% | 27.2 / 29.1% | 1.35 |
| B. + Australia removed from Developed at 2.5% (1990-07 on) | 12.38% | 11.09% | 12.18% | 27.2 / 29.1% | 1.35 |
| C. + original's pre-1990 global series (French international index, back-cast US weight 36–44%) | 12.16% | 10.87% | 11.98% | 25.7 / 28.2% | 1.52 |
| D. + ETF fees 0.07% and 0.18% a year, deducted before the signal | 11.90% | 10.59% | 11.83% | 25.7 / 28.2% | 1.52 |
| E. + cost 0.138% instead of 0.08% | 11.84% | 10.53% | 11.81% | 25.8 / 28.4% | 1.52 |
| Report 36 | 11.87% | 10.55% | 11.84% | 25.8 / 28.3% | 1.52 |

| Cause | Effect on L1 CAGR (cash RBA) | Which is right per the spec text |
|---|---|---|
| ETF fees on proxy data | −0.26 pp | Original. RND-021 requires "the fund's management fee on proxy-era data". The brief I worked from omitted it |
| Pre-1990 global series | −0.22 pp, and all of the switch-count and 1987 / 1990 differences | Original is better. It uses French's own value-weighted ex-US index; mine is a fixed-weight basket that over-weights 1980s Japan and UK (global CAGR 1976-07..1990-06: 22.0% mine, 20.7% original). The spec does not define this series; it is a proxy either way |
| Australia stripped from Developed | +0.08 pp | Original (the sleeve is "ex-Australia"). The 2.5% weight is an assumption |
| Cost rate 0.138% against 0.08% | −0.06 pp | Original. RND-021: max(A$6.60, 0.088%) commission including GST plus 5 bp half-spread |
| Cost charged on monthly rebalancing trades | −0.03 pp (the residual between row E and the report) | Mine, marginally. The original's unit-price engine charges cost only on changes in target weight, so drift-correcting trades and the whole of B2 are free. Its dollar engine does charge them |

Initial state: the spec (PRT-13) says OFF before the first evaluation; I started ON. Both sleeves have two or more votes at the first evaluation (1975-12), so this makes no difference from 1976 on.

Marginal votes: three global-sleeve whipsaws differ after 1990 and each is a vote decided by a few basis points. Stripping Australia adds an OFF/ON pair at 2009-10/11 and removes the 2018-12/2019-02 pair; deducting fees restores 2018-12/2019-02 and removes my 1994-08/09 pair. The Australian sleeve's 32 switch dates are identical in both studies.

## 5. H1, crash table, cost table

### 5.1 H1 on 1990–2023

Report 36's H1 figures come from its dollar engine: B2 rebalanced each July, L1 rebalanced only on a state change or a ±20% band breach. My brief specified monthly rebalancing. After opening the report I wrote my own band engine (no order minimums). Results with cash at 0:

| Inputs | Engine | L1 max DD | B2 max DD | Reduction | p |
|---|---|---|---|---|---|
| Report 36 | dollar, A$50,000 | 19.2% | 39.5% | 51% | 0.066 |
| Original's inputs | my band engine | 19.2% | 39.5% | 51.3% | 0.067 |
| Original's inputs | my monthly engine | 19.4% | 39.8% | 51.3% | 0.062 |
| My data, 0.08%, no fees | my monthly engine | 19.6% | 39.8% | 50.8% | 0.080 |
| My data, 0.08%, no fees | my band engine | 19.4% | 39.7% | 51.0% | 0.089 |

p is from my own paired stationary bootstrap (10,000 paths, mean block 12, different random stream). H1 passes in all five rows. L1's worst drawdown in this window is February–March 2020, when it was fully invested; B2's is the 2007–09 fall.

### 5.2 H1 on 1976–2023

| Inputs | Engine | L1 max DD | B2 max DD | Reduction | p |
|---|---|---|---|---|---|
| Report 36 | dollar, A$50,000 | 28.9% | 39.5% | 27% | 0.184 |
| Original's inputs | my band engine | 28.85% | 39.53% | 27.0% | 0.185 |
| Original's inputs | my monthly engine | 28.4% | 39.8% | 28.7% | 0.193 |
| My data, 0.08%, no fees | my monthly engine | 29.1% | 39.8% | 26.7% | 0.231 |
| My data, 0.08%, no fees | my band engine | 30.8% | 39.7% | 22.3% | 0.260 |

The 27% is reproduced. The report's sentence that the point estimate "clears the 25% bar by two points" is true for its data and not robust: with my pre-1990 global basket and the same band rebalancing the reduction is 22%, below the bar. The report's own A$5,000 row gives 30.1% against 39.5%, which is 24%. L1's worst drawdown in this window is the 1987 crash, so the figure depends on how far the pre-1990 global proxy fell in September–November 1987 (−16.8% in the original's series, −20.4% in mine, in AUD). The conclusion "not passed on 1976–2023" holds in every row, because p is never below 0.10.

### 5.3 Crash table

Peak-to-trough between the original's B2 peak and trough months. "Mine" is my independent data at 0.08% and no fees.

| Episode | B2: report / mine | L1 cash RBA: report / mine | L1 cash 0: report / mine | L1 +1 lag: report / mine | Round trip L1 − B2, cash RBA: report / mine | Class |
|---|---|---|---|---|---|---|
| 1980-11..1982-03 | −18.1 / −16.4% | −7.3 / −6.9% | −13.6 / −11.9% | −6.7 / −5.1% | +6.3 / +6.3 | REPLICATED |
| 1987-09..1987-11 | −25.1 / −27.1% | −25.1 / −27.1% | −25.1 / −27.1% | −25.1 / −27.1% | −6.7 / −2.5 | CLOSE: pre-1990 global series |
| 1989-12..1990-09 | −20.8 / −18.0% | −9.0 / −10.6% | −10.9 / −11.2% | −11.4 / −18.0% | +0.6 / −4.3 | CLOSE: straddles the splice; global OFF at 1990-04 (original) or 1990-08 (mine) |
| 1994-01..1995-01 | −12.0 / −12.0% | −11.5 / −12.8% | −13.6 / −14.6% | −5.9 / −5.0% | −9.8 / −11.2 | REPLICATED |
| 2000-10..2003-02 | −33.8 / −33.0% | −3.7 / −3.3% | −10.4 / −10.0% | −4.5 / −4.2% | +26.5 / +26.1 | REPLICATED |
| 2007-05..2009-02 | −39.7 / −39.7% | −2.7 / −2.4% | −8.9 / −8.7% | −6.6 / −6.3% | +28.2 / +30.4 | REPLICATED (round trip 2.2 pp apart: the 2009-10 whipsaw) |
| 2011-03..2011-09 | −13.6 / −13.6% | −10.1 / −10.0% | −10.5 / −10.4% | −13.2 / −13.1% | −2.1 / −2.0 | REPLICATED |
| 2015-07..2016-02 | −9.8 / −9.8% | −10.5 / −10.4% | −10.8 / −10.7% | −10.0 / −9.9% | −8.9 / −8.8 | REPLICATED |
| 2018-09..2018-12 | −10.8 / −10.7% | −10.6 / −10.5% | −10.6 / −10.5% | −10.8 / −10.7% | −9.9 / −9.8 | REPLICATED |
| 2020-01..2020-03 | −19.4 / −19.6% | −19.4 / −19.6% | −19.4 / −19.6% | −19.4 / −19.6% | −8.1 / −8.0 | REPLICATED |
| 2021-12..2022-06 | −14.6 / −14.5% | −12.2 / −11.9% | −12.2 / −12.0% | −14.6 / −14.5% | −6.0 / −5.9 | REPLICATED |

With the original's inputs my engine returns every cell of the report's table to within 0.1 point. The report's reading stands: large savings in 2000–02 and 2008–09, none in 1987 and 2020, and a net loss on the round trip in most of the smaller episodes.

### 5.4 Cost table

| Item | Report 36 | Mine |
|---|---|---|
| Gross to net, unit-price, 1976–2023 | 11.99% → 11.87% (0.12 pp at 0.138%) | 12.37% → 12.30% (0.07 pp at 0.08%); 0.11 pp at 0.138% (turnover 0.82× a year) |
| Constant-size switching cost, A$25,000 and above | 0.11% a year | 0.11% a year at 0.138% |
| A$50,000, L1 cash 0 / L1 cash RBA / B2 CAGR | 10.39 / 11.76 / 11.68% | Original's inputs, my band engine: 10.39 / 11.76 / 11.67%. My data: 10.99 / 12.26 / 12.08% |
| A$50,000, max DD L1 cash 0 / L1 cash RBA / B2 | 28.9 / 27.5 / 39.5% | Original's inputs: 28.85 / 27.52 / 39.53%. My data: 30.8 / 28.8 / 39.7% |
| L1 − B2, cash 0, 1976 / 1990 | −1.30 / −0.70 pp | Original's inputs: −1.29 / −0.71. My data: −1.09 / −0.83 |
| L1 − B2, cash RBA, 1976 / 1990 | +0.08 / +0.38 pp | Original's inputs: +0.09 / +0.37. My data: +0.18 / +0.21 |

The report's conclusion that brokerage is not what L1 costs is confirmed: even at 1.00% per trade the drag is under one point a year, and the gap between cash at 0 and cash at the RBA rate is 1.28 points on 1976–2023 and 1.05 on 1990–2023 in my run (report: 1.31 and 1.08).

A first draft of my band engine let buys exceed cash on hand. That gave L1 a 30.0% drawdown and 10.72% CAGR on the original's inputs. Capping buys at available cash, as the original does, gave 28.85% and 10.39%. The original's handling is the correct one.

## 6. Points for the authors of report 36

1. **US table label.** The row "US 1926-07..2023-12, 1,152 months" is measured over 1928-01..2023-12 (18 warm-up months are dropped). The 9.8% buy-and-hold CAGR is for that window; from 1927-07 it is 10.0%. Drawdowns and the cost of the rule are unaffected.
2. **Unit-price engine charges nothing for drift rebalancing.** B2 pays no cost at all in section 4.1 and L1 pays only on state changes. Worth 0.03 points a year. The dollar engine is not affected.
3. **The 27% figure for 1976–2023 should carry a range.** It is 22–29% across reasonable pre-1990 global proxies and rebalancing conventions, and 24% in the report's own A$5,000 run. "Clears the 25% bar by two points" overstates what is known.
4. **Section 4.1 against section 6.1.** The headline table gives 28.3% for L1 with cash at 0 and conclusion 1 gives 28.9%. Both are correct (unit-price against dollar engine), but they are easy to read as a discrepancy.
5. Three post-1990 whipsaws depend on votes decided by a few basis points (fee deduction or the 2.5% Australia weight flips them). This does not change any headline, but it is a reminder that individual switch dates in section 11.2 are not robust facts.

## 7. Files

All under `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/replication_36/` (session storage; copy it if it is to be kept).

| File | Purpose |
|---|---|
| `code/load.py`, `code/backtest.py` | Steps 1 and 2: parsers, rule, engine, metrics. Run: `python3 -I code/backtest.py data out` |
| `out_frozen_before_step3/` | Results as they stood before report 36 was opened (`results.json`, `results.csv`, monthly returns and states) |
| `code/reconcile.py` | Step 3: series comparison, engine check on the original's panel, ladder, crash table, US check |
| `code/band_engine.py`, `code/boot.py` | Step 3: July / band rebalancing engine and paired stationary bootstrap |
| `code/switchlog.py`, `code/sw2.py`, `code/explore.py` | Switch dates, marginal-vote check, file hashes and data checks |
| `out/reconcile_log.txt`, `out/band_log.txt`, `out/boot_log.txt`, `out/reconcile/*.csv` | Step 3 outputs |
| `data/raw/` | Downloads (hashes in section 2) |
