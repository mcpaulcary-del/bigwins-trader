"""BF-D82..BF-D87: the disaster-recovery fixes (DR review of 24 Nov 2026, M1-M9, S1-S5).

Owner presence and the incapacity default (owner decision 24 Nov 2026, option b), the
memorised passphrase and Lock actions, new-totp, update signatures, the worker's
heartbeat before the trader runs, the presence ping, backups with the code bundle and a
second off-site copy, renewal reminders. No strategy rule or parameter changes."""

from __future__ import annotations

import io
import json
import os
import runpy
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests.test_bf_app_actions import OWNER, _post, _session, _setup
from tests.test_bf_execution import SEED, T_APPROVE
from trader import presence as pr
from trader.app_store import get_state, set_state
from trader.approval import Incoming, TotpVerifier, totp
from trader.journal import Journal
from trader.passphrase import hash_passphrase, stored_hash, verify
from trader.risk import SafetyLevel
from trader.secrets import KNOWN_SECRETS, SecretValue

REPO = Path(__file__).resolve().parent.parent
SH = REPO / "deploy" / "bigwins.sh"
T0 = datetime.fromisoformat("2027-03-01T09:00:00+11:00")
PHRASE = "purple kettle mountain river"


# ---------------------------------------------------------------- the strategy is frozen


def test_BF_D82_strategy_hash_and_settings_hash_unchanged() -> None:
    """EMG2-18 + shield + C6 is frozen until 1 Jan 2027: these safety-layer changes leave the
    strategy hash and the strategy settings hash exactly as before (e3e496b)."""
    from trader.strategy_version import config_hash, strategy_hash
    from trader.yamlio import load_yaml

    assert strategy_hash(REPO) == "a50dfa0b4eb1"
    cfg = load_yaml((REPO / "config" / "bfast.yaml").read_text()) or {}
    assert config_hash(cfg) == "02589a19293b"
    assert cfg["app"]["presence_days"] == 14  # in the app's own (non-trading) section


def test_BF_D82_no_strategy_file_changed_since_e3e496b() -> None:
    from trader.strategy_version import STRATEGY_FILES

    try:
        files = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", "e3e496b"],
                               capture_output=True, text=True, check=True).stdout.split()  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("the base commit is not in this checkout (shallow clone)")
    assert not [f for f in files for s in STRATEGY_FILES if f.startswith(s)]


# ---------------------------------------------------------------- owner presence (BF-D82)


def _hook(j: Journal, days: int = 14, warn: int = 10) -> tuple[pr.PresenceHook, list[str]]:
    said: list[str] = []
    return pr.PresenceHook(j, lambda t, k, link: said.append(f"{k}|{t}"), days, warn), said


def test_BF_D82_warning_on_day_10_pause_on_day_14_once_each() -> None:
    j = Journal.sqlite()
    hook, said = _hook(j)
    assert hook.tick(T0) == []  # the clock starts: no pause on the first run
    assert hook.tick(T0 + timedelta(days=9, hours=23)) == []
    assert hook.tick(T0 + timedelta(days=10, minutes=1)) == ["warned"]
    assert hook.tick(T0 + timedelta(days=11)) == []  # once
    assert said[0].startswith("page|PAGE no owner action") and "I'm here" in said[0]
    assert "Paper account" in said[0]  # labelled as paper
    assert j.safety_level() is SafetyLevel.NORMAL
    assert hook.tick(T0 + timedelta(days=14, minutes=1)) == ["paused"]
    assert j.safety_level() is SafetyLevel.HALTED_BUYS
    assert j.safety_reason().startswith("owner presence:")
    assert "Nothing is sold automatically" in said[-1] and "Resume" in said[-1]
    assert hook.tick(T0 + timedelta(days=20)) == []  # one page per absence
    # nothing else lowers it: only /resume with a code (below)


@pytest.mark.parametrize(
    "stricter", [SafetyLevel.KILLED, SafetyLevel.HALTED_INTEGRITY, SafetyLevel.HALTED_LINE]
)
def test_BF_D82_the_pause_never_lowers_a_stricter_level(stricter: SafetyLevel) -> None:
    j = Journal.sqlite()
    hook, said = _hook(j)
    hook.tick(T0)
    j.set_safety(stricter, "owner /kill", "app:x", T0 + timedelta(days=1))
    assert hook.tick(T0 + timedelta(days=15)) == ["paused"]
    assert j.safety_level() is stricter and j.safety_reason() == "owner /kill"
    assert f"stays {stricter.value}" in said[-1]


