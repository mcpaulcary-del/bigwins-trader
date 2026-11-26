"""The paper record in the app (BF-D93, BF-D94): presentation and alerts only.

* **Paper record** (``/record``): the REAL record's own outputs, read-only, from the
  display copy the host worker keeps (``/data/recordview``: the research environment's
  nightly copy until the cut-over, this server's record after it): each line's value,
  change today, return since its start against A200 and the 40/60 plan after costs, and
  where it sits among its random twins; the holdings with their day moves. The rules of
  the scoreboard hold here too: the main line against A200 leads; every other line is
  **information only, mostly luck at this stage**, in the registered order, never ranked;
  NEWS-C per-share ratings are never shown.
* **Nightly report** (``/record/report``): the short report the cloud task writes at about
  20:30 Sydney and drops into the OneDrive relay (``reports/<day>/report.json`` and
  ``report.md``), with its "Big movers" list (also on the News tab). Everything read from
  the relay is treated as untrusted text: strict types and lengths, https links only,
  every character escaped, the Markdown limited to the research pages' safe subset.
* **Health and the missed-job alarm**: the host worker reports each moved job
  (``trader-bf server-jobs record``); ``freshness`` gives each job's expected time
  (the same table as ``record/tools/jobs.py``; a test keeps them equal), so a late or
  failed record job pages once per incident like every other job (BF-D77).
* **Inbox**: one message when the paper day is booked (plain numbers, written on the
  server, so a report exists even if the cloud task fails), one when the nightly report
  arrives, one line a day for the parallel run's comparison, and a PAGE for a refused
  relay file or a failed job.

Nothing here trades, approves or changes a setting, and nothing writes to the record.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from trader import ops_view as ov
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.webui import backlink, chev, e, icon, plural, section

MAIN_BOOK = "EMG2_18_SIM_BT_C6"  # the live trader's strategy as a paper line of the record
MAIN_NAME = "Main line on paper (EMG2-18 + shield + patient sell)"
A200_CMP = ("CMP_A200_100k_b0", "CMP_A200_25k_b0")  # A$0 brokerage: the record's primary comparator
P4060_CMP = ("CMP_4060_100k_b0", "CMP_4060_25k_b0")
INFO_ONLY = "Information only, never evidence for or against the main line"
MAX_FILE = 4 * 1024 * 1024
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CODE_RE = re.compile(r"^[A-Z0-9]{1,6}$")
BOOK_RE = re.compile(r"^[A-Za-z0-9_ ()+-]{1,60}$")


# ---------------------------------------------------------------- reading the record's outputs
def _fl(x: object) -> float | None:
    try:
        v = float(str(x))
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _rows(p: Path) -> list[dict[str, str]]:
    try:
        if not p.is_file() or p.stat().st_size > MAX_FILE:
            return []
        with p.open(newline="", encoding="utf-8-sig") as fh:
            return [dict(r) for r in csv.DictReader(fh)]
    except (OSError, csv.Error, UnicodeDecodeError):
        return []


def _text(p: Path, limit: int = 600_000) -> str:
    try:
        if not p.is_file() or p.stat().st_size > limit:
            return ""
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def view_dir(src: Any) -> Path | None:
    """Where the record's display files are: the worker's copy; else (a real, non-demo app)
    the record folder the trader already mounts."""
    rv = getattr(src, "record_view", None)
    if isinstance(rv, Path) and (rv / "paper" / "scorecard_latest.csv").is_file():
        return rv
    sc = getattr(src, "scorecard", None)
    if not getattr(src, "demo", False) and isinstance(sc, Path) and sc.is_file():
        return sc.parent.parent
    return None


@dataclass(frozen=True)
class Line:
    book: str
    name: str
    group: str  # main | kept | other | comparator
    capital: float | None
    nav: float | None
    change: float | None  # the last booked day's change of value (fraction)
    ret: float | None  # since the line's start, after the record's own costs
    vs_a200: float | None
    vs_4060: float | None
    worked_out: bool  # vs figures worked out here from the record's comparators
    pct_random: float | None  # share of its random twins it is ahead of (0..1)
    holdings: int | None
    asof: str
    start: str
    note: str = ""

    @property
    def started(self) -> bool:
        return self.nav is not None


@dataclass
class Record:
    asof: str = ""
    lines: list[Line] = field(default_factory=list)
    holdings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    source: str = ""
    source_note: str = ""
    refreshed: str = ""
    prev_asof: str = ""

    def by_group(self, g: str) -> list[Line]:
        return [x for x in self.lines if x.group == g]


def _history(rows: Sequence[Mapping[str, str]]) -> dict[str, list[tuple[str, float]]]:
    out: dict[str, list[tuple[str, float]]] = {}
    for r in rows:
        nav = _fl(r.get("nav"))
        b, d = str(r.get("book", "")).strip(), str(r.get("asof", ""))[:10]
        if b and nav is not None and DAY_RE.match(d):
            out.setdefault(b, []).append((d, nav))
    for v in out.values():
        v.sort()
    return out


def _since(hist: Mapping[str, list[tuple[str, float]]], books: Sequence[str], start: str,
           asof: str) -> float | None:  # fmt: skip
    """The comparator's return from the close of ``start`` to ``asof`` (the same money put
    into the fund at the close the line's first orders filled)."""
    for b in books:
        pts = dict(hist.get(b, []))
        if start in pts and asof in pts and pts[start] > 0:
            return pts[asof] / pts[start] - 1
    return None


def _kept_names() -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for _lid, name, books in ov.KEPT_LINES:
        for b in books:
            out[b] = ("kept", name)
    return out


def _group(book: str, kind: str) -> tuple[str, str]:
    if book == MAIN_BOOK:
        return "main", MAIN_NAME
    kept = _kept_names()
    if book in kept:
        return kept[book]
    if book.startswith("CMP_") or "RND" in book or "_CMP_" in book or kind.endswith("_RND"):
        return "comparator", book
    return "other", book


