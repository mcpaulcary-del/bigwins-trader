"""Full review, tax (22 Nov 2026; BF-D71): flag for the accountant rather than guess."""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime
from decimal import Decimal as D  # noqa: N817
from types import SimpleNamespace as NS  # noqa: N814
from typing import Any

from trader.corporate_actions import Booking, CaCalendar, CaKind, _action_bookings
from trader.data.flex import FlexCorporateAction as CA  # noqa: N814
from trader.journal import FillRecord, Journal
from trader.orders import Side
from trader.tax_report import AmitEntry, TaxParams, accountant_items, build_report

BOOK = "B"
P12 = TaxParams("FIFO", 367, frozenset({"A200"}), "12_months")
N = datetime(2026, 1, 1, tzinfo=UTC)


def J() -> Journal:
    j = Journal.sqlite()
    j.add_cash(BOOK, "DEPOSIT", D(100000), "t", datetime(2020, 7, 1, tzinfo=UTC))
    return j


def fill(j: Journal, x: str, code: str, side: Side, q: int, px: str, d: date, brk: str = "6",
         h: int = 1) -> None:  # fmt: skip
    j.add_fill(FillRecord(x, None, BOOK, code, side, q, D(px), D(brk),
                          datetime(d.year, d.month, d.day, h, 0, tzinfo=UTC)))  # fmt: skip


def test_F1_scrip_merger_is_a_provisional_takeover_not_a_code_change() -> None:
    d = date(2026, 8, 3)
    desc = "TGT(AU000000TGT1) MERGED(Acquisition) FOR AU000000ACQ1 1 FOR 2 + AUD 0.50"
    rows = [CA("1", "A1", "TC", "TGT", None, D(-1000), D(0), None, d, None, desc),
            CA("2", "A1", "TC", "ACQ", None, D(500), D(500), D(3000), d, None, desc)]  # fmt: skip
    (b,), ids = _action_bookings(rows, CaCalendar([]), lambda c, x: 1000, {})
    assert b.kind is CaKind.DISPOSAL and ids == []  # no identity hint applied
    assert (b.new_code, b.new_shares, b.child_cost, b.cash) == ("ACQ", 500, D(3000), D(500))
    j = J()
    fill(j, "B1", "TGT", Side.BUY, 1000, "2", date(2025, 1, 10))
    j.add_ca(BOOK, b, N)
    r = build_report(j, BOOK, "2026-27", P12)
    (row,) = [c for c in r.cgt if c.code == "TGT"]
    assert row.event == "TAKEOVER" and row.proceeds == D(3500) and "PROVISIONAL" in row.note
    assert any("Subdiv 124-M" in f for f in r.flags)
    assert any(p.code == "ACQ" and p.cost == D(3000) for p in r.parcels)
    assert j.positions(BOOK) == {"ACQ": 500}


def test_F2_worthless_delisting_books_no_loss_and_disposals_are_flagged() -> None:
    j = J()
    fill(j, "B1", "DED", Side.BUY, 1000, "1", date(2025, 7, 10))
    j.add_ca(BOOK, Booking("K5", CaKind.DISPOSAL, "DED", date(2026, 8, 3), date(2026, 8, 3), 1000,
                           cash=D(0), qty_change=-1000), N)  # fmt: skip
    fill(j, "B2", "TKO", Side.BUY, 1000, "2", date(2025, 6, 27))
    j.add_ca(BOOK, Booking("K4", CaKind.DISPOSAL, "TKO", date(2026, 7, 3), date(2026, 7, 3), 1000,
                           cash=D(3000), qty_change=-1000,
                           note="TKO OFF-MARKET BUY BACK"), N)  # fmt: skip
    r = build_report(j, BOOK, "2026-27", P12)
    assert not [c for c in r.cgt if c.code == "DED"]  # no loss booked
    assert any("possible capital loss" in f and "G3" in f for f in r.flags)
    assert any("TKO" in f and "contract / scheme implementation date" in f for f in r.flags)
    assert any("buy-back" in f for f in r.flags)


