# 72. Review of the Big Wins research, internet sweep, and the design brief for one buy-and-sell algorithm

16 November 2026. Author: research agent (Fable). Work folder: `scratchpad/r72/` (`code/desc_dev.py`, `out/desc_dev.txt`, `out/trials_72.csv`).
Research and paper only. General information, not financial advice. Nothing here can place an order.
No back-test was run on 2016 or later data. One descriptive run was made on 2001–2015 development data and is counted as a trial (library count 402 → **403**).

**Tags.** [2+] two or more independent sources agree. [1] one source or abstract only. [memory] from model memory, not re-checked today. [computed] my own figure from files held. [issuer] taken from the fund issuer's own page or data file.

---

## 0. Plain-English summary

1. **What has been done is sound, and its answer is consistent.** Across 403 counted trials, the best rule found (H82, "steady winners") is level with the index on data it never saw. In every one of six rounds, the attempted improvement gained in development and lost afterwards. I found no error that overturns this.
2. **The research has a blind spot that matters for the owner's actual request.** The owner asked for big winners. Nothing so far models "which shares go up 50% or more" directly. I measured it on 2001–2015: the single best predictor that a share will gain 50% is high volatility, and high volatility is an even better predictor that it will lose 50%. A model trained only to find +50% winners will buy the most dangerous shares on the board. The build agent's target must be changed before it trains anything (section 4.2).
3. **The untested ground is narrower than "everything".** Prices have been worked to exhaustion. What has never been tested as a signal: liquidity and volume measures, changes in short interest, resources and industrials as separate problems, and any signal-driven hold/sell rule with a buy/hold gap. What cannot be tested honestly at this budget: fundamentals, analyst revisions and director trades, because no affordable history exists that includes dead companies. Those can only be collected from today.
4. **The internet evidence points the same way as our own results.** Published stock-picking signals are real on paper but shrink by about half after publication in the US, live mostly in tiny illiquid shares, and lose 60–80% of their profit once those shares are removed. Machine learning adds a little over simple rules, almost all of it in shares a small account cannot trade cheaply. The methods that do survive costs are dull: combine a few signals into one score, trade slowly, and make it harder to buy than to keep holding.
5. **"Beat everything on the market" cannot be promised, and the bar is higher than the ASX index.** Over the ten years to October 2026 the ASX 200 funds returned about 9.3–9.6% a year, the owner's 40/60 mix about 12.3%, global shares 14.0%, the S&P 500 fund 16.1% and the Nasdaq fund 20.9%. An ASX-only share picker must beat the local index by about 3 points a year after costs and tax just to match the plan the owner already holds.
6. **The best algorithm I can justify** is one integrated score built from a small number of signal families, trained to rank shares by expected return with the loss tail counted, scored weekly, traded only when a share crosses a wide buy/hold gap and the expected gain exceeds twice the cost and tax of the trade, held in 25–30 equal positions with sector and commodity caps, taxed under the real July 2027 rules, re-trained once a year on a fixed recipe, and judged on paper against six named benchmarks with kill rules. Section 4 gives it in full.
7. **Honest expectation.** Most likely result: level with the ASX index, behind the 40/60 plan. Chance that a back-test can prove an edge: close to nil, because a real 3-point edge needs about 35 years of data to show at the ordinary 95% level and about 75 years at the programme's own bar (t of 3). The value of building it is a clean, hindsight-free forward record and a system that keeps learning. Real money stays in the index plan.

---

## 1. Part 1 — Review of what Fable and the earlier agents did

### 1.1 Every item the reports said the algorithm should look for, and its status

Status words: **Tested-failed** (ran, did not pass on unseen data). **Tested-alive** (ran, weak, on paper). **Dev-only** (ran on 2001–2015, never taken further). **Not done**. **Forward-only** (cannot be tested on history; collection needed).

| # | Item | Where asked | Status | Result or reason |
|---|---|---|---|---|
| 1 | Momentum 12-1, 6-month momentum, closeness to 52-week high, low volatility (H80 score) | R51, R53 | Tested-alive | H82: dev +6.3 / +3.2 pts a year; unseen level with index (R64: +1.3–1.4 pts, t 0.3–0.4; R68 after duplicate fix 8.3% / 10.0% vs 8.8%) |
| 2 | Sell rules: trend break, stops, trailing stops, loss cuts | R53 | Tested-failed | Best dev +1.6 pts; unseen −0.6 to −3.2 |
| 3 | More frequent review (half-yearly to monthly) | R55 | Tested-failed | Dev +1.2; unseen −1.6 at A$100k |
| 4 | Yearly self-adapting rule choice | R55 | Tested-failed | 4 of 5 worse; random choices did as well |
| 5 | Lottery (MAX), beta, reversal, seasonality, residual momentum, momentum ÷ volatility, months 12–7, share of up months | R56, R64 | Tested-failed (dev gate) | None added information beyond the H80 score |
| 6 | Frog-in-the-pan (H88), recency of the high (H90) | R56, R64 | Tested-failed | Failed both unseen sets |
| 7 | Tranches, inverse-volatility weights, resources cap, more shares, keep-while-rank ≤ 90, universe of 500 | R64 | Tranche failed unseen; rest dev-only | Only tranching passed dev; lost 1.5–3.8 pts unseen. Keep-buffer halved turnover at no loss (dev) and was not pursued |
| 8 | June tax-loss rebound in small caps (H100) | R59 | Tested-alive, weakening | 23 Junes +3.5% (t 2.1); the three newest Junes −0.3% |
| 9 | Neglected small caps (H101) | R59 | Tested-failed as a rule | Median pick loses; tracking line only |
| 10 | LIC discounts and premiums | R59 | Avoid rule alive | Premium fifth lags, pooled t −4.0, before costs |
| 11 | Share purchase plans | R59 | Not done | Issue prices not obtainable (4 of 1,228) |
| 12 | Index adds and deletes, spin-offs | R59 | Tested-failed | Lose after costs; spin-off sign flipped |
| 13 | Commodity and macro drivers through an exposure map | R60 | Tested-failed | Nothing beyond own momentum; map useful for risk only |
| 14 | Daily commodity lead on miners | R60 | **Not done** | "Not ruled out"; data held is monthly averages |
| 15 | News (GDELT) | R60 | **Not done** | API rate limit; forward-only |
| 16 | Commodity-regime tilt (H121) | R60 | Dev gate failed | Unseen looked good (+7.0 / +3.1); observation only |
| 17 | Short interest, top tenth, as an exclusion | R61 → R62 | Tested-failed | Wrong sign on unseen data |
| 18 | **Change** in short interest; low short interest as a positive; days to cover | R61 (implied) | **Not done** | Only the level was tested |
| 19 | Aggregate short interest as a market signal | R61 #21 | **Not done** | Asked of R60; no result recorded |
| 20 | Dilution (12-month share growth) | R61 → R62 | Stand-alone confirmed; exclusion failed | Flagged shares −3.5 pts (t −2.2) unseen; engine rarely holds them |
| 21 | Dilution forward shadow line on the paper book | R68 #5 | **Not done** | No share-count field in the forward snapshot code [computed: grep of `bigwins_forward/code`] |
| 22 | Listing age | R61 → R62, R64 | Flag only | −8.9 pts unseen (t −1.5); exclusion did nothing |
| 23 | Results-day reaction on real dates | R61 → R62 | Tested, not robust | Dev t 2.8; failed June replication; survivors-only data |
| 24 | Director trades (Appendix 3Y) | R61 #4 | **Forward-only, not started** | 84,673 notice headlines held, direction unknown without the PDF |
| 25 | Resources and industrials as separate problems | R61 #5 | **Not done** | Parked "until licensed data"; EODHD is now held but has no dated sector |
| 26 | Announcement flow, price-sensitive intensity | R61 #7 | Table built; **never tested** | 1.26 million headlines held; survivor-biased |
| 27 | Liquidity, turnover, volume, spreads as signals | R61 #8 | **Not done** | Marked "fix the data"; data now fixed (panel_v2); no test followed |
| 28 | Cash runway (4C/5B), going concern | R61 #9 | **Forward-only, not started** | 30,443 4C/5B headlines held; figures are in PDFs |
| 29 | Event seasonality, dividend changes, halts, substantial holders, takeover targets, management changes, guidance | R61 #10–17 | **Not done** | Parked or event-table only |
| 30 | Analyst coverage, revisions, targets | R61 #16 | **Forward-only, not started** | No affordable dated history |
| 31 | Accounting quality, valuation, profitability | R57, R61 #18–19 | **Not testable** | Fundamentals held are survivors-only, six years, restated; licence bars ML training |
| 32 | Quality through ETFs (H97 scoreboard) | R57 | Proposed; no scoreboard file found | AQLT ahead since 2022; see section 3 |
| 33 | Forward archive of filings (schema `fa`) | R61 A5, R62 | **Partly**: ASIC daily files are being kept (`asic_archive/`); nothing else | ASX fetch permission unresolved (R62 §7.1) |
| 34 | Monthly fundamentals snapshot job | R58 | **Not scheduled** | Owner decision never recorded |
| 35 | ASX listed-companies file saved monthly (dated sectors) | R68 #7 | **Not started** | First forward snapshots used a file dated 14 Nov 2026 |
| 36 | Real quotes for H100 names | R68 #2 | Due June 2027 | — |
| 37 | Outcomes of shares that stopped trading after April 2020 | R68 #3 | **Not done** | A few hours by hand; moves unseen B by 2–3 points under stress |
| 38 | Norgate rental (dev period in total return, index membership) | R53, R68 #4 | Owner: hold off | Still the only way to check 2001–2015 with dividends |
| 39 | EODHD fundamentals forward snapshots | R68 #6 | Not started | About A$93 a month |
| 40 | Clean total-return panel, rename and calendar fixes | R51–R63 | **Done** | panel_v2 and EODHD; verdicts unchanged |
| 41 | Verify the deflated-Sharpe formulas against the papers | R51 | **Not done** | Still "from memory" in R64 |
| 42 | Position sizing by signal strength; risk balancing by commodity exposure | Deep-dive prompt | Partly | Inverse-vol and a resources cap tried; exposure-map caps never tried |
| 43 | A model of big winners as such (the NEXTDC request) | R31, R51 | One screen only | "NEXTDC look-alike" screen: median −18% over five years. No model of the +50% outcome until today (section 1.4) |
| 44 | Learning engine that records and improves (R52) | R52, R68 §2.9 | Designed; ledger started | No retraining loop exists yet |

