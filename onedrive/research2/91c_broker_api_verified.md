# 91c — Broker APIs for ASX automation: verified from official docs (follows report 91)

Research date: 2026-11-20. Web only. No sign-ups, credentials or trading.

**Method.** Unlike report 91, the official pages were fetched in full this time, with curl through the proxy (openapi.moomoo.com, open.moomoo.com, docs-en.itigerup.com and its `.md` page versions, www.itiger.com, interactivebrokers.com / .com.au). Quotes below are copied from the fetched pages.

Two sources could not be read:
- quant.itigerup.com deep pages timed out. They are superseded by docs-en.itigerup.com.
- interactivebrokers.github.io is not on the network allowlist.

IBKR's per-exchange order-type matrix is rendered by JavaScript, so its ASX row could not be read.

**Context from the trading system (GO_LIVE_GUIDE.md):**
- The EMG2-18 build sends **LOC orders into the ASX closing auction** (`config/bfast.yaml` `execution.order_type: LOC`), with an `LMT` (15:30 limit order) fallback.
- It runs on an **IBKR paper (`DU`) account** through `trader/broker/ibkr.py`.

Any broker change has to be judged against those two facts.

---

## 1. moomoo (Futu) AU

moomoo now has **two different APIs**, and their docs disagree about Australia.

