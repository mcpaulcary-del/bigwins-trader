"""The phone app's screens (BF-D43): Home, Holdings (+ one holding, + Tax), Orders
(+ one batch), Inbox, Server and Settings. Server-rendered from what the trader records
(read-only); the bottom tab bar and ``webui.JS`` make them feel like an app (smooth tab
switching, refresh, chart interaction, unread badges) but every screen works without
JavaScript. Action buttons are plain links to the trader's confirm screens
(``/act/confirm?...``, BF-D39): a GET here never changes anything.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import pairwise
from typing import Any, TypeVar
from urllib.parse import quote, urlencode

from trader.app_store import SERVER_ACTIONS, get_state, inbox_rows, server_job_rows
from trader.approval import OPEN_FOR_APPROVAL, approved_seqs, deadline
from trader.constants import ASX_TZ
from trader.journal import FillRecord, Journal, Status, broker_orders, events
from trader.orders import Side
from trader.webui import e, page, section, tile

CENT = Decimal("0.01")
MINUS = "−"
EPOCH = date(1970, 1, 1)
T = TypeVar("T")

STATUS_WORDS = {
    Status.PLANNED: "proposed",
    Status.RISK_OK: "proposed (checks passed)",
    Status.HELD: "held (waiting for funds)",
    Status.APPROVED: "approved",
    Status.SENDING: "sending",
    Status.SENT: "sent",
    Status.PARTIAL: "part filled",
    Status.FILLED: "filled",
    Status.LAPSED: "lapsed (not approved)",
    Status.VETOED: "vetoed",
    Status.RISK_REJECTED: "stopped by a limit",
    Status.EXPIRED: "not filled (expired)",
    Status.CANCELLED: "cancelled",
    Status.REJECTED: "rejected by the broker",
    Status.NEEDS_REVIEW: "needs review",
}
BAD_END = frozenset({Status.EXPIRED, Status.CANCELLED, Status.REJECTED, Status.LAPSED,
                     Status.VETOED, Status.RISK_REJECTED, Status.NEEDS_REVIEW})  # fmt: skip
KIND_WORDS = {"page": "Alert", "approval": "Approval", "report": "Daily report",
              "info": "Info", "action": "Your action"}  # fmt: skip


def safe(fn: Callable[[], T], default: T) -> T:
    """A screen never fails because a table is missing (an older journal) or empty."""
    try:
        return fn()
    except Exception:
        return default


def aud(x: Decimal | float | None, sign: bool = False, dp: int = 2) -> str:
    if x is None:
        return "-"
    q = Decimal(str(x)).quantize(Decimal(1) if dp == 0 else CENT)
    s = f"{abs(q):,.{dp}f}"
    if sign:
        return ("+" if q >= 0 else MINUS) + "A$" + s
    return (MINUS if q < 0 else "") + "A$" + s


def pct(x: float | None, sign: bool = True) -> str:
    if x is None or not math.isfinite(x):
        return "-"
    s = f"{abs(x) * 100:.1f}%"
    return (("+" if x >= 0 else MINUS) + s) if sign else s


def tone(x: float | Decimal | None) -> str:
    if x is None:
        return ""
    return "up" if x > 0 else ("down" if x < 0 else "")


def when(t: datetime | None) -> str:
    return "-" if t is None else t.astimezone(ASX_TZ).strftime("%a %d %b %H:%M")


def ago(t: datetime | None, now: datetime) -> str:
    if t is None:
        return "never"
    s = (now - t).total_seconds()
    if s < 90:
        return "just now"
    if s < 5400:
        return f"{s / 60:.0f} min ago"
    if s < 2 * 86400:
        return f"{s / 3600:.0f} h ago"
    return f"{s / 86400:.0f} days ago"


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def jobs(j: Journal, prefix: str) -> list[tuple[str, dict[str, Any]]]:
    return safe(lambda: j.job_records(prefix), [])


# ---------------------------------------------------------------- extra data


@dataclass
class Waiting:
    batch_id: str
    n: int
    total: Decimal
    by: datetime


@dataclass
class Extras:
    """What the app shows beyond the dashboard's ``View``."""

    inbox: list[dict[str, Any]] = field(default_factory=list)
    waiting: list[Waiting] = field(default_factory=list)
    twin_hist: list[tuple[date, float]] = field(default_factory=list)
    twin_values: list[float] = field(default_factory=list)
    twin_sim: float | None = None
    heartbeat: tuple[dict[str, Any], datetime] | None = None
    host: tuple[dict[str, Any], datetime] | None = None
    server_jobs: list[dict[str, Any]] = field(default_factory=list)
    alerts: dict[str, Any] = field(default_factory=dict)
    lockout: datetime | None = None
    viewer: str = ""
    action_logins: frozenset[str] = frozenset()
    channel: str = "app"
    approval_deadline: str = "15:20"
    update: dict[str, Any] = field(default_factory=dict)  # BF-D45 update-available
    running: dict[str, Any] = field(default_factory=dict)  # BF-D45 strategy-running
    stamps: list[tuple[date, str, str]] = field(default_factory=list)  # (day, id, version)
    update_mode: str = "immediate"
    changelog: list[dict[str, Any]] = field(default_factory=list)
    pending_jobs: list[dict[str, Any]] = field(default_factory=list)

    @property
    def latest_inbox(self) -> int:
        return max((int(r["id"]) for r in self.inbox), default=0)

    @property
    def can_act(self) -> bool:
        return bool(self.action_logins) and self.viewer in self.action_logins


def waiting_batches(j: Journal, book: str, now: datetime, dl: str) -> list[Waiting]:
    out = []
    bl: list[tuple[str, date | None]] = safe(lambda: j.batches_of(book), [])
    for bid, xd in bl:
        b = j.batch(bid)
        if b is None or b["approval_mode"] == "auto" or xd is None:
            continue
        by = deadline(xd, dl)
        if now > by or any(a["action"] == "REFUSE" for a in j.approvals(bid)):
            continue
        ok = approved_seqs(j, bid)
        its = [it for it, st in j.intents_of(bid) if st in OPEN_FOR_APPROVAL and it.seq not in ok]
        if its:
            tot = sum((Decimal(str(it.value_at_ref)) for it in its), Decimal(0))
            out.append(Waiting(bid, len(its), tot, by))
    return out


