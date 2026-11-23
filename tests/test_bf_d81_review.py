"""BF-D81: the review fixes of BF-D75..BF-D80 (M1-M4, S1-S7, N1-N8). All data is made up;
the research-line fixtures only copy the record's book-name pattern."""

from __future__ import annotations

import csv
import gzip
import importlib.util
import subprocess
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from trader import info_view as iv
from trader import ops_view as ov
from trader.app_store import set_state
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.ops_hooks import OpsHooks

REPO = Path(__file__).resolve().parents[1]
BOOK = "EMG2_18_PAPER"


def _collect(out: list[tuple[str, str, str]]) -> Any:
    def notify(text: str, kind: str = "", link: str = "", *a: Any, **k: Any) -> int:
        out.append((text, kind, link))
        return 0

    return notify


def _sessions(a: date, b: date, holidays: tuple[date, ...] = ()) -> list[date]:
    out = []
    d = a
    while d <= b:
        if d.weekday() < 5 and d not in holidays:
            out.append(d)
        d += timedelta(days=1)
    return out


# ---------------------------------------------------------------- M1 classification


def test_BF_D81_M1_display_files_are_ui_only_in_both_classifiers() -> None:
    import runpy

    from trader import strategy_version as sv

    w = runpy.run_path(str(REPO / "deploy" / "classify.py"))
    for f in ("trader/ops_view.py", "trader/info_view.py", "trader/ops_hooks.py",
              "trader/app_ops.py"):  # fmt: skip
        assert f in sv.UI_ONLY and f in w["UI_ONLY"]
        assert not sv.is_trading_path(f) and w["classify"]([f]) == "app"
    assert w["UI_ONLY"] == sv.UI_ONLY


def test_BF_D81_M1_this_build_changes_no_strategy_file_or_setting() -> None:
    """c162146..HEAD: no strategy file (``STRATEGY_FILES``) and no strategy setting changed;
    the trading paths it does change are engineering files, listed here on purpose."""
    from trader.strategy_version import STRATEGY_FILES, config_hash, is_trading_path
    from trader.yamlio import load_yaml

    try:
        files = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", "c162146", "HEAD"],
                               capture_output=True, text=True, check=True).stdout.split()  # fmt: skip
        old = subprocess.run(["git", "-C", str(REPO), "show", "c162146:config/bfast.yaml"],
                             capture_output=True, text=True, check=True).stdout  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("the base commit is not in this checkout (shallow clone)")
    assert not [f for f in files for s in STRATEGY_FILES if f.startswith(s)]
    new = (REPO / "config" / "bfast.yaml").read_text()
    assert config_hash(load_yaml(old) or {}) == config_hash(load_yaml(new) or {})
    engineering = {
        "trader/bfast_cli.py", "trader/bfast_config.py", "trader/app_control.py",
        "trader/app_store.py", "trader/secrets.py", "trader/share_pages.py",
        "trader/strategy_version.py", "config/bfast.yaml", "pyproject.toml",
    }  # fmt: skip
    trading = {f for f in files if is_trading_path(f) and not f.startswith("deploy/")}
    assert trading <= engineering, trading - engineering


# ---------------------------------------------------------------- M2 / S1 the scoreboard


def test_BF_D81_M2_without_tax_it_says_before_tax() -> None:
    series = [(date(2026, 1, 1), Decimal(10000)), (date(2026, 12, 31), Decimal(11000))]
    idx = [(date(2026, 1, 1), 1.0), (date(2026, 12, 31), 1.05)]
    no_tax = ov.scoreboard(series, idx, Decimal(10000), Decimal(0))
    assert no_tax is not None and no_tax.basis == "after running costs, before tax"
    assert no_tax.sentence == "Ahead of A200 by $500 after running costs, before tax."
    taxed = ov.scoreboard(series, idx, Decimal(10000), Decimal(0), tax=Decimal(100))
    assert taxed is not None and taxed.sentence.endswith("after all costs.")
    j = Journal.sqlite()
    dg = ov.digest(j, BOOK, date(2026, 12, 31), no_tax, None, None, [])
    assert "before tax" in dg.text() and "after all costs" not in dg.text()


