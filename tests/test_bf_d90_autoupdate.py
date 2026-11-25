"""BF-D90: automatic app updates (deploy/autoupdate.py, bigwins.sh ``do_autoupdate``, the
trader's Inbox / PAGE messages, Health, Settings and the demo's note). PAPER ONLY.

The bash tests run the real functions against a real git repository (a bare "GitHub"
and the server's clone) with docker, curl and sleep stubbed: nothing is built or started."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from trader import presence as pr
from trader.app_store import SERVER_ACTIONS, get_state, set_state
from trader.journal import Journal
from trader.ops_hooks import autoupdate_text, record_autoupdate, tell_autoupdate
from trader.server_status import clean_autoupdate, clean_status

REPO = Path(__file__).resolve().parents[1]
SH = REPO / "deploy" / "bigwins.sh"
AU = runpy.run_path(str(REPO / "deploy" / "autoupdate.py"))
SAT = "2026-11-28T11:00:00+11:00"  # a Saturday
TUE_11 = "2026-12-01T11:00:00+11:00"  # a trading day, ASX hours
GREEN = "a" * 40


def _facts(**kw: Any) -> Any:
    base: dict[str, Any] = {
        "head": "1" * 40, "tip": GREEN, "title": "Screens: nicer chart",
        "files": ["trader/app_pages.py", "docs/research/studies/x.md"], "cls": "app",
        "descendant": True, "enabled": True, "live": False, "sign_mode": "warn", "sig": "bad",
        "seen_h": 2, "min_age_h": 1, "dirty": False, "window_ok": True,
    }  # fmt: skip
    base.update(kw)
    return AU["Facts"](**base)


# ---------------------------------------------------------------- what may apply by itself


TRADING_OR_INFRA = (
    "trader/bf_app.py", "trader/orders.py", "trader/lines/emg2.py", "trader/secrets.py",
    "trader/bfast_config.py", "trader/presence.py", "trader/bfast_cli.py", "config/bfast.yaml",
    "config/lic_list.csv", "migrations/journal/versions/x.py", "deploy/bigwins.sh",
    "deploy/autoupdate.py", "deploy/classify.py", "deploy/Dockerfile", "deploy/docker-compose.yml",
    "deploy/gitops.py", "deploy/secret_tool.py", "scripts/req_coverage.py", "pyproject.toml",
    "uv.lock", "alembic.ini", "CLAUDE.md", ".claude/settings.json", ".github/workflows/ci.yml",
    "Makefile", ".gitignore",
)  # fmt: skip


@pytest.mark.parametrize("path", TRADING_OR_INFRA)
def test_BF_D90_strategy_and_infra_changes_are_never_applied_automatically(path: str) -> None:
    k, bad = AU["kind"]([path, "docs/x.md"])
    assert k == "approval" and path in bad
    cls = AU["C"].classify([path])
    action, _, code = AU["decide"](_facts(files=[path], cls=cls), "green")
    assert action == "approval" and code == "approval"


def test_BF_D90_app_only_paths_and_hash_inputs() -> None:
    for f in ("trader/app_pages.py", "trader/dashboard.py", "trader/app_research.py",
              "docs/research/studies/x.md", "docs/HANDOVER.md", "tests/test_x.py",
              "research/odds_table/build_odds_table.py", "README.md", "NEXT.md"):  # fmt: skip
        assert AU["auto_path"](f), f
    assert AU["kind"]([]) == ("auto", [])  # an empty signed release commit changes nothing
    # every input of the frozen strategy hash and settings hash needs approval, so an
    # automatic update can never change either
    from trader import strategy_version as sv

    for name in (*sv.STRATEGY_FILES, "config/bfast.yaml", "config/strategy_changelog.yaml"):
        assert not AU["auto_path"](name.rstrip("/") + ("/x.py" if name.endswith("/") else ""))
    for p in (REPO / "trader").rglob("*.py"):
        rel = p.relative_to(REPO).as_posix()
        if rel not in sv.UI_ONLY:
            assert not AU["auto_path"](rel), rel
    assert sv.strategy_hash(REPO) == "a50dfa0b4eb1"
    from trader.yamlio import load_yaml

    cfg = load_yaml((REPO / "config/bfast.yaml").read_text(encoding="utf-8"))
    assert sv.config_hash(cfg) == "02589a19293b"


# ---------------------------------------------------------------- ASX hours


def test_BF_D90_never_during_asx_hours_weekends_and_holidays_allowed() -> None:
    w = AU["window"]

    def at(s: str) -> datetime:
        return datetime.fromisoformat(s)

    tue = date(2026, 12, 1)
    sessions = {tue, date(2026, 12, 2), date(2026, 12, 24), date(2026, 12, 29)}
    assert not w(at("2026-12-01T09:30:00+11:00"), sessions)[0]
    assert not w(at("2026-12-01T12:00:00+11:00"), sessions)[0]
    assert not w(at("2026-12-01T16:30:00+11:00"), sessions)[0]
    assert w(at("2026-12-01T09:29:00+11:00"), sessions)[0]
    assert w(at("2026-12-01T16:31:00+11:00"), sessions)[0]
    assert w(at("2026-11-28T12:00:00+11:00"), sessions)[0]  # Saturday
    assert w(at("2026-12-25T12:00:00+11:00"), sessions)[0]  # Christmas: an ASX holiday
    assert not w(at("2026-12-25T12:00:00+11:00"), None)[0]  # no calendar: weekday = trading
    assert not w(at("2027-03-02T12:00:00+11:00"), sessions)[0]  # beyond the calendar: fails safe
    action, reason, code = AU["decide"](_facts(window_ok=False, window_why="waiting: ASX"), "green")
    assert (action, code) == ("wait", "hours")


# ---------------------------------------------------------------- the gates


def test_BF_D90_gates_ci_signature_descendant_live_age_switch() -> None:
    d = AU["decide"]
    assert d(_facts(), "green")[0] == "apply"  # paper, warn mode, unsigned: allowed
    assert d(_facts(), None)[0] == "needci"
    assert d(_facts(), "red")[:1] == ("block",) and d(_facts(), "red")[2] == "ci-red"
    assert d(_facts(), "pending")[0] == "wait"
    assert d(_facts(), "unknown:GitHub not reachable")[2] == "ci-unknown"
    assert d(_facts(descendant=False), "green")[2] == "nonff"
    assert d(_facts(tip="1" * 40), "green")[0] == "none"
    # signing enforced: only a good signature
    assert d(_facts(sign_mode="enforce", sig="bad"), "green")[2] == "sig"
    assert d(_facts(sign_mode="enforce", sig="none"), "green")[2] == "sig"
    assert d(_facts(sign_mode="enforce", sig="good"), "green")[0] == "apply"
    # live: never in warn mode, 24 hours minimum age
    assert d(_facts(live=True, sign_mode="warn"), "green")[2] == "live-nosign"
    assert d(_facts(live=True, sign_mode="nokey"), "green")[2] == "live-nosign"
    live = _facts(live=True, sign_mode="enforce", sig="good", min_age_h=24, seen_h=23)
    assert d(live, "green")[2] == "age"
    live.seen_h = 24
    assert d(live, "green")[0] == "apply"
    assert d(_facts(seen_h=0), "green")[2] == "age"  # paper: 1 hour
    assert d(_facts(enabled=False), "green")[2] == "off"  # the kill switch
    assert d(_facts(dirty=True), "green")[2] == "dirty"
    assert d(_facts(bad=frozenset({GREEN})), "green")[2] == "rolledback"  # never twice
    assert d(_facts(fetch_failed=True), "green")[2] == "fetch"


def test_BF_D90_ci_status_reads_the_exact_commit(tmp_path: Path) -> None:
    sha = "b" * 40

    def run(*runs: dict[str, Any]) -> str:
        f = tmp_path / "ci.json"
        f.write_text(json.dumps({"workflow_runs": list(runs)}))
        return str(AU["ci_status"]("o/r", sha, "", str(f)))

    ok = {"head_sha": sha, "path": ".github/workflows/ci.yml", "event": "push",
          "status": "completed", "conclusion": "success", "created_at": "2026-11-25T01:00:00Z",
          "id": 1}  # fmt: skip
    assert run(ok) == "green"
    assert run({**ok, "head_sha": "c" * 40}) == "pending"  # another commit's run never counts
    assert run({**ok, "path": ".github/workflows/other.yml"}) == "pending"
    assert run({**ok, "conclusion": "failure"}) == "red"
    assert run({**ok, "status": "in_progress", "conclusion": None}) == "pending"
    assert run({**ok, "conclusion": "cancelled"}).startswith("unknown:")
    rerun = {**ok, "conclusion": "failure", "created_at": "2026-11-25T02:00:00Z", "id": 2}
    assert run(ok, rerun) == "red"  # the newest run decides
    assert AU["ci_status"]("o/r", "not-a-sha").startswith("unknown:")


def test_BF_D90_pages_once_and_records_events(tmp_path: Path) -> None:
    ci = tmp_path / "ci.json"
    ci.write_text(json.dumps({"workflow_runs": [{
        "head_sha": GREEN, "path": ".github/workflows/ci.yml", "event": "push",
        "status": "completed", "conclusion": "failure", "id": 1}]}))  # fmt: skip
    env = {"AU_STATE": str(tmp_path), "AU_OUTBOX": str(tmp_path / "out.jsonl"),
           "AU_HEAD": "1" * 40, "AU_TIP": GREEN, "AU_TITLE": "Screens", "AU_FILES": "docs/x.md",
           "AU_CLASS": "app", "AU_DESC": "1", "AU_ENABLED": "1", "AU_LIVE": "0",
           "AU_SIGN_MODE": "warn", "AU_SIG": "none", "AU_SEEN_H": "3", "AU_MIN_AGE_H": "1",
           "AU_NOW": SAT, "AU_CI_FIXTURE": str(ci)}  # fmt: skip
    action, _, pages = AU["run_decide"](env)
    assert action == "block" and len(pages) == 1 and "CI FAILED" in pages[0]
    assert AU["run_decide"](env)[2] == []  # once per commit and reason
    ev = [json.loads(x) for x in (tmp_path / "out.jsonl").read_text().splitlines()]
    assert [e["kind"] for e in ev] == ["blocked"]
    st = AU["status"]({**env, "AU_ENABLED": "1", "AU_TIMER": "1"})
    assert st["pending"]["action"] == "block" and st["enabled"] and st["timer"]
    assert st["next_check"] > st["last_check"]
    pages = AU["run_result"]({**env, "AU_REASON": "the app does not answer"}, "rolled_back")
    assert "ROLLED BACK" in pages[0]
    assert AU["run_decide"](env)[0] == "approval"  # a rolled-back commit never applies again
    AU["run_result"]({**env, "AU_TIP": "d" * 40}, "applied")
    st = AU["status"](env)
    assert st["last_applied"]["commit"] == "d" * 40 and "secret" not in json.dumps(st).lower()


# ---------------------------------------------------------------- the host side (bash)


def _git(repo: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *a],
                          capture_output=True, text=True, check=True).stdout.strip()  # fmt: skip


def _commit(work: Path, path: str, text: str, msg: str) -> str:
    f = work / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    _git(work, "add", path)
    _git(work, "commit", "-q", "--no-gpg-sign", "-m", msg)
    _git(work, "push", "-q", "origin", "HEAD:bigwins-fast")
    return _git(work, "rev-parse", "HEAD")


class Server:
    """A bare 'GitHub', an engineer's clone and the server's clone, with stubs."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        origin = tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "bigwins-fast", str(origin)],
                       check=True)  # fmt: skip
        self.work = tmp / "work"
        subprocess.run(["git", "clone", "-q", str(origin), str(self.work)], check=True,
                       capture_output=True)  # fmt: skip
        _git(self.work, "config", "user.email", "e@example.invalid")
        _git(self.work, "config", "user.name", "Engineer")
        _git(self.work, "checkout", "-q", "-b", "bigwins-fast")
        (self.work / "config").mkdir()
        (self.work / "config" / "bfast.yaml").write_text("mode: paper\n")
        _git(self.work, "add", "config/bfast.yaml")
        self.base = _commit(self.work, "docs/a.md", "one", "first")
        self.srv = tmp / "srv"
        subprocess.run(["git", "clone", "-q", "-b", "bigwins-fast", str(origin), str(self.srv)],
                       check=True, capture_output=True)  # fmt: skip
        dep = tmp / "deploy"
        (dep / "secrets").mkdir(parents=True)
        for f in ("autoupdate.py", "classify.py", "gitops.py"):
            (dep / f).write_text((REPO / "deploy" / f).read_text())
        for d in ("state", "etc", "public", "bin"):
            (tmp / d).mkdir()
        (dep / "secrets" / "healthchecks_url").write_text("https://hc-ping.com/xyz")
        stub = (
            '#!/bin/sh\necho "$0 $@" >> "{log}"\n{extra}exit $(cat "{rc}" 2>/dev/null || echo 0)\n'
        )
        bin_ = tmp / "bin"
        (bin_ / "curl").write_text(stub.format(log=tmp / "calls.log", rc=tmp / "curl_rc", extra=""))
        (bin_ / "docker").write_text(stub.format(
            log=tmp / "calls.log", rc=tmp / "docker_rc",
            extra=f'[ "$1" = ps ] && [ -f "{tmp}/demo" ] && echo bigwins-demo\n'))  # fmt: skip
        (bin_ / "sleep").write_text("#!/bin/sh\nexit 0\n")
        for b in bin_.iterdir():
            b.chmod(0o755)
        (tmp / "demo").write_text("")
        self.ci = tmp / "ci.json"

    def green(self, sha: str, conclusion: str = "success") -> None:
        self.ci.write_text(json.dumps({"workflow_runs": [{
            "head_sha": sha, "path": ".github/workflows/ci.yml", "event": "push",
            "status": "completed", "conclusion": conclusion, "id": 1}]}))  # fmt: skip

    def age(self, sha: str, hours: int = 5) -> None:
        t = int(datetime.now().timestamp()) - hours * 3600  # noqa: DTZ005 - epoch seconds
        (self.tmp / "state" / "seen_remote").write_text(f"{sha} {t}\n")

    def run(self, script: str, now: str = SAT) -> subprocess.CompletedProcess[str]:
        t = self.tmp
        pre = (f'source "{SH}" __lib__ >/dev/null; REPO="{self.srv}"; DEPLOY="{t}/deploy"; '
               f'SECRETS="{t}/deploy/secrets"; STATE="{t}/state"; ETC="{t}/etc"; '
               f'SIGNERS="{t}/etc/allowed_signers"; SIGN_ENFORCE="{t}/etc/require_signed"; '
               f'AU_SWITCH="{t}/etc/autoupdate"; AU_PUBLIC="{t}/public"; '
               f'CONFIG="{self.srv}/config/bfast.yaml"; LOCAL="{t}/local.yaml"; ')  # fmt: skip
        env = {**os.environ, "PATH": f"{t / 'bin'}:{os.environ['PATH']}", "AU_NOW": now,
               "AU_CI_FIXTURE": str(self.ci), "AU_TRIES": "2", "AU_PAUSE": "0",
               "AU_SETTLE": "0", "GIT_CONFIG_PARAMETERS": "'commit.gpgsign=false'"}  # fmt: skip
        return subprocess.run(["bash", "-c", pre + script], capture_output=True, text=True,
                              env=env, check=False)  # fmt: skip

    def head(self) -> str:
        return _git(self.srv, "rev-parse", "HEAD")

    def calls(self) -> str:
        p = self.tmp / "calls.log"
        return p.read_text() if p.is_file() else ""

    def state(self) -> dict[str, Any]:
        return dict(json.loads((self.tmp / "state" / "autoupdate.json").read_text()))


