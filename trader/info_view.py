"""Announcements, director trades and short positions on a share's page (BF-D78).

Reads, read-only, what the private info archive (``deploy/info_archive.py``, a host job,
owner decision 24 Nov 2026) stores under its data folder (``info_archive.app_dir``,
mounted read-only into the app):

* ``asx_notices/<YYYY-MM-DD>/list.csv`` (code, date, time, price_sensitive, headline,
  ids_id, kept) and ``DONE`` once the day is complete;
* ``asx_notices/<day>/pdf/<CODE>_<idsId>.txt`` (``pdftotext -layout``) for director-interest
  (Appendix 3Y / 3X / 3Z) and capital-raising notices;
* ``asic_short/RR<YYYYMMDD>-<ver>-SSDailyAggShortPos.csv.gz`` (ASIC's daily short positions).

BF-D92 (the News tab): ``feed`` lists the headlines of the held shares together and
``pdf_file`` finds a stored ``pdf/<CODE>_<idsId>.pdf``; still read-only, nothing is fetched.

INFORMATION ONLY: nothing here feeds the strategy, a paper line or an order. The data is
private (personal, non-commercial use): it is shown only inside the owner's app.

Director trades are read from the 3Y text by a deliberately cautious heuristic: an
on-market buy or sell is reported only when the "Nature of change" says on-market and one
side (acquired / disposed) is clearly nil; option, right and plan issues are never buys;
anything else is "unclear" rather than a guess.
"""

from __future__ import annotations

import csv
import gzip
import io
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from trader.constants import ASX_TZ

CAP_RAISE = re.compile(
    r"proposed issue|application for quotation|placement|entitlement|capital rais|"
    r"share purchase plan|\bspp\b|cleansing|appendix 2a|appendix 3b|rights issue|"
    r"institutional offer|retail offer|underwrit",
    re.I,
)
HALT = re.compile(r"trading halt|suspension from (official )?quotation|voluntary suspension|"
                  r"reinstatement to (official )?quotation", re.I)  # fmt: skip
TAKEOVER = re.compile(r"takeover|bidder'?s statement|target'?s statement|scheme booklet|"
                      r"scheme implementation|scheme of arrangement|off-market bid|"
                      r"non-binding indicative|unsolicited proposal", re.I)  # fmt: skip
DIRECTOR = re.compile(r"director'?s?.? interest|appendix 3[xyz]", re.I)
FLAG_WORDS = (("raise", "Capital raising"), ("halt", "Trading halt"), ("takeover", "Takeover"),
              ("director", "Director's interest"))  # fmt: skip
NOT_COLLECTED = "Not collected yet"


@dataclass(frozen=True)
class DirectorTrade:
    """``kind``: buy | sell | not a buy | unclear (never a guess)."""

    kind: str
    number: int | None = None
    value: Decimal | None = None
    why: str = ""


@dataclass(frozen=True)
class Notice:
    day: date
    time: str
    code: str
    headline: str
    price_sensitive: bool
    ids_id: str
    flags: tuple[str, ...] = ()
    trade: DirectorTrade | None = None
    pdf: bool = False  # BF-D92: the archive stores this notice's PDF


@dataclass(frozen=True)
class ShortPos:
    day: date
    pct: float  # % of the shares on issue reported short
    before_day: date | None = None
    before_pct: float | None = None


@dataclass
class ArchiveStatus:
    days: list[date] = field(default_factory=list)  # complete days stored (DONE)
    missed: list[date] = field(
        default_factory=list
    )  # ASX sessions since the first day, none stored
    short_day: date | None = None
    short_files: int = 0

    @property
    def last(self) -> date | None:
        return self.days[-1] if self.days else None


def flags_of(headline: str) -> tuple[str, ...]:
    out = []
    if CAP_RAISE.search(headline):
        out.append("raise")
    if HALT.search(headline):
        out.append("halt")
    if TAKEOVER.search(headline):
        out.append("takeover")
    if DIRECTOR.search(headline):
        out.append("director")
    return tuple(out)


# ---------------------------------------------------------------- reading the archive

_LIST_CACHE: dict[str, tuple[float, dict[str, list[dict[str, str]]]]] = {}


