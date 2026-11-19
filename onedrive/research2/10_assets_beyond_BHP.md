# Beyond BHP: which assets for the A$5k live account and the paper universe

**Short answer:** yes, there are better choices than BHP for a one-asset account. The evidence favours switching a broad index ETF (VAS, or a global fund such as VGS) over any single stock. For the full strategy, the six-stock universe is too narrow and too iron-ore-heavy.

How to read the evidence: figures with a link come from web searches run on 2026-11-13, mostly secondary sources. Anything marked **[unverified]** is from memory or a single weak source, and should be checked against issuer PDS or factsheets before it goes into the spec. No backtests were run for this report.

## 1. Small-account mode (one asset or cash, ~A$5k)

### What the trend-filter evidence says

- **Trend filters mainly cut drawdowns; they do not reliably add return.** Faber's 10-month SMA rule, tested on US stocks since 1900, reduced the 1930s drawdown from about 84% to 42% per a secondary summary ([the7circles](https://the7circles.uk/?p=35413), [Quantpedia](https://quantpedia.com/strategies/asset-class-trend-following)).
- **The return edge is overstated.** Zakamulin's out-of-sample test (1930–2012) concludes the reported performance is "highly overstated" by data-mining ([Journal of Asset Management](https://link.springer.com/article/10.1057/jam.2014.25), [SSRN](https://papers.ssrn.com/abstract=2677212)). A related study finds no statistically significant outperformance in the second half of its sample.
- **The same holds in Australia.** The Chartist's 200-day test on STW finds the benefit "is really only during very bad periods" and the rule can "seriously dilute the long-term return" otherwise ([The Chartist](https://thechartist.com.au/?p=58921)). I found no rigorous published ASX backtest that includes costs and franking.
- **Dual momentum (Antonacci GEM) is fragile.** Newfound's analysis finds all 1–18 month lookbacks have similar expected results and the 12-month version's edge is "most likely random luck"; lookback choice alone can swing results by hundreds of basis points a year ([Advisor Perspectives](https://files.advisorperspectives.com/articles/2019/05/06/global-equity-momentum-a-craftsmans-perspective)). One post-publication test (2014 to March 2023) shows 6.3% a year versus 10.8% for SPY buy-and-hold ([Price Action Lab](https://priceactionlab.com/Blog/?p=68274), single source).
- **These studies are on diversified indices, not single stocks.** A single stock adds gap risk that an end-of-day trend rule cannot dodge. About 4% of US stocks produced all net wealth creation since 1926, and only 42.6% beat T-bills over their lifetime ([Bessembinder](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:3:p:440-457), [summary](https://blogs.wpcarey.asu.edu/20180917-do-stocks-outperform-treasury-bills)).

### Candidate comparison

| Candidate | Fee p.a. | Liquidity / spread | Diversification | Franking | Currency | Verdict for one-asset mode |
|---|---|---|---|---|---|---|
| **VAS** (ASX 300) | 0.07% | Best: ~0.02% spread, ~A$86m/day | ~300 stocks, but over half the index is financials and materials | Yes | AUD | Strong default |
| **A200** | 0.04% | ~0.02–0.03% | ASX 200 | Yes | AUD | Equivalent to VAS; fee saving is ~A$1.50/yr on A$5k |
| **IOZ / STW** | 0.05% | 0.03–0.04% | ASX 200 | Yes | AUD | Equivalent; STW's history from 2001 makes it the best backtest proxy |
| **VGS** (developed world ex-Australia) | 0.18% | Good, but wider in the Australian morning | ~1,300 stocks [unverified], US-heavy | None | Unhedged | Best single-asset diversifier |
| **IWLD / BGBL** | ~0.09% / ~0.08% [unverified] | Thinner than VGS [unverified] | As VGS | None | Unhedged | Cheaper alternates |
| **IVV** (S&P 500) | ~0.04% [unverified] | Very good | One country | None | Unhedged | Fine as the "global" leg; risks chasing recent US outperformance |
| **NDQ** (Nasdaq 100) | ~0.48% [unverified] | Good | Concentrated tech | None | Unhedged | Not for live; paper only |
| **VTS** | 0.03% | Thinner [unverified] | Broad US | None | Unhedged | Skip: US-domiciled, extra tax paperwork [unverified]; IVV is cleaner |
| **PMGOLD / GOLD** | 0.15% / 0.40% | Good | Low correlation to equities | No income | Unhedged | Not as the sole asset; candidate third leg (PMGOLD is cheaper) |
| **BHP** | nil | Excellent | One company, iron ore and copper | Full | AUD, USD earnings | Not recommended as sole asset |
| **CBA** | nil | Excellent | One bank | Full | AUD | Not recommended, same reason |
| **Managed-futures / trend ETF on ASX** | n/a | n/a | n/a | n/a | n/a | None found |

Fees and spreads are from [Stockspot](https://blog.stockspot.com.au/best-australian-share-etfs/), [ReviewETF](https://www.reviewetf.com.au/blog/vas-vs-a200-vs-ioz-which-australian-shares-etf-is-best), [Fool (VTS, VGS)](https://www.fool.com.au/2026/01/21/asx-etfs-with-big-gains-and-low-fees/) and [Finder (gold)](https://www.finder.com.au/share-trading/exchange-traded-funds/best-etfs). Index concentration is from [StockWireX](https://stockwirex.com/analysis/asx-200-concentration-risk-portfolio/).

- **Managed futures:** two searches found only US-listed products (DBMF, KMLM, CTA, AHLT) and unlisted Australian funds from Aspect, Man AHL and Winton ([Morningstar](https://www.morningstar.com.au/investments/security/fund/17745/overview)). Absence is not proven; check the ASX product list.
- **Recent returns, not a forecast:** A$10k over five years to May 2026 became about A$22.9k in IVV, A$19.8k in VGS and A$16.2k in VAS ([ReviewETF](https://www.reviewetf.com.au/blog/what-10000-invested-5-years-ago-is-worth-today-every-asx-etf-ranked)). PMGOLD's ten-year cumulative return was about 320% ([Pearler](https://pearler.com/explore/invest/au-shares/compare/VGS-vs-PMGOLD/performance)). These are trailing figures after a very strong US and gold run.
- **Gold and trend:** gold returned 12.3% a year above its 200-day average versus 1.9% below, since 1975 ([SentimenTrader](https://sentimentrader.com/blog/a-persistent-uptrend-in-gold-suggests-more-upside)). A critic notes such rules lost on two-thirds of trades ([Irrelevant Investor](https://theirrelevantinvestor.com/?p=7344)).
- **BHP, RIO and FMG move together:** all three are "inextricably tied" to the iron ore price ([Firstlinks](https://www.firstlinks.com.au/article/bhp-v-rio-v-fortescue--it-s-all-about-the-iron-ore-price)).

### Two issues that matter more than the ticker

**1. The opening auction is the wrong place to trade ETFs.**
- Issuers and brokers advise avoiding the first 10–15 minutes, because market makers cannot price the fund until the underlying stocks trade ([Betashares](https://betashares.com.au/education/how-do-etf-bid-and-offer-spreads-work), [Bell Potter](https://bellpotter.com.au/?p=5503), [Russell](https://russellinvestments.com/au/blog/etf-market-making-how-and-when-to-trade-etfs-efficiently)).
- ASX's November 2025 report on the move to a simultaneous open says spreads are elevated in the first two minutes, then settle lower than before ([ASX](https://www.asx.com.au/content/dam/asx/markets/trade-our-cash-market/equity-markets-working-groups/asx-sr15-post-implementation-report-november-2025.pdf)).
- International ETFs have wider spreads in the Australian morning because their underlying markets are closed.
- Opening-auction limits are fine for BHP or CBA. ETF orders need a different rule (see spec list).

**2. Costs and tax at A$5k.**
- A$6.60 is 0.13% per trade on A$5k. The 0.088% rate only applies above A$7,500 per trade. Four switches a year costs about A$53 (around 1.1%), which is tolerable; weekly trading is not.
- A rotation from one ETF to another costs two commissions.
- Positions sold within 12 months get no CGT discount [unverified in this research; ATO rule from memory].
- The 45-day franking rule does not bind: individuals with A$5,000 or less in franking credits a year are exempt ([ATO](https://www.ato.gov.au/forms-and-instructions/you-and-your-shares-2021/when-you-are-not-entitled-to-claim-a-franking-tax-offset)).
- Check whether IBKR pays interest on small AUD balances; I believe it does not below a threshold [unverified]. If "cash" earns nothing, a cash ETF (AAA or BILL) is worth the A$13.20 round trip only when the out-of-market spell is likely to exceed about two months.
- IBKR's public schedule shows 0.08% with a A$6 minimum on fixed pricing, consistent with your GST-inclusive figure, and A$5 on tiered ([IBKR](https://www.interactivebrokers.ie/en/pricing/commissions-bonds-asia-pacific.php)).

### Single asset or a 2–3 asset rotation?

| Setup | Trades/yr (estimate, not backtested) | For | Against |
|---|---|---|---|
| VAS or cash | 2–6 | Simplest, cheapest, franking, best liquidity | 100% home bias; banks and miners |
| VGS or cash | 2–6 | Broadest single holding | No franking; ETF pricing at the open |
| **VAS / VGS / cash** | 3–8 | Removes the home-country bet; only one extra rule | Relative-momentum edge is not robust; can rotate into the recent winner late |
| VAS / VGS / PMGOLD / cash | 4–10 | Adds a genuinely different asset when equities are below trend | More parameters; gold whipsaws; unproven here |
| BHP or cash | 4–10 | Franking | Single-stock gap risk; noisier signals |

**Recommendation:** run VAS / VGS / cash live, and paper-trade the gold variant alongside it.
- **Why not single-asset:** rotation's main benefit is not being permanently tied to one country's market. Treat any momentum return edge as zero.
- **How it works:** hold whichever of VAS or VGS has the higher blended 6/9/12-month total return, provided its own trend score and the regime filter pass. Otherwise hold cash.
- **Controls:** evaluate monthly, not daily, with a switching buffer (see spec list).
- **Fallback:** if you want the absolute simplest live system, VAS or cash is fine. It is still better than BHP or cash.

## 2. Full-strategy universe

### Is BHP/RIO/FMG/CBA/CSL/WDS right?

No. It is six names but roughly four independent bets: iron ore (three times), one bank, healthcare and energy.

- **Breadth is where trend following gets its edge.** The core studies use 58 futures across four asset classes ([Moskowitz, Ooi and Pedersen, summary](https://themenonlab.blog/blog/time-series-momentum-hedge-fund-strategy-explained)) and 67 markets over a century ([AQR](https://www.TrendFollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf)). Single-market trend Sharpe ratios are low; the portfolio result comes from combining many weakly correlated markets [the per-market magnitude is unverified].
- **On stocks, a few outliers carry the result.** The 2025 revisit of Wilcox and Crittenden finds under 7% of trades generate the majority of profits, on a Russell 3000 universe ([Concretum](https://concretumgroup.com/does-trend-following-still-work-on-stocks/)). Six mega-caps will rarely contain those outliers, so the stock sleeve behaves like timed ASX exposure.
- **Hand-picked names carry hindsight bias.** Backtesting today's survivors overstates results. Use a rule to define the universe.

### Suggested paper universe (about 20 instruments)

| Sleeve | Tickers | Role |
|---|---|---|
| Australian equity | VAS (or A200) | Default holding and regime reference |
| Global equity | VGS (or BGBL); IVV as alternate | Biggest diversifier versus ASX |
| Emerging markets | VGE or IEM [liquidity unverified] | Different cycle |
| Growth tilt | NDQ | Paper only |
| Gold | PMGOLD | Lowest equity correlation |
| Bonds | VAF or IAF; VGB | Defensive trend leg |
| Cash | AAA or BILL | Parking |
| Listed property | VAP | Rate-sensitive sleeve |
| Stocks | BHP, CBA, CSL, WDS, plus about six of WES, MQG, TLS, GMG, WOW or COL, TCL, QBE, ALL, NST, XRO | One or two per sector |

- **Drop FMG.** It is a pure-play iron ore producer, so it largely duplicates BHP and RIO.
- **Keep one of BHP or RIO as a tradeable position** (BHP, for liquidity and copper). RIO can stay as a data series for testing the commodity-confirmation rule.
- **Keep CSL.** It is the only healthcare exposure. Dropping it because it has been weak is hindsight; the trend rules exist to keep you out of it.
- **Skip ASX sector ETFs** (QFN, QRE, MVB, MVR). They are thinner [unverified], and direct large-caps plus the caps above do the same job.
- **Skip futures-based commodity ETFs** such as OOO. Roll costs distort trend signals [unverified].

### Practicality

- **Data:** end-of-day data from IBKR or Yahoo covers all of these. Use dividend-adjusted closes for momentum signals. ETF histories are short (VAS from 2009, VGS from 2014, A200 from 2018) [unverified], so backtest on index proxies: the ASX 200 accumulation index, STW from 2001, MSCI World ex-Australia in AUD, and the gold price in AUD.
- **Cost floor:** at A$6.60, a A$1,000 position costs 0.66% per side. A minimum position of about A$2,500 keeps that near 0.26%, so an eight-position book needs roughly A$20–25k (my arithmetic).
- **RSI(2) dip-buying:** not viable until positions are A$5k or more, because its per-trade edge is small relative to a 0.26% round trip [edge size unverified].

## 3. Bottom line for the owner

1. **BHP is a reasonable company but a poor one-asset strategy.** With one holding, own a market, not a single company.
2. **Most sensible live setup at A$5k:** hold VAS or VGS, whichever is stronger and trending up; otherwise cash. Check monthly and expect a few trades a year.
3. **Be honest about what it buys you.** Expect smaller drawdowns in big bear markets, and probably somewhat lower returns than buy-and-hold in ordinary years, after whipsaws, lost dividends and tax. If the goal is maximum long-run wealth on A$5k, plain buy-and-hold of VAS plus VGS (or a single diversified fund such as DHHF or VDHG) is the benchmark the system must beat. Log that benchmark alongside live results.
4. **Do not send ETF orders into the opening auction.**
5. **In paper:** widen to about 20 instruments across asset classes and sectors, drop FMG, and measure whether stock-level trend adds anything over ETF-level trend.

## Spec-ready recommendations

1. **Small-account universe (live):** `VAS` (Australian equity), `VGS` (global equity), `CASH`. Remove `BHP` as a small-account option.
2. **Small-account selection rule:**
   - Evaluate on the last trading day of each month.
   - Candidate is the higher of VAS or VGS on the average of 6-, 9- and 12-month total return.
   - Hold the candidate only if its trend score is at or above your threshold and the regime filter is on. Otherwise hold cash.
   - Switch between VAS and VGS only if the challenger leads by at least 2 percentage points; this is a starting value to tune in paper.
   - Keep the chandelier stop as a daily emergency exit only.
3. **Signals for VGS:** compute the trend score on VGS's own adjusted price. Test in paper whether the regime filter should reference VAS, VGS or either.
4. **ETF execution rule:**
   - No opening-auction orders for ETFs.
   - Submit a day limit order between 10:20 and 10:30 AEST, priced at the offer (buy) or bid (sell), capped at ±0.3% of last price.
   - Cancel and retry once at 11:00.
   - For VGS, prefer after 11:00.
   - Opening-auction limits remain acceptable for ASX 20 stocks.
5. **Cash leg:** confirm IBKR's AUD interest threshold. If idle cash earns nothing, add `AAA` or `BILL` as the cash proxy, used only when the regime filter is off (expected long out-period).
6. **Trade budget:** alert if commissions exceed 1.5% of equity in a rolling 12 months (about 11 trades at A$5k).
7. **Benchmark logging:** track buy-and-hold VAS, buy-and-hold 50/50 VAS/VGS, and the old "BHP or cash" variant alongside live results.
8. **Paper universe — ETFs:** `VAS`, `VGS`, `IVV`, `NDQ`, `VGE`, `PMGOLD`, `VAF`, `VGB`, `VAP`, `AAA`.
9. **Paper universe — stocks:** keep `BHP`, `CBA`, `CSL`, `WDS`. Drop `FMG`. Move `RIO` to signal-only. Add `WES`, `MQG`, `TLS`, `GMG`, `WOW`, `TCL`, `QBE`, `NST`.
10. **Universe rule:** state it as "ASX 20 constituents, maximum two per sector, maximum one iron-ore major", so membership is not hand-picked.
11. **Portfolio constraints (full strategy):** minimum position A$2,500; maximum 25% per single stock; maximum 30% per sector; do not enable full-strategy mode below about A$20k.
12. **RSI(2) module:** gate on position size of A$5,000 or more.
13. **Paper variant B:** `VAS` / `VGS` / `PMGOLD` / cash under the same rule. Promote to live only if, over at least 12 months of paper trading plus an index-proxy backtest from 2001, it shows a lower maximum drawdown without materially more trades.
14. **Verify before finalising:** current fees for IVV, NDQ, IWLD, BGBL; liquidity for VGE, BGBL, VAP; ATO CGT discount treatment; IBKR interest tiers; whether any ASX-listed managed-futures ETF exists.