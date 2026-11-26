"""Research in the Big Wins app (BF-D89): what the owner's own research found, what is
being tested, the dates that matter, and a glossary. Presentation only and read-only.

* **Content** lives in ``docs/research/`` (``highlights.yaml``, ``dates.yaml``,
  ``testing.yaml``, ``glossary.yaml``, ``studies/<id>.md``, optional
  ``reports/<id>.md``), reaches the phone only through a signed commit and the owner's
  Approve update, and is checked in CI by ``tests/test_bf_d89_research.py``. YAML and
  front matter go through ``trader.yamlio`` (strict, safe loader) against fixed key
  lists: an unknown key is an error.
* **Rendering** is escape-first: every text is escaped with ``webui.e`` before anything
  else, and then only headings, bullets, pipe tables, paragraphs and ``**bold**`` are
  recognised (``research_md``). No links, images, raw HTML or code from a content file.
* **Ids** in a URL are matched against the loaded index (``ID_RE``); a URL segment is
  never joined into a path.
* **Trial count**: the tail (256 KB) of the research record's ``LEDGER.jsonl``, mounted
  read-only; the last entry with an integer ``n_trials``. Without the file the
  ``trials_total`` of ``highlights.yaml`` is shown "as of" its date. A live count above
  every card's ``n_total`` says "The record has newer tests than this library" and Health
  shows "behind". The hash chain is checked by the record's own tools, not here.
* **No ranking**: paper-line figures are only inside a closed fold-out labelled "mostly
  luck at this stage", in the registered order of ledger seq 96, never sorted or coloured.

Nothing here decides or trades; the trader never imports it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from trader.constants import ASX_TZ
from trader.webui import backlink, chev, e, section
from trader.yamlio import load_yaml

ID_RE = re.compile(r"^[a-z0-9_]{1,40}$")
LUCK = "mostly luck at this stage"  # = ops_view.LUCK (a test keeps them equal)
VERDICTS: dict[str, tuple[str, str]] = {
    "works": ("Works", "rc-works"),
    "doesnt": ("Doesn't work", "rc-doesnt"),
    "mixed": ("Mixed", "rc-mixed"),
    "testing": ("Testing", "rc-testing"),
    "closed": ("Closed", "rc-closed"),
    "proposed": ("Proposed", "rc-proposed"),
}
CHIPS: dict[str, tuple[str, str]] = {**VERDICTS, "date": ("Next", "rc-date")}
CONFIDENCE = {"solid": "Solid", "likely": "Likely, not proven", "cant_tell": "Can't tell yet"}
CONF_STEPS = {"solid": 3, "likely": 2, "cant_tell": 1}  # the grade as a three-step meter
NOWRAP = 18  # a key number this short never breaks in the middle
KINDS = ("study", "review", "app_review")
MARKETS = {"ASX": "ASX", "US": "US", "app": "App & safety"}
FILTERS = {"all": "All", "asx": "ASX", "us": "US", "app": "App & safety"}
FILTER_MARKET = {"asx": "ASX", "us": "US", "app": "app"}
SLOTS = ("plan", "core", "tax", "finding", "testing", "next")
FIXED_SLOTS = ("plan", "core", "tax", "testing", "next")
DATE_KINDS = ("decision", "date", "window")
SECTIONS = ("Summary", "Key numbers", "What it means for you", "How sure are we?")

STUDY_REQUIRED = (
    "id",
    "title",
    "date",
    "kind",
    "market",
    "verdict",
    "question",
    "answer",
    "trials",
    "n_total",
    "ledger_seq",
    "confidence",
    "report",
)
STUDY_KEYS = (*STUDY_REQUIRED, "verdict_note", "placeholder")
HL_TOP = ("version", "checked", "trials_total", "trials_ledger_seq", "footer", "items")
HL_ITEM_REQUIRED = ("id", "slot", "chip", "line", "why", "do", "sources")
HL_ITEM = (*HL_ITEM_REQUIRED, "review_by")
DATES_TOP = ("version", "items")
DATE_REQUIRED = ("day", "kind", "title", "detail")
DATE_ITEM = (*DATE_REQUIRED, "do", "ref")
TESTING_TOP = (
    "version",
    "intro",
    "first_decision",
    "groups",
    "info_lines",
    "retiring",
    "rules",
    "archives",
    "in_progress",
)
GROUP_KEYS = ("name", "note", "lines")
LINE_REQUIRED = ("id", "name", "what", "reading")
LINE_KEYS = (*LINE_REQUIRED, "label")
INFO_KEYS = ("note", "lines")
RETIRING_KEYS = ("day", "note", "lines", "also")
ARCHIVES_KEYS = ("note", "items")
ARCHIVE_REQUIRED = ("id", "name", "what", "since", "reading")
ARCHIVE_KEYS = (*ARCHIVE_REQUIRED, "health_key")
PROGRESS_KEYS = ("study", "name")
GLOSSARY_TOP = ("version", "terms")
TERM_REQUIRED = ("term", "means")
TERM_KEYS = (*TERM_REQUIRED, "also")

LEDGER_TAIL = 256 * 1024
MAX_FILE = 60 * 1024
COULD_NOT_READ = "This card could not be read"
BEHIND = "The record has newer tests than this library"
ONEDRIVE = "OneDrive \u203a Big Wins forward record"
ALLOWED_TAGS = frozenset(
    {"h2", "h3", "p", "ul", "li", "table", "thead", "tbody", "tr", "th", "td", "b", "div"}
)


class ContentError(ValueError):
    """A content file breaks the fixed format (shown as "could not be read")."""


# ---------------------------------------------------------------- loading


@dataclass(frozen=True)
class Study:
    id: str
    title: str
    date: date | None
    kind: str
    market: str
    verdict: str
    verdict_note: str
    question: str
    answer: str
    trials: int | None
    n_total: int | None
    ledger_seq: int | None
    confidence: str
    report: str | None
    placeholder: bool
    summary: tuple[str, ...]
    numbers: tuple[tuple[str, str], ...]
    means: str
    sure: str
    numbers_head: str = ""  # the key-number table's first header cell (often the period)


@dataclass
class Content:
    highlights: dict[str, Any] | None = None
    dates: list[dict[str, Any]] = field(default_factory=list)
    testing: dict[str, Any] | None = None
    glossary: list[dict[str, Any]] = field(default_factory=list)
    studies: dict[str, Study] = field(default_factory=dict)
    reports: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)  # file names that could not be read
    bad_studies: list[str] = field(default_factory=list)


def _keys(d: object, allowed: Sequence[str], required: Sequence[str], where: str) -> dict[str, Any]:
    if not isinstance(d, Mapping):
        raise ContentError(f"{where}: not a mapping")
    unknown = [str(k) for k in d if k not in allowed]
    if unknown:
        raise ContentError(f"{where}: unknown key {unknown[0]!r}")
    missing = [k for k in required if k not in d]
    if missing:
        raise ContentError(f"{where}: missing key {missing[0]!r}")
    return dict(d)


def _text(d: Mapping[str, Any], k: str, where: str, optional: bool = False) -> str:
    v = d.get(k)
    if v is None and optional:
        return ""
    if not isinstance(v, str) or not v.strip():
        raise ContentError(f"{where}: {k} must be text")
    return v


def _int(d: Mapping[str, Any], k: str, where: str) -> int | None:
    v = d.get(k)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ContentError(f"{where}: {k} must be a whole number or null")
    return int(v)


def _day(v: object, where: str, optional: bool = False) -> date | None:
    if v is None and optional:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    raise ContentError(f"{where}: not a date")


def _list(v: object, where: str) -> list[Any]:
    if not isinstance(v, list):
        raise ContentError(f"{where}: not a list")
    return v


def _read(p: Path) -> str:
    if p.stat().st_size > MAX_FILE:
        raise ContentError(f"{p.name}: larger than 60 KB")
    return p.read_text(encoding="utf-8")


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ContentError("no front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ContentError("front matter not closed")
    fm = load_yaml(text[4 : end + 1])
    if not isinstance(fm, dict):
        raise ContentError("front matter is not a mapping")
    return fm, text[end + 5 :]


def _sections(body: str, where: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cur: str | None = None
    for raw in body.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            cur = line[3:].strip()
            if cur not in SECTIONS or cur in out:
                raise ContentError(f"{where}: unexpected section {cur!r}")
            out[cur] = []
        elif line.startswith("#"):
            raise ContentError(f"{where}: only '## ' headings are allowed")
        elif cur is None:
            if line.strip():
                raise ContentError(f"{where}: text before the first section")
        else:
            out[cur].append(line)
    return out


def _paragraph(lines: Iterable[str]) -> str:
    return " ".join(x.strip() for x in lines if x.strip())


def _table(lines: Iterable[str], where: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    rows: list[tuple[str, str]] = []
    for ln in (x.strip() for x in lines):
        if not ln:
            continue
        if not ln.startswith("|"):
            raise ContentError(f"{where}: key numbers must be a table")
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if len(cells) != 2:
            raise ContentError(f"{where}: key numbers have two columns")
        rows.append((cells[0], cells[1]))
    if not rows:
        return "", ()
    return rows[0][0], tuple(rows[1:])  # the first row is the header


def parse_study(text: str, file_id: str) -> Study:
    fm, body = split_front_matter(text)
    d = _keys(fm, STUDY_KEYS, STUDY_REQUIRED, file_id)
    sid = d["id"]
    if not isinstance(sid, str) or not ID_RE.match(sid) or sid != file_id:
        raise ContentError(f"{file_id}: id must equal the file name")
    for k, allowed in (
        ("kind", KINDS),
        ("market", tuple(MARKETS)),
        ("verdict", tuple(VERDICTS)),
        ("confidence", tuple(CONFIDENCE)),
    ):
        if d[k] not in allowed:
            raise ContentError(f"{file_id}: {k} {d[k]!r} is not allowed")
    report = d.get("report")
    if report is not None and report != f"reports/{sid}.md":
        raise ContentError(f"{file_id}: report must be null or reports/{sid}.md")
    placeholder = d.get("placeholder", False)
    if not isinstance(placeholder, bool):
        raise ContentError(f"{file_id}: placeholder must be true or false")
    sec = _sections(body, file_id)
    if "Summary" not in sec or "What it means for you" not in sec:
        raise ContentError(f"{file_id}: Summary and What it means for you are required")
    if not placeholder and ("Key numbers" not in sec or "How sure are we?" not in sec):
        raise ContentError(f"{file_id}: a finished card needs Key numbers and How sure are we?")
    bullets = []
    for ln in sec["Summary"]:
        if ln.startswith("- "):
            bullets.append(ln[2:].strip())
        elif ln.startswith("  ") and bullets:
            bullets[-1] += " " + ln.strip()
        elif ln.strip():
            raise ContentError(f"{file_id}: the summary is a list of '- ' bullets")
    head, numbers = _table(sec.get("Key numbers", []), file_id)
    return Study(
        sid,
        _text(d, "title", file_id),
        _day(d["date"], file_id, optional=True),
        d["kind"],
        d["market"],
        d["verdict"],
        _text(d, "verdict_note", file_id, optional=True),
        _text(d, "question", file_id),
        _text(d, "answer", file_id),
        _int(d, "trials", file_id),
        _int(d, "n_total", file_id),
        _int(d, "ledger_seq", file_id),
        d["confidence"],
        report,
        placeholder,
        tuple(bullets),
        numbers,
        _paragraph(sec["What it means for you"]),
        _paragraph(sec.get("How sure are we?", [])),
        head,
    )


def check_highlights(raw: object) -> dict[str, Any]:
    d = _keys(raw, HL_TOP, HL_TOP, "highlights.yaml")
    _day(d["checked"], "highlights.yaml: checked")
    if _int(d, "trials_total", "highlights.yaml") is None:
        raise ContentError("highlights.yaml: trials_total is required")
    _int(d, "trials_ledger_seq", "highlights.yaml")
    _text(d, "footer", "highlights.yaml")
    items = _list(d["items"], "highlights.yaml: items")
    ids = set()
    for i, it in enumerate(items):
        w = f"highlights.yaml item {i + 1}"
        x = _keys(it, HL_ITEM, HL_ITEM_REQUIRED, w)
        if not isinstance(x["id"], str) or not ID_RE.match(x["id"]) or x["id"] in ids:
            raise ContentError(f"{w}: id missing, malformed or repeated")
        ids.add(x["id"])
        if x["slot"] not in SLOTS or x["chip"] not in CHIPS:
            raise ContentError(f"{w}: slot or chip not allowed")
        for k in ("line", "why", "do"):
            _text(x, k, w)
        if not all(isinstance(s, str) for s in _list(x["sources"], w)):
            raise ContentError(f"{w}: sources must be study ids")
        _day(x.get("review_by"), f"{w}: review_by", optional=True)
    return d


def check_dates(raw: object) -> list[dict[str, Any]]:
    d = _keys(raw, DATES_TOP, DATES_TOP, "dates.yaml")
    out = []
    for i, it in enumerate(_list(d["items"], "dates.yaml: items")):
        w = f"dates.yaml item {i + 1}"
        x = _keys(it, DATE_ITEM, DATE_REQUIRED, w)
        _day(x["day"], w)
        if x["kind"] not in DATE_KINDS:
            raise ContentError(f"{w}: kind not allowed")
        for k in ("title", "detail"):
            _text(x, k, w)
        for k in ("do", "ref"):
            _text(x, k, w, optional=True)
        out.append(x)
    return out


def check_testing(raw: object) -> dict[str, Any]:
    d = _keys(raw, TESTING_TOP, TESTING_TOP, "testing.yaml")
    _text(d, "intro", "testing.yaml")
    _day(d["first_decision"], "testing.yaml: first_decision")
    for g in _list(d["groups"], "testing.yaml: groups"):
        gg = _keys(g, GROUP_KEYS, GROUP_KEYS, "testing.yaml group")
        for ln in _list(gg["lines"], "testing.yaml group lines"):
            _keys(ln, LINE_KEYS, LINE_REQUIRED, "testing.yaml line")
    info = _keys(d["info_lines"], INFO_KEYS, INFO_KEYS, "testing.yaml info_lines")
    for ln in _list(info["lines"], "testing.yaml info lines"):
        _keys(ln, LINE_KEYS, LINE_REQUIRED, "testing.yaml info line")
    ret = _keys(d["retiring"], RETIRING_KEYS, RETIRING_KEYS, "testing.yaml retiring")
    _day(ret["day"], "testing.yaml: retiring day")
    _list(ret["lines"], "testing.yaml retiring lines")
    if not all(isinstance(r, str) for r in _list(d["rules"], "testing.yaml rules")):
        raise ContentError("testing.yaml: rules are text")
    ar = _keys(d["archives"], ARCHIVES_KEYS, ARCHIVES_KEYS, "testing.yaml archives")
    for it in _list(ar["items"], "testing.yaml archives"):
        _keys(it, ARCHIVE_KEYS, ARCHIVE_REQUIRED, "testing.yaml archive")
    for it in _list(d["in_progress"] or [], "testing.yaml in_progress"):
        _keys(it, PROGRESS_KEYS, PROGRESS_KEYS, "testing.yaml in_progress")
    return d


def check_glossary(raw: object) -> list[dict[str, Any]]:
    d = _keys(raw, GLOSSARY_TOP, GLOSSARY_TOP, "glossary.yaml")
    out = []
    for i, it in enumerate(_list(d["terms"], "glossary.yaml: terms")):
        w = f"glossary.yaml term {i + 1}"
        x = _keys(it, TERM_KEYS, TERM_REQUIRED, w)
        _text(x, "term", w)
        _text(x, "means", w)
        if not all(isinstance(a, str) for a in _list(x.get("also", []), w)):
            raise ContentError(f"{w}: also must be text")
        out.append(x)
    return out


_CACHE: dict[str, tuple[tuple[tuple[str, int, int], ...], Content]] = {}


def _signature(root: Path) -> tuple[tuple[str, int, int], ...]:
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            st = p.stat()
            out.append((p.relative_to(root).as_posix(), st.st_mtime_ns, st.st_size))
    return tuple(out)


def load(root: Path | None) -> Content:
    """Every content file under ``root``, each failing on its own; cached per process
    (re-read only when a file changes)."""
    if root is None or not root.is_dir():
        return Content(errors=["docs/research (not on this server)"])
    sig = _signature(root)
    hit = _CACHE.get(str(root))
    if hit is not None and hit[0] == sig:
        return hit[1]
    c = _load(root)
    _CACHE[str(root)] = (sig, c)
    return c


def _yaml(root: Path, name: str, c: Content, check: Callable[[object], Any]) -> Any:
    try:
        return check(load_yaml(_read(root / name)))
    except Exception:
        c.errors.append(name)
        return None


def _load(root: Path) -> Content:
    c = Content()
    c.highlights = _yaml(root, "highlights.yaml", c, check_highlights)
    c.dates = _yaml(root, "dates.yaml", c, check_dates) or []
    c.testing = _yaml(root, "testing.yaml", c, check_testing)
    c.glossary = _yaml(root, "glossary.yaml", c, check_glossary) or []
    sdir = root / "studies"
    for p in sorted(sdir.glob("*.md")) if sdir.is_dir() else []:
        try:
            s = parse_study(_read(p), p.stem)
        except Exception:
            c.errors.append(f"studies/{p.name}")
            c.bad_studies.append(p.stem if ID_RE.match(p.stem) else "?")
            continue
        c.studies[s.id] = s
        if s.report:
            try:
                c.reports[s.id] = _read(root / s.report)
            except Exception:
                c.errors.append(s.report)
    if c.highlights is not None:
        missing = [s for it in c.highlights["items"] for s in it["sources"] if s not in c.studies]
        if missing and not c.bad_studies:
            c.errors.append("highlights.yaml")
            c.highlights = None
    return c


def today_for(src: Any, v: Any) -> date:
    """The research content is real in the demo too, so the demo uses the real date."""
    if getattr(src, "demo", False):
        return datetime.now(ASX_TZ).date()
    now: datetime = v.now
    return now.astimezone(ASX_TZ).date()


def research_dir(src: Any) -> Path | None:
    rd = getattr(src, "research_dir", None)
    if rd is not None:
        return Path(rd)
    fd = getattr(src, "forecast_dir", None)  # the config folder: docs/ sits beside it
    return None if fd is None else Path(fd).parent / "docs" / "research"


# ---------------------------------------------------------------- the trial count


@dataclass(frozen=True)
class Trials:
    n: int | None
    seq: int | None
    live: bool  # from the record's ledger (else the highlights fallback)
    asof: date | None = None
    behind: bool = False  # the record has more tests than any study card


def ledger_trials(path: Path | None) -> tuple[int, int | None] | None:
    """(n_trials, seq) of the last ledger entry carrying an integer ``n_trials``, read
    from the last 256 KB; a malformed line is skipped. None: no file or no such entry."""
    if path is None:
        return None
    try:
        with path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - LEDGER_TAIL))
            data = fh.read(LEDGER_TAIL)
    except OSError:
        return None
    lines = data.split(b"\n")
    if size > LEDGER_TAIL:
        lines = lines[1:]  # the first line is cut
    for raw in reversed(lines):
        if not raw.strip():
            continue
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        n = d.get("n_trials")
        if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
            seq = d.get("seq")
            return n, seq if isinstance(seq, int) and not isinstance(seq, bool) else None
    return None


def trials(c: Content, ledger: Path | None) -> Trials:
    cards = max((s.n_total for s in c.studies.values() if s.n_total is not None), default=None)
    live = ledger_trials(ledger)
    if live is not None:
        n, seq = live
        return Trials(n, seq, True, None, cards is not None and n > cards)
    h = c.highlights or {}
    n0 = h.get("trials_total")
    seq0 = h.get("trials_ledger_seq")
    return Trials(
        n0 if isinstance(n0, int) else None,
        seq0 if isinstance(seq0, int) else None,
        False,
        h.get("checked") if isinstance(h.get("checked"), date) else None,
    )


def trials_text(t: Trials) -> str:
    if t.n is None:
        return "tests not counted"
    if t.live:
        return f"{t.n:,} tests counted" + (f" · record entry {t.seq}" if t.seq is not None else "")
    return f"{t.n:,} tests counted · as of {fday(t.asof)}" if t.asof else f"{t.n:,} tests counted"


# ---------------------------------------------------------------- Health


@dataclass(frozen=True)
class Status:
    state: str  # ok | due | behind | error
    text: str


def status(c: Content, t: Trials, today: date) -> Status:
    if c.errors:
        return Status("error", f"Could not read: {', '.join(c.errors[:4])}")
    if t.behind:
        cards = max(s.n_total or 0 for s in c.studies.values())
        return Status("behind", f"{BEHIND}: {t.n:,} tests in the record, {cards:,} in the cards")
    due = sorted(
        d
        for d in (it.get("review_by") for it in (c.highlights or {}).get("items", []))
        if isinstance(d, date) and d < today
    )
    if due:
        return Status("due", f"A highlight is due a re-check since {fday(due[0])}")
    h = c.highlights or {}
    return Status("ok", f"Checked {fday(h.get('checked'))} · {trials_text(t)}")


def status_for(src: Any, v: Any) -> Status:
    c = load(research_dir(src))
    return status(c, trials(c, getattr(src, "ledger", None)), today_for(src, v))


# ---------------------------------------------------------------- safe rendering


def fday(d: object, weekday: bool = False) -> str:
    if not isinstance(d, date):
        return "\u2013"
    return f"{d:%a %-d %b %Y}" if weekday else f"{d:%-d %b %Y}"


def when_text(it: Mapping[str, Any]) -> str:
    """A date, or for ``kind: window`` an honest "about late Feb 2027" (never a false day)."""
    d = it["day"]
    if it.get("kind") != "window":
        return fday(d, weekday=True)
    if d.day == 1:
        return f"about {d:%b %Y}"
    part = "early" if d.day <= 10 else ("mid" if d.day <= 20 else "late")
    return f"about {part} {d:%b %Y}"


_BOLD = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str, link: Linker | None = None) -> str:
    """Escape first; then glossary links (our own markup) and ``**bold**``."""
    s = e(text)
    if link is not None:
        s = link(s)
    return _BOLD.sub(r"<b>\1</b>", s)


def research_md(text: str) -> str:
    """The safe Markdown subset of BF-D89: the whole text is escaped first, then only
    ``## `` headings, ``- `` bullets, pipe tables, blank-line paragraphs and ``**bold**``
    are recognised. Nothing in a content file can emit a tag of its own."""
    out: list[str] = []
    para: list[str] = []
    bullets: list[str] = []
    rows: list[list[str]] = []

    def b(s: str) -> str:
        return _BOLD.sub(r"<b>\1</b>", s)

    def flush() -> None:
        if para:
            out.append(f"<p>{b(' '.join(para))}</p>")
            para.clear()
        if bullets:
            out.append("<ul>" + "".join(f"<li>{b(x)}</li>" for x in bullets) + "</ul>")
            bullets.clear()
        if rows:
            head, *rest = rows
            out.append(
                "<div class='tscroll'><table><thead><tr>"
                + "".join(f"<th>{b(x)}</th>" for x in head)
                + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{b(x)}</td>" for x in r) + "</tr>" for r in rest)
                + "</tbody></table></div>"
            )
            rows.clear()

    for raw in e(text).splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            flush()
            out.append(f"<h2>{b(line[3:].strip())}</h2>")
        elif line.startswith("|"):
            if para or bullets:
                flush()
            cells = [x.strip() for x in line.strip("|").split("|")]
            if not all(set(x) <= set("-: ") for x in cells):
                rows.append(cells)
        elif line.startswith("- "):
            if para or rows:
                flush()
            bullets.append(line[2:].strip())
        elif not line.strip():
            flush()
        else:
            if rows or bullets:
                flush()
            para.append(line.strip())
    flush()
    return "".join(out)


def slug(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


class Linker:
    """Dotted-underlines the first use of each glossary term on a page (one pass over
    escaped text, so a link is never nested or put inside markup)."""

    def __init__(self, terms: Sequence[Mapping[str, Any]]) -> None:
        self.to: dict[str, str] = {}
        for t in terms:
            s = slug(str(t["term"]))
            for raw in (t["term"], *t.get("also", [])):
                w = str(raw)
                if len(w) >= 3 and w.lower() not in self.to:
                    self.to[w.lower()] = s
        words = sorted(self.to, key=len, reverse=True)
        self.rx = (
            re.compile(
                r"(?<![\w-])(" + "|".join(re.escape(e(w)) for w in words) + r")(s?)(?![\w-])", re.I
            )
            if words
            else None
        )
        self.used: set[str] = set()

    def __call__(self, escaped: str) -> str:
        if self.rx is None:
            return escaped

        def sub(m: re.Match[str]) -> str:
            s = self.to.get(m.group(1).lower(), "")
            if not s or s in self.used:
                return m.group(0)
            self.used.add(s)
            return f'<a class="gl" href="/research/glossary#{s}">{m.group(0)}</a>'

        return self.rx.sub(sub, escaped)


def chip(kind: str, note: str = "", table: Mapping[str, tuple[str, str]] = CHIPS) -> str:
    label, cls = table.get(kind, (kind, "rc-mixed"))
    n = f'<span class="rnote"> · {e(note)}</span>' if note else ""
    return f'<span class="rchip {cls}">{e(label)}</span>{n}'


def _fill(text: str, t: Trials) -> str:
    return text.replace("{trials}", f"{t.n:,}" if t.n is not None else "all the")


SEG = (
    ("highlights", "/research", "Highlights"),
    ("library", "/research/library", "Library"),
    ("testing", "/research/testing", "Testing"),
    ("dates", "/research/dates", "Dates"),
)


def _head(active: str) -> str:
    seg = "".join(
        f'<a{" class=on" if k == active else ""} href="{h}" data-nav'
        f"{' aria-current=page' if k == active else ''}>{lab}</a>"
        for k, h, lab in SEG
    )
    return backlink("/", "Home") + "<h1>Research</h1>" + f'<div class="seg rseg">{seg}</div>'


def _foot(c: Content) -> str:
    text = (c.highlights or {}).get(
        "footer"
    ) or "General information, not personal financial advice."
    return f'<p class="rfoot">{e(text)} · <a href="/research/glossary">Glossary</a></p>'


def _unreadable(name: str) -> str:
    return (
        f'<li class="rbad"><span class="rchip rc-closed">{e(COULD_NOT_READ)}</span>'
        f'<span class="sub">{e(name)}</span></li>'
    )


def _behind(t: Trials) -> str:
    if not t.behind:
        return ""
    return (
        f'<p class="note info">{e(BEHIND)}: the cards are updated by a content commit '
        "after each study.</p>"
    )


# ---------------------------------------------------------------- highlights


def next_date(c: Content, today: date) -> dict[str, Any] | None:
    for it in sorted(c.dates, key=lambda x: x["day"]):
        if it["kind"] != "decision" and it["day"] >= today:
            return it
    return None


def resolved(c: Content, t: Trials, today: date) -> list[dict[str, Any]]:
    """The highlight items with ``{trials}`` filled and the ``next`` slot computed."""
    out = []
    for it in (c.highlights or {}).get("items", []):
        x = dict(it)
        if x["slot"] == "next":
            nd = next_date(c, today)
            if nd is None:
                x.update(line="No dates set", why="", do="")
            else:
                x.update(
                    line=f"Next: {when_text(nd)} — {nd['title']}",
                    why=nd["detail"],
                    do=nd.get("do") or "",
                )
        for k in ("line", "why", "do"):
            x[k] = _fill(str(x[k]), t)
        out.append(x)
    return out


def _sources(c: Content, ids: Sequence[str]) -> str:
    links = [
        f'<a href="/research/library/{s}" data-nav>{e(c.studies[s].title)}</a>'
        for s in ids
        if s in c.studies
    ]
    return f'<p class="caption">From: {" · ".join(links)}</p>' if links else ""


def highlights_page(c: Content, t: Trials, today: date) -> str:
    lk = Linker(c.glossary)
    h = c.highlights
    parts = [_head("highlights")]
    if h is None:
        parts.append(f'<ul class="list">{_unreadable("highlights.yaml")}</ul>')
        return "".join(parts) + _foot(c)
    parts.append(f'<p class="caption">Checked {fday(h["checked"])} · {e(trials_text(t))}</p>')
    parts.append(_behind(t))
    for it in resolved(c, t, today):
        due = it.get("review_by")
        cap = (
            f'<p class="rdue">Due a re-check since {fday(due)}</p>'
            if isinstance(due, date) and due < today
            else ""
        )
        # what to do is on the card itself (the owner's first question); the reason folds
        do = f'<p class="hdo"><span>What to do</span>{inline(it["do"], lk)}</p>' if it["do"] else ""
        why = ""
        if it["why"]:
            why = (
                '<details class="why"><summary>Why</summary>'
                + f"<p>{inline(it['why'], lk)}</p>"
                + _sources(c, it["sources"])
                + "</details>"
            )
        elif it["do"]:
            why = _sources(c, it["sources"])
        parts.append(
            f'<section class="rhl" id="{e(it["id"])}"><p>{chip(it["chip"])}</p>'
            f'<p class="hline">{inline(it["line"], lk)}</p>{cap}{do}{why}</section>'
        )
    return "".join(parts) + _foot(c)


def home_card(c: Content, t: Trials, today: date) -> str:
    """Home's "What we know" (under the scoreboard): the plan, core and next lines."""
    items = {
        it["slot"]: it for it in resolved(c, t, today) if it["slot"] in ("plan", "core", "next")
    }
    if not items:
        return ""
    lis = "".join(
        f"<li>{inline(items[k]['line'])}</li>" for k in ("plan", "core", "next") if k in items
    )
    more = f'<a class="rmore" href="/research" data-nav>All highlights{chev()}</a>'
    return section("What we know", f'<ul class="list know">{lis}</ul>{more}', "knowcard")


