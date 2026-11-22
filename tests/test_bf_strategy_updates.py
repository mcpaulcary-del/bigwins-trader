"""BF-D45: strategy versions and updates from the app. Classification of an incoming
update (strategy or app-only), the update mode (immediate / next_decision), the 24-hour
block before a month-end decision, waiting for the close and for working orders, the
rollback target, version stamping, and the out-of-cycle decision after an update going
through the same decision and approval path as a month-end."""

from __future__ import annotations

import runpy
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from tests.test_bf_app import CHAT, D0, DAYS, SEED, _app, _closes
from trader.app_store import (
    IMMEDIATE,
    STRATEGY,
    add_server_job,
    claim_server_job,
    get_state,
    server_job_rows,
)
from trader.approval import Incoming, totp
from trader.bf_app import dry_run, mock_auction, owner_approves_all
from trader.bfast_config import load_bfast_config
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.strategy_runtime import StrategyRuntime
from trader.strategy_version import (
    Fingerprint,
    apply_wait,
    classify_update,
    fingerprint,
    load_changelog,
    next_decision_at,
    segments,
    update_block,
)

ROOT = Path(__file__).resolve().parent.parent
CFG = (ROOT / "config/bfast.yaml").read_text()


def test_BF_D45_classification_strategy_vs_app_only() -> None:
    app_only = classify_update(["trader/app_pages.py", "docs/GO_LIVE_GUIDE.md"], CFG, CFG)
    assert app_only == {"strategy": False, "reasons": []}
    code = classify_update(["trader/lines/emg2.py", "trader/webui.py"], CFG, CFG)
    assert code["strategy"] and code["reasons"] == ["strategy code: trader/lines/emg2.py"]
    for f in ("trader/universe.py", "trader/features.py", "config/lic_list.csv"):
        assert classify_update([f], CFG, CFG)["strategy"], f
    new = CFG.replace("slots: 18", "slots: 17")
    cfg = classify_update(["config/bfast.yaml"], CFG, new)
    assert cfg["strategy"] and cfg["reasons"] == ["strategy setting: live_emg2_20"]
    # a config change outside the strategy keys (the app's own settings) is app-only
    other = CFG.replace("every_seconds: 300", "every_seconds: 600")
    assert not classify_update(["config/bfast.yaml"], CFG, other)["strategy"]
    assert classify_update([], CFG, "::: not yaml")["strategy"]  # unreadable = careful side


def test_BF_D45_fingerprint_ignores_app_only_changes(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "trader/lines").mkdir(parents=True)
    (tmp_path / "trader/lines/emg2.py").write_text("RULE = 1\n")
    (tmp_path / "trader/webui.py").write_text("A = 1\n")
    p = tmp_path / "config/bfast.yaml"
    p.write_text(CFG)
    a = fingerprint(p, tmp_path)
    (tmp_path / "trader/webui.py").write_text("A = 2\n")
    p.write_text(CFG.replace("every_seconds: 300", "every_seconds: 600"))
    assert fingerprint(p, tmp_path).id == a.id
    (tmp_path / "trader/lines/emg2.py").write_text("RULE = 2\n")
    assert fingerprint(p, tmp_path).id != a.id
    assert a.version == "unversioned"
    notes = load_changelog((ROOT / "config/strategy_changelog.yaml").read_text())
    assert notes and {"version", "what", "why", "tested", "takes_effect"} <= set(notes[0])


def test_BF_D45_mode_switch_default_immediate_and_next_decision_block(tmp_path: Path) -> None:
    assert load_bfast_config(ROOT / "config/bfast.yaml").strategy.update_mode == "immediate"
    sess = [date(2026, 11, 26), date(2026, 11, 27), date(2026, 11, 30), date(2026, 12, 1)]
    before = datetime(2026, 11, 29, 23, 0, tzinfo=ASX_TZ)  # 23 h 20 min before the decision
    assert next_decision_at(sess, before) == datetime(2026, 11, 30, 22, 20, tzinfo=ASX_TZ)
    assert update_block("next_decision", True, sess, before, False) is not None
    assert update_block("next_decision", True, sess, before, True) is None  # override
    assert update_block("next_decision", False, sess, before, False) is None  # app-only
    assert update_block("immediate", True, sess, before, False) is None  # no block
    early = datetime(2026, 11, 26, 12, 0, tzinfo=ASX_TZ)
    assert update_block("next_decision", True, sess, early, False) is None


