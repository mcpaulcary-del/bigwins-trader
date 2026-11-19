# 78. Round 7 — a multi-market forward paper record

18 November 2026. Research and paper only. General information, not financial or tax advice. Nothing here can place an order; the AI never places trades.
Work folder: `scratchpad/fwd_multi/` (`PROGRESS.md`, `code/`, `out/`, `data/`). Job: `scratchpad/bigwins_forward/code/paper_multi.py`. Pre-registration: `68_forward_record/AMENDMENT_forward_multimarket.md` (SHA-256 `2c6a67c6752dbef56a0134c004977607ba23c7c8e6f980e796574d0571b9ea16`, ledger entry 14 (entry SHA-256 `ea3103d7c88b72b0492fd84765b88649d1e53e96e8137f9eb5d57444a7f00f3a`)).

## 0. Plain English

**What now runs.** From the month-end of Monday 30 November 2026, three frozen designs are tracked on paper in 14 stock markets at once, each against that market's own index fund:

- **M3**, the round-5 momentum design (half index fund, half up to 30 shares), in all 14 markets: Australia, Germany, France, Sweden, Switzerland, Canada, Korea, Taiwan, Thailand, Brazil, and also China, Finland, Poland and Belgium, where M3 had its round-5 looks.
- **EI10I**, report 77's enhanced index (shares held at market-cap weight, tilted a little towards momentum and low share issuance), and **CW**, the same book with no tilt, in the ten markets where report 77's cap data passed the check.
- Each design runs with A$25,000 and A$100,000 (local-currency equivalents), with the same costs and tax as the back-tests. 68 paper books in all, plus 100 random-pick books per design and market as a luck yardstick.

A job runs early each month (04:17 UTC, days 1–8). It downloads month-end data, books the paper trades at the next day's close with the frozen engines, and writes `68_forward_record/multi/SCORECARD_MULTI.md`, a history file and one tamper-evident ledger line. It costs about 7,000 (about 17,000 in the months, roughly every third, when share-count files are refreshed; about 10,000 a month on average) API credits a month, inside the existing data plan. It does not touch the Big Wins H82 books, the M3/E3 shadow lines or the daily ASX job.

**How long until an answer.** Long — longer than hoped, and this should be said plainly.

- The designs' monthly results wander around the index fund's by about 4–7 points a year in a single market (tracking error). Against that noise, a +1 point a year edge is invisible for decades in one market.
- Pooling markets helps, but less than tenfold: results in different markets move partly together, so 10–14 markets act like about 3–7 independent ones.
- **For the best case (EI10I or CW at A$100,000):** a true edge of **+2 points a year** would usually show at ordinary statistical strength after about **6–7 years** pooled (ASX alone: 50–90 years). A **+1 point** edge would take about **25–30 years** pooled (ASX alone: over 200 years).
- **M3 is noisier:** about 27 years pooled for +2 points, over 100 for +1.
- **The adopt bar is stricter still**, because 1,649 ideas were tried on history before these: to count, the forward result has to clear a deflated Sharpe ratio of 0.95, which is about the same as a t-statistic of 5. At that bar a +2 point edge in EI10I or CW needs about **27–32 years** pooled; a +1 point edge about a century.
- **What the record can realistically do:** within about 10 years it can show a large edge (roughly +3 points a year or more) if one exists, and it can show quickly if a design is clearly worse than the fund. It will most likely end up saying "level with the index", as every round so far has.

**The rule, set now before any data arrive.** No formal reading before 36 months; readings only at December month-ends (first possible: 31 December 2029).
- **Adopt** (a real-money *proposal*, which the owner then decides on): one design, at both sizes, has a pooled t of 3 or more, a deflated Sharpe ratio of 0.95 or more at 1,649 trials, an after-tax lead of at least +1 point a year, beats 90% of the random books, and is ahead after tax in more than half the markets.
- **Stop** a design and size: pooled t of −2 or worse at a December review from 13 months on, or an after-tax lead of −1 point a year or worse from 60 months on.
- Until then, real money stays in the 40/60 plan.

**First decision:** Monday 30 November 2026 (paper fills at the close of Tuesday 1 December). The first scorecard with returns comes after the 31 December 2026 month-end, in early January 2027.

**Test.** A full live run on 18 Nov 2026 (pretending the first decision was September 2026) downloaded all 14 markets, booked September and October 2026, wrote a scorecard and two ledger lines to a test copy, and said "nothing due" when run again. Its packs agree with the tested ones (top-100 overlap 97–100 of 100 in 13 markets; France 94, because the round-3 France pack lacked six large companies). It used 8,784 of the day's 100,000 credits. The real H82 books and ledger were not touched.