@pytest.mark.parametrize("weaker", [SafetyLevel.NORMAL, SafetyLevel.PAUSED])
def test_BF_D82_the_pause_raises_normal_and_paused(weaker: SafetyLevel) -> None:
    j = Journal.sqlite()
    hook, _ = _hook(j)
    hook.tick(T0)
    j.set_safety(weaker, "owner /pause", "app:x", T0 + timedelta(days=1))
    hook.tick(T0 + timedelta(days=15))
    assert j.safety_level() is SafetyLevel.HALTED_BUYS


def test_BF_D82_an_l11_halt_is_taken_over_so_the_staged_test_cannot_clear_it() -> None:
    """The L11 staged test clears only HALTED_BUYS whose reason is its own ("book monitor:"
    / "L11"); the presence pause rewrites the same level with its own reason."""
    j = Journal.sqlite()
    hook, _ = _hook(j)
    hook.tick(T0)
    j.set_safety(SafetyLevel.HALTED_BUYS, "book monitor: BW-RSK-20", "risk", T0 + timedelta(days=1))
    hook.tick(T0 + timedelta(days=15))
    assert j.safety_level() is SafetyLevel.HALTED_BUYS
    assert not j.safety_reason().startswith(("book monitor:", "L11"))


def test_BF_D82_any_accepted_owner_action_resets_the_clock() -> None:
    j, _bot, ctl, _bid, _ = _setup()
    hook, _ = _hook(j)
    hook.tick(T0)
    ctl.clock_box["t"] = T0 + timedelta(days=13)  # type: ignore[attr-defined]
    st, page = _post(ctl, {"a": "here"})
    assert st == 200 and "Thank you" in page
    p = pr.status(j)
    assert p.last == T0 + timedelta(days=13) and p.what
    assert hook.tick(T0 + timedelta(days=14, hours=1)) == []
    assert j.safety_level() is SafetyLevel.NORMAL
    # a wrong code is not an owner action
    ctl.clock_box["t"] = T0 + timedelta(days=20)  # type: ignore[attr-defined]
    _post(ctl, {"a": "re", "code": "000000"})
    assert pr.status(j).last == T0 + timedelta(days=13)
    # Pause is one tap and counts
    _post(ctl, {"a": "pa"})
    assert pr.status(j).last == T0 + timedelta(days=20)


def test_BF_D82_opening_a_page_does_not_count() -> None:
    j, _bot, ctl, _bid, _ = _setup()
    for path in ("/act", "/act/confirm?a=here", "/act/alerts"):
        ctl.respond("GET", path, {"Tailscale-User-Login": OWNER})
    assert get_state(j, pr.PRESENCE) is None


def test_BF_D82_resume_from_the_pause_needs_the_code_and_the_passphrase() -> None:
    j, _bot, ctl, _bid, pages = _setup()
    ctl.passphrase = hash_passphrase(PHRASE, b"s" * 16, 1000)
    hook, _ = _hook(j)
    hook.tick(T0)
    hook.tick(T0 + timedelta(days=15))
    assert j.safety_level() is SafetyLevel.HALTED_BUYS
    t = T0 + timedelta(days=16)
    ctl.clock_box["t"] = t  # type: ignore[attr-defined]
    st, page = _post(ctl, {"a": "re", "code": totp(SEED, t)})
    assert "enter your passphrase" in page and j.safety_level() is SafetyLevel.HALTED_BUYS
    st, page = _post(ctl, {"a": "re", "code": totp(SEED, t), "pp": "wrong words here"})
    assert "wrong passphrase" in page and j.safety_level() is SafetyLevel.HALTED_BUYS
    st, page = _post(ctl, {"a": "re", "code": "123456", "pp": PHRASE})
    assert "refused" in page and j.safety_level() is SafetyLevel.HALTED_BUYS
    t2 = t + timedelta(seconds=60)
    ctl.clock_box["t"] = t2  # type: ignore[attr-defined]
    st, page = _post(ctl, {"a": "re", "code": totp(SEED, t2), "pp": PHRASE})
    assert "re-armed: NORMAL" in page and j.safety_level() is SafetyLevel.NORMAL
    # the passphrase never reaches the inbox or the journal state
    from trader.app_store import inbox_rows

    assert PHRASE not in json.dumps([dict(r) for r in inbox_rows(j)], default=str)


def test_BF_D82_resume_without_a_passphrase_set_needs_the_code_only() -> None:
    j, _bot, ctl, _bid, _ = _setup()
    j.set_safety(SafetyLevel.HALTED_BUYS, pr.REASON.format(days=14), "presence", T_APPROVE)
    assert "refused" in _post(ctl, {"a": "re", "code": "000000"})[1]
    assert j.safety_level() is SafetyLevel.HALTED_BUYS
    ctl.clock_box["t"] = T_APPROVE + timedelta(seconds=60)  # type: ignore[attr-defined]
    _post(ctl, {"a": "re", "code": totp(SEED, T_APPROVE + timedelta(seconds=60))})
    assert j.safety_level() is SafetyLevel.NORMAL


