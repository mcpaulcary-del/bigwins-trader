# Amendment note — intraday looking (written Mon 16 Nov 2026, before the Tue 17 Nov ASX open)

PAPER ONLY. No real money, no broker orders. The AI never places trades.

## Owner directive (verbatim)
"The cloud server should also be looking every few hours not daily or weekly."

## What is added
`bigwins_forward/code/paper_intraday.py`, run about every 2 hours in ASX hours (10:00–16:10 Sydney = 23:00–05:10 UTC under AEDT; 00:00–06:10 UTC under AEST from 5 Apr 2027).

It does only four things:
1. Pulls EODHD **delayed** quotes (`real-time` end-point, batched) for the held names, names with pending paper orders, A200, BGBL and the 300-company universe of the latest decision. (The intraday-history end-point returns Forbidden on this plan.)
2. Archives every quote in `bigwins_forward/out/intraday/YYYY-MM-DD.csv.gz` (append-only).
3. Marks every paper book and comparator to the latest quote in `paper/INTRADAY.md`, labelled **"indicative, delayed"**.
4. Writes alerts (`paper/alerts.md` append-only, `paper/alerts_latest.md`): a holding moving ±8% on the day; a held or pending name with no trade / zero volume by midday (possible halt); a +20% jump in a held, pending or universe name (possible takeover or scheme); a universe name entering or leaving the top-30 or top-90 score band when s2 and s3 are recomputed on the latest quote (s1 and s4 kept at the decision day — indicative only); broken data (missing, stale, non-positive, or >60% away from the last close).

## What is NOT changed
- **No trading decision is made intraday.** Rules v1.3 make every decision on closing prices (B, C at decision days; D fills at the close). Intraday rules are untested and are not part of v1.3.
- No alert changes a book, an order, n, T or a list. An alert is information for the owner (for example: read the company's announcement).
- The daily job (`paper_daily.py`) remains the only writer of the books and the ledger.

## Why it is harmless to honesty
Quotes are archived, not used. If a future engine (e.g. report 73's challenger) wants intraday rules, it must freeze them in advance and is then scored on data gathered after its freeze.
