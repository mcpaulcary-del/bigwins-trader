"""Review of 4c24f0e..12b5952 (22 Nov 2026): one test per finding, written to fail on the
reviewed code and pass on the fix (BF-D46..BF-D54)."""

from __future__ import annotations

import csv
import io
import json
import runpy
import threading
import time
import urllib.request
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlencode

import pytest
import yaml

from tests.test_bf_app_actions import OWNER, _post, _rows, _session, _setup
from tests.test_bf_execution import SEED, T_APPROVE
from trader.app_control import Control, same_origin
from trader.app_sign import NonceCache, sign_job, sign_proxy, verify_proxy
from trader.app_store import (
    STRATEGY,
    add_server_job,
    cancel_server_job,
    claim_server_job,
    created_text,
    finish_server_job,
    get_state,
    inbox_rows,
    push_sub_rows,
    server_job_rows,
    set_state,
)
from trader.approval import totp
from trader.journal import Journal

ROOT = Path(__file__).resolve().parent.parent
KEY = b"k" * 64
REMOTE = "c" * 40


# ---------------------------------------------------------------- H1


def test_H1_dashboard_drops_a_login_header_from_an_untrusted_address(tmp_path: Path) -> None:
    from trader.dashboard import Dashboard, Sources
    from trader.journal import read_only_engine

    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{tmp_path / 'n.sqlite'}"))
    seen: list[dict[str, str]] = []

    def act(m: str, p: str, h: Any, b: bytes) -> tuple[int, dict[str, str], bytes]:
        seen.append(dict(h))
        return 200, {}, b"ok"

    d = Dashboard(Sources(j), actions=act, trusted_peers=frozenset({"172.31.250.1"}))
    forged = {"Tailscale-User-Login": OWNER}
    d.respond("POST", "/act/do", forged, b"a=pa", peer="172.31.0.7")  # gw-paper / db
    assert "Tailscale-User-Login" not in seen[-1]
    d.respond("POST", "/act/do", forged, b"a=pa", peer="172.31.250.1")  # the published port
    assert seen[-1]["Tailscale-User-Login"] == OWNER
    cfg = yaml.safe_load((ROOT / "config/bfast.yaml").read_text())
    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    gw = dc["networks"]["dashboard"]["ipam"]["config"][0]["gateway"]
    assert cfg["dashboard"]["trusted_proxies"] == [gw]


def test_H1_trader_accepts_only_fresh_signed_requests() -> None:
    j, bot, ctl, bid, _ = _setup()
    ctl.proxy_key = KEY
    forged = {"Tailscale-User-Login": OWNER}  # what anything on the control network could send
    assert ctl.respond("GET", "/act", forged)[0] == 403
    assert ctl.respond("POST", "/act/do", forged, b"a=pa")[0] == 403
    h = sign_proxy(KEY, OWNER, "", "same-origin", "GET", "/act", b"")
    st, hdrs, body = ctl.respond("GET", "/act", h)
    assert st == 200 and "Controls" in body.decode()
    assert ctl.respond("GET", "/act", h)[0] == 403  # replayed nonce
    old = sign_proxy(KEY, OWNER, "", "same-origin", "GET", "/act", b"", now=time.time() - 120)
    assert ctl.respond("GET", "/act", old)[0] == 403  # stale
    sid = hdrs["Set-Cookie"].split(";")[0].split("=", 1)[1]
    token = body.decode().split('name="csrf" value="')[1].split('"')[0]
    form = urlencode({"a": "pa", "csrf": token}).encode()
    p = sign_proxy(KEY, OWNER, "", "same-origin", "POST", "/act/do", form)
    tampered = {**p, "Cookie": f"bw_sid={sid}"}
    assert ctl.respond("POST", "/act/do", tampered, form + b"&x=1")[0] == 403  # body changed
    good = {**sign_proxy(KEY, OWNER, "", "same-origin", "POST", "/act/do", form),
            "Cookie": f"bw_sid={sid}"}  # fmt: skip
    assert "PAUSED" in ctl.respond("POST", "/act/do", good, form)[2].decode()
    other = sign_proxy(b"x" * 64, OWNER, "", "same-origin", "GET", "/act", b"")
    assert ctl.respond("GET", "/act", other)[0] == 403  # another key
    assert verify_proxy(KEY, {}, "GET", "/act", b"", NonceCache()) is None