def load(root: Path | None) -> Record | None:
    """The record's display files, or None when there is no record copy here."""
    if root is None:
        return None
    paper = root / "paper"
    rows = _rows(paper / "scorecard_latest.csv")
    if not rows:
        return None
    hist = _history(_rows(paper / "scorecard_history.csv"))
    rec = Record(asof=max((str(r.get("asof", ""))[:10] for r in rows), default=""))
    try:
        meta = json.loads(_text(root / "source.json", 4000) or "{}")
    except ValueError:
        meta = {}
    if isinstance(meta, dict):
        rec.source = str(meta.get("source", ""))[:160]
        rec.source_note = str(meta.get("note", ""))[:200]
        rec.refreshed = str(meta.get("refreshed", ""))[:25]
    seen: set[str] = set()
    for r in rows:
        book = str(r.get("book", "")).strip()
        if not book or book in seen or not BOOK_RE.match(book):
            continue
        seen.add(book)
        group, name = _group(book, str(r.get("kind", "")))
        nav = _fl(r.get("nav"))
        asof = str(r.get("asof", ""))[:10]
        h = hist.get(book, [])
        start = h[0][0] if h else ""
        prev = [x for d, x in h if d < asof]
        change = nav / prev[-1] - 1 if nav is not None and prev and prev[-1] > 0 else None
        ret = _fl(r.get("return_since_start")) if nav is not None else None
        # the record's own A$0-brokerage comparison first (b0), then its J3 one
        va = _fl(r.get("vs_a200_b0"))
        va = va if va is not None else _fl(r.get("vs_a200"))
        vp = _fl(r.get("vs_4060_b0"))
        vp = vp if vp is not None else _fl(r.get("vs_4060"))
        worked = False
        if ret is not None and group != "comparator" and start and (va is None or vp is None):
            a = _since(hist, A200_CMP, start, asof)
            p = _since(hist, P4060_CMP, start, asof)
            if va is None and a is not None:
                va, worked = ret - a, True
            if vp is None and p is not None:
                vp, worked = ret - p, True
        hold = _fl(r.get("holdings")) if group != "comparator" else None
        rec.lines.append(Line(
            book, name, group, _fl(r.get("capital")), nav, change, ret, va, vp, worked,
            _fl(r.get("pct_of_random")), int(hold) if hold is not None else None, asof, start,
            str(r.get("note", ""))[:300] if nav is None else ""))  # fmt: skip
    # the kept lines in the REGISTERED order (never by result); the rest as the record lists them
    reg = [b for _, _, books in ov.KEPT_LINES for b in books]
    rec.lines.sort(key=lambda x: reg.index(x.book) if x.group == "kept" and x.book in reg else -1)
    rec.holdings, rec.prev_asof = _holdings(paper)
    return rec


def _holdings(paper: Path) -> tuple[dict[str, list[dict[str, Any]]], str]:
    """Holdings by book, each with its day move when the previous booked day's file (kept
    by the worker as ``holdings_prev.csv``) has the same share count for it."""
    prev: dict[tuple[str, str], tuple[float, float, str]] = {}
    prev_asof = ""
    for r in _rows(paper / "holdings_prev.csv"):
        c, sh = _fl(r.get("last_close")), _fl(r.get("shares"))
        if c and sh:
            prev[(str(r.get("book", "")), str(r.get("code", "")))] = (
                c, sh, str(r.get("last_close_date", ""))[:10])  # fmt: skip
            prev_asof = max(prev_asof, str(r.get("asof", ""))[:10])
    out: dict[str, list[dict[str, Any]]] = {}
    for r in _rows(paper / "holdings_latest.csv"):
        book, code = str(r.get("book", "")).strip(), str(r.get("code", "")).strip().upper()
        if not BOOK_RE.match(book) or not CODE_RE.match(code):
            continue
        close, shares = _fl(r.get("last_close")), _fl(r.get("shares"))
        asof, cd = str(r.get("asof", ""))[:10], str(r.get("last_close_date", ""))[:10]
        move: float | None = None
        p = prev.get((book, code))
        no_close = bool(cd and asof and cd < asof)
        if p and close and shares and not no_close and p[1] == shares and p[2] < cd and p[0] > 0:
            move = close / p[0] - 1
        out.setdefault(book, []).append({
            "code": code, "name": str(r.get("name", ""))[:60], "shares": shares, "close": close,
            "value": _fl(r.get("value_AUD")), "pnl_pct": _fl(r.get("pnl_pct")), "move": move,
            "no_close": no_close, "close_day": cd,
            "awaiting_sale": str(r.get("awaiting_sale", "")).lower() == "true"})  # fmt: skip
    return out, prev_asof


def summary_line(rec: Record | None) -> str:
    """One plain sentence for the Inbox: the main paper line against A200, never a ranking."""
    if rec is None:
        return "The record's numbers are not on this server yet."
    main = next((x for x in rec.lines if x.group == "main"), None)
    if main is None or not main.started:
        h = next((x for x in rec.lines if x.book == "H82_25k" and x.started), None)
        if h is None or h.nav is None:
            return "The main paper line has not started yet."
        return (f"The main paper line has not started yet. Large-Cap Core (A$25k): "
                f"{ov.money(h.nav)}, {ov.pct(h.ret)} since its start"
                + (f", {_pts(h.vs_a200)} against A200" if h.vs_a200 is not None else "")
                + f" ({ov.LUCK}).")  # fmt: skip
    return (f"Main line on paper: {ov.money(main.nav)}"
            + (f", {ov.pct(main.change)} on the day" if main.change is not None else "")
            + (f", {_pts(main.vs_a200)} against A200 since its start, after costs"
               if main.vs_a200 is not None else "")
            + f" ({ov.LUCK}).")  # fmt: skip


def _pts(x: float | None) -> str:
    if x is None:
        return "–"
    return f"{'+' if x > 0 else ov.MINUS if x < 0 else ''}{abs(x) * 100:.1f} pts"


# ---------------------------------------------------------------- the nightly report (relay)
@dataclass(frozen=True)
class Mover:
    code: str
    name: str
    move: float | None
    no_close: bool
    six_month: float | None
    from_high: float | None
    score_rank: int | None
    held_by: tuple[str, ...]
    why: str
    sources: tuple[int, ...]


@dataclass(frozen=True)
class Report:
    day: date
    title: str
    verdict: str
    needs: tuple[str, ...]
    movers: tuple[Mover, ...]
    sources: tuple[tuple[int, str, str], ...]  # (n, title, https url)
    markdown: str
    written: str = ""


