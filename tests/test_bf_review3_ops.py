"""Full review, operations + security review of the backups (22 Nov 2026; BF-D70):
the gateway's network, the image, the trader command, restore that fails closed,
signed manifests, retention, monitoring, CI status on the update card, and the
static checks of the server scripts."""

from __future__ import annotations

import json
import os
import runpy
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
B: dict[str, Any] = runpy.run_path(str(ROOT / "deploy" / "backup.py"))
SH = (ROOT / "deploy" / "bigwins.sh").read_text()
age = pytest.mark.skipif(shutil.which("age") is None, reason="age is not installed")


# ------------------------------------------------------------------ compose / image
def test_F1_gateway_has_its_own_egress_and_no_ports() -> None:
    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    gw = dc["services"]["gw-paper"]
    nets = gw["networks"]
    assert "internal" in nets and "gw-egress" in nets and "ports" not in gw
    assert not dc["networks"]["gw-egress"].get("internal")
    assert dc["networks"]["internal"]["internal"] is True
    assert "gw-egress" not in dc["services"]["trader"]["networks"]  # trader: its own egress
    assert "gw-egress" not in dc["services"]["db"]["networks"]


def test_F3_F11_F21_F22_image_and_limits() -> None:
    df = (ROOT / "deploy/Dockerfile").read_text()
    assert "uv:0.11.32@sha256:" in df  # L6: uv pinned by digest
    assert "mkdir -p /app/out && chown trader:trader /app/out" in df
    assert df.index("--no-install-project") < df.index("COPY trader ./trader")
    assert "ARG BUILD_SHA" in df and "_build_sha.txt" in df
    assert "COPY docs/FORECAST_BANDS.md" in df
    ign = (ROOT / ".dockerignore").read_text()
    assert "deploy/secrets" in ign and "deploy/.env" in ign and ".git" in ign
    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    assert dc["services"]["gw-paper"]["mem_limit"] == "1500m"
    assert dc["services"]["dashboard"]["mem_limit"] == "512m"
    cmd = " ".join(dc["services"]["trader"]["command"])
    assert "${TRADER_CMD:-sleep infinity}" in cmd  # F5


# ------------------------------------------------------------------ the server scripts
def test_F4_F5_F17_F19_F23_F24_script_paths() -> None:
    restart = SH[SH.index("cmd_restart() {") : SH.index("cmd_new_backup_key() {")]
    assert "docker rm -f bigwins-demo" in restart  # F4
    assert "start-trader) cmd_start_trader" in SH and "TRADER_CMD=" in SH  # F5
    assert "Postgres keeps the original" in SH  # F17
    inst = SH[SH.index("cmd_install_worker() {") : SH.index("cmd_check() {")]
    assert inst.index("systemctl daemon-reload") < inst.index("enable --now")  # F19
    assert "cmd_seed_data" in SH and "chown -R 10001:10001" in SH  # F23
    assert "DU[0-9]{5,10}" in SH and "IBKR_PAPER_USERID=" in SH  # F24
    assert "docker image prune -f" in SH and "builder prune" in SH  # F11


def test_F6_M1_restore_fails_closed() -> None:
    r = SH[SH.index("cmd_restore() {") : SH.index("finish_job() {")]
    for must in ("up -d --wait db", "pg_isready", "ON_ERROR_STOP=1", "--single-transaction",
                 "ledger_bf_paper", "createdb", "already has journal tables", "age-keygen -y",
                 "check-manifest", "Row counts differ", "git -C $REPO checkout -q", "ls-files",
                 "Restore this one?", "Paste a recovery key now"):  # fmt: skip
        assert must in r, must
    # the database is loaded and checked before the stack (dc up -d) starts
    assert r.index("Row counts differ") < r.index("  dc up -d &&")
    t = SH[SH.index("do_restore_test() {") : SH.index("cmd_onedrive() {")]
    assert "--network none" in t and "openssl rand" in t and "trap" in t and "--keep" in t
    assert "pg_isready -h 127.0.0.1" in t and "bool(want) and bool(got)" in t