def test_H1_dashboard_signs_what_it_forwards(monkeypatch: pytest.MonkeyPatch) -> None:
    from trader.dashboard import proxy_to

    got: dict[str, Any] = {}

    class _R(io.BytesIO):
        status = 200
        headers: ClassVar[dict[str, str]] = {"Content-Type": "text/html"}

        def __enter__(self) -> _R:
            return self

        def __exit__(self, *a: object) -> None:
            return None

    def fake(req: urllib.request.Request, timeout: float) -> _R:
        got["h"] = dict(req.header_items())
        got["body"] = req.data
        return _R(b"ok")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    fwd = proxy_to("http://trader-control:8081", KEY)
    fwd("POST", "/act/do", {"Tailscale-User-Login": OWNER, "Origin": "https://app.example",
                            "Sec-Fetch-Site": "same-origin"}, b"a=pa")  # fmt: skip
    signed = verify_proxy(KEY, got["h"], "POST", "/act/do", b"a=pa", NonceCache())
    assert signed == {
        "login": OWNER,
        "origin": "https://app.example",
        "site": "same-origin",
        "host": "",
    }  # (no Host header in this call; BF-D55 signs it)
    assert not any(k.lower() == "tailscale-user-login" for k in got["h"])


def test_H1_control_server_binds_its_control_address_only() -> None:
    from trader.bfast_cli import control_bind_address

    assert control_bind_address("localhost") == "127.0.0.1"
    with pytest.raises(SystemExit):
        control_bind_address("0.0.0.0")
    src = (ROOT / "trader/bfast_cli.py").read_text()
    assert 'serve_control(ctl, "0.0.0.0"' not in src and "control_bind_address(" in src
    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    svc = dc["services"]
    assert svc["trader"]["networks"]["control"]["aliases"] == ["trader-control"]
    holders = {n for n, v in svc.items() if "app_proxy_key" in v.get("secrets", [])}
    assert holders == {"trader", "dashboard", "secrets-check"}
    holders = {n for n, v in svc.items() if "worker_job_key" in v.get("secrets", [])}
    assert holders == {"trader", "secrets-check"}  # never the dashboard or db


def test_H1_L3_new_alert_device_needs_a_code_and_a_device_limit() -> None:
    j, bot, ctl, _, _ = _setup()
    ctl.max_devices = 2
    sid, token = _session(ctl)
    hdrs = {"Tailscale-User-Login": OWNER, "Cookie": f"bw_sid={sid}", "X-CSRF-Token": token,
            "Sec-Fetch-Site": "same-origin"}  # fmt: skip

    def sub(n: int, code: str) -> tuple[int, bytes]:
        body = json.dumps(
            {
                "subscription": {
                    "endpoint": f"https://fcm.googleapis.com/x{n}",
                    "keys": {"p256dh": "a", "auth": "b"},
                },
                "code": code,
            }
        )
        st, _, out = ctl.respond("POST", "/act/push/subscribe", hdrs, body.encode())
        return st, out

    assert sub(1, "")[0] == 400  # no code: nothing saved
    assert sub(1, "123456")[0] == 403 and push_sub_rows(j) == []
    for n, minutes in ((1, 1), (2, 2), (3, 3)):
        ctl.clock_box["t"] = T_APPROVE + timedelta(minutes=minutes)  # type: ignore[attr-defined]
        st, out = sub(n, totp(SEED, ctl.clock_box["t"]))  # type: ignore[attr-defined]
    assert st == 403 and b"limit" in out and len(push_sub_rows(j)) == 2
    off = urlencode({"csrf": token}).encode()
    assert ctl.respond("POST", "/act/push/off-all", hdrs, off)[0] == 200
    assert push_sub_rows(j) == []


