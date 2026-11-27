"""BF-D93: the paper record on the server, the tools (record/tools). Fixture data only
(made-up trees; no vendor data, no network): the ledger library against the research
helper, the writer fence and every fork attempt, the relay puller and the research
request queue, the sync bundle, the parallel-run comparison and its pass rule, the
EODHD token shim, the job table, the disk and PDF-backup rules, and the code manifest."""

from __future__ import annotations

import datetime as dt
import gzip
import io
import json
import runpy
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import pytest

from record.tools import (
    eodhd_shim,
    fence,
    hashing,
    jobs,
    ops,
    paths,
    record_compare,
    relay,
    runner,
    steps,
    sync_bundle,
)
from record.tools import ledgerlib as L
from tests import record_support as S

REPO = Path(__file__).resolve().parents[1]
BWREC = REPO / "record/tools/bwrec.py"


def bwrec(root: Path, *args: str, me: str = "server", env: dict[str, str] | None = None
          ) -> subprocess.CompletedProcess[str]:  # fmt: skip
    e = {"PATH": "/usr/bin:/bin", "BW_ROOT": str(root), "BW_RECORD_HOST": me, **(env or {})}
    return subprocess.run([sys.executable, "-I", str(BWREC), *args], env=e, capture_output=True,
                          text=True, check=False)  # fmt: skip


# ---------------------------------------------------------------- the code copy
def test_record_code_matches_its_manifest_and_frozen_files_are_unchanged() -> None:
    """E5/E6: record/code is a byte-identical copy; the manifest the runner checks is current."""
    assert bwrec(REPO, "code-manifest", "--check").stdout.strip() == "ok"
    want = hashing.read_sha256sums((REPO / "record/MANIFEST.sha256").read_text())
    for frozen in (
        "code/blind3_frozen/strat.py",
        "code/multi_frozen/sim6.py",
        "code/multi_frozen/dlf.py",
    ):
        assert frozen in want
        # the hash-frozen files still name the cloud path: it is mounted, never edited
        assert paths.CLOUD_ROOT in (REPO / "record" / frozen).read_text()
    assert len(want) >= 100 and not any("__pycache__" in k for k in want)


def test_runner_refuses_changed_code_and_a_different_environment(tmp_path: Path) -> None:
    root = tmp_path / "t"
    shutil.copytree(REPO / "record/code", root / paths.REL_CODE)
    shutil.copytree(REPO / "record/data_foundation_code", root / paths.REL_DF_CODE)
    assert runner.check_code(root) == []
    (root / paths.REL_CODE / "paper_lib.py").write_text("# edited\n")
    (root / paths.REL_CODE / "extra.py").write_text("x = 1\n")
    bad = runner.check_code(root)
    assert "changed: code/paper_lib.py" in bad and "not in the manifest: code/extra.py" in bad
    want = json.loads((REPO / "record/ENVIRONMENT.json").read_text())["versions"]
    assert runner.check_env(want) == []
    assert runner.check_env({**want, "numpy": "0.0.1"}) == [
        f"numpy: 0.0.1 here, {want['numpy']} on the cloud"
    ]
    S.make_tree(root, writer="server")
    res = runner.run_job("daily", {}, root=root)  # this test environment is not the cloud's
    assert not res["ok"] and res["error"].startswith("refused:") and res["steps"] == []


# ---------------------------------------------------------------- ledger library
def test_ledgerlib_writes_the_same_bytes_as_the_research_helper(tmp_path: Path) -> None:
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    rows: list[dict[str, Any]] = [{"kind": "daily", "asof": "2026-12-14", "x": [1, 2], "event": "é", "recorded_utc": "2026-12-14T00:00:00Z"},
            {"kind": "trials", "asof": "2026-12-15", "n_trials": 7, "recorded_utc": "2026-12-15T00:00:00Z"}]  # fmt: skip
    # the research helper itself (record/code/fwd_ledger.py), in its own process
    prog = ("import json, sys; sys.path.insert(0, sys.argv[1]); import fwd_ledger as L; L.LED = sys.argv[2]\n"
            "for f in json.loads(sys.argv[3]): L.append(**f)\nprint(L.verify())")  # fmt: skip
    r = subprocess.run([sys.executable, "-W", "ignore", "-c", prog, str(REPO / "record/code"), str(a),
                        json.dumps(rows)], capture_output=True, text=True, check=True)  # fmt: skip
    for f in rows:
        L.append(b, f)
    assert a.read_bytes() == b.read_bytes()
    assert r.stdout.strip() == L.head(b)


def test_ledger_verify_catches_a_changed_or_dropped_entry(tmp_path: Path) -> None:
    rec = S.make_tree(tmp_path, entries=4)
    es = L.read(rec / "LEDGER.jsonl")
    assert L.verify(es) == es[-1]["entry_sha256"]
    with pytest.raises(L.ChainError):
        L.verify([es[0], es[2], es[3]])
    es[1]["n_trials"] = 99
    with pytest.raises(L.ChainError):
        L.verify(es)
    assert L.is_prefix(L.read(rec / "LEDGER.jsonl")[:2], L.read(rec / "LEDGER.jsonl"))


# ---------------------------------------------------------------- fence and handover
def test_fence_default_deny() -> None:
    f = fence.Fence(2, "server", "writer")
    assert fence.decide(f, "server").ok and not fence.decide(f, "cloud").ok
    assert not fence.decide(None, "server").ok  # no fence file: nobody appends
    assert not fence.decide(f, "").ok and not fence.decide(f, "laptop").ok
    assert fence.decide(fence.Fence(2, "cloud", "standby"), "cloud").standby
    stale = fence.decide(f, "server", relay=fence.Fence(3, "cloud", "writer"))
    assert not stale.ok and "newer writer" in stale.reason  # a takeover happened elsewhere
    assert fence.decide(f, "server", relay=fence.Fence(2, "server", "writer")).ok
    bad: Any
    for bad in ({"epoch": 0, "writer": "server"}, {"epoch": 1, "writer": "x"}, {"epoch": True, "writer": "cloud"},
                {"epoch": 1, "writer": "cloud", "role": "boss"}, {"epoch": 1, "writer": "cloud", "head": "zz"}, []):  # fmt: skip
        with pytest.raises(fence.FenceError):
            fence.parse(bad)


