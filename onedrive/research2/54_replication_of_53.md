# 54 — Independent replication of report 53 (Big Wins engine)

Date: 2026-11-14. Status: validator's report. Research use only; general information, not financial advice.
Validator's code and outputs: `scratchpad/replication_53/` (`code/`, `out/`, `out_frozen/`). Builder's material: `scratchpad/bigwins/`.

## 0. Answer first

**Report 53's numbers are reproduced, and its conclusion stands: on the unseen period (2016 to May 2024) the engine did not beat the index.**

| Question | Answer |
|---|---|
| Does a blind re-implementation from `FINAL_RULES.md` give the same picture? | Yes. Same signs everywhere, same drawdowns (within 2 points), same hit rates, same random-portfolio picture. Of the 12 CAGR figures before and after costs, 7 are within 0.5 points; 5 differ by 0.5 to 1.0 points, all on the A$25,000 account or the unseen period |
| Why do those 4 differ? | Two things the rule text does not settle. (1) Whether the volatility signal uses 251 or 252 daily returns (rule B2). (2) Whether public-holiday rows in the price file count as trading days (rule A1). Nothing else |
| With the builder's reading of those two points, does my engine match his? | Exactly. Every figure in Tables 4.1, 4.2 and 4.4 to the printed digit, tax paid to the dollar, and all 520 + 608 closed positions with identical entry date, exit date and return |
| Is the builder's code a faithful implementation of the rules? | Yes, with one data defect (it trades on 1 January 2001 and 1 January 2009, which are holiday copies in the file) and two harmless departures (section 5) |
| Unseen period, A$25,000 | Behind the index under all four readings: engine 1.6% to 2.6% a year after costs, index 4.6% |
| Unseen period, A$100,000 | Level with the index under all four readings: engine 4.0% to 4.8%, index 4.6%; t between −0.1 and +0.2 |
| What is new | The A$25,000 unseen result moves by a full point (1.6% → 2.6%) when one day is dropped from a 252-day volatility window. Differences of a point between variants of this engine are noise. Report 53 says this about small accounts; this is a sharper example |
| Spec defects | 2 that change results, 15 that forced a guess but did not (section 6). One index-data defect that slightly flatters the engine before 2016 (section 5.3) |

## 1. What was done, in order

