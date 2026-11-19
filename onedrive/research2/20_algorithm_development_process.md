# Wave 3: R&D process from evidence to algorithm (2026-11-13)

**Evidence caveat.** This session's network policy blocked most primary hosts (federalreserve.gov, ssrn.com, duke.edu, twosigma.com, morningstar.com, vanguard, ato.gov.au, davidhbailey.com). Quotes marked † were fetched and read directly; the rest come from search-result extracts and are tagged down accordingly. To upgrade the [1] and [unverified] items, allow those hosts and re-run.

Tags: **[2+]** two independent sources, **[1]** one source or search extract only, **[unverified]** my inference or design choice. All thresholds in sections 2–4 are my proposed design values, not sourced facts.

## 1. How professional shops run research to production, adapted for one person

| Practice | Evidence | Tag | One-person + AI-agent adaptation |
|---|---|---|---|
| Research as a factory, not a lone hunt | López de Prado: "Every successful quantitative firm I am aware of applies the meta-strategy paradigm. Your firm must set up a research factory where tasks of the assembly line are clearly divided into subtasks, where quality is independently measured and monitored for each subtask"† (quantpedia.com/why-machine-learning-funds-fail; same text reported in the GARP/SSRN paper) | [2+] | Fixed pipeline stages (data → signal → portfolio → cost/tax → report), each with its own tests. Agents staff stations; the owner is the only approver. |
| Count every trial | Harvey–Liu (Man Institute): "A common practice in evaluating backtests of trading strategies is to discount the reported Sharpe ratios by 50%… The 50% haircut is only a rule of thumb… the multiple testing haircut is nonlinear… The marginal Sharpe ratio strategies should be thrown out."† (man.com/insights/backtesting). LdP pitfall #7: use "The Deflated Sharpe Ratio… controlling for the inflationary effect of multiple trials"† | [2+] | Append-only trial log; every backtest run is recorded automatically by the harness. |
| Higher significance hurdle | Harvey–Liu–Zhu: "a newly discovered factor needs to clear a much higher hurdle, with a t-ratio greater than 3.0… most claimed research findings in financial economics are likely false."† (nber.org/papers/w20592) | [1] primary | t ≥ 3.0 for any return-enhancement claim. |
| Protocol and culture | Arnott–Harvey–Markowitz seven-element protocol: economic foundation first, "keep track of what is tried", reward method not results; "false strategies can survive simple cross-validation"† (cxoadvisory.com summary; SSRN 3275654 via search) | [2+] | Hypothesis must have an ex-ante rationale and be registered before data is touched. |
| Enforced holdout | QuantConnect lets managers "enforce all backtests must end a certain number of months before the current date"†. Bailey et al. argue plain hold-out "tend[s] to be unreliable" for backtests and propose CSCV/PBO (search extract; wording varies by version) | [1] each | Harness hard-locks the holdout; add start-date dispersion and bootstrap rather than relying on one split. |
| Seed capital before client capital | Risk.net correction: Man AHL "preliminarily tests its models with seed capital earmarked for researching new algorithms, rather than shareholders' money" (search extract) | [1] | A$5k live is the seed stage; scale only via promotion gates. |
| AI assists, humans evaluate | Man Group on off-the-shelf LLM output: "fails to adhere to standard best practice for research, such as in-sample/out-of-sample testing protocols… no knowledge of the firm's specific execution assumptions, including trading costs and slippage models"†; the assistant "is by no means a replacement for the human researcher"† (man.com/insights/ai-agents-trend) | [1] primary | Agents may research, code and test. They may never approve a spec, promote a variant or originate an order. |
| Falsification culture | Two Sigma defines a failure as "a well-designed experiment that disproves a hypothesis under sound test conditions" (search extract) | [1] | Failed hypotheses stay in the registry as results. |
| Model risk management | SR 11-7 (2011) was **superseded by SR 26-2 on 17 April 2026** (Fed/OCC/FDIC; reported by Orrick, EY, KPMG and the Fed page in search). Effective challenge is retained, now framed as expertise plus independence; the guidance is non-binding and risk-proportionate. | [2+] on supersession; exact wording [unverified] | Borrow the principles: model inventory, independent validation, ongoing monitoring, outcomes analysis, change control. Cite "SR 26-2 (superseding SR 11-7)" in the spec. |

