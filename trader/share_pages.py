"""Shares and "Expected vs actual" (BF-D66): for every share the strategy held, sold,
proposed or passed over, its rank history at each month-end decision, the historical
range of similar picks (``trader.forecast``) with the share's actual path on top, its
price history and what the rules do next. Read-only screens (GET only); every chart has
a tap read-out (``data-tips`` in ``webui.JS``) and works as a plain picture without
JavaScript.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any
from urllib.parse import quote

from trader import forecast as fc
from trader.constants import ASX_TZ
from trader.journal import FillRecord, Journal
from trader.orders import Side
from trader.webui import backlink, chev, e, section

SKEW = ("Most picks end near or a bit behind the market; the strategy's gains come from a "
        "minority of big winners — that's why it holds 18 shares.")  # fmt: skip
NOT_PREDICTION = "Historical range for similar picks — not a price prediction."
STATUS_LABEL = {"holding": "Holding", "sold": "Sold", "proposed": "Proposed",
                "passed": "Passed over"}  # fmt: skip
Series = list[tuple[date, float]]


@dataclass
class ShareCtx:
    """What the share screens read (all read-only)."""

    journal: Journal
    book: str
    now: datetime
    sessions: Sequence[date] = ()
    prices: Callable[[str], Series] | None = None
    index: Callable[[], Series] | None = None
    index_label: str = "index"
    bands: dict[str, fc.Bands | None] = field(default_factory=dict)
    demo: bool = False
    # BF-D72 (strategy review L2): a share's total-return level (dividends in, splits
    # neutral); None = the closes (then dividends are missing from the actual line)
    tr: Callable[[str], Series] | None = None
    names: dict[str, str] = field(default_factory=dict)  # code -> company name

    @property
    def today(self) -> date:
        return self.now.astimezone(ASX_TZ).date()


@dataclass
class Info:
    code: str
    status: str
    held: bool = False
    fills: list[FillRecord] = field(default_factory=list)
    ranks: list[dict[str, Any]] = field(default_factory=list)  # one per decision it was in
    first_flag: date | None = None  # first decision on T (proposed) or in the top 20%


def _aware(t: datetime) -> datetime:
    from trader.app_pages import _aware as aw

    return aw(t)


def _lists(j: Journal) -> list[tuple[date, dict[str, Any]]]:
    from trader.app_pages import jobs

    out = []
    for k, r in jobs(j, "emg2list:"):
        try:
            out.append((date.fromisoformat(k.split(":", 1)[1]), r))
        except ValueError:
            continue
    return sorted(out, key=lambda x: x[0])


def _f(x: object) -> float | None:
    try:
        return None if x is None else float(str(x))
    except ValueError:
        return None


def rank_rows(lists: Sequence[tuple[date, dict[str, Any]]], code: str) -> list[dict[str, Any]]:
    """The share's row at every recorded decision (``None`` fields when not in band C)."""
    out = []
    for d, rec in lists:
        bc = rec.get("band_c", [])
        row = next((r for r in bc if r and r[0] == code), None)
        out.append({
            "day": d, "n": len(bc), "in": row is not None,
            "rank": int(row[5]) if row is not None else None,
            "pct": _f(row[4]) if row is not None else None,
            "s": [_f(row[k]) for k in (1, 2, 3)] if row is not None else [None] * 3,
            "target": code in rec.get("targets", []),
        })  # fmt: skip
    return out


def collect(ctx: ShareCtx, held: Sequence[str], limit: int = 400) -> dict[str, Info]:
    """Every share ever held, sold, proposed (on the buy list T) or passed over (in the
    top 20% of band C but never on T or bought), newest decision first."""
    from trader.app_pages import safe

    j = ctx.journal
    allf: list[FillRecord] = safe(lambda: j.fills(ctx.book), [])
    lists = _lists(j)
    out: dict[str, Info] = {}
    for f in allf:
        out.setdefault(f.entity, Info(f.entity, "sold")).fills.append(f)
    for c in held:
        out.setdefault(c, Info(c, "holding")).status = "holding"
        out[c].held = True
    for _d, rec in reversed(lists):
        for c in rec.get("targets", []):
            if c not in out:
                out[c] = Info(c, "proposed")
        for r in rec.get("band_c", []):
            p = _f(r[4]) if len(r) > 4 else None
            if p is not None and p > 0.80 and r[0] not in out:
                out[r[0]] = Info(r[0], "passed")
        if len(out) >= limit:
            break
    for c, info in out.items():
        for d, rec in lists:
            on_t = c in rec.get("targets", [])
            top = any(r[0] == c and (_f(r[4]) or 0) > 0.80 for r in rec.get("band_c", []))
            if on_t or top:
                info.first_flag = d
                break
    return out


# ---------------------------------------------------------------- chart helpers


def _hit(x: float, w: float, h: float, tip: str, top: float = 0) -> str:
    return (f'<rect class="hit" x="{x:.1f}" y="{top:.1f}" width="{max(w, 1):.1f}" '
            f'height="{h:.1f}" data-tip="{e(tip)}"/>')  # fmt: skip


def _tipbox(svg: str, legend: str = "") -> str:
    return (f'<div class="chartbox" data-tips>{svg}<div class="ctip" aria-hidden="true"></div>'
            f"</div>{legend}")  # fmt: skip


