"""The display copy of the paper record that the app reads (BF-D94). The host worker
refreshes it after every record job (this server's record) or, before the cut-over, from
the research environment's nightly ``paper-record`` copy. Display files only: the
scorecards, holdings, cost comparison and movers lists. Never the ledger, the fence, the
engine states or any vendor data file; the app never sees the record tree itself.

When the booked day changes, the previous day's ``holdings_latest.csv`` is kept as
``holdings_prev.csv`` so the app can show each holding's day move from the record's own
two closes. Standard library only.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from record.tools import paths

MAX_BYTES = 5 * 1024 * 1024
SKIP_PREFIX = ("controls_targets_",)  # thousands of rows of twin targets: not a display file
KEEP_MOVERS = 40


def _asof(p: Path) -> str:
    try:
        with p.open(newline="", encoding="utf-8-sig") as f:
            row = next(csv.DictReader(f), None)
    except (OSError, csv.Error, UnicodeDecodeError):
        return ""
    return str((row or {}).get("asof", ""))[:10]


def view_copy(
    src: Path, dst: Path, source: str, note: str, now: float | None = None
) -> dict[str, Any]:
    paper = src / paths.REL_RECORD / "paper"
    mv = src / paths.REL_OUT / "movers"
    base = src.resolve()
    # the folders themselves must be real folders INSIDE the source tree: a link planted in a
    # fetched copy can never make this read (and publish to the app) anything else
    for d in (paper, mv):
        if d.exists() and (d.is_symlink() or base not in d.resolve().parents):
            return {"ok": False, "error": f"{d.name} is a link or lies outside the source tree"}
    if not (paper / "scorecard_latest.csv").is_file():
        return {"ok": False, "error": "no scorecard in the source tree"}
    tmp = dst / ".new"
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "paper").mkdir(parents=True)
    (tmp / "movers").mkdir()
    n = 0
    for p in sorted(paper.iterdir()):
        if p.is_symlink() or not p.is_file() or p.suffix not in (".csv", ".md") \
                or p.name.startswith(SKIP_PREFIX) or p.stat().st_size > MAX_BYTES:  # fmt: skip
            continue
        shutil.copyfile(p, tmp / "paper" / p.name)
        n += 1
    for p in sorted(mv.glob("movers_*.md"))[-KEEP_MOVERS:] if mv.is_dir() else []:
        if p.is_file() and not p.is_symlink() and p.stat().st_size <= MAX_BYTES:
            shutil.copyfile(p, tmp / "movers" / p.name)
    old, new = dst / "paper" / "holdings_latest.csv", tmp / "paper" / "holdings_latest.csv"
    prev = dst / "paper" / "holdings_prev.csv"
    if old.is_file() and new.is_file() and _asof(old) and _asof(old) != _asof(new):
        shutil.copyfile(old, tmp / "paper" / "holdings_prev.csv")
    elif prev.is_file():
        shutil.copyfile(prev, tmp / "paper" / "holdings_prev.csv")
    meta = {"source": source[:160], "note": note[:200],
            "refreshed": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
            "asof": _asof(tmp / "paper" / "scorecard_latest.csv")}  # fmt: skip
    (tmp / "source.json").write_text(json.dumps(meta, sort_keys=True) + "\n", encoding="utf-8")
    for p in tmp.rglob("*"):
        os.chmod(p, 0o755 if p.is_dir() else 0o644)
    for name in ("paper", "movers"):
        shutil.rmtree(dst / (name + ".old"), ignore_errors=True)
        if (dst / name).is_dir():
            os.replace(dst / name, dst / (name + ".old"))
        os.replace(tmp / name, dst / name)
        shutil.rmtree(dst / (name + ".old"), ignore_errors=True)
    os.replace(tmp / "source.json", dst / "source.json")
    shutil.rmtree(tmp, ignore_errors=True)
    return {"ok": True, "files": n, **meta}
