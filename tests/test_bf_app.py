"""BF3/BF4: scheduler jobs, canary flow, simulated twin, approval timeout, dry-run harness."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pytest

from tests.bf_support import synthetic_panel
from trader.approval import FakeTransport, TotpVerifier, totp
from trader.bf_app import (
    DAY_JOBS,
    AppSettings,
    BfApp,
    at,
    dry_run,
    mock_auction,
    owner_approves_all,
)
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.constants import ASX_TZ
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
DAYS = list(PANEL.dates[270:310])  # 15 Jan - 8 Mar 2024: two month-ends


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
    sim_s = app.j.intents_of(f"EMG2_18_SIM-{D0}-S")
    assert len(sim_s) == 18 and {st for _, st in sim_s} == {Status.FILLED}
    assert {it.entity for it, _ in sim_s} == {
        it.entity for b in ("C", "S") for it, _ in app.j.intents_of(f"EMG2_18_PAPER-{D0}-{b}")
    }
    # month-end decisions: the start month's month-end is skipped for the broker book
    # (L6), not for the twin; the next month-end runs for both
    m1, m2 = (d for d in DAYS[:-1] if app.is_month_end(d))
    assert m1.month == D0.month and m2.month == D0.month + 1
    assert app.j.batch(f"EMG2_18_PAPER-{m1}-R") is None
    assert app.j.batch(f"EMG2_18_SIM-{m1}-R") is not None
    assert app.j.batch(f"EMG2_18_PAPER-{m2}-R") is not None
    assert app.j.batch(f"EMG2_18_SIM-{m2}-R") is not None
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
    assert [n for _, n in jobs][:6] == ["tick", "tick", "remind", "tick", "submit", "collect"]
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
    """End to end on recorded data against the mock gateway: start decision 30 Oct
    (canary 2 Nov, the other 17 on 3 Nov after the canary reconciled), every session to
    18 Nov with the closing auction at the recorded close, a regular decision on 18 Nov
    for 19 Nov; reconciled to the cent every day; no page, no halt."""
    from pathlib import Path

    from tests.bf_support import asx_sessions, real_config
    from trader.bf_dryrun import forward_store_dry_run

    assert FWD
    cfg, sess = real_config(), asx_sessions()
    start, end = date(2026, 10, 30), date(2026, 11, 18)
    days = [d for d in sess if start <= d <= end]
    summ, app, tr = forward_store_dry_run(cfg, Path(FWD), sess, days, {start: "S", end: "R"})
    assert summ.batches["EMG2_18_PAPER-2026-10-30-C"] == {Status.FILLED: 1}
    assert app.j.batch("EMG2_18_PAPER-2026-10-30-C")["execution_date"] == date(2026, 11, 2)  # type: ignore[index]
    assert app.j.batch("EMG2_18_PAPER-2026-10-30-S")["execution_date"] == date(2026, 11, 3)  # type: ignore[index]
    start_buys = [
        it for b in ("C", "S") for it, _ in app.j.intents_of(f"EMG2_18_PAPER-2026-10-30-{b}")
    ]
    assert len(start_buys) == 18 and all(it.value_at_ref >= 500 for it in start_buys)
    assert summ.batches["EMG2_18_PAPER-2026-10-30-S"].get(Status.FILLED, 0) >= 14
    sim_start = app.j.intents_of("EMG2_18_SIM-2026-10-30-S")
    assert {it.entity for it, _ in sim_start} == {it.entity for it in start_buys}
    assert app.j.batch("EMG2_18_PAPER-2026-11-18-R")["execution_date"] == date(2026, 11, 19)  # type: ignore[index]
    assert summ.safety == "NORMAL" and not summ.pages
    assert summ.positions == app.broker.positions()
    assert abs(summ.cash - summ.broker_cash) < Decimal("0.01")
    assert len([t for _, t in tr.outbox if t.startswith(PAPER_BANNER)]) == len(days)
    assert any(t.startswith("Decision 2026-10-30") and "LIC list" in t for _, t in tr.outbox)


# ---------------------------------------------------------------- carry, restart, data


def _auction_without(
    gw: MockGateway,
    drop: Callable[[date], set[str]],
    fix: Callable[[date], dict[str, float]] = lambda d: {},
) -> Callable[[date], None]:
    """The closing auction with no close for the names ``drop(day)`` (their orders
    expire) and the closes ``fix(day)`` set by the test."""

    def run(day: date) -> None:
        closes = {e: float(c) for e, c in _closes(day).items() if e not in drop(day)}
        gw.auction({**closes, **fix(day)}, at(day, "16:12"))

    return run


@pytest.mark.parametrize("misses", [1, 2])
def test_L6_L7_unfilled_canary_is_carried_once_then_the_start_stops(misses: int) -> None:
    app, gw, tr = _app(D0)
    approve = owner_approves_all(app, SEED)
    canary: set[str] = set()  # filled in after the decision

    def drop(day: date) -> set[str]:
        return canary if day in DAYS[1 : 1 + misses] else set()

    dry_run(app, DAYS[:1], {}, approve, mock_auction(gw, _closes))
    canary |= {it.entity for it, _ in app.j.intents_of(f"EMG2_18_PAPER-{D0}-C")}

    def fix(day: date) -> dict[str, float]:  # D+2: the carried canary's limit allows
        hit = misses == 1 and day == DAYS[2]
        return {e: float(_closes(DAYS[1])[e]) for e in canary} if hit else {}

    dry_run(app, DAYS[1:4], {}, approve, _auction_without(gw, drop, fix))
    x = app.j.intents_of(f"EMG2_18_PAPER-{DAYS[1]}-X")
    assert len(x) == 1 and "CANARY" in x[0][0].flags and x[0][0].attempt == 2
    assert app.j.batch(f"EMG2_18_PAPER-{DAYS[1]}-X")["execution_date"] == DAYS[2]  # type: ignore[index]
    rest = app.j.batch(f"EMG2_18_PAPER-{D0}-S")
    if misses == 1:  # carried canary filled on D+2; the other 17 go on D+3
        assert x[0][1] == Status.FILLED
        assert rest is not None and rest["execution_date"] == DAYS[3]
        assert app.j.safety_level() is SafetyLevel.NORMAL
    else:  # a buy is carried once (L7): the start stops and pages
        assert x[0][1] == Status.EXPIRED and rest is None
        assert any("canary did not fill" in t for _, t in tr.outbox)
        assert not app.j.intents_of(f"EMG2_18_PAPER-{DAYS[2]}-X")


def test_L7_unfilled_sell_is_carried_three_sessions_then_paged() -> None:
    app, gw, tr = _app(D0)
    approve = owner_approves_all(app, SEED)
    m2 = [d for d in DAYS[:-1] if app.is_month_end(d)][1]
    k = DAYS.index(m2)
    dry_run(app, DAYS[: k + 1], {}, approve, mock_auction(gw, _closes))
    sells = [it for it, _ in app.j.intents_of(f"EMG2_18_PAPER-{m2}-R") if it.side.value == "SELL"]
    assert sells
    e = sells[0].entity
    dry_run(app, DAYS[k + 1 : k + 6], {}, approve, _auction_without(gw, lambda d: {e}))
    tries = sorted(
        (it.attempt, st) for it, st in app._all_intents(app.s.book) if it.entity == e and it.side.value == "SELL"
    )  # fmt: skip
    assert tries == [
        (1, Status.EXPIRED),
        (2, Status.EXPIRED),
        (3, Status.EXPIRED),
        (4, Status.EXPIRED),
    ]
    assert any("unfilled after 4 sessions" in t and e in t for _, t in tr.outbox)
    assert e in app.j.positions(app.s.book)  # still held: a halt or page never sells by itself


def test_restart_mid_start_continues_from_the_journal() -> None:
    """Nothing the start needs lives only in memory: a new process (new BfApp on the
    same journal and gateway) plans the other start buys after the canary."""
    app, gw, _ = _app(D0)
    approve = owner_approves_all(app, SEED)
    dry_run(app, DAYS[:1], {}, approve, mock_auction(gw, _closes))
    app2 = BfApp(app.s, app.j, app.broker, app.sim, app.transport,
                 TotpVerifier(SecretValue(SEED)), PANEL.dates, _panel, _closes)  # fmt: skip
    dry_run(app2, DAYS[1:3], {}, owner_approves_all(app2, SEED), mock_auction(gw, _closes))
    rest = app2.j.intents_of(f"EMG2_18_PAPER-{D0}-S")
    assert len(rest) == 17 and {st for _, st in rest} <= {Status.FILLED, Status.EXPIRED}


def test_rule14_decision_waits_for_data_then_pages_a_data_block() -> None:
    app, gw, tr = _app(None)
    late = DAYS[0]

    def no_data(day: date) -> PricePanel:
        p = _panel(day)
        if day != late:
            return p
        close = p.close.copy()
        close[-1, :] = np.nan
        return PricePanel(as_of=p.as_of, dates=p.dates, entities=p.entities, close=close,
                          ret=p.ret, tv=p.tv, sec_class=p.sec_class)  # fmt: skip

    app.panels = no_data
    assert app.job_decide(late, at(late, "22:20"), "R") is False  # not done: retried later
    assert not app.j.batches_of(app.s.book)
    assert app.job_decide(late, at(late, "23:45"), "R") is True
    assert not app.j.batches_of(app.s.book)
    assert any("rule 14 data block" in t for _, t in tr.outbox)


def test_scheduler_retries_a_job_that_is_not_done_and_pages_a_failing_one() -> None:
    from trader.scheduler import run_once

    app, _, tr = _app(None)
    day = DAYS[0]
    calls: list[str] = []

    def flaky(d: date, now: datetime) -> bool:
        calls.append("sim")
        return len(calls) > 1

    def boom(d: date, now: datetime) -> None:
        raise RuntimeError("gateway down")

    app.job_sim = flaky  # type: ignore[method-assign,assignment]
    app.job_report = boom  # type: ignore[method-assign,assignment]
    ran = run_once(app, at(day, "22:16"))
    assert not any(k.endswith(":sim") for k in ran)  # not done: not marked, retried
    ran = run_once(app, at(day, "22:50"))
    assert any(k.endswith(":sim") for k in ran) and any(k.endswith(":report") for k in ran)
    assert any("PAGE job report" in t and "gateway down" in t for _, t in tr.outbox)
    assert run_once(app, at(day, "23:00")) == []  # a failed job is not retried blindly


def test_L8_reminder_at_1430_lists_unapproved_orders() -> None:
    app, gw, tr = _app(D0)
    dry_run(app, DAYS[:1], {}, lambda d, t: [], mock_auction(gw, _closes))
    app.job_remind(DAYS[1], at(DAYS[1], "14:30"))
    assert any(t.startswith("Reminder: 1 order(s)") for _, t in tr.outbox)


# ---------------------------------------------------------------- L11 staged loss rule


def _loss_app(
    twin_pct: Decimal | None = Decimal(50), l12: str | None = None
) -> tuple[BfApp, MockGateway, FakeTransport]:
    """A started book (canary + start filled, reconciled) four sessions after D0, with
    the staged test's inputs injected (random-twin percentile, L12 stop)."""
    app, gw, tr = _app(D0)
    app.twin_rank = lambda d: twin_pct
    app.l12_stop = lambda d: l12
    dry_run(app, DAYS[:4], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    assert len(app.j.positions(app.s.book)) >= 15
    assert app.j.safety_level() is SafetyLevel.NORMAL
    return app, gw, tr


class _Marks:
    """Report the book at a chosen value: scale every holding's mark."""

    def __init__(self, app: BfApp) -> None:
        self.app = app
        self.day = DAYS[4]
        self.px = dict(app.marks(self.day))
        self.days = iter(DAYS[5:])

    def walk(self, *vs: str) -> date:
        return [self.report(v) for v in vs][-1]

    def report(self, v: str, d: date | None = None) -> date:
        app = self.app
        held = app.j.positions(app.s.book)
        cash = app.j.cash(app.s.book)
        worth = sum((self.px[e] * q for e, q in held.items()), Decimal(0))
        f = (Decimal(v) - cash) / worth
        app.marks = lambda _d: {e: self.px[e] * f for e in held}
        d = d or next(self.days)
        app.job_report(d, at(d, "22:45"))
        return d


def _high(tr: FakeTransport) -> list[str]:
    return [t for _, t in tr.outbox if "PAGE HIGH PRIORITY" in t]


def _owner(app: BfApp, d: date, text: str, hhmm: str = "16:00") -> None:
    from trader.approval import Incoming

    t = at(d, hhmm)
    app.transport_inject(Incoming(CHAT, text.replace("<code>", totp(SEED, t)), t))
    app.job_tick(d, t)


M2 = next(d for d in DAYS if d.month == D0.month + 1 and DAYS[DAYS.index(d) + 1].month != d.month)


def test_L11_stage1_below_7000_pages_and_runs_the_integrity_check() -> None:
    """Owner staged rule (19 Nov 2026), stage 1: NAV < A$7,000 -> high-priority page and
    an integrity check (live holdings = simulated twin; fills and costs as modelled).
    Buying is not affected; a failed check latches HALTED_INTEGRITY."""
    app, _, tr = _loss_app()
    m = _Marks(app)
    m.walk("9000", "8100", "7200", "7000.00")  # no day falls 12% or more
    assert not _high(tr)  # exactly A$7,000: not below
    m.report("6990")
    page = _high(tr)[-1]
    assert "L11 stage 1" in page and "Integrity check passed" in page
    assert app.j.safety_level() is SafetyLevel.NORMAL
    m.report("6800")  # still in stage 1: no second page
    assert len(_high(tr)) == 1
    m.walk("8000", "7500")
    # a holding of the twin the live book does not have, with no order to explain it
    from trader.journal import FillRecord
    from trader.orders import Side

    app.j.add_fill(FillRecord("x-1", None, app.s.sim_book, "ZZZ", Side.BUY, 10, Decimal(1),
                              Decimal(0), at(DAYS[9], "16:00")))  # fmt: skip
    m.report("6900")
    assert any("Integrity check FAILED" in t and "HOLDING ZZZ" in t for t in _high(tr))
    assert app.j.safety_level() is SafetyLevel.HALTED_INTEGRITY


def test_L11_integrity_check_flags_fills_and_costs_not_as_modelled() -> None:
    from trader.loss_rule import ModelledFill, integrity_breaks
    from trader.orders import Side

    ok = ModelledFill("o1", "AAA", Side.BUY, 100, Decimal("5.00"), Decimal("6.60"), Decimal("5.10"))
    assert integrity_breaks({"AAA": 100}, {"AAA": 100}, (), [ok]) == ()
    bad = [
        ModelledFill("o2", "BBB", Side.BUY, 100, Decimal("5.20"), Decimal("6.60"), Decimal("5.10")),
        ModelledFill(
            "o3", "CCC", Side.SELL, 100, Decimal("4.90"), Decimal("6.60"), Decimal("5.00")
        ),
        ModelledFill("o4", "DDD", Side.BUY, 100, Decimal("5.00"), Decimal("9.99"), Decimal("5.10")),
    ]
    out = integrity_breaks({"AAA": 1, "EEE": 5}, {"AAA": 1}, ("XYZ",), bad)
    assert [o.split()[0] for o in out] == ["HOLDING", "FILL", "FILL", "COST"]
    # partial fills of one order pay the minimum once
    parts = [
        ModelledFill("o5", "FFF", Side.BUY, 50, Decimal("5.00"), Decimal("3.30"), Decimal("5.10")),
        ModelledFill("o5", "FFF", Side.BUY, 50, Decimal("5.00"), Decimal("3.30"), Decimal("5.10")),
    ]
    assert integrity_breaks({}, {}, (), parts) == ()


def test_L11_stage2_below_6000_pauses_buys_sells_go_on_and_resume_automatically_at_month_end() -> (
    None
):
    """Stage 2: NAV < A$6,000 -> HALTED_BUYS (page), holdings kept, sells continue, buys
    refused; at the next month-end decision buying resumes automatically when the
    staged test passes (integrity, twin >= 10th percentile, no L12 stop, no owner stop)."""
    from trader.orders import (
        OrderBatch,
        OrderIntent,
        OrderType,
        Side,
        client_order_id,
        round_to_step,
    )

    app, gw, tr = _loss_app()
    book = app.s.book
    held = app.j.positions(book)
    m = _Marks(app)
    m.walk("9000", "8100", "7200", "6400", "6000.00")  # no day falls 12% or more
    assert app.j.safety_level() is SafetyLevel.NORMAL  # exactly A$6,000: not below
    batches_before = app.j.batches_of(book)
    last = m.report("5990.00")
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    page = _high(tr)[-1]
    assert "L11 stage 2" in page and "sells continue" in page
    assert f"resume automatically at the {M2} decision" in page
    assert app.j.positions(book) == held and app.j.batches_of(book) == batches_before
    m.report("5900")
    m.report("6500")  # recovery alone does not resume before the decision
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    n_high = len(_high(tr))
    # under the pause a sell is sent and a buy is not
    x = DAYS[DAYS.index(last) + 3]
    px = m.px
    sell_e = sorted(held)[0]
    buy_e = next(e for e in sorted(px) if e not in held and px[e] > 1)

    def intent(e: str, side: Side, qty: int, ref: Decimal, seq: int) -> OrderIntent:
        band = Decimal("1.03") if side is Side.BUY else Decimal("0.97")
        return OrderIntent(
            client_order_id(book, last, e, side), f"{book}-{last}-X", seq, "EMG2_18",
            book, last, e, side, qty, OrderType.LOC, ref, round_to_step(ref * band, side),
            "T", tv_med20=Decimal(10**9), prev_close=ref,
        )  # fmt: skip

    its = (
        intent(sell_e, Side.SELL, held[sell_e], px[sell_e], 1),
        intent(buy_e, Side.BUY, int(Decimal(520) / px[buy_e]) + 1, px[buy_e], 2),
    )
    batch = OrderBatch(f"{book}-{last}-X", book, last, its, (), "d" * 64)
    app.ex.plan(batch, "auto", x, app._ctx(book, app.broker, x, last, at(last, "22:20"), False))
    gw.placed.clear()
    app.job_submit(x, at(x, "15:45"))
    assert {o.orderRef for _, o in gw.placed} == {its[0].client_order_id}
    st = {it.client_order_id: s for it, s in app.j.intents_of(batch.batch_id)}
    assert st[its[1].client_order_id] == Status.RISK_REJECTED
    # the month-end decision: the staged test passes -> buys resume with this decision
    app.job_decide(M2, at(M2, "22:20"))
    assert app.j.safety_level() is SafetyLevel.NORMAL
    assert any(t.startswith(f"L11 {M2}: staged test passed") for _, t in tr.outbox)
    assert app.j.batch(f"{book}-{M2}-R") is not None and len(_high(tr)) == n_high
    k = DAYS.index(M2)
    m.report("5900", DAYS[k + 1])  # it had recovered to A$6,500: a new breach, a new episode
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS and len(_high(tr)) == n_high + 1
    m.report("5800", DAYS[k + 2])  # the same breach: no second page
    assert len(_high(tr)) == n_high + 1


@pytest.mark.parametrize(
    ("pct", "l12", "owner", "integrity", "why"),
    [
        (Decimal("9.9"), None, None, False, "(b) twin at the 9.9 percentile"),
        (None, None, None, False, "(b) twin percentile unknown"),
        (Decimal(50), "signal spread t <= -1.0", None, False, "(c) L12 stop rule met"),
        (Decimal(50), None, "/stop", False, "(d) the owner said stop"),
        (Decimal(50), None, None, True, "(a) integrity check failed"),
    ],
)
def test_L11_stage2_stays_paused_when_the_staged_test_fails(
    pct: Decimal | None, l12: str | None, owner: str | None, integrity: bool, why: str
) -> None:
    """Stage 2 resumes automatically UNLESS (a) the integrity check fails, (b) the twin is
    below the 10th percentile of its 100 random twins (or they are not running: fails
    safe), (c) an L12 stop rule is met, (d) the owner says stop."""
    app, _, tr = _loss_app(pct, l12)
    m = _Marks(app)
    d = m.walk("9000", "8100", "7200", "6400", "5900")
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    if owner:
        _owner(app, d, owner)
        assert app.j.safety_level() is SafetyLevel.PAUSED
    if integrity:
        from trader.journal import FillRecord
        from trader.orders import Side

        app.j.add_fill(FillRecord("x-9", None, app.s.sim_book, "ZZZ", Side.BUY, 10,
                                  Decimal(1), Decimal(0), at(d, "16:00")))  # fmt: skip
    app.job_decide(M2, at(M2, "22:20"))
    assert app.j.safety_level() is not SafetyLevel.NORMAL
    page = _high(tr)[-1]
    assert f"L11 {M2}: buys stay paused" in page and why in page
    # the owner can still resume by hand
    _owner(app, DAYS[DAYS.index(M2) + 1], "/resume <code>", "10:30")
    assert app.j.safety_level() is SafetyLevel.NORMAL


def test_L11_stage3_owner_confirms_in_writing_then_buys_resume() -> None:
    """Stage 3: NAV < A$5,000 -> the same test, and the owner must confirm in writing
    (/continue <code>, 2FA) to continue."""
    app, _, tr = _loss_app()
    m = _Marks(app)
    d = m.walk("9000", "8100", "7200", "6400", "5700", "5050", "4990")
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    assert "L11 stage 3" in _high(tr)[-1] and f"/continue <code> before the {M2}" in _high(tr)[-1]
    _owner(app, d, "/continue 000000")
    assert "refused" in tr.outbox[-1][1]
    _owner(app, d, "/continue <code>")
    assert "confirmation recorded" in tr.outbox[-1][1]
    app.job_decide(M2, at(M2, "22:20"))
    assert app.j.safety_level() is SafetyLevel.NORMAL
    assert app.j.batch(f"{app.s.book}-{M2}-W") is None


def test_L11_stage3_without_confirmation_sells_the_book_over_two_decisions() -> None:
    """Stage 3 without the owner's written confirmation by the next decision: the book is
    sold over that decision (half of each holding, rounded up) and the next (the rest).
    Buys stay paused; each sell still goes through approval (L8) and the breaker."""
    app, gw, tr = _loss_app()
    book = app.s.book
    marks = app.marks
    _Marks(app).walk("9000", "8100", "7200", "6400", "5700", "5050", "4900")
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    app.marks = marks
    held = app.j.positions(book)
    dry_run(app, [M2], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    w1 = app.j.intents_of(f"{book}-{M2}-W")
    assert {it.entity: it.qty for it, _ in w1} == {e: (q + 1) // 2 for e, q in held.items()}
    assert all(it.side.value == "SELL" and "L11_WIND_DOWN" in it.flags for it, _ in w1)
    assert app.j.batch(f"{book}-{M2}-R") is None  # the wind-down replaces the decision
    assert any("L11 wind-down" in t for t in _high(tr))
    # the sells go the next session (approved by the owner), the rest at the next month-end
    i = PANEL.dates.index(M2) + 1
    m3 = next(d for d in PANEL.dates[i:] if app.is_month_end(d))
    rest = list(PANEL.dates[i : PANEL.dates.index(m3) + 2])
    summ = dry_run(app, rest, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    w1_st = [st for _, st in app.j.intents_of(f"{book}-{M2}-W")]
    assert w1_st.count(Status.FILLED) >= len(w1) // 2  # an unfilled sell is carried (L7)
    w2 = app.j.intents_of(f"{book}-{m3}-W")
    assert w2 and {it.entity for it, _ in w2} <= set(held)
    assert sum(summ.positions.values()) < sum(held.values()) // 4
    assert summ.pages == [] or all("unfilled" in p or "L11" in p for p in summ.pages)
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS  # buying does not restart
    assert app.j.batch(f"{book}-{m3}-R") is None
    assert app._l11_episode() is None  # closed after the second step


def test_L11_owner_resume_stops_a_wind_down() -> None:
    app, gw, _ = _loss_app()
    marks = app.marks
    _Marks(app).walk("9000", "8100", "7200", "6400", "5700", "5050", "4900")
    app.marks = marks
    dry_run(app, [M2], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    assert app.j.batch(f"{app.s.book}-{M2}-W") is not None
    nxt = DAYS[DAYS.index(M2) + 1]
    _owner(app, nxt, "/resume <code>", "10:30")
    assert app._l11_episode() is None and app.j.safety_level() is SafetyLevel.NORMAL


# ---------------------------------------------------------------- per-book safety (BF-D16)


@pytest.mark.parametrize("cmd", ["/pause", "/kill", "/stop"])
def test_BF_D16_paused_or_killed_paper_book_leaves_the_twin_buying(cmd: str) -> None:
    """The owner's /pause, /kill, /stop (and the paper book's L11 halts) latch the broker
    book only; the simulated twin (L13) follows the registered rules and keeps buying."""
    app, gw, tr = _app(D0)
    first = owner_approves_all(app, SEED)

    def owner(d: date, hhmm: str) -> list[str]:
        return ([cmd] if (d, hhmm) == (D0, "10:30") else []) + list(first(d, hhmm))

    summ = dry_run(app, DAYS[:3], {}, owner, mock_auction(gw, _closes))
    assert app.j.safety_level() is not SafetyLevel.NORMAL
    assert app.j.safety_level(app.s.sim_book) is SafetyLevel.NORMAL
    assert summ.positions == {} and not gw.placed  # the canary buy was never sent
    sim_s = app.j.intents_of(f"EMG2_18_SIM-{D0}-S")
    assert len(sim_s) == 18 and {st for _, st in sim_s} == {Status.FILLED}
    assert len(summ.sim_positions) == 18
    # no L13 integrity break: the paper book's unsent orders explain the difference
    assert not any("L13" in p for p in summ.pages)


def test_BF_D16_twin_latch_does_not_reach_the_broker_book() -> None:
    j = Journal.sqlite()
    j.set_safety(SafetyLevel.HALTED_BUYS, "twin breaker latch", "risk", scope="EMG2_18_SIM")
    assert j.safety_level() is SafetyLevel.NORMAL
    assert j.safety_level("EMG2_18_SIM") is SafetyLevel.HALTED_BUYS
    j.set_safety(SafetyLevel.KILLED, "owner /kill", "telegram:1")
    assert j.safety_level("EMG2_18_SIM") is SafetyLevel.HALTED_BUYS
    assert j.safety_level() is SafetyLevel.KILLED


# ---------------------------------------------------------------- scheduler (piece 1c)


def _drive(
    app: BfApp,
    gw: MockGateway,
    days: list[date],
    owner: dict[tuple[date, str], list[str]] | None = None,
) -> list[str]:
    """Run the real scheduler loop (``run_forever``) on a fake clock: every 10 minutes
    from 09:00 to 23:50 of each day; the mock exchange runs its closing auction at 16:10;
    the owner's messages arrive at the given (day, HH:MM)."""
    from trader.approval import Incoming
    from trader.scheduler import run_forever

    ticks = [at(d, "09:00") + timedelta(minutes=10 * k) for d in days for k in range(90)]
    auction = mock_auction(gw, _closes)
    pos = {"i": 0}
    ran: list[str] = []

    def clock() -> datetime:
        return ticks[pos["i"]]

    def sleep(_: float) -> None:
        pos["i"] += 1
        if pos["i"] >= len(ticks):
            return
        t = ticks[pos["i"]]
        d = t.astimezone(ASX_TZ).date()
        hhmm = t.astimezone(ASX_TZ).strftime("%H:%M")
        if hhmm == "16:10" and app.is_session(d):
            auction(d)
        for k, text in enumerate((owner or {}).get((d, hhmm), [])):
            app.transport_inject(Incoming(CHAT, text, t + timedelta(seconds=31 * k)))

    def stop() -> bool:
        return pos["i"] >= len(ticks)

    orig = app.j.mark_job

    def spy(key: str, detail: Mapping[str, Any] | None = None, at: datetime | None = None) -> None:
        if key.count(":") >= 2 and key[:4].isdigit():
            ran.append(key)
        orig(key, detail, at)

    app.j.mark_job = spy  # type: ignore[method-assign]
    run_forever(app, clock=clock, sleep=sleep, stop=stop)
    return ran


def _month_end_window() -> tuple[date, list[date]]:
    m = next(d for d in DAYS[5:] if PANEL.dates[PANEL.dates.index(d) + 1].month != d.month)
    k = PANEL.dates.index(m)
    return m, list(PANEL.dates[k - 1 : k + 3])


def test_scheduler_month_end_decision_then_order_day_unapproved_orders_expire() -> None:
    """Daily ticks run every session; the EMG2-18 decision runs only at the month-end
    (22:20), its orders are for the next session (the order day); with no /ok by the
    15:20 deadline nothing is sent (never auto-executed), the orders lapse at 15:45, a
    late /ok is refused, and the simulated twin is not held back."""
    app, gw, tr = _app(None)
    m, days = _month_end_window()
    x = days[2]
    late = at(x, "15:30")
    ran = _drive(app, gw, days, {(x, "15:30"): [f"/ok EMG2_18_PAPER-{m}-R all {totp(SEED, late)}"]})
    for d in days:  # every job once per session, in order
        assert [k.split(":", 3)[3] for k in ran if k.startswith(f"{d}:")] == [
            n for _, n in DAY_JOBS
        ]
    assert [b for b, _ in app.j.batches_of(app.s.book)] == [f"EMG2_18_PAPER-{m}-R"]
    assert app.j.batch(f"EMG2_18_PAPER-{m}-R")["execution_date"] == x  # type: ignore[index]
    assert not gw.placed  # never auto-executed
    sts = {st for _, st in app.j.intents_of(f"EMG2_18_PAPER-{m}-R")}
    # L10 (A$4,500 of buys on a normal day) rejects some at plan; the rest lapse unapproved
    assert Status.LAPSED in sts and sts <= {Status.LAPSED, Status.RISK_REJECTED}
    assert any("past the approval deadline (15:20)" in t for _, t in tr.outbox)
    assert any(t.startswith("Reminder:") for _, t in tr.outbox)  # 14:30 on the order day
    assert len(app.j.positions(app.s.sim_book)) >= 5  # the twin bought (auto; L10 A$4,500)


def test_scheduler_order_day_sends_only_approved_orders_once() -> None:
    """The owner approves two orders by number at 11:00 of the order day: exactly those
    two go to the (mock) paper gateway at 15:45, once; the rest lapse."""
    app, gw, _ = _app(None)
    m, days = _month_end_window()
    x = days[2]
    t = at(x, "11:00")
    bid = f"EMG2_18_PAPER-{m}-R"
    owner = {
        (x, "11:00"): [
            f"/ok {bid} 1 {totp(SEED, t)}",
            f"/ok {bid} 2 {totp(SEED, t + timedelta(seconds=31))}",
        ]
    }
    _drive(app, gw, days, owner)
    sts = {it.seq: st for it, st in app.j.intents_of(bid)}
    assert {o.orderRef for _, o in gw.placed} == {
        it.client_order_id for it, _ in app.j.intents_of(bid) if it.seq in (1, 2)
    }
    assert all(
        st in (Status.LAPSED, Status.RISK_REJECTED) for s, st in sts.items() if s not in (1, 2)
    )
    assert sts[1] in (Status.FILLED, Status.EXPIRED) and sts[2] in (Status.FILLED, Status.EXPIRED)


def test_scheduler_non_session_days_only_poll_telegram() -> None:
    from trader.approval import Incoming
    from trader.scheduler import due_jobs, run_once

    app, _, tr = _app(None)
    sat = date(2024, 2, 3)
    assert not app.is_session(sat) and due_jobs(app, at(sat, "23:00")) == []
    app.transport_inject(Incoming(CHAT, "/pause", at(sat, "10:00")))
    assert run_once(app, at(sat, "23:00")) == []
    assert app.j.safety_level() is SafetyLevel.PAUSED
    assert any("PAUSED" in t for _, t in tr.outbox)
