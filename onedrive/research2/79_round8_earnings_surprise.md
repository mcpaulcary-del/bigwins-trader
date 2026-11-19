# 79. Round 8: earnings surprise (EODHD analyst estimates) on ASX, with a 12-market replication

19 November 2026. Research and paper only. General information, not financial or tax advice. Nothing here can place an order.
Work folder: `scratchpad/improve8/` (`PREREG_79.md`, `code/`, `out/`, `data/`, `PROGRESS.md`). Trial ledger: `out/trials_79.csv` (cumulative count **1,649 → 1,709**). Nothing was written to `68_forward_record/`, the ledger, or any scheduled job. No new data was downloaded; every file was already archived.

## 0. Summary in plain English

**Did it beat the index after costs? No.** The design chosen in advance on 2016–2020 ASX data (M3 with an earnings-surprise tilt) trailed the ASX 200 accumulation fund in the 2021–2026 ASX holdout:

| ASX holdout, Dec 2020 – Oct 2026 | A$25,000 | A$100,000 |
|---|---|---|
| Lead over the index fund, after costs and tax (points a year) | **−1.4** | **−1.5** |
| Lead after costs, before tax | −2.7 | −2.0 |
| Share of 200 matched random-pick books it beat | 54% | 76% |
| Deflated Sharpe ratio at N = 1,709 | 0.00 | 0.00 |

- **Replication across 12 other markets also failed.** It was ahead by at least +1 point at both sizes in 4 of the 12 markets. The bar was 7. It beat 90% of random books in 1 of the 12, against 7 needed. On average the surprise tilt made M3 **worse**, by −1.5 points at A$25,000 and −0.5 at A$100,000, and it was ahead of plain M3 at both sizes in only 2 of 12 markets.
- **None of the other seven surprise designs looked better in the holdout.** Seven were standalone or cap-weight-tilt versions and were run in the holdout for information only. The best was +1.1 / +0.4, and the plain cap-weighted book with no surprise tilt beat it (+2.6 / +1.0).
- **Confidence: high that this does not meet the bar.** Every pre-registered item except the data-validity gate failed. The design's own development result (+4.7 / +2.4) was already below plain M3 in the same years (+8.2 / +2.4).
- **Shadow line: no.** No AMENDMENT has been drafted. Real money stays in the 40/60 plan.
- **The data were the main limit.** The vendor's ASX "actual" and "estimate" often seem to measure different things. The median miss is 40%, and actual and estimate have opposite signs in 22% of rows. About a quarter of the values are placeholder zeros. Coverage collapses in 2023–24, and companies that later delisted mostly have no estimates. Still, the estimates are not random noise: on results day, share prices did move in the direction of the surprise (section 3).

---

## 1. Data audit (done before any return was computed; `out/audit.log`, `out/coverage.csv`)

