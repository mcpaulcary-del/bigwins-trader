"""BF-D94 (with BF-D93's app side): the REAL paper record in the app, the nightly report
and its Big movers from the OneDrive relay, the Inbox messages, Health and the missed-job
alarm for every moved job. Fixture data only: every book value, share and headline here
is made up; only the file layouts are the record's."""

from __future__ import annotations

import json
import runpy
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from record.tools import jobs as record_jobs
from trader import app_ops, app_research
from trader import ops_view as ov
from trader import record_view as rv
from trader import strategy_version as sv
from trader.app_pages import Extras, shell
from trader.app_store import SERVER_ACTIONS, set_state
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.ops_hooks import record_record, tell_record
from trader.server_status import clean_record, clean_status

REPO = Path(__file__).resolve().parents[1]
D0, D1, D2 = "2026-12-01", "2026-12-14", "2026-12-15"
NOW = datetime(2026, 12, 15, 21, 0, tzinfo=ASX_TZ)
HEAD = ("asof,book,kind,capital,nav,holdings,return_since_start,vs_a200,vs_4060,vs_a200_b0,"
        "vs_4060_b0,pct_of_random,note")  # fmt: skip


def _paper(root: Path, with_prev: bool = True) -> Path:
    """A made-up display copy in the layout record/tools/view.py writes."""
    paper = root / "paper"
    paper.mkdir(parents=True)
    rows: list[tuple[Any, ...]] = [
        # (book, kind, capital, nav D0, nav D1, nav D2, own vs_a200_b0, own vs_4060_b0, pct_random)
        ("EMG2_18_SIM_BT_C6", "paper line", 10000, 9990, 10100, 10201, "", "", 0.62),
        ("EMG2_18_REF", "REF", 10000, 9990, 9900, 9950, "", "", ""),
        ("EMG2_100k", "SHADOW_EMG2", 100000, 99900, 100500, 100400, "", "", 0.4),
        ("H82_25k", "H82", 25000, 24900, 25200, 25100, 0.011, 0.009, 0.9),
        ("BLIND3_10k", "BLIND3", 10000, 9995, 10900, 11500, "", "", 0.99),
        ("EMG2_18_SIM_BT_C6_SWEEP", "side line SWEEP", 10000, 9990, 10050, 10020, "", "", 0.5),
        ("EMG2_MOON_TOP5", "MOON", 10000, 9980, 9000, 8800, "", "", 0.1),
        ("PAIR_10k", "PAIR", 10000, 9990, 10010, 10030, "", "", 0.55),
        ("CMP_A200_100k_b0", "CMP", 100000, 100000, 101000, 101500, "", "", ""),
        ("CMP_4060_100k_b0", "CMP", 100000, 100000, 100600, 100900, "", "", ""),
        ("RND_25k (200 seeds)", "RND", 25000, "", "", "", "", "", ""),
        ("MOM_25k", "MOM", 25000, "", "", "", "", "", ""),  # a line that has not started
    ]  # fmt: skip
    hist = [HEAD]
    latest = [HEAD]
    for book, kind, cap, n0, n1, n2, va, vp, pr in rows:
        for day, nav in ((D0, n0), (D1, n1), (D2, n2)):
            ret = "" if nav == "" else round(float(nav) / cap - 1, 5)
            line = (
                f"{day},{book},{kind},{cap},{nav},{'' if nav == '' else 5},{ret},,,{va},{vp},{pr},"
            )
            if nav == "":
                line += '"not started: first decision 2026-11-30 <b>x</b>"'
            hist.append(line)
            if day == D2:
                latest.append(line)
    (paper / "scorecard_history.csv").write_text("\n".join(hist) + "\n")
    (paper / "scorecard_latest.csv").write_text("\n".join(latest) + "\n")
    hh = "asof,book,code,name,shares,cost_AUD,first_buy,last_close,last_close_date,value_AUD,pnl_AUD,pnl_pct,awaiting_sale,q6_flag"
    (paper / "holdings_latest.csv").write_text("\n".join([
        hh,
        f"{D2},H82_25k,AAA,Alpha <i>Ltd</i>,100,1000,{D0},11.0,{D2},1100,100,0.10,False,False",
        f"{D2},H82_25k,BBB,Beta Ltd,50,500,{D0},9.5,{D2},475,-25,-0.05,False,False",
        f"{D2},H82_25k,CCC,Gamma Ltd,10,100,{D0},10.0,{D1},100,0,0.0,False,False",  # no close today
        f"{D2},H82_25k,DDD,Delta Ltd,20,200,{D0},5.0,{D2},100,-100,-0.5,True,False",  # split: count changed
    ]) + "\n")  # fmt: skip
    if with_prev:
        (paper / "holdings_prev.csv").write_text("\n".join([
            hh,
            f"{D1},H82_25k,AAA,Alpha Ltd,100,1000,{D0},10.0,{D1},1000,0,0.0,False,False",
            f"{D1},H82_25k,BBB,Beta Ltd,50,500,{D0},10.0,{D1},500,0,0.0,False,False",
            f"{D1},H82_25k,CCC,Gamma Ltd,10,100,{D0},10.0,{D1},100,0,0.0,False,False",
            f"{D1},H82_25k,DDD,Delta Ltd,10,200,{D0},10.0,{D1},100,0,0.0,False,False",
        ]) + "\n")  # fmt: skip
    (paper / "SCORECARD.md").write_text(
        "# Made-up scorecard\n\n## Lines\n\n| Book | NAV |\n|---|---|\n| X <script>alert(1)</script> | 1 |\n"
    )
    (root / "source.json").write_text(json.dumps({
        "source": "the research environment (nightly copy abc1234)", "refreshed": "2026-12-15T20:55:00+1100",
        "note": "read-only copy; the record is still written in the research environment"}))  # fmt: skip
    return root


