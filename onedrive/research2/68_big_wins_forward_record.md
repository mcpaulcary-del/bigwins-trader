# 68. Big Wins: the forward paper record — design, first frozen entries, and what new data would help

16 November 2026. Author: research agent (Fable). Work folder: `scratchpad/bigwins_forward/` (`code/`, `out/`). Every script was run with `python3 -I`. Paper and research only. General information, not financial advice. Nothing here can place an order.

## 0. Answer first

1. **No more tuning on history.** Report 64 showed that a one-point edge needs about 180 years to show. The only honest sources of new information are time and a different kind of data. This report sets up both.
2. **Rules v1.3 are written** (`67_FINAL_RULES_v1.3.md`, SHA-256 `b38abcd7…54b0`): one self-contained document, every ambiguity of reports 54, 63 and 65 settled, no engine rule changed. It reproduces report 64's EODHD result exactly with the frozen engine and to 0.0003 point with independent code (target 0.05).
3. **One real defect was found on the way.** EODHD carries renamed companies under both codes, and report 64's duplicate test missed 145 of them, including Woodside (WPL/WDS), TPG (TPM/TPG) and Seven Group (SVW/SGH). The engine held Seven Group twice in 2023–2024. Corrected, the 2018–2026 result is 8.3% a year at A$25,000 (was 9.6%) and 10.0% at A$100,000 (was 9.7%), against 8.8% for the index fund. The verdict does not change: level with the index, no measurable edge. The forward record uses the corrected test.
4. **The forward record has started.** Two score snapshots are frozen and hash-chained: the month-end of 30 October 2026 (31 October was a Saturday) and an interim one for 13 November 2026. No trades yet. First formation: the month-end of Thursday 31 December 2026, traded Monday 4 January 2027.
5. **It costs about A$370 a year in data** (EODHD at US$19.99 a month). The free plan cannot do it: one month-end needs about 5,500 calls and the free plan allows about 600 a month. A cut-down design at about A$62–93 a year is possible and is described in section 3.
6. **Honest forecast, unchanged from report 53:** the record will most likely show the engine near the index and will not pass the promotion test. Its value is in showing what the engine really does and costs, with no hindsight.

## 1. Rules v1.3 and the reproduction check

Full text and tables are in report 67. Summary of the check on unseen B (EODHD total return, 29 Dec 2017–13 Nov 2026):

| % a year | Report 64 | v1.3 prep + frozen engine | Independent code following v1.3 | Report 65 (v1.2 text) |
|---|---|---|---|---|
| A$25k after costs / tax A / tax B | 9.612 / 7.237 / 6.577 | identical | identical | identical |
| A$100k before costs | 10.449 | identical | 10.449 (−0.0003 pt) | +0.039 pt |
| A$100k after costs / tax A / tax B | 9.746 / 7.542 / 6.685 | identical | −0.0001 / 0.0000 / 0.0000 pt | +0.024 / +0.008 / +0.006 pt |
| Comparator after costs / tax A / tax B | 8.777 / 6.835 / 6.208 | identical | identical | −0.043 / −0.029 / −0.029 pt |
| H100, each June 2016–2026 | — | identical (to 4e-9 pt) | not re-run | within 0.13 pt |

What closed report 65's gap:
- **Calendar.** Report 65 took trading days from the old panel's calendar file, which lacks 31 Oct–4 Nov 2016 and 29 May 2020. v1.3 defines a trading day as a day with an `AXJO.INDX` row. That one change removed the unexplained FBU/NIC difference.
- **7 May 2018.** VAS supplies the comparator's return on that day; the A200 index takes over from 8 May.

What v1.3 adds beyond a merge: the split rule exactly as coded (v1.2 described it loosely); the ASX tick table; the takeover keyword list; the delisting-record window, with the WFL case (record 426 days after the last trade) as the worked example; the H100 year range; an H101 tracking-line definition; and part Q, the production procedure from EODHD daily data alone.

