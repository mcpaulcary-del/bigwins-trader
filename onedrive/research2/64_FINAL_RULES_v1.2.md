# Big Wins engine — frozen rules v1.2 (report 64). Rules text only: no result, no rationale.

Frozen 2026-11-16. v1.2 = `bigwins2/out/FINAL_RULES_v1.1.md` (SHA-256 in `bigwins2/out/final_rules_v1.1_hash.txt`) UNCHANGED, plus the parts below.
A validator re-implements from v1.1 and this file alone. Where a number is not stated, it is not part of the rule. Section letters
continue v1.1 (A–H); "v1.1 X9" means rule X9 of v1.1. Every point marked [guess-proof] is one that reports 54 and 63 show a second
reader would otherwise have to guess.

## I. Inputs when the price source carries dividends (licensed total-return source; here EODHD "eod", "splits", "div" files)

I1. Securities: records the vendor types "Common Stock" whose code is exactly three characters and is not in the exchange-traded-product
    list (`bigwins_lab/data/etp_list.txt`). All other types are dropped before anything is computed.
I2. Days: only days of the official ASX trading calendar (v1.1 A1); the file is cut at 13 Nov 2026. Rows with close ≤ 0 are dropped.
I3. Duplicate codes [guess-proof]. The vendor keeps a renamed company under both codes. Code X is a duplicate of code Y, and X is dropped
    entirely, when: X's last close is before the file's last day; Y has a close after X's last day; on X's last day both have the same raw
    close (difference < 1e-9); and over the 60 trading days ending on X's last day there are at least 30 days on which both have a row and
    on all of those days raw close and volume agree to a relative 1e-6. If several Y qualify, the first in alphabetical order.
I4. Code re-use [guess-proof]. Within one code, a gap of more than 200 calendar days between consecutive rows starts a new company (v1.1 A2).
    The earlier part ends at its last row (and is then subject to v1.1 C1); the later part has no history before its first row.
I5. Split-neutral daily return of day d: r(d) = close(d) × s(d) ÷ close(d−1) − 1, where s(d) is the split ratio the vendor lists within
    −3..+5 sessions of d AND for which the raw close shows the matching jump on d (within 3%); otherwise s(d) = 1. (This is the `ret_pr`
    column of `data_foundation/out/eodhd/panel_tr.pkl`; the validator may take that column as given.)
I6. Adjusted close (replaces "adjusted close" in v1.1 A2): P(d) = G(d) × (last raw close ÷ last G), G = cumulative product of 1 + r from the
    company's first row (r = 0 on the first row). The A$0.50 test (v1.1 B6) and the tick test (v1.1 E2) use P.
I7. Traded value of day d = raw close(d) × volume(d). No row: zero.
I8. Dividend of day d (its ex-date), in cash per adjusted share: D(d) = [ (close(d) × s(d) + div(d)) ÷ close(d−1) − 1 − r(d) ] × P(previous
    row), where div(d) is the vendor's unadjusted dividend amount. Franking credits are ignored. A value ≤ 1e-9 × P is no dividend.
I9. Dividend cash. On each ex-date after the account's start day, the account receives shares held at the previous close × D(d) in cash
    that day, before that day's trades (v1.1 D6 order: dividends, sells, buys, top-ups, month-end decisions). Holdings awaiting sale receive
    it too. The cash is ordinary income of the financial year.
I10. Tax with dividends (extends v1.1 F3–F4): tax of the year = 32% × (taxable gains as v1.1 F3) + 32% × dividends received in the year.
    Capital losses do not reduce dividend income. Tax reserved (v1.1 F4) includes the 32% on dividends received so far in the year.
I11. Delisting records (v1.1 C1) are matched on the code of the company part (I4). After April 2020 no record exists and f = 1; the stress
    "unexplained = 0.7" pays f = 0.7 whenever there is no record or the record has neither a failure nor a takeover keyword
    (takeover keywords as in `company_study/data/delist.pkl`, column `takekw`).
I12. Index (v1.1 A6) = the vendor's AXJO.INDX close. In the v2 panel, XJO on a day flagged stale (`xjo_ffill`) is replaced by AXJO.INDX.

## J. Total-return comparator (replaces v1.1 G3 when I applies)

J1. Series TR: from Vanguard's daily VAS net asset value and the issuer's distribution list (`actuals/data/derived/vanguard_nav_daily.csv`,
    `dist_VAS.csv`): return of day d = (NAV(d) + distribution with ex-date d) ÷ NAV(previous NAV day) − 1. From 7 May 2018 the daily change
    of Betashares' own A200 total-return index (`betashares_total_return_index_daily.csv`) is used instead. Missing days carry the last value.
