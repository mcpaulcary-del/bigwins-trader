"""DAT checks and per-symbol verdicts (DAT-01 to DAT-08, DAT-13, DAT-17, DAT-19, DAT-22)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tests.m1_support import (
    T0,
    add_bar,
    add_validated,
    calendar,
    data_cfg,
    sched,
    setup_market,
    syd,
)
from trader.data.instruments import require_instrument
from trader.data.issuer import enter_distribution
from trader.data.models import CorpAction, QcEvent, ValidatedClose
from trader.data.quality import (
    NotATradingDayError,
    OverrideError,
    SymbolContext,
    SymbolVerdict,
    dat01_missing_level,
    dat02_level,
    dat03_sanity,
    dat13_confirmed_exit,
    dat13_held,
    dat13_reference,
    dat19_trial,
    latest_verdict,
    qc_override,
    validate_symbol_day,
)
from trader.data.store import validated_closes
from trader.enums import AlertLevel, DistributionStatus, Verdict

D = date(2026, 11, 12)
NEXT = date(2026, 11, 13)
HIST = [date(2026, 11, d) for d in (2, 3, 4, 5, 6, 9, 10, 11)]
SLEEVE = SymbolContext(role="sleeve", held=True)
NOT_HELD = SymbolContext(role="sleeve", held=False)


@pytest.fixture
def s(market_engine: Engine) -> Session:
    sess = Session(market_engine)
    setup_market(sess)
    vas = require_instrument(sess, "VAS").id
    for i, d in enumerate(HIST):
        px = Decimal("100.00") + Decimal("0.05") * i
        add_bar(sess, vas, d, px)
        add_validated(sess, vas, d, px)
    sess.commit()
    return sess


def _v(
    s: Session, now_day: date = NEXT, hh: int = 8, ctx: SymbolContext = SLEEVE, sym: str = "VAS"
) -> SymbolVerdict:
    return validate_symbol_day(s, sym, D, syd(now_day, hh), calendar(s), data_cfg(), sched(), ctx)


def _vas(s: Session) -> int:
    return require_instrument(s, "VAS").id


class TestDAT01Freshness:
    """DAT-01: a bar for every trading day; WARN at 21:30, BLOCK if still missing at 08:00
    (except DAT-02 case (c)); a late bar is fetched by the range request and validated."""

    def test_DAT_01_levels_over_time(self, s: Session) -> None:
        cal = calendar(s)
        assert dat01_missing_level(syd(D, 19, 45), D, cal, sched()) == "INFO"
        assert dat01_missing_level(syd(D, 21, 30), D, cal, sched()) == "WARN"
        assert dat01_missing_level(syd(NEXT, 7, 59), D, cal, sched()) == "WARN"
        assert dat01_missing_level(syd(NEXT, 8, 0), D, cal, sched()) == "BLOCK"

    def test_DAT_01_missing_bar_block_at_0800_and_pending_before_2130(self, s: Session) -> None:
        early = _v(s, D, 20)
        assert latest_verdict(s, _vas(s), D) is None  # pending, no verdict yet
        assert early.detail["missing"] == "INFO"
        v = _v(s)
        assert v.level is Verdict.BLOCK and not (v.buy_ok or v.sell_ok or v.evaluate_ok)
        assert latest_verdict(s, _vas(s), D).level == "BLOCK"  # type: ignore[union-attr]

    def test_DAT_01_late_bar_validated_against_stored_mark(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.40", source="flex", fetch_time=syd(NEXT, 16))
        add_bar(s, _vas(s), D, "100.41", fetch_time=syd(NEXT, 19, 31))  # arrived a day late
        v = _v(s, NEXT, 20)
        assert v.level is Verdict.OK and not v.backfill

    def test_DAT_01_late_bar_without_mark_is_single_source_backfill(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.41", fetch_time=syd(NEXT, 19, 31))
        v = _v(s, NEXT, 20, NOT_HELD)
        assert v.level is Verdict.SINGLE_SOURCE and v.backfill


class TestDAT02CrossSource:
    """DAT-02: EODHD close vs Flex mark: within 0.1% or one tick OK, 0.1-0.5% WARN, above
    0.5% BLOCK; no mark SINGLE_SOURCE with cases (a), (b), (c)."""

    def test_DAT_02_thresholds(self) -> None:
        cfg = data_cfg()
        m = Decimal("100.00")
        assert dat02_level(Decimal("100.10"), m, cfg, None) is Verdict.OK
        assert dat02_level(Decimal("100.11"), m, cfg, None) is Verdict.WARN
        assert dat02_level(Decimal("100.11"), m, cfg, Decimal("0.20")) is Verdict.OK  # one tick
        assert dat02_level(Decimal("100.50"), m, cfg, None) is Verdict.WARN
        assert dat02_level(Decimal("100.51"), m, cfg, None) is Verdict.BLOCK

    def test_DAT_02_two_source_verdicts(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.40")
        add_bar(s, _vas(s), D, "101.00", source="flex")
        v = _v(s)
        assert v.level is Verdict.BLOCK and "DATA_MISMATCH" in " ".join(v.reasons)
        assert not v.sell_ok
        assert D not in validated_closes(s, _vas(s))

    def test_DAT_02_case_a_not_held_single_source_buys_and_sells(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.40")
        v = _v(s, ctx=NOT_HELD)
        assert v.level is Verdict.SINGLE_SOURCE
        assert v.buy_ok and v.sell_ok and v.evaluate_ok and v.detail["case"] == "a"

    def test_DAT_02_case_b_held_no_flex_buy_waits_sell_proceeds(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.40")
        add_bar(s, _vas(s), date(2026, 11, 11), "100.30", source="flex")
        v = _v(s)
        assert v.level is Verdict.SINGLE_SOURCE and v.detail["case"] == "b"
        assert v.sell_ok and not v.buy_ok
        # R37: a missing day-D Flex is the expected case; the latest mark is tagged
        lm = v.detail["latest_flex_mark"]
        assert lm["date"] == "2026-11-11" and Decimal(lm["price"]) == Decimal("100.30")

    def test_DAT_02_verdict_reissued_when_mark_arrives(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.40")
        assert _v(s).level is Verdict.SINGLE_SOURCE
        add_bar(s, _vas(s), D, "100.40", source="flex", fetch_time=syd(NEXT, 15))
        v = _v(s, NEXT, 16)
        assert v.level is Verdict.OK and v.buy_ok
        assert latest_verdict(s, _vas(s), D).level == "OK"  # type: ignore[union-attr]

    def test_DAT_02_case_c_bar_missing_flex_present(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.40", source="flex", fetch_time=syd(D, 23))
        v = _v(s)
        assert v.level is Verdict.SINGLE_SOURCE and v.close == Decimal("100.40")
        assert v.close_source == "flex" and v.sell_ok and not v.buy_ok and not v.evaluate_ok
        vc = validated_closes(s, _vas(s))[D]
        assert not vc.signals_ok  # evaluations wait for the bar

    def test_DAT_02_benchmark_single_source_by_design_no_warn(self, s: Session) -> None:
        dh = require_instrument(s, "DHHF").id
        add_bar(s, dh, D, "38.20")
        v = _v(s, ctx=SymbolContext(role="benchmark"), sym="DHHF")
        assert v.level is Verdict.SINGLE_SOURCE
        warns = s.execute(select(QcEvent).where(QcEvent.instrument_id == dh,
                                                QcEvent.check_id != "VERDICT")).scalars().all()  # fmt: skip
        assert warns == []

    def test_DAT_02_history_bars_backfill_on_dat03_04_10_11_alone(self, s: Session) -> None:
        old = date(2025, 11, 12)  # before the calendar table: DAT-08 does not apply
        add_bar(s, _vas(s), old, "90.00")
        v = validate_symbol_day(s, "VAS", old, syd(NEXT, 8), calendar(s), data_cfg(), sched(),
                                SymbolContext(role="sleeve", history=True))  # fmt: skip
        assert v.level is Verdict.OK and v.backfill
        assert validated_closes(s, _vas(s))[old].backfill


class TestDAT03Sanity:
    """DAT-03: prices > 0; high >= max(open, close); low <= min(open, close); volume >= 0."""

    def test_DAT_03_rules(self, s: Session) -> None:
        bar = add_bar(s, _vas(s), D, "100.40", high="100.30")
        assert "high < max(open, close)" in dat03_sanity(bar)
        v = _v(s)
        assert v.level is Verdict.BLOCK and v.quarantined
        assert D not in validated_closes(s, _vas(s))

    def test_DAT_03_negative_volume_and_price(self, s: Session) -> None:
        bar = add_bar(s, _vas(s), D, "100.40", volume=-1)
        assert dat03_sanity(bar) == ["volume < 0"]
        bar2 = add_bar(s, _vas(s), NEXT, "0", high="0.1", low="0")
        assert "price <= 0" in dat03_sanity(bar2)


class TestDAT04Spike:
    """DAT-04: return vs the last validated close above 8x the 60-day mean absolute
    change or above 15%, with no corporate action: quarantined until override, or WARN
    when the Flex mark agrees inside the OK tolerance and the return is 15% or less."""

    def test_DAT_04_spike_quarantined_until_mark(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "104.00")  # ~3.8% vs ~0.05% mean change: a spike
        v = _v(s)
        assert v.level is Verdict.BLOCK and v.quarantined and "DATA_SPIKE" in v.reasons[0]
        assert D not in validated_closes(s, _vas(s))

    def test_DAT_04_spike_confirmed_by_mark_is_warn(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "104.00")
        add_bar(s, _vas(s), D, "104.05", source="flex")
        v = _v(s)
        assert v.level is Verdict.WARN and not v.quarantined
        assert validated_closes(s, _vas(s))[D].close == Decimal("104.00")

    def test_DAT_04_above_15pct_never_validated_without_override(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "120.00")
        add_bar(s, _vas(s), D, "120.00", source="flex")
        assert _v(s).level is Verdict.BLOCK

    def test_DAT_04_corporate_action_record_exempts(self, s: Session) -> None:
        s.add(CorpAction(instrument_id=_vas(s), type="split", ex_date=D, ratio=Decimal(2),
                         source="issuer", fetch_time=T0))  # fmt: skip
        add_bar(s, _vas(s), D, "50.20")
        add_bar(s, _vas(s), D, "50.20", source="flex")
        assert _v(s).level is Verdict.OK


class TestDAT05To08:
    def test_DAT_06_stale_three_sessions(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = _vas(s)
            for d in (date(2026, 11, 10), date(2026, 11, 11), D):
                add_bar(s, vas, d, "100.00", volume=0)
            add_validated(s, vas, date(2026, 11, 11), "100.00")
            v = validate_symbol_day(s, "VAS", D, syd(NEXT, 8), calendar(s), data_cfg(), sched(),
                                    NOT_HELD)  # fmt: skip
            assert v.level is Verdict.WARN and "DAT-06 stale" in v.reasons

    def test_DAT_08_non_trading_day_is_whole_run(self, s: Session) -> None:
        with pytest.raises(NotATradingDayError, match="DAT-08"):
            validate_symbol_day(s, "VAS", date(2026, 11, 14), syd(NEXT, 8), calendar(s),
                                data_cfg(), sched(), SLEEVE)  # fmt: skip


class TestDAT13Reference:
    """DAT-13: hold an order more than 2% from the reference (last validated close minus
    distributions ex after it and on or before today); confirming snapshot for exits."""

    def test_DAT_13_reference_minus_distribution(self) -> None:
        r = dat13_reference(Decimal("100.00"), date(2026, 12, 31),
                            {date(2027, 1, 4): Decimal("0.90"), date(2026, 10, 1): Decimal("1")},
                            date(2027, 1, 4))  # fmt: skip
        assert r.price == Decimal("99.10") and r.adjusted and not r.dist_missing

    def test_DAT_13_missing_amount_leaves_reference_unadjusted(self) -> None:
        r = dat13_reference(Decimal("100.00"), date(2026, 12, 31), {date(2027, 1, 4): None},
                            date(2027, 1, 4))  # fmt: skip
        assert r.price == Decimal("100.00") and r.dist_missing  # buys held (DAT-22)

    def test_DAT_13_hold_beyond_two_percent(self) -> None:
        cfg = data_cfg()
        assert not dat13_held(Decimal("102.00"), Decimal("100"), cfg)
        assert dat13_held(Decimal("102.01"), Decimal("100"), cfg)
        assert dat13_held(Decimal("97.99"), Decimal("100"), cfg)

    def test_DAT_13_confirming_snapshot_exits_only(self) -> None:
        cfg = data_cfg()
        kw = dict(bid_1130=Decimal("95.0"), bid_1300=Decimal("95.5"), quote_1300_valid=True,
                  halted=False, limit=Decimal("95.4"), reference=Decimal("100"), cfg=cfg)  # fmt: skip
        assert dat13_confirmed_exit(side="SELL", kind="transition", **kw)  # type: ignore[arg-type]
        assert dat13_confirmed_exit(side="SELL", kind="withdrawal", **kw)  # type: ignore[arg-type]
        assert not dat13_confirmed_exit(side="BUY", kind="transition", **kw)  # type: ignore[arg-type]
        assert not dat13_confirmed_exit(side="SELL", kind="band", **kw)  # type: ignore[arg-type]
        bad = {**kw, "bid_1300": Decimal("96.5")}  # moved more than 1%
        assert not dat13_confirmed_exit(side="SELL", kind="transition", **bad)  # type: ignore[arg-type]
        far = {**kw, "limit": Decimal("89.9")}  # more than 10% below the reference
        assert not dat13_confirmed_exit(side="SELL", kind="transition", **far)  # type: ignore[arg-type]
        halted = {**kw, "halted": None}
        assert not dat13_confirmed_exit(side="SELL", kind="transition", **halted)  # type: ignore[arg-type]


class TestDAT17Override:
    """DAT-17: INFO/WARN/BLOCK levels; a BLOCK is cleared only by qc override with a typed
    reason recorded as a qc_event; the named close enters the validated set with its id."""

    def test_DAT_17_levels(self) -> None:
        assert [lv.value for lv in AlertLevel] == ["INFO", "WARN", "BLOCK"]

    def test_DAT_17_override_names_the_close(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "104.00")
        assert _v(s).level is Verdict.BLOCK
        with pytest.raises(OverrideError, match="typed reason"):
            qc_override(s, "VAS", D, syd(NEXT, 9), reason=" ", actor="a", use="eodhd")
        with pytest.raises(OverrideError, match="exactly one"):
            qc_override(s, "VAS", D, syd(NEXT, 9), reason="x", actor="a")
        row = qc_override(s, "VAS", D, syd(NEXT, 9), reason="checked issuer NAV", actor="a",
                          use="eodhd")  # fmt: skip
        ev = s.get(QcEvent, row.override_id)
        assert ev is not None and ev.check_id == "DAT-17"
        assert (ev.override_by, ev.override_reason) == ("a", "checked issuer NAV")
        assert validated_closes(s, _vas(s))[D].close == Decimal("104.00")
        assert latest_verdict(s, _vas(s), D).check_id == "DAT-17"  # type: ignore[union-attr]

    def test_DAT_17_override_with_price_or_flex(self, s: Session) -> None:
        add_bar(s, _vas(s), D, "100.30", source="flex")
        r1 = qc_override(
            s, "VAS", D, syd(NEXT, 9), reason="r", actor="a", use="flex", cal=calendar(s)
        )
        assert r1.source == "flex" and r1.close == Decimal("100.30")
        r2 = qc_override(s, "VAS", D, syd(NEXT, 10), reason="r", actor="a", price=Decimal("100.25"))
        assert r2.source == "override"
        assert validated_closes(s, _vas(s))[D].close == Decimal("100.25")


class TestDAT19Trial:
    """DAT-19: a 20-trading-day trial of Flex mark vs EODHD close sets the DAT-02 tolerances."""

    def test_DAT_19_trial_needs_20_days(self) -> None:
        days = [date(2026, 11, 2) + timedelta(days=i) for i in range(30)]
        pairs = [(d, Decimal("100.00"), Decimal("100.00") if i % 2 else Decimal("100.05"))
                 for i, d in enumerate(days[:19])]  # fmt: skip
        t = dat19_trial(pairs)
        assert not t.complete and t.days == 19
        t = dat19_trial([*pairs, (days[19], Decimal("100"), Decimal("100"))])
        assert t.complete and t.days_equal == 10
        assert t.max_abs_rel == Decimal("0.05") / Decimal("100.05")


class TestDAT22Verdict:
    """DAT-22: from an expected ex-date with no amount, every evaluation dated on or after
    it is blocked (DIST_MISSING) and buys are held; sells proceed."""

    def test_DAT_22_expected_row_blocks_evaluation_from_ex_date(self, s: Session) -> None:
        enter_distribution(s, "VAS", D, DistributionStatus.EXPECTED, T0)
        add_bar(s, _vas(s), D, "100.40")
        add_bar(s, _vas(s), D, "100.40", source="flex")
        v = _v(s)
        assert v.level is Verdict.OK and not v.evaluate_ok and not v.buy_ok and v.sell_ok
        assert "DIST_MISSING" in v.reasons
        assert not validated_closes(s, _vas(s))[D].signals_ok

    def test_DAT_22_evaluation_before_ex_date_not_blocked(self, s: Session) -> None:
        enter_distribution(s, "VAS", NEXT, DistributionStatus.EXPECTED, T0)
        add_bar(s, _vas(s), D, "100.40")
        add_bar(s, _vas(s), D, "100.40", source="flex")
        assert _v(s).evaluate_ok


def test_DAT_17_validated_rows_are_insert_only(s: Session) -> None:
    add_bar(s, _vas(s), D, "100.40")
    add_bar(s, _vas(s), D, "100.40", source="flex")
    _v(s)
    _v(s, NEXT, 9)
    rows = s.execute(select(ValidatedClose).where(ValidatedClose.trade_date == D)).scalars().all()
    assert len(rows) == 2  # each verdict issue is a new row; the latest is the record
