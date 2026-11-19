"""Extract the EMG2 golden lists from report 85's T6 back-test (BF1 acceptance test).

Runs OUTSIDE the trading system, once, against the research panel ``W.pkl`` that
``deep85/code/build85.py`` wrote (it needs a pandas able to read that pickle).
For each sampled month-end it repeats T6's own list code (``deep85/code/t6.py``,
the ``PRE`` block, copied verbatim below) and writes:

* ``expected_lists.json``: per month-end, T6's eligible-set size, band-C size,
  the ordered target list ``cand`` (top fifth of band C by score, best first) with
  its scores, and T6's selection inputs per eligible symbol ``E`` (rank,
  ``tv_med252``, ``tv_med63``, ``s1``, ``s2``, ``s3``);
* one ``slab_<date>.npz`` per month-end: the rows ``[i-260, i]`` of T6's ``r``,
  ``close`` and ``tv`` arrays (float32, exactly as T6 read them) for every symbol
  whose traded-value rank was <= 650 that day. Ranks <= 600 depend only on
  symbols ranked above them, so the slab reproduces T6's ranks exactly.

Usage::

    python3 -I scripts/golden/t6_extract.py <W.pkl> <out_dir> [YYYY-MM ...]
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_MONTHS = [
    "2010-06", "2011-12", "2013-03", "2014-09", "2016-02", "2017-08",
    "2019-01", "2020-04", "2021-07", "2022-10", "2024-05", "2026-10",
]  # fmt: skip
KEEP_RANK = 650
BACK = 260


def main(argv: list[str]) -> int:
    w_path, out = Path(argv[1]), Path(argv[2])
    months = argv[3:] or DEFAULT_MONTHS
    out.mkdir(parents=True, exist_ok=True)
    W = pd.read_pickle(w_path)  # noqa: S301 - the research agent's own panel, read once offline
    R = W["r"]
    CL = W["close"]
    TV = W["tv"]
    idx = R.index
    n = len(idx)
    # ---- verbatim from t6.py
    lr = np.log1p(R.fillna(0)).cumsum()
    L = lr.values
    nv = R.notna().cumsum().values
    m252 = TV.rolling(252, min_periods=120).median()
    m63 = TV.rolling(63, min_periods=30).median()
    hi = lr.rolling(252, min_periods=200).max().values
    clf = CL.ffill(limit=5).values
    clv = CL.values
    lastv = pd.DataFrame(np.where(~np.isnan(clv), np.arange(n)[:, None], -1)).cummax().values
    ser = pd.Series(np.arange(n), index=idx)
    ME = ser.groupby([idx.year, idx.month]).last().values
    # ----
    expected = {}
    for i in ME:
        tag = idx[i].strftime("%Y-%m")
        if tag not in months:
            continue
        rk = m252.iloc[i].rank(ascending=False).values
        s1 = np.expm1(L[i - 21] - L[i - 252])
        s1[(nv[i - 21] - nv[i - 252]) < 150] = np.nan
        s2 = np.expm1(L[i] - L[i - 126])
        s2[(nv[i] - nv[i - 126]) < 80] = np.nan
        s3 = np.exp(L[i] - hi[i])
        el = (
            (rk <= 600) & (m63.iloc[i].values >= 100000) & (clf[i] >= 0.10) & (lastv[i] >= i - 4)
            & ~np.isnan(s1) & ~np.isnan(s2) & ~np.isnan(s3)
        )  # fmt: skip
        E = np.where(el)[0]

        def pc(x: np.ndarray, ids: np.ndarray) -> np.ndarray:
            return pd.Series(x[ids]).rank(pct=True).values

        C = E[rk[E] > 300]
        scC = (pc(s1, C) + pc(s2, C) + pc(s3, C)) / 3
        prC = pd.Series(scC).rank(pct=True).values
        cand = C[prC > 0.8][np.argsort(-scC[prC > 0.8])]
        cols = R.columns
        date = idx[i].strftime("%Y-%m-%d")
        expected[date] = {
            "E_size": len(E),
            "C_size": len(C),
            "cand": [str(cols[j]) for j in cand],
            "score": [float(x) for x in scC[prC > 0.8][np.argsort(-scC[prC > 0.8])]],
            # T6's own inputs to the selection step, per eligible symbol (float64 repr)
            "E": {
                str(cols[j]): [
                    float(rk[j]),
                    float(m252.iloc[i, j]),
                    float(m63.iloc[i, j]),
                    float(s1[j]),
                    float(s2[j]),
                    float(s3[j]),
                ]
                for j in E
            },
        }
        keep = np.where(rk <= KEEP_RANK)[0]
        rows = slice(i - BACK, i + 1)
        np.savez_compressed(
            out / f"slab_{date}.npz",
            dates=np.array([d.strftime("%Y-%m-%d") for d in idx[rows]]),
            symbols=np.array([str(c) for c in cols[keep]]),
            r=R.values[rows][:, keep],
            close=CL.values[rows][:, keep],
            tv=TV.values[rows][:, keep],
            first_row_index=np.array([i - BACK]),
        )
        print(date, len(E), len(C), len(cand), flush=True)
    (out / "expected_lists.json").write_text(json.dumps(expected, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
