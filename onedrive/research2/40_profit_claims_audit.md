# 40. Profit claims audit: who says they make money trading, and is it true

Date: 2026-11-13. Spec read: FD_FINAL.md v2.10 (opening statement, D14, PRT-22 to PRT-26, RSK-29, RND-010 to RND-029, MON-07, section 27 stages). Prior reports used and not redone: R06 (copy trading, CTA indices as signal), R11 (economics gate), R14 (trend literature), R33 (owner reporting, behaviour gap), R34 (platform features — this report does not repeat its feature matrix), R35 (algorithm survey, cards H30–H41).

Tags: **[2+]** two or more independent sources agree; **[1]** one source; **[unverified]** no source reached today, or model memory only; **[computed]** my arithmetic from stated inputs; **[estimate]** my judgment, not evidence.

**Access limit that affects every tag.** WebFetch could not reach `asic.gov.au`, `download.asic.gov.au`, `spglobal.com` or `morningstar.com` (outside this session's allowed network domains). No primary PDF was opened today. Every figure rests on search-result extracts of the primary page plus secondary coverage. Where the regulator's own page and at least one independent outlet gave the same number, the tag is [2+]. Allowing those hosts would let a later pass read REP 626, REP 828, the SPIVA Australia scorecard and the Morningstar barometer directly.

---

## 0. Answer in brief

1. **Real, large, repeatable trading profits exist, and almost none of them are for sale to a person with A$5,000.** The verified cases are a handful of closed or institution-only funds: Renaissance Medallion (about 66% a year before fees and 39% after, 1988–2018, employees only) [2+], Citadel Wellington (about 19% a year net since 1990) [2+], D. E. Shaw Composite (about 12.9% a year net since 2001, closed to new money) [2+]. Their edge comes from scale, data, speed, financing and hundreds of staff. None of it is copyable at home.
2. **What a retail investor can actually buy from professionals has earned about cash-plus to equity-minus.** Trend-following funds as a group returned about 4.8% a year from 2000 to mid-2024, against 5.9% for global shares [1]. AQR's retail managed-futures fund has returned 4.2% a year since 2010 [2+]. Man AHL Alpha (AUD), open to Australians, 4.7% a year since 2009 [1]. Renaissance's own outside fund has roughly matched its index, not Medallion [1]. Their honest value is diversification in bad equity years (2008, 2022), not higher return.
3. **Retail products that advertise high returns are almost all unaudited, backtested, or annualised from a few weeks.** Tickeron's "116% annualised" is about 22–30% over 93 days [computed]. Danelfin's "+376%" is a self-described backtest. Trade Ideas' Holly figures are the vendor's simulation. No retail bot, signal service or copy-trading leaderboard examined here publishes an independently audited, net-of-fee, all-accounts record. The one long-running, fully audited "AI stock picker" — the AIEQ exchange-traded fund, live since 2017 — has trailed the S&P 500 [1].
4. **Regulator data on what retail traders actually earn is consistent across countries and decades: most lose.** Australia: 68% of retail CFD clients lost money in 2023–24, A$458 million in total; 85% for options CFDs [2+]. Brazil: 97% of persistent day traders lost [2+]. Taiwan: fewer than 1% are reliably profitable [2+]. India: 93% of individual derivatives traders lost over three years [2+]. Europe: 74–89% of CFD accounts lose [2+].
5. **Professional stock-pickers mostly lose to the index too.** In 2025, 74% of Australian general equity funds trailed the S&P/ASX 200; over 15 years about 85–87% did [2+ for one year; the 15-year figure is two secondary sources that differ by two points]. In the US, 21% of active funds survived and beat their passive peer over the 10 years to 2025 [1].
6. **Australian newsletters: the claims are real numbers measured generously.** Motley Fool Share Advisor reports an average gain per pick (73.2% vs 44.4% for the index at December 2021), before brokerage and tax, not a portfolio return [1]. Intelligent Investor's model income portfolio shows +0.7% a year over the ASX 200 since 2001 before fees; its real listed funds have trailed the index over three and five years [1]. No independent audit of either was found.
7. **"AI trading bots" advertised to Australians on social media are, in ASIC's words, very unlikely to exist.** ASIC took down more than 19,400 scam sites and ads in 2025–26 [2+].
8. **Where our system stands, honestly.** It has **no live track record**. It makes **no return claim**; the spec says so in its second paragraph. Its expected result is the index return minus small costs, with a possible reduction in drawdown that is still an untested hypothesis (H1). On the evidence above, "index return minus small costs" beats the median outcome of every retail category in this report and most professional ones. It will not beat Medallion, it does not have the crisis protection of a diversified trend fund, and at A$5,000 a zero-brokerage index account or a robo-adviser gets the same return with less work (R34 §5.1).
9. **Three things the evidence supports that the spec lacks** (cards in §8): H60, a small managed-futures diversifier sleeve as a tested hypothesis for the larger-account stage; H61, a pre-registered forecast of the live result so the live record can later be scored against it; H62, a counterfactual ledger of every owner override. Plus one piece of spec text: a fixed "track-record statement" so that our own numbers are held to the standard this report applies to everyone else (§7.3).

---

## 1. The claim-auditing framework

Ten tests. A claim that fails any of the first four is not evidence of anything.

| # | Test | What passes | What fails | Why it matters (evidence) |
| --- | --- | --- | --- | --- |
| A1 | **Live or backtest?** | Real money, real fills, dated | Backtest, "simulation", "paper", "hypothetical", "model portfolio" | Median Sharpe of 215 bank strategy indices fell from 1.20 in backtest to 0.31 live, a 73% drop [2+]. Across 888 Quantopian algorithms, backtest Sharpe had almost no power to predict live results, and more backtesting meant a bigger gap [2+]. |
| A2 | **Who verified it?** | Auditor, regulator filing, fund administrator, exchange-listed fund price, broker statements for all accounts | Vendor's own page, screenshots, press releases | A vendor chooses what to show. A listed fund's unit price cannot be edited. |
| A3 | **All accounts or the best ones?** | Every strategy ever launched, including closed ones; asset-weighted | Leaderboards; "top 5 bots"; surviving funds only | Leaderboards select on luck and leverage (R06 A1). Young Collective2 systems "have a high mortality rate" [1]. |
| A4 | **Net of what?** | After fees, spreads, commissions, financing; ideally after tax | "Gross", "before costs", "per recommendation" | Multi-manager hedge fund investors kept 46–59 cents of each dollar earned in 2021–23 [1]. Motley Fool's scorecard excludes brokerage and tax [1]. |
| A5 | **Against what benchmark?** | An investable index of the same risk, with dividends | Price index without dividends; cash; nothing | Benchmarks changed between All Ordinaries, All Ords Total Return and ASX 200 Accumulation across Intelligent Investor's own reports [1]. |
| A6 | **How long?** | 10+ years including at least one bear market | Weeks or months, annualised | 116% "annualised" from 93 days is 22–30% actual [computed]. With 5% tracking error, a true 1%-a-year edge needs about 100 years of data to reach t = 2; a 2% edge needs 25 years [computed: (2 × 5 ÷ edge)²]. |
| A7 | **How much risk and leverage?** | Volatility, maximum drawdown and leverage stated | Win rate only; "90% win rate" | A high win rate with rare large losses is the signature of short-volatility and martingale styles (R06 A1). |
| A8 | **Compounded or averaged?** | CAGR, time-weighted; money-weighted for the investor | Arithmetic average of annual returns; average gain per pick | Medallion's famous 66%/39% are arithmetic averages, and the fund pays out profits so nobody compounded at that rate [1]. |
| A9 | **Can I get in, at what size?** | Open, with a minimum I can meet, at the fee quoted | Closed, capped, employees only, wholesale only | Medallion is capped near US$10 billion and closed [1]. D. E. Shaw's main funds are closed [2+]. |
| A10 | **Who gets paid if I lose?** | Fee on assets or flat subscription with no flow incentive | Broker is the counterparty; signal seller paid on volume; "challenge" fees | 45% of new Australian retail CFD clients came from paid online ads and 20% from paid referrals [1]. Roughly 7% of prop-firm "challenge" buyers ever receive a payout [1]. |

GIPS (the Global Investment Performance Standards) is the institutional form of A2–A5 and A8: composites must include every fee-paying discretionary account, terminated ones stay in the history, returns are time-weighted, and the firm, not the product, claims compliance. No retail bot, signal marketplace or newsletter found today claims GIPS compliance [unverified as a universal statement; none was found].

---

## 2. Retail bots, signals, copy trading and "AI trading"

### 2.1 What the regulators say

- **ASIC, August 2026 (26-195MR):** scammers "claim their fake trading bots use AI to generate passive income and unachievable returns"; ASIC says it is "very unlikely that these trading bots exist". More than 19,400 scam websites and ads were taken down in 2025–26, up 182% [2+: ASIC release extract; Finance Magnates; Crowdfund Insider]. Typical pattern: a social-media ad with an AI-generated celebrity endorsement, a fake news page, a site with a live chart and a chatbot, sometimes a false claim of an ASIC licence [2+].
- **National Anti-Scam Centre:** Australians lost A$2.18 billion to scams in 2025, A$837.7 million of it to investment scams [1].
- **CFTC, January 2024, "AI Won't Turn Trading Bots into Money Machines":** "AI technology can't predict the future or sudden market changes"; promises of high or guaranteed returns are a fraud flag [2+: CFTC page; press release 8854-24]. The advisory cites a US$3.4 billion forex fraud that advertised an AI bot [1].
- **SEC, NASAA and FINRA** issued a joint investor alert on AI-labelled investment fraud [2+].
- **ASIC finfluencer actions:** 18 warning notices in June 2025; a second sweep targeted free content that funnels followers into paid "signals" groups; the Federal Court found one finfluencer ran an unlicensed advice business through Instagram, seminars and a paid Discord group and made permanent injunctions [2+].
- **ASIC v eToro (filed August 2023):** ASIC's first design-and-distribution case; it alleges the CFD target market was "far too broad" for a product "where most clients lose money". Still in court at August 2025 (a procedural ruling, [2025] FCA 904); no penalty outcome found [2+ for the filing; 1 for the 2025 status].

### 2.2 Company by company

| Who | What is claimed | Audit test result | Tag |
| --- | --- | --- | --- |
| **Tickeron** (AI "robots" and "agents") | Press releases: "116% annualised" over 93 days; "159% average annualised with 90% win rates" on leveraged ETFs; "up to 210%" | Fails A1 (some are "real-money simulations"), A2 (self-published by wire), A3 ("top 5", "top 10"), A6 (31–141 days), A7 (leveraged ETFs, win rate only). 116% annualised over 93 days is +22% compounded or +30% simple [computed] | [2+] that the claims are made this way; no independent verification exists [1] |
| **Trade Ideas — Holly AI** | Published performance reports; "68% win rate" | Vendor's own simulation of signals, not audited live trading; no third-party audit of user results found | [1] (secondary reviews; several are affiliate pages) |
| **Danelfin** | "Best Stocks" strategy +376% from January 2017 to June 2025 vs +166% S&P 500; top-score stocks beat the market by about 15–21% annualised over three months | Danelfin itself labels the result backtested; it is the average of 10 randomised simulated portfolios; the headline figure differs by publication date (+191%, +263%, +376%). Fails A1, A2 | [2+] (Danelfin's own pages plus reviews) |
| **Kavout** (K Score) | No specific return claim located today | Cannot audit | [unverified] |
| **TrendSpider** | A charting and backtesting tool; no vendor return claim located | Nothing to audit; user backtests are subject to A1 | [unverified] |
| **AIEQ** (AI Powered Equity ETF, live since October 2017) | Marketed as AI stock selection | **The only fully audited case in this group** (a listed fund). About +57% since inception against +84% for the S&P 500 at early 2022; still behind on later snapshots | [1] for each snapshot; direction consistent across three sources |
| **AI-run mutual funds generally** | — | Chen and Ren (2022): AI-powered US funds "do not outperform the market per se"; they beat human-run peers mainly through lower turnover (31% vs 72%) | [2+] |
| **3Commas** | Bot marketplace; no audited returns | Security, not performance, is the verified fact: leaked API keys led to an estimated US$15–22 million of user losses in late 2022; the company first blamed phishing, then confirmed the leak | [2+] |
| **Cryptohopper** | Marketplace statistics and strategy backtests | Own disclaimer: displayed profits "are not indicative of future results"; statistics are the platform's own; buyer beware; no third-party verification found | [1] |
| **Pionex** (grid and arbitrage bots) | Arbitrage bot "15–50% APR with extremely low risk"; displayed grid "APR" | APR is an extrapolation from recent funding rates or grid profits, not a realised yearly return. A grid bot is short volatility: it earns in ranges and holds the falling asset in a downtrend. No audit found | [1] |
| **Crypto bots as a class** | "Passive income" | No rigorous independent study of retail bot outcomes was found. Figures that circulate ("73% fail in six months", a "Cambridge study") could not be traced to a primary source | [unverified] |
| **Composer** (strategies called "symphonies") | Backtest charts on each shared strategy | Composer's own help pages call a backtest "a model, or simulation"; default window one year, slippage assumed at 1 basis point. Many shared strategies rotate leveraged ETFs. No all-accounts live record published | [1] |
| **Quantopian** (closed 2020) | Crowd-sourced algorithms for a hedge fund | Its own study of 888 algorithms: backtest Sharpe had little value in predicting live performance; the firm ended live trading in 2017 and shut down | [2+] |
| **Collective2** | Marketplace with live-tracked strategy records | Better than most on A1 (trades are tracked forward), but pages state "All results are hypothetical"; fails A3 (leaderboard, high system mortality; a 2009 snapshot found 18% of stock systems matched or beat the S&P 500 over 30 days). Not usable for ASX shares at IBKR Australia (R06) | [1] |
| **eToro CopyTrader / Popular Investors** | Popular Investor pages show each leader's returns | No published statistic on what **copiers** earn was found. eToro's CFD risk warnings show 51–78% of retail accounts lose, depending on entity and period. Academic work: no "wisdom of the crowd"; popularity does not predict returns; being copied increases the leader's risk-taking (R06 A1; Dorfleitner et al. 2018) | [1] for the disclosure range; [2+] for the academic direction |
| **ZuluTrade** | Signal-provider rankings | No independent outcome data found | [unverified] |
| **Prop-firm "funded trader" challenges** | "Trade our capital" | Industry data: about 14% pass the evaluation and about 7% of buyers ever receive a payout; FTMO's own 2026 figure is 12% receiving at least one payout. Revenue is the challenge fee | [1] |
| **"AI trading" apps in Australian social-media ads** | Guaranteed or very high passive income | ASIC: very unlikely to exist; mass takedowns | [2+] |

### 2.3 Verdict on the category

No retail bot, signal service, AI scorer or copy-trading platform examined passes tests A1–A4 together. That does not prove every one loses money. It means **none has shown it makes money** to the standard a listed index fund meets every day. Where an audited equivalent exists (AIEQ; AI-run mutual funds), the result is ordinary: at or below the index.

---

## 3. Australian newsletters and advisory services

| Who | Claim | What it actually measures | Independent evidence | Verdict |
| --- | --- | --- | --- | --- |
| **Motley Fool Share Advisor (AU)**, launched December 2011 | "Average return per recommendation" 73.2% vs 44.4% for the All Ordinaries at December 2021; 60.5% vs 39.6% in early 2021; 53.8% vs 25.3% about 2017 [1, all from fool.com.au] | The simple average of each pick's gain since its own recommendation date, against the index from the same date. It is not a portfolio return: no position sizing, no cash, no selling discipline, no annualisation. Brokerage and tax excluded [1] | None found. One user review claims a 0.75% edge; unverifiable [unverified] | **Plausibly ahead of the index on its own measure; unproven as an investor outcome.** Fails A2, A4, A8. An average of picks is dominated by a few very large winners; a subscriber who bought only some picks could be well below it |
| **Intelligent Investor / InvestSMART** | Equity Income model: 9.2% a year since August 2001, +0.7% a year over the S&P/ASX 200 Accumulation (2025 fact sheet). Earlier reports: 13.6% vs 8.0% (2016), 12.7% vs 7.56% (2018) [1] | Model portfolios, before fees. The claimed margin has shrunk from +5 points to +0.7 as the record lengthened and the benchmark changed | **The live, listed funds are the audit.** INIF at 30 June 2026: 6.74% a year over 3 years vs 10.62% for the index; 7.43% vs 7.76% over 5 years. IIGF from October 2020 to April 2025: 8.1% a year vs 11.3% [1, InvestSMART's own fund pages] | **Model edge small and pre-fee; real-money funds behind the index.** Credit: InvestSMART publishes the unflattering fund numbers itself |
| **Marcus Today** (newsletter and SMAs) | No performance figures retrieved today | — | — | [unverified]. The SMAs have real records on platform reports; someone should read the fact sheet before any view is formed |
| **Morgans and other brokers' model portfolios** | No performance figures retrieved today | Model portfolios are hypothetical by construction (A1) | Australian evidence on analyst revisions in large caps: no significant abnormal return after costs (R06 A2) | [unverified] for Morgans specifically |
| **Simply Wall St** | Makes no return claim. Terms say content is "factual information or general advice" from an analysis model [1] | A research and visualisation tool | — | **Nothing to audit.** Not a profit claim |
| **Stockspot** (covered for features in R34) | Model portfolios "outperformed 336 of 336 comparable diversified funds over ten years"; 15.8–18.2% after fees in the year to June 2025 [1, Stockspot] | Index ETFs at low cost against **surviving** active multi-asset funds | Consistent with SPIVA: low-cost indexing beats most active funds. The comparison group excludes dead funds, which flatters the active side, so the true margin is if anything larger | **Credible, and not a trading claim.** The return is the market's |
| **Investment newsletters in general** | — | — | Metrick (1999, Journal of Finance): 153 US newsletters, data free of survivorship and backfill bias; no evidence of stock-picking skill beyond chance and no "hot hands" [2+] | The base rate for a newsletter is zero skill |

---

## 4. Professional systematic managers

### 4.1 The record

| Manager / index | Verified record | Fees | Can a retail Australian invest? | Tag |
| --- | --- | --- | --- | --- |
| **Renaissance Medallion** | About 66% a year gross, 39% net, 1988–2018 (Zuckerman; Cornell's paper gives 63.3% and 39.2%). These are arithmetic averages; profits are distributed, not compounded. +76% in 2020 | 5% of assets plus 44% of profits | **No.** Employees and insiders only; outside investors were bought out (sources say 1993–2006); capped near US$10 billion | [2+] for returns; [1] for cap and averaging |
| **Renaissance RIEF** (the outside fund) | −19% in 2020, the same year Medallion made 76%. Annualised 9.1% since inception against 9.7% for its index at that date | Institutional | Wholesale only | [2+] for 2020; [1] for since-inception |
| **Citadel Wellington** | 19.2% a year net since 1990 (to May 2025); 10.2% in 2025 | Pass-through of all costs plus performance fee. Citadel's pass-through alone was about 5–6% of assets in 2014–15. Across multi-managers, investors kept 46 cents of each gross dollar in 2021 and 59 cents in 2023 | **No.** Institutional, capacity-limited; it returned US$5 billion of profits to investors for 2025 | [2+] for returns; [1] for fee shares |
| **Millennium** | 10.5% in 2025; long-run double-digit net | Pass-through. In one weak year the charges left investors 3.3% | **No** | [2+] for 2025; long-run figure [unverified] |
| **D. E. Shaw Composite** | 12.9% a year net since 2001, one losing year; 18.5% in 2025. Oculus 14.4% a year since 2004 | High; not retrieved | **No.** Closed to new capital | [2+] (Reuters, Bloomberg, via sources) |
| **Two Sigma** | Returns not retrieved. SEC fined it US$90 million in January 2025 for leaving known model vulnerabilities unfixed from 2019 to 2023; some funds gained US$400 million and others lost US$165 million as a result | — | **No** | [2+] for the SEC order |
| **AQR Managed Futures (AQMIX)** | 4.16% a year since January 2010 (to March 2026) | Net expense ratio shown as 2.72% (includes costs of the fund's structure) | US mutual fund; not offered to Australian retail | [2+] (AQR page; Zacks 4.27% to June 2026) |
| **Man AHL Alpha (AUD)** | 4.73% a year net since September 2009 (to March 2026); 16.9% in the latest year; 5.0% a year over three years | Fee rates not retrieved; indirect cost of a sister class 1.64% | **Yes.** Unlisted Australian unit trust; a retail class is listed with a A$5,000 minimum [1, to be confirmed in the PDS] | [1] |
| **Man AHL Diversified** | 15.1% a year from 1996 to 2011; later figure not retrieved | 2-and-20 style historically | Via the Australian trusts | [1], dated |
| **Winton** | Assets fell from above US$30 billion to under US$10 billion and the flagship lost about 20% in 2020 [unverified — model memory; today's search confirmed only a −21% 2020 for a Winton-managed UCITS fund] | — | An Australian wholesale class shows a A$20 million minimum [1] | [unverified] mostly |
| **Aspect Diversified Futures** | Performance not retrieved | — | **Yes**, A$20,000 minimum listed [1] | [1] |
| **SG CTA Index** (large CTAs, equal-weighted) | 4.8% a year from January 2000 to May 2024, against 5.9% for global shares; beat global shares in 35% of rolling three-year periods. Sharpe 0.61 from 2000 to late 2022. +20.1% in 2022, its best year; about −3% in 2023; +2.4% in 2024; a −16.3% drawdown from April 2024 to May 2025 | Index is net of manager fees | Not investable directly | [1] for long-run (Morningstar); [2+] for 2022; [1] others |
| **SG Trend Index** | About 4.9% a year since 2000; +20.9% in 2008; +2.4% in 2025 | — | — | [1] each |
| **Barclay CTA Index** | Average 12.2% a year from 1980 as quoted in 2009; 5.67% a year from 2000 to 2007. Started with 15 programs, so the early decades carry survivorship and backfill doubts | — | — | [1] |
| **Hedge funds as a group** | Commonly found not to beat a 60/40 stock-bond mix after fees. Buffett's ten-year bet (2008–2017): S&P 500 index fund about 7.1% a year against about 2.2% for the chosen funds of hedge funds | 2-and-20 plus fund-of-funds layer | Wholesale | [1] for 60/40; Buffett figures [unverified — model memory, widely reported] |
| **US managed-futures ETFs (DBMF, KMLM)** | KMLM: US$10,000 at December 2020 was US$14,551 at November 2026, about 6.5% a year [computed from one source]. DBMF: a 20% maximum drawdown and a negative latest 12 months on one snapshot | About 0.85–0.90% (R07) | **Probably**, through IBKR as US-listed ETFs; R07 asked for this to be confirmed. No ASX-listed managed-futures ETF was found today or in R10 | [1] |

### 4.2 What this shows

1. **The extraordinary records are real and closed.** Medallion, Citadel, D. E. Shaw and Millennium pass tests A1, A2, A4 and A6. They fail A9 for us. Their fees alone (5-and-44; pass-through of 5–7% of assets) exceed the total return of most strategies.
2. **Capacity is the reason they are closed.** Medallion returns profits each year to stay near its cap. D. E. Shaw and Citadel hand money back. An edge that works on US$10 billion with a thousand staff is not the same object as a monthly rule on two ETFs.
3. **The same firm's public product is ordinary.** RIEF against Medallion in 2020 is the clearest demonstration: −19% and +76% from one building [2+].
4. **Retail-accessible systematic funds have delivered cash-plus with useful timing.** About 4–5% a year over 15–25 years, with the gains concentrated in equity crises: 2008 (+13% to +21%) and 2022 (+20%) [1 to 2+]. This agrees with R14. They also have long flat or losing stretches (2011–2013, 2016–2018, April 2024 to May 2025) [1; R06 A3].
5. **Even the best quants have operational failures.** Two Sigma left a known model flaw unfixed for four years [2+]. The lesson for us is about controls, and the spec's change control, hashing and replay checks (RND-010, MON-07) are the right kind of answer.

---

## 5. What retail active traders actually earn

| Evidence | Finding | Tag |
| --- | --- | --- |
| **ASIC REP 626 (2019)**, retail OTC derivatives | Share of clients losing money: binary options about 80%, CFDs 72%, margin FX 63%. 9.3 million positions closed out on margin call; over 41,000 accounts went negative, owing A$33 million | [2+] |
| **ASIC product intervention order (March 2021)** | Leverage limits cut aggregate retail CFD losses by 91%, from A$372 million to A$33 million a quarter, in the first six months. Extended to May 2027; ASIC proposed in October 2026 (CS 64) to extend to 2037. Binary options are banned for retail until 2031 [1] | [2+] except where marked |
| **ASIC REP 828 (January 2026)**, review of 52 CFD issuers | In 2023–24, 133,674 retail clients lost money on CFDs: 68% of all retail CFD clients; net losses over A$458 million including A$73 million in fees. 84–85% of retail clients trading CFDs over options lost. Over half the sector breached the intervention order with margin discounts; nearly A$40 million refunded to 38,000 clients | [2+] |
| **ASIC, May 2020**, retail trading in the COVID crash | Retail turnover and new accounts jumped; holding periods shortened; retail investors were poor at timing (prices tended to fall after net-buying days and rise after net-selling days). CFD losses were A$234 million in one week at 12 providers | [2+] for direction and the CFD week; the exact timing percentages differ between secondary sources |
| **ASIC studies of retail exchange-traded options or day trading, 2022–2024** | None found today. The task brief mentions them; I could not confirm they exist | [unverified] |
| **ESMA / FCA** | 74–89% of retail CFD accounts lose; FCA about 80% | [2+] |
| **Barber and Odean (2000)**, 66,465 US households, 1991–96 | The most active traders earned 11.4% a year; the market returned 17.9% | [2+] |
| **Barber, Lee, Liu and Odean (2014)**, all Taiwan day traders | Fewer than 1% reliably earn positive returns after fees | [2+] |
| **Chague, De-Losso and Giovannetti (2020)**, all Brazilian futures day traders, 2013–15 | Of those who persisted over 300 days, 97% lost money; 1.1% earned more than the minimum wage; no evidence of learning | [2+] |
| **SEBI (September 2024)**, Indian equity derivatives | 93% of 11.3 million individual traders lost over three years; aggregate loss ₹1.81 lakh crore; of those who lost two years running and kept going, 8% made money in the third | [2+] |
| **SPIVA Australia, year-end 2025** | 74% of Australian general equity funds trailed the S&P/ASX 200 in 2025. Over 15 years 85% (mid-2025 scorecard) to 87% (one summary of year-end). A majority in every category trailed over ten years | [2+] one-year; [1] each 15-year figure |
| **Morningstar Active/Passive Barometer (US)** | 38% of active funds survived and beat passive in 2025; 21% over the ten years to 2025; 25% over the ten years to June 2026. The cheapest fifth succeeded 31% of the time | [1] per figure; consistent |
| **Published strategies** | Stock-return anomalies lose about a third of their return after publication (McLean and Pontiff) | [2+] |

The pattern is stable across four continents, three decades and every product type: **the more a retail investor trades, and the more leverage the product has, the worse the result.** The spec's design choices — monthly evaluation, no leverage, no derivatives, ETFs only, turnover bands — sit at the safe end of every one of these gradients.

---

## 6. Claims table

Verdict key: **True** = verified to audit standard. **True but unavailable** = verified, cannot be bought. **True, modest** = verified, return near or below a share index. **Unproven** = no evidence either way to audit standard. **Misleading** = the number is real but measured in a way that overstates the investor's outcome. **False/scam** = regulator says so.

| # | Who | Claim | Claim source | Independent evidence | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Renaissance Medallion | 66% gross / 39% net a year, 1988–2018 | Zuckerman (2019); Cornell (2020) | Institutional Investor, Bloomberg, Morningstar agree [2+] | **True but unavailable** |
| 2 | Renaissance RIEF | Institutional quant equity | Investor letters via Bloomberg | −19% in 2020; about index-like since inception [2+/1] | **True, modest** |
| 3 | Citadel Wellington | 19% a year net since 1990 | Investor reports via Bloomberg, CNBC | Several outlets agree [2+] | **True but unavailable** |
| 4 | D. E. Shaw Composite | 12.9% a year net since 2001 | Reuters, Bloomberg sources | Agree [2+] | **True but unavailable** (closed) |
| 5 | Millennium | Double-digit net long-run; 10.5% in 2025 | Bloomberg | 2025 [2+]; long-run [unverified] | **True but unavailable** |
| 6 | Two Sigma | Scientific, model-driven investing | Firm | SEC order: known model flaws unfixed 2019–23, US$90m penalty [2+] | Returns not audited here; **control failure proven** |
| 7 | CTAs / trend followers (SG CTA Index) | Positive returns with crisis protection | SG, managers | 4.8% a year 2000–2024 vs 5.9% global shares [1]; +20% in 2022 [2+]; 2008 positive [1] | **True, modest**; diversifier, not a return engine |
| 8 | AQR Managed Futures | Trend premium for retail | AQR | 4.16% a year since 2010 [2+] | **True, modest** |
| 9 | Man AHL Alpha (AUD) | Systematic trend for Australian investors | GSFM | 4.73% a year net since 2009 [1] | **True, modest**; accessible |
| 10 | Winton | Scientific trend following | Firm | Large asset decline and a bad 2020 [unverified] | **Unproven today** |
| 11 | Hedge funds as a group | Absolute returns | Industry | Do not beat 60/40 after fees [1] | **Mostly not delivered** |
| 12 | Active Australian equity funds | Beat the index | Fund marketing | SPIVA: 74% failed in 2025; about 85–87% over 15 years [2+/1] | **False for most** |
| 13 | Motley Fool Share Advisor AU | Picks average 73% vs 44% for the index (2021) | fool.com.au | No audit; average-per-pick, before costs [1] | **Misleading measure; outcome unproven** |
| 14 | Intelligent Investor models | +0.7% a year over the ASX 200 since 2001 | InvestSMART fact sheet | Its own listed funds trail the index over 3 and 5 years [1] | **Models: small pre-fee edge. Real funds: behind** |
| 15 | Marcus Today; Morgans model portfolios | Not retrieved | — | — | **Unverified** |
| 16 | Simply Wall St | None | Terms | — | **No claim** |
| 17 | Stockspot | Beat 336 of 336 comparable funds over 10 years | Stockspot | Consistent with SPIVA; survivor-only comparison [1] | **Credible; it is the index return** |
| 18 | Tickeron | 116–210% annualised | Own press releases | Short windows, simulations, top-N lists; no audit [2+ that this is the method] | **Misleading** |
| 19 | Trade Ideas Holly AI | Market-beating AI signals | Vendor reports | Simulated, unaudited [1] | **Unproven** |
| 20 | Danelfin | +376% vs +166% since 2017 | Danelfin | Self-labelled backtest [2+] | **Unproven** (backtest) |
| 21 | Kavout; TrendSpider | No specific claim found | — | — | **Unverified** |
| 22 | AIEQ (AI ETF) | AI stock selection | Issuer | Trails the S&P 500 since 2017 [1] | **True record; below index** |
| 23 | 3Commas, Cryptohopper, Pionex | Automated crypto profits; "15–50% APR, extremely low risk" | Vendors | No audited all-user results; APR is extrapolated; 3Commas key leak cost users US$15–22m [1/2+] | **Unproven; "low risk" is misleading** |
| 24 | Composer strategies | Backtest curves | Platform | Own documents call them simulations [1] | **Unproven** (backtest) |
| 25 | Collective2 | Tracked strategy records | Platform | "Hypothetical" label; high system mortality [1] | **Unproven; survivorship** |
| 26 | eToro Popular Investors / CopyTrader | Leader returns on profile pages | eToro | No copier-outcome data; 51–78% of CFD accounts lose; ASIC case pending [1/2+] | **Unproven for copiers** |
| 27 | ZuluTrade | Ranked signal providers | Platform | None found | **Unverified** |
| 28 | Prop-firm challenges | Get funded | Firms | About 7% ever paid [1] | **Misleading** |
| 29 | "AI trading bot" social-media ads (Australia) | Guaranteed passive income | Ads | ASIC: very unlikely to exist; 19,400 takedowns in a year [2+] | **False / scam** |
| 30 | Retail CFD and FX trading | "Trade the markets" | Brokers | 68% lose (Australia 2023–24); 72% (2019); 74–89% (EU) [2+] | **False for most** |
| 31 | Day trading for a living | Courses, finfluencers | — | 97% lose (Brazil); under 1% skilled (Taiwan); 93% lose (India derivatives) [2+] | **False for almost all** |
| 32 | Investment newsletters in general | Stock-picking skill | — | Metrick 1999: none beyond chance [2+] | **False on average** |
| 33 | **Our system (v2.10)** | **None.** "Nothing in this document may be read as a claim of higher returns" | Spec, paragraph 2 | **No live record. No backtest run yet** (H1 untested; G2 not reached) | **Unproven**, and says so |

---

## 7. Our system against each category

**Stated first, because it governs everything below: the system has no live track record and has not yet run its own backtest.** By this report's own framework it fails test A1 today, exactly as Danelfin does. The difference is that it claims nothing. Every "better" below is a statement about design and expected cost, not about results.

### 7.1 Category by category

| Against | Where we are better | Where we are about equal | Where they are better, or could beat us |
| --- | --- | --- | --- |
| **Retail bots and AI signal services** (Tickeron, Holly, Danelfin, crypto bots) | Evidence standard: frozen cards, one primary metric, multiple-testing control, holdout lock, a control hypothesis designed to catch our own false positives (RND-010 to RND-015). They publish best-of lists. No leverage, no derivatives, no crypto. Deterministic; AI never trades (SYS-06). No third party holds an API key that can trade or withdraw, which is the 3Commas failure. Full tax ledger. No subscription fee | Both are automated. Neither has an audited live record | They can make large gains in a strong trend in leveraged or crypto assets, and some users will. We cannot, by design. They need no build effort |
| **Copy trading** (eToro, ZuluTrade, Collective2) | No selection of leaders on luck; no leader incentive to raise risk; no CFDs; assets held in the owner's name at IBKR. Costs known in advance | — | A copier who happens to pick a skilled leader does better. The evidence says that cannot be identified in advance (R06). Zero effort |
| **Scam "AI bots"** | Everything | — | Nothing |
| **Australian newsletters** (Motley Fool, Intelligent Investor) | Our result will be measured as a real, money-weighted, after-cost, after-tax portfolio return against two fixed benchmarks (PRT-22; R33 MON-09), not as an average of picks. No annual fee. No dependence on the reader's discipline in following picks | Honest ones publish benchmark comparisons, as we will | A stock-picking service can beat the index in a given decade; Intelligent Investor's models claim to have. We hold the index, so we cannot beat it by selection. They provide research and education we do not |
| **Active managed funds** | Cost: the ETFs' management fees plus small brokerage, against roughly 1% or more. SPIVA says cost is why 74–87% of them lose to the index. Full transparency of every rule and trade. Tax: parcel-level control and no forced distributions of other investors' gains | Both hold diversified shares. Expected gross return about the same | The 13–26% that do beat the index over long periods. A professional manager handles everything, including when the owner is ill or away (R34 §5.3) |
| **Robo-advisers and auto-invest** (features in R34) | Control and transparency of the rule set; tax-lot handling; no platform fee; the trend overlay, if H1 passes | Same underlying index returns. Stockspot's record is the index, as ours will be | **Convenience, and at A$5,000 probably net return too.** R34 §5.1: a zero-brokerage or low-fee account dominates our STATIC mode at small size because our fixed running costs are several percent of A$5,000 (R13). They need no maintenance and survive the owner's absence |
| **Trend-following funds / CTAs** (Man AHL, AQR, SG CTA Index) | Cost: no 1.5–2.7% fee layer. No leverage. Tax simplicity. Our trend overlay uses the same documented effect (R14) on two share ETFs | Both are rule-based and unemotional. Long-run return expectations are similar or favour us: shares have out-returned CTA indices since 2000 (5.9% vs 4.8%) [1] | **Crisis diversification.** A CTA trades 100+ futures markets long and short and made +13% to +21% in 2008 and +20% in 2022. Our overlay can only step out of shares into cash: it can avoid part of a loss; it cannot profit from one, and in 2022 it had no bond or commodity short. In a slow grinding bear market they are strictly better protection than we are |
| **Elite quant funds** (Medallion, Citadel, D. E. Shaw, Millennium) | We can invest in ours. Cost. Transparency. No pass-through fees, no lock-ups | — | **Return, by a very wide margin, and it is real.** 13–39% a year net over decades. Nothing in our design, at any size, approaches this, and no later version should pretend otherwise |
| **Retail active trading** (CFDs, day trading, options) | Everything measurable: 68–97% of them lose; we hold index funds, trade about monthly at most, and use no leverage | — | The under-1% who are skilled, and anyone who gets lucky in a given year |

### 7.2 Where the system could still lose to doing nothing

These are our own claims, audited the same way.

1. **The trend overlay may reduce return.** R11 and R35 both say it is not a return source; H2 is written to catch a backtest that says otherwise. Over 2000–2024 a buy-and-hold share index beat the trend-follower index. If H1 fails, the system runs STATIC and is an expensive way to hold two ETFs.
2. **Fixed costs at A$5,000 are several percent of capital a year** (R13). Until the account is much larger, B1 in a zero-brokerage account wins on return.
3. **Tax drag from switching** can exceed the drawdown benefit (H11 untested).
4. **Our backtest, when it runs, is still a backtest.** Median live decay across 215 professional strategy indices was 73% of Sharpe [2+]. H12 halves benefits and doubles costs; that is the right direction, and on this evidence it may still be optimistic.
5. **We will not be able to prove the overlay works from live results for a very long time.** At 5% tracking error, a 1%-a-year effect needs about a century to reach t = 2 [computed]. Drawdown differences need several bear markets. PRT-26 and RSK-29 already accept this; the owner should hear it plainly.
6. **Key-person and operational risk.** One maintainer. Even Two Sigma mishandled model controls.

### 7.3 Spec text proposed: hold our own numbers to this report's standard

Not a hypothesis; a reporting rule. Numbering is for the editor.

> **MON-xx Track-record statement.** Every figure the system reports about its own performance carries one of three labels and they are never combined in one number or one chart line: `backtest` (harness output), `paper` (paper_sim), `live` (ledger). A live figure is shown only with: start date and months of record; time-weighted and money-weighted return; after commissions, spreads and running costs entered under PRT-21; after estimated tax (TAX-10 method); the same for B1 and B2 over the same cash flows; maximum drawdown; and the sentence "A record of N months cannot distinguish skill from luck" until N ≥ 120. Every retired or replaced live configuration (including STATIC periods and any period under an owner override) stays in the record; the live history is never restarted. Annualised figures are not shown for periods under 12 months. No performance figure is shared with anyone outside the owner's household without these fields. [R40 §1 tests A1–A8]

This overlaps R33's MON-09 (money-weighted return and benchmarks) and adds the label separation, the survivorship rule, the annualisation rule and the significance sentence.

---

## 8. Techniques the evidence supports that the spec lacks

Screened against R14, R31–R35 so nothing is proposed twice.

| Technique | Who uses it | Evidence | In spec? | Proposal |
| --- | --- | --- | --- | --- |
| Diversified multi-asset trend as a **separate diversifying sleeve** (long and short, 100+ markets) | CTAs: Man AHL, AQR, Aspect, Winton | Positive in 2008 and 2022 [1 to 2+]; correlation to shares about −0.1 [1]; long-run return about 4–5% a year [1 to 2+]; R14 | No. R07 and R10 mention US managed-futures ETFs as a shortcut; D20 defers futures; no card exists | **H60**, Stage 3 only |
| **Pre-registered live expectation** (state in advance what the live record should look like, then score it) | Institutional allocators; GIPS-style reporting; Quantopian's own post-mortem | Backtest-to-live decay of 73% in Sharpe [2+]; backtest metrics barely predict live results [2+]; post-publication decay about a third [2+] | Partly. H12 haircuts the backtest; MON-07 detects implementation decay (live vs replay). Nothing records a dated forecast distribution for the live result | **H61**, META family, no live effect |
| **Counterfactual ledger of manual interventions** | Multi-manager risk desks; behavioural research | Investors' own timing costs about 1.2% a year (R33, Morningstar) [1]; ASIC 2020: retail timing was wrong more often than right [2+]; copied leaders and active traders do worse with more activity [2+] | No. `/veto` and `/kill` exist; R34 §5.7 covers making overrides harder; nothing measures what each override cost or saved | **H62**, META family, no live effect |
| Low turnover as the main durable advantage | AI-run funds beat human peers through 31% vs 72% turnover [2+]; Barber–Odean [2+] | — | Yes (monthly evaluation, bands, H4) | None |
| Cost as the only reliable predictor of fund success | Morningstar: cheapest quintile succeeds most [1]; SPIVA | — | Yes (PRT-21, RSK-26); R34 §5.1 already raises the zero-brokerage point | None |
| Volatility targeting | CTAs, AQR | R14, R15 | Covered by H35 | None |
| Wide signal ensembles | CTAs | R14, R35 | Covered by H30 | None |
| Capacity limits, pass-through fee structures, short-horizon statistical arbitrage, alternative data | Medallion, multi-managers | Real, and unavailable at this scale | Not applicable | **Reject** |
| Leaderboard selection, copy trading, grid bots, leveraged-ETF rotation | Retail platforms | Evidence is negative or absent (§2) | Not applicable | **Reject** |

### H60 — Managed-futures diversifier sleeve (family P1, promotable, Stage 3 only)

| Field | Content |
| --- | --- |
| ID / class | H60 / `promotable` (risk claim, Family A) |
| Economic rationale | Before data: diversified trend following has had near-zero or negative correlation to shares and positive returns in the two largest equity drawdowns since 2000 (2008, 2022), because it can be short shares and bonds and long commodities; our overlay can only go to cash. Counter-rationale: long-run return about 4–5% a year is below shares, so a permanent sleeve lowers expected return; multi-year flat periods (2011–2013, April 2024 to May 2025) test the owner's patience; fund fee about 0.85–1.6%; the product is a managed fund, so this is manager selection with one manager; US-listed ETFs bring FX, Division 775, foreign-income and US estate-tax questions [unverified]; an Australian unit trust brings unlisted-fund dealing, annual tax distributions and no IBKR execution. |
| Exact rule | Static mix V0 of the account's then-current live configuration, with 10% of total weight moved pro rata from the equity sleeves into one managed-futures vehicle, rebalanced under the existing band rule (PRT-16). The vehicle is named in the card at freeze after the access check below; candidates are DBMF or KMLM (US-listed, via the Stage 3 US venue) or Man AHL Alpha (AUD) held outside IBKR and tracked as an external holding. No trend filter is applied to this sleeve. |
| Fixed parameters | Weight 10%; funded from equity sleeves; band as PRT-16. |
| Permitted perturbation grid | Weight {5%, 20%}. Two neighbours. |
| Data and proxy map | SG CTA Index or SG Trend Index monthly returns from 2000 as proxy, converted to AUD, minus the vehicle's fee where the index does not already carry it; licensed data only (R06 A3 notes SG data is fee-liable). If no licensed monthly history is obtained: "not testable" under RND-029, and the card is closed, not approximated. Live ETF history (from 2019–2020) is reported as a short-sample cross-check only. |
| Sample and holdout | 2000-01 to 2023-12; holdout from 2024-01 as RND-025. |
| Benchmark | The same configuration without the sleeve; B2 reported. |
| Primary metric (one) | Maximum drawdown difference against the benchmark, in AUD, after costs and tax. |
| Secondary metrics | After-tax CAGR difference; 2008 and 2022 calendar-year rows; worst rolling 36-month shortfall against B2; correlation of the sleeve to the equity sleeves; AUD/USD contribution; all-in fee paid. |
| Pass threshold | Maximum drawdown at least 3 points lower; after-tax CAGR no more than 0.5 points lower; drawdown benefit present in both 2008 and 2022; passes H12 (benefit halved, costs doubled). |
| Fail threshold | Drawdown improvement under 1 point, or CAGR more than 1.0 point lower. |
| Multiple-testing family and adjustment | Family A; Holm within its promotion window. Strategy family `P1`. |
| Trials consumed | 3 |
| Preconditions (not part of the test) | Stage 3 entry conditions met (section 27); written confirmation that IBKR Australia lets a retail client buy the named ETF, or that the unit trust accepts the investment; tax agent's view on foreign income, forex and US estate-tax exposure recorded. At A$5,000 this card is not run: 10% is A$500, below the minimum order. |

### H61 — Pre-registered live expectation (family META, measurement only)

| Field | Content |
| --- | --- |
| ID / class | H61 / `measurement` (cannot promote or demote a rule) |
| Economic rationale | Before data: backtests overstate live results (median 73% Sharpe decay across 215 professional strategy indices; near-zero predictive power of backtest Sharpe across 888 algorithms). A forecast written before go-live is the only way to tell, years later, whether the live record was "as expected" without moving the goalposts. Counter-rationale: the live sample will be too short for a sharp test for a decade; the value is mainly discipline. |
| Exact rule | At G2, when H1's backtest result is first known and before the first live order, the harness writes a frozen forecast file for the live configuration: for horizons of 12, 36, 60 and 120 months, the 5th, 25th, 50th, 75th and 95th percentiles of (a) return difference against B2 after costs and tax, (b) maximum drawdown difference against B2, (c) number of switches, (d) commissions as a percent of NAV. Percentiles come from the stationary bootstrap already used for RND-012, applied to backtest results **after** the H12 haircut (benefit halved, costs doubled). The file is hashed with the card set. Each monthly report plots the live value against the frozen band. |
| Fixed parameters | Horizons and percentiles above; haircut as H12; bootstrap settings as RND-012. |
| Permitted perturbation grid | None. |
| Data and proxy map | As H1. |
| Benchmark | B2. |
| Primary metric (one) | Share of the four horizon checkpoints at which the live return difference lies inside the frozen 5th–95th band. |
| Secondary metrics | The same for drawdown difference, switches and cost. |
| Pass threshold | None (measurement). Reporting rule: a live value outside the 5–95 band at any checkpoint is reported to the owner as "outside expectation" and triggers the MON-07 implementation check first, then a written review. It does not by itself change the rule (PRT-26 stands). |
| Fail threshold | None. |
| Multiple-testing family and adjustment | Not a test of a strategy; no trials consumed against any strategy family. Family `META`. |
| Trials consumed | 0 (uses H1's runs) |

### H62 — Counterfactual ledger of owner interventions (family META, measurement only)

| Field | Content |
| --- | --- |
| ID / class | H62 / `measurement` |
| Economic rationale | Before data: discretionary timing by individuals costs return on average (behaviour gap about 1.2% a year; ASIC's 2020 finding that retail net buying preceded falls and net selling preceded rises). The system's main claimed value is discipline; an override is the one place discipline can leak. Counter-rationale: some overrides are correct and necessary (a real emergency; a data fault the code missed); a ledger that shames every intervention could make the owner slow to use the stop when it matters. |
| Exact rule | Every `/veto`, `/kill`, manual order at the broker, pause, skipped contribution and manual withdrawal is recorded with a timestamp, a reason chosen from a fixed list (`safety`, `data_fault`, `cash_need`, `market_view`, `other`) and free text. `paper_sim` continues to run the unmodified rule from the same starting state. At 1, 3, 12 and 36 months after each event the report shows the dollar difference between the actual account and the unmodified path, after costs and estimated tax. Interventions with reason `safety` or `data_fault` are shown separately and are never summed into a "cost of overrides" figure. |
| Fixed parameters | Reason list; horizons 1, 3, 12, 36 months. |
| Permitted perturbation grid | None. |
| Data and proxy map | Live ledger and `paper_sim`. |
| Benchmark | The unmodified rule path. |
| Primary metric (one) | Cumulative dollar difference, `market_view` interventions only, at the 12-month horizon. |
| Secondary metrics | Count by reason; the same at other horizons; share of interventions that helped. |
| Pass threshold | None (measurement). Reporting rule: the cumulative figure appears in the annual review. No automatic consequence. |
| Fail threshold | None. |
| Multiple-testing family and adjustment | Family `META`; no trials consumed. |
| Trials consumed | 0 |

Trial cost of this report's cards: H60 3, H61 0, H62 0 = **3 trials** [computed]. H60 is run only at Stage 3, so it adds nothing to the hurdle at G2.

---

## 9. What our system does better — and what it doesn't

Written for the owner.

**What nobody should tell you.** Nobody selling a bot, a signal, a course or a newsletter has shown, to the standard of an audited fund, that their customers make more than an index fund. The people who verifiably do make extraordinary money from systematic trading — Medallion, Citadel, D. E. Shaw — do not sell it; they have closed their doors and hand money back. That is how you can tell.

**What our system is.** Two low-cost index funds, checked once a month by fixed rules, with a full record of every trade and every dollar of tax. It makes no promise of beating the market, and it has not traded a dollar yet. It has no track record. When it has one, the first several years will not be long enough to prove anything.

**What it does better than the alternatives:**

1. **Cost.** No management fee beyond the ETFs' own, no performance fee, no subscription. Cost is the one thing every study agrees predicts results.
2. **It avoids the proven ways to lose.** No leverage, no CFDs, no options, no crypto, no day trading. In Australia 68% of CFD clients lost money last measured year; you cannot be one of them.
3. **Honesty of measurement.** Results will be shown after all costs and tax, beside two do-nothing benchmarks, with no restarting the clock and no best-of lists. Almost none of the products in this report do that.
4. **Evidence standard.** Every rule must pass a test written down before the data is looked at. If the trend rule fails its test, the system drops it and just holds the funds. Vendors do the opposite: they test until something looks good and publish that.
5. **Control and safety.** Your money sits in your own name at a large regulated broker. No outside service can trade or withdraw. You can read every rule. AI does not make trading decisions.
6. **Tax.** A parcel-by-parcel ledger built for the Australian rules. No fund, robo-adviser, bot or newsletter does this for you at this level.

**Where it is about the same:**

1. **Return.** Expect the market's return minus small costs. That is what a robo-adviser or a single diversified ETF gives too.
2. **Discipline through automation.** Robo-advisers and auto-invest plans also remove the temptation to tinker.

**Where others are better, or could beat it:**

1. **The elite funds make far more. You cannot invest in them.** This is real and will stay true.
2. **A diversified trend-following fund protects better in a long bear market.** It can make money when shares and bonds both fall, as in 2022. Ours can only step aside into cash, and only if its rule passes testing. The price of their protection is a fee of 1–2% and a long-run return below shares. Card H60 tests whether a small slice of one is worth adding once the account is large.
3. **A robo-adviser or a zero-brokerage ETF account is easier and, at A$5,000, probably cheaper.** Our fixed running costs are several percent of A$5,000 a year. That is the price of learning and of building something that can scale; it is not a saving.
4. **A good stock-picker or newsletter can beat the index in a given decade.** We never will by picking, because we hold the whole index. The odds are against finding that picker in advance: about three in four Australian share funds lost to the index last year and about six in seven over fifteen years.
5. **Someone who gambles with leverage and gets lucky will beat it in any given year.** Most who try lose.
6. **It depends on one person to maintain it.** A fund or a robo-adviser keeps running if you are ill or lose interest.

**The fair one-line summary.** This system is designed to reliably get the market's return, cheaply, safely and with good records, and perhaps with smaller falls along the way. That is less than the advertisements promise and more than most people who respond to them end up with.

---

## 10. What could be wrong, and what to re-check

1. **No primary document was opened today.** The network block on ASIC, S&P and Morningstar means REP 626, REP 828, SPIVA and the barometer figures rest on search extracts. They agree across sources, and the direction is not in doubt, but exact percentages should be re-read from the PDFs before any is quoted outside the project.
2. **SPIVA 15-year figure:** 85% (mid-2025) and 87% (one summary of year-end 2025). Use "about 85%" until the PDF is read.
3. **ASIC retail options and day-trading studies for 2022–2024** named in the brief were not found. Either they do not exist under those descriptions or the search missed them.
4. **Medallion's averages are arithmetic and partly from a book, not an audit.** The fund files regulatory forms, and several outlets have seen investor documents, so [2+] is fair for "about 66/39"; the precise numbers are not audited public data.
5. **CTA long-run return (4.8% a year) is one source** (Morningstar) with a consistent second figure for the sister index (4.9%). A licensed SG series is needed for H60 in any case.
6. **Winton, Millennium long-run, Marcus Today, Morgans, Kavout, TrendSpider, ZuluTrade:** no usable figures today. They are marked unverified, not judged.
7. **Motley Fool AU and Intelligent Investor numbers are the firms' own.** No independent measurement exists that I could find. The verdicts are about the method of measurement, which is documented, not about bad faith.
8. **eToro copier outcomes:** absence of published data is not evidence of losses. The academic literature (R06) is the basis for the caution.
9. **"No retail bot passes A1–A4"** is a statement about the firms examined, not a proof about all firms.
10. **H60's access and tax preconditions are unverified:** whether IBKR Australia lets a retail client buy DBMF or KMLM; US estate-tax exposure on US-domiciled ETFs; the current retail minimum and fees of Man AHL Alpha (AUD).

---

## 11. Sources

Reached through search extracts only; no page was fetched in full (see access limit at the top).

**Regulators and retail outcomes**
- ASIC REP 626 (2019): https://download.asic.gov.au/media/5241548/rep626-published-22-august-2019.pdf ; coverage https://www.moneymanagement.com.au/news/financial-planning/asic-calls-otc-derivatives-sector-improve-practices
- ASIC 22-082MR, CFD order extended: https://asic.gov.au/about-asic/news-centre/find-a-media-release/2022-releases/22-082mr-asic-s-cfd-product-intervention-order-extended-for-five-years/ ; https://financefeeds.com/asic-renews-cfd-restrictions-91-reduction-retail-losses/
- ASIC REP 828 (January 2026): https://download.asic.gov.au/media/tq0he35c/rep828-published-20-january-2026.pdf ; 26-004MR https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-004mr-asic-secures-nearly-40-million-in-refunds-to-investors-and-drives-change-after-cfd-sector-falls-short/ ; https://fnarena.com/index.php/2026/01/22/asic-watch-cfd-sector-faces-40m-refund-bill ; https://www.financemagnates.com/forex/etoro-dominates-australias-cfd-market-where-trader-loyalty-rarely-survives-a-year
- ASIC CS 64 / 26-239MR (October 2026): https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-239mr-asic-moves-to-extend-and-strengthen-cfd-consumer-protections ; https://www.gtlaw.com.au/insights/key-topics/regulation-in-motion/asic-proposes-to-extend-and-strengthen-the-cfd-product-intervention-order
- ASIC, Retail investor trading during COVID-19 volatility (May 2020): https://download.asic.gov.au/media/5584799/retail-investor-trading-during-covid-19-volatility-published-6-may-2020.pdf ; 20-102MR https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2020-releases/20-102mr-retail-investors-at-risk-in-volatile-markets
- ASIC 26-195MR (AI scams, August 2026): https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-195mr-asic-warns-scammers-are-using-ai-to-spin-vast-webs-of-deception ; 26-063MR https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-063mr-asic-ramps-up-action-to-protect-consumers-from-ai-powered-online-investment-scams/ ; https://financemagnates.com/forex/regulation/australia-and-new-zealand-sound-alarm-on-ai-powered-investment-scams-as-takedowns-hit-record-pace
- ASIC finfluencers: https://www.ifa.com.au/court-makes-permanent-injunctions-against-finfluencer ; https://smsmagazine.com.au/news/2025/06/12/asic-moves-against-18-finfluencers/
- ASIC v eToro: 23-204MR https://asic.gov.au/about-asic/news-centre/find-a-media-release/2023-releases/23-204mr-asic-sues-etoro-in-its-first-design-and-distribution-action-to-protect-consumers-from-high-risk-cfd-products/ ; [2025] FCA 904 https://www.judgments.fedcourt.gov.au/judgments/Judgments/fca/single/2025/2025fca0904
- CFTC advisory (January 2024): https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html ; https://www.cftc.gov/PressRoom/PressReleases/8854-24
- SEC v Two Sigma (January 2025): https://www.sec.gov/newsroom/press-releases/2025-15
- ESMA / FCA CFD loss rates: https://www.consob.it/documents/1912911/1970971/esma35_43_1000.pdf/6dc9bc30-c528-09dc-9430-398c8df4c3af ; https://www.fca.org.uk/publication/consultation/cp18-38.pdf
- SEBI (September 2024): https://www.sebi.gov.in/media-and-notifications/press-releases/sep-2024/updated-sebi-study-reveals-93-of-individual-traders-incurred-losses-in-equity-fando-between-fy22-and-fy24-aggregate-losses-exceed-1-8-lakh-crores-over-three-years_86906.html
- Chague, De-Losso, Giovannetti, "Day Trading for a Living?": https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101 ; https://quantpedia.com/?p=4771
- Barber, Lee, Liu, Odean (2014): https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html ; https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf
- Barber and Odean (2000): https://faculty.haas.berkeley.edu/odean/papers/returns/Returns.html
- SPIVA Australia year-end 2025: https://www.spglobal.com/spdji/en/documents/spiva/spiva-australia-scorecard-year-end-2025.pdf ; https://financialnewswire.com.au/funds-management/three-quarters-of-active-managers-underperformed/ ; https://www.reviewetf.com.au/blog/active-vs-passive-etfs-the-data-that-settles-the-debate
- Morningstar Active/Passive Barometer: https://www.morningstar.com/funds/better-conditions-did-not-yield-better-results-active-managers-2025 ; https://www.investmentnews.com/practice-management/active-managers-face-shrinking-odds-of-beating-indexes-morningstar-finds/265335
- Metrick (1999): https://nber.org/papers/w6648 ; https://ideas.repec.org/a/bla/jfinan/v54y1999i5p1743-1775.html

**Backtest versus live**
- Wiecki et al. (2016), 888 algorithms: https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/ ; https://www.cxoadvisory.com/big-ideas/in-sample-vs-out-of-sample-performance-of-888-trading-strategies ; https://www.quantrocket.com/blog/quantopian-shutting-down/
- Suhonen, Lennkh, Perez (2017): https://alphaarchitect.com/?p=36892 ; https://mathinvestor.org/2017/08/backtest-overfitting-in-smart-beta-investments/
- McLean and Pontiff: https://www.cxoadvisory.com/big-ideas/effects-of-market-adaptation

**Retail products**
- Tickeron press releases: https://tickeron.com/trading-investing-101/ai-trading-agent-achieves-116-annualized-return-on-aapl-amd-nvda-ebay-stx/ ; https://tickeron.com/trading-investing-101/tickeron-ai-trading-robots-post-159-annualized-returns-with-90-win-rates-on-leveraged-etfs-in-2025/
- Trade Ideas Holly reviews: https://www.liberatedstocktrader.com/trade-ideas-review/ ; https://daytradingtoolkit.com/day-trading-basics/ai-trading-bots-truth-vs-hype
- Danelfin: https://danelfin.com/how-it-works ; https://blog.danelfin.com/?p=5049 ; https://support.danelfin.com/hc/en-us/articles/4404382344465-Are-AI-Scores-reliable-How-successful-were-AI-Scores-predictions-in-the-past
- AIEQ: https://www.techbrew.com/stories/2022/01/26/how-the-world-s-first-ai-managed-etf-stacks-up-almost-five-years-later ; https://seekingalpha.com/article/4702788-aieq-mobilizing-ai-resources-for-disappointing-results ; https://portfolioslab.com/tools/stock-comparison/AIEQ/SPY
- Chen and Ren (2022): https://alphaarchitect.com/ai-funds/ ; https://marginalrevolution.com/marginalrevolution/2021/12/do-ai-powered-mutual-funds-outperform-the-market.html ; https://www.morningstar.com.au/insights/markets/255657/can-ai-predict-future-stock-returns
- 3Commas: https://decrypt.co/118094/after-repeated-denials-3commas-admits-it-was-source-for-earlier-hacks/ ; https://cointelegraph.com/news/3commas-ceo-confirms-api-key-leak-following-warning-from-cz ; https://halborn.com/explained-the-3commas-breach-december-2022/
- Cryptohopper: https://support.cryptohopper.com/en/articles/9197405-can-i-see-how-trading-strategies-perform-before-purchasing-them
- Pionex: https://finbold.com/review/pionex-review/
- Composer: https://www.composer.trade/learn/how-do-backtests-work-in-composer ; https://help.composer.trade/article/215-7-how-do-backtests-work-in-composer
- Collective2: https://www.cxoadvisory.com/?p=4128
- Social trading: Dorfleitner et al. (2018) https://ideas.repec.org/a/eee/quaeco/v70y2018icp160-171.html ; https://www.aaii.com/journal/article/returns-for-social-trading-platforms-are-negative
- Prop firms: https://tradeinformer.com/prop-weekly/what-ftmo-tells-us-about-prop-firm-finances ; https://invezz.com/news/2026/07/24/a-review-of-six-prop-firms-rulebooks-why-funded-traders-rarely-get-paid/

**Australian newsletters and services**
- Motley Fool AU: https://fool.com.au/2021/12/07/an-auspicious-day ; https://fool.com.au/2021/02/26/some-of-my-best-gains-last-year-were-invisible ; https://www.fool.com.au/2017/04/26/is-motley-fool-share-advisor-worth-the-money/
- Intelligent Investor / InvestSMART: https://www.investsmart.com.au/investment-news/the-key-to-a-15-year-track-record-of-outperformance/138295 ; https://cdn-blob.investsmart.com.au/distributions/documents/2025-08-06%20Fact%20sheet-INIF_20250806_1430.pdf ; https://cdn-blob.investsmart.com.au/distributions/documents/2025-04-30%20IIGF%20Factsheet_20250507_1607.pdf ; https://www.investsmart.com.au/shares/asx-inif/intelligent-investor-aus-equity-income-fund-managed-fund/fund-details/24277
- Simply Wall St: https://simplywall.st/termsandconditions
- Stockspot: https://blog.stockspot.com.au/stockspot-performance-update-june-2025/

**Professional managers**
- Medallion and RIEF: https://www.institutionalinvestor.com/article/2bswymr8cih3jeaslxc00/portfolio/famed-medallion-fund-stretches-explanation-to-the-limit-professor-claims ; https://www.institutionalinvestor.com/article/2bswms7wco7as686o8ikg/portfolio/renaissances-medallion-fund-surged-76-in-2020-but-funds-open-to-outsiders-tanked ; https://www.morningstar.com/columns/rekenthaler-report/medallion-fund-is-like-no-other ; Cornell, SSRN 3504766
- Citadel, Millennium: https://www.bloomberg.com/news/articles/2026-01-02/citadel-s-flagship-hedge-fund-wellington-climbed-10-2-last-year ; https://www.hedgeweek.com/millennium-and-citadel-post-double-digit-2025-gains-but-lag-smaller-hedge-funds/ ; https://www.nbcchicago.com/news/business/money-report/billionaire-ken-griffins-hedge-funds-at-citadel-are-all-in-the-green-for-2025/3780143/
- Pass-through fees: https://www.bloomberg.com/graphics/2025-hedge-fund-investment-fees/ ; https://www.fxempire.com/news/article/multi-manager-hedge-funds-offer-big-returns-but-at-high-cost-1278303 ; https://www.hedgeweek.com/investors-push-back-on-multi-strategy-hedge-fund-fee-structures/
- D. E. Shaw: https://wsau.com/2026/01/02/d-e-shaws-flagship-funds-trump-market-volatility-to-beat-sp-500-in-2025-source-says/ ; https://bnnbloomberg.ca/business/company-news/2025/01/02/de-shaw-to-return-billions-after-flagship-hedge-fund-gains-18
- AQR Managed Futures: https://funds.aqr.com/funds/aqr-managed-futures-strategy-fund ; https://www.zacks.com/funds/mutual-fund/quote/AQMIX/performance
- Man AHL Alpha (AUD): https://www.gsfm.com.au/fund-hub/man-ahl-alpha-aud-fund ; https://www.investsmart.com.au/managed-funds/fund/mahlalphaudca/17475 ; Aspect https://investsmart.com.au/managed-funds/fund/aspect-diversified-futures/17745
- SG CTA and SG Trend: https://www.morningstar.com/funds/managed-futures-open-new-frontier-etfs ; https://www.hedgeweek.com/flat-december-sees-ctas-complete-record-year-2022/ ; https://www.cfm.com/steady-trends-the-reality-of-cta-return-dispersion/ ; https://www.toptradersunplugged.com/trend-following-performance-report-june-2025/ ; https://autumngold.com/SubLeaf/gold_report.php?id=114703 ; https://hedgenordic.com/2023/03/bringing-back-crisis-alpha/
- Barclay CTA Index: https://www.barclayhedge.com/pr_jan_20_2009/ ; https://barclayhedge.com/insider/pr_jan_22_2008
- Managed-futures ETFs: https://totalrealreturns.com/n/KMLM,DBMF,SPY ; https://portfolioslab.com/tools/stock-comparison/DBMF/KMLM
- Hedge funds vs 60/40: https://www.cxoadvisory.com/mutual-hedge-funds/recent-hedge-fund-performance-and-research ; https://www.aqr.com/-/media/AQR/Documents/Insights/Perspectives/Cliffs-Perspective-05302018.pdf
