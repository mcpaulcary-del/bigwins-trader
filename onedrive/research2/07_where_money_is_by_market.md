# Where is the most money to be made? Markets comparison for an Australian IBKR end-of-day systematic trader (13 Nov 2026)

**Research limits.** WebFetch could not reach `www.interactivebrokers.com.au`, `www.interactivebrokers.com`, `www.ato.gov.au` or `qoppac.blogspot.com`; these hosts need to be allowed in the session's network settings. No primary page was fetched directly, so every figure comes from search summaries of the cited pages or from memory. Tags: **[S]** = seen in a search summary this session; **[M]** = from memory, unverified. Check all fee, margin and tax numbers against the live pages before they go into a spec.

## 1. Bottom line

- **No market has "the most money" for a retail systematic trader.** Durable return comes from being paid to hold risk (shares, bonds, trend) cheaply and for a long time, not from out-trading anyone.
- **At A$5,000, market choice barely matters in dollars.** A good 8% year is A$400; a bad cost structure takes A$100–400 of it. Savings rate and cost control dominate.
- **Best expected return per unit of effort:** cheap diversified equity exposure, with a trend overlay mainly to cut drawdowns rather than raise returns.
- **Best-documented genuinely systematic strategy:** diversified trend following across futures. Done properly it needs roughly A$100k+, and live net Sharpe has been about 0.3–0.5, not the 1.0+ of backtests.
- **US-listed ETFs are the best venue for a small account.** Commissions are roughly a tenth of ASX, and a Faber-style five-asset trend portfolio becomes viable at A$5k.
- **Reject CFDs and spot FX.** Defer options and direct futures until the account is large enough. Treat crypto as a small, capped ETF sleeve at most.

## 2. Risk premia versus alpha

- **Risk premia** are compensation for bearing risk anyone can hold. These are my planning ranges, not guarantees:
  - Equity premium: about 4–5% real long-run on global equities, Sharpe about 0.3–0.4, drawdowns of 50% [M, Dimson-Marsh-Staunton].
  - Term premium on bonds: small and unstable.
  - Trend and carry "style premia": Sharpe about 0.3–0.6 net when diversified.
  - Volatility premium from option selling: equity-like Sharpe with crash skew.
- **Alpha** is beating other participants. An end-of-day retail system on public data has no informational or speed edge, so plan on zero alpha.
- **The retail edge is structural:** low costs, no management fees, no career risk, and tolerance for long flat periods.

## 3. Market by market

### 3.1 ASX shares and ETFs (current design)

- **For:** AUD-denominated, franking credits on VAS, simple tax, daytime hours, already built.
- **Against:** the A$6.60 minimum binds until an order reaches A$7,500 (6.60 / 0.088%).
  - A A$1,000 order costs 0.66% a side; a A$250 order costs 2.6% a side.
  - The ~20-instrument ASX trend universe is uneconomic at A$5k. It is tolerable at about A$40k (A$2k positions, 0.33% a side) and unconstrained at about A$150k.
- VAS/VGS/cash monthly switching at 4–6 orders a year costs A$26–40, or 0.5–0.8% of A$5k. That is acceptable.
- I could not confirm IBKR's current ASX rate; the Asia-Pacific pricing page showed headers only [S]. I used your max(A$6.60, 0.088%).

### 3.2 US-listed ETFs and stocks

**Costs**
- Fixed: USD 0.005 a share, minimum USD 1.00 [S].
- Tiered: USD 0.0035 a share at the lowest volume tier [S]. The USD 0.35 minimum appears on an IBKR schedule but its tier mapping was unclear in the summary [S]; small exchange and regulatory pass-throughs are extra [M].
- FX: a manual AUD-to-USD conversion costs 0.002% with a USD 2.00 minimum and no added spread; auto-conversion costs about 0.03% [S].
  - Below roughly A$10k per conversion, auto-conversion is cheaper (0.03% of A$5,000 is A$1.50, versus about A$3).
  - Confirm which applies to an IBKR Australia cash account.

**Can A$5k run a Faber-style five-asset trend portfolio more cheaply on US ETFs? Yes, by roughly ten times on commissions.** The table assumes AUD/USD 0.65 and five A$1,000 sleeves.