class ReportError(ValueError):
    """A relay report that does not fit the format; it is not shown."""


def _s(x: object, n: int, what: str, required: bool = False) -> str:
    if x is None and not required:
        return ""
    if not isinstance(x, str) or len(x) > n or (required and not x.strip()):
        raise ReportError(f"{what}: not a short text")
    if any(ord(c) < 32 and c not in "\n\t" for c in x):
        raise ReportError(f"{what}: control characters")
    return x.strip()


def _frac(x: object, what: str) -> float | None:
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, int | float) or not math.isfinite(x) or abs(x) > 50:
        raise ReportError(f"{what}: not a number")
    return float(x)


def safe_url(u: object) -> str:
    """An https link to an ordinary host, or ReportError. No other scheme is ever a link."""
    if (
        not isinstance(u, str)
        or len(u) > 500
        or not re.fullmatch(r"https://[A-Za-z0-9.-]{3,200}(:\d{2,5})?(/[^\s\"'<>\\^`{|}]*)?", u)
    ):
        raise ReportError("a source link is not a plain https address")
    return u


def parse_report(  # noqa: PLR0912 - one check per field
    raw: object, markdown: str = ""
) -> Report:
    """``report.json`` (schema 1), checked field by field. Unknown keys are ignored, so the
    cloud can never put anything on the screen that is not in this format."""
    if not isinstance(raw, Mapping) or raw.get("schema") != 1:
        raise ReportError("not a schema-1 report")
    try:
        day = date.fromisoformat(str(raw.get("day")))
    except ValueError as ex:
        raise ReportError("no valid day") from ex
    srcs: list[tuple[int, str, str]] = []
    for s in raw.get("sources") or []:
        if (
            not isinstance(s, Mapping)
            or not isinstance(s.get("n"), int)
            or isinstance(s.get("n"), bool)
        ):
            raise ReportError("bad source entry")
        srcs.append((int(s["n"]), _s(s.get("title"), 160, "source title") or "source",
                     safe_url(s.get("url"))))  # fmt: skip
    if len(srcs) > 40:
        raise ReportError("too many sources")
    ns = {n for n, _, _ in srcs}
    movers: list[Mover] = []
    for m in raw.get("movers") or []:
        if not isinstance(m, Mapping):
            raise ReportError("bad mover entry")
        code = str(m.get("code", ""))
        if not CODE_RE.match(code):
            raise ReportError("bad share code")
        held = m.get("held_by") or []
        if (
            not isinstance(held, list)
            or len(held) > 20
            or any(not isinstance(h, str) or not BOOK_RE.match(h) for h in held)
        ):
            raise ReportError("bad held_by")
        rank = m.get("score_rank")
        if rank is not None and (
            isinstance(rank, bool) or not isinstance(rank, int) or not 0 < rank < 5000
        ):
            raise ReportError("bad score rank")
        refs = m.get("sources") or []
        if not isinstance(refs, list) or any(
            isinstance(x, bool) or not isinstance(x, int) for x in refs
        ):
            raise ReportError("bad source numbers")
        movers.append(Mover(
            code, _s(m.get("name"), 80, "name"), _frac(m.get("move"), "move"),
            bool(m.get("no_close")), _frac(m.get("six_month"), "six_month"),
            _frac(m.get("from_high"), "from_high"), rank, tuple(held),
            _s(m.get("why"), 240, "why") or "no news found",
            tuple(x for x in refs if x in ns)))  # fmt: skip
    if len(movers) > 15:
        raise ReportError("too many movers")
    needs = raw.get("needs_attention") or []
    if not isinstance(needs, list) or len(needs) > 10:
        raise ReportError("bad needs_attention")
    if len(markdown) > 200_000:
        raise ReportError("report.md is too long")
    return Report(day, _s(raw.get("title"), 120, "title") or f"Big Wins, {day:%a %-d %b}",
                  _s(raw.get("verdict"), 300, "verdict"),
                  tuple(_s(x, 300, "needs_attention", True) for x in needs),
                  tuple(movers), tuple(sorted(srcs)), markdown,
                  _s(raw.get("written_utc"), 25, "written_utc"))  # fmt: skip


def report_days(relay: Path | None) -> list[date]:
    base = relay / "reports" if relay is not None else None
    out = []
    for p in sorted(base.iterdir()) if base is not None and base.is_dir() else []:
        if DAY_RE.match(p.name) and (p / "report.json").is_file():
            try:
                out.append(date.fromisoformat(p.name))
            except ValueError:
                continue
    return out


def load_report(relay: Path | None, day: date | None = None) -> Report | None:
    """The report of ``day`` (default: the newest), or None when absent or not acceptable."""
    days = report_days(relay)
    if relay is None or not days:
        return None
    d = day if day in days else (None if day is not None else days[-1])
    if d is None:
        return None
    folder = relay / "reports" / str(d)
    try:
        rep = parse_report(json.loads(_text(folder / "report.json", 300_000) or "null"),
                           _text(folder / "report.md", 300_000))  # fmt: skip
    except (ValueError, ReportError):
        return None
    return rep if rep.day == d else None  # the folder's name and the report's day must agree


# ---------------------------------------------------------------- pages
def _signed(x: float | None, text: str) -> str:
    if x is None:
        return "–"
    cls = "up" if x > 0 else "down" if x < 0 else ""
    arr = "▲ " if x > 0 else "▼ " if x < 0 else ""
    return f'<span class="num {cls}">{arr}{e(text)}</span>'


def _twins(x: float | None) -> str:
    if x is None:
        return ""
    return f"ahead of {x * 100:.0f}% of its random twins"


