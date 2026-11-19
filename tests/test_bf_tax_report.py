"""BF-D29 / BW-TAX-01 / BW-TAX-02: the financial-year tax report (``trader-bf tax-report``)
on synthetic journals and IBKR Flex fixtures. General information, not tax advice."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from trader.bfast_cli import main
from trader.ca_book import ingest_flex
from trader.corporate_actions import Booking, CaCalendar, CaKind, load_ca_csv
from trader.data.flex import parse_statements
from trader.journal import FillRecord, Journal
from trader.orders import Side
from trader.tax_report import (
    AMIT_MANUAL,
    NOT_ADVICE,
    AmitEntry,
    TaxParams,
    TaxReportError,
    build_report,
    fy_bounds,
    load_amit_csv,
    render_summary,
)

BOOK = "EMG2_18_PAPER"
FX = Path(__file__).parent / "fixtures"
FIFO = TaxParams("FIFO", 367, frozenset({"A200"}))
D = Decimal


def _fill(j: Journal, xid: str, code: str, side: Side, qty: int, px: str, d: date,
          brk: str = "6") -> None:  # fmt: skip
    # 05:00 UTC is 15:00/16:00 in Sydney: the same trade date
    t = datetime(d.year, d.month, d.day, 5, 0, tzinfo=UTC)
    j.add_fill(FillRecord(xid, None, BOOK, code, side, qty, D(px), D(brk), t))


def _j() -> Journal:
    j = Journal.sqlite()
    j.add_cash(BOOK, "DEPOSIT", D(10000), "test", datetime(2024, 7, 1, tzinfo=UTC))
    return j


def _by[T](rows: Iterable[T], **kw: object) -> list[T]:
    return [r for r in rows if all(getattr(r, k) == v for k, v in kw.items())]


def test_BF_D29_financial_year_bounds() -> None:
    assert fy_bounds("2026-27") == (date(2026, 7, 1), date(2027, 6, 30), "2026-27")
    for bad in ("2026", "2026-28", "26-27"):
        with pytest.raises(TaxReportError):
            fy_bounds(bad)


def test_BF_D29_BW_TAX_01_fifo_parcels_cost_with_brokerage_and_discount_split() -> None:
    """Two parcels, one sale across both: FIFO takes the old one first; the cost base has
    the purchase brokerage, the proceeds lose the sale brokerage."""
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 100, "10", date(2025, 8, 1))  # 1,006
    _fill(j, "B2", "AAA", Side.BUY, 100, "12", date(2026, 9, 1))  # 1,206
    _fill(j, "S1", "AAA", Side.SELL, 150, "15", date(2026, 10, 15))  # 2,250 - 6 = 2,244
    r = build_report(j, BOOK, "2026-27", FIFO)
    a, b = r.cgt
    assert (a.pid, a.qty, a.cost_base, a.proceeds, a.long) == (
        "P0001",
        D(100),
        D(1006),
        D(1496),
        True,
    )
    assert a.days_held == 440
    assert (b.pid, b.qty, b.cost_base, b.proceeds, b.long) == (
        "P0002",
        D(50),
        D(603),
        D(748),
        False,
    )
    s = r.summary
    assert (s.short_gains, s.long_gains, s.discount, s.net_gain) == (D(145), D(490), D(245), D(390))
    p1, p2 = r.parcels
    assert (p1.qty, p2.qty, p2.cost) == (D(0), D(50), D(603))
    assert r.totals()["brokerage_buys"] == D(6) and r.totals()["brokerage_sells"] == D(6)  # B2, S1
    assert r.flags == ()


def test_BF_D29_BW_TAX_01_min_tax_takes_the_loss_parcel_first() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 100, "10", date(2025, 8, 1))
    _fill(j, "B2", "AAA", Side.BUY, 100, "12", date(2026, 9, 1))
    _fill(j, "S1", "AAA", Side.SELL, 150, "11", date(2026, 10, 15))  # 10.96 a share net
    fifo = build_report(j, BOOK, "2026-27", FIFO)
    mt = build_report(j, BOOK, "2026-27", TaxParams("min_tax", 367, frozenset()))
    assert [c.pid for c in fifo.cgt] == ["P0001", "P0002"]
    assert [c.pid for c in mt.cgt] == ["P0002", "P0001"]
    assert mt.cgt[0].gain == D("1096") - D("1206")  # the loss is realised first
    assert "specific identification" in render_summary(mt)
    assert "FIFO" in render_summary(fifo) and "confirm the method" in render_summary(fifo)


def test_BF_D29_367_day_safety_margin_and_near_line_flag() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 10, "10", date(2025, 10, 15))
    _fill(j, "B2", "BBB", Side.BUY, 10, "10", date(2025, 10, 15))
    _fill(j, "S1", "AAA", Side.SELL, 10, "20", date(2026, 10, 16))  # 366 days
    _fill(j, "S2", "BBB", Side.SELL, 10, "20", date(2026, 10, 17))  # 367 days
    r = build_report(j, BOOK, "2026-27", FIFO)
    a, b = r.cgt
    assert (a.days_held, a.long, a.near_line) == (366, False, True)
    assert (b.days_held, b.long, b.near_line) == (367, True, False)
    assert any("near the 12-month line" in f for f in r.flags)
    md = render_summary(r)
    assert "367 days" in md and "safety" in md and NOT_ADVICE in md


def test_BF_D29_losses_offset_and_carry_forward_across_years() -> None:
    j = _j()
    _fill(j, "B1", "LLL", Side.BUY, 100, "10", date(2025, 8, 1))  # 1,006
    _fill(j, "S1", "LLL", Side.SELL, 100, "8", date(2026, 3, 2))  # 794: loss 212 in 2025-26
    r25 = build_report(j, BOOK, "2025-26", FIFO)
    assert (r25.summary.losses, r25.summary.net_gain, r25.summary.carried_out) == (
        D(212), D(0), D(212),
    )  # fmt: skip
    _fill(j, "B2", "GGG", Side.BUY, 100, "10", date(2025, 9, 1))  # 1,006, long by sale
    _fill(j, "B3", "HHH", Side.BUY, 100, "10", date(2026, 8, 1))  # 1,006, short
    _fill(j, "S2", "GGG", Side.SELL, 100, "14", date(2026, 11, 2))  # 1,394: +388 long
    _fill(j, "S3", "HHH", Side.SELL, 100, "11", date(2026, 11, 2))  # 1,094: +88 short
    s = build_report(j, BOOK, "2026-27", FIFO, prior_losses=D(50)).summary
    assert s.carried_in == D(262)  # 212 from 2025-26 of this book + 50 entered
    assert (s.applied_short, s.applied_long) == (D(88), D(174))
    assert (s.discount, s.net_gain, s.carried_out) == (D(107), D(107), D(0))


def test_BF_D29_BW_TAX_02_dividends_franking_known_and_unknown() -> None:
    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 100, "10", date(2026, 11, 10))
    _fill(j, "B2", "ZZZ", Side.BUY, 100, "10", date(2026, 11, 10))
    cal = CaCalendar()
    ingest_flex(j, BOOK, parse_statements((FX / "flex_ca" / "cash_dividend.xml").read_bytes()), cal)
    j.add_ca(BOOK, Booking("X:ZZZ", CaKind.DIVIDEND, "ZZZ", date(2026, 12, 1), date(2026, 12, 9),
                           100, cash=D(20), income=D(20)))  # fmt: skip
    r = build_report(j, BOOK, "2026-27", FIFO)
    t = r.totals()
    assert (t["dividends"], t["franked"], t["unfranked"], t["franking_credits"]) == (
        D(75), D(55), D(0), D("23.57"),
    )  # fmt: skip
    assert t["franking_not_known"] == D(20)
    assert "small-shareholder exemption" in render_summary(r)


def test_BF_D29_capital_return_lowers_parcel_cost_and_excess_is_g1() -> None:
    j = _j()
    _fill(j, "B1", "BBB", Side.BUY, 100, "0.20", date(2026, 11, 2))  # cost 26
    ingest_flex(j, BOOK, parse_statements((FX / "flex_ca" / "capital_return.xml").read_bytes()),
                CaCalendar())  # fmt: skip
    r = build_report(j, BOOK, "2026-27", FIFO)
    (adj,) = _by(r.adjust, kind="CAPITAL_RETURN")
    assert (adj.cost_before, adj.cost_after) == (D(26), D(0))
    (g1,) = _by(r.cgt, event="G1")
    assert g1.gain == D(4)
    assert r.parcels[0].cost == 0 and r.parcels[0].adjusted == D(-26)
    assert r.totals()["capital_returns"] == D(26)


def test_BF_D29_demerger_apportions_cost_and_keeps_acquisition_date() -> None:
    j = Journal.sqlite()
    _fill(j, "B1", "WOW", Side.BUY, 40, "37", date(2021, 6, 1))  # 1,486
    cal = CaCalendar.merged([], load_ca_csv(FX / "flex_ca" / "corporate_actions.csv"))
    ingest_flex(j, BOOK, parse_statements((FX / "flex_ca" / "demerger_wow_edv.xml").read_bytes()),
                cal)  # fmt: skip
    _fill(j, "S1", "EDV", Side.SELL, 40, "6", date(2022, 7, 1))
    r = build_report(j, BOOK, "2022-23", FIFO)
    wow, edv = r.parcels
    assert edv.code == "EDV" and edv.acquired == date(2021, 6, 1)  # roll-over: original date
    moved = D(1486) * D("0.1407")
    assert wow.cost == D(1486) - moved
    (sale,) = r.cgt
    assert (sale.cost_base, sale.proceeds, sale.long) == (moved, D(234), True)
    assert len(_by(r.adjust, kind="DEMERGER")) == 0  # adjustments were in 2020-21
    r21 = build_report(j, BOOK, "2020-21", FIFO)
    assert {a.code for a in _by(r21.adjust, kind="DEMERGER")} == {"WOW", "EDV"}


def test_BF_D29_split_code_change_disposal_and_cash_in_lieu() -> None:
    j = _j()
    _fill(j, "B1", "OLD", Side.BUY, 1005, "0.10", date(2026, 11, 2))  # 106.50
    ingest_flex(j, BOOK,
                parse_statements((FX / "flex_ca" / "code_change_ratio.xml").read_bytes()),
                CaCalendar())  # fmt: skip
    _fill(j, "B2", "SSS", Side.BUY, 10, "50", date(2026, 11, 2))  # 506
    j.add_ca(BOOK, Booking("X:SPLIT", CaKind.SPLIT, "SSS", date(2027, 1, 5), date(2027, 1, 5),
                           10, qty_change=10, ratio=D(2)))  # fmt: skip
    j.add_ca(BOOK, Booking("X:TAKE", CaKind.DISPOSAL, "SSS", date(2027, 3, 1), date(2027, 3, 1),
                           20, cash=D(700), qty_change=-20))  # fmt: skip
    r = build_report(j, BOOK, "2026-27", FIFO)
    new = _by(list(r.parcels), code="NEW")[0]
    frac_cost = D("106.50") * D("0.5") / D("100.5")  # 1,005 OLD = 100.5 NEW; 0.5 for cash
    assert (new.qty, new.cost, new.traded_as) == (D(100), D("106.50") - frac_cost, "OLD")
    assert not any(f.startswith("parcels v journal") for f in r.flags)
    (cil,) = _by(r.cgt, event="CASH_IN_LIEU")
    assert (cil.qty, cil.cost_base, cil.proceeds) == (D("0.5"), frac_cost, D("0.45"))
    assert _by(r.adjust, kind="CODE_CHANGE")[0].qty_after == D("100.5")
    (sp,) = _by(r.adjust, kind="SPLIT")
    assert (sp.qty_before, sp.qty_after, sp.cost_after) == (D(10), D(20), D(506))
    (dis,) = _by(r.cgt, event="DISPOSAL")
    assert (dis.qty, dis.cost_base, dis.proceeds, dis.gain) == (D(20), D(506), D(700), D(194))


def test_BF_D29_fund_distribution_and_amit_entered_or_flagged() -> None:
    j = _j()
    _fill(j, "B1", "A200", Side.BUY, 70, "130", date(2026, 12, 1), "9.10")  # 9,109.10
    j.add_ca(BOOK, Booking("X:A200", CaKind.DIVIDEND, "A200", date(2027, 1, 2), date(2027, 1, 15),
                           70, cash=D(84), income=D(84)))  # fmt: skip
    r = build_report(j, BOOK, "2026-27", FIFO)
    (dist,) = r.income
    assert dist.kind == "DISTRIBUTION" and r.totals()["distributions"] == D(84)
    assert r.totals()["dividends"] == 0
    assert r.amit_missing == ("A200",)
    assert any(AMIT_MANUAL in f for f in r.flags)
    assert "NOT ENTERED" in render_summary(r) and AMIT_MANUAL in render_summary(r)
    amit = [AmitEntry(2026, "A200", D(0), D("12.60"), "statement 2027-08")]
    r2 = build_report(j, BOOK, "2026-27", FIFO, amit=amit)
    assert r2.amit_missing == ()
    (adj,) = _by(r2.adjust, kind="AMIT")
    assert (adj.day, adj.cost_before, adj.cost_after) == (
        date(2027, 6, 30), D("9109.10"), D("9096.50"),
    )  # fmt: skip
    assert r2.parcels[0].cost == D("9096.50")


def test_BF_D29_amit_csv_loads_and_rejects_negative(tmp_path: Path) -> None:
    p = tmp_path / "amit.csv"
    p.write_text("fy,code,cost_base_increase,cost_base_decrease,note\n2026-27,a200,1.5,,x\n")
    assert load_amit_csv(p) == [AmitEntry(2026, "A200", D("1.5"), D(0), "x")]
    p.write_text("fy,code,cost_base_increase,cost_base_decrease,note\n2026-27,A200,-1,,x\n")
    with pytest.raises(TaxReportError):
        load_amit_csv(p)


def _recon_journal() -> Journal:
    j = Journal.sqlite()
    j.add_cash(BOOK, "DEPOSIT", D(10000), "owner", datetime(2026, 8, 1, 0, 30, tzinfo=UTC))
    _fill(j, "T1", "AAA", Side.BUY, 100, "10", date(2026, 8, 3))
    _fill(j, "T2", "AAA", Side.SELL, 40, "12", date(2026, 10, 15), "6.60")  # IBKR: 6.00
    _fill(j, "T3", "A200", Side.BUY, 70, "130", date(2026, 12, 1), "9.10")
    _fill(j, "T4", "CCC", Side.BUY, 5, "100", date(2027, 2, 1))  # not in IBKR's records
    return j


def test_BF_D29_reconciliation_against_flex_flags_every_difference() -> None:
    j = _recon_journal()
    sts = parse_statements((FX / "tax" / "flex_fy2026_27.xml").read_bytes())
    ingest_flex(j, BOOK, sts, CaCalendar())
    r = build_report(j, BOOK, "2026-27", FIFO, sts, account_id="DU1234567")
    st = {(x.area, x.ref): x for x in r.recon}
    assert st[("TRADE", "T2")].status == "DIFF" and "brokerage" in st[("TRADE", "T2")].note
    assert st[("TRADE", "T4")].status == "MISSING_IN_FLEX"
    assert st[("TRADE", "T9")].status == "MISSING_IN_JOURNAL"
    assert ("TRADE", "T1") not in st and ("TRADE", "T3") not in st  # agree
    assert st[("TOTAL", "brokerage")].status == "DIFF"
    assert st[("CASH", "dividends and distributions")].status == "OK"  # 30 + 84
    assert st[("CASH", "deposits and withdrawals")].status == "OK"
    assert st[("CASH", "Broker Interest Received")].status == "NOT_BOOKED"
    assert st[("POSITION", "AAA at 2027-06-30")].status == "OK"
    assert st[("POSITION", "CCC at 2027-06-30")].status == "DIFF"
    assert st[("POSITION", "A200 at 2027-06-30")].status == "OK"
    md = render_summary(r)
    assert "difference(s)" in md and "MISSING_IN_FLEX" in md
    (div,) = _by(r.income, code="AAA")
    assert (div.franked_pct, div.franking_credit) == (D(100), D("12.86"))


def test_BF_D29_reconciliation_without_statements_and_other_accounts() -> None:
    j = _recon_journal()
    sts = parse_statements((FX / "tax" / "flex_fy2026_27.xml").read_bytes())
    r = build_report(j, BOOK, "2026-27", FIFO, sts, account_id="DU7654321")
    assert [x.status for x in r.recon] == ["INFO", "DIFF"]
    assert build_report(j, BOOK, "2026-27", FIFO).recon == ()
    assert "Not run" in render_summary(build_report(j, BOOK, "2026-27", FIFO))


def test_BF_D29_cli_writes_csv_and_summary(tmp_path: Path) -> None:
    db = tmp_path / "j.sqlite3"
    from sqlalchemy import create_engine

    j = Journal(create_engine(f"sqlite:///{db}"))
    j.add_cash(BOOK, "DEPOSIT", D(10000), "owner", datetime(2026, 8, 1, 0, 30, tzinfo=UTC))
    _fill(j, "T1", "AAA", Side.BUY, 100, "10", date(2026, 8, 3))
    _fill(j, "T2", "AAA", Side.SELL, 40, "12", date(2026, 10, 15))
    flex = tmp_path / "flex"
    flex.mkdir()
    (flex / "a.xml").write_bytes((FX / "tax" / "flex_fy2026_27.xml").read_bytes())
    amit = tmp_path / "amit.csv"
    amit.write_text("fy,code,cost_base_increase,cost_base_decrease,note\n")
    out = tmp_path / "out"
    rc = main(["tax-report", "--fy", "2026-27", "--journal", f"sqlite:///{db}", "--flex",
               str(flex), "--amit", str(amit), "--out", str(out)])  # fmt: skip
    assert rc == 0
    names = sorted(p.name for p in out.iterdir())
    pre = f"tax_{BOOK}_FY2026-27_"
    assert names == sorted(pre + x for x in (
        "capital_gains.csv", "cost_base_changes.csv", "income.csv", "parcels.csv",
        "reconciliation.csv", "summary.md", "trades.csv",
    ))  # fmt: skip
    for p in out.glob("*.csv"):
        assert NOT_ADVICE in p.read_text()
    rows = list(csv.reader((out / f"{pre}capital_gains.csv").read_text().splitlines()))
    assert rows[1][:3] == ["event", "code", "parcel"]
    assert rows[2][:2] == ["SALE", "AAA"] and rows[2][8] == "71.60"  # 474 - 402.40
    md = (out / f"{pre}summary.md").read_text()
    assert "PAPER ACCOUNT" in md and NOT_ADVICE in md and "FIFO" in md


def test_BF_D29_tax_config_defaults_and_fund_codes() -> None:
    from trader.bfast_config import load_bfast_config

    cfg = load_bfast_config(Path("config/bfast.yaml"))
    assert (cfg.tax.parcel_method, cfg.tax.discount_days) == ("FIFO", 367)
    assert "A200" in cfg.fund_codes()


def test_BF_D29_in_specie_income_capital_part_and_new_parcel() -> None:
    j = _j()
    _fill(j, "B1", "XYZ", Side.BUY, 400, "5", date(2026, 11, 2))  # 2,006
    j.add_ca(BOOK, Booking("X:XYZ", CaKind.IN_SPECIE, "XYZ", date(2026, 11, 23), date(2026, 12, 1),
                           400, income=D(600), franked_pct=D(100), franking_credit=D("257.14"),
                           cost_reduction=D(200), new_code="CHD", new_shares=100,
                           child_cost=D(800)))  # fmt: skip
    r = build_report(j, BOOK, "2026-27", FIFO)
    (inc,) = r.income
    assert (inc.kind, inc.income, inc.franked, inc.franking_credit) == (
        "IN_SPECIE", D(600), D(600), D("257.14"),
    )  # fmt: skip
    xyz, chd = r.parcels
    assert xyz.cost == D(1806)
    assert (chd.code, chd.qty, chd.cost, chd.acquired) == (
        "CHD",
        D(100),
        D(800),
        date(2026, 11, 23),
    )