def test_BF_D81_S1_each_cash_move_goes_into_a200_on_its_own_day() -> None:
    d0, d1, d2 = date(2026, 1, 5), date(2026, 6, 1), date(2026, 12, 31)
    idx = [(d0, 1.0), (d1, 1.10), (d2, 1.21)]
    series = [(d0, Decimal(10000)), (d2, Decimal(25000))]
    flows = [(d0, Decimal(10000)), (d1, Decimal(11000))]
    sb = ov.scoreboard(series, idx, flows, Decimal(0))
    assert sb is not None and sb.capital == Decimal(21000)
    assert sb.a200 == Decimal("24200.00")  # 10,000 x 1.21 + 11,000 x 1.10
    w = ov.scoreboard(series, idx, [(d0, Decimal(10000)), (d1, Decimal(-5500))], Decimal(0))
    assert w is not None and w.capital == Decimal(4500)
    assert w.a200 == Decimal("6050.00")  # (10,000 - 5,000 units) x 1.21
    # entry costs are taken from each deposit
    c = ov.scoreboard(series, idx, flows, Decimal(0), lambda a: Decimal(10))
    assert c is not None and c.a200_cost == Decimal(20)
    j = Journal.sqlite()
    j.add_cash(BOOK, "DEPOSIT", Decimal(10000), "t", datetime.combine(d0, time(9), ASX_TZ))
    j.add_cash(BOOK, "WITHDRAWAL", Decimal(5500), "t", datetime.combine(d1, time(9), ASX_TZ))
    assert ov.book_flows(j, BOOK) == [(d0, Decimal(10000)), (d1, Decimal(-5500))]


# ---------------------------------------------------------------- M3 the cost verdict


class _Fill:
    def __init__(self, d: date, qty: int, price: str, comm: str) -> None:
        self.executed_at = datetime.combine(d, time(16, 10), ASX_TZ)
        self.qty, self.price, self.commission = qty, Decimal(price), Decimal(comm)


def test_BF_D81_M3_verdict_from_the_same_yearly_parts() -> None:
    fc = ov.FixedCosts((("total", "Fixed", Decimal(600)),), "total")
    series = [(date(2026, 12, 1), Decimal(10000)), (date(2026, 12, 31), Decimal(10000))]
    fills = [_Fill(date(2026, 12, 1), 1000, "10.00", "10.00")]  # $10,000 of buys
    r = ov.cost_report(fills, series, date(2026, 12, 31), fc, Decimal("0.005"))
    assert r is not None and r.days == 31
    assert r.fixed_annual == pytest.approx(0.06)
    assert r.trading_annual == pytest.approx(0.006 * 365 / 31)
    assert r.verdict.startswith("High: so far") and "Estimated for a full year" in r.verdict
    assert "trading costs are most of it" in r.verdict and "too high" in r.verdict
    long = [(date(2026, 1, 1), Decimal(10000)), (date(2026, 12, 31), Decimal(10000))]
    r2 = ov.cost_report(fills[:0], long, date(2026, 12, 31), fc, Decimal("0.005"))
    assert r2 is not None and r2.verdict.startswith("High: about 6.0% of the account a year")
    assert "fixed costs are most of it" in r2.verdict and "so far" not in r2.verdict


# ---------------------------------------------------------------- M4 one scoreboard


def _book(j: Journal, sess: list[date]) -> list[tuple[date, float]]:
    j.add_cash(BOOK, "DEPOSIT", Decimal(10000), "t", datetime.combine(sess[0], time(9), ASX_TZ))
    for k, d in enumerate(sess):
        j.mark_job(f"value:{BOOK}:{d}", {"value": str(10000 + 15 * k)},
                   datetime.combine(d, time(22, 45), ASX_TZ))  # fmt: skip
    return [(d, 1.0 + 0.001 * k) for k, d in enumerate(sess)]


def test_BF_D81_M4_digest_and_app_show_the_same_scoreboard() -> None:
    from trader import app_ops
    from trader.app_pages import Extras
    from trader.dashboard import Sources, collect

    j = Journal.sqlite()
    sess = _sessions(date(2026, 3, 2), date(2026, 3, 27))
    idx = _book(j, sess)
    now = datetime(2026, 3, 27, 23, 5, tzinfo=ASX_TZ)

    def comm(a: Decimal) -> Decimal:
        return Decimal("6.60")

    src = Sources(j, BOOK, index=lambda: idx, sessions=lambda: sess, today=lambda: now.date(),
                  clock=lambda: now, commission=comm, fund_half_spread=Decimal("0.0005"))  # fmt: skip
    v = collect(src)
    o = app_ops.collect(src, v, True)
    app_dg = app_ops.digest_for(src, v, o, date(2026, 3, 27), Extras())
    hooks = OpsHooks(j, BOOK, lambda: sess, _collect([]), index=lambda: idx, commission=comm)
    hook_dg = hooks.build(date(2026, 3, 27), now)
    assert o.score is not None and hook_dg.sentence == o.score.sentence == app_dg.sentence
    assert hook_dg.main == app_dg.main
    assert o.score.a200_cost == Decimal("11.60")  # $6.60 brokerage + 0.05% of $10,000


