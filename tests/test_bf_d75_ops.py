"""BF-D75..BF-D80: the honest scoreboard, running costs, research lines (unranked), the
missed-job alarm and the daily-cycle check, the private info archive on the share pages
(announcements, director trades, short positions), the weekly digest and the
previous-version twin. All data here is made up."""

from __future__ import annotations

import csv
import gzip
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pytest

from trader import info_view as iv
from trader import ops_view as ov
from trader.app_store import add_inbox, get_state, inbox_rows, set_state
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.ops_hooks import OpsHooks, cycle_ok_day, record_archive, record_prev_twin
from trader.orders import Side

REPO = Path(__file__).resolve().parents[1]
BOOK = "EMG2_18_PAPER"

BUY_3Y = """                        Appendix 3Y
                        Change of Director's Interest Notice
                        Part 1 - Change of director's relevant interests in securities
                         Direct or indirect interest                        Direct
                         Date of change                                     3 March 2026
                         Class                                              Fully paid ordinary shares
                         Number acquired                                    {acq}
                         Number disposed                                    {disp}
                         Value/Consideration                                {val}
                         Note: If consideration is non-cash, provide details and estimated
                         Nature of change                                   {nature}
                         Example: on-market trade, off-market trade,        {more}
                         exercise of options, issue of securities
                        Part 2 - Change of director's interests in contracts
                         Nature of change                                   Not applicable
"""


def _3y(acq: str = "20,000", disp: str = "Nil", val: str = "$12,500.00",
        nature: str = "On-market trade", more: str = "") -> str:  # fmt: skip
    return BUY_3Y.format(acq=acq, disp=disp, val=val, nature=nature, more=more)


# ---------------------------------------------------------------- director trades (heuristic)


def test_BF_D78_director_trade_on_market_buy_and_sell() -> None:
    t = iv.director_trade(_3y())
    assert t is not None and (t.kind, t.number, t.value) == ("buy", 20000, Decimal(12500))
    t = iv.director_trade(
        _3y(acq="Nil", disp="5,000", val="$1.20 per share", nature="On market sale")
    )
    assert t is not None and (t.kind, t.number, t.value) == ("sell", 5000, Decimal(6000))


def test_BF_D78_options_and_rights_are_never_buys() -> None:
    for nature in ("Issue of options under the employee plan", "Grant of performance rights",
                   "Exercise of options", "Issue of shares under the dividend reinvestment plan",
                   "Participation in the placement"):  # fmt: skip
        t = iv.director_trade(_3y(nature=nature))
        assert t is not None and t.kind == "not a buy", nature


def test_BF_D78_unclear_rather_than_a_guess() -> None:
    cases = [
        _3y(nature="Off-market transfer"),  # not on-market
        _3y(nature="On-market purchase and exercise of options"),  # mixed
        _3y(acq="(a) 1,000 (b) 2,000", disp="Nil"),  # a list: the total is unclear
        _3y(acq="10,000", disp="4,000"),  # both sides
        _3y(nature=""),  # no nature
    ]
    for c in cases:
        t = iv.director_trade(c)
        assert t is not None and t.kind == "unclear", c
    two = _3y().replace("Part 2 -", "Part 1 - Change of director's relevant interests\n Part 2 -")
    t = iv.director_trade(two)
    assert t is not None and t.kind == "unclear"
    t = iv.director_trade(_3y(val="Two lots: $5,000 and $7,500"))
    assert t is not None and t.kind == "buy" and t.value is None  # the value is unclear
    assert iv.director_trade("Quarterly report") is None
    assert iv.director_trade("Appendix 3X Initial Director's Interest Notice").kind == "not a buy"  # type: ignore[union-attr]


# ---------------------------------------------------------------- the archive on the share page