def collect_extras(
    j: Journal,
    book: str,
    now: datetime,
    viewer: str = "",
    action_logins: frozenset[str] = frozenset(),
    channel: str = "app",
    approval_deadline: str = "15:20",
) -> Extras:
    x = Extras(viewer=viewer, action_logins=action_logins, channel=channel,
               approval_deadline=approval_deadline)  # fmt: skip
    x.inbox = safe(lambda: inbox_rows(j, 200), [])
    x.waiting = safe(lambda: waiting_batches(j, book, now, approval_deadline), [])
    for k, r in jobs(j, "rnd:"):
        if k == "rnd-origin" or "percentile" not in r:
            continue
        try:
            x.twin_hist.append((date.fromisoformat(k.split(":", 1)[1]), float(r["percentile"])))
        except (ValueError, TypeError):
            continue
        x.twin_values = [float(v) for v in r.get("values", [])]
        x.twin_sim = float(r["sim"]) if "sim" in r else None
    x.heartbeat = safe(lambda: get_state(j, "heartbeat"), None)
    x.host = safe(lambda: get_state(j, "host-status"), None)
    x.server_jobs = safe(lambda: server_job_rows(j, 10), [])
    al = safe(lambda: get_state(j, "alerts"), None)
    x.alerts = al[0] if al and isinstance(al[0], dict) else {}
    up = safe(lambda: get_state(j, "update-available"), None)
    x.update = dict(up[0]) if up and isinstance(up[0], dict) else {}
    rn = safe(lambda: get_state(j, "strategy-running"), None)
    x.running = dict(rn[0]) if rn and isinstance(rn[0], dict) else {}
    for k, r in jobs(j, "strategy:"):
        try:
            x.stamps.append((date.fromisoformat(k.split(":", 1)[1]), str(r.get("id", "?")),
                             str(r.get("version", "?"))))  # fmt: skip
        except ValueError:
            continue
    x.pending_jobs = [r for r in x.server_jobs if r["status"] in ("PENDING", "RUNNING")]
    lk = safe(lambda: get_state(j, "app-lockout"), None)
    if lk and isinstance(lk[0], dict) and lk[0].get("until"):
        until = datetime.fromisoformat(str(lk[0]["until"]))
        x.lockout = until if until > now else None
    return x


def act_link(**kw: str) -> str:
    return e("/act/confirm?" + urlencode({k: v for k, v in kw.items() if v}))


# ---------------------------------------------------------------- charts


def _epoch(d: date) -> int:
    return (d - EPOCH).days


def perf_chart(series: Sequence[tuple[date, Decimal]], index: Sequence[tuple[date, float]],
               label: str, note: str) -> str:  # fmt: skip
    """The interactive performance chart: a static SVG (all history) that the script
    redraws for 1M / 3M / 6M / All with a tap-and-drag read-out."""
    if len(series) < 2:
        return '<p class="muted">The chart starts after the second trading day.</p>'
    data = {
        "book": [[_epoch(d), float(v)] for d, v in series],
        "index": [[_epoch(d), float(v)] for d, v in index],
        "label": label,
    }
    w, h, pl, pr, pt, pb = 340, 190, 34, 8, 10, 22
    base = float(series[0][1])
    book = [(d, float(v) / base * 100) for d, v in series]
    idx = [(d, v / index[0][1] * 100) for d, v in index] if index else []
    allv = [y for _, y in book + idx]
    lo, hi = min(allv), max(allv)
    pad = max((hi - lo) * 0.1, 0.5)
    lo, hi = lo - pad, hi + pad
    d0, d1 = book[0][0], book[-1][0]
    span = max((d1 - d0).days, 1)

    def xx(d: date) -> float:
        return pl + (d - d0).days / span * (w - pl - pr)

    def yy(v: float) -> float:
        return pt + (hi - v) / (hi - lo) * (h - pt - pb)

    def path(pts: list[tuple[date, float]]) -> str:
        return " ".join(f"{'M' if i == 0 else 'L'}{xx(d):.1f},{yy(v):.1f}"
                        for i, (d, v) in enumerate(pts))  # fmt: skip

    grid = "".join(
        f'<line x1="{pl}" x2="{w - pr}" y1="{yy(v):.1f}" y2="{yy(v):.1f}" class="grid"/>'
        f'<text x="{pl - 4}" y="{yy(v) + 3:.1f}" class="ax" text-anchor="end">{v:.0f}</text>'
        for v in (lo + (hi - lo) * (k + 0.5) / 4 for k in range(4))
    )
    svg = (
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" '
        f'aria-label="Paper book vs {e(label)}, both 100 at the start">{grid}'
        f'<line x1="{pl}" x2="{w - pr}" y1="{yy(100):.1f}" y2="{yy(100):.1f}" class="base"/>'
        + (f'<path d="{path(idx)}" class="s2"/>' if idx else "")
        + f'<path d="{path(book)}" class="s1"/>'
        f'<circle cx="{xx(book[-1][0]):.1f}" cy="{yy(book[-1][1]):.1f}" r="4" class="d1"/>'
        f'<text x="{pl}" y="{h - 6}" class="ax">{d0:%d %b %y}</text>'
        f'<text x="{w - pr}" y="{h - 6}" class="ax" text-anchor="end">{d1:%d %b %y}</text></svg>'
    )
    ranges = "".join(
        f'<button type="button" data-range="{n}"{" class=on" if n == 0 else ""}>{lab}</button>'
        for lab, n in (("1M", 31), ("3M", 92), ("6M", 183), ("All", 0))
    )
    legend = '<span class="key k1"></span>Paper book'
    if idx:
        legend += f' <span class="key k2"></span>{e(label)} ({e(note)})'
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return (
        f'<div data-chart="perf-data"><div class="seg">{ranges}</div>{svg}</div>'
        f'<script type="application/json" id="perf-data">{blob}</script>'
        f'<p class="legend">{legend} · tap or drag the chart to read a day</p>'
    )


def drawdown(series: Sequence[tuple[date, Decimal]]) -> list[tuple[date, float]]:
    peak = 0.0
    out = []
    for d, v in series:
        peak = max(peak, float(v))
        out.append((d, float(v) / peak - 1 if peak else 0.0))
    return out


def dd_chart(dd: Sequence[tuple[date, float]]) -> str:
    if len(dd) < 2:
        return ""
    w, h, pl, pr, pt, pb = 340, 70, 34, 8, 6, 14
    lo = min(*(v for _, v in dd), -0.01)
    d0, d1 = dd[0][0], dd[-1][0]
    span = max((d1 - d0).days, 1)

    def xx(d: date) -> float:
        return pl + (d - d0).days / span * (w - pl - pr)

    def yy(v: float) -> float:
        return pt + (0 - v) / (0 - lo) * (h - pt - pb)

    pts = " ".join(f"{xx(d):.1f},{yy(v):.1f}" for d, v in dd)
    return (
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Drawdown from peak">'
        f'<polygon class="dd" points="{xx(d0):.1f},{yy(0):.1f} {pts} {xx(d1):.1f},{yy(0):.1f}"/>'
        f'<text x="{pl - 4}" y="{yy(0) + 3:.1f}" class="ax" text-anchor="end">0%</text>'
        f'<text x="{pl - 4}" y="{yy(lo) + 3:.1f}" class="ax" text-anchor="end">'
        f"{lo * 100:.0f}%</text></svg>"
    )


