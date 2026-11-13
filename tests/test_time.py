"""SYS-14: timestamps stored in UTC; dates are ASX local dates; schedules use
Australia/Sydney."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import DateTime, Engine, select, text
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from tests.conftest import COMMON_PATH
from trader.config import parse_common
from trader.constants import ASX_TZ
from trader.data.models import MarketBase
from trader.dbtypes import UTCDateTime
from trader.ledger import ConfigVersion, LedgerBase
from trader.timeutil import (
    NaiveDatetimeError,
    asx_date,
    asx_local,
    asx_local_to_utc,
    ensure_utc,
    parse_hhmm,
    utc_now,
)


def test_SYS_14_utc_now_is_aware_utc() -> None:
    now = utc_now()
    assert now.tzinfo is UTC


def test_SYS_14_naive_datetime_refused() -> None:
    with pytest.raises(NaiveDatetimeError):
        ensure_utc(datetime(2026, 11, 13, 9, 0))


def test_SYS_14_asx_date_across_utc_midnight() -> None:
    # 23:30 UTC on 12 Nov is 10:30 AEDT on 13 Nov (UTC+11 in summer).
    assert asx_date(datetime(2026, 11, 12, 23, 30, tzinfo=UTC)) == date(2026, 11, 13)
    # 12:59 UTC on 13 Nov is 23:59 AEDT on 13 Nov; 13:00 UTC is the 14th.
    assert asx_date(datetime(2026, 11, 13, 12, 59, tzinfo=UTC)) == date(2026, 11, 13)
    assert asx_date(datetime(2026, 11, 13, 13, 0, tzinfo=UTC)) == date(2026, 11, 14)


def test_SYS_14_sydney_dst_offsets() -> None:
    # 09:30 Sydney is 22:30 UTC the day before in summer (AEDT, +11) and
    # 23:30 UTC the day before in winter (AEST, +10).
    assert asx_local_to_utc(date(2027, 1, 15), time(9, 30)) == datetime(
        2027, 1, 14, 22, 30, tzinfo=UTC
    )
    assert asx_local_to_utc(date(2027, 6, 15), time(9, 30)) == datetime(
        2027, 6, 14, 23, 30, tzinfo=UTC
    )
    assert asx_local(date(2027, 6, 15), time(9, 30)).tzinfo is ASX_TZ


def test_SYS_14_schedule_times_are_sydney_wall_clock() -> None:
    c = parse_common(COMMON_PATH.read_bytes())
    assert c.schedule.submit_orders == time(11, 30)
    assert c.schedule.fetch_vendor_data == (time(19, 30), time(21, 30), time(7, 0))
    assert c.schedule.full_redownload == ("Sun", time(3, 0))
    assert c.venue.XASX.tz == "Australia/Sydney"
    # Times carry no tzinfo: the zone is always Australia/Sydney.
    assert c.schedule.decide.tzinfo is None
    assert str(ASX_TZ) == "Australia/Sydney"


def test_SYS_14_parse_hhmm() -> None:
    assert parse_hhmm("09:50:00") == time(9, 50)
    for bad in ("9:50", "0950", "09:50:0", "ab:cd"):
        with pytest.raises(ValueError, match="HH:MM"):
            parse_hhmm(bad)


def test_SYS_14_every_timestamp_column_is_utc_aware() -> None:
    n = 0
    for base in (LedgerBase, MarketBase):
        for table in base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, DateTime | UTCDateTime):
                    n += 1
                    assert isinstance(col.type, UTCDateTime), f"{table.name}.{col.name}"
                    assert col.type.impl.timezone is True
    assert n >= 30


def test_SYS_14_db_stores_utc_and_refuses_naive(sqlite_engine: Engine) -> None:
    sydney_ts = datetime(2026, 11, 13, 19, 15, tzinfo=ASX_TZ)
    with Session(sqlite_engine) as s:
        s.add(ConfigVersion(hash="h1", content="x", approved_by="a", approved_at=sydney_ts))
        s.commit()
        raw = s.execute(text("SELECT approved_at FROM config_versions")).scalar_one()
        assert str(raw).startswith("2026-11-13 08:15:00")  # stored as UTC
        got = s.execute(select(ConfigVersion.approved_at)).scalar_one()
        assert got.tzinfo is not None
        assert got.utcoffset() == timedelta(0)
        assert got == sydney_ts
        s.add(
            ConfigVersion(
                hash="h2", content="x", approved_by="a", approved_at=datetime(2026, 11, 13, 9, 0)
            )
        )
        with pytest.raises(StatementError, match="naive"):
            s.flush()


def test_SYS_14_non_utc_aware_input_converted() -> None:
    ts = datetime(2026, 11, 13, 9, 0, tzinfo=timezone(timedelta(hours=11)))
    assert ensure_utc(ts) == datetime(2026, 11, 12, 22, 0, tzinfo=UTC)
