"""BF-D23 / BF-D25: dividends, capital returns, specials, demergers, in-specie receipts
and code changes with a share ratio, booked into the journal from IBKR's Flex records
(broker books) or from the vendor + record calendar (simulated books), and matched by
reconciliation while IBKR's records are still on their way. Synthetic Flex fixtures
(``tests/fixtures/flex_ca``): one per event type."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from trader.ca_book import book_calendar_day, describe, ingest_flex, pending_expectations
from trader.corporate_actions import (
    CaCalendar,
    CaError,
    CaEvent,
    CaKind,
    kind_of,
    load_ca_csv,
    parse_ratio,
    ratio_from_note,
    vendor_events,
    vendor_split_events,
)
from trader.data.flex import parse_statements
from trader.data.forward_store import split_ratio
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
    assert b.franking_credit == Decimal(0)  # tax F7: no rate assumed (enter from statement)
    assert b.expected_key == "VENDOR:AAA:2026-11-18"
    assert r.skipped == ("Deposits/Withdrawals 9100001",)  # deposits are booked by hand
    assert j.cash(BOOK) == cash0 + 55
    assert ingest_flex(j, BOOK, _flex("cash_dividend.xml"), cal).booked == ()  # once only
    assert j.cash(BOOK) == cash0 + 55
    tv = j.tax_view(BOOK, date(2027, 6, 30))
    assert (tv["dividends"], tv["franking_credits"], tv["capital_returns"]) == (
        "55.00", "0.00", "0.00",  # tax F7
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
        CaKind.SPECIAL, Decimal(140), Decimal(50), Decimal(0),
    )  # fmt: skip  # tax F7: the credit comes from the statement
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
        Decimal("150.00"), Decimal("50.00"), Decimal(0),
    )  # fmt: skip  # tax F7: no franking rate in the CSV row
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


# ---------------------------------------------------------------------------
# BF-D26: splits and consolidations
# ---------------------------------------------------------------------------

SX = date(2026, 12, 3)  # split / consolidation date


def _avg(j: Journal, code: str) -> Decimal:
    cb = j.cost_book(BOOK)
    return cb.cost[code] / cb.qty[code]


def test_BF_D26_BW_UNI_20_vendor_consolidation_1_for_10_and_split_2_for_1_simulated_books() -> None:
    """The twin's (and every random twin's) holdings on the split date: count x ratio,
    cost per share / ratio, total cost unchanged; booked once; nothing held, nothing."""
    j = _journal(("CNS", 1005, "0.20", date(2026, 11, 2)), ("SPL", 40, "12.50", date(2026, 11, 2)))
    j.add_cash("RND1", "DEPOSIT", Decimal(10000), "t", datetime(2020, 1, 1, tzinfo=UTC))
    j.add_fill(FillRecord("R1", None, "RND1", "SPL", Side.BUY, 7, Decimal(10), Decimal(6),
                          datetime(2026, 11, 2, 5, 10, tzinfo=UTC)))  # fmt: skip
    cal = CaCalendar.merged(
        vendor_split_events(
            [("CNS", SX, Decimal("0.1")), ("SPL", SX, Decimal(2)), ("ZZZ", SX, Decimal(2))]
        ),
        [],
    )
    cost0, cash0 = j.holdings_cost(BOOK), j.cash(BOOK)
    avg_c, avg_s = _avg(j, "CNS"), _avg(j, "SPL")
    assert j.positions(BOOK, before=datetime(2026, 12, 2, tzinfo=UTC)) == {"CNS": 1005, "SPL": 40}
    got = book_calendar_day(j, [BOOK, "RND1"], cal.on(SX))
    assert sorted((bk, b.code, b.held, b.qty_change) for bk, b in got) == [
        (BOOK, "CNS", 1005, -905), (BOOK, "SPL", 40, 40), ("RND1", "SPL", 7, 7),
    ]  # fmt: skip
    assert j.positions(BOOK) == {"CNS": 100, "SPL": 80} and j.positions("RND1") == {"SPL": 14}
    assert j.holdings_cost(BOOK) == cost0 and j.cash(BOOK) == cash0
    assert _avg(j, "CNS") == avg_c * 1005 / 100  # 1-for-10: fraction dropped, cost kept
    assert _avg(j, "SPL") == avg_s / 2
    assert describe(got[0][1]).startswith("SPLIT CNS: 1005 -> 100 shares (x0.1)")
    assert book_calendar_day(j, [BOOK, "RND1"], cal.on(SX)) == []  # once only
    # after the split date the entitlement is the new count
    assert j.held_at(BOOK, "SPL", date(2026, 12, 4)) == 80


def test_BF_D26_vendor_split_rows_parse_and_merge_with_the_record_csv() -> None:
    assert split_ratio("2.000000/1.000000") == 2 and split_ratio("1.000000/10.000000") == Decimal(
        "0.1"
    )
    assert split_ratio("bad") is None and split_ratio("0/1") is None
    assert vendor_split_events([("A", SX, Decimal(1))]) == []  # no change: no event
    spl = vendor_split_events([("A", SX, Decimal(2))])
    div = vendor_events([("A", SX, Decimal("0.10"), None)])
    csv_div = CaEvent("CSV:A:div", CaKind.SPECIAL, "A", SX, per_share=Decimal(1), source="CSV")
    csv_spl = CaEvent("CSV:A:spl", CaKind.SPLIT, "A", SX, ratio=Decimal(3), source="CSV")
    # a CSV special replaces the vendor's dividend, not its split
    assert {e.key for e in CaCalendar.merged([*spl, *div], [csv_div]).events} == {
        "VENDOR:SPLIT:A:2026-12-03", "CSV:A:div",
    }  # fmt: skip
    # a CSV split (e.g. the right ratio) replaces the vendor's split, not its dividend
    assert {e.key for e in CaCalendar.merged([*spl, *div], [csv_spl]).events} == {
        "VENDOR:A:2026-12-03", "CSV:A:spl",
    }  # fmt: skip
    assert kind_of("Consolidation") is CaKind.SPLIT and kind_of("share split") is CaKind.SPLIT


@pytest.mark.parametrize(
    ("code", "qty", "ratio", "fixture", "new"),
    [("CNS", 1005, Decimal("0.1"), "consolidation_1_for_10.xml", 100),
     ("SPL", 40, Decimal(2), "split_2_for_1.xml", 80)],
)  # fmt: skip
def test_BF_D26_paper_book_split_from_flex_reconciles_before_and_after(
    code: str, qty: int, ratio: Decimal, fixture: str, new: int
) -> None:
    """The broker shows the new count on the split date; IBKR's Flex record comes later.
    In between the calendar split explains the difference (not a break); a wrong count
    still halts; the Flex booking settles it with the same count and cost rule as the
    simulated books."""
    j = _journal((code, qty, "1.00", date(2026, 11, 2)))
    cal = CaCalendar.merged(vendor_split_events([(code, SX, ratio)]), [])
    pos, cash, cost0 = j.positions(BOOK), j.cash(BOOK), j.holdings_cost(BOOK)
    pend = pending_expectations(j, BOOK, cal, SX)
    assert [p.shares for p in pend] == [{code: new - qty}]
    r = reconcile(pos, cash, {code: new}, cash, pending=pend)
    assert r.ok and r.explained
    assert not reconcile(pos, cash, {code: new + 5}, cash, pending=pend).ok  # wrong count
    assert not reconcile(pos, cash, {code: new}, cash).ok  # no calendar: halts
    res = ingest_flex(j, BOOK, _flex(fixture), cal)
    (b,) = res.booked
    assert (b.kind, b.qty_change, b.ratio, b.expected_key, b.ex_date) == (
        CaKind.SPLIT, new - qty, ratio, f"VENDOR:SPLIT:{code}:{SX}", SX,
    )  # fmt: skip
    assert res.identity == ()  # same code: not a code change
    assert j.positions(BOOK) == {code: new} and j.holdings_cost(BOOK) == cost0
    assert pending_expectations(j, BOOK, cal, SX + timedelta(days=1)) == []  # settled
    assert reconcile(j.positions(BOOK), j.cash(BOOK), {code: new}, j.cash(BOOK)).ok
    # the simulated book's booking of the same event gives the same count and cost
    k = _journal((code, qty, "1.00", date(2026, 11, 2)))
    book_calendar_day(k, [BOOK], cal.on(SX))
    assert k.positions(BOOK) == j.positions(BOOK) and k.holdings_cost(BOOK) == cost0


def test_BF_D26_forward_split_shown_as_extra_shares_only() -> None:
    j = _journal(("SPL", 40, "12.50", date(2026, 11, 2)))
    cost0 = j.holdings_cost(BOOK)
    body = (FX / "split_2_for_1.xml").read_bytes()
    body = body.replace(b'quantity="-40"', b'quantity="0"').replace(
        b'quantity="80"', b'quantity="40"'
    )
    res = ingest_flex(j, BOOK, parse_statements(body), CaCalendar())
    assert [(b.kind, b.qty_change) for b in res.booked] == [(CaKind.SPLIT, 40)]
    assert j.positions(BOOK) == {"SPL": 80} and j.holdings_cost(BOOK) == cost0