def _archive(root: Path, days: list[date], code: str = "ZZQ") -> None:
    heads = ["Trading Halt", "Proposed issue of securities - ZZQ", "Change of Director's Interest "
             "Notice", "Bidder's Statement", "Half year report"]  # fmt: skip
    for i, d in enumerate(days):
        dd = root / "asx_notices" / str(d)
        (dd / "pdf").mkdir(parents=True)
        h = heads[i % len(heads)]
        with (dd / "list.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["code", "date", "time", "price_sensitive", "headline", "ids_id", "kept"])
            w.writerow([code, f"{d:%d/%m/%Y}", f"9:3{i} am", int(i % 2 == 0), h, f"0100{i:04d}", 1])
            w.writerow(["OTH", f"{d:%d/%m/%Y}", "1:00 pm", 0, "Other news", "02000001", 0])
        if "Interest" in h:
            (dd / "pdf" / f"{code}_0100{i:04d}.txt").write_text(_3y())
        (dd / "DONE").write_text("{}")
    sd = root / "asic_short"
    sd.mkdir(parents=True)
    for d, p in ((days[0], 1.5), (days[-1], 2.25)):
        with gzip.open(sd / f"RR{d:%Y%m%d}-001-SSDailyAggShortPos.csv.gz", "wt") as f:
            f.write("Product,Product Code,Reported Short Positions,Total Product in Issue,"
                    "% of Total Product in Issue Reported as Short Positions\n"
                    f"MADE UP LTD,{code},100,1000,{p}\n")  # fmt: skip


def test_BF_D78_notices_flags_90_days_and_short_position(tmp_path: Path) -> None:
    assert iv.notices(tmp_path, "ZZQ", date(2026, 3, 31)) is None  # nothing collected yet
    days = [date(2026, 3, 2) + timedelta(days=7 * k) for k in range(5)] + [date(2025, 10, 1)]
    _archive(tmp_path, sorted(days))
    ns = iv.notices(tmp_path, "zzq", date(2026, 3, 31))
    assert ns is not None and len(ns) == 5  # the October one is older than 90 days
    assert ns[0].day > ns[-1].day  # newest first
    flags = {f for n in ns for f in n.flags}
    assert {"raise", "halt", "takeover", "director"} <= flags
    trades = [n.trade for n in ns if n.trade is not None]
    assert trades and trades[0].kind == "buy"
    sp = iv.short_position(tmp_path, "ZZQ")
    assert sp is not None and sp.pct == pytest.approx(2.25) and sp.before_pct == pytest.approx(1.5)
    assert iv.short_position(tmp_path, "NOPE") is None
    st = iv.status(
        tmp_path, [date(2026, 3, 2), date(2026, 3, 3), date(2026, 3, 9)], date(2026, 3, 31)
    )
    assert st.last == date(2026, 3, 30) and date(2026, 3, 3) in st.missed


def test_BF_D78_share_page_shows_not_collected_yet(tmp_path: Path) -> None:
    from trader.app_ops import announcements

    html = announcements(None, "ZZQ", date(2026, 3, 31))
    assert "Not collected yet" in html
    html = announcements(tmp_path, "ZZQ", date(2026, 3, 31))
    assert "Not collected yet" in html and "Short position: not collected yet" in html


# ---------------------------------------------------------------- scoreboard and costs


def test_BF_D75_scoreboard_after_all_costs_against_a200() -> None:
    series = [(date(2026, 1, 1), Decimal(10000)), (date(2026, 12, 31), Decimal(11000))]
    idx = [(date(2026, 1, 1), 1.0), (date(2026, 12, 31), 1.12)]
    sb = ov.scoreboard(series, idx, Decimal(10000), Decimal(600), Decimal(10), Decimal(50))
    assert sb is not None
    assert sb.fixed == Decimal("600.00")  # the whole year
    assert sb.after_costs == Decimal("10350.00")
    assert sb.a200 == Decimal("11188.80")
    assert sb.gap == Decimal("-838.80")
    assert sb.sentence == "Behind A200 by $839 after all costs."
    up = ov.scoreboard(series, [(date(2026, 1, 1), 1.0), (date(2026, 12, 31), 1.01)],
                       Decimal(10000), Decimal(0))  # fmt: skip
    assert up is not None and up.sentence.startswith("Ahead of A200 by $900")
    assert ov.scoreboard([], idx, Decimal(10000), Decimal(600)) is None


class _Fill:
    def __init__(self, d: date, qty: int, price: str, comm: str) -> None:
        self.executed_at = datetime.combine(d, time(16, 10), ASX_TZ)
        self.qty, self.price, self.commission, self.side = (
            qty,
            Decimal(price),
            Decimal(comm),
            Side.BUY,
        )


def test_BF_D76_costs_by_month_year_to_date_and_verdict() -> None:
    series = [(date(2026, 6, 1), Decimal(10000)), (date(2026, 8, 31), Decimal(10200))]
    fills = [
        _Fill(date(2026, 6, 2), 100, "5.00", "6.00"),
        _Fill(date(2026, 8, 3), 100, "5.00", "6.00"),
    ]
    fc = ov.FixedCosts((("server", "Server", Decimal(365)), ("data", "Data", Decimal(0)),
                        ("other", "Other", Decimal(0))), "config")  # fmt: skip
    r = ov.cost_report(fills, series, date(2026, 8, 31), fc, Decimal("0.005"))
    assert r is not None
    assert [m.label for m in r.months] == ["Aug 26", "Jul 26", "Jun 26"]
    assert r.since_start.brokerage == Decimal(12) and r.since_start.spread == Decimal("5.00")
    assert r.since_start.fixed == Decimal(92)  # 92 days at $1 a day
    assert r.ytd.start == date(2026, 7, 1) and r.ytd.brokerage == Decimal(6)
    assert r.ytd.share(r.ytd.total) == pytest.approx(float(r.ytd.total / Decimal(10200)))
    assert r.verdict.startswith(("Low", "Noticeable", "High"))


def test_BF_D76_fixed_costs_app_then_config_then_total() -> None:
    j = Journal.sqlite()
    fc = ov.fixed_costs(
        j, {"server": Decimal(0), "data": Decimal(0), "other": Decimal(0)}, Decimal(600)
    )
    assert fc.source == "total" and fc.per_year == Decimal(600)
    fc = ov.fixed_costs(
        j, {"server": Decimal(300), "data": Decimal(200), "other": Decimal(0)}, Decimal(600)
    )
    assert fc.source == "config" and fc.per_year == Decimal(500)
    set_state(
        j, "running-costs", {"server": "240", "data": "360", "other": "50"}, datetime.now(ASX_TZ)
    )
    fc = ov.fixed_costs(j, {"server": Decimal(300)}, Decimal(600))
    assert fc.source == "app" and fc.per_year == Decimal(650)
    set_state(j, "running-costs", {}, datetime.now(ASX_TZ))  # all cleared in the app
    assert ov.fixed_costs(j, None, Decimal(600)).source == "total"


# ---------------------------------------------------------------- research lines


def test_BF_D75_research_lines_kept_unranked_and_labelled(tmp_path: Path) -> None:
    f = tmp_path / "scorecard_latest.csv"
    with f.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["asof", "book", "kind", "capital", "nav", "return_since_start", "vs_a200"])
        w.writerow(["2026-12-01", "H82_25k", "h82", 25000, 25500, 0.02, 0.01])
        w.writerow(["2026-12-01", "H82_lifecycle_5k", "h82", 5000, 5050, 0.01, 0.0])
        w.writerow(["2026-12-01", "EMG2_MOON_TOP5", "moon", 10000, 13000, 0.3, 0.29])
        w.writerow(["2026-12-01", "SHADOW_CXL_25k", "SHADOW_CXL", 25000, 26000, 0.04, 0.03])
        w.writerow(["2026-12-01", "RND_25k (200 seeds)", "random control", 25000, "", -0.05, ""])
    lines = ov.research_lines(f, date(2026, 12, 2))
    assert lines is not None
    assert [ln.id for ln in lines] == [k for k, _, _ in ov.KEPT_LINES]  # registered order
    h82 = next(ln for ln in lines if ln.id == "H82")
    assert h82.book == "H82_25k"  # the exact names, in order of preference
    assert not any("CXL" in (ln.book or "") for ln in lines)  # retired lines are not shown
    assert ov.research_lines(tmp_path / "missing.csv", date(2026, 12, 2)) is None
    from trader.app_ops import Ops, research_section

    html = research_section(Ops(research=lines), date(2026, 12, 2))
    assert html.count(ov.LUCK) >= len(lines) and "not ranked" in html
    assert "rank" not in html.replace("not ranked", "")  # no leaderboard words
    assert "Retired 31 Dec 2026" not in html
    assert "Retired 31 Dec 2026" in research_section(Ops(research=lines), date(2027, 1, 5))


