"""Read-only adapter to the forward record's EODHD store (FD v3.0 §21.1, B-fast).

Until milestone B1 (bulk connector and feature store) exists, B-fast reads the
prices the record's scripts already maintain under ``$B/bigwins_forward/data/eodhd``:

* ``manifest.tsv`` (one row per stored response; the latest HTTP-200 file per
  kind and symbol wins), ``symbols.csv`` (vendor symbol list),
* ``raw/eod/<SYM>__<stamp>.json.gz`` full histories, ``raw/splits``, ``raw/div``,
* ``raw/bulk_eod/AU_<date>__<stamp>.json.gz`` daily bulk rows appended after the
  histories, ``raw/bulk_div`` and ``raw/bulk_splits`` likewise.

Nothing is written. The adapter computes split-neutral total returns with the
record's nearest-row split rule (rules v1.3 A3, ``build_tr.reconcile_splits``),
traded value = close adjusted to the decision day x vendor volume (Amendment v1.4),
applies A8 code re-use and the A7(b)/(c) duplicate tests on the panel window, and
returns a ``PricePanel`` whose last row is D (BW-SYS-12).

Deviation recorded in ``docs/DECISIONS.md`` (BF-05): A7 runs on the panel window
(about three years), not on the whole file since 2014; a duplicate needs 120 common
days, so the window only misses pairs whose overlap ended more than three years ago,
which cannot be eligible on D.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from trader.data.identity import cut_code_reuse, duplicates_a7b, duplicates_a7c, security_class
from trader.panel import PricePanel

RET_MIN, RET_MAX = -0.95, 10.0  # T6/build85: returns outside are invalid


@dataclass(frozen=True)
class SymbolInfo:
    code: str  # without ".AU"
    name: str
    vendor_type: str
    delisted: bool


def parse_split(text: str) -> float:
    try:
        a, b = (float(x) for x in str(text).split("/"))
    except ValueError:
        return math.nan
    return a / b if a > 0 and b > 0 else math.nan


def reconcile_splits(
    close: Sequence[float], listed: Sequence[float], before: int = 3, after: int = 5
) -> list[float]:
    """Rules v1.3 A3 (``build_tr.reconcile_splits``): apply each listed ratio on the
    session within -``before``..+``after`` whose close jump best matches 1/ratio; skip it
    when none matches; ratios within 10% of 1 only when the listed-day jump agrees."""
    n = len(close)
    split = [1.0] * n
    c = [x if x > 0 else math.nan for x in close]
    jump = [math.nan] + [c[i] / c[i - 1] for i in range(1, n)]
    for k in range(n):
        s = listed[k]
        if s == 1.0 or not math.isfinite(s):
            continue
        ls = abs(math.log(s))
        if ls < math.log(1.10):
            j = jump[k]
            if math.isfinite(j) and abs(math.log(j * s)) < abs(math.log(j)):
                split[k] *= s
            continue
        best, bk = math.inf, -1
        for i in range(max(1, k - before), min(n - 1, k + after) + 1):
            if math.isfinite(jump[i]):
                e = abs(math.log(jump[i] * s))
                if e < best:
                    best, bk = e, i
        if bk >= 0 and best < 0.5 * ls:
            split[bk] *= s
    return split


def symbol_returns(
    rows: Sequence[dict[str, Any]], splits: Iterable[tuple[date, float]],
    divs: Iterable[tuple[date, float]],
) -> tuple[list[date], list[float], list[float], list[float], list[float]]:  # fmt: skip
    """Per symbol: (dates, close, volume, split factor applied, total return)."""
    days = [date.fromisoformat(str(r["date"])[:10]) for r in rows]
    close = [float(r.get("close") or 0.0) for r in rows]
    vol = [float(r.get("volume") or 0.0) for r in rows]
    listed = [1.0] * len(days)
    div = [0.0] * len(days)
    pos = {d: i for i, d in enumerate(days)}

    def slot(d: date) -> int | None:  # an event on a non-trading date goes to the next row
        if d in pos:
            return pos[d]
        later = [i for i, x in enumerate(days) if x > d]
        return later[0] if later else None

    for d, r in splits:
        k = slot(d)
        if k is not None and math.isfinite(r):
            listed[k] *= r
    for d, v in divs:
        k = slot(d)
        if k is not None and math.isfinite(v):
            div[k] += v
    split = reconcile_splits(close, listed)
    ret = [math.nan] * len(days)
    for i in range(1, len(days)):
        c, pc = close[i], close[i - 1]
        if c > 0 and pc > 0:
            r = (c * split[i] + div[i]) / pc - 1.0
            ret[i] = r if RET_MIN <= r <= RET_MAX else math.nan
    return days, close, vol, split, ret


def adjusted_to_last(close: Sequence[float], split: Sequence[float]) -> list[float]:
    """Amendment v1.4: close adjusted to the last row (each later split divides it)."""
    factor = 1.0
    adj = [math.nan] * len(close)
    for i in range(len(close) - 1, -1, -1):
        adj[i] = close[i] / factor if close[i] > 0 else math.nan
        factor *= split[i]
    return adj


class ForwardStore:
    """Read-only view of ``bigwins_forward/data/eodhd``."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        if not (self.root / "manifest.tsv").is_file():
            raise FileNotFoundError(f"no manifest.tsv under {self.root}")
        self._latest: dict[tuple[str, str], Path] = {}
        with (self.root / "manifest.tsv").open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r.get("http") == "200" and r.get("file"):
                    self._latest[(r["kind"], r["symbol"])] = self.root / r["file"]

    @staticmethod
    def _read(path: Path) -> Any:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)

    def symbols(self) -> dict[str, SymbolInfo]:
        out: dict[str, SymbolInfo] = {}
        with (self.root / "symbols.csv").open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out[r["Code"]] = SymbolInfo(
                    r["Code"], r.get("Name", ""), r.get("Type", ""), r.get("delisted") == "1"
                )
        return out

    def _bulk(self, kind: str) -> dict[date, list[dict[str, Any]]]:
        out: dict[date, list[dict[str, Any]]] = {}
        d = self.root / "raw" / kind
        if not d.is_dir():
            return out
        for p in sorted(d.glob("AU_*.json.gz")):  # later stamps of a day replace earlier
            rows = self._read(p)
            if rows:
                out[date.fromisoformat(p.name[3:13])] = rows
        return out

    def build_panel(
        self,
        as_of: date,
        sessions: Sequence[date],
        *,
        history: int = 760,
        etp_codes: frozenset[str] = frozenset(),
        lic_codes: frozenset[str] = frozenset(),
        apply_duplicates: bool = True,
    ) -> PricePanel:
        """The panel of every stored ``.AU`` symbol for the last ``history`` sessions to D."""
        if as_of not in sessions:
            raise ValueError(f"{as_of} is not an ASX session")
        sess = [d for d in sessions if d <= as_of][-history:]
        idx = {d: i for i, d in enumerate(sess)}
        all_sess = frozenset(sessions)
        warmup = sessions[max(0, sessions.index(sess[0]) - 10)]
        bulk = self._bulk("bulk_eod")
        bulk_div = self._bulk("bulk_div")
        bulk_split = self._bulk("bulk_splits")
        info = self.symbols()
        syms = sorted(s for (k, s) in self._latest if k == "eod" and s.endswith(".AU"))
        t, n = len(sess), len(syms)
        close = np.full((t, n), np.nan)
        ret = np.full((t, n), np.nan)
        tv = np.full((t, n), np.nan)
        cls: dict[str, str] = {}
        for j, sym in enumerate(syms):
            code = sym[:-3]
            rows = [
                r
                for r in self._read(self._latest[("eod", sym)])
                if str(r["date"])[:10] <= str(as_of)
            ]
            last = str(rows[-1]["date"])[:10] if rows else ""
            for d in sorted(bulk):
                if str(d) > last and d <= as_of:
                    rows += [r for r in bulk[d] if r.get("code") == code]
            rows = [
                r for r in rows if _day(r) in all_sess and _day(r) >= warmup
            ]  # A3: sessions only
            spl = [
                (date.fromisoformat(x["date"]), parse_split(x["split"]))
                for x in self._events("splits", sym)
            ]
            spl += [
                (d, parse_split(x["split"]))
                for d, xs in bulk_split.items()
                for x in xs
                if x.get("code") == code
            ]
            dv = [(date.fromisoformat(x["date"]), _num(x)) for x in self._events("div", sym)]
            dv += [
                (d, _num(x))
                for d, xs in bulk_div.items()
                for x in xs
                if x.get("code") == code and x.get("currency") in (None, "AUD")
            ]
            days, c, v, split, r = symbol_returns(
                rows, [s for s in spl if s[0] <= as_of], [x for x in dv if x[0] <= as_of]
            )
            adj = adjusted_to_last(c, split)
            for i, d in enumerate(days):
                k = idx.get(d)
                if k is None or not c[i] > 0:
                    continue
                close[k, j] = c[i]
                ret[k, j] = r[i]
                tv[k, j] = adj[i] * v[i]
            si = info.get(code)
            cls[code] = security_class(
                code, si.vendor_type if si else "", si.name if si else "",
                etp_codes=etp_codes, lic_codes=lic_codes,
            )  # fmt: skip
        close = cut_code_reuse(sess, close)
        ret = np.where(np.isnan(close), np.nan, ret)
        tv = np.where(np.isnan(close), np.nan, tv)
        keep = list(range(n))
        if apply_duplicates:
            dups = duplicates_a7b(close)
            dropped = frozenset(p.dup for p in dups)
            dups += duplicates_a7c(close, tv, ret, exclude=dropped)
            gone = {p.dup for p in dups}
            keep = [j for j in range(n) if j not in gone]
        codes = [syms[j][:-3] for j in keep]
        return PricePanel(
            as_of=as_of, dates=tuple(sess), entities=tuple(codes),
            close=close[:, keep], ret=ret[:, keep], tv=tv[:, keep],
            sec_class={c: cls[c] for c in codes},
        )  # fmt: skip

    def _events(self, kind: str, sym: str) -> list[dict[str, Any]]:
        p = self._latest.get((kind, sym))
        if p is None:
            return []
        data = self._read(p)
        return list(data) if isinstance(data, list) else []


def _day(r: dict[str, Any]) -> date:
    return date.fromisoformat(str(r["date"])[:10])


def _num(x: dict[str, Any]) -> float:
    try:
        return float(x.get("unadjustedValue") or x.get("value") or x.get("dividend") or "nan")
    except (TypeError, ValueError):
        return math.nan