def home_card_for(src: Any, v: Any) -> str:
    c = load(research_dir(src))
    return home_card(c, trials(c, getattr(src, "ledger", None)), today_for(src, v))


# ---------------------------------------------------------------- library


def _order(studies: Iterable[Study]) -> list[Study]:
    """Newest first by date (date order only, never by result); undated last."""
    return sorted(
        studies, key=lambda s: (s.date is None, -(s.date.toordinal() if s.date else 0), s.id)
    )


def _card(s: Study, compact: bool = False) -> str:
    meta = " · ".join(x for x in (fday(s.date) if s.date else "", MARKETS[s.market]) if x)
    ans = "" if compact else f'<span class="ans">{inline(s.answer)}</span>'
    return (
        f'<li><a class="rcard" href="/research/library/{s.id}" data-nav><span class="grow">'
        f'<span class="caption">{e(meta)}</span><b>{e(s.title)}</b>{ans}'
        f"<span>{chip(s.verdict, s.verdict_note, VERDICTS)}</span></span>{chev()}</a></li>"
    )


def _groups(c: Content, f: str, compact: bool = False) -> str:
    mk = FILTER_MARKET.get(f)
    shown = [s for s in c.studies.values() if mk is None or s.market == mk]
    running = _order(s for s in shown if s.placeholder)
    done = _order(s for s in shown if not s.placeholder)
    out = ""
    if running:
        out += section(
            "Still running",
            '<ul class="list">' + "".join(_card(s, compact) for s in running) + "</ul>",
        )
    bad = "".join(_unreadable(f"studies/{b}.md") for b in c.bad_studies) if mk is None else ""
    if done or bad:
        out += section(
            "Finished",
            '<ul class="list">' + bad + "".join(_card(s, compact) for s in done) + "</ul>",
        )
    return out or "<p class='muted'>No studies here yet.</p>"


