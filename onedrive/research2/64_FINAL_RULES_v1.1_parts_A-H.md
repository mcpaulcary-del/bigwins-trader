# Big Wins engine — frozen rules, v1.1 (v-final = v0; wording completed after the blind replication)

Frozen 2026-11-14. Rules text only: no result, no rationale. A validator re-implements from this file
alone, without the builder's code. Where a number is not stated here, it is not part of the rule.
v1.1 changes no rule choice of v1 (`FINAL_RULES.md`, SHA-256 e0aa433a…). It (i) corrects the trading
calendar (A1) and the industry count (C4, C9), and (ii) states in words every point report 54 section 6
had to guess. Each change is marked [54-n], n = report 54's ambiguity number.

## A. Inputs

A1. Trading calendar [54-2]: the days on which the ASX traded. Rows of the price file on any other day are
    deleted before anything is computed. In the study file these are: 27, 28 Dec 1999; 25, 26 Dec 2000;
    1 Jan 2001; 29 Mar 2002; 14 Jun 2004; 27 Dec 2005; 1 Jan 2009; every Saturday and Sunday row
    (17 Mar 2018 and 17 rows from 6 Oct 2024 to 2 Feb 2025); 26 Dec 2024; 1 Jan 2025; 27 Jan 2025.
    A row on a day the ASX was open stays even if the vendor's prices equal the previous day's
    (31 Dec 1999, 7 Nov 2001, 29 Mar 2006, 2 Mar 2007) or most companies are missing (12 Nov 2002,
    7 Apr 2011). "Month-end" = the last trading day of a calendar month. "Trading day" below always means
    a day of this calendar.
A2. For each company (one continuous listing; a code change continues the same company; a gap of more
    than 200 calendar days with no trade starts a new company): daily close adjusted for splits and
    consolidations (not for dividends), and daily traded value = unadjusted close × volume. A day with no
    row has no close and a traded value of zero. [54-3] A row with a close and zero volume keeps its close
    (it counts as a traded day in B1 and can be traded on in D) and has a traded value of zero.
A3. `close10(d)` = the adjusted close of day d, or the most recent close within the previous 10 trading
    days if d has none; otherwise missing. `last(d)` = the most recent adjusted close on or before d,
    however old.
A4. Excluded securities: exchange-traded products (ETFs, managed funds, structured products), indices,
    and codes that are not three characters. Listed investment companies and property trusts are included.
A5. Industry group of a company [54-4]: the GICS industry group shown, in the official ASX
    listed-companies file dated 14 Nov 2026, against the code under which the company last traded in the
    price file. No code-change mapping is applied. Code not in the file, "Not Applic" or "Class Pend" =
    unknown. Consequence, accepted for the back-test and stated here so that it is reproduced: a company
    that has stopped trading and whose code is now used by a different company takes that company's group.
    (Live operation uses the group in the ASX file saved at the decision month; spec BW-04.)
A6. Index: S&P/ASX 200 price index (XJO) daily close, carried forward over days with no index row.

## B. Signals at a month-end t

Let W be the 252 trading days ending at t, and W⁻ the trading day before the first day of W.

B1. Universe: companies with a close on at least 200 days of W, ranked by the median of daily traded
    value over the 252 days of W (largest first). [54-5] Equal medians: alphabetical order of the company
    identifier (code, then listing number), which is the column order of the price file. The first 300
    are the universe; a company's position in the full order is its traded-value rank.
B2. For each universe company, with ME(j) the month-end j months before t and ME(0) = t:
    - s1 = close10(ME(1)) ÷ close10(ME(12)) − 1
    - s2 = close10(t) ÷ close10(ME(6)) − 1
    - s3 = close10(t) ÷ (highest actual close in W)
    - s4 [54-1] = −(sample standard deviation, divisor n − 1, of the daily log returns DATED in W). The
      log return dated d is ln(close(d) ÷ close(previous trading day)) and exists only if both days have an
      actual close. There are at most 252 of them: the return dated on the first day of W uses the close
      of W⁻. At least 200 are required.
B3. Percentile of a signal = its rank among the universe companies that have that signal (smallest = 1,
    ties share the average rank) ÷ the number that have it.
B4. Score = the mean of the four percentiles. A company missing any of the four has no score.
B5. Score order: highest score first; equal scores in traded-value-rank order. Score rank 1 = best.
B6. A company is buy-eligible at t if it has a score, close10(t) ≥ A$0.50, and its median daily traded
    value (B1) ≥ 100 × T, where T is the target position value of C3. [54-6] The A$0.50 test uses the
    adjusted close as the file gives it (for a company that consolidated its shares after t this is not
    the price quoted on t).

## C. Decisions at each month-end t (in this order)