def test_L2_origin_pinned_to_the_apps_host() -> None:
    host = "bigwins.example.ts.net"
    assert same_origin({"Origin": f"https://{host}"}, host)
    assert not same_origin({"Origin": "https://evil.example", "Host": "evil.example"}, host)
    assert not same_origin({}, host)  # neither Origin nor Sec-Fetch-Site
    assert same_origin({"Sec-Fetch-Site": "same-origin"}, host)


# ---------------------------------------------------------------- H2


def test_H2_status_between_wrong_codes_does_not_reset_the_count() -> None:
    """The reviewer's lock.py case A: wrong code, Status, wrong code, ..."""
    j, bot, ctl, bid, pages = _setup()
    s = _session(ctl)
    for i in range(3):
        _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": f"{i:06d}"}, session=s)
        _post(ctl, {"a": "st"}, session=s)
    assert ctl.locked(T_APPROVE) is not None and pages[-1].startswith("PAGE")
    _, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": totp(SEED, T_APPROVE)},
                    session=s)  # fmt: skip
    assert "locked" in page and _rows(j, bid) == []
    notes = [r for r in inbox_rows(j) if r["title"] == "A wrong code was entered in the app"]
    assert len(notes) == 2  # quiet notes for the first two; the third is the PAGE


def test_H2_count_is_persistent_and_cleared_only_by_a_correct_code() -> None:
    j, bot, ctl, bid, _ = _setup()
    s = _session(ctl)
    for i in range(2):
        _post(ctl, {"a": "ok", "b": bid, "n": "1", "code": f"{i:06d}"}, session=s)
    ctl2 = Control(j, bot, frozenset({OWNER}), book=ctl.book, clock=ctl.clock, inline=True)
    _post(ctl2, {"a": "ok", "b": bid, "n": "1", "code": "999999"})
    assert ctl2.locked(T_APPROVE) is not None  # 2 before the restart + 1 after
    j2, bot2, c2, bid2, _ = _setup()
    s2 = _session(c2)
    _post(c2, {"a": "ok", "b": bid2, "n": "1", "code": "000001"}, session=s2)
    _post(c2, {"a": "ok", "b": bid2, "n": "1", "code": totp(SEED, T_APPROVE)}, session=s2)
    assert get_state(j2, "app-code-fails")[0] == []  # type: ignore[index]


