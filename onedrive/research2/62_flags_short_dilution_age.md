# 62 — Red flags tested: short interest, dilution, listing age, results-day reaction; and the forward archive design

Date: 2026-11-14. Status: the five actions of report 61 section 5, run as pre-registered (`flags/PREREG_FLAGS.md`, SHA-256 c80c4805…, hashed at 12:27 UTC before the bulk download and before any return was computed). Ten trials, programme count 368. Research use only; general information, not financial advice.

## 0. Answer first

**No flag passed the test for changing what the Big Wins engine buys.** One flag, heavy share issuance, is a confirmed fact about later returns and belongs on the owner's red-flag panel. The results-day idea looked strong in December-reviewed accounts and failed a June-reviewed replication.

| Flag (card) | Stand-alone, unseen 2017–2023: flagged minus rest of the top 300, next 12 months | Same, development period | Exclusion on the engine, unseen: change in return a year, A$25,000 / A$100,000 | Position against 1,000 random exclusions | Verdict |
|---|---|---|---|---|---|
| **A1 short interest**, top tenth (H130) | **+2.4 points**, t = 0.5. Wrong sign | −5.0, t = −1.3 | −0.04 / −0.13 points (−A$10 / −A$135 a year) | 48th / 14th percentile | **Not passed.** Show on the panel as a fact only |
| **A2 dilution**, top fifth by 12-month share growth (H131) | **−3.5 points**, t = −2.2; 5 of 6 Decembers negative | −14.8, t = −5.0; 6 of 6 | −0.16 / −0.15 points (−A$39 / −A$147) | 52nd / 17th | **Stand-alone effect confirmed; exclusion not passed.** Panel flag with an evidence line |
| A2 "shrinkers", share count down 1% or more (H131) | −2.4 points, t = −1.4. Wrong sign | +10.4, t = 2.6 | not tested (by design) | — | **Not passed.** Development result did not repeat |
| **A3 listed under 504 trading days** (H132) | **−8.9 points**, t = −1.5; 6 of 7 Decembers negative | −4.9, t = −1.4 | −0.35 / −0.05 points (−A$86 / −A$54) | 20th / 32nd | **Promising as a flag; exclusion not passed** |
| Composite: any of the three | (information) −1.5, t = −0.7 | −11.7, t = −7.5 | **−1.03 / −0.98 points** (−A$257 / −A$976) | 32nd / 4th | **Not passed.** Excluding 87 names a month made the engine worse |
| **A4 results-day reaction** (H133), stand-alone, 6 months | +1.8 points, t = 1.1 (top 300); +2.7, t = 2.1 (top 500) | +4.7, t = 2.8 | — | — | **Partly tested; not confirmed in the top 300** |
| A4 combined with the engine's score | +7.2 / +3.2 points over the engine; 92nd / 97th percentile of "score + noise" | +0.1 / +1.6; 96th / 96th | — | June-reviewed replication: 35th / 33rd percentile (unseen), 60th / 46th (development) | **Not robust. Closed as an engine input; kept as a measurement line** |

What this means in practice:

1. **Leave the engine alone.** Every exclusion moved the unseen result by less than the engine's own one-point path noise (report 54), except the composite, which cost a point. The engine already avoids most of these names: the flagged companies sit, on average, in the lower half of its score order, and typically only 3% to 10% of them are in its top 30.
2. **Put three facts on the "Your picks, honestly" page,** with their evidence stated plainly: share count up about 10% or more in a year (top-300 companies with this lost 3.5 points a year against the rest in 2017–2023, and twice as many of them halved); listed under two years (8.9 points worse, not conclusive); short interest in the top tenth (no reliable difference).
3. **Do not act on short interest.** In the unseen period heavily shorted top-300 companies did slightly better than the rest. The engine's own heavily shorted picks did better than its other picks in both periods.
4. **The forward archive (section 7) is the only route to an honest test of the announcement-based ideas.** It needs two owner decisions first: the spec currently forbids fetching from asx.com.au (DAT-15), and the ASIC licence terms could not be read from this session.

Confirmed about the ASIC source: the daily short-position files exist as CSV from 16 June 2010 at the URL pattern report 61 guessed, **and they carry "Total Product in Issue"**, so a free, dated share count exists for about 96% of the top 300, delisted companies included. All 4,151 daily files to 9 November 2026 were downloaded (229 MB).

## 0.1 Caveats

- **Six or seven December cohorts per half.** The short data starts in 2010. Stand-alone tests use 66 to 89 overlapping monthly formations; the exclusion tests rest on six or seven yearly reviews of a 10- or 30-name book. An exclusion would need to add several points a year to be visible. None came close.
- **The unseen period is blind for each flag, not for the engine** (looked at eight or nine times before this report, as report 61 disclosed).
- **Price-only returns.** Dividends are ignored on both sides. Diluting companies pay fewer dividends, so the true gap is probably somewhat wider than shown; buy-back companies pay more, which would help "shrinkers" a little.
- **The share count is the ASIC file's count.** For CHESS depositary interests it is the number held in Australia, not the company's shares. A sensitivity without those products is shown; it changes nothing.
- **The dilution flag needed a reconciliation of 325 share-count events against the price panel's split factors.** It was done by written rules before any return was attached (deviation D2). One rule had a bug that was found and fixed after the first run (deviation D9); 6 of 8,521 flag memberships changed and no conclusion moved. It is still the most judgement-laden step in the report.
- **A4 uses a headline table that contains only companies listed today.** Nothing from it can be more than "partly tested".
- **One accidental look** (deviation D4), **one bug-fix re-run** of A2 and the composite (D9) and **one post-hoc replication** (June accounts for A4) are logged. None involved a parameter choice.
- **The ASIC copyright page was not readable from this session.** The files are held for private research; this report publishes derived statistics only.

## 1. The ASIC source, verified

