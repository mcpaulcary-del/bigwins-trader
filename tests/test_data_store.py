"""Raw store, manifest and rental tree (DAT-09, DAT-16, DAT-18)."""

from __future__ import annotations

import gzip
import os
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from tests.m1_support import add_bar, setup_market, syd
from trader.data.instruments import require_instrument
from trader.data.store import (
    MANIFEST,
    RawStore,
    RawStoreError,
    RentalStore,
    latest_bar,
    latest_bars,
)

NOW = datetime(2026, 11, 12, 8, 30, 15, 123456, tzinfo=UTC)


class TestDAT18RawLayout:
    """DAT-18: raw responses stored as data/raw/{source}/{fetch_date}/...json.gz with a
    sha256 manifest; market rows carry trade date and fetch time; nothing updated."""

    def test_DAT_18_path_layout_and_unchanged_bytes(self, tmp_path: Path) -> None:
        store = RawStore(tmp_path / "data", "a")
        rf = store.put("eodhd", "eod_VAS_20261102_20261112", b'[{"close": 1}]', NOW)
        rel = rf.path.relative_to(tmp_path / "data")
        assert rel.parts[:3] == ("raw", "eodhd", "2026-11-12")
        assert rel.name == "eod_VAS_20261102_20261112.083015123456Z.json.gz"
        assert gzip.decompress(rf.path.read_bytes()) == b'[{"close": 1}]'
        assert RawStore.read(rf.path) == b'[{"close": 1}]'

    def test_DAT_18_never_overwritten_and_read_only(self, tmp_path: Path) -> None:
        store = RawStore(tmp_path, "a")
        rf = store.put("rba", "f11.1", b"x", NOW, ext="csv")
        with pytest.raises(RawStoreError, match="never overwritten"):
            store.put("rba", "f11.1", b"y", NOW, ext="csv")
        assert oct(rf.path.stat().st_mode & 0o777) == "0o440"
        with pytest.raises(RawStoreError):
            store.put("rba", "../escape", b"y", NOW)

    def test_DAT_18_bitemporal_reads(self, market_engine: Engine) -> None:
        with Session(market_engine) as s:
            setup_market(s)
            vas = require_instrument(s, "VAS").id
            d = date(2026, 11, 3)
            add_bar(s, vas, d, "100.00", fetch_time=syd(d, 19, 31))
            add_bar(s, vas, d, "100.05", fetch_time=syd(date(2026, 11, 8), 3))  # restated later
            assert latest_bar(s, vas, d, "eodhd").close == Decimal("100.05")  # type: ignore[union-attr]
            known_then = latest_bar(s, vas, d, "eodhd", as_of=syd(date(2026, 11, 5), 8))
            assert known_then is not None and known_then.close == Decimal("100.00")
            assert latest_bars(s, vas, "eodhd")[d].close == Decimal("100.05")


class TestDAT09Integrity:
    """DAT-09: every raw file hashed (sha256 manifest); hashes in the audit record."""

    def test_DAT_09_manifest_and_verify(self, tmp_path: Path) -> None:
        store = RawStore(tmp_path, "a")
        a = store.put("eodhd", "a", b"one", NOW)
        b = store.put("eodhd", "b", b"two", NOW)
        assert store.verify() == []
        lines = (a.path.parent / MANIFEST).read_text().splitlines()
        assert [ln.split("  ")[1] for ln in lines] == [a.path.name, b.path.name]
        hashes = store.manifest_hashes([a.path, b.path])
        assert hashes[f"eodhd/2026-11-12/{a.path.name}"] == a.sha256

    def test_DAT_09_tampered_or_unlisted_file_is_reported(self, tmp_path: Path) -> None:
        store = RawStore(tmp_path, "a")
        a = store.put("eodhd", "a", b"one", NOW)
        os.chmod(a.path, 0o640)
        a.path.write_bytes(gzip.compress(b"changed", mtime=0))
        (a.path.parent / "stray.json.gz").write_bytes(b"x")
        problems = store.verify()
        assert any("sha256 changed" in p for p in problems)
        assert any("not in MANIFEST" in p for p in problems)

    def test_DAT_09_same_bytes_same_hash(self, tmp_path: Path) -> None:
        store = RawStore(tmp_path, "a")
        x = store.put("eodhd", "x", b"payload", NOW)
        y = store.put("eodhd", "y", b"payload", NOW)
        assert x.sha256 == y.sha256  # gzip header carries no timestamp


class TestDAT16Rental:
    """DAT-16: rented data lives in a separate rental/ tree with a deletion date; only
    derived results are kept after expiry."""

    def test_DAT_16_purge_on_deletion_date(self, tmp_path: Path) -> None:
        r = RentalStore(tmp_path)
        r.put("norgate_xjo.csv", b"rented", date(2027, 5, 1))
        r.put("norgate_xao.csv", b"rented", date(2027, 8, 1))
        assert r.purge(date(2027, 4, 30)) == []
        removed = r.purge(date(2027, 5, 1))
        assert [p.name for p in removed] == ["norgate_xjo.csv"]
        assert not (r.root / "norgate_xjo.csv").exists()
        assert (r.root / "norgate_xao.csv").exists()

    def test_DAT_16_every_rental_file_has_a_deletion_date(self, tmp_path: Path) -> None:
        r = RentalStore(tmp_path)
        r.put("a.csv", b"x", date(2027, 1, 1))
        (r.root / "sneaked_in.csv").write_bytes(b"x")
        assert [p.name for p in r.undated()] == ["sneaked_in.csv"]

    def test_DAT_16_raw_store_is_never_inside_the_rental_tree(self, tmp_path: Path) -> None:
        with pytest.raises(RawStoreError, match="rental"):
            RawStore(tmp_path / "rental", "a")