def library_page(c: Content, t: Trials, f: str) -> str:
    f = f if f in FILTERS else "all"
    chips = "".join(
        f'<a class="chip{" on" if k == f else ""}" href="/research/library?f={k}" '
        f"data-nav>{e(lab)}</a>"
        for k, lab in FILTERS.items()
    )
    return (
        _head("library")
        + _behind(t)
        + f'<div class="chips">{chips}</div>'
        + _groups(c, f)
        + _foot(c)
    )


def _tests_line(s: Study) -> str:
    if s.placeholder and s.trials is None:
        return "Tests: counted when it reports"
    bits = []
    if s.trials is not None:
        bits.append(
            f"Tests in this study: {s.trials:,}" if s.trials else "Tests in this study: none"
        )
    if s.n_total is not None:
        bits.append(f"running total after it: {s.n_total:,}")
    if s.ledger_seq is not None:
        bits.append(f"record entry {s.ledger_seq}")
    return " · ".join(bits)


def study_page(c: Content, sid: str) -> str | None:
    s = c.studies.get(sid) if ID_RE.match(sid) else None
    if s is None:
        return None
    lk = Linker(c.glossary)
    meta = " · ".join(
        x for x in (fday(s.date) if s.date else "In progress", MARKETS[s.market]) if x
    )
    parts = [
        backlink("/research/library", "Library"),
        f"<h1>{e(s.title)}</h1>",
        f'<p class="caption">{e(meta)}</p><p>{chip(s.verdict, s.verdict_note, VERDICTS)}</p>',
        f'<p class="rans">{inline(s.answer, lk)}</p>',
    ]
    # the reader's order: the answer, what it means for you, how sure, then the detail
    parts.append(section("What it means for you", f"<p>{inline(s.means, lk)}</p>", "rmeans"))
    grade = CONFIDENCE[s.confidence]
    meter = (
        f'<span class="conf c{CONF_STEPS[s.confidence]}" aria-hidden="true">'
        "<span></span><span></span><span></span></span>"
    )
    if s.sure:
        parts.append(
            f'<details class="rsure"><summary>{meter}<span>How sure are we? '
            f'<b>{e(grade)}</b></span><span class="sp"></span>{chev()}</summary>'
            f"<p>{inline(s.sure)}</p></details>"
        )
    else:
        parts.append(
            f'<p class="rsure nofold">{meter}<span>How sure are we? <b>{e(grade)}</b></span></p>'
        )
    if s.summary:
        parts.append(
            section(
                "In short",
                '<ul class="bul">'
                + "".join(f"<li>{inline(b, lk)}</li>" for b in s.summary)
                + "</ul>",
            )
        )
    if s.numbers:
        rows = "".join(
            f'<tr><td>{inline(a)}</td><td class="r{" nw" if len(b) <= NOWRAP else ""}">'
            f"{inline(b)}</td></tr>"
            for a, b in s.numbers
        )
        cap = s.numbers_head if s.numbers_head.lower() != "what" else ""
        cap = cap[len("What") :].strip(" ()") if cap.startswith("What (") else cap
        head = f'<p class="caption">{inline(cap)}</p>' if cap else ""
        table = f'<table class="rnum"><tbody>{rows}</tbody></table>'
        parts.append(section("Key numbers", head + table))
    foot = _tests_line(s)
    rep = (
        f'<a class="rmore" href="/research/report/{s.id}" data-nav>Full report{chev()}</a>'
        if s.report and s.id in c.reports
        else f'<p class="caption">Full report: {e(ONEDRIVE)} \u203a {e(s.id)}</p>'
    )
    parts.append(f'<p class="caption">{e(foot)}</p>{rep}' if foot else rep)
    detail = "".join(parts)
    side = f'<div class="rside">{_groups(c, "all", compact=True)}</div>'
    return f'<div class="rtwo">{side}<div class="rdetail">{detail}</div></div>' + _foot(c)


