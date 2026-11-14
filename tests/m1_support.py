"""Shared helpers for the M1 data-pipeline tests (synthetic data only; no network)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from tests.conftest import COMMON_PATH
from trader.calendar import AsxCalendar, VenueTimes
from trader.config import CommonConfig, DataConfig, parse_common
from trader.data.instruments import QualifiedContract, ensure_instrument, register_unqualified
from trader.data.models import CalendarDay, RawBar, ValidatedClose
from trader.data.quality import Schedule
from trader.dbtypes import install_mutability_guard
from trader.secrets import SecretValue
from trader.timeutil import asx_local_to_utc

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN = Path(__file__).resolve().parent / "golden"
T0 = datetime(2026, 11, 1, tzinfo=UTC)
TOKEN = "TESTKEY0123456789abcdef"  # dummy; real keys come only from Docker secrets


def common() -> CommonConfig:
    return parse_common(COMMON_PATH.read_bytes())


def data_cfg() -> DataConfig:
    return common().data


def sched() -> Schedule:
    return Schedule.from_config(common().schedule)


def venue() -> VenueTimes:
    return VenueTimes.from_config(common().venue.XASX)


def syd(d: date, hh: int, mm: int = 0) -> datetime:
    """Australia/Sydney wall clock -> aware UTC."""
    return asx_local_to_utc(d, time(hh, mm))


class FakeQualifier:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def qualify(self, symbol: str, exchange: str, currency: str) -> QualifiedContract:
        self.calls.append(symbol)
        con = {"VAS": 900001, "VGS": 900002}.get(symbol, 900100 + len(self.calls))
        # Price bands as IBKR market rules give them (stand-in values, not ASX's schedule)
        rules = ((Decimal("0"), Decimal("0.001")), (Decimal("2"), Decimal("0.005")),
                 (Decimal("5"), Decimal("0.01")))  # fmt: skip
        return QualifiedContract(con, exchange, currency, rules)


def setup_market(s: Session) -> FakeQualifier:
    install_mutability_guard(s)
    q = FakeQualifier()
    ensure_instrument(s, "VAS", q, T0, issuer="Vanguard")
    ensure_instrument(s, "VGS", q, T0, issuer="Vanguard")
    register_unqualified(s, "DHHF", T0)
    s.commit()
    return q


def calendar(s: Session) -> AsxCalendar:
    return AsxCalendar.from_session(s, venue())


def load_weekday_calendar(s: Session, start: date, end: date) -> None:
    """Synthetic history rows (weekdays open, 16:10) for tests that need old months."""
    d = start
    while d <= end:
        s.add(
            CalendarDay(
                venue="XASX", date=d, is_trading=d.weekday() < 5,
                close_time=time(16, 10) if d.weekday() < 5 else None,
                source="synthetic test calendar", fetch_time=T0,
            )
        )  # fmt: skip
        d += timedelta(days=1)
    s.flush()


def add_bar(
    s: Session,
    inst_id: int,
    d: date,
    close: str | Decimal,
    *,
    fetch_time: datetime | None = None,
    source: str = "eodhd",
    volume: int | None = 100000,
    adj: str | Decimal | None = None,
    high: str | Decimal | None = None,
    low: str | Decimal | None = None,
) -> RawBar:
    c = Decimal(close)
    bar = RawBar(
        instrument_id=inst_id, trade_date=d, source=source,
        fetch_time=fetch_time or syd(d, 19, 31),
        open=c if source == "eodhd" else None,
        high=(Decimal(high) if high is not None else c + Decimal("0.1")) if source == "eodhd" else None,
        low=(Decimal(low) if low is not None else c - Decimal("0.1")) if source == "eodhd" else None,
        close=c, volume=volume if source == "eodhd" else None,
        vendor_adjusted_close=None if adj is None else Decimal(adj),
        file_hash="0" * 64, licensee="a",
    )  # fmt: skip
    s.add(bar)
    s.flush()
    return bar


def add_validated(
    s: Session, inst_id: int, d: date, close: str | Decimal, at: datetime | None = None
) -> ValidatedClose:
    row = ValidatedClose(
        instrument_id=inst_id, trade_date=d, validated_at=at or syd(d, 23),
        close=Decimal(close), source="eodhd", verdict="OK", backfill=False, signals_ok=True,
        override_id=None, detail={},
    )  # fmt: skip
    s.add(row)
    s.flush()
    return row


@dataclass
class RecordingTransport:
    """EODHD transport fake: serves fixture bodies by path prefix and records calls."""

    bodies: Mapping[str, bytes]
    calls: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def __call__(self, url: str, params: Mapping[str, str]) -> bytes:
        self.calls.append((url, dict(params)))
        for key, body in self.bodies.items():
            if key in url:
                return body
        return b"[]"


def eod_body(rows: list[dict[str, Any]]) -> bytes:
    return json.dumps(rows).encode()


def token() -> SecretValue:
    return SecretValue(TOKEN)