def test_BF_D82_presence_ping_stops_after_the_days() -> None:
    j = Journal.sqlite()
    assert pr.status(j).ok(T0)  # not tracking yet: ping (the second contact sees a dead server)
    pr.start_tracking(j, T0)
    assert pr.status(j).ok(T0 + timedelta(days=13, hours=23))
    assert not pr.status(j).ok(T0 + timedelta(days=14))
    pr.record_action(j, T0 + timedelta(days=15), "I'm here")
    assert pr.status(j).ok(T0 + timedelta(days=16))
    assert not pr.status(j, days=7).ok(T0 + timedelta(days=22))


def test_BF_D82_status_op_prints_presence_ok_only_within_the_days(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from trader.bfast_cli import main

    url = f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"
    j = Journal.sqlite(str(tmp_path / "j.sqlite"))
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    assert main(["server-jobs", "status", "--journal", url]) == 0
    assert "presence-ok" in capsys.readouterr().out.split("\n")
    pr.start_tracking(j, datetime.now(T0.tzinfo) - timedelta(days=15))
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    assert main(["server-jobs", "status", "--journal", url]) == 0
    assert "presence-ok" not in capsys.readouterr().out.split("\n")


def test_BF_D82_config_bounds() -> None:
    from pydantic import ValidationError

    from trader.bfast_config import AppCfg

    assert AppCfg().presence_days == 14 and AppCfg().presence_warn_days == 10
    with pytest.raises(ValidationError):
        AppCfg(presence_days=14, presence_warn_days=14)
    with pytest.raises(ValidationError):
        AppCfg(presence_days=1)


# ---------------------------------------------------------------- passphrase and Lock (BF-D83)


def test_BF_D83_passphrase_hash_from_the_server_tool_verifies_in_the_trader(tmp_path: Path) -> None:
    tool = runpy.run_path(str(REPO / "deploy" / "secret_tool.py"))
    from trader import passphrase as tp

    assert tool["ITERATIONS"] == tp.ITERATIONS and tool["PREFIX"] == tp.PREFIX
    assert tool["MIN_LENGTH"] == tp.MIN_LENGTH
    f = tmp_path / "secrets" / "app_passphrase"
    r = subprocess.run([sys.executable, "-I", str(REPO / "deploy" / "secret_tool.py"),
                        "passphrase", str(f)], input=f"{PHRASE}\n{PHRASE}\n", text=True,
                       capture_output=True, check=False)  # fmt: skip
    assert r.returncode == 0 and PHRASE not in r.stdout + r.stderr
    stored = f.read_text()
    assert PHRASE not in stored and (f.stat().st_mode & 0o777) == 0o444
    h = stored_hash(SecretValue(stored))
    assert h is not None and verify(h, PHRASE) and not verify(h, PHRASE + "x")
    assert stored_hash(SecretValue("none")) is None and not verify(None, PHRASE)
    bad = subprocess.run([sys.executable, "-I", str(REPO / "deploy" / "secret_tool.py"),
                          "passphrase", str(f)], input="short\nshort\n", text=True,
                         capture_output=True, check=False)  # fmt: skip
    assert bad.returncode == 1 and "too short" in bad.stderr and f.read_text() == stored
    diff = subprocess.run([sys.executable, "-I", str(REPO / "deploy" / "secret_tool.py"),
                           "passphrase", str(f)], input=f"{PHRASE}\n{PHRASE}!\n", text=True,
                          capture_output=True, check=False)  # fmt: skip
    assert diff.returncode == 1 and "differ" in diff.stderr


def test_BF_D83_passphrase_is_asked_for_the_riskiest_actions_only() -> None:
    _j, _bot, ctl, bid, _ = _setup()
    ctl.passphrase = hash_passphrase(PHRASE, b"s" * 16, 1000)
    sid_tok = _session(ctl)
    for a in ("re", "srv:update", "srv:rollback", "srv:backup_key", "srv:claude_remote"):
        _, _, body = ctl.respond("GET", f"/act/confirm?a={a}",
                                 {"Tailscale-User-Login": OWNER, "Cookie": f"bw_sid={sid_tok[0]}"})  # fmt: skip
        assert 'name="pp"' in body.decode(), a
    _, _, body = ctl.respond("GET", f"/act/confirm?a=ok&b={bid}&n=all",
                             {"Tailscale-User-Login": OWNER})  # fmt: skip
    assert 'name="pp"' not in body.decode()  # an approval needs the code only
    _, _, body = ctl.respond("GET", "/act/confirm?a=pa", {"Tailscale-User-Login": OWNER})
    assert 'name="pp"' not in body.decode() and 'name="code"' not in body.decode()


def test_BF_D83_wrong_passphrases_share_the_wrong_code_lock_out() -> None:
    j, _bot, ctl, bid, pages = _setup()
    ctl.passphrase = hash_passphrase(PHRASE, b"s" * 16, 1000)
    j.set_safety(SafetyLevel.PAUSED, "owner /pause", "app:x", T_APPROVE)
    _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": "000001"})  # a wrong code
    _post(ctl, {"a": "re", "code": totp(SEED, T_APPROVE), "pp": "not it at all"})
    assert ctl.locked(T_APPROVE) is None
    _post(ctl, {"a": "re", "code": totp(SEED, T_APPROVE), "pp": "still not it"})
    assert ctl.locked(T_APPROVE) is not None  # 3 wrong in 15 minutes: one count for both
    assert any("LOCKED" in p for p in pages)
    st, page = _post(ctl, {"a": "re", "code": totp(SEED, T_APPROVE), "pp": PHRASE})
    assert "locked" in page and j.safety_level() is SafetyLevel.PAUSED
    assert len(get_state(j, "app-code-fails")[0]) == 3  # type: ignore[index]


def test_BF_D83_lock_blocks_approvals_and_rearming_but_never_pause_kill_stop() -> None:
    j, _bot, ctl, bid, _ = _setup()
    st, page = _post(ctl, {"a": "lock"})
    assert "Actions locked" in page and ctl.actions_locked()
    _, _, body = ctl.respond("GET", f"/act/confirm?a=ok&b={bid}&n=all",
                             {"Tailscale-User-Login": OWNER})  # fmt: skip
    assert "Actions are locked" in body.decode() and 'name="code"' not in body.decode()
    st, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": totp(SEED, T_APPROVE)})
    assert "locked" in page and j.approvals(bid) == []
    _post(ctl, {"a": "pa"})
    assert j.safety_level() is SafetyLevel.PAUSED  # Pause: one tap, no unlock
    _post(ctl, {"a": "so", "confirm": "yes"})
    _post(ctl, {"a": "ki", "confirm": "yes"})
    assert j.safety_level() is SafetyLevel.KILLED  # Kill: no unlock needed
    t = T_APPROVE + timedelta(seconds=40)
    ctl.clock_box["t"] = t  # type: ignore[attr-defined]
    st, page = _post(ctl, {"a": "re", "code": totp(SEED, t)})
    assert "locked" in page and j.safety_level() is SafetyLevel.KILLED  # re-arm waits
    st, page = _post(ctl, {"a": "unlock", "code": totp(SEED, t)})
    assert "unlocked" in page and not ctl.actions_locked()
    t2 = t + timedelta(seconds=60)
    ctl.clock_box["t"] = t2  # type: ignore[attr-defined]
    _post(ctl, {"a": "re", "code": totp(SEED, t2)})
    assert j.safety_level() is SafetyLevel.NORMAL


def test_BF_D83_unlock_needs_the_passphrase_when_set() -> None:
    _j, _bot, ctl, _bid, _ = _setup()
    ctl.passphrase = hash_passphrase(PHRASE, b"s" * 16, 1000)
    _post(ctl, {"a": "lock"})
    assert "passphrase" in _post(ctl, {"a": "unlock", "code": totp(SEED, T_APPROVE)})[1]
    assert ctl.actions_locked()
    _post(ctl, {"a": "unlock", "code": totp(SEED, T_APPROVE), "pp": PHRASE})
    assert not ctl.actions_locked()


def test_BF_D83_telegram_follows_the_lock_and_the_passphrase_rule() -> None:
    from tests.test_bf_execution import CHAT

    j, bot, ctl, bid, _ = _setup()
    bot.gate = ctl.telegram_gate
    seen: list[str] = []
    bot.on_owner = lambda at, cmd: seen.append(cmd)
    _post(ctl, {"a": "lock"})
    r = bot.handle(Incoming(CHAT, f"/ok {bid} all {totp(SEED, T_APPROVE)}", T_APPROVE))
    assert r.startswith("refused: actions are locked") and j.approvals(bid) == []
    assert bot.handle(Incoming(CHAT, "/pause", T_APPROVE)).startswith("PAUSED")
    assert seen == ["/pause"]  # an accepted Telegram command is an owner action
    set_state(j, "actions-lock", {"locked": False}, T_APPROVE)
    ctl.passphrase = hash_passphrase(PHRASE, b"s" * 16, 1000)
    r = bot.handle(Incoming(CHAT, f"/resume {totp(SEED, T_APPROVE)}", T_APPROVE))
    assert "in the app" in r and j.safety_level() is SafetyLevel.PAUSED


def test_BF_D83_new_totp_invalidates_the_old_seed(tmp_path: Path) -> None:
    tool = runpy.run_path(str(REPO / "deploy" / "secret_tool.py"))
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "totp_seed").write_text(SEED)
    (d / "totp_seed").chmod(0o444)
    inode = (d / "totp_seed").stat().st_ino
    uri = tool["new_totp"](d)
    new = (d / "totp_seed").read_text()
    assert new != SEED and f"secret={new}" in uri and uri.startswith("otpauth://totp/")
    assert (d / "totp_seed").stat().st_ino == inode  # in place: the bind mount keeps it
    assert ((d / "totp_seed").stat().st_mode & 0o777) == 0o444
    old_code = totp(SEED, T_APPROVE)
    v = TotpVerifier(SecretValue(new))  # the trader after its restart
    assert not v.verify(old_code, T_APPROVE) or totp(new, T_APPROVE) == old_code
    assert v.verify(totp(new, T_APPROVE + timedelta(seconds=30)), T_APPROVE + timedelta(seconds=30))
    sh = SH.read_text()
    assert "cmd_new_totp" in sh and "dc restart trader dashboard" in sh
    assert 'secret_tool.py" new-totp "$SECRETS" | qrencode' in sh  # the seed goes only to the QR