# ---------------------------------------------------------------- missed-job alarm


def _collect(out: list[tuple[str, str, str]]) -> Any:
    def notify(text: str, kind: str = "", link: str = "", *a: Any, **k: Any) -> int:
        out.append((text, kind, link))
        return 0

    return notify


def _sessions(a: date, b: date) -> list[date]:
    return [
        a + timedelta(days=k)
        for k in range((b - a).days + 1)
        if (a + timedelta(days=k)).weekday() < 5
    ]


def test_BF_D77_freshness_late_failed_and_one_push_per_incident() -> None:
    j = Journal.sqlite()
    sess = _sessions(date(2026, 3, 2), date(2026, 3, 13))
    t0 = datetime(2026, 3, 10, 23, 0, tzinfo=ASX_TZ)
    j.mark_job(f"value:{BOOK}:2026-03-09", {"value": "10000"}, t0)
    j.mark_job("store-refresh:2026-03-10", {}, t0)
    set_state(j, "backup-last", {"ok": False, "error": "disk full"}, t0)
    set_state(j, "restore-test-last", {"ok": True}, t0 - timedelta(days=2))
    now = datetime(2026, 3, 11, 9, 0, tzinfo=ASX_TZ)
    fr = {f.key: f for f in ov.freshness(j, BOOK, sess, now, info_enabled=False)}
    assert fr["daily"].status == "late" and "10 Mar" in fr["daily"].detail
    assert fr["prices"].status == "ok" and fr["restore"].status == "ok"
    assert fr["backup"].status == "failed" and fr["info"].status == "off"
    sent: list[tuple[str, str, str]] = []
    hooks = OpsHooks(j, BOOK, lambda: sess, _collect(sent))
    set_state(j, "digest-last", "2026-03-06", now)  # (the digest is tested on its own)
    hooks.tick(now)
    # the failed backup is already paged by the trader itself: only the late daily run here
    assert len(sent) == 1 and sent[0][0].startswith("PAGE Trader daily run")
    assert sent[0][2] == "/health"
    hooks.tick(now + timedelta(minutes=10))  # the same incidents: no second push
    assert len(sent) == 1
    fr = {f.key: f for f in ov.freshness(j, BOOK, sess, now + timedelta(days=1), True)}
    assert fr["info"].status == "late"  # switched on, nothing stored


