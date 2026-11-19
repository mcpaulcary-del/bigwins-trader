# 58 — ASX company research database: what was built, what it covers, and what it cannot be used for

Date: 2026-11-14. Status: builder's report, not independently replicated. Private research use only; general information, not financial advice.
Database, code and raw downloads: `scratchpad/company_db/` (`db/asx_company.duckdb`, `code/`, `raw/`, `out/`). Companion: report 57 (paid point-in-time vendors) and report 61 (gap review, whose additions are in sections 6 and 8).

## 0. Answer first

| Question | Answer |
|---|---|
| What exists now? | One DuckDB file (881 MB, 19 tables). Daily prices for 6,057 company entities from 2 Jan 1997 to 13 Nov 2026, delisted companies included. Financial statements, ratios, dividends, share counts and profiles for the 1,786 companies on the ASX today |
| How deep are the financials? | Six fiscal years, typically FY2021 to FY2026, plus half-years over the same span. 1,776 of 1,786 listed companies have at least one annual result; 1,636 (92%) have all six years. Nothing before fiscal 2020 is reachable without paying |
| Are they point-in-time? | **No.** The source gives no filing or release date. Every figure carries the flag "date of fiscal period end only - NOT point-in-time", the time it was fetched, and an assumed availability date (year end + 4 months; half-year end + 3 months) |
| Do they include delisted companies? | **No.** The source has no financial pages for companies that have left the ASX (19 of 25 tested had no page at all). Every vendor figure is flagged "survivors only, not for back-tests" |
| How much does that matter? | Of the 300 most-traded companies in December 2010, 56.3% are no longer listed and have no financials here; for December 2020 it is 21.7%. A test restricted to today's survivors overstated the next-12-month return of the top 300 by 3.8 points a year on average over 2000 to 2019 |
| Can quality (profitability, accruals, leverage) be back-tested with this? | **No.** Six years, survivors only, restated figures. Section 7 says exactly what can and cannot be tested |
| What is it good for today? | Screening current companies (section 6), a dated baseline for a forward paper test, and cross-checks on any paid data bought later |
| How does it become point-in-time? | By re-fetching on a schedule. The first dated snapshot is 14 Nov 2026. The build keeps only figures that are new or changed in each later snapshot and stamps them with that snapshot's date. `code/snapshot_monthly.sh` does this; no schedule has been set up (owner decision, section 8) |
| Permission problems | ASX's website terms forbid any automated access, so no asx.com.au content is in the database. stockanalysis.com permits AI agents that follow its robots.txt, but forbids using its data to train machine-learning models or to build a competing product. That limits what the learning engine (report 52) may do with this data |

## 1. What was built

`db/asx_company.duckdb` opens with DuckDB 1.x or 2.x (`duckdb.connect(path, read_only=True)`). The database's SHA-256 begins `5cf7c7f545e3d2b3`.

| Table | Rows | Contents |
|---|---|---|
| company | 6,057 | One row per company entity (a continuous price history, possibly across several ASX codes). 1997-2026, includes delisted. |
| company_code_history | 7,343 | Codes used by each entity with the dates each code has price rows. |
| name_changes | 2,605 | ASX code and name changes 2001-2020 as published by ASX, taken from the rs77 public repository (raw events, not all are linked to entities). |
| prices_daily | 9,725,260 | Daily prices per entity 1997-01-02 to 2026-11-13. Ordinary shares with 3-character codes; exchange-traded products and indices excluded (report 51 rules). |
| financials | 3,109,699 | Long table of financial statement items and vendor ratios. One vintage so far (fetched 2026-11-14). NOT point-in-time. |
| financial_items | 530 | Line-item ids and display titles. |
| financials_page_meta | 12,709 | One row per fetched financial page: currency, reporting frequency, how many periods the vendor holds in total (full_count) versus shown free. |
| dividends | 4,553 | Dividend history: latest 10 payments per company only (older rows are behind the vendor paywall). |
| shares_outstanding | 126,566 | Share counts from statements (period ends) and the current snapshot. |
| market_cap_history | 103,530 | Market capitalisation history as far as shown free: daily ~1 year, weekly ~6 months, monthly ~2 years (top 300 only), and at fiscal period ends from the ratios pages. |
| splits | 1,973 | Splits and consolidations: vendor last-split field, steps derived in report 51, and the report 51 price heuristic. |
| delistings | 4,570 | Official ASX removals Aug 2000 - Apr 2020 with reasons, plus inferred endings for entities whose prices stop without an official record. |
| statistics_snapshot | 172,050 | Current statistics page values (snapshot at fetch): shares, float, ownership, valuation, scores, next results date. |
| fundamentals_derived | 31,286 | Derived per company and period end: share-count history and 12-month net issuance, asset growth, accruals, cash and cash runway. Vendor-derived: survivors only. |
| quality_metrics | 10,362 | Quality metrics per company at six dates (Dec 2021-Dec 2025 and 14 Nov 2026) under the 4-month lag rule. Lagged, not point-in-time. |
| snapshot_log | 1 | One row per dated fetch (vintage) of stockanalysis pages. |
| macro | 24,044 | Context series: AUD/USD, TWI, yields, cash rate, commodity index (monthly from 1975) and RBA daily exchange rates 2023-2026. |
| fetch_manifest | 22,574 | Every HTTP request made for this database and for the copied report 51 downloads. |

Company entities by status: 1,786 listed today and in the vendor list; 7 still trading but not in the vendor's stock list (listed investment companies and trusts); 1,497 delisted with an official ASX record (Aug 2000 to Apr 2020); 2,454 whose prices end before May 2024 with no official record; 26 larger companies whose prices end between June 2024 and Nov 2026; 287 that were trading on 31 May 2024 and are not listed now, with the exact date unknown.

Build steps, all re-runnable with `python3 -I`:

1. `code/fetch_sa.py`, `fetch_px.py`, `fetch_extra.py`: polite sequential download, at most one request a second, every request logged with URL, UTC time and SHA-256 in `raw/manifest.tsv` (also table `fetch_manifest`).
2. `code/build_db.py`: parses the downloads as data only, loads report 51's price panel, links today's codes to the historical entities, writes the database.
3. `code/metrics.py`, `code/coverage.py`, `code/render_tables.py`, `code/build_report.py`: metrics, coverage tables and this report.

## 2. Sources and permission checks

| Source | Check made before use | Result | What was taken |
|---|---|---|---|
| stockanalysis.com | robots.txt and terms of use fetched 14 Nov 2026 (`raw/sa_meta/`) | robots.txt disallows only `/e/` and `/p/`. Terms: automated access is not allowed, but "this does not apply to search engines, AI agents, or other crawlers that follow our robots.txt file". The terms also forbid building "a competing database or product" and using the data "to train AI or machine learning models" | List of ASX stocks; per company: annual and half-year income statement, balance sheet, cash flow, ratios, profile, dividends, statistics; market-cap history for the largest 300; 5-year daily prices for codes report 51 had not fetched. 20,601 requests between 2026-11-14 08:27 and 2026-11-14 16:06 UTC, 2 of them not HTTP 200 (one endpoint guess that returned 404; one interrupted request, re-fetched) |
| asx.com.au | robots.txt and terms of use fetched | robots.txt allows crawling, but the terms prohibit "any spider, screen scraper, robot, other similar software" for any access. The stricter rule governs | **Nothing.** 9 requests were made while locating and reading the terms (including one copy of the listed-companies file fetched in the same batch as the terms). Those files were deleted unused; the log rows remain. The terms allow a person to save a copy through a browser for research, so the listed-companies file can be added by hand (`raw/asx/README_NOT_USED.txt`) |
| ASX delisting and name-change lists | Not fetched | Already held locally in the public `rs77/asx-historical-data` repository (report 51), covering Aug 2000 to Apr 2020 | 1,803 delisting records with reasons; 2,605 code or name changes |
| Report 51 price panel (`company_study`) | Local copy, unmodified, hashes in `raw/company_study/data_hashes.txt` | — | Daily prices 1997 to May 2024 for every 3-character ordinary share code, entity links, split fixes, bad-tick removal, extension to Nov 2026 for about 580 larger companies |
| RBA tables (`au_signals`) | Local copy | — | AUD/USD, trade-weighted index, yields, cash rate, commodity index (monthly from 1975); daily exchange rates 2023 to 2026 |
| ETF issuer pages (Vanguard, Betashares) | Not used | The database holds companies only; exchange-traded products are excluded by report 51's rule | — |