# ---------------------------------------------------------------- S2 research lines


def test_BF_D81_S2_exact_book_names_never_twins_or_comparators(tmp_path: Path) -> None:
    head = ["asof", "book", "kind", "capital", "nav", "return_since_start", "vs_a200"]
    rows = [
        ["2026-12-04", "EMG2_25k", "SHADOW_EMG2", 25000, 25100, 0.004, 0.001],
        ["2026-12-04", "EMG2_100k", "SHADOW_EMG2", 100000, 100900, 0.009, 0.002],
        ["2026-12-04", "BLIND3_RND_10k_s001", "PAPER BLIND3", 10000, 13000, 0.3, 0.3],
        ["2026-12-04", "BLIND3_10k", "PAPER BLIND3 (information only)", 10000, 10050, 0.005, 0.0],
        ["2026-12-04", "MOON_TOP5_RND_s001", "MOON_TOP5", 10000, 15000, 0.5, 0.5],
        ["2026-12-04", "EMG2_MOON_TOP5", "side line MOON_TOP5 (information only)", 10000, "", "",
         ""],
        ["2026-12-04", "EMG2_18_REF_RND_s003", "random", 10000, 9000, -0.1, -0.1],
        ["2026-12-04", "CMP_A200_25k", "comparator", 25000, 25000, 0.0, ""],
        ["2026-12-04", "EMG2_18_SIM_BT_C6_WIDE", "side line WIDE (information only)", 10000,
         10200, 0.02, 0.01],
    ]  # fmt: skip
    for name, data in (("scorecard_latest.csv", rows),
                       ("scorecard_history.csv", [[*r[:1], *r[1:]] for r in rows]
                        + [["2026-12-01", "EMG2_100k", "x", 100000, 100000, 0, 0]])):  # fmt: skip
        with (tmp_path / name).open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows(sorted(data, key=lambda r: str(next(iter(r)))))
    lines = {ln.id: ln for ln in ov.research_lines(tmp_path / "scorecard_latest.csv",  # type: ignore[union-attr]
                                                   date(2026, 12, 5))}  # fmt: skip
    assert lines["EMG2"].book == "EMG2_100k" and lines["EMG2"].start == "2026-12-01"
    assert lines["BLIND3"].book == "BLIND3_10k" and lines["BLIND3"].ret == pytest.approx(0.005)
    assert lines["MOON_TOP5"].book == "EMG2_MOON_TOP5" and lines["MOON_TOP5"].ret is None
    assert lines["REF"].book is None  # only its twin row exists: never shown in its place
    assert lines["WIDE"].ret == pytest.approx(0.02)
    for _, _, books in ov.KEPT_LINES:
        assert not any("RND" in b or b.startswith("CMP_") for b in books)
    from trader.app_ops import Ops, research_section

    html = research_section(Ops(research=list(lines.values())), date(2026, 12, 5))
    assert "$100,000 book" in html and "from 1 Dec 2026" in html


# ---------------------------------------------------------------- S3 the previous-version twin


def test_BF_D81_S3_twin_runs_offline_without_secrets_on_its_own_volume() -> None:
    sh = (REPO / "deploy" / "bigwins.sh").read_text()
    body = sh[sh.index("run_twin() {") : sh.index("do_prev_twin() {")]
    assert "--network none" in body and "-u 10001:10001" in body
    assert "$SECRETS" not in body and "/run/secrets" not in body and "traderout" not in body
    assert "$TWINS_VOL:/twins" in body and "TWINS_VOL=bigwins_twins" in sh
    twin = sh[sh.index("do_prev_twin() {") : sh.index("EXTRA_UNITS=")]
    assert "archive HEAD config" in twin and "bfast.local.yaml" not in twin  # S3 e
    assert "flock -n" in twin
    compose = (REPO / "deploy" / "docker-compose.yml").read_text()
    assert "twins:/data/twins:ro" in compose and "name: bigwins_twins" in compose


