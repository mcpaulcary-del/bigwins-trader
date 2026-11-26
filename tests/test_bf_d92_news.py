"""BF-D92: the News tab (presentation only, read-only). What is happening to the shares
the book holds and why: the announcements the private info archive already stores
(headline, time, price-sensitive marker, the stored PDF when there is one), big moves and
halts from the closes the app already has, and the held shares against the index on the
day. Information only: no rating, no cause label, no advice, no new network request."""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from decimal import Decimal
from html import unescape
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from trader import app_ops, webui
from trader import info_view as iv
from trader.app_pages import Extras
from trader.constants import ASX_TZ
from trader.dashboard import Holding
from trader.journal import Journal

REPO = Path(__file__).resolve().parents[1]
D1, D2, D3 = date(2026, 11, 24), date(2026, 11, 25), date(2026, 11, 26)
NOW = datetime(2026, 11, 27, 8, 30, tzinfo=ASX_TZ)
PDF = b"%PDF-1.4\n% made up for the test\n"


def _archive(root: Path, days: dict[date, list[tuple[str, str, int, str, str]]]) -> Path:
    """A fixture archive in the layout ``deploy/info_archive.py`` writes (made-up rows)."""
    for d, rows in days.items():
        dd = root / "asx_notices" / str(d)
        (dd / "pdf").mkdir(parents=True, exist_ok=True)
        with (dd / "list.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["code", "date", "time", "price_sensitive", "headline", "ids_id", "kept"])
            for code, tm, ps, head, ids in rows:
                w.writerow([code, f"{d:%d/%m/%Y}", tm, ps, head, ids, 0])
        (dd / "DONE").write_text("{}")
    return root


def _fixture(tmp_path: Path) -> Path:
    root = _archive(tmp_path / "info", {
        D1: [("AAA", "9:10 am", 0, "Investor Presentation", "03000001"),
             ("CCC", "8:20 am", 1, "Trading Halt", "03000002"),
             ("ZZZ", "9:00 am", 1, "Not held: takeover bid", "03000003")],
        D2: [("AAA", "4:45 pm", 1, "Half Year Results <script>alert(1)</script>", "03000004"),
             ("BBB", "10:05 am", 0, "Change of Director's Interest Notice", "03000005"),
             ("DDD", "11:00 am", 1, "Scheme Implementation Deed signed", "03000006")],
    })  # fmt: skip
    (root / "asx_notices" / str(D2) / "pdf" / "AAA_03000004.pdf").write_bytes(PDF)
    (root / "asx_notices" / str(D2) / "pdf" / "BBB_03000005.pdf").write_bytes(b"<html>no</html>")
    return root


def _hold(code: str, qty: int = 100) -> Holding:
    return Holding(code, qty, Decimal(500), Decimal(5), str(D3), False, 20)


PRICES = {  # the last closes (made up): AAA +8%, BBB flat-ish, CCC no close on the last day
    "AAA": [(D1, 5.0), (D2, 5.0), (D3, 5.4)],
    "BBB": [(D1, 2.0), (D2, 2.0), (D3, 2.02)],
    "CCC": [(D1, 1.0), (D2, 1.0)],
    "DDD": [(D1, 10.0), (D2, 10.0), (D3, 9.3)],
}
INDEX = [(D1, 100.0), (D2, 100.0), (D3, 100.5)]


def _src_v(root: Path | None, codes: tuple[str, ...] = ("AAA", "BBB", "CCC", "DDD")) -> Any:
    src = SimpleNamespace(info_dir=root, prices=lambda c: PRICES.get(c, []), index=lambda: INDEX)
    v = SimpleNamespace(now=NOW, holdings=[_hold(c) for c in codes], index=[], index_label="A200",
                        notes=[], demo=False, live=False, book="EMG2_18_PAPER")  # fmt: skip
    return src, v


def _page(nw: app_ops.News, v: Any, qs: dict[str, str] | None = None) -> str:
    x = Extras(names={"AAA": "Alpha Ltd", "BBB": "Beta Ltd", "CCC": "Gamma Ltd"})
    html = app_ops.news_page(v, x, nw, qs or {})
    return html[html.index("<main") : html.index("</main>")]


# ---------------------------------------------------------------- reading the archive


def test_BF_D92_feed_is_held_shares_only_newest_first(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    items = iv.feed(root, ["AAA", "BBB", "CCC", "DDD"], D3)
    assert items is not None
    assert [(n.code, str(n.day), n.time) for n in items] == [
        ("AAA", str(D2), "4:45 pm"), ("DDD", str(D2), "11:00 am"), ("BBB", str(D2), "10:05 am"),
        ("AAA", str(D1), "9:10 am"), ("CCC", str(D1), "8:20 am")]  # fmt: skip
    assert [n.price_sensitive for n in items] == [True, True, False, False, True]
    # the PDF marker only when the archive really stores that notice's PDF
    assert [n.pdf for n in items] == [True, False, False, False, False]
    assert items[4].flags == ("halt",) and items[1].flags == ("takeover",)
    assert all(n.trade is None for n in items)  # headlines only: no notice text is read
    assert iv.latest_day(root) == D2
    assert iv.stamp(items[0]) == 202611250000 + 16 * 60 + 45 > iv.stamp(items[1])
    # a window: a notice older than the window is left to the share's own page
    assert [n.code for n in iv.feed(root, ["CCC"], D3, days=1) or []] == []
    # nothing collected yet is "None" (not "no news")
    assert iv.feed(None, ["AAA"], D3) is None and iv.feed(tmp_path / "none", ["AAA"], D3) is None
    assert iv.latest_day(tmp_path / "none") is None


def test_BF_D92_pdf_only_from_inside_the_archive(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    ok = iv.pdf_file(root, str(D2), "AAA_03000004.pdf")
    assert ok is not None and ok.read_bytes() == PDF
    secret = tmp_path / "secret.pdf"
    secret.write_bytes(PDF)
    (root / "asx_notices" / str(D2) / "pdf" / "LNK_1.pdf").symlink_to(secret)
    for day_s, name in ((str(D2), "BBB_03000005.pdf"),  # stored, but not a PDF
                        (str(D2), "AAA_99.pdf"),  # not stored
                        (str(D2), "LNK_1.pdf"),  # a link out of the archive
                        (str(D2), "../list.csv"), (str(D2), "..%2f..%2fsecret.pdf"),
                        ("..", "AAA_03000004.pdf"), ("2026-11-25/..", "AAA_03000004.pdf"),
                        (str(D2), "AAA_03000004.txt"), (str(D2), "aaa_03000004.pdf")):  # fmt: skip
        assert iv.pdf_file(root, day_s, name) is None, (day_s, name)
    assert iv.pdf_file(None, str(D2), "AAA_03000004.pdf") is None


# ---------------------------------------------------------------- what the tab shows


def test_BF_D92_big_moves_halts_and_the_day_against_the_index(tmp_path: Path) -> None:
    src, v = _src_v(_fixture(tmp_path))
    nw = app_ops.collect_news(src, v)
    assert nw.price_day == D3 and nw.archive_day == D2
    got = {(m.code, m.kind): m for m in nw.movers}
    assert set(got) == {("CCC", "halt"), ("CCC", "quiet"), ("DDD", "takeover"), ("AAA", "move"),
                        ("DDD", "move")}  # fmt: skip
    assert got[("AAA", "move")].move == pytest.approx(0.08)
    assert got[("DDD", "move")].move == pytest.approx(-0.07)
    assert "No trade recorded on Thu 26 Nov" in got[("CCC", "quiet")].what
    # most serious first: a halt, then no trade, then a takeover notice, then the moves
    assert [m.kind for m in nw.movers] == ["halt", "quiet", "takeover", "move", "move"]
    # the held shares together, weighted by what is held; BBB's +1% is not a "big move"
    was = 100 * (5.0 + 2.0 + 1.0 + 10.0)
    assert nw.book_move == pytest.approx((100 * (5.4 + 2.02 + 1.0 + 9.3)) / was - 1)
    assert nw.index_move == pytest.approx(0.005)
    assert nw.stamp == app_ops.news_stamp(src, v) == 202611250000 + 16 * 60 + 45
    # a reinstatement is "trading again", not a halt
    root2 = _archive(tmp_path / "i2", {D2: [("CCC", "9:00 am", 1,
                                             "Reinstatement to Official Quotation", "1")]})  # fmt: skip
    kinds = [m.kind for m in app_ops.collect_news(*_src_v(root2, ("CCC",))).movers]
    assert kinds == ["back"]


def test_BF_D92_page_order_label_links_and_escaping(tmp_path: Path) -> None:
    src, v = _src_v(_fixture(tmp_path))
    html = _page(app_ops.collect_news(src, v), v)
    order = [html.index(s) for s in ("3 announcements on your shares, 2 price sensitive",
                                     "Your shares", "A200", app_ops.NEWS_INFO,
                                     "Big moves and halts", "Announcements</h2>",
                                     "Wed 25 Nov · latest", 'class="day">Tue 24 Nov')]  # fmt: skip
    assert order == sorted(order)
    assert "close of Thu 26 Nov" in html and "▼" in html and "▲" in html  # never colour alone
    # each row names the share and links to its page; the PDF link only where one is stored
    assert 'href="/holdings/AAA" data-nav>Alpha Ltd' in html
    assert html.count('class="pdfl"') == 1
    assert 'href="/news/pdf/2026-11-25/AAA_03000004.pdf" target="_blank" rel="noopener"' in html
    assert html.count("Price sensitive</span>") == 3
    assert "<script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "ZZZ" not in html and "Not held" not in html  # only the shares the book holds
    # the price-sensitive filter is a plain link (no script needed)
    ps = _page(app_ops.collect_news(src, v), v, {"f": "ps"})
    assert 'class="chip on" href="/news?f=ps"' in ps
    assert "Investor Presentation" not in ps and "Trading Halt" in ps


def test_BF_D92_information_only_no_ratings_no_advice(tmp_path: Path) -> None:
    src, v = _src_v(_fixture(tmp_path))
    html = _page(app_ops.collect_news(src, v), v)
    text = unescape(re.sub(r"<[^>]+>", " ", html))
    assert "Information only, not a trading signal." in text
    # NEWS-C stays out: no per-share rating, no cause label, nothing that reads as advice
    for word in ("NEWS-C", "rating", "rated", "score", "drop cause", "cause:", "buy", "sell",
                 "should", "recommend", "opportunity", "bullish", "bearish", "good news",
                 "bad news"):  # fmt: skip
        assert not re.search(rf"\b{re.escape(word)}\b", text, re.I), word
    # the tab reads headlines only: a director's notice is named, its trade is not judged
    assert "Director's interest" in text and "bought" not in text.lower()
    # nothing in the display code fetches anything: only the archive job talks to the ASX
    for f in ("trader/info_view.py", "trader/app_ops.py"):
        code = (REPO / f).read_text()
        assert "urllib.request" not in code and "requests" not in code and "http.client" not in code


def test_BF_D92_empty_states(tmp_path: Path) -> None:
    # a quiet day: the archive is collecting, nothing on the latest day, no big move
    root = _archive(tmp_path / "q", {D1: [("AAA", "9:10 am", 0, "Investor Presentation", "1")],
                                     D2: [("ZZZ", "9:00 am", 1, "Someone else", "2")]})  # fmt: skip
    src, v = _src_v(root, ("BBB",))
    html = _page(app_ops.collect_news(src, v), v)
    assert "No news on your shares today" in html
    assert "Announcements last collected for Wed 25 Nov." in html
    assert "No big moves or halts on your shares on Thu 26 Nov." in html
    assert "No announcements on your shares in the last 14 days." in html
    assert "Your shares" in html and "+1.0%" in html  # the one-line context is still there
    # the archive has stored nothing yet: said plainly, the moves still shown
    src, v = _src_v(None, ("AAA",))
    html = _page(app_ops.collect_news(src, v), v)
    assert "Announcements are not collected yet" in html and "Up 8.0% on Thu 26 Nov" in html
    assert "Announcements</h2>" not in html and app_ops.NEWS_INFO in html
    # all cash
    src, v = _src_v(_fixture(tmp_path), ())
    nw = app_ops.collect_news(src, v)
    html = _page(nw, v)
    assert "You hold no shares right now" in html and nw.stamp == 0 and "pdfl" not in html
    # a broken price source or archive never breaks the screen
    src, v = _src_v(tmp_path / "missing", ("AAA",))
    src.prices = lambda c: 1 / 0
    src.index = lambda: 1 / 0
    assert "Announcements are not collected yet" in _page(app_ops.collect_news(src, v), v)


# ---------------------------------------------------------------- the tab bar and the dot


def test_BF_D92_six_tabs_news_dot_same_mechanism_as_inbox() -> None:
    assert [t[0] for t in webui.TABS] == ["home", "holdings", "news", "orders", "inbox", "server"]
    html = webui.page("X", "<p>x</p>", "news", latest_news=202611251645)
    nav = html[html.index("<nav") : html.index("</nav>")]
    assert (
        len(re.findall(r'class="tab( on)?"', nav)) == 6
        and nav.count('<b class="dot" hidden></b>') == 2
    )
    assert 'href="/news" class="tab on" data-nav data-tab="news" aria-current="page"' in nav
    assert 'data-latest-news="202611251645"' in html
    assert 'data-latest-news="0"' in webui.page("X", "", "home")
    # the dot is the app's own script and localStorage, as for the Inbox: no new file
    assert "bw.newsSeen" in webui.JS and "latestNews" in webui.JS
    assert set(webui.STATIC) == {"/app.css", "/app.js", "/sw.js"}
    assert "http://" not in webui.CSS and "https://" not in webui.CSS  # no outside file


# ---------------------------------------------------------------- the routes (demo data)


@pytest.fixture(scope="module")
def demo_app(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo, demo_control
    from trader.journal import read_only_engine

    demo = build_demo(tmp_path_factory.mktemp("d92") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
    src = Sources(j, index=demo.index, sessions=lambda: demo.sessions, today=lambda: demo.last_day,
                  clock=lambda: demo.now, demo=True, prices=demo.prices,
                  forecast_dir=REPO / "config", scorecard=demo.scorecard, info_dir=demo.info_dir,
                  info_enabled=True)  # fmt: skip
    ctl = demo_control(j, demo)
    return demo, Dashboard(src, actions=ctl.respond)


def test_BF_D92_routes_read_only(demo_app: Any) -> None:
    demo, d = demo_app
    st, hdrs, body = d.respond("GET", "/news", {})
    html = body.decode()
    assert st == 200 and hdrs["Content-Type"].startswith("text/html")
    assert 'data-tab="news"' in html and app_ops.NEWS_INFO in html
    assert "Big moves and halts" in html and "Announcements</h2>" in html
    assert d.respond("GET", "/news?f=ps", {})[0] == 200 and d.respond("HEAD", "/news", {})[0] == 200
    assert d.respond("POST", "/news", {})[0] == 405  # nothing to change here
    # every screen carries the stamp of the newest price-sensitive notice on a held share
    m = re.search(r'data-latest-news="(\d+)"', html)
    assert m and int(m.group(1)) > 202401010000
    assert f'data-latest-news="{m.group(1)}"' in d.respond("GET", "/holdings", {})[2].decode()
    # a stored PDF opens; anything else under /news/pdf is not found
    link = re.search(r'href="(/news/pdf/[^"]+)"', html)
    assert link is not None
    st, hdrs, body = d.respond("GET", link.group(1), {})
    assert st == 200 and hdrs["Content-Type"] == "application/pdf" and body.startswith(b"%PDF-")
    assert hdrs["X-Content-Type-Options"] == "nosniff" and hdrs["Cache-Control"] == "no-store"
    for bad in ("/news/pdf/2024-02-28/NOPE_1.pdf", "/news/pdf/2024-02-28/..%2Flist.csv",
                "/news/pdf/x/y/z.pdf", "/news/pdf/", "/news/other"):  # fmt: skip
        assert d.respond("GET", bad, {})[0] == 404, bad
    assert d.respond("POST", link.group(1), {})[0] == 405
    # a log-in that may not view the app may not read a PDF either
    from dataclasses import replace

    locked = replace(d, allowed_logins=frozenset({"owner@example.com"}))
    assert locked.respond("GET", link.group(1), {})[0] == 403
    assert locked.respond("GET", "/news", {"Tailscale-User-Login": "x@example.com"})[0] == 403


def test_BF_D92_display_files_only() -> None:
    """Everything this build changes in ``trader/`` is on the app-only list, and the
    archive job itself is untouched (it stays the only code that talks to the ASX)."""
    from trader import strategy_version as sv

    for f in ("trader/webui.py", "trader/app_pages.py", "trader/app_ops.py",
              "trader/info_view.py", "trader/dashboard.py", "trader/dashboard_demo.py"):  # fmt: skip
        assert f in sv.UI_ONLY and not sv.is_trading_path(f)
    assert sv.is_trading_path("deploy/info_archive.py")


# ---------------------------------------------------------------- a real browser


def test_BF_D92_news_tab_in_a_real_browser(tmp_path: Path) -> None:
    import json
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
        r = subprocess.run(["node", str(REPO / "tests" / "browser" / "news_pages.js"), base],
                           capture_output=True, text=True, env=env, timeout=240,
                           check=False)  # fmt: skip
        if r.returncode != 0 and "Executable doesn't exist" in r.stderr:
            pytest.skip("no Chromium for Playwright here")
        assert r.returncode == 0, r.stderr[-2000:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.terminate()
        srv.wait(10)
    assert out["scroll"] == [], out["scroll"]  # no horizontal scroll at 360 and 390 px
    assert out["tabs"] == [], out["tabs"]  # six tabs: one row, 44 px targets, no label cut
    assert out["contrast"] == [], out["contrast"]  # at least 4.5:1, light and dark
    assert out["pages"] == 20 and out["rows"] >= 5 and out["nojsRows"] == out["rows"]
    # the dot: there until News has been opened, then gone (and stays gone)
    assert (out["dotBefore"], out["dotOnNews"], out["dotAfter"]) == (True, False, False)
    assert out["pdfLinks"] >= 1 and out["pdf"] == "200 application/pdf %PDF-"
    assert out["nojsLabel"] is True