def line_chart(pts: Sequence[tuple[date, float]], cls: str = "s3", lo: float | None = None,
               hi: float | None = None, marks: Sequence[tuple[date, float, str]] = (),
               ref: float | None = None, fmt: str = "{:.0f}") -> str:  # fmt: skip
    if len(pts) < 2:
        return '<p class="muted small">Not enough days for a line yet.</p>'
    w, h, pl, pr, pt, pb = 340, 150, 40, 8, 10, 20
    vals = [v for _, v in pts] + [v for _, v, _ in marks]
    lo = min(vals) if lo is None else lo
    hi = max(vals) if hi is None else hi
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    d0, d1 = pts[0][0], pts[-1][0]
    span = max((d1 - d0).days, 1)

    def xx(d: date) -> float:
        return pl + (d - d0).days / span * (w - pl - pr)

    def yy(v: float) -> float:
        return pt + (hi - v) / (hi - lo) * (h - pt - pb)

    path = " ".join(f"{'M' if i == 0 else 'L'}{xx(d):.1f},{yy(v):.1f}"
                    for i, (d, v) in enumerate(pts))  # fmt: skip
    dots = "".join(
        f'<circle cx="{xx(d):.1f}" cy="{yy(v):.1f}" r="5" class="{c}"/>' for d, v, c in marks
    )
    refl = (
        f'<line x1="{pl}" x2="{w - pr}" y1="{yy(ref):.1f}" y2="{yy(ref):.1f}" class="base"/>'
        if ref is not None else ""
    )  # fmt: skip
    return (
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img">'
        f'<text x="{pl - 4}" y="{yy(hi) + 8:.1f}" class="ax" text-anchor="end">{fmt.format(hi)}</text>'
        f'<text x="{pl - 4}" y="{yy(lo):.1f}" class="ax" text-anchor="end">{fmt.format(lo)}</text>'
        f'{refl}<path d="{path}" class="{cls}"/>{dots}'
        f'<text x="{pl}" y="{h - 4}" class="ax">{d0:%d %b}</text>'
        f'<text x="{w - pr}" y="{h - 4}" class="ax" text-anchor="end">{d1:%d %b}</text></svg>'
    )


def histogram(values: Sequence[float], me: float | None) -> str:
    """The random twins' values with "you are here" (the simulated twin)."""
    if len(values) < 3:
        return ""
    lo, hi = min([*values, me or values[0]]), max([*values, me or values[0]])
    bins = 12
    width = (hi - lo) / bins or 1.0
    counts = [0] * bins
    for v in values:
        counts[min(int((v - lo) / width), bins - 1)] += 1
    mine = min(int(((me or lo) - lo) / width), bins - 1) if me is not None else -1
    w, h, pb = 340, 110, 18
    bw = (w - 8) / bins
    top = max(counts) or 1
    bars = "".join(
        f'<rect x="{4 + i * bw:.1f}" y="{(h - pb) - c / top * (h - pb - 14):.1f}" '
        f'width="{bw - 2:.1f}" height="{c / top * (h - pb - 14):.1f}" '
        f'class="bar{" me" if i == mine else ""}"/>'
        for i, c in enumerate(counts)
    )
    label = ""
    if me is not None:
        mx = 4 + (mine + 0.5) * bw
        label = f'<text x="{mx:.1f}" y="11" class="tip" text-anchor="middle">you are here</text>'
    return (
        f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Random twins">'
        f"{bars}{label}"
        f'<text x="4" y="{h - 4}" class="ax">{aud(lo, dp=0)}</text>'
        f'<text x="{w - 4}" y="{h - 4}" class="ax" text-anchor="end">{aud(hi, dp=0)}</text></svg>'
    )


# ---------------------------------------------------------------- shell


def shell(v: Any, x: Extras, title: str, body: str, active: str) -> str:
    sub = f"{v.book} · updated {when(v.now)}"
    notes = list(v.notes)
    if x.lockout is not None:
        notes.append(f"Code actions are locked until {x.lockout.astimezone(ASX_TZ):%H:%M} "
                     "(too many wrong codes).")  # fmt: skip
    return page(title, body, active, demo=v.demo, subtitle=sub, notes=notes,
                latest_inbox=x.latest_inbox, live=getattr(v, "live", False))  # fmt: skip


def actions_note(x: Extras, demo: bool) -> str:
    if demo:
        return '<p class="small muted">DEMO: buttons open simulated screens.</p>'
    if not x.action_logins:
        return ('<p class="note">Actions are off: no Tailscale log-in is allowed to act. On the '
                'server: <code>bigwins</code> › "Allow my phone to act".</p>')  # fmt: skip
    if not x.can_act:
        return (f'<p class="note">This log-in ({e(x.viewer or "none")}) may view but not act.'
                "</p>")  # fmt: skip
    return ""


def waiting_card(x: Extras, demo: bool) -> str:
    if not x.waiting:
        return ""
    out = []
    for w in x.waiting:
        out.append(
            f'<p class="summary">{w.n} order(s) waiting for your approval</p>'
            f'<p class="muted small">{e(w.batch_id)} · ≈ {aud(w.total, dp=0)} · by '
            f"{w.by:%a %d %b %H:%M}. Orders not approved are not sent.</p>"
            '<div class="btns">'
            f'<a class="btn" href="{act_link(a="ok", b=w.batch_id, n="all")}">✅ Approve all</a>'
            f'<a class="btn sec" href="{act_link(a="rf", b=w.batch_id)}">❌ Refuse</a></div>'
            f'<a href="/orders/{quote(w.batch_id)}" data-nav class="small">See each order ›</a>'
        )
    return section("Waiting for you", "".join(out) + actions_note(x, demo), "waitcard")


# ---------------------------------------------------------------- Home


def home(v: Any, x: Extras) -> str:
    if not v.started:
        nd = (f"<p>Next decision: <b>{v.next_decision:%A %d %B %Y}</b> (22:20).</p>"
              if v.next_decision else "")  # fmt: skip
        body = section(
            "Waiting for the first trading day",
            "<p>The trader has not made its first decision yet, so there is nothing to "
            "show. This page fills in by itself after the first trading evening "
            "(the daily report at 22:45 Sydney).</p>" + nd,
        )
        body += safety_card(v) + inbox_peek(x) + health_card(v, x)
        return shell(v, x, "Home", body, "home")
    val = v.value
    ct = v.change_today
    prev = v.series[-2][1] if len(v.series) > 1 else None
    ct_pct = float(ct / prev) if ct is not None and prev else None
    since = val - v.capital_in if val is not None and v.capital_in else None
    vs = (v.book_return - v.index_return
          if v.book_return is not None and v.index_return is not None else None)  # fmt: skip
    dd = drawdown(v.series)
    cur_dd = dd[-1][1] if dd else None
    max_dd = min((d for _, d in dd), default=None)
    tiles = (
        tile("Account value", aud(val), f"on {v.series[-1][0]:%d %b}" if v.series else "")
        + tile("Today", aud(ct, True), pct(ct_pct), tone(ct))
        + tile("Since start", aud(since, True), pct(v.since_start), tone(since))
        + tile(f"vs {v.index_label}", pct(vs) if vs is not None else "-",
               f"{v.index_label} {pct(v.index_return)}" if v.index_return is not None
               else "index line not available", tone(vs))
        + tile("From peak", pct(cur_dd), f"worst {pct(max_dd)}", tone(cur_dd))
        + tile("Cash", aud(v.cash), f"money in {aud(v.capital_in, dp=0)}")
    )  # fmt: skip
    body = waiting_card(x, v.demo)
    body += section("Performance", f'<div class="tiles">{tiles}</div>'
                    + perf_chart(v.series, v.index, v.index_label, v.index_note)
                    + '<p class="small muted">Drawdown from peak</p>' + dd_chart(dd))  # fmt: skip
    body += twins_card(v, x)
    nd = (f"Next decision <b>{v.next_decision:%a %d %b %Y}</b>, 22:20 Sydney"
          if v.next_decision else "Next decision: -")  # fmt: skip
    body += section("Next", f"<p>{nd}.</p>")
    body += safety_card(v) + inbox_peek(x)
    body += (
        '<div class="btns"><a class="btn sec" href="/act">⚙️ Controls</a>'
        '<a class="btn sec" href="/holdings" data-nav>📈 Holdings</a></div>'
        + (
            "<footer>LIVE account - real money. Not shown to beat the index.</footer>"
            if getattr(v, "live", False)
            else "<footer>PAPER - no real money. Not shown to beat the index.</footer>"
        )
    )
    return shell(v, x, "Home", body, "home")


