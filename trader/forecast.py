"""Forecast bands (BF-D66): the historical range of excess returns for shares the
strategy picked with a similar score, read from ``config/forecast_bands*.csv`` (method
fb1, docs/FORECAST_BANDS.md). Read-only and for display only: the trader never reads
these files and nothing here can trade. A missing file, column or bucket means "not
available yet", never an error on the screen.
"""

from __future__ import annotations

import csv
import math
import re
from bisect import bisect_right
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from itertools import pairwise
from pathlib import Path

BUCKETS = ("top5", "top20", "20_40", "40_60", "60_100")
BUCKET_LABEL = {
    "top5": "top 5% of band C",
    "top20": "top 5-20% of band C",
    "20_40": "20-40% of band C",
    "40_60": "40-60% of band C",
    "60_100": "bottom 40% of band C",
}
QS = (0.10, 0.25, 0.50, 0.75, 0.90)
REQUIRED = ("score_bucket", "months_since_entry", "p10", "p25", "p50", "p75", "p90", "n_obs",
            "period_start", "period_end", "method_version")  # fmt: skip
BENCH = {"a200": ("forecast_bands_a200.csv", "ASX 200"),
         "bandc": ("forecast_bands.csv", "band C average")}  # fmt: skip


@dataclass(frozen=True)
class BandRow:
    month: int
    q: tuple[float, float, float, float, float]  # p10, p25, p50, p75, p90
    n_obs: int
    mean: float | None = None  # only when the file has a ``mean`` column


@dataclass(frozen=True)
class Bands:
    bench: str  # "a200" or "bandc"
    label: str
    rows: dict[str, dict[int, BandRow]]
    period: tuple[str, str]
    method: str
    means_12m: dict[str, float] = field(default_factory=dict)  # from the doc (band C only)

    def bucket(self, b: str | None) -> dict[int, BandRow]:
        return dict(self.rows.get(b or "", {}))


def bucket_of(score_pct: float | None) -> str | None:
    """The score bucket of a band-C score percentile (1.0 = the best score)."""
    if score_pct is None or not math.isfinite(score_pct):
        return None
    if score_pct > 0.95:
        return "top5"
    if score_pct > 0.80:
        return "top20"
    if score_pct > 0.60:
        return "20_40"
    if score_pct > 0.40:
        return "40_60"
    return "60_100"