**The duplicate-code defect, in numbers** (a data correction; not counted as a trial):

| Unseen B, % a year | A$25k as report 64 | A$25k corrected | A$100k as report 64 | A$100k corrected | Comparator |
|---|---|---|---|---|---|
| After costs | 9.61 | 8.27 | 9.75 | 9.96 | 8.78 |
| After tax, 50% discount | 7.24 | 6.95 | 7.54 | 7.47 | 6.84 |
| After tax, no discount | 6.58 | 6.32 | 6.69 | 6.47 | 6.21 |

H100 with the correction: no June changes sign, the largest change is −1.5 points (2022), and the 2018–2026 mean stays +4.0%.

## 2. Forward paper record: design

### 2.1 Principles

- Every decision uses only data dated on or before its decision day, downloaded that evening. The inputs and outputs are hashed and the hash is chained to the previous entry, so a later change is detectable.
- Rules v1.3 are frozen. No parameter changes during the record. A change is a new card with its own clock (BW-26).
- Between formal looks the scorecard is information only. Nothing is switched on, off or resized because of it.
- No table ranks variants by return (LE-28). No result is described as skill.

### 2.2 Calendar

| Date | Event |
|---|---|
| Fri 30 Oct 2026 | Snapshot 1 frozen (month-end; no book yet) |
| Fri 13 Nov 2026 | Snapshot 2 frozen (interim; proves the daily path) |
| Mon 30 Nov 2026 | Month-end snapshot (still no book) |
| **Thu 31 Dec 2026** | **First formation.** H82 lists for A$25,000 (10 names) and A$100,000 (30 names); H101 cohort 1; first prediction written |
| Mon 4 Jan 2027 | Paper buys at the close (1 Jan is a holiday) |
| Each month-end | Snapshot; vacancies refilled (C9); scorecard on the first trading day after |
| Thu 24 Jun 2027 | H100 measurement day S: loser list frozen and hashed after the close |
| Fri 25 Jun 2027 | H100 buy day B (4th-last trading day of June) |
| Fri 30 Jul 2027 | H100 exit day X |
| Month-ends of Mar, Jun, Sep | H101 shadow cohorts |
| Fri 31 Dec 2027 | First review; first prediction resolved |
| 31 Dec 2029 / 2031 / 2036 | Formal looks at 36, 60 and 120 months |

Dates are from the XASX calendar of `exchange_calendars` 4.13.3 and must be confirmed against the ASX's published calendar each December.

### 2.3 Monthly snapshot (rules v1.3, Q2)

After the close of each month-end:
1. Download from EODHD: the AU symbol list (active and delisted) and, for every common-stock code, `eod`, `splits` and `div`; plus `AXJO.INDX`.
2. Run `bw13_snapshot.py <date>`. It writes to `out/forward_record/`:
   - `scores_top300_<date>.csv`: the 300 universe companies with traded-value rank, median daily value, close, the four signals, their percentiles, the H80 score and score rank, industry group, and whether the name would be in a 10-name or 30-name review list that day.
   - `scores_h101_<date>.csv`: the H101 universe (ranks 301–1000, A$50,000 a day, 50 cents) with scores and the top tenth.
   - `dupcodes_<date>.csv`: the renamed-code pairs removed.
   - `manifest_<date>.json`: SHA-256 of every input and output, counts, index levels.
3. One line is appended to `LEDGER.jsonl`, carrying the manifest hash and the hash of the previous line.
4. The owner saves the ASX listed-companies file in a browser that month (industry groups; the system may not fetch asx.com.au).

A no-look-ahead test is part of the code: the 30 Oct 2026 scores computed from the file cut at 30 Oct equal those computed from the file cut at 13 Nov (same 300 names, largest score difference 3e-11).

### 2.4 The books

