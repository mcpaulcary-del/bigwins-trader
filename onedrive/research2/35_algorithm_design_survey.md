# 35. Algorithm design survey and learning architecture: what "more" can honestly mean for this account

Date: 2026-11-13. Spec read: FD_FINAL.md v2.10 (§4, §9.1, §10, §15–17, §23–28). Prior reports read for their conclusions and not redone: 11–21, 31, 32, 33. Reports 33 and 34 own asset mix, tax and platform features; this report covers the algorithm and how the platform learns.

Tags: **[2+]** two or more independent sources agree; **[1]** one source; **[unverified]** no source reached, or model memory; **[computed]** my arithmetic or simulation from stated inputs; **[estimate]** my judgment, not evidence. "Primary" means I read the paper or page itself in this session; "abstract" and "extract" mean what they say. "R14" etc. is an earlier report in this folder.

---

## 0. Answer in brief

1. **A richer live rule does not buy more return here. A learning platform can buy robustness, lower costs and honest knowledge.** Of the design families surveyed, the only things that survive out-of-sample testing, costs and Australian tax at A$5,000–100,000 are the two the spec already uses: slow trend as a drawdown overlay, and diversification across asset classes. The rest is unproven out of sample (Keller-family, regime models, ML), failed after publication (winner-take-all dual momentum, Sell in May), close to zero after honest testing (macro and valuation timing), or too expensive to trade at this size (rotation, turn of month).
2. **"The platform must learn" is achievable, with one hard line.** The system can safely learn *how the world it trades in behaves*: volatility, correlations, its own costs and slippage, spreads, distribution patterns, tax position, data and broker reliability, and its own operational failures. It cannot safely learn *which rule will make more money* from its own short record: an edge loss worth 0.3 of Sharpe takes about 16 years to detect [computed, §4.5], and the best of 12 no-edge challengers leads by about 8 points a year by luck [computed, §4.3]. So estimates update automatically inside bounds; rules change only through pre-registered cards, a yearly promotion window and the owner's approval. Section 4 specifies this in full and §5 gives the requirement text (LRN-01 to LRN-34).
3. **One live-path signal upgrade has [2+] support: a wider trend ensemble** (card H30). It does not raise expected return. It removes specification luck, which is worth hundreds of basis points a year between a lucky and an unlucky single rule.
4. **A challenger library runs in `paper_sim` from day one**: 14 pre-registered algorithms covering every idea in the brief, on the same data, at three account sizes, at almost no cost. Shadow results can veto a candidate; they can never select one.
5. **Staging.** A$5k: L1 or STATIC live (as G2 and report 33 decide), library and learning layer on. About A$15–25k: P1 as already specified, cut to the number of sleeves the A$1,000 minimum order allows. About A$25k: graded wide ensemble if H30 passes. About A$60–100k: the §26 continuous-forecast engine becomes implementable. No rotation, regime, macro, seasonal or ML rule reaches the live path at any size unless it clears the Family B bar (t ≥ 3.0, DSR ≥ 0.95).

### 0.1 Ranked shortlist