Whether SR 26-2 excludes generative/agentic AI is contested across secondary sources [1]. It is not binding on a private investor either way.

**Stage gates for the one-person shop** [unverified design]:

| Gate | Owner of work | Exit criterion | Approver |
|---|---|---|---|
| G0 Register | Agent drafts, owner edits | Hypothesis card frozen and hashed before any run | Owner |
| G1 Build | Agent A (code + tests) | Unit and golden-file tests pass; harness reproduces a known benchmark within 1 bp/month | CI |
| G2 Validate | Agent B, fresh context, re-implements the signal from the spec only | Two implementations agree; robustness battery run; validation memo lists weaknesses | Owner |
| G3 Paper | System | Section 4 criteria | Owner |
| G4 Live seed | System | Section 4 criteria | Owner, plus second user once multi-user |
| G5 Monitor | System | Monthly pack; triggers | Owner |

Effective challenge for one person means an independent validator agent with no access to the builder's code, a mandatory 7-day cooling-off between seeing results and approving, and a written "reasons this could be wrong" section.

## 2. Hypothesis registry

**Card template (RND-010):**
`ID | date registered | spec hash | economic rationale | exact rule | fixed parameters | permitted perturbation grid | data + proxy map | sample / holdout dates | benchmark | primary metric (one) | secondary metrics | pass/fail thresholds | multiple-testing family and adjustment | trials consumed | result | decision | approver`

**Shared settings.**
- Data: monthly total-return index proxies 1990-01 to 2023-12 for development. 2024-01 onward is a locked holdout, opened once.
- Costs and tax: the section 3 model.
- Benchmarks: B1 = DHHF buy-and-hold (proxied); B2 = static 40% VAS / 60% VGS.

**Multiple-testing rule (RND-012).**
- Two families: Family A is drawdown/risk claims, Family B is return claims.
- Holm step-down at family α = 0.10 for A, using stationary-bootstrap p-values on the paired difference.
- For B, require t ≥ 3.0 and Deflated Sharpe ≥ 0.95 using N = all logged trials.
- Any un-registered run increments N.

The limit of this design: 34 years gives t ≈ SR-difference × √34, so t = 3 needs a Sharpe difference of about 0.51 (my arithmetic from the standard approximation t ≈ SR·√T). Almost no overlay will clear it. This is why the registry treats trend as a drawdown overlay and judges it on non-inferiority of return plus superiority on drawdown.