def test_BF_D90_applies_an_app_only_update_and_restarts_only_the_app(tmp_path: Path) -> None:
    s = Server(tmp_path)
    tip = _commit(s.work, "docs/research/studies/x.md", "new card", "Research card x")
    s.green(tip)
    r = s.run("do_autoupdate")
    assert "wait" in r.stdout and s.head() == s.base, r.stdout + r.stderr  # 0 of 1 hour
    s.age(tip)
    r = s.run("do_autoupdate")
    assert s.head() == tip, r.stdout + r.stderr
    assert "applied" in r.stdout
    calls = s.calls()
    assert "docker build" in calls and "bigwins-demo" in calls and "healthz" in calls
    cmds = [x.split("/bin/", 1)[1] for x in calls.splitlines() if "/bin/" in x]
    assert not any(c.startswith(("docker compose", "docker restart", "docker stop")) for c in cmds)
    assert "trader-bf run" not in calls  # the trader is never touched
    st = s.state()
    assert st["last_applied"]["commit"] == tip and st["last_applied"]["title"] == "Research card x"
    out = (tmp_path / "state" / "autoupdate_outbox.jsonl").read_text()
    assert '"kind": "applied"' in out  # for the app's Inbox once the trader runs
    assert (tmp_path / "state" / "previous_commit").read_text().strip() == s.base  # Roll back
    pub = json.loads((tmp_path / "public" / "status.json").read_text())
    assert pub["last_applied"]["commit"] == tip  # the demo's banner


