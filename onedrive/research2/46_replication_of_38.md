# 46 — Independent replication of report 38 (algorithm tournament)

Date: 2026-11-13. Subject: `research2/38_algorithm_tournament.md`, its tables file and `scratchpad/algo_tournament/`.
Method: blind re-implementation of five contestants from a written brief. Report 38, its tables and its code were not opened until my results were frozen (`replication_38/out_frozen_before_step3/`, `results.json` SHA-256 `a52228a85d4bc546b8e434db27f3873a1e6e330a3b709c573754f0f76eb0c615`). Everything labelled "step 3" came after.

## 1. Verdict

**The tournament's conclusion stands.** In my independent run no contestant beats static 40/60 on return with statistical confidence; rules that step out of equities cut drawdown and cost return. My engine, fed the tournament's own input series, reproduces its frictionless monthly returns for static 40/60, static 60/40, both L1 versions and GEM to within 0.00000001 a month. No coding error was found in the tournament for these contestants.

| Contestant | Report 38 (frictionless / net at A$25,000) | My independent run (0.138% cost) | My engine on the tournament's inputs | Class |
|---|---|---|---|---|
| Static 40/60 | CAGR 11.99 / 11.78%; max DD 39.9 / 40.1% | 12.19%; 39.8% | 11.99%; 39.9% (exact) | **REPLICATED** |
| Static 60/40 | 10.87 / 10.93%; 20.2 / 18.6% | 10.87%; 19.6% | 10.87%; 20.2% (exact, with its bond mix) | **CLOSE (explained)**: the headline matches, but partly by coincidence (section 4.2) |
| L1, idle cash 0% | 10.97 / 10.73%; 26.4 / 26.6% | 10.96%; 29.2% | 10.97%; 26.4% (exact) | Return **REPLICATED**; drawdown **CLOSE (explained)**, 2.8 points, pre-1990 global series |
| L1, cash at RBA rate / cash ETF | 12.27 / 11.98%; 26.4 / 27.1% | 12.25%; 27.2% | 12.27%; 26.4% (exact) | **REPLICATED** |
| Dual momentum GEM | 11.98 / 11.30%; 41.7 / 41.6% | 12.80%; 41.7% | 11.98%; 41.7% (exact) | Drawdown **REPLICATED**; return **CLOSE (explained)**, 0.8 to 1.5 points, data not rule (section 4.3) |
| 3/6/12-month trend ensemble | T2: 10.99 / 9.64%; 13.7 / 14.7% | 9.31%; 27.1% (cash 0%). 11.33%; 25.2% (cash at RBA) | not comparable | **NOT REPLICATED as a number: different rule** (section 4.4). Direction replicated |
| Conclusion: nothing beats 40/60 on return with confidence | 90% intervals all include zero or are negative; reality-check p 0.25–0.63 before tax | Same. Best P(CAGR difference > 0) is 0.62 (GEM). My reality-check p = 0.56 | 0 of 38 trials have a 90% interval above zero under my bootstrap | **REPLICATED** |
| Conclusion: trend rules cut drawdown and cost return | L1 −13.5 points of drawdown, −1.05 CAGR; T2 −25.5, −2.14 | L1 −10.6, −1.22; ensemble −12.6, −2.88 | — | **REPLICATED in direction**; see the two cautions in section 5 |

## 2. What I built (steps 1 and 2, before opening report 38)

**Window.** 1976-07 to 2023-12, 570 months, AUD. Signals at month-end t set the weights for month t+1.

**Data.**

