"""Immutable raw-file store with a sha256 manifest, and bitemporal reads (DAT-09, DAT-16, DAT-18).

Raw responses are stored unchanged as
``<root>/raw/{source}/{fetch_date}/{name}.{HHMMSSffffff}Z.{ext}.gz`` where
``fetch_date`` is the UTC date of the fetch. Files are written once (never
overwritten, read-only mode) and each one is appended to the directory's
``MANIFEST.sha256`` (``<sha256>  <file name>``), so ``verify`` can prove that no
stored file changed (DAT-09). Gzip headers carry no timestamp, so the same bytes
always hash the same.

Rented data (for example a Norgate rental) lives only in a separate ``rental/``
tree, every file with a deletion date, and ``RentalStore.purge`` deletes it on
expiry (DAT-16). The raw store refuses to write into the rental tree.

Market tables are append-only and bitemporal: the value "as known at T" for a
key is the row with the latest fetch time <= T (``latest_row``).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from trader.data.models import RawBar
from trader.timeutil import ensure_utc

MANIFEST = "MANIFEST.sha256"
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")
_SOURCES = frozenset({"eodhd", "flex", "rba", "issuer", "abs"})
_EXTS = frozenset({"json", "xml", "csv", "txt"})
READ_ONLY = 0o440


class RawStoreError(Exception):
    pass


@dataclass(frozen=True)
class RawFile:
    path: Path
    sha256: str
    fetch_time: datetime
    source: str

    @property
    def relpath(self) -> str:
        return "/".join(self.path.parts[-4:])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class RawStore:
    """Append-only raw-response store for one user's licensed data (USR-05)."""

    def __init__(self, root: Path, licensee: str) -> None:
        self.root = root.resolve()
        self.raw = self.root / "raw"
        self.licensee = licensee
        if "rental" in self.raw.parts:
            raise RawStoreError("the raw store must not live inside the rental/ tree (DAT-16)")

    def _dir(self, source: str, fetch_time: datetime) -> Path:
        if source not in _SOURCES:
            raise RawStoreError(f"unknown source {source!r}")
        return self.raw / source / ensure_utc(fetch_time).date().isoformat()

    def put(
        self, source: str, name: str, payload: bytes, fetch_time: datetime, ext: str = "json"
    ) -> RawFile:
        """Store ``payload`` unchanged; returns the file and its sha256 (DAT-09)."""
        if not _NAME_RE.fullmatch(name) or ext not in _EXTS:
            raise RawStoreError(f"unsafe raw file name {name!r}.{ext}")
        ft = ensure_utc(fetch_time)
        d = self._dir(source, ft)
        d.mkdir(parents=True, exist_ok=True)
        fname = f"{name}.{ft.strftime('%H%M%S%f')}Z.{ext}.gz"
        path = d / fname
        data = gzip.compress(payload, mtime=0)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640)
        except FileExistsError:
            raise RawStoreError(f"raw file already exists, never overwritten: {path}") from None
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        path.chmod(READ_ONLY)
        digest = hashlib.sha256(data).hexdigest()
        with (d / MANIFEST).open("a", encoding="ascii") as m:
            m.write(f"{digest}  {fname}\n")
        return RawFile(path, digest, ft, source)

    @staticmethod
    def read(path: Path) -> bytes:
        return gzip.decompress(path.read_bytes())

    def files(self, source: str | None = None) -> list[Path]:
        base = self.raw / source if source else self.raw
        if not base.exists():
            return []
        return sorted(p for p in base.rglob("*.gz") if p.is_file())

    def verify(self) -> list[str]:
        """DAT-09: every file is in its manifest with an unchanged hash. Returns problems."""
        problems: list[str] = []
        if not self.raw.exists():
            return problems
        for d in sorted({p.parent for p in self.raw.rglob("*") if p.is_file()}):
            listed: dict[str, str] = {}
            mf = d / MANIFEST
            if mf.exists():
                for line in mf.read_text(encoding="ascii").splitlines():
                    digest, _, fname = line.partition("  ")
                    listed[fname] = digest
            for p in sorted(d.glob("*.gz")):
                want = listed.pop(p.name, None)
                if want is None:
                    problems.append(f"{p}: not in {MANIFEST}")
                elif sha256_file(p) != want:
                    problems.append(f"{p}: sha256 changed")
            problems.extend(f"{d / f}: listed in {MANIFEST} but missing" for f in listed)
        return problems

    def manifest_hashes(self, paths: Iterable[Path]) -> dict[str, str]:
        """Hashes for the audit record (``runs.data_hashes``, DAT-09)."""
        return {"/".join(p.parts[-3:]): sha256_file(p) for p in paths}


