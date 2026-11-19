**Method limit:** this session's network policy blocked every direct provider fetch (hetzner.com, docs.hetzner.com, binarylane.com.au, docs.oracle.com, interactivebrokers.com.au, eodhd.com, rba.gov.au). All figures below come from web-search excerpts of those pages plus third-party sources, not from reading the pages myself. Those hosts need allowing in the session's network settings for a first-hand check.

FX used for conversions is my assumption, not verified: A$1.54 per US$, A$1.75 per EUR.

## 1. Server

| Option | Price | A$/yr incl. GST | Tag |
|---|---|---|---|
| Hetzner CX23 (2 vCPU / 4 GB) | €5.49/mo + €0.50 IPv4, ex VAT | ~A$138 | [2+ sources] price; [1 source] tax |
| BinaryLane 1 vCPU / 2 GB | A$9.80/mo ex GST | ~A$129 | [1 source] price; [1 source] GST |
| BinaryLane 2 vCPU / 4 GB | A$19.60/mo ex GST | ~A$259 | [2+ sources] price (both BinaryLane's own pages); [1 source] GST |
| Vultr 2 GB / 4 GB | US$10 / US$20 | ~A$203 / ~A$406 | [1 source] third-party; GST assumed 10% |
| DigitalOcean 2 GB / 4 GB | US$12 / US$24 | ~A$243 / ~A$487 | [1 source] third-party, with conflicting figures (US$18 cited for some tiers) |

- **Hetzner 2026 changes:** CX23 went €2.99 → €3.99 (1 April) → €5.49 (15 June), new orders and rescales only. "CX23 … €3.99 | €5.49 | +38%" ([bitdoze](https://www.bitdoze.com/hetzner-cloud-cost-optimized-plans/), [northflank](https://northflank.com/blog/hetzner-cloud-server-price-increases), [Tom's Hardware](https://www.tomshardware.com/tech-industry/hetzner-to-raise-prices-by-up-to-37-percent-from-april-1)).
- **Hetzner availability:** one source says CX23 is currently unorderable and cites a "Limited availability of cloud instances" status notice since 26 June 2026; another says CX plans remain orderable. [unverified]
- **Hetzner tax:** its VAT page lists Australia at 10% from 1 January 2021 ([docs.hetzner.com](https://docs.hetzner.com/general/billing-and-account-management/billing-at-hetzner/value-added-tax)). [1 source]
- **BinaryLane:** "$9.80/mo" (1 vCPU / 2 GB) and "$19.60/mo" (2 vCPU / 4 GB, 60 GB NVMe) ([binarylane.com.au/vps-hosting](https://www.binarylane.com.au/vps-hosting); 4 GB also in its [support article](https://support.binarylane.com.au/support/solutions/articles/11000135372-installing-openclaw-on-binarylane)). The ex-GST treatment comes only from a [whtop review](https://www.whtop.com/review/binarylane.com.au).
- **Vultr / DigitalOcean:** list prices from [stackfreeks](https://stackfreeks.com/vultr-pricing-2026/) and [betterstack](https://betterstack.com/community/guides/web-servers/digitalocean-vs-vultr/).

**Oracle Always Free A1** [2+ sources]
- The allowance was halved on 15 June 2026 to 2 OCPU / 12 GB (1,500 OCPU-hours and 9,000 GB-hours a month), with "no public announcement" ([InfoQ](https://www.infoq.com/news/2026/07/oracle-cloud-free-tier-limits/), [linuxiac](https://linuxiac.com/oracle-quietly-cuts-free-tier-ampere-a1-resources-in-half/)).
- Idle reclaim applies when, over 7 days, "CPU utilization for the 95th percentile is less than 20%, network utilization is less than 20%, and memory utilization is less than 20% (A1 shapes)" ([Oracle docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [oracommit](https://oracommit.blogspot.com/2026/02/understanding-oci-always-free-compute.html)).
- An idle end-of-day trader will fall under those thresholds, and regional capacity shortages are common. It is still large enough for the stack, but treat it as paper-only.

**Home device**
- **Raspberry Pi 5 8GB:** board A$283.85 inc GST ([Core Electronics](https://core-electronics.com.au/raspberry-pi-5-model-b-8gb.html)); PB Tech lists A$286.50. Kits run about A$380–390. Four memory-driven price rises in ten months took the US price to $175 ([How-To Geek](https://www.howtogeek.com/raspberry-pi-boards-are-getting-another-price-hike-thanks-to-ram-costs/)). [2+ sources]
- **N100/N150 mini PC, 16 GB:** A$229–300 delivered in OzBargain deals ([Beelink](https://ozbargain.com.au/node/888637), [Trigkey](https://ozbargain.com.au/node/890402)), but these are expired; retail listings run A$390–490. [1 source]
- **Power:** Pi 5 idles at 3.0–3.6 W, an N100 at about 7.5–10 W ([CNX Software](https://www.cnx-software.com/2024/04/29/raspberry-pi-5-intel-n100-mini-pc-comparison-features-benchmarks-price/), [selfhosting.sh](https://selfhosting.sh/hardware/raspberry-pi-vs-mini-pc/)). [2+ sources]
- **Tariff:** about 33 c/kWh (Ausgrid flat-rate example for 2026-27, via [Canstar](https://www.canstar.com.au/news/power-bill-plunge-households-pocket-up-to-155-in-electricity-price-drop/); a consumer guide gives 30–35 c). [1 source]
- **Annual electricity:** Pi at ~5 W average is about A$14; mini PC at ~8 W is about A$23.

**ARM support** [2+ sources]
- The gnzsnz image publishes `linux/arm64` tags ([Docker Hub](https://hub.docker.com/r/gnzsnz/ib-gateway/tags)).
- The repo labels aarch64 "experimental, so expects bugs" and builds it with a Zulu 17 aarch64 JRE ([PR #397 diff](https://github-users.yhajoa.workers.dev/gnzsnz/ib-gateway-docker/pull/397/files)).
- It runs on ARM, but x86 is the safer choice for live money.

## 2. IBKR data

**(a) Snapshots** [1 source — IBKR's own pages; a third-party page repeats the 3c figure]
- Non-US instruments cost "USD 0.03 per quote request", and "accounts will receive a waiver of USD 1.00 per month" ([IBKR AU market data](https://www.interactivebrokers.com.au/en/pricing/market-data-pricing.php), [IBKR FAQ](https://www.interactivebrokers.com/lib/cstools/faq/#/content/1136177301)).
- That is about 33 free ASX snapshots a month; the charge is made in base-currency equivalent and capped at the streaming price.
- Two symbols on one trade day a month costs nothing.

**(b) Historical bars without a subscription: no** [2+ sources — two IBKR documents plus a user report]
- IBKR's API docs say the API "always requires Level 1 streaming real time data to return historical data" ([TWS API docs](https://interactivebrokers.github.io/tws-api/historical_data.html)).
- IBKR Campus says the same: historical data "generally needs a market data subscription… just like live data" ([Campus](https://www.interactivebrokers.com/campus/ibkr-quant-news/ibkr-api-historical-data-how-to-download-bars-without-pacing-violations/)).
- A user reported "No market data permissions for ASX STK" ([EliteTrader](https://www.elitetrader.com/et/threads/tws-api-and-asx-historical-data.338962/), an old thread).
- One developer says 1-minute TRADES bars came back as a fallback on a paper account; this is unconfirmed. [unverified]

**(c) ASX live bundle** [1 source]
- "ASX Total (L1, L2) AUD 25.00" non-professional, AUD 152 professional, on IBKR's AU and global pricing pages.
- No source anywhere shows A$37.50; treat that figure as wrong or obsolete.
- A US$500 minimum equity for subscriptions is mentioned only by a third-party review. [unverified]

**(d) Delayed ASX data (type 3): not dependable** [1 source for the failure reports]
- IBKR says free delayed data is given only "when made available by the exchanges" ([IBKR docs](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-delayed/market-data-type-behavior)).
- Community reports show ASX delayed requests returning error 10167 and then no ticks ([twsapi group](https://groups.io/g/twsapi/topic/requested_market_data_is_not/98029220), [Sapient PR](https://github.com/KevinHindmarch/Sapient/pull/28)).
- It needs an empirical test on the actual account.

## 3. Backtest history

**EODHD**
- "EOD Historical Data — All World" is US$19.99/mo or US$199/yr, with a one-month minimum ("no long-term commitments") ([eodhd.com/pricing](https://eodhd.com/pricing), [NexusFi](https://nexusfi.com/d/data-providers/eodhd-eod-historical-data/)). [2+ sources]
- It offers "30+ years of daily historical data with adjusted prices" for ASX, including splits and dividends ([eodhd.com/asx-data](https://eodhd.com/asx-data)). [1 source]
- The plan is marked personal use; commercial use needs a separate plan (from €399/mo). [1 source]
- Not verified: the per-ticker start dates for VAS and VGS, the exact terms on keeping data after cancelling, and the free-tier limits.
- One month is about A$31.

**Free alternatives**
- **Yahoo / yfinance:** an unofficial wrapper, "intended for personal use only", with repeated breakages (2023, May 2025) and per-IP 429 rate limits, worse from cloud IPs ([yfinance discussion](https://github.com/ranaroussi/yfinance/discussions/2431), [scrapfly](https://scrapfly.io/blog/posts/guide-to-yahoo-finance-api)). [2+ sources]
- **Stooq:** has required a captcha-gated API key since about March–April 2026 ([pandas-datareader #1012](https://github.com/pydata/pandas-datareader/issues/1012), [lite-C forum](https://opserver.de/ubb7/ubbthreads.php?Number=489362)); files are personal-use only. [2+ sources] ASX coverage is not confirmed. [unverified]

## 4. RBA FX

- The free daily CSV is `rba.gov.au/statistics/tables/csv/f11.1-data.csv`, covering the TWI and about 22 bilateral rates including AUD/USD ([RBA exchange rates](https://www.rba.gov.au/statistics/frequency/exchange-rates.html), [OpenDataRouter](https://opendatarouter.com/datasets/rba/exchange-rates)). [2+ sources]
- The RBA release schedule reads "Exchange Rates – Daily – 2023 to Current – F11.1: Weekdays, After 4.00 pm" ([RBA schedule](https://www.rba.gov.au/schedules-events/frequency-statistical-releases.html)). [1 source — RBA; the other mentions are mirrors]
- The current file starts in 2023; 2018–2022 and earlier are separate historical files (pre-2018 in XLS).
- Nothing is published on NSW public holidays, so carry the last rate forward.

## 5. Annual running cost at A$5,000

Trading: 6 trades at the A$6 fixed-plan minimum is A$36 (0.08% with a minimum of AUD 6.00; [IBKR commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-stocks.php), [compareforexbrokers](https://www.compareforexbrokers.com.au/reviews/ibkr/)). [2+ sources] GST treatment conflicts: IBKR's table header says "Exclusive of GST", while third parties variously say inclusive or plus. I use A$39.60 as the conservative figure.

| Item (A$/yr) | (i) Home mini PC | (ii) Cheapest cloud | (iii) Oracle free, paper only |
|---|---|---|---|
| Server | ~70 amortised (A$280 over 4 yrs) + 23 power = 93 | 129 (BinaryLane 2 GB) to 138 (Hetzner CX23) | 0 |
| IBKR data (snapshots within waiver) | 0 | 0 | 0 |
| EODHD, one month (year 1) | 31 | 31 | 31 |
| Trading, 6 trades | 39.60 | 39.60 | 0 |
| **Running total** | **~164 (3.3%)** | **~200–209 (4.0–4.2%)** | **~31 (0.6%)** |
| Tax drag (my estimate, unsourced) | ~0.5–1.0% | ~0.5–1.0% | n/a |
| **Total drag** | **~3.8–4.3%** | **~4.5–5.2%** | **0.6%** |

- With hardware already owned, (i) falls to about A$94 (1.9%) before tax.
- A Pi 5 kit instead of the mini PC makes (i) about A$111 for the server line.
- Adding ASX Total would cost A$300/yr, or 6.0% of capital on its own.
- The tax estimate assumes roughly 3% blended distributions at a 30% rate plus 2% Medicare, less franking credits, with small discounted capital gains. [unverified]
- At A$5,000 the fixed costs are several percent of capital a year, so they are a material hurdle for the strategy.

## Spec-ready decisions

1. Do not buy ASX Total (A$25/mo, 6% of capital a year). Do not design around `reqHistoricalData` for ASX; IBKR documents it as needing a Level 1 subscription.
2. Take signal data from outside IBKR: an EODHD one-month backfill (about A$31), then daily closes from a free source with a cross-check, treating Yahoo and Stooq as breakable.
3. Use IBKR snapshots only at order time (2 a month, inside the US$1 waiver), with limit orders. Test delayed type 3 on the paper account before relying on it, and code for 10167 with no ticks.
4. Host on x86: an owned or cheap N100/N150 mini PC is cheapest, otherwise Hetzner CX23 (4 GB, if orderable) or BinaryLane 4 GB. BinaryLane 2 GB is tight for Gateway plus Postgres and needs swap.
5. Use Oracle A1 for paper only: size to 2 OCPU / 12 GB or less, expect idle reclaim and capacity failures, and note that the ARM gateway image is experimental.
6. Budget A$6.60 per ASX trade until the GST treatment is confirmed on a real statement, and cap trades at about 6 a year.
7. For FX, pull RBA F11.1 CSV after 4 pm Sydney time on weekdays, carry forward on NSW holidays, and stitch in the historical files for pre-2023.
8. Re-check first-hand once the hosts are allowed: IBKR GST treatment, the ASX snapshot and delayed entitlements, BinaryLane GST, Hetzner CX23 orderability, and EODHD's VAS/VGS history depth and licence text.