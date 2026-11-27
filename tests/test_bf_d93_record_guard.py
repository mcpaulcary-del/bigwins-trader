"""BF-D93 (owner decision 27 Nov 2026, "Yes use the newer collector"): the research
collector runs on the server only behind the older server copy's safety checks, added as
a guard AROUND the unedited code; and a record job can never starve the trader of memory.
Fixture data only: the list page, notices and PDFs are made up; nothing touches a network."""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from record.tools import jobs, net_guard, paths, runner, steps
from tests import record_support as S

REPO = Path(__file__).resolve().parents[1]


class _Resp:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def read(self, n: int = -1) -> bytes:
        return self.data if n < 0 else self.data[:n]

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *a: object) -> None:
        return None


class _Opener:
    def __init__(self, pages: dict[str, bytes], seen: list[str]) -> None:
        self.pages, self.seen = pages, seen

    def open(self, req: Any, timeout: float = 0) -> _Resp:
        url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        self.seen.append(url)
        return _Resp(self.pages[url])


def test_BF_D93_guard_allows_only_the_exception_hosts_over_https() -> None:
    seen: list[str] = []
    pages = {"https://www.asx.com.au/a": b"ok", "https://announcements.asx.com.au/x.pdf": b"%PDF",
             "https://download.asic.gov.au/short-selling/RR.csv": b"csv"}  # fmt: skip
    groups: list[tuple[str, ...]] = []

    def factory(hosts: tuple[str, ...]) -> _Opener:
        groups.append(hosts)
        return _Opener(pages, seen)

    urlopen = net_guard.guarded(factory)
    for url, body in pages.items():
        with urlopen(urllib.request.Request(url, headers={"User-Agent": "x"}), timeout=5) as r:
            assert r.read() == body
    assert groups == [("asx.com.au",), ("asx.com.au",), ("download.asic.gov.au",)]
    refused = ["http://www.asx.com.au/a", "file:///etc/passwd", "ftp://www.asx.com.au/x",
               "https://asx.com.au.evil.example/a", "https://evil.example/asx.com.au",
               "https://example.com/x.pdf", "https://asic.gov.au/x", "not a url"]  # fmt: skip
    n = len(seen)
    for url in refused:
        with pytest.raises(net_guard.RefusedError):
            urlopen(url)
    assert len(seen) == n  # refused BEFORE any connection
    with pytest.raises(net_guard.RefusedError):  # the collector only reads: no request body, ever
        urlopen("https://www.asx.com.au/a", data=b"x")


def test_BF_D93_guard_pins_redirects_and_caps_size(monkeypatch: pytest.MonkeyPatch) -> None:
    h = net_guard.Pinned(net_guard.ASX_HOSTS)
    req = urllib.request.Request("https://www.asx.com.au/a")
    ok = h.redirect_request(req, None, 302, "Found", {}, "https://announcements.asx.com.au/b.pdf")
    assert ok is not None and ok.full_url == "https://announcements.asx.com.au/b.pdf"
    for bad in ("https://cdn.example.com/b.pdf", "http://www.asx.com.au/b.pdf",
                "https://download.asic.gov.au/x", "file:///etc/passwd"):  # fmt: skip
        with pytest.raises(urllib.error.HTTPError):
            h.redirect_request(req, None, 302, "Found", {}, bad)
    monkeypatch.setattr(net_guard, "MAX_BYTES", 10)
    urlopen = net_guard.guarded(lambda hosts: _Opener({"https://www.asx.com.au/big": b"x" * 11,
                                                       "https://www.asx.com.au/fits": b"x" * 10}, []))  # fmt: skip
    assert urlopen("https://www.asx.com.au/fits").read() == b"x" * 10
    with pytest.raises(net_guard.RefusedError, match="refused"):
        urlopen("https://www.asx.com.au/big")


def test_BF_D93_guard_cleans_the_asic_index() -> None:
    good = [{"date": "20261120", "version": "001"}, {"date": 20261119, "version": 2}]
    raw = json.dumps([good[0], {"date": "../../etc/x", "version": "001"}, {"date": "20261118", "version": "1/../x"},
                      "junk", {"version": "001"}, good[1]]).encode()  # fmt: skip
    assert (
        json.loads(net_guard.clean_index(raw)) == good
    )  # the original order, well-formed entries only
    for bad in (b"<html>", b"{}", b"[]", json.dumps([{"date": "x"}]).encode()):
        with pytest.raises(net_guard.RefusedError):
            net_guard.clean_index(bad)
    urlopen = net_guard.guarded(lambda hosts: _Opener({net_guard.ASIC_INDEX: raw}, []))
    assert json.loads(urlopen(net_guard.ASIC_INDEX).read()) == good


