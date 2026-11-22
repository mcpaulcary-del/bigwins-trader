"""Signatures between the app's parts (BF-D46, BF-D48).

* **Dashboard -> trader** (``app_proxy_key``, a secret held by those two containers
  only): the dashboard forwards ``/act/...`` with the viewer's log-in, the browser's
  ``Origin`` / ``Sec-Fetch-Site``, a timestamp and a nonce, signed (HMAC-SHA256) together
  with the method, path and a hash of the body. The trader accepts the log-in only from a
  valid, fresh (30 s), never-seen signature; another container on the ``control`` network
  (or anything else that can reach port 8081) cannot forge it.
* **Trader -> host worker** (``worker_job_key``: a trader-only Docker secret and the same
  root-owned file on the host): each server job is signed over (id, action, commit, force
  bits, requested-at). The root worker runs a job only with a valid signature, so a row
  written into the database by anything else is refused.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections.abc import Mapping

SIGNED = ("x-bw-login", "x-bw-origin", "x-bw-site", "x-bw-host", "x-bw-ts", "x-bw-nonce",
          "x-bw-sig")  # fmt: skip
MAX_SKEW_S = 30


def _mac(key: bytes, text: str) -> str:
    return hmac.new(key, text.encode(), hashlib.sha256).hexdigest()


def proxy_text(login: str, origin: str, site: str, host: str, method: str, path: str,
               body: bytes, ts: str, nonce: str) -> str:  # fmt: skip
    return "\n".join((login, origin, site, host.lower(), method.upper(), path,
                      hashlib.sha256(body).hexdigest(), ts, nonce))  # fmt: skip


def sign_proxy(
    key: bytes,
    login: str,
    origin: str,
    site: str,
    method: str,
    path: str,
    body: bytes,
    now: float | None = None,
    host: str = "",
) -> dict[str, str]:
    """The headers the dashboard adds when it forwards a request (BF-D55: with the host
    the browser asked for, so the trader can check the Origin without a pinned name)."""
    ts = str(int(time.time() if now is None else now))
    nonce = secrets.token_hex(16)
    sig = _mac(key, proxy_text(login, origin, site, host, method, path, body, ts, nonce))
    return {"X-BW-Login": login, "X-BW-Origin": origin, "X-BW-Site": site, "X-BW-Host": host,
            "X-BW-Ts": ts, "X-BW-Nonce": nonce, "X-BW-Sig": sig}  # fmt: skip


class NonceCache:
    """Nonces seen in the last ``2 * MAX_SKEW_S`` seconds (replay refusal)."""

    def __init__(self) -> None:
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def fresh(self, nonce: str, now: float) -> bool:
        with self._lock:
            self._seen = {n: t for n, t in self._seen.items() if now - t < 2 * MAX_SKEW_S}
            if nonce in self._seen:
                return False
            self._seen[nonce] = now
            return True


def verify_proxy(
    key: bytes,
    headers: Mapping[str, str],
    method: str,
    path: str,
    body: bytes,
    nonces: NonceCache,
    now: float | None = None,
) -> dict[str, str] | None:
    """The signed values (login, origin, site) or None (unsigned, stale, replayed)."""
    h = {k.lower(): v for k, v in headers.items()}
    if not all(k in h for k in SIGNED):
        return None
    t = time.time() if now is None else now
    try:
        ts = int(h["x-bw-ts"])
    except ValueError:
        return None
    if abs(t - ts) > MAX_SKEW_S or len(h["x-bw-nonce"]) < 16:
        return None
    want = _mac(key, proxy_text(h["x-bw-login"], h["x-bw-origin"], h["x-bw-site"],
                                h["x-bw-host"], method, path, body, h["x-bw-ts"],
                                h["x-bw-nonce"]))  # fmt: skip
    if not hmac.compare_digest(want, h["x-bw-sig"]) or not nonces.fresh(h["x-bw-nonce"], t):
        return None
    return {"login": h["x-bw-login"].strip().lower(), "origin": h["x-bw-origin"],
            "site": h["x-bw-site"], "host": h["x-bw-host"].strip().lower()}  # fmt: skip


def job_text(job_id: int, action: str, commit: str, force: int, created: str) -> str:
    return f"{job_id}|{action}|{commit}|{force}|{created}"


def sign_job(key: bytes, job_id: int, action: str, commit: str, force: int, created: str) -> str:
    return _mac(key, job_text(job_id, action, commit, force, created))