def _pc(x: float | None, dp: int = 1) -> str:
    if x is None:
        return "-"
    return f"{'+' if x >= 0 else '−'}{abs(x) * 100:.{dp}f}%"


def _path(pts: Sequence[tuple[float, float]]) -> str:
    return " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))


# ---------------------------------------------------------------- 1. rank history


def rank_chart(rows: Sequence[dict[str, Any]], code: str) -> str:
    pts = [r for r in rows if r["pct"] is not None]
    if not rows:
        return '<p class="muted">No month-end decision has been recorded yet.</p>'
    w, h, pl, pr, pt, pb = 340, 150, 34, 10, 10, 22
    n = len(rows)

    def xx(i: int) -> float:
        return pl + (i + 0.5) / n * (w - pl - pr)

    def yy(p: float) -> float:
        return pt + (1 - p) * (h - pt - pb)

    cut = "".join(
        f'<line x1="{pl}" x2="{w - pr}" y1="{yy(p):.1f}" y2="{yy(p):.1f}" class="cut {c}"/>'
        f'<text x="{w - pr}" y="{yy(p) - 3:.1f}" class="ax" text-anchor="end">{lab}</text>'
        for p, c, lab in ((0.80, "c20", "top 20% (buy list)"), (0.60, "c40", "top 40% (keep)"))
    )
    axis = "".join(
        f'<text x="{pl - 4}" y="{yy(p) + 3:.1f}" class="ax" text-anchor="end">{p * 100:.0f}</text>'
        for p in (0.0, 0.5, 1.0)
    )
    line_pts: list[tuple[float, float]] = []
    segs: list[str] = []
    for i, r in enumerate(rows):
        if r["pct"] is None:
            if len(line_pts) > 1:
                segs.append(_path(line_pts))
            line_pts = []
        else:
            line_pts.append((xx(i), yy(r["pct"])))
    if len(line_pts) > 1:
        segs.append(_path(line_pts))
    dots, hits = [], []
    cw = (w - pl - pr) / n
    for i, r in enumerate(rows):
        if r["pct"] is None:
            dots.append(f'<circle cx="{xx(i):.1f}" cy="{h - pb - 3:.1f}" r="3" class="out"/>')
            tip = f"{r['day']:%d %b %Y}\nnot in band C ({r['n']} names)"
        else:
            cls = "rk top" if r["pct"] > 0.80 else ("rk keep" if r["pct"] > 0.60 else "rk")
            dots.append(f'<circle cx="{xx(i):.1f}" cy="{yy(r["pct"]):.1f}" r="4" class="{cls}"/>')
            s = r["s"]
            tip = (f"{r['day']:%d %b %Y}\nrank {r['rank']} of {r['n']} · percentile "
                   f"{r['pct'] * 100:.0f}\ns1 {_n(s[0])} · s2 {_n(s[1])} · s3 {_n(s[2])}"
                   + ("\non the buy list" if r["target"] else ""))  # fmt: skip
        hits.append(_hit(pl + i * cw, cw, h - pb, tip))
    svg = (
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{e(code)} score '
        f'percentile in band C at each month-end decision">{axis}{cut}'
        + "".join(f'<path d="{s}" class="s1"/>' for s in segs) + "".join(dots)
        + f'<text x="{pl}" y="{h - 5}" class="ax">{rows[0]["day"]:%b %y}</text>'
        f'<text x="{w - pr}" y="{h - 5}" class="ax" text-anchor="end">{rows[-1]["day"]:%b %y}</text>'
        + "".join(hits) + "</svg>"
    )  # fmt: skip
    legend = ('<p class="legend">Score percentile in band C (100 = best). Tap a decision to '
              "read its rank and scores.</p>")  # fmt: skip
    last = pts[-1] if pts else None
    head = (
        f"<p>Latest: rank <b>{last['rank']} of {last['n']}</b> (percentile "
        f"{last['pct'] * 100:.0f}) on {last['day']:%d %b %Y}.</p>"
        if last else "<p class='muted'>It has not been in band C at a recorded decision.</p>"
    )  # fmt: skip
    table = "".join(
        f"<tr><td>{r['day']:%d %b %y}</td><td class='r'>{r['rank'] or '-'}</td>"
        f"<td class='r'>{'-' if r['pct'] is None else format(r['pct'] * 100, '.0f')}</td>"
        f"<td class='r'>{_n(r['s'][0])}</td><td class='r'>{_n(r['s'][1])}</td>"
        f"<td class='r'>{_n(r['s'][2])}</td></tr>"
        for r in reversed(rows[-24:])
    )
    return head + _tipbox(svg, legend) + (
        "<details><summary>Table</summary><table><thead><tr><th>Decision</th><th class='r'>Rank"
        "</th><th class='r'>Pct</th><th class='r'>s1</th><th class='r'>s2</th><th class='r'>s3"
        f"</th></tr></thead><tbody>{table}</tbody></table></details>"
    )  # fmt: skip


def _n(x: float | None) -> str:
    return "-" if x is None else f"{x:.3f}"


# ---------------------------------------------------------------- 2. expected range


