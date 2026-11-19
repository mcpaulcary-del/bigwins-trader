# TAA and factor strategies for an AUD retail ETF investor: evidence and spec decisions (13 Nov 2026)

## 0. Scope and verification limits

- **What I read directly:** 15 primary sources in full text or publisher/author abstract (marked **P**). Everything marked **S** was reached only through secondary summaries or search snippets.
- **Blocked hosts:** `papers.ssrn.com`, `alphaarchitect.com`, `blog.thinknewfound.com`, `onlinelibrary.wiley.com`, `sciencedirect.com`, `pm-research.com`, `ato.gov.au`, `vanguard.com.au`, `betashares.com.au`, `advisorperspectives.com`, `concretumgroup.com`, `mebfaber.com`, `optimalmomentum.com`. These need allowing in the session network settings.
- **Consequence:** Faber, Antonacci, Keller, McLean-Pontiff and Anderson-Bianchi-Goldberg were not read in the original. Their numbers are tagged accordingly.
- **No backtest:** Yahoo and Stooq are also blocked, so I could not run a VAS/VGS backtest. Every performance number below is from US/global literature, not Australian ETF data.
- **Not covered:** the wider 30+ scan was cut by the tightened scope. Ilmanen, Butler's Adaptive Asset Allocation, Barroso-Santa-Clara, low-vol/quality primaries, Research Affiliates and Vanguard hedging papers were not reached. Arnott's "Factorland" was seen only as a search summary.

Tag rule: **[2+]** means two independent studies or datasets agree. Two summaries of the same paper count as one source. **[1]** is one source; **[unverified]** is a snippet only.

## 1. Annotated bibliography