def test_BF_D81_S3_twin_lateness_allows_the_weekend() -> None:
    j = Journal.sqlite()
    sat = datetime(2026, 3, 14, 1, 25, tzinfo=ASX_TZ)  # the Saturday 01:20 run
    set_state(j, "prev-twin", {"ok": True, "since": "2026-03-02"}, sat)
    mon = datetime(2026, 3, 16, 9, 0, tzinfo=ASX_TZ)
    fr = {f.key: f for f in ov.freshness(j, BOOK, [], mon)}
    assert fr["twin"].status == "ok"
    fr = {f.key: f for f in ov.freshness(j, BOOK, [], sat + timedelta(hours=81))}
    assert fr["twin"].status == "late"


def test_BF_D81_S3_dry_run_twins_make_month_end_decisions(tmp_path: Path) -> None:
    """The twin replay (``trader-bf dry-run``) decides at each month-end by itself
    (``BfApp.decision_kind``): the demo, a dry run with only a start decision, has one."""
    from trader.dashboard_demo import build_demo

    demo = build_demo(tmp_path / "j.sqlite", days=45, random_twins=0)
    j = Journal.sqlite(str(demo.journal_path))
    days = {k.rsplit(":", 1)[1] for k, _ in j.job_records(f"decide:{BOOK}:")}
    assert len(days) >= 2  # the start and at least one month-end


# ---------------------------------------------------------------- S4 the alarm


def test_BF_D81_S4_bad_keys_monitor_failure_reminders_and_holidays() -> None:
    j = Journal.sqlite()
    hol = (date(2026, 3, 9),)  # a made-up public holiday on Monday
    sess = _sessions(date(2026, 3, 2), date(2026, 3, 13), hol)
    j.mark_job("store-refresh:oops", {}, datetime(2026, 3, 6, 22, tzinfo=ASX_TZ))
    j.mark_job("store-refresh:2026-03-06", {}, datetime(2026, 3, 6, 22, tzinfo=ASX_TZ))
    j.mark_job(f"value:{BOOK}:2026-03-06", {"value": "1"}, datetime(2026, 3, 6, 23, tzinfo=ASX_TZ))
    j.mark_job("store-refresh:oops2", {}, datetime(2026, 3, 7, 22, tzinfo=ASX_TZ))
    # Monday 9 March is a holiday: on Tuesday morning nothing is late
    tue = datetime(2026, 3, 10, 9, 0, tzinfo=ASX_TZ)
    fr = {f.key: f for f in ov.freshness(j, BOOK, sess, tue)}
    assert fr["prices"].status == "ok" and fr["daily"].status == "ok"
    # a monitor failure pages once a day, the other hook still runs
    sent: list[tuple[str, str, str]] = []
    h = OpsHooks(j, BOOK, lambda: sess, _collect(sent))
    set_state(j, "digest-last", "2026-03-06", tue)

    def boom(now: datetime) -> list[str]:
        raise RuntimeError("x")

    h.alerts = boom  # type: ignore[method-assign]
    h.tick(tue)
    h._last = None
    h.tick(tue + timedelta(hours=1))
    assert len([t for t, _, _ in sent if "check itself failed" in t]) == 1
    # a late job: one push, a reminder a day later, none in between
    sent.clear()
    j2 = Journal.sqlite()
    old = datetime(2026, 3, 1, 4, 0, tzinfo=ASX_TZ)
    set_state(j2, "restore-test-last", {"ok": True}, old)
    h2 = OpsHooks(j2, BOOK, lambda: sess, _collect(sent))
    wed = datetime(2026, 3, 11, 9, 0, tzinfo=ASX_TZ)
    h2.alerts(wed)
    h2.alerts(wed + timedelta(hours=5))
    h2.alerts(wed + timedelta(hours=25))
    rt = [t for t, _, _ in sent if "Weekly restore test" in t]
    assert len(rt) == 2 and rt[1].startswith("PAGE reminder")