| Question | Finding |
|---|---|
| URL pattern | `https://download.asic.gov.au/short-selling/RR{yyyymmdd}-{vvv}-SSDailyAggShortPos.csv` (a `.pdf` twin exists). HTTP 200 for 16 Jun 2010, 15 Jun 2016 and 12 Jun 2024 in both formats |
| Index | `…/short-selling/short-selling-data.json`: 4,151 position dates, 16 Jun 2010 to 9 Nov 2026, one version each. 3,806 dates are version 001; 345 were re-issued (002: 182; 010: 154; 003: 8; 004: 1). 156 of the re-issued dates are in 2023 and 103 in 2025 |
| Layout | Five columns: Product, Product Code, Reported Short Positions, **Total Product in Issue**, % of Total Product in Issue Reported as Short Positions. 2010–2016 samples are UTF-16 and tab-separated with a padded code; the 2024 sample is ASCII and comma-separated |
| Timing | The 2024 PDF for position date 12 June was produced on 18 June: four business days, as report 61 said. The tests use a position from the fifth trading day after its date |
| Size | 438 to 720 products a day (yearly averages); 2,312,533 rows in all; 4,329 distinct codes |
| Bad files | Three empty, one HTML error page, one with three unparseable rows. One file (16 Jul 2021) failed on first request and was fetched on retry after the first A1 run; rebuilding with it changed none of the 5,040 short-interest flag memberships |
| Match to the price panel | 95.8% of rows to May 2024 match a company in the price panel by code and date. Unmatched: exchange-traded products, hybrids, suspended shells, and companies the panel does not hold (section 9) |
| Coverage of the top 300 | 95.3% (2010–2016) and 96.4% (2017–2023) of top-300 companies have a row on the latest usable day |
| Licence | Each PDF says "No responsibility is accepted for any inaccuracies contained in the matter published." The ASIC copyright page (`www.asic.gov.au`) is blocked from this session. A search snippet says ASIC owns copyright in its material unless stated and licenses some of it under CC BY 4.0 [1, unverified for these files]. Treated as private-use material until read |

