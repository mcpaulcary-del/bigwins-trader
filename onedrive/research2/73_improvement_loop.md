# 73. The improvement loop — three engines, eleven fresh market tests, none beat the index

17 November 2026. Research and paper only. General information, not financial advice. Nothing here can place an order.
Work folder: `scratchpad/improve/` (`PREREG_73_R1.md`, `_R2.md`, `_R3.md`, `code/`, `out/`). Trial ledger: `out/trials_73.csv` (cumulative count 427 → 950). Progress log: `out/PROGRESS.md`.

## 0. Plain-English verdict

**Question.** Can the Big Wins engine be improved until it beats the index, after costs and tax, on data it was not designed on?

**Answer: no. Nothing passed, and the evidence now says a price-only share-picking engine of this kind does not beat a cheap index fund in a taxed A$5,000–100,000 account.**

1. **How it was tested.** The ASX years after 2015 are used up, so each engine was designed on ASX 2001–2015 and then given one look at markets this project had never touched: Canada, the UK, Germany, France, Sweden (2018–2026, or 2020–2026 for Sweden) and three size bands of US shares in two eras (2001–2013 and 2014–2026). Eleven fresh sets in three rounds. Each engine and each bar was written down and hashed before the returns were computed.
2. **Result.** After costs and tax, at A$25,000 and A$100,000, the engine had to lead the local index fund by 1 point a year in most markets with none worse than −2. It managed that lead in **1 of 3, 0 of 5 and 1 of 3 sets**. Averaged over a round's sets the three engines finished **4.8, 1.5 and 0.6 points a year behind** the fund.
3. **The current engine's own recipe did worst.** E1 is the H82 idea (steady risers, yearly review) written in a form that runs on any market. It lost by 2 to 7 points a year in Canada, the UK and the US.
4. **There is some skill, and it is not enough.** In 10 of 20 tests at A$100,000 the engine beat three-quarters of random portfolios trading the same amount. Trend signals do sort shares, in most markets. But an equal-weight book of the most-traded shares starts behind a cap-weighted fund (by about 5 points a year in US large shares 2014–2026 and 3 in the UK), and brokerage, spread and yearly capital-gains tax take another 1.5 to 2.5. The picking skill wins back part of that gap, not all of it.
5. **The owner's account (A$5,000 plus A$500 a month).** The engine finished behind the index fund in 10 of the 11 sets for the eligible candidates (for example A$74,000 against A$86,000 in the UK, A$190,000 against A$200,000 in US large shares). The small-account fix (index fund until A$25,000, then at least ten shares) removed the coin-toss, not the shortfall.
6. **Two errors were found and fixed along the way; both had flattered the engine.** (a) The data vendor's volume is adjusted for later share splits and its close is not, so "most traded" quietly favoured future winners. Before the fix one test showed +10.9 points a year; after it, −1.2. (b) Index-fund share splits were being taxed as dividends. Every figure in this report is after both fixes. Item (a) may also touch the main project's ASX figures from 2018 on and should be checked (section 7).
7. **Other questions the brief asked.** The daily commodity lead has no signal (t = 0.7 gold, −0.1 oil). Weekly instead of monthly decisions changes nothing. Small learned models did not beat a plain average. EODHD fundamentals are not on the current plan ("Forbidden"). The A-versus-B disagreement of report 70 was the start date: begun on the same day, the two data sets give 3.8%/4.4% and 2.1%/7.1%.
8. **Against the 40/60 plan.** No engine beat even its own single-market index fund, and the plan earned 11.9% a year over 2018–2026 (report 70). Real money stays there.
9. **What goes to paper.** E3 (trend quality, wide hold band) is the last and least-bad engine. It did not pass. It can be recorded as a shadow line at no cost; a 70% fund / 30% E3 version (E3c) loses least. Neither should be promoted without 36 forward months.
10. **Confidence.** High that these three designs do not clear the bar. Moderate that no price-and-volume design can: the same shortfall appeared in 9 of 11 markets, with different engines, and the pieces of it (weighting gap, costs, tax) are structural. Fresh data remain on the plan (Korea, Taiwan, Brazil, South Africa, Switzerland, Norway, Denmark, Spain, Netherlands) and were deliberately not spent, because no candidate has a development case worth testing.

