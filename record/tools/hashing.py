"""File hashes and tree manifests for the paper record (BF-D93). Standard library only.

A *tree manifest* is ``{relative path: sha256}`` of the files that make the record:
engine states, the record folder (ledger, fence, amendments, ``paper/``, ``multi/``) and
the multi-market state. ``.gz`` files are hashed on their DECOMPRESSED bytes (a gzip
file carries its own timestamp, so two downloads of the same data never match as files).
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path

SKIP_NAMES = (".lock", ".part", ".tmp")
SKIP_PARTS = ("__pycache__",)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_content(path: Path) -> str:
    """SHA-256 of the file, or of what it decompresses to for ``.gz``."""
    if path.suffix != ".gz":
        return sha_file(path)
    h = hashlib.sha256()
    try:
        with gzip.open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
    except (OSError, EOFError):
        return "unreadable-gzip:" + sha_file(path)
    return h.hexdigest()


def wanted(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return not (name.endswith(SKIP_NAMES) or (name.startswith(".") and name.endswith(".lock"))
                or any(p in SKIP_PARTS for p in rel.split("/")))  # fmt: skip


def tree(base: Path, rels: Iterable[str]) -> dict[str, str]:
    """``{path relative to base: content hash}`` of every file under the given folders
    (or single files); symlinks are never followed."""
    out: dict[str, str] = {}
    for rel in rels:
        top = base / rel
        files = [top] if top.is_file() else sorted(top.rglob("*")) if top.is_dir() else []
        for p in files:
            if p.is_symlink() or not p.is_file():
                continue
            r = p.relative_to(base).as_posix()
            if wanted(r):
                out[r] = sha_content(p)
    return out


def manifest_sha(m: Mapping[str, str]) -> str:
    return hashlib.sha256(json.dumps(dict(sorted(m.items())), sort_keys=True).encode()).hexdigest()


def read_sha256sums(text: str) -> dict[str, str]:
    """``sha256sum`` output -> {path: hash} (the code manifest ``record/MANIFEST.sha256``)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        h, _, name = line.strip().partition("  ")
        if len(h) == 64 and name:
            out[name.removeprefix("./")] = h
    return out
