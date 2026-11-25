"""bigwins worker (BF-D90): automatic app updates, the decisions. Standard library only
(the host's python3); the git, Docker and restart steps are in deploy/bigwins.sh
(``do_autoupdate``), which runs this every 30 minutes from the bigwins-autoupdate timer.

    git diff --no-renames --name-only A B | python3 autoupdate.py kind   "auto" or "approval"
    python3 autoupdate.py window                     exit 0 outside ASX hours (prints why not)
    python3 autoupdate.py decide                     the facts in AU_* variables; prints the
                                                     action (apply|none|wait|approval|block),
                                                     then the reason, then "page <text>" lines
    python3 autoupdate.py result applied|rolled_back|failed     record what happened
    python3 autoupdate.py status                     JSON for the app (no secrets)
    python3 autoupdate.py ci <owner/repo> <sha> [token_file]    GitHub CI of that commit

**What may be applied automatically** (default-deny): the BF-D53 classifier says app-only
AND every changed path is on the short allow-list below (the display-only files of
``UI_ONLY``, ``docs/``, ``tests/``, ``research/`` and top-level ``*.md`` other than
CLAUDE.md). Anything else (trading code, config, migrations, deploy scripts with the
worker, this file, the timers, compose and the Dockerfile, secrets handling, the config
schema, CI workflows, dependencies) needs the owner's approval in the app as before.
Every input of the strategy hash and of the strategy settings hash is a trading path, so
an automatic update can never change either (a test checks).

**Gates**, in this order: a fast-forward of the running commit; app-only; the switch on;
on a live book only with signing enforced; with signing enforced, a good signature; the
tracked config unedited; outside ASX hours (weekdays before 09:30 and after 16:30
Sydney, weekends and ASX holidays); at least 1 hour (paper) / 24 hours (live) since this
server first saw the commit; GitHub CI passed for that exact commit (read from GitHub's
API: the ``ci-ok/`` tags stay information only, BF-D84).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ALLOW_DIRS = ("docs/", "tests/", "research/")
CI_WORKFLOW = ".github/workflows/ci.yml"
EVERY_MIN = 30  # the timer: at :07 and :37 past every hour
SLOT_MINUTES = (7, 37)
BLOCK_FROM, BLOCK_TO = 930, 1630  # HHMM Sydney on trading days (inclusive)
PAGE_CODES = frozenset({"nonff", "sig", "dirty", "ci-red", "ci-unknown", "fetch"})
KEEP = 40


def _classify() -> Any:
    """deploy/classify.py, loaded by path (``python3 -I`` puts no script folder on sys.path)."""
    spec = importlib.util.spec_from_file_location("bw_classify", HERE / "classify.py")
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = _classify()


def auto_path(path: str) -> bool:
    """One changed path that an automatic update may carry (default-deny)."""
    f = path.strip()
    if not f or C.is_trading_path(f):
        return False
    if f in C.UI_ONLY or f.startswith(ALLOW_DIRS):
        return True
    return "/" not in f and f.endswith(".md") and f not in C.TRADING_FILES


def kind(files: Iterable[str]) -> tuple[str, list[str]]:
    """("auto", []) or ("approval", the paths that need approval). No changed file at all
    (e.g. an empty signed release commit, F5b) is "auto": nothing changes."""
    fs = [f.strip() for f in files if f.strip()]
    bad = [f for f in fs if not auto_path(f)]
    if C.classify(fs) != "app" and not bad:  # never: both lists come from classify.py
        bad = ["(classified as a trading change)"]
    return ("approval" if bad else "auto"), bad


# ---------------------------------------------------------------- the ASX window
def sydney_now() -> datetime:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo("Australia/Sydney"))
    except Exception:  # no time-zone data: the server clock is Sydney time (B1)
        return datetime.now()  # noqa: DTZ005


def load_sessions(path: str | None) -> set[date] | None:
    """The ASX trading days the image's calendar helper wrote (trader.bfast_cli._sessions);
    None when missing or unreadable (then every weekday counts as a trading day)."""
    if not path:
        return None
    try:
        days = {date.fromisoformat(x.strip()) for x in Path(path).read_text().split() if x.strip()}
    except (OSError, ValueError):
        return None
    return days or None


def window(now: datetime, sessions: set[date] | None) -> tuple[bool, str]:
    """Outside ASX hours? Weekdays before 09:30 or after 16:30 Sydney, weekends and ASX
    holidays. A day the calendar does not cover counts as a trading day (fails safe)."""
    d = now.date()
    covered = sessions is not None and min(sessions) <= d <= max(sessions)
    trading = (d in sessions) if covered and sessions is not None else d.weekday() < 5
    hm = now.hour * 100 + now.minute
    if trading and BLOCK_FROM <= hm <= BLOCK_TO:
        return False, "waiting: ASX hours (09:30-16:30 Sydney on trading days); applies after 16:30"
    return True, "outside ASX hours"


def next_slot(now: datetime) -> datetime:
    base = now.replace(second=0, microsecond=0)
    for add in range(1, 62):
        t = base + timedelta(minutes=add)
        if t.minute in SLOT_MINUTES:
            return t
    return base + timedelta(minutes=EVERY_MIN)


# ---------------------------------------------------------------- GitHub CI
def ci_status(slug: str, sha: str, token: str = "", fixture: str = "") -> str:  # noqa: PLR0911
    """green | red | pending | unknown:<why> for the CI workflow run of exactly ``sha``
    (GitHub Actions API; public repository: no token; private: a read-only token)."""
    if not (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)):
        return "unknown:not a commit id"
    if fixture:  # tests only: a saved API answer instead of the network
        try:
            data = json.loads(Path(fixture).read_text())
        except (OSError, ValueError):
            return "unknown:bad fixture"
    else:
        url = f"https://api.github.com/repos/{slug}/actions/runs?head_sha={sha}&per_page=30"
        req = urllib.request.Request(url, headers={  # noqa: S310 - the https URL above
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "bigwins-server"})  # fmt: skip
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 - https URL above
                data = json.loads(r.read(2_000_000))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404):
                return ("unknown:GitHub refused (repository private? add the read-only "
                        "github_ci_token)")  # fmt: skip
            return f"unknown:GitHub answered {e.code}"
        except (OSError, ValueError):
            return "unknown:GitHub not reachable"
    runs = [r for r in (data.get("workflow_runs") or []) if isinstance(r, Mapping)
            and r.get("head_sha") == sha and r.get("path") == CI_WORKFLOW
            and r.get("event") == "push"]  # fmt: skip
    if not runs:
        return "pending"
    last = max(runs, key=lambda r: (str(r.get("created_at") or ""), int(r.get("id") or 0)))
    if last.get("status") != "completed":
        return "pending"
    c = str(last.get("conclusion") or "")
    if c == "success":
        return "green"
    if c in ("cancelled", "skipped", "stale", ""):
        return f"unknown:CI run {c or 'without a result'}"
    return "red"


# ---------------------------------------------------------------- the decision
@dataclass
class Facts:
    head: str = ""
    tip: str = ""
    title: str = ""
    files: list[str] = field(default_factory=list)
    cls: str = "strategy"  # classify.py's answer
    descendant: bool = False
    enabled: bool = False
    live: bool = True
    sign_mode: str = "nokey"  # enforce | warn | nokey
    sig: str = "none"  # good | bad | none
    seen_h: int = 0
    min_age_h: int = 24
    dirty: bool = False
    fetch_failed: bool = False
    window_ok: bool = False
    window_why: str = ""
    bad: frozenset[str] = frozenset()  # commits rolled back automatically before

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Facts:
        def flag(k: str) -> bool:
            return env.get(k, "") == "1"

        def num(k: str, d: int) -> int:
            v = env.get(k, "")
            return int(v) if v.isdigit() else d

        return cls(
            head=env.get("AU_HEAD", ""), tip=env.get("AU_TIP", ""),
            title=env.get("AU_TITLE", "")[:200],
            files=[f for f in env.get("AU_FILES", "").splitlines() if f.strip()],
            cls=env.get("AU_CLASS", "strategy"), descendant=flag("AU_DESC"),
            enabled=flag("AU_ENABLED"), live=env.get("AU_LIVE", "1") != "0",
            sign_mode=env.get("AU_SIGN_MODE", "nokey"), sig=env.get("AU_SIG", "none"),
            seen_h=num("AU_SEEN_H", 0), min_age_h=num("AU_MIN_AGE_H", 24),
            dirty=flag("AU_DIRTY"), fetch_failed=flag("AU_FETCH_FAILED"),
        )  # fmt: skip


def decide(f: Facts, ci: str | None) -> tuple[str, str, str]:  # noqa: PLR0911, PLR0912
    """(action, reason, code). Actions: none (up to date), apply, wait (try again at the
    next check), approval (the owner approves it in the app), block (refused: pages once),
    needci (all else passed: read GitHub CI, then decide again)."""
    sha = len(f.tip) == 40 and all(c in "0123456789abcdef" for c in f.tip)
    if f.fetch_failed:
        return "block", "could not reach GitHub (git fetch failed)", "fetch"
    if not sha:
        return "wait", "no commit known on GitHub yet", "noremote"
    if f.tip == f.head:
        return "none", "up to date", "uptodate"
    if not f.descendant:
        return ("block", "the newest commit on GitHub does not follow the running one (not a "
                "fast-forward): nothing applied", "nonff")  # fmt: skip
    if f.tip in f.bad:
        return ("approval", "this commit failed its health check and was rolled back; it "
                "needs your approval now", "rolledback")  # fmt: skip
    k, why = kind(f.files)
    if k != "auto" or f.cls != "app":
        shown = ", ".join(why[:3]) + (" ..." if len(why) > 3 else "")
        return "approval", f"not app-only (changes {shown}): needs your approval", "approval"
    if not f.enabled:
        return "approval", "automatic app updates are off: needs your approval", "off"
    if f.live and f.sign_mode != "enforce":
        return ("approval", "live book: automatic updates need signing enforced (bigwins "
                "signing enforce)", "live-nosign")  # fmt: skip
    if f.sign_mode == "enforce" and f.sig != "good":
        return "block", "not signed by the engineer's key (signing is enforced)", "sig"
    if f.dirty:
        return "block", "config/bfast.yaml was edited on this server", "dirty"
    if not f.window_ok:
        return "wait", f.window_why or "waiting: ASX hours", "hours"
    if f.seen_h < f.min_age_h:
        return ("wait", f"waiting: known here for {f.seen_h} of the {f.min_age_h} hour(s) "
                "minimum", "age")  # fmt: skip
    if ci is None:
        return "needci", "", "needci"
    if ci == "red":
        return "block", "GitHub CI FAILED for this commit: not applied", "ci-red"
    if ci == "pending":
        return "wait", "waiting for GitHub CI to finish", "ci-pending"
    if ci != "green":
        return "wait", "GitHub CI result not known: " + ci.partition(":")[2], "ci-unknown"
    return "apply", "all checks passed", "apply"


# ---------------------------------------------------------------- state and events
def _load(state: Path) -> dict[str, Any]:
    try:
        d = json.loads((state / "autoupdate.json").read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(state: Path, d: Mapping[str, Any]) -> None:
    state.mkdir(parents=True, exist_ok=True)
    tmp = state / "autoupdate.json.new"
    tmp.write_text(json.dumps(d, sort_keys=True))
    tmp.replace(state / "autoupdate.json")


def _event(state: Path, d: dict[str, Any], outbox: Path | None, ev: dict[str, Any]) -> None:
    """One message for the app (the trader pushes it once; kept here while it is down)."""
    d["seq"] = int(d.get("seq") or 0) + 1
    ev = {"id": d["seq"], **ev}
    d["history"] = [ev, *(d.get("history") or [])][:20]
    if outbox is not None:
        lines = outbox.read_text().splitlines() if outbox.is_file() else []
        lines = [*lines, json.dumps(ev, sort_keys=True)][-50:]
        outbox.write_text("\n".join(lines) + "\n")


def page_text(code: str, reason: str, f: Facts) -> str:
    what = f"{f.title[:120]} ({f.tip[:10]})" if f.tip else "the newest commit"
    return f"PAGE Automatic app update not applied: {reason}. Update: {what}. See Server > Health."


def run_decide(env: Mapping[str, str], now: datetime | None = None) -> tuple[str, str, list[str]]:
    state = Path(env.get("AU_STATE", "."))
    outbox = Path(env["AU_OUTBOX"]) if env.get("AU_OUTBOX") else None
    now = now or (datetime.fromisoformat(env["AU_NOW"]) if env.get("AU_NOW") else sydney_now())
    d = _load(state)
    f = Facts.from_env(env)
    f.bad = frozenset(map(str, d.get("bad") or []))
    f.window_ok, f.window_why = window(now, load_sessions(env.get("AU_SESSIONS")))
    action, reason, code = decide(f, None)
    if action == "needci":
        token = ""
        tf = env.get("AU_TOKEN_FILE", "")
        if tf:
            try:
                token = Path(tf).read_text().strip()
            except OSError:
                token = ""
        if token.lower() in ("", "none"):
            token = ""
        ci = ci_status(env.get("AU_SLUG", ""), f.tip, token, env.get("AU_CI_FIXTURE", ""))
        action, reason, code = decide(f, ci)
    pages: list[str] = []
    fails = int(d.get("fetch_fails") or 0) + 1 if code == "fetch" else 0
    d["fetch_fails"] = fails
    key = f"{f.tip}:{code}" if code != "fetch" else f"fetch:{now.date()}"
    pageable = code in PAGE_CODES and (code != "fetch" or fails >= 3) and (
        code != "ci-unknown" or f.seen_h >= 6)  # fmt: skip
    paged = [str(x) for x in d.get("paged") or []]
    if action in ("block", "wait") and pageable and key not in paged:
        pages.append(page_text(code, reason, f))
        d["paged"] = [*paged, key][-KEEP:]
        _event(state, d, outbox, {"kind": "blocked", "commit": f.tip, "title": f.title,
                                  "reason": reason, "at": now.isoformat()})  # fmt: skip
    d["last_check"] = now.isoformat()
    d["next_check"] = next_slot(now).isoformat()
    d["last"] = {"action": action, "reason": reason, "code": code, "commit": f.tip,
                 "title": f.title, "at": now.isoformat()}  # fmt: skip
    pend = {"commit": f.tip, "title": f.title, "action": action, "reason": reason}
    d["pending"] = {} if action in ("none", "apply") else pend
    _save(state, d)
    return action, reason, pages


def run_result(env: Mapping[str, str], what: str, now: datetime | None = None) -> list[str]:
    """applied | rolled_back | failed: kept for Health and sent to the app's Inbox."""
    state = Path(env.get("AU_STATE", "."))
    outbox = Path(env["AU_OUTBOX"]) if env.get("AU_OUTBOX") else None
    now = now or (datetime.fromisoformat(env["AU_NOW"]) if env.get("AU_NOW") else sydney_now())
    d = _load(state)
    tip, title = env.get("AU_TIP", ""), env.get("AU_TITLE", "")[:200]
    frm, reason = env.get("AU_HEAD", ""), env.get("AU_REASON", "")[:300]
    ev = {"kind": what, "commit": tip, "title": title, "from": frm, "at": now.isoformat()}
    pages: list[str] = []
    if what == "applied":
        d["last_applied"] = {"commit": tip, "title": title, "at": now.isoformat(), "from": frm}
        d["pending"] = {}
    else:
        ev["reason"] = reason
        d["bad"] = [*[str(x) for x in d.get("bad") or [] if x != tip], tip][-KEEP:]
        d["pending"] = {"commit": tip, "title": title, "action": "approval",
                        "reason": f"rolled back automatically: {reason}"}  # fmt: skip
        word = "ROLLED BACK" if what == "rolled_back" else "FAILED"
        pages.append(
            f"PAGE Automatic app update {word}: {title[:120]} ({tip[:10]}). {reason}. "
            f"The app runs the previous version ({frm[:10]}). Tell your engineer."
        )
    _event(state, d, outbox, ev)
    _save(state, d)
    return pages


