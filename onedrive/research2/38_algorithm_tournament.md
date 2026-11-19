# 38 — Algorithm tournament on real historical data: nine strategy families raced head to head

Date: 2026-11-13. Spec: `FD_FINAL.md` v2.10 (live rule L1, section 9.1; sizing engine, section 26; registry, section 24). Companion reports: 35 (design survey), 36 (L1 variants on real data — not repeated here).
Status: research report. **Not a card run under RND-025.** No frozen card, no production harness and no licensed index proxy exists yet. This is an exploratory race of pre-declared rules on free public data.

Every number in the tables is produced by code in `scratchpad/algo_tournament/code/` from files downloaded today; tables are generated, not typed. Re-run with `sh scratchpad/algo_tournament/run_all.sh`. Tables that do not fit here are in `38_algorithm_tournament_tables.md`.

## 0. Answer first

**Nothing beat static 40/60 with statistical confidence, at any account size, once costs are counted. After tax, almost everything is clearly worse.** 47 pre-declared rule configurations in nine families were run on 48 years of monthly AUD data (1976–2023), with 2024-01 onward held out.

**Compact leaderboard, 1976–2023 (23 of the 39 long-sample trials; full tables in sections 3 and 4).** Sorted by CAGR after costs and Regime-B tax at A$25,000. "vs 40/60" columns: is the 90% bootstrap interval of the difference clear of zero?

| Contestant | Trial | Paper Sharpe | Max drawdown, net A$25k | After-tax CAGR A$5k | After-tax CAGR A$25k | After-tax CAGR A$100k | Gap to 40/60 at A$25k (pp) | Pre-tax return vs 40/60 | After-tax return vs 40/60 | Drawdown vs 40/60 | Reality-check p (38 trials) | Holdout 2024–25, net A$25k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 40/50 + 10% momentum sleeve | F1_momg10 | 0.43 | -39.8% | 10.02% | 10.94% | 10.91% | +0.18 | noise | noise | noise | 0.92 | 38.1% |
| Static DHHF-like 37/63 | S3_dhhf3763 | 0.42 | -40.2% | 10.64% | 10.81% | 10.82% | +0.06 | noise | noise | noise | 0.98 | 38.9% |
| Static 40/60 (B2) | S1_4060 | 0.42 | -40.1% | 10.64% | 10.76% | 10.76% | +0.00 | – | – | – | – | 38.2% |
| Static 100% global equity | S2_world100 | 0.38 | -46.4% | 10.58% | 10.58% | 10.58% | -0.18 | noise | noise | noise | 1.00 | 45.3% |
| Macro: CAPE gated by trend (M3) | M3_cape_trend | 0.49 | -27.1% | 10.18% | 10.41% | 10.44% | -0.35 | noise | noise | better | 0.33 | 36.3% |
| L1, OFF money in cash ETF | L1_cashetf | 0.49 | -27.1% | 9.50% | 9.81% | 9.83% | -0.94 | noise | noise | better | 0.90 | 36.5% |
| Macro: yield-curve inversion | M1_curve | 0.42 | -30.0% | 9.39% | 9.27% | 9.26% | -1.48 | noise | worse | noise | 1.00 | 23.0% |
| Regime: volatility-managed 40/60 | H3_volmanaged | 0.42 | -34.0% | 9.12% | 9.27% | 9.40% | -1.48 | noise | worse | better | 1.00 | 36.2% |
| Static 60/40 equity/bond | S4_6040 | 0.48 | -18.6% | 8.97% | 9.19% | 9.28% | -1.56 | noise | worse | better | 0.40 | 21.3% |
| Static 55/30/15 shares/bonds/gold (S5) | S5_div | 0.46 | -15.4% | 7.60% | 9.01% | 9.10% | -1.74 | noise | noise | better | 0.96 | 37.5% |
| Regime: 2-state HMM | H1_hmm_us | 0.38 | -31.1% | 7.96% | 8.97% | 9.17% | -1.79 | worse | worse | noise | 1.00 | 34.3% |
| L1 as specified (idle cash 0%) | L1_spec | 0.38 | -26.6% | 8.81% | 8.95% | 8.95% | -1.81 | noise | worse | noise | 1.00 | 37.0% |
| Dual momentum (GEM) | G1_gem12 | 0.40 | -41.6% | 8.18% | 8.39% | 8.39% | -2.36 | noise | noise | noise | 1.00 | 37.8% |
| Keller PAA style | K4_paa_core | 0.54 | -30.5% | 7.10% | 8.33% | 8.51% | -2.42 | noise | noise | noise | 0.99 | 55.6% |
| Ensemble: trend + RP + vol-managed | E3_slow3 | 0.54 | -10.9% | 7.49% | 7.47% | 7.71% | -3.29 | noise | worse | better | 0.98 | 29.5% |
| Keller DAA style | K2_daa_core | 0.69 | -22.5% | 5.14% | 7.46% | 7.64% | -3.30 | noise | worse | better | 0.98 | 27.6% |
| Ensemble of six primaries | E1_six | 0.51 | -23.3% | 6.70% | 7.15% | 7.46% | -3.61 | noise | worse | better | 1.00 | 23.1% |
| Spec P1 analogue (budgets x trend score) | R5_p1like | 0.59 | -16.1% | 5.59% | 7.01% | 7.46% | -3.74 | noise | worse | better | 1.00 | 25.5% |
| Trend ensemble 3/6/12m, 10% vol | T2_tsmom_core10 | 0.65 | -14.7% | 5.33% | 6.53% | 7.00% | -4.23 | noise | worse | better | 0.99 | 26.6% |
| Risk parity + trend | R4_classrp_ts | 0.69 | -7.7% | 4.59% | 6.50% | 6.70% | -4.26 | noise | worse | better | 0.93 | 27.7% |
| Risk parity | R2_classrp | 0.37 | -10.9% | 5.07% | 6.45% | 6.58% | -4.31 | noise | worse | better | 1.00 | 29.6% |
| Trend ensemble EWMAC, 10% vol | T1_ewmac_core10 | 0.65 | -12.0% | 5.46% | 6.25% | 6.78% | -4.50 | noise | worse | better | 1.00 | 21.5% |
| Keller VAA style | K1_vaa_core | 0.36 | -41.6% | 4.53% | 5.21% | 5.21% | -5.54 | noise | worse | noise | 1.00 | 1.3% |

After-tax CAGR = after trading costs, tax at 32% under the post-1 July 2027 rules, and tax on a full sale at the end. Pre-1 July 2027 rules give the same order (Table C1). "After-tax return vs 40/60" uses yearly tax paid without the final sale.

1. **No algorithm earns a return claim.** The best net-of-cost result against a volatility-matched 40/60 is the valuation-gated trend rule M3 (t = 2.1 at A$25,000). The bar for the best of 38 trials is t = 3.2. White's reality-check p-value is 0.33 at A$25,000, 0.24 at A$100,000, 0.63 at A$5,000, and 0.89 after tax (Table G7). Deflated Sharpe of the active return is at most 0.62 (pass mark 0.95).
2. **The one result that looked significant is an artefact.** On frictionless returns from 1991 the Keller-style canary rule K2x has a Sharpe of 1.08 and passes the reality check (p = 0.012). With a one-month execution delay its Sharpe drops to 0.69 and nothing passes (p = 0.22 for the best trial). With costs at A$25,000 nothing passes (p = 0.13, and the "best" trial is then the static 60/40). About 1 point of the long-sample sibling's return comes from a gold price series that is a monthly average (Table H5). After tax K2x trails 40/60 by 2.2 points a year.
3. **What is real is drawdown reduction, and it comes from the asset mix, not the algorithm.** Holding bonds and gold cuts maximum drawdown from 40% to 15–19% with a 90% confidence interval that excludes zero (static 60/40 and the static 55/30/15 mix S5, Table F1). Trend, risk-parity and ensemble rules on the same five sleeves cut it further (to 5–12%), but against their own static parent S5 the extra gain is 3–10 points of drawdown for 0.9–2.0 points a year of return before tax (Table F6) and 1.5–2.8 points after tax.
4. **Costs and the A$1,000 minimum order make every rotation rule, and every mix with a sleeve under 20% of the account, infeasible at A$5,000.** They lose 2.5 to 6.3 points a year after costs and tax against 40/60 (Table E-5k). A 15% sleeve of A$5,000 is A$750, below the minimum order, so the money sits idle. Only mixes whose every sleeve is at least A$1,000 (static two-sleeve mixes, L1, the macro and regime overlays) work at that size.
5. **Tax is the larger cost at every size.** At A$100,000, where brokerage is small, the trend ensemble T1 earns 9.8% before tax against 11.8% for 40/60, and 6.8% against 10.8% after Regime-B tax. Rules that trade monthly realise gains under 12 months and hold more interest-bearing assets, whose income is taxed in full each year.
6. **In-sample ranking does not predict out-of-sample ranking.** Probability of backtest overfitting, net at A$25,000: 0.73 when picking by Sharpe, 0.70 by CAGR (Table G8). Rank correlation between development and holdout Sharpe across the 47 trials: 0.25. The only ranking that persists is by return-to-drawdown ratio (PBO 0.02), which is a persistent property of low-volatility asset mixes, not skill.
7. **Holdout (2024–2025).** Static 40/60 returned 38.2% net at A$25,000. Only six of 46 other trials did better: global-only equity (45.3%), the DHHF-like 37/63 mix (38.9%), the AU-region momentum sleeve (39.6%) and three Keller rules whose universes include gold, which doubled in AUD (K4 55.6%, K3 42.8%, K4x 41.4%). Every trend, risk-parity, regime, macro and ensemble rule trailed, most by 8 to 20 points. The five-sleeve trend ensemble T1 returned 21.5%. Nothing protected in February–April 2025 (40/60 −5.8%, L1 −5.6%).

**Recommended live algorithm by stage**

| Stage | Live | Why | Paper challengers |
|---|---|---|---|
| A$5,000 | **STATIC 40/60** (or L1 only if H1 passes at G2 and the owner chooses the drawdown trade; that is report 36's question) | Top of the after-tax table together with the other static equity mixes. L1 with a cash ETF costs 1.1 points a year after tax at this size; L1 as specified (idle cash at 0%) costs 1.8. No other contestant can be implemented at A$5,000 | None that trades. Record M3 and S5 as shadow series only |
| A$25,000 | **Unchanged** | No contestant is distinguishable from 40/60 before tax; every dynamic one is worse after tax, by 0.4 to 5.5 points | H70 static diversified mix (S5); H71 valuation-gated trend (M3); H72 trend ensemble against its static parent, 10% no-trade band |
| A$100,000 | **Unchanged core.** If the owner's objective is lower drawdown, the supported change is a static mix with bonds and gold (H70), not an algorithm | At this size S5 costs nothing to hold (shortfall 0.0 points); the price is the lower expected return of bonds: 1.1 points a year before tax and 1.7 after on 1976–2023; 0.1 and 0.3 on 2007–2023 | H72 and H73 (risk parity with trend) as capital-preservation candidates; H74 negative controls |

**Brutally honest summary.** The spec's section 26 engine (continuous forecasts, volatility target, risk budgets) run on five ETFs is a low-return, bond-heavy portfolio: its 10–12% volatility target never binds without leverage (realised 5.4–6.8%). It does what it says for drawdown and loses about 4 points a year to 40/60 after tax. Dual momentum, the Keller family, the HMM and the yield-curve rule add nothing. The ensemble of six is the average of things that do not work. The momentum sleeve adds 0.2 points with a confidence interval that includes zero, before its own trading costs. The honest live choice at all three sizes is the one the spec already has.

## 0.1 Caveats that change how far to trust this

- **Monthly proxies, not ETFs.** Fama–French country and region portfolios, RBA yields through a bond-pricing model, AQR's global bond futures series, a World Bank gold series. They are not the RND-024 index proxies. Section 1 lists each compromise.
- **Gold is a monthly-average price.** That makes gold look smoother and more trend-friendly than it was. Table H5 measures the effect: small for most contestants, about 1 point a year for the Keller rules.
- **Same-bar execution** (RND-028): signal and fill use the same month-end price. The one-month-delay columns bound the optimism. It matters a great deal for rules that weight the last month's return heavily (Keller's 13612W).
- **The holdout has now been read** for all these families on these proxies, including L1 (it never switched off, so it equals 40/60 apart from rebalancing drift; report 36 says the same). Any card registered from this report must treat 2024-01 to 2026-09 as seen. Real out-of-sample evidence for these cards starts with paper trading.
- **History is not the forward regime.** Cash returned about 7% a year over 1976–2023 and bonds had a 40-year bull market from 1982. Sharpe ratios of bond-heavy rules flatter them, and the tax drag on interest is larger than it would be in a 3–4% cash world. Table D2 repeats everything on 2007–2023 only. The ranking does not change.
- **The tax model is an approximation** (section 2.4). It is good enough to rank a buy-and-hold rule against a monthly switcher; it is not a tax calculation.
- **I added things after seeing the first run** (section 2.6): an execution-band study, a lifecycle study, a gold diagnostic and a 2007+ table. None changed a rule or a parameter of a contestant. All are logged.

## 1. Data and provenance

All downloads are in `scratchpad/algo_tournament/data/`, hashed in `data/derived/provenance.json` (SHA-256 of every raw file and of the two derived files). They were parsed as text or spreadsheets only; Python was run with `-I`.

| Sleeve (ETF it stands for) | Series built | Source and method | From | Known weakness |
|---|---|---|---|---|
| AUEQ (VAS) | Australia market, value-weighted, **local-currency** total return, less 0.07% a year | Ken French, *F-F International Countries*, `Austrlia.Dat`, first block | 1975-01 | Excludes franking credits (added in the tax model). Ends 2025-12; **2026-01 to 2026-09 is the French Asia-Pacific ex-Japan market in AUD** (correlation 0.83, tracking error 7.5% a year, 2010–2025) — flagged proxy, used only in the extended holdout |
| WXAU (VGS, unhedged) | Developed-markets total return in USD × AUD/USD, less 0.18% | French *Developed 3 Factors* (Mkt-RF + RF) from 1990-07. Before that 45% US market (French) + 55% French international index `Ind_all`; the 45% was declared before running; the best fit on the 1990–2023 overlap is 42%, and the declared blend tracks the Developed series within 1.3% a year | 1975-01 | Includes Australia (about 2%). Gross of withholding tax. Month-end FX from RBA F11 differs from French's own conversion by 0.44% a month on average (timing) |
| WXAUH (VGAD, hedged) | (1 + USD return) × (1 + AU cash) ÷ (1 + US bill) − 1, less 0.21% | As WXAU; hedge carry from RBA cash and the French US bill rate | 1975-01 | Treats all foreign exposure as USD. Used only by the Keller-style rules |
| US (IVV) | French US market in AUD, less 0.04% | *F-F Research Data Factors* | 1975-01 | — |
| EM (VGE) | French *Emerging 5 Factors* market in AUD, less 0.48% | — | 1989-07 | Short history; 1991+ trials only |
| SMALL (VISM) | Mean of the three small-cap portfolios of French *Developed 6 Portfolios ME × BE/ME* in AUD (US 6 portfolios before 1990-07), less 0.33% | — | 1975-01 | Paper portfolios, no trading costs inside |
| AUBOND (VAF) | 50% 5-year + 50% 10-year Australian Government **constant-maturity par bond**: buy at last month's yield, reprice a month later at the new yield with one month less to run, semi-annual coupons. Less 0.10% | RBA F2: month-end yields 1969–1994 from the historical table; month-end values taken from the daily tables from 1995 | 1975-01 | Government only, no credit or semi-government; synthetic. Lag-1 autocorrelation 0.10 |
| GBOND (VBND, hedged) | AU cash + AQR *Century of Factor Premia* "Fixed income Market" excess return (multi-country government bond futures). Less 0.20% | AQR data library | 1975-01 | 4.6% volatility. AQR ends 2026-02; **2026-03 to 2026-09 = 0.39 × US 10-year par-bond excess return** (beta fitted on 1975–2023; the US yield is a monthly average) — flagged proxy |
| GOLD (PMGOLD) | USD gold × AUD/USD, less 0.15% | World Bank "Pink Sheet" monthly series through the `datasets/gold-prices` repository | 1975-01 | **Monthly average price**, converted at month-end FX. Lag-1 autocorrelation of USD gold returns 0.19, roughly what averaging alone produces |
| CASH (cash ETF) | RBA cash rate target (interbank overnight rate 1976–1990, 90-day bank bill before) ÷ 12, less 0.10% | RBA F1 | 1975-01 | Monthly average rate |
| MOMG / MOMAU (momentum ETFs) | French *6 Portfolios ME × Prior 12-2*, "Big, High prior": Developed (US before 1990-11) and Asia-Pacific ex-Japan, in AUD, less 0.35% | — | 1975-01 / 1990-11 | Long-only paper portfolios, rebalanced monthly with **no internal trading cost**. Asia-Pacific ex-Japan is a poor stand-in for Australia |
| Signals | US CAPE (Shiller, through `datasets/s-and-p-500`; published to 2023-09, then extended by the price ratio with 6% a year assumed earnings growth; lagged one month). AU curve = 10-year yield − 90-day bill. US curve = 10-year − 1-month bill. CPI: RBA G1. US market from 1926 for the HMM | — | 1881 / 1969 / 1953 / 1922 | CAPE after 2023-09 is an approximation; the series was far above its 80th percentile throughout, so the approximation does not move the signal |

Not reachable from this session: Shiller's own site, FRED, the World Bank document server, LBMA, Yahoo, Stooq. Mirrors on GitHub (`datasets/…`) were used where stated.

Sleeve statistics, 1976–2023, AUD, net of fee: Australian equity 11.4% a year, 16.8% volatility, −48% maximum drawdown; world 11.7%, 14.1%, −46%; AU bonds 8.0%, 6.3%, −19%; global bonds hedged 9.2%, 4.8%, −18%; gold 6.9%, 18.4%, −50%; cash 7.0%. Full table and the 1990+ correlation matrix: `data/derived/splice_report.txt`.

## 2. Method

### 2.1 Contestants

47 configurations, declared in `code/strategies.py` before the first full run (file SHA-256 `3526217e…`, recorded in `out/freeze_run1.txt` and in every trial record). Nine carry the tag "primary" for their family. Each is a function of information up to month-end *t* that returns target weights applied to month *t*+1. Long-only, weights sum to at most 1, no leverage.

| Trial | Family | Rule (pre-declared parameters) | Sample from | Execution | Primary |
|---|---|---|---|---|---|
| S1_4060 | 1 Static | B2: 40% AU / 60% world ex-AU unhedged | 1976-01 | yearly, ±20% band | yes |
| S2_world100 | 1 Static | 100% equity, global cap-weight (no home bias) | 1976-01 | yearly, ±20% band |  |
| S2b_au100 | 1 Static | 100% Australian equity | 1976-01 | yearly, ±20% band |  |
| S3_dhhf3763 | 1 Static | DHHF-like 37/63, two sleeves (long sample) | 1976-01 | yearly, ±20% band |  |
| S3x_dhhf_ext | 1 Static | DHHF-like with EM and small caps (1991+) | 1991-01 | yearly, ±20% band |  |
| S4_6040 | 1 Static | 60/40 equity/bond | 1976-01 | yearly, ±20% band |  |
| S5_div | 1 Static | static diversified 55 eq / 30 bonds / 15 gold (parent mix of trend and RP contestants) | 1976-01 | yearly, ±20% band |  |
| L1_spec | 2 L1 | L1 exactly as spec 9.1: OFF sleeve = idle cash at 0% | 1976-01 | L1 (PRT-14/16/17) |  |
| L1_cashetf | 2 L1 | L1 with OFF sleeve in a cash ETF (spec H10 variant) | 1976-01 | L1 + cash ETF | yes |
| T1_ewmac_core10 | 3 Trend | EWMAC 3-speed, 5 sleeves, 10% vol target | 1976-01 | monthly, 2% band | yes |
| T2_tsmom_core10 | 3 Trend | 3/6/12m TSMOM blend, 5 sleeves, 10% vol target | 1976-01 | monthly, 2% band |  |
| T3_ewmac_core12 | 3 Trend | T1 at 12% | 1976-01 | monthly, 2% band |  |
| T4_tsmom_core12 | 3 Trend | T2 at 12% | 1976-01 | monthly, 2% band |  |
| T5_ewmac_eq2_12 | 3 Trend | EWMAC on the L1 universe (AU, world), 12% | 1976-01 | monthly, 2% band |  |
| T6_ewmac_ext10 | 3 Trend | EWMAC, 8 sleeves (adds US, EM, small), 10% | 1991-01 | monthly, 2% band |  |
| G1_gem12 | 4 Dual momentum | GEM: best of AU/world by 12m if > cash else AU bonds | 1976-01 | monthly, 2% band | yes |
| G2_gem12_2bond | 4 Dual momentum | GEM, safe = 50/50 AU/global bonds | 1976-01 | monthly, 2% band |  |
| G3_gem_blend | 4 Dual momentum | GEM with 3/6/12m blended lookback | 1976-01 | monthly, 2% band |  |
| G4_gem6 | 4 Dual momentum | GEM with 6m lookback | 1976-01 | monthly, 2% band |  |
| K1_vaa_core | 5 Keller | VAA-G4 style, top 1 | 1976-01 | monthly, 2% band | yes |
| K1x_vaa_ext | 5 Keller | VAA with US and EM (1991+) | 1991-01 | monthly, 2% band |  |
| K2_daa_core | 5 Keller | DAA style, canary = hedged world + AU bonds | 1976-01 | monthly, 2% band |  |
| K2x_daa_ext | 5 Keller | DAA with EM + AU bond canary (1991+) | 1991-01 | monthly, 2% band |  |
| K3_baa_core | 5 Keller | BAA style, core | 1976-01 | monthly, 2% band |  |
| K3x_baa_ext | 5 Keller | BAA with US/world/EM/bond canary (1991+) | 1991-01 | monthly, 2% band |  |
| K4_paa_core | 5 Keller | PAA style breadth protection (spec V4 analogue), core | 1976-01 | monthly, 2% band |  |
| K4x_paa_ext | 5 Keller | PAA, 7 risky sleeves (1991+) | 1991-01 | monthly, 2% band |  |
| R1_invvol | 6 Risk parity | inverse 12m vol, 5 sleeves | 1976-01 | monthly, 2% band |  |
| R2_classrp | 6 Risk parity | equal risk across equity/bond/gold classes (naive) | 1976-01 | monthly, 2% band | yes |
| R3_invvol_sma | 6 Risk parity | R1 + 10m SMA overlay | 1976-01 | monthly, 2% band |  |
| R4_classrp_ts | 6 Risk parity | R2 + 12m TSMOM overlay | 1976-01 | monthly, 2% band |  |
| R5_p1like | 6 Risk parity | spec P1 (SIZ-14) analogue on 5 sleeves: budgets x five-vote trend score | 1976-01 | monthly, 2% band |  |
| R5x_p1like_ext | 6 Risk parity | P1 analogue, 8 sleeves (1991+) | 1991-01 | monthly, 2% band |  |
| H1_hmm_us | 7 Regime | 2-state HMM on US market 1926+, equity = P(calm) x 40/60 | 1976-01 | monthly, 2% band | yes |
| H1b_hmm_own | 7 Regime | 2-state HMM on own 40/60 returns (120m burn-in, static before) | 1976-01 | monthly, 2% band |  |
| H2_volswitch | 7 Regime | halve equity when EW vol > expanding 75th percentile | 1976-01 | monthly, 2% band |  |
| H3_volmanaged | 7 Regime | 40/60 scaled to 12% vol, capped at 100% | 1976-01 | monthly, 2% band |  |
| M1_curve | 8 Macro | halve a sleeve while its home yield curve (10y - 3m) is inverted | 1976-01 | monthly, 2% band | yes |
| M1b_curve12 | 8 Macro | M1, stay de-risked until 12 months after inversion ends | 1976-01 | monthly, 2% band |  |
| M2_cape_step | 8 Macro | halve equity when US CAPE > expanding 80th percentile | 1976-01 | monthly, 2% band |  |
| M2b_cape_lin | 8 Macro | equity 100% -> 50% linearly from CAPE median to max percentile | 1976-01 | monthly, 2% band |  |
| M3_cape_trend | 8 Macro | halve equity only if CAPE > 80th pct AND 40/60 below 10m SMA | 1976-01 | monthly, 2% band |  |
| F1_momg10 | 10 Factor sleeve | 40/50/10 with global big-cap high-momentum sleeve | 1976-01 | yearly, ±20% band |  |
| F2_momau10 | 10 Factor sleeve | card H14 shape: 10% AU-region momentum carved from AU sleeve (APxJ proxy, 1991+) | 1991-01 | yearly, ±20% band |  |
| E1_six | 9 Ensemble | equal weight of the six family primaries (3-8) | 1976-01 | monthly, 2% band | yes |
| E2_mom3 | 9 Ensemble | three momentum styles | 1976-01 | monthly, 2% band |  |
| E3_slow3 | 9 Ensemble | trend + risk parity + vol-managed | 1976-01 | monthly, 2% band |  |

Two samples. **Long: 1976-01 to 2023-12 (576 months), 39 trials.** **1991-01 to 2023-12 (396 months): 8 more trials** that need emerging markets, small caps or the AU-region momentum portfolio; on that window all 47 are compared (Table D in the tables file). **Holdout: 2024-01 to 2025-12** on clean data, with an extension to 2026-09 on flagged proxies.

Design notes that matter:

- **L1** is copied from PRT-12 and PRT-13 (three votes, hysteresis, start OFF) and not tuned. Two versions: as specified, with an OFF sleeve in idle cash at 0% (PRT-18); and the H10 variant with OFF money in a cash ETF. The cash-ETF version is the fair comparator, because every other contestant parks money in the cash ETF. L1 switched 6.7 times a decade per sleeve and was invested 83% of the time.
- **Trend ensembles (T)** follow section 26: forecasts scaled to an average absolute value of 10 (scalars estimated on an expanding window), capped at 20, long-only, position = risk weight × 1.4 × target ÷ volatility × forecast ÷ 10, capped at 100% in total. Carver's 16/64, 32/128 and 64/256-day pairs become 1/3, 1.5/6 and 3/12-month pairs; the 8/32 pair is shorter than a month and cannot exist on monthly data. T2 and T4 use 3-, 6- and 12-month excess returns instead.
- **Keller-style rules (K)** are my adaptations to the ASX ETF set, not Keller's published universes. Their published track records do not transfer.
- **HMM (H1)** is refitted every December on data to that date and filtered forward; equity share = predicted probability of the calm state.
- **Macro (M)** uses fixed thresholds (curve below zero) or expanding percentiles (CAPE since 1881). M3 halves equity only when CAPE is above its expanding 80th percentile **and** the 40/60 portfolio is below its 10-month average.
- **Ensembles (E)** average the member target weights in one account, so opposing trades net.