def _report(relay: Path, folder: str = D2, **over: Any) -> Path:
    day = folder
    d = relay / "reports" / folder
    d.mkdir(parents=True, exist_ok=True)
    raw: dict[str, Any] = {
        "schema": 1, "day": day, "written_utc": "2026-12-15T09:40:00Z",
        "title": "Big Wins — Tue 15 Dec", "verdict": "Up day: books +0.4%, market +0.5%.",
        "needs_attention": ["CCC had no close today (possible halt)"],
        "movers": [
            {"code": "AAA", "name": "Alpha Ltd", "move": 0.10, "six_month": 0.38, "from_high": -0.09,
             "score_rank": 2, "held_by": ["H82_25k"], "why": "Raised its profit guidance <b>x</b>",
             "sources": [1, 9], "rating": "+2", "newsc_label": "T"},
            {"code": "CCC", "name": "Gamma Ltd", "move": None, "no_close": True, "held_by": ["H82_25k"],
             "why": "", "sources": []},
        ],
        "sources": [{"n": 1, "title": "Made-up news site", "url": "https://news.example.com/a?b=1"}],
    }  # fmt: skip
    raw.update(over)
    (d / "report.json").write_text(json.dumps(raw))
    (d / "report.md").write_text(
        "**Big Wins — Tue 15 Dec**\n\n**Verdict:** Up day.\n\n| Book | Value |\n|---|---|\n| H82 | 25,100 |\n\n"
        "<script>alert(1)</script>\n")  # fmt: skip
    return relay


def _vx() -> tuple[Any, Extras]:
    v = SimpleNamespace(now=NOW, holdings=[], index=[], index_label="A200", notes=[], demo=False,
                        live=False, book="EMG2_18_PAPER")  # fmt: skip
    return v, Extras(names={})


def _main(html: str) -> str:
    return html[html.index("<main") : html.index("</main>")]