### 1.2 Mistakes, gaps and weak points

Ranked by how much they could change a conclusion or mislead the build.

1. **The unseen years are no longer unseen.** The 2016–May 2024 window has been read at least 12 times for the momentum family (briefing §2.2), plus three more looks in R64 and a correction in R68. Any engine containing momentum, the 52-week high or low volatility has been chosen with knowledge of how those behaved after 2015. Report 70's "one unseen look" is a re-used holdout and must be labelled so. Only data after 14 November 2026 is clean.
2. **The objective tested was never the objective asked for.** Every report optimised the average after-tax return of a 10–30 share book. None modelled the +50% outcome. Section 1.4 shows why this matters: the features that find winners also find wrecks.
3. **Loss labels are contaminated.** On development data, 26% of all "fell 50% or more within 12 months" outcomes include a data row flagged as a residual split, spike or unexplained ±45% move, against 6.5% for all shares and 4.8% for winners [computed]. Missed splits of dead companies show up as fake collapses. A model trained on raw labels will partly learn data errors. No report has cleaned the labels.
4. **Franking credits are left out on both sides** (R64 limits). The index yields 4.1% and the engine's shares 3.1%. At roughly 70–80% franking, the index gets about 0.3–0.4 points a year more in credits than the engine [computed, approximate]. The reported "level with the index" is therefore slightly flattering to the engine.
5. **The tax model is a stand-in, and the law has moved.** The May 2026 Budget replaces the 50% discount with cost-base indexation and a 30% minimum tax on real gains for assets held over 12 months, for gains accruing from 1 July 2027 [2+: PwC, BDO, Baker McKenzie, Chartered Accountants ANZ, via search listings]. Whether the bill has passed is reported both ways [conflicting; unverified]. R64's "Regime B" ignores indexation and the transition split. R66 handled this for the index plan; the engine has not been re-run under the real rule. The change also taxes the index holder more at the end, so the relative penalty for trading shrinks. That needs measuring, not assuming.
6. **Ten-share books kept being reported as if they meant something.** R64 itself measured a 2.2-point gap between two data sources at A$25,000 from a handful of different picks, and a 3.7-point spread between start months. Results at A$25,000 should be shown only as a warning.
7. **Sectors are not dated.** Industry groups come from today's ASX file, so dead companies have none and the 25% cap is weaker in history than in the rules. "Resources against industrials" could not be tested for this reason.
8. **Delisting outcomes after April 2020 are assumed** (paid in full, or 70% under stress). The assumption alone moves the 2018–2026 result by 2–3 points.
9. **Costs have never been checked against a real quote.** Every spread is modelled. For the small-cap ideas the edge equals the modelled cost.
10. **The deflated-Sharpe code is still unverified against the source papers.** It has not changed a verdict (nothing is near the bar), but it is the programme's main luck control.
11. **Some of the "fixes" were themselves fitted.** Tranching was adopted because it removed start-month luck in development, then lost on unseen data. Judging on eight start-month accounts is right; choosing a construction because it scores well on that measure is still selection.
12. **Development data remains price-only and unlicensed** before 2018. Dividends cost the engine about one point a year against the index after 2018; the same is probably true before, so the development lead of 3–6 points is overstated by about one.
13. **The events table has been treated as usable history; it is not.** It covers only companies listed today: 22% of codes trading in 2009, 50% in 2019, 80% in 2024. It cannot be used to train anything. Its legal status is also open (ASX terms forbid automated access).
14. **No test of interactions.** Whether a signal works differently in small and large shares, or in miners and non-miners, has never been examined. The literature says most of the action is in that interaction (section 2).
15. **Trial counts were under-stated for several reports** (fixed in the briefing: 385, then 402 after R64). With this report, 403.

### 1.3 Data held and not used

| Data | Held where | Used so far | Unused part | Can the model use it? |
|---|---|---|---|---|
| Daily open, high, low, volume, traded value 1997–2024, dead companies included | `data_foundation/out/panel_v2_long.pkl` | Closes only; traded value for ranking | Range-based volatility, overnight gap, Amihud illiquidity, turnover trend, zero-volume days, volume surges | **Yes.** Dated, includes dead companies. Unlicensed copy: research only |
| ASIC daily short positions and shares on issue, 2010–2026 | `flags/out/asic_long.pkl`, `asic_archive/` | Level of short interest (top tenth); 12-month share growth | Change in short interest, days to cover, low-short positive, market-wide short interest, share shrinkers | **Yes from mid-2010.** Published with a four-day lag; licence unread (private use) |
| ASX announcement headlines, 1.26 million, Jul 2009–Nov 2026, with price-sensitive flag | `niche/out/events.csv.gz` | Results dates (4E/4D); SPP events | 84,673 director notices, 103,547 substantial-holder notices, 18,618 halts, 30,443 cash-flow reports, 17,529 placements, 4,509 guidance items | **No for training** (survivors only). Forward use only if the ASX access question is settled |
| EODHD total-return panel, 4,488 symbols | `data_foundation/out/eodhd/panel_tr.pkl` | Engine re-runs 2018–2026 | ETF and LIC total returns (used here for the benchmark table); open/high/low/volume after 2018 | **Yes** (personal licence). Weak before 2018 for dead companies |
| Drivers database: 82,500 company-month commodity exposures | `drivers/db/drivers.duckdb` | Signal tests (failed) | Exposure caps in portfolio construction | **Yes, for risk caps.** Betas must be estimated on data before each date |
| Delisting reasons 2000–2020 | `company_study/data/delist.pkl` | Payout rules | A "failure" label for a loss-tail model | **Yes to 2020** |
| ETF monthly flows 2017–2026 | `niche/out/etf_flows_monthly.csv` | Not used | All | Low value; market-level only |
| Index add/delete events 2012–2024 | `niche/out/index_events.pkl` | Event test (failed) | Dated index membership as a universe definition | Partly; 129 unmatched |
| Company financials, 1,786 companies, six years | `company_db/db/asx_company.duckdb` | Screening | All | **No.** Survivors only, restated, and the source's terms bar ML training |
| Issuer NAV and distribution files for A200, BGBL, DHHF, VAS, VGS, VDHG | `actuals/data/` | R47, R64 comparators | — | Yes; the benchmark source of truth |

### 1.4 New descriptive finding on development data (trial D1, counted)

Top 500 shares by 63-day median traded value, every month-end from December 2000 to December 2014, price-only, next 12 months (84,473 share-months; a share that stopped trading is carried at its last price). No strategy was simulated.