### 2.2 Execution and costs

- Month-end decision, same-bar fill. Dynamic rules trade a sleeve when target and holding differ by at least 2% of NAV and by at least A$1,000; a sleeve with a zero target is sold in full (exempt from the minimum, as PRT-17). Static mixes rebalance at the end of June if a weight is more than 20% (relative) off target, as PRT-22. L1 trades on a state change (buys from A$500, PRT-14) and otherwise like a static mix. Orders are whole dollars. Sells first; buys scaled to available cash. Idle cash of A$1,000 or more goes to the most under-weight sleeve.
- Commission max(A$6.60, 0.088%) (A$6 / 0.08% plus GST, RND-021). Half-spread 5 bp for VAS, VGS, IVV and VAF; 2 bp for the cash ETF; 10 bp for the rest. Idle cash earns 0%.
- **Constant-size simulation.** To measure cost drag *at* A$5,000, A$25,000 and A$100,000 the account is rescaled to that size after each month (holdings and tax parcels scale together). The lifecycle study (Table H3) instead lets a real account grow from A$5,000 with A$500 a month.
- "Paper" = frictionless, rebalanced to target monthly. "Shortfall" = paper CAGR − net CAGR; it includes cash drag and the effect of skipped orders.

### 2.3 Statistics

- Sharpe is over the cash-ETF return. Maximum drawdown and Ulcer use month-end values.
- **Block bootstrap:** stationary bootstrap, mean block 12 months, 10,000 paths, paired (the same resampled months for strategy and benchmark), for differences in CAGR, Sharpe and maximum drawdown against static 40/60, L1 and the static diversified mix S5.
- **Deflated Sharpe** (Bailey and López de Prado), twice: on Sharpe over cash, and on the information ratio against a 40/60-plus-cash blend of the same volatility, which is the fair test for a rule that runs at lower risk. N = every trial in the sample.
- **White's reality check** on the same volatility-matched active return: bootstrap distribution of the maximum t-statistic over all trials.
- **PBO by CSCV:** 16 blocks, all 12,870 half-splits, selecting by Sharpe, CAGR or return-to-drawdown.

### 2.4 Tax model (approximate; assumptions stated)

- Resident individual, capital account, marginal rate 30% + 2% Medicare. Sensitivities at 45% + 2% and at 0%.
- Parcels are FIFO. A parcel counts as held 12 months only when 13 month-ends have passed (the days of acquisition and disposal are excluded).
- **Regime A** (CGT events before 1 July 2027): 50% discount on gains held 12 months; losses offset undiscounted gains first; net losses carried forward.
- **Regime B** (from 1 July 2027): cost base indexed by CPI for parcels held 12 months, gains only; net gain taxed at max(marginal rate, 30%) + Medicare. Applied to the whole history, as RND-022(b). Adding Medicare on top of the 30% floor is my assumption [unverified].
- Distributions are taxed each year at the marginal rate and reinvested (cost base stepped up): Australian shares 4.0% yield, 75% franked, franking credit offset or refunded; world 1.8%; US 1.3%; EM 2.2%; small caps 1.8%; AU bonds the running yield; hedged global bonds cash rate + 1%; cash all of it; gold none. The equity yields are fixed assumptions, not historical series.
- Tax is paid from the portfolio every 30 June. "After tax" CAGR figures also deduct the tax on a full sale at the end of the sample, so buy-and-hold gets no free deferral.
- Not modelled: the 1 July 2027 deemed sale itself, the 45-day rule, AMIT cost-base adjustments, foreign tax offsets, the sale needed to pay the tax bill.

### 2.5 Trial accounting

| What | Count | Where |
|---|---|---|
| Rule configurations declared and run once (run 1) | 47 | `out/trials.jsonl`, note "run1" |
| Execution-band variants (2 extra bands × 2 sizes × 37 dynamic rules), added after run 1 | 148 | note "exec-band variant" |
| Diagnostics (gold removed or lagged), not candidates | 14 | note "diagnostic" |
| **Total logged** | **209** | — |

Before run 1 the engine was unit-tested on two configurations only (static 40/60 and GEM). That exposed two engine bugs (costs were not reducing returns; CPI indexation was applied to reinvested distributions from the parcel date). Both were fixed before the freeze. No rule or parameter changed after any result was seen. Deflated Sharpe and the reality check use N = 39 or 47 (distinct rules). Counting all 209 would raise the bar further and change no conclusion, because nothing passes at N = 39.

### 2.6 What I added beyond the brief, and why

| Addition | Why |
|---|---|
| Static diversified mix S5 (55/30/15) and a comparison of every rule against it | Without it, the benefit of holding bonds and gold is credited to whichever algorithm happens to hold them |
| 1991+ versions with US, EM and small caps; PAA and BAA styles; the spec's P1 (SIZ-14) analogue; an HMM on the portfolio's own returns; three more macro variants | The brief's families at the breadth the ASX ETF set allows; P1 is the spec's own paper strategy |
| Execution-band study (2%, 5%, 10% of NAV) | Run 1 showed that the declared 2% band makes continuous rules trade 30+ times a year. Section 26 (SIZ-07) prescribes a buffer; a fair test needs one |
| Lifecycle study: A$5,000 + A$500 a month, 39 ten-year windows, dollars, tax | The owner's actual situation. Constant-size results cannot show what contributions and a growing account do |
| One-month-delay and double-cost reruns; gold diagnostic; 2007–2023 table; reality check | Each closes a specific way the headline could be wrong: same-bar optimism, averaged gold prices, the high-yield era, selection among many trials |

## 3. Results

### 3.1 Frictionless performance

**Table A1. Frictionless ("paper") performance, development sample 1976-01 to 2023-12 (576 months), AUD, net of ETF-like fees, before trading costs and tax**

| Trial | CAGR | Vol | Sharpe | MaxDD | Ulcer | Worst 12m | Time under water % | Turnover x/yr | Skew | Delay-1m CAGR | Delay-1m Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | 11.99 | 12.86 | 0.42 | -39.87 | 11.00 | -31.39 | 64 | 0.10 | -0.90 | 11.99 | 0.42 |
| S2_world100 | 11.74 | 14.13 | 0.38 | -46.44 | 15.05 | -31.25 | 71 | 0.00 | 0.24 | 11.74 | 0.38 |
| S2b_au100 | 11.41 | 16.82 | 0.33 | -48.37 | 12.83 | -41.53 | 69 | 0.00 | -1.42 | 11.41 | 0.33 |
| S3_dhhf3763 | 11.99 | 12.84 | 0.42 | -39.67 | 11.18 | -30.86 | 64 | 0.10 | -0.81 | 11.99 | 0.42 |
| S4_6040 | 10.87 | 8.22 | 0.48 | -20.20 | 4.36 | -15.02 | 55 | 0.12 | -0.78 | 10.87 | 0.48 |
| S5_div | 10.66 | 8.05 | 0.46 | -14.80 | 3.90 | -11.80 | 53 | 0.14 | -0.06 | 10.66 | 0.46 |
| L1_spec | 10.97 | 11.27 | 0.38 | -26.39 | 8.03 | -24.02 | 66 | 0.74 | -0.93 | 10.63 | 0.35 |
| L1_cashetf | 12.27 | 11.19 | 0.49 | -26.39 | 6.08 | -19.09 | 62 | 0.74 | -1.03 | 11.93 | 0.46 |
| T1_ewmac_core10 | 10.60 | 5.43 | 0.65 | -12.38 | 1.77 | -6.50 | 43 | 2.26 | -1.30 | 10.08 | 0.55 |
| T2_tsmom_core10 | 10.99 | 6.07 | 0.65 | -13.69 | 2.35 | -8.10 | 47 | 2.38 | -0.76 | 10.16 | 0.52 |
| T3_ewmac_core12 | 10.66 | 5.65 | 0.64 | -12.38 | 1.93 | -7.49 | 44 | 2.27 | -1.34 | 10.23 | 0.56 |
| T4_tsmom_core12 | 11.27 | 6.76 | 0.63 | -16.62 | 2.87 | -9.24 | 48 | 2.48 | -0.92 | 10.43 | 0.51 |
| T5_ewmac_eq2_12 | 11.42 | 9.43 | 0.48 | -24.80 | 4.78 | -17.42 | 63 | 2.51 | -1.19 | 11.67 | 0.49 |
| G1_gem12 | 11.98 | 14.24 | 0.40 | -41.68 | 11.26 | -31.00 | 70 | 2.15 | -1.86 | 12.26 | 0.41 |
| G2_gem12_2bond | 11.97 | 14.11 | 0.40 | -41.68 | 11.36 | -31.58 | 70 | 2.15 | -1.91 | 12.22 | 0.41 |
| G3_gem_blend | 11.84 | 14.39 | 0.39 | -41.68 | 10.52 | -24.40 | 70 | 2.56 | -1.77 | 11.53 | 0.36 |
| G4_gem6 | 11.73 | 14.26 | 0.38 | -41.68 | 10.10 | -25.13 | 68 | 3.04 | -1.82 | 11.72 | 0.38 |
| K1_vaa_core | 10.76 | 11.72 | 0.36 | -41.68 | 7.64 | -28.85 | 63 | 7.27 | -2.95 | 10.85 | 0.37 |
| K2_daa_core | 13.20 | 8.93 | 0.69 | -21.48 | 3.18 | -10.19 | 51 | 5.40 | 0.28 | 10.93 | 0.44 |
| K3_baa_core | 11.31 | 9.41 | 0.48 | -22.51 | 4.48 | -12.98 | 60 | 4.45 | 0.24 | 11.64 | 0.50 |
| K4_paa_core | 13.00 | 11.37 | 0.54 | -29.90 | 5.38 | -18.57 | 58 | 2.80 | 0.10 | 12.29 | 0.49 |
| R1_invvol | 9.15 | 4.84 | 0.44 | -12.33 | 2.10 | -11.00 | 41 | 0.38 | -0.14 | 9.13 | 0.44 |
| R2_classrp | 8.85 | 5.07 | 0.37 | -10.45 | 1.99 | -10.05 | 45 | 0.40 | 0.20 | 8.87 | 0.37 |
| R3_invvol_sma | 9.49 | 4.12 | 0.61 | -5.18 | 1.14 | -4.25 | 38 | 1.43 | -0.06 | 9.19 | 0.53 |
| R4_classrp_ts | 9.76 | 4.04 | 0.69 | -7.55 | 1.50 | -5.16 | 36 | 1.36 | -0.08 | 9.23 | 0.59 |
| R5_p1like | 10.61 | 6.05 | 0.59 | -15.02 | 2.32 | -6.49 | 44 | 1.43 | -0.83 | 10.25 | 0.53 |
| H1_hmm_us | 11.15 | 11.89 | 0.38 | -29.83 | 9.75 | -26.02 | 65 | 0.56 | -0.94 | 11.00 | 0.37 |
| H1b_hmm_own | 11.57 | 12.09 | 0.41 | -37.26 | 10.21 | -29.32 | 64 | 0.20 | -0.77 | 11.59 | 0.41 |
| H2_volswitch | 11.59 | 11.67 | 0.42 | -34.31 | 9.07 | -25.53 | 62 | 0.81 | -0.93 | 11.74 | 0.44 |
| H3_volmanaged | 11.50 | 11.29 | 0.42 | -33.42 | 9.56 | -26.52 | 62 | 0.36 | -0.72 | 11.58 | 0.43 |
| M1_curve | 11.51 | 11.69 | 0.42 | -30.69 | 7.96 | -24.31 | 62 | 0.51 | -1.01 | 11.62 | 0.42 |
| M1b_curve12 | 11.59 | 10.07 | 0.47 | -25.74 | 6.07 | -23.71 | 59 | 0.26 | -0.39 | 11.85 | 0.50 |
| M2_cape_step | 10.66 | 10.40 | 0.38 | -26.39 | 5.66 | -20.77 | 56 | 0.24 | -1.03 | 10.72 | 0.39 |
| M2b_cape_lin | 11.07 | 9.94 | 0.43 | -28.23 | 5.34 | -22.01 | 56 | 0.19 | -0.40 | 11.01 | 0.42 |
| M3_cape_trend | 12.61 | 11.92 | 0.49 | -27.56 | 6.94 | -20.77 | 62 | 0.55 | -0.85 | 12.24 | 0.46 |
| F1_momg10 | 12.19 | 12.92 | 0.43 | -39.71 | 11.13 | -31.12 | 64 | 0.10 | -0.91 | 12.19 | 0.43 |
| E1_six | 11.20 | 8.30 | 0.51 | -25.00 | 3.99 | -13.82 | 54 | 2.07 | -2.12 | 11.09 | 0.50 |
| E2_mom3 | 11.33 | 9.28 | 0.48 | -31.91 | 5.33 | -19.70 | 59 | 3.68 | -2.90 | 11.31 | 0.48 |
| E3_slow3 | 10.43 | 6.29 | 0.54 | -11.47 | 2.34 | -7.91 | 48 | 0.83 | -0.62 | 10.29 | 0.52 |


**Table A2. As A1 for the contestants that need EM / small caps / AU-region momentum: 1991-01 to 2023-12 (396 months)**

| Trial | CAGR | Vol | Sharpe | MaxDD | Ulcer | Worst 12m | Time under water % | Turnover x/yr | Skew | Delay-1m CAGR | Delay-1m Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S3x_dhhf_ext | 9.14 | 11.38 | 0.46 | -40.27 | 12.01 | -32.16 | 68 | 0.08 | -0.61 | 9.14 | 0.46 |
| T6_ewmac_ext10 | 8.96 | 4.90 | 0.94 | -6.89 | 1.68 | -6.55 | 51 | 2.44 | -0.18 | 8.27 | 0.76 |
| K1x_vaa_ext | 9.62 | 7.67 | 0.69 | -9.18 | 3.16 | -8.62 | 61 | 7.18 | 0.61 | 10.81 | 0.75 |
| K2x_daa_ext | 11.93 | 6.87 | 1.08 | -11.81 | 2.46 | -9.69 | 50 | 5.96 | 0.12 | 9.22 | 0.68 |
| K3x_baa_ext | 7.73 | 7.72 | 0.46 | -14.64 | 3.78 | -10.53 | 65 | 5.39 | 0.19 | 9.61 | 0.68 |
| K4x_paa_ext | 10.92 | 7.56 | 0.86 | -16.27 | 3.67 | -15.68 | 55 | 2.57 | -0.02 | 10.51 | 0.81 |
| R5x_p1like_ext | 7.85 | 4.66 | 0.75 | -6.18 | 1.67 | -5.91 | 51 | 1.42 | 0.01 | 7.63 | 0.70 |
| F2_momau10 | 9.42 | 11.40 | 0.48 | -39.21 | 12.16 | -30.85 | 68 | 0.08 | -0.56 | 9.42 | 0.48 |


Reading: the highest Sharpe ratios belong to the bond-heavy rules (T, R, the 1991+ Keller rules). The highest returns belong to all-equity mixes and to K2 and K4. Trend ensembles ran at 5.4–6.8% volatility against targets of 10% and 12%: without leverage, risk-budget sizing puts 55–60% of capital in bonds and the target cannot be reached. The one-month-delay columns show which results depend on trading at the signal price: K2 loses 2.3 points of CAGR and a third of its Sharpe; the trend ensembles lose 0.5–0.9 points; the statics, L1 and the macro rules lose little.

### 3.2 Costs by account size

**Table B1. Net of trading costs by account size (constant-size simulation; IBKR A$6.60 min / 0.088% incl. GST, half-spread 5-10 bp, A$1,000 minimum order, whole-dollar orders), 1976-2023. Shortfall = paper CAGR minus net CAGR (includes cash drag and tracking from skipped orders); explicit cost = commissions + spread as % of NAV per year**

| Trial | Paper CAGR | Net CAGR 5k | Net CAGR 25k | Net CAGR 100k | Shortfall 5k | Shortfall 25k | Shortfall 100k | Explicit cost 5k | Explicit cost 25k | Explicit cost 100k | Trades/yr 5k | Trades/yr 25k | Trades/yr 100k | Idle cash % 5k | Orders skipped/yr 5k | MaxDD 5k | MaxDD 25k | 2x cost CAGR 25k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | 11.99 | 11.60 | 11.78 | 11.78 | 0.39 | 0.21 | 0.21 | 0.01 | 0.01 | 0.00 | 0.0 | 0.2 | 0.2 | 0.0 | 0.5 | -40.8 | -40.1 | 11.77 |
| S2_world100 | 11.74 | 11.73 | 11.73 | 11.73 | 0.01 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -46.4 | -46.4 | 11.73 |
| S2b_au100 | 11.41 | 11.41 | 11.41 | 11.41 | 0.01 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | -48.4 | -48.4 | 11.41 |
| S3_dhhf3763 | 11.99 | 11.61 | 11.88 | 11.89 | 0.38 | 0.11 | 0.11 | 0.01 | 0.01 | 0.01 | 0.0 | 0.2 | 0.2 | 0.0 | 0.5 | -40.3 | -40.2 | 11.87 |
| S4_6040 | 10.87 | 10.39 | 10.93 | 11.03 | 0.49 | -0.06 | -0.16 | 0.02 | 0.02 | 0.01 | 0.1 | 0.7 | 0.8 | 3.8 | 2.1 | -24.7 | -18.6 | 10.94 |
| S5_div | 10.66 | 8.54 | 10.63 | 10.70 | 2.12 | 0.04 | -0.04 | 0.02 | 0.02 | 0.01 | 0.1 | 0.7 | 1.0 | 27.9 | 4.5 | -27.9 | -15.4 | 10.61 |
| L1_spec | 10.97 | 10.60 | 10.73 | 10.73 | 0.37 | 0.24 | 0.24 | 0.21 | 0.09 | 0.09 | 1.4 | 1.5 | 1.5 | 16.8 | 0.1 | -26.6 | -26.6 | 10.63 |
| L1_cashetf | 12.27 | 11.67 | 11.98 | 12.02 | 0.60 | 0.29 | 0.24 | 0.39 | 0.19 | 0.18 | 2.6 | 3.5 | 5.2 | 0.2 | 13.1 | -26.7 | -27.1 | 11.76 |
| T1_ewmac_core10 | 10.60 | 7.98 | 9.17 | 9.79 | 2.62 | 1.43 | 0.81 | 1.27 | 1.10 | 0.72 | 8.7 | 32.1 | 44.0 | 12.4 | 36.7 | -12.0 | -12.0 | 7.98 |
| T2_tsmom_core10 | 10.99 | 7.90 | 9.64 | 10.18 | 3.10 | 1.36 | 0.82 | 1.44 | 1.10 | 0.71 | 9.9 | 31.9 | 41.2 | 11.4 | 30.8 | -16.1 | -14.7 | 8.45 |
| T3_ewmac_core12 | 10.66 | 7.94 | 9.35 | 9.83 | 2.72 | 1.31 | 0.83 | 1.33 | 1.09 | 0.73 | 9.0 | 31.2 | 43.4 | 12.6 | 36.1 | -12.0 | -10.5 | 8.16 |
| T4_tsmom_core12 | 11.27 | 8.50 | 9.87 | 10.41 | 2.77 | 1.40 | 0.86 | 1.47 | 1.12 | 0.75 | 10.0 | 31.9 | 41.0 | 11.0 | 30.0 | -16.3 | -17.6 | 8.64 |
| T5_ewmac_eq2_12 | 11.42 | 9.14 | 10.49 | 10.70 | 2.29 | 0.94 | 0.72 | 1.46 | 0.85 | 0.65 | 10.0 | 21.8 | 24.7 | 5.8 | 14.7 | -29.0 | -24.9 | 9.57 |
| G1_gem12 | 11.98 | 11.09 | 11.30 | 11.30 | 0.89 | 0.67 | 0.67 | 0.78 | 0.59 | 0.59 | 4.3 | 4.3 | 4.3 | 0.1 | 0.0 | -41.6 | -41.6 | 10.64 |
| G2_gem12_2bond | 11.97 | 10.88 | 11.27 | 11.27 | 1.09 | 0.71 | 0.71 | 0.97 | 0.62 | 0.62 | 5.5 | 5.5 | 5.6 | 0.1 | 0.2 | -41.6 | -41.6 | 10.57 |
| G3_gem_blend | 11.84 | 10.79 | 11.04 | 11.04 | 1.06 | 0.80 | 0.80 | 0.94 | 0.71 | 0.71 | 5.1 | 5.1 | 5.1 | 0.1 | 0.0 | -41.6 | -41.6 | 10.26 |
| G4_gem6 | 11.73 | 10.49 | 10.79 | 10.79 | 1.24 | 0.94 | 0.94 | 1.11 | 0.84 | 0.84 | 6.1 | 6.1 | 6.1 | 0.1 | 0.0 | -41.6 | -41.6 | 9.86 |
| K1_vaa_core | 10.76 | 7.64 | 8.34 | 8.34 | 3.11 | 2.42 | 2.42 | 2.84 | 2.20 | 2.20 | 14.6 | 14.6 | 14.6 | 0.1 | 0.0 | -41.6 | -41.6 | 5.98 |
| K2_daa_core | 13.20 | 8.64 | 11.12 | 11.32 | 4.56 | 2.08 | 1.88 | 3.66 | 1.80 | 1.65 | 23.5 | 35.1 | 35.9 | 6.3 | 14.6 | -25.1 | -22.5 | 9.14 |
| K3_baa_core | 11.31 | 7.83 | 9.71 | 9.82 | 3.49 | 1.60 | 1.50 | 3.00 | 1.39 | 1.35 | 19.1 | 23.8 | 24.8 | 2.3 | 10.0 | -25.2 | -24.3 | 8.20 |
| K4_paa_core | 13.00 | 10.10 | 11.83 | 12.02 | 2.90 | 1.17 | 0.99 | 1.61 | 1.05 | 0.90 | 10.0 | 21.4 | 22.4 | 12.0 | 20.1 | -30.5 | -30.5 | 10.67 |
| R1_invvol | 9.15 | 7.25 | 8.75 | 9.01 | 1.90 | 0.40 | 0.14 | 0.04 | 0.18 | 0.14 | 0.2 | 5.7 | 14.9 | 12.9 | 54.1 | -14.0 | -13.1 | 8.57 |
| R2_classrp | 8.85 | 6.83 | 8.53 | 8.72 | 2.02 | 0.32 | 0.13 | 0.05 | 0.20 | 0.15 | 0.3 | 6.4 | 15.5 | 15.2 | 53.1 | -9.3 | -10.9 | 8.36 |
| R3_invvol_sma | 9.49 | 6.36 | 8.65 | 9.05 | 3.13 | 0.84 | 0.43 | 0.72 | 0.59 | 0.42 | 4.9 | 16.7 | 24.5 | 21.4 | 43.5 | -7.0 | -5.5 | 8.02 |
| R4_classrp_ts | 9.76 | 6.72 | 9.10 | 9.36 | 3.04 | 0.65 | 0.40 | 0.79 | 0.53 | 0.40 | 5.4 | 14.7 | 21.1 | 15.6 | 36.3 | -10.8 | -7.7 | 8.51 |
| R5_p1like | 10.61 | 7.54 | 9.53 | 10.11 | 3.06 | 1.07 | 0.50 | 0.60 | 0.75 | 0.45 | 4.3 | 24.5 | 39.2 | 22.0 | 52.8 | -19.5 | -16.1 | 8.73 |
| H1_hmm_us | 11.15 | 9.52 | 10.66 | 10.90 | 1.63 | 0.49 | 0.25 | 0.20 | 0.23 | 0.15 | 1.4 | 7.1 | 11.0 | 8.7 | 28.7 | -25.8 | -31.1 | 10.40 |
| H1b_hmm_own | 11.57 | 10.70 | 11.27 | 11.47 | 0.88 | 0.30 | 0.10 | 0.02 | 0.08 | 0.06 | 0.2 | 2.7 | 6.4 | 6.9 | 27.2 | -41.3 | -36.3 | 11.19 |
| H2_volswitch | 11.59 | 10.62 | 11.30 | 11.34 | 0.97 | 0.29 | 0.25 | 0.45 | 0.21 | 0.20 | 3.1 | 4.9 | 6.9 | 6.0 | 13.8 | -34.1 | -34.3 | 11.07 |
| H3_volmanaged | 11.50 | 10.47 | 11.10 | 11.34 | 1.03 | 0.39 | 0.16 | 0.07 | 0.19 | 0.13 | 0.5 | 6.6 | 15.1 | 9.8 | 26.0 | -32.9 | -34.0 | 10.88 |
| M1_curve | 11.51 | 11.19 | 11.38 | 11.36 | 0.32 | 0.13 | 0.15 | 0.27 | 0.15 | 0.13 | 1.9 | 4.4 | 6.4 | 6.2 | 20.6 | -30.1 | -30.0 | 11.15 |
| M1b_curve12 | 11.59 | 11.08 | 11.40 | 11.52 | 0.52 | 0.19 | 0.07 | 0.13 | 0.07 | 0.07 | 0.9 | 2.2 | 5.0 | 4.8 | 20.8 | -26.1 | -25.3 | 11.36 |
| M2_cape_step | 10.66 | 10.49 | 10.54 | 10.60 | 0.17 | 0.12 | 0.06 | 0.09 | 0.07 | 0.07 | 0.6 | 2.1 | 4.5 | 2.6 | 26.2 | -28.1 | -27.1 | 10.46 |
| M2b_cape_lin | 11.07 | 10.59 | 10.97 | 10.96 | 0.48 | 0.10 | 0.11 | 0.04 | 0.10 | 0.06 | 0.3 | 3.4 | 7.5 | 6.7 | 29.4 | -27.2 | -27.2 | 10.86 |
| M3_cape_trend | 12.61 | 11.92 | 12.35 | 12.42 | 0.69 | 0.26 | 0.19 | 0.29 | 0.15 | 0.14 | 2.0 | 3.7 | 5.7 | 1.8 | 17.9 | -27.6 | -27.1 | 12.18 |
| F1_momg10 | 12.19 | 10.95 | 11.97 | 11.95 | 1.23 | 0.21 | 0.24 | 0.01 | 0.01 | 0.01 | 0.1 | 0.2 | 0.4 | 6.1 | 1.6 | -41.4 | -39.8 | 11.96 |
| E1_six | 11.20 | 8.71 | 10.07 | 10.45 | 2.49 | 1.14 | 0.75 | 0.59 | 0.89 | 0.64 | 4.1 | 25.6 | 36.9 | 10.3 | 50.4 | -24.7 | -23.3 | 9.12 |
| E2_mom3 | 11.33 | 7.49 | 9.83 | 10.03 | 3.85 | 1.50 | 1.30 | 2.90 | 1.24 | 1.13 | 19.0 | 27.4 | 37.9 | 6.1 | 22.5 | -31.0 | -31.8 | 8.50 |
| E3_slow3 | 10.43 | 9.17 | 9.71 | 10.06 | 1.26 | 0.72 | 0.37 | 0.11 | 0.44 | 0.29 | 0.8 | 14.5 | 30.0 | 13.4 | 57.7 | -15.7 | -10.9 | 9.25 |


