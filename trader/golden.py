"""Live-parameter golden check (BF-D72, strategy review M2): the live EMG2 list (band C,
scores, the top fifth, bid-peg in band C) and the L15 band-trend level / mean on 13
recorded month-ends, against the research record's ``paper_emg2.table`` /
``paper_emg2bt.band_trend`` (live ``Emg2Params``, class rule v2). The golden file
(``config/golden/emg2_live_golden.json``) holds only derived lists and figures.

Run by ``trader-bf golden-check`` (the server's update path: the trader is not
restarted when it fails) and by ``tests/test_bf_review3_golden.py``; both need the
record's price store mounted.

Known difference: the store lacks some names that delisted before it was built, so on
older month-ends band C can differ at the rank boundary; there the check bounds the
difference by the number of paper band-C names missing from the store (3 per name);
where none is missing, band C, T, the scores and bid-peg must match.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

SCORE_TOL = 0.005
RATIO_TOL = 0.002


def build_golden(paper: dict[str, Any]) -> dict[str, Any]:
    """The golden file's content from the paper tables (``p1.py`` output)."""
    out: dict[str, Any] = {}
    for d, r in sorted(paper.items()):
        base = [c.split("#")[0] for c in r["C"]]
        rows = r["rows"]
        out[d] = {
            "band_c": base,
            "score": {c.split("#")[0]: round(float(rows[c]["score"]), 6) for c in r["C"]},
            "targets": [c.split("#")[0] for c in r["C_top"]],
            "peg_in_c": sorted({c.split("#")[0] for c in r["peg"]} & set(base)),
            "bt_ratio": round(float(r["bt"]["level"]) / float(r["bt"]["mean"]), 6),
            "bt_state": "FUND" if r["bt"]["state"] == "OFF" else "EMG2",
        }
    return out


def check(golden: dict[str, Any], panel: Callable[[date], Any], bt_params: Any,
          steps: Any) -> list[str]:  # fmt: skip
    """Problems (empty: the live code matches the record)."""
    from trader.features import bid_peg
    from trader.lines.band_trend import band_trend
    from trader.lines.emg2 import emg2_list

    bad: list[str] = []
    for d, g in sorted(golden.items()):
        p = panel(date.fromisoformat(d))
        lst = emg2_list(p)
        live = [r.entity for r in lst.band_c]
        missing = [c for c in g["band_c"] if c not in p.entities]
        sym = set(live) ^ set(g["band_c"])
        # each missing name is itself a difference and shifts the 300 / 600 rank boundaries
        # by one (up to two more swaps): at most 3 per missing name, + 2 for ties
        if len(sym) > (3 * len(missing) + 2 if missing else 0):
            bad.append(f"{d}: band C differs by {len(sym)} names ({len(missing)} not in the store)")
        if not missing:
            if list(lst.targets) != g["targets"]:
                bad.append(f"{d}: the top fifth (T) differs")
            sc = {r.entity: r.score for r in lst.band_c}
            worst = max((abs(sc[c] - v) for c, v in g["score"].items() if c in sc), default=0.0)
            if worst > SCORE_TOL:
                bad.append(f"{d}: a score differs by {worst:.4f}")
            peg = bid_peg(p)
            lp = sorted(e for j, e in enumerate(p.entities) if peg[j] and e in set(live))
            if lp != g["peg_in_c"]:
                bad.append(f"{d}: bid-peg in band C {lp} v {g['peg_in_c']}")
        bt = band_trend(p, bt_params, steps=steps)
        if abs(bt.level / bt.mean - g["bt_ratio"]) > RATIO_TOL or bt.state != g["bt_state"]:
            bad.append(f"{d}: band-trend {bt.state} {bt.level / bt.mean:.4f} v "
                       f"{g['bt_state']} {g['bt_ratio']:.4f}")  # fmt: skip
    return bad


def run(cfg: Any, store: Path, golden_path: Path, sessions: Sequence[date]) -> list[str]:
    from trader.bf_dryrun import store_providers
    from trader.lines.band_trend import load_steps

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    panel, _, _, _ = store_providers(cfg, store, sessions)
    return check(golden, panel, cfg.band_trend_params(), load_steps(cfg.data.band_trend_steps))
