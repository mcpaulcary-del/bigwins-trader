"""BF-D23..D25 through the app: the simulated books follow the calendar on the ex-date,
the paper book follows IBKR's own records (Flex), reconciliation and L13 tolerate the
gap between them and halt on anything else; demerged shares are sold at the next
month-end decision unless on the list; owner-confirmed code changes with a ratio."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal

import pytest

from tests.test_bf_app import CHAT, D0, DAYS, SEED, _app, _closes, _panel
from trader.approval import Incoming, totp
from trader.bf_app import BfApp, at, dry_run, mock_auction, owner_approves_all
from trader.broker.mock_gateway import MockGateway
from trader.corporate_actions import CaCalendar, CaEvent, CaKind
from trader.data.flex import FlexStatement, parse_statements
from trader.lines.emg2 import emg2_list
from trader.risk import SafetyLevel

X = DAYS[6]  # ex-date
PAY = DAYS[8]  # IBKR credits the paper book
LATE = DAYS[9]  # IBKR's Flex record of PAY arrives


def _xml(account: str, d: date, cash: str = "", actions: str = "") -> bytes:
    ds = d.strftime("%Y%m%d")
    return f"""<FlexQueryResponse queryName="t" type="AF"><FlexStatements count="1">
<FlexStatement accountId="{account}" fromDate="{ds}" toDate="{ds}" period="" whenGenerated="{ds};200000">
<CashTransactions>{cash}</CashTransactions><CorporateActions>{actions}</CorporateActions>
</FlexStatement></FlexStatements></FlexQueryResponse>""".encode()


def _started() -> tuple[BfApp, MockGateway, str]:
    app, gw, _ = _app(D0)
    dry_run(app, DAYS[:6], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    held = sorted(set(app.j.positions(app.s.book)) & set(app.j.positions(app.s.sim_book)))
    return app, gw, held[0]


def _cal(*evs: CaEvent) -> Callable[[frozenset[str], date, date], CaCalendar]:
    return lambda codes, a, b: CaCalendar.merged([], [e for e in evs if a <= e.ex_date <= b])


def _credit(gw: MockGateway, day: date, fn: Callable[[], None]) -> Callable[[date], None]:
    auction = mock_auction(gw, _closes)

    def run(d: date) -> None:
        auction(d)
        if d == day:
            fn()

    return run


def _flex(day: date, body: bytes) -> Callable[[date], Sequence[FlexStatement]]:
    sts = parse_statements(body)
    return lambda d: sts if d >= day else []


def test_BF_D23_dividend_twin_on_ex_date_paper_from_flex_reconciles_every_day() -> None:
    app, gw, e = _started()
    q_book, q_sim = app.j.positions(app.s.book)[e], app.j.positions(app.s.sim_book)[e]
    ev = CaEvent(f"CSV:{e}:{X}:DIVIDEND", CaKind.DIVIDEND, e, X, PAY, Decimal("0.05"),
                 franked_pct=Decimal(100), source="CSV")  # fmt: skip
    app.ca_source = _cal(ev)
    amt = Decimal("0.05") * q_book
    cash_xml = (
        f'<CashTransaction currency="AUD" symbol="{e}" transactionID="T1" type="Dividends" '
        f'amount="{amt}" settleDate="{PAY:%Y%m%d}" description="{e}(AU0) CASH DIVIDEND AUD '
        f'0.05 PER SHARE - FULLY FRANKED"/>'
    )
    app.flex = _flex(LATE, _xml("DU1234567", PAY, cash=cash_xml))
    cash0 = app.j.cash(app.s.book)

    def pay() -> None:
        gw.cash += float(amt)

    dry_run(app, DAYS[6:11], {}, owner_approves_all(app, SEED), _credit(gw, PAY, pay))
    sim_b = [b for b in app.j.ca_bookings(app.s.sim_book) if b.code == e]
    assert sim_b and sim_b[0].cash == Decimal("0.05") * q_sim and sim_b[0].ex_date == X
    (b,) = [b for b in app.j.ca_bookings(app.s.book) if b.code == e]
    assert (b.kind, b.cash, b.expected_key) == (CaKind.DIVIDEND, amt, ev.key)
    assert b.franked_pct == Decimal(100)
    recs = dict(app.j.job_records(f"recon:{app.s.book}:"))
    assert all(r["ok"] for r in recs.values())
    assert recs[f"recon:{app.s.book}:{PAY}"]["explained"]  # matched before Flex
    assert not recs[f"recon:{app.s.book}:{LATE}"]["explained"]  # booked: nothing pending
    assert app.j.safety_level() is SafetyLevel.NORMAL
    assert app.j.cash(app.s.book) - cash0 == amt + sum(  # dividend + the fills since
        ((-f.price * f.qty if f.side.value == "BUY" else f.price * f.qty) - f.commission
         for f in app.j.fills(app.s.book) if f.executed_at.date() >= X),
        Decimal(0),
    )  # fmt: skip
    assert app.sim.cash == app.j.cash(app.s.sim_book)


def test_BF_D23_unexplained_cash_still_halts() -> None:
    app, gw, e = _started()
    app.ca_source = _cal()

    def stray() -> None:
        gw.cash += 12.34

    dry_run(app, DAYS[6:9], {}, owner_approves_all(app, SEED), _credit(gw, PAY, stray))
    assert app.j.safety_level() is SafetyLevel.HALTED_INTEGRITY


def test_BF_D23_D24_demerger_shares_twin_at_ex_paper_at_credit_then_sold_at_month_end() -> None:
    """WOW -> EDV style: 1 child per parent share; the twin gets the shares on the
    ex-date, the paper book when IBKR credits them (reconciliation and L13 explained,
    no halt) and books them from Flex; at the next month-end decision both books sell
    the child unless it is on T (BF-D24: rule L4 unchanged)."""
    app, gw, e = _started()
    p = _panel(DAYS[5])
    held = set(app.j.positions(app.s.book)) | set(app.j.positions(app.s.sim_book))
    tv = {c: float(p.tv[-1, j]) for j, c in enumerate(p.entities)}
    child = min((c for c in p.entities if c not in held and tv[c] == tv[c]), key=lambda c: tv[c])
    ev = CaEvent(f"CSV:{e}:{X}:DEMERGER", CaKind.DEMERGER, e, X, PAY, new_code=child,
                 ratio=Decimal(1), cost_base_pct=Decimal("0.2"), source="CSV")  # fmt: skip
    app.ca_source = _cal(ev)
    q = app.j.positions(app.s.book)[e]
    act = (
        f'<CorporateAction currency="AUD" assetCategory="STK" symbol="{child}" '
        f'reportDate="{PAY:%Y%m%d}" description="{e}(AU0) SPINOFF  1 FOR 1 ({child}, KID)" '
        f'quantity="{q}" amount="0" value="0" type="SO" transactionID="C1" actionID="A1"/>'
    )
    app.flex = _flex(LATE, _xml("DU1234567", PAY, actions=act))

    def credit() -> None:
        gw.pos[child] = float(q)

    m1, m2 = [d for d in DAYS[6:-1] if app.is_month_end(d)][:2]
    days = [d for d in DAYS[6:] if d <= app.next_session(m2)]
    dry_run(app, days, {}, owner_approves_all(app, SEED), _credit(gw, PAY, credit))
    assert app.j.safety_level() is SafetyLevel.NORMAL
    assert app.j.safety_level(app.s.sim_book) is SafetyLevel.NORMAL
    sim_b = [b for b in app.j.ca_bookings(app.s.sim_book) if b.new_code == child]
    (bk_b,) = [b for b in app.j.ca_bookings(app.s.book) if b.new_code == child]
    assert sim_b[0].ex_date == X and bk_b.expected_key == ev.key and bk_b.new_shares == q
    assert bk_b.cost_moved_pct == Decimal("0.2")
    recs = dict(app.j.job_records(f"recon:{app.s.book}:"))
    assert all(r["ok"] for r in recs.values())
    assert any(child in x for x in recs[f"recon:{app.s.book}:{PAY}"]["explained"])
    # the start month's month-end is skipped for the broker book (L6): its next is m2
    for book, m_end in ((app.s.sim_book, m1), (app.s.book, m2)):
        targets = set(emg2_list(_panel(m_end)).targets)
        sells = [it for it, _ in app.j.intents_of(f"{book}-{m_end}-R") if it.entity == child]
        assert child not in targets  # the least liquid name: never on T
        if child in targets:
            assert not sells  # on the list: kept
        else:
            assert sells and sells[0].reason == "EMG2_OFF_LIST" and sells[0].side.value == "SELL"


def _owner(app: BfApp, d: date, text: str, hhmm: str = "12:00") -> str:
    t = at(d, hhmm)
    app.transport_inject(Incoming(CHAT, text.replace("<code>", totp(SEED, t)), t))
    app.job_tick(d, t)
    return str([t for _, t in app.transport.outbox][-1])  # type: ignore[attr-defined]


def test_BF_D25_unlinked_rename_with_ratio_confirmed_by_owner_reconciles() -> None:
    """The vendor does not link OLD -> NEW (no A7 alias): the owner maps it with a
    ratio by /idmap (2FA). The journal carries NEW at the ratio; a broker still on OLD,
    or already on NEW at the new count, reconciles; nothing halts."""
    app, gw, e = _started()
    q = app.j.positions(app.s.book)[e]
    assert _owner(app, X, f"/idmap {e} ZZNEW 1:2 000000").startswith("refused")  # bad code
    assert _owner(app, X, "/idmap NOPE ZZNEW <code>", "12:01").startswith("refused")  # not held
    assert _owner(app, X, f"/idmap {e} ZZNEW 1:2 <code>", "12:02").endswith("ratio 0.5 confirmed")
    assert app.j.positions(app.s.book)["ZZNEW"] == q // 2
    assert e not in app.j.positions(app.s.book)
    t = at(X, "16:30")
    app.job_reconcile(X, t)  # broker still shows the old code and count
    gw.pos["ZZNEW"] = float(q // 2)
    del gw.pos[e]
    app.job_reconcile(DAYS[7], at(DAYS[7], "16:30"))  # broker renamed
    recs = dict(app.j.job_records(f"recon:{app.s.book}:"))
    assert recs[f"recon:{app.s.book}:{X}"]["ok"] and recs[f"recon:{app.s.book}:{DAYS[7]}"]["ok"]
    assert app.j.safety_level() is SafetyLevel.NORMAL
    assert _owner(app, X, f"/idmap {e} OTHER <code>", "12:03").startswith("refused")


def test_BF_D25_flex_code_change_with_ratio_is_proposed_and_reconciles() -> None:
    app, gw, e = _started()
    q = app.j.positions(app.s.book)[e]
    acts = "".join(
        f'<CorporateAction currency="AUD" assetCategory="STK" symbol="{s}" '
        f'reportDate="{X:%Y%m%d}" description="{e}(AU0) SPLIT 1 FOR 4 (NWC, NEWCO, AU1)" '
        f'quantity="{n}" amount="0" value="0" type="RS" transactionID="I{i}" actionID="A9"/>'
        for i, (s, n) in enumerate(((e, -q), ("NWC", q // 4)))
    )
    app.flex = _flex(X, _xml("DU1234567", X, actions=acts))
    gw.pos["NWC"] = float(q // 4)
    del gw.pos[e]
    app.job_reconcile(X, at(X, "16:30"))
    assert app.j.identity_records()[e]["status"] == "PROPOSED"
    assert app.j.positions(app.s.book)["NWC"] == q // 4
    assert dict(app.j.job_records(f"recon:{app.s.book}:{X}"))[f"recon:{app.s.book}:{X}"]["ok"]
    assert any(f"/idmap {e} NWC" in t for _, t in app.transport.outbox)  # type: ignore[attr-defined]
    assert _owner(app, X, f"/idmap {e} NWC <code>", "17:00").endswith("ratio 0.25 confirmed")


@pytest.mark.parametrize(
    ("ratio", "words"), [(Decimal("0.1"), "1 FOR 10"), (Decimal(2), "2 FOR 1")]
)
def test_BF_D26_vendor_split_twin_and_random_twins_on_the_date_paper_from_flex(
    ratio: Decimal, words: str
) -> None:
    """A 1-for-10 consolidation and a 2-for-1 split of a held name: the twin and every
    random twin holding it change count on the split date (cost kept); the paper book
    when IBKR's Flex record arrives; reconciliation explains the broker's new count in
    between and matches after; nothing halts."""
    app, gw, _ = _app(D0, random_twins=3)
    dry_run(app, DAYS[:6], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    books = [app.s.book, app.s.sim_book, *(n for n, _, _, _ in app.rnd)]
    pos = {b: app.j.positions(b) for b in books}
    both = set(pos[app.s.book]) & set(pos[app.s.sim_book])
    e = max(sorted(both), key=lambda c: sum(c in pos[b] for b in books))
    ev = CaEvent(f"VENDOR:SPLIT:{e}:{X}", CaKind.SPLIT, e, X, ratio=ratio, source="VENDOR")
    app.ca_source = _cal(ev)
    scale = {e: 1 / ratio}

    def closes(d: date) -> dict[str, Decimal]:  # the vendor's raw closes after the split
        c = _closes(d)
        return {k: (v * scale.get(k, 1) if d >= X else v) for k, v in c.items()}

    marks0 = app.marks
    app.closes = closes
    app.marks = lambda d: {k: (v * scale.get(k, 1) if d >= X else v) for k, v in marks0(d).items()}
    cost0 = {b: app.j.cost_book(b).cost.get(e) for b in books}
    q = pos[app.s.book][e]
    new = int(q * ratio)
    acts = "".join(
        f'<CorporateAction currency="AUD" assetCategory="STK" symbol="{e}" '
        f'reportDate="{X:%Y%m%d}" description="{e}(AU0) SPLIT {words} ({e}, CO, AU1)" '
        f'quantity="{n}" amount="0" value="0" type="RS" transactionID="S{i}" actionID="SP1"/>'
        for i, n in enumerate((-q, new))
    )
    app.flex = _flex(LATE, _xml("DU1234567", X, actions=acts))

    def at_ibkr() -> None:  # IBKR applies it on the split date, its Flex record comes later
        gw.pos[e] = float(new)

    dry_run(app, DAYS[6:11], {}, owner_approves_all(app, SEED), _credit(gw, X, at_ibkr))
    assert app.j.safety_level() is SafetyLevel.NORMAL  # no L11 fall: valued at the new count
    for b in books:
        if e not in pos[b]:
            continue
        (x,) = [x for x in app.j.ca_bookings(b) if x.code == e and x.kind is CaKind.SPLIT]
        assert x.qty_change == int(pos[b][e] * ratio) - pos[b][e] and x.ex_date == X
        assert app.j.positions(b)[e] == int(pos[b][e] * ratio)
        assert app.j.cost_book(b).cost[e] == cost0[b]  # total cost unchanged
    assert sum(e in pos[b] for b in books) >= 3  # paper, twin and a random twin at least
    assert app.sim.holdings[e] == app.j.positions(app.s.sim_book)[e]
    for name, _, _, rb in app.rnd:
        assert rb.holdings.get(e, 0) == app.j.positions(name).get(e, 0)
    (bk,) = [x for x in app.j.ca_bookings(app.s.book) if x.code == e]
    assert bk.expected_key == ev.key and bk.source == "FLEX"
    recs = dict(app.j.job_records(f"recon:{app.s.book}:"))
    assert all(r["ok"] for r in recs.values())
    assert any(e in x for x in recs[f"recon:{app.s.book}:{X}"]["explained"])
    assert not recs[f"recon:{app.s.book}:{LATE}"]["explained"]
