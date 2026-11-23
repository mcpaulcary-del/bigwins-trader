"""The app's second interactive pass (BF-D68; presentation and read-only): the holdings
treemap, the what-if slider, the calendar, compare mode, the month replay and the global
search index. Every screen is a GET page built from what the app already reads; the
only things kept are client-side preferences (localStorage). Nothing here can trade.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import Any
from urllib.parse import quote

from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.orders import Side
from trader.webui import backlink, e, icon, section

REASON_WORDS = {
    "EMG2_OFF_LIST": "it was no longer on the buy list T",
    "EMG2_BID_PEG": "its price was stuck at the bid (the bid-peg rule)",
    "EMG2_C6_EXIT": "rule C6: held 6 or more month-ends and outside the top 40% of band C",
    "EMG2_NEW_ENTRY": "a new entry from the buy list T",
    "BT_OFF_SELL": "the trend shield moved the book to the A200 fund, so every share was sold",
    "BT_FUND_SELL": "the trend shield moved back to shares, so the fund was sold",
    "BT_FUND_BUY": "the trend shield moved the book into the A200 fund",
    "BT_FUND_SWEEP": "spare cash went into the A200 fund",
    "BT_LEFTOVER_SELL": "a leftover parcel was sold",
}


def reason_words(code: str) -> str:
    """A rule's reason code in plain words (the code itself when it is not known)."""
    return REASON_WORDS.get(str(code).strip(), str(code))


UP = "▲"
DOWN = "▼"


def _blob(data: object) -> str:
    return json.dumps(data, separators=(",", ":")).replace("</", "<\\/")


def _pc(x: float | None, dp: int = 1) -> str:
    if x is None:
        return "–"
    return f"{UP if x >= 0 else DOWN} {'+' if x >= 0 else '−'}{abs(x) * 100:.{dp}f}%"


# ---------------------------------------------------------------- treemap


def squarify(values: Sequence[float], x: float, y: float, w: float, h: float
             ) -> list[tuple[float, float, float, float]]:  # fmt: skip
    """Squarified treemap rectangles (Bruls et al.) for ``values`` (sorted large first)."""
    vals = [max(float(v), 0.0) for v in values]
    total = sum(vals)
    if total <= 0 or not vals:
        return [(x, y, 0.0, 0.0) for _ in vals]
    scale = w * h / total
    areas = [v * scale for v in vals]
    out: list[tuple[float, float, float, float]] = []

    def worst(row: list[float], side: float) -> float:
        s = sum(row)
        if s <= 0 or side <= 0:
            return math.inf
        return max(
            max(side * side * r / (s * s), (s * s) / (side * side * r)) for r in row if r > 0
        )

    i = 0
    while i < len(areas):
        side = min(w, h)
        row = [areas[i]]
        i += 1
        while i < len(areas) and worst([*row, areas[i]], side) <= worst(row, side):
            row.append(areas[i])
            i += 1
        s = sum(row)
        if w >= h:  # a column on the left
            cw = s / h if h else 0
            yy = y
            for r in row:
                rh = r / cw if cw else 0
                out.append((x, yy, cw, rh))
                yy += rh
            x, w = x + cw, w - cw
        else:  # a row on top
            rh = s / w if w else 0
            xx = x
            for r in row:
                rw = r / rh if rh else 0
                out.append((xx, y, rw, rh))
                xx += rw
            y, h = y + rh, h - rh
    return out


def _tone(g: float | None) -> str:
    """Colour step on the up / down ramp (BF-D73); losses are hatched and every label
    carries its sign, so colour is never the only signal."""
    if g is None or abs(g) < 0.005:
        return "tm0"
    k = 1 if abs(g) < 0.05 else (2 if abs(g) < 0.20 else 3)
    return f"tm{'u' if g > 0 else 'd'}{k}"


