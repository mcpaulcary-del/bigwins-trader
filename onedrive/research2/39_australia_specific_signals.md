# 39. Australia-specific market structure and signals: what an ASX ETF system can and cannot exploit

Date: 2026-11-13. Spec read: FD_FINAL.md (v2.10). Scope: the eight Australia-specific topics in the brief (currency, commodities, rates, dividends and franking, index and financial-year events, ASX microstructure, concentration, flows). Other reports cover the L1 variants, algorithm families, momentum, decision frequency, platforms and source verification; they are not repeated here.

Evidence tags: **[2+]** two or more independent sources agree, or a primary source plus my own test on data; **[1]** one source, or my own test only; **[unverified]** could not be confirmed. "Test" means code run today on downloaded data; scripts and outputs are listed in section 12.

---

## 0. Answer first

1. **None of the eight topics yields a tradable timing signal for a monthly ETF system.** I tested 40+ Australia-specific predictors and calendar windows on up to 51 years of data. The ones that look significant are either gone in the most recent third of the sample (turn of month), contradict each other across eras (yield curve), are too small to cover one brokerage fee (ex-date effects), or cannot be captured at a monthly cadence (overnight commodity moves). No live rule is recommended.
2. **Three things are worth money and are already in the spec or need only a wording change:**
   - **Stay unhedged (keep D3 / PRT-24), as a risk choice.** Over 1990–2025 the unhedged 40/60 mix had lower volatility (11.9% vs 13.4%) and a shallower worst drawdown (−38% vs −47%, both in 2007–09) than the hedged one, because the Australian dollar fell in 15 of the 20 worst US-equity months since the float. This is not statistically secure (bootstrap p = 0.22), it did not hold before 2000, and it failed in April 2025. There is no return edge either way and no usable hedge-timing signal.
   - **Never buy an ETF at the first print of the day (keep D5 / OPS-03).** In 2022–24 the first trade of the day was priced above the same day's close by 3 bp for VAS, 6 bp for VGS, 11 bp for VGAD and 16 bp for BGBL on average; BHP and CBA show zero. Opening prices are also 2–3 times noisier than closing prices. The spec's 11:30–15:00 window already avoids this.
   - **The IBKR closing-auction order type for ASX is Limit-on-Close.** IBKR's ASX exchange page lists LOC as native for stocks and does not list MOC or any opening-auction type. This closes most of the "unverified" note in D5. The data give no reason to use the auction for orders this small.
3. **Franking is the one structural Australian return source**, worth about 1.1–1.4% a year on the VAS holding (about 0.4–0.55% of a 40/60 account) to a resident who can use the credits. It needs no rule: it is collected by holding. At A$5,000 to A$100,000 the A$5,000 small-shareholder exemption makes the 45-day rule irrelevant (subject to open item T3).
4. **Concentration is real but the fix is already in the design.** Ten names are 49.2% of the ASX 200 (27 March 2026) and explain 93% of its daily variance. The 60% global sleeve is the diversifier. An equal-weight Australian sleeve (MVW) is not supported: its 2014–19 lead reversed (five years to October 2026: MVW 7.65% a year, VAS 8.95%).
5. **Three hypothesis cards are proposed (H50–H52)**, all low-stakes design checks. Seven ideas are rejected without a card so they do not use up the trial budget.
6. **Open item P9 can be closed at secondary-source level:** the lowest non-zero resident rate is 15% for 2026–27 (16% in 2024–25 and 2025–26; 14% from 1 July 2027). The ATO page itself was blocked.

**Disclosure that affects the registry.** My exploratory tests used monthly data to December 2025 and daily ETF data to May 2024. The spec locks 2024-01 onward as holdout. No parameter was fitted and no rule is proposed from those tests, but any card that builds on this report must declare the exposure. The three cards below set their holdout to start after the data I have seen.

---

## 1. Ranked findings

| Rank | Finding | Evidence | Size after costs and tax | Recommendation |
| --- | --- | --- | --- | --- |
| 1 | First print of the day is biased high for ETFs and 2–3× noisier than the close | [2+] my test on 12 ETFs plus four issuer/broker guides | 3–16 bp per buy avoided: A$0.60–4.80 per order at A$5k, A$3–24 at A$25k, A$12–96 at A$100k | **Execution rule already in spec — keep.** Card H50 confirms on unseen data |
| 2 | Unhedged global sleeve lowers portfolio risk for an AUD investor; no return edge; no timing signal | [2+] my test, RBA 2009 and 2025, Campbell et al. | Risk: 1.5–2.7 pts lower volatility and a worst drawdown about 9 pts shallower (bootstrap median 7 pts). Return: zero expected. A hedge switch costs 0.12–0.28% of the account in brokerage plus 1.6–3% in CGT | **Keep unhedged (owner decision stands).** Add two calibrated stress cases to PRT-24. Reject timing |
| 3 | IBKR supports LOC, not MOC, for the ASX close | [2+] two IBKR pages fetched today | Nil for small orders (close noise 5–7 bp is larger than the 1 bp half-spread at midday) | **Spec wording change (D5, §21).** Do not use the auction |
| 4 | Franking credits: about 1.1–1.4% a year on VAS, usable in full under A$5,000 of credits a year | [2+] | +A$21–27 a year at A$5k; A$107–137 at A$25k; A$430–550 at A$100k (40% VAS) | **Owner guidance.** No rule |
| 5 | Top-10 weight 49.2%; ten names explain 93% of index variance; equal-weight and ex-20 variants are not reliably better | [2+] VanEck, STW/IOZ holdings, my test | MVW costs 0.11% of the account a year more in fees; its excess return is t = 1.7 and has reversed | **Keep VAS (or A200).** Card H52 as a paper control only |
| 6 | ETF price is about 10–14 bp rich in the five days before its ex-date (30 bp for VHY) | [1] my test, t = 1.8 to 3.4 | 10–14 bp of one purchase: under A$1 on a A$500 top-up | **Hypothesis card H51.** No rule |
| 7 | July is strong and June weak in Australia; small caps lag in June and rebound in July | [2+] my test plus Brown et al. 1983 and 2010 | Index: July +3.3% a month 2009–25 but +0.25% 1992–2008. Deferring one June contribution saves about 0.7% of that contribution: A$3.50 a year at A$500 a month | **Owner guidance only.** Reject as a rule: unstable across eras, one observation a year |
| 8 | Turn-of-month effect has disappeared | [2+] my test plus a 2000–19 thesis | 6.0% a year 1980–99; 2.9% 2000–11; 0.2% 2012–24 | **Reject** |
| 9 | Yield curve and RBA cycle do not predict ASX returns out of sample at one or three months | [2+] my test plus Dou et al. 2012 | Timing rules cost 1.0–2.1% a year of return before tax | **Reject** |
| 10 | Commodity prices do not lead the ASX at a monthly horizon; if anything equities lead commodities | [2+] my test plus Chen, Rogoff and Rossi 2010 | Commodity-trend timing: 5.4–7.3% a year vs 10.7% buy-and-hold | **Reject** |
| 11 | Quarterly index rebalance days: no index-level effect; ETF volume only 1.1–1.3× normal | [1] my test; [2+] for the stock-level effect | Nil for an index ETF holder | **Reject.** Nothing to schedule around |
| 12 | Super guarantee quarterly due dates: no return pattern; payday super from 1 July 2026 removes the quarterly lump anyway | [1] my test; [2+] for the law | Nil | **Reject** |

---

## 2. Data used, and what I added and why

The owner asked for depth and said to add data or tests where needed. Yahoo, Stooq, FRED, S&P, ATO, SSRN, Wiley and ScienceDirect were blocked from this session. I therefore built the dataset from what was reachable.