def test_BF_D90_rolls_back_when_the_health_check_fails_and_pages(tmp_path: Path) -> None:
    s = Server(tmp_path)
    tip = _commit(s.work, "trader/app_pages.py", "broken = (", "Screens: broken")
    s.green(tip)
    s.age(tip)
    (tmp_path / "curl_rc").write_text("1")  # /healthz never answers
    r = s.run("do_autoupdate")
    assert s.head() == s.base, r.stdout + r.stderr
    assert "ROLLED BACK" in r.stdout
    assert "hc-ping.com/xyz/fail" in s.calls()  # no trader running: healthchecks.io pages
    assert '"kind": "rolled_back"' in (tmp_path / "state" / "autoupdate_outbox.jsonl").read_text()
    assert not (tmp_path / "state" / "previous_commit").exists()  # as before the attempt
    (tmp_path / "curl_rc").write_text("0")
    r = s.run("do_autoupdate")
    assert s.head() == s.base and "approval" in r.stdout  # never retried by itself


def test_BF_D90_strategy_commit_hours_switch_live_and_enforce_block(tmp_path: Path) -> None:
    s = Server(tmp_path)
    tip = _commit(s.work, "trader/orders.py", "x = 1", "Orders: change")
    s.green(tip)
    s.age(tip)
    r = s.run("do_autoupdate")
    assert s.head() == s.base and "approval" in r.stdout
    assert "docker build" not in s.calls()
    # an app-only commit on top: the range still holds the trading file
    tip2 = _commit(s.work, "docs/b.md", "two", "Docs")
    s.green(tip2)
    s.age(tip2)
    assert "approval" in s.run("do_autoupdate").stdout and s.head() == s.base