def fan_chart(  # noqa: PLR0912, PLR0915 - one block per layer of the chart
    bands: fc.Bands, bucket: str, act: Sequence[fc.Actual], code: str,
              exit_point: tuple[int, float] | None = None) -> str:  # fmt: skip
    rows = bands.bucket(bucket)
    if not rows:
        return (f'<p class="muted">Not available yet: the {e(bands.label)} file has no rows '
                f"for the {e(fc.BUCKET_LABEL.get(bucket, bucket))} bucket.</p>")  # fmt: skip
    months = sorted(rows)
    w, h, pl, pr, pt, pb = 340, 210, 40, 12, 12, 24
    mean12 = bands.means_12m.get(bucket)
    vals = [v for m in months for v in rows[m].q] + [0.0] + [a.excess for a in act]
    vals += [rows[m].mean for m in months if rows[m].mean is not None]  # type: ignore[misc]
    if mean12 is not None:
        vals.append(mean12)
    if exit_point:
        vals.append(exit_point[1])
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.06 or 0.05
    lo, hi = lo - pad, hi + pad

    def xx(m: float) -> float:
        return pl + m / 12 * (w - pl - pr)

    def yy(v: float) -> float:
        return pt + (hi - v) / (hi - lo) * (h - pt - pb)

    def band(a: int, b: int) -> str:
        top = [(xx(0), yy(0))] + [(xx(m), yy(rows[m].q[b])) for m in months]
        bot = [(xx(m), yy(rows[m].q[a])) for m in reversed(months)] + [(xx(0), yy(0))]
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in top + bot)

    med = _path([(xx(0), yy(0))] + [(xx(m), yy(rows[m].q[2])) for m in months])
    mean_line = ""
    if all(rows[m].mean is not None for m in months):
        mean_line = (f'<path d="{_path([(xx(0), yy(0))] + [(xx(m), yy(rows[m].mean or 0)) for m in months])}" '
                     'class="meanl"/>')  # fmt: skip
    elif mean12 is not None and 12 in rows:
        mean_line = (
            f'<path d="{_path([(xx(0), yy(0)), (xx(12), yy(mean12))])}" class="meanl"/>'
            f'<path d="M{xx(12):.1f},{yy(mean12) - 6:.1f} l6,6 l-6,6 l-6,-6 z" class="meand"/>'
        )
    grid = "".join(
        f'<line x1="{pl}" x2="{w - pr}" y1="{yy(v):.1f}" y2="{yy(v):.1f}" class="grid"/>'
        f'<text x="{pl - 4}" y="{yy(v) + 3:.1f}" class="ax" text-anchor="end">{_pc(v, 0)}</text>'
        for v in _ticks(lo, hi)
    )
    actual = ""
    if act:
        ap = [(xx(0), yy(0))] + [(xx(a.month), yy(a.excess)) for a in act]
        actual = (f'<path d="{_path(ap)}" class="act"/>'
                  + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4.5 if k == len(ap) - 1 else 3}" '
                            'class="actd"/>' for k, (x, y) in enumerate(ap) if k))  # fmt: skip
    if exit_point:
        m_, v_ = exit_point
        actual += f'<circle cx="{xx(m_):.1f}" cy="{yy(v_):.1f}" r="5.5" class="selld"/>'
    by_m = {a.month: a for a in act}
    hits = []
    cw = (w - pl - pr) / 12
    for m in range(1, 13):
        r = rows.get(m)
        if r is None:
            tip = f"Month {m}: no historical row"
        else:
            tip = (f"Month {m} (n = {r.n_obs:,})\np10 {_pc(r.q[0])} · p25 {_pc(r.q[1])}\n"
                   f"median {_pc(r.q[2])}\np75 {_pc(r.q[3])} · p90 {_pc(r.q[4])}")  # fmt: skip
            if r.mean is not None:
                tip += f"\nmean {_pc(r.mean)}"
            elif m == 12 and mean12 is not None:
                tip += f"\nmean {_pc(mean12)}"
        if m in by_m:
            a = by_m[m]
            tip += f"\n{code}: {_pc(a.excess)} vs {bands.label} on {a.day:%d %b %Y}" + (
                f" ({fc.percentile_text(fc.percentile_of(a.excess, r))})" if r else ""
            )
        hits.append(_hit(pl + (m - 0.5) * cw, cw, h - pb, tip))
    svg = (
        f'<svg viewBox="0 0 {w} {h}" class="chart fan" role="img" aria-label="Historical range '
        f'of excess return vs {e(bands.label)} for similar picks, months 1 to 12, with '
        f'{e(code)} actual">{grid}'
        f'<polygon points="{band(0, 4)}" class="fan1"/><polygon points="{band(1, 3)}" class="fan2"/>'
        f'<line x1="{pl}" x2="{w - pr}" y1="{yy(0):.1f}" y2="{yy(0):.1f}" class="base"/>'
        f'<path d="{med}" class="med"/>{mean_line}{actual}'
        + "".join(f'<text x="{xx(m):.1f}" y="{h - 6}" class="ax" text-anchor="middle">{m}</text>'
                  for m in (1, 3, 6, 9, 12))
        + "".join(hits) + "</svg>"
    )  # fmt: skip
    legend = (
        '<p class="legend"><span class="key fk1"></span>p10-p90 <span class="key fk2"></span>'
        'p25-p75 <span class="key k1"></span>median'
        + (
            ""
            if not mean_line
            else ' <span class="key km"></span>mean'
            + ("" if all(rows[m].mean is not None for m in months) else " (12 months)")
        )
        + f' <span class="key ka"></span>{e(code)} · months since bought</p>'
    )
    return _tipbox(svg, legend)


