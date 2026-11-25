"""BF-D89: the research pages (Highlights, Library, Testing, Dates, Glossary). The
content tests run over docs/research/ in CI, so a bad content commit cannot merge. The
ledger and scorecard fixtures here are made up."""

from __future__ import annotations

import csv
import json
import random
import re
import runpy
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from trader import app_research as ar
from trader import ops_view as ov
from trader.journal import Journal
from trader.webui import e

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "docs" / "research"
WRITTEN = date(2026, 11, 25)  # the day these tests were written
BANNED = ("t-stat", "p-value", "bonferroni", "deflated", "sharpe", "cagr", "alpha", "drawdown",
          "percentile", "in-sample", "auc", "nw")  # fmt: skip
IMPERATIVE = ("Do", "Don't", "Keep", "Hold", "Set", "Read", "Approve", "Treat", "Expect", "Think",
              "Ask", "Wait", "Never", "Decide", "Put", "Check", "Leave", "Tap", "Use", "Stay")  # fmt: skip


def words(s: str) -> int:
    return len(s.split())


@pytest.fixture(scope="module")
def content() -> ar.Content:
    return ar._load(DIR)  # uncached: exactly what is in the repository


# ---------------------------------------------------------------- 1-8: the content


def test_BF_D89_content_loads_strictly(content: ar.Content) -> None:
    assert content.errors == [] and content.bad_studies == []
    files = sorted(p.stem for p in (DIR / "studies").glob("*.md"))
    assert sorted(content.studies) == files and len(files) >= 13
    for s in content.studies.values():
        assert ar.ID_RE.match(s.id) and s.verdict in ar.VERDICTS
        assert s.kind in ar.KINDS and s.confidence in ar.CONFIDENCE and s.market in ar.MARKETS
        assert s.report is None  # owner decision: the full reports stay on OneDrive
    assert content.highlights is not None and content.testing is not None
    assert content.dates and content.glossary
    # an unknown key, a bad enum or an id that differs from the file name is an error
    good = (DIR / "studies" / "research_big.md").read_text()
    for bad in (good.replace("confidence: solid", "confidence: solid\nrank: 1"),
                good.replace("verdict: doesnt", "verdict: great"),
                good.replace("id: research_big", "id: research_bigger")):  # fmt: skip
        with pytest.raises(ar.ContentError):
            ar.parse_study(bad, "research_big")
    with pytest.raises(ar.ContentError):
        ar.check_glossary({"version": 1, "terms": [{"term": "X", "means": "Y", "extra": 1}]})


def test_BF_D89_readability_limits(content: ar.Content) -> None:
    h = content.highlights
    assert h is not None
    for it in h["items"]:
        if it["slot"] == "next":
            continue
        assert words(it["line"]) <= 20, it["id"]
        assert len(re.findall(r"[.!?](?:\s|$)", it["line"])) <= 1, it["id"]
        assert words(it["why"]) <= 70 and words(it["do"]) <= 30, it["id"]
    for s in content.studies.values():
        assert words(s.title) <= 12 and words(s.answer) <= 30, s.id
        assert len(s.verdict_note.split()) <= 4, s.id
        if not s.placeholder:
            assert 4 <= len(s.summary) <= 7, s.id
            assert 3 <= len(s.numbers) <= 8, s.id
        assert all(words(b) <= 35 for b in s.summary), s.id
        assert words(s.means) <= 70, s.id
        assert re.search(r"\byou(r)?\b", s.means, re.I), s.id  # second person
        last = re.split(r"(?<=[.;])\s+", s.means.strip())[-1]
        assert "nothing to do" in s.means.lower() or last.split()[0] in IMPERATIVE, s.id
    for t in content.glossary:
        assert words(t["means"]) <= 30, t["term"]
    for p in DIR.rglob("*"):
        if p.is_file():
            assert "!" not in p.read_text().replace("<!", ""), p.name  # no exclamation marks


def test_BF_D89_highlight_slots(content: ar.Content) -> None:
    items = (content.highlights or {})["items"]
    assert 5 <= len(items) <= 8
    slots = [it["slot"] for it in items]
    for s in ar.FIXED_SLOTS:
        assert slots.count(s) == 1, s
    assert slots.count("finding") <= 3
    order = [ar.SLOTS.index(s) for s in slots]
    assert order == sorted(order)  # editorial order: what to do first, detail after
    for it in items:
        assert all(s in content.studies for s in it["sources"]), it["id"]


