"""Entity identity: security class, code re-use and duplicate codes (FD v3.0 §5.1).

Pure functions ported from the record's reference code (``bigwins_forward/code/
bw13_prep.py``: rules v1.3 A4, A7(b), A8; Amendment v1.5 ``_old`` codes; Amendment
v1.6 A7(c) daily-return duplicate test).

* ``security_class`` (BW-UNI-03, EMG2 amendment §2): ``ORD`` / ``REIT`` / ``LIC`` /
  ``FUND`` / ``OTHER``. ``DUAL`` needs first-seen market cap and is not assigned in
  B-fast (it is "flagged, kept", so it never changes a list).
* ``cut_code_reuse`` (BW-UNI-01, A8): a gap of more than 200 calendar days between
  consecutive closes starts a new entity; the forward panel keeps the current one.
* ``duplicates_a7b`` / ``duplicates_a7c`` (BW-UNI-02): codes that carry the same
  company. The later-living code is kept.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import numpy as np
import numpy.typing as npt

OLD_RE = re.compile(r"^[A-Z0-9]{3}_old[0-9]*$")
LIC_NAME_RE = re.compile(r"\bINVESTMENTS?\b|\bCAPITAL FUND\b|\bLIC\b")
REIT_NAME_RE = re.compile(r"\bREIT\b|\bPROPERTY (TRUST|FUND|GROUP)\b|\bPROPERTIES\b")
FUND_TYPES = frozenset({"ETF", "FUND", "MUTUAL FUND"})


def security_class(
    code: str,
    vendor_type: str,
    name: str,
    *,
    etp_codes: frozenset[str] = frozenset(),
    lic_codes: frozenset[str] = frozenset(),
) -> str:
    """BW-UNI-03 class of one vendor code (code without the ``.AU`` suffix)."""
    base = code.split("_old")[0]
    upper = (name or "").upper()
    if vendor_type.upper() in FUND_TYPES or base in etp_codes:
        return "FUND"
    if vendor_type != "Common Stock" or not (len(code) == 3 or OLD_RE.match(code)):
        return "OTHER"
    if base in lic_codes or LIC_NAME_RE.search(upper):
        return "LIC"
    if REIT_NAME_RE.search(upper):
        return "REIT"
    return "ORD"


def cut_code_reuse(
    dates: Sequence[date], close: npt.NDArray[np.float64], gap_days: int = 200
) -> npt.NDArray[np.float64]:
    """A8: NaN every row of a column before its last gap of more than ``gap_days``
    calendar days between consecutive closes (the earlier rows were another company)."""
    out = np.array(close, dtype=np.float64, copy=True)
    ords = np.array([d.toordinal() for d in dates])
    for j in range(out.shape[1]):
        rows = np.flatnonzero(~np.isnan(out[:, j]))
        if len(rows) < 2:
            continue
        gaps = np.flatnonzero(np.diff(ords[rows]) > gap_days)
        if len(gaps):
            out[: rows[gaps[-1] + 1], j] = np.nan
    return out


@dataclass(frozen=True)
class DupPair:
    dup: int  # column dropped
    keep: int  # column it continues as
    rule: str  # "A7b" | "A7c"
    score: float


def _last_rows(close: npt.NDArray[np.float64]) -> npt.NDArray[np.int64]:
    has = ~np.isnan(close)
    t = close.shape[0]
    last = t - 1 - np.argmax(has[::-1], axis=0)
    return np.where(has.any(axis=0), last, -1).astype(np.int64)


def _later(
    last: npt.NDArray[np.int64], ncl: npt.NDArray[np.int64], j: int
) -> npt.NDArray[np.bool_]:
    """Codes living after column ``j`` (A7(c) tie rules: more closes, then column order)."""
    col = np.arange(len(last))
    lj = last[j]
    same = (last == lj) & ((ncl > ncl[j]) | ((ncl == ncl[j]) & (col < j)))
    return np.asarray((last > lj) | same, dtype=np.bool_)


def duplicates_a7b(
    close: npt.NDArray[np.float64], window: int = 60, min_days: int = 30
) -> list[DupPair]:
    """A7(b): X's closes over the last ``window`` rows of its life agree with Y's on at
    least 90% of at least ``min_days`` common days, with at least 5 distinct closes, and
    Y's life ends later."""
    last = _last_rows(close)
    t = close.shape[0]
    out: list[DupPair] = []
    for j in range(close.shape[1]):
        lj = last[j]
        if lj < window or lj >= t - 1:
            continue
        a = close[lj - window + 1 : lj + 1, j]
        m = ~np.isnan(a)
        if m.sum() < min_days:
            continue
        block = close[lj - window + 1 : lj + 1]
        both = m[:, None] & ~np.isnan(block)
        nb = both.sum(axis=0)
        with np.errstate(invalid="ignore"):
            agree = (both & (np.abs(block - a[:, None]) <= 1e-6 * np.abs(a[:, None]))).sum(axis=0)
        cand = [
            q
            for q in np.flatnonzero((nb >= min_days) & (agree >= 0.9 * nb) & (last > lj))
            if q != j and len(np.unique(a[both[:, q]])) >= 5
        ]
        if cand:
            q = sorted(cand, key=lambda q: (-agree[q], q))[0]
            out.append(DupPair(j, int(q), "A7b", float(agree[q] / nb[q])))
    return out