def treemap(holdings: Sequence[Any], hist: Mapping[str, Sequence[float]]) -> str:
    hs = sorted((h for h in holdings if (h.value or 0) > 0), key=lambda h: -float(h.value or 0))
    if not hs:
        return ""
    tw, th = 100.0, 62.0
    rects = squarify([float(h.value or 0) for h in hs], 0, 0, tw, th)
    tiles = []
    for h, (x, y, w, hh) in zip(hs, rects, strict=True):
        since = float(h.gain_pct) if h.gain_pct is not None else None
        pts = list(hist.get(h.code, []))
        today = pts[-1] / pts[-2] - 1 if len(pts) > 1 and pts[-2] else None
        small = w * hh < 70
        tiles.append(
            f'<a class="tm" href="/holdings/{quote(h.code)}" data-nav data-sheet="1" '
            f'style="left:{x:.3f}%;top:{y / th * 100:.3f}%;width:{w:.3f}%;height:{hh / th * 100:.3f}%" '
            f'data-cs="{_tone(since)}" data-ct="{_tone(today)}" data-ls="{e(_pc(since))}" '
            f'data-lt="{e(_pc(today))}" aria-label="{e(h.code)}: {e(_pc(since))} since bought, '
            f'{e(_pc(today))} today"><span class="tmi {_tone(since)}"><b>{e(h.code)}</b>'
            f'{"" if small else "<br>"}<span class="tml">{e(_pc(since))}</span></span></a>'
        )
    chips = ('<div class="chips" role="group" aria-label="Colour by" data-tmseg>'
             '<button type="button" class="chip on" data-tm="s" aria-pressed="true">Since bought'
             '</button><button type="button" class="chip" data-tm="t" aria-pressed="false">Today'
             "</button></div>")  # fmt: skip
    return (f'<div class="tmwrap">{chips}<div class="tmap" data-tmap>{"".join(tiles)}</div>'
            '<p class="legend">Size = value. Colour = gain: green up, hatched red down, darker = '
            "bigger. Tap a tile for the holding.</p></div>")  # fmt: skip


# ---------------------------------------------------------------- what-if


def beta_of(px: Sequence[float], ix: Sequence[float]) -> float | None:
    """Beta of daily returns (same days), at least 15 pairs; else None (the app uses 1.0)."""
    r1 = [b / a - 1 for a, b in pairwise(px) if a > 0]
    r2 = [b / a - 1 for a, b in pairwise(ix) if a > 0]
    n = min(len(r1), len(r2))
    if n < 15:
        return None
    r1, r2 = r1[-n:], r2[-n:]
    m1, m2 = sum(r1) / n, sum(r2) / n
    var = sum((b - m2) ** 2 for b in r2)
    if var <= 0:
        return None
    cov = sum((a - m1) * (b - m2) for a, b in zip(r1, r2, strict=True))
    return max(-1.0, min(3.0, cov / var))


def whatif(v: Any, j: Journal | None) -> str:
    """Market moves -20% .. +20%: the estimated account value against the L11 lines and
    the trend shield (an estimate: each holding moves by its recent beta x the move)."""
    if v.value is None or getattr(v, "limits", None) is None:
        return ""
    from trader.app_pages import jobs

    ix = dict(getattr(v, "index", []))
    marks: dict[str, list[tuple[date, float]]] = {}
    if j is not None:
        for k, mk in jobs(j, "marks:")[-70:]:
            try:
                d = date.fromisoformat(k.split(":", 1)[1])
            except ValueError:
                continue
            for c, p in mk.items():
                try:
                    marks.setdefault(c, []).append((d, float(p)))
                except (TypeError, ValueError):
                    continue
    rows = []
    for h in v.holdings:
        pts = [(d, p) for d, p in marks.get(h.code, []) if d in ix]
        b = beta_of([p for _, p in pts], [ix[d] for d, _ in pts]) if len(pts) > 15 else None
        rows.append([h.code, float(h.value or 0), round(b, 3) if b is not None else None])
    lim = v.limits
    tr = getattr(v, "trend", None) or {}
    lv = [float(z) for z in tr.get("levels", []) if isinstance(z, int | float)]
    mean = tr.get("mean")
    data = {
        "cash": float(v.cash or 0), "h": rows, "now": float(v.value),
        "lines": [[float(lim.review), "$7k check" if lim.review == 7000 else "check"],
                  [float(lim.halt), "pause"], [float(lim.line), "stop"]],
        "trend": [lv[-1], float(mean)] if lv and mean is not None else None,
    }  # fmt: skip
    known = sum(1 for r in rows if r[2] is not None)
    lo = float(lim.line) * 0.8
    hi = max(float(v.value) * 1.25, float(lim.review) * 1.1)

    def pos(x: float) -> float:
        return max(0.0, min(100.0, (x - lo) / (hi - lo) * 100))

    ticks = "".join(
        f'<span class="wk" style="left:{pos(x):.1f}%"></span>'
        f'<span class="wkl" style="left:{pos(x):.1f}%">${x / 1000:.0f}k</span>'
        for x in (float(lim.line), float(lim.halt), float(lim.review))
    )
    return section("What if the market moves?", (
        f'<div class="whatif" data-whatif data-lo="{lo:.0f}" data-hi="{hi:.0f}">'
        '<label class="wl" for="wi-r">Market move <b data-wi-m>0%</b></label>'
        '<input id="wi-r" type="range" min="-20" max="20" step="1" value="0" '
        'aria-label="Market move, per cent">'
        '<div class="wscale"><span>−20%</span><span>0</span><span>+20%</span></div>'
        f'<p class="wv">Estimated value <b class="num" data-wi-v>${float(v.value):,.0f}</b> '
        '<span class="sub" data-wi-d></span></p>'
        f'<div class="wbar" aria-hidden="true"><b data-wi-bar style="width:{pos(float(v.value)):.1f}%">'
        f"</b>{ticks}</div>"
        '<p data-wi-s class="small">Above the $7k check.</p><p data-wi-t class="small muted"></p>'
        f'<script type="application/json" data-wi-data>{_blob(data)}</script></div>'
        "<p class='small muted'><b>An estimate, not a forecast:</b> each holding moves by its "
        f"recent beta to {e(v.index_label)} × the market move ({known} of {len(rows)} with "
        "enough days; the rest use 1.0); cash stays the same. Real moves are not this tidy.</p>"
    ), "", "")  # fmt: skip