def test_BF_D45_wait_for_the_close_and_for_working_orders() -> None:
    assert apply_wait(False, True, 3) is None  # app-only: the market guard decides
    assert "16:15" in (apply_wait(True, True, 0) or "")
    assert "working" in (apply_wait(True, False, 2) or "")
    assert apply_wait(True, False, 0) is None
    j = Journal.sqlite()
    t = datetime(2026, 12, 1, 11, 0, tzinfo=ASX_TZ)
    jid = add_server_job(j, "update", STRATEGY | IMMEDIATE, "o", t)
    later = add_server_job(j, "check", 0, "o", t)
    assert claim_server_job(j, t, wait=lambda m: apply_wait(True, True, 0)) is None
    rows = {r["id"]: r for r in server_job_rows(j)}
    assert rows[jid]["status"] == "PENDING" and "16:15" in rows[jid]["result"]
    assert rows[later]["status"] == "PENDING"  # nothing jumps the waiting update
    # still waiting hours later (not refused as stale), then applied after the close
    close = datetime(2026, 12, 1, 16, 20, tzinfo=ASX_TZ)
    got = claim_server_job(j, close, wait=lambda m: apply_wait(True, False, 0))
    assert got is not None and got["id"] == jid and got["force"] & STRATEGY


def test_BF_D45_cli_claim_waits_for_working_orders(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import json

    from tests.test_bf_execution import BOOK, X, _batch, _ctx, _sim
    from trader.bfast_cli import main, working_orders
    from trader.execution import Executor
    from trader.journal import Status

    url = f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"
    j = Journal.sqlite(str(tmp_path / "j.sqlite"))
    sim = _sim()
    b = _batch(1)
    Executor(j, sim, BOOK).plan(b, "per_order", X, _ctx(sim))
    it = j.intents_of(b.batch_id)[0][0]
    for st in (Status.APPROVED, Status.SENDING, Status.SENT):
        j.set_status(it.client_order_id, st)
    assert working_orders(j, BOOK) == 1
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CFG.replace("book: EMG2_18_PAPER", f"book: {BOOK}"))
    add_server_job(j, "rollback", STRATEGY, "o", datetime.now(ASX_TZ))
    assert main(["server-jobs", "claim", "--journal", url, "--config", str(cfg)]) == 0
    assert json.loads(capsys.readouterr().out) == {}
    assert "working" in server_job_rows(j)[0]["result"]


def test_BF_D45_rollback_target_is_the_recorded_previous_commit(tmp_path: Path) -> None:
    g = runpy.run_path(str(ROOT / "deploy/gitops.py"))
    a, b = "a" * 40, "b" * 40
    assert g["target"](tmp_path, b) is None  # nothing recorded: no rollback
    g["record"](tmp_path, a)  # the worker, before updating from a to b
    assert g["target"](tmp_path, b) == a
    assert g["target"](tmp_path, a) is None  # already on it
    with pytest.raises(ValueError):
        g["record"](tmp_path, "HEAD~1")  # only a full commit id the worker read itself
    g["done"](tmp_path)
    assert g["target"](tmp_path, b) is None  # no ping-pong after a rollback
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert 'gitops.py" record "$STATE" "$before"' in sh and "merge-base --is-ancestor" in sh
    assert "rollback) out=$(do_rollback" in sh


def test_BF_D45_server_whitelist_has_rollback_and_claude_jobs() -> None:
    from trader.app_store import SERVER_ACTIONS

    assert {"rollback", "claude_remote", "claude_stop"} <= set(SERVER_ACTIONS)
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert "check|claude_remote|claude_stop) ;;" in sh
    assert "claude_remote) out=$(claude_remote_status start" in sh
    assert "tmux kill-session -t remote" in sh


