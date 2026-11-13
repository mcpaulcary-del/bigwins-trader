"""Configuration loading and validation (spec v2.10 §18; OPS-10, OPS-11, OPS-12).

``config/common.yaml`` holds the settings that ship with a release;
``config/<user>.yaml`` holds one user's account, limits, contacts and approval
pins. Both are validated with pydantic; an invalid file stops the run.

Rules implemented here:

* Schema exactly per §18 (v2.10); unknown keys are rejected (``extra="forbid"``).
* Every non-integer number is an exact ``Decimal`` (the YAML loader never builds
  a binary float), so money and thresholds never pass through float (SYS-13).
* Personal limits may only be tighter than the common defaults (§18).
* Secrets never appear in config files (OPS-11): a key/value scan refuses them.
* Approval pins: ``approved_git_sha`` must equal the deployed code SHA and
  ``approved_common_hash`` must equal the SHA-256 of ``common.yaml``; any
  mismatch refuses to run (OPS-10).
* OPS-12 (v2.10): tranche-count / minimum-order check, tax flags, hosting,
  ``mode: L1`` evidence and ``backtest_max_drawdown`` for a live L1 account.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, time
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)

from trader.constants import (
    BUILD_SHA_FILE,
    CENT,
    COMMON_CONFIG_NAME,
    GIT_SHA_LENGTH,
    SHA256_HEX_LENGTH,
    USER_CONFIG_FORBIDDEN_MODE_BITS,
)
from trader.enums import IbkrMode, ParcelMethod
from trader.timeutil import asx_today, parse_hhmm
from trader.yamlio import load_yaml

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ConfigError(Exception):
    """Base class: any config problem stops the run."""


class ConfigValidationError(ConfigError):
    """Schema or cross-field validation failed."""


class SecretInConfigError(ConfigError):
    """A secret (or something that looks like one) was found in a config file (OPS-11)."""


class ApprovalPinMismatchError(ConfigError):
    """Deployed code or common.yaml differs from the user's approval pins (OPS-10)."""


class ConfigPermissionError(ConfigError):
    """A per-user config file is readable by group or others (§18: owner-only)."""


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------


def _reject_float(v: object) -> object:
    # SYS-13: numbers are never built from a binary float.
    if isinstance(v, float):
        raise ValueError("numbers must be written as decimal literals, not binary floats")
    if isinstance(v, bool):
        raise ValueError("expected a number")
    return v


def _clock(v: object) -> time:
    if not isinstance(v, str):
        raise ValueError("times must be quoted strings 'HH:MM' or 'HH:MM:SS' (Australia/Sydney)")
    return parse_hhmm(v)


_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,6}$")


def _symbol(v: str) -> str:
    if not _SYMBOL_RE.fullmatch(v):
        raise ValueError(f"invalid ASX symbol {v!r}")
    return v


Money = Annotated[
    Decimal, BeforeValidator(_reject_float), Field(ge=0, max_digits=18, decimal_places=4)
]
PositiveMoney = Annotated[
    Decimal, BeforeValidator(_reject_float), Field(gt=0, max_digits=18, decimal_places=4)
]
Dec = Annotated[Decimal, BeforeValidator(_reject_float)]
Ratio = Annotated[Decimal, BeforeValidator(_reject_float), Field(ge=0, le=1)]
PosDec = Annotated[Decimal, BeforeValidator(_reject_float), Field(gt=0)]
PosInt = Annotated[StrictInt, Field(gt=0)]
NonNegInt = Annotated[StrictInt, Field(ge=0)]
Clock = Annotated[time, BeforeValidator(_clock)]
Symbol = Annotated[StrictStr, AfterValidator(_symbol)]