def test_BF_D81_S4_missed_digest_is_sent_late() -> None:
    j = Journal.sqlite()
    sess = _sessions(date(2026, 3, 2), date(2026, 3, 20))
    idx = _book(j, sess[:10])
    sent: list[tuple[str, str, str]] = []
    h = OpsHooks(j, BOOK, lambda: sess, _collect(sent), index=lambda: idx)
    set_state(j, "digest-last", "2026-03-06", datetime(2026, 3, 6, 23, tzinfo=ASX_TZ))
    # the trader was down on Friday 13 March evening; it is back on Saturday morning
    assert h.weekly(datetime(2026, 3, 14, 8, 0, tzinfo=ASX_TZ))
    assert sent[0][2] == "/digest?w=2026-03-13" and "(sent late)" in sent[0][0]
    assert not h.weekly(datetime(2026, 3, 14, 9, 0, tzinfo=ASX_TZ))


# ---------------------------------------------------------------- S5 the info archive


def _archive_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "bw_info_archive", REPO / "deploy" / "info_archive.py"
    )
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _page(n: int) -> str:
    rows = "".join(
        f'<tr><td>Z{k:02d}</td><td> 23/11/2026<br> <span class="dates-time">9:{k % 60:02d} am'
        f'</span> </td><td class="pricesens">x</td><td><a href="/asx/v2/statistics/'
        f'displayAnnouncement.do?display=pdf&amp;idsId={k:08d}"> '
        + ("Change of Director&#39;s Interest Notice" if k == 1 else f"Made-up news {k}")
        + " <br> </a></td></tr>"
        for k in range(n)
    )
    return f"<html>published on 23 November 2026 <table>{rows}</table></html>"


def test_BF_D81_S5_archive_parse_guard_done_and_parts(tmp_path: Path, monkeypatch: Any) -> None:
    m = _archive_module()
    day, rows = m.parse_list(_page(60))
    assert day == "2026-11-23" and len(rows) == 60
    assert rows[1]["kept"] == 1 and rows[1]["headline"] == "Change of Director's Interest Notice"
    assert rows[1]["price_sensitive"] == 1 and rows[2]["kept"] == 0
    monkeypatch.setattr(m, "get", lambda url, hosts=m.ASX_HOSTS: _page(20).encode())
    with pytest.raises(ValueError, match="only 20 rows"):
        m.asx_notices(str(tmp_path))
    assert not (tmp_path / "asx_notices" / "2026-11-23" / "list.csv").exists()  # nothing kept

    def fake_get(url: str, hosts: tuple[str, ...] = m.ASX_HOSTS) -> bytes:
        if "prevBusDayAnns" in url:
            return _page(60).encode()
        if "displayAnnouncement" in url:
            return b'<input name="pdfURL" value="https://www.asx.com.au/asxpdf/x.pdf">'
        return b"%PDF-1.4 made up"

    def fake_run(cmd: list[str], **k: Any) -> Any:
        Path(cmd[-1]).write_text("Appendix 3Y made up")
        return None

    monkeypatch.setattr(m, "get", fake_get)
    monkeypatch.setattr(m.subprocess, "run", fake_run)
    res = m.asx_notices(str(tmp_path))
    d = tmp_path / "asx_notices" / "2026-11-23"
    assert res["pdfs"] == 1 and (d / "DONE").is_file()
    assert (d / "pdf" / "Z01_00000001.pdf").is_file() and (d / "pdf" / "Z01_00000001.txt").is_file()
    assert not list(d.rglob("*.part"))
    assert m.asx_notices(str(tmp_path)) == {"day": "2026-11-23", "note": "already stored"}


