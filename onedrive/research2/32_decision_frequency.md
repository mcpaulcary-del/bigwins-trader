# 32. Decision frequency and fast-crash protection: daily vs weekly vs monthly

Date: 2026-11-13. Scope: how often the L1 core (VAS 40 / VGS 60, three-vote trend filter) should decide and trade, whether a daily "emergency brake" earns its place, what that costs at A$5,000 / A$25,000 / A$100,000 after brokerage and Australian CGT, and whether intraday monitoring adds anything. The momentum / "big winners" satellite and crash-rebound predictability are report 31's subject; here they appear only where frequency is the question.

## 0. Answer first

1. **Check daily, trade monthly.** The evidence does not support trading a slow trend filter more often than monthly. Every study found that compares daily with monthly evaluation of a long (roughly 200-day / 10-month) rule on an equity index finds no net advantage to daily, and several find monthly better. Daily evaluation multiplies switches by roughly 4 to 6 times and each extra switch is a whipsaw.
2. **A daily emergency brake is not supported as a live rule.** Stop-loss and volatility-trigger overlays lower return unless returns trend strongly, tight triggers lose after costs, and the two most recent fast crashes (March 2020, April 2025) reversed fast enough that an exit was followed by buying back higher. It is worth testing as a registered hypothesis and running in shadow (report-only) mode. It is not worth switching on.
3. **At A$5,000 the costs settle it regardless.** One full round trip costs about 0.64% of the account. A daily 200-day rule at about 3.8 round trips a year costs about 2.4% a year in brokerage and spread alone, breaks the spec's own order-count halt (RSK-26), loses the CGT discount on every parcel, and strengthens the ATO's case that the account is a share-trading business.
4. **What the owner can have daily:** a daily decision record. The system already fetches and validates data every trading day. Add a daily computation of votes, distance to each switch and the shadow brake state to the 08:10 run and the 20:00 digest. That is a decision every day ("hold, because …") with an order only when the monthly rule says so.
5. **Intraday: no.** Signals are defined on closes, real-time ASX data costs A$300 a year (6% of A$5,000), and most of VGS's information arrives as an opening gap that intraday monitoring cannot get ahead of.

## 0.1 Access caveats

- **Blocked hosts** (proxy 403 or not resolvable from this session): cxoadvisory.com, alphaarchitect.com, blog.thinknewfound.com, openaccess.city.ac.uk, bayes.citystgeorges.ac.uk, york.ac.uk, dspace.mit.edu, lehigh.edu, spiral.imperial.ac.uk, researchaffiliates.com, mebfaber.com, advisoranalyst.com, awealthofcommonsense.com, algostrategylab.github.io, r-bloggers.com, ncbi.nlm.nih.gov, ato.gov.au (403), rstudio.uia.no. They need allowing in the session's network settings for a full-text pass.
- **Read directly today:** IBKR Australia market-data pricing page; IDEAS/EconPapers abstracts for Clare et al., Kaminski–Lo, Cederburg et al., Dai et al.; NBER w22208 (Moreira–Muir, full PDF); arXiv 2507.04481 abstract; the ASX Investment Products reports for September and October 2026 already stored in `scratchpad/dl_asx/`; AQR "Demystifying Managed Futures" (stored text from report 14).
- **Read only as search-engine extracts:** everything else. Where a figure comes from an extract I say so. No table from Clare et al. (2013), Zakamulin (2017), Faber (2007) or Lo–Remorov (2017) was read in full.
- **No price data was reachable** (Yahoo and Stooq are blocked). The episode walk-throughs in section 3 use index levels recalled from memory and are tagged [unverified]. They are predictions for the harness to confirm, not results.

Tags: **[2+]** two or more independent sources; **[1]** one source (several summaries of one paper count as one); **[unverified]** my inference, recollection or arithmetic on recalled inputs; **[computed]** arithmetic on verified inputs.

## 1. Claim table