| Check | Finding | Consequence |
|---|---|---|
| Files | 295 ASX files. The list was every company among the 100 most traded at any time since 2012, so dead companies were requested. 240 files have estimate rows | — |
| Dated rows with actual and estimate | Fewer than 25 a year before 2014. Then 204–445 a year from 2014 to 2025: 2014 221, 2016 301, 2019 366, 2022 445, **2024 322 (120 companies against 200 in 2022)**, 2025 368 | Development has to start in mid-2016 |
| Announcement dates | Median 49 days after the period end (1%–99%: 16–87 days). Reports cluster in February and August (half-yearly), with May and November for September/March year-ends. Before 2013, 54–68% of report dates are placeholders equal to the period end; from 2016 on, almost none are | Rows dated less than 14 days after the period end are dropped |
| Is the estimate point-in-time? | **Cannot be verified from the file.** There is one number per report, with no timestamp and no analyst count. `surprisePercent` and `epsDifference` match (A − E)/\|E\| and A − E in all 3,474 rows. That shows internal consistency, not timing | Tested indirectly by the validity gate in section 3 |
| Do actual and estimate measure the same thing? | Often not. The median \|A − E\|/\|E\| is **40%** (a real consensus miss is a few per cent). Signs differ in **22%** of rows. Only **42%** of ASX surprises are positive, against **64%** in the US file, where most companies beat consensus. This looks like statutory actuals compared with underlying-earnings consensus, plus mixed periods. For example, the BHP and FMG estimates look like a different period or basis from the actual | Surprise is clipped to ±100% and used only as a rank. The SUE version is scaled by the company's own past misses |
| Placeholders and stale copies | 25% of rows have actual exactly 0 and 19% have estimate exactly 0 (WES in 2014–15, for example). 480 actuals, 263 of them with estimates, repeat the previous period's figure | Dropped |
| **Survivorship** | No file is flagged delisted. Among companies in the 100 most traded at December 2015–2019, a fresh estimate exists for **25–71% of those that later delisted**, against **90–93% of survivors**. Companies with no estimate cannot be scored, so the scored set leans towards survivors. The bias is smaller in 2021–22 (70–86% against 90–95%) | Probably flatters any surprise book a little, so the failure is not caused by it |
| Coverage of the 100 most traded (fresh estimate ≤ 200 days, December) | 2015 13%; 2016–2022 68–80%; **2023 35%; 2024 23%**; 2025 77% | The holdout has a thin patch in 2024. The M3-tilt design falls back to plain M3 there |
| ASX code re-use | Three pack codes have more than one listing life. Rows are used only inside the matching listing's trading life | — |
| Other markets | Estimate coverage is at least 60% of the 100 most traded at both Dec 2019 and Dec 2023 in Germany, Sweden, Canada, US large/mid/small, Korea, Taiwan, Thailand, China, Brazil and Norway. Coverage is too thin in the UK, France, the Netherlands, Switzerland, Denmark, Spain and South Africa (3%). Only the US (300) and Brazil (36) files include delisted-flagged companies | Those 12 markets form the replication set, fixed before any return |

## 2. Pre-registration

`improve8/PREREG_79.md`, SHA-256 **`6b5bf086362b752f24e9d882b87cee121dacb0c846350a99bf3a7d8d962e24d5`**. It was frozen at 2026-11-19T03:43:13Z at N = 1,649, before any return using the signal was computed. The hashes of all code and data files are in `out/prereg79_sha256.txt`. The only thing computed before the freeze was a machinery test that printed holdings counts and run times.