def twins_card(v: Any, x: Extras) -> str:
    if v.twin_pct is None and not x.twin_hist:
        if v.sim_value is not None:
            return section("Twin", f"<p>Simulated twin value: <b>{aud(v.sim_value)}</b></p>")
        return ""
    warn = " ⚠ below 10" if v.twin_pct is not None and v.twin_pct < 10 else ""
    head = (
        f"<p>Twin vs {v.twin_n} random twins: <b>{v.twin_pct:.0f}th percentile</b>{warn}"
        f'<span class="sub"> · L11 test (b) needs ≥ 10 · {e(v.twin_day)}</span></p>'
        if v.twin_pct is not None else ""
    )  # fmt: skip
    hist = line_chart(x.twin_hist, "s3", 0, 100, ref=10) if len(x.twin_hist) > 1 else ""
    sim = (
        f"<p class='small muted'>Simulated twin value {aud(v.sim_value)}</p>" if v.sim_value else ""
    )
    return section(
        "Twin check (L13 / L11 b)",
        head + ('<p class="small muted">Percentile history</p>' + hist if hist else "")
        + ('<p class="small muted">The random twins today (the bar with "you are here" is the '
           "simulated twin)</p>" + histogram(x.twin_values, x.twin_sim) if x.twin_values else "")
        + sim,
    )  # fmt: skip


SAFETY_WORDS = {
    "NORMAL": "All normal",
    "PAUSED": "Paused: no new buys (sells go on)",
    "HALTED_BUYS": "Buys halted by a loss rule (sells go on)",
    "HALTED_LINE": "Halted: no new orders",
    "HALTED_INTEGRITY": "Halted: a check failed, no orders until re-armed",
    "KILLED": "Killed: no new orders",
}


def safety_card(v: Any) -> str:
    lvl = v.safety
    t = "ok" if lvl == "NORMAL" else ("bad" if lvl in ("KILLED", "HALTED_INTEGRITY") else "amber")
    items = [
        f'<li><span class="pill {t}">{e(lvl)}</span> {e(SAFETY_WORDS.get(lvl, lvl))}'
        + (f'<div class="sub">{e(v.safety_reason)} · {when(v.safety_at)}</div>'
           if v.safety_at else "") + "</li>"
    ]  # fmt: skip
    if v.started:
        items.append(f"<li>Loss rule (L11): <b>{e(v.l11_text or 'Normal')}</b></li>")
    tr = v.trend
    if tr:
        state = str(tr.get("state", "?"))
        what = "shares (EMG2-18)" if state == "EMG2" else "the A200 fund"
        forced = (f" - FORCED for the paper dry run (rule said {tr['forced_from']})"
                  if tr.get("forced_from") else "")  # fmt: skip
        items.append(f"<li>Trend shield (L15): <b>{e(state)}</b>, holding {what}{e(forced)}</li>")
    else:
        items.append("<li>Trend shield (L15): not decided yet</li>")
    return section("Safety", f'<ul class="list">{"".join(items)}</ul>'
                   '<a class="small" href="/act">Pause, Kill, Stop, Resume ›</a>')  # fmt: skip


def inbox_peek(x: Extras) -> str:
    rows = x.inbox[:3]
    if not rows:
        return ""
    items = "".join(
        f'<li class="msg {e(r["kind"])}" data-inbox-id="{int(r["id"])}"><a class="rowlink" '
        f'href="/inbox#m{int(r["id"])}" data-nav><span class="grow"><span class="t">'
        f'{e(r["title"])}</span><div class="sub">{when(r["at"])}</div></span>'
        '<span class="chev">›</span></a></li>'
        for r in rows
    )
    return section("Latest messages", f'<ul class="list">{items}</ul>')


# ---------------------------------------------------------------- Holdings


def holdings(v: Any, x: Extras, j: Journal | None) -> str:
    seg = ('<div class="seg"><a class="on" href="/holdings" data-nav>Holdings</a>'
           '<a href="/tax" data-nav>Tax</a></div>')  # fmt: skip
    if not v.holdings:
        body = seg + section("Holdings", '<p class="muted">No shares held (all cash).</p>')
        return shell(v, x, "Holdings", body, "holdings")
    total = sum((h.value or Decimal(0) for h in v.holdings), Decimal(0))
    gain = sum((h.gain or Decimal(0) for h in v.holdings), Decimal(0))
    rows = []
    for h in sorted(v.holdings, key=lambda h: -(h.value or 0)):
        flag = ' <span class="warn">⚠ old price</span>' if h.stale else ""
        mark = f"{h.mark}" if h.mark is not None else "no price"
        rows.append(
            f'<li><a class="rowlink" href="/holdings/{quote(h.code)}" data-nav>'
            f'<span class="grow"><b>{e(h.code)}</b>{flag}<div class="sub">{h.qty} @ {e(mark)}'
            + (f" ({e(h.mark_day)})" if h.stale and h.mark_day else "")
            + f" · {h.days_held if h.days_held is not None else '-'} days</div></span>"
            f'<span class="r">{aud(h.value)}<div class="sub {tone(h.gain)}">{aud(h.gain, True)} '
            f'{pct(h.gain_pct)}</div></span><span class="chev">›</span></a></li>'
        )
    stale = sum(1 for h in v.holdings if h.stale)
    note = (f'<p class="warn small">⚠ {stale} share(s) had no price on the last report day; '
            "valued at their last price.</p>" if stale else "")  # fmt: skip
    tiles = (tile("Shares", aud(total), f"{len(v.holdings)} holdings")
             + tile("Unrealised", aud(gain, True), "", tone(gain)))  # fmt: skip
    body = seg + section(
        f"Holdings ({len(v.holdings)})",
        f'<div class="tiles">{tiles}</div><ul class="list">{"".join(rows)}</ul>{note}',
    )
    return shell(v, x, "Holdings", body, "holdings")


def month_ends_between(sessions: Sequence[date], a: date, b: date) -> int:
    """BF-D35 age: month-end sessions after ``a`` up to and including ``b``."""
    ss = sorted(sessions)
    n = 0
    for s, nxt in pairwise(ss):
        if a < s <= b and nxt.month != s.month:
            n += 1
    return n