| Series | Construction | Source |
|---|---|---|
| Australia, global | The frozen sleeve series of replication 36 (`replication_36/out_frozen_before_step3/sleeve_returns_base.csv`): French Australia local-currency market; French Developed market in USD from 1990-07, before that 50% US + 50% my fixed-weight basket of 13 French country files; converted at RBA F11 month-end rates. No fund fees | Ken French library, RBA F11 |
| Cash | RBA F1.1 interbank overnight rate, monthly average ÷ 12. For 1975-01 to 1976-04 (needed only for GEM's first 12-month cash look-backs) the 90-day bank bill rate | RBA F1.1 |
| Bonds | Australian Government 10-year yield at month-end. Return for month t = y(t−1) ÷ 12 − 7 × (y(t) − y(t−1)). Constant duration 7, no convexity term, no fee. Yields: historical monthly table to 1994-12 (last business day, per the RBA note); last daily observation of the month from 1995 | RBA `f02histhist.xls`, `f2histd.xls`, `f2-data.csv` |
| Gold | Monthly USD price from the `datasets/gold-prices` repository on GitHub (`data/monthly.csv`), divided by RBA month-end AUD/USD. **It is a monthly-average price.** The World Bank document server was blocked from this session. Gold is not used by any of the five contestants; it was built because the brief asked for it (7.35% a year, 18.4% volatility, 1976-07 to 2023-12) | GitHub mirror, RBA F11 |

No global bond series was built: the F2 table holds Australian yields only, so "bonds" means Australian government bonds throughout my run.

| File | Bytes | SHA-256 |
|---|---|---|
| `rba_f2hist/f02histhist.xls` | 115,200 | `8732bf2560f9ebcfa3657ac1830748ceafba50f549d152d7d02fcc7b75e4bb2f` |
| `rba_f2hist/f2histd.xls` | 598,016 | `5cf24d18a93545b8873df925efa385cd7901eec591eb084d0ba19448de845e66` |
| `rba_f2/f2-data.csv` | 202,265 | `ce557587cb80a8d5a2c288ae9bc0bcff15053e1b6caa08923dbc822c4eef8655` |
| `rba_f2/f2.1-data.csv` (not used) | 72,251 | `2e236c7c4162ccdf9e1e6c3e273177f6bb7606b6d505802507b3d761baf3a480` |
| `gold_datahub/monthly.csv` | 35,747 | `f20720f3413b3dd114cd116951516f0fab577ff8c91e102a3a92549582ea9608` |

Downloads were parsed as data only; Python ran with `-I`.

**Rules.**

| Contestant | Implementation |
|---|---|
| (a) Static 40/60 | 40% Australia, 60% global, rebalanced to target every month |
| (b) Static 60/40 | 24% Australia, 36% global, 40% Australian bonds, rebalanced monthly |
| (c) L1 | Per sleeve three votes on the total-return index: 6-month return > 0, 12-month return > 0, index above the mean of its last 10 month-ends. 0 votes → off; 2 or 3 → on; 1 → hold. Sleeves start on. Off money earns 0% (base) or the RBA cash rate (variant) |
| (d) GEM | Take the better of Australia and global by 12-month return. If it beats the 12-month compounded cash return, hold 100% of it; otherwise 100% bonds |
| (e) Trend ensemble | Per sleeve, weight = target × (number of 3-, 6-, 12-month returns above zero) ÷ 3. Remainder in cash at 0% (variant at the RBA rate) |

**Costs.** 0.138% of every dollar bought or sold in a sleeve, including monthly rebalancing trades; the cash leg is free. A full GEM switch trades two units (sell one, buy one). The opening purchase is not charged.

**Statistics.** Sharpe = mean excess return over RBA cash ÷ volatility. Maximum drawdown on month-end values. Paired stationary bootstrap, mean block 12 months, 2,000 paths, seed 38: the same resampled months for the strategy and for static 40/60; 5th and 95th percentiles of the differences. The bootstrap resamples realised returns; it does not re-run the signals.

## 3. My results (frozen before step 3)

1976-07 to 2023-12. Differences are against static 40/60. A negative drawdown difference means a shallower drawdown.

| Contestant | CAGR | Vol | Sharpe | Max DD | CAGR diff (pp) | 90% CI | P(diff > 0) | Max DD diff (pp) | 90% CI | Turnover a year | Average invested |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Static 40/60 | 12.19% | 12.86% | 0.43 | 39.8% | — | — | — | — | — | 0.20 | 100% |
| Static 60/40 | 10.87% | 8.74% | 0.44 | 19.6% | −1.32 | [−3.24, +0.45] | 0.12 | −20.2 | [−26.0, −7.2] | 0.24 | 100% |
| L1, cash 0% | 10.96% | 11.29% | 0.37 | 29.2% | −1.22 | [−2.94, +0.61] | 0.13 | −10.6 | [−24.9, +4.8] | 0.82 | 83% |
| L1, cash at RBA rate | 12.25% | 11.21% | 0.48 | 27.2% | +0.06 | [−1.73, +2.04] | 0.49 | −12.6 | [−26.8, +1.7] | 0.82 | 83% |
| GEM | 12.80% | 14.67% | 0.43 | 41.7% | +0.61 | [−2.18, +3.51] | 0.62 | +1.9 | [−20.3, +15.3] | 4.25 | 100% |
| Trend 3/6/12, cash 0% | 9.31% | 9.93% | 0.26 | 27.1% | −2.88 | [−4.55, −1.01] | 0.01 | −12.6 | [−26.9, +1.9] | 1.67 | 73% |
| Trend 3/6/12, cash at RBA rate | 11.33% | 9.88% | 0.44 | 25.2% | −0.86 | [−2.63, +1.09] | 0.21 | −14.6 | [−30.4, −1.7] | 1.67 | 73% |

Turnover counts buys plus sells as a multiple of the account. GEM held Australia 38% of months, global 38%, bonds 24%, with 101 switches.

What these say on their own:

- No contestant has a 90% interval for the CAGR difference that lies above zero. The only interval that excludes zero is negative: the trend ensemble with idle cash at 0%.
- Static 60/40 is the only contestant whose drawdown improvement is clear of zero in both tails. The trend ensemble with cash at the RBA rate just clears it. L1 does not, in either cash version.
- GEM does not reduce drawdown at all. Its worst loss is October 1987, in one month, fully invested.
- Every worst drawdown of a trend rule is 1987 (peak 1987-09). The two static mixes bottom in 2009-02.

## 4. Comparison with report 38 (step 3)

### 4.1 What the tournament did differently from my brief

| Item | My brief | Report 38 |
|---|---|---|
| Sample | 1976-07 to 2023-12 | 1976-01 to 2023-12 |
| Fund fees | none | 0.07% Australia, 0.18% global, 0.10% bonds, 0.10% cash, deducted from the series |
| Global before 1990-07 | 50% US + 50% my 13-country basket | 45% US + 55% French international index |
| Bonds | 10-year yield, duration 7 | 50% 5-year + 50% 10-year par bond, repriced monthly |
| Costs | 0.138% of trades, monthly rebalancing | "Paper" = no cost. "Net" = dollar-level engine: commission with a A$6.60 minimum, spreads, A$1,000 minimum order, yearly band rebalancing for static mixes |
| Static 60/40 | 40% Australian bonds | 20% Australian bonds + 20% hedged global bonds (AQR series) |
| L1 start state | on | off until the first two-vote month (1975-12) |
| Trend ensemble | binary 3/6/12 votes on the two equity sleeves, rest in cash | T2: continuous forecasts on five sleeves including bonds and gold, volatility-targeted |

Series check, 1976-07 to 2023-12, my series against the tournament's before fees: Australia identical; gold identical (same file); cash identical to 0.001% a month; global 12.10% against 11.83% a year (correlation 0.998; the gap is all before 1990-07, 22.0% against 21.0% a year); bonds 8.28% against 8.06%, volatility 8.2% against 6.3% (correlation 0.979).

### 4.2 Ladder from my run to the tournament's frictionless table

One change at a time, my engine. CAGR, with maximum drawdown in brackets where it moves.

| Step | 40/60 | 60/40 | L1 cash 0% | L1 cash RBA | GEM |
|---|---|---|---|---|---|
| A. My run | 12.19 | 10.87 | 10.96 (29.2) | 12.25 (27.2) | 12.80 |
| A with only the tournament's global series | 12.01 | 10.76 | 10.83 (26.4) | 12.14 (26.4) | 11.80 |
| A with only the tournament's bond series | 12.19 | 10.75 | 10.96 | 12.25 | 12.29 |
| B. All tournament inputs, before fees | 12.01 | 10.65 | 10.83 (26.4) | 12.14 (26.4) | 11.37 |
| C. + fund fees | 11.86 | 10.52 | 10.74 | 12.04 | 11.28 |
| D. + start 1976-01 | 11.96 | 10.58 | 10.85 | 12.14 | 11.32 |
| E. + L1 starts off | 11.96 | 10.58 | 10.85 | 12.14 | 11.32 |
| F. + no trading cost | 11.99 | 10.62 | 10.97 | 12.27 | 11.98 |
| Report 38, frictionless (Table A1) | 11.99 | 10.87 | 10.97 | 12.27 | 11.98 |
| Report 38, net at A$25,000 (Table B1) | 11.78 | 10.93 | 10.73 | 11.98 | 11.30 |

At step F the monthly returns equal the tournament's `returns_paper.csv` to 4 × 10⁻⁹ or better for 40/60, both L1 versions and GEM. Static 60/40 matches to 5 × 10⁻⁹ once the bond leg is 20% Australian + 20% hedged global bonds (10.87%, volatility 8.22%, drawdown 20.2%).

Step D is the like-for-like comparison with the net table: my flat 0.138% cost against the tournament's dollar engine. The gaps are 0.18 points (40/60), 0.12 (L1), 0.16 (L1 with cash) and 0.02 (GEM). All are inside tolerance and are what a minimum commission, cash drag and yearly rebalancing should cost.

### 4.3 Each difference above tolerance

**Static 60/40: headline agrees, components do not.** My 10.87% equals the tournament's 10.87% only because two differences cancel. With Australian bonds alone, the tournament's data gives 10.62% (step F). Its 60/40 holds half its bonds in a hedged global bond series that returned 9.24% a year against 7.97% for its Australian bond series, which adds 0.25 points. On my side, my global equity and bond series together add 0.22 points and the absence of fund fees adds 0.13, less small window and cost effects. The rule text I was given ("60/40 equity/bonds") allows either bond mix; the tournament states its mix. The drawdown, about 20%, and the bootstrap verdict (return difference noise, drawdown clearly better) agree. Volatility is 8.7% in my run against 8.2% because a duration-7 proxy of the 10-year bond is more volatile than a 5-year/10-year blend.

**L1 with idle cash at 0%: drawdown 29.2% against 26.4%.** Cause: the global series before 1990-07. Swapping in the tournament's global series alone gives 26.4%. Both worst drawdowns start at 1987-09; mine runs to 1988-11, the tournament's to 1987-11. Replication 36 found the same sensitivity. The tournament's international leg (French's own index) is the better-founded choice than my fixed-weight basket. Its figure is the one to keep. The L1 start state changes nothing from 1976.