def _line_row(x: Line) -> str:
    if not x.started:
        return (f'<li class="frow"><span class="grow"><b>{e(x.name)}</b>'
                f'<span class="sub">{e(x.note or "not started yet")}</span></span>'
                '<span class="pill">not started</span></li>')  # fmt: skip
    bits = [f"since {_dm(x.start)}: {ov.pct(x.ret)}" if x.start else ov.pct(x.ret)]
    if x.vs_a200 is not None:
        bits.append(f"{_pts(x.vs_a200)} v A200")
    if x.vs_4060 is not None:
        bits.append(f"{_pts(x.vs_4060)} v 40/60")
    sub2 = _twins(x.pct_random)
    name = x.name if x.name != x.book else x.book
    return (f'<li class="frow"><span class="grow"><b>{e(name)}</b>'
            f'<span class="sub">{e(" · ".join(bits))}{"*" if x.worked_out else ""}</span>'
            + (f'<span class="sub">{e(sub2)}</span>' if sub2 else "")
            + f'<span class="sub mono">{e(x.book)} · A${(x.capital or 0):,.0f} start</span></span>'
            f'<span class="rcol"><b class="num">{e(ov.money(x.nav))}</b>'
            f'<span class="sub">{_signed(x.change, ov.pct(x.change)) if x.change is not None else "–"}'
            "</span></span></li>")  # fmt: skip


def _dm(day_s: str) -> str:
    try:
        return f"{date.fromisoformat(day_s):%-d %b}"
    except ValueError:
        return day_s


def _head(rec: Record) -> str:
    main = next((x for x in rec.lines if x.group == "main"), None)
    try:
        when = f"{date.fromisoformat(rec.asof):%A %-d %B %Y}"
    except ValueError:
        when = rec.asof
    if main is None or not main.started:
        verdict = "The main paper line has not started yet"
        sub = ("Its first decision is Mon 30 Nov 2026; the orders fill at the close of Tue 1 Dec. "
               "Lines that already run are below.")  # fmt: skip
        figs = ""
    else:
        ahead = main.vs_a200
        verdict = ("Main line on paper: level with A200" if ahead is None or abs(ahead) < 0.0005
                   else f"Main line on paper: {'ahead of' if ahead > 0 else 'behind'} A200 by "
                        f"{abs(ahead) * 100:.1f} points")  # fmt: skip
        sub = (f"After the record's costs (brokerage and spread), since {_dm(main.start)}. "
               "Paper only: no real money.")  # fmt: skip
        figs = ('<div class="tiles">'
                f'<div class="tile"><div class="tl">Value</div><div class="tv">{e(ov.money(main.nav))}</div>'
                f'<div class="ts">from A${(main.capital or 0):,.0f}</div></div>'
                f'<div class="tile"><div class="tl">Today</div><div class="tv">'
                f"{_signed(main.change, ov.pct(main.change))}</div></div>"
                f'<div class="tile"><div class="tl">v 40/60</div><div class="tv">{e(_pts(main.vs_4060))}</div>'
                f'<div class="ts">{e(_twins(main.pct_random))}</div></div></div>')  # fmt: skip
    src = (f'<p class="caption">Booked for {e(when)}. Source: {e(rec.source or "the record on this server")}'
           + (f" ({e(rec.source_note)})" if rec.source_note else "") + ".</p>")  # fmt: skip
    return (f'<section class="newshead"><p class="verdict">{e(verdict)}</p>'
            f'<p class="bigsub">{e(sub)}</p>{figs}'
            f'<p class="luck">{icon("info")}<span>A record this short is {e(ov.LUCK)}. '
            f"The scoreboard on Home is the trader's own book; this page is the research record's "
            "paper lines.</span></p>" + src + "</section>")  # fmt: skip


def _holdings_section(rec: Record, names: Mapping[str, str]) -> str:
    if not rec.holdings:
        return section("Holdings", "<p class='muted'>The record lists no holdings yet.</p>")
    parts = []
    order = [x.book for x in rec.lines if x.book in rec.holdings]
    order += [b for b in rec.holdings if b not in order]
    for book in order:
        rows = []
        for h in rec.holdings[book]:
            if h["no_close"]:
                right = '<span class="pill wait">no close</span>'
            elif h["move"] is not None:
                right = _signed(h["move"], ov.pct(h["move"]))
            else:
                right = '<span class="sub">–</span>'
            nm = h["name"] or names.get(h["code"], "")
            rows.append(
                f'<li class="frow"><span class="grow"><b>{e(h["code"])}</b> '
                f'<span class="sub">{e(nm)}</span><span class="sub">'
                f'{e(ov.money(h["value"]))} · since buying {e(ov.pct(h["pnl_pct"]))}'
                + (" · awaiting sale" if h["awaiting_sale"] else "")
                + f'</span></span><span class="rcol">{right}</span></li>')  # fmt: skip
        parts.append(f'<details class="fold"><summary><b>{e(book)}</b> '
                     f'<span class="sub">{plural(len(rows), "share")}</span></summary>'
                     f'<ul class="list">{"".join(rows)}</ul></details>')  # fmt: skip
    cap = ("Day moves compare the last two booked closes of the record"
           + (f" ({_dm(rec.prev_asof)} to {_dm(rec.asof)})" if rec.prev_asof else "")
           + "; a dash means no earlier day here yet, or the share count changed. Lines that "
           "started on 30 Nov list their shares in the full scorecard.")  # fmt: skip
    return section("Holdings (paper)", "".join(parts) + f'<p class="caption">{e(cap)}</p>')