# ---------------------------------------------------------------- the record's own numbers
def test_BF_D94_lines_values_change_and_comparisons(tmp_path: Path) -> None:
    rec = rv.load(_paper(tmp_path / "view"))
    assert rec is not None and rec.asof == D2
    by = {x.book: x for x in rec.lines}
    main = by["EMG2_18_SIM_BT_C6"]
    assert main.group == "main" and main.nav == 10201 and main.start == D0
    assert main.change == pytest.approx(10201 / 10100 - 1)  # change on the last booked day
    assert main.ret == pytest.approx(0.0201)
    # the record gives no A200 column for this line: worked out from its A200 comparator
    assert main.worked_out and main.vs_a200 == pytest.approx(0.0201 - (101500 / 100000 - 1))
    assert main.vs_4060 == pytest.approx(0.0201 - 0.009) and main.pct_random == 0.62
    h82 = by["H82_25k"]  # the record's own figures win when it gives them
    assert not h82.worked_out and h82.vs_a200 == 0.011 and h82.vs_4060 == 0.009
    assert by["MOM_25k"].group == "kept" and not by["MOM_25k"].started
    assert by["PAIR_10k"].group == "other" and by["CMP_A200_100k_b0"].group == "comparator"
    assert by["RND_25k (200 seeds)"].group == "comparator"
    # kept lines come in the REGISTERED order (ops_view.KEPT_LINES), whatever their returns
    kept = [x.book for x in rec.by_group("kept")]
    order = [b for _, _, books in ov.KEPT_LINES for b in books]
    assert kept == sorted(kept, key=order.index)
    assert kept.index("EMG2_18_REF") < kept.index("BLIND3_10k") < kept.index("EMG2_MOON_TOP5")
    assert rv.load(tmp_path / "missing") is None and rv.load(None) is None


def test_BF_D94_holdings_day_moves_from_the_records_two_closes(tmp_path: Path) -> None:
    rec = rv.load(_paper(tmp_path / "view"))
    assert rec is not None and rec.prev_asof == D1
    h = {x["code"]: x for x in rec.holdings["H82_25k"]}
    assert h["AAA"]["move"] == pytest.approx(0.10) and h["BBB"]["move"] == pytest.approx(-0.05)
    assert h["CCC"]["no_close"] and h["CCC"]["move"] is None  # no close on the booked day
    assert (
        h["DDD"]["move"] is None and h["DDD"]["awaiting_sale"]
    )  # share count changed: no move shown
    first_day = rv.load(_paper(tmp_path / "v2", with_prev=False))
    assert first_day is not None and all(x["move"] is None for x in first_day.holdings["H82_25k"])


def test_BF_D94_record_page_keeps_the_scoreboard_rules(tmp_path: Path) -> None:
    root = _paper(tmp_path / "view")
    relay = _report(tmp_path / "relay")
    v, x = _vx()
    html = _main(rv.record_page(v, x, rv.load(root), rv.load_report(relay), shell))
    # 1. the main line against A200 is the headline
    assert html.index("Main line on paper: ahead of A200 by 0.5 points") < html.index(
        "Research lines"
    )
    assert "After the record" in html and "Paper only: no real money" in html
    # 2. every other line: information only, mostly luck, registered order, never ranked
    assert "mostly luck at this stage" in html and "not ranked" in html
    assert "never evidence for or against the main line" in html
    low = html.lower()
    for word in ("leaderboard", "best line", "winner", "top performer", "#1", "1st"):
        assert word not in low
    # BLIND3 has the highest return in the fixture and still sits in its registered place
    assert html.index("Reference book") < html.index("Steady Momentum") < html.index("MOON TOP5")
    # 3. value, change today, vs A200, vs 40/60, twins
    assert "$10,201" in html and "▲ +1.0%" in html and "v A200" in html and "v 40/60" in html
    assert "ahead of 62% of its random twins" in html and "worked out by the app" in html
    assert "not started" in html and "&lt;b&gt;x&lt;/b&gt;" in html  # the record's note, escaped
    # 4. holdings with day moves; made-up markup in a name is escaped
    assert "▲ +10.0%" in html and f"▼ {ov.MINUS}5.0%" in html
    assert "no close" in html and "Alpha &lt;i&gt;Ltd&lt;/i&gt;" in html and "<i>Ltd" not in html
    assert "Comparators" in html and "CMP_A200_100k_b0" in html
    assert "nightly copy abc1234" in html and 'href="/record/report?d=2026-12-15"' in html
    # 5. no NEWS-C rating anywhere
    assert "rating" not in low and "news-c" not in low
    # no record copy yet: says how to switch it on, shows nothing made up
    empty = _main(rv.record_page(v, x, None, None, shell))
    assert "not shown on this server yet" in empty and "sudo bigwins record view on" in empty