| ID | Rule under test | Fixed parameters | Benchmark | Primary metric → pass | Fail / kill |
|---|---|---|---|---|---|
| H1 | 3-vote trend filter on 40/60 reduces drawdown | Votes: price > 10-month SMA; 12-month return > cash; blend of 4/8/12-month MAs. Risk-off at ≤1 vote, back on at ≥2. Monthly, 3 tranches. | B2 | Max drawdown reduced ≥ 25% relative and Ulcer index lower, Holm-adjusted p < 0.10 | Max drawdown reduction < 10%, or after-tax CAGR cost > 1.5 pp |
| H2 | Trend is not a return source (negative control) | As H1 | B2 | After-tax CAGR difference within −1.5 to +0.5 pp | Above +1 pp triggers a bug/look-ahead audit, not celebration |
| H3 | Blended votes beat a single 10-month SMA | H1 vs SMA-only | SMA-only | Start-date/tranche CAGR dispersion ≥ 30% lower; switches per decade ≥ 25% fewer | No reduction → use the simpler SMA |
| H4 | Hysteresis and no-trade bands cut turnover | Band ±20% relative weight; min trade A$1,000 | H1 without bands | Turnover −30% with max drawdown worsening ≤ 2 pp | Drawdown worsens > 4 pp |
| H5 | Tranching cuts rebalance timing luck | N = 1, 3, 4 tranches | N = 1 | Std dev of 12-month returns across offsets falls roughly 1/N | No fall, or added cost exceeds benefit at A$5k |
| H6 | Diversification helps (V0 → 6–10 sleeves) | Sleeves and class risk budgets fixed ex ante | B2 | Sharpe non-inferior (difference ≥ −0.05) and max drawdown lower, in ≥ 3 of 4 regime splits | Worse in 2022-type regime and overall |
| H7 | Inverse-vol within class vs equal weight | 12-month vol, monthly | Equal weight | Realised vol lower, Sharpe non-inferior | Turnover cost exceeds benefit |
| H8 | Monthly evaluation is sufficient | Monthly vs weekly check | Monthly | Weekly shows no net-of-cost drawdown improvement ≥ 2 pp | If weekly passes, register a new hypothesis; do not switch |
| H9 | Graded vs binary states | 0/50/100% vs 0/100% | Binary | Graded lowers tracking error to B2 without worse drawdown | — |
| H10 | Overlay survives small-scale costs | A$5k, A$50k, A$250k | B1 | Cost drag ≤ 0.5%/yr at A$50k; reported at A$5k | At A$5k, if drag > 1%/yr, the live rule stays "seed/learning" and no performance claim is made |
| H11 | Overlay survives tax | Marginal 30%, 37%, 45% + Medicare; both CGT regimes | B2 after tax | After-tax terminal wealth ≥ 90% of B2 with max drawdown −25% | Below 85% |
| H12 | Survives the haircut | Halve every measured benefit, double costs, one-month delay | — | H1 and H6 still pass | Fail → demote to paper-only |

Map V0–V4 to these cards exactly as already pre-registered. I did not have the variant definitions, so that mapping is unconfirmed.

The halving in H12 follows the brief's decided "~halve post-publication" rule. I could not re-verify McLean–Pontiff's exact figures this session: the 26%/58% abstract numbers are [unverified], and search extracts only showed "about 35%" from the working-paper version [1].

## 3. Backtest harness requirements

**Engine (RND-020).** Use an event-driven daily loop as the system of record, sharing signal, portfolio and order-sizing code with the live system. Add a vectorised twin for fast sweeps, and reconcile the two.
- Vectorised code is prone to shift/off-by-one look-ahead, while an event-driven backtester "can be used for both historical backtesting and live trading with minimal switch-out of components" (QuantStart and IBKR Campus via search) [2+, extracts].
- That monthly rules do not need event-driven speed but do need its lot-level cash/tax state is my inference [unverified].

**Cost model (RND-021).** IBKR Australia, fetched†: Fixed "0.08% of Trade Value", "Minimum per order… AUD 6.00" excluding GST (example: A$16.00 ex / A$17.60 inc GST); Tiered Tier I 0.08% with A$5.00 minimum plus exchange fees [1 primary].

| Account | Typical trade | Commission (fixed, inc GST) | Round-trip incl. assumed 5 bp half-spread |
|---|---|---|---|
| A$5k | A$1,000 | A$6.60 = 0.66% | about 1.4% |
| A$50k | A$5,000 | A$6.60 = 0.13% | about 0.36% |
| A$250k | A$25,000 | A$22 = 0.088% | about 0.28% |

These are my arithmetic. The percentage rate takes over from the minimum at A$7,500 per order. The model must also include a per-ETF spread table, MER, FX where relevant, whole-share rounding and cash drag.

**Tax model (RND-022).**
- Parcel-level lots, selectable parcel method, distributions and franking, loss carry-forward, and tax paid from the portfolio at 30 June.
- Current rule: a 50% discount for individuals if "you owned the asset for at least 12 months", excluding acquisition and disposal days (ATO via search) [1].
- **New finding:** the 2026–27 Budget proposes replacing the 50% discount with cost-base indexation plus a 30% minimum tax on real gains accruing from 1 July 2027 (ATO reform page, PwC, BDO, KWM, Hall & Wilcox via search) [2+]. Whether it has passed Parliament is [unverified].
- The harness therefore needs a tax-regime switch, and H11 must run under both regimes.

