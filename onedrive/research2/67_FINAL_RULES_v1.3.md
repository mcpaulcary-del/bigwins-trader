# 67. Big Wins engine — rules v1.3 (one self-contained document)

16 November 2026. Supersedes `64_FINAL_RULES_v1.1_parts_A-H.md` and `64_FINAL_RULES_v1.2.md`. Paper and research only; nothing here is advice and nothing may place a real order.

**What v1.3 is.** v1.1 (parts A–H) and v1.2 (parts I–O) merged into one text, with every ambiguity listed in reports 54 (17 points), 63 (18 points) and 65 (12 points) settled by an explicit choice. No rule of the engine is changed. Wherever a choice existed, v1.3 takes what the frozen builder code of report 64 actually did, so report 64's figures do not move. Part R lists every choice and says where it would change a number. Part S is the proof that v1.3 reproduces report 64. Part Q is new: the exact inputs and procedure for forward (paper) use from EODHD daily data only.

**One defect found while writing it (section S3).** The duplicate-code test of v1.2 (I3) misses 145 renamed companies, among them WPL/WDS, TPM/TPG and SVW/SGH. In report 64's unseen-B run the engine therefore held Seven Group twice (as SVW and as SGH) in 2023–2024. v1.3 keeps the old test for reproducing report 64 (rule A7(a)) and adds a wider test for forward use (A7(b)). With A7(b) the unseen-B result moves by −1.3 points (A$25,000) and +0.2 points (A$100,000) a year after costs. The verdict of report 64 ("level with the index, no measurable edge") does not change.

Convention: "trading day", "month-end", "close", "adjusted close", `close10` and `last` always have the meanings of part A. Where a number is not stated, it is not part of the rule. Text marked [54-n], [63-n], [65-n] settles that report's ambiguity n.

---

## A. Inputs

There are two sources. **Source E** (EODHD, licensed, with dividends) is the only source for forward use and for 2018 onward. **Source V** (the unlicensed price-only panel `panel_v2`) is used only to re-run the 2001–May 2024 history; its special handling is in annex A-V at the end of this part.

**A1. Trading calendar.** A trading day is a day on which the vendor's index series `AXJO.INDX` has a row. Over 2 Jun 2014–13 Nov 2026 this is identical, day for day, to the official ASX calendar (3,156 days; checked against the XASX session list of `exchange_calendars` 4.13.3). It includes 31 Oct–4 Nov 2016 and 29 May 2020 [65-3-cause: the v2 calendar file lacks those six days; using it shifts a month-end and one volatility window and was the whole cause of report 65's 0.04-point gap]. Rows of any security on any other day are deleted before anything is computed (EODHD carries copy rows on some holidays, for example 1,955 rows on 28 Dec 2015). "Month-end" = the last trading day of a calendar month. Non-trading weekdays in the file, for a validator without the index series:

| Year | Closed weekdays |
|---|---|
| 2014 (from 2 Jun) | 9 Jun, 25 Dec, 26 Dec |
| 2015 | 1 Jan, 26 Jan, 3 Apr, 6 Apr, 8 Jun, 25 Dec, 28 Dec |
| 2016 | 1 Jan, 26 Jan, 25 Mar, 28 Mar, 25 Apr, 13 Jun, 26 Dec, 27 Dec |
| 2017 | 2 Jan, 26 Jan, 14 Apr, 17 Apr, 25 Apr, 12 Jun, 25 Dec, 26 Dec |
| 2018 | 1 Jan, 26 Jan, 30 Mar, 2 Apr, 25 Apr, 11 Jun, 25 Dec, 26 Dec |
| 2019 | 1 Jan, 28 Jan, 19 Apr, 22 Apr, 25 Apr, 10 Jun, 25 Dec, 26 Dec |
| 2020 | 1 Jan, 27 Jan, 10 Apr, 13 Apr, 8 Jun, 25 Dec, 28 Dec |
| 2021 | 1 Jan, 26 Jan, 2 Apr, 5 Apr, 14 Jun, 27 Dec, 28 Dec |
| 2022 | 3 Jan, 26 Jan, 15 Apr, 18 Apr, 25 Apr, 13 Jun, 22 Sep, 26 Dec, 27 Dec |
| 2023 | 2 Jan, 26 Jan, 7 Apr, 10 Apr, 25 Apr, 12 Jun, 25 Dec, 26 Dec |
| 2024 | 1 Jan, 26 Jan, 29 Mar, 1 Apr, 25 Apr, 10 Jun, 25 Dec, 26 Dec |
| 2025 | 1 Jan, 27 Jan, 18 Apr, 21 Apr, 25 Apr, 9 Jun, 25 Dec, 26 Dec |
| 2026 (to 13 Nov) | 1 Jan, 26 Jan, 3 Apr, 6 Apr, 8 Jun |

**A2. Raw files (source E).** Four EODHD end-points, exchange code AU: the symbol list (active and delisted), and per symbol `eod` (date, open, high, low, close, volume — as traded, not adjusted), `splits` (date, ratio "new/old") and `div` (ex-date, `unadjustedValue`, or `value` where that field is absent). Per symbol: rows sorted by date, a repeated date keeps the last row. The working file starts on 2 Jun 2014 (first trading day on or after 1 Jun 2014) and ends on the last complete day of the download (13 Nov 2026 in report 64; the decision day in forward use). Rows with close ≤ 0 are dropped after A3's return is computed.