| Orders per year | ASX at A$6.60 | US tiered at USD 0.35 | US fixed at USD 1 |
|---|---|---|---|
| 7 (Faber reports under one round trip per asset per year [M]) | A$46 (0.92%) | A$3.80 (0.08%) | A$10.80 (0.22%) |
| 20 (whipsaw year plus rebalances) | A$132 (2.6%) | A$10.80 (0.22%) | A$30.80 (0.62%) |
| 60 (monthly rebalance of all five) | A$396 (7.9%) | A$32 (0.65%) | A$92 (1.8%) |

- Initial FX adds A$1.50–3, and spreads on the liquid US ETFs are about 1–2 bps [M].
- US expense ratios are also lower: VTI/VEA about 0.03–0.05% against VGS 0.18%, GLDM 0.10% against ASX gold ETFs 0.15–0.40% [M].
- ASX has no good broad-commodity ETF; the US has DBC and PDBC [M].

**Frictions**
- **Dividends:** 15% US withholding with a W-8BEN on file [M; the search did not confirm the rate]. It is creditable through the foreign income tax offset, which needs no limit calculation up to A$1,000 of foreign tax and is non-refundable [S, ATO].
- **Lost franking:** worth roughly 1–1.5% a year on the Australian equity sleeve [M]. Keep Australian equities on ASX.
- **Currency:** every sleeve becomes an AUD/USD position. Unhedged US Treasuries are mostly a currency bet for an AUD investor, so prefer AUD bonds or cash for the defensive leg.
- **Idle cash:** IBKR pays no interest on roughly the first USD 10k and pro-rates below USD 100k of account value [M]. Hold a T-bill ETF such as SGOV or BIL when "in cash"; that is cheap at USD 0.35 an order but ruinous at A$6.60.
- **US estate tax:** non-residents get only a USD 60,000 exemption on US-situs assets, which includes US-domiciled ETFs [S].
  - The 1953 Australia–US estate tax convention gives Australian domiciliaries a pro-rata share of the full unified credit (US assets divided by worldwide estate) [S, law-firm sources that disagree on detail].
  - In practice ordinary estates likely owe nothing, but a US estate return is needed above USD 60k to claim it.
  - Irrelevant at A$5k; get advice before US holdings exceed about A$90k per person.
- **PFIC:** not relevant to Australian residents.
- **Hours:** the US session is 01:30–08:00 AEDT (November to March) and 23:30–06:00 AEST (April to September), with an hour's shift in changeover weeks [M].
  - Compute signals after the US close at about 08:30 Sydney time and queue market-on-open or limit-on-open orders for the next session.
  - Orders execute while you sleep, so the system needs robust order-state reconciliation.
- **Share prices:** SPY costs several hundred USD a share. Use lower-priced equivalents (VEA, IEF, VNQ, GLDM, SPYM) or fractional shares; verify API fractional support in paper.

### 3.3 Futures (CME micros, ASX SPI)

**Evidence: the strongest for any systematic strategy**
- Moskowitz, Ooi and Pedersen (2012): time-series momentum across 58 futures markets, diversified gross Sharpe above 1 for 1985–2009 [M].
- Hurst, Ooi and Pedersen: 67 markets from 1880 to 2016, net Sharpe about 0.76 after simulated costs and 2/20 fees [S, secondary write-up].
- Live results are much lower. The SG Trend Index has run at roughly Sharpe 0.3–0.4 since 2000 [M].
  - SG CTA Index +20.1% in 2022 [S]; down almost 3% in 2023 [S].
  - SG Trend about +2.6% in 2024, down 10.5% in the first half of 2025, about +2.4% for 2025 [S, trade press].
  - Expect multi-year flat stretches; the payoff is crisis convexity (2008, 2022).

**Costs**
- IBKR charges USD 0.85 a contract, and micros carry a CME fee of USD 0.353 [S]. That is about USD 1.20 a side, or about 0.003% of notional on MES. Costs are negligible; capital is the constraint.

**Margin and contract size**
- MES overnight margin is about USD 2,350 [S, a third-party figure, unverified].
- MES notional is 5 × the index. At an illustrative S&P level of 7,000 that is USD 35k, about A$54k: more than ten times a A$5k account in one contract.
- SPI 200 is A$25 a point and the mini is A$5 a point [S]. Margin of about A$15.7k is quoted by a third-party broker, undated [S]. Even the mini is about A$45k notional at an illustrative index of 9,000.

