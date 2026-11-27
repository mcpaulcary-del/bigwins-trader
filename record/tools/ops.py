"""Disk and backup decisions for the record on the server (BF-D93; plan 2.3, 2.4,
owner decision D4). Pure functions: ``deploy/record.sh`` does the tar / age / rclone.

**Disk** (free space on the record's file system): under 5 GB the owner is paged; under
3 GB a month-end daily job is refused (the month-end store refresh needs working space:
that is what failed on the cloud on 16 Nov) and the bulk collectors stop; under 2 GB
only the daily close and the archive's list still run (the archive script itself stops
downloading price-sensitive PDFs under 1 GB free).

**Archive PDFs** (about 15 GB a year) never go into the nightly archive: one encrypted
file per finished archive day, uploaded once, kept off-site for 60 days (D4); older
days stay on the server only, with their hashes in the nightly backup. The nightly
backup takes a "light" copy of the info archive (everything except ``pdf/*.pdf``), so
the 500 MB cap of BF-D86 can no longer silently drop the lists and texts.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
from collections.abc import Iterable, Sequence
from pathlib import Path

from record.tools import hashing

PAGE_GB, TIGHT_GB, CRITICAL_GB = 5.0, 3.0, 2.0
BULK_JOBS = ("collect", "multi", "usfwd")
KEEP_OFFSITE_DAYS = 60
PDF_NAME = re.compile(r"^asxpdf-(\d{4}-\d{2}-\d{2})\.tar\.age$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def disk_level(free_gb: float) -> str:
    if free_gb < CRITICAL_GB:
        return "critical"
    if free_gb < TIGHT_GB:
        return "tight"
    return "low" if free_gb < PAGE_GB else "ok"


def month_end(day: dt.date) -> bool:
    """The last weekday of its month (holidays ignored: at worst one day too careful)."""
    nxt = day + dt.timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += dt.timedelta(days=1)
    return nxt.month != day.month


def disk_gate(job: str, free_gb: float, day: dt.date) -> tuple[bool, str]:
    lvl = disk_level(free_gb)
    if lvl in ("tight", "critical") and job in BULK_JOBS:
        return False, f"only {free_gb:.1f} GB free: {job} does not download until space is freed"
    if lvl in ("tight", "critical") and job == "daily" and month_end(day):
        return False, (f"only {free_gb:.1f} GB free on a month-end: the store refresh needs "
                       f"{TIGHT_GB:.0f} GB; free space, then run: bigwins record run daily")  # fmt: skip
    if lvl == "critical" and job not in ("daily", "archive", "newsc-prepare", "newsc-record",
                                          "newsc-drops-record", "replay"):  # fmt: skip
        return False, f"only {free_gb:.1f} GB free: {job} is stopped"
    return True, lvl


def free_gb(path: Path) -> float:
    return shutil.disk_usage(path).free / 1e9


# ---------------------------------------------------------------- archive PDFs (D4)
def finished_days(info_dir: Path) -> list[str]:
    """Archive days whose price-sensitive step is complete and that hold PDFs."""
    base = info_dir / "asx_notices"
    out = []
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if DAY.match(d.name) and (d / "DONE").exists() and (d / "DONE_PS").exists() \
                and any((d / "pdf").glob("*.pdf")):  # fmt: skip
            out.append(d.name)
    return out


def pdf_plan(local_days: Sequence[str], remote_names: Iterable[str], today: dt.date,
             keep_days: int = KEEP_OFFSITE_DAYS) -> tuple[list[str], list[str]]:  # fmt: skip
    """(days to encrypt and upload, remote file names to delete): the last ``keep_days``
    days are kept off-site, each uploaded once and never changed."""
    cut = str(today - dt.timedelta(days=keep_days))
    have = {m.group(1): n for n in remote_names if (m := PDF_NAME.match(n))}
    upload = [d for d in local_days if d >= cut and d not in have]
    delete = sorted(n for d, n in have.items() if d < cut)
    return upload, delete


def pdf_hashes(day_dir: Path) -> str:
    """``sha256  name`` lines of one day's PDFs (kept in the nightly backup for ever, so a
    PDF fetched again later can be checked)."""
    return "".join(
        f"{hashing.sha_file(p)}  {p.name}\n" for p in sorted((day_dir / "pdf").glob("*.pdf"))
    )


def stage_light(src: Path, dst: Path) -> dict[str, int]:
    """A copy of the info archive without the PDFs (hard links where the file system
    allows, else copies), plus one ``pdf.sha256`` per day. ``dst`` must be new."""
    n = skipped = 0
    for p in sorted(src.rglob("*")) if src.is_dir() else []:
        if p.is_symlink() or not p.is_file():
            continue
        rel = p.relative_to(src)
        if p.suffix == ".pdf" and p.parent.name == "pdf":
            skipped += 1
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(p, out)
        except OSError:
            shutil.copyfile(p, out)
        n += 1
    base = src / "asx_notices"
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if DAY.match(d.name) and (d / "pdf").is_dir():
            out = dst / "asx_notices" / d.name / "pdf.sha256"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(pdf_hashes(d), encoding="utf-8")
    return {"files": n, "pdfs_left_out": skipped}