def test_BF_D89_highlight_numbers_trace_to_their_cards(content: ar.Content) -> None:
    tok = re.compile(r"[+\u2212-]?\$[\d,]+(?:-[\d,]+)?|[+\u2212-]?\d[\d.,-]*%")
    for it in (content.highlights or {})["items"]:
        text = " ".join(str(it[k]) for k in ("line", "why", "do"))
        src = " ".join((DIR / "studies" / f"{s}.md").read_text() for s in it["sources"])
        for raw in tok.findall(text):
            t = raw.rstrip(".,")
            assert t in src, (it["id"], t)


def _outside_sure(p: Path) -> str:
    text = p.read_text()
    if p.suffix == ".md":
        text = text.split("## How sure are we?")[0]
    return text


def test_BF_D89_banned_words_only_inside_how_sure() -> None:
    for p in DIR.rglob("*"):
        if not p.is_file() or "reports" in p.parts:
            continue
        low = _outside_sure(p).lower()
        for w in BANNED:
            assert not re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", low), (p.name, w)


def test_BF_D89_privacy_lint() -> None:
    for p in DIR.rglob("*"):
        if p.is_dir():
            continue
        assert p.suffix in (".md", ".yaml"), p.name  # only content files
        assert p.stat().st_size <= 60 * 1024, p.name
        text = p.read_text()
        for bad in ("/tmp/", "scratchpad", "/home/", "@", "api_token", "A$", "```"):
            assert bad not in text, (p.name, bad)


def test_BF_D89_testing_lines_are_the_registered_lines(content: ar.Content) -> None:
    t = content.testing
    assert t is not None
    ids = [ln["id"] for g in t["groups"] for ln in g["lines"]]
    assert ids == ["BT_C6"] + [k for k, _, _ in ov.KEPT_LINES]
    assert tuple(t["retiring"]["lines"]) == ov.RETIRED_LINES
    assert t["retiring"]["day"] == ov.RETIRED_ON
    assert ar.LUCK == ov.LUCK
    assert t["intro"].endswith(ov.LUCK + ".")


def test_BF_D89_dates_sorted_and_next_computed(content: ar.Content) -> None:
    days = [d["day"] for d in content.dates]
    assert days == sorted(days)
    nd = ar.next_date(content, WRITTEN)
    assert nd is not None and nd["day"] >= WRITTEN
    t = ar.trials(content, None)
    nxt = next(it for it in ar.resolved(content, t, WRITTEN) if it["slot"] == "next")
    assert nxt["line"] == "Next: Mon 30 Nov 2026 — First paper decision"
    late = next(it for it in ar.resolved(content, t, date(2031, 1, 1)) if it["slot"] == "next")
    assert late["line"] == "No dates set" and late["why"] == ""
    assert "No dates set" in ar.dates_page(content, date(2031, 1, 1))
    win = {"day": date(2027, 2, 26), "kind": "window"}
    assert ar.when_text(win) == "about late Feb 2027"
    assert ar.when_text({"day": date(2027, 3, 1), "kind": "window"}) == "about Mar 2027"


# ---------------------------------------------------------------- 9-10: the renderer

EVIL = ["<script>alert(1)</script>", '<img src=x onerror="alert(1)">', "[x](javascript:alert(1))",
        "</section>", "&lt;b&gt; &amp;", "**<i>bold</i>**"]  # fmt: skip
TAG = re.compile(r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9]*)")


def test_BF_D89_research_md_escapes_everything() -> None:
    for x in EVIL:
        md = f"## {x}\n\n{x}\n\n- {x}\n- ok\n\n| a | {x} |\n|---|---|\n| {x} | 1 |\n\n**{x}**\n"
        out = ar.research_md(md)
        assert set(TAG.findall(out)) <= ar.ALLOWED_TAGS, (x, out)
        assert "<script" not in out and "onerror=" not in out.replace("onerror=&quot;", "")
        assert "javascript:" not in out or "href" not in out
        assert "<img" not in out and "</section>" not in out
    assert ar.research_md("**a** b") == "<p><b>a</b> b</p>"