# ---------------------------------------------------------------- calendar


@dataclass(frozen=True)
class Ev:
    day: date
    kind: str  # decision | cutoff | exdiv | pay | c6 | cgt | eofy
    text: str
    href: str = ""


KIND_LABEL = {"decision": "Decision", "cutoff": "Approve by 15:20", "exdiv": "Ex-dividend",
              "pay": "Dividend paid", "c6": "C6 review", "cgt": "CGT discount", "eofy": "EOFY"}  # fmt: skip


def calendar_events(  # noqa: PLR0912 - one block per kind of date
    v: Any, j: Journal | None, sessions: Sequence[date], share: Any,
                    divs: Mapping[str, Sequence[tuple[date, date | None, float]]],
                    a: date, b: date) -> list[Ev]:  # fmt: skip
    ss = sorted(sessions)
    out: list[Ev] = []
    for s, nxt in pairwise(ss):
        if a <= s <= b and nxt.month != s.month:
            out.append(Ev(s, "decision", "Month-end decision, 22:20 Sydney", "/orders"))
        if a <= nxt <= b and nxt.month != s.month:
            out.append(Ev(nxt, "cutoff", "Approve the batch by 15:20 (orders go at the close "
                          "auction)", "/orders"))  # fmt: skip
    for y in range(a.year, b.year + 1):
        d = date(y, 6, 30)
        if a <= d <= b:
            out.append(Ev(d, "eofy", f"End of the financial year {y - 1}-{y % 100:02d}", "/tax"))
    for code, rows in divs.items():
        for ex, pay, amt in rows:
            if a <= ex <= b:
                out.append(Ev(ex, "exdiv", f"{code} ex-dividend ({amt:.3f} a share)",
                              f"/holdings/{quote(code)}"))  # fmt: skip
            if pay and a <= pay <= b:
                out.append(Ev(pay, "pay", f"{code} dividend paid", f"/holdings/{quote(code)}"))
    if share is not None and j is not None:
        from trader import share_pages

        infos = share_pages.collect(share, [h.code for h in v.holdings])
        lists = share_pages._lists(j)
        for h in v.holdings:
            info = infos.get(h.code)
            if info is None:
                continue
            f = share_pages.facts(share, info, lists, [])
            if f.decision:
                due = share_pages._nth_month_end(ss, f.decision, 6)
                if due and a <= due <= b:
                    out.append(Ev(due, "c6", f"{h.code}: earliest C6 review (6 month-ends held)",
                                  f"/holdings/{quote(h.code)}"))  # fmt: skip
            for acq, qty, cg in share_pages.parcel_dates(j, v.book, h.code, b):  # per parcel
                if a <= cg <= b:
                    out.append(Ev(cg, "cgt", f"{h.code}: 50% CGT discount from today for the "
                                  f"{qty:f} bought {acq:%d %b %Y} (estimate)",
                                  f"/holdings/{quote(h.code)}"))  # fmt: skip
    return sorted(out, key=lambda x: (x.day, x.kind))


