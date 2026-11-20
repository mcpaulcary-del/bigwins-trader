"""BF3/BF4 piece 2: the full dry run on the record's data (30 Oct and 18 Nov 2026)
against the mock gateway, the canary flow (L6) and the L11 drill on the same data.

Runs where ``TRADER_FORWARD_STORE`` points at the record's EODHD store (vendor data
stays off the repository, DAT-15); the LIC and ETP lists come from
``TRADER_BF_LIC_LIST`` / ``TRADER_BF_ETP_LIST`` as in ``trader-bf dry-run``. The
panels are built once per module and shared by every scenario.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from tests.bf_support import asx_sessions, real_config
from trader.approval import Incoming, totp
from trader.bf_app import (
    DAY_JOBS,
    OWNER_TICKS,
    BfApp,
    at,
    dry_run,
    mock_auction,
    owner_approves_all,
)
from trader.bf_dryrun import Providers, forward_store_dry_run, mock_app, store_providers
from trader.broker.mock_gateway import MockGateway
from trader.journal import Status
from trader.orders import Side
from trader.report import PAPER_BANNER
from trader.risk import SafetyLevel

FWD = os.environ.get("TRADER_FORWARD_STORE")
pytestmark = pytest.mark.skipif(not FWD, reason="set TRADER_FORWARD_STORE to the record's store")

START, END = date(2026, 10, 30), date(2026, 11, 18)
NOV2, NOV3 = date(2026, 11, 2), date(2026, 11, 3)
BOOK = "EMG2_18_PAPER"
Rec = tuple[Any, list[date], Providers]


@pytest.fixture(scope="module")
def rec() -> Rec:
    assert FWD
    cfg, sess = real_config(), asx_sessions()
    return cfg, sess, store_providers(cfg, Path(FWD), sess)


def _days(sess: Sequence[date], a: date = START, b: date = END) -> list[date]:
    return [d for d in sess if a <= d <= b]


def _app(r: Rec, **kw: Any) -> tuple[BfApp, MockGateway, str]:
    """The scenarios below run without the 100 random twins (the full replay has them)
    and, like it, with the L15 band-trend switch off: they drill the registered EMG2-18
    path, which on this data the switch would replace by the fund (BF-D28; the switch on
    the same data: ``test_BF_D28_record_replay_switch_on_holds_the_fund``), and with the
    registered sell rule L4: the drills need the 18 Nov sells, which C6 (BF-D35) would not
    make three weeks after the start (C6 on the same data: ``tests/test_bf_c6.py``)."""
    kw.setdefault("random_twins", 0)
    kw.setdefault("band_trend", False)
    kw.setdefault("sell_rule", "L4")
    cfg, sess, prov = r
    return mock_app(cfg, prov, sess, START, **kw)


def _outbox(app: BfApp) -> list[str]:
    return [t for _, t in getattr(app.transport, "outbox", [])]


def test_BF_dry_run_replays_30_oct_and_18_nov_record_data(rec: Rec) -> None:
    """End to end on recorded data: start decision 30 Oct (canary 2 Nov, the other 17 on
    3 Nov after the canary reconciled), every session to 18 Nov with the closing auction
    at the recorded close, a forced regular decision on 18 Nov for 19 Nov. Every buy is
    >= A$500 at the reference and <= A$800 at its limit; the book reconciles to the unit
    and the cent every session; the L13 comparison is explained every day; one PAPER
    report a session; no page, no halt."""
    cfg, sess, prov = rec
    days = _days(sess)
    summ, app, tr = forward_store_dry_run(
        cfg, Path(str(FWD)), sess, days, {START: "S", END: "R"}, providers=prov, band_trend=False
    )
    assert summ.batches[f"{BOOK}-2026-10-30-C"] == {Status.FILLED: 1}
    assert app.j.batch(f"{BOOK}-2026-10-30-C")["execution_date"] == NOV2  # type: ignore[index]
    assert app.j.batch(f"{BOOK}-2026-10-30-S")["execution_date"] == NOV3  # type: ignore[index]
    start_buys = [it for b in ("C", "S") for it, _ in app.j.intents_of(f"{BOOK}-2026-10-30-{b}")]
    assert len(start_buys) == 18
    assert summ.batches[f"{BOOK}-2026-10-30-S"].get(Status.FILLED, 0) >= 14
    buys = [
        it
        for bid, _ in app.j.batches_of(BOOK)
        for it, _ in app.j.intents_of(bid)
        if it.side is Side.BUY
    ]
    assert buys and all(it.value_at_ref >= 500 and it.value_at_limit <= 800 for it in buys)
    sim_start = app.j.intents_of("EMG2_18_SIM-2026-10-30-S")
    assert {it.entity for it, _ in sim_start} == {it.entity for it in start_buys}
    assert app.j.batch(f"{BOOK}-2026-11-18-R")["execution_date"] == date(2026, 11, 19)  # type: ignore[index]
    assert summ.safety == "NORMAL"
    # BF-D19: HGO (held) stops after 13 Nov and continues as KAN: one page, carried as KAN
    assert [p[:46] for p in summ.pages] == ["PAGE code change 2026-11-16: HGO has no close "]
    assert "carried as KAN" in summ.pages[0] and "/idmap HGO KAN <code>" in summ.pages[0]
    idr = app.j.identity_records()["HGO"]
    assert (idr["new_code"], idr["status"], idr["rule"]) == ("KAN", "PROPOSED", "A7b")
    assert summ.positions["KAN"] == summ.sim_positions["KAN"] == 458
    assert "HGO" not in summ.positions and "HGO" not in summ.sim_positions
    held_hgo = [
        b
        for b in (BOOK, "EMG2_18_SIM", *(n for n, *_ in app.rnd))
        if any(f.entity == "HGO" for f in app.j.fills(b))
    ]
    assert BOOK in held_hgo and len(held_hgo) > 2
    kan_buys = [
        it
        for b in held_hgo
        for it, _ in app.j.intents_of_book(b)
        if it.entity == "KAN" and it.side is Side.BUY
    ]
    assert not kan_buys  # never a second holding of the same company
    assert summ.recon == {str(d): True for d in days}  # to the unit and the cent, each day
    assert summ.positions == app.j.map_codes(app.broker.positions())
    assert abs(summ.cash - summ.broker_cash) < Decimal("0.01")
    assert set(summ.l13_notes) == {"2026-10-30", "2026-11-18"}
    assert not any("L13 sim/broker holdings differ" in t for _, t in tr.outbox)
    reports = [t for _, t in tr.outbox if t.startswith(PAPER_BANNER)]
    assert len(reports) == len(days)
    assert any(t.startswith("Decision 2026-10-30") and "LIC list" in t for _, t in tr.outbox)
    # HGO's last mark (1.045) is no longer used: KAN's close values the holding
    assert not any("no mark for HGO" in t for t in reports)
    assert "KAN" in reports[-1] and "code change HGO -> KAN not confirmed" in reports[-1]
    # BF-D20 (class rule v2, LICs left out of the ranks): the start buys RG1 in place of AMI
    assert "RG1" in {it.entity for it in start_buys} and "AMI" not in summ.positions
    assert reports[-1].count("Value A$10022.36") == 1
    assert not any("no price" in t for t in reports)
    # BF-D18 golden: the 100 random twins on the record data (18 Nov 2026); re-pinned for
    # BF-D20 (the class fix changes band C, so the twins' draws and the twin's book move)
    assert len(app.rnd) == 100 and app.rnd[0][:2] == ("EMG2_18_RND_s001", 8550001)
    rnd = dict(app.j.job_records("rnd:2026-11-18"))["rnd:2026-11-18"]
    assert rnd["sim"] == "9887.8987" and rnd["percentile"] == "49.0"
    assert app.twin_rank(END) == Decimal("49.0")
    digest = hashlib.sha256(json.dumps(rnd["values"]).encode()).hexdigest()
    assert digest == "168fa642af3098d030230c4f5c470c9dc415612d3837a6215d7382d9a4a45a05"
    assert "Simulated twin at the 49.0 percentile of 100 random twins" in reports[-1]


def _auction_without(
    gw: MockGateway, prov: Providers, drop: Callable[[date], set[str]]
) -> Callable[[date], None]:
    def run(day: date) -> None:
        closes = {e: float(c) for e, c in prov[1](day).items() if e not in drop(day)}
        gw.auction(closes, at(day, "16:12"))

    return run


def test_L6_record_canary_unfilled_is_carried_once_then_the_start_stops(rec: Rec) -> None:
    """The canary does not fill on 2 Nov nor, carried once (L7), on 3 Nov: the start
    stops and pages; the other 17 are never planned; the twin is unaffected (L13)."""
    _, sess, prov = rec
    app, gw, seed = _app(rec)
    canary: set[str] = set()
    owner = owner_approves_all(app, seed)
    dry_run(app, [START], {}, owner, mock_auction(gw, prov[1]))
    canary |= {it.entity for it, _ in app.j.intents_of(f"{BOOK}-2026-10-30-C")}
    assert len(canary) == 1
    drop = _auction_without(gw, prov, lambda d: canary if d in (NOV2, NOV3) else set())
    summ = dry_run(app, _days(sess, NOV2, date(2026, 11, 5)), {}, owner, drop)
    x = app.j.intents_of(f"{BOOK}-{NOV2}-X")
    assert len(x) == 1 and "CANARY" in x[0][0].flags and x[0][1] == Status.EXPIRED
    assert app.j.batch(f"{BOOK}-2026-10-30-S") is None and summ.positions == {}
    assert any("canary did not fill; the start stops" in p for p in summ.pages)
    assert len(summ.sim_positions) == 18 and summ.safety == "NORMAL"


def test_L6_record_canary_filled_but_reconciliation_broken_the_17_wait(rec: Rec) -> None:
    """The canary fills on 2 Nov but the broker's cash differs from the ledger: the
    reconciliation breaks (HALTED_INTEGRITY, paged) and the other 17 are not planned.
    When the books agree again the 17 are planned, and wait for the owner's re-arm."""
    _, sess, prov = rec
    app, gw, seed = _app(rec)
    owner = owner_approves_all(app, seed)
    auction = mock_auction(gw, prov[1])

    def broken(day: date) -> None:
        auction(day)
        if day == NOV2:
            gw.cash += 5.0  # a cash movement the ledger does not know

    dry_run(app, [START, NOV2, NOV3], {}, owner, broken)
    assert app.j.intents_of(f"{BOOK}-2026-10-30-C")[0][1] == Status.FILLED
    assert app.j.safety_level() is SafetyLevel.HALTED_INTEGRITY
    assert app.j.batch(f"{BOOK}-2026-10-30-S") is None
    assert any("HALTED_INTEGRITY" in t and "CASH" in t for t in _outbox(app))
    gw.cash -= 5.0  # the cause is found and corrected at the broker
    nov4 = date(2026, 11, 4)
    dry_run(app, [nov4], {}, owner, auction)
    s = app.j.batch(f"{BOOK}-2026-10-30-S")
    assert s is not None and s["execution_date"] == date(2026, 11, 5)
    assert app.j.safety_level() is SafetyLevel.HALTED_INTEGRITY  # owner re-arms (2FA)