def holding_detail(  # noqa: PLR0912, PLR0915 - one block per part of the screen
    v: Any, x: Extras, j: Journal, code: str, sessions: Sequence[date]
) -> str | None:
    h = next((h for h in v.holdings if h.code == code), None)
    allf: list[FillRecord] = safe(lambda: j.fills(v.book), [])
    fills = [f for f in allf if f.entity == code]
    if h is None and not fills:
        return None
    buys = sorted((f for f in fills if f.side is Side.BUY), key=lambda f: _aware(f.executed_at))
    first = _aware(buys[0].executed_at).astimezone(ASX_TZ).date() if buys else None
    px: list[tuple[date, float]] = []
    for k, mk in jobs(j, "marks:"):
        if code in mk:
            try:
                d = date.fromisoformat(k.split(":", 1)[1])
            except ValueError:
                continue
            if first is None or d >= first:
                px.append((d, float(mk[code])))
    marks = [(_aware(f.executed_at).astimezone(ASX_TZ).date(), float(f.price),
              "buyd" if f.side is Side.BUY else "selld") for f in fills]  # fmt: skip
    if px:
        marks = [m for m in marks if m[0] >= px[0][0]]
    parts = [f'<p><a href="/holdings" data-nav>‹ Holdings</a></p><h1>{e(code)}</h1>']
    if h is not None:
        tiles = (
            tile("Value", aud(h.value), f"{h.qty} @ {h.mark}")
            + tile("Gain / loss", aud(h.gain, True), pct(h.gain_pct), tone(h.gain))
            + tile("Cost", aud(h.cost), "incl. brokerage")
            + tile("Held", f"{h.days_held if h.days_held is not None else '-'} days",
                   f"since {first:%d %b %Y}" if first else "")
        )  # fmt: skip
        parts.append(f'<div class="tiles">{tiles}</div>')
    buy_px = float(buys[0].price) if buys else None
    parts.append(section("Price since bought",
                         line_chart(px, "s1", marks=marks, ref=buy_px, fmt="{:.3f}")
                         + '<p class="legend"><span class="key" style="background:var(--up)">'
                         "</span>buy <span class=\"key\" style=\"background:var(--down)\"></span>"
                         "sell · dashed line: first buy price</p>"))  # fmt: skip
    # why it was chosen: the day's EMG2 list (rule 3 inputs) at its buy decision
    lists = jobs(j, "emg2list:")
    dec_day: date | None = None
    if buys and buys[0].client_order_id:
        try:
            dec_day = j.intent(buys[0].client_order_id)[0].decision_date
        except Exception:
            dec_day = None
    rec: dict[str, Any] | None = None
    for k, r in lists:
        if dec_day is not None and k.split(":", 1)[1] == str(dec_day):
            rec = r
    why = '<p class="muted">Not recorded (decided before the app kept the list, BF-D43).</p>'
    if rec is not None:
        row = next((r for r in rec.get("band_c", []) if r[0] == code), None)
        n = len(rec.get("band_c", []))
        if row is not None:
            on_t = code in rec.get("targets", [])

            def num(x: object) -> str:
                return "-" if x is None else f"{float(str(x)):.3f}"

            why = (
                f"<p>At the decision of <b>{e(dec_day)}</b> it ranked <b>{row[5]} of {n}</b> in "
                f"band C (score percentile {num(row[4])}){' and was on the list T' if on_t else ''}"
                ".</p><table><tbody>"
                f"<tr><td>s1 (momentum)</td><td class='r'>{num(row[1])}</td></tr>"
                f"<tr><td>s2</td><td class='r'>{num(row[2])}</td></tr>"
                f"<tr><td>s3</td><td class='r'>{num(row[3])}</td></tr></tbody></table>"
            )
        else:
            why = f"<p class='muted'>Not in band C of {e(dec_day)} (bought for another reason, e.g. the fund).</p>"
    parts.append(section("Why it was chosen", why))
    # sell rule C6: age >= 6 month-ends AND outside the keep zone (top 40% of band C)
    age = (
        month_ends_between(sessions, dec_day, v.now.astimezone(ASX_TZ).date()) if dec_day else None
    )
    latest = lists[-1][1] if lists else None
    kz: bool | None = None
    if latest is not None:
        r2 = next((r for r in latest.get("band_c", []) if r[0] == code), None)
        kz = r2 is not None and r2[4] is not None and float(r2[4]) > 0.60
    rule = (
        f"<p>Months held: <b>{age if age is not None else '-'}</b> of 6"
        + (" (old enough)" if age is not None and age >= 6 else "") + "</p>"
        '<div class="meter"><b style="width:'
        f'{min(100, (age or 0) / 6 * 100):.0f}%"></b></div>'
        + ("<p>In the top 40% of band C (keep zone): <b>"
           + ("yes" if kz else "no") + f"</b> ({e(latest.get('as_of', ''))})</p>"
           if latest is not None else "<p class='muted'>Keep zone: not recorded yet.</p>")
        + "<p class='small muted'>C6 sells only when both: 6 or more month-ends held and "
        "outside the keep zone.</p>"
    )  # fmt: skip
    parts.append(section("Sell rule (C6)", rule))
    return shell(v, x, code, "".join(parts), "holdings")


# ---------------------------------------------------------------- Orders


def _batches(j: Journal, book: str) -> list[dict[str, Any]]:
    out = []
    bl: list[tuple[str, date | None]] = safe(lambda: j.batches_of(book), [])
    for bid, _ in bl:
        b = j.batch(bid)
        if b is not None:
            out.append(b)
    return sorted(out, key=lambda b: (b["decision_date"], b["batch_id"]), reverse=True)


def orders(v: Any, x: Extras, j: Journal) -> str:
    body = waiting_card(x, v.demo)
    nd = (f"<p>Next decision: <b>{v.next_decision:%A %d %B %Y}</b>, 22:20 Sydney (orders go "
          "the next trading day, after your approval by 15:20).</p>" if v.next_decision else "")  # fmt: skip
    ver = {d: lab for d, _, lab in x.stamps}
    groups: dict[date, list[dict[str, Any]]] = {}
    for b in _batches(j, v.book):
        groups.setdefault(b["decision_date"], []).append(b)
    items = []
    for d, bs in groups.items():
        for b in bs:
            its = j.intents_of(b["batch_id"])
            counts: dict[str, int] = {}
            for _, st in its:
                w = STATUS_WORDS.get(st, st.lower())
                counts[w] = counts.get(w, 0) + 1
            summ = ", ".join(f"{n} {w}" for w, n in sorted(counts.items()))
            items.append(
                f'<li><a class="rowlink" href="/orders/{quote(b["batch_id"])}" data-nav>'
                f'<span class="grow"><b>{d:%d %b %Y}</b> · {len(its)} order(s)'
                f'<div class="sub">{e(b["batch_id"])}</div><div class="sub">{e(summ)}</div>'
                + (f'<div class="sub">strategy {e(ver[d])}</div>' if d in ver else "")
                + '</span><span class="chev">›</span></a></li>'
            )
    hist = (
        f'<ul class="list">{"".join(items)}</ul>'
        if items
        else '<p class="muted">No orders yet.</p>'
    )
    body += section("Decisions", nd + hist)
    return shell(v, x, "Orders", body, "orders")