| Dataset | Source | Coverage | Used for |
| --- | --- | --- | --- |
| AUD/USD and TWI, monthly and daily | RBA F11 and historical daily files | Monthly 1969–2026-10; daily 1983-12 to 2026-11-13 | Topic 1 |
| Cash rate, 90-day bills, 2/3/5/10-year bond yields | RBA F1.1, F2.1 and historical F2 | 1969–2026-10 (3-year from 1992) | Topic 3 |
| RBA Index of Commodity Prices (all items, bulk, base metals; USD, AUD, SDR) | RBA I2 | 1982-07 to 2026-10 | Topic 2 |
| Australian market returns, with and without dividends, local and USD; high/low/zero-yield portfolios | Ken French international country file | 1975-01 to 2025-12 monthly | Topics 1–5 |
| Developed-market and US returns, monthly and daily | Ken French factor files | 1990-07 to 2026-09 (US from 1926) | Topic 1 |
| **Added:** daily open/high/low/close/volume for every ASX code, unadjusted | Public GitHub repository `rs77/asx-historical-data` | 1997-01 to 2024-05-31; 6,921 daily files | Topics 4–7. Gives XJO, XAO, sector and size indices, XNT (net total return) and every ETF |
| **Added:** All Ordinaries daily, copper, crude, gold, CRB | Public GitHub snapshot of Stooq (`arekbee/StooqHistoricalDataDaily`) | All Ords daily 1980–2014; futures to 2014 | Topics 2, 5 |
| **Added:** ASX 200 daily | Public GitHub repository `xiaohaoyanglei/asx200-dataset-axjo` | 2020-10 to 2025-10 | Extends XJO; cross-check |
| ASX Investment Products monthly report | ASX, October 2026 (already downloaded) | One month | Spreads, fees, flows, returns |

Why the additions: the brief asks for ex-date, June/July, auction and concentration evidence, and none of that can be tested on monthly index data. The GitHub price files are third-party copies, so I checked them: XJO in the repository matches the Yahoo-sourced series within 0.3% on all 918 overlapping days, and XAO matches the Stooq All Ordinaries to a median difference of zero over 3,374 days. The repository has about 3% fewer XJO rows than the trading calendar implies (5,753 against roughly 5,925), so a few days are missing. These files are good enough for research in this report. They are not licensed data and must not be used for card runs (open items O5, P2).

Two modelling approximations to keep in mind:

- **Hedged global return** = USD return + (Australian 90-day bill rate − US T-bill rate), monthly. This hedges the US dollar only. The check against real funds is good: over 2016-06 to 2024-05 the monthly gap between VGAD and VGS has a 0.93 correlation with the change in AUD/USD.
- **French's Australian dividend series is smoothed before 2000** (every month shows the same yield), so dividend seasonality is measured only from 2000.

---

## 3. Topic 1 — The Australian dollar as a natural hedge

### 3.1 What the data show

**The dollar falls when world equities fall, but only since about 2000.** [2+]

| Period | Correlation of monthly AUD/USD change with US equity return | With developed-market return |
| --- | --- | --- |
| 1984–1999 | 0.12 | 0.17 |
| 2000–2012 | 0.56 | 0.68 |
| 2013–2025 | 0.54 | 0.62 |
| Weekly, 2024 | 0.52 | 0.62 |
| Weekly, 2025 | 0.25 | 0.36 |
| Weekly, 2026 to September | 0.27 | 0.37 |

In the 20 worst months for US equities since the 1983 float, the US market fell 10.7% on average and the Australian dollar fell 3.9%; it fell in 15 of the 20. An unhedged Australian holder lost 6.9% on average in those months, a hedged one 10.4%.

**Episodes (peak to trough, month-end data):**

| Episode | US equities, USD | AUD/USD | Unhedged, in AUD | Hedged to AUD | Australian shares |
| --- | --- | --- | --- | --- | --- |
| 1987 crash | −29.9% | −1.0% | −29.1% | −28.6% | −36.5% |
| 2000–02 | −45.0% | −5.4% | −41.8% | −42.9% | −4.0% |
| 2007–09 | −50.3% | −30.0% | −29.0% | −46.6% | −48.3% |
| 2020 (Jan–Mar) | −20.2% | −11.9% | −9.5% | −20.3% | −24.5% |
| 2022 (Jan–Sep) | −24.8% | −10.4% | −16.1% | −24.8% | −11.1% |
| 2025 (Feb–Apr) | −8.5% | +3.1% | −11.2% | −8.5% | −4.0% |

The real funds agree: from January to March 2020 VGS fell 10.5% and VGAD 20.6% (price only).

**The cushion failed in 2025.** In the four weeks to 4 April 2025 US equities fell 12.1% and the Australian dollar fell only 1.1%; across February to April it rose. The weekly correlation in 2025–26 is about half its 2013–24 level. Report 12 noted this; the numbers above size it. [2+]

**Portfolio effect on 40% Australian / 60% global, rebalanced monthly:**

| Period | Global sleeve | CAGR | Volatility | Worst drawdown |
| --- | --- | --- | --- | --- |
| 1990-07 to 2025 (US proxy) | Unhedged | 10.9% | 11.9% | −38.0% |
| | Hedged | 11.8% | 13.4% | −47.2% |
| | 50/50 | 11.4% | 12.3% | −42.2% |
| 2008–2025 (US proxy) | Unhedged | 10.4% | 12.0% | −29.2% |
| | Hedged | 10.4% | 14.7% | −42.3% |
| 2008–2025 (developed proxy) | Unhedged | 8.5% | 11.6% | −31.9% |
| | Hedged | 8.5% | 14.8% | −44.9% |

The hedge share that minimised volatility was 50% in 1984–99, 0% in 2000–12 and in 2013–25, and 5% over 1990–2025.

**It is not statistically secure.** A paired stationary bootstrap (12-month blocks, 10,000 paths, 1990-07 to 2023-12, developed-market proxy) gives a 22% chance that the unhedged mix does *not* have the shallower drawdown. That would not pass the spec's Family A test at α = 0.10. Treat "unhedged is safer" as likely, not proven. [1]

**No return edge.** Hedged beat unhedged by 2.6 points a year over 1984–2023, entirely because Australian short rates averaged 3.0 points above US rates. That gap was 4.4 points in 1984–99, 0.8 points in 2013–23, and is about 1.1 points now (Australian 90-day bills 4.80%, US T-bill about 3.7%, October 2026). Over 2008–2025 the two returned the same. The RBA's 2009 study found the same thing for 1988–2008 and attributed it to the dollar "having depreciated by less than implied by interest rate differentials". [2+]

**The regret is large in both directions.** Over rolling three-year windows the gap between hedged and unhedged ranged from −35% to +64% cumulative. The year to October 2026 is the current example: VGS +4.6%, VGAD +13.1% (ASX report), with AUD/USD up from 0.655 to 0.704.

### 3.2 Is the dollar's trend or level a usable signal?

No. I tested seven signals for switching the global sleeve between hedged and unhedged, 1984–2025, each acting with a one-month lag, before any cost:

| Signal (hedge when…) | t-stat for predicting next month | Switches | Excess over a fixed 50/50, t-stat | First half / second half, % a year |
| --- | --- | --- | --- | --- |
| AUD 12-month change > 0 | −0.35 | 63 | 0.05 | +0.4 / −0.3 |
| AUD 6-month change > 0 | 0.77 | 78 | 1.32 | +1.5 / +0.8 |
| AUD above its 10-month average | 0.31 | 88 | 0.30 | +1.5 / −1.0 |
| AUD below its 10-year average | 0.64 | 12 | −0.02 | +0.7 / −0.8 |
| AUD below its expanding average | 1.62 | 8 | 1.03 | +1.7 / +0.1 |
| Rate gap (AU − US) > 0 | 1.68 | 29 | 1.21 | +1.2 / +0.9 |
| Commodity index 12-month change > 0 | −0.58 | 31 | 0.99 | +1.6 / +0.1 |