**Tranching (RND-023).** Simulate N sub-portfolios with staggered dates and all 12 or 21 offsets. Hoffstein reports a 60/40 rebalanced annually shows 0.36% standard deviation in 12-month returns across month offsets, and N tranches cut timing luck by about 1/N (CXO summary and Newfound abstract via search) [2+, extracts].

**Proxies from 1990 (RND-024).**
- Map each ETF to a total-return index minus MER (for example S&P/ASX 300 TR, MSCI World ex-Australia NR in AUD, a Bloomberg AusBond composite, a hedged global aggregate, gold in AUD, a bank-bill cash rate).
- Splice to the live ETF at inception and report the splice tracking error.
- Flag proxy-era results separately.
- The specific index choices are mine and unverified.

**Validation design (RND-025).**
- Development sample 1990–2023; locked holdout 2024-01 to the present, which includes April 2025.
- No parameters are fitted. The walk-forward is anchored and used only for inverse-vol estimates.
- Report CSCV/PBO across the perturbation grid.

**Robustness battery (RND-026):**

| Test | Specification | Pass |
|---|---|---|
| Parameter perturbation | ±25% on every lookback; alternative vote sets | ≥ 80% of neighbours pass H1; no cliff edges |
| Start-date / tranche dispersion | All monthly starts × all offsets | 5th-percentile outcome still passes |
| Cost doubling | 2× commission and spread | H10 holds at A$50k |
| One-period delay | Signal at t, trade at t+1 month (also t+1 day) | Drawdown benefit retained ≥ 70% |
| Block bootstrap | Stationary bootstrap, mean block 6–12 months, 10,000 paths, paired with benchmark | 90% CI on drawdown difference excludes 0 |
| Regime splits | 2000–02, 2008–09, 2020 Q1, 2022, Feb–Apr 2025, plus one whipsaw period (2015–16) | Reported individually; must not rely on 2008 alone |
| Placebo | Randomised signal dates with matched time-in-market | Real rule beats the 90th percentile of placebos on drawdown |

On April 2025: the S&P 500 fell about 17.7% on closes from 19 February to 7 April, about 21% intraday, and the ASX 200 fell 4.2% on 7 April (Betashares timeline and Reuters via search) [1]. A V-shaped fall this fast is exactly where monthly trend rules sell late and re-buy higher, so it is a required adverse case.

**Reporting pack (RND-027).** One auto-generated document per run containing:
- spec hash, data hash and trial count N;
- equity and drawdown curves against B1 and B2;
- CAGR pre- and post-tax, volatility, Sharpe, max drawdown, Ulcer index, time under water;
- turnover, cost, tax paid and the number of trades under A$1,000 suppressed;
- the battery table, DSR/PSR and PBO;
- "what would falsify this";
- the validator memo.

## 4. Paper to live, monitoring and change control

