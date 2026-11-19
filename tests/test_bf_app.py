"""BF3/BF4: scheduler jobs, canary flow, simulated twin, approval timeout, dry-run harness."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
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


def test_BW_RSK_29_owner_loss_rule_nav_below_6000_pauses_buys_keeps_holdings_until_resume() -> None:
    """Owner decision (19 Nov 2026): account value below A$6,000 -> HALTED_BUYS and a
    high-priority page; holdings kept (nothing sold by the halt), registered sells still
    go, buys are not sent; only the owner's /resume re-enables buying. A breach that
    continues after /resume is the owner's call (not re-latched); a new breach is."""
    from trader.approval import Incoming
    from trader.orders import OrderBatch, Side, client_order_id

    app, gw, tr = _app(D0)
    dry_run(app, DAYS[:4], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    book = app.s.book
    held = app.j.positions(book)
    cash = app.j.cash(book)
    assert len(held) >= 15 and app.j.safety_level() is SafetyLevel.NORMAL
    day = DAYS[4]
    px = dict(app.marks(day))
    worth = sum((px[e] * q for e, q in held.items()), Decimal(0))

    def at_value(v: str) -> Callable[[date], dict[str, Decimal]]:
        f = (Decimal(v) - cash) / worth
        return lambda d: {e: px[e] * f for e in held}

    def high() -> int:
        return sum("PAGE HIGH PRIORITY" in t for _, t in tr.outbox)

    batches_before = app.j.batches_of(book)
    days = iter(DAYS[5:])

    def report(v: str) -> date:
        d = next(days)
        app.marks = at_value(v)
        app.job_report(d, at(d, "22:45"))
        return d

    for v in ("9000", "8000", "7100", "6300", "6000.00"):  # no day falls 12% or more
        report(v)
    assert app.j.safety_level() is SafetyLevel.NORMAL and high() == 0  # A$6,000: review only
    report("5990.00")
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS and high() == 1
    page = next(t for _, t in tr.outbox if "PAGE HIGH PRIORITY" in t)
    assert "holdings are kept" in page and "/resume" in page
    assert app.j.positions(book) == held and app.j.batches_of(book) == batches_before
    report("5900")  # still below: latched, no second page
    last = report("6500")  # recovery does not re-arm by itself
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS and high() == 1
    # under the halt a registered sell is sent and a buy is not
    x = next(days)
    sell_e = sorted(held)[0]
    buy_e = next(e for e in sorted(px) if e not in held and px[e] > 1)
    ref_s, ref_b = px[sell_e], px[buy_e]
    from trader.orders import OrderIntent, OrderType, round_to_step

    def intent(e: str, side: Side, qty: int, ref: Decimal, seq: int) -> OrderIntent:
        band = Decimal("1.03") if side is Side.BUY else Decimal("0.97")
        return OrderIntent(
            client_order_id(book, last, e, side), f"{book}-{last}-X", seq, "EMG2_18",
            book, last, e, side, qty, OrderType.LOC, ref, round_to_step(ref * band, side),
            "T", tv_med20=Decimal(10**9), prev_close=ref,
        )  # fmt: skip

    its = (
        intent(sell_e, Side.SELL, held[sell_e], ref_s, 1),
        intent(buy_e, Side.BUY, int(Decimal(520) / ref_b) + 1, ref_b, 2),
    )
    batch = OrderBatch(f"{book}-{last}-X", book, last, its, (), "d" * 64)
    ctx = app._ctx(book, app.broker, x, last, at(last, "22:20"), False)
    app.ex.plan(batch, "auto", x, ctx)
    gw.placed.clear()
    app.job_submit(x, at(x, "15:45"))
    assert {o.orderRef for _, o in gw.placed} == {its[0].client_order_id}
    st = {it.client_order_id: s for it, s in app.j.intents_of(batch.batch_id)}
    assert st[its[1].client_order_id] == Status.RISK_REJECTED

    def resume(d: date) -> None:
        t = at(d, "16:00")
        app.transport_inject(Incoming(CHAT, f"/resume {totp(SEED, t)}", t))
        app.job_tick(d, t)

    resume(x)  # only the owner's command re-enables buying
    assert app.j.safety_level() is SafetyLevel.NORMAL
    report("6400")
    d = report("5950")  # a new breach latches again
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS and high() == 2
    resume(d)  # the owner resumes while still below the floor: honoured
    report("5800")
    assert app.j.safety_level() is SafetyLevel.NORMAL and high() == 2