def test_BF_D94_demo_app_shows_the_real_record_only_from_the_view_copy(tmp_path: Path) -> None:
    """Owner: "the app must show the REAL paper record, not demo data"."""
    root = _paper(tmp_path / "view")
    demo_card = tmp_path / "demo" / "paper" / "scorecard_latest.csv"
    demo_card.parent.mkdir(parents=True)
    demo_card.write_text(HEAD + "\n")
    demo = SimpleNamespace(demo=True, record_view=None, scorecard=demo_card, relay_dir=None)
    assert rv.view_dir(demo) is None  # the demo's made-up scorecard is never the paper record
    real = SimpleNamespace(demo=True, record_view=root, scorecard=demo_card, relay_dir=None)
    assert rv.view_dir(real) == root
    live = SimpleNamespace(
        demo=False, record_view=tmp_path / "none", scorecard=root / "paper" / "scorecard_latest.csv"
    )
    assert rv.view_dir(live) == root  # the real app falls back to the mounted record folder
    v, x = _vx()
    page = app_ops.record_screen(real, v, x, "/record", {})
    assert page is not None and "Main line on paper" in page
    card = app_ops.record_home_card(real)
    assert 'href="/record"' in card and "Main line on paper: $10,201" in card
    assert app_ops.record_home_card(demo) == ""
    sc = app_ops.record_screen(real, v, x, "/record/scorecard", {})
    assert sc is not None and "&lt;script&gt;" in sc and "<script>alert" not in _main(sc)
    assert app_ops.record_screen(real, v, x, "/record/costs", {}) is None  # no such file: 404
    assert app_ops.record_screen(real, v, x, "/record/../etc", {}) is None
    from trader.dashboard import Dashboard, Sources

    assert {"/record", "/record/report", "/record/scorecard", "/record/costs"} <= set(
        Dashboard.SCREENS
    )
    assert Sources(Journal.sqlite()).record_view is None


# ---------------------------------------------------------------- the nightly report (relay)
def test_BF_D94_report_format_is_strict(tmp_path: Path) -> None:
    relay = _report(tmp_path / "relay")
    rep = rv.load_report(relay)
    assert rep is not None and rep.day == date(2026, 12, 15) and len(rep.movers) == 2
    assert rep.movers[0].sources == (1,)  # a source number that does not exist is dropped
    assert rep.movers[1].why == "no news found" and rep.movers[1].no_close
    assert not hasattr(rep.movers[0], "rating")  # unknown keys never get in
    good = json.loads((relay / "reports" / D2 / "report.json").read_text())
    bad_cases: list[dict[str, Any]] = [
        {"schema": 2}, {"day": "tomorrow"},
        {"sources": [{"n": 1, "title": "x", "url": "javascript:alert(1)"}]},
        {"sources": [{"n": 1, "title": "x", "url": "http://plain.example.com/"}]},
        {"sources": [{"n": 1, "title": "x", "url": "https://ok.example.com/\"><script>"}]},
        {"movers": [{"code": "<b>", "why": "x"}]}, {"movers": [{"code": "AAA", "why": "x" * 500}]},
        {"movers": [{"code": "AAA", "move": "big"}]}, {"movers": [{"code": "AAA", "held_by": ["<x>"]}]},
        {"movers": [{"code": "AAA"}] * 16}, {"verdict": "x" * 400}, {"needs_attention": "all good"},
        {"title": "a\x00b"},
    ]  # fmt: skip
    for over in bad_cases:
        with pytest.raises(rv.ReportError):
            rv.parse_report({**good, **over})
    with pytest.raises(rv.ReportError):
        rv.parse_report([1, 2])
    # a report filed under another day's folder, or unreadable JSON, is not shown
    _report(tmp_path / "relay", "2026-12-16", day="2026-12-17")
    assert rv.load_report(relay, date(2026, 12, 16)) is None
    (relay / "reports" / "2026-12-16" / "report.json").write_text("{not json")
    assert rv.load_report(relay, date(2026, 12, 16)) is None
    assert rv.load_report(relay, date(2026, 12, 1)) is None and rv.load_report(None) is None
    assert rv.report_days(relay) == [date(2026, 12, 15), date(2026, 12, 16)]