| Group | Chance of +50% or more | Chance of −50% or worse | Mean | Median |
|---|---|---|---|---|
| Ranks 1–100 | 7.7% | 5.6% | +5.7% | +4.6% |
| Ranks 101–300 | 13.5% | 15.0% | +4.1% | 0.0% |
| Ranks 301–500 | 17.1% | 18.4% | +6.5% | −5.3% |
| Lowest-volatility fifth | 4.4% | 3.4% | +5.7% | +6.0% |
| Highest-volatility fifth | 17.3% | **28.6%** | +1.6% | **−22.9%** |
| Lowest-momentum fifth | 12.9% | 23.9% | −3.8% | −15.0% |
| Highest-momentum fifth | **19.3%** | 16.1% | +11.3% | 0.0% |
| Furthest from 52-week high (fifth) | 14.4% | 28.3% | −4.4% | −22.1% |
| Closest to 52-week high (fifth) | 13.0% | **6.4%** | **+12.5%** | **+6.6%** |
| Gained 50%+ in the prior 12 months | 19.4% | 15.7% | +10.7% | −0.5% |

How well each single signal separates the outcomes (0.50 = no better than chance):

| Signal | Finds +50% winners | Finds −50% losers | Rank correlation with the 12-month return |
|---|---|---|---|
| High volatility | 0.61 | **0.72** | −0.20 |
| High momentum | 0.56 | 0.44 (so low momentum finds losers at 0.56) | +0.11 |
| Close to 52-week high | 0.49 (none) | 0.31 (so distance from the high finds losers at **0.69**) | +0.22 |

What this says:
- **Big winners are common, and so are wrecks.** In the mid and small groups, one share in seven to one in six gains 50% in a year, and slightly more lose half.
- **The best "winner detector" is a risk detector.** Volatility separates winners from the rest better than momentum does, and separates losers better still. A classifier aimed at +50% alone will rank by volatility and small size and buy a group whose median share loses 23%.
- **The engine's edge is in avoiding wrecks, not in finding rockets.** Closeness to the high has no power to find winners and strong power to avoid losers, and it has the best link to the average return. This is what R51 and R61 said in words ("mostly about which stocks to avoid"); now it is measured.
- **Momentum is the only signal that raises the winner rate (13% → 19%) without raising the loser rate above average.** That is the honest size of "predicting big winners" from prices: six extra winners per hundred shares.
- Caveat: one in four loser labels touches flagged data, so the loser rates are somewhat overstated.

---

## 2. Part 2 — Internet sweep: what survives costs, out of sample

**Reach.** Web search worked. Full text was reachable only on a few hosts. SSRN, ScienceDirect, Wiley, S&P, Alpha Architect and the ATO returned 403; several university and issuer hosts did not resolve. Most academic items below are therefore from abstracts, publisher listings and secondary summaries, and are tagged. I did not open a full paper today. Report 64 read Daniel–Moskowitz and Hou–Xue–Zhang in full.

### 2.1 The base rates

| Question | Best evidence | What it says | Tag |
|---|---|---|---|
| Are published signals real? | Hou, Xue, Zhang, *Replicating Anomalies* | 64% of 447 fail once micro-caps are removed; 85% at t ≥ 3 | Read in R64 |
| | Jensen, Kelly, Pedersen, *Is There a Replication Crisis in Finance?* (J. Finance 2023) | 153 factors, 93 countries; about 82–85% replicate when grouped into themes and judged with a Bayesian model. The two papers disagree less than they seem: signals cluster into about a dozen themes, the themes are real, and individual variants are not independent discoveries | [2+] |
| Do they decay after publication? | McLean, Pontiff (2016) | US returns about 50–58% lower after publication | [2+] |
| | Jacobs, Müller (JFE 2020), 241 signals, 39 markets | Decay is strong in the US and mostly insignificant elsewhere. Barriers to arbitrage keep markets segmented | [2+] |
| | A 2025 working paper, *Out-of-Sample Alphas* | Average post-publication alpha close to zero and insignificant (US) | [1], not read |
| Do they survive trading costs? | Novy-Marx, Velikov (RFS 2016) | Most signals with one-sided turnover under 50% a month keep a significant net spread if built to save costs; few faster ones do. A buy/hold spread (harder to enter than to stay) is the most effective cost saver | [2+] |
| | DeMiguel, Martín-Utrera, Nogales, Uppal (RFS 2020) | Combining signals cuts trading cost by about 65% because trades cancel; more signals matter after costs, not fewer | [1] |
| Where do the profits live? | Avramov, Cheng, Metzker (Management Science 2023) | Machine-learning profits fall 62% without micro-caps, 68% without unrated firms, 80% without distressed firms; high turnover; long side and recent years still positive | [2+] |
| | Dou, Gallagher, Schneider (Aust. J. Management 2013) | In Australia, size, value, profitability, asset growth and accruals come mainly from micro-caps. **Momentum and asset growth work in big shares; momentum does not work in micro-caps** | [2+] |

**Reading for this project.** Australia is a segmented, smaller market where decay after publication is weaker than in the US. That favours simple known themes over new discoveries. The one theme with Australian large-share support is momentum, which is what H82 already uses.

### 2.2 Machine learning in the cross-section

| Study | Finding | Bearing | Tag |
|---|---|---|---|
| Gu, Kelly, Xiu (RFS 2020), US 1957–2016 | Monthly out-of-sample R² about 0.33–0.40% for trees and neural nets against 0.26% for the best linear model. Long-short Sharpe 1.35 value-weighted, 2.45 equal-weighted. All methods agree the dominant signals are **momentum, liquidity and volatility** | The gain from ML over linear is real but small; the equal- versus value-weight gap shows it sits in small shares. Liquidity is one of three dominant families and we have never tested it | [2+] |
| Leippold, Wang, Zhou (JFE 2022), China | Liquidity and fundamentals lead; price trend matters less; retail-dominated small shares are the most predictable at short horizons; survives costs | A retail-heavy market behaves differently from the US; ASX small caps are retail-heavy | [1] |
| Cakici, Fieberg, Metko, Zaremba (JEDC 2023), 46 markets | Predictability varies with the number of listed firms and with idiosyncratic risk; depends heavily on firm size | Small markets with few liquid names give ML less to work with | [1], abstract |
| Chen, Hanauer, Kalsbach, *Design choices in ML* | 1,056 model variants from reasonable design choices give widely different results | A single ML back-test is one draw from a wide range; choices must be fixed in advance | [1] |
| Australia-specific ML study | **None found** in two searches | Report 70 has no local precedent to lean on | — |

**Arithmetic for our data.** Development holds about 500 shares × 169 months ≈ 84,000 rows, but 12-month labels overlap, so there are about 14 independent years. A model with hundreds of free parameters will fit those 14 years. The prior from the literature and from six of our own rounds is that a flexible model will match the linear score in development and trail it afterwards.

### 2.3 Predicting extreme winners

| Evidence | Finding | Tag |
|---|---|---|
| Bessembinder, Chen, Choi, Wei (FAJ 2023), 64,000 global shares, 1990–2020 | 2.4% of shares produced all net wealth creation; 57.4% of non-US shares did worse than Treasury bills. Skewness is stronger outside the US | [2+] |
| Conrad, Kapadia, Xing (JFE 2014), *Death and jackpot* | Shares with a high **predicted** chance of a jackpot return earn abnormally **low** average returns; the same shares have a high chance of failure | [2+] |
| Bali, Cakici, Whitelaw (MAX effect) | Lottery-like shares underperform | [memory]; our R56 test of MAX failed as a buy signal, consistent |
| Yartseva (2025 working paper, not peer reviewed), 464 US ten-baggers 2009–2024 | Small size, cheap valuation (free-cash-flow yield), profitability; earnings growth not predictive; winners were often **not** near 12-month highs at the start | [1], secondary summaries; hindsight sample of winners only |
| Our D1 run (section 1.4) | Same pattern on the ASX: winner probability and loser probability rise together | [computed] |

**Reading.** Two independent sources and our own data agree: aiming at the jackpot selects overpriced lottery shares. Big winners have to be reached indirectly, by ranking on expected return, cutting the loss tail and holding long enough for the few that run to compound. Valuation and profitability appear in the winner studies and cannot be tested by us (no dated fundamentals).

### 2.4 Signal by signal

