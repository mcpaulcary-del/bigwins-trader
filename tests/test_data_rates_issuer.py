"""RBA series and CPI (DAT-07; TAX-04 loader stub, R37), issuer distributions (DAT-14,
DAT-22)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from tests.m1_support import FIXTURES, T0, add_bar, setup_market, syd
from trader.data.instruments import require_instrument
from trader.data.issuer import (
    DistributionError,
    benchmark_dividend_warnings,
    effective_distributions,
    enter_distribution,
    first_missing_amount,
    load_vendor_backfill,
    missing_distributions,
    no_future_expected_warning,
    vendor_amount_mismatch,
)
from trader.data.models import CashRate, Fx, MarketAuditLog, QcEvent, VendorDividend
from trader.data.rates import (
    AUDUSD,
    CASH_RATE_TARGET,
    F1_URL,
    F11_URL,
    RbaError,
    fetch_rba,
    indexation_factor,
    load_cpi,
    parse_rba_csv,
    value_on,
)
from trader.data.store import RawStore
from trader.enums import DistributionSource, DistributionStatus

D = date(2026, 11, 12)


def _rba(url: str) -> bytes:
    name = "f11.1-data.csv" if url == F11_URL else "f1.1-data.csv"
    assert url in (F11_URL, F1_URL)
    return (FIXTURES / "rba" / name).read_bytes()


class TestDAT07Rba:
    """DAT-07: an RBA rate move above 3% in a day is a WARN; the last rate carries forward
    over days the RBA does not publish."""

    def test_DAT_07_fetch_parse_store_and_warn(self, market_engine: Engine, tmp_path: Path) -> None:
        with Session(market_engine) as s:
            moves = fetch_rba(s, _rba, RawStore(tmp_path, "a"), syd(D, 19, 30),
                              fx_move_warn=Decimal("0.03"))  # fmt: skip
            assert [(m.prev_day, m.day) for m in moves] == [(date(2026, 11, 4), date(2026, 11, 6))]
            ev = s.execute(select(QcEvent).where(QcEvent.check_id == "DAT-07")).scalar_one()
            assert ev.level == "WARN" and ev.instrument_id is None
            # 5 Nov not published: the 4 Nov rate is carried forward (§5)
            assert value_on(s, Fx, AUDUSD, date(2026, 11, 5)) == (
                date(2026, 11, 4),
                Decimal("0.6490"),
            )
            assert value_on(s, CashRate, CASH_RATE_TARGET, D) == (
                date(2026, 11, 4),
                Decimal("3.85"),
            )
            # a re-fetch of unchanged values appends nothing and raises no new WARN
            again = fetch_rba(s, _rba, RawStore(tmp_path, "a"), syd(D, 21, 30),
                              fx_move_warn=Decimal("0.03"))  # fmt: skip
            assert again == []
            assert len(s.execute(select(Fx)).scalars().all()) == 8

    def test_DAT_07_parser_errors(self) -> None:
        with pytest.raises(RbaError, match="Series ID"):
            parse_rba_csv(b"a,b\n1,2\n", AUDUSD)
        with pytest.raises(RbaError, match="not found"):
            parse_rba_csv((FIXTURES / "rba/f11.1-data.csv").read_bytes(), "NOPE")


class TestCpiR37:
    def test_indexation_factor_three_decimals_half_up_none_if_not_above_one(self) -> None:
        assert indexation_factor(Decimal("140.25"), Decimal("140.00")) == Decimal("1.002")
        assert indexation_factor(Decimal("140.07"), Decimal("140.00")) == Decimal(
            "1.001"
        )  # 1.0005 up
        assert indexation_factor(Decimal("140.06"), Decimal("140.00")) is None  # rounds to 1.000
        assert indexation_factor(Decimal("139"), Decimal("140")) is None

    def test_load_cpi_insert_only_audited(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            assert load_cpi(s, [("2027Q3", Decimal("141.2"))], "ABS 6401.0 first release", T0) == 1
            assert s.execute(select(MarketAuditLog.action)).scalar_one() == "import.cpi"
            with pytest.raises(ValueError, match="quarter"):
                load_cpi(s, [("2027-09", Decimal(1))], "x", T0)


@pytest.fixture
def s(market_engine: Engine) -> Session:
    sess = Session(market_engine)
    setup_market(sess)
    return sess


class TestDAT14Distributions:
    """DAT-14: issuer amounts with status expected / estimated / final; vendor figures are
    a cross-check; pre-init vendor_backfill rows; DHHF vendor dividends without a row WARN."""

    def test_DAT_14_entry_rules(self, s: Session) -> None:
        with pytest.raises(DistributionError, match="no amount"):
            enter_distribution(s, "VAS", D, DistributionStatus.EXPECTED, T0, amount=Decimal(1))
        with pytest.raises(DistributionError, match="period_end"):
            enter_distribution(s, "VAS", D, DistributionStatus.ESTIMATED, T0, amount=Decimal(1))
        with pytest.raises(DistributionError, match="record date"):
            enter_distribution(s, "VAS", D, DistributionStatus.FINAL, T0, amount=Decimal(1),
                               period_end=D, record_date=date(2026, 11, 1))  # fmt: skip

    def test_DAT_14_final_supersedes_estimate(self, s: Session) -> None:
        ex = date(2027, 7, 1)  # Vanguard ex-dates: first trading day of Jan/Apr/Jul/Oct (R37)
        enter_distribution(s, "VAS", ex, DistributionStatus.EXPECTED, T0)
        enter_distribution(s, "VAS", ex, DistributionStatus.ESTIMATED, syd(D, 9),
                           amount=Decimal("1.200000"), period_end=date(2027, 6, 30))  # fmt: skip
        enter_distribution(s, "VAS", ex, DistributionStatus.FINAL, syd(D, 10),
                           amount=Decimal("1.234567"), franking=Decimal("0.123456"),
                           period_end=date(2027, 6, 30))  # fmt: skip
        row = effective_distributions(s, require_instrument(s, "VAS").id)[ex]
        assert row.status == DistributionStatus.FINAL and row.cash_amount == Decimal("1.234567")
        actions = s.execute(select(MarketAuditLog.action)).scalars().all()
        assert actions.count("distribution.enter") == 3

    def test_DAT_14_vendor_backfill_before_init_only(self, s: Session) -> None:
        vas = require_instrument(s, "VAS").id
        for ex, v in ((date(2026, 7, 1), "1.2035"), (date(2026, 10, 1), "0.9123")):
            s.add(VendorDividend(instrument_id=vas, ex_date=ex, fetch_time=T0, value=Decimal(v),
                                 unadjusted_value=Decimal(v), currency="AUD", file_hash="0" * 64,
                                 licensee="a"))  # fmt: skip
        rows = load_vendor_backfill(s, "VAS", date(2026, 9, 1), T0)
        assert [(r.ex_date, r.source, r.status) for r in rows] == [
            (date(2026, 7, 1), DistributionSource.VENDOR_BACKFILL, DistributionStatus.FINAL)
        ]

    def test_DAT_14_dhhf_vendor_dividend_without_row_warns(self, s: Session) -> None:
        dh = require_instrument(s, "DHHF").id
        s.add(VendorDividend(instrument_id=dh, ex_date=date(2026, 10, 1), fetch_time=T0,
                             value=Decimal("0.21"), unadjusted_value=None, currency="AUD",
                             file_hash="0" * 64, licensee="a"))  # fmt: skip
        assert benchmark_dividend_warnings(s, "DHHF") == [date(2026, 10, 1)]

    def test_DAT_14_vendor_cross_check(self, s: Session) -> None:
        vas = require_instrument(s, "VAS").id
        ex = date(2026, 10, 1)
        enter_distribution(s, "VAS", ex, DistributionStatus.FINAL, T0, amount=Decimal("0.9123"),
                           period_end=date(2026, 9, 30))  # fmt: skip
        s.add(VendorDividend(instrument_id=vas, ex_date=ex, fetch_time=T0, value=Decimal("0.95"),
                             unadjusted_value=Decimal("0.95"), currency="AUD", file_hash="0" * 64,
                             licensee="a"))  # fmt: skip
        assert vendor_amount_mismatch(s, vas, Decimal("0.01")) == [
            (ex, Decimal("0.9123"), Decimal("0.95"))
        ]


class TestDAT22Missing:
    """DAT-22: a vendor dividend or adjusted/raw ratio change with no distribution row
    blocks evaluation (DIST_MISSING); an expected row without amount blocks evaluations
    dated on or after its ex-date; WARN when no future expected row exists."""

    def test_DAT_22_expected_row(self, s: Session) -> None:
        vas = require_instrument(s, "VAS").id
        enter_distribution(s, "VAS", date(2027, 1, 4), DistributionStatus.EXPECTED, T0)
        assert missing_distributions(s, vas, date(2026, 12, 31)) == []
        (b,) = missing_distributions(s, vas, date(2027, 1, 4))
        assert (b.ex_date, b.cause, b.reason.value) == (date(2027, 1, 4), "expected_no_amount",
                                                        "DIST_MISSING")  # fmt: skip
        assert first_missing_amount(s, vas) == date(2027, 1, 4)

    def test_DAT_22_vendor_dividend_or_ratio_change_without_row(self, s: Session) -> None:
        vas = require_instrument(s, "VAS").id
        s.add(VendorDividend(instrument_id=vas, ex_date=date(2026, 10, 1), fetch_time=T0,
                             value=Decimal("0.91"), unadjusted_value=None, currency="AUD",
                             file_hash="0" * 64, licensee="a"))  # fmt: skip
        add_bar(s, vas, date(2026, 11, 2), "100", adj="99")
        add_bar(s, vas, date(2026, 11, 3), "100", adj="100")  # ratio changed: no row
        causes = {(b.ex_date, b.cause) for b in missing_distributions(s, vas, D)}
        assert causes == {(date(2026, 10, 1), "vendor_dividend"),
                          (date(2026, 11, 3), "ratio_change")}  # fmt: skip
        assert missing_distributions(s, vas, D, split_dates={date(2026, 11, 3)})[0].cause == (
            "vendor_dividend"
        )

    def test_DAT_22_warn_without_future_expected_row(self, s: Session) -> None:
        w = no_future_expected_warning(s, "VAS", D)
        assert w is not None and "no future expected ex-date" in w
        enter_distribution(s, "VAS", date(2027, 1, 4), DistributionStatus.EXPECTED, T0)
        assert no_future_expected_warning(s, "VAS", D) is None