---

## 1. Power analysis: how long the wait is

### 1.1 Method

- Monthly lead = the design's monthly return minus its local fund's, before tax and after costs, from the round-5/6 engines on their own packs, December 2019 – October 2026 (81 months), December start. M3 on 14 markets; EI10I and CW on the ten cap markets (`fwd_multi/code/power.py`; series in `out/power_series.csv`). These are variance estimates, not results: nothing was chosen or changed (not a trial).
- For a true edge δ (points a year), the months needed so that the expected t reaches z_crit + 0.84 (80% power) are n = ((z_crit + 0.84) × σ / δ)², with σ the tracking error of the series being tested: one market's own (ASX) or the equal-weight pooled series across markets (which carries the measured cross-market correlation).
- Three bars: t ≥ 1.96 (ordinary), t ≥ 3.0, and DSR ≥ 0.95 at N = 1,649 (for normal returns the latter needs t ≥ 5.04; `out/power2.json`).
- Before-tax leads stand in for after-tax ones; tax changes the level of the lead much more than its month-to-month noise.

### 1.2 Inputs

| Design, size | Tracking error, median market (pts/yr) | ASX | Mean pairwise correlation of monthly leads | Pooled tracking error | Markets |
|---|---|---|---|---|---|
| EI10I, A$100k | 4.3 | 6.7 | 0.05 | 1.9 | 10 |
| CW, A$100k | 4.4 | 5.2 | 0.05 | 1.8 | 10 |
| M3, A$100k | 6.3 | 5.8 | 0.16 | 3.7 | 14 |
| EI10I, A$25k | 6.5 | 8.9 | 0.05 | 2.6 | 10 |
| CW, A$25k | 7.2 | 7.0 | 0.06 | 2.7 | 10 |
| M3, A$25k | 10.2 | 9.6 | 0.12 | 4.7 | 14 |

### 1.3 Years needed (80% power)

| Design, size | Edge | t ≥ 1.96: ASX only | pooled (calendar years) | pooled market-years | t ≥ 3: ASX only | pooled | DSR ≥ 0.95 (t ≈ 5): ASX only | pooled |
|---|---|---|---|---|---|---|---|---|
| EI10I, A$100k | +2 | 87 | 7 | 72 | 164 | 14 | 385 | 32 |
| EI10I, A$100k | +1 | 350 | 29 | 287 | 657 | 54 | 1539 | 126 |
| CW, A$100k | +2 | 53 | 6 | 62 | 100 | 12 | 234 | 27 |
| CW, A$100k | +1 | 212 | 25 | 246 | 399 | 46 | 935 | 108 |
| M3, A$100k | +2 | 66 | 27 | 380 | 124 | 51 | 292 | 120 |
| M3, A$100k | +1 | 265 | 108 | 1518 | 498 | 204 | 1168 | 479 |
| EI10I, A$25k | +2 | 157 | 13 | 131 | 295 | 24 | 693 | 58 |
| EI10I, A$25k | +1 | 628 | 52 | 522 | 1181 | 98 | 2771 | 230 |
| CW, A$25k | +2 | 95 | 14 | 144 | 179 | 27 | 419 | 64 |
| CW, A$25k | +1 | 380 | 58 | 576 | 715 | 108 | 1676 | 254 |
| M3, A$25k | +2 | 180 | 44 | 612 | 339 | 82 | 795 | 193 |
| M3, A$25k | +1 | 722 | 175 | 2450 | 1357 | 329 | 3181 | 771 |

### 1.4 Smallest edge the record can find (80% power), points a year

| Design, size | in 5 years, t ≥ 1.96 | 10 years, t ≥ 1.96 | 10 years, t ≥ 3 | 10 years, DSR bar | 20 years, DSR bar | ASX only, 10 years, t ≥ 1.96 |
|---|---|---|---|---|---|---|
| EI10I, A$100k | 2.4 | 1.7 | 2.3 | 3.5 | 2.5 | 5.9 |
| CW, A$100k | 2.2 | 1.6 | 2.1 | 3.3 | 2.3 | 4.6 |
| M3, A$100k | 4.7 | 3.3 | 4.5 | 6.9 | 4.9 | 5.2 |
| EI10I, A$25k | 3.2 | 2.3 | 3.1 | 4.8 | 3.4 | 7.9 |
| CW, A$25k | 3.4 | 2.4 | 3.3 | 5.0 | 3.6 | 6.2 |
| M3, A$25k | 5.9 | 4.2 | 5.7 | 8.8 | 6.2 | 8.5 |

