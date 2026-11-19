"""Synthetic market data and a verbatim port of report 85 T6's list code (B-fast tests)."""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from trader.bfast_config import BfastConfig, load_bfast_config
from trader.panel import PricePanel


def sessions(n: int, start: date = date(2023, 1, 2)) -> tuple[date, ...]:
    out: list[date] = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return tuple(out)


def synthetic_panel(
    n_rows: int = 300, n_ent: int = 800, seed: int = 7, *, classes: dict[str, str] | None = None
) -> PricePanel:
    rng = np.random.default_rng(seed)
    drift = rng.normal(0.0003, 0.001, n_ent)
    vol = rng.uniform(0.01, 0.05, n_ent)
    r = rng.normal(drift, vol, (n_rows, n_ent))
    close = 2.0 * np.exp(np.cumsum(r, axis=0)) * rng.uniform(0.2, 5.0, n_ent)
    liq = np.exp(rng.normal(13.0, 1.6, n_ent))  # median traded value ~ A$440k, wide spread
    tv = liq * np.exp(rng.normal(0, 0.5, (n_rows, n_ent)))
    # some names list late, some have gaps and missing days
    start = rng.integers(0, n_rows, n_ent)
    start[rng.random(n_ent) < 0.85] = 0
    rows = np.arange(n_rows)[:, None]
    miss = (rows < start[None, :]) | (rng.random((n_rows, n_ent)) < 0.03)
    close[miss] = np.nan
    tv[miss] = np.nan
    ret = np.full_like(close, np.nan)
    ret[1:] = close[1:] / close[:-1] - 1  # NaN where either day missing
    ents = tuple(f"S{j:03d}" for j in range(n_ent))
    dts = sessions(n_rows)
    return PricePanel(
        as_of=dts[-1], dates=dts, entities=ents, close=close, ret=ret, tv=tv,
        sec_class=classes or dict.fromkeys(ents, "ORD"),
    )  # fmt: skip


def t6_reference_list(panel: PricePanel) -> list[str]:
    """``deep85/code/t6.py`` PRE block, verbatim apart from reading the panel."""
    R = pd.DataFrame(panel.ret, columns=list(panel.entities))
    CL = pd.DataFrame(panel.close, columns=list(panel.entities))
    TV = pd.DataFrame(panel.tv, columns=list(panel.entities))
    n = len(R)
    lr = np.log1p(R.fillna(0)).cumsum()
    L = lr.values
    nv = R.notna().cumsum().values
    m252 = TV.rolling(252, min_periods=120).median()
    m63 = TV.rolling(63, min_periods=30).median()
    hi = lr.rolling(252, min_periods=200).max().values
    clf = CL.ffill(limit=5).values
    clv = CL.values
    lastv = pd.DataFrame(np.where(~np.isnan(clv), np.arange(n)[:, None], -1)).cummax().values
    i = n - 1
    rk = m252.iloc[i].rank(ascending=False).values
    s1 = np.expm1(L[i - 21] - L[i - 252])
    s1[(nv[i - 21] - nv[i - 252]) < 150] = np.nan
    s2 = np.expm1(L[i] - L[i - 126])
    s2[(nv[i] - nv[i - 126]) < 80] = np.nan
    s3 = np.exp(L[i] - hi[i])
    with np.errstate(invalid="ignore"):
        el = (
            (rk <= 600) & (m63.iloc[i].values >= 100000) & (clf[i] >= 0.10) & (lastv[i] >= i - 4)
            & ~np.isnan(s1) & ~np.isnan(s2) & ~np.isnan(s3)
        )  # fmt: skip
    E = np.where(el)[0]

    def pc(x: np.ndarray, ids: np.ndarray) -> np.ndarray:
        return np.asarray(pd.Series(x[ids]).rank(pct=True).values)

    C = E[rk[E] > 300]
    scC = (pc(s1, C) + pc(s2, C) + pc(s3, C)) / 3
    prC = np.asarray(pd.Series(scC).rank(pct=True).values)
    cand = C[prC > 0.8][np.argsort(-scC[prC > 0.8], kind="stable")]
    return [panel.entities[j] for j in cand]


# ---------------------------------------------------------------- recorded data (opt-in)
# TRADER_FORWARD_STORE: the record's EODHD forward store; TRADER_BF_LIC_LIST: the record
# keeper's frozen LIC list; TRADER_BF_ETP_LIST: the ETP list. Tests skip without the store.


def real_config() -> BfastConfig:
    """``config/bfast.yaml`` with the local paths of the recorded data."""
    cfg = load_bfast_config(Path(__file__).resolve().parent.parent / "config" / "bfast.yaml")
    etp = os.environ.get("TRADER_BF_ETP_LIST")
    if etp:
        cfg = cfg.model_copy(update={"data": cfg.data.model_copy(update={"etp_list": Path(etp)})})
    return cfg


def asx_sessions() -> list[date]:
    import exchange_calendars as xc

    cal = xc.get_calendar("XASX", start="2022-01-01", end="2026-12-31")
    return [x.date() for x in cal.sessions]