def duplicates_a7c(
    close: npt.NDArray[np.float64],
    volume: npt.NDArray[np.float64],
    price_ret: npt.NDArray[np.float64],
    *,
    exclude: frozenset[int] = frozenset(),
    min_common: int = 120,
    min_nonzero: int = 100,
    pearson: float = 0.995,
) -> list[DupPair]:
    """A7(c) (Amendment v1.6): daily-return duplicate test.

    A code has a clean return on day t when it has a row with close > 0 and volume > 0
    on t and on the previous day. X duplicates Y when, on days both have a clean
    return, there are >= ``min_common`` days, X's return is non-zero on >=
    ``min_nonzero`` of them and the Pearson correlation is >= ``pearson``; Y must live
    later (``_later``). Several Y: highest correlation, then column order.
    """
    n = close.shape[1]
    live = np.array([j not in exclude for j in range(n)])
    with np.errstate(invalid="ignore"):
        trd = np.isfinite(close) & (close > 0) & (np.nan_to_num(volume) > 0)
    u = np.zeros_like(trd)
    u[1:] = trd[1:] & trd[:-1]
    u &= np.isfinite(price_ret)
    u[:, ~live] = False
    last = _last_rows(close)
    ncl = np.isfinite(close).sum(axis=0).astype(np.int64)
    # Matrix estimate of every pairwise correlation; only pairs >= 0.99 are computed exactly
    r0 = np.where(u, price_ret, 0.0)
    mf = u.astype(np.float64)
    cnt = mf.T @ mf
    sx = r0.T @ mf
    sxx = (r0 * r0).T @ mf
    sxy = r0.T @ r0
    with np.errstate(all="ignore"):
        est = (cnt * sxy - sx * sx.T) / np.sqrt((cnt * sxx - sx * sx) * (cnt * sxx.T - sx.T * sx.T))
    out: list[DupPair] = []
    for j in range(n):
        if not live[j] or last[j] < 0 or u[:, j].sum() < min_common:
            continue
        cand = np.flatnonzero(
            _later(last, ncl, j) & live & (cnt[j] >= min_common) & (np.nan_to_num(est[j]) >= 0.99)
        )
        best: tuple[int, float] | None = None
        for q in cand:
            if q == j:
                continue
            m = u[:, j] & u[:, q]
            if m.sum() < min_common:
                continue
            x = price_ret[m, j]
            y = price_ret[m, q]
            if (np.abs(x) > 1e-12).sum() < min_nonzero or x.std() == 0 or y.std() == 0:
                continue
            c = float(np.corrcoef(x, y)[0, 1])
            if c >= pearson and (best is None or c > best[1]):
                best = (int(q), c)
        if best is not None:
            out.append(DupPair(j, best[0], "A7c", best[1]))
    return out
