"""Made-up paper-record trees for the BF-D93 tests. Nothing here is vendor data: codes,
prices and file contents are invented; only the folder layout is the record's."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from record.tools import fence, paths
from record.tools import ledgerlib as L

REPO = Path(__file__).resolve().parents[1]


def make_tree(root: Path, writer: str = "cloud", role: str = "writer", epoch: int = 1,
              entries: int = 3) -> Path:  # fmt: skip
    """A small record tree under ``root`` with a verified ledger and a fence."""
    rec = paths.record_dir(root)
    (rec / "paper").mkdir(parents=True)
    (root / paths.REL_STATE / "decisions").mkdir(parents=True)
    (root / paths.REL_DATA / "bulk").mkdir(parents=True)
    for i in range(entries):
        L.append(rec / "LEDGER.jsonl", {"kind": "trials", "asof": "2026-12-01", "event": f"made-up {i}",
                                        "n_trials": i}, now=1_700_000_000 + i)  # fmt: skip
    fence.save(
        rec, fence.Fence(epoch, writer, role, L.head(rec / "LEDGER.jsonl")), now=1_700_000_100
    )
    return rec


def book_day(root: Path, day: str, nav: float = 10000.0, extra: dict[str, Any] | None = None,
             now: float = 1_700_100_000) -> dict[str, Any]:  # fmt: skip
    """What a daily job leaves behind for one day: a state, outputs and a ``daily`` entry."""
    rec = paths.record_dir(root)
    state = {"last": day, "nav": nav, "books": [{"id": "TEST_BOOK", "cash": 12.5}]}
    sp = root / paths.REL_STATE / "state.json"
    sp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    (root / paths.REL_STATE / "decisions" / f"{day}.json").write_text(
        json.dumps({"day": day, "picks": ["AAA", "BBB"]}), encoding="utf-8")  # fmt: skip
    (rec / "paper" / "SCORECARD.md").write_text(
        f"# made-up scorecard {day}\nNAV {nav:.2f}\n", encoding="utf-8"
    )
    (rec / "paper" / "scorecard_latest.csv").write_text(
        f"asof,book,kind,capital,nav\n{day},TEST_BOOK,TEST,10000.0,{nav}\n", encoding="utf-8")  # fmt: skip
    fields = {"kind": "daily", "asof": day, "event": f"paper day booked {day}",
              "state_sha256": L.sha_file(sp), "trades": 0, **(extra or {})}  # fmt: skip
    return L.append(rec / "LEDGER.jsonl", fields, now=now)


def raw_inputs(root: Path, day: str, close: float = 1.23) -> None:
    d = root / paths.REL_DATA / "bulk" / day
    d.mkdir(parents=True, exist_ok=True)
    with gzip.open(d / "eod.json.gz", "wb") as f:
        f.write(
            json.dumps([{"code": "AAA", "close": close}, {"code": "BBB", "close": 2.5}]).encode()
        )


def archive_day(root: Path, day: str, pdf: bytes = b"%PDF-1.4 made-up") -> Path:
    d = root / paths.REL_DATA / "asx_notices" / day
    (d / "pdf").mkdir(parents=True, exist_ok=True)
    (d / "list.csv").write_text("code,time,headline,price_sensitive,ids_id\nAAA,9:01 am,Made-up notice,1,0001\n",
                                encoding="utf-8")  # fmt: skip
    (d / "pdf" / "AAA_0001.pdf").write_bytes(pdf)
    (d / "pdf" / "AAA_0001.txt").write_text("made-up text\n", encoding="utf-8")
    (d / "ps_state.json").write_text(
        json.dumps({"day": day, "runs": [{"start_utc": "x"}]}), encoding="utf-8"
    )
    (d / "DONE").write_text("ok", encoding="utf-8")
    (d / "DONE_PS").write_text(json.dumps({"utc": "x"}), encoding="utf-8")
    return d
