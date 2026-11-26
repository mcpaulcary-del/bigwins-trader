"""The hash-chained ledger, read and written exactly as the research helper
``record/code/fwd_ledger.py`` does (BF-D93; a test appends the same fields with both and
compares the bytes). Standard library only. Used by the host-side tools (handover,
compare, relay); the paper jobs keep using ``fwd_ledger`` itself, under the fence.

Entry format: one JSON object a line, ``sort_keys=True``; ``seq`` from 1;
``prev_entry_sha256`` is the previous entry's hash (64 zeros first); ``entry_sha256`` is
the SHA-256 of the entry's JSON without that key. Append and verify run under an
exclusive / shared ``flock`` on ``LEDGER.jsonl.lock`` (the research code's own lock).
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import time
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

ZERO = "0" * 64
Entry = dict[str, Any]


class ChainError(ValueError):
    """The ledger does not verify (a broken link or a changed entry)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def entry_hash(e: Mapping[str, Any]) -> str:
    x = {k: v for k, v in e.items() if k != "entry_sha256"}
    return sha_bytes(json.dumps(x, sort_keys=True).encode())


@contextlib.contextmanager
def locked(path: Path, exclusive: bool = True) -> Iterator[None]:
    with open(str(path) + ".lock", "a", encoding="utf-8") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def parse(text: str) -> list[Entry]:
    out: list[Entry] = []
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError as ex:
            raise ChainError(f"line {n} is not JSON") from ex
        if not isinstance(e, dict):
            raise ChainError(f"line {n} is not an entry")
        out.append(e)
    return out


def read(path: Path) -> list[Entry]:
    if not path.exists():
        return []
    return parse(path.read_text(encoding="utf-8"))


def verify(entries: Sequence[Mapping[str, Any]]) -> str:
    """The head (last entry's hash; 64 zeros for an empty ledger). Raises ChainError."""
    prev = ZERO
    for n, e in enumerate(entries, 1):
        if e.get("seq") != n:
            raise ChainError(f"seq {e.get('seq')!r} at position {n}")
        if e.get("prev_entry_sha256") != prev:
            raise ChainError(f"chain broken at seq {n}")
        if entry_hash(e) != e.get("entry_sha256"):
            raise ChainError(f"entry hash bad at seq {n}")
        prev = str(e["entry_sha256"])
    return prev


def head(path: Path) -> str:
    with locked(path, exclusive=False):
        return verify(read(path))


def append(path: Path, fields: Mapping[str, Any], now: float | None = None) -> Entry:
    """Append one entry (the caller has already passed the fence, ``fence.decide``)."""
    with locked(path, exclusive=True):
        es = read(path)
        prev = verify(es)
        e: Entry = dict(fields)
        e["seq"] = len(es) + 1
        e["prev_entry_sha256"] = prev
        e.setdefault("recorded_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
        e["entry_sha256"] = sha_bytes(json.dumps(e, sort_keys=True).encode())
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return e


def is_prefix(short: Sequence[Mapping[str, Any]], long: Sequence[Mapping[str, Any]]) -> bool:
    """``short`` is the start of ``long`` (same entries, in order): no fork between them."""
    return len(short) <= len(long) and all(
        a.get("entry_sha256") == b.get("entry_sha256") for a, b in zip(short, long, strict=False)
    )
