# Market-agnostic, adaptive design for the EOD trading system: research and spec recommendations

**Evidence status.** WebFetch could not reach `qoppac.blogspot.com` or `www.interactivebrokers.com.au` (both outside this session's network allowlist), so nothing was read from a primary page. Claims marked **[S]** come from search-result summaries, **[M]** are from memory of the books and papers and were not re-checked, and **[U]** are unverified and must be confirmed before coding. No backtests were run; every threshold below is a proposed default.

## 0. Key findings

1. **"Varies to suit" should mean structural adaptivity, not parameter adaptivity.** One fixed, pre-registered rule set is applied everywhere. What varies per market is derived mechanically from measured volatility, costs, correlations, contract size and capital.
2. **CME micro futures do not fit the A$5k account, and barely fit below roughly A$150k.** At a 20% vol target, one MES contract held as a single instrument needs on the order of US$100k by Carver's 4-contract rule (my arithmetic, [U] on index level). The small account stays on ETFs.
3. **IBKR fractional shares are not usable through the TWS API** (which ib_async wraps). IBKR's docs say its APIs do not support fractional or cash-quantity trading except for crypto and forex [S]. The Web API changelog mentions stock `cashQty`, but that is a different product [S]. Design for whole units.
4. **The existing 8 binary trend tests are already a lookback ensemble.** Convert the vote count to a capped, scaled forecast and the rest of the Carver sizing chain applies without re-fitting anything.
5. **Validation must count every variant ever tried** and deflate for it (Deflated Sharpe Ratio, PBO). Adding markets is itself a multiple-testing act.

## 1. Market-agnostic architecture

### 1.1 How the open-source systems do it

| System | Useful pattern | Take / leave |
|---|---|---|
| **pysystemtrade** (Carver) | Per-instrument config (point value, currency, asset class, costs) and per-instrument roll config (`RollOffsetDays`, `CarryOffset`, `ExpiryOffset`) [S]. Separate price series: per-contract, "multiple" (current/forward/carry) and back-adjusted [M]. Pipeline stages: rules, scaling, combination, sizing, portfolio, buffering. | Take the stage pipeline and roll-parameter model. Leave the MongoDB/Parquet production stack. |
| **NautilusTrader** | Typed instrument classes (Equity, FuturesContract, CurrencyPair, CryptoPerpetual) with `price_increment`, `size_increment`, `multiplier`, `lot_size`, margin rates, maker/taker fees and optional min/max quantity and notional [S]. | Take the typed fields and the "validate order against instrument before sending" idea. |
| **LEAN** | Static per-symbol data (`SymbolProperties`: lot size, min price variation) and a `MarketHoursDatabase`, kept apart from pluggable per-security models (Fee, Fill, Slippage, BuyingPower) [S]. A brokerage model reportedly sets these as a bundle [U]. | Take the split between static data and swappable models. |
| **exchange_calendars** (successor to zipline's trading_calendars) | Calendars keyed by ISO 10383 MIC (`XASX`, `XNYS`, `CMES`), with sessions, opens/closes and early closes maintained per calendar [S]. | Use directly. Pin the version and reconcile against IBKR `ContractDetails.tradingHours` daily, because calendar bugs do occur (the changelog shows an XASX early-close fix [S]). |

### 1.2 Design principles

- **Per-venue session clock.** Replace the single "ASX end-of-day" job with one job per venue session, each with a decision time after that venue's close. Every bar carries an `as_of_session` and `venue` tag.
- **NAV at a fixed UTC cut.** Use the last close per instrument and flag stale marks. Value FX at one snapshot rate per run.
- **Three futures price series.** Use actual contract prices for orders and notional. Use a difference ("Panama") back-adjusted series for trend signals and volatility in price units. Derive percentage vol as `σ(Δ back-adjusted) / current contract price`. Never take percentage returns of a back-adjusted series, which can pass through zero [M].
- **Rolls are their own order type.** A roll is not a signal change and is costed separately. Hard guard: flatten or roll before first notice day or last trade day, ahead of IBKR's own close-out deadline [U on exact deadlines].
- **Multi-currency.** Positions are sized in base-currency (AUD) risk terms. For futures, only margin and P&L are FX-exposed; for foreign ETFs the full notional is. Model both explicitly. Config needs a policy per currency: hold foreign cash, sweep to AUD above a threshold, or permit a margin loan (default off).
- **Tax flags are metadata, not signals.** They are consumed by reporting and an optional tie-breaker.

### 1.3 Python data model sketch

```python
from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Protocol, Literal

class AssetType(Enum):
    STOCK = "stock"; ETF = "etf"; FUTURE = "future"; CRYPTO = "crypto"; FX = "fx"

class AssetClass(Enum):
    EQUITY_AU = "eq_au"; EQUITY_GLOBAL = "eq_glob"; BOND = "bond"
    METAL = "metal"; ENERGY = "energy"; FX = "fx"; CRYPTO = "crypto"; CASH = "cash"

@dataclass(frozen=True)
class TickRule:                 # price-banded tick table
    min_price: Decimal          # band lower bound (inclusive)
    tick: Decimal

@dataclass(frozen=True)
class Venue:
    mic: str                    # "XASX", "XNYS", "ARCX", "CMES"/"XCME"
    ib_exchange: str            # "ASX", "SMART", "CME", "COMEX", "NYMEX", "PAXOS"
    calendar: str               # exchange_calendars key
    tz: str                     # "Australia/Sydney", "America/New_York", "America/Chicago"
    currency: str
    has_close_auction: bool
    close_auction_order: Literal["MOC", "LOC", "AUCTION_LMT", None]
    decision_offset_min: int    # minutes after official close to run signals
    order_window: tuple[time, time]   # local time window in which orders may be worked
    tick_table: tuple[TickRule, ...]
    settlement_days: int        # T+N for cash availability
    commission_model: str       # key into the CommissionModel registry

class CommissionModel(Protocol):
    def estimate(self, qty: Decimal, price: Decimal, inst: "Instrument") -> Decimal: ...

@dataclass(frozen=True)
class PctWithMin:               # e.g. ASX: pct of value with a minimum
    pct: Decimal; minimum: Decimal; currency: str
    def estimate(self, qty, price, inst): return max(self.minimum, abs(qty)*price*self.pct)

@dataclass(frozen=True)
class PerUnitWithMinMax:        # e.g. US shares: per share, min, max % of value
    per_unit: Decimal; minimum: Decimal; max_pct: Decimal; currency: str

@dataclass(frozen=True)
class PerContract:              # futures: broker + exchange + regulatory
    broker: Decimal; exchange: Decimal; regulatory: Decimal; currency: str

@dataclass(frozen=True)
class TaxFlags:
    cgt_discount_eligible: bool       # AU 12-month discount possible
    franking: bool                    # 45-day holding rule relevant
    us_withholding: bool              # W-8BEN dividend withholding
    us_situs_estate_risk: bool
    revenue_account_likely: bool      # futures / frequent trading

@dataclass(frozen=True)
class RollSpec:
    cycle: str                        # "HMUZ", "GJMQZ", "FGHJKMNQUVXZ"
    roll_offset_days: int             # calendar days before expiry to roll
    expiry_rule: str                  # symbolic rule or "from_ib"
    first_notice_guard_days: int | None   # physically delivered contracts
    hold_position: int = 0            # 0 = front, 1 = second
    adjust_method: Literal["panama_diff", "ratio"] = "panama_diff"
    roll_execution: Literal["calendar_spread", "two_legs"] = "two_legs"

@dataclass(frozen=True)
class ExecutionPolicy:
    entry: Literal["close_auction", "next_open_auction", "limit_passive", "adaptive_mkt"]
    exit: Literal["close_auction", "adaptive_mkt", "stop_at_broker", "stop_synthetic"]
    max_participation_adv: Decimal    # fraction of 20-day ADV
    max_spread_bps: Decimal           # skip/defer if quoted spread wider
    limit_offset_ticks: int
    allow_outside_rth: bool = False

@dataclass(frozen=True)
class Instrument:
    key: str                          # internal id, e.g. "VAS.XASX", "MES.CME"
    asset_type: AssetType
    asset_class: AssetClass
    venue: Venue
    currency: str
    multiplier: Decimal = Decimal(1)  # contract point value; 1 for shares
    lot_size: Decimal = Decimal(1)
    size_increment: Decimal = Decimal(1)   # <1 only where the API allows it
    min_notional: Decimal | None = None
    ib_conid: int | None = None       # None for futures roots; resolved per contract
    roll: RollSpec | None = None
    exec_policy: ExecutionPolicy | None = None
    tax: TaxFlags | None = None
    shortable: bool = False
    history_start: date | None = None
    proxy_key: str | None = None      # longer-history proxy for research/vol priors
    enabled_rules: tuple[str, ...] = ()    # filled by the cost filter, not by hand
    account_eligibility: tuple[str, ...] = ()

@dataclass
class CashLedger:
    base_ccy: str
    balances: dict[str, Decimal] = field(default_factory=dict)
    def nav(self, positions_value_by_ccy: dict[str, Decimal], fx: dict[str, Decimal]) -> Decimal:
        ccys = set(self.balances) | set(positions_value_by_ccy)
        return sum((self.balances.get(c, 0) + positions_value_by_ccy.get(c, 0)) * fx[c] for c in ccys)

class RollCalendar(Protocol):
    def current_contract(self, root: str, on: date) -> str: ...
    def roll_due(self, root: str, on: date) -> bool: ...

class PriceStore(Protocol):
    def contract_prices(self, key: str): ...       # actual tradable prices
    def adjusted_prices(self, key: str): ...       # back-adjusted, for signals
    def fx_rate(self, ccy: str, base: str, on: date) -> Decimal: ...
```

### 1.4 Execution policy by type

| Type | Policy | Notes |
|---|---|---|
| ASX stock/ETF | Closing auction (CSPA). | Pre-CSPA runs 16:00–16:10 with a randomised match around 16:10; timings changed in June 2025 [S]. Re-verify the current schedule and IBKR's ASX auction order type [U]. For ETFs, avoid the first and last minutes of continuous trading, when market-maker spreads widen [M]. |
| US ETF | MOC/LOC into the closing auction, or a passive limit in the final 30 minutes. | The session is overnight Sydney time, so orders are staged by the scheduler. NYSE/Nasdaq MOC cut-off times apply [U]. |
| Micro futures | Limit at the touch, or IBKR Adaptive, during liquid US hours. Never trade the thin Asian session on market orders. | Rolls go by spread where IBKR supports it for the product [U]. |
| Crypto | Prefer exchange-listed spot ETFs, so crypto is "just another ETF" on an existing venue. | Direct IBKR crypto (Paxos/Zero Hash) for Australian retail is reported by only one review site [S][U]. CME MBT/MET micros hit the same capital problem as MES. |

**Commissions (confirm on IBKR's own pages):**
- ASX fixed pricing is about 0.08% with an A$6 minimum [S, review site]. A A$1,000 trade therefore costs 0.6% one-way, and the minimum stops binding at A$7,500.
- US shares are US$0.005 per share fixed, with a reported US$1 minimum [S].
- CME micros (MES tier) are US$0.25 per contract plus exchange and regulatory fees [S; exchange fee not found].
- FX conversion cost is [U].

## 2. Adaptivity without overfitting

### 2.1 What the literature supports

- **(a) Ensembles beat selection.** ReSolve found walk-forward selection of specifications added nothing over a naive ensemble. Newfound found little persistence in which lookback (21–378 days) performed best [S]. A 2025 arXiv paper argues dynamic horizon weighting can help, but this is an open question, not established [S]. Carver's position is fixed or handcrafted weights and scalars pooled across instruments on an expanding window [S].
- **(b) Vol targeting is mainly risk control.** Moreira and Muir (2017) found positive alphas for volatility-managed portfolios. Cederburg et al. found they do not systematically beat unmanaged portfolios out of sample, and Barroso and Detzel found none survive costs [S]. Harvey et al. (2018) report vol targeting stabilises realised vol and reduces tail risk for equity-like assets [M]. Use it for risk, not for expected extra return.
- **(c) Speed limit.** Carver's rule is that costs should be at most one third of a conservative pre-cost Sharpe ratio (SR). That gives about 0.13 SR per year for a subsystem SR of 0.4, and 0.08 for slower asset-allocating systems. Annual cost equals turnover times round-trip cost in SR units [S, secondary summaries of *Systematic Trading*].
- **(d) Allocation.** Estimation error in means usually defeats optimisation, so 1/N is hard to beat (DeMiguel, Garlappi and Uppal 2009 [M]). Handcrafted equal-risk weights, grouped by asset class, are the robust middle path.
- **(e) Adaptive optimisation, online learning, regime models.** HMMs are sensitive to mis-specification and mis-estimation; Shu, Yu and Mulvey propose jump models as more robust [S]. Positive out-of-sample HMM results exist but are theses and single-design studies [S]. Online learning helps where signal-to-noise is high and data plentiful (intraday), not with about 250 daily observations a year [M, judgment]. Keep the existing hysteresis regime filter as a fixed-parameter exposure scalar, and treat any learned regime model as a research candidate under the section 4 gates.
- **(f) Short histories.** Pool, do not fit. New instruments inherit pooled scalars and class-level weights. Volatility is the only thing estimated from the instrument's own short history.

### 2.2 Recommended scheme

**Volatility.** Daily returns r, EWMA with span 32 days, blended with a long-run average as in Carver's later books [M]:

`σ_i = 16 × (0.7 × σ_EWMA32 + 0.3 × mean_10y(σ_EWMA32))`

For histories under 10 years use all available. Under 1 year, floor at the proxy or asset-class median vol.

**Forecasts.** Each rule j gives a raw forecast scaled to average absolute value 10 and capped at ±20:

`f_j = clip(s_j × raw_j, −20, +20)`, with `s_j = 10 / pooled median(|raw_j|)`, fixed in config.

- Existing binary tests: with k of 8 tests passing, `F_trend = 20 × k/8` for long-only (range 0–20). For a long/short futures sleeve use `20 × (2k/8 − 1)`.
- Check that the pooled long-run mean of |F| is near 10. If it is not, apply one global scalar, fixed once.
- Optional continuous rules for futures: EWMAC(16,64), (32,128), (64,256) with `raw = (EWMA_fast − EWMA_slow) / σ_price_daily`. Published scalars are about 4.10, 2.79 and 1.91 [S, from a QuantConnect re-implementation].
- RSI(2) dip-buy stays a discrete overlay on a capped risk budget. It is a different trade type and does not enter the forecast combination.

**Combination.**

`F_i = clip(FDM × Σ_j w_j × f_j, −20, +20)`, with `FDM = min(2.5, 1 / sqrt(wᵀ ρ_f w))`

ρ_f is the pooled forecast correlation with negatives floored at 0; the 2.5 cap is [M]. Weights w_j are equal across speed buckets and renormalised over the rules that survive the cost filter. The eight tests are highly correlated, so expect FDM of roughly 1.0–1.2.

**Cost-aware rule selection.**

`c_i = (half-spread + commission per unit + slippage) × 2 / (price × multiplier × σ_i)` (round-trip cost in SR units)

- Rule j is enabled on instrument i only if `turnover_j × c_i ≤ 0.13`.
- Exclude the instrument entirely if `(turnover of the slowest rule + roll turnover) × c_i > 0.13`, or if `c_i > 0.01` [M/U].
- Recompute quarterly. A change takes effect only after two consecutive reviews agree (hysteresis).

**Regime and vol scalars.** `M_regime ∈ {1.0, 0.5, 0.0}` from the existing hysteresis filter on long equity-like exposure. Apply it once, at the portfolio stage, to avoid double-counting with the trend forecast. Commodity-trend confirmation becomes a multiplier in [0.5, 1.0] on the relevant sector instead of a hard gate.

**Position sizing.**

`N*_i = (F_i / 10) × (C × τ × w_i × IDM × M_regime) / (σ_i × P_i × mult_i × FX_i)`

- C is NAV in AUD, P is the actual contract or share price, and FX is AUD per unit of instrument currency.
- τ is the annual vol target. Suggest 10–12% for long-only ETF accounts. A long/short futures sleeve at up to 20% only after validation. Carver's guidance is to stay at or below half-Kelly [M].
- `IDM = min(2.5, 1 / sqrt(wᵀ ρ w))`, using correlations of subsystem returns, weekly data, negatives floored at 0, and the matrix shrunk to keep it positive semi-definite.
- Instrument weights w_i are handcrafted: equal risk across asset classes, then equal within class. They are recomputed only when the instrument set changes.
- Existing caps (per-name, per-sector, gross exposure) are applied after this as hard limits.

**Buffering.**

`B_i = 0.10 × |N*_i at F = 10|`

If the current position is inside `[N* − B, N* + B]`, do nothing. Otherwise trade to the nearest edge, not the centre. The 10% of average position is Carver's long-standing default [S]. Round after buffering.

**Chandelier stop.** Keep it for the discrete share sleeve, where positions are binary. In the continuous-forecast sleeve the stop is redundant with forecast decay and adds a fitted parameter, so set it per sleeve and do not run both on the same position.

## 3. Small-account adaptations

**Minimum-capital test.** Run at each monthly review.

- `N_avg,i` is N* at F = 10. A futures instrument is eligible only if `N_avg,i ≥ 4` in the full scheme, so that forecast changes map to position changes (Carver's 4-contract heuristic [M]).
- Under dynamic optimisation the test relaxes to: the account can hold at least one contract without that position exceeding its risk cap.
- For shares and ETFs the test is economic. Typical rebalance trade value must satisfy `commission / trade value ≤ 0.25%`, else widen the buffer or drop the instrument. The lowest-priced unit must be no more than 10% of the average position.

**Instrument selection for a given capital** (Carver's static method, from his 2016 small-account post and later books [S/M]). Add instruments greedily, each time choosing the one that most improves expected portfolio SR net of costs. Assume equal pre-cost SR; correlations drive IDM and costs are instrument-specific. Stop when the next addition breaches a minimum-position test. Review quarterly with hysteresis.

**Dynamic optimisation** (accounts that want more instruments than they can hold). Carver's first attempt failed in June 2021. The October 2021 version minimises tracking-error variance against the unrounded optimal portfolio using a greedy integer search, and November 2021 added portfolio-level buffering [S].

- Minimise over integer positions x: `sqrt((w(x) − w*)ᵀ Σ (w(x) − w*)) + λ × cost(x − x_prev)`.
- Start from zero (or from current positions) and repeatedly add the one-unit step in whichever instrument reduces the objective most, until no step improves it.
- Trade only if the tracking error of current against optimised positions exceeds a threshold, then trade part-way.
- Shrink Σ, because pandas correlation matrices are not guaranteed positive semi-definite and users hit negative-variance errors [S].
- Scope this to a futures sleeve of about A$150k or more, phase 2.

**Fractional shares.** Not available through the TWS API for stocks [S], and ASX-listed products are not mentioned as eligible on IBKR Australia's pages [S]. Assume whole units everywhere, with `size_increment` in config so it can be switched if IBKR changes.

**A$5k account.** Keep the monthly VAS/VGS/cash switch.

- At an A$6 minimum, each switch of A$2,500 costs about 0.24% one-way, so a monthly cadence with a no-trade band is the right speed.
- Do not add US ETFs unless a cost model including FX conversion minimums shows a net benefit [U].
- No futures, no RSI(2).
- Add a band: skip rebalances where the trade is under A$500 or drift is under 5% of NAV.

**Integer rounding.** Round to nearest. If |N*| < 0.5 the position is zero, and the unallocated risk is logged, not redistributed. Report "rounding tracking error" daily as a health metric.

## 4. Validation

| Element | Specification |
|---|---|
| **Research protocol** | Pre-register the rule set, the parameter grid (ideally none) and the metrics before running. Keep a persistent trial ledger of every variant, universe and cost assumption evaluated. N from this ledger feeds the Deflated Sharpe Ratio. |
| **Walk-forward** | Expanding window. Anything estimated (scalars, FDM, IDM, weights, cost filter) uses only data up to t−1 and is re-estimated annually. No parameter is selected on the full sample. |
| **Purged CV** | Combinatorial purged CV (López de Prado 2018 [M]): split into N = 10 groups, test on k = 2, giving 45 splits and 9 backtest paths. Purge observations whose signal window (up to 252 days) overlaps test blocks, with an embargo of at least 21 days. Report the distribution of path Sharpes, not the best. Only needed for components with fitted parameters. |
| **Deflated Sharpe** | Bailey and López de Prado (2014) [S for the paper, M for the formula]. `SR0 = sqrt(Var(SR_n)) × ((1−γ) Z⁻¹(1 − 1/N) + γ Z⁻¹(1 − 1/(N e)))`, γ ≈ 0.5772. `DSR = Z((SR − SR0) × sqrt(T−1) / sqrt(1 − skew × SR + ((kurt−1)/4) × SR²))`, with SR per period. Gate: DSR ≥ 0.95 for any change to rules. |
| **PBO** | Combinatorially symmetric CV (Bailey, Borwein, López de Prado and Zhu, J. Computational Finance 2017 [S]). Split the T × N trial matrix into S = 16 blocks, form all 12,870 half/half splits, take the out-of-sample relative rank of the in-sample best, and set PBO to the share with logit below 0. Gate: PBO ≤ 0.2 [my threshold]. It weakens temporal ordering, so it complements walk-forward and does not replace it [S]. |
| **Cost models** | Per venue: commission from the model above; half-spread from sampled quotes at the intended execution time; impact `k × σ_daily × sqrt(Q/ADV)` with k ≈ 0.1–1 [M]; roll costs for futures; FX conversion cost; withholding-tax drag on dividends; margin and cash interest. Run each backtest at 1×, 2× and 3× costs. Gate: positive net SR at 2×. |
| **Data hygiene** | ASX and US stocks need delisted names and point-in-time index membership, dividends and corporate actions. ETF-only universes avoid most survivorship bias but have selection bias (funds that exist today) and short histories, so splice index or futures proxies before inception and flag those periods. Futures need individual contract data with real expiries, stitched in-house. Micros started around 2019, so use the full-size contract for signal history [M]. Crypto: 24/7 data with venue-specific closes, and exclude pre-2017 data. |
| **Stress tests** | Replay 2008–09, 2011, 2015, Feb–Mar 2020, 2022 (joint equity and bond drawdown) and April 2025 [U on which window]. Synthetic shocks: an overnight gap of 5σ against all positions, correlations set to 1, AUD moving ±15%, spreads ×5, and a venue closed for 3 days with open positions. |
| **Monte Carlo** | Stationary block bootstrap of daily portfolio returns, block of about 20–60 days, to keep vol clustering. Trade-order shuffling alone destroys serial dependence and understates drawdowns [M]. Report the 5th/50th/95th percentile of maximum drawdown and of time under water. Also bootstrap across instruments to test dependence on a few winners. |
| **Go-live gates** | At least 3 months of paper trading per new venue. Live against backtest tracking error is monitored. A new venue starts at 25% of target risk and steps up after 3 clean months. |

## 5. Spec-ready recommendations

### New requirements (suggested IDs)

**Instrument and venue**
- **FR-MKT-001** All market-specific behaviour comes from `Instrument`/`Venue` config; no exchange literals in strategy code.
- **FR-MKT-002** Sessions and holidays come from `exchange_calendars` (pinned) and are reconciled daily with IBKR `tradingHours`. A mismatch means no trading on that venue plus an alert.
- **FR-MKT-003** Per-venue scheduler: a signal run at close plus offset for each venue; idempotent per (venue, session).
- **FR-MKT-004** Prices are rounded to the venue tick table and quantities to `lot_size`/`size_increment` before submission; violations are rejected locally.
- **FR-MKT-005** Pluggable `CommissionModel` per venue, used identically in backtest, pre-trade checks and reporting. Estimated against actual commission is reconciled monthly.
- **FR-MKT-006** Multi-currency ledger: NAV in AUD at a single FX snapshot, a per-currency cash policy and an FX exposure report. No unintended margin loans.
- **FR-MKT-007** Tax flags per instrument, with holding-period tracking (12-month CGT, 45-day franking) in reporting.

**Futures (phase 2)**
- **FR-FUT-001** Roll calendar per root, a first-notice and expiry guard, and separate roll order tagging.
- **FR-FUT-002** Three price series (contract, adjusted, carry); signals use adjusted and sizing uses contract.
- **FR-FUT-003** Margin check: required margin at most 30% of NAV [proposed].

**Signal and sizing**
- **FR-SIG-010** All rules emit forecasts scaled to mean absolute 10 and capped at ±20; scalars are fixed in config.
- **FR-SIG-011** Combination with fixed weights and FDM (cap 2.5); weights renormalise over cost-eligible rules.
- **FR-SIG-012** Cost-based rule eligibility (speed limit 0.13 SR), reviewed quarterly with two-review hysteresis.
- **FR-SIZ-010** The position formula in section 2.2, with blended EWMA vol, IDM (cap 2.5) and a per-account τ.
- **FR-SIZ-011** Buffer of 10% of average position, trading to the edge.
- **FR-SIZ-012** Minimum-position eligibility test and capital-aware instrument selection (monthly test, quarterly set review).
- **FR-SIZ-013** (phase 2) Greedy tracking-error dynamic optimisation for the futures sleeve.
- **FR-SIZ-014** Whole-unit sizing only; fractional is disabled unless `size_increment < 1` and the API path is verified.

**Adaptivity governance**
- **FR-ADP-001** Whitelist of quantities that may adapt automatically: vol, correlations, IDM, FDM, cost estimates, rule eligibility, the instrument set and regime state. Everything else is frozen.
- **FR-ADP-002** Any change outside the whitelist requires the validation gates and a version bump.
- **FR-ADP-003** New-instrument onboarding uses pooled parameters, a proxy history and a 25% risk ramp.

**Validation**
- **FR-VAL-001** Trial ledger.
- **FR-VAL-002** Expanding walk-forward.
- **FR-VAL-003** DSR ≥ 0.95 and PBO ≤ 0.2 gates.
- **FR-VAL-004** Cost-multiple test (net SR above 0 at 2×).
- **FR-VAL-005** Stress replay suite.
- **FR-VAL-006** Block-bootstrap drawdown distribution.
- **FR-VAL-007** Live against backtest tracking monitor.

### Config schema additions

```yaml
venues:
  XASX: {ib_exchange: ASX, calendar: XASX, tz: Australia/Sydney, currency: AUD,
         close_auction: true, decision_offset_min: 30, commission_model: asx_fixed}
commission_models:
  asx_fixed:  {type: pct_with_min, pct: 0.0008, minimum: 6.00, currency: AUD}   # verify
  us_fixed:   {type: per_unit, per_unit: 0.005, minimum: 1.00, max_pct: 0.01, currency: USD}  # verify
  cme_micro:  {type: per_contract, broker: 0.25, exchange: null, regulatory: null, currency: USD}  # fill in
instruments:
  VAS.XASX: {type: etf, asset_class: eq_au, venue: XASX, multiplier: 1, lot_size: 1,
             tax: {cgt_discount_eligible: true, franking: true}, proxy_key: XJO_TR}
  MES.CME:  {type: future, asset_class: eq_glob, venue: CMES, multiplier: 5, currency: USD,
             roll: {cycle: HMUZ, roll_offset_days: 5, adjust_method: panama_diff}, proxy_key: ES.CME}
forecast:   {cap: 20, target_abs: 10, fdm_cap: 2.5, scalars: {...}, weights: {...}}
sizing:     {vol_span_days: 32, vol_blend_longrun: 0.3, idm_cap: 2.5, buffer_frac: 0.10,
             min_avg_position_units: 4, max_commission_pct_per_trade: 0.0025}
costs:      {speed_limit_sr: 0.13, max_instrument_cost_sr: 0.01, review: quarterly, hysteresis_reviews: 2}
accounts:
  small: {base_ccy: AUD, vol_target: null, mode: monthly_switch, venues: [XASX], min_trade_aud: 500}
  large: {base_ccy: AUD, vol_target: 0.12, mode: forecast_portfolio, venues: [XASX, ARCX],
          fx_policy: {USD: {max_idle: 2000, allow_margin_loan: false}}}
validation: {dsr_min: 0.95, pbo_max: 0.20, cost_multiples: [1, 2, 3], cpcv: {groups: 10, test_groups: 2, embargo_days: 21}}
```

MES multiplier of 5 and the quarterly cycle are from memory [M].

### Changes to the existing ASX-only design

1. Replace hard-coded ASX hours, ticks and commission with the `Venue`/`Instrument` lookup. ASX becomes the first configured venue with no behaviour change. Prove this with a regression test before adding any market.
2. Convert the 8 binary tests to a 0–20 forecast and move sizing to the FR-SIZ-010 formula. Keep the existing caps as hard limits afterwards.
3. Apply the regime filter once, at portfolio level. Make commodity-trend confirmation a multiplier.
4. Keep the chandelier stop only for the discrete sleeve, and add the buffer rule for the continuous sleeve.
5. Split the daily job into per-venue runs with as-of tagging, and change NAV to multi-currency.
6. Leave the A$5k account's logic unchanged apart from the no-trade band and whole-unit enforcement.
7. Rollout order: (i) abstraction refactor on ASX only; (ii) US ETFs for the large account, in paper trading; (iii) futures sleeve only if account size passes FR-SIZ-012; (iv) crypto only through listed ETFs, at a capped risk weight.

### Must verify before build

- IBKR Australia's current commission schedule, FX conversion cost and CME exchange fees.
- The ASX auction order type through the API, and current CSPA timings.
- Stock `cashQty` behaviour in the installed TWS API version.
- IBKR futures close-out deadlines, and whether calendar-spread orders are supported for the micro contracts.
- Crypto availability for Australian retail accounts on IBKR.
- Carver's exact numbers (EWMAC scalars, 0.13 and 0.01 SR cost limits, FDM/IDM caps, the 4-contract rule) against the books or the pysystemtrade source, since his blog was unreachable.
- Australian tax treatment, with an accountant.

## Sources

Reached via search summaries, not fetched in full:
- Carver: [correlations, weights, multipliers](https://qoppac.blogspot.com.es/2016/01/correlations-weights-multipliers.html) · [estimated forecast scalars](https://qoppac.blogspot.com/2016/01/pysystemtrader-estimated-forecast.html) · [diversification and small account size](https://qoppac.blogspot.com.es/2016/03/diversification-and-small-account-size.html) · [small-account optimisation, June 2021](https://qoppac.blogspot.com/2021/06/optimising-portfolios-for-small.html) · [Mr Greedy, Oct 2021](https://qoppac.blogspot.com/2021/10/mr-greedy-and-tale-of-minimum-tracking.html) · [Nov 2021 buffering](https://qoppac.blogspot.com/2021/11) · [gist with 0.13 cost limit](https://gist.github.com/robcarver17/795d11b977261065d1f0da68eb95624f)
- Carver, secondary: [7circles on speed limits](https://the7circles.uk/?p=24243) · [7circles on position adjustment](https://the7circles.uk/?p=27928) · [QuantConnect re-implementation](https://www.quantconnect.com/research/15875/futures-fast-trend-following-with-trend-strength/) · [EliteTrader PSD issue](https://elitetrader.com/et/threads/fully-automated-futures-trading.289589/page-389)
- pysystemtrade: [data.md (fork)](https://www.github.com/willsliou/pysystemtrade/blob/master/docs/data.md)
- NautilusTrader: [instruments](https://nautilustrader.io/docs/latest/concepts/instruments) · [futures contract](https://nautilustrader.io/docs/latest/concepts/instruments/futures_contract/)
- LEAN: [security properties](https://www.QuantConnect.com/docs/v2/writing-algorithms/securities/properties) · [trading and orders](https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/key-concepts)
- exchange_calendars: [PyPI](https://pypi.org/project/exchange-calendars/4.5)
- IBKR: [API order-type limitations](https://www.interactivebrokers.com/docs/general/order-types/notes-limitations/introduction) · [Web API changelog](https://www.interactivebrokers.com/docs/web-api/changelog) · [fractional share orders (AU)](https://www.interactivebrokers.com.au/en/trading/orders/fractional-share-orders.php) · [commissions (AU)](https://www.interactivebrokers.com.au/en/pricing/commissions-home.php) · [futures commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-futures.php?re=amer) · [Invezz review of IBKR Australia](https://invezz.com/au/reviews/interactive-brokers-review-australia/)
- ASX: [closing price determination](https://asx.com.au/content/dam/asx/about/regulations/public-consultations/2017/asx-equity-market-closing-and-settlement-price-determination.pdf) · [Bell Direct on trading-hours changes](https://belldirect.com.au/asx-trading-changes) · [Market Index trading hours](https://marketindex.com.au/trading-hours)
- Overfitting: [Probability of Backtest Overfitting](https://papers.ssrn.com/abstract=2326253) · [Deflated Sharpe Ratio](https://papers.ssrn.com/abstract=2460551)
- Ensembles and regimes: [ReSolve on ensembles](https://investresolve.com/from-fragility-to-robustness-the-value-of-ensembles/) · [Newfound on timing specifications](https://blog.thinknewfound.com/2019/12/timing-trend-model-specification-with-momentum/) · [arXiv 2510.23150](https://arxiv.org/pdf/2510.23150v1) · [Shu, Yu and Mulvey jump models](https://arxiv.org/html/2402.05272v1) · [Quantpedia HMM study](https://quantpedia.com/?p=46520)

From memory, not retrieved: Carver's *Systematic Trading*, *Leveraged Trading* and *Advanced Futures Trading Strategies*; López de Prado's *Advances in Financial Machine Learning*; Moreira and Muir (2017); Harvey et al. (2018); DeMiguel, Garlappi and Uppal (2009).