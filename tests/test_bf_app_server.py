"""BF-D42 / BF-D43: running the server from the app (a queue of whitelisted server jobs
for the host worker; no Docker socket in any container), the host status snapshot, the
server-only config overlay and the app's screens on a run of the real app."""

from __future__ import annotations

import json
import runpy
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

from trader.app_store import (
    SERVER_ACTIONS,
    add_server_job,
    claim_server_job,
    finish_server_job,
    get_state,
    server_job_rows,
)
from trader.bfast_cli import main
from trader.bfast_config import load_bfast_config, local_path
from trader.journal import Journal
from trader.server_status import clean_line, clean_status

ROOT = Path(__file__).resolve().parent.parent
T0 = datetime(2026, 12, 1, 3, 0, tzinfo=UTC)


def test_BF_D42_queue_claims_one_job_at_a_time_and_records_the_result() -> None:
    j = Journal.sqlite()
    a = add_server_job(j, "restart", False, "o", T0)
    b = add_server_job(j, "check", False, "o", T0 + timedelta(seconds=5))
    got = claim_server_job(j, T0 + timedelta(seconds=30))
    assert got is not None and got["id"] == a and got["status"] == "RUNNING"
    nxt = claim_server_job(j, T0 + timedelta(seconds=31))
    assert nxt is not None and nxt["id"] == b
    assert claim_server_job(j, T0 + timedelta(seconds=32)) is None
    assert finish_server_job(j, a, "DONE", "restarted", T0 + timedelta(minutes=1))
    assert not finish_server_job(j, a, "DONE", "twice", T0 + timedelta(minutes=2))  # once only
    with pytest.raises(ValueError, match="bad final status"):
        finish_server_job(j, b, "PENDING", "", T0)
    rows = {r["id"]: r for r in server_job_rows(j)}
    assert rows[a]["status"] == "DONE" and rows[a]["result"] == "restarted"


def test_BF_D42_old_requests_are_not_run_and_only_whitelisted_names_exist() -> None:
    j = Journal.sqlite()
    add_server_job(j, "restart", True, "o", T0)
    assert claim_server_job(j, T0 + timedelta(minutes=16)) is None
    assert server_job_rows(j)[0]["status"] == "REFUSED"
    add_server_job(j, "update", True, "o", T0, "a" * 40)  # may wait for the close: 12 h
    assert claim_server_job(j, T0 + timedelta(hours=13)) is None
    assert server_job_rows(j)[0]["status"] == "REFUSED"
    assert set(SERVER_ACTIONS) == {"restart", "update", "rollback", "check", "claude_remote",
                                   "claude_stop", "backup_now", "restore_test", "backup_key",
                                   "fetch", "hc_ping"}  # fmt: skip
    for bad in ("rm", "update; rm -rf /", "shell"):
        with pytest.raises(ValueError):
            add_server_job(j, bad, False, "o", T0)


def test_BF_D42_cli_claim_finish_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:  # fmt: skip
    import io

    url = f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"
    j = Journal.sqlite(str(tmp_path / "j.sqlite"))
    jid = add_server_job(j, "check", False, "o", datetime.now(UTC))
    assert main(["server-jobs", "claim", "--journal", url]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "id": jid, "action": "check", "force": False, "strategy": False, "immediate": False,
        "migration": False, "flags": 0, "commit": "", "sig": "",
        "created": server_job_rows(j)[0]["requested_at"].strftime("%Y-%m-%dT%H:%M:%SZ")}  # fmt: skip
    assert main(["server-jobs", "claim", "--journal", url]) == 0
    assert json.loads(capsys.readouterr().out) == {}
    monkeypatch.setattr("sys.stdin", io.StringIO("ok: 8 files\ntoken=abcdef123\n"))
    assert (
        main(["server-jobs", "finish", "--id", str(jid), "--status", "DONE", "--journal", url]) == 0
    )
    res = server_job_rows(j)[0]["result"]
    assert "ok: 8 files" in res and "abcdef123" not in res
    snap = {"load1": 0.2, "cpus": 2, "log": ["x password=hunter2", "https://hc-ping.com/uuid"],
            "containers": [{"name": "trader", "state": "Up"}], "evil": "dropped"}  # fmt: skip
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(snap)))
    assert main(["server-jobs", "status", "--journal", url]) == 0
    st = get_state(j, "host-status")
    assert st is not None and "evil" not in st[0]
    assert "hunter2" not in json.dumps(st[0]) and "hc-ping" not in json.dumps(st[0])


def test_BF_D42_log_cleaning() -> None:
    for secret in ("bot123456:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw", "owner@example.com",
                   "DU1234567", "https://hc-ping.com/abc", "password: x1", "A" * 40):  # fmt: skip
        assert secret not in clean_line(f"line {secret} end")
    assert clean_status({"load1": "x", "cpus": 2})["cpus"] == 2.0


