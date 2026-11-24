"""Strategy versions and updates (BF-D45): which strategy made each decision, what an
incoming code update changes, and when it may be applied.

* **Fingerprint**: a strategy version is the hash of the strategy's config sections
  (``STRATEGY_KEYS`` of config/bfast.yaml) and of its source files (``STRATEGY_FILES``),
  plus the newest entry of ``config/strategy_changelog.yaml`` (plain-English release
  notes). App-only changes (screens, alerts, deploy scripts) do not change it.
* **Stamping**: every decision records ``strategy:<day>`` with the fingerprint, so each
  batch (and through it each fill) has the version that made it; the app splits the
  results by version.
* **Classification** (BF-D53, default-deny): an update is a strategy / trading update
  when it touches anything under trader/, config/ or migrations/ except the UI-only
  files (``UI_ONLY``); else (docs, tests, deploy scripts) app-only.
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
# BF-D53 (M2): default-deny. Any change under trader/, config/ or migrations/ is a
# trading / strategy change, except these UI-only files; docs/, tests/ and the rest
# (deploy scripts, README) are app-only. deploy/classify.py holds the same lists for the
# root worker (a test keeps them equal).
TRADING_DIRS = ("trader/", "config/", "migrations/", "deploy/", "scripts/", ".claude/")
# BF-D60 (N5): infrastructure that changes what runs is not app-only either
TRADING_FILES = ("pyproject.toml", "uv.lock", "alembic.ini", "CLAUDE.md")  # + .claude/: L6
UI_ONLY = (
    "trader/dashboard.py", "trader/webui.py", "trader/app_pages.py", "trader/app_notify.py",
    "trader/tax_screen.py", "trader/server_status.py", "trader/dashboard_demo.py",
    "trader/app_ops.py",  # BF-D75..BF-D80: screens only
    # BF-D81 (review M1): display and alert code; nothing here decides or trades
    "trader/ops_view.py", "trader/info_view.py", "trader/ops_hooks.py",
    # BF-D89: the research pages and the share pages' odds card (display only)
    "trader/app_research.py", "trader/odds.py",
)  # fmt: skip
APP_ONLY_DIRS = ("docs/", "tests/")
# keys of config/bfast.yaml that are not trading settings (the fingerprint ignores them)
NON_TRADING_CONFIG = ("dashboard", "notify", "app", "heartbeat", "telegram", "journal", "tax",
                      "strategy", "running_costs", "info_archive", "research")  # fmt: skip
CHANGELOG = "config/strategy_changelog.yaml"
DECISION_AT = time(22, 20)
BLOCK_BEFORE = timedelta(hours=24)
WORKING = ("SENDING", "SENT", "PARTIAL")


def _h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strategy_config(raw: Mapping[str, Any]) -> dict[str, Any]:
    """The trading part of a config mapping (default-deny, BF-D53: every section except
    the app's own settings)."""
    return {k: v for k, v in raw.items() if k not in NON_TRADING_CONFIG}


def is_trading_path(path: str) -> bool:
    """BF-D53: a changed file that makes an update a strategy / trading update."""
    f = path.strip()
    if not f or f in UI_ONLY or f.startswith(APP_ONLY_DIRS):
        return False
    return f.startswith(TRADING_DIRS) or f in TRADING_FILES


STRATEGY_FILES = (
    "trader/lines/",
    "trader/universe.py",
    "trader/features.py",
    "trader/panel.py",
    "trader/data/forward_store.py",
    "trader/random_twins.py",
    "config/lic_list.csv",
    "config/band_trend_steps.csv",
    "uv.lock",
)


def strategy_hash(root: Path, config_path: Path | None = None) -> str:
    """BF-D72 (strategy review M4): the hash of what decides (the strategy source files,
    the lists and steps, the locked dependencies and the strategy part of the config
    with its LIC / ETP pins). The changelog's newest entry records it (``fingerprint``),
    so a change of the strategy needs a new top changelog entry (a test checks)."""
    h = hashlib.sha256()
    files: list[Path] = []
    for name in STRATEGY_FILES:
        p = root / name
        files += sorted(p.rglob("*.py")) if name.endswith("/") else [p]
    for fp in files:
        if fp.is_file() and "__pycache__" not in fp.parts:
            h.update(fp.relative_to(root).as_posix().encode() + b"\0" + fp.read_bytes() + b"\0")
    cp = config_path or root / "config/bfast.yaml"
    if cp.is_file():
        h.update(config_hash(load_yaml(cp.read_text(encoding="utf-8")) or {}).encode())
    return h.hexdigest()[:12]


def config_hash(raw: Mapping[str, Any]) -> str:
    blob = json.dumps(strategy_config(raw), sort_keys=True, default=str).encode()
    return _h(blob)[:12]


def code_hash(root: Path) -> str:
    """Hash of the trading source under ``root`` (the repository or /app): every file of
    trader/ except the UI-only ones, plus config/lic_list.csv (BF-D53, default-deny)."""
    h = hashlib.sha256()
    files = [
        *sorted((root / "trader").rglob("*.py")),
        root / "config/lic_list.csv",
        root / "uv.lock",
        root / "config/band_trend_steps.csv",
    ]  # BF-D72: deps, steps
    for f in files:
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(root).as_posix()
        if rel in UI_ONLY:
            continue
        h.update(rel.encode() + b"\0" + f.read_bytes() + b"\0")
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
    """Is an incoming update a strategy / trading change (BF-D53, default-deny)?
    ``files``: the changed paths (any trading path counts, config/bfast.yaml included);
    ``old_config`` / ``new_config``: config/bfast.yaml before and after (text), only to
    name the settings that change."""
    reasons: list[str] = []
    for raw in files:
        f = raw.strip()
        if is_trading_path(f):
            reasons.append(f"trading code or data: {f}")
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