def report_page(c: Content, sid: str) -> str | None:
    s = c.studies.get(sid) if ID_RE.match(sid) else None
    if s is None or s.id not in c.reports:
        return None
    return (
        backlink(f"/research/library/{s.id}", "Study")
        + f"<h1>{e(s.title)}</h1>"
        + f'<div class="doc">{research_md(c.reports[s.id])}</div>'
        + _foot(c)
    )


# ---------------------------------------------------------------- what we're testing


def _result(
    lid: str, main: bool, lines: Sequence[Any] | None, first: date | None, today: date
) -> str:
    """The paper result of one line: inside its closed fold-out only, never coloured."""
    from trader.app_pages import aud, day, pct

    if main:
        return (
            "<p>The main line's result after costs is the scoreboard on "
            '<a href="/" data-nav>Home</a>.</p>'
        )
    if lines is None:
        return (
            "<p class='muted'>Not collected yet: the research record moves to this server "
            "after 30 Nov.</p>"
        )
    ln = next((x for x in lines if x.id == lid), None)
    if ln is None or ln.ret is None:
        before = first is not None and today <= first
        return (
            "<p>Not started"
            + (f": the first decision is on {fday(first)}." if before else ".")
            + "</p>"
        )
    cap = f"{aud(ln.capital, dp=0)} book · " if ln.capital else ""
    st = f"since {day(ln.start)}" if ln.start else "since start"
    return (
        f"<p>{pct(ln.ret)} {e(st)} · {pct(ln.vs_a200)} against A200</p>"
        f'<p class="caption">{e(cap)}before fixed costs · from the research record'
        + (f", {e(day(ln.asof))}" if ln.asof else "")
        + "</p>"
    )