def record_page(
    v: Any, x: Any, rec: Record | None, rep: Report | None, shell: Callable[..., str]
) -> str:
    back = backlink("/", "Home") + "<h1>Paper record</h1>"
    if rec is None:
        body = section("", (
            "<p class='muted'>The paper record is not shown on this server yet.</p>"
            "<p class='caption'>It is kept in the research environment until the move. To see "
            "it here from a read-only copy, run on the server: "
            "<code>sudo bigwins record view on</code>.</p>"))  # fmt: skip
        return shell(v, x, "Paper record", back + body + _report_link(rep), "home")
    main = rec.by_group("main")
    kept = rec.by_group("kept")
    other = rec.by_group("other")
    cmp_rows = "".join(
        f"<tr><td>{e(c.book)}</td><td class='r num'>{e(ov.money(c.nav)) if c.nav is not None else '–'}</td>"
        f"<td class='r num'>{e(ov.pct(c.ret))}</td></tr>"
        for c in rec.by_group("comparator") if c.book.endswith("_b0") or "RND" in c.book)  # fmt: skip
    parts = [back, _head(rec), _report_link(rep)]
    if main and main[0].started:
        parts.append(section("Main line on paper", f'<ul class="list">{_line_row(main[0])}</ul>'))
    note = (f'<p class="luck">{icon("info")}<span>{e(INFO_ONLY)}; {e(ov.LUCK)}. Shown in the '
            "registered order, not ranked.</span></p>")  # fmt: skip
    if kept:
        parts.append(section("Research lines", note + '<ul class="list">'
                             + "".join(_line_row(k) for k in kept) + "</ul>"))  # fmt: skip
    if other:
        parts.append(section("Other paper lines in the record", (
            f'<p class="caption">{e(INFO_ONLY)}. Lines on the retirement list stop at the '
            f"31 Dec 2026 close; their history is kept.</p>"
            '<ul class="list">' + "".join(_line_row(k) for k in other) + "</ul>")))  # fmt: skip
    parts.append(_holdings_section(rec, getattr(x, "names", {}) or {}))
    if cmp_rows:
        parts.append(section("Comparators", (
            "<div class='tscroll'><table><thead><tr><th>Book</th><th class='r'>Value</th>"
            f"<th class='r'>Return</th></tr></thead><tbody>{cmp_rows}</tbody></table></div>"
            "<p class='caption'>A200 and the 40/60 plan with the same money and A$0 brokerage "
            "(the record's primary comparison); RND = the median of the random twins.</p>")))  # fmt: skip
    if any(k.worked_out for k in rec.lines):
        parts.append("<p class='caption'>* worked out by the app from the record's A200 and "
                     "40/60 comparators over the same days; every other figure is the record's own.</p>")  # fmt: skip
    parts.append('<ul class="list menu">'
                 f'<li><a class="nrow" href="/record/scorecard" data-nav><span class="grow"><b>Full '
                 f'scorecard</b><span class="sub">every line, as the record writes it</span></span>{chev()}</a></li>'
                 f'<li><a class="nrow" href="/record/costs" data-nav><span class="grow"><b>Cheaper-broker '
                 f'comparison</b><span class="sub">information only</span></span>{chev()}</a></li></ul>')  # fmt: skip
    return shell(v, x, "Paper record", "".join(parts), "home")


def _report_link(rep: Report | None) -> str:
    if rep is None:
        return ""
    return (f'<a class="nrow card" href="/record/report?d={rep.day}" data-nav><span class="grow">'
            f"<b>Nightly report, {rep.day:%a %-d %b}</b>"
            f'<span class="sub">{e(rep.verdict or rep.title)}</span></span>{chev()}</a>')  # fmt: skip


def doc_page(v: Any, x: Any, root: Path | None, name: str, title: str, md: Callable[[str], str],
             shell: Callable[..., str]) -> str | None:  # fmt: skip
    """SCORECARD.md / COST_ALT.md as the record writes them (escaped; safe Markdown subset)."""
    text = _text(root / "paper" / name) if root is not None else ""
    if not text:
        return None
    body = (backlink("/record", "Paper record") + f"<h1>{e(title)}</h1>"
            f'<div class="prose">{md(text)}</div>'
            "<p class='caption'>The record's own text, unchanged. Paper only.</p>")  # fmt: skip
    return shell(v, x, title, body, "home")


def movers_card(rep: Report | None, names: Mapping[str, str], today: date) -> str:
    """The News tab's "Big movers" (from the nightly report): the move, the one-line why,
    the source links. Hidden when the newest report is more than four days old."""
    if rep is None or (today - rep.day).days > 4:
        return ""
    if not rep.movers:
        body = (f'<p class="allok">{icon("check")}<span>No big moves on {rep.day:%a %-d %b}.'
                "</span></p>")  # fmt: skip
    else:
        url = {n: (t, u) for n, t, u in rep.sources}
        rows = []
        for m in rep.movers:
            ctx = []
            if m.six_month is not None:
                ctx.append(f"6 months {ov.pct(m.six_month)}")
            if m.from_high is not None:
                ctx.append(f"{ov.pct(m.from_high)} from its 12-month high")
            if m.score_rank is not None:
                ctx.append(f"score rank {m.score_rank}")
            held = ("held on paper by " + ", ".join(m.held_by)) if m.held_by else "not held"
            links = " ".join(
                f'<a href="{e(url[n][1])}" target="_blank" rel="noopener noreferrer nofollow">'
                f"[{n}]</a>" for n in m.sources if n in url)  # fmt: skip
            right = ('<span class="pill wait">no close</span>' if m.no_close or m.move is None
                     else _signed(m.move, ov.pct(m.move)))  # fmt: skip
            rows.append(
                f'<li class="frow"><span class="grow"><b>{e(m.code)}</b> '
                f'<span class="sub">{e(m.name or names.get(m.code, ""))}</span>'
                f'<span class="why">{e(m.why)} {links}</span>'
                f'<span class="sub">{e(" · ".join(ctx))}</span>'
                f'<span class="sub">{e(held)}</span></span><span class="rcol">{right}</span></li>')  # fmt: skip
        body = f'<ul class="list nlist">{"".join(rows)}</ul>'
    return section("Big movers", body + (
        f'<p class="caption">Close of {rep.day:%a %-d %b}: the 200 largest companies moving 5% or '
        "more, and shares the paper lines hold moving 3% or more or with no close. The reasons "
        "are written by the nightly report from public news; \"no news found\" means exactly "
        "that. Information only, not a trading signal. "
        f'<a href="/record/report?d={rep.day}" data-nav>The whole report</a></p>'), cls="moves")  # fmt: skip