def _run_jobs(app: BfApp, day: date, jobs: Sequence[str], seed: str, gw: MockGateway,
              prov: Providers) -> None:  # fmt: skip
    """``run_day`` for the named jobs only (a process that stops or starts mid-day)."""
    owner = owner_approves_all(app, seed)
    for hhmm, name in DAY_JOBS:
        if name not in jobs:
            continue
        now = at(day, hhmm)
        if name in OWNER_TICKS:
            for k, text in enumerate(owner(day, hhmm)):
                app.transport_inject(Incoming(1, text, now + timedelta(seconds=31 * k)))
        if name == "collect":
            mock_auction(gw, prov[1])(day)
        assert app.run_job(name, day, now)


def test_L6_record_restart_between_canary_and_the_17_uses_the_journal_only(
    rec: Rec, tmp_path: Path
) -> None:
    """The process stops on 2 Nov after the canary filled (16:20) and before the
    reconciliation (16:30). A new process on the same journal and broker reconciles,
    plans the other 17 for 3 Nov and sends them: nothing lived only in memory."""
    _, sess, prov = rec
    jp = str(tmp_path / "journal.sqlite3")
    app, gw, seed = _app(rec, journal_path=jp)
    dry_run(app, [START], {}, owner_approves_all(app, seed), mock_auction(gw, prov[1]))
    names = [n for _, n in DAY_JOBS]
    cut = names.index("reconcile")
    _run_jobs(app, NOV2, names[:cut], seed, gw, prov)
    assert app.j.intents_of(f"{BOOK}-2026-10-30-C")[0][1] == Status.FILLED
    del app
    app2, _, _ = _app(rec, journal_path=jp, gw=gw, seed=seed)
    _run_jobs(app2, NOV2, names[cut:], seed, gw, prov)
    s = app2.j.batch(f"{BOOK}-2026-10-30-S")
    assert s is not None and s["execution_date"] == NOV3
    summ = dry_run(app2, _days(sess, NOV3, date(2026, 11, 5)), {}, owner_approves_all(app2, seed),
                   mock_auction(gw, prov[1]))  # fmt: skip
    rest = app2.j.intents_of(f"{BOOK}-2026-10-30-S")
    assert len(rest) == 17 and sum(st == Status.FILLED for _, st in rest) >= 14
    assert summ.safety == "NORMAL" and all(summ.recon.values())
    assert summ.positions == app2.j.map_codes(app2.broker.positions())
    # the twin was rebuilt from the journal too and holds the same names
    assert set(summ.sim_positions) >= set(summ.positions)


