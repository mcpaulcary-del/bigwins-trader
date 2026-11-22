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
from typing import Any

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
              "disk_free_gb"):  # fmt: skip
        v = _num(raw.get(k))
        if v is not None:
            out[k] = v
    for k in ("tailscale", "code_version", "asx", "worker_at", "serve"):
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
    sec = raw.get("secrets")
    if isinstance(sec, Mapping):  # BF-D63: known secret NAMES -> present?; never a value
        from trader.secrets import KNOWN_SECRETS

        out["secrets"] = {str(k): bool(v) for k, v in sec.items() if k in KNOWN_SECRETS}
    log = raw.get("log")
    if isinstance(log, list):
        out["log"] = [clean_line(str(x)) for x in log[-LOG_LINES:]]
    return out