- **A$5,000.** Two-sleeve binary rules lose 0.3–0.7 points. Five-sleeve rules lose 2–3 points, mostly from money that cannot be invested (idle cash 11–28%); the rotation rule K2 loses 4.6. The 1991+ rules with eight or nine sleeves are worse (Table B2 in the tables file): the P1 analogue holds 59% idle cash and returns 1.7% a year.
- **A$25,000.** Continuous rules still lose 1.1–1.4 points (30+ trades a year at a A$6.60 minimum). Rotation rules lose 0.7–2.4 points. Overlays on 40/60 lose 0.1–0.5.
- **A$100,000.** Continuous rules lose 0.5–0.9 points; the Keller rules 1.0–2.4, because they turn the whole portfolio over 3–7 times a year and that cost is proportional.
- Static mixes cost about nothing at A$25,000 and above. Their "shortfall" against a monthly-rebalanced paper portfolio is the missing rebalancing premium of a once-a-year banded rebalance, not a cost.

### 3.3 After tax

**Table C1. After costs and approximate Australian tax, CAGR % (liquidated at the end of 2023), 1976-2023. Regime A = 50% CGT discount after 12 months (law for CGT events before 1 July 2027); Regime B = CPI indexation after 12 months + 30% minimum rate on net gains (law from 1 July 2027), each applied to the whole history. Marginal rate 30% + 2% Medicare unless stated**

| Trial | Pre-tax 5k | After-tax A 5k | After-tax B 5k | Pre-tax 25k | After-tax A 25k | After-tax B 25k | Pre-tax 100k | After-tax A 100k | After-tax B 100k | Tax drag A 25k | Tax drag B 25k | A, 47% rate, 25k | B, 47% rate, 25k | A, 0% rate, 25k | B, 0% income rate (30% CGT floor), 25k | After-tax B MaxDD 25k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | 11.60 | 10.79 | 10.64 | 11.78 | 10.92 | 10.76 | 11.78 | 10.92 | 10.76 | 0.86 | 1.02 | 10.26 | 10.00 | 12.32 | 11.85 | -41.6 |
| S2_world100 | 11.73 | 10.81 | 10.58 | 11.73 | 10.82 | 10.58 | 11.73 | 10.82 | 10.58 | 0.92 | 1.16 | 10.37 | 9.99 | 11.73 | 11.22 | -47.1 |
| S2b_au100 | 11.41 | 10.78 | 10.77 | 11.41 | 10.78 | 10.77 | 11.41 | 10.78 | 10.77 | 0.63 | 0.64 | 9.85 | 9.83 | 12.76 | 12.56 | -48.6 |
| S3_dhhf3763 | 11.61 | 10.80 | 10.64 | 11.88 | 10.99 | 10.81 | 11.89 | 11.00 | 10.82 | 0.89 | 1.07 | 10.34 | 10.06 | 12.36 | 11.86 | -40.7 |
| S4_6040 | 10.39 | 9.07 | 8.97 | 10.93 | 9.31 | 9.19 | 11.03 | 9.40 | 9.28 | 1.62 | 1.74 | 8.39 | 8.22 | 11.25 | 10.83 | -18.9 |
| S5_div | 8.54 | 7.78 | 7.60 | 10.63 | 9.18 | 9.01 | 10.70 | 9.26 | 9.10 | 1.45 | 1.61 | 8.36 | 8.10 | 10.93 | 10.39 | -18.4 |
| L1_spec | 10.60 | 9.18 | 8.81 | 10.73 | 9.32 | 8.95 | 10.73 | 9.32 | 8.95 | 1.42 | 1.79 | 8.43 | 7.86 | 11.17 | 9.91 | -38.6 |
| L1_cashetf | 11.67 | 9.87 | 9.50 | 11.98 | 10.17 | 9.81 | 12.02 | 10.20 | 9.83 | 1.80 | 2.16 | 9.09 | 8.55 | 12.43 | 11.19 | -34.4 |
| T1_ewmac_core10 | 7.98 | 5.58 | 5.46 | 9.17 | 6.28 | 6.25 | 9.79 | 6.77 | 6.78 | 2.89 | 2.92 | 4.86 | 4.82 | 9.30 | 8.38 | -12.0 |
| T2_tsmom_core10 | 7.90 | 5.47 | 5.33 | 9.64 | 6.66 | 6.53 | 10.18 | 7.07 | 7.00 | 2.98 | 3.11 | 5.18 | 4.99 | 9.79 | 8.61 | -14.7 |
| T3_ewmac_core12 | 7.94 | 5.57 | 5.46 | 9.35 | 6.42 | 6.39 | 9.83 | 6.79 | 6.80 | 2.93 | 2.96 | 4.98 | 4.94 | 9.49 | 8.52 | -10.5 |
| T4_tsmom_core12 | 8.50 | 5.97 | 5.80 | 9.87 | 6.79 | 6.70 | 10.41 | 7.22 | 7.16 | 3.08 | 3.17 | 5.26 | 5.13 | 10.04 | 8.77 | -17.6 |
| T5_ewmac_eq2_12 | 9.14 | 6.83 | 6.50 | 10.49 | 7.61 | 7.46 | 10.70 | 7.80 | 7.66 | 2.88 | 3.03 | 6.10 | 5.88 | 10.82 | 9.10 | -24.9 |
| G1_gem12 | 11.09 | 8.56 | 8.18 | 11.30 | 8.77 | 8.39 | 11.30 | 8.77 | 8.39 | 2.53 | 2.91 | 7.34 | 6.75 | 11.84 | 10.09 | -41.6 |
| G2_gem12_2bond | 10.88 | 8.35 | 7.97 | 11.27 | 8.73 | 8.35 | 11.27 | 8.73 | 8.35 | 2.54 | 2.92 | 7.28 | 6.71 | 11.80 | 10.07 | -41.6 |
| G3_gem_blend | 10.79 | 8.24 | 8.01 | 11.04 | 8.49 | 8.26 | 11.04 | 8.49 | 8.26 | 2.56 | 2.78 | 6.99 | 6.64 | 11.63 | 9.96 | -41.6 |
| G4_gem6 | 10.49 | 7.43 | 7.44 | 10.79 | 7.72 | 7.73 | 10.79 | 7.72 | 7.73 | 3.06 | 3.05 | 5.99 | 6.00 | 11.36 | 9.47 | -41.6 |
| K1_vaa_core | 7.64 | 4.53 | 4.53 | 8.34 | 5.21 | 5.21 | 8.34 | 5.21 | 5.21 | 3.13 | 3.13 | 3.62 | 3.62 | 8.58 | 7.01 | -42.3 |
| K2_daa_core | 8.64 | 5.29 | 5.14 | 11.12 | 7.49 | 7.46 | 11.32 | 7.67 | 7.64 | 3.64 | 3.67 | 5.66 | 5.62 | 11.35 | 9.07 | -22.5 |
| K3_baa_core | 7.83 | 5.02 | 4.85 | 9.71 | 6.60 | 6.55 | 9.82 | 6.67 | 6.63 | 3.11 | 3.16 | 5.06 | 4.99 | 9.86 | 8.21 | -24.3 |
| K4_paa_core | 10.10 | 7.41 | 7.10 | 11.83 | 8.51 | 8.33 | 12.02 | 8.68 | 8.51 | 3.32 | 3.50 | 6.83 | 6.56 | 12.08 | 9.91 | -30.5 |
| R1_invvol | 7.25 | 5.19 | 5.20 | 8.75 | 6.59 | 6.65 | 9.01 | 6.75 | 6.77 | 2.17 | 2.10 | 5.50 | 5.60 | 8.89 | 8.64 | -14.0 |
| R2_classrp | 6.83 | 5.05 | 5.07 | 8.53 | 6.45 | 6.45 | 8.72 | 6.58 | 6.58 | 2.08 | 2.08 | 5.41 | 5.41 | 8.65 | 8.27 | -12.8 |
| R3_invvol_sma | 6.36 | 4.28 | 4.34 | 8.65 | 6.26 | 6.28 | 9.05 | 6.60 | 6.61 | 2.39 | 2.37 | 5.08 | 5.12 | 8.75 | 8.40 | -7.0 |
| R4_classrp_ts | 6.72 | 4.57 | 4.59 | 9.10 | 6.60 | 6.50 | 9.36 | 6.81 | 6.70 | 2.50 | 2.61 | 5.38 | 5.23 | 9.19 | 8.63 | -10.1 |
| R5_p1like | 7.54 | 5.74 | 5.59 | 9.53 | 7.27 | 7.01 | 10.11 | 7.74 | 7.46 | 2.27 | 2.52 | 6.09 | 5.72 | 9.76 | 8.84 | -16.3 |
| H1_hmm_us | 9.52 | 8.15 | 7.96 | 10.66 | 9.16 | 8.97 | 10.90 | 9.37 | 9.17 | 1.50 | 1.69 | 8.23 | 7.94 | 11.13 | 10.15 | -34.4 |
| H1b_hmm_own | 10.70 | 9.84 | 9.68 | 11.27 | 10.05 | 9.91 | 11.47 | 10.11 | 9.98 | 1.22 | 1.35 | 9.24 | 9.04 | 11.77 | 11.07 | -38.6 |
| H2_volswitch | 10.62 | 8.86 | 8.66 | 11.30 | 9.27 | 9.07 | 11.34 | 9.27 | 9.07 | 2.03 | 2.24 | 8.07 | 7.77 | 11.79 | 10.40 | -35.1 |
| H3_volmanaged | 10.47 | 9.32 | 9.12 | 11.10 | 9.44 | 9.27 | 11.34 | 9.59 | 9.40 | 1.66 | 1.83 | 8.44 | 8.18 | 11.58 | 10.61 | -36.1 |
| M1_curve | 11.19 | 9.64 | 9.39 | 11.38 | 9.57 | 9.27 | 11.36 | 9.55 | 9.26 | 1.81 | 2.10 | 8.51 | 8.07 | 11.82 | 10.59 | -36.7 |
| M1b_curve12 | 11.08 | 9.53 | 9.25 | 11.40 | 9.70 | 9.44 | 11.52 | 9.75 | 9.48 | 1.70 | 1.96 | 8.72 | 8.34 | 11.76 | 10.85 | -30.5 |
| M2_cape_step | 10.49 | 9.31 | 9.11 | 10.54 | 9.09 | 8.93 | 10.60 | 9.10 | 8.94 | 1.44 | 1.61 | 8.23 | 7.98 | 10.91 | 10.13 | -27.4 |
| M2b_cape_lin | 10.59 | 9.59 | 9.38 | 10.97 | 9.55 | 9.32 | 10.96 | 9.48 | 9.28 | 1.43 | 1.66 | 8.69 | 8.35 | 11.36 | 10.54 | -28.7 |
| M3_cape_trend | 11.92 | 10.55 | 10.18 | 12.35 | 10.78 | 10.41 | 12.42 | 10.81 | 10.44 | 1.57 | 1.94 | 9.81 | 9.25 | 12.85 | 11.59 | -29.3 |
| F1_momg10 | 10.95 | 10.16 | 10.02 | 11.97 | 11.12 | 10.94 | 11.95 | 11.09 | 10.91 | 0.85 | 1.03 | 10.45 | 10.18 | 12.52 | 12.03 | -41.2 |
| E1_six | 8.71 | 6.79 | 6.70 | 10.07 | 7.30 | 7.15 | 10.45 | 7.62 | 7.46 | 2.77 | 2.92 | 5.84 | 5.62 | 10.38 | 8.88 | -23.3 |
| E2_mom3 | 7.49 | 4.59 | 4.52 | 9.83 | 6.71 | 6.67 | 10.03 | 6.87 | 6.83 | 3.13 | 3.17 | 5.10 | 5.04 | 10.13 | 8.55 | -31.8 |
| E3_slow3 | 9.17 | 7.59 | 7.49 | 9.71 | 7.60 | 7.47 | 10.06 | 7.86 | 7.71 | 2.12 | 2.24 | 6.49 | 6.30 | 9.95 | 9.22 | -12.2 |


- Static equity mixes lose about 1.0 point a year to tax under either regime (franking credits offset part of it). L1 with a cash ETF loses 2.2. Trend, risk-parity and Keller rules lose 2.1–3.7.
- Regime B is slightly worse than Regime A for buy-and-hold over 48 years (10.76 against 10.92 for 40/60) and for switchers (L1: 9.81 against 10.17). The ranking is the same under both.
- At a 47% rate the gaps widen: 40/60 10.0%, L1 8.6%, T1 4.8%.

### 3.4 Leaderboards after costs and tax

**Table E-5k. Leaderboard at A$5,000, 1976-2023, ranked by CAGR after costs and Regime-B tax**

| Trial | Rank | After-tax B CAGR | After-tax A CAGR | Pre-tax net CAGR | MaxDD | Sharpe | After-tax B CAGR ÷ abs(MaxDD) | vs S1 (pp) |
|---|---|---|---|---|---|---|---|---|
| S2b_au100 | 1 | 10.77 | 10.78 | 11.41 | -48.4 | 0.33 | 0.22 | 0.13 |
| S1_4060 | 2 | 10.64 | 10.79 | 11.60 | -40.8 | 0.39 | 0.26 | 0.00 |
| S3_dhhf3763 | 3 | 10.64 | 10.80 | 11.61 | -40.3 | 0.39 | 0.26 | -0.01 |
| S2_world100 | 4 | 10.58 | 10.81 | 11.73 | -46.4 | 0.38 | 0.23 | -0.07 |
| M3_cape_trend | 5 | 10.18 | 10.55 | 11.92 | -27.6 | 0.44 | 0.37 | -0.47 |
| F1_momg10 | 6 | 10.02 | 10.16 | 10.95 | -41.4 | 0.36 | 0.24 | -0.63 |
| H1b_hmm_own | 7 | 9.68 | 9.84 | 10.70 | -41.3 | 0.34 | 0.23 | -0.96 |
| L1_cashetf | 8 | 9.50 | 9.87 | 11.67 | -26.7 | 0.44 | 0.36 | -1.14 |
| M1_curve | 9 | 9.39 | 9.64 | 11.19 | -30.1 | 0.40 | 0.31 | -1.25 |
| M2b_cape_lin | 10 | 9.38 | 9.59 | 10.59 | -27.2 | 0.36 | 0.35 | -1.27 |
| M1b_curve12 | 11 | 9.25 | 9.53 | 11.08 | -26.1 | 0.43 | 0.35 | -1.40 |
| H3_volmanaged | 12 | 9.12 | 9.32 | 10.47 | -32.9 | 0.36 | 0.28 | -1.53 |
| M2_cape_step | 13 | 9.11 | 9.31 | 10.49 | -28.1 | 0.35 | 0.32 | -1.54 |
| S4_6040 | 14 | 8.97 | 9.07 | 10.39 | -24.7 | 0.39 | 0.36 | -1.67 |
| L1_spec | 15 | 8.81 | 9.18 | 10.60 | -26.6 | 0.35 | 0.33 | -1.83 |
| H2_volswitch | 16 | 8.66 | 8.86 | 10.62 | -34.1 | 0.36 | 0.25 | -1.98 |
| G1_gem12 | 17 | 8.18 | 8.56 | 11.09 | -41.6 | 0.34 | 0.20 | -2.46 |
| G3_gem_blend | 18 | 8.01 | 8.24 | 10.79 | -41.6 | 0.32 | 0.19 | -2.64 |
| G2_gem12_2bond | 19 | 7.97 | 8.35 | 10.88 | -41.6 | 0.33 | 0.19 | -2.67 |
| H1_hmm_us | 20 | 7.96 | 8.15 | 9.52 | -25.8 | 0.28 | 0.31 | -2.69 |
| S5_div | 21 | 7.60 | 7.78 | 8.54 | -27.9 | 0.20 | 0.27 | -3.04 |
| E3_slow3 | 22 | 7.49 | 7.59 | 9.17 | -15.7 | 0.33 | 0.48 | -3.15 |
| G4_gem6 | 23 | 7.44 | 7.43 | 10.49 | -41.6 | 0.30 | 0.18 | -3.20 |
| K4_paa_core | 24 | 7.10 | 7.41 | 10.10 | -30.5 | 0.31 | 0.23 | -3.54 |
| E1_six | 25 | 6.70 | 6.79 | 8.71 | -24.7 | 0.25 | 0.27 | -3.95 |
| T5_ewmac_eq2_12 | 26 | 6.50 | 6.83 | 9.14 | -29.0 | 0.26 | 0.22 | -4.14 |
| T4_tsmom_core12 | 27 | 5.80 | 5.97 | 8.50 | -16.3 | 0.25 | 0.36 | -4.84 |
| R5_p1like | 28 | 5.59 | 5.74 | 7.54 | -19.5 | 0.12 | 0.29 | -5.06 |
| T1_ewmac_core10 | 29 | 5.46 | 5.58 | 7.98 | -12.0 | 0.21 | 0.45 | -5.19 |
| T3_ewmac_core12 | 30 | 5.46 | 5.57 | 7.94 | -12.0 | 0.20 | 0.45 | -5.19 |
| T2_tsmom_core10 | 31 | 5.33 | 5.47 | 7.90 | -16.1 | 0.18 | 0.33 | -5.31 |
| R1_invvol | 32 | 5.20 | 5.19 | 7.25 | -14.0 | 0.07 | 0.37 | -5.44 |
| K2_daa_core | 33 | 5.14 | 5.29 | 8.64 | -25.1 | 0.22 | 0.20 | -5.51 |
| R2_classrp | 34 | 5.07 | 5.05 | 6.83 | -9.3 | -0.02 | 0.55 | -5.57 |
| K3_baa_core | 35 | 4.85 | 5.02 | 7.83 | -25.2 | 0.13 | 0.19 | -5.79 |
| R4_classrp_ts | 36 | 4.59 | 4.57 | 6.72 | -10.8 | -0.08 | 0.42 | -6.05 |
| K1_vaa_core | 37 | 4.53 | 4.53 | 7.64 | -41.6 | 0.11 | 0.11 | -6.11 |
| E2_mom3 | 38 | 4.52 | 4.59 | 7.49 | -31.0 | 0.10 | 0.15 | -6.13 |
| R3_invvol_sma | 39 | 4.34 | 4.28 | 6.36 | -7.0 | -0.20 | 0.62 | -6.31 |


**Table E-25k. Leaderboard at A$25,000, 1976-2023, ranked by CAGR after costs and Regime-B tax**

| Trial | Rank | After-tax B CAGR | After-tax A CAGR | Pre-tax net CAGR | MaxDD | Sharpe | After-tax B CAGR ÷ abs(MaxDD) | vs S1 (pp) |
|---|---|---|---|---|---|---|---|---|
| F1_momg10 | 1 | 10.94 | 11.12 | 11.97 | -39.8 | 0.42 | 0.27 | 0.18 |
| S3_dhhf3763 | 2 | 10.81 | 10.99 | 11.88 | -40.2 | 0.41 | 0.27 | 0.06 |
| S2b_au100 | 3 | 10.77 | 10.78 | 11.41 | -48.4 | 0.33 | 0.22 | 0.01 |
| S1_4060 | 4 | 10.76 | 10.92 | 11.78 | -40.1 | 0.41 | 0.27 | 0.00 |
| S2_world100 | 5 | 10.58 | 10.82 | 11.73 | -46.4 | 0.38 | 0.23 | -0.18 |
| M3_cape_trend | 6 | 10.41 | 10.78 | 12.35 | -27.1 | 0.47 | 0.38 | -0.35 |
| H1b_hmm_own | 7 | 9.91 | 10.05 | 11.27 | -36.3 | 0.39 | 0.27 | -0.84 |
| L1_cashetf | 8 | 9.81 | 10.17 | 11.98 | -27.1 | 0.47 | 0.36 | -0.94 |
| M1b_curve12 | 9 | 9.44 | 9.70 | 11.40 | -25.3 | 0.46 | 0.37 | -1.32 |
| M2b_cape_lin | 10 | 9.32 | 9.55 | 10.97 | -27.2 | 0.42 | 0.34 | -1.44 |
| M1_curve | 11 | 9.27 | 9.57 | 11.38 | -30.0 | 0.41 | 0.31 | -1.48 |
| H3_volmanaged | 12 | 9.27 | 9.44 | 11.10 | -34.0 | 0.40 | 0.27 | -1.48 |
| S4_6040 | 13 | 9.19 | 9.31 | 10.93 | -18.6 | 0.48 | 0.49 | -1.56 |
| H2_volswitch | 14 | 9.07 | 9.27 | 11.30 | -34.3 | 0.40 | 0.26 | -1.69 |
| S5_div | 15 | 9.01 | 9.18 | 10.63 | -15.4 | 0.45 | 0.59 | -1.74 |
| H1_hmm_us | 16 | 8.97 | 9.16 | 10.66 | -31.1 | 0.35 | 0.29 | -1.79 |
| L1_spec | 17 | 8.95 | 9.32 | 10.73 | -26.6 | 0.36 | 0.34 | -1.81 |
| M2_cape_step | 18 | 8.93 | 9.09 | 10.54 | -27.1 | 0.37 | 0.33 | -1.83 |
| G1_gem12 | 19 | 8.39 | 8.77 | 11.30 | -41.6 | 0.35 | 0.20 | -2.36 |
| G2_gem12_2bond | 20 | 8.35 | 8.73 | 11.27 | -41.6 | 0.35 | 0.20 | -2.41 |
| K4_paa_core | 21 | 8.33 | 8.51 | 11.83 | -30.5 | 0.45 | 0.27 | -2.42 |
| G3_gem_blend | 22 | 8.26 | 8.49 | 11.04 | -41.6 | 0.34 | 0.20 | -2.50 |
| G4_gem6 | 23 | 7.73 | 7.72 | 10.79 | -41.6 | 0.32 | 0.19 | -3.02 |
| E3_slow3 | 24 | 7.47 | 7.60 | 9.71 | -10.9 | 0.44 | 0.68 | -3.29 |
| T5_ewmac_eq2_12 | 25 | 7.46 | 7.61 | 10.49 | -24.9 | 0.39 | 0.30 | -3.29 |
| K2_daa_core | 26 | 7.46 | 7.49 | 11.12 | -22.5 | 0.47 | 0.33 | -3.30 |
| E1_six | 27 | 7.15 | 7.30 | 10.07 | -23.3 | 0.39 | 0.31 | -3.61 |
| R5_p1like | 28 | 7.01 | 7.27 | 9.53 | -16.1 | 0.43 | 0.44 | -3.74 |
| T4_tsmom_core12 | 29 | 6.70 | 6.79 | 9.87 | -17.6 | 0.44 | 0.38 | -4.06 |
| E2_mom3 | 30 | 6.67 | 6.71 | 9.83 | -31.8 | 0.33 | 0.21 | -4.09 |
| R1_invvol | 31 | 6.65 | 6.59 | 8.75 | -13.1 | 0.37 | 0.51 | -4.11 |
| K3_baa_core | 32 | 6.55 | 6.60 | 9.71 | -24.3 | 0.32 | 0.27 | -4.20 |
| T2_tsmom_core10 | 33 | 6.53 | 6.66 | 9.64 | -14.7 | 0.44 | 0.45 | -4.23 |
| R4_classrp_ts | 34 | 6.50 | 6.60 | 9.10 | -7.7 | 0.54 | 0.84 | -4.26 |
| R2_classrp | 35 | 6.45 | 6.45 | 8.53 | -10.9 | 0.31 | 0.59 | -4.31 |
| T3_ewmac_core12 | 36 | 6.39 | 6.42 | 9.35 | -10.5 | 0.43 | 0.61 | -4.36 |
| R3_invvol_sma | 37 | 6.28 | 6.26 | 8.65 | -5.5 | 0.41 | 1.13 | -4.48 |
| T1_ewmac_core10 | 38 | 6.25 | 6.28 | 9.17 | -12.0 | 0.41 | 0.52 | -4.50 |
| K1_vaa_core | 39 | 5.21 | 5.21 | 8.34 | -41.6 | 0.17 | 0.13 | -5.54 |


**Table E-100k. Leaderboard at A$100,000, 1976-2023, ranked by CAGR after costs and Regime-B tax**

