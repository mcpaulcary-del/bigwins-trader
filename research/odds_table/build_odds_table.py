# ruff: noqa: E501  (the CSV header lines are written as they appear)
"""Build ``config/odds_table_v1.csv`` (BF-D88): the historical odds card of the share pages.

OFFLINE RESEARCH TOOL. It never runs in production: the trader and the app only read the
small aggregated CSV it writes. It needs the private research environment (the long
survivorship-free ASX panel of report 100 and the frozen research engines ``acct3`` and
``eng88``), which are not in this repository. The panel's EODHD rows never leave that
environment; only aggregated percentages and counts are written.

Two steps::

    # 1. per stock-month rows (big; write them to /dev/shm, delete afterwards)
    python research/odds_table/build_odds_table.py extract \
        --panel /dev/shm/odds/asxlong --kit $B/blind3_clean/kit --kit $B/blind2_build \
        --rows /dev/shm/odds/rows.csv.gz
    # 2. the small table
    python research/odds_table/build_odds_table.py aggregate \
        --rows /dev/shm/odds/rows.csv.gz --out config/odds_table_v1.csv

Definitions (as in research_big Study A, REPORT.md section 1):

* unit: a stock-month; formations are the month-ends from Jan 2005 to Oct 2025;
* universe: ordinary shares (the panel's exclusion flag) with a close on the entry
  session (the session after the month-end) and a 20-session median traded value of at
  least A$10,000 (TRADE), that are eligible for a score (the strategy's eligibility:
  63-session median traded value >= A$100,000, close >= A$0.10, traded in the last five
  sessions, s1/s2/s3 defined);
* size band: rank by 252-session median traded value (1 = largest): 1-100, 101-300,
  301-600 (band C), 601-1000;
* score: M3 = mean of the within-band percentiles of s1 (12-1 month momentum), s2
  (6-month) and s3 (nearness to the 52-week high); its percentile within the band's
  eligible names that month; quintile 5 = top fifth (> 80%), as the app's score
  percentile and the strategy's top fifth;
* outcome: the total return over the next 252 sessions from the entry close, with the
  backtests' payout rule for shares that stop trading (takeover: last close; failure:
  zero; unknown: last close if within 30% of its 250-session high, else zero).
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

BANDS = ((1, 100), (101, 300), (301, 600), (601, 1000))
FIRST, LAST = "2005-01-01", "2025-10-31"
SPLIT = "2016-01-01"  # halves: 2005-2015 and 2016-2025
MIN_CELL = 300  # a third split is used only if every cell keeps this many stock-months
METHOD = "odds1"
HORIZON = 252
TRADE_MIN = 10_000.0


def _band(rk: float) -> int | None:
    for k, (lo, hi) in enumerate(BANDS):
        if lo - 1 < rk <= hi:
            return k
    return None


def extract(panel: str, kits: list[str], out: str) -> None:
    for k in kits:
        sys.path.insert(0, k)
    import acct3  # type: ignore[import-not-found]
    import eng88  # type: ignore[import-not-found]

    eng = acct3.Engine(panel)
    e8 = eng88.Eng(panel)
    n, ncol = eng.n, len(eng.cols)
    # payout multiplier of a share that stopped trading (research_big common.load)
    term = np.ones(ncol)
    for j in range(ncol):
        l0 = int(eng.end_last[j])
        if l0 < 0:
            continue
        dc = eng.dcl.get(eng.cols[j], "unk")
        hh = np.nanmax(eng.CR[max(0, l0 - 250) : l0 + 1, j])
        term[j] = {"takeover": 1.0, "fail": 0.0}.get(
            dc, 1.0 if eng.clff[l0, j] >= 0.7 * hh else 0.0
        )

    def mult(t: int, cols: np.ndarray) -> np.ndarray:
        dead = (eng.lastv[t, cols] < t - 20) & (eng.end_last[cols] == eng.lastv[t, cols])
        return np.where(dead, term[cols], 1.0)

    rows = []
    for i in eng.ME:
        dt = eng.idx[i]
        a = i + 1
        if not (pd.Timestamp(FIRST) <= dt <= pd.Timestamp(LAST)) or a + HORIZON > n - 1:
            continue
        rk = eng.rank(i)
        b = e8.base(i)
        pct = np.full(ncol, np.nan)
        s3p = np.full(ncol, np.nan)
        for lo, hi in BANDS:
            c = np.flatnonzero(b["el"] & (rk > lo - 1) & (rk <= hi))
            if not len(c):
                continue
            parts = [pd.Series(b[p][c]).rank(pct=True).to_numpy() for p in ("s1", "s2", "s3")]
            pct[c] = pd.Series(np.mean(parts, axis=0)).rank(pct=True).to_numpy()
            s3p[c] = parts[2]
        cols = np.flatnonzero(
            eng.ok & ~np.isnan(eng.CR[a]) & (np.nan_to_num(eng.m20[i]) >= TRADE_MIN)
            & b["el"] & ~np.isnan(pct)
        )  # fmt: skip
        f12 = np.exp(eng.L[a + HORIZON, cols] - eng.L[a, cols]) * mult(a + HORIZON, cols) - 1
        rows.append(pd.DataFrame({
            "date": dt.date().isoformat(), "eid": np.asarray(eng.cols)[cols], "rk": rk[cols],
            "pct": pct[cols], "s3p": s3p[cols], "lot": b["lot"][cols].astype(int), "f12": f12,
        }))  # fmt: skip
    df = pd.concat(rows, ignore_index=True)
    df.to_csv(out, index=False, compression="gzip")
    print(f"{len(df)} stock-months, {df.date.nunique()} months -> {out}")


def quintile(pct: float) -> int:
    """1..5 from a percentile in (0, 1]; 5 = top fifth (> 0.80)."""
    return min(5, max(1, math.ceil(round(pct * 5, 9))))


def _stats(g: pd.DataFrame) -> dict[str, Any]:
    f = g.f12
    return {
        "n": len(g), "companies": g.eid.nunique(),
        "p_up40": round(100 * float((f >= 0.4).mean()), 1),
        "p_double": round(100 * float((f >= 1.0).mean()), 1),
        "p_halve": round(100 * float((f <= -0.5).mean()), 1),
        "median": round(100 * float(f.median()), 1),
    }  # fmt: skip


def cells(df: pd.DataFrame, split: str | None) -> pd.DataFrame:
    keys = ["band", "q"] + ([split] if split else [])
    out = []
    for key, g in df.groupby(keys, sort=True):
        kt = key if isinstance(key, tuple) else (key,)
        row: dict[str, Any] = {"band": BANDS[int(kt[0])], "quintile": int(kt[1]),
                               "split": "" if not split else ("yes" if kt[2] else "no")}  # fmt: skip
        row.update(_stats(g))
        for h, sub in (("h1", g[g.date < SPLIT]), ("h2", g[g.date >= SPLIT])):
            row.update({f"{h}_{k}": v for k, v in _stats(sub).items() if k != "companies"})
        out.append(row)
    return pd.DataFrame(out)


def aggregate(rows: str, out: str, built: str) -> None:
    df = pd.read_csv(rows, compression="gzip")
    df["band"] = [_band(x) for x in df.rk]
    df = df[df.band.notna()].copy()
    df["q"] = [quintile(x) for x in df.pct]
    df["near_high"] = df.s3p > 2 / 3  # top third of the band by nearness to the 52-week high
    # the optional third split: only if every cell keeps MIN_CELL stock-months
    split = None
    for cand in ("near_high",):
        if int(cells(df, cand).n.min()) >= MIN_CELL:
            split = cand
    tab = cells(df, split)
    first, last = df.date.min(), df.date.max()
    head = [
        f"# odds_table_v1 (method {METHOD}, BF-D88): historical 12-month odds by size band and score quintile.",
        f"# Built {built} by research/odds_table/build_odds_table.py from the long survivorship-free ASX research panel",
        "# (report 100, deep100/build100.py; daily total returns, dead companies included). Aggregated percentages and",
        "# counts only: no prices, no per-company rows. Descriptive history; not a trial, changes no strategy.",
        f"# Unit: stock-month, formations {first[:7]} to {last[:7]}, TRADE universe (20-session median traded value",
        "# >= A$10,000) and score-eligible; outcome over the next 252 sessions with the payout rule for dead shares.",
        "# band = rank by 252-session median traded value; quintile 5 = M3 score percentile within the band > 80%.",
        f"# split = {split or 'none'} (third split used only if every cell has >= {MIN_CELL} stock-months).",
        "# Percent columns: p_up40 = P(>= +40%), p_double = P(>= +100%), p_halve = P(<= -50%), median = median return.",
        "# h1 = formations 2005-2015, h2 = 2016-2025.",
    ]
    cols = ["band_lo", "band_hi", "quintile", *(["split"] if split else []), "n", "companies", "p_up40", "p_double",
            "p_halve", "median", "h1_n", "h1_p_up40", "h1_p_double", "h1_p_halve", "h1_median",
            "h2_n", "h2_p_up40", "h2_p_double", "h2_p_halve", "h2_median"]  # fmt: skip
    tab["band_lo"] = [b[0] for b in tab.band]
    tab["band_hi"] = [b[1] for b in tab.band]
    body = tab[cols].to_csv(index=False, lineterminator="\n")
    Path(out).write_text("\n".join(head) + "\n" + body, encoding="utf-8")
    print(f"split={split}; {len(tab)} cells; min n {int(tab.n.min())} -> {out}")
    print(tab[cols].to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("extract")
    x.add_argument("--panel", required=True)
    x.add_argument("--kit", action="append", required=True)
    x.add_argument("--rows", required=True)
    g = sub.add_parser("aggregate")
    g.add_argument("--rows", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--built", default=date.today().isoformat())  # noqa: DTZ011 - a label
    a = ap.parse_args()
    if a.cmd == "extract":
        extract(a.panel, a.kit, a.rows)
    else:
        aggregate(a.rows, a.out, a.built)


if __name__ == "__main__":
    main()
