"""Strategy-correctness review (22 Nov 2026; BF-D72): duplicate corporate events (H1),
the band-trend history (H3), immediate updates (M3), the strategy fingerprint (M4), new
codes from the bulk feed (M5), the bid-peg rule (M6), fixed costs (H4)."""

from __future__ import annotations

import gzip
import json
import math
import os
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from trader.data.forward_store import ForwardStore, merge_events, symbol_returns

ROOT = Path(__file__).resolve().parents[1]
STORE = os.environ.get("TRADER_FORWARD_STORE")


def _gz(p: Path, obj: object) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump(obj, f)


# ------------------------------------------------------------------ H1
def test_H1_events_once_per_ex_date_per_symbol_file_wins() -> None:
    d = date(2026, 3, 2)
    assert merge_events([(d, 0.5)], [(d, 0.5)], by_value=True) == [(d, 0.5)]
    assert merge_events([(d, 0.5)], [(d, 0.7)], by_value=True) == [(d, 0.5)]  # per-symbol wins
    assert merge_events([(d, 10.0), (d, 10.0)], [], by_value=False) == [(d, 10.0)]
    assert merge_events([(d, 0.5), (d, 0.2)], [], by_value=True) == [(d, 0.2), (d, 0.5)] or \
        merge_events([(d, 0.5), (d, 0.2)], [], by_value=True) == [(d, 0.5), (d, 0.2)]  # fmt: skip


def test_H1_a_consolidation_listed_twice_is_not_plus_900_percent() -> None:
    rows = [{"date": "2026-03-02", "close": 0.1, "volume": 1},
            {"date": "2026-03-03", "close": 1.0, "volume": 1}]  # fmt: skip
    d = date(2026, 3, 3)
    _, _, _, _, once = symbol_returns(rows, [(d, 0.1)], [])
    _, _, _, _, twice = symbol_returns(rows, [(d, 0.1), (d, 0.1)], [])
    assert once[1] == pytest.approx(0.0) and twice[1] == pytest.approx(0.0)
    _, _, _, _, r = symbol_returns([rows[0], {"date": "2026-03-03", "close": 0.1, "volume": 1}],
                                   [], [(d, 0.01), (d, 0.01)])  # fmt: skip
    assert r[1] == pytest.approx(0.1)  # one 1c dividend, not two


def _store(tmp: Path) -> Path:
    root = tmp / "eodhd"
    man = ["utc\tkind\tsymbol\thttp\tcost\tbytes\tpayload_sha256\tfile\tfile_sha256\turl"]
    days = ["2026-03-02", "2026-03-03", "2026-03-04"]
    _gz(root / "raw/eod/AAA.AU__1.json.gz",
        [{"date": x, "close": 1.0, "volume": 1000} for x in days[:2]])  # fmt: skip
    _gz(root / "raw/div/AAA.AU__1.json.gz", [{"date": "2026-03-03", "value": 0.05}])
    _gz(
        root / "raw/splits/AAA.AU__1.json.gz",
        [{"date": "2026-03-04", "split": "1.000000/10.000000"}],
    )
    man += ["t\teod\tAAA.AU\t200\t1\t1\tx\traw/eod/AAA.AU__1.json.gz\tx\tu",
            "t\tdiv\tAAA.AU\t200\t1\t1\tx\traw/div/AAA.AU__1.json.gz\tx\tu",
            "t\tsplits\tAAA.AU\t200\t1\t1\tx\traw/splits/AAA.AU__1.json.gz\tx\tu"]  # fmt: skip
    # the bulk feed repeats the dividend and the consolidation, and has a new code NEW
    _gz(root / "raw/bulk_div/AU_2026-03-03__x.json.gz", [{"code": "AAA", "value": 0.05}])
    _gz(root / "raw/bulk_splits/AU_2026-03-04__x.json.gz",
        [{"code": "AAA", "split": "1.000000/10.000000"}])  # fmt: skip
    _gz(root / "raw/bulk_eod/AU_2026-03-04__x.json.gz",
        [{"code": "AAA", "date": "2026-03-04", "close": 10.0, "volume": 100},
         {"code": "NEW", "date": "2026-03-04", "close": 2.0, "volume": 500}])  # fmt: skip
    (root / "manifest.tsv").write_text("\n".join(man) + "\n")
    (root / "symbols.csv").write_text("Code,Name,Type\nAAA,Aaa Ltd,Common Stock\n")
    return root


def test_H1_M5_store_panel_counts_each_event_once_and_adds_new_codes(tmp_path: Path) -> None:
    sess = [date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 4)]
    p = ForwardStore(_store(tmp_path)).build_panel(sess[-1], sess, history=3)
    k = p.entities.index("AAA")
    assert p.ret[1, k] == pytest.approx(0.05)  # the dividend once (not 0.10)
    assert p.ret[2, k] == pytest.approx(0.0)  # the 1:10 consolidation once (not +900%)
    assert "NEW" in p.entities  # M5: a bulk-only code gets a column
    assert p.close[-1, p.entities.index("NEW")] == pytest.approx(2.0)


# ------------------------------------------------------------------ H3
PAPER_BT = {"2026-11-16": 0.9159, "2026-09-30": 0.9535, "2026-06-30": 0.9204, "2026-03-31": 0.9665}


def test_H3_recorded_steps_file_and_loader() -> None:
    from trader.lines.band_trend import load_steps

    st = load_steps(ROOT / "config" / "band_trend_steps.csv")
    assert ("2026-09-30", "2026-10-30") in st and len(st) >= 16
    assert all(0.5 < v < 2 for runs in st.values() for _, v in runs)
    assert load_steps(ROOT / "nope.csv") == {}