def report_page(v: Any, x: Any, rep: Report | None, days: Sequence[date], md: Callable[[str], str],
                shell: Callable[..., str]) -> str:  # fmt: skip
    back = backlink("/record", "Paper record") + "<h1>Nightly report</h1>"
    if rep is None:
        return shell(v, x, "Nightly report", back + section("", (
            "<p class='muted'>No nightly report has arrived yet.</p><p class='caption'>It is "
            "written each trading evening and comes through the OneDrive relay; the paper "
            "record's own numbers are on the Paper record page either way.</p>")), "home")  # fmt: skip
    needs = ("<ul class='list attn'>" + "".join(
        f'<li><span class="sd wait"></span><span class="grow">{e(n)}</span></li>' for n in rep.needs)
        + "</ul>" if rep.needs else "<p class='allok'>Nothing needs you.</p>")  # fmt: skip
    older = " · ".join(f'<a href="/record/report?d={d}" data-nav>{d:%-d %b}</a>'
                       for d in reversed(days[-8:]) if d != rep.day)  # fmt: skip
    today = v.now.astimezone(ASX_TZ).date()
    body = (back + f'<section class="newshead"><p class="verdict">{e(rep.title)}</p>'
            + (f'<p class="bigsub">{e(rep.verdict)}</p>' if rep.verdict else "")
            + f'<p class="luck">{icon("info")}<span>Written by the cloud task from the record\'s '
            f"numbers and public news. {e(ov.LUCK).capitalize()}. No advice to buy or sell."
            "</span></p></section>"
            + section("Needs you", needs)
            + movers_card(rep, getattr(x, "names", {}) or {}, min(today, rep.day))
            + (section("The report", f'<div class="prose">{md(rep.markdown)}</div>')
               if rep.markdown.strip() else "")
            + (section("Sources", "<ol class='srcs'>" + "".join(
                f'<li value="{n}"><a href="{e(u)}" target="_blank" rel="noopener noreferrer nofollow">'
                f"{e(t)}</a></li>" for n, t, u in rep.sources) + "</ol>") if rep.sources else "")
            + (f"<p class='caption'>Earlier: {older}</p>" if older else ""))  # fmt: skip
    return shell(v, x, "Nightly report", body, "home")


def home_card(rec: Record | None, rep: Report | None) -> str:
    """Home: one row into the paper record (and the newest nightly report)."""
    if rec is None and rep is None:
        return ""
    sub = summary_line(rec) if rec is not None else "The record's numbers are not here yet."
    out = (f'<a class="nrow card" href="/record" data-nav><span class="grow"><b>Paper record</b>'
           f'<span class="sub">{e(sub)}</span></span>{chev()}</a>')  # fmt: skip
    return out + _report_link(rep)


# ---------------------------------------------------------------- job results from the host worker
JOBS_KEY = "record-jobs"
EVENTS_KEY = "record-events"
TOLD_KEY = "record-told"
COMPARE_KEY = "record-compare"
# job -> (name, cadence, kind of day, due HH:MM Sydney); the same table as record/tools/jobs.py
EXPECT: dict[str, tuple[str, str, str, str]] = {
    "daily": ("Paper record: daily close", "every ASX day by 21:30", "session", "21:30"),
    "intraday": ("Paper record: intraday look", "every ASX day, four looks", "session", "16:50"),
    "collect": ("Estimates and new listings", "the morning after each ASX day", "after", "09:30"),
    "archive": ("Paper record: info archive", "the morning after each ASX day", "after", "09:30"),
    "newsc-record": ("NEWS-C ratings recorded", "every ASX day before 10:00", "session", "10:00"),
    "export": ("Record sent to OneDrive (relay)", "after every record job", "session", "21:45"),
    "compare": ("Shadow compare (parallel run)", "every ASX day by 23:15", "session", "23:15"),
}
WRITER_ONLY = ("intraday", "collect")  # not run in the parallel week
SHADOW_ONLY = ("compare",)
_CLEAN = re.compile(r"[^\x20-\x7e]")


def _clean(x: object, n: int = 240) -> str:
    return _CLEAN.sub(" ", str(x))[:n]


def record_event(  # noqa: PLR0912 - one branch per kind of event
    j: Journal, raw: Mapping[str, Any], now: datetime
) -> dict[str, Any]:
    """One event from the host worker, cleaned (known keys, plain values): a job's result,
    the day's comparison, a nightly report's arrival, or a refused relay file."""
    from trader.app_store import set_state

    kind = str(raw.get("kind", ""))
    if kind not in ("job", "compare", "report", "relay"):
        return {}
    ev: dict[str, Any] = {"kind": kind, "ok": bool(raw.get("ok")), "at": now.isoformat()}
    d = ov._day(raw.get("day"))
    if d is not None:
        ev["day"] = str(d)
    if kind == "job":
        job = str(raw.get("job", ""))
        if job not in EXPECT and not re.fullmatch(r"[a-z][a-z-]{1,30}", job):
            return {}
        ev["job"] = job
        ev["mode"] = _clean(raw.get("mode", ""), 10)
        for k in ("error", "role"):
            if raw.get(k):
                ev[k] = _clean(raw[k])
        if isinstance(raw.get("head"), str) and re.fullmatch(r"[0-9a-f]{64}", raw["head"]):
            ev["head"] = raw["head"][:12]
        for k in ("seconds", "peak_mb"):
            v = _fl(raw.get(k))
            if v is not None:
                ev[k] = round(v, 1)
        if isinstance(raw.get("entries"), list):
            ev["entries"] = [{"seq": int(x["seq"]), "kind": _clean(x.get("kind", ""), 40)}
                             for x in raw["entries"][:20]
                             if isinstance(x, Mapping) and isinstance(x.get("seq"), int)]  # fmt: skip
        if isinstance(raw.get("failed_steps"), list):
            ev["failed_steps"] = [_clean(x, 40) for x in raw["failed_steps"][:8]]
        st = ov.state(j, JOBS_KEY)
        jobs = dict(st[0]) if st and isinstance(st[0], Mapping) else {}
        prev = jobs.get(job) if isinstance(jobs.get(job), Mapping) else {}
        rec = dict(ev)
        if ev["ok"]:
            rec["ok_at"] = ev["at"]
        elif isinstance(prev, Mapping) and prev.get("ok_at"):
            rec["ok_at"] = prev["ok_at"]
        jobs[job] = rec
        set_state(j, JOBS_KEY, jobs, now)
    elif kind == "compare":
        ev["pass"] = bool(raw.get("pass"))
        ev["line"] = _clean(raw.get("line", ""), 300)
        if isinstance(raw.get("diffs"), list):
            ev["diffs"] = [_clean(x, 120) for x in raw["diffs"][:8]]
        st = ov.state(j, COMPARE_KEY)
        hist = (
            [dict(x) for x in st[0] if isinstance(x, Mapping)]
            if st and isinstance(st[0], list)
            else []
        )
        hist = [h for h in hist if h.get("day") != ev.get("day")]
        set_state(j, COMPARE_KEY, [ev, *hist][:40], now)
    elif kind == "relay" and isinstance(raw.get("rejected"), list):
        ev["rejected"] = [_clean(x, 120) for x in raw["rejected"][:5]]
    st = ov.state(j, EVENTS_KEY)
    old = (
        [dict(x) for x in st[0] if isinstance(x, Mapping)] if st and isinstance(st[0], list) else []
    )
    ev["id"] = (int(old[0].get("id", 0)) + 1) if old else 1
    set_state(j, EVENTS_KEY, [ev, *old][:60], now)
    return ev


