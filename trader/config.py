"""Configuration loading and validation (spec §18, §14; OPS-10, OPS-11, OPS-12).

``config/common.yaml`` holds shared strategy settings; ``config/<user>.yaml``
holds one user's account, limits, contacts and approval pins. Both are
validated with pydantic; an invalid file stops the run.

Rules implemented here:

* Schema exactly per §18; unknown keys are rejected (``extra="forbid"``).
* Personal limits may only be tighter than the common defaults (§14, §18).
* Secrets never appear in config files (OPS-11): a key/value scan refuses them.
* Approval pins: ``approved_git_sha`` must equal the deployed code SHA and
  ``approved_common_hash`` must equal the SHA-256 of ``common.yaml``; any
  mismatch refuses to run (OPS-10, §14).
* OPS-12: the median full-trend position x sizing NAV must reach
  ``min_order_value_aud``; a hard failure at ``trader init`` and on any config
  change, a warning otherwise.
"""

from __future__ import annotations

import hashlib
import itertools
import re
import statistics
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, time
from decimal import Decimal
from enum import StrEnum
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
    COMMON_CONFIG_NAME,
    GIT_SHA_LENGTH,
    SHA256_HEX_LENGTH,
    USER_CONFIG_FORBIDDEN_MODE_BITS,
)
from trader.enums import IbkrMode, ParcelMethod
from trader.timeutil import parse_hhmm
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
    # SYS-13: money is never built from a binary float.
    if isinstance(v, float):
        raise ValueError("money must be written as a decimal literal, not a float")
    if isinstance(v, bool):
        raise ValueError("money must be a number")
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
DecRatio = Annotated[Decimal, BeforeValidator(_reject_float), Field(ge=0, le=1)]
Ratio = Annotated[float, Field(ge=0, le=1)]
PosFloat = Annotated[float, Field(gt=0)]
PosInt = Annotated[StrictInt, Field(gt=0)]
NonNegInt = Annotated[StrictInt, Field(ge=0)]
Clock = Annotated[time, BeforeValidator(_clock)]
Symbol = Annotated[StrictStr, AfterValidator(_symbol)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# common.yaml
# ---------------------------------------------------------------------------


class ColdStart(_Model):
    a: Clock
    b: Clock


class DecideSchedule(_Model):
    first: Clock
    second: Clock
    alternate_daily: StrictBool


_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _weekday_clock(v: object) -> tuple[str, time]:
    if not isinstance(v, str) or len(v.split()) != 2:
        raise ValueError("expected 'Ddd HH:MM', e.g. 'Sat 06:00'")
    day, hhmm = v.split()
    if day not in _WEEKDAYS:
        raise ValueError(f"unknown weekday {day!r}")
    return day, parse_hhmm(hhmm)


def _window(v: tuple[time, time]) -> tuple[time, time]:
    if not v[0] < v[1]:
        raise ValueError("window start must be before end")
    return v


Window = Annotated[tuple[Clock, Clock], AfterValidator(_window)]


class ScheduleConfig(_Model):
    """Job times, Australia/Sydney (SYS-14). Post-close times do not shift on half-days."""

    gateway_stop: Annotated[tuple[str, time], BeforeValidator(_weekday_clock)]
    cold_start: ColdStart
    twofa_window: Window
    ingest_flows: tuple[Clock, Clock]
    pre_open_check: Clock
    veto_deadline: Clock
    event_check: Clock
    submit_shares: Window
    close_auction_orders: Clock
    escalate_exits: Window
    vas_orders: Window
    reconcile: tuple[Clock, Clock]
    fetch_broker_bars: Clock
    fetch_vendor_data: Window
    quality_check: Clock
    mark_to_market: Clock
    decide: DecideSchedule
    evening_report: Clock
    decision_cutoff: Clock
    backup: Clock


class DataConfig(_Model):
    min_bars_share: PosInt
    min_bars_index: PosInt
    cross_source_tolerance: Ratio
    max_unexplained_jump: Ratio
    driver_stale_bdays: PosInt
    fx_stale_bdays: PosInt
    single_source_max_sessions: NonNegInt
    futures_roll_bdays_before_expiry: NonNegInt


class MomentumSpec(_Model):
    lookback: PosInt
    skip: NonNegInt = 0
    vs_cash: StrictBool = False

    @model_validator(mode="after")
    def _skip_lt_lookback(self) -> Self:
        if self.skip >= self.lookback:
            raise ValueError("momentum skip must be less than lookback")
        return self


class SmaCross(_Model):
    fast: PosInt
    slow: PosInt

    @model_validator(mode="after")
    def _order(self) -> Self:
        if self.fast >= self.slow:
            raise ValueError("sma_cross.fast must be < slow")
        return self


class Chandelier(_Model):
    atr: PosInt
    mult: PosFloat
    stop_days: PosInt
    reentry_high: PosInt
    reentry_min_tr: Ratio


class TrendConfig(_Model):
    momentum: Annotated[list[MomentumSpec], Field(min_length=1)]
    price_above_sma: Annotated[list[PosInt], Field(min_length=1)]
    sma_cross: SmaCross
    chandelier: Chandelier


class DipExit(_Model):
    above_sma: PosInt
    rsi_above: Annotated[float, Field(ge=0, le=100)]
    max_days: PosInt


class SleeveSwitch(_Model):
    on_mult: PosFloat
    off_mult: PosFloat
    evaluate: Literal["first_trading_day_of_month"]

    @model_validator(mode="after")
    def _hysteresis(self) -> Self:
        if not self.on_mult > self.off_mult:
            raise ValueError("sleeve_switch.on_mult must exceed off_mult (hysteresis)")
        return self


class DipConfig(_Model):
    rsi_period: PosInt
    rsi_min_bars: PosInt
    entry_below: Annotated[float, Field(ge=0, le=100)]
    exit: DipExit
    trend_filter_sma: PosInt
    sleeve_switch: SleeveSwitch


Driver = Literal["copper", "iron_ore", "brent"]


class BasketEntry(_Model):
    from_: Annotated[date, Field(alias="from")]
    weights: dict[Driver, Ratio]

    @model_validator(mode="after")
    def _sum_one(self) -> Self:
        if not self.weights or abs(sum(self.weights.values()) - 1.0) > 1e-9:
            raise ValueError("basket weights must sum to 1")
        return self


class CommodityConfig(_Model):
    lookbacks: Annotated[list[PosInt], Field(min_length=1)]
    baskets: dict[Symbol, Annotated[list[BasketEntry], Field(min_length=1)]]

    @model_validator(mode="after")
    def _basket_dates(self) -> Self:
        for sym, entries in self.baskets.items():
            froms = [e.from_ for e in entries]
            if froms != sorted(froms, reverse=True) or len(set(froms)) != len(froms):
                raise ValueError(
                    f"{sym} basket entries must be in strictly descending 'from' order"
                )
        return self


def _sums_to_one(weights: Mapping[str, float], where: str) -> None:
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError(f"{where} family weights must sum to 1")


class CommodityFamilyWeights(_Model):
    trend: Ratio
    dip: Ratio
    commodity: Ratio


class OtherFamilyWeights(_Model):
    trend: Ratio
    dip: Ratio


class CommodityNamesWeights(_Model):
    dip_on: CommodityFamilyWeights
    dip_off: CommodityFamilyWeights

    @model_validator(mode="after")
    def _sums(self) -> Self:
        _sums_to_one(self.dip_on.model_dump(), "commodity_names.dip_on")
        _sums_to_one(self.dip_off.model_dump(), "commodity_names.dip_off")
        if self.dip_off.dip != 0:
            raise ValueError("commodity_names.dip_off.dip must be 0")
        return self


class OtherNamesWeights(_Model):
    dip_on: OtherFamilyWeights
    dip_off: OtherFamilyWeights

    @model_validator(mode="after")
    def _sums(self) -> Self:
        _sums_to_one(self.dip_on.model_dump(), "other.dip_on")
        _sums_to_one(self.dip_off.model_dump(), "other.dip_off")
        if self.dip_off.dip != 0:
            raise ValueError("other.dip_off.dip must be 0")
        return self


class FamilyWeights(_Model):
    commodity_names: CommodityNamesWeights
    other: OtherNamesWeights


class SignalsConfig(_Model):
    trend: TrendConfig
    dip: DipConfig
    commodity: CommodityConfig
    family_weights: FamilyWeights


Offsets = tuple[StrictInt, StrictInt]


class BlackoutConfig(_Model):
    """Execution-date offsets around event date V. Keys other than ``default`` and
    ``estimate_widen`` are per-symbol overrides (e.g. ``CSL: [-3, 0]``)."""

    default: Offsets
    estimate_widen: NonNegInt
    overrides: dict[Symbol, Offsets] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _split_overrides(cls, data: Any) -> Any:
        if isinstance(data, Mapping) and "overrides" not in data:
            fixed = {"default", "estimate_widen"}
            data = {
                **{k: v for k, v in data.items() if k in fixed},
                "overrides": {k: v for k, v in data.items() if k not in fixed},
            }
        return data

    @model_validator(mode="after")
    def _offsets(self) -> Self:
        for name, (lo, hi) in [("default", self.default), *self.overrides.items()]:
            # V itself is always included (§5), so the window must cover offset 0.
            if not lo <= 0 <= hi:
                raise ValueError(f"blackout {name} offsets must satisfy start <= 0 <= end")
        return self

    def offsets_for(self, symbol: str) -> tuple[int, int]:
        return self.overrides.get(symbol, self.default)


class NewsFilter(_Model):
    enabled: StrictBool
    veto_days: PosInt

    @model_validator(mode="after")
    def _off_in_v1(self) -> Self:
        # D7: off in v1 until a licensed source is confirmed; changing needs a spec update.
        if self.enabled:
            raise ValueError("filters.news.enabled must be false in v1 (decision D7)")
        return self


class InsiderSellFilter(_Model):
    enabled: StrictBool
    min_directors: PosInt
    window_days: PosInt
    block_days: PosInt


class DowngradesFilter(_Model):
    enabled: StrictBool
    min_count: PosInt
    window_days: PosInt
    block_days: PosInt


class RegimeFilter(_Model):
    sma: PosInt
    off_below: PosFloat
    on_above: PosFloat
    on_confirm_closes: PosInt
    vol_window: PosInt
    vol_off_pctile: Ratio
    vol_on_pctile: Ratio
    vol_history: PosInt
    off_stock_cap: Ratio
    off_vas_fraction: Ratio

    @model_validator(mode="after")
    def _hysteresis(self) -> Self:
        if not self.off_below < 1 < self.on_above:
            raise ValueError("regime: need off_below < 1 < on_above")
        if not self.vol_on_pctile < self.vol_off_pctile:
            raise ValueError("regime: need vol_on_pctile < vol_off_pctile")
        return self


class FiltersConfig(_Model):
    blackout: BlackoutConfig
    news: NewsFilter
    insider_sell: InsiderSellFilter
    downgrades: DowngradesFilter
    regime: RegimeFilter


class CslGapCap(_Model):
    weight: Ratio
    vol_window: PosInt
    vol_on: PosFloat
    release_closes: PosInt


class PortfolioVolCap(_Model):
    cap: PosFloat
    engage: PosFloat
    cov_window: PosInt

    @model_validator(mode="after")
    def _band(self) -> Self:
        if self.engage < self.cap:
            raise ValueError("portfolio_vol_cap.engage must be >= cap")
        return self


class SizingConfig(_Model):
    n_names: PosInt
    target_vol: PosFloat
    ewma_lambda: Annotated[float, Field(gt=0, lt=1)]
    ewma_seed_returns: PosInt
    max_vol_scale: PosFloat
    vol_floors: dict[Symbol, PosFloat]
    per_name_cap: Ratio
    cluster_caps: dict[StrictStr, Ratio]
    csl_gap_cap: CslGapCap
    portfolio_vol_cap: PortfolioVolCap
    cash_target: Ratio
    cash_buffer: Ratio
    rebuild_sleeve_below: Ratio
    min_weight_change: Ratio
    min_order_value_aud: PositiveMoney
    min_exit_value_aud: PositiveMoney

    @model_validator(mode="after")
    def _cash(self) -> Self:
        if not self.cash_buffer < self.rebuild_sleeve_below < self.cash_target:
            raise ValueError("sizing: need cash_buffer < rebuild_sleeve_below < cash_target")
        if self.min_exit_value_aud > self.min_order_value_aud:
            raise ValueError("sizing: min_exit_value_aud must not exceed min_order_value_aud")
        return self


class ContinuousStep(_Model):
    continuous: Literal[True]
    at: Clock
    floor: DecRatio


class Commission(_Model):
    min_aud_incl_gst: PositiveMoney
    rate_incl_gst: DecRatio
    tolerance: Ratio


class ExecutionConfig(_Model):
    exchange: Literal["ASX"]
    collar: DecRatio
    exit_ladder: tuple[DecRatio, DecRatio, ContinuousStep]
    vas_band: DecRatio
    commission: Commission

    @model_validator(mode="after")
    def _ladder(self) -> Self:
        s1, s2, s3 = self.exit_ladder
        if not self.collar <= s1 < s2 < s3.floor:
            raise ValueError("exit_ladder steps must widen: collar <= step1 < step2 < floor")
        return self


class RiskLimitsCommon(_Model):
    max_order_value_aud: PositiveMoney
    max_order_value_pct: DecRatio
    backtest_max_drawdown: Ratio | None
    adv_pct: Ratio
    adv_days: PosInt
    max_orders_per_day: PosInt
    daily_loss_pct: Ratio
    soft_drawdown_pct: Ratio
    hard_drawdown_pct: Ratio
    min_live_sharpe_12m: float | None

    @model_validator(mode="after")
    def _dd(self) -> Self:
        if not self.soft_drawdown_pct < self.hard_drawdown_pct:
            raise ValueError("risk_defaults: soft_drawdown_pct must be < hard_drawdown_pct")
        return self


class BacktestPeriods(_Model):
    design: tuple[date, date]
    validation: tuple[date, date]
    holdout: tuple[date, date]

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        seq = [self.design, self.validation, self.holdout]
        for start, end in seq:
            if start > end:
                raise ValueError("backtest period start after end")
        for (_, e1), (s2, _) in itertools.pairwise(seq):
            if not e1 < s2:
                raise ValueError("backtest periods must be ordered and non-overlapping")
        return self


class SlippageBps(_Model):
    shares: Annotated[float, Field(ge=0)]
    vas: Annotated[float, Field(ge=0)]


class StressBps(_Model):
    shares: list[Annotated[float, Field(ge=0)]]
    vas: list[Annotated[float, Field(ge=0)]]


class BacktestCosts(_Model):
    exchange_clearing: Ratio
    slippage_bps: SlippageBps
    stress_bps: StressBps


class RandomEntry(_Model):
    runs: PosInt
    block_days: PosInt
    seed: NonNegInt


class BacktestConfig(_Model):
    periods: BacktestPeriods
    initial_navs: Annotated[list[PositiveMoney], Field(min_length=1)]
    costs: BacktestCosts
    tax_marginal_rate: Ratio
    random_entry: RandomEntry


class ShadowConfig(_Model):
    short_interest: StrictBool
    analog: StrictBool
    trend_health: StrictBool
    meta_model: StrictBool


class AlertsCommon(_Model):
    warning_repeat_min: PosInt


class BackupCommon(_Model):
    keep_daily: PosInt
    keep_monthly: PosInt


class UniverseRule(_Model):
    """v1.3 amendment: rule for choosing a paper universe. Schema only in M0."""

    source: Literal["ASX20"]
    max_per_sector: PosInt
    max_iron_ore_majors: NonNegInt


class CommonConfig(_Model):
    version: Literal[1]
    universe: Annotated[list[Symbol], Field(min_length=1)]
    index_etf: Symbol
    proxies: dict[Symbol, list[Symbol]]
    clusters: dict[StrictStr, list[Symbol]]
    schedule: ScheduleConfig
    data: DataConfig
    signals: SignalsConfig
    filters: FiltersConfig
    sizing: SizingConfig
    execution: ExecutionConfig
    risk_defaults: RiskLimitsCommon
    backtest: BacktestConfig
    shadow: ShadowConfig
    alerts: AlertsCommon
    backup: BackupCommon
    # v1.3 amendment: schema only, no behaviour in M0.
    paper_universe: list[Symbol] | None = None
    universe_rule: UniverseRule | None = None

    @model_validator(mode="after")
    def _cross(self) -> Self:
        uni = self.universe
        if len(set(uni)) != len(uni):
            raise ValueError("universe has duplicates")
        if self.index_etf in uni:
            raise ValueError("index_etf must not be in the scored universe")
        if self.sizing.n_names != len(uni):
            raise ValueError("sizing.n_names must equal the number of universe shares (N fixed)")
        members = [s for syms in self.clusters.values() for s in syms]
        if sorted(members) != sorted(uni):
            raise ValueError("every universe share must be in exactly one cluster")
        if set(self.sizing.vol_floors) != set(uni):
            raise ValueError("sizing.vol_floors must cover exactly the universe")
        if not set(self.sizing.cluster_caps) <= set(self.clusters):
            raise ValueError("sizing.cluster_caps refers to an unknown cluster")
        if not set(self.signals.commodity.baskets) <= set(uni):
            raise ValueError("commodity baskets refer to a symbol outside the universe")
        if not set(self.proxies) <= {*uni, self.index_etf}:
            raise ValueError("proxies refer to an unknown symbol")
        if not set(self.filters.blackout.overrides) <= set(uni):
            raise ValueError("blackout overrides refer to a symbol outside the universe")
        if self.paper_universe is not None and len(set(self.paper_universe)) != len(
            self.paper_universe
        ):
            raise ValueError("paper_universe has duplicates")
        if self.sizing.per_name_cap + self.sizing.cash_target > 1:
            raise ValueError("per_name_cap + cash_target must not exceed 1")
        return self

    @property
    def commodity_names(self) -> frozenset[str]:
        return frozenset(self.signals.commodity.baskets)


# ---------------------------------------------------------------------------
# <user>.yaml
# ---------------------------------------------------------------------------

_HEX40 = re.compile(rf"^[0-9a-f]{{{GIT_SHA_LENGTH}}}$")
_HEX64 = re.compile(rf"^[0-9a-f]{{{SHA256_HEX_LENGTH}}}$")
_AGE_PUB = re.compile(r"^age1[02-9ac-hj-np-z]{58}$")  # bech32 charset
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _git_sha(v: str) -> str:
    if not _HEX40.fullmatch(v):
        raise ValueError("approved_git_sha must be a full 40-char lowercase hex git SHA")
    return v


def _sha256(v: str) -> str:
    if not _HEX64.fullmatch(v):
        raise ValueError("approved_common_hash must be a 64-char lowercase hex SHA-256")
    return v


TRADER_CLIENT_ID = 11  # §19: client ID 11 for the trader, 12 for tools
_MODE_PORT = {IbkrMode.PAPER: 4004, IbkrMode.LIVE: 4003}


class IbkrConfig(_Model):
    account_id: Annotated[StrictStr, Field(pattern=r"^(U|DU)\d{5,10}$")]
    gateway_host: StrictStr
    port: Literal[4003, 4004]
    client_id: StrictInt
    mode: IbkrMode

    @model_validator(mode="after")
    def _port_matches_mode(self) -> Self:
        if self.port != _MODE_PORT[self.mode]:
            raise ValueError(f"ibkr.port {self.port} does not match mode {self.mode} (§19)")
        if self.client_id != TRADER_CLIENT_ID:
            raise ValueError(f"ibkr.client_id must be {TRADER_CLIENT_ID} for the trader (§19)")
        return self


class UserLimits(_Model):
    """Personal limits; each may only be tighter than ``risk_defaults``."""

    max_order_value_aud: PositiveMoney | None = None
    max_orders_per_day: PosInt | None = None
    daily_loss_pct: Ratio | None = None
    hard_drawdown_pct: Ratio | None = None


class UserBacktest(_Model):
    initial_nav: PositiveMoney


class UserAlerts(_Model):
    telegram_chat_id: Annotated[StrictStr, Field(pattern=r"^-?\d{1,20}$")]
    email: Annotated[StrictStr, Field(pattern=_EMAIL.pattern)]


class UserTax(_Model):
    marginal_rate: Ratio
    parcel_method: ParcelMethod


class UserBackup(_Model):
    onedrive_path: StrictStr
    age_public_key: Annotated[StrictStr, Field(pattern=_AGE_PUB.pattern)]


class UserDashboard(_Model):
    snapshot_key_id: StrictStr


SmallAccountAsset = Literal["VAS", "VGS", "PMGOLD", "CASH"]


def _default_small_universe() -> list[SmallAccountAsset]:
    return ["VAS", "VGS", "CASH"]


class SmallAccount(_Model):
    """Small-account mode (spec v1.3 amendment, §9.1). Schema only in M0;
    behaviour (PRT-10..PRT-17) is M2."""

    enabled: StrictBool = True
    universe: Annotated[list[SmallAccountAsset], Field(min_length=1)] = Field(
        default_factory=_default_small_universe
    )
    switch_buffer: Annotated[float, Field(ge=0, le=0.1)] = 0.02
    momentum_months: Annotated[list[PosInt], Field(min_length=1)] = Field(
        default_factory=lambda: [6, 9, 12]
    )
    cash_proxy: Symbol | None = None

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        if len(set(self.universe)) != len(self.universe):
            raise ValueError("small_account.universe has duplicates")
        if len(set(self.momentum_months)) != len(self.momentum_months):
            raise ValueError("small_account.momentum_months has duplicates")
        return self


class UserConfig(_Model):
    user: Annotated[StrictStr, Field(pattern=r"^[a-z][a-z0-9_]{0,15}$")]
    approved_git_sha: Annotated[StrictStr, AfterValidator(_git_sha)]
    approved_common_hash: Annotated[StrictStr, AfterValidator(_sha256)]
    ibkr: IbkrConfig
    capital_cap_aud: PositiveMoney | None
    small_account: SmallAccount = Field(default_factory=SmallAccount)
    exclude_symbols: list[Symbol]
    limits: UserLimits
    backtest: UserBacktest
    alerts: UserAlerts
    tax: UserTax
    backup: UserBackup
    dashboard: UserDashboard

    @model_validator(mode="after")
    def _own_gateway(self) -> Self:
        # §14/§19 isolation: trader-a reaches only gw-a.
        if self.ibkr.gateway_host != f"gw-{self.user}":
            raise ValueError(f"ibkr.gateway_host must be 'gw-{self.user}' (§14 isolation)")
        if len(set(self.exclude_symbols)) != len(self.exclude_symbols):
            raise ValueError("exclude_symbols has duplicates")
        return self


# ---------------------------------------------------------------------------
# Cross-file checks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EffectiveLimits:
    """Risk limits after applying the user's (tighter) overrides."""

    max_order_value_aud: Decimal
    max_order_value_pct: Decimal
    max_orders_per_day: int
    daily_loss_pct: float
    hard_drawdown_pct: float
    soft_drawdown_pct: float


def check_user_against_common(common: CommonConfig, user: UserConfig) -> EffectiveLimits:
    """Personal limits may only be tighter; exclusions must be universe shares."""
    errors: list[str] = []
    d, lim = common.risk_defaults, user.limits
    pairs: list[tuple[str, Decimal | float | int | None, Decimal | float | int]] = [
        ("max_order_value_aud", lim.max_order_value_aud, d.max_order_value_aud),
        ("max_orders_per_day", lim.max_orders_per_day, d.max_orders_per_day),
        ("daily_loss_pct", lim.daily_loss_pct, d.daily_loss_pct),
        ("hard_drawdown_pct", lim.hard_drawdown_pct, d.hard_drawdown_pct),
    ]
    for name, mine, default in pairs:
        if mine is not None and mine > default:
            errors.append(
                f"limits.{name}={mine} is looser than the common default {default}; "
                "personal limits may only be tighter"
            )
    if lim.hard_drawdown_pct is not None and lim.hard_drawdown_pct <= d.soft_drawdown_pct:
        errors.append("limits.hard_drawdown_pct must stay above risk_defaults.soft_drawdown_pct")
    unknown = set(user.exclude_symbols) - set(common.universe)
    if unknown:
        errors.append(f"exclude_symbols not in universe: {sorted(unknown)}")
    if errors:
        raise ConfigValidationError("; ".join(errors))
    return EffectiveLimits(
        max_order_value_aud=lim.max_order_value_aud or d.max_order_value_aud,
        max_order_value_pct=d.max_order_value_pct,
        max_orders_per_day=lim.max_orders_per_day or d.max_orders_per_day,
        daily_loss_pct=lim.daily_loss_pct if lim.daily_loss_pct is not None else d.daily_loss_pct,
        hard_drawdown_pct=(
            lim.hard_drawdown_pct if lim.hard_drawdown_pct is not None else d.hard_drawdown_pct
        ),
        soft_drawdown_pct=d.soft_drawdown_pct,
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
)
# Keys whose names match _SECRET_KEY_RE but are known to hold public material.
_PUBLIC_KEY_NAMES = frozenset({"age_public_key", "snapshot_key_id"})


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


# ---------------------------------------------------------------------------
# OPS-12: account size vs minimum order
# ---------------------------------------------------------------------------


class Ops12Mode(StrEnum):
    HARD = "hard"  # trader init, or config changed: failure stops the run
    WARN = "warn"  # other startups: warning in the evening report


@dataclass(frozen=True)
class Ops12Result:
    ok: bool
    median_position_aud: Decimal
    min_order_value_aud: Decimal
    sizing_nav: Decimal
    per_symbol_weight: dict[str, float]
    dip_sleeve_assumed_on: bool
    vol_source: str
    message: str


def ops12_check(
    common: CommonConfig,
    sizing_nav: Decimal,
    *,
    vol_estimates: Mapping[str, float] | None = None,
    dip_sleeve_on: bool | None = None,
) -> Ops12Result:
    """Median full-trend position x sizing NAV vs ``min_order_value_aud`` (§9, OPS-12).

    Full-trend weight of share i = w_TR(i) / N x min(max_vol_scale,
    target_vol / max(sigma_i, floor_i)). w_TR is the trend family weight for the
    share's group under the current dip-sleeve state. If the dip-sleeve state is
    unknown, the dip-ON weights (smaller trend weight) are used: conservative.
    If no volatility estimates are available, sigma_i = floor_i (see DECISIONS.md).
    """
    if not isinstance(sizing_nav, Decimal):
        raise TypeError("sizing_nav must be Decimal (SYS-13)")
    s = common.sizing
    fw = common.signals.family_weights
    assume_on = True if dip_sleeve_on is None else dip_sleeve_on
    weights: dict[str, float] = {}
    for sym in common.universe:
        group = fw.commodity_names if sym in common.commodity_names else fw.other
        w_tr = (group.dip_on if assume_on else group.dip_off).trend
        floor = s.vol_floors[sym]
        sigma = floor if vol_estimates is None else vol_estimates[sym]
        scale = min(s.max_vol_scale, s.target_vol / max(sigma, floor))
        weights[sym] = w_tr / s.n_names * scale
    median_w = statistics.median(weights.values())
    # Convert the float weight to Decimal via repr-free rounding (SYS-13 boundary).
    median_pos = (Decimal(str(round(median_w, 10))) * sizing_nav).quantize(Decimal("0.01"))
    ok = median_pos >= s.min_order_value_aud
    msg = (
        f"OPS-12: median full-trend position {median_pos} AUD "
        f"({median_w:.4%} of sizing NAV {sizing_nav}) "
        f"{'>=' if ok else '<'} min_order_value_aud {s.min_order_value_aud}"
    )
    return Ops12Result(
        ok=ok,
        median_position_aud=median_pos,
        min_order_value_aud=s.min_order_value_aud,
        sizing_nav=sizing_nav,
        per_symbol_weight=weights,
        dip_sleeve_assumed_on=assume_on,
        vol_source="floor" if vol_estimates is None else "estimate",
        message=msg,
    )


def enforce_ops12(result: Ops12Result, mode: Ops12Mode) -> str | None:
    """Raise in HARD mode on failure; return a warning text in WARN mode."""
    if result.ok:
        return None
    if mode is Ops12Mode.HARD:
        raise ConfigValidationError(
            result.message + ". Lower sizing.min_order_value_aud (e.g. 2000) or add capital."
        )
    return "WARNING " + result.message


def ops12_mode(
    *,
    is_init: bool,
    config_hash: str,
    known_hashes: Iterable[str],
    small_account_enabled: bool = False,
) -> Ops12Mode:
    """HARD at ``trader init`` and whenever the config hash has not been seen before.

    In small-account mode (§9.1 amendment) the full-trend sleeve is not traded,
    so OPS-12 is reported as a warning only; leaving small-account mode
    (``trader mode full --confirm``) is a config change and makes it HARD again.
    See docs/DECISIONS.md.
    """
    if small_account_enabled:
        return Ops12Mode.WARN
    if is_init or config_hash not in set(known_hashes):
        return Ops12Mode.HARD
    return Ops12Mode.WARN


def default_sizing_nav(user: UserConfig) -> Decimal:
    """Sizing NAV used for validation when no live NAV is available:
    min(user.backtest.initial_nav, capital_cap_aud)."""
    nav = user.backtest.initial_nav
    if user.capital_cap_aud is not None:
        nav = min(nav, user.capital_cap_aud)
    return nav


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