def _line_row(
    ln: Mapping[str, Any],
    info: bool,
    lines: Sequence[Any] | None,
    first: date | None,
    today: date,
    lk: Linker,
) -> str:
    main = ln.get("label") == "main"
    tag = "" if main else '<span class="rchip rc-info">Information only</span>'
    if info:
        res = (
            "<p>Holds no money: a reading, not a result. "
            "Nothing to show before its first reading.</p>"
        )
    else:
        res = _result(str(ln["id"]), main, lines, first, today)
    return (
        f'<li class="tline"><p class="tname"><b>{e(ln["name"])}</b> {tag}</p>'
        f"<p>{inline(ln['what'], lk)}</p>"
        f'<p class="caption tread">First honest reading: {e(ln["reading"])}</p>'
        f'<details class="pres"><summary>Paper result so far ({LUCK})</summary>{res}</details></li>'
    )


def lines_page(
    c: Content,
    today: date,
    lines: Sequence[Any] | None = None,
    fresh: Sequence[Any] = (),
    retired_shown: bool = False,
) -> str:
    tdoc = c.testing
    parts = [_head("testing")]
    if tdoc is None:
        parts.append(f'<ul class="list">{_unreadable("testing.yaml")}</ul>')
        return "".join(parts) + _foot(c)
    lk = Linker(c.glossary)
    first = tdoc["first_decision"]
    parts.append(f'<p class="note info">{inline(tdoc["intro"], lk)}</p>')
    jump = [(f"g{i}", str(g["name"])) for i, g in enumerate(tdoc["groups"])]
    jump += [("ginfo", "Information lines"), ("grules", "The rules"), ("gdata", "Data")]
    parts.append(
        '<nav class="chips rjump" aria-label="On this page">'
        + "".join(f'<a class="chip" href="#{i}">{e(n)}</a>' for i, n in jump)
        + "</nav>"
    )

    def anchored(html: str, i: str) -> str:
        return html.replace("<section ", f'<section id="{i}" ', 1)

    for i, g in enumerate(tdoc["groups"]):
        rows = "".join(_line_row(ln, False, lines, first, today, lk) for ln in g["lines"])
        parts.append(
            anchored(
                section(
                    g["name"],
                    f'<p class="caption">{inline(g["note"])}</p><ul class="list">{rows}</ul>',
                ),
                f"g{i}",
            )
        )
    il = tdoc["info_lines"]
    rows = "".join(_line_row(ln, True, lines, first, today, lk) for ln in il["lines"])
    parts.append(
        anchored(
            section(
                "Information lines",
                f'<p class="caption">{inline(il["note"])}</p><ul class="list">{rows}</ul>',
            ),
            "ginfo",
        )
    )
    ret = tdoc["retiring"]
    names = ", ".join(str(x) for x in ret["lines"])
    title = f"Retired {fday(ret['day'])}" if retired_shown else f"Retiring {fday(ret['day'])}"
    parts.append(
        section(
            title,
            f"<p><b>{e(names)}</b></p><p>{inline(ret['note'])}</p>"
            f'<p class="caption">{inline(ret["also"])}</p>',
        )
    )
    parts.append(
        anchored(
            section(
                "The rules",
                '<ul class="bul">'
                + "".join(f"<li>{inline(r, lk)}</li>" for r in tdoc["rules"])
                + "</ul>",
            ),
            "grules",
        )
    )
    by_key = {getattr(f, "key", ""): f for f in fresh}
    items = []
    for a in tdoc["archives"]["items"]:
        fr = by_key.get(a.get("health_key") or "")
        last = (
            f'<p class="caption">Last collected: {e(fr.last)}</p>'
            if fr is not None and fr.status not in ("off", "new")
            else ""
        )
        items.append(
            f"<li><b>{e(a['name'])}</b><p>{inline(a['what'])}</p>"
            f'<p class="caption">Since {e(a["since"])} · {e(a["reading"])}</p>{last}</li>'
        )
    parts.append(
        anchored(
            section(
                "Data we are collecting",
                f'<p class="caption">{inline(tdoc["archives"]["note"])}</p>'
                f'<ul class="list">{"".join(items)}</ul>',
            ),
            "gdata",
        )
    )
    prog = [p for p in tdoc["in_progress"] or [] if p["study"] in c.studies]
    if prog:
        parts.append(
            section(
                "Still running",
                '<ul class="list">'
                + "".join(
                    f'<li><a class="rowlink" href="/research/library/{p["study"]}" data-nav>'
                    f'<span class="grow">{e(p["name"])}</span>{chev()}</a></li>'
                    for p in prog
                )
                + "</ul>",
            )
        )
    return "".join(parts) + _foot(c)


