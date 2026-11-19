# 70. The all-information, actively traded Big Wins engine — built, tested once, did not pass

16 November 2026. Research and paper only. General information, not financial advice. Nothing here can place an order.
Work folder: `scratchpad/allinfo/` (`PREREG_70.md`, `PREREG_70c.md`, `code/`, `out/`). Trial ledger: `out/trials_70.csv`.

## 0. Plain-English verdict

**Question.** Does one engine that uses every dated piece of information we hold (prices, volume and liquidity, commodities and currency, short selling, share issuance, listing age, index changes, market state), looks every week, and buys and sells when its readings change, beat the price-only yearly engine (H82, rules v1.3) and the index plan on years it was not designed on?

**Answer: no.** It was built as asked, frozen, and given one look at the held-out years.

1. **On the cleanest data (EODHD total return, 2018 to 13 Nov 2026, which includes two and a half years nobody had tested), the new engine lost to everything.** At A$100,000 it earned 7.6% a year after costs against 9.7% for H82, 8.8% for the ASX 200 fund and 11.9% for the 40/60 plan. At A$25,000: 5.2% against 9.6%, 8.8% and 11.9%. It ranked 71st and 45th out of 100 against random share-picking run through the same trading rules.
2. **On the older price-only data (2016 to May 2024) it looked good and still did not pass.** 9.5% a year against 4.0% for H82 and 4.6% for the index at A$100,000. But random picking through the same trading rules earned 6.7% at the median, the engine was only at the 83rd to 88th percentile of those random runs (the bar was 90), and its whole profit came from five shares it bought in 2016–2018 and then held for years (WiseTech, Pro Medicus, Saracen, Xero, Seven Group). By the rule written down in advance, that is luck, not skill.
3. **For the owner's actual account (A$5,000 plus A$500 a month, 2018–2026): A$58,000 paid in became about A$66,000 in the engine, A$89,000 in H82 and A$99,000 in the 40/60 index plan, all after tax.** The engine finished below 84% of random accounts run the same way.
4. **Does the extra information carry signal? A little, and not where it helps.**
   - Asked directly to find shares that rise 50% in a year, a model using everything does find more of them than chance (17 in 100 against 11 in 100 in development). But the shares it picks are the most dangerous on the board: their typical result was a loss, and 31 in 100 fell by 30% or more. This is the lottery-ticket trap report 72 predicted. Price and liquidity carry almost all of that signal; commodities add a trace; short selling, share issuance, listing age, index changes and seasonality add nothing measurable.
   - Asked the better question (rank shares by expected return), two of six never-tested inputs passed the development gate: shares with days of no trading do worse, and momentum works better in smaller shares. Adding them improved the development result by 2.3 points a year. On unseen data that gain was positive on one data set and negative on the other.
   - Commodity and currency exposure used as a risk cap changed little. A market-trend switch cut the 2008 fall in development, but that is one episode and it was dropped under the review's rule against market timing.
5. **Trading more often did not help.** The engine looks every week and can sell within weeks: one position in six was held under 90 days. Its typical holding still lasted seven months, because selling costs brokerage, spread and tax brought forward. In development, the same price-only score traded weekly earned 1.0 point a year less after tax than the yearly review. Faster variants were far worse (an exit line at the top 10% cost 5 points a year in turnover).
6. **Confidence.** High that this design does not beat H82 or the index plan: it failed on the better data set, on the account size the owner has, and against random controls. Low that any back-test could ever prove the opposite: with nine years of data a real 3-point edge would show a t-value near 1, against a bar of 3.
7. **What goes to paper.** H82 rules v1.3, unchanged, as already scheduled (31 Dec 2026 formation). The new engine gets no paper card. Its score and the printed flags (share issuance, short interest, commodity cluster, listing age) are added to the forward snapshot as columns so that clean, hindsight-free evidence accumulates from now. Real money stays in the 40/60 plan.

This is the seventh round in which a development gain did not survive unseen data. A null result was the expected result (report 72 §5 item 18).

---

## 1. What was done, in order

| Step | What | Hash time (UTC, 16 Nov) | Counted trials |
|---|---|---|---|
| PREREG_70 | First pre-registration: all families, a +50% classifier, weekly engine. Hash `d3d65a84…7cfd27` | 21:21 | — |
| Phase 1 | Development only (2005–2015): classifier check; four scores in the weekly engine; exit lines; stop; exposure caps; regime switch; price-only ablation; yearly machinery | after 21:21 | 12 |
| PREREG_70c | Amendment after report 72's brief arrived: rank target, cleaned labels, small fixed model, the brief's trading form, three tax regimes, franking, named benchmarks, one look. Hash `76e680a3…458f08`. Phase 1's finalists were denied an unseen look | 21:39 | — |
| Phase 2 | Stage A gates (6); price-only score in the new trading form (1); champion with families, model M1, model M2 (3); 50% hold line (1) | after 21:39 | 11 |
| Freeze | Code and development results hashed (`out/freeze_before_look_hashes.txt`) | before the look | — |
| The look | Final engine on unseen A (panel_v2, 2016–May 2024) and unseen B (EODHD, 2018–13 Nov 2026) | after the freeze | 1 |

