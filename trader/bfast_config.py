"""B-fast config schema (``config/bfast.yaml``). Strict: unknown keys are errors.

``mode`` is ``Literal["paper"]`` and ``broker.allow_live`` is ``Literal[False]``: a
config that asks for live trading does not validate (BW-SYS-16 in spirit: live needs
the signed gate record and an owner-reviewed code change, not a config edit).
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from trader.lines.emg2 import Emg2_20Params
from trader.orders import OrderParams, OrderType
from trader.risk import RiskLimits
from trader.yamlio import load_yaml

HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BrokerCfg(_M):
    host: str
    port: int
    client_id: int
    account_id: str | None = None
    allow_live: Literal[False] = False

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
    approval_mode: Literal["per_order", "batch", "auto"]
    approval_deadline: str
    buy_funds_wait_sessions: int = Field(ge=0, le=4)

    @field_validator("submit_at", "fallback_send_at", "fallback_cancel_at", "approval_deadline")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        if not HHMM.match(v):
            raise ValueError("time must be HH:MM")
        return v


class Emg2_20Cfg(_M):  # noqa: N801
    capital_cap_aud: Decimal = Field(gt=0, le=Decimal(10000))  # D-4: never above A$10,000
    slots: int = Field(ge=1, le=20)
    min_parcel_aud: Decimal = Field(ge=Decimal(500))
    cash_reserve_aud: Decimal = Field(ge=0)
    skip_lottery: bool


class StartNormal(_M):
    start: Decimal
    normal: Decimal


class OrdersPerDay(_M):
    start: int = Field(ge=1, le=24)
    normal: int = Field(ge=1, le=16)
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


class DataCfg(_M):
    forward_store: Path
    etp_list: Path
    lic_list: Path
    history_sessions: int = Field(ge=300)


class TelegramCfg(_M):
    allowed_chat_ids: list[int]


class JournalCfg(_M):
    url_env: str


class BfastConfig(_M):
    version: Literal[1]
    book: str
    line: Literal["EMG2_20"]
    mode: Literal["paper"]
    broker: BrokerCfg
    execution: ExecutionCfg
    live_emg2_20: Emg2_20Cfg
    risk: RiskCfg
    data: DataCfg
    telegram: TelegramCfg
    journal: JournalCfg

    def emg2_20_params(self) -> Emg2_20Params:
        c = self.live_emg2_20
        return Emg2_20Params(
            slots=c.slots,
            min_parcel_aud=c.min_parcel_aud,
            cash_reserve_aud=c.cash_reserve_aud,
            capital_cap_aud=c.capital_cap_aud,
            skip_lottery=c.skip_lottery,
        )

    def order_params(self) -> OrderParams:
        return OrderParams(
            order_type=self.execution.order_type,
            limit_band=self.execution.limit_band,
            min_parcel_aud=self.live_emg2_20.min_parcel_aud,
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
        )


def load_bfast_config(path: Path) -> BfastConfig:
    return BfastConfig.model_validate(load_yaml(path.read_text(encoding="utf-8")))
