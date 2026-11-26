"""Tool steps of the record jobs (BF-D93): the small pieces of glue the cloud tasks did by
hand or with a subagent, now plain scripts. No network anywhere in this file.

* ``asic_daily``: the CXL paper line reads ASIC's short-position files from
  ``asic_daily/RR*.csv``; the cloud filled that folder with a subagent (download, CRLF to
  LF). The archive already stores the same files gzipped: this writes the LF copies.
* ``gapcheck``: the evening check that every recent ASX day has its announcements and its
  prices (the list page shows only the previous trading day: a missed day is gone).
* ``newsc_record`` / ``newsc_drops_record``: take the cloud raters' replies that the relay
  puller validated, put them byte for byte where the research recorder expects them and
  run it (unedited, behind the fence). Metadata comes from ``meta.json`` as fixed, short,
  printable strings passed as arguments, never through a shell.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from record.tools import paths

SYD = ZoneInfo("Australia/Sydney")
ASIC_NAME = re.compile(r"^RR(\d{8})-\d{3}-SSDailyAggShortPos\.csv\.gz$")
ARCHIVE_START = dt.date(2026, 11, 23)  # the info archive's first day
REPLY = re.compile(r"^[A-Z]{1,3}_\d{2}_p[12]\.json$")
DROPS_REPLY = re.compile(r"^drops_p[12]\.json$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
META_KEYS = ("model", "model_source", "session_id", "subagent_model", "failures")
META_MAX = 400
HERE = Path(__file__).resolve().parent


def write_atomic(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, p)


# ---------------------------------------------------------------- ASIC files for the CXL line
def asic_daily(root: Path, dry_run: bool = False, days: int = 45,
               today: dt.date | None = None) -> int:  # fmt: skip
    src = root / paths.REL_DATA / "asic_short"
    dst = root / "asic_daily"
    today = today or dt.datetime.now(SYD).date()
    new = 0
    for p in sorted(src.glob("RR*.csv.gz")) if src.is_dir() else []:
        m = ASIC_NAME.match(p.name)
        if not m:
            continue
        d = dt.datetime.strptime(m.group(1), "%Y%m%d").replace(tzinfo=SYD).date()
        out = dst / p.name[:-3]
        if (today - d).days > days or out.exists():
            continue
        try:
            with gzip.open(p, "rb") as f:
                data = f.read().replace(b"\r\n", b"\n")
        except (OSError, EOFError):
            print(f"asic_daily: unreadable {p.name}")
            return 1
        if not dry_run:
            write_atomic(out, data)
        new += 1
    print(f"asic_daily: {new} new files")
    return 0


# ---------------------------------------------------------------- gap check
def weekdays(a: dt.date, b: dt.date) -> list[dt.date]:
    return [a + dt.timedelta(days=i) for i in range((b - a).days + 1)
            if (a + dt.timedelta(days=i)).weekday() < 5]  # fmt: skip


def sessions(a: dt.date, b: dt.date) -> list[dt.date]:
    """ASX trading days in [a, b]: the exchange calendar when the container has it."""
    try:
        import exchange_calendars as xc

        cal = xc.get_calendar("XASX", start=str(a - dt.timedelta(days=10)),
                              end=str(b + dt.timedelta(days=10)))  # fmt: skip
        return [x.date() for x in cal.sessions if a <= x.date() <= b]
    except Exception:
        return weekdays(a, b)


def gaps(root: Path, today: dt.date, days: Sequence[dt.date]) -> dict[str, Any]:
    """Which of ``days`` (trading days before ``today``) lack announcements or prices."""
    data = root / paths.REL_DATA
    no_list = [str(d) for d in days if d >= ARCHIVE_START
               and not (data / "asx_notices" / str(d) / "DONE").exists()]  # fmt: skip
    no_ps = [str(d) for d in days if d >= ARCHIVE_START and str(d) not in no_list
             and not (data / "asx_notices" / str(d) / "DONE_PS").exists()]  # fmt: skip
    no_bulk = [str(d) for d in days if not (data / "bulk" / str(d) / "eod.json.gz").exists()]
    return {"checked": [str(d) for d in days], "asof": str(today), "announcements_missing": no_list,
            "price_sensitive_incomplete": no_ps, "prices_missing": no_bulk,
            "ok": not (no_list or no_bulk)}  # fmt: skip


def gapcheck(root: Path, dry_run: bool = False, today: dt.date | None = None) -> int:
    now = dt.datetime.now(SYD)
    today = today or now.date()
    # the list of session D is published on the morning of D+1: before today only
    days = [d for d in sessions(today - dt.timedelta(days=7), today) if d < today]
    res = gaps(root, today, days)
    if not dry_run:
        write_atomic(root / paths.REL_OUT / "sync" / "gaps.json",
                     (json.dumps(res, indent=1, sort_keys=True) + "\n").encode())  # fmt: skip
    print("gapcheck: " + ("ok" if res["ok"] else json.dumps(res, sort_keys=True)))
    return 0 if res["ok"] else 1


# ---------------------------------------------------------------- NEWS-C through the relay
def relay_inbox() -> Path:
    return Path(os.environ.get("BW_RELAY_INBOX", "/relay/inbox"))


def clean_meta(raw: object) -> dict[str, str]:
    """``meta.json`` -> the recorder's arguments: known keys, short printable strings."""
    if not isinstance(raw, dict):
        raise ValueError("meta.json is not an object")
    out: dict[str, str] = {}
    for k in META_KEYS:
        v = raw.get(k)
        if v is None or v == "":
            continue
        if not isinstance(v, str) or len(v) > META_MAX or not v.isprintable() or v.startswith("-"):
            raise ValueError(f"meta.json: bad {k}")
        out[k] = v
    for k in ("model", "model_source"):
        if k not in out:
            raise ValueError(f"meta.json: {k} is required")
    return out