HARNESS = r"""
import importlib.util, json, sys, time, urllib.request
sys.path.insert(0, sys.argv[1])
from record.tools import net_guard
out, pages = sys.argv[2], json.loads(open(sys.argv[3]).read())
seen = []
class R:
    def __init__(s, b): s.b = b
    def read(s, n=-1): return s.b if n < 0 else s.b[:n]
    def __enter__(s): return s
    def __exit__(s, *a): pass
class O:
    def open(s, req, timeout=0):
        seen.append(req.full_url); return R(pages[req.full_url].encode("latin-1"))
net_guard.install(lambda hosts: O())
time.sleep = lambda s: None                      # the test does not wait out the pacing
spec = importlib.util.spec_from_file_location("ia", sys.argv[1] + "/record/code/info_archive.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)   # the UNEDITED collector
m.OUT = out; m.BANDC = out + "/bandC.json"; m.HOLD_CSV = out + "/none.csv"; m.STATE_DIR = out + "/none"
m.GAP = 0.0
m.inside_asx_hours = lambda now=None: False
print(m.asx_notices()); print(m.asic_short(5)); print(json.dumps(seen))
"""


def test_BF_D93_the_unedited_collector_runs_behind_the_guard(tmp_path: Path) -> None:
    """The research collector itself (record/code/info_archive.py, byte-identical) with
    the guard installed as launch.py does: allowed fetches work and store the day; a PDF
    address on another host, a file: address and an http: address are refused and stored
    nowhere; a malformed ASIC entry cannot become a file name."""
    base = "https://www.asx.com.au"
    rows: list[str] = []
    pages: dict[str, str] = {}

    def row(code: str, ids: str, head: str, ps: bool = False) -> str:
        return (f'<tr><td>{code}</td><td> 14/12/2026<br> <span class="dates-time">9:0{len(rows) % 10} am</span> </td>'
                f'<td>{"<img class=pricesens>" if ps else ""}</td>'
                f'<td><a href="/asx/v2/statistics/displayAnnouncement.do?display=pdf&amp;idsId={ids}">{head}<br></a></td></tr>')  # fmt: skip

    for i in range(56):
        rows.append(row(f"Z{i:02d}", f"09{i:06d}", "Made-up update"))
    plan = {"AAA": "https://announcements.asx.com.au/asxpdf/aaa.pdf",  # allowed
            "BBB": "https://cdn.evil.example/bbb.pdf",  # another host
            "CCC": "file:///etc/passwd", "DDD": "http://www.asx.com.au/ddd.pdf"}  # fmt: skip
    for n, (code, pdf) in enumerate(plan.items()):
        ids = f"0300000{n}"
        rows.append(row(code, ids, "Change of Director's Interest Notice"))
        pages[f"{base}/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId={ids}"] = (
            f'<input name="pdfURL" value="{pdf}">')  # fmt: skip
    pages[plan["AAA"]] = "%PDF-1.4 made-up notice\n%%EOF\n"
    pages[f"{base}/asx/v2/statistics/prevBusDayAnns.do"] = (
        "<html>Announcements published on 14 December 2026<table>" + "".join(rows) + "</table></html>")  # fmt: skip
    pages[net_guard.ASIC_INDEX] = json.dumps([
        {"date": "20261210", "version": "001"}, {"date": "../../../x", "version": "001"}])  # fmt: skip
    pages["https://download.asic.gov.au/short-selling/RR20261210-001-SSDailyAggShortPos.csv"] = (
        "Product,Code\r\nMADE UP,AAA\r\n"
    )
    out = tmp_path / "data"
    out.mkdir()
    (out / "bandC.json").write_text(json.dumps({"codes": [], "asof": "2026-12-01"}))
    (tmp_path / "pages.json").write_text(json.dumps(pages))
    (tmp_path / "h.py").write_text(HARNESS)
    stub = tmp_path / "bin"  # the collector calls pdftotext: a stand-in, so no tool is needed here
    stub.mkdir()
    (stub / "pdftotext").write_text(
        '#!/bin/sh\nfor a; do last=$a; done\necho "made-up text" > "$last"\n'
    )
    (stub / "pdftotext").chmod(0o755)
    env = {**os.environ, "PATH": f"{stub}:{os.environ['PATH']}"}
    r = subprocess.run([sys.executable, "-W", "ignore", str(tmp_path / "h.py"), str(REPO), str(out),
                        str(tmp_path / "pages.json")], capture_output=True, text=True, check=False, env=env)  # fmt: skip
    assert r.returncode == 0, r.stdout + r.stderr
    assert "asx 2026-12-14: 60 announcements, 1 notices stored, 3 failed" in r.stdout
    seen = json.loads(r.stdout.strip().splitlines()[-1])
    assert plan["AAA"] in seen
    assert not any(
        u.startswith(("https://cdn.evil", "file:", "http:")) for u in seen
    )  # never requested
    day = out / "asx_notices" / "2026-12-14"
    assert sorted(p.name for p in (day / "pdf").glob("*.pdf")) == ["AAA_03000000.pdf"]
    assert (day / "DONE").is_file() and (day / "DONE_PS").is_file()
    assert json.loads((day / "DONE").read_text())["failed"] == 3
    assert (
        "asic short: 1 new files, 1 stored of 1 listed" in r.stdout
    )  # the bad entry never reached it
    assert [p.name for p in (out / "asic_short").iterdir()] == [
        "RR20261210-001-SSDailyAggShortPos.csv.gz"
    ]
    # the sanity step after the run accepts this day
    tree = tmp_path / "tree"
    (tree / paths.REL_DATA).mkdir(parents=True)
    (out / "asx_notices").rename(tree / paths.REL_DATA / "asx_notices")
    assert steps.archive_check(tree, today=dt.date(2026, 12, 15)) == 0


