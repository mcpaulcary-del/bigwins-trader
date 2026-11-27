"""bigwins worker (BF-D53): is an update a trading / strategy change? Default-deny: any
change under trader/, config/, migrations/, deploy/ or scripts/, or of pyproject.toml,
uv.lock or alembic.ini, except the UI-only files below; docs/, tests/ and the rest are
app-only. The same lists as trader/strategy_version.py (a test
keeps them equal). Standard library only (the host's python3).

BF-D93: a third class, "record": the research code run inside the record container
(``record/code/``, ``record/data_foundation_code/``, its manifest and environment file,
and the record image's two build files), and only when nothing else but documents and
tests changes with it. It is not the trader: applying it never rebuilds or restarts the
trader and never changes the strategy version, but it changes what books the paper record,
so it is never applied automatically (the owner approves it; deploy/autoupdate.py).
``record/tools/`` is NOT in this class: those tools run on the host for the worker, so a
change there is a trading / infrastructure change with every guard of one.

    git diff --name-only HEAD <commit> | python3 classify.py     "strategy", "record" or "app"
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

TRADING_DIRS = (
    "trader/",
    "config/",
    "migrations/",
    "deploy/",
    "scripts/",
    ".claude/",
    "record/",
)  # BF-D93 (review): record/tools runs on the host; only the paths below are "record"
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
    # BF-D93 / BF-D94: the paper record's pages, Health rows and alerts (read-only display)
    "trader/record_view.py",
)  # fmt: skip
APP_ONLY_DIRS = ("docs/", "tests/")
# BF-D93: the paper record's code and its container's build files (class "record")
RECORD_DIRS = ("record/code/", "record/data_foundation_code/")
RECORD_FILES = ("deploy/record.Dockerfile", "deploy/record_requirements.txt",
                "record/MANIFEST.sha256", "record/ENVIRONMENT.json")  # fmt: skip


def is_trading_path(path: str) -> bool:
    f = path.strip()
    if not f or f in UI_ONLY or f.startswith(APP_ONLY_DIRS):
        return False
    if f in RECORD_FILES or f.startswith(RECORD_DIRS):
        return False  # the research code and its container's inputs: class "record"
    return f.startswith(TRADING_DIRS) or f in TRADING_FILES


def is_record_path(path: str) -> bool:
    f = path.strip()
    return f.startswith(RECORD_DIRS) or f in RECORD_FILES


def classify(files: Iterable[str]) -> str:
    fs = [f for f in files if f.strip()]
    if any(is_trading_path(f) for f in fs):
        return "strategy"
    # "record" only when EVERY changed path is record code, a document or a test: a commit
    # that also changes an app file is an app update (the app is rebuilt; the record image
    # too, when the record is on this server). Never automatic either way (autoupdate.py).
    rec = [f for f in fs if is_record_path(f)]
    rest = [f for f in fs if not is_record_path(f) and not f.strip().startswith(APP_ONLY_DIRS)]
    return "record" if rec and not rest else "app"


if __name__ == "__main__":
    print(classify(sys.stdin.read().splitlines()))