What this says:
1. **Pooling buys a factor of about 3–7, not 10.** The leads are weakly but really correlated across markets (0.05–0.16; M3 most, because momentum crashes are global), and several markets are noisier than ASX (China, Korea, Taiwan, Thailand). With correlation ρ, even infinitely many markets cannot push the pooled tracking error below about √ρ × the single-market figure.
2. **The earlier estimate of 10–30 years for ASX alone was too optimistic.** Measured tracking errors of 5–9 points a year put ASX-only detection of +1 to +3 points at roughly 25 to 350 years at ordinary strength.
3. **CW and EI10I at A$100,000 are the only lines with a realistic horizon**: a +2 point edge within 6–7 years at ordinary strength, about 30 years at the full adopt bar. A$25,000 books are noisier (fewer names).
4. **The record is still worth running**, because it is nearly free, because a large edge or a clearly harmful one would show within a decade, and because it measures what the designs really cost and do — with no hindsight.

## 2. The pre-registration

`68_forward_record/AMENDMENT_forward_multimarket.md`, SHA-256 `2c6a67c6752dbef56a0134c004977607ba23c7c8e6f980e796574d0571b9ea16`, appended to `LEDGER.jsonl` as entry 14 (entry SHA-256 `ea3103d7c88b72b0492fd84765b88649d1e53e96e8137f9eb5d57444a7f00f3a`) at 18 Nov 2026 01:02 UTC, before any forward decision. Its sections: why (§1), the designs and frozen-engine hashes (§2), markets (§3), clock and books (§4), the job (§5), data and calls (§6), scoring (§7), the adopt/stop rule (§8), trial count (§9), code hashes (§10). Main points:

