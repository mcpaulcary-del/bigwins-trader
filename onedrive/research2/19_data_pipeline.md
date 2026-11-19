# Wave 3: data pipeline design for the ASX end-of-day system (2026-11-13)

**Evidence caveat.** WebFetch could not resolve hosts, so I used curl through the proxy. I read these directly: eodhd.com, norgatedata.com, ibkrguides.com, asx.com.au, rba.gov.au, pypi.org, quantconnect.com and raw.githubusercontent.com (pysystemtrade). The proxy blocked stooq.com, twelvedata.com, marketstack.com, help.yahoo.com, msci.com, spglobal.com, perthmint.com, ato.gov.au, docs.rs, alphavantage.co and tiingo.com; claims about those rest on search snippets only and are tagged down.

Tags: [2+] = two independent sources; [1] = one source (the vendor's own page counts as one); [unverified] = not confirmed.

## 1. Daily closes going forward

Three findings change the design:

- **EODHD is strictly single-person, but lets you keep the data.**
  - Sharing: "Can several people use one API key or one subscription? No. A personal subscription is for one person." Not allowed: "Sharing your account or API key with anyone, including family members, friends or groups." Personal use applies "as long as the data and results are not provided to anyone else." https://eodhd.com/help/personal-use [1]
  - Retention: "May I subscribe for one month, download a large historical dataset, and keep using it after cancelling? Yes." and "The Terms contain no deletion requirement and no deadline." https://eodhd.com/help/storage [1]
  - Cross-checking: "Can I compare your data with another provider's data for quality checks? Yes, for your own quality checks, as long as neither dataset is redistributed." [1]
  - Price: All World "$ 19.99 /mo." or "$ 199.00 /year"; free plan "20 API calls per day and 1 year of history for end-of-day prices, splits and dividends"; "1 for EOD/live… 100+ for bulk". https://eodhd.com/pricing, https://eodhd.com/help/plans [1]
  - No exchange fees on personal plans: "there are no additional exchange or non-display fees on personal plans." [1]
- **Norgate cannot be your point-in-time archive.**
  - "Data that has been exported from the database, or extracted from it, must be deleted after a subscription has expired… This includes raw exports, normalized rows, point-in-time snapshots, events, backups and any metadata." Derived results "may be retained". https://norgatedata.com/faq.php [1]
  - "At present, our data service can only be licensed for personal use by individuals. There is no alternative business/commercial licensing." [1]
  - "The 'Norgate Data Updater' application (NDU) is a Windows-only application." https://pypi.org/project/norgatedata/ [1]
  - ASX packages (A$, ex-GST): Silver 148.50/270, Gold 198/360, Platinum 346.50/630 for 6/12 months; Platinum goes "Back to 1992" and includes delisted securities. https://norgatedata.com/stockmarketpackages.php [1]
- **IBKR Flex does carry closing prices, but only for held positions.**
  - Open Positions: "Mark Price: The closing price of the position as of the report date." https://www.ibkrguides.com/reportingreference/reportguide/open%20positionsfq.htm
  - The Mark-to-Market Performance Summary has "Previous Close Price" and "Close Price: Today's closing price of the position"; Prior Period Positions has "Price: The previous day's price."
  - The third-party ib-flex parser documents the same `markPrice` field (https://docs.rs/ib-flex/0.1.7/ib_flex/types/activity/struct.Position.html, snippet only). [2+]
  - Timing: Activity Flex data is "only updated once daily at close of business", so fetch the next morning. https://www.interactivebrokers.com/docs/web-api/web-api-v-1-0-documentation/flex-web-service [1, snippet]
  - It is a free second source for raw closes of anything held. A permanent one-unit holding in each universe ETF would keep coverage while a sleeve is in cash (my design suggestion). Whether Mark Price equals the official ASX closing-auction price is [unverified]; test it for 20 days.

| Source | ASX | Adjusted / distributions | Licence | Cost | Verdict |
|---|---|---|---|---|---|
| EODHD | Yes (XASX); "30+ years" | Raw OHLC plus `adjusted_close` "adjusted for both splits and dividends"; dividends "with franking credits & DRP details" (https://eodhd.com/asx-data) [1] | One person; retention allowed; team use needs a commercial quote | US$19.99/mo, US$199/yr, or free at 20 calls/day | Primary |
| IBKR Flex | Held positions only | Raw close; distributions appear as cash transactions | Your own account data | Free | Cross-check |
| Norgate | Full, including delisted | TOTALRETURN / CAPITAL / NONE adjustment modes | One individual; delete on expiry; Windows | A$270–630/yr | Backtest rental only |
| Twelve Data | Yes, 20-minute delayed and end-of-day | Not checked | Individual plans personal; ASX "from $120/year for internal usage", from Pro tier | Higher | [1, snippets conflict] Not needed |
| Marketstack | ASX listed in reviews | Not checked | Free tier reportedly non-commercial | Free at 100 requests/month | [1] Quota too small |
| Alpha Vantage | `.AX` support unconfirmed | Adjusted daily endpoint is premium | Not checked | 25 requests/day free | [1] Reject |
| Tiingo | No ASX found ("US & Chinese markets") | Not checked | Not checked | Not checked | [1] US phase only |
| Massive (Polygon) | US only | Not checked | Individual / non-professional per third party | Free: end-of-day, 5 calls/min, 2 years | [1] US phase candidate |
| Stooq | Not checked | Not checked | No official terms found | Free, manual key | Reject for automation |
| Yahoo / yfinance | Yes | Adjusted close per "CRSP standards" (https://help.yahoo.com/kb/SLN28256.html) | "intended for personal use only"; yfinance "not affiliated, endorsed, or vetted by Yahoo" | Free | [2+, snippets] Not for production |
| ASX own products | Not researched this wave | Not researched | Not researched | Not researched | [unverified] Likely vendor-priced |

Stooq detail: "As March 2026, Stooq requires an API key for data downloads" (https://github.com/pydata/pandas-datareader/issues/1012), and the key comes from a captcha page per a Qiita tutorial (https://qiita.com/katafuchix/items/c74793e5041e1b5e3051). [2+, both secondary, snippets]

**Recommendation for one user**
- Primary: EODHD. Buy one paid month for the full-history download, then drop to the free plan (20 calls/day covers about 15 tickers) if it serves `.AU` symbols; that is [unverified], so test before paying. Otherwise take the US$199 yearly plan.
- Cross-check: IBKR Flex Mark Price next morning, the IBKR snapshot at order time, and issuer distribution announcements for amounts.
- FX: RBA F11.1. It is CC BY 4.0 ("may be reproduced…", https://www.rba.gov.au/copyright/), but the RBA says "These data should not be relied upon for any regulatory or commercial purposes" (https://www.rba.gov.au/statistics/frequency/exchange-rates.html). [1]

**Recommendation for up to five users**
- An EODHD personal plan is not compliant if other users see the data or results derived from it.
- Option A, the cheapest: only the owner's processes touch vendor data and signals; the other users see only IBKR-sourced account data (positions, orders, P&L). Get EODHD sales to confirm this in writing, since "results… not provided to anyone else" is broad.
- Option B: an EODHD commercial or internal-team quote. Their page says "Commercial terms depend on the actual use case; a personal-plan price is not a quote for those rights" and that they "report all commercial users of exchange data to the relevant exchanges" (https://eodhd.com/help/commercial, https://eodhd.com/financial-apis/commercial-vs-personal-license-use). [1]
- Norgate cannot be licensed for this at all.

## 2. Total-return construction

- **Core formula.** TR_t = TR_{t-1} × (P_t + D_t) / P_{t-1}, with D_t the cash distribution per unit on its ex-date and P the raw close. This matches Yahoo's backward adjustment, whose "dividend multiplier is 1 − (0.08 / 24.96)" in the help-page example. [1, snippet]
- **Store raw, compute your own.** EODHD's "OHLC fields are raw… The adjusted_close field is adjusted for both splits and dividends. The volume field is adjusted for splits only" (https://eodhd.com/financial-apis/api-for-historical-data-and-volumes). [1] Keep the vendor's adjusted close only as a comparison series.
- **Vendor differences.**
  - Norgate offers `NONE`, `CAPITAL`, `CAPITALSPECIAL` and `TOTALRETURN` (default). [1]
  - Yahoo reportedly adjusts only the close for dividends, and a user thread disputes its dividend handling. [1, forum]
  - LEAN stores raw prices and applies factor files (price factor, split factor) at read time, with delistings and renames in map files (https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/quantconnect/us-equity-security-master, plus forum 1411). [2+, same organisation]
- **Franking.** Credits are not cash: a Vanguard notice lists "cash distribution (cents per unit) 128.813679" and "franking credits 48.748494" separately, and VAS franking ran roughly 64–88% across FY22–FY24 (fool.com.au, InvestSMART). [2+, snippets]
  - Keep two series: `tr_net` (cash only) for signals, and `tr_gross` (D + franking credit × the owner's realisable rate) for after-tax evaluation only.
  - `tr_net` is the one comparable to vendors; that it also matches standard accumulation indices is [unverified].
  - S&P publishes separate Franking Credit Adjusted indices (mondovisione.com, professionalplanner.com.au). [2+, snippets]
- **AMIT cost-base adjustments.** These are tax-ledger items, not price events. "Your cost base is adjusted at the end of each income year by the 'AMIT cost base net amount'", shown on the AMMA or annual tax statement (ATO "cost base adjustments for AMIT members"; https://help.sharesight.com/au/au-amit-tax-components/). [2+, snippets]
  - Keep them out of the total-return series and in a per-parcel tax table.
  - June distributions are announced as estimates and then finalised; store both with a status.
- **Tests for bad adjustments.**
  - Own total return versus vendor adjusted close: daily return gap above 5 bp on a non-ex-date, or above 25 bp on an ex-date, raises a flag.
  - The adjusted/raw ratio may change only on ex or split dates, and must not fall as dates advance.
  - The implied dividend, (1 − factor ratio) × prior close, must be within 1% of the issuer-announced amount.
  - Count distributions per year against the issuer's schedule (VAS should have four).
  - Any absolute daily return above 15% on an ETF with no corporate-action record is quarantined.
  - Yearly total return must be within 0.5% of the issuer's published fund return.
  - Re-download the full history monthly and diff it to catch silent restatements.

## 3. Point-in-time storage and data quality

- **Principles.**
  - Append-only and bitemporal: every row carries the trade date and the fetch time; nothing is updated in place.
  - This mirrors LEAN's raw-plus-factor design and CRSP's permanent identifiers and delisting returns (the CRSP identifier detail is from memory, [unverified]).
  - EODHD explicitly permits keeping "source values, tickers, dates, retrieval timestamps, hashes… also after your subscription ends". [1]
- **Schema.**
  - `instrument`: internal id, symbol history, exchange, currency, issuer, list date, delist date, delist reason, final payout.
  - `raw_bar`: instrument id, trade date, source, OHLCV, fetch time, file hash.
  - `distribution`: ex/record/pay dates, cash amount, franking credit, components, status (estimated or final), source, fetch time.
  - `corp_action`, `calendar`, `fx`, `qc_event`.
  - `tr_series`: derived, stamped with a build id and the as-of date of its inputs.
- **Survivorship.**
  - Keep closed ETFs with their wind-up payout as the last return.
  - Australian ETF closures are real: "since 2010, 17 ETFs have been delisted… approximately 1% per annum" (https://firstlinks.com.au/etfs-survival-fittest); Betashares closed funds in December 2024 (investordaily.com.au). [2+, snippets]
  - Missing delisting returns bias results (Shumway 1997, J. Finance 52(1); https://ideas.repec.org/a/bla/jfinan/v52y1997i1p327-40.html, https://scholarsarchive.byu.edu/facpub/9278). [2+]
  - Norgate marks delisted symbols with a suffix, "e.g. ONE-200105.au". [1]
- **Spike rule.** In pysystemtrade, "If any spikes are found… it will not be written. The system will attempt to email the user", with spikes defined as "a large multiple of the average absolute daily change" (`max_price_spike`, shown at 6 and 8) (https://github.com/robcarver17/pysystemtrade/blob/master/docs/production.md). [1] Adopt the same quarantine-not-write behaviour.
- **Calendar.** Use ASX's published trading calendar for 2026 and 2027, entered by hand each year (https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours/trading-calendar). [1] RBA rates are "published daily except on public and bank holidays observed in New South Wales", so the FX calendar differs from the ASX one. [1]
- **Alerting.** Three levels: INFO to the log, WARN by email or push, BLOCK when the signal run refuses to trade. Add a dead-man heartbeat so that a silent pipeline also alerts. A BLOCK needs the owner's override, which is recorded as a `qc_event`.

## 4. Backtest history

| Sleeve | Longest series | Legal, cheap route |
|---|---|---|
| ASX 200 accumulation | Premium Data/Norgate history "back to 1992", "includes All Ordinaries and S&P/ASX 200 Accumulation indices, plus simulated data before index launch dates" (https://premiumdata.net/products/premiumdata/asxhistorical.php) [1, snippet] | Six months of Norgate Platinum (A$346.50): run the backtests, keep only derived results, delete the data on expiry. Retainable alternative: STW/VAS total return from EODHD. Market Index offers CSV with a free login [1, snippet]; its terms were not read. |
| MSCI World ex-Australia (AUD) | Index "launched on Dec 31, 1969" (MSCI factsheet) [1, snippet] | MSCI's end-of-day index search page for monthly net AUD levels; availability and terms [unverified, blocked]. Retainable proxy: VGS/VGAD via EODHD. |
| AusBond Composite 0+ | Series "since September 1989" (FIIG); Bloomberg ticker BACM0 (Betashares) [1, snippets] | No free licensed download found. Proxies: VAF/IAF total return; before that, a duration model on RBA F2 yields (CC BY), labelled as synthetic. |
| Gold in AUD | Norgate AU Extras list "Gold/Australian Dollar Spot Rate" and "Gold - London PM Fix" [1]; Perth Mint CSVs "1968–2015" and later [1, snippet] | Perth Mint CSV (terms unread), or USD gold × RBA AUD/USD. Avoid raw LBMA data: "a licence is required from IBA" [1, snippet]. |

ETF inception dates and index start dates other than those quoted are [unverified].

## 5. Spec-ready decisions

**Sources and licences**
1. Prices and distributions: EODHD personal plan, owner only, with the key on the owner's machine. Store raw responses.
2. Second source: IBKR Activity Flex (Open Positions Mark Price, MTM Close Price, cash transactions) for raw closes and distribution cash.
3. FX: RBA F11.1, CC BY with attribution.
4. Calendar: ASX trading calendar, entered by hand each year.
5. Distribution truth: issuer announcements, entered quarterly.
6. Excluded from production: Yahoo, Stooq, any asx.com.au scraping, and Norgate as an archive.
7. Other users see only IBKR-derived account views until EODHD confirms otherwise in writing.

**Schedule (Sydney time)**
- 16:10–16:11: closing auction ("The Closing Single Price Auction takes place between 16:10:00 (randomised 30 seconds) to 16:11:00", https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours). [1]
- 19:30: fetch EODHD and RBA. EODHD's ASX publication time is [unverified]; its API allowance "resets at midnight GMT".
- 21:30: retry.
- 07:30 next day: pull Flex and reconcile.
- 08:00: validation verdict.
- Month-end signals are computed only after a clean verdict; orders go the next session using the IBKR snapshot.
- Sunday: full-history re-download and diff.

**Validation thresholds (my proposed starting values; tune after 60 days)**
- EODHD close versus Flex mark: up to 0.1% or one tick is fine; 0.1–0.5% is a WARN; above 0.5% is a BLOCK.
- Missing bar on an ASX trading day: retry, then WARN at 21:30, then BLOCK if still missing at 08:00.
- Stale data: an identical close with zero volume for three or more sessions is a WARN.
- Spike: an absolute return above 8× the 60-day mean absolute change, or above 15%, is quarantined.
- Restatement: any change to a stored raw close is a WARN; more than five rows or more than 0.5% is a BLOCK.
- Total-return checks as in section 2.
- FX: an RBA move above 3% in a day is a WARN.
- Order time: an IBKR snapshot more than 2% from the last validated close holds the order.

**Storage layout**
- `data/raw/{source}/{fetch_date}/…json.gz` plus a sha256 manifest, immutable.
- `data/db/market.duckdb` (or SQLite) with the section 3 tables.
- `data/derived/{build_id}/tr_*.parquet`.
- `data/tax/` for AMIT and franking records.
- Nightly encrypted backup; EODHD permits "encrypted backups". [1]
- Any Norgate data goes in a separate `rental/` tree with a deletion date.

**Verify before buying**
- EODHD:
  - Does the free plan serve `.AU` end-of-day prices and dividends?
  - Do distribution amounts and ex-dates for VAS, VGS, VAF, IVV, A200 and BGBL match issuer figures over three years?
  - Are delisted ASX ETFs included?
  - What time is ASX data published?
  - Written answer on whether showing IBKR-only account views to other users is acceptable, and a commercial quote if not.
- IBKR: run a 20-day trial of Mark Price against the official close, and confirm the Flex token lifetime and rate limits. [unverified]
- Norgate: confirm the 6-month Platinum covers the accumulation indices and AUD gold, and the exact derived-data definition in the licence agreement.
- MSCI, S&P, Perth Mint, Market Index: read the terms of use for stored personal copies.

To re-check the blocked hosts directly, the session's network settings need stooq.com, twelvedata.com, marketstack.com, help.yahoo.com, msci.com, spglobal.com, perthmint.com, ato.gov.au, docs.rs, alphavantage.co and tiingo.com allowed. Fetched page copies are in `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/dl/`.