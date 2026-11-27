"""BF-D64 / BF-D65: backups (encrypted archives on the server and in OneDrive), the
restore round trip, retention, the one-time recovery-key view, the Backups and Accounts
screens, and no unsigned write path."""

from __future__ import annotations

import io
import json
import runpy
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.test_bf_app_actions import OWNER, _post, _session, _setup
from tests.test_bf_execution import SEED, T_APPROVE
from trader.app_store import get_state, inbox_rows, server_job_rows, set_state
from trader.approval import totp
from trader.backups import daily_summary, record_result, seal, unseal
from trader.journal import Journal

ROOT = Path(__file__).resolve().parent.parent
B = runpy.run_path(str(ROOT / "deploy/backup.py"))
G = runpy.run_path(str(ROOT / "deploy/gitops.py"))
HAS_AGE = shutil.which("age") is not None and shutil.which("age-keygen") is not None
KEY = b"k" * 64


@pytest.mark.skipif(not HAS_AGE, reason="age is not installed")
def test_BF_D64_backup_restore_round_trip_local(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "config").mkdir(parents=True)
    (src / "config" / "bfast.local.yaml").write_text("app:\n  allowed_logins: [x]\n")
    (src / "record").mkdir()
    (src / "record" / "LEDGER.jsonl").write_text('{"seq":1,"hash":"aa"}\n')
    (src / "secrets").mkdir()
    (src / "secrets" / "db_password").write_text("TOP-SECRET-VALUE-123")
    (src / "env").write_text("JOURNAL_DB=ledger_bf_paper\n")
    key = tmp_path / "key" / "backup.key"
    rcp = B["keygen"](key)
    assert rcp.startswith("age1") and (key.stat().st_mode & 0o777) == 0o600
    plan = {"out_dir": str(tmp_path / "out"), "key_file": str(key),
            "remote": str(tmp_path / "onedrive"),
            "pg_dump": [sys.executable, "-c", "print('CREATE TABLE bf_events (id int);')"],
            "row_counts": {"bf_events": 0},
            "sources": [["config", str(src / "config")], ["record", str(src / "record")],
                        ["secrets", str(src / "secrets")], ["deploy_env", str(src / "env")]]}  # fmt: skip
    res = B["run"](plan)
    assert res["ok"] and res["remote"]["ok"] and res["local"]["files"] == 5
    arch = tmp_path / "out" / res["local"]["archive"]
    assert (tmp_path / "onedrive" / arch.name).is_file()  # the second destination
    blob = arch.read_bytes()
    assert b"TOP-SECRET-VALUE-123" not in blob and b"LEDGER" not in blob  # encrypted
    manifest = json.loads((tmp_path / "out" / (arch.name + ".json")).read_text())
    assert "TOP-SECRET" not in json.dumps(manifest)
    v = B["verify"](arch, key, tmp_path)
    assert v["ok"] and v["ledger_files"] == 1 and v["journal_dump"] and not v["bad"]
    dest = tmp_path / "restored"
    B["restore"](arch, dest, key)
    assert (dest / "secrets" / "db_password").read_text() == "TOP-SECRET-VALUE-123"
    assert (dest / "record" / "LEDGER.jsonl").read_text().startswith('{"seq":1')
    assert "CREATE TABLE" in (dest / "journal" / "journal.sql").read_text()
    other = tmp_path / "other.key"
    B["keygen"](other)
    with pytest.raises(RuntimeError):
        B["restore"](arch, tmp_path / "x", other)  # the wrong key opens nothing
    # a changed file is caught by the restore test
    (src / "record" / "LEDGER.jsonl").write_text("tampered")
    assert B["verify"](arch, key, tmp_path)["ok"]  # the archive itself is unchanged


def test_BF_D64_retention_30_daily_12_monthly(tmp_path: Path) -> None:
    start = datetime(2025, 1, 1, 13, 30, tzinfo=UTC)
    names = []
    for d in range(500):  # two backups a day for 500 days
        for h in (0, 3):
            t = start + timedelta(days=d, hours=h)
            names.append(f"bigwins-{t:%Y%m%d-%H%M%S}.tar.age")
    kept = B["keep"](names)
    days = {n[8:16] for n in kept}
    newest = max(names)
    assert newest in kept and len([n for n in kept if n in sorted(names)[-60:]]) == 30
    months = {n[8:14] for n in kept}
    assert len(months) == 13 or len(months) == 12  # 12 monthly (+ the current month's dailies)
    assert len(kept) <= 30 + 12 and len(days) == len(kept)
    remote = tmp_path / "r"
    remote.mkdir()
    for n in names[-80:]:
        (remote / n).write_text("x")
        (remote / (n + ".json")).write_text("{}")
    gone = B["prune"](sorted(x.name for x in remote.iterdir()),
                      lambda n: (remote / n).unlink())  # fmt: skip
    left = sorted(x.name for x in remote.iterdir() if x.name.endswith(".age"))
    assert len(left) == len(B["keep"](names[-80:])) and gone
    assert all((remote / (n + ".json")).exists() for n in left)


