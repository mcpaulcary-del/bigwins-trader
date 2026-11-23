"""BF-D68: the app's second interactive pass. Read-only GET screens (treemap, what-if,
calendar, compare, month replay, search index) built from what the app already reads;
the preferences (card order, density, tour) live on the phone only."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from trader import app_more
from trader.journal import Journal

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def demo_app(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo
    from trader.journal import read_only_engine

    demo = build_demo(tmp_path_factory.mktemp("d") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
    src = Sources(j, index=demo.index, sessions=lambda: demo.sessions, today=lambda: demo.last_day,
                  clock=lambda: demo.now, demo=True, prices=demo.prices,
                  forecast_dir=REPO / "config")  # fmt: skip
    return demo, Dashboard(src)


def _get(d: Any, path: str) -> tuple[int, str]:
    st, _, b = d.respond("GET", path, {})
    return st, b.decode()


def test_BF_D68_squarify_fills_the_box_in_proportion() -> None:
    vals = [6.0, 6, 4, 3, 2, 2, 1]
    rs = app_more.squarify(vals, 0, 0, 100, 62)
    assert len(rs) == len(vals)
    total = sum(w * h for _, _, w, h in rs)
    assert total == pytest.approx(6200, rel=1e-6)
    for v, (_, _, w, h) in zip(vals, rs, strict=True):
        assert w * h == pytest.approx(v / sum(vals) * 6200, rel=1e-6)
    assert all(x >= -1e-9 and y >= -1e-9 and x + w <= 100 + 1e-6 and y + h <= 62 + 1e-6
               for x, y, w, h in rs)  # fmt: skip
    assert app_more.squarify([], 0, 0, 10, 10) == []


def test_BF_D68_beta_and_colour_steps_and_reason_words() -> None:
    ix = [100 * (1 + 0.01 * ((k % 3) - 1)) ** k for k in range(40)]
    px = [2 * x for x in ix]
    assert app_more.beta_of(px, ix) == pytest.approx(1.0)
    assert app_more.beta_of(px[:5], ix[:5]) is None  # too few days: the app uses 1.0
    assert app_more._tone(0.3) == "tmu3" and app_more._tone(-0.01) == "tmd1"
    assert app_more._tone(None) == "tm0"
    assert app_more._pc(0.05).startswith("▲") and app_more._pc(-0.05).startswith("▼")
    assert "top 40%" in app_more.reason_words("EMG2_C6_EXIT")
    assert app_more.reason_words("SOMETHING_NEW") == "SOMETHING_NEW"


def test_BF_D68_calendar_events_decisions_cutoffs_eofy_and_dividends() -> None:
    sess = [date(2026, 6, d) for d in (25, 26, 29, 30)] + [date(2026, 7, 1), date(2026, 7, 2)]
    v = SimpleNamespace(holdings=[])
    divs = {"AAA": [(date(2026, 6, 26), date(2026, 7, 2), 0.12)]}
    evs = app_more.calendar_events(v, None, sess, None, divs, date(2026, 6, 1), date(2026, 7, 31))
    kinds = {(x.day, x.kind) for x in evs}
    assert (date(2026, 6, 30), "decision") in kinds and (date(2026, 7, 1), "cutoff") in kinds
    assert (date(2026, 6, 30), "eofy") in kinds
    assert (date(2026, 6, 26), "exdiv") in kinds and (date(2026, 7, 2), "pay") in kinds
    html = app_more.calendar(v, date(2026, 6, 1), evs, date(2026, 6, 29))
    assert 'data-cday="2026-06-30"' in html and "June 2026" in html
    assert 'href="/calendar?m=2026-07"' in html and 'href="/calendar?m=2026-05"' in html
    assert html.count("data-cev=") == 3  # the June ones (decision, EOFY, ex-dividend)


def test_BF_D68_screens_are_read_only_and_render(demo_app: Any) -> None:
    demo, d = demo_app
    st, home = _get(d, "/")
    assert st == 200 and "data-whatif" in home and 'id="wi-r"' in home
    assert "An estimate, not a forecast" in home and 'data-card="perf"' in home
    assert 'id="searchbtn"' in home
    st, hold = _get(d, "/holdings")
    assert st == 200 and hold.count('class="tm"') >= 5 and 'data-tm="t"' in hold
    assert 'href="/compare"' in hold
    st, cal = _get(d, "/calendar")
    assert st == 200 and "data-cal" in cal and "Month-end decision" in cal
    st, cal2 = _get(d, "/calendar?m=2024-02")
    assert st == 200 and "February 2024" in cal2
    st, cmp_ = _get(d, "/compare")
    data = json.loads(re.search(r"data-compare-data>(.*?)</script>", cmp_).group(1))  # type: ignore[union-attr]
    assert st == 200 and len(data["s"]) >= 2 and data["idx"]
    st, orders = _get(d, "/orders")
    day = re.search(r'href="/replay/([0-9-]+)"', orders).group(1)  # type: ignore[union-attr]
    st, rp = _get(d, f"/replay/{day}")
    assert st == 200 and rp.count('class="rpane"') == 4 and "Band C ranked" in rp
    assert "Final orders" in rp and "nothing is recomputed" in rp
    assert "EMG2_OFF_LIST" not in rp  # reason codes in plain words
    assert _get(d, "/replay/1999-01-31")[0] == 404 and _get(d, "/replay/nope")[0] == 404
    st, sj = _get(d, "/search.json")
    rows = json.loads(sj)
    assert st == 200 and {r["g"] for r in rows} >= {"Shares", "Orders", "Inbox"}
    assert all(r["u"].startswith("/") for r in rows)
    st, settings = _get(d, "/settings")
    assert "data-density" in settings and "data-tour-replay" in settings
    for p in ("/calendar", "/compare", f"/replay/{day}", "/search.json"):
        assert d.respond("POST", p, {})[0] == 405
    for page in (home, hold, cal, cmp_, rp, settings):
        assert "<form" not in page  # no new write path


def test_BF_D68_milestone_is_subtle_and_only_when_ahead() -> None:
    d0, d1, d2 = date(2026, 10, 30), date(2026, 11, 2), date(2026, 11, 20)
    from decimal import Decimal

    ahead = SimpleNamespace(series=[(d0, Decimal(100)), (d1, Decimal(101)), (d2, Decimal(105))],
                            index=[(d0, 100.0), (d1, 100.0), (d2, 102.0)])  # fmt: skip
    behind = SimpleNamespace(series=ahead.series, index=[(d0, 100.0), (d2, 110.0)])
    assert "Ahead of the index this month" in app_more.month_milestone(ahead)
    assert app_more.month_milestone(behind) == ""


def test_BF_D68_no_gamification_words_in_the_script() -> None:
    from trader import webui

    low = webui.JS.lower()
    for w in ("confetti", "streak", "trade more"):
        assert w not in low
