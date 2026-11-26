"""Sync tools between the two machines (BF-D93; plan 3.1 and 5). Standard library only.

* ``cloud_manifest``: content hashes of one machine's states, record outputs, archive and
  NEWS-C input files, with the ledger entries its jobs appended for the day. No data.
  It travels by the nightly ``paper-record`` push and by the relay.
* ``make``: one tar of the raw input files that are new or changed since the last bundle
  (an index of what was already sent is kept beside the data), with a ``BUNDLE.json``
  listing every member and its SHA-256. Plain tar, no compression (the inputs are gzip
  already). The inputs are EODHD files: the bundle goes only to the owner's own OneDrive.
* ``apply``: verify first, write second. Every member must be listed, be a regular file
  under one of the input folders, and match its SHA-256; a link, a device, an absolute or
  ``..`` path, an unlisted member, or a hash mismatch refuses the whole bundle and
  nothing is written.

The same two functions serve both directions: cloud to server in the parallel week,
server to cloud for the standby afterwards.
"""

from __future__ import annotations

import io
import json
import os
import tarfile
import time
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from record.tools import hashing, paths
from record.tools import ledgerlib as L
from record.tools import record_compare as RC

INPUT_DIRS = ("bigwins_forward/data/bulk", "bigwins_forward/data/eodhd",
              "bigwins_forward/data/estimates_pit", "bigwins_forward/data/newlist", "asic_daily")  # fmt: skip
BIG = (".pkl", ".pkl.gz", ".npz", ".parquet")  # rebuilt panels: never bundled by default
INDEX = "bigwins_forward/out/sync/bundle_index.json"
META = "BUNDLE.json"
MAX_MEMBER = 200 * 1024 * 1024


class BundleError(ValueError):
    pass


def cloud_manifest(root: Path, day: str, archive_days: Sequence[str],
                   now: float | None = None) -> dict[str, Any]:  # fmt: skip
    es = L.read(paths.ledger(root))
    head = L.verify(es)
    return {
        "schema": 1, "day": day, "archive_days": list(archive_days),
        "made_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "files": RC.shadow_files(root, archive_days),
        "ledger_head": head, "ledger_seq": len(es),
        "ledger_entries": RC.day_entries(es, day),
    }  # fmt: skip


def _inputs(root: Path, dirs: Iterable[str], with_panels: bool) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for rel in dirs:
        top = root / rel
        for p in sorted(top.rglob("*")) if top.is_dir() else []:
            r = p.relative_to(root).as_posix()
            if p.is_symlink() or not p.is_file() or not hashing.wanted(r):
                continue
            if not with_panels and r.endswith(BIG):
                continue
            out[r] = p
    return out


def read_index(root: Path) -> dict[str, str]:
    try:
        raw = json.loads((root / INDEX).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in raw.items()} if isinstance(raw, dict) else {}


def write_index(root: Path, index: Mapping[str, str]) -> None:
    p = root / INDEX
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".part")
    tmp.write_text(json.dumps(dict(sorted(index.items()))), encoding="utf-8")
    os.replace(tmp, p)


def make(root: Path, day: str, out: Path, dirs: Sequence[str] = INPUT_DIRS,
         with_panels: bool = False, mark_only: bool = False) -> dict[str, Any]:  # fmt: skip
    """Bundle what changed since the last bundle. ``mark_only``: record everything as
    already sent without writing a tar (run once after the seed)."""
    index = read_index(root)
    files = _inputs(root, dirs, with_panels)
    cur = {r: hashing.sha_file(p) for r, p in files.items()}
    new = {r: h for r, h in cur.items() if index.get(r) != h}
    if mark_only:
        write_index(root, cur)
        return {"day": day, "members": 0, "marked": len(cur)}
    meta = {"schema": 1, "day": day, "members": new}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".part")
    with tarfile.open(tmp, "w") as tar:
        blob = json.dumps(meta, sort_keys=True).encode()
        ti = tarfile.TarInfo(META)
        ti.size = len(blob)
        tar.addfile(ti, io.BytesIO(blob))
        for r in sorted(new):
            ti = tarfile.TarInfo(r)
            ti.size = files[r].stat().st_size
            ti.mode = 0o644
            with files[r].open("rb") as f:
                tar.addfile(ti, f)
    os.replace(tmp, out)
    write_index(root, cur)
    return {"day": day, "members": len(new), "bytes": out.stat().st_size,
            "sha256": hashing.sha_file(out)}  # fmt: skip


def _safe(name: str, dirs: Sequence[str]) -> bool:
    parts = name.split("/")
    return (not name.startswith("/") and ".." not in parts and "" not in parts and "\\" not in name
            and any(name.startswith(d + "/") for d in dirs))  # fmt: skip


def apply(bundle: Path, root: Path, dirs: Sequence[str] = INPUT_DIRS) -> dict[str, Any]:
    """Verify the whole bundle, then write its files (atomic renames)."""
    staged: dict[str, bytes] = {}
    try:
        with tarfile.open(bundle, "r:") as tar:
            members = tar.getmembers()
            if not members or members[0].name != META or not members[0].isreg():
                raise BundleError("no BUNDLE.json first in the tar")
            f0 = tar.extractfile(members[0])
            meta = json.loads(f0.read().decode()) if f0 is not None else {}
            want = meta.get("members") if isinstance(meta, dict) else None
            if not isinstance(want, dict) or meta.get("schema") != 1:
                raise BundleError("BUNDLE.json is not a schema-1 member list")
            for m in members[1:]:
                if not m.isreg() or m.name not in want or not _safe(m.name, dirs):
                    raise BundleError(f"member not allowed: {m.name[:120]}")
                if m.size > MAX_MEMBER or m.name in staged:
                    raise BundleError(f"member too large or repeated: {m.name[:120]}")
                f = tar.extractfile(m)
                data = f.read() if f is not None else b""
                if L.sha_bytes(data) != want[m.name]:
                    raise BundleError(f"hash mismatch: {m.name[:120]}")
                staged[m.name] = data
    except (tarfile.TarError, OSError, ValueError, UnicodeDecodeError) as e:
        if isinstance(e, BundleError):
            raise
        raise BundleError(f"unreadable bundle: {type(e).__name__}") from e
    missing = set(want) - set(staged)
    if missing:
        raise BundleError(f"{len(missing)} listed members are not in the tar")
    for name, data in staged.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".part")
        tmp.write_bytes(data)
        os.replace(tmp, p)
    return {"day": meta.get("day"), "applied": len(staged)}