| Signal | Effect size reported | Out-of-sample / Australia | Survives retail costs and tax? | Data an individual can get legally |
|---|---|---|---|---|
| Momentum (12-1, 6-month) | About 1% a month long-short in early studies | Works in Australian big shares (Dou et al.); significant after spreads 1990–2007 (Pac.-Basin Fin. J. 2009) [1]. Ours: dev yes, unseen level | Yes at yearly turnover; no at monthly on A$2,500 parcels (R56: 12 points a year) | Prices: EODHD (held) |
| 52-week high | — | Bettman, Sault, von Reibnitz (2010), ASX 1996–2008: no significant dollar profit among liquid shares after costs and short-sale limits [1] | As a loser-avoider inside a composite, yes (our D1) | Prices |
| Low volatility / avoid lottery | — | Our D1: strongest loss-avoider | Yes (it lowers turnover) | Prices |
| Liquidity (Amihud, turnover) | One of three dominant families (Gu et al.) | Never tested here | Unknown; illiquid shares cost more to trade, so it must be tested net | Prices and volume (held) |
| Short-horizon composite (reversal, short momentum, revisions, short-term risk, seasonality) | Blitz, Hanauer, Honarvar, Huisman, van Vliet (FAJ 2023): net alpha above 6% a year on MSCI World 1985–2021 with a rule that buys in the top 10% and holds to the 50% line; single signals turn over 1,300–2,000% a year; costs took more than two-thirds of gross | Large liquid shares, 25 basis points assumed cost, institutional execution, analyst data needed | **No at retail scale.** A$6 minimum on A$2,500 is 24 basis points a side before any spread; ASX mid-cap spreads add 20–100. Our R56 short-horizon tests lost 6–12 points a year to costs | Analyst revisions not available |
| Earnings-announcement drift | Classic US effect | Australian studies exist (Bird, Choi, Yeung 2011; a University of Sydney thesis finds algorithmic trading has not removed it) [1]. Ours: dev t 2.8, unseen 1.1–2.1, failed replication | Marginal | Results dates: ASX site by hand; headline harvest is survivors-only |
| Analyst forecast revisions | Among the strongest short-term signals internationally | Hou, Hung, Gao (2014), ASX 1992–2009: drift after revisions, stronger under uncertainty [1] | Unknown here | **No affordable dated history.** EODHD lists ASX fundamentals; ASX estimate coverage is unconfirmed. Forward collection only |
| Director trades (Appendix 3Y) | US: buys informative | **Mixed in Australia.** 2005 sample: small-company directors earn abnormal returns on buys and sells. Uylangco, Easton, Faff (2010): outsiders can copy, before costs. Berkman et al. (2016 working paper) and a 2023 paper: in small and mid firms only **sells** are informative; in large firms following pays about 4% a year. 13% of notices are lodged late | Weak for a long-only buyer of small shares | Free to read on the ASX site by hand; no automated access; no history with dead companies |
| Short interest | Strong internationally | Melbourne working paper: negative predictor in Australia [1]. Ours (R62): wrong sign on unseen data. ASIC data lags four days | Only as an avoid flag | ASIC files, free (held) |
| Share issuance / dilution | Holds in 41 countries [R61] | Ours: stand-alone confirmed (t −2.2 unseen) | Yes: it removes trades | ASIC shares on issue, free, 2010 on (held) |
| IPO / listing age | Australian IPOs lag for 1–3 years [R61] | Ours: −8.9 pts, t −1.5 | Yes | Prices (held) |
| June tax-loss rebound | — | Ours: 23 Junes +3.5%, t 2.1; newest three −0.3% | Edge about equals cost | Prices |
| Commodity-linked prediction | Practitioner claims only; one thesis | Ours (R60): nothing beyond own momentum at a monthly horizon. Daily lead untested | Unlikely: daily signal, retail costs | FRED, RBA, World Bank (monthly); daily metals need a source |
| Market or regime timing | — | Ours (R38, R39, R48): nothing beats static holding; a 2012 Australian paper finds most predictors fail out of sample [1] | No | — |
| Google Trends, social media, job ads, web traffic | Short-lived attention effects that reverse [memory] | No Australian evidence of a tradable edge found (R61) | No: daily horizon, or institutional data prices | Trends is free but re-scaled on each download, so history is not dated |
| Retail short-term trading in general | Barber, Lee, Liu, Odean (Taiwan): day traders in aggregate lose after fees in every one of 15 years; fewer than about 15% show any persistent skill | — | No | — |

### 2.5 How professional quantitative managers build portfolios

| Practice | Source | Tag |
|---|---|---|
| Integrate signals into one score per share; do not run separate books per signal | Fitzgibbons, Friedman, Pomorski, Serban (AQR), *Long-Only Style Investing: Don't Just Mix, Integrate* | [2+] |
| Treat implementation (rebalance design, cost-aware trading, risk control) as a source of return equal to signal choice | Israel, Jiang, Ross (AQR), *Craftsmanship Alpha* | [2+] |
| Buy/hold spread to cut turnover | Novy-Marx, Velikov; Blitz et al. | [2+] |
| Combine many weak signals because their trades cancel | DeMiguel et al. | [1] |
| Spread rebalancing across dates to remove timing luck | Hoffstein et al. | [memory]; our tranche test of this failed |
| Expect half the published effect | McLean–Pontiff; the spec's own VAL-26 rule | [2+] |

---

## 3. Part 3 — "Beat all other options on the market": the benchmarks

### 3.1 After-fee total returns to 30–31 October 2026, % a year, before the investor's own tax

Sources. **[issuer]**: Betashares fund pages saved 14 Nov 2026 (as at 30 Oct 2026) and Vanguard's own monthly total-return data to 31 Oct 2026, both in `actuals/data/`. **[EODHD]**: computed today from the licensed EODHD panel as ASX closing price plus distributions to 30 Oct 2026; these can differ from the issuer's NAV figure by up to about one point over one year for global funds (ASX close against overseas close) and carry the small distribution mismatches noted in briefing addendum 3. Franking credits are not included anywhere. Issuer pages for iShares, VanEck, the robo-advisers and the LICs could not be reached from this session; Betashares now blocks scripted access and I did not work around it.

