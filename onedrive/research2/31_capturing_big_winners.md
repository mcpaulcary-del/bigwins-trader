# Capturing big winners (NEXTDC-type stocks) and "buying the fall": evidence and spec-ready decisions

Report 31, 13 November 2026. Scope: the owner's two statements, "stocks like NEXTDC (ASX: NXT) are the ones I don't want to miss" (sections 1–6) and "look at the fall and then understand the gains... predict that" (section 7). Written against FD_FINAL.md (v2.10) and reports 12, 14, 15, 16 and 18.

**Tags.** **[2+]** two independent sources; **[1]** one source or one originating source; **[unverified]** inference, model memory or a figure I could not confirm; **[computed]** my arithmetic from tagged inputs.

**Access limits.** Read in full: the ASX Investment Products report for October 2026 (PDF, primary) and the September 2026 edition; RePEc/EconPapers abstracts for the journal papers; Quantpedia. Blocked in this session: betashares.com.au, blackrock.com, globalxetfs.com.au, vaneck.com.au, solactive.com, msci.com, aqr.com, nber.org, morningstar.com.au, alphaarchitect.com, core.ac.uk, spglobal.com, cboe.com, firstlinks.com.au, and every price-data host (Yahoo, Stooq, FRED). Consequences:

- **No issuer page was read directly.** ETF fees, size and spreads come from the ASX monthly report (the exchange republishing issuer data), cross-checked against search excerpts of issuer pages where one was returned. That is the basis for [2+] on a fee.
- **No price series could be downloaded**, so I ran no backtest and computed no drawdown table myself. Every return-after-fall figure is from a secondary source.
- **Journal papers were read at abstract level only.** Numbers not in an abstract are from secondary summaries and tagged [1].

---

## 0. Answer in brief

1. **The core already owns NEXTDC, and will own every future one.** VAS has held NXT since it entered the S&P/ASX 300; NXT is about 0.3–0.4% of VAS today. A cap-weighted index cannot miss a listed winner, and its weight rises as the stock wins, with no trade and no tax. What an index cannot do is hold a *large* weight in a winner *before* it wins. Nothing else can either, without prediction.
2. **The evidence does not support adding a live satellite at A$5,000.** The recommendation is **no live satellite sleeve**; one paper-only card (H14) so the idea is tested once, properly; and a reporting change so the owner can see the winners he already holds.
3. **Momentum is the only systematic "own the winners" method with real evidence, and the evidence is weaker than its reputation.** Global long-short evidence is strong before publication; it has decayed since; Australian evidence is mixed; the one Australian momentum ETF (MTUM) is 27 months old and trailed VAS by about 11 points in the last year.
4. **Thematic and sector ETFs are the wrong tool.** The academic and Morningstar evidence says they are launched after the run-up and lose afterwards. The ETF that holds NXT at 8–10% (ATEC) returned −1.4% a year over five years while VAS returned +9.0%.
5. **Direct stock momentum is not feasible below about A$50,000.** At A$5,000 commission alone costs 2.6–5.3% of the book a year.
6. **Falls do not predict the timing of gains.** Average returns after large index falls are somewhat above normal, but one third of Australian −20% episodes kept falling for another year, recoveries have taken from 5 months to 7 years in the US (longer for the ASX 200 after 2007, a figure I could not confirm), and 196 tested buy-the-dip rules on the S&P 500 did slightly worse than buy-and-hold. At stock level about half of stocks never regain their prior peak.
7. **The spec's own bar decides it.** A return claim needs t ≥ 3.0 and DSR ≥ 0.95 (VAL-20). A 10% tilt cannot reach that on the available history even if the premium is real (section 6.3). Under the owner's own rules the honest result is "not passed", and the rule is not promoted.

---

## 1. Claim table