# Evaluation offset: 'last' or the k-th trading day of the month (§4, PRT-14).
MAX_TRADING_DAY_OFFSET = 23
Offset = Literal["last"] | Annotated[StrictInt, Field(ge=1, le=MAX_TRADING_DAY_OFFSET)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


def income_year(d: date) -> str:
    """Australian income year label of date ``d``, e.g. 2026-27 (1 July - 30 June)."""
    first = d.year if d.month >= 7 else d.year - 1
    return f"{first}-{(first + 1) % 100:02d}"


def _distinct(items: list[Any], where: str) -> None:
    if len(set(items)) != len(items):
        raise ValueError(f"{where} has duplicates")


def _sums_to_one(weights: Mapping[str, Decimal], where: str) -> None:
    if not weights or sum(weights.values()) != 1:
        raise ValueError(f"{where} weights must sum to exactly 1")


# ---------------------------------------------------------------------------
# common.yaml
# ---------------------------------------------------------------------------


class Sleeve(_Model):
    base_weight: Ratio


class BenchmarkB1(_Model):
    weights: dict[Symbol, Ratio]
    reinvest_distributions: Literal["pay_date_close"]
    flow_commission: StrictBool
    min_order: StrictBool

    @model_validator(mode="after")
    def _w(self) -> Self:
        _sums_to_one(self.weights, "benchmarks.B1")
        return self


class BenchmarkB2(_Model):
    weights: dict[Symbol, Ratio]
    rebalance: Literal["first_execution_date_of_july"]
    order_rules: Literal["live"]

    @model_validator(mode="after")
    def _w(self) -> Self:
        _sums_to_one(self.weights, "benchmarks.B2")
        return self


class Benchmarks(_Model):
    B1: BenchmarkB1
    B2: BenchmarkB2


class Vote(_Model):
    type: Literal["return_gt_zero", "price_gt_sma"]
    months: PosInt


class L1Config(_Model):
    votes: Annotated[list[Vote], Field(min_length=1)]
    on_at_votes: NonNegInt
    off_at_votes: NonNegInt
    bootstrap_state: Literal["OFF", "ON"]
    tranches_max: PosInt
    tranche_min_order_mult: PosDec
    tranche_offsets_by_n: dict[PosInt, list[Offset]]
    band_relative: Ratio
    min_order_value_aud: PositiveMoney
    transition_buy_min_mult: Ratio
    cash_reserve_aud: Money
    cash_etf: None  # off in v2.10; enabling it needs a spec change (PRT-18)
    sentinel_unit: StrictBool

    @model_validator(mode="after")
    def _cross(self) -> Self:
        n_votes = len(self.votes)
        if not self.off_at_votes < self.on_at_votes <= n_votes:
            raise ValueError("l1: need off_at_votes < on_at_votes <= number of votes")
        if 1 not in self.tranche_offsets_by_n or self.tranches_max not in self.tranche_offsets_by_n:
            raise ValueError("l1.tranche_offsets_by_n must define N = 1 and N = tranches_max")
        for n, offs in self.tranche_offsets_by_n.items():
            if len(offs) != n:
                raise ValueError(f"l1.tranche_offsets_by_n[{n}] must list exactly {n} offsets")
            _distinct(offs, f"l1.tranche_offsets_by_n[{n}]")
        return self


class VenueXASX(_Model):
    """Venue timing held in config, never taken from a library (§4, OPS-05)."""

    tz: Literal["Australia/Sydney"]
    opening_auction: Clock
    closing_auction: tuple[Clock, Clock]
    post_close_end: Clock
    close_available_after: Clock
    settlement_days: PosInt
    early_close: Clock
    library_calendar: Literal["XASX"]

    @model_validator(mode="after")
    def _order(self) -> Self:
        start, end = self.closing_auction
        if not (
            self.opening_auction
            < self.early_close
            < start
            < end
            < self.post_close_end
            < self.close_available_after
        ):
            raise ValueError(
                "venue.XASX: need opening_auction < early_close < closing auction start < "
                "closing auction end < post_close_end < close_available_after"
            )
        return self


class Venues(_Model):
    XASX: VenueXASX


_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _weekday_clock(v: object) -> tuple[str, time]:
    if not isinstance(v, str) or len(v.split()) != 2:
        raise ValueError("expected 'Ddd HH:MM', e.g. 'Sun 03:00'")
    day, hhmm = v.split()
    if day not in _WEEKDAYS:
        raise ValueError(f"unknown weekday {day!r}")
    return day, parse_hhmm(hhmm)


WeekdayClock = Annotated[tuple[str, time], BeforeValidator(_weekday_clock)]


class Misfire(_Model):
    decide_min_notice_min: PosInt
    new_order_auth_until: Clock
    reconcile_until: Clock


class ScheduleConfig(_Model):
    """Job times, Australia/Sydney (§4, SYS-14)."""

    fetch_vendor_data: tuple[Clock, Clock, Clock]
    daily_digest: Clock
    heartbeat: Clock
    backup: Clock
    full_redownload: WeekdayClock
    flex_pull: Clock
    flex_retry_min: PosInt
    flex_retry_until: Clock
    validate_data: Clock
    mark_and_reconcile: Clock
    decide: Clock
    gateway_start: Clock
    veto_deadline: Clock
    submit_orders: Clock
    retry_orders: Clock
    last_new_order: Clock
    cancel_unfilled: Clock
    reconcile_broker: Clock
    gateway_stop_latest: Clock
    misfire: Misfire
    twofa_reprompt_min: PosInt
    buy_carry_days: PosInt
    evaluation_catchup_days: PosInt
    connectivity_check_days: PosInt
    deploy_freeze_hours: PosInt

    @model_validator(mode="after")
    def _order(self) -> Self:
        morning = [
            self.flex_pull,
            self.validate_data,
            self.mark_and_reconcile,
            self.decide,
            self.gateway_start,
            self.veto_deadline,
            self.submit_orders,
            self.retry_orders,
            self.last_new_order,
            self.cancel_unfilled,
            self.reconcile_broker,
            self.gateway_stop_latest,
        ]
        if morning != sorted(morning) or len(set(morning)) != len(morning):
            raise ValueError("schedule: the trading-day jobs must be in strictly increasing order")
        first, retry1, retry2 = self.fetch_vendor_data
        if not (retry2 < self.validate_data and first < retry1):
            raise ValueError(
                "schedule.fetch_vendor_data: evening fetch, later evening retry, and a morning "
                "retry before validate_data"
            )
        return self


class CrossSource(_Model):
    ok: Ratio
    block: Ratio

    @model_validator(mode="after")
    def _order(self) -> Self:
        if not self.ok < self.block:
            raise ValueError("data.cross_source: need ok < block")
        return self


class Spike(_Model):
    mult_of_mean_abs_60d: PosDec
    abs_return: Ratio


class Restatement(_Model):
    block_rows: PosInt
    block_pct: Ratio


class TrGapBp(_Model):
    non_ex: PosInt
    ex: PosInt


class EodhdPlan(_Model):
    plan: Literal["free", "paid"]
    calls_per_day: PosInt
    calls_per_minute: PosInt
    history_years: PosInt
    daily_requests: list[Literal["eod", "dividends"]]
    instruments: Annotated[list[Symbol], Field(min_length=1)]
    on_budget_exceeded: Literal["fail_closed"]

    @model_validator(mode="after")
    def _d(self) -> Self:
        _distinct(self.instruments, "data.eodhd.instruments")
        _distinct(list(self.daily_requests), "data.eodhd.daily_requests")
        if "eod" not in self.daily_requests:
            raise ValueError("data.eodhd.daily_requests must include eod")
        return self


class DataConfig(_Model):
    cross_source: CrossSource
    spike: Spike
    stale_sessions: PosInt
    restatement: Restatement
    tr_gap_bp: TrGapBp
    implied_dividend_tolerance: Ratio
    yearly_tr_tolerance: Ratio
    fx_move_warn: Ratio
    snapshot_gap_hold: Ratio
    snapshot_confirm_tolerance: Ratio
    snapshot_gap_sell_max: Ratio
    min_evaluation_closes: PosInt
    spread_warn: Ratio
    eodhd: EodhdPlan
    spread_exclude: Ratio

    @model_validator(mode="after")
    def _cross(self) -> Self:
        if not self.spread_warn < self.spread_exclude:
            raise ValueError("data: need spread_warn < spread_exclude")
        if not self.snapshot_gap_hold < self.snapshot_gap_sell_max:
            raise ValueError("data: need snapshot_gap_hold < snapshot_gap_sell_max")
        return self


class Commission(_Model):
    model: Literal["asx_fixed", "asx_tiered"]
    rate_ex_gst: Ratio
    min_ex_gst_aud: PositiveMoney
    gst_rate: Ratio
    budget_rate_incl_gst: Ratio
    budget_min_incl_gst_aud: PositiveMoney
    review_gap: Ratio


class ExecutionConfig(_Model):
    exchange: Literal["ASX"]
    tif: Literal["DAY"]  # GTD only after open item I15 passes, by a config/spec change
    max_quote_spread: Ratio
    no_quote_collar: Ratio
    open_blackout_min: PosInt
    cancel_confirm_timeout_s: PosInt
    manual_match_days: PosInt
    canary_units: dict[Symbol, PosInt]
    snapshot_free_per_month: NonNegInt
    commission: Commission


class DrawdownLimits(_Model):
    review_pctile: Ratio
    review_abs: Ratio
    halt_pctile: Ratio
    halt_mult_of_backtest: PosDec
    frequency: Literal["month_end"]
    min_horizon_months: PosInt
    static_review_abs: Ratio
    static_review_step: Ratio
    rearm_step: Ratio

    @model_validator(mode="after")
    def _order(self) -> Self:
        if not self.review_pctile < self.halt_pctile:
            raise ValueError("risk_defaults.drawdown: need review_pctile < halt_pctile")
        return self


class TrackingBp(_Model):
    review_month: PosInt
    review_cum: PosInt
    halt: PosInt


class CostVsModel(_Model):
    review: PosDec
    halt: PosDec
    window_months: PosInt


class TradingCostPctNav(_Model):
    review: Ratio
    halt: Ratio
    applies_from_nav_aud: PositiveMoney


class OrderCount12m(_Model):
    review: PosInt
    halt: PosInt


class CommissionWarn(_Model):
    pct_nav: Ratio
    min_commissions: PosInt


class VoteFlipsReview(_Model):
    count: PosInt
    months: PosInt


class RiskDefaults(_Model):
    max_buy_order_value_mult_of_sleeve: PosDec
    max_sleeve_weight_mult: PosDec
    adv_pct: Ratio
    adv_days: PosInt
    price_band: Ratio
    max_orders_per_day: PosInt
    max_daily_buy_turnover_mult: PosDec
    drawdown: DrawdownLimits
    # Always null in a release; each user's own G2 run writes it under `limits` (USR-05).
    backtest_max_drawdown: None
    tracking_bp: TrackingBp
    cost_vs_model: CostVsModel
    trading_cost_pct_nav: TradingCostPctNav
    order_count_12m: OrderCount12m
    commission_warn: CommissionWarn
    vote_flips_review: VoteFlipsReview
    price_gap_no_trade: Ratio


class LagReview(_Model):
    months: PosInt
    lag_pp: PosInt
    drawdown_saving_pp: PosInt


class KillCriteria(_Model):
    drawdown: Ratio
    all_in_cost_pct: Ratio
    all_in_cost_from_nav_aud: PositiveMoney
    incidents_per_year: PosInt
    overrides_per_year: PosInt
    lag_review: LagReview


class CapRiseStaging(_Model):
    threshold: Ratio
    first_step: Ratio
    months: PosInt


class CapitalConfig(_Model):
    cap_rise_staging: CapRiseStaging


class DistributionMatchTolerance(_Model):
    abs_aud: Money
    pct: Ratio


class IdleCashPage(_Model):
    after_cycles: PosInt
    repeat_days: PosInt


class OpsConfig(_Model):
    flex_pending_days: PosInt
    flex_pending_deficit_max_aud: Money
    flex_pending_fee_types: list[Literal["snapshot_fee", "withholding", "commission_gst"]]
    distribution_match_tolerance: DistributionMatchTolerance
    withdrawal_lapse_days: PosInt
    withdrawal_sell_buffer: Ratio
    idle_cash_page: IdleCashPage
    calendar_min_days_ahead: PosInt
    flex_token_warn_days: PosInt
    clock_skew_max_s: PosInt
    deadman_grace_min: PosInt
    nav_vs_netliq_tolerance: Ratio
    recon_page_within_min: PosInt
    server_cost_warn_aud_month: Money
    dependency_min_age_days: PosInt
    log_retention_days: PosInt


class TaxDefaults(_Model):
    medicare_levy: Ratio
    franking_exemption_aud: Money
    franking_warn_aud: Money
    holding_period_days: PosInt
    rebuy_warn_days: PosInt
    record_retention_years: PosInt


IncomeYear = Annotated[StrictStr, Field(pattern=r"^\d{4}-\d{2}$")]
YearMonth = Annotated[StrictStr, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


class H1AfterTaxDefaults(_Model):
    nav_aud: PositiveMoney
    marginal_rate: Ratio
    regime: Literal["a", "b"]
    contributions: Literal["none"]


class BootstrapConfig(_Model):
    paths: PosInt
    mean_block_months: PosInt


class FamilyB(_Model):
    t_min: PosDec
    dsr_min: Ratio


class ResearchConfig(_Model):
    development: tuple[YearMonth, YearMonth]
    holdout_from: YearMonth
    trial_cap_per_family: PosInt
    families: dict[Literal["L1", "P1"], list[Annotated[StrictStr, Field(pattern=r"^H\d+$")]]]
    family_a_alpha: Ratio
    family_b: FamilyB
    backtest_navs: Annotated[list[PositiveMoney], Field(min_length=1)]
    # v2.10 + R37 correction: keyed by income year ("2026-27"); see docs/DECISIONS.md C-13.
    marginal_rates: dict[IncomeYear, Annotated[list[Ratio], Field(min_length=1)]]
    h1_after_tax_defaults: H1AfterTaxDefaults
    bootstrap: BootstrapConfig

    @model_validator(mode="after")
    def _periods(self) -> Self:
        start, end = self.development
        if not start <= end < self.holdout_from:
            raise ValueError("research: need development start <= end < holdout_from")
        for year in self.marginal_rates:
            first, second = int(year[:4]), int(year[5:])
            if (first + 1) % 100 != second:
                raise ValueError(f"research.marginal_rates: {year!r} is not an income year")
        return self

    def rates_for(self, d: date) -> list[Decimal] | None:
        """Resident marginal rates for the income year containing ``d`` (1 July - 30 June)."""
        return self.marginal_rates.get(income_year(d))


class AlertsCommon(_Model):
    page_budget_per_month: PosInt


class BackupCommon(_Model):
    keep_daily: PosInt
    keep_monthly: PosInt


_HEX40 = re.compile(rf"^[0-9a-f]{{{GIT_SHA_LENGTH}}}$")
_HEX64 = re.compile(rf"^[0-9a-f]{{{SHA256_HEX_LENGTH}}}$")


def _sha256(v: str) -> str:
    if not _HEX64.fullmatch(v):
        raise ValueError("must be a 64-char lowercase hex SHA-256")
    return v


Sha256 = Annotated[StrictStr, AfterValidator(_sha256)]


class CommonConfig(_Model):
    version: Literal[3]
    spec_hash: Sha256
    # null until the hypothesis card set is frozen at G0 (docs/DECISIONS.md C-12);
    # `mode: L1` is refused while it is null (OPS-12).
    card_set_hash: Sha256 | None
    rule: Literal["L1"]
    sleeves: dict[Symbol, Sleeve]
    benchmarks: Benchmarks
    l1: L1Config
    venue: Venues
    schedule: ScheduleConfig
    data: DataConfig
    execution: ExecutionConfig
    risk_defaults: RiskDefaults
    kill_criteria: KillCriteria
    capital: CapitalConfig
    ops: OpsConfig
    tax_defaults: TaxDefaults
    research: ResearchConfig
    alerts: AlertsCommon
    backup: BackupCommon

    @model_validator(mode="after")
    def _cross(self) -> Self:
        _sums_to_one({k: v.base_weight for k, v in self.sleeves.items()}, "sleeves base")
        if any(v.base_weight <= 0 for v in self.sleeves.values()):
            raise ValueError("every sleeve needs a positive base_weight")
        if set(self.execution.canary_units) != set(self.sleeves):
            raise ValueError("execution.canary_units must list exactly the sleeves")
        needed = (
            set(self.sleeves) | set(self.benchmarks.B1.weights) | set(self.benchmarks.B2.weights)
        )
        if not needed <= set(self.data.eodhd.instruments):
            raise ValueError(
                "data.eodhd.instruments must include every sleeve and benchmark symbol "
                f"(missing {sorted(needed - set(self.data.eodhd.instruments))})"
            )
        if set(self.benchmarks.B2.weights) != set(self.sleeves):
            raise ValueError("benchmarks.B2 must hold exactly the live sleeves (PRT-22)")
        if set(self.benchmarks.B1.weights) & set(self.sleeves):
            raise ValueError("benchmarks.B1 must not be a live sleeve (it is never traded, §5)")
        return self

    @property
    def benchmark_only_symbols(self) -> frozenset[str]:
        """Symbols fetched only for the benchmarks (single-source by design, DAT-02)."""
        b = set(self.benchmarks.B1.weights) | set(self.benchmarks.B2.weights)
        return frozenset(b - set(self.sleeves))


# ---------------------------------------------------------------------------
# <user>.yaml
# ---------------------------------------------------------------------------

_AGE_PUB = re.compile(r"^age1[02-9ac-hj-np-z]{58}$")  # bech32 charset
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _git_sha(v: str) -> str:
    if not _HEX40.fullmatch(v):
        raise ValueError("approved_git_sha must be a full 40-char lowercase hex git SHA")
    return v


TRADER_CLIENT_ID = 11  # §19: client ID 11 for the trader, 12 for tools (read-only)
MODE_PORT: dict[IbkrMode, int] = {IbkrMode.PAPER: 4004, IbkrMode.LIVE: 4003}
_ACCOUNT_PATTERN: dict[IbkrMode, str] = {
    IbkrMode.LIVE: r"^U\d{5,10}$",
    IbkrMode.PAPER: r"^DU\d{5,10}$",
}


class IbkrAccount(_Model):
    account_id: Annotated[StrictStr, Field(pattern=r"^D?U\d{5,10}$")]
    gateway_host: StrictStr
    port: Literal[4003, 4004]
    client_id: StrictInt


class IbkrConfig(_Model):
    mode: IbkrMode
    live: IbkrAccount
    paper: IbkrAccount

    def active(self) -> IbkrAccount:
        return self.live if self.mode is IbkrMode.LIVE else self.paper

    @model_validator(mode="after")
    def _accounts(self) -> Self:
        for mode, acct in ((IbkrMode.LIVE, self.live), (IbkrMode.PAPER, self.paper)):
            if acct.port != MODE_PORT[mode]:
                raise ValueError(f"ibkr.{mode}.port must be {MODE_PORT[mode]} (§19)")
            if acct.client_id != TRADER_CLIENT_ID:
                raise ValueError(f"ibkr.{mode}.client_id must be {TRADER_CLIENT_ID} (§19)")
            if not re.fullmatch(_ACCOUNT_PATTERN[mode], acct.account_id):
                raise ValueError(f"ibkr.{mode}.account_id does not look like a {mode} account")
        return self


class UserEodhd(_Model):
    licensee: Annotated[StrictStr, Field(pattern=r"^[a-z][a-z0-9_]{0,15}$")]


class UserLimits(_Model):
    """Personal limits; each may only be tighter than ``risk_defaults``."""

    max_orders_per_day: PosInt | None = None
    backtest_max_drawdown: (
        Annotated[Decimal, BeforeValidator(_reject_float), Field(gt=0, lt=1)] | None
    ) = None


class UserAlerts(_Model):
    telegram_chat_id: Annotated[StrictStr, Field(pattern=r"^-?\d{1,20}$")]
    email: Annotated[StrictStr, Field(pattern=_EMAIL.pattern)]


class UserTax(_Model):
    entity: Literal["individual"]  # TAX-03: the engine refuses any other value
    residency: Literal["resident"]
    regime: Literal["capital", "revenue"]
    marginal_rate: Ratio | None
    parcel_method: ParcelMethod
    minimum_tax_exempt: StrictBool
    franking_realisable_rate: Ratio


class UserBackup(_Model):
    remote_path: StrictStr
    age_public_key: Annotated[StrictStr, Field(pattern=_AGE_PUB.pattern)]


class UserDashboard(_Model):
    snapshot_key_id: StrictStr


class UserConfig(_Model):
    user: Annotated[StrictStr, Field(pattern=r"^[a-z][a-z0-9_]{0,15}$")]
    approved_git_sha: Annotated[StrictStr, AfterValidator(_git_sha)]
    approved_common_hash: Sha256
    ibkr: IbkrConfig
    hosting: Literal["owner_host", "self_hosted"]  # USR-10: no shared host
    eodhd: UserEodhd
    capital_cap_aud: PositiveMoney
    capital_cap_follows_contributions: StrictBool
    mode: Literal["STATIC", "L1"]
    # With N = 1 the user's single offset overrides the common default (USR-13).
    tranche_offsets: Annotated[list[Offset], Field(min_length=1, max_length=1)]
    exclude_symbols: list[Symbol]
    limits: UserLimits
    alerts: UserAlerts
    tax: UserTax
    backup: UserBackup
    dashboard: UserDashboard

    @model_validator(mode="after")
    def _own(self) -> Self:
        # §19 isolation: trader-<user> reaches only gw-<user>-live / gw-<user>-paper.
        for mode, acct in ((IbkrMode.LIVE, self.ibkr.live), (IbkrMode.PAPER, self.ibkr.paper)):
            if acct.gateway_host != f"gw-{self.user}-{mode}":
                raise ValueError(f"ibkr.{mode}.gateway_host must be 'gw-{self.user}-{mode}' (§19)")
        if self.eodhd.licensee != self.user:
            raise ValueError("eodhd.licensee must be this user: own data licence (USR-05, DAT-15)")
        _distinct(self.exclude_symbols, "exclude_symbols")
        return self


# ---------------------------------------------------------------------------
# Cross-file checks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EffectiveLimits:
    """Risk limits after applying the user's (tighter) overrides (RiskLimits, §3)."""

    max_orders_per_day: int
    backtest_max_drawdown: Decimal | None


def check_user_against_common(common: CommonConfig, user: UserConfig) -> EffectiveLimits:
    """Personal limits may only be tighter; exclusions must be live sleeves."""
    errors: list[str] = []
    d, lim = common.risk_defaults, user.limits
    if lim.max_orders_per_day is not None and lim.max_orders_per_day > d.max_orders_per_day:
        errors.append(
            f"limits.max_orders_per_day={lim.max_orders_per_day} is looser than the common "
            f"default {d.max_orders_per_day}; personal limits may only be tighter"
        )
    unknown = set(user.exclude_symbols) - set(common.sleeves)
    if unknown:
        errors.append(f"exclude_symbols not live sleeves: {sorted(unknown)}")
    if errors:
        raise ConfigValidationError("; ".join(errors))
    return EffectiveLimits(
        max_orders_per_day=lim.max_orders_per_day or d.max_orders_per_day,
        backtest_max_drawdown=lim.backtest_max_drawdown,
    )


# ---------------------------------------------------------------------------
# OPS-11: secrets never in config
# ---------------------------------------------------------------------------

_SECRET_KEY_RE = re.compile(
    r"(?i)(pass(word|wd|phrase)?|secret|token|api[_-]?key|private[_-]?key|credential|"
    r"auth[_-]?key|bearer|cookie|session[_-]?key|pin_code|^pwd$|^key$)"
)
_SECRET_VALUE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\d{6,12}:[A-Za-z0-9_-]{30,}$"),  # Telegram bot token
    re.compile(r"AGE-SECRET-KEY-1", re.I),  # age private key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),  # GitHub token
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b"),  # Slack token
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."),  # JWT
    re.compile(r"(?i)^(postgres(ql)?|mysql|redis|amqp)://[^:/@\s]+:[^@\s]+@"),  # DSN with password
    re.compile(r"(?i)[?&]api_token=[A-Za-z0-9.]{8,}"),  # EODHD-style key in a URL
)
# Keys whose names match _SECRET_KEY_RE but are known to hold public material.
_PUBLIC_KEY_NAMES = frozenset({"age_public_key", "snapshot_key_id", "flex_token_warn_days"})


def find_secrets(data: object, path: str = "") -> list[str]:
    """Return the paths of keys or values that look like secrets (OPS-11)."""
    hits: list[str] = []
    if isinstance(data, Mapping):
        for k, v in data.items():
            p = f"{path}.{k}" if path else str(k)
            if isinstance(k, str) and k not in _PUBLIC_KEY_NAMES and _SECRET_KEY_RE.search(k):
                hits.append(f"{p} (secret-like key name)")
            hits.extend(find_secrets(v, p))
    elif isinstance(data, list | tuple):
        for i, v in enumerate(data):
            hits.extend(find_secrets(v, f"{path}[{i}]"))
    elif isinstance(data, str) and any(rx.search(data) for rx in _SECRET_VALUE_RES):
        hits.append(f"{path} (secret-like value)")
    return hits


def _refuse_secrets(data: object, source: str) -> None:
    hits = find_secrets(data)
    if hits:
        raise SecretInConfigError(
            f"{source}: secrets must never be in config files (OPS-11); "
            f"use Docker secrets via `trader secret set`. Found: {', '.join(hits)}"
        )


# ---------------------------------------------------------------------------
# Hashes and approval pins (OPS-10)
# ---------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_config_hash(common_bytes: bytes, user_bytes: bytes) -> str:
    """Config hash stored with every run: SHA-256 over both files' exact bytes."""
    h = hashlib.sha256()
    for label, blob in ((b"common", common_bytes), (b"user", user_bytes)):
        h.update(label + b"\0" + str(len(blob)).encode() + b"\0" + blob)
    return h.hexdigest()


def deployed_git_sha(
    repo_root: Path | None = None, build_sha_file: Path = BUILD_SHA_FILE
) -> str | None:
    """SHA of the deployed code.

    In the container image (no ``.git``) the SHA is baked into
    ``trader/_build_sha.txt`` at build time. Otherwise it is read from git; a
    working tree with uncommitted changes to tracked files yields
    ``<sha>-dirty``, which can never match an approval pin.
    Returns ``None`` if it cannot be determined (callers refuse to run).
    """
    if build_sha_file.is_file():
        return build_sha_file.read_text(encoding="ascii").strip()
    root = repo_root or Path(__file__).resolve().parent.parent
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return f"{sha}-dirty" if dirty else sha


def check_approval_pins(user: UserConfig, common_hash: str, deployed_sha: str | None) -> None:
    """Refuse to run if deployed code or common.yaml differ from the user's pins."""
    problems: list[str] = []
    if deployed_sha is None:
        problems.append("deployed git SHA could not be determined")
    elif deployed_sha != user.approved_git_sha:
        problems.append(f"deployed code {deployed_sha} != approved_git_sha {user.approved_git_sha}")
    if common_hash != user.approved_common_hash:
        problems.append(
            f"common.yaml sha256 {common_hash} != approved_common_hash {user.approved_common_hash}"
        )
    if problems:
        raise ApprovalPinMismatchError(
            f"user {user.user}: refusing to run (OPS-10): " + "; ".join(problems)
        )


@dataclass(frozen=True)
class RunHashes:
    """What every run stores (OPS-10, SYS-15): config hash, spec_hash, card_set_hash."""

    config_hash: str
    spec_hash: str
    card_set_hash: str | None


# ---------------------------------------------------------------------------
# OPS-12 (v2.10)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CardEvidence:
    """Evidence from the hypothesis registry (M3) that ``mode: L1`` may be selected.

    ``h1_passed_with_approval``: card H1 has result ``passed`` and an owner
    approval record. ``h11_passed_rates``: marginal rates at which H11 passed.
    """

    h1_passed_with_approval: bool
    h11_passed_rates: frozenset[Decimal]


def tranche_count(common: CommonConfig, sizing_nav: Decimal) -> int:
    """Effective tranche count N (PRT-14): 1 or ``tranches_max``.

    N = tranches_max only if min(base weight) x sizing NAV / tranches_max >=
    tranche_min_order_mult x min_order_value_aud; otherwise N = 1.
    """
    if not isinstance(sizing_nav, Decimal):
        raise TypeError("sizing_nav must be Decimal (SYS-13)")
    l1 = common.l1
    smallest = min(s.base_weight for s in common.sleeves.values())
    smallest_order = smallest * sizing_nav / l1.tranches_max
    if smallest_order >= l1.tranche_min_order_mult * l1.min_order_value_aud:
        return l1.tranches_max
    return 1


@dataclass(frozen=True)
class Ops12Result:
    ok: bool
    tranche_count: int
    sizing_nav: Decimal
    transition_orders: dict[str, Decimal]
    problems: tuple[str, ...]

    @property
    def message(self) -> str:
        orders = ", ".join(f"{k} {v}" for k, v in sorted(self.transition_orders.items()))
        head = (
            f"OPS-12: N={self.tranche_count} at sizing NAV {self.sizing_nav}; "
            f"transition orders {orders}"
        )
        return head if self.ok else head + ". FAILED: " + "; ".join(self.problems)


def ops12_check(
    common: CommonConfig,
    user: UserConfig,
    sizing_nav: Decimal,
    cards: CardEvidence | None = None,
    *,
    as_of: date | None = None,
) -> Ops12Result:
    """The OPS-12 validation (hard at ``trader init`` and on any config change).

    ``cards`` is the registry evidence for ``mode: L1``; ``None`` means no
    evidence is available, which refuses ``mode: L1`` (fail closed).
    The tax entity/residency and ``hosting`` value checks are also enforced by
    the schema (``Literal`` fields) before this runs.
    """
    if not isinstance(sizing_nav, Decimal):
        raise TypeError("sizing_nav must be Decimal (SYS-13)")
    problems: list[str] = []
    n = tranche_count(common, sizing_nav)
    orders: dict[str, Decimal] = {}
    for sym, sleeve in common.sleeves.items():
        order = (sleeve.base_weight * sizing_nav / n).quantize(CENT, rounding=ROUND_DOWN)
        orders[sym] = order
        if order < common.l1.min_order_value_aud:
            problems.append(
                f"{sym} transition order {order} AUD at N={n} is below "
                f"min_order_value_aud {common.l1.min_order_value_aud}"
            )
    # tax.entity / tax.residency (TAX-03) and hosting (USR-10) are Literal fields: any
    # other value has already failed schema validation, which is an OPS-12 failure.
    live = user.ibkr.mode is IbkrMode.LIVE
    day = as_of or asx_today()
    year_rates = common.research.rates_for(day)
    mr = user.tax.marginal_rate
    if mr is None:
        if live:
            problems.append("tax.marginal_rate must be set for a live account")
    elif year_rates is None:
        problems.append(f"research.marginal_rates has no rates for income year {income_year(day)}")
    elif mr not in year_rates:
        problems.append(
            f"tax.marginal_rate {mr} is not one of research.marginal_rates[{income_year(day)}]"
        )
    if user.mode == "L1":
        if common.card_set_hash is None:
            problems.append("mode: L1 needs a frozen card set (card_set_hash is null)")
        if cards is None or not cards.h1_passed_with_approval:
            problems.append("mode: L1 needs card H1 with result passed and an owner approval")
        elif mr is None or mr not in cards.h11_passed_rates:
            problems.append("mode: L1 needs H11 passed at the user's tax.marginal_rate")
        if live and user.limits.backtest_max_drawdown is None:
            problems.append("limits.backtest_max_drawdown must be set for a live account in L1")
    return Ops12Result(
        ok=not problems,
        tranche_count=n,
        sizing_nav=sizing_nav,
        transition_orders=orders,
        problems=tuple(problems),
    )


def enforce_ops12(result: Ops12Result) -> None:
    """OPS-12 failures always stop validation (v2.10: no warning-only mode)."""
    if not result.ok:
        raise ConfigValidationError(result.message)


def default_sizing_nav(user: UserConfig) -> Decimal:
    """Sizing NAV used for validation when no live NAV is available: the
    configured base ``capital_cap_aud`` (sizing NAV can never exceed the cap)."""
    return user.capital_cap_aud


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LoadedConfig:
    common: CommonConfig
    user: UserConfig
    limits: EffectiveLimits
    common_hash: str
    user_hash: str
    config_hash: str
    common_bytes: bytes = field(repr=False)
    user_bytes: bytes = field(repr=False)

    @property
    def run_hashes(self) -> RunHashes:
        return RunHashes(self.config_hash, self.common.spec_hash, self.common.card_set_hash)


def _parse(model: type[_Model], raw: object, source: str) -> Any:
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        raise ConfigValidationError(f"{source}: {exc}") from exc


def parse_common(data: bytes, source: str = COMMON_CONFIG_NAME) -> CommonConfig:
    try:
        raw = load_yaml(data.decode("utf-8"))
    except Exception as exc:
        raise ConfigValidationError(f"{source}: invalid YAML: {exc}") from exc
    _refuse_secrets(raw, source)
    result: CommonConfig = _parse(CommonConfig, raw, source)
    return result


def parse_user(data: bytes, source: str) -> UserConfig:
    try:
        raw = load_yaml(data.decode("utf-8"))
    except Exception as exc:
        raise ConfigValidationError(f"{source}: invalid YAML: {exc}") from exc
    _refuse_secrets(raw, source)
    result: UserConfig = _parse(UserConfig, raw, source)
    return result


def check_user_file_permissions(path: Path) -> None:
    mode = path.stat().st_mode
    if mode & USER_CONFIG_FORBIDDEN_MODE_BITS:
        raise ConfigPermissionError(
            f"{path}: per-user config must be owner-only (chmod 600); mode is {oct(mode & 0o777)}"
        )


def load_common(config_dir: Path) -> CommonConfig:
    path = config_dir / COMMON_CONFIG_NAME
    return parse_common(path.read_bytes(), str(path))


def load_config(
    config_dir: Path,
    user: str,
    *,
    deployed_sha: str | None,
    check_pins: bool = True,
) -> LoadedConfig:
    """Load and fully validate ``common.yaml`` + ``<user>.yaml``.

    ``check_pins=False`` is only for tooling that must compute hashes before a
    user has approved them (``trader validate-config --print-hashes``); the
    runner always checks pins.
    """
    common_path = config_dir / COMMON_CONFIG_NAME
    user_path = config_dir / f"{user}.yaml"
    for p in (common_path, user_path):
        if not p.is_file():
            raise ConfigError(f"missing config file {p}")
    check_user_file_permissions(user_path)
    common_bytes = common_path.read_bytes()
    user_bytes = user_path.read_bytes()
    common = parse_common(common_bytes, str(common_path))
    user_cfg = parse_user(user_bytes, str(user_path))
    if user_cfg.user != user:
        raise ConfigValidationError(
            f"{user_path}: 'user: {user_cfg.user}' does not match file name"
        )
    limits = check_user_against_common(common, user_cfg)
    common_hash = sha256_bytes(common_bytes)
    if check_pins:
        check_approval_pins(user_cfg, common_hash, deployed_sha)
    return LoadedConfig(
        common=common,
        user=user_cfg,
        limits=limits,
        common_hash=common_hash,
        user_hash=sha256_bytes(user_bytes),
        config_hash=compute_config_hash(common_bytes, user_bytes),
        common_bytes=common_bytes,
        user_bytes=user_bytes,
    )
