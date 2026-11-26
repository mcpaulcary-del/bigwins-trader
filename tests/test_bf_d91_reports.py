"""BF-D91: the report display (presentation only). The scoreboard as two bars and a gap
chart with the luck label, "Needs you" directly under it, the daily report and approval
messages opened as cards (the stored text kept word for word), the weekly digest, the
running costs, Health's summary and the research pages' reading order. No figure changes
meaning: every number shown is one the trader already wrote."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from trader import app_ops, app_pages
from trader import app_research as ar
from trader import ops_view as ov
from trader.journal import FillRecord, Journal
from trader.orders import Side
from trader.report import DailyInputs, daily_report
from trader.webui import e

REPO = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- the daily report card


def _report(**kw: Any) -> str:
    fill = FillRecord("x1", "B-1", "EMG2_18_PAPER", "ABC", Side.BUY, 100, Decimal("2.50"),
                      Decimal("1.00"), datetime(2026, 12, 1, 6, 12, tzinfo=UTC))  # fmt: skip
    base: dict[str, Any] = dict(
        book="EMG2_18_PAPER", session=date(2026, 12, 1), real_money=False,
        cash=Decimal("1128.45"), positions={"ABC": 100, "XYZ": 2500, "NOPX": 5},
        prices={"ABC": Decimal("2.5"), "XYZ": Decimal("3.6")}, capital_in=Decimal(10000),
        fills_today=[fill], commission_to_date=Decimal("112.20"),
        orders_today=[("EMG2_18_PAPER-2026-11-30-R-001", "FILLED")], safety="NORMAL",
        sim_value=Decimal("10314.35"), a200_value=Decimal("10244.10"),
        random_twins="Simulated twin at the 80.0 percentile of 20 random twins (their median "
                     "A$10022.53; L11 test (b) needs >= 10)",
        state="state: EMG2 (band index above its 10-month average)",
        fixed_costs_to_date=Decimal("75.62"),
    )  # fmt: skip
    base.update(kw)
    return daily_report(DailyInputs(**base))


def test_BF_D91_daily_report_text_reads_back_to_the_same_figures() -> None:
    text = _report()
    r = app_pages.parse_daily_report(text)
    assert r is not None
    assert r["day"] == date(2026, 12, 1) and r["safety"] == "NORMAL"
    assert r["value"] == Decimal("10378.45") and r["cash"] == Decimal("1128.45")
    assert r["capital"] == Decimal("10000") and r["result"] == pytest.approx(0.0378)
    assert r["brokerage"] == Decimal("112.20") and r["fixed"] == Decimal("75.62")
    assert r["after"] == pytest.approx(0.0303)  # the report's own "after all costs"
    assert r["twin"] == Decimal("10314.35") and r["twin_diff"] == Decimal("64.10")
    assert r["rnd_pct"] == 80.0 and r["rnd_n"] == 20 and r["a200"] == Decimal("10244.10")
    assert [h[0] for h in r["holdings"]] == ["ABC", "NOPX", "XYZ"]  # the report's order
    assert r["holdings"][1][3] is None  # "no price" stays "no price"
    assert r["fills"] == [(True, 100, "ABC", Decimal("2.50"), Decimal("1.00"))]
    assert r["orders"] == ["EMG2_18_PAPER-2026-11-30-R-001 FILLED"]
    assert r["notes"] == ["state: EMG2 (band index above its 10-month average)"]


def test_BF_D91_daily_report_card_result_first_original_kept() -> None:
    text = _report()
    html = app_pages.daily_report_card(text)
    assert html is not None
    for s in ("Close of Tue 1 Dec 2026", "$10,378", "+3.8%", "on the $10,000 put in",
              "After all costs", "+3.0%", "Same money in A200", "$10,244", "no fixed costs",
              "Simulated twin", "book $64 ahead", "Brokerage so far", "$112.20",
              "Fixed costs so far", "$75.62", "Twin check", "Passes", "Holdings · 3",
              "no price", "Bought 100 ABC at $2.50", "Not shown to beat the index.",
              "Original message"):  # fmt: skip
        assert s in html, s
    assert html.index("$10,378") < html.index("Holdings · 3") < html.index("Original message")
    # the stored text is shown word for word (escaped) under "Original message"
    assert e(text) in html
    assert "A$" not in html.split("Original message")[0]  # no "A$" jargon on the card
    # a bad day is not dressed up: breaks and flags are loud, a loss carries the down arrow
    bad = app_pages.daily_report_card(_report(
        safety="HALTED_INTEGRITY", recon_breaks=["ABC: book 100, broker 90"],
        flags=["L11: value below A$7000"], cash=Decimal("-900"), fills_today=[],
        orders_today=[]))  # fmt: skip
    assert bad is not None and "note bad" in bad and "ABC: book 100, broker 90" in bad
    assert "pill bad" in bad and "▼" in bad and "value below $7000" in bad
    assert "Trades today</span><b>none" in bad and "Orders today</span><b>none" in bad


def test_BF_D91_inbox_row_shows_the_days_result_not_ids() -> None:
    row = {"kind": "report", "title": "Daily report EMG2_18_PAPER 2026-12-01 - safety NORMAL",
           "body": _report()}  # fmt: skip
    assert app_pages.msg_line(row, "EMG2_18_PAPER") == (
        "$10,378 · +3.8% on the money put in · all normal")  # fmt: skip
    halted = {**row, "body": _report(safety="HALTED_BUYS")}
    assert app_pages.msg_line(halted).endswith("· Buys halted")
    # a report it cannot read keeps its title; an approval loses only the list's id
    assert app_pages.msg_line({**row, "body": "?"}, "EMG2_18_PAPER") == "Safety NORMAL"
    ap = {"kind": "approval", "title": "Decision 2026-11-30 (regular); list 0a4f12080d8e; "
          "2 order(s)", "body": ""}  # fmt: skip
    assert app_pages.msg_line(ap) == "Decision (regular); 2 orders"


def test_BF_D91_unknown_or_hostile_message_falls_back_to_escaped_text() -> None:
    assert app_pages.parse_daily_report("something else entirely") is None
    assert app_pages.daily_report_card("Value A$1 only") is None
    evil = "Hello <script>alert(1)</script>\n- one <img src=x>\n- two\n\nPAGE 2026-12-01 A$5"
    for kind in ("report", "approval", "info", "page"):
        out = app_pages.message_body({"kind": kind, "body": evil}, "app")
        assert "<script" not in out and "<img" not in out
        assert "&lt;script&gt;" in out and "1 Dec 2026" in out and "$5" in out
    # a digest-style message: a short line before bullets is a heading
    out = app_pages.message_body({"kind": "info", "body": "Needs you\n- one\n- two"}, "app")
    assert '<p class="h3">Needs you</p>' in out and "<li>one</li><li>two</li>" in out


def test_BF_D91_approval_message_as_orders_without_telegram_words() -> None:
    body = ("Decision 2026-11-30 (regular); list 0a4f12080d8e; 2 order(s)\nPAPER\n"
            "Batch EMG2_18_PAPER-2026-11-30-R (per_order), decision 2026-11-30, execution "
            "2026-12-01:\n"
            " 1. SELL 26 S350 LOC lim 12.68 (ref 13.068, ~A$339.77) EMG2_OFF_LIST [RISK_OK]\n"
            " 2. BUY 1,0 BAD\n"
            " 3. BUY 34 S458 LOC lim 12.4 (ref 12.778, ~A$434.45) EMG2_TOP [RISK_OK]\n"
            "Reply /ok EMG2_18_PAPER-2026-11-30-R <n> <code> by 15:20.\n"
            "Or tap a button below, then send your 6-digit code (within 3 minutes).")  # fmt: skip
    html = app_pages.approval_card(body, "app")
    assert html is not None
    shown = html.split("Original message")[0]
    assert "Decided 30 Nov 2026 · orders go on 1 Dec 2026" in shown and "2 orders" in shown
    assert ">Sell</span> <b>26 S350</b>" in shown and "limit $12.68" in shown and "≈ $340" in shown
    assert ">Buy</span> <b>34 S458</b>" in shown
    assert "/ok" not in shown and "tap a button" not in shown  # Telegram is off
    assert "Reply /ok" in html  # ... and still in the original text
    assert "Reply /ok" in (app_pages.approval_card(body, "telegram") or "").split("Original")[0]
    assert app_pages.approval_card("approved all 2 orders of X", "app") is None


# ---------------------------------------------------------------- the scoreboard's pictures


def test_BF_D91_comparison_bars_one_scale_sign_in_words() -> None:
    html = app_ops.cmp_bars([("Big Wins", "$10,390", 0.039, "me"),
                             ("Same money in A200", "$10,244", 0.0195, "ix")], "note")  # fmt: skip
    w = [float(x) for x in re.findall(r"width:([\d.]+)%", html)]
    assert w[0] == pytest.approx(100.0) and w[1] == pytest.approx(50.0)
    assert html.count("▲") == 2 and "<u " not in html  # both gains: no zero mark needed
    # a loss runs left of a drawn zero line and carries the down arrow
    html = app_ops.cmp_bars([("Big Wins", "$9,700", -0.03, "me"),
                             ("A200", "$10,100", 0.01, "ix")])  # fmt: skip
    left = [float(x) for x in re.findall(r"left:([\d.]+)%", html)]
    assert "▼" in html and "▲" in html and html.count("<u ") == 2
    assert left[0] == pytest.approx(0.0) and left[1] == pytest.approx(75.0)  # zero at 75%
    assert "width" not in app_ops.cmp_bars([("A200", "no fund prices yet", None, "ix")])


def test_BF_D91_gap_chart_has_the_level_line_and_says_ahead_or_behind() -> None:
    d0 = date(2026, 12, 1)
    up = app_ops.gap_chart([(d0 + timedelta(days=i), x) for i, x in
                            enumerate((0.0, -40.0, 20.0, 147.4))], "gap")  # fmt: skip
    assert 'class="gapz"' in up and "$147 ahead" in up and "▲" in up
    assert "1 Dec" in up and "4 Dec" in up and "level with A200" in up
    down = app_ops.gap_chart([(d0, 0.0), (d0 + timedelta(days=1), -60.0)], "gap")
    assert "$60 behind" in down and "▼" in down
    assert "level" in app_ops.gap_chart([(d0, 0.0), (d0 + timedelta(days=1), 0.4)], "gap")
    assert app_ops.gap_chart([(d0, 0.0)], "gap") == ""


def test_BF_D91_luck_label_until_24_months() -> None:
    def board(days: int) -> ov.Scoreboard:
        s = date(2026, 12, 1)
        return ov.Scoreboard(s, s + timedelta(days=days), Decimal(10000), Decimal(10400),
                             Decimal(60), None, Decimal(10200), Decimal(5))  # fmt: skip

    assert "Only 6 weeks in" in app_ops.luck_line(board(45))
    assert ov.LUCK in app_ops.luck_line(board(45)) and "Only 3 days in" in app_ops.luck_line(
        board(3)
    )
    assert "Only 23 months in" in app_ops.luck_line(board(700))
    assert app_ops.luck_line(board(731)) == ""
    assert app_ops.how_long(1) == "1 day" and app_ops.how_long(7 * 9) == "9 weeks"


# ---------------------------------------------------------------- the screens (demo data)


@pytest.fixture(scope="module")
def demo_app(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo, demo_control
    from trader.journal import read_only_engine

    demo = build_demo(tmp_path_factory.mktemp("d91") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
    src = Sources(j, index=demo.index, sessions=lambda: demo.sessions, today=lambda: demo.last_day,
                  clock=lambda: demo.now, demo=True, prices=demo.prices,
                  forecast_dir=REPO / "config", scorecard=demo.scorecard, info_dir=demo.info_dir,
                  info_enabled=True)  # fmt: skip
    ctl = demo_control(j, demo)
    return demo, Dashboard(src, actions=ctl.respond)


def _get(d: Any, path: str) -> str:
    st, _, b = d.respond("GET", path, {})
    assert st == 200, path
    return str(b.decode())


def test_BF_D91_home_winning_then_what_to_do_then_what_is_happening(demo_app: Any) -> None:
    _, d = demo_app
    html = _get(d, "/")
    order = [html.index(s) for s in ("Scoreboard ·", 'class="cmp"', "Gap to A200 over time",
                                     ov.LUCK, "Needs your approval", "Also needs you",
                                     "What we know", 'class="hero"', ">Status<")]  # fmt: skip
    assert order == sorted(order)
    # the headline is still the main line against A200 after costs, in the same words
    assert "A200 by $" in html and "after running costs, before tax." in html
    assert "Big Wins, after running costs, before tax" in html and "Same money in A200" in html
    assert "Bars: gain or loss on the $10,000 put in." in html
    # what needs the owner: the demo's late job and its waiting update, each one tap away
    needs = html[html.index("Also needs you") : html.index("What we know")]
    assert "Info archive (announcements) late" in needs and 'href="/health"' in needs
    assert "update is waiting for your approval" in needs and 'href="/strategy"' in needs
    assert html.count("Needs your approval") == 1  # the approval card is shown once


def test_BF_D91_needs_card_calm_when_nothing_to_do() -> None:
    class V:
        safety = "NORMAL"
        now = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)
        next_decision = date(2026, 12, 31)

    x = app_pages.Extras()
    html = app_pages.needs_card(V(), x)
    assert "Nothing needs you right now." in html and "Next decision: Thu 31 Dec, 22:20." in html
    assert app_pages.needs_items(V(), x) == []
    V.safety = "HALTED_BUYS"
    x.update = {"ahead": 2, "strategy": False, "auto": "auto"}  # applies by itself: not a to-do
    items = app_pages.needs_items(V(), x)
    assert [i[3] for i in items] == ["/act"] and "Buys halted" in items[0][1]
    x.update = {"ahead": 2, "strategy": False, "auto": "approval"}
    assert "An app update is waiting" in app_pages.needs_card(V(), x)
    # with an approval waiting and nothing else, the approval card is the whole answer
    x2 = app_pages.Extras(waiting=[app_pages.Waiting("B", 2, Decimal(700), V.now)])
    V.safety = "NORMAL"
    assert app_pages.needs_card(V(), x2) == ""


def test_BF_D91_inbox_opens_reports_as_cards(demo_app: Any) -> None:
    _, d = demo_app
    html = _get(d, "/inbox")
    assert "<pre>PAPER (IBKR paper account" in html  # the original, inside the fold-out
    assert html.count('class="orig"') >= 30 and "After all costs" in html
    assert "Holdings · 17" in html and 'class="list olist"' in html
    first = html[html.index('data-kind="report"') :]
    first = first[: first.index("Original message")]
    assert "A$" not in first and "EMG2_18_PAPER" not in first and "L11 test" not in first
    assert re.search(r"Close of \w{3} \d{1,2} \w{3} \d{4}", first)


def test_BF_D91_digest_action_first_research_unranked_table(demo_app: Any) -> None:
    demo, d = demo_app
    html = _get(d, "/digest")
    order = [html.index(s) for s in ("Weekly digest", 'class="verdict', "Needs you",
                                     "Main strategy against A200", "This week",
                                     "Research lines (information only, unranked)",
                                     "Data collected", "Alerts this week", "Week before")]  # fmt: skip
    assert order == sorted(order)
    block = html[html.index("Research lines (information only, unranked)") :]
    block = block[: block.index("Data collected")]
    assert ov.LUCK in block and "not ranked" in block
    lines = ov.research_lines(demo.scorecard, demo.last_day) or []
    going = [ln.name for ln in lines if ln.ret is not None]
    pos = [block.index(f"<td>{e(n)}</td>") for n in going]
    assert going and pos == sorted(pos)  # the registered order, whatever the results
    for n in (ln.name for ln in lines if ln.ret is None):
        assert n in block[block.index("Not started yet") :]
    # information only: no colour, no arrow, no chart on a research figure
    assert not re.search(r'class="[^"]*\b(up|down)\b', block) and "▲" not in block
    assert "gapsvg" not in block and "spk" not in block and 'class="cmp"' not in block
    assert not re.search(r"\b(leader|leaderboard|best|winner)\b", block, re.I)


def test_BF_D91_research_table_never_sorts() -> None:
    def ln(i: str, r: float | None) -> ov.ResearchLine:
        return ov.ResearchLine(i, f"Line {i}", i, 10000.0, None, r,
                               None if r is None else r - 0.01)  # fmt: skip

    rows = [ln("A", -0.2), ln("B", 0.5), ln("C", None), ln("D", 0.1)]
    html = app_ops.research_table(rows)
    assert html.index("Line A") < html.index("Line B") < html.index("Line D")
    assert "Not started yet: Line C." in html and ov.LUCK in html
    assert "not on this server" in app_ops.research_table(
        None, ["The research record is not on this server yet."])  # fmt: skip


def test_BF_D91_costs_one_headline_one_table_parts_drawn(demo_app: Any) -> None:
    _, d = demo_app
    html = _get(d, "/costs")
    assert "Cost so far" in html and 'class="bignum num">$' in html
    assert "of the account in " in html and "Estimated for a full year: <b>about " in html
    assert html.count('class="split"') == 2 and "Fixed (server, data, tools)" in html
    assert "Trading (brokerage, spread)" in html and "% a year</b>" in html
    # the verdict's remarks are kept as words; its level is the chip
    assert "The first buys make the yearly trading figure too high." in html
    assert re.search(r'class="pill (ok|amber|bad)">(Low|Noticeable|High)<', html)
    # the demo book started this financial year: one table, not the same one twice
    assert html.count("<th>Cost</th>") == 1 and "also since the start" in html
    assert "This financial year" in html and "By month" in html and "/act/costs" in html


def test_BF_D91_split_bar_figures_are_in_the_legend() -> None:
    html = app_ops.split_bar([("Fixed", 3.0, "sg1", "$3"), ("Trading", 1.0, "sg0", "$1"),
                              ("Nothing", 0.0, "sg2", "$0")])  # fmt: skip
    assert "flex:75.00 0 0" in html and "flex:25.00 0 0" in html and html.count("<li>") == 3
    assert "<b>$3</b>" in html and "<b>$0</b>" in html
    assert app_ops.split_bar([("Fixed", 0.0, "sg1", "$0")]) == ""


def test_BF_D91_health_says_what_to_look_at_first(demo_app: Any) -> None:
    _, d = demo_app
    html = _get(d, "/health")
    top = html[html.index("<h1>Health</h1>") : html.index("owner presence")]
    assert re.search(r"\d things? to look at", top)
    assert "Info archive (announcements): late" in top
    assert html.index("to look at") < html.index("Scheduled jobs") < html.index("Versions")

    class V:
        disk_free = (50 * 1024**3, 100 * 1024**3)
        now = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)

    calm = app_ops.health_summary(V(), app_pages.Extras(passphrase_set=True), app_ops.Ops())
    assert "Everything is working" in calm
    V.disk_free = (1024**3, 100 * 1024**3)
    x = app_pages.Extras(passphrase_set=False, reminders={"card": date(2026, 12, 4)})
    items = app_ops.health_attention(V(), x, app_ops.Ops())
    assert [t for t, _, _ in items] == ["bad", "bad", "wait"]  # the serious ones first
    assert "Disk nearly full" in items[0][1] and "renew within 3 days" in items[1][1]


def test_BF_D91_research_reading_order(demo_app: Any) -> None:
    _, d = demo_app
    html = _get(d, "/research/library/research_bw")
    order = [html.index(s) for s in ('class="rans"', "What it means for you", "How sure are we?",
                                     "In short", "Key numbers", "Tests in this study")]  # fmt: skip
    assert order == sorted(order)
    assert 'class="conf c3"' in html and '<details class="rsure">' in html  # Solid; still folded
    assert '<td class="r nw">$20,770</td>' in html  # a number never breaks in the middle
    html = _get(d, "/research")
    card = html[html.index('<section class="rhl"') :]
    card = card[: card.index("</section>")]
    assert card.index("What to do") < card.index("<summary>Why</summary>")  # visible, not folded
    assert "What to do" not in card[card.index("<details") :]
    html = _get(d, "/research/testing")
    assert 'class="chips rjump"' in html and 'href="#g0"' in html and '<section id="g0"' in html
    assert 'href="#grules"' in html and '<section id="grules"' in html


def test_BF_D91_confidence_meter_steps() -> None:
    assert ar.CONF_STEPS == {"solid": 3, "likely": 2, "cant_tell": 1}
    assert set(ar.CONF_STEPS) == set(ar.CONFIDENCE)


def test_BF_D91_display_files_only() -> None:
    """Everything this build changes in ``trader/`` is on the app-only list."""
    from trader import strategy_version as sv

    for f in ("trader/webui.py", "trader/app_pages.py", "trader/app_ops.py",
              "trader/app_research.py", "trader/ops_view.py"):  # fmt: skip
        assert f in sv.UI_ONLY and not sv.is_trading_path(f)


# ---------------------------------------------------------------- a real browser


def test_BF_D91_report_screens_in_a_real_browser(tmp_path: Path) -> None:
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
        r = subprocess.run(["node", str(REPO / "tests" / "browser" / "report_pages.js"), base],
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
    assert out["contrast"] == [], out["contrast"]  # report text at least 4.5:1, light and dark
    assert out["pages"] >= 40 and out["reportOpens"] is True and out["holdingsOpen"] is True
    assert out["barsVisible"] is True