| Book | Rule | Capital | Starts |
|---|---|---|---|
| H82 main | v1.3 parts B–F, I | A$100,000, no contributions | 31 Dec 2026 |
| H82 small | same | A$25,000 | 31 Dec 2026 |
| H83 controls | 200 random-score portfolios through the same machine (seeds 1–200 fixed now); 12-1 momentum with 10 names | as H82 | 31 Dec 2026 |
| H100 June sleeve | v1.3 part N; full list, and a 10-name draw by seed 2027 from the frozen list | A$2,500 a name | 24–25 Jun 2027 |
| H101 tracking line | v1.3 part P; one bet with H82 | A$2,500 a name | 31 Dec 2026 |
| Comparator | A200 total return (issuer index and distributions), bought once on 4 Jan 2027, v1.3 J3 | same dollars | 31 Dec 2026 |
| Second comparator | Owner's plan B2: A200 40% / BGBL 60% | same dollars | 31 Dec 2026 |

Fills: `paper_sim` books each trade at the close of its day with the modelled costs (v1.3 D, E). If the IBKR paper account is live, its fills form a second line and the difference is the cost-model error.

Stocks that stop trading are not paid out by formula. They are carried at the last close and flagged until the company's announcement settles the outcome (takeover cash, scrip, or zero); meanwhile a second NAV shows them at 70% (v1.3 Q6).

### 2.5 H100 guard rails (report 63 §8, kept)

Buy only on B, never earlier. Each position capped at the lower of A$2,500 and 5% of the 63-day median daily value. Record the realised or quoted spread on every name against the modelled 1.05–1.15% a side. Report the under-20-cent and 20-cent-and-over halves separately. Score against A200 and against the equal-weight small-cap universe. Print the median pick beside the mean.

### 2.6 Monthly scorecard (first trading day of each month)

For the month and since 31 Dec 2026, for each H82 book:
- Total return (dividends in) after modelled costs; after estimated tax at 32% with and without the 12-month discount.
- A200 on the same dollars and dates; the difference; the same against the owner's plan.
- Maximum drawdown of each; worst 12-month gap; months ahead and behind.
- Turnover, costs and tax in dollars; a line net of the data cost (A$370 a year is 0.37% of A$100,000 and 1.5% of A$25,000).
- Percentile among the 200 random portfolios; the momentum control.
- Tracking error to date and, from it, the years needed to show the measured gap at t = 2.
- Data notes: duplicate pairs removed, holdings flagged as stopped, any data block.
- First line of every scorecard: "PAPER — Big Wins. Not shown to beat the index."

### 2.7 Formal looks (report 53 §7 and §8.3; owner decision O42 still open)

| Look | Date | Promotion test: ahead of A200 after costs and tax by at least | Chance of passing with no edge | With a true +2.5 pts a year |
|---|---|---|---|---|
| 36 months | 31 Dec 2029 | 7.4 points a year | 6.7% | 16% |
| 60 months | 31 Dec 2031 | 5.7 points a year | 6.7% | 20% |
| 120 months | 31 Dec 2036 | 4.0 points a year | 6.7% | 28% |

The test as written in report 53: total return above A200's on the same dollars, and a one-sided stationary-bootstrap confidence of at least 0.933 that the mean monthly difference is above zero; at or above the 80th percentile of the random portfolios; the controls did not pass; largest fall not more than 10 points deeper than A200's; worst 12-month gap not below −35 points. A pass gives no return claim (that needs t ≥ 3.0 and DSR ≥ 0.95) and is more likely luck than skill.

### 2.8 Kill criteria

| Line | Close it when |
|---|---|
| H82 | At a formal look: more than 15 points in total behind A200 after costs and tax, or a drawdown more than 20 points deeper than A200's (H82 card) |
| H82 | A control passes where the engine does not: stop reading the result and audit data and code first (H83) |
| H82 | Two data blocks in 12 months, or a broken ledger chain not explained in 20 trading days |
| H100 | After 5 Junes, 4 or 5 behind A200 after costs; or cumulatively more than 15 points behind at any review; or the realised spread over two Junes averages above 1.7% a side |
| H101 | Behind A200 at the 36-month look |
| Whole record | The owner no longer reads the scorecard: stop the data plan and set the mode to off (O39) |

