# Trend following literature review: decisions for a small long-only ETF account

Date: 2026-11-13. Scope tightened per your instruction to the 15 most decision-relevant papers.

## 0. Access caveats

- **Fetching:** WebFetch could not resolve any host in this session, so I fetched pages with `curl` through the session proxy and converted the PDFs locally.
- **Blocked hosts (403):** papers.ssrn.com, alphaarchitect.com, sciencedirect.com, onlinelibrary.wiley.com, pm-research.com, cmegroup.com, core.ac.uk, people.duke.edu, mebfaber.com, city.ac.uk and ibkr.com. These need allowing in the session's network settings for a fuller pass.
- **What was not read in full:** Faber (2007), Huang et al. (2020), Kim-Tse-Wald (2016), Goulding-Harvey-Mazzoleni (2023), Clare et al. (2016) and Zarattini et al. (2025) were read only as abstracts or third-party summaries.
- **Exhibit gaps:** the exhibits in "A Century of Evidence" are images, so I could not extract its headline return, Sharpe or fee figures. I cite only its text.
- **Not covered:** Baltas & Kosowski, Hutchinson & O'Brien, Greyserman & Kaminski, Levine & Pedersen (abstract only), Winton research, peer-reviewed Australian trend studies and primary crypto papers.

Tags: **[2+]** means two or more independent studies agree; **[1]** means one study (summaries of the same paper count as one); **[unverified]** means secondary only or not checked.

## 1. Annotated bibliography