---

## 1. What was done

| Step | What | Counted trials |
|---|---|---|
| Diagnosis | Report 70's look A against look B from one start date | 0 (re-read of used data) |
| Own engine | `packlib.py` (daily data → month-end pack), `sim.py` (accounts, costs, three tax regimes, index-fund core, lifecycle, matched placebo). Same code on every market. Reproduces the H82 order of magnitude on ASX 2001–2015 (10.5% after costs at A$25,000 against report 64's 9.7%) | — |
| Development, ASX 2001–2015 | Signal sweep (17), commodity lead (2), trading forms (27), scores and learned models (15), small accounts and core weights (9), weekly cadence (2) | 72 |
| Round 1 | E1 frozen (hash in `out/prereg73_R1_hash.txt`), one look at Canada, UK, US mid band 2001–13 | 3 + 42 descriptive |
| Round 2 | E2 designed on ASX + round-1 sets (about 75 trials), frozen, one look at US large and small 2001–13, Germany, France, Sweden | 5 + 70 |
| Corrections | Split-volume error found; all packs rebuilt; rounds 1 and 2 re-run (R1d, R2d); 20 design trials repeated on nine corrected sets | about 150 |
| Round 3 | E3 frozen, one look at US 2014–Oct 2026, three bands; E1, E2 and E3c shown beside it | 12 + 42 |
| After | Gross description on all 12 sets | 4 |

Cumulative count for the deflated Sharpe ratio: **950** (re-runs and every descriptive regression counted, which is conservative).

**Fresh-data coverage.** Dead companies are in the vendor file from 2000 for the US (3–10% of listings end each year) and only from 2018 for Canada, the UK, Germany and France (0–2% before, 5–13% after) and 2020 for Sweden. Earlier years of those markets were not used at all. New Zealand, Japan, Hong Kong and India are not on the plan.

## 2. Development on ASX 2001–2015 (price only; index = price index)

After-tax return, mean of eight accounts (A$25,000 and A$100,000, four start months). Index fund: 2.8%.

| Variant | After tax, % a year | Turnover | Note |
|---|---|---|---|
| H80 score, yearly review, corrected H82-like form | 5.8 | 0.87 | |
| **H80, yearly review, "winners ride"** (a profitable holding still in the top 70% is kept another year) | **7.8** | 0.69 | became E1 |
| H80, monthly band, hold line 60 / 90 / 120 / 150 | 6.6 / 6.4 / 6.2 / 6.8 | 1.46–0.60 | |
| Swap test with full / light / no tax in the test | 5.6 / 6.1 / 6.3 | 0.48–1.06 | lighter tax reading: no gain |
| 20 / 40 holdings; A$5,000 minimum position | 6.2 / 6.9; 5.7 | | |
| Weekly decisions, hold line 90 / 150 | 7.6 / 7.7 | 1.45 / 0.65 | same as yearly |
| H80 + zero-volume share | 8.4 | | inside the noise |
| H80 + zero-volume + momentum × size (report 70's CH) | 6.3 | | |
| Plain 12-1 momentum; low volatility alone | 2.4; 0.9 | | |
| Residual momentum blend; trend-quality blend | 7.7; 6.8 | | |
| Ridge model; boosted trees; H80 + trees | 3.9; 7.0; 8.2 | | no better than H80 |
| 30% / 50% / 70% in the index fund | 6.4 / 5.1 / 3.9 | | lead shrinks in proportion |

Signals (monthly regression inside the 300 most traded, 180 months): H80 t = 3.8; high recency 5.3; trend quality 4.4; residual momentum 4.5; zero-volume share −4.0. On top of H80 only zero-volume share (−3.1) and momentum × size (+2.5) add anything. Frog-in-the-pan adds nothing.

Daily commodity lead: shares exposed to gold or oil (trailing one-year beta, t ≥ 2), bought one day after a five-day commodity move, held five days, against the rest: gold +0.1% per week (t = 0.7), Brent 0.0% (t = −0.1). Closed.

Small accounts (A$5,000 + A$500 a month, A$94,500 paid in): index fund A$110,000; engine with v1.3 sizing A$153,000–173,000 depending on start month; fund until A$25,000 then engine with ten or more shares A$138,000–143,000. An A$5,000 lump sum in four shares earned 0.6% a year with a −2% to +4% spread. The fund-first rule was adopted for every candidate.

No variant led the simplest one by more than the one-point noise floor. Development could not separate them; only fresh markets could.

## 3. The three candidates

| | E1 | E2 | E3 |
|---|---|---|---|
| Universe | 300 most traded | 100 most traded | 300 most traded |
| Score | H80 (12-1 and 6-month return, nearness to high, low volatility) | Recency of the 52-week high | Trend quality: t-statistic of the 12-month log-price slope |
| Form | Yearly review, sell below rank 30, winners ride | Monthly; buy rank ≤ 15, sell after two months below 67 | Monthly; buy rank ≤ 30, sell after two months below 200 |
| Holdings | up to 30 | up to 20 | up to 30 |
| Designed on | ASX 2001–15 | ASX + Canada, UK, US mid 2001–13 (data later found biased; choice of 100 is void) | ASX + eight corrected fresh sets |

E3c = E3 with 70% of the account in the index fund (descriptive only).

## 4. Results on fresh markets (all after both corrections)

X = after-tax return of the engine minus after-tax return of the local index fund, points a year, mean of four start months. CL = current law; AN = announced July-2027 design. Franking does not apply outside Australia. "Placebo" = percentile among 200 random accounts making the same number of sales each month.

| Round | Cand | Set | X_CL 25k | X_CL 100k | X_AN 25k | X_AN 100k | eng/fund net 100k | placebo pct 25k/100k | top5 100k | t | DSR | maxDD eng/fund | life engine / fund (paid in) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1d | E1 | CA | -6.0 | -5.2 | -5.6 | -4.7 | 8.4 / 13.3 | 28 / 12 | 36% | -1.4 | 0.00 | -25 / -20 | 89.9k / 107.8k (57.5k) |
| R1d | E1 | UK | -7.4 | -4.4 | -7.8 | -4.6 | 3.2 / 8.2 | 18 / 52 | 160% | -1.7 | 0.00 | -23 / -24 | 73.9k / 86.2k (57.5k) |
| R1d | E1 | USM1 | -2.1 | -3.4 | -2.3 | -3.2 | 6.9 / 10.0 | 57 / 40 | 38% | -1.1 | 0.00 | -48 / -49 | 114.5k / 164.4k (82.5k) |
| R2d | E2 | USL1 | -1.2 | -0.6 | -1.5 | -1.1 | 5.3 / 5.7 | 82 / 89 | 424% | -0.4 | 0.00 | -67 / -51 | 125.6k / 133.1k (82.5k) |
| R2d | E2 | USS1 | -1.1 | -2.5 | -1.3 | -2.4 | 8.8 / 10.7 | 86 / 72 | 49% | -0.2 | 0.00 | -58 / -52 | 159.3k / 170.0k (82.5k) |
| R2d | E2 | DE | -3.6 | -3.6 | -3.3 | -3.2 | 5.3 / 8.5 | 20 / 36 | 253% | -1.3 | 0.00 | -34 / -26 | 79.4k / 89.2k (57.5k) |
| R2d | E2 | FR | -0.0 | -1.5 | -0.4 | -1.7 | 6.7 / 7.8 | 94 / 88 | 122% | -0.9 | 0.00 | -25 / -26 | 74.7k / 77.6k (57.5k) |
| R2d | E2 | SE | -0.2 | -0.9 | -0.4 | -0.9 | 13.7 / 13.8 | 86 / 95 | 70% | 0.5 | 0.00 | -35 / -23 | 66.6k / 70.1k (45.5k) |
| R3 | E3 | USL2 | -2.3 | -3.4 | -2.3 | -3.0 | 10.8 / 13.5 | 82 / 87 | 45% | -1.0 | 0.00 | -30 / -24 | 189.5k / 199.6k (81.5k) |
| R3 | E3 | USM2 | -1.3 | -1.0 | -1.7 | -1.1 | 8.9 / 9.8 | 82 / 57 | 54% | -0.5 | 0.00 | -27 / -30 | 143.3k / 149.5k (81.5k) |
| R3 | E3 | USS2 | +1.7 | +2.5 | +0.6 | +1.4 | 12.0 / 9.5 | 76 / 96 | 68% | 0.6 | 0.00 | -28 / -36 | 184.0k / 145.2k (81.5k) |
| R3 | E3c | USL2 | -0.7 | -0.8 | -0.8 | -0.9 | 12.8 / 13.5 | 78 / 74 | 50% | -1.2 | 0.00 | -26 / -24 | 189.4k / 199.6k (81.5k) |
| R3 | E3c | USM2 | -0.4 | -0.5 | -0.5 | -0.5 | 9.8 / 9.8 | 76 / 84 | 57% | 0.1 | 0.00 | -26 / -30 | 139.2k / 149.5k (81.5k) |
| R3 | E3c | USS2 | +0.1 | +0.6 | -0.1 | +0.3 | 10.4 / 9.5 | 78 / 89 | 73% | 0.3 | 0.00 | -27 / -36 | 179.3k / 145.2k (81.5k) |
| R3 | E1 | USL2 | -7.2 | -6.1 | -6.8 | -5.7 | 7.5 / 13.5 | 37 / 34 | 25% | -2.4 | 0.00 | -33 / -24 | 127.9k / 199.6k (81.5k) |
| R3 | E1 | USM2 | -0.5 | -1.6 | -0.9 | -1.7 | 8.5 / 9.8 | 80 / 62 | 24% | -0.5 | 0.00 | -26 / -30 | 142.2k / 149.5k (81.5k) |
| R3 | E1 | USS2 | -2.5 | -1.5 | -2.7 | -1.7 | 8.6 / 9.5 | 40 / 63 | 29% | -0.4 | 0.00 | -30 / -36 | 130.2k / 145.2k (81.5k) |
| R3 | E2 | USL2 | -3.3 | -1.9 | -3.6 | -2.1 | 12.7 / 13.5 | 80 / 93 | 48% | 0.4 | 0.00 | -26 / -24 | 177.5k / 199.6k (81.5k) |
| R3 | E2 | USM2 | +2.6 | +1.6 | +2.2 | +1.1 | 12.3 / 9.8 | 98 / 94 | 53% | 0.8 | 0.01 | -25 / -30 | 176.4k / 149.5k (81.5k) |
| R3 | E2 | USS2 | -1.2 | -1.4 | -1.4 | -1.8 | 8.0 / 9.5 | 84 / 75 | 55% | -0.2 | 0.00 | -27 / -36 | 132.4k / 145.2k (81.5k) |

Sets: CA Canada, UK, DE Germany, FR France, SE Sweden (windows Dec 2017–Oct 2026; Sweden from Dec 2019). USL/USM/USS = US traded-value ranks 1–300 / 301–600 / 601–900 (E2: first 100 of each band); 1 = Dec 2000–Dec 2013, 2 = Dec 2013–Oct 2026. Funds: XIU, ISF, EXS1, CAC, XACT OMXS30, SPY, IJH, IJR. Rows R3/E1, R3/E2 and R3/E3c are descriptive.

### Pass or fail against the pre-registered bar

| Bar | Round 1 (E1) | Round 2 (E2) | Round 3 (E3) |
|---|---|---|---|
| X ≥ +1.0 at both sizes in a majority of sets | 0 of 3 | 0 of 5 | 1 of 3 |
| No set below −2.0 at either size | fail (all three) | fail (US small, Germany) | fail (US large) |
| X under the announced law > 0 in a majority | 0 of 3 | 0 of 5 | 1 of 3 |
| ≥ 90th percentile of matched random accounts, both sizes, majority | 0 of 3 | 0 of 5 | 0 of 3 |
| Top five positions < 50% of profit (A$100k), majority | 2 of 3 | 1 of 5 | 1 of 3 |
| Deflated Sharpe at N ≈ 900 (reported) | 0.00 | 0.00 | 0.00 |
| **Verdict** | **fail** | **fail** | **fail** |

Mean X over a round's cells: E1 −4.8; E2 −1.5; E3 −0.6 (E3c −0.3; E1 and E2 on the round-3 sets −3.2 and −0.6).

Round 3 detail, E3 at A$100,000, lead over the fund by year (points): US large 2014 −3.5, 2015 +13.5, 2016 −19.6, 2017 +10.0, 2018 −8.4, 2019 +1.4, 2020 +0.9, 2021 −9.0, 2022 −2.1, 2023 −13.1, 2024 +3.7, 2025 +6.9, 2026 −9.6. US small: +3.9, +7.6, −25.5, +11.4, +8.7, +8.5, +7.0, −19.5, −2.8, −4.5, +42.7, +31.7, −23.3. The one pass (US small) rests on 2024–2025.

Stress (E3, A$100,000, December start, after tax; US large / mid / small): costs × 1.5 lowers the return by 0.1 / −0.3 / 0.6 points; paying every delisting at 70% by 0.0 / 0.1 / 1.4. UK stamp duty (E1) costs 0.3. Differences this small are path noise (a different bill changes which orders fit).

### What the fresh markets say about the signals

t of the monthly slope of next-month return on the signal's percentile, inside each set's universe:

| Signal | CA | UK | DE | FR | SE | USL1 | USM1 | USS1 | USL2 | USM2 | USS2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H80 | 0.5 | 1.1 | 0.5 | 2.5 | 0.3 | 2.5 | −0.2 | −0.6 | 3.7 | 1.8 | 1.4 |
| Trend quality | 1.6 | 1.4 | 2.2 | 3.3 | 0.3 | 2.9 | −0.2 | 0.2 | 4.4 | 1.8 | 1.9 |
| High recency | 1.3 | 1.5 | 2.1 | 2.6 | 0.6 | 1.8 | 0.5 | 1.6 | 4.6 | 2.5 | 1.9 |
| Low volatility (s4) | −0.3 | 1.4 | −0.4 | 1.5 | 1.7 | 1.9 | 0.1 | −0.4 | 2.1 | 1.2 | 0.6 |
| Zero-volume share | −1.5 | −2.1 | 0.0 | −0.3 | 0.8 | 0.2 | 0.5 | 0.0 | −2.2 | −0.6 | −1.6 |
| Momentum × size | 0.5 | −0.5 | −0.7 | 0.1 | −0.1 | 0.4 | −0.1 | 0.8 | −3.4 | −0.9 | −1.7 |

(CA, UK, USM1: 300 most traded; DE, FR, SE, USL1, USS1: 100; round 3: 300.) Trend signals are positive in 10 of 11 sets and above 2 in four or five. Zero-volume share and momentum × size, the two inputs report 70 added, do not hold up. The sorting is real; a taxed, equal-weight, long-only account does not turn it into a lead over a cap-weighted fund.

### Why skill does not become a lead

Gross returns, monthly rebalanced, no costs or tax, % a year (`out/dev15.log`):

| Set | Index fund | Equal-weight universe | Top 30 by trend quality |
|---|---|---|---|
| ASX 2001–15 (price) | 3.4 | −0.3 | 13.0 |
| Canada | 12.7 | 11.6 | 20.4 |
| UK | 7.6 | 2.9 | 6.8 |
| Germany | 7.6 | 6.1 | 18.5 |
| France | 7.7 | −5.0 | 12.9 |
| Sweden | 12.2 | 5.3 | 15.0 |
| US large / mid / small 2001–13 | 4.6 / 8.9 / 10.0 | 0.9 / 7.2 / 9.7 | 3.6 / 5.2 / 11.6 |
| US large / mid / small 2014–26 | 13.5 / 9.8 / 9.2 | 4.2 / 6.9 / 7.7 | 13.2 / 9.0 / 15.7 |

The equal-weight "most traded" universe trails the fund in every set, by 0.3 to 13 points. The top-30 list beats its own universe almost everywhere and beats the fund in 7 of 12 before costs, with monthly rebalancing that a taxed account cannot afford. Held for a year or more to keep tax down, the lead shrinks; costs and tax then take 1.5–2.5 points. A traded-value-weighted version was computed and is not reported: the weights are dominated by a few bad vendor rows.

## 5. Ranking of what came closest

| Rank | Engine | Mean lead over the local fund on fresh sets, points a year after tax | Sets passing | Worst cell |
|---|---|---|---|---|
| 1 | E3c: 70% index fund, 30% E3 | −0.3 (3 sets) | 0 of 3 | −0.8 |
| 2 | E3: trend quality, wide band | −0.6 (3 sets) | 1 of 3 | −3.4 |
| 3 | E2: high recency, 100 most traded | −1.5 (5 sets); −0.6 on round-3 sets | 0 of 5; 1 of 3 | −3.6 |
| 4 | E1: H80 yearly (the H82 idea, generic form) | −4.8 (3 sets); −3.2 on round-3 sets | 0 of 3; 0 of 3 | −7.4 |

The index fund itself is rank 0.

## 6. Frozen rules of E3 (the tested engine; it did not pass and is not a paper rule)

Parts A (inputs), C1 (payouts), E (costs), F (tax) and G of rules v1.3 apply unless stated. "Month-end" = last trading day of a calendar month.

- **T1. Traded value.** Day's traded value = raw close × volume ÷ F, where F = the product of all split ratios dated after that day (EODHD volume is split-adjusted; in forward use this matters only for a split inside the last 252 days).
- **T2. Universe at month-end t.** Companies with a close on at least 200 of the 252 trading days ending t, ordered by the median of daily traded value over those days (days with no row count as zero; ties in identifier order). The first 300.
- **T3. Score.** L(d) = ln of the adjusted close of day d, or of the most recent earlier close if d has none. All 252 days ending t must have a value. Regress L on day number 1…252 by ordinary least squares. Score = slope ÷ its standard error (residual variance with divisor 250). Rank 1 = highest; ties in traded-value-rank order.
- **T4. Book.** At every month-end, after payouts: NAV = cash + holdings at last price; n = min(30, max(4, floor(NAV ÷ 2,500))); T = NAV ÷ n.
- **T5. Sales.** For each holding, b = consecutive month-ends, ending now, at which its rank was worse than 200 or missing. b ≥ 2 → sold in full, except a holding worth more than its cost whose first lot is 300–365 days old and whose rank is 210 or better: it waits. At the May month-end, a holding with b ≥ 1 worth no more than its cost is sold.
- **T6. Trim.** A holding above max(15% NAV, 2T) is cut to max(10% NAV, 4T ÷ 3); lots held 367 days or more first, highest cost per share first.
- **T7. Buys.** While holdings < n: best-ranked company with rank ≤ 30, a close on t, raw close ≥ A$0.50, median traded value ≥ 100 × T, not held. Amount = min(T, free cash); stop if that is below max(1,000, 0.5 T).
- **T8. Top-up.** If the book is full: holdings ranked ≤ 200 worth less than 0.75 T are topped up to T, smallest first, when the amount is at least A$1,000.
- **T9. Execution.** Next trading day's close: sells, trims, buys, top-ups. A sale with no close that day is decided again next month. Whole shares.
- **T10. Small accounts.** Index fund only until NAV ≥ A$25,000 at a December month-end; then the fund is sold and T4 applies with n ≥ 10. (E3c: 70% of NAV stays in the fund; the book is built from the rest.)
- **T11. Not in the rule.** No stops, no market timing, no sector or commodity caps, no learned model.
- **Data guard (back-tests on foreign markets only).** Adjusted-close jumps above ×3 that revert by half within ten rows are deleted; unreverted jumps above ×20 are removed; a code with a gap of more than 200 calendar days is split into companies; a line whose last 60 rows match another line's close and volume on 30 days is dropped.

**Forward-snapshot procedure (shadow line only).**
1. On the first trading day after each month-end, with the same EODHD file the v1.3 snapshot uses (cut at the month-end), build the pack: `python3 improve/code/mk_asx.py eod M` (or the forward pipeline's equivalent arrays).
2. `python3 improve/code/snapshot_e3.py <pack> <out folder>` writes `forward_E3_snapshot_<date>.csv`: 300 rows with code, E3 rank, trend-quality value, traded-value rank, close, traded-on-day flag, buy zone (rank ≤ 30), hold zone (rank ≤ 200), price test, and the H80 rank for comparison. First files: `improve/out/forward_E3_snapshot_2026-10-30.csv` and `…_2026-11-13.csv` (interim).
3. Hash the file into the forward chain beside the v1.3 snapshot. Apply T4–T9 by hand or with `sim.run(form='band', B=30, H=200, kconf=2)` to keep a paper book from the 31 Dec 2026 month-end.
4. Compare monthly with A200 total return and with H82. Status: closed for promotion; no look before 36 months.
Nothing was written to `68_forward_record/` or `bigwins_forward/`.

## 7. Errors, deviations and reasons this could be wrong

- **Split-adjusted volume (found after the round-2 look).** Close × volume overstated past traded value for companies that split later. All fresh packs were rebuilt; rounds 1 and 2 were re-run. Biased figures are kept in `out/biased_tv/` for the record (E2 on US large 2001–13: +10.9 / +10.6 biased, −1.2 / −0.6 corrected). **Rules v1.3 A5 define traded value as raw close × volume on the same vendor.** If the ASX file behaves the same way, the 2018–2026 universe of H82 has the same lean towards later winners. ASX has few splits and the vendor's older ASX closes look pre-adjusted, so the effect may be small. It was not measured here and should be.
- **Fund splits taxed as dividends (found after the round-3 look).** Fixed; affected looks re-run; old files in `out/fund_split_bug/`. Development tables in `out/dev7`–`dev14.log` that include US mid or US small 2001–13 overstate the engine's lead there by about 0.8 and 2.0 points; the choice between candidates is unaffected (same comparator for all).
- **Code re-use** was added after the round-1 look (one ticker gave a fake sixfold gain). Round 1 was re-run.
- **Each round was therefore looked at more than once**, always with the frozen candidate and always after a correction that made the data less favourable. No candidate was changed after its look.
- **E1's form was found by accident** (a deferral that waited a year instead of a month) and kept because it scored higher in development.
- **Costs and tax are the owner's Australian schedule in local currency units.** Real cross-border investing would add currency, withholding tax and, in the UK, stamp duty. Dividends are inferred from adjusted against raw closes. Australian CPI is used for the announced-law regime.
- **Delistings are paid at the last price** (no reasons are available); a 70% stress is shown. Dead companies before 2018 are missing outside the US, which is why those years were not used.
- **Markets overlap in time** (five sets cover 2018–2026) and are not independent. Eleven sets are fewer than eleven independent tests.
- **Vendor data quality** outside the US is uneven (150–450 unit errors removed per market).
- **Deflated Sharpe** uses the Bailey–López de Prado formula with the cross-trial variance set to 1/(T−1); at N ≈ 900 every figure is 0.00–0.01.
- **Not replicated** by a second agent.
- **Not tested:** Google Trends, daily macro as a share-level input, and any fundamental data (not on the plan). Report 70 found the macro and commodity families added nothing on ASX, and none of them exists point-in-time for the foreign markets.

## 8. Files

- Pre-registrations and hashes: `improve/PREREG_73_R1.md`, `_R2.md`, `_R3.md`; `out/prereg73_R1_hash.txt`, `_R2_`, `_R3_`.
- Code: `code/packlib.py`, `sim.py`, `devlib.py`, `scores.py`, `mk_asx.py`, `mk_fresh.py`, `dl.py`, `look.py`, `devmulti.py`, `dev1.py`–`dev15.py`, `dev_cmd.py`, `summ.py`, `showlook.py`, `snapshot_e3.py`, `freeze.py`.
- Data kept: `data/pack_*.npz` (month-end packs, 12–30 MB each), `data/etf/`, `data/cmd/`. Raw vendor downloads were held in memory only and are gone; `dl.py` and `mk_fresh.py` rebuild them (about 36,000 API calls).
- Results: `out/look_R1d_*`, `look_R2d_*`, `look_R3_*` (JSON, one per candidate and set), `out/summary_table.md`, `out/dev*.log`, `out/coverage_*.csv`, `out/trials_73.csv`, `out/forward_E3_snapshot_*.csv`, `out/PROGRESS.md`.