def test_BF_D87_secret_list_matches_the_guide() -> None:
    assert {"smtp_password", "object_store_token", "rclone_config"}.isdisjoint(KNOWN_SECRETS)
    assert {"app_passphrase", "healthchecks_presence_url"} <= KNOWN_SECRETS
    b6 = (REPO / "docs" / "GO_LIVE_GUIDE.md").read_text().split("### B6.")[1].split("### B7.")[0]
    for name in KNOWN_SECRETS:
        assert f"`{name}`" in b6, name


# ---------------------------------------------------------------- the host worker (bash)


def _bash(
    tmp: Path, script: str, extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run bigwins.sh functions with the paths moved into ``tmp`` and curl stubbed."""
    bin_ = tmp / "bin"
    bin_.mkdir(exist_ok=True)
    (bin_ / "curl").write_text(f'#!/bin/sh\necho "$@" >> "{tmp}/curl.log"\nexit 0\n')
    (bin_ / "curl").chmod(0o755)
    for d in ("deploy/secrets", "state", "etc"):
        (tmp / d).mkdir(parents=True, exist_ok=True)
    pre = (f'source "{SH}" __lib__ >/dev/null; DEPLOY="{tmp}/deploy"; SECRETS="{tmp}/deploy/secrets"; '
           f'STATE="{tmp}/state"; ETC="{tmp}/etc"; SIGNERS="{tmp}/etc/allowed_signers"; '
           f'SIGN_ENFORCE="{tmp}/etc/require_signed"; ')  # fmt: skip
    env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", **(extra or {})}
    return subprocess.run(["bash", "-c", pre + script], capture_output=True, text=True,
                          env=env, check=False)  # fmt: skip


def _pings(tmp: Path) -> list[str]:
    log = tmp / "curl.log"
    return log.read_text().splitlines() if log.is_file() else []


def test_BF_D87_worker_pings_the_heartbeat_while_the_trader_is_the_placeholder(
    tmp_path: Path,
) -> None:
    (tmp_path / "deploy" / "secrets").mkdir(parents=True)
    (tmp_path / "deploy" / "secrets" / "healthchecks_url").write_text("https://hc-ping.com/abc")
    (tmp_path / "deploy" / ".env").write_text("JOURNAL_DB=x\n")  # TRADER_CMD unset: sleep
    r = _bash(tmp_path, "worker_heartbeat; worker_heartbeat")
    assert r.returncode == 0, r.stderr
    assert len(_pings(tmp_path)) == 1 and "hc-ping.com/abc" in _pings(tmp_path)[0]  # once / 5 min
    (tmp_path / "state" / "hb_ping_at").write_text("1")  # long ago
    _bash(tmp_path, "worker_heartbeat")
    assert len(_pings(tmp_path)) == 2
    # the real trader pings itself: the worker does not mask a dead trader
    (tmp_path / "state" / "hb_ping_at").write_text("1")
    (tmp_path / "deploy" / ".env").write_text("TRADER_CMD=trader-bf run --start 2026-12-01\n")
    _bash(tmp_path, "worker_heartbeat")
    assert len(_pings(tmp_path)) == 2
    (tmp_path / "deploy" / ".env").write_text("TRADER_CMD=sleep infinity\n")
    (tmp_path / "deploy" / "secrets" / "healthchecks_url").write_text("none")
    _bash(tmp_path, "worker_heartbeat")
    assert len(_pings(tmp_path)) == 2  # off when the URL is none


def test_BF_D82_worker_presence_ping_once_a_day_and_only_when_present(tmp_path: Path) -> None:
    sec = tmp_path / "deploy" / "secrets"
    sec.mkdir(parents=True)
    _bash(tmp_path, 'presence_ping "presence-ok"')
    assert _pings(tmp_path) == []  # not set up: nothing
    (sec / "healthchecks_presence_url").write_text("https://hc-ping.com/presence")
    _bash(tmp_path, 'presence_ping "status stored"')
    assert _pings(tmp_path) == []  # the owner is away: no ping, healthchecks.io tells the contact
    _bash(tmp_path, "presence_ping $'status stored\\npresence-ok'; presence_ping 'presence-ok'")
    assert len(_pings(tmp_path)) == 1 and "presence" in _pings(tmp_path)[0]  # once a day
    sh = SH.read_text()
    assert 'presence_ping "$st"' in sh and "worker_heartbeat  #" in sh


HAS_SSH_KEYGEN = shutil.which("ssh-keygen") is not None


def _signed_repo(tmp: Path) -> tuple[Path, str, str, str]:
    repo = tmp / "repo"
    repo.mkdir()
    key = tmp / "signkey"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "engineer", "-f",
                    str(key)], check=True)  # fmt: skip

    def git(*a: str) -> str:
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True,
                              check=True).stdout.strip()  # fmt: skip

    git("init", "-q")
    git("config", "user.email", "engineer@example.invalid")
    git("config", "user.name", "Engineer")
    git("config", "gpg.format", "ssh")
    git("config", "user.signingkey", str(key))
    git("config", "gpg.ssh.program", "ssh-keygen")  # not the machine's own signing helper
    (repo / "a.txt").write_text("1")
    git("add", "a.txt")
    git("commit", "-q", "-S", "-m", "signed")
    good = git("rev-parse", "HEAD")
    (repo / "a.txt").write_text("2")
    git("-c", "commit.gpgsign=false", "commit", "-q", "-a", "--no-gpg-sign", "-m", "unsigned")
    bad = git("rev-parse", "HEAD")
    return repo, good, bad, (tmp / "signkey.pub").read_text().strip()


@pytest.mark.skipif(not HAS_SSH_KEYGEN, reason="ssh-keygen is not installed")
def test_BF_D84_verify_commit_gating_warn_and_enforce(tmp_path: Path) -> None:
    repo, good, bad, pub = _signed_repo(tmp_path)

    def run(s: str) -> subprocess.CompletedProcess[str]:
        return _bash(tmp_path, f'REPO="{repo}"; {s}')

    # no key on the server: every commit is "none"; warn mode applies with a warning
    r = run(f"sign_mode; commit_sig {bad}; check_signed {bad}; echo rc=$?")
    assert (
        r.stdout.split()[:2] == ["nokey", "none"] and "warning" in r.stdout and "rc=0" in r.stdout
    )
    (tmp_path / "etc" / "allowed_signers").write_text(f'engineer namespaces="git" {pub}\n')
    r = run(f"sign_mode; commit_sig {good}; commit_sig {bad}")
    assert r.stdout.split() == ["warn", "good", "bad"], r.stderr
    r = run(f"check_signed {bad}; echo rc=$?")
    assert "warning" in r.stdout and "rc=0" in r.stdout  # warn: applied anyway
    (tmp_path / "etc" / "require_signed").write_text("")
    r = run(f"sign_mode; check_signed {bad}; echo rc=$?")
    assert r.stdout.startswith("enforce") and "refused" in r.stdout and "rc=1" in r.stdout
    r = run(f"check_signed {good}; echo rc=$?")
    assert "signature: good" in r.stdout and "rc=0" in r.stdout
    # enforce without a key refuses everything (fails closed)
    (tmp_path / "etc" / "allowed_signers").unlink()
    r = run(f"check_signed {good}; echo rc=$?")
    assert "refused" in r.stdout and "rc=1" in r.stdout


def test_BF_D84_both_update_paths_check_the_signature_before_moving() -> None:
    sh = SH.read_text()
    upd = sh.split("update_to() {")[1].split("\n}\n")[0]
    assert upd.index('check_signed "$commit"') < upd.index("merge --ff-only")
    assert "update_min_age_h" in upd and "seen_hours" in upd
    man = sh.split("do_update() {")[1].split("\n}\n")[0]
    assert man.index('check_signed "$tip"') < man.index("merge --ff-only")
    assert "pull --ff-only" not in man  # nothing is merged before the check
    # the ci-ok tags are information only (anyone who can push can make one)
    from trader.app_pages import _ci_line

    assert "information only" in _ci_line({"ci": "green", "signed": "bad"})
    assert "Not signed" in _ci_line({"ci": "green", "signed": "bad"})


def test_BF_D84_min_age_live_24_paper_0(tmp_path: Path) -> None:
    cfg = tmp_path / "bfast.yaml"
    cfg.write_text("mode: paper\n")
    r = _bash(tmp_path, f'CONFIG="{cfg}"; LOCAL=/nonexistent; update_min_age_h')
    assert r.stdout.strip() == "0"
    cfg.write_text("mode: live\n")
    r = _bash(tmp_path, f'CONFIG="{cfg}"; LOCAL=/nonexistent; update_min_age_h')
    assert r.stdout.strip() == "24"
    (tmp_path / "etc" / "update_min_age_hours").write_text("48")
    r = _bash(tmp_path, f'CONFIG="{cfg}"; LOCAL=/nonexistent; update_min_age_h')
    assert r.stdout.strip() == "48"
    sha = "a" * 40
    (tmp_path / "state" / "seen_remote").write_text(f"{sha} 1\n")
    r = _bash(tmp_path, f"seen_hours {sha}; seen_hours {'b' * 40}")
    assert int(r.stdout.split()[0]) > 1000 and r.stdout.split()[1] == "0"


def test_BF_D84_one_alert_per_new_remote_commit() -> None:
    j = Journal.sqlite()
    hook, said = _hook(j)
    u = {"remote": "c" * 40, "head": "d" * 40, "ahead": 2, "subject": "Fix things",
         "signed": "good"}  # fmt: skip
    set_state(j, "update-available", u, T0)
    assert hook._new_code(T0) == ["c" * 40]
    assert hook._new_code(T0) == []  # once per commit
    # BF-D90: an update that needs approval says "Update ready ... tap to review and approve"
    assert said[-1].startswith("info|Update ready: Fix things") and "signed by" in said[-1]
    assert "New code on GitHub (not applied)" in said[-1]
    set_state(j, "update-available", {**u, "remote": "e" * 40, "signed": "bad"}, T0)
    hook._new_code(T0)
    assert said[-1].startswith("page|PAGE Update ready") and "NOT signed" in said[-1]
    set_state(j, "update-available", {**u, "remote": "d" * 40}, T0)
    assert hook._new_code(T0) == []  # nothing new


def test_BF_D85_claude_remote_stops_by_itself(tmp_path: Path) -> None:
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    (bin_ / "tmux").write_text(f'#!/bin/sh\necho "$@" >> "{tmp_path}/tmux.log"\nexit 0\n')
    (bin_ / "tmux").chmod(0o755)
    r = _bash(tmp_path, 'claude_hours; claude_autostop; cat "$STATE/claude_remote_started"')
    assert r.stdout.split()[0] == "2"  # default 2 hours; the clock starts on first sight
    (tmp_path / "state" / "claude_remote_started").write_text("1")
    r = _bash(tmp_path, "claude_autostop")
    assert "stopped after 2 hours" in r.stdout
    assert "kill-session -t remote" in (tmp_path / "tmux.log").read_text()
    sh = SH.read_text()
    assert "claude_remote_live" in sh and "is_live" in sh  # off by default when live


# ---------------------------------------------------------------- backups (BF-D86)


B = runpy.run_path(str(REPO / "deploy" / "backup.py"))
HAS_AGE = shutil.which("age") is not None and shutil.which("age-keygen") is not None


@pytest.mark.skipif(not HAS_AGE, reason="age is not installed")
def test_BF_D86_second_offsite_copy_code_bundle_and_notes(tmp_path: Path) -> None:
    src = tmp_path / "src"
    (src / "config").mkdir(parents=True)
    (src / "config" / "x.yaml").write_text("a: 1\n")
    subprocess.run(["git", "-C", str(REPO), "bundle", "create", str(tmp_path / "code.bundle"),
                    "HEAD"], check=True, capture_output=True)  # fmt: skip
    (src / "info").mkdir()
    (src / "info" / "notice.txt").write_text("headline")
    key = tmp_path / "k" / "backup.key"
    B["keygen"](key)
    plan = {"out_dir": str(tmp_path / "out"), "key_file": str(key),
            "remote": str(tmp_path / "onedrive"), "remote2": str(tmp_path / "b2"),
            "notes": ["info archive not backed up: 900 MB is over 500 MB"],
            "pg_dump": [sys.executable, "-c", "print('CREATE TABLE bf_events (id int);')"],
            "row_counts": {"bf_events": 0},
            "sources": [["config", str(src / "config")], ["code.bundle", str(tmp_path / "code.bundle")],
                        ["info_archive", str(src / "info")]]}  # fmt: skip
    res = B["run"](plan)
    assert res["ok"] and res["remote"]["ok"] and res["remote2"]["ok"], res
    arch = res["local"]["archive"]
    assert (tmp_path / "b2" / arch).is_file() and (tmp_path / "onedrive" / arch).is_file()
    assert res["notes"] == plan["notes"]
    dest = tmp_path / "restored"
    B["restore"](tmp_path / "out" / arch, dest, key)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(dest / "code.bundle"), str(clone)], check=True)
    assert (clone / "deploy" / "bigwins.sh").is_file()  # the code without GitHub
    assert (dest / "info_archive" / "notice.txt").read_text() == "headline"
    # a broken second destination fails the backup loudly
    plan["remote2"] = "/proc/nope/b2"
    assert not B["run"](plan)["ok"]


def test_BF_D86_archive_check_and_restore_paths(tmp_path: Path) -> None:
    good = tmp_path / "bigwins-20270301-120000.tar.age"
    good.write_bytes(b"age-encryption.org/v1\n-> X25519 abc\n")
    page = tmp_path / "page.html"
    page.write_text("<html>Sign in to OneDrive</html>")
    r = _bash(tmp_path, f'archive_ok "{good}" && echo good; archive_ok "{page}" || echo page')
    assert r.stdout.split() == ["good", "page"]
    sh = SH.read_text()
    restore = sh.split("cmd_restore() {")[1].split("\n}\n")[0]
    assert "code.bundle" in restore and "info_archive" in restore and "od2_path" in restore
    test = sh.split("do_restore_test() {")[1].split("\n}\n")[0]
    assert "onedrive_verify" in test  # the weekly test checks the OneDrive copy too
    backup = sh.split("do_backup() {")[1].split("\n}\n")[0]
    assert "bundle create" in backup and "INFO_CAP_MB" in backup and "remote2" in backup


# ---------------------------------------------------------------- reminders and screens


def test_BF_D86_renewal_reminders_once_per_step() -> None:
    j = Journal.sqlite()
    hook, said = _hook(j)
    today = T0.date()
    set_state(j, "reminders", {"flex_token": (today + timedelta(days=20)).isoformat(),
                               "card": "not a date"}, T0)  # fmt: skip
    assert len(hook._reminders(T0)) == 1 and "IBKR Flex token ends in 20 days" in said[-1]
    assert hook._reminders(T0 + timedelta(days=1)) == []  # same 30-day step
    assert len(hook._reminders(T0 + timedelta(days=14))) == 1  # the 7-day step
    assert len(hook._reminders(T0 + timedelta(days=25))) == 1  # past
    assert "expired" in said[-1]
    assert pr.reminders_due({"card": date(2030, 1, 1)}, today) == []


def test_BF_D86_reminders_page_saves_dates_without_a_code() -> None:
    j, _bot, ctl, _bid, _ = _setup()
    st, page = _post(ctl, {"flex_token": "2027-11-20", "card": ""}, path="/act/reminders")
    assert st == 200 and "saved" in page
    assert pr.reminder_dates(j) == {"flex_token": date(2027, 11, 20)}
    st, page = _post(ctl, {"flex_token": "20/11/2027"}, path="/act/reminders")
    assert "not a date" in page


def test_BF_D82_health_and_home_show_presence_lock_and_passphrase_nag() -> None:
    from trader.app_ops import phone_safety_section, presence_section
    from trader.app_pages import Extras, dr_rows, lock_note

    j = Journal.sqlite()
    pr.start_tracking(j, T0)
    x = Extras(viewer=OWNER, action_logins=frozenset({OWNER}))
    x.presence = pr.status(j)
    x.passphrase_set = False
    v: Any = type("V", (), {"now": T0 + timedelta(days=11), "live": False, "demo": False})()
    html = presence_section(v, x)
    assert "11</b>&nbsp;days since your last action" in html and "15 Mar 2027" in html
    assert (
        "I'm here" in html
        and "owner presence · paper" in html
        and "&lt;span" not in html
        and "Opening a page does not count" in html
    )
    nag = phone_safety_section(x)
    assert "not set" in nag and "bigwins secret app_passphrase" in nag
    rows = "".join(dr_rows(v, x))
    assert "a=here" in rows and "a=lock" in rows and lock_note(x) == ""
    x.actions_locked = True
    assert "a=unlock" in "".join(dr_rows(v, x)) and "locked" in lock_note(x)
