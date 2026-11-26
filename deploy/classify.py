"""bigwins worker (BF-D53): is an update a trading / strategy change? Default-deny: any
change under trader/, config/, migrations/, deploy/ or scripts/, or of pyproject.toml,
uv.lock or alembic.ini, except the UI-only files below; docs/, tests/ and the rest are
app-only. The same lists as trader/strategy_version.py (a test
keeps them equal). Standard library only (the host's python3).

BF-D93: a third class, "record": the paper record's own code (``record/`` and the record
image's two build files). It is not the trader: applying it never rebuilds or restarts the
trader and never changes the strategy version, but it changes what books the paper record,
so it is never applied automatically (the owner approves it; deploy/autoupdate.py).

    git diff --name-only HEAD <commit> | python3 classify.py     "strategy", "record" or "app"
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

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
    # BF-D93 / BF-D94: the paper record's pages, Health rows and alerts (read-only display)
    "trader/record_view.py",
)  # fmt: skip
APP_ONLY_DIRS = ("docs/", "tests/")
# BF-D93: the paper record's code and its container's build files (class "record")
RECORD_DIRS = ("record/",)
RECORD_FILES = ("deploy/record.Dockerfile", "deploy/record_requirements.txt")


def is_trading_path(path: str) -> bool:
    f = path.strip()
    if not f or f in UI_ONLY or f.startswith(APP_ONLY_DIRS) or f in RECORD_FILES:
        return False
    return f.startswith(TRADING_DIRS) or f in TRADING_FILES


def is_record_path(path: str) -> bool:
    f = path.strip()
    return f.startswith(RECORD_DIRS) or f in RECORD_FILES


def classify(files: Iterable[str]) -> str:
    fs = [f for f in files if f.strip()]
    if any(is_trading_path(f) for f in fs):
        return "strategy"
    return "record" if any(is_record_path(f) for f in fs) else "app"


if __name__ == "__main__":
    print(classify(sys.stdin.read().splitlines()))
