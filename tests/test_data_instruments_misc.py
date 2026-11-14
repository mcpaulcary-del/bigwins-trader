"""Instruments (SYS-20, SYS-29, SYS-31, SYS-32), spreads (SYS-30), dead-man check-ins
(DAT-12), sentinel unit (DAT-20), licence guard scan (DAT-15) and the M1 CLI commands."""

from __future__ import annotations

import io
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session

from tests.conftest import COMMON_PATH, FAKE_SHA, REPO, migrate, write_config_dir
from tests.m1_support import T0, FakeQualifier, add_bar, common, setup_market, syd
from trader import cli
from trader.config import ApprovalPinMismatchError, load_config, parse_common
from trader.data.commands import import_calendar, import_spreads
from trader.data.instruments import (
    InstrumentError,
    ensure_instrument,
    order_con_id,
    record_delisting,
    register_unqualified,
    require_instrument,
    tick_size,
)
from trader.data.models import CalendarDay, Distribution, Instrument, MarketAuditLog, QcEvent
from trader.data.spreads import (
    identity_change_needs_card,
    instrument_identity,
    spread_level,
    spread_verdicts,
)
from trader.monitor import DeadManMonitor
from trader.orders import sentinel_floor
from trader.secrets import SecretValue


class TestSYS20Contracts:
    """SYS-20: contracts are resolved once with qualifyContracts; the conId is stored in
    instrument and used for every order."""

    def test_SYS_20_resolved_once(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            q = setup_market(s)
            assert q.calls == ["VAS", "VGS"]
            again = ensure_instrument(s, "VAS", q, T0)
            assert q.calls == ["VAS", "VGS"]  # not re-resolved
            assert order_con_id(again) == 900001

    def test_SYS_20_unqualified_instrument_cannot_be_ordered(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            with pytest.raises(InstrumentError, match="SYS-20"):
                order_con_id(require_instrument(s, "DHHF"))
            q = FakeQualifier()
            dh = ensure_instrument(s, "DHHF", q, T0)  # qualifies a data-only row once
            assert dh.version == 2 and dh.con_id is not None and q.calls == ["DHHF"]


class TestSYS29Ticks:
    """SYS-29: tick sizes are read from IBKR contract data, never hard-coded."""

    def test_SYS_29_tick_from_stored_market_rule(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = require_instrument(s, "VAS")
            assert tick_size(vas, Decimal("1.50")) == Decimal("0.001")
            assert tick_size(vas, Decimal("3.00")) == Decimal("0.005")
            assert tick_size(vas, Decimal("100")) == Decimal("0.01")
            assert tick_size(require_instrument(s, "DHHF"), Decimal("38")) is None

    def test_SYS_29_no_hard_coded_tick_table(self) -> None:
        for p in (REPO / "trader").rglob("*.py"):
            text = p.read_text()
            assert not re.search(r"(?i)tick\w*\s*=\s*Decimal\(", text), p


class TestSYS30Spreads:
    """SYS-30: monthly reported spreads; above 0.04% WARN and review; 0.07% or wider may
    not be a live sleeve."""

    def test_SYS_30_levels_and_import(self, market_engine: Engine, tmp_path: Path) -> None:
        cfg = common().data
        assert spread_level(Decimal("0.0002"), cfg.spread_warn, cfg.spread_exclude) == "OK"
        assert spread_level(Decimal("0.0004"), cfg.spread_warn, cfg.spread_exclude) == "OK"
        assert spread_level(Decimal("0.0005"), cfg.spread_warn, cfg.spread_exclude) == "WARN"
        assert spread_level(Decimal("0.0007"), cfg.spread_warn, cfg.spread_exclude) == "EXCLUDE"
        f = tmp_path / "spreads.csv"
        f.write_text("symbol,month,spread\nVAS,2026-09,0.0002\nVGS,2026-09,0.0005\n")
        with Session(market_engine) as s:
            setup_market(s)
            assert import_spreads(s, f, "ASX Investment Products Sep 2026", T0) == 2
            got = {v.symbol: v.level for v in spread_verdicts(s, common(), "2026-09")}
            assert got == {"VAS": "OK", "VGS": "WARN"}
            assert {v.level for v in spread_verdicts(s, common(), "2026-10")} == {"WARN"}  # missing
            assert "import.spread" in s.execute(select(MarketAuditLog.action)).scalars().all()


class TestSYS31Identity:
    """SYS-31: replacing a live instrument, a base weight or a benchmark is a new card and
    goes through change control: it changes the approved common hash."""

    def test_SYS_31_identity_change_refused_until_reapproved(self, tmp_path: Path) -> None:
        old = common()
        text = COMMON_PATH.read_text()
        new_text = text.replace("VAS: {base_weight: 0.40}", "VAS: {base_weight: 0.30}").replace(
            "VGS: {base_weight: 0.60}", "VGS: {base_weight: 0.70}"
        )
        new = parse_common(new_text.encode())
        assert identity_change_needs_card(old, new)
        assert not identity_change_needs_card(old, parse_common(text.encode()))
        assert len(instrument_identity(old)) == 64
        d = write_config_dir(tmp_path, common_text=new_text)
        with pytest.raises(ApprovalPinMismatchError):
            load_config(d, "a", deployed_sha=FAKE_SHA)


class TestSYS32Delisting:
    """SYS-32: closed or delisted ETFs stay in instrument with delist date, reason and
    final payout (see also the tr test: the payout is the last return)."""

    def test_SYS_32_versions_kept(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            record_delisting(s, "VGS", date(2027, 3, 1), "merged", Decimal("151.2"), T0)
            rows = s.execute(select(Instrument).where(Instrument.symbol == "VGS")).scalars().all()
            assert [r.version for r in rows] == [1, 2]
            assert rows[1].final_payout == Decimal("151.2") and rows[0].delist_date is None
            with pytest.raises(ValueError):
                record_delisting(s, "VGS", date(2027, 3, 1), "x", Decimal("-1"), T0)


class TestDAT12DeadMan:
    """DAT-12: a silent pipeline alerts through the external monitor (MON-01)."""

    def test_DAT_12_job_checks_in_or_reports_failure(self) -> None:
        pings: list[str] = []
        m = DeadManMonitor(
            lambda: SecretValue("https://hc.example.invalid/ping/uuid"), pings.append
        )
        with m.job("fetch_vendor_data"):
            pass
        with pytest.raises(RuntimeError), m.job("flex_pull"):
            raise RuntimeError("boom")
        assert pings == [
            "https://hc.example.invalid/ping/uuid/fetch_vendor_data",
            "https://hc.example.invalid/ping/uuid/flex_pull/fail",
        ]


class TestDAT20Sentinel:
    """DAT-20 (SHOULD): one unit kept when a sleeve's target is zero (inside build_orders)."""

    def test_DAT_20_floor(self) -> None:
        assert sentinel_floor(0, sentinel_unit=True) == 1
        assert sentinel_floor(0, sentinel_unit=False) == 0
        assert sentinel_floor(17, sentinel_unit=True) == 17
        with pytest.raises(ValueError):
            sentinel_floor(-1, sentinel_unit=True)
        assert common().l1.sentinel_unit is True


class TestDAT15LicenceScan:
    """DAT-15 CI test: the code never imports yfinance or pandas_datareader nor requests
    stooq.com, finance.yahoo.com or asx.com.au."""

    def test_DAT_15_no_excluded_sources(self) -> None:
        bad = re.compile(
            r"^\s*(import|from)\s+(yfinance|pandas_datareader)\b|stooq\.com|finance\.yahoo\.com"
            r"|asx\.com\.au", re.M
        )  # fmt: skip
        hits = []
        for d in ("trader", "scripts", "migrations"):
            for p in (REPO / d).rglob("*.py"):
                if bad.search(p.read_text()):
                    hits.append(str(p))
        assert hits == []
        lock = (REPO / "uv.lock").read_text()
        assert 'name = "yfinance"' not in lock and 'name = "pandas-datareader"' not in lock


class TestCliCommands:
    """The M1 commands: import calendar|spread, distribution enter, qc override."""

    def _env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Engine]:
        url = f"sqlite:///{tmp_path / 'market_a.db'}"
        eng = create_engine(url)
        migrate(eng, "market")
        with Session(eng) as s:
            setup_market(s)
        monkeypatch.setenv("TRADER_MARKET_DATABASE_URL", url)
        monkeypatch.setattr("trader.data.commands.deployed_git_sha", lambda: FAKE_SHA)
        return write_config_dir(tmp_path), eng

    def test_OPS_05_import_calendar_insert_only_audited(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cfg, eng = self._env(tmp_path, monkeypatch)
        f = tmp_path / "cal.csv"
        f.write_text(
            "venue,date,is_trading,close_time\nXASX,2028-01-03,false,\nXASX,2028-01-04,true,16:10\n"
        )
        out = io.StringIO()
        rc = cli.main(["import", "calendar", str(f), "--source", "ASX calendar 2028",
                       "--user", "a", "--config-dir", str(cfg)], out=out, err=io.StringIO())  # fmt: skip
        assert rc == 0 and "2 calendar rows" in out.getvalue()
        with Session(eng) as s:
            rows = (
                s.execute(select(CalendarDay).where(CalendarDay.date >= date(2028, 1, 1)))
                .scalars()
                .all()
            )
            assert {r.source for r in rows} == {"ASX calendar 2028"}
            assert "import.calendar" in s.execute(select(MarketAuditLog.action)).scalars().all()
        f.write_text("venue,date,is_trading,close_time\nXASX,2028-01-05,true,\n")
        with Session(eng) as s, pytest.raises(ValueError):
            import_calendar(s, f, "x", T0)

    def test_DAT_14_cli_distribution_enter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cfg, eng = self._env(tmp_path, monkeypatch)
        base = ["distribution", "enter", "--symbol", "VAS", "--ex-date", "2027-01-04",
                "--user", "a", "--config-dir", str(cfg), "--source-note", "Vanguard notice"]  # fmt: skip
        assert cli.main([*base, "--status", "expected"], out=io.StringIO(), err=io.StringIO()) == 0
        err = io.StringIO()
        assert (
            cli.main([*base, "--status", "final", "--amount", "0.9"], out=io.StringIO(), err=err)
            == 1
        )
        assert "period_end" in err.getvalue()
        with Session(eng) as s:
            assert len(s.execute(select(Distribution)).scalars().all()) == 1

    def test_DAT_17_cli_qc_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg, eng = self._env(tmp_path, monkeypatch)
        with Session(eng) as s:
            add_bar(s, require_instrument(s, "VAS").id, date(2026, 11, 12), "100.40")
            s.commit()
        out = io.StringIO()
        rc = cli.main(["qc", "override", "--symbol", "VAS", "--date", "2026-11-12", "--use", "eodhd",
                       "--reason", "checked", "--user", "a", "--config-dir", str(cfg)],
                      out=out, err=io.StringIO())  # fmt: skip
        assert rc == 0 and "close 100.4" in out.getvalue()
        with Session(eng) as s:
            ev = s.execute(select(QcEvent).where(QcEvent.check_id == "DAT-17")).scalar_one()
            assert ev.override_reason == "checked"

    def test_DAT_23_cli_fetch_fails_closed_without_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cfg, _ = self._env(tmp_path, monkeypatch)
        monkeypatch.setenv("TRADER_DATA_DIR", str(tmp_path / "data"))

        def no_network(url: str, params: object) -> bytes:
            raise AssertionError("no network in tests")

        monkeypatch.setattr("trader.data.commands.urllib_transport", no_network)
        err = io.StringIO()
        rc = cli.main(["fetch", "--symbol", "VAS", "--from", "2026-11-02", "--to", "2026-11-03",
                       "--user", "a", "--config-dir", str(cfg)], out=io.StringIO(), err=err)  # fmt: skip
        assert rc == 1  # the secret is missing outside the container: nothing is fetched
        assert "eodhd_api_token" in err.getvalue()


def test_SYS_20_unqualified_registration_is_data_only(market_engine: Engine) -> None:
    with Session(market_engine) as s:
        inst = register_unqualified(s, "DHHF", syd(date(2026, 11, 1), 9))
        assert inst.con_id is None and inst.version == 1
