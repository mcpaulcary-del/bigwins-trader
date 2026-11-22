"""BF-D44: the app's Tax screen and EOFY CSV (Australian individual, 1 July - 30 June).
Estimate for your records - not tax advice. Paper account: no real tax."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from tests.test_bf_tax_report import BOOK, _by, _fill, _j
from trader.app_pages import Extras
from trader.corporate_actions import Booking, CaKind
from trader.dashboard import Sources, collect
from trader.journal import Journal
from trader.orders import Side
from trader.tax_report import CgtRow, TaxParams, build_report, plus_12_months, summarise
from trader.tax_screen import CSV_COLUMNS, LABEL, csv_export, rebuy_flags, screen, unrealised

D = Decimal
ATO = TaxParams("FIFO", 367, frozenset(), "12_months")


def test_BF_D44_twelve_month_boundary() -> None:
    a = date(2025, 11, 3)
    assert not ATO.eligible(a, date(2026, 11, 3))  # exactly 12 months: not yet
    assert ATO.eligible(a, date(2026, 11, 4))  # the day after: eligible
    assert ATO.eligible_from(a) == date(2026, 11, 4)
    assert plus_12_months(date(2024, 2, 29)) == date(2025, 2, 28)
    assert not ATO.eligible(date(2024, 2, 29), date(2025, 2, 28))
    assert ATO.eligible(date(2024, 2, 29), date(2025, 3, 1))
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 10, "10", date(2025, 11, 3))
    _fill(j, "B2", "BBB", Side.BUY, 10, "10", date(2025, 11, 3))
    _fill(j, "S1", "AAA", Side.SELL, 10, "20", date(2026, 11, 3))
    _fill(j, "S2", "BBB", Side.SELL, 10, "20", date(2026, 11, 4))
    r = build_report(j, BOOK, "2026-27", ATO)
    a_, b_ = _by(r.cgt, code="AAA")[0], _by(r.cgt, code="BBB")[0]
    assert (a_.long, b_.long) == (False, True) and a_.near_line


def _row(gain: str, long: bool) -> CgtRow:
    g = D(gain)
    cost = D(1000)
    return CgtRow(2026, "SALE", "X", "P", date(2025, 1, 1), date(2026, 8, 1), D(1), cost,
                  cost + g, 400, long, False, "r")  # fmt: skip


def test_BF_D44_losses_go_to_non_discount_gains_first_then_discount() -> None:
    s = summarise([_row("100", False), _row("300", True), _row("-150", False)], D(0))
    assert (s.applied_short, s.applied_long, s.discount, s.net_gain) == (
        D(100), D(50), D(125), D(125))  # fmt: skip
    s2 = summarise([_row("100", False)], D(300))  # carried-in losses: same order
    assert (s2.applied_short, s2.net_gain, s2.carried_out) == (D(100), D(0), D(200))


def test_BF_D44_fifo_partial_sells_split_parcels_with_brokerage() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 100, "1", date(2026, 7, 2), brk="5")  # cost 105
    _fill(j, "B2", "AAA", Side.BUY, 100, "2", date(2026, 7, 9), brk="5")  # cost 205
    _fill(j, "S1", "AAA", Side.SELL, 150, "3", date(2026, 8, 3), brk="6")  # net 444
    r = build_report(j, BOOK, "2026-27", ATO)
    rows = sorted(_by(r.cgt, code="AAA"), key=lambda c: c.acquired or date.min)
    assert [(c.qty, c.cost_base) for c in rows] == [(D(100), D(105)), (D(50), D("102.5"))]
    assert sum((c.proceeds for c in rows), D(0)) == D(444)  # proceeds net of sell brokerage
    assert rows[0].proceeds == D(296) and rows[1].proceeds == D(148)
    left = [p for p in r.parcels if p.qty > 0]
    assert [(p.qty, p.cost) for p in left] == [(D(50), D("102.5"))]


def test_BF_D44_split_keeps_cost_and_halves_cost_per_share() -> None:
    j = _j()
    _fill(j, "B1", "SSS", Side.BUY, 10, "50", date(2026, 7, 2))  # cost 506
    j.add_ca(BOOK, Booking("X:SPLIT", CaKind.SPLIT, "SSS", date(2026, 9, 1), date(2026, 9, 1),
                           10, qty_change=10, ratio=D(2)))  # fmt: skip
    r = build_report(j, BOOK, "2026-27", ATO)
    (p,) = _by(list(r.parcels), code="SSS")
    assert (p.qty, p.cost, p.cost / p.qty, p.acquired) == (
        D(20),
        D(506),
        D("25.3"),
        date(2026, 7, 2),
    )


def test_BF_D44_code_change_keeps_the_acquisition_date() -> None:
    j = _j()
    _fill(j, "B1", "HGO", Side.BUY, 100, "1", date(2025, 7, 2))
    t = datetime(2026, 1, 5, tzinfo=UTC)
    j.add_identity("HGO", "KAN", "CONFIRMED", "OWNER", None, "test", "owner", t)
    _fill(j, "S1", "KAN", Side.SELL, 100, "2", date(2026, 8, 3))
    r = build_report(j, BOOK, "2026-27", ATO)
    (c,) = r.cgt
    assert (c.code, c.acquired, c.long) == ("KAN", date(2025, 7, 2), True)


def test_BF_D44_financial_year_boundary_30_june_1_july() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 10, "10", date(2026, 1, 5))
    _fill(j, "S1", "AAA", Side.SELL, 5, "12", date(2026, 6, 30))
    _fill(j, "S2", "AAA", Side.SELL, 5, "12", date(2026, 7, 1))
    a = build_report(j, BOOK, "2025-26", ATO)
    b = build_report(j, BOOK, "2026-27", ATO)
    assert [c.disposed for c in a.cgt] == [date(2026, 6, 30)]
    assert [c.disposed for c in b.cgt] == [date(2026, 7, 1)]


@dataclass
class _Src:
    journal: Journal
    book: str = BOOK
    tax_params: TaxParams = ATO
    marginal_rate: Decimal | None = None
    clock: Any = lambda: datetime(2026, 12, 1, 3, tzinfo=UTC)


def test_BF_D44_csv_columns_and_rows() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 10, "10", date(2025, 7, 2))
    _fill(j, "S1", "AAA", Side.SELL, 10, "20", date(2026, 8, 3))
    out = list(csv.reader(io.StringIO(csv_export(_Src(j), {"fy": "2026-27"}))))
    assert tuple(out[0]) == CSV_COLUMNS == (
        "section", "code", "qty", "acquired", "disposed", "cost_base", "proceeds", "gain",
        "discount_eligible", "discount_applied", "method", "note")  # fmt: skip
    disp = [r for r in out if r[0] == "disposal"]
    assert disp == [["disposal", "AAA", "10", "2025-07-02", "2026-08-03", "106.00", "194.00",
                     "88.00", "yes", "44.00", "FIFO", "SALE"]]  # fmt: skip
    assert out[-1][-1] == LABEL and "not tax advice" in LABEL


def test_BF_D44_screen_unrealised_rebuy_flag_and_estimate() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 10, "10", date(2025, 11, 3))
    _fill(j, "S1", "BBB", Side.BUY, 10, "10", date(2026, 7, 2))
    _fill(j, "S2", "BBB", Side.SELL, 10, "8", date(2026, 8, 3))  # a loss (L4)
    _fill(j, "S3", "BBB", Side.BUY, 10, "11", date(2026, 8, 20))
    j.mark_job("marks:2026-11-30", {"AAA": "15", "BBB": "11"}, datetime(2026, 11, 30, tzinfo=UTC))
    today = date(2026, 12, 1)
    un = unrealised(_Src(j), {"AAA": D(15)}, today)
    aaa = next(u for u in un if u.code == "AAA")
    assert aaa.eligible_from == date(2026, 11, 4) and aaa.value == D(150)
    rep = build_report(j, BOOK, "2026-27", ATO)
    flags = rebuy_flags(_Src(j), date(2026, 7, 1), date(2027, 6, 30), rep)
    assert flags and "BBB" in flags[0] and "17 days" in flags[0]
    src = Sources(j, BOOK, clock=lambda: datetime(2026, 12, 1, 10, tzinfo=UTC),
                  today=lambda: today, tax_params=ATO, marginal_rate=D("0.345"))  # fmt: skip
    v = collect(src)
    page = screen(v, Extras(), src, {"fy": "2026-27"})
    assert "not tax advice" in page and "Paper account: no real tax" in page
    assert "Estimated tax" in page and "34.5%" in page and "FIFO" in page
    assert "TR 2008/1" in page and "discount now" in page
    assert "enter them from your dividend statements" not in page  # no dividends: no gap