def _day_dirs(root: Path) -> list[tuple[date, Path]]:
    base = root / "asx_notices"
    out = []
    try:
        for p in base.iterdir():
            try:
                out.append((date.fromisoformat(p.name), p))
            except ValueError:
                continue
    except OSError:
        return []
    return sorted(out)


def _rows_by_code(day_dir: Path) -> dict[str, list[dict[str, str]]]:
    f = day_dir / "list.csv"
    try:
        mt = f.stat().st_mtime
    except OSError:
        return {}
    hit = _LIST_CACHE.get(str(f))
    if hit and hit[0] == mt:
        return hit[1]
    out: dict[str, list[dict[str, str]]] = {}
    try:
        with f.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            for r in csv.DictReader(fh):
                code = (r.get("code") or "").strip().upper()
                if code:
                    out.setdefault(code, []).append({k: (v or "") for k, v in r.items() if k})
    except (OSError, csv.Error):
        return {}
    if len(_LIST_CACHE) > 400:
        _LIST_CACHE.clear()
    _LIST_CACHE[str(f)] = (mt, out)
    return out


def notices(root: Path | None, code: str, today: date, days: int = 90) -> list[Notice] | None:
    """The share's announcements of the last ``days`` days, newest first; None when the
    archive has not collected anything yet."""
    if root is None:
        return None
    dirs = _day_dirs(root)
    if not dirs:
        return None
    code = code.upper()
    since = today - timedelta(days=days)
    out: list[Notice] = []
    for d, p in dirs:
        if not since <= d <= today:
            continue
        for r in _rows_by_code(p).get(code, []):
            head = r.get("headline", "").strip()
            ids = re.sub(r"\D", "", r.get("ids_id", ""))[:12]
            fl = flags_of(head)
            trade = None
            if "director" in fl and ids:
                txt = p / "pdf" / f"{code}_{ids}.txt"
                trade = director_trade(_read_text(txt)) if txt.is_file() else None
            out.append(Notice(d, r.get("time", "").strip()[:12], code, head[:300],
                              r.get("price_sensitive", "").strip() == "1", ids, fl, trade))  # fmt: skip
    out.sort(key=lambda n: (n.day, _minutes(n.time)), reverse=True)
    return out


# ---------------------------------------------------------------- the News tab (BF-D92)

REINSTATE = re.compile(r"reinstatement to (official )?quotation", re.I)
PDF_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PDF_NAME = re.compile(r"^([A-Z0-9]{1,6})_(\d{1,12})\.pdf$")


def latest_day(root: Path | None) -> date | None:
    """The newest day the archive holds a list for (None = nothing collected yet)."""
    if root is None:
        return None
    days = [d for d, p in _day_dirs(root) if (p / "list.csv").is_file()]
    return days[-1] if days else None


def feed(root: Path | None, codes: Sequence[str], today: date,
         days: int = 14) -> list[Notice] | None:  # fmt: skip
    """BF-D92: the announcements of several shares (the ones held) in the last ``days``
    days as one list, newest first; None when the archive has collected nothing yet.
    Headlines only: no notice text is read, so nothing here rates or judges a notice."""
    if root is None:
        return None
    dirs = [(d, p) for d, p in _day_dirs(root) if (p / "list.csv").is_file()]
    if not dirs:
        return None
    want = [c.upper() for c in dict.fromkeys(codes)]
    since = today - timedelta(days=days)
    out: list[Notice] = []
    for d, p in dirs:
        if not since <= d <= today:
            continue
        by = _rows_by_code(p)
        for code in want:
            for r in by.get(code, []):
                head = r.get("headline", "").strip()
                ids = re.sub(r"\D", "", r.get("ids_id", ""))[:12]
                has = bool(ids) and pdf_file(root, str(d), f"{code}_{ids}.pdf") is not None
                out.append(Notice(d, r.get("time", "").strip()[:12], code, head[:300],
                                  r.get("price_sensitive", "").strip() == "1", ids,
                                  flags_of(head), None, has))  # fmt: skip
    out.sort(key=lambda n: (n.day, _minutes(n.time), n.code), reverse=True)
    return out