def _ticks(lo: float, hi: float) -> list[float]:
    span = hi - lo
    step = next((s for s in (0.05, 0.1, 0.2, 0.25, 0.5, 1.0) if span / s <= 5), 2.0)
    k = int(lo / step)
    out = []
    v = k * step
    while v <= hi:
        if v >= lo:
            out.append(round(v, 6))
        v += step
    return out


def rebased_chart(px: Series, idx: Series, entry: date, end: date, code: str,
                  label: str) -> str:  # fmt: skip
    p = [(d, v) for d, v in px if entry <= d <= end and v > 0]
    i = [(d, v) for d, v in idx if entry <= d <= end and v > 0]
    if len(p) < 2 or len(i) < 2:
        return ""
    p0, i0 = p[0][1], i[0][1]
    a = [(d, v / p0 * 100) for d, v in p]
    b = [(d, v / i0 * 100) for d, v in i]
    return _lines([(a, "s1", code), (b, "s2", label)], f"{code} and {label}, both 100 at entry",
                  "{:.0f}", base=100.0)  # fmt: skip


def _lines(series: Sequence[tuple[Series, str, str]], label: str, fmt: str,
           marks: Sequence[tuple[date, float, str]] = (), base: float | None = None,
           extra_tip: Callable[[date], str] | None = None) -> str:  # fmt: skip
    """A small multi-line chart with a tap read-out (up to 48 tap zones)."""
    allp = [pt_ for s, _, _ in series for pt_ in s]
    if len(allp) < 2:
        return ""
    w, h, pl, pr, pt, pb = 340, 160, 40, 10, 10, 22
    vals = [v for _, v in allp] + [v for _, v, _ in marks] + ([base] if base else [])
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.06 or 1.0
    lo, hi = lo - pad, hi + pad
    d0 = min(d for d, _ in allp)
    d1 = max(d for d, _ in allp)
    span = max((d1 - d0).days, 1)

    def xx(d: date) -> float:
        return pl + (d - d0).days / span * (w - pl - pr)

    def yy(v: float) -> float:
        return pt + (hi - v) / (hi - lo) * (h - pt - pb)

    paths = "".join(
        f'<path d="{_path([(xx(d), yy(v)) for d, v in s])}" class="{c}"/>'
        for s, c, _ in series
        if len(s) > 1
    )
    dots = "".join(f'<circle cx="{xx(d):.1f}" cy="{yy(v):.1f}" r="5" class="{c}"/>'
                   for d, v, c in marks)  # fmt: skip
    refl = (f'<line x1="{pl}" x2="{w - pr}" y1="{yy(base):.1f}" y2="{yy(base):.1f}" class="base"/>'
            if base else "")  # fmt: skip
    zones = min(48, max(len(s) for s, _, _ in series))
    cw = (w - pl - pr) / zones
    hits = []
    for k in range(zones):
        t = d0 + timedelta(days=round((k + 0.5) / zones * span))
        lines = [f"{t:%d %b %Y}"]
        for s, _, name in series:
            v = fc._at(s, t)
            if v is not None:
                lines.append(f"{name}: {fmt.format(v)}")
        if extra_tip:
            x = extra_tip(t)
            if x:
                lines.append(x)
        hits.append(_hit(pl + k * cw, cw, h - pb, "\n".join(lines)))
    svg = (
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{e(label)}">'
        f'<text x="{pl - 4}" y="{yy(hi) + 8:.1f}" class="ax" text-anchor="end">{fmt.format(hi)}</text>'
        f'<text x="{pl - 4}" y="{yy(lo):.1f}" class="ax" text-anchor="end">{fmt.format(lo)}</text>'
        f"{refl}{paths}{dots}"
        f'<text x="{pl}" y="{h - 5}" class="ax">{d0:%d %b %y}</text>'
        f'<text x="{w - pr}" y="{h - 5}" class="ax" text-anchor="end">{d1:%d %b %y}</text>'
        + "".join(hits) + "</svg>"
    )  # fmt: skip
    return _tipbox(svg)


# ---------------------------------------------------------------- the share's facts


@dataclass
class Facts:
    entry: date | None = None
    entry_price: float | None = None
    decision: date | None = None
    bucket: str | None = None
    exit_day: date | None = None
    exit_price: float | None = None
    exit_reason: str = ""
    realised: float | None = None
    hypothetical: bool = False