### 2.9 What the learning engine records (report 52)

- **Run record (LE-07):** for each snapshot and each book update: rules version and hash, code hashes, input hashes, parameters, seed, start and end time, status.
- **Hash chain (LE-08):** `LEDGER.jsonl`; the chain head is printed on each scorecard.
- **Predictions before the outcome (LE-19, BW-30):** at each December review, "the list beats A200 total return over the next 12 months", probability 0.50, 80% band ±11 points; and for H100 each June, "losers beat A200 from B to X", probability 0.55 [my estimate from 15 of 23 Junes, shaded for the three weak recent ones]. Resolved a year (or five weeks) later; Brier score and band coverage reported.
- **Scorecards (LE-18)** on post-freeze data only.
- **Cost-model error (LE-20):** modelled against quoted or paper-fill spread, per trade.
- **Data events:** duplicate pairs, code re-use, restated closes found by comparing this month's download with last month's, stopped holdings and their eventual outcome (takeover, failure, unknown).
- **Lessons (LE-38):** one row for this report: "duplicate test based on exact volume match missed 145 renames; forward test relaxed".
- **Never:** a change to any rule value, or any ranking of variants by recent return (LE-01, LE-28).

Trial count: nothing in this report is a new trial (replications and one data correction). The library count stays 402.

## 3. First entries of the record (information only, not advice)

Inputs: the EODHD download of 16 Nov 2026 (`panel_tr.pkl`, hash in each manifest), cut at each date; the ASX listed-companies file of 14 Nov 2026. 16 Nov rows were present for only 1,899 of about 2,356 symbols at download time, so 13 Nov is the latest complete day.

| Entry | As of | Kind | Manifest SHA-256 | Scores file SHA-256 |
|---|---|---|---|---|
| 1 | Fri 30 Oct 2026 | Month-end | `21cfec54…d26a` | `32efb8b1…2e5c` |
| 2 | Fri 13 Nov 2026 | Interim, not a decision day | `50f6d50f…9ff7` | `86850f88…f250` |

Ledger head after entry 2: `f769af8b…93bf`. Full hashes are in `out/forward_record/LEDGER.jsonl`.

Because both were computed on 16 Nov, they are "frozen late" by 17 and 3 days. From 30 Nov onward a snapshot is frozen the same evening.

**Top 10 by H80 score, month-end 30 Oct 2026** (all 300 scored; the review list would hold 10 of these at A$25,000 and 30 at A$100,000):

| Rank | Code | Company | Score | Close | Traded-value rank | Industry group |
|---|---|---|---|---|---|---|
| 1 | RHC | Ramsay Health Care | 0.899 | 55.60 | 68 | Health Care Equipment & Services |
| 2 | ANN | Ansell | 0.884 | 45.44 | 114 | Health Care Equipment & Services |
| 3 | CPU | Computershare | 0.879 | 43.24 | 34 | Commercial & Professional Services |
| 4 | WOW | Woolworths Group | 0.872 | 40.22 | 18 | Consumer Staples Distribution & Retail |
| 5 | QBE | QBE Insurance Group | 0.861 | 26.18 | 23 | Insurance |
| 6 | STO | Santos | 0.848 | 9.25 | 17 | Energy |
| 7 | FPH | Fisher & Paykel Healthcare | 0.843 | 38.13 | 107 | Health Care Equipment & Services |
| 8 | SOL | Washington H Soul Pattinson | 0.841 | 45.77 | 85 | Financial Services |
| 9 | APA | APA Group | 0.838 | 11.27 | 67 | Utilities |
| 10 | DNL | Dyno Nobel | 0.835 | 3.99 | 99 | Materials |

Interim, 13 Nov 2026: QBE, CPU, RHC, ANN, WOW, FPH, APA, CGF, ASX, SOL. Seven of ten names are the same two weeks apart.

