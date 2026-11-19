"""BF-D23 / BF-D25: dividends, capital returns, specials, demergers, in-specie receipts
and code changes with a share ratio, booked into the journal from IBKR's Flex records
(broker books) or from the vendor + record calendar (simulated books), and matched by
reconciliation while IBKR's records are still on their way. Synthetic Flex fixtures
(``tests/fixtures/flex_ca``): one per event type."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from trader.ca_book import book_calendar_day, describe, ingest_flex, pending_expectations
from trader.corporate_actions import (
    CaCalendar,
    CaError,
    CaEvent,
    CaKind,
    load_ca_csv,
    parse_ratio,
    ratio_from_note,
    vendor_events,
)
from trader.data.flex import parse_statements
from trader.journal import FillRecord, Journal
from trader.orders import Side
from trader.reconcile import reconcile

FX = Path(__file__).parent / "fixtures" / "flex_ca"
BOOK = "EMG2_18_PAPER"


def _flex(name: str) -> list:  # type: ignore[type-arg]
    return parse_statements((FX / name).read_bytes())


def _journal(*holdings: tuple[str, int, str, date]) -> Journal:
    j = Journal.sqlite()
    j.add_cash(BOOK, "DEPOSIT", Decimal(10000), "test", datetime(2020, 1, 1, tzinfo=UTC))
    for i, (code, qty, px, d) in enumerate(holdings):
        j.add_fill(
            FillRecord(f"X{i}", None, BOOK, code, Side.BUY, qty, Decimal(px), Decimal(6),
                       datetime(d.year, d.month, d.day, 5, 10, tzinfo=UTC))
        )  # fmt: skip
    return j


def _cal(*vendor: tuple[str, date, str]) -> CaCalendar:
    v = vendor_events((c, d, Decimal(x), None) for c, d, x in vendor)
    return CaCalendar.merged(v, load_ca_csv(FX / "corporate_actions.csv"))


def test_BF_D23_flex_parser_reads_corporate_action_rows_and_dividend_dates() -> None:
    st = _flex("code_change_ratio.xml")[0]
    rows = st.corporate_actions
    assert [(r.symbol, r.quantity, r.type, r.action_id) for r in rows] == [
        ("OLD", Decimal(-1005), "RS", "77041"),
        ("NEW", Decimal(100), "RS", "77041"),
    ]
    assert rows[1].amount == Decimal("0.45")
    c = _flex("cash_dividend.xml")[0].cash_transactions[1]
    assert (c.ex_date, c.pay_date) == (date(2026, 11, 18), date(2026, 11, 25))
    assert _flex("cash_dividend.xml")[0].corporate_actions == ()


def test_BF_D23_BW_UNI_23_cash_dividend_from_flex_is_income_with_franking() -> None:
    j = _journal(("AAA", 100, "10", date(2026, 11, 10)))
    cal = _cal(("AAA", date(2026, 11, 18), "0.55"))
    cash0 = j.cash(BOOK)
    r = ingest_flex(j, BOOK, _flex("cash_dividend.xml"), cal)
    (b,) = r.booked
    assert b.kind is CaKind.DIVIDEND
    assert (b.cash, b.income, b.held) == (Decimal(55), Decimal(55), 100)
    assert b.franked_pct == 100
    assert b.franking_credit == Decimal("23.57")  # 55 x 30/70
    assert b.expected_key == "VENDOR:AAA:2026-11-18"
    assert r.skipped == ("Deposits/Withdrawals 9100001",)  # deposits are booked by hand
    assert j.cash(BOOK) == cash0 + 55
    assert ingest_flex(j, BOOK, _flex("cash_dividend.xml"), cal).booked == ()  # once only
    assert j.cash(BOOK) == cash0 + 55
    tv = j.tax_view(BOOK, date(2027, 6, 30))
    assert (tv["dividends"], tv["franking_credits"], tv["capital_returns"]) == (
        "55.00", "23.57", "0.00",
    )  # fmt: skip
    assert "100% franked" in describe(b)


def test_BF_D23_capital_return_reduces_the_cost_base_not_income() -> None:
    """BBB: IBKR's text says return of capital. CCC: IBKR and the vendor call it a
    dividend; the record's CSV says capital return, and the CSV wins."""
    j = _journal(("BBB", 100, "5", date(2026, 11, 2)), ("CCC", 200, "4", date(2026, 11, 2)))
    cal = _cal(("CCC", date(2026, 11, 19), "0.40"), ("BBB", date(2026, 11, 19), "0.30"))
    assert [e.source for e in cal.events if e.code == "CCC"] == ["CSV"]  # vendor row replaced
    cost0 = j.holdings_cost(BOOK)
    r = ingest_flex(j, BOOK, _flex("capital_return.xml"), cal)
    kinds = {b.code: b for b in r.booked}
    assert kinds["BBB"].kind is CaKind.CAPITAL_RETURN
    assert kinds["CCC"].kind is CaKind.CAPITAL_RETURN
    assert kinds["CCC"].expected_key == "CSV:CCC:2026-11-19:CAPITAL_RETURN"
    assert j.holdings_cost(BOOK) == cost0 - 30 - 80
    tv = j.tax_view(BOOK, date(2027, 6, 30))
    assert (tv["dividends"], tv["capital_returns"], tv["g1_gains"]) == ("0.00", "110.00", "0.00")