None reaches t = 2, let alone the spec's t ≥ 3 for a return claim. Seven signals were tried, so the best one (t = 1.32) is what chance alone would produce.

**Level does mean-revert, slowly.** When AUD/USD was below 0.60 it rose 33% on average over the next three years; above 0.90 it fell 14%. But those buckets hold one or two independent episodes each (2001–02; 2011–13), the windows overlap, and it is in-sample. At today's 0.68 the bucket average is +8% over three years, which is noise. [1]

**After costs and tax, hedge switching is clearly negative:**

| Account | Brokerage and spread per switch of the 60% sleeve | As % of account | CGT if the sleeve carries a 20% gain, 32% rate, 50% discount | Without discount (rules from 1 July 2027) |
| --- | --- | --- | --- | --- |
| A$5,000 | A$13.80 | 0.28% | A$80 (1.6%) | up to A$160 (3.2%) |
| A$25,000 | A$29.40 | 0.12% | A$400 (1.6%) | up to A$800 (3.2%) |
| A$100,000 | A$117.60 | 0.12% | A$1,600 (1.6%) | up to A$3,200 (3.2%) |

Brokerage uses the spec's max(A$6.60, 0.088%) and a 2 bp spread; the tax line is my arithmetic on stated assumptions [computed]. Indexation would reduce the last column.

### 3.3 Recommendation

- **Keep the global sleeve unhedged.** The owner decision (C12, D3, PRT-24) stands and the data support it as a risk choice. Evidence: [2+].
- **Do not time the hedge.** Reject, no card. The existing V3 control in H13 already tests hedged against unhedged; attach section 3.1 to it rather than register a duplicate.
- **Owner guidance:** unhedged is expected to hurt in years when the dollar rises (the year to October 2026 cost 8.5 points against VGAD). That is the price of the cushion, not a fault. A fixed 25–50% hedged share is a defensible alternative if the owner would rather halve that regret; it gave a drawdown about halfway between the two. Super funds hedge about one-fifth of listed overseas equities (RBA, September 2025).
- **Spec text:** see section 11.1 (two calibrated stress cases for PRT-24).

---

## 4. Topic 2 — Commodity linkage

**The link is real and simultaneous.** With month-end futures prices (1990–2014), the Australian market's excess return has a 0.34 correlation with copper and 0.33 with the CRB index in the same month; materials relative to the ASX 200 has 0.45 with copper. [1]

**There is no lead.** [2+]

| Test (monthly) | Result |
| --- | --- |
| Copper last month → Australian market this month | correlation 0.004, t = 0.06 |
| CRB last month → Australian market this month | −0.021, t = −0.32 |
| Crude last month → market | −0.066, t = −1.14 |
| Copper last month → materials minus ASX 200 | −0.055, t = −0.69 |
| RBA commodity index (USD), 1-month change, lagged one month → market, 1982–2025 | t = 0.28; out-of-sample R² −0.7% |
| Same, 12-month change | t = −1.83 (wrong sign); out-of-sample R² −0.3% |
| Australian market last month → RBA commodity index this month | t = +2.8 |

Across 22 predictor/lag combinations for the market, the best out-of-sample R² is 0.8% and the signs are mostly negative: a strong commodity year was followed by slightly weaker equity returns. For materials relative to the index, all 22 out-of-sample R² values are between −1.5% and +0.4%.

**Equities lead commodities, not the reverse.** This matches Chen, Rogoff and Rossi (2010): asset prices of commodity exporters are forward-looking and predict commodity prices; commodity prices do not robustly predict them out of sample. Part of the t = 2.8 above is mechanical, because the RBA index uses monthly averages and some contract prices.

**A commodity-trend overlay loses.** "Hold Australian shares only when the RBA commodity index is above its level 12 months ago" (two-month lag, 10 bp a switch): 7.3% a year against 10.7% buy-and-hold, same worst drawdown (−48%). The bulk-commodity and three-month versions are worse.

**Daily lead is real but not capturable.** Overnight copper and S&P 500 moves predict the next ASX day (t = 7.6 and 47.7, 1990–2014). That is the time-zone gap: the information is in the 10:00 open, before any order of this system could trade.

**Iron ore specifically** could not be tested as a spot series (World Bank and IMF hosts blocked); the RBA bulk-commodities sub-index stands in for it. [unverified for spot iron ore]

**Recommendation: reject.** No rule, no card. Effect net of costs is negative at every account size. The useful fact for the owner: a bad month for commodities is a bad month for VAS at the same time, and the Australian dollar usually falls with it, which is one more reason the unhedged global sleeve diversifies.

---

## 5. Topic 3 — RBA cycle and yield curve

Sample: Australian market excess return over 90-day bills, 1975–2025 (611 months). Out-of-sample tests use an expanding window against the historical mean (Campbell–Thompson R² and Clark–West statistic).

| Predictor | 1 month: t / OOS R² | 3 months: t / OOS R² | 12 months: t / OOS R² |
| --- | --- | --- | --- |
| 10-year minus 90-day bill | 0.16 / −0.5% | 0.90 / +0.1% | 1.18 / +1.2% |
| 10-year minus 3-year (from 1992) | 1.40 / +0.6% | 1.31 / +0.5% | 1.42 / −6.6% |
| 10-year minus cash rate | 0.29 / −0.1% | 0.37 / −0.4% | 0.41 / −0.7% |
| Bill rate, 12-month change | −0.46 / 0.0% | −0.82 / +0.5% | −1.33 / +1.6% |
| Bill rate minus its 12-month average | 0.33 / −0.6% | −0.33 / −0.3% | −1.50 / +2.0% |
| Bill rate level | −0.63 / −0.3% | −1.16 / −0.7% | −1.22 / −2.0% |
| Dividend yield minus 10-year yield | 0.69 / −0.4% | 1.07 / −0.8% | 1.32 / −3.0% |
| Cash-rate target, 6-month change (from 1990) | −0.72 / −0.2% | −0.97 / −0.9% | −0.94 / −6.2% |

No predictor has an in-sample |t| above 1.5 at any horizon. At 12 months two short-rate measures show small positive out-of-sample R² (1.6–2.0%), which agrees with Dou, Gallagher, Schneider and Walter (2012): most single predictors fail out of sample in Australia, with some predictability at one year from combinations. [2+]

**The inverted-curve signal flips sign between eras:**

| Era | Return after an inverted curve (10-year below bills) | After a normal curve |
| --- | --- | --- |
| 1976–1992 | +9.2% a year | −3.8% |
| 1993–2009 | −2.5% | +9.8% |
| 2010–2025 | +9.8% | +5.8% |

A rule that would have been right in one era was wrong in the next. Australia's curve was inverted in 36% of all months since 1975, so inversion is not a rare warning here.

**Rate direction has the expected sign but is not significant.** Returns were 7.5% a year when bills were lower than 12 months earlier and 2.9% when higher, in all three eras (t = 0.98). After an RBA cut the next three months averaged +2.3%; after a hike −0.3%; unconditional +1.45%.

**Every timing rule lowers return:**