def calendar(v: Any, month: date, events: Sequence[Ev], today: date) -> str:
    first = month.replace(day=1)
    nxt = (first + timedelta(days=32)).replace(day=1)
    prev = (first - timedelta(days=1)).replace(day=1)
    start = first - timedelta(days=first.weekday())
    by: dict[date, list[Ev]] = {}
    for x in events:
        by.setdefault(x.day, []).append(x)
    cells = []
    d = start
    while d < nxt or d.weekday() != 0:
        evs = by.get(d, [])
        dots = "".join(f'<i class="cd-{k}"></i>' for k in dict.fromkeys(x.kind for x in evs))
        cls = ("out " if d.month != first.month else "") + ("today " if d == today else "") \
            + ("has" if evs else "")  # fmt: skip
        lab = f"{d:%A %d %B}" + (f": {len(evs)} event(s)" if evs else "")
        cells.append(
            f'<button type="button" class="cday {cls}" data-cday="{d}" aria-label="{e(lab)}"'
            f"{' disabled' if d.month != first.month else ''}><span>{d.day}</span>"
            f'<span class="cdots">{dots}</span></button>'
        )
        d += timedelta(days=1)
    head = "".join(f"<span>{w}</span>" for w in ("M", "T", "W", "T", "F", "S", "S"))
    items = "".join(
        f'<li data-cev="{x.day}" class="cev-{x.kind}"><span class="cdk cd-{x.kind}"></span>'
        f'<span class="grow"><b>{x.day:%a %d %b}</b> · {e(KIND_LABEL[x.kind])}'
        f'<div class="sub">{e(x.text)}</div></span>'
        + (f'<a class="small" href="{e(x.href)}" data-nav>Open</a>' if x.href else "")
        + "</li>"
        for x in events
        if x.day.month == first.month
    )
    legend = "".join(f'<span class="cl"><i class="cd-{k}"></i>{e(lab)}</span>'
                     for k, lab in KIND_LABEL.items())  # fmt: skip
    nav = (f'<div class="calnav"><a class="iconbtn" href="/calendar?m={prev:%Y-%m}" data-nav '
           f'aria-label="Previous month">{icon("chevron-left")}</a><h2 class="calt">{first:%B %Y}</h2>'
           f'<a class="iconbtn" href="/calendar?m={nxt:%Y-%m}" data-nav aria-label="Next month">{icon("chevron-right")}'
           "</a></div>")  # fmt: skip
    return section("", (
        nav + f'<div class="cal" data-cal><div class="cwk">{head}</div><div class="cgrid">'
        + "".join(cells) + "</div></div>"
        + f'<div class="clegend">{legend}</div>'
        + '<p class="small muted" data-cal-hint>Tap a day for its details.</p>'
        + (f'<ul class="list cevs" data-cevs>{items}</ul>' if items else
           "<p class='muted'>Nothing this month.</p>")
    ), "wide")  # fmt: skip


def store_divs(root: Any, codes: Sequence[str]) -> dict[str, list[tuple[date, date | None, float]]]:
    """Ex-dividend and pay dates of ``codes`` from the price store (read-only)."""
    out: dict[str, list[tuple[date, date | None, float]]] = {}
    if root is None:
        return out
    try:
        from trader.data.forward_store import ForwardStore

        fs = ForwardStore(root)
    except Exception:
        return out
    for c in codes:
        try:
            rows = list(fs._events("div", f"{c}.AU"))
        except Exception:  # noqa: S112 - a share without dividend events
            continue
        for r in rows:
            try:
                ex = date.fromisoformat(str(r["date"])[:10])
                pd_ = r.get("paymentDate") or r.get("payment_date")
                pay = date.fromisoformat(str(pd_)[:10]) if pd_ else None
                out.setdefault(c, []).append((ex, pay, float(r.get("value") or 0)))
            except (KeyError, TypeError, ValueError):
                continue
    return out


# ---------------------------------------------------------------- compare