**Minimum capital (Carver)**
- Minimum capital per instrument is roughly: minimum contracts × notional × instrument volatility ÷ (diversification multiplier × instrument weight × target volatility) [M, from *Systematic Trading* and *Advanced Futures Trading Strategies*]. He prefers about 4 contracts per instrument so positions can scale [S, podcast recap].
- My worked example: MES at 16% volatility, 10 instruments, multiplier 2, 20% target volatility needs about USD 140k for one contract and about USD 560k for four. Micro FX and micro yield contracts need far less.
- Carver's own statements: "absolute minimum… around the 50k mark" (forum post attributed to him) and about USD 100k to capture diversification [S, secondary].
- *Leveraged Trading*'s starter system works from about £1–4k, but on spread bets or CFDs with a single instrument [S, book review]. That is not a diversified futures portfolio.

**Tax and risk**
- Tax is most likely on revenue account, by analogy with the ATO's CFD ruling TR 2005/15: ordinary income, no CGT concession, losses deductible [S, secondary]. No futures-specific ATO ruling was found; get advice.
- Leverage is the main danger: gaps can lose more than the margin posted. Size by volatility target, never by margin.

**Shortcut for small accounts:** US-listed managed-futures ETFs (DBMF, KMLM, CTA; fees about 0.85–0.90% [M]) give diversified futures trend for a USD 0.35 commission at any size. Confirm IBKR Australia lets retail clients trade them.

### 3.4 FX and share CFDs: reject

- ASIC's product intervention order caps retail leverage at 30:1 on major FX and 2:1 on crypto [S]; other tiers are 20:1, 10:1 and 5:1 [M].
- The order runs to 23 May 2027. ASIC proposed on 12 October 2026 to extend it to 2037 [S].
- In 2023–24, 68% of retail CFD clients lost money. Net losses exceeded A$458 million, including A$73 million in fees [S, ASIC figures via secondary coverage].
- ASIC's January 2026 review (REP 828) found more than half the sector breached the order, with about A$40 million refunded [S].
- Why reject: the dealer is your counterparty, overnight financing and spreads compound against you, there is no documented stand-alone edge in retail spot FX, and gains are taxed on revenue account.
- Everything a CFD offers is available cheaper through ETFs now and exchange-traded micros later.

### 3.5 Crypto: small optional sleeve, through ETFs only

- **Evidence:** Liu and Tsyvinski (Review of Financial Studies, 2021) find strong time-series momentum [S]. A peer-reviewed crypto trend factor survives costs for 2015–2022 [S]. Other work finds no out-of-sample predictability for Bitcoin itself [S]. A recent preprint claiming net Sharpe 2.4 is unreviewed [S]. The history is short and mostly one regime, so treat the evidence as moderate to weak.
- **Risk:** annualised volatility of 50–80% and drawdowns of 75–85% (2018, 2022) [M].
- **Access:** IBKR Australia reportedly does not offer spot crypto to retail clients; exposure is through spot-bitcoin exchange-traded products and CME futures [S, third-party]. IBKR Australia has a spot-bitcoin ETP page [S].
- **Why ETFs:** no exchange custody risk, no 24/7 operations, and the same order plumbing as every other sleeve.
- **Regulation:** the Digital Assets Framework legislation passed in about April 2026 and requires platforms to hold an Australian financial services licence, with roughly 12 months of transition [S; dates conflict between sources].
- **Tax:** a CGT asset; every disposal, including crypto-to-crypto swaps, is a CGT event [S, ATO].
- **Verdict:** if wanted, a trend-filtered bitcoin ETF sleeve capped at 5% or less of the portfolio. Paper it first.

### 3.6 Options (covered calls, cash-secured puts): defer to A$100k+

- Cboe's PutWrite index returned 9.40% a year against 9.91% for the S&P 500 from July 1986 to August 2023, with volatility of 10.3% against 15.4% and a maximum drawdown of 32.7% against 51.0% [S, Cboe].
- The BuyWrite index returned about 8.5% against 11.2% since 1986 [S, secondary].
- Israelov and Nielsen (2015) show a covered call is equity exposure plus short volatility [S]. It is a different risk mix with capped upside, not "income".
- One US contract covers 100 shares, so a cash-secured put on SPY ties up more than USD 60k. Even a USD 50 ETF needs USD 5k, which is a whole account in one position.
- Assignment, early exercise, rolls and ex-dividend handling add substantial automation complexity.
- Premiums are likely revenue-like for a systematic writer [M].