def test_BF_D81_S5_archive_hosts_are_pinned_and_asic_is_recent(tmp_path: Path,
                                                               monkeypatch: Any) -> None:  # fmt: skip
    import urllib.error

    m = _archive_module()
    assert m.host_ok("https://www.asx.com.au/x.pdf", m.ASX_HOSTS)
    assert m.host_ok("https://announcements.asx.com.au/x.pdf", m.ASX_HOSTS)
    for bad in ("http://www.asx.com.au/x", "https://asx.com.au.evil.example/x",
                "https://example.com/x.pdf", "https://download.asic.gov.au/x"):  # fmt: skip
        assert not m.host_ok(bad, m.ASX_HOSTS)
    with pytest.raises(ValueError, match="not an allowed host"):
        m.get("https://example.com/x")
    h = m._Pinned(m.ASX_HOSTS)
    with pytest.raises(urllib.error.HTTPError):
        h.redirect_request(None, None, 302, "Found", {}, "https://example.com/elsewhere")
    asked: list[str] = []
    idx = [{"date": "20261120", "version": "001"}, {"date": "20260101", "version": "001"},
           {"date": "20100104", "version": "001"}]  # fmt: skip

    def fake_get(url: str, hosts: tuple[str, ...] = m.ASIC_HOSTS) -> bytes:
        asked.append(url)
        assert hosts == m.ASIC_HOSTS
        if url.endswith(".json"):
            import json

            return json.dumps(idx).encode()
        return b"Product,Product Code\n"

    monkeypatch.setattr(m, "get", fake_get)
    res = m.asic_short(str(tmp_path), 400, date(2026, 11, 24))
    assert res["asic_new"] == 1 and len(asked) == 2  # the index and the one recent file
    assert not list((tmp_path / "asic_short").glob("*.part"))


def test_BF_D81_S5_archive_switch_has_one_source(tmp_path: Path) -> None:
    import shutil

    from trader.bfast_cli import main

    cfg = tmp_path / "config"
    shutil.copytree(REPO / "config", cfg)
    (cfg / "bfast.local.yaml").unlink(missing_ok=True)
    assert main(["archive-enabled", "--config", str(cfg / "bfast.yaml")]) == 1
    (cfg / "bfast.local.yaml").write_text("info_archive:\n    archive_enabled: true\n")
    assert main(["archive-enabled", "--config", str(cfg / "bfast.yaml")]) == 0
    sh = (REPO / "deploy" / "bigwins.sh").read_text()
    body = sh[sh.index("info_enabled() {") : sh.index("info_dir() {")]
    assert "trader-bf archive-enabled" in body and "sed" not in body


def test_BF_D81_S5_missed_days_wording_and_N4_not_yet_due(tmp_path: Path) -> None:
    days = _sessions(date(2026, 3, 2), date(2026, 3, 6))
    for d in days[:-1]:
        (tmp_path / "asx_notices" / str(d)).mkdir(parents=True)
        (tmp_path / "asx_notices" / str(d) / "DONE").write_text("{}")
    early = datetime(2026, 3, 7, 7, 0, tzinfo=ASX_TZ)  # before Friday's archive is due
    assert iv.status(tmp_path, days, early.date(), early).missed == []
    later = datetime(2026, 3, 7, 10, 0, tzinfo=ASX_TZ)
    assert iv.status(tmp_path, days, later.date(), later).missed == [date(2026, 3, 6)]
    j = Journal.sqlite()
    set_state(j, "info-archive-last", {"ok": True, "day": "2026-03-05"}, later)
    fr = {f.key: f for f in ov.freshness(j, BOOK, days, later, True)}
    assert fr["info"].status == "late" and "cannot be collected later" in fr["info"].detail