def test_BF_D77_daily_cycle_check_day() -> None:
    j = Journal.sqlite()
    sess = _sessions(date(2026, 3, 2), date(2026, 3, 13))
    d = date(2026, 3, 10)
    at = datetime.combine(d, time(23, 5), ASX_TZ)
    assert cycle_ok_day(j, BOOK, sess, at) is None  # not started
    j.mark_job(f"value:{BOOK}:{d}", {"value": "1"}, at)
    assert cycle_ok_day(j, BOOK, sess, at) is None  # no report job
    j.mark_job(f"{d}:22:45:report", None, at)
    assert cycle_ok_day(j, BOOK, sess, at) == d
    assert cycle_ok_day(j, BOOK, sess, at.replace(hour=22)) is None  # before 23:00
    assert cycle_ok_day(j, BOOK, sess, datetime(2026, 3, 14, 23, 30, tzinfo=ASX_TZ)) == date(
        2026, 3, 14
    )
    j.mark_job(f"value:{BOOK}:2026-03-11", {"value": "1"}, at)
    j.mark_job("2026-03-11:22:45:report", {"error": "boom"}, at)
    assert cycle_ok_day(j, BOOK, sess, datetime(2026, 3, 11, 23, 30, tzinfo=ASX_TZ)) is None


def test_BF_D77_daily_url_is_a_secret_never_in_the_repo() -> None:
    from trader.secrets import KNOWN_SECRETS
    from trader.server_status import clean_status

    assert "healthchecks_daily_url" in KNOWN_SECRETS
    sh = (REPO / "deploy" / "bigwins.sh").read_text()
    assert "healthchecks_daily_url" in sh and "hc-ping.com/" not in sh
    st = clean_status({"daily_ping_set": True, "daily_ping": "https://hc-ping.com/x"})
    assert st["daily_ping_set"] is True and "daily_ping" not in st  # a URL is never kept