def test_F7_F8_bootstrap() -> None:
    bs = (ROOT / "deploy/server_bootstrap.sh").read_text()
    for must in ("age rclone tmux", "/usr/local/bin/bigwins", "core.sshCommand", "swapfile",
                 "/etc/docker/daemon.json", "max-size", "chown -R 10001:10001",
                 "Disable key expiry", "Singapore"):  # fmt: skip
        assert must in bs, must
    assert bs.index("daemon.json") < bs.index("get.docker.com")


@pytest.mark.skipif(shutil.which("bash") is None, reason="no bash")
def test_scripts_parse_and_pass_shellcheck() -> None:
    for f in ("deploy/bigwins.sh", "deploy/server_bootstrap.sh", "deploy/check_secrets.sh"):
        subprocess.run(["bash", "-n", str(ROOT / f)], check=True)
    if shutil.which("shellcheck"):
        subprocess.run(["shellcheck", "-S", "error", str(ROOT / "deploy/bigwins.sh")], check=True)


def test_M3_no_silent_new_backup_key_and_explicit_rotation() -> None:
    mk = SH[SH.index("make_keys() {") : SH.index("update_to() {")]
    assert "NO new key made" in mk and "bigwins new-backup-key" in mk
    assert "new-backup-key) cmd_new_backup_key" in SH


# ------------------------------------------------------------------ backup.py
def _plan(tmp: Path, key: Path, **kw: Any) -> dict[str, Any]:
    src = tmp / "src"
    (src / "config").mkdir(parents=True, exist_ok=True)
    (src / "config" / "bfast.local.yaml").write_text("app: {}\n")
    return {"out_dir": str(tmp / "out"), "key_file": str(key), "remote": str(tmp / "remote"),
            "sources": [["config", str(src / "config")]], "work_dir": str(tmp), "commit": "a" * 40,
            "row_counts": {"bf_events": 3}, "pg_dump": ["echo", "-- a journal dump"], **kw}  # fmt: skip


@age
def test_L1_signed_manifest_tamper_and_foreign_key(tmp_path: Path) -> None:
    key = tmp_path / "k" / "backup.key"
    B["keygen"](key)
    r = B["run"](_plan(tmp_path, key))
    assert r["ok"] and len(r["key_fp"]) == 12, r
    arch = tmp_path / "out" / r["local"]["archive"]
    v = B["verify"](arch, key, tmp_path)
    assert v["ok"] and v["commit"] == "a" * 40 and not v["missing_sources"]
    dest = tmp_path / "d"
    B["restore"](arch, dest, key)
    (dest / "MANIFEST.json").write_text((dest / "MANIFEST.json").read_text().replace("3", "4"))
    with pytest.raises(RuntimeError, match="signature"):
        B["check_manifest"](dest, key)
    other = tmp_path / "k2" / "other.key"
    B["keygen"](other)
    v2 = B["verify"](arch, other, tmp_path)
    assert not v2["ok"] and "does not open" in v2["error"]  # L4: an accurate message


def test_L1_future_dated_archives_are_never_picked_or_pruned() -> None:
    now = datetime(2026, 11, 22, 12, tzinfo=UTC)
    names = [f"bigwins-202611{d:02d}-010000.tar.age" for d in range(1, 22)]
    fut = "bigwins-20990101-000000.tar.age"
    assert B["latest"]([*names, fut], now) == names[-1]
    gone: list[str] = []
    B["prune"]([*names, fut], gone.append, 7, 0, now)
    assert fut not in gone and len(gone) == 21 - 7


@age
def test_L4_absolute_symlinks_refused_part_files_removed_big_archive_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = tmp_path / "k" / "backup.key"
    B["keygen"](key)
    plan = _plan(tmp_path, key)
    out = Path(plan["out_dir"])
    out.mkdir(parents=True)
    (out / "bigwins-x.tar.part").write_text("half")
    os.symlink("/etc/hostname", tmp_path / "src" / "config" / "link")
    r = B["run"](plan)
    assert not r["ok"] and "symlink" in r["error"]
    (tmp_path / "src" / "config" / "link").unlink()
    run = B["run"]
    run.__globals__["BIG"] = 10  # anything is "big" for this run
    try:
        r = run(plan)
    finally:
        run.__globals__["BIG"] = 300 * 1024 * 1024
    assert r["ok"] and "over 300 MB" in r["warn"]
    assert not list(out.glob("*.part"))