def stamp(n: Notice) -> int:
    """A number that grows with a notice's day and time (the News tab's unread dot)."""
    return int(f"{n.day:%Y%m%d}") * 10000 + _minutes(n.time)


def pdf_file(root: Path | None, day_s: str, name: str) -> Path | None:
    """The stored PDF ``asx_notices/<day>/pdf/<CODE>_<idsId>.pdf``, or None. The day and
    the name are matched against fixed patterns and the file must lie inside the archive
    (no link is followed out of it) and start like a PDF."""
    if root is None or not PDF_NAME.match(name) or not PDF_DAY.match(day_s):
        return None
    f = root / "asx_notices" / day_s / "pdf" / name
    try:
        base = (root / "asx_notices").resolve()
        real = f.resolve()
        ok = base in real.parents and real.is_file() and not f.is_symlink()
        if ok:
            with real.open("rb") as fh:
                ok = fh.read(5) == b"%PDF-"
    except OSError:
        return None
    return real if ok else None


def _minutes(t: str) -> int:
    m = re.match(r"(\d{1,2}):(\d{2})\s*([ap]m)?", t.strip(), re.I)
    if not m:
        return 0
    h = int(m.group(1)) % 12 if m.group(3) else int(m.group(1))
    if m.group(3) and m.group(3).lower() == "pm":
        h += 12
    return h * 60 + int(m.group(2))


def _read_text(p: Path, limit: int = 400_000) -> str:
    try:
        with p.open("rb") as fh:
            return fh.read(limit).decode("utf-8", "replace")
    except OSError:
        return ""


_SHORT_CACHE: dict[str, tuple[float, dict[str, float]]] = {}
SHORT_NAME = re.compile(r"^RR(\d{8})-(\d{3})-SSDailyAggShortPos\.csv\.gz$")


def _short_files(root: Path) -> list[tuple[date, int, Path]]:
    out = []
    try:
        for p in (root / "asic_short").iterdir():
            m = SHORT_NAME.match(p.name)
            if not m:
                continue
            try:
                d = date(int(m.group(1)[:4]), int(m.group(1)[4:6]), int(m.group(1)[6:]))
            except ValueError:
                continue
            out.append((d, int(m.group(2)), p))
    except OSError:
        return []
    out.sort()
    best: dict[date, tuple[date, int, Path]] = {}
    for x in out:  # the newest version of each day
        best[x[0]] = x
    return sorted(best.values())


def _short_table(p: Path) -> dict[str, float]:
    try:
        mt = p.stat().st_mtime
    except OSError:
        return {}
    hit = _SHORT_CACHE.get(str(p))
    if hit and hit[0] == mt:
        return hit[1]
    out: dict[str, float] = {}
    try:
        with gzip.open(p, "rb") as fh:
            raw = fh.read(20_000_000)
    except (OSError, EOFError):
        return {}
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode(
        "utf-8-sig", "replace")  # fmt: skip
    rd = csv.reader(io.StringIO(text))
    head = next(rd, [])
    cols = [h.strip().lower() for h in head]
    ci = next((i for i, h in enumerate(cols) if h == "product code"), 1)
    pi = next((i for i, h in enumerate(cols) if h.startswith("% of")), len(cols) - 1)
    for r in rd:
        if len(r) <= max(ci, pi):
            continue
        try:
            out[r[ci].strip().upper()] = float(r[pi].strip() or "nan")
        except ValueError:
            continue
    if len(_SHORT_CACHE) > 8:
        _SHORT_CACHE.clear()
    _SHORT_CACHE[str(p)] = (mt, out)
    return out


def short_position(root: Path | None, code: str) -> ShortPos | None:
    """The latest ASIC short position of ``code`` (and about a month earlier)."""
    if root is None:
        return None
    files = _short_files(root)
    if not files:
        return None
    d, _, p = files[-1]
    v = _short_table(p).get(code.upper())
    if v is None or math.isnan(v):
        return None
    before = [x for x in files if x[0] <= d - timedelta(days=28)]
    bd = bp = None
    if before:
        b = _short_table(before[-1][2]).get(code.upper())
        if b is not None and not math.isnan(b):
            bd, bp = before[-1][0], b
    return ShortPos(d, v, bd, bp)