**What paper trading can and cannot prove.** With t ≈ SR·√T (Lo 2002; Bailey–López de Prado's minimum track record length answers "How long should a track record be in order to have statistical confidence that its Sharpe ratio is above a given threshold?") [2+, extracts], detecting a Sharpe difference of 0.2 at about 2σ takes roughly 100 years (my arithmetic). No feasible paper period validates performance. Paper trading validates implementation fidelity, which is a low-variance quantity.

**Promotion criteria (RND-030)** [unverified design]:
- At least 6 monthly cycles and at least 2 full rotations of every tranche.
- At least one risk-off and one risk-on transition executed. If none occurs naturally, run a forced-signal replay drill in the paper account.
- Paper-versus-harness replay over the same dates: weight difference ≤ 0.5 pp, monthly return difference ≤ 10 bp, order lists identical.
- Zero unexplained reconciliation breaks.
- Kill-switch and restart drills passed.

**Live monitoring (RND-031):**

| Metric | Review trigger | Kill / halt trigger |
|---|---|---|
| Live vs same-period replay tracking difference | > 25 bp/month, or > 50 bp cumulative | > 100 bp unexplained → halt new orders, hold positions |
| Realised cost vs model | > 1.5× over 6 months | > 2.5× |
| Drawdown vs bootstrap distribution | Beyond 95th percentile | Beyond 99th percentile, or > 1.5× backtest max drawdown |
| Rolling 36-month excess drawdown protection vs B2 | Review only; statistical power is too low to kill on returns | — |
| Signal sanity | Vote flips > 3 in 6 months | Data-feed staleness or price gap > 20% → no trade |
| Operational | Missed run, rejected order | Position mismatch against broker |

Decay detection uses a CUSUM on monthly live-minus-replay difference (implementation decay) and an annual re-run of the battery on extended data (edge decay). The default response to underperformance against B2 in a bull market is to do nothing, because that is the expected cost of the overlay.

**Change control (RND-032).**
- Semantic-versioned spec; code tagged to the spec hash.
- A parameter change is a new hypothesis and a new card, with N incremented.
- Champion/challenger: the challenger runs in paper for at least 6 cycles alongside the live champion; maximum one promotion per 12 months.
- Two-step approval for multi-user: a proposer and a different approver, with a 7-day delay.
- Emergency halt is single-key; resume is two-key.
- Agents have no merge rights to the live branch and no order permissions.

## 5. What "world's best algorithm" can honestly mean

A monthly ETF trend overlay at A$5k cannot be "best" in the sense of highest return. The evidence says most discovered edges are false or shrink (Harvey–Liu–Zhu†; Harvey–Liu†), and this overlay is expected to cost return in exchange for shallower drawdowns. "Best" here can mean four things:
- **Robust:** passes the battery without tuned parameters.
- **Cheap:** total drag below a stated budget.
- **Explainable:** a one-page rule the owner could run by hand.
- **Survivable:** a drawdown the owner will actually sit through, so the plan is not abandoned.

At A$5k the algorithm's contribution to wealth is small. The five levers below matter more.

| Lever | Evidence | Tag |
|---|---|---|
| 1. Contributions | Vanguard: "Over a two-year time horizon, 94% of a portfolio's ending balance is achieved through savings… Over 10 years, 80%" (4% real return assumed; search extract) | [1] |
| 2. Costs | Morningstar/Kinnel: "The expense ratio is the most proven predictor of future fund returns"; cheapest-quintile US equity funds had a 62% success rate vs 20% for the priciest (search extract). IBKR's A$6.60 minimum is 0.66% of a A$1,000 trade† | [2+] |
| 3. Discipline | Morningstar Mind the Gap 2025: investors earned 8.7% vs 9.9% fund returns, a gap of about 1.2 pp/yr; least-volatile funds had a −0.4% gap vs −2.1% for the most volatile. Vanguard Advisor's Alpha attributes about 150 bp of its "about 3%" to behavioural coaching; that is Vanguard's own estimate and is contested (search extracts) | [2+] |
| 4. Tax | Each overlay switch realises gains and can forfeit the 12-month discount (ATO); the regime may change on 1 July 2027 | [2+] on rules; magnitude [unverified] until H11 runs |
| 5. Diversification and process | AQR time-series momentum "back to 1880… consistently profitable over the next 110 years"† supports trend as a robust diversifier, not a small-account return engine; tranching removes timing luck (Hoffstein) | [1] / [2+] |

Lever 1 has a direct consequence at this scale: a A$500/month contribution is 10% of the account each month. Contributions should do most of the rebalancing, at zero tax and near-zero marginal cost. Lever 3 is the real case for automation plus a drawdown overlay.

## Spec-ready decisions

- **RND-001** Trend is specified, tested and reported as a drawdown overlay; no return-enhancement claim without t ≥ 3.0 and DSR ≥ 0.95.
- **RND-002** AI agents may research, code, test and validate; they may never approve specs, promote variants or create or modify orders. This is enforced by repository and broker permissions.
- **RND-003** Builder and validator agents are separated; the validator re-implements from the spec only.
- **RND-010** Hypothesis card template as in section 2; a card is frozen and hashed before the first run.
- **RND-011** Append-only trial log written by the harness; N feeds DSR.
- **RND-012** Two test families; Holm at α = 0.10 for risk claims; t ≥ 3.0 plus DSR for return claims.
- **RND-013** H1–H12 are the complete initial set; additions need a new card.
- **RND-014** H2 negative control: a backtest return uplift above 1 pp/yr triggers an audit.
- **RND-020** Event-driven system of record sharing code with live; vectorised twin reconciled to 1 bp/month.
- **RND-021** Cost model: IBKR fixed 0.08% / A$6 ex-GST minimum plus spread table; re-verified quarterly.
- **RND-022** Parcel-level tax engine with a switch for the current 50% discount and the proposed 1 July 2027 indexation / 30% minimum; confirm legislative status before go-live.
- **RND-023** All tranche offsets simulated; dispersion reported.
- **RND-024** Proxy map from 1990 with splice tracking error; proxy-era results flagged.
- **RND-025** Holdout 2024-01 onward locked in code and opened once.
- **RND-026** Robustness battery as in section 3, including the placebo test and the Feb–Apr 2025 window.
- **RND-027** Standard reporting pack per run.
- **RND-030** Paper-to-live requires ≥ 6 cycles, ≥ 2 tranche rotations, both state transitions exercised and fidelity tolerances met; it is explicitly not a performance test.
- **RND-031** Monitoring triggers as in section 4; halt means stop new orders and hold positions.
- **RND-032** Versioned spec, champion/challenger, at most one promotion per 12 months, two-step approval with 7-day delay, single-key halt and two-key resume.
- **RND-033** Contributions are directed to underweight sleeves before any sell.
- **RND-034** Owner-facing statement of "best" as robust, cheap, explainable and survivable, with the expected-underperformance-in-bull-markets disclosure signed before go-live.
- **RND-035** Model-risk references cite SR 26-2 (17 April 2026) as superseding SR 11-7.

## Sources

Fetched directly:
- https://www.man.com/insights/backtesting
- https://www.man.com/insights/ai-agents-trend
- https://quantpedia.com/why-machine-learning-funds-fail/
- https://www.nber.org/papers/w20592
- https://www.cxoadvisory.com/big-ideas/curbing-data-snooping/
- https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php
- https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/research-guide
- https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing

Via search extracts only (hosts blocked):
- https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm
- https://www.orrick.com/en/Insights/2026/04/Agencies-Overhaul-Model-Risk-Management-Guidance-for-Banks-Heres-What-Changed
- https://www.ey.com/content/dam/ey-unified-site/ey-com/en-us/insights/banking-capital-markets/documents/ey-model-risk-management-guidance.pdf
- https://papers.ssrn.com/abstract=3275654
- https://papers.ssrn.com/abstract=2326253
- https://papers.ssrn.com/abstract=2460551
- https://www.risk.net/journal-risk/2223785/sharpe-ratio-efficient-frontier
- https://rdrr.io/cran/PerformanceAnalytics/man/MinTrackRecord.html
- https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios
- https://www.risk.net/hedge-funds-review/news/2470076/man-ahl-investors-profit-from-artificial-intelligence
- https://www.twosigma.com/articles/why-failure-is-an-option-in-science
- https://www.thinknewfound.com/rebalance-timing-luck
- https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount
- https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/capital-gains-tax-reform
- https://www.pwc.com.au/tax/tax-alerts/cgt-and-housing-tax-reform.html
- https://www.bdo.com.au/en-au/insights/budget/2026/changes-to-the-capital-gains-tax-discount
- https://www.betashares.com.au/advisers/insights/liberation-day-upended-markets/
- https://www.morningstar.com/business/insights/research/mind-the-gap-2025
- https://global.morningstar.com/en-gb/funds/how-fund-fees-are-the-best-predictor-of-returns
- https://www.vanguard.ca/content/dam/intl/americas/canada/en/documents/gas/quantifying-your-value-to-clients-advisor.pdf
- https://externalcrewnet.vanguard.com/content/corporatesite/us/en/corp/articles/flipping-the-script-how-we-talk-about-investing-success.html
- https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/
- https://www.interactivebrokers.com/campus/ibkr-quant-news/a-practical-breakdown-of-vector-based-vs-event-based-backtesting/