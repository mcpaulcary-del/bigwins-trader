"""Run one record job inside the record container (BF-D93); the host worker starts it:

    python -I /opt/bwrecord/record/tools/bwrec.py run-job <job> [--dry-run]

Before anything runs: the code mounted at the cloud's path must be byte-identical to
``record/MANIFEST.sha256`` of the approved commit, and Python and the numeric libraries
must be the versions in ``record/ENVIRONMENT.json`` (the cloud's). Each ``py`` step is
its own process (``launch.py``), like the cloud task's own commands. The last line of
output is a JSON summary (steps, exit codes, seconds, peak memory, ledger entries
appended) that the worker hands to the app.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from record.tools import fence, hashing, jobs, paths
from record.tools import ledgerlib as L

HERE = Path(__file__).resolve().parent
REPO_RECORD = HERE.parent  # the read-only mount of the repository's record/ folder
MANIFEST = REPO_RECORD / "MANIFEST.sha256"
ENVIRONMENT = REPO_RECORD / "ENVIRONMENT.json"
CODE_MOUNTS = (("code", paths.REL_CODE), ("data_foundation_code", paths.REL_DF_CODE))


def check_code(root: Path, manifest: Path = MANIFEST) -> list[str]:
    """Differences between the code the jobs will run and the approved manifest."""
    try:
        want = hashing.read_sha256sums(manifest.read_text(encoding="utf-8"))
    except OSError:
        return ["record/MANIFEST.sha256 is missing"]
    bad: list[str] = []
    seen: set[str] = set()
    for top, rel in CODE_MOUNTS:
        base = root / rel
        for name, h in want.items():
            if not name.startswith(top + "/"):
                continue
            seen.add(name)
            p = base / name[len(top) + 1 :]
            if not p.is_file():
                bad.append(f"missing: {name}")
            elif hashing.sha_file(p) != h:
                bad.append(f"changed: {name}")
        for p in sorted(base.rglob("*")) if base.is_dir() else []:
            r = f"{top}/{p.relative_to(base).as_posix()}"
            if p.is_file() and "__pycache__" not in p.parts and r not in want:
                bad.append(f"not in the manifest: {r}")
    if not seen:
        bad.append("the manifest lists no code")
    return bad


def versions() -> dict[str, str]:
    out = {"python": ".".join(str(x) for x in sys.version_info[:3])}
    for mod in ("pandas", "numpy", "scipy", "requests", "exchange_calendars"):
        try:
            out[mod] = str(__import__(mod).__version__)
        except Exception:
            out[mod] = "missing"
    return out


def check_env(have: Mapping[str, str], path: Path = ENVIRONMENT) -> list[str]:
    try:
        want = json.loads(path.read_text(encoding="utf-8"))["versions"]
    except (OSError, ValueError, KeyError):
        return ["record/ENVIRONMENT.json is missing or unreadable"]
    return [f"{k}: {have.get(k, 'missing')} here, {v} on the cloud"
            for k, v in want.items() if have.get(k) != v]  # fmt: skip


def run_py(step: jobs.Step, extra: Sequence[str] = ()) -> int:
    cmd = [sys.executable, "-I", str(HERE / "launch.py")]
    if step.isolated:
        cmd.append("--isolated")
    cmd += [step.name, *step.args, *extra]
    try:
        return subprocess.run(cmd, timeout=step.timeout_s, check=False).returncode
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {step.timeout_s} s: {step.name}")
        return 124


def run_job(key: str, tools: Mapping[str, Callable[[Path, bool], int]], dry_run: bool = False,
            root: Path | None = None, checks: bool = True) -> dict[str, Any]:  # fmt: skip
    root = root or paths.root()
    job = jobs.JOBS.get(key)
    res: dict[str, Any] = {"job": key, "ok": False, "steps": [], "started_utc": _utc()}
    if job is None:
        res["error"] = "unknown job"
        return res
    if checks:
        bad = check_code(root) + check_env(versions())
        if bad:
            res["error"] = "refused: " + "; ".join(bad[:6])
            return res
    me = os.environ.get("BW_RECORD_HOST", "")
    d = fence.decide_dir(paths.record_dir(root), me)
    if not d.ok:
        res["error"] = "refused (writer fence): " + d.reason
        return res
    res["role"] = d.reason
    ledger = paths.ledger(root)
    before = L.read(ledger)
    t0 = time.monotonic()
    ok = True
    for step in job.steps:
        t = time.monotonic()
        if step.kind == "py":
            rc = run_py(step)
        elif step.name in tools:
            rc = tools[step.name](root, dry_run)
        else:
            rc = 2
        res["steps"].append({"name": step.name, "rc": rc, "s": round(time.monotonic() - t, 1)})
        if rc != 0:
            ok = ok and not step.must
            if step.must:
                break
    after = L.read(ledger)
    try:
        res["head"] = L.verify(after)
    except L.ChainError as e:
        ok = False
        res["error"] = f"the ledger does not verify after the job: {e}"
    res["entries"] = [{"seq": e.get("seq"), "kind": e.get("kind"), "asof": e.get("asof")}
                      for e in after[len(before):]]  # fmt: skip
    res["seconds"] = round(time.monotonic() - t0, 1)
    peak = max(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)  # fmt: skip
    res["peak_mb"] = round(peak / 1024, 1)
    res["failed_steps"] = [s["name"] for s in res["steps"] if s["rc"] != 0]
    res["ok"] = ok and "error" not in res
    return res


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