Library count for the deflated Sharpe ratio: 403 (after report 72) + 12 + 11 + 1 = **427**. The blind rebuild in `blind13/` was not read; rows at N = 450 and 1,000 cover any trials it adds.

**Power statement (pre-registered, report 72 §4.11).** With tracking error near 9 points and 9 years of holdout, a true edge of 3 points a year gives an expected t of about 1.0. The new engine's tracking error turned out to be 13–16 points, which lowers that to 0.6–0.7. The chance of passing "t ≥ 3 and deflated Sharpe ≥ 0.95" is under 5% even if the edge is real. The look can reject a design. It cannot confirm one.

**"Unseen" is a re-used holdout.** 2016–May 2024 has been read at least 15 times for momentum-type rules. Only June 2024–November 2026 in unseen B is close to clean, and only for rules that are not H82/H88/H90.

## 2. Data inventory: every series held, and whether it could be used

"Dated" means the value was knowable on the decision day and the history includes companies that later died.

| Family | Series | Span | Dated? | Used how |
|---|---|---|---|---|
| Prices, volume | panel_v2 daily close, value traded, raw close; quality flags | 1997–May 2024 | Yes (unlicensed copy; research only) | Features, labels, development and unseen A |
| Prices, dividends | EODHD total-return panel, 4,488 symbols | Jun 2014–13 Nov 2026 (dead companies weak before 2018) | Yes | Unseen B; model rows after May 2023 |
| Commodities (monthly) | Iron ore, copper, gold, nickel, aluminium, zinc, coal, LNG, wheat, Brent, RBA commodity index | 1990–Oct 2026 | Yes with a publication lag (used from the 15th of the next month) | Exposures; driver momentum (phase 1); risk caps |
| Daily macro | Brent, WTI, AUD, US 10y/2y/3m, credit spread, Nasdaq, VIX, CNY (FRED) | 1990–Nov 2026 | Yes, previous day | Market-state and daily-driver features (phase 1) |
| Company exposures | Rebuilt here: 60-month regressions of each company's monthly return on 11 drivers, ending two months before | 2003–2026 | Yes | Features (phase 1); commodity clusters for caps |
| Short selling | ASIC daily short positions | 16 Jun 2010–Nov 2026 | Yes, five-day lag | Level, 65-day change, days to cover |
| Share issuance | ASIC total product in issue, made split-neutral with raw/adjusted close | Jun 2010–Nov 2026 | Yes, five-day lag | 12- and 3-month share growth; market cap |
| Listing age | Days since first close (EODHD full history for source E) | all | Yes | Feature |
| Index changes | S&P/ASX 200/300 additions and removals | Sep 2012–Mar 2024 | Yes (129 unmatched) | Feature (phase 1): no signal |
| Sector | ASX listed-companies file | today only | **No** (dead companies have none) | Caps only, as in v1.3. Kept out of every fitted model: "unknown sector" would tell the model the company dies |
| Headlines, results days | 1.26 million ASX headlines | Jul 2009–2026 | **No** (companies listed today only) | Not used |
| Fundamentals | company_db / stockanalysis | six years, survivors | **No**; terms bar ML training | Not used. EODHD fundamentals plan not bought and not assumed |
| ETF flows, LIC data | ASX investment-product files | 2017–2026 | Market-level only | Not used (one number a month for eight years) |
| News (GDELT) | — | — | Not obtainable | Not used |
| CPI | ABS monthly series | 1922–2026 | Yes | Announced-law tax regime |
| ETF comparators | Vanguard and Betashares NAV, distributions, total-return indices; EODHD for VHY, AQLT, MTUM | 2014–Nov 2026 | Yes | Benchmarks |

No new public series was fetched. Daily metals prices were not needed for a weekly engine, and the optional "daily commodity lead" diagnostic was not run because the amended budget had no room for it. It remains untested.

**Label cleaning.** 5.2% of development 12-month outcomes contain a row flagged as a residual split, spike or unexplained ±45% move in panel_v2. Among "fell 50% or more" outcomes the share is 27%; among "rose 50% or more" it is 3.6%. Those outcomes were left out of phase-2 training and of every hit-rate table.

## 3. Phase 1 — the first design (development 2005–2015 only; no unseen look was ever given)

**3.1 Can a model find +50% winners?** Walk-forward gradient-boosted trees on 49 features in nine families, retrained each December, scored on the 300 most-traded shares each week.

| Top 30 by… | Share that rose ≥ 50% in 12 months | Median 12-month return | Share that fell ≥ 30% |
|---|---|---|---|
| All 300 (base rate) | 10.8% | about 0% | — |
| All-family model, P(+50%) | **16.8%** | **−5.4%** | **31.0%** |
| Price, liquidity, age, seasonality only | 15.4% | — | — |
| Ridge logistic, all families | 18.4% | — | — |
| H80 "steady winners" score | 9.2% | **+6.1%** | 10.6% |

Average precision by year: all-family model 0.159, logistic 0.158, price-only model 0.143, base rate 0.105. The all-family model beat the price-only model in 6 of 11 years.

**Which families carry the +50% signal** (drop in average precision when one family is shuffled, points; years positive out of 10):