C1. Payouts. Any holding whose last close in the whole price file is 20 or more trading days before t is
    removed and paid in cash at that last close × f, with no brokerage and no spread. [54-8] "Whole file"
    means to the file's end (13 Nov 2026 for companies still listed, 31 May 2024 for the others): the
    back-test knows that a silent stock never trades again; a suspended stock that trades again later is
    kept and valued at its last close. [54-7] f: take the ASX delisting records whose code equals the code
    under which the company last traded and whose date lies from 30 calendar days before to 1,500
    calendar days after the company's last close; use the earliest such record. f = 0 if its reason
    contains (case-insensitive) any of: liquidat, administrat, receiver, wound, listing fee, deed of
    company, 17.12, 17.15, failure to pay, insolven. No such record, or no keyword: f = 1. (The record
    list ends in April 2020; a later failure is therefore paid at f = 1.) [54-9] A payout is a disposal
    of every lot for tax (F) and closes the position (G6).
C2. [54-10] NAV(t) = cash + Σ shares × last(t), struck after C1 and BEFORE any tax payment; this is the
    reported month-end NAV. At a June month-end the year's tax (F4) is then paid from cash, and the NAV
    used for n and T in C3 is recomputed after that payment.
C3. Review month-ends are the account's first month-end and every December month-end. At a review:
    n = min(30, max(4, floor(NAV ÷ 2,500))); T = NAV ÷ n. At other month-ends n is unchanged and
    T = NAV(t) ÷ n.
    Definitions used below [54-11]: a holding is "awaiting sale" from the month-end at which its full sale
    is decided (C5) until that sale executes or it is paid out (C1) — this covers a deferred sale (C6) and a
    sale carried because the stock is not trading (D1). A holding with only a trim pending (C7) is NOT
    awaiting sale. "Live holdings" = holdings not awaiting sale.
C4. Review — target list. Walk the companies in score order. Take a company if it is buy-eligible and
    fewer than ceil(0.25 × n) companies of its (known) industry group have already been taken into this
    list; companies of unknown industry group are never refused by this cap. Stop at n companies. (At a
    review the list is built from an empty count: existing holdings do not pre-fill the industry count.)
C5. Review — sells. Every live holding not in the target list is sold in full on E, the next trading day,
    except under C6. [54-11] A holding already awaiting sale at a review keeps its pending sale; it is
    neither kept nor re-bought even if it is in the target list, and its place stays empty until C9.
C6. Twelve-month deferral. For a holding sold under C5 that is in profit at t (shares × last(t) > the sum
    of the cost of its remaining lots): for each lot let q = the first trading day on or after E that is at
    least 367 calendar days after the lot's purchase date. If at least one lot has q later than E and not
    more than 31 calendar days after E, the whole holding is sold on the latest such q instead of E.
C7. Review — holdings that stay (live holdings in the target list). If value = shares × last(t) exceeds
    2 T by A$1,000 or more, sell floor((value − 2 T) ÷ last(t)) shares on E (a trim; carried like any sell
    under D1). Otherwise, if value < 0.75 T and T − value ≥ A$1,000, the holding is a top-up candidate for
    the amount T − value. Top-up candidates are ordered by value ÷ T, smallest first.
C8. Review — buys. Each target-list company not held (in any state) is a buy for the amount T, in score
    order.
C9. Other month-ends — vacancies. If the number of live holdings is below n, walk the companies in score
    order and take those that are buy-eligible, not held in any state, and allowed by the industry cap,
    until the vacancies are filled. The cap count starts from the live holdings: every live holding with a
    known industry group counts, whether or not it is still in the universe. Each company taken is a buy
    for the amount T. No sale and no top-up is decided at a non-review month-end.
C10. There is no stop-loss, no trend exit, no market-regime rule and no other sell rule.

## D. Execution

D1. Sells execute at the close of their day (E, or the deferred day of C6). A sell for a stock with no
    close that day is carried to the next day it has one; if it never trades again it is left to C1.
D2. [54-12] Attempt days for buys: E, and any later trading day on which at least one sell executes, up to
    and including the next month-end; buys and top-ups still unfilled when the next month-end's decisions
    are made lapse. On an attempt day, after that day's sells, each open buy is processed once, in order:
    (i) cash test first: a = min(A, free cash). If a < max(A$1,000, 0.5 × A) the buy waits for the next
    attempt day; a waiting buy does not block the buys after it.
    (ii) otherwise, if the stock has no close that day, the buy is dropped (not retried);
    (iii) otherwise buy s = floor((a − brokerage(a)) ÷ (close × (1 + h))) whole shares at that day's
    close; if s = 0 the buy is dropped. Cash paid = s × close × (1 + h) + brokerage(s × close).
