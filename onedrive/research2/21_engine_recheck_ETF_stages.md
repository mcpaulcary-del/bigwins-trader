# Verification pass for the ETF stages (ASX monthly, then US-listed ETFs)

I re-checked the claims that matter for the two ETF stages, reading pages myself where the host was reachable. Four things in my earlier report were wrong or incomplete and are corrected below; the core Carver numbers held up.

**Access.** WebFetch is still blocked for every host, but `curl` through the session proxy reached `qoppac.blogspot.com`, `www.interactivebrokers.com`, `www.asx.com.au`, `raw.githubusercontent.com` and `pypi.org`, so those were read in full. Still blocked (403): `papers.ssrn.com`, `www.cmegroup.com`, `alphaarchitect.com`, `dtcc.com`, `finra.org`, `ibkb.interactivebrokers.com`. I could not open Carver's books, so book-only numbers stay unverified.

**How to read the tags.** "Read" means I read the page text; "snippet" means a search-result summary only. For "what Carver recommends", the blog, the pysystemtrade code and its docs share one author. I count them as two documents but flag "same origin" where no independent party confirms.

## Corrections to the earlier report

1. **Minimum position rule.** I wrote "at least 4 units at the average forecast (F=10)". Carver's post says the maximum forecast: "I recommend that you are holding at least 4 contracts at the maximum forecast". That is 2 units at F=10, so my rule was twice as strict as the source. The books may state it differently; I could not check.
2. **EWMA span.** I wrote 32 days. The pysystemtrade source and config say 35 (`days: int = 35`; `days: 35`). The 32 figure is from memory of the 2023 book and remains unverified. Either is defensible; 35 is the one I can cite.
3. **Calendar close is not the ASX auction close.** `exchange_calendars` sets XASX close at 16:00 and states "During any pre-trading, post-trading or auction period the exchange is treated as closed." ASX's page shows the closing auction at 16:10–16:11. A job keyed to the library's close would run before the official closing price exists.
4. **Long-only 0–20 forecast mapping.** Carver's post warns that a forecast varying between 0 and +20 averaging +10 has the right average absolute value but roughly half the standard deviation, and says "better still avoid using biased forecasts". My mapping is still usable, but it carries a permanent long bias and lower forecast variability than a symmetric rule. The spec must say so and realised vol must be checked against target.

Smaller fixes:
- ASX tiered pricing has an A$5 minimum (fixed is A$6); I had only quoted the fixed schedule.
- ASX now opens with a single auction at 09:59, not 10:00.
- The pysystemtrade docs name the multiplier cap `div_mult: 2.5` while the code and defaults name it `dm_max: 2.5`. The value agrees; the key name does not.

## Claim table

