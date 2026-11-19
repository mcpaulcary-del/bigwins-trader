"""Pure feature functions over a ``PricePanel`` (FD v3.0 §6.3; BW-SYS-10).

Every function reads only the panel (all rows <= D) and returns one value per
entity, evaluated at the panel's last session D. Float maths is allowed here
(SYS-13: floats only inside signal maths).

Exact definitions (EMG2 amendment §2, FD §6.3), with i = the row of D and
L = cumulative sum of log(1 + ret) with invalid returns counted as 0:

* ``s1`` = exp(L[i-21] - L[i-252]) - 1, at least ``s1_min_valid`` (150) valid
  returns in rows i-251 .. i-21;
* ``s2`` = exp(L[i] - L[i-126]) - 1, at least ``s2_min_valid`` (80) valid returns in
  rows i-125 .. i;
* ``s3`` = exp(L[i] - max(L[i-251 .. i])), at least ``s3_min_valid`` (200) valid
  returns in rows i-251 .. i.

These are the formulas of report 85's T6 code (``deep85/code/t6.py``); T6 itself
did not apply the 200-day minimum to ``s3`` (``s3_min_valid = 0`` reproduces it).
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from trader.panel import FloatArray, PricePanel

BoolArray = npt.NDArray[np.bool_]

S1_FROM, S1_TO, S2_LEN, S3_LEN = 252, 21, 126, 252


def avg_rank(x: FloatArray) -> FloatArray:
    """1-based ascending ranks, ties averaged (``pandas.Series.rank()`` default)."""
    n = len(x)
    if n == 0:
        return np.zeros(0)
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    starts = np.r_[0, np.flatnonzero(np.diff(xs) != 0) + 1]
    ends = np.r_[starts[1:], n]
    avg = (starts + 1 + ends) / 2.0
    ranks = np.empty(n)
    ranks[order] = np.repeat(avg, ends - starts)
    return ranks


def pct_rank(x: FloatArray) -> FloatArray:
    """``pandas.Series.rank(pct=True)``: average rank / count (x has no NaN)."""
    return avg_rank(x) / len(x) if len(x) else np.zeros(0)


def first_row(panel: PricePanel) -> npt.NDArray[np.int64]:
    """Row index of each entity's first close in the panel (``T`` if none)."""
    has = ~np.isnan(panel.close)
    t = panel.n_sessions
    return np.where(has.any(axis=0), has.argmax(axis=0), t).astype(np.int64)


def tv_median(
    panel: PricePanel, window: int, min_days: int, *, zero_fill_listed: bool
) -> FloatArray:
    """Median traded value over the last ``window`` sessions (BW-UNI-10).

    NaN unless the window holds at least ``min_days`` sessions with a row. With
    ``zero_fill_listed`` a session without a row counts as zero once the entity has
    had its first row (FD BW-UNI-10, "inside a listed life"); without it, sessions
    without a row are ignored (report 85 T6).
    """
    tv = panel.tv[-window:]
    valid = ~np.isnan(tv)
    n_valid = valid.sum(axis=0)
    if zero_fill_listed:
        start = panel.n_sessions - tv.shape[0]
        rows = np.arange(start, panel.n_sessions)[:, None]
        listed = rows >= first_row(panel)[None, :]
        tv = np.where(~valid & listed, 0.0, tv)
    out = np.full(tv.shape[1], np.nan)
    ok = n_valid >= min_days
    if ok.any():
        out[ok] = np.nanmedian(tv[:, ok], axis=0)
    return out


def traded_within(panel: PricePanel, sessions: int) -> BoolArray:
    """True if the entity has a close in the last ``sessions`` sessions (D included)."""
    return np.asarray((~np.isnan(panel.close[-sessions:])).any(axis=0), dtype=np.bool_)


def recent_close(panel: PricePanel, sessions: int) -> FloatArray:
    """Close on D, else the latest close within the previous ``sessions`` sessions."""
    block = panel.close[-(sessions + 1) :]
    out = np.full(block.shape[1], np.nan)
    for k in range(block.shape[0]):  # later rows overwrite earlier ones
        row = block[k]
        has = ~np.isnan(row)
        out[has] = row[has]
    return out


def momentum(
    panel: PricePanel, *, s1_min_valid: int = 150, s2_min_valid: int = 80, s3_min_valid: int = 200
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """``(s1, s2, s3)`` at D; all NaN if the panel has fewer than 253 sessions."""
    t, n = panel.ret.shape
    nan = np.full(n, np.nan)
    if t < S1_FROM + 1:
        return nan, nan.copy(), nan.copy()
    r = panel.ret
    valid = ~np.isnan(r)
    lg = np.cumsum(np.log1p(np.where(valid, r, 0.0)), axis=0)
    nv = np.cumsum(valid, axis=0)
    i = t - 1
    with np.errstate(invalid="ignore", over="ignore"):
        s1 = np.expm1(lg[i - S1_TO] - lg[i - S1_FROM])
        s2 = np.expm1(lg[i] - lg[i - S2_LEN])
        s3 = np.exp(lg[i] - lg[i - S3_LEN + 1 : i + 1].max(axis=0))
    s1[(nv[i - S1_TO] - nv[i - S1_FROM]) < s1_min_valid] = np.nan
    s2[(nv[i] - nv[i - S2_LEN]) < s2_min_valid] = np.nan
    if s3_min_valid > 0:
        s3[valid[i - S3_LEN + 1 : i + 1].sum(axis=0) < s3_min_valid] = np.nan
    return s1, s2, s3


def bid_peg(
    panel: PricePanel, *, window: int = 10, span_max: float = 0.03, jump: float = 0.15,
    lookback: int = 30,
) -> BoolArray:  # fmt: skip
    """BW-UNI-22 / EMG2 amendment §2: closes over the last ``window`` sessions span
    less than ``span_max`` (highest / lowest - 1) and a one-day total return of at
    least ``jump`` happened inside the window or in the ``lookback`` sessions before it."""
    c = panel.close[-window:]
    n_c = (~np.isnan(c)).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore", all="ignore"):
        hi = np.nanmax(np.where(np.isnan(c), -np.inf, c), axis=0)
        lo = np.nanmin(np.where(np.isnan(c), np.inf, c), axis=0)
        span = hi / lo - 1.0
    r = panel.ret[-(window + lookback) :]
    jumped = (np.nan_to_num(r, nan=0.0) >= jump).any(axis=0)
    out: BoolArray = (n_c >= 2) & (span < span_max) & jumped
    return out


def age_sessions(panel: PricePanel) -> npt.NDArray[np.int64]:
    """Sessions since the entity's first price row (FD §8.4), a lower bound when the
    first row precedes the panel and is not in ``first_session``."""
    t = panel.n_sessions
    fr = first_row(panel)
    out = np.empty(len(panel.entities), dtype=np.int64)
    for j, e in enumerate(panel.entities):
        known = panel.first_session.get(e)
        if known is not None and known in panel.dates:
            out[j] = t - 1 - panel.dates.index(known)
        elif known is not None and known < panel.dates[0]:
            out[j] = panel.sessions_before + t - 1  # lower bound
        elif fr[j] >= t:
            out[j] = -1
        else:
            out[j] = t - 1 - int(fr[j]) + (panel.sessions_before if fr[j] == 0 else 0)
    return out
