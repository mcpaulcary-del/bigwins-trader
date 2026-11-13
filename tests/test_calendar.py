"""OPS-05: session dates come only from the market ``calendar`` table; auction and
close times only from venue config; the pinned library is a date cross-check."""

from __future__ import annotations

import ast
from datetime import UTC, date, datetime, time
from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tests.conftest import COMMON_PATH
from trader.calendar import (
    AsxCalendar,
    CalendarEntry,
    CalendarGapError,
    VenueTimes,
    coverage_warning,
    library_cross_check,
)
from trader.config import parse_common
from trader.data.models import CalendarDay

CAL_SRC = Path(__file__).resolve().parent.parent / "trader" / "calendar.py"
VENUE = VenueTimes.from_config(parse_common(COMMON_PATH.read_bytes()).venue.XASX)


@pytest.fixture
def cal(market_engine: Engine) -> AsxCalendar:
    with Session(market_engine) as s:
        return AsxCalendar.from_session(s, VENUE)


class TestOPS05Calendar:
    """OPS-05: session dates come from the calendar table, loaded by hand each year."""

    @pytest.mark.parametrize(
        "d",
        [
            date(2026, 12, 25), date(2026, 12, 28), date(2027, 1, 1), date(2027, 1, 26),
            date(2027, 3, 26), date(2027, 3, 29), date(2027, 6, 14), date(2027, 12, 27),
            date(2027, 12, 28),
        ],
    )  # fmt: skip
    def test_OPS_05_spec_closures_seeded(self, cal: AsxCalendar, d: date) -> None:
        assert not cal.is_trading_day(d)

    @pytest.mark.parametrize(
        "d", [date(2026, 12, 24), date(2026, 12, 31), date(2027, 12, 24), date(2027, 12, 31)]
    )
    def test_OPS_05_early_closes_1410_are_not_execution_dates(
        self, cal: AsxCalendar, d: date
    ) -> None:
        assert cal.is_trading_day(d)
        assert cal.close_time(d) == time(14, 10)
        assert cal.is_early_close(d)
        assert not cal.is_full_trading_day(d)

    def test_OPS_05_anzac_monday_2027_is_open(self, cal: AsxCalendar) -> None:
        # v2.10 marks it [unverified]; R37 confirmed it is an ASX trading day.
        assert cal.is_full_trading_day(date(2027, 4, 26))
        assert "R37" in cal.entry(date(2027, 4, 26)).source

    def test_OPS_05_normal_close_is_closing_auction_start(self, cal: AsxCalendar) -> None:
        assert cal.close_time(date(2026, 11, 13)) == VENUE.closing_auction[0] == time(16, 10)
        assert not cal.is_trading_day(date(2026, 11, 14))  # Saturday

    def test_OPS_05_rows_carry_venue_source_and_fetch_time(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            rows = s.execute(select(CalendarDay)).scalars().all()
        assert {r.venue for r in rows} == {"XASX"}
        assert all(r.source and r.fetch_time.tzinfo is not None for r in rows)
        assert len(rows) == 426
        assert sum(r.is_trading for r in rows) == 296

    def test_OPS_05_latest_fetch_wins(self, market_engine: Engine) -> None:
        # A correction is a new row (insert-only, bitemporal): the latest fetch is the record.
        with Session(market_engine) as s:
            s.add(
                CalendarDay(
                    venue="XASX", date=date(2027, 4, 26), is_trading=False, close_time=None,
                    source="test correction", fetch_time=datetime(2026, 12, 1, tzinfo=UTC),
                )
            )  # fmt: skip
            s.commit()
            c = AsxCalendar.from_session(s, VENUE)
        assert not c.is_trading_day(date(2027, 4, 26))

    def test_OPS_05_navigation_and_execution_date(self, cal: AsxCalendar) -> None:
        assert cal.next_trading_day(date(2026, 12, 24)) == date(2026, 12, 29)
        assert cal.prev_trading_day(date(2027, 1, 4)) == date(2026, 12, 31)
        # D = 30 Dec 2026: the next trading day (31 Dec) is an early close, so E = 4 Jan.
        assert cal.next_full_trading_day(date(2026, 12, 30)) == date(2027, 1, 4)

    def test_OPS_05_evaluation_dates(self, cal: AsxCalendar) -> None:
        assert cal.evaluation_date(2026, 12, "last") == date(2026, 12, 31)
        assert cal.evaluation_date(2027, 1, 1) == date(2027, 1, 4)
        assert cal.evaluation_date(2027, 1, 7) == date(2027, 1, 12)
        got = cal.evaluation_dates(date(2026, 11, 1), date(2027, 2, 28), "last")
        assert got == [date(2026, 11, 30), date(2026, 12, 31), date(2027, 1, 29), date(2027, 2, 26)]

    def test_OPS_05_dates_outside_table_are_errors_not_guesses(self, cal: AsxCalendar) -> None:
        with pytest.raises(CalendarGapError):
            cal.is_trading_day(date(2028, 1, 4))
        with pytest.raises(CalendarGapError):
            cal.is_trading_day(date(2026, 10, 30))
        with pytest.raises(CalendarGapError):
            cal.next_trading_day(date(2027, 12, 31))

    def test_OPS_05_calendar_follows_table_contents(self) -> None:
        entries = [
            CalendarEntry(date(2030, 1, 7), True, time(16, 10)),
            CalendarEntry(date(2030, 1, 8), False, None),  # a Tuesday
            CalendarEntry(date(2030, 1, 9), True, time(14, 10)),
        ]
        c = AsxCalendar(entries, VENUE)
        assert not c.is_trading_day(date(2030, 1, 8))
        assert c.is_early_close(date(2030, 1, 9))

    def test_OPS_05_table_gaps_rejected(self) -> None:
        with pytest.raises(CalendarGapError, match="gaps"):
            AsxCalendar(
                [
                    CalendarEntry(date(2030, 1, 7), True, time(16, 10)),
                    CalendarEntry(date(2030, 1, 9), True, time(16, 10)),
                ]
            )

    def test_OPS_05_close_readable_only_from_1625(self, cal: AsxCalendar) -> None:
        d = date(2026, 11, 13)  # AEDT = UTC+11: 16:25 Sydney = 05:25 UTC
        assert cal.close_available_utc(d) == datetime(2026, 11, 13, 5, 25, tzinfo=UTC)
        assert cal.latest_readable_close(datetime(2026, 11, 13, 5, 24, tzinfo=UTC)) == date(
            2026, 11, 12
        )
        assert cal.latest_readable_close(datetime(2026, 11, 13, 5, 25, tzinfo=UTC)) == d

    def test_OPS_05_coverage_warning_under_60_days(self, cal: AsxCalendar) -> None:
        assert coverage_warning(cal, date(2026, 11, 13), 60) is None
        w = coverage_warning(cal, date(2027, 11, 15), 60)
        assert w is not None and "OPS-05 WARN" in w

    def test_OPS_05_library_cross_check_dates_only(self, cal: AsxCalendar) -> None:
        start, end = date(2026, 11, 1), date(2027, 6, 30)
        lib = set(cal.trading_days(start, end)) - {date(2027, 4, 26)} | {date(2026, 12, 28)}
        diff = library_cross_check(cal, start, end, sessions=lib)
        assert diff.only_in_table == (date(2027, 4, 26),)
        assert diff.only_in_library == (date(2026, 12, 28),)
        assert not diff.ok

    def test_OPS_05_library_cross_check_with_pinned_exchange_calendars(
        self, cal: AsxCalendar
    ) -> None:
        diff = library_cross_check(cal, date(2026, 11, 13), date(2027, 6, 30))
        # Whatever the library says, the table stays the source; the diff is reported.
        assert isinstance(diff.only_in_table, tuple)
        assert cal.is_trading_day(date(2027, 4, 26))

    def test_OPS_05_module_has_no_hardcoded_holidays_or_times(self) -> None:
        tree = ast.parse(CAL_SRC.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) in {"date", "time"}:
                assert not all(isinstance(a, ast.Constant) for a in node.args), (
                    "calendar.py constructs a literal date or time"
                )
            if isinstance(node, ast.Import | ast.ImportFrom):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any("holiday" in n for n in names)
            if isinstance(node, ast.Attribute) and node.attr in {"weekday", "isoweekday"}:
                pytest.fail("calendar.py infers trading days from weekdays")
            if (
                isinstance(node, ast.Attribute)
                and node.attr in {"opens", "closes", "schedule"}
                and isinstance(node.value, ast.Name)
                and node.value.id == "cal"
            ):
                pytest.fail("calendar.py reads times from the library")