def test_BF_D81_hostile_headline_is_escaped(tmp_path: Path) -> None:
    from trader.app_ops import announcements

    d = tmp_path / "asx_notices" / "2026-03-02"
    d.mkdir(parents=True)
    with (d / "list.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["code", "date", "time", "price_sensitive", "headline", "ids_id", "kept"])
        w.writerow(["ZZQ", "02/03/2026", "<b>9am</b>", 0, '<script>alert("x")</script> Trading Halt',
                    "1<img>", 0])  # fmt: skip
    html = announcements(tmp_path, "ZZQ", date(2026, 3, 3))
    assert "<script>" not in html and "&lt;script&gt;" in html and "<b>9am" not in html


# ---------------------------------------------------------------- S6 / S7 the screens


@pytest.fixture(scope="module")
def demo(tmp_path_factory: pytest.TempPathFactory) -> Any:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo
    from trader.journal import read_only_engine

    dm = build_demo(tmp_path_factory.mktemp("d") / "j.sqlite", days=45, random_twins=5)
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{dm.journal_path}"))
    src = Sources(j, index=dm.index, sessions=lambda: dm.sessions, today=lambda: dm.last_day,
                  clock=lambda: dm.now, demo=True, prices=dm.prices,
                  forecast_dir=REPO / "config", scorecard=dm.scorecard, info_dir=dm.info_dir,
                  info_enabled=True)  # fmt: skip
    return Dashboard(src)


def test_BF_D81_S6_home_has_one_comparison_after_costs(demo: Any) -> None:
    st, _, b = demo.respond("GET", "/", {})
    html = b.decode()
    assert "Account value · before running costs" in html
    assert "Ahead of the index this month" not in html and "Behind the index this month" not in html
    assert "the scoreboard above is the comparison after costs" in html


def test_BF_D81_S7_health_shows_a_missing_timer() -> None:
    from trader import app_ops
    from trader.app_pages import Extras
    from trader.server_status import clean_status

    st = clean_status({"timers": {"worker": True, "info": False, "evil": False}})
    assert st["timers"] == {"worker": True, "info": False}
    x = Extras(host=(st, datetime(2026, 3, 2, tzinfo=ASX_TZ)))

    class V:
        now = datetime(2026, 3, 2, 10, tzinfo=ASX_TZ)
        disk_free = (1024**3, 10 * 1024**3)
        store_day = None
        store_refreshed_at = None
        notes: tuple[str, ...] = ()
        demo = False
        book = BOOK
        live = False

    html = app_ops.health(V(), x, app_ops.Ops(), "1")
    assert "Timer not installed: announcements archive" in html
    assert "under 2 GB" in html
    sh = (REPO / "deploy" / "bigwins.sh").read_text()
    assert "ensure_timers" in sh[sh.index("cmd_worker() {") : sh.index("cmd_worker() {") + 2000]


# ---------------------------------------------------------------- N1 edited costs


def test_BF_D81_N1_edited_costs_apply_from_their_day() -> None:
    j = Journal.sqlite()
    set_state(j, "running-costs", {"history": [
        {"server": "365", "data": "0", "other": "0", "from": "2026-03-11"}]},
        datetime(2026, 3, 11, tzinfo=ASX_TZ))  # fmt: skip
    fc = ov.fixed_costs(j, None, Decimal(730))
    assert fc.source == "app" and fc.per_year == Decimal(365) and fc.since == date(2026, 3, 11)
    got = fc.between(date(2026, 3, 1), date(2026, 3, 20))
    # 10 days at $730 a year (the server total before the edit), 10 days at $365
    assert sum(got.values()) == Decimal("30.00")
    sb = ov.scoreboard([(date(2026, 3, 1), Decimal(10000)), (date(2026, 3, 20), Decimal(10000))],
                       [], Decimal(10000), fc)  # fmt: skip
    assert sb is not None and sb.fixed == Decimal("30.00")


def test_BF_D81_N1_absurd_amounts_are_refused() -> None:
    from tests.test_bf_app_actions import _post, _session, _setup

    j, _, ctl, _, _ = _setup()
    sess = _session(ctl)
    for form in ({"server": "0.01"}, {"server": "20"}, {"server": "-5"}, {"server": "999999"}):
        _, body = _post(ctl, form, session=sess, path="/act/costs")
        assert "Not saved" in body, form
    _, body = _post(
        ctl, {"server": "0", "data": "0", "other": "0"}, session=sess, path="/act/costs"
    )
    assert "running costs saved" in body  # all zero = back to the server's total
    fc = ov.fixed_costs(j, None, Decimal(600))
    assert fc.source == "total" and fc.per_year == Decimal(600)


def test_BF_D81_N7_digest_wording_and_not_yet_status() -> None:
    j = Journal.sqlite()
    dg = ov.digest(j, BOOK, date(2026, 3, 13), None, None, None, [], store_days=[date(2026, 3, 9)])
    assert "1 trading day downloaded" in dg.text() and "(s)" not in dg.text()
    fr = {f.key: f for f in ov.freshness(j, BOOK, [], datetime(2026, 3, 2, tzinfo=ASX_TZ))}
    assert fr["prices"].status == "new" and not fr["prices"].bad


def test_BF_D81_short_file_gzip_roundtrip(tmp_path: Path) -> None:
    sd = tmp_path / "asic_short"
    sd.mkdir()
    with gzip.open(sd / "RR20260302-001-SSDailyAggShortPos.csv.gz", "wt") as f:
        f.write("Product,Product Code,Reported Short Positions,Total Product in Issue,"
                "% of Total Product in Issue Reported as Short Positions\nMADE UP,ZZQ,1,100,1.0\n")  # fmt: skip
    sp = iv.short_position(tmp_path, "ZZQ")
    assert sp is not None and sp.pct == pytest.approx(1.0)
