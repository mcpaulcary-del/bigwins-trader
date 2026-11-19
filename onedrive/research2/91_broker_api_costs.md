# 91 — Broker API costs for ASX order automation (EMG2-18)

Research date: 2026-11-19. Web only; no sign-ups, credentials or trading.

**How this was researched (important caveat):** in this session, direct page fetches to broker sites failed. The hosts did not resolve: openapi.moomoo.com, openapi.futunn.com, docs-en.itigerup.com and www.itiger.com. Everything below therefore comes from search-engine extracts of the official pages listed. Quotes are as the search tool returned them; they were **not read in full on the live page**. Anything marked **UNCONFIRMED** must be checked on the page itself, or inside the app or OpenD, before you commit money.

Assumptions: 128 orders a year at about A$550 each; A$10,000 account; all fees include GST unless stated.

## Comparison table

| Broker | API places/cancels ASX orders for an AU retail account? | Evidence (official source + quote) | Order types incl. closing auction | Brokerage per A$550 order | Est. yearly cost (128 orders) | Paper trading for ASX via API | Setup steps | Risks / unknowns |
|---|---|---|---|---|---|---|---|---|
| **moomoo AU** (Futu; AFSL holder, CHESS-sponsored) | **Likely YES (documented, not live-tested).** | open.moomoo.com/api/overview: trading covers Australia; the Overview table marks *Live Trading – Moomoo AU – Australian stocks* as available. openapi.moomoo.com trade definitions: `TrdMarket_AU = 8; //AU market`, min OpenD 9.0.5008. Modify/cancel uses the same `modify_order` endpoint as other markets. moomoo help (SG/US topic3_436): "no additional charge for trading via Moomoo API". | In the app, AU orders are Limit, Market, **Market On Close**, VWAP and POV (moomoo AU manual topic-14-183). AU help says market orders are sometimes disabled for illiquid stocks. **Whether MOC/auction types are exposed through the API for AU is UNCONFIRMED.** Limit orders are safe to assume. | max(A$3, 0.03%) incl GST, so **A$3.00** (moomoo AU's own "moomoo vs CommSec" page; third parties agree; one Finder table shows A$6.60, likely stale or wrong). | **≈ A$384** (3.8% of capital) | **Conflicting.** The Overview table marks AU-stock paper trading as ✗. The changelog (2026-05-21) mentions AU paper *competition* accounts, and the Q&A shows moomoo AU paper for **US** stocks only. **Treat ASX paper via API as NOT available.** | Open moomoo AU account (CHESS HIN) → install OpenD (local or cloud) → log in → complete the **API Questionnaire and Agreements** (required on first login) → unlock trade with trading password → `OpenSecTradeContext(filter_trdmarket=TrdMarket.AU, security_firm=FUTUAU…)`. | (1) **AU market data via API is shown as ✗ for moomoo users**, so you would need EOD/quote data from elsewhere (fine for EMG2-18 if signals are EOD). (2) AU code format and `SecurityFirm` value were not seen in docs (UNCONFIRMED). (3) Rate limit per API; place_order limit not confirmed (Futu docs historically say 15 per 30 s per account, UNCONFIRMED). (4) OpenD must run continuously. |
| **Tiger Brokers AU** (TBAU, AFSL 300767; CHESS via Openmarkets) | **Likely YES (documented).** | docs-en.itigerup.com: products table lists "Australia: Stocks, ETFs" for Prime and paper accounts. "API trading fees are the same as the app; no extra API fee". Market data is bought separately for the API. Java SDK references list licence `TBAU`. | Market, limit, stop, stop-limit, trailing stop, attached orders, plus TWAP/VWAP (generic, not AU-specific). **ASX closing-auction / MOC via API: UNCONFIRMED, not seen.** | A$3/order for trades ≤ A$10k (itiger.com/au commissions page: "Brokerage fee for ≤ AUD 10,000 trade value AUD 3 / Order"), so **A$3.00**. GST treatment unconfirmed. | **≈ A$384** | Docs list paper accounts with Australia stocks/ETFs, so **probably yes** (UNCONFIRMED in practice). | Open TBAU account → apply for OpenAPI developer access on the Tiger site (generate RSA key pair, tiger_id) → install `tigeropen` Python SDK → set license TBAU → place/cancel via `TradeClient`. | No AU-specific code example found. Paper accounts "may have extra restrictions". API market-data subscription costs extra. Smaller broker, with clearing via Openmarkets. |
| **Interactive Brokers AU** (current plan) | **YES (established).** | interactivebrokers.com.au pricing page (Asia-Pacific stocks). TWS API and Client Portal API support ASX stocks. | Limit, market, MOC, LOC, many others. MOC/LOC smart-routed to the primary exchange (IBKR order-types page). **ASX specifically in the MOC/LOC "supported exchanges" table: UNCONFIRMED** (not shown in extracts; check orderTypesMatrix for ASX). | **Fixed:** 0.08%, min A$6.00 ex GST, so **A$6.60** incl GST. **Tiered:** 0.08% for low volume, min A$5.00 ex GST (A$5.50) **plus** exchange/clearing fees passed through (a few cents at A$550). | Fixed **≈ A$845**; Tiered **≈ A$710–720** (UNCONFIRMED exact pass-through fees) | **YES**: IBKR paper account mirrors ASX via API. | Already planned (TWS/IB Gateway + API). | Highest cost. Tiered vs fixed min to re-verify on the live page. Possible market-data subscription for ASX quotes. |
| **Webull AU** | **NO (currently).** | developer.webull.com.au Trading API overview: supported-products table lists only "Stocks: US Equities". webull.com.au/open-api lists "AU Shares" but Markets shows US only, "expanded offerings in development". | n/a | n/a | n/a | n/a | — | Watch for ASX API launch. |
| **Saxo AU → "Totality"** (DMA-owned since 2025) | **UNCONFIRMED.** | Saxo sold 80.1% of Saxo Australia to DMA (2025), now rebranded Totality. Existing retail clients were kept. No current evidence that Saxo OpenAPI is offered to AU retail. | — | Unknown | Unknown | Saxo had a SIM env historically | — | Ownership change; not recommended without direct confirmation. |
| CMC Invest / CommSec / SelfWealth / Stake | **No public retail trading API for ASX shares found.** | — | — | — | — | — | — | — |

## Bottom line / recommendation

1. **Cost:** moomoo AU or Tiger AU at **A$3/order is about A$384 a year** for 128 orders, against **≈ A$845 at IBKR fixed** (≈ A$710 tiered). The saving is **≈ A$330–460 a year (3.3–4.6% of capital)**, which is material for a A$10k account.
2. **Preferred candidate: moomoo AU.** Official docs show a dedicated `TrdMarket_AU` enum and "Live trading – Moomoo AU – Australian stocks: ✓". There is no API surcharge, holdings are CHESS-sponsored, and API onboarding (OpenD + questionnaire) is free. Main gaps: **no ASX paper trading via API**, **no AU market data via API**, and **closing-auction (MOC) via API unconfirmed.** Mitigation: use limit orders, source signals and prices from EOD data, and validate with 1–2 tiny live orders.
3. **Fallback: Tiger AU.** Same A$3 fee, and docs list Australia for live and paper. It has less AU-specific evidence.
4. **Keep IBKR** only if the strategy truly needs ASX closing-auction orders via API, or a full ASX paper environment. Even then, consider IBKR **tiered** (≈ A$140/yr cheaper than fixed, pending verification).
5. **Before switching:** allow the doc hosts (openapi.moomoo.com, open.moomoo.com, docs-en.itigerup.com, www.itiger.com) and re-verify:
   - the AU row of moomoo's Overview table;
   - the AU order types in the place_order docs (MOC / at-auction);
   - the place_order rate limit;
   - Tiger's ASX fee GST treatment;
   - the IBKR ASX MOC/LOC support matrix.

## Sources (accessed 2026-11-19 via search extracts)
- moomoo OpenAPI overview: https://open.moomoo.com/api/overview
- moomoo trade definitions (TrdMarket_AU): https://openapi.moomoo.com/moomoo-api-doc/en/trade/trade.html
- moomoo Q&A transaction: https://openapi.moomoo.com/moomoo-api-doc/en/qa/trade.html
- moomoo changelog (2026-05-21 AU paper competition): https://openapi.moomoo.com/moomoo-api-doc/en/changelog/changelog.html
- moomoo Python doc (API questionnaire): https://openapi.moomoo.com/mds/moomoo-API-Doc-en-Python.md
- moomoo authorities/limits: https://openapi.moomoo.com/moomoo-api-doc/en/intro/authority.html
- moomoo AU order types manual: https://www.moomoo.com/au/manual/topic-14-183
- moomoo vs CommSec (A$3 / 0.03% GST incl): https://www.moomoo.com/au/learn/moomoo-vs-commsec
- moomoo API help (no extra charge): https://www.moomoo.com/sg/support/topic3_436
- Tiger OpenAPI docs: https://docs-en.itigerup.com/ ; https://quant.itigerup.com/openapi/en/cpp/overview/introduction.html
- Tiger SDK: https://github.com/tigerfintech/openapi-python-sdk
- Tiger AU ASX fees: https://www.itiger.com/au/commissions/fees/stocks_etf?lang=en_US ; https://www.itiger.com/au/invest/asx-stocks
- IBKR AU APAC stock commissions: https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php
- IBKR order types: https://www.interactivebrokers.com.au/en/trading/ordertypes.php ; https://interactivebrokers.github.io/tws-api/basic_orders.html
- Webull AU API: https://developer.webull.com.au/apis/docs/trade-api/overview/ ; https://www.webull.com.au/open-api
- Saxo AU sale: https://www.financemagnates.com/forex/saxo-australia-has-been-sold-to-a-south-african-trading-technology-provider/