| Family | Drop | Years positive | Share of model gain |
|---|---|---|---|
| Price and momentum (14 features) | 2.43 | 8 | 29% |
| Liquidity and size (6) | 1.91 | 9 | 17% |
| Market state (8) | 0.85 | 4 | 29% |
| Commodity and currency exposure × driver moves (12) | 0.31 | 6 | 23% |
| Short selling (3; 2010 on) | 0.08 | 2 | 0.5% |
| Share issuance (3; 2010 on) | −0.01 | 1 | 0.4% |
| Listing age | 0.00 | 3 | 0.8% |
| Index changes | 0.00 | 1 | 0.0% |
| Seasonality | −0.01 | 4 | 0.1% |

Reading: price and liquidity carry the signal. The model leans heavily on market state and commodity exposure inside the training years (52% of gain), but that buys little on years it has not seen: it is mostly memory of which years were good for miners.

**3.2 The scores in a weekly engine** (buy from the top 30, sell when the rank falls below an exit line). RS = mean after-tax return (no CGT discount) of eight accounts: A$25,000 and A$100,000, four start months.

| Version | RS, % a year | Trades a year | Mean hold, days | Costs, % a year | Max fall |
|---|---|---|---|---|---|
| H82 yearly (same windows) | 3.8 | 34 | — | 0.7 | −56% |
| Transparent all-family score T, exit line 60 | 4.4 | 102 | 151 | 1.7 | −52% |
| P(+50%), exit 60 | **−3.9** | 111 | 138 | 2.2 | −71% |
| P(+50%) − P(−30%), exit 60 | −0.6 | 128 | 120 | 2.6 | −67% |
| That blended with a 3-month return model, exit 60 | 4.2 | 122 | 136 | 2.1 | −54% |
| T, exit line 30 (fast) | 0.2 | 263 | 64 | 5.0 | −55% |
| T, exit line 120 (slow) | 6.0 | 47 | 317 | 0.8 | −48% |
| T, 120, 20% stop-loss | 4.9 | 52 | 284 | 0.9 | −51% |
| T, 120, commodity-cluster caps | 6.0 | 49 | 307 | 0.8 | −47% |
| T, 120, caps + no buying while the index is below its 200-day average | 5.7 | 41 | 320 | 0.7 | **−29%** |
| **Price-only H80, same last configuration** | **7.1** | 49 | 280 | 0.8 | −29% |
| T through the yearly v1.3 machinery | 3.8 | 32 | — | 0.7 | −62% |

T weights: 40% H80, 10% each frog-in-the-pan, recency of high, residual momentum, low share growth; 5% each low short interest, age, commodity-driver momentum, low maximum daily return.

What phase 1 showed:
- Buying the highest "+50% probability" shares lost money. The classifier works as a classifier and fails as a portfolio.
- Trading speed is the main lever, and slower is better. Each step from exit line 30 to 60 to 120 added 4 and then 1.6 points a year.
- **The all-family score did not beat price-only H80 in the same machine (5.7% against 7.1%).** The pre-registered claim "all information beats price-only" failed here, in development.
- The stop-loss cost 1.1 points. Exposure caps did nothing measurable. The market-trend switch cut the worst fall from −48% to −29%, all of it in 2008.

## 4. Phase 2 — the redesign under report 72's brief (development only)

**4.1 Stage A: six inputs never tested before.** Weekly regression of the cleaned 12-month return on the H80 percentile plus the candidate, 184 four-weekly formations Dec 2000–Dec 2014. Gate: |t| ≥ 2.0 and the same sign in both halves.

| Trial | Input | Slope | t | First half | Second half | Gate |
|---|---|---|---|---|---|---|
| A1 | Amihud illiquidity | +0.024 | 0.6 | +0.076 | −0.027 | fail |
| A2 | Traded-value ratio, 63 / 252 days | +0.017 | 0.9 | +0.066 | −0.032 | fail |
| A3 | Share of zero-volume days | −0.087 | **−2.4** | −0.065 | −0.109 | **pass** |
| A4 | 65-day change in short interest (2010–14, 56 formations) | −0.008 | −0.3 | −0.031 | +0.016 | fail |
| A5 | Momentum × size (momentum counts for more in less-traded shares) | +0.203 | **3.0** | +0.230 | +0.177 | **pass** |
| A6 | H80 × miner (dated commodity exposure) | +0.012 | 0.2 | −0.084 | +0.109 | fail |

**4.2 Scores in the brief's trading form** (weekly; buy rank ≤ 30; hold while rank ≤ 90; sale candidate after two readings below; swap only if expected gain ≥ 2 × costs and tax; caps; no stops). RS is now after tax under current law.

