"""B-fast data layer: identity rules and the read-only forward-store adapter (FD §5.1, §21.1)."""

from __future__ import annotations

import gzip
import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from tests.bf_support import sessions
from trader.data.forward_store import (
    ForwardStore,
    adjusted_to_last,
    reconcile_splits,
    symbol_returns,
)
from trader.data.identity import (
    cut_code_reuse,
    duplicates_a7b,
    duplicates_a7c,
    security_class,
)


@pytest.mark.parametrize(
    ("code", "vtype", "name", "want"),
    [
        ("BHP", "Common Stock", "BHP Group", "ORD"),
        ("ABC_old", "Common Stock", "Old Co", "ORD"),
        # BF-D20: LIC only by the frozen list (here AFI), never by words in the name
        ("AFI", "Common Stock", "Australian Foundation Investment Co", "LIC"),
        ("AFI_old", "Common Stock", "Australian Foundation Investment Co", "LIC"),
        ("PNI", "Common Stock", "Pinnacle Investment Management Group", "ORD"),
        ("RG1", "Common Stock", "Regal Partners Global Investments Ltd", "ORD"),
        ("ZZZ", "Common Stock", "Some LIC Capital Fund Investments", "ORD"),
        ("PUB", "Common Stock", "Republic Mining", "ORD"),
        ("SCG", "Common Stock", "Scentre Property Group", "REIT"),
        ("VAS", "ETF", "Vanguard", "FUND"),
        ("XYZ", "Common Stock", "listed as ETP", "FUND"),
        ("ABCDE", "Common Stock", "Five letter", "OTHER"),
        ("ABCPA", "Preferred Stock", "Notes", "OTHER"),
    ],
)
def test_BW_UNI_03_security_class(code: str, vtype: str, name: str, want: str) -> None:
    got = security_class(
        code, vtype, name, etp_codes=frozenset({"XYZ"}), lic_codes=frozenset({"AFI"})
    )
    assert got == want


def test_BW_UNI_01_code_reuse_after_200_day_gap() -> None:
    d = (date(2020, 1, 1), date(2020, 1, 2), date(2021, 1, 4), date(2021, 1, 5))
    c = np.array([[1.0, 1.0], [1.1, np.nan], [5.0, 2.0], [5.1, 2.1]])
    out = cut_code_reuse(d, c)
    assert np.isnan(out[:2, 0]).all() and out[2, 0] == 5.0  # earlier company dropped
    assert np.isnan(out[0, 1]) and out[2, 1] == 2.0  # 369-day gap -> re-use
    assert np.isnan(cut_code_reuse((*d[:2], date(2020, 3, 1), date(2020, 3, 2)), c)).sum() == 1


def _dup_matrix(n: int = 300, seed: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.02, (n, 4))
    r[:, 1] = r[:, 0]  # column 1 carries column 0's company at another price scale
    close = 5 * np.exp(np.cumsum(r, axis=0))
    close[:, 1] *= 0.1
    close[200:, 0] = np.nan  # the old code stops; the new one lives on
    vol = np.ones_like(close)
    ret = np.full_like(close, np.nan)
    ret[1:] = close[1:] / close[:-1] - 1
    return close, vol, ret


def test_BW_UNI_02_a7c_daily_return_duplicates() -> None:
    close, vol, ret = _dup_matrix()
    pairs = duplicates_a7c(close, vol, ret)
    assert [(p.dup, p.keep, p.rule) for p in pairs] == [(0, 1, "A7c")]
    assert pairs[0].score > 0.999
    assert duplicates_a7c(close, vol, ret, exclude=frozenset({0})) == []


def test_BW_UNI_02_a7b_same_closes() -> None:
    close, _, _ = _dup_matrix()
    close[:, 2] = close[:, 0]
    close[150:, 2] = np.nan  # code 2 is the same quote as code 0 and ends earlier
    pairs = duplicates_a7b(close)
    assert (2, 0) in {(p.dup, p.keep) for p in pairs}