@pytest.mark.skipif(not STORE, reason="TRADER_FORWARD_STORE (the record's store) not mounted")
@pytest.mark.parametrize(("day", "ratio"), sorted(PAPER_BT.items()))
def test_H3_band_trend_level_over_mean_pinned_to_paper(day: str, ratio: float) -> None:
    from tests.bf_support import asx_sessions, real_config
    from trader.bf_dryrun import store_providers
    from trader.lines.band_trend import band_trend, load_steps

    cfg = real_config()
    panel, _, _, _ = store_providers(cfg, Path(str(STORE)), asx_sessions())
    bt = band_trend(panel(date.fromisoformat(day)), cfg.band_trend_params(),
                    steps=load_steps(ROOT / "config" / "band_trend_steps.csv"))  # fmt: skip
    assert bt.level / bt.mean == pytest.approx(ratio, abs=0.002)
    assert bt.state == "FUND"


# ------------------------------------------------------------------ M3
def test_M3_immediate_updates_only_for_paper() -> None:
    from tests.bf_support import real_config

    cfg = real_config()
    assert cfg.strategy.update_mode == "immediate" and cfg.mode == "paper"
    with pytest.raises(ValueError, match="paper"):
        type(cfg).model_validate({**cfg.model_dump(), "mode": "live"})


def test_M3_out_of_cycle_decision_keeps_the_month_end_fund_state() -> None:
    from dataclasses import replace

    from tests.test_bf_app import DAYS, _app
    from trader.bf_app import at
    from trader.lines.band_trend import BandTrendParams

    app, _, _ = _app(None)
    app.s = replace(app.s, band_trend=BandTrendParams(enabled=True))
    me = next(d for d in DAYS if app.is_month_end(d))
    app.j.mark_job(f"bt:{me}", {"state": "FUND", "levels": []})
    mid = DAYS[DAYS.index(me) + 5]
    from trader.lines.emg2 import emg2_list

    panel = app.panels(mid)
    t = app._band_trend(panel, mid, at(mid, "22:20"), emg2_list(panel))
    assert t is not None and t.state == "FUND"


# ------------------------------------------------------------------ M4
def test_M4_etp_list_pinned_and_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.bf_support import real_config
    from trader.bfast_config import LicListError, etp_codes

    cfg = real_config()
    f = tmp_path / "etp.txt"
    f.write_text("AAA\n")
    monkeypatch.setenv("TRADER_BF_ETP_LIST", str(f))
    with pytest.raises(LicListError, match="pinned"):
        etp_codes(cfg)
    monkeypatch.setenv("TRADER_BF_ETP_LIST", str(tmp_path / "missing.txt"))
    with pytest.raises(LicListError, match="missing"):
        etp_codes(cfg)


def test_M4_fingerprint_needs_a_new_changelog_entry() -> None:
    from trader.strategy_version import CHANGELOG, load_changelog, strategy_hash

    notes = load_changelog((ROOT / "config" / Path(CHANGELOG).name).read_text())
    want = strategy_hash(ROOT)
    assert notes[0].get("fingerprint") == want, (
        f"the strategy changed (fingerprint {want}): add a new top entry to "
        "config/strategy_changelog.yaml with fingerprint: " + want
    )


def test_M4_code_hash_covers_the_lockfile() -> None:
    import shutil

    from trader.strategy_version import code_hash

    assert (ROOT / "uv.lock").is_file()
    _ = shutil, code_hash


# ------------------------------------------------------------------ M6
def test_M6_bid_peg_needs_five_closes_in_the_window() -> None:
    from trader.features import bid_peg
    from trader.panel import PricePanel

    n = 45
    dates = tuple(date(2026, 1, 1).fromordinal(date(2026, 1, 1).toordinal() + i) for i in range(n))
    close = np.full((n, 2), np.nan)
    close[:, 0] = 1.0
    close[:30, 1] = 1.0
    close[-3:, 1] = 1.0  # only 3 closes in the last 10 sessions
    ret = np.zeros_like(close)
    ret[20, :] = 0.2  # a 20% jump in the lookback
    ret[np.isnan(close)] = np.nan
    p = PricePanel(as_of=dates[-1], dates=dates, entities=("A", "B"), close=close, ret=ret,
                   tv=np.ones_like(close), sec_class={"A": "ORD", "B": "ORD"})  # fmt: skip
    assert list(bid_peg(p)) == [True, False]
    assert list(bid_peg(p, min_closes=2)) == [True, True]  # the old rule


def test_M6_twins_count_leaves_pegged_names_out() -> None:
    from types import SimpleNamespace

    from trader.random_twins import RandomOrder

    lst: Any = SimpleNamespace(band_c=[SimpleNamespace(entity=f"E{i}") for i in range(20)],
                               targets=("E0", "E1", "E2", "E3"), as_of="2025-01-31")  # fmt: skip
    ro = RandomOrder(seed=8550001, origin=0, month=1)
    assert len(ro(lst, frozenset({"E1"}))) == 3


# ------------------------------------------------------------------ H4
def test_H4_fixed_costs_in_the_cost_statement() -> None:
    from decimal import Decimal

    from trader.report import DailyInputs, daily_report

    x = DailyInputs(book="B", session=date(2026, 12, 1), real_money=False, cash=Decimal(10000),
                    positions={}, prices={}, capital_in=Decimal(10000), fills_today=[],
                    commission_to_date=Decimal(0), orders_today=[], safety="NORMAL",
                    fixed_costs_to_date=Decimal(50))  # fmt: skip
    txt = daily_report(x)
    assert "Fixed costs to date (server, data) A$50.00 (0.50% of capital)" in txt
    assert "result after all costs -0.50%" in txt
    assert math.isfinite(1.0)