J2. Series PR = the index of I12.
J3. Comparator account: capital S; on the trading day after the start month-end the value is (S − brokerage(S)) ÷ 1.0003. Each later day
    through the end date: y = TR change − PR change of that day (NOT floored at zero); value ← value × (1 + PR change) + value × y × (1 − τ);
    cost base ← cost base + value × y × (1 − τ) (cost base starts at S; "value" in the y terms is the value before the day's change).
    τ = 0 for "after costs", 32% for "after tax". At the end: net = value × (1 − 0.0003) − brokerage(value);
    tax = τ × (1 − d) × max(0, net − cost base), d as v1.1 F3. Final = net − tax. CAGR as v1.1 G4.
J4. Monthly excess (v1.1 G5) is measured against the month-end to month-end change of TR.

## K. Scores of the two retired challengers (for replication only)

K1. H88. For each universe company with a v1.1 B4 score: ID = sign(Q) × (share of negative daily returns − share of positive daily returns),
    over the 231 trading days from t−251 to t−21 inclusive (t = the month-end, counted in calendar trading days). A daily return exists only
    when both that day and the previous trading day have an actual close; shares are of the returns that exist; at least 150 must exist.
    Q = last(t−21) ÷ last(t−252) − 1 (v1.1 A3 `last`); sign(0) = 0. X = −ID. H88 score = mean of two percentiles: the percentile of the B4 score and the
    percentile of X, each computed as in v1.1 B3 over the universe companies that have that one quantity. A company missing either has no
    H88 score. Order: v1.1 B5.
K2. H90. X = −(number of trading days between t and the most recent day, within the 252 trading days ending at t, on which last(day) was
    at its maximum over those 252 days; if the maximum occurs more than once the latest day counts). Missing if last(t) is missing.
    Score = percentile of X (v1.1 B3). Order: v1.1 B5 (ties, which are common at X = 0, go by traded-value rank).
K3. Everything else as v1.1.

## L. Tranche form (candidate F1 of report 64; retired after its look; for replication only)

L1. Capital S is split into four sub-accounts of S ÷ 4, one for each review month m ∈ {March, June, September, December}.
L2. Sub-account m starts (in cash, v1.1 G1) at the first month-end of calendar month m on or after the account's start month-end. Before its
    start its value is S ÷ 4 in cash at 0%. Its only review month-ends are its start and every later month-end of month m (replaces
    "every December" in v1.1 C3).
L3. In v1.1 C3, n = min(8, max(3, floor(NAV ÷ 2,500))) with NAV the sub-account's own. Every other rule (C–F) applies inside each
    sub-account separately: its own cash, its own industry count, its own tax years, its own loss carry-forward; no transfer between
    sub-accounts; the same company may be held by several sub-accounts.
L4. Account NAV at a month-end = sum of the four sub-account NAVs (v1.1 C2). Final value = sum of the four finals. Costs, turnover, CAGR,
    excess and drawdown are computed on the sums. Random-portfolio control (v1.1 G7): the same seed is used in the four sub-accounts.

## M. Start-month stress and the robust development score

M1. An account "started in month m" starts at the stated month-end and uses month m in place of December in v1.1 C3.
M2. Robust score = arithmetic mean of the after-tax-B CAGRs of eight accounts: A$25,000 and A$100,000, each started 29 Dec 2000,
    30 Mar 2001, 29 Jun 2001 and 28 Sep 2001, all ended 31 Dec 2015.
M3. Unseen periods: A = 31 Dec 2015 – 31 May 2024 on the v2 panel, price-only, v1.1 G3 comparator. B = 29 Dec 2017 – 13 Nov 2026 on the
    I-source with dividends, J comparator.

## N. H100 June sleeve — rule text as run in report 64 (paper card; guard rails of report 63 section 8 stay in force)

N1. Each year: B = the 4th-last ASX trading day of June; S = the trading day before B; X = the last trading day of July.
N2. Measured on S over the 252 trading days ending at S [63-1]: traded days = days with a close; median traded value = median over all 252
    days (no-row days count as zero); traded-value rank among companies with ≥ 200 traded days (1 = largest; ties by code order).
N3. Universe: rank > 300; median traded value ≥ A$50,000; a raw (as-quoted) close ON S [63-2: a company with no
    close on S is not in the universe] that is ≥ A$0.05 [63-9: raw]; `last(S)` and `last(S − 252 trading days)` both exist. Securities as I1 (or v1.1 A4).
N4. Loser group [63-18]: universe companies whose return last(S) ÷ last(S−252) − 1 is ≤ the 0.2 quantile of the universe's returns
    (linear-interpolation quantile). No cap on the number.
N5. Buy every loser that has a close on B, at that close [63-3: a loser with no close on B is dropped, not bought later]. Equal dollars,
    A$2,500 per name in the evaluation. Sell at the close of X; a name with no close on X is valued at last(X); if its last close in the
    whole file is 20 or more trading days before X it is paid last close × f (failure record 0, takeover record 1, otherwise 0.7).
N6. Costs per side: half-spread = max(0.5 × tick ÷ raw close; 0.50%; half of the Abdi–Ranaldo (2017) two-day estimate) + brokerage
    A$6.60 on A$2,500 (0.264%) on both sides [63-14]. Estimate: over the 64 trading days ending on the measurement day (S for the buy, X for
    the sell) [63-13: trading days, not traded days], c = ln close, η = (ln high + ln low) ÷ 2 of the same day; spread =
    2 × sqrt(max(0, mean over consecutive-day pairs of (c(d) − η(d)) × (c(d) − η(d+1)))), pairs with a missing value skipped; no pair = 0.
    Net return of a name = (1 + gross) × (1 − h_sell − 0.00264) ÷ (1 + h_buy + 0.00264) − 1; with dividends, gross includes D (I8) for
    ex-dates after B up to X.
N7. Year result = mean net return of the names bought − index change from the close of B to the close of X (PR index for price-only data,
    TR series J1 with dividends). Second benchmark [63-17]: the same net return computed for every universe company with a close on B.
N8. Reported split [63-16]: names with raw close on S below / at-or-above A$0.20, as a filter of the picks (the universe is not re-formed).

## O. Validator files

Builder's outputs for the check: `deepdive/out/phase2_unseenA.json`, `phase2_unseenB.json`, `p0_v2.json`, `p0_eod.json`,
`p0_h100_v2.csv`, `p0_h100_eod.csv`, `stageBC.json`, `p0_holdings_overlap_*.csv`. A difference above 1.0 point a year at A$100,000, or a
different sign of any H100 year, is a finding to be explained from this text, not from the builder's code.