- **Designs.** M3 with its tested behaviour (report 77 §1–2 and the v1.1 amendment: hold zone = top 100, fund order before the day's sales, top-ups only when full), EI10I and CW, all run by byte-identical copies of the round-5/6 engines (`sim6.py`, `ei6.py`, `packlib.py`, `scores.py`, `dlf.py`), checked by SHA-256 on every run. One forward adaptation of `capbuild.py`: the fixed "share reports up to 17 Nov 2026" cut becomes "up to the decision date".
- **Markets.** All three designs: ASX, Germany, France, Sweden, Switzerland, Canada, Korea, Taiwan, Thailand, Brazil (cap-weighted index within 4 points of tracking error of the fund in report 77). M3 only: China (caps not valid), Finland, Poland, Belgium (M3's round-5 fresh-market looks; no caps built). Left out: UK, Netherlands, Denmark, Spain, Norway, South Africa, the US bands.
- **Funds, sizes, costs, tax:** local index fund per market (table in the amendment §3); A$25,000 and A$100,000 at constant exchange-rate scales; brokerage, half-spreads, 32% tax on Australian rules as in the looks.
- **Clock:** first decision at each market's November 2026 month-end (30 Nov 2026 everywhere), fills at the next close.
- **Scoring:** monthly; per market and pooled (equal weight); t, DSR at N = 1,649, after-tax lead, 100 random controls per design and market with fixed seeds 1000–1099.
- **ASX:** the multi-market ASX rows use the same generic machinery as the other markets (A200 as the fund). The ASX shadow M3 line keeps running unchanged and remains the canonical ASX M3 record.

## 3. The job: `bigwins_forward/code/paper_multi.py`

### 3.1 What it does each month

1. Reads `/api/user`; paces requests at ≤ 280 credits a minute; stops before the day's usage would leave fewer than 15,000 credits spare, and resumes on the next run.
2. For each market and the oldest unbooked month-end: symbol lists (2 calls); one bulk end-of-day file of the whole exchange for the month-end (100 credits; China 200) to find every company traded heavily enough; end-of-day rows for each candidate company and the fund (1 call each, incremental, adjusted closes re-based on a 40-day overlap; a restated series is fetched again in full); fundamentals for universe companies in cap markets whose file is missing or over 85 days old (10 credits).
3. Builds the decision-date pack with `multi_build.py` (the three tested builders as one function), reading the month-end and the fill day from the data.
4. Runs the frozen engines from the first decision to the month-end: each design and size before and after tax, the fund on the same dollars, and 100 random controls per design.
5. Writes the scorecard, `history_multi.csv` (append-only), `orders_<month>.csv` and one ledger entry; archives every raw response gzip-compressed under `fwd_multi/data/<market>/raw/<date>/` with an index.
6. Is idempotent: a month is booked once; a second run says "nothing due". It books the month when all 14 markets are complete, or on the 8th day of the next month with those that are (the rest recorded as a data block).

Scheduled: not yet; the owner schedules it. Needed: **cron `17 4 1-8 * *` (UTC)**, i.e. 04:17 UTC on days 1–8 of every month, running `python3 -W ignore scratchpad/bigwins_forward/code/paper_multi.py` with no arguments (first booking 1–8 Dec 2026 for the 30 Nov 2026 decisions). It is idempotent, so runs after a month is booked just say "nothing due". 04:17 UTC avoids the ASX daily job (09:27 UTC weekdays) and keeps away from the intraday looks; the job's own pacing (≤ 280 credits a minute, 15,000 spare) protects them anyway.

### 3.2 Checks

**A. Builder against the tested packs (raw files on disk).** For Switzerland, Korea, Taiwan, Brazil, Thailand, China, Finland, Poland and Belgium, the round-4/5 raw downloads were cut to the shape of the forward store (rows from 1 Sep 2024; monthly top-450 candidates) and rebuilt with `multi_build.py`. At every month-end from November 2025 to October 2026 the forward pack matched the tested pack exactly: the same 100 universe companies, the same M3 top 15, identical momentum inputs, rank correlation 1.000 (`out/validate_builder_all.json`).

**B. Live download.** Live run of 18 Nov 2026 (`fwd_multi/test_live/`, `--k0 2026-09 --today 2026-11-18`): all 14 markets downloaded (bulk files, symbol lists, 5,494 end-of-day files, 23 fundamentals) and packs built. Compared with the tested packs at every month-end Nov 2025 – Oct 2026 (`code/validate_live.py`, `out/validate_live.json`), month-end dates equal in all 14. Top-100 overlap (mean / minimum of 100): ASX 99.5/99, Germany 99.1/98, Sweden 99.3/99, Canada 99.0/97, Switzerland 98.6/97, Korea 99.5/98, Taiwan 99.9/99, Brazil 98.3/95, Thailand 99.0/99, China 98.2/89 (one month), Finland 99.4/99, Poland 100/100, Belgium 97.2/96, **France 94.0/94**. M3 top-15 overlap 14.0–15.0 on average (minimum 13). This is Check A for Germany, France, Sweden, Canada and ASX, whose raw files were not on disk. The small gaps elsewhere are vendor revisions since the tested downloads (the same builder matched 100/100 on the original raw files, Check A). **France:** the tested round-3 Paris pack lacks six large companies that the vendor serves today (Saint-Gobain SGO rank 18, Soitec SOI 35, SPIE 52, Sopra Steria SOP 72, SESG 81, SEB SK 90); the six companies ranked 94–100 in the tested pack sit at 101–106 forward. The round-3 raw files are gone, so the cause (most likely a gap in the round-3 download) cannot be traced; the forward pack is the more complete one. Report 77's France results were therefore computed on a universe missing six top-100 names; this does not change the frozen rules

**C. Engines.** On the offline test (Switzerland and Thailand, decision 30 Sep 2026, one month to 30 Oct 2026), the forward job's values equal the tested engine on the tested packs to the cent for M3 and the fund. EI10I and CW differ by 0.02–0.4%, because each company's cap level is anchored to the vendor's market cap against the pack's last row (2 Nov here, 16 Nov in the look) — the one forward adaptation listed in the amendment §2.

**D. Live end-to-end test.** Same run: September 2026 booked as decisions only (bootstrap, 7,046 credits) and October 2026 as one month (1,738 credits), all 14 markets, 34 design-markets, 68 books, 100 controls each; `SCORECARD_MULTI.md`, `history_multi.csv` (142 rows), `orders_2026-09.csv`, `orders_2026-10.csv` and two hash-chained ledger lines written to the test folder and the ledger COPY; a second run said "nothing due". The one-month numbers are information only (for example, pooled before-tax lead for October: M3 −3.8 / −1.7 points at A$25k / A$100k, EI10I −0.5 / −0.2, CW −0.7 / +0.0; one month says nothing)

**E. ASX H82 state untouched.** SHA-256 of the 27 H82 / shadow / ASX-job files taken before any of this work (`out/h82_state_before.sha256`), checked after the live test and after registration: 24 unchanged; the three that changed (`paper/INTRADAY.md`, `alerts.md`, `alerts_latest.md`) are rewritten every two hours by the scheduled ASX intraday look (23:20 UTC run), not by this work. The H82 books, state, code and the shadow lines are unchanged. The real `LEDGER.jsonl` had 13 entries before registration and 14 after (only the amendment entry); the chain verifies

### 3.3 Calls per month

| Item | Credits | When |
|---|---|---|
| Bulk end-of-day file per market (China 2 exchanges) | 1,500 | monthly |
| Symbol lists (2 per market) | 28 | monthly |
| End-of-day files of candidates and funds (≈ 110–600 per market) | ≈ 5,300 | monthly |
| **Typical month** | **≈ 6,900** | |
| Fundamentals (share counts), 10 cap markets × ≈ 100 universe names × 10 credits | ≈ 10,000 | every 85 days (first due Feb 2027) |
| **Average a month** | **≈ 10,000** | |
| One-time bootstrap (done 18 Nov 2026; store kept in `fwd_multi/data/`) | 7,046 | once |

Measured in the live test: 8,784 credits in all (bootstrap 7,046: 5,286 end-of-day, 1,500 bulk, 30 lists, 230 fundamentals; one further month 1,738, low only because the files had just been fetched). Against a daily limit of 100,000 with 15,000 kept spare for the ASX record, even a share-count month (≈ 17,000) fits in one run of about an hour at 280 credits a minute

## 4. Raw data archive

Every response is kept gzip-compressed: `fwd_multi/data/<market>/raw/<YYYY-MM-DD>/<kind>__<symbol>.<csv|json>.gz`, with `fwd_multi/data/<market>/raw/index.csv` (UTC time, kind, symbol, endpoint and parameters without credentials, HTTP status, credits, bytes, SHA-256). The working store is `fwd_multi/data/<market>/store.pkl.gz`. After the live test: about 100 MB in `fwd_multi/data/` (raw archive 1–7 MB a market, 56 MB in all; the rest is the working stores). Expect roughly 15–20 MB of new raw files a month

## 5. Reasons this could be wrong or fail

- **Power figures rest on 81 months of development data** (2019–2026). Tracking errors in a calmer or wilder decade could differ by a third either way; the order of magnitude will not change.
- **Correlation across markets may rise in a crisis**, which would cut the pooling gain further.
- **Data drift.** The store holds candidates only. A company that was never a candidate but became one of the 100 most traded between two month-ends is caught by the bulk file; the builder check showed no gap over 12 months, but a vendor gap in the bulk file could hide one for a month.
- **Cap anchoring and fundamentals plan.** EI10I and CW need share counts. If the fundamentals plan lapses, share counts are carried forward and the scorecard says so; caps then drift with issuance.
- **Engine shortcuts kept as tested.** Dividends are reinvested at no cost, fills are at the next day's adjusted close, a stock that stops trading is paid at its last close, foreign withholding, franking and currency are not modelled. Report 77 found these work slightly against M3; they are kept so the record tests what was tested.
- **Calendars.** Month-ends and fill days are read from the data; China's published holidays end in 2026.
- **Session dependence.** The job runs in this cloud session's scratchpad. If the scratchpad is cleared, the store can be rebuilt (it costs one bootstrap, about 7,000 credits), but the raw archive and ledger should be copied somewhere durable each month.

## 6. Files

| What | Where |
|---|---|
| Pre-registration | `onedrive/research2/68_forward_record/AMENDMENT_forward_multimarket.md` and `.sha256`; ledger entry 14 (entry SHA-256 `ea3103d7c88b72b0492fd84765b88649d1e53e96e8137f9eb5d57444a7f00f3a`) |
| Monthly outputs | `onedrive/research2/68_forward_record/multi/` (`SCORECARD_MULTI.md`, `history_multi.csv`, `orders_<YYYY-MM>.csv`) |
| Job and frozen engines | `bigwins_forward/code/paper_multi.py`, `multi_build.py`, `multi_engine.py`, `multi_frozen/` |
| Job state, packs, evaluations | `bigwins_forward/out/multi/` |
| Store and raw archive | `fwd_multi/data/<market>/` |
| Power analysis | `fwd_multi/code/power.py`, `power2.py`; `fwd_multi/out/power_series.csv`, `power.json`, `power2.json` |
| Checks | `fwd_multi/code/validate_builder.py`, `validate_live.py`, `seed_test_store.py`; `fwd_multi/out/validate_builder_all.json`, `validate_live.json`; tests in `fwd_multi/test_offline/`, `fwd_multi/test_live/`; H82 hashes `fwd_multi/out/h82_state_before.sha256` |
| Progress log | `fwd_multi/PROGRESS.md` |