def _handover_pair(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    cloud, server = tmp_path / "cloud", tmp_path / "server"
    rec_c = S.make_tree(cloud, writer="cloud")
    h = fence.handover(rec_c, "cloud", "2026-12-19", {"tree_manifest_sha256": "ab" * 32})
    shutil.copytree(cloud, server)  # the commit + bundle the server fetches
    return rec_c, paths.record_dir(server), h


def test_handover_then_acceptance_is_one_chain(tmp_path: Path) -> None:
    rec_c, rec_s, h = _handover_pair(tmp_path)
    assert h["kind"] == "handover" and h["epoch"] == 2 and h["to"] == "server"
    assert not fence.decide_dir(rec_c, "cloud").ok  # the cloud's next append is refused
    assert bwrec(tmp_path / "server", "accept", "--check").stdout.strip() == h["entry_sha256"][:12]
    acc = fence.accept(rec_s, "server", "2026-12-19")
    assert (
        acc["prev_entry_sha256"] == h["entry_sha256"] and acc["accepted_head"] == h["entry_sha256"]
    )
    assert acc["tree_manifest_sha256"] == "ab" * 32
    f = fence.load(rec_s)
    assert f is not None and (f.writer, f.role, f.epoch) == ("server", "writer", 2)
    assert L.is_prefix(L.read(rec_c / "LEDGER.jsonl"), L.read(rec_s / "LEDGER.jsonl"))


def test_fork_attempts_are_refused(tmp_path: Path) -> None:
    rec_c, rec_s, _h = _handover_pair(tmp_path)
    # 1. two appenders: after the handover the old writer cannot hand over or accept again
    with pytest.raises(fence.FenceError):
        fence.handover(rec_c, "cloud", "2026-12-19")
    with pytest.raises(fence.FenceError):
        fence.accept(rec_c, "cloud", "2026-12-19")
    fence.accept(rec_s, "server", "2026-12-19")
    # 2. a replayed handover: accepting the same tree twice
    with pytest.raises(fence.FenceError, match="not a handover"):
        fence.accept(rec_s, "server", "2026-12-19")
    # 3. a shadow ledger offered as the canonical record
    shadow = S.make_tree(tmp_path / "shadow", writer="server", role="shadow")
    with pytest.raises(fence.FenceError):
        fence.check_incoming(shadow, "server")
    # 4. a handover whose fence was tampered with (points at another head / epoch)
    rec_x = S.make_tree(tmp_path / "x", writer="cloud")
    fence.handover(rec_x, "cloud", "2026-12-19")
    fence.save(rec_x, fence.Fence(5, "server", "writer", "0" * 64))
    with pytest.raises(fence.FenceError):
        fence.check_incoming(rec_x, "server")
    # 5. a ledger with a standby tail is never a canonical record
    rec_y = S.make_tree(tmp_path / "y", writer="cloud")
    L.append(rec_y / "LEDGER.jsonl", {"kind": "daily", "asof": "2026-12-21", "standby": True})
    with pytest.raises(fence.FenceError):
        fence.handover(rec_y, "server", "2026-12-21")
    with pytest.raises(fence.FenceError, match="standby"):
        fence.takeover(rec_y, "server", "2026-12-21", "test")


def test_cancel_takeover_and_standby(tmp_path: Path) -> None:
    rec_c, rec_s, h = _handover_pair(tmp_path)
    # the cut-over stops half-way: the cloud takes the record back, one more entry
    c = fence.cancel(rec_c, "cloud", "2026-12-19")
    assert (
        c["kind"] == "handover-cancelled"
        and c["epoch"] == 3
        and fence.decide_dir(rec_c, "cloud").ok
    )
    with pytest.raises(fence.FenceError):
        fence.cancel(rec_c, "cloud", "2026-12-19")
    # the server's copy of the cancelled handover can no longer win: the relay epoch is higher
    assert not fence.decide(fence.load(rec_s), "server", relay=fence.load(rec_c)).ok
    # emergency: the server accepted, then died; the cloud takes over from the shipped ledger
    rec_c2, rec_s2, _ = _handover_pair(tmp_path / "two")
    acc = fence.accept(rec_s2, "server", "2026-12-19")
    shipped = tmp_path / "shipped"
    shutil.copytree(rec_s2, shipped)
    t = fence.takeover(shipped, "cloud", "2026-12-23", "server unreachable, powered off")
    assert (
        t["kind"] == "writer-takeover"
        and t["epoch"] == 3
        and t["built_on_head"] == acc["entry_sha256"]
    )
    assert not fence.decide(fence.load(rec_s2), "server", relay=fence.load(shipped)).ok
    # standby: only after the acceptance was read back; its appends are marked
    sb = fence.to_standby(rec_c2, "cloud", acc["entry_sha256"])
    assert sb.role == "standby" and fence.decide(sb, "cloud").standby
    with pytest.raises(fence.FenceError):
        fence.to_standby(rec_s2, "server", acc["entry_sha256"])
    assert h["epoch"] == 2


def test_launch_wraps_the_research_append_with_the_fence(tmp_path: Path) -> None:
    """E3 without editing fwd_ledger.py: a script under the launcher appends only when the
    fence allows it; a standby copy marks its entries; the format is the research one."""
    root = tmp_path / "t"
    rec = S.make_tree(root, writer="server")
    code = root / paths.REL_CODE
    code.mkdir(parents=True)
    shutil.copy(REPO / "record/code/fwd_ledger.py", code / "fwd_ledger.py")
    (code / "job.py").write_text(
        "import sys, fwd_ledger as L\n"
        f"L.LED = {str(rec / 'LEDGER.jsonl')!r}\n"
        "e = L.append(kind='daily', asof=sys.argv[1], event='made-up')\nprint('seq', e['seq'])\n")  # fmt: skip
    launch = str(REPO / "record/tools/launch.py")

    def run(me: str, *extra: str) -> subprocess.CompletedProcess[str]:
        env = {"PATH": "/usr/bin:/bin", "BW_ROOT": str(root), "BW_RECORD_HOST": me,
               "BW_EODHD_TOKEN_FILE": str(tmp_path / "none")}  # fmt: skip
        return subprocess.run([sys.executable, "-I", launch, *extra, "job.py", "2026-12-14"], env=env,
                              capture_output=True, text=True, check=False)  # fmt: skip

    ok = run("server")
    assert ok.returncode == 0 and "seq 4" in ok.stdout
    assert run("cloud").returncode == 75 and len(L.read(rec / "LEDGER.jsonl")) == 4
    (rec / fence.FENCE).unlink()
    assert run("server").returncode == 75  # no fence: refuse
    fence.save(rec, fence.Fence(2, "server", "standby", "a" * 64))
    assert run("server").returncode == 0
    last = L.read(rec / "LEDGER.jsonl")[-1]
    assert last["standby"] is True and L.head(rec / "LEDGER.jsonl") == last["entry_sha256"]
    assert run("server", "../../../etc/passwd").returncode == 2  # only scripts of the code folder


# ---------------------------------------------------------------- EODHD token shim
class _Req:
    def __init__(self, url: str, auth: str = "Bearer proxy-injected") -> None:
        self.url, self.headers = url, {"Authorization": auth}


class _Resp:
    def __init__(self, req: _Req) -> None:
        self.url, self.request, self.status_code = req.url, req, 200
        self.history: list[Any] = []


def _session(fail: bool = False) -> tuple[type, list[tuple[str, dict[str, str]]]]:
    wire: list[tuple[str, dict[str, str]]] = []

    class Session:
        def send(self, request: _Req, **kw: Any) -> _Resp:
            wire.append((request.url, dict(request.headers)))
            if fail:
                raise ConnectionError(
                    f"Max retries exceeded with url: {request.url} {request.headers}"
                )
            return _Resp(request)

    return Session, wire


@pytest.mark.parametrize("mode", ["header", "query"])
def test_eodhd_token_reaches_eodhd_only_and_never_comes_back(mode: str, tmp_path: Path) -> None:
    """E2: no log line, manifest row or exception text can contain the token."""
    token = "tok3n-Made.Up_123456"
    tf = tmp_path / "eodhd_api_token"
    tf.write_text(token + "\n")
    assert eodhd_shim.read_token(tf) == token
    cls, wire = _session()
    assert eodhd_shim.install(cls, token, mode) and not eodhd_shim.install(cls, token, mode)
    r = cls().send(_Req("https://eodhd.com/api/eod/AAA.AU?fmt=json&from=2026-01-01"))
    sent_url, sent_headers = wire[-1]
    assert token in (sent_headers.get("Authorization", "") if mode == "header" else sent_url)
    # what the research code sees afterwards has the placeholder again
    assert token not in r.url + r.request.url + str(r.request.headers)
    assert r.request.url == "https://eodhd.com/api/eod/AAA.AU?fmt=json&from=2026-01-01"
    assert (
        r.request.headers.get("Authorization", "Bearer proxy-injected") == "Bearer proxy-injected"
    )
    # other hosts, http, and requests without the placeholder are left alone
    for url, auth in (("https://example.com/api?x=1", "Bearer proxy-injected"),
                      ("http://eodhd.com/api/eod/AAA.AU", "Bearer proxy-injected"),
                      ("https://eodhd.com.evil.example/api", "Bearer proxy-injected"),
                      ("https://eodhd.com/api/eod/AAA.AU", "Bearer something-else")):  # fmt: skip
        cls().send(_Req(url, auth))
        assert token not in wire[-1][0] + str(wire[-1][1])
    bad, wire2 = _session(fail=True)
    eodhd_shim.install(bad, token, mode)
    with pytest.raises(Exception) as ei:
        bad().send(_Req("https://eodhd.com/api/eod/AAA.AU"))
    assert token in wire2[-1][0] + str(wire2[-1][1])
    assert token not in str(ei.value) + repr(ei.value) and ei.value.__cause__ is None


def test_eodhd_token_file_rules(tmp_path: Path) -> None:
    for text in ("", "none", "short", "has space in it 12345", "x" * 300):
        p = tmp_path / "t"
        p.write_text(text)
        assert eodhd_shim.read_token(p) == ""
    assert eodhd_shim.read_token(tmp_path / "missing") == ""
    cls, _ = _session()
    assert not eodhd_shim.install(cls, "", "header") and not eodhd_shim.install(
        cls, "abcdefgh1234", "cookie"
    )
    assert eodhd_shim.redact("a tok%2Fen b tok/en", "tok/en") == "a REDACTED b REDACTED"


# ---------------------------------------------------------------- relay
def _put(base: Path, rel: str, data: bytes | str) -> Path:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return p


def test_relay_pull_accepts_only_expected_files(tmp_path: Path) -> None:
    raw, val, rej = tmp_path / "raw", tmp_path / "validated", tmp_path / "rejected"
    good = {
        "newsc/2026-12-14/F_01_p1.json": '{"ratings": []}', "newsc/2026-12-14/meta.json": '{"model": "m"}',
        "newsc/2026-12-14/drops_p2.json": "{}", "reports/2026-12-14/report.json": '{"schema": 1}',
        "reports/2026-12-14/report.md": "# Report\n", "fence.json": '{"epoch": 3, "writer": "cloud"}',
        "ledger_requests/20270105-001-trials.json": "{}", "ledger_requests/AMENDMENT_x_v1.md": "text",
    }  # fmt: skip
    bad = {
        "newsc/2026-12-14/F_01_p3.json": "{}", "newsc/2026-12-14/run.sh": "#!/bin/sh\nid\n",
        "newsc/2026-12-14/H_02_p1.json": "not json", "reports/2026-12-14/report.html": "<script>",
        "evil.py": "import os", "newsc/../../etc/cron.d/x": "* * * * * root id", "reports/2026-12-14/report.md.sh": "x",
        "newsc/2026-12-14/F_02_p1.json": "x" * (300 * 1024), "ledger_requests/20270105-001-handover.json.exe": "{}",
    }  # fmt: skip
    for rel, data in {**good, **bad}.items():
        if ".." not in rel:
            _put(raw, rel, data)
    (raw / "newsc/2026-12-14/link_p1.json").symlink_to("/etc/passwd")
    res = relay.validate(raw, val, rej)
    assert sorted(res.accepted) == sorted(good)
    assert {n for n, _ in res.rejected} >= {k for k in bad if ".." not in k}
    assert not (val / "evil.py").exists() and not list(val.rglob("*.sh"))
    assert relay.classify("newsc/../../etc/cron.d/x", 10)[1] == "bad path"
    assert relay.relay_fence(val) == fence.Fence(3, "cloud", "writer")
    # write-once: a second, different reply with an accepted name is refused; a report may be replaced
    _put(raw, "newsc/2026-12-14/F_01_p1.json", '{"ratings": [1]}')
    _put(raw, "reports/2026-12-14/report.md", "# Report v2\n")
    res2 = relay.validate(raw, val, rej)
    assert (
        res2.accepted == ["reports/2026-12-14/report.md"]
        and "already accepted" in res2.rejected[0][1]
    )
    assert (val / "newsc/2026-12-14/F_01_p1.json").read_text() == '{"ratings": []}'


def test_relay_export_stages_the_readable_record_and_the_head_last(tmp_path: Path) -> None:
    root, out = tmp_path / "t", tmp_path / "outbox"
    rec = S.make_tree(root, writer="server", epoch=2)
    S.book_day(root, "2026-12-21")
    S.raw_inputs(root, "2026-12-21")
    _put(rec, "paper/intraday.csv.gz", gzip.compress(b"vendor rows"))
    info = relay.export(root, out, {"disk_free_gb": 30.1}, "2026-12-21")
    assert (
        info["head"] == L.head(rec / "LEDGER.jsonl")
        and info["seq"] == 4
        and info["writer"] == "server"
    )
    assert (out / "record/LEDGER.jsonl").read_bytes() == (rec / "LEDGER.jsonl").read_bytes()
    assert (out / "record/WRITER.json").is_file() and (out / "state/state.json").is_file()
    assert json.loads((out / "daily/2026-12-21/status.json").read_text())["disk_free_gb"] == 30.1
    # vendor data never leaves readable: no bulk files, no .gz
    assert not list(out.rglob("*.gz")) and not (out / "bulk").exists()
    assert relay.export(root, out)["files_changed"] == 0  # unchanged files are not staged again
    assert relay.gate(info["head"], info["head"])[0]
    blocked = relay.gate(info["head"], "f" * 64)
    assert not blocked[0] and "waits" in blocked[1]


def _request(
    rid: str, kind: str, fields: dict[str, Any], att: list[dict[str, str]] | None = None
) -> str:
    return json.dumps({"schema": 1, "id": rid, "kind": kind, "fields": fields, "attachments": att or [],
                       "requested_utc": "2027-01-05T01:02:03Z"})  # fmt: skip


def test_research_requests_wait_for_the_owner_and_cannot_forge_chain_entries(
    tmp_path: Path,
) -> None:
    """D6 / plan 6.4: the cloud asks, the owner confirms, the server appends."""
    root, val, done = tmp_path / "t", tmp_path / "validated", tmp_path / "done"
    rec = S.make_tree(root, writer="server", epoch=2)
    amend = b"# AMENDMENT made-up\n"
    _put(val, "ledger_requests/AMENDMENT_made_up.md", amend)
    _put(val, "ledger_requests/20270105-001-amendment.json", _request(
        "20270105-001-amendment", "amendment", {"asof": "2027-01-05", "event": "made-up amendment",
                                                "amendment": "AMENDMENT_made_up.md"},
        [{"name": "AMENDMENT_made_up.md", "sha256": L.sha_bytes(amend)}]))  # fmt: skip
    _put(
        val,
        "ledger_requests/20270105-002-trials.json",
        _request(
            "20270105-002-trials",
            "trials",
            {"asof": "2027-01-05", "event": "made-up trials", "n_trials": 12},
        ),
    )
    forged: dict[str, dict[str, Any]] = {
        "20270105-003-note": {"asof": "2027-01-05", "event": "x", "kind": "handover-accepted"},
        "20270105-004-note": {"asof": "2027-01-05", "event": "x", "seq": 1},
        "20270105-005-note": {"asof": "2027-01-05", "event": "x", "standby": True},
        "20270105-006-note": {"event": "no asof"},
    }
    for rid, fields in forged.items():
        _put(val, f"ledger_requests/{rid}.json", _request(rid, "note", fields))
    good, bad = relay.pending(val, done)
    assert [r.id for r in good] == ["20270105-001-amendment", "20270105-002-trials"] and len(
        bad
    ) == 4
    assert "n_trials 12" in good[1].summary() and "AMENDMENT_made_up.md" in good[0].summary()
    with pytest.raises(relay.RequestError):  # the cloud cannot apply it; only the writer
        relay.apply_request(root, val, done, good[0], "cloud")
    e = relay.apply_request(root, val, done, good[0], "server")
    assert (
        e["seq"] == 4 and e["kind"] == "amendment" and e["request_id"] == "20270105-001-amendment"
    )
    assert (rec / "AMENDMENT_made_up.md").read_bytes() == amend
    assert [r.id for r in relay.pending(val, done)[0]] == ["20270105-002-trials"]
    # an existing amendment file is never changed by a request
    _put(val, "ledger_requests/AMENDMENT_made_up.md", b"changed\n")
    _put(val, "ledger_requests/20270106-001-amendment.json", _request(
        "20270106-001-amendment", "amendment", {"asof": "2027-01-06", "event": "again"},
        [{"name": "AMENDMENT_made_up.md", "sha256": L.sha_bytes(b"changed\n")}]))  # fmt: skip
    again = next(r for r in relay.pending(val, done)[0] if r.id.startswith("20270106"))
    with pytest.raises(relay.RequestError, match="already exists"):
        relay.apply_request(root, val, done, again, "server")
    out = bwrec(root, "requests", str(val), str(done), "--apply", "20270105-002-trials")
    assert out.returncode == 0 and out.stdout.startswith("appended seq 5")
    L.verify(L.read(rec / "LEDGER.jsonl"))


# ---------------------------------------------------------------- bundle, manifest, compare
def _cloud_and_shadow(tmp_path: Path) -> tuple[Path, Path]:
    cloud, shadow = tmp_path / "cloud", tmp_path / "shadow"
    S.make_tree(cloud, writer="cloud")
    (cloud / paths.REL_CODE).mkdir(parents=True)
    (cloud / paths.REL_CODE / "paper_made_up.py").write_text("# the same code on both machines\n")
    shutil.copytree(cloud, shadow)  # the seed
    fence.save(paths.record_dir(shadow), fence.Fence(1, "server", "shadow"))
    sync_bundle.make(cloud, "seed", tmp_path / "x.tar", mark_only=True)
    return cloud, shadow


def _replay_day(tmp_path: Path, cloud: Path, shadow: Path, day: str, nav: float = 10100.0,
                shadow_nav: float | None = None, t: float = 1_700_200_000) -> dict[str, Any]:  # fmt: skip
    """One made-up day end to end: the cloud books it and bundles its raw inputs; the
    shadow applies the bundle and books the same day; then the comparison."""
    S.raw_inputs(cloud, day, close=nav / 1000)
    S.archive_day(cloud, day)
    S.archive_day(shadow, day)  # the server collects its own archive
    S.book_day(cloud, day, nav, now=t)
    L.append(paths.ledger(cloud), {"kind": "trials", "asof": day, "event": "hand-written, cloud only",
                                   "n_trials": 1}, now=t + 5)  # fmt: skip
    tar = tmp_path / f"bundle_{day}.tar"
    made = sync_bundle.make(cloud, day, tar)
    assert made["members"] == 1
    man = sync_bundle.cloud_manifest(cloud, day, [day])
    assert sync_bundle.apply(tar, shadow)["applied"] == 1
    S.book_day(
        shadow, day, nav if shadow_nav is None else shadow_nav, now=t + 3600
    )  # later, other chain
    return record_compare.compare(man, record_compare.shadow_files(shadow, [day]),
                                  record_compare.shadow_entries(shadow, day), day,
                                  today=dt.date.fromisoformat(day),
                                  server_code_files=hashing.tree(shadow, [paths.REL_CODE]))  # fmt: skip


def test_three_made_up_days_replay_identically_then_a_difference_fails(tmp_path: Path) -> None:
    """E14: end-to-end replay of three made-up days through bundle, apply and compare."""
    cloud, shadow = _cloud_and_shadow(tmp_path)
    days = ["2026-12-14", "2026-12-15", "2026-12-16"]
    results = []
    for i, d in enumerate(days):
        res = _replay_day(tmp_path, cloud, shadow, d, 10000.0 + i, t=1_700_200_000 + i * 86400)
        assert res["pass"], res
        assert (
            res["line"]
            == f"Shadow compare {int(d[-2:])} Dec: PASS (A {2 + i}/{2 + i}, B 2/2, C 1/1, D ok, code ok)"
        )
        results.append(res)
    assert record_compare.streak(results, days) == 3
    # the two chains differ (other times, the cloud's hand-written entries) and both verify
    assert L.head(paths.ledger(cloud)) != L.head(paths.ledger(shadow))
    bad = _replay_day(tmp_path, cloud, shadow, "2026-12-17", 10003.0, shadow_nav=10003.01)
    assert not bad["pass"] and "FAIL" in bad["line"]
    assert (
        not bad["classes"]["A"]["ok"]
        and not bad["classes"]["B"]["ok"]
        and not bad["classes"]["C"]["ok"]
    )
    diff = bad["classes"]["A"]["diffs"][0]
    assert diff["path"].endswith("state.json") and diff["cloud"] != diff["server"]
    # pass criterion 1: a strict difference resets the count of consecutive days to zero
    assert record_compare.streak([*results, bad], [*days, "2026-12-17"]) == 0
    assert record_compare.streak(results, [*days, "2026-12-17"]) == 0  # a missing day too


def test_compare_rules_by_class(tmp_path: Path) -> None:
    cloud, shadow = _cloud_and_shadow(tmp_path)
    day = "2026-12-14"
    S.archive_day(cloud, day)
    d = S.archive_day(shadow, day)
    S.book_day(cloud, day)
    S.book_day(shadow, day)
    for root in (cloud, shadow):  # same data, gzipped at different times
        p = root / paths.REL_DATA / "asic_short" / "RR20261210-001-SSDailyAggShortPos.csv.gz"
        p.parent.mkdir(parents=True, exist_ok=True)
        with (
            p.open("wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=1 if root == cloud else 99) as f,
        ):
            f.write(b"Product,Product Code\r\nMADE UP LTD,AAA\r\n")
    cp = cloud / paths.REL_DATA / "asic_short" / "RR20261210-001-SSDailyAggShortPos.csv.gz"
    assert cp.read_bytes() != (shadow / cp.relative_to(cloud)).read_bytes()
    # class E: fetch times and intraday files differ and do not fail
    (d / "ps_state.json").write_text('{"runs": [{"start_utc": "other"}]}')
    (paths.record_dir(shadow) / "paper" / "INTRADAY.md").write_text("server look\n")
    (d / "DONE_PS").write_text('{"utc": "other time"}')  # markers: presence only

    def run() -> dict[str, Any]:
        man = sync_bundle.cloud_manifest(cloud, day, [day])
        return record_compare.compare(man, record_compare.shadow_files(shadow, [day]),
                                      record_compare.shadow_entries(shadow, day), day,
                                      today=dt.date(2026, 12, 14),
                                      server_code_files=hashing.tree(shadow, [paths.REL_CODE]))  # fmt: skip

    ok = run()
    assert ok["pass"] and ok["classes"]["E"]["total"] >= 2 and not ok["classes"]["E"]["ok"]
    # class D strict: a different PDF, a missing marker, a changed list
    (d / "pdf" / "AAA_0001.pdf").write_bytes(b"%PDF other")
    assert not run()["classes"]["D"]["ok"]
    S.archive_day(shadow, day)
    (d / "DONE").unlink()
    assert not run()["classes"]["D"]["ok"]
    S.archive_day(shadow, day)
    assert run()["pass"]
    # class C: an unpaired entry on either side fails; dropped keys only are ignored
    L.append(paths.ledger(shadow), {"kind": "month-end", "asof": day, "event": "only here"})
    c = run()["classes"]["C"]
    assert not c["ok"] and c["diffs"][0]["cloud"] == "missing"
    a = {"kind": "multi", "asof": day, "api_credits": 5, "seq": 9, "recorded_utc": "a", "entry_sha256": "x",
         "prev_entry_sha256": "y", "code_sha256": "same"}  # fmt: skip
    b = {**a, "api_credits": 0, "seq": 3, "recorded_utc": "b"}
    assert record_compare.canonical(a) == record_compare.canonical(b)
    assert record_compare.canonical(a) != record_compare.canonical({**b, "code_sha256": "other"})
    assert record_compare.canonical(
        {"kind": "daily", "api_credits": 1}
    ) != record_compare.canonical({"kind": "daily"})
    assert not record_compare.job_entry({"kind": "amendment + code"}) and record_compare.job_entry(
        {"kind": "info_news"}
    )
    # an empty comparison is never a pass
    empty = record_compare.compare({"files": {}}, {}, [], day, server_code_files={})
    assert not empty["pass"] and "no states or outputs to compare" in empty["line"]
    assert record_compare.load_allow() == ()  # the written allow-list is empty and frozen


def test_a_day_counts_only_if_it_was_booked_archived_and_run_on_the_same_code(
    tmp_path: Path,
) -> None:
    """Review: a day on which nothing happened, or with other code on the server, never
    counts toward the five days."""
    cloud, shadow = _cloud_and_shadow(tmp_path)
    day = "2026-12-14"
    S.archive_day(cloud, day)
    S.archive_day(shadow, day)
    S.book_day(cloud, day)
    S.book_day(shadow, day)
    code = hashing.tree(shadow, [paths.REL_CODE])

    def run(man: dict[str, Any], sc: dict[str, str] = code) -> dict[str, Any]:
        return record_compare.compare(man, record_compare.shadow_files(shadow, man.get("archive_days") or []),
                                      record_compare.shadow_entries(shadow, day), day,
                                      today=dt.date(2026, 12, 14), server_code_files=sc)  # fmt: skip

    good = sync_bundle.cloud_manifest(cloud, day, [day])
    assert run(good)["pass"] and list(good["code"]) == [f"{paths.REL_CODE}/paper_made_up.py"]
    # the server runs other code than the cloud: FAIL, named
    other = run(good, {**code, f"{paths.REL_CODE}/paper_made_up.py": "0" * 64})
    assert not other["pass"] and "code DIFFERS" in other["line"] and not other["classes"]["K"]["ok"]
    assert not run(good, {**code, f"{paths.REL_CODE}/only_here.py": "1" * 64})["pass"]
    # a manifest without code hashes (an older tool), without an archive day, or of a day
    # the cloud did not book: never a pass, whatever else matches
    assert "lists no code" in run({**good, "code": {}})["line"]
    assert "no archive day was compared" in run({**good, "archive_days": []})["line"]
    quiet = "2026-12-15"  # both sides idle: states and outputs trivially identical
    man = sync_bundle.cloud_manifest(cloud, quiet, [day])
    res = record_compare.compare(man, record_compare.shadow_files(shadow, [day]),
                                 record_compare.shadow_entries(shadow, quiet), quiet,
                                 today=dt.date(2026, 12, 15), server_code_files=code)  # fmt: skip
    assert not res["pass"] and "booked no daily entry" in res["line"]
    assert all(res["classes"][k]["ok"] for k in "ABCD")
    # the real checkout's code map names the files as the tree does
    sc = record_compare.server_code()
    assert f"{paths.REL_CODE}/paper_daily.py" in sc and f"{paths.REL_DF_CODE}/eodhd/client.py" in sc
    assert record_compare.server_code(only=paths.REL_CODE).keys() < sc.keys()


def test_streak_must_end_at_the_last_session(tmp_path: Path) -> None:
    from record.tools import bwrec as cli

    sync = tmp_path / paths.REL_OUT / "sync"
    sync.mkdir(parents=True)

    def results(days: dict[str, bool]) -> None:
        for p in sync.glob("compare_*.json"):
            p.unlink()
        for d, ok in days.items():
            (sync / f"compare_{d}.json").write_text(json.dumps({"day": d, "pass": ok}))

    week = ["2026-12-14", "2026-12-15", "2026-12-16", "2026-12-17", "2026-12-18"]
    sat = dt.datetime(2026, 12, 19, 18, 0, tzinfo=steps.SYD)
    results(dict.fromkeys(week, True))
    assert cli.compare_streak(tmp_path, sat) == 5
    assert cli.last_session(sat) == dt.date(2026, 12, 18)
    # the run ended a day early (Friday was never compared): it counts for nothing
    results(dict.fromkeys(week[:4], True))
    assert cli.compare_streak(tmp_path, sat) == 0
    # a missing day in the middle breaks it
    results({d: True for d in week if d != "2026-12-16"})
    assert cli.compare_streak(tmp_path, sat) == 2
    results({**dict.fromkeys(week, True), "2026-12-17": False})
    assert cli.compare_streak(tmp_path, sat) == 1
    # a week later the same five days are stale
    results(dict.fromkeys(week, True))
    assert cli.compare_streak(tmp_path, sat + dt.timedelta(days=7)) == 0
    # a weekday: today's session counts only once it has closed
    assert cli.last_session(dt.datetime(2026, 12, 18, 12, 0, tzinfo=steps.SYD)) == dt.date(
        2026, 12, 17
    )
    assert cli.last_session(dt.datetime(2026, 12, 18, 21, 0, tzinfo=steps.SYD)) == dt.date(
        2026, 12, 18
    )
    assert cli.compare_streak(tmp_path / "none", sat) == 0


def test_server_archive_outside_the_tree_is_compared_under_the_clouds_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On the server the announcements archive is a separate folder mounted into the
    container; the comparison lists it under the same paths as the cloud's in-tree copy."""
    cloud, server = tmp_path / "cloud", tmp_path / "server"
    day = "2026-12-14"
    S.archive_day(cloud, day)
    moved = S.archive_day(server, day)
    info = tmp_path / "info"
    (info / "asx_notices").mkdir(parents=True)
    shutil.move(str(moved), str(info / "asx_notices" / day))
    want = record_compare.shadow_files(cloud, [day])
    assert not any("asx_notices" in k for k in record_compare.shadow_files(server, [day]))
    monkeypatch.setenv("BW_INFO_DIR", str(info))
    assert record_compare.shadow_files(server, [day]) == want
    assert f"{paths.REL_DATA}/asx_notices/{day}/list.csv" in want


def test_bundle_apply_refuses_anything_unsafe(tmp_path: Path) -> None:
    root = tmp_path / "t"
    root.mkdir()

    def tar_of(members: list[tuple[str, bytes, str]], meta: dict[str, Any] | None) -> Path:
        p = tmp_path / "b.tar"
        with tarfile.open(p, "w") as tar:
            if meta is not None:
                blob = json.dumps(meta).encode()
                ti = tarfile.TarInfo("BUNDLE.json")
                ti.size = len(blob)
                tar.addfile(ti, io.BytesIO(blob))
            for name, data, kind in members:
                ti = tarfile.TarInfo(name)
                if kind == "link":
                    ti.type, ti.linkname = tarfile.SYMTYPE, "/etc/passwd"
                    tar.addfile(ti)
                else:
                    ti.size = len(data)
                    tar.addfile(ti, io.BytesIO(data))
        return p

    good = "bigwins_forward/data/bulk/2026-12-14/eod.json.gz"
    h = L.sha_bytes(b"data")
    cases = [
        ([(good, b"data", "f")], None),  # no member list
        ([(good, b"other", "f")], {"schema": 1, "members": {good: h}}),  # hash mismatch
        ([("../../etc/cron.d/x", b"data", "f")], {"schema": 1, "members": {"../../etc/cron.d/x": h}}),
        ([("/etc/x", b"data", "f")], {"schema": 1, "members": {"/etc/x": h}}),
        ([("onedrive/research2/68_forward_record/LEDGER.jsonl", b"data", "f")],
         {"schema": 1, "members": {"onedrive/research2/68_forward_record/LEDGER.jsonl": h}}),  # never the ledger
        ([(good, b"", "link")], {"schema": 1, "members": {good: h}}),
        ([(good, b"data", "f"), ("bigwins_forward/data/bulk/extra", b"data", "f")], {"schema": 1, "members": {good: h}}),
        ([], {"schema": 1, "members": {good: h}}),  # a listed member is missing
    ]  # fmt: skip
    for members, meta in cases:
        with pytest.raises(sync_bundle.BundleError):
            sync_bundle.apply(tar_of(members, meta), root)
        assert not list(root.rglob("*.gz")) and not list(root.rglob("LEDGER.jsonl"))
    assert sync_bundle.apply(tar_of([(good, b"data", "f")], {"schema": 1, "day": "d", "members": {good: h}}), root) == {
        "day": "d", "applied": 1}  # fmt: skip
    (tmp_path / "junk.tar").write_bytes(b"not a tar")
    with pytest.raises(sync_bundle.BundleError):
        sync_bundle.apply(tmp_path / "junk.tar", root)
    assert bwrec(root, "bundle-apply", str(tmp_path / "junk.tar")).returncode == 1


# ---------------------------------------------------------------- jobs, units, tool steps
def test_job_table_covers_every_cloud_task_and_units_are_valid() -> None:
    """E4: every moved job has a timer with an explicit Australia/Sydney zone."""
    scripts = {s.name for j in jobs.JOBS.values() for s in j.steps if s.kind == "py"}
    assert scripts >= {"paper_daily.py", "paper_costalt.py", "paper_intraday.py", "paper_multi.py",
                       "est_snapshot.py", "newlist_tracker.py", "info_archive.py", "newsc_prepare.py",
                       "newsc_drops.py", "paper_us_forward.py", "movers.py"}  # fmt: skip
    for name in scripts:
        assert (REPO / "record/code" / name).is_file()
    tools = {s.name for j in jobs.JOBS.values() for s in j.steps if s.kind == "tool"}
    assert tools == set(steps.TOOLS)
    # the only job that may contact asx.com.au is the archive; the AI-free NEWS-C steps have no network
    assert [
        k for k, j in jobs.JOBS.items() if any(s.name == "info_archive.py" for s in j.steps)
    ] == ["archive"]
    assert not jobs.JOBS["newsc-prepare"].network and not jobs.JOBS["newsc-record"].network
    assert (
        not jobs.JOBS["replay"].network and not jobs.JOBS["replay"].eodhd
    )  # the replay downloads nothing
    assert not jobs.JOBS["archive"].eodhd  # the archive job never gets the EODHD token
    units = runpy.run_path(
        str(REPO / "deploy" / "record_units.py")
    )  # root writes timers from deploy code
    chains = {u.chain for u in units["UNITS"]}
    assert chains == {
        "morning",
        "collect",
        "newsc",
        "intraday",
        "daily",
        "multi",
        "usfwd",
        "compare",
        "relay",
    }
    for u in units["UNITS"]:
        svc, tmr = units["unit_files"](u, "/srv/asx-trader/deploy/bigwins.sh")
        assert f"ExecStart=/srv/asx-trader/deploy/bigwins.sh record run {u.chain}\n" in svc
        cals = [ln for ln in tmr.splitlines() if ln.startswith("OnCalendar=")]
        assert len(cals) == len(u.calendars) and all(c.endswith(" Australia/Sydney") for c in cals)
        if shutil.which("systemd-analyze"):
            for c in cals:
                r = subprocess.run(
                    ["systemd-analyze", "calendar", c.split("=", 1)[1]],
                    capture_output=True,
                    check=False,
                )
                assert r.returncode == 0, c
    assert not hasattr(jobs, "UNITS")  # nothing under record/ decides what root installs
    assert set(jobs.EXPECT) <= {*jobs.JOBS, "export", "compare", "pdf-backup"}
    # memory: the heavy jobs run in the evening; everything in or near ASX hours is small
    assert {k: j.memory_mb for k, j in jobs.JOBS.items()} == {
        "daily": 1500, "multi": 1500, "usfwd": 1500, "replay": 1500, "collect": 800, "intraday": 600,
        "archive": 600, "newsc-prepare": 600, "newsc-record": 600, "newsc-drops-record": 600}  # fmt: skip


def test_bwrec_units_and_gate(tmp_path: Path) -> None:
    out = tmp_path / "units"
    out.mkdir()
    r = subprocess.run([sys.executable, "-I", str(REPO / "deploy/record_units.py"), "write", str(out),
                        "/srv/asx-trader/deploy/bigwins.sh"], capture_output=True, text=True, check=False)  # fmt: skip
    assert r.returncode == 0 and len(list(out.glob("bigwins-rec-*.timer"))) == 9
    assert "rec-compare shadow" in r.stdout and "rec-intraday writer" in r.stdout
    assert bwrec(tmp_path, "units", str(out), "x").returncode == 2  # no longer a record tool
    root = tmp_path / "t"
    rec = S.make_tree(root, writer="server", epoch=2)
    shipped = tmp_path / "shipped_head"
    shipped.write_text(L.head(rec / "LEDGER.jsonl"))
    assert bwrec(
        root, "gate", "daily", "--shipped", str(shipped), "--free-gb", "40"
    ).stdout.startswith("ok")
    assert "writer fence" in bwrec(root, "gate", "daily", "--free-gb", "40", me="cloud").stdout
    # a job that never writes the ledger passes the fence (the server keeps collecting after
    # a hand-back or a takeover); a hold stops the ledger jobs only
    assert bwrec(root, "gate", "archive", "--free-gb", "40", me="cloud").returncode == 0
    hold = tmp_path / "HOLD"
    hold.write_text("restored")
    held = bwrec(
        root, "gate", "daily", "--shipped", str(shipped), "--free-gb", "40", "--hold", str(hold)
    )
    assert held.returncode == 1 and "on hold" in held.stdout and "reconcile" in held.stdout
    assert bwrec(root, "gate", "archive", "--free-gb", "40", "--hold", str(hold)).returncode == 0
    S.book_day(root, "2026-12-21")  # an entry that has not reached OneDrive yet
    g = bwrec(root, "gate", "daily", "--shipped", str(shipped), "--free-gb", "40")
    assert g.returncode == 1 and "ledger shipping" in g.stdout
    # jobs that do not write the ledger are not held by shipping; disk rules still apply
    assert (
        bwrec(root, "gate", "archive", "--shipped", str(shipped), "--free-gb", "40").returncode == 0
    )
    assert "refused (disk)" in bwrec(root, "gate", "collect", "--free-gb", "2.5").stdout
    relay_dir = tmp_path / "validated"
    _put(relay_dir, "fence.json", json.dumps({"epoch": 9, "writer": "cloud"}))
    assert "newer writer" in bwrec(root, "gate", "daily", "--relay", str(relay_dir), "--free-gb", "40",
                                   "--shipped", str(shipped)).stdout  # fmt: skip
    assert (
        bwrec(root, "gate", "archive", "--relay", str(relay_dir), "--free-gb", "40").returncode == 0
    )
    st = json.loads(bwrec(root, "status").stdout)
    assert st["writer"] == "server" and st["epoch"] == 2 and st["chain_ok"] and st["seq"] == 4


def test_asic_daily_copies_match_the_cloud_convention(tmp_path: Path) -> None:
    """T3 (B) without a subagent: LF copies of the archive's files for the CXL line."""
    src = tmp_path / paths.REL_DATA / "asic_short"
    src.mkdir(parents=True)
    body = b"Product,Product Code,Reported Short Positions\r\nMADE UP LTD,AAA,100\r\n"
    for name in (
        "RR20261210-001-SSDailyAggShortPos.csv.gz",
        "RR20200101-001-SSDailyAggShortPos.csv.gz",
        "junk.gz",
    ):
        with gzip.open(src / name, "wb") as f:
            f.write(body)
    assert steps.asic_daily(tmp_path, today=dt.date(2026, 12, 14)) == 0
    out = sorted(p.name for p in (tmp_path / "asic_daily").iterdir())
    assert out == ["RR20261210-001-SSDailyAggShortPos.csv"]  # recent files only; nothing else
    assert (tmp_path / "asic_daily" / out[0]).read_bytes() == body.replace(b"\r\n", b"\n")


def test_gap_check_names_the_missing_days(tmp_path: Path) -> None:
    days = [dt.date(2026, 12, 14), dt.date(2026, 12, 15)]
    S.archive_day(tmp_path, "2026-12-14")
    S.raw_inputs(tmp_path, "2026-12-14")
    S.raw_inputs(tmp_path, "2026-12-15")
    g = steps.gaps(tmp_path, dt.date(2026, 12, 16), days)
    assert (
        g["announcements_missing"] == ["2026-12-15"] and g["prices_missing"] == [] and not g["ok"]
    )
    S.archive_day(tmp_path, "2026-12-15")
    assert steps.gaps(tmp_path, dt.date(2026, 12, 16), days)["ok"]
    assert steps.weekdays(dt.date(2026, 12, 11), dt.date(2026, 12, 14)) == [
        dt.date(2026, 12, 11),
        dt.date(2026, 12, 14),
    ]


def test_newsc_meta_is_cleaned_and_replies_wait_until_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert steps.clean_meta({"model": "claude-x", "model_source": "get_session: a=b", "junk": 1}) == {
        "model": "claude-x", "model_source": "get_session: a=b"}  # fmt: skip
    bad: Any
    for bad in ({"model": "m"}, {"model": "--ledger=/tmp/x", "model_source": "s"}, {"model": "m\n", "model_source": "s"},
                {"model": "m", "model_source": "s" * 500}, {"model": 5, "model_source": "s"}, []):  # fmt: skip
        with pytest.raises(ValueError):
            steps.clean_meta(bad)
    root, inbox = tmp_path / "t", tmp_path / "inbox"
    day = "2026-12-14"
    newsc = root / paths.REL_DATA / "newsc"
    _put(
        newsc,
        f"{day}/manifest.json",
        json.dumps({"batches": [{"batch": "F_01"}, {"batch": "H_01"}]}),
    )
    _put(inbox, f"newsc/{day}/meta.json", json.dumps({"model": "m", "model_source": "s"}))
    _put(inbox, f"newsc/{day}/F_01_p1.json", "{}")
    monkeypatch.setenv("BW_RELAY_INBOX", str(inbox))
    calls: list[list[str]] = []

    def fake_launch(args: list[str], capture: bool) -> tuple[int, str]:
        calls.append(list(args))
        return 0, "{}"

    monkeypatch.setattr(steps, "_launch", fake_launch)
    assert steps.newsc_record(root) == 0 and calls == []  # 3 replies missing: wait, record nothing
    for name in ("F_01_p2.json", "H_01_p1.json", "H_01_p2.json"):
        _put(inbox, f"newsc/{day}/{name}", '{"r": 1}')
    assert steps.newsc_record(root, dry_run=True) == 0
    assert calls[0][:3] == ["newsc_record.py", "--day", day] and calls[0][-1] == "--dry-run"
    assert (newsc / day / "incoming" / "H_01_p2.json").read_bytes() == b'{"r": 1}'  # byte for byte
    assert (root / paths.REL_OUT / "sync" / f"dryrun_newsc_record_{day}.json").is_file()
    assert steps.newsc_record(root, dry_run=True) == 0 and len(calls) == 1  # once per day
    assert steps.newsc_record(root) == 0 and "--dry-run" not in calls[1]
    assert steps.pending_day(inbox, newsc, "RELAY_RECORDED") is None
    # the drops step runs with no replies when the dossier is empty
    _put(newsc, f"{day}/drops_manifest.json", json.dumps({"dossier_path": None}))
    assert steps.newsc_drops_record(root) == 0 and calls[2][0] == "newsc_drops_record.py"


# ---------------------------------------------------------------- disk and PDF backups
def test_disk_levels_and_gates() -> None:
    assert [ops.disk_level(x) for x in (30, 4.9, 2.9, 1.9)] == ["ok", "low", "tight", "critical"]
    mon, month_end = dt.date(2026, 12, 14), dt.date(2026, 12, 31)
    assert (
        ops.month_end(month_end) and ops.month_end(dt.date(2027, 1, 29)) and not ops.month_end(mon)
    )
    assert ops.disk_gate("daily", 2.5, mon)[0] and not ops.disk_gate("daily", 2.5, month_end)[0]
    assert ops.disk_gate("daily", 3.5, month_end) == (True, "low")
    assert not ops.disk_gate("collect", 2.5, mon)[0] and not ops.disk_gate("multi", 2.5, mon)[0]
    assert ops.disk_gate("archive", 1.5, mon)[0] and not ops.disk_gate("intraday", 1.5, mon)[0]


def test_pdf_backups_one_file_a_day_sixty_days_offsite(tmp_path: Path) -> None:
    """D4 and the 500 MB cap fix (E8): PDFs travel apart from the nightly archive."""
    info = tmp_path / "info"
    for day in ("2026-10-01", "2026-12-10", "2026-12-11"):
        d = info / "asx_notices" / day
        (d / "pdf").mkdir(parents=True)
        (d / "pdf" / "AAA_1.pdf").write_bytes(b"%PDF made-up " + day.encode())
        (d / "pdf" / "AAA_1.txt").write_text("text")
        (d / "list.csv").write_text("code\nAAA\n")
        (d / "DONE").write_text("ok")
        if day != "2026-12-11":
            (d / "DONE_PS").write_text("{}")
    (info / "asic_short").mkdir()
    (info / "asic_short" / "RR.csv.gz").write_bytes(b"x")
    assert ops.finished_days(info) == ["2026-10-01", "2026-12-10"]  # the unfinished day waits
    today = dt.date(2026, 12, 14)
    remote = ["asxpdf-2026-09-01.tar.age", "asxpdf-2026-12-09.tar.age", "notes.txt"]
    up, rm = ops.pdf_plan(ops.finished_days(info), remote, today)
    assert up == ["2026-12-10"] and rm == ["asxpdf-2026-09-01.tar.age"]  # old day: server only
    assert ops.pdf_plan(["2026-12-10"], ["asxpdf-2026-12-10.tar.age"], today) == (
        [],
        [],
    )  # uploaded once
    light = tmp_path / "light"
    res = ops.stage_light(info, light)
    assert res["pdfs_left_out"] == 3 and not list(light.rglob("*.pdf"))
    assert (light / "asx_notices/2026-12-10/list.csv").is_file() and (
        light / "asx_notices/2026-12-10/pdf/AAA_1.txt"
    ).is_file()
    line = (light / "asx_notices/2026-12-10/pdf.sha256").read_text()
    assert line == f"{hashing.sha_file(info / 'asx_notices/2026-12-10/pdf/AAA_1.pdf')}  AAA_1.pdf\n"


def test_tree_manifest_hashes_gz_on_content(tmp_path: Path) -> None:
    for name, mtime in (("a", 1), ("b", 2)):
        (tmp_path / name).mkdir()
        with (
            (tmp_path / name / "x.csv.gz").open("wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=mtime) as f,
        ):
            f.write(b"same rows")
        (tmp_path / name / ".daily.lock").write_text("")
        (tmp_path / name / "y.json.part").write_text("")
    ta, tb = hashing.tree(tmp_path / "a", ["."]), hashing.tree(tmp_path / "b", ["."])
    assert ta == tb and list(ta) == ["x.csv.gz"]
    assert (tmp_path / "a/x.csv.gz").read_bytes() != (tmp_path / "b/x.csv.gz").read_bytes()
    (tmp_path / "a/x.csv.gz").write_bytes(b"broken")
    assert hashing.tree(tmp_path / "a", ["."])["x.csv.gz"].startswith("unreadable-gzip:")


def test_prefix_check_refuses_an_older_or_different_local_ledger(tmp_path: Path) -> None:
    """Review (critical): a server restored from an older backup must never export over,
    or book on top of, the newer ledger in OneDrive."""
    new = tmp_path / "new"
    S.make_tree(new, writer="server", epoch=2)
    S.book_day(new, "2026-12-21")
    old = tmp_path / "old"
    shutil.copytree(new, old)
    S.book_day(new, "2026-12-22")  # the day after the backup was made
    remote = paths.ledger(new)
    ok = bwrec(new, "prefix-check", str(paths.ledger(old)))
    assert ok.returncode == 0 and "4 of this machine's 5" in ok.stdout  # OneDrive behind: fine
    assert bwrec(new, "prefix-check", str(remote)).returncode == 0  # equal: fine
    ahead = bwrec(old, "prefix-check", str(remote))  # the restored server
    assert ahead.returncode == 1 and "OneDrive is AHEAD: 5 entries there, 4 here" in ahead.stdout
    S.book_day(old, "2026-12-22", nav=1.0)  # it booked on the old head: a fork
    fork = bwrec(old, "prefix-check", str(remote))
    assert fork.returncode == 1 and "DIFFERENT chains" in fork.stdout
    (tmp_path / "junk").write_text("not a ledger\n")
    assert bwrec(old, "prefix-check", str(tmp_path / "junk")).returncode == 1


def test_requests_in_a_record_job_reach_eodhd_only() -> None:
    cls, wire = _session()
    assert eodhd_shim.install_allowlist(cls) and not eodhd_shim.install_allowlist(cls)
    eodhd_shim.install(cls, "tok3n-Made.Up_123456", "query")
    cls().send(_Req("https://eodhd.com/api/eod/AAA.AU"))
    assert len(wire) == 1 and "api_token=tok3n" in wire[0][0]
    for url in ("https://example.com/x", "http://eodhd.com/api/x", "https://www.asx.com.au/x",
                "https://eodhd.com.evil.example/x", "file:///etc/passwd"):  # fmt: skip
        with pytest.raises(eodhd_shim.HostRefusedError):
            cls().send(_Req(url))
    assert len(wire) == 1  # nothing else was sent anywhere, with or without a token


def test_view_copy_never_follows_a_link_out_of_the_source(tmp_path: Path) -> None:
    from record.tools import view

    src, dst, secret = tmp_path / "src", tmp_path / "dst", tmp_path / "elsewhere"
    dst.mkdir()
    (secret / "paper").mkdir(parents=True)
    (secret / "paper" / "scorecard_latest.csv").write_text("asof,book\n2026-12-14,SECRET\n")
    rec = src / paths.REL_RECORD
    rec.mkdir(parents=True)
    (rec / "paper").symlink_to(secret / "paper", target_is_directory=True)  # a planted link
    res = view.view_copy(src, dst, "x", "y")
    assert not res["ok"] and "link" in res["error"] and not (dst / "paper").exists()
    (rec / "paper").unlink()
    (rec / "paper").mkdir()
    (rec / "paper" / "scorecard_latest.csv").write_text("asof,book\n2026-12-14,T\n")
    (rec / "paper" / "leak.csv").symlink_to(
        secret / "paper" / "scorecard_latest.csv"
    )  # a linked file
    (src / paths.REL_OUT).mkdir(parents=True)
    (src / paths.REL_OUT / "movers").symlink_to(secret, target_is_directory=True)
    assert not view.view_copy(src, dst, "x", "y")["ok"]
    (src / paths.REL_OUT / "movers").unlink()
    ok = view.view_copy(src, dst, "x", "y")
    assert ok["ok"] and sorted(p.name for p in (dst / "paper").iterdir()) == [
        "scorecard_latest.csv"
    ]