def _timeline(j: Journal, coid: str, it: Any, st: str) -> str:
    rows: list[tuple[datetime, str, str]] = []
    with j.engine.connect() as c:
        from sqlalchemy import select

        q = (
            select(events.c.at, events.c.to_status)
            .where(events.c.kind == "intent", events.c.ref == coid)
            .order_by(events.c.id)
        )
        for at, to in c.execute(q):
            rows.append((_aware(at), STATUS_WORDS.get(str(to), str(to).lower()),
                         "badst" if to in BAD_END else "done"))  # fmt: skip
        bo = c.execute(select(broker_orders).where(broker_orders.c.client_order_id == coid)).first()
    fl: list[FillRecord] = safe(lambda: j.fills(coid=coid), [])
    for f in fl:
        rows.append((_aware(f.executed_at), f"filled {f.qty} @ {f.price} (brokerage A${f.commission})",
                     "done"))  # fmt: skip
    rows.sort(key=lambda r: r[0])
    li = "".join(
        f'<li class="{c}">{e(w)} <span class="sub">{when(t)}</span></li>' for t, w, c in rows
    )
    extra = (
        f'<div class="sub">broker order {e(bo.broker_order_id)}</div>'
        if bo is not None and bo.broker_order_id
        else ""
    )
    return f'<ul class="tl2">{li}</ul>{extra}'


def batch_detail(v: Any, x: Extras, j: Journal, batch_id: str) -> str | None:
    b = safe(lambda: j.batch(batch_id), None)
    if b is None:
        return None
    its = j.intents_of(batch_id)
    ok = approved_seqs(j, batch_id)
    w = next((w for w in x.waiting if w.batch_id == batch_id), None)
    apps = j.approvals(batch_id)
    who = "".join(
        f"<li>{e(a['action'])} {'all' if a['seq'] is None else a['seq']} · "
        f"{e(str(a['actor']).split(':')[0])} · {when(_aware(a['at']))}</li>"
        for a in apps
    )
    head = (
        f'<p><a href="/orders" data-nav>‹ Orders</a></p><h1>{b["decision_date"]:%d %b %Y}</h1>'
        f'<p class="muted small">{e(batch_id)} · {e(b["approval_mode"])} · execution '
        f"{b['execution_date'] or '-'}</p>"
    )
    top = ""
    if w is not None:
        top = section("Waiting for you", (
            f'<p class="summary">{w.n} order(s) · ≈ {aud(w.total, dp=0)}</p>'
            '<div class="btns">'
            f'<a class="btn" href="{act_link(a="ok", b=batch_id, n="all")}">✅ Approve all</a>'
            f'<a class="btn sec" href="{act_link(a="rf", b=batch_id)}">❌ Refuse</a></div>'
            f'<p class="small muted">Deadline {w.by:%a %d %b %H:%M}.</p>' + actions_note(x, v.demo)))  # fmt: skip
    cards = []
    for it, st in its:
        waiting = w is not None and st in OPEN_FOR_APPROVAL and it.seq not in ok
        word = ("approved" if st in OPEN_FOR_APPROVAL and it.seq in ok
                else STATUS_WORDS.get(st, st.lower()))  # fmt: skip
        btn = ""
        if waiting:
            btn = (f'<div class="btns"><a class="btn sec" href="{act_link(a="ok", b=batch_id, n=str(it.seq))}">'
                   f"Approve {it.seq}</a>"
                   + (f'<a class="btn sec" href="{act_link(a="veto", b=batch_id, n=str(it.seq))}">Veto</a>'
                      if it.side is Side.BUY else "") + "</div>")  # fmt: skip
        cards.append(
            f"<li><b class='{'buy' if it.side is Side.BUY else 'sell'}'>{it.seq}. "
            f"{e(it.side.value)}</b> <b>{it.qty} {e(it.entity)}</b> "
            f'<span class="pill {"amber" if waiting else "ok" if st == Status.FILLED else ""}">{e(word)}</span>'
            f'<div class="sub">{e(it.order_type.value)} limit {it.limit_price} (ref {it.ref_price}, '
            f"≈ {aud(Decimal(str(it.value_at_ref)), dp=0)}) · {e(it.reason)}</div>"
            + _timeline(j, it.client_order_id, it, st)
            + btn
            + "</li>"
        )
    body = head + top + section("Orders", f'<ul class="list">{"".join(cards)}</ul>')
    if who:
        body += section("Approvals", f'<ul class="list small">{who}</ul>')
    return shell(v, x, "Batch", body, "orders")


# ---------------------------------------------------------------- Inbox

FILTERS = (("all", "All"), ("alerts", "Alerts"), ("approval", "Approvals"),
           ("report", "Reports"), ("action", "My actions"))  # fmt: skip


def inbox(v: Any, x: Extras, kind: str = "all") -> str:
    chips = "".join(
        f'<a class="chip{" on" if k == kind else ""}" href="/inbox?kind={k}" data-filter="{k}">'
        f"{e(lab)}</a>"
        for k, lab in FILTERS
    )
    rows = []
    for r in x.inbox:
        k = str(r["kind"])
        hide = kind != "all" and not (k == kind or (kind == "alerts" and k == "page"))
        link = str(r["link"] or "")
        go = (f' <a href="{e(link)}"{" data-nav" if not link.startswith("/act") else ""}>Open ›</a>'
              if link and link != "/inbox" else "")  # fmt: skip
        rows.append(
            f'<li class="msg {e(k)}" id="m{int(r["id"])}" data-inbox-id="{int(r["id"])}" '
            f'data-kind="{e(k)}"{" hidden" if hide else ""}>'
            f'<span class="pill {"bad" if k == "page" else "amber" if k == "approval" else ""}">'
            f'{e(KIND_WORDS.get(k, k))}</span> <span class="t">{e(r["title"])}</span>'
            f'<div class="sub">{when(r["at"])} · {e(r["source"])}'
            + (f" · push {e(r['push'])}" if r["push"] and r["push"] != "off" else "")
            + f"{go}</div>"
            f"<details><summary class='small'>Show message</summary><pre>{e(r['body'])}</pre>"
            "</details></li>"
        )
    body = (f'<div class="seg">{chips}</div>'
            + section(f"Inbox ({len(x.inbox)})", f'<ul class="list">{"".join(rows)}</ul>' if rows
                      else '<p class="muted">No messages yet. Daily reports, approval requests '
                      "and alerts appear here (and as phone alerts once you turn them on).</p>")
            + '<p class="small"><a href="/act/alerts">🔔 Alerts on this phone ›</a></p>')  # fmt: skip
    return shell(v, x, "Inbox", body, "inbox")


# ---------------------------------------------------------------- Server


