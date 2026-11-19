# 55 — Big Wins engine: rounds 2–5 reopened, a rule that "adapts each year", and the 2024–2026 extension

Date: 2026-11-14. Status: research report on the unlicensed public data of report 51. Not a card run under RND-025. Research use only; general information, not financial advice.
Code, pre-registration, trial log, rules text and validator files: `scratchpad/bigwins2/` (section 9). Builds on reports 48, 51, 53 and 54. Report 53's files in `scratchpad/bigwins/` were not modified.

Every number in sections 2 to 5 comes from code run after a second pre-registration file was hashed (SHA-256 `c0e6c75f…`). Deviations are in section 6.

## 0. Answer first

**Nothing was adopted. The engine stays v0. The owner's request, "make it better for the newer years", was tested the only honest way available, and the answer is no: neither a more frequent review nor a rule that re-chooses itself every December from recent history did better than plain v0 on 2016–May 2024. The rules text is re-issued as v1.1 with the blind replication's 17 ambiguities resolved; no rule choice changed.**

| Question | Answer | Where |
|---|---|---|
| Why not just tune it on 2016–2024? | Those are the only years the rule was not built on. A rule chosen because it did well there will look good there by construction, and nothing is left to show whether the gain is real. Round 1 (report 53) and round 2 (here) both show a development gain of 1.2–1.6 points a year turning into a loss afterwards | Section 1 |
| Rounds 2–5 | Round 2 (review frequency) was run: 8 variants on 2001–2015. Best: monthly review, keep a holding while its score rank ≤ 90 (variant 2h): +1.2 points a year after tax in development. On the unseen period it gained 0.4 at A$25,000 and **lost 1.6** at A$100,000. Not an improvement; the loop stopped as declared. Rounds 3, 4 and 5 (19 variants) were not run | Section 2 |
| "Adapts each year" | Five pre-declared adaptive procedures, run forward from December 2005. The primary one (each December pick, from a fixed menu of four rules, the one with the best trailing 10 years) returned −0.2% / +0.7% a year after tax on 2016–May 2024 against v0's +0.7% / +2.3%. Four of five procedures were worse than v0 on the unseen years; one was 0.5 points better, which is inside the noise and failed every luck control. Random December choices did as well or better | Section 3 |
| Does any version beat the index on the unseen period? | No. After costs: v0 1.6% (A$25,000) and 4.0% (A$100,000); index 4.6%. Every variant and procedure tested here is at or below v0 or within half a point of it | Tables 2.2, 3.1 |
| 2024–2026 extension (weaker: survivors only) | v0 from June 2024 to 13 Nov 2026: +15.3% a year (A$25,000) and +11.0% (A$100,000) after costs against the index's +6.5%; 88th percentile of random portfolios. 2.5 years, 30 months, a universe from which every later delisting is missing. Encouraging, not evidence; not used for any choice | Section 4 |
| Luck controls | Deflated Sharpe ratio (325 trials): v0 0.02–0.04 on the unseen period; best candidate 0.05; bar 0.95. No variant or procedure passed any required control set | Sections 2–3 |
| Budget used | 17 of 41 rule versions; 3 of 6 looks at the unseen period; 5 walk-forward procedures. Trial count is now 303 + 17 + 5 = **325** | Section 5 |
| What changed in the rules text | `FINAL_RULES_v1.1.md`: trading calendar corrected (the old code traded on 1 Jan 2001 and 1 Jan 2009), volatility window stated exactly, 15 other points written out, measures defined, validator files produced. The corrected engine matches the validator's corrected run on every month-end NAV and every holdings list | Section 7 |

What this means, in one paragraph. Three attempts have now been made to improve this engine on past data — sell rules, review frequency, yearly self-adaptation — and each time what looked better on the years it was chosen on did worse on the years after. This is the same result as report 48 (asset-allocation rules) on a different problem with different data. The reason is the same: on 8 to 15 years of returns, the differences between sensible variants of one rule are smaller than the luck in each (report 54 measured about one point a year from a one-day change in a window). A procedure that chases the recent winner among them is chasing noise and paying extra brokerage and tax for it. The engine cannot be made "better for the newer years" by looking backward. What can be done is what is already decided: run v0 unchanged on paper, score it monthly against the index, and read the record at 36, 60 and 120 months.