| Trial | Rank | After-tax B CAGR | After-tax A CAGR | Pre-tax net CAGR | MaxDD | Sharpe | After-tax B CAGR ÷ abs(MaxDD) | vs S1 (pp) |
|---|---|---|---|---|---|---|---|---|
| F1_momg10 | 1 | 10.91 | 11.09 | 11.95 | -39.9 | 0.42 | 0.27 | 0.16 |
| S3_dhhf3763 | 2 | 10.82 | 11.00 | 11.89 | -40.2 | 0.41 | 0.27 | 0.06 |
| S2b_au100 | 3 | 10.77 | 10.78 | 11.41 | -48.4 | 0.33 | 0.22 | 0.01 |
| S1_4060 | 4 | 10.76 | 10.92 | 11.78 | -40.1 | 0.41 | 0.27 | 0.00 |
| S2_world100 | 5 | 10.58 | 10.82 | 11.73 | -46.4 | 0.38 | 0.23 | -0.18 |
| M3_cape_trend | 6 | 10.44 | 10.81 | 12.42 | -27.6 | 0.48 | 0.38 | -0.32 |
| H1b_hmm_own | 7 | 9.98 | 10.11 | 11.47 | -37.3 | 0.40 | 0.27 | -0.78 |
| L1_cashetf | 8 | 9.83 | 10.20 | 12.02 | -26.4 | 0.47 | 0.37 | -0.93 |
| M1b_curve12 | 9 | 9.48 | 9.75 | 11.52 | -25.7 | 0.47 | 0.37 | -1.28 |
| H3_volmanaged | 10 | 9.40 | 9.59 | 11.34 | -33.6 | 0.41 | 0.28 | -1.36 |
| M2b_cape_lin | 11 | 9.28 | 9.48 | 10.96 | -28.5 | 0.42 | 0.33 | -1.48 |
| S4_6040 | 12 | 9.28 | 9.40 | 11.03 | -19.2 | 0.49 | 0.48 | -1.48 |
| M1_curve | 13 | 9.26 | 9.55 | 11.36 | -30.4 | 0.40 | 0.30 | -1.50 |
| H1_hmm_us | 14 | 9.17 | 9.37 | 10.90 | -30.5 | 0.37 | 0.30 | -1.59 |
| S5_div | 15 | 9.10 | 9.26 | 10.70 | -15.4 | 0.46 | 0.59 | -1.66 |
| H2_volswitch | 16 | 9.07 | 9.27 | 11.34 | -34.5 | 0.40 | 0.26 | -1.69 |
| L1_spec | 17 | 8.95 | 9.32 | 10.73 | -26.6 | 0.36 | 0.34 | -1.81 |
| M2_cape_step | 18 | 8.94 | 9.10 | 10.60 | -26.4 | 0.38 | 0.34 | -1.81 |
| K4_paa_core | 19 | 8.51 | 8.68 | 12.02 | -29.9 | 0.46 | 0.28 | -2.25 |
| G1_gem12 | 20 | 8.39 | 8.77 | 11.30 | -41.6 | 0.35 | 0.20 | -2.37 |
| G2_gem12_2bond | 21 | 8.35 | 8.73 | 11.27 | -41.6 | 0.35 | 0.20 | -2.41 |
| G3_gem_blend | 22 | 8.26 | 8.49 | 11.04 | -41.6 | 0.34 | 0.20 | -2.50 |
| G4_gem6 | 23 | 7.73 | 7.72 | 10.79 | -41.6 | 0.32 | 0.19 | -3.03 |
| E3_slow3 | 24 | 7.71 | 7.86 | 10.06 | -11.5 | 0.49 | 0.67 | -3.05 |
| T5_ewmac_eq2_12 | 25 | 7.66 | 7.80 | 10.70 | -24.8 | 0.41 | 0.31 | -3.10 |
| K2_daa_core | 26 | 7.64 | 7.67 | 11.32 | -22.2 | 0.49 | 0.34 | -3.12 |
| E1_six | 27 | 7.46 | 7.62 | 10.45 | -24.2 | 0.43 | 0.31 | -3.30 |
| R5_p1like | 28 | 7.46 | 7.74 | 10.11 | -15.0 | 0.52 | 0.50 | -3.30 |
| T4_tsmom_core12 | 29 | 7.16 | 7.22 | 10.41 | -16.7 | 0.51 | 0.43 | -3.60 |
| T2_tsmom_core10 | 30 | 7.00 | 7.07 | 10.18 | -13.8 | 0.52 | 0.51 | -3.76 |
| E2_mom3 | 31 | 6.83 | 6.87 | 10.03 | -32.0 | 0.35 | 0.21 | -3.93 |
| T3_ewmac_core12 | 32 | 6.80 | 6.79 | 9.83 | -12.4 | 0.50 | 0.55 | -3.96 |
| T1_ewmac_core10 | 33 | 6.78 | 6.77 | 9.79 | -12.4 | 0.51 | 0.55 | -3.98 |
| R1_invvol | 34 | 6.77 | 6.75 | 9.01 | -12.8 | 0.42 | 0.53 | -3.99 |
| R4_classrp_ts | 35 | 6.70 | 6.81 | 9.36 | -7.8 | 0.60 | 0.86 | -4.06 |
| K3_baa_core | 36 | 6.63 | 6.67 | 9.82 | -23.4 | 0.33 | 0.28 | -4.13 |
| R3_invvol_sma | 37 | 6.61 | 6.60 | 9.05 | -5.3 | 0.50 | 1.24 | -4.15 |
| R2_classrp | 38 | 6.58 | 6.58 | 8.72 | -10.7 | 0.34 | 0.61 | -4.18 |
| K1_vaa_core | 39 | 5.21 | 5.21 | 8.34 | -41.6 | 0.17 | 0.13 | -5.55 |


The same on the common 1991–2023 window, all 47 trials, at A$25,000:

**Table E2-25k. Leaderboard at A$25,000 on the common 1991-2023 window (all 47), ranked by CAGR after costs and Regime-B tax**

| Trial | Rank | After-tax B 25k | Net 25k | vs S1 (pp) | Net MaxDD 25k |
|---|---|---|---|---|---|
| S2b_au100 | 1 | 9.05 | 9.76 | 1.02 | -48.4 |
| F1_momg10 | 2 | 8.23 | 9.38 | 0.20 | -39.3 |
| F2_momau10 | 3 | 8.22 | 9.37 | 0.19 | -39.8 |
| S1_4060 | 4 | 8.03 | 9.14 | 0.00 | -40.1 |
| S3_dhhf3763 | 5 | 7.98 | 9.10 | -0.06 | -39.8 |
| S3x_dhhf_ext | 6 | 7.94 | 9.07 | -0.09 | -40.1 |
| M3_cape_trend | 7 | 7.84 | 9.89 | -0.20 | -27.1 |
| H2_volswitch | 8 | 7.42 | 9.19 | -0.61 | -34.3 |
| H1b_hmm_own | 9 | 7.42 | 8.69 | -0.62 | -36.3 |
| L1_cashetf | 10 | 7.29 | 9.13 | -0.75 | -19.4 |
| S2_world100 | 11 | 7.25 | 8.51 | -0.78 | -46.4 |
| M1_curve | 12 | 7.18 | 8.86 | -0.85 | -30.0 |
| H3_volmanaged | 13 | 7.09 | 8.53 | -0.94 | -34.0 |
| S4_6040 | 14 | 6.92 | 8.30 | -1.12 | -18.2 |
| M1b_curve12 | 15 | 6.90 | 8.47 | -1.13 | -25.3 |
| S5_div | 16 | 6.90 | 8.27 | -1.13 | -11.9 |
| G1_gem12 | 17 | 6.86 | 9.30 | -1.18 | -22.6 |
| G4_gem6 | 18 | 6.81 | 9.43 | -1.23 | -23.4 |
| L1_spec | 19 | 6.75 | 8.31 | -1.28 | -19.4 |
| G2_gem12_2bond | 20 | 6.75 | 9.18 | -1.28 | -23.7 |
| H1_hmm_us | 21 | 6.39 | 7.92 | -1.64 | -31.1 |
| G3_gem_blend | 22 | 6.38 | 8.62 | -1.65 | -22.4 |
| K4x_paa_ext | 23 | 6.36 | 9.48 | -1.68 | -17.7 |
| K4_paa_core | 24 | 5.96 | 8.72 | -2.07 | -15.2 |
| M2b_cape_lin | 25 | 5.89 | 7.40 | -2.14 | -27.2 |
| K2x_daa_ext | 26 | 5.82 | 9.39 | -2.22 | -14.5 |
| E3_slow3 | 27 | 5.79 | 7.66 | -2.24 | -9.9 |
| M2_cape_step | 28 | 5.71 | 7.30 | -2.32 | -26.2 |
| T5_ewmac_eq2_12 | 29 | 5.57 | 7.90 | -2.47 | -10.6 |
| R1_invvol | 30 | 5.39 | 6.94 | -2.64 | -13.1 |
| E1_six | 31 | 5.27 | 7.60 | -2.77 | -10.5 |
| R2_classrp | 32 | 5.24 | 6.79 | -2.80 | -10.9 |
| E2_mom3 | 33 | 5.13 | 7.74 | -2.90 | -12.8 |
| T3_ewmac_core12 | 34 | 4.97 | 7.44 | -3.06 | -8.1 |
| T6_ewmac_ext10 | 35 | 4.82 | 7.20 | -3.21 | -8.0 |
| T1_ewmac_core10 | 36 | 4.81 | 7.23 | -3.22 | -7.1 |
| R5_p1like | 37 | 4.80 | 6.62 | -3.23 | -7.3 |
| T4_tsmom_core12 | 38 | 4.76 | 7.19 | -3.27 | -10.0 |
| R5x_p1like_ext | 39 | 4.70 | 6.58 | -3.34 | -7.2 |
| K2_daa_core | 40 | 4.67 | 7.44 | -3.37 | -13.3 |
| R3_invvol_sma | 41 | 4.62 | 6.37 | -3.41 | -5.5 |
| T2_tsmom_core10 | 42 | 4.59 | 6.94 | -3.45 | -8.9 |
| R4_classrp_ts | 43 | 4.51 | 6.32 | -3.53 | -7.7 |
| K1x_vaa_ext | 44 | 4.28 | 7.21 | -3.76 | -12.3 |
| K1_vaa_core | 45 | 3.59 | 6.17 | -4.45 | -18.3 |
| K3x_baa_ext | 46 | 3.49 | 5.87 | -4.54 | -18.0 |
| K3_baa_core | 47 | 3.30 | 5.30 | -4.73 | -13.9 |


And on 2007–2023 only, when yields were low (a fresh account started in January 2007):

**Table D2. Low-yield era only: fresh start 2007-01 to 2023-12 (204 months; cash-ETF return averaged 2.7% a year), all 47 trials, ranked by CAGR after costs and Regime-B tax at A$25,000**

| Trial | Net 5k | After-tax B 5k | Net 25k | MaxDD 25k | Sharpe 25k | Vol 25k | After-tax B 25k | Net 100k | After-tax B 100k | vs S1 after tax 25k |
|---|---|---|---|---|---|---|---|---|---|---|
| G4_gem6 | 9.40 | 6.59 | 9.61 | -23.4 | 0.65 | 10.86 | 6.80 | 9.61 | 6.80 | 0.79 |
| M3_cape_trend | 8.06 | 6.38 | 8.34 | -27.1 | 0.60 | 9.55 | 6.60 | 8.31 | 6.59 | 0.59 |
| S2_world100 | 7.57 | 6.19 | 7.57 | -37.9 | 0.44 | 11.87 | 6.19 | 7.57 | 6.19 | 0.17 |
| F1_momg10 | 6.54 | 5.62 | 7.09 | -40.2 | 0.41 | 11.59 | 6.06 | 7.11 | 6.08 | 0.04 |
| H2_volswitch | 6.83 | 5.39 | 7.58 | -26.5 | 0.50 | 10.21 | 6.06 | 7.65 | 6.11 | 0.04 |
| S3_dhhf3763 | 7.07 | 6.02 | 7.08 | -40.0 | 0.41 | 11.65 | 6.03 | 7.08 | 6.03 | 0.01 |
| S1_4060 | 7.03 | 6.00 | 7.04 | -40.4 | 0.41 | 11.70 | 6.02 | 7.04 | 6.02 | 0.00 |
| F2_momau10 | 6.69 | 5.67 | 7.03 | -39.8 | 0.41 | 11.53 | 6.00 | 7.11 | 6.05 | -0.01 |
| M1_curve | 6.42 | 5.33 | 7.27 | -30.5 | 0.46 | 10.45 | 5.95 | 7.24 | 5.93 | -0.07 |
| S3x_dhhf_ext | 6.53 | 5.59 | 6.83 | -40.8 | 0.39 | 11.58 | 5.84 | 6.91 | 5.90 | -0.18 |
| S5_div | 4.74 | 4.03 | 7.01 | -11.6 | 0.66 | 6.49 | 5.75 | 6.98 | 5.75 | -0.27 |
| S2b_au100 | 6.15 | 5.74 | 6.15 | -48.3 | 0.30 | 14.77 | 5.74 | 6.15 | 5.74 | -0.28 |
| H3_volmanaged | 6.61 | 5.59 | 6.72 | -33.9 | 0.41 | 10.71 | 5.60 | 6.85 | 5.68 | -0.41 |
| L1_cashetf | 6.66 | 5.24 | 6.91 | -19.4 | 0.48 | 9.19 | 5.51 | 6.92 | 5.52 | -0.50 |
| M1b_curve12 | 6.14 | 5.00 | 6.68 | -23.8 | 0.46 | 8.98 | 5.49 | 6.68 | 5.47 | -0.53 |
| H1b_hmm_own | 6.32 | 5.39 | 6.41 | -36.3 | 0.39 | 10.31 | 5.33 | 6.48 | 5.38 | -0.69 |
| S4_6040 | 6.02 | 4.90 | 6.36 | -17.3 | 0.51 | 7.29 | 5.17 | 6.52 | 5.32 | -0.84 |
| L1_spec | 6.14 | 4.97 | 6.28 | -19.4 | 0.41 | 9.29 | 5.12 | 6.28 | 5.12 | -0.90 |
| K4_paa_core | 6.33 | 4.20 | 7.26 | -15.2 | 0.61 | 7.52 | 4.91 | 7.43 | 5.08 | -1.11 |
| G1_gem12 | 6.53 | 4.70 | 6.73 | -22.6 | 0.41 | 10.58 | 4.89 | 6.73 | 4.89 | -1.12 |
| G2_gem12_2bond | 6.31 | 4.46 | 6.64 | -23.7 | 0.41 | 10.48 | 4.79 | 6.65 | 4.79 | -1.23 |
| T5_ewmac_eq2_12 | 5.42 | 3.71 | 6.77 | -10.6 | 0.59 | 6.94 | 4.79 | 6.95 | 4.96 | -1.23 |
| E3_slow3 | 5.05 | 4.24 | 6.16 | -9.9 | 0.63 | 5.42 | 4.68 | 6.43 | 4.89 | -1.33 |
| G3_gem_blend | 6.17 | 4.44 | 6.37 | -22.4 | 0.38 | 10.68 | 4.65 | 6.37 | 4.65 | -1.37 |
| K4x_paa_ext | 4.91 | 2.90 | 7.00 | -17.7 | 0.65 | 6.64 | 4.58 | 7.55 | 5.08 | -1.44 |
| R2_classrp | 4.43 | 3.39 | 5.75 | -11.0 | 0.63 | 4.76 | 4.52 | 6.07 | 4.71 | -1.50 |
| M2_cape_step | 6.16 | 4.84 | 5.74 | -26.1 | 0.43 | 7.16 | 4.47 | 5.75 | 4.48 | -1.54 |
| M2b_cape_lin | 6.47 | 5.21 | 5.56 | -27.8 | 0.40 | 7.41 | 4.41 | 5.51 | 4.37 | -1.61 |
| H1_hmm_us | 4.16 | 3.40 | 5.48 | -27.9 | 0.31 | 9.80 | 4.35 | 5.63 | 4.50 | -1.67 |
| R1_invvol | 5.13 | 3.87 | 5.31 | -12.4 | 0.55 | 4.67 | 4.21 | 5.64 | 4.36 | -1.81 |
| K2x_daa_ext | 3.98 | 1.25 | 6.72 | -14.5 | 0.67 | 5.98 | 3.91 | 7.26 | 4.43 | -2.10 |
| T3_ewmac_core12 | 4.45 | 2.78 | 5.79 | -8.1 | 0.59 | 5.20 | 3.75 | 6.40 | 4.29 | -2.26 |
| R5_p1like | 2.88 | 2.07 | 5.15 | -7.3 | 0.55 | 4.42 | 3.75 | 5.54 | 4.06 | -2.26 |
| E1_six | 4.85 | 3.62 | 5.45 | -10.5 | 0.47 | 5.94 | 3.72 | 5.88 | 4.07 | -2.30 |
| T4_tsmom_core12 | 4.56 | 2.89 | 5.60 | -10.0 | 0.51 | 5.74 | 3.63 | 6.09 | 4.09 | -2.39 |
| T1_ewmac_core10 | 4.41 | 2.72 | 5.49 | -7.1 | 0.57 | 4.89 | 3.53 | 6.17 | 4.12 | -2.48 |
| R5x_p1like_ext | 0.83 | 0.47 | 4.95 | -7.2 | 0.52 | 4.25 | 3.53 | 5.54 | 3.99 | -2.49 |
| T2_tsmom_core10 | 4.56 | 2.91 | 5.31 | -8.9 | 0.49 | 5.32 | 3.45 | 5.84 | 3.94 | -2.57 |
| E2_mom3 | 2.97 | 1.21 | 5.37 | -12.8 | 0.45 | 6.00 | 3.40 | 5.60 | 3.60 | -2.62 |
| T6_ewmac_ext10 | 3.24 | 1.98 | 5.22 | -8.0 | 0.53 | 4.70 | 3.34 | 6.15 | 4.10 | -2.68 |
| R3_invvol_sma | 1.87 | 1.12 | 4.55 | -5.2 | 0.50 | 3.65 | 3.32 | 4.99 | 3.68 | -2.69 |
| R4_classrp_ts | 2.64 | 1.71 | 4.55 | -7.0 | 0.44 | 4.23 | 3.29 | 4.78 | 3.47 | -2.72 |
| K2_daa_core | 4.34 | 2.03 | 5.37 | -13.3 | 0.43 | 6.29 | 3.22 | 5.55 | 3.40 | -2.80 |
| K3_baa_core | 1.94 | 0.39 | 3.88 | -12.6 | 0.18 | 7.76 | 2.27 | 3.91 | 2.31 | -3.75 |
| K3x_baa_ext | 0.50 | -1.22 | 3.83 | -18.0 | 0.17 | 8.04 | 2.05 | 3.91 | 2.14 | -3.96 |
| K1_vaa_core | 2.89 | 1.02 | 3.59 | -18.3 | 0.14 | 7.89 | 1.70 | 3.59 | 1.70 | -4.31 |
| K1x_vaa_ext | 2.60 | 0.78 | 3.30 | -12.3 | 0.12 | 6.37 | 1.46 | 3.30 | 1.46 | -4.55 |


The order barely moves across sizes, windows and regimes: static equity mixes and the momentum-sleeve statics on top; M3 next; then the two-sleeve overlays and L1; then the static mixes with bonds; then everything that trades many sleeves monthly. In 2007–2023 the six-month dual momentum rule G4 tops the table while its 12-month sibling G1 is 1.1 points *below* 40/60 in the same window. That is what noise looks like.

## 4. What beats what, with confidence

### 4.1 Against static 40/60

**Table F1. Paired stationary block bootstrap (mean block 12 months, 10,000 paths) of differences vs static 40/60, net of costs at A$25,000, 1976-2023. dMaxDD positive = shallower drawdown. "better/worse" = 90% CI excludes zero; otherwise noise**

| Trial | dCAGR pp | dCAGR pp 90% CI | dCAGR pp sig | dSharpe | dSharpe 90% CI | dSharpe sig | dMaxDD pp | dMaxDD pp 90% CI | dMaxDD pp sig |
|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | – | – | – | – | – | – | – | – | – |
| S2_world100 | -0.05 | [-1.54, +1.48] | noise | -0.03 | [-0.13, +0.07] | noise | -6.3 | [-13.93, +7.00] | noise |
| S2b_au100 | -0.37 | [-2.68, +1.90] | noise | -0.08 | [-0.23, +0.07] | noise | -8.2 | [-18.83, +0.89] | noise |
| S3_dhhf3763 | +0.10 | [-0.10, +0.32] | noise | +0.01 | [-0.01, +0.02] | noise | -0.1 | [-2.67, +0.58] | noise |
| S4_6040 | -0.85 | [-2.56, +0.87] | noise | +0.07 | [-0.01, +0.16] | noise | +21.5 | [+9.20, +29.54] | better |
| S5_div | -1.15 | [-2.99, +0.76] | noise | +0.04 | [-0.07, +0.16] | noise | +24.8 | [+9.83, +33.50] | better |
| L1_spec | -1.05 | [-2.61, +0.67] | noise | -0.05 | [-0.17, +0.09] | noise | +13.5 | [-1.74, +24.47] | noise |
| L1_cashetf | +0.20 | [-1.48, +2.06] | noise | +0.06 | [-0.07, +0.20] | noise | +13.0 | [+0.09, +26.64] | better |
| T1_ewmac_core10 | -2.61 | [-5.78, +0.67] | noise | +0.00 | [-0.24, +0.26] | noise | +28.1 | [+15.53, +40.45] | better |
| T2_tsmom_core10 | -2.14 | [-5.16, +0.98] | noise | +0.04 | [-0.18, +0.28] | noise | +25.5 | [+13.55, +38.36] | better |
| T3_ewmac_core12 | -2.43 | [-5.58, +0.84] | noise | +0.02 | [-0.22, +0.28] | noise | +29.6 | [+15.42, +40.95] | better |
| T4_tsmom_core12 | -1.91 | [-4.85, +1.17] | noise | +0.03 | [-0.18, +0.27] | noise | +22.5 | [+10.65, +36.21] | better |
| T5_ewmac_eq2_12 | -1.29 | [-3.53, +1.16] | noise | -0.01 | [-0.19, +0.17] | noise | +15.3 | [+3.39, +32.02] | better |
| G1_gem12 | -0.48 | [-3.39, +2.51] | noise | -0.05 | [-0.26, +0.17] | noise | -1.5 | [-15.39, +20.47] | noise |
| G2_gem12_2bond | -0.52 | [-3.42, +2.50] | noise | -0.05 | [-0.26, +0.17] | noise | -1.5 | [-15.55, +20.46] | noise |
| G3_gem_blend | -0.74 | [-3.68, +2.36] | noise | -0.07 | [-0.28, +0.15] | noise | -1.5 | [-14.91, +20.31] | noise |
| G4_gem6 | -1.00 | [-3.98, +2.17] | noise | -0.09 | [-0.30, +0.15] | noise | -1.5 | [-14.56, +19.86] | noise |
| K1_vaa_core | -3.44 | [-7.36, +0.70] | noise | -0.24 | [-0.54, +0.09] | noise | -1.5 | [-15.34, +25.38] | noise |
| K2_daa_core | -0.66 | [-3.72, +2.71] | noise | +0.06 | [-0.17, +0.31] | noise | +17.6 | [+5.76, +33.30] | better |
| K3_baa_core | -2.07 | [-5.70, +1.78] | noise | -0.09 | [-0.39, +0.19] | noise | +15.8 | [+3.10, +30.79] | better |
| K4_paa_core | +0.05 | [-2.91, +3.33] | noise | +0.04 | [-0.17, +0.28] | noise | +9.6 | [-2.26, +28.53] | noise |
| R1_invvol | -3.03 | [-6.20, +0.16] | noise | -0.04 | [-0.29, +0.21] | noise | +27.0 | [+12.54, +40.63] | better |
| R2_classrp | -3.25 | [-6.43, +0.05] | noise | -0.09 | [-0.34, +0.17] | noise | +29.3 | [+14.18, +41.74] | better |
| R3_invvol_sma | -3.13 | [-6.47, +0.30] | noise | +0.00 | [-0.24, +0.25] | noise | +34.6 | [+19.55, +45.64] | better |
| R4_classrp_ts | -2.68 | [-6.20, +0.95] | noise | +0.13 | [-0.14, +0.41] | noise | +32.4 | [+17.63, +44.12] | better |
| R5_p1like | -2.25 | [-4.97, +0.63] | noise | +0.02 | [-0.16, +0.22] | noise | +24.0 | [+12.17, +38.09] | better |
| H1_hmm_us | -1.12 | [-2.00, -0.29] | worse | -0.06 | [-0.12, -0.00] | worse | +9.0 | [-0.65, +12.71] | noise |
| H1b_hmm_own | -0.51 | [-1.05, -0.02] | worse | -0.02 | [-0.04, +0.01] | noise | +3.9 | [+0.50, +5.91] | better |
| H2_volswitch | -0.48 | [-1.36, +0.39] | noise | -0.01 | [-0.06, +0.05] | noise | +5.9 | [-1.89, +13.94] | noise |
| H3_volmanaged | -0.68 | [-1.45, +0.06] | noise | -0.01 | [-0.05, +0.03] | noise | +6.1 | [+0.18, +10.30] | better |
| M1_curve | -0.40 | [-1.37, +0.57] | noise | -0.00 | [-0.07, +0.06] | noise | +10.1 | [-0.41, +12.59] | noise |
| M1b_curve12 | -0.38 | [-1.67, +0.91] | noise | +0.05 | [-0.03, +0.12] | noise | +14.9 | [+2.95, +20.89] | better |
| M2_cape_step | -1.24 | [-2.70, +0.23] | noise | -0.04 | [-0.12, +0.05] | noise | +13.0 | [+1.15, +19.44] | better |
| M2b_cape_lin | -0.81 | [-2.20, +0.60] | noise | +0.02 | [-0.06, +0.09] | noise | +12.9 | [+6.15, +20.61] | better |
| M3_cape_trend | +0.57 | [-0.24, +1.46] | noise | +0.07 | [+0.01, +0.13] | better | +13.0 | [+0.89, +16.87] | better |
| F1_momg10 | +0.19 | [-0.05, +0.44] | noise | +0.01 | [-0.01, +0.03] | noise | +0.3 | [-1.37, +1.94] | noise |
| E1_six | -1.72 | [-3.86, +0.55] | noise | -0.01 | [-0.15, +0.14] | noise | +16.9 | [+5.02, +33.75] | better |
| E2_mom3 | -1.95 | [-4.75, +1.06] | noise | -0.07 | [-0.28, +0.18] | noise | +8.3 | [-3.55, +31.78] | noise |
| E3_slow3 | -2.07 | [-4.36, +0.27] | noise | +0.03 | [-0.09, +0.16] | noise | +29.2 | [+15.07, +39.59] | better |


- **Return:** every 90% interval on the CAGR difference includes zero except two HMM variants, which are *worse*. For most contestants the interval is ±1.5 to ±3.5 points wide. 48 years cannot tell a 1-point edge from none.
- **Sharpe:** one interval excludes zero on the good side: M3, +0.07 [+0.01, +0.13]. One in 38 at the 10% level is fewer than chance alone would produce.
- **Drawdown:** 23 of 38 have a shallower maximum drawdown with an interval that excludes zero. Every one of them holds bonds, gold or cash for a large share of the time. Dual momentum and VAA do not reduce drawdown at all (October 1987 hit them fully invested).

After tax (Table F4 in the tables file) the picture hardens: 27 of 38 have a CAGR difference that is *significantly negative*, including every trend, risk-parity and ensemble rule (T1: −4.9 points [−8.1, −1.5]).

### 4.2 Against L1

**Table F2. As F1, differences vs L1 (cash-ETF variant)**