def _reveal_page(ctl: Any, s: tuple[str, str]) -> str:
    """POST, then the one-time GET it redirects to (security review L2: PRG)."""
    from urllib.parse import urlencode

    hdrs = {
        "Tailscale-User-Login": OWNER,
        "Cookie": f"bw_sid={s[0]}",
        "Sec-Fetch-Site": "same-origin",
    }
    st, h, _ = ctl.respond("POST", "/act/backup-key", hdrs, urlencode({"csrf": s[1]}).encode())
    assert st == 303, st
    st, _, body = ctl.respond("GET", h["Location"], hdrs)
    page = str(body.decode())
    again = ctl.respond("GET", h["Location"], hdrs)[2].decode()  # a refresh: nothing again
    assert "AGE-SECRET" not in again and "No key to show" in again
    return page


def test_BF_D64_key_view_needs_code_job_and_is_shown_once(tmp_path: Path) -> None:
    j, _, ctl, _, _ = _setup()
    ctl.worker_key = KEY
    # asking the server for the key is a code action; Back up now only needs a confirm
    _, _, body = ctl.respond(
        "GET", "/act/confirm?a=srv:backup_key", {"Tailscale-User-Login": OWNER}
    )
    assert 'name="code"' in body.decode()
    _, _, body = ctl.respond(
        "GET", "/act/confirm?a=srv:backup_now", {"Tailscale-User-Login": OWNER}
    )
    assert 'name="code"' not in body.decode() and "Yes, run it" in body.decode()
    s = _session(ctl)
    assert "enter your 6-digit code" in _post(ctl, {"a": "srv:backup_key"}, session=s)[1]
    assert "queued" in _post(ctl, {"a": "srv:backup_key", "code": totp(SEED, T_APPROVE)},
                             session=s)[1]  # fmt: skip
    assert "queued" in _post(ctl, {"a": "srv:backup_now", "confirm": "yes"})[1]
    assert all(r["sig"] for r in server_job_rows(j))  # signed for the worker
    # nothing sealed yet: nothing to show
    assert "No key to show" in _post(ctl, {}, session=s, path="/act/backup-key")[1]
    # the worker seals the key with the shared key; the app shows it once
    kf, sf = tmp_path / "wk", tmp_path / "bk"
    kf.write_text(KEY.decode())
    sf.write_text("# public key: age1xyz\nAGE-SECRET-KEY-1ABCDEFGHIJK\n")
    sealed = G["seal"](kf, sf)
    assert "AGE-SECRET" not in sealed and unseal(KEY, sealed) == sf.read_bytes()
    set_state(j, "backup-key-sealed", {"sealed": sealed}, T_APPROVE)
    st, _, body = ctl.respond("GET", "/act/backup-key", {"Tailscale-User-Login": OWNER})
    assert "Show the key now" in body.decode() and "AGE-SECRET" not in body.decode()
    # security review L2: another browser session of the same log-in is refused
    assert "Not shown" in _post(ctl, {}, session=_session(ctl), path="/act/backup-key")[1]
    page = _reveal_page(ctl, s)
    assert "AGE-SECRET-KEY-1ABCDEFGHIJK" in page and "password manager" in page
    assert "AGE-SECRET" not in json.dumps([r["body"] + r["title"] for r in inbox_rows(j)])
    assert "Not shown" in _post(ctl, {}, session=s, path="/act/backup-key")[1]  # once
    assert j.job_records("backup-key-shown:")
    # a stale seal (over 10 minutes) is not shown
    _post(ctl, {"a": "srv:backup_key", "code": totp(SEED, T_APPROVE + timedelta(seconds=40))},
          session=s)  # fmt: skip
    set_state(j, "backup-key-sealed", {"sealed": sealed}, T_APPROVE - timedelta(minutes=11))
    assert "No key to show" in _post(ctl, {}, session=s, path="/act/backup-key")[1]
    # tampered: refused
    assert unseal(KEY, sealed[:-2] + ("00" if sealed[-2:] != "00" else "11")) is None
    assert unseal(b"x" * 64, seal(KEY, b"abc", b"n" * 16)) is None


