"""BF3/BF4: scheduler jobs, canary flow, simulated twin, approval timeout, dry-run harness."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import numpy as np
import pytest

from tests.bf_support import synthetic_panel
from trader.approval import FakeTransport, TotpVerifier, totp
from trader.bf_app import AppSettings, BfApp, at, dry_run, mock_auction, owner_approves_all
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.journal import Journal, Status
from trader.lines.emg2 import Emg2_20Params
from trader.panel import PricePanel
from trader.report import PAPER_BANNER
from trader.risk import SafetyLevel
from trader.secrets import SecretValue

SEED = "JBSWY3DPEHPK3PXP"
CHAT = 77
PANEL = synthetic_panel(n_rows=330, n_ent=800, seed=7)


def _closes(day: date) -> dict[str, Decimal]:
    k = PANEL.dates.index(day)
    return {e: Decimal(repr(round(float(c), 3))) for e, c in zip(PANEL.entities, PANEL.close[k], strict=True)
            if not np.isnan(c)}  # fmt: skip


def _panel(day: date) -> PricePanel:
    # closes rounded to 0.001 so that orders, auction and reports see the same prices
    p = PANEL.truncate(day)
    close = np.round(p.close, 3)
    return PricePanel(as_of=p.as_of, dates=p.dates, entities=p.entities, close=close, ret=p.ret,
                      tv=p.tv * 50, sec_class=p.sec_class)  # fmt: skip


def _app(start: date | None) -> tuple[BfApp, MockGateway, FakeTransport]:
    gw = MockGateway(cash=10000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    j = Journal.sqlite()
    s = AppSettings(chats=frozenset({CHAT}), start_date=start,
                    params=Emg2_20Params(skip_lottery=False))  # fmt: skip
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", Decimal(10000), "paper deposit")
    sim = SimBroker(cash=Decimal(10000), half_spread=s.sim_half_spread)
    tr = FakeTransport()
    app = BfApp(
        s, j, broker, sim, tr, TotpVerifier(SecretValue(SEED)), PANEL.dates, _panel, _closes
    )
    return app, gw, tr


D0 = PANEL.dates[270]
DAYS = list(PANEL.dates[270:300])


def test_BF_dry_run_canary_then_start_then_month_end_reconciled() -> None:
    app, gw, tr = _app(D0)
    summ = dry_run(app, DAYS, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    x1, x2 = PANEL.dates[271], PANEL.dates[272]
    canary = summ.batches[f"EMG2_18_PAPER-{D0}-C"]
    assert canary == {Status.FILLED: 1}  # one canary buy, filled on the first session
    rest = summ.batches[f"EMG2_18_PAPER-{D0}-S"]
    assert rest.get(Status.FILLED, 0) >= 15  # the others, the session after the canary reconciled
    assert app.j.batch(f"EMG2_18_PAPER-{D0}-S")["execution_date"] == x2  # type: ignore[index]
    assert app.j.batch(f"EMG2_18_PAPER-{D0}-C")["execution_date"] == x1  # type: ignore[index]
    # the twin bought its whole start list at once (L13), with the same rules
    assert len(summ.sim_positions) >= 15
    # month-end decisions ran for both books
    month_ends = [d for d in DAYS[:-1] if app.is_month_end(d)]
    assert month_ends and all(
        any(b.startswith(f"EMG2_18_PAPER-{m}-R") for b in summ.batches) for m in month_ends
    )
    # the ledger equals the broker to the unit and the cent every day; nothing paged
    assert summ.safety == SafetyLevel.NORMAL.value and not summ.pages
    assert summ.positions == app.broker.positions()
    assert abs(summ.cash - summ.broker_cash) < Decimal("0.01")
    reports = [t for _, t in tr.outbox if t.startswith(PAPER_BANNER)]
    assert len(reports) == len(DAYS)
    refs = [o.orderRef for _, o in gw.placed]
    assert len(refs) == len(set(refs))  # one broker order per intent


def test_L8_approval_timeout_unapproved_orders_lapse_and_are_never_sent() -> None:
    app, gw, tr = _app(D0)
    dry_run(app, DAYS[:3], {}, lambda d, t: [], mock_auction(gw, _closes))
    assert not gw.placed
    assert {st for _, st in app.j.intents_of(f"EMG2_18_PAPER-{D0}-C")} == {Status.LAPSED}
    assert any("not approved 1" in t for _, t in tr.outbox)
    assert len(app.j.positions("EMG2_18_SIM")) >= 15  # the twin is not held back (as registered)


def test_BW_RSK_30_kill_from_telegram_before_submit_stops_the_day() -> None:
    app, gw, tr = _app(D0)
    approve = owner_approves_all(app, SEED)

    def owner(d: date, hhmm: str) -> list[str]:
        msgs = list(approve(d, hhmm))
        if d == DAYS[1] and hhmm == "14:30":
            msgs.append("/kill")
        return msgs

    dry_run(app, DAYS[:3], {}, owner, mock_auction(gw, _closes))
    assert not gw.placed and app.j.safety_level() is SafetyLevel.KILLED
    assert any("KILLED" in t for _, t in tr.outbox)
    t = at(DAYS[2], "16:00")
    from trader.approval import Incoming

    app.transport_inject(Incoming(CHAT, f"/resume {totp(SEED, t)}", t))
    app.job_tick(DAYS[2], t)
    assert app.j.safety_level() is SafetyLevel.NORMAL


def test_L7_buy_waits_for_settled_funds_and_is_sent_on_a_later_session() -> None:
    """O-2 stand-in: the cash is there but not settled; buys wait (HELD), then go."""
    app, gw, _ = _app(D0)
    approve = owner_approves_all(app, SEED)
    dry_run(app, DAYS[:1], {}, approve, mock_auction(gw, _closes))
    dry_run(app, DAYS[1:2], {}, approve, mock_auction(gw, _closes))  # canary filled
    gw.unsettled = 9000.0
    bid = f"EMG2_18_PAPER-{D0}-S"
    dry_run(app, DAYS[2:3], {}, approve, mock_auction(gw, _closes))
    assert {st for _, st in app.j.intents_of(bid)} == {Status.HELD}
    assert app.j.safety_level() is SafetyLevel.NORMAL  # recon uses total cash
    gw.unsettled = 0.0
    dry_run(app, DAYS[3:4], {}, approve, mock_auction(gw, _closes))
    after = [st for _, st in app.j.intents_of(bid)]
    # sent a session late; a few miss their limit (set off the decision close) and expire
    assert after.count(Status.FILLED) >= 10 and Status.HELD not in after


def test_scheduler_runs_each_job_once_per_session() -> None:
    from trader.scheduler import due_jobs

    app, _, _ = _app(None)
    day = DAYS[0]
    jobs = due_jobs(app, at(day, "16:35"))
    assert [n for _, n in jobs][:6] == ["tick", "tick", "tick", "tick", "submit", "collect"]
    for k, _ in jobs:
        app.j.mark_job(k)
    assert due_jobs(app, at(day, "16:35")) == []
    assert [n for _, n in due_jobs(app, at(day, "23:00"))] == ["sim", "decide", "report"]
    assert due_jobs(app, at(date(2023, 1, 7), "23:00")) == []  # Saturday: no session


@pytest.mark.parametrize("bad", ["U1234567", "F1234567"])
def test_app_never_builds_a_live_broker(bad: str) -> None:
    from trader.broker.base import LiveTradingRefusedError

    with pytest.raises(LiveTradingRefusedError):
        IbkrPaperBroker(IbkrSettings("gw", 4004, 21, bad), ib_factory=MockGateway)


FWD = __import__("os").environ.get("TRADER_FORWARD_STORE")


@pytest.mark.skipif(not FWD, reason="set TRADER_FORWARD_STORE to the record's EODHD store")
def test_BF_dry_run_replays_30_oct_and_18_nov_record_data() -> None:
    """End to end on recorded data: start decision 30 Oct (canary 2 Nov, the rest 3 Nov),
    marks every session to 18 Nov, regular decision 18 Nov planned for 19 Nov; every
    day reconciled to the cent; no page."""
    from pathlib import Path

    import exchange_calendars as xc

    from trader.bf_dryrun import forward_store_dry_run
    from trader.bfast_config import load_bfast_config

    assert FWD
    cfg = load_bfast_config(Path(__file__).resolve().parent.parent / "config" / "bfast.yaml")
    sess = [
        x.date() for x in xc.get_calendar("XASX", start="2022-01-01", end="2026-12-31").sessions
    ]
    start, end = date(2026, 10, 30), date(2026, 11, 18)
    days = [d for d in sess if start <= d <= end]
    summ, app, tr = forward_store_dry_run(cfg, Path(FWD), sess, days, {start: "S", end: "R"})
    assert summ.batches["EMG2_18_PAPER-2026-10-30-C"] == {Status.FILLED: 1}
    assert app.j.batch("EMG2_18_PAPER-2026-10-30-C")["execution_date"] == date(2026, 11, 2)  # type: ignore[index]
    assert app.j.batch("EMG2_18_PAPER-2026-10-30-S")["execution_date"] == date(2026, 11, 3)  # type: ignore[index]
    assert summ.batches["EMG2_18_PAPER-2026-10-30-S"].get(Status.FILLED, 0) >= 14
    assert app.j.batch("EMG2_18_PAPER-2026-11-18-R")["execution_date"] == date(2026, 11, 19)  # type: ignore[index]
    assert summ.safety == "NORMAL" and not summ.pages
    assert abs(summ.cash - summ.broker_cash) < Decimal("0.01")
    assert len([t for _, t in tr.outbox if t.startswith(PAPER_BANNER)]) == len(days)