def test_BF_D23_capital_return_above_the_cost_base_is_a_g1_gain() -> None:
    j = _journal(("BBB", 100, "0.20", date(2026, 11, 2)))  # cost 20 + 6 = 26
    ingest_flex(j, BOOK, _flex("capital_return.xml"), CaCalendar())
    assert j.holdings_cost(BOOK) == 0
    assert j.tax_view(BOOK, date(2027, 6, 30))["g1_gains"] == "4.00"


def test_BF_D23_special_dividend_is_reported_apart_with_its_franking() -> None:
    j = _journal(("DDD", 200, "9", date(2026, 11, 2)))
    (b,) = ingest_flex(j, BOOK, _flex("special_dividend.xml"), CaCalendar()).booked
    assert (b.kind, b.cash, b.franked_pct, b.franking_credit) == (
        CaKind.SPECIAL, Decimal(140), Decimal(50), Decimal("30.00"),
    )  # fmt: skip
    tv = j.tax_view(BOOK, date(2027, 6, 30))
    assert (tv["dividends"], tv["specials"], tv["franked_amount"]) == ("0.00", "140.00", "70.00")


def test_BF_D23_demerger_wow_edv_style_adds_a_holding_with_apportioned_cost() -> None:
    """WOW -> EDV (June 2021 style): 1 EDV per WOW; the CSV gives the share of the cost
    base that moves (synthetic 14.07%); IBKR's SO row credits the shares."""
    j = _journal(("WOW", 40, "37", date(2021, 6, 1)))  # cost 1,480 + 6
    cal = _cal()
    r = ingest_flex(j, BOOK, _flex("demerger_wow_edv.xml"), cal)
    (b,) = r.booked
    assert (b.kind, b.code, b.new_code, b.new_shares, b.held) == (
        CaKind.DEMERGER, "WOW", "EDV", 40, 40,
    )  # fmt: skip
    assert b.cost_moved_pct == Decimal("0.1407") and b.tax_class == ""
    assert b.expected_key == "CSV:WOW:2021-06-24:DEMERGER"
    assert j.positions(BOOK) == {"EDV": 40, "WOW": 40}
    cb = j.cost_book(BOOK)
    assert cb.cost["EDV"].quantize(Decimal("0.01")) == Decimal("209.08")  # 1,486 x 14.07%
    assert j.holdings_cost(BOOK) == Decimal("1486.00")  # nothing created or lost
    assert j.tax_view(BOOK, date(2021, 6, 30))["share_receipts"] == ["DEMERGER WOW->EDV 40"]


def test_BF_D23_demerger_without_a_cost_figure_is_provisional_by_value() -> None:
    j = _journal(("WOW", 40, "37", date(2021, 6, 1)))
    px = {"WOW": Decimal("31.10")}
    (b,) = ingest_flex(j, BOOK, _flex("demerger_wow_edv.xml"), CaCalendar(), px).booked
    assert b.tax_class == "PROVISIONAL"
    assert b.cost_moved_pct == (Decimal(214) / (Decimal("31.10") * 40 + 214)).quantize(
        Decimal("0.000001")
    )
    assert "PROVISIONAL" in describe(b)