| # | Claim | Tag | Sources and quotes |
|---|---|---|---|
| 1 | `exchange_calendars` covers XASX and XNYS | [2+ sources, same project] | [PyPI](https://pypi.org/project/exchange-calendars/) (read): calendar list includes `'CMES', 'IEPA', 'XAMS', 'XASX'`; `xcals.get_calendar("XNYS")`. [XASX source](https://raw.githubusercontent.com/gerrymanoim/exchange_calendars/master/exchange_calendars/exchange_calendar_xasx.py) (read): `open_times = ((None, time(10)),)`, `close_times = ((None, time(16)),)`, `regular_early_close = time(14, 10)`. |
| 2 | Calendars are community-maintained and have had XASX errors | [2+ sources] | PyPI README (read): "All of the exchange calendars are maintained by…" user contributions. [4.5.3 release notes](https://newreleases.io/project/github/gerrymanoim/exchange_calendars/release/4.5.3) (snippet): "XASX Dec 2022 early closes fix (#374)". |
| 3 | Library treats auctions as closed; ASX closing auction is 16:10–16:11 | [2+ sources, independent] | PyPI README quote above. [ASX trading hours](https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours) (read): "16:00:00 - 16:10:00 Pre CSPA; 16:10:00^ - 16:11:00 Closing Single Price Auction; 16:11:00 – 16:21:30 Post Close". |
| 4 | ASX opening auction is a single auction at 09:59 | [2+ sources] | ASX page (read): "The Opening Auction takes place at 09:59:00 (randomised 15 seconds)". [Bell Direct](https://belldirect.com.au/asx-trading-changes) and [Motley Fool](https://www.fool.com.au/2025/06/23/important-changes-to-asx-trading-times/) (snippets) describe the June 2025 timing change. |
| 5 | ARCX / XNAS calendars exist in the library | [unverified] | Not checked. XNYS holidays cover US-listed ETFs in practice; confirm at build. |
| 6 | IBKR session hours are available per contract for cross-checking | [1 source] | [ib_async API docs](https://ib-api-reloaded.github.io/ib_async/api.html) (read): `ContractDetails.timeZoneId`, `ContractDetails.tradingHours`, `ContractDetails.liquidHours`. |
| 7 | Fractional or cash-quantity stock orders are not supported by IBKR's APIs | [2+ sources, independent] | [IBKR order-type notes](https://www.interactivebrokers.com/docs/general/order-types/notes-limitations/introduction) (read): "Interacive Brokers APIs do not support fractional or cash quantity trading with exception to Cryptocurrencies and Forex trading." [ib_insync discussion 706](https://github.com/erdewit/ib_insync/discussions/706) (snippet): IBKR "has never supported fractional equity shares via the API". [IBKR order types page](https://www.interactivebrokers.com/en/trading/orders/fractional-share-orders.php) (read): "Platforms: TWS, IBKR Desktop, IBKR Mobile, Client Portal" — no API. |
| 8 | Fractional eligibility excludes ASX | [1 source] | Same IBKR page (read): "any eligible US, Canadian or European stock (or ETF, where available)". |
| 9 | Web API changelog mentions stock `cashQty` | [1 source, snippet] | [Web API changelog](https://www.interactivebrokers.com/docs/web-api/changelog). Conflicts in spirit with row 7; it is a different API from the one ib_async uses. |
| 10 | ASX commission: fixed 0.08%, min A$6; tiered 0.08% (tier I), min A$5 plus third-party fees | [2+ sources] | [IBKR Asia-Pacific stocks](https://www.interactivebrokers.com/en/pricing/commissions-stocks-asia-pacific.php) (read): "≤ 3,000,000 Tier I - 0.08% of Trade Value / 0.08% of Trade Value"; "Minimum per order Tier I - AUD 5.00 … AUD 6.00"; "Fixed Example: 400 Shares @ AUD 50 Share Price = AUD 16.00". [Invezz review](https://invezz.com/au/reviews/interactive-brokers-review-australia/) (snippet): "from AUD 6.00 per trade or 0.08%". |
| 11 | US commission: fixed US$0.005/share, min US$1.00, max 1% of trade value; tiered US$0.0035/share, min US$0.35, plus fees | [2+ sources] | [IBKR stocks commissions](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php) (read): "USD 0.0035 / USD 0.005"; "Minimum per order USD 0.35 / USD 1.00"; "Maximum per order 1% of Trade Value". Review sites (snippet) repeat US$0.005 and US$1. |
| 12 | IBKR Lite ($0 commission) is not available to Australians | [1 source] | Same page (read): Lite eligibility "US Residents Only". |
| 13 | FX conversion: 0.20 basis points of trade value, minimum US$2 per order | [1 source, primary] | [IBKR spot currency commissions](https://www.interactivebrokers.com/en/pricing/commissions-spot-currencies.php) (read): "0.20 basis point * Trade Value"; "Minimum per order Tier I - USD 2.00". No second source found. |
| 14 | ASX equities settle T+2 | [1 source, primary] | [ASX Settlement](https://www.asx.com.au/markets/clearing-and-settlement-services/asx-settlement) (read): "automatically settles equity trades two business days after they take place (T+2)". The page also links "Communications regarding the T+1 settlement cycle"; status of any ASX move to T+1 is unverified. |
| 15 | US securities settle T+1 since 28 May 2024 | [2+ sources, snippets] | [SEC press release](https://www.sec.gov/news/press-release/2024-62), [Davis Polk](https://www.davispolk.com/insights/client-update/sec-adopts-t-1-settlement-effective-may-2024), [DTCC](https://www.dtcc.com/insights/2023/sec-announces-t1-implementation-date). None names ETFs specifically. |
| 16 | IBKR cash accounts cannot run a debit balance; settled cash is checked at order entry; free-riding leads to a 90-day restriction | [2+ sources, snippets] | [IBKR KB 3101](https://ibkb.interactivebrokers.com/de/node/3101), [IBKR KB 814](https://ibkb.interactivebrokers.com/es/node/814), [Mustachian Post](https://www.mustachianpost.com/ibkr-insufficient-settled-cash/). Pages not readable from here. Whether FX conversion on unsettled funds triggers it is unverified. |
| 17 | IBKR holds ASX shares in custody, not on an individual HIN | [1 source, snippet] | Review-site search result. Not an engine matter, but the owner should know. |
| 18 | Vol estimate: EWMA with 35-day lookback | [2+ sources, same origin] | [vol.py](https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/sysquant/estimators/vol.py) (read): `days: int = 35`. [defaults.yaml](https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/sysdata/config/defaults.yaml) (read): `days: 35`, `min_periods: 10`. |
| 19 | Vol blend: 70% current, 30% ten-year average | [2+ sources] | defaults.yaml (read): `func: "sysquant.estimators.vol.mixed_vol_calc"`, `slow_vol_years: 10`, `proportion_of_slow_vol: 0.3`. [QuantConnect re-creation](https://www.quantconnect.com/research/15989/futures-trend-following-and-carry-in-different-risk-regimes/) (snippet): 30% ten-year average plus 70% current. Disagreement: the function's own default is `slow_vol_years: int = 20`; the config overrides it to 10. |
| 20 | Forecasts scaled to average absolute 10, capped at 20 | [2+ sources] | defaults.yaml (read): `forecast_cap: 20.0`, `average_absolute_forecast: 10.0`. [Carver 2016](https://qoppac.blogspot.com/2016/01/pysystemtrader-estimated-forecast.html) (read): "the correct average absolute value, normally 10". |
| 21 | Scalars pooled across instruments, median, long window | [2+ sources, same origin] | Same post (read): "I prefer the median… more robust"; "Pool data across instruments". defaults.yaml: `pool_instruments: True`, `window: 250000`, `min_periods: 500`. |
| 22 | Diversification multiplier = 1/sqrt(W·H·Wᵀ), capped at 2.5, negative correlations floored at zero, weekly returns, smoothed | [2+ sources, same origin] | [diversification_multipliers.py](https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/sysquant/estimators/diversification_multipliers.py) (read): "the diversification multiplier will be 1 / [ ( W x H x WT ) 1/2 ]"; `dm_max: float = 2.5`. [Carver 2016](https://qoppac.blogspot.com/2016/01/correlations-weights-multipliers.html) (read): "I also floor negative correlations to avoid getting very large values for the multiplier"; "correlations of daily returns tend to be unrealistically low". defaults.yaml: `frequency: "W"`, `ewma_span: 125`. |
| 23 | Position = vol scalar × forecast / 10, where vol scalar = cash vol target / (unit value × % vol × FX) | [2+ sources] | [positionsizing.py](https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/systems/positionsizing.py) (read): `subsystem_position_raw = vol_scalar * forecast / avg_abs_forecast`; `vol_scalar = cash_vol_target / instr_value_vol`; `instr_value_vol = instr_ccy_vol.ffill() * fx_rate`. QuantConnect re-creation (snippet) gives the same formula. |
| 24 | Buffer = 10% of average position (position at forecast 10), trade to the edge | [2+ sources] | [backtesting.md](https://raw.githubusercontent.com/robcarver17/pysystemtrade/master/docs/backtesting.md) (read): "we take a proportion of the average absolute position (what we get with a forecast of 10)… we trade to the nearest edge of the buffer… my recommended settings: `buffer_trade_to_edge: True`, `buffer_method: forecast`, `buffer_size: 0.10`". [7circles on Leveraged Trading](https://the7circles.uk/?p=27928) (snippet): trades only when off by more than 10% of average exposure. |
| 25 | Speed limit: drop rules whose cost exceeds 0.13 SR a year | [2+ sources] | defaults.yaml (read): "Set this to 0.13 to enforce the speed limit". backtesting.md (read): "`ceiling_cost_SR: 0.13` ## Max cost to allow for assets, annual SR units". [Carver gist](https://gist.github.com/robcarver17/795d11b977261065d1f0da68eb95624f) (read): `max_cost = 0.13 / rule_turnover`. [7circles](https://the7circles.uk/?p=24243) (snippet): one third of an SR of 0.4. Note the shipped default is 999 (off). |
| 26 | Minimum position: 4 units at maximum forecast | [1 source] | [Carver 2016](https://qoppac.blogspot.com/2016/03/diversification-and-small-account-size.html) (read): quote in correction 1. |
| 27 | Shares with minimum fees are uneconomic below about £1,000 per trade | [1 source] | Same post (read): "With trades in shares having minimum fees it isn't economic to trade in amounts of less than £1,000 or so." |
| 28 | Small-account instrument selection: choose by asset class and achievable position size | [1 source] | Same post (read): "narrow down the selection criteria to just two: asset class, and maximum position size". |
| 29 | Inverse-vol / risk parity / handcrafting as robust weighting | [1 source] | [Carver 2018](https://qoppac.blogspot.com/2018/12/portfolio-construction-through.html) (read): lists "Risk parity: Equally weight each asset class; Inverse volatility weighting". DeMiguel et al. (1/N) not re-read. |
| 30 | Handcrafting is pysystemtrade's default weighting method | [1 source] | defaults.yaml (read): `method: handcraft`. |
| 31 | Vol target of 10–12% for long-only ETF accounts | [unverified] | My proposal. pysystemtrade's `percentage_vol_target: 16.0` is a config default, not advice. |
| 32 | Commission-per-trade ceiling of 0.25%, A$500 minimum trade, 5% drift band | [unverified] | My proposals; to be set by backtest. |
| 33 | Tracking-error greedy optimisation for small accounts | deferred | [Carver Oct 2021](https://qoppac.blogspot.com/2021/10/mr-greedy-and-tale-of-minimum-tracking.html) (read): his own update says "It didn't work, at least not as well as I'd hoped"; the November 2021 version with buffering is what he uses. pysystemtrade defaults: `shadow_cost: 50`, `tracking_error_buffer: 0.0125`. Futures-only; not needed for ETFs. |
| 34 | Futures items (rolls, back-adjustment, micro contract specs, margins) | deferred | CME host blocked. |
| 35 | Crypto items | deferred | — |
| 36 | DSR / PBO formulas, vol-managed portfolio literature | [unverified this pass] | SSRN blocked; outside the narrowed scope. |

## Cost arithmetic that follows from the verified numbers

- **ASX, fixed pricing:** the A$6 minimum binds below A$7,500. A A$2,500 switch costs 0.24% one-way; A$1,000 costs 0.60%.
- **US, fixed pricing:** US$1 minimum; a US$1,000 trade costs 0.10% plus the FX leg.
- **FX leg:** the US$2 minimum dominates below about US$1m. Converting the equivalent of US$1,650 (roughly A$2,500) costs about 0.12% each way.
- **Round trip for the A$5k account into a US ETF and back:** two FX legs plus two trades, roughly US$6 on US$1,650, about 0.36%, against 0.48% for two ASX legs. The saving is small and brings FX exposure and currency-cash handling with it.

## Decisions for the spec (ETF stages)

**Calendars and scheduling**
- **D1.** Use `exchange_calendars` (pinned) for session dates only: XASX for ASX, XNYS for US-listed ETFs.
- **D2.** Do not take auction times from the library. Hold venue config for auction windows: ASX close auction 16:10–16:11, post-close to 16:21:30, opening auction 09:59. ASX signal run starts no earlier than 16:25 Sydney.
- **D3.** Cross-check each session against IBKR `ContractDetails.tradingHours` / `liquidHours` before sending orders. On mismatch, do not trade that venue and alert.
- **D4.** Add an annual task to diff the library's XASX holidays and early closes (14:10 in the library) against the ASX published calendar.

**Orders and quantities**
- **D5.** Whole units only on every venue. `size_increment = 1` is fixed in config for stocks and ETFs; `cashQty` is never set on stock orders.
- **D6.** Commission models, with values as verified in rows 10–13:
  - `asx_fixed` (0.08%, min A$6) is the default.
  - `asx_tiered` (0.08%, min A$5, plus exchange fees) is an alternative.
  - `us_fixed` (US$0.005/share, min US$1, cap 1%) and `us_tiered` (US$0.0035/share, min US$0.35, cap 1%, plus fees).
  - `fx` (0.00002 × value, min US$2).
  - Which IBKR plan the two accounts are on is unknown and must be read from the account.
- **D7.** Reconcile modelled against charged commission monthly; a persistent gap above 10% raises a config review.

**Cash and currency**
- **D8.** Ledger tracks settled and unsettled cash per currency: ASX T+2, US T+1. Buy orders are sized against settled cash only, unless the account is confirmed as margin type.
- **D9.** No debit balance in any currency. FX conversion is an explicit, costed order placed before the security order, never left to automatic borrowing.
- **D10.** FX conversions below a configurable floor are not made (proposed US$2,000, where the US$2 minimum is 0.10%).
- **D11.** NAV is computed in AUD from one FX snapshot per run; each instrument's last close is tagged with its session date.

**Volatility, forecasts, sizing**
- **D12.** Vol: EWMA with 35-day lookback, minimum 10 observations, blended 70/30 with the ten-year average of itself, using all history when under ten years. If the existing ASX spec already fixes a span between 30 and 36, keep it.
- **D13.** Forecast scale: average absolute 10, cap ±20. Scalars are fixed in config, pooled across instruments, estimated by median.
- **D14.** The eight binary tests map to a 0–20 long-only forecast. The spec states that this is a biased forecast with lower variability than a symmetric one, and the backtest must report realised against target vol; one global scalar may be fixed once to correct it.
- **D15.** Forecast and instrument diversification multipliers: 1/sqrt(wᵀρw), weekly returns, negative correlations floored at zero, capped at 2.5, smoothed with a 125-day EWMA. With two to six ETFs, expect values well below the cap.
- **D16.** Sizing formula as in pysystemtrade (row 23), in AUD risk terms with FX applied to foreign instruments.
- **D17.** Buffer: 10% of the position at forecast 10, trade to the edge, applied before rounding to whole units.
- **D18.** Speed limit 0.13 SR a year per rule per instrument, computed from the D6 cost models. It is on by default in this system, unlike pysystemtrade's shipped default.

**Small accounts**
- **D19.** Eligibility for an ETF in an account: at least 4 units at maximum forecast, and typical rebalance trade large enough that commission stays under a configurable ceiling (proposed 0.25%, unverified).
- **D20.** Instrument weights are handcrafted: equal risk across asset classes, then equal within class. No return-based optimisation.
- **D21.** The A$5k account stays ASX-only on the monthly VAS/VGS/cash switch, with a no-trade band (proposed: skip trades under A$500 or drift under 5% of NAV, unverified). US ETFs are excluded for it on the cost arithmetic above.
- **D22.** The US ETF stage applies to the large account only, after three months of paper trading on that venue.

**Deferred**
- **D23.** Futures (rolls, back-adjustment, tracking-error optimisation, margin) and crypto are out of the ETF stages. The `Instrument` model keeps the optional fields so they can be added without a schema change.

## Open items the owner must settle

- Account type (cash or margin) and pricing plan (fixed or tiered) for both IBKR accounts; D8 and D6 depend on them.
- Whether ASX is moving to T+1 and when; D8 uses T+2 until confirmed.
- The IBKR API order type for the ASX closing auction; not verified in either pass.
- The vol target and the three thresholds in D19 and D21 are my proposals and need backtest support.
- Carver's book figures (32-day span, minimum capital wording) could not be checked against the books.