def test_BF_D93_archive_check_refuses_a_short_or_odd_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    d = S.archive_day(tmp_path, "2026-12-14")
    head = ",".join(steps.LIST_HEAD)
    body = "".join(f"Z{i:02d},14/12/2026,9:00 am,0,Made-up,{i},0\n" for i in range(60))
    (d / "list.csv").write_text(head + "\n" + body)
    (d / "pdf" / "AAA_0001.pdf").write_bytes(b"%PDF-1.4 made-up\n%%EOF\n")
    today = dt.date(2026, 12, 15)
    assert steps.archive_check(tmp_path, today=today) == 0
    (d / "list.csv").write_text(head + "\n" + body[:200])  # the page format changed: a short list
    assert steps.archive_check(tmp_path, today=today) == 1
    (d / "list.csv").write_text("a,b\n1,2\n")
    assert steps.archive_check(tmp_path, today=today) == 1
    (d / "list.csv").write_text(head + "\n" + body)
    assert steps.archive_check(tmp_path, today=dt.date(2026, 12, 1)) == 1  # a day in the future
    (d / "pdf" / "BBB_0002.pdf").write_bytes(b"<html>not a pdf</html>")
    assert steps.archive_check(tmp_path, today=today) == 1
    (d / "pdf" / "BBB_0002.pdf").write_bytes(b"%PDF-1.4 cut off in the mid")
    capsys.readouterr()
    assert (
        steps.archive_check(tmp_path, today=today) == 0
    )  # reported, not a failure, nothing deleted
    assert "WARNING 1 PDF(s) without an end marker" in capsys.readouterr().out
    assert (d / "pdf" / "BBB_0002.pdf").is_file()
    assert steps.archive_check(tmp_path / "empty", today=today) == 0
    arch = jobs.JOBS["archive"]
    assert [s.name for s in arch.steps] == ["info_archive.py", "archive_check"] and arch.steps[
        1
    ].must


def test_BF_D93_launcher_installs_the_guard_for_every_script(tmp_path: Path) -> None:
    root = tmp_path / "t"
    S.make_tree(root, writer="server")
    code = root / paths.REL_CODE
    code.mkdir(parents=True)
    (code / "fwd_ledger.py").write_text((REPO / "record/code/fwd_ledger.py").read_text())
    (code / "probe.py").write_text(
        "import urllib.request\n"
        "for u in ('https://example.com/x', 'file:///etc/passwd', 'http://www.asx.com.au/'):\n"
        "    try:\n        urllib.request.urlopen(urllib.request.Request(u), timeout=1)\n"
        "        print('OPENED', u)\n    except Exception as e:\n        print(type(e).__name__, u)\n")  # fmt: skip
    env = {"PATH": "/usr/bin:/bin", "BW_ROOT": str(root), "BW_RECORD_HOST": "server",
           "BW_EODHD_TOKEN_FILE": str(tmp_path / "none")}  # fmt: skip
    r = subprocess.run([sys.executable, "-I", str(REPO / "record/tools/launch.py"), "probe.py"], env=env,
                       capture_output=True, text=True, check=False)  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert r.stdout.count("RefusedError") == 3 and "OPENED" not in r.stdout
    # the collector's own code is still the registered bytes
    assert runner.check_code(REPO / "nonexistent") != []  # (sanity: a wrong root is noticed)
    assert "info_archive.py" in (REPO / "record/MANIFEST.sha256").read_text()