**A3. Split-neutral daily return** [replaces v1.2 I5, which described this loosely]. For each symbol, on its own rows (before the cut of A2 and before close ≤ 0 rows are dropped):
- Listed ratio of a row = product of the vendor's split ratios dated that day (1 if none). A split or dividend dated on a day with no row is moved to the symbol's next row.
- jump(d) = close(d) ÷ close(previous row), using closes > 0 only.
- A listed ratio s with |ln s| ≥ ln 1.10 is applied on the row, among the listed row and the 3 rows before and 5 rows after it, whose |ln(jump × s)| is smallest, provided that smallest value is below 0.5 × |ln s|; otherwise it is not applied at all (the vendor's closes are taken as already adjusted).
- A listed ratio with |ln s| < ln 1.10 is applied on its own row only if |ln(jump × s)| < |ln(jump)|; otherwise not applied.
- s(d) = product of the ratios applied on row d (1 if none). r(d) = close(d) × s(d) ÷ close(previous row) − 1; total return rt(d) = (close(d) × s(d) + div(d)) ÷ close(previous row) − 1. Both are missing on a symbol's first row or when either close is ≤ 0.
These are the `ret_pr` and `ret_tr` columns of `data_foundation/out/eodhd/panel_tr.pkl` (code `data_foundation/code/eodhd/build_tr.py`); a validator may take them as given.

**A4. Securities.** Symbols the vendor types "Common Stock" whose code is exactly three characters and is not in the exchange-traded-product list (`bigwins_lab/data/etp_list.txt`, 484 codes, SHA-256 `58f00694…f08cc`). Listed investment companies and property trusts are therefore included; ETFs, funds, notes, preference shares, bonds and indices are not.

**A5. Close, adjusted close, traded value.** "Close" of a day = the raw close of the row (a day with no row has none). A row with zero volume keeps its close [54-3]. G(d) = cumulative product of (1 + r(d)) over the symbol's rows in the working file, with a missing r counted as 0. Adjusted close P(d) = G(d) × (last raw close in the file ÷ last G). Traded value of a day = raw close × volume; zero on a day with no row. The adjustment is computed per vendor code before A8 splits a re-used code [65-new]; the earlier part's adjusted closes are therefore scaled by any later split under the same code. In forward use the file ends on the decision day, so P on the decision day equals the quoted close.

**A6. Dividend cash per adjusted share** on ex-date d: D(d) = (rt(d) − r(d)) × P(previous day with a close). A value with |rt − r| ≤ 1e-9, or D ≤ 0, is no dividend. Franking credits are ignored.

**A7. Duplicate codes (renamed companies carried twice).** Applied to the file as downloaded, before the cut at the decision day and before A8. Code X is dropped entirely as a duplicate of code Y when test (a) holds; in forward use also when test (b) holds.
- (a) [frozen test of report 64; 65-10] X's last close is at least 60 trading days after the file's first day and before the file's last day. Over the 60 trading days ending on X's last day X has at least 30 closes. Y has a close after X's last day, and on X's last day |close_Y − close_X| < 1e-9. On the days of that window where both have a close there are at least 30 days, and on every one of them |close_X − close_Y| ≤ 1e-8 + 1e-6 × |close_Y| and |volume_X − volume_Y| ≤ 1e-8 + 1e-6 × |volume_Y|. Candidates Y are tried in alphabetical order; the first that passes is taken. (327 codes on the 13 Nov 2026 file.)
- (b) [new, forward use; not used for report 64's figures] same window and counts; Y has a close after X's last day; closes agree (|close_X − close_Y| ≤ 1e-6 × |close_X|) on at least 90% of the common days; X has at least 5 different close values on the common days. Volume is not tested and the last-day close need not match. If several Y pass, the one with most agreeing days, then alphabetical. (145 more codes; 472 in all.)
- The list of (X, Y, X's last day) pairs is written out at every run. It is the engine's code-change map: a holding recorded under X continues as Y with its lots, dates and cost unchanged.

**A8. Code re-use** [65-11: applies to both sources]. Within one code, a gap of more than 200 calendar days between consecutive days with a close starts a new company. The parts are named `CODE#E`, `CODE#E1`, `CODE#E2`… in time order (source V: the panel's entity id, then the part number). The earlier part ends at its last close and is then subject to C1. The later part has no history before its first close.

**A9. Company order.** "Company-identifier order" = alphabetical order of the vendor code, with a code's original part before all added parts, and added parts after all original codes (this is the column order of the working file). It breaks every tie that the rules send to "identifier order" [54-5, 65-6].

**A10. `close10` and `last`.** `close10(d)` = adjusted close of d, or the most recent adjusted close within the previous 10 trading days if d has none; otherwise missing. `last(d)` = the most recent adjusted close on or before d, however old.

**A11. Industry group** [54-4]. The GICS industry group shown in the official ASX listed-companies file against the company's vendor code (source V: the first code in the entity id). "Not Applic", "Class Pend", or a code not in the file = unknown. For every back-test in reports 53–64 the file is the one dated 14 Nov 2026 (SHA-256 `494034e3…52b6`); a dead company whose code is now used by another company takes that company's group, and most dead companies have none. Forward use: the file saved at the decision month (Q3).

**A12. Index.** S&P/ASX 200 price index = the vendor's `AXJO.INDX` close on each trading day (it has a row on every trading day; a missing value would carry the previous one).

**A13. Delisting records** (used by C1 and N5 in back-tests only). The 1,803 official ASX delisting records, Aug 2000–20 Apr 2020 (`company_study/data/delist.pkl`). A company's record = the earliest record whose code equals the company's vendor code (A8 part; source V: first code of the entity id) and whose date lies from 30 calendar days before to 1,500 calendar days after the company's last close [54-7, 63-12, 65-1]. It is a failure record if its reason contains (case-insensitive) any of: liquidat, administrat, receiver, wound, listing fee, deed of company, 17.12, 17.15, failure to pay, insolven. Otherwise it is a takeover record if the reason contains any of: acqui, scheme, merger, takeover, compulsor, 17.11, amalgamat. Failure is tested first; no record matches both. A company whose last close is on the file's last day has no record. (Example: WFL last traded 30 Jun 2010; its record, unpaid listing fees, is dated 30 Aug 2011, 426 days later, and counts.)

### Annex A-V. Source V (`panel_v2`, price only; replication of 2001–May 2024 only)

- V1. Calendar: the days on which the ASX traded, as the file gives them after these rows are deleted: 27, 28 Dec 1999; 25, 26 Dec 2000; 1 Jan 2001; 29 Mar 2002; 14 Jun 2004; 27 Dec 2005; 1 Jan 2009; every Saturday and Sunday row; 26 Dec 2024; 1 Jan 2025; 27 Jan 2025 [54-2]. The file has no rows on 31 Oct–4 Nov 2016 or 29 May 2020; those days do not exist for source V.
- V2. Securities: entity ids whose first code has three characters, exchange-traded products excluded. Adjusted close = the panel's `p` column; a row whose `p` is missing (3,905 bad-tick rows) has no close for every purpose but keeps its traded value [65-7]. Traded value = the panel's `val`.
- V3. Index: the panel's XJO close; on the 196 days flagged stale (`xjo_ffill`) it is replaced by `AXJO.INDX`; then carried forward over days with no value. 29 Dec 2000 = 3,206.2.
- V4. C1's "whole file" = to 13 Nov 2026 for companies still listed, 31 May 2024 for the others [54-8]. No dividends (A6, I, J do not apply; comparator G3).

---

## B. Signals at a day t (a month-end in the engine)

W = the 252 trading days ending at t. W⁻ = the trading day before the first day of W.

- **B1. Universe.** Companies with a close on at least 200 days of W, ordered by the median of daily traded value over the 252 days of W (largest first; days with no row count as zero); equal medians in identifier order (A9). A company's position is its traded-value rank. The first 300 are the universe.
- **B2.** For each universe company, with ME(j) the month-end j months before t and ME(0) = t:
  - s1 = close10(ME(1)) ÷ close10(ME(12)) − 1
  - s2 = close10(t) ÷ close10(ME(6)) − 1
  - s3 = close10(t) ÷ (highest adjusted close on a day of W that has a close)
  - s4 = −(sample standard deviation, divisor n − 1, of the daily log returns dated in W) [54-1]. The log return dated d = ln(P(d) ÷ P(previous trading day)) and exists only if both days have a close. At most 252 exist (the first uses W⁻). At least 200 are required.
  When t is not a month-end (an interim snapshot, Q2), ME(1) is the latest month-end before t.
- **B3.** Percentile of a signal = its rank among the universe companies that have it (smallest = 1; ties share the average rank) ÷ the number that have it.
- **B4.** Score = mean of the four percentiles. A company missing any has no score.
- **B5.** Score order: highest first; equal scores in traded-value-rank order. Score rank 1 = best.
- **B6.** Buy-eligible at t: has a score; close10(t) ≥ A$0.50 (adjusted close as the file gives it [54-6]; in forward use this is the quoted price); median daily traded value (B1) ≥ 100 × T (C3).

## C. Decisions at each month-end t, in this order

- **C1. Payouts.** A holding whose last close in the whole file is 20 or more trading days before t is removed and paid in cash at that last close × f, with no brokerage or spread. f = 0 if the company has a failure record (A13); otherwise f = 1 (no record exists after April 2020, so a later failure is paid in full). The stress "unexplained = 0.7" pays 0.7 unless the record is a failure (0) or a takeover (1). A payout is a disposal of every lot for tax and closes the position [54-9]. The back-test knows a silent stock never trades again; a suspended stock that trades again later is kept and valued at `last`. Forward use: Q6.
- **C2.** NAV(t) = cash + Σ shares × last(t), struck after C1 and before any tax payment; this is the reported month-end NAV [54-10]. At a June month-end the year's tax (F4) is then paid, and the NAV used in C3 is recomputed after it. Not at the account's first month-end.
- **C3.** Reviews: the account's first month-end and every December month-end (M1 may name another month). At a review n = min(30, max(4, floor(NAV ÷ 2,500))) and T = NAV ÷ n. At other month-ends n is unchanged and T = NAV(t) ÷ n. A holding is "awaiting sale" from the month-end at which its full sale is decided until the sale executes or it is paid out; a pending trim does not count [54-11]. "Live holdings" = holdings not awaiting sale.
- **C4. Review, target list.** Walk companies in score order. Take a company if it is buy-eligible and fewer than ceil(0.25 × n) companies of its (known) industry group are already in this list. Unknown group: never refused. Stop at n. Existing holdings do not pre-fill the count.
- **C5. Review, sells.** Every live holding not in the list is sold in full on E, the next trading day, except under C6. A holding already awaiting sale keeps its pending sale and is neither kept nor re-bought; its place stays empty until C9.
- **C6. Twelve-month deferral.** For a C5 sale in profit at t (shares × last(t) > cost of remaining lots): for each lot, q = the first trading day on or after E at least 367 calendar days after the lot's purchase. If any lot has E < q ≤ E + 31 calendar days, the whole holding is sold on the latest such q.
- **C7. Review, holdings that stay.** value = shares × last(t). If value − 2T ≥ A$1,000: sell floor((value − 2T) ÷ last(t)) shares on E (a trim). Otherwise if value < 0.75 T and T − value ≥ A$1,000: top-up candidate for T − value. Candidates ordered by value ÷ T, smallest first.
- **C8. Review, buys.** Each list company not held in any state is a buy for T, in score order.
- **C9. Other month-ends.** If live holdings < n: walk in score order; take companies that are buy-eligible, not held in any state, and allowed by the industry cap counted from live holdings with a known group; until vacancies are filled. Each is a buy for T. No sale or top-up is decided.
- **C10.** No stop-loss, trend exit, market-regime rule or other sell rule.

## D. Execution (back-test convention)

- **D1.** Sells execute at the close of their day. No close that day: carried to the next day with one; if it never trades again, left to C1.
- **D2.** Buy attempt days: E, and any later trading day on which at least one sell executes, up to and including the next month-end, but never the account's end date. Unfilled buys and top-ups lapse when the next month-end's decisions are made. On an attempt day, after the sells, each open buy once, in order [54-12]: (i) a = min(amount, free cash); if a < max(A$1,000, 0.5 × amount) it waits (it does not block later buys); (ii) else if the stock has no close that day it is dropped; (iii) else buy s = floor((a − brokerage(a)) ÷ (close × (1 + h))) shares; s = 0 drops it. Cash paid = s × close × (1 + h) + brokerage(s × close).
- **D3.** Top-ups: once, together, in C7's order, on the first attempt day at the end of which no buy is waiting: a = min(amount, free cash); executed if a ≥ A$1,000 and the holding is live, sized as D2(iii); otherwise dropped [54-13].
- **D4.** Free cash = cash − tax reserved (F4). Idle cash earns nothing. Whole shares.
- **D5.** Lots are sold oldest first.
- **D6.** Order in a day: dividends (I1); carried and scheduled sells; buys; top-ups; then month-end decisions (effective next trading day).

## E. Costs

- **E1.** Brokerage per order = max(A$6.60, 0.088% of order value).
- **E2.** Half-spread per side h = max(base, 0.5 × tick ÷ price). Base = 0.10% for traded-value rank 1–100, 0.25% for 101–300, 0.50% otherwise or unranked. The rank is that of the most recent month-end strictly before the trade day (a trade on E uses the month-end just decided) [54-14]. Final liquidation: the end date's own rank if the end date is a calendar month-end, otherwise the latest month-end before it (unseen B ends 13 Nov 2026 and uses 30 Oct 2026). Price = adjusted close of the trade. ASX tick sizes: A$0.001 below A$0.10; A$0.005 from A$0.10 to below A$2.00; A$0.01 from A$2.00. Buy pays shares × close × (1 + h) + brokerage; sell receives shares × close × (1 − h) − brokerage, not below zero.

## F. Tax (approximate)

- **F1.** Financial year July–June; the June month-end closes it.
- **F2.** Lot gain = its share of net proceeds − its cost (cost includes spread and brokerage). Long-term if sale date − purchase date ≥ 367 calendar days.
- **F3.** Losses of the year plus losses carried forward are set against short-term gains first, then long-term. Taxable = remaining short-term + remaining long-term × (1 − d); regime A d = 0.5, regime B d = 0. Tax = 32% × taxable + 32% × dividends received in the year (I2). Capital losses do not reduce dividend income. Unused losses carry forward.
- **F4.** Tax reserved = the tax due if the year ended now. Paid from cash at the June month-end and at final liquidation.

## G. Start, end, measures

- **G1.** The account starts as cash at a month-end, which is a review. At the end date: NAV is struck (it closes the last, possibly partial, month); C1 applies; every other holding is sold at last(end) with E costs (a holding with no close on the end date and none later is paid as C1); then F4.
- **G2. Periods.** Development 29 Dec 2000–31 Dec 2015 (V). Unseen A 31 Dec 2015–31 May 2024 (V, price only, comparator G3). Unseen B 29 Dec 2017–13 Nov 2026 (E, dividends, comparator J). Whole 29 Dec 2000–31 May 2024 is one continuous account [54-15].
- **G3. Price comparator.** Index bought once at the close of the trading day after the start (brokerage E1, half-spread 0.03%), sold at the end (same costs); tax 32% × (1 − d) on the gain. NAV at the start month-end = the capital.
- **G4.** CAGR = (final cash ÷ capital)^(1 ÷ years) − 1, years = calendar days ÷ 365.25. "Before costs" = a separate run with E off. "After costs" = E on, tax off. "After tax A/B" = E and F on [54-16].
- **G5.** Monthly return = NAV(month-end) ÷ NAV(previous) − 1 on the after-costs run. Excess = that − the comparator's change over the same dates (G3: index; J: TR series). Annualised excess = 12 × mean; t = mean ÷ (s.d. ÷ √months). Max drawdown on month-end NAV. Turnover = value sold (payouts included; final liquidation of trading holdings not) ÷ mean month-end NAV ÷ years. Trades = executed buys and sells.
- **G6.** Position = one continuous holding from first buy to zero shares. Return = total net proceeds ÷ total cost − 1. "Doubled" ≥ +100%.
- **G7. Random control.** B4's score replaced each month-end by a uniform random number for each company that has a score; 200 runs. Percentile = share of runs with after-costs CAGR below the engine's.
- **G8. Deflated Sharpe.** Bailey and López de Prado (2014) on G5's excess; N stated beside each figure; cross-trial variance = variance of the yearly Sharpe ratios of report 51's 16 models ÷ 12.

## H. Validator files [54-17]

For A$25,000 and A$100,000 on each period: month-end holdings after the next day's trades, every trade and payout, month-end NAV with the comparator, closed positions, and the G4 summary. Builder's files: `deepdive/out/phase2_unseenA.json`, `phase2_unseenB.json`, `p0_v2.json`, `p0_eod.json`, `p0_h100_*.csv`, `stageBC.json`. A difference above 1.0 point a year at A$100,000, or a different sign of an H100 year, is a finding to be explained from this text.

## I. Dividends (source E)

- **I1.** On each ex-date after the account's start day the account receives shares held at the previous close × D (A6), in cash, before that day's trades. Holdings awaiting sale receive it.
- **I2.** The cash is ordinary income of the financial year, taxed as F3; tax reserved includes it.

## J. Total-return comparator (source E)

- **J1. Series TR.** From Vanguard's daily VAS net asset value and the issuer's distribution list (column `cash`, not `gross` [65-8]): return of NAV day d = (NAV(d) + distribution with ex-date d) ÷ NAV(previous NAV day) − 1; a distribution whose ex-date is not a NAV day is ignored. The VAS level is carried over trading days with no NAV. From 8 May 2018 the daily change of Betashares' own A200 total-return index is used; VAS supplies every day up to and including 7 May 2018 [65-2]. Missing days carry the last value.
- **J2. Series PR** = A12.
- **J3. Comparator account.** Capital S. On the trading day after the start the value is (S − brokerage(S)) ÷ 1.0003 and the cost base is S. Each later trading day to the end: y = TR change − PR change of the day (not floored at zero); value ← value × (1 + PR change) + value × y × (1 − τ); cost base ← cost base + value × y × (1 − τ) ("value" in the y terms = value before the day's change). τ = 0 after costs, 32% after tax. End: net = value × (1 − 0.0003) − brokerage(value); tax = τ × (1 − d) × max(0, net − cost base). CAGR as G4. Month-end NAV = value; at the start month-end = S.
- **J4.** Monthly excess (G5) is against the month-end to month-end change of TR.

## K. Retired challengers H88, H90 (for replication only) — text unchanged from v1.2

- **K1. H88.** For each universe company with a B4 score: ID = sign(Q) × (share of negative daily returns − share of positive daily returns) over the 231 trading days t−251 to t−21. A daily return exists only when that day and the previous trading day both have a close; at least 150 must exist. Q = last(t−21) ÷ last(t−252) − 1; sign(0) = 0. X = −ID. H88 score = mean of the percentile of the B4 score and the percentile of X (B3, each over the companies that have it). Order B5.
- **K2. H90.** X = −(trading days between t and the most recent day in W on which last(day) was at its maximum over W; latest day if repeated). Score = percentile of X. Order B5.

## L. Tranche form F1 (retired; replication only) — unchanged from v1.2

Capital split into four sub-accounts of S ÷ 4, reviewed in March, June, September, December respectively; each starts at the first month-end of its month on or after the start and holds S ÷ 4 cash at 0% before that. n = min(8, max(3, floor(NAV ÷ 2,500))) on the sub-account's NAV. All rules C–F apply inside each sub-account separately. Account figures are sums. G7 uses the same seed in all four.

## M. Start-month stress and robust score — unchanged

- M1. An account "started in month m" starts at the stated month-end and reviews in month m instead of December.
- M2. Robust score = mean after-tax-B CAGR of eight development accounts: A$25,000 and A$100,000, started 29 Dec 2000, 30 Mar 2001, 29 Jun 2001, 28 Sep 2001, ended 31 Dec 2015.

## N. H100 June sleeve (paper card; report 63's guard rails stay in force)

- **N1.** Each year: B = the 4th-last trading day of June; S = the trading day before B; X = the last trading day of July.
- **N2.** Measured on S over the 252 trading days ending at S [63-1]: traded days = days with a close [63-10]; median traded value over all 252 days; traded-value rank among companies with ≥ 200 traded days (ties: identifier order [65-6]).
- **N3. Universe:** rank > 300; median traded value ≥ A$50,000; a raw close on S [63-2] that is ≥ A$0.05 [63-9]; last(S) and last(S − 252 trading days) both exist. Securities A4.
- **N4. Losers** [63-18]: universe companies whose return last(S) ÷ last(S − 252) − 1 is ≤ the 0.2 quantile of the universe's returns (linear interpolation). No cap on the number. A year with fewer than 25 universe companies is skipped.
- **N5.** Buy every loser with a close on B, at that close; a loser with no close on B is dropped [63-3]. A$2,500 a name. Sell at the close of X; no close on X: valued at last(X). If its last close in the whole file is 20 or more trading days before X [63-11] it is paid last close × f, where f = 0 for a failure record, 1 for a takeover record, 0.7 otherwise (A13 decides the record [65-1]). The 0.7 applies after April 2020 too: C1's "paid in full" is the engine's rule, not this sleeve's.
- **N6. Costs per side:** half-spread = max(0.5 × tick ÷ price; 0.50%; half the Abdi–Ranaldo (2017) estimate), plus brokerage A$6.60 on A$2,500 (0.264%) on both sides [63-14]. Tick price = the raw close on the measurement day (S for the buy, X for the sell), or last() of that day if it has none [65-4]; ticks as E2. Estimate, over the 64 trading days ending on the measurement day [63-13]: c = ln raw close, η = (ln raw high + ln raw low) ÷ 2; spread = 2 × sqrt(max(0, mean over the 63 consecutive-day pairs inside the window of (c(d) − η(d)) × (c(d) − η(d+1)))); a pair with a missing or non-positive price is skipped; no pair = 0; no split adjustment inside the window [65-5]. Net return = (1 + gross) × (1 − h_sell − 0.00264) ÷ (1 + h_buy + 0.00264) − 1. With dividends, gross includes D (A6) for ex-dates after B up to X, added to the exit value.
- **N7.** Year result = mean net return of the names bought − comparator change from the close of B to the close of X (PR for source V, TR for source E). Second benchmark [63-17]: the same net return for every universe company with a close on B; its count is of those companies [65-12].
- **N8.** Reported split [63-16]: names with raw close on S below, or at or above, A$0.20, as a filter of the picks.
- **N9. Years** [65-9]. Source V: 2002 and 2004–2023 exist (2001 and 2003 have fewer than 25 universe companies); reported statistics use 2004–2015 (development) and 2016–2023. Source E: 2016–2026 exist; reported 2018–2026, of which 2024–2026 had never been seen. Forward: June 2027 onward only.

## P. H101 tracking line (forward only; no back-test figure depends on this text)

Report 64's H101 check used a simplified reading and is not the definition. From the December 2026 month-end t:
- **P1. Universe** [63-2, 63-8]: traded-value rank 301–1000 at t (B1 ordering); median traded value ≥ A$50,000; a raw close on t that is ≥ A$0.50.
- **P2. Score** [63-4, 63-6]: B2–B4 computed inside this universe (month-end closes with `close10`); companies without a score stay in the universe benchmark.
- **P3. Picks** [63-8]: the ceil(0.10 × number scored) best by B5 order. No minimum count.
- **P4. Hold** [63-3, 63-5]: bought at the close of the trading day after t (no close that day: dropped); sold at the close of the first trading day at least 367 calendar days after the buy. Equal dollars, A$2,500 a name.
- **P5. Costs** [63-7]: N6 on both sides, on every name. A pick that stops trading is recorded as takeover, failure or unknown from the actual announcement (Q6).
- **P6. Reported:** mean and median pick against A200 total return and against the equal-weight universe; a shadow cohort each March, June and September month-end. H101 and H82 count as one bet. Closed at the 36-month look if behind A200.

## Q. Forward (paper) operation: exact inputs and procedure

- **Q1. Inputs.** EODHD "EOD Historical Data" plan only: A2's four end-points for every AU symbol, downloaded after the close of the decision day and before the next open. Plus three static or hand-saved files: the ETP list (A4); the ASX listed-companies file saved by the owner in a browser in the decision month (A11); issuer figures for the comparator (Betashares A200 total-return index and distributions). Nothing from `panel_v2`, rs77, stockanalysis or any unlicensed copy enters a forward decision. The delisting-record list (A13) is not used forward.
- **Q2. Procedure at a decision day t.** Apply A1; A3; A4; A7(a) and A7(b) on the file as downloaded; cut at t; A5–A10; B1–B6 at t. Write the snapshot (the 300 universe companies with rank, median value, close, s1–s4, the four percentiles, score, score rank, industry group), the A7 pair list and a manifest with the SHA-256 of every input and output. The manifest's hash is appended to a hash-chained ledger. Code: `bigwins_forward/code/bw13_prep.py`, `bw13_snapshot.py`.
- **Q3. Industry groups.** The file saved in the decision month; if none was saved, the latest earlier saved file. Unknown never blocks a buy.
- **Q4. Data block.** If `AXJO.INDX` has no row for t, or fewer than 285 of the 300 universe companies have a close on t, no decision is made that month and the ledger records `BW_DATA_BLOCK`.
- **Q5. Prices and fills.** `paper_sim` books every trade at the close of its day under D and E (the back-test convention), from the next day's download. If the IBKR paper account is used as well, its fills are a second line; the scorecard shows both.
- **Q6. Stopped trading.** A holding with no close for 20 trading days is not paid out automatically. It is carried at its last close and flagged until the outcome is known from the company's announcement: takeover or scheme = the cash actually paid, on the payment date; scrip = the shares received continue the holding; failure = zero. While flagged, the scorecard also shows NAV with the holding at 70% of its last close.
- **Q7. Corporate actions.** Splits and consolidations follow A3 on the next download; share counts in the ledger are multiplied by the applied ratio. Code changes follow A7's pair list. Vendor restatements of past closes never change a frozen snapshot.

## R. Register of choices (every ambiguity of reports 54, 63, 65)

"No change" = the choice is what the frozen code did, so no reported figure moves.

| Ref | Point | v1.3 choice | Rule | Changes a number? |
|---|---|---|---|---|
| 54-1 | Volatility: 251 or 252 returns | 252 dated in W | B2 | No change (other reading: up to 1.0 pt) |
| 54-2 | Calendar vs file rows | Listed rows deleted | A1, V1 | No change (other: up to 0.5 pt) |
| 54-3 | Close with zero volume | Kept as a close | A5 | No change |
| 54-4 | Industry group of renamed / dead code | Literal lookup of the vendor code, file of 14 Nov 2026 | A11 | No change |
| 54-5 | Tie in median traded value | Identifier order | A9, B1 | No change |
| 54-6 | A$0.50 on adjusted or quoted price | Adjusted (equal to quoted in forward use) | B6 | No change |
| 54-7 | Delisting record matching | Earliest record −30…+1,500 days, same code | A13 | No change |
| 54-8 | "Last trade ever" | Whole file | C1, V4 | No change |
| 54-9 | Payout a tax disposal | Yes | C1 | No change |
| 54-10 | June NAV before or after tax | Reported before; n and T after | C2 | No change |
| 54-11 | Pending sale at a review; pending trim | Sale kept, not re-bought; trim is not "awaiting sale" | C3, C5 | No change |
| 54-12 | Order of buy tests | Cash test, then no-close drop; no blocking; brokerage on shares × close | D2 | No change |
| 54-13 | Top-up with no trade; lapse | Dropped; lapses | D3 | No change |
| 54-14 | Rank for cost; liquidation; tick basis | Previous month-end; end date's own only if a calendar month-end; adjusted price | E2 | No change |
| 54-15 | Whole period | One account | G2 | No change |
| 54-16 | Reported measures | Defined | G4–G8 | No change |
| 54-17 | Validator files | Listed | H | — |
| 63-1 | H100 measured on buy day or day before | Day before (S) | N2 | No change (other: up to 5 pts in a year) |
| 63-2 | Must have traded on the measurement day | Yes (raw close on S; on t for H101) | N3, P1 | No change for H100 |
| 63-3 | No trade on buy day | Dropped | N5, P4 | No change |
| 63-4 | H101 scores: month-ends or day counts | Month-ends, `close10` | P2 | Forward only |
| 63-5 | H101 "12 months" | First trading day ≥ 367 calendar days after the buy | P4 | Forward only |
| 63-6 | H101 unscored companies in the benchmark | Yes | P2 | Forward only |
| 63-7 | H101 costs | Full cost, every name, both sides | P5 | Forward only |
| 63-8 | H101 top tenth before or after the filter; minimum | After the filter; no minimum | P1, P3 | Forward only |
| 63-9 | Price tests raw or adjusted | Raw for H100 and H101 | N3, P1 | No change |
| 63-10 | "Traded day" | Day with a close | N2 | No change |
| 63-11 | When is a stock "delisted" at exit | Last close ≥ 20 trading days before X | N5 | No change |
| 63-12 | Record look-up window | 1,500 days | A13 | No change |
| 63-13 | Spread window | 64 trading days (63 pairs) ending on the measurement day | N6 | No change |
| 63-14 | Sale commission | On A$2,500 | N6 | No change |
| 63-15 | Capacity median | 63-day median, 5% of it (guard rail, not a return rule) | 68 §2.5 | — |
| 63-16 | ≥ 20c variant | Filter the picks | N8 | No change |
| 63-17 | Universe benchmark gross or net | Net, same costs | N7 | No change |
| 63-18 | Worst fifth cut-off | Return ≤ 0.2 quantile | N4 | No change |
| 65-1 | N5 record matching; failure vs takeover; 0.7 vs "f = 1" | A13 window; failure first; 0.7 in H100 always | A13, N5 | No change (a 365-day window moves 2010 by 1.35 pts) |
| 65-2 | TR series on 7 May 2018 | VAS supplies 7 May | J1 | No change (other: comparator −0.04 pt) |
| 65-3 | v1.2 not self-contained | This document | all | — |
| 65-4 | N6 tick price | Raw close on the measurement day | N6 | No change |
| 65-5 | Abdi–Ranaldo details | Pairs inside the window; non-positive skipped; no split adjustment | N6 | No change |
| 65-6 | Rank ties, renamed company | Identifier order (A9) | A9 | No change |
| 65-7 | v2 rows with raw close, no adjusted close | No close; traded value kept | V2 | No change |
| 65-8 | `cash` or `gross` distribution | `cash` | J1 | No change (gross: +0.04 pt) |
| 65-9 | H100 years | Stated | N9 | — |
| 65-10 | I3 tolerance | 1e-8 + 1e-6 × |Y's value| | A7(a) | No change |
| 65-11 | Code re-use on v2 | Both sources | A8 | No change |
| 65-12 | Benchmark count | Companies with a close on B | N7 | — |
| new | Calendar for source E | Index-row days, including 31 Oct–4 Nov 2016 and 29 May 2020 | A1 | No change; this was the unexplained FBU/NIC difference of report 65 |
| new | Split rule as coded | Stated in full | A3 | No change |
| new | Adjustment per code before the re-use split | Stated | A5 | No change |
| new | End date not a month-end | Closes the last month; cost rank of the previous month-end | E2, G1 | No change |
| new | Duplicate codes missed by the frozen test | A7(b), forward use | A7 | **Yes if applied to history: see S3** |

## S. Reproduction of report 64

**S1. v1.3 production code with the frozen engine.** `bw13_prep.py` (parts A–B, test A7(a)) builds the bundle from the EODHD panel; the frozen engine (`deepdive/code/engine_dd.py`, SHA-256 `67468ad7…be55`, unchanged) runs it. The bundle equals report 64's in every array and in all 924 month-end table fields compared. Unseen B, 29 Dec 2017–13 Nov 2026:

| Measure, % a year | Report 64 A$25k | v1.3 A$25k | Report 64 A$100k | v1.3 A$100k | Largest difference |
|---|---|---|---|---|---|
| Before costs | 9.964 | 9.964 | 10.449 | 10.449 | 0.000 pt |
| After costs | 9.612 | 9.612 | 9.746 | 9.746 | 0.000 |
| After tax A | 7.237 | 7.237 | 7.542 | 7.542 | 0.000 |
| After tax B | 6.577 | 6.577 | 6.685 | 6.685 | 0.000 |
| Comparator after costs / tax A / tax B | 8.777 / 6.835 / 6.208 | same | same | same | 0.000 |
| Max drawdown | −22.93 | −22.93 | −25.53 | −25.53 | 0.000 |

**S2. Independent code from the text.** Report 65's blind re-implementation, changed in exactly three places to follow v1.3 (calendar A1; working-file start A2; 7 May 2018 in J1), in `bigwins_forward/code/rep13/`:

| Measure, % a year | Report 64 | Independent, v1.3 | Difference | Report 65 (v1.2) difference |
|---|---|---|---|---|
| A$25k before / after costs / tax A / tax B | 9.964 / 9.612 / 7.237 / 6.577 | 9.964 / 9.612 / 7.237 / 6.577 | 0.0000 pt | 0.000 |
| A$100k before costs | 10.4493 | 10.4490 | −0.0003 | +0.039 |
| A$100k after costs | 9.7457 | 9.7456 | −0.0001 | +0.024 |
| A$100k after tax A / B | 7.5416 / 6.6853 | 7.5416 / 6.6853 | 0.0000 | +0.008 / +0.006 |
| Comparator after costs / tax A / tax B | 8.7769 / 6.8353 / 6.2082 | same | 0.0000 | −0.043 / −0.029 / −0.029 |

Largest difference 0.0003 point, against the 0.05-point target. The remaining 0.0003 comes from the SVW/SGH pair of S3 (the two codes of one company are bought in the opposite order, 225 and 215 shares swapped) and one share of a later trade (SSM, 3,975 against 3,974 shares, Jan 2025).

H100 on source E, 2016–2026, from `bw13_h100.py` (part N): every year equal to report 64's `p0_h100_eod.csv` to 4e-9 point; same counts.

**S3. Where a v1.3 choice would change history: duplicate codes.** The frozen test A7(a) needs prices and volumes to agree on every common day and on the old code's last day. EODHD's old-code files often carry different volumes, or one stale last row. The wider test A7(b) finds 145 more renamed companies (472 in all), including WPL→WDS, TPM→TPG, SVW→SGH, SYA→ELV, ABP→ABG, PTM→L1G, IMF→OBL, FXL→HUM, GMA→HLI, ECX→FPR, VVR→WPR, COE→AEL, RED→VAU. (Report 64 named WPL/WDS as an example of a pair its test removed; it did not.) In the frozen run both copies sat in the universe until the rename, and the A$100,000 account bought Seven Group twice on 3 and 9 Jan 2023.

Unseen B re-run with A7(b) (a data correction, not a new trial; file `out/sensitivity_unseenB_dupfix_A7b.csv`):

| % a year | A$25k frozen | A$25k A7(b) | A$100k frozen | A$100k A7(b) | Comparator |
|---|---|---|---|---|---|
| After costs | 9.61 | 8.27 | 9.75 | 9.96 | 8.78 |
| After tax A | 7.24 | 6.95 | 7.54 | 7.47 | 6.84 |
| After tax B | 6.58 | 6.32 | 6.69 | 6.47 | 6.21 |
| Excess a year (t) | +1.4 (0.3) | +0.1 (0.0) | +1.3 (0.4) | +1.5 (0.5) | — |

H100 with A7(b): no year changes sign; the largest change is −1.5 points (2022); the 2018–2026 mean stays +4.0%. Reading: the moves are inside the one-point noise floor at A$100,000 and show again how little a ten-share account means. Report 64's verdict stands. Forward use applies A7(b).

**S4. Files** (under `scratchpad/bigwins_forward/`): `code/bw13_prep.py`, `bw13_snapshot.py`, `bw13_h100.py`, `repro_builder.py`, `rep13/`; `out/repro_check1_frozen_engine.csv`, `repro_check2_independent.csv`, `h100_check_frozen.csv`, `h100_check_A7b.csv`, `sensitivity_unseenB_dupfix_A7b.csv`, `dup_codes_frozen.csv`, `dup_codes_A7b.csv`, `dup_relaxed_candidates.csv`.

**Limits.** Parts K, L, M and annex A-V were merged as text and not re-run here; report 65 replicated the source-V accounts exactly under the same readings. The S2 code shares its ancestry with report 65's validator, so it is independent of the builder but was not written blind to v1.3. A3 was transcribed from `build_tr.py`; a validator who rebuilds returns from raw files rather than taking the two columns has not yet been tried.