def test_H2_one_code_request_at_a_time_and_lock_checked_at_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reviewer's lock.py case B / lockb.py: a burst of queued codes."""
    from sqlalchemy import create_engine

    import trader.app_control as ac

    db = tmp_path / "j.sqlite"
    monkeypatch.setattr(Journal, "sqlite", classmethod(
        lambda cls, path=None: cls(create_engine(f"sqlite+pysqlite:///{db}"))))  # fmt: skip
    j, bot, ctl, bid, _ = _setup()
    ctl.inline = False
    monkeypatch.setattr(ac, "WAIT_S", 2)
    s = _session(ctl)
    res: list[str] = []
    ths = [threading.Thread(target=lambda i=i: res.append(
        _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": f"{i:06d}"}, session=s)[1]))
        for i in range(20)]  # fmt: skip
    for t in ths:
        t.start()
    time.sleep(0.5)
    assert ctl._q.qsize() == 1  # one queued, the others refused at once
    ctl.process()
    for t in ths:
        t.join()
    assert sum("another code request" in r for r in res) == 19
    assert bot.verifier.failures == 1
    # the lock is checked where the code is verified: a queued good code after a lock fails
    from trader.app_control import _Req

    ctl._locked_until = T_APPROVE + timedelta(minutes=5)
    r = ctl._execute(
        _Req(
            "bot",
            OWNER,
            T_APPROVE,
            {
                "command": f"/ok {bid} all {totp(SEED, T_APPROVE)}",
                "shown": "x",
                "code_bearing": True,
            },
        )
    )
    assert "locked" in r and _rows(j, bid) == []


# ---------------------------------------------------------------- H3


def _approve_update(ctl: Control, commit: str) -> str:
    set_state(ctl.journal, "update-available", {"ahead": 1, "remote": REMOTE, "strategy": False,
                                                 "previous": "d" * 40}, T_APPROVE)  # fmt: skip
    ctl.market_open = lambda now: False
    return _post(ctl, {"a": "srv:update", "commit": commit, "code": totp(SEED, T_APPROVE)})[1]


def test_H3_update_job_carries_the_reviewed_commit_and_a_signature(tmp_path: Path) -> None:
    j, _, ctl, _, _ = _setup()
    ctl.worker_key = KEY
    assert "changed since you looked" in _approve_update(ctl, "e" * 40)
    assert server_job_rows(j) == []
    j, _, ctl, _, _ = _setup()
    ctl.worker_key = KEY
    assert "queued" in _approve_update(ctl, REMOTE)
    row = server_job_rows(j)[0]
    assert row["commit"] == REMOTE and row["sig"]
    keyfile = tmp_path / "worker_job_key"
    keyfile.write_text(KEY.decode())
    g = runpy.run_path(str(ROOT / "deploy/gitops.py"))
    created = created_text(row["requested_at"])
    args = (str(row["id"]), "update", REMOTE, str(row["force"]), created)
    assert g["verify"](keyfile, *args, row["sig"])
    assert not g["verify"](keyfile, str(row["id"]), "update", "e" * 40, str(row["force"]),
                           created, row["sig"])  # a commit swapped in the database  # fmt: skip
    assert not g["verify"](keyfile, *args, sign_job(b"y" * 64, row["id"], "update", REMOTE,
                                                    row["force"], created))  # fmt: skip
    with pytest.raises(ValueError, match="exact commit"):
        add_server_job(j, "update", 0, OWNER, T_APPROVE)


def test_H3_worker_applies_exactly_the_signed_commit_and_reclassifies() -> None:
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert 'gitops.py" verify "$SECRETS/worker_job_key"' in sh
    assert 'merge-base --is-ancestor "$before" "$commit"' in sh
    assert 'merge-base --is-ancestor "$commit" "origin/$BRANCH"' in sh
    assert 'merge --ff-only -q "$commit"' in sh and "git -C $REPO pull" not in sh.split(
        "update_to() {")[1].split("\n}\n")[0]  # fmt: skip
    assert 'python3 "$DEPLOY/classify.py"' in sh and "approved as app-only" in sh


def test_H3_approval_expires_after_12_hours() -> None:
    j = Journal.sqlite()
    t = datetime(2026, 12, 1, 3, 0, tzinfo=UTC)
    add_server_job(j, "update", STRATEGY, OWNER, t, REMOTE)
    assert claim_server_job(j, t + timedelta(hours=11), wait=lambda m: "waiting") is None
    assert server_job_rows(j)[0]["status"] == "PENDING"
    assert claim_server_job(j, t + timedelta(hours=13)) is None
    assert server_job_rows(j)[0]["status"] == "REFUSED"


# ---------------------------------------------------------------- M1


def test_M1_dashboard_uses_a_select_only_role() -> None:
    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    d = dc["services"]["dashboard"]
    assert "db_password" not in d["secrets"] and "db_dashboard_password" in d["secrets"]
    assert d["environment"]["TRADER_BF_DB_PASSWORD_SECRET"] == "db_dashboard_password"
    assert d["depends_on"]["db-roles"] == {"condition": "service_completed_successfully"}
    roles = dc["services"]["db-roles"]
    assert "./db_roles.sql:/sql/db_roles.sql:ro" in roles["volumes"]
    sql = (ROOT / "deploy/db_roles.sql").read_text()
    assert "WHERE NOT EXISTS (SELECT 1 FROM pg_roles" in sql  # idempotent
    assert "GRANT SELECT ON ALL TABLES" in sql and "ALTER DEFAULT PRIVILEGES" in sql
    assert "default_transaction_read_only = on" in sql
    for verb in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALL PRIVILEGES"):
        assert f"GRANT {verb}" not in sql


def test_M1_postgres_role_cannot_write(pg_url: str) -> None:
    import subprocess

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import DBAPIError

    Journal(create_engine(pg_url)).engine.dispose()
    u = make_url(pg_url)
    env = {"PGPASSWORD": u.password or ""}
    r = subprocess.run(
        ["psql", "-h", u.host or "localhost", "-p", str(u.port or 5432), "-U", u.username or "",
         "-d", u.database or "", "-v", "ON_ERROR_STOP=1", "-v", f"db={u.database}", "-v",
         "pw=dashpw", "-f", str(ROOT / "deploy/db_roles.sql")],
        env=env, capture_output=True, check=False,
    )  # fmt: skip
    if r.returncode != 0:
        pytest.skip(f"psql not usable here: {r.stderr[:200]!r}")
    ro = create_engine(u.set(username="bigwins_dashboard", password="dashpw"))
    with ro.connect() as c:
        c.execute(text("SELECT count(*) FROM bf_events"))
    sql = "INSERT INTO bf_app_state (key, value, at) VALUES ('x', '{}', now())"
    with ro.begin() as c:
        c.execute(text("SET TRANSACTION READ WRITE"))  # even when it asks to write
        with pytest.raises(DBAPIError):
            c.execute(text(sql))
    ro.dispose()


# ---------------------------------------------------------------- M2


def test_M2_default_deny_classification_and_worker_agrees() -> None:
    from trader import strategy_version as sv

    w = runpy.run_path(str(ROOT / "deploy/classify.py"))
    assert w["UI_ONLY"] == sv.UI_ONLY and w["TRADING_DIRS"] == sv.TRADING_DIRS
    assert w["APP_ONLY_DIRS"] == sv.APP_ONLY_DIRS
    trading = ["trader/bf_app.py", "trader/orders.py", "trader/risk.py", "trader/execution.py",
               "trader/approval.py", "trader/scheduler.py", "trader/bfast_config.py",
               "migrations/versions/j0007_bf_server_job_commit.py", "config/bfast.yaml",
               "trader/app_control.py", "trader/broker/ibkr.py"]  # fmt: skip
    for f in trading:
        assert sv.is_trading_path(f) and w["classify"]([f]) == "strategy", f
    ui = ["trader/dashboard.py", "trader/webui.py", "trader/app_pages.py", "trader/app_notify.py",
          "trader/tax_screen.py", "trader/server_status.py", "trader/dashboard_demo.py",
          "docs/DECISIONS.md", "tests/test_x.py", "README.md"]  # fmt: skip
    # (deploy/ counts as infrastructure since BF-D60, tested in test_bf_rereview_fixes)
    for f in ui:
        assert not sv.is_trading_path(f) and w["classify"]([f]) == "app", f


# ---------------------------------------------------------------- M3


def test_M3_a_same_day_decision_by_the_old_version_does_not_cover_the_update() -> None:
    from tests.test_bf_app import D0, DAYS, _app, _closes
    from trader.bf_app import dry_run, mock_auction, owner_approves_all
    from trader.constants import ASX_TZ
    from trader.strategy_runtime import StrategyRuntime
    from trader.strategy_version import Fingerprint

    app, gw, _ = _app(D0)
    v1 = Fingerprint("v1", "c1", "k1", "")
    StrategyRuntime(app, v1, "immediate").start(datetime(2024, 1, 15, 9, tzinfo=ASX_TZ))
    dry_run(app, DAYS[:8], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    day = DAYS[7]
    # the old version already decided "today"; then the update arrives and restarts
    app.j.mark_job(
        f"decide:{app.s.book}:{day}", {"digest": "old"}, datetime(2024, 1, 1, tzinfo=UTC)
    )
    app.j.mark_job(f"strategy:{day}", v1.record(), datetime(2024, 1, 1, tzinfo=UTC))
    v2 = Fingerprint("v2", "c2", "k2", "")
    rt = StrategyRuntime(app, v2, "immediate")
    rt.start(datetime.combine(day, datetime.min.time(), ASX_TZ).replace(hour=23))
    t = datetime.combine(day, datetime.min.time(), ASX_TZ).replace(hour=23, minute=5)
    for key in ("22:15:sim", "22:20:decide", "22:25:fund_sweep"):
        app.j.mark_job(f"{day}:{key}", None, t)
    assert rt.tick(t) == "wait"  # not "covered": the decision was the old version's
    st = get_state(app.j, "strategy-pending")
    assert st is not None and not st[0].get("done")


# ---------------------------------------------------------------- M4 / L5


def test_M4_a_waiting_update_does_not_block_restart_check_or_claude() -> None:
    j = Journal.sqlite()
    t = datetime(2026, 12, 1, 1, 0, tzinfo=UTC)
    up = add_server_job(j, "update", STRATEGY, OWNER, t, REMOTE)
    rb = add_server_job(j, "rollback", STRATEGY, OWNER, t, "d" * 40)
    stop = add_server_job(j, "claude_stop", 0, OWNER, t)

    def wait(m: dict[str, Any]) -> str | None:
        return "waiting: the ASX is open" if m["action"] in ("update", "rollback") else None

    got = claim_server_job(j, t + timedelta(minutes=1), wait=wait)
    assert got is not None and got["id"] == stop
    rows = {r["id"]: r for r in server_job_rows(j)}
    assert rows[up]["status"] == rows[rb]["status"] == "PENDING"


def test_M4_cancel_a_queued_job_with_confirm_and_no_code() -> None:
    j, _, ctl, _, _ = _setup()
    jid = add_server_job(j, "restart", 0, OWNER, T_APPROVE)
    st, _, body = ctl.respond("GET", f"/act/confirm?a=cancel&job={jid}",
                              {"Tailscale-User-Login": OWNER})  # fmt: skip
    assert "Yes, Cancel the queued job" in body.decode() and 'name="code"' not in body.decode()
    assert "Yes button" in _post(ctl, {"a": "cancel", "job": str(jid)})[1]
    assert "cancelled" in _post(ctl, {"a": "cancel", "job": str(jid), "confirm": "yes"})[1]
    assert server_job_rows(j)[0]["status"] == "REFUSED"
    assert not cancel_server_job(j, jid, OWNER, T_APPROVE)  # only a queued job


def test_L5_a_hung_running_job_is_failed_and_the_unit_can_build() -> None:
    j = Journal.sqlite()
    t = datetime(2026, 12, 1, 1, 0, tzinfo=UTC)
    jid = add_server_job(j, "check", 0, OWNER, t)
    assert claim_server_job(j, t) is not None
    claim_server_job(j, t + timedelta(hours=3))
    row = server_job_rows(j)[0]
    assert row["id"] == jid and row["status"] == "FAILED" and "2 hours" in row["result"]
    assert not finish_server_job(j, jid, "DONE", "late", t + timedelta(hours=4))
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert "TimeoutStartSec=3600" in sh
    assert "crosses a database migration" in sh and "$((flags & 16))" in sh


def test_L5_rollback_across_a_migration_needs_the_box() -> None:
    j, _, ctl, _, _ = _setup()
    set_state(j, "update-available", {"previous": "d" * 40, "previous_migrations": True},
              T_APPROVE)  # fmt: skip
    ctl.market_open = lambda now: False
    _, _, body = ctl.respond("GET", "/act/confirm?a=srv:rollback", {"Tailscale-User-Login": OWNER})
    assert 'name="migration"' in body.decode() and "does not undo" in body.decode()
    page = _post(ctl, {"a": "srv:rollback", "code": totp(SEED, T_APPROVE)})[1]
    assert "crosses a database migration" in page and server_job_rows(j) == []
    later = T_APPROVE + timedelta(minutes=1)
    ctl.clock_box["t"] = later  # type: ignore[attr-defined]
    page = _post(ctl, {"a": "srv:rollback", "migration": "1", "code": totp(SEED, later)})[1]
    assert "queued" in page and server_job_rows(j)[0]["force"] & 16


# ---------------------------------------------------------------- M5


def test_M5_labels_follow_the_broker_mode() -> None:
    from trader.app_notify import AppNotifier
    from trader.tax_screen import LIVE_LABEL, label
    from trader.webui import page

    assert ">LIVE<" in page("x", "", live=True) and ">PAPER<" in page("x", "")
    assert ">DEMO<" in page("x", "", demo=True)

    class _S:
        live = True

    assert label(_S()) == LIVE_LABEL and "Paper" not in LIVE_LABEL
    n = AppNotifier(Journal.sqlite(), None, label="LIVE")
    assert n.label == "LIVE"
    src = (ROOT / "trader/bfast_cli.py").read_text()
    assert 'label="PAPER" if cfg.mode == "paper" else "LIVE"' in src
    assert 'live=cfg.mode != "paper"' in src


# ---------------------------------------------------------------- M6, L1, L4


def test_M6_screen_and_cli_agree_with_amit_and_prior_losses(tmp_path: Path) -> None:
    from tests.test_bf_tax_report import BOOK, _fill, _j
    from trader.bfast_cli import main
    from trader.orders import Side
    from trader.tax_report import TaxParams, build_report
    from trader.tax_screen import csv_export, report

    j = _j()
    _fill(j, "B1", "AAA", Side.BUY, 10, "10", date(2025, 7, 2))
    _fill(j, "S1", "AAA", Side.SELL, 10, "30", date(2026, 8, 3))
    _fill(j, "B2", "BBB", Side.BUY, 10, "10", date(2026, 7, 2))
    _fill(j, "S2", "BBB", Side.SELL, 10, "8", date(2026, 8, 3))
    amit = tmp_path / "amit.csv"
    amit.write_text("fy,code,cost_base_increase,cost_base_decrease,note\n")
    params = TaxParams("FIFO", 367, frozenset({"A200"}), "12_months")

    class _Src:
        journal = j
        book = BOOK
        tax_params = params
        prior_losses = Decimal(50)
        amit_csv = amit
        live = False

        @staticmethod
        def clock() -> datetime:
            return datetime(2026, 12, 1, tzinfo=UTC)

    scr = report(_Src(), 2026).summary
    cli = build_report(j, BOOK, "2026-27", params, None, [], Decimal(50)).summary
    assert scr == cli and scr.carried_in == Decimal(50)
    rows = list(csv.reader(io.StringIO(csv_export(_Src(), {"fy": "2026-27"}))))
    summ = {r[1]: r[7] for r in rows if r[0] == "summary"}
    assert summ["total current-year capital gains"] == f"{cli.short_gains + cli.long_gains:.2f}"
    assert summ["current-year capital losses applied"] == f"{cli.losses:.2f}"
    assert summ["prior-year (carried-in) losses applied"] == "50.00"
    assert summ["CGT discount applied"] == f"{cli.discount:.2f}"
    assert summ["net capital gain"] == f"{cli.net_gain:.2f}"
    assert summ["net capital loss carried forward"] == f"{cli.carried_out:.2f}"
    out = tmp_path / "tax"
    url = f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"
    j2 = Journal.sqlite(str(tmp_path / "j.sqlite"))
    for f in j.fills(BOOK):
        j2.add_fill(f)
    assert main(["tax-report", "--fy", "2026-27", "--book", BOOK, "--journal", url,
                 "--prior-losses", "50", "--out", str(out)]) == 0  # fmt: skip


def test_L1_last_day_of_february_before_a_leap_year() -> None:
    from trader.tax_report import TaxParams, plus_12_months

    p = TaxParams("FIFO", 367, frozenset(), "12_months")
    assert plus_12_months(date(2023, 2, 28)) == date(2024, 2, 29)
    assert not p.eligible(date(2023, 2, 28), date(2024, 2, 29))
    assert p.eligible(date(2023, 2, 28), date(2024, 3, 1))
    assert p.eligible_from(date(2023, 2, 28)) == date(2024, 3, 1)
    assert p.eligible_from(date(2024, 2, 28)) == date(2025, 3, 1)  # not the last day: 28 + 1


def test_L4_rebuy_flags_losses_only_and_buys_after_the_sale() -> None:
    from tests.test_bf_tax_report import BOOK, _fill, _j
    from trader.orders import Side
    from trader.tax_report import TaxParams, build_report
    from trader.tax_screen import rebuy_flags

    j = _j()
    p = TaxParams("FIFO", 367, frozenset(), "12_months")
    _fill(j, "B1", "WIN", Side.BUY, 10, "10", date(2026, 7, 2))
    _fill(j, "S1", "WIN", Side.SELL, 10, "12", date(2026, 8, 3))  # a gain: not flagged
    _fill(j, "B2", "WIN", Side.BUY, 10, "11", date(2026, 8, 10))
    _fill(j, "B3", "LOS", Side.BUY, 10, "10", date(2026, 7, 2))
    _fill(j, "B4", "LOS", Side.BUY, 10, "9", date(2026, 7, 30))  # before the sale
    _fill(j, "S2", "LOS", Side.SELL, 20, "8", date(2026, 8, 3))  # a loss, nothing re-bought

    class _Src:
        journal = j
        book = BOOK

    r = build_report(j, BOOK, "2026-27", p)
    assert rebuy_flags(_Src(), date(2026, 7, 1), date(2027, 6, 30), r) == []
    _fill(j, "B5", "LOS", Side.BUY, 5, "8", date(2026, 8, 20))  # after: flagged
    r = build_report(j, BOOK, "2026-27", p)
    flags = rebuy_flags(_Src(), date(2026, 7, 1), date(2027, 6, 30), r)
    assert len(flags) == 1 and flags[0].startswith("LOS: sold at a loss")


def test_review_inbox_and_journal_tables_still_match_alembic(tmp_path: Path) -> None:
    from alembic import command
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine

    from tests.conftest import alembic_config
    from trader.journal import md

    eng = create_engine(f"sqlite:///{tmp_path / 'j.db'}")
    with eng.begin() as conn:
        command.upgrade(alembic_config(conn, db="journal"), "journal@head")
    with eng.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), md) == []
    eng.dispose()
    _ = json  # (imported for the H1 bodies)


def test_H3_a_journal_from_the_reviewed_build_gets_the_new_columns(tmp_path: Path) -> None:
    from sqlalchemy import create_engine, inspect, text

    eng = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with eng.begin() as c:  # bf_server_jobs as j0006 created it
        c.execute(text("CREATE TABLE bf_server_jobs (id INTEGER PRIMARY KEY, action VARCHAR(32) "
                       "NOT NULL, force INTEGER NOT NULL, login VARCHAR(200) NOT NULL, "
                       "requested_at DATETIME NOT NULL, status VARCHAR(16) NOT NULL, started_at "
                       "DATETIME, finished_at DATETIME, result TEXT NOT NULL)"))  # fmt: skip
    j = Journal(eng)
    assert {"commit", "sig"} <= {c["name"] for c in inspect(eng).get_columns("bf_server_jobs")}
    add_server_job(j, "update", STRATEGY, OWNER, T_APPROVE, REMOTE, KEY)
    assert server_job_rows(j)[0]["commit"] == REMOTE
    Journal(eng)  # idempotent