def event_text(ev: Mapping[str, Any], numbers: str = "") -> tuple[str, str, str] | None:
    """(text, kind, link) of the message an event deserves, or None (most job results are
    shown on Health only; the missed-job alarm pages a late or failed job once)."""
    k = ev.get("kind")
    day_s = _dm(str(ev.get("day", "")))
    if k == "job" and ev.get("job") == "daily" and ev.get("ok") and ev.get("mode") == "writer":
        seqs = [str(x.get("seq")) for x in ev.get("entries") or [] if isinstance(x, Mapping)]
        led = f" Ledger entry {', '.join(seqs[:4])}, head {ev.get('head', '')}." if seqs else ""
        warn = (" Some side steps failed: " + ", ".join(ev.get("failed_steps") or []) + "."
                if ev.get("failed_steps") else "")  # fmt: skip
        return (f"Paper record booked for {day_s} on the server. {numbers}{led}{warn} The nightly "
                "report with the news follows from the cloud; the numbers are on Paper record.",
                "report", "/record")  # fmt: skip
    if k == "report" and ev.get("ok"):
        return (f"Nightly report for {day_s} is ready: Big movers, what needs you, the day's "
                "numbers.", "report", f"/record/report?d={ev.get('day', '')}")  # fmt: skip
    if k == "compare":
        line = str(ev.get("line") or "Shadow compare: no result")
        if ev.get("pass"):
            return (line + " The server reproduced the research environment's day exactly.",
                    "info", "/health")  # fmt: skip
        diffs = "; ".join(ev.get("diffs") or [])
        return (f"PAGE {line}." + (f" Differs: {diffs}." if diffs else "") + " The move waits "
                "until this is explained (tell Claude).", "page", "/health")  # fmt: skip
    if k == "relay" and not ev.get("ok"):
        return ("PAGE A file in the OneDrive relay folder was refused (not an expected name, "
                "size or format): " + "; ".join(ev.get("rejected") or []) + ". Nothing was used. "
                "If you did not put it there, tell Claude.", "page", "/health")  # fmt: skip
    return None


def tell(j: Journal, notify: Callable[..., object], numbers: Callable[[], str]) -> int:
    """Each event's message once, oldest first (after a trader restart too)."""
    from trader.app_store import set_state

    st = ov.state(j, EVENTS_KEY)
    evs = [x for x in st[0] if isinstance(x, Mapping)] if st and isinstance(st[0], list) else []
    told_st = ov.state(j, TOLD_KEY)
    told = int(told_st[0]) if told_st and isinstance(told_st[0], int) else 0
    n, newest = 0, told
    for ev in reversed(evs):
        eid = int(ev.get("id", 0))
        if eid <= told:
            continue
        newest = max(newest, eid)
        try:
            num = numbers() if ev.get("kind") == "job" and ev.get("job") == "daily" else ""
        except Exception:
            num = ""
        msg = event_text(ev, num)
        if msg is not None:
            notify(*msg)
            n += 1
    if newest != told:
        set_state(j, TOLD_KEY, newest, datetime.now(ASX_TZ))
    return n


# ---------------------------------------------------------------- freshness (the missed-job alarm)
def _due(kind: str, hhmm: str) -> Callable[[date], datetime]:
    h, m = (int(x) for x in hhmm.split(":"))
    shift = timedelta(days=1) if kind == "after" else timedelta(0)
    return lambda s: datetime.combine(s + shift, time(h, m), ASX_TZ)


def host_mode(j: Journal) -> str:
    st = ov.state(j, "host-status")
    rec = st[0].get("record") if st and isinstance(st[0], Mapping) else None
    return str(rec.get("mode", "off")) if isinstance(rec, Mapping) else "off"


def freshness(j: Journal, sessions: Sequence[date], now: datetime) -> list[ov.Fresh]:
    """Each moved job against its expected time. Nothing is expected while the record is
    not on this server (mode off / view), or of a job its mode does not run."""
    mode = host_mode(j)
    if mode not in ("shadow", "writer"):
        return []
    st = ov.state(j, JOBS_KEY)
    jobs = st[0] if st and isinstance(st[0], Mapping) else {}
    out = []
    for key, (name, cadence, kind, hhmm) in EXPECT.items():
        if (mode == "shadow" and key in WRITER_ONLY) or (mode == "writer" and key in SHADOW_ONLY):
            continue
        spec = (f"rec-{key}", name, cadence)
        rec = jobs.get(key) if isinstance(jobs.get(key), Mapping) else None
        due = _due(kind, hhmm)
        past = [s for s in sessions if due(s) <= now]
        exp = max(past) if past else None
        if rec is None:
            if exp is not None and now - due(exp) < timedelta(days=3) and jobs:
                out.append(ov.Fresh(*spec, "late", "never", f"no run recorded for {exp:%a %d %b}",
                                    f"rec-{key}:late:{exp}"))  # fmt: skip
            else:
                out.append(ov.Fresh(*spec, "new", "not run yet"))
            continue
        at = _parse(rec.get("at"))
        ok_at = _parse(rec.get("ok_at"))
        last = ov._ago(ok_at, now) if ok_at else "never"
        if not rec.get("ok"):
            out.append(ov.Fresh(*spec, "failed", last, str(rec.get("error") or "see the server log")[:160],
                                f"rec-{key}:failed:{at.isoformat() if at else ''}"))  # fmt: skip
        elif exp is not None and (ok_at is None or ok_at < _start(kind, exp)):
            out.append(ov.Fresh(*spec, "late", last, f"no good run for {exp:%a %d %b}",
                                f"rec-{key}:late:{exp}"))  # fmt: skip
        else:
            out.append(ov.Fresh(*spec, "ok", last))
    return out