def test_BF_D45_segments() -> None:
    d = date(2026, 1, 1)
    stamps = [(d, "v1", "A"), (d + timedelta(30), "v1", "A"), (d + timedelta(40), "v2", "B")]
    assert segments(stamps) == [(d, "v1", "A"), (d + timedelta(40), "v2", "B")]


def test_BF_D45_update_out_of_cycle_decision_is_stamped_and_needs_approval() -> None:
    """After an update (immediate mode) the trader decides out of cycle at 22:20 through
    the month-end path; the batch waits for the owner's approval like any other."""
    app, gw, tr = _app(D0)
    v1 = Fingerprint("v1", "c1", "k1", "")
    rt1 = StrategyRuntime(app, v1, "immediate")
    assert rt1.start(datetime(2024, 1, 15, 9, tzinfo=ASX_TZ)) == "first"
    days = DAYS[:8]
    dry_run(app, days, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    stamped = [k for k, _ in app.j.job_records("strategy:")]
    assert stamped == [f"strategy:{D0}"]  # the start decision, made by v1
    assert app.j.job_records(f"strategy:{D0}")[0][1]["id"] == v1.id
    # an update arrives: the trader restarts with v2
    day = days[-1]
    nxt = next(d for d in app.sessions if d > day)
    v2 = Fingerprint("v2", "c2", "k2", "")
    told: list[str] = []
    rt2 = StrategyRuntime(app, v2, "immediate", told.append)
    assert (
        rt2.start(datetime.combine(nxt, datetime.min.time(), ASX_TZ).replace(hour=17)) == "changed"
    )
    assert told and "out-of-cycle decision" in told[0]
    assert rt2.tick(datetime.combine(nxt, datetime.min.time(), ASX_TZ).replace(hour=21)) == "wait"
    for job in ("sim",):  # the twins at the day's closes first, as the scheduler does
        app.run_job(
            job, nxt, datetime.combine(nxt, datetime.min.time(), ASX_TZ).replace(hour=22, minute=15)
        )
    t = datetime.combine(nxt, datetime.min.time(), ASX_TZ).replace(hour=22, minute=21)
    assert rt2.tick(t) == "decided" and rt2.tick(t) == "idle"
    assert app.j.job_records(f"strategy:{nxt}")[0][1]["id"] == v2.id
    bid = f"EMG2_18_PAPER-{nxt}-R"
    b = app.j.batch(bid)
    assert b is not None and b["approval_mode"] == "per_order"
    assert app.j.approvals(bid) == []  # nothing is approved by the update
    assert any("Decision" in text or bid in text for _, text in tr.outbox)
    # the same approval path: the owner's code, by 15:20 of the next session
    x = b["execution_date"]
    at = datetime.combine(x, datetime.min.time(), ASX_TZ).replace(hour=10, minute=30)
    reply = app.bot.handle(Incoming(CHAT, f"/ok {bid} all {totp(SEED, at)}", at))
    assert reply.startswith("approved all")
    assert [(a["seq"], a["action"]) for a in app.j.approvals(bid)] == [(None, "OK")]
    st = get_state(app.j, "strategy-pending")
    assert st is not None and st[0]["done"] == str(nxt)


def test_BF_D45_next_decision_mode_makes_no_out_of_cycle_decision() -> None:
    app, gw, tr = _app(D0)
    StrategyRuntime(app, Fingerprint("v1", "c1", "k1", ""), "next_decision").start(
        datetime(2024, 1, 15, 9, tzinfo=ASX_TZ))  # fmt: skip
    rt = StrategyRuntime(app, Fingerprint("v2", "c2", "k2", ""), "next_decision")
    assert rt.start(datetime(2024, 1, 16, 17, tzinfo=ASX_TZ)) == "changed"
    assert rt.tick(datetime(2024, 1, 16, 22, 30, tzinfo=ASX_TZ)) == "idle"
    assert get_state(app.j, "strategy-pending") is None