| Rank | Design | Verdict | When | Card |
| --- | --- | --- | --- | --- |
| 1 | Learning architecture: bounded auto-estimates, drift monitors, execution learning, research cycle, quarterly "what the system learned" report (§4) | **Build** | Now, with M3–M6 | LRN-01 to LRN-34 |
| 2 | Challenger library with multiple-testing control (§4.3) | **Build** (no live effect) | Now, with M3 | H40, H41 |
| 3 | Wide trend ensemble: 13 signals, four signal types, equal weight by type | **Live candidate** (replaces L1's votes if it passes); shadow from day one | Binary form any size; graded form ≥ about A$25k | H30 |
| 4 | Contribution-only trend overlay ("never sell; steer new money") | **Live candidate for a growth-objective owner**; shadow from day one | Most useful below about A$25k, fades with size [computed] | H42 |
| 5 | P1: strategic risk budgets × per-asset trend score (already §26.4) | **Keep as specified**; live sleeve count limited by order size | Stage 2, ≥ about A$15–25k, owner risk choice (R33 §2.5) | H6, H13 (existing) |
| 6 | Defensive-asset choice when a sleeve is OFF (cash, or bonds while bonds trend up) | **Shadow; promotable** | With or after R33's HG1 | H34 |
| 7 | Continuous forecasts with buffers (§26 engine, Carver style) | **Live candidate later** | Two sleeves ≥ about A$25k; six sleeves ≥ about A$60k [computed] | H9 (existing), H30 grid |
| 8 | Downward-only volatility cap on top of trend | **Shadow; promotable as a risk control** | Shadow now | H35 |
| 9 | Managed-futures (trend) ETF as a 10% sleeve, to buy breadth instead of building it | **Shadow only until Stage 3**; US-listed only [unverified: no ASX fund found] | ≥ A$25k and every Stage 3 condition | H43 |
| 10 | Unlevered inverse-volatility / risk-parity static mix | **Shadow control** against P1's V0 | Shadow now | H33 |
| 11 | Relative-strength rotation, top 3 of 8 ASX asset-class ETFs, with absolute filter | **Shadow only**; a return claim, so Family B | Never live below A$50k; above it at most a 20% satellite, only if Family B passes | H32 |
| 12 | Two-state regime model (HMM or jump model) | **Shadow only, not promotable** | Shadow now | H36 |
| 13 | Macro / valuation composite, "sin a little" tilt | **Shadow only, not promotable** | Shadow now | H37 |
| 14 | ML summariser (regularised, walk-forward) | **Shadow only, not promotable** | After 12 clean library months | H39 |
| 15 | Dual momentum, winner-take-all (GEM, AU version) | **Reject live**; registered control | Shadow now | H31 |
| 16 | Keller DAA / VAA / BAA | **Reject live**; already control V4 in H13 | — | — |
| 17 | Sell in May; turn of month | **Reject live**; Sell in May runs as a placebo control | Shadow now | H38 |
| — | Online learning of rule parameters; re-weighting algorithms by recent results; leveraged risk parity; daily breakouts; CPPI floors; protective puts | **Reject** | — | — |

### 0.2 What was added after the owner's two instructions, and why

- **Depth.** I re-read primary texts where the session could reach them (list in §0.3) and replaced extract-level numbers with table values: AQR's valuation-timing tables, the jump-model paper's results table, Gu–Kelly–Xiu's timing numbers, Carver's signal-correlation matrix, EODHD's call-cost table, and CXO's summaries of the Dichtl–Drobetz, Keller, Quantopian and bank-strategy studies.
- **Designs added** (§2.7): (a) a contribution-only trend overlay, because for a small account with regular deposits it gives part of the trend filter's protection with no sale, no commission and no tax event; (b) defensive-asset choice, because what the money sits in while OFF is worth more than any signal refinement (R33 §2.3 found the same for cash); (c) a managed-futures ETF sleeve, because R14 found breadth, not signal design, drives trend returns and a two-sleeve account cannot build breadth; (d) CPPI floors and protective puts, assessed and rejected so the owner need not ask again.
- **Learning architecture made central** (§4, §5): library, auto-updating estimates, drift detection, execution learning, research cycles, quarterly report, safe ML, with requirement text and schedule slots.
- **One finding that applies to this report itself:** every card here was proposed by an AI model whose training data include 2024–2026 market history. For those cards the spec's 2024+ holdout is not blind (§4.7, LRN-23). Only data after each card's freeze date is clean.

### 0.3 Access record

- **Read in full or in the relevant sections (primary):** Asness, Ilmanen & Maloney (2017) from aqr.com; Shu, Yu & Mulvey (2024) from arXiv; Gu, Kelly & Xiu (NBER w25398); Ang & Timmermann (NBER w17182); Goyal & Welch (NBER w10483); Falck, Rej & Thesmar (arXiv 2105.01380); Hurst, Ooi & Pedersen, "Demystifying Managed Futures" (aqr.com); Carver's breakout post (qoppac.blogspot.com); EODHD's API-limits page; CXO Advisory's summaries of eight papers; the AlgoStrategyLab GEM repository page; arXiv abstracts 2309.17322, 2605.24564, 2602.14233, 2501.03938.
- **Abstract or extract only:** everything else. SSRN, ScienceDirect, Wiley, MPRA, Advisor Perspectives, Newfound, ReSolve, Allocate Smartly, Alpha Architect, Duke and LSE hosts refused connections or returned 403 to this session. Claims from them are tagged at extract level.
- **Not found at all:** any Australian study of Sell in May or turn of month on the ASX; any out-of-sample test of the RBA cycle, the AUD or iron ore as an Australian equity-timing signal; any audited live record for Keller-family strategies; any ASX-listed managed-futures ETF.

---

## 1. Claim table

| # | Claim | Tag | Sources |
| --- | --- | --- | --- |
| C1 | Trend lookbacks between about 2 and 12 months perform alike; blending them adds a little Sharpe and removes dependence on one choice. | [2+] | R14 findings 1, 3 |
| C2 | Signal types are near-substitutes. Carver's forecast-correlation matrix over 37 futures: a breakout rule and an EWMAC rule of matched speed correlate 0.93; adjacent EWMAC speeds 0.88; adjacent breakout windows 0.80; all breakouts vs all EWMACs 0.58 on average. His conclusion on adding breakout to EWMAC plus carry: "a small improvement in performance … though probably not a significant one"; on why bother: "As long as the correlation is less than 1.0 there will be some benefit." Levine & Pedersen show MA crossovers and time-series momentum are closely related filters. | [2+] (Carver primary; Levine & Pedersen extract) | S1, S2 |
| C3 | ReSolve tested 1,226 GEM specifications: the original rule's in-sample lead over its neighbours is "most likely due to random luck" and regressed to the median out of sample; an ensemble is recommended. Newfound reaches the same conclusion. | [2+] (extracts) | S3, S4; R15 #4 |
| C4 | Picking the best trend specification by its recent performance gives little benefit over naive diversification across specifications (1,023 trend strategies). | [1] practitioner, extract | S5 |
| C5 | Technical rules: even with false-discovery control an investor "would never have been able to select ex ante the future best-performing rules"; in-sample profit is offset by low transaction costs (DJIA 1897–2008). | [1] peer-reviewed, abstract | S6 |
| C6 | GEM since publication: an open backtest finds it beat the S&P 500 by 5.1 points a year in 1997–2013 and trailed by 5.4 points a year in 2014–2026, with a −33.8% drawdown in February–March 2020 and "no protection in fast crashes (2020, 2025)"; lookbacks of 9–15 months perform alike; walk-forward re-optimisation of the lookback did worse than a fixed one (8.7% vs 9.2% CAGR). A second test reports 8.4% CAGR, Sharpe 0.70, −20% drawdown since 2014 and "worse" results out of sample. A third says GEM trailed S&P 500 buy-and-hold over 2014–2022. The book's own figure: 17.43% a year, Sharpe 0.87, 1974–2013, gross. | [2+] on direction (three hobbyist-grade backtests; none audited); [1] each number | S7 (primary page), S8, S9; S10 (CXO primary for the book figure) |
| C7 | Faber's GTAA after publication: CAGR 6.05%, Sharpe 0.68, maximum drawdown 11.7% (2006–March 2025). Drawdown control persisted; return fell. | [1] | R15 #2 |
| C8 | Keller's VAA and DAA: the breadth threshold B and the number of holdings T are "set (via backtest)"; the canary universe was "selected experimentally"; data before ETF inception are simulated; the "out-of-sample" half follows in-sample optimisation of the same author's earlier designs. No audited live record found. Allocate Smartly, tracking 100+ such strategies live, says more than half would at some point have appeared on its underperformer watchlist. CXO's own tracked rotation strategy (SACEMS, tracked since 2010) has had its lookback and ETF list changed several times, most recently in September 2026. | [2+] that the evidence is pseudo out-of-sample (CXO primary ×2; R15 #6); [1] extract for Allocate Smartly | S11, S12, S13 |
| C9 | Unlevered risk parity has higher Sharpe and lower return than 60/40; levered versions lose to 60/40 after borrowing and trading costs. | [2+] | R15 #16 |
| C10 | Risk parity in 2022: the RPAR ETF fell more than 32% from its November 2021 peak (30.2% on closing data to 20 October 2022). Bridgewater All Weather lost roughly 22% in 2022. | [2+] for RPAR; [1] low-reliability secondary for All Weather | S14, S15 |
| C11 | Regime models: allocations differ across regimes, but the filtered (real-time) regime probability tracks the true regime with difficulty; a small misclassification of the future regime "can eliminate any advantage from knowing the correct model". | [2+] (Ang & Timmermann primary; Dacco & Satchell abstract) | S16, S17 |
| C12 | Markov-switching allocation on daily US, Japanese and German indices over about 40 years: profitable out of sample after costs; volatility down 41% on average; annualised excess return 18.5 to 201.6 basis points. | [1] peer-reviewed, abstract | S18 |
| C13 | Jump-model paper, results table (1990–2023, daily data, 10 bp one-way cost, one-day delay), S&P 500: buy-and-hold 10.2% a year, Sharpe 0.48, maximum drawdown −55.2%; HMM 0/1 strategy 8.5%, 0.54, −28.9%, turnover 141% a year; jump-model 0/1 strategy 11.2%, 0.68, −26.6%, turnover 44%. Similar ordering for DAX and Nikkei. An unsmoothed HMM changes state 8.5 times a year. The jump penalty is re-chosen each month to maximise Sharpe over the previous 8 years. The authors note the signal "requires several days of negative returns to confirm a regime shift". arXiv preprint by the method's authors; no tax; no independent replication found. | [1] primary | S19 |
| C14 | Goyal & Welch: "not a single one would have helped a real-world investor outpredicting the then-prevailing historical equity premium mean"; they add that out-of-sample tests on much-mined data are not truly out of sample. Goyal, Welch & Zafirov (2024): of 29 newer variables plus the original 17, more than a third fail even in-sample; half the rest fail out of sample; "a small number" still perform. | [2+] (2008 primary; 2024 abstract) | S20, S21; R31 C33 |
| C15 | Combination forecasts give positive out-of-sample R² where single predictors fail (US). In Australia "most of the empirically well-known predictive variables fail to generate out-of-sample predictability", but a combination forecast predicts one-year-ahead excess returns; a sector-rotation strategy on it outperformed by 3.27% a year risk-adjusted. Equal-weight averages often beat estimated "optimal" combination weights (the forecast combination puzzle), because weight estimation error dominates. | [1] each for the two return studies (abstracts); [2+] for the puzzle | S22, S23, S24 |
| C16 | CAPE timing, AQR's own tables, US 1900–2015, position scaled 50–150%, gross: buy-and-hold Sharpe 0.38, value timing 0.37; 1958–2015: 0.37 vs 0.37 with lower return (5.4% vs 5.5% excess) and a maximum relative drawdown of −32%. "Even before costs, the timing strategy cannot beat the Sharpe ratio of buy-and-hold." Momentum timing: 0.48 and 0.43; value plus momentum: 0.43 and 0.41 with maximum relative drawdown −17%. The paper's advice is to "sin a little". | [1] primary; [2+] with R31 C36 on direction | S25 |
| C17 | Inverted yield curves: Fama & French find "no evidence" that they predict stocks underperforming bills over 1–5 years (11 markets, 1975–2018); switching to cash underperformed buy-and-hold in all 24 US and World tests. | [2+] (extracts of the paper and two commentaries) | S26 |
| C18 | Commodity-currency exchange rates (AUD among them) forecast commodity prices; the reverse does not survive out of sample. Nothing found says the AUD, iron ore or the RBA cycle forecasts Australian equity returns. | [1] abstract; [unverified] for any equity-timing use | S27 |
| C19 | Sell in May. For: Bouman & Jacobsen, 36 of 37 countries; Zhang & Jacobsen, about 4 points across 100+ markets. Against: Dichtl & Drobetz, five indices to 2012 with 0.5% switching cost: significant over full samples, but "since January 2003, buy-and-hold significantly outperforms the Halloween strategy for all five indexes"; Sullivan, Timmermann & White: across about 9,500 calendar rules on 100 years of data none stays significant once the search is accounted for. | Contested; the post-publication test is [1] (CXO primary summary) | S28, S29, S30 |
| C20 | Turn of month: reported in 34 of 38 country indexes and in 8 of 9 international ETFs. Allocate Smartly's live record since late 2016: month-end trading of TAA strategies beat other days by more than 0.96% a year, but slightly underperformed if Q1 2020 is excluded. | [1] extract each | S31, S13 |
| C21 | Gu, Kelly & Xiu: almost 30,000 US stocks, 1957–2016. Out-of-sample monthly R² at stock level 0.16% for the benchmark regression, 0.26–0.40% for the best methods. Timing the S&P 500 with neural-network forecasts: Sharpe 0.77 vs 0.51 for buy-and-hold; "regularized linear methods fail to outperform naive constant forecasts of the S&P 500". | [1] primary | S32 |
| C22 | Avramov, Cheng & Metzker: ML stock-selection profits fall sharply once microcaps, distressed firms and high-volatility periods are excluded, and fall further after trading costs. | [2+] (abstract plus university summaries) | S33 |
| C23 | Nagel (NBER w34104, 2025): the "virtue of complexity" timing model, trained on 12 months with thousands of features, reduces to "a recency-weighted average" of training returns, "essentially a momentum strategy", volatility-timed; fed artificial data with reversals it builds the same strategy and fails. He calls the virtue "an illusion". | [1] abstract | S34 |
| C24 | Quantopian, 888 algorithms: backtest Sharpe offers "little value in predicting out of sample performance (R² < 0.025)"; "the more backtests a user ran, the bigger the difference between IS and OOS performance". A machine-learning model on backtest features predicted out-of-sample Sharpe better (R² 0.17). Out-of-sample window: June 2015–February 2016 only. | [2+] (abstract via Quantpedia primary page; CXO primary summary) | S35 |
| C25 | 215 bank "alternative beta" strategies: median Sharpe 1.20 in backtest, 0.31 live; median deterioration 73%, at least 50% in every asset class; "the industry practice of derating backtested Sharpe ratios by 50% is not conservative enough". Published anomalies: Sharpe falls 43% (Falck et al.) to 58% (McLean & Pontiff) after publication. | [2+] | S36, S37 |
| C26 | Harvey & Liu: the multiple-testing haircut is nonlinear; below a gross Sharpe of about 0.4 it exceeds 50%, above 1.0 it is at most 25%. | [1] (CXO primary summary) | S38 |
| C27 | Protocols: Arnott, Harvey & Markowitz (hypothesis first, log everything, expect most tests to fail); Bailey et al. (PBO by CSCV; Deflated Sharpe; minimum track record length); López de Prado (research-through-backtesting is the main failure mode). | [2+] (abstracts) | S39, S40 |
| C28 | DeMiguel, Garlappi & Uppal: of 14 optimising models on seven datasets "none is consistently better than the 1/N rule"; for 25 assets the estimation window needed for mean-variance to beat 1/N is about 3,000 months. | [2+] (abstract plus NBER draft extract) | S41 |
| C29 | CUSUM monitoring of managers (Philips, Yashchin & Stein, JPM 2003): detects a fall from information ratio 0.5 to 0 in about 40 months; a common setting gives one false alarm per 84 months. | [1] (IBM abstract and package documentation, extract) | S42 |
| C30 | Costs estimated from a trader's own executions differ greatly from literature models: Frazzini, Israel & Moskowitz, US$1.7 trillion of live trades, find costs "an order of magnitude smaller than previous studies suggest"; a model calibrated to realised costs predicts better out of sample. The authors caution it is one investor's experience. | [2+] (abstract plus two secondary accounts) | S43 |
| C31 | LLMs carry look-ahead bias into backtests: a model trained after the test period "may already encode how stocks moved"; removing memorised outcomes cut in-sample returns by up to 67%; of 164 finance-LLM papers, no bias type is discussed in more than 28%. | [2+] (three arXiv abstracts, primary) | S44 |
| C32 | Managed-futures fund returns are explained by simple time-series momentum: controlling for it "drives the alphas of most managers to zero". About 17 US-listed managed-futures ETFs exist; none found on the ASX. | [1] primary for the first; [1] extract and [unverified] for the second | S45, S46 |
| C33 | CPPI with a multiplier above 1 is path-dependent, can be "cash-locked" even when the market ends higher, and tends to be dominated by simple strategies; portfolio insurance gives downside protection with lower excess return. | [1] extracts | S47 |
| C34 | EODHD, vendor's limits page: end-of-day, splits and dividends requests cost 1 call each; several symbols in one request multiply the cost; bulk whole-exchange 100; fundamentals 10; free plan 20 calls a day, reset at midnight GMT; a refused request (HTTP 402) consumes nothing; the usage endpoint `/api/user` costs 0. | [1] primary; [2+] with spec VF1 for the daily limit | S48 |
| C35 | ASX ETF fees: VAS 0.07%, VGS 0.18%, IVV 0.04%, VGE 0.48%, VSO 0.30%, PMGOLD 0.15%, AAA 0.18%, BILL 0.07%. VAF is quoted at both 0.10% and 0.20%. | [1] each (aggregators; R31, R33 primary for some) | S49 |

---

## 2. Design survey

For each family: what it is, what the evidence says, what it would do to this account, how it fails. Expected effects are relative to static 40/60 (B2), net of the spec's cost model (RND-021: max(A$6.60, 0.088%) commission, 5 bp half-spread), and are **[estimate]** unless tagged. Published edges are halved first (VAL-26); C25 says even that may be generous.

### 2.1 Multi-signal trend ensembles

**Design.** Replace three votes with many signals of several types, each mapped to 0–1, averaged with equal weight by type: (a) time-series momentum over 3, 6, 9, 12 months; (b) price against its 6-, 8-, 10-, 12-month simple average; (c) exponential crossovers at 1/4, 2/8, 3/12 months (close to Carver's 16/64, 32/128, 64/256 days); (d) breakout: position of price in its 6- and 12-month range. A continuous forecast (§26, SIZ-03/04) is the same average used as a position size instead of being cut into ON and OFF.

**Evidence.**
- Lookback choice within 2–12 months barely matters, and blending gives a modest gain [2+, C1].
- Signal types of matched speed correlate about 0.9 [C2]. Adding types adds little information; it protects against the luck of one specification.
- That luck is large: ReSolve's 1,226 variants and Newfound [2+, C3]. In the open GEM backtest, lookbacks of 9–15 months performed alike and re-optimising the lookback walk-forward did *worse* than fixing it [1, C6].
- Selecting the "best" specification dynamically does not work [C4, C5]. Equal weights beat estimated weights in forecast combination generally [2+, C15]. So: equal weights, never fitted (R14 R2 stands).
- Continuous against binary: Carver's argument is that forecast strength relates roughly linearly to subsequent risk-adjusted return and that scaled positions trade less. I found his statements, not an independent quantified comparison [1, extract]. H9 already tests graded against binary.

**Effect on this account.**

| | A$5k | A$25k | A$100k |
| --- | --- | --- | --- |
| Return vs L1 | 0 (both about −0.5 to −1.5 points vs B2, R33 §2.2) | 0 | 0 |
| Drawdown vs L1 | Same on average; narrower spread of outcomes across start dates and specifications | Same | Same |
| Turnover | Binary with hysteresis: about L1's (one round trip per sleeve a year or fewer) | Graded: more, smaller trades; one step of a 40% sleeve is A$3,333 [computed] | Continuous with 10% buffer: A$4,000 steps on a 40% sleeve [computed] |
| Tax | As L1 | Graded exits realise part of a parcel at a time, which suits R33's `min_tax` logic | Same |

**Implementability.** Binary: any size, no new data. Graded thirds: clean from about A$25,000 once tranches and bands are counted [computed]. Continuous with a 10% buffer: two sleeves from about A$25,000; a six-sleeve P1 with 16% average weights from about A$62,500 [computed: 1,000 ÷ (0.16 × 0.10)].

**Failure modes.** Believing more signals means more edge; fitting the weights; all 13 signals failing together in a V-shaped fall, because they are one bet.

**Verdict.** The one signal design with [2+] support for the live path. Card H30, decided on dispersion like H3, with no return claim.

### 2.2 Multi-asset allocation engines

**(a) Dual momentum (GEM).** In-sample 17.4% a year (gross, the author's book). Since publication it has trailed the S&P 500 by several points a year and gave no protection in 2020 [2+ direction, C6]. The absolute-momentum leg did the useful work; the relative leg is a single-lookback, winner-take-all choice between correlated equity sleeves, the most fragile construction in this literature [2+, C3]. R15 D1 rejected it; post-publication data confirm that.
- Australian version (VAS / VGS / bond or cash): each VAS↔VGS switch sells 100% of the book: at A$5,000, A$13.20 commission plus about A$5 spread, 0.36% of NAV [computed], and every gain is short-term.
- Verdict: **reject live; registered control H31.**

**(b) Relative-strength rotation among ASX asset-class ETFs.** Universe of eight: VAS, VGS, IVV, VGE, VSO, VAF, PMGOLD, and AAA or BILL. Hold the top three by blended 3/6/12-month return, each only if its own trend is up.
- Evidence: cross-asset momentum exists in long-short academic portfolios (R15 #15, in-sample, gross). Ranking without an absolute filter gave no drawdown protection (R14 R4). After publication GTAA kept its drawdown control and lost about half its return [1, C7]. The nearest carefully tracked rotation strategy has needed repeated changes to lookback and universe [1, C8], which is what a weak, unstable edge looks like. No Australian-ETF study exists [unverified].
- Order-size arithmetic [computed]:

| NAV | Top-3 position | One switch (sell + buy) | % of NAV | At 6 switches a year |
| --- | --- | --- | --- | --- |
| A$5,000 | A$1,667 | A$13.20 + A$1.67 | 0.30% | 1.8% |
| A$25,000 | A$8,333 | A$14.67 + A$8.33 | 0.092% | 0.55% |
| A$100,000 | A$33,333 | A$58.67 + A$33.33 | 0.092% | 0.55% |

  Six switches a year is an assumption [estimate]; the card measures it.
- Tax [computed, illustrative: pre-July-2027 rules, 32% marginal rate, 7% a year growth, 20 years]: holding and paying discounted tax once at the end compounds at 6.33% after tax; realising every gain each year compounds at 4.76%. The gap is about 1.6 points a year, and rotation sits near the second case. The 1 July 2027 regime changes the size of the gap (R18; H11 runs both), not its sign for short holdings.
- Net expectation: gross edge after haircut 0 to +1 point; costs −0.55 to −1.8; tax −1 to −1.5. **Negative at every account size for a taxable investor** [estimate from the computed rows].
- Verdict: **shadow only (H32)**, Family B.

**(c) Risk parity, inverse volatility, All Weather.** Without leverage this is a low-equity portfolio: higher Sharpe, lower return [2+, C9]. It did not protect in 2022 [2+, C10]. P1 already uses class risk budgets and inverse volatility within a class, the sensible unlevered form. Expected effect vs B2: about −1.0 to −1.4 points a year (R33 §2.5 [unverified estimate]) for roughly half the volatility. **Shadow control H33**; no leverage (R14 R8).

**(d) Keller DAA / VAA / BAA.** Fast "13612W" momentum (the average of annualised 1-, 3-, 6-, 12-month returns, which over-weights the last month), canary assets, full switches to "cash". Thresholds and universes were chosen by backtest [2+, C8]. They are the opposite of what suits this account: monthly full-book switches, fast signals (R14 R1), every gain short-term. The spec already carries V4 as a non-promotable control in H13. **No new card. Reject live.**

**Sleeve count under the A$1,000 minimum** [computed]: a sleeve needs a base position of about A$2,500 for a ±20% band move or a one-third step to reach the minimum. Live sleeves should not exceed NAV ÷ 2,500: two at A$5,000, six at A$15,000, eight at A$20,000, ten at A$25,000. P1's "12–20 ETFs" is a paper universe; live P1 at Stage 2 entry should be four to six sleeves. Spec text in §5.4 (SIZ-09).

### 2.3 Regime detection

**Evidence.**
- In real time the regime is recognised late, and small misclassification removes the advantage [2+, C11].
- The peer-reviewed test found a large volatility cut and a small return gain [1, C12]. The newest paper's own table shows a plain HMM *lowering* return (8.5% vs 10.2% on the S&P 500) while halving drawdown, at 141% turnover; the jump model does better with a penalty re-tuned monthly on trailing Sharpe [1 primary, C13]. Under VAL-26 that tuning makes it in-sample evidence.
- All of that is daily data and daily switching, before tax. This system's development data are 408 monthly observations with perhaps five or six bear regimes: about six parameters fitted to about six events [computed from the spec's dates; the event count is an estimate].
- The jump model's features are downside deviation and Sortino ratios over rolling windows with a persistence penalty [1 primary]. That is a smoothed trend-plus-volatility signal. L1 is the three-parameter version of the same idea.

**Trend plus volatility.** The evidence for volatility scaling is tail control, not return (R14 finding 8; R15 #13 [2+]). The spec's forms are the downward-only cap (SIZ-11) and control V2. A cap on L1 itself is worth one card (H35) because it is fully specified without fitting.

**Effect.** Same sign as L1: lower drawdown in slow bears, return 0 to −1 point, plus model risk. **Failure modes:** label switching between refits; states that change when history is extended (a truncation-invariance failure under SYS-16); penalty or state-count tuning; late recognition in fast crashes.

**Verdict.** **Shadow only, not promotable (H36).**

### 2.4 Macro and valuation signals

- The comprehensive tests are negative, re-confirmed in 2024 [2+, C14].
- CAPE: AQR's own tables show no Sharpe gain over 116 years before costs, and a 32-point maximum shortfall against buy-and-hold along the way [1 primary, C16]. The part that helped in their test was momentum, which this system already has.
- Yield curve: no equity-timing value in 11 markets [2+, C17]. Credit spreads: no isolated out-of-sample equity-timing test found [unverified].
- Combination forecasts do better than single predictors, including in the one Australian study [1 each, C15]; its economic gain came from sector rotation, which this account cannot run cheaply.
- Australian-specific (RBA cycle, AUD, iron ore): no supporting evidence found [C18, unverified].

**Effect.** Return 0 ± noise. A ±10% tilt implies trades of A$500 at A$5,000: below the minimum, so nothing would trade. **Data:** RBA statistical tables, FRED, index-provider valuation; none on the EODHD budget; values must be stored with their publication dates because revised macro series leak the future.

**Verdict.** **Shadow only, not promotable (H37).**

### 2.5 Seasonality and calendar effects

- Sell in May worked in long samples and stopped after it was published: buy-and-hold beat it significantly in all five indices tested from 2003 with realistic switching costs [1, C19]. That is the McLean–Pontiff pattern (C25). No ASX test found [unverified].
- Cost here [computed from R32 §4.1 and RND-021]: one full round trip of both sleeves is about 0.64% of a A$5,000 account and about 0.28% of a A$100,000 account. Sell in May is one a year, plus six months at IBKR's 0% on small cash balances (R33 §2.3), plus every gain realised inside 12 months. Turn of month is twelve a year: about 7.7% at A$5,000 and 3.3% at A$100,000.
- One practical point: L1 trades the day after month-end, inside the turn-of-month window. The only live record found says month-end trading has not reliably beaten other days once Q1 2020 is removed [1, C20]. That supports H5's tranching by offset and gives no reason to prefer a day.

**Verdict.** **Reject live. H38 runs Sell in May as a calendar placebo**: if the harness shows it working by a wide margin in both sample halves, suspect the harness.

### 2.6 Machine learning

- ML finds structure in the cross-section of almost 30,000 US stocks, at a monthly R² of 0.4% or less [1 primary, C21]. Much of the profit sits in stocks that are hard to trade and goes after costs [2+, C22]. The headline market-timing extension has been shown to be a disguised momentum rule [1, C23].
- Backtested strategies deteriorate badly when they go live, and complexity makes it worse [2+, C24, C25]. Optimised weights lose to equal weights on realistic sample sizes [2+, C28].
- This system has 2 to 8 assets × 408 months and about six independent bear markets. ML's advantage is breadth; this problem has none. I found no credible out-of-sample ML result for a small ETF allocation set [unverified].

Safe uses are in §4.9. **Verdict: shadow only, not promotable (H39), deferred 12 months.**

### 2.7 Designs added in this pass

**(a) Contribution-only trend overlay (new; my design, no direct literature).** Never sell. When a sleeve's trend state is OFF, hold what is owned, and send new contributions and distributions to the cash leg; when it turns ON, deploy the accumulated cash.
- Why it matters for this owner: R33's rank-2 finding is that L1 serves drawdown control while the owner wants growth, and that STATIC is the evidence-based default for growth. This rule sits between them. It creates no sale, so no commission beyond the buys that would happen anyway, no CGT event and no reset of the 12-month clock.
- How much protection it gives [computed]: the share of the portfolio kept out of the market during an OFF spell is (months OFF × monthly contribution) ÷ NAV. At A$500 a month and a 10-month OFF spell, A$5,000 is held back: equal to the whole of a A$5,000 account at the start of the spell (half of the balance at its end), 20% of a A$25,000 account, 5% of a A$100,000 account. It is a trend filter that is strong when the account is small and fades as it grows. That matches where this account is.
- Evidence: none directly [unverified]. Lump-sum investing beats drip-feeding about two-thirds of the time (R33 §2.10 [1]), which argues *against* holding contributions back on average; the trend literature argues that the held-back months are worse than average ones. The card (H42) settles it on this account's assumptions.
- Failure modes: cash drag at IBKR's 0% unless HG1's cash ETF is adopted; re-entry at higher prices after a V-shaped fall; no help to capital already invested.

**(b) Defensive-asset choice (new card H34).** What the OFF money holds matters more than the signal. R33 §2.3 priced cash at 0% against a cash ETF at about 4.2%: about 1 point a year on the whole account while OFF. Dual-momentum and Keller designs switch to bonds; bonds added return in 2000–02 and 2008 and lost in 2022 [C10]. The simple, non-fitted form: hold AAA when OFF, or VAF if VAF's own 12-month return beats cash. One more instrument, one more order pair per transition.

**(c) Managed-futures ETF sleeve (new card H43).** R14's main finding is that breadth, not signal design, drives trend returns: one or two instruments give Sharpe 0.3–0.4, 50+ markets give far more. A two-sleeve account cannot build breadth; it can buy it. Managed-futures funds are, in substance, diversified time-series momentum [1 primary, C32].
- Obstacles: no ASX-listed fund found [unverified]; the US-listed ones (about 17) need Stage 3: A$25,000, the US venue, W-8BEN, Division 775 records, the US-situs cap. R14 planned on 0.3–0.7 net Sharpe and 20–25% drawdowns for trend programmes, and these funds lost in the 2024–25 whipsaw (R14, R32). ETF track records are short.
- Verdict: **shadow only now; a Stage 3 candidate** as a 10% sleeve. It is the only design here that adds a return source uncorrelated with equities, and it is also the hardest to hold through its own drawdowns.

**(d) CPPI / floor rules.** Sell as the portfolio approaches a floor, buy as it rises. Path-dependent, prone to cash-lock, generally dominated [1, C33]. R32's H14 already registers the nearest testable form (a 15% drawdown brake) in shadow. **Reject; no new card.**

**(e) Protective puts.** Outside a long-only ETF cash account. The published evidence I know says systematic put buying costs more than it protects over horizons longer than the option's life [unverified: AQR's page for the paper returned no text in this session]. **Reject.**

### 2.8 Summary: evidence quality and expected effect

Effects are vs static 40/60, net of costs, before tax, **[estimate]**. "DD" is maximum drawdown in a slow bear market; none of these helps in a fast crash (R32).

| Design | Evidence quality | Return, A$5k / 25k / 100k (points a year) | DD effect | Extra tax drag | Complexity | New data |
| --- | --- | --- | --- | --- | --- | --- |
| L1 three votes (today) | [2+] for drawdown; [2+] against a return claim | −1.4 / −0.8 / −0.6 (R33, R11 model) | About one-third to one-half lower | Low to moderate | Low | None |
| Wide ensemble (H30) | [2+] for robustness | Same as L1 | Same mean, narrower spread | Same | Low | None |
| Contribution-only overlay (H42) | Rationale only | −0.3 to 0 / −0.1 to 0 / about 0 | Lower by up to about half at A$5k; negligible at A$100k [computed share of NAV held back] | None | Low | None |
| Defensive asset: cash ETF or trending bonds (H34) | [1]; R33 computed the cash part | +0.7 / +1.0 / +1.0 vs L1 as specified, from the cash yield alone (R33) | Unchanged; worse in a 2022-type year if in bonds | Interest taxed at marginal rate | Low | 1–2 symbols |
| Continuous forecast | [1] | Same as L1; lower tracking error to B2 | Similar | Lower per trade | Medium (§26 engine) | None |
| Volatility cap on L1 (H35) | [2+] tail control; [2+] no return | −0.2 to 0 | Slightly lower | Low | Low | Daily closes (already fetched) |
| P1 (existing) | [2+] diversification; [1] post-publication drawdown control | −1.0 to −1.4 from the asset mix, plus the overlay | Lower, including 2008-type; not 2022 | Moderate | Medium | 4–10 symbols |
| Managed-futures sleeve 10% (H43) | [2+] long-run trend; short ETF record | −0.3 to +0.3 after fees, FX and tax records | Lower in slow bears; adds its own 20–25% sleeve drawdowns | US income, Division 775 | High (Stage 3) | 1–2 US symbols |
| Risk parity, unlevered (H33) | [2+] | −1.5 to −3 | Lower in equity bears; not 2022 | Low | Low | Bond, gold |
| Rotation top 3 of 8 (H32) | [1] in-sample; weak after publication | −1.8 to −0.8 / −0.5 to +0.5 / −0.5 to +0.5 | Lower only through the absolute filter | High: −1 to −1.5 | Medium | 6 symbols |
| Dual momentum (H31) | [2+] that it failed after publication | −1 to −3 at any size | Lower in slow bears only | High | Low | 1 symbol |
| Keller family | Pseudo out-of-sample | Unknown; assume negative after tax | Claimed low; unproven | Very high | High | 12+ symbols |
| HMM / jump model (H36) | [1]; authors' preprints | 0 to −1 | Like L1 | Like L1 or worse | High (model risk) | None |
| Macro composite (H37) | [2+] negative | 0 ± noise | None reliable | Low | Medium | RBA, FRED |
| Sell in May (H38) | Failed after publication [1] | −0.6 to +0.5 at A$5k incl. costs | None reliable | High | Low | None |
| ML summariser (H39) | [2+] negative for this data size | 0 ± noise | Unknown | Unknown | Very high | None |

---

## 3. What the survey changes in the existing design

1. **L1's three votes are a small ensemble; a wider one is better supported than a different rule** (H30 follows H3).
2. **P1 is the right multi-asset design and should not be replaced** by rotation, dual momentum or a Keller model. Its properties (no winner-take-all, no redistribution to winners, per-asset trend) are what the post-publication record favours [C6, C7, C8].
3. **For this owner the most useful new rule is the one that never sells** (H42), because it attacks the tax and cost drag that make every other overlay expensive at A$5,000.
4. **§23–28 has a research process but no learning process.** RND-032 allows "a challenger"; MON-07 has one CUSUM; SIZ-12 has a whitelist for an engine that is not built yet. Nothing says what the running system may update by itself, what its monitors trigger, how its own fills feed back, who proposes the next card, or what the owner is told. §4 and §5 supply that.

---

## 4. The learning architecture

### 4.1 What can be learned, and what cannot

The dividing line is statistical power, and the evidence for it is direct.

| The system can learn this from its own data | Why | The system cannot learn this from its own data | Why |
| --- | --- | --- | --- |
| Volatility and correlations | Persistent and forecastable over weeks to months (R14 finding 8, R15 #13, [2+]) | Which rule has the higher expected return | Backtest Sharpe barely predicts live Sharpe [2+, C24]; a 12-month shadow record has a standard error of about 1.0 on annual Sharpe [computed: 1 ÷ √years] |
| Its own trading costs: commission, spread, slippage, delay | Measured on every fill; own-execution models beat literature models [2+, C30] | Better lookbacks, thresholds or weights | Lookbacks within 2–12 months are indistinguishable [2+, C1]; re-optimising did worse than fixing [1, C6]; equal weights beat estimated ones [2+, C15, C28] |
| Spreads and liquidity of each ETF | Observed in every pre-trade snapshot | Whether its edge has decayed, quickly | An information-ratio loss of 0.3 takes about 194 months to detect at a false-alarm rate of one per 28 years [computed, §4.5] |
| Distribution dates and amounts; year-to-date tax position | Bookkeeping facts from Flex and the tax engine | Regime turning points in real time | Recognised late; misclassification removes the benefit [2+, C11, C13] |
| Data-vendor and broker reliability; job timings | Counted events | Which challenger to promote, from shadow results | The best of 12 no-edge rules leads by 1.63 tracking-error units a year [computed, §4.3] |
| Its own defects | Every reconciliation break and incident has a cause | — | — |

So the platform learns in three ways, each with its own safety mechanism:

- **Estimates** update automatically, inside bounds, with an audit trail (§4.4).
- **Monitors** watch for drift and trigger reviews, re-validation or halts, never a rule change (§4.5, §4.6).
- **Rules** change only through the research cycle: a card, a test, the yearly window, the owner (§4.3, §4.7).

### 4.2 Layers

| Layer | What changes | How often | Who decides | Guard |
| --- | --- | --- | --- | --- |
| L0 Facts | Prices, distributions, fills, cash, tax lots | Daily | Nobody; recorded | Reconciliation (RSK-25), bitemporal store |
| L1 Estimates | Volatility, correlations, multipliers, spread table, slippage, commission check, distribution forecast, tax estimate, eligibility | Monthly, effective at the next evaluation | The system | Whitelist, shrinkage, clamps, step limit, audit row, one-command revert (LRN-08 to LRN-12) |
| L2 Monitors | Drift states: implementation, cost, data, behaviour, edge, assumptions, environment | Monthly; yearly battery | The system raises; the owner disposes | Fixed thresholds with stated false-alarm rates (LRN-13 to LRN-17) |
| L3 Shadow knowledge | Challenger ledgers; library table | Monthly | Nobody; recorded | No broker access; luck band printed (LRN-01 to LRN-07) |
| L4 Rules | Signals, weights, sleeves, thresholds | At most once a year | The owner, after G2 and cooling-off | Cards, trial log, DSR / PBO / Holm, holdout budget, one promotion per 12 months |
| L5 Process | The gates, thresholds and this architecture | By spec version | The owner | Semantic versioning, `spec_hash` |

Nothing moves up a layer automatically. An L1 estimate can change an order's size or stop a symbol trading; it can never change a signal's direction or a rule's parameter.

### 4.3 The challenger library

**Size and growth.** At most 12 active challengers on the free data plan and 24 on a paid plan; at most 4 new cards a year; archived challengers are unlimited and keep their card, ledger and place in the trial count. The library starts with the 14 cards in §6 (12 active on day one; H39 and H43 start later), plus P1 and its variants, which the spec already runs.

**How a challenger is added.** A proposal memo (agent or owner) → the owner accepts it into the next freeze window → the card is frozen and hashed (G0) → builder and validator implement it (G1, G2 mechanics) → the backtest runs once on development data and is logged as a trial → the challenger starts in `paper_sim` at the next month-end.

**What it runs on.** Each challenger has its own `paper_sim` ledger at three notional sizes (A$5,000, A$25,000, A$100,000) and calls the production `decide()`, `build_orders()` and `RiskManager.apply()` with the section 25 cost model and the section 13 tax engine. It holds no broker credentials.

**Compute.** All rules are monthly on at most 15–30 symbols and about 420 months. One backtest is well under a minute on a small VPS [estimate]; the battery for 12 challengers at three sizes is 36 battery runs, minutes to an hour, off-hours. The monthly shadow step is 36 calls of the decision functions. Model refits (H36, H39) happen once a year. No GPU, no new service.

**Data budget (EODHD free plan, 20 calls a day)** [C34 primary; arithmetic computed].
- End-of-day, dividend and split requests cost 1 call each per symbol; a date range is one request; bulk requests cost 100 and are unusable on the free plan; a refused request costs nothing; the usage endpoint is free, so the fetcher can check the balance before every library call.
- Reserve 10 calls a day for the live symbols, benchmarks and retries (DAT-23). The other 10 may serve the library.
- Library symbols are fetched weekly, not daily: every challenger is a monthly rule, and a paper rule can wait two days for a month-end bar. 10 spare calls × 5 weekdays = 50 a week. Fifteen library symbols need 15 end-of-day calls a week plus 15 dividend calls a month: about 19 a week.
- Month-end: fetch all library symbols over the first two trading days of the month (8 a day); evaluate on the third.
- History: the free plan serves one year. The one-off paid month (DAT-23(1)) must download full history for every library symbol; a new symbol added later waits for another paid month (US$19.99).
- Proxies before ETF inception come from the `rental/` tree (RND-029). Macro series come from RBA and FRED files, outside the budget.
- Still unverified: whether the free plan serves ASX tickers at all (open item E1). If not, the system is on the paid plan and the cap rises to 24 challengers.
- This replaces §5.1's "P1 paper trading starts only while a paid plan is active" for `paper_sim` challengers only. P1 on the IBKR paper account needs daily data and keeps that rule.

**Trial counting.**
- Families: `L1`, `P1` (existing; H33 joins `P1`); new `L2` (H30, H34, H35, H42: changes to the overlay on the same sleeves); `R1` (H31, H32: switching and rotation); `X1` (H36–H39: exploratory); `S3` (H43: Stage 3 sleeve); `META` (H40, H41). Cap 50 per family (VAL-22).
- A grid neighbour is a trial. A refit that a card schedules is a replication. A re-run of a frozen card on refreshed cost tables or extended data is a replication (LRN-12, LRN-16). Anything else is a new card.
- **Library N** = all distinct trials ever run against the same benchmark, across families. Every pack prints family N and library N. Family B claims use library N (VAL-20 says "every logged trial"; this fixes the scope).
- This report's cards cost 46 trials if every grid is run: H30 7, H31 3, H32 7, H33 3, H34 3, H35 4, H36 3, H37 3, H38 2, H39 3, H40 2, H41 1, H42 3, H43 2 [computed]. The original L1 family is 12 and R31's S1 is 7.

**Why shadow results cannot select** [computed, 200,000 draws].

| Challengers with no true edge | Expected lead of the best, in tracking-error units | At 5% tracking error |
| --- | --- | --- |
| 5 | 1.16 | +5.8 points a year |
| 10 | 1.54 | +7.7 |
| 12 | 1.63 | +8.2 |
| 20 | 1.87 | +9.3 |
| 30 | 2.04 | +10.2 |

Every year the library table will show something beating the live rule by 6–10 points by chance. On the backtest side: over 34 years the standard error of an annual Sharpe difference is about 0.17, so the best of 20 no-edge rules shows about +0.32 by luck, and t ≥ 3.0 needs 0.51. The Deflated Sharpe Ratio makes exactly this correction, which is why N must be the library's.

**Promotion rule.**
1. One window a year, at the yearly review. At most one promotion per 12 months per account (RND-032).
2. Candidates: class `promotable`; result "passed" at G2 on development data; H12 passed; at least 12 shadow cycles (6 if the change adds no instrument and no signal type); one ON→OFF and one OFF→ON transition seen or drilled; fidelity clean.
3. Family A candidates in the window form one Holm family at α = 0.10. Family B candidates need t ≥ 3.0, DSR ≥ 0.95 at library N, and VAL-24 including Reality Check and SPA across the library.
4. Library PBO (CSCV, 16 blocks, all promotable cards' backtest returns) is printed. Above 0.25, rank among candidates may not be used.
5. Holdout: opened for a family only after its candidate has passed everything on development data; at most two openings a year.
6. If more than one candidate survives, the order of preference is fixed: the one that removes parameters or code; then the equal-weight blend of champion and candidate, if every order it implies meets the minimum; then the earliest freeze date. Never "the one that did best last year".
7. Glide: the new rule's targets apply at its next evaluation and are reached by its own orders and by contributions; no order is planned only to match the new rule on day one.
8. Seven-day cooling-off and owner approval (RND-005). The memo carries the luck table for the current N.

**Demotion and kill rules.**

| Object | Trigger | Consequence |
| --- | --- | --- |
| Challenger | Shadow ledger disagrees with a harness replay by more than 1 bp a month | Suspended from the window until fixed; two unresolved cycles → retired "fidelity" |
| Challenger | Shadow drawdown beyond the 95th percentile of its own pre-registered bootstrap | Struck from this year's window |
| Challenger | Beyond the 99th percentile | Card marked "outside envelope"; never promotable; kept running for the record |
| Challenger | Month-end data missing three cycles running | Suspended "data"; retired after six |
| Challenger | Card result "failed" or "not passed" | Stays as a reference for 12 months, then archived; a `control` stays indefinitely |
| Any card | Retired or archived | Card, ledger and trials remain; N never falls |
| Champion | RSK-22 drawdown halt, RSK-30 kill criteria | As today: buys halted; owner chooses STATIC or records a reason |
| Champion | Yearly battery on extended data fails the champion's own card thresholds two years running | Owner decision page: continue with a written reason, or `trader mode static`. Not automatic, and never a re-fit (MON-07) |
| Champion | A promoted rule breaches its drawdown envelope within 24 months of promotion | Reversion to the previous champion is offered as a single owner command; the reversion does not count as a promotion |

### 4.4 Estimates that update automatically, and parameters that never do

**Update mechanics (all whitelisted estimates).** New value = shrunk estimate, then clamped, then step-limited:

- shrinkage: (n₀ × prior + n × sample mean) ÷ (n₀ + n), with the prior and n₀ set in config;
- clamp: inside [lower, upper] bounds set in config;
- step limit: at most ±25% change per update;
- timing: computed on the first Sunday of the month, effective from the next evaluation, never on an evaluation or execution date;
- record: one append-only row (old, new, n, reason, inputs hash); `trader learn revert <id>` restores the previous value.

| Estimate | Estimator | Prior, n₀ | Clamp | Used by | Notes |
| --- | --- | --- | --- | --- | --- |
| Instrument volatility | SIZ-02 (35-day EW, 70/30 blend with long-run) | — | SIZ-02's own floor | §26 sizing; H35's cap; report | Already whitelisted (SIZ-12) |
| Correlations, FDM, IDM | SIZ-05 | — | Cap 2.5 | §26 sizing | Already whitelisted |
| Half-spread per ETF | Median of (ask − bid) ÷ 2 ÷ mid over pre-trade snapshots and weekly quote samples | RND-021 table (5 or 10 bp), n₀ = 20 | 0.5× to 3× prior | Cost model version; limit-price sanity; eligibility | Source is the system's own snapshots |
| Slippage per fill | Mean signed (fill − arrival mid) ÷ mid, by side | 1 tick, n₀ = 20 | 0 to 3× prior | Cost model version | Expect only 8–20 fills a year [estimate]: this converges over years |
| Delay cost | Mean move from D's close to arrival mid | Reported only | — | Report | RSK-26 already separates it; never enters the cost model |
| Commission | Realised vs `asx_fixed` | Exact schedule | Any mismatch above `review_gap` is an alert, not an update | EXE-09 | A fee-schedule change is an environment event (§4.5), fixed by the owner in config |
| Distribution forecast | Same-quarter amount last year × unit count; ex-dates from the last 8 | Issuer calendar | — | Cash forecast; DAT-14 expectation; tax estimate | Never used for signals |
| Tax estimate | Year-to-date realised gains and income from the section 13 engine; projected liability at the configured marginal rate | — | — | Quarterly report; contribution note | Informational; no order uses it unless a card says so (R33 HG3) |
| Liquidity (`adv20`) and eligibility | 20-day median value traded; SIZ-09 tests | — | — | RSK-07; live sleeve set can shrink | Can remove a symbol from trading; can never add one |
| Vendor and broker reliability | Late bars, restatements, Flex lateness, 2FA response time, rejects | — | — | Report; proposes schedule changes to the owner | No automatic schedule change |

**Cost-model versions.** The backtest cost model is a versioned table. A monthly update creates a new version only if any entry moved by more than 20% from the version the champion's card was validated on. A new version triggers a replication re-run of the champion's card and every promotable card (no new trials). If the champion's pass flips, the owner is paged and G2 is repeated, as G4 already requires when realised cost exceeds 1.5 × the model.

**Never updated automatically** (change only by card and promotion window, or by a spec version for process values): lookbacks, vote sets, thresholds and hysteresis; base weights, sleeve list, class risk budgets; tranche count rule, offsets, minimum order, band width; volatility-cap level and windows; blend weights and membership; any model's hyper-parameters or feature list; benchmark definitions; halt, kill and alert thresholds; the holdout boundary; test thresholds (t, DSR, PBO, Holm α); card classes; this whitelist.

The second list is long on purpose. C1, C6, C15 and C28 are the evidence that fitting these loses to leaving them alone.

### 4.5 Drift and decay detection

**CUSUM design** [computed by simulation, 3,000–4,000 paths per cell; one-sided on standardised monthly values, reference k = 0.5]:

| Decision limit h | Months between false alarms | Months to detect a 1.0 σ shift | 0.5 σ | 0.25 σ |
| --- | --- | --- | --- | --- |
| 3 | 117 | 6 | 18 | 39 |
| 4 | 342 | 8 | 26 | 77 |
| 5 | 947 | 10 | 38 | 140 |

Applied to a strategy's return against its benchmark, a loss of information ratio of 0.5 a year is a shift of only 0.144 σ a month and takes about 141 months to detect at h = 4 (62 at h = 3); a loss of 0.3 takes about 194 months (80 at h = 3) [computed]. Philips et al. report about 40 months for the same 0.5 loss at a much higher false-alarm rate, one per 7 years [1, C29]. The minimum track record to show a Sharpe of 0.5 is above zero at 95% is about 11 years of monthly data; for 0.3 it is about 30 years [computed from the Bailey–López de Prado formula, normal returns].

The conclusion drives the design: **CUSUM is sharp for things with small noise (implementation error, costs, data) and blunt for edge.** So edge monitors trigger reviews, and only integrity monitors trigger halts.

| # | Monitor | Statistic | Threshold | Triggers |
| --- | --- | --- | --- | --- |
| D1 | Implementation drift | CUSUM on monthly live-minus-replay return (MON-07), standardised by its own first-24-month σ, floor 2 bp | h = 4 | PAGE; integrity review. RSK-24's halts are unchanged |
| D2 | Cost drift | CUSUM on per-fill (realised cost − modelled cost) in bp, standardised | h = 4; also RSK-26 | Cost-model version refresh; replication re-run of champion and promotable cards |
| D3 | Data drift | Count of restated closes, late bars, vendor-vs-Flex mark gaps above 10 bp, per quarter | More than 2 of any kind in a quarter | WARN; vendor review item; proposes a paid-plan month for a full diff |
| D4 | Behaviour drift | Switches per sleeve and share of months in the market, against the card's bootstrap range; RSK-27 | Outside the 5th–95th percentile at the yearly review | Review memo: is it the market or the code? Replay check first |
| D5 | Shadow fidelity | Each challenger's ledger vs harness replay | 1 bp a month | §4.3 demotion table |
| D6 | Edge decay | Yearly battery on extended data (MON-07); rolling 36-month vs B2 (RSK-29); drawdown vs envelope (RSK-22) | The card's own thresholds | Reported. Two consecutive yearly failures → owner decision page (§4.3). Never a re-fit |
| D7 | Assumption monitors | Each card lists the observable assumptions it rests on; the monitor tracks them: 36-month share–bond correlation sign (P1, H33, H34); AUD-vs-global-equity correlation (PRT-24, R12); realised volatility percentile; cash rate vs distribution yield; ETF spread; ETF fee | Leaves its 1990–2023 range, or changes sign for 12 months | Flags the card "assumption changed" in the quarterly report and adds an item to the next research cycle. No automatic action |
| D8 | Environment | IBKR fee schedule and cash interest; ETF fee, index or closure notices; tax law dates (1 July 2027); EODHD plan terms; ASX calendar and auction times | Any change found by the quarterly check | Owner config or spec change; affected cards re-run as replications |

Regime change is handled by D6 and D7, not by a regime model in the live path: the evidence says such models recognise the change late [C11, C13], and a monitor that prompts a human review loses nothing by being late.

### 4.6 Learning from execution and reconciliation

**Per-fill record** (most fields exist in section 11 and 12; the learning layer adds the derived ones): decision close; arrival bid, ask and mid at snapshot; limit price and offset; venue phase (auction or continuous); time to fill; partial fills; fill price; commission and GST; slippage and delay cost in bp; whether the order was carried or replaced.

**What is learned from it.**
- The spread and slippage estimates of §4.4.
- A fill-quality table by time of day, phase and order size, in the quarterly report. With 8–20 fills a year no tactic comparison has power, so **execution tactics (order time, limit offset, auction use) change only by an "execution change note"**: a written before/after rationale, a paper drill, the owner's approval. Not a hypothesis card, because it makes no investment claim, and not automatic.
- Suppressed-order statistics: how often `MIN_ORDER` skipped a buy, and the cash it left idle. That feeds the yearly check of the tranche threshold and sleeve count (PRT-14, SIZ-09).

**Reconciliation and incidents: every break teaches a test.**
- Each `RECON_BREAK`, `TRACKING_HALT`, rejected order, missed run or data BLOCK gets a root-cause code from a fixed list (data vendor, broker, calendar, corporate action, distribution, timing, code defect, operator).
- Any incident closed as "code defect" must add a regression test and, where it involved a sequence of events, a scenario to the golden-file set (R25's walkthrough scenarios are the seed). The fix cannot be deployed without the test (BP-14 sequence).
- A root-cause code that recurs twice in 12 months opens a defect card with an owner-visible due date.
- The scenario count and the incident table go in the quarterly report. This is the most reliable learning the platform does: its failure library only grows.

### 4.7 Research cycles: where new rules come from

| Step | When | Who | Output | Limit |
| --- | --- | --- | --- | --- |
| Evidence scan | Quarterly | Research agent | A memo: new or updated papers on the system's designs; post-publication results for registered designs; ETF launches, fee changes, closures; law and broker changes; items raised by D6–D8 | At most 3 proposed cards per scan; every claim tagged and sourced as in this report |
| Triage | Within 14 days | Owner | Accept into the next freeze window, park, or reject, each with one line of reason | Parked and rejected proposals stay in the registry |
| Freeze window | Twice a year | Owner approves; agent drafts | Cards frozen and hashed (G0) | At most 4 new cards a year |
| Build and validate | After freeze | Builder agent; validator agent in a fresh context from the card only | Code, tests, backtest logged as trials, validation memo with "reasons this could be wrong" | RND-003, RND-005 |
| Shadow start | Next month-end | System | `paper_sim` ledgers | Library cap |
| Yearly review | Once a year | Owner, with agent-prepared pack | Battery re-run; library PBO; promotion window; retirements; holdout openings | One promotion; two openings |

**Agents may propose, code, test and report. They may never freeze a card, approve a result, open a holdout, promote, merge to the live branch or touch an order** (RND-002, unchanged). An agent's proposal has no standing until the owner accepts it.

**Agent knowledge contaminates the holdout.** Language models carry knowledge of the period they are asked to "test" [2+, C31]. A card drafted by a model trained on data through 2025 or 2026 was written with knowledge of 2024–2026 markets, whether or not the harness lock was opened. Three consequences, written into LRN-23:
1. every card records who proposed it (owner, or agent with model name and stated training cutoff);
2. for an agent-proposed card, holdout dates before the model's cutoff are reported as "holdout, proposer-exposed" and cannot by themselves satisfy the holdout confirmation; the card must also carry an economic rationale sourced to literature dated before the holdout begins;
3. the only clean evidence for such a card is post-registration data, which accumulates one month at a time.

This applies to every card in §6: they were drafted by an AI model with knowledge to mid-2026. The registry should say so.

### 4.8 The owner's quarterly report: "What the system learned"

Two pages, plain English, generated on the first Sunday of January, April, July and October. Fixed sections:

1. **What changed by itself.** A table of every estimate that moved: old value, new value, number of observations, and one line of why. Example row: "VAS half-spread: 5.0 → 4.1 bp, from 14 quotes and 6 fills."
2. **What it cost to trade.** Fills this quarter and year to date; commission, spread, slippage and delay against the model; orders skipped under the minimum and the cash that left idle.
3. **What drifted.** Each monitor D1–D8 as green, amber or red with its number and what it triggered.
4. **What the challengers did.** The library table: class, current holdings at the account's size, return and drawdown since shadow start, difference from the live rule; and beside it the luck band for the current N with the sentence: "A lead inside this band is what chance alone produces. Shadow results are not a reason to switch."
5. **What the research found.** Cards proposed, frozen, run; results including failures; trial counts (family and library); the DSR hurdle those counts now imply.
6. **What broke and what was fixed.** Incidents, root causes, tests and scenarios added.
7. **What did not change, and why.** The live rule's parameters, listed, with "unchanged since <date>; next window <date>".
8. **Decisions waiting for you.** Triage items, a freeze window, a promotion window, or none.
9. **One paragraph of honest limits.** How many years of live record the system has, and what that is and is not enough to conclude (for example: "23 months of live data cannot distinguish a good rule from a lucky one; the minimum for a Sharpe of 0.5 is about 11 years").

Section 7 is there because for a system built on restraint, "nothing changed" is a result, and the owner should see it stated.

### 4.9 Using machine learning safely

Ranked from safe to unsafe:

| Use | Risk | Rule |
| --- | --- | --- |
| Anomaly detection on operational data (odd bars, odd fills, unusual job timings) | Low: a false alarm costs a look | Allowed as an *additional* WARN source. It can never clear or replace a DAT check |
| Cost and slippage regression on own fills | Low; small sample | Allowed only as shrinkage toward the RND-021 prior (§4.4); no features beyond side, size and phase |
| Agents reading literature and drafting cards | Medium: look-ahead in the model's knowledge [C31] | §4.7 rules |
| Summarising existing signals (H39) | Medium: overfitting | Challenger only, class `exploratory`; fixed model class and penalty rule, no search; expanding-window walk-forward with a 12-month embargo; yearly refit; model objects hashed; benchmark is the equal-weight ensemble (H30) |
| Predicting which challenger will do best | High: this is selection on noise | Not allowed in any decision. May be explored offline; in the one large study an ML model predicted out-of-sample Sharpe better than backtest Sharpe did (R² 0.17 vs 0.02) on 888 strategies [C24], and this library will have about 14 |
| Return prediction in the live path; online learning; reinforcement learning | Very high | Not allowed (SIZ-12; section 8 of the spec) |

Ensembles are the form of "ML" with support here: equal-weight averaging of pre-registered rules (H30, H40). A learned ensemble must first beat the equal-weight one in its own card, at library N.

### 4.10 How it slots into the schedule and milestones

| Time (Sydney) | Days | Job | Does | On failure |
| --- | --- | --- | --- | --- |
| 19:45 | Trading days | `fetch_library` | After `fetch_vendor_data` has finished: reads the free usage endpoint; fetches today's round-robin share of library symbols by range request; all library symbols on the first two trading days of a month | Skip and log `LIB_DATA_GAP`; never retried from reserved calls; no page |
| 20:30 | Third trading day of the month | `library_evaluate` | Runs every active challenger's evaluation in `paper_sim` at three sizes; runs D5 | WARN |
| 04:00 | First Sunday of the month | `learn_update` | Computes the §4.4 estimates, applies shrink–clamp–step, writes audit rows effective from the next evaluation; runs D1–D4; creates a cost-model version if due | WARN; values stay as they were |
| 05:00 | First Sunday of Jan, Apr, Jul, Oct | `learning_report` | Builds the §4.8 report; runs D7 and the D8 checklist | WARN |
| Off-host | Quarterly | Evidence scan | Agent memo (§4.7) | — |
| — | Yearly review | Battery re-run (MON-07), library PBO, promotion window, retirements, holdout openings | As §4.3 | — |

None of these jobs runs within 2 hours of a trading job (BP-14), and none is on the order path: if every learning job failed for a year, L1 would trade exactly as it does today.

Milestones: M3 gains the library runner, trial-count fields and holdout budget (LRN-01 to LRN-07, LRN-25). M5 gains the per-fill derived fields and root-cause codes (LRN-18 to LRN-20). M6 gains `learn_update`, the monitors and the quarterly report (LRN-08 to LRN-17, LRN-26 to LRN-28). The research-cycle requirements (LRN-21 to LRN-24) and ML rules (LRN-29 to LRN-31) are process and need no build beyond registry fields.

---

## 5. Spec text (ready to paste)

New IDs: LRN-01 to LRN-34 and DAT-24. None is used in v2.10 or in reports 31–33. Proposed placement: a new **section 28A, "Learning architecture"**, after section 28, with the cross-references below.

### 5.1 Section 28A — challenger library (LRN-01 to LRN-07)

| ID | Requirement | Source |
| --- | --- | --- |
| LRN-01 | **Library.** The system runs a library of challengers beside the champion. A challenger is a frozen card (RND-010) bound to its own `paper_sim` ledger. Active challengers: at most 12 on the free vendor plan and 24 on a paid plan [design value — operational]. At most 4 new cards are frozen per calendar year. Archived challengers are unlimited; an archived or retired challenger keeps its card, ledger and trial rows. | [R35 §4.3] |
| LRN-02 | **Isolation.** Each challenger runs at notional sizing NAVs of A$5,000, A$25,000 and A$100,000 with the production `decide()`, `build_orders()` and `RiskManager.apply()`, the section 25 cost model and the section 13 tax engine. The challenger runner holds no broker credentials and imports no module under `broker/` except `paper_sim` (CI test). No challenger output is an input to any live decision. | [R20 RND-002], [R35 §4.3] |
| LRN-03 | **Card class and proposer.** Every card carries `class` (`promotable`, `control` or `exploratory`) and `proposer` (owner, or agent with model name and stated training cutoff), both fixed at freeze. Only a `promotable` card can enter a promotion window. Changing the class is a new card. | [R35 §4.3, §4.7] |
| LRN-04 | **Shadow results do not select.** No promotion decision may cite a challenger's shadow or live-period return, Sharpe or rank as a ground. Shadow results are used only to test fidelity (LRN-06), to veto (LRN-06) and to inform the owner (LRN-26). | [R20 RND-030], [R35 §4.3] |
| LRN-05 | **Library trial count and selection control.** The `trials` table records `family` and `library`. Library N is the number of distinct trials ever run against the same benchmark, across all families. Every reporting pack prints family N and library N. Family B claims use library N in the Deflated Sharpe Ratio. At a promotion window: all Family A candidates form one Holm family at α = 0.10; Family B candidates need t ≥ 3.0, DSR ≥ 0.95 and VAL-24 including Reality Check and SPA across the library; the Probability of Backtest Overfitting is computed by CSCV with 16 blocks over the backtest returns of every `promotable` card, and if it exceeds 0.25 rank among candidates may not be used. New families: `L2` (H30, H34, H35, H42), `R1` (H31, H32), `X1` (H36–H39), `S3` (H43), `META` (H40, H41); H33 joins `P1`; each has the VAL-22 cap of 50. | [R16 VAL-20, VAL-24], [R35 §4.3] |
| LRN-06 | **Challenger demotion.** (a) A shadow ledger that disagrees with a harness replay of the same months by more than 1 bp a month suspends the challenger from the window; unresolved after two cycles, it is retired with reason `fidelity`. (b) A shadow drawdown beyond the 95th percentile of the bootstrap recorded in the card strikes it from the current window; beyond the 99th percentile the card is marked `outside_envelope` and is never promotable. (c) Month-end data missing for three consecutive cycles suspends it; six retires it. (d) A card with result "failed" or "not passed" stays active for 12 months as a reference and is then archived; a `control` stays. Retirement is a dated registry entry with a reason; N never decreases. | [R35 §4.3] |
| LRN-07 | **Promotion window.** One window a year, in the yearly review. A candidate needs: class `promotable`; "passed" at G2 on development data; H12 passed; the holdout confirmation under LRN-25; at least 12 shadow cycles, or 6 if it adds no instrument and no signal type [design value — operational]; one ON→OFF and one OFF→ON transition seen or drilled; LRN-06 clean. If more than one candidate survives LRN-05, the choice is, in order: the candidate that removes parameters or code; the equal-weight blend of champion and candidate, if every order it implies is at least `min_order_value_aud`; the earliest freeze date. At most one promotion per 12 months (RND-032). **Glide:** after a promotion the new rule's targets apply from its next scheduled evaluation and positions move only by orders the new rule itself plans (PRT-16) and by contributions; a promotion that removes an instrument sells it on the first execution date as a transition sell. **Reversion:** if a promoted rule breaches its drawdown envelope (RSK-22) within 24 months, `trader champion revert --confirm` restores the previous champion; a reversion is not a promotion. | [R35 §4.3] |

### 5.2 Section 28A — automatic estimates (LRN-08 to LRN-12)

| ID | Requirement | Source |
| --- | --- | --- |
| LRN-08 | **Whitelist.** Only these values may change without a card: instrument volatility (SIZ-02); correlations and diversification multipliers (SIZ-05); the per-ETF half-spread table; per-fill slippage; the distribution forecast; the tax estimate; `adv20` and eligibility (RSK-07, SIZ-09); vendor and broker reliability statistics. This list extends SIZ-12 and is exhaustive. Adding to it is a spec change. | [R14], [R16], [R35 §4.4] |
| LRN-09 | **Never automatic.** The following change only by a new card and a promotion window, or by a spec version where they are process values: lookbacks, vote sets, thresholds and hysteresis; base weights, the sleeve list, class risk budgets; the tranche rule, offsets, minimum order and band; volatility-cap level and windows; blend weights and membership; any model's hyper-parameters or features; benchmark definitions; halt, kill and alert thresholds; the holdout boundary; test thresholds; card classes; LRN-08. A CI test fails if any of these config keys is written by a job. | [R14 R2], [R35 §4.4, C1, C6, C15, C28] |
| LRN-10 | **Update mechanics.** A whitelisted estimate with a prior is updated as (n₀ × prior + n × sample mean) ÷ (n₀ + n), then clamped to its configured bounds, then limited to a ±25% change per update [design value — operational]. Defaults: half-spread prior = the RND-021 table, n₀ = 20, bounds 0.5× to 3× the prior; slippage prior = one tick, n₀ = 20, bounds 0 to 3× the prior. Updates are computed by `learn_update` on the first Sunday of the month and take effect at the next evaluation; none takes effect on an evaluation or execution date. | [R35 §4.4] |
| LRN-11 | **Audit and revert.** Every update appends one row to `learned_values` (key, old, new, n, inputs hash, job run id, effective date). The app role has INSERT only. `trader learn show` lists current values and their history; `trader learn revert <id> --confirm` restores a previous value and logs the reason. An estimate can reduce an order, skip an order or remove a symbol from trading; no estimate can change a signal's direction, a target weight's rule or add a symbol. A test confirms L1's decisions are identical with `learn_update` enabled or disabled when the estimates are at their priors. | [R35 §4.4] |
| LRN-12 | **Cost-model versions.** The section 25 cost model reads a versioned cost table. `learn_update` creates a new version only if an entry differs by more than 20% from the version on which the champion's card was validated [design value — operational]. A new version triggers a re-run of the champion's card and every `promotable` card as replications (VAL-22), not new trials. If the champion's result changes from "passed", the owner is paged and G2 is repeated with the new version (as section 17, G4). Commission is never estimated: a realised commission outside `review_gap` of the configured schedule raises an alert and the owner corrects the schedule. | [R16], [R35 §4.4, C30] |

### 5.3 Section 28A — monitors, execution learning, research cycle, report, ML (LRN-13 to LRN-34)

| ID | Requirement | Source |
| --- | --- | --- |
| LRN-13 | **CUSUM standard.** Drift monitors use a one-sided CUSUM on standardised values with reference value 0.5 and decision limit 4 [design value — operational]: about 342 months between false alarms, and about 8 months to detect a one-standard-deviation shift [computed, R35 §4.5]. Each monitor's standardising mean and deviation are fixed from its first 24 observations or from the card's bootstrap, and are recorded. A monitor is reset only by a logged owner command. | [R35 §4.5], [Philips et al. 2003] |
| LRN-14 | **Integrity monitors (may page).** D1: CUSUM on monthly live-minus-replay return (MON-07; deviation floor 2 bp) → PAGE and integrity review; RSK-24 is unchanged. D2: CUSUM on per-fill realised-minus-modelled cost → LRN-12 version check. D3: more than two restated closes, late bars or vendor-vs-Flex mark gaps above 10 bp in a quarter → WARN and a vendor review item. D5: LRN-06(a). | [R20 MON-07], [R35 §4.5] |
| LRN-15 | **Behaviour and edge monitors (review only).** D4: switches per sleeve and share of months in the market against the card's bootstrap range, checked at the yearly review; outside the 5th–95th percentile → a review memo, starting with a replay check. D6: the yearly battery on extended data (MON-07), RSK-29 and RSK-22. If the champion fails its own card thresholds in two consecutive yearly batteries, the owner is paged with a decision: continue with a written reason, or `trader mode static --confirm`. No monitor in this requirement halts orders, and no result is used to re-fit. | [R20 RND-031], [R35 §4.5] |
| LRN-16 | **Assumption monitors.** Every card lists the observable assumptions it rests on (field `assumptions`, added to RND-010). `learning_report` tracks each: for example the 36-month share–bond correlation sign, the AUD–global-equity correlation, realised volatility percentile, cash rate, ETF spread and fee. An assumption that leaves its 1990–2023 range, or changes sign for 12 consecutive months, flags the card `assumption_changed` in the report and adds an item to the next evidence scan. It triggers no order and no parameter change. A re-run of a frozen card on extended data is a replication. | [R35 §4.5] |
| LRN-17 | **Environment check.** Each quarter the report lists, with source and date: IBKR's commission schedule and cash interest tiers; each held ETF's fee, index and any closure notice; tax-law commencement dates in section 13; the vendor's plan terms; next year's ASX calendar status. A change is applied only by the owner (config or spec change); affected cards are re-run as replications. | [R35 §4.5] |
| LRN-18 | **Per-fill learning record.** For every fill the ledger derives and stores: arrival bid, ask and mid; limit offset; venue phase; time to fill; slippage and delay cost in basis points (RSK-26 definitions); carried or replaced flag. For every skipped buy: reason code and the cash left idle. | [R35 §4.6] |
| LRN-19 | **Execution tactics.** Order time, limit offset and auction use are not learned automatically. A change needs an execution change note (before and after, rationale, expected effect), a paper drill, and the owner's approval under BP-14. The quarterly report shows fill quality by phase and size so the note has data. | [R35 §4.6] |
| LRN-20 | **Incidents teach tests.** Every `RECON_BREAK`, `TRACKING_HALT`, rejected order, missed run and data BLOCK is closed with one root-cause code from a fixed list (vendor, broker, calendar, corporate action, distribution, timing, code defect, operator). An incident closed as `code defect` cannot be deployed as fixed without a regression test and, where it involved a sequence of events, a golden-file scenario. A code that recurs twice in 12 months opens a defect card with a due date. | [R17], [R25], [R35 §4.6] |
| LRN-21 | **Evidence scan.** Each quarter a research agent produces a memo: new or updated evidence on registered designs, including post-publication results; ETF launches, fee changes and closures; law and broker changes; items raised by LRN-15 to LRN-17. Every claim is tagged [2+], [1] or [unverified] with a URL. The memo proposes at most 3 cards. | [R20], [R35 §4.7] |
| LRN-22 | **Triage and freeze windows.** The owner triages each proposal within 14 days: accept into the next freeze window, park or reject, with a one-line reason stored in the registry. Cards are frozen in two windows a year, at most 4 a year (LRN-01). An agent may draft a card, code it, test it and report on it. An agent may not freeze a card, approve a result, open a holdout, promote, merge to the live branch, or create or modify an order (RND-002). | [R20 RND-002], [R35 §4.7] |
| LRN-23 | **Proposer exposure.** For a card whose `proposer` is an agent, holdout dates earlier than the model's stated training cutoff are reported as "holdout, proposer-exposed". They cannot by themselves satisfy the holdout confirmation: the card must also cite an economic rationale from sources dated before 2024-01, and its post-registration record is reported separately as the only unexposed evidence. Cards H30–H43 are agent-proposed with a cutoff after the holdout start and carry this label. | [R35 §4.7, C31] |
| LRN-24 | **Failed research is kept.** Every proposal, parked item, failed card and retired challenger stays in the registry with its reason (RND-006). The quarterly report counts them. | [R20 RND-006] |
| LRN-25 | **Holdout budget.** A holdout opening (RND-025) is granted to a family only after its candidate card has passed every development-data threshold and the battery. At most two openings per calendar year across all families. Each opening is logged with who saw the result. Data dated after a card's freeze is labelled "post-registration" and never pooled with development data for that card. | [R20 RND-025], [R35 §4.3] |
| LRN-26 | **Quarterly learning report.** On the first Sunday of January, April, July and October the system generates "What the system learned", at most two pages, with these sections in this order: what changed by itself (every LRN-11 row); what it cost to trade (against the model); what drifted (each monitor's state and number); what the challengers did (LRN-27); what the research found (cards proposed, frozen, run, results including failures; family and library N); what broke and what was fixed (LRN-20); what did not change and why (the live rule's parameters with "unchanged since"); decisions waiting for the owner; and one paragraph on what the length of the live record can and cannot show. | [R33 §2.8], [R35 §4.8] |
| LRN-27 | **Library table and luck band.** The report's library table lists, per challenger: class, current target weights at the account's size, return and maximum drawdown since shadow start, and difference from the champion. Beside it the report prints, for the current number of challengers N and their median tracking error σ, the expected lead of the best of N no-edge rules (σ × E[max of N standard normals]) and the sentence: "A lead inside this band is what chance alone produces. Shadow results are not a reason to switch (LRN-04)." | [R35 §4.3] |
| LRN-28 | **Learning jobs are off the order path.** `fetch_library`, `library_evaluate`, `learn_update` and `learning_report` never run within 2 hours of a trading job, hold no broker connection, and fail to WARN only. A test confirms that with all four disabled the live plan for a recorded month is byte-identical. | [R35 §4.10], [BP-14] |
| LRN-29 | **Machine learning: permitted uses.** (a) Anomaly detection on operational data as an additional WARN source; it never clears or replaces a section 6 check. (b) Cost estimation only as LRN-10 shrinkage. (c) A model inside a challenger of class `exploratory`. No model output is an input to a live decision. | [R35 §4.9] |
| LRN-30 | **Machine learning: challenger rules.** A model-based card fixes before any run: the feature list; one model class; hyper-parameters or a closed-form rule for them (no search); an expanding-window walk-forward with a 12-month embargo; a yearly refit month. Every fitted model object is hashed and stored. Its benchmark is the equal-weight ensemble of the same features. A promotable version is a new card under Family B at library N. | [R35 §4.9, C21–C25] |
| LRN-31 | **No performance-driven selection or weighting.** No rule, job or model may weight, select or switch between algorithms using their realised, shadow or backtest performance. A blend of rules has fixed equal weights and a membership list set in a card. (Extends SIZ-12.) | [R35 C4, C5, C15, C24, C28] |
| LRN-32 | **Champion decay.** Champion demotion follows RSK-22 and RSK-30 unchanged, plus LRN-15's two-year battery rule and LRN-07's reversion. No demotion is triggered by a challenger's results. | [R35 §4.3] |
| LRN-33 | **Schedule.** `fetch_library` 19:45 on trading days, after `fetch_vendor_data` completes; `library_evaluate` 20:30 on the third trading day of each month; `learn_update` 04:00 on the first Sunday of each month; `learning_report` 05:00 on the first Sunday of January, April, July and October. Times are config (`schedule.*`). | [R35 §4.10] |
| LRN-34 | **Acceptance tests.** (i) LRN-02's import test; (ii) LRN-09's write test; (iii) LRN-11's identity test; (iv) LRN-28's identity test; (v) a seeded simulation in CI reproduces the LRN-13 false-alarm and detection figures within 15%; (vi) a fault-injected spread series moves the half-spread estimate by no more than the step limit per update and never outside its bounds; (vii) the report generator prints the luck band for N = 5, 10 and 20 as 1.16, 1.54 and 1.87 σ. | [R35] |

### 5.4 Amendments to existing requirements

| Where | Change |
| --- | --- |
| Section 6, new **DAT-24** | **Library data budget.** Of the daily vendor budget (DAT-23), 10 calls are reserved for the live symbols, benchmarks and their retries; the remainder may be used for library symbols. Before each library request the fetcher reads the vendor's usage endpoint (no call cost) and stops if the reserve would be touched. Library symbols are fetched by one range request per symbol per week on a fixed round-robin, and all of them on the first two trading days of each month; one dividend request per symbol per month. At most 15 library symbols on the free plan [design value — operational]. If a library symbol's month-end bar is missing on the third trading day, that challenger's evaluation is skipped and logged (`LIB_DATA_GAP`); nothing is paged. Full history for a library symbol is loaded only during a paid month (DAT-23(1)). Macro series for exploratory cards are read from RBA and FRED files, stored bitemporally with their publication date, and are not vendor calls. Sources: [R35 §4.3], [EODHD limits page, read 13 Nov 2026]. |
| Section 5.1, last sentence | Add: "This restriction applies to P1 on the IBKR paper account. `paper_sim` challengers follow DAT-24." |
| RND-010 | Add fields: `class`, `proposer`, `assumptions` (LRN-03, LRN-16). |
| RND-013 | Add: "H30–H43 are added by report 35 (LRN-05 lists their families)." |
| RND-032 | Replace "a challenger runs in paper for at least 6 cycles beside the live champion" with "challengers run under section 28A; the minimum shadow period is in LRN-07". |
| MON-07 | Add: "The CUSUM parameters and the full set of drift monitors are in LRN-13 to LRN-17." |
| SIZ-09 | Add: "The number of live sleeves in an account does not exceed sizing NAV ÷ (2.5 × `min_order_value_aud`), rounded down [design value — operational]: two at A$5,000, six at A$15,000, ten at A$25,000 [computed]. P1's paper universe may be larger than its live set." |
| SIZ-12 | Add: "LRN-08 and LRN-09 are the complete lists; LRN-31 forbids performance-driven selection among algorithms." |
| Section 4 schedule | Add the four rows of LRN-33. |
| Section 17, yearly procedures | Add: "run the promotion window (LRN-07); run library PBO (LRN-05); review assumption flags (LRN-16); retire or archive challengers (LRN-06)." Quarterly: "triage the evidence scan (LRN-22); read the learning report (LRN-26)." |
| Section 20 milestones | M3: LRN-01 to LRN-07, LRN-25. M5: LRN-18 to LRN-20. M6: LRN-08 to LRN-17, LRN-26 to LRN-28, LRN-33, LRN-34. |

### 5.5 Configuration (common.yaml)

```yaml
learning:
  enabled: true
  library:
    max_active_free_plan: 12
    max_active_paid_plan: 24
    max_new_cards_per_year: 4
    notional_navs_aud: [5000, 25000, 100000]
    max_symbols_free_plan: 15
    reserved_live_calls_per_day: 10
    fetch: {eod: weekly_round_robin, month_start_days: 2, dividends: monthly}
  promotion:
    window: yearly_review
    min_shadow_cycles: 12
    min_shadow_cycles_same_instruments: 6
    pbo_max: 0.25
    holdout_openings_per_year: 2
    fidelity_tolerance_bp_month: 1
    shadow_dd_strike_percentile: 95
    shadow_dd_bar_percentile: 99
    reversion_window_months: 24
  estimates:
    step_limit: 0.25
    half_spread: {prior: rnd021_table, n0: 20, lower_mult: 0.5, upper_mult: 3.0}
    slippage:    {prior_ticks: 1, n0: 20, lower_mult: 0.0, upper_mult: 3.0}
    cost_version_trigger: 0.20
  monitors:
    cusum: {k: 0.5, h: 4.0, warmup_obs: 24}
    replay_sigma_floor_bp: 2
    data_events_per_quarter_warn: 2
    battery_fail_years_for_decision: 2
  research:
    evidence_scan: quarterly
    max_proposals_per_scan: 3
    triage_days: 14
    freeze_windows_per_year: 2
schedule:
  fetch_library: "19:45"
  library_evaluate: {day: 3rd_trading_day, time: "20:30"}
  learn_update: {day: first_sunday, time: "04:00"}
  learning_report: {months: [1, 4, 7, 10], day: first_sunday, time: "05:00"}
```

---

## 6. Hypothesis cards (RND-010 format)

**Fields common to every card below** (stated once): *Date registered* and *card hash*: set at `trader hypothesis freeze`. *Proposer*: agent (AI model, knowledge to mid-2026); LRN-23 applies. *Sample*: development 1990-01 to 2023-12 on monthly total-return proxies (RND-024), ETF data from inception; *holdout* 2024-01 onward, opened under LRN-25 and labelled proposer-exposed. *Costs and tax*: section 25 models; results at A$5,000, A$25,000, A$100,000 and under both CGT regimes (RND-022). *Shared settings*: N = 1 tranche, offset `last`, cash return per RND-021. *Result, decision, approver*: blank until run. *Trials consumed* counts the rule plus every grid neighbour.

### H30 — Wide trend ensemble (family L2, promotable)

| Field | Content |
| --- | --- |
| ID / class | H30 / `promotable` |
| Economic rationale | Before data: trend signals between 3 and 12 months are near-substitutes [C1, C2]; one specification's result contains luck worth hundreds of basis points a year [C3]. Averaging many removes the luck without changing the bet. Counter-rationale: all signals share one exposure and fail together in a V-shaped fall; more signals may add turnover at the margins. |
| Assumptions | Trend persists at 3–12 months in equity indices; signal types stay correlated above about 0.8. |
| Exact rule | Per sleeve at each month-end, 13 signals on the total-return series, each in [0, 1]. Type A (4): 1 if TR(m) ÷ TR(m−k) − 1 > the cash return over k months, k = 3, 6, 9, 12. Type B (4): 1 if TR(m) > simple mean of the last k month-ends, k = 6, 8, 10, 12. Type C (3): 1 if EMA(f) > EMA(s) of month-end TR, (f, s) = (1, 4), (2, 8), (3, 12) months. Type D (2): (TR(m) − min) ÷ (max − min) over the last k month-ends, k = 6, 12. Score s = mean of the four type means. State machine as PRT-13 with: s ≥ 0.60 → ON; s ≤ 0.40 → OFF; otherwise keep the prior state. Everything else exactly as section 9.1. |
| Fixed parameters | The 13 signals; equal weight by type; thresholds 0.60 / 0.40; VAS 0.40, VGS 0.60. |
| Permitted perturbation grid | Thresholds {0.67 / 0.33, 0.50 / 0.50}; drop each type in turn (4 variants); graded mapping: target = base weight × round(3s) ÷ 3 with a one-step dead band, evaluated at A$25,000 and A$100,000 only (reported, decided with H9). Six neighbours counted as trials. |
| Data and proxy map | As H1. |
| Benchmark | L1 exactly as H1. |
| Primary metric (one) | Specification dispersion: the standard deviation of CAGR across 12 start months × the rule's own perturbation grid, H30 against L1. |
| Secondary metrics | Maximum drawdown vs B2 (must still meet H1's 25% relative reduction); switches per decade; after-tax CAGR vs L1; February–April 2025 row; Ulcer index. |
| Pass threshold | Dispersion at least 30% lower than L1's; maximum drawdown no more than 2 points worse than L1; switches per decade no more than 10% higher; after-tax CAGR within −0.3 points of L1; H1's threshold met in its own right. |
| Fail threshold | Dispersion not lower; or drawdown more than 4 points worse than L1. Between: "not passed" (RND-015); L1 stays. |
| Multiple-testing family and adjustment | Family A, design choice (as H3); if a candidate, in the window's Holm family (LRN-05). Strategy family `L2`. |
| Trials consumed | 7 |

### H31 — Dual momentum, Australian GEM (family R1, control)

| Field | Content |
| --- | --- |
| ID / class | H31 / `control` |
| Economic rationale | Before data: relative strength persists across equity regions and absolute momentum avoids bear markets (Antonacci). Counter-rationale, which is the expectation: the relative leg is specification luck [C3]; the rule trailed after publication [C6]; full-book switches are costly and tax-hostile here. Registered so the owner can see it, and to check the harness reproduces the known post-2014 weakness. |
| Assumptions | Regional equity leadership persists for months. |
| Exact rule | Month-end: if the 12-month total return of VGS exceeds the 12-month cash return, hold 100% in whichever of VAS or VGS has the higher 12-month total return; otherwise hold 100% VAF. |
| Fixed parameters | 12-month lookback; one holding; monthly. |
| Permitted perturbation grid | Lookback {6, 9}; defensive asset cash instead of VAF (reported). Two neighbours. |
| Data and proxy map | VAS, VGS as RND-024; VAF: Bloomberg AusBond Composite 0+ Yr total return minus the fund fee; start date and licence [unverified]. |
| Benchmark | B2. |
| Primary metric (one) | After-tax CAGR difference vs B2 at A$25,000, 37% plus Medicare, regime (b). |
| Secondary metrics | Maximum drawdown; switches per year; cost drag at each NAV; 2014–2023 vs 1990–2013; dispersion across the grid; 2020 Q1 and February–April 2025 rows. |
| Pass threshold | None (control). Expectation: after-tax CAGR below B2; post-2014 weaker than pre-2014. |
| Fail threshold | Audit trigger, as H2: an after-tax uplift above +1.0 point a year, or post-2014 stronger than pre-2014, triggers a look-ahead and data audit. |
| Multiple-testing family and adjustment | Family B form, reported only. Strategy family `R1`. |
| Trials consumed | 3 |

### H32 — Relative-strength rotation, top 3 of 8 (family R1, promotable under Family B)

| Field | Content |
| --- | --- |
| ID / class | H32 / `promotable` |
| Economic rationale | Before data: cross-asset momentum is documented in long-short portfolios (R15 #15); an absolute filter supplies the drawdown control that ranking alone lacks (R14 R4). Counter-rationale: published and decayed [C7]; the best-tracked example needed repeated re-tuning [C8]; costs 0.55–1.8% a year and about 1–1.5 points of extra tax here; expected net negative. |
| Assumptions | Asset-class leadership persists 3–12 months; ETF spreads stay near their table values. |
| Exact rule | Universe: VAS, VGS, IVV, VGE, VSO, VAF, PMGOLD, AAA. Month-end score = mean of 3-, 6- and 12-month total returns. Rank the seven non-cash assets. Hold the top three at one-third each; a slot whose asset's score ≤ the cash score holds AAA. A held asset keeps its slot while its rank ≤ 4 (buy at rank ≤ 3, hold to rank 4). No rebalancing between slots unless a slot drifts outside ±20% relative. |
| Fixed parameters | Lookbacks 3/6/12; top 3; hold-to rank 4; equal slots. |
| Permitted perturbation grid | Top {2, 4}; lookback {12 only, 6/12}; hold-to rank {3, 5}. Six neighbours. |
| Data and proxy map | Proxies, each [unverified] for start date and licence until frozen: S&P/ASX 300 accumulation; MSCI World ex-Australia NR AUD; S&P 500 TR in AUD; MSCI Emerging Markets NR AUD; S&P/ASX Small Ordinaries accumulation; Bloomberg AusBond Composite; LBMA gold PM in AUD; RBA cash rate compounded. Each less the fund fee [C35]. Thin-ETF half-spread (10 bp) for VSO, VGE. A proxy starting after 1990 shortens the sample for the whole card; under 25 years: "not testable". |
| Benchmark | B2; and, reported, the equal-weight static mix of the same eight. |
| Primary metric (one) | Net-of-cost, after-tax annualised return difference vs B2 at A$100,000. |
| Secondary metrics | Same at A$5,000 and A$25,000; maximum drawdown; switches per year; cost and tax drag separately; share of profit by asset (VAL-24: none above 30%); 2022 row. |
| Pass threshold | t ≥ 3.0 and DSR ≥ 0.95 at library N; VAL-24; positive after H12; maximum drawdown not worse than B2's. Even then it may be proposed only as a satellite of at most 20% at sizing NAV ≥ A$50,000, by spec change. |
| Fail threshold | Return difference ≤ 0 after H12 at A$100,000; or drawdown more than 4 points worse than B2. Between: "not passed". |
| Multiple-testing family and adjustment | Family B. Strategy family `R1`, cap 50, own holdout opening under LRN-25. |
| Trials consumed | 7 |

### H33 — Unlevered risk parity static mix (family P1, control)

| Field | Content |
| --- | --- |
| ID / class | H33 / `control` |
| Economic rationale | Before data: equal risk contribution diversifies better than capital weights. Counter-rationale: without leverage it is a low-equity, lower-return portfolio [C9], and it fell with everything else in 2022 [C10]. |
| Assumptions | Share–bond correlation is not persistently positive. |
| Exact rule | Four sleeves: VAS, VGS, VAF, PMGOLD. Weight ∝ 1 ÷ 12-month volatility of monthly returns, normalised to 1, recomputed monthly, traded only outside a ±20% relative band. No trend filter, no leverage. |
| Fixed parameters | 12-month volatility; four sleeves; band ±20%. |
| Permitted perturbation grid | 36-month volatility; AAA as a fifth sleeve. Two neighbours. |
| Data and proxy map | As H31 and H32. |
| Benchmark | P1's V0; B2 reported. |
| Primary metric (one) | Maximum drawdown difference vs V0. |
| Secondary metrics | After-tax CAGR vs V0 and B2; volatility; 2022 row; turnover. |
| Pass threshold | None (control). Expectation: return 1.5–3 points below B2; drawdown lower than B2's in 2008, not in 2022. |
| Fail threshold | Audit trigger: CAGR above B2's over the full sample. |
| Multiple-testing family and adjustment | Family A form, reported only. Strategy family `P1`. |
| Trials consumed | 3 |

### H34 — Defensive-asset choice while OFF (family L2, promotable)

| Field | Content |
| --- | --- |
| ID / class | H34 / `promotable`. Depends on R33's HG1 (cash ETF while OFF); if HG1 is not adopted the benchmark below is L1 with uninvested cash. |
| Economic rationale | Before data: the trend literature credits a cash or bond return while out of the market; bonds have rallied in most equity bear markets. Counter-rationale: bonds and shares fell together in 2022 [C10]; a second instrument doubles the orders at each transition; bond distributions are taxed as income. |
| Assumptions | Share–bond correlation in equity bear markets is negative or near zero; AAA and VAF spreads stay at table values. |
| Exact rule | L1 as section 9.1. When a sleeve's target falls to zero and its sale has settled: buy VAF with the proceeds if VAF's 12-month total return exceeds the 12-month cash return at that month-end, otherwise buy AAA. Re-check the choice only at that sleeve's evaluations; switch between VAF and AAA only if the condition has held or failed for two consecutive evaluations. On any ON transition sell the defensive holding and buy the sleeve on the first day proceeds are settled. Orders below `min_order_value_aud` are skipped. |
| Fixed parameters | 12-month bond trend; two-evaluation confirmation; instruments VAF and AAA. |
| Permitted perturbation grid | Always VAF (no bond trend test); bond lookback 6 months. Two neighbours. |
| Data and proxy map | AAA: RBA cash rate less 0.18% before listing. VAF as H31. |
| Benchmark | L1 with HG1's cash-ETF leg (or L1 as specified, see ID row). |
| Primary metric (one) | After-tax CAGR difference vs the benchmark at A$25,000. |
| Secondary metrics | Maximum drawdown (must not be worse by more than 1 point); 2022 row; extra orders per year; result at A$5,000 where transition orders are smallest; re-entry delay in days from the extra settlement. |
| Pass threshold | After-tax CAGR at least 0.25 points a year higher at A$25,000, not lower at A$5,000, drawdown no more than 1 point worse, 2022 row no worse than the benchmark by more than 2 points; passes H12. |
| Fail threshold | No CAGR gain at A$25,000, or drawdown more than 2 points worse. |
| Multiple-testing family and adjustment | Family A design choice by thresholds (it claims a cash-return pickup, not timing skill); Holm family of its window. Strategy family `L2`. |
| Trials consumed | 3 |

### H35 — Downward-only volatility cap on L1 (family L2, promotable)

| Field | Content |
| --- | --- |
| ID / class | H35 / `promotable` |
| Economic rationale | Before data: volatility clusters and high-volatility periods carry fatter left tails; scaling down thins the tail (R14 finding 8). Counter-rationale: real-time volatility timing does not raise return (R15 #13); the cap can sell after a fall and miss the rebound; at A$5,000 the adjustments fall below the minimum order. |
| Assumptions | Volatility remains persistent month to month. |
| Exact rule | L1 as section 9.1. At each evaluation, if the trailing 3-month realised volatility of the 40/60 mix (daily returns, annualised) exceeds 20%, every ON sleeve's target is multiplied by 20% ÷ realised volatility, floor 0.5. Recomputed only at evaluations (PRT-20 stands). A change that implies an order below `min_order_value_aud` is skipped. |
| Fixed parameters | Cap 20%; 3-month window; floor 0.5. |
| Permitted perturbation grid | Cap {15%, 25%}; window {1 month}. Three neighbours. |
| Data and proxy map | Needs daily data: licensed daily proxy history where available, else ETF-era, labelled "short sample"; if neither, "not testable" (as H5, H8). |
| Benchmark | L1 as H1. |
| Primary metric (one) | Maximum drawdown difference vs L1 at A$25,000. |
| Secondary metrics | 2020 Q1 and February–April 2025 rows; after-tax CAGR; orders suppressed at A$5,000; turnover. |
| Pass threshold | Maximum drawdown at least 2 points lower than L1; after-tax CAGR no more than 0.3 points lower; holds in at least 3 of 4 regime splits; passes H12. |
| Fail threshold | No drawdown improvement, or CAGR more than 0.75 points lower. |
| Multiple-testing family and adjustment | Family A; Holm family of its window. Strategy family `L2`. |
| Trials consumed | 4 |

### H36 — Two-state regime model (family X1, exploratory)

| Field | Content |
| --- | --- |
| ID / class | H36 / `exploratory` |
| Economic rationale | Before data: markets alternate between calm and turbulent states [C11]. Counter-rationale: regimes are recognised late; with about six bear markets the model is fitted to a handful of events; the published gains are on daily data with tuned smoothing and no tax [C12, C13]. |
| Assumptions | Two persistent volatility states exist and are stable across refits. |
| Exact rule | Two-state Gaussian hidden Markov model on monthly returns of the 40/60 mix. Expanding window, first fit 1990-01 to 1999-12, refit each January; states ordered by variance (low = state 0). Each month-end, filtered (not smoothed) probability of state 1 > 0.5 → all sleeves OFF; ≤ 0.5 → all ON. Seed and library version recorded; every refit's parameters hashed and stored. |
| Fixed parameters | Two states; Gaussian emissions; expanding window; annual refit; threshold 0.5. |
| Permitted perturbation grid | Hysteresis 0.7 / 0.3; a statistical jump model on the same monthly series with the penalty fixed at one value named in the card at freeze, not re-tuned. Two neighbours. |
| Data and proxy map | As H1. Truncation invariance (SYS-16) is tested on the filtered probabilities and reported; a failure is recorded. |
| Benchmark | L1 as H1; B2 reported. |
| Primary metric (one) | Maximum drawdown difference vs L1. |
| Secondary metrics | After-tax CAGR; switches per decade; months of lag at each regime-split episode against L1's exit month; parameter drift across refits. |
| Pass threshold | None (exploratory). Finding recorded as "no worse than L1", "worse" or "better". "Better" (drawdown at least 3 points lower, CAGR not lower) permits a new promotable card at library N, nothing more. |
| Fail threshold | Not applicable. |
| Multiple-testing family and adjustment | Family A form, reported only. Strategy family `X1`. Scheduled refits are replications. |
| Trials consumed | 3 |

### H37 — Macro and valuation composite, "sin a little" (family X1, exploratory)

| Field | Content |
| --- | --- |
| ID / class | H37 / `exploratory` |
| Economic rationale | Before data: valuations and the cycle move expected returns at long horizons [C16]. Counter-rationale, which is the expectation: out-of-sample value is near zero [C14, C16, C17]; combinations do somewhat better than single predictors [C15]; Australian-specific signals have no evidence [C18]. |
| Assumptions | The signals' relation to subsequent returns has the same sign as in the published studies. |
| Exact rule | Three signals, each scored −1, 0 or +1 against its own expanding-window terciles using only values published by the evaluation date: (1) Australian 10-year minus 3-month government yield; (2) US BAA-minus-10-year credit spread, inverted; (3) the Australian index earnings yield minus the 10-year real yield. Composite = sum ÷ 3. Target equity weight of the 40/60 mix = 1.0 if composite ≥ 0; 0.9 if composite < 0. Monthly. No trend filter. |
| Fixed parameters | Three signals; terciles; expanding window from the first 10 years; tilt 10%. |
| Permitted perturbation grid | Tilt 20%; composite combined with L1 (L1 state AND tilt). Two neighbours. |
| Data and proxy map | RBA statistical tables; FRED; index-provider earnings yield. Point-in-time vintages where they exist; otherwise the signal is lagged 3 months and the card says so. History depth for (3) is [unverified]; under 25 years the signal is dropped and the composite uses two. |
| Benchmark | B2. |
| Primary metric (one) | After-tax CAGR difference vs B2 at A$100,000. |
| Secondary metrics | Maximum drawdown; maximum cumulative shortfall vs B2 (AQR reports −32% for value timing [C16]); trades suppressed at A$5,000 (expected: all); out-of-sample R² of each signal vs the historical mean. |
| Pass threshold | None (exploratory). Expectation: indistinguishable from zero. |
| Fail threshold | Audit trigger: uplift above +0.5 points a year. |
| Multiple-testing family and adjustment | Family B form, reported only. Strategy family `X1`. |
| Trials consumed | 3 |

### H38 — Sell in May (family X1, control)

| Field | Content |
| --- | --- |
| ID / class | H38 / `control` |
| Economic rationale | Before data: a documented seasonal that stopped working in five major indices after publication [C19]. No Australian evidence found. Registered as a calendar placebo: it uses no price information, so a large measured benefit in both halves is a warning about the sample or the harness. |
| Assumptions | None claimed. |
| Exact rule | Hold 40/60 from the last trading day of October to the last trading day of April; hold cash otherwise. |
| Fixed parameters | Months as stated. |
| Permitted perturbation grid | Window shifted one month later. One neighbour. |
| Data and proxy map | As H1. |
| Benchmark | B2. |
| Primary metric (one) | After-tax CAGR difference vs B2 at A$25,000. |
| Secondary metrics | Maximum drawdown; first vs second half of the sample; 2003 onward vs before; cost at A$5,000. |
| Pass threshold | None (control). |
| Fail threshold | Audit trigger: after-tax uplift above +0.5 points a year in both sample halves. |
| Multiple-testing family and adjustment | Reported only. Strategy family `X1`. |
| Trials consumed | 2 |

### H39 — Regularised ML summariser (family X1, exploratory, deferred)

| Field | Content |
| --- | --- |
| ID / class | H39 / `exploratory`. Not frozen until the library has 12 clean shadow months. LRN-30 applies. |
| Economic rationale | Before data: if the 13 ensemble signals carry unequal information, a regularised model might weight them better than equal weights. Counter-rationale, which is the expectation: with about 800 sleeve-months and six bear markets fitted weights are noise [C24, C25, C28]; selection among near-identical rules has not worked [C4, C5]; regularised linear models failed to beat a constant for index timing even with 30,000 stocks behind them [C21]. |
| Assumptions | Signal–return relations are stable across decades. |
| Exact rule | Features: H30's 13 signals per sleeve, pooled across both sleeves, plus trailing 3-month volatility. Target: next-month sleeve return minus cash. Model: ridge regression with penalty λ = number of features ÷ number of training months (no search). Expanding window from 1990-01, first fit after 15 years, refit each January with a 12-month embargo. Position: sleeve ON if predicted excess return > 0, with a one-month confirmation before any change. |
| Fixed parameters | Feature list; ridge; penalty rule; embargo; refit month. |
| Permitted perturbation grid | Gradient-boosted trees, depth 2, 100 trees, learning rate 0.05 (fixed); features without the volatility term. Two neighbours. |
| Data and proxy map | As H30. Every fitted model object hashed and stored. |
| Benchmark | H30. B2 and L1 reported. |
| Primary metric (one) | Maximum drawdown difference vs H30. |
| Secondary metrics | After-tax CAGR vs H30; switches per decade; coefficient stability across refits; share of months disagreeing with H30. |
| Pass threshold | None (exploratory). "Better" = drawdown at least 3 points lower than H30, CAGR not lower, switches no more than 25% higher; this permits a new promotable card under Family B at library N. |
| Fail threshold | Not applicable. |
| Multiple-testing family and adjustment | Reported only. Strategy family `X1`. Scheduled refits are replications. |
| Trials consumed | 3 |

### H40 — Equal-weight blend of passed rules (family META, promotable)

| Field | Content |
| --- | --- |
| ID / class | H40 / `promotable` |
| Economic rationale | Before data: averaging rules reduces the error of any one, and equal weights beat fitted ones [C3, C15, C28]. Counter-rationale: the passed rules are highly correlated trend rules, so the gain may be nil; blending makes smaller orders. |
| Assumptions | Member rules remain individually valid. |
| Exact rule | Target weight per sleeve = the simple mean of the target weights of the champion and of every `promotable` card with result "passed" on the same sleeves. Orders under PRT-16 and PRT-17. Evaluated only where every implied order is ≥ `min_order_value_aud` at that NAV. |
| Fixed parameters | Equal weights; membership fixed at this card's freeze (list of card IDs). |
| Permitted perturbation grid | Leave-one-out of the membership (reported, counted once). One neighbour. |
| Data and proxy map | As the member cards. |
| Benchmark | The champion alone. |
| Primary metric (one) | Specification dispersion as in H30, blend vs champion. |
| Secondary metrics | Maximum drawdown; tracking error to B2; orders suppressed by the minimum at each NAV; after-tax CAGR. |
| Pass threshold | Dispersion at least 20% lower; drawdown no more than 2 points worse; after-tax CAGR within −0.3 points. |
| Fail threshold | No dispersion reduction, or more than half of orders suppressed at the account's NAV. |
| Multiple-testing family and adjustment | Family A, design choice. Strategy family `META`. |
| Trials consumed | 2 |

### H41 — Negative control on the selection process (family META, control)

| Field | Content |
| --- | --- |
| ID / class | H41 / `control` |
| Economic rationale | Before data: picking last year's best rule is the natural temptation and the evidence says it does not work [C4, C5, C24]. This card measures it on the library itself. It protects LRN-04 the way H2 protects PRT-25. |
| Assumptions | None claimed. |
| Exact rule | Each January, over the backtest, hold for the next 12 months the library rule (among all `promotable` and `control` cards on the VAS/VGS sleeves) with the highest trailing 12-month return. Compare with holding the champion throughout. |
| Fixed parameters | 12-month selection window; annual switch. |
| Permitted perturbation grid | None. |
| Data and proxy map | The backtest return series of the member cards. |
| Benchmark | The champion held throughout. |
| Primary metric (one) | After-tax CAGR difference, chase-the-winner minus champion. |
| Secondary metrics | Maximum drawdown; number of switches; the same with a 36-month window (reported, not a trial). |
| Pass threshold | The control "holds" if the difference is ≤ +0.5 points a year. |
| Fail threshold | Above +0.5: audit for leakage first. If no defect is found, record "passed after audit"; LRN-04 is not relaxed, and a promotable selection rule would need its own Family B card. |
| Multiple-testing family and adjustment | Reported only. Strategy family `META`. |
| Trials consumed | 1 |

### H42 — Contribution-only trend overlay (family L2, promotable)

| Field | Content |
| --- | --- |
| ID / class | H42 / `promotable` |
| Economic rationale | Before data: for an account that grows by regular deposits, steering new money by the trend state gives part of a trend filter's protection with no sale, no extra commission, no CGT event and no reset of holding periods. Counter-rationale: investing on arrival beats waiting about two-thirds of the time (R33 §2.10); held-back cash earns little; it protects only new money, so the effect fades as NAV grows. No direct literature [unverified]. |
| Assumptions | Contributions continue at the planned rate (open item O7); the trend state has the same information as in H1. |
| Exact rule | Sleeves and base weights as section 9.1. Trend state per sleeve from PRT-12 and PRT-13 exactly. No sell order is ever planned for trend reasons. Contributions and distributions are directed (PRT-16(b)) to the most underweight sleeve whose state is ON; if no sleeve is ON they stay as cash (or AAA if HG1 is adopted). When a sleeve turns ON, accumulated cash is deployed to underweight ON sleeves at the next execution date, subject to PRT-17. The ±20% band rebalance (PRT-16(c)) is suspended for a sleeve that is OFF. |
| Fixed parameters | L1's votes and hysteresis; contribution schedule A$500 a month and, separately, A$1,000 every two months, from a A$5,000 start. |
| Permitted perturbation grid | Votes replaced by H30's score; deploy accumulated cash over three evaluations instead of one. Two neighbours. |
| Data and proxy map | As H1, with the contribution schedule applied from each of the 12 start months. |
| Benchmark | STATIC (B2) with the same contributions invested on arrival. L1 with the same contributions is reported. |
| Primary metric (one) | Maximum drawdown of the money-weighted unit value, difference vs STATIC, over each rolling 10-year window starting at A$5,000. |
| Secondary metrics | After-tax terminal wealth vs STATIC and vs L1 at 10 and 20 years; tax paid; commission paid; share of NAV in cash at each regime-split trough; the NAV at which the drawdown benefit falls below 1 point. |
| Pass threshold | Median drawdown reduction across windows at least 15% relative; after-tax terminal wealth at 10 years no more than 1% below STATIC and not below L1; passes H12. |
| Fail threshold | No drawdown reduction, or terminal wealth more than 3% below STATIC at 10 years. |
| Multiple-testing family and adjustment | Family A; Holm family of its window. Strategy family `L2`. |
| Trials consumed | 3 |

### H43 — Managed-futures sleeve (family S3, promotable at Stage 3 only)

| Field | Content |
| --- | --- |
| ID / class | H43 / `promotable`, but only for an account that meets every Stage 3 condition (section 27) and USE-02. |
| Economic rationale | Before data: breadth is the main driver of trend returns (R14 finding 4), a two-sleeve account has none, and managed-futures funds are diversified time-series momentum [C32]. A 10% sleeve adds a return source with low correlation to equities and a record of gains in slow bear markets. Counter-rationale: realised net Sharpe is far below paper (R14 finding 5); the funds lost in the 2024–25 whipsaw; ETF records are short; fees, FX, US-situs and Division 775 costs apply; no ASX-listed fund was found [unverified]. |
| Assumptions | The fund continues to track a diversified trend programme; US venue costs as ENG-04. |
| Exact rule | 36% VAS, 54% VGS, 10% a US-listed managed-futures ETF named in the card at freeze (the largest by assets with at least five years of history on the freeze date). Static weights, ±20% relative band, no trend filter on the sleeve. L1's filter, if live, applies to VAS and VGS only. |
| Fixed parameters | 10% sleeve; band; instrument fixed at freeze. |
| Permitted perturbation grid | Sleeve 20%. One neighbour. |
| Data and proxy map | Before the ETF's inception: the SG Trend Index or an equivalent published trend index, net of the ETF's fee, in AUD, if licensable; otherwise "short sample" and reported only. |
| Benchmark | B2 (or the champion on VAS and VGS). |
| Primary metric (one) | Maximum drawdown difference vs the benchmark at A$100,000. |
| Secondary metrics | After-tax CAGR including FX conversion costs and US withholding; 2022 row; 2024–25 row; correlation of the sleeve with the benchmark in equity drawdowns; added record-keeping cost. |
| Pass threshold | Maximum drawdown at least 2 points lower; after-tax CAGR no more than 0.3 points lower; holds in at least 3 of 4 regime splits; passes H12. |
| Fail threshold | No drawdown improvement, or CAGR more than 0.75 points lower. |
| Multiple-testing family and adjustment | Family A. Strategy family `S3`, own holdout opening under LRN-25. |
| Trials consumed | 2 |

---

## 7. Roadmap by account size

| Sizing NAV | Live rule | Learning layer | Shadow library | Decision gates |
| --- | --- | --- | --- | --- |
| **A$5,000** (now) | L1 or STATIC per G2 and the owner's objective (R33 §2.2). Two sleeves. | All of §4 on from go-live: bounded estimates, monitors D1–D8, per-fill record, quarterly report. Expect 8–20 fills a year, so cost estimates move slowly. | Twelve active challengers on monthly proxies and ETF data: STATIC, L1, H30–H38, H42 (H40 and H41 are computed from them). The one paid EODHD month must include the library symbols. | G0: freeze H30–H38, H40–H42. No promotion before 12 shadow cycles. |
| **A$10,000–15,000** | Unchanged. Tranche threshold as R33 §2.7 decides. | First yearly review: battery re-run, library PBO, assumption flags. | First research cycle may add up to 4 cards. | First promotion window. Realistic candidates: H30 (binary), H42, R33's HG cards. |
| **A$15,000–25,000** | Stage 2 if the owner chooses it: P1 with four sleeves at A$15k, six at A$20k (NAV ÷ 2,500). Otherwise unchanged. | Volatility, correlation and multiplier estimates start to affect sizes (SIZ-01 on). | H33, H32, H34 also reported at the account's real size. | H6, H12, H13 (existing). |
| **A$25,000–50,000** | Graded wide ensemble (thirds) if H30 and H9 passed. Up to ten P1 sleeves. Stage 3 may open: H43 becomes a candidate. | RSK-26 switches to cost as a share of NAV; the cost CUSUM (D2) has enough fills to mean something. | H39 starts after 12 clean library months. H43 in shadow needs one US symbol. | Second or third window. |
| **A$50,000–100,000** | Unchanged unless a card passed. A rotation satellite of at most 20% may be *proposed* only if H32 passed Family B; expect that it will not. | `min_tax` parcel logic (R33) matters more than any signal here. | Paid data plan is under 0.5% of NAV; the cap can rise to 24 challengers. | — |
| **A$100,000+** | §26 continuous forecasts with 10% buffers for P1 (steps of about A$1,600 on a 16% sleeve [computed]); downward-only volatility cap (SIZ-11). H40's equal-weight blend becomes implementable. | H42's benefit has faded [computed]; it should be retired here unless the card shows otherwise. | Continues. | A new card for the continuous engine. |

At no size does the roadmap add an algorithm because the account grew. Size removes the order-size obstacle; the evidence gate stays the same.

---

## 8. Reasons this could be wrong, and open items

1. **Many sources were read as abstracts or extracts** (§0.3). Every [2+] direction rests on more than one of them, but individual numbers in C3, C5, C10, C12, C17, C20, C22, C29 and C33 should be re-checked before the spec quotes them.
2. **GEM's post-publication record rests on hobbyist backtests** measured against the S&P 500 in its strongest decade; against a global benchmark the shortfall is smaller. The rejection does not depend on its size: cost and tax arithmetic decide it at this account size.
3. **No Australian evidence** was found for seasonality, macro timing, regime models or contribution-timed investing. Absence in a few searches is not evidence of absence. The cards exist to produce it.
4. **H42 is my own design with no literature behind it.** It is listed fourth because its costs are near zero and its logic follows from R33's findings, not because it is proven. It could simply fail its card.
5. **The CUSUM and luck-band figures are simulations under normal, independent monthly values.** Real differences are fat-tailed and autocorrelated, so false alarms will be more frequent than stated. LRN-34(v) pins the figures for the test only; the first two years of live data should be used to check the standardisation, not to tune the limits.
6. **Bounded learning is still learning from a small sample.** With 8–20 fills a year the spread and slippage estimates will sit near their priors for years. That is intended, but it means the "what changed by itself" section will often be nearly empty. The report says so in its limits paragraph.
7. **Forty-six more trials raise the DSR hurdle for everything**, including any future honest return claim. If the owner prefers a lower hurdle, drop the exploratory family (H36–H39) and H43: 33 trials.
8. **A library can become a temptation machine.** LRN-04, LRN-27 and LRN-31 are the mitigations. If the owner finds himself wanting to override them, the evidence-based response is report 33's: run STATIC live and keep the library for interest.
9. **Proxy availability** for emerging markets, small caps, bonds, gold and a trend index from 1990 in AUD is unverified. H32, H33, H34 and H43 may be "not testable" on the history that can be licensed.
10. **Free-plan ASX coverage at EODHD is still unverified** (E1). If it fails, DAT-24's budget is moot and the fixed-cost tables in R13 and R33 change by US$19.99 a month.
11. **Interaction with reports 33 and 34.** R33's objective decision sits above this report: if the live account is STATIC, H30 challenges a rule that is itself in paper, and H42 becomes the most relevant live candidate. H34 depends on HG1. Report 34 was not available to read.
12. **The proposer-exposure rule (LRN-23) weakens every card in this report**, by design. It means none of them can be confirmed on the existing holdout alone; each needs time. That is a cost of having AI agents draft research, and the spec should state it.

---

## 9. Sources

| # | Source | How read |
| --- | --- | --- |
| S1 | Carver, ["A simple breakout trading rule"](https://qoppac.blogspot.com/2016/05/a-simple-breakout-trading-rule.html) (2016), including the forecast-correlation matrix and comments | Primary |
| S2 | Levine & Pedersen (2016), "Which Trend Is Your Friend?", FAJ 72(3). [CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2016/which-trend-is-your-friend); [CXO summary](https://www.cxoadvisory.com/technical-trading/trend-indicator-similarities) | Extracts |
| S3 | ReSolve, ["Global Equity Momentum: A Craftsman's Perspective"](https://www.advisorperspectives.com/articles/2019/05/06/global-equity-momentum-a-craftsmans-perspective) (2019) | Extracts; host refused |
| S4 | Newfound Research, ["Fragility Case Study: Dual Momentum GEM"](https://blog.thinknewfound.com/tag/gem/) (2019) | Extracts; host refused |
| S5 | Newfound Research, ["Timing Trend Model Specification with Momentum"](https://blog.thinknewfound.com/2019/12/timing-trend-model-specification-with-momentum/) (2019) | Extract |
| S6 | Bajgrowicz & Scaillet (2012), JFE 106(3). [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:106:y:2012:i:3:p:473-491) | Abstract |
| S7 | AlgoStrategyLab, [dual-momentum repository](https://github.com/AlgoStrategyLab/dual-momentum) (backtest May 1997–Oct 2026) | Primary page |
| S8 | Quant for Free, ["Dual Momentum out of sample"](https://quant4free.com/analysis/dual-momentum/) | Extract; host refused |
| S9 | Reblnc, ["Dual Momentum Explained"](https://reblnc.com/insights/dual-momentum) | Extract |
| S10 | CXO Advisory, ["A Few Notes on Dual Momentum Investing"](https://www.cxoadvisory.com/momentum-investing/a-few-notes-on-dual-momentum-investing) | Primary |
| S11 | CXO Advisory on Keller & Keuning: [VAA](https://www.cxoadvisory.com/?p=30082), [DAA](https://www.cxoadvisory.com/?p=31391); papers at [SSRN 3002624](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3002624), [SSRN 3212862](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3212862) | CXO primary; SSRN refused |
| S12 | CXO Advisory, [SACEMS strategy page](https://www.cxoadvisory.com/momentum-strategy) and [robustness tests](https://www.cxoadvisory.com/momentum-investing/simple-asset-class-etf-momentum-strategy-robustnesssensitivity-tests/) | Primary |
| S13 | Allocate Smartly: ["The Underperformer Watchlist"](https://allocatesmartly.com/new-feature-the-underperformer-watchlist/); ["Does the Day of the Month Matter?"](https://allocatesmartly.com/diving-deeper-does-the-day-of-the-month-matter/) | Extracts; host refused |
| S14 | Bloomberg, ["Risk-Parity Strategy Disappoints as ETF Posts Record 32% Drop"](https://www.bloomberg.com/news/articles/2022-09-28/-perfect-storm-for-risk-parity-has-etf-posting-record-32-drop); [PortfoliosLab RPAR](https://portfolioslab.com/symbol/RPAR) | Extracts |
| S15 | Angel Investors Network, ["Risk Parity Explained"](https://angelinvestorsnetwork.com/market-analysis/risk-parity-hedge-fund-strategy-bridgewater-all-weather) | Extract; low reliability |
| S16 | Ang & Timmermann, "Regime Changes and Financial Markets", [NBER w17182](https://www.nber.org/system/files/working_papers/w17182/w17182.pdf) | Primary |
| S17 | Dacco & Satchell (1999), J. Forecasting 18(1). [Record](https://iaorifors.com/paper/30956) | Abstract |
| S18 | Bulla et al. (2011), J. Asset Management 12(5). [IDEAS, MPRA 21154](https://ideas.repec.org/p/pra/mprapa/21154.html) | Abstract |
| S19 | Shu, Yu & Mulvey (2024), ["Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach"](https://arxiv.org/abs/2402.05272) | Primary |
| S20 | Goyal & Welch, [NBER w10483](https://www.nber.org/system/files/working_papers/w10483/w10483.pdf) (published RFS 2008) | Primary |
| S21 | Goyal, Welch & Zafirov (2024), RFS 37(11). [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:37:y:2024:i:11:p:3490-3557.) | Abstract |
| S22 | Rapach, Strauss & Zhou (2010), RFS 23(2). [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:23:y:2010:i:2:p:821-862) | Abstract |
| S23 | Dou, Gallagher, Schneider & Walter (2012), Aust. J. Management 37(3). [IDEAS](https://ideas.repec.org/a/sae/ausman/v37y2012i3p461-479.html) | Abstract (primary page) |
| S24 | Forecast combination puzzle: Qian, Rolling, Cheng & Yang (2019), [Econometrics 7(3)](https://econpapers.repec.org/RePEc:gam:jecnmx:v:7:y:2019:i:3:p:39-:d:265946); [UMN record](https://experts.umn.edu/en/publications/on-the-forecast-combination-puzzle/) | Extracts |
| S25 | Asness, Ilmanen & Maloney (2017), ["Market Timing: Sin a Little"](https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Market-Timing-Sin-a-Little.pdf), JOIM 15(3), Tables 2, 5, 6 | Primary |
| S26 | Fama & French (2019), "Inverted Yield Curves and Expected Stock Returns". [Carlson](https://awealthofcommonsense.com/2019/08/you-probably-cant-use-the-yield-curve-to-time-the-market/); [Fortune](https://fortune.com/2019/08/13/recession-benchmark-timing-stock-market/) | Extracts; paper host refused |
| S27 | Chen, Rogoff & Rossi, [NBER w13901](https://www.nber.org/system/files/working_papers/w13901/w13901.pdf) (QJE 2010) | Abstract (PDF fetched) |
| S28 | Zhang & Jacobsen (2021), JIMF. [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0261560620302242) | Abstract; versions differ on market counts |
| S29 | CXO Advisory, ["Halloween Indicator Out-of-Sample Test"](https://www.cxoadvisory.com/calendar-effects/halloween-indicator-out-of-sample-test) (Dichtl & Drobetz); [EconPapers record](https://econpapers.repec.org/RePEc:eee:finlet:v:11:y:2014:i:2:p:112-121) | CXO primary |
| S30 | Sullivan, Timmermann & White (2001), J. Econometrics 105. [LSE record](https://researchonline.lse.ac.uk/id/eprint/119142) | Abstract |
| S31 | Chen, Shin & Sun (2023), ["Return-enhancing strategies with international ETFs"](https://openjournals.libs.uga.edu/fsr/article/view/3338), citing McConnell & Xu (2008); CXO, ["Survey of Seasonal Anomalies"](https://www.cxoadvisory.com/calendar-effects/survey-of-seasonal-anomalies/) | Extract; CXO primary |
| S32 | Gu, Kelly & Xiu, [NBER w25398](https://www.nber.org/system/files/working_papers/w25398/w25398.pdf) (RFS 2020) | Primary |
| S33 | Avramov, Cheng & Metzker (2023), Management Science 69(5). [EconPapers](https://econpapers.repec.org/RePEc:inm:ormnsc:v:69:y:2023:i:5:p:2587-2619) | Abstract |
| S34 | Nagel (2025), ["Seemingly Virtuous Complexity in Return Prediction"](https://www.nber.org/papers/w34104), NBER w34104; Kelly, Malamud & Zhou, [NBER w30217](https://www.nber.org/system/files/working_papers/w30217/w30217.pdf) | Abstract; KMZ PDF fetched |
| S35 | Wiecki, Campbell, Lent & Stauth (2016). [Quantpedia, abstract and conclusions](https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/); [CXO](https://www.cxoadvisory.com/big-ideas/in-sample-vs-out-of-sample-performance-of-888-trading-strategies) | Primary pages |
| S36 | Suhonen, Lennkh & Perez (2017), JPM. [CXO](https://www.cxoadvisory.com/big-ideas/live-performance-of-alternative-beta-products/) | CXO primary |
| S37 | Falck, Rej & Thesmar (2021), ["Why and how systematic strategies decay"](https://arxiv.org/abs/2105.01380) | Primary |
| S38 | Harvey & Liu, "Backtesting". [CXO](https://www.cxoadvisory.com/?p=24128) | CXO primary |
| S39 | Arnott, Harvey & Markowitz (2018), ["A Backtesting Protocol in the Era of Machine Learning"](https://papers.ssrn.com/abstract=3275654); López de Prado (2018), [Quantpedia note](https://quantpedia.com/why-machine-learning-funds-fail/) | Abstracts |
| S40 | Bailey, Borwein, López de Prado & Zhu, ["The Probability of Backtest Overfitting"](https://papers.ssrn.com/abstract=2326253); Bailey & López de Prado, "The Sharpe Ratio Efficient Frontier", [J. Risk](https://risk.net/node/2223785); [formula notes](https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/) | Abstracts, extract |
| S41 | DeMiguel, Garlappi & Uppal (2009), RFS 22(5). [EconPapers](https://econpapers.repec.org/RePEc:oup:rfinst:v:22:y:2009:i:5:p:1915-1953) | Abstract, extract |
| S42 | Philips, Yashchin & Stein (2003), JPM. [IBM Research abstract](https://researcher.watson.ibm.com/publications/using-statistical-process-control-to-monitor-active-managers); [cusumActMgr documentation](https://rdrr.io/github/kecoli/PCRM/man/cusumActMgr.html) | Extracts |
| S43 | Frazzini, Israel & Moskowitz (2018), ["Trading Costs"](https://papers.ssrn.com/abstract=3229719); [Swedroe summary](https://www.etf.com/sections/index-investor-corner/swedroe-trading-cost-truths) | Abstract, extract |
| S44 | Glasserman & Lin, [arXiv 2309.17322](https://arxiv.org/abs/2309.17322); Li et al., [arXiv 2605.24564](https://arxiv.org/abs/2605.24564); position paper, [arXiv 2602.14233](https://arxiv.org/abs/2602.14233) | Abstracts (primary pages) |
| S45 | Hurst, Ooi & Pedersen (2013), ["Demystifying Managed Futures"](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Demystifying-Managed-Futures.pdf), JOIM 11(3) | Primary (abstract and introduction) |
| S46 | Managed-futures ETF landscape: [HedgeNordic (2026)](https://hedgenordic.com/2026/04/muddling-through-the-mess-managed-futures-etfs/); [Quantseeker](https://www.quantseeker.com/p/managed-futures-etfs-what-the-data) | Extracts |
| S47 | CPPI: [Carvalho, Gaspar & Sousa (2016)](https://ecomod.net/system/files/Carvalho_Gaspar_Sousa_2016_draft.pdf); ["How does CPPI perform against the simplest guarantee strategies?"](https://core.ac.uk/works/8725368) | Extracts |
| S48 | EODHD, ["API Limits: Daily Calls, Rate Limits and Costs"](https://eodhd.com/financial-apis/api-limits) | Primary |
| S49 | ASX ETF fee aggregators: [ReviewETF](https://www.reviewetf.com.au/blog/low-cost-etfs-on-the-asx-the-smart-way-to-keep-more-of-your-returns-in-2026); [Finder](https://www.finder.com.au/20-cheapest-etfs-on-the-asx); [Motley Fool AU](https://www.fool.com.au/2026/05/23/these-are-the-cheapest-asx-etfs-on-the-australian-market/) | Extracts |
| — | Own computations: `scratchpad/tools/cusum.py` (CUSUM run lengths, minimum track record length, expected maximum of N normals), seed fixed | Computed |