# ---------------------------------------------------------------- digest and twins


def test_BF_D79_weekly_digest_once_on_friday_after_the_report(tmp_path: Path) -> None:
    j = Journal.sqlite()
    j.add_cash(BOOK, "DEPOSIT", Decimal(10000), "test")
    sess = _sessions(date(2026, 3, 2), date(2026, 3, 13))
    for k, d in enumerate(sess[:10]):
        j.mark_job(f"value:{BOOK}:{d}", {"value": str(10000 + 10 * k)},
                   datetime.combine(d, time(22, 45), ASX_TZ))  # fmt: skip
    add_inbox(j, datetime(2026, 3, 11, 12, tzinfo=ASX_TZ), "page", "PAGE test alert", "x")
    idx = [(d, 1.0 + 0.002 * k) for k, d in enumerate(sess)]
    sent: list[tuple[str, str, str]] = []
    hooks = OpsHooks(j, BOOK, lambda: sess, _collect(sent),
                     index=lambda: idx)  # fmt: skip
    set_state(j, "digest-last", "2026-03-06", datetime(2026, 3, 6, 23, tzinfo=ASX_TZ))
    assert not hooks.weekly(datetime(2026, 3, 13, 22, 0, tzinfo=ASX_TZ))  # before 22:55
    assert hooks.weekly(datetime(2026, 3, 13, 23, 0, tzinfo=ASX_TZ))
    assert not hooks.weekly(datetime(2026, 3, 13, 23, 30, tzinfo=ASX_TZ))  # once a week
    text, kind, link = sent[0]
    assert kind == "info" and link == "/digest?w=2026-03-13"
    assert text.startswith("Weekly digest") and "A200" in text and "PAGE test alert" in text
    assert "Research lines" in text and ov.LUCK in text


def test_BF_D78_D80_host_results_are_cleaned(tmp_path: Path) -> None:
    j = Journal.sqlite()
    now = datetime(2026, 12, 2, 8, tzinfo=ASX_TZ)
    rec = record_archive(j, {"ok": True, "day": "2026-12-01", "rows": "690", "pdfs": 120,
                             "error": "token=abcdef", "evil": "<script>"}, now)  # fmt: skip
    assert rec == {"ok": True, "day": "2026-12-01", "rows": 690, "pdfs": 120, "error": "[hidden]"}
    # the previous-version twin: two dry-run journals with daily values
    for name, k in (("new", 1.0), ("prev", 0.99)):
        d = tmp_path / name
        d.mkdir()
        jj = Journal.sqlite(str(d / "dryrun_2026-12-01_2026-12-05.sqlite3"))
        for i, day in enumerate(("2026-12-01", "2026-12-02", "2026-12-03")):
            jj.mark_job(f"value:{BOOK}:{day}", {"value": str(10000 * k + i)}, now)
        jj.engine.dispose()
    (tmp_path / "prev" / "strategy_changelog.yaml").write_text('versions:\n  - version: "v1.0"\n')
    rec = record_prev_twin(j, tmp_path, BOOK, {"ok": True, "since": "2026-12-01"}, now)
    assert rec["ok"] and rec["prev_label"] == "v1.0" and rec["new_label"] == "unversioned"
    assert rec["new"][-1] == ["2026-12-03", 10002.0] and rec["prev"][0] == ["2026-12-01", 9900.0]
    from trader.app_ops import prev_twin_section

    html = prev_twin_section(get_state(j, "prev-twin")[0])  # type: ignore[index]
    assert "So far this version is ahead by $100" in html and ov.LUCK in html
    assert "simulated" in html and 'class="verdict' not in html.replace("verdict2", "")
    assert "Nothing to compare yet" in prev_twin_section(None)