**GEM: 12.80% against 11.98% frictionless, 11.30% net.** The rule and the code are the same; with the tournament's inputs my engine reproduces its GEM returns to machine precision. The gap is data:

| Cause | Effect on GEM CAGR |
|---|---|
| Global series before 1990-07 | −1.00 point. The holding differs in only 7 months, all between 1981 and 1987. From 1990-07 both series give 10.06% |
| Bond series | −0.51 on its own |
| Both together (they interact) | −1.43 |
| Fund fees, six extra months | −0.05 |
| No trading cost (frictionless table) | +0.66 |

GEM holds 100% of one asset, so a small difference in one input series moves the result about five times more than it moves static 40/60 (1.00 point against 0.18 for the global series). Neither series is "wrong"; the tournament's is the better-founded one before 1990. The finding that survives is the one both runs share: the interval for the difference against 40/60 is about ±3 points wide and centred near zero (mine +0.61 [−2.18, +3.51]; the tournament's −0.48 [−3.39, +2.51] net), and the drawdown is no better than 40/60's (41.7% in both).

### 4.4 The trend ensemble is a different rule

My brief defined the ensemble as binary 3-, 6- and 12-month votes on the two equity sleeves, with the remainder in cash at 0%. No contestant in the tournament is that rule. Its "3/6/12m TSMOM blend" (T2) uses continuous, volatility-scaled forecasts of excess return over cash on five sleeves (22/33/15/15/15 risk weights across Australian shares, global shares, Australian bonds, global bonds, gold), sized to a 10% volatility target, with the remainder in a cash ETF. Its nearest two-sleeve rule (T5) uses moving-average crossovers, not 3/6/12-month returns.