def status(root: Path | None, sessions: Sequence[date], today: date,
           now: datetime | None = None) -> ArchiveStatus:  # fmt: skip
    """What the archive holds: complete days, ASX sessions missed since its first day
    (only sessions already due: the next morning at 09:30, BF-D81 N4; without ``now``,
    up to yesterday), and the newest ASIC short-position file."""
    st = ArchiveStatus()
    if root is None:
        return st
    st.days = [d for d, p in _day_dirs(root) if (p / "DONE").is_file()]
    if st.days:
        have = set(st.days)

        def due(s: date) -> bool:
            if now is None:
                return s < today
            return datetime.combine(s + timedelta(days=1), time(9, 30), ASX_TZ) <= now

        st.missed = [s for s in sessions if st.days[0] <= s and due(s) and s not in have][-30:]
    files = _short_files(root)
    st.short_files = len(files)
    st.short_day = files[-1][0] if files else None
    return st


# ---------------------------------------------------------------- Appendix 3Y (heuristic)

LABELS = (
    ("nature", r"Nature of change"),
    ("acquired", r"Number acquired"),
    ("disposed", r"Number disposed"),
    ("value", r"Value\s*/\s*Consideration"),
    ("class", r"Class"),
    ("after", r"No\. of securities held after change"),
    ("prior", r"No\. of securities held prior to change"),
    ("date", r"Date of change"),
    ("direct", r"Direct or indirect interest"),
    ("indirect", r"Nature of indirect interest"),
)
_LABEL_RE = re.compile(
    r"^(\s*)(" + "|".join(f"(?P<{k}>{p})" for k, p in LABELS) + r")\b(.*)$", re.I
)
ISSUE = re.compile(
    r"option|right|performance|grant|issue|plan\b|vest|exercis|conver|dividend reinvest|"
    r"\bdrp\b|placement|entitlement|share purchase|\bspp\b|in lieu|fees|salary|incentive|"
    r"\brsu|award|subscription|capital rais|allot|consideration for|remuneration",
    re.I,
)
ON_MARKET = re.compile(r"\bon[\s-]?market", re.I)
OFF_MARKET = re.compile(r"\boff[\s-]?market", re.I)
PAGE_BREAK = re.compile(
    r"appendix\s*3[xyz]\b|\bpage \d|\+ see chapter|for personal use only|"
    r"change of director",
    re.I,
)
CHUNK = re.compile(r"\S+(?: {1,2}\S+)*")
NIL = re.compile(r"^\s*(nil|n/?a|none|-|–|0)\.?\s*$", re.I)


def _fields(part: str) -> dict[str, str]:
    """Label -> value text, read from the right-hand column of the layout text (the
    left column holds the form's own notes and examples, which are dropped)."""
    out: dict[str, list[str]] = {}
    cur: str | None = None
    col = 0
    known = 0
    for line in part.splitlines():
        m = _LABEL_RE.match(line)
        if m:
            key = next(k for k, _ in LABELS if m.group(k))
            if key in out:  # a second block (another holder or director): stop
                cur = None
                if key == "nature":
                    out.setdefault("_repeat", []).append("1")
                continue
            rest = m.group(len(LABELS) + 3) or ""
            lead = len(rest) - len(rest.lstrip())
            col = m.end(2) + lead if rest.strip() else known
            known = known or col  # the table's value column, for labels with no inline value
            cur = key
            out[key] = [rest.strip()] if rest.strip() else []
            continue
        if cur is None:
            continue
        if not line.strip():
            continue
        if col == 0:  # the value starts on the next line: find its column there
            stripped = line.lstrip()
            if stripped.lower().startswith(("note:", "example:")):
                continue
            col = len(line) - len(stripped)
            known = col
        # the right-hand column: text chunks (split by 3+ spaces) that start at or after it
        right = " ".join(m.group(0) for m in CHUNK.finditer(line) if m.start() >= col - 2)
        if PAGE_BREAK.search(line):
            cur = None  # the page footer / header: the value ended
            continue
        if right and not right.lower().startswith(("note:", "example:")):
            out[cur].append(right)
    res = {k: " ".join(v).strip() for k, v in out.items()}
    res.update({k + "_1": v[0] for k, v in out.items() if v})
    return res