def _num(x: str | None) -> float | None:
    try:
        v = float(str(x).strip())
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def doc_means(text: str) -> dict[str, float]:
    """The 12-month means per bucket from the doc's "Median and mean" table (vs band C)."""
    out: dict[str, float] = {}
    head = text.find("mean 12m")
    if head < 0:
        return out
    for line in text[head:].splitlines()[1:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.strip().startswith("|"):
            if out:
                break
            continue
        if cells and cells[0] in BUCKETS:
            m = re.match(r"([+\-\u2212]?)(\d+(?:\.\d+)?)%", cells[-1])
            if m:
                sign = -1 if m.group(1) in ("-", "\u2212") else 1
                out[cells[0]] = sign * float(m.group(2)) / 100
    return out


def load_bands(config_dir: Path | None, bench: str = "a200") -> Bands | None:
    """One benchmark's bands, or None when the file is missing or not in the fb format."""
    if config_dir is None or bench not in BENCH:
        return None
    name, label = BENCH[bench]
    p = Path(config_dir) / name
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return None
    rd = csv.DictReader(text.splitlines())
    if rd.fieldnames is None or any(c not in rd.fieldnames for c in REQUIRED):
        return None
    rows: dict[str, dict[int, BandRow]] = {}
    period = ("", "")
    method = ""
    for r in rd:
        b = (r.get("score_bucket") or "").strip()
        m = _num(r.get("months_since_entry"))
        q = [_num(r.get(k)) for k in ("p10", "p25", "p50", "p75", "p90")]
        n = _num(r.get("n_obs"))
        if b not in BUCKETS or m is None or not 1 <= m <= 12 or any(x is None for x in q):
            continue
        qq = tuple(float(x or 0.0) for x in q)
        if list(qq) != sorted(qq):
            continue
        rows.setdefault(b, {})[int(m)] = BandRow(
            int(m), (qq[0], qq[1], qq[2], qq[3], qq[4]), int(n or 0), _num(r.get("mean"))
        )
        period = (str(r.get("period_start") or ""), str(r.get("period_end") or ""))
        method = str(r.get("method_version") or "")
    if not rows:
        return None
    means: dict[str, float] = {}
    if bench == "bandc":
        doc = Path(config_dir).parent / "docs" / "FORECAST_BANDS.md"
        try:
            means = doc_means(doc.read_text(encoding="utf-8"))
        except OSError:
            means = {}
    return Bands(bench, label, rows, period, method, means)


def percentile_of(x: float, row: BandRow) -> float:
    """Where ``x`` sits among past picks (0.10..0.90 by linear interpolation between the
    quantiles; 0.05 below p10 and 0.95 above p90, read as "below 10th" / "above 90th")."""
    q = row.q
    if x < q[0]:
        return 0.05
    if x > q[-1]:
        return 0.95
    for (a, pa), (b, pb) in pairwise(zip(q, QS, strict=True)):
        if a <= x <= b:
            return pa if b - a < 1e-12 else pa + (x - a) / (b - a) * (pb - pa)
    return 0.5


def percentile_text(p: float) -> str:
    if p <= 0.05:
        return "below the 10th percentile"
    if p >= 0.95:
        return "above the 90th percentile"
    n = round(p * 100)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"at the {n}{suf} percentile"


def _at(series: Sequence[tuple[date, float]], d: date) -> float | None:
    """The last value on or before ``d``."""
    k = bisect_right([x for x, _ in series], d) - 1
    return series[k][1] if k >= 0 else None


def _from(series: Sequence[tuple[date, float]], d: date) -> tuple[date, float] | None:
    """The first point on or after ``d``."""
    for x, v in series:
        if x >= d and v > 0:
            return x, v
    return None


def month_ends(after: date, upto: date, sessions: Sequence[date],
               px: Sequence[tuple[date, float]]) -> list[date]:  # fmt: skip
    """Month-end sessions after ``after`` up to ``upto`` (from the sessions, else from the
    price days: a day whose next price day is in another month)."""
    days = sorted(sessions) if sessions else [d for d, _ in px]
    return [a for a, b in pairwise(days) if after < a <= upto and b.month != a.month]


@dataclass(frozen=True)
class Actual:
    entry: date
    month: int
    day: date
    excess: float  # stock return minus index return since entry
    stock: float
    index: float


def actual_path(px: Sequence[tuple[date, float]], idx: Sequence[tuple[date, float]],
                entry: date, upto: date, sessions: Sequence[date] = (),
                entry_price: float | None = None) -> list[Actual]:  # fmt: skip
    """The share's excess return vs the index at each month-end after entry (1..12)."""
    p0 = _from(px, entry)
    i0 = _from(idx, entry)
    if p0 is None or i0 is None:
        return []
    base = entry_price if entry_price and entry_price > 0 else p0[1]
    out: list[Actual] = []
    for m, d in enumerate(month_ends(entry, upto, sessions, px), 1):
        if m > 12:
            break
        p, i = _at(px, d), _at(idx, d)
        if p is None or i is None or p <= 0 or i <= 0:
            continue
        s, ix = p / base - 1, i / i0[1] - 1
        out.append(Actual(entry, m, d, s - ix, s, ix))
    return out


def excess_on(px: Sequence[tuple[date, float]], idx: Sequence[tuple[date, float]],
              entry: date, d: date, entry_price: float | None = None,
              price: float | None = None) -> float | None:  # fmt: skip
    """Excess return vs the index from entry to day ``d`` (e.g. the sell day)."""
    p0, i0 = _from(px, entry), _from(idx, entry)
    if i0 is None:
        return None
    base = entry_price if entry_price and entry_price > 0 else (p0[1] if p0 else None)
    p = price if price is not None else _at(px, d)
    i = _at(idx, d)
    if not base or p is None or i is None or i <= 0:
        return None
    return (p / base - 1) - (i / i0[1] - 1)


def high_52w(px: Sequence[tuple[date, float]]) -> list[tuple[date, float]]:
    """The rolling 52-week high (365 calendar days) of a price series."""
    out: list[tuple[date, float]] = []
    win: list[tuple[date, float]] = []
    for d, v in px:
        win.append((d, v))
        while win and (d - win[0][0]).days > 365:
            win.pop(0)
        out.append((d, max(x for _, x in win)))
    return out