- **Signal.** SP = (actual − estimate)/\|estimate\|, clipped to ±1. SUE = (actual − estimate) ÷ the standard deviation of the company's previous 3–8 misses. A score is taken from the latest report dated **strictly before** the month-end decision date and is valid for 200 days ("until the next report"), or 92 days (about 60 trading days) in one variant. Shares are bought at the **next session's close** after the month-end, so every entry comes at least one full session after the announcement and on average about two weeks after it. There is no look-ahead.
- **Costs and engine.** Unchanged from rounds 5–6 (`improve6/code/sim6.py`): brokerage max(A$6.60, 0.088%) plus half-spread (0.10% for the top 100, 0.25%, then 0.5%, with the ASX tick floor), tax at 32% with the 12-month discount, and a fund fee of zero. Books of A$25,000 and A$100,000, each the mean of four start months.
- **Eight designs** (each a counted trial):
  - three standalone books (SP 200 days, SUE 200 days, SP 92 days);
  - two tilts on M3 (half index fund plus up to 30 shares, score = mean of the M3 and surprise percentiles);
  - two tilts on the cap-weighted core of report 77;
  - one cap tilt on M3 plus surprise.
  - Four descriptive rows: M3, CW (cap-weighted, no tilt), EI10, and H80M3 (the H80 score behind H82, in M3's structure; a proxy, not the H82 rules).
- **Choice rule.** Best mean development result over the two sizes on ASX, starts June 2016 to March 2017, ending Dec 2020. Holdout: ASX, starts Dec 2020 to Sep 2021, ending Oct 2026. Replication: the 12 markets, starts Dec 2018 to Sep 2019, ending Oct 2026.
- **Bar** (all required for a shadow line):
  1. the validity gate passes;
  2. the ASX holdout is at least +1 point at both sizes;
  3. the ASX holdout is at or above the 90th percentile of 200 random books at both sizes;
  4. the replication is at least +1 at both sizes in 7 or more of the 12 markets, and below −2 in no more than one;
  5. the top five positions make up less than 50% of profit;
  6. the deflated Sharpe ratio is reported.
- **Expected result, written down beforehand:** "within ±1 point, bar not met."

## 3. Validity gate: do the estimates behave like pre-report consensus? (`out/gate.json`)

The gate checks the share-price move from the day before to the day after the announcement, measured against the ASX 200. It compares that move with the surprise, using the dated ASX rows.

| Period | Rows | Spearman ρ (SP) | t | Top-third surprise, 3-day move | Bottom third |
|---|---|---|---|---|---|
| 2014–2020 (gate) | 1,274 | +0.08 | 2.9 | +1.3% | −0.2% |
| 2021–2026 | 1,231 | +0.11 | 4.0 | +1.1% | −0.8% |
| SUE, 2014–2020 / 2021–26 | 894 / 1,119 | +0.13 / +0.13 | 3.9 / 4.5 | | |

**The gate passed, but weakly.** The market does react in the direction of the vendor's surprise, so the estimates carry real information and are probably mostly pre-report. However, ρ ≈ 0.1 is a weak link: genuine consensus surprises usually give ρ of 0.2–0.3. This fits the definition mismatch found in the audit. The 3-day reaction is also already over before the first possible month-end entry.

## 4. Development (ASX, June 2016 – Dec 2020; `out/dev.log`)

Lead over the index fund in points a year, A$25,000 / A$100,000.

| Design | After costs and tax | After costs, before tax | Turnover |
|---|---|---|---|
| Standalone SP | +0.1 / −2.4 | +0.1 / −3.4 | 0.65 |
| Standalone SUE | −0.5 / −1.3 | −1.8 / −1.4 | 0.58 |
| Standalone SP 92 days | +2.9 / −1.0 | +3.8 / −1.7 | 1.35 |
| M3 + SP | +1.6 / +1.7 | +1.9 / +2.3 | 0.52 |
| **M3 + SUE (chosen)** | **+4.7 / +2.4** | +7.5 / +3.0 | 0.45 |
| Cap tilt SP | +0.6 / +0.7 | +1.1 / +2.0 | 0.39 |
| Cap tilt SUE | +2.0 / +3.1 | +2.8 / +3.6 | 0.45 |
| Cap tilt M3 + SP | +2.0 / +1.5 | +2.1 / +2.6 | 0.44 |
| *M3 (no surprise)* | *+8.2 / +2.4* | *+9.9 / +2.9* | 0.48 |
| *CW (cap-weight, no tilt)* | *+2.7 / +2.3* | *+3.3 / +3.0* | 0.29 |
| *EI10* | *+2.9 / +2.4* | *+4.4 / +2.9* | 0.43 |
| *H80M3 (H82 proxy)* | *+0.2 / −0.6* | *+0.3 / −0.4* | 0.42 |

The warning was already visible in development. The rule chose M3 + SUE, yet it was behind plain M3 (+8.2 / +2.4) and roughly level with the untilted cap-weighted book. The standalone surprise books were the weakest. Even in-sample, the surprise added nothing to the cores it was laid on.

## 5. ASX holdout (Dec 2020 – Oct 2026; `out/hold.log`, `out/summary.log`)

Lead over the index fund in points a year, A$25,000 / A$100,000. The index fund returned 6.9% a year after tax.

| Design | After costs and tax | After costs, before tax | Tracking error (A$100k) |
|---|---|---|---|
| **M3 + SUE (eligible)** | **−1.4 / −1.5** | −2.7 / −2.0 | 4.9 |
| Standalone SP | −2.9 / −0.6 | −1.0 / −0.4 | 5.7 |
| Standalone SUE | −1.9 / −1.6 | −2.4 / −1.9 | 5.0 |
| Standalone SP 92 days | −0.5 / −1.5 | −0.8 / −1.9 | 5.0 |
| M3 + SP | −0.5 / −1.6 | −1.1 / −1.4 | 4.4 |
| Cap tilt SP | +0.6 / +0.1 | +1.1 / +0.5 | 4.1 |
| Cap tilt SUE | +0.4 / +0.6 | +0.9 / +1.4 | 4.0 |
| Cap tilt M3 + SP | +1.1 / +0.4 | +1.6 / +0.6 | 4.8 |
| *M3* | *−4.1 / −1.0* | *−5.3 / −0.8* | 5.0 |
| *CW* | *+2.6 / +1.0* | *+3.0 / +1.2* | 4.5 |
| *EI10* | *+1.6 / +0.3* | *+1.7 / +1.0* | 5.5 |
| *H80M3 (H82 proxy)* | *−1.8 / −1.3* | *−1.6 / −1.4* | 3.2 |

**The eligible design in detail:**
- **Start months.** The four start months ranged from −4.3 to +2.1 at A$25,000 and from −1.9 to −1.3 at A$100,000.
- **Random books.** It beat 54% / 76% of the 200 matched random books. Those books have the same structure and the same eligible names, with the surprise replaced by a random number. Their 90th percentile was 5.0% / 6.5% a year against the design's 5.5% / 5.4%.
- **Statistics.** Monthly excess t = −0.4 at A$100,000. Deflated Sharpe 0.00 at N = 1,709.
- **Drawdown.** Worst fall −12.4% at A$100,000, against −11.6% for the fund.
- **Year by year at A$100,000, before tax** (points): +6.0, −2.0, −5.6, +8.2, −1.1, −10.5 (2026 to October).
- **Profit concentration.** The top five positions were 276% of the small total profit (Stanmore, Pilbara, Whitehaven, Lynas, Brambles), so item 5 fails.

**Against the comparators over the same holdout:**

| Comparator | Lead of the surprise design (A$25,000 / A$100,000) |
|---|---|
| ASX 200 fund (A200-style) | −1.4 / −1.5 |
| CW, the computed cap-weighted book | −3.9 / −2.5 |
| M3 | +2.7 / −0.5 |
| H82 proxy | +0.4 / −0.2 |

On the cap-weighted core, the surprise tilts also trailed the plain cap book (CW +2.6 / +1.0 against the best tilt's +1.1 / +0.4).

## 6. Replication on 12 markets (Dec 2018 – Oct 2026; Sweden from Dec 2019; `out/rep.log`)

These prices are development data from earlier rounds. Only the surprise signal is new to them.

| Market | After tax, A$25k / A$100k | Before tax | Beat random books | TE (A$100k) | M3 | CW |
|---|---|---|---|---|---|---|
| Germany | −1.7 / −1.9 | −1.6 / −1.8 | 24% / 0% | 4.7 | +2.3 / +1.0 | −1.2 / −1.3 |
| Sweden | −1.5 / −0.3 | −1.2 / −0.0 | 70% / 98% | 4.8 | −2.5 / −1.7 | +2.0 / +0.6 |
| Canada | **+3.2 / +1.8** | +3.4 / +2.6 | **91% / 97%** | 5.3 | +0.2 / +0.1 | −1.2 / −1.2 |
| US large | −0.1 / −0.9 | +0.7 / −0.7 | 62% / 7% | 6.0 | −0.2 / −0.7 | +4.6 / +3.1 |
| US mid | +0.6 / +0.6 | +0.7 / +1.0 | 56% / 31% | 4.8 | +4.4 / +1.1 | −2.4 / −1.7 |
| US small | **+1.6 / +1.5** | +3.3 / +2.0 | 98% / 85% | 6.4 | +5.2 / +1.2 | −3.5 / −2.3 |
| Korea | +0.4 / −0.1 | +1.3 / +0.6 | 23% / 7% | 9.0 | +3.1 / +2.3 | +3.6 / +1.8 |
| Taiwan | −2.2 / −0.1 | −0.2 / +1.2 | 17% / 100% | 9.6 | +0.9 / −0.6 | −3.3 / −3.3 |
| Thailand | **+3.6 / +1.5** | +4.8 / +1.9 | 55% / 61% | 7.5 | +2.6 / +2.4 | +1.3 / +0.4 |
| China | **+2.0 / +3.5** | +3.5 / +4.0 | 62% / 75% | 14.1 | +3.0 / +3.3 | −0.2 / −0.5 |
| Brazil | +0.2 / +0.7 | −1.2 / +1.2 | 71% / 18% | 5.8 | +0.3 / +2.0 | +5.3 / +5.2 |
| Norway | +0.5 / +1.4 | +0.9 / +2.6 | 27% / 20% | 6.1 | +4.9 / +3.8 | −0.6 / −0.7 |
| **Mean** | **+0.6 / +0.6** | | | | **+2.0 / +1.2** | +0.4 / +0.0 |

**Against the bar:**
- At least +1 at both sizes in 4 of 12 (7 needed).
- Below −2 in 1 of 12 (allowed).
- At or above the 90th random percentile at both sizes in 1 of 12 (7 needed).

**Pooled across all 12 markets** (A$100,000, before tax): +1.9 points a year, t = 1.4, deflated Sharpe 0.03.

**Surprise tilt minus plain M3:** −1.5 / −0.5 on average. It was ahead of M3 at both sizes in 2 of 12 markets (Sweden and Canada). Most of the design's lead where it was ahead (China, Thailand, US small) is M3's momentum, not the surprise.

## 7. Bar, item by item

| # | Item | Result | Pass? |
|---|---|---|---|
| 1 | Validity gate (ρ > 0, t ≥ 2) | ρ +0.08, t 2.9 | Yes (weak) |
| 2 | ASX holdout ≥ +1 at both sizes | −1.4 / −1.5 | **No** |
| 3 | ≥ 90th percentile of 200 random books at both sizes | 54% / 76% | **No** |
| 4 | Replication: ≥ +1 at both sizes in ≥ 7 of 12, and ≤ 1 below −2 | 4 of 12; 1 below −2 | **No** |
| 5 | Top five < 50% of profit (A$100k) | 276% | **No** |
| 6 | Deflated Sharpe (reported) | 0.00 (ASX holdout); 0.03 (pooled replication) | — |

**Verdict: fail. No shadow line. No AMENDMENT drafted.**

## 8. Caveats and what this does and does not show

- **This is a test of EODHD's surprise fields, not of post-earnings drift in general.**
  - On ASX the actual and estimate often seem to be on different bases. Cleaner consensus data (I/B/E/S, FactSet) could behave differently, but that remains institutional and unaffordable (report 57).
  - The 2023–24 coverage gap weakens the holdout.
- **Monthly entry.** Entry is at the first month-end after the report, about two weeks later on average, which misses the announcement-window move and the first days of drift. Daily entry would cost far more at retail size. Report 72's "results-day reaction" test failed for the same cost reason.
- **Survivor lean.** It works in the design's favour. Removing it would not turn this failure into a pass.
- **The one positive finding is about the data, not about money.** EODHD's estimates do carry information on results day (sections 3 and 1). That keeps open the forward-only use already planned in report 72 (record the surprise at each snapshot). It does not justify a trading rule.
- **Counting.** 60 trials were added: 12 development, 12 holdout and 36 replication. N is now **1,709**. The forward record's adopt threshold (report 78) was set at 1,649; at 1,709 the deflated-Sharpe hurdle is very slightly higher (t ≈ 5.05 instead of 5.04).

## 9. Files

- Pre-registration and hashes: `improve8/PREREG_79.md`, `improve8/out/prereg79_sha256.txt`
- Audit: `improve8/out/audit.log`, `improve8/out/coverage.csv`; parsed rows `improve8/data/earn_all.pkl` (27 MB)
- Gate: `improve8/out/gate.json`. Development, holdout and replication: `improve8/out/dev.json|log`, `hold.json|log`, `rep.json|log`, `chosen.json`, `summary.log`
- Code: `improve8/code/` (`parse_earn.py`, `audit.py`, `esig.py`, `coverage.py`, `r8.py`, `gate.py`, `run_dev.py`, `run_hold.py`, `run_rep.py`, `summ8.py`)
- Ledger: `improve8/out/trials_79.csv` (N 1,650–1,709)