| # | Claim | Tag | Sources |
|---|---|---|---|
| **Skew and indexing** | | | |
| C1 | US, 1926–2016: most stocks had lifetime returns below one-month Treasury bills; "the best-performing 4% of listed companies explain the net gain for the entire US stock market". | [2+] | S1 abstract; S2 |
| C2 | Global, 1990–2020, 64,000 stocks: 55.2% of US and 57.4% of non-US stocks underperformed bills; "the top-performing 2.4% of firms account for all of the $US 75.7 trillion in net global stock market wealth creation"; outside the US, 1.41% of firms. | [2+] | S3 abstract; S4 |
| C3 | The author's stated implication: the results "help to explain why poorly diversified active strategies most often underperform market averages". | [1] | S1 abstract |
| C4 | No Australian replication of the Bessembinder study was found. The non-US figure (C2) includes Australia but is not broken out. | [unverified] | search returned none |
| C5 | NXT listed December 2010 at A$1.00, raising A$40m. | [2+] | S5, S6 |
| C6 | NXT joined the S&P/ASX 200 in September 2016, the ASX 100 in June 2020 and the ASX 50 on 21 September 2026. | [1] for 2016 and 2020; [2+] for 2026 | S7, S8, S9 |
| C7 | NXT is about 0.29–0.4% of VAS. | [1] each, two aggregators that disagree; treat as "about a third of one per cent" | S10 |
| C8 | The date NXT entered the S&P/ASX 300 (and so VAS) is not confirmed. It must be on or before September 2016. | [unverified] | — |
| **Momentum** | | | |
| C9 | Buying past winners and selling past losers earned "significant positive returns over three- to twelve-month holding periods" in US data 1965–1989; part of the gain "dissipates in the following two years". | [2+] | S11 abstract; S12 |
| C10 | Momentum "has offered investors the highest Sharpe ratio" of the standard factors and "has also had the worst crashes". | [2+] | S13 abstract; S14 abstract |
| C11 | Momentum crashes "occur in panic states, following market declines and when market volatility is high, and are contemporaneous with market rebounds". March–May 2009: past-loser decile +163%, past-winner decile +8%. | [2+] mechanism; [1] the 163/8 figures | S14 abstract; S15 |
| C12 | The long-short momentum factor lost about 73% in three months in 2009 and about 91% in two months in 1932. | [1] | S16 (secondary summaries of S13) |
| C13 | Across 97 published predictors, returns are "26% lower out-of-sample and 58% lower post-publication". | [2+] | S17, S18 |
| C14 | US momentum profits "have become insignificant since the late 1990s" (1965–2012 study). A defender puts the 1994–2015 long-short premium at 5.5% a year, smaller than before. Both agree it shrank; they disagree on whether it is gone. | [2+] that it declined; contested whether it survives | S19; S20 |
| C15 | Costs: "Most anomalies with less than 50% turnover per month generate significant net spreads when designed to mitigate transaction costs; few with higher turnover do." The best mitigation is "a buy/hold spread" (stricter rule to enter than to stay). | [1] | S21 abstract |
| C16 | Institutional-cost study: momentum costs about 48 bp a month to trade against 5–6 bp for size and value, and still nets positive; capacity is small. Institutional costs, not retail. | [1] | S22 (secondary) |
| C17 | About half the long-short premium comes from the long side. | [1] | S23 (secondary; AQR is a momentum-fund vendor) |
| C18 | MSCI World Momentum 12.3% a year against MSCI World 9.58%, May 1973–May 2018, gross, USD; most of that window is index back-history, not live. | [1] | S24 |
| C19 | Australia: mixed. Four published studies find momentum in ASX 200 or large stocks; spreads reduce it; mining names damage it; one working paper finds none since the late 1970s once delisting foresight is removed; one study finds none in ASX 200 weekly data 1997–2006. | [2+] that the evidence is mixed | Report 12 #13–#19; S25 |
| C20 | Australia 1883–1984: momentum profitable, and positive in January, unlike the US. | [1] | S26 abstract |
| C21 | Australian momentum crashes: they follow steep market falls and come from large gains in past losers, as in the US. Authors and journal not identified. | [1] | S27 |
| C22 | Australian momentum (ASX 200, 2000–2013) was hurt in the GFC but "not persistently"; capacity is material. | [1] | Report 12 #19 |
| C23 | Live Australian momentum ETF: MTUM returned −7.34% in the year to 30 October 2026 against VAS +3.93%; −4.03% in October alone against VAS +1.57%. | [1] primary | S28 |
| C24 | Live global momentum ETF: GTUM returned −12.20% in October 2026 against VGS −1.54%. | [1] primary | S28 |
| C25 | MTUM's index back-test claims +2.8% a year over the S&P/ASX 200, May 2011–June 2024. It is a back-test published by the issuer at launch. | [1], issuer back-test | S29 |
| **Thematic funds** | | | |
| C26 | "Over their first 5 years, specialized ETFs lose about 30% (risk-adjusted). This underperformance cannot be explained by high fees or hedging demand. Rather, it is driven by the overvaluation of the underlying stocks at the time of the launch." | [2+] | S30 abstract; S31 |
| C27 | Providers cater "to investors' extrapolative beliefs by issuing specialized ETFs that track attention-grabbing themes". | [2+] | S30 abstract; S31 |
| C28 | Morningstar 2024: 9% of thematic funds survived and beat a global index over 15 years to mid-2024; about 60% closed. The 2021 edition gave 22% and 57%. | [1] originating source (several republications); editions differ | S32 |
| C29 | Morningstar: over five years thematic funds returned 7.3% a year while their investors earned 2.4%, because money arrived late. | [1] | S33 |
| C30 | ATEC (Australian technology index fund; NXT weight 8.4–9.7%) returned −28.55% over one year and −1.43% a year over five years to October 2026; VAS returned +3.93% and +8.95%. | [1] primary for returns; [2+] for NXT being a top holding | S28; S34 |
| C31 | Over five years to October 2026 every Australian small-cap, mid-cap, ex-20 and technology ETF on the ASX trailed VAS: MVE 6.72%, VSO 5.39%, SMLL 5.36%, EX20 5.09%, MVS 1.54%, ISO 0.57%, ATEC −1.43%, against VAS 8.95%. | [1] primary; [computed] comparison | S28 |
| C32 | Global thematic ETFs on the ASX ranged from −10.4% to +33.0% a year over the same five years (CRYP, SEMI), against VGS 12.37%. | [1] primary | S28 |
| **Falls and recoveries (section 7)** | | | |
| C33 | Equity-premium predictors "have predicted poorly both in-sample and out-of-sample for 30 years" and "would not have helped an investor … to profitably time the market". The 2024 re-test of 46 variables: a third of the newer ones fail in-sample, half the rest fail out-of-sample, "a small number … still perform reasonably well". | [2+] | S35, S36 abstracts |
| C34 | Long-horizon mean reversion: 1926–85, "predictable price variation due to mean reversion accounts for large fractions of 3 to 5-year return variances" (about 25% for large firms, 40% for small). | [2+] with Poterba–Summers | S37 abstract; S38 |
| C35 | Re-examination: "mean reversion is entirely a pre-war phenomenon"; a later paper says earlier work "overstates the evidence" because the Depression and war years dominate. | [2+] | S39 abstract; S40 |
| C36 | CAPE explains roughly 30–40% of the variation in 10-year real returns and is not usable for short-horizon timing; AQR's own conclusion is to "sin a little" at most. | [2+] direction; [1] each number | S41, S42 |
| C37 | S&P 500 since 1950, bought when the index was 10%, 20% or 30% below its high at a month-end: about +15%, +17%, +21% over the next year, against roughly 12% unconditionally; win rate above 70%. | [1] (secondary summary of one blog study) | S43 |
| C38 | US market 1926–2022: three-year gains above 30% after declines of 10% and 20%, "not as impressive" after 30%. This contradicts the neat "deeper fall, bigger gain" ordering in C37. | [1] | S44 |
| C39 | Australia since 1900: 18 bear markets; in 12 the market was higher a year after first falling 20%, in 6 it kept falling over the next 12 months. Average total falls 26% and 46%. | [1] originating source (AMP), widely republished | S45 |
| C40 | Recovery of the prior peak has taken very different times: S&P 500 about 19 months after 1987; about 7 years after 2000; 2007 peak regained in 2013; about 5 months after the 2020 fall of 34% in 33 days; about 2 years after 2022. | [2+] for 2020; [1] for the others | S46 |
| C41 | April 2025: ASX fell 15.8% peak to trough "in a matter of days". The S&P 500 fell about 19% from 19 February to 8 April 2025 and made a new high in late June 2025. | [1] for the ASX figure; [unverified] (model memory) for the S&P dates | S47 |
| C42 | Australian index recoveries: All Ordinaries about −50% in late 1987; S&P/ASX 200 about −54% from November 2007 to March 2009 with the price peak regained only in 2019; about −37% in February–March 2020. | [1] for 2020 depth; [unverified] (model memory) for 1987, the GFC depth and the 2019 date | S48 |
| C43 | AQR "Hold the Dip" (December 2025): 196 buy-the-dip rules on the S&P 500, 1965–September 2025. Average Sharpe ratio 0.04 below buy-and-hold; more than 60% of the rules were worse. In the four worst drawdowns since 2000 the average dip rule lost 18.4% while trend-following gained 28.6%. | [2+] for the headline (two secondary summaries agree); [1] for the drawdown comparison. AQR sells trend funds. | S49, S50 |
| C44 | Why it fails: buy-the-dip "is usually positioned opposite momentum"; contrarian timing fights the shorter-term momentum effect. | [2+] | S49, S42 |
| C45 | Volatility-managed portfolios (cut exposure when volatility is high, i.e. after falls): positive in-sample alphas, but they "do not systematically outperform" and "reasonable out-of-sample versions generally earn lower certainty equivalent returns and Sharpe ratios" (103 strategies). | [2+] | S51 abstract; S52 |
| C46 | Faster trend signals do not fix late re-entry: "Faster trend signals… rather than solving the problem, increase the tendency of placing bad bets." Trend rules re-entered late after the 2020 V-shape. No rigorous study of an asymmetric (fast re-entry, slow exit) rule on equity indices was found. | [1] for the quote (report 14 #10); [2+] practitioner for 2020; [unverified] that no study exists | Report 14 #10; S53 |
| C47 | Individual stocks, US 1985–2024, 6,500 firms: median maximum drawdown about 85%; about 54% never returned to the prior peak; of stocks that fell 95–100%, about one in six did. The study excludes stocks that went to zero. | [2+] (several summaries of one originating study) | S54 |
| C48 | Russell 3000, 1980–2014: about 40% of stocks suffered a 70%+ fall from peak that was not recovered; 57% in technology; two thirds underperformed the index. | [2+] (summaries of one originating study) | S55 |
| C49 | Financially distressed stocks "have delivered anomalously low returns" since 1981, with much higher volatility and beta. | [1] abstract | S56 |
| C50 | Lottery-like stocks (highest recent daily spike) underperform by more than 1% a month. | [1] abstract | S57 |
| C51 | Long-term reversal: past 3–5 year losers beat winners by about 25% over the next three years (De Bondt–Thaler). Later work ties it to January, small and low-priced stocks and tax effects, and finds no reversal when strength is measured by nearness to the 52-week high. | [1] each; the effect is contested | S58 |
| **Costs and tax** | | | |
| C52 | IBKR fixed: max(A$6.60, 0.088%) per order including GST; the percentage takes over at A$7,500. | spec RND-021 | FD_FINAL.md |
| C53 | Parcels held under 12 months get no 50% discount before 1 July 2027 and no indexation after it; a 30% minimum tax applies to post-July 2027 capital gains. | [2+] / [1] as tagged in report 18 | Report 18 |

---

## 2. Positive skew: what "not missing NEXTDC" actually requires

**The fact.** A few stocks produce all of the market's excess return (C1, C2). The owner's instinct is right about the phenomenon.

**The implication runs the other way from stock-picking.**

- If 2.4% of firms make all the money, a portfolio of 10 randomly chosen stocks will usually hold none of them. A portfolio of all of them always holds all of them. Bessembinder's own conclusion is that skew explains why concentrated strategies "most often underperform" (C3).
- A cap-weighted index is a zero-turnover "let winners run" rule. NXT's weight in VAS grew from nothing to about a third of a per cent as the price rose, with no order and no CGT event. [unverified] as a description of weight history; the mechanism is arithmetic.
- VAS tracks the S&P/ASX 300, so it reaches down to roughly the 300th company. NXT was in the index family by September 2016 at the latest (C6, C8).

**What the index did not give.** Honest limits:

- NXT's gain from the A$1.00 float to index entry was earned outside the index. No liquid rule-based product would have held it then either; an ASX 200 momentum screen cannot buy a stock that is not yet in the ASX 200.
- At 0.3–0.4% of VAS and VAS at 40% of the account, look-through NXT exposure is about 0.12–0.16% of the account, or A$6–8 on A$5,000 [computed]. If NXT went up ten times, the account would gain about 1.1–1.4% from it [computed]. Owning a winner and owning enough of it to matter are different things.
- Closing that gap means overweighting future winners before they win. That is prediction. The only rule-based predictor with a research record is momentum (section 3).

**Decision.** D1 below: state in the spec that "not missing a winner" is met by the core, and report it (D7).

---

## 3. Cross-sectional momentum

### 3.1 What the evidence supports

- **It existed, broadly.** US (C9), many countries and asset classes (C10, C14 context), Australia in older data (C20). [2+]
- **Its headline numbers are long-short and gross.** A retail long-only holder gets roughly the long half (C17, [1]) and pays costs and tax on high turnover.
- **It decayed after publication.** The general result is a 58% fall (C13, [2+]). For momentum specifically, one study finds it insignificant in the US since the late 1990s and a defender still concedes a smaller premium (C14). The spec's VAL-26 already halves published edges.
- **It crashes, and it crashes in rebounds.** The 2009 loss was about 73% in three months for the long-short factor (C12, [1]). The mechanism (C11, [2+]) matters for section 7: momentum's worst months are the months the market bounces off a low.
- **A long-only holder does not suffer the 73%.** That figure is the short side exploding. The long-only cost of a momentum crash is lagging the index in the rebound. October 2026 is a small live example: MTUM −4.0% against VAS +1.6%; GTUM −12.2% against VGS −1.5% (C23, C24).

### 3.2 Australia

- Report 12 concluded "more evidence for than against" in large caps, with spreads, mining names and survivorship as the known problems (C19).
- New in this report: momentum crashes are documented in Australian data too (C21, [1]); the pre-1984 evidence is positive (C20, [1]); and the first live Australian momentum ETF has had a poor year (C23).
- **No Australian study reports a net-of-cost, after-tax, long-only momentum return for a small investor.** [unverified] that none exists; none was found here or in report 12.

### 3.3 Magnitude a small investor could plausibly expect

| Step | Figure | Tag |
|---|---|---|
| Long-only momentum index over its parent, long history | about 2.7 points a year (C18) | [1], mostly back-history |
| After the spec's haircut (VAL-26: halve it) | about 1.35 points | [computed] |
| Less extra fee (MTUM 0.35% against VAS 0.07%) | about 1.1 points on the sleeve | [computed] |
| At a 10% sleeve | about 0.11 points a year on the account | [computed] |
| In dollars at A$5,000 | about A$5 a year, before any commission | [computed] |
| One IBKR order | A$6.60 | spec |

The expected gain from a 10% momentum tilt at A$5,000 is smaller than one commission. That is the central number in this report.

### 3.4 Turnover

- Index products hide turnover inside the fund, but it still costs: trading inside the fund and distributed capital gains. MTUM's fee is 0.35%; its internal turnover figure was not obtainable (issuer and index-provider pages blocked). [unverified]
- For a direct portfolio, the cost literature's one practical lesson is the buy/hold spread: a stricter rule to enter than to stay (C15). Cards H14 and H15 use it.

---

## 4. ASX-listed vehicles

All figures are from the ASX Investment Products report for October 2026 (period ending 30 October 2026) unless noted: MER, funds under management, time-weighted average spread, total returns. "History" is a bound I derived from which return columns the report fills: a 5-year figure means listed before November 2021; 3-year only, between November 2021 and October 2023; 1-year only, between November 2023 and October 2025; none, after October 2025. Exact inception dates in brackets are from search excerpts or memory and are tagged.

**Existence.** Every ticker below appears in the ASX report, so each exists and is quoted on the ASX. [1] primary. IMTM is the exception: it is quoted on Cboe Australia, not the ASX, and is not in the report.

### 4.1 Core, for comparison

| Ticker | Fund | MER | FUM A$m | Spread | 1y | 3y p.a. | 5y p.a. |
|---|---|---|---|---|---|---|---|
| VAS | Vanguard Australian Shares | 0.07% | 26,993 | 0.02% | 3.93% | 14.33% | 8.95% |
| VGS | Vanguard MSCI International | 0.18% | 18,630 | 0.02% | 4.64% | 18.84% | 12.37% |

### 4.2 Momentum

| Ticker | Fund | MER | FUM A$m | Spread | 1y | 3y | 5y | History | Index method | Fee tag |
|---|---|---|---|---|---|---|---|---|---|---|
| MTUM | Betashares Australian Momentum | 0.35% | 272 | 0.07% | −7.34% | n/a | n/a | Listed 24 July 2024 [2+]; 27 months | Solactive Australia Momentum Select: Solactive Australia 200 universe ranked on 6- and 12-month risk-adjusted return [1]. Constituent count and rebalance frequency not confirmed [unverified] | [2+] |
| GTUM | Betashares Global Momentum | 0.35% | 213 | 0.16% | n/a | n/a | n/a | Listed 30 January 2026 [2+]; 9 months. −12.20% in October 2026 | Solactive Developed Markets ex Australia Momentum Select; same risk-adjusted method; a two-monthly rebalance is reported for this index [1] | [2+] |
| IMTM | iShares MSCI World ex Australia Momentum | 0.25% | not in ASX report | not in ASX report | — | — | — | Listed February 2024 (14–16 Feb, sources differ) [2+] | MSCI World ex Australia Momentum; 6- and 12-month price strength. **Quoted on Cboe Australia.** Whether IBKR Australia routes to Cboe-quoted funds is [unverified] | [2+] |

- **History length is the binding problem.** None has three years. VAL-24 needs 15 years of daily data covering 2008, 2020 and 2022. MTUM's index back-history starts May 2011 (C25) and misses 2008. Only an MSCI momentum index (history to 1973/1994, C18) covers the required period, and that data is licensed.
- The ASX report lists GTUM under type "Active"; the issuer describes it as index-tracking. Unresolved. [unverified]

### 4.3 Australian technology, mid and small caps (where a "next NEXTDC" would sit)

| Ticker | Fund | MER | FUM A$m | Spread | 1y | 3y p.a. | 5y p.a. | History |
|---|---|---|---|---|---|---|---|---|
| ATEC | Betashares S&P/ASX Australian Technology | 0.48% | 558 | 0.10% | −28.55% | 7.89% | −1.43% | 5y+ (2020 [unverified]) |
| MVE | VanEck S&P/ASX MidCap (ASX 51–100) | 0.45% | 502 | 0.06% | −2.68% | 13.54% | 6.72% | 5y+ (2013 [unverified]) |
| VSO | Vanguard MSCI Australian Small Companies | 0.30% | 1,172 | 0.08% | −4.62% | 13.97% | 5.39% | 5y+ (2011 [unverified]) |
| SMLL | Betashares Australian Small Companies Select | 0.39% | 366 | 0.40% | −0.88% | 16.12% | 5.36% | 5y+ |
| MVS | VanEck Small Companies Masters | 0.49% | 171 | 0.18% | −11.60% | 10.02% | 1.54% | 5y+ |
| ISO | iShares S&P/ASX Small Ordinaries | 0.55% | 123 | 0.32% | −14.45% | 9.61% | 0.57% | 5y+ |
| EX20 | Betashares Australian Ex-20 | 0.25% | 674 | 0.10% | −5.59% | 11.42% | 5.09% | 5y+ |

- **All seven trailed VAS over five years** (C31). Fees [1] primary except ATEC [2+].
- **ATEC is the instructive case.** NXT is a top-four holding at 8.4–9.7% (C30). The fund still lost money over five years because the other 90% is the same sector bet. Owning the theme did not capture the winner's return.
- **NXT has left the mid-cap index.** MVE tracks the ASX 51–100; NXT moved to the ASX 50 in September 2026 (C6). A mid-cap fund sells its biggest winners by construction. [computed from index rules; unverified against the VanEck methodology]
- VAS already holds everything in MVE, VSO's large end, and ATEC's index members that are in the ASX 300, at market weight.

### 4.4 Global technology, AI and data-centre themes

| Ticker | Fund | MER | FUM A$m | Spread | 1y | 3y p.a. | 5y p.a. | History | Fee tag |
|---|---|---|---|---|---|---|---|---|---|
| AINF | Global X AI Infrastructure (power, data-centre infrastructure, materials; Mirae Asset AI Infrastructure Index) | 0.57% | 185 | 0.18% | 4.51% | n/a | n/a | Launched about April 2025 [1] | [2+] |
| GXAI | Global X Artificial Intelligence | 0.57% | 269 | 0.14% | 7.10% | n/a | n/a | 1–3y | [1] |
| RBTZ | Betashares Global Robotics and AI | 0.57% | 268 | 0.16% | −17.94% | 9.87% | −1.01% | 5y+ | [1] |
| SEMI | Global X Semiconductor | 0.45% | 953 | 0.07% | 50.76% | 54.19% | 33.04% | 5y+ | [2+] |
| NDQ | Betashares NASDAQ 100 | 0.48% | 9,036 | 0.03% | 3.28% | 22.42% | 14.79% | 5y+ | [2+] |
| FANG | Global X FANG+ | 0.35% | 1,601 | 0.05% | −4.33% | 30.19% | 19.71% | 5y+ | [2+] |
| HACK | Betashares Global Cybersecurity | 0.67% | 1,724 | 0.09% | 26.97% | 29.39% | 16.28% | 5y+ | [1] |
| CLDD | Betashares Cloud Computing | 0.67% | 41 | 0.29% | 12.23% | 13.78% | −0.12% | 5y+ | [1] |
| TECH | Global X Morningstar Global Technology | 0.45% | 341 | 0.20% | 17.31% | 21.09% | 10.18% | 5y+ | [1] |
| VTEK | Vanguard Global Technology Index | 0.23% | 83 | 0.12% | n/a | n/a | n/a | Under 1y | [1] |

- **There is no ASX-listed pure data-centre ETF.** The nearest is AINF, where data centres are one of three sub-themes. The pure products (DTCR on Nasdaq, RACK on Cboe US) are US-listed and excluded for this account by MKT-02. [1]
- **Five-year results run from −1% to +33% a year** against VGS at 12.4%. Picking the theme is stock-picking one level up.
- **October 2026 alone:** SEMI −13.65%, AINF −10.50%, FANG −7.85%, NDQ −5.59%, against VGS −1.54%. [1] primary. These are concentrated, high-beta sleeves.
- VGS already holds the large global data-centre, chip and cloud companies at market weight. [unverified]; I could not open the VGS holdings file.

### 4.5 Quality and growth

| Ticker | Fund | MER | FUM A$m | Spread | 1y | 3y p.a. | 5y p.a. | Fee tag |
|---|---|---|---|---|---|---|---|---|
| QUAL | VanEck MSCI International Quality | 0.40% | 9,103 | 0.03% | 4.33% | 16.49% | 11.65% | [2+] |
| QLTY | Betashares Global Quality Leaders | 0.35% | 1,054 | 0.10% | 4.39% | 15.35% | 9.27% | [2+] |
| AQLT | Betashares Australian Quality | 0.35% | 1,627 | 0.05% | 10.50% | 22.44% | n/a | [1] |
| MOAT | VanEck Morningstar Wide Moat | 0.49% | 877 | 0.09% | 4.82% | 13.53% | 10.77% | [1] |
| GWTH | VanEck MSCI International Growth | 0.40% | 14 | 0.57% | −10.14% | n/a | n/a | [1] |
| GARP | Global X S&P World ex Australia GARP | 0.30% | 124 | 0.15% | 0.02% | n/a | n/a | [1] |
| HYGG | Hyperion Global Growth (active) | 0.70% | 3,137 | 0.24% | −15.52% | 19.38% | 6.94% | [1] |

- Quality is a different factor from "big winners". It is listed because the owner asked. None of the global quality or growth funds beat VGS over five years; AQLT has beaten VAS over three. [1] primary
- GWTH at A$14m with a 0.57% spread is not investable at the spec's cost assumptions.

### 4.6 Liquidity screen against the spec

RND-021 assumes a 10 bp half-spread for thin ETFs. Reported full spreads above 0.20% fail that assumption: SMLL, ISO, CLDD, GWTH, HYGG, TECH (at the limit). MTUM at 0.07% and GTUM at 0.16% pass. [computed]

---

## 5. Direct stock momentum at A$5,000 to A$50,000

### 5.1 How many holdings

- The skew results (C1, C2) are the argument for many holdings: with few names, the chance of holding a top-2% stock is small, and half of all stocks never regain their peak (C47).
- Academic momentum portfolios hold a decile or more: 20 names from the ASX 200, 30 from the ASX 300. MTUM's count was not confirmed. [unverified]
- A practical floor for a rule that claims to be "momentum" and not "five stocks I like" is about 10 names; 20 is closer to the research. [unverified], judgment

### 5.2 Commission and spread drag

Assumptions: commission max(A$6.60, 0.088%) per order (C52); half-spread 10 bp per side for ASX 200 names [unverified]; "turnover" is the share of names replaced per year; each replacement is one sell and one buy. All figures [computed].

| Account in the strategy | Names | Position | Turnover 100% a year | Turnover 200% a year | Meets A$1,000 minimum order? |
|---|---|---|---|---|---|
| A$5,000 | 10 | A$500 | 2.8% a year | 5.7% a year | No |
| A$5,000 | 5 | A$1,000 | 1.5% | 3.0% | Yes, but 5 names is not a momentum portfolio |
| A$20,000 | 10 | A$2,000 | 0.9% | 1.7% | Yes |
| A$50,000 | 20 | A$2,500 | 0.7% | 1.5% | Yes |
| A$50,000 | 10 | A$5,000 | 0.5% | 0.9% | Yes |

- Published monthly-rebalanced momentum turns over well above 200% a year; the 100% column needs a 12-month hold or a wide buy/hold buffer. [unverified]
- Against a haircut expectation of about 1.35 points (section 3.3), the strategy is under water on commission alone below A$20,000 and marginal at A$50,000.
- These figures are for the whole account in the strategy. As a satellite capped at 10% (D6) the same position count needs an account ten times larger: **a 10-name satellite meets the A$1,000 minimum order only from about A$100,000** (10 × A$1,000 ÷ 0.10). [computed]

### 5.3 Tax

- **Before 1 July 2027:** a momentum holding sold inside 12 months gets no 50% discount (C53). At a 32% marginal rate (30% plus Medicare) the gain is taxed at 32% against 16% for a discounted gain. On a 10% realised gain that is about 1.6 points a year of extra tax. [computed]
- **From 1 July 2027:** the discount goes for everyone. The penalty for short holding shrinks to (a) no indexation, worth roughly inflation × the marginal rate, about 0.8–1.0 point a year at 2.5–3% inflation, and (b) loss of deferral. For a holder with a marginal rate under 30% the 30% minimum tax applies to these gains. [computed; unverified reading, see report 18's open questions for the tax agent]
- **Trader risk.** Frequent, systematic share turnover moves toward the revenue-account boundary that report 18 flags. More names and more trades make that worse than the two-ETF core. [unverified]
- **Franking.** Holdings rotated inside 45 days lose franking credits once total credits exceed A$5,000 (report 12 #12); irrelevant at A$5,000, relevant later.
- **Records.** 20 names with corporate actions, against two ETFs. The spec has no corporate-action engine for shares (section 7 is withdrawn).

### 5.4 Verdict

Not feasible at A$5,000. Not worth it below about A$50,000 as a whole-account strategy or about A$100,000 as a satellite. The spec's D3 ("No single shares") stands, now with a cost table behind it. Card H15 is written so the question can be tested in paper when the account is large enough; it is not recommended for registration now.

---

## 6. Recommendation

### 6.1 Decisions (spec-ready)

| # | Decision | Basis |
|---|---|---|
| D1 | **No live satellite sleeve at A$5,000.** The live universe stays VAS 40% / VGS 60%. Add to the decision log: "The requirement not to miss big winners is met by the cap-weighted core, which holds every S&P/ASX 300 and MSCI World ex-Australia constituent." | C1–C3, C7; section 3.3; spec D3, D16 |
| D2 | **No thematic, sector, technology, AI or data-centre ETF, live or paper, and no card for one.** A card spends a trial and the prior evidence is negative. | C26–C32 |
| D3 | **No small-cap or mid-cap ETF as a "winner-catcher".** VAS already holds the ASX 300; the mid-cap fund sells its winners on promotion; all such funds trailed VAS over five years. | C31; section 4.3 |
| D4 | **Momentum is admitted to paper only, through card H14, in a new strategy family `S1`.** The vehicle, if it ever passes, is MTUM carved 10% out of the VAS sleeve. It is not eligible for live until H14 passes at Family B thresholds, H12 (haircut) passes, sizing NAV is at least A$20,000, and 6 paper cycles are complete. | C9–C25; VAL-20, VAL-24, RND-032 |
| D5 | **Direct single-stock momentum stays out (D3 unchanged).** Card H15 is drafted and held unregistered until sizing NAV is at least A$100,000 and the spec has a share corporate-action engine. | Section 5 |
| D6 | **Hard cap on any future satellite: 10% of sizing NAV at target, 12% hard limit, one vehicle, funded from contributions only.** | Section 6.4 |
| D7 | **Add a "winners you already own" block to the monthly digest**: look-through weight and 12-month contribution of the top 10 contributors in each core ETF, and the look-through weight of any stock on a user watch-list (NXT). Reporting only; no order path. | Section 2; behavioural |
| D8 | **Satellite return claims are Family B.** A tilt whose purpose is higher return cannot be registered as a Family A design choice. | RND-001 |

### 6.2 Why not, in the owner's terms

- **The wish is already met.** He holds NXT now and will hold the next one from the day it enters the ASX 300.
- **The wish was formed after the run.** NXT is named because it has already risen. That is the exact pattern the thematic-ETF research describes: products and enthusiasm arrive after the gains (C26–C29). This is said with respect; it is what the evidence on investors in general shows.
- **The numbers are too small to matter at this size.** About A$5 a year of expected gain against A$6.60 an order (section 3.3).
- **The risk is not small.** A 10% sleeve that lags the core by 11 points, as MTUM did last year, costs 1.1% of the account [computed].
- **His own validation rule forbids it.** See 6.3.

### 6.3 Can the card pass? Power arithmetic

- The spec's own approximation: t ≈ Sharpe difference × √years; t = 3 on 34 years needs a Sharpe difference of about 0.51 (section 24).
- For a sleeve test (momentum portfolio against its parent index) the equivalent is the information ratio. Take a true premium of 2 points and a tracking error of 8 points: information ratio 0.25. On the 24 years of point-in-time ASX 200 data that H14 can use, t ≈ 0.25 × √24 ≈ 1.2. [computed; inputs unverified]
- To reach t = 3 on 24 years the information ratio must be about 0.61. Long-only momentum indices do not show that after costs. [unverified]
- **Expected result of H14: "not passed".** The card is still worth one trial because it closes the question on the record, by the owner's own process, and stops it being reopened informally each time a stock runs.

### 6.4 If a satellite were ever promoted: how it would fit the spec

Not for build. This is the shape the spec change would take if H14 passed.

```yaml
# config/common.yaml — family S1. Disabled in every release until H14 = passed with an owner approval record.
satellite:
  enabled: false
  mode: paper_sim               # RND-032: challengers run in paper_sim, not the IBKR paper account
  symbol: MTUM
  carve_from: VAS               # VAS base weight becomes 0.30 while enabled; VGS stays 0.60
  base_weight: 0.10
  hard_max_weight: 0.12         # RSK-13 style ceiling: reject buys that increase a breach
  min_sizing_nav_aud: 20000     # 0.10 x 20,000 = 2 x min_order_value_aud; matches Stage 2 entry (section 27)
  state_source: VAS             # no votes of its own; ON/OFF follows the VAS sleeve's tranche state
  fund_from: contributions_only # RND-033; never sell VAS to fund the satellite
  band_relative: 0.20           # same band as l1
  tranches: 1
```

- **Trend filter.** The satellite takes the VAS sleeve's state. No new signal, no new parameter, no extra trial. When VAS turns OFF, both are sold: one extra order per transition, A$6.60, which is 0.33% of a A$2,000 sleeve per leg [computed].
- **Known bad interaction.** Momentum lags most in rebounds (C11). L1 re-enters at ≥ 2 votes, which is after a rebound has started, so the satellite is bought when a momentum portfolio is most likely to be holding the previous regime's winners. H14 must report the 12 months after each OFF→ON transition separately. [unverified inference]
- **Minimum order.** Initial buy: 10% × NAV ≥ A$1,000 needs A$10,000; the A$20,000 floor keeps the order at twice the minimum. A band rebalance of a 10% sleeve is about 2% of NAV, below A$1,000 until NAV is about A$50,000, so in practice the sleeve is kept on weight by contributions only (PRT-16(b)) and band trades are skipped (`BAND`). [computed]
- **Tranching.** N = 1. Three tranches of a A$2,000 sleeve are A$667 each, below the minimum (same arithmetic as C4 in the change log). Entry is one order.
- **OPS-12** would add: validation fails if `satellite.enabled` and H14 is not `passed`, or sizing NAV is below `min_sizing_nav_aud`, or 0.10 × sizing NAV is below `min_order_value_aud`.
- **Stage table.** A new row between Stage 1 and Stage 2, or folded into Stage 2: "S1 momentum tilt: H14, H12 passed; 6 paper cycles; sizing NAV ≥ A$20,000".

### 6.5 Cost and risk if the owner overrode this at A$5,000

For the record, not a recommendation. A 10% MTUM sleeve is A$500, half the minimum order, so it needs a spec exception.

| Item | Amount | Tag |
|---|---|---|
| Entry commission | A$6.60 = 1.3% of the sleeve | [computed] |
| Extra fee | 0.28% × A$500 = A$1.40 a year | [computed] |
| One trend round trip a year | A$13.20 = 2.6% of the sleeve, 0.26% of the account | [computed] |
| Expected gain after haircut, already net of the extra fee | about A$5 a year | [computed], section 3.3 |
| Net expectation with one trend round trip a year | negative: about −A$8 a year, before the entry commission | [computed] |
| One-year relative risk, sleeve lags by 11 points | −A$55, 1.1% of the account | [computed] from C23 |
| At 20% (A$1,000, meets the minimum) | VAS core falls to A$1,000; every figure doubles; expectation still negative | [computed] |

### 6.6 Hypothesis cards (RND-010 format)

IDs continue from H13. Dates and hashes are set at `trader hypothesis freeze`.

#### Card H14 — Australian momentum tilt (family S1, paper)

| Field | Content |
|---|---|
| ID | H14 |
| Date registered | set at freeze |
| Card hash | set at freeze |
| Economic rationale | Written before data: investors under-react to news and then herd, so 6–12 month winners keep outperforming for some months (C9). Counter-rationale recorded with it: the effect is published, has decayed (C13, C14), crashes in rebounds (C11), and Australian evidence is mixed (C19). |
| Exact rule | Universe: point-in-time S&P/ASX 200 constituents, including later-delisted names. Score: mean of 6-month and 12-month total return, each skipping the most recent month, each divided by the stock's 12-month daily volatility. Hold the top 30 by score, weighted by float market cap, single-name cap 10%. Review at the last trading day of May and November. A held stock stays while its rank is ≤ 45 (buy/hold spread, C15). Portfolio under test: 30% VAS proxy + 10% this portfolio + 60% VGS proxy, under L1 with the momentum leg taking the VAS sleeve's state. |
| Fixed parameters | Lookbacks 6 and 12 months, skip 1 month; 30 names; exit rank 45; semi-annual review; 10% cap; sleeve weight 10%; modelled fund fee 0.35% a year on the momentum leg. |
| Permitted perturbation grid | Lookback {12 only}; names {20, 40}; review {quarterly}; exit rank {30, 60}. Six neighbours, each a logged trial. Reported, not a grid: results with and without GICS Materials (report 12, decision 8). |
| Data and proxy map | Licensed point-in-time ASX 200 constituents and daily total returns (RND-029 `rental/` tree). VAS and VGS proxies as RND-024. Splice check: tracking error of the self-built portfolio against MTUM from 24 July 2024, daily, reported; if annualised tracking error exceeds 4 points the card result does not transfer to MTUM and no vehicle is approved. |
| Sample and holdout dates | Development: first date with point-in-time constituents (about 2000) to 2023-12. Holdout: 2024-01 onward, opened once for family S1. If fewer than 15 years of daily data covering 2008, 2020 and 2022 are available: result "not testable" (VAL-24). |
| Benchmark | L1 on 40% VAS / 60% VGS, same costs and tax. |
| Primary metric (exactly one) | Net-of-cost, after-tax annualised return difference, portfolio under test minus benchmark. |
| Secondary metrics | Maximum drawdown difference; tracking error; return in the 12 months after each OFF→ON transition; return in the three worst momentum months; turnover; distributed capital gains; result at A$20,000, A$50,000, A$250,000; result under both CGT regimes (RND-022). |
| Pass threshold | t ≥ 3.0 and DSR ≥ 0.95 with N = all S1 trials; and every VAL-24 condition; and still positive after H12 (benefit halved, costs doubled, one-month delay); and maximum drawdown no more than 2 points worse than the benchmark. |
| Fail threshold | Return difference ≤ 0 after the H12 haircut; or maximum drawdown more than 4 points worse. Anything between pass and fail is "not passed" (RND-015). |
| Multiple-testing family and adjustment | Family B. Strategy family `S1`, new, cap 50 trials, own holdout lock. |
| Trials consumed | 7 if the full grid is run (1 + 6). |
| Result | — |
| Decision | Pass: 6 paper cycles in `paper_sim`, then owner decision with 7-day cooling-off (RND-005). Not passed or fail: stays in the registry; no sleeve; may not be re-run with changes (RND-015). |
| Approver | Owner |

#### Card H15 — Direct ASX stock momentum (family S1) — drafted, not for registration now

| Field | Content |
|---|---|
| ID | H15 |
| Date registered | not before sizing NAV ≥ A$100,000 and a share corporate-action engine exists |
| Card hash | — |
| Economic rationale | As H14. Added: holding the stocks directly removes the fund fee and gives control of parcel selection and holding period. Counter-rationale: retail commission, spreads, short-holding tax and concentration (section 5). |
| Exact rule | Universe: point-in-time S&P/ASX 100. Score: 12-month total return skipping the most recent month. Hold the top 10, equal weight. Monthly check on the last trading day; a holding is sold only when its rank falls below 30, or after 13 months if below rank 10 (so that most exits clear the 12-month line). Replacement is the highest-ranked stock not held. No rebalancing between names except on replacement. Whole shares; minimum order A$1,000. |
| Fixed parameters | 12-1 momentum; 10 names; exit rank 30; equal weight; monthly check. |
| Permitted perturbation grid | Names {20}; exit rank {20, 40}; universe {ASX 200}. Four neighbours. |
| Data and proxy map | As H14, plus dividends with franking, splits, consolidations, takeovers and delistings at last traded price. |
| Sample and holdout dates | As H14. |
| Benchmark | VAS proxy (S&P/ASX 300 accumulation less 0.07%), buy-and-hold, same contributions. |
| Primary metric (exactly one) | Net-of-cost, after-tax annualised return difference against the benchmark at a strategy size of A$50,000. |
| Secondary metrics | The same at A$5,000 and A$250,000; maximum drawdown; share of profit from the top 3 names; share of exits held over 12 months; tax paid under both regimes; number of orders a year. |
| Pass threshold | t ≥ 3.0 and DSR ≥ 0.95; every VAL-24 condition, including "none supplies more than 30% of profit"; positive after the H12 haircut. |
| Fail threshold | Cost plus tax drag exceeds the gross return difference at A$50,000; or maximum drawdown more than 1.25 × the benchmark's. |
| Multiple-testing family and adjustment | Family B, strategy family `S1`. |
| Trials consumed | 5 if the full grid is run. |
| Result / Decision / Approver | — / paper only on a pass / Owner |

---

## 7. "Look at the fall, then understand the gains… predict that"

### 7.1 Index level: do falls predict gains?

**Average forward returns after falls are somewhat above normal.**

- S&P 500 since 1950: about +15%, +17% and +21% in the year after being 10%, 20% and 30% down, against about 12% unconditionally (C37, [1]).
- A second study agrees on direction for 10% and 20% falls but finds returns after 30% falls "not as impressive" (C38, [1]). The two disagree on whether deeper is better.
- Both rest on a dozen or so independent episodes at the −20% level and fewer at −30%. Overlapping monthly observations make the sample look larger than it is. [unverified], my assessment

**The distribution is the problem, not the average.**

- Australia since 1900: of 18 falls of 20% or more, 12 were higher a year later and **6 kept falling for another 12 months**, ending with average total losses of 46% (C39, [1]). Buying at −20% was wrong one time in three, and badly wrong.
- Time to regain the prior peak has ranged from about 5 months (2020) to about 7 years (S&P after 2000) and, on a price basis, almost 12 years for the ASX 200 after 2007 (C40, C42; the last is [unverified]). Depth at the time of purchase did not tell these apart: at −20% in early 2008 and −20% in March 2020 the next year looked completely different.
- V and L shapes, from the sources: 1987 sharp fall, 19-month recovery in the US; 2000–02 long grind, 7 years; 2008–09 deep, 5.5 years in the US; 2020 V, 5 months; 2022 slow, about 2 years; April 2025 V, about 2 months in the US (C40, C41; April 2025 dates [unverified]).

**Long-horizon mean reversion is weak evidence.**

- Found in 1926–85 data (C34, [2+]); then shown to come entirely from the pre-war period (C35, [2+]). It is not a basis for a rule.

**Valuation predicts over a decade, not over a year.**

- CAPE explains a third or so of 10-year returns and nothing useful for timing (C36). The comprehensive tests of every published predictor conclude they "would not have helped an investor … to profitably time the market" (C33, [2+]).

**Verdict (a).** Expected returns are probably higher after large falls. The size is modest, the sample is small, and neither the timing nor the shape of the recovery is predictable from the fall.

### 7.2 Re-entry timing: can a rule beat the spec's trend re-entry?

- **Buy-the-dip, tested directly:** 196 rule variants over 60 years averaged a slightly lower Sharpe ratio than doing nothing, and most were worse (C43, [2+] for the headline). The stated reason is that dip-buying bets against momentum at exactly the horizon where momentum works (C44).
- **Caveat on that source.** AQR sells trend-following, and the paper compares dip-buying unfavourably with trend. The headline result is reported consistently by two independent summaries; the AQR page itself was blocked.
- **Trend re-entry has a real cost in V-shaped recoveries.** After March 2020 monthly trend rules bought back above their exit price. That is the known price of the overlay; the spec budgets for it (H2 allows up to 1.5 points a year of after-tax return given up).
- **Faster re-entry is not a free fix.** The one academic source in the reports says faster signals "increase the tendency of placing bad bets" and that blending slow and fast signals is what helps (C46). L1 already blends three signals of 6, 10 and 12 months. I found no rigorous test of "fast in, slow out" on equity indices. [unverified]
- **Volatility-managed portfolios** do the opposite of buying the fall (they cut exposure when volatility is high). They also fail out of sample (C45, [2+]). Timing in either direction around falls does not survive real-time testing.
- **Short-term reversal** in liquid Australian stocks is not robust after cleaning (report 12 #16, #17).

**Verdict (b).** No evidence that a dip rule or a faster re-entry beats L1's ≥ 2-vote re-entry net of costs and whipsaw. The best-supported statement is that they are about equal to buy-and-hold on return and worse than trend on drawdown.

**What the spec already does that buys falls without predicting anything.**

- Contributions and distributions go to the underweight sleeve first (RND-033). After a fall in one sleeve, that is the fallen one.
- The ±20% band rebalance sells the sleeve that has risen and buys the one that has fallen (PRT-16(c)).
- If the owner's priority is to capture every rebound in full, the spec already has the mode for it: static mode (PRT-23), which is B2. It is never out of the market, so it never misses a recovery. The trend overlay is a deliberate trade of some rebound for a smaller drawdown. He cannot have both, and the evidence in 7.1 is the reason.

### 7.3 Stock level: do heavily fallen stocks recover?

- **Base rates are poor.** Median maximum drawdown about 85%; about 54% of stocks never regain the prior peak; of those that fell 95% or more, one in six did (C47). About 40% of Russell 3000 stocks suffered a 70% fall they never recovered from, 57% in technology (C48).
- **The averages are flattering and misleading.** The average recovery is far above the median because a few survivors multiply; and the main study excludes stocks that went to zero (C47). This is the same skew as section 2, seen from the bottom.
- **The stocks that fall hardest have the worst forward returns as a group.** Distressed stocks earn "anomalously low returns" (C49); lottery-like stocks lose more than 1% a month relative to dull ones (C50).
- **Long-term reversal** (losers of the last 3–5 years outperform) exists in older data but is concentrated in small, low-priced stocks and in January, and disappears under an alternative measure (C51). It is not evidence that a fallen large growth stock will come back.
- **NEXTDC itself.** It fell roughly 40% from 2021 to 2022 on the one series I could see (US OTC line, USD, monthly; [1], rough) and later made new highs [unverified]. That is one survivor. For each NXT there are fallen growth names that did not return; the base rate, not the example, is what a rule would be trading.
- **Momentum says the opposite of "buy the fallen stock".** The best-documented stock-level effect is that 6–12 month losers keep losing on average, except in the brief market-wide rebounds of C11.

**Verdict (c).** No. Whether a particular fallen stock recovers is not predictable from the fall, and the group averages argue against buying them.

### 7.4 What is predictable and what is not

| Question | Answer | Tag |
|---|---|---|
| Are expected index returns higher after a large fall? | Probably, modestly | [1] each, direction agreed by two |
| Can the timing or speed of the recovery be predicted from the fall? | No | [2+] (C33, C39, C40, C43) |
| Does buying dips beat staying invested? | No; about equal or slightly worse | [2+] headline |
| Does a faster trend re-entry help? | No evidence it does; one source says faster signals add bad bets | [1] / [unverified] |
| Is volatility high after falls? | Yes | [2+] (C10, C11, C45) |
| Do momentum portfolios lag in rebounds? | Yes | [2+] (C11) |
| Do individual fallen stocks recover? | About half never do; distressed ones do worst | [2+] (C47, C48) |
| Does long-run valuation predict 10-year returns? | Weakly; not usable for timing | [2+] |

**Nothing here survives as a rule to adopt.** Two things survive as testable questions inside the spec's process. H16 is recommended for registration because it tests the owner's idea in the only form compatible with L1, at a cost of one trial. H17 is optional.

### 7.5 Hypothesis cards for section 7

Both change L1's behaviour, so both belong to strategy family `L1` and consume its trial count: every trial added here raises N in L1's Deflated Sharpe Ratio. Both are return claims and are Family B under RND-001. Registering them as Family A "design choices" would be a way round the rule and is not proposed.

#### Card H16 — Drawdown-conditioned early re-entry

| Field | Content |
|---|---|
| ID | H16 |
| Date registered | set at freeze; not before H1–H5, H8, H9 are decided |
| Card hash | set at freeze |
| Economic rationale | Written before data: expected returns may be higher after large falls (C37, C39), and trend re-entry is late in V-shaped recoveries (C46), so after a deep fall a lower re-entry bar might recover some of the rebound L1 gives up. Counter-rationale: one third of Australian −20% episodes kept falling (C39); dip rules tested no better than buy-and-hold (C43); faster signals add bad bets (C46). |
| Exact rule | L1 exactly as section 9.1, plus one flag per (tranche, sleeve). The flag is set at a month-end evaluation if the sleeve is OFF and its total-return index is at least 20% below its highest month-end value to date. While the flag is set, the sleeve turns ON at votes ≥ 1 instead of ≥ 2. The flag clears when the sleeve turns ON. Exit rule unchanged (OFF at 0 votes). |
| Fixed parameters | Drawdown threshold 20%; early-entry votes 1; reference high = all-time month-end high of the sleeve's total-return series. |
| Permitted perturbation grid | Threshold {15%, 30%}. Two neighbours. |
| Data and proxy map | As H1 (RND-024 proxies, monthly, N = 1, offset `last`). |
| Sample and holdout dates | Development 1990-01 to 2023-12. The L1 holdout is opened once for the family and is not reopened for this card; H16 is reported on development data only unless it is registered before the L1 holdout is opened. |
| Benchmark | L1 as promoted (after H3, H4, H5, H8, H9). |
| Primary metric (exactly one) | Net-of-cost, after-tax CAGR difference, H16 rule minus L1. |
| Secondary metrics | Maximum drawdown difference; number of qualifying episodes per sleeve; for each episode, re-entry price ÷ exit price under both rules; switches per decade; results by regime split (2000–03, 2008–09, 2020, 2022). |
| Pass threshold | t ≥ 3.0 and DSR ≥ 0.95 with N = all L1 trials; maximum drawdown no more than 2 points worse than L1; H1 still passes with the rule in place; positive after the H12 haircut. |
| Fail threshold | CAGR difference ≤ 0; or maximum drawdown more than 4 points worse; or H1 no longer passes. Between: "not passed". |
| Multiple-testing family and adjustment | Family B; strategy family `L1`; counts toward the L1 cap of 50 and toward N. |
| Trials consumed | 3 if the grid is run. |
| Expected outcome, stated in advance | "Not passed". The development sample holds perhaps 3 to 6 qualifying episodes per sleeve [unverified]; t ≥ 3 is not reachable on that many events. The card exists so the idea is tested once and recorded. |
| Result | — |
| Decision | Pass: champion/challenger in `paper_sim` for 6 cycles (RND-032). Otherwise L1 unchanged. |
| Approver | Owner |

#### Card H17 — Contributions into a deep drawdown ("staged buy after −20%") — optional

| Field | Content |
|---|---|
| ID | H17 |
| Date registered | set at freeze, if the owner wants it |
| Card hash | set at freeze |
| Economic rationale | Written before data: while a sleeve is OFF, L1 holds that sleeve's share of new contributions in cash. If expected returns are higher after deep falls (C37), investing new money (not existing holdings) during a deep drawdown buys at lower prices without removing the overlay's protection of the existing balance. Counter-rationale: the amounts are small; holding cash back to deploy later was a net loser in the dip study (C43); one third of −20% episodes kept falling (C39). |
| Exact rule | L1, plus: while a sleeve is OFF and the H16 flag condition holds (at least 20% below its month-end high), that sleeve's base-weight share of each external contribution booked in the month is accumulated in a `dd_contribution` pocket and bought in that sleeve at the next execution date once the pocket is at least `min_order_value_aud`. Units bought this way are tagged and are exempt from the OFF reconciliation sell of PRT-16(a) until the sleeve next turns ON, when they merge into the managed position. No money is ever held back while a sleeve is ON. |
| Fixed parameters | Threshold 20%; minimum order A$1,000; contribution schedule fixed in the card at the owner's actual monthly amount. |
| Permitted perturbation grid | Threshold {30%}. One neighbour. |
| Data and proxy map | As H1, with the contribution schedule applied. |
| Sample and holdout dates | As H16. |
| Benchmark | L1 as promoted, same contributions. |
| Primary metric (exactly one) | Money-weighted (internal rate of) return difference, after cost and tax, against L1. |
| Secondary metrics | Maximum drawdown of the account; worst 12-month result of the tagged units; number of tagged buys; idle months for the pocket. |
| Pass threshold | t ≥ 3.0 and DSR ≥ 0.95; maximum drawdown no more than 2 points worse. |
| Fail threshold | Return difference ≤ 0, or drawdown more than 4 points worse. |
| Multiple-testing family and adjustment | Family B; strategy family `L1`. |
| Trials consumed | 2. |
| Expected outcome, stated in advance | "Not passed", for the same power reason as H16, and because at typical contribution sizes the pocket rarely reaches A$1,000 inside a drawdown. |
| Build cost if it passed | A tagged-units pocket that PRT-16(a) must skip, a new plan kind, and new reconciliation cases. This is real complexity for a rule that moves a few hundred dollars. I would not register it. |
| Result / Decision / Approver | — / — / Owner |

### 7.6 Decisions from section 7

| # | Decision | Basis |
|---|---|---|
| D9 | **No buy-the-dip rule, no drawdown-triggered re-entry and no cash held back for dips in the live spec.** L1's re-entry (ON at ≥ 2 of 3 votes) is unchanged. | C33, C39, C43, C46 |
| D10 | **Register H16 after the L1 design cards are decided**, with its expected outcome written in the card. One base trial. | 7.5 |
| D11 | **Do not register H17** unless the owner asks; its build cost exceeds its plausible benefit. | 7.5 |
| D12 | **No stock-level "fallen stock" rule of any kind.** | C47–C51 |
| D13 | **Add one sentence to the expectations statement (section 30, RND-034):** "After a large fall the system may be out of the market during the first part of the recovery. This is the cost of the drawdown overlay. Static mode never misses a recovery and never avoids a fall." | 7.2 |
| D14 | **H1's reporting pack gains one table:** for each OFF episode, exit price, re-entry price, the ratio, and the market's return while OFF. It shows the owner what L1 gave up and avoided, episode by episode. Reporting only. | 7.2 |

---

## 8. Open items and reasons this could be wrong

**Open items.**

1. **Issuer verification.** Fees, index rules, constituent counts, rebalance schedules and inception dates for MTUM, GTUM, IMTM, ATEC and AINF need reading from the issuer and index-provider pages. Hosts to allow: betashares.com.au, solactive.com, blackrock.com, globalxetfs.com.au, vaneck.com.au, msci.com, cboe.com. This extends open item P3.
2. **NXT's ASX 300 entry date and current VAS weight**, from the S&P announcements and the Vanguard holdings file (C7, C8).
3. **Whether IBKR Australia can trade Cboe Australia-quoted funds** (IMTM). Not confirmed.
4. **Point-in-time ASX 200 constituent data** for H14 and H15: licence, start date and whether it reaches 2000 (RND-029).
5. **Australian index drawdown and recovery table** (C42) should be rebuilt from data in the harness once the proxies are loaded. It is a by-product of H1's bootstrap and costs no trial if run as a description of the benchmark, not of a rule.
6. **AQR "Hold the Dip"** should be read in full (aqr.com blocked), in particular the post-1989 result, for which the two summaries I found give different numbers.
7. **Tax agent:** whether Division 119's 30% floor applies to short-held share gains as report 18 reads it; this changes section 5.3.

**Reasons this could be wrong.**

- **The last five years may be unrepresentative.** Australian small, mid and technology funds all trailed VAS over one window. A different window would look different. The argument in section 4 rests on the research in C26–C29 more than on that window.
- **Momentum may be about to work.** One bad year for MTUM says little. A real premium of 2 points would be worth having at A$250,000. The recommendation is "not at A$5,000 and not without passing the card", not "never".
- **The power arithmetic cuts both ways.** A rule that cannot reach t = 3 is not thereby shown to be useless. The spec chose a bar that rejects most true small edges in order to reject nearly all false ones. That is the owner's standing decision (RND-001); this report applies it and does not relitigate it.
- **Secondary sources.** C37, C39, C43 and C47 are each one originating study seen through summaries. The direction of each is corroborated; the exact numbers are not.
- **Conflicts of interest in sources.** AQR sells momentum and trend funds; Betashares, Global X and VanEck sell the ETFs; Morningstar and the academic papers have no product at stake.
- **Model memory.** The S&P April 2025 dates and the Australian 1987 and 2007–2019 figures are from memory and tagged [unverified].

---

## 9. Sources

| # | Source | How read |
|---|---|---|
| S1 | Bessembinder (2018), "Do stocks outperform Treasury bills?", JFE 129. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:3:p:440-457) | Abstract |
| S2 | ASU W. P. Carey summary of S1. [link](https://blogs.wpcarey.asu.edu/20180917-do-stocks-outperform-treasury-bills) | Search excerpt |
| S3 | Bessembinder, Chen, Choi, Wei (2023), "Long-Term Shareholder Returns: Evidence from 64,000 Global Stocks", FAJ 79(3). [EconPapers](https://econpapers.repec.org/RePEc:taf:ufajxx:v:79:y:2023:i:3:p:33-63) | Abstract |
| S4 | Morningstar Australia, "Only 2.4% of companies deliver all net shareholder wealth". [link](https://www.morningstar.com.au/insights/stocks/233587/only-24-of-companies-deliver-all-net-shareholder-wealth) | Search excerpt |
| S5 | Data Center Knowledge, "Australia's NEXT DC Raises $40 Million in IPO". [link](https://datacenterknowledge.com/investing/australia-s-next-dc-raises-40-million-in-ipo) | Search excerpt |
| S6 | Stockhead, "Zero to hero: how NEXTDC went from start-up to $5.5b stock in 10 years". [link](https://stockhead.com.au/tech/zero-to-hero-how-nextdc-went-from-start-up-to-5-5b-stock-in-10-years) | Search excerpt |
| S7 | Data Center Knowledge, "Data Center Stocks are Hot Internationally" (26 Sep 2016). [link](https://datacenterknowledge.com/infrastructure/data-center-stocks-are-hot-internationally) | Search excerpt |
| S8 | Motley Fool Australia, S&P quarterly rebalance June 2020. [link](https://www.fool.com.au/2020/06/12/sp-quarterly-rebalance-a2-milk-added-to-asx-50-nextdc-in-the-asx-100) | Search excerpt |
| S9 | S&P DJI September 2026 rebalance: [S&P commentary](https://www.spglobal.com/spdji/en/commentary/article/sp-asx-indices-rebalance/); [ASX announcement PDF](https://announcements.asx.com.au/asxpdf/20260904/pdf/073rbz4q8nrckg.pdf) | Search excerpts |
| S10 | NXT weight in VAS: [InvestSMART ETF holders](https://www.investsmart.com.au/security/asx/nxt/nextdc-limited/etf-holders); [TradingView](https://www.tradingview.com/symbols/ASX:NXT) | Search excerpts; they disagree |
| S11 | Jegadeesh & Titman (1993), JF 48. [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:48:y:1993:i:1:p:65-91) | Abstract |
| S12 | Asness, Moskowitz, Pedersen (2013), "Value and Momentum Everywhere", JF 68; report 15 #15 | Report 15 |
| S13 | Barroso & Santa-Clara (2015), "Momentum has its moments", JFE 116. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:116:y:2015:i:1:p:111-120) | Abstract |
| S14 | Daniel & Moskowitz (2016), "Momentum crashes", JFE 122. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:122:y:2016:i:2:p:221-247) | Abstract |
| S15 | [Chicago Booth Review, "Understanding Momentum Crashes"](https://www.chicagobooth.edu/review/understanding-momentum-crashes); [AAII](https://www.aaii.com/journal/article/why-momentum-strategies-can-crash) | Search excerpts |
| S16 | [Alpha Architect, "Avoiding momentum crashes"](https://alphaarchitect.com/avoiding-momentum-crashes/); [etf.com, Swedroe](https://www.etf.com/sections/index-investor-corner/swedroe-downside-momentum) | Search excerpts |
| S17 | McLean & Pontiff (2016), JF 71. [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:71:y:2016:i:1:p:5-32) | Abstract via search |
| S18 | [Counterpoint copy of S17](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf) | Search excerpt |
| S19 | Bhattacharya, Li, Sonaer, "Has Momentum Lost Its Momentum?", via [Quantpedia](https://quantpedia.com/has-momentum-lost-its-momentum/) | Page read |
| S20 | Swedroe, "Is Momentum Really Dead?". [etf.com](https://www.etf.com/sections/index-investor-corner/swedroe-momentum-really-dead) | Search excerpt |
| S21 | Novy-Marx & Velikov (2016), RFS 29. [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:29:y:2016:i:1:p:104-147.) | Abstract |
| S22 | Frazzini, Israel, Moskowitz, "Trading Costs of Asset Pricing Anomalies", via [Alpha Architect](https://alphaarchitect.com/surprise-the-size-value-and-momentum-anomalies-survive-after-trading-costs/) | Search excerpt |
| S23 | Asness, Frazzini, Israel, Moskowitz (2014), "Fact, Fiction and Momentum Investing", via [ThinkAdvisor](https://www.thinkadvisor.com/2014/05/13/10-myths-about-momentum-investing-aqr-capital/) and [CXO](https://www.cxoadvisory.com/value-premium/mocking-momentum-myths) | Search excerpts |
| S24 | MSCI momentum factor documents. [link](https://www.msci.com/documents/1296102/1339060/Factor+Factsheets+Momentum.pdf) | Search excerpt |
| S25 | Nandha & Singh (2012), "Does Momentum Still Exist in the Australian Stock-Market?". [IDEAS](https://ideas.repec.org/a/ijb/journl/v11y2012i1p89-92.html); Henker working paper, [Bond](https://pure.bond.edu.au/ws/files/27740886/Survivorship_Bias_and_Alternative_Explanations_of_Momentum_Effect.pdf) | Search excerpts |
| S26 | "Momentum: Further Evidence from Australia", Finance Research Letters 18 (2016). [IDEAS](https://ideas.repec.org/a/eee/finlet/v18y2016icp234-236.html) | Abstract |
| S27 | "Momentum crashes: the Australian evidence". [CORE](https://core.ac.uk/works/25144183) | Search excerpt; authors not identified |
| S28 | ASX Investment Products report, October 2026. [PDF](https://www.asx.com.au/content/dam/asx/issuers/asx-investment-products-reports/2026/pdf/asx-investment-products-oct-2026.pdf); September 2026 [PDF](https://www.asx.com.au/content/dam/asx/issuers/asx-investment-products-reports/2026/pdf/asx-investment-products-sep-2026.pdf) | Full PDFs |
| S29 | MTUM: [Solactive launch release](https://www.solactive.com/wp-content/uploads/2024/07/Press-Release-Betashares-Launches-Australian-Momentum-ETF-Tracking-Solactive-Australia-Momentum-Select-Index.pdf); [Adviser Voice](https://www.adviservoice.com.au/2024/07/betashares-launches-first-australian-equities-momentum-etf/); [Betashares, "Our rules for momentum investing"](https://www.betashares.com.au/advisers/insights/rules-for-momentum-investing/); [fund page](https://www.betashares.com.au/fund/australian-momentum-etf/). GTUM: [fund page](https://www.betashares.com.au/fund/global-momentum-etf/); [StockAnalysis](https://stockanalysis.com/quote/asx/GTUM/); [SMS Magazine](https://smsmagazine.com.au/news/2026/02/10/new-momentum-strategy-etf-released/). IMTM: [BlackRock](https://www.blackrock.com/au/products/335486/ishares-msci-world-ex-australia-momentum-etf); [Cboe](https://www.cboe.com/au/equities/products/funds/fund/IMTM) | Search excerpts |
| S30 | Ben-David, Franzoni, Kim, Moussawi (2023), "Competition for Attention in the ETF Space", RFS 36(3). [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:36:y:2023:i:3:p:987-1042.) | Abstract |
| S31 | [Alpha Architect summary of S30](https://alphaarchitect.com/competition-for-attention-in-the-etf-space/); [SFI](https://www.sfi.ch/en/publications/competition-for-attention-in-the-etf-space) | Search excerpts |
| S32 | Morningstar Global Thematic Funds Landscape 2024, [PDF](https://assets.contentstack.io/v3/assets/blt4eb669caa7dc65b2/bltdcc1650217a6ca47/6716663877dcca724419a5b0/Morningstar_Global_Thematic_Funds_Landscape_2024.pdf); ["The Thematic Fund Landscape in 7 Charts"](https://www.morningstar.com/funds/thematic-fund-landscape-7-charts); 2021 edition [PDF](https://www.investmentofficer.nl/sites/default/files/Global-Thematic-Funds-Landscape-May-2021.pdf) | Search excerpts |
| S33 | Morningstar Australia, ["You're likely going to underperform with a thematic ETF"](https://www.morningstar.com.au/etfs/chart-week-youre-likely-going-underperform-with-thematic-etf) | Search excerpt |
| S34 | ATEC holdings: [Betashares fund page](https://www.betashares.com.au/fund/sp-asx-australian-technology-etf); [ReviewETF](https://www.reviewetf.com.au/etf/ATEC) | Search excerpts |
| S35 | Goyal & Welch (2008), RFS 21. [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:21:y:2008:i:4:p:1455-1508) | Abstract |
| S36 | Goyal, Welch, Zafirov (2024), RFS 37(11). [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:37:y:2024:i:11:p:3490-3557.) | Abstract |
| S37 | Fama & French (1988), JPE 96. [EconPapers](https://econpapers.repec.org/RePEc:ucp:jpolec:v:96:y:1988:i:2:p:246-73) | Abstract |
| S38 | Poterba & Summers (1988), JFE 22. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:22:y:1988:i:1:p:27-59) | Citation; finding via search |
| S39 | Kim, Nelson, Startz (1991), RES 58. [EconPapers](https://econpapers.repec.org/RePEc:oup:restud:v:58:y:1991:i:3:p:515-528.) | Abstract |
| S40 | "Long-Horizon Mean-Reverting Stock Prices Revisited", JFQA. [Cambridge](https://resolve.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/longhorizon-meanreverting-stock-prices-revisited/9E5B50277CCDE2451639A1B87E05AAFD) | Search excerpt |
| S41 | [Advisor Perspectives, "The Use and Misuse of the CAPE Ratio"](https://www.advisorperspectives.com/articles/2019/05/20/the-use-and-misuse-of-the-cape-ratio); [Swedroe](https://www.etf.com/sections/index-investor-corner/swedroe-using-valuation-metrics) | Search excerpts |
| S42 | Asness, Ilmanen, Maloney, "Market Timing: Sin a Little". [AQR PDF](https://www.Aqr.Com/-/media/AQR/Documents/Insights/White-Papers/Market-Timing-Sin-a-Little.pdf) | Search excerpt |
| S43 | Carlson, ["How the Stock Market Performs After a Correction"](https://awealthofcommonsense.com/2026/03/how-the-stock-market-performs-after-a-correction/) (March 2026), via a [repost](https://www.pulse.bot/stock-investing/blogs/how-the-stock-market-performs-after-a-correction-3f9b102a-3eda-4425-a50e-593bc0b16fa6) | Search excerpt |
| S44 | Dimensional, ["Stock Gains Can Add Up after Big Declines"](https://www.dimensional.com/fi-en/insights/stock-gains-can-add-up-after-big-declines) | Search excerpt |
| S45 | Oliver (AMP), ["Corrections, gummy bears and grizzly bears"](https://amp.com.au/insights-hub/blog/investing/corrections-gummy-bears-and-grizzly-bears); [2022 republication](https://www.sharecafe.com.au/2022/02/11/corrections-gummy-bears-and-grizzly-bears/); [table of Australian bear markets since 1900](https://topforeignstocks.com/2018/11/29/bear-markets-in-australian-stock-market-since-1900/) | Search excerpts |
| S46 | [Plus500 / Stacker table of corrections since 1950](https://us.plus500.com/en/newsandmarketinsights/stock-market-corrections-since-1950); [MoneyWeek](https://moneyweek.com/investments/how-long-does-a-stock-market-recovery-take); [Visual Capitalist](https://www.visualcapitalist.com/sp-500-market-crashes/) | Search excerpts |
| S47 | Motley Fool Australia (26 Mar 2026), citing Betashares on April 2025. [link](https://www.fool.com.au/2026/03/26/how-long-will-it-take-for-the-asx-200-to-recover-expert/) | Search excerpt |
| S48 | [InvestSMART, "History shows the path to recovery is never smooth"](https://www.investsmart.com.au/investment-news/history-shows-the-path-to-recovery-is-never-smooth/30062) | Search excerpt |
| S49 | Cao, Chong, Villalon, "Hold the Dip", AQR Alternative Thinking, December 2025. [AQR](https://www.aqr.com/Insights/Research/Alternative-Thinking/Hold-the-Dip); summary at [Alpha Architect](https://alphaarchitect.com/is-trend-following-better-than-buy-the-dip/) | Search excerpts |
| S50 | Independent summaries of S49: [Zacks IM](https://zacksim.com/financial-professionals-insights/why-buying-the-dip-can-hurt-returns-over-time/); [Evidence Investor](https://www.evidenceinvestor.com/post/buy-the-dip) | Search excerpts |
| S51 | Cederburg, O'Doherty, Wang, Yan (2020), JFE 138. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117) | Abstract |
| S52 | Moreira & Muir (2017), "Volatility-Managed Portfolios", JF 72. [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:72:y:2017:i:4:p:1611-1644) | Citation; finding via S51 |
| S53 | [Of Dollars and Data, "Why Trend Following is Harder Than it Looks"](https://ofdollarsanddata.com/why-trend-following-is-harder-than-it-looks/); [RCM, "Why you Should be Afraid of the V-Shaped Reversal"](https://www.rcmalternatives.com/?p=12339) | Search excerpts |
| S54 | Mauboussin & Callahan (May 2025), "Drawdowns and Recoveries", Morgan Stanley. [PDF](https://www.eatonvance.com/content/dam/im/assets/publication/thought-leadership/consilient-observer/article_drawdownsandrecoveries.pdf); summaries: [A Wealth of Common Sense](https://awealthofcommonsense.com/2025/05/not-all-stocks-recover-their-losses/), [Morningstar Australia](https://www.morningstar.com.au/personal-finance/how-weigh-up-companies-after-big-share-price-fall) | Search excerpts |
| S55 | Cembalest (J.P. Morgan, 2014), "The Agony & the Ecstasy". [PDF](https://www.chase.com/content/dam/privatebanking/en/mobile/documents/eotm/eotm_2014_09_02_agonyescstasy.pdf); [Irish Times](https://www.irishtimes.com/business/personal-finance/extreme-winners-take-it-all-while-40-of-stocks-suffer-catastrophic-declines-1.1970035) | Search excerpts |
| S56 | Campbell, Hilscher, Szilagyi (2008), "In Search of Distress Risk", JF 63. [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:63:y:2008:i:6:p:2899-2939) | Abstract |
| S57 | Bali, Cakici, Whitelaw (2011), "Maxing out", JFE 99. [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:99:y:2011:i:2:p:427-446) | Abstract |
| S58 | De Bondt & Thaler (1985), JF 40, [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:40:y:1985:i:3:p:793-805); George & Hwang (2004), [working copy](https://www.bauer.uh.edu/tgeorge/papers/gh5-paper.pdf) | Citations; findings via search excerpts |
| — | AINF: [Investor Daily](https://www.investordaily.com.au/global-x-provides-exposure-to-critical-backbone-of-ai-revolution); [SMS Magazine, 30 Apr 2025](https://smsmagazine.com.au/news/2025/04/30/global-x-releases-ai-infrastructure-etf/); [product flyer](https://files.globalxetfs.com.au/AINF_Product_Flyer_a798b80112.pdf); offshore data-centre ETFs, [AUSIEX](https://axis.ausiex.com.au/articles/data-centres-test-investor-appetite/) | Search excerpts |
| — | Internal: FD_FINAL.md v2.10 (D3, D16, PRT-13 to PRT-19, RND-001, RND-010 to RND-033, VAL-20 to VAL-27, MKT-02, section 27); reports 12, 14, 15, 16, 18 | Read |