def compare(v: Any, share: Any, codes: Sequence[str]) -> str:
    from trader import share_pages

    start = v.now.astimezone(ASX_TZ).date() - timedelta(days=183)
    ser: dict[str, list[list[float]]] = {}
    for c in codes:
        px = share_pages._price_series(share, c)
        pts = [[(d - date(1970, 1, 1)).days, p] for d, p in px if d >= start]
        if len(pts) > 1:
            ser[c] = pts
    idx = [[(d - date(1970, 1, 1)).days, x] for d, x in share_pages._index_series(share)
           if start <= d <= v.now.astimezone(ASX_TZ).date()]  # fmt: skip
    if not ser:
        return section("Compare", "<p class='muted'>No price history yet.</p>")
    keys = list(ser)
    chips = "".join(
        f'<button type="button" class="chip{" on" if k < 2 else ""}" data-cmp="{e(c)}" '
        f'aria-pressed="{"true" if k < 2 else "false"}">{e(c)}</button>'
        for k, c in enumerate(keys)
    )
    if idx:
        chips += (f'<button type="button" class="chip on" data-cmp="__idx" aria-pressed="true">'
                  f"{e(v.index_label)}</button>")  # fmt: skip
    data = {"s": ser, "idx": idx, "label": v.index_label}
    return section("Compare", (
        "<p class='small muted'>Pick up to 3 holdings (and the index). Lines start at 100 on "
        "the first common day; drag across the chart to read each line.</p>"
        f'<div class="chips" role="group" aria-label="Lines to compare">{chips}</div>'
        '<div class="chartbox" data-compare><svg viewBox="0 0 340 200" class="chart" role="img" '
        'aria-label="Compare: rebased lines"></svg><div class="ctip cmpout" aria-live="polite">'
        "</div></div>"
        f'<script type="application/json" data-compare-data>{_blob(data)}</script>'
        '<p class="legend" data-compare-legend></p>'
    ), "wide")  # fmt: skip


# ---------------------------------------------------------------- month replay


def replay(v: Any, j: Journal, day: date) -> str | None:
    from trader import share_pages
    from trader.app_pages import _batches

    lists = dict(share_pages._lists(j))
    rec = lists.get(day)
    batches = [b for b in _batches(j, v.book) if b["decision_date"] == day]
    if rec is None and not batches:
        return None
    rec = rec or {}
    band = list(rec.get("band_c", []))
    n = len(band)
    targets = list(rec.get("targets", []))
    top = [r for r in band if (share_pages._f(r[4]) or 0) > 0.80]
    left = [r for r in top if r[0] not in targets]
    its = []
    for b in batches:
        its += [it for it, _ in j.intents_of(b["batch_id"])]
    rank = {r[0]: r for r in band}

    def bar(r: list[Any], cls: str = "") -> str:
        p = share_pages._f(r[4]) or 0
        return (f'<li class="rb {cls}"><span class="rbn">{e(r[0])}</span><span class="rbb">'
                f'<b style="width:{p * 100:.0f}%"></b></span><span class="rbv">#{e(r[5])}</span></li>')  # fmt: skip

    steps = []
    steps.append(("Band C ranked", (
        f"<p>Band C held <b>{n}</b> shares: ranks 301-600 by traded value, after leaving out "
        "LICs, funds and ETFs. Each got a score from momentum (s1) and two steadiness inputs "
        "(s2, s3), then a percentile (100 = best).</p>"
        f'<ul class="rbars">{"".join(bar(r) for r in band[:12])}</ul>'
        + (f"<p class='small muted'>And {n - 12} more.</p>" if n > 12 else "")
    )))  # fmt: skip
    steps.append(("Top fifth picked", (
        f"<p>The top 20% by score: <b>{len(top)}</b> shares. Only these can be bought "
        "(rule 3).</p>"
        f'<ul class="rbars">{"".join(bar(r, "pick") for r in top[:20])}</ul>'
    )))  # fmt: skip
    steps.append(("Filters", (
        f"<p>The buy step's filters (lottery, bid-peg, duplicate listing) left "
        f"<b>{len(targets)}</b> on the buy list T"
        + (f" and set aside <b>{len(left)}</b>: " + ", ".join(e(r[0]) for r in left[:15])
           if left else "; none were set aside") + ".</p>"
        "<p class='small muted'>LICs are already out before band C is ranked.</p>"
    )))  # fmt: skip
    words = []
    for it in its:
        r = rank.get(it.entity)
        where = (f"rank {e(r[5])} of {n}, percentile {(share_pages._f(r[4]) or 0) * 100:.0f}"
                 if r else "not in band C")  # fmt: skip
        if it.side is Side.BUY:
            why = (f"<b>Bought {e(it.entity)}</b>: {where}; on the buy list T and a slot was free "
                   f"({it.qty} shares, ≈ ${float(it.value_at_ref):,.0f}).")  # fmt: skip
        else:
            why = f"<b>Sold {e(it.entity)}</b>: {where}; {e(reason_words(it.reason))}."
        words.append(f'<li class="{"rbuy" if it.side is Side.BUY else "rsell"}">{why}</li>')
    steps.append(("Final orders", (
        f'<ul class="bul">{"".join(words)}</ul>' if words else
        "<p>No orders: the book already held enough of the list, or no slot was free.</p>"
    ) + (f'<p><a href="/orders/{quote(batches[0]["batch_id"])}" data-nav>The batch</a></p>'
         if batches else "")))  # fmt: skip
    dots = "".join(f'<button type="button" class="rdot{" on" if k == 0 else ""}" data-rgo="{k}" '
                   f'aria-label="Step {k + 1}: {e(t)}"></button>' for k, (t, _) in enumerate(steps))  # fmt: skip
    panes = "".join(
        f'<div class="rpane" data-rstep="{k}"><h3 class="h3">{k + 1}. {e(t)}</h3>{b}</div>'
        for k, (t, b) in enumerate(steps)
    )
    return (
        backlink("/orders", "Orders") + f"<h1>Replay: {day:%d %b %Y}</h1>"
        + section("", (
            f'<div class="replay" data-replay><div class="rdots">{dots}</div>{panes}'
            '<div class="btns rbtn"><button type="button" class="btn sec" data-rprev>Back</button>'
            '<button type="button" class="btn" data-rnext>Next</button></div>'
            '<button type="button" class="chip" data-rplay>▶ Play</button></div>'
        ), "wide")
        + "<p class='small muted'>From the decision's stored ranks and scores (the list "
        "recorded that night); nothing is recomputed.</p>"
    )  # fmt: skip