D3. [54-13] Top-ups are attempted once, all together and in C7's order, on the first attempt day at the
    end of which no buy is waiting (after that day's buys): a = min(amount, free cash); executed if
    a ≥ A$1,000 and the holding is still live, sized and paid as in D2 (iii); a top-up whose stock has no
    close that day, or with a < A$1,000, is dropped. Top-ups never wait and lapse at the next month-end.
D4. Free cash = cash − tax reserved (F4). Idle cash earns nothing. Whole shares only.
D5. Lots are sold oldest first.
D6. Order within a day: carried and scheduled sells; buys; top-ups; then, if the day is a month-end, the
    month-end decisions of section C (which take effect from the next trading day).

## E. Costs (evaluation convention)

E1. Brokerage per order = max(A$6.60, 0.088% of order value).
E2. Half-spread h per side = max(base, 0.5 × tick ÷ price); base = 0.10% if the company's traded-value
    rank is 1–100, 0.25% if 101–300, 0.50% otherwise (including a company with no rank). [54-14] The rank
    is that of the most recent month-end strictly before the trade day (a trade on E uses the month-end
    just decided; a trade that falls on a month-end uses the previous month-end's rank); the final
    liquidation (G1) uses the end date's own rank when the end date is a month-end. Price = the adjusted
    close of the trade; tick = A$0.001 below A$0.10, A$0.005 below A$2.00, else A$0.01, tested on that
    adjusted price. A buy pays shares × close × (1 + h) + brokerage; a sell receives
    shares × close × (1 − h) − brokerage, not less than zero.

## F. Tax (evaluation convention, approximate)

F1. Financial year = July to June; the June month-end closes the year.
F2. A lot's gain = its share of net proceeds − its cost (cost includes spread and brokerage). A gain is
    long-term if sale date − purchase date ≥ 367 calendar days. A payout (C1) is a sale at its payout value.
F3. Year's net: losses of the year plus losses carried forward are set first against short-term gains, then
    against long-term gains. Taxable = remaining short-term gains + remaining long-term gains × (1 − d);
    regime A: d = 0.5; regime B: d = 0. Tax = 32% × taxable. Unused losses carry forward.
F4. Tax reserved at any time = the tax that would be due if the year ended now. Tax is paid from cash at the
    June month-end (C2) and at the final liquidation. Dividends and franking are ignored.

## G. Start, end, comparator and reported measures (evaluation convention) [54-15, 54-16]

G1. The account starts as cash at a month-end, which is a review (C3). At the end date every holding is
    sold at last(end) with E1–E2 costs (a holding that never trades again is paid out as in C1), then F4.
G2. Periods: development 29 Dec 2000 – 31 Dec 2015; unseen 31 Dec 2015 – 31 May 2024; whole
    29 Dec 2000 – 31 May 2024. Each is ONE separate account started in cash; "whole" is one continuous
    account, not the two others joined.
G3. Index comparator: the index is bought once at the close of the trading day after the start month-end
    (brokerage E1, half-spread 0.03%) and sold at the end date (same costs); tax on the gain at
    32% × (1 − d). Its month-end NAV = units × index close; its NAV at the start month-end = the capital.
G4. CAGR = (final cash after G1 ÷ starting capital)^(1 ÷ years) − 1, years = calendar days ÷ 365.25.
    "Before costs" = a separate run with E1 and E2 set to zero (the index too). "After costs" = E on,
    tax off. "After tax A/B" = E on and F on with regime A/B.
G5. Monthly return = NAV(month-end) ÷ NAV(previous month-end) − 1 from the after-costs, tax-off run (the
    last month uses NAV before the final liquidation). Monthly excess = monthly return − the XJO price
    change over the same month-ends. Annualised excess = 12 × mean. t = mean ÷ (sample s.d. ÷ √months).
    Maximum drawdown = the lowest value of NAV ÷ (highest earlier-or-same month-end NAV) − 1 on that run.
    Turnover a year = value of all shares sold (including payouts; the final liquidation of holdings that
    still trade is not counted) ÷ the mean month-end NAV ÷ years. Trades = executed buy and sell orders (payouts and the final liquidation not
    counted).
G6. A position = one continuous holding of a company from its first buy to the day its share count returns
    to zero (top-ups and trims are part of it). Return = total net proceeds ÷ total cost − 1. It "beat the
    index" if that return > XJO(exit day) ÷ XJO(entry day) − 1. "Doubled" = return ≥ +100%; "lost more
    than x%" = return < −x%.
G7. Random-portfolio control: the same account with B4's score replaced, at every month-end, by an
    independent uniform random number for each company that has a score (companies without a score stay
    unscored); everything else unchanged; 200 runs per size and period. Percentile = share of runs whose
    after-costs CAGR is below the engine's.
G8. Deflated Sharpe ratio: Bailey and López de Prado (2014) on the monthly excess series of G5, number of
    trials N as stated beside each figure, cross-trial variance = variance of the yearly Sharpe ratios of
    report 51's 16 models ÷ 12.

## H. What the validator checks, and the builder's files [54-17]

For a A$25,000 and a A$100,000 account over the development and the unseen period (four accounts), the
builder supplies in `out/validator/` (company identifiers as in the price file):
- `holdings_<size>_<period>.csv`: for every month-end, the companies held at the close of the next trading
  day (after that day's trades), including holdings awaiting sale;
- `trades_<size>_<period>.csv`: every buy, sell and payout: date, company, shares, adjusted price, cash;
- `nav_<size>_<period>.csv`: month-end NAV (C2), cash, and the index NAV (G3);
- `positions_<size>_<period>.csv`: every closed position (G6);
- `summary_<size>_<period>.json`: CAGR before costs, after costs, after tax A and B; index CAGR; drawdown.
Any difference in a holdings list is a finding to be explained in writing by reference to this text, not
by reading the builder's code.