def test_BF_D25_code_change_with_a_share_ratio_from_flex() -> None:
    """OLD -> NEW, 1 for 10, 5 shares' fraction paid in cash: the journal carries 100
    NEW (cost kept), the cash in lieu is booked, the change is PROPOSED with its ratio
    for the owner to confirm, and a broker on either code reconciles."""
    j = _journal(("OLD", 1005, "0.10", date(2026, 11, 2)))
    cost0, cash0 = j.holdings_cost(BOOK), j.cash(BOOK)
    r = ingest_flex(j, BOOK, _flex("code_change_ratio.xml"), CaCalendar())
    assert r.identity == ("OLD -> NEW ratio 0.1",)
    rec = j.identity_records()["OLD"]
    assert (rec["status"], rec["rule"], Decimal(str(rec["ratio"]))) == (
        "PROPOSED",
        "FLEX",
        Decimal("0.1"),
    )
    assert j.positions(BOOK) == {"NEW": 100}
    assert j.cash(BOOK) == cash0 + Decimal("0.45")
    assert j.holdings_cost(BOOK) == cost0
    for broker in ({"NEW": 100}, {"OLD": 1005}):
        assert reconcile(j.positions(BOOK), j.cash(BOOK), j.map_codes(broker), j.cash(BOOK)).ok
    assert ingest_flex(j, BOOK, _flex("code_change_ratio.xml"), CaCalendar()).identity == ()


def test_BF_D25_rename_from_flex_without_vendor_link() -> None:
    j = _journal(("PTM", 500, "0.70", date(2026, 11, 2)))
    r = ingest_flex(j, BOOK, _flex("rename_ptm_l1g.xml"), CaCalendar())
    assert r.identity == ("PTM -> L1G ratio 1",)
    assert j.positions(BOOK) == {"L1G": 500}
    assert j.identity_ratios() == {"PTM": ("L1G", Decimal(1))}


def test_BF_D23_reconciliation_matches_pending_events_and_halts_on_the_rest() -> None:
    j = _journal(("AAA", 100, "10", date(2026, 11, 10)), ("WOW", 40, "37", date(2026, 11, 10)))
    cal = CaCalendar.merged(
        vendor_events([("AAA", date(2026, 11, 18), Decimal("0.55"), date(2026, 11, 25))]),
        [CaEvent("CSV:WOW:2026-11-24:DEMERGER", CaKind.DEMERGER, "WOW", date(2026, 11, 24),
                 date(2026, 11, 30), new_code="EDV", ratio=Decimal(1), source="CSV")],
    )  # fmt: skip
    pos, cash = j.positions(BOOK), j.cash(BOOK)
    pend = pending_expectations(j, BOOK, cal, date(2026, 12, 1))
    assert {p.key for p in pend} == {"VENDOR:AAA:2026-11-18", "CSV:WOW:2026-11-24:DEMERGER"}
    brk_pos = {**pos, "EDV": 40}
    r = reconcile(pos, cash, brk_pos, cash + 55, pending=pend)
    assert r.ok and len(r.explained) == 2  # dividend and demerged shares, before Flex
    assert not reconcile(pos, cash, brk_pos, cash + 55).ok  # without the calendar: halts
    assert not reconcile(pos, cash, brk_pos, cash + 65, pending=pend).ok  # A$10 unexplained
    assert not reconcile(pos, cash, {**pos, "EDV": 45}, cash, pending=pend).ok  # wrong count
    late = pending_expectations(j, BOOK, cal, date(2027, 1, 20))  # beyond pay date + grace
    assert not reconcile(pos, cash, pos, cash + 55, pending=late).ok
    ingest_flex(j, BOOK, _flex("cash_dividend.xml"), cal)  # IBKR's record arrives
    assert "VENDOR:AAA:2026-11-18" not in {
        p.key for p in pending_expectations(j, BOOK, cal, date(2026, 12, 1))
    }
    assert reconcile(j.positions(BOOK), j.cash(BOOK), pos, cash + 55).ok