| # | Claim | Tag | Sources |
|---|---|---|---|
| C1 | On the S&P 500, end-of-month decision rules beat rules that trade more often: "monthly end of month investment decision rules are superior to those which trade more frequently" | [2+] | Clare, Seaton, Smith, Thomas (2013) abstract [S1]; Zakamulin (2017) as summarised by Alpha Architect: daily better in back-tests, monthly better in forward tests, "no evidence" daily is better [S2] |
| C2 | For signals longer than about 100 days there is no risk-adjusted advantage to daily over monthly calculation; monthly had higher return and lower volatility. Net Sharpe 0.06 to 0.59 for monthly SMA rules against −0.79 to 0.54 for daily, at 0.2% a trade | [1] | Clare et al. (2013) via two secondary summaries [S1], [S3]; figures from search extracts only |
| C3 | For diversified **futures** trend portfolios, daily and weekly rebalancing "perform similarly, while the performance trails off with monthly and quarterly" | [1] | Hurst, Ooi, Pedersen (2013) [S4], read in full in report 14. Futures, long-short, vol-sized, 1- to 12-month signals: not the L1 case |
| C4 | A daily close-vs-200-day rule on SPY trades far more than a monthly rule: SPY crossed its 200-day average over 150 times since 2000; a close/200-day system made 83 trades in about 22 years (about 3.8 a year) with a 34% win rate; smoothing with a 5-day average cut that to 31 trades | [1] | StockCharts / TrendInvestorPro (2022) [S5]. A forum back-test reports 5–6 trades a year and 18% of trades one day apart [S6], anecdotal |
| C5 | A month-end 10-month SMA makes under one round trip a year | [unverified] | Recollection of Faber (2007); the search could not confirm the figure. Carver's slowest crossover trades 1.1 times a year (report 14 #12) |
| C6 | Rebalance-date choice alone moves a 10-month SMA result a lot: best vs worst day-of-month offset gave total returns of 717% vs 463%; one day's shift moved max drawdown from 19.0% to 30.2% and annual return from 11.33% to 10.51% | [1] | Hoffstein, Newfound (2013) [S7], search extract |
| C7 | Tranching (staggered sub-portfolios) cuts timing luck by about 1/N and is the standard remedy; Newfound runs daily signals through 21 overlapping one-month tranches rather than acting all-in each day | [2+] | Newfound [S7], [S8]; Hoffstein, Faber, Braun (2019/2020) [S9]; the spec's H5 already tests it |
| C8 | Acting on a signal every day implicitly assumes a one-day forecast horizon; trend signals work over about a month | [1] | Newfound (March 2020) [S8], search extract |
| C9 | In March 2020 trend-equity implementations dispersed widely: some went fully to cash at end-February, some stayed invested; execution timing moved results by "hundreds of basis points"; in 12 of 14 asset classes a 20-day tranche did no worse than acting immediately | [1] | Newfound notes, March–April 2020 [S8], search extracts |
| C10 | Stop-loss rules reduce expected return when returns are a random walk; they add value only under momentum or regime switching. On monthly US equity data 1950–2004 (bonds as the stop-out asset) certain rules added 50–100 bp a month during stop-out periods | [2+] | Kaminski & Lo (2014) abstract [S10] and working-paper abstract via search [S11] |
| C11 | Tight stop-losses underperform buy-and-hold because of trading costs; wide ones roughly match it on risk-adjusted terms with lower raw return. A one-day delayed execution did marginally better than immediate | [2+] on tight-stop underperformance | Lo & Remorov (2017) [S12]; Dai, Marshall, Nguyen, Visaltanachoti (2021) [S13]: trailing stops have "inferior mean returns", reduce downside risk, and "transaction costs reduce the benefits of tighter stop-loss rules" (benefit gone below about 10%, per a secondary summary) |
| C12 | On the S&P 500, adding popular stop-loss rules (breakout, trailing, purchase-cost) to a 200-day rule "do[es] not add value" | [1] | Clare et al. (2013) abstract [S1] |
| C13 | Volatility-managed portfolios show large in-sample alphas (Moreira–Muir) that survive modelled transaction costs | [1] | Moreira & Muir (2017), NBER w22208, read in full [S14] |
| C14 | Those gains are not available in real time: managed versions beat unmanaged on Sharpe in only 53 of 103 strategies (8 significant); out-of-sample versions were worse in 72 of 103 | [2+] | Cederburg, O'Doherty, Wang, Yan (2020) abstract [S15] plus search extract of the paper; Liu, Tang, Zhou (2019): look-ahead bias in the scaling constant, corrected max drawdown 68–93%, outperforms only in the financial crisis [S16] |
| C15 | Volatility targeting does help equities modestly and thins the left tail: US equity Sharpe 0.40 unscaled vs 0.48–0.51 scaled; the mechanism is the leverage effect, so it "introduces some momentum" | [2+] | Harvey et al. (2018) [S17] via report 14 #8 and search extract; consistent with C13 in sign |
| C16 | A 6–9 month trend system does not hedge a crash that lasts days; trend commonly loses in the first leg of a crisis | [2+] | Dao et al. (2016), Man Group (2025), both in report 14 (#11, #14) |
| C17 | Large up days cluster next to large down days: 6–7 of the S&P 500's 10 best days in 20 years fell within two weeks of the 10 worst | [2+] | J.P. Morgan Guide to Retirement, several editions, via press summaries [S18] |
| C18 | S&P 500, 2025: first close below the 200-day average since November 2023 on 10 March 2025; closed below its 12-month average on 31 March; +9.52% on 9 April; all of April's tariff loss recovered within weeks | [2+] | Briefing.com / Reuters (10 March) [S19]; Alpha Architect and others [S20] |
| C19 | 1987: the S&P 500 closed below its 200-day average on Friday 16 October, the session before the −20.5% day; a month-end rule was still fully invested and finished the episode down about 24% | [2+] on the 16 October break; [1] on the month-end outcome | Technical write-up and a second secondary account [S21]; one independent back-test [S22]. One source claims the Faber rule "exited 16 October", which is true only of a daily version |
| C20 | VAS and VGS quoted spreads average 0.02% (ASX-reported, September and October 2026); AAA 0.02%, BILL 0.01–0.02% | [2+] | ASX Investment Products reports, Sep and Oct 2026 (local copies) [S23]; Stockspot lists VAS at 0.02% [S24] |
| C21 | IBKR: ASX Total (L1, L2) is AUD 25.00 a month non-professional; without it ASX data is delayed 20 minutes; snapshots are USD 0.03 each for non-US instruments with a USD 1.00 monthly waiver | [2+] | IBKR Australia pricing page fetched today [S25]; report 13 |
| C22 | IBKR fixed ASX commission 0.08%, minimum A$6.00, GST treatment unsettled; the spec models max(A$6.60, 0.088%) | [2+] | Report 13; spec RND-021 |
| C23 | ATO: repetition, volume and regularity of transactions are markers of a share-trading business; holding periods and dividend intent point to investor | [2+] | ATO "Share investing versus share trading" (via search; page 403 from here) [S26]; report 18 priority 1 |
| C24 | Nearly all the US equity premium over 30 years was earned overnight; intraday returns averaged flat or negative | [2+] | arXiv 2507.04481 abstract [S27]; Cliff, Cooper, Gulen (2008) and Lou, Polk, Skouras (2019) via search [S28] |
| C25 | A parcel held under 12 months gets no CGT discount before 1 July 2027 and no indexation after; a 30% minimum tax applies to post-July-2027 capital gains | [2+] | Report 18 (statute text) |

**Disagreements found**

- **Futures vs equity index.** C3 (daily ≈ weekly > monthly) and C1/C2 (monthly ≥ daily) point in opposite directions. They are not the same experiment. C3 is a 58-market long-short portfolio that includes 1-month signals, where the delay cost on the fast signal is real and costs are in basis points. C1/C2 is a single index with a 200-day signal and a retail cost. L1 is the second case. [unverified — my reconciliation]
- **1987.** Sources disagree on whether "the 10-month rule" avoided the crash. The disagreement is exactly the daily-vs-monthly question: the daily 200-day version signalled on the Friday close, the month-end version did not.
- **Volatility management.** Moreira–Muir (C13) against Cederburg et al. and Liu et al. (C14). The critiques are about real-time implementability and are the later, larger studies. Harvey et al. (C15) sits between them.

## 2. What the evidence says about frequency

### 2.1 The signal is slow, so the evaluation need not be fast

L1's votes use 6-month and 12-month returns and a 10-month average. A day's price moves a 10-month average by about 1/210 of the gap between today's price and the price leaving the window. Evaluating such a signal daily adds almost no information; what it adds is opportunities to cross the threshold and cross back. That is the mechanism behind C1, C2 and C4. [unverified — reasoning; consistent with the cited results]

### 2.2 Switches per year

| Rule | Evaluation | Round trips a year | Tag |
|---|---|---|---|
| L1 three votes with hold zone (off at 0, on at ≥ 2) | Month-end | About 0.2–0.4 expected | [unverified — to be measured by H1/H3] |
| 10-month SMA | Month-end | Under 1 (about 0.6) | [unverified], C5 |
| 200-day SMA with 5-day smoothing | Daily | About 1.4 (31 trades in 22 years) | [1], C4 |
| 200-day SMA, raw close | Daily | About 3.8 (83 trades in 22 years); 5–6 in a forum test | [1], C4 |

A 1% band around the average is reported to cut the raw daily trade count by about 60% [1, forum source S6]. Bands and smoothing work by making the daily rule behave like a slower-sampled one, which is what monthly evaluation already is.

### 2.3 Net results where reported

- Clare et al. (S&P 500, 1988–2011 daily; 1952–2011 monthly, 0.2% a trade): monthly rules ahead of daily ones; best 200-day-type rule about 10.7% a year, Sharpe about 0.58 [1, search extract].
- Zakamulin: timing rules give "higher Sharpe ratios than buy-and-hold despite lower mean returns" (report 14 #15); in about 80% of exit-to-re-entry intervals the timing rule underperformed buy-and-hold [1, CXO summary via search]. That 80% is the whipsaw rate: four exits in five are bought back higher.
- No source reports a net return or drawdown gain from weekly over monthly evaluation of a long-only index filter. The only weekly evidence is from futures (C3). [gap]

### 2.4 Drawdown: where daily helps and where it does not

| Episode | Daily 200-day rule | Month-end 10-month SMA | L1 three-vote rule, month-end (prediction) |
|---|---|---|---|
| October 1987 | Signal on Friday 16 Oct close [2+]. Helps only with execution at that close; a next-day order sells into the crash | Fully invested; about −24% [1] | 12-month vote still positive at end-October, so 1 vote = hold. Off at end-November, near the low; back on mid-1988 at higher prices. No protection [unverified] |
| 2008 | Out around the turn of 2007–08 | Out around December 2007 – January 2008 | Off at end-January 2008, on again around end-May 2009. Works, as slow bear markets do [unverified] |
| February–March 2020 | Out 27 February, about 12% below the high; back in late May a few percent higher | Out at end-February, back at end-May. Same result, by luck of the calendar: the fall began ten days before a month-end [unverified] | Still 2 votes at end-February. Off at end-March, near the low; back on at end-May for the S&P 500, about 17% higher in USD. A clear whipsaw. The Australian sleeve re-enters later still [unverified] |
| April 2025 | Out 10 March [2+], at least one false re-cross in late March, back in mid-May about 4–5% higher in total [unverified] | Out at end-March [2+], back at end-May about 5% higher [unverified] | 12-month vote stays positive: 1 vote = hold. Never sells. The hold zone avoids the whipsaw entirely [unverified] |

Reading across:

- Daily evaluation is decisively better in exactly one episode (1987), and only if the order executes on the signal day's close. The spec decides at 08:10 and submits at 11:30 the next session, which in 1987 was the crash day.
- In 2008, 2020 and 2025 daily and monthly 200-day-type rules end within a few percent of each other.
- L1's hold zone is what differs. It avoided the 2025 whipsaw and made the 2020 one worse. That trade-off belongs to H1's grid (the "no-hold" variant), not to evaluation frequency.
- April 2025 is inside the locked holdout (from 2024-01). Nothing in this report may be used to tune a parameter on it; any new card is frozen before the holdout opens, and the 2025 row stays confirmatory.

### 2.5 Timing luck is the real frequency problem

C6 shows that the choice of evaluation day can matter more than the choice of rule. A monthly rule with one tranche carries this risk in full. The fix with evidence behind it is not a faster signal but several slow ones on staggered dates (C7): with weekly-staggered tranches the account makes a real decision every week, each tranche still trades about as rarely as before, and one tranche's bad date moves only 1/N of the money. This is the closest evidence-backed match to "a lot more regular". It is H5, and PRT-14 already allows it from a sizing NAV of A$9,375.

## 3. Emergency brakes

### 3.1 What the literature supports

- **Theory.** A stop adds value only if losses predict further losses (C10). Equity indices show that weakly at monthly horizons and show reversal at daily horizons, which is why a one-day-delayed stop did slightly better than an immediate one (C11) and why big up days sit next to big down days (C17).
- **Thresholds.** Stops tighter than about 10% lose their benefit to costs (C11). Any brake must be wide.
- **Stops on top of trend.** Clare et al. tested exactly this combination on the S&P 500 and found no added value (C12). A trailing stop and a moving-average rule use the same information, so the stop mostly duplicates the trend filter at a faster, noisier speed. [unverified — reasoning]
- **Volatility triggers.** A downward-only volatility cap (no leverage) is the defensible form. The equity evidence is a Sharpe gain of about 0.1 and a thinner left tail in-sample (C15), with out-of-sample doubts (C14). At A$5,000 a half-step de-risk means orders of A$1,000 and A$1,500, costing 0.66% and 0.44% of the order in commission [computed], and it cannot scale finely in whole units.
- **Fast crashes.** Trend-type overlays do not hedge moves that last days (C16). The protection for that case is the base allocation: holding less equity, or a cash buffer.

### 3.2 A 15% drawdown brake on the four episodes (prediction, recalled index levels)

Rule sketched: sleeve goes OFF when its close is 15% or more below its 252-day high; re-entry by the normal monthly rule (votes ≥ 2).

| Episode | Fires | Compared with L1 unbraked | Net |
|---|---|---|---|
| 1987 | 16 Oct close (−16% from high); order next session, mid-crash | Saves perhaps half of one day's fall; both versions re-enter mid-1988 | Small gain |
| 2008 | January 2008, the same month L1 exits anyway | No difference | Nil |
| 2020 | About 9 March; exits around 8–10% above L1's early-April exit | Same re-entry | Gain of roughly 8–10% on the sleeve |
| 2025 | About 4 April; sells about 7 April, two sessions before the +9.5% day. Re-entry needs 2 votes: end-May, about 17% higher | L1 unbraked never sold | Loss of roughly 15–17% on the sleeve |

All four rows are [unverified]. Net over four crashes: roughly zero, with the largest single effect a loss, plus four to six extra orders and a tax event each time. This agrees in sign with C10–C12. The honest position is that a brake changes which crashes hurt; it does not reduce the total reliably.

### 3.3 Does a brake help net of re-entry whipsaw?

The condition is simple. A brake helps in an episode only if the further fall after the trigger, measured to the re-entry price, exceeds the round-trip cost plus tax:

`benefit = (exit price − re-entry price) ÷ exit price − c_RT − tax drag`

With re-entry by a slow rule, the re-entry price is above the exit price in V-shaped episodes (2020 for the unbraked rule, 2025 for the braked one) and far below it in slow bears (2008), where the trend filter already acts. The brake's own territory is the narrow case of a fast fall that keeps falling for months. In the US record since 1987 that is at most one episode in four. [unverified — count from section 3.2]

## 4. Cost and tax arithmetic

### 4.1 Explicit cost of one full round trip (both sleeves out and back in: four orders)

Spec cost model (RND-021): commission max(A$6.60, 0.088%) an order, half-spread 5 bp, one tick. "Observed" uses the ASX-reported 0.02% spread (C20), half-spread 1 bp. [computed]

| NAV | VAS / VGS order | Commission, 4 orders | Round trip, spec model | Round trip, observed spread |
|---|---|---|---|---|
| A$5,000 | 2,000 / 3,000 | A$26.40 = 0.53% | A$32.12 = **0.64%** | A$28.12 = 0.56% |
| A$25,000 | 10,000 / 15,000 | A$44.00 = 0.18% | A$72.60 = **0.29%** | A$52.60 = 0.21% |
| A$100,000 | 40,000 / 60,000 | A$176.00 = 0.18% | A$290.40 = **0.29%** | A$210.40 = 0.21% |

The minimum commission stops binding at A$7,500 an order, so cost per round trip is flat at 0.29% from about A$19,000 of NAV upward. [computed]

### 4.2 Annual explicit drag by switching rate (spec model) [computed; the rates are the section 2.2 estimates]

| Round trips a year | Typical of | Orders a year | A$5,000 | A$25,000 | A$100,000 |
|---|---|---|---|---|---|
| 0.3 | L1 monthly, hold zone | 1.2 | 0.19% | 0.09% | 0.09% |
| 0.6 | 10-month SMA, monthly | 2.4 | 0.39% | 0.17% | 0.17% |
| 1.2 | Weekly evaluation, or smoothed daily | 4.8 | 0.77% | 0.35% | 0.35% |
| 2.0 | — | 8 | 1.28% | 0.58% | 0.58% |
| 3.8 | Raw daily 200-day | 15.2 | 2.44% | 1.10% | 1.10% |
| 6.0 | Fast daily rule | 24 | 3.85% | 1.74% | 1.74% |

RSK-26 warns above 8 orders and halts buys above 12 orders in 12 months while NAV is under A$25,000. Any rule above about 2 round trips a year trips the warning and above 3 trips the halt, before top-ups are counted. Above A$25,000 the limit is 1.0% (warn) and 1.3% (halt) of NAV: raw daily sits at the warn line. [computed]

### 4.3 Whipsaw price cost

Explicit cost is the smaller part. A false exit is bought back higher: about 2–3% in 2020 and 4–5% in 2025 for a 200-day rule (section 2.4, [unverified]), and about four exits in five are false (section 2.3, [1]). At 3.8 round trips a year, even a 1% average re-entry premium on the false ones is about 3% a year gross. The backtest measures this directly; the literature's verdict is that it roughly cancels the drawdown saved. [unverified — order of magnitude]

### 4.4 CGT

Tax on a realised gain equal to 10% of NAV, as a percentage of NAV [computed from report 18's rules; Medicare 2% included; CPI 3% assumed]:

| Marginal rate | Before 1 July 2027: held < 12 months | Before: held ≥ 12 months (50% discount) | From 1 July 2027: held < 12 months | From: held ≥ 12 months (indexation, one year) |
|---|---|---|---|---|
| 18% (16% + 2%) | 1.80% | 0.90% | 3.00% (30% floor) | 2.10% (30% floor) |
| 32% (30% + 2%) | 3.20% | 1.60% | 3.20% | 2.24% |
| 39% (37% + 2%) | 3.90% | 1.95% | 3.90% | 2.73% |
| 47% (45% + 2%) | 4.70% | 2.35% | 4.70% | 3.29% |

- The gap between the short-holding and long-holding columns is the tax price of frequency: 0.9 to 2.4 points of NAV per 10% of gain realised before July 2027, and about 0.9 to 1.4 points after (indexation is worth less than the discount at these inflation rates, and worth more the longer the holding).
- A rule that round-trips 3–4 times a year never holds a parcel 12 months, so it always pays the short-holding column. A rule that switches every 2–4 years mostly pays the long-holding column. This cost does not shrink with account size.
- Whether Medicare levy applies on top of the 30% floor, and how the floor meets franking offsets, are tax-agent questions already listed in report 18. The 18% row's rate is [unverified] (open item P9).
- Losses from whipsaws are capital losses: usable only against capital gains, carried forward otherwise, never indexed.
- **Trader status.** Daily or weekly switching by an automated system with records and a written plan matches the ATO's business indicators (C23) far better than one or two switches every few years. On revenue account there is no discount or indexation at all, though losses become deductible. Report 18 asks the tax agent this at monthly frequency; at daily frequency the answer is much less likely to be "investor". [unverified — inference]

### 4.5 Breakeven

For a faster rule to beat monthly it must add, every year, gross benefit at least equal to: extra round trips × (c_RT + average re-entry premium) + extra tax.

| Move | Extra round trips | Extra explicit cost at A$5,000 / A$25,000+ | Extra tax (32% rate, gains of 8% a year realised short instead of long, pre-2027) | Gross benefit needed each year |
|---|---|---|---|---|
| Monthly → weekly | about +0.6 to +0.9 | 0.4–0.6% / 0.2–0.3% | up to 1.3% | about 1.5–2% at A$5,000; 1.5% above |
| Monthly → raw daily | about +3.2 to +3.5 | 2.1–2.2% / 0.9–1.0% | 1.3% | about 3.4% at A$5,000; 2.3% above, before re-entry premium |

[computed; the round-trip counts and the 8% are assumptions]. The measured gross benefit of daily over monthly in the literature is zero or negative (C1, C2). There is no breakeven at any of the three sizes; larger accounts lose less, they do not start to win.

For the brake: at a cost of 0.64% (A$5,000) or 0.29% a firing plus tax, the cost side is small. The brake fails on the re-entry premium, not on brokerage (section 3.2). Account size does not rescue it.

## 5. Intraday and real-time monitoring

- **No evidence of value for an index investor.** Every study above defines signals on closes. Lo–Remorov found delayed execution no worse than immediate (C11). [1]
- **The return is earned overnight** (C24). Selling intraday after a fall and sitting out the next overnight session gives up the part of the day that carries the premium and the rebound gaps. [2+] for the fact; [unverified] for the implication.
- **VGS cannot be front-run from Sydney.** Its holdings trade in US and European hours. During the ASX session its price moves on futures and the currency; the substantive news arrives as the opening gap. An intraday trigger on VGS would mostly be reacting to yesterday's US close a few hours late. [unverified — reasoning]
- **Cost.** ASX Total is A$25 a month (C21): A$300 a year, which is 6.0% of A$5,000, 1.2% of A$25,000 and 0.3% of A$100,000 [computed]. Free ASX data from IBKR is 20 minutes delayed. Snapshots at US$0.03 with a US$1 waiver cover about 33 quotes a month, which is enough for order-time quotes and nothing else (report 13).
- **Operations.** The gateway needs a human 2FA approval, the spec trades inside 11:30–15:00 to avoid both auctions, and every added intraday path is a new way to send a wrong order in a disorderly market, which is when it would fire.
- **Decision:** no intraday monitoring and no real-time subscription at any of the three sizes. Revisit only if a later strategy trades instruments whose signals are intraday by construction.

## 6. Recommendation

### 6.1 (a) Core L1

**Keep monthly evaluation and execution. Add a daily decision record. Use weekly-staggered tranches once NAV allows.**

| ID | Decision | Rule | Status |
|---|---|---|---|
| F-D1 | Evaluation frequency | One evaluation per tranche per month, as PRT-12 to PRT-16 now say. No change | Keep; confirmed by C1, C2 |
| F-D2 | Daily decision record | Every trading day at 08:10, for each sleeve, on the validated close of D−1: compute v1, v2, v3 using the trailing 126-, 252- and 210-trading-day windows [design value — set by backtest], the price change that would flip each vote, days to the next evaluation, and the shadow brake state (F-D5). Store one row a day. Report in the 08:10 plan message and the 20:00 digest as "HOLD — n votes; next evaluation dd mmm; VAS flips at −x.x%". It creates no order and changes no state | New, report-only. Meets the owner's request for a daily decision without a daily trade |
| F-D3 | More regular real decisions | Raise `tranches_max` from 3 to 4 with weekly offsets (evaluation on the last trading day of each week-of-month bucket) [design value — set by backtest, card H5]. At the PRT-14 test this needs a sizing NAV of A$12,500 [computed: 1.25 × 1,000 × 4 ÷ 0.40]. Below that, N = 1 | Proposed as an H5 grid point, not a live change |
| F-D4 | H8 | Extend the card so "weekly" and "daily with confirmation" are both arms, and so that a pass leads somewhere defined (card below) | Card amendment before freeze |

Planning numbers to put beside F-D1: expect daily evaluation of the same votes to show 3–6 times the switches, drawdown within about ±2 points of monthly, and lower net return at every NAV tested. [unverified — expectation from C1, C2, C4]

### 6.2 (b) Emergency brake

**Do not enable. Register, test, and run in shadow.**

| ID | Decision | Rule |
|---|---|---|
| F-D5 | Shadow brake (report-only from G1) | For each sleeve that is ON, on the validated total-return close of D−1: `brake_dd` = 1 − TR(D−1) ÷ max TR over the trailing 252 trading days. The shadow state is FIRED when `brake_dd` ≥ X on two consecutive validated closes, X = 15% [design value — set by backtest]. It clears at the first monthly evaluation, at least 21 trading days later [design value — set by backtest], at which votes ≥ 2. The digest shows "brake: armed / FIRED (shadow) / n.a.", the distance to the trigger, and what the order would have been. No order is planned |
| F-D6 | Live brake | Only by spec change after card H14 passes. Then: a firing makes D a planning day (add to PRT-16's list); order kind `brake`, a sell of the whole sleeve, exempt from the minimum order like a transition sell; it goes through the 11:15 veto and the 11:30 submit like any other intent; at most one firing per sleeve per 63 trading days [design value — operational] |
| F-D7 | Data guard (applies to shadow and live) | The brake reads only bars with verdict `OK`. A bar that is `WARN`, `SINGLE_SOURCE`, `DATA_SPIKE` or `BLOCK` cannot fire it; the two confirming closes must both be cross-source confirmed (DAT-02). A brake is triggered by exactly the large moves that DAT-04 treats as suspect, so a bad print must never be able to sell the account |
| F-D8 | Halts | Under `HALTED_BUYS` a brake sell passes, like a transition sell (RSK-01). Under `HALTED_INTEGRITY` or `KILLED` nothing is sent and the blocked sell is paged daily, as now. A brake order counts as a `transition` event for RSK-26, so brakes cannot exceed the order budget silently |
| F-D9 | No volatility-scaling brake at A$5,000 | A downward-only volatility cap is deferred to Stage 2 sizing (section 26), where report 14 D7 already places it. Not testable sensibly in whole units below about A$25,000 |
| F-D10 | Spec text for the owner | Add to section 9.1: "L1 does not protect against a fall that happens within days. In March 2020-type and 1987-type events it is expected to sell late or not at all. Protection against that case is the size of the equity allocation, not a faster rule." (Extends report 14 D10) |

PRT-20 ("no intra-month action … no stop, no emergency exit, no daily signal") stays as written. F-D2 and F-D5 are reports, not actions; the wording "no daily signal" should be read as "no daily signal that trades", and one clause saying so avoids a contradiction.

### 6.3 (c) Momentum satellite (frequency only; design is report 31's)

| ID | Decision | Rule |
|---|---|---|
| F-D11 | Selection frequency | Rank and rebalance monthly, on a mid-month date so its timing luck is not the core's [design value — set by backtest]. Evidence: monthly formation with a skipped month is the tested form of momentum; faster is costlier and has decayed (report 14 R1) |
| F-D12 | Exit checks | Daily check on validated closes for position-level exits only, with a wide trailing stop of 15–20% [design value — set by backtest] if the sleeve holds single stocks (C11: under 10% loses to costs). ETF-only satellites need no stop: the core's argument applies |
| F-D13 | Size gate | No satellite order under the A$1,000 minimum. A 10% satellite of two positions needs a sizing NAV of about A$25,000 [computed: 2 × 1.25 × 1,000 ÷ 0.10]. Below that the satellite is paper-only |
| F-D14 | Family | A satellite is a new strategy family with its own trial cap and holdout, not part of L1 |

## 7. Hypothesis cards (RND-010 format)

All thresholds are [design value — set by backtest] and are frozen before the first run. Cards H14 and H15 are new and must be added to RND-013's list and to `research.families.L1`. Each consumes trials from L1's cap of 50.

### H8 (amended): Monthly evaluation is sufficient

| Field | Content |
|---|---|
| ID | H8 (amendment before freeze) |
| Date registered | To be set at freeze |
| Card hash | Set by `trader hypothesis freeze` |
| Economic rationale | L1's votes use 6- to 12-month windows. Daily or weekly sampling of a slow signal adds threshold crossings, not information (C1, C2, C4). The owner has asked for more frequent decisions, so the claim is tested, not assumed |
| Exact rule | Arm M: section 9.1, N = 1, offset `last`. Arm W: the same votes on trailing 126 / 252 / 210 trading-day windows, evaluated on the last trading day of every week. Arm D: the same, evaluated every trading day, a state change acted on only after 3 consecutive closes give the same vote count. All arms: order on the next trading day's close (RND-028), same hysteresis, same minimum order |
| Fixed parameters | Windows 126 / 252 / 210 days; confirmation 3 days (arm D); hold zone as PRT-13 |
| Permitted perturbation grid | Confirmation {1, 3, 5} days; arm W weekday {Mon, Wed, Fri}; no lookback changes (those belong to H1) |
| Data and proxy map | Daily total-return proxies as RND-024 where licensed; otherwise ETF-era daily data labelled "short sample" (section 24 shared settings). If neither exists: "not testable", arm M stands |
| Sample and holdout | Development to 2023-12; holdout from 2024-01, confirmatory only |
| Benchmark | Arm M |
| Primary metric (one) | Maximum drawdown of the 40/60 portfolio, net of the section 25 cost model, at A$50,000 |
| Secondary metrics | After-tax CAGR at the H11 rates under both CGT regimes; round trips a year; share of parcels sold under 12 months; share of exits re-entered at a higher price; orders a year against RSK-26; results at A$5,000 and A$250,000; the 1987, 2008 and 2020 regime rows |
| Pass / fail | **Monthly stands** if neither arm W nor arm D lowers net maximum drawdown by 2 pp or more. **A faster arm is a candidate** only if it lowers net maximum drawdown by ≥ 2 pp **and** its after-tax CAGR is no more than 0.5 pp below arm M's at the account holder's rate **and** its orders a year at A$5,000 stay within RSK-26's warning level |
| Multiple-testing family | L1 design choice; decided by threshold, no significance test (RND-012) |
| Trials consumed | 3 base specifications (M is H1's), plus grid points run |
| Decision rule | If a faster arm is a candidate: register a new promotion card for it; do not switch on H8 alone. Otherwise monthly is confirmed and F-D2 is the only daily element |
| Result / decision / approver | — |

### H14 (new): A daily drawdown brake improves L1

| Field | Content |
|---|---|
| ID | H14 |
| Date registered / hash | At freeze |
| Economic rationale | L1 evaluates monthly on slow windows and is known not to act in falls that take days (C16). A wide daily drawdown trigger might cut the loss in a fast fall that continues. Against: stops lower return unless losses persist (C10), tight stops lose to costs (C11), stops added nothing to a 200-day rule on the S&P 500 (C12), and fast falls often reverse within days (C17, C18). Prior expectation: fail |
| Exact rule | Section 6.2, F-D5 to F-D8, applied as a live rule in the harness on top of H1's exact L1 |
| Fixed parameters | X = 15%; high-water window 252 trading days; 2 confirming closes; re-entry lockout 21 trading days then the monthly rule; one firing per sleeve per 63 trading days |
| Permitted perturbation grid | X {10%, 15%, 20%}; confirmation {1, 2}; lockout {21, 63} days; re-entry variant "back ON when `brake_dd` < X/2 at a month-end". Nothing below 10% (C11) |
| Data and proxy map | Daily, as H8. "Not testable" on monthly data |
| Sample and holdout | As H8. The April 2025 episode is in the holdout: it is reported once, when the L1 holdout is opened, and no parameter may be chosen with reference to it. This report's section 3.2 has looked at 2025 informally; that is declared here as a contamination risk, which is one more reason the grid is fixed now |
| Benchmark | L1 exactly as H1 (no brake) |
| Primary metric (one) | Maximum drawdown on daily unit prices, net of costs, at A$50,000 |
| Secondary metrics | After-tax CAGR (both regimes, H11 rates); number of firings; share of firings re-entered above the exit price; worst 20-day loss; orders a year at A$5,000; regime rows 1987, 2008, 2020 |
| Pass | Net maximum drawdown at least 5 pp lower than L1's, with bootstrap p < 0.10 (RND-012 family A defaults), **and** after-tax CAGR no more than 0.5 pp below L1's, **and** the result holds at X = 10% and 20% in sign, **and** it survives H12's haircut |
| Fail | Any one not met → the brake stays shadow-only (F-D5) and PRT-20 is unchanged. A fail is the expected result and is recorded as such |
| Multiple-testing family | L1, family A. If H14 is ever a promotion candidate it joins H1 in the Holm family at α = 0.10 |
| Trials consumed | 1 base + up to 11 grid points |
| Result / decision / approver | — |

### H15 (new): Shadow-brake live record (observational)

| Field | Content |
|---|---|
| ID | H15 |
| Economic rationale | A backtest of a rare-event rule has few events. A live shadow record adds out-of-sample events at no cost and no risk |
| Exact rule | F-D5 in production, report-only, from the first live day. Each firing is logged with the hypothetical exit and re-entry fills from validated closes and the cost model |
| Fixed parameters | As H14's base |
| Benchmark | The live L1 account |
| Primary metric (one) | Cumulative hypothetical difference in unit price, braked minus actual, after modelled costs and tax |
| Pass / fail | None. Reviewed at each yearly review (PRT-26). It can support registering a promotion card; it can never change live behaviour by itself |
| Family / trials | Logged with replication kind `replay`; not a trial (VAL-22) |

## 8. How it slots into the daily schedule

| Time | Job | Change |
|---|---|---|
| 19:30 | `fetch_vendor_data` | None. The same bars feed the daily record. No extra EODHD calls (DAT-23 budget unchanged) |
| 08:00 | `validate_data` | None. F-D7 reads the verdicts |
| 08:05 | `mark_and_reconcile` | None |
| 08:10 | `decide` | After the existing steps, run `daily_record` for every sleeve: daily votes, flip distances, shadow brake state (F-D2, F-D5). Pure function of validated closes; writes `daily_signal` rows; cannot create a plan line. If H14 is later adopted, a live firing is planned here as kind `brake` and today becomes a planning day |
| 11:15 | `approve_plan` + `pre_trade_check` | Unchanged. A live brake sell would have the same veto window as any intent: three hours, not zero. That delay is deliberate; C11 found delay costs nothing |
| 11:30 | `submit_orders` | Unchanged. A live brake sell uses the confirming-snapshot path that transition sells use (DAT-13), since it would trade on a day when the 2% quote check is likely to hold orders |
| 20:00 | `daily_digest` | Add one line per sleeve: votes today, change needed to flip, days to evaluation, shadow brake state |

New storage: one table `daily_signal` (date, sleeve, v1, v2, v3, flip distances, `brake_dd`, shadow state, verdict level used). New config: `daily_record.enabled` (default true), `brake.mode` ∈ {`off`, `shadow`} with `live` refused by config validation until H14 is recorded as passed, in the way OPS-12 gates `L1`. No new halt class and no new command.

Risk and halt design is otherwise untouched: a report-only path cannot breach RSK-03, RSK-06 or RSK-26. The one new failure mode is a wrong line in the digest; the test is that `daily_record` on an evaluation date reproduces that date's `tranche_state.votes` exactly when given the month-end windows.

## 9. What I could not establish

1. The exact tables of Clare et al. (2013): trades per rule, drawdown by frequency. The direction is [2+], the figures [1] from extracts.
2. Any study of weekly evaluation for a long-only index filter. None found.
3. Any Australian-market test of daily vs monthly trend evaluation. None found (report 12 found only practitioner pieces on trend generally).
4. Signal dates and prices in section 2.4 and 3.2. Recalled, in USD, on the S&P 500 price index; VAS and VGS in AUD will differ, particularly in March 2020 when the falling dollar cushioned VGS.
5. The switch counts for L1's own three-vote rule at any frequency. Only the harness can give them.
6. Kaminski–Lo's and Lo–Remorov's threshold tables; Han, Zhou and Zhu's stop-loss momentum result (not retrieved; relevant to report 31).

## 10. Sources

| Ref | Source | How read |
|---|---|---|
| S1 | Clare, Seaton, Smith, Thomas (2013), "Breaking into the blackbox: trend following, stop losses and the frequency of trading – the case of the S&P500", J. Asset Management 14(3). [IDEAS working paper](https://ideas.repec.org/p/yor/yorken/12-11.html), [journal record](https://ideas.repec.org/a/pal/assmgt/v14y2013i3d10.1057_jam.2013.11.html) | Abstract fetched |
| S2 | Alpha Architect, ["Daily vs. Monthly Trend-Following Rules"](https://alphaarchitect.com/daily-vs-monthly-trend-following-rules-plus-some-diy-tools/) (Zakamulin); ["If you had to do a trend following strategy"](https://alphaarchitect.com/2019/02/22/if-you-had-to-do-a-trend-following-strategy-what-would-it-be-and-why/) | Search extract |
| S3 | Alpha Architect, ["Trend Following the S&P 500? Some Practical Advice"](https://alphaarchitect.com/trend-following-the-sp-500-some-practical-advice/); CXO, ["Following S&P 500 Index Trends"](https://www.cxoadvisory.com/technical-trading/following-sp-500-index-trends/) | Search extract |
| S4 | Hurst, Ooi, Pedersen (2013), ["Demystifying Managed Futures"](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Demystifying-Managed-Futures.pdf) | Full text (report 14) |
| S5 | StockCharts / TrendInvestorPro (2022), ["Quantifying the Battle for the 200-day"](https://trendinvestorpro.com/quantitative-analysis-backtest-200-day-moving-average-spy-spx/) | Search extract |
| S6 | r/LETFs, "Mitigating MA whipsaws: backtest 1886–2025" (27 March 2025) | Search extract; anecdotal |
| S7 | Hoffstein, Newfound, ["The Luck of the Rebalance Timing"](https://blog.thinknewfound.com/2013/08/the-luck-of-the-rebalance-timing/) (2013) | Search extract |
| S8 | Newfound, ["Well, you… No, you gotta do more than that"](https://advisoranalyst.com/?p=128492) and ["What the Trend"](https://advisoranalyst.com/2020/03/23/what-the-trend.html/) (March 2020) | Search extract |
| S9 | Hoffstein, Faber, Braun, ["Rebalance Timing Luck: The Dumb (Timing) Luck of Smart Beta"](https://www.panoptica.com/rebalance-timing-luck-the-dumb-timing-luck-of-smart-beta-by-hoffstein-faber-and-braun/) | Search extract |
| S10 | Kaminski & Lo (2014), "When do stop-loss rules stop losses?", J. Financial Markets 18. [EconPapers](https://econpapers.repec.org/RePEc:eee:finmar:v:18:y:2014:i:c:p:234-254) | Abstract fetched |
| S11 | Kaminski & Lo, working paper. [EconPapers SIFR 63](https://econpapers.repec.org/RePEc:hhs:sifrwp:0063), [MIT DSpace](https://dspace.mit.edu/handle/1721.1/114876) | Search extract |
| S12 | Lo & Remorov (2017), "Stop-loss strategies with serial correlation, regime switching, and transaction costs", J. Financial Markets 34. [MIT DSpace](https://dspace.mit.edu/handle/1721.1/107017); [CXO summary](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth) | Search extract |
| S13 | Dai, Marshall, Nguyen, Visaltanachoti (2021), "Risk reduction using trailing stop-loss rules", Int. Review of Finance 21(4). [IDEAS](https://ideas.repec.org/a/bla/irvfin/v21y2021i4p1334-1352.html) | Abstract fetched |
| S14 | Moreira & Muir (2017), "Volatility-Managed Portfolios", J. Finance 72(4). [NBER w22208](https://www.nber.org/papers/w22208) | Full PDF |
| S15 | Cederburg, O'Doherty, Wang, Yan (2020), "On the performance of volatility-managed portfolios", JFE 138(1). [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:138:y:2020:i:1:p:95-117) | Abstract fetched; counts from search extract |
| S16 | Liu, Tang, Zhou (2019), "Volatility-Managed Portfolio: Does It Really Work?". [WashU record](https://profiles.wustl.edu/en/publications/volatility-managed-portfolio-does-it-really-work/) | Search extract; journal not confirmed |
| S17 | Harvey, Hoyle, Korgaonkar, Rattray, Sargaison, Van Hemert (2018), "The Impact of Volatility Targeting", JPM 45(1). [Quantpedia](https://quantpedia.com/?p=830), [Man](https://www.man.com/insights/the-impact-of-volatility-targeting) | Search extract; Man page read in report 14 |
| S18 | J.P. Morgan Guide to Retirement, via [CNBC](https://www.cnbc.com/2022/03/09/you-may-miss-the-markets-best-days-if-you-sell-amid-high-volatility.html), [401k Specialist](https://401kspecialistmag.com/folly-of-timing-the-market-explained-in-jpmams-2024-guide-to-retirement/) | Search extract |
| S19 | [Briefing.com closing summary, 10 March 2025](https://briefing.com/stock-market-update/archive/2025/3/10/closing-summary-); Reuters via [iTiger](https://itiger.com/news/2518767207) | Search extract |
| S20 | Alpha Architect, ["The Return of the King"](https://alphaarchitect.com/the-return-of-the-king-trend-following-is-back-but-will-it-last/); [HedgeNordic](https://hedgenordic.com/?p=44399); [Cambridge Associates](https://publishedresearch.cambridgeassociates.com/?p=19140) | Search extract |
| S21 | [The Pattern Site, Dow 1987](https://www.thepatternsite.com/dj87.html); [Wealthy Doc](https://wealthydoc.org/avoid-market-crashes/) | Search extract |
| S22 | [AlgoStrategyLab, 10-month SMA tested over 40 years](https://algostrategylab.github.io/sma-trend-filter/) | Search extract |
| S23 | ASX Investment Products monthly reports, [September 2026](https://www.asx.com.au/content/dam/asx/issuers/asx-investment-products-reports/2026/pdf/asx-investment-products-sep-2026.pdf) and October 2026 | Local copies in `scratchpad/dl_asx/`, read directly |
| S24 | [Stockspot ETF table](https://blog.stockspot.com.au/?p=7388) | Search extract; undated |
| S25 | [IBKR Australia market data pricing](https://www.interactivebrokers.com.au/en/pricing/market-data-pricing.php) | Fetched 13 November 2026 |
| S26 | ATO, ["Share investing versus share trading"](https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/shares-and-similar-investments/share-investing-versus-share-trading) | Search extract (page 403) |
| S27 | ["Does Overnight News Explain Overnight Returns?"](https://arxiv.org/abs/2507.04481), arXiv 2507.04481 | Abstract fetched |
| S28 | Lou, Polk, Skouras (2019), ["A tug of war"](https://researchonline.lse.ac.uk/id/eprint/119010); Cliff, Cooper, Gulen (2008) | Search extract |
| — | Baltas & Kosowski, ["Demystifying Time-Series Momentum Strategies"](https://papers.ssrn.com/abstract=2140091) | Search extract. Finding: better volatility estimators and a continuous signal cut turnover by more than a third with no significant performance loss [1]. Futures; relevant to Stage 2 sizing, not to L1's binary monthly rule |
| — | Reports 13, 14, 16, 18, 20 and FD_FINAL.md v2.10 | Local |