| Trial | Score | RS | A$25k | A$100k | Lead over REF | Halves (2005–10 / 2010–15) | Entries: rose ≥ 50% / fell ≥ 50% | Decision |
|---|---|---|---|---|---|---|---|---|
| — | H82 yearly review (replication) | 4.3 | 4.3 | 4.4 | — | — | — | baseline |
| T7 | REF = H80 score, weekly form | 3.3 | 3.8 | 2.9 | — | 0.8 / 8.2 | 12.1% / 2.9% | weekly form is 1.0 point behind yearly |
| T8 | **CH** = mean of H80, low zero-volume share, momentum × size | **5.6** | 7.4 | 3.8 | **+2.3** | 1.8 / 11.8 | 12.4% / 5.4% | passes; 95th percentile of 20 shuffled-input placebos (median 3.7, 90th 5.2) → **adopted** |
| T9 | M1: small boosted-tree model, rank target, 13 features, 10 seeds | 3.8 | 4.5 | 3.0 | +0.4 | 3.6 / 11.0 | 10.2% / 4.7% | no difference; not adopted |
| T10 | M2: P(+50%) − 1.7 × P(−50%) | 1.2 | −0.2 | 2.6 | −2.1 | 2.4 / 3.9 | **16.2%** / 8.9% | worse; not adopted |
| T11 | CH with the 50% hold line (rank ≤ 150) | 4.5 | 5.1 | 3.8 | — | 1.0 / 13.1 | 10.1% / 4.1% | 1.1 points below the 30% line; line stays at 90 |

Base rates in the traded universe over the same weeks: 11.0% rose ≥ 50%, 10.8% fell ≥ 50%.

Notes:
- The machine-learning models did not beat a plain average. M2 again finds winners (16% against 11%) and again does not turn that into return.
- Model gain by family (M1): trend 42%, risk 21%, liquidity 18%, size and age 13%, short selling 3%, share issuance 2%.
- CH's lead is uneven: +3.6 points at A$25,000, +0.9 at A$100,000. At A$100,000 in the December account it earned 4.0% after costs against H82's 3.1%: inside the noise floor.
- The patched engine reproduces report 64's H82 development figure exactly (9.741% at A$25,000, 2001–2015).

**Final engine, frozen before the look:** score CH, trading form W, hold line 90. Full text in section 8.

## 5. The one look