def test_F3_F4_amit_flags_and_attribution_year() -> None:
    j = J()
    fill(j, "B0", "A200", Side.BUY, 100, "130", date(2025, 7, 10))
    fill(j, "S0", "A200", Side.SELL, 90, "140", date(2026, 6, 10))
    j.add_ca(BOOK, Booking("DIST", CaKind.DIVIDEND, "A200", date(2026, 6, 29), date(2026, 7, 16),
                           10, cash=D(12), income=D(12)), N)  # fmt: skip
    r = build_report(j, BOOK, "2025-26", P12, amit=[AmitEntry(2025, "A200", D(100), D(0))])
    assert any("apportion" in f for f in r.flags)
    assert [i.kind for i in r.income] == ["DISTRIBUTION"]  # June ex-date: this year
    r2 = build_report(j, BOOK, "2025-26", P12)
    assert any("units sold" in f and "no AMIT entry" in f for f in r2.flags)


def test_F5_consolidation_keeps_every_parcels_cost_base() -> None:
    j = J()
    fill(j, "B1", "CON", Side.BUY, 4, "1", date(2024, 8, 1), "0")
    fill(j, "B2", "CON", Side.BUY, 1000, "1", date(2024, 10, 1), "6")
    j.add_ca(BOOK, Booking("K2", CaKind.SPLIT, "CON", date(2025, 2, 3), date(2025, 2, 3), 1004,
                           qty_change=-904, ratio=D("0.1")), N)  # fmt: skip
    fill(j, "S1", "CON", Side.SELL, 100, "12", date(2025, 9, 1))
    r = build_report(j, BOOK, "2025-26", P12)
    assert sum(c.cost_base for c in r.cgt) == D(1010)  # 4 + 1006: nothing dropped


def test_F6_capital_return_gain_dated_by_payment() -> None:
    j = J()
    fill(j, "B1", "CAP", Side.BUY, 100, "1", date(2024, 8, 1), "0")
    j.add_ca(BOOK, Booking("K6", CaKind.CAPITAL_RETURN, "CAP", date(2026, 6, 25),
                           date(2026, 7, 20), 100, cash=D(300), cost_reduction=D(300)), N)  # fmt: skip
    r = build_report(j, BOOK, "2026-27", P12)
    (g1,) = [c for c in r.cgt if c.event == "G1"]
    assert g1.disposed == date(2026, 7, 20) and g1.proceeds == D(200)


def test_F7_franking_only_from_the_statement_rate() -> None:
    from trader.corporate_actions import CaEvent, book_event

    ev = CaEvent("E", CaKind.DIVIDEND, "AAA", date(2026, 9, 1), per_share=D("0.70"),
                 franked_pct=D(100))  # fmt: skip
    assert book_event(ev, 100, {}, "k").franking_credit == 0  # type: ignore[union-attr]
    ev2 = CaEvent("E", CaKind.DIVIDEND, "AAA", date(2026, 9, 1), per_share=D("0.70"),
                  franked_pct=D(100), franking_rate=D("0.25"))  # fmt: skip
    assert book_event(ev2, 100, {}, "k").franking_credit == D("23.33")  # type: ignore[union-attr]


def _src(j: Journal, **kw: object) -> NS:
    return NS(journal=j, book=BOOK, tax_params=P12, live=False, amit_csv=None,
              clock=lambda: datetime(2026, 7, 10, tzinfo=UTC), prior_losses=0, **kw)  # fmt: skip


def test_F8_estimate_subtracts_tfn_withholding() -> None:
    from trader.dashboard import Sources, collect
    from trader.tax_screen import screen

    j = J()
    fill(j, "B1", "UNF", Side.BUY, 1000, "1", date(2025, 7, 10))
    j.add_ca(BOOK, Booking("W", CaKind.WITHHOLDING, "UNF", date(2025, 9, 1), date(2025, 9, 25),
                           1000, cash=D(-141)), N)  # fmt: skip
    j.add_ca(BOOK, Booking("DV", CaKind.DIVIDEND, "UNF", date(2025, 9, 1), date(2025, 9, 25),
                           1000, cash=D(300), income=D(300), franked_pct=D(0)), N)  # fmt: skip
    src = Sources(j, BOOK, clock=lambda: datetime(2026, 7, 10, tzinfo=UTC),
                  today=lambda: date(2026, 7, 10), tax_params=P12, marginal_rate=D("0.30"))  # fmt: skip
    page = screen(collect(src), _x(), src, {"fy": "2025-26"})
    # 300 x 30% = 90, less the 141 withheld = -51 (a refund)
    assert "TFN amounts withheld \u2013 claimable credit" in page and "\u2212A$51.00" in page