@pytest.mark.parametrize("case", ["hours", "off", "live", "enforce", "ci", "nonff"])
def test_BF_D90_app_only_update_is_held_back(tmp_path: Path, case: str) -> None:
    s = Server(tmp_path)
    tip = _commit(s.work, "docs/c.md", "three", "Docs only")
    s.green(tip)
    s.age(tip, 30)
    now = SAT
    if case == "hours":
        now = TUE_11
    elif case == "off":
        assert "off" in s.run("au_set off").stdout
    elif case == "live":
        (tmp_path / "local.yaml").write_text("broker:\n  account_id: U1234567\n")
    elif case == "enforce":
        (tmp_path / "etc" / "allowed_signers").write_text(
            'engineer namespaces="git" ssh-ed25519 AAAA\n'
        )
        (tmp_path / "etc" / "require_signed").write_text("")
    elif case == "ci":
        s.green(tip, "failure")
    elif case == "nonff":
        _git(s.srv, "config", "user.email", "s@example.invalid")
        _git(s.srv, "config", "user.name", "Server")
        (s.srv / "docs" / "local.md").write_text("edited here")
        _git(s.srv, "add", "docs/local.md")
        _git(s.srv, "commit", "-q", "--no-gpg-sign", "-m", "local")
    before = s.head()
    r = s.run("do_autoupdate", now)
    assert s.head() == before, r.stdout + r.stderr
    want = {"hours": "wait", "off": "approval", "live": "approval", "enforce": "block",
            "ci": "block", "nonff": "block"}[case]  # fmt: skip
    assert f"auto-update: {want}" in r.stdout, r.stdout + r.stderr
    assert "docker build" not in s.calls()


