# Amendment: SHADOW line EARLY — "young companies that have started well, held while they keep working"

Status: **ADOPTED AS A SHADOW LINE 19 Nov 2026 — PAPER ONLY, INFORMATION ONLY, UNPROVEN** (owner instruction "early investing running by 30 Nov", via the coordinator; report 84 `84_early_stage_new_listings_fable.md`; FD v3.0 §23 item 8). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before the EARLY code is installed** and before its first decision (Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026). **EARLY is not shown to beat the index; no rule in report 84 met the adopt bar; it is tracked to learn, not to fund.** No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence. No automated access to asx.com.au. Rules text below is Fable's draft (`deep84/AMENDMENT_shadow_EARLY.DRAFT.md`, SHA-256 given in the ledger entry) unchanged except this status line and the title. Wiring (record keeper): `bigwins_forward/code/paper_early.py`, a separate idempotent step called from `paper_daily.py` after the other shadow lines, using frozen copies of `deep84/code/early_ref.py` (rules, `PARAMS`) and `deep84/code/early_live.py` (tracker adapter) in `bigwins_forward/code/` (`early_ref.py`, `early_live.py`). Tracker caveats carried: listed funds/trusts classed `new_listing` by the tracker are removed by Y2's name filter (kept); the tracker's ISIN field was repaired on 19 Nov 2026 (ledger seq 32).
No existing rule or line is changed by this amendment.

## 1. Status and honest expectation
**SHADOW: not adopted; tracked for information. UNPROVEN.** Report 84 tested 14 rules and 13 indicators on 2,221 ordinary new listings (2001–2022, later-delisted companies included). **None met the adopt bar.** EARLY is the design the pre-set selection rule picked from the second, exploratory stage (`deep84/PREREG_84b.md`): the only one ahead of the index fund and of both sets of random controls in both periods.

| A$100,000 book, after tax, against the ASX 200 fund | Listings 2001–2012 | Listings 2013–2022 | Listings 2023–May 2025 (tiny) |
|---|---|---|---|
| Report-84 engine (buys on the day the listing reaches 126 sessions) | +2.9 points a year (t 1.4) | +1.7 (t 0.6) | +2.2 (6 names) |
| **This amendment's month-end clock (`early_hist.py`)** | **+1.4 (t 0.6)** | **+3.3 (t 1.0)** | +2.0 (6 names) |
| Same, best single name removed (Zinifex; a2 Milk) | +0.7 | +0.3 | |
| Same, best three names removed | −0.9 | −2.1 | |
| Same, every company with no known takeover written off at delisting | +1.4 | +1.6 | |
| A$25,000 book (10 names), month-end clock | +0.6 | −2.2 | +4.6 |
| Percentile among random young companies with the same exit (C1s) / random older companies with the same exit (C2s), report-84 engine | 92 / 96 | 84 / 91 | |

Read plainly: positive in three samples, never statistically distinguishable from luck, **and the whole lead in each period comes from one to three companies**. The two clocks differ by up to 1.6 points on the same data, which is the size of the noise. Both test periods had been looked at before this design was written, so there is no clean held-out test. The expectation to hold is **"about level with the index fund, with a much bumpier ride; a small chance of one large winner"**.
It cannot be proven by the forward record either: at a tracking error of 8–13% a year, a true +2 point lead needs more than a century to reach t = 3. What the forward record **can** do is (a) show what the rule really buys and what it costs, and (b) score the early-warning indicators on every new listing, where there are about 100 new cases a year (section 7).