| Rule (10 bp a switch, no tax) | CAGR | Buy-and-hold | Volatility | Worst drawdown |
| --- | --- | --- | --- | --- |
| Out when curve inverted | 9.7% | 11.8% | 13.1% vs 16.6% | −41.7% vs −48.3% |
| Out when bills rising over 12 months | 10.5% | 11.5% | 12.5% vs 16.6% | −41.7% vs −48.3% |
| 2000–2025, out when curve inverted | 7.7% | 8.1% | 10.9% vs 13.2% | −27.9% vs −48.3% |

The lower risk comes from being in cash a third to half of the time, not from skill: Sharpe ratios are equal or lower (0.24–0.30 against 0.32–0.33). With 20–50 switches, CGT would take a further 1–2 points a year.

**Recommendation: reject.** No rule, no card. Effect net of costs and tax is −1 to −3% a year at every account size. Current state for the record: cash target 4.85%, 90-day bills 4.80%, 3-year 4.88%, 10-year 5.26% (October 2026); the RBA has been tightening through 2026.

---

## 6. Topic 4 — Dividends, franking, ex-dates and the 45-day rule

### 6.1 Dividend clustering [2+]

Share of the year's index dividend yield by month (French 2013–2025; the XNT-minus-XJO measure for 2011–2024 agrees to within 0.1 point):

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.03% | 0.64% | 0.65% | 0.04% | 0.47% | 0.20% | 0.02% | 0.67% | 0.67% | 0.05% | 0.50% | 0.18% |

February–March and August–September carry 64% of the year's 4.1% yield; May and November (bank dividends) another 24%. Clustering has increased: those four months were 48% in 2000–12.

This matters for one thing only: **price-only data understate VAS in those months by 0.6–0.7 points**. The spec already builds total-return series and blocks evaluation across a missing distribution (DAT-22). No change needed.

### 6.2 Is there a dividend run-up to trade? No

- High-yield minus low-yield Australian portfolios (French), in the two months before the heavy ex-dividend months: +0.05% a month, t = 0.13. No run-up at the portfolio level. [1]
- The run-up literature for Australia is about single stocks around their own ex-dates. I could not open those papers. [unverified]

### 6.3 ETF ex-dates: a small, consistent effect

ETF distributions go ex on the first trading day of January, April, July and October (VAS: 49 of 52 inferred ex-dates on day 1; A200: 21 of 22). Inferred from the price drop against the net-total-return index, the average VAS distribution was 1.1% a quarter.

Relative to the total-return index, before and after the ex-date:

| ETF | Events | Five days before | Day before | Day after | Ten days after |
| --- | --- | --- | --- | --- | --- |
| VAS | 36 | +13 bp (t = 1.8) | +14 bp (1.7) | −9 bp (−1.3) | −7 bp (−1.3) |
| A200 | 22 | +13 bp (2.6) | +9 bp (1.5) | +2 bp | +4 bp |
| VHY (high yield) | 33 | +30 bp (3.4) | +21 bp (3.3) | +3 bp | +11 bp |

So units are about 10–14 bp rich just before they go ex, and about 30 bp for the high-yield fund, consistent with investors buying for the distribution and its franking credit. Volume on the day before is normal (0.9–1.1× the 20-day median). [1]

**Who gains from buying just before or just after?** [computed, on stated assumptions: VAS quarterly cash distribution 1.1%, franking credit 0.35%, 50% CGT discount on the eventual sale]

| Marginal rate incl. Medicare | Net tax effect of buying the day before ex instead of on ex | After the 10–14 bp price premium |
| --- | --- | --- |
| 0% | +0.35% | about +0.23% |
| 17% (15% + 2%) | +0.20% | about +0.08% |
| 32% | +0.06% | about −0.06% |
| 39% | 0.00% | about −0.12% |
| 47% | −0.07% | about −0.19% |

On a A$500 top-up the largest of these is about A$1. Under the post-July-2027 rules (no discount) the higher-rate rows move further negative. **No rule is justified.** Card H51 records the price effect for a clean test on unseen ex-dates.

### 6.4 Franking: what it is worth

- VAS's franking level is about 82% (October 2026 distribution 82.2%; fund level 81.5%; it ranged 68–82% over 2026). [1]
- Franking credits ≈ distribution yield × franked share × 30/70. At a 3.1–4.0% yield and 80% franked that is **1.1–1.4% of the VAS holding a year** [computed]. Published long-run estimates for the ASX 200 are 1.5–1.7% a year to a 0% taxpayer, and S&P's own franking-adjusted ASX 300 index beat the plain total-return index by 1.48% a year (tax-exempt) and 0.57% (15% super rate) from 2005 to 2022. [2+]
- The market does not fully price the credits: ex-day studies put the drop-off at 0.72–0.78 of the grossed-up dividend and about 1.0 of the cash dividend. Report 12 cites roughly 35% of face value. A resident who can use the credits therefore earns something the marginal price-setter does not. This is the structural Australian tilt, and it supports a home-bias weight above Australia's 2% world share. [2+]

| Account (40% VAS) | Franking credits a year | Share of the A$5,000 exemption |
| --- | --- | --- |
| A$5,000 | A$21–27 | 0.5% |
| A$25,000 | A$107–137 | 3% |
| A$100,000 | A$430–550 | 11% |

Franking credits reach A$5,000 a year only at about A$365,000–470,000 of VAS.

### 6.5 The 45-day rule [2+ from ATO pages via search; the pages themselves were blocked]

- Shares must be held "at risk" for at least 45 days, not counting the day of purchase or sale, to claim the franking offset.
- The rule is ignored if total franking credit entitlements for the income year are below A$5,000. ATO pages word the boundary both as "less than $5,000" and as applying at "$5,000 or more"; the spec's "≤ A$5,000" (TAX-07) should be read as **strictly less than** until the tax agent confirms.
- Last-in-first-out identifies which units were sold.
- Whether credits received through a trust such as VAS count toward the exemption in the same way is still open (T3).

**Interaction with L1.** A trend exit that sells VAS within 45 days of a purchase loses nothing while credits stay under A$5,000. TAX-07 already tracks this. No change except the boundary wording (section 11.4).

### 6.6 Recommendation

- **Owner guidance:** franking is worth roughly half a percent of the account a year and arrives by holding VAS. Do not trade for it.
- **Hypothesis card H51** for the pre-ex-date premium.
- **Spec text:** one boundary correction in TAX-07; close P9.

---

## 7. Topic 5 — Index events, June tax-loss selling and July

### 7.1 June and July [2+]

Total return by calendar month, Australian market (French, local currency), 1975–2025, % a month:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1975–2025 | 1.52 | 0.20 | 0.88 | **2.86** | 1.02 | **−0.24** | **2.35** | 1.33 | 0.23 | −0.07 | 0.63 | **2.30** |
| 1975–1991 | 3.47 | −0.89 | 2.26 | 3.82 | 3.05 | −0.96 | 3.54 | 2.70 | 1.31 | −1.73 | −0.04 | 2.85 |
| 1992–2008 | 0.54 | 0.62 | 0.07 | 2.71 | 0.53 | 0.62 | **0.25** | 0.59 | −0.22 | 0.25 | 0.73 | 2.58 |
| 2009–2025 | 0.53 | 0.87 | 0.29 | 2.04 | −0.52 | −0.38 | **3.28** | 0.70 | −0.40 | 1.26 | 1.21 | 1.47 |

Unconditional mean 1.08% a month. t-statistics against other months: April +3.4, December +2.7, July +2.0, June −2.8.

