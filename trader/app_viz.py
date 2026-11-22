"""Small server-rendered visuals for the phone app (BF-D62): sparklines, rings, a gauge,
a threshold meter, a donut and the hero number. Pure SVG/HTML strings, no scripts; the
app's script only animates them (and does nothing when the viewer prefers reduced
motion). Gains and losses are never told by colour alone: every signed number carries
▲ / ▼ and + / −.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from decimal import Decimal

from trader.webui import e

MINUS = "−"


def arrow(x: float | Decimal | None) -> str:
    """▲ / ▼ in front of a gain / loss (colour-blind safe), nothing for zero / unknown."""
    if x is None or x == 0:
        return ""
    return "▲ " if x > 0 else "▼ "


def spark(values: Sequence[float], w: int = 96, h: int = 28, cls: str = "spk",
          label: str = "trend") -> str:  # fmt: skip
    """A tiny line with a soft area under it; the last point is a dot."""
    vs = [float(v) for v in values if math.isfinite(float(v))]
    if len(vs) < 2:
        return f'<svg class="{cls}" viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}"></svg>'
    lo, hi = min(vs), max(vs)
    span = (hi - lo) or 1.0
    pts = [(i / (len(vs) - 1) * (w - 4) + 2, h - 3 - (v - lo) / span * (h - 6))
           for i, v in enumerate(vs)]  # fmt: skip
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    area = f"{line} L{pts[-1][0]:.1f},{h} L{pts[0][0]:.1f},{h} Z"
    tone = "up" if vs[-1] >= vs[0] else "down"
    lx, ly = pts[-1]
    return (
        f'<svg class="{cls} {tone}" viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}">'
        f'<path class="spa" d="{area}"/><path class="spl" d="{line}"/>'
        f'<circle class="spd" cx="{lx:.1f}" cy="{ly:.1f}" r="2.2"/></svg>'
    )


def ring(frac: float, big: str, small: str, label: str, tone: str = "acc", size: int = 92
         ) -> str:  # fmt: skip
    """A progress ring (0..1) with a value in the middle."""
    f = max(0.0, min(1.0, frac))
    r = size / 2 - 7
    c = 2 * math.pi * r
    return (
        f'<figure class="ring {tone}" role="img" aria-label="{e(label)}">'
        f'<svg viewBox="0 0 {size} {size}"><circle class="rt" cx="{size / 2}" cy="{size / 2}" '
        f'r="{r:.1f}"/><circle class="rv" cx="{size / 2}" cy="{size / 2}" r="{r:.1f}" '
        f'stroke-dasharray="{c * f:.1f} {c:.1f}" data-dash="{c * f:.1f}" '
        f'transform="rotate(-90 {size / 2} {size / 2})"/></svg>'
        f"<figcaption><b>{e(big)}</b><span>{e(small)}</span></figcaption></figure>"
    )


def gauge(pct_: float | None, mark: float = 10.0, label: str = "percentile") -> str:
    """A half-circle gauge 0..100 with the L11 (b) line at ``mark``."""
    w, h, r, cx, cy = 200, 112, 84, 100, 100

    def pt(p: float) -> tuple[float, float]:
        a = math.pi * (1 - p / 100)
        return cx + r * math.cos(a), cy - r * math.sin(a)

    arc = f"M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy}"
    v = 0.0 if pct_ is None else max(0.0, min(100.0, pct_))
    x1, y1 = pt(v)
    big = 1 if v > 50 else 0
    val = f"M{cx - r},{cy} A{r},{r} 0 {big} 1 {x1:.1f},{y1:.1f}" if v > 0 else ""
    mx, my = pt(mark)
    tone = "bad" if pct_ is not None and pct_ < mark else "good"
    txt = "-" if pct_ is None else f"{pct_:.0f}"
    return (
        f'<svg class="gauge {tone}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{e(label)}: {txt} of 100">'
        f'<path class="gt" d="{arc}"/>'
        + (f'<path class="gv" d="{val}"/>' if val else "")
        + f'<circle class="gm" cx="{mx:.1f}" cy="{my:.1f}" r="4"/>'
        f'<text x="{cx}" y="{cy - 14}" class="gbig" text-anchor="middle">{e(txt)}</text>'
        f'<text x="{cx}" y="{cy + 8}" class="ax" text-anchor="middle">percentile · line at '
        f"{mark:.0f}</text></svg>"
    )


def threshold_meter(value: float | None, marks: Sequence[tuple[float, str]], hi: float,
                    label: str) -> str:  # fmt: skip
    """A horizontal bar 0..``hi`` with the value and labelled threshold ticks (L11)."""
    if value is None:
        return ""
    lo = min(m for m, _ in marks) * 0.8
    span = (hi - lo) or 1.0

    def x(v: float) -> float:
        return max(0.0, min(100.0, (v - lo) / span * 100))

    ticks = "".join(
        f'<i class="tk" style="left:{x(m):.1f}%"></i><span class="tl3" style="left:{x(m):.1f}%">'
        f"{e(t)}</span>"
        for m, t in marks
    )
    below = [t for m, t in marks if value < m]
    tone = "bad" if below else "good"
    return (
        f'<div class="tmeter {tone}" role="img" aria-label="{e(label)}">'
        f'<div class="tbar"><b style="width:{x(value):.1f}%"></b>{ticks}</div></div>'
    )


def donut(parts: Sequence[tuple[str, float]], centre: str, sub: str) -> str:
    """Allocation donut; each slice carries ``data-code`` for the tap-to-highlight script."""
    total = sum(v for _, v in parts) or 1.0
    r, c = 42.0, 2 * math.pi * 42.0
    off = 0.0
    segs = []
    for i, (code, v) in enumerate(parts):
        ln = v / total * c
        segs.append(
            f'<circle class="ds c{i % 8}" data-code="{e(code)}" cx="60" cy="60" r="{r}" '
            f'stroke-dasharray="{max(ln - 1.2, 0.1):.2f} {c:.2f}" stroke-dashoffset="{-off:.2f}" '
            f'transform="rotate(-90 60 60)"><title>{e(code)} {v / total * 100:.0f}%</title></circle>'
        )
        off += ln
    return (
        '<figure class="donut" role="img" aria-label="Allocation by holding">'
        f'<svg viewBox="0 0 120 120">{"".join(segs)}</svg>'
        f"<figcaption><b>{e(centre)}</b><span>{e(sub)}</span></figcaption></figure>"
    )


def hero(value: Decimal | None, label: str, change: str, change_tone: str, extra: str = "") -> str:
    """The big number first: value with a count-up (``data-countup``), the day's change."""
    if value is None:
        big = "-"
        data = ""
    else:
        q = Decimal(str(value)).quantize(Decimal("0.01"))
        big = f"A${q:,.2f}"
        data = f' data-countup="{q}"'
    return (
        f'<div class="hero"><div class="hl">{e(label)}</div>'
        f'<div class="hv num"{data}>{e(big)}</div>'
        f'<div class="hc {change_tone}">{change}</div>{extra}</div>'
    )
