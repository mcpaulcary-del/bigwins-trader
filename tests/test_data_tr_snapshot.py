"""Total-return series (DAT-11, DAT-18, DAT-22, SYS-32) and MarketSnapshot (SYS-12,
DAT-05, DAT-21, DAT-23 lookbacks from the local store). Golden file: synthetic data."""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tests.m1_support import (
    GOLDEN,
    T0,
    add_bar,
    add_validated,
    calendar,
    data_cfg,
    load_weekday_calendar,
    sched,
    setup_market,
    syd,
)
from trader.data.instruments import record_delisting, require_instrument
from trader.data.issuer import enter_distribution
from trader.data.models import QcEvent, TrSeries
from trader.data.quality import (
    SymbolContext,
    dat11_checks,
    dat11_distribution_count,
    dat11_yearly_return,
    validate_symbol_day,
)
from trader.data.snapshot import MarketSnapshot, SnapshotError, build_snapshot
from trader.data.totalreturn import Payout, build_tr_series, compute_tr
from trader.enums import DistributionStatus

ONE = Decimal(1)


def _synthetic() -> tuple[
    dict[date, Decimal], dict[date, tuple[Decimal, Decimal]], dict[date, Decimal]
]:
    start = date(2027, 1, 4)
    closes: dict[date, Decimal] = {}
    px = Decimal("100.00")
    d, i = start, 0
    while len(closes) < 40:
        if d.weekday() < 5:
            px = (px * (ONE + Decimal((i % 7) - 3) / 1000)).quantize(Decimal("0.01"))
            closes[d] = px
            i += 1
        d += timedelta(days=1)
    days = sorted(closes)
    ex = days[10]
    closes[ex] = (closes[ex] - Decimal("0.90")).quantize(Decimal("0.01"))
    split = days[25]
    for dd in days[25:]:
        closes[dd] = (closes[dd] / 2).quantize(Decimal("0.01"))
    return closes, {ex: (Decimal("0.90"), Decimal("0.30"))}, {split: Decimal(2)}