def _count(text: str) -> int | None:
    """One quantity, or None (missing, several different numbers, unreadable); nil = 0."""
    t = re.sub(r"\(\s*\w\s*\)", " ", text)  # "(1)", "(a)" list markers
    if not t.strip() or NIL.match(t):
        return 0 if t.strip() else None
    raw = re.findall(r"(?<![\d.$])(\d{1,3}(?:,\d{3})+|\d+)(?![\d.])", t)
    # a bare 4-digit 1990-2099 is a year (a date in the text), not a quantity
    nums = {int(n.replace(",", "")) for n in raw if not re.fullmatch(r"(19|20)\d\d", n)}
    nums.discard(0)
    if len(nums) == 1:
        return nums.pop()
    if not nums and re.fullmatch(r"\s*(nil|n/?a|none)\b.*", t, re.I):
        return 0
    return None


def _money(text: str, number: int | None) -> Decimal | None:
    amounts = []
    for m in re.finditer(r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)", text):
        try:
            amounts.append(Decimal(m.group(1).replace(",", "")))
        except InvalidOperation:
            continue
    if len(amounts) != 1:
        return None
    a = amounts[0]
    if re.search(r"per\b[^$]{0,24}(share|security|unit)|average price|avg\.? price|@", text, re.I):
        return (a * number).quantize(Decimal(1)) if number else None
    return a.quantize(Decimal(1)) if a > 0 else None


def director_trade(text: str) -> DirectorTrade | None:  # noqa: PLR0911, PLR0912 - one rule a line
    """Read an Appendix 3Y's Part 1. None = not a 3Y (or no text)."""
    if not text or not re.search(r"appendix\s*3[xyz]|director.{0,3}s interest", text, re.I):
        return None
    if re.search(r"appendix\s*3x", text, re.I) and not re.search(r"appendix\s*3y", text, re.I):
        return DirectorTrade(
            "not a buy", why="initial notice (Appendix 3X): a new director's holding"
        )
    if re.search(r"appendix\s*3z", text, re.I) and not re.search(r"appendix\s*3y", text, re.I):
        return DirectorTrade("not a buy", why="final notice (Appendix 3Z): a director leaving")
    a = re.search(r"Part\s*1\s*[-–]", text)
    b = re.search(r"Part\s*2\s*[-–]", text)
    part = text[
        a.start() if a else 0 : b.start() if b and (not a or b.start() > a.start()) else None
    ]
    f = _fields(part)
    if len(re.findall(r"Part\s*1\s*[-–]", text)) > 1 or f.get("_repeat"):
        return DirectorTrade("unclear", why="several changes in one notice")
    nature = f.get("nature", "")
    if not nature:
        return DirectorTrade("unclear", why="no nature of change found")
    on = bool(ON_MARKET.search(nature)) and not OFF_MARKET.search(nature)
    issue = bool(ISSUE.search(nature)) or bool(re.search(r"option|right", f.get("class", ""), re.I))
    if issue and not on:
        return DirectorTrade("not a buy", why=_short(nature))
    if not on:
        return DirectorTrade("unclear", why=_short(nature))
    if issue:
        return DirectorTrade("unclear", why="on-market trade mixed with an issue or exercise")
    acq, disp = _count(f.get("acquired", "")), _count(f.get("disposed", ""))
    listed = re.search(r"\(\s*\w\s*\)", f.get("acquired", "") + f.get("disposed", ""))
    if acq is None and not listed:  # several numbers: the first line may say it plainly
        acq = _count(f.get("acquired_1", "")) or None
    if disp is None and not listed:
        disp = _count(f.get("disposed_1", ""))
    if acq is None or disp is None:
        return DirectorTrade("unclear", why="the numbers could not be read")
    if acq > 0 and disp == 0:
        kind, n = "buy", acq
    elif disp > 0 and acq == 0:
        kind, n = "sell", disp
    else:
        return DirectorTrade("unclear", why="both or neither side filled in")
    return DirectorTrade(kind, n, _money(f.get("value", ""), n), _short(nature))


def _short(s: str, n: int = 90) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"