def health_card(v: Any, x: Extras) -> str:
    items = []
    items.append("<li>Price store: " + (f"<b>{v.store_day:%a %d %b}</b>" if v.store_day else "<b>-</b>")
                 + (f" · refreshed {when(v.store_refreshed_at)}" if v.store_refreshed_at else "")
                 + "</li>")  # fmt: skip
    items.append(f"<li>Last daily report: <b>{when(v.report_at)}</b></li>")
    if v.recon:
        ok = "reconciled to the cent" if v.recon[1] else "BREAK - see Inbox"
        items.append(f"<li>Broker check {e(v.recon[0])}: <b>{ok}</b></li>")
    if v.last_job:
        key, at, err = v.last_job
        items.append(f"<li>Last scheduled job: <b>{e(key.rsplit(':', 1)[1])}</b> {when(at)}"
                     + (f' <span class="warn">failed: {e(str(err)[:80])}</span>' if err else "")
                     + "</li>")  # fmt: skip
    if v.job_errors:
        items.append(f'<li class="warn">{v.job_errors} job error(s) in the last 7 days</li>')
    if x.heartbeat is None:
        items.append("<li>Heartbeat: <b>no ping yet</b> (off if healthchecks_url is none)</li>")
    else:
        hb, at = x.heartbeat
        good = bool(hb.get("ok"))
        items.append(f"<li>Heartbeat: <span class='pill {'ok' if good else 'bad'}'>"
                     f"{'OK' if good else 'FAILED'}</span> {ago(at, v.now)}"
                     + (f" ({e(hb.get('error', ''))})" if not good else "") + "</li>")  # fmt: skip
    if v.disk_free:
        free, total = v.disk_free
        items.append(f"<li{' class=warn' if free < 0.1 * total else ''}>Disk free: "
                     f"<b>{free / 1e9:.1f} GB</b> of {total / 1e9:.1f} GB</li>")  # fmt: skip
    return section("Trader health", f'<ul class="list">{"".join(items)}</ul>')


def server(v: Any, x: Extras) -> str:
    parts = ["<h1>Server</h1>"]
    if x.host is None:
        parts.append(section("Server", (
            "<p class='muted'>No status from the server yet. The host worker sends it every "
            "minute once installed: on the server run <code>bigwins install-worker</code>.</p>")))  # fmt: skip
    else:
        hs, at = x.host
        stale = (v.now - at).total_seconds() > 300

        def meter(label: str, p: float | None) -> str:
            if p is None:
                return ""
            return (f"<li>{e(label)} <b>{p:.0f}%</b><div class='meter'><b style='width:"
                    f"{min(100.0, p):.0f}%'></b></div></li>")  # fmt: skip

        up = hs.get("uptime_s")
        cpus = hs.get("cpus") or 1
        load = hs.get("load1")
        items = [
            meter("CPU (1-min load)", None if load is None else float(load) / float(cpus) * 100),
            meter("Memory used", hs.get("mem_used_pct")),
            meter("Disk used", hs.get("disk_used_pct")),
            f"<li>Up <b>{float(up) / 86400:.1f} days</b></li>" if up is not None else "",
            f"<li>Tailscale: <b>{e(hs.get('tailscale', '-'))}</b></li>",
            f"<li>Code version: <b>{e(hs.get('code_version', '-'))}</b></li>",
            f"<li>ASX: {e(hs.get('asx', '-'))}</li>",
        ]
        cont = "".join(
            f"<li>{e(c['name'])}: <span class='pill {'ok' if 'Up' in c['state'] or 'running' in c['state'] else 'bad'}'>"
            f"{e(c['state'])}</span></li>"
            for c in hs.get("containers", [])
        )
        parts.append(section(
            "Machine", (f'<p class="note">Status is {ago(at, v.now)} old: is the worker running?</p>'
                        if stale else f'<p class="small muted">Status {ago(at, v.now)}</p>')
            + f'<ul class="list">{"".join(items)}</ul>'))  # fmt: skip
        if cont:
            parts.append(section("Containers", f'<ul class="list">{cont}</ul>'))
        if hs.get("log"):
            parts.append(section("Trader log (last lines, cleaned)",
                                 f'<div class="logs">{e(chr(10).join(hs["log"]))}</div>'))  # fmt: skip
    parts.append(health_card(v, x))
    btns = "".join(
        f'<a class="btn sec wide" style="margin:4px 0" href="{act_link(a="srv:" + k)}">{e(lab)}…</a>'
        for k, lab in SERVER_ACTIONS.items()
    )
    btns += f'<a class="btn sec wide" style="margin:4px 0" href="{act_link(a="refresh")}">Refresh prices now…</a>'
    parts.append(section("Run the server", btns + "<p class='small muted'>Each asks for your "
                         "6-digit code; restart and update are refused while the ASX is open "
                         "unless you tick “Do it anyway”.</p>" + actions_note(x, v.demo)))  # fmt: skip
    if x.server_jobs:
        rows = "".join(
            f"<li><b>{e(r['action'])}</b> <span class='pill {'ok' if r['status'] == 'DONE' else 'amber' if r['status'] in ('PENDING', 'RUNNING') else 'bad'}'>"
            f"{e(r['status'])}</span><div class='sub'>{when(r['requested_at'])} · "
            f"{e(str(r['result']).strip().splitlines()[-1] if str(r['result']).strip() else '')}</div>"
            + (
                f' <a class="small" href="{act_link(a="cancel", job=str(r["id"]))}">Cancel…</a>'
                if r["status"] == "PENDING"
                else ""
            )
            + "</li>"
            for r in x.server_jobs
        )
        parts.append(section("Server jobs", f'<ul class="list">{rows}</ul>'))
    parts.append(strategy_card(x))
    parts.append(section("Ask Claude about the server", (
        "<p class='small'>Claude Code runs on the server in the tmux session <code>remote</code> "
        "(<code>claude remote-control</code>); you talk to it in the official Claude app, signed "
        "in with your Claude account. This app never runs Claude or any command itself.</p>"
        '<div class="btns">'
        f'<a class="btn sec" href="{act_link(a="srv:claude_remote")}">Start / check…</a>'
        f'<a class="btn sec" href="{act_link(a="srv:claude_stop")}">Stop…</a></div>'
        '<a class="btn wide" href="https://claude.ai/code" target="_blank" rel="noopener noreferrer">'
        "Open Claude ↗</a><p class='small muted'>First time only: sign in once on the server "
        "(Termius: <code>tmux attach -t remote</code>).</p>")))  # fmt: skip
    parts.append('<a class="btn sec wide" href="/act">⚙️ Trader controls (pause, kill…)</a>')
    return shell(v, x, "Server", "".join(parts), "server")


def strategy_card(x: Extras) -> str:
    u = x.update
    run = x.running
    head = (f"<p>Running: <b>{e(run.get('version', '-'))}</b> <span class='sub'>({e(run.get('id', '?'))})"
            f"</span></p>") if run else "<p class='muted'>Running version: recorded when the trader starts.</p>"  # fmt: skip
    card = ""
    if int(u.get("ahead") or 0) > 0:
        strat = bool(u.get("strategy", True))
        card = (f'<p class="note"><b>{"Strategy update" if strat else "App-only update"} available</b>'
                f" · {int(u['ahead'])} commit(s)" + (f" · {e(u['notes'].get('version', ''))}"
                if u.get("notes") else "") + "</p>")  # fmt: skip
    return section("Strategy", head + card + '<a class="btn sec wide" href="/strategy" data-nav>'
                   "Strategy, updates and versions ›</a>")  # fmt: skip