| | CAGR | Vol | Max DD | CAGR diff vs 40/60 | DD change vs 40/60 |
|---|---|---|---|---|---|
| My rule, cash 0% | 9.31% | 9.9% | 27.1% | −2.88 [−4.55, −1.01] | −12.6 |
| My rule, cash at RBA rate | 11.33% | 9.9% | 25.2% | −0.86 [−2.63, +1.09] | −14.6 |
| My rule on the tournament's inputs, no cost, cash 0% / cash ETF | 9.59% / 11.63% | 9.9% | 25.8 / 24.7% | — | — |
| Report 38 T5 (two equity sleeves), frictionless / net | 11.42 / 10.49% | 9.4% | 24.8 / 24.9% | −1.29 [−3.53, +1.16] net | −15.3 |
| Report 38 T2 (five sleeves), frictionless / net | 10.99 / 9.64% | 6.1% | 13.7 / 14.7% | −2.14 [−5.16, +0.98] net | −25.5 |

The numbers cannot be reconciled and should not be: T2's drawdown of 14% comes from holding bonds and gold, which my rule does not hold. The like-for-like pair is my rule with cash earning interest against T5: 11.3–11.6% against 11.4%, volatility 9.9% against 9.4%, drawdown 25% against 25%. That agreement is between two different trend rules on the same two sleeves, so it supports the tournament's ranking, not its T2 figures. I did not re-implement T2's signal construction; its forecast scaling has details that are in the code and not in the report text.