| # | Source | Access | Key numbers | Sample status | Tag |
|---|---|---|---|---|---|
| 1 | Faber, "A Quantitative Approach to TAA" (2007; 2013 update), SSRN 962461. Via [CXO](https://www.cxoadvisory.com/?p=1115), [Quantpedia](https://quantpedia.com/strategies/asset-class-trend-following/) | S | US stocks 1901–2012, 10-month SMA vs buy-and-hold: return 10.2% vs 9.3%, vol 12.0% vs 17.9%, Sharpe 0.55 vs 0.32, max drawdown −50% vs −83%. Five assets 1973–2012: 10.5% vs 9.9%, vol 7.0% vs 10.3%, Sharpe 0.73 vs 0.44, drawdown −9.5% vs −46%. 13 assets: Sharpe 0.94. "Three to four round-trip trades per year" for five assets. Gross, no tax. | In-sample | [1] |
| 2 | Zarattini (2025), "GTAA Updated Results… Python and IBKR". Via [CXO](https://www.cxoadvisory.com/?p=46808), Concretum snippet | S | Jan 2006–Mar 2025: CAGR 6.05%, Sharpe 0.68, max drawdown 11.7%, against 11.7% CAGR and 0.81 Sharpe originally. Tests 21 rebalance-day variants and a tranche fix. 0.1% friction. CXO notes "descriptive, no benchmark". | Post-publication | [1] |
| 3 | Antonacci, *Dual Momentum Investing* (2015). Via [CXO quotes](https://www.cxoadvisory.com/momentum-investing/a-few-notes-on-dual-momentum-investing) | S | GEM 1974–2013: "average annual return of 17.43% with a 12.64% standard deviation, a 0.87 Sharpe ratio, and a maximum drawdown of 22.7%", "almost doubling" ACWI. Gross. | In-sample | [1] |
| 4 | ReSolve/Newfound GEM critiques (2019), [Advisor Perspectives](https://api.advisorperspectives.com/articles/2019/05/06/global-equity-momentum-a-craftsmans-perspective) | S, snippet | Original specification's edge over neighbouring lookbacks is "most likely… random luck". Lucky vs unlucky specifications differ by 64 points over five years. Lookback choice moves results by hundreds of bps a year. | Robustness | [unverified] |
| 5 | Hoffstein, Faber & Braun (2020), "Rebalance Timing Luck" | S, snippet | Timing luck of 100–400 bps a year in semi-annual 100-stock portfolios. Worse with concentration and fast signals. N tranches cut it by 1/N. | — | [unverified] |
| 6 | Keller & Keuning PAA/VAA/DAA. Via CXO: [PAA](https://www.cxoadvisory.com/?p=28414), [VAA](https://www.cxoadvisory.com/?p=30082), [DAA](https://www.cxoadvisory.com/?p=31391) | S | PAA2 "out-of-sample" 1993–2015: 10.4% vs 8.2% for 60/40, Sharpe 1.00, drawdown −8.8%. VAA: 10–16% CAGR. CXO: PAA2 "underperforms 60/40 during the 1990s and since 2008"; "multiple moving parts"; reused out-of-sample data is "largely in-sample". No live record found. | Pseudo out-of-sample | [1] |
| 7 | Zakamulin, moving-average timing 1860–2009. Via [CXO](https://www.cxoadvisory.com/technical-trading/market-timing-with-moving-averages-over-the-very-long-run) | S | Higher Sharpe but lower mean return than buy-and-hold. Over 5–10 year horizons timing is "about equally likely to outperform and underperform". No significant outperformance in the second half-sample. | Long-run out-of-sample | [1] |
| 8 | Huang, Li, Wang & Zhou (2020), JFE 135. [Abstract](https://econpapers.repec.org/RePEc:eee:jfinec:v:135:y:2020:i:3:p:774-794) | P | Time-series momentum "performance is virtually the same as that of a similar strategy that is based on historical sample mean and does not require predictability… the evidence on TSM is weak." | Out-of-sample critique | [2+] with #7 |
| 9 | Moskowitz, Ooi & Pedersen (2012); Hurst, Ooi & Pedersen. [AQR TSMOM](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum), [AQR Century](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing) | P, abstracts | 12-month trend positive "for every asset contract we examine" (58 futures). Profitable back to 1880. These are long/short futures results, not long-only ETFs. | In-sample plus extended history | [1] (same group) |
| 10 | AQR, ["You Can't Always Trend When You Want"](https://www.aqr.com/Insights/Research/Journal-Article/You-Cant-Always-Trend-When-You-Want) | S, snippet | Weak 2010s trend returns attributed to "fewer large moves", not a broken signal. | Post-publication | [1] |
| 11 | McLean & Pontiff (2016), JF 71; Falck, Rej & Thesmar (2021), [arXiv 2105.01380](https://arxiv.org/pdf/2105.01380) | S for the first; P for the second | McLean-Pontiff: 97 predictors, returns 26% lower out of sample and 58% lower post-publication (via [Quantpedia](https://quantpedia.com/how-do-investment-strategies-perform-after-publication/)). Falck et al., independent data: "Sharpe ratios of strategies decay by about one half after publication"; decay grows 5 points per publication year. | Post-publication | [2+] |
| 12 | Harvey, Liu & Zhu, [NBER w20592](https://www.nber.org/papers/w20592) | P, abstract | New factors need "a t-ratio greater than 3.0"; "most claimed research findings in financial economics are likely false". | — | [1] |
| 13 | Moreira & Muir, [NBER w22208](https://www.nber.org/system/files/working_papers/w22208/w22208.pdf); Cederburg et al. (2020), [JFE abstract](https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117) | P both | Moreira-Muir: volatility-scaled market factor alpha 4.86% a year, in-sample. Cederburg: managed portfolios "do not systematically outperform… in direct comparisons"; real-time versions "generally earn lower certainty equivalent returns and Sharpe ratios". Worse for 72 of 103 strategies ([CXO](https://www.cxoadvisory.com/?p=32455)). | In-sample vs out-of-sample | [2+] that it is contested |
| 14 | Daniel & Moskowitz, [NBER w20439](https://www.nber.org/system/files/working_papers/w20439/w20439.pdf) | P, abstract | Momentum crashes occur "following market declines and when market volatility is high… contemporaneous with market rebounds". | In-sample | [1] |
| 15 | Asness, Moskowitz & Pedersen, ["Value and Momentum Everywhere"](https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere); Koijen et al., ["Carry"](https://www.nber.org/system/files/working_papers/w19325/w19325.pdf) | P, abstracts | Value and momentum premia in eight markets, negatively correlated with each other. Carry predicts returns across asset classes but does "poorly" in global recessions. Long/short, gross. | In-sample | [1] each |
| 16 | Asness, Frazzini & Pedersen, [risk parity](https://www.aqr.com/Insights/Research/Journal-Article/Leverage-Aversion-and-Risk-Parity); Anderson, Bianchi & Goldberg (2012) | P abstract; S snippet | AFP: levered risk parity outperformed since 1926. ABG: unlevered risk parity had the highest Sharpe and the lowest return 1926–2010; after borrowing and trading costs the levered version loses to 60/40. | Contested | [2+] that unlevered risk parity means lower return |
| 17 | Asness et al., ["Contrarian Factor Timing is Deceptively Difficult"](https://www.aqr.com/Insights/Research/Journal-Article/Contrarian-Factor-Timing-is-Deceptively-Difficult) | P, abstract | Value-spread factor timing gives "somewhat disappointing results"; "a weak addition". | — | [1] |
| 18 | Campbell, Serfaty-de Medeiros & Viceira, [NBER w13088](https://www.nber.org/system/files/working_papers/w13088/w13088.pdf) | P, full text | The AUD and CAD "are positively correlated with local-currency returns on equity markets around the world". "The volatility reduction from full currency hedging is particularly small for Australian and Canadian investors." 1975–2005. | In-sample | see #19 |
| 19 | [RBA Bulletin, Sept 2009](https://www.rba.gov.au/publications/bulletin/2009/sep/2.html) | P | Over the prior two decades "the hedging ratio yielding the highest returns for a given level of volatility would have been between 60 and 100 per cent". With positive covariance, hedged returns "will always be less volatile than unhedged". | In-sample | Disagrees with #18 |
| 20 | Australian factor study (25 years), via [Quantpedia](https://quantpedia.com/smart-beta-strategies-in-australia/); ASX 52-week-high study, [RePEc](https://ideas.repec.org/a/sae/ausman/v35y2010i3p227-244.html) | S | "Statistically significant evidence" for value, momentum, low volatility and quality in Australia; diversify across them. But liquid-stock momentum showed no significant profit after costs and short-sale limits, 1996–2008. | In-sample | Contested |
| 21 | [IBKR Australia pricing page](https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php) | P | Fixed: 0.08% of trade value, minimum A$6 per order, ex-GST. Tiered: 0.08%, minimum A$5, plus exchange fees. | Current | [1] primary |
| 22 | ATO CGT discount and franking rules (snippets); Budget 2026–27 coverage: [BDO](https://www.bdo.com.au/en-au/insights/budget/2026/changes-to-the-capital-gains-tax-discount), [PwC](https://www.pwc.com.au/tax/tax-alerts/2026-27-federal-budget-cgt-changes-is-30-june-2027-a-transaction-deadline.html), [EY](https://www.ey.com/en_gl/technical/tax-alerts/australias-2026-27-federal-budget) | S | Current law: 50% discount only if held at least 12 months; none below. Franking 45-day rule, with an exemption at A$5,000 or less of credits a year. Proposed: discount replaced by indexation from 1 July 2027, plus a 30% minimum tax on capital gains. Bills reportedly introduced 28 May 2026; one site says not yet legislated. | Current / proposed | [2+] on the announcement; legislative status [unverified] |

**Data-quality flags**
- CXO's "2006–2012 since publication" line for Faber repeats the 1973–2012 return and drawdown figures and looks garbled. I did not use it.
- The 11.7% in row 2 appears as "original CAGR" in CXO and "max drawdown" in Concretum. Both may be true; confirm in the paper.
- No independent year-by-year GEM record for 2014–2025 was found. One blog (Price Action Lab, not read) claims post-2018 returns fell to about a third of pre-publication. [unverified]
- The DHHF 0.19% and VDHG 0.27% fees are from one aggregator (Pearler). [1]

## 2. Robust versus contested

**Robust**

1. **Trend filters cut drawdown and volatility; they do not reliably add return.** [2+: Faber, Zakamulin, Huang et al.]
   - In-sample the return gain is 0 to +1 point a year, gross.
   - Over 5–10 year windows, beating buy-and-hold is a coin flip.
   - Much of the "trend profit" is simply being long assets with positive drift.
   - Post-publication GTAA kept the drawdown control (11.7% through the GFC, 2020 and 2022) but returned only about 6% a year. [1]
2. **Published edges roughly halve after publication.** [2+: McLean-Pontiff, Falck et al.] Haircut any backtest Sharpe by 50%.
3. **Concentrated, single-specification rules are fragile.** [1 primary-quality, 2 unverified snippets] Winner-take-all, one lookback and one rebalance day carry timing luck of hundreds of bps a year. GEM is the textbook case. Ensembles and tranches are the fix.
4. **Volatility-timing as a return source does not survive real-time implementation.** [2+ as a contested in-sample result]
5. **Unlevered risk parity raises Sharpe but lowers return.** [2+] A long-only, no-leverage investor pays for the smoother ride.
6. **Costs and tax at this scale are first-order.**
   - A$6 on a A$2,500 sleeve is 0.24% per order, so a VAS-to-VGS switch costs about 0.5% of that sleeve.
   - Every switch realises gains, and under current law gains held under 12 months get no discount.
   - Franking is not a constraint: the small-holder exemption covers a A$5k account, but time in cash forgoes franked dividends.

**Contested**

- **Whether time-series momentum is real predictability.** AQR says yes; Huang et al. say it is weak.
- **Hedging for AUD investors.** Campbell et al. find little risk benefit; the RBA found 60–100% hedging was best on a return-per-volatility basis over the two decades to 2009. Neither is post-2009.
- **Keller-family strategies.** Their "out-of-sample" tests reuse well-mined data, and I found no live record.
- **ASX factor premia net of costs.**
- **Factor timing.** AQR finds it weak; the Research Affiliates counter-view was not retrieved.

## 3. Decisions for the spec

### (a) Live A$5k rule

**D1. Do not run VAS/VGS/cash dual momentum as currently framed (winner-take-all).** I do not recommend it as the live rule.
- Its relative-momentum leg picks between two highly correlated equity sleeves on one lookback and one date. That is the most fragile construction in the literature.
- Its only in-sample support (GEM, 17.4% vs 9.6%) is gross, from one author's book, and specification-sensitive.
- The robust part of the evidence is the trend leg, and that buys drawdown control, not return.

**D2. Declare the benchmark: buy-and-hold DHHF, or static 40% VAS / 60% VGS.**
- Expected net return of any trend rule against this is about zero or slightly negative after costs and tax.
- The live rule's justification is drawdown control plus operational learning. Write that into the spec so nobody later judges it on return alone.
- If the goal were purely wealth at A$5k, hold DHHF and stop.

**D3. If a live rule is run, use this one (L1: a fixed-weight ensemble trend filter).**

| Item | Rule |
|---|---|
| Sleeves | VAS 40%, VGS 60% (unhedged). No relative-momentum switching between them. |
| Signal data | Month-end adjusted (total-return) closes. |
| Signal | Three votes per sleeve: 6-month return above 0, 12-month return above 0, price above 10-month SMA. Score = votes ÷ 3. |
| Target | Sleeve weight × state. State is 1 if score ≥ 2/3; 0 if score = 0. If score = 1/3, keep the prior state. Binary states keep orders at A$2,000 or more. |
| Out-of-market asset | A cash ETF, only if the IBKR cash rate on small balances is about zero. This was not checked; confirm before go-live. Otherwise leave uninvested cash. |
| Timing | Evaluate once a month after the close; trade next session with limit or auction orders. No intra-month stops and no daily checking. All the evidence is monthly. |
| Tranching | Person A evaluates on the last trading day; person B on the 10th trading day. Two accounts halve household timing luck for free. |
| Cost guard | Fixed pricing. Skip any order under A$1,000. Log commissions; flag if annual costs exceed 0.6% of the account. |
| Expected behaviour | About one round trip or fewer per sleeve per year; invested roughly 70% of the time. [1, secondary] |
| Review | Judge on max drawdown and tracking against D2 over at least 3–5 years. Do not re-tune lookbacks on live results. |

**D4. No bonds, gold or risk-parity sleeves live at A$5k.** Each extra sleeve drops order size below about A$1,700, where the A$6 minimum exceeds 0.35% per order. Revisit when each account passes about A$15–20k. Test them in paper first.

**D5. Hedging: VGS unhedged for live.** Campbell et al. support it on risk grounds, and DHHF is also unhedged [not verified here]. The RBA result is why the hedged-versus-unhedged choice becomes a paper experiment rather than settled.

**D6. Tax handling.**
- Record parcel-level cost base for every trade.
- The spec must not assume the 50% discount persists. The 2026–27 Budget package would replace it with indexation and a 30% minimum tax from 1 July 2027.
- Confirm the bill's status with the ATO or an adviser before go-live. It changes the after-tax comparison between L1 and buy-and-hold, and I have not modelled the direction.
- Under current law, model short-held gains at full marginal rate.

### (b) Paper multi-asset strategy

**D7. Design: strategic risk-budgeted weights times a per-asset ensemble trend score.** No winner-take-all, no optimised breadth or canary parameters.

| Item | Rule |
|---|---|
| Universe | About 12–20 ASX-listed ETFs across at least four asset classes. Candidate tickers below are not verified; confirm liquidity and inception. |
| Candidates | AU equity (VAS, small caps); global equity (VGS, hedged VGAD, US, Europe, Japan, Asia, EM); listed property and infrastructure; AU and global government bonds (VAF, VGB, a hedged global bond fund); gold; cash ETF. |
| Factor sleeves | Global quality, value, minimum-volatility and an Australian factor ETF, held static. No factor timing. |
| Strategic weights | Class budgets: equities 55%, real assets 10%, bonds 25%, gold 10%. Within a class, inverse 12-month volatility, capped at twice equal weight. |
| Trend score | Average of five votes: 3-, 6-, 9- and 12-month total return above the cash ETF's return, and price above 10-month SMA. Score takes values 0, 0.2, …, 1. |
| Target weight | Strategic weight × score. The remainder goes to the cash ETF. No leverage and no redistribution to winners. |
| Rebalance | Monthly in four weekly tranches. No-trade band: act only if the weight drifts by more than 20% relative, or 1 point absolute. |
| Cost model | 0.08% with a A$6 minimum per order, plus 5 bps half-spread (10 bps for thin ETFs). Run at notional A$5k, A$50k and A$250k to show where the minimum bites. |
| Tax model | Parcel-level, under both current law and the proposed indexation regime. |
| Benchmarks | DHHF; the static strategic mix; L1. |
| Variants to pre-register | V0 static mix; V1 the rule above; V2 V1 with a 10% portfolio volatility cap; V3 V1 with the hedged global sleeve swapped for unhedged; V4 a Keller-style top-6 with breadth protection. |
| Reporting | Net CAGR, volatility, Sharpe, max drawdown, turnover, share of time in cash, and dispersion across the four tranche start days. |

- **Why this shape:** going from 5 to 13 assets lifted Faber's in-sample Sharpe from 0.73 to 0.94 [1]. Timing luck falls with breadth and tranching. Inverse-vol weighting within a risk budget is the long-only version of risk parity that does not depend on leverage.
- **Why V2 and V4 are controls only:** the volatility cap is risk control, not alpha (Cederburg). V4 exists to show the fragility locally, not as a candidate.

**D8. Acceptance test before any paper variant goes live.** V1 must:
- cut max drawdown by at least a third against V0;
- lose no more than 1 point a year of net CAGR;
- show tranche dispersion under 1.5 points a year;
- still pass after its excess Sharpe is halved.

**D9. Data.** VGS and DHHF histories are too short to test anything. Backtest on index proxies from 1990 or earlier (S&P/ASX 300 TR, MSCI World ex-Australia NR in AUD, both hedged and unhedged). Treat the ETF era as a sanity check only.

**Stopping point:** the last rounds of searching (GEM live record, Keller live record, AUD hedging, CGT) changed nothing in D1–D9 except adding D6's CGT warning.

**Open items for the coordinator**
1. Legislative status of the CGT bills.
2. IBKR interest on small AUD balances.
3. ETF tickers and fees.
4. An independent 2014–2026 GEM record.
5. The blocked hosts above, if primary reads of Faber, Antonacci, Keller and McLean-Pontiff are required.