1. **Blind build.** Read only `bigwins/out/FINAL_RULES.md` (SHA-256 `e0aa433a…`, matches the builder's hash file) and report 51's cleaned panel (`company_study/data/P.pkl`, `V.pkl`, `index.pkl`, `delist.pkl`, the ASX company list, `sa_map.csv`). Read `company_study` data-preparation code for file formats only. Wrote `code/prep.py` (signals) and `code/engine.py` (account).
2. **Runs.** A$25,000 and A$100,000; development 29 Dec 2000 – 31 Dec 2015, unseen 31 Dec 2015 – 31 May 2024, whole period as one account. Costs: brokerage max(A$6.60, 0.088%), half-spread as rule E2.
3. **Random control.** 200 random portfolios per size and period through the same engine (same count, review dates, floors, industry cap, costs); only the score order is random. Seed 53.
4. **Freeze.** Results, code and a list of every guess copied to `out_frozen/` with SHA-256 sums at 08:08 UTC, before opening report 53, `bigwins/code` or any builder result. Sums re-checked after step 3: unchanged.
5. **Comparison.** Opened report 53 and `bigwins/out`. Then read `bigwins/code` to explain the differences. Added two labelled post-hoc variants.

Two blind variants were frozen, because the price file's calendar is itself doubtful (section 5.1): **Blind main** (holiday copies and weekend rows removed, as rule A1 "every ASX trading day" reads) and **Blind raw-calendar** (file as supplied).

## 2. Headline comparison

CAGR in percent a year, prices only. "Blind" = frozen before step 3. "Aligned" = my engine with the builder's reading of the two open points (run after step 3).

**Table 2.1. Report 53 Table 4.1**

| Period | Account | Measure | Report 53 | Blind main | Blind raw-calendar | Aligned | Verdict (blind main) |
|---|---|---|---|---|---|---|---|
| Development | A$25,000 | Before costs | 9.5 | 9.9 | 9.4 | 9.5 | REPLICATED |
| | | After costs | 9.0 | 9.6 | 9.2 | 9.0 | CLOSE (explained): +0.6 |
| | | After tax A / B | 7.5 / 6.4 | 8.0 / 7.0 | 7.6 / 6.7 | 7.5 / 6.4 | REPLICATED / CLOSE: +0.5 |
| Development | A$100,000 | Before costs | 6.7 | 7.0 | 6.9 | 6.7 | REPLICATED |
| | | After costs | 6.4 | 6.5 | 6.3 | 6.4 | REPLICATED |
| | | After tax A / B | 5.4 / 5.0 | 5.5 / 5.0 | 5.6 / 5.1 | 5.4 / 5.0 | REPLICATED |
| **Unseen** | A$25,000 | Before costs | 2.9 | 3.3 | 3.3 | 2.9 | REPLICATED |
| | | After costs | 1.6 | 2.6 | 2.6 | 1.6 | CLOSE (explained): +1.0 |
| | | After tax A / B | 1.1 / 0.7 | 1.5 / 0.7 | 1.5 / 0.7 | 1.1 / 0.7 | REPLICATED |
| **Unseen** | A$100,000 | Before costs | 4.9 | 5.5 | 5.5 | 4.9 | CLOSE (explained): +0.6 |
| | | After costs | 4.3 | 4.6 | 4.8 | 4.3 | REPLICATED |
| | | After tax A / B | 3.4 / 2.5 | 3.7 / 2.8 | 3.8 / 2.7 | 3.4 / 2.5 | REPLICATED |
| Whole | A$25,000 | Before costs | 7.9 | 8.4 | 8.0 | 7.9 | CLOSE (explained): +0.5 |
| | | After costs | 7.2 | 7.8 | 7.4 | 7.2 | CLOSE (explained): +0.6 |
| | | After tax A / B | 5.9 / 4.6 | 6.5 / 5.0 | 5.8 / 4.9 | 5.9 / 4.6 | CLOSE: +0.6 / REPLICATED |
| Whole | A$100,000 | Before costs | 6.5 | 6.7 | 6.6 | 6.5 | REPLICATED |
| | | After costs | 6.0 | 6.0 | 6.0 | 6.0 | REPLICATED |
| | | After tax A / B | 5.0 / 4.4 | 4.9 / 4.3 | 5.0 / 4.5 | 5.0 / 4.4 | REPLICATED |
| All | Index (XJO) | After costs: dev / unseen / whole | 3.2 / 4.6 / 3.7 | 3.2 / 4.6 / 3.7 | same | same | REPLICATED (identical) |
| All | Index | After tax A; B | 2.8, 3.9, 3.3; 2.3, 3.3, 2.8 | identical | same | same | REPLICATED |

**Table 2.2. Engine minus index, after costs (points a year)**

| Period | Account | Report 53 | Blind main | Blind raw-calendar | Aligned |
|---|---|---|---|---|---|
| Development | A$25,000 | +5.7 | +6.3 | +5.9 | +5.7 |
| Development | A$100,000 | +3.1 | +3.3 | +3.1 | +3.1 |
| **Unseen** | A$25,000 | **−3.0** | **−2.0** | **−2.0** | **−3.0** |
| **Unseen** | A$100,000 | **−0.3** | **0.0** | **+0.2** | **−0.3** |
| Whole | A$25,000 | +3.5 | +4.1 | +3.7 | +3.5 |
| Whole | A$100,000 | +2.3 | +2.3 | +2.3 | +2.3 |

**Table 2.3. Report 53 Table 4.2: drawdown and t**

| Period | Account | Max drawdown: report 53 | Blind main | Aligned | t of monthly excess: report 53 | Blind main | Aligned | Verdict |
|---|---|---|---|---|---|---|---|---|
| Development | A$25,000 | −55% | −55.0% | −55.0% | 2.3 | 2.5 | 2.3 | REPLICATED |
| Development | A$100,000 | −53% | −52.5% | −53.1% | 1.5 | 1.6 | 1.5 | REPLICATED |
| Unseen | A$25,000 | −30% | −28.1% | −30.1% | −0.5 | −0.3 | −0.5 | REPLICATED |
| Unseen | A$100,000 | −26% | −26.2% | −26.3% | −0.0 | +0.1 | −0.0 | REPLICATED |
| Whole | A$25,000 | −55% | −55.0% | −55.0% | 1.9 | 2.2 | 1.9 | REPLICATED |
| Whole | A$100,000 | −53% | −52.5% | −53.1% | 1.4 | 1.5 | 1.4 | REPLICATED |

Index drawdown −50% / −28%: identical. Tax paid, aligned run: A$10,292 / 18,219, 23,450 / 50,846, 1,093 / 2,136, 8,151 / 15,226, 15,205 / 23,798, 45,756 / 91,990. These are report 53's figures to the dollar.

**Table 2.4. Report 53 Table 4.7: hit rates, one continuous account 2001–May 2024**

| Account | Measure | Report 53 | Blind main | Aligned | Verdict |
|---|---|---|---|---|---|
| A$100,000 | Positions | 608 | 608 | 608 | REPLICATED |
| | Beat XJO over the same days | 49% | 49% | 49% | REPLICATED |
| | More than doubled | 3% | 3% | 3% | REPLICATED |
| | Lost more than 50% | 4% | 3% (3.5%) | 4% (3.6%) | REPLICATED |
| A$25,000 | Positions | 520 | 537 | 520 | REPLICATED (path differences) |
| | Beat XJO | 49% | 51% | 49% | REPLICATED |
| | More than doubled | 2% | 2% | 2% | REPLICATED |
| | Lost more than 50% | 5% | 5% | 5% | REPLICATED |

My position definition (one unbroken holding of a company, net proceeds ÷ total cost, index over the same entry and exit days) was written before step 3 and turned out to be the builder's. In the aligned run every one of the 1,128 closed positions matches the builder's file on company, entry date, exit date and return, with a largest return difference of zero.

**Table 2.5. Report 53 Table 4.3: random portfolios (CAGR after costs; 200 draws each, different seeds)**

| Period | Account | Random median: report 53 | Blind main | Aligned | Engine's percentile: report 53 | Blind main | Aligned | Verdict |
|---|---|---|---|---|---|---|---|---|
| Development | A$25,000 | 1.0 | 0.1 | 0.3 | 99.5 | 100 | 100 | REPLICATED |
| Development | A$100,000 | 1.0 | 1.0 | 1.0 | 100 | 99.5 | 100 | REPLICATED |
| Unseen | A$25,000 | 2.8 | 3.7 | 3.4 | 37 | 43 | 29 | REPLICATED (sampling) |
| Unseen | A$100,000 | 3.1 | 3.5 | 3.4 | 69 | 75 | 65 | REPLICATED (sampling) |
| Whole | A$25,000 | 1.6 | 1.2 | 1.3 | 99.5 | 100 | 99.5 | REPLICATED |
| Whole | A$100,000 | 1.8 | 1.6 | 1.8 | 100 | 100 | 100 | REPLICATED |

With 200 draws a percentile near 40 has a sampling error of about 3.5 points on each side, so 29, 37 and 43 are the same answer: the engine sat inside the random band on unseen years and above it on 2001–2015. "A random 10-stock list did better than the engine 63% of the time": 57% blind, 71% aligned. Before costs the percentiles are the same to within 3 points (`out/random_summary.csv`).

**Table 2.6. Report 53 Table 4.4: eras (aligned run)**: 20.8 / −7.9 / 13.4 / 0.4 / 7.6 at A$25,000 and 15.3 / −7.5 / 11.5 / 2.8 / 7.5 at A$100,000, index 9.9 / −6.0 / 4.4 / 6.0 / 3.3. Identical to the report. Blind main: 22.0 / −7.5 / 13.3 / 0.8 / 8.6 and 15.2 / −7.1 / 11.6 / 2.7 / 7.2. REPLICATED, including "lost 2016–2019, won 2020–2024".

Not re-run: A$5,000 and A$10,000 rows, variant 1c and the sell-rule loop, dividend estimates (4.5), sensitivities (4.6), the contribution plan (4.8), deflated Sharpe, case studies. They were outside the brief.

## 3. Does the conclusion stand?

Yes.

- **A$25,000, unseen:** behind the index by 2.0 to 3.0 points a year after costs under every reading, and inside the lower half of the random band.
- **A$100,000, unseen:** between 0.6 behind and 0.2 ahead after costs; t between −0.1 and +0.2. That is "level", which is what report 53 says ("level with or behind the index before dividends"). Before costs the engine is 0.3 to 0.9 ahead; costs take it away. After tax it is behind under every reading (regime B: 2.3–2.8 against 3.3).
- **Whole period:** ahead by 2.3 points (A$100,000, t 1.4–1.5) and 3.5–4.1 points (A$25,000, t 1.9–2.2), all of it earned before 2016. No reading reaches t = 3.
- One wording check. Report 53 section 0 says the engine "did not beat the index" on unseen years. For A$100,000 the precise statement is "did not differ from the index before dividends". One blind reading shows +0.2 points. This does not change any decision.

## 4. Where the differences come from

| Step | Dev 25k | Dev 100k | Unseen 25k | Unseen 100k | Whole 25k | Whole 100k |
|---|---|---|---|---|---|---|
| Report 53, CAGR after costs | 8.95 | 6.38 | 1.63 | 4.25 | 7.18 | 5.96 |
| Aligned (builder's calendar, 252 returns) | 8.95 | 6.38 | 1.63 | 4.25 | 7.18 | 5.96 |
| Change the volatility window to 251 returns (blind raw-calendar) | 9.18 | 6.33 | 2.59 | 4.81 | 7.43 | 5.96 |
| Remove non-trading days, keep 252 returns (post-hoc) | 9.43 | 6.28 | 1.63 | 3.99 | 7.56 | 5.88 |
| Both (blind main) | 9.58 | 6.53 | 2.59 | 4.58 | 7.84 | 5.99 |

**4.1 Volatility window (rule B2, s4).** The rule says "daily log returns in W", W being 252 trading days. I took returns whose two days both lie in W (251 at most). The builder, through report 51's cohort file, takes the 252 returns dated in W, so the first one starts on the day before W. The other three signals, the universe, the traded-value ranks and the prices agree exactly at all 282 month-ends. The largest score difference from this one day is 0.057; it reorders near-ties at every month-end. The top-n list changes by a name or two a year, and at 10 names that is enough to move the unseen result by 1.0 point. Neither reading is wrong on the text. **Spec defect.**

**4.2 Calendar (rule A1).** The price file has rows on seven public holidays that are copies of the previous day (25 and 26 Dec 2000, 1 Jan 2001, 29 Mar 2002, 14 Jun 2004, 27 Dec 2005, 1 Jan 2009; also 27 and 28 Dec 1999) and stray weekend rows (17 Mar 2018 inside the test period). The builder's engine treats them as trading days, so its first purchases are dated Monday 1 January 2001 at the 29 December 2000 closing prices, and its January 2009 review trades on New Year's Day at 31 December 2008 prices. The rule says E is "the next trading day"; ASX was shut. On the rule text the blind main reading is right and the builder's dates are wrong for those two reviews. Effect: +0.5 points on the A$25,000 development result, +0.4 on the whole period, about −0.1 at A$100,000, and on the unseen period −0.3 to 0 (one Saturday row shifts every later window by a day). **Data defect in report 51's panel, inherited.**

## 5. Other findings from reading the builder's code

**5.1 Code against rule text.** Three departures; only the first changes any number.
1. Trades on holiday copies (4.2).
2. Rule A5 says the industry group is looked up by the company's *current* code. The code uses the code in the price file, which stops in May 2024. Nine universe companies renamed since then (for example IPL, GUD, SVW, MFG in the mapping file) have a group under the rule and none in the builder's run. Effect on these runs: none (tested).
3. Rule C9 counts "the current holdings not awaiting sale" against the industry cap. The code counts only those still in the current top 300; a holding that has dropped out of the 300 has no group there. Effect on these runs: none (my engine counts all and still matches exactly).

Everything else I checked in the code is the rule as written: universe, score and tie-break, eligibility, n and T, December review, trims and top-ups, the 367-day deferral, vacancies, payouts, buy sizing and the waiting rule, costs, tax, the index comparator.

**5.2 Rule H cannot be carried out as written.** It asks the validator to compare holdings lists, trade dates and month-end NAV series "against the builder's files". `bigwins/out` has no holdings lists, no trade list and no NAV series, only closed positions for the whole-period account and a results file. I compared closed positions (entry and exit dates, returns) and every summary figure instead.

**5.3 The index series is stale for most of 2001.** In `company_study/data/index.pkl` XJO is forward-filled over gaps: it shows 3,274.6 on every day from 30 Nov 2000 to early Feb 2001, and is flat again for 37 days from 8 Feb 2001 and 101 days from 9 Apr 2001. Both the builder and I buy the index at 3,274.6. The published year-end 2000 close was about 3,206 [from memory; not verified in this session]. If so, the index is bought about 2% too dear: its CAGR is understated by roughly 0.14 points on 2001–2015 and 0.09 on the whole period, so the engine's lead there is overstated by the same amount. Monthly excess returns for 2001 are also distorted, which touches the development and whole-period t values slightly. The unseen period is not affected. This does not change a conclusion; it should be fixed in the panel.

**5.4 Path noise.** One day more or less in a volatility window: up to 1.0 point. Holiday rows: up to 0.5. Report 53 section 0.1 gives 0.15 points for a 1% change in starting balance and 0.8 for settlement timing. Taken together, no difference under about one point a year between two versions of this engine at A$25,000 means anything.

## 6. Ambiguities in `FINAL_RULES.md` that forced a guess (spec defects)

Each guess was written down in `out_frozen/CHOICES_before_step3.md` before step 3.

**Changed results**

| # | Rule | Ambiguity | My guess | Builder | Effect |
|---|---|---|---|---|---|
| 1 | B2 (s4) | "Returns in W": 251 returns inside W, or 252 returns dated in W | 251 | 252 | Up to 1.0 point |
| 2 | A1 | "ASX trading day" is not defined against the file, which has holiday copies and weekend rows | Removed them | Kept them | Up to 0.5 point |

**Forced a guess, no effect found**

| # | Rule | Ambiguity | My guess |
|---|---|---|---|
| 3 | A2 | 3,019 file rows have a close and zero volume. "A day with no trade has no close" | Kept the close (as the builder) |
| 4 | A5 | "Current code" when the code changed after the price file ends; and a dead company whose code has been reused by another company gets that company's group | Mapped code where known; literal lookup otherwise |
| 5 | B1 | Tie-break for equal median traded value | File column order |
| 6 | B6 | Price floor on the adjusted close, not the price quoted that day (differs after a later consolidation) | As written (adjusted) |
| 7 | C1 | "The ASX delisting reason for that code": codes are reused and can have several records; no matching rule is given. The list also ends in April 2020, so every later failure is paid at full last price | First record from 30 days before to 1,500 days after the last trade; none = paid in full |
| 8 | C1 | "Last trade ever" needs knowledge of the future and depends on where the file ends (survivors run to Nov 2026, others stop in May 2024) | Whole file |
| 9 | C1, F | Whether a payout is a disposal for tax | Yes |
| 10 | C2 | At a June month-end, is NAV struck before or after tax is paid (changes T in tax runs) | After (builder: recorded before, T after) |
| 11 | C5, C7, C9 | A holding with a sale already pending at a review; whether a pending trim counts as "awaiting sale" | Pending full sale kept; trim does not count |
| 12 | D2 | Order of the cash test and the "no trade → dropped" test; whether a waiting buy blocks later buys; brokerage in the cost on shares × close or on amount a | Cash test first; no blocking; shares × close |
| 13 | D3 | Top-up whose stock does not trade on its one attempt day; whether top-ups lapse at month-end | Dropped; lapse |
| 14 | E2 | "Latest month-end" for a trade that falls on a month-end; rank for the final liquidation; a company with no rank; tick size on adjusted price | Previous month-end; end date's rank; 0.50%; adjusted |
| 15 | G | "Whole period" is not in section H: one continuous account or two joined | One account |
| 16 | G | None of the reported measures is defined: CAGR on liquidated value or last NAV; "before costs" as a separate zero-cost run; max drawdown on month-end NAV; t-statistic; what a "position" is; doubling as ≥ or > 100%; the random-portfolio design | See `CHOICES_before_step3.md`; all matched the builder |
| 17 | H | Names files that do not exist (5.2) | Compared closed positions |

Recommended wording fixes: B2 "the 252 daily log returns dated in W (the first uses the close of the day before W)"; A1 "days on the official ASX trading calendar; rows on other days are deleted before anything is computed"; C1 "the delisting record for that code dated nearest after the last trade, within N days"; and a section defining the reported measures.

## 7. Verdict by headline

| Headline in report 53 | Verdict |
|---|---|
| Table 4.1, development rows | REPLICATED at A$100,000; CLOSE (explained) at A$25,000 (+0.6 after costs: calendar +0.5, volatility window +0.2). On the rule text the blind figure (9.6) is the better one, because 1 Jan 2001 and 1 Jan 2009 were not trading days |
| Table 4.1, unseen rows | A$100,000 REPLICATED (4.3 vs 4.6); A$25,000 CLOSE (explained) (1.6 vs 2.6: volatility window only; rule text does not decide) |
| Table 4.1, whole-period rows | A$100,000 REPLICATED (6.0 vs 6.0); A$25,000 CLOSE (explained) (7.2 vs 7.8) |
| Index rows | REPLICATED (identical), subject to the stale-index defect in 5.3 |
| Table 4.2 drawdowns and t | REPLICATED (all drawdowns within 2 points, all t within 0.3) |
| Table 4.3 random portfolios | REPLICATED within sampling error |
| Table 4.4 eras | REPLICATED |
| Table 4.7 hit rates | REPLICATED |
| "On the unseen period the engine did not beat the index" | STANDS |
| "The whole advantage was earned before 2016" | STANDS |
| "It beat all, or all but one, of 200 random portfolios over 23 years" | STANDS (100th and 99.5th–100th percentile) |
| Nothing | NOT REPLICATED |

## 8. Files

- `replication_53/code/prep.py`, `engine.py`, `run_main.py`, `run_random.py`, `diag1.py` (run with `python3 -I`).
- `replication_53/out_frozen/`: blind results (`results.csv`, `hitrates.csv`, `random_summary.csv`, positions, trades, holdings and NAV files; `rawcal/` for the raw-calendar variant), `CHOICES_before_step3.md`, `SHA256SUMS`, `FROZEN_AT.txt`.
- `replication_53/out/252/`, `out/rawcal252/`, `out/rawcal252prefix/`: post-step-3 variants. `rawcal252` is the aligned run.