## 2. Books
| Book | Start | Sizing | Brokerage |
|---|---|---|---|
| `SHADOW_EARLY_100k_b0` (primary; the only book the adopt bar can read) | A$100,000 in the ASX 200 fund (A200) at the first fill close | each buy 4% of the book's value, at most 25 names | A$0 |
| `SHADOW_EARLY_25k_b0` (information) | A$25,000 in A200 | each buy 10%, at most 10 names | A$0 |
| `SHADOW_EARLY_100k_e1` (cost stress, not a trial) | as primary | as primary | v1.3 E1: max(A$6.60, 0.088%) |
Money not in young companies stays in A200 (distributions reinvested, record's proxy). Whole shares. Half-spread per side on the young companies: the larger of half a price tick and a band by median traded value over the last 63 sessions — A$3m a day or more 0.25%; A$1–3m 0.50%; A$250k–1m 0.75%; A$50–250k 1.25%; below 2.50%. A200 trades: 0.03%.

## 3. Rules
- **Y1 Clock.** Decisions at each ASX month-end after the close, from **Mon 30 Nov 2026**; fills at the close of the next ASX trading day (first: Tue 1 Dec 2026). Nothing is decided on other days.
- **Y2 Universe.** Companies in the new-listings tracker (`newlist_tracker.py`, registry class `new_listing`) whose first trading day in the tracker agrees with the first price row within 5 days. **Never bought:** ETFs, listed funds, listed investment companies, trusts, stapled securities, notes and other non-ordinary securities (`early_ref.fund_flag`, name list); renames, relistings after recapitalisation, demerger children and deferred-settlement codes (tracker classes other than `new_listing`); any code the tracker marks `likely_rename`.
- **Y3 Age window.** A company is looked at once: at the first month-end decision on or after its **126th trading session** (first trading day = session 0). If it fails that day it is never bought later. *Start-up only (30 Nov 2026):* companies between their 126th and 252nd session are also looked at, once, so the book does not start empty; these buys are marked `catch-up` in the orders file and reported separately.
- **Y4 Tests, all measured at the decision close** (`early_ref.features`, `early_ref.passes`):
  1. not a resources company (`early_ref.res_flag`: vendor industry containing mining, gold, silver, copper, uranium, coal, oil and gas, metals, steel or aluminium; if no industry is held, the report-84 name list);
  2. median daily traded value since listing (last 126 sessions) **A$100,000 or more**;
  3. close **A$0.20 or more**;
  4. total return since the first day's close **above zero**;
  5. that return **above the S&P/ASX 200's** price return over the same days.
- **Y5 Buys.** Every company passing Y4 is bought at the fill close for the book's slice (4% or 10% of the book's value at that close), paid for by selling A200. If more pass than there are free places, the highest traded value first; the rest are dropped, not queued. No top-ups. An order with no close on the fill day is dropped. No buy if A200 holds less than 1.02 × the slice.
- **Y6 Sells — only three reasons.** (a) **Stop:** at a month-end decision the holding's value (total return since its fill) is **35% or more below its highest month-end value since the fill** (the fill counts as 1.00). (b) **Time:** 756 trading sessions after the fill. (c) **Payout:** no close for 20 trading sessions — taken as cash at the last close at the next decision (v1.3 C1); a known scheme or takeover is taken at the amount paid. Sells fill at the next session's close; proceeds buy A200. No trimming, no rebalancing, no sale for any other reason.
- **Y7 Income, corporate actions, renames.** Company dividends are cash on the ex-date and buy A200 at the next decision; splits multiply share counts; a code change in the record's A7 list carries the holding. Prices for held companies come from the record's EODHD store once they leave the tracker's window.
- **Y8 Data block.** If the tracker did not run for the decision date, or the price store fails the record's Q4 checks, no decision that month; missed age windows are not revisited.
- **Y9 Nothing is tuned.** Thresholds in Y3–Y6 are frozen (`early_ref.PARAMS`). Section 7's indicator scoreboard is a measurement; it cannot change this line. A changed rule is a new line with its own card, clock and trial.

## 4. Comparators and controls
- `SHADOW_EARLY_CMP_A200_100k` / `_25k`: the same starting money in A200, A$0, never traded.
- **C1s (100 books, seeded):** at each decision, the same number of buys drawn at random from the Y2 universe companies in the same age window (any that traded that day), same sizing, same Y6 exits. Answers "do the Y4 tests add anything".
- **C2s (100 books, seeded):** the same number of buys drawn at random from companies listed more than five years, in the same traded-value band, same sizing, same Y6 exits. Answers "is it the young companies or just the exit rule".
- The scorecard leads with **EARLY minus the median C2s book**, then EARLY minus A200. Controls can never be adopted.