def _x() -> Any:
    from trader.app_pages import Extras

    return Extras()


def test_F9_buy_before_a_loss_sale_is_flagged_per_fill() -> None:
    j = J()
    fill(j, "B3", "PRE", Side.BUY, 100, "10", date(2025, 8, 1))
    fill(j, "B4", "PRE", Side.BUY, 100, "7", date(2026, 3, 2))
    fill(j, "S4", "PRE", Side.SELL, 100, "7", date(2026, 3, 5))
    r = build_report(j, BOOK, "2025-26", P12)
    w = [f for f in r.flags if "TR 2008/1" in f]
    assert len(w) == 1 and "fill S4" in w[0] and "before" in w[0] and "fill B4" in w[0]


def test_F10_F11_csv_rounding_columns_sections_and_checklist() -> None:
    from trader.tax_screen import csv_export

    j = J()
    fill(j, "B1", "AAA", Side.BUY, 100, "10", date(2024, 8, 1), "6")
    fill(j, "B2", "AAA", Side.BUY, 200, "12", date(2025, 3, 3), "9.5")
    fill(j, "S2", "AAA", Side.SELL, 150, "20", date(2025, 9, 1), "7.37")
    fill(j, "B4", "CCC", Side.BUY, 300, "7", date(2025, 7, 1), "6")
    fill(j, "S3", "CCC", Side.SELL, 300, "6", date(2025, 12, 1), "6")
    fill(j, "S4", "AAA", Side.SELL, 150, "25", date(2026, 3, 4), "7")
    out = list(csv.reader(io.StringIO(csv_export(_src(j), {"fy": "2025-26"}))))
    disp = [r for r in out if r[0] == "disposal"]
    summ = {r[1].strip(): D(r[7]) for r in out if r[0] == "summary"}
    assert sum(D(r[9]) for r in disp) == summ["CGT discount applied"]
    assert summ["total current-year capital losses"] > 0
    assert "of which listed shares" in summ and "of which units in listed trusts" in summ
    assert all(r[12].startswith("P") and r[13] for r in disp)
    assert any(r[0] == "section" and r[1] == "code" and r[2] == "units" for r in out)
    chk = [r for r in out if r[0] == "checklist"][1:]
    assert len(chk) == 11 and any(r[1].startswith("10.") and r[2] == "yes" for r in chk)


def test_F12_gst_in_flex_taxes_goes_into_the_cost_base() -> None:
    j = J()
    fill(j, "B1", "AAA", Side.BUY, 100, "10", date(2025, 8, 1), "6.60")  # incl. GST
    fill(j, "B2", "BBB", Side.BUY, 100, "10", date(2025, 8, 1), "6.00")  # no GST row
    r = build_report(j, BOOK, "2025-26", P12)
    cost = {p.code: p.cost for p in r.parcels}
    assert cost == {"AAA": D("1006.60"), "BBB": D("1006.00")}


def test_checklist_items_marked_not_applicable_when_no_data() -> None:
    j = J()
    r = build_report(j, BOOK, "2025-26", P12)
    items = accountant_items(r)
    assert len(items) == 11
    rel = {t.split(".")[0]: x for t, x in items}
    assert rel["10"] is True and rel["3"] is False and rel["5"] is False


def test_per_parcel_discount_dates_on_the_share_screen() -> None:
    from trader.share_pages import parcel_dates

    j = J()
    fill(j, "B1", "AAA", Side.BUY, 100, "10", date(2025, 8, 1))
    fill(j, "B2", "AAA", Side.BUY, 50, "11", date(2026, 2, 2))
    got = parcel_dates(j, BOOK, "AAA", date(2026, 3, 1))
    assert [(a, e) for a, _, e in got] == [(date(2025, 8, 1), date(2026, 8, 2)),
                                           (date(2026, 2, 2), date(2027, 2, 3))]  # fmt: skip