def _study(field: str, value: str) -> str:
    text = (DIR / "studies" / "research_big.md").read_text()
    return text.replace(
        {"title": 'title: "Can big winners be caught in advance?"',
         "answer": "answer: \"No. The boldest",
         "body": "## What it means for you\n"}[field],
        value,
    )  # fmt: skip


def test_BF_D89_every_field_is_escaped(tmp_path: Path) -> None:
    for x in EVIL:
        root = tmp_path / str(abs(hash(x)))
        shutil.copytree(DIR, root)
        sp = root / "studies" / "research_big.md"
        text = sp.read_text()
        text = text.replace('title: "Can big winners be caught in advance?"',
                            f"title: {json.dumps(x)}")  # fmt: skip
        text = text.replace("## What it means for you\n", f"## What it means for you\n{x} ")
        text = text.replace("| Worst fall | 55% to 75% |", f"| {x} | {x} |")
        text = text.replace("## Summary\n", f"## Summary\n- {x}\n")
        sp.write_text(text)
        c = ar.load(root)
        assert c.errors == [], c.errors
        t = ar.trials(c, None)
        pages = [ar.study_page(c, "research_big") or "", ar.library_page(c, t, "all"),
                 ar.highlights_page(c, t, WRITTEN)]  # fmt: skip
        for out in pages:
            assert "<script" not in out and "<img" not in out and "<i>" not in out
            assert out.count("</section>") == out.count("<section")


def _broken(tmp_path: Path) -> Path:
    root = tmp_path / "broken"
    shutil.copytree(DIR, root)
    (root / "studies" / "research_us.md").write_text("---\nid: research_us\nnope: [\n---\n")
    (root / "glossary.yaml").write_text("terms: [")
    return root


# ---------------------------------------------------------------- 11-16: the screens