def test_BF_D90_kill_switch_and_status_commands(tmp_path: Path) -> None:
    s = Server(tmp_path)
    r = s.run("au_enabled && echo on; au_set off; au_enabled || echo off-now; au_set on; "
              "au_enabled && echo on-again; au_set maybe; echo rc=$?")  # fmt: skip
    assert r.stdout.splitlines()[0] == "on"  # default on while paper
    assert "off-now" in r.stdout and "on-again" in r.stdout and "rc=1" in r.stdout
    (tmp_path / "etc" / "autoupdate").unlink()
    (tmp_path / "local.yaml").write_text("broker:\n  account_id: U7654321\n")
    r = s.run("au_live && echo live; au_enabled || echo off-by-default; au_min_age_h")
    assert r.stdout.split() == ["live", "off-by-default", "24"]
    (tmp_path / "local.yaml").write_text("broker:\n  account_id: DU7654321\n")
    r = s.run("au_live || echo paper; au_min_age_h; cmd_autoupdate status")
    assert r.stdout.split()[:2] == ["paper", "1"] and "Automatic app updates: ON" in r.stdout


def test_BF_D90_script_wiring() -> None:
    sh = SH.read_text()
    assert subprocess.run(["bash", "-n", str(SH)], check=False).returncode == 0
    assert "autoupdate|autoupdate-run|automatic app updates" in sh  # the timer (BF-D81 S7)
    assert "bigwins-autoupdate.timer" in sh.split("ensure_timers() {")[1].split("\n}\n")[0]
    assert "autoupdate" in sh.split("timer_states() {")[1].split("\n}\n")[0]
    for fn in ("update_to() {", "do_update() {", "do_rollback() {"):
        assert "au_lock" in sh.split(fn)[1].split("\n}\n")[0], fn  # one update at a time
    restart = sh.split("au_restart() {")[1].split("\n}\n")[0]
    assert "dc up -d --no-deps dashboard" in restart and "restart trader" not in restart
    demo = sh.split("cmd_demo() {")[1].split("\n}\n")[0]
    assert "pull" not in demo and "do_update" in demo  # the demo's update is checked too
    worker = sh.split("cmd_worker() {")[1].split("\n}\n")[0]
    assert "autoupdate_on) out=$(au_set on" in worker and "au_flush" in worker
    assert "--no-renames" in sh.split("update_to() {")[1].split("\n}\n")[0]
    assert "github_ci_token" in sh.split("TYPED_SECRETS=")[1].split("\n")[0]