# ---------------------------------------------------------------- decisions and dates


def _tl(it: Mapping[str, Any], nxt: bool, lk: Linker | None) -> str:
    tag = ' <span class="rchip rc-date">Next</span>' if nxt else ""
    you = (
        f'<p class="you">You: {inline(it["do"])}</p>'
        if it.get("do") and it["kind"] != "decision"
        else ""
    )
    ref = f'<p class="caption">{e(it["ref"])}</p>' if it.get("ref") else ""
    d = when_text(it) if it["kind"] != "decision" else fday(it["day"])
    return (
        f'<li><p class="tday">{e(d)}{tag}</p>'
        f'<p class="h3">{e(it["title"])}</p><p>{inline(it["detail"], lk)}</p>{you}{ref}</li>'
    )


def dates_page(c: Content, today: date) -> str:
    lk = Linker(c.glossary)
    items = sorted(c.dates, key=lambda x: x["day"])
    coming = [x for x in items if x["kind"] != "decision" and x["day"] >= today]
    earlier = [x for x in items if x["kind"] != "decision" and x["day"] < today][::-1]
    decided = [x for x in items if x["kind"] == "decision"][::-1]
    parts = [_head("dates")]
    if "dates.yaml" in c.errors:
        parts.append(f'<ul class="list">{_unreadable("dates.yaml")}</ul>')
    up = "".join(_tl(x, i == 0, lk) for i, x in enumerate(coming))
    parts.append(
        section(
            "Coming up",
            f'<ul class="tlist">{up}</ul>' if up else "<p class='muted'>No dates set.</p>",
        )
    )
    if decided:
        parts.append(
            section(
                "Decided",
                '<ul class="tlist done">' + "".join(_tl(x, False, lk) for x in decided) + "</ul>",
            )
        )
    if earlier:
        parts.append(
            '<details class="about"><summary>Earlier</summary><ul class="tlist done">'
            + "".join(_tl(x, False, None) for x in earlier)
            + "</ul></details>"
        )
    return "".join(parts) + _foot(c)


# ---------------------------------------------------------------- glossary


def glossary_page(c: Content) -> str:
    rows = []
    for t in c.glossary:
        also = t.get("also") or []
        alt = f' <span class="sub">({e(", ".join(str(a) for a in also))})</span>' if also else ""
        rows.append(
            f'<dt id="{slug(str(t["term"]))}">{e(t["term"])}{alt}</dt><dd>{inline(t["means"])}</dd>'
        )
    body = (
        f'<dl class="gloss">{"".join(rows)}</dl>'
        if rows
        else f'<ul class="list">{_unreadable("glossary.yaml")}</ul>'
    )
    return backlink("/research", "Research") + "<h1>Glossary</h1>" + section("", body) + _foot(c)