| Trial | dCAGR pp | dCAGR pp 90% CI | dCAGR pp sig | dSharpe | dSharpe 90% CI | dSharpe sig | dMaxDD pp | dMaxDD pp 90% CI | dMaxDD pp sig |
|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | -0.20 | [-2.06, +1.48] | noise | -0.06 | [-0.20, +0.07] | noise | -13.0 | [-26.64, -0.09] | worse |
| S2_world100 | -0.24 | [-2.78, +2.14] | noise | -0.09 | [-0.27, +0.08] | noise | -19.3 | [-32.24, +2.74] | noise |
| S2b_au100 | -0.57 | [-3.34, +2.04] | noise | -0.14 | [-0.32, +0.04] | noise | -21.3 | [-35.77, -9.11] | worse |
| S3_dhhf3763 | -0.09 | [-2.03, +1.63] | noise | -0.05 | [-0.20, +0.08] | noise | -13.1 | [-27.19, -0.10] | worse |
| S4_6040 | -1.05 | [-2.71, +0.58] | noise | +0.01 | [-0.12, +0.15] | noise | +8.5 | [-0.93, +13.50] | noise |
| S5_div | -1.35 | [-3.03, +0.27] | noise | -0.02 | [-0.16, +0.13] | noise | +11.8 | [+0.54, +16.56] | better |
| L1_spec | -1.24 | [-1.83, -0.72] | worse | -0.10 | [-0.15, -0.06] | worse | +0.5 | [-6.36, +0.57] | noise |
| L1_cashetf | – | – | – | – | – | – | – | – | – |
| T1_ewmac_core10 | -2.81 | [-5.40, -0.37] | worse | -0.06 | [-0.27, +0.16] | noise | +15.1 | [+7.23, +22.57] | better |
| T2_tsmom_core10 | -2.34 | [-4.73, -0.03] | worse | -0.02 | [-0.20, +0.17] | noise | +12.5 | [+5.80, +20.07] | better |
| T3_ewmac_core12 | -2.63 | [-5.20, -0.18] | worse | -0.03 | [-0.25, +0.18] | noise | +16.6 | [+6.31, +23.67] | better |
| T4_tsmom_core12 | -2.10 | [-4.40, +0.14] | noise | -0.03 | [-0.20, +0.17] | noise | +9.5 | [+4.29, +17.18] | better |
| T5_ewmac_eq2_12 | -1.49 | [-2.93, -0.10] | worse | -0.07 | [-0.19, +0.04] | noise | +2.2 | [+0.58, +11.15] | better |
| G1_gem12 | -0.67 | [-3.05, +1.62] | noise | -0.11 | [-0.28, +0.07] | noise | -14.5 | [-19.69, +0.50] | noise |
| G2_gem12_2bond | -0.71 | [-3.08, +1.55] | noise | -0.11 | [-0.28, +0.07] | noise | -14.5 | [-20.00, +0.37] | noise |
| G3_gem_blend | -0.93 | [-3.16, +1.26] | noise | -0.13 | [-0.29, +0.04] | noise | -14.5 | [-18.99, -0.03] | worse |
| G4_gem6 | -1.19 | [-3.66, +1.25] | noise | -0.15 | [-0.33, +0.04] | noise | -14.5 | [-18.94, -0.36] | worse |
| K1_vaa_core | -3.64 | [-6.71, -0.60] | worse | -0.30 | [-0.55, -0.04] | worse | -14.5 | [-19.22, +5.63] | noise |
| K2_daa_core | -0.85 | [-3.13, +1.48] | noise | +0.01 | [-0.18, +0.18] | noise | +4.6 | [+1.39, +13.36] | better |
| K3_baa_core | -2.26 | [-5.27, +0.73] | noise | -0.15 | [-0.42, +0.09] | noise | +2.8 | [-2.47, +11.11] | noise |
| K4_paa_core | -0.15 | [-2.40, +2.22] | noise | -0.02 | [-0.18, +0.15] | noise | -3.4 | [-4.85, +8.16] | noise |
| R1_invvol | -3.23 | [-5.98, -0.65] | worse | -0.10 | [-0.35, +0.15] | noise | +14.0 | [+3.54, +24.69] | better |
| R2_classrp | -3.45 | [-6.19, -0.87] | worse | -0.15 | [-0.39, +0.09] | noise | +16.2 | [+5.04, +25.61] | better |
| R3_invvol_sma | -3.33 | [-6.10, -0.72] | worse | -0.05 | [-0.27, +0.16] | noise | +21.6 | [+9.83, +29.02] | better |
| R4_classrp_ts | -2.87 | [-5.77, -0.11] | worse | +0.07 | [-0.17, +0.31] | noise | +19.4 | [+8.38, +27.59] | better |
| R5_p1like | -2.44 | [-4.49, -0.50] | worse | -0.04 | [-0.16, +0.10] | noise | +11.0 | [+7.04, +18.73] | better |
| H1_hmm_us | -1.32 | [-2.81, +0.09] | noise | -0.12 | [-0.25, +0.00] | noise | -4.0 | [-19.25, +3.77] | noise |
| H1b_hmm_own | -0.71 | [-2.39, +0.84] | noise | -0.08 | [-0.22, +0.06] | noise | -9.1 | [-22.90, +3.68] | noise |
| H2_volswitch | -0.68 | [-2.30, +0.86] | noise | -0.07 | [-0.21, +0.06] | noise | -7.2 | [-18.78, +3.66] | noise |
| H3_volmanaged | -0.87 | [-2.58, +0.73] | noise | -0.07 | [-0.23, +0.07] | noise | -6.9 | [-20.78, +8.31] | noise |
| M1_curve | -0.60 | [-2.27, +0.95] | noise | -0.06 | [-0.20, +0.07] | noise | -2.9 | [-17.79, +3.40] | noise |
| M1b_curve12 | -0.58 | [-2.21, +0.98] | noise | -0.01 | [-0.17, +0.13] | noise | +1.8 | [-11.83, +10.89] | noise |
| M2_cape_step | -1.44 | [-2.89, -0.02] | worse | -0.10 | [-0.22, +0.03] | noise | -0.0 | [-11.72, +5.48] | noise |
| M2b_cape_lin | -1.00 | [-2.52, +0.50] | noise | -0.04 | [-0.19, +0.09] | noise | -0.1 | [-11.09, +11.13] | noise |
| M3_cape_trend | +0.37 | [-0.83, +1.51] | noise | +0.01 | [-0.09, +0.11] | noise | -0.0 | [-13.33, +3.85] | noise |
| F1_momg10 | -0.01 | [-1.87, +1.66] | noise | -0.05 | [-0.19, +0.08] | noise | -12.7 | [-26.18, -0.66] | worse |
| E1_six | -1.91 | [-3.48, -0.41] | worse | -0.07 | [-0.18, +0.04] | noise | +3.9 | [+3.33, +12.75] | better |
| E2_mom3 | -2.14 | [-4.20, -0.13] | worse | -0.13 | [-0.29, +0.05] | noise | -4.7 | [-5.33, +11.18] | noise |
| E3_slow3 | -2.26 | [-4.24, -0.42] | worse | -0.03 | [-0.17, +0.12] | noise | +16.2 | [+5.74, +22.09] | better |


Nothing has a better return or Sharpe than L1 (cash-ETF version) with confidence. Fifteen contestants have significantly lower returns. Fourteen have significantly shallower drawdowns; nearly all hold bonds and gold. L1 as specified (idle cash at 0%) is significantly worse than L1 with a cash ETF: −1.24 points a year [−1.83, −0.72]. That confirms report 36's point that what OFF money earns matters more than the rule.

### 4.3 Against the static diversified mix: does the algorithm add anything?

**Table F6. As F1, differences vs the static diversified mix S5 (55 equity / 30 bonds / 15 gold): does the algorithm add anything beyond the asset mix?**

| Trial | dCAGR pp | dCAGR pp 90% CI | dCAGR pp sig | dSharpe | dSharpe 90% CI | dSharpe sig | dMaxDD pp | dMaxDD pp 90% CI | dMaxDD pp sig |
|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | +1.15 | [-0.76, +2.99] | noise | -0.04 | [-0.16, +0.07] | noise | -24.8 | [-33.50, -9.83] | worse |
| S2_world100 | +1.11 | [-1.53, +3.74] | noise | -0.07 | [-0.23, +0.08] | noise | -31.1 | [-38.79, -8.84] | worse |
| S2b_au100 | +0.78 | [-1.85, +3.34] | noise | -0.12 | [-0.29, +0.05] | noise | -33.0 | [-44.02, -16.99] | worse |
| S3_dhhf3763 | +1.26 | [-0.74, +3.19] | noise | -0.04 | [-0.16, +0.08] | noise | -24.9 | [-34.38, -10.10] | worse |
| S4_6040 | +0.30 | [-0.52, +1.07] | noise | +0.03 | [-0.05, +0.12] | noise | -3.3 | [-6.17, +2.62] | noise |
| S5_div | – | – | – | – | – | – | – | – | – |
| L1_spec | +0.11 | [-1.62, +1.93] | noise | -0.09 | [-0.22, +0.04] | noise | -11.3 | [-19.23, -2.93] | worse |
| L1_cashetf | +1.35 | [-0.27, +3.03] | noise | +0.02 | [-0.13, +0.16] | noise | -11.8 | [-16.56, -0.54] | worse |
| T1_ewmac_core10 | -1.46 | [-3.24, +0.28] | noise | -0.04 | [-0.24, +0.17] | noise | +3.3 | [+2.69, +11.34] | better |
| T2_tsmom_core10 | -0.99 | [-2.64, +0.73] | noise | -0.01 | [-0.20, +0.21] | noise | +0.7 | [+0.12, +9.59] | better |
| T3_ewmac_core12 | -1.28 | [-3.05, +0.46] | noise | -0.02 | [-0.22, +0.19] | noise | +4.8 | [+2.16, +11.76] | better |
| T4_tsmom_core12 | -0.75 | [-2.38, +0.95] | noise | -0.01 | [-0.21, +0.20] | noise | -2.3 | [-2.97, +7.86] | noise |
| T5_ewmac_eq2_12 | -0.14 | [-1.82, +1.52] | noise | -0.06 | [-0.23, +0.12] | noise | -9.5 | [-11.89, +5.15] | noise |
| G1_gem12 | +0.68 | [-1.83, +3.11] | noise | -0.09 | [-0.29, +0.11] | noise | -26.3 | [-32.31, -5.05] | worse |
| G2_gem12_2bond | +0.64 | [-1.86, +3.11] | noise | -0.10 | [-0.29, +0.11] | noise | -26.3 | [-32.75, -5.11] | worse |
| G3_gem_blend | +0.42 | [-2.04, +2.87] | noise | -0.11 | [-0.31, +0.09] | noise | -26.3 | [-31.76, -5.35] | worse |
| G4_gem6 | +0.16 | [-2.32, +2.63] | noise | -0.13 | [-0.33, +0.08] | noise | -26.3 | [-31.41, -5.92] | worse |
| K1_vaa_core | -2.29 | [-5.10, +0.63] | noise | -0.28 | [-0.56, +0.02] | noise | -26.3 | [-32.41, +0.03] | noise |
| K2_daa_core | +0.50 | [-1.49, +2.64] | noise | +0.02 | [-0.20, +0.24] | noise | -7.1 | [-8.56, +6.22] | noise |
| K3_baa_core | -0.91 | [-3.36, +1.61] | noise | -0.13 | [-0.41, +0.12] | noise | -9.0 | [-12.87, +3.71] | noise |
| K4_paa_core | +1.21 | [-0.75, +3.38] | noise | +0.00 | [-0.18, +0.19] | noise | -15.2 | [-16.67, +1.73] | noise |
| R1_invvol | -1.87 | [-3.59, -0.25] | worse | -0.08 | [-0.28, +0.10] | noise | +2.3 | [-1.10, +12.28] | noise |
| R2_classrp | -2.10 | [-3.68, -0.54] | worse | -0.14 | [-0.31, +0.04] | noise | +4.5 | [+0.82, +12.98] | better |
| R3_invvol_sma | -1.98 | [-3.80, -0.18] | worse | -0.04 | [-0.23, +0.14] | noise | +9.8 | [+6.13, +16.60] | better |
| R4_classrp_ts | -1.52 | [-3.47, +0.51] | noise | +0.09 | [-0.15, +0.32] | noise | +7.6 | [+4.03, +15.38] | better |
| R5_p1like | -1.09 | [-2.37, +0.31] | noise | -0.02 | [-0.17, +0.14] | noise | -0.7 | [-0.77, +9.71] | noise |
| H1_hmm_us | +0.03 | [-1.53, +1.65] | noise | -0.10 | [-0.22, +0.01] | noise | -15.8 | [-26.11, -6.66] | worse |
| H1b_hmm_own | +0.64 | [-0.96, +2.18] | noise | -0.06 | [-0.17, +0.05] | noise | -20.9 | [-29.44, -7.40] | worse |
| H2_volswitch | +0.67 | [-0.82, +2.15] | noise | -0.05 | [-0.16, +0.05] | noise | -18.9 | [-25.10, -5.95] | worse |
| H3_volmanaged | +0.48 | [-1.01, +1.94] | noise | -0.05 | [-0.18, +0.06] | noise | -18.7 | [-27.32, -3.64] | worse |
| M1_curve | +0.75 | [-0.90, +2.36] | noise | -0.04 | [-0.17, +0.08] | noise | -14.7 | [-24.73, -5.50] | worse |
| M1b_curve12 | +0.77 | [-0.63, +2.12] | noise | +0.01 | [-0.14, +0.14] | noise | -9.9 | [-17.70, -0.50] | worse |
| M2_cape_step | -0.09 | [-1.27, +1.17] | noise | -0.08 | [-0.19, +0.03] | noise | -11.8 | [-18.74, -3.41] | worse |
| M2b_cape_lin | +0.35 | [-0.82, +1.62] | noise | -0.03 | [-0.14, +0.08] | noise | -11.9 | [-16.74, -1.46] | worse |
| M3_cape_trend | +1.72 | [+0.31, +3.17] | better | +0.02 | [-0.07, +0.12] | noise | -11.8 | [-20.14, -5.21] | worse |
| F1_momg10 | +1.34 | [-0.57, +3.17] | noise | -0.03 | [-0.15, +0.08] | noise | -24.4 | [-33.16, -9.55] | worse |
| E1_six | -0.56 | [-1.55, +0.45] | noise | -0.06 | [-0.18, +0.07] | noise | -7.9 | [-8.69, +6.60] | noise |
| E2_mom3 | -0.79 | [-2.43, +0.89] | noise | -0.11 | [-0.30, +0.10] | noise | -16.5 | [-17.57, +5.75] | noise |
| E3_slow3 | -0.91 | [-1.84, -0.06] | worse | -0.01 | [-0.09, +0.06] | noise | +4.5 | [+1.94, +9.58] | better |


This is the comparison that matters for section 26 and for P1.

- The trend ensembles T1–T3 reduce maximum drawdown by a further 1–5 points against S5 (the intervals exclude zero), for 1.0–1.5 points a year less return before tax (intervals include zero) and 2.5–2.8 points less after tax.
- **The spec's P1 analogue (R5) does not reduce drawdown against its static parent at all** (−0.7 points, noise) and returns 1.1 points a year less before tax. Card H13 requires a drawdown at least a third lower and a return no more than 1 point lower. On these proxies **neither leg is met**. This is a five-sleeve version on substitute data, so it is a warning, not a card result.
- Risk parity with trend (R3, R4) is the only group with a clear extra drawdown benefit (8–10 points shallower, to −5.5% and −7.7%). It pays 1.5–2.0 points a year for it before tax.
- No overlay on 40/60 comes close to S5's drawdown; all are significantly deeper.

### 4.4 Multiple-testing control

**Table G7. White reality check: is the best of all trials better than a vol-matched 40/60 after allowing for the number of trials?**

| Series | Sample | Best | Best t-stat | 95% critical (max of N) | Reality-check p | Survivors at 10% |
|---|---|---|---|---|---|---|
| paper | 1976-2023 (39) | M3_cape_trend | 2.31 | 3.18 | 0.249 | none |
| paper | 1991-2023 (47) | K2x_daa_ext | 3.89 | 3.22 | 0.012 | K2x_daa_ext, M3_cape_trend, E3_slow3 |
| paper_delay1 | 1976-2023 (39) | M1b_curve12 | 1.77 | 3.11 | 0.516 | none |
| paper_delay1 | 1991-2023 (47) | E1_six | 2.34 | 3.13 | 0.219 | none |
| net_100k | 1976-2023 (39) | M3_cape_trend | 2.34 | 3.19 | 0.238 | none |
| net_100k | 1991-2023 (47) | S4_6040 | 2.88 | 3.26 | 0.097 | S4_6040 |
| net_25k | 1976-2023 (39) | M3_cape_trend | 2.13 | 3.21 | 0.328 | none |
| net_25k | 1991-2023 (47) | S4_6040 | 2.73 | 3.27 | 0.128 | none |
| net_5k | 1976-2023 (39) | M3_cape_trend | 1.68 | 3.34 | 0.626 | none |
| net_5k | 1991-2023 (47) | M3_cape_trend | 2.33 | 3.44 | 0.307 | none |
| atB_25k | 1976-2023 (39) | F1_momg10 | 0.86 | 3.01 | 0.891 | none |
| atB_25k | 1991-2023 (47) | F1_momg10 | 1.28 | 3.11 | 0.722 | none |


**Table G1. Multiple-testing control, net of costs at A$25,000, 1976-2023 (39 long-sample trials). IR = information ratio of the strategy against a 40/60 + cash blend of the same volatility. DSR = deflated Sharpe ratio (probability the true value exceeds the expected maximum of N unskilled trials). RC adj. p = White reality-check p-value adjusted for all trials (single-step max-t, stationary bootstrap)**

| Trial | Sharpe | DSR (vs cash) | IR vs vol-matched 40/60 | PSR(IR>0), single test | DSR(IR), N=all | Reality-check stat | RC adj. p |
|---|---|---|---|---|---|---|---|
| M3_cape_trend | 0.47 | 0.983 | 0.31 | 0.987 | 0.620 | 2.13 | 0.328 |
| S4_6040 | 0.48 | 0.984 | 0.28 | 0.976 | 0.551 | 1.96 | 0.404 |
| M1b_curve12 | 0.46 | 0.983 | 0.17 | 0.888 | 0.260 | 1.20 | 0.796 |
| L1_cashetf | 0.47 | 0.980 | 0.13 | 0.823 | 0.179 | 0.92 | 0.902 |
| F1_momg10 | 0.42 | 0.964 | 0.12 | 0.800 | 0.163 | 0.85 | 0.921 |
| R4_classrp_ts | 0.54 | 0.996 | 0.12 | 0.793 | 0.152 | 0.81 | 0.931 |
| S5_div | 0.45 | 0.981 | 0.10 | 0.752 | 0.118 | 0.67 | 0.963 |
| S3_dhhf3763 | 0.41 | 0.962 | 0.08 | 0.713 | 0.099 | 0.56 | 0.976 |
| K2_daa_core | 0.47 | 0.986 | 0.08 | 0.708 | 0.094 | 0.54 | 0.979 |
| E3_slow3 | 0.44 | 0.975 | 0.07 | 0.692 | 0.091 | 0.50 | 0.983 |
| M2b_cape_lin | 0.42 | 0.969 | 0.06 | 0.661 | 0.077 | 0.41 | 0.989 |
| K4_paa_core | 0.45 | 0.977 | 0.05 | 0.639 | 0.067 | 0.35 | 0.992 |
| T2_tsmom_core10 | 0.44 | 0.972 | 0.04 | 0.611 | 0.059 | 0.28 | 0.995 |
| T4_tsmom_core12 | 0.44 | 0.966 | 0.03 | 0.587 | 0.053 | 0.22 | 0.996 |
| R5_p1like | 0.43 | 0.962 | 0.03 | 0.581 | 0.051 | 0.20 | 0.997 |
| T3_ewmac_core12 | 0.43 | 0.969 | 0.03 | 0.575 | 0.049 | 0.19 | 0.997 |
| R3_invvol_sma | 0.41 | 0.967 | 0.00 | 0.512 | 0.036 | 0.03 | 0.999 |
| T1_ewmac_core10 | 0.41 | 0.954 | 0.00 | 0.507 | 0.035 | 0.02 | 0.999 |
| S1_4060 | 0.41 | 0.958 | 0.00 | 0.500 | 0.033 | – | – |
| M1_curve | 0.41 | 0.957 | -0.01 | 0.473 | 0.029 | -0.07 | 1.000 |
| T5_ewmac_eq2_12 | 0.39 | 0.945 | -0.02 | 0.440 | 0.024 | -0.15 | 1.000 |
| E1_six | 0.39 | 0.938 | -0.03 | 0.417 | 0.021 | -0.21 | 1.000 |
| H2_volswitch | 0.40 | 0.954 | -0.03 | 0.405 | 0.019 | -0.24 | 1.000 |
| R1_invvol | 0.37 | 0.940 | -0.05 | 0.372 | 0.015 | -0.33 | 1.000 |
| S2_world100 | 0.38 | 0.952 | -0.06 | 0.345 | 0.013 | -0.40 | 1.000 |
| G1_gem12 | 0.35 | 0.909 | -0.07 | 0.320 | 0.011 | -0.47 | 1.000 |
| G2_gem12_2bond | 0.35 | 0.907 | -0.07 | 0.314 | 0.010 | -0.49 | 1.000 |
| H3_volmanaged | 0.40 | 0.955 | -0.07 | 0.305 | 0.010 | -0.52 | 1.000 |
| K3_baa_core | 0.32 | 0.885 | -0.08 | 0.282 | 0.008 | -0.58 | 1.000 |
| G3_gem_blend | 0.34 | 0.891 | -0.09 | 0.262 | 0.007 | -0.64 | 1.000 |
| E2_mom3 | 0.33 | 0.874 | -0.09 | 0.260 | 0.007 | -0.64 | 1.000 |
| R2_classrp | 0.31 | 0.888 | -0.10 | 0.248 | 0.006 | -0.68 | 1.000 |
| L1_spec | 0.36 | 0.928 | -0.10 | 0.242 | 0.006 | -0.70 | 1.000 |
| G4_gem6 | 0.32 | 0.873 | -0.11 | 0.223 | 0.005 | -0.77 | 1.000 |
| S2b_au100 | 0.33 | 0.889 | -0.12 | 0.197 | 0.003 | -0.84 | 1.000 |
| M2_cape_step | 0.37 | 0.928 | -0.12 | 0.199 | 0.004 | -0.85 | 1.000 |
| H1b_hmm_own | 0.39 | 0.950 | -0.17 | 0.113 | 0.001 | -1.18 | 1.000 |
| K1_vaa_core | 0.17 | 0.582 | -0.24 | 0.048 | 0.000 | -1.68 | 1.000 |
| H1_hmm_us | 0.35 | 0.917 | -0.26 | 0.036 | 0.000 | -1.79 | 1.000 |


- **Deflated Sharpe over cash** is above 0.95 for most trials. That says only that a long-only equity or bond portfolio beat cash over 48 years. It is the wrong test for "is this algorithm better than holding the assets".
- **Deflated Sharpe of the active return** is the right test. Maximum 0.62 (M3). The static 60/40 is second at 0.55. Nothing reaches 0.95.
- On the 1991+ window the top of the list after costs is the static 60/40, then M3, then the static S5 (Table G2 in the tables file). Two of the top three are not algorithms.

**Table G8 (selected rows). Probability of backtest overfitting (CSCV, 16 blocks, 12,870 splits), all trials in the sample. PBO = share of splits in which the in-sample winner lands in the bottom half out of sample. Slope = regression of out-of-sample on in-sample performance of the winner. Full table in the tables file**

| Series | Sample | Selection metric | N | PBO | IS→OOS slope | Most often the in-sample winner |
|---|---|---|---|---|---|---|
| paper | 1976–2023 | sharpe | 39 | 0.22 | -1.04 | K2_daa_core 31%; R4_classrp_ts 28%; T1_ewmac_core10 14% |
| paper | 1976–2023 | cagr | 39 | 0.52 | -0.97 | K2_daa_core 30%; K4_paa_core 18%; S2_world100 15% |
| paper | 1976–2023 | calmar | 39 | 0.02 | -0.74 | R3_invvol_sma 83%; T3_ewmac_core12 5%; R2_classrp 3% |
| paper | 1991–2023 | sharpe | 47 | 0.03 | -0.78 | K2x_daa_ext 80%; T6_ewmac_ext10 17%; K1x_vaa_ext 2% |
| paper | 1991–2023 | cagr | 47 | 0.36 | -1.28 | K2x_daa_ext 52%; K4x_paa_ext 9%; S2_world100 8% |
| paper | 1991–2023 | calmar | 47 | 0.02 | -0.54 | R3_invvol_sma 43%; K2x_daa_ext 28%; R5x_p1like_ext 9% |
| paper_delay1 | 1976–2023 | sharpe | 39 | 0.69 | -0.95 | R4_classrp_ts 28%; T3_ewmac_core12 25%; K3_baa_core 7% |
| paper_delay1 | 1976–2023 | cagr | 39 | 0.78 | -0.94 | K4_paa_core 22%; S2_world100 18%; F1_momg10 11% |
| paper_delay1 | 1976–2023 | calmar | 39 | 0.02 | -0.56 | R4_classrp_ts 43%; R3_invvol_sma 41%; R1_invvol 5% |
| paper_delay1 | 1991–2023 | sharpe | 47 | 0.42 | -0.90 | K4x_paa_ext 39%; K1x_vaa_ext 24%; T6_ewmac_ext10 8% |
| paper_delay1 | 1991–2023 | cagr | 47 | 0.54 | -1.23 | K1x_vaa_ext 36%; K4x_paa_ext 20%; S2_world100 9% |
| paper_delay1 | 1991–2023 | calmar | 47 | 0.15 | -0.31 | K1x_vaa_ext 23%; R4_classrp_ts 17%; R5x_p1like_ext 16% |
| net_100k | 1976–2023 | sharpe | 39 | 0.62 | -0.85 | R4_classrp_ts 40%; T1_ewmac_core10 9%; R3_invvol_sma 7% |
| net_100k | 1976–2023 | cagr | 39 | 0.70 | -0.95 | K4_paa_core 25%; S2_world100 21%; M3_cape_trend 13% |
| net_100k | 1976–2023 | calmar | 39 | 0.02 | -0.84 | R3_invvol_sma 76%; R4_classrp_ts 9%; T3_ewmac_core12 5% |
| net_100k | 1991–2023 | sharpe | 47 | 0.32 | -0.89 | K2x_daa_ext 39%; T6_ewmac_ext10 21%; K4x_paa_ext 16% |
| net_100k | 1991–2023 | cagr | 47 | 0.57 | -1.23 | K4x_paa_ext 20%; K2x_daa_ext 18%; S2b_au100 16% |
| net_100k | 1991–2023 | calmar | 47 | 0.10 | -0.68 | R3_invvol_sma 50%; K2x_daa_ext 18%; T6_ewmac_ext10 7% |
| net_25k | 1976–2023 | sharpe | 39 | 0.73 | -0.89 | R4_classrp_ts 34%; K2_daa_core 9%; S4_6040 7% |
| net_25k | 1976–2023 | cagr | 39 | 0.70 | -0.95 | S2_world100 22%; K4_paa_core 22%; M3_cape_trend 11% |
| net_25k | 1976–2023 | calmar | 39 | 0.02 | -0.72 | R3_invvol_sma 78%; R2_classrp 9%; T3_ewmac_core12 5% |
| net_25k | 1991–2023 | sharpe | 47 | 0.47 | -0.90 | K2x_daa_ext 38%; K4x_paa_ext 19%; S4_6040 11% |
| net_25k | 1991–2023 | cagr | 47 | 0.64 | -1.11 | S2b_au100 19%; G4_gem6 17%; K4x_paa_ext 13% |
| net_25k | 1991–2023 | calmar | 47 | 0.16 | -0.69 | R3_invvol_sma 50%; K2x_daa_ext 17%; R1_invvol 8% |
| net_5k | 1976–2023 | sharpe | 39 | 0.51 | -0.60 | L1_cashetf 22%; M1b_curve12 14%; M3_cape_trend 10% |
| net_5k | 1976–2023 | cagr | 39 | 0.51 | -0.80 | S2_world100 32%; S2b_au100 19%; L1_cashetf 12% |
| net_5k | 1976–2023 | calmar | 39 | 0.08 | -0.30 | R3_invvol_sma 34%; T1_ewmac_core10 34%; R2_classrp 14% |
| net_5k | 1991–2023 | sharpe | 47 | 0.72 | -0.65 | S4_6040 18%; T1_ewmac_core10 11%; G4_gem6 8% |
| net_5k | 1991–2023 | cagr | 47 | 0.39 | -0.94 | S2b_au100 33%; G4_gem6 24%; S2_world100 17% |
| net_5k | 1991–2023 | calmar | 47 | 0.27 | -0.38 | R5x_p1like_ext 33%; T1_ewmac_core10 23%; T6_ewmac_ext10 10% |
| atB_25k | 1976–2023 | sharpe | 39 | 0.15 | -0.71 | F1_momg10 25%; S2_world100 19%; S2b_au100 18% |
| atB_25k | 1976–2023 | cagr | 39 | 0.13 | -0.80 | S2_world100 36%; S2b_au100 33%; F1_momg10 15% |
| atB_25k | 1976–2023 | calmar | 39 | 0.07 | -1.00 | R3_invvol_sma 78%; R1_invvol 10%; R4_classrp_ts 10% |
| atB_25k | 1991–2023 | sharpe | 47 | 0.33 | -0.68 | S5_div 23%; S2b_au100 20%; S4_6040 14% |
| atB_25k | 1991–2023 | cagr | 47 | 0.30 | -0.83 | S2b_au100 48%; S2_world100 14%; F2_momau10 12% |
| atB_25k | 1991–2023 | calmar | 47 | 0.32 | -0.52 | R3_invvol_sma 41%; R1_invvol 17%; S5_div 9% |