## 5. Scoring
Rows marked SHADOW EARLY on the scorecard: NAV, time-weighted return, lead against A200 before and after tax (32%, 50% discount after 12 months, losses carried forward; sold and kept bases per `AMENDMENT_scoring_v2.md`), share of the book in young companies, names held, each holding's return and distance from its stop, spread and tax paid, the largest single holding's share of the total gain, percentile among C1s and C2s. Daily: marks only (no decisions). State `out/paper_state/early_state.json`; orders `shadow/early_orders_<date>.csv`; decision table (every company looked at, each test's value, pass/fail reason) `shadow/early_decision_<date>.csv`.

## 6. Bar and stop
`AMENDMENT_adopt_rule_v2.md` applies unchanged to `SHADOW_EARLY_100k_b0` (pooled monthly t ≥ 3.0, after-tax lead ≥ +1.0 point a year, ≥ 90th percentile of controls, December reviews from 36 months; staged step from 60 months). **Stated honestly: this line is not expected ever to reach t ≥ 3.0.** Stop rule §4 of that amendment applies (t ≤ −2.0 from 13 months; after-tax lead ≤ −1.0 a year from 60 months). The A$25,000 book is information only.

## 7. Daily learning: the indicator scoreboard (measurement, not a trial)
For **every** ordinary new listing in the tracker (bought or not), record at its 126-session decision: traded value, close, return since first close against the index, daily volatility, first-day move, resources flag, share count and its change since listing, latest reported revenue, profit or loss, cash, and the count of new listings in the previous 12 months. Each day the tracker updates the running return, the worst fall and the best gain. Score each record at +12 and +24 months: return against the index, halved, doubled. Publish a table each month-end of the indicator groups report 84 found worth watching, with their running count:

| Watch-list indicator (report 84, listings 2013–2022) | What it showed | Status |
|---|---|---|
| Most volatile third in the first six months | halved within two years 61% against 33% for the calmest third | one period only; not confirmed 2001–2012 |
| Close under A$0.20 at six months | halved 56% against 45% | one period only |
| Shares on issue up more than 10% in the first year | halved 72% against 25% (191 listings) | one period, small sample |
| Loss-making at twelve months (2016–2022) | halved 57% against 30% for profit-makers; none of the profit-makers went up five-fold | one period; vendor data not point-in-time |
| Above the first-day close at six months | later five-fold winners were 2–3 times as common (6–8% against 2%) | both periods; too rare to trade alone |
First formal reading of the scoreboard: 31 Dec 2028 (about 150–200 scored listings). It informs a future card; it does not alter EARLY.
Forward-only collection (manual, optional, about 10 minutes a company, only for companies that pass Y4 tests 1–3 — about 15–25 a year): issue price, escrow release dates and size, prospectus forecast against the first result, cornerstone or venture backing. Stored beside the scoreboard; no rule uses them.

## 8. Reference code and history test
`deep84/code/early_ref.py` (rules; pure functions; state is a plain dict), `early_live.py` (adapter that reads the tracker's files read-only and prints the decision table), `early_hist.py` (history test on the report-84 dataset), `simlib.py` (report-84 engine). SHA-256 in `deep84/out/early_code_hashes.txt`. `early_hist.py` reproduces the table in section 1; with the traded-value floor set to A$250,000 it reproduces report 84's rule R4 to within 0.2 points. A dry run on the tracker's data as of 18 Nov 2026 with the start-up catch-up looked at 22 companies and passed two (KOA, SK1) — an illustration of the mechanics, **not a registered decision and not a recommendation**.
Known gaps for whoever wires it in: (i) the tracker lists some listed funds and trusts as `new_listing` — Y2's name filter removes them; (ii) the tracker's `registry.csv` has a broken `isin` column (a pandas method was written instead of the value); (iii) the tracker's 2014–2025 baseline is built from the vendor's symbol list, which lacks most companies delisted before 2018, so its base rates are slightly too kind (report 84 §2.4); (iv) held companies need prices from the main store after the tracker's window; (v) the tracker's history holds no delisting reasons — payouts follow Y6(c).

## 9. Trial count
Report 84 added 28 back-test trials (18 in `PREREG_84.md`, 9 in `PREREG_84b.md`, 1 for the month-end implementation). Registering EARLY for forward data adds one. The verdict stands for all lines: **not shown to beat the index.**
