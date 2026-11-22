"""Strategy versions and updates (BF-D45): which strategy made each decision, what an
incoming code update changes, and when it may be applied.

* **Fingerprint**: a strategy version is the hash of the strategy's config sections
  (``STRATEGY_KEYS`` of config/bfast.yaml) and of its source files (``STRATEGY_FILES``),
  plus the newest entry of ``config/strategy_changelog.yaml`` (plain-English release
  notes). App-only changes (screens, alerts, deploy scripts) do not change it.
* **Stamping**: every decision records ``strategy:<day>`` with the fingerprint, so each
  batch (and through it each fill) has the version that made it; the app splits the
  results by version.
* **Classification**: an update is a strategy update when it touches a strategy file or a
  strategy key of the config; else app-only.
* **Timing** (``strategy.update_mode``): ``immediate`` (default while paper): the host
  worker applies an approved update as soon as the ASX is closed and no order of the
  book is working, then the trader makes an out-of-cycle decision with the new rules
  (the month-end decision path, the same checks), whose batch needs the owner's
  approval like any other. ``next_decision``: applied outside ASX hours, takes effect at
  the next month-end decision, refused in the 24 hours before one unless overridden.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any

from trader.constants import ASX_TZ
from trader.yamlio import load_yaml

STRATEGY_KEYS = ("line", "live_emg2_20", "band_trend", "risk", "execution")
STRATEGY_DATA_KEYS = ("lic_list_sha256", "random_twins", "random_prefix", "random_seed_base",
                      "sim_half_spread", "history_sessions", "etp_list", "lic_list")  # fmt: skip
STRATEGY_FILES = (
    "trader/lines/",
    "trader/universe.py",
    "trader/features.py",
    "trader/panel.py",
    "config/lic_list.csv",
)
CHANGELOG = "config/strategy_changelog.yaml"
DECISION_AT = time(22, 20)
BLOCK_BEFORE = timedelta(hours=24)
WORKING = ("SENDING", "SENT", "PARTIAL")


def _h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strategy_config(raw: Mapping[str, Any]) -> dict[str, Any]:
    """The strategy part of a config mapping (what a strategy version covers)."""
    out = {k: raw.get(k) for k in STRATEGY_KEYS}
    data = raw.get("data") or {}
    out["data"] = {k: data.get(k) for k in STRATEGY_DATA_KEYS} if isinstance(data, Mapping) else {}
    return out


def config_hash(raw: Mapping[str, Any]) -> str:
    blob = json.dumps(strategy_config(raw), sort_keys=True, default=str).encode()
    return _h(blob)[:12]


def code_hash(root: Path) -> str:
    """Hash of the strategy source files under ``root`` (the repository or /app)."""
    h = hashlib.sha256()
    for spec in STRATEGY_FILES:
        p = root / spec
        files = sorted(p.rglob("*.py")) if spec.endswith("/") else [p]
        for f in files:
            if f.is_file():
                h.update(str(f.relative_to(root)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:12]


def load_changelog(text: str) -> list[dict[str, Any]]:
    """Release notes, newest first (``versions:`` list of mappings)."""
    try:
        raw = load_yaml(text) or {}
    except Exception:
        return []
    vs = raw.get("versions") if isinstance(raw, Mapping) else None
    out = [dict(v) for v in vs or [] if isinstance(v, Mapping) and v.get("version")]
    return out


@dataclass(frozen=True)
class Fingerprint:
    version: str  # the newest changelog version, e.g. "EMG2-18 C6 v1.3"
    config: str
    code: str
    commit: str

    @property
    def id(self) -> str:
        return _h(f"{self.config}:{self.code}".encode())[:12]

    def record(self) -> dict[str, str]:
        return {"version": self.version, "config": self.config, "code": self.code,
                "commit": self.commit, "id": self.id}  # fmt: skip

    @property
    def label(self) -> str:
        return f"{self.version} · cfg {self.config[:8]} · code {self.code[:8]}"


def fingerprint(config_path: Path, code_root: Path, commit: str = "") -> Fingerprint:
    from trader.bfast_config import local_path

    raw = load_yaml(config_path.read_text(encoding="utf-8")) or {}
    loc = local_path(config_path)
    if loc.is_file():  # server-only settings may change a strategy key too
        from trader.bfast_config import _merge

        raw = _merge(raw, load_yaml(loc.read_text(encoding="utf-8")) or {})
    cl = config_path.parent / Path(CHANGELOG).name
    notes = load_changelog(cl.read_text(encoding="utf-8")) if cl.is_file() else []
    ver = str(notes[0]["version"]) if notes else "unversioned"
    return Fingerprint(ver, config_hash(raw), code_hash(code_root), commit)


def classify_update(
    files: Iterable[str], old_config: str | None, new_config: str | None
) -> dict[str, Any]:
    """Is an incoming update a strategy change? ``files``: the changed paths;
    ``old_config`` / ``new_config``: config/bfast.yaml before and after (text)."""
    reasons: list[str] = []
    for raw in files:
        f = raw.strip()
        if f and any(f == s or (s.endswith("/") and f.startswith(s)) for s in STRATEGY_FILES):
            reasons.append(f"strategy code: {f}")
    if old_config is not None and new_config is not None:
        try:
            a = strategy_config(load_yaml(old_config) or {})
            b = strategy_config(load_yaml(new_config) or {})
        except Exception:
            reasons.append("config/bfast.yaml could not be read: treated as a strategy change")
        else:
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    reasons.append(f"strategy setting: {k}")
    return {"strategy": bool(reasons), "reasons": reasons[:20]}


def next_decision_at(sessions: Sequence[date], now: datetime) -> datetime | None:
    """22:20 Sydney on the next month-end session (today included until 22:20)."""
    t = now.astimezone(ASX_TZ)
    for a, b in pairwise(sorted(sessions)):
        if b.month != a.month:
            at = datetime.combine(a, DECISION_AT, ASX_TZ)
            if at >= t:
                return at
    return None


def update_block(
    mode: str, strategy: bool, sessions: Sequence[date], now: datetime, override: bool
) -> str | None:
    """Why a strategy update may not be queued now (None: it may)."""
    if not strategy or mode == "immediate" or override:
        return None
    nd = next_decision_at(sessions, now)
    if nd is not None and nd - now <= BLOCK_BEFORE:
        return (
            f"a month-end decision is due {nd:%a %d %b %H:%M}: a strategy update is not applied "
            "in the 24 hours before it (tick the override to do it anyway)"
        )
    return None


def apply_wait(strategy: bool, market_open: bool, working: int) -> str | None:
    """Immediate mode (and every strategy update / rollback): why the worker must wait
    before applying it now (None: apply). Never interrupts working orders."""
    if not strategy:
        return None
    if working:
        return f"waiting: {working} order(s) are working at the broker; applying after they finish"
    if market_open:
        return "waiting: the ASX is open; applying at 16:15 Sydney"
    return None


def segments(stamps: Sequence[tuple[date, str, str]]) -> list[tuple[date, str, str]]:
    """(first day, version id, label) of each run of decisions by one version."""
    out: list[tuple[date, str, str]] = []
    for d, vid, label in sorted(stamps):
        if not out or out[-1][1] != vid:
            out.append((d, vid, label))
    return out