## 4. Ranked comparison

Return and Sharpe figures are my planning estimates after costs and before tax.

| Rank | Market / approach | Expected net result | Evidence | Realistic minimum | Costs | Tax (Australian resident) | Ops complexity | Automation fit |
|---|---|---|---|---|---|---|---|---|
| 1 | US-listed ETF trend portfolio (GTAA-style) | Equity-like or slightly lower return; Sharpe 0.4–0.6; drawdown 15–25% | Strong in-sample, weaker since 2007 [M] | A$5k | About 0.1–0.3% a year | CGT, 15% withholding with offset, FX records | Medium (FX, overnight fills) | High |
| 2 | ASX ETF trend switch (current) | Similar, less diversified | Same | A$5k for 2–3 ETFs; A$40k+ for 20 names | 0.5–1% at A$5k | Simplest; franking | Low | High |
| 3 | Managed-futures ETF sleeve | Sharpe about 0.3–0.5; low equity correlation | Strong (live indices) | A$5k | Fees about 0.85% | CGT and foreign income | Low | High |
| 4 | Direct micro-futures trend | Sharpe 0.3–0.6 at 10–20% volatility | Strongest | A$100k (bare minimum about A$75k) | About 1% a year or less | Revenue account (verify) | High (rolls, margin, 23-hour market) | High, unforgiving |
| 5 | Option overwriting | Equity-like Sharpe, lower return | Strong, but not extra return | A$100k+ | Moderate | Mostly revenue | High | Medium |
| 6 | Crypto trend via ETFs | Highly uncertain; extreme volatility | Moderate to weak | A$5k (capped sleeve) | Low | CGT | Low via ETF, high via exchange | High via ETF |
| 7 | ASX SPI futures | Single-market bet | n/a | A$250k+ | Low | Revenue | Medium | Medium |
| 8 | FX and share CFDs | Negative for the median client | Strong evidence of losses | n/a | Spread plus financing | Revenue | Medium | Reject |

## 5. How account size changes the answer

| Account | What is feasible | What is not |
|---|---|---|
| A$5k | 2–3 ASX ETFs, or 5–6 US ETFs on tiered pricing | 20 ASX names, any futures, options |
| A$20k | US GTAA plus a managed-futures ETF sleeve plus VAS on ASX; perhaps 5–8 ASX names | Direct futures (one MES is about 2.7 times the account) |
| A$100k | Starter micro-futures trend (8–12 instruments at 10–12% target volatility); full ASX 20-name universe; first covered calls | Carver-grade 4-contract granularity |
| A$250k+ | 20–30 futures instruments; options overlay; US estate tax planning becomes necessary | — |

## 6. Tax flags that affect design

- **CGT change (confirm with a tax agent):** the 2026–27 Budget replaces the 50% CGT discount with cost-base indexation and a 30% minimum tax on capital gains from 1 July 2027. Gains accrued before that date keep the discount [S, PwC, KPMG, Treasury]. It is reported as enacted in mid-2026, but sources conflict on the Act name and date [S].
  - The after-tax advantage of holding more than 12 months shrinks, which narrows the gap between trend switching and buy-and-hold.
  - The 30% floor hurts low-bracket holders.
- **Investor or trader:** the ATO treats a shareholder as an investor unless they show a business of trading; the tests are repetition, volume and business-like organisation [S, ATO]. A monthly ETF system is plausibly capital account; frequent automated trading may not be. Decide and document this with an adviser.
- **Foreign income tax offset:** stays simple while foreign tax is A$1,000 a year or less [S].

## 7. Staged recommendation

| Stage | Live | Paper (must pass before the next stage) |
|---|---|---|
| Now, A$5k each | Keep VAS/VGS/cash monthly trend on ASX. Optionally move the non-Australian sleeves to a US GTAA-5 after 3 clean paper months. | (a) US GTAA-5 with real FX, overnight on-open orders and reconciliation. (b) Managed-futures ETF sleeve. (c) Micro-futures trend at a notional A$150k. (d) Bitcoin-ETF trend sleeve. (e) Keep the ASX 20-name paper running. |
| A$20k | VAS on ASX for franking, US GTAA sleeves, 10–20% managed-futures ETF, T-bill ETF as cash. | Micro-futures system for 12+ months including contract rolls, margin stress tests and gap scenarios; covered-call simulator. |
| A$100k+ | Add direct micro-futures trend at 25–30% of capital, 10–12% target volatility, 8–12 instruments. Turn on the ASX 20-name universe. | Options overlay; expansion to 20–30 futures. |
| A$250k+ | Full diversified futures; estate tax review; consider a company or trust structure with an adviser. | — |

