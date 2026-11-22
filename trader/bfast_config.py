"""B-fast config schema (``config/bfast.yaml``). Strict: unknown keys are errors.

``mode`` is ``Literal["paper"]`` and ``broker.allow_live`` is ``Literal[False]``: a
config that asks for live trading does not validate (BW-SYS-16 in spirit: live needs
the signed gate record and an owner-reviewed code change, not a config edit).
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from trader.lines.band_trend import BandTrendParams
from trader.lines.emg2 import Emg2_20Params
from trader.orders import CommissionModel, OrderParams, OrderType
from trader.risk import RiskLimits
from trader.yamlio import load_yaml

if TYPE_CHECKING:
    from trader.tax_report import TaxParams

HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CommissionCfg(_M):
    """Review M1: the IBKR pricing plan's numbers (ex GST). Tiered tier I from IBKR's
    public schedule; ``fees_rate`` (ASX exchange / clearing pass-through) is
    [unverified] until the reality spike compares it with real fills."""

    tiered_rate: Decimal = Decimal("0.0008")
    tiered_min_aud: Decimal = Decimal("5.00")
    fixed_rate: Decimal = Decimal("0.0008")
    fixed_min_aud: Decimal = Decimal("6.00")
    fees_rate: Decimal = Decimal("0.00005")
    gst: Decimal = Decimal("0.10")


class BrokerCfg(_M):
    host: str
    port: int
    client_id: int
    account_id: str | None = None
    allow_live: Literal[False] = False
    pricing: Literal["tiered", "fixed"] = "tiered"  # review M1: the owner's IBKR plan
    commission: CommissionCfg = Field(default_factory=CommissionCfg)

    @field_validator("account_id")
    @classmethod
    def _paper_id(cls, v: str | None) -> str | None:
        if v is not None and not re.fullmatch(r"DU\d{5,10}", v):
            raise ValueError("account_id must be an IBKR paper account (DU...)")
        return v


class ExecutionCfg(_M):
    order_type: OrderType
    limit_band: Decimal = Field(gt=0, le=Decimal("0.05"))
    submit_at: str
    fallback_send_at: str
    fallback_cancel_at: str
    # L8: every broker-book order needs the owner's approval; "auto" (BW-APR-02) is
    # refused here so an unapproved order can never be sent (only the twin auto-approves)
    approval_mode: Literal["per_order", "batch"]
    approval_deadline: str
    buy_funds_wait_sessions: int = Field(ge=0, le=4)
    latest_send: str = "15:55"  # review H3: nothing is sent after this (early close: -10 min)
    no_order_days: list[date] = Field(default_factory=list)  # review H4: ad-hoc closures

    @field_validator("order_type")
    @classmethod
    def _no_lmt_yet(cls, v: OrderType) -> OrderType:
        # review M5: the LMT fallback (send 15:30, cancel 15:58) is not implemented; it is
        # refused until the reality spike decides LOC vs LMT and it is built and tested
        if v is not OrderType.LOC:
            raise ValueError("order_type LMT is not implemented yet (review M5): use LOC")
        return v

    @field_validator(
        "submit_at", "fallback_send_at", "fallback_cancel_at", "approval_deadline", "latest_send"
    )
    @classmethod
    def _hhmm(cls, v: str) -> str:
        if not HHMM.match(v):
            raise ValueError("time must be HH:MM")
        return v


class Emg2_20Cfg(_M):  # noqa: N801
    capital_cap_aud: Decimal = Field(gt=0, le=Decimal(10000))  # D-4: never above A$10,000
    slots: int = Field(ge=1, le=20)  # name count (BF-D1: 18)
    slot_unit_aud: Decimal = Field(ge=Decimal(500))  # L3 divisor (EMG2-18: A$550)
    min_parcel_aud: Decimal = Field(ge=Decimal(500))
    cash_reserve_aud: Decimal = Field(ge=0)
    skip_lottery: bool
    # BF-D35 (AMENDMENT_live_EMG2_18_C6.md): C6 = sell only after 6 month-ends held and
    # outside the top 40% of band C; L4 = the registered rule (kept for the paper comparison)
    sell_rule: Literal["L4", "C6"] = "L4"


class BandTrendCfg(_M):
    """L15 band-trend switch (``AMENDMENT_live_EMG2_18_BT.md``, owner decision; BF-D28).
    The window (10 month-ends) is the registered rule and is pinned here."""

    enabled: bool
    fund: str = Field(pattern=r"^[A-Z0-9]{3,6}$")  # A200, the record's ASX 200 fund
    months: int = Field(default=10, ge=10, le=10)
    top_up_fraction: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    # one fund order (BF-D28): never above the capital cap; paged above the A$800 limit
    fund_order_max_aud: Decimal = Field(default=Decimal(10000), ge=Decimal(500), le=Decimal(10000))
    fund_half_spread: Decimal = Field(default=Decimal("0.0005"), ge=0, le=Decimal("0.02"))


class PaperDryRunCfg(_M):
    """BF-D32: the paper dry run while the book's real L15 state is FUND. Extra decisions
    on the listed dates with the band-trend state forced to ``EMG2`` (real 18-share buy
    and sell flows) or ``FUND``, or ``REAL`` (the rule's own state: the FUND switch). Paper
    only: the schema has ``mode: paper`` and a ``DU`` account only, the app refuses a
    non-paper broker, and ``trader-bf run`` refuses the flag after ``until``."""

    until: date
    decisions: dict[date, Literal["EMG2", "FUND", "REAL"]] = Field(min_length=1)

    @model_validator(mode="after")
    def _inside(self) -> PaperDryRunCfg:
        late = [d for d in self.decisions if d > self.until]
        if late:
            raise ValueError(f"paper_dry_run decisions after until {self.until}: {late}")
        return self


class StartNormal(_M):
    start: Decimal
    normal: Decimal


class OrdersPerDay(_M):
    start: int = Field(ge=1, le=24)
    normal: int = Field(ge=1, le=24)  # review H6: 18 buys must fit (L10 amendment)
    hard: int = Field(ge=1, le=80)


class ReviewHalt(_M):
    review: Decimal
    halt: Decimal


class RiskCfg(_M):
    order_value_max_aud: Decimal = Field(gt=0, le=Decimal(800))
    orders_per_day: OrdersPerDay
    buys_per_day_aud: StartNormal
    price_band: Decimal = Field(gt=0, le=Decimal("0.05"))
    gap_hold: Decimal
    absurd_move: Decimal
    participation_max: Decimal = Field(gt=0, le=Decimal("0.05"))
    quote_stale_minutes: int = Field(ge=1, le=40)
    value_review_aud: Decimal
    value_halt_buys_aud: Decimal
    value_line_halt_aud: Decimal
    drawdown: ReviewHalt
    day_move: ReviewHalt
    real_money_floor: Decimal


class FlexPullCfg(_M):
    """BF-D27: the scheduled Flex Web Service download into ``data.flex_inbox``. No
    token or query id here (``extra=forbid``): both are Docker secrets only
    (``ibkr_flex_token``, ``ibkr_flex_query_id``)."""

    raw_dir: Path  # every response kept unchanged (raw store, source ``flex``)
    lookback_days: int = Field(default=7, ge=1, le=30)
    max_days: int = Field(default=30, ge=1, le=365)
    attempts: int = Field(default=2, ge=1, le=3)
    backoff_seconds: float = Field(default=5.0, ge=0, le=15)


class StoreRefreshCfg(_M):
    """BF-D31: the daily EODHD bulk refresh of ``data.forward_store`` on the server. No
    key here (``extra=forbid``): it is the Docker secret ``eodhd_api_token`` only."""

    raw_dir: Path  # every vendor response kept unchanged (raw store, source ``eodhd``)
    calls_per_day: int = Field(default=100000, ge=100)  # the plan's EODHD calls a GMT day
    bulk_call_cost: int = Field(default=100, ge=1, le=1000)  # EODHD counts a bulk call as 100
    min_rows: int = Field(default=1000, ge=1)  # closes dated D needed (about 1,400-1,900)
    min_share: Decimal = Field(default=Decimal("0.9"), gt=0, le=1)  # of the previous day's
    attempts: int = Field(default=2, ge=1, le=3)
    backoff_seconds: float = Field(default=5.0, ge=0, le=15)


class DataCfg(_M):
    forward_store: Path
    sim_book: str
    sim_half_spread: Decimal = Field(ge=0, le=Decimal("0.02"))
    # L13 / L11 (b): the registered 100 random twins of the simulated book (BF-D18)
    random_twins: int = Field(default=100, ge=100, le=100)
    random_prefix: str = Field(default="EMG2_18_RND", pattern=r"^[A-Z0-9_]{1,30}$")
    random_seed_base: int = Field(default=8550000, ge=8550000, le=8550000)
    etp_list: Path
    lic_list: Path
    # BF-D21: the pin is required and there is no fallback list; a missing or changed
    # frozen file refuses every decision and every order (fail closed, owner paged)
    lic_list_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    history_sessions: int = Field(ge=300)
    # BF-D23: the record keeper's CORPORATE_ACTIONS.csv (capital returns, specials,
    # demergers, in-specie, code changes; overrides the vendor's dividends); env
    # TRADER_BF_CA_CSV overrides the path; a missing file means vendor dividends only
    corporate_actions_csv: Path | None = None
    # IBKR Activity Flex statements (XML) of the broker book, read before each
    # reconciliation: its dividends and corporate actions are booked from them
    flex_inbox: Path | None = None
    # BF-D27: download the paper account's Flex statement into flex_inbox before the
    # 16:30 reconciliation (None: the inbox is filled by hand)
    flex_pull: FlexPullCfg | None = None
    # BF-D31: append the day's EODHD bulk files to forward_store after the close (the
    # store must then be mounted writable); None: the store is filled elsewhere
    store_refresh: StoreRefreshCfg | None = None

    @model_validator(mode="after")
    def _pull_needs_inbox(self) -> DataCfg:
        if self.flex_pull is not None and self.flex_inbox is None:
            raise ValueError("data.flex_pull needs data.flex_inbox")
        return self


class TaxCfg(_M):
    """BF-D29: ``trader-bf tax-report`` (Australian financial year; general information,
    not tax advice). FIFO is the default parcel method; ``min_tax`` (specific
    identification: loss parcels first, then discount-eligible gains, then the
    highest-cost short-term parcel) only after the owner's accountant confirms it (O-8).
    ``discount_days``: the record's 367-day safety margin for the 12-month CGT discount
    test. ``fund_codes``: managed funds / ETFs whose payments are trust distributions
    (with ``band_trend.fund`` added). ``amit_csv``: the owner's entries from each fund's
    annual (AMIT) tax statement; nothing secret."""

    parcel_method: Literal["FIFO", "min_tax"] = "FIFO"
    discount_days: int = Field(default=367, ge=366, le=400)
    # BF-D44 (owner, 22 Nov 2026): "12_months" = disposal later than acquisition + 12
    # months (the ATO test); "days" = held discount_days or more (BF-D29's margin)
    discount_rule: Literal["12_months", "days"] = "12_months"
    fund_codes: list[str] = Field(default_factory=list)
    amit_csv: Path | None = None
    # BF-D44: your marginal tax rate incl. Medicare levy (e.g. 0.345) for the app's estimate;
    # empty by default: set it on the server only, never in the repository
    marginal_rate: Decimal | None = Field(default=None, ge=0, le=Decimal("0.6"))
    # BF-D51: net capital losses carried in from before this book (as --prior-losses)
    prior_losses_aud: Decimal = Field(default=Decimal(0), ge=0)

    def params(self, funds: frozenset[str]) -> TaxParams:
        from trader.tax_report import TaxParams

        return TaxParams(self.parcel_method, self.discount_days, funds, self.discount_rule)


class TelegramCfg(_M):
    # needed only when notify.channel is telegram or both (BF-D40)
    allowed_chat_ids: list[int] = Field(default_factory=list)


class NotifyCfg(_M):
    """BF-D40: where the trader's messages go and where the owner's commands come from.
    ``app`` (default): the phone app only (inbox + Web Push, actions in the app);
    ``telegram``: Telegram only (as before); ``both``."""

    channel: Literal["app", "telegram", "both"] = "app"

    @property
    def telegram(self) -> bool:
        return self.channel in ("telegram", "both")

    @property
    def app(self) -> bool:
        return self.channel in ("app", "both")


class AppCfg(_M):
    """BF-D39: the phone app's actions. ``allowed_logins``: the Tailscale log-ins (the
    ``Tailscale-User-Login`` header) that may act (approve, pause...); empty = actions
    off, viewing still works. Set it on the server only (``bigwins`` menu), never in the
    repository. The trader serves the actions on ``control_port`` of its private network;
    the dashboard forwards ``/act/...`` there (``control_url``)."""

    allowed_logins: list[str] = Field(default_factory=list)
    control_port: int = Field(default=8081, ge=1024, le=65535)
    control_url: str = "http://trader-control:8081"
    # BF-D46: the trader listens only on this name's address (its `control` network alias),
    # never 0.0.0.0
    control_bind_host: str = "trader-control"
    # BF-D46 / L2: the app's host name (https://<this>); with it the Origin of every action
    # must be exactly this host. Written to bfast.local.yaml by `bigwins login`.
    public_host: str = ""
    push_subject: str = "mailto:bigwins-paper-trader@users.noreply.github.com"

    @field_validator("push_subject")
    @classmethod
    def _subject(cls, v: str) -> str:
        if not v.startswith(("mailto:", "https://")):
            raise ValueError("push_subject must be a mailto: or https:// URL (RFC 8292)")
        return v

    @field_validator("control_url")
    @classmethod
    def _control(cls, v: str) -> str:
        if not v.startswith("http://"):
            raise ValueError("control_url is the trader's private http address")
        return v


class StrategyCfg(_M):
    """BF-D45: how an approved strategy update takes effect. ``immediate`` (default while
    the book is paper; the owner's choice for the early stage): applied as soon as the
    ASX is closed and no order is working, then an out-of-cycle decision with the new
    rules, its batch approved by the owner like any other. ``next_decision``: from the
    next month-end decision (not in the 24 hours before one). Changing a live book to
    ``immediate`` will need an explicit, acknowledged config change (later live step);
    nothing here changes a live guard."""

    update_mode: Literal["immediate", "next_decision"] = "immediate"


class HeartbeatCfg(_M):
    """BF-D41: ping the ``healthchecks_url`` secret every ``every_seconds`` (``none``: off)."""

    every_seconds: int = Field(default=300, ge=60, le=3600)


class JournalCfg(_M):
    url_env: str


class DashboardCfg(_M):
    """BF-D37: the read-only phone dashboard (``trader-bf dashboard``). Reached only
    through Tailscale (``tailscale serve`` on the host's loopback port)."""

    # Tailscale log-ins (the ``Tailscale-User-Login`` header that ``tailscale serve``
    # adds) allowed to see the page; empty = everyone on the owner's tailnet
    allowed_logins: list[str] = Field(default_factory=list)
    index_code: str = "A200"  # the comparison line: the ASX 200 fund of the L15 switch
    # BF-D46: the Tailscale-User-Login header is believed only from these source addresses
    # (the gateway of the `dashboard` Docker network, where the host's published port
    # arrives from); a header from anywhere else is dropped. Empty = believe any (dev).
    trusted_proxies: list[str] = Field(default_factory=lambda: ["172.31.250.1"])


class BfastConfig(_M):
    version: Literal[1]
    book: str
    line: Literal["EMG2_18", "EMG2_20"]
    mode: Literal["paper"]
    broker: BrokerCfg
    execution: ExecutionCfg
    live_emg2_20: Emg2_20Cfg
    risk: RiskCfg
    data: DataCfg
    telegram: TelegramCfg = Field(default_factory=TelegramCfg)
    journal: JournalCfg
    band_trend: BandTrendCfg | None = None  # None = the switch is off (L15 not in use)
    tax: TaxCfg = Field(default_factory=TaxCfg)  # BF-D29 tax report
    # BF-D32: paper dry run with forced L15 states (None in normal running)
    paper_dry_run: PaperDryRunCfg | None = None
    dashboard: DashboardCfg = Field(default_factory=DashboardCfg)  # BF-D37
    notify: NotifyCfg = Field(default_factory=NotifyCfg)  # BF-D40
    app: AppCfg = Field(default_factory=AppCfg)  # BF-D39
    heartbeat: HeartbeatCfg = Field(default_factory=HeartbeatCfg)  # BF-D41
    strategy: StrategyCfg = Field(default_factory=StrategyCfg)  # BF-D45

    @model_validator(mode="after")
    def _limits_fit_the_book(self) -> BfastConfig:
        """Review H6: a whole book of buys (the start, a switch back from the fund) fits
        the L10 day limits: buys a day >= capital cap x (1 + price band), and the buy
        orders a day >= the slot count (sells never count against them)."""
        cap = self.live_emg2_20.capital_cap_aud * (1 + self.risk.price_band)
        for lab, v in (("start", self.risk.buys_per_day_aud.start),
                       ("normal", self.risk.buys_per_day_aud.normal)):  # fmt: skip
            if v < cap:
                raise ValueError(f"risk.buys_per_day_aud.{lab} {v} < cap x (1 + band) {cap}")
        n = self.live_emg2_20.slots
        if min(self.risk.orders_per_day.start, self.risk.orders_per_day.normal) < n:
            raise ValueError(f"risk.orders_per_day below the {n} slots (review H6)")
        return self

    @model_validator(mode="after")
    def _dry_run_paper_only(self) -> BfastConfig:
        d = self.paper_dry_run
        if d is None:
            return self
        if self.mode != "paper" or self.broker.allow_live:  # belt and braces (BW-EXE-09)
            raise ValueError("paper_dry_run is for the paper account only")
        if self.band_trend is None or not self.band_trend.enabled:
            raise ValueError("paper_dry_run forces the L15 state: band_trend must be enabled")
        return self

    def fund_codes(self) -> frozenset[str]:
        """Codes whose payments are fund (trust) distributions (BF-D29)."""
        out = {c.upper() for c in self.tax.fund_codes}
        if self.band_trend is not None:
            out.add(self.band_trend.fund)
        return frozenset(out)

    def band_trend_params(self) -> BandTrendParams:
        b = self.band_trend
        if b is None:
            return BandTrendParams(enabled=False)
        return BandTrendParams(
            enabled=b.enabled,
            fund=b.fund,
            months=b.months,
            top_up_fraction=float(b.top_up_fraction),
            fund_half_spread=float(b.fund_half_spread),
        )

    def emg2_20_params(self) -> Emg2_20Params:
        c = self.live_emg2_20
        return Emg2_20Params(
            slots=c.slots,
            slot_unit_aud=c.slot_unit_aud,
            min_parcel_aud=c.min_parcel_aud,
            cash_reserve_aud=c.cash_reserve_aud,
            capital_cap_aud=c.capital_cap_aud,
            skip_lottery=c.skip_lottery,
            sell_rule=c.sell_rule,
        )

    def commission_model(self) -> CommissionModel:
        """Review M1: the configured IBKR plan, GST included."""
        c = self.broker.commission
        if self.broker.pricing == "tiered":
            return CommissionModel(c.tiered_min_aud, c.tiered_rate, "tiered", c.fees_rate, c.gst)
        return CommissionModel(
            (c.fixed_min_aud * (1 + c.gst)).quantize(Decimal("0.01")), c.fixed_rate * (1 + c.gst)
        )

    def order_params(self) -> OrderParams:
        return OrderParams(
            order_type=self.execution.order_type,
            limit_band=self.execution.limit_band,
            min_parcel_aud=self.live_emg2_20.min_parcel_aud,
            commission=self.commission_model(),
        )

    def risk_limits(self) -> RiskLimits:
        r = self.risk
        return RiskLimits(
            order_value_max_aud=r.order_value_max_aud,
            orders_per_day_start=r.orders_per_day.start,
            orders_per_day_normal=r.orders_per_day.normal,
            orders_per_day_hard=r.orders_per_day.hard,
            buys_per_day_start_aud=r.buys_per_day_aud.start,
            buys_per_day_normal_aud=r.buys_per_day_aud.normal,
            price_band=r.price_band,
            gap_hold=r.gap_hold,
            absurd_move=r.absurd_move,
            participation_max=r.participation_max,
            quote_stale_minutes=r.quote_stale_minutes,
            min_parcel_aud=self.live_emg2_20.min_parcel_aud,
            capital_cap_aud=self.live_emg2_20.capital_cap_aud,
            value_review_aud=r.value_review_aud,
            value_halt_buys_aud=r.value_halt_buys_aud,
            value_line_halt_aud=r.value_line_halt_aud,
            drawdown_review=r.drawdown.review,
            drawdown_halt=r.drawdown.halt,
            day_move_review=r.day_move.review,
            day_move_halt=r.day_move.halt,
            real_money_floor=r.real_money_floor,
            fund_order_max_aud=(
                self.band_trend.fund_order_max_aud
                if self.band_trend is not None
                else RiskLimits().fund_order_max_aud
            ),
        )


CA_CSV_ENV = "TRADER_BF_CA_CSV"  # overrides ``data.corporate_actions_csv`` (BF-D23)
LIC_LIST_ENV = "TRADER_BF_LIC_LIST"  # overrides ``data.lic_list`` (the frozen list's path)


def read_codes(path: Path, text: str | None = None) -> frozenset[str]:
    """First column of a CSV with a header row (``code,...``); blank lines skipped.
    ``text``: the file's contents already read (so the codes are those of the bytes
    that were hashed)."""
    body = path.read_text(encoding="utf-8") if text is None else text
    codes = frozenset(r.split(",")[0].strip().upper() for r in body.splitlines()[1:] if r.strip())
    if not codes:
        raise ValueError(f"{path}: no codes (an empty list would exclude no LIC)")
    return codes


class LicListError(RuntimeError):
    """BF-D21: the frozen LIC list is missing, empty or not the registered file. No
    decision may be made and no order sent until it is restored (fail closed)."""


@dataclass(frozen=True)
class LicList:
    codes: frozenset[str]
    path: Path
    sha256: str

    def describe(self) -> str:
        return (
            f"LIC list: frozen record list {self.path} ({len(self.codes)} codes, "
            f"sha256 {self.sha256[:12]}...)"
        )


def lic_codes(cfg: BfastConfig) -> LicList:
    """BF-D6 / BF-D20 / BF-D21: the record keeper's frozen LIC list (``data.lic_list``, or
    the path in ``$TRADER_BF_LIC_LIST``), byte for byte the registered file
    (``data.lic_list_sha256``). Missing, unreadable, empty or different from the pin is a
    ``LicListError``: there is no fallback list (the 5-code candidates file would let
    the traditional LICs into the class), so callers refuse to decide or send."""
    env = os.environ.get(LIC_LIST_ENV)
    frozen = Path(env) if env else cfg.data.lic_list
    pin = cfg.data.lic_list_sha256
    try:
        raw = frozen.read_bytes()
    except OSError as e:
        raise LicListError(f"frozen LIC list {frozen} is missing or unreadable ({e})") from e
    got = hashlib.sha256(raw).hexdigest()
    if got != pin:  # the registered file, byte for byte
        raise LicListError(f"{frozen}: sha256 {got[:12]}... is not the registered {pin[:12]}...")
    try:
        codes = read_codes(frozen, raw.decode("utf-8"))
    except ValueError as e:  # UnicodeDecodeError included  # a pinned empty file is still refused
        raise LicListError(str(e)) from e
    return LicList(codes, frozen, got)


LOCAL_SUFFIX = ".local.yaml"  # BF-D39: server-only settings, never in git


def local_path(path: Path) -> Path:
    """``config/bfast.yaml`` -> ``config/bfast.local.yaml``."""
    return path.with_name(path.stem + LOCAL_SUFFIX)


def _merge(base: dict[str, object], over: dict[str, object]) -> dict[str, object]:
    out = dict(base)
    for k, v in over.items():
        b = out.get(k)
        out[k] = _merge(b, v) if isinstance(b, dict) and isinstance(v, dict) else v
    return out


def load_bfast_config(path: Path) -> BfastConfig:
    """The config file, with the server's own ``<name>.local.yaml`` next to it laid over
    it when present (BF-D39: the owner's Tailscale log-in, the tax rate, the paper
    account id... stay on the server, out of git, and never block a ``git pull``)."""
    raw = load_yaml(path.read_text(encoding="utf-8"))
    loc = local_path(path)
    if loc.is_file():
        over = load_yaml(loc.read_text(encoding="utf-8")) or {}
        if not isinstance(over, dict) or not isinstance(raw, dict):
            raise ValueError(f"{loc}: must be a mapping of config sections")
        raw = _merge(raw, over)
    return BfastConfig.model_validate(raw)


def corporate_actions_csv(cfg: BfastConfig) -> Path | None:
    """BF-D23: the record's CORPORATE_ACTIONS.csv (``$TRADER_BF_CA_CSV`` wins)."""
    env = os.environ.get(CA_CSV_ENV)
    return Path(env) if env else cfg.data.corporate_actions_csv