- A PBO near or above 0.5 with a negative slope means that choosing the past winner is no better than choosing at random. That is the case for Sharpe and CAGR once costs or a one-month delay are included.
- Frictionless Sharpe on the 1991+ window shows a low PBO (0.03) because one rule, K2x, wins 80% of the splits. With a one-month delay the PBO is 0.42 and K2x is no longer the usual winner. The persistence was in the execution assumption.
- PBO for the return-to-drawdown ratio is 0.02–0.2. The winner is nearly always R3 (inverse volatility with a moving-average filter), the lowest-volatility rule in the set. Low volatility persists. That is information about the asset mix.

## 5. Episodes, holdout and the sub-studies

### 5.1 Crash episodes

Windows (first to last month): 1980-12 to 1982-07; 1987-10 to 1987-11; 1989-09 to 1990-12; 1994-02 to 1994-11; 2000-04 to 2003-03; 2007-11 to 2009-02; 2011-05 to 2011-09; 2015-05 to 2016-02; 2018-09 to 2018-12; 2020-02 to 2020-03; 2022-01 to 2022-09; 2025-02 to 2025-04.

**Table H1. Crash episodes: cumulative return %, net of costs at A$25,000 (window = first to last month shown in s5.1)**

| Trial | AU bear 1981-82 | Oct 1987 crash | 1990 recession | 1994 bond rout | tech bust (AUD) | GFC | 2011 euro crisis | 2015-16 whipsaw | Q4 2018 | COVID crash | 2022 stocks+bonds | Feb-Apr 2025 (holdout) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | -17.4 | -28.3 | -15.1 | -12.1 | -27.8 | -40.1 | -13.2 | -5.1 | -10.6 | -18.7 | -15.1 | -5.8 |
| S2_world100 | -3.3 | -19.0 | -13.3 | -9.7 | -43.5 | -33.9 | -11.4 | -1.8 | -11.2 | -13.9 | -16.9 | -6.6 |
| S2b_au100 | -34.8 | -39.3 | -17.6 | -14.8 | 0.5 | -48.4 | -15.4 | -10.7 | -9.7 | -27.9 | -11.1 | -4.0 |
| S3_dhhf3763 | -16.4 | -28.3 | -15.1 | -11.7 | -31.0 | -40.2 | -13.1 | -4.5 | -10.7 | -17.8 | -15.4 | -6.0 |
| S3x_dhhf_ext | – | – | – | -11.7 | -28.9 | -40.1 | -13.3 | -5.6 | -10.6 | -18.4 | -15.4 | -5.2 |
| S4_6040 | -6.4 | -18.6 | -1.6 | -11.6 | -6.2 | -16.9 | -2.9 | -1.8 | -5.8 | -11.6 | -14.0 | -3.0 |
| S5_div | -12.6 | -15.4 | -2.9 | -11.3 | -6.6 | -6.7 | 2.1 | -0.7 | -4.7 | -9.1 | -11.0 | 0.4 |
| L1_spec | -16.3 | -26.6 | -13.8 | -13.7 | -6.5 | -9.1 | -10.4 | -5.6 | -10.4 | -19.4 | -12.8 | -5.7 |
| L1_cashetf | -6.6 | -27.1 | -10.2 | -12.8 | 2.0 | -3.3 | -9.5 | -6.1 | -10.4 | -19.4 | -12.1 | -5.6 |
| T1_ewmac_core10 | 9.7 | -11.3 | 12.3 | -4.1 | 14.3 | 16.6 | 9.9 | -2.5 | -3.9 | -1.8 | -6.1 | -0.3 |
| T2_tsmom_core10 | 21.1 | -14.0 | 19.4 | -1.3 | 6.6 | 13.3 | 8.6 | -3.5 | -5.5 | -3.0 | -8.5 | -1.3 |
| T3_ewmac_core12 | 8.8 | -9.8 | 12.0 | -5.0 | 13.8 | 16.7 | 10.0 | -2.1 | -3.9 | -1.7 | -6.9 | 0.2 |
| T4_tsmom_core12 | 20.0 | -17.0 | 18.8 | -1.9 | 6.6 | 13.1 | 9.0 | -3.6 | -5.4 | -3.0 | -9.4 | -1.5 |
| T5_ewmac_eq2_12 | 8.4 | -24.3 | 4.0 | -9.6 | -0.2 | 1.5 | 0.5 | -3.5 | -6.2 | -6.9 | -7.7 | -6.7 |
| T6_ewmac_ext10 | – | – | – | -4.3 | 13.4 | 14.9 | 9.9 | -1.9 | -3.9 | -1.8 | -6.6 | 0.2 |
| G1_gem12 | -7.3 | -40.0 | 15.9 | -8.3 | -5.1 | 0.0 | -3.7 | -1.8 | -11.1 | -13.9 | -21.9 | -6.6 |
| G2_gem12_2bond | -2.2 | -40.3 | 13.7 | -8.0 | -4.1 | -3.1 | -3.2 | -1.8 | -11.1 | -13.9 | -23.1 | -6.6 |
| G3_gem_blend | -7.3 | -40.0 | 11.9 | -13.2 | -3.1 | 0.0 | 2.5 | 0.5 | -5.7 | -13.9 | -21.9 | -6.6 |
| G4_gem6 | 5.2 | -40.0 | 12.8 | -16.2 | -8.1 | 0.0 | 2.5 | -0.3 | -5.7 | -13.9 | -21.2 | -6.6 |
| K1_vaa_core | 13.5 | -40.6 | 4.4 | -2.2 | 17.7 | 16.0 | 9.4 | -7.4 | 3.1 | -5.6 | -4.6 | -0.6 |
| K1x_vaa_ext | – | – | – | 0.7 | 11.9 | 14.4 | 9.4 | -1.3 | 0.8 | -5.2 | -4.8 | -1.8 |
| K2_daa_core | 9.4 | -21.1 | 3.6 | -8.3 | 3.6 | 18.5 | 11.0 | -8.5 | -4.0 | -2.0 | -5.8 | 1.0 |
| K2x_daa_ext | – | – | – | -4.5 | -4.3 | 13.3 | 8.1 | -2.2 | -2.0 | -4.5 | -7.8 | -0.7 |
| K3_baa_core | 14.9 | -24.3 | 8.3 | -3.6 | -7.0 | 33.0 | 18.0 | -6.6 | 0.5 | -0.3 | 0.3 | 5.6 |
| K3x_baa_ext | – | – | – | -3.4 | -5.0 | 32.3 | 18.0 | -0.4 | -0.5 | -1.0 | 0.4 | 0.5 |
| K4_paa_core | 3.9 | -28.9 | -0.3 | -11.0 | 9.4 | 10.6 | 1.5 | 2.4 | -3.4 | -0.7 | -15.0 | 4.1 |
| K4x_paa_ext | – | – | – | -10.9 | 16.4 | 17.0 | 2.0 | 4.4 | -0.8 | -3.8 | -16.9 | -1.9 |
| R1_invvol | 3.7 | -4.6 | 9.5 | -11.3 | 12.3 | 5.8 | 3.8 | 3.0 | -1.0 | -3.2 | -12.5 | 1.2 |
| R2_classrp | 1.6 | -4.1 | 8.2 | -10.4 | 13.8 | 10.6 | 6.9 | 3.3 | -0.6 | -2.9 | -10.7 | 2.5 |
| R3_invvol_sma | 10.8 | -4.0 | 10.6 | -5.5 | 16.0 | 16.7 | 7.9 | -0.2 | -1.1 | -0.9 | -3.5 | 0.4 |
| R4_classrp_ts | 22.9 | -5.3 | 21.8 | -5.5 | 16.9 | 19.6 | 8.3 | 0.2 | -2.0 | -2.6 | -3.7 | 1.2 |
| R5_p1like | 14.4 | -15.8 | 10.2 | -5.6 | 6.2 | 10.9 | 4.8 | -1.9 | -3.8 | -5.7 | -6.0 | -1.0 |
| R5x_p1like_ext | – | – | – | -4.4 | 4.4 | 10.7 | 5.1 | -1.5 | -4.3 | -6.3 | -5.4 | -0.5 |
| H1_hmm_us | -14.8 | -22.9 | -13.0 | -11.3 | -26.6 | -27.6 | -12.4 | -4.9 | -10.0 | -17.7 | -12.2 | -5.3 |
| H1b_hmm_own | -16.8 | -23.5 | -13.3 | -11.0 | -27.0 | -36.3 | -11.8 | -4.9 | -9.4 | -16.1 | -14.3 | -5.0 |
| H2_volswitch | -12.4 | -25.3 | -10.6 | -11.9 | -29.6 | -26.6 | -13.0 | -4.0 | -10.6 | -13.3 | -14.4 | -5.6 |
| H3_volmanaged | -12.0 | -18.8 | -7.8 | -10.7 | -27.3 | -34.0 | -12.9 | -5.2 | -10.4 | -18.6 | -13.7 | -5.6 |
| M1_curve | -2.1 | -26.9 | -9.1 | -11.8 | -26.3 | -29.8 | -11.4 | -5.4 | -10.6 | -15.6 | -14.1 | -5.7 |
| M1b_curve12 | 3.6 | -18.6 | 2.9 | -11.7 | -21.2 | -23.9 | -11.4 | -2.6 | -10.5 | -10.5 | -14.6 | -2.5 |
| M2_cape_step | -16.8 | -27.1 | -14.6 | -4.7 | -7.7 | -26.2 | -5.6 | -1.9 | -5.4 | -10.5 | -7.1 | -2.3 |
| M2b_cape_lin | -16.8 | -18.6 | -6.8 | -5.3 | -10.3 | -27.2 | -7.4 | -2.7 | -5.5 | -11.3 | -7.9 | -2.7 |
| M3_cape_trend | -16.8 | -27.1 | -14.6 | -13.3 | -16.0 | -27.1 | -7.7 | -5.0 | -8.3 | -13.2 | -10.3 | -5.6 |
| F1_momg10 | -17.7 | -29.6 | -14.9 | -12.3 | -28.1 | -39.8 | -13.4 | -4.6 | -10.9 | -18.2 | -15.0 | -6.4 |
| F2_momau10 | – | – | – | -13.1 | -30.3 | -39.8 | -13.4 | -5.9 | -10.8 | -18.1 | -15.4 | -5.4 |
| E1_six | 2.4 | -22.7 | 4.6 | -7.2 | -2.6 | -1.9 | -0.6 | -3.6 | -6.0 | -9.7 | -10.5 | -2.6 |
| E2_mom3 | 5.1 | -30.5 | 10.0 | -4.7 | 9.7 | 9.7 | 4.2 | -3.6 | -4.0 | -7.2 | -10.7 | -3.0 |
| E3_slow3 | -0.5 | -10.6 | 3.5 | -8.5 | -1.3 | -5.2 | 0.4 | -0.6 | -4.5 | -7.8 | -9.9 | -1.1 |


- **Slow bear markets (2000–03, 2007–09):** every trend-type rule worked. L1 with a cash ETF: +2.0% and −3.3% against −27.8% and −40.1%.
- **Fast falls (October 1987, 2020, early 2025):** rules that only switch between equity and cash did nothing (L1 −27.1%, −19.4%, −5.6%). Only rules already holding bonds and gold were cushioned. The top-one rotation rules (GEM, VAA) lost 40% in October 1987.
- **2022, when bonds fell with shares:** the static 60/40 lost 14.0%, about the same as 40/60 (−15.1%). GEM, whose safe asset is bonds, lost 21.9%. Rules with a trend filter on the bonds themselves lost 4–9%. This is the one episode where trend on the defensive assets, as distinct from holding them, clearly earned its keep.
- **1994 bond rout:** bond-heavy risk parity lost 10–11%, about the same as equities.

### 5.2 Holdout

**Table H2. Holdout 2024-01 to 2025-12 (24 months, clean data), cumulative return unless stated; extension to 2026-09 uses flagged proxies for AU equity (from 2026-01) and global bonds (from 2026-03)**

| Trial | Paper % | Net 5k % | Net 25k % | Net 100k % | CAGR 25k | Vol 25k | Sharpe 25k | MaxDD 25k | Feb-Apr 2025 | Ext. to 2026-09: net 25k % | Ext. MaxDD | Ext. Sharpe | Dev rank (net 25k Sharpe) | Holdout rank (Sharpe) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | 36.4 | 37.3 | 38.2 | 38.2 | 17.5 | 8.6 | 1.47 | -6.2 | -5.8 | 46.1 | -6.2 | 1.23 | 25 | 14 |
| S2_world100 | 45.3 | 45.3 | 45.3 | 45.3 | 20.6 | 9.8 | 1.57 | -6.6 | -6.6 | 54.4 | -6.6 | 1.27 | 33 | 11 |
| S2b_au100 | 23.3 | 23.3 | 23.3 | 23.3 | 11.0 | 9.1 | 0.76 | -7.3 | -4.0 | 29.1 | -7.3 | 0.64 | 42 | 44 |
| S3_dhhf3763 | 37.0 | 37.9 | 38.9 | 38.9 | 17.9 | 8.8 | 1.47 | -6.1 | -6.0 | 46.7 | -6.1 | 1.24 | 22 | 13 |
| S3x_dhhf_ext | 36.1 | 33.2 | 34.9 | 35.9 | 16.1 | 8.0 | 1.43 | -5.9 | -5.2 | 43.0 | -5.9 | 1.20 | 12 | 16 |
| S4_6040 | 19.1 | 24.7 | 21.3 | 21.0 | 10.1 | 5.9 | 0.99 | -4.2 | -3.0 | 26.3 | -4.2 | 0.82 | 6 | 41 |
| S5_div | 32.6 | 29.5 | 37.5 | 35.5 | 17.3 | 5.1 | 2.41 | -2.2 | 0.4 | 41.2 | -2.2 | 1.73 | 14 | 1 |
| L1_spec | 36.4 | 37.0 | 37.0 | 37.0 | 17.0 | 8.5 | 1.44 | -6.3 | -5.7 | 44.8 | -6.3 | 1.21 | 36 | 15 |
| L1_cashetf | 36.4 | 36.9 | 36.5 | 36.3 | 16.8 | 8.4 | 1.42 | -6.3 | -5.6 | 44.1 | -6.3 | 1.20 | 10 | 19 |
| T1_ewmac_core10 | 25.5 | 15.0 | 21.5 | 23.0 | 10.2 | 6.0 | 0.99 | -3.8 | -0.3 | 21.4 | -3.8 | 0.55 | 24 | 42 |
| T2_tsmom_core10 | 30.7 | 33.1 | 26.6 | 28.4 | 12.5 | 5.7 | 1.40 | -2.7 | -1.3 | 26.8 | -2.7 | 0.89 | 15 | 27 |
| T3_ewmac_core12 | 26.0 | 9.8 | 22.5 | 23.6 | 10.7 | 6.1 | 1.05 | -3.3 | 0.2 | 22.6 | -4.3 | 0.59 | 18 | 37 |
| T4_tsmom_core12 | 31.1 | 27.4 | 27.7 | 28.6 | 13.0 | 5.9 | 1.42 | -3.1 | -1.5 | 27.3 | -3.3 | 0.86 | 17 | 18 |
| T5_ewmac_eq2_12 | 29.0 | 23.9 | 27.2 | 27.5 | 12.8 | 8.4 | 1.01 | -6.7 | -6.7 | 27.6 | -6.7 | 0.64 | 30 | 38 |
| T6_ewmac_ext10 | 24.7 | 15.0 | 20.1 | 21.7 | 9.6 | 5.3 | 1.01 | -3.0 | 0.2 | 20.1 | -4.6 | 0.51 | 3 | 39 |
| G1_gem12 | 38.6 | 37.5 | 37.8 | 37.8 | 17.4 | 9.9 | 1.27 | -6.6 | -6.6 | 42.2 | -6.6 | 0.95 | 37 | 30 |
| G2_gem12_2bond | 38.6 | 37.5 | 37.8 | 37.8 | 17.4 | 9.9 | 1.27 | -6.6 | -6.6 | 42.2 | -6.6 | 0.95 | 38 | 31 |
| G3_gem_blend | 35.5 | 33.5 | 34.0 | 34.0 | 15.7 | 10.0 | 1.12 | -6.6 | -6.6 | 38.3 | -6.6 | 0.84 | 40 | 36 |
| G4_gem6 | 30.6 | 27.8 | 28.4 | 28.4 | 13.3 | 9.3 | 0.96 | -6.6 | -6.6 | 23.4 | -7.0 | 0.44 | 43 | 43 |
| K1_vaa_core | 7.1 | -0.4 | 1.3 | 1.3 | 0.7 | 12.0 | -0.22 | -14.7 | -0.6 | 0.7 | -14.7 | -0.31 | 47 | 47 |
| K1x_vaa_ext | 7.8 | 1.2 | 2.7 | 2.7 | 1.4 | 13.0 | -0.14 | -16.5 | -1.8 | -2.5 | -16.5 | -0.36 | 27 | 46 |
| K2_daa_core | 31.7 | 26.1 | 27.6 | 28.0 | 13.0 | 6.2 | 1.36 | -3.8 | 1.0 | 30.1 | -3.8 | 0.93 | 9 | 29 |
| K2x_daa_ext | 31.3 | 11.9 | 25.2 | 26.0 | 11.9 | 6.4 | 1.16 | -2.9 | -0.7 | 24.9 | -4.9 | 0.62 | 1 | 34 |
| K3_baa_core | 46.1 | 39.9 | 42.8 | 43.0 | 19.5 | 6.3 | 2.23 | -4.0 | 5.6 | 41.6 | -7.7 | 1.29 | 44 | 3 |
| K3x_baa_ext | 41.9 | 29.1 | 37.7 | 38.0 | 17.4 | 7.1 | 1.73 | -4.2 | 0.5 | 38.3 | -5.3 | 1.09 | 46 | 9 |
| K4_paa_core | 58.6 | 46.1 | 55.6 | 55.5 | 24.7 | 8.1 | 2.28 | -3.7 | 4.1 | 64.5 | -3.7 | 1.83 | 13 | 2 |
| K4x_paa_ext | 44.4 | 39.5 | 41.4 | 42.2 | 18.9 | 6.9 | 1.98 | -3.6 | -1.9 | 50.1 | -3.9 | 1.54 | 2 | 5 |
| R1_invvol | 20.6 | 13.1 | 20.5 | 20.3 | 9.8 | 4.6 | 1.18 | -2.0 | 1.2 | 22.5 | -2.0 | 0.79 | 35 | 32 |
| R2_classrp | 29.5 | 29.4 | 29.6 | 29.2 | 13.8 | 4.7 | 1.96 | -1.4 | 2.5 | 30.9 | -2.1 | 1.28 | 45 | 6 |
| R3_invvol_sma | 19.2 | 4.7 | 19.3 | 18.3 | 9.2 | 4.4 | 1.13 | -2.4 | 0.4 | 19.8 | -2.4 | 0.66 | 23 | 35 |
| R4_classrp_ts | 29.5 | 20.3 | 27.7 | 28.0 | 13.0 | 4.4 | 1.92 | -1.8 | 1.2 | 31.3 | -1.8 | 1.48 | 4 | 7 |
| R5_p1like | 28.2 | 16.2 | 25.5 | 27.3 | 12.0 | 4.2 | 1.78 | -2.0 | -1.0 | 26.1 | -2.1 | 1.10 | 19 | 8 |
| R5x_p1like_ext | 30.4 | 0.9 | 27.8 | 30.1 | 13.0 | 4.2 | 2.00 | -1.5 | -0.5 | 29.6 | -2.5 | 1.27 | 5 | 4 |
| H1_hmm_us | 34.8 | 29.7 | 34.3 | 34.6 | 15.9 | 7.9 | 1.40 | -6.1 | -5.3 | 40.8 | -6.1 | 1.16 | 39 | 28 |
| H1b_hmm_own | 34.1 | 31.9 | 33.8 | 33.7 | 15.7 | 7.7 | 1.42 | -5.7 | -5.0 | 40.9 | -5.7 | 1.20 | 32 | 22 |
| H2_volswitch | 36.4 | 34.3 | 36.6 | 36.2 | 16.9 | 8.4 | 1.43 | -6.4 | -5.6 | 44.2 | -6.4 | 1.20 | 28 | 17 |
| H3_volmanaged | 36.2 | 35.1 | 36.2 | 36.1 | 16.7 | 8.4 | 1.42 | -6.3 | -5.6 | 44.0 | -6.3 | 1.20 | 29 | 20 |
| M1_curve | 23.9 | 23.5 | 23.0 | 23.0 | 10.9 | 6.6 | 0.99 | -6.5 | -5.7 | 29.8 | -6.5 | 0.86 | 26 | 40 |
| M1b_curve12 | 21.8 | 23.2 | 22.3 | 21.8 | 10.6 | 4.4 | 1.41 | -3.1 | -2.5 | 27.5 | -3.1 | 1.12 | 11 | 24 |
| M2_cape_step | 21.8 | 24.1 | 22.1 | 21.8 | 10.5 | 4.3 | 1.41 | -2.9 | -2.3 | 27.4 | -2.9 | 1.18 | 34 | 25 |
| M2b_cape_lin | 22.8 | 25.3 | 23.0 | 22.7 | 10.9 | 4.6 | 1.41 | -3.2 | -2.7 | 28.4 | -3.2 | 1.19 | 20 | 26 |
| M3_cape_trend | 36.4 | 34.7 | 36.3 | 36.2 | 16.7 | 8.4 | 1.42 | -6.3 | -5.6 | 41.1 | -6.3 | 1.13 | 8 | 21 |
| F1_momg10 | 36.4 | 34.1 | 38.1 | 37.5 | 17.5 | 8.9 | 1.42 | -6.8 | -6.4 | 47.6 | -6.8 | 1.20 | 21 | 23 |
| F2_momau10 | 38.7 | 35.7 | 39.6 | 39.6 | 18.2 | 8.6 | 1.52 | -5.7 | -5.4 | 47.3 | -5.7 | 1.25 | 7 | 12 |
| E1_six | 26.6 | 15.5 | 23.1 | 25.3 | 11.0 | 5.6 | 1.18 | -3.3 | -2.6 | 26.3 | -3.3 | 0.86 | 31 | 33 |
| E2_mom3 | 23.6 | 11.4 | 17.7 | 20.0 | 8.5 | 7.4 | 0.60 | -6.8 | -3.0 | 18.7 | -6.8 | 0.36 | 41 | 45 |
| E3_slow3 | 30.5 | 13.3 | 29.5 | 29.6 | 13.8 | 5.3 | 1.71 | -2.7 | -1.1 | 32.2 | -2.7 | 1.21 | 16 | 10 |

Spearman rank correlation development vs holdout across 47 trials: Sharpe 0.25; CAGR 0.44.


The holdout was a strong bull market in global shares and gold with one sharp V-shaped dip. Being fully invested won. The rules ranked highest by development Sharpe (R4, the T family) were in the bottom half for return. The development-sample losers that did well (K3, K4) did so because their universes include gold. Twenty-four months decide nothing; the point is that nothing in the holdout contradicts section 4.

### 5.3 Lifecycle: A$5,000 plus A$500 a month for ten years

**Table H3. Lifecycle sub-study: A$5,000 start + A$500 a month for 10 years (A$65,000 paid in), every January start (39 windows 1976-2014; 24 windows for the 1991+ trials), dollar-level costs and minimum orders, Regime-B tax at 32% with liquidation at year 10**