**Gate for every promotion:** paper tracking error against backtest within tolerance, zero unreconciled orders for three months, and a written maximum-drawdown expectation the owners have signed off.

## 8. Spec-ready recommendations

1. **Markets, in order:** ASX ETFs (live) → US-listed ETFs (next) → managed-futures ETF sleeve → CME micro futures (A$100k+) → options (A$100k+, optional). Excluded: CFDs, spot FX, spot crypto on exchanges, SPI below A$250k.
2. **US GTAA instruments** (confirm tickers and tradability):
   - US equity: VTI or SPYM.
   - International equity: VEA, plus optionally VWO.
   - Real estate: VNQ.
   - Gold: GLDM.
   - Commodities: PDBC or DBC.
   - Defensive leg: SGOV or BIL rather than long Treasuries.
   - Keep VAS on ASX.
3. **Signal:** month-end price against the 10-month moving average, per sleeve, with a rebalance band of ±20% relative so you avoid full monthly rebalances.
4. **IBKR settings:**
   - Cash account at stages 1–2; margin account only when futures start.
   - Tiered pricing for US.
   - W-8BEN on file.
   - FX by auto-conversion below about A$10k per conversion, manual above.
   - Market data: delayed or the cheapest snapshot bundle.
   - Permissions: US stocks/ETFs now; futures in paper only.
5. **Execution:** signals at 08:30 Sydney after the US close; limit-on-open or market-on-open for the next US session; the reconciliation job runs before the ASX open; handle both daylight-saving changeovers explicitly.
6. **Cost guards:**
   - Reject any order whose commission exceeds 0.5% of its value.
   - Minimum ASX order A$1,500.
   - Minimum ASX position A$2,000 before the 20-name universe goes live, which needs an account of about A$40k or more.
7. **Capital thresholds:**
   - A$5k: at most 3 ASX or 6 US positions.
   - A$20k: add the managed-futures ETF.
   - A$100k: micro futures on at most 30% of capital.
   - About A$90k of US-situs assets per person: estate tax review.
8. **Futures paper spec:** MES, MNQ or M2K (one only), micro 10-year yield, MGC, MCL, M6A, M6E, plus 2–4 more low-notional markets. Volatility target 10–12%; position sizing in the Carver style; record the minimum capital per instrument; go-live requires at least one whole contract in every instrument at average forecast.
9. **Crypto, optional:** one spot-bitcoin ETF, the same 10-month trend rule, hard cap of 5%.
10. **Tax data:** log the AUD value of every fill, withholding per dividend and parcel-level cost base from day one; flag 1 July 2027 valuations for the CGT transition.
11. **Verify before coding the numbers:** IBKR Australia's ASX and US commission schedules, the tiered minimum, auto-conversion on cash accounts, API fractional-share support, interest tiers, MES and SPI margins, and Carver's formula against the books.

## Sources