def version_perf(v: Any, x: Extras) -> list[tuple[str, date, date, float | None, float | None]]:
    """(version, from, to, book return, index return) per run of one strategy version."""
    from trader.strategy_version import segments

    segs = segments(x.stamps)
    if not segs or len(v.series) < 2:
        return []
    out = []
    for i, (d0, _vid, label) in enumerate(segs):
        d1 = segs[i + 1][0] if i + 1 < len(segs) else v.series[-1][0]
        pts = [val for d, val in v.series if d0 <= d <= d1]
        ix = [val for d, val in v.index if d0 <= d <= d1]
        br = float(pts[-1] / pts[0] - 1) if len(pts) > 1 and pts[0] else None
        ir = ix[-1] / ix[0] - 1 if len(ix) > 1 and ix[0] else None
        out.append((label, d0, d1, br, ir))
    return out


def strategy(v: Any, x: Extras) -> str:
    run = x.running
    u = x.update
    parts = ['<p><a href="/server" data-nav>‹ Server</a></p><h1>Strategy</h1>']
    rows = "".join(
        f"<tr><td>{e(k)}</td><td class='r'><b>{e(run.get(key, '-') or '-')}</b></td></tr>"
        for k, key in (("Version", "version"), ("Version id", "id"), ("Config hash", "config"),
                       ("Strategy code hash", "code"), ("Code commit", "commit"))
    )  # fmt: skip
    mode = ("immediate: an approved update is applied once the ASX is closed and no order is "
            "working, then an out-of-cycle decision for your approval" if x.update_mode == "immediate"
            else "next decision: an approved update takes effect at the next month-end decision")  # fmt: skip
    parts.append(section("Running now", f"<table><tbody>{rows}</tbody></table>"
                         f"<p class='small'>Update mode: <b>{e(mode)}</b> (strategy.update_mode)</p>"
                         "<p class='small muted'>Live later: daily strategy changes increase trading "
                         "costs and tax; immediate mode on a live book will need an explicit, "
                         "acknowledged config change.</p>"))  # fmt: skip
    if int(u.get("ahead") or 0) > 0:
        strat = bool(u.get("strategy", True))
        n = u.get("notes") or {}
        body = (f'<p class="summary">{"Strategy update" if strat else "App-only update"} available</p>'
                f"<p class='small muted'>{int(u['ahead'])} commit(s) · {e(u.get('subject', ''))}</p>")  # fmt: skip
        for k, lab in (("version", "Version"), ("what", "What changes"), ("why", "Why"),
                       ("tested", "Tested"), ("takes_effect", "Takes effect")):  # fmt: skip
            if n.get(k):
                body += f"<p class='small'><b>{lab}:</b> {e(n[k])}</p>"
        if not strat:
            body += "<p class='small'>Screens, alerts or server scripts only: the trading rules do not change.</p>"
        elif u.get("reasons"):
            body += "<p class='small muted'>" + e("; ".join(u["reasons"][:6])) + "</p>"
        body += f'<a class="btn wide" href="{act_link(a="srv:update")}">Approve update…</a>'
        parts.append(section("Update available", body))
    else:
        parts.append(section("Updates", "<p class='muted'>Up to date with the branch on GitHub "
                             "(checked by the server worker every 10 minutes).</p>"))  # fmt: skip
    for r in x.pending_jobs:
        if r["action"] in ("update", "rollback"):
            parts.append(f'<p class="note">{e(r["action"])}: {e(r["status"])} · '
                         f'{e(str(r["result"] or "queued"))}</p>')  # fmt: skip
    if u.get("previous"):
        parts.append(section("Go back", (
            f"<p>Previous version: commit <b>{e(str(u['previous'])[:10])}</b> (the one running "
            "before the last update).</p>"
            f'<a class="btn sec wide" href="{act_link(a="srv:rollback")}">Go back to the previous version…</a>')))  # fmt: skip
    perf = version_perf(v, x)
    if perf:
        rows2 = "".join(
            f"<tr><td><b>{e(lab)}</b><div class='sub'>{d0:%d %b} – {d1:%d %b %y}</div></td>"
            f"<td class='r {tone(br)}'>{pct(br)}</td><td class='r'>{pct(ir)}</td></tr>"
            for lab, d0, d1, br, ir in perf
        )
        parts.append(section("Results by strategy version", "<table><thead><tr><th>Version</th>"
                             f"<th class='r'>Book</th><th class='r'>Index</th></tr></thead><tbody>{rows2}"
                             "</tbody></table><p class='small muted'>Each decision is stamped with the "
                             "version that made it.</p>"))  # fmt: skip
    notes = "".join(
        f"<li><b>{e(c.get('version'))}</b> <span class='sub'>{e(c.get('date', ''))}</span>"
        + "".join(f"<div class='small'><b>{lab}:</b> {e(c[k])}</div>"
                  for k, lab in (("what", "What"), ("why", "Why"), ("tested", "Tested"),
                                 ("takes_effect", "Takes effect")) if c.get(k))
        + "</li>"
        for c in x.changelog
    )  # fmt: skip
    parts.append(section("Release notes", f'<ul class="list">{notes}</ul>' if notes
                         else "<p class='muted'>No release notes.</p>"))  # fmt: skip
    return shell(v, x, "Strategy", "".join(parts), "server")


# ---------------------------------------------------------------- Settings


def settings(v: Any, x: Extras, version: str, checklist: Sequence[tuple[str, bool | None]]) -> str:
    al = x.alerts
    rows = "".join(
        f"<li>{e(lab)}: <b>{'on' if on else 'off'}</b></li>"
        for lab, on in (("PAGE alerts", True), ("Approval requests", True),
                        ("Daily report", al.get("report", True)), ("Other messages", al.get("info", False)),
                        ("My own actions", al.get("action", False)))
    )  # fmt: skip
    who = ", ".join(sorted(x.action_logins)) or "nobody (actions off)"
    ck = "".join(
        f"<li><span class='pill {'ok' if ok else 'bad' if ok is False else 'amber'}'>"
        f"{'yes' if ok else 'no' if ok is False else '?'}</span> {e(lab)}</li>"
        for lab, ok in checklist
    )
    body = (
        "<h1>Settings</h1>"
        + section("Alerts", f'<ul class="list">{rows}</ul><a class="btn wide" href="/act/alerts">'
                  "🔔 Turn on alerts / choose which</a>")
        + section("Who may act", f"<p>Allowed log-ins: <b>{e(who)}</b></p>"
                  f"<p class='small muted'>You are: {e(x.viewer or 'unknown (not through Tailscale)')}"
                  "</p><p class='small muted'>Changed on the server only (bigwins menu).</p>")
        + section("Messages", f"<p>Channel: <b>{e(x.channel)}</b> (notify.channel)</p>")
        + section("Go-live checklist (docs/GO_LIVE_GUIDE.md part E)",
                  f'<ul class="list">{ck}</ul><p class="small muted">This build is PAPER ONLY; '
                  "going live is a separate, reviewed owner step.</p>")
        + section("About", f"<p>App version <b>{e(version)}</b></p>")
    )  # fmt: skip
    return shell(v, x, "Settings", body, "")


def dumps_mapping(m: Mapping[str, Any]) -> str:
    return json.dumps(m, default=str)