# ---------------------------------------------------------------- the app


T0 = datetime.fromisoformat("2026-11-28T11:00:00+11:00")


def test_BF_D90_inbox_once_per_event_and_pages_on_rollback() -> None:
    j = Journal.sqlite()
    said: list[str] = []

    def note(t: str, k: str, link: str) -> None:
        said.append(f"{k}|{t}")

    ok = {"id": 1, "kind": "applied", "commit": GREEN, "title": "Screens: nicer chart",
          "at": T0.isoformat(), "from": "1" * 40}  # fmt: skip
    assert record_autoupdate(j, ok, T0)["kind"] == "applied"
    record_autoupdate(j, ok, T0)  # a retry is kept once
    assert record_autoupdate(j, {"id": 2, "kind": "rm -rf"}, T0) == {}
    assert tell_autoupdate(j, note) == 1 and tell_autoupdate(j, note) == 0
    assert said[0].startswith("info|Updated automatically: Screens: nicer chart")
    bad = {**ok, "id": 2, "kind": "rolled_back", "reason": "the app does not answer"}
    record_autoupdate(j, bad, T0)
    assert tell_autoupdate(j, note) == 1 and said[-1].startswith(
        "page|PAGE Automatic app update ROLLED BACK"
    )
    assert autoupdate_text({**ok, "kind": "blocked", "reason": "GitHub CI FAILED"})[1] == "page"