def test_A3_split_reconciliation_nearest_row() -> None:
    close = [10.0, 10.1, 10.2, 5.1, 5.2, 5.3]
    # vendor lists a 2:1 split two rows late: the jump is on row 3
    assert reconcile_splits(close, [1, 1, 1, 1, 1, 2.0]) == [1, 1, 1, 2.0, 1, 1]
    # no jump anywhere: the series was already adjusted, the split is not applied
    assert reconcile_splits([5.0] * 6, [1, 1, 2.0, 1, 1, 1]) == [1.0] * 6
    assert adjusted_to_last([10.0, 5.0], [1.0, 2.0]) == [5.0, 5.0]


def test_A3_total_return_with_dividend_and_split() -> None:
    rows = [
        {"date": f"2026-01-0{k}", "close": c, "volume": 100}
        for k, c in [(5, 10.0), (6, 10.0), (7, 5.0), (8, 4.9)]
    ]
    days, _, _, split, ret = symbol_returns(
        rows, [(date(2026, 1, 7), 2.0)], [(date(2026, 1, 8), 0.1)]
    )
    assert split[2] == 2.0
    assert ret[2] == pytest.approx(0.0) and ret[3] == pytest.approx((4.9 + 0.1) / 5.0 - 1)
    assert days[0] == date(2026, 1, 5)


def _gz(p: Path, obj: object) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump(obj, f)


def test_forward_store_builds_panel_read_only(tmp_path: Path) -> None:
    sess = sessions(30, date(2026, 10, 1))
    man = ["utc\tkind\tsymbol\thttp\tcost\tbytes\tpayload_sha256\tfile\tfile_sha256\turl"]
    syms = ["Code,Name,Country,Exchange,Currency,Type,Isin,delisted,api_symbol,in_both_lists"]
    for k, (code, name) in enumerate([("AAA", "Alpha Ltd"), ("BBB", "Beta Investments")]):
        rows = [
            {"date": str(d), "close": 1.0 + 0.01 * i + k, "volume": 1000}
            for i, d in enumerate(sess[:-2])
        ]
        f = f"raw/eod/{code}.AU__1.json.gz"
        _gz(tmp_path / f, rows)
        man.append(f"t\teod\t{code}.AU\t200\t1\t1\tx\t{f}\tx\tu")
        syms.append(f"{code},{name},Australia,AU,AUD,Common Stock,,0,{code}.AU,False")
    for d in sess[-2:]:  # two later days arrive as bulk files
        _gz(
            tmp_path / f"raw/bulk_eod/AU_{d}__1.json.gz",
            [{"code": "AAA", "date": str(d), "close": 2.0, "volume": 10}],
        )
    (tmp_path / "manifest.tsv").write_text("\n".join(man) + "\n")
    (tmp_path / "symbols.csv").write_text("\n".join(syms) + "\n")
    before = sorted((p, p.stat().st_mtime_ns) for p in tmp_path.rglob("*"))
    fs = ForwardStore(tmp_path)
    p = fs.build_panel(sess[-1], sess, history=20)
    assert p.sec_class == {"AAA": "ORD", "BBB": "ORD"}  # BF-D20: no name-word rule
    p = fs.build_panel(sess[-1], sess, history=20, lic_codes=frozenset({"BBB"}))
    assert p.as_of == sess[-1] and p.close.shape == (20, 2)
    assert p.sec_class == {"AAA": "ORD", "BBB": "LIC"}
    assert p.close[-1, 0] == 2.0 and np.isnan(p.close[-1, 1])
    assert p.tv[-1, 0] == 20.0
    q = fs.build_panel(sess[-3], sess, history=20)  # an earlier D sees no later row
    assert q.dates[-1] == sess[-3] and q.close[-1, 0] == pytest.approx(1.27)
    assert sorted((p, p.stat().st_mtime_ns) for p in tmp_path.rglob("*")) == before
    with pytest.raises(ValueError):
        fs.build_panel(date(2026, 10, 3), sess)  # a Saturday
