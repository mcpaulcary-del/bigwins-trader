"""The host's status snapshot for the app's Server screen (BF-D42).

The host worker (``deploy/bigwins.sh worker``, root on the host) sends a small JSON
snapshot through ``trader-bf server-jobs status``: load, memory, disk, uptime, Tailscale,
container states, the code version and the trader's last log lines. Only the keys below
are kept, every value is coerced to a plain type, and log lines are cleaned of anything
that looks secret (tokens, long keys, URLs with paths or queries, passwords, e-mail
addresses) before they reach the journal and the phone.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

from trader.constants import ASX_TZ

LOG_LINES = 40
_SECRETISH = (
    re.compile(r"bot\d+:[A-Za-z0-9_-]{20,}"),  # a Telegram bot token
    re.compile(r"https?://\S+"),  # URLs (a healthchecks ping URL is a secret)
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # e-mail addresses / log-ins
    re.compile(r"(?i)(password|passwd|token|secret|apikey|api_key|auth)\S*\s*[=:]\s*\S+"),
    re.compile(r"\b(?:DU|U)\d{5,}\b"),  # IBKR account ids
    re.compile(r"[A-Za-z0-9+/_=-]{32,}"),  # long keys / base64
)


def clean_line(line: str) -> str:
    out = line.replace("\r", "").rstrip()[:300]
    for rx in _SECRETISH:
        out = rx.sub("[hidden]", out)
    return out


def _num(x: Any) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def clean_status(raw: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k in ("load1", "load5", "cpus", "mem_used_pct", "disk_used_pct", "uptime_s",
              "disk_free_gb", "backup_age_h"):  # fmt: skip
        v = _num(raw.get(k))
        if v is not None:
            out[k] = v
    for k in ("tailscale", "code_version", "asx", "worker_at", "serve", "key_fp"):
        if k in raw:
            out[k] = clean_line(str(raw[k]))[:120]
    cont = raw.get("containers")
    if isinstance(cont, list):
        out["containers"] = [
            {"name": clean_line(str(c.get("name", "")))[:40],
             "state": clean_line(str(c.get("state", "")))[:80]}
            for c in cont[:12] if isinstance(c, Mapping)
        ]  # fmt: skip
    if "onedrive" in raw:  # BF-D64
        out["onedrive"] = bool(raw.get("onedrive"))
    tm = raw.get("timers")
    if isinstance(tm, Mapping):  # BF-D81 (S7): which systemd timers exist (known names only)
        out["timers"] = {k: bool(v) for k, v in tm.items()
                         if k in ("worker", "backup", "weekly", "info", "twin")}  # fmt: skip
    if "daily_ping_set" in raw:  # BF-D77 (b): the optional daily-cycle check (never its URL)
        out["daily_ping_set"] = bool(raw.get("daily_ping_set"))
        dp = str(raw.get("daily_ping") or "")
        if len(dp) == 10 and dp[4] == "-" and dp[7] == "-" and dp.replace("-", "").isdigit():
            out["daily_ping"] = dp
    sec = raw.get("secrets")
    if isinstance(sec, Mapping):  # BF-D63: known secret NAMES -> present?; never a value
        from trader.secrets import KNOWN_SECRETS

        out["secrets"] = {str(k): bool(v) for k, v in sec.items() if k in KNOWN_SECRETS}
    log = raw.get("log")
    if isinstance(log, list):
        out["log"] = [clean_line(str(x)) for x in log[-LOG_LINES:]]
    return out


HOST_PAGE_EVERY = 3600  # seconds between repeats of the same host page


def host_alerts(status: Mapping[str, Any] | None, at: datetime | None, now: datetime,
                worker_installed: bool = True) -> list[str]:  # fmt: skip
    """Review F9 / security M3: what about the server should page the owner. The worker
    writes its snapshot every 30 s; older than 5 minutes means the worker (or the host)
    is not running. Disk over 80%, available memory under 10%, no good backup for 26
    hours."""
    out: list[str] = []
    if status is None or at is None:
        return out
    if worker_installed and now - at > timedelta(minutes=5):
        out.append(f"server worker silent since {at.astimezone(ASX_TZ):%a %H:%M}: the host "
                   "status, server jobs and backups are not running "
                   "(sudo bigwins install-worker)")  # fmt: skip
    disk = status.get("disk_used_pct")
    if isinstance(disk, int | float) and disk > 80:
        out.append(f"server disk {disk:.0f}% used (over 80%): free space (bigwins status)")
    mem = status.get("mem_used_pct")
    if isinstance(mem, int | float) and mem > 90:
        out.append(f"server memory {100 - mem:.0f}% available (under 10%)")
    age = status.get("backup_age_h")
    if isinstance(age, int | float) and age > 26:
        when = "ever" if age >= 9999 else f"{age:.0f} hours"
        out.append(f"no good backup for {when} (over 26): check Backups")
    return out


def page_host(j: Any, say: Any, now: datetime) -> list[str]:
    """The trader's loop hook: page each host alert at most once an hour."""
    from trader.app_store import get_state, set_state

    got = get_state(j, "host-status")
    if got is None:
        return []
    alerts = host_alerts(got[0], got[1], now)
    seen = get_state(j, "host-paged")
    last: dict[str, str] = dict(seen[0]) if seen and isinstance(seen[0], Mapping) else {}
    sent = []
    for a in alerts:
        key = a.split(":")[0][:40]
        prev = last.get(key)
        if prev and (now - datetime.fromisoformat(prev)).total_seconds() < HOST_PAGE_EVERY:
            continue
        say("PAGE " + a)
        last[key] = now.isoformat()
        sent.append(a)
    if sent:
        set_state(j, "host-paged", last, now)
    return sent