def test_BF_D90_new_code_alert_says_auto_or_update_ready() -> None:
    j = Journal.sqlite()
    said: list[str] = []
    hook = pr.PresenceHook(j, lambda t, k, link: said.append(f"{k}|{t}"))
    u = {"remote": "c" * 40, "head": "d" * 40, "ahead": 1, "subject": "Docs", "signed": "none",
         "auto": "auto"}  # fmt: skip
    set_state(j, "update-available", u, T0)
    hook._new_code(T0)
    assert said[-1].startswith("info|New app update on GitHub: Docs") and "by itself" in said[-1]
    set_state(j, "update-available", {**u, "remote": "e" * 40, "auto": "approval",
                                      "subject": "Orders"}, T0)  # fmt: skip
    hook._new_code(T0)
    assert "Update ready: Orders — tap to review and approve" in said[-1]
    assert "6-digit code" in said[-1] and len(said) == 2  # one push per commit


def test_BF_D90_health_settings_and_status_cleaning() -> None:
    from trader import app_ops
    from trader.app_control import PASS_ACTS, SRV_TITLE
    from trader.app_pages import Extras, autoupdate_settings

    raw = {"enabled": True, "timer": True, "mode": "demo", "next_check": "2026-11-28T11:37:00+11:00",
           "last_applied": {"commit": GREEN, "title": "Screens <b>x</b>", "at": T0.isoformat(),
                            "token": "not-a-real-value"},
           "pending": {"commit": "b" * 40, "title": "Orders", "action": "approval",
                       "reason": "not app-only"}, "evil": "x"}  # fmt: skip
    au = clean_autoupdate(raw)
    assert "evil" not in au and "token" not in au["last_applied"]
    assert clean_status({"autoupdate": raw, "timers": {"autoupdate": True}})["timers"] == {
        "autoupdate": True
    }
    line = app_ops.autoupdate_line({"autoupdate": au})
    assert "Auto-update:" in line and ">on<" in line and "last applied" in line
    assert "Screens &lt;b&gt;x&lt;/b&gt;" in line and "next check Sat 28 Nov 11:37" in line
    assert "Waiting for your approval: Orders" in line
    x = Extras()
    x.host = ({"autoupdate": au}, T0)
    html = autoupdate_settings(x)
    assert "autoupdate_off" in html and "Turn off" in html and "6-digit code" in html
    x.host = ({"autoupdate": {**au, "enabled": False}}, T0)
    assert "autoupdate_on" in autoupdate_settings(x)
    assert {"autoupdate_on", "autoupdate_off"} <= set(SERVER_ACTIONS) <= set(SRV_TITLE)
    assert "srv:autoupdate_on" in PASS_ACTS  # turning it on also needs the passphrase


def test_BF_D90_toggle_from_the_app_needs_the_code() -> None:
    from tests.test_bf_app_actions import _post, _setup
    from tests.test_bf_execution import SEED, T_APPROVE
    from trader.approval import totp

    j, _, ctl, _, _ = _setup()
    assert "enter your 6-digit code" in _post(ctl, {"a": "srv:autoupdate_off"})[1]
    _post(ctl, {"a": "srv:autoupdate_off", "code": "000000"})
    assert not _jobs(j)  # a wrong code queues nothing
    _, page = _post(ctl, {"a": "srv:autoupdate_off", "code": totp(SEED, T_APPROVE)})
    assert "queued" in page
    assert [r["action"] for r in _jobs(j)] == ["autoupdate_off"]


def _jobs(j: Journal) -> list[dict[str, Any]]:
    from trader.app_store import server_job_rows

    return list(server_job_rows(j, 20))


def test_BF_D90_demo_note_shows_the_real_status(tmp_path: Path) -> None:
    from trader.dashboard import demo_autoupdate_notes

    f = tmp_path / "status.json"
    assert demo_autoupdate_notes(f) == []
    f.write_text(json.dumps({"enabled": True, "next_check": "2026-11-28T11:37:00+11:00",
                             "pending": {"commit": "b" * 40, "title": "Worker change",
                                         "action": "approval", "reason": "x"}}))  # fmt: skip
    notes = demo_autoupdate_notes(f)
    assert "automatic app updates on" in notes[0] and "next check 11:37" in notes[0]
    assert "Update ready on the server: Worker change" in notes[1] and "bigwins update" in notes[1]
    f.write_text("not json")
    assert demo_autoupdate_notes(f) == []
    assert get_state(Journal.sqlite(), "autoupdate-events") is None
    assert timedelta(0) == timedelta(0)