def facts(ctx: ShareCtx, info: Info, lists: Sequence[tuple[date, dict[str, Any]]],
          px: Series) -> Facts:  # fmt: skip
    j = ctx.journal
    out = Facts()
    buys = sorted(
        (f for f in info.fills if f.side is Side.BUY), key=lambda f: _aware(f.executed_at)
    )
    sells = sorted(
        (f for f in info.fills if f.side is Side.SELL), key=lambda f: _aware(f.executed_at)
    )
    if buys:
        out.entry = _aware(buys[0].executed_at).astimezone(ASX_TZ).date()
        out.entry_price = float(buys[0].price)
        if buys[0].client_order_id:
            try:
                out.decision = j.intent(buys[0].client_order_id)[0].decision_date
            except Exception:
                out.decision = None
    elif info.first_flag is not None:
        out.hypothetical = True
        out.decision = info.first_flag
        days = sorted(ctx.sessions) if ctx.sessions else [d for d, _ in px]
        out.entry = next((d for d in days if d > info.first_flag), None)
    if out.decision is None and buys and out.entry is not None:
        # no order intent (e.g. a fill from the broker's record): the last decision before it
        out.decision = max((d for d, _ in lists if d < out.entry), default=None)
    if out.decision is not None:
        for d, rec in lists:
            if d == out.decision:
                row = next((r for r in rec.get("band_c", []) if r[0] == info.code), None)
                out.bucket = fc.bucket_of(_f(row[4])) if row is not None else None
    if sells and not info.held:
        last = sells[-1]
        out.exit_day = _aware(last.executed_at).astimezone(ASX_TZ).date()
        q = sum(f.qty for f in sells)
        out.exit_price = sum(float(f.price) * f.qty for f in sells) / q if q else None
        bq = sum(f.qty for f in buys)
        buy_avg = sum(float(f.price) * f.qty for f in buys) / bq if bq else None
        if out.exit_price and buy_avg:
            out.realised = out.exit_price / buy_avg - 1
        if last.client_order_id:
            try:
                out.exit_reason = str(j.intent(last.client_order_id)[0].reason or "")
            except Exception:
                out.exit_reason = ""
    return out


def _price_series(ctx: ShareCtx, code: str) -> Series:
    from trader.app_pages import jobs

    if ctx.prices is not None:
        try:
            s = [(d, float(v)) for d, v in ctx.prices(code) if v and v > 0]
        except Exception:
            s = []
        if s:
            return s
    out = []
    for k, mk in jobs(ctx.journal, "marks:"):
        if code in mk:
            try:
                out.append((date.fromisoformat(k.split(":", 1)[1]), float(mk[code])))
            except ValueError:
                continue
    return sorted(out)


def _index_series(ctx: ShareCtx) -> Series:
    if ctx.index is None:
        return []
    try:
        return [(d, float(v)) for d, v in ctx.index() if v and v > 0]
    except Exception:
        return []


# ---------------------------------------------------------------- the sections


def bandc_index(j: Journal) -> Series:
    """BF-D72 (strategy review L1): the band C equal-weight index at month-ends, chained
    from the band-trend records (``bt:<day>``: the same index L15 uses); later records
    win for a step."""
    from trader.app_pages import jobs

    steps: dict[tuple[str, str], float] = {}
    for _, r in jobs(j, "bt:"):
        lv = r.get("levels") or []
        for a, b in pairwise(lv):
            try:
                if float(a[1]) > 0:
                    steps[(str(a[0]), str(b[0]))] = float(b[1]) / float(a[1])
            except (TypeError, ValueError, IndexError):
                continue
    out: Series = []
    for (a, b), s in sorted(steps.items()):
        if not out:
            out.append((date.fromisoformat(a), 1.0))
        if out[-1][0].isoformat() == a:
            out.append((date.fromisoformat(b), out[-1][1] * s))
    return out