def status(env: Mapping[str, str]) -> dict[str, Any]:
    """For the app's Health screen and the demo's banner. No secrets: commit ids, commit
    titles, times and reasons only."""
    d = _load(Path(env.get("AU_STATE", ".")))
    keep = ("last_check", "next_check", "last", "last_applied", "pending", "history")
    out: dict[str, Any] = {k: d[k] for k in keep if k in d}
    out["history"] = (out.get("history") or [])[:8]
    out.update(enabled=env.get("AU_ENABLED") == "1", live=env.get("AU_LIVE") == "1",
               timer=env.get("AU_TIMER") == "1", mode=env.get("AU_MODE", ""))  # fmt: skip
    return out


def main(argv: list[str]) -> int:  # noqa: PLR0911
    op = argv[1] if len(argv) > 1 else ""
    env = dict(os.environ)
    if op == "kind":
        k, bad = kind(sys.stdin.read().splitlines())
        print(k)
        if bad:
            print(", ".join(bad[:5]))
        return 0
    if op == "window":
        ok, why = window(sydney_now(), load_sessions(env.get("AU_SESSIONS")))
        print(why)
        return 0 if ok else 1
    if op == "decide":
        action, reason, pages = run_decide(env)
        print(action)
        print(reason)
        for p in pages:
            print("page " + p.replace("\n", " "))
        return 0
    if op == "result" and len(argv) > 2 and argv[2] in ("applied", "rolled_back", "failed"):
        for p in run_result(env, argv[2]):
            print("page " + p.replace("\n", " "))
        return 0
    if op == "status":
        st = status(env)
        print(json.dumps(st, sort_keys=True))
        pub = env.get("AU_PUBLIC", "")
        if pub and Path(pub).is_dir():  # the demo app reads this copy (read-only mount)
            tmp = Path(pub) / "status.json.new"
            tmp.write_text(json.dumps(st, sort_keys=True))
            tmp.chmod(0o644)
            tmp.replace(Path(pub) / "status.json")
        return 0
    if op == "ci" and len(argv) > 3:
        tok = ""
        if len(argv) > 4:
            try:
                tok = Path(argv[4]).read_text().strip()
            except OSError:
                tok = ""
        print(ci_status(argv[2], argv[3], "" if tok.lower() == "none" else tok))
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
