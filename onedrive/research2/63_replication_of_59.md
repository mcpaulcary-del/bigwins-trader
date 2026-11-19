# 63 — Independent replication of report 59 (cards H100 and H101)

Date: 2026-11-14. Status: validator's report. Research use only; general information, not financial advice.
Validator's code and outputs: `scratchpad/replication_59/` (`code/`, `out/`, `out_frozen/`). Builder's material: `scratchpad/niche/`.

## 0. Answer first

**H100 (June tax-loss rebound) is reproduced. H101 (steady winners in ranks 301–1000) is reproduced in sign only: its unseen figure moves between +2 and +7 points a year on choices the rule text does not settle, and never reaches t = 1.5.**

| Question | Answer |
|---|---|
| H100, blind build, net of costs minus XJO | Development 2004–2015: **+2.4%** (t = 1.1, 8 of 12 years ahead). Unseen 2016–2023: **+6.0%** (t = 2.4, 6 of 8). Report 59: +2.5% (1.1, 7 of 12) and +6.0% (2.2, 6 of 8). **REPLICATED** |
| H101 card form (N4: price ≥ 50c, ≥ A$50,000 a day), blind build | Development 2003–2015: +12.4 points a year (t = 1.7). Unseen 2016–2022: **+5.6** (t = 1.4, 5 of 7). Report 59: +13.5 (1.6) and +3.7 (0.9, 4 of 7). **CLOSE** |
| H101 wider form (N1, the report's headline) | Development 2000–2015: +14.7 (t = 2.9, 13 of 16). Unseen: **+2.4** (t = 0.5, 5 of 7). Report 59: +18.8 (3.4, 14 of 16) and +6.0 (1.2, 3 of 7). Development **CLOSE**; unseen **NOT REPLICATED** as "promising" (the registered label needs t between 1.0 and 2.0) |
| Why the differences | Five reading choices in the builder's code that the registration does not state (section 4). With all five switched on, my engine matches every yearly figure of the builder's to within 0.25 points, for both cards |
| Is the builder's code faithful to the registration? | Mostly. One data defect: 256 companies whose ASX code changed after April 2020 have no raw price or turnover history before the change in the builder's files, so they drop out of earlier universes. Three departures from the registered text (section 5) |
| Stress tests, H100 | Keeps its sign with a 10c price floor, position sizes A$1,000–5,000, the harshest delisting rule, trimming of extremes, and ±3 days on the exit. Does not survive doubled spreads in development (−0.1%), a 20c price floor (−0.1% development, +2.3% unseen), or buying 3 days early in development (−0.2%). June is first of 12 start months in both periods; the other 11 all lose |
| Stress tests, H101 | Costs and timing barely matter (12-month hold). Unknown delistings at zero: card form +1.9, wider form −2.9 in unseen. Median pick lags XJO by 4.6 to 6.1 points a year in unseen. Same rule formed in March, June or September: unseen −3.6 to +1.4 |
| Paper forward test? | **H100: yes**, with the guard rails in section 8. **H101: only as a no-cost tracking line beside H82**, not as a candidate; the evidence does not support "promising" |

## 1. What was done, in order

1. **Blind build.** Read only sections 0, 5 and 6 of `niche/PREREG_59.md` (lines 1–57 and 147–178; the frozen copy hashes to `dcabd05e…`, as report 59 states) and the cleaned panel of report 51 (`company_study/data`: `P.pkl`, `V.pkl`, `stage1.pkl`, `index.pkl`, `delist.pkl`). Read `company_study/code` for file formats and for report 51's score definitions (`cohorts.py`), which the registration cites. Did not open report 59, `niche/out`, `niche/code`, the deviations section of the registration or any trials file.
2. **Step 1 freeze.** Base results for both exits of H100 (end July, end August) and both forms of H101, written to `out_frozen/step1/`. SHA-256 of the file list: `f43483c4…766baf8d`.
3. **Step 2 freeze.** Stress tests, still blind, written to `out_frozen/step2/`. SHA-256 of the file list: `71d91c56…1e9fb`.
4. **Step 3.** Opened report 59, `niche/out` and `niche/code`. Compared name by name, then switched the builder's conventions on one at a time in my engine (`code/recon_attrib.py`).

I did not know which exit was card H100 or which form was card H101 while blind, so both were built. The card says: H100 = sell end of July; H101 = the N4 form, with N1 as a reference.

The task asked for development 2004–2015. Before June 2004 fewer than 30 companies meet the H100 universe rule (2001: 18 companies, 3 losers, −18.1% against XJO; 2003: none), and XJO in the index file starts in November 2000. The builder made the same cut (registration deviation 10.2, read at step 3). For H101 both 2000–2015 and 2004–2015 are shown.

## 2. Headline comparison

"Mine" is the frozen blind figure. Returns are means across years (one observation a year); t-statistics are across years.

### 2.1 H100 — June tax-loss rebound, sell end of July

| Figure | Report 59 | Mine | Verdict |
|---|---|---|---|
| Stocks per year, development / unseen | 40 / 60 | 42 / 66 | CLOSE (universe 10–15% larger, section 4) |
| Gross return, about 5 weeks | +7.9% / +12.2% | +7.8% / +12.1% | REPLICATED |
| XJO same days | +2.3% / +2.9% | +2.3% / +2.8% | REPLICATED |
| Gross minus XJO (t) | +5.7% (2.4) / +9.4% (3.1) | +5.5% (2.5) / +9.3% (3.5) | REPLICATED |
| Gross minus all small caps in the universe (t) | +2.5% (2.2) / +5.4% (2.4) | +2.8% (2.6) / +5.7% (2.9) | REPLICATED |
| **Net of costs minus XJO (t), development** | **+2.5% (1.1)** | **+2.4% (1.1)** | REPLICATED |
| **Net of costs minus XJO (t), unseen** | **+6.0% (2.2)** | **+6.0% (2.4)** | REPLICATED |
| Pooled 20 Junes | +3.9% (2.2) | +3.8% (2.3) | REPLICATED |
| Years ahead of XJO after costs | 7 of 12; 6 of 8 | 8 of 12; 6 of 8 | REPLICATED (2010 is +0.0% in mine, −0.7% in the builder's) |
| June's rank among 12 start months | 1st; 1st | 1st; 1st | REPLICATED |
| June minus the other 11 months, against the universe (t) | +4.5% (3.5) / +6.9% (2.7) | +4.6% (3.3) / +6.8% (3.2) | REPLICATED |
| Random same-size draws from the universe (2,000) | Beat all 2,000 | 99.9th percentile (development), 100th (unseen) | REPLICATED |
| Sell end of August instead | +1.1% (0.4) / +4.8% (1.7) | +1.1% (0.4) / +3.8% (1.6) | REPLICATED / CLOSE |
| Price ≥ 20c | −0.1% / +3.7% (1.4) | −0.1% / +2.3% (1.1) | REPLICATED / CLOSE (different definition, section 4) |
| Same rule in the top 300 | Negative after costs | −0.2% / −0.2% | REPLICATED |
| Winners in the same universe, net | Nothing / +1.5% | −1.0% / +1.4% | REPLICATED |
| Worst year | −13.3% (2012) | −11.4% (2012) | CLOSE |
| Largest yearly gap between the two builds | — | 3.9 points (2009: −2.9% builder, −6.8% mine; 25 names) | Explained in section 4 |
| Median half-spread per side | 1.15% | 1.05% / 1.10% | REPLICATED |
| Largest single stock return; data-error flags | +137%; none | +137%; none | REPLICATED |
| Delisted inside the hold | 4 of 958 | 7 of 1,039 | REPLICATED |
| "A$2,500 fits every name" at 5% of a day's value | 100% | 76% development, 81% unseen | **NOT REPLICATED** (section 5) |
| A$10,000 fits | 10% / 29% | 11% / 23% | CLOSE |

### 2.2 H101 — steady winners in ranks 301–1000, December cohorts

| Figure | Report 59 | Mine | Verdict |
|---|---|---|---|
| N1 names held, development / unseen | 19 / 32 | 23 / 36 | CLOSE (universe 25% larger) |
| N1 top tenth, 12 months, gross | +25.9% / +12.9% | +21.7% / +8.7% | Differs by 4 points |
| All of the universe | +8.1% / +1.9% | +7.2% / +1.1% | REPLICATED |
| XJO | +5.0% / +4.9% | +5.2% / +4.7% | REPLICATED |
| N1 gross minus universe (t) | +17.8 (3.4) / +11.0 (2.3) | +14.5 (2.7) / +7.6 (2.2) | CLOSE |
| **N1 net minus XJO (t), development 2000–2015** | **+18.8 (3.4)** | **+14.7 (2.9)** | CLOSE (same sign, both clear the development bar) |
| **N1 net minus XJO (t), unseen** | **+6.0 (1.2)** | **+2.4 (0.5)** | **NOT REPLICATED** as "promising" |
| N1 years ahead of XJO | 14 of 16; 3 of 7 | 13 of 16; 5 of 7 | Three unseen years sit within 2 points of zero in both builds |
| N1 median stock minus XJO | +11.8 / −3.8 | +5.9 / −6.1 | Same message |
| N1 unknown delistings at zero, unseen | 0.0 | −2.9 | Same message |
| **N4 net minus XJO (t), development 2003–2015** | **+13.5 (1.6)** | **+12.4 (1.7)** | CLOSE |
| **N4 net minus XJO (t), unseen** | **+3.7 (0.9)** | **+5.6 (1.4)** | CLOSE (1.9 points; neither passes) |
| N4 years ahead | 10 of 13; 4 of 7 | 10 of 13; 5 of 7 | CLOSE |
| N4 unknown delistings at zero, unseen | +0.2 | +1.9 | CLOSE |
| N1, all monthly formations, Newey–West t | +15.0 (4.8) / +1.6 (0.9) | +15.0 (5.1) / +0.6 (0.3) | REPLICATED / CLOSE |
| Low volatility alone (N3), unseen | −7.7 (t = −3.9) | −6.0 (t = −2.8) | CLOSE |
| Momentum alone (N2), unseen | +3.0 | −2.4 | Sign differs; neither is distinguishable from zero |
| Random decile-size draws, unseen (percentile of the strategy) | not stated per period | N1 94.5th, N4 94.4th (2,000 draws) | Just under the registered 95th |

Development 2004–2015 only (the window the task asked for): N1 +8.7 (t = 2.0, 9 of 12); N4 +16.7 (t = 2.6, 10 of 12). The four cohorts of 2000–2003 hold 10–15 names each and add 6 points to N1's development mean.

## 3. Does report 59's conclusion stand?

- **H100: yes.** "Not passed, promising, the strongest candidate" is what the blind build shows. Development t is 1.1 against a registered bar of 1.5.
- **H101: partly.** "Not passed" stands. "Promising" does not hold for the N1 headline in my build (t = 0.5). For the N4 form on the card it is the other way round: mine has t = 1.4, the builder's 0.9, which is below his own "promising" threshold of 1.0. The honest range for the unseen edge is +2 to +7 points a year with t between 0.5 and 1.4.

## 4. Where the differences come from

Each row switches on one more of the builder's conventions in my engine. Figures are net of costs minus XJO, mean across years.

**H100**

| Version | Development | Unseen | Largest yearly gap to the builder |
|---|---|---|---|
| Mine, as frozen | +2.4% (t 1.1) | +6.0% (t 2.4) | 3.9 points |
| + universe measured the day before the buy, and only companies that traded that day | +3.0% (1.4) | +6.2% (2.3) | 1.5 |
| + builder's raw files (renamed companies lose their history) | +2.5% (1.1) | +6.1% (2.2) | 0.2 |
| + buy at the next traded close within 5 days if no trade on the day | +2.5% (1.1) | +6.1% (2.2) | 0.1 |
| Builder | +2.5% (1.1) | +6.0% (2.2) | — |

Names held by both builds have the same net return to 0.1 points in every year. All of the gap is which companies are in the universe: mine has 10–15% more, so the worst-fifth cut-off moves and 2–8 names a year differ.

The "price ≥ 20c" line differs for a separate reason. The builder keeps the losers picked from the 5c universe and drops those under 20c. I re-form the worst fifth inside a 20c universe. Both are fair readings.

**H101, wider form (N1)**

| Version | Development 2000–15 | Unseen | Largest yearly gap |
|---|---|---|---|
| Mine, full round-trip cost on every name | +14.6 (t 2.9) | +2.2 (t 0.5) | 12.7 points |
| + only companies that traded on the formation day; missing scores dropped | +18.9 (3.5) | +2.8 (0.6) | 14.0 |
| + builder's raw files (renamed companies lose their history) | +19.9 (3.5) | +3.6 (0.9) | 19.2 |
| + momentum measured 21/126/252 trading days back instead of month-ends | +19.3 (3.4) | +7.1 (1.4) | 4.9 |
| + sell after 252 trading days; buy at next traded close | +18.9 (3.4) | +6.0 (1.2) | 0.2 |
| Builder | +18.8 (3.4) | +6.0 (1.2) | — |

**H101, card form (N4)**: the same steps take mine from +12.3 / +5.5 to +13.6 / +3.7 (builder +13.5 / +3.7), largest yearly gap 0.2 points.

Three things stand out.

1. **The December 2020 cohort decides the N1 unseen figure.** Changing the momentum look-back by a day or two moves that one cohort from +6.5 to +25.4 points. Two companies (NMT, +316%; CXL, +514%) sit at the edge of the top tenth: ranked at the 90.0th and 85.3rd percentile in my build, inside the top tenth in the builder's. In the builder's cohort of 38 names, the best three supply 29 of the 36 points of return.
2. **Companies that did not trade on the last day of December were poor picks before 2016.** Keeping them (my reading) costs 4 points a year in development and nothing in unseen.
3. **With the builder's five conventions my engine reproduces his yearly figures to 0.25 points.** His code does what it does consistently; the gaps are reading choices, not arithmetic.

## 5. Other findings from reading the builder's code

1. **Data defect: renamed companies lose their history.** `niche/code/build_base.py` maps raw prices to companies with the stage-1 link file only. Report 51's stage 2 added 256 more links for code changes before 2001 and after April 2020 (for example WPL→WDS, CTX→ALD). In the builder's raw-close and traded-value files those 256 companies have no data before the change: 325,000 company-days where the adjusted price exists and the raw data does not. They fail the "200 traded days" test and are left out of every earlier universe. This uses a future event (a later rename) to decide membership. Measured effect: H100 development +3.0% → +2.5%, unseen unchanged; N1 +1.1 development, +0.8 unseen; N4 +2.4 development, +0.3 unseen. It also removes large companies from the top 300, which shifts every rank by a few places.
2. **Capacity is measured on the wrong window.** The registration says 5% of the median daily value over the trailing 63 days. The builder uses the 252-day median, which the universe rule already forces above A$50,000, so "A$2,500 fits every name" is true by construction. On the registered 63-day measure 24% of June losers in development and 19% in unseen cannot take A$2,500. Registered condition (e) asks for 80%: failed in development, met by a point in unseen. Capping each position at 5% of the 63-day value does not change the return (+2.2% / +6.1%).
3. **H101 holds 252 trading days, not 12 months.** That exit falls 2–4 trading days before the anniversary. The card says "12 months and one day". Effect on return about 1 point in unseen; it matters more for tax if the 12-month line ever counts.
4. **H101 costs.** The registration says costs on the names that leave. The builder charges every name a full round trip every year. Only 10% of names carry over, so the difference is 0.2 points; the builder's choice is the conservative one.
5. **Delisting look-up window.** The builder matches a delisting reason within 900 days of the last trade; I used 1,500 (report 51's convention). No measurable effect.
6. **Spread model.** The builder averages the last 63 days on which the stock traded and lags the estimate two days; I average the last 63 calendar trading days. Median half-spread 1.15% against 1.05–1.10%. No measurable effect on the conclusions.

## 6. Stress tests (blind, frozen before step 3)

Net of costs minus XJO, mean across years in % (t), then years ahead. Development is 2004–2015 throughout.

### 6.1 H100

| Test | Sell end July (T1): dev 2004–15 | Sell end July (T1): unseen | Sell end August (T2): dev 2004–15 | Sell end August (T2): unseen |
|---|---|---|---|---|
| Base (5c floor, A$2,500, D30) | +2.4 (1.1), 8/12 | +6.0 (2.4), 6/8 | +1.1 (0.4), 6/12 | +3.8 (1.6), 5/8 |
| price ≥ 10c | +1.5 (0.8), 7/12 | +5.2 (2.2), 6/8 | +0.2 (0.1), 7/12 | +3.6 (1.9), 6/8 |
| price ≥ 20c | −0.1 (−0.1), 6/12 | +2.3 (1.1), 4/8 | −1.0 (−0.5), 4/12 | +1.5 (1.1), 6/8 |
| A$1,000 per name, no ADV cap | +1.6 (0.7), 7/12 | +5.2 (2.1), 6/8 | +0.3 (0.1), 6/12 | +3.0 (1.3), 5/8 |
| A$1,000 per name, 5% ADV cap | +1.5 (0.7), 7/12 | +5.2 (2.1), 6/8 | +0.2 (0.1), 6/12 | +2.9 (1.2), 5/8 |
| A$2,500 per name, 5% ADV cap | +2.2 (1.0), 7/12 | +6.1 (2.4), 6/8 | +1.1 (0.3), 6/12 | +3.9 (1.6), 5/8 |
| A$5,000 per name, no ADV cap | +2.7 (1.2), 8/12 | +6.3 (2.5), 6/8 | +1.4 (0.4), 7/12 | +4.0 (1.7), 5/8 |
| A$5,000 per name, 5% ADV cap | +2.5 (1.3), 9/12 | +6.2 (2.5), 6/8 | +1.6 (0.5), 6/12 | +4.1 (1.8), 5/8 |
| delisting unknown = −100% (D100) | +2.1 (0.9), 8/12 | +5.9 (2.4), 6/8 | +0.7 (0.2), 6/12 | +3.5 (1.5), 5/8 |
| delisting at last price (D0) | +2.7 (1.3), 8/12 | +6.1 (2.4), 6/8 | +1.8 (0.6), 7/12 | +3.9 (1.7), 5/8 |
| spreads doubled | −0.1 (−0.0), 7/12 | +3.4 (1.4), 5/8 | −1.4 (−0.5), 5/12 | +1.2 (0.6), 4/8 |
| spreads doubled + ≥ 20c | −2.0 (−1.4), 5/12 | +0.4 (0.2), 4/8 | −2.9 (−1.5), 4/12 | −0.4 (−0.3), 4/8 |
| entry 3 days earlier | −0.2 (−0.1), 8/12 | +4.5 (1.8), 6/8 | −1.0 (−0.4), 5/12 | +2.2 (1.0), 5/8 |
| entry 3 days later | +3.2 (1.3), 8/12 | +5.3 (2.3), 6/8 | +1.7 (0.5), 7/12 | +2.7 (1.1), 4/8 |
| exit 3 days earlier | +3.3 (1.6), 10/12 | +5.3 (2.6), 7/8 | +0.2 (0.1), 6/12 | +4.1 (1.7), 5/8 |
| exit 3 days later | +1.8 (0.9), 8/12 | +5.3 (2.5), 6/8 | +1.4 (0.4), 6/12 | +3.7 (1.6), 5/8 |
| control: winner quintile | −1.0 (−0.6), 4/12 | +1.4 (0.7), 5/8 | −1.4 (−0.5), 7/12 | +4.9 (1.5), 5/8 |
| control: rank 1-300 losers | −0.2 (−0.1), 6/12 | −0.2 (−0.1), 4/8 | −0.5 (−0.2), 6/12 | −0.8 (−0.6), 3/8 |
| top/bottom 1% of position returns: drop | +2.0 (1.1), 8/12 | +5.4 (2.5), 6/8 | +0.1 (0.0), 6/12 | +2.4 (1.3), 5/8 |
| top/bottom 1% of position returns: winsorise | +2.3 (1.2), 8/12 | +6.0 (2.4), 6/8 | +1.0 (0.4), 7/12 | +3.0 (1.5), 5/8 |
| median position instead of mean | −0.9 (−0.5), 6/12 | +2.2 (1.0), 5/8 | −2.8 (−1.3), 5/12 | +0.1 (0.0), 5/8 |

Start-month placebo, same rule started on the 4th-last trading day of each month and sold at the end of the next:

| Start month | Dev 2004–15: net minus XJO (t) | Years ahead | Unseen 2016–23: net minus XJO (t) | Years ahead | Unseen: net minus universe |
|---|---|---|---|---|---|
| Jan | −5.8 (−3.3) | 2/12 | −6.7 (−2.1) | 1/8 | −4.4 |
| Feb | −5.7 (−2.2) | 1/12 | −6.2 (−4.0) | 0/8 | −4.1 |
| Mar | −5.6 (−2.0) | 3/12 | −1.4 (−0.3) | 1/8 | −2.3 |
| Apr | −6.2 (−3.3) | 2/12 | −6.9 (−4.1) | 1/8 | −6.0 |
| May | −9.7 (−9.6) | 0/12 | −10.5 (−5.5) | 0/8 | −8.0 |
| Jun (the rule) | +2.4 (1.1) | 8/12 | +6.0 (2.4) | 6/8 | +2.4 |
| Jul | −5.1 (−2.5) | 2/12 | −4.6 (−2.8) | 1/8 | −6.0 |
| Aug | −3.5 (−2.0) | 3/12 | −1.9 (−1.2) | 2/8 | −3.5 |
| Sep | −5.1 (−2.9) | 2/12 | −2.4 (−1.7) | 3/8 | −2.7 |
| Oct | −6.0 (−5.2) | 0/12 | −4.5 (−1.7) | 2/8 | −2.6 |
| Nov | −7.5 (−3.9) | 1/12 | −5.7 (−3.7) | 0/8 | −5.0 |
| Dec | −1.8 (−1.0) | 4/12 | −2.4 (−1.4) | 3/8 | −3.8 |

Losers lose 1 to 10 points against XJO after costs in every other start month. June minus the average of the other eleven: +8.1 points in development (t = 3.0), +10.8 in unseen (t = 3.4).

A A$25,000 account buys 10 names, not 50. Across 2,000 random 10-name samples of each year's list: mean +3.9% over XJO for the 20 Junes, ahead in 65% of years, median worst year −13%, one sample in twenty has a worst year below −21%. In development 6% of samples had a negative 12-year mean.

Reading:
- The edge is about the size of one round trip. Costs are 3.1 points per trade in my build; doubling the spread removes the development result and leaves +3.4% (t = 1.4) in unseen.
- 41% of picks are under 20c. Without them: −0.1% development, +2.3% unseen (t = 1.1).
- The mean depends on the right tail. The median pick is −0.9% (development) and +2.2% (unseen) against XJO.
- Against the equal-weight small-cap universe the net edge is −0.3% in development and +2.4% (t = 1.3) in unseen. Much of the excess over XJO is small caps rising in July.
- Buying 3 days early removes the development edge; the selling pressure is still on. Buying 3 days late or selling 3 days either side changes little.
- Delisting treatment, position size and trimming do not matter.

### 6.2 H101

| Test | Card form (N4): dev 2004–15 | Card form (N4): unseen | Wider form (N1): dev 2004–15 | Wider form (N1): unseen |
|---|---|---|---|---|
| Base (20c floor, A$2,500, D30) | +16.7 (2.6), 10/12 | +5.6 (1.4), 5/7 | +8.7 (2.0), 9/12 | +2.4 (0.5), 5/7 |
| price ≥ 5c | +17.2 (2.7), 10/12 | +6.0 (1.5), 5/7 | +8.5 (2.1), 9/12 | +7.7 (1.1), 4/7 |
| price ≥ 10c | +17.3 (2.7), 10/12 | +5.1 (1.1), 5/7 | +9.7 (2.5), 9/12 | +7.2 (1.1), 3/7 |
| price ≥ 50c | +15.5 (2.6), 10/12 | +2.4 (0.5), 4/7 | +11.1 (2.1), 9/12 | +4.8 (1.1), 4/7 |
| A$1,000 per name, no ADV cap | +15.9 (2.5), 9/12 | +4.9 (1.2), 5/7 | +8.0 (1.8), 9/12 | +1.6 (0.4), 4/7 |
| A$1,000 per name, 5% ADV cap | +15.8 (2.5), 9/12 | +4.9 (1.2), 5/7 | +8.0 (1.8), 9/12 | +1.8 (0.4), 4/7 |
| A$2,500 per name, 5% ADV cap | +16.4 (2.6), 10/12 | +5.6 (1.3), 5/7 | +8.9 (2.0), 9/12 | +3.0 (0.7), 5/7 |
| A$5,000 per name, no ADV cap | +16.9 (2.7), 10/12 | +5.9 (1.4), 5/7 | +9.0 (2.0), 9/12 | +2.6 (0.6), 5/7 |
| A$5,000 per name, 5% ADV cap | +16.7 (2.5), 9/12 | +5.2 (1.4), 5/7 | +9.1 (1.9), 9/12 | +3.2 (0.7), 5/7 |
| delisting unknown = −100% (D100) | +16.0 (2.5), 10/12 | +1.9 (0.4), 5/7 | +8.3 (1.8), 8/12 | −2.9 (−0.6), 2/7 |
| delisting at last price (D0) | +16.9 (2.7), 10/12 | +7.2 (1.7), 5/7 | +8.9 (2.0), 9/12 | +4.6 (1.0), 5/7 |
| spreads doubled | +15.4 (2.5), 9/12 | +4.4 (1.1), 5/7 | +7.6 (1.7), 8/12 | +1.2 (0.3), 4/7 |
| entry 3 days earlier | +19.0 (2.9), 9/12 | +7.5 (1.6), 5/7 | +10.9 (2.4), 10/12 | +4.6 (1.0), 5/7 |
| entry 3 days later | +15.8 (2.5), 10/12 | +5.5 (1.3), 5/7 | +7.7 (1.7), 9/12 | +2.4 (0.5), 4/7 |
| exit 3 days earlier | +15.8 (2.6), 9/12 | +4.3 (1.0), 5/7 | +8.0 (1.9), 9/12 | +0.9 (0.2), 4/7 |
| exit 3 days later | +16.7 (2.7), 10/12 | +4.8 (1.1), 5/7 | +9.1 (2.0), 9/12 | +2.0 (0.4), 4/7 |
| top/bottom 1% of position returns: drop | +11.6 (3.4), 10/12 | +3.8 (1.2), 5/7 | +5.5 (1.8), 8/12 | +0.5 (0.1), 5/7 |
| top/bottom 1% of position returns: winsorise | +13.6 (3.2), 10/12 | +5.1 (1.3), 5/7 | +6.8 (2.0), 9/12 | +1.4 (0.4), 5/7 |
| median position instead of mean | +8.8 (2.2), 10/12 | −4.6 (−1.9), 1/7 | +0.7 (0.3), 5/12 | −6.1 (−2.1), 2/7 |
| annual cohort formed end of month 03 | +10.7 (1.6), 8/12 | −3.6 (−1.0), 1/7 | +10.1 (2.2), 8/12 | −0.1 (−0.0), 3/7 |
| annual cohort formed end of month 06 | +10.1 (2.9), 9/12 | +1.1 (0.3), 3/7 | +15.4 (3.5), 10/12 | −3.4 (−1.1), 3/7 |
| annual cohort formed end of month 09 | +13.5 (3.7), 11/12 | −0.1 (−0.0), 2/7 | +15.3 (4.4), 11/12 | +1.4 (0.4), 4/7 |

All monthly formations, full costs, Newey–West t with 11 lags: N1 +12.3 (4.2) in development 2004–2015, +0.6 (0.3) in unseen; N4 +13.2 (4.1), then +1.2 (0.6).

Reading:
- Costs, position size and ±3 days do not matter for a 12-month hold.
- The unseen result depends on December. Formed in March, June or September the card form gives −3.6, +1.1 and −0.1; averaged over all months +1.2.
- The unseen mean depends on a few large winners. The median pick lags XJO by 4.6 points (card form) and 6.1 points (wider form).
- Counting unknown delistings as total losses leaves +1.9 (card form) and −2.9 (wider form). 6–7% of unseen picks stopped trading with no reason on file.
- Development holds up under every test; the break is at 2016, the same pattern as report 51's top-300 version.

## 7. Rule ambiguities that forced a guess

| # | Point the text does not settle | My reading | Builder's reading | Changes results? |
|---|---|---|---|---|
| 1 | H100: are turnover rank, traded days and the 5c test measured on the buy day or the day before? | Buy day | Day before | Yes, up to 5 points in a year |
| 2 | Both: must a company have traded on the measurement day to be in the universe? | No (last close used) | Yes | Yes: H101 development +4 points |
| 3 | Both: buy price when there is no trade on the buy day | Last traded close, flagged | Next traded close within 5 days, else dropped | No |
| 4 | H101: "scores as report 51" — month-end prices (report 51's code) or fixed day counts? | Month-ends, gaps filled up to 10 days | 21/126/252 trading days, gaps filled without limit | Yes: unseen +3.6 points, one cohort |
| 5 | H101: "hold 12 months" | Sell the trading day after the month-end 12 months on | Sell 252 trading days after entry | About 1 point |
| 6 | H101: are companies with a missing score in the universe benchmark? | Yes | No | Small |
| 7 | H101: costs "on the names that leave" | Turnover-based (headline), full cost shown | Full cost on all | 0.2 points |
| 8 | H101 N4: is the top tenth taken after the 50c / A$50,000 filter, and with what minimum? | After; no minimum | After; at least 30 companies, so starts 2003 | Only which cohorts exist |
| 9 | Price tests: raw or split-adjusted close? | Raw | Raw | — |
| 10 | "Traded days": price present, or volume above zero? | Price present | Volume above zero | No |
| 11 | When is a stock "delisted" rather than not trading on the exit day? | Last trade more than 30 days before the data ends | More than 5 days | No |
| 12 | Delisting reason look-up window | 1,500 days | 900 days | No |
| 13 | Spread estimate: 63 trading days or 63 days with trades; fallback when too few | 63 trading days | 63 traded days, lagged 2 | No |
| 14 | Commission on the sale: on A$2,500 or on the sale value? | Sale value | A$2,500 | No |
| 15 | Capacity: 63-day median (text) or 252-day | 63-day | 252-day | Changes the feasibility claim |
| 16 | "Price ≥ 20c" variant: filter the picks or re-form the universe? | Re-form | Filter picks | 1.4 points unseen |
| 17 | Excess over the universe: universe gross or net of costs? | Gross | Gross | — |
| 18 | Worst fifth: ties and rounding at the cut-off | Percentile rank ≤ 0.2 | Return ≤ the 20% quantile | One name in some years |

## 8. Verdict on paper forward tests

### H100 — yes, paper test it

It is the one result here that a second, independent build gives back to a tenth of a point, it is first of twelve start months in both periods, and it beats every random draw. It is also thin: one observation a year, a development t of 1.1, and an edge no bigger than its own costs. Guard rails:

1. **Fix the rule text before June 2027.** State points 1, 2, 3 and 18 of section 7 on the card. I would take the builder's readings (universe the day before; must have traded; limit order at the close, unfilled names dropped), because they are what a person can actually do.
2. **Costs are the test.** Record the realised spread on every fill against the modelled 1.05–1.15% a side. If the realised average over two Junes is above 1.7% a side (one and a half times the model), close: at double the model the back-test is zero in development.
3. **No early entry.** Buy on the 4th-last trading day, not before. Sell at the end of July; the August exit is weaker in both periods.
4. **Cap each position** at the lower of A$2,500 and 5% of the 63-day median daily value. About one name in five needs the cap.
5. **Run two paper books:** the full list, and a 10-name draw chosen by a seed written down beforehand. Hand-picking is not allowed; the mean lives in a few big winners and the median pick is about level with the index.
6. **Score against two benchmarks:** A200, and the equal-weight universe. Against the universe the back-test edge is +2.4% in unseen and zero in development.
7. **Report the under-20c and 20c-and-over halves separately.** If only the under-20c half works on paper, the result is a spread artefact until real fills say otherwise.
8. **Fix the rename defect** (section 5.1) in whatever store feeds the card.
9. **Keep the card's review and fail triggers** (4 of 5 Junes behind; 15 points behind cumulatively). Expect a worst year near −13% on the full list and −20% on 10 names.
10. **No real money.** Eight unseen Junes cannot support it.

### H101 — not as a candidate; a tracking line at most

The blind build does not support "promising". On the card form the unseen edge is +5.6 with t = 1.4 in December, +1.2 across all formation months, negative for the median pick, and near zero if unknown delistings are losses. The headline N1 figure of +6.0 rests on one cohort and two stocks. It uses the same score as H82 on a neighbouring size band, so it adds little that H82's paper test is not already measuring. If it is kept because paper costs nothing:

1. Fix points 2, 4 and 5 of section 7 on the card, and hold 12 months and one day as the card says, not 252 trading days.
2. Treat H101 and H82 as one bet for any sizing or pass/fail count.
3. Print the median pick and the equal-weight universe beside the mean every month.
4. Record every pick that stops trading as takeover, failure or unknown.
5. Form a shadow cohort each quarter as well as each December, to see whether December is special.
6. Close at the 36-month look if behind A200, as the card says. No path to real money from this evidence.

## 9. Files

- `replication_59/code/prep.py`, `core.py`, `run_base.py`, `run_stress.py` — blind build and stress tests (run with `python3 -I`).
- `replication_59/code/recon_names.py`, `recon_why.py`, `recon_attrib.py`, `recon_extra.py` — step 3 comparison, written after the freeze.
- `replication_59/out_frozen/step1/`, `step2/`, `step3/` with `SHA256_step1.txt`, `SHA256_step2.txt`, `SHA256_step3.txt`; `FREEZE_MANIFEST.txt` holds the two blind hashes.
- `replication_59/out/stress_table.csv` — every stress row with means, t, hit rates, worst years, and excess over the universe.
- `replication_59/out/recon_h100_attrib.csv`, `recon_h101_N1_attrib.csv`, `recon_h101_N4_attrib.csv` — yearly figures for each step of section 4.
