# New ASX listings tracker - 2026-11-19

INFORMATION ONLY. Makes no trading decision; feeds nothing in the paper record. EODHD data (private, non-commercial use); no ASX-website access. Returns from the FIRST EODHD CLOSE (no offer price available), EODHD adjusted close. Code: bigwins_forward/code/newlist_tracker.py; data: bigwins_forward/data/newlist/.

- Symbol-list diff vs 2026-11-16 (seed: forward-store symbols.csv): 15 new codes, 1 codes left the active list, 0 same-code name changes.
- Genuine new listings (3-letter ordinary shares) tracked: 77 active, 0 already delisted; first traded in the last 30 days: 4.
- Excluded from the table: 3 renames / carried-over histories / data stubs, 92 ETFs/funds, 55 other securities (rights, deferred settlement, notes...), 0 pending first trade (see newlist_other.csv).

## Latest listings

| listed | code | name | sector | first close | last | since first close | mcap A$m | status |
|---|---|---|---|---|---|---|---|---|
| 2026-11-12 | CX8 | Capability X Limited | Technology | 0.29 | 0.27 | -7% | 46 | active |
| 2026-11-02 | SMG | Seven Media Group Limited | Communication Services | 0.495 | 0.45 | -9% | 215 | active |
| 2026-10-23 | MSX | Miro Sciences Ltd | Healthcare | 0.056 | 0.043 | -23% | 17 | active |
| 2026-10-22 | WMC | Wiluna Mining Corporation Ltd | Basic Materials | 0.56 | 0.39 | -30% | 141 | active |
| 2026-10-16 | OWL | Overwatch Technologies Limited | Technology | 0.175 | 0.12 | -31% | 16 | active |
| 2026-10-14 | GLC* | Glencore Plc | Basic Materials | 11.2 | 9.59 | -15% | 112,236 | active |
| 2026-10-13 | ID1 | Identifai Genetics Limited | Healthcare | 0.25 | 0.4 | +60% | 77 | active |
| 2026-10-05 | NMD | Normandy Minerals Ltd | Basic Materials | 0.29 | 0.2 | -31% | 24 | active |
| 2026-10-02 | NRL | Northstone Resources Limited | Basic Materials | 0.013 | 0.007 | -46% | 16 | active |
| 2026-10-01 | AQ1 | Aqyr Ltd | Industrials | 0.026 | 0.038 | +46% | 8 | active |
| 2026-09-28 | AGT | Arbitr Group Limited | Technology | 0.115 | 0.091 | -21% | 6 | active |
| 2026-09-22 | PRB | Parbo Resources Limited | Basic Materials | 0.27 | 0.27 | +0% | 12 | active |
| 2026-09-22 | INN | Innovaero Technologies Limited | Industrials | 0.5 | 0.25 | -50% | 79 | active |
| 2026-09-02 | AXR | Axiant Resources Limited | Basic Materials | 0.215 | 0.135 | -37% | 8 | active |
| 2026-08-31 | AMK | Almasar Minerals Limited | Basic Materials | 0.255 | 0.175 | -31% | 24 | active |

\* large at listing (> A$1bn): likely a secondary/dual listing, demerger or merger vehicle rather than an IPO (kept, flagged). EODHD gives no IPODate/offer price for AU codes, so returns start at the first close.

## Best since listing (tracked window, >= 5 trading days)

| code | name | listed | since first close | max drawdown |
|---|---|---|---|---|
| PC2 | PC Gold Ltd | 2025-10-21 | +159% | -49% |
| DSM | Desert Minerals Ltd | 2025-10-21 | +128% | -35% |
| KAO | Kaoko Metals Limited | 2026-05-07 | +108% | -72% |
| GRS | Gwardar Resources Limited | 2026-07-31 | +90% | -35% |
| ID1 | Identifai Genetics Limited | 2026-10-13 | +60% | -33% |

## Worst since listing (tracked window, >= 5 trading days)

| code | name | listed | since first close | max drawdown |
|---|---|---|---|---|
| BPG | Black Pearl Group Limited | 2025-11-25 | -87% | -91% |
| SLD | Saluda Medical Inc | 2025-12-05 | -85% | -88% |
| TIO | Temas Resources Corp. | 2025-10-27 | -81% | -82% |
| EPI | Epiminder Ltd | 2025-12-01 | -79% | -82% |
| LFT | Li-ft Power Ltd. | 2026-05-26 | -78% | -81% |

## Baseline 2014+ (descriptive only; survivorship-aware; no strategy test)

Per first-trade year: new listings (3-letter ordinary shares, renames/relistings excluded); over the first 365 days from the first close (price return, split-adjusted; delisted names to their last EODHD close): share that ever halved / ever doubled, median 12-month return vs the S&P/ASX 200 price index over the same window. 2026 is incomplete.

| year | listed | 12m complete | delisted <12m | halved % | doubled % | median 12m | median ASX200 | median excess | beat ASX200 % |
|---|---|---|---|---|---|---|---|---|---|
| 2014 | 75 | 75 | 0 | 12.0 | 17.3 | 3.1 | -0.9 | 2.0 | 52.0 |
| 2015 | 104 | 104 | 0 | 26.0 | 16.3 | -10.6 | 2.1 | -9.2 | 37.5 |
| 2016 | 107 | 107 | 0 | 29.0 | 10.3 | -12.8 | 9.1 | -21.8 | 24.3 |
| 2017 | 128 | 128 | 0 | 33.6 | 21.9 | -14.5 | 3.2 | -16.1 | 31.2 |
| 2018 | 108 | 108 | 1 | 46.3 | 12.0 | -38.2 | 7.2 | -44.7 | 18.5 |
| 2019 | 62 | 62 | 0 | 48.4 | 24.2 | -9.6 | -6.7 | -2.0 | 46.8 |
| 2020 | 93 | 93 | 2 | 35.5 | 28.0 | -11.5 | 13.4 | -31.8 | 31.2 |
| 2021 | 201 | 201 | 0 | 42.3 | 17.4 | -31.1 | -6.2 | -26.0 | 25.9 |
| 2022 | 99 | 99 | 0 | 50.5 | 13.1 | -32.5 | 0.8 | -33.4 | 18.2 |
| 2023 | 34 | 34 | 0 | 50.0 | 17.6 | -21.7 | 9.3 | -30.7 | 29.4 |
| 2024 | 33 | 33 | 0 | 30.3 | 15.2 | -7.5 | 7.2 | -15.6 | 33.3 |
| 2025 | 45 | 32 | 2 | 25.0 | 43.8 | -7.0 | 0.4 | -11.4 | 43.8 |
| 2026 | 55 | 0 | 0 | nan | nan | nan | nan | nan | nan |
| 2014-2025 | 1089 | 1076 | 5 | 36.5 | 18.2 | -17.9 | 3.2 | -20.3 | 30.4 |