def expected_section(ctx: ShareCtx, info: Info, f: Facts, px: Series, idx: Series) -> str:  # noqa: PLR0912, PLR0915 - one block per pane
    code = info.code
    trs: Series = []
    if ctx.tr is not None:  # L2: the actual line uses the share's total return
        try:
            trs = [(d, float(v)) for d, v in ctx.tr(code) if v and v > 0]
        except Exception:
            trs = []
    line = trs or px
    base = None if trs else f.entry_price  # a TR level's base is its entry-day level
    if f.entry is None:
        return section("Expected vs actual", "<p class='muted'>No buy or buy-list date yet, so "
                       "there is no starting point for the range.</p>")  # fmt: skip
    avail = {k: b for k, b in ctx.bands.items() if b is not None}
    if not avail:
        return section("Expected vs actual", "<p class='muted'>Not available yet: the forecast "
                       "bands file is not on this server (config/forecast_bands_a200.csv).</p>")  # fmt: skip
    if f.bucket is None:
        return section("Expected vs actual", "<p class='muted'>Not available: its score bucket at "
                       "the buy decision was not recorded (BF-D43 lists start with the app).</p>")  # fmt: skip
    end = f.exit_day or ctx.today
    bci = bandc_index(ctx.journal)

    def path_for(bench: Series) -> tuple[list[fc.Actual], tuple[int, float] | None]:
        assert f.entry is not None
        a = fc.actual_path(line, bench, f.entry, end, ctx.sessions, base)
        ep: tuple[int, float] | None = None
        if f.exit_day is not None:
            x = fc.excess_on(line, bench, f.entry, f.exit_day, base,
                             None if trs else f.exit_price)  # fmt: skip
            m = max(1, min(12, len(fc.month_ends(f.entry, f.exit_day, ctx.sessions, px)) or 1))
            if x is not None:
                ep = (m, x)
        return a, ep

    lead = (f"<p>Bought on <b>{f.entry:%d %b %Y}</b>" if not f.hypothetical else
            f"<p><b>Never bought.</b> The line shows what would have happened if it had been "
            f"bought on <b>{f.entry:%d %b %Y}</b>")  # fmt: skip
    lead += (f", when its score was in the <b>{e(fc.BUCKET_LABEL[f.bucket])}</b>"
             + (f" (decision {f.decision:%d %b %Y})" if f.decision else "") + ".</p>")  # fmt: skip
    order = [k for k in ("a200", "bandc") if k in avail]
    seg = "".join(
        f'<button type="button" class="chip{" on" if k == order[0] else ""}" data-bench="{k}" '
        f'aria-pressed="{"true" if k == order[0] else "false"}">vs {e(avail[k].label)}</button>'
        for k in order
    )
    panes = []
    for k in order:
        b = avail[k]
        assert b is not None
        rows = b.bucket(f.bucket)
        bench_note = ""
        if k == "bandc" and len(bci) > 1:  # L1: against band C itself
            act, exit_pt = path_for(bci)
        else:
            act, exit_pt = path_for(idx)
            if k == "bandc":
                bench_note = ("<p class='small muted'>The band C index is not recorded yet "
                              f"(it starts with the L15 records); the line is vs {e(ctx.index_label)}.</p>")  # fmt: skip
        track = ""
        if exit_pt and rows.get(exit_pt[0]):
            p = fc.percentile_of(exit_pt[1], rows[exit_pt[0]])
            track = (f"<p>At the sale it was <b>{_pc(exit_pt[1])}</b> vs {e(b.label)}: "
                     f"<b>{fc.percentile_text(p)}</b> of similar picks after {exit_pt[0]} "
                     f"month{'s' if exit_pt[0] != 1 else ''}.</p>")  # fmt: skip
        elif act and rows.get(act[-1].month):
            a = act[-1]
            p = fc.percentile_of(a.excess, rows[a.month])
            track = (f"<p class='lead2'>Tracking <b>{fc.percentile_text(p)}</b> of similar picks: "
                     f"<b>{_pc(a.excess)}</b> vs {e(b.label)} after {a.month} month"
                     f"{'s' if a.month != 1 else ''} ({a.day:%d %b %Y}).</p>")  # fmt: skip
        else:
            track = ("<p class='muted'>The first point is at the first month-end after it was "
                     "bought.</p>")  # fmt: skip
        n12 = rows.get(12) or (rows[max(rows)] if rows else None)
        about = (
            "<details class='about'><summary>About this chart</summary><p class='small'>"
            f"Benchmark: {e(b.label)}. Bucket: {e(fc.BUCKET_LABEL[f.bucket])}. "
            + (f"{n12.n_obs:,} past picks at {n12.month} months; " if n12 else "")
            + f"entries {e(b.period[0])} to {e(b.period[1])}; method {e(b.method)}. "
            "Excess return = the share's total return minus the benchmark's over the same days, "
            "no costs or tax. Past picks overlap in time, so the real sample is closer to the "
            "number of months. Most sample months before about 2015 had a thin band C (often "
            "under 150 names), so the early years weigh less than the count suggests.</p>"
            "<p class='small'><a href=\"/forecast-method\">How these ranges "
            "were made (the full note)</a></p></details>"
        )  # fmt: skip
        mean_note = ""
        if k != "bandc" and not any(r.mean is not None for r in rows.values()):
            bc = avail.get("bandc")
            m12 = bc.means_12m.get(f.bucket) if bc else None
            if m12 is not None:
                mean_note = (f"<p class='small muted'>This file has no mean; vs band C the average "
                             f"12-month result for this bucket was {_pc(m12)} (median "
                             f"{_pc(bc.bucket(f.bucket)[12].q[2]) if bc and 12 in bc.bucket(f.bucket) else '-'}).</p>")  # fmt: skip
        panes.append(
            f'<div data-bench-pane="{k}"{"" if k == order[0] else " hidden"}>'
            + track
            + bench_note
            + fan_chart(b, f.bucket, act, code, exit_pt)
            + f"<p class='small'><b>{NOT_PREDICTION}</b></p><p class='small'>{e(SKEW)}</p>"
            + mean_note
            + about
            + "</div>"
        )
    reb = rebased_chart(px, idx, f.entry, end, code, ctx.index_label)
    reb_s = (f"<h3 class='h3'>Price vs {e(ctx.index_label)}, both 100 at entry</h3>{reb}"
             '<p class="legend"><span class="key k1"></span>' + e(code)
             + f' <span class="key k2"></span>{e(ctx.index_label)}</p>') if reb else ""  # fmt: skip
    return section(
        "Expected vs actual",
        lead + (f'<div class="seg" role="group" aria-label="Benchmark" data-benchseg>{seg}</div>'
                if len(order) > 1 else "") + "".join(panes) + reb_s,
    )  # fmt: skip


def price_section(info: Info, f: Facts, px: Series) -> str:
    if f.entry is None or len(px) < 2:
        return ""
    start = f.entry - timedelta(days=365)
    s = [(d, v) for d, v in px if d >= start]
    hi = [(d, v) for d, v in fc.high_52w(px) if d >= start]
    marks = [
        (_aware(x.executed_at).astimezone(ASX_TZ).date(), float(x.price),
         "buyd" if x.side is Side.BUY else "selld")
        for x in info.fills
    ]  # fmt: skip
    if f.hypothetical:
        p = fc._from(px, f.entry)
        if p:
            marks.append((p[0], p[1], "hypd"))
    marks = [m for m in marks if s and m[0] >= s[0][0]]
    chart = _lines([(s, "s1", info.code), (hi, "hi52", "52-week high")],
                   f"{info.code} price from 12 months before entry, 52-week high dashed", "{:.3f}",
                   marks)  # fmt: skip
    if not chart:
        return ""
    return section("Price history", chart + (
        '<p class="legend"><span class="key k1"></span>price <span class="key khi"></span>52-week '
        'high <span class="key" style="background:var(--up)"></span>buy <span class="key" '
        'style="background:var(--down)"></span>sell'
        + (' <span class="key" style="background:var(--s3)"></span>would-be entry'
           if f.hypothetical else "") + " · from 12 months before entry</p>"))  # fmt: skip


