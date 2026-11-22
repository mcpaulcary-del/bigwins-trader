"""BF-D72 (strategy review M2): the live-parameter golden on 13 recorded month-ends (band C,
scores, the top fifth, bid-peg in band C, the band-trend level / mean) against the
research record's paper tables. Needs the record's store (``TRADER_FORWARD_STORE``); the
same check runs on the server before every trader restart (``trader-bf golden-check``)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STORE = os.environ.get("TRADER_FORWARD_STORE")
GOLDEN = ROOT / "config" / "golden" / "emg2_live_golden.json"


def test_M2_golden_file_covers_twelve_month_ends() -> None:
    import json

    g = json.loads(GOLDEN.read_text())
    assert len(g) >= 12
    for d, r in g.items():
        assert r["band_c"] and set(r["targets"]) <= set(r["band_c"]), d
        assert r["bt_state"] in ("EMG2", "FUND") and 0.5 < r["bt_ratio"] < 1.5


@pytest.mark.skipif(not STORE, reason="TRADER_FORWARD_STORE (the record's store) not mounted")
def test_M2_live_code_matches_the_record_on_twelve_month_ends() -> None:
    from tests.bf_support import asx_sessions, real_config
    from trader.golden import run

    bad = run(real_config(), Path(str(STORE)), GOLDEN, asx_sessions())
    assert bad == [], "\n".join(bad)


def test_M2_cli_skips_without_the_record(tmp_path: Path) -> None:
    from trader.bfast_cli import main

    assert main(["golden-check", "--store", str(tmp_path), "--golden", str(GOLDEN)]) == 0