def test_BF_D94_big_movers_on_the_news_tab_with_why_and_links(tmp_path: Path) -> None:
    relay = _report(tmp_path / "relay")
    src = SimpleNamespace(info_dir=None, prices=None, index=lambda: [], relay_dir=relay)
    v, x = _vx()
    nw = app_ops.collect_news(src, v)
    html = _main(app_ops.news_page(v, x, nw, {}))
    assert "Big movers" in html and "Raised its profit guidance &lt;b&gt;x&lt;/b&gt;" in html
    assert ('<a href="https://news.example.com/a?b=1" target="_blank" rel="noopener noreferrer nofollow">[1]</a>'
            in html)  # fmt: skip
    assert (
        "6 months +38.0%" in html and "score rank 2" in html and "held on paper by H82_25k" in html
    )
    assert "no news found" in html and "no close" in html
    assert "Information only, not a trading signal" in html
    assert "+2" not in html and "newsc" not in html.lower()  # no NEWS-C per-share rating, ever
    # a stale report is not shown as today's movers
    assert rv.movers_card(rv.load_report(relay), {}, date(2026, 12, 21)) == ""
    assert "No big moves on Tue 15 Dec" in rv.movers_card(
        rv.parse_report({"schema": 1, "day": D2}), {}, date(2026, 12, 15))  # fmt: skip


def test_BF_D94_report_page_escapes_everything(tmp_path: Path) -> None:
    relay = _report(tmp_path / "relay")
    src = SimpleNamespace(record_view=None, scorecard=None, demo=False, relay_dir=relay)
    v, x = _vx()
    page = app_ops.record_screen(src, v, x, "/record/report", {"d": D2})
    assert page is not None
    html = _main(page)
    assert "Up day: books +0.4%, market +0.5%." in html and "CCC had no close today" in html
    assert "<script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<table>" in html and "No advice to buy or sell" in html and "Made-up news site" in html
    none = app_ops.record_screen(src, v, x, "/record/report", {"d": "2020-01-01"})
    assert none is not None and "No nightly report has arrived yet" in none
    assert app_research.research_md("<img src=x onerror=1>") == "<p>&lt;img src=x onerror=1&gt;</p>"


# ---------------------------------------------------------------- Inbox messages
def _said(j: Journal, record_dir: Path | None) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    tell_record(j, lambda t, k, link: out.append((k, link, t)), record_dir)
    return out