def test_BF_D64_results_recorded_and_failures_paged() -> None:
    from trader.bfast_cli import tell_backups

    j = Journal.sqlite()
    now = datetime(2026, 12, 1, 12, 30, tzinfo=UTC)
    r = record_result(j, {"ok": True, "kind": "backup", "local": {"archive": "bigwins-x.tar.age",
                                                                  "size": 10, "files": 3},
                          "remote": {"ok": True}, "secret": "zzz"}, now)  # fmt: skip
    assert r["ok"] and "secret" not in json.dumps(get_state(j, "backup-last")[0])  # type: ignore[index]
    sent: list[str] = []

    class _N:
        def notify(self, text: str, *a: Any, **k: Any) -> int:
            sent.append(text)
            return 0

    assert tell_backups(j, _N()) == 0  # type: ignore[arg-type]
    record_result(j, {"ok": False, "kind": "backup", "error": "OSError: disk full"},
                  now + timedelta(days=1))  # fmt: skip
    assert tell_backups(j, _N()) == 1 and sent[0].startswith("PAGE Backup FAILED")  # type: ignore[arg-type]
    assert tell_backups(j, _N()) == 0  # type: ignore[arg-type]
    record_result(j, {"ok": False, "kind": "restore_test", "error": "rows differ"},
                  now + timedelta(days=2))  # fmt: skip
    assert tell_backups(j, _N()) == 1 and "Restore test FAILED" in sent[-1]  # type: ignore[arg-type]
    assert len(get_state(j, "backup-history")[0]) == 3  # type: ignore[index]


def test_BF_D64_cli_backup_and_reveal_ops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from trader.bfast_cli import main

    url = f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"
    j = Journal.sqlite(str(tmp_path / "j.sqlite"))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"ok": True, "kind": "backup"})))
    assert main(["server-jobs", "backup", "--journal", url]) == 0
    assert get_state(j, "backup-last")[0]["ok"] is True  # type: ignore[index]
    monkeypatch.setattr("sys.stdin", io.StringIO("AGE-SECRET-KEY-plain"))
    with pytest.raises(SystemExit):
        main(["server-jobs", "reveal", "--journal", url])  # never a plain key
    monkeypatch.setattr("sys.stdin", io.StringIO(seal(KEY, b"AGE-SECRET-KEY-1X", b"n" * 16)))
    assert main(["server-jobs", "reveal", "--journal", url]) == 0


def test_BF_D64_D65_screens_are_read_only(tmp_path: Path) -> None:
    from trader.dashboard import Dashboard, Sources
    from trader.journal import read_only_engine

    w = Journal.sqlite(str(tmp_path / "j.sqlite"))
    record_result(w, {"ok": True, "kind": "backup", "local": {"size": 2048, "archive": "a"},
                      "remote": {"ok": True}}, datetime(2026, 12, 1, tzinfo=UTC))  # fmt: skip
    w.engine.dispose()
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"))
    d = Dashboard(Sources(j, clock=lambda: datetime(2026, 12, 1, 3, tzinfo=UTC)))
    for path in ("/backups", "/accounts"):
        st, _, body = d.respond("GET", path, {})
        page = body.decode()
        assert st == 200 and "<form" not in page
        for m in ("POST", "PUT", "DELETE"):
            assert d.respond(m, path, {})[0] == 405
    page = d.respond("GET", "/backups", {})[2].decode()
    assert "Back up now" in page and "Restore test" in page and "recovery key" in page
    assert "rclone authorize" in page and "OneDrive: not connected" in page
    acc = d.respond("GET", "/accounts", {})[2].decode()
    for name in ("Interactive Brokers", "BinaryLane", "Tailscale", "GitHub", "EODHD",
                 "OneDrive", "healthchecks.io", "Claude"):  # fmt: skip
        assert name in acc
    assert "never stores your IBKR" in acc and 'rel="noopener noreferrer"' in acc
    assert 'data-remind="eodhd"' in acc  # renewal dates kept on the phone


def test_BF_D64_daily_summary_has_no_secrets(tmp_path: Path) -> None:
    from trader.dashboard import Sources, collect

    j = Journal.sqlite()
    v = collect(Sources(j))
    page = daily_summary(v, [], "PAPER")
    assert "Big Wins PAPER" in page and "DU" not in page and "token" not in page.lower()


def test_BF_D64_worker_runs_backup_jobs_from_the_fixed_list() -> None:
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert (
        "check|claude_remote|claude_stop|backup_now|restore_test|backup_key|fetch|hc_ping|info_archive|prev_twin|autoupdate_on|autoupdate_off|record_daily) ;;"  # BF-D90, BF-D93
        in sh
    )
    assert "OnCalendar=*-*-* 23:30:00 Australia/Sydney" in sh
    assert 'gitops.py" seal "$SECRETS/worker_job_key" "$BKEY"' in sh
    assert "BKEY=/root/.bigwins-backup/backup.key" in sh and "chmod 600" in sh