def _nth_month_end(sessions: Sequence[date], after: date, n: int) -> date | None:
    ends = [a for a, b in pairwise(sorted(sessions)) if a > after and b.month != a.month]
    if len(ends) >= n:
        return ends[n - 1]
    # past the known calendar: the last weekday of the month n months on
    y, m = after.year, after.month + n
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    d = date(y + (m // 12), m % 12 + 1, 1) - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def next_section(ctx: ShareCtx, info: Info, f: Facts, lists: Sequence[tuple[date, dict[str, Any]]],
                 px: Series, idx: Series) -> str:  # fmt: skip
    items: list[str] = []
    latest = lists[-1] if lists else None
    row = None
    if latest:
        row = next((r for r in latest[1].get("band_c", []) if r[0] == info.code), None)
    pct = _f(row[4]) if row is not None else None
    if info.held:
        if f.decision:
            due = _nth_month_end(ctx.sessions, f.decision, 6)
            items.append(f"<li><b>Earliest C6 review:</b> the month-end decision of "
                         f"<b>{due:%d %b %Y}</b> (6 month-ends after {f.decision:%d %b %Y}).</li>"
                         if due else "")  # fmt: skip
        if latest:
            kz = pct is not None and pct > 0.60
            items.append(
                f"<li><b>Keep zone now:</b> {'in' if kz else 'not in'} the top 40% of band C "
                f"({latest[0]:%d %b %Y}"
                + (f", percentile {pct * 100:.0f}" if pct is not None else ", not in band C")
                + "). At the review it is kept while it stays in the top 40%; outside it, C6 "
                "sells it.</li>")  # fmt: skip
        pds = parcel_dates(ctx.journal, ctx.book, info.code, ctx.today)  # tax review: per parcel
        for acq, qty, cg in pds:
            left = (cg - ctx.today).days
            items.append("<li><b>Capital gains discount</b>"
                         + (f" (parcel of {qty:f} bought {acq:%d %b %Y})" if len(pds) > 1 else "")
                         + f": from <b>{cg:%d %b %Y}</b>"
                         + (" (applies now)" if left <= 0 else f" ({left} days)")
                         + "; estimate, not tax advice.</li>")  # fmt: skip
    elif f.exit_day is not None:
        from trader.app_more import reason_words

        why = reason_words(f.exit_reason) if f.exit_reason else "reason not recorded"
        items.append(f"<li><b>Sold</b> on {f.exit_day:%d %b %Y}: {e(why)}.</li>")
        if f.realised is not None:
            items.append(f"<li><b>Realised result:</b> {_pc(f.realised)} on the price (before "
                         "costs and tax).</li>")  # fmt: skip
        if f.entry:
            x = fc.excess_on(px, idx, f.entry, f.exit_day, f.entry_price, f.exit_price)
            bands = next((b for b in ctx.bands.values() if b is not None), None)
            m = max(1, min(12, len(fc.month_ends(f.entry, f.exit_day, ctx.sessions, px)) or 1))
            if x is not None and bands is not None and f.bucket:
                r = bands.bucket(f.bucket).get(m)
                if r:
                    items.append(f"<li><b>Against the range at the sale:</b> {_pc(x)} vs "
                                 f"{e(bands.label)}, {fc.percentile_text(fc.percentile_of(x, r))} "
                                 f"of similar picks after {m} month{'s' if m != 1 else ''}.</li>")  # fmt: skip
    else:
        items.append("<li>It is not held. It is looked at again at every month-end decision: "
                     "it can be bought only from the top 20% of band C (the buy list T) with a "
                     "free slot.</li>")  # fmt: skip
        if latest:
            items.append(f"<li><b>Latest decision ({latest[0]:%d %b %Y}):</b> "
                         + ("not in band C" if pct is None else f"percentile {pct * 100:.0f}"
                            + (" — in the top 20%" if pct > 0.80 else ""))
                         + ".</li>")  # fmt: skip
    body = "".join(i for i in items if i)
    return section("What happens next", f'<ul class="bul">{body}</ul>' if body else
                   "<p class='muted'>Nothing scheduled.</p>")  # fmt: skip


def parcel_dates(j: Journal, book: str, code: str, today: date
                 ) -> list[tuple[date, Any, date]]:  # fmt: skip
    """The open tax parcels of ``code``: (acquired, quantity, discount date), so a holding
    bought in parts shows each parcel's 12-month date (tax review)."""
    from decimal import Decimal

    from trader.tax_report import TaxParams, run_engine

    p = TaxParams(discount_rule="12_months")
    try:
        eng = run_engine(j, book, p, today)
    except Exception:
        return []
    return [(x.acquired, x.qty.normalize() if isinstance(x.qty, Decimal) else x.qty,
             p.eligible_from(x.acquired))
            for x in sorted(eng.open_of(code), key=lambda x: (x.acquired, x.pid))]  # fmt: skip


def detail_sections(ctx: ShareCtx, code: str, info: Info | None = None) -> str:
    """Rank history, expected vs actual, price history and what happens next."""
    lists = _lists(ctx.journal)
    if info is None:
        info = collect(ctx, ()).get(code) or Info(code, "passed")
    px = _price_series(ctx, code)
    idx = _index_series(ctx)
    f = facts(ctx, info, lists, px)
    return (
        section("Rank history", rank_chart(rank_rows(lists, code), code))
        + expected_section(ctx, info, f, px, idx)
        + price_section(info, f, px)
        + next_section(ctx, info, f, lists, px, idx)
    )


# ---------------------------------------------------------------- screens


def shares_list(ctx: ShareCtx, held: Sequence[str]) -> str:
    infos = collect(ctx, held)
    lists = _lists(ctx.journal)
    latest = lists[-1][1] if lists else {}
    lrow = {r[0]: r for r in latest.get("band_c", [])}
    order = {"holding": 0, "sold": 1, "proposed": 2, "passed": 3}
    counts = {k: sum(1 for i in infos.values() if i.status == k) for k in order}
    chips = '<button type="button" class="chip on" data-filter="all">All</button>' + "".join(
        f'<button type="button" class="chip" data-filter="{k}">{STATUS_LABEL[k]} '
        f"({counts[k]})</button>"
        for k in order
        if counts[k]
    )
    rows = []
    for info in sorted(infos.values(), key=lambda i: (order[i.status], i.code)):
        r = lrow.get(info.code)
        p = _f(r[4]) if r is not None else None
        sub = (f"rank {r[5]} · percentile {p * 100:.0f}" if r is not None and p is not None
               else "not in the latest band C")  # fmt: skip
        if info.first_flag:
            sub += f" · first flagged {info.first_flag:%b %Y}"
        rows.append(
            f'<li data-kind="{info.status}"><a class="rowlink" href="/shares/{quote(info.code)}" '
            f'data-nav data-sheet="1"><span class="grow"><b>{e(info.code)}</b> '
            f'<span class="pill st-{info.status}">{STATUS_LABEL[info.status]}</span>'
            f'<div class="sub">{e(sub)}</div></span>{chev()}'
            "</a></li>"
        )
    body = (
        f'<div class="seg" role="group" aria-label="Filter">{chips}</div>'
        + (f'<ul class="list">{"".join(rows)}</ul>' if rows else
           "<p class='muted'>No shares yet: the list fills from the first decision.</p>")
        + "<p class='small muted'>Every share the strategy held, sold, proposed (buy list T) or "
        "passed over (top 20% of band C, never bought). Tap one for its rank history and the "
        "historical range of similar picks.</p>"
    )  # fmt: skip
    return body


def share_detail(ctx: ShareCtx, code: str) -> str | None:
    infos = collect(ctx, ())
    info = infos.get(code)
    if info is None:
        return None
    return (
        backlink("/shares", "Shares") + f"<h1>{e(code)} "
        f'<span class="pill st-{info.status}">{STATUS_LABEL[info.status]}</span></h1>'
        + (f'<p class="coname">{e(ctx.names[code])}</p>' if code in ctx.names else "")
        + detail_sections(ctx, code, info)
    )


# ---------------------------------------------------------------- the method note


def md_to_html(text: str) -> str:
    """A small Markdown subset (headings, paragraphs, bullets, tables, bold, code) for
    docs/FORECAST_BANDS.md; everything is escaped first."""
    out: list[str] = []
    para: list[str] = []
    lst: list[str] = []
    tbl: list[list[str]] = []

    def inline(s: str) -> str:
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)

    def flush() -> None:
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if lst:
            out.append("<ul class='bul'>" + "".join(f"<li>{inline(x)}</li>" for x in lst) + "</ul>")
            lst.clear()
        if tbl:
            head, *rest = tbl
            out.append("<div class='tscroll'><table><thead><tr>"
                       + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                                 for r in rest) + "</tbody></table></div>")  # fmt: skip
            tbl.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("#"):
            flush()
            n = min(len(line) - len(line.lstrip("#")) + 1, 4)
            out.append(f"<h{n}>{inline(line.lstrip('#').strip())}</h{n}>")
        elif line.startswith("|"):
            if para or lst:
                flush()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                tbl.append(cells)
        elif line.startswith(("* ", "- ")):
            if para or tbl:
                flush()
            lst.append(line[2:].strip())
        elif line.startswith("  ") and lst:
            lst[-1] += " " + line.strip()
        elif not line.strip():
            flush()
        else:
            if tbl:
                flush()
            para.append(line.strip())
    flush()
    return "".join(out)


def method_page(config_dir: Path | None) -> str:
    doc = None if config_dir is None else Path(config_dir).parent / "docs" / "FORECAST_BANDS.md"
    try:
        text = doc.read_text(encoding="utf-8") if doc else ""
    except OSError:
        text = ""
    if not text:
        return "<h1>Forecast bands</h1><p class='muted'>The method note is not on this server.</p>"
    return (backlink("/shares", "Shares") + '<div class="doc">'
            + md_to_html(text) + "</div>")  # fmt: skip