| Option | Fee | 1 year | 3 years | 5 years | 10 years | Source |
|---|---|---|---|---|---|---|
| **A200** Betashares Australia 200 | 0.04% | 3.95 | 13.47 | 8.13 | index 9.58 (fund began May 2018) | [issuer] |
| **VAS** Vanguard Australian Shares | 0.07% | 3.05 | 13.15 | 7.65 | 9.31 | [issuer] |
| IOZ iShares Core S&P/ASX 200 | 0.05% [memory] | 3.57 | 13.30 | 7.98 | 9.40 | [EODHD] |
| **BGBL** Betashares Global Shares | 0.08% | 4.51 | 18.43 | index 12.06 | index 13.94 (fund began May 2023) | [issuer] |
| **VGS** Vanguard International Shares | 0.18% | 4.30 | 18.19 | 12.06 | 13.99 | [issuer] |
| IVV iShares S&P 500 | 0.04% [memory] | 5.10 | 19.96 | 13.72 | 16.07 | [EODHD] |
| **NDQ** Betashares Nasdaq 100 | 0.48% [memory] | 3.80 | 22.80 | 14.98 | 20.92 | [EODHD] |
| **MTUM** Betashares Australian Momentum (began Jul 2024) | 0.35% | −7.94 | — | — | — | [EODHD] |
| **AQLT** Betashares Australian Quality (began Apr 2022) | 0.35% [memory] | 9.10 | 21.41 | — | — | [EODHD] |
| AUMF iShares Australia Multifactor | 0.30% [memory] | 0.72 | 15.29 | 8.64 | 9.24 | [EODHD] |
| **QUAL** VanEck MSCI International Quality | 0.40% [memory] | 4.66 | 16.73 | 11.66 | 15.49 | [EODHD] |
| QLTY Betashares Global Quality Leaders | 0.35% [memory] | 3.09 | 15.48 | 9.26 | — | [EODHD] |
| VHY Vanguard Australian High Yield | 0.25% [memory] | 12.32 | 16.81 | 12.63 | 10.70 | [EODHD] |
| MVW VanEck Australian Equal Weight | 0.35% [memory] | 2.43 | 11.31 | 7.12 | 9.10 | [EODHD] |
| VSO Vanguard Australian Small Companies | 0.30% [memory] | −4.94 | 13.09 | 4.58 | 8.88 | [EODHD] |
| DHHF Betashares Diversified All Growth | 0.19% | 4.20 | 15.85 | 9.74 | — | [issuer] |
| VDHG Vanguard Diversified High Growth | 0.27% | 5.10 | 15.34 | 8.50 | — | [issuer] |
| **Owner's plan: 40% Australian / 60% global** (VAS and VGS monthly returns, constant weights; A200 and BGBL track the same indexes for less) | about 0.064% | 3.98 | 16.31 | 10.45 | **12.25** | [computed from issuer data] |
| LIC: AFI (share price, dividends reinvested) | about 0.15% | −1.76 | 6.03 | 0.93 | 6.30 | [EODHD] |
| LIC: Argo (ARG) | about 0.15% | 5.87 | 7.92 | 3.44 | 6.47 | [EODHD] |
| LIC: Australian United (AUI) | about 0.10% | 10.08 | 13.64 | 8.28 | 9.66 | [EODHD] |
| LIC: MFF Capital (global) | performance-linked | 13.18 | 29.39 | 16.97 | 15.36 | [EODHD] |
| Robo: Stockspot Topaz (high growth) | 0.4–0.66% plus ETF fees | 14.9 (to 31 Mar 2026); 14.7 (to 30 Jun 2026) | 13.9 (to Mar 2026) | 10.4 (to Mar 2026) | 10.6 (to Jun 2026) | Stockspot's own pages via search listing [1]; different dates from the rows above |
| Robo: Stockspot Emerald (growth) | as above | 13.2 | 12.9 | 9.5 | — | as above |
| Robo: Raiz Aggressive | A$4.50 a month or 0.275% | not obtained | not obtained | not obtained | not obtained | Issuer page unreachable |
| Robo: Spaceship Universe | 0.50% above A$100 | 33.75 (to 30 Jun 2025) | — | — | 15.14 since May 2018 (to Jun 2025) | Spaceship pages via search listing [1]; stale |
| **Active Australian share funds as a group** | typically 0.7–1.2% | 74% lagged the S&P/ASX 200 in 2025 | — | about 80% lagged | about 85–88% lagged over 10–15 years | SPIVA Australia year-end 2025 via news reports [2+] for 74% and 85%; the rest [1] |
| Active mid- and small-cap funds | — | 64% lagged | — | 60% lagged | — | SPIVA via a secondary site [1] |
| **Big Wins engine H82 on paper** (EODHD, 2018–13 Nov 2026, after costs) | data A$370 a year | — | — | — | 8.3 (A$25k) / 10.0 (A$100k) against 8.8 for the index fund | R68 |

One LIC (WAM Capital) showed −36.9% for one year in the EODHD file. That looks like a data defect and is not quoted.

### 3.2 What the table means

- **The hurdle is not the ASX 200.** The owner already holds a plan that returned about 12.3% a year over ten years. An ASX-only picker needs about +3 points a year over the local index, after costs and tax, to match it, and about +11 to match the Nasdaq fund. No Australian anomaly study, and nothing in 403 trials, supports +3 after costs.
- **Past ten-year winners are not forecasts.** The global and Nasdaq lead is one decade of US technology. R38 and R66 found that no allocation between 30/70 and 50/50 can be told apart on return. The table sets the comparison; it does not say which row will win next.
- **Ready-made factor funds are the direct rivals of any ASX stock rule.** MTUM (momentum) lost 7.9% in its last year while the index made 4%; AQLT (quality) is far ahead over three years. Both do, for 0.35% a year and no tax churn in the owner's hands beyond distributions, roughly what a home-built engine does.
- **Professionals mostly fail the same test.** Three in four active Australian funds lagged the index in 2025 and about 85% over 15 years.

### 3.3 What evidence would be needed to claim the engine beats these

1. **A margin after everything.** Total return after brokerage, spreads, data cost and the owner's tax (including franking on both sides), compared with each benchmark bought once and held, on the same dollars and dates.
2. **On data the design never saw.** After 14 November 2026 only. History can reject a design; it can no longer confirm one.
3. **Beyond luck.** The programme's bar: t ≥ 3.0 on the monthly difference and a deflated Sharpe ratio ≥ 0.95 with all 403+ trials counted; at or above the 90th percentile of 200 random portfolios run through the same machine.
4. **Long enough.** With a tracking error of about 9 points a year, a true 3-point edge reaches t = 2 in about 35 years and t = 3 in about 75. A 5-point edge reaches t = 2 in about 13 years. No paper record of 3–10 years can establish a 1–3 point edge.
5. **Against every row, not one.** Beating A200 while trailing the 40/60 plan is not "beating the market options".

**Plain statement.** No algorithm can be guaranteed to beat these. What can honestly be delivered is: a design with the best prior odds the evidence supports, a test that would reject it if it is bad, and a live scoreboard that shows the owner every month where it stands against each rival.

---

## 4. Part 4 — Design brief: the one algorithm

### 4.1 Shape

**One engine, one score per share, one book.** Each week every eligible share gets a single number: its expected 12-month standing among its peers, with the chance of a collapse counted against it. The book buys from the top of that list, keeps a holding until it has clearly fallen down the list, and trades only when the expected gain is at least twice the cost and tax of the trade. Holding periods are therefore set by the signal, not by the calendar: typically one to three years for shares that keep working, a few months for ones that break.

It sits beside the owner's index plan, on paper, until the conditions in spec §17.1 are met. That is not a hedge in the writing; it is the first design element, because the largest expected loss available here is moving real money to an unproven stock rule.

### 4.2 Objective (the change that matters most)

| Option | Verdict |
|---|---|
| Classify "+50% or more in 12 months" and buy the highest probabilities | **Reject.** Selects volatility and small size; median pick loses (section 1.4; Conrad–Kapadia–Xing) |
| Predict the average return | Workable but dominated by a few extreme, often erroneous, observations |
| **Primary: predict the share's rank among its peers by 12-month total return** (0 to 1 within each month) | **Adopt.** Robust to outliers and data errors; matches how H82 was built; standard in the literature |
| **Secondary (challenger): two heads, P(gain ≥ 50%) and P(loss ≥ 50%); score = P(gain) − 1.7 × P(loss)** | **Adopt as the one challenger.** It serves the owner's request directly. The 1.7 is arithmetic, not tuning: a 50% loss removes 1.7 times as much compounded wealth as a 50% gain adds (ln 0.5 ÷ ln 1.5 = −1.71) |

Report for every candidate, beside return: the share of its picks that gained 50% or more, and the share that lost 50% or more, each against the universe base rate. That is the honest "big wins" scorecard.

### 4.3 Inputs

Rule for admission: dated at the time, includes companies that later died, legally usable for model training, and backed by outside evidence. Anything failing the first two is collected forward and kept out of the trained model.

| # | Input family | Signals | Source | Dated and complete? | Licence | Role |
|---|---|---|---|---|---|---|
| 1 | Trend | 12-1 month return; 6-month return; price ÷ 52-week high | panel_v2 (to 2015), EODHD (2018 on) | Yes | panel_v2 unlicensed copy: research only. EODHD personal | Core (the H80 parts) |
| 2 | Risk | 252-day volatility (low is good); downside volatility | Same | Yes | Same | Core; main loss-avoider |
| 3 | Liquidity (new) | Amihud illiquidity over 252 days; 63-day ÷ 252-day traded value; share of zero-volume days | Same | Yes | Same | Candidate; must pass the development gate |
| 4 | Size and age | Rank by traded value; days since first trade | Same | Yes | Same | Conditioning feature for the challenger; printed flag |
| 5 | Short interest (new forms) | Level; 3-month change; short ÷ 20-day volume | ASIC daily files | Yes from Jun 2010; four-day lag | Unread; private use | Challenger feature and printed flag. Only 5½ development years |
| 6 | Dilution | 12-month change in shares on issue | ASIC "total product in issue" | Yes from Jun 2011 | Same | Printed flag and challenger feature. Not a veto (R62: vetoes did not help) |
| 7 | Commodity and currency exposure | Rolling betas to iron ore, gold, copper, coal, oil, lithium (when a series is found), AUD | drivers DB; FRED, RBA, World Bank | Yes if betas use prior data only | Public | **Risk caps only.** Not a return signal (R60) |
| 8 | Sector | Industry group | ASX listed-companies file, saved monthly from now | Forward only; history is today's file | Save by hand | Caps |
| 9 | Market state | Index 12-month return and drawdown | Index series | Yes | — | **Not used for timing** (R38, R39, R48). Recorded for attribution only |
| 10 | Dividends and franking | Cash per share; franking percentage where known | EODHD dividends | 2018 on | Personal | Accounting, not a signal |
| F1 | Results-day reaction | Return over the three days around the 4E/4D release | ASX site by hand, or headline archive | Forward only | ASX terms: no automated access | Shadow feature |
| F2 | Director trades | Net on-market buying by directors over 6 months | Appendix 3Y, read by hand | Forward only | Same | Shadow feature; low prior (Australian evidence mixed) |
| F3 | Analyst revisions | 3-month change in consensus earnings | A paid feed with ASX estimates, if one is confirmed | Forward only | Vendor terms | Shadow feature; highest prior of the forward items |
| F4 | Fundamentals as first reported | Gross profitability, accruals, asset growth, cash runway | EODHD fundamentals snapshots twice a year | Forward only | Personal | Archive; no test for 36 months |