- **July** was positive in all 12 years 2012–2023 on the All Ordinaries price index (+3.3% average), and again in 2024 (+4.2%) and 2025 (+2.4%). But it averaged only +0.25% over 1992–2008. Fifty-one observations split three ways is not a basis for a rule.
- **June** weakness sits in the first ten trading days (−0.7% on average 1980–2024, t = −1.6), not the last ten (+0.1%).
- **Small caps carry the tax-loss pattern.** Small Ordinaries minus ASX 20: June −1.7% (t = −2.9), July +1.3% (t = 2.0), August +1.6% (t = 2.4), 2001–2024. Zero-dividend stocks lag the market by 1.8% in June. This matches Brown, Keim, Kleidon and Marsh (1983) and Brown, Ferguson and Sherry (2010), who found heavier June selling and a July rebound in losers, especially small mining stocks, for 1994–2007.
- **April and December** are as strong as July and more stable across eras. They have no Australian tax explanation, which is a warning that these are patterns, not mechanisms.

**Can a VAS/VGS system use it?** Not as a trading rule: the small-cap effect is not in VAS (its largest 20 stocks dominate it), and the index effect is one bet a year with a standard deviation of about 2 points over a two-week window. The only free choice the owner has is *when in June a contribution is invested*:

| Contribution | Expected gain from investing in the last days of June rather than the first half | Per year |
| --- | --- | --- |
| A$500 a month | 0.7% of one contribution | about A$3.50 |
| A$2,000 a month | same | about A$14 |

That is below one brokerage fee and not statistically reliable. **Reject as a rule; mention to the owner.**

**One real end-of-year action** is outside the system's rule: realising a loss before 30 June to offset gains. The spec already warns on a loss sale followed by a re-buy within 30 days (TAX-09) and holds the Part IVA question open (T7). Nothing to add.

**A one-off to watch:** the CGT change on 1 July 2027 (TAX-04, TAX-05) could distort June–July 2027 trading in ways the history above cannot show. [unverified]

### 7.2 Other calendar windows

| Window, All Ordinaries price index | 1980–1999 | 2000–2011 | 2012–2024 |
| --- | --- | --- | --- |
| Turn of month (last day + first three), % a year captured | 6.0% (t = 5.1) | 2.9% (2.1) | **0.2% (0.1)** |
| Last 10 trading days of December | +2.6% (5.1) | +1.3% (1.6) | +2.0% (2.3) |
| First 3 days of each quarter, % a day | 0.19 | 0.04 | 0.11 (not significant) |
| Day of week, ASX 200, 2000–2024 | No day differs from zero (largest t = 1.6) | | |

The turn-of-month effect was large and has gone. A 2000–2019 thesis on the ASX 300 found the same decay and a negative effect after 2016. [2+] **Reject.**

### 7.3 Quarterly index rebalances [2+ for the rules; 1 for my test]

- S&P/ASX 20, 50, 100 and 200 rebalance quarterly, effective after the close on the third Friday of March, June, September and December. The 300 and All Ordinaries change only in March and September. Since September 2021 the announcement is on the first Friday of the month, two weeks ahead. (The S&P methodology page was blocked; this rests on several secondary sources and ASX announcements.)
- Stock level: additions show price pressure between announcement and effective date that partly reverses over the next 20 days (Zhao, Schmidt and Terry 2016). That is a single-stock trade, out of scope.
- Index level, 95 rebalance days 2001–2024: return on the day +0.20% (t = 2.1), next day 0.00%, next five days +0.21% (t = 1.1), absolute move the same as any other day. The day-zero figure is one significant result among several windows tested and coincides with index futures and options expiry; I treat it as chance. STW volume was 1.28× its 20-day median and VAS 1.06×.
- ASX says closing-auction volume is "much higher on days when indexes are being rebalanced". The system trades 11:30–15:00, so this does not touch it.

**Recommendation: reject.** No calendar entry is needed. VAS and A200 turnover from rebalances is the fund's cost, already inside tracking difference.

### 7.4 ETF creation and redemption

For the system's ETFs this is invisible: spreads are 0.02% (VAS, A200, VGS, BGBL, VGAD) and daily turnover is A$7–18 million a day in VAS, A200 and VGS (2024 medians), against orders of A$2,000 to A$60,000. October 2026 net inflows were +A$334 million to VAS and +A$307 million to A200 (ASX report). There is no signal in flows that I could test with one month of data. [1]

---

## 8. Topic 6 — ASX microstructure for small ETF orders

### 8.1 Session times [1 primary: ASX trading-hours page already in the project downloads]

| Phase | Time (Sydney) |
| --- | --- |
| Pre-open | 07:00 – 09:59 |
| Opening single price auction, all securities | 09:59:00, randomised 15 seconds; continuous trading from 09:59:45 |
| Normal trading | to 16:00 |
| Pre-CSPA | 16:00 – 16:10 |
| Closing single price auction | 16:10:00 (randomised 30 seconds) to 16:11 |
| Post close (trading at the auction price) | 16:11 – 16:21:30 |

The brief's times (09:59 open, 16:10 close) are confirmed, and they match section 4 of the spec. The staggered 10:00–10:09 open that older guides describe ended on 23 June 2025.

### 8.2 The first print is the expensive one [2+]

Mean of log(close ÷ first trade of the day), by era, in basis points. A negative number means the first trade was above the close.

| | 2012–2017 | 2018–2021 | 2022–2024-05 | t-stat, latest era |
| --- | --- | --- | --- | --- |
| VAS | −15.5 | −6.1 | −3.3 | −1.6 |
| A200 | — | −5.7 | −3.5 | −1.7 |
| IOZ | −11.7 | −3.2 | −1.3 | −0.6 |
| STW | −3.7 | −2.8 | −0.8 | −0.4 |
| VGS | −14.2 | −7.6 | −6.4 | −3.9 |
| VGAD | −8.4 | −13.1 | −11.1 | −5.6 |
| IVV | −5.0 | −4.4 | −5.6 | −3.5 |
| BGBL | — | — | −15.6 | −5.2 |
| VHY | −13.8 | −12.9 | −8.2 | −3.5 |
| MVW | −7.8 | −5.6 | −6.7 | −2.5 |
| BHP (control) | −3.5 | −2.9 | +0.3 | 0.1 |
| CBA (control) | −1.1 | −2.6 | −0.6 | −0.2 |

The bias is specific to ETFs, largest in international and retail-heavy funds, and has shrunk for the Australian-share funds as they have grown. The likely cause is retail market buy orders meeting wide early quotes. It is an average: on any one day the first print can be on either side.

**Opening prices are also noisier.** Using pairs of funds that track nearly the same index, I split each fund's price into a common part and a fund-specific error:

| Pair, 2022–2024 | Error at the close (standard deviation) | Error at the first print |
| --- | --- | --- |
| VAS / IOZ | 5.0 bp | 11.4 bp |
| VAS / A200 | 5.8 bp | 12.2 bp |
| VGS / IVV | 11.4 bp | 24.3 bp |
| VGS / BGBL (2023-06 on) | 7.2 bp | 28.4 bp |

(The VGS pairs track different indices, so their close figures overstate the true error.)

Four practitioner guides say the same: wait until about 10:20–10:30, spreads are U-shaped through the day for Australian-share funds, and the pattern is weaker for international funds because their markets are closed (Ausiex, Russell Investments, Livewire, SSGA; read as search summaries, pages blocked). [2+]

**Size of the saving** (3–16 bp on the order value):

| Account | Typical order | Saving per buy |
| --- | --- | --- |
| A$5,000 | A$2,000–3,000 | A$0.60–4.80 |
| A$25,000 | A$10,000–15,000 | A$3–24 |
| A$100,000 | A$40,000–60,000 | A$12–96 |

At A$5,000 that is up to 70% of the A$6.60 commission.

