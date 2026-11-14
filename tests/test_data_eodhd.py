"""EODHD connector (DAT-23 call budget, DAT-15 licence guard, DAT-01 range request,
DAT-10 Sunday re-download). Synthetic recorded fixtures; no network."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from tests.m1_support import (
    FIXTURES,
    TOKEN,
    RecordingTransport,
    add_bar,
    calendar,
    common,
    setup_market,
    syd,
    token,
)
from trader.config import EodhdPlan
from trader.data.eodhd import (
    BudgetExceededError,
    CallBudget,
    EodhdClient,
    EodhdError,
    HistoryDepthError,
    LicenceError,
    Restatement,
    fetch_by_hand,
    fetch_vendor_data,
    full_redownload,
    parse_eod,
    pending_redownloads,
    restatement_level,
)
from trader.data.instruments import require_instrument
from trader.data.models import QcEvent, RawBar, VendorCallLog, VendorDividend
from trader.data.store import RawStore, latest_bars
from trader.enums import ReasonCode

D = date(2026, 11, 12)  # Thursday, a trading day


def _bodies() -> dict[str, bytes]:
    return {
        "eod/VAS.AU": (FIXTURES / "eodhd/eod_VAS_20261102_20261112.json").read_bytes(),
        "eod/VGS.AU": (FIXTURES / "eodhd/eod_VGS_20261102_20261112.json").read_bytes(),
        "eod/DHHF.AU": (FIXTURES / "eodhd/eod_DHHF_20261102_20261112.json").read_bytes(),
        "div/VAS.AU": (FIXTURES / "eodhd/div_VAS.json").read_bytes(),
    }


def _client(
    engine: Engine, tmp_path: Path, transport: RecordingTransport, plan: EodhdPlan | None = None
) -> EodhdClient:
    budget = CallBudget(engine, plan or common().data.eodhd)
    return EodhdClient(transport, budget, RawStore(tmp_path, "a"), "a", "a", token=token)


@pytest.fixture
def s(market_engine: Engine) -> Session:
    sess = Session(market_engine)
    setup_market(sess)
    return sess


def _seed_until(s: Session, last: date) -> None:
    for sym in ("VAS", "VGS", "DHHF"):
        add_bar(s, require_instrument(s, sym).id, last, "100.00")
    s.commit()


class TestDAT23Budget:
    """DAT-23: every EODHD request is counted against the daily budget (20 calls, from
    midnight GMT) in vendor_call_log; a job that would exceed it fails closed."""

    def test_DAT_23_each_request_is_counted_and_survives_restart(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        _seed_until(s, date(2026, 11, 1))
        t = RecordingTransport(_bodies())
        out = fetch_vendor_data(s, _client(market_engine, tmp_path, t), calendar(s),
                                ["VAS", "VGS", "DHHF"], syd(D, 19, 30))  # fmt: skip
        s.commit()
        assert [o.warnings for o in out] == [[], [], []]
        assert len(t.calls) == 6  # one eod range request + one dividend request each
        fresh = CallBudget(market_engine, common().data.eodhd)  # a restarted process
        assert fresh.used(date(2026, 11, 12)) == 6
        assert fresh.remaining(syd(D, 21, 30)) == 14

    def test_DAT_23_budget_fails_closed_without_calling(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        _seed_until(s, date(2026, 11, 1))
        budget = CallBudget(market_engine, common().data.eodhd)
        base = datetime(2026, 11, 12, 0, 0, tzinfo=UTC)
        for i in range(20):
            budget.reserve(f"x:{i}", base.replace(minute=i * 2))
        t = RecordingTransport(_bodies())
        out = fetch_vendor_data(s, _client(market_engine, tmp_path, t), calendar(s), ["VAS"],
                                syd(D, 19, 30))  # fmt: skip
        assert t.calls == []  # the API was not called
        assert out[0].budget_blocked
        assert "DATA_BUDGET" in out[0].warnings[0]
        assert BudgetExceededError.reason is ReasonCode.DATA_BUDGET
        assert budget.used(date(2026, 11, 12)) == 20  # refused calls are not counted

    def test_DAT_23_budget_resets_at_midnight_gmt(self, market_engine: Engine, s: Session) -> None:
        budget = CallBudget(market_engine, common().data.eodhd)
        late = datetime(2026, 11, 12, 23, 30, tzinfo=UTC)
        for i in range(20):
            budget.reserve(f"x:{i}", late.replace(minute=i))
        with pytest.raises(BudgetExceededError):
            budget.reserve("x", late.replace(minute=59))
        budget.reserve("x", datetime(2026, 11, 13, 0, 1, tzinfo=UTC))  # new GMT day
        assert budget.used(date(2026, 11, 13)) == 1

    def test_DAT_23_per_minute_limit(self, market_engine: Engine, s: Session) -> None:
        plan = common().data.eodhd.model_copy(update={"calls_per_minute": 2})
        budget = CallBudget(market_engine, plan)
        t0 = datetime(2026, 11, 12, 1, 0, tzinfo=UTC)
        budget.reserve("a", t0)
        budget.reserve("b", t0)
        with pytest.raises(BudgetExceededError, match="per-minute"):
            budget.reserve("c", t0)
        budget.reserve("c", t0.replace(minute=2))

    def test_DAT_23_history_older_than_plan_is_refused_without_a_call(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        t = RecordingTransport(_bodies())
        c = _client(market_engine, tmp_path, t)
        with pytest.raises(HistoryDepthError, match="1-year history"):
            c.eod("VAS", date(2025, 11, 1), date(2025, 12, 1), syd(D, 19, 30))
        assert t.calls == []
        assert c.budget.used(date(2026, 11, 12)) == 0

    def test_DAT_23_one_range_request_from_day_after_last_stored_bar(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        _seed_until(s, date(2026, 11, 5))  # 6 Nov onward is missing
        t = RecordingTransport(_bodies())
        out = fetch_vendor_data(s, _client(market_engine, tmp_path, t), calendar(s), ["VAS"],
                                syd(D, 19, 30), include_dividends=False)  # fmt: skip
        assert len(t.calls) == 1
        url, params = t.calls[0]
        assert url.endswith("/eod/VAS.AU")
        assert (params["from"], params["to"]) == ("2026-11-06", "2026-11-12")
        assert out[0].requested == (date(2026, 11, 6), D)
        assert out[0].bars_stored == 5  # 6, 9, 10, 11 and 12 Nov
        vas = require_instrument(s, "VAS").id
        assert set(latest_bars(s, vas, "eodhd")) >= {date(2026, 11, 6), D}

    def test_DAT_23_close_not_requested_before_1625(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        _seed_until(s, date(2026, 11, 11))
        t = RecordingTransport(_bodies())
        fetch_vendor_data(s, _client(market_engine, tmp_path, t), calendar(s), ["VAS"],
                          syd(D, 16, 20), include_dividends=False)  # fmt: skip
        assert t.calls == []  # 12 Nov close may only be read from 16:25 (OPS-08, §4)

    def test_DAT_23_retries_fetch_bars_only(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        _seed_until(s, date(2026, 11, 11))
        t = RecordingTransport({"eod/VAS.AU": b"[]"})
        c = _client(market_engine, tmp_path, t)
        fetch_vendor_data(s, c, calendar(s), ["VAS"], syd(D, 19, 30))  # bar not there yet
        fetch_vendor_data(s, c, calendar(s), ["VAS"], syd(D, 21, 30), include_dividends=False)
        assert [u.rsplit("/", 1)[0].rsplit("/", 1)[1] for u, _ in t.calls] == ["eod", "div", "eod"]

    def test_DAT_23_manual_fetch_inside_the_same_budget(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        t = RecordingTransport(_bodies())
        c = _client(market_engine, tmp_path, t)
        res = fetch_by_hand(s, c, "VAS", date(2026, 11, 2), date(2026, 11, 3), syd(D, 19, 30))
        assert res.bars_stored == 2
        assert c.budget.used(date(2026, 11, 12)) == 1
        ep = s.execute(select(VendorCallLog.endpoint)).scalars().all()
        assert ep == ["eod_manual:VAS"]

    def test_DAT_23_dividends_stored_as_vendor_cross_check(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        _seed_until(s, D)
        t = RecordingTransport(_bodies())
        fetch_vendor_data(s, _client(market_engine, tmp_path, t), calendar(s), ["VAS"],
                          syd(D, 19, 30))  # fmt: skip
        n = s.execute(select(func.count()).select_from(VendorDividend)).scalar_one()
        assert n == 4

    def test_DAT_23_key_never_in_errors_or_files(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        def boom(url: str, params: object) -> bytes:
            raise OSError(f"connection reset for {url}?api_token={TOKEN}")

        c = EodhdClient(boom, CallBudget(market_engine, common().data.eodhd),
                        RawStore(tmp_path, "a"), "a", "a", token=token)  # fmt: skip
        with pytest.raises(EodhdError) as ei:
            c.eod("VAS", date(2026, 11, 2), date(2026, 11, 3), syd(D, 19, 30))
        assert TOKEN not in str(ei.value) and ei.value.__cause__ is None
        t = RecordingTransport(_bodies())
        _client(market_engine, tmp_path, t).eod("VAS", date(2026, 11, 2), D, syd(D, 19, 30))
        assert t.calls[0][1]["api_token"] == TOKEN  # sent only to the vendor
        for p in tmp_path.rglob("*"):
            if p.is_file():
                assert TOKEN.encode() not in p.read_bytes()

    def test_DAT_23_bad_response_is_an_error(self) -> None:
        with pytest.raises(EodhdError, match="not JSON"):
            parse_eod((FIXTURES / "eodhd/error_not_json.txt").read_bytes())
        with pytest.raises(EodhdError, match="shape"):
            parse_eod(b'{"error": "x"}')


class TestDAT15Licence:
    """DAT-15: vendor data is fetched only with the licensee's key; rows carry the licensee."""

    def test_DAT_15_other_licensee_refused(self, market_engine: Engine, tmp_path: Path) -> None:
        budget = CallBudget(market_engine, common().data.eodhd)
        with pytest.raises(LicenceError, match="LICENCE"):
            EodhdClient(RecordingTransport({}), budget, RawStore(tmp_path, "a"), "a", "b",
                        token=token)  # fmt: skip
        with pytest.raises(LicenceError):
            EodhdClient(RecordingTransport({}), budget, RawStore(tmp_path, "b"), "a", "a",
                        token=token)  # fmt: skip

    def test_DAT_15_rows_carry_licensee(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        fetch_by_hand(s, _client(market_engine, tmp_path, RecordingTransport(_bodies())), "VAS",
                      date(2026, 11, 2), D, syd(D, 19, 30))  # fmt: skip
        assert set(s.execute(select(RawBar.licensee)).scalars()) == {"a"}


class TestDAT10Redownload:
    """DAT-10: any change to a stored raw close found by the Sunday re-download is WARN;
    more than five rows or more than 0.5% is BLOCK."""

    def _stored(self, s: Session) -> int:
        vas = require_instrument(s, "VAS").id
        rows = parse_eod((FIXTURES / "eodhd/eod_VAS_20261102_20261112.json").read_bytes())
        for b in rows:
            add_bar(s, vas, b.trade_date, b.close, fetch_time=syd(b.trade_date, 19, 31))
        s.commit()
        return vas

    def _run(self, market_engine: Engine, s: Session, tmp_path: Path, body: bytes) -> list:  # type: ignore[type-arg]
        t = RecordingTransport({"eod/VAS.AU": body})
        cfg = common().data.restatement
        sunday = syd(date(2026, 11, 15), 3)
        return full_redownload(s, _client(market_engine, tmp_path, t), calendar(s), ["VAS"],
                               sunday, block_rows=cfg.block_rows, block_pct=cfg.block_pct)  # fmt: skip

    def _body(self, changes: dict[str, str]) -> bytes:
        import json

        rows = json.loads((FIXTURES / "eodhd/eod_VAS_20261102_20261112.json").read_text())
        for r in rows:
            if r["date"] in changes:
                r["close"] = float(changes[r["date"]])
        return json.dumps(rows).encode()

    def test_DAT_10_no_change_is_ok(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        self._stored(s)
        res = self._run(market_engine, s, tmp_path, self._body({}))
        assert res[0].level == "OK" and res[0].compared == 9

    def test_DAT_10_small_change_is_warn_and_appended(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        vas = self._stored(s)
        res = self._run(market_engine, s, tmp_path, self._body({"2026-11-03": "100.12"}))
        assert res[0].level == "WARN"
        assert [r.trade_date for r in res[0].restated] == [date(2026, 11, 3)]
        rows = s.execute(select(RawBar).where(RawBar.trade_date == date(2026, 11, 3),
                                              RawBar.instrument_id == vas)).scalars().all()  # fmt: skip
        assert sorted(r.close for r in rows) == [
            Decimal("100.11"),
            Decimal("100.12"),
        ]  # nothing updated
        ev = s.execute(select(QcEvent).where(QcEvent.check_id == "DAT-10")).scalar_one()
        assert ev.level == "WARN" and ev.detail["reason"] == "DATA_RESTATED"

    def test_DAT_10_more_than_five_rows_is_block(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        self._stored(s)
        changes = {f"2026-11-{d:02d}": f"{100 + 0.11 * i + 0.01:.2f}"
                   for i, d in enumerate((2, 3, 4, 5, 6, 9))}  # fmt: skip
        res = self._run(market_engine, s, tmp_path, self._body(changes))
        assert len(res[0].restated) == 6 and res[0].level == "BLOCK"

    def test_DAT_10_one_close_moved_more_than_half_percent_is_block(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        self._stored(s)
        res = self._run(market_engine, s, tmp_path, self._body({"2026-11-03": "101.00"}))
        assert res[0].level == "BLOCK"

    def test_DAT_10_level_rule(self) -> None:
        r = Restatement(date(2026, 1, 1), Decimal("100"), Decimal("100.1"))
        assert restatement_level([], 250, 5, Decimal("0.005")) == "OK"
        assert restatement_level([r], 250, 5, Decimal("0.005")) == "WARN"
        assert restatement_level([r] * 6, 250, 5, Decimal("0.005")) == "BLOCK"
        big = Restatement(date(2026, 1, 1), Decimal("100"), Decimal("100.6"))
        assert restatement_level([big], 250, 5, Decimal("0.005")) == "BLOCK"

    def test_DAT_10_DAT_23_redownload_spread_over_later_days(
        self, market_engine: Engine, s: Session, tmp_path: Path
    ) -> None:
        self._stored(s)
        c = _client(market_engine, tmp_path, RecordingTransport({"eod/": self._body({})}))
        sunday = syd(date(2026, 11, 15), 3)
        for i in range(19):
            c.budget.reserve(f"x:{i}", sunday.replace(minute=i * 2))
        cfg = common().data.restatement
        res = full_redownload(s, c, calendar(s), ["VAS", "VGS"], sunday,
                              block_rows=cfg.block_rows, block_pct=cfg.block_pct)  # fmt: skip
        assert [r.deferred for r in res] == [False, True]
        monday = syd(date(2026, 11, 16), 20)
        assert pending_redownloads(c.budget, ["VAS", "VGS"], monday) == ["VGS"]