# ---------------------------------------------------------------- search


def search_index(v: Any, j: Journal | None, share: Any, x: Any, tax_rows: Sequence[Any]
                 ) -> list[dict[str, str]]:  # fmt: skip
    from trader import share_pages
    from trader.app_pages import _batches

    out: list[dict[str, str]] = []
    if share is not None and j is not None:
        for c, info in share_pages.collect(share, [h.code for h in v.holdings]).items():
            out.append({"g": "Shares", "t": c, "s": share_pages.STATUS_LABEL[info.status],
                        "u": f"/shares/{quote(c)}"})  # fmt: skip
    if j is not None:
        try:
            bl = _batches(j, v.book)[:60]
        except Exception:
            bl = []
        for b in bl:
            its = j.intents_of(b["batch_id"])
            ents = " ".join(f"{it.side.value} {it.entity}" for it, _ in its)
            out.append({"g": "Orders", "t": f"{b['decision_date']:%d %b %Y} · {len(its)} order(s)",
                        "s": ents[:160], "u": f"/orders/{quote(b['batch_id'])}"})  # fmt: skip
    for r in x.inbox[:150]:
        out.append({"g": "Inbox", "t": str(r.get("title", ""))[:120],
                    "s": f"{r['at']:%d %b %H:%M}", "u": f"/inbox#m{r['id']}"})  # fmt: skip
    for r in tax_rows[:200]:
        out.append({"g": "Tax", "t": f"{r.code} · {r.event} {r.disposed:%d %b %Y}",
                    "s": f"qty {r.qty} · gain {Decimal(r.proceeds) - Decimal(r.cost_base):,.2f}",
                    "u": f"/tax?fy={r.fy}"})  # fmt: skip
    return out


def month_milestone(v: Any) -> str:
    """A subtle chip when the book is ahead of the index this month (nothing else)."""
    s, ix = getattr(v, "series", []), getattr(v, "index", [])
    if len(s) < 2 or len(ix) < 2:
        return ""
    last = s[-1][0]
    ms = [(d, float(x)) for d, x in s if (d.year, d.month) == (last.year, last.month)]
    prev = [(d, float(x)) for d, x in s if d < last.replace(day=1)]
    base = prev[-1][1] if prev else (ms[0][1] if ms else None)
    ip = [x for d, x in ix if d < last.replace(day=1)]
    im = [x for d, x in ix if (d.year, d.month) == (last.year, last.month)]
    ibase = ip[-1] if ip else (im[0] if im else None)
    if not ms or not im or not base or not ibase:
        return ""
    if ms[-1][1] / base - 1 > im[-1] / ibase - 1:
        return '<span class="vs mile">Ahead of the index this month</span>'
    return ""