## 0.1 Caveats

- **The unseen period has now been looked at eight times** (v0; 1c; 2h; five walk-forward procedures), nine counting report 54's four readings as one. Each look that rejects costs nothing; a look that had accepted would have needed the luck controls for exactly this reason.
- **Reopening a stopped loop is itself a second chance.** Report 53's pre-registration said the loop stops at the first failed look. It was reopened at the owner's request, with the variants already written and hashed before round 1, thresholds unchanged or stricter, and every version counted. It stopped again at its first look.
- **Rounds 3–5 remain untested** (number of names, weights, universe 200, industry cap, market-regime guards, signal changes). The declared stop rule forbids running them on this data. They stay parked (card H86).
- **Report 53's numbers move slightly** because of the calendar correction (section 7): v0 development 9.4% / 6.3% after costs (was 9.0% / 6.4%), unseen 1.6% / 4.0% (was 1.6% / 4.3%). No conclusion changes. Report 54 found the same.
- **Differences under about one point a year between two versions are noise** (report 54 §5.4). This was written into the adoption rule before any run (section 1).
- **The walk-forward menu is hindsight for 2006–2015**: its members were the development-period favourites. Only 2016–May 2024 is a fair test of the adaptive procedures, and that is where they are judged.
- **Index start value not fixed.** The XJO series is stale at 3,274.6 from 1 Dec 2000 to early Feb 2001. I could not reach a source for the true 29 Dec 2000 close (Stooq, Yahoo and the RBA's historical share-market table were refused or missing in this session), so the series is unchanged. If the close was 3,206.2 [from memory, unverified; a monthly series from the French data library implies about 3,214], the index's development CAGR is 3.39% rather than 3.24% and its whole-period CAGR 3.80% rather than 3.71%. Parts A, B and C here do not depend on it.
- All of report 53 §0.1 still applies: unlicensed data, price-only, approximate tax, today's industry groups, idealised execution.

## 1. What was declared before running (`PREREG_BW2.md`, SHA-256 `c0e6c75fa418e5c807c3deb303f0f820c7f14b1f4e55302411406417f236893f`)

1. **No tuning on 2016–May 2024.** Every choice is made on data dated before the period it is judged on.
2. **Corrections first** (from report 54): non-trading rows removed from the price file; the volatility window kept as report 51 registered it (252 returns); the industry count fixed. v0 on the corrected engine equals the validator's corrected run to five decimals and is the incumbent.
3. **Part A.** Rounds 2–5 exactly as listed in `PREREG_BW.md` section 4, development 29 Dec 2000 – 31 Dec 2015, at A$25,000 and A$100,000. Candidate of a round = best after-tax (no-discount) CAGR among variants that beat the incumbent at both sizes by ≥ 0.25 points on average without a drawdown more than 5 points deeper. One look at the unseen period per round. Adoption needs: better after tax at both sizes; ≥ 90th percentile of 200 random portfolios; paired bootstrap ≥ 0.90; deflated Sharpe ≥ 0.95 with all trials counted; and a new condition, **at least 1.0 point a year better on average** (the noise floor). Stop at the first look that does not improve.
4. **Part B.** Five adaptive procedures (section 3), one of them named primary and the only one that could be adopted; random-choice placebo added to the controls.
5. **Part C.** Extension to 13 Nov 2026 after everything is frozen; reporting only.

## 2. Part A — round 2, review frequency

### 2.1 Development, 2001–2015 (CAGR % a year; "after tax" = regime B, no discount)

| Variant | A$25k after costs | A$25k after tax | A$100k after costs | A$100k after tax | Mean after tax | Max drawdown A$100k | Turnover a year 25k / 100k | Candidate? |
|---|---|---|---|---|---|---|---|---|
| **v0** (December review) | 9.4 | 6.5 | 6.3 | 5.0 | 5.8 | −53% | 0.81 / 0.76 | — |
| XJO price index | 3.2 | 2.4 | 3.2 | 2.4 | 2.4 | −50% | — | — |
| 2a half-yearly | 8.7 | 5.4 | 6.6 | 4.7 | 5.1 | −50% | 1.47 / 1.35 | no |
| 2b quarterly | 6.7 | 4.7 | 7.3 | 5.1 | 4.9 | −42% | 2.45 / 1.95 | no |
| 2c monthly | 5.3 | 1.9 | 6.5 | 4.5 | 3.2 | −44% | 5.15 / 3.73 | no |
| 2d half-yearly, keep rank ≤ 60 | 8.8 | 6.0 | 7.2 | 5.8 | 5.9 | −50% | 1.07 / 1.11 | no (worse at A$25k) |
| 2e quarterly, keep ≤ 60 | 9.7 | 7.3 | 7.5 | 5.7 | 6.5 | −48% | 1.45 / 1.52 | yes |
| 2f quarterly, keep ≤ 90 | 9.0 | 6.9 | 8.3 | 5.9 | 6.4 | −45% | 1.04 / 1.08 | yes |
| 2g monthly, keep ≤ 60 | 8.3 | 6.2 | 7.3 | 5.4 | 5.8 | −46% | 1.96 / 2.31 | no |
| **2h monthly, keep ≤ 90** | 10.6 | 7.7 | 7.8 | 6.2 | 6.9 | −46% | 1.24 / 1.37 | **yes — best** |

Reading it: re-ranking more often without a buffer (2a–2c) costs up to 4.6 points a year in brokerage and short-term tax. With a wide buffer the extra reviews looked worth about a point after tax and 7 points of drawdown.

### 2.2 The look at the unseen period, 2016–May 2024 (look 3 of 6)

| | A$25k before costs | after costs | after tax B | A$100k before costs | after costs | after tax B | Max drawdown 25k / 100k | Turnover | Trades (8.4 years, A$100k) |
|---|---|---|---|---|---|---|---|---|---|
| XJO price index | | 4.6 | 3.3 | | 4.6 | 3.3 | −28% | | |
| v0 (incumbent) | 2.9 | 1.6 | 0.7 | 4.9 | 4.0 | 2.3 | −30% / −27% | 0.99 / 0.89 | 462 |
| 2h monthly, keep ≤ 90 | 4.2 | 1.9 | 1.2 | 2.4 | 1.1 | 0.8 | −33% / −28% | 1.47 / 1.44 | 774 |
| 2h minus v0 | +1.3 | +0.2 | **+0.4** | −2.5 | −2.9 | **−1.6** | | | |

Controls for 2h: mean after-tax difference −0.6 points (needed ≥ +1.0). Paired bootstrap share of paths ahead of v0: 0.12 (needed 0.90). Deflated Sharpe ratio against the index, 320 trials: 0.001 (needed 0.95). Random portfolios: exactly the 90th percentile at both sizes, which says little, because a random score reviewed monthly churns the whole list every month (random median −3.0% and −2.4% a year).

**Result: not better at A$100,000, so not an improvement under rule 3. The loop stopped. Rounds 3, 4 and 5 were not run.** The +0.4 at A$25,000 is inside the one-point noise band.

## 3. Part B — rolling-origin walk-forward: a rule that re-chooses itself each December

**Design.** At each December month-end from 2005 to 2023, using only data to that day, the procedure sets the rule for the next year. Accounts are fresh A$25,000 and A$100,000.

| Procedure | What it does each December |
|---|---|
| **W1 (primary)** | Runs each of four fixed rules over the trailing 10 years (from Dec 2000 while shorter) at both sizes after costs and tax; uses the best one for the next year. Menu, fixed by rule before the run: v0; v0 + trend exit (1c); monthly review with keep ≤ 90 (2h, round 2's development best); v0 + rank-collapse exit (1d) |
| W2 | As W1 with a trailing 5 years |
| W3 | Re-weights the four score components by their trailing 10-year rank correlation with next-12-month returns, shrunk half-way to equal weights |
| W4 | As W3 with 5 years |
| W5 | As W3 with six components (adds residual momentum and return consistency) |

**Table 3.1. CAGR % a year, prices only** (after tax = regime B)

| | 2006–May 2024: A$25k after costs / after tax | A$100k after costs / after tax | 2006–2015: A$25k | A$100k | **2016–May 2024**: A$25k after costs / after tax | A$100k after costs / after tax |
|---|---|---|---|---|---|---|
| XJO price index | 2.6 / 1.9 | 2.6 / 1.9 | 1.0 / 0.7 | 1.0 / 0.7 | 4.6 / 3.3 | 4.6 / 3.3 |
| **v0, fixed** | 5.9 / 3.2 | 3.9 / 2.9 | 9.2 / 5.2 | 2.8 / 2.6 | **1.6 / 0.7** | **4.0 / 2.3** |
| W1 menu, 10 years (primary) | 3.3 / 2.1 | 3.8 / 3.2 | 5.5 / 4.5 | 6.0 / 4.5 | 0.4 / −0.2 | 0.9 / 0.7 |
| W2 menu, 5 years | 1.8 / 1.8 | 4.4 / 2.9 | 4.6 / 3.8 | 4.9 / 3.2 | −1.5 / −1.5 | 2.3 / 1.2 |
| W3 weights, 10 years | 5.8 / 4.0 | 2.8 / 2.0 | 8.1 / 6.2 | 2.8 / 2.1 | 1.2 / 0.6 | 2.9 / 1.8 |
| W4 weights, 5 years | 4.1 / 3.7 | 2.0 / 1.4 | 6.3 / 5.3 | 1.5 / 1.0 | 1.2 / 0.5 | 2.6 / 1.3 |
| W5 weights, 10 years, 6 components | 4.8 / 3.2 | 3.7 / 2.9 | 4.9 / 3.6 | 3.5 / 3.0 | 2.5 / 1.3 | 4.1 / 2.8 |

(v0's A$100,000 account started in December 2005 shows 2.8% for 2006–2015 where the A$25,000 one shows 9.2%. Same rule, different number of names and a different path through 2008. That gap is the size of the luck in a single account.)

**Table 3.2. Luck controls on 2016–May 2024** (the fair window)

| Procedure | After tax minus v0, mean of the two sizes (needs ≥ +1.0) | Better than v0 at both sizes? | Random-portfolio percentile 25k / 100k (needs ≥ 90) | Percentile among 100 random December choices 25k / 100k (needs ≥ 90) | Bootstrap share ahead of v0 (needs ≥ 0.90) | Deflated Sharpe, 325 trials (needs ≥ 0.95) | Verdict |
|---|---|---|---|---|---|---|---|
| W1 (primary) | −1.3 | no | 52 / 50 | 47 / 6 | 0.03 | 0.001 | **fails all** |
| W2 | −1.7 | no | 33 / 80 | 21 / 36 | 0.16 | 0.008 | fails all |
| W3 | −0.4 | no | 33 / 47 | 30 / 11 | 0.12 | 0.015 | fails all |
| W4 | −0.6 | no | 32 / 40 | 29 / 6 | 0.06 | 0.013 | fails all |
| W5 | +0.5 | yes | 46 / 64 | 42 / 39 | 0.56 | 0.051 | fails all five controls |

**What the procedures actually chose.**

- W1's pick by December: 2005 2h; 2006–07 1d; 2008–13 trend exit; 2014 2h; 2015 trend exit; 2016 2h; 2017–18 trend exit; 2019–20 2h; 2021–22 v0; 2023 2h. Nine changes in 19 years. It chose the trend exit after 2008 (when a trailing window containing 2008 flattered it) and held it through years in which it lost; it chose plain v0 in only 2 of 19 years. W2 changed its pick 14 times.
- A coin-toss among the same four rules each December did as well as W1 at A$25,000 (W1 at the 47th percentile of random choices) and clearly better at A$100,000 (6th percentile). Past performance among these rules carried no usable information about the next year. This is report 48's finding again.
- The component weights barely moved: on 10 years of history they stayed between 0.17 and 0.30 (equal = 0.25). The four components are close to equally informative, which is what the fixed equal-weight score already assumes. The 5-year version moved more (12-month momentum down to 0.13 by 2022–23) and did worse.
- W5 is the only procedure ahead of v0 on the unseen years, by 0.5 points a year, with a 56% chance of being ahead on resampling and behind 58–61% of random weightings of the same six components. It could not be adopted under the declared rules whatever it showed, and it shows nothing.

**Result: no adaptive procedure is adopted. "Adapting each year" lowered the after-tax return in four cases of five and raised turnover by half for the menu procedures (1.3–1.5 a year against 0.9–1.0).**

## 4. Part C — extension to 13 November 2026 (survivor-only; weaker; chose nothing)

Run after the freeze. The price file after May 2024 contains only companies still listed in November 2026: a company that failed or was taken over after May 2024 is missing from the universe from that month, and a holding that delisted is paid at its last price in the file. This flatters any stock-picking rule and the random portfolios alike.

| Window | Account | v0 before costs | After costs | After tax A | After tax B | XJO after costs | XJO after tax B | v0 − XJO after costs | t | Max drawdown v0 / XJO | Random-portfolio percentile (median random) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| June 2024 – 13 Nov 2026 (2.5 years) | A$25,000 | 16.1 | 15.3 | 10.5 | 9.5 | 6.5 | 4.5 | +8.8 | 1.1 | −15% / −7% | 88 (3.5%) |
| June 2024 – 13 Nov 2026 | A$100,000 | 11.8 | 11.0 | 8.8 | 7.1 | 6.5 | 4.5 | +4.5 | 0.7 | −15% / −7% | 88 (4.3%) |
| 2016 – 13 Nov 2026 (10.9 years) | A$25,000 | 5.1 | 3.5 | 3.3 | 2.8 | 5.1 | 3.7 | −1.6 | −0.2 | −30% / −28% | 55 |
| 2016 – 13 Nov 2026 | A$100,000 | 5.9 | 5.1 | 4.2 | 3.4 | 5.1 | 3.7 | 0.0 | 0.2 | −27% / −28% | 75 |

Reading it: the last 2.5 years were good for the engine (ahead of the index by 4.5 to 8.8 points a year, with a drawdown twice the index's). Thirty months, t of 0.7 to 1.1, on a survivor-only universe, is not evidence of an edge. Joined to the clean unseen period, the engine from 2016 to today is level with the price index at A$100,000 and 1.6 points a year behind at A$25,000, before dividends, which favour the index by a further 1 to 4 points (report 53 Table 4.5).

## 5. Loop log (cumulative, reports 53 and 55)

| # | Version | Sample | Development result (mean after tax B, vs incumbent) | Unseen look | Unseen result vs incumbent (after tax B, 25k / 100k) | Decision |
|---|---|---|---|---|---|---|
| 1 | v0 | dev + unseen | — | look 1 | reference | incumbent |
| 2–9 | 1a–1h sell rules | dev | 1c best: +1.6 | look 2 (1c) | −3.2 / −0.6 | rejected; loop stopped (report 53) |
| 10 | 2a half-yearly | dev | −0.7 | — | — | no candidate |
| 11 | 2b quarterly | dev | −0.8 | — | — | no candidate |
| 12 | 2c monthly | dev | −2.6 | — | — | no candidate |
| 13 | 2d half-yearly keep ≤ 60 | dev | +0.1 | — | — | no (worse at A$25k) |
| 14 | 2e quarterly keep ≤ 60 | dev | +0.7 | — | — | candidate, not the best |
| 15 | 2f quarterly keep ≤ 90 | dev | +0.6 | — | — | candidate, not the best |
| 16 | 2g monthly keep ≤ 60 | dev | 0.0 | — | — | no candidate |
| 17 | 2h monthly keep ≤ 90 | dev | +1.2 | **look 3** | **+0.4 / −1.6** | rejected; loop stopped |
| — | rounds 3, 4, 5 (19 variants) | not run | — | — | — | parked (H86) |
| W1–W5 | five adaptive procedures | walk-forward 2006–May 2024 | n/a | 5 walk-forward exposures | W1 −1.0 / −1.6; W2 −2.2 / −1.1; W3 −0.2 / −0.5; W4 −0.3 / −1.0; W5 +0.6 / +0.4 | none adopted |

| Count | Value |
|---|---|
| Rounds run / allowed | 2 / 5 |
| Rule versions run / allowed | 17 / 41 |
| Looks at the unseen period, loop / allowed | 3 / 6 |
| Walk-forward procedures (each one trial, each touches the unseen period) | 5 |
| Trial count (report 51's log + loop + walk-forward) | 303 + 17 + 5 = **325** |
| LE-23 return bar at 325 trials | t ≥ 3.78 (was 3.77 at 312) [computed] |
| Adopted | 0 |

**v0 = v-final on the corrected engine** (CAGR % a year, prices only; DSR with 325 trials)

| Period | Account | Before costs | After costs | After tax A | After tax B | XJO after costs / tax B | Excess, annualised (t) | Max drawdown | DSR | Random-portfolio percentile |
|---|---|---|---|---|---|---|---|---|---|---|
| Development 2001–2015 | A$25,000 | 9.9 | 9.4 | 7.6 | 6.5 | 3.2 / 2.4 | +6.3 (2.5) | −55% | 0.60 | 100 |
| Development | A$100,000 | 6.8 | 6.3 | 5.4 | 5.0 | 3.2 / 2.4 | +3.2 (1.4) | −53% | 0.23 | 100 |
| Unseen 2016–May 2024 | A$25,000 | 2.9 | 1.6 | 1.1 | 0.7 | 4.6 / 3.3 | −2.3 (−0.5) | −30% | 0.02 | 37 |
| Unseen | A$100,000 | 4.9 | 4.0 | 3.1 | 2.3 | 4.6 / 3.3 | −0.3 (−0.1) | −27% | 0.04 | 63 |
| Whole 2001–May 2024 | A$25,000 | 8.1 | 7.6 | 5.9 | 4.6 | 3.7 / 2.8 | +4.0 (2.1) | −55% | 0.27 | 100 |
| Whole | A$100,000 | 6.5 | 5.9 | 5.0 | 4.5 | 3.7 / 2.8 | +2.4 (1.4) | −53% | 0.09 | 100 |

## 6. Deviations from the pre-registration

- The loop stopped at round 2, so the walk-forward menu has four members (v0, 1c, 2h, 1d), as the pre-declared rule for that case says.
- The first run of the extension crashed at the final sale on 13 November 2026 (no signal table for that day). Fixed to use the last month-end's liquidity ranks; no number had been produced; runs ending by May 2024 are unchanged.
- The random-portfolio control is a weak bar for rules that re-rank monthly (section 2.2). Recorded; it decided nothing.
- After the freeze, replications of v0 only: the tables of section 5, the index sensitivity, the validator files.

## 7. Rules text v1.1 and the blind replication's findings (report 54)

Nothing was adopted, so there is no `FINAL_RULES_v2.md`. `out/FINAL_RULES_v1.1.md` (SHA-256 `1be57c4a…`) is v0 with every ambiguity of report 54 section 6 resolved in words. Two points change numbers; fifteen do not.

| # (report 54) | Rule | Resolution in v1.1 | Behaviour change? |
|---|---|---|---|
| 1 | B2 volatility window | **252 daily log returns dated in the window; the first uses the close of the day before the window.** Chosen because it is the score exactly as report 51 registered and tested it. The other reading (251) scores 1 point higher on the unseen A$25,000 account; picking it now would be choosing on the unseen period | none (as built) |
| 2 | A1 trading day | Days the ASX traded. Rows on other days are deleted before anything is computed; the 30 rows are listed in the rule (seven holiday copies 1999–2009, 18 weekend rows, three 2024–25 holidays). Vendor copies on days the ASX was open stay | **yes — code fixed.** The engine no longer trades on 1 Jan 2001 or 1 Jan 2009 |
| 3 | A2 close with zero volume | Close kept; counts as a traded day; traded value zero | none |
| 4 | A5 industry group, reused codes | Looked up by the code the company last traded under, in the ASX file of 14 Nov 2026, with no code-change mapping; a dead company whose code is reused takes the present company's group. Stated as a back-test convention; live uses the file saved at the decision month | none (text now says what the code does) |
| 5 | B1 ties | Alphabetical company identifier | none |
| 6 | B6 price floor | Adjusted close as in the file | none |
| 7 | C1 delisting reason | Earliest ASX record for the last-traded code dated from 30 days before to 1,500 days after the last close; none = paid in full; list ends April 2020 | none |
| 8 | C1 "last trade ever" | Last close in the whole file (uses hindsight; stated) | none |
| 9 | C1/F payout | A disposal for tax; closes the position | none |
| 10 | C2 June NAV | Reported NAV is struck before the tax payment; n and T use NAV after it | none |
| 11 | C5/C7/C9 pending sales | "Awaiting sale" defined (deferred or carried full sale); a trim is not; such a holding keeps its pending sale, is not re-bought, and its place waits for the vacancy rule; **the industry count includes every live holding with a known group** | code aligned to text; no effect on any v0 number |
| 12 | D2 buy order | Cash test first; a waiting buy does not block later buys; "no trade" drops the buy only after the cash test passes; brokerage in the sizing on the amount, in the cost on shares × close; attempt days defined | none |
| 13 | D3 top-ups | Once, together, on the first attempt day with no buy waiting; dropped if no trade or under A$1,000; lapse at month-end | none |
| 14 | E2 rank date | Most recent month-end strictly before the trade day; final liquidation uses the end date's rank; no rank = 0.50%; tick on adjusted price | none |
| 15 | G whole period | One continuous account | none |
| 16 | G measures | CAGR, before/after costs, monthly return, excess, t, drawdown, turnover, trades, position, doubling, random control and deflated Sharpe each defined (G4–G8) | none |
| 17 | H validator files | Holdings after every month-end, trades, month-end NAV, closed positions and a summary, for both sizes and both periods: 20 files in `out/validator/` | files now exist |

Check of the corrected engine against the validator's independent corrected run (`replication_53/out/252/`): CAGR before costs, after costs and after both tax regimes equal to five decimals for all six accounts; tax paid equal to the dollar; **all 566 month-end NAVs equal to four decimals and all 562 holdings lists identical**.

Report 54's remaining code note (holiday trading) is fixed. Its index note is not (section 0.1): the true end-2000 close could not be confirmed here.

## 8. Spec-ready text: what changes for v2.14 (everything else in report 53 section 8 stands)

No rule, cap, mode or milestone changes. Replace or add the following.

| ID | Change |
|---|---|
| BW-08 | In (d) replace "over those days (consecutive traded days only; at least 200 returns)" with "of the 252 daily log returns dated in those 252 trading days (the first uses the close of the trading day before the window; a return exists only for two consecutive trading days that both have a close; at least 200 returns)". Replace "FINAL_RULES sections A and B" with "`FINAL_RULES_v1.1` sections A and B". Source adds [R54 §4.1], [R55 §7] |
| BW-06 | Add a sentence: "Before any signal is computed, rows dated on a day that is not in the official ASX trading calendar are deleted (weekend rows, vendor copies on public holidays); a day on which more than 5% of the universe repeats the previous close exactly is a WARN." Source [R54 §4.2], [R55 §7] |
| BW-11 | Add: "A trading day is a day of the official ASX calendar held in `calendar` (section 4), never a row of the price file." |
| BW-13 | Append to the evidence sentence: "More frequent reviews were tested in report 55: without a rank buffer they cost 0.7 to 2.6 points a year after tax in development; the best buffered version (monthly, keep rank ≤ 90) gained 1.2 points in development and lost 1.6 points a year at A$100,000 on the unseen period." Source adds [R55 §2] |
| BW-15 | Replace "counted over current holdings" with "counted over every current holding not awaiting sale that has a known industry group, whether or not it is still in the top 300" |
| BW-26 | Replace the sentence beginning "Making it better" with: "'Making it better' on past data is closed: the 2016–May 2024 window is spent (three loop looks and five walk-forward runs, reports 53 and 55). A rule that re-chooses its own variant or weights from trailing results is itself a change of rule under this requirement and was tested and rejected in report 55 §3; it may not be introduced as 'learning'." Rest unchanged |
| BW-30 | Replace "report 53's 9 rule versions; at 312 the return bar of LE-23 is t ≥ 3.77" with "the 17 rule versions and 5 adaptive procedures of reports 53 and 55; at 325 the return bar of LE-23 is t ≥ 3.78" |
| BW-31 | Add: "No job may re-weight the score's components, switch between rule variants, or change the review frequency from realised results (tested and rejected, report 55 §3)." |
| BW-40 | Replace "report 53's A$25,000 and A$100,000 accounts for 2016–May 2024" with "the accounts in `bigwins2/out/validator/` (report 55; corrected calendar) for 2001–2015 and 2016–May 2024", and "`FINAL_RULES`" with "`FINAL_RULES_v1.1`" |
| Section 17.3, H82 | "Exact rule" row: `FINAL_RULES_v1.1.md` of report 55 (hash in section 9). Reference results: section 5 of this report |

Cards.

| Card | Change |
|---|---|
| H82 | Rule text → `FINAL_RULES_v1.1.md`; development and unseen reference numbers → section 5 above; N_lib 325 |
| H86 | Now covers rounds 3, 4 and 5 only (19 variants). Round 2 is closed as H88. Rule for running unchanged: only on months after this freeze |
| **H88 — Closed: review frequency (round 2)** | Family `BW`, closed. Rules: H82 with half-yearly, quarterly or monthly reviews, with and without a keep-rank buffer of 60 or 90 (8 versions). Result: best in development 2h (monthly, keep ≤ 90) +1.2 points a year after tax; unseen +0.4 at A$25,000, −1.6 at A$100,000; bootstrap 0.12; DSR 0.001. Not adopted (RND-015). A different frequency or buffer is a new card and adds to N_lib. Trials consumed: 8. H85's shadow challengers (yearly review with keep ≤ 90; rank-collapse exit) are unaffected |
| **H89 — Closed: yearly self-adaptation** | Family `BW`, closed. Rules: each December choose among {v0, 1c, 2h, 1d} by trailing 10- or 5-year after-tax return; or re-weight the 4 (or 6) score components by trailing rank correlation with shrinkage. Result on 2016–May 2024: four of five behind v0 by 0.4 to 1.7 points a year after tax; one ahead by 0.5; none above the 50th percentile of random December choices at both sizes; DSR ≤ 0.05. Not adopted. Trials consumed: 5 |

## 9. Files and hashes

- Working directory: `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins2/`
  - `PREREG_BW2.md` (frozen copy `out/PREREG_BW2_frozen.md`, SHA-256 `c0e6c75fa418e5c807c3deb303f0f820c7f14b1f4e55302411406417f236893f`; with section 9.1 appended: second line of `out/prereg_bw2_hash.txt`); `PREREG_BW.md` unchanged
  - `out/FINAL_RULES_v1.1.md` (SHA-256 `1be57c4a3d79f940a236259b1a5e790dd972ee06a9475c6cd66260e08847b9a1`)
  - `code/`: `prep2.py` (corrected-calendar bundle, signals only), `engine.py` (report 53's engine plus: bundle path, industry count, schedule hook, component weights, trade/holdings tracking, extension end), `loop.py` (unchanged), `loop2.py` (reopened loop, LC4, guard placebo), `walk.py` (part B), `final2.py` (tables, extension, validator files), `chk1.py` (engine against the validator). Hashes: `out/code_hashes.txt`
  - `out/`: `trials_bw.csv` (27 rows: reports 53 and 55), `holdout_looks.csv`, `loop_state.json`, `round2_dev.csv`, `look_round2.json`, `walkforward.json` (picks, weights, every window, controls), `wf_trailing_scores.csv` (audit only), `final2_main.csv`, `index_sensitivity.json`, `validator/` (20 files)
  - `data2/bundle.pkl` (corrected calendar); `data/` is a link to report 53's read-only data
- Sources applied: reports 48, 51, 53, 54; `replication_53/out/252/` (the validator's corrected run, used as the check).
- Method notes: deflated Sharpe ratio and stationary bootstrap as in report 53 (implemented from memory of the papers [unverified against the originals]).
- Not verified in this session: the true XJO close of 29 December 2000 (no reachable source); everything listed as unverified in report 53 section 12.