### 8.3 Opening auction, closing auction or continuous trading?

- **Opening auction: no.** Section 8.2. IBKR also lists no opening-auction order type for ASX.
- **Closing auction: possible, not worth it.** The closing price carries a 5–7 bp fund-specific error (table above; a Roll-type estimate from the negative autocorrelation of ETF-minus-index returns gives 11–14 bp round trip). A marketable limit order at midday crosses half of a 2 bp spread: about 1 bp, or A$0.30–0.50 on a A$3,000–5,000 order. The auction's advantage is matching a backtest's closing price, and the spec deliberately decides on yesterday's close and trades the next day, so that advantage does not apply.
- **Continuous trading, 11:30–15:00: keep.** It avoids the open, and ends an hour before the pre-close phase.
- **Time of day for the global ETF.** VGS's market makers hedge with US futures and the currency while the underlying markets are shut. I found no data showing a better hour within the ASX day. [unverified]

### 8.4 IBKR order types for ASX [2+ — two IBKR pages fetched 13 November 2026]

IBKR's exchange page for ASX lists, as **native to the exchange**: Good-Till-Cancel, Immediate-or-Cancel, Limit, **Limit On Close (bonds, stocks, warrants)**, Market-to-Limit, and Quote Request (options). Simulated by IBKR: Market, Stop, Stop Limit, Good-After-Time, Good-Till-Date, and others. **Market On Close is not listed for ASX. No on-open type is listed.** IBKR's order-types page describes Limit-on-Close as available for stocks in US and non-US regions with directed routing.

What this means for the system:

- The API order type would be `orderType='LOC'`, routed `exchange='ASX'` (the spec already forbids SMART, EXE-01).
- "Market" is simulated by IBKR on ASX, which is one more reason for EXE-02 (limit orders only).
- Good-Till-Date is simulated by IBKR, which is relevant to open item I15: it should work but depends on IBKR's servers, not the exchange.
- What I could not verify: the cut-off time for entering or cancelling a LOC on ASX, whether an unfilled LOC rests into the post-close session, and behaviour in the paper account (which does not simulate auctions). A one-unit live test would settle it. [unverified]

### 8.5 Recommendation

**Execution tweak: none needed; confirm the existing rule and correct one note.** Card H50 tests the first-print bias on data I have not seen. Spec text in section 11.2.

---

## 9. Topic 7 — Concentration

### 9.1 How concentrated [2+]

- Top 10 = **49.2%** of the S&P/ASX 200 at 27 March 2026, up from 45.6% in November 2025; long-run average 48.6% (VanEck, citing S&P and FactSet). STW's top 10 was 46.9% in February 2026 and IOZ's 48.4% (undated). The S&P factsheet was blocked.
- CBA and BHP are about 9.5–11% each; the four major banks plus Macquarie about 27%. Financials about 33%, materials about 22%. [1, secondary; figures vary by date]
- My test: ten stocks (CBA, BHP, CSL, NAB, WBC, ANZ, WES, MQG, RIO, TLS) explain **93% of the ASX 200's daily variance**, 2015–2024. The index has a 0.83 correlation with the average of the four big banks.

### 9.2 Do less concentrated variants do better?

Price indices, December 2000 to May 2024 (dividends excluded, so levels understate all of them):

| Index | CAGR | Volatility | Worst drawdown |
| --- | --- | --- | --- |
| ASX 20 | 3.97% | 13.5% | −44.7% |
| ASX 200 | 4.17% | 13.5% | −50.5% |
| MidCap 50 | 6.49% | 15.8% | −57.3% |
| Small Ordinaries | 3.20% | 17.7% | −62.9% |

Mid caps beat the top 20 by 2.8 points a year, in each of three sub-periods, but with t = 1.44, higher volatility and deeper drawdowns. Small caps did worse than large on every measure.

ETFs, price only:

| | 2014-04 to 2019-12 | 2020-01 to 2024-05 | Five years to Oct 2026, total return (ASX report) | Fee | Spread |
| --- | --- | --- | --- | --- | --- |
| VAS | 3.7% | 2.7% | 8.95% | 0.07% | 0.02% |
| A200 | — | 3.1% | 9.58% | 0.04% | 0.02% |
| MVW (equal weight) | 8.4% | 3.2% | 7.65% | 0.35% | 0.05% |
| EX20 (ex top 20) | — | 1.9% | 5.09% | 0.25% | 0.10% |

MVW minus VAS, 2014–2024: +3.0 points a year, tracking error 5.5%, **t = 1.74**, beta 1.10; deeper falls in 2020 (−30.6% against −26.9%). Almost all of the lead came before 2020 (+4.7 points a year then, +0.6 after), and the five years to October 2026 reversed it.

VanEck reports that when top-10 concentration was at or above its average, equal weight beat the index over the next five years "in every single observation, 91 out of 91". That is 20 years of overlapping five-year windows, which is about four independent observations, measured by the product's issuer. It is not evidence at the spec's standard. [1, vendor]

### 9.3 What the portfolio actually holds

With 40% in VAS and 60% in VGS, the ten largest Australian names are about 20% of the account and CBA or BHP about 4% each. The concentration problem belongs to an all-Australian portfolio, and the spec does not have one.

### 9.4 Recommendation

- **Keep VAS as the Australian sleeve. A200 is an equal choice** (0.04% fee against 0.07%, same spread, ASX 200 instead of 300). The difference is 1.2 bp of the account a year: A$0.60 at A$5,000, A$12 at A$100,000. Never sell VAS to switch; the CGT would take decades to recover.
- **Reject an equal-weight or ex-top-20 sleeve for live.** Extra fee 0.11% of the account a year (A$5.60 / A$28 / A$112 at the three sizes) for an edge that is not significant and has reversed.
- **Card H52** registers MVW as a paper control so the VanEck claim is tested forward, not argued.

---

## 10. Topic 8 — Super and retail flows

- **Super guarantee timing.** Until 30 June 2026 employers' contributions were due quarterly, on the 28th of January, April, July and October. From **1 July 2026**, under the Payday Superannuation Act (Royal Assent 6 November 2025), contributions are due within seven business days of each payday. [2+] Any quarterly lump has therefore been replaced by a steady weekly-to-monthly flow. I could not confirm post-July implementation detail.
- **Was there a quarterly pattern to lose?** Returns in the five trading days from each due date, 1993–2024: +0.30% against +0.32% for the 28th of other months. No difference (t = −0.1). The 1993–2008 half shows +0.57% (t = 2.2) and the 2009–2024 half +0.02%. [1]
- **Turn of month**, the usual home of salary-linked flows, has disappeared (section 7.2).
- **Super funds and the dollar.** Foreign equities were nearly half of super funds' equity holdings at March 2022 (RBA Bulletin, March 2023), and the sector hedges about one-fifth of its listed overseas equities (RBA speech, 16 September 2025). A structural flow of this size leans on the dollar in one direction for years, which is context for section 3, not a signal. [1 primary]
- **Retail flows.** The first-print bias in section 8.2 is the measurable footprint of retail ETF buying: largest in retail-heavy funds, shrinking as funds grow. Report 12 covers the ASIC evidence on retail timing. I found no Australian flow series at a frequency that could be tested as a signal. [unverified]

**Recommendation: reject.** No rule, no card.

---

## 11. Exact spec text

All changes are additions or wording corrections. None changes a locked decision (D3, D5) or adds a live rule.

### 11.1 PRT-24 (hedging) — replace the row text

