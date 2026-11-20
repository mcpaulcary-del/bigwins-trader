"""BF-D34 (report 98): on a FUND switch day a share that cannot be sold (halted, no
trade, limit not met) does not hold up the fund: the books buy the fund with the cash
they have, offer the leftover share again every session it trades, and put its
proceeds into the fund at once (not at the next month-end). The paper book, the
simulated twin and the random twins do exactly the same."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import numpy as np
import pytest

from tests.test_bf_band_trend import DAYS, FUND, SEED, _closes, _panel
from tests.test_bf_paper_dry_run import _always_fund, _app
from trader.bf_app import dry_run, marks_from_panels, mock_auction, owner_approves_all
from trader.journal import Status
from trader.lines.emg2 import BT_FUND_SWEEP, BT_LEFTOVER_SELL
from trader.orders import OrderIntent, OrderType, Side
from trader.panel import PricePanel
from trader.risk import RiskContext, RiskLimits, SafetyLevel, check_intents

D0, SW = DAYS[0], DAYS[3]  # start EMG2 (forced); the switch decision (the rule's FUND)
HALT = frozenset(DAYS[4:9])  # the held share does not trade from the switch session on
BOOKS = ("EMG2_18_PAPER", "EMG2_18_SIM", "EMG2_18_RND_s001", "EMG2_18_RND_s002")


def _halted(victims: set[str]) -> tuple[Any, Any]:
    def closes(d: date) -> dict[str, Decimal]:
        c = _closes(d)
        if d in HALT:
            for v in victims:
                c.pop(v, None)
        return c

    def panel(d: date) -> PricePanel:
        p = _panel(d)
        close = p.close.copy()
        for v in victims:
            j = p.entities.index(v)
            for i, x in enumerate(p.dates):
                if x in HALT:
                    close[i, j] = np.nan
        return PricePanel(as_of=p.as_of, dates=p.dates, entities=p.entities, close=close,
                          ret=p.ret, tv=p.tv, sec_class=p.sec_class)  # fmt: skip

    return closes, panel


def test_BF_D34_halted_holding_on_a_switch_day(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trader.bf_app.band_trend", _always_fund)
    app, gw, tr = _app(forced=((D0, "EMG2"), (SW, "REAL")))
    owner = owner_approves_all(app, SEED)
    dry_run(app, DAYS[:4], {}, owner, mock_auction(gw, _closes))  # to the switch decision
    held = {b: dict(app.j.positions(b)) for b in BOOKS}
    # one share of each book stops trading from the switch session (the paper book's and
    # the twin's is the same share; each random twin's is one of its own)
    vic = {b: next(e for e in sorted(h) if e != FUND) for b, h in held.items()}
    vic["EMG2_18_SIM"] = vic["EMG2_18_PAPER"]
    assert vic["EMG2_18_PAPER"] in held["EMG2_18_SIM"]
    closes, panel = _halted(set(vic.values()))
    app.closes, app.panels, app.marks = closes, panel, marks_from_panels(panel)
    summ = dry_run(app, DAYS[4:16], {}, owner, mock_auction(gw, closes))
    for book in BOOKS:
        sw = app.j.intents_of(f"{book}-{SW}-B")
        # the switch sold the shares and bought the fund with the cash it had
        victim = vic[book]
        assert any(it.entity == victim and it.side is Side.SELL for it, _ in sw), book
        assert [it.entity for it, _ in sw if it.side is Side.BUY] == [FUND], book
        fills = app.j.fills(book)
        first_fund = min(f.executed_at.date() for f in fills if f.entity == FUND)
        assert first_fund <= DAYS[5], (book, first_fund)  # not held back by the halted share
        # the leftover was sold once it traded again, its cash went into the fund
        out = [f for f in fills if f.entity == victim and f.side is Side.SELL]
        assert out and min(f.executed_at.date() for f in out) > max(HALT), book
        last_sale = max(f.executed_at.date() for f in out)
        later_fund = [f for f in fills if f.entity == FUND and f.executed_at.date() > last_sale]
        assert later_fund, book  # swept into the fund within days, not at the month-end
        assert later_fund[0].executed_at.date() <= DAYS[13], book
        pos = app.j.positions(book)
        assert list(pos) == [FUND], (book, pos)
        assert app.j.cash(book) < Decimal(600), (book, app.j.cash(book))  # invested
    # the sweep's own orders exist in every book (same rule, same days)
    reasons = {b: {it.reason for it, _ in app.j.intents_of_book(b)} for b in BOOKS}
    assert all(BT_FUND_SWEEP in r for r in reasons.values()), reasons
    paper = app.j.intents_of_book("EMG2_18_PAPER")
    assert any(it.entity == vic["EMG2_18_PAPER"] and it.side is Side.SELL for it, _ in paper)
    assert BT_LEFTOVER_SELL in {it.reason for b in BOOKS for it, _ in app.j.intents_of_book(b)}
    assert summ.safety == "NORMAL" and all(summ.recon.values())
    assert summ.positions == app.broker.positions()
    assert any(t.startswith("Fund sweep") and "BF-D34" in t for _, t in tr.outbox)
    assert all(st != Status.RISK_REJECTED for it, st in paper if it.reason == BT_FUND_SWEEP)


def test_BF_D34_no_sweep_in_emg2_state_or_without_a_switch_sale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("trader.bf_app.band_trend", _always_fund)
    app, gw, _ = _app(forced=((D0, "EMG2"),))
    dry_run(app, DAYS[:3], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    assert not app.j.job_records("sweep:")  # state EMG2: nothing to sweep
    assert all(not b.endswith("-F") for b, _ in app.j.batches_of(app.s.book))


def _fund_buy(value: Decimal) -> OrderIntent:
    q = int(value / Decimal(100))
    return OrderIntent("c", "b", 1, "EMG2_18", "B", DAYS[0], FUND, Side.BUY, q, OrderType.LOC,
                       Decimal(100), Decimal(103), BT_FUND_SWEEP, tv_med20=Decimal(10**9),
                       prev_close=Decimal(100), flags=("FUND",))  # fmt: skip


def test_BF_D34_fund_buy_is_capped_on_the_fund_not_on_shares_being_sold() -> None:
    from datetime import UTC, datetime

    def ctx(fund_cost: Decimal | None) -> RiskContext:
        return RiskContext(now=datetime(2024, 1, 15, 4, tzinfo=UTC), session=DAYS[0],
                           expected_data_date=DAYS[0], data_as_of=DAYS[0], start_day=True, safety=SafetyLevel.NORMAL,
                           positions={"XYZ": 100}, settled_cash=Decimal(9500),
                           holdings_cost=Decimal(1500), fund_cost=fund_cost)  # fmt: skip

    it = _fund_buy(Decimal(9000))  # A$9,270 at the limit; with the share's cost > A$10,000
    blocked = check_intents([it], ctx(None), RiskLimits())
    assert "CAPITAL_CAP" in blocked.results[0].reasons
    ok = check_intents([it], ctx(Decimal(0)), RiskLimits())
    assert ok.results[0].sendable
    over = check_intents([it], ctx(Decimal(1000)), RiskLimits())  # the fund itself: capped
    assert "CAPITAL_CAP" in over.results[0].reasons