After costs unless stated. "CL" = current law (32%, 50% discount after 12 months). "AN" = the announced July-2027 design applied throughout (cost base indexed to CPI after 12 months, no discount). "ST" = no discount, no indexation. "+fr" = franking credited (75% assumed for the engine's dividends; 74% for the index fund, the VAS issuer average 2018–2026).

### 5.1 Unseen B — EODHD total return, 29 Dec 2017 to 13 Nov 2026 (the cleaner test)

| % a year | New engine A$25k | H82 A$25k | New engine A$100k | H82 A$100k | ASX 200 fund | 40/60 plan |
|---|---|---|---|---|---|---|
| Before costs | 7.4 | 10.0 | 7.3 | 10.4 | — | — |
| **After costs** | **5.2** | **9.6** | **7.6** | **9.7** | **8.8** | **11.9** |
| After tax, CL | 2.3 | 7.2 | 5.3 | 7.5 | 6.8 | — |
| After tax, CL + franking | 2.6 | 8.2 | 5.0 | 8.4 | 7.7 | 10.3 |
| After tax, AN + franking | 4.4 | 7.8 | 4.8 | 7.8 | 8.0 | 9.8 |
| After tax, ST | 4.4 | 6.6 | 4.7 | 6.7 | 6.2 | 9.1 (+fr) |
| Excess over the index fund (t) | −1.6 (−0.3) | +1.4 (0.3) | +0.5 (0.1) | +1.3 (0.4) | — | — |
| Tracking error | 16.4 | 12.5 | 14.9 | 8.7 | — | — |
| Worst fall | −41% | −23% | −35% | −26% | −27% | −18% |
| Trades a year | 24 | 25 | 47 | 52 | — | — |
| Mean / median hold, days | 326 / 195 | about 1 year | 347 / 210 | about 1 year | — | — |
| Positions held under 90 days | 12% | — | 17% | — | — | — |
| Costs, % of balance a year | 1.0 | 0.8 | 0.6 | 0.6 | — | — |
| Percentile among 1,000 random-score runs, same machine | 45 | 84 | 71 | 91 | — | — |
| Percentile among 1,000 matched random buy/sell runs | 59 | — | 77 | — | — | — |
| Bootstrap, share of paths ahead of H82 | 0.24 | — | 0.43 | — | — | — |
| Deflated Sharpe, N = 427 (N = 1,000) | 0.02 (0.02) | 0.08 | 0.05 (0.04) | 0.10 | — | — |
| Stress, CL: costs × 1.5 / 39% tax / unexplained delistings at 70% | 2.2 / 0.7 / −1.1 | 7.5 / 6.9 / 5.7 | 5.1 / 5.0 / 3.3 | 7.3 / 7.0 / 5.8 | — | — |
| After costs at the A$3 brokerage tier | 4.7 | — | 7.3 | — | — | — |
| Plain 12-1 momentum, 10 names (negative control), after costs | −1.8 | — | 0.9 | — | — | — |

Odd-looking cells are path noise, not errors: with 10 to 30 whole-share positions, a different tax or brokerage bill changes which buys fit, and the account takes a different path. That is why "after tax CL" can sit below "ST", and the A$3 tier below the A$6.60 tier. Differences of that size mean nothing (the one-point noise floor).

Excess over the index fund by calendar year, points:

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| New engine A$100k | −5.6 | +27.8 | +17.8 | −2.2 | **−31.1** | +3.7 | +7.9 | −0.3 | −10.6 |
| H82 A$100k | −10.9 | −4.8 | +18.8 | +16.3 | −12.5 | −3.3 | +9.6 | +7.1 | −4.4 |
| New engine A$25k | −9.9 | +31.9 | +9.4 | −12.2 | −27.9 | −15.5 | −3.8 | +18.2 | −3.4 |

Five positions (Pro Medicus A$44,031, Codan, Neuren, SRG, Emerald) made 132% of the A$100,000 account's total profit of A$65,607. The other 200-odd positions lost money in total. 39% of positions made a profit.

**Benchmarks from their first day** (after costs, before the investor's tax, same dates, A$100,000):

| From | Fund | Fund's return | New engine | H82 | ASX 200 fund | 40/60 |
|---|---|---|---|---|---|---|
| 29 Dec 2017 | VHY | 10.0 | 7.6 | 9.8 | 8.8 | 11.9 |
| 29 Apr 2022 | AQLT | 13.7 | 4.7 | 8.4 | 8.6 | 13.5 |
| 31 Jul 2024 | MTUM | 5.0 | 8.5 | 12.4 | 9.0 | 12.6 |

**The owner's account: A$5,000 plus A$500 at each month-end, 29 Dec 2017 to 13 Nov 2026.**

| A$ at the end | Paid in | 40/60 index plan | H82 | New engine |
|---|---|---|---|---|
| Before tax (plan not sold) | 58,000 | 107,858 | 98,321 | 64,330 |
| After tax, current law + franking (everything sold) | 58,000 | **98,662** | 88,671 | **66,026** |
| After tax, announced law + franking | 58,000 | 96,269 | 84,923 | 66,143 |
| After tax, no discount | 58,000 | 92,403 | 82,831 | 65,910 |
| Plan held, not sold (distributions taxed) | 58,000 | 105,048 | — | — |

The new engine made 27 trades a year in this account, paid A$3,348 in brokerage and spread, held a typical position 257 days, and finished at the 16th percentile of 1,000 random accounts run through the same rules (their median: A$76,690 before tax). H82's figure includes one extra A$500 (the frozen engine adds a contribution in the final month).

**A$5,000 lump sum** (4 shares): the new engine lost 20% in its first year, fell below A$4,000, and from then on could not place an order because every order must be at least A$1,000 (a v1.3 rule). It sat in cash and ended at −4.6% a year. H82 at A$5,000 earned 10.3% after costs on this set and −5.3% on unseen A, where the same thing happened to it. Four-share accounts are a coin toss, as reports 51 and 53 said.

### 5.2 Unseen A — panel_v2, price only, 31 Dec 2015 to 31 May 2024 (re-used holdout, no dividends)

| % a year | New engine A$5k | New engine A$25k | H82 A$25k | New engine A$100k | H82 A$100k | XJO price index |
|---|---|---|---|---|---|---|
| Before costs | 9.8 | 9.8 | 2.9 | 12.3 | 4.9 | — |
| **After costs** | 9.4 | **9.7** | **1.6** | **9.5** | **4.0** | **4.6** |
| After tax, CL | 2.9 | 8.7 | 1.1 | 8.4 | 3.1 | 3.9 |
| After tax, AN | 2.0 | 7.6 | 0.8 | 7.5 | 2.5 | 4.1 |
| After tax, ST | 2.0 | 7.5 | 0.7 | 7.3 | 2.3 | 3.3 |
| Excess over the index (t) | +8.0 (1.0) | +6.7 (1.2) | −2.3 (−0.5) | +5.7 (1.3) | −0.3 (−0.1) | — |
| Worst fall | −47% | −36% | −30% | −34% | −27% | −28% |
| Trades a year | 8 | 21 | 20 | 43 | 55 | — |
| Mean / median hold, days | 441 / 266 | 433 / 213 | — | 387 / 210 | — | — |
| Positions held under 90 days | 22% | 20% | — | 19% | — | — |
| Costs, % a year | 0.8 | 0.6 | 1.0 | 0.5 | 0.7 | — |
| Percentile among 1,000 random-score runs, same machine (median random) | 80 (2.0) | **88** (4.5) | 38 | **83** (6.7) | 57 | — |
| Percentile among 1,000 matched random buy/sell runs | 90 | 98 | — | 99 | — | — |
| Bootstrap vs H82 | 0.95 | 0.92 | — | 0.87 | — | — |
| Deflated Sharpe, N = 427 (N = 1,000) | 0.25 | 0.32 (0.27) | 0.01 | 0.35 (0.30) | 0.04 | — |
| Stress, CL: costs × 1.5 / 39% tax / delistings 70% | 2.1 / 6.9 / 0.6 | 8.7 / 8.4 / 8.1 | 0.8 / 1.0 / 0.0 | 8.9 / 8.3 / 5.4 | 2.8 / 2.9 / 2.0 | — |
| Plain 12-1 momentum, 10 names | −4.7 | −1.5 | — | 2.4 | — | — |

Excess by year, A$100,000: 2016 −6.7, 2017 +27.1, 2018 +10.4, 2019 +15.2, 2020 +10.6, 2021 +8.0, 2022 −23.0, 2023 +6.8, 2024 (5 months) +5.3.

Five positions (WiseTech A$38,049, Pro Medicus A$28,013, Saracen, Xero, Seven Group) made 102% of the account's total profit of A$114,325. At A$25,000: WiseTech, Seven Group, Xero, Appen and Data#3 made 120%.

Why this is not a pass:
- **Random picking through the same rules did nearly as well.** The trading form itself (keep what is above the line, sell losers, never sell a share sitting on a large taxed gain) earned 6.7% at the median with random scores at A$100,000, against 3.4% for random yearly portfolios and 4.6% for the index. Most of the engine's lead over H82 on this set is the form's "let winners run" behaviour in a period when a few technology shares rose tenfold. The score added about 3 points on top, at the 83rd percentile.
- **The same form added nothing on unseen B** (random-score median 6.1% against 6.1% for random yearly portfolios).
- **The two sets disagree on the years they share.** For 2018–2023 the engine's excess is +10, +15, +11, +8, −23, +7 on panel_v2 and −6, +28, +18, −2, −31, +4 on EODHD. Different start date, different comparator (price against total return), different data vendor, and a book of 30 shares that had already found its winners in one case and not in the other. A result that depends on which year the account started is not an edge.

### 5.3 Pass / fail against the pre-registered bars

| Bar (needed at A$25k and A$100k on both sets) | Unseen A | Unseen B |
|---|---|---|
| After tax above H82 by ≥ 1.0 point (CL and AN) | yes (+5 to +8) | **no** (−2 to −5) |
| After tax above the index comparator | yes | **no** |
| Ahead of the 40/60 plan on the same dollars | not testable (no dividends) | **no** |
| ≥ 90th percentile of random-score runs | **no** (88, 83) | **no** (45, 71) |
| ≥ 90th percentile of matched random buy/sell runs | yes (98, 99) | **no** (59, 77) |
| Bootstrap vs H82 ≥ 0.90 | 0.92 / **0.87** | **no** (0.24, 0.43) |
| Deflated Sharpe ≥ 0.95 | **no** (0.32, 0.35) | **no** (0.02, 0.05) |
| Lead not from five or fewer positions | **no** | **no** |
| **Verdict** | did not pass | did not pass |

### 5.4 The big-wins scorecard (non-void 12-month outcomes after each entry)

| | Unseen A: rose ≥ 50% | fell ≥ 50% | Unseen B: rose ≥ 50% | fell ≥ 50% |
|---|---|---|---|---|
| All 300 traded shares, every week (base rate) | 10.4% | 5.4% | 11.0% | 7.0% |
| Top 30 by the new score, every week | 10.3% | 3.2% | 12.1% | 6.4% |
| Top 30 by H80, every week | 6.7% | 1.5% | 8.4% | 1.8% |
| New engine's actual buys, A$100k (171 / 207 buys) | 9.9% | 3.5% | 12.6% | 5.8% |
| New engine's actual buys, A$25k (79 / 102) | 16.5% | 2.5% | 10.8% | 7.8% |
| H82's buys, A$100k (218 / 225) | 8.3% | 1.8% | 8.9% | 1.8% |

Neither engine finds 50% winners at a rate above chance. H82 finds slightly fewer than chance and avoids wrecks three to four times better than chance; that is all its edge has ever been. The new score gives up half of that protection to get back to the base rate of winners. The winners both engines did hold for years (Pro Medicus, WiseTech, Xero, NEXTDC in earlier reports) were bought as steady risers, not predicted as rockets.

Precision, recall and calibration of the P(+50%) model were computed in development only (section 3.1): by the one-look rule the learned models were not scored on unseen data, because the final engine does not use them.

## 6. Answers to the owner's points

- **"You have so much information and you aren't using it."** It has now all been put through one model and one engine, together, with the big-win target tried directly. The dated, bias-free part of that information is smaller than it looks: prices and volume, eleven macro and commodity series, and (from 2010) short selling and share counts. Sector history, announcements and fundamentals cannot be used honestly because our copies only cover companies that survived. Inside the usable set, price and liquidity carry the signal; the rest added nothing that lasted.
- **"If it needs to be sold in two weeks, sell it."** The engine does this when the readings say so: about one position in six was sold within 90 days and one in ten within about 60. What the tests show is that an engine made to sell faster loses more to brokerage, spread and tax than it gains: 5 points a year at the fastest setting tried, on an A$25,000–100,000 account.
- **Commodities as risk control.** Dated exposure clusters (gold, bulk and base metals, energy) are built and capped in the engine. In development the caps moved the worst fall by one point. They describe the book's risk well and do not change its return.

## 7. What goes forward

| Item | Decision | Card |
|---|---|---|
| H82, rules v1.3 | Unchanged. Paper record starts at the 31 Dec 2026 formation as planned | H82 |
| New engine (CH score, weekly form) | **Not passed. No paper card.** May be recorded as a shadow line at no cost (weekly snapshot only); no promotion without 36 forward months | H138 (closed for promotion) |
| P(+50%) classifier portfolios | Closed. Finds winners, loses money | H139 (closed) |
| Zero-volume share; momentum × size | Development facts that did not hold up consistently. Panel flags only | H140 |
| Amihud, value ratio, short-interest change, miners × H80 | Closed at the development gate | H140 |
| Market-trend entry block | Observation only (one episode). Not carried: market timing is ruled out by R38/R39/R48 | H121 note |
| Forward snapshot columns | Added by `allinfo/code/snapshot_addon.py` (first file `out/forward_addon_2026-11-13.csv`, 300 rows): H80 and CH score and rank, 12-month share growth, short-interest level and 65-day change, eight exposure t-values, commodity cluster, dated industry group, three printed flags, and five empty forward-only columns (results-day reaction, director buying, analyst revision, fundamentals reference, results within five days) | — |
| Real money | Stays in the 40/60 plan | — |

Not done, and why:
- Daily commodity lead (R60's open item): no trial left in the budget. Still untested.
- Unseen scoring of the learned models, and the price-only score in the weekly form on unseen data: each would be a second look.
- Blind replication of this report's engine by another agent (T8 of report 72).
- The takeover rule of report 72 §4.6 and hand-read delisting outcomes after April 2020: need announcement data.

## 8. Rule text of the tested engine (for replication only; it did not pass and is not a paper rule)

Parts A (inputs), C1 (payouts), E (costs), F1–F4 (tax, with the regime changes below), G and I–J of rules v1.3 apply unchanged. Only what differs is stated.

**W1. Decision day.** W = the last trading day (v1.3 A1) of each calendar week, Monday to Sunday. The file's final partial week has no decision day unless it ends on a Friday.

**W2. Universe at W.** v1.3 B1 computed at W: companies with a close on at least 200 of the 252 trading days ending W, ordered by median daily traded value over those days (ties in identifier order). The first 300 are the traded universe. Position in that order = traded-value rank.

**W3. Signals at W** for each traded-universe company, with P(d) the adjusted close of d or the most recent within the previous 10 trading days:
- s1 = P(W−21) ÷ P(W−252) − 1; s2 = P(W) ÷ P(W−126) − 1 (offsets in trading days);
- s3 = P(W) ÷ highest adjusted close on a day with a close among the 252 days ending W;
- s4 = −(sample standard deviation of the daily log returns dated in those 252 days; at least 200 required; a return exists only if that day and the previous trading day both have a close);
- H80 = mean of the four percentiles (v1.3 B3) inside the traded universe; missing if any part is missing;
- z = share of the 252 days with no close (zero-volume share);
- q = (pct(s1) − 0.5) × (pct(traded-value rank) − 0.5), percentiles inside the traded universe, rank 300 having the highest percentile.

**W4. Score.** CH = [pct(H80) + pct(−z) + pct(q)] ÷ 3, percentiles inside the traded universe among companies that have the value (ties share the average rank). No H80 = no score. Score rank 1 = highest CH; ties in traded-value-rank order. pctl(c) = 1 − (rank − 1) ÷ (number ranked); 0 if unranked.

**W5. Book size.** At each W, after payouts: NAV = cash + Σ shares × last(W); n = min(30, max(4, floor(NAV ÷ 2,500))); T = NAV ÷ n.

**W6. Below-line counter.** For each holding, b = number of consecutive decision days, ending at W, on which its score rank was worse than 90 or missing.

**W7. Sale candidates.** Holdings with b ≥ 2, except: (a) tax clock — value > cost of remaining lots, its oldest lot is 300 to 366 calendar days old at W, and its rank is 210 or better; (b) June — if W is one of the last two decision days of June and value ≤ cost, the holding is sold outright (no test).

**W8. Caps for buys**, counted over holdings that stay plus buys already chosen at this W:
- industry group (v1.3 A11): fewer than ceil(0.25 n) already in the group; unknown never refused;
- Materials plus Energy groups together: fewer than ceil(0.30 n);
- commodity cluster: fewer than max(1, ceil(2 × w × n)), w = the cluster's share of the traded universe's summed median traded value at W. A company's cluster: take the univariate t-statistics of its monthly returns (month-end adjusted closes) on the monthly log changes of gold, iron ore, copper, Brent, coal, nickel, aluminium and zinc over the 60 months ending two month-ends before the latest month-end strictly before W (at least 24 months), clipped at ±4. If the largest is ≥ 2: GOLD if it is gold, ENERGY if Brent, otherwise BULK-BASE. Else no cluster.

**W9. Buy-eligible.** Has a close on W; P(W) ≥ A$0.50; median traded value ≥ 100 × T; not held; score rank ≤ 30; passes W8.

**W10. Decisions at W, in order.** (1) Payouts (v1.3 C1). (2) W7(b) sales. (3) Vacancies = n − holdings not being sold: filled with the best-ranked buy-eligible companies. (4) Swaps: candidates in order of worst rank first. Replacement R = best-ranked buy-eligible company not yet chosen, with the candidate removed from the cap counts. V = shares × last(W). EG = 0.5 × 0.20 × (pctl(R) − pctl(candidate)). COST = [max(6.60, 0.00088 V) + max(6.60, 0.00088 T) + h(candidate) × V + h(R) × T + TAXNOW] ÷ V, with h = v1.3 E2 half-spread at W's rank and TAXNOW = 0.32 × max(0, Gs + 0.5 × Gl) when Gl > 0, else 0.32 × max(0, Gs + Gl); Gs, Gl = unrealised gains at last(W) on lots younger than / at least 367 days. If EG ≥ 2 × COST the candidate is sold in full and R bought for T; otherwise nothing. (5) Trim: a holding that stays with value > max(0.15 NAV, 2T) is sold down by floor((value − max(0.10 NAV, 4T ÷ 3)) ÷ last(W)) shares; lots at least 367 days old go first, highest cost per share first, then the rest oldest first. Full sales take lots oldest first.

**W11. Execution.** At the close of the next trading day: sells, then buys in the order chosen. A sell with no close that day carries to the next day with one (v1.3 D1). A buy: a = min(T, cash − tax reserved if positive); dropped if a < max(1,000, 0.5 T) or there is no close; shares = floor((a − brokerage(a)) ÷ (close × (1 + h))). Impact: an order above 1% of the company's median daily traded value pays a further 0.5 × (252-day daily standard deviation) × sqrt(order ÷ median value) on top of h. No orders on the account's end date.

**W12. Tax regimes.** CL = v1.3 regime A. AN = lots at least 367 days old taxed on max(0, proceeds − cost × CPI(sale month) ÷ CPI(purchase month)), no discount; losses nominal. ST = v1.3 regime B. Franking option: tax on dividends = 32% × (cash + credit) − credit, credit = cash × f × 30/70, f = 0.75.

**W13. Not in the rule.** No stop, no trend exit, no market-state switch, no minimum hold, no top-ups, no deferral other than W7(a).

Controls: random-score = each traded-universe company carries a uniform random score, redrawn with probability 1/26 each week. Matched placebo = at each W the same number of sales as the engine made (W7(b) plus swaps), applied to random holdings; vacancies filled with random companies passing W9 without the rank test.

## 9. Limits, deviations and reasons this could be wrong

- **One early peek.** A machinery test of the index-plan code printed two lines of unseen-B hit rates (the "top 30 every week" rows of section 5.4) about two minutes before the code freeze. No engine return was visible, the final engine had already been fixed by the development log, and nothing was changed afterwards.
- **Look A was run twice.** The first run was killed for memory after the A$5,000 block; the fix clears the frozen engine's table cache between random runs and changes no number (`out/unseen2_frozen_before_oomfix.py` is the original). The A$5,000 block printed identically both times.
- **Phase 1 was run before report 72 arrived**, on a +50% target that the review rightly rejected. Its 12 trials are counted. What it showed (wide exit lines do better; all-family T is not better than H80) was known when PREREG_70c was written, and is listed there.
- **Deviations from report 72's instructions** (declared in PREREG_70c §9): v1.3's universe and A$0.50 floor were kept instead of the 63-day / 20-cent universe; A$5,000 and A$25,000 are reported in full at the coordinator's instruction; 1,000 random runs instead of 200; the brief's "tax brought forward" was read as the whole tax due on the gain, which makes the engine hold large winners almost indefinitely.
- **That last reading matters.** A holding with an untaxed gain above roughly 13% (short-term) or 26% (long-term) of its value can never pass the swap test, whatever its rank. This is the main reason the form "lets winners run", and the main reason random picking did well in it on unseen A. A different reading (time value of the tax only) would trade more and is untested.
- **Sectors are today's**, so industry caps are weaker in history than in the rule. **Delistings after April 2020 are paid in full**; at 70% the engine loses 2 to 3.4 points on unseen B.
- **Franking is assumed** at 75% for every dividend the engine receives.
- **The announced CGT design** is applied as if in force for the whole period; the transition split at 30 June 2027 and the 30% floor (which does not bind at 32%) are not modelled. Whether it is law was not checked.
- **Development is price-only.** The label is a price return, and the engine's development lead over the index is overstated by about one point of dividends.
- **Models were trained on panel_v2**, an unlicensed copy with known split errors; cleaned labels remove the flagged ones only.
- **Deflated Sharpe code** is still the programme's unverified implementation.
- **Not replicated.** Nobody has rebuilt this engine from section 8.

## 10. Files

- Pre-registrations and hashes: `allinfo/PREREG_70.md`, `PREREG_70c.md`, `out/prereg70_hash.txt`, `out/prereg70c_hash.txt`, `out/phase1_hashes.txt`, `out/freeze_before_look_hashes.txt`, `out/result_hashes.txt`.
- Code: `code/feat.py` (weekly features and labels), `model.py` / `model2.py` (walk-forward models), `stageA.py`, `aiw.py` (phase-1 engine), `aiw2.py` (tested engine), `engine_dd_p.py` (frozen v1.3 engine plus franking and the announced tax regime), `common.py`, `common2.py`, `dev.py`, `dev2.py`, `dev2b.py`, `unseen2.py`, `metrics.py`, `snapshot_addon.py`.
- Results: `out/dev.log`, `dev_results.json`, `dev_classification.csv`, `importance_gain_dev.csv`, `importance_perm_dev.csv`, `stageA2.json`, `dev2.log`, `dev2b.log`, `dev2_results.json`, `importance2_gain_dev.csv`, `look_A.json`, `look_B.json`, `look_A.log`, `look_B.log`, `holdout_looks_70.csv`, `trials_70.csv`, `forward_addon_2026-11-13.csv`, `PROGRESS.md`.
