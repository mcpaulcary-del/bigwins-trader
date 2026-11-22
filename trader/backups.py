"""The app's side of backups (BF-D64): results, the recovery-key reveal and the readable
daily summary. The backups themselves are made by the root host worker
(``deploy/backup.py``); nothing here reads a secret file.

* ``record_result``: the worker's backup / restore-test result (cleaned: numbers, names,
  ok flags; never a path to a secret or a value) into app state ``backup-last`` and a
  30-entry ``backup-history``.
* Recovery key reveal: the worker seals the age key with ``worker_job_key`` (an
  HMAC-SHA256 keystream with a random nonce and a MAC; the same construction in the
  worker's ``gitops.py seal``) into ``backup-key-sealed``; the trader unseals it only for
  an allowed log-in who confirmed with the code, shows it once and clears it. The plain
  key is never in the journal, an inbox message or a push.
* ``daily_summary``: one plain HTML page of the day (value, holdings, orders, messages) for
  OneDrive ``reports/YYYY/``; no secret, no account id.
"""

from __future__ import annotations

import hashlib
import hmac
import html
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from trader.app_store import get_state, set_state
from trader.journal import Journal

HISTORY = 30
REVEAL_TTL_S = 600


def _clean(r: Mapping[str, Any]) -> dict[str, Any]:
    def part(x: Any) -> dict[str, Any] | None:
        if not isinstance(x, Mapping):
            return None
        out: dict[str, Any] = {"ok": bool(x.get("ok", True))}
        for k in ("archive", "size", "files", "error"):
            if k in x:
                out[k] = str(x[k])[:120] if k in ("archive", "error") else x[k]
        return out

    return {
        "kind": str(r.get("kind", "backup"))[:20],
        "ok": bool(r.get("ok")),
        "at": str(r.get("at", ""))[:20],
        "seconds": r.get("seconds"),
        "local": part(r.get("local")),
        "remote": part(r.get("remote")),
        "files": r.get("files"),
        "bad": [str(b)[:120] for b in (r.get("bad") or [])][:10],
        "ledger_files": r.get("ledger_files"),
        "journal_dump": r.get("journal_dump"),
        "error": str(r.get("error", ""))[:200],
        "onedrive": r.get("onedrive"),
    }


def record_result(j: Journal, raw: Mapping[str, Any], now: datetime) -> dict[str, Any]:
    r = _clean(raw)
    key = "restore-test-last" if r["kind"] == "restore_test" else "backup-last"
    set_state(j, key, r, now)
    st = get_state(j, "backup-history")
    hist = list(st[0]) if st and isinstance(st[0], list) else []
    set_state(j, "backup-history", [{**r, "recorded": now.isoformat()}, *hist][:HISTORY], now)
    return r


# ---------------------------------------------------------------- sealed key reveal


def _stream(key: bytes, nonce: bytes, n: int) -> bytes:
    out = b""
    i = 0
    while len(out) < n:
        out += hmac.new(key, b"stream" + nonce + i.to_bytes(4, "big"), hashlib.sha256).digest()
        i += 1
    return out[:n]


def seal(key: bytes, plain: bytes, nonce: bytes) -> str:
    """HMAC-SHA256 keystream encryption with a MAC (encrypt-then-MAC); hex."""
    ct = bytes(a ^ b for a, b in zip(plain, _stream(key, nonce, len(plain)), strict=True))
    tag = hmac.new(key, b"mac" + nonce + ct, hashlib.sha256).digest()
    return (nonce + tag + ct).hex()


def unseal(key: bytes, sealed: str) -> bytes | None:
    try:
        raw = bytes.fromhex(sealed)
    except ValueError:
        return None
    nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
    want = hmac.new(key, b"mac" + nonce + ct, hashlib.sha256).digest()
    if len(nonce) != 16 or not hmac.compare_digest(want, tag):
        return None
    return bytes(a ^ b for a, b in zip(ct, _stream(key, nonce, len(ct)), strict=True))


def take_sealed(j: Journal, now: datetime) -> dict[str, Any] | None:
    """The worker's sealed key if it is fresh (``REVEAL_TTL_S``); else None."""
    st = get_state(j, "backup-key-sealed")
    if not st or not isinstance(st[0], dict) or not st[0].get("sealed"):
        return None
    if (now - st[1]).total_seconds() > REVEAL_TTL_S:
        return None
    return dict(st[0])


def clear_sealed(j: Journal, now: datetime, login: str) -> None:
    set_state(j, "backup-key-sealed", {}, now)
    j.mark_job(f"backup-key-shown:{now.isoformat()}", {"login": login}, now)


# ---------------------------------------------------------------- readable daily summary


def daily_summary(v: Any, inbox: list[dict[str, Any]], label: str) -> str:
    """A self-contained HTML page of the day; no secrets, no account id."""

    def e(x: object) -> str:
        return html.escape(str(x))

    rows = "".join(
        f"<tr><td>{e(h.code)}</td><td>{h.qty}</td><td>{e(h.mark)}</td><td>{e(h.value)}</td>"
        f"<td>{e(h.gain)}</td><td>{h.days_held if h.days_held is not None else ''}</td></tr>"
        for h in v.holdings
    )
    orders = "".join(
        f"<tr><td>{e(o.batch_id)}</td><td>{o.seq}</td><td>{e(o.side)}</td><td>{o.qty}</td>"
        f"<td>{e(o.code)}</td><td>{e(o.value)}</td><td>{e(o.status)}</td></tr>"
        for o in v.orders
    )
    day = v.series[-1][0] if v.series else v.now.date()
    msgs = "".join(
        f"<li>{e(r['at'])} [{e(r['kind'])}] {e(r['title'])}</li>"
        for r in inbox
        if r["at"] is not None and r["at"].date() == day
    )
    css = ("body{font:14px system-ui,sans-serif;max-width:760px;margin:20px auto;padding:0 12px}"
           "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;"
           "padding:4px;text-align:left}")  # fmt: skip
    return (
        f"<!doctype html><meta charset='utf-8'><title>Big Wins {e(day)}</title><style>{css}"
        f"</style><h1>Big Wins {e(label)} - {e(day)}</h1>"
        f"<p>Value <b>A${e(v.value)}</b> · cash A${e(v.cash)} · money in A${e(v.capital_in)} · "
        f"safety {e(v.safety)}</p><h2>Holdings ({len(v.holdings)})</h2><table><tr><th>Code</th>"
        "<th>Qty</th><th>Last price</th><th>Value</th><th>Gain</th><th>Days</th></tr>"
        f"{rows}</table><h2>Latest decision's orders</h2><table><tr><th>Batch</th><th>#</th>"
        "<th>Side</th><th>Qty</th><th>Code</th><th>~Value</th><th>Status</th></tr>"
        f"{orders}</table><h2>Messages of the day</h2><ul>{msgs}</ul>"
        "<p><small>Made by the Big Wins server for your records. Not tax advice.</small></p>"
    )