def test_BF_D42_host_scripts() -> None:
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert (
        subprocess.run(["bash", "-n", str(ROOT / "deploy/bigwins.sh")], check=False).returncode == 0
    )
    # the worker runs only the fixed list, refuses restart/update while the ASX is open
    assert "restart) out=$(dc up -d" in sh and 'update) out=$(update_to "$commit"' in sh
    assert '*) finish_job "$id" REFUSED' in sh and 'market_open && [ "$force" != True ]' in sh
    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    for name, svc in dc["services"].items():  # no container gets the Docker socket or the host
        assert not any("docker.sock" in str(v) for v in svc.get("volumes", [])), name
        assert not svc.get("privileged") and svc.get("network_mode") != "host", name
    ns = runpy.run_path(str(ROOT / "deploy/set_login.py"))
    set_login = ns["set_login"]
    t = set_login("", "owner@example.com")
    assert yaml.safe_load(t)["app"]["allowed_logins"] == ["owner@example.com"]
    t2 = set_login("tax:\n  marginal_rate: 0.3\napp:\n  allowed_logins: []\n  x: 1\n", "a@b.c")
    assert yaml.safe_load(t2) == {"tax": {"marginal_rate": 0.3},
                                  "app": {"allowed_logins": ["a@b.c"], "x": 1}}  # fmt: skip
    with pytest.raises(ValueError):
        set_login("", "x\n  evil: 1")
    hs = runpy.run_path(str(ROOT / "deploy/host_status.py"))
    snap = hs["snapshot"]({"PS": "trader|Up 1 h\ndb|Up", "TS": "Running"})
    assert snap["containers"][0] == {"name": "trader", "state": "Up 1 h"} and snap["cpus"] >= 1


def test_BF_D39_local_overlay_holds_server_only_settings(tmp_path: Path) -> None:
    base = (ROOT / "config/bfast.yaml").read_text()
    p = tmp_path / "bfast.yaml"
    p.write_text(base)
    assert load_bfast_config(p).app.allowed_logins == []
    local_path(p).write_text(
        "app:\n  allowed_logins: [owner@example.com]\ntax:\n  marginal_rate: 0.345\n"
    )
    cfg = load_bfast_config(p)
    assert cfg.app.allowed_logins == ["owner@example.com"] and str(cfg.tax.marginal_rate) == "0.345"
    assert cfg.app.control_port == 8081 and cfg.tax.parcel_method == "FIFO"  # rest kept
    assert "config/*.local.yaml" in (ROOT / ".gitignore").read_text()
    assert not local_path(ROOT / "config/bfast.yaml").exists()  # never in the repository


# ---------------------------------------------------------------- the screens (BF-D43)


@pytest.fixture(scope="module")
def demo_app(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo, demo_control
    from trader.journal import read_only_engine

    demo = build_demo(tmp_path_factory.mktemp("d") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
    src = Sources(j, index=demo.index, sessions=lambda: demo.sessions, today=lambda: demo.last_day,
                  clock=lambda: demo.now, demo=True)  # fmt: skip
    return demo, Dashboard(
        src, actions=demo_control(j, demo).respond, action_logins=frozenset({"demo"})
    )


def _get(d: Any, path: str) -> tuple[int, str]:
    s, _, b = d.respond("GET", path, {})
    return s, b.decode()


def test_BF_D43_every_tab_renders_with_the_tab_bar(demo_app: Any) -> None:
    _, d = demo_app
    for path, tab in (("/", "home"), ("/holdings", "holdings"), ("/orders", "orders"),
                      ("/inbox", "inbox"), ("/server", "server"), ("/tax", "holdings")):  # fmt: skip
        s, page = _get(d, path)
        assert s == 200 and f'data-tab="{tab}"' in page and 'class="tabs"' in page, path
        assert "Traceback" not in page and "DEMO" in page
    s, page = _get(d, "/settings")
    assert s == 200 and "Go-live checklist" in page


def test_BF_D43_home_has_waiting_batch_chart_ranges_and_twins(demo_app: Any) -> None:
    demo, d = demo_app
    _, page = _get(d, "/")
    assert "Needs your approval" in page and "/act/confirm?a=ok&amp;b=" in page
    assert 'data-range="31"' in page and 'id="perf-data"' in page and "From peak" in page
    assert "you are here" in page and "Percentile history" in page


def test_BF_D43_holding_and_batch_screens(demo_app: Any) -> None:
    demo, d = demo_app
    w = Journal.sqlite(str(demo.journal_path))
    code = sorted(w.positions("EMG2_18_PAPER"))[0]
    s, page = _get(d, f"/holdings/{code}")
    assert s == 200 and "Price since bought" in page and "Why it was chosen" in page
    assert "Sell rule (C6)" in page and "of 6" in page and "band C" in page
    assert _get(d, "/holdings/NOPE")[0] == 404
    bid = w.batches_of("EMG2_18_PAPER")[0][0]
    s, page = _get(d, f"/orders/{bid}")
    assert s == 200 and "filled" in page and 'class="tl2"' in page
    s, page = _get(d, "/orders")
    assert s == 200 and "Decisions" in page and bid in page


def test_BF_D43_inbox_filters_and_demo_actions_change_nothing(demo_app: Any) -> None:
    demo, d = demo_app
    _, page = _get(d, "/inbox?kind=report")
    assert 'data-filter="alerts"' in page and "Daily report" in page
    assert 'data-kind="approval" hidden' in page  # server-side filter (works without JS)
    w = Journal.sqlite(str(demo.journal_path))
    before = (len(w.events()), w.safety_level())
    s, _, body = d.respond("GET", "/act/confirm?a=pa", {})
    token = body.decode().split('name="csrf" value="')[1].split('"')[0]
    s, hdrs, body = d.respond("GET", "/act", {})
    sid = hdrs["Set-Cookie"].split(";")[0].split("=", 1)[1]
    token = body.decode().split('name="csrf" value="')[1].split('"')[0]
    s, _, body = d.respond("POST", "/act/do", {"Cookie": f"bw_sid={sid}"},
                           f"a=ki&confirm=yes&csrf={token}".encode())  # fmt: skip
    assert s == 200 and "DEMO: nothing was done" in body.decode()
    assert (len(w.events()), w.safety_level()) == before