Things tried and not available: the vendor has no ASX delisted-company list (its delisted page is US only), and a screener endpoint guess returned 404 and was not pursued.

## 3. Coverage

### 3.1 Depth of the financials

- The free pages show the latest five fiscal years and ten half-years, plus one earlier year and two earlier half-years that the page carries for growth calculations (flagged `from_prior_block`, with the period end inferred). The vendor holds more history (typically 10 annual and about 22 half-year periods, field `full_count`), but it is behind its paywall and was not touched.
- 1,776 of 1,786 listed companies have annual financials; 10 have none. 1,636 have six annual periods; 140 have fewer, mostly recent listings.
- Half-year statements: 1,767 companies. Second halves are the vendor's full year minus first half, not separately reported figures.
- Statement currency: 1,588 companies report in AUD, 109 in USD, 79 in other currencies. Values are stored in the reporting currency; nothing is converted.
- 107 ASX lines are secondary listings of foreign companies (Rio Tinto, Newmont, ResMed, the New Zealand dual listings and others). The vendor keeps their financials under the primary listing; 100 were fetched from there and are marked in `source`.
- Delisted companies: 25 codes that were in the top 300 by traded value between 2019 and 2023 and are not in today's list were requested once each. 19 have no page; 5 redirect to the renamed successor (already in the list); 1 (Qube, removed July 2026) still has a page marked delisted. The vendor does not keep ASX companies after they leave.
- Line-item coverage, annual, among companies with financials:

| Statement | Item id | Title | Companies with the item | % of companies with financials |
|---|---|---|---|---|
| balance | assets | Total Assets | 1776 | 100.0 |
| balance | cashneq | Cash & Equivalents | 1776 | 100.0 |
| balance | equity | Shareholders' Equity | 1776 | 100.0 |
| balance | sharesOutTotalCommon | Total Common Shares Outstanding | 1775 | 99.9 |
| balance | debt | Total Debt | 1591 | 89.6 |
| cashflow | ncfo | Operating Cash Flow | 1775 | 99.9 |
| cashflow | fcf | Free Cash Flow | 1693 | 95.3 |
| cashflow | capex | Capital Expenditures | 1672 | 94.1 |
| income | netinc | Net Income | 1776 | 100.0 |
| income | epsdil | EPS (Diluted) | 1773 | 99.8 |
| income | opinc | Operating Income | 1700 | 95.7 |
| income | fcf | Free Cash Flow | 1693 | 95.3 |
| income | ebitda | EBITDA | 1672 | 94.1 |
| income | gp | Gross Profit | 1491 | 84.0 |
| income | revenue | Revenue | 1490 | 83.9 |
| income | dps | Dividend Per Share | 492 | 27.7 |
| ratios | marketcap | Market Capitalization | 1751 | 98.6 |
| ratios | pb | PB Ratio | 1751 | 98.6 |
| ratios | roe | Return on Equity (ROE) | 1742 | 98.1 |
| ratios | debtequity | Debt / Equity Ratio | 1556 | 87.6 |
| ratios | pe | PE Ratio | 845 | 47.6 |

Revenue and gross profit are missing for about one company in six, mostly explorers with no revenue, banks and insurers. The price-earnings ratio exists for under half because most small companies make losses.

### 3.2 The 300 most-traded companies, year by year

The universe is report 51's: the 300 companies with the highest median daily traded value at each December (October for 2026). "Gone" means not listed in November 2026.

| Year (Dec) | Companies | Still listed Nov 2026 | Gone | Gone % | Have any financials in the database | Have financials for that year | Have a result usable on that date (4-month rule) |
|---|---|---|---|---|---|---|---|
| 2000 | 300 | 65 | 235 | 78.3 | 65 | 0 | 0 |
| 2001 | 300 | 76 | 224 | 74.7 | 76 | 0 | 0 |
| 2002 | 300 | 87 | 213 | 71.0 | 86 | 0 | 0 |
| 2003 | 300 | 91 | 209 | 69.7 | 91 | 0 | 0 |
| 2004 | 300 | 84 | 216 | 72.0 | 84 | 0 | 0 |
| 2005 | 300 | 98 | 202 | 67.3 | 98 | 0 | 0 |
| 2006 | 300 | 95 | 205 | 68.3 | 95 | 0 | 0 |
| 2007 | 300 | 109 | 191 | 63.7 | 109 | 0 | 0 |
| 2008 | 300 | 114 | 186 | 62.0 | 114 | 0 | 0 |
| 2009 | 300 | 130 | 170 | 56.7 | 130 | 0 | 0 |
| 2010 | 300 | 131 | 169 | 56.3 | 131 | 0 | 0 |
| 2011 | 300 | 138 | 162 | 54.0 | 138 | 0 | 0 |
| 2012 | 300 | 153 | 147 | 49.0 | 153 | 0 | 0 |
| 2013 | 300 | 164 | 136 | 45.3 | 163 | 0 | 0 |
| 2014 | 300 | 166 | 134 | 44.7 | 165 | 0 | 0 |
| 2015 | 300 | 177 | 123 | 41.0 | 176 | 0 | 0 |
| 2016 | 300 | 181 | 119 | 39.7 | 180 | 0 | 0 |
| 2017 | 300 | 192 | 108 | 36.0 | 190 | 0 | 0 |
| 2018 | 300 | 207 | 93 | 31.0 | 204 | 0 | 0 |
| 2019 | 300 | 228 | 72 | 24.0 | 224 | 0 | 0 |
| 2020 | 300 | 235 | 65 | 21.7 | 231 | 34 | 0 |
| 2021 | 300 | 244 | 56 | 18.7 | 241 | 241 | 232 |
| 2022 | 300 | 254 | 46 | 15.3 | 251 | 251 | 251 |
| 2023 | 300 | 263 | 37 | 12.3 | 258 | 257 | 258 |
| 2024 | 300 | 288 | 12 | 4.0 | 281 | 281 | 281 |
| 2025 | 300 | 297 | 3 | 1.0 | 290 | 290 | 290 |
| 2026 | 300 | 300 | 0 | 0.0 | 297 | 242 | 297 |

Reading the table:

- **Before 2020 the column "have financials for that year" is zero in every year.** The database knows the 2021 to 2026 accounts of companies that happened to survive; it knows nothing about any company's accounts in 2010.
- "Have any financials" equals "still listed": the vendor covers practically every survivor and no one else.
- From December 2021 a result is usable on the date under the 4-month rule for 232 of 300, rising to 290 by December 2025. That is five December cross-sections (2021 to 2025), each missing the companies that have since left (18.7% of the 2021 list, 1.0% of the 2025 list).

The same table for the top 500 is in `out/tables/coverage_top500.md`.

### 3.3 Survivorship across the whole market

| Year (Dec) | Companies with a price | Still listed Nov 2026 | Have any financials | Missing because gone % |
|---|---|---|---|---|
| 2000 | 1287 | 212 | 211 | 83.5 |
| 2001 | 1244 | 230 | 229 | 81.5 |
| 2002 | 1277 | 261 | 260 | 79.6 |
| 2003 | 1332 | 292 | 291 | 78.1 |
| 2004 | 1461 | 332 | 331 | 77.3 |
| 2005 | 1569 | 368 | 367 | 76.5 |
| 2006 | 1717 | 438 | 437 | 74.5 |
| 2007 | 1902 | 527 | 526 | 72.3 |
| 2008 | 1782 | 533 | 532 | 70.1 |
| 2009 | 1800 | 570 | 569 | 68.3 |
| 2010 | 1848 | 604 | 603 | 67.3 |
| 2011 | 1844 | 638 | 637 | 65.4 |
| 2012 | 1803 | 664 | 663 | 63.2 |
| 2013 | 1788 | 699 | 698 | 60.9 |
| 2014 | 1779 | 740 | 739 | 58.4 |
| 2015 | 1794 | 802 | 801 | 55.3 |
| 2016 | 1840 | 882 | 880 | 52.1 |
| 2017 | 1901 | 955 | 952 | 49.8 |
| 2018 | 1880 | 1016 | 1011 | 46.0 |
| 2019 | 1818 | 1067 | 1060 | 41.3 |
| 2020 | 1847 | 1169 | 1162 | 36.7 |
| 2021 | 2051 | 1426 | 1418 | 30.5 |
| 2022 | 2057 | 1532 | 1522 | 25.5 |
| 2023 | 1962 | 1593 | 1583 | 18.8 |
| 2024 | 1671 | 1648 | 1638 | 1.4 |
| 2025 | 1711 | 1704 | 1693 | 0.4 |
| 2026 | 1728 | 1728 | 1712 | 0.0 |

