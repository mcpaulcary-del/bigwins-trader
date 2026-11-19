Research is complete enough to set the spec, with one process caveat: WebFetch could not resolve any host and search was rate-limited mid-run, so I read primaries by direct download where the proxy allowed. Hosts that stayed blocked: `www.asx.com.au` (SR15 reports), `papers.ssrn.com`, `cmegroup.com`, `people.duke.edu`, `dspace.mit.edu`, `carmamaths.org`, `alphaarchitect.com`. Those need allowlisting to close the gaps flagged below.

Tags: **[2+]** = two independent sources agree; **[1]** = one source; **[unverified]** = could not confirm; **[computed]** = my own calculation from a verified formula. "Read" means I read the page text itself; "search" means a search-engine extract only.

## 1. Annotated bibliography

| # | Source | Finding used | How verified | Tag |
|---|---|---|---|---|
| 1 | Bailey, Borwein, López de Prado, Zhu, "Pseudo-Mathematics and Financial Charlatanism" (2014), [PDF](https://carmamaths.org/jon/backtest.pdf) | With 5 years of daily data, about 45 tried variants are enough to expect a Sharpe 1.0 backtest from pure noise. The number of trials must be reported. | Author slides, news release and an R replication (4.998 years for N=45), all search; my own calculation agrees | [2+] |
| 2 | Same authors, "The Probability of Backtest Overfitting", J. Computational Finance 2017, DOI 10.21314/JCF.2016.322, [SSRN](https://papers.ssrn.com/abstract=2326253) | Hold-out is "unreliable" for backtests; CSCV gives a model-free PBO estimate. No numeric pass threshold is given. | RePEc and SSRN abstracts (search) | [2+] |
| 3 | Bailey & López de Prado, "The Deflated Sharpe Ratio", JPM 2014, [SSRN](https://papers.ssrn.com/abstract=2460551) | Corrects Sharpe for number of trials, skew and kurtosis. | SSRN abstract and CXO Advisory (search) | [2+] |
| 4 | Bailey & López de Prado, "The Sharpe Ratio Efficient Frontier", J. Risk 2012, [RePEc](https://ideas.repec.org/a/rsk/journ4/2223785.html) | MinTRL = 1 + (1 − γ3·SR + ((γ4−1)/4)·SR²)·(z/(SR−SR*))². | RePEc abstract (read); formula from the PerformanceAnalytics implementation (search) | [2+] |
| 5 | Lo, "The Statistics of Sharpe Ratios", FAJ 2002, [CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios) | "The annual Sharpe ratio for a hedge fund can be overstated by as much as 65 percent because of the presence of serial correlation." | CFA page (read); RePEc (search) | [2+] |
| 6 | Harvey & Liu, "Backtesting", JPM 2015, [PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF) | The flat 50% haircut is wrong. Sharpe below 0.4 gets a haircut above 50%; Sharpe above 1.0 gets at most 25%. | [CXO Advisory](https://www.cxoadvisory.com/?p=24128) (read; it covers the 2013 draft); Duke PDF (search) | [2+], figures may differ by draft |
| 7 | Harvey, Liu, Zhu, "…and the Cross-Section of Expected Returns", RFS 2016, [RePEc](https://ideas.repec.org/a/oup/rfinst/v29y2016i1p5-68..html) | "A new factor needs to clear a much higher hurdle, with a t-statistic greater than 3.0." | RePEc abstract (read); NBER w20592 (search) | [2+] |
| 8 | Suhonen, Lennkh, Perez, "Quantifying Backtest Overfitting in Alternative Beta Strategies", JPM 2017 | Across 215 bank strategies, median Sharpe was 1.20 in backtest and 0.31 live (73% deterioration). Only 18 of 215 did better live. | [CXO Advisory](https://www.cxoadvisory.com/big-ideas/live-performance-of-alternative-beta-products/) (read); Alpha Architect (search) | [2+]; sources disagree on 15 vs 17 banks |
| 9 | Wiecki et al., "All that Glitters Is Not Gold" (Quantopian, 2016), SSRN 2745220 | Across 888 algorithms, backtest Sharpe predicts out-of-sample Sharpe with R² below 0.025. Volatility (R² 0.67) and drawdown (0.34) do persist. | Quantpedia and CXO Advisory (search) | [2+] |
| 10 | White, "A Reality Check for Data Snooping", Econometrica 2000; Hansen, "A Test for Superior Predictive Ability", JBES 2005; Sullivan, Timmermann, White, JF 1999 | The best of 7,846 technical rules on 100 years of DJIA did not hold up in 1987–96. Hansen's test is "more powerful and less sensitive to poor and irrelevant alternatives". | Search only; the 1999 out-of-sample result is from secondary summaries | [2+] secondary |
| 11 | Carver, ["How much risk should we take?"](https://qoppac.blogspot.com/2020/03/how-much-risk-should-we-take.html) (2020) | "Optimal risk target = Expected Sharpe Ratio… A better rule of thumb is to use half." Expected Sharpe for a simple one-rule, one-instrument retail system is 0.24, giving a 12% target. Use the most conservative of all constraints. He runs 25%. | Post (read); search | [2+] |
| 12 | Carver, *Systematic Trading* (cost "speed limit") | Costs should be at most one third of a conservative pre-cost Sharpe, roughly 0.13 Sharpe units a year per subsystem. | Two secondary book summaries (search) | [2+] secondary |
| 13 | MacLean, Thorp, Ziemba, "Good and bad properties of the Kelly criterion", Quantitative Finance 2010, DOI 10.1080/14697688.2010.506108 | Full Kelly maximises long-run growth but can lose most of wealth along the way; fractional Kelly trades growth for security. | Search (two records) | [2+] qualitative |
| 14 | Harvey et al., ["The Impact of Volatility Targeting"](https://www.man.com/insights/the-impact-of-volatility-targeting), JPM 2018 | Improves Sharpe for equities and credit only; "negligible" for bonds, currencies and commodities. Reduces left tails and max drawdown across 60+ assets. | Man Group page and Quantpedia abstract (both read) | [2+] |
| 15 | Moreira & Muir, "Volatility-Managed Portfolios", JF 2017, [NBER w22208](https://www.nber.org/papers/w22208) | Portfolios that cut risk when volatility is high "produce large alphas". Market-factor alpha 4.9% a year, about 25% Sharpe gain. | NBER abstract (read); the numbers are search only | [2+] claim, [1] numbers |
| 16 | Cederburg et al., "On the performance of volatility-managed portfolios", JFE 2020, DOI 10.1016/j.jfineco.2020.04.015 | Real-time versions "generally earn lower certainty equivalent returns and Sharpe ratios". Worse in 72 of 103 strategies. | RePEc abstract and [CXO Advisory](https://www.cxoadvisory.com/volatility-effects/does-volatility-management-work-for-equity-factor-portfolios/) (both read) | [2+] |
| 17 | Kaminski & Lo, "When do stop-loss rules stop losses?", JFM 2014, DOI 10.1016/j.finmar.2013.07.001 | Under a random walk the stop premium is negative. Stops help only with momentum or regime-switching. | RePEc abstract (read); MIT abstract (search) | [2+] |
| 18 | Lo & Remorov, "Stop-loss strategies with serial correlation, regime switching, and transaction costs", JFM 2017 | "Tight stop-loss strategies tend to underperform the buy-and-hold policy due to excessive trading costs." Wide 10-day stops roughly match buy-and-hold. A one-day execution delay is not harmful. | [CXO Advisory](https://www.cxoadvisory.com/?p=27891) (read); journal abstract (search) | [2+] |
| 19 | Grossman & Zhou, "Optimal investment strategies for controlling drawdowns", Mathematical Finance 1993, DOI 10.1111/j.1467-9965.1993.tb00044.x | Optimal risky exposure is proportional to the cushion above a trailing floor. Klass & Nowicki (2005) show this is not optimal in discrete time. | Two RePEc records (search) | [2+] qualitative |
| 20 | Frazzini, Israel, Moskowitz, ["Trading Costs"](https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs) (AQR, 2018) | On US$1.7 trillion of live trades, actual costs are "an order of magnitude smaller than previous studies suggest". Zero impact for retail-size orders is my inference. | AQR page (read) | [1] |
| 21 | IBKR Australia, [stock commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php) and [ASX fees](https://www.interactivebrokers.com.au/en/accounts/fees/ASX-Fees.php) | Fixed: 0.08%, minimum A$6.00 ex-GST, third-party fees "None". The GST-inclusive example (400 shares at A$50 = A$17.60) implies 0.088% and an A$6.60 minimum. Tiered: 0.08%, minimum A$5.00, plus exchange 0.00165% (auction 0.00308%) and clearing 0.002475%, all ex-GST. | Pages (read); search | [2+], one vendor |
| 22 | IBKR, [US stock commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-stocks.php) and [FX](https://www.interactivebrokers.com.au/en/pricing/commissions-spot-currencies.php) | Tiered US$0.0035 a share, minimum US$0.35; fixed US$0.005, minimum US$1.00; cap 1% of value. Tiered adds clearing US$0.0002 a share and SEC fee 0.00206% of sale value. FX 0.2 bp, minimum US$2. | Pages (read); search | [2+], one vendor |
| 23 | IBKR, [futures commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-futures.php) and [CME fees](https://www.interactivebrokers.com.au/en/accounts/fees/CME.php) | CME micros (MES, MNQ, M2K, MYM, MGC and others): US$0.25 a contract, plus exchange US$0.35 and regulatory US$0.01. Micro FX: US$0.15. | Pages (read); the search extract matches | [2+], one vendor |
| 24 | CME, [MES contract specs](https://www.cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.html) | Multiplier US$5; tick 0.25 points = US$1.25; calendar-spread tick 0.05 = US$0.25. | Two CME pages (search) | [2+] |
| 25 | ASX SR15 post-implementation reports ([Aug 2025](https://www.asx.com.au/content/dam/asx/markets/trade-our-cash-market/equity-markets-working-groups/asx-trade-service-release-15-post-implementation-report.pdf), [Nov 2025](https://www.asx.com.au/content/dam/asx/markets/trade-our-cash-market/equity-markets-working-groups/asx-sr15-post-implementation-report-november-2025.pdf)) | The staggered open became a single randomised open (live 30 June 2025). Spreads tightened overall, but in the first two minutes "both price variance and average spread are elevated". | Search extracts of both reports; not read, and no ETF-specific numbers obtained | [2+] qualitative |
| 26 | [ASIC Report 583](https://download.asic.gov.au/media/etod0gwe/rep583-published-02-august-2018-20210526.pdf) (2018); Betashares, VanEck, Firstlinks, Livewire | ETP spreads are generally narrow but can temporarily widen. Spreads are U-shaped through the day, elevated at the open and in the closing auction. Large ETFs such as IVV and VGS run about 0.02%; the Australian-equity ETF category averaged 0.09% in May 2020. | Search; each spread number has one source | [2+] pattern, [1] numbers |
| 27 | IBKR Guides, "About Paper Trading Accounts" | Paper has "no support for some order types including: VWAP, Auction…"; "fills are simulated from the top of the book"; stops are "always simulated". | Read from a copy already in the session cache; I did not record its URL | [1] |

Disagreements and unresolved items:
- **Volatility targeting:** #15 and #16 conflict; #14 reconciles them. The Sharpe gain is unreliable outside equities, but the tail and drawdown benefit is robust.
- **Stops:** #17 finds they can help, #18 finds tight ones hurt after costs. Both agree the benefit needs trending returns and wide thresholds.
- **Half-Kelly growth cost:** the Kelly algebra gives 75% of full-Kelly growth at half the volatility [computed]. A search extract attributes "about a third less" to Carver; I did not find that wording in the post I read.
- **McLean & Pontiff (JF 2016):** search returned about 32–35% post-publication decay from working-paper versions; the 26%/58% figures commonly cited could not be confirmed [unverified]. No decision depends on which is right.
- **Not reached before the search limit, all [unverified]:** Broman, Petajisto, CME roll-cost studies, the Australian payment-for-order-flow rules, CPCV detail beyond package documentation, and any cap on Carver's diversification multiplier.

## 2. Validation protocol

### What the numbers force

- **Paper trading cannot validate performance.** The standard error of a one-year Sharpe estimate is about 1.0 [computed, Lo's formula]. Time needed to show Sharpe above zero at 95% confidence:

| True Sharpe | Years needed |
|---|---|
| 0.3 | 30 |
| 0.5 | 11 |
| 0.7 | 5.5 |
| 1.0 | 2.7 |

- **Backtest Sharpe is a weak predictor of live Sharpe.** See #8 and #9. Volatility and drawdown do persist, so those are what live trading can be judged on.
- **Selection alone manufactures Sharpe.** Expected best Sharpe from zero-skill variants [computed, DSR formula]:

| Variants tried | 10 years of data | 15 years | 20 years |
|---|---|---|---|
| 20 | 0.60 | 0.49 | 0.43 |
| 100 | 0.80 | 0.65 | 0.57 |
| 500 | 0.97 | 0.79 | 0.68 |

Paper and live gates therefore test implementation and cost assumptions. Only the backtest gate tests the edge.

### Gate 0: pre-registration
- Write down the hypothesis, universe, rule family, parameter grid, cost model and pass criteria before running anything.
- Keep an append-only trial log. Every backtest run, including discarded ones, counts toward N.
- Hard cap N at 50 per strategy family. Use one parameter set for all 7–20 instruments; no per-instrument tuning.

### Gate 1: backtest
Thresholds marked * are my engineering judgment; the literature gives no number.

- **History:** at least 15 years of daily data, including 2008, 2020 and 2022. Where an ETF is younger, use its index with fees and the cost model applied, and flag it as a proxy.
- **Significance:** net-of-cost t-statistic of at least 3.0 if N is above 1 (#7). That means net Sharpe of at least 0.77 over 15 years or 0.67 over 20. A t-statistic of 2.0 is acceptable only for a single pre-registered spec.
- **Deflated Sharpe:** at least 0.95, using logged N and sample skew and kurtosis.
- **PBO:** at most 0.25*, by CSCV with 16 blocks over the full grid.
- **Serial correlation:** report the Lo-adjusted Sharpe; fail if the adjustment removes more than 25%*.
- **Parameter plateau*:** every neighbour within ±25% of each parameter keeps at least 70% of the chosen Sharpe.
- **Breadth*:**
  - at least 70% of instruments contribute positively;
  - no instrument supplies more than 30% of P&L;
  - both halves of the sample are positive;
  - at least 65% of rolling 3-year windows are positive.
- **Cost stress:** still net-positive at twice modelled costs with a one-day execution delay. #18 supports treating the delay as benign.
- **Bootstrap:** stationary block bootstrap, 10,000 paths, mean block of 20 days. Report the Sharpe 5th–95th percentile and the drawdown distribution. The 5th-percentile Sharpe must exceed zero.
- **Benchmark:** compare with buy-and-hold of the same universe at equal volatility, and with a 60/40 portfolio. Report on both the Reality Check and SPA tests if more than one rule family is compared.
- **Report in every run:** N, gross and net Sharpe, turnover, cost drag, skew, kurtosis, maximum and average drawdown, time under water, and Sharpe by instrument and by sub-period.

### Gate 2: paper trading
- **Length:** at least 60 trading days and at least 40 order events, whichever is later.
- **Coverage:** must include a month-end, an ex-dividend date, a holiday and one forced restart or outage drill.
- **Pass criteria*:**
  - no unexplained position breaks against the backtest replay on the same dates;
  - all orders reconciled;
  - daily return correlation with the replay of at least 0.95;
  - mean absolute daily difference of at most 5 bp.
- **Limitation:** IBKR paper does not support auction orders and fills from the top of book (#27). Closing-auction execution, which is the natural end-of-day venue on ASX, cannot be validated on paper. Do not extend paper trading hoping for performance evidence.

### Gate 3: live pilot
- **Size:** 10–25% of intended risk, large enough that most ASX tickets exceed A$2,000 (33 bp at the minimum fee).
- **Length:** at least 3 months and at least 40 fills.
- **Pass criteria*:**
  - realised cost per trade (commission plus slippage against the decision price) at most 1.5 times the model. If it is higher, re-run Gate 1 with realised costs;
  - same tracking tests as Gate 2;
  - realised volatility within 0.7–1.4 times target.

### Gate 4: scale-up and monitoring
- Go to 50% for 3 months, then 100%. Scale on tracking and cost evidence, never on P&L.
- **Do not compare live Sharpe with backtest Sharpe before year 3.** With a standard error near 1.0, a one-year live Sharpe of −0.5 is consistent with a true 0.5. At a 10% target and true Sharpe 0.3, a losing first year has 38% probability [computed].
- **Use the drawdown envelope instead.** At 10% target volatility and Sharpe 0.3, simulated with fat-tailed (t, 5 d.f.) returns [computed]:

| Horizon | Median max drawdown | 95th percentile | 99th percentile |
|---|---|---|---|
| 1 year | 9.5% | 19% | 25% |
| 3 years | 16% | 32% | 41% |

- **Monthly review:** tracking error against replay, cost against model, realised against target volatility, and drawdown percentile against the bootstrap.
- **Kill or re-validate triggers:** a tracking break; costs above twice the model for 3 months; drawdown beyond the 99th percentile; realised volatility above 1.5 times target for 60 days.

## 3. Sizing and risk framework

- **Assumed Sharpe for sizing:** the lower of half the backtest net Sharpe and 0.5 (#6, #8). For a simple end-of-day ETF system, expect 0.25–0.4 (#11).
- **Volatility target:** half-Kelly is half the assumed Sharpe (15% at Sharpe 0.3). Take the most conservative of half-Kelly, risk tolerance and crash-leverage limits, per #11. Decision: 10% annualised at launch, with a hard ceiling of 12% until 3 live years.
- **Crash-leverage test (Carver's method):** the largest gross leverage such that a 1987-size one-day fall of about 23% loses no more than the owner's stated maximum. For a 25% maximum that is about 1.1 times.
- **Position size:** capital × target volatility × weight × diversification multiplier ÷ instrument volatility. Estimate volatility with a roughly 25–35 day exponential window blended 70/30 with a 10-year average. Cap any single volatility-driven upscaling at 1.5 times the long-run-volatility size*.
- **Why scale by volatility:** for tail and drawdown control (#14), not for alpha (#16). Do not count a Sharpe uplift in expectations.
- **Diversification multiplier:** compute it from the correlation matrix (1 ÷ √(w′ρw)) and cap it at 2.0*. Carver's published cap could not be verified.
- **Leverage:** gross at most 1.0 times in the ASX-only phase. In a futures phase, at most 2.0 times notional and margin at most 25% of equity*.
- **Turnover control:** a no-trade buffer of ±10% of target position*, and a minimum ticket (section 4). Annual cost budget is at most one third of assumed Sharpe (#12). At Sharpe 0.3 and 10% volatility that is at most 1.0% of capital a year, with a hard fail at 1.3%.
- **Stops:** no tight per-position stops (#17, #18). The trend or signal exit is the stop.
- **Portfolio drawdown ladder*,** in the spirit of #19 and tied to the envelope above:
  - at −15%, review;
  - at −20%, halve the risk target;
  - at −25%, go flat and repeat Gate 1.
  - Re-risk only at a new 6-month high in the replay, or after a documented re-validation. Do not use a continuous cushion rule; it is not optimal in discrete time.
- **Stress tests:** replay 1987 (index proxy), 2008, March 2020 and 2022, plus a synthetic −23% gap day and a correlation-to-one day. The maximum one-day loss must not exceed 2.5 times target daily volatility × 4*.

## 4. Per-venue cost model

Fees are verified (#21–#24). Spread inputs are assumptions to be replaced with the project's own fill data after the pilot, except where tagged.

| Venue | Commission | Half-spread assumption | Other | One-way all-in |
|---|---|---|---|---|
| ASX share (IBKR fixed) | max(A$6.60, 0.088%) incl. GST; breakeven ticket A$7,500 | ASX 50: 3 bp; ASX 51–200: 8 bp; smaller: 20 bp or more [unverified] | none | A$2k ticket 33 bp + spread; A$5k 13 bp + spread; A$7.5k and above 8.8 bp + spread |
| ASX ETF (IBKR fixed) | same | broad large ETFs 1–2.5 bp ([1]: about 2 bp full spread for IVV/VGS); Australian-equity average 4.5 bp ([1], 2020); thematic or small 10–25 bp [unverified] | avoid the first 15 minutes; the close auction also runs wide for ETFs | large ETF, A$10k ticket: about 11 bp |
| US ETF (IBKR tiered) | max(US$0.35, US$0.0035 a share) + about US$0.0002 clearing + exchange fees; sells add 0.2 bp SEC fee | SPY/IVV class 0.5 bp; other liquid 1–3 bp [unverified] | FX 0.2 bp with US$2 minimum, so convert in blocks of A$20k or more (about 1.5 bp or less); US-domiciled ETFs carry W-8BEN and estate-tax issues outside this review | US$5k ticket: about 1–3 bp + FX |
| CME micro (MES) | US$0.25 + 0.35 + 0.01 = US$0.61 a side | half a tick = US$0.625 | 4 rolls a year, each about 2 × 0.61 + about 0.25 spread = about US$1.5 | about US$1.24 a side, or about 0.35–0.4 bp of roughly US$33k notional (index level assumed, not verified); rolls about 1.8 bp a year |

- **Tiered pricing on ASX:** minimum A$5.50 including GST plus about 0.45 bp of exchange and clearing fees. It saves about A$1 on tickets under A$6k and costs slightly more above A$7.5k. Use tiered only if the median ticket is under A$6k.
- **Market impact:** set to zero for orders under 1% of average daily volume and under A$50k. This is inferred from #20, which measures institutional trades. Enforce a rule that orders stay under 1% of 20-day average volume.
- **Micro futures granularity:** one MES is about US$33k notional (index level assumed), which is too coarse for small accounts. A futures phase needs enough capital that one contract is at most 10% of an instrument's target position*.
- **Backtest setting:** use the table plus one tick of adverse slippage, then run the twice-cost stress in Gate 1.

## 5. Decisions for the spec

1. **Paper trading is 60 trading days and 40 orders, pass/fail on reconciliation only.** No performance conclusion is drawn from it.
2. **Live pilot is 3 months at 10–25% size**, then 50% for 3 months, then 100%. Scaling depends on tracking (correlation at least 0.95 with replay) and realised cost at most 1.5 times the model.
3. **Evidence of edge comes only from Gate 1.** Require at least 15 years of data, net t-statistic at least 3.0, deflated Sharpe at least 0.95, PBO at most 0.25, a parameter plateau, survival at twice costs, and a logged trial count capped at 50.
4. **One global parameter set across all instruments.** Pooling is the only way 7–20 instruments yield usable statistics.
5. **Size on a haircut Sharpe:** the lower of half the backtest Sharpe and 0.5. Target volatility is 10%, capped at 12% for 3 years. Gross leverage is at most 1.0 times in the ASX phase.
6. **Scale positions by volatility for risk control,** and budget zero Sharpe uplift from it.
7. **No per-position stop-losses.** Use the portfolio ladder at −15%, −20% and −25%, with the bootstrap 99th-percentile drawdown as the kill line.
8. **Judge live trading on drawdown percentile, realised volatility, tracking and costs.** Make no Sharpe comparison before year 3.
9. **ASX cost function is max(A$6.60, 0.088%) plus half-spread by liquidity bucket.** Minimum ticket is A$2,000 hard and A$7,500 preferred. Use a ±10% no-trade buffer and keep annual cost at or below 1.0% of capital.
10. **Execution timing:** trade ASX ETFs in continuous trading, not in the first 15 minutes, with marketable limit orders. Auction execution must be validated live in the pilot because paper cannot simulate it.
11. **US ETF phase:** tiered pricing, block FX conversions of at least A$20k, cost about 1–3 bp one-way.
12. **CME micro phase:** model US$0.61 a side plus half a tick, and about 1.8 bp a year for rolls. Defer until one contract is at most 10% of an instrument's target position.

**Open items:**
- Read the two ASX SR15 reports for ETF open and close spread numbers.
- Pull current per-ticker spreads from the ASX monthly investment products report.
- Read Harvey–Liu and the DSR and PBO papers in full to confirm exact figures.
- Confirm the Australian order-routing and payment-for-order-flow position.

None of these is likely to change a decision above; they would refine the half-spread inputs in section 4.