**Kept out on purpose:** the survivors-only headline table and stockanalysis fundamentals (cannot be used to train: biased, and the latter's terms bar ML training); Google Trends, social media, job ads, web traffic (no usable evidence at this scale); intraday data.

### 4.4 How the signals are combined, and why

**Champion form: a plain average.** Rank each signal within the month, average within its family, then average the families that passed the gate, with equal weights. No fitted weights. Reasons: it is what the professional literature recommends (integrate into one score); equal weights cannot overfit 14 independent years; it is the form of the only rule that has held level on unseen data.

**Challenger form: one small machine-learning model, fixed in advance.**
- Gradient-boosted trees, depth 3, 300 trees, learning rate 0.03, 70% row sampling, at least 200 share-months per leaf, average of 10 seeds.
- Direction constraints from prior evidence: more momentum never lowers the score, more volatility never raises it, nearer the high never lowers it.
- About a dozen inputs (families 1–6). Missing values allowed (short interest and dilution before 2010).
- Trained on an expanding window, re-trained each December. Because labels look 12 months ahead, the last 12 months before each prediction date are left out of training.
- Hyper-parameters are those above. They are not searched. If the build agent wants a search, it must run inside the training window only and each setting counts as a trial.
- Two targets, as in 4.2: rank (M1) and the two-headed gain/loss model (M2).

**Adoption rule, set now.** A challenger or a new family replaces or joins the champion only if, on development predictions made out of sample (2006–2015), it (a) improves the eight-account robust score by at least 1.0 point a year, (b) has the same sign in both halves, and (c) beats 90% of placebo runs in which the new input is shuffled across shares within each month. Otherwise the champion stays as H82's score. Expected outcome, stated in advance: nothing passes.

### 4.5 Buy rules

1. **Universe.** Ordinary shares and stapled securities among the 300 most-traded by 63-day median traded value, price at least 20 cents, at least 40 trading days in the last 63, not suspended. Funds, LICs and duplicate or re-used codes removed (rules v1.3 A7).
2. **Signal.** Buy only from the top tenth of the list (rank 1–30 of 300), best first.
3. **Room.** A slot is free, or a swap passes the trade test in 4.6.
4. **Liquidity.** Position no larger than 5% of the share's 63-day median daily traded value.
5. **Caps hold after the purchase** (4.7).
6. **Flags are printed, not enforced:** dilution above 20% in 12 months, listed under two years, short interest in the top tenth, a results day within five trading days. The owner sees them; the engine does not act on them unless a later forward test earns them a place.

### 4.6 Sell rules

1. **Hold line.** Keep a share while it ranks in the top 30% (rank ≤ 90). Below that line at two weekly readings in a row, it becomes a sale candidate. This is the buy/hold spread that the cost literature finds most effective, and the "keep while rank ≤ 90" form that halved turnover at no cost in R64.
2. **Trade test.** Sell a candidate and buy its replacement only if the expected gain is at least twice the full cost: both brokerages, both half-spreads, and any tax brought forward. Expected gain = the rank gap between the two shares × the development return per unit of rank, halved. With today's cost model this lets through swaps of roughly three rank-deciles or more.
3. **No price stops, no trailing stops, no trend-break exits.** All were tested and lost (R53).
4. **Let winners run.** Never sell a share for having risen. Trim only if one position exceeds 15% of the book, back to 10%.
5. **Tax clock.** A candidate sitting on a gain and held for 10–12 months waits for the 12-month mark unless its rank is worse than 70%. Candidates sitting on a loss are sold without waiting, and in June before the 30th.
6. **Corporate events.** A share under an agreed cash takeover trading within 3% of the offer is sold and the money redeployed. A suspended share is carried at its last price with a second valuation at 70%. [Both are operating judgements, untested.]
7. **Whole-engine exit.** The kill rules in 4.10.

### 4.7 Sizing and risk

| Rule | Setting | Basis |
|---|---|---|
| Number of holdings | 30 at A$100,000; never fewer than 20 | R64: ten-share results are noise |
| Minimum account | A$50,000. Below that, hold the index | A$6.60 minimum brokerage is 0.26% a side on A$2,500 |
| Weights | Equal at purchase; no rebalancing back to equal | R64: inverse-volatility weights did not help; rebalancing sells winners |
| Industry cap | 25% per industry group | H82 rule |
| Resources cap | 30% in Materials plus Energy | R64 (rarely binds) |
| Commodity cap (new) | Book's summed exposure to any one commodity no more than twice the index's | R60: the map describes risk well. Untested as a cap |
| Single position | Trim above 15% | Judgement |
| Cash | Fully invested; cash only when fewer than 20 shares qualify | No market timing (R38) |
| Leverage, shorting, derivatives | None | Spec |

### 4.8 Cadence

| When | What |
|---|---|
| Every trading day | Update prices; check data quality, suspensions, takeover and delisting notices. No scoring, no trades |
| Every Friday close | Re-score; apply hold line and trade test; orders for Monday |
| Monthly (first trading day) | Scorecard against every benchmark in section 3; frozen, hash-chained snapshot |
| June | Loss harvesting before 30 June |
| Every 31 December | Re-train the challenger on the fixed recipe; annual review of families and kill rules |

Daily or weekly *trading* is not in the design, because the evidence is against it at this scale: monthly-turnover rules cost about 12 points a year at A$25,000 (R56); faster review lost on unseen data (R55); the published short-horizon strategies need 25-basis-point costs and analyst data; retail short-term traders lose in aggregate. Weekly *decisions* with a wide hold line give the owner what was asked for in substance: the engine looks every week and acts when the signal says so.

### 4.9 Costs and tax

- **Costs:** as rules v1.3: brokerage the larger of A$6.60 and 0.088%; half-spread 0.10% (100 most-traded), 0.25% (101–300), never less than half a tick; whole shares; idle cash earns nothing. Stress at 1.5×. Replace with recorded paper fills as they arrive.
- **Data cost** (A$370 a year) shown as a separate line: 0.37% of A$100,000.
- **Tax, three regimes, all reported:**
  - *Current law* to 30 June 2027: 32% marginal rate; 50% discount after 12 months.
  - *Announced law* from 1 July 2027: for holdings over 12 months, cost base indexed to inflation and tax on the real gain at the marginal rate, with a 30% floor; gains to 30 June 2027 keep the discount; under 12 months, full nominal gain. Implement the transition split. [2+ for the design; passage into law unverified.]
  - *Stress:* no discount, no indexation.
- **Franking:** credit the engine and every Australian benchmark with franking at the franking percentage where known, 75% assumed otherwise, and say which.
- **Parcels:** sell highest-cost parcels held over 12 months first.
- **The comparator pays tax too:** bought once, distributions taxed each year, sold at the end.

### 4.10 Learning without overfitting

1. **One frozen recipe.** Features, model settings, rules and thresholds are hashed before any return is computed. Re-training changes numbers inside the recipe, never the recipe.
2. **Walk-forward only.** Every prediction is made by a model that saw only earlier data, with the 12-month gap.
3. **Champion and challenger.** One champion trades the paper book. At most two challengers run in shadow. A challenger is promoted only at a December review, only on results after its own registration date, and only if it leads by the noise floor (1.0 point a year) and beats the random-portfolio 80th percentile.
4. **Decay monitor.** Each month, record each family's rank correlation with the next 12-month return as it matures. A family whose trailing 36-month average is negative with t below −2 is dropped at the next review. This is declared now so that dropping it later is not a tuned choice.
5. **Trial ledger.** Every specification ever run is counted (403 today). The bar rises with the count.
6. **Kill rules** (R68, kept): at a formal look, more than 15 points behind A200 in total after costs and tax; drawdown more than 20 points deeper than A200's; a random or plain-momentum control passes where the engine does not; two data failures in 12 months. Added: below the 10th percentile of its 200 random portfolios at 36 months.
7. **What it records** (R52): every score, every flag, every order, every cost, every outcome, and every forward-only feature beside the outcome it would have predicted. After 36 months those forward features get their first test, each with one pre-registered look.

### 4.11 The honest test plan

| Step | Data | Purpose | Counted trials |
|---|---|---|---|
| T0 | — | Hash the pre-registration: features, both objectives, model settings, rules 4.5–4.9, gates, budget | 0 |
| T1 | Dev 2001–2015 | Rebuild H82 v1.3 as the reference; confirm it reproduces R64 | 0 (replication) |
| T2 | Dev | Label cleaning: drop or winsorise outcomes that include a flagged data row; report how many | 0 |
| T3 | Dev | Stage A gates for new inputs: liquidity (3), short-interest change (1, 2010–2015 only), size interaction (1), miners against others using dated exposures (1) | 6 |
| T4 | Dev, out-of-sample predictions 2006–2015 | Champion (plain average, with any family that passed T3); challenger M1; challenger M2. Eight-account robust score; placebo with shuffled inputs; base-rate table of +50% and −50% picks | 3 |
| T5 | Dev | Trading form: weekly scoring with the 10% / 30% hold line and trade test, against yearly review; one alternative hold line (50%) | 2 |
| T6 | Dev | Choose **one** final engine by the adoption rule. If nothing passes, the final engine is H82's score in the new trading form, or H82 unchanged | 0 |
| T7 | 2016–May 2024 (panel_v2) and 2018–Nov 2026 (EODHD total return) | The single look, both sizes, pass rule as R64 §4. Labelled "re-used holdout". Benchmarks: A200, 40/60, and the factor funds from their start dates | 1 |
| T8 | — | Blind rebuild from the rule text by another agent | 0 |
| T9 | After 31 Dec 2026 | Forward paper record beside H82, same clock, formal looks at 36, 60, 120 months | — |

Budget: at most 11 development trials and 1 look. Library count after the work: at most 403 + 12 = 415.

**Power statement to print before T7.** With tracking error near 9 points and 9 to 11 years of holdout, a true edge of 3 points a year gives an expected t of about 1.0–1.1. The chance of passing "t ≥ 3 and deflated Sharpe ≥ 0.95" is under 5% even if the edge is real. T7 can therefore reject a bad design; it cannot confirm a good one. The forward record is the confirmation.

### 4.12 Additions ranked by expected value against cost and effort

| Rank | Element | Expected value | Cost / effort | New data or money |
|---|---|---|---|---|
| 1 | Keep real money in the 40/60 plan; engine on paper with a monthly scoreboard against all benchmarks | Avoids the one large loss available; ten-year gap to the ASX index is about 3 points a year | None | None |
| 2 | Change the objective from "+50% probability" to rank, with the gain-minus-1.7×loss challenger | Removes a design that would pick the worst group (median −23%) | Hours | None |
| 3 | Clean labels and data before any training | A quarter of loss labels are suspect; prevents learning errors | A day | None |
| 4 | Buy/hold line plus the twice-cost trade test, scored weekly | Best-evidenced cost saver; R64 saw turnover halve for no loss. Worth perhaps 0.3–0.8 points a year | A day | None |
| 5 | Plain-average champion with a fixed, constrained ML challenger and an adoption rule | Caps overfitting; small chance (I put it near 15%) the challenger adds a point | 1–2 days | None |
| 6 | Real tax rules (July 2027) and franking on both sides | Could move the comparison by 0.3–1 point either way; needed for any honest claim | A day | None |
| 7 | Robust evaluation: eight start-month accounts, 12-month training gap, shuffled-input placebos, random portfolios, full trial count | Stops false positives; no return of its own | Mostly built | None |
| 8 | Liquidity family, short-interest change, miners-versus-others interaction (the untested price-and-filing ideas) | Each perhaps a 10–15% chance of passing; the last free tests on held data | 1–2 days; 6 trials | None |
| 9 | Risk caps from the commodity exposure map; dated sector file monthly | Tail control; no expected return | Half a day, then minutes a month | None |
| 10 | Forward archive: results-day reactions, director trades, share counts, and (if bought) fundamentals and analyst estimates; learning loop with decay and kill rules | The only route to genuinely new information; pays off, if at all, after 3+ years | Hours a month by hand for ASX items | EODHD fundamentals about A$93 a month (two months a year ≈ A$186); an ASX-estimates feed: price and existence unconfirmed |
| 11 | Hand-read outcomes of shares that stopped trading after April 2020 | Removes a 2–3 point uncertainty in the 2018–2026 result | A few hours | None |
| 12 | Norgate rental (dev period in total return; dated index membership) | Settles whether the 2001–2015 lead survives dividends; cannot promote anything | A$381 once; Windows | Owner has said hold off |
| 13 | Verify the deflated-Sharpe code against the papers | Protects the main luck control | Hours; needs a reachable copy of the papers | None |

**Money already committed:** EODHD All World, about A$370 a year. **Optional:** A$186 a year for fundamentals snapshots; A$381 once for Norgate. Nothing else in this brief needs a purchase.

---

## 5. Instructions for the build agent (report 70)

1. **Do not train on a "+50% in 12 months" label alone.** Primary target: within-month rank of the 12-month forward return. One challenger: two heads, score = P(gain ≥ 50%) − 1.7 × P(loss ≥ 50%). Print the +50% and −50% hit rates of every candidate's picks beside the universe base rates (13.5% / 15.0% for ranks 101–300 in development).
2. **Clean the labels first.** Exclude or winsorise any 12-month outcome whose window contains a row flagged `split_residual`, `spike_residual` or `big_move_unexplained` in panel_v2; report the count (about 26% of loser labels, 5% of winner labels). Cap daily returns used in features.
3. **Use only inputs that are dated and include dead companies:** panel_v2 open/high/low/close/volume/value; ASIC short positions and shares on issue (2010 on, with a four-day lag); drivers exposures estimated on prior data only. **Do not train on** `niche/out/events.csv.gz` (survivors only) or anything from `company_db` or stockanalysis (survivors only; terms bar ML training). After May 2024 panel_v2 rows come from stockanalysis: do not use them in any model fit.
4. **Keep the model small and fixed:** about a dozen features in six families; gradient-boosted trees of depth 3, 300 trees, learning rate 0.03, minimum 200 rows a leaf, 10 seeds, direction constraints on momentum (+), 52-week high (+), volatility (−). No hyper-parameter search unless it is inside the training window and every setting is logged as a trial.
5. **Leave a 12-month gap** between the end of the training data and each prediction date (labels overlap). Expanding window, re-train each December. Report only out-of-sample development predictions (2006–2015).
6. **Benchmark every candidate against H82 v1.3's score in the same machine.** A candidate is adopted only if it leads by 1.0 point a year on the eight-account robust score (two sizes × four start months, after tax), has the same sign in both halves, and beats 90% of shuffled-input placebos.
7. **Trading form to build:** weekly scoring; buy from the top 10% (rank ≤ 30 of 300); hold while rank ≤ 90; sale candidate after two readings below the line; swap only if expected gain ≥ 2 × (two brokerages + two half-spreads + tax brought forward); no price stops; trim only above 15% of the book; 12-month tax clock as in 4.6. Test it once against the yearly review, and once with a 50% hold line. Do not test daily or weekly trading rules beyond this without declaring them as trials; R55 and R56 are the priors.
8. **Book:** 30 equal positions at A$100,000 (primary). Show A$25,000 only as a warning line. Industry group ≤ 25%, Materials + Energy ≤ 30%, position ≤ 5% of 63-day median daily value, price ≥ 20 cents.
9. **Costs and tax exactly as rules v1.3, plus:** the announced July 2027 regime (indexation after 12 months, 30% floor, transition split at 30 June 2027) as a third tax regime, and franking credits on both the engine and the Australian comparators (state the franking percentage assumed).
10. **Comparators in every results table:** A200/VAS total return (issuer data, `actuals/data/derived`), the owner's 40/60 plan on the same dollars, and from their start dates AQLT, MTUM and VHY (EODHD). Use the figures in section 3.1 as the cross-check.
11. **Treat 2016+ as a re-used holdout and say so.** One look only, for one final engine, on both unseen sets. Hash code and development results first. Print the power statement of section 4.11 above the results.
12. **Luck controls:** 200 random portfolios through the same machine; plain 12-1 momentum with 10 names as the negative control; deflated Sharpe with N = 403 plus your own trials; the one-point noise floor.
13. **Trial budget:** at most 11 development trials and 1 look; log each in a `trials_70.csv`. This report used 1 (D1), so start your count from 403.
14. **Untested inputs worth their six trials** (stage-A gate: t ≥ 2.0 and the same sign in both halves, beyond the H80 score): Amihud illiquidity; 63/252-day traded-value ratio; zero-volume-day share; 3-month change in short interest (2010–2015 only); momentum × size-rank interaction; miners against others using dated exposure betas.
15. **Do not re-test** anything in briefing §7.2 or R64 §6 (sell rules, stops, tranches, FIP, recency, MAX, beta, reversal, seasonality, driver-based selection, short-interest level, composite exclusion).
16. **Record, do not use,** the forward-only features (results-day reaction, director trades, analyst revisions, first-reported fundamentals). Give each a column in the snapshot schema so collection can start at the 31 December 2026 formation.
17. **Add to the forward snapshot now:** 12-month change in shares on issue per name (R68 item 5 is not yet in `bigwins_forward/code`), short-interest level and 3-month change, exposure betas, and the dated industry group.
18. **If nothing passes the adoption rule, say so and ship H82 v1.3** with the hold-line trading form only if T5 supports it. A null result is the expected result and is a valid deliverable.
19. **Write the rules so a blind validator can rebuild them** (R54, R63, R65 found 17 + 18 ambiguities; follow the v1.3 style), and state what would make you reject your own result.

---

## 6. What I could not verify, and reasons this could be wrong

- **No full academic text was read today.** SSRN, ScienceDirect, Wiley and several university hosts were blocked. Effect sizes in section 2 come from abstracts and secondary summaries. To read them, these hosts need to be allowed in the session's network settings: `papers.ssrn.com`, `www.sciencedirect.com`, `onlinelibrary.wiley.com`, `open.icm.edu.pl`, `finance-conference.wpcarey.asu.edu`.
- **Issuer pages not reached:** iShares, VanEck, Stockspot, Raiz, Spaceship, AFIC, Argo, S&P (SPIVA), BDO, ATO, Treasury. Their rows use the licensed EODHD price-plus-distribution series or search listings, and are tagged. Fees marked [memory] should be checked on the issuer page before anyone relies on them.
- **The CGT change:** design confirmed by several firms' summaries; whether it has passed Parliament is reported both ways. The engine must carry both regimes until this is checked against the Act.
- **The descriptive run (D1)** is price-only on the unlicensed panel, carries shares that stopped trading at their last price, and pools overlapping months, so the separation figures have no t-statistics. The direction is large and matches two published studies; the exact numbers are indicative.
- **The 1.7 loss weight, the 15% trim, the 20-cent floor, the takeover rule and the commodity cap** are judgements set in advance, not estimates.
- **My prior that the ML challenger will not beat the plain average** (about 85%) rests on six failed rounds here and on small-market evidence abroad; it is not a measurement.
- **No Australian machine-learning study was found.** One may exist behind a paywall.
- **The build agent's folder was empty** when read (16 Nov, 21:16 UTC): no pre-registration existed to review.

## 7. Files and sources

| What | Path |
|---|---|
| Descriptive run D1 and its output | `scratchpad/r72/code/desc_dev.py`, `scratchpad/r72/out/desc_dev.txt` |
| Trial log for this report | `scratchpad/r72/out/trials_72.csv` |
| Issuer data used for section 3 | `scratchpad/actuals/data/betashares/*_fundpage.html`, `scratchpad/actuals/data/derived/vanguard_monthly_total_return.csv` |
| EODHD panel used for section 3 | `scratchpad/data_foundation/out/eodhd/panel_tr.pkl` |

Web sources consulted (search listings and abstracts unless marked):
- Jensen, Kelly, Pedersen: https://nber.org/system/files/working_papers/w28432/w28432.pdf
- Hou, Xue, Zhang; Daniel, Moskowitz: read in full for report 64 (`deepdive/lit/`)
- Jacobs, Müller: https://www.wiwi.hu-berlin.de/en/Professorships/bwl/finance/seminars/papers-fin-acc-res-seminars/17s/jacobs.pdf
- Novy-Marx, Velikov: https://www.nber.org/papers/w20721
- DeMiguel et al.: https://www.london.edu/faculty-and-research/academic-research/a/a-transactioncost-perspective-on-the-multitude-of-firm-characteris
- Avramov, Cheng, Metzker: https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2022.4449
- Gu, Kelly, Xiu: https://www.nber.org/papers/w25398.pdf
- Leippold, Wang, Zhou: https://www.sfi.ch/en/publications/machine-learning-in-the-chinese-stock-market
- Cakici, Fieberg, Metko, Zaremba: https://ideas.repec.org/a/eee/dyncon/v155y2023ics0165188923001318.html
- Chen, Hanauer, Kalsbach (design choices): https://quantpedia.com/design-choices-in-ml-and-the-cross-section-of-stock-returns/
- Bessembinder et al.: https://rpc.cfainstitute.org/research/financial-analysts-journal/2023/long-term-shareholder-returns-evidence-from-64000-global-stocks
- Conrad, Kapadia, Xing: https://business.rice.edu/wisdom/peer-reviewed-research/why-do-retail-investors-hold-high-risk-stocks
- Yartseva: https://econpapers.repec.org/paper/akfcafewp/33.htm
- Blitz et al. (short-term signals): https://www.robeco.com/en-au/insights/2022/05/beyond-fama-french-alpha-from-short-term-signals
- Dou, Gallagher, Schneider: https://econpapers.repec.org/RePEc:sae:ausman:v:38:y:2013:i:2:p:353-373
- Bettman, Sault, von Reibnitz (52-week high, Australia): https://econpapers.repec.org/RePEc:sae:ausman:v:35:y:2010:i:3:p:227-244
- Australian momentum, matched-firm study: https://researchportalplus.anu.edu.au/en/publications/momentum-profits-in-the-australian-equity-market-a-matched-firm-a/
- Out-of-sample predictability in Australia (2012): https://ideas.repec.org/a/sae/ausman/v37y2012i3p461-479.html
- Director trading, Australia: https://ideas.repec.org/a/eme/arjpps/v23y2010i1p5-19.html ; https://research-repository.uwa.edu.au/en/publications/trading-by-insiders-in-australia-evidence-on-the-profitability-of/ ; https://doaj.org/article/31db1ad7063d42e2ac9f66e89bbbb192
- Analyst revisions, Australia (Hou, Hung, Gao): https://napier-repository.worktribe.com/output/178954/investors-reactions-to-analysts-forecast-revisions-and-information-uncertainty-evidence-of-stock-price-drift
- Earnings drift, Australia: https://opus.lib.uts.edu.au/handle/10453/19406
- Short interest, Australia: https://minerva-access.unimelb.edu.au/server/api/core/bitstreams/2acb73ae-2c88-5de3-83c2-a7a9c8cc2fed/content
- Day traders (Barber, Lee, Liu, Odean): https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf
- AQR, integrate and craftsmanship: https://www.aqr.com/Insights/Research/Journal-Article/Craftsmanship-Alpha-An-Application-to-Style-Investing
- SPIVA Australia year-end 2025: https://www.spglobal.com/spdji/en/spiva/article/spiva-australia-year-end-2025/ ; https://www.moneymanagement.com.au/news/funds-management/majority-aussie-equity-funds-underperforming-asx-200
- CGT change: https://www.pwc.com.au/tax/tax-alerts/2026-27-federal-budget-cgt-changes-is-30-june-2027-a-transaction-deadline.html ; https://www.bdo.com.au/en-au/insights/budget/2026/changes-to-the-capital-gains-tax-discount ; https://www.charteredaccountantsanz.com/news-and-analysis/news/federal-budget-2026-27-proposed-capital-gains-tax-changes
- Stockspot: https://blog.stockspot.com.au/stockspot-performance-update-june-2026/ ; https://www.stockspot.com.au/compare-investsmart-stockspot/
- Spaceship: https://www.spaceship.com.au/learn/2025-spaceship-voyager-annual-letter-exclusive-insights-from-our-vp-of-investments/
- EODHD coverage: https://eodhd.com/asx-data ; https://eodhd.com/financial-apis/insider-transactions-api
- Brokerage comparison: https://peakifi.com/investing/platforms/brokerage-fees-comparison/