@pytest.fixture(scope="module")
def demo(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard_demo import build_demo
    from trader.journal import read_only_engine

    d = build_demo(tmp_path_factory.mktemp("d89") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{d.journal_path}"))
    return d, j


def _app(demo: Any, **kw: Any) -> Any:
    from trader.dashboard import Dashboard, Sources

    d, j = demo
    allowed = kw.pop("allowed", frozenset())
    src = Sources(j, index=d.index, sessions=lambda: d.sessions, today=lambda: d.last_day,
                  clock=lambda: d.now, demo=True, prices=d.prices, forecast_dir=REPO / "config",
                  scorecard=d.scorecard, info_dir=d.info_dir, info_enabled=True, **kw)  # fmt: skip
    return Dashboard(src, allowed_logins=allowed, action_logins=frozenset({"owner@example.test"}))


def _get(app: Any, path: str, who: str = "") -> tuple[int, str]:
    hdr = {"Tailscale-User-Login": who} if who else {}
    st, _, b = app.respond("GET", path, hdr)
    return st, b.decode()


ROUTES = ("/research", "/research/library", "/research/library?f=us", "/research/library?f=app",
          "/research/library/research_big", "/research/library/research_bw",
          "/research/testing", "/research/dates", "/research/glossary")  # fmt: skip


def test_BF_D89_routes_read_only_home_tab(demo: Any) -> None:
    app = _app(demo)
    for r in ROUTES:
        st, html = _get(app, r)
        assert st == 200, r
        assert 'class="tab on" data-nav data-tab="home"' in html, r
        st, _, _ = app.respond("POST", r.split("?")[0], {})
        assert st == 405, r
    for bad in ("/research/library/nope", "/research/library/Research_Big",
                "/research/library/../dashboard", "/research/library/%2e%2e%2fhighlights",
                "/research/library/research_big/x", "/research/report/research_big",
                "/research/nothing", "/research/library/" + "a" * 41):  # fmt: skip
        assert app.respond("GET", bad, {})[0] == 404, bad


def test_BF_D89_view_only_login_reads_everything_no_actions(demo: Any) -> None:
    app = _app(demo, allowed=frozenset({"viewer@example.test", "owner@example.test"}))
    for r in ROUTES:
        st, html = _get(app, r, "viewer@example.test")
        assert st == 200, r
        main = html[html.index("<main") : html.index("</main>")]
        assert "/act" not in main and "<form" not in html, r
    assert _get(app, "/research", "stranger@example.test")[0] == 403


def _scorecard(tmp_path: Path, seed: int) -> Path:
    p = tmp_path / f"sc{seed}" / "scorecard_latest.csv"
    p.parent.mkdir()
    books = [books[0] for _, _, books in ov.KEPT_LINES]
    rets = [random.Random(seed).uniform(-0.5, 0.9) for _ in books]
    random.Random(seed).shuffle(rets)
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["asof", "book", "kind", "capital", "nav", "return_since_start", "vs_a200"])
        for b, r in zip(books, rets, strict=True):
            w.writerow(["2027-01-29", b, "paper", 10000, round(10000 * (1 + r), 2), r, r - 0.01])
    return p


def test_BF_D89_testing_page_unranked_figures_folded(content: ar.Content, tmp_path: Path) -> None:
    t = content.testing
    assert t is not None
    names = [ln["name"] for g in t["groups"] for ln in g["lines"]]
    names += [ln["name"] for ln in t["info_lines"]["lines"]]
    for seed in (1, 2, 3):
        lines = ov.research_lines(_scorecard(tmp_path, seed), date(2027, 2, 1))
        html = ar.lines_page(content, date(2027, 2, 1), lines, (), True)
        pos = [html.index(f"<b>{n}</b>") for n in names]
        assert pos == sorted(pos)  # the registered order, whatever the results
        outside = re.sub(r"<details.*?</details>", "", html, flags=re.S)
        assert not re.search(r"\$\d|\d%", outside), seed  # no figure unless opened
        assert "against A200" in html  # the figures are there, folded
        assert html.count(f"Paper result so far ({ov.LUCK})") == len(names)
        assert "<select" not in html and "Sort" not in html
        assert not re.search(r"\b(ranked|leader|leaderboard|winner so far)\b", html, re.I)
        assert "Retired 31 Dec 2026" in html
    assert "Retiring 31 Dec 2026" in ar.lines_page(content, WRITTEN, None)
    assert "Not collected yet" in ar.lines_page(content, WRITTEN, None)


def _ledger(p: Path, rows: list[object], tail: str = "") -> Path:
    p.write_text("".join(json.dumps(r) + "\n" for r in rows) + tail)
    return p


def test_BF_D89_trial_count_live_fallback_behind(content: ar.Content, tmp_path: Path) -> None:
    lg = _ledger(tmp_path / "LEDGER.jsonl", [
        {"seq": 99, "n_trials": 3114}, {"seq": 100, "n_trials": 3117},
        {"seq": 101, "n_trials": 3147, "event": "x"}, {"seq": 102, "kind": "decision"}],
        tail='{"seq": 103, "n_trials": 9999')  # a corrupt last line is skipped  # fmt: skip
    t = ar.trials(content, lg)
    assert (t.n, t.seq, t.live, t.behind) == (3147, 101, True, False)
    assert ar.trials_text(t) == "3,147 tests counted · record entry 101"
    fb = ar.trials(content, tmp_path / "missing.jsonl")
    assert (fb.n, fb.live) == (3261, False)
    assert ar.trials_text(fb) == "3,261 tests counted · as of 25 Nov 2026"
    newer = _ledger(tmp_path / "L2.jsonl", [{"seq": 105, "n_trials": 3290}])
    tb = ar.trials(content, newer)
    assert tb.behind and ar.BEHIND in ar.highlights_page(content, tb, WRITTEN)
    assert ar.BEHIND in ar.library_page(content, tb, "all")
    assert ar.status(content, tb, WRITTEN).state == "behind"
    assert ar.status(content, t, WRITTEN).state == "ok"
    # a big file: only the tail is read; its first (cut) line is ignored
    big = tmp_path / "L3.jsonl"
    big.write_text(json.dumps({"seq": 1, "n_trials": 1, "pad": "x" * 300_000}) + "\n"
                   + json.dumps({"seq": 2, "n_trials": 2}) + "\n")  # fmt: skip
    assert ar.ledger_trials(big) == (2, 2)
    assert ar.ledger_trials(_ledger(tmp_path / "L4.jsonl", [{"n_trials": True}])) is None


def test_BF_D89_live_count_on_the_pages_and_health(demo: Any, tmp_path: Path) -> None:
    lg = _ledger(tmp_path / "LEDGER.jsonl", [{"seq": 105, "n_trials": 3290}])
    app = _app(demo, ledger=lg)
    st, html = _get(app, "/research")
    assert st == 200 and "3,290 tests counted · record entry 105" in html and ar.BEHIND in html
    st, html = _get(app, "/health")
    assert st == 200 and "Research content" in html and ">behind<" in html
    st, html = _get(_app(demo), "/research")
    assert "Checked 25 Nov 2026 · 3,261 tests counted · as of 25 Nov 2026" in html
    assert "Across 3,261 counted tests" in html  # {trials} filled


def test_BF_D89_review_by_past_is_due(content: ar.Content) -> None:
    t = ar.trials(content, None)
    html = ar.highlights_page(content, t, date(2027, 1, 6))
    assert "Due a re-check since 6 Jan 2027" not in html
    assert "Due a re-check since 5 Jan 2027" in html
    assert "Due a re-check" not in ar.highlights_page(content, t, WRITTEN)
    st = ar.status(content, t, date(2027, 1, 6))
    assert st.state == "due" and "5 Jan 2027" in st.text


def test_BF_D89_malformed_file_reads_as_one_row(demo: Any, tmp_path: Path) -> None:
    root = _broken(tmp_path)
    app = _app(demo, research_dir=root)
    st, html = _get(app, "/research/library")
    assert st == 200 and ar.COULD_NOT_READ in html and "studies/research_us.md" in html
    st, html = _get(app, "/research/glossary")
    assert st == 200 and ar.COULD_NOT_READ in html
    assert _get(app, "/research/library/research_us")[0] == 404
    assert _get(app, "/research")[0] == 200  # the rest still reads
    st, html = _get(app, "/health")
    assert st == 200 and "could not read" in html and "glossary.yaml" in html
    missing = _app(demo, research_dir=tmp_path / "none")
    for r in ("/research", "/research/library", "/research/testing", "/research/dates"):
        assert _get(missing, r)[0] == 200, r


def test_BF_D89_home_what_we_know_and_entry_points(demo: Any) -> None:
    app = _app(demo)
    st, html = _get(app, "/")
    assert st == 200 and "What we know" in html
    assert html.index("Scoreboard ·") < html.index("What we know") < html.index('class="hero"')
    assert "Big Wins is a $10,000 experiment" in html and "Next: " in html
    assert 'href="/research"' in html and "All highlights" in html
    assert 'href="/research/testing"' in html and "What we&#x27;re testing" not in html
    assert "Research lines (information only)" not in html
    st, html = _get(app, "/server")
    assert html.index('href="/research"') < html.index('href="/strategy"')
    st, html = _get(app, "/strategy")
    assert "Research (information only)" in html and "More in Research" in html
    st, html = _get(app, "/digest")
    assert "href='/research/testing'" in html


def test_BF_D89_pages_content(demo: Any) -> None:
    app = _app(demo)
    _, html = _get(app, "/research")
    for s in ("Highlights", "Library", "Testing", "Dates", "<summary>Why</summary>",
              "What to do", "General information, not personal financial advice",
              'href="/research/glossary"'):  # fmt: skip
        assert s in html, s
    _, html = _get(app, "/research/library")
    assert "Still running" not in html  # nothing in progress since research_us4 reported
    assert "US large-company" in html[html.index("Finished") :]
    assert "Doesn&#x27;t work" in html and "no change passed" in html
    assert "Testing" in html and "information only" in html  # NEWS-C registered (seq 106)
    assert "Mixed" in html and "describes, does not forecast" in html
    _, us = _get(app, "/research/library?f=us")
    assert "insiders" in us and "Odds card" not in us
    _, html = _get(app, "/research/library/research_bw")
    for s in ("In short", "Key numbers", "What it means for you", "How sure are we?",
              "Solid", "Tests in this study: 30 · running total after it: 3,147 · record entry 101",
              "Full report: OneDrive \u203a Big Wins forward record \u203a research_bw", "$20,770",
              "$10,000 from 2019 to Oct 2026, after tax, before running costs"):  # fmt: skip
        assert s in html, s
    assert html.index("What it means for you") < html.index("How sure are we?")
    assert '<details class="rsure">' in html  # closed by default
    assert 'class="gl" href="/research/glossary#' in html  # glossary terms underlined
    _, html = _get(app, "/research/library/odds_card")
    assert "Tests in this study: none" in html and "26.9%" in html
    _, html = _get(app, "/research/dates")
    assert html.index("Coming up") < html.index("Decided")
    assert "about late Feb 2027" in html and "You: " in html and "Ledger seq 96" in html
    _, html = _get(app, "/research/glossary")
    assert 'id="random-twins"' in html and 'id="conviction-sizing"' in html


def test_BF_D89_linker_first_use_only() -> None:
    lk = ar.Linker([{"term": "Index fund", "also": ["A200"], "means": "x"},
                    {"term": "Super", "means": "y"}])  # fmt: skip
    out = lk(e("An index fund (A200). Super funds; superannuation; index funds."))
    assert out.count('class="gl"') == 2 and "superannuation" in out
    assert out.count("#index-fund") == 1 and out.count("#super") == 1


# ---------------------------------------------------------------- 17: classifiers


def test_BF_D89_classifiers_ui_only_and_hashes_unchanged() -> None:
    from trader import strategy_version as sv
    from trader.yamlio import load_yaml

    w = runpy.run_path(str(REPO / "deploy" / "classify.py"))
    for f in ("trader/app_research.py", "trader/odds.py"):
        assert f in sv.UI_ONLY and f in w["UI_ONLY"]
        assert not sv.is_trading_path(f) and w["classify"]([f]) == "app"
    assert w["UI_ONLY"] == sv.UI_ONLY
    docs = ["docs/research/highlights.yaml", "docs/research/studies/research_bw.md",
            "docs/research/reports/research_bw.md", "docs/DECISIONS.md"]  # fmt: skip
    assert w["classify"](docs) == "app" and not any(sv.is_trading_path(f) for f in docs)
    assert sv.strategy_hash(REPO) == "a50dfa0b4eb1"
    cfg = load_yaml((REPO / "config" / "bfast.yaml").read_text()) or {}
    assert sv.config_hash(cfg) == "02589a19293b"
    assert "ledger_jsonl" in cfg["research"]  # an app-only section (NON_TRADING_CONFIG)
    # this build itself touches the Dockerfile, config and the classifiers: a trading update
    assert w["classify"](["deploy/Dockerfile", "config/bfast.yaml"]) == "strategy"
    assert "COPY docs/research ./docs/research" in (REPO / "deploy" / "Dockerfile").read_text()


def test_BF_D89_trader_never_imports_research() -> None:
    imp = re.compile(r"^\s*(from trader(\.app_research)? import .*\bapp_research\b|"
                     r"import trader\.app_research)", re.M)  # fmt: skip
    users = sorted(f.name for f in (REPO / "trader").rglob("*.py")
                   if imp.search(f.read_text(encoding="utf-8")))  # fmt: skip
    assert users == ["app_ops.py", "dashboard.py"]


# ---------------------------------------------------------------- 18: a real browser


def test_BF_D89_research_pages_in_a_real_browser(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys
    import time
    import urllib.request

    from tests.test_bf_app_browser import _free_port, _playwright

    module = _playwright()
    if module is None:
        pytest.skip("node / playwright not installed")
    port = _free_port()
    srv = subprocess.Popen(
        [sys.executable, "-m", "trader.bfast_cli", "dashboard", "--demo", "--host", "127.0.0.1",
         "--port", str(port), "--out", str(tmp_path)],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(240):
            try:
                with urllib.request.urlopen(base + "/healthz", timeout=2) as r:
                    if r.status == 200:
                        break
            except OSError:
                time.sleep(0.5)
        else:
            pytest.fail("the demo app did not start")
        env = {**os.environ, "PLAYWRIGHT_MODULE": module}
        r = subprocess.run(["node", str(REPO / "tests" / "browser" / "research_pages.js"), base,
                            "360"], capture_output=True, text=True, env=env, timeout=180,
                           check=False)  # fmt: skip
        if r.returncode != 0 and "Executable doesn't exist" in r.stderr:
            pytest.skip("no Chromium for Playwright here")
        assert r.returncode == 0, r.stderr[-2000:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.terminate()
        srv.wait(10)
    assert out["scroll"] == [], out["scroll"]  # no horizontal scroll at 360 px
    assert out["contrast"] == [], out["contrast"]  # every chip pair at least 4.5:1
    assert out["chips"] > 20 and out["whyOpens"] is True
