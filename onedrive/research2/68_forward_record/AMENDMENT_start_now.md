# Amendment to report 68 — paper record starts now (decided Mon 16 Nov 2026, ~22:40 UTC)

PAPER ONLY. No real money, no broker orders. The AI never places trades. Rules: v1.3 (`67_FINAL_RULES_v1.3.md`, SHA-256 b38abcd7…54b0), unchanged except as written here.

Written and hashed BEFORE any target list was computed and BEFORE the Tue 17 Nov 2026 ASX close (05:10 UTC 17 Nov) existed.

## 1. Owner directive (verbatim)
"Paper record to be started ASAP."
Added later the same evening: "The cloud server should also be looking every few hours, not daily or weekly."

## 2. What changes
1. **Start date.** The H82 books, the controls and the comparators no longer start at the month-end of Thu 31 Dec 2026. They start at **decision day Mon 16 Nov 2026** (the last ASX close available when this was written).
2. **First review.** Rules C3/G1 say the account starts "as cash at a month-end, which is a review" and that "the account's first month-end" is a review. Here "the account's first month-end" is read as **"the start decision day" (16 Nov 2026)**. The B-signals at a non-month-end day follow B2's interim reading (ME(1) = the latest month-end before t = 30 Oct 2026), exactly as the 13 Nov snapshot already did.
3. **Fills.** Trades are booked at the close of the next trading day, **Tue 17 Nov 2026** (D1/D2 with E = 17 Nov; costs E1/E2; cost rank from the decision-day table; Q5).
4. **Afterwards nothing changes.** Mon 30 Nov 2026 is an ordinary month-end (C1, C2, C9). Thu 31 Dec 2026 is the normal December review (C3–C8), traded Mon 4 Jan 2027. All later dates as report 68 §2.2.
5. **Data-block fallback (Q4), fixed before looking at lists.** If on the download of 16 Nov `AXJO.INDX` has no 16 Nov row, or fewer than 285 of the 300 universe companies have a 16 Nov close, then the decision day is **Fri 13 Nov 2026** and the fill day is **Mon 16 Nov 2026** (its close is already known, but it is the close of the trading day after 13 Nov and no choice depends on it — the lists are fixed by 13 Nov data only). The outcome of this test is recorded in the ledger entry that opens the account.

## 3. Books (report 68 §2.4, amended)
| Book | Capital | Contributions |
|---|---|---|
| H82 lifecycle (owner's real size) | A$5,000 | A$500 credited as cash at each month-end from Mon 30 Nov 2026 (before C2's NAV, so it counts in T) |
| H82 small | A$25,000 | none |
| H82 main | A$100,000 | none |
| H83 random controls | 200 portfolios, seeds 1–200, at A$25,000 and A$100,000 (G7: score replaced at every decision by a uniform random number per scored company, numpy default_rng(seed), drawn in score-table order) | none |
| H83 momentum control | 12-1 momentum (s1 percentile as the score), n = 10 fixed, at A$25,000 and A$100,000, same machine otherwise | none |
| Comparator 1 | A200 total return, same dollars and contribution dates, J3 with τ = 0 | as the book |
| Comparator 2 | Owner's plan: 40% A200 / 60% BGBL, same dollars and contribution dates | as the book |
| Placeholder | **Improved challenger engine (report 73, in progress).** Added only after its rules are frozen and hashed, with its own start date and clock. No rules are assumed here. | — |

**How contributions are used (lifecycle book only, rule-bound, no discretion).** Contributions are cash. Cash is spent only by the v1.3 machinery: C9 vacancy buys at non-review month-ends (vacancy = live holdings < n), C8 buys and C7 top-ups at December reviews, and D2 buy attempts. n = min(30, max(4, floor(NAV ÷ 2,500))) is recomputed only at reviews; at A$5,000 n = 4 and T = NAV ÷ 4. Cash that no rule spends stays as cash (earns nothing, D4). This can leave cash idle for months; that is the rule's real behaviour at this size and is reported, not fixed.

**Comparator mechanics.** A200 TR = EODHD `A200.AU` close plus distributions on ex-dates (EODHD `div`, cash reinvested on the ex-date) — **flagged "EODHD proxy"**; the Betashares issuer index is used as a cross-check where the owner's saved file covers the date (the system may not fetch issuer sites daily). BGBL likewise. Each comparator buys at the close of the fill day: value = (S − brokerage(S)) ÷ 1.0003, then follows the TR series; each contribution buys the same way at the close of the trading day after its month-end (40/60 split for comparator 2, one brokerage per fund). Fractional units (J3 convention).

**Tax.** The daily books run the v1.3 "after costs" convention (E on, F off; G4). Every lot keeps its date and cost so tax A/B can be estimated in the scorecard; tax reserve does not restrict buys in these books. Stated so nobody reads the NAV as after tax.

## 4. Intraday looking (owner's second directive)
`paper_intraday.py` pulls EODHD delayed quotes every ~2 hours in ASX hours, archives them, marks every book to the latest quote (labelled "indicative, delayed") and writes alerts. **It makes no trading decision.** Under v1.3 every decision is made on closing prices only; intraday rules are untested. The archive exists so that a future engine (e.g. report 73), if it freezes intraday rules in advance, has its own data.

## 5. Why this deviation is harmless to honesty
- It uses forward data only: everything after 16 Nov 2026 is unseen by every rule and every agent.
- It was decided and hashed before the 17 Nov close was known, and before any list was computed under it.
- No rule value changes; only the calendar start moves earlier by 45 days, and one reading ("first month-end" → "start decision day") is fixed in writing.
- The cost is a small loss of comparability with the back-test convention (accounts there start at month-ends). It is recorded as a deviation, not a new trial. Trial count unchanged (402).