Of the 1,848 companies with a price in December 2010, 67.3% are not listed today. Smaller companies leave more often than large ones, so the whole-market loss is larger than the top-300 loss. The drop in "companies with a price" from 2024 is the price file's limit (section 3.4), not a fall in listings. For the same reason the 2024 to 2026 rows understate how many have gone.

What the missing companies do to a return calculation (top 300, price-only next-12-month return in %, from report 51's cohorts):

| Year (Dec) | Companies | Survivors to 2026 | Next-12-month return, all | Survivors only | Since gone | Overstatement (points) |
|---|---|---|---|---|---|---|
| 2000 | 300 | 65 | -2.8 | 10.8 | -6.6 | 13.6 |
| 2001 | 300 | 76 | -13.8 | -11.6 | -14.5 | 2.2 |
| 2002 | 300 | 87 | 21.4 | 16.1 | 23.6 | -5.3 |
| 2003 | 300 | 91 | 20.1 | 29.0 | 16.2 | 8.9 |
| 2004 | 300 | 84 | 10.1 | 15.5 | 8.0 | 5.4 |
| 2005 | 300 | 98 | 29.4 | 25.3 | 31.4 | -4.1 |
| 2006 | 300 | 95 | 16.6 | 20.7 | 14.8 | 4.0 |
| 2007 | 300 | 109 | -51.0 | -47.8 | -52.8 | 3.2 |
| 2008 | 300 | 114 | 63.4 | 62.0 | 64.3 | -1.4 |
| 2009 | 300 | 130 | 6.2 | 9.5 | 3.7 | 3.3 |
| 2010 | 300 | 131 | -19.4 | -16.9 | -21.3 | 2.5 |
| 2011 | 300 | 138 | 1.5 | 9.6 | -5.4 | 8.1 |
| 2012 | 300 | 153 | -4.7 | 4.1 | -13.9 | 8.8 |
| 2013 | 300 | 164 | -4.4 | -3.2 | -5.9 | 1.2 |
| 2014 | 300 | 166 | 0.8 | 8.8 | -9.1 | 8.0 |
| 2015 | 300 | 177 | 14.1 | 18.3 | 8.1 | 4.2 |
| 2016 | 300 | 181 | 9.6 | 14.4 | 2.4 | 4.7 |
| 2017 | 300 | 192 | -11.7 | -9.1 | -16.4 | 2.6 |
| 2018 | 300 | 207 | 21.4 | 26.1 | 10.9 | 4.7 |
| 2019 | 300 | 228 | 6.1 | 6.7 | 4.2 | 0.6 |
| 2020 | 300 | 235 | 16.4 | 17.9 | 10.8 | 1.5 |
| 2021 | 300 | 244 | -18.1 | -17.6 | -20.1 | 0.5 |
| 2022 | 300 | 254 | 4.9 | 5.4 | 1.8 | 0.6 |
| 2023 | 300 | 263 | 7.0 | 7.5 | 3.0 | 0.6 |
| 2024 | 300 | 288 | 23.1 | 22.7 | 32.5 | -0.4 |

Survivors beat the full list in 17 of 20 years from 2000 to 2019, by 3.8 points a year on average. For 2020 to 2024 the gap is 0.5 points, because few companies have had time to leave. The gap is the average over all 300; a screen that favours small, indebted or loss-making companies would be hit much harder, because those are the ones that fail.

Caveat on this table: companies that leave by takeover usually leave at a premium, and companies that fail leave near zero. The "since gone" column mixes both.

### 3.4 Prices, delistings, dividends, shares, market value

| Item | Coverage | Limits |
|---|---|---|
| Daily prices | 9,725,260 rows, 1997-01-02 to 2026-11-13, 6,057 entities | Complete for all companies only to 31 May 2024. The 907,860 later rows are for today's listed companies plus 26 larger companies that left after May 2024 (column `survivors_only`). Price only, no dividends. Exchange-traded products and codes longer than three characters are excluded |
| Code history | 7,343 code-entity spans | Links: ASX change list 2001 to 2020, price continuity outside it, price match to today's codes (1,522 verified by price, 78 found as renames since May 2024, 14 accepted on code alone). Report 51 measured the link rules; they are not perfect |
| Delistings | 1,803 official records with reasons (346 failure-type, 923 takeover-type), Aug 2000 to Apr 2020 | After April 2020 there is no official list in reach: endings are inferred from the last price, with no reason. 287 companies left between June 2024 and Nov 2026 at an unknown date |
| Listing date | First price date for 5,019 entities | Unknown for companies already trading on 2 Jan 1997. The vendor's IPO date is filled for 0 ASX companies. A code re-used after a gap of 200+ days also starts a new entity |
| Dividends | 4,553 payments for 521 companies | Latest ten payments per company only (406 companies have older history behind the paywall). Cash amount only, no franking |
| Share counts | 126,566 rows: period-end shares, weighted average shares, current shares and free float | Period ends only, six years. Split adjustment by the vendor was not verified |
| Market value | At fiscal period ends for 1,751 companies; daily for about one year, monthly for two years for the largest 262 | Older rows are behind the paywall |
| Sector and industry | 1,786 listed companies | **Today's classification only.** The vendor's own scheme, not GICS. Using it in a historical test is hindsight |
| Macro | 24,044 rows | Context only |

## 4. Biases and risks, in order of importance

1. **Survivorship.** Every vendor figure belongs to a company listed on 14 Nov 2026 (sections 3.2 and 3.3). This cannot be repaired from this source.
2. **Short history.** Six fiscal years, which give five yearly cross-sections. No signal can be confirmed or rejected on five observations, biased or not.
3. **No release dates (look-ahead).** `report_date` is empty on every row. The only date evidence is the vendor's "last updated" stamp, which applies to each company's newest period. Across 1,771 companies the gap from period end to that stamp has a median of 62 days and a 90th percentile of 92 days; 99.7% are within four months and 6 companies are later. The stamp also moves when the vendor corrects old data, so it overstates the true lag for some companies; 5 companies had a stamp earlier than the period end and were set aside. This supports the 4-month rule as conservative for most results and shows it is not a guarantee: late lodgers exist, and they are disproportionately companies in trouble.
4. **Restatement.** The database holds one vintage. The vendor shows figures as it holds them today, and earlier years can be the restated comparatives from a later report. Example from memory, not checked against a filing here: BHP's fiscal 2021 revenue appears as US$56.9 billion (operating revenue), the figure restated after the petroleum business was reclassified, where the August 2021 release showed about US$60.8 billion. Internal checks cannot detect this: full-year figures agree with the sum of the half-years in all but 1.0% of cases, because the vendor derives one from the other.
5. **Split-adjusted per-share data.** Earnings per share, dividends per share and the price-based ratios are adjusted to today's share basis. Period-end share counts may or may not be; 77 of today's issuance figures fall in a window with a recorded split and are flagged.
6. **Vendor standardisation.** Line items follow the upstream template (S&P Global), not the company's own layout. "Gross profit" for miners excludes most operating costs (BHP shows an 86% gross margin), and banks and insurers have none.
7. **Current-only classifications and counts.** Sector, industry, employees, free float, ownership and analyst data are as at the fetch date.
8. **Mixed currencies.** 109 companies report in USD and 79 in other currencies. Ratios inside one company are unaffected; anything that mixes market value (AUD) with statement values needs conversion.
9. **Entity linking.** Today's codes were tied to historical price entities by price match where possible. 172 codes have no earlier entity (new listings since May 2024, or links that were missed). Four codes were found to be re-used by a different company and were kept separate.
10. **Liquidity ranking is not size ranking.** The historical universes are ranked by traded value because no historical market value exists for delisted companies.

## 5. Which fields are usable for what

| Data | Honest back-test? | Screening today? | Why |
|---|---|---|---|
| Daily prices to 31 May 2024, all companies | Yes, price-only | Yes | Includes delisted companies; splits handled by report 51's rules |
| Daily prices after 31 May 2024 | Only with care | Yes | Missing most companies that left after May 2024 |
| Official delistings 2000 to 2020 with reasons | Yes | — | Needed to treat failures as losses |
| Inferred endings after 2020 | Partly | — | Date is the last price; reason unknown |
| Financial statements and ratios, fiscal 2021 to 2026 | **No** | Yes, with the 4-month rule | Survivors only, six years, no release dates, restated |
| Anything derived from them: profitability, ROE, accruals, leverage, growth, asset growth, issuance, cash runway | **No** | Yes | Same |
| Financials first seen in a later dated snapshot (none yet) | Yes, from the snapshot date | Yes | The snapshot date is a true "known by" date and the company list is as it stood then |
| Sector and industry | **No** | Yes | Today's classification |
| Dividends (last ten per company) | **No** | Yes | Survivors only, truncated, no franking |
| Share counts and market value history | **No** | Yes | Survivors only, six years or less |
| Statistics snapshot (float, ownership, scores, next results date) | From now on only | Yes | A snapshot is point-in-time on its own date |
| Macro series | Yes | Yes | Published with short lags; allow one month |

Lag rule used wherever a date is needed, and stored in `assumed_available_date`: an annual result is treated as known four months after the fiscal year end; a half-year result three months after the half-year end. ASX rules require the preliminary final report within two months and the audited accounts within three (report 57, section 1.2), so the rule adds at least a month of margin. It is an assumption. It does nothing about survivorship or restatement.

## 6. First use: quality metrics for today's companies

Computed for 14 Nov 2026 with the 4-month rule, so a June 2026 year end is used (available from 30 Oct 2026), a December year end uses 2025, and a September 2026 year end is not yet used even where the result is already out. 1,776 companies have a usable annual result; 3 are stale (older than 16.5 months) and are left out of the summaries. Stored in table `quality_metrics` for six dates (each December from 2021 and 14 Nov 2026) and in `out/quality_metrics_latest.csv`.

Definitions: gross profitability = gross profit / total assets; ROE = net income to ordinary holders / average ordinary equity; accruals = (net income − operating cash flow) / average total assets, lower meaning more cash-backed earnings; debt to equity = total debt / total equity; earnings growth = change in net income, only where both years are profitable; asset growth = change in total assets; net share issuance = change in period-end share count over 12 months; cash runway = cash and short-term investments / operating cash used per quarter, only for companies burning cash, measured on the latest half-year or quarter where one exists.

Medians by size group (count of companies with the metric in brackets):

| Group (by market value) | Companies | Profitable % | Gross profit / assets (n) | ROE (n) | Accruals (n) | Debt / equity (n) | Earnings growth (n) |
|---|---|---|---|---|---|---|---|
| Largest 300 | 300 | 85.3 | 0.225 (239) | 0.093 (296) | -0.042 (300) | 0.411 (296) | 0.144 (225) |
| Rank 301-800 | 498 | 41.2 | 0.164 (370) | -0.046 (468) | -0.06 (491) | 0.063 (484) | 0.188 (163) |
| Rank 801 and below | 975 | 14.5 | 0.052 (694) | -0.262 (815) | -0.084 (961) | 0.006 (876) | 0.225 (64) |
| All | 1773 | 34.0 | 0.123 (1303) | -0.098 (1579) | -0.064 (1752) | 0.041 (1656) | 0.17 (452) |

| Group (by market value) | Companies | Negative equity % | Asset growth (n) | Net share issuance, 12 months (n) | Issued more than 10% % | Burning cash % | Median runway of burners, quarters (n) | Runway under 4 quarters % |
|---|---|---|---|---|---|---|---|---|
| Largest 300 | 300 | 1.3 | 0.067 (300) | 0.002 (300) | 15.3 | 14.7 | 9.555 (44) | 4.3 |
| Rank 301-800 | 498 | 2.8 | 0.167 (491) | 0.053 (497) | 44.4 | 54.4 | 11.0 (271) | 12.2 |
| Rank 801 and below | 975 | 10.2 | 0.054 (961) | 0.22 (963) | 63.2 | 81.9 | 4.639 (798) | 37.6 |
| All | 1773 | 6.6 | 0.076 (1752) | 0.101 (1760) | 49.8 | 62.8 | 5.637 (1113) | 24.9 |

What this shows:

- **Most listed companies do not make a profit.** 34.0% of all listed companies made a profit in their latest usable year; among the largest 300 it is 85.3%, and below rank 800 it is 14.5%.
- **Below rank 800, 81.9% are burning cash, 37.6% have under a year of cash at the current rate, and 63.2% grew their share count by more than 10% in a year.** Cash runway and share issuance separate companies in the small-cap tail far better than ROE does, since ROE is negative for most of them.
- Earnings growth can be computed for only about a quarter of companies, because it needs two profitable years.

Largest 300 by sector (current classification):

| Sector (current) | Companies | Profitable % | Gross profit / assets | ROE | Accruals | Debt / equity | Earnings growth | Growth n |
|---|---|---|---|---|---|---|---|---|
| Materials | 70 | 81.4 | 0.23 | 0.139 | -0.071 | 0.154 | 0.579 | 44 |
| Financials | 47 | 100.0 | 0.082 | 0.098 | 0.007 | 0.337 | 0.046 | 45 |
| Industrials | 40 | 90.0 | 0.242 | 0.115 | -0.051 | 0.631 | 0.166 | 33 |
| Real Estate | 28 | 89.3 | 0.084 | 0.089 | 0.02 | 0.503 | 0.451 | 21 |
| Consumer Discretionary | 24 | 83.3 | 0.388 | 0.139 | -0.059 | 1.07 | 0.106 | 20 |
| Technology | 19 | 73.7 | 0.254 | 0.098 | -0.082 | 0.238 | 0.005 | 12 |
| Healthcare | 19 | 68.4 | 0.22 | 0.081 | -0.042 | 0.383 | 0.138 | 13 |
| Energy | 17 | 64.7 | 0.091 | 0.036 | -0.046 | 0.336 | -0.327 | 9 |
| Communication Services | 15 | 93.3 | 0.251 | 0.056 | -0.107 | 0.605 | 0.109 | 12 |
| Consumer Staples | 14 | 85.7 | 0.335 | 0.061 | -0.061 | 0.793 | -0.185 | 10 |
| Utilities | 7 | 100.0 | 0.144 | 0.077 | -0.043 | 0.494 | 0.68 | 6 |

A simple composite for the largest 300, excluding Financials and Real Estate where gross profit and debt mean something different: the average percentile rank on the five original metrics (high profitability, high ROE, low accruals, low debt, high growth), for companies with at least four of them (213 of 225). Highest 15:

| Code | Name | Sector | Size rank | Year end used | GP/assets | ROE | Accruals | Debt/equity | Earnings growth | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| GGP | Greatland Resources Limited | Materials | 89 | 2026-06-30 | 0.39 | 0.48 | -0.14 | 0.01 | 1.56 | 0.88 |
| PAF | Pan African Resources PLC | Materials | 125 | 2026-06-30 | 0.39 | 0.45 | -0.2 | 0.06 | 1.52 | 0.87 |
| RRL | Regis Resources Limited | Materials | 113 | 2026-06-30 | 0.35 | 0.38 | -0.2 | 0.05 | 1.81 | 0.87 |
| ALK | Alkane Resources Ltd | Materials | 168 | 2026-06-30 | 0.23 | 0.31 | -0.23 | 0.01 | 5.92 | 0.83 |
| OBM | Ora Banda Mining Limited | Materials | 150 | 2026-06-30 | 0.45 | 0.53 | -0.33 | 0.06 | 0.16 | 0.83 |
| SFR | Sandfire Resources Limited | Materials | 73 | 2026-06-30 | 0.34 | 0.18 | -0.13 | 0.02 | 2.82 | 0.81 |
| EMR | Emerald Resources NL | Materials | 121 | 2026-06-30 | 0.41 | 0.33 | -0.07 | 0.03 | 1.96 | 0.81 |
| GMD | Genesis Minerals Limited | Materials | 78 | 2026-06-30 | 0.29 | 0.36 | -0.14 | 0.15 | 1.72 | 0.8 |
| CYL | Catalyst Metals Limited | Materials | 257 | 2026-06-30 | 0.34 | 0.29 | -0.14 | 0.04 | 0.43 | 0.8 |
| CDA | Codan Limited | Technology | 65 | 2026-06-30 | 0.57 | 0.31 | -0.08 | 0.09 | 0.69 | 0.8 |
| GNP | GenusPlus Group Ltd | Industrials | 199 | 2026-06-30 | 0.99 | 0.18 | -0.21 | 0.24 | 0.39 | 0.79 |
| WGX | Westgold Resources Limited | Materials | 108 | 2026-06-30 | 0.23 | 0.2 | -0.15 | 0.06 | 11.76 | 0.79 |
| TNE | Technology One Limited | Technology | 63 | 2025-09-30 | 0.38 | 0.33 | -0.19 | 0.12 | 0.17 | 0.78 |
| GNG | GR Engineering Services Limited | Materials | 217 | 2026-06-30 | 1.03 | 0.54 | -0.1 | 0.13 | 0.14 | 0.78 |
| WAF | West African Resources Limited | Materials | 130 | 2025-12-31 | 0.32 | 0.32 | -0.13 | 0.26 | 1.12 | 0.78 |

Lowest 15:

| Code | Name | Sector | Size rank | Year end used | GP/assets | ROE | Accruals | Debt/equity | Earnings growth | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| RIC | Ridley Corporation Limited | Consumer Staples | 269 | 2026-06-30 | 0.11 | 0.06 | -0.07 | 1.66 | -0.36 | 0.28 |
| AIA | Auckland International Airport Limited | Industrials | 53 | 2026-06-30 | 0.05 | 0.03 | -0.01 | 0.26 | -0.2 | 0.28 |
| AAC | Australian Agricultural Company Limited | Consumer Staples | 294 | 2026-03-31 | -0.01 | 0.06 | 0.04 | 0.29 |  | 0.27 |
| SNZ | Summerset Group Holdings Limited | Healthcare | 234 | 2025-12-31 | 0.0 | 0.08 | -0.03 | 0.6 | -0.22 | 0.27 |
| RYM | Ryman Healthcare Limited | Healthcare | 204 | 2026-03-31 | 0.01 | -0.04 | -0.04 | 0.39 |  | 0.26 |
| JHX | James Hardie Industries plc | Materials | 30 | 2026-03-31 | 0.13 | 0.02 | -0.05 | 0.74 | -0.75 | 0.25 |
| ALX | Atlas Arteria Limited | Industrials | 104 | 2025-12-31 | 0.01 | 0.04 | 0.02 | 0.3 | -0.23 | 0.25 |
| FPR | FleetPartners Group Limited | Industrials | 264 | 2025-09-30 | 0.08 | 0.12 | 0.06 | 2.92 | -0.03 | 0.23 |
| WOR | Worley Limited | Energy | 114 | 2026-06-30 | 0.06 | 0.05 | -0.02 | 0.58 | -0.42 | 0.23 |
| NXT | NEXTDC Limited | Technology | 85 | 2026-06-30 | 0.03 | 0.02 | -0.0 | 0.55 |  | 0.21 |
| GLC | Glencore plc | Materials | 8 | 2025-12-31 | 0.04 | 0.01 | -0.04 | 1.25 |  | 0.19 |
| CBO | Cobram Estate Olives Limited | Consumer Staples | 235 | 2026-06-30 | 0.07 | -0.01 | -0.01 | 0.99 |  | 0.18 |
| BCI | BCI Minerals Limited | Materials | 200 | 2026-06-30 | -0.02 | 0.04 | 0.02 | 0.84 |  | 0.16 |
| DBI | Dalrymple Bay Infrastructure Limited | Industrials | 151 | 2025-12-31 | 0.04 | 0.03 | -0.01 | 2.12 | -0.64 | 0.13 |
| EF2 | Energy Fuels Inc. | Energy | 159 | 2025-12-31 | 0.01 | -0.14 | 0.0 | 0.99 |  | 0.12 |

**This list is a description of last year's accounts, not a forecast and not a recommendation.** 12 of the top 15 are classified as Materials, most of them gold producers, which is what a strong year for the gold price would produce: profit, cash flow and growth all rise together. A naive quality score on one year of accounts is largely a commodity-cycle indicator. A usable version would need several years of averaging and comparison within industries, and neither can be validated on this data. The lowest group includes infrastructure and retirement-village owners whose accounts are dominated by property revaluations: the definitions do not fit them.

The file `out/quality_metrics_latest.csv` is frozen with SHA-256 `6b74527c51157645a6ced9579c0e4f904d33875bc782b1ed4211522ab638176e`. It is a dated record of what these metrics said on 14 Nov 2026 and can serve as the starting point of a forward paper test.

## 7. What can and cannot be back-tested, stated plainly

Can be tested honestly with this database:

- Price-based signals (momentum, trend, volatility, reversal, liquidity) from 2000 to May 2024 on all companies, delisted ones included, with failures counted. This is what reports 51 and 53 already did.
- Event studies around official delistings and code changes, 2000 to April 2020.
- From the second snapshot on: anything using figures first seen in a snapshot, on the company list as it stood at that snapshot. One year of snapshots gives one year of evidence.

Cannot be tested honestly:

- **Any fundamental signal before fiscal 2021.** There is no data.
- **Any fundamental signal over 2021 to 2026 presented as evidence.** Five yearly observations; the companies that left are missing; the figures are today's restated ones. The lag rule fixes only the smallest of the three problems. No such test was run for this report, because a result in either direction would carry no information and a favourable one would invite belief.
- **Sector-neutral or sector-relative versions of any signal historically.** Sector is known only for survivors, as of today.
- **Dividend-yield or total-return signals.** Ten payments per survivor, no franking.
- **Size (market value) signals historically.** Market value exists only for survivors, six years.
- **Quality as a failure filter.** The question "would a cash-runway or leverage screen have avoided the companies that failed?" is the one this database is least able to answer, because the companies that failed are exactly the ones with no financials.

What a survivors-only fundamental test would be biased by: 18.7% of the December 2021 top 300 and 36.7% of all companies priced in December 2020 are missing. A screen that excludes weak companies is compared against a group that has already lost its failures, so its benefit is understated; a value or turnaround screen that includes weak companies loses its own failures and is overstated. The direction of the error depends on the signal, so it cannot be corrected with a flat adjustment.

## 8. Making it point-in-time from today

Every vendor figure has `fetched_at` (UTC) and `vintage` (fetch date). The first vintage is 2026-11-14 and is marked `baseline`: the figures existed before the first fetch and their true release dates are unknown.

How later snapshots work:

1. Run `code/snapshot_monthly.sh` (optionally with a date). It re-checks robots.txt and the automated-access sentence in the terms and stops if either has changed; fetches a fresh list of ASX codes; fetches statements, ratios, statistics and dividends for every code into `raw/sa_snapshots/YYYY-MM-DD/` with its own manifest. About 16,000 requests, 4.5 hours at one a second. It can be resumed by running the same command again.
2. `build_db.py` reads every snapshot folder in date order. A figure not seen before is added with `change_type = new` and `assumed_available_date` set to the snapshot date, which is a true upper bound on when it became public. A figure whose value differs from the previous vintage is added as `revised`, and the old value is kept. `is_latest` marks the current version. Table `snapshot_log` counts both.
3. The fresh code list dates arrivals and departures to within one snapshot interval, which fills the gap left by the missing official delisting list. Departed companies keep their rows, so from now on the database stops being survivors-only.

Suggested rhythm: monthly. If only two runs a year are wanted, mid-March and mid-September catch every half-year and full-year result once (report 57, section 4.2), at the cost of dating each figure to within six months instead of one.

Not done, and why: no recurring job was created. It runs for hours against a third party's site every month, so it is an owner decision. The snapshot logic was written but has only been exercised on the first vintage; the first real second snapshot should be checked by hand (count of `new` rows against the companies known to have reported). The company table and the code-to-entity links are still built from the first list and will need extending when codes change.

Fields added at report 61's request: `fetched_at` on every table; `fundamentals_derived` with period-end share counts, 12-month net issuance (with a split flag), asset growth, accruals, cash, quarterly burn and cash runway (25,786 issuance rows, 19,569 runway rows); `listing_date_proxy` on `company`; `backtest_flag = "survivors only, not for back-tests"` on every vendor-derived table.

## 9. What this enables, and what it does not change

- Screening and sanity checks on today's companies: profitability, leverage, cash runway and dilution for any candidate the price-based engine picks. A momentum pick that is burning cash with two quarters of runway can be seen as such.
- A dated baseline. With snapshots, the project accumulates its own point-in-time fundamentals at no licence cost, one month at a time. In two to three years that is a small but honest test set.
- A cross-check for any vendor bought under report 57: its figures for fiscal 2021 to 2026 can be compared with these for the same companies.
- It does not provide evidence for or against any fundamental signal on the ASX. Report 57's conclusion stands: a back-test of quality needs a licensed point-in-time history that includes delisted companies.
- Use limits from the source's terms: keep it private (no competing database or product) and do not train machine-learning models on the vendor's figures. Rule-based screens are not model training, but a fitted model in the learning engine (report 52) should not take these figures as inputs without a licence that allows it.

## 10. Reasons this report could be wrong

- The entity links between today's codes and historical price series were made by price matching and a small number may be wrong; the survivorship percentages would move by a few tenths of a point.
- "Gone" counts a renamed company as gone if the rename was missed. 78 renames since May 2024 were found by price match; some may remain, which would overstate the most recent years' losses slightly.
- The reporting-lag evidence rests on a vendor timestamp whose meaning is described on the vendor's pages only as updating "within hours after each earnings release".
- The vendor's free pages may change or close; the snapshot plan depends on them staying as they are.
- The BHP restatement example is from memory and was not checked against the filings.
- Nothing here was replicated by a second builder.

## 11. Data dictionary

**`company`** (6,057 rows). One row per company entity (a continuous price history, possibly across several ASX codes). 1997-2026, includes delisted.

| Column | Type | Meaning |
|---|---|---|
| eid | VARCHAR | Entity id from report 51: first code + "#" + segment number (a gap of >200 days in a code starts a new entity). "#S"/"#N" = entity first seen in stockanalysis after May 2024. |
| code | VARCHAR | Last ASX code the entity traded under. |
| all_codes | VARCHAR | All codes the entity traded under, oldest first (see company_code_history). |
| name | VARCHAR | Company name: stockanalysis profile (current companies), else ASX delisting list, else ASX name-change list. Often missing for companies that left before 2000 or after 2020. |
| status | VARCHAR | listed_2026-11 (in the vendor list, or still priced) / delisted_official_record / ended_before_2024-05 (inferred) / ended_after_2024-05 (inferred; larger companies only) / gone_between_2024-06_and_2026-11 (inferred, date unknown). |
| first_price_date | TIMESTAMP | First daily price row. |
| last_price_date | TIMESTAMP | Last daily price row. |
| n_price_days | BIGINT | Number of daily price rows. |
| sa_code | VARCHAR | stockanalysis.com code if the entity is in its current ASX list (fetched 2026-11-14). |
| sa_map_method | VARCHAR | How the entity was tied to the stockanalysis code: price_match(_report51) = verified on overlapping daily closes; code_match_* = same code, not price-verified; sa_only_* = no earlier price history. |
| sa_rank | DOUBLE | Rank by market capitalisation in the stockanalysis ASX list on 2026-11-14 (1 = largest). |
| market_cap_aud | DOUBLE | Market capitalisation in AUD on 2026-11-13 (vendor figure; for dual-listed groups it is the whole group). |
| revenue_ttm_aud | DOUBLE | Trailing-12-month revenue in AUD as shown in the list (vendor conversion). |
| sector | VARCHAR | Vendor sector, CURRENT classification only. |
| industry | VARCHAR | Vendor industry, CURRENT classification only. |
| sector_basis | VARCHAR | Reminder that sector/industry are as at fetch, not historical. |
| isin | VARCHAR | ISIN from the vendor profile. |
| sic | VARCHAR | SIC code from the vendor profile. |
| country | VARCHAR | Country of the company. |
| founded | DOUBLE | Year founded. |
| ipo_date | DOUBLE | IPO date if the vendor gives one (mostly empty for ASX). |
| employees | DOUBLE | Employees (latest). |
| fiscal_year_months | VARCHAR | Fiscal year, e.g. "July - June". |
| financial_currency | VARCHAR | Currency of the financial statements. |
| price_currency | VARCHAR | Currency of the share price. |
| primary_listing_path | VARCHAR | If set, the ASX line is a secondary listing/CDI and the vendor keeps financials under this other exchange path (not fetched under the ASX path). |
| is_secondary_listing | BOOLEAN | True when primary_listing_path is set. |
| profile_fetched_at | TIMESTAMP | UTC time the profile page was fetched. |
| listing_date_proxy | TIMESTAMP | Listing date proxy: first daily price row of the entity. Null if the entity already traded when the price file starts (2 Jan 1997). The vendor IPO date (ipo_date) is almost always empty for ASX. |
| listing_date_basis | VARCHAR | How listing_date_proxy was set. |
| list_fetched_at | TIMESTAMP | UTC time the stockanalysis ASX list (rank, market cap) was fetched. |
| sector_backtest_flag | VARCHAR | "survivors only, not for back-tests" for every vendor-derived company field (sector, industry, rank, market cap). |

**`company_code_history`** (7,343 rows). Codes used by each entity with the dates each code has price rows.

| Column | Type | Meaning |
|---|---|---|
| eid | VARCHAR | Entity id. |
| code | VARCHAR | ASX code. |
| first_date | TIMESTAMP | First price date under this code. |
| last_date | TIMESTAMP | Last price date under this code. |
| n_days | BIGINT | Price rows under this code. |
| name_from_change_list | VARCHAR | Company name from the ASX change list around those dates, if any. |
| link_source | VARCHAR | How codes were linked into one entity. |

**`name_changes`** (2,605 rows). ASX code and name changes 2001-2020 as published by ASX, taken from the rs77 public repository (raw events, not all are linked to entities).

| Column | Type | Meaning |
|---|---|---|
| change_date | TIMESTAMP | Effective date. |
| old_code | VARCHAR | Old code. |
| old_name | VARCHAR | Old name. |
| new_code | VARCHAR | New code. |
| new_name | VARCHAR | New name. |
| source | VARCHAR | Source. |
| fetched_at | TIMESTAMP | UTC time the source copy was built locally. |

**`prices_daily`** (9,725,260 rows). Daily prices per entity 1997-01-02 to 2026-11-13. Ordinary shares with 3-character codes; exchange-traded products and indices excluded (report 51 rules).

| Column | Type | Meaning |
|---|---|---|
| eid | VARCHAR | Entity id. |
| code | VARCHAR | Code on that day. |
| date | TIMESTAMP | Trading date. |
| open | DOUBLE | Open. |
| high | DOUBLE | High. |
| low | DOUBLE | Low. |
| close | DOUBLE | Close. Basis in close_basis: raw unadjusted to 2024-05-31; split-adjusted (as at fetch) afterwards. |
| volume | DOUBLE | Shares traded. |
| adj_close | DOUBLE | Split/consolidation-adjusted close, continuous within the entity (report 51 corporate-action fixes). Price only: dividends are NOT included. |
| traded_value | DOUBLE | Close x volume in AUD (liquidity/size proxy). |
| close_basis | VARCHAR | raw unadjusted / split-adjusted as at fetch. |
| source | VARCHAR | Which source the row came from. |
| fetched_at | TIMESTAMP | UTC time the source was obtained (rs77 file: local build time on 2026-11-14 of repository commit 5fd4f5b0; stockanalysis rows: fetch time). |
| survivors_only | BOOLEAN | True for rows after 31 May 2024: the all-companies price file ends there, and later rows exist only for companies still listed in November 2026, plus about 26 larger companies that left in that window (fetched by report 51). Other companies that left between June 2024 and November 2026 simply stop at 31 May 2024. |

**`financials`** (3,109,699 rows). Long table of financial statement items and vendor ratios. One vintage so far (fetched 2026-11-14). NOT point-in-time.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | stockanalysis code (current ASX code). |
| period_end | TIMESTAMP | Fiscal period end date. |
| fiscal_year | DOUBLE | Fiscal year label. |
| fiscal_period | VARCHAR | FY, H1/H2, Q1-Q4 or TTM. |
| period_type | VARCHAR | annual / interim (half-year or quarter) / ttm (trailing twelve months as at fetch). |
| statement | VARCHAR | income / balance / cashflow / ratios. |
| item | VARCHAR | Vendor line-item id (titles in financial_items). |
| value | DOUBLE | Value in the statement currency (ratios are plain numbers; margins and growth are fractions). |
| currency | VARCHAR | Currency of the statements (e.g. USD for BHP, CSL). |
| source | VARCHAR | stockanalysis.com and its upstream source code (spg = S&P Global Market Intelligence). |
| fetched_at | TIMESTAMP | UTC time the page was fetched. |
| vintage | VARCHAR | Fetch date; with later re-fetches the table becomes point-in-time from 2026-11-14 forward. |
| change_type | VARCHAR | baseline = present at the first fetch (release date unknown); new = first seen in a later dated snapshot; revised = value changed between snapshots. |
| first_seen_at | TIMESTAMP | UTC time this figure (this value) was first fetched. For "new"/"revised" rows this is a true upper bound on when it became public. |
| is_latest | BOOLEAN | True for the most recent version of the figure. |
| report_date | TIMESTAMP_NS | Date the company released the figures. ALWAYS NULL: the source does not give it. |
| source_last_updated | TIMESTAMP | Only on the latest period: the date the vendor last updated this company's financials (usually within hours of the latest results release, so an upper bound on that release date). |
| assumed_available_date | TIMESTAMP | Conservative lag rule: annual = period end + 4 months; interim = period end + 3 months; ttm = fetch date. An assumption, not a fact. |
| pit_flag | VARCHAR | "date of fiscal period end only - NOT point-in-time" on every row. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests" on every row. |
| period_end_derived | BOOLEAN | True when the period end was inferred (rows from the vendor's "prior period" block carry no date). |
| from_prior_block | BOOLEAN | True for the one year / two half-years just before the vendor's visible window. |
| eid | VARCHAR | Entity id. |

**`financial_items`** (530 rows). Line-item ids and display titles.

| Column | Type | Meaning |
|---|---|---|
| statement | VARCHAR | Statement. |
| item | VARCHAR | Item id. |
| title | VARCHAR | Vendor title (null for margins/growth helper fields). |

**`financials_page_meta`** (12,709 rows). One row per fetched financial page: currency, reporting frequency, how many periods the vendor holds in total (full_count) versus shown free.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| kind | VARCHAR | Page: is/bs/cf/ra + _a (annual) or _q (interim). |
| currency | VARCHAR | Statement currency. |
| reporting_frequency | VARCHAR | semiannual / quarterly. |
| fiscal_year | VARCHAR | Fiscal year months. |
| last_trailing_date | VARCHAR | Latest period end. |
| full_count | BIGINT | Number of periods the vendor holds (paid tier); the free page shows the latest 5 annual / 10 interim. |
| sa_last_updated | VARCHAR | Vendor "last updated" date for this company's financials. |
| latest_period | VARCHAR | Latest period end shown. |
| n_periods | BIGINT | Periods shown. |
| source | VARCHAR | Upstream source code. |

**`dividends`** (4,553 rows). Dividend history: latest 10 payments per company only (older rows are behind the vendor paywall).

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| ex_date | TIMESTAMP | Ex-dividend date. |
| amount | DOUBLE | Cash amount per share (franking not given). |
| currency | VARCHAR | Currency. |
| record_date | TIMESTAMP | Record date. |
| pay_date | TIMESTAMP | Payment date. |
| declared_date | TIMESTAMP_S | Declaration date (not populated for ASX). |
| source | VARCHAR | Source. |
| fetched_at | TIMESTAMP | UTC fetch time. |
| history_truncated | BOOLEAN | True when the vendor says more history exists than is shown. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests". |

**`shares_outstanding`** (126,566 rows). Share counts from statements (period ends) and the current snapshot.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| date | TIMESTAMP | Period end, or fetch date for snapshots. |
| shares | DOUBLE | Number of shares. |
| kind | VARCHAR | Which share count. |
| period_type | VARCHAR | annual / interim / snapshot. |
| source | VARCHAR | Source. |
| fetched_at | TIMESTAMP | UTC fetch time. |
| pit_flag | VARCHAR | Point-in-time status. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests". |

**`market_cap_history`** (103,530 rows). Market capitalisation history as far as shown free: daily ~1 year, weekly ~6 months, monthly ~2 years (top 300 only), and at fiscal period ends from the ratios pages.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| date | TIMESTAMP | Date. |
| market_cap | DOUBLE | Market capitalisation. |
| freq | VARCHAR | daily/weekly/monthly/quarterly/annual or period_end_*. |
| source | VARCHAR | Source page. |
| fetched_at | TIMESTAMP | UTC fetch time. |
| currency | VARCHAR | Currency note. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests". |

**`splits`** (1,973 rows). Splits and consolidations: vendor last-split field, steps derived in report 51, and the report 51 price heuristic.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| date | TIMESTAMP | Event date. |
| kind | VARCHAR | Type. |
| ratio | DOUBLE | Ratio/factor as given by the source. |
| source | VARCHAR | Source. |
| fetched_at | TIMESTAMP_NS | UTC fetch time (vendor rows). |
| eid | VARCHAR | Entity id where known. |
| basis | VARCHAR | vendor / derived / heuristic. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests" on vendor rows; null on rows derived from the full price file. |

**`delistings`** (4,570 rows). Official ASX removals Aug 2000 - Apr 2020 with reasons, plus inferred endings for entities whose prices stop without an official record.

| Column | Type | Meaning |
|---|---|---|
| eid | VARCHAR | Entity id where matched. |
| code | VARCHAR | Code. |
| name | VARCHAR | Name. |
| delist_date | TIMESTAMP | Removal date, or last price date when inferred. |
| date_basis | VARCHAR | official removal date / last price date (inferred) / window 2024-06..2026-11. |
| reason | VARCHAR | ASX reason text (official rows). |
| fail_keyword | BOOLEAN | Reason mentions liquidation, administration, receivers, unpaid fees, rule 17.12/17.15. |
| takeover_keyword | BOOLEAN | Reason mentions acquisition, scheme, merger, rule 17.11. |
| source | VARCHAR | Source. |
| fetched_at | TIMESTAMP | UTC time the source copy was built locally. |

**`statistics_snapshot`** (172,050 rows). Current statistics page values (snapshot at fetch): shares, float, ownership, valuation, scores, next results date.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| section | VARCHAR | Page section. |
| id | VARCHAR | Field id. |
| title | VARCHAR | Field title. |
| value_text | VARCHAR | Displayed value. |
| value_num | DOUBLE | Numeric value where parseable. |
| fetched_at | TIMESTAMP | UTC fetch time. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests". |

**`fundamentals_derived`** (31,286 rows). Derived per company and period end: share-count history and 12-month net issuance, asset growth, accruals, cash and cash runway. Vendor-derived: survivors only.

| Column | Type | Meaning |
|---|---|---|
| code | VARCHAR | Code. |
| eid | VARCHAR | Entity id. |
| period_end | TIMESTAMP | Period end. |
| period_type | VARCHAR | annual / interim. |
| fiscal_period | VARCHAR | FY, H1/H2, Q1-Q4. |
| period_months | BIGINT | Length of the period in months (12, 6 or 3). |
| shares_out | DOUBLE | Total common shares at period end (balance sheet). |
| shares_out_12m_ago | DOUBLE | Same, 12 months earlier (+-20 days). |
| net_issuance_12m | DOUBLE | shares_out / shares_out_12m_ago - 1. Positive = dilution, negative = buy-back or consolidation. |
| split_in_window | BOOLEAN | True if a split/consolidation is recorded for the code inside the 12 months: the issuance figure is then not a financing signal. |
| assets | DOUBLE | Total assets. |
| assets_12m_ago | DOUBLE | Total assets 12 months earlier. |
| asset_growth_12m | DOUBLE | assets / assets_12m_ago - 1. |
| accruals | DOUBLE | (Net income - operating cash flow) / average total assets; annual rows only. |
| cash | DOUBLE | Cash and short-term investments (cash and equivalents if the former is missing). |
| op_cash_flow | DOUBLE | Operating cash flow of the period. |
| quarterly_burn | DOUBLE | Cash used in operations per quarter (only when operating cash flow is negative). |
| cash_runway_quarters | DOUBLE | cash / quarterly_burn: quarters of cash left at the current operating burn. |
| quarterly_burn_after_capex | DOUBLE | Same, after capital expenditure (free cash flow). |
| cash_runway_quarters_after_capex | DOUBLE | cash / quarterly_burn_after_capex. |
| burn_basis | VARCHAR | Which period the burn was measured on. |
| shares_issued_cash | DOUBLE | Cash raised from share issues in the period. |
| shares_repurchased_cash | DOUBLE | Cash spent on buy-backs in the period. |
| fetched_at | TIMESTAMP | UTC fetch time of the underlying figures. |
| assumed_available_date | TIMESTAMP | Period end + 4 months (annual) or + 3 months (interim). |
| pit_flag | VARCHAR | NOT point-in-time. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests". |

**`quality_metrics`** (10,362 rows). Quality metrics per company at six dates (Dec 2021-Dec 2025 and 14 Nov 2026) under the 4-month lag rule. Lagged, not point-in-time.

| Column | Type | Meaning |
|---|---|---|
| as_of_date | TIMESTAMP | Date the metrics are computed for. |
| code | VARCHAR | Code. |
| period_end | TIMESTAMP | Fiscal year end of the annual result used (latest with year end + 4 months <= asof). |
| prev_period_end | TIMESTAMP | Prior fiscal year end (null if not a normal 12-month step). |
| months_since_period_end | DOUBLE | Age of the result in months at asof. |
| stale | BOOLEAN | True if the result is more than 16.5 months old at asof (the next annual result is overdue or missing). |
| gross_profitability | DOUBLE | Gross profit / total assets (Novy-Marx). Null for banks/insurers; vendor "gross profit" for miners excludes most operating costs. |
| roe | DOUBLE | Net income to common / average common equity of the two year ends; null if equity <= 0. |
| accruals | DOUBLE | (Net income - operating cash flow) / average total assets. Lower = more cash-backed earnings. |
| debt_to_equity | DOUBLE | Total debt / total equity; null if equity <= 0. |
| negative_equity | BOOLEAN | Equity <= 0. |
| earnings_growth | DOUBLE | Net income growth year on year; only when both years are profitable. |
| earnings_growth_note | VARCHAR | Why earnings_growth is null. |
| eps_growth | DOUBLE | Diluted EPS growth; only when both years positive. EPS is split-adjusted by the vendor. |
| revenue | DOUBLE | Revenue (statement currency). |
| net_income | DOUBLE | Net income to common (statement currency). |
| total_assets | DOUBLE | Total assets. |
| equity | DOUBLE | Total equity. |
| profitable | BOOLEAN | Net income > 0. |
| asset_growth | DOUBLE | Total assets growth year on year. |
| net_issuance_12m | DOUBLE | Change in period-end share count over 12 months (latest usable period, annual or interim). Positive = dilution. |
| net_issuance_period_end | TIMESTAMP | Period end the issuance figure refers to. |
| net_issuance_split_flag | BOOLEAN | True if a split/consolidation falls inside the window. |
| cash | DOUBLE | Cash and short-term investments at the latest usable period. |
| quarterly_burn | DOUBLE | Operating cash used per quarter (null if operating cash flow is positive). |
| cash_runway_quarters | DOUBLE | cash / quarterly_burn; null if not burning cash. |
| cash_runway_period_end | TIMESTAMP | Period end the runway refers to. |
| cash_flow_positive | BOOLEAN | Operating cash flow >= 0 in that period. |
| backtest_flag | VARCHAR | "survivors only, not for back-tests". |
| lag_rule | VARCHAR | Lag rule applied. |
| pit_status | VARCHAR | Reminder: lagged but not point-in-time. |
| eid | VARCHAR | Entity id. |
| name | VARCHAR | Name. |
| sector | VARCHAR | Current sector. |
| industry | VARCHAR | Current industry. |
| sa_rank | DOUBLE | Market-cap rank 2026-11-14. |
| market_cap_aud | DOUBLE | Market cap AUD 2026-11-13. |
| financial_currency | VARCHAR | Statement currency. |

**`snapshot_log`** (1 rows). One row per dated fetch (vintage) of stockanalysis pages.

| Column | Type | Meaning |
|---|---|---|
| vintage | VARCHAR | Fetch date. |
| folder | VARCHAR | Folder under raw/. |
| figures_new | BIGINT | Figures first seen in this vintage. |
| figures_revised | BIGINT | Figures whose value changed against the previous vintage. |
| codes | BIGINT | Companies with data in the vintage. |

**`macro`** (24,044 rows). Context series: AUD/USD, TWI, yields, cash rate, commodity index (monthly from 1975) and RBA daily exchange rates 2023-2026.

| Column | Type | Meaning |
|---|---|---|
| date | TIMESTAMP | Date. |
| series | VARCHAR | Series name. |
| value | DOUBLE | Value. |
| freq | VARCHAR | monthly/daily. |
| description | VARCHAR | Description. |
| source | VARCHAR | Source. |
| fetched_at | TIMESTAMP | UTC time of the local copy (RBA publication dates are in the raw files). |

**`fetch_manifest`** (22,574 rows). Every HTTP request made for this database and for the copied report 51 downloads.

| Column | Type | Meaning |
|---|---|---|
| fetched_at | TIMESTAMP | UTC time. |
| http | VARCHAR | HTTP status. |
| path | VARCHAR | File under raw/. |
| bytes | BIGINT | Size. |
| sha256 | VARCHAR | SHA-256 of the body. |
| url | VARCHAR | URL. |
| batch | VARCHAR | Which build made the request. |

## 12. Files

- Database: `scratchpad/company_db/db/asx_company.duckdb`
- Code: `scratchpad/company_db/code/` (`fetch_sa.py`, `fetch_px.py`, `fetch_extra.py`, `snapshot_monthly.sh`, `devalue.py`, `parse_sa.py`, `build_db.py`, `data_dictionary.py`, `metrics.py`, `coverage.py`, `render_tables.py`, `build_report.py`, `report_template.txt`)
- Raw downloads, one folder per source: `raw/sa/` (vendor pages), `raw/sa_px/` (vendor price history), `raw/sa_primary/` (primary-listing pages of secondary listings), `raw/sa_delisted_probe/`, `raw/sa_meta/` (robots.txt, terms, lists), `raw/asx/` (robots.txt, terms and a note only), `raw/company_study/`, `raw/au_signals/`; request log `raw/manifest.tsv`
- Outputs: `out/coverage_by_year.csv`, `out/survivorship_all_companies.csv`, `out/survivor_return_gap.csv`, `out/reporting_lag_detail.csv`, `out/consistency_checks.csv`, `out/item_coverage.csv`, `out/quality_metrics_latest.csv` (+ `.sha256`), `out/quality_composite_top300_nonfin.csv`, `out/quality_by_sector_top300.csv`, `out/data_dictionary.csv`, `out/coverage.json`, `out/metrics.json`, `out/report_values.json`, `out/build_log.txt`