class TestTotalReturn:
    """§6 tr_net / tr_gross: TR_t = TR_{t-1} x (P_t x s_t + D_t) / P_{t-1}."""

    def test_DAT_11_formula_by_hand(self) -> None:
        closes = {date(2027, 1, 4): Decimal("100"), date(2027, 1, 5): Decimal("99.5"),
                  date(2027, 1, 6): Decimal("50")}  # fmt: skip
        pts = compute_tr(closes, {date(2027, 1, 5): (Decimal("1.0"), Decimal("0.4"))},
                         {date(2027, 1, 6): Decimal(2)}, Decimal("0.5"))  # fmt: skip
        assert [p.tr_net for p in pts] == [ONE, Decimal("1.005"), Decimal("1.010050251256")]
        assert pts[1].tr_gross == Decimal("1.007")  # + 0.4 x 0.5 franking

    def test_DAT_11_golden_synthetic_series(self) -> None:
        closes, dists, ratios = _synthetic()
        pts = compute_tr(closes, dists, ratios, Decimal("1.0"))
        got = [[p.date.isoformat(), str(p.tr_net), str(p.tr_gross)] for p in pts]
        path = GOLDEN / "tr_synthetic.json"
        if os.environ.get("UPDATE_GOLDEN") == "1":
            path.write_text(json.dumps(got, indent=1) + "\n")
        assert got == json.loads(path.read_text())

    def test_DAT_22_never_built_across_missing_amount(self) -> None:
        closes, dists, ratios = _synthetic()
        stop = sorted(closes)[10]
        pts = compute_tr(closes, {}, ratios, ONE, stop_before=stop)
        assert max(p.date for p in pts) < stop

    def test_SYS_32_wind_up_payout_is_last_return(self) -> None:
        closes = {date(2027, 1, 4): Decimal("10"), date(2027, 1, 5): Decimal("10")}
        pts = compute_tr(closes, {}, {}, ONE, final_payout=Payout(date(2027, 1, 8), Decimal("9.5")))
        assert pts[-1].date == date(2027, 1, 8) and pts[-1].tr_net == Decimal("0.95")

    def test_DAT_18_build_stamped_and_reproducible(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = require_instrument(s, "VAS").id
            for i, d in enumerate((date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4))):
                add_validated(s, vas, d, Decimal("100") + i)
            enter_distribution(s, "VAS", date(2026, 11, 4), DistributionStatus.FINAL, T0,
                               amount=Decimal("0.5"), period_end=date(2026, 9, 30))  # fmt: skip
            b1 = build_tr_series(s, "VAS", ONE, syd(date(2026, 11, 5), 8))
            b2 = build_tr_series(s, "VAS", ONE, syd(date(2026, 11, 6), 8))
            assert b1.build_id == b2.build_id and len(b1.build_id) == 32
            rows = s.execute(select(TrSeries)).scalars().all()
            assert len(rows) == 3 and {r.inputs_as_of for r in rows} == {b1.inputs_as_of}
            assert rows[-1].tr_net == Decimal("1.025")
            add_validated(s, vas, date(2026, 11, 5), "103")
            assert build_tr_series(s, "VAS", ONE, syd(date(2026, 11, 6), 9)).build_id != b1.build_id

    def test_SYS_32_delisting_keeps_instrument_and_payout(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = require_instrument(s, "VAS").id
            add_validated(s, vas, date(2026, 11, 2), "100")
            add_validated(s, vas, date(2026, 11, 3), "100")
            row = record_delisting(s, "VAS", date(2026, 11, 6), "fund terminated",
                                   Decimal("98.0"), T0)  # fmt: skip
            assert row.version == 2 and row.con_id == 900001
            assert require_instrument(s, "VAS").delist_reason == "fund terminated"
            b = build_tr_series(s, "VAS", ONE, syd(date(2026, 11, 9), 8))
            assert b.points[-1].date == date(2026, 11, 6) and b.points[-1].tr_net == Decimal("0.98")


class TestDAT11Checks:
    """DAT-11: own tr_net vs vendor adjusted close; WARN TR_CHECK, BLOCK only on a date
    with no issuer amount or a restated close."""

    def _series(self) -> tuple[dict[date, Decimal], dict[date, Decimal], dict[date, Decimal]]:
        d1, d2, d3 = date(2027, 1, 4), date(2027, 1, 5), date(2027, 1, 6)
        closes = {d1: Decimal("100"), d2: Decimal("99"), d3: Decimal("99.5")}
        # vendor back-adjusted for a 1.00 distribution ex d2
        adj = {d1: Decimal("99"), d2: Decimal("99"), d3: Decimal("99.5")}
        tr = {p.date: p.tr_net for p in compute_tr(closes, {d2: (ONE, Decimal(0))}, {}, ONE)}
        return closes, adj, tr

    def test_DAT_11_consistent_series_no_flag(self) -> None:
        closes, adj, tr = self._series()
        assert dat11_checks(closes, adj, tr, {date(2027, 1, 5): ONE}, set(), data_cfg()) == []

    def test_DAT_11_gap_and_ratio_off_ex_date(self) -> None:
        closes, adj, _ = self._series()
        tr = {p.date: p.tr_net for p in compute_tr(closes, {}, {}, ONE)}  # amount never entered
        flags = dat11_checks(closes, adj, tr, {}, set(), data_cfg())
        checks = {(f.check, f.level) for f in flags}
        assert ("ratio_change_off_ex", "WARN") in checks
        flags = dat11_checks(closes, adj, tr, {}, set(), data_cfg(),
                             missing_amount_dates={date(2027, 1, 5)})  # fmt: skip
        assert any(f.level == "BLOCK" for f in flags)

    def test_DAT_11_return_gap_thresholds(self) -> None:
        d1, d2 = date(2027, 1, 4), date(2027, 1, 5)
        closes = {d1: Decimal("100"), d2: Decimal("100")}
        tr = {d1: ONE, d2: ONE}
        adj = {d1: Decimal("100"), d2: Decimal("100.06")}  # 6 bp gap, ratio change off ex
        flags = dat11_checks(closes, adj, tr, {}, set(), data_cfg(), restated_dates={d2})
        gap = [f for f in flags if f.check == "return_gap"]
        assert gap and gap[0].level == "BLOCK"
        adj = {d1: Decimal("100"), d2: Decimal("100.04")}
        assert not [f for f in dat11_checks(closes, adj, tr, {}, set(), data_cfg())
                    if f.check == "return_gap"]  # fmt: skip

    def test_DAT_11_implied_dividend_counts_and_yearly(self) -> None:
        closes, adj, tr = self._series()
        flags = dat11_checks(
            closes, adj, tr, {date(2027, 1, 5): Decimal("0.80")}, set(), data_cfg()
        )
        assert [f.check for f in flags] == ["implied_dividend"] or "implied_dividend" in [
            f.check for f in flags
        ]
        assert dat11_distribution_count([date(2027, 1, 4)], [], 2027) is not None
        assert dat11_distribution_count([date(2027, 1, 4)], [date(2027, 1, 4)], 2027) is None
        cfg = data_cfg()
        assert (
            dat11_yearly_return(Decimal("0.10"), Decimal("0.104"), cfg, date(2027, 6, 30)) is None
        )
        assert dat11_yearly_return(Decimal("0.10"), Decimal("0.106"), cfg, date(2027, 6, 30))


class TestSnapshot:
    """SYS-12: MarketSnapshot raises on a price after D or a symbol with no D verdict."""

    def _snap(self, **kw: object) -> MarketSnapshot:
        base: dict[str, object] = dict(
            as_of=date(2027, 1, 29), verdict_at=datetime(2027, 1, 31, 21, tzinfo=UTC),
            monthly_tr={"VAS": pd.Series({date(2026, 12, 31): Decimal(1), date(2027, 1, 29): Decimal("1.01")})},
            last_close={"VAS": Decimal("101")}, verdict={"VAS": "OK"}, adv20={"VAS": None},
            blocked=frozenset(),
        )  # fmt: skip
        base.update(kw)
        return MarketSnapshot(**base)  # type: ignore[arg-type]

    def test_SYS_12_valid_snapshot(self) -> None:
        assert self._snap().verdict == {"VAS": "OK"}

    def test_SYS_12_price_after_d_raises(self) -> None:
        late = pd.Series({date(2027, 2, 1): Decimal(1)})
        with pytest.raises(SnapshotError, match="after D"):
            self._snap(monthly_tr={"VAS": late})

    def test_SYS_12_symbol_without_verdict_raises(self) -> None:
        with pytest.raises(SnapshotError, match="no validation verdict"):
            self._snap(verdict={})
        with pytest.raises(SnapshotError, match="blocked"):
            self._snap(verdict={"VAS": "BLOCK"}, last_close={})
        with pytest.raises(SnapshotError, match="validated close"):
            self._snap(verdict={"VAS": "BLOCK"}, blocked=frozenset({"VAS"}))

    def _history(self, s: Session, months: int) -> None:
        """Synthetic calendar and validated closes ending at D = 12 Nov 2026."""
        load_weekday_calendar(s, date(2025, 11, 1), date(2026, 10, 31))
        vas = require_instrument(s, "VAS").id
        cal = calendar(s)
        start = date(2026, 11, 1)
        for _ in range(months):
            start = (start - timedelta(days=1)).replace(day=1)
        for d in cal.trading_days(start, date(2026, 11, 11)):
            add_validated(s, vas, d, "100")
        add_bar(s, vas, date(2026, 11, 12), "100.00")
        add_bar(s, vas, date(2026, 11, 12), "100.00", source="flex")
        s.commit()

    def test_DAT_21_DAT_05_snapshot_waits_for_verdict_and_needs_13_closes(
        self, market_engine: Engine
    ) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            self._history(s, 12)
            d, now = date(2026, 11, 12), syd(date(2026, 11, 13), 8, 10)
            kw = dict(min_evaluation_closes=13, franking_realisable_rate=ONE)
            with pytest.raises(SnapshotError, match="DAT-21"):
                build_snapshot(s, ["VAS"], d, calendar(s), 9, now, **kw)  # type: ignore[arg-type]
            validate_symbol_day(s, "VAS", d, syd(date(2026, 11, 13), 8), calendar(s), data_cfg(),
                                sched(), SymbolContext(role="sleeve", held=True))  # fmt: skip
            # offset 9: 12 Nov 2026 is the 9th trading day; Nov 2025..Nov 2026 = 13 months
            snap = build_snapshot(s, ["VAS"], d, calendar(s), 9, now, **kw)  # type: ignore[arg-type]
            assert len(snap.monthly_tr["VAS"]) == 13, snap.monthly_tr["VAS"]
            assert snap.verdict == {"VAS": "OK"} and "VAS" not in snap.blocked
            assert max(snap.monthly_tr["VAS"].index) == d
            assert snap.last_close["VAS"] == Decimal("100.00")
            assert snap.adv20["VAS"] is None  # validated history has no volumes here
            snap = build_snapshot(s, ["VAS"], d, calendar(s), 9, now,
                                  min_evaluation_closes=14, franking_realisable_rate=ONE)  # fmt: skip
            assert "VAS" in snap.blocked
            assert (
                s.execute(select(QcEvent.level).where(QcEvent.check_id == "DAT-05")).scalar()
                == "BLOCK"
            )

    def test_DAT_23_lookbacks_read_from_local_store(self, market_engine: Engine) -> None:
        """No vendor transport exists on this path: the snapshot reads the local store only."""
        import trader.data.snapshot as snapmod

        assert "eodhd" not in snapmod.__dict__
        from pathlib import Path

        src = Path(snapmod.__file__).read_text()
        assert "EodhdClient" not in src and "transport" not in src