Download record: `flags/raw/manifest.tsv` (URL, UTC time, status, bytes, SHA-256 for every file; the manifest's own SHA-256 is 818eb4e6…). One request at a time, starts 1.1 seconds apart, 12:27 to 13:46 UTC.

## 2. Method in brief

All of this is fixed in the pre-registration; the choices where report 61 was silent are marked there.

- **Engine.** `bigwins2/code/engine.py` copied byte for byte (SHA-256 416f7573…) and never edited. The exclusion is a wrapper around its month-end table that marks flagged companies as not buy-eligible; scores and ranks are not recomputed, so the engine takes the next-ranked name. The unfiltered runs reproduce report 55's figures to the last digit (9.43% and 6.28% a year, development, A$25,000 and A$100,000).
- **X1, stand-alone.** At each month-end, the equal-weight 12-month price return of flagged top-300 companies minus that of the other top-300 companies. A company that stops trading is paid out at its last price × 0 (failure record), × 1 (takeover record) or × 0.70 (no record); the D0 and D100 variants are in the tables. The test statistic is the mean over monthly formations with a Newey–West t (11 lags). December formations are shown as the headline cohort.
- **X2, exclusion.** One account per period and size, started in cash, costs on, tax off for the headline (tax in the tables). Δ = filtered minus unfiltered compound return. Placebo: 1,000 runs that exclude, each month, the same number of randomly chosen names from the engine's candidate list. A second, "rank-matched" placebo (200 runs) draws the random names from the same score deciles as the flagged ones.
- **"Survives"** needs, on unseen data, X1 negative with t ≤ −2.0 and negative Decembers; X1 negative with t ≤ −1.5 on development data; and Δ ≥ 0 above the 90th percentile of the placebo at both sizes. "Promising" is X1 negative in both periods with unseen t between −1 and −2.
- **Deflated Sharpe ratio** with N = 368 (and 1,000), on the monthly calendar-time series of rest-minus-flagged (X1) and on the paired monthly difference of the two accounts (X2).
- **Order.** Development first, then unseen once per idea; every run on any data is in `flags/out/looks.csv` (18 lines).

Deviations D1 to D9 are listed in section 10 of the pre-registration and summarised in section 8.3 below.

## 3. A1 — short interest (H130)

Signal: reported short positions ÷ total product in issue, mean of the five most recent usable days; flag = the 30 highest in the top 300. The cut-off averaged 5.2% of shares on issue in 2010–2016 and 5.8% in 2017–2023 (the most-shorted name was between 12% and 21%).

| | Development, Jul 2010 – Dec 2016 | Unseen, Jan 2017 – May 2023 |
|---|---|---|
| Monthly formations | 78 | 77 |
| Flagged − rest, next 12 months | −5.0 points | **+2.4 points** |
| Newey–West t | −1.25 | 0.50 |
| December cohorts: mean, t, number negative | −4.8, −0.79, 3 of 7 | −2.0, −0.33, 4 of 6 |
| Median difference / winsorised | −9.2 / −4.3 | +1.4 / +2.0 |
| D0 / D100 | −4.6 / −4.6 | +2.5 / +2.3 |
| Flagged / rest: lost more than half | 15.9% / 11.7% | 14.8% / 6.7% |
| Flagged / rest: doubled | 2.0% / 1.6% | 5.3% / 3.0% |
| Flagged / rest: failure record | 1.5% / 0.5% | 0.2% / 0.0% (records end Apr 2020) |
| Deflated Sharpe, rest − flagged (N = 368 / 1,000) | 0.44 / 0.38 | 0.10 / 0.08 |

December cohorts, flagged − rest: 2010 −18.8; 2011 +3.0; 2012 +1.3; 2013 −14.5; 2014 −26.0; 2015 +20.7; 2016 +0.9; 2017 −10.0; 2018 +5.4; 2019 +21.7; 2020 −20.7; 2021 −0.5; 2022 −7.6. The sign changes from year to year.

Exclusion on the engine:

| Period | Size | Engine | With exclusion | Δ points | Placebo 10th / 50th / 90th | Percentile | Rank-matched percentile | Paired t |
|---|---|---|---|---|---|---|---|---|
| Development | A$25,000 | 14.9% | 13.3% | −1.56 | −2.40 / −1.05 / −0.04 | 30 | 4 | −1.73 |
| Development | A$100,000 | 9.1% | 9.6% | +0.49 | −1.20 / −0.19 / +0.76 | 82 | 74 | 0.62 |
| **Unseen** | A$25,000 | 1.8% | 1.7% | **−0.04** | −1.24 / −0.02 / +1.21 | 48 | 34 | −0.07 |
| **Unseen** | A$100,000 | 4.7% | 4.5% | **−0.13** | −0.29 / +0.67 / +1.56 | 14 | 16 | −0.13 |

Secondary, not trials:

- **SI of 5% or more** (33 to 39 names): −3.2 points (t −0.7) in development; +0.6 (t 0.1) unseen.
- **Three-month rise in SI, top tenth:** −4.8 points (t −2.3) in development; 0.0 (t 0.0) unseen. The one secondary that looked good in development vanished.
- **Tail risk is real even though the mean is not.** In both periods flagged companies were more likely to halve (15% against 7% unseen) and more likely to double (5.3% against 3.0%). Heavy short interest marks a wide range of outcomes, not a low average.
- **The engine's own heavily shorted picks did better than its other picks:** unseen, A$100,000: 12 of 225 positions carried the flag at entry and returned +22.6% on average against +4.8% for the rest; development: 13 of 176, +15.5% against +11.0%. A stock that scores well on trend and low volatility while heavily shorted has, more often than not, been one where the shorts were wrong.
- **Make-up.** In each December the largest named groups among the 30 were materials (4 to 8 names) and retail (3 to 4); 6 to 15 had no industry group on file because they have since delisted. It is not a single-sector bet, which was one of report 61's worries.

**Reading.** Report 61 expected X1 negative by 2 to 6 points and X2 within ±0.5. X2 came in as expected. X1 did not hold: −5.0 then +2.4, neither distinguishable from zero. In Australia's top 300 since 2017, being in the most-shorted tenth has not predicted a lower 12-month return. **Verdict: not passed.** The panel may still show the number, because the tail statistic (twice the rate of halving) is a fact an owner would want when sizing a pick.

## 4. A2 — dilution and "shrinkers" (H131)

Signal: NI = ln(split-adjusted total product in issue now ÷ 12 months earlier), each end the median of five usable days. Flag = top fifth of the top 300 (about 54 companies). The cut-off averaged NI = 0.098 in development and 0.090 unseen: **a share count up about 9% to 10% in a year.** NI was available for 268 and 272 of the 300 on average.

**Reconciliation before returns were attached.** 325 events were checked by rule (log: `flags/out/a2_reconcile.csv`): 69 splits or consolidations consistent with the count (the factor step was moved to the day the count jumped); 23 price factors that were distributions or demergers, not splits (removed for counts); 11 raisings with a bonus-element or doubtful-split price factor (count kept, factor removed); 18 consolidations where the count gave a different whole-number ratio from the price panel (resized); 13 consolidations with a simultaneous issue (panel factor kept); 2 large issues made into a falling price (left alone); 1 unresolved (News Corp's 2013 separation; set to missing); 188 with no count close enough on one side (panel factor used as it stands). These are the counts after the bug fix of deviation D9; the figures below are from the corrected run, and the first run is kept beside it.

| | Development, Jul 2011 – Dec 2016 | Unseen, Jan 2017 – May 2023 |
|---|---|---|
| Monthly formations | 66 | 77 |
| Flagged − rest, next 12 months | **−14.8 points** | **−3.5 points** |
| Newey–West t | −5.00 | **−2.22** |
| December cohorts: mean, t, number negative | −12.4, −3.79, 6 of 6 | −5.2, −1.71, 5 of 6 |
| Median difference / winsorised (t) | −15.2 / −14.0 (−4.4) | −5.8 / −3.7 (−2.7) |
| D0 / D100 | −14.5 / −14.4 | −3.4 / −3.6 |
| Flagged / rest: 12-month return | −12.2% / +2.6% | +0.9% / +4.3% |
| Flagged / rest: lost more than half | 22.3% / 9.9% | 13.5% / 6.2% |
| Flagged / rest: doubled | 1.6% / 1.8% | 4.6% / 2.9% |
| Deflated Sharpe, rest − flagged (N = 368 / 1,000) | 0.98 / 0.97 | 0.40 / 0.34 |
| Without CDI products (sensitivity) | −15.2, t −5.2 | −4.0, t −2.4; Decembers −6.0, t −1.9 |

December cohorts, flagged − rest: 2011 −15.7; 2012 −26.6; 2013 −6.7; 2014 −8.3; 2015 −12.4; 2016 −4.7; 2017 −13.6; 2018 −3.8; 2019 +8.3; 2020 −7.0; 2021 −9.0; 2022 −5.8. Eleven of twelve negative.

Exclusion on the engine:

| Period | Size | Engine | With exclusion | Δ points | Placebo 10th / 50th / 90th | Percentile | Rank-matched percentile | Paired t |
|---|---|---|---|---|---|---|---|---|
| Development | A$25,000 | 8.9% | 7.3% | −1.56 | −2.62 / −0.90 / +0.70 | 31 | 16 | −1.10 |
| Development | A$100,000 | 6.2% | 6.2% | −0.06 | −1.41 / −0.17 / +1.07 | 55 | 36 | −0.03 |
| **Unseen** | A$25,000 | 1.8% | 1.6% | **−0.16** | −1.75 / −0.20 / +1.55 | 52 | 44 | −0.13 |
| **Unseen** | A$100,000 | 4.7% | 4.5% | **−0.15** | −0.45 / +0.72 / +1.87 | 17 | 28 | −0.04 |

Why a real stand-alone effect does nothing for the engine: the engine bought few of these companies, and the names that replaced them were no better. Unseen, A$100,000: 26 of 225 positions carried the flag at entry. They returned +0.2% on average against +6.5% for the other positions, and 11.5% of them halved against 1.5%. That is the stand-alone effect, visible inside the engine's own book. But excluding them promoted the next names in score order, changed the timing of every later purchase, and the account ended 0.15 points a year lower. At 10 to 30 names, removing two or three below-average positions a year is smaller than the noise from reshuffling the rest.

**Shrinkers** (share count down 1% or more; 15 companies a month in development, 24 unseen):

| | Development | Unseen |
|---|---|---|
| Shrinkers − rest, next 12 months | +10.4 points, t = 2.55 | **−2.4 points, t = −1.36** |
| December cohorts | +5.8, t = 1.09, 3 of 6 positive | −1.8, t = −0.66, 3 of 6 positive |
| Lost more than half: shrinkers / rest | 4.5% / 12.6% | 4.8% / 7.8% |
| Without CDI products | +11.7, t = 2.8 | −1.7, t = −0.7 |
| Deflated Sharpe (N = 368) | 0.77 | 0.05 |

The development result did not repeat. What did repeat is the lower rate of large losses, which is what one would expect of companies with spare cash. **Verdict for shrinkers: not passed.**

Ranks 301–500 (information only; the engine tables stop at 500, so report 61's 301–1,000 was narrowed): flag − rest −12.1 points (t −5.1) in development, −4.2 (t −1.1) unseen; Decembers −9.7 and −11.4. The same direction, noisier.

**Reading.** This is the one result in the batch that held on unseen data in the predicted direction: t = −2.2 on the pre-registered statistic, −2.7 winsorised, 5 of 6 unseen Decembers negative, robust to the delisting assumption and to removing CDIs. The effect was four times larger in 2011–2016 (the mining bust, when serial issuers collapsed), so −3.5 points is the more believable size. The unseen deflated Sharpe ratio is 0.40, far below the spec's 0.95, and report 61's expectation for the exclusion (0 to 1 point) was not met: it was −0.15. **Verdict: stand-alone effect confirmed; exclusion not passed.** It goes on the panel with its evidence line. It is not a candidate for the engine and I would not spend a paper-book challenger slot on it: the exclusion test already answered that question.

## 5. A3 — listing age (H132) and the composite

Signal: fewer than 504 trading days since the company's first row in the price panel, with linked code changes continued and 36 demerger children excluded. 20 companies a month in development (57 in December 2000, 2 in 2009), 13 unseen.

| | Development, Dec 2000 – Dec 2015 | Unseen, Jan 2016 – May 2023 |
|---|---|---|
| Monthly formations | 181 | 89 |
| Flagged − rest, next 12 months | −4.9 points | **−8.9 points** |
| Newey–West t | −1.44 | −1.47 |
| December cohorts: mean, t, number negative | −7.3, −1.60, 12 of 16 | −14.9, −1.95, 6 of 7 |
| Median difference / winsorised (t) | −6.4 / −5.1 (−1.7) | −13.3 / −10.3 (−1.7) |
| D0 / D100 | −4.6 / −5.2 | −9.5 / −7.4 |
| Flagged / rest: lost more than half | 16.0% / 11.5% | **24.2% / 6.7%** |
| Flagged / rest: doubled | 3.9% / 3.5% | 7.2% / 2.9% |
| Raw-code age (sensitivity) | −4.5, t −1.4 | −7.4, t −1.8 |
| Deflated Sharpe, rest − flagged (N = 368 / 1,000) | 0.65 / 0.56 | 0.54 / 0.48 |

| Period | Size | Engine | With exclusion | Δ points | Placebo 10th / 50th / 90th | Percentile | Rank-matched percentile |
|---|---|---|---|---|---|---|---|
| Development | A$25,000 | 9.4% | 9.3% | −0.13 | −1.13 / −0.18 / +0.45 | 53 | 77 |
| Development | A$100,000 | 6.3% | 6.5% | +0.23 | −0.58 / −0.03 / +0.39 | 77 | 68 |
| **Unseen** | A$25,000 | 1.6% | 1.3% | **−0.35** | −0.72 / −0.02 / +0.82 | 20 | 30 |
| **Unseen** | A$100,000 | 4.0% | 3.9% | **−0.05** | −0.43 / +0.17 / +0.81 | 32 | 28 |

The engine rarely buys these names (12 of 288 positions in development at A$25,000; 4 of 92 unseen), because a company needs 200 traded days to enter the universe and a year of calm prices to score well. The few it did buy were poor: development, A$25,000, −1.0% against +11.1% for other positions, a third of them halved. The exclusion still made no difference to the account.

**Reading.** Negative in both periods, larger in the second, about one company in four halving within a year since 2016 against one in fifteen for the rest, but only 13 names a month and t = −1.5. **Verdict: promising as a flag; exclusion not passed.** On the panel it reads "listed 14 months; top-300 companies this young halved within a year about one time in four, 2016–2023".

**Composite** (excluded if any of the three flags is set; about 87 to 91 of the 300 each month):

| Period | Size | Engine | With exclusion | Δ points | Placebo 10th / 50th / 90th | Percentile | Rank-matched percentile |
|---|---|---|---|---|---|---|---|
| Development | A$25,000 | 8.9% | 6.9% | −2.01 | −3.35 / −1.16 / +0.96 | 29 | 12 |
| Development | A$100,000 | 6.2% | 6.0% | −0.24 | −2.13 / −0.47 / +1.10 | 58 | 60 |
| **Unseen** | A$25,000 | 1.8% | 0.7% | **−1.03** | −2.31 / −0.17 / +2.34 | 32 | 19 |
| **Unseen** | A$100,000 | 4.7% | 3.7% | **−0.98** | −0.53 / +0.88 / +2.24 | 4 | 4 |

Stand-alone, for information: any-flag minus rest −11.7 points (t −7.5) in development, −1.5 (t −0.7) unseen; the short-interest names dilute the dilution effect. On the engine the composite cost a point a year at both sizes and sat at the 4th percentile of random exclusions at A$100,000. **Verdict: not passed.** The three flags overlap little (in a typical December 2 to 11 companies carry both the short and the dilution flag; almost none carry age and short together), so the composite removes nearly a third of the universe, and what it removes includes names the engine does well with.

## 6. A4 — results-day reaction on real dates (H133)

The report 59 agent's typed event table (`niche/out/events.csv.gz`, 1,256,400 headlines, every weekday from 1 July 2009) was complete when needed, so A4 was run. Report 61's regex found 39,020 results headlines; 74% mapped to a company in the price panel on the release date; after "first per company per half-year" and the price requirements there are 6,545 events, of which 89 to 223 a season are top-300 companies. A top-300 season should have about 280 reporters, so **between a fifth and two-thirds of each season is missing**: companies no longer listed, and headlines the regex does not catch.

### 6.1 Trial 9: stand-alone drift

EAR = stock return minus XJO over event days −1 to +2 (after-market releases moved to the next day). Top fifth of EAR against the rest of that season's reporters, from the close of day +3 to day +126, minus XJO.

| Sample | Seasons | Reporters a season | Top fifth − rest, 6 months | t across seasons | Seasons positive | Top fifth / rest / bottom fifth | Top − bottom (t) |
|---|---|---|---|---|---|---|---|
| Development 2009-08 to 2016-08, top 300 | 15 | 116 | **+4.7 points** | 2.84 | 11 | +3.5 / −1.2 / −3.5 | +7.0 (2.6) |
| Development, top 500 | 15 | 167 | +4.3 | 2.54 | 10 | +3.6 / −0.7 / −3.6 | +7.2 (2.8) |
| **Unseen 2017-02 to 2023-08, top 300** | 14 | 189 | **+1.8 points** | 1.10 | 10 | +1.7 / −0.1 / −1.6 | +3.3 (1.8) |
| Unseen, top 500 | 14 | 288 | +2.7 | 2.11 | 9 | +2.3 / −0.4 / −2.7 | +5.0 (2.7) |

The top fifth's average three-day reaction was +10% to +12%; the bottom fifth's −8% to −10%. Delisting assumptions move nothing (D0 and D100 within 0.2 points). Development passed its gate (positive, t ≥ 1.5). Unseen is positive in 10 of 14 seasons but t = 1.1 in the top 300; the last five seasons, from 2021-08, were −8.0, +0.5, −0.5, +3.8 and −8.2. The drift is there in the wider sample and in the top-minus-bottom spread, and it is roughly half its 2009–2016 size.

### 6.2 Trial 10: combined with the engine's score

Because trial 9 passed on development data, trial 10 was run: the engine's score replaced by the average of its percentile and the percentile of the company's most recent EAR (within 200 trading days; companies with none get 0.5). Placebo: 200 runs with the EAR replaced by random numbers for the same companies.

| Accounts | Size | Engine | Engine + EAR | Δ points | Noise runs: median / 90th | Percentile of noise runs | Max drawdown: engine / combined |
|---|---|---|---|---|---|---|---|
| December, development (Dec 2009 – Dec 2016) | A$25,000 | 10.3% | 10.4% | +0.09 | 6.2% / 9.5% | 96 | −18% / −15% |
| | A$100,000 | 7.2% | 8.8% | +1.55 | 6.8% / 8.4% | 96 | −15% / −13% |
| **December, unseen (Dec 2016 – May 2024)** | A$25,000 | 1.8% | 8.9% | **+7.15** | 5.6% / 8.5% | 92 | −29% / −37% |
| | A$100,000 | 4.7% | 7.8% | **+3.16** | 4.8% / 6.6% | 97 | −27% / −35% |
| *June replication, development (Jun 2010 – Jun 2017)* | A$25,000 | 7.1% | 10.9% | +3.77 | 10.3% / 14.2% | **60** | |
| | A$100,000 | 8.6% | 8.9% | +0.25 | 9.1% / 11.4% | **46** | |
| *June replication, unseen (Jun 2017 – May 2024)* | A$25,000 | 0.2% | 2.7% | +2.43 | 3.6% / 7.8% | **35** | |
| | A$100,000 | 4.7% | 3.7% | −1.05 | 4.5% / 6.9% | **33** | |

On the pre-registered December accounts the combination passed its development gate and then beat more than 90% of the noise runs on unseen data at both sizes. That would have been the strongest result in the programme since H80. So, before believing it, I ran the replication report 56 used for its own shortlisted idea: the same accounts started and reviewed in June. **The advantage disappeared.** In June accounts the combination is in the middle of the noise runs in both periods (60th and 46th percentile; 35th and 33rd). This is post-hoc and logged as an extra look, but it is a test the idea had to pass and did not. It is the same pattern as report 56's C3: ahead in December accounts, inside the noise band in June accounts.

One plausible reason: a December review comes four months after the August results and two months before the February ones, so "most recent EAR" is always the August reaction; a June review uses the February reaction at a similar lag. If the signal were real it should work from either. A dependence on one calendar alignment over seven yearly reviews is what chance looks like.

### 6.3 What the noise runs say about the headline table

In three of the four A$25,000 comparisons the *random* version of the combination beat the engine by 3.2 to 3.9 points a year (in the fourth it trailed by 4.1). A random number adds no information. What it does is push the list toward companies that have an EAR at all, which on this table means companies still listed in 2026. Any test that selects on "has an announcement in the harvest" carries a bias of that order at 10 names. Report 59's users should read its headline-based ideas with that in mind.

**Verdict for A4.** Stand-alone: partly tested; real in development, weaker and not significant in the top 300 since 2017. Combination: passes in December accounts, fails the June replication; not robust. **Closed as an engine input** with report 56's L4. The results-day reaction stays as a measurement line (card H133) to be scored on the forward archive, where every company's results date is recorded on the day.

## 7. A5 — forward archive and red-flag panel (design; no back-test, no trial)

The archive's purpose is narrow: from the day it starts, record what was publicly known on each day about every listed company, including the ones that will later fail or be taken over, so that in three to five years the flags above (and the four measurement cards below) can be scored on data nobody could have rewritten. Section 6.3 shows what the lack of such a record costs: on today's survivors-only headline table, a combination of the engine's score with random numbers beat the engine by 3.2 to 3.9 points a year in three of four A$25,000 accounts.

### 7.1 Two decisions the owner has to make before anything is built

| # | Decision | Why it is needed | Options | My recommendation |
|---|---|---|---|---|
| 1 | Whether the system may fetch announcement lists and PDFs from asx.com.au | Spec DAT-15 has a CI test that fails if the code contains a request to asx.com.au, and report 52 section 3.4 puts scraping asx.com.au in class D (prohibited). Report 61's A5 table lists "ASX announcement list by release date" as a source without resolving this. Five of the nine archive items depend on it | (a) Keep DAT-15: take announcements from a licensed feed (EODHD has no ASX announcement feed that I have verified [unverified]; Market Index, Morningstar or ASX's own ComNews product are paid). (b) Amend DAT-15 for one host and one job, after the ASX terms of use are read and recorded in `kb.source`. (c) Collect only what does not need ASX: ASIC shorts, share counts, listing dates, prices | (c) now, at no cost; (b) only after the terms are read; do not build the announcement jobs until then |
| 2 | Licence class of the ASIC files | The ASIC copyright page could not be opened from the research session (host blocked). The files carry only an accuracy disclaimer | Class B (private use, no redistribution) until the page is read; class A if it turns out to be CC BY | Class B. Store raw files; publish nothing but derived statistics |

Without decision 1(b), cards H134–H136 below cannot be measured and H137's panel shows three flags instead of five.

### 7.2 Collection jobs

All times Australia/Sydney. Every job writes insert-only rows with `recorded_at`; a correction or re-issue is a new row; nothing is overwritten. Each fetch writes a `kb.document` row (URL, `retrieved_at`, SHA-256, bytes, licence class). One request at a time, at least 1.1 seconds between requests to a host. Parsers treat every file as untrusted text (report 52 section 5.4).

| Job | When | Source | Steps | Needs decision 1(b)? | On failure |
|---|---|---|---|---|---|
| `fa_asic_short` | Trading days 11:10; retry 15:10 | `download.asic.gov.au/short-selling/short-selling-data.json`, then `RR{yyyymmdd}-{vvv}-SSDailyAggShortPos.csv` | Read the index; fetch every (date, version) pair not yet stored, including re-issued versions of old dates; store the raw file; parse (UTF-16 tab or ASCII comma, detected from the first bytes) into `fa.short_position` | No | WARN; `fa.gap` row if no new position date for 3 business days (ASIC publishes four business days after the position date) |
| `fa_listing` | First trading day of each month, after `bw_fetch` | The ASX listed-companies file that BW-04 already saves | Diff against last month: new codes (first-seen date = listing date for the age flag), removed codes, name changes into `fa.listing_event` | No (already fetched under BW-04) | WARN |
| `fa_fund_snapshot` | First trading day of each month | Report 58's company database | Dated full copy as a `kb.dataset_snapshot`; changed figures appended to `kb.fundamental` with `recorded_at`, so restatements become visible | No | WARN |
| `fa_headlines` | Trading days 19:45; catch-up 08:20 | ASX announcement list by release date | One list per day: `ids_id`, code, release date and time, headline, price-sensitive flag, pages, into `fa.announcement`; typed by the regex table of `niche/code/parse_ann.py` (version stored with each row) | **Yes** | WARN; `fa.gap` row. A missed day can be re-fetched for about a week from the "previous business days" list; after that it is a permanent gap for delisted companies |
| `fa_parse_3y` | After `fa_headlines` | Appendix 3Y PDFs | Extract director, date of change, nature (on-market or other), number, consideration, holding after; keep facts and file hash, not the PDF (class C) into `fa.director_trade`; unparsed files flagged for the owner | **Yes** | WARN; row with `parse_status = failed` |
| `fa_parse_subst` | After `fa_headlines` | Forms 603, 604, 605 | Holder, previous and present voting power, date of change into `fa.substantial_holding` | **Yes** | As above |
| `fa_parse_issue` | After `fa_headlines` | Appendix 3B, 2A, 3C, 3G, 3H; daily buy-back notices | Type (placement, entitlement, SPP, conversion, buy-back), number, price, date into `fa.capital_change`. Cross-check monthly against the change in ASIC "total product in issue" | **Yes** | As above |
| `fa_parse_cash` | Daily in Jan, Apr, Jul, Oct; weekly otherwise | Appendix 4C and 5B | Cash at quarter end, net operating cash flow, the company's own "estimated quarters of funding" (item 8.5 / 8.7) into `fa.cash_runway` | **Yes** | As above |
| `fa_etf_flows` | Monthly, when the file appears | ASX Investment Products spreadsheet | Whole file stored; funds under management and flows parsed (report 59 has the parser) | **Yes** (same host) | WARN |
| `fa_consensus` | Monthly | Only a feed the owner already licenses | Mean estimate, target price, analyst count into `fa.consensus`. Off by default | No | — |
| `fa_flags` | Trading days 20:30 | The tables above and the price store | Recompute `fa.red_flag` for every company in the top 500 and every owner pick; write one row per (company, flag, day) only when the value or state changes | No | WARN; the panel shows "flags not updated since [date]" |
| `fa_health` | Trading days 20:40 | — | Row counts against the trailing 20-day median; missing days into `fa.gap`; a weekly line in the system report | No | WARN |

Disk: the ASIC history downloaded for this report is 4,151 files and about 200 MB raw (about 15 MB a year compressed). Headlines are about 280 rows a day. Nothing here strains the 2 GB server.

### 7.3 Schema (schema `fa`, beside `kb`; app role INSERT only)

| Table | Columns |
|---|---|
| `fa.short_position` | `position_date`, `code`, `product_name`, `short_qty`, `total_in_issue`, `pct_reported` (as printed), `file_version`, `doc_id`, `recorded_at`. PK (`position_date`, `code`, `file_version`) |
| `fa.announcement` | `ids_id` PK, `code`, `released_at` (date and time), `headline`, `price_sensitive`, `pages`, `doc_type`, `type_rule_version`, `doc_id` (the day list), `recorded_at` |
| `fa.director_trade` | `ids_id`, `code`, `director`, `change_date`, `nature` (on-market buy, on-market sell, off-market, issue, exercise, other), `number`, `consideration_aud`, `held_after`, `parse_status`, `file_sha256`, `recorded_at` |
| `fa.substantial_holding` | `ids_id`, `code`, `holder`, `form` (603, 604, 605), `change_date`, `prev_pct`, `present_pct`, `parse_status`, `file_sha256`, `recorded_at` |
| `fa.capital_change` | `ids_id`, `code`, `kind`, `number`, `price_aud`, `effective_date`, `parse_status`, `file_sha256`, `recorded_at` |
| `fa.cash_runway` | `ids_id`, `code`, `quarter_end`, `cash_aud`, `net_operating_cf_aud`, `quarters_funding_stated`, `quarters_funding_computed`, `parse_status`, `file_sha256`, `recorded_at` |
| `fa.listing_event` | `code`, `event` (first seen, removed, name change), `valid_at`, `name`, `industry_group`, `doc_id`, `recorded_at` |
| `fa.consensus` | `code`, `as_of`, `item`, `mean`, `n_analysts`, `target_price`, `source_id`, `recorded_at` |
| `fa.red_flag` | `entity_id`, `as_of`, `flag` (SI, ISSUE, AGE, RUNWAY, RAISE), `value`, `threshold`, `state` (set, clear, unknown), `data_date`, `rule_version`, `recorded_at`. PK (`entity_id`, `flag`, `as_of`) |
| `fa.pick_flag_snapshot` | `pick_id`, `flag`, `state`, `value`, `data_date`, `frozen_at`. Written once, at the pick's logging time; never updated |
| `fa.gap` | `source`, `missing_date`, `reason`, `backfilled` (bool), `recorded_at`. A backfilled day is kept but marked, and is excluded from any later honest test for companies no longer listed on the backfill date |

Code-to-company mapping uses `kb.entity` (code changes continue the entity), as the engine's rule A2 does.

### 7.4 Flag rules (rule version 1; frozen with this report)

| Flag | Set when | Data | "Unknown" when |
|---|---|---|---|
| SI | Short interest (five-day mean of reported short positions ÷ total product in issue, usable five trading days after the position date) is in the top decile of the top 300 by traded value. For a company outside the top 300: at or above that day's top-300 cut-off | `fa.short_position` | No file in the last 15 trading days |
| ISSUE | Split-adjusted total product in issue is more than 20% above its level 12 months earlier (report 61's panel threshold; the back-tested rule in section 4 is the top fifth of the top 300, whose cut-off averaged +9% to +10%. I recommend the panel use the tested rule and print the percentage, so the owner sees both) | `fa.short_position`, split factors from the price store | Company not in the ASIC file on either date |
| AGE | Fewer than 504 trading days since the company's first trade (demerged children excluded) | Price store; `fa.listing_event` from now on | Never |
| RUNWAY | The latest Appendix 4C or 5B shows fewer than four quarters of funding | `fa.cash_runway` | No 4C/5B on file (most top-300 companies do not lodge one: shown as "not applicable") |
| RAISE | A headline typed guidance-downgrade, or a trading halt followed within five trading days by a placement, entitlement or SPP headline, in the last six months | `fa.announcement` | Announcement jobs not running |

### 7.5 The panel on "Your picks, honestly"

A new part 5a, after "Thesis checks that fell due this month" (report 53 section 6.4), and the same block beside each name on the Big Wins paper list.

- **One row per open pick, in order of purchase date** (the report's existing rule; never sorted by flag count or result). Columns: company; the five flags as at the pick's logging day (from `fa.pick_flag_snapshot`); the five flags today; the value behind each set flag ("short interest 9.4%, top-300 cut-off 6.1%"; "shares on issue +31% in 12 months"; "listed 14 months"); the data date of each.
- **States are words: "set", "clear", "unknown", "not applicable".** No colours that read as buy or sell, no score, no ranking.
- **A fixed evidence line under the table**, taken from this report and not updated by the system: "Top-300 companies, 2017–2023, next 12 months, against the rest of the top 300. Share count up about 10% or more in a year: 3.5 points lower return (t −2.2; 14.8 points lower in 2011–2016); 13.5% halved against 6.2%. Listed under two years: 8.9 points lower (t −1.5, not conclusive); 24% halved against 7%. Short interest in the top tenth: no reliable difference in return (+2.4 points, t 0.5); 15% halved against 7%, and 5% doubled against 3%. Runway and raising flags: not tested; no honest history exists yet."
- **A fixed caution line:** "A flag is a fact about the company, not a forecast. None of these flags passed the test for changing what the engine buys (report 62)."
- **Outcome by number of flags** (card H137): shown only once there are at least 20 closed picks or 36 months; until then the line reads "Too few picks to say whether flagged picks did worse."
- **The panel never blocks, delays or resizes an order**, and no flag state is readable by the trader role (report 52's separation rule). On the Big Wins paper list the flags are shown beside the names the engine chose; the engine does not see them.
- **Staleness:** if `fa_flags` has not run for three trading days the panel prints "flags not updated since [date]" in place of today's column.

### 7.6 Measurement cards (scoreboard lines; no money, no gates, not trials)

Renumbered from report 61's provisional H114–H117 because report 59 reserves H100 onward and the drivers pre-registration reserves H120 onward.

| Card | Was | What is measured | Comparison | Starts | First formal look |
|---|---|---|---|---|---|
| **H134** | H114 | Clustered director buying: two or more directors buying on-market, A$100,000 or more in total, within 30 days, company in the top 500. 12-month price return from the fifth trading day after the second notice | XJO; and one random top-500 company from the same traded-value band on the same day (drawn and stored when the event is logged) | When `fa_parse_3y` has run for a month without gaps | 36 months, then 60 |
| **H135** | H115 | Cash runway under four quarters at a 4C/5B lodgement: 12-month excess return; share that announce a raising within 12 months; share suspended or delisted | Lodgers with four or more quarters, same quarter | When `fa_parse_cash` starts | 36 months |
| **H136** | H116 | A new substantial holder (form 603) from a fixed list of small-cap specialist managers. The list is written by the owner and hashed **before** `fa_parse_subst` first runs; additions apply only to later notices | Other 603 notices in the same traded-value band and quarter | When the list is hashed | 36 months |
| **H137** | H117 | Red-flag count on owner picks and on the engine's paper list: number of flags set on the logging day (section 7.4), then the 12-month return against the index twin, by flag count 0, 1, 2+ | Picks with no flag | Now for SI, ISSUE, AGE; later for RUNWAY, RAISE | 20 closed picks or 36 months |

Each card records, when registered, the rule version, the start date and the number of events expected a year, and is scored only on events after its start date (report 52, LE-18). The back-tests in this report are the cards' prior evidence, not part of their record.

## 8. Cards, trial count, looks and deviations

### 8.1 Cards

Report 61's provisional numbers H110–H117 are replaced by **H130–H137**. Reason: report 57 uses H95–H100, report 59's pre-registration reserves H100 onward for its survivors, and the drivers pre-registration (report 60) reserves H120 onward. Reports 58–60 were not in `research2/` when this was written, so the H130 block is chosen to be clear of all three.

| Card | Was | Idea | Result here | Status |
|---|---|---|---|---|
| H130 | H110 | Short interest in the top tenth as an exclusion | X1 −5.0 (t −1.3) then +2.4 (t 0.5); X2 −0.04 / −0.13 | Closed as a rule. Panel fact (tail risk only) |
| H131 | H111 | Share count up, top fifth, as an exclusion; shrinkers as a positive | X1 −14.8 (t −5.0) then −3.5 (t −2.2); X2 −0.16 / −0.15. Shrinkers +10.4 then −2.4 | Closed as a rule. **Panel flag with evidence.** Shrinkers closed |
| H132 | H112 | Listed under 504 trading days as an exclusion | X1 −4.9 (t −1.4) then −8.9 (t −1.5); X2 −0.35 / −0.05 | Closed as a rule. Panel flag, "not conclusive" |
| — | — | Composite of the three | X2 −1.03 / −0.98 | Closed |
| H133 | H113 | Results-day reaction | Drift +4.7 (t 2.8) then +1.8 (t 1.1); combination fails the June replication | Closed as an engine input. Measurement line on the forward archive |
| H134–H137 | H114–H117 | Forward measurement cards | Section 7.6 | Open; start with the archive |

No card from this report goes onto the paper book as a challenger. Report 61 allowed "promising" flags a shadow-challenger slot; I recommend against using it, because for each flag the exclusion test has already been run on unseen data and showed nothing, and a paper challenger at 10 to 30 names would need decades to show a difference that the back-test puts at −0.4 to +0.0 points.

### 8.2 Trials and looks

- **Trials: 10**, as pre-registered (A1: X1, X2; A2: X1, X2, shrinkers; A3: X1, X2; composite; A4: trials 9 and 10). **Programme count: 358 + 10 = 368.** All deflated Sharpe ratios above use N = 368; with N = 1,000 the highest unseen value (A3 X1, 0.54) becomes 0.48 and the dilution X1 becomes 0.34. No unseen series reaches 0.95.
- **Looks at unseen data** (`flags/out/looks.csv`): one planned look each for A1, A2, A3, the composite, A4 trial 9 and A4 trial 10; one accidental look (D4); one bug-fix re-run each for A2 and the composite (D9); one post-hoc replication (A4, June accounts). So A2 and the composite have been looked at twice, with near-identical flags.
- Not trials, by the convention of reports 51 and 53: placebos (16,000 uniform and 3,200 rank-matched engine runs, plus the same again for the D9 re-run of A2 and the composite; 800 noise runs for A4 and 800 for its replication), delisting variants, the CDI sensitivity, the raw-code age variant, the 301–500 table, the absolute and 3-month short-interest secondaries.

### 8.3 Deviations from the pre-registration

| # | What | Effect |
|---|---|---|
| D1 | Request starts 1.1 s apart, not 1.1 s after each response | None on results |
| D2 | A2's "hand" reconciliation written as rules and logged, before returns | The flag includes deep-discount raisings and recapitalisations, as section 5 of the pre-registration intends. A first draft that set them to missing was replaced before any return was read |
| D3 | CDI-excluded sensitivity added before returns | Reported beside the trials; same conclusions |
| D4 | Accidental look at a test flag file built from the partial download | Discarded; nothing tunable |
| D5 | Six trading days with no price rows; four bad ASIC files | Those days unused |
| D6 | A4 trial 10 unseen account opened after the development gate passed; June replication run after seeing it | Replication is post-hoc and is what closed the idea |
| D7 | A4 trial 9 unseen pass mark taken by analogy (t ≥ 2.0) | Not met in the top 300 |
| D8 | "X1 passes, X2 fails" named "stand-alone effect confirmed; exclusion not passed" | Applies to A2 |
| D9 | Bug in the reconciliation: a count jump across a gap in the ASIC file was compared with the price move over the whole gap, so 10 splits already in the factor table were applied twice. Fixed; A2 and the composite re-run | 6 of 8,521 flag memberships changed. Unseen X1 −3.5 (t −2.24) before, −3.5 (t −2.22) after; no X2 figure moved by more than 0.01 point. First-run files kept as `*_v1_prebugfix.*` |

## 9. Data findings for reports 53, 58 and 59

These came out of matching the ASIC files to the price panel. None was corrected in the frozen engine data.

1. **The price panel has no rows for 31 October to 4 November 2016** (a whole trading week, every company) or for 29 May 2020. The engine's October 2016 month-end is therefore 28 October. It affects every report built on `company_study/data`.
2. **Eleven price-panel "splits" that the share count contradicts**: the count rose by far more or less than the factor implies. Most are deep-discount rights issues where the panel applies a bonus-element adjustment (KMD, WEB, OML and DCN in March–April 2020; SKT; AIZ 2022), which is defensible for returns. **GCY (April 2019)** has a 2-for-1 split in the panel where the share count rose 15%, and **VMG (October 2011)** a 3-for-1 where the count rose 383%; both deserve a look by whoever maintains the panel.
3. **Eighteen consolidations where the panel's ratio differs from the count's whole-number ratio** (for example MDL 2010: panel 4, count 10; AOG 2012: panel 6, count 7; EGG 2012: panel 15, count 18). The panel's ratios came from a price heuristic; where a consolidation coincided with a distribution or an issue the heuristic picks the wrong whole number. The return effect is small when a real price move explains the gap, but the list is in `flags/out/a2_reconcile.csv` for checking.
4. **Twenty-three price factors are distributions or demergers**, not splits (AIX, WPG, EXS, TAH and others). Correct for returns; they must not be applied to share counts. Report 58's reconciliation column against ASIC should start from the rule file `flags/out/a2_reconcile.csv`. An earlier draft of this report listed ten splits "missing from the price panel"; that was the bug of deviation D9, and the panel was right.
5. **Companies missing from the price panel for years in which ASIC shows them trading**: AAC before August 2014, AAD before March 2012, among others (`flags/out/asic_unmatched_codes.csv`). These are holes in the "all companies including delisted" claim of the panel.
6. **Survivorship in the headline table** is large enough to move a 10-name account by three to four points a year (section 6.3).
7. **ASIC re-issues files.** 345 of 4,151 dates have a version above 001, 156 of them in 2023. Only the latest version is offered. The forward archive (section 7) keeps every version as it appears.
8. **Aggregate short interest for report 60** can be built from `flags/out/asic_long.pkl` (code, date, short, total) without another download.

## 10. Reasons this could be wrong

- **Thirteen years is short for an exclusion test.** A flag worth one point a year to a 30-name book cannot be seen in seven yearly reviews; the placebo bands are ±1.2 to ±2.3 points wide. "Not passed" means "no evidence of help", not "proven useless". The stand-alone tables are the better evidence, and they say dilution matters and short interest does not.
- **Equal-weight, price-only, 12-month returns.** Value-weighted or dividend-inclusive returns could differ. McLean, Pontiff and Watanabe's issuance effect is weaker value-weighted; ours is equal-weight within the top 300 only.
- **The dilution effect may be a resources-cycle effect.** It was four times larger in 2011–2016. The unseen figure is the one to use, and it rests on six Decembers.
- **The reconciliation rules could misclassify.** A consolidation with a simultaneous issue keeps the price panel's factor, which report 51 chose from price behaviour; if that factor is wrong the company's NI is wrong for a year. There are 13 such cases, mostly outside the top 300. One rule already had a bug (D9); there may be others I have not found, though the six-in-8,521 effect of that one suggests the flag is not sensitive to them.
- **The top tenth by short interest is a blunt cut.** A different cut (top 10 names; days to cover) might behave differently. I did not look, and looking now would be a new trial on used data.
- **Revised ASIC files** were used where ASIC replaced the original (345 dates). If revisions correct errors that short sellers could not have known, the short-interest test had slightly better data than a live user. This would favour the flag, and it still failed.
- **A4's replication is post-hoc.** Had I pre-registered June accounts and not December ones, the idea would have been closed at the development gate with no fuss. The December result may be the true one and June the unlucky one. Two calendars and 14 reviews cannot tell; the forward archive can.
- **The licence position is unread.** If ASIC's terms forbid storage of the daily files, the archive job for them must go and the raw files here must be deleted, keeping hashes and derived results (report 52, section 3.5).

## 11. Files

All under `scratchpad/flags/` (absolute path: `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/flags/`).

- `PREREG_FLAGS.md` (frozen copy `out/PREREG_FLAGS_frozen.md`, hash and time in `out/prereg_flags_hash.txt`; deviations appended in section 10).
- `raw/sample/` (six verification files), `raw/terms/short-selling-data.json`, `raw/asic/` (4,151 CSV files, 229 MB), `raw/manifest.tsv`, `raw/manifest_samples.tsv`.
- `code/`: `bw_frozen/engine.py` (unmodified copy), `flib.py` (wrapper, X1, X2, placebos, DSR), `fetch_asic.sh`, `build_map.py`, `build_asic.py`, `a12.py` (A1, A2, composite, reconciliation), `a3.py`, `a4.py`, `a4_rep.py`, `overlap.py`, `secondary.py`, `tables.py`. Hashes: `out/code_hashes.txt`.
- `out/`: `trials_62.csv`, `looks.csv`, `a1_*.json`, `a2_*.json`, `a3_*.json`, `comp_*.json`, `a4_*.json`, `a4_replication_june.json`, per-formation CSVs (`*_x1_*.csv`, `a2_shr_*.csv`, `a4_t9_*.csv`), `a2_reconcile.csv`, `a2_reconcile_list.csv`, `overlap.csv`, `secondary_flags_by_year.csv`, `asic_parse_log.csv`, `asic_unmatched_codes.csv`, `asic_long.pkl`, `asic_wide.pkl`, flag sets (`a12_flags.pkl`, `a3_flags.pkl`), `output_hashes.txt`.

Sources: ASIC short-position files and index (URLs in section 1); report 61 for the designs and its literature list; reports 51–56 for the engine, conventions and the noise floor; `niche/out/events.csv.gz` (report 59's harvest) for A4. ASIC copyright page located by search only: https://asic.gov.au/copyright (not opened).