def test_BF_D93_inbox_messages_once_each(tmp_path: Path) -> None:
    root = _paper(tmp_path / "view")
    j = Journal.sqlite()
    daily = {"kind": "job", "job": "daily", "ok": True, "mode": "writer", "day": D2, "head": "ab" * 32,
             "entries": [{"seq": 131, "kind": "daily"}], "seconds": 412.5, "peak_mb": 900.2,
             "failed_steps": ["movers.py"], "evil": "<script>"}  # fmt: skip
    ev = record_record(j, daily, NOW)
    assert ev["job"] == "daily" and ev["head"] == "abababababab" and "evil" not in ev
    said = _said(j, root)
    assert len(said) == 1 and said[0][0] == "report" and said[0][1] == "/record"
    text = said[0][2]
    assert text.startswith(
        "Paper record booked for 15 Dec on the server. Main line on paper: $10,201"
    )
    assert "against A200 since its start, after costs (mostly luck at this stage)" in text
    assert "Ledger entry 131, head abababababab" in text and "movers.py" in text
    assert _said(j, root) == []  # once
    # the shadow's replay and ordinary jobs make no Inbox message (Health shows them)
    record_record(j, {**daily, "mode": "shadow"}, NOW)
    record_record(j, {"kind": "job", "job": "archive", "ok": True, "mode": "writer"}, NOW)
    assert _said(j, root) == []
    record_record(j, {"kind": "report", "ok": True, "day": D2}, NOW)
    record_record(j, {"kind": "compare", "ok": True, "pass": True, "day": D2,
                      "line": "Shadow compare 15 Dec: PASS (A 41/41, B 23/23, C 3/3, D ok)"}, NOW)  # fmt: skip
    record_record(j, {"kind": "compare", "ok": False, "pass": False, "day": "2026-12-16",
                      "line": "Shadow compare 16 Dec: FAIL (A 40/41, B 23/23, C 3/3, D ok)",
                      "diffs": ["out/paper_state/state.json"]}, NOW)  # fmt: skip
    record_record(
        j, {"kind": "relay", "ok": False, "rejected": ["evil.py: not an expected file name"]}, NOW
    )
    said = _said(j, root)
    assert [(k, link) for k, link, _ in said] == [
        ("report", "/record/report?d=2026-12-15"), ("info", "/health"), ("page", "/health"), ("page", "/health")]  # fmt: skip
    assert "PASS (A 41/41" in said[1][2] and said[2][2].startswith(
        "PAGE Shadow compare 16 Dec: FAIL"
    )
    assert (
        "state.json" in said[2][2] and "evil.py" in said[3][2] and "Nothing was used" in said[3][2]
    )
    # junk from the worker is ignored
    assert record_record(j, {"kind": "rm -rf"}, NOW) == {}
    assert record_record(j, {"kind": "job", "job": "../x", "ok": True}, NOW) == {}
    assert rv.summary_line(None).startswith("The record's numbers are not on this server")


# ---------------------------------------------------------------- the missed-job alarm
def _mode(j: Journal, mode: str, at: datetime = NOW, **rec: Any) -> None:
    set_state(j, "host-status", {"record": {"mode": mode, **rec}}, at)


def test_BF_D93_expected_times_match_the_job_table() -> None:
    assert rv.EXPECT == record_jobs.EXPECT
    for _name, _cad, kind, hhmm in rv.EXPECT.values():
        assert kind in ("session", "after") and 0 <= int(hhmm[:2]) < 24