> | PRT-24 | **Hedging.** The global sleeve is unhedged. A hedged share is tested only as paper variant V3 (section 26.4). The currency is not modelled as a reliable crisis hedge. Every stress test of the live rule includes these two cases, built from history: **(a) no cushion** — global equities fall 12% in USD over four weeks while AUD/USD is unchanged (the four weeks to 4 April 2025: US equities −12.1%, AUD/USD −1.1%); **(b) currency drag** — AUD/USD rises 7.5% over twelve months while global equities return +13% hedged, giving about +5% unhedged (the year to October 2026: VGAD +13.1%, VGS +4.6%). The hedged share is not switched on any currency, rate or commodity signal: seven such signals tested on 1984–2025 gave no t-statistic above 1.7 before costs (report 39). | [R12], [R15 D5], [R39] |

### 11.2 D5 (decision log) — replace the "why" cell; and add one row to section 21.5

D5, third cell:

> Spreads and price variance are elevated just after the open: in 2022–24 the first trade of the day was on average above the same day's close by 3 bp (VAS), 6 bp (VGS), 11 bp (VGAD) and 16 bp (BGBL), and ETF-specific pricing error was two to three times larger at the first print than at the close [R39]. IBKR paper cannot simulate auctions. IBKR lists Limit-on-Close as a native ASX order type for stocks and does not list Market-on-Close or any on-open type (IBKR ASX exchange page, read 13 November 2026); its entry cut-off and post-close behaviour are untested (I18). The closing auction is not used: for orders of this size its pricing error exceeds the half-spread paid in continuous trading [R39].

Section 21.5, new row:

> | I18 | Only if a later spec version proposes closing-auction execution: the cut-off time for entering and cancelling an ASX `LOC` order through the API, whether an unfilled `LOC` rests into Post Close (16:11–16:21:30), and the fill price against the published CSPA price | One-unit live test (paper does not simulate auctions) | Not blocking; blocks any closing-auction proposal | [R39] |

### 11.3 Section 21.6, row P9 — replace

> | P9 | The lowest non-zero resident marginal rate. **Resolved at secondary-source level:** 16% for 2024–25 and 2025–26, **15% for 2026–27**, 14% from 1 July 2027, on taxable income of A$18,201–45,000; Medicare levy 2% on top. Set `research.marginal_rates` to include 0.15 for runs under the pre-July-2027 setting and 0.14 for the post-July-2027 setting. The ATO rate table itself could not be opened; the builder reads it once before G0 | ATO published rates | G0 for H11 (confirmation only) | [R22 F-25], [R39] |

### 11.4 TAX-07 — replace one sentence

Replace "If the year's franking total is ≤ A$5,000 the credit is reported as claimable under the exemption (subject to T3)" with:

> If the year's franking total is below A$5,000 the credit is reported as claimable under the exemption (subject to T3). At exactly A$5,000 or more the 45-day result decides: ATO pages word the boundary both as "less than $5,000" and as the rule applying at "$5,000 or more", so the engine uses the stricter reading until the tax agent confirms [R39].

### 11.5 Section 30 (the statement each user signs) — add one paragraph of owner guidance

> **Australian features you should expect.** (1) The global holding is not currency-hedged. In most equity falls since 2000 the Australian dollar fell too and softened the loss, but it did not in April 2025, and in a year when the dollar rises this holding will lag a hedged fund by roughly the size of the rise (8.5 points in the year to October 2026). (2) About half a percent of the account a year arrives as franking credits on VAS distributions. You receive it by holding; the system never trades to capture it. (3) Australian shares have tended to be weak in June and strong in July, April and December. The system ignores this: the pattern was absent from 1992 to 2008 and one month a year cannot be tested to the standard in section 24. (4) Ten companies are about half of VAS. The 60% global holding is the system's answer to that.

### 11.6 Section 21.7 (evidence gaps) — add three bullets

> - No Australia-specific predictor tested in report 39 (currency trend or level, commodity prices, yield curve, RBA cycle, calendar windows, index rebalance days, super due dates) gave an out-of-sample edge at a monthly horizon. None is in the registry, and adding one needs a new card.
> - Report 39's daily tests used unlicensed third-party copies of ASX end-of-day data to May 2024 and are exploratory. They saw data inside the holdout period (monthly to December 2025, daily to May 2024). Cards H50–H52 start their holdout after those dates.
> - Spot iron ore, single-stock dividend run-up studies, the S&P/ASX methodology and factsheet, and the ATO pages on franking and rates could not be opened for report 39; the related statements rest on secondary sources.

---

## 12. Hypothesis cards (RND-010 format)

Common to all three: date registered — on freezing; card hash, trials consumed, result, decision, approver — blank until frozen and run. Costs and tax: section 25 models. None is in the L1 Holm family; each is a design check decided by its stated threshold without a significance test, as H3, H4, H5, H8 and H9 are (RND-012). None can promote a live rule without a spec change.

### H50 — The first print of the day is a worse price than later continuous trading

| Field | Content |
| --- | --- |
| ID / family | H50 / A (execution design check) |
| Economic rationale | Retail market orders meet wide early quotes; market makers price international ETFs with less certainty at the open. If true, the 11:30 start in OPS-03 is justified by data, not only by guidance |
| Exact rule | For each trading day and ETF, x = ln(close ÷ first trade price). Statistic = mean of x over the sample, in basis points. Control: the same statistic for BHP and CBA |
| Fixed parameters | ETFs: VAS, VGS (live); A200, VGAD, BGBL, IVV (reported). Days with a distribution ex-date excluded. |x| > 10% excluded as data error |
| Permitted perturbation grid | Reference price: close; or (high + low + close) ÷ 3. No other variation |
| Data and proxy map | Licensed daily open/high/low/close from the spec's vendor (DAT), not the files used in report 39 |
| Sample and holdout | Development 2018-01 to 2024-05 (already seen in report 39: VAS −3.3 to −6.1 bp, VGS −6.4 to −7.6 bp). **Holdout 2024-06-01 to the freeze date**, never examined |
| Benchmark | Zero, and the BHP/CBA control |
| Primary metric → pass | Holdout mean of x for VGS ≤ −3 bp **and** for VAS ≤ 0 bp, with the control within ±2 bp → the opening blackout is confirmed and D5 stands |
| Fail | Holdout mean for both VAS and VGS > −1 bp → the bias has gone; record it, keep OPS-03 unchanged (it costs nothing), and drop the claim from D5 |
| Secondary metrics | Share of days with first trade above close; the pair-based opening and closing pricing error of section 8.2 |
| Multiple-testing family | None (design check, one statistic) |

### H51 — ETF units are priced rich in the days before the distribution ex-date

| Field | Content |
| --- | --- |
| ID / family | H51 / A (design check) |
| Economic rationale | Demand for the distribution and its franking credit from investors who value the credit above its market price; ETF arbitrage should remove it, so a persistent premium would be informative |
| Exact rule | For each ex-date of the ETF, r = cumulative (ETF total return − S&P/ASX 200 net total return) over trading days −5 to −1. Statistic = mean r across events, in basis points |
| Fixed parameters | ETFs: VAS (primary), A200, VHY (reported). Ex-dates from the `distribution` table, not inferred from prices. Window −5 to −1 |
| Permitted perturbation grid | Window −3 to −1; benchmark gross total return instead of net |
| Data and proxy map | Licensed daily ETF closes and distributions; licensed index total-return series (O5) |
| Sample and holdout | Development: ex-dates 2011-07 to 2024-04 (seen: VAS +13 bp, t = 1.8, 36 events). **Holdout: ex-dates from 2024-07-01**, 10 events by end 2026 and 4 a year after |
| Benchmark | Zero |
| Primary metric → pass | Holdout mean r for VAS ≥ +8 bp with at least 12 holdout events → propose (by spec change, not automatically) that contribution top-ups (PRT-16(b)) are not planned in the five trading days before an expected ex-date |
| Fail | Holdout mean r for VAS ≤ +3 bp → record "no premium"; no change |
| Secondary metrics | Days +1 to +10; the same for A200 and VHY; after-tax effect at 0%, 17%, 32%, 39%, 47% under both CGT regimes (RND-022) |
| Multiple-testing family | None (design check). Note the low power: 12 events cannot separate +8 bp from zero statistically; this is why a pass only permits a proposal |