def pending_day(inbox: Path, newsc: Path, marker: str) -> str | None:
    """The newest day with a ``meta.json`` in the relay and no marker yet in the record."""
    base = inbox / "newsc"
    days = sorted(p.name for p in base.iterdir() if p.is_dir() and DAY.match(p.name)) \
        if base.is_dir() else []  # fmt: skip
    for d in reversed(days):
        if (base / d / "meta.json").is_file() and not (newsc / d / marker).exists():
            return d
    return None


def _launch(args: Sequence[str], capture: bool) -> tuple[int, str]:
    cmd = [sys.executable, "-I", str(HERE / "launch.py"), *args]
    r = subprocess.run(cmd, check=False, timeout=900, text=True,
                       stdout=subprocess.PIPE if capture else None)  # fmt: skip
    return r.returncode, r.stdout or ""


def _record(root: Path, dry_run: bool, script: str, sub: str, pattern: re.Pattern[str],
            needed: Sequence[str], day: str, marker: str) -> int:  # fmt: skip
    inbox = relay_inbox() / "newsc" / day
    newsc = root / paths.REL_DATA / "newsc" / day
    have = {p.name for p in inbox.iterdir() if p.is_file() and pattern.match(p.name)}
    missing = [n for n in needed if n not in have]
    if missing:
        print(f"{script} {day}: waiting for {len(missing)} replies (e.g. {missing[0]})")
        return 0
    try:
        meta = clean_meta(json.loads((inbox / "meta.json").read_text(encoding="utf-8")))
    except (OSError, ValueError) as e:
        print(f"{script} {day}: REFUSED: {e}")
        return 2
    for n in needed:  # byte for byte; a reply already in place is never replaced
        if not (newsc / sub / n).exists():
            write_atomic(newsc / sub / n, (inbox / n).read_bytes())
    (newsc / sub).mkdir(parents=True, exist_ok=True)
    args = [script, "--day", day, "--ratings-dir", str(newsc / sub),
            "--model", meta["model"], "--model-source", meta["model_source"]]  # fmt: skip
    for k, flag in (("session_id", "--session-id"), ("subagent_model", "--subagent-model"),
                    ("failures", "--failures")):  # fmt: skip
        if k in meta:
            args += [flag, meta[k]]
    if dry_run:
        args.append("--dry-run")
    rc, out = _launch(args, capture=dry_run)
    if rc == 0 and dry_run:  # the entry the shadow WOULD have written, for the compare
        write_atomic(
            root / paths.REL_OUT / "sync" / f"dryrun_{script[:-3]}_{day}.json", out.encode()
        )
    if rc == 0:
        write_atomic(newsc / marker, (day + "\n").encode())
    return rc


def newsc_record(root: Path, dry_run: bool = False) -> int:
    marker = "RELAY_DRYRUN" if dry_run else "RELAY_RECORDED"
    newsc = root / paths.REL_DATA / "newsc"
    day = pending_day(relay_inbox(), newsc, marker)
    if day is None:
        print("newsc_record: nothing waiting in the relay")
        return 0
    try:
        man = json.loads((newsc / day / "manifest.json").read_text(encoding="utf-8"))
        needed = [f"{b['batch']}_p{n}.json" for b in man["batches"] for n in (1, 2)]
    except (OSError, ValueError, KeyError, TypeError):
        print(f"newsc_record {day}: REFUSED: no prepared manifest on this machine")
        return 2
    if any(not REPLY.match(n) for n in needed):
        print(f"newsc_record {day}: REFUSED: unexpected batch name")
        return 2
    return _record(root, dry_run, "newsc_record.py", "incoming", REPLY, needed, day, marker)


def newsc_drops_record(root: Path, dry_run: bool = False) -> int:
    marker = "RELAY_DROPS_DRYRUN" if dry_run else "RELAY_DROPS_RECORDED"
    newsc = root / paths.REL_DATA / "newsc"
    day = pending_day(relay_inbox(), newsc, marker)
    if day is None:
        print("newsc_drops_record: nothing waiting in the relay")
        return 0
    try:
        man = json.loads((newsc / day / "drops_manifest.json").read_text(encoding="utf-8"))
        needed = ["drops_p1.json", "drops_p2.json"] if man.get("dossier_path") else []
    except (OSError, ValueError):
        print(f"newsc_drops_record {day}: no drops manifest (big-drop step not run): skipped")
        return 0
    return _record(root, dry_run, "newsc_drops_record.py", "drops_incoming", DROPS_REPLY,
                   needed, day, marker)  # fmt: skip


TOOLS: dict[str, Callable[[Path, bool], int]] = {"asic_daily": asic_daily, "gapcheck": gapcheck, "newsc_record": newsc_record,
         "newsc_drops_record": newsc_drops_record}  # fmt: skip