| Question | Finding | Exact quote + URL |
|---|---|---|
| **Can a moomoo AU account place and cancel ASX orders through the API?** | **Through the classic OpenD API: NO.** The intro page's "Trading Capacity" table marks Australian Stocks/ETFs **X for paper and for every broker, Moomoo AU included**. The `TrdMarket_AU = 8` enum and `SecurityFirm_FutuAU = 4` do exist, so the plumbing is there, but the support table says not enabled. | "Supports trading across multiple markets including Hong Kong, the US, A-Shares, Singapore, Japan, and Malaysia." Table row: "Australian Market / Stocks, ETFs / X X X X X X X X". (https://openapi.moomoo.com/moomoo-api-doc/en/intro/intro.html, Moomoo API Doc v10.12). Enum: "TrdMarket_AU = 8 ; //AU market", "AU market Minimum OpenD version requirements: 9.0.5008" (https://openapi.moomoo.com/moomoo-api-doc/en/trade/trade.html) |
| | **Through the new REST "WebAPI" (webapi.moomoo.com, OAuth 2.1 / API key): YES for live trading, Moomoo AU only.** | "Supports trading across Hong Kong, US, China A-shares, Singapore, Japan, Korea, Malaysia, Australia, Canada, and more… The Live Trading columns below follow the products each broker has enabled on WebAPI." Table row: "Australia Market / Stocks / Paper ✗ / … Moomoo AU ✓ …" (https://open.moomoo.com/api/overview). "Place, modify, and cancel require the OAuth scope trade:write" (https://open.moomoo.com/api/trading/overview). The Naming Dictionary lists "AU — Australia market", "ASX — Australian Securities Exchange", "FUTUAU — Moomoo (Australia)" (https://open.moomoo.com/api/trading/naming-dictionary) |
| **Order types incl. at-auction / closing auction** | **No closing-auction order for ASX.** OpenD: auction types are HK-only, and there is no MOC/LOC type. WebAPI: the only auction types are `AUCTION`/`AUCTION_LIMIT`, described as "Often HK auction"; there is no market-on-close type in the enum. (The moomoo AU *app* offers MOC per report 91, but the API does not expose it.) Use **LIMIT** (or MARKET). | OpenD: "AUCTION — At-auction market orders. Valid for HK stocks early and closing auctions only" (trade.html). WebAPI: "AUCTION — At-auction market — Often HK auction" and "Whether an order can be placed still depends on the account market, symbol, and trading permissions; unsupported requests return an error." (https://open.moomoo.com/api/trading/trade/place-order) |
| **API paper trading for ASX** | **NO** (both APIs). | WebAPI table: Australia Stocks — Paper Trading "✗" (https://open.moomoo.com/api/overview). OpenD table: Australian Market paper "X" (intro.html). The 2026-05-21 changelog note, "Moomoo Australia now supports paper trading competition accounts, with Skills-based account queries." (https://openapi.moomoo.com/moomoo-api-doc/en/changelog/changelog.html), is about competition-account *queries*, not ASX order simulation. |
| **Quote rights / market data** | **No ASX market data through the API.** Australia is absent from the OpenD quote-rights table and marked ✗ in the WebAPI table. Prices would have to come from the existing EODHD store, which already happens. | "Australia Market / Stocks, ETFs / ✗" (https://open.moomoo.com/api/overview, Market Data table); "Australian Market / Stocks, ETFs / X" (intro.html) |
| **Rate limits** | OpenD place_order: **15 per 30 s per account**. OpenD modify/cancel: **20 per 30 s**. WebAPI: **100 requests/min per IP** per API family. All far above ~125 orders/yr. | "A maximum of 15 requests per 30 seconds under a single account ID (acc_id)…" (https://openapi.moomoo.com/moomoo-api-doc/en/trade/place-order.html). "A maximum of 20 requests per 30 seconds under a single account ID (acc_id)…" (https://openapi.moomoo.com/moomoo-api-doc/en/trade/modify-order.html). "quote, trading, crypto and simulated-trading APIs each allow at most 100 requests per minute from the same IP." (https://open.moomoo.com/api/overview/rate-limit) |
| **API permission / questionnaire** | OpenD requires a questionnaire on first login. WebAPI requires OAuth consent with `trade:write`, and the account must have the market enabled. Some orders return `need_order_confirm`/`jump_url`, a browser step that would interrupt unattended trading. | "After the first login, you need to complete API Questionnaire and Agreements before you can continue to use Moomoo API." (https://openapi.moomoo.com/moomoo-api-doc/en/intro/authority.html). "trade:write means the API layer may accept trading write requests. It does not replace whether the account is eligible to trade a given market — check enable_market" (https://open.moomoo.com/api/overview/getting-started). "jump_url is present: open it in a browser to continue." (place-order) |
| **API fee** | None extra; same as the app. | "Trading through the Moomoo API incurs no additional charges. Fees are the same as trading through the app." (https://open.moomoo.com/api/overview/api-fee) |

**Verdict:** ASX live trading is possible only through the new REST WebAPI, which is new and conflicts with the classic OpenD docs. It has no ASX paper trading, no closing-auction order and no ASX data.

## 2. Tiger Brokers AU (TBAU)

| Question | Finding | Exact quote + URL |
|---|---|---|
| **Live ASX orders through the API** | **YES** (Prime account). | Supported Products table: "Australia — Stocks, ETFs — Prime ✓ — Paper Trading ✓" (https://docs-en.itigerup.com/docs/intro). Account types: Prime "Supported markets: US, Hong Kong, China A-shares (Stock Connect), Singapore, Australia" (https://docs-en.itigerup.com/docs/account-type) |
| **Paper ASX through the API** | **CONTRADICTORY in Tiger's own docs. Treat it as unproven.** The intro table says ✓. The account-type page lists paper markets as US/HK/A-shares only. | "Paper Trading Account: Supports trading in US stocks, Hong Kong stocks, A-shares, and options." and the table row "Supported markets … Paper Trading Account: US, Hong Kong, China A-shares" (https://docs-en.itigerup.com/docs/account-type) |
| **Order types incl. auction** | **No auction / closing-auction order for ASX.** The Australia table lists Limit, Market, Stop Limit, Stop, Attached, Bracket and Trailing Stop. The "Pre-market Auction Order (OPG/DAY)" row appears only under Hong Kong. | Australia → Stocks, ETFs: "Limit Order DAY/GTC ✓ / Market Order DAY/GTC ✓ / Stop Limit Order … / Stop Order … / Attached Order … / Bracket Order … / Trailing Stop Order …" (https://docs-en.itigerup.com/docs/trade-rules). Auction example: "HK auction orders need OPG for the opening auction and DAY for the closing auction" (https://docs-en.itigerup.com/docs/place-order) |
| **Market data subscription** | API data is bought separately from app data. **No ASX package is listed** (US, HK and futures only). Not needed if prices come from EODHD. | "Tiger OpenAPI market data access is separate from access in the desktop and mobile apps and must be purchased separately." (https://docs-en.itigerup.com/docs/fee). Package list: US Stock L1/L2, HK Stock BMP/L2, … (https://docs-en.itigerup.com/docs/permission) |
| **Rate limits** | place/modify: 120/min per method, plus a shared **5 per second per account**. Repeated breaches can blacklist the account. | "`place_order` and `modify_order` share one rate limit per `account`: up to 5 requests per second in total for each account" and "If you repeatedly exceed a rate limit, the system may automatically blacklist the account." (https://docs-en.itigerup.com/docs/ratelimit) |
| **API activation** | Fund the account, then activate on the developer portal (RSA key or OAuth2). No questionnaire is documented. | "Retail investors: Open and fund an account, then activate API access on the API Access Activation Page… Individual users may use signature authentication or OAuth2 authorization" (https://docs-en.itigerup.com/docs/intro) |
| **Fee per ASX order via API** | **A$3 incl. GST** up to A$10k trade value; third-party (exchange/clearing) fees extra. No API surcharge. GST question from report 91: **resolved, GST-inclusive.** | "Brokerage fee for ≤ AUD 10,000 trade value AUD 3 / Order … (2) The fees above are GST inclusive." (https://www.itiger.com/au/invest/asx-stocks). "AUD 3 flat brokerage to buy or sell up to AUD 10,000 per order and 0.03% of trade value after that"; "The third-party fees and other fees still apply." (https://www.itiger.com/au/commissions/fees/stocks_etf?lang=en_US). "Tiger OpenAPI charges no additional fees for trading." (https://docs-en.itigerup.com/docs/fee). The order object has a "gst" field "for orders in the AU and SG markets" (https://docs-en.itigerup.com/docs/appendix-object-detail) |

**Verdict:** ASX live trading through the API is clearly documented and costs A$3 incl. GST. There is no closing-auction order. ASX paper trading is doubtful.

## 3. IBKR (current) — LOC/MOC on ASX

| Question | Finding | Exact quote + URL |
|---|---|---|
| LOC/MOC in the API | **YES as API order types** (`"LOC"`, `"MOC"`), marked for "US and Non-US Products". | "A Limit-on-close (LOC) order will be submitted at the close and will execute if the closing price is at or better than the submitted limit price." with `order.orderType = "LOC"` (https://www.interactivebrokers.com/docs/general/order-types/basic-orders/limit-orders/limit-on-close). MOC: `order.orderType = "MOC"` (https://www.interactivebrokers.com/docs/general/order-types/market-orders/market-on-close). IBKR AU page: "Limit on Close … Products: Stocks, Futures, CFDs, Warrants … Regions: US and Non-US Products"; "Smart routed Limit on close orders are designed to be routed to, and execute on the Primary Listing Exchange of the product." (https://www.interactivebrokers.com.au/en/trading/orders/moc.php) |
| **ASX specifically** | **STILL UNCONFIRMED in writing.** The API page links "More on Supported exchanges" to the exchange matrix, which renders by JavaScript, and its ASX row could not be read. The exchange-specific timing text on the pages covers NYSE/Nasdaq only. | — |
| | **Practical resolution:** GO_LIVE item E1.1 already tests this on the paper gateway ("I check: LOC orders accepted and their cut-off (else the system switches to a 15:30 limit order, `execution.order_type: LMT`)"). That paper test is the authoritative check, and it costs nothing. | GO_LIVE_GUIDE.md §E1 |
| Fees (re-read) | Tiered: 0.08%, **min A$5.00 ex GST** (A$5.50 incl.) plus ASX/clearing pass-through. Fixed: **A$6.00 ex GST** (A$6.60 incl.). | Australia table: "Minimum per order Tier I - AUD 5.00 … [Fixed] AUD 6.00"; tiered adds "Exchange, Clearing and Regulatory Fees" (https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php) |
| Paper | Full ASX paper through the API. The system is already built for it (`DU` accounts). | GO_LIVE_GUIDE.md |

---

## Cost at ~125 orders/yr, about A$550 each

| Option | Per order | Per year | % of A$10k |
|---|---|---|---|
| IBKR fixed | A$6.60 | ≈ A$825 | 8.3% |
| **IBKR tiered** | A$5.50 + pass-through | **≈ A$700–710** | 7.1% |
| Tiger AU / moomoo AU | A$3.00 (+ third-party fees at Tiger) | ≈ A$375–380 | 3.8% |

The saving from switching is **about A$330/yr versus IBKR tiered**.

That saving is partly offset by losing the closing auction. EMG2 trades ranks 301–600, which are small and less liquid stocks. A limit order in continuous trading pays roughly half the bid-ask spread, while the auction pays none. As an *estimate*, a half-spread of 0.3–0.6% on A$550 is about A$1.70–3.30 per order. That is the same size as the A$2.50 fee difference, so the net saving may be anywhere from about A$0 to A$300 a year.

## Recommendation for the A$10k EMG2-18 book

1. **Stay on IBKR for go-live, and switch the pricing plan from fixed to tiered** (≈ A$120–135/yr saved, no code change). Reasons:
   - The system is built and paper-tested on IBKR.
   - It relies on LOC into the closing auction. **Neither moomoo nor Tiger offers a closing-auction order for ASX via API** (both document auction orders for HK only).
   - **Neither has a usable ASX paper account via API.** For moomoo this is explicitly ✗. For Tiger the docs contradict each other.
2. **Confirm ASX LOC on the IBKR paper gateway** during the planned reality spike (E1.1). If IBKR rejects LOC for ASX, the system already falls back to a 15:30 LMT order, and at that point the auction argument for IBKR disappears. That is the trigger to reconsider Tiger.
3. **If the owner later wants the A$3 broker, choose Tiger AU over moomoo AU.**
   - Tiger's ASX live trading is documented consistently, and its A$3 fee is GST-inclusive.
   - Tiger has a mature Python SDK (`tigeropen`) with a `TBAU` licence.
   - moomoo's ASX trading exists only in its new REST WebAPI and is contradicted by its own OpenD docs. Some of its orders can also need a browser confirmation (`jump_url`), which breaks unattended running.
4. **What switching would take in the trading system:**
   - **New adapter.** A new broker module beside `trader/broker/ibkr.py` covering: place LMT orders, cancel, poll status and fills, account cash and positions, and reconciliation.
   - **Order logic change.** `execution.order_type` must become LMT. LOC is not available, so the order time and limit-price rule need re-deciding, for example 15:30–15:55 at bid/ask ± a small buffer.
   - **Replacement safety guards.** The IBKR-specific `DU`/port guards need a broker-neutral equivalent.
   - **Cost reporting.** The Flex-based reconciliation needs Tiger's order/transaction queries instead.
   - **Quotes.** The quote logging (BF-D22) has no ASX API data at Tiger without a package that is not listed. It would use EODHD or record "no quote".
   - **Testing.** Because ASX paper via API is not reliably available, testing would be: unit and mocked tests, then **live canaries with 1–2 minimum-parcel trades at real cost** (minimum A$500 first buy). Expect several days of build and review, plus a canary period.

   This is not worth doing before the 30 Nov decision or the first live months. Revisit after 3–6 months of live IBKR fills, using the measured auction-vs-spread cost from `bf_order_quotes`.

## Still unconfirmed
- The IBKR ASX row in the LOC/MOC exchange matrix. Settle it with the paper-gateway test, or by allowing interactivebrokers.github.io.
- Whether a Tiger AU paper account actually accepts ASX orders (the docs conflict).
- moomoo WebAPI behaviour for AU in practice (this is a new product).