def test_L11_record_drill_marks_scaled_below_6000_buys_stop_sells_go_resume(rec: Rec) -> None:
    """L11 drill on the replay: from 5 Nov the marks are scaled so the book walks down
    to A$5,900 (no day falls 12%). Stage 1 pages with the integrity check, stage 2
    pauses buys (the daily report shows HALTED_BUYS); at the 18 Nov decision the staged
    test runs: with the random-twin percentile unknown it fails safe and buys stay
    paused, so on 19 Nov the decision's sells are sent and its buy is not; the owner's
    /resume re-enables buying."""
    _, sess, prov = rec
    app, gw, seed = _app(rec)
    owner = owner_approves_all(app, seed)
    auction = mock_auction(gw, prov[1])
    dry_run(app, _days(sess, START, date(2026, 11, 4)), {}, owner, auction)
    real = app.marks
    path = ["9300", "8500", "7700", "6900", "6200", "5900"]
    walk = dict(zip(_days(sess, date(2026, 11, 5), END), path + ["5900"] * 20, strict=False))

    def scaled(d: date) -> dict[str, Decimal]:
        px = dict(real(d))
        if d not in walk:
            return px
        held = app.j.positions(BOOK)
        cash = app.j.cash(BOOK)
        last = {e: px.get(e) or Decimal(app.j.job_records("marks:")[-1][1].get(e, "0"))
                for e in held}  # fmt: skip
        worth = sum((last[e] * q for e, q in held.items()), Decimal(0))
        f = (Decimal(walk[d]) - cash) / worth
        return {**px, **{e: last[e] * f for e in held}}

    app.marks = scaled
    summ = dry_run(app, _days(sess, date(2026, 11, 5), END), {END: "R"}, owner, auction)
    out = _outbox(app)
    assert any("L11 stage 1" in t and "Integrity check passed" in t for t in out)
    assert any("L11 stage 2" in t and "resume automatically at the 2026-11-30" in t for t in out)
    assert summ.safety == "HALTED_BUYS"
    reports = [t for t in out if t.startswith(PAPER_BANNER)]
    assert any("safety HALTED_BUYS" in t and "L11 stage 2" in t for t in reports)
    assert any(f"L11 {END}: buys stay paused" in t and "(b) twin percentile unknown" in t
               for t in out)  # fmt: skip
    assert all(summ.recon.values()) and summ.positions == app.j.map_codes(app.broker.positions())
    # 19 Nov: the 18 Nov decision's sells go, its buys are refused by the breaker
    nov19 = date(2026, 11, 19)
    gw.placed.clear()
    app.job_tick(nov19, at(nov19, "10:30"))
    for msg in owner(nov19, "10:30"):
        app.transport_inject(Incoming(1, msg, at(nov19, "10:30")))
    app.job_tick(nov19, at(nov19, "10:31"))
    app.job_submit(nov19, at(nov19, "15:45"))
    batch = app.j.intents_of(f"{BOOK}-{END}-R")
    sent = {o.orderRef for _, o in gw.placed}
    sells = {it.client_order_id for it, _ in batch if it.side is Side.SELL}
    buys = {it.client_order_id: st for it, st in batch if it.side is Side.BUY}
    assert sells and sells <= sent and not (set(buys) & sent)
    assert set(buys.values()) <= {Status.RISK_REJECTED}
    t = at(nov19, "16:00")
    app.transport_inject(Incoming(1, f"/resume {totp(seed, t)}", t))
    app.job_tick(nov19, t)
    assert app.j.safety_level() is SafetyLevel.NORMAL