### H52 — A less concentrated Australian sleeve does not beat VAS (paper control)

| Field | Content |
| --- | --- |
| ID / family | H52 / A (control; never a candidate for promotion from this card) |
| Economic rationale | Ten names are about half of the ASX 200. An issuer claims equal weight has always outperformed over five years from concentration at or above average. The control tests that forward |
| Exact rule | Static 40% Australian sleeve / 60% VGS, rebalanced yearly as B2. Arm A: VAS. Arm B: MVW. Arm C: A200 (fee control) |
| Fixed parameters | Weights and rebalance as PRT-22. No trend filter |
| Permitted perturbation grid | None |
| Data and proxy map | ETF total returns from the vendor, 2014-03 on (MVW inception). No index proxy before that: recorded "short sample" |
| Sample and holdout | Development 2014-03 to 2023-12. **Holdout 2026-01 onward** (report 39 quoted ASX-report returns to October 2026 for these funds; those five-year figures are declared as seen, so the forward test proper starts at the freeze date and reports yearly) |
| Benchmark | Arm A |
| Primary metric → pass (for "VAS is adequate") | Arm B's after-fee CAGR minus Arm A's < +1.0 point a year on the holdout **or** Arm B's maximum drawdown deeper than Arm A's by more than 2 points → no change |
| Fail (control triggers a review) | Arm B ahead by ≥ 1.0 point a year after fees over at least five holdout years **and** drawdown no more than 2 points deeper → register a new card for an Australian-sleeve change; do not switch from this card |
| Secondary metrics | Tracking error to Arm A; fee and spread drag at A$5,000, A$25,000, A$100,000; top-10 weight at each year start |
| Multiple-testing family | None |

### Ideas rejected without a card (so they do not count toward N)

| Idea | Why no card |
| --- | --- |
| Hedge timing on AUD trend, level, rate gap or commodity trend | Best t = 1.3 of seven before costs; switching costs 0.1–0.3% in brokerage plus CGT. V3 in H13 already covers hedged against unhedged |
| Commodity-trend overlay on VAS | Out-of-sample R² negative; overlay 3–5 points a year below buy-and-hold |
| Yield-curve or RBA-cycle overlay | Sign flips between eras; 1–2 points a year below buy-and-hold |
| June/July contribution timing | One observation a year; absent 1992–2008; worth A$3.50 a year at A$500 a month |
| Turn-of-month execution timing | Effect is 0.2% a year since 2012 |
| Avoiding index-rebalance days | No index-level effect; system does not trade the close |
| Super due-date timing | No effect; regime ended 30 June 2026 |

---

## 13. Sources

### Data and code (all in the scratchpad)

- Scripts: `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/au_signals/code/` — `aud.py` (loaders), `a1_aud.py`, `a1b_aud.py` (currency), `a23_pred.py` (commodities, rates), `a45_season.py` (dividends, calendar, rebalances), `a4b_exdate.py`, `a4c_exdate_tr.py` (ex-dates), `a6_micro.py`, `a6b_open.py` (microstructure), `a7_conc.py` (concentration), `a8_extra.py` (weekly currency, spot commodities, super dates), `extract_eod.py`.
- Outputs: `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/au_signals/data/` — `a1_out.txt`, `a1b_out.txt`, `a23_out.txt`, `a45_out.txt`, `a4b_out.txt`, `a4c_out.txt`, `a6_out.txt`, `a6b_out.txt`, `a7_out.txt`, `a8_out.txt`, `monthly_panel.csv`.
- RBA statistical tables F1.1, F2.1, F11, F11.1, I2 and historical F2, F11 and daily exchange-rate files (rba.gov.au/statistics), fetched 13 November 2026. [primary]
- Kenneth French data library: international country returns (Australia, with and without dividends), Developed and US factors, monthly and daily. [primary]
- GitHub: `rs77/asx-historical-data`, `arekbee/StooqHistoricalDataDaily`, `xiaohaoyanglei/asx200-dataset-axjo`. [third-party copies; cross-checked in section 2]
- ASX Investment Products monthly report, October 2026. [primary]

### Documents read directly

- ASX trading hours page (project download `dl/asxhours.txt`). [primary]
- Interactive Brokers Australia, exchange page for ASX and order-types page, fetched 13 November 2026 (interactivebrokers.com.au/en/trading/exchanges.php?exch=asx). [primary]
- RBA Bulletin, September 2009, "The Impact of Currency Hedging on Investment Returns". [primary]
- RBA Bulletin, March 2023, "Foreign Currency Exposure and Hedging in Australia". [primary]
- RBA speech, 16 September 2025, "A Hedge Between Keeps Friendship Green" (super funds hedge about one-fifth of listed overseas equities). [primary]
- ASX, "Finding value through ASX closing auctions", 23 August 2023 (closing auction about 21% of turnover). [primary]
- VanEck, "The ASX concentration risk is rising" (top 10 = 49.2% at 27 March 2026). [vendor]
- Brown, Ferguson and Sherry (2010), "Investor behaviour in response to Australia's capital gains tax", Accounting and Finance 50(4) — abstract on IDEAS/RePEc.
- Dou, Gallagher, Schneider and Walter (2012), "Out-of-sample stock return predictability in Australia", Australian Journal of Management 37(3) — abstract.
- Zhao, Schmidt and Terry (2016), "Index effects: evidence from Australia", UTS working paper — abstract.

### Known only through search summaries (hosts blocked)

- Brown, Keim, Kleidon and Marsh (1983), Journal of Financial Economics (July seasonal in Australia).
- Chen, Rogoff and Rossi (2010), Quarterly Journal of Economics, "Can Exchange Rates Forecast Commodity Prices?".
- Campbell, Serfaty-de Medeiros and Viceira (2010), Journal of Finance, "Global Currency Hedging" (the Australian-dollar-specific conclusion was not confirmed).
- Beggs and Skeels (2006), Economic Record; Treasury Finance Discipline Group paper (franking drop-off 0.72–0.78).
- ATO, "You and your shares 2026" (holding period rule, A$5,000 exemption, last-in-first-out); ATO and Budget pages on 2026–27 rates.
- S&P Dow Jones Indices rebalance rules (third Friday; first-Friday announcement since September 2021), via Market Index, Stockhead, ASX announcements.
- Payday super: Grant Thornton, SmartCompany, Mondaq, ATO media release (Royal Assent 6 November 2025; start 1 July 2026).
- ETF trading-time guidance: Ausiex, Russell Investments, Livewire, SSGA.
- InvestSMART (VAS franking 82.2% for October 2026; fund level 81.5%); S&P franking-credit-adjusted index figures via secondary articles.

### Hosts that would need to be allowed to close the gaps

www.spglobal.com, www.ato.gov.au, papers.ssrn.com, onlinelibrary.wiley.com, www.sciencedirect.com, www.marketindex.com.au, betashares.com.au, insights.ultumus.com, russellinvestments.com, axis.ausiex.com.au, thedocs.worldbank.org (iron ore), query1.finance.yahoo.com or stooq.com (daily prices after May 2024).