| # | Paper | Read as | Data | Key finding, with quote | Tag |
|---|---|---|---|---|---|
| 1 | Lempérière, Deremble, Seager, Potters, Bouchaud (2014), "Two centuries of trend following". [arXiv 1404.3274](https://arxiv.org/abs/1404.3274) | Full PDF | Futures 1960+ (7 commodities, 7 bonds, 7 indices, 6 FX); spot back to 1800 | Sharpe is flat across 2–10 month horizons and decays beyond: 0.80 / 0.83 / 0.78 / 0.80 / 0.76 / 0.65 / 0.57 at n = 2 / 3 / 5 / 7 / 10 / 15 / 20 months. Futures pool Sharpe is 0.8 (t = 5.9; 5.0 after removing long bias). Since 1800 Sharpe is 0.72. "Sharpe ratio and t-stat are only weakly dependent on n." Trend and long-only are "only +15% correlated." Signals saturate: "strong signals tend to flatten." | [2+] with #2, #3 |
| 2 | Hurst, Ooi, Pedersen (2017), "A Century of Evidence on Trend-Following Investing", JPM. [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/AQR-JPM-Fall-2017.pdf) | Full text; exhibits are images | 67 markets, 1880–2016 | Equal blend of 1, 3 and 12-month signals, each position vol-sized, portfolio at 10% ex-ante vol. "Trend-following at each of these horizons has delivered positive returns in each decade." Lagging the signal one month hurts "especially for the shorter-term signals." Drawdowns: "losing up to 25%, over extended time periods." | [2+] on qualitative claims; return and Sharpe figures [unverified] |
| 3 | Hurst, Ooi, Pedersen (2013), "Demystifying Managed Futures", JOIM. [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Demystifying-Managed-Futures.pdf) | Full PDF | 58 futures and forwards, 1985–2012 | Average single-asset Sharpe is "0.29 for the 1-month strategy, 0.36 for the 3-month strategy, and 0.38 for the 12-month strategy." Diversified gross Sharpe is 1.26 / 1.43 / 1.52 by horizon and 1.79 blended. Costs are "1–4% per year for a sophisticated manager"; after 2-and-20 fees and costs, Sharpe "would historically have been near 1." Daily and weekly rebalancing "perform similarly, while the performance trails off with monthly and quarterly." | [2+] |
| 4 | Moskowitz, Ooi, Pedersen (2012), "Time series momentum", JFE. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250), [AQR page](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum) | Abstract plus authors' summary | 58 instruments, 25+ years | "Persistence in returns for one to 12 months that partially reverses over longer horizons." | [2+] on existence; contested by #6, #7 |
| 5 | Babu, Levine, Ooi, Pedersen, Stamelos (2020), "Trends Everywhere", JOIM. [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/AQR-Trends-Everywhere_JOIM.pdf?sc_lang=en) | Full PDF | 58 traditional assets plus alternatives and equity factors, 1985–2017 | 12-month gross Sharpe is 1.17 (traditional), 1.34 (alternative), 0.95 (factors) and 1.60 combined. "Portfolio Sharpe ratios are far above the median individual Sharpe ratios." | [2+] on breadth, with #3, #12 |
| 6 | Kim, Tse, Wald (2016), "Time series momentum and volatility scaling", JFM. [EconPapers](https://econpapers.repec.org/RePEc:eee:finmar:v:30:y:2016:i:c:p:103-124), [Quantpedia](https://quantpedia.com/deconstructing-the-time-series-momentum-strategy/) | Abstract plus working-paper quotes | 55 futures, 1985–2013 | "Without scaling by volatility, time series momentum and a buy-and-hold strategy offer similar cumulative returns." Monthly alpha is 1.27% scaled against 0.41% unscaled (working-paper figure). Trend beat buy-and-hold on only 29 of 55 contracts unscaled. | [2+] with #7, #8 |
| 7 | Huang, Li, Wang, Zhou (2020), "Time series momentum: Is it there?", JFE. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:135:y:2020:i:3:p:774-794) | Abstract only | Same asset set as #4 | "Asset-by-asset time series regressions reveal little evidence of TSM"; the strategy is profitable "but its performance is virtually the same as that of a similar strategy that is based on historical sample mean." | [1]; disagrees with #1, #5 |
| 8 | Harvey, Hoyle, Korgaonkar, Rattray, Sargaison, Van Hemert (2018), "The Impact of Volatility Targeting". [Man](https://www.man.com/insights/the-impact-of-volatility-targeting) | Authors' summary page | 60+ assets, daily from 1926 | Vol targeting improves Sharpe for "risk assets (equities and credit)"; "for bonds, currencies, and commodities the impact on the Sharpe ratio is negligible." Left tails are "less severe." | [2+] with Moreira-Muir (NBER w22208; abstract page fetched, not analysed) |
| 9 | Babu, Hoffman, Levine, Ooi, Schroeder, Stamelos (2020), "You Can't Always Trend When You Want", JPM. [AQR PDF](https://www.aqr.com/-/media/AQR/Documents/Journal-Articles/JPM-You-Cant-Always-Trend-When-You-Want.pdf?sc_lang=en) | Full PDF | 1880–2018 backtest plus SG Trend Index | SG Trend "realized a -19.7% return" from April 2015 to end 2018; Sharpe "0.05" for 2010–18 against "0.28" since 2000. Attributed to "fewer large moves across markets," not lost efficacy. | [2+] on the weak decade (with #1, #10); cause is contested |
| 10 | Garg, Goulding, Harvey, Mazzoleni: "Momentum Turning Points" (JFE 2023) and "Breaking Bad Trends" (FAJ). [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:149:y:2023:i:3:p:378-406), [Quantpedia](https://quantpedia.com/trend-breaks-in-trend-following-strategies/), [CXO](https://www.cxoadvisory.com/technical-trading/mitigating-impact-of-price-turning-points-on-trend-following/) | JFE abstract plus paper excerpts | 55 series, 1971–2019 | A static 12-month rule returned about 7.5% a year over 30 years but 1.8% in the last decade (at 10% vol); the dynamic version returned 4.3%. "Faster trend signals… rather than solving the problem, increase the tendency of placing bad bets." "Intermediate-speed momentum portfolios, formed by blending slow and fast momentum strategies" produce positive alpha. | [1] for the dynamic rule; [2+] for blending and decay |
| 11 | Dao, Nguyen, Deremble, Lempérière, Bouchaud, Potters (2016), "Tail protection for long investors: Trend convexity at work". [arXiv 1607.02410](https://arxiv.org/abs/1607.02410) | Full PDF | SG CTA Index replication | CTA index is replicated at over 80% correlation with one filter "of the order of 6 months." "It is wrong to expect a 6 to 9 months trending system rebalanced every week to hedge against a market crash that lasts a few days." Trend is "a much cheaper way to hedge long-only exposures" than options. | [2+] with #14 |
| 12 | Carver, three posts on qoppac.blogspot.com: [small accounts (2016)](https://qoppac.blogspot.com/2016/03/diversification-and-small-account-size.html), [speed (2020)](https://qoppac.blogspot.com/2020/04/how-fast-should-we-trade.html), [allocation (2022)](https://qoppac.blogspot.com/2022/11/optimal-trend-following-allocation.html) | Full posts | 37 futures; S&P 500 and US 10-year 1982–2022 | Diversification multiplier "asymptot[es] at around 2.75"; one instrument per asset class "roughly doubles" it, and "the next 20 or so instruments have a marginal effect." Per-instrument Sharpe is about 0.35 time-weighted. The slowest crossover (64/256) has Sharpe of about 0.28 at 1.1 trades a year; 2/8 has 0.07; momentum does "consistently well between MAC8 and MAC64." "Smaller traders have linear trading costs." On two assets, Sharpe is 0.31 (fast), 0.38 (long-only) and 0.49 (slow). | [2+] on breadth and slow speed; practitioner, not peer-reviewed |
| 13 | Clare, Seaton, Smith, Thomas (2016), "The trend is our friend", JBEF. [IDEAS](https://ideas.repec.org/p/yor/yorken/12-25.html), [CXO](https://www.cxoadvisory.com/?p=21860) | Abstract plus summary | 5 asset classes, 95 indices, 1993–2015, long-or-cash | 10-month average on 5 class indices: return 6.6% to 8.0%, Sharpe 0.33 to 0.79, max drawdown −46.6% to −11.6%, all gross. Trend is "a superior method of asset allocation than risk parity." Relative momentum alone gave "no protection" (−43.8% drawdown). | [2+] directionally with Faber (#15); figures [1] |
| 14 | Man Group 2025: ["Why patience matters"](https://www.man.com/insights/why-patience-matters-during-market-stress), ["Is this time different?"](https://www.man.com/insights/is-this-time-different), ["Deep dive"](https://www.man.com/insights/deep-dive-trend-following) | Full pages | SG Trend 2000–2025; 20 proxy CTAs | Trend lost about 17% early in the 2007 episode and "endured another 20% drawdown" on the way to dot-com gains. Fast trend (two-day peak weight) shows "declining efficacy over time." Costs assumed: "2% for fast and 1% for slow." After 12-month losses over 10%, the next 12 months averaged +9.8%. | [2+] on 2024–25 drawdown |
| 15 | Long-only timing and single stocks, secondary only: Faber (2007); Zakamulin (2015), [CXO](https://www.cxoadvisory.com/technical-trading/market-timing-with-moving-averages-over-the-very-long-run); [CXO trend guide](https://www.cxoadvisory.com/guides/trend-momentum/); Lim, Wang, Yao (2018), [IDEAS abstract](https://ideas.repec.org/a/eee/jbfina/v97y2018icp283-296.html); Zarattini, Pagani, Wilcox (2025), [CXO](https://www.cxoadvisory.com/momentum-investing/all-time-high-trend-following) | Summaries and abstracts | US equity 1860–2009; ETFs; US stocks 1927–2017 and 1991–2024 | Zakamulin: timing rules had "higher Sharpe ratios than buy-and-hold despite lower mean returns"; over 5–10 year horizons they are "about equally likely to outperform and underperform"; optimal lookback is about 7 months (momentum) or 10 months (moving average). CXO: buy-and-hold beat six moving-average rules on net return for 15 of 21 ETFs. Zarattini: 15.0% gross against 11.2% for the market; "net CAGR depends on portfolio size." | Drawdown cut, no return gain: [2+]. Stock result: [1], gross |

Recent performance (SG Trend Index):
- **2022:** +27.3%, a record. [2+] ([Alpha Week](https://alpha-week.com/2022-cta-index-performance-review), [The Full FX](https://thefullfx.com/year-end-drop-fails-to-dampen-stellar-2022-for-trend-followers/))
- **2024:** +2.6%. [1] ([Alternatives Watch](https://www.alternativeswatch.com/2025/06/02/trend-following-hedge-funds-endure-more-pain-societe-generale-indices/))
- **May 2024 to May 2025:** −20.4% peak to trough, the second-largest drawdown since 2000. Rolling 12 months to April 2025 was about −18.6%. [2+] ([Cambridge Associates](https://www.cambridgeassociates.com/insight/does-trend-followings-recent-struggle-signal-that-the-strategy-is-structurally-broken/), [Man](https://www.man.com/insights/is-this-time-different))
- **2023:** calendar-year figure not found. [unverified]

## 2. Synthesis

### Robust findings

1. **Trend exists at 2–12 month horizons and lookback choice barely matters there.** Sharpe is flat from 2 to 10 months and falls beyond 15 (#1). The 1, 3 and 12-month signals are each positive every decade (#2). Zakamulin's out-of-sample optimum is 7–10 months (#15). [2+]
2. **Very fast trend has decayed and costs more.** Carver's 2/8 crossover has Sharpe 0.07 (#12), Man shows fast trend declining (#14), and delays hurt short signals most (#2, #3). [2+]
3. **Blending speeds helps modestly through diversification.** Blended gross Sharpe is 1.79 against 1.26–1.52 for single horizons (#3), and intermediate blends earn alpha (#10). The gain is small next to breadth. [2+]
4. **Breadth is the main Sharpe driver, with fast-diminishing returns.** Single-asset trend Sharpe is about 0.3–0.4 (#3, #12). Diversified gross Sharpe of 1.2–1.8 (#3, #5) comes from 50+ low-correlation markets. One instrument per asset class captures most of the benefit (#12). [2+]
5. **Realised net Sharpe is far below paper Sharpe.** The paper figure is 1.8 gross against about 1.0 after fees and costs (#3). SG Trend's Sharpe was 0.28 over 2000–2018 (#9). A diversified time-series momentum benchmark earned 0.62 net with a −23.4% drawdown over 1994–2015 ([CXO summary of Elaut & Erdős](https://www.cxoadvisory.com/momentum-investing/benchmarking-trend-following-managed-futures/)), and that figure is still net of fund fees. For a broad futures programme, plan on 0.3–0.7 net Sharpe and 20–25% drawdowns at 10% vol. [2+]
6. **Crisis protection works for slow bear markets, not sudden shocks.** Dao et al. (#11) and Man (#14) agree, and Man shows trend often loses first. [2+]
7. **Long-only trend filters cut drawdown but do not reliably raise return.** Clare shows −46.6% to −11.6% (#13); Zakamulin shows higher Sharpe with lower mean return (#15); CXO's ETF tests show buy-and-hold winning on net return for most assets. Treat the filter as risk control paid for with whipsaw. [2+]
8. **Volatility scaling is a separate, real effect.** It improves Sharpe mainly for equities and credit and thins left tails (#8), and it explains much of the headline trend alpha (#6). [2+]

### Contested findings

- **Is trend a real predictability effect or disguised long exposure plus vol scaling?** Kim-Tse-Wald and Huang et al. say largely the latter. Babu et al. respond by controlling for vol-scaled long-only and asset fixed effects, and Lempérière finds t = 5.0 after removing the long bias. For a long-only account this dispute matters little: you keep the risk premium either way, and the filter's job is drawdown control.
- **Why was 2010–2019 weak?** AQR blames smaller market moves (#9); Garg et al. blame more frequent turning points (#10); Man concedes fast-signal decay (#14). All parties sell trend products. The 2024–25 drawdown falls after every one of these samples.
- **Dynamic speed switching.** It doubles last-decade returns in the authors' own test (#10), but that is one research group with fitted weights. [1]
- **Trend on single stocks.** Lim et al. report "strong time-series momentum effects in individual stocks," and Zarattini shows a gross edge. But profits are concentrated in a small minority of trades and the net result depends on account size. [1], unverified for small accounts
- **Australian evidence.** I found only practitioner pieces, nothing peer-reviewed. [unverified]
- **Crypto.** One secondary headline (18% net return, long-only ensemble, 25% vol target), with the paper unread. [unverified]

## 3. Decisions for the spec

### Adopt

**D1. Role of trend.** In the long-only ETF account, trend is a drawdown-control overlay, not a return source.
- Success test: a materially lower maximum drawdown than buy-and-hold at similar or modestly lower return.
- Do not put "beats buy-and-hold on return" in the spec.
- Evidence: robust finding 7; #6, #7.

**D2. Signal: blend of three slow lookbacks, equal weight.**
- Signal for each ETF is the average of three indicators: total-return price above its 4-, 8- and 12-month moving average (roughly 84, 168 and 252 trading days).
- Target exposure is 0, ⅓, ⅔ or 1 of the base weight. Graded exposure stands in for the signal saturation found in #1 and halves the whipsaw of an all-or-nothing rule.
- Equal weights, not optimised, because the Sharpe difference across 2–10 months is within noise (#1).
- Nothing faster than about 3 months; nothing slower than 12 (Sharpe falls at 15–20 months in #1).

**D3. Evaluation and trade frequency.**
- Futures: evaluate signals weekly. Daily and weekly rebalancing perform alike, and monthly trails off (#3).
- ETF account: evaluate monthly. The 4–12 month signals are slow enough that the loss should be small, though #3 measured it only for futures, and fixed brokerage dominates at this size (#12).
- Stagger the two holders' accounts or use two mid-month dates to reduce timing luck. This is my inference, not something the sources tested.

**D4. Buffer.** Trade only when target exposure and current exposure differ by at least one full step (⅓ of that ETF's base weight) and the trade is at least about A$1,000.
- At roughly A$5–6 minimum commission, A$1,000 keeps the commission near 0.5%. The IBKR ASX fee schedule was unreachable, so this is unverified; check it before fixing the number.
- Rationale: small traders face linear costs (#12).

**D5. Annual cost budget.**
- Compute expected annual cost as holding cost plus (cost per trade × trades per year), expressed as a fraction of the ETF's volatility (#12).
- Reject any ETF or rule where this exceeds about 0.10 Sharpe units. With single-asset trend Sharpe near 0.3–0.4, that already consumes a third of it. The threshold is my choice, derived from #3 and #12.
- At A$5k the cost budget supports only 3–4 holdings with at most about 4 round trips a year each.

**D6. Breadth: one ETF per distinct asset class before any second ETF in a class.**
- Minimum 4 sleeves: Australian equity, global equity, bonds, gold or commodities.
- Target 6–8 by adding listed property, a second bond duration and emerging or small-cap equity.
- Cap at about 10; beyond that the gain is marginal (#12, #5).
- Expect a diversification gain of about 1.3–1.5× on a long-only ETF set, not the 2–2.75× of futures, because equity sleeves are highly correlated. That lower figure is my inference; Carver notes only that the benefit is lower in a narrower universe.

**D7. Sizing.**
- Base weights are inverse-volatility (63-day or exponentially weighted, 36-day half-life), recomputed monthly.
- Cap total exposure at 100%, with no leverage. Unused weight goes to a cash or short-bond ETF.
- Do not vol-target the long-only account upward. A downward-only cap is acceptable: scale down if forecast portfolio vol exceeds about 12%.
- Evidence: #8 (benefit concentrated in equities, tail thinning), #6.

**D8. Planning numbers for the long-only ETF sleeve.**
- Sharpe 0.4–0.6, against 0.3–0.4 for buy-and-hold multi-asset.
- Maximum drawdown 15–20%, against 40–45% (stress case from #13 and #15).
- Expect multi-year stretches lagging buy-and-hold, with roughly even odds of lagging over any 5–10 year window (#15).
- Pre-commit a review trigger, not a kill switch. Only review the rule if drawdown exceeds 25% or it lags by more than 10 years.

**D9. Futures phase gate (later, secondary).** Go to futures only when capital supports at least 6–8 markets across four asset classes with meaningful minimum position granularity.
- Carver's ideal is at least 4 contracts at maximum forecast; micro contracts help (#12).
- Then use three to four blended speeds (crossovers of 16/64, 32/128 and 64/256 days, optionally 8/32 for cheap markets only).
- Long-short, per-instrument vol sizing, portfolio vol target of 10–12%, weekly or daily evaluation with a position buffer.
- Plan on 0.3–0.5 net Sharpe at 6–8 markets and at most about 0.7 at 30+ (#3, #9, #12, and the 0.62 benchmark).
- Expect a 25% drawdown at 10% vol (#2, SG Trend 2024–25).
- On a stock-and-bond-only set, slow trend beat fast (0.49 against 0.31), and long-only was 0.38 before removing secular tailwinds (#12).

**D10. Crisis expectation.** Document in the spec that the overlay will not protect against gaps or crashes lasting days (#11) and commonly loses in the first leg of a crisis (#14). Tail protection for short shocks, if wanted, must come from base allocation (bonds, cash), not the trend rule.

### Reject

- **R1. Fast trend (lookbacks under about 2 months, daily breakouts) in the ETF account.** Decayed, and the costliest to trade (#12, #14, #2).
- **R2. Parameter optimisation of lookbacks or blend weights.** Differences are within noise (#1) and fitted weights are a known snooping risk.
- **R3. Dynamic speed switching on turning points for v1.** Single research group, fitted weights (#10). Revisit only as a futures-phase experiment.
- **R4. Relative momentum ranking without an absolute trend filter.** Gave no drawdown protection, −43.8% (#13).
- **R5. Single-stock trend as a core strategy at A$5k–100k.** The evidence is gross, relies on rare big winners across hundreds of names, and its net result depends on account size (#15).
- **R6. Backtest Sharpe above 1 as a planning input.** Paper figures of 1.2–1.8 are gross, 1985–2012, across 58+ markets (#3, #5). Realised index Sharpe was 0.28 (#9).
- **R7. Crypto trend sleeve for now.** No primary source read. Needs its own review.
- **R8. Leverage to hit a vol target in the long-only account.** Much of the headline "trend alpha" in the literature came from leveraged vol scaling (#6).

### Open items before coding

1. Confirm IBKR ASX commission and typical ETF spreads to finalise D4 and D5.
2. Read Faber (2007) and Huang et al. (2020) in full once SSRN or ScienceDirect is reachable.
3. Extract the Hurst et al. (2017) Exhibit 1 and 8 figures.
4. Search for a peer-reviewed Australian trend study.

I judged that further reading would not change D1–D10. The remaining uncertainty is in costs (open item 1), not signal design.

Local text copies of everything fetched are in `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/dl/`.