def test_BF_D28_record_replay_switch_on_holds_the_fund(rec: Rec) -> None:
    """L15 on the record's data (config as shipped, switch on): on 30 Oct 2026 the band
    index is below its 10-month average, so the start is "state: FUND": the canary is the
    one A200 order (2 Nov, approved by the owner, paged above A$800), no share is bought,
    the twin and the random twins hold A200 too; the forced 18 Nov decision is FUND again
    (no top-up: cash under 10%); reconciled to the cent every session; every report says
    "state: FUND"."""
    cfg, sess, prov = rec
    days = _days(sess)
    assert cfg.band_trend is not None and cfg.band_trend.enabled
    summ, app, tr = forward_store_dry_run(
        cfg, Path(str(FWD)), sess, days, {START: "S", END: "R"}, providers=prov, random_twins=3
    )
    can = app.j.intents_of(f"{BOOK}-2026-10-30-C")
    assert [(it.entity, it.flags) for it, _ in can] == [("A200", ("CANARY", "FUND"))]
    assert summ.batches[f"{BOOK}-2026-10-30-C"] == {Status.FILLED: 1}
    assert app.j.batch(f"{BOOK}-2026-10-30-C")["execution_date"] == NOV2  # type: ignore[index]
    assert app.j.batch(f"{BOOK}-2026-10-30-S") is None
    assert 9000 < can[0][0].value_at_limit <= 9950
    for book in (BOOK, "EMG2_18_SIM", *(n for n, *_ in app.rnd)):
        assert list(app.j.positions(book)) == ["A200"], book
    assert not app.j.intents_of(f"{BOOK}-2026-11-18-R") and not app.j.intents_of(
        f"{BOOK}-2026-11-18-B"
    )
    bt = dict(app.j.job_records("bt:"))
    assert {k: r["state"] for k, r in bt.items()} == {
        "bt:2026-10-30": "FUND",
        "bt:2026-11-18": "FUND",
    }
    assert summ.safety == "NORMAL" and summ.recon == {str(d): True for d in days}
    assert summ.positions == app.j.map_codes(app.broker.positions())
    assert [p for p in summ.pages if "above the L10" not in p] == []
    reports = [t for _, t in tr.outbox if t.startswith(PAPER_BANNER)]
    assert len(reports) == len(days) and all("state: FUND" in t for t in reports)
    assert any(t.startswith("Decision 2026-10-30") and "state: FUND" in t for _, t in tr.outbox)
