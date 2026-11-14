"""IBKR Activity Flex connector: parser, Web Service client and mark mapping
(DAT-02 second source; v2.10 + R37 corrections). Synthetic recorded fixtures."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tests.m1_support import FIXTURES, add_bar, calendar, setup_market, syd, token
from trader.data.flex import (
    FlexClient,
    FlexError,
    FlexNotReadyError,
    RateLimiter,
    ingest_marks,
    latest_mark,
    mark_for_day,
    parse_statements,
    statement_dates_to_pull,
)
from trader.data.instruments import require_instrument
from trader.data.models import RawBar
from trader.data.store import RawStore

STATEMENT = (FIXTURES / "flex/statement_20261112.xml").read_bytes()


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def clock(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.slept.append(s)
        self.t += s


class FlexTransport:
    def __init__(self, responses: list[bytes]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def __call__(self, url: str, params: Mapping[str, str], headers: Mapping[str, str]) -> bytes:
        self.calls.append((url, dict(params), dict(headers)))
        return self.responses.pop(0)


def _client(tmp_path: Path, responses: list[bytes]) -> tuple[FlexClient, FlexTransport, FakeClock]:
    t = FlexTransport(responses)
    fc = FakeClock()
    c = FlexClient(t, RawStore(tmp_path, "a"), RateLimiter(clock=fc.clock, sleep=fc.sleep),
                   token=token, query_id=token)  # fmt: skip
    return c, t, fc


class TestFlexParser:
    def test_DAT_02_parses_marks_positions_cash_and_trades(self) -> None:
        (st,) = parse_statements(STATEMENT)
        assert st.account_id == "DU1234567"
        assert (st.from_date, st.to_date) == (date(2026, 11, 12), date(2026, 11, 12))
        marks = {p.symbol: p.mark_price for p in st.positions}
        assert marks == {
            "VAS": Decimal("100.88"),
            "VGS": Decimal("150.95"),
            "CBA": Decimal("150.00"),
        }
        assert len(st.positions) == 3  # the LOT row repeats the summary and is skipped
        assert [c.transaction_id for c in st.cash_transactions] == ["5550001", "5550002"]
        assert all(isinstance(c.amount, Decimal) for c in st.cash_transactions)
        buy, sell = st.trades
        assert (buy.side, buy.quantity, buy.price) == ("BUY", Decimal(1), Decimal("100.80"))
        assert (sell.side, sell.quantity) == ("SELL", Decimal(2))

    def test_order_reference_optional_r37(self) -> None:
        """R37: orderReference is present only with Audit Trail fields, never on paper."""
        buy, sell = parse_statements(STATEMENT)[0].trades
        assert buy.order_reference is None
        assert sell.order_reference == "atr-a-20261112-VGS-S-1"

    def test_refuses_dtd_and_status_responses(self) -> None:
        with pytest.raises(FlexError, match="DTD"):
            parse_statements(b'<!DOCTYPE x [<!ENTITY a "b">]><FlexQueryResponse/>')
        with pytest.raises(FlexError, match="status response"):
            parse_statements((FIXTURES / "flex/get_in_progress.xml").read_bytes())
        with pytest.raises(FlexError, match="no FlexStatement"):
            parse_statements(b"<FlexQueryResponse><FlexStatements/></FlexQueryResponse>")


class TestFlexWebService:
    def test_date_range_user_agent_and_two_steps_r37(self, tmp_path: Path) -> None:
        c, t, _ = _client(tmp_path, [(FIXTURES / "flex/send_success.xml").read_bytes(),
                                     (FIXTURES / "flex/get_in_progress.xml").read_bytes(),
                                     STATEMENT])  # fmt: skip
        raw, statements = c.fetch(
            date(2026, 11, 12), date(2026, 11, 12), syd(date(2026, 11, 13), 16)
        )
        assert len(statements) == 1
        send = t.calls[0]
        assert send[1]["fd"] == send[1]["td"] == "20261112"
        assert "p" not in send[1]  # fd/td, never with p
        assert all(h["User-Agent"].startswith("asx-trader") for _, _, h in t.calls)
        assert t.calls[1][1]["q"] == "1234567890"
        assert raw.path.name.startswith("statement_20261112_20261112") and raw.source == "flex"

    def test_rate_limit_1_per_second_10_per_minute_r37(self) -> None:
        fc = FakeClock()
        rl = RateLimiter(clock=fc.clock, sleep=fc.sleep)
        for _ in range(11):
            rl.wait()
        assert fc.t >= 60  # the 11th request waited for the minute window
        assert all(s > 0 for s in fc.slept)
        fc2 = FakeClock()
        rl2 = RateLimiter(clock=fc2.clock, sleep=fc2.sleep)
        rl2.wait()
        rl2.wait()
        assert fc2.t >= 1

    def test_errors_fail_clearly(self, tmp_path: Path) -> None:
        c, _, _ = _client(tmp_path, [(FIXTURES / "flex/send_bad_token.xml").read_bytes()])
        with pytest.raises(FlexError, match="1012"):
            c.fetch(date(2026, 11, 12), date(2026, 11, 12), syd(date(2026, 11, 13), 16))
        c, _, _ = _client(tmp_path, [(FIXTURES / "flex/send_success.xml").read_bytes()]
                          + [(FIXTURES / "flex/get_in_progress.xml").read_bytes()] * 10)  # fmt: skip
        with pytest.raises(FlexNotReadyError):
            c.fetch(date(2026, 11, 12), date(2026, 11, 12), syd(date(2026, 11, 13), 16))

    def test_statement_dates_every_calendar_day_since_last(self) -> None:
        got = statement_dates_to_pull(date(2026, 11, 12), date(2026, 11, 16), date(2026, 1, 1))
        assert got == [date(2026, 11, 13), date(2026, 11, 14), date(2026, 11, 15)]


class TestDAT02MarkMapping:
    """DAT-02 second source: the mark for D is in the statement dated D or, if none, in
    the first later statement with no ASX session in between (§4 flex_pull row)."""

    def test_DAT_02_ingest_stores_universe_marks_only(
        self, market_engine: Engine, tmp_path: Path
    ) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            store = RawStore(tmp_path, "a")
            raw = store.put(
                "flex", "statement_20261112", STATEMENT, syd(date(2026, 11, 13), 16), ext="xml"
            )
            n = ingest_marks(s, parse_statements(STATEMENT), raw, "a", ["VAS", "VGS", "DHHF"])
            assert n == 2  # CBA is outside the universe
            rows = s.execute(select(RawBar).where(RawBar.source == "flex")).scalars().all()
            assert {r.close for r in rows} == {Decimal("100.88"), Decimal("150.95")}
            assert all(r.open is None and r.volume is None for r in rows)

    def test_DAT_02_mark_from_later_statement_without_session_between(
        self, market_engine: Engine
    ) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = require_instrument(s, "VAS").id
            cal = calendar(s)
            fri, sat, mon = date(2026, 11, 13), date(2026, 11, 14), date(2026, 11, 16)
            add_bar(s, vas, sat, "101.00", source="flex")
            assert mark_for_day(s, vas, fri, cal) == mark_for_day(s, vas, fri, cal)
            m = mark_for_day(s, vas, fri, cal)
            assert m is not None and m.statement_date == sat and m.price == Decimal("101.00")
            # A Monday statement is the Monday close, never Thursday's
            add_bar(s, vas, mon, "102.00", source="flex")
            assert mark_for_day(s, vas, date(2026, 11, 12), cal) is None

    def test_DAT_02_latest_available_mark_is_tagged_with_its_date_r37(
        self, market_engine: Engine
    ) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = require_instrument(s, "VAS").id
            add_bar(s, vas, date(2026, 11, 11), "100.70", source="flex")
            lm = latest_mark(s, vas, date(2026, 11, 12))
            assert lm is not None and lm.statement_date == date(2026, 11, 11)