def test_BF_D23_simulated_books_follow_the_calendar_on_the_ex_date() -> None:
    """In specie (synthetic XYZ -> CHD, 1 per 4, A$2.00 a share of which A$0.50
    capital, fully franked): shares at their value, dividend part income, capital part
    off the parent's cost base. A vendor dividend: cash on the ex-date."""
    j = _journal(("XYZ", 100, "8", date(2026, 11, 2)), ("AAA", 10, "10", date(2026, 11, 2)))
    cal = _cal(("AAA", date(2026, 11, 23), "0.25"))
    cost0, cash0 = j.holdings_cost(BOOK), j.cash(BOOK)
    got = book_calendar_day(j, [BOOK], cal.on(date(2026, 11, 23)))
    by = {b.code: b for _, b in got}
    x = by["XYZ"]
    assert (x.kind, x.new_code, x.new_shares, x.child_cost) == (
        CaKind.IN_SPECIE, "CHD", 25, Decimal("200.00"),
    )  # fmt: skip
    assert (x.income, x.cost_reduction, x.franking_credit) == (
        Decimal("150.00"), Decimal("50.00"), Decimal("64.29"),
    )  # fmt: skip
    assert by["AAA"].cash == Decimal("2.50") and by["AAA"].franked_pct is None
    assert j.positions(BOOK) == {"AAA": 10, "CHD": 25, "XYZ": 100}
    assert j.cash(BOOK) == cash0 + Decimal("2.50")
    assert j.holdings_cost(BOOK) == cost0 - 50 + 200
    assert book_calendar_day(j, [BOOK], cal.on(date(2026, 11, 23))) == []  # once only
    tv = j.tax_view(BOOK, date(2027, 6, 30))
    assert tv["franking_not_counted"] == "2.50"  # the vendor gives no franking


def test_BF_D23_entitlement_is_the_holding_before_the_ex_date() -> None:
    j = _journal(("AAA", 100, "10", date(2026, 11, 10)))
    j.add_fill(
        FillRecord("S1", None, BOOK, "AAA", Side.SELL, 100, Decimal(11), Decimal(6),
                   datetime(2026, 11, 18, 5, 10, tzinfo=UTC))
    )  # fmt: skip
    assert j.held_at(BOOK, "AAA", date(2026, 11, 18)) == 100  # sold on the ex-date: entitled
    assert j.held_at(BOOK, "AAA", date(2026, 11, 19)) == 0


def test_BF_D23_csv_ratios_and_kinds_from_the_record_notes() -> None:
    assert ratio_from_note("1 WDS per 5.5340 BHP held at record date", "BHP", "WDS") == (
        Decimal(1) / Decimal("5.5340"), False,
    )  # fmt: skip
    assert ratio_from_note("record 30 Jan. 7.2021 MYR per PMV.", "PMV", "MYR") == (
        Decimal("7.2021"), False,
    )  # fmt: skip
    assert ratio_from_note("~0.25 GMD per SBM (final ratio)", "SBM", "GMD") == (
        Decimal("0.25"), True,
    )  # fmt: skip
    assert ratio_from_note("Confirmed: 1 TLC per 1 TAH, ex 24 May", "TAH", "TLC")[0] == 1
    assert parse_ratio("1:10") == Decimal("0.1") and parse_ratio("2") == 2
    with pytest.raises(CaError):
        parse_ratio("0:5")
    evs = {e.code: e for e in load_ca_csv(FX / "corporate_actions.csv")}
    assert evs["WOW"].kind is CaKind.DEMERGER and evs["WOW"].ratio == 1
    assert evs["XYZ"].ratio == Decimal("0.25") and evs["XYZ"].franked_pct == 100
    assert evs["CCC"].kind is CaKind.CAPITAL_RETURN


def test_BF_D23_record_corporate_actions_csv_loads_when_mounted() -> None:
    import os

    p = os.environ.get("TRADER_BF_CA_CSV")
    if not p or not Path(p).is_file():
        pytest.skip("TRADER_BF_CA_CSV (the record's CORPORATE_ACTIONS.csv) not mounted")
    evs = {e.code: e for e in load_ca_csv(Path(p))}
    assert evs["BHP"].kind is CaKind.IN_SPECIE and evs["BHP"].new_code == "WDS"
    assert evs["TAH"].kind is CaKind.DEMERGER and evs["TAH"].ratio == 1
    assert evs["PMV"].ratio == Decimal("7.2021")