def test_BF_D93_missed_job_alarm_covers_every_moved_job() -> None:
    j = Journal.sqlite()
    sess = [date(2026, 12, 14), date(2026, 12, 15)]
    assert rv.freshness(j, sess, NOW) == []  # the record is not on this server: nothing expected
    _mode(j, "view")
    assert rv.freshness(j, sess, NOW) == []
    _mode(j, "writer")
    t_ok = datetime(2026, 12, 15, 20, 40, tzinfo=ASX_TZ)
    for job in ("daily", "intraday", "export", "newsc-record"):
        record_record(j, {"kind": "job", "job": job, "ok": True, "mode": "writer"}, t_ok)
    for job in ("archive", "collect"):
        record_record(j, {"kind": "job", "job": job, "ok": True, "mode": "writer"},
                      datetime(2026, 12, 15, 8, 50, tzinfo=ASX_TZ))  # fmt: skip
    at = datetime(2026, 12, 15, 22, 0, tzinfo=ASX_TZ)
    fresh = {f.key: f for f in rv.freshness(j, sess, at)}
    assert set(fresh) == {"rec-daily", "rec-intraday", "rec-collect", "rec-archive", "rec-newsc-record",
                          "rec-export"}  # fmt: skip
    assert all(f.status == "ok" for f in fresh.values()), fresh
    # the next day nothing runs: each job goes late at its own time, one incident each
    sess.append(date(2026, 12, 16))
    late = {f.key: f for f in rv.freshness(j, sess, datetime(2026, 12, 16, 21, 31, tzinfo=ASX_TZ))}
    assert (
        late["rec-daily"].status == "late"
        and late["rec-daily"].incident == "rec-daily:late:2026-12-16"
    )
    assert late["rec-newsc-record"].status == "late" and late["rec-intraday"].status == "late"
    assert late["rec-archive"].status == "late"  # the 15 Dec list was due on the 16th by 09:30
    assert late["rec-export"].status == "ok"  # not due until 21:45
    before = {
        f.key: f for f in rv.freshness(j, sess, datetime(2026, 12, 16, 21, 29, tzinfo=ASX_TZ))
    }
    assert before["rec-daily"].status == "ok"
    # a failed job is "failed" with the worker's reason
    record_record(j, {"kind": "job", "job": "daily", "ok": False, "mode": "writer",
                      "error": "refused (ledger shipping): the last ledger entries have not reached OneDrive"},
                  datetime(2026, 12, 16, 20, 28, tzinfo=ASX_TZ))  # fmt: skip
    bad = {f.key: f for f in rv.freshness(j, sess, datetime(2026, 12, 16, 20, 40, tzinfo=ASX_TZ))}
    assert bad["rec-daily"].status == "failed" and "ledger shipping" in bad["rec-daily"].detail
    # the whole-app freshness list (what the alarm pages from) includes them
    allf = ov.freshness(j, "EMG2_18_PAPER", sess, datetime(2026, 12, 16, 21, 31, tzinfo=ASX_TZ))
    assert any(f.key == "rec-daily" and f.bad for f in allf)
    # parallel week: no intraday / collect expected, the compare is
    j2 = Journal.sqlite()
    _mode(j2, "shadow")
    record_record(j2, {"kind": "job", "job": "daily", "ok": True, "mode": "shadow"}, t_ok)
    keys = {f.key for f in rv.freshness(j2, sess[:2], at)}
    assert "rec-compare" in keys and "rec-intraday" not in keys and "rec-collect" not in keys


def test_BF_D93_alarm_pages_once_per_incident() -> None:
    from trader.ops_hooks import OpsHooks

    j = Journal.sqlite()
    _mode(j, "writer")
    record_record(j, {"kind": "job", "job": "export", "ok": True, "mode": "writer"},
                  datetime(2026, 12, 14, 21, 0, tzinfo=ASX_TZ))  # fmt: skip
    said: list[str] = []

    def note(t: str, k: str, link: str) -> int:
        said.append(t)
        return 1

    hooks = OpsHooks(j, "EMG2_18_PAPER", lambda: [date(2026, 12, 14), date(2026, 12, 15)], note)
    at = datetime(2026, 12, 15, 21, 40, tzinfo=ASX_TZ)
    hooks.alerts(at)
    pages = [t for t in said if "Paper record: daily close" in t]
    assert len(pages) == 1 and pages[0].startswith("PAGE Paper record: daily close is late")
    hooks.alerts(at + timedelta(minutes=10))
    assert len([t for t in said if "Paper record: daily close" in t]) == 1