Per the rule text of my brief, my figures are the right ones for that rule, and the tournament's are right for its declared T2. The brief's description of the tournament contestant was too loose to pin down one rule.

## 5. The return and drawdown claims

**Return: replicated.**

- My run: the highest probability that any contestant's CAGR beats 40/60 is 0.62 (GEM); L1 with interest-bearing cash is 0.49. Nothing approaches 0.95.
- My bootstrap (2,000 paths) applied to the tournament's own return files reproduces its Table F1 intervals for the contestants I checked to within 0.1 point at most ends and 0.2 at the worst (60/40 −0.85 [−2.60, +0.81] against its [−2.56, +0.87]; L1 −1.05 [−2.68, +0.72] against [−2.61, +0.67]; GEM −0.48 [−3.43, +2.47] against [−3.39, +2.51]; T2 −2.14 [−5.20, +0.80] against [−5.16, +0.98]).
- Across all 38 long-sample trials in the tournament's files, none has a 90% interval for the CAGR difference above zero under my bootstrap, frictionless or net at A$25,000. The closest is the 10% momentum-sleeve mix (probability 0.90–0.91, 5th percentile −0.04 points), which matches the report's "+0.2 points with an interval that includes zero".
- Reality check, qualitative. On my own six non-benchmark series I formed the active return against a blend of 40/60 and cash with the same volatility. Best t-statistic 0.77 (L1 with cash at the RBA rate); 95% critical value for the maximum of six, 2.37; p = 0.56. The tournament reports a best t of 2.1–2.3 against a bar of 3.2 with p of 0.25–0.33 for 38 trials. Same answer: nothing passes. Its best trial (M3) is not one I built, so I cannot confirm that t-statistic itself.
- Not checked: deflated Sharpe values, PBO figures, the 1991+ sample, tax, account-size effects, the holdout. The PBO claim that in-sample winners do not persist is consistent with what I see (GEM's sign against 40/60 flips with seven months of one input series) but I did not compute it.

**Drawdown: replicated in direction, with two cautions.**

- Static 60/40 cutting maximum drawdown by about 20 points with an interval clear of zero is confirmed in my run (−20.2 [−26.0, −7.2]) and on the tournament's returns.
- L1 with idle cash at 0%: "noise" in both studies (mine −10.6 [−24.9, +4.8]; the tournament's 13.5 points shallower [−1.7, +24.5] in its sign convention).
- Caution 1. The tournament labels L1 with a cash ETF "better" on drawdown. Its interval's lower end is +0.09 points. My bootstrap on its own returns gives a lower end of 0.0, and my independent run gives an interval that includes zero ([−26.8, +1.7]). That label rests on a few hundredths of a point and should read "borderline".
- Caution 2. For the brief's ensemble with idle cash at 0% the return cost is significant before tax (−2.88, interval [−4.55, −1.01]), which is harsher than the tournament's "noise" for T2. The cause is 27% of the account earning nothing. With cash earning the RBA rate the interval includes zero, as the tournament finds.

## 6. Limits of this replication

- Five of 47 contestants, and only before tax. The two static mixes, L1 and GEM are confirmed at the level of monthly returns; the trend family is confirmed only in direction.
- The Australian, cash and gold inputs are the same public files in both studies, so agreement on them is a check of parsing, not of the data.
- My bond series is a duration approximation and my gold series is a monthly average. Neither changes a verdict; bonds move GEM by 0.5 points.
- My bootstrap resamples realised strategy returns. So does the tournament's. Neither tests the rules on resampled price paths.
- After opening the tournament I saw its code before writing the reconciliation script, so section 4 is a reconciliation, not a blind result. Section 3 is blind.

## 7. Files

All under `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/replication_38/`.

| File | Purpose |
|---|---|
| `code/data38.py` | Yield, bond, gold and cash series; loads the replication-36 sleeves |
| `code/tourn38.py` | The five contestants, engine, metrics, bootstrap (steps 1–2) |
| `code/reconcile38.py` | Step 3 ladder, comparison with the tournament's return files, reality check |
| `out_frozen_before_step3/` | Results, returns, weights and code as they stood before report 38 was opened |
| `out/log_step3.txt`, `out/ladder.csv` | Step 3 output |