These names are what the frozen rule ranks highest today. The evidence says a list like this has been level with the index, with a wide range either way. No book exists until 31 Dec 2026, and the December list will differ.

### Data cost

| Design | EODHD calls | Cost | What is lost |
|---|---|---|---|
| **A. Full record** (recommended if the record is wanted at all): subscribe every month; one full refresh each month-end | About 1,826 active common-stock codes × 3 end-points + 2 list calls + index ≈ **5,500 calls a month-end** (the full history download was 13,470). A daily bulk update would be 300 calls a trading day (prices, splits, dividends), about 6,300 a month | US$19.99 a month ≈ A$31; **about A$370 a year** | Nothing |
| B. Two paid months a year (December and June) | The same 5,500 calls, twice; the other ten month-end snapshots are computed in arrears from those downloads and marked "in arrears" | About A$62 a year (A$93 with a third month for the July exit) | Ten snapshots a year are not frozen on the day; vacancies are refilled late or not at all; restated closes go unseen for up to six months |
| Free plan | 20 calls a day ≈ 600 a month. Even 400 codes × 3 = 1,200 calls is twice that, and the universe ranking needs all 1,826 | A$0 | Not workable |

The paid plan allows 100,000 calls a day, so a month-end refresh fits in one evening. Design A is within report 53's O39 but above the spec's A$150 ceiling (OPS-20); it needs the owner's yes. Whether EODHD's free plan also limits history to one year is [unverified].

## 4. What new data would genuinely help, ranked

Each item is either forward-only or a one-shot run declared in advance. None spends more unseen history, and none adds a tuned variant.

| Rank | Data | Cost | What it would settle | Design that spends no history |
|---|---|---|---|---|
| 1 | **Time: the forward record itself** (EODHD prices monthly) | A$370 a year (or A$62–93, design B) | Whether the engine is built as written, what it costs, how it behaves; the only truly unseen sample | Section 2. Read at 36, 60, 120 months only |
| 2 | **Real quotes or paper fills for H100 names** (IBKR paper account, or closing bid and ask noted by hand for the June list) | A$0 | H100's edge is about the size of its modelled cost (1.2–1.3% a side). This is the one input that can close or keep the card quickly | Forward-only: record the quoted spread at the close of S, B and X in June 2027 and June 2028. Kill line already set at 1.7% a side |
| 3 | **Outcomes of stocks that stopped trading after April 2020** (takeover, failure, scrip), read by a person from company announcements | A$0; a few hours | The engine's 14 payouts and H100's stopped names are paid at assumed values (100% or 70%). The "unexplained = 70%" stress alone moves unseen B by 2–3 points | One-shot data correction for the 14 + about 30 names actually held; declared in advance as a replacement of an assumption, not a trial. Forward: recorded as it happens (v1.3 Q6) |
| 4 | **Norgate ASX package, one six-month rental** (survivorship-free from 1992, delisted dividends, historical index membership, name-change history) | A$346.50 ex GST (about A$381); Windows; raw data deleted at expiry, derived results kept | (a) Development 2001–2015 in total return on licensed data, which no source held can give. (b) An independent check of the 472 duplicate pairs and 112 re-used codes. (c) A second source for 2018–2026 | One pre-registered replication of H82 v1.3 unchanged, both periods, both sizes; no variant, no selection. Pass line written first: development excess t ≥ 1.0 on licensed total-return data, else recorded as "weaker than report 53". It replicates; it cannot promote |
| 5 | **ASIC share counts as a dilution flag on the paper book** (free daily short-position files, 2010 on, already held) | A$0 | Whether heavy issuers among the picks do worse going forward | Forward-only shadow flag: each snapshot records the 12-month change in shares on issue per name; a shadow line "H82 without names that issued more than 20%" runs from 31 Dec 2026 with its own clock. No re-run on 2018–2026: report 62 already spent that window and found no effect for this engine |
| 6 | **EODHD fundamentals, forward snapshots** | US$59.99 a month ≈ A$93; two months a year after reporting seasons ≈ A$186 a year | Builds the point-in-time fundamentals archive that does not exist for the ASX in any source held (as first reported, with delisted companies) | Archive only. No test for at least 36 months. The signals to test later (for example gross profitability, net issuance, accruals) are written on a card now, before any data exists. Low priority: it buys an option, not an answer, and breaks the cost ceiling |
| 7 | **ASX listed-companies file saved monthly** | A$0; one browser save | Point-in-time industry groups; today every dead company has none and the 25% cap is weaker than written | Forward-only; part of the monthly routine |