| Trial | Windows | Median wealth pre-tax A$ | Median after tax B A$ | 10th pct after tax B A$ | Worst window A$ | Median ratio vs 40/60 | Win rate vs 40/60 % | Worst ratio | Best ratio | Median MaxDD % | Worst MaxDD % | Trades/yr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | 39 | 115428 | 102890 | 74033 | 63976 | 1.00 | 0 | 1.00 | 1.00 | -28.0 | -39.7 | 4.8 |
| S2_world100 | 39 | 118752 | 105178 | 65112 | 57317 | 1.01 | 51 | 0.81 | 1.13 | -27.4 | -46.2 | 4.1 |
| S2b_au100 | 39 | 120123 | 110746 | 88648 | 76153 | 0.98 | 46 | 0.82 | 1.35 | -41.7 | -48.2 | 4.1 |
| S3_dhhf3763 | 39 | 115540 | 103514 | 73613 | 63702 | 1.00 | 49 | 0.99 | 1.02 | -27.6 | -39.5 | 4.8 |
| S3x_dhhf_ext | 24 | 103372 | 94972 | 74034 | 64641 | 0.99 | 29 | 0.96 | 1.03 | -32.2 | -40.4 | 5.1 |
| S4_6040 | 39 | 104808 | 94907 | 80045 | 74752 | 0.95 | 23 | 0.77 | 1.17 | -14.2 | -19.6 | 5.3 |
| S5_div | 39 | 104056 | 94693 | 83494 | 79990 | 0.90 | 13 | 0.76 | 1.26 | -12.3 | -16.8 | 5.5 |
| L1_spec | 39 | 105768 | 94892 | 82393 | 76926 | 0.90 | 36 | 0.78 | 1.40 | -13.6 | -28.4 | 4.8 |
| L1_cashetf | 39 | 111854 | 98475 | 87080 | 81689 | 0.97 | 38 | 0.81 | 1.50 | -12.5 | -26.7 | 7.2 |
| T1_ewmac_core10 | 39 | 104666 | 89831 | 79746 | 72324 | 0.87 | 21 | 0.62 | 1.39 | -5.5 | -13.1 | 36.9 |
| T2_tsmom_core10 | 39 | 101709 | 88160 | 79795 | 72168 | 0.86 | 18 | 0.65 | 1.44 | -6.5 | -14.3 | 35.0 |
| T3_ewmac_core12 | 39 | 104898 | 90025 | 81505 | 73098 | 0.88 | 21 | 0.62 | 1.38 | -5.2 | -12.9 | 36.3 |
| T4_tsmom_core12 | 39 | 102506 | 88571 | 80887 | 72297 | 0.86 | 18 | 0.67 | 1.46 | -7.3 | -17.1 | 35.0 |
| T5_ewmac_eq2_12 | 39 | 107902 | 93012 | 84067 | 79758 | 0.84 | 31 | 0.75 | 1.47 | -10.4 | -24.8 | 22.5 |
| T6_ewmac_ext10 | 24 | 97175 | 85009 | 78329 | 72174 | 0.91 | 29 | 0.68 | 1.39 | -4.4 | -7.8 | 45.5 |
| G1_gem12 | 39 | 116981 | 99910 | 84012 | 73397 | 0.93 | 36 | 0.55 | 1.67 | -18.6 | -41.5 | 7.5 |
| G2_gem12_2bond | 39 | 117085 | 99394 | 84332 | 72470 | 0.92 | 36 | 0.55 | 1.64 | -18.7 | -41.5 | 8.8 |
| G3_gem_blend | 39 | 113568 | 98891 | 83919 | 67956 | 0.85 | 36 | 0.63 | 1.73 | -17.2 | -41.6 | 8.3 |
| G4_gem6 | 39 | 120231 | 100390 | 86874 | 75414 | 0.91 | 36 | 0.56 | 1.53 | -17.4 | -41.7 | 8.8 |
| K1_vaa_core | 39 | 109648 | 90902 | 63989 | 61325 | 0.73 | 18 | 0.51 | 1.56 | -16.3 | -41.7 | 15.8 |
| K1x_vaa_ext | 24 | 104882 | 86568 | 68130 | 61167 | 0.93 | 38 | 0.58 | 1.64 | -9.5 | -12.3 | 15.6 |
| K2_daa_core | 39 | 111389 | 92220 | 73578 | 68207 | 0.84 | 18 | 0.65 | 1.57 | -11.1 | -22.1 | 35.9 |
| K2x_daa_ext | 24 | 113055 | 92232 | 82138 | 71129 | 0.99 | 50 | 0.69 | 1.65 | -6.2 | -14.0 | 48.9 |
| K3_baa_core | 39 | 100062 | 85271 | 67187 | 64094 | 0.81 | 13 | 0.57 | 1.55 | -12.6 | -23.4 | 24.7 |
| K3x_baa_ext | 24 | 87370 | 77169 | 69583 | 67504 | 0.82 | 21 | 0.61 | 1.48 | -11.3 | -18.2 | 32.0 |
| K4_paa_core | 39 | 115122 | 96428 | 85792 | 72412 | 0.85 | 31 | 0.72 | 1.68 | -11.1 | -29.9 | 22.6 |
| K4x_paa_ext | 24 | 113393 | 95488 | 88589 | 72737 | 1.05 | 54 | 0.72 | 1.77 | -7.4 | -17.1 | 33.1 |
| R1_invvol | 39 | 98828 | 89506 | 84023 | 71547 | 0.86 | 13 | 0.60 | 1.37 | -4.5 | -12.6 | 11.4 |
| R2_classrp | 39 | 98394 | 88773 | 83212 | 72585 | 0.84 | 13 | 0.59 | 1.40 | -5.4 | -10.8 | 11.9 |
| R3_invvol_sma | 39 | 98316 | 87732 | 76454 | 70162 | 0.86 | 13 | 0.62 | 1.39 | -4.2 | -5.6 | 20.5 |
| R4_classrp_ts | 39 | 97287 | 86662 | 76195 | 69546 | 0.87 | 13 | 0.62 | 1.44 | -5.2 | -7.9 | 18.4 |
| R5_p1like | 39 | 102508 | 90434 | 80940 | 73623 | 0.85 | 13 | 0.69 | 1.43 | -5.2 | -15.8 | 31.3 |
| R5x_p1like_ext | 24 | 93984 | 84149 | 79393 | 72318 | 0.92 | 21 | 0.68 | 1.38 | -3.8 | -7.4 | 35.8 |
| H1_hmm_us | 39 | 110573 | 99517 | 75272 | 66956 | 0.98 | 13 | 0.82 | 1.10 | -24.6 | -31.0 | 10.6 |
| H1b_hmm_own | 39 | 112732 | 100537 | 73813 | 65493 | 0.98 | 10 | 0.93 | 1.02 | -23.6 | -37.2 | 7.2 |
| H2_volswitch | 39 | 116056 | 100682 | 78167 | 68744 | 0.97 | 26 | 0.74 | 1.12 | -25.3 | -34.4 | 8.6 |
| H3_volmanaged | 39 | 114996 | 101803 | 75185 | 66299 | 0.97 | 28 | 0.84 | 1.07 | -18.7 | -34.1 | 12.1 |
| M1_curve | 39 | 113888 | 101240 | 73011 | 63272 | 0.96 | 13 | 0.87 | 1.02 | -26.8 | -30.4 | 7.8 |
| M1b_curve12 | 39 | 112614 | 99713 | 74755 | 67776 | 0.96 | 31 | 0.88 | 1.11 | -19.4 | -25.9 | 6.6 |
| M2_cape_step | 39 | 97153 | 88002 | 79642 | 69473 | 0.92 | 31 | 0.75 | 1.15 | -19.6 | -26.7 | 6.4 |
| M2b_cape_lin | 39 | 98537 | 89657 | 77075 | 69192 | 0.94 | 36 | 0.78 | 1.15 | -18.5 | -28.2 | 7.9 |
| M3_cape_trend | 39 | 113519 | 101146 | 85436 | 77280 | 1.00 | 51 | 0.92 | 1.21 | -21.3 | -27.6 | 7.7 |
| F1_momg10 | 39 | 116808 | 103528 | 74415 | 65045 | 1.00 | 54 | 0.97 | 1.02 | -28.9 | -39.6 | 4.9 |
| F2_momau10 | 24 | 104343 | 95573 | 72561 | 65603 | 1.00 | 54 | 0.98 | 1.03 | -32.5 | -39.3 | 5.0 |
| E1_six | 39 | 105716 | 91732 | 82622 | 73730 | 0.85 | 13 | 0.70 | 1.35 | -7.3 | -24.7 | 30.4 |
| E2_mom3 | 39 | 110021 | 92715 | 78980 | 68691 | 0.84 | 26 | 0.60 | 1.53 | -6.9 | -31.8 | 32.4 |
| E3_slow3 | 39 | 101952 | 91017 | 81561 | 79197 | 0.89 | 13 | 0.69 | 1.28 | -7.8 | -11.6 | 22.6 |


- **Median outcome:** static 40/60 ends with about A$102,900 after tax from A$65,000 paid in. The only higher medians belong to other static equity mixes (100% Australian +7.6%, global-only +2.2%, 37/63 and the global momentum sleeve +0.6%). Every dynamic rule has a lower median; M3 is the closest, 1.7% lower.
- **Bad outcomes:** the worst 10% of windows end near A$74,000 for 40/60. L1 with a cash ETF lifts that to A$87,100, M3 to A$85,400, S5 to A$83,500, T1 to A$79,700. Their medians are lower by A$4,400 (L1), A$1,700 (M3), A$8,200 (S5) and A$13,100 (T1).
- So the trade on offer is the one the spec already describes for L1: pay out of the typical outcome to raise the floor. Among the ways to buy that, M3 and L1 were the cheapest per dollar of floor in this sample and the trend ensemble the most expensive.
- Share of windows ahead of 40/60 after tax: M3 51%, L1 38%, GEM 36%, T1 21%, S5 13%.

### 5.4 Execution band

**Table H4. Execution-band sub-study (added after run 1): no-trade band of 2% (declared), 5% and 10% of NAV; development sample**

| Trial | Net CAGR 25k band 2% | Net CAGR 25k band 5% | Net CAGR 25k band 10% | Net CAGR 100k band 2% | Net CAGR 100k band 5% | Net CAGR 100k band 10% | Trades/yr 25k band 2% | Trades/yr 25k band 5% | Trades/yr 25k band 10% | After-tax B 25k band 2% | After-tax B 25k band 10% | After-tax B 100k band 2% | After-tax B 100k band 10% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1_cashetf | 11.98 | 12.03 | 11.97 | 12.02 | 12.05 | 11.97 | 3.5 | 3.3 | 2.8 | 9.81 | 9.81 | 9.83 | 9.82 |
| T1_ewmac_core10 | 9.17 | 9.26 | 9.75 | 9.79 | 9.93 | 10.17 | 32.1 | 29.7 | 21.2 | 6.25 | 6.91 | 6.78 | 7.27 |
| T2_tsmom_core10 | 9.64 | 9.73 | 10.06 | 10.18 | 10.30 | 10.52 | 31.9 | 29.4 | 23.0 | 6.53 | 7.00 | 7.00 | 7.42 |
| T3_ewmac_core12 | 9.35 | 9.45 | 9.75 | 9.83 | 10.03 | 10.09 | 31.2 | 29.1 | 21.3 | 6.39 | 6.89 | 6.80 | 7.18 |
| T4_tsmom_core12 | 9.87 | 10.00 | 10.24 | 10.41 | 10.54 | 10.67 | 31.9 | 29.8 | 22.8 | 6.70 | 7.13 | 7.16 | 7.54 |
| T5_ewmac_eq2_12 | 10.49 | 10.54 | 10.63 | 10.70 | 10.78 | 10.83 | 21.8 | 20.8 | 17.4 | 7.46 | 7.65 | 7.66 | 7.84 |
| T6_ewmac_ext10 | 7.20 | 7.21 | 7.85 | 8.02 | 8.11 | 8.38 | 37.1 | 34.4 | 24.5 | 4.82 | 5.51 | 5.47 | 5.97 |
| G1_gem12 | 11.30 | 11.30 | 11.30 | 11.30 | 11.30 | 11.30 | 4.3 | 4.3 | 4.3 | 8.39 | 8.39 | 8.39 | 8.39 |
| G2_gem12_2bond | 11.27 | 11.27 | 11.27 | 11.27 | 11.27 | 11.27 | 5.5 | 5.5 | 5.5 | 8.35 | 8.35 | 8.35 | 8.35 |
| G3_gem_blend | 11.04 | 11.04 | 11.04 | 11.04 | 11.04 | 11.04 | 5.1 | 5.1 | 5.1 | 8.26 | 8.26 | 8.26 | 8.26 |
| G4_gem6 | 10.79 | 10.79 | 10.79 | 10.79 | 10.79 | 10.79 | 6.1 | 6.1 | 6.1 | 7.73 | 7.73 | 7.73 | 7.73 |
| K1_vaa_core | 8.34 | 8.34 | 8.34 | 8.34 | 8.34 | 8.34 | 14.6 | 14.6 | 14.6 | 5.21 | 5.21 | 5.21 | 5.21 |
| K1x_vaa_ext | 7.21 | 7.21 | 7.21 | 7.21 | 7.21 | 7.21 | 14.4 | 14.4 | 14.4 | 4.28 | 4.28 | 4.28 | 4.28 |
| K2_daa_core | 11.12 | 11.12 | 11.04 | 11.32 | 11.30 | 11.22 | 35.1 | 35.0 | 35.0 | 7.46 | 7.40 | 7.64 | 7.58 |
| K2x_daa_ext | 9.39 | 9.39 | 9.38 | 9.89 | 9.88 | 9.87 | 49.3 | 49.3 | 49.2 | 5.82 | 5.81 | 6.31 | 6.30 |
| K3_baa_core | 9.71 | 9.72 | 9.67 | 9.82 | 9.78 | 9.73 | 23.8 | 23.7 | 23.6 | 6.55 | 6.53 | 6.63 | 6.58 |
| K3x_baa_ext | 5.87 | 5.85 | 5.82 | 5.95 | 5.96 | 5.93 | 31.6 | 31.5 | 31.4 | 3.49 | 3.46 | 3.59 | 3.57 |
| K4_paa_core | 11.83 | 11.85 | 11.91 | 12.02 | 12.03 | 12.04 | 21.4 | 21.2 | 21.0 | 8.33 | 8.40 | 8.51 | 8.55 |
| K4x_paa_ext | 9.48 | 9.48 | 10.35 | 10.01 | 10.02 | 10.69 | 33.4 | 33.3 | 24.3 | 6.36 | 7.18 | 6.85 | 7.51 |
| R1_invvol | 8.75 | 8.70 | 9.34 | 9.01 | 9.19 | 9.61 | 5.7 | 4.2 | 1.5 | 6.65 | 7.26 | 6.77 | 7.44 |
| R2_classrp | 8.53 | 8.71 | 8.94 | 8.72 | 8.84 | 9.15 | 6.4 | 4.7 | 1.8 | 6.45 | 6.87 | 6.58 | 7.10 |
| R3_invvol_sma | 8.65 | 8.71 | 8.92 | 9.05 | 9.04 | 9.02 | 16.7 | 15.6 | 13.2 | 6.28 | 6.52 | 6.61 | 6.65 |
| R4_classrp_ts | 9.10 | 9.18 | 9.13 | 9.36 | 9.38 | 9.15 | 14.7 | 13.5 | 11.4 | 6.50 | 6.57 | 6.70 | 6.62 |
| R5_p1like | 9.53 | 9.58 | 9.78 | 10.11 | 10.04 | 10.09 | 24.5 | 22.0 | 14.2 | 7.01 | 7.32 | 7.46 | 7.62 |
| R5x_p1like_ext | 6.58 | 6.76 | 7.61 | 7.22 | 7.55 | 7.97 | 25.5 | 23.5 | 13.2 | 4.70 | 5.63 | 5.17 | 5.96 |
| H1_hmm_us | 10.66 | 10.72 | 10.83 | 10.90 | 10.92 | 10.93 | 7.1 | 6.5 | 4.4 | 8.97 | 9.10 | 9.17 | 9.20 |
| H1b_hmm_own | 11.27 | 11.33 | 11.28 | 11.47 | 11.51 | 11.33 | 2.7 | 1.9 | 0.9 | 9.91 | 10.12 | 9.98 | 10.17 |
| H2_volswitch | 11.30 | 11.33 | 11.32 | 11.34 | 11.35 | 11.33 | 4.9 | 4.8 | 4.5 | 9.07 | 9.10 | 9.07 | 9.12 |
| H3_volmanaged | 11.10 | 11.25 | 11.30 | 11.34 | 11.56 | 11.75 | 6.6 | 5.6 | 2.4 | 9.27 | 9.63 | 9.40 | 9.97 |
| M1_curve | 11.38 | 11.37 | 11.52 | 11.36 | 11.46 | 11.60 | 4.4 | 4.1 | 3.7 | 9.27 | 9.42 | 9.26 | 9.50 |
| M1b_curve12 | 11.40 | 11.41 | 11.36 | 11.52 | 11.57 | 11.45 | 2.2 | 2.1 | 1.6 | 9.44 | 9.45 | 9.48 | 9.54 |
| M2_cape_step | 10.54 | 10.69 | 10.59 | 10.60 | 10.72 | 10.60 | 2.1 | 1.8 | 1.1 | 8.93 | 9.00 | 8.94 | 9.01 |
| M2b_cape_lin | 10.97 | 11.06 | 11.11 | 10.96 | 11.15 | 11.19 | 3.4 | 2.9 | 1.2 | 9.32 | 9.58 | 9.28 | 9.62 |
| M3_cape_trend | 12.35 | 12.43 | 12.35 | 12.42 | 12.45 | 12.36 | 3.7 | 3.6 | 2.9 | 10.41 | 10.45 | 10.44 | 10.46 |
| E1_six | 10.07 | 9.96 | 10.10 | 10.45 | 10.43 | 10.53 | 25.6 | 24.0 | 20.3 | 7.15 | 7.26 | 7.46 | 7.65 |
| E2_mom3 | 9.83 | 9.94 | 9.93 | 10.03 | 10.19 | 10.15 | 27.4 | 26.3 | 22.7 | 6.67 | 6.80 | 6.83 | 6.99 |
| E3_slow3 | 9.71 | 9.97 | 10.16 | 10.06 | 10.29 | 10.36 | 14.5 | 12.0 | 4.8 | 7.47 | 8.02 | 7.71 | 8.24 |


A 10% band adds 0.3–0.6 points a year for the continuous rules at A$25,000 (T1: 9.17 → 9.75 before tax, 6.25 → 6.91 after) and cuts their trades by a third. It does not close the gap to the static parent (S5: 10.63 and 9.01). It makes no difference to binary rotation rules, which always trade the whole position.

### 5.5 Gold data diagnostic

**Table H5. Gold data diagnostic (gold is a monthly-average price series): contestants re-run without gold, and with the gold weight applied one month late**

| variant | paper_cagr | paper_sharpe | paper_maxdd | net25k_cagr | net25k_sharpe | net25k_maxdd |
|---|---|---|---|---|---|---|
| T1 (declared) | 10.60 | 0.65 | -12.38 | 9.17 | 0.41 | -12.04 |
| T1 no gold | 10.63 | 0.64 | -13.03 | 9.45 | 0.45 | -12.46 |
| K2 (declared) | 13.20 | 0.69 | -21.48 | 11.12 | 0.47 | -22.51 |
| K2 no gold | 12.46 | 0.67 | -21.48 | 10.69 | 0.47 | -21.82 |
| K4 (declared) | 13.00 | 0.54 | -29.90 | 11.83 | 0.45 | -30.53 |
| K4 no gold | 12.99 | 0.55 | -29.90 | 12.07 | 0.47 | -30.67 |
| R4 (declared) | 9.76 | 0.69 | -7.55 | 9.10 | 0.54 | -7.74 |
| R4 no gold | 9.80 | 0.70 | -8.41 | 9.20 | 0.56 | -8.82 |
| S5 (declared) | 10.66 | 0.46 | -14.80 | 10.63 | 0.45 | -15.36 |
| S5 no gold (gold->bonds) | 10.71 | 0.49 | -17.39 | 10.59 | 0.46 | -16.55 |
| T1 gold weight lagged 1m | 10.48 | 0.63 | -12.17 | 9.12 | 0.41 | -10.59 |
| K2 gold weight lagged 1m | 12.12 | 0.60 | -21.48 | 9.93 | 0.36 | -22.22 |
| K4 gold weight lagged 1m | 12.30 | 0.49 | -29.90 | 11.06 | 0.39 | -29.95 |
| R4 gold weight lagged 1m | 9.63 | 0.68 | -7.14 | 8.97 | 0.51 | -7.62 |


Removing gold changes little for T1, K4 and R4. Applying the gold weight one month late costs K2 1.1 points and K4 0.7 points of paper CAGR. The averaged gold series contributes materially to the Keller rules' paper results and little to the others.

### 5.6 Sub-periods

**Table H6. Sub-periods, net of costs at A$25,000 (1991+ trials have no first period)**

| Trial | 1976-89 cagr | 1976-89 sharpe | 1976-89 maxdd | 1990-2006 cagr | 1990-2006 sharpe | 1990-2006 maxdd | 2007-23 cagr | 2007-23 sharpe | 2007-23 maxdd |
|---|---|---|---|---|---|---|---|---|---|
| S1_4060 | 20.52 | 0.50 | -28.27 | 9.63 | 0.31 | -32.72 | 7.13 | 0.41 | -40.14 |
| S2_world100 | 22.05 | 0.55 | -21.57 | 7.90 | 0.16 | -46.44 | 7.58 | 0.44 | -37.94 |
| S2b_au100 | 17.54 | 0.30 | -41.67 | 11.86 | 0.46 | -16.56 | 6.16 | 0.30 | -48.37 |
| S3_dhhf3763 | 20.80 | 0.52 | -28.28 | 9.52 | 0.30 | -35.49 | 7.30 | 0.43 | -40.22 |
| S3x_dhhf_ext | – | – | – | 11.26 | 0.50 | -32.61 | 7.04 | 0.41 | -40.09 |
| S4_6040 | 17.67 | 0.45 | -18.65 | 10.10 | 0.49 | -11.58 | 6.46 | 0.52 | -16.87 |
| S5_div | 17.48 | 0.41 | -15.36 | 8.94 | 0.35 | -11.85 | 6.91 | 0.66 | -11.01 |
| L1_spec | 18.72 | 0.42 | -26.61 | 8.88 | 0.27 | -13.85 | 6.34 | 0.42 | -19.44 |
| L1_cashetf | 20.83 | 0.55 | -27.12 | 10.17 | 0.39 | -12.78 | 6.90 | 0.48 | -19.44 |
| T1_ewmac_core10 | 13.78 | 0.13 | -12.04 | 9.19 | 0.54 | -4.24 | 5.50 | 0.57 | -7.05 |
| T2_tsmom_core10 | 15.83 | 0.36 | -14.67 | 9.09 | 0.52 | -4.45 | 5.31 | 0.49 | -8.93 |
| T3_ewmac_core12 | 13.91 | 0.15 | -10.53 | 9.28 | 0.55 | -5.04 | 5.79 | 0.59 | -8.09 |
| T4_tsmom_core12 | 16.02 | 0.34 | -17.62 | 9.30 | 0.53 | -4.93 | 5.60 | 0.51 | -10.02 |
| T5_ewmac_eq2_12 | 17.28 | 0.36 | -24.88 | 8.85 | 0.31 | -9.58 | 6.78 | 0.59 | -10.60 |
| T6_ewmac_ext10 | – | – | – | 9.37 | 0.70 | -4.68 | 5.21 | 0.53 | -7.96 |
| G1_gem12 | 15.99 | 0.24 | -41.64 | 12.19 | 0.54 | -18.94 | 6.74 | 0.41 | -22.58 |
| G2_gem12_2bond | 16.29 | 0.25 | -41.64 | 11.93 | 0.52 | -19.07 | 6.65 | 0.41 | -23.70 |
| G3_gem_blend | 16.74 | 0.27 | -41.65 | 11.23 | 0.45 | -17.24 | 6.38 | 0.38 | -22.44 |
| G4_gem6 | 13.39 | 0.13 | -41.65 | 9.84 | 0.34 | -17.53 | 9.62 | 0.65 | -23.36 |
| K1_vaa_core | 14.13 | 0.15 | -41.64 | 8.57 | 0.28 | -7.70 | 3.57 | 0.14 | -18.34 |
| K1x_vaa_ext | – | – | – | 11.55 | 0.63 | -11.73 | 3.28 | 0.11 | -12.30 |
| K2_daa_core | 21.20 | 0.61 | -22.51 | 9.11 | 0.38 | -8.77 | 5.37 | 0.43 | -13.26 |
| K2x_daa_ext | – | – | – | 12.29 | 0.80 | -6.82 | 6.72 | 0.67 | -14.48 |
| K3_baa_core | 21.43 | 0.63 | -24.32 | 6.60 | 0.05 | -13.90 | 3.87 | 0.18 | -12.60 |
| K3x_baa_ext | – | – | – | 8.08 | 0.31 | -11.40 | 3.82 | 0.17 | -17.95 |
| K4_paa_core | 20.59 | 0.47 | -30.53 | 9.57 | 0.38 | -11.16 | 7.27 | 0.61 | -15.18 |
| K4x_paa_ext | – | – | – | 12.18 | 0.73 | -12.42 | 7.01 | 0.65 | -17.74 |
| R1_invvol | 13.32 | 0.07 | -5.65 | 8.68 | 0.46 | -11.27 | 5.20 | 0.53 | -13.10 |
| R2_classrp | 13.12 | 0.03 | -5.56 | 7.72 | 0.27 | -10.39 | 5.67 | 0.61 | -10.88 |
| R3_invvol_sma | 14.26 | 0.27 | -5.44 | 8.30 | 0.45 | -5.54 | 4.57 | 0.51 | -5.19 |
| R4_classrp_ts | 15.39 | 0.56 | -6.10 | 8.72 | 0.64 | -7.74 | 4.55 | 0.44 | -7.03 |
| R5_p1like | 16.86 | 0.44 | -16.10 | 8.15 | 0.36 | -5.62 | 5.18 | 0.55 | -7.26 |
| R5x_p1like_ext | – | – | – | 8.43 | 0.51 | -5.57 | 4.87 | 0.50 | -7.22 |
| H1_hmm_us | 19.71 | 0.48 | -23.37 | 8.78 | 0.25 | -31.12 | 5.52 | 0.32 | -27.64 |
| H1b_hmm_own | 20.00 | 0.50 | -23.45 | 9.31 | 0.29 | -31.66 | 6.43 | 0.39 | -36.26 |
| H2_volswitch | 18.28 | 0.40 | -25.30 | 9.53 | 0.31 | -34.28 | 7.58 | 0.50 | -26.64 |
| H3_volmanaged | 19.10 | 0.49 | -18.81 | 9.23 | 0.29 | -32.13 | 6.73 | 0.41 | -34.01 |
| M1_curve | 19.26 | 0.47 | -26.90 | 9.24 | 0.28 | -30.04 | 7.33 | 0.47 | -29.82 |
| M1b_curve12 | 19.53 | 0.57 | -18.92 | 9.84 | 0.36 | -25.28 | 6.61 | 0.45 | -23.92 |
| M2_cape_step | 20.73 | 0.52 | -27.12 | 7.45 | 0.15 | -19.56 | 5.74 | 0.43 | -26.23 |
| M2b_cape_lin | 21.45 | 0.59 | -18.59 | 8.25 | 0.26 | -14.96 | 5.62 | 0.41 | -27.21 |
| M3_cape_trend | 20.73 | 0.52 | -27.12 | 9.79 | 0.33 | -21.12 | 8.35 | 0.60 | -27.11 |
| F1_momg10 | 20.72 | 0.50 | -29.64 | 9.97 | 0.33 | -31.40 | 7.15 | 0.42 | -39.80 |
| F2_momau10 | – | – | – | 11.85 | 0.54 | -33.61 | 7.08 | 0.41 | -39.85 |
| E1_six | 16.65 | 0.34 | -23.25 | 9.51 | 0.45 | -7.54 | 5.46 | 0.47 | -10.50 |
| E2_mom3 | 15.06 | 0.20 | -31.82 | 10.19 | 0.53 | -6.86 | 5.37 | 0.45 | -12.83 |
| E3_slow3 | 15.39 | 0.32 | -10.91 | 8.78 | 0.39 | -8.47 | 6.15 | 0.62 | -9.94 |