# ---------------------------------------------------------------- the screens (demo data)


@pytest.fixture(scope="module")
def demo_app(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo, demo_control
    from trader.journal import read_only_engine

    demo = build_demo(tmp_path_factory.mktemp("d") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
    src = Sources(j, index=demo.index, sessions=lambda: demo.sessions, today=lambda: demo.last_day,
                  clock=lambda: demo.now, demo=True, prices=demo.prices,
                  forecast_dir=REPO / "config", scorecard=demo.scorecard, info_dir=demo.info_dir,
                  info_enabled=True)  # fmt: skip
    ctl = demo_control(j, demo)
    return demo, Dashboard(src, actions=ctl.respond)


def _get(d: Any, path: str) -> tuple[int, str]:
    st, _, b = d.respond("GET", path, {})
    return st, b.decode()


def test_BF_D75_home_leads_with_the_honest_scoreboard(demo_app: Any) -> None:
    _, d = demo_app
    st, html = _get(d, "/")
    assert st == 200
    i = html.index("Scoreboard · after running costs, before tax")  # no tax rate here (M2)
    assert i < html.index('class="hero"')  # the headline comes first
    assert "A200 by $" in html and "after running costs, before tax." in html
    assert "after all costs" not in html
    assert "Same money in A200" in html and "Fixed running costs" in html
    assert "$21.0k against $18.6k" in html and "Research lines (information only)" in html
    assert "Info archive (announcements) late" in html  # the demo's late job is flagged


def test_BF_D77_health_costs_digest_and_share_page(demo_app: Any) -> None:
    demo, d = demo_app
    st, html = _get(d, "/health")
    assert st == 200 and "Scheduled jobs" in html and "Trader daily run" in html
    assert "Disk" in html and "Versions" in html and "Info archive" in html
    st, html = _get(d, "/costs")
    assert st == 200 and "This financial year" in html and "% of account" in html
    assert "/act/costs" in html
    st, html = _get(d, "/digest")
    assert st == 200 and "Weekly digest" in html and "unranked" in html
    st, html = _get(d, "/server")
    assert 'href="/health"' in html and 'href="/costs"' in html
    st, html = _get(d, "/strategy")
    assert "Did the last update help?" in html and "simulated" in html
    st, html = _get(d, "/holdings")
    code = html.split('href="/holdings/')[1].split('"')[0]
    st, html = _get(d, f"/holdings/{code}")
    assert st == 200 and "Announcements · last 90 days" in html and "Short position" in html


def test_BF_D76_running_costs_edit_through_the_control_server() -> None:
    from tests.test_bf_app_actions import OWNER, _post, _session, _setup
    from tests.test_bf_execution import T_APPROVE

    j, _, ctl, _, _ = _setup()
    sess = _session(ctl)
    st, body = _post(
        ctl, {"server": "240", "data": "360.5", "other": ""}, session=sess, path="/act/costs"
    )
    assert st == 200 and "running costs saved" in body
    got = get_state(j, "running-costs")
    assert got is not None and got[0]["history"][-1] == {
        "server": "240.00", "data": "360.50", "other": "0.00",
        "from": str(T_APPROVE.astimezone(ASX_TZ).date())}  # fmt: skip
    st, body = _post(ctl, {"server": "abc"}, session=sess, path="/act/costs")
    assert "Not saved" in body
    assert any("running costs changed" in r["title"] for r in inbox_rows(j))
    # no form token: refused
    st, _, _ = ctl.respond("POST", "/act/costs", {"Tailscale-User-Login": OWNER},
                           urlencode({"server": "1"}).encode())  # fmt: skip
    assert st == 403
    assert json.dumps(got[0])