- IBKR pricing (via search; direct fetch blocked): [commissions home](https://www.interactivebrokers.com.au/en/pricing/commissions-home.php), [Asia-Pacific stocks](https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php), [futures](https://www.interactivebrokers.com/en/pricing/commissions-futures.php), [CME fees](https://interactivebrokers.com/en/accounts/fees/CME.php), [spot currencies](https://www.interactivebrokers.co.uk/en/pricing/commissions-spot-currencies.php), [spot bitcoin ETPs](https://interactivebrokers.com.au/en/trading/spot-bitcoin-etps.php), [Australia margin accounts](https://ibkb.interactivebrokers.com/de/node/4370)
- MES margin (third party): [MetroTrade](https://www.metrotrade.com/interactive-brokers-vs-metrotrade-futures-broker-comparison/). SPI specs and margin: [ASX summary](https://www.asx.com.au/data/futures/reports/EODWebMarketSummary261020SFD.htm), [Capital Futures](https://www.capitalfutures.com.tw/en-us/productinformation/commodityinfo?cid=ap)
- ASIC: [26-239MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-239mr-asic-moves-to-extend-and-strengthen-cfd-consumer-protections), [CS 64](https://asic.gov.au/regulatory-resources/find-a-document/consultations/cs-64-protecting-retail-investors-proposed-extension-and-amendments-to-the-cfd-product-intervention-order), [REP 828](https://download.asic.gov.au/media/tq0he35c/rep828-published-20-january-2026.pdf), [26-004MR](https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-004mr-asic-secures-nearly-40-million-in-refunds-to-investors-and-drives-change-after-cfd-sector-falls-short/), [22-082MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2022-releases/22-082mr-asic-s-cfd-product-intervention-order-extended-for-five-years/)
- ATO: [foreign income tax offset](https://www.ato.gov.au/individuals-and-families/your-tax-return/instructions-to-complete-your-tax-return/mytax-instructions/2026/tax-offsets/foreign-income-tax-offset), [share investing versus trading](https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/shares-and-similar-investments/share-investing-versus-share-trading), [crypto swaps](https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-to-crypto-exchange-or-swap), [TD 2006/25](https://www.ato.gov.au/law/view/pdf/pbr/td2006-025.pdf)
- CGT reform: [Treasury](https://treasury.gov.au/policy-topics/taxation/budget2026-27), [PwC](https://www.pwc.com.au/tax/tax-alerts/2026-27-federal-budget-cgt-changes-is-30-june-2027-a-transaction-deadline.html), [KPMG](https://kpmg.com/us/en/taxnewsflash/news/2026/06/tnf-australia-legislation-amending-capital-gains-tax-and-introduce-new-tax-reform-measures-passes-parliament-with-amendments.html), [Accountants Daily](https://www.accountantsdaily.com.au/tax-compliance/22862-top-10-things-you-need-to-know-about-the-cgt-changes)
- US estate tax: [1953 convention Act](https://www.legislation.gov.au/C1953A00083/asmade/1953-12-11/text/original/epub/OEBPS/document_1/document_1.html), [Treasury treaties page](https://treasury.gov.au/tax-treaties/estate-gift-tax-treaties/), [SF Tax Counsel](https://sftaxcounsel.com/blog/us-australia-estate-tax-treaty-australian-investors/), [Hall & Wilcox](https://hallandwilcox.com.au/news/us-links-big-risks-how-your-us-citizenship-or-assets-could-cost-your-estate-millions/)
- Trend evidence: [Century of Evidence (PDF)](https://www.TrendFollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf), [Alpha Architect summary](https://alphaarchitect.com/time-series-momentum-aka-trend-following-the-historical-evidence/), [SG CTA 2022](https://www.hedgeweek.com/flat-december-sees-ctas-complete-record-year-2022/), [SG Trend first half 2025](https://www.alternativeswatch.com/2025/07/01/trend-following-hedge-funds-loss-h1-societe-generale-index/), [Top Traders Unplugged](https://www.toptradersunplugged.com/trend-following-performance-report-october-2025/), [Cambridge Associates](https://publishedresearch.cambridgeassociates.com/?p=19140), [Faber via Swedroe](https://www.etf.com/sections/index-investor-corner/swedroe-why-financial-trends-persist)
- Carver (secondary): [podcast recap](https://thealgorithmicadvantage.substack.com/p/033-rob-carver-the-comprehensive), [Elite Trader thread](https://test.elitetrader.com/et/threads/fully-automated-futures-trading.289589/page-405), [Leveraged Trading review](https://the7circles.uk/?p=27861), [Harriman House](https://harriman-house.com/leveragedtrading)
- Options: [Cboe PutWrite white paper](https://www.cboe.com/insights/posts/white-paper-shows-volatility-risk-premium-facilitated-higher-risk-adjusted-returns-for-put-index), [CXO Advisory](https://www.cxoadvisory.com/equity-options/performance-of-cboe-putwrite-indexes)
- Crypto: [Liu and Tsyvinski, NBER w24877](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf), [crypto trend factor, JFQA](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/S0022109024000747), [arXiv preprint 2602.11708](https://arxiv.org/pdf/2602.11708), [IBKR crypto availability](https://brokerlistings.com/reviews/interactive-brokers/does-interactive-brokers-have-crypto), [digital assets law](https://www.financemagnates.com/cryptocurrency/australia-moves-to-regulate-crypto-platforms-as-parliament-passes-bill-for-afsl/), [Law Society Journal](https://lsj.com.au/articles/crypto-bitcoin-stablecoin-regulated-under-first-australian-digital-assets-legislation/)