# ---------------------------------------------------------------------------
# DAT-16 rental tree
# ---------------------------------------------------------------------------


class RentalStore:
    """Rented data with a deletion date; only derived results outlive it (DAT-16)."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve() / "rental"

    def put(self, name: str, payload: bytes, deletion_date: date) -> Path:
        if not _NAME_RE.fullmatch(name):
            raise RawStoreError(f"unsafe rental file name {name!r}")
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / name
        if path.exists():
            raise RawStoreError(f"rental file exists: {path}")
        path.write_bytes(payload)
        meta = {"deletion_date": deletion_date.isoformat()}
        (self.root / f"{name}.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        return path

    def deletion_date(self, name: str) -> date:
        meta = json.loads((self.root / f"{name}.meta.json").read_text(encoding="utf-8"))
        return date.fromisoformat(meta["deletion_date"])

    def undated(self) -> list[Path]:
        """Rental files without a deletion date (each is a DAT-16 violation)."""
        if not self.root.exists():
            return []
        return sorted(
            p
            for p in self.root.iterdir()
            if p.is_file()
            and not p.name.endswith(".meta.json")
            and not (self.root / f"{p.name}.meta.json").exists()
        )

    def purge(self, today: date) -> list[Path]:
        """Delete every rental file whose deletion date is on or before ``today``."""
        removed: list[Path] = []
        if not self.root.exists():
            return removed
        for meta in sorted(self.root.glob("*.meta.json")):
            name = meta.name.removesuffix(".meta.json")
            if self.deletion_date(name) <= today:
                (self.root / name).unlink(missing_ok=True)
                meta.unlink()
                removed.append(self.root / name)
        return removed


# ---------------------------------------------------------------------------
# Bitemporal reads (DAT-18)
# ---------------------------------------------------------------------------


def latest_bar(
    session: Session,
    instrument_id: int,
    trade_date: date,
    source: str,
    as_of: datetime | None = None,
) -> RawBar | None:
    """The bar for (instrument, date, source) as known at ``as_of`` (latest fetch)."""
    q = select(RawBar).where(
        RawBar.instrument_id == instrument_id,
        RawBar.trade_date == trade_date,
        RawBar.source == source,
    )
    if as_of is not None:
        q = q.where(RawBar.fetch_time <= ensure_utc(as_of))
    return session.execute(q.order_by(RawBar.fetch_time.desc()).limit(1)).scalar_one_or_none()


def latest_bars(
    session: Session,
    instrument_id: int,
    source: str,
    start: date | None = None,
    end: date | None = None,
    as_of: datetime | None = None,
) -> dict[date, RawBar]:
    """Latest-known bar per trade date in [start, end] (read from the local store)."""
    q: Select[Any] = select(RawBar).where(
        RawBar.instrument_id == instrument_id, RawBar.source == source
    )
    if start is not None:
        q = q.where(RawBar.trade_date >= start)
    if end is not None:
        q = q.where(RawBar.trade_date <= end)
    if as_of is not None:
        q = q.where(RawBar.fetch_time <= ensure_utc(as_of))
    out: dict[date, RawBar] = {}
    for bar in session.execute(q.order_by(RawBar.trade_date, RawBar.fetch_time)).scalars():
        out[bar.trade_date] = bar  # later fetch overwrites earlier
    return out


def last_stored_bar_date(session: Session, instrument_id: int, source: str) -> date | None:
    return session.execute(
        select(func.max(RawBar.trade_date)).where(
            RawBar.instrument_id == instrument_id, RawBar.source == source
        )
    ).scalar_one_or_none()


def validated_closes(
    session: Session,
    instrument_id: int,
    *,
    start: date | None = None,
    end: date | None = None,
    as_of: datetime | None = None,
    signals_only: bool = False,
) -> dict[date, Any]:
    """The validated set: the latest verdict row per trade date (DAT-17, DAT-21).

    ``signals_only`` drops dates whose latest validated close may not feed a signal
    (a Flex-only close under DAT-02 case (c)).
    """
    from trader.data.models import ValidatedClose

    q: Select[Any] = select(ValidatedClose).where(ValidatedClose.instrument_id == instrument_id)
    if start is not None:
        q = q.where(ValidatedClose.trade_date >= start)
    if end is not None:
        q = q.where(ValidatedClose.trade_date <= end)
    if as_of is not None:
        q = q.where(ValidatedClose.validated_at <= ensure_utc(as_of))
    out: dict[date, Any] = {}
    for row in session.execute(
        q.order_by(ValidatedClose.trade_date, ValidatedClose.validated_at)
    ).scalars():
        out[row.trade_date] = row
    if signals_only:
        out = {d: r for d, r in out.items() if r.signals_ok}
    return out