def _start(kind: str, s: date) -> datetime:
    """A run counts for session ``s`` from this moment on."""
    d = s + timedelta(days=1) if kind == "after" else s
    return datetime.combine(d, time(0, 0), ASX_TZ)


def _parse(x: object) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(x))
    except ValueError:
        return None
    return t if t.tzinfo is not None else t.replace(tzinfo=ASX_TZ)


# ---------------------------------------------------------------- Health
MODE_WORDS = {
    "off": "not on this server (kept in the research environment)",
    "view": "shown here from a read-only copy; written in the research environment",
    "shadow": "parallel run: this server replays each day; the research environment writes",
    "writer": "written on this server",
}


def _map(x: object) -> Mapping[str, Any]:
    return x if isinstance(x, Mapping) else {}


def health_attention(host: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    rec = _map(host.get("record"))
    out: list[tuple[str, str, str]] = []
    if not rec or rec.get("mode") not in ("shadow", "writer"):
        return out
    st = _map(rec.get("status"))
    if st and st.get("chain_ok") is False:
        out.append(("bad", "Paper record: the ledger does not verify", "tell Claude now"))
    if rec.get("mode") == "writer" and st and st.get("writer") != "server":
        out.append(("bad", "Paper record: this server is not the writer any more",
                    f"writer = {st.get('writer', '?')}, epoch {st.get('epoch', '?')}"))  # fmt: skip
    lvl = rec.get("disk_level")
    if lvl in ("low", "tight", "critical"):
        free = rec.get("disk_free_gb")
        what = {"low": "under 5 GB free", "tight": "under 3 GB: month-end and bulk jobs are held",
                "critical": "under 2 GB: only the daily close and the archive list run"}[str(lvl)]  # fmt: skip
        out.append(("bad" if lvl != "low" else "wait", "Paper record disk: " + what,
                    f"{free} GB free" if free is not None else ""))  # fmt: skip
    n = rec.get("requests_waiting")
    if isinstance(n, int) and n > 0:
        out.append(("wait", f"{plural(n, 'research entry', 'research entries')} waiting for your yes",
                    "on the server: bigwins record requests"))  # fmt: skip
    return out


def health_card(j: Journal | None, host: Mapping[str, Any], now: datetime) -> str:
    rec = _map(host.get("record"))
    mode = str(rec.get("mode", "off")) if rec else "off"
    st = _map(rec.get("status"))
    rows = [f"<li>Paper record: <b>{e(MODE_WORDS.get(mode, mode))}</b></li>"]
    if st:
        who = {"server": "this server", "cloud": "the research environment"}.get(
            str(st.get("writer")), str(st.get("writer", "?")))  # fmt: skip
        ok = st.get("chain_ok")
        rows.append(f"<li>Writer = <b>{e(who)}</b> ({e(st.get('role', '?'))}), epoch "
                    f"{e(st.get('epoch', '?'))} · {e(st.get('seq', 0))} ledger entries · head "
                    f"<span class='mono'>{e(str(st.get('head', ''))[:12])}</span> "
                    f"<span class='pill {'ok' if ok else 'bad'}'>{'chain verifies' if ok else 'CHAIN BROKEN'}"
                    "</span></li>")  # fmt: skip
        sh = str(rec.get("shipped_head", ""))[:12]
        if mode == "writer":
            same = sh and sh == str(st.get("head", ""))[:12]
            rows.append("<li>Sent to OneDrive: " + ("<b>up to date</b>" if same else
                        f"<b>behind</b> <span class='sub'>(last sent head {e(sh or 'none')}; the "
                        "next record job waits for it)</span>") + "</li>")  # fmt: skip
    view = _map(rec.get("view"))
    if view:
        rows.append(f"<li>Shown in the app from: <b>{e(str(view.get('source', ''))[:120])}</b> "
                    f"<span class='sub'>refreshed {e(str(view.get('refreshed', ''))[:16])}</span></li>")  # fmt: skip
    if rec.get("disk_free_gb") is not None and mode in ("shadow", "writer"):
        rows.append(f"<li>Record disk: <b class='num'>{e(rec.get('disk_free_gb'))} GB</b> free "
                    f"<span class='sub'>alarms under 5, 3 and 2 GB</span></li>")  # fmt: skip
    cmp_rows = ""
    if j is not None and mode == "shadow":
        cst = ov.state(j, COMPARE_KEY)
        hist = (
            [x for x in cst[0] if isinstance(x, Mapping)]
            if cst and isinstance(cst[0], list)
            else []
        )
        if hist:
            run = 0
            for h in hist:
                if not h.get("pass"):
                    break
                run += 1
            rows.append(f"<li>Parallel run: <b>{plural(run, 'day')} identical in a row</b> "
                        "<span class='sub'>the move needs 5</span></li>")  # fmt: skip
            cmp_rows = "".join(
                f"<li class='frow'><span class='grow'><span class='sub'>{e(h.get('line', ''))}</span>"
                + (f"<span class='sub warn'>{e('; '.join(h.get('diffs') or []))}</span>"
                   if h.get("diffs") else "")
                + f"</span><span class='pill {'ok' if h.get('pass') else 'bad'}'>"
                f"{'PASS' if h.get('pass') else 'FAIL'}</span></li>" for h in hist[:7])  # fmt: skip
    if mode in ("shadow", "writer"):
        rows.append("<li>Outside checks (healthchecks.io), one per record job: <b>"
                    + ("set up" if rec.get("ping_set") else "not set up")
                    + "</b>" + ("" if rec.get("ping_set") else " <span class='sub'>(optional: "
                    "bigwins secret healthchecks_record_url)</span>") + "</li>")  # fmt: skip
    n = rec.get("requests_waiting") if rec else 0
    if isinstance(n, int) and n > 0:
        rows.append(f"<li class='warn'>{plural(n, 'research entry', 'research entries')} waiting "
                    "for your yes: on the server run <code>bigwins record requests</code></li>")  # fmt: skip
    return section("Paper record", f"<ul class='list'>{''.join(rows)}{cmp_rows}</ul>"
                   "<p class='caption'>One machine writes the record at a time; a handover is "
                   "two chained ledger entries and 12 characters you compare. Paper only.</p>")  # fmt: skip
