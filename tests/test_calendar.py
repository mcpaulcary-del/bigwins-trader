"""OPS-05: holidays and half-days come only from the ``calendar`` table."""

from __future__ import annotations

import ast
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from trader.calendar import AsxCalendar, CalendarEntry, CalendarGapError, EventEntry, load_events
from trader.enums import EventType
from trader.ledger import CalendarDay

CAL_SRC = Path(__file__).resolve().parent.parent / "trader" / "calendar.py"


@pytest.fixture
def cal(sqlite_engine: Engine) -> AsxCalendar:
    with Session(sqlite_engine) as s:
        return AsxCalendar.from_session(s)


class TestOPS05Calendar:
    """OPS-05: holidays and half-days come only from the calendar table."""

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
    def test_OPS_05_half_days_close_1410(self, cal: AsxCalendar, d: date) -> None:
        assert cal.is_trading_day(d)
        assert cal.close_time(d) == time(14, 10)
        assert cal.is_half_day(d)

    def test_OPS_05_anzac_substitute_is_open(self, cal: AsxCalendar) -> None:
        assert cal.is_trading_day(date(2027, 4, 26))
        assert not cal.is_half_day(date(2027, 4, 26))

    def test_OPS_05_normal_day_and_weekend(self, cal: AsxCalendar) -> None:
        assert cal.close_time(date(2026, 11, 13)) == time(16, 10)
        assert not cal.is_trading_day(date(2026, 11, 14))  # Saturday

    def test_OPS_05_seed_range_and_counts(self, sqlite_engine: Engine) -> None:
        with Session(sqlite_engine) as s:
            rows = s.execute(select(CalendarDay)).scalars().all()
        assert min(r.date for r in rows) == date(2026, 11, 1)
        assert max(r.date for r in rows) == date(2027, 12, 31)
        assert len(rows) == 426
        assert sum(r.is_trading for r in rows) == 296
        assert sum(1 for r in rows if r.close_time == time(14, 10)) == 4

    def test_OPS_05_navigation_skips_holidays(self, cal: AsxCalendar) -> None:
        assert cal.next_trading_day(date(2026, 12, 24)) == date(2026, 12, 29)
        assert cal.prev_trading_day(date(2027, 1, 4)) == date(2026, 12, 31)
        assert cal.add_trading_days(date(2027, 3, 25), 1) == date(2027, 3, 30)
        assert cal.trading_days(date(2026, 12, 24), date(2027, 1, 4)) == [
            date(2026, 12, 24), date(2026, 12, 29), date(2026, 12, 30), date(2026, 12, 31),
            date(2027, 1, 4),
        ]  # fmt: skip

    def test_OPS_05_dates_outside_table_are_errors_not_guesses(self, cal: AsxCalendar) -> None:
        with pytest.raises(CalendarGapError):
            cal.is_trading_day(date(2028, 1, 4))
        with pytest.raises(CalendarGapError):
            cal.is_trading_day(date(2026, 10, 30))
        with pytest.raises(CalendarGapError):
            cal.next_trading_day(date(2027, 12, 31))

    def test_OPS_05_calendar_follows_table_contents(self) -> None:
        # A weekday marked closed in the table is closed: no weekday rule overrides it.
        entries = [
            CalendarEntry(date(2030, 1, 7), True, time(16, 10)),
            CalendarEntry(date(2030, 1, 8), False, None),  # a Tuesday
            CalendarEntry(date(2030, 1, 9), True, time(12, 0)),
        ]
        c = AsxCalendar(entries)
        assert not c.is_trading_day(date(2030, 1, 8))
        assert c.is_half_day(date(2030, 1, 9))

    def test_OPS_05_table_gaps_rejected(self) -> None:
        with pytest.raises(CalendarGapError, match="gaps"):
            AsxCalendar(
                [
                    CalendarEntry(date(2030, 1, 7), True, time(16, 10)),
                    CalendarEntry(date(2030, 1, 9), True, time(16, 10)),
                ]
            )

    def test_OPS_05_module_has_no_hardcoded_holidays(self) -> None:
        tree = ast.parse(CAL_SRC.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "date":
                pytest.fail("calendar.py constructs a literal date")
            if isinstance(node, ast.Import | ast.ImportFrom):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any("holiday" in n for n in names)
            if isinstance(node, ast.Attribute) and node.attr in {"weekday", "isoweekday"}:
                pytest.fail("calendar.py infers trading days from weekdays")


class TestEventsAndBlackouts:
    def test_OPS_05_events_seeded(self, sqlite_engine: Engine) -> None:
        with Session(sqlite_engine) as s:
            ev = load_events(s)
        bhp = [e for e in ev if e.symbol == "BHP"]
        assert {e.type for e in bhp} == {
            EventType.QUARTERLY_REVIEW,
            EventType.RESULTS,
            EventType.EX_DIVIDEND,
        }
        assert all(e.is_estimate for e in ev)
        assert sum(1 for e in ev if e.type is EventType.RBA_DECISION and e.symbol is None) == 3

    def test_blackout_default_window_widened_for_estimate(self, cal: AsxCalendar) -> None:
        e = EventEntry("CBA", EventType.RESULTS, date(2027, 2, 10), is_estimate=False)
        assert cal.blackout_dates(e, (-1, 0), 2) == [date(2027, 2, 9), date(2027, 2, 10)]
        est = EventEntry("CBA", EventType.RESULTS, date(2027, 2, 10), is_estimate=True)
        got = cal.blackout_dates(est, (-1, 0), 2)
        assert got[0] == date(2027, 2, 5) and got[-1] == date(2027, 2, 12)
        assert len(got) == 6

    def test_blackout_csl_window(self, cal: AsxCalendar) -> None:
        e = EventEntry("CSL", EventType.RESULTS, date(2027, 2, 17), is_estimate=False)
        assert cal.blackout_dates(e, (-3, 0), 2) == [
            date(2027, 2, 12), date(2027, 2, 15), date(2027, 2, 16), date(2027, 2, 17)
        ]  # fmt: skip

    def test_no_blackout_for_ex_dividend_or_rba(self, cal: AsxCalendar) -> None:
        for t in (EventType.EX_DIVIDEND, EventType.RBA_DECISION):
            assert (
                cal.blackout_dates(EventEntry("BHP", t, date(2027, 3, 4), True), (-1, 0), 2) == []
            )

    def test_blackout_event_on_closed_day(self, cal: AsxCalendar) -> None:
        e = EventEntry("BHP", EventType.RESULTS, date(2027, 1, 26), is_estimate=False)
        assert cal.blackout_dates(e, (-1, 0), 2) == [
            date(2027, 1, 22), date(2027, 1, 25), date(2027, 1, 27)
        ]  # fmt: skip