def test_BF_D93_record_jobs_cannot_starve_the_trader(tmp_path: Path) -> None:
    """A 3.9 GB server: every record job has a hard RAM cap well under what is free, swap
    above it, is the first to be killed under pressure, and reports what it used."""
    assert max(j.memory_mb for j in jobs.JOBS.values()) == 1500
    assert all(
        jobs.JOBS[k].memory_mb <= 800 for k in ("intraday", "archive", "collect", "newsc-record")
    )
    cg = tmp_path / "cg"
    cg.mkdir()
    (cg / "memory.peak").write_text("1258291200\n")
    (cg / "memory.max").write_text("1572864000\n")
    (cg / "memory.swap.peak").write_text("0\n")
    (cg / "memory.events").write_text("low 0\nhigh 0\nmax 12\noom 1\noom_kill 1\n")
    assert runner.cgroup_memory(cg) == {"cgroup_peak_mb": 1200.0, "mem_limit_mb": 1500.0,
                                        "swap_peak_mb": 0.0, "oom_kills": 1}  # fmt: skip
    (cg / "memory.max").write_text("max\n")  # no limit set: reported as absent, not as a number
    assert "mem_limit_mb" not in runner.cgroup_memory(cg)
    assert runner.cgroup_memory(tmp_path / "none") == {}
    sh = (REPO / "deploy/record.sh").read_text()
    assert '--memory "${mem}m" --memory-swap "$((mem * 2))m"' in sh and "--oom-score-adj 500" in sh
    from tests.test_bf_d93_record_server import Server

    (tmp_path / "srv").mkdir()
    s = Server(tmp_path / "srv")
    assert s.run("rec_mem 1500").stdout.strip() == "1500"
    for text, want in (
        ("1200", "1200"),
        ("99999", "1500"),
        ("100", "1500"),
        ("abc", "1500"),
        ("2000", "2000"),
    ):
        (tmp_path / "srv" / "etc" / "record_memory_mb").write_text(text)
        assert s.run("rec_mem 1500").stdout.strip() == want
    (tmp_path / "srv" / "state" / "record").mkdir(parents=True, exist_ok=True)
    (tmp_path / "srv" / "state" / "record" / "daily.out").write_text(
        'log line\n{"ok": true, "peak_mb": 900.5, "cgroup_peak_mb": 1200.0, "swap_peak_mb": 0.0, "oom_kills": 0, "seconds": 400}\n'
    )
    out = s.run("rec_memory").stdout
    assert (
        "daily" in out and "largest process 900.5 MB" in out and "container peak 1200.0 MB" in out
    )
    # the app keeps and shows it
    from datetime import datetime

    from trader import record_view as rv
    from trader.constants import ASX_TZ
    from trader.journal import Journal

    j = Journal.sqlite()
    now = datetime(2026, 12, 21, 21, 0, tzinfo=ASX_TZ)
    ev = rv.record_event(j, {"kind": "job", "job": "daily", "ok": True, "mode": "writer", "peak_mb": 900.5,
                             "cgroup_peak_mb": 1200.0, "mem_limit_mb": 1500.0, "oom_kills": 0}, now)  # fmt: skip
    assert ev["cgroup_peak_mb"] == 1200.0 and ev["mem_limit_mb"] == 1500.0
    card = rv.health_card(j, {"record": {"mode": "writer"}}, now)
    assert "1200.0 MB</b> (daily) of a 1500.0 MB cap" in card and "killed for memory" not in card
    rv.record_event(j, {"kind": "job", "job": "multi", "ok": False, "mode": "writer", "cgroup_peak_mb": 1499.0,
                        "mem_limit_mb": 1500.0, "oom_kills": 2}, now)  # fmt: skip
    assert "killed for memory: 2" in rv.health_card(j, {"record": {"mode": "writer"}}, now)