**Not worth buying or building now:** more price history or more price signals (402 trials; the data cannot separate a one-point edge from luck); news or sentiment feeds (report 60: forward-only and no base rate); intraday data (the engine trades at the close once a year).

**If only one thing is done:** item 1 with items 2, 3 and 7 attached. They cost A$370 a year and a few hours.

**If one purchase is added:** Norgate (item 4), once, timed so the rental covers a December formation. It is the only way to learn whether the 2001–2015 result survives dividends and licensed data, and it audits the duplicate problem this report found.

## 5. Reasons this could be wrong

- The wider duplicate test (A7(b)) was designed today by inspecting the vendor's files. I read the 145 new pairs by name and they are renames, but a false match would silently drop a real company. The pair list is written out every month so it can be checked.
- The first two snapshots were computed on 16 Nov from one download; a company renamed between a snapshot date and the download appears under its new code. One case: Magellan Financial Group's old code MFG has its last row on 30 Oct 2026, so the October snapshot lists the company as BJY. The pair is in `dupcodes_2026-10-30.csv`. From 30 Nov the download is made the same evening and this cannot happen.
- EODHD back-adjusts past closes for some rights and bonus issues. Ratios are unaffected within one download, but a month-end close can differ between downloads; the frozen snapshot is the record.
- Industry groups for the first snapshots come from a file dated 14 Nov 2026; 9 of the 300 have no group.
- The independent check in report 67 reuses report 65's validator code with three edits. It is independent of the builder, but it was not rebuilt blind from the v1.3 text.
- The data-cost figures use prices as read in report 52 and the plan shown by the account today (paid, 100,000 calls a day). The exchange rate is approximate.
- Trading dates for 2027 come from a software calendar, not yet from the ASX's published list.

## 6. Files

| What | Path under `scratchpad/bigwins_forward/` |
|---|---|
| Rules v1.3 and hash | `out/FINAL_RULES_v1.3.md`, `out/final_rules_v1.3_hash.txt` (also `research2/67_FINAL_RULES_v1.3.md`) |
| Production prep, snapshot, H100 | `code/bw13_prep.py`, `code/bw13_snapshot.py`, `code/bw13_h100.py`; hashes in `out/code_hashes.txt` |
| Reproduction checks | `code/repro_builder.py`, `code/rep13/`; `out/repro_check1_frozen_engine.csv`, `out/repro_check2_independent.csv`, `out/h100_check_frozen.csv` |
| Duplicate-code correction | `out/dup_codes_frozen.csv` (327), `out/dup_codes_A7b.csv` (472), `out/dup_relaxed_candidates.csv`, `out/sensitivity_unseenB_dupfix_A7b.csv`, `out/h100_check_A7b.csv` |
| Forward record | `out/forward_record/LEDGER.jsonl`, `manifest_<date>.json`, `scores_top300_<date>.csv`, `scores_h101_<date>.csv`, `dupcodes_<date>.csv` for 2026-10-30 and 2026-11-13 |

The scratchpad can be cleared. The forward record folder and the two reports should be copied somewhere durable before the session ends; the ledger is only tamper-evident if a copy of its head hash is kept elsewhere. EODHD data is licensed for the owner's personal use: the snapshots and anything derived stay private.
