"""BF4: reconciliation, L13 side-by-side check, daily report."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from trader.approval import FakeTransport
from trader.broker.paper_sim import SimBroker
from trader.journal import FillRecord, Journal
from trader.orders import Side
from trader.reconcile import compare_books, reconcile
from trader.report import INDEX_BANNER, L14_BANNER, PAPER_BANNER, DailyInputs, daily_report
from trader.risk import SafetyLevel
from trader.runner import reconcile_and_page

NOW = datetime(2026, 12, 1, 5, 30, tzinfo=UTC)


def test_BW_SYS_03_reconcile_units_and_cents() -> None:
    assert reconcile({"A": 10}, Decimal("100.004"), {"A": 10}, Decimal("100.00")).ok
    r = reconcile({"A": 10}, Decimal(100), {"A": 9, "B": 1}, Decimal("100.02"))
    assert r.level is SafetyLevel.HALTED_INTEGRITY and len(r.breaks) == 3


def test_BW_RSK_27_planted_mismatch_halts_and_pages_at_once() -> None:
    j, sim = Journal.sqlite(), SimBroker(cash=Decimal(1000))
    j.add_cash("BK", "DEPOSIT", Decimal(1000), "paper")
    sim.holdings["XYZ"] = 5  # planted: a position the ledger never booked
    tr = FakeTransport()
    r = reconcile_and_page(j, sim, "BK", tr, [42], NOW)
    assert not r.ok and j.safety_level() is SafetyLevel.HALTED_INTEGRITY
    assert tr.outbox and tr.outbox[0][0] == 42 and "XYZ" in tr.outbox[0][1]
    # a clean book stays NORMAL and sends nothing
    j2, sim2, tr2 = Journal.sqlite(), SimBroker(cash=Decimal(1000)), FakeTransport()
    j2.add_cash("BK", "DEPOSIT", Decimal(1000), "paper")
    assert reconcile_and_page(j2, sim2, "BK", tr2, [42], NOW).ok and not tr2.outbox


def test_L13_sim_vs_broker_holdings() -> None:
    assert compare_books({"A": 1, "B": 2}, {"A": 3, "B": 1}).ok
    r = compare_books({"A": 1, "B": 2}, {"A": 1})
    assert not r.ok and "B" in r.breaks[0]
    assert compare_books({"A": 1, "B": 2}, {"A": 1}, explained={"B"}).ok  # unfilled buy


def test_L14_report_banners_and_figures() -> None:
    f = FillRecord("E1", "c1", "BK", "AAA", Side.BUY, 500, Decimal("1.03"), Decimal("6.60"), NOW)
    x = DailyInputs(
        "EMG2_20_PAPER",
        date(2026, 12, 1),
        False,
        Decimal("9478.40"),
        {"AAA": 500},
        {"AAA": Decimal("1.05")},
        Decimal(10000),
        [f],
        Decimal("6.60"),
        [("c1", "FILLED")],
        "NORMAL",
        sim_value=Decimal("10001"),
    )
    txt = daily_report(x)
    assert txt.startswith(PAPER_BANNER) and INDEX_BANNER in txt and L14_BANNER not in txt
    assert "Value A$10003.40" in txt and "+500 AAA @ 1.03" in txt and "0.07% of capital" in txt
    live = daily_report(DailyInputs(**{**x.__dict__, "real_money": True}))
    assert live.startswith(L14_BANNER)


def test_journal_ledger_views() -> None:
    j = Journal.sqlite()
    j.add_cash("BK", "DEPOSIT", Decimal(1000), "d")
    j.add_fill(FillRecord("E1", None, "BK", "A", Side.BUY, 10, Decimal(2), Decimal("6.60"), NOW))
    assert not j.add_fill(
        FillRecord("E1", None, "BK", "A", Side.BUY, 10, Decimal(2), Decimal("6.60"), NOW)
    )
    j.add_fill(FillRecord("E2", None, "BK", "A", Side.SELL, 4, Decimal(3), Decimal("6.60"), NOW))
    assert j.positions("BK") == {"A": 6}
    assert j.cash("BK") == Decimal("1000") - 20 - Decimal("6.60") + 12 - Decimal("6.60")
    assert j.holdings_cost("BK") == Decimal("15.96")
