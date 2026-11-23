"""bigwins worker (BF-D42): the host's status snapshot as JSON for the app's Server tab.

Reads load, memory, disk and uptime from the host, and the Tailscale state, code version,
ASX open/closed, container states and the trader's last log lines from the environment
(TS, CV, ASX, PS = "service|status" lines, LOGS). Standard library only. The trader
cleans every value again (trader/server_status.py) before it is stored.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any


def snapshot(env: dict[str, str], proc: str = "/proc") -> dict[str, Any]:
    mem: dict[str, int] = {}
    with open(f"{proc}/meminfo", encoding="utf-8") as f:
        for line in f:
            k, _, v = line.partition(":")
            if v.split():
                mem[k] = int(v.split()[0])
    with open(f"{proc}/loadavg", encoding="utf-8") as f:
        load = [float(x) for x in f.read().split()[:2]]
    with open(f"{proc}/uptime", encoding="utf-8") as f:
        up = float(f.read().split()[0])
    du = shutil.disk_usage("/")
    used = 100 * (1 - mem.get("MemAvailable", 0) / max(mem.get("MemTotal", 1), 1))
    cont = [
        {"name": a, "state": b}
        for a, _, b in (x.partition("|") for x in env.get("PS", "").splitlines())
        if b
    ]
    return {
        "load1": load[0], "load5": load[1], "cpus": os.cpu_count() or 1,
        "mem_used_pct": round(used, 1), "disk_used_pct": round(100 * du.used / du.total, 1),
        "disk_free_gb": round(du.free / 1e9, 1), "uptime_s": up,
        "tailscale": env.get("TS") or "?", "code_version": env.get("CV", ""),
        "asx": env.get("ASX", ""), "containers": cont,
        "log": env.get("LOGS", "").splitlines()[-30:],
        "onedrive": env.get("ONEDRIVE") == "1",  # BF-D64: the backup remote is configured
        # review F9 / security M3: hours since the newest good backup; the key's fingerprint
        "backup_age_h": int(env["BACKUP_AGE_H"]) if env.get("BACKUP_AGE_H", "").isdigit() else None,
        "key_fp": env.get("KEY_FP", ""),
        # BF-D77 (b): is the optional daily-cycle check set up, and the last day it pinged
        "daily_ping_set": env.get("DAILY_PING_SET") == "1",
        "daily_ping": env.get("DAILY_PING", ""),
        # BF-D63: which secret files exist (names only; the worker tests -s, never reads)
        "secrets": {**dict.fromkeys(env.get("SECRETS_PRESENT", "").split(), True),
                    **dict.fromkeys(env.get("SECRETS_MISSING", "").split(), False)},
        # BF-D45: the branch on GitHub vs the running code (classified by the trader)
        "update": {
            "head": env.get("UPD_HEAD", ""), "remote": env.get("UPD_REMOTE", ""),
            "ahead": env.get("UPD_AHEAD", "0"), "files": env.get("UPD_FILES", "").splitlines(),
            "new_config": env.get("UPD_CFG") or None, "new_changelog": env.get("UPD_LOG", ""),
            "subject": env.get("UPD_SUBJECT", ""), "previous": env.get("UPD_PREV", ""),
            "previous_migrations": bool(env.get("UPD_PREV_MIG", "").strip()),
            "ci": env.get("UPD_CI", "unknown"),  # review F13
        },
    }  # fmt: skip


if __name__ == "__main__":
    print(json.dumps(snapshot(dict(os.environ))))