No active rule has the best Sharpe in all three periods. Most bond-heavy rules were poor in 1976–1989, when cash paid double-digit rates (Sharpe 0.03–0.36 for T1, T2 and R1–R3), and good afterwards. Dual momentum was poor in the first period, good in the second and average in the third. M3 is essentially 40/60 before 1990 (CAPE was never high) and gets its edge from 2000–2003 and 2008.

## 6. Family verdicts

| Family | Verdict | Evidence |
|---|---|---|
| 1. Static benchmarks | **Winners after tax at every size.** 40/60, 37/63 and 100% Australian are indistinguishable. 60/40 and S5 trade about 1.6–1.7 points of after-tax return for a drawdown of 15–19% instead of 40% | Tables E, F1 |
| 2. L1 (reference) | Drawdown −27% against −40% (interval just excludes zero); pre-tax return equal to 40/60 if OFF money earns the cash rate; −0.9 points after tax; −1.8 with idle cash at 0%. Nothing here displaces it as the overlay of choice on two sleeves, and nothing here proves it either. Report 36 owns the detail | F1, F2, E |
| 3. Continuous trend ensemble, vol-targeted | **Reject as a live rule below A$100,000 and do not expect it to pass above.** Best drawdowns of the trend rules (−12%), highest paper Sharpe on the long sample with risk parity plus trend (0.65), and 4 points a year behind 40/60 after tax. Against its own static parent: 3–5 points less drawdown for 2.5–2.8 points less after-tax return. The volatility target is decorative without leverage | A1, C1, F6 |
| 4. Dual momentum (GEM) | **Reject.** No drawdown reduction (−41.6%), 0.5–1.0 point lower return before tax, 2.4–3.0 lower after tax, 4–6 trades of the whole account a year | E, F1, H1 |
| 5. Keller DAA / VAA / BAA / PAA styles | **Reject. The headline numbers are execution artefacts.** A paper Sharpe of up to 1.08 collapses with a one-month delay; explicit costs are 1.0–2.3 points a year at A$25,000; after tax they are 2.4–5.5 points behind 40/60. VAA top-one is the worst contestant in the race | A1, A2, G7, G8, H5 |
| 6. Risk parity / inverse volatility | Without trend: a low-return bond fund (CAGR 8.5–8.8% against 10.6% for S5), **dominated by S5**. With trend: the smallest drawdowns in the race (−5.5%, −7.7%) at 4.3–4.5 points a year less than 40/60 after tax. A capital-preservation tool, not a growth rule | E, F6 |
| 7. Regime (HMM, volatility switch, volatility-managed) | **Reject.** The HMM is significantly *worse* than 40/60 on return and Sharpe. Volatility-managed 40/60 trims drawdown by 6 points for 0.7 points of return. None helps in a fast fall | F1 |
| 8. Macro (yield curve, CAPE) | Yield-curve inversion: nothing (return −0.4, Sharpe 0.00). CAPE alone: costs 0.8–1.2 points. **CAPE gated by trend (M3) is the only contestant with positive point estimates on return, Sharpe and drawdown at once:** +0.57 points before tax, −0.35 after; t = 2.1 against a bar of 3.2. A paper candidate, no more | F1, G1 |
| 9. Ensemble of the six primaries | **No diversification benefit across algorithms.** Sharpe 0.39 net at A$25,000 (40/60: 0.41), after tax 3.6 points behind. Averaging rules that have no edge gives no edge and keeps their costs. The "slow three" (trend + risk parity + volatility-managed) is a slightly cheaper way to hold a low-drawdown mix | E, F1 |
| 10. Momentum sleeve at 10% | +0.19 points a year before tax [−0.05, +0.44], +0.18 after; drawdown unchanged. The proxy pays no internal trading costs, which for a monthly-rebalanced momentum portfolio could plausibly consume the whole 0.2. Consistent with card H14's expected "not passed" and with report 36 | F1, E |

How this maps to report 35's cards (preliminary evidence only, on substitute data): H31 dual-momentum control — behaves as a control should (no benefit). H33 inverse-volatility static mix — dominated by the fixed-weight mix S5. H35 downward-only volatility cap — H3 here: 6 points of drawdown for 0.7 points of return. H36 regime model — negative. H37 macro composite — CAPE alone negative; CAPE with trend the most interesting. H40 equal-weight blend — no benefit when the members have none. H30 (a wide trend ensemble in place of L1's votes) is nearest to T5 here: about the same drawdown as L1 (−24.9% against −27.1%) and 1.5 points a year less return because it trades 22 times a year; a graded or banded version is needed before that comparison is fair.

## 7. Recommendations

1. **Live rule at A$5,000, A$25,000 and A$100,000: no change.** STATIC 40/60, or L1 if H1 passes at G2 and the owner accepts paying about 1 point a year after tax (with a cash ETF) for a higher floor. No contestant in this tournament qualifies to replace either.
2. **If the owner wants materially smaller drawdowns, the supported lever is the strategic mix (card H70), not an algorithm.** It is feasible from about A$8,400 (smallest sleeve 15% of NAV at 1.25 × the minimum order) or at any size through one diversified fund. Its cost is the lower expected return of bonds, and that cost is uncertain: 1.7 points a year after tax on 1976–2023, 0.3 on 2007–2023.
3. **Do not enable the section 26 engine or P1 on the strength of Sharpe ratios.** Require the comparison against the static parent, after tax (card H72, and the amendment to H13 below).
4. **Paper challengers, in order of interest:** H71 (M3, valuation-gated trend; two sleeves, so it works at A$5,000); H70 (S5 as a shadow benchmark from day one); H72 (trend ensemble with a 10% band against S5); H73 (risk parity with trend, for a capital-preservation objective at A$100,000 or more).
5. **Register the failures as negative controls (card H74)** so that they are not re-proposed with new parameters, and so that a harness which shows them winning is audited for look-ahead.
6. **Treat any backtest of a rotation rule on same-bar monthly data as inadmissible** unless the one-month-delay figure is the headline.

## 8. Hypothesis cards (RND-010 format)

**Numbering.** The brief asked for IDs from H40. Reports 35, 39 and others have since used H30–H44, H50–H52 and H59–H63. To avoid a clash these cards are H70–H74; renumber at registration if the owner prefers.

**Common to all five cards.** Date registered and card hash: set at freeze. Approver: owner. Data: the RND-024 proxies where they exist, otherwise "not testable" (RND-029); the proxies of this report may be used only for a run labelled "substitute data". Development sample 1990-01 to 2023-12 as the spec's shared settings; the long sample 1976–2023 is a secondary report. **Holdout: 2024-01 to 2026-09 has been read in this tournament on substitute data and is recorded as "seen"; the confirmatory period for these cards is paper trading from the freeze date.** Costs and tax: the section 25 models, both CGT regimes. Trials already consumed by this exploratory tournament: 209, logged under family `T38`.

#### Card H70 — Static diversified mix against two-sleeve 40/60 (family P1, promotable as a STATIC variant)

| Field | Content |
|---|---|
| ID | H70 |
| Economic rationale | Written after this tournament and before any card run: government bonds and gold have low or negative correlation with shares in slow bear markets; a fixed mix needs no signal, trades about once a year and keeps the 12-month CGT treatment. Counter-rationale: bonds fell with shares in 1994 and 2022; the 1982–2020 bond bull market will not repeat from today's yields; gold has no income. |
| Exact rule | Hold VAS 22%, VGS 33%, VAF 15%, VBND 15%, a physical gold ETF 15%. Rebalance on the first execution date of July if any weight is more than 20% (relative) from target, minimum order A$1,000 (as PRT-22 for B2). Contributions go to the most under-weight sleeve (PRT-16(b)). No trend filter. |
| Fixed parameters | The five weights; yearly rebalance; ±20% band. |
| Permitted perturbation grid | Equity 55% → {45, 65}; gold 15% → {0 with bonds 45, 10}; VBND replaced by VAF. Five neighbours. |
| Data and proxy map | VAS, VGS as RND-024. VAF: AusBond Composite, or the RBA F2 duration model labelled synthetic. VBND: a hedged global aggregate index or a labelled proxy. Gold: a **month-end** AUD price (Perth Mint, or USD gold × RBA AUD/USD); a monthly-average series is not admissible. |
| Sample and holdout dates | As the common settings. |
| Benchmark | B2. |
| Primary metric (exactly one) | Maximum drawdown on month-end values, relative reduction against B2, paired stationary bootstrap (mean block 12, 10,000 paths). |
| Secondary metrics | After-tax CAGR difference under both regimes at 30% and 45% + Medicare; Ulcer; worst 12 months; result in 1994 and 2022; result from 2007 onward; terminal wealth in the A$5,000 + A$500 a month replay; cost at A$10,000, A$25,000, A$100,000. |
| Pass threshold | Drawdown at least one third lower with a 90% interval that excludes zero, **and** after-tax CAGR no more than 2.0 points a year below B2 under both regimes, **and** no more than 1.0 point below on the 2007-onward window. |
| Fail threshold | Drawdown-reduction interval includes zero, or after-tax CAGR more than 3.0 points lower. Between: "not passed". |
| Multiple-testing family and adjustment | Family A (protection). No return claim. Strategy family `P1`. |
| Trials consumed | 6 if the grid is run. Exploratory evidence in this report, at A$25,000: drawdown −15.4% against −40.1%, 90% interval of the difference [+9.8, +33.5] points; after-tax CAGR −1.7 points under both regimes on 1976–2023 and −0.3 on 2007–2023. |
| Result | — |
| Decision | Pass: the owner may select it as the STATIC mix for an account with sizing NAV of A$8,400 or more, by spec change and with the section 30 statement re-signed (it is a different risk level, not an improvement). It also becomes the benchmark V0 for P1. Not passed: stays as a shadow benchmark. |
| Approver | Owner |

#### Card H71 — Valuation-gated trend filter on 40/60 (family L2, paper; promotable only as a drawdown overlay)

| Field | Content |
|---|---|
| ID | H71 |
| Economic rationale | Trend filters cost return mostly through whipsaws in ordinary corrections. Large, slow bear markets have tended to start from high valuations. Applying the filter only when valuation is high should keep most of the protection in the slow bears and avoid most whipsaws. Counter-rationale: one country's CAPE has been "high" for most of the last 30 years; the gate was open in 2000 and 2007, which is what the sample would select for; the rule did nothing in 1987, 2020 or 2025. |
| Exact rule | At each month-end compute (a) the expanding percentile, since 1881, of the Shiller CAPE as published one month earlier; (b) whether the 40/60 portfolio's total-return index is below the simple mean of its last 10 month-end values. If the percentile is above 0.80 **and** (b) holds, hold 50% of each sleeve's base weight and the rest in the cash leg; otherwise hold base weights. Execution, bands and minimum orders as L1. |
| Fixed parameters | Percentile 0.80; reduction to 50%; 10-month average; one-month publication lag. |
| Permitted perturbation grid | Percentile {0.70, 0.90}; reduction {to 0%, to 75%}; average {8, 12} months; L1's three votes in place of the 10-month average. Seven neighbours. |
| Data and proxy map | CAPE from Shiller's published file (hash stored at each update); values after the last published month are **not** extrapolated: the last published value is carried forward. VAS, VGS as RND-024. |
| Sample and holdout dates | As the common settings. |
| Benchmark | B2; L1 as a second comparator. |
| Primary metric (exactly one) | Maximum drawdown, relative reduction against B2, paired bootstrap. |
| Secondary metrics | After-tax CAGR difference against B2 and against L1 (both regimes); switches per decade; share of the result from 2000–2003 and 2007–2009; one-month delay; 10th-percentile terminal wealth in the contribution replay. |
| Pass threshold | Drawdown at least 25% lower (90% interval excludes zero); after-tax CAGR within −1.0 to +0.5 points of B2; at least 80% of grid neighbours pass; the drawdown is still lower with 2007–2009 removed. |
| Fail threshold | No drawdown reduction, or after-tax CAGR more than 1.5 points below B2. A return uplift above +0.5 points triggers a look-ahead audit and no return claim (as H2). |
| Multiple-testing family and adjustment | Family A; counted in library N. Exploratory result: t = 2.1 against a reality-check bar of 3.2 (38 trials). |
| Trials consumed | 8 if the grid is run. Exploratory evidence at A$25,000: CAGR +0.57 points before tax [−0.24, +1.46], −0.35 after tax (regime B); drawdown −27.1% against −40.1% [+0.9, +16.9]; holdout: never triggered, equal to B2. |
| Result | — |
| Decision | Pass: 12 paper cycles beside L1, then an owner decision between L1 and H71 as the overlay. Not passed: stays in the registry. |
| Approver | Owner |

#### Card H72 — Continuous trend ensemble against its static parent, after tax (family P1; gate for section 26)

| Field | Content |
|---|---|
| ID | H72 |
| Economic rationale | Section 26's engine is justified by trend-following evidence from 50+ leveraged futures markets. On five long-only ETFs with no leverage the breadth and the leverage are absent, and monthly trading gives up the CGT concessions. The card asks whether anything is left. |
| Exact rule | T2 of this report: forecast = average of 3-, 6- and 12-month excess-return signals, each scaled to a mean absolute value of 10 on an expanding window, capped ±20, × 1.15, floored at 0. Weight = risk weight × 1.4 × 10% ÷ volatility × forecast ÷ 10, total capped at 100%, remainder in the cash leg. Risk weights VAS 0.22, VGS 0.33, VAF 0.15, VBND 0.15, gold 0.15. Volatility as SIZ-02. **No-trade band 10% of NAV** per sleeve; minimum order A$1,000. Monthly. |
| Fixed parameters | As stated. |
| Permitted perturbation grid | EWMAC pairs (1/3, 1.5/6, 3/12 months) in place of the three lookbacks; target 12%; band {5%, 15%}; the risk weights of H70's neighbours. Six neighbours. |
| Data and proxy map | As H70. |
| Sample and holdout dates | As the common settings. |
| Benchmark | **H70's static mix (V0)**, same sleeves, same costs and tax. B2 is reported, not the benchmark. |
| Primary metric (exactly one) | After-tax CAGR difference against V0 (regime B, 30% + Medicare, liquidation value) at A$100,000. |
| Secondary metrics | Maximum drawdown difference against V0; the same at A$25,000; regime A; 45% rate; one-month delay; 2022; realised against target volatility (SIZ-04). |
| Pass threshold | After-tax CAGR no more than 1.0 point below V0 **and** maximum drawdown at least one third lower than V0's (interval excludes zero), and both survive H12. |
| Fail threshold | After-tax CAGR more than 2.0 points below V0, or no drawdown reduction. |
| Multiple-testing family and adjustment | Family A. Strategy family `P1`; shares P1's holdout lock. |
| Trials consumed | 7 if the grid is run. Exploratory evidence at A$100,000 (2% band): after-tax CAGR 7.00% against 9.10% for V0 (−2.1); with a 10% band 7.42% (−1.7); drawdown −13.8% against −15.4% (one tenth lower, not one third). **Expected result: fail on drawdown; not passed or fail on return.** |
| Result | — |
| Decision | Pass: the section 26 engine may be proposed for P1 at Stage 2. Fail or not passed: SIZ-15 is not available to any account; P1 stays in paper; the question is closed for monthly five-sleeve implementations until breadth changes (for example a managed-futures fund, report 35 card H43). |
| Approver | Owner |

#### Card H73 — Risk parity with a trend filter as a capital-preservation mode (family P1, paper, A$100,000 or more)

| Field | Content |
|---|---|
| ID | H73 |
| Economic rationale | Equal risk across shares, bonds and gold, with each sleeve switched to cash when its own 12-month excess return is negative. The filter on the defensive sleeves is what a fixed mix lacks in a year like 2022. Counter-rationale: it is a bond fund most of the time; its long-run return is 4 points below shares after tax; the result leans on 1982–2020. |
| Exact rule | R4 of this report: weights ∝ budget ÷ 12-month volatility with budgets VAS 1/6, VGS 1/6, VAF 1/6, VBND 1/6, gold 1/3, normalised to 100%; a sleeve whose 12-month return is not above the cash return over the same 12 months is held as cash. Monthly; 10% no-trade band; minimum order A$1,000. |
| Fixed parameters | As stated. |
| Permitted perturbation grid | Filter: price above its 10-month average; volatility window 36 months; equal budgets across the five. Three neighbours. |
| Data and proxy map | As H70. |
| Sample and holdout dates | As the common settings. |
| Benchmark | H70's static mix (V0). |
| Primary metric (exactly one) | Maximum drawdown, relative reduction against V0. |
| Secondary metrics | After-tax CAGR difference against V0 and B2; worst 12 months; 1994 and 2022; real (CPI-deflated) after-tax return, which must be positive from 2007 onward. |
| Pass threshold | Drawdown at least 40% lower than V0's (interval excludes zero) and after-tax CAGR no more than 2.5 points below V0. |
| Fail threshold | Drawdown-reduction interval includes zero, or real after-tax return from 2007 onward at or below zero. |
| Multiple-testing family and adjustment | Family A. Strategy family `P1`. |
| Trials consumed | 4. Exploratory evidence at A$25,000: drawdown −7.7% against −15.4% [+4.0, +15.4]; CAGR −1.5 points before tax, −2.5 after (6.50% against 9.01%); 2022: −3.7% against −11.0%. |
| Result | — |
| Decision | Pass: available in paper as a preservation mode; live use needs a new owner objective statement (section 30) and the Stage 2 conditions. It is never described as a growth strategy. |
| Approver | Owner |

#### Card H74 — Negative controls: rotation, regime and curve rules (families R1 / X1, control, never promotable)

| Field | Content |
|---|---|
| ID | H74 |
| Economic rationale | These rules failed on 48 years of substitute data after costs. Registering them as controls (a) stops them being re-proposed with new parameters, and (b) gives the harness a look-ahead alarm: a harness in which they win is suspect. |
| Exact rule | Four rules exactly as coded in this report. G1: best of VAS / VGS by 12-month return if above cash, else VAF. K2: top 3 of six sleeves by 13612W momentum, with a cash share equal to the fraction of {hedged world, AU bonds} whose momentum is negative. H1: 40/60 scaled by a two-state HMM's predicted calm probability, refitted each December. M1: halve a sleeve while its home 10-year minus 3-month spread is negative. |
| Fixed parameters | As coded (`strategies.py`, SHA-256 in the trial log). |
| Permitted perturbation grid | None. |
| Data and proxy map | As H70; K2 needs a hedged world series. |
| Sample and holdout dates | As the common settings. |
| Benchmark | B2. |
| Primary metric (exactly one) | Net-of-cost CAGR difference against B2 at A$50,000 with a one-month execution delay. |
| Secondary metrics | The same with same-bar execution; Sharpe; drawdown. |
| Pass threshold | The controls behave as expected: no rule exceeds B2 by more than 0.5 points a year. |
| Fail threshold | Any rule exceeds B2 by more than 0.5 points net with the delay: **look-ahead and data audit of the harness**, not adoption (as H2). |
| Multiple-testing family and adjustment | Control; counted in library N. |
| Trials consumed | 4. Exploratory evidence, net at A$25,000, one-month delay: G1 −0.2; K2 −2.8; H1 −1.0; M1 −0.3 points (same-bar: −0.5, −0.7, −1.1, −0.4). |
| Result | — |
| Decision | None. Never promotable. A new rotation or regime idea needs a new card and an economic argument that these four do not already cover. |
| Approver | Owner |

## 9. Spec text

Exact wording, ready to paste. None of it changes live behaviour.

**9.1 Section 24, after RND-013 (new paragraph).**

> **Report 38 tournament.** Report 38 raced 47 rule configurations in nine families on substitute monthly data (Fama–French, RBA, AQR; 1976–2023) with 162 further execution and diagnostic runs. It was not a card run. Its 209 runs are entered in `trials` with family `T38` and replication kind `exploratory`, and count toward library N (LRN-05). Because it read 2024-01 to 2026-09, that period is recorded as seen for families `P1`, `L2`, `R1` and `X1` on substitute data; for cards H70–H74 the confirmatory period is paper trading from the card's freeze date. Cards H70–H74 are added (report 38, section 8). No family in report 38 met the bar to replace `L1` or `STATIC` at any account size.

**9.2 Section 24, card table, H13 row, "Primary metric → pass" (append).**

> …; and after-tax CAGR under both CGT regimes (RND-022) no more than 1.5 points a year below V0 [R38: tax, not brokerage, is the larger cost of a monthly multi-sleeve rule].

**9.3 Section 26.4, SIZ-15 (replace).**

> | SIZ-15 | P1 may replace L1 in a live account only if H6, H12, H13 **and H72** pass, the account meets the Stage 2 conditions, and change control (section 28) is followed. A Sharpe ratio higher than B2's is not evidence for promotion: on a long-only ETF set it reflects the bond share of the mix [R38 section 4.3]. | [R15 D8], [R20], [R38] |

**9.4 Section 26.1, SIZ-07 (append).**

> On monthly evaluation with ETF minimum commissions the no-trade buffer is at least 10% of sizing NAV per sleeve [design value — set by backtest, card H72]; report 38 measured more than 30 orders a year and 1.1 points a year of cost at A$25,000 with a 2% band.

**9.5 Section 26.1, SIZ-04 (append).**

> With no leverage the volatility target is an upper bound, not a target: report 38 measured realised volatility of 5.4–6.8% against targets of 10% and 12% on five sleeves. Reports must not describe the portfolio as "targeting" a volatility it cannot reach.

**9.6 Section 25, RND-028 (append).**

> For any rule whose signal gives the latest month's return a weight of one quarter or more (for example 13612W momentum), the one-month-delay result is the headline figure and the same-bar result is secondary [R38: a paper Sharpe of 1.08 fell to 0.69 with the delay].

**9.7 Section 25, "Routes to backtest history", gold row (append).**

> A monthly-average gold series is not admissible for any rule with a trend or momentum signal on gold; it must be a month-end price [R38 section 5.5].

**9.8 Section 9, new requirement after PRT-23.**

> | PRT-29 | **Sleeve feasibility.** A sleeve may be included in a live mix only if its base weight × sizing NAV ≥ 1.25 × `min_order_value_aud`. At A$5,000 that is a 25% sleeve; a 15% sleeve needs A$8,334 [computed]. Below that the mix is two sleeves or one diversified fund. | [R38 section 3.2] |

**9.9 Section 27, Stage 2 row, conditions (append).**

> …; H72 passed (the trend engine beats its own static mix after tax), or the account stays on its Stage 1 rule.

**9.10 Section 30 (append to the list of things the system does not claim).**

> No tested algorithm — trend ensemble, dual momentum, canary rotation, risk parity, regime model, macro overlay, ensemble or momentum sleeve — beat holding 40% Australian and 60% global shares after costs and tax on 48 years of data (report 38). Smaller drawdowns were available only by holding bonds, gold or cash, at a lower expected return.

## 10. What would falsify this

- Licensed index proxies (RND-024) giving materially different sleeve returns, especially a month-end gold series and a real AusBond Composite series.
- A harness run with next-day fills in which a rotation rule keeps its same-bar advantage.
- A tax agent's answer that makes switching cheaper than modelled (for example revenue-account treatment with losses offset against other income), or dearer.
- A forward decade in which bonds and gold fail together with shares for years (S5 would lose its drawdown advantage), or in which trends are long and clean (the T family would do better than here).
- Leverage or 50+ markets (a managed-futures fund): this tournament says nothing about trend following at that breadth.

## Appendix A. Code and outputs

| File | Purpose |
|---|---|
| `algo_tournament/run_all.sh` | Rebuild data, run everything, regenerate this report |
| `code/build_data.py` | Raw downloads → `data/derived/returns.csv`, `macro.csv`, `provenance.json`, `splice_report.txt` |
| `code/strategies.py` | The 47 contestants and their frozen parameters |
| `code/engine.py` | Dollar-level simulator: orders, costs, parcels, tax; performance statistics |
| `code/run_tournament.py` | Runs every trial at three sizes, two tax regimes, cost × 2, one-month delay; writes `out/metrics.csv`, `crash.csv`, `holdout.csv` and the return matrices; appends to `out/trials.jsonl` |
| `code/stats_mt.py` | Bootstrap intervals, deflated Sharpe, reality check, CSCV / PBO |
| `code/substudies.py`, `code/diagnostics.py` | Execution band, lifecycle, gold diagnostic |
| `code/make_tables.py`, `code/make_tables2.py`, `code/build_report.py` | Tables and this document (prose template: `code/report_template.txt`) |

SHA-256 (first 16 hex digits) at the time of writing: `code/strategies.py` 3526217e26db604e; `code/engine.py` 7d19e6127107f040; `code/run_tournament.py` a4415841751d5b78; `code/stats_mt.py` 09ee5f2013ae4555; `code/build_data.py` 62394c7d496f3ec6; `data/derived/returns.csv` 00ab7d4a69e4afab; `data/derived/macro.csv` 11e421b9e9481a6b.

Bootstrap seed 20261113; 10,000 paths; mean block 12 months. A full re-run appends 209 new records to `out/trials.jsonl`; it does not overwrite the log.