# ---------------------------------------------------------------- Health
def test_BF_D93_health_rows_and_status_cleaning() -> None:
    raw = {"mode": "writer", "disk_level": "tight", "disk_free_gb": 2.71, "ping_set": True,
           "status": {"writer": "server", "role": "writer", "epoch": 2, "seq": 131, "head": "cd" * 32,
                      "chain_ok": True, "evil": "x", "last_kind": "daily"},
           "shipped_head": "ab" * 32, "requests_waiting": 2,
           "view": {"source": "this server", "refreshed": "2026-12-21T20:40:00+1100", "x": "<script>"},
           "timers": {"rec-daily": True, "evil-timer": True}, "token": "not-a-real-value"}  # fmt: skip
    rec = clean_record(raw)
    assert (
        "token" not in rec and "evil" not in rec["status"] and rec["timers"] == {"rec-daily": True}
    )
    assert rec["status"]["head"] == "cd" * 32 and "x" not in rec["view"]
    assert clean_record({"mode": "root", "status": {"writer": "attacker", "head": "zz"}}) == {
        "mode": "off", "status": {}, "ping_set": False, "requests_waiting": 0}  # fmt: skip
    host = clean_status({"record": raw})
    j = Journal.sqlite()
    card = rv.health_card(j, host, NOW)
    assert "written on this server" in card and "Writer = <b>this server</b>" in card
    assert "epoch 2" in card and "cdcdcdcdcdcd" in card and "chain verifies" in card
    assert "behind" in card  # the shipped head differs: the next job waits
    assert "2 research entries waiting" in card and "bigwins record requests" in card
    att = rv.health_attention(host)
    assert (
        "bad",
        "Paper record disk: under 3 GB: month-end and bulk jobs are held",
        "2.7 GB free",
    ) in att
    assert any("research entries waiting" in what for _, what, _ in att)
    broken = {"record": {**rec, "status": {**rec["status"], "chain_ok": False, "writer": "cloud"}}}
    words = [what for _, what, _ in rv.health_attention(broken)]
    assert "Paper record: the ledger does not verify" in words
    assert "Paper record: this server is not the writer any more" in words
    assert rv.health_attention({}) == [] and "not on this server" in rv.health_card(None, {}, NOW)
    # parallel run: the streak and the last comparisons
    _mode(j, "shadow")
    for d, ok in (("2026-12-14", True), ("2026-12-15", True)):
        record_record(j, {"kind": "compare", "pass": ok, "ok": ok, "day": d,
                          "line": f"Shadow compare {d}: PASS (A 2/2, B 2/2, C 1/1, D ok)"}, NOW)  # fmt: skip
    shadow = rv.health_card(j, {"record": {"mode": "shadow"}}, NOW)
    assert (
        "2 days identical in a row" in shadow and "the move needs 5" in shadow and "PASS" in shadow
    )


def test_BF_D93_app_wiring() -> None:
    w = runpy.run_path(str(REPO / "deploy" / "classify.py"))
    assert "trader/record_view.py" in sv.UI_ONLY and w["UI_ONLY"] == sv.UI_ONLY
    assert "record_daily" in SERVER_ACTIONS
    from trader.app_control import NO_CODE_SERVER, SRV_TITLE

    assert "record_daily" in NO_CODE_SERVER and "record_daily" in SRV_TITLE  # confirm only
    cli = (REPO / "trader/bfast_cli.py").read_text()
    assert '"autoupdate", "record"]' in cli and "tell_record(j, notifier.notify" in cli
    compose = (REPO / "deploy/docker-compose.yml").read_text()
    assert (
        compose.count("${RECORD_VIEW_DIR:-/var/lib/bigwins/recordview}:/data/recordview:ro") == 2
    )  # app + trader
    assert "${RELAY_VIEW_DIR:-/var/lib/bigwins/relay/inbox/validated}:/data/relay:ro" in compose
    from trader.bfast_config import load_bfast_config

    cfg = load_bfast_config(REPO / "config/bfast.yaml")
    assert (
        str(cfg.research.record_view_dir) == "/data/recordview"
        and str(cfg.research.relay_dir) == "/data/relay"
    )
    assert "research" in sv.NON_TRADING_CONFIG  # display paths: no strategy-version change