@age
def test_M2_required_sources_missing_fail_the_check(tmp_path: Path) -> None:
    key = tmp_path / "k" / "backup.key"
    B["keygen"](key)
    plan = _plan(tmp_path, key)
    plan["sources"].append(["ref", str(tmp_path / "nope")])  # REF_DIR missing on disk
    r = B["run"](plan)
    v = B["verify"](Path(plan["out_dir"]) / r["local"]["archive"], key, tmp_path)
    assert not v["ok"] and v["missing_sources"] == ["ref"]


# ------------------------------------------------------------------ monitoring / app
def test_F9_host_alerts() -> None:
    from trader.server_status import host_alerts

    now = datetime(2026, 11, 22, 12, tzinfo=UTC)
    ok = {"disk_used_pct": 40, "mem_used_pct": 50, "backup_age_h": 3}
    assert host_alerts(ok, now - timedelta(minutes=1), now) == []
    bad = {"disk_used_pct": 85, "mem_used_pct": 95, "backup_age_h": 30}
    msgs = " | ".join(host_alerts(bad, now - timedelta(minutes=9), now))
    for must in ("worker silent", "disk 85%", "memory 5% available", "30 hours"):
        assert must in msgs, must


def test_F9_page_host_once_an_hour() -> None:
    from trader.app_store import set_state
    from trader.journal import Journal
    from trader.server_status import page_host

    j = Journal.sqlite()
    now = datetime(2026, 11, 22, 12, tzinfo=UTC)
    set_state(j, "host-status", {"disk_used_pct": 90}, now)
    said: list[str] = []
    assert page_host(j, said.append, now) and said
    later = now + timedelta(minutes=10)
    set_state(j, "host-status", {"disk_used_pct": 90}, later)  # the worker writes every 30 s
    assert page_host(j, said.append, later) == []  # the same page within the hour
    later = now + timedelta(minutes=70)
    set_state(j, "host-status", {"disk_used_pct": 90}, later)
    assert page_host(j, said.append, later)


def test_F13_ci_on_the_server_branch_and_the_update_card() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "bigwins-fast" in ci and "ci-ok/" in ci and "ci-fail/" in ci
    from trader.app_pages import _ci_line

    assert "CI passed" in _ci_line({"ci": "green"})
    assert "FAILED" in _ci_line({"ci": "red"}) and "not known yet" in _ci_line({})
    assert "UPD_CI" in SH and "ls-remote" in SH


def test_L6_claude_files_are_infra_in_both_classifiers() -> None:
    from trader.strategy_version import is_trading_path

    cls: dict[str, Any] = runpy.run_path(str(ROOT / "deploy" / "classify.py"))
    for f in (".claude/settings.json", "CLAUDE.md"):
        assert is_trading_path(f) and cls["is_trading_path"](f)


def test_M3_backups_screen_shows_the_key_fingerprint_until_saved() -> None:
    from trader.app_store import set_state
    from trader.backups import clear_sealed, key_saved, record_result
    from trader.journal import Journal

    j = Journal.sqlite()
    now = datetime(2026, 11, 22, 12, tzinfo=UTC)
    assert not key_saved(j, "abcdef012345")
    clear_sealed(j, now, "owner", "abcdef012345")
    assert key_saved(j, "abcdef012345") and not key_saved(j, "999999999999")
    r = record_result(j, {"ok": "yes", "files": "<b>", "seconds": True, "key_fp": "<x>"}, now)
    assert r["ok"] is False and r["files"] is None and r["seconds"] is None and r["key_fp"] == ""
    set_state(j, "host-status", {"key_fp": "abcdef012345"}, now)
    _ = json


def test_L2_unclaimed_sealed_key_is_cleared_by_the_loop() -> None:
    from tests.test_bf_app_actions import _setup
    from trader.app_store import get_state, set_state

    j, _, ctl, _, _ = _setup()
    set_state(j, "backup-key-sealed", {"sealed": "ab" * 60}, ctl.clock() - timedelta(minutes=11))
    ctl.process()
    st = get_state(j, "backup-key-sealed")
    assert st is not None and st[0] == {}
