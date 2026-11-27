"""BF-D93: the paper record on the server, the host worker side (deploy/record.sh inside
deploy/bigwins.sh), the "record" update class, the record image and the install steps.
The shell functions run for real against made-up trees; docker, rclone, curl, age,
systemctl and setpriv are small stubs that log their calls. No network, no vendor data."""

from __future__ import annotations

import json
import os
import runpy
import shutil
import subprocess
from pathlib import Path
from typing import Any

from record.tools import fence, paths
from record.tools import ledgerlib as L
from tests import record_support as S
from trader import strategy_version as sv

REPO = Path(__file__).resolve().parents[1]
SH = REPO / "deploy" / "bigwins.sh"
REC = (REPO / "deploy" / "record.sh").read_text()
STUB = '#!/bin/sh\necho "$(basename "$0") $*" >> "{log}"\n{extra}exit $(cat "{rc}" 2>/dev/null || echo 0)\n'
RCLONE = r"""#!/bin/sh
echo "rclone $*" >> "{log}"
[ "$(cat "{rc}" 2>/dev/null || echo 0)" = 0 ] || exit 1
map() {{ case "$1" in bigwins-onedrive:*) echo "{remote}/${{1#bigwins-onedrive:}}";; *) echo "$1";; esac; }}
case "$1" in
  listremotes) echo "bigwins-onedrive:";;
  copy) s=$(map "$2"); d=$(map "$3"); mkdir -p "$d"; [ -d "$s" ] && cp -R "$s/." "$d/"; exit 0;;
  copyto) s=$(map "$2"); d=$(map "$3"); mkdir -p "$(dirname "$d")"; cp "$s" "$d" || exit 1;;
  lsf) ls "$(map "$2")" 2>/dev/null;;
  deletefile) rm -f "$(map "$2")";;
  mkdir) mkdir -p "$(map "$2")";;
esac
exit 0
"""


class Server:
    """The worker's functions with every path pointed into a temp folder."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        for d in (
            "state",
            "etc",
            "bin",
            "secrets",
            "relay",
            "view",
            "units",
            "remote",
            "backups",
            "info",
        ):
            (tmp / d).mkdir()
        self.log = tmp / "calls.log"
        b = tmp / "bin"
        job_out = 'if [ "$1" = run ]; then echo \'{"ok": true, "job": "x", "seconds": 1.5, "peak_mb": 321.0, "entries": []}\'; fi\n'
        (b / "docker").write_text(STUB.format(log=self.log, rc=tmp / "docker_rc", extra=job_out))
        for name in ("curl", "systemctl", "chown", "useradd", "age"):
            (b / name).write_text(STUB.format(log=self.log, rc=tmp / f"{name}_rc", extra=""))
        (b / "age").write_text(STUB.format(log=self.log, rc=tmp / "age_rc",
                                           extra='while [ $# -gt 0 ]; do [ "$1" = -o ] && cat > "$2"; shift; done\n'))  # fmt: skip
        (b / "age-keygen").write_text("#!/bin/sh\necho age1madeuprecipient\n")
        (b / "setpriv").write_text(f'#!/bin/sh\necho "setpriv $*" >> "{self.log}"\n'
                                   'while [ "${1#--}" != "$1" ]; do shift; done\nexec "$@"\n')  # fmt: skip
        (b / "id").write_text(
            '#!/bin/sh\nif [ "$1" = -u ] && [ $# = 1 ]; then echo 0; else exit 1; fi\n'
        )
        (b / "rclone").write_text(
            RCLONE.format(log=self.log, rc=tmp / "rclone_rc", remote=tmp / "remote")
        )
        for f in b.iterdir():
            f.chmod(0o755)
        (tmp / "units" / "bigwins-worker.timer").write_text("")
        self.tree, self.shadow, self.mirror = tmp / "tree", tmp / "shadow", tmp / "mirror"

    def mode(self, m: str) -> None:
        (self.tmp / "etc" / "record_mode").write_text(m + "\n")

    def run(
        self, script: str, stdin: str = "", today: str = ""
    ) -> subprocess.CompletedProcess[str]:
        t = self.tmp
        pre = (f'source "{SH}" __lib__ >/dev/null; REPO="{REPO}"; REC_TOOLS="{REPO}/record/tools/bwrec.py"; '
               f'DEPLOY="{t}/deploy"; SECRETS="{t}/secrets"; REC_UNITS="{REPO}/deploy/record_units.py"; '
               f'REC_HOLD="{t}/relay/state/HOLD"; '
               f'STATE="{t}/state"; ETC="{t}/etc"; REC_MODE_FILE="{t}/etc/record_mode"; '
               f'REC_TREE="{self.tree}"; REC_SHADOW="{self.shadow}"; REC_MIRROR="{self.mirror}"; '
               f'REC_VIEW="{t}/view"; RELAY="{t}/relay"; REC_UNIT_DIR="{t}/units"; '
               f'BACKUP_DIR="{t}/backups"; BKEY="{t}/backup.key"; REC_LOCK_WAIT=5; '
               f'info_dir() {{ echo "{t}/info"; }}; market_open() {{ return 1; }}; '
               'rec_mirror_fetch() { return 0; }; do_backup() { echo backup; }; ')  # fmt: skip
        env = {**os.environ, "PATH": f"{t / 'bin'}:{os.environ['PATH']}", "TZ": "Australia/Sydney",
               "BW_TODAY": today}  # fmt: skip
        return subprocess.run(["bash", "-c", pre + script], capture_output=True, text=True, env=env,
                              input=stdin, check=False)  # fmt: skip

    def calls(self, prefix: str = "") -> list[str]:
        if not self.log.is_file():
            return []
        return [x for x in self.log.read_text().splitlines() if x.startswith(prefix)]

    def events(self) -> list[dict[str, Any]]:
        p = self.tmp / "state" / "record" / "outbox.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.is_file() else []


# ---------------------------------------------------------------- the "record" update class
def test_BF_D93_record_update_class() -> None:
    """E6: the research code is its own class: owner approval, no trader restart, no version
    bump. Review: only code that runs INSIDE the record container is in it; the tools the
    worker runs on the host, and anything mixed with other changes, are not."""
    w = runpy.run_path(str(REPO / "deploy" / "classify.py"))
    rec = ["record/code/paper_daily.py", "record/data_foundation_code/eodhd/client.py",
           "record/MANIFEST.sha256", "record/ENVIRONMENT.json",
           "deploy/record.Dockerfile", "deploy/record_requirements.txt"]  # fmt: skip
    for f in rec:
        assert (
            w["classify"]([f]) == "record" and not sv.is_trading_path(f) and sv.is_record_path(f)
        ), f
    assert w["classify"]([*rec, "docs/HANDOVER.md", "tests/test_x.py"]) == "record"
    # host-side code is a trading / infrastructure change, with every guard of one
    for f in ("record/tools/fence.py", "record/tools/bwrec.py", "record/tools/jobs.py", "record/__init__.py",
              "record/COMPARE_ALLOW.json", "deploy/record.sh", "deploy/record_units.py"):  # fmt: skip
        assert (
            w["classify"]([f]) == "strategy" and sv.is_trading_path(f) and not sv.is_record_path(f)
        ), f
        assert w["classify"]([*rec, f]) == "strategy"
        assert sv.classify_update([*rec, f], None, None)["strategy"] is True
    assert w["classify"]([*rec, "trader/lines/emg2.py"]) == "strategy"
    # a commit that also changes an app file is an APP update (the app must be rebuilt):
    # never "record", which would leave the app on the old code with nothing pending
    for mixed in (["record/code/movers.py", "trader/record_view.py"], [*rec, "trader/webui.py"],
                  ["record/code/movers.py", "README.md"]):  # fmt: skip
        assert w["classify"](mixed) == "app", mixed
        cu = sv.classify_update(mixed, None, None)
        assert cu["strategy"] is False and not cu.get("record"), mixed
    assert w["classify"](["docs/x.md", "trader/record_view.py"]) == "app"
    assert (w["RECORD_DIRS"], w["RECORD_FILES"], w["TRADING_DIRS"]) == (
        sv.RECORD_DIRS, sv.RECORD_FILES, sv.TRADING_DIRS)  # fmt: skip
    cls = sv.classify_update(iter([*rec, "docs/x.md"]), None, None)
    assert cls["strategy"] is False and cls["record"] is True
    assert "paper record code: 6 file(s)" in cls["reasons"][0]
    # never applied automatically: not on the automatic allow-list
    au = runpy.run_path(str(REPO / "deploy" / "autoupdate.py"))
    for f in [*rec, "record/tools/fence.py"]:
        assert au["kind"]([f])[0] == "approval", f
    assert (
        au["kind"](["record/code/movers.py", "trader/record_view.py"])[0] == "approval"
    )  # mixed: never auto
    # no strategy-version change: nothing under record/ is an input of either hash
    assert not any(str(x).startswith("record") for x in sv.STRATEGY_FILES)
    assert sv.code_hash(REPO) == sv.code_hash(REPO)  # reads trader/ and config only
    assert "\nrecord\n" in (REPO / ".dockerignore").read_text()  # not in the trader image at all


def test_BF_D93_a_record_update_rebuilds_only_the_record_image(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("writer")
    (tmp_path / "state" / "update_kind").write_text("record\n")
    r = s.run("after_update")
    assert "The trader was not touched" in r.stdout, r.stdout + r.stderr
    d = s.calls("docker")
    assert any("build" in c and "record.Dockerfile" in c for c in d)
    assert not any(c.startswith("docker compose") for c in d)  # no trader build, no restart
    assert not (tmp_path / "state" / "update_kind").exists()
    sh = SH.read_text()
    assert (
        'printf \'%s\\n\' "$kind" > "$STATE/update_kind"' in sh
    )  # the approved update notes its class


# ---------------------------------------------------------------- jobs in the record container
def test_BF_D93_job_runs_in_a_locked_down_container_at_the_cloud_path(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    (tmp_path / "secrets" / "healthchecks_record_url").write_text(
        "https://hc-ping.com/made-up-ping-key"
    )
    assert s.run("rec_export").returncode == 0  # the ledger's head is in OneDrive
    r = s.run("rec_run_job daily")
    assert r.returncode == 0 and '"ok": true' in r.stdout, r.stdout + r.stderr
    run = next(c for c in s.calls("docker run"))
    for want in ("--rm", "-u 10002:10002", "--read-only", "--cap-drop ALL", "no-new-privileges:true",
                 "--memory 1500m", "--memory-swap 3000m", "--oom-score-adj 500", "--cpus 1.0", "-e TZ=UTC", "--network bigwins_record_egress",
                 f"-v {s.tree}:{paths.CLOUD_ROOT} ",
                 f"-v {REPO}/record/code:{paths.CLOUD_ROOT}/bigwins_forward/code:ro",
                 f"-v {REPO}/record/data_foundation_code:{paths.CLOUD_ROOT}/data_foundation/code:ro",
                 "/secrets/eodhd_api_token:/run/secrets/eodhd_api_token:ro",
                 "bigwins-record:local python3 -I /opt/bwrecord/record/tools/bwrec.py run-job daily"):  # fmt: skip
        assert want in run, want
    assert "docker.sock" not in run and "--privileged" not in run and "EODHD_API_TOKEN" not in run
    assert "asx_notices:ro" in run  # only the archive job may write the announcements archive
    # health-check pings: start, then success, one check per job
    pings = s.calls("curl")
    assert any("made-up-ping-key/bigwins-daily/start?create=1" in c for c in pings)
    assert any(c.endswith("made-up-ping-key/bigwins-daily?create=1") for c in pings)
    ev = s.events()[-1]
    assert ev["kind"] == "job" and ev["job"] == "daily" and ev["ok"] and ev["mode"] == "writer"
    assert ev["peak_mb"] == 321.0
    # a job without downloads has no network and no secret at all
    s.log.unlink()
    assert s.run("rec_run_job newsc-prepare").returncode == 0
    run = next(c for c in s.calls("docker run"))
    assert "--network none" in run and "eodhd_api_token" not in run and "egress" not in run
    s.log.unlink()
    s.run("rec_run_job archive")
    run = next(c for c in s.calls("docker run"))
    assert "asx_notices " in run and "asx_notices:ro" not in run and "eodhd_api_token" not in run


def test_BF_D93_job_is_refused_before_docker_when_the_gate_says_no(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("writer")
    rec = S.make_tree(s.tree, writer="cloud")  # the fence names the other machine
    (tmp_path / "secrets" / "healthchecks_record_url").write_text(
        "https://hc-ping.com/made-up-ping-key"
    )
    r = s.run("rec_run_job daily")
    assert r.returncode == 1 and "writer fence" in r.stdout
    assert not s.calls("docker run")
    ev = s.events()[-1]
    assert ev["ok"] is False and "writer fence" in ev["error"]
    assert any("bigwins-daily/fail" in c for c in s.calls("curl"))
    # ledger shipping: the writer's next job waits until the last entries reached OneDrive
    fence.save(rec, fence.Fence(2, "server", "writer"))
    (tmp_path / "relay" / "state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "relay" / "state" / "shipped_head").write_text("0" * 63 + "1")
    r = s.run("rec_run_job daily")
    assert r.returncode == 1 and "ledger shipping" in r.stdout and not s.calls("docker run")
    # the relay shows a newer writer (a takeover): no ledger job runs; the announcements are
    # still collected (two collectors are safer than one, and a missed ASX day is gone for good)
    (tmp_path / "relay" / "inbox" / "validated").mkdir(parents=True, exist_ok=True)
    (tmp_path / "relay" / "inbox" / "validated" / "fence.json").write_text(
        '{"epoch": 9, "writer": "cloud"}'
    )
    (tmp_path / "relay" / "state" / "shipped_head").write_text(L.head(rec / "LEDGER.jsonl"))
    assert "newer writer" in s.run("rec_run_job daily").stdout and not s.calls("docker run")
    assert s.run("rec_run_job archive").returncode == 0
    assert any("run-job archive" in c for c in s.calls("docker run"))


def test_BF_D93_chains_follow_the_mode(tmp_path: Path) -> None:
    s = Server(tmp_path)
    assert "not on this server yet" in s.run("rec_chain daily").stdout and not s.calls("docker")
    s.mode("view")
    assert "view only" in s.run("rec_chain daily").stdout and not s.calls("docker run")
    s.mode("shadow")
    S.make_tree(s.shadow, writer="server", role="shadow")
    for chain in ("intraday", "collect", "multi", "usfwd"):  # the shadow never downloads prices
        assert "nothing to do" in s.run(f"rec_chain {chain}").stdout
    assert not s.calls("docker run")
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    r = s.run("rec_chain intraday")
    assert r.returncode == 0, r.stdout + r.stderr
    assert any("run-job intraday" in c for c in s.calls("docker run"))
    # the chain exported the record afterwards and noted the shipped head
    assert (tmp_path / "remote" / "Big Wins relay" / "outbox" / "record" / "LEDGER.jsonl").is_file()
    assert (tmp_path / "relay" / "state" / "shipped_head").read_text().strip() == L.head(
        paths.ledger(s.tree))  # fmt: skip
    assert s.events()[-1]["job"] == "export" and s.events()[-1]["ok"]
    assert (
        tmp_path / "view" / "source.json"
    ).is_file() is False  # no scorecard in this made-up tree


def test_BF_D93_one_asx_collector_per_server(tmp_path: Path) -> None:
    """The archive is the only automated asx.com.au access; with the record here the
    older host job (deploy/info_archive.py) stands down, so the site is never asked twice."""
    s = Server(tmp_path)
    s.mode("shadow")
    r = s.run("INFO_SCRIPT=/nonexistent; info_enabled() { return 0; }; do_info_archive")
    assert r.returncode == 0 and "collected by the paper record's own job" in r.stdout
    from record.tools import jobs

    asx = [k for k, j in jobs.JOBS.items() if any(st.name == "info_archive.py" for st in j.steps)]
    assert asx == ["archive"]
    # the research collector keeps the owner's limits in its own code (unedited copy)
    src = (REPO / "record/code/info_archive.py").read_text()
    assert "PS_CAP = 60" in src and "GAP = 2.0" in src and "ASX_HOURS = ((10, 0), (16, 12))" in src


def test_BF_D93_export_failure_is_reported_and_holds_the_next_ledger_job(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    (tmp_path / "rclone_rc").write_text("1")
    r = s.run("rec_export 2026-12-21")
    assert r.returncode == 1
    assert not (tmp_path / "relay" / "state" / "shipped_head").exists()
    assert "OneDrive" in s.events()[-1]["error"] and s.events()[-1]["ok"] is False
    (tmp_path / "rclone_rc").write_text("0")
    assert s.run("rec_export 2026-12-21").returncode == 0
    status = json.loads(
        (tmp_path / "relay" / "outbox" / "daily" / "2026-12-21" / "status.json").read_text()
    )
    assert status["mode"] == "writer" and "disk_free_gb" in status


# ---------------------------------------------------------------- the relay pull
def test_BF_D93_relay_pull_validates_and_reports_once(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("view")
    inbox = tmp_path / "remote" / "Big Wins relay" / "inbox"
    (inbox / "reports" / "2026-12-15").mkdir(parents=True)
    (inbox / "reports" / "2026-12-15" / "report.json").write_text(
        '{"schema": 1, "day": "2026-12-15"}'
    )
    (inbox / "reports" / "2026-12-15" / "report.md").write_text("# report\n")
    (inbox / "evil.sh").write_text("#!/bin/sh\nid\n")
    r = s.run("rec_pull")
    assert r.returncode == 0, r.stdout + r.stderr
    val = tmp_path / "relay" / "inbox" / "validated"
    assert (val / "reports" / "2026-12-15" / "report.json").is_file() and not (
        val / "evil.sh"
    ).exists()
    kinds = [(e["kind"], e.get("ok")) for e in s.events()]
    assert kinds == [("relay", False), ("report", True)]
    assert "evil.sh" in s.events()[0]["rejected"][0]
    s.run("rec_pull")  # again: nothing new to say
    assert len(s.events()) == 2
    (inbox / "reports" / "2026-12-15" / "report.json").write_text(
        '{"schema": 1, "day": "2026-12-15", "verdict": "v2"}'
    )
    s.run("rec_pull")  # a corrected report is announced again
    assert [e["kind"] for e in s.events()].count("report") == 2
    assert "v2" in (val / "reports" / "2026-12-15" / "report.json").read_text()


# ---------------------------------------------------------------- timers
def test_BF_D93_timers_are_installed_and_rewritten_when_the_set_changes(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("shadow")
    r = s.run("rec_ensure_timers; rec_timer_states")
    assert r.returncode == 0, r.stderr
    units = tmp_path / "units"
    names = sorted(p.name for p in units.glob("bigwins-rec-*.timer"))
    assert (
        "bigwins-rec-daily.timer" in names
        and "bigwins-rec-compare.timer" in names
        and len(names) == 9
    )
    t = (units / "bigwins-rec-daily.timer").read_text()
    assert "OnCalendar=Mon..Fri *-*-* 20:27:00 Australia/Sydney" in t and "Persistent=true" in t
    assert "bigwins.sh record run daily" in (units / "bigwins-rec-daily.service").read_text()
    assert "rec-daily:1" in r.stdout and "rec-relay:1" in r.stdout
    assert any("enable --now bigwins-rec-daily.timer" in c for c in s.calls("systemctl"))
    s.log.unlink()
    s.run("rec_ensure_timers")
    assert not s.calls("systemctl")  # same version: nothing rewritten
    (units / ".bigwins-rec-units").write_text("an-older-version")
    (units / "bigwins-rec-gone.timer").write_text("old")
    s.run("rec_ensure_timers")
    assert not (units / "bigwins-rec-gone.timer").exists()  # a timer this version no longer has
    assert any("daemon-reload" in c for c in s.calls("systemctl"))
    assert "rec_ensure_timers  # BF-D93" in SH.read_text()  # the worker keeps them current


# ---------------------------------------------------------------- cut-over, hand-back, requests
CUT = "2026-12-19T18:00"  # Saturday evening after the parallel week


def _ready_for_cutover(s: Server, days: int = 5) -> str:
    """A shadow that reproduced the cloud for ``days`` days, and the cloud's handover."""
    cloud = s.tmp / "cloud"
    S.make_tree(cloud, writer="cloud")
    S.book_day(cloud, "2026-12-18")
    shutil.copytree(cloud, s.shadow)
    fence.save(paths.record_dir(s.shadow), fence.Fence(1, "server", "shadow"))
    sync = s.shadow / paths.REL_OUT / "sync"
    sync.mkdir(parents=True)
    for d in ["2026-12-14", "2026-12-15", "2026-12-16", "2026-12-17", "2026-12-18"][-days:]:
        (sync / f"compare_{d}.json").write_text(
            json.dumps({"day": d, "pass": True, "line": f"{d} PASS"})
        )
    h = fence.handover(
        paths.record_dir(cloud), "cloud", "2026-12-19", {"record_code_commit": "c" * 40}
    )
    shutil.copytree(cloud, s.mirror)  # the final paper-record commit the server fetches
    shutil.copytree(REPO / "record" / "code", s.mirror / paths.REL_CODE,
                    ignore=shutil.ignore_patterns("__pycache__"))  # fmt: skip
    s.mode("shadow")
    return str(h["entry_sha256"])


def test_BF_D93_cutover_needs_five_days_the_handover_and_the_owners_yes(tmp_path: Path) -> None:
    s = Server(tmp_path)
    head = _ready_for_cutover(s)
    no = s.run("rec_cutover", stdin="no\n", today=CUT)
    assert head[:12] in no.stdout and "Nothing changed" in no.stdout
    assert (
        s.shadow.is_dir()
        and not s.tree.exists()
        and "shadow" in (tmp_path / "etc/record_mode").read_text()
    )
    r = s.run("rec_cutover", stdin="yes\n", today=CUT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"Handover head, first 12 characters:   {head[:12]}" in r.stdout
    assert "This server is the only writer" in r.stdout
    es = L.read(paths.ledger(s.tree))
    L.verify(es)
    assert [e["kind"] for e in es[-2:]] == ["handover", "handover-accepted"]
    assert es[-1]["prev_entry_sha256"] == head and es[-1]["accepted_head"] == head
    assert es[-1]["record_code_commit"] == "c" * 40
    f = fence.load(paths.record_dir(s.tree))
    assert f is not None and (f.writer, f.role, f.epoch) == ("server", "writer", 2)
    assert (tmp_path / "etc/record_mode").read_text().strip() == "writer" and not s.shadow.exists()
    assert (
        s.tree / "shadow_kept" / "LEDGER.jsonl"
    ).is_file()  # the shadow's own ledger is kept aside
    # the record went out and its head is the shipped one; the next daily job may start
    assert (tmp_path / "relay/state/shipped_head").read_text().strip() == es[-1]["entry_sha256"]
    assert s.run(
        "rec_tool gate daily --shipped $RELAY/state/shipped_head --free-gb 40"
    ).stdout.startswith("ok")
    # a second cut-over is impossible
    assert "not on" in s.run("rec_cutover", stdin="yes\n", today=CUT).stdout


def test_BF_D93_cutover_refusals_change_nothing(tmp_path: Path) -> None:
    s = Server(tmp_path)
    _ready_for_cutover(s, days=4)
    r = s.run("rec_cutover", stdin="yes\n", today=CUT)
    assert (
        "Only 4 trading day(s) in a row" in r.stdout and s.shadow.is_dir() and not s.tree.exists()
    )
    (tmp_path / "b").mkdir()
    s2 = Server(tmp_path / "b")
    _ready_for_cutover(s2)
    # the shadow's state differs from the cloud's final one
    (s2.shadow / paths.REL_STATE / "state.json").write_text('{"nav": 1}')
    r = s2.run("rec_cutover", stdin="yes\n", today=CUT)
    assert "differ from the cloud's final ones" in r.stdout and "DIFFERENT" in r.stdout
    assert not s2.tree.exists() and len(L.read(paths.ledger(s2.shadow))) == 4
    (tmp_path / "c").mkdir()
    s3 = Server(tmp_path / "c")
    _ready_for_cutover(s3)
    # what was fetched is not a handover to this server (the cloud cancelled it)
    fence.cancel(paths.record_dir(s3.mirror), "cloud", "2026-12-19")
    r = s3.run("rec_cutover", stdin="yes\n", today=CUT)
    assert "not a handover to this server" in r.stdout and not s3.tree.exists()
    (tmp_path / "d").mkdir()
    s4 = Server(tmp_path / "d")
    _ready_for_cutover(s4)
    # review 5: the cloud ran its last day on other record code than this server has
    (s4.mirror / paths.REL_CODE / "paper_daily.py").write_text("# another version\n")
    r = s4.run("rec_cutover", stdin="yes\n", today=CUT)
    assert "code differs: bigwins_forward/code/paper_daily.py" in r.stdout and not s4.tree.exists()


def test_BF_D93_handback_and_research_requests(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("writer")
    rec = S.make_tree(s.tree, writer="server", epoch=2)
    inbox = tmp_path / "remote" / "Big Wins relay" / "inbox" / "ledger_requests"
    inbox.mkdir(parents=True)
    (inbox / "20270105-001-trials.json").write_text(json.dumps({
        "schema": 1, "id": "20270105-001-trials", "kind": "trials",
        "fields": {"asof": "2027-01-05", "event": "made-up study", "n_trials": 9}}))  # fmt: skip
    # D6: a request is appended only after the owner's yes (read from the terminal; here: listed)
    listed = s.run('rec_pull >/dev/null; rec_tool requests "$RELAY/inbox/validated" "$RELAY/done"')
    assert "20270105-001-trials [trials] made-up study; n_trials 9" in listed.stdout
    assert len(L.read(rec / "LEDGER.jsonl")) == 3  # nothing appended by listing
    st = json.loads(s.run("rec_host_status").stdout)
    assert (
        st["mode"] == "writer"
        and st["requests_waiting"] == 1
        and st["status"]["writer"] == "server"
    )
    ok = s.run(
        'rec_tool_u requests "$RELAY/inbox/validated" "$RELAY/done" --apply 20270105-001-trials'
    )
    assert ok.stdout.startswith("appended seq 4")
    assert json.loads(s.run("rec_host_status").stdout)["requests_waiting"] == 0
    # hand-back: one chained entry, 12 characters, the fence names the cloud, the server stops
    r = s.run("rec_handback", stdin="y\n")
    last = L.read(rec / "LEDGER.jsonl")[-1]
    assert last["kind"] == "handover" and last["to"] == "cloud" and last["epoch"] == 3
    assert f"first 12 characters:   {last['entry_sha256'][:12]}" in r.stdout
    assert "writer fence" in s.run("rec_run_job daily").stdout and not s.calls("docker run")
    assert "the last entry is 'handover'" not in r.stdout


# ---------------------------------------------------------------- backups, view, install
def test_BF_D93_backup_sources_and_pdf_days(tmp_path: Path) -> None:
    s = Server(tmp_path)
    assert s.run("rec_backup_sources").stdout == ""  # nothing while the record is not here
    s.mode("writer")
    S.make_tree(s.tree, writer="server")
    S.raw_inputs(s.tree, "2026-12-21")
    src = dict(line.split("|") for line in s.run("rec_backup_sources").stdout.splitlines())
    assert src["record_bigwins_forward_out"] == f"{s.tree}/bigwins_forward/out"
    assert src["record_bigwins_forward_data_bulk"] == f"{s.tree}/bigwins_forward/data/bulk"
    assert not any(
        "eodhd" in k or "asx_notices" in k for k in src
    )  # big stores and PDFs travel apart
    d = S.archive_day(
        tmp_path, "2026-12-18"
    )  # under tmp/bigwins_forward/data: move it to the info dir
    shutil.move(str(d.parent), str(tmp_path / "info" / "asx_notices"))
    (tmp_path / "backup.key").write_text("AGE-SECRET-KEY-MADEUP")
    light = s.run(f'rec_info_light "{tmp_path}/light"').stdout.strip()
    assert (
        light
        and not list(Path(light).rglob("*.pdf"))
        and (Path(light) / "asx_notices/2026-12-18/pdf.sha256").is_file()
    )
    out = s.run("rec_backup_pdfs", today="2026-12-21").stdout
    sent = tmp_path / "remote" / "Big Wins server backups" / "pdf" / "asxpdf-2026-12-18.tar.age"
    assert "2026-12-18 sent" in out and sent.is_file(), out
    assert any(c.startswith("age -r age1madeuprecipient") for c in s.calls("age"))
    ev = s.events()[-1]
    assert ev["job"] == "pdf-backup" and ev["ok"] is True
    # the day is uploaded once; an old day is removed off-site (kept on the server)
    assert "sent" not in s.run("rec_backup_pdfs", today="2026-12-22").stdout
    assert (
        "removed off-site" in s.run("rec_backup_pdfs", today="2027-03-01").stdout
        and not sent.exists()
    )
    # a failure is not swallowed: it goes to Health and the alarm
    (tmp_path / "age_rc").write_text("1")
    bad = s.run("rec_backup_pdfs", today="2026-12-21")
    assert "2026-12-18 FAILED" in bad.stdout and bad.returncode == 1
    assert (
        s.events()[-1]["ok"] is False
        and "could not be encrypted or sent" in s.events()[-1]["error"]
    )
    (tmp_path / "age_rc").write_text("0")
    sh = SH.read_text()
    assert (
        'rec_info_light "$stage/info_light"' in sh
        and "REC_SOURCES" in sh
        and "rec_backup_pdfs" in sh
    )
    assert "rec_backup_set stores" in sh  # weekly, only when the store changed


def test_BF_D94_view_copy_and_the_demo_app_mounts(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("view")
    S.make_tree(s.mirror, writer="cloud")
    S.book_day(s.mirror, "2026-12-14", 10100.0)
    (paths.record_dir(s.mirror) / "paper" / "holdings_latest.csv").write_text(
        "asof,book,code\n2026-12-14,T,AAA\n"
    )
    (s.mirror / paths.REL_OUT / "movers").mkdir(parents=True)
    (s.mirror / paths.REL_OUT / "movers" / "movers_2026-12-14.md").write_text("# made-up movers\n")
    assert s.run("rec_view_refresh").returncode == 0
    view = tmp_path / "view"
    meta = json.loads((view / "source.json").read_text())
    assert (
        meta["source"].startswith("the research environment (nightly copy")
        and meta["asof"] == "2026-12-14"
    )
    assert (view / "paper" / "scorecard_latest.csv").is_file() and (
        view / "movers" / "movers_2026-12-14.md"
    ).is_file()
    assert not list(view.rglob("LEDGER.jsonl")) and not list(
        view.rglob("WRITER.json")
    )  # display files only
    assert not list(view.rglob("state.json")) and not list(view.rglob("*.gz"))
    S.book_day(s.mirror, "2026-12-15", 10200.0)
    (paths.record_dir(s.mirror) / "paper" / "holdings_latest.csv").write_text(
        "asof,book,code\n2026-12-15,T,AAA\n"
    )
    s.run("rec_view_refresh")
    assert (
        "2026-12-14" in (view / "paper" / "holdings_prev.csv").read_text()
    )  # yesterday's closes kept
    s.run("rec_view_refresh")
    assert (
        "2026-12-14" in (view / "paper" / "holdings_prev.csv").read_text()
    )  # and carried on a re-run
    # the demo app (before the trader starts) mounts the real record copy and the relay, read-only
    r = s.run("demo_start")
    run = next(c for c in s.calls("docker run"))
    assert (
        f"-v {view}:/data/recordview:ro" in run and "/relay/inbox/validated:/data/relay:ro" in run
    ), r.stderr
    on = s.run("rec_set_mode off; rec_view on")
    assert (
        "now shows the paper record" in on.stdout
        and (tmp_path / "etc/record_mode").read_text().strip() == "view"
    )


def test_BF_D93_install_files_are_consistent() -> None:
    assert (
        subprocess.run(["bash", "-n", str(REPO / "deploy/record.sh")], check=False).returncode == 0
    )
    assert subprocess.run(["bash", "-n", str(SH)], check=False).returncode == 0
    df = (REPO / "deploy/record.Dockerfile").read_text()
    env = json.loads((REPO / "record/ENVIRONMENT.json").read_text())
    assert (
        f"(3, {env['versions']['python'].split('.')[1]}, {env['versions']['python'].split('.')[2]})"
        in df
    )
    assert (
        f"version {env['poppler']}" in df and "--require-hashes --no-deps --only-binary :all:" in df
    )
    assert "USER 10002:10002" in df and "docker.sock" not in df
    req = (REPO / "deploy/record_requirements.txt").read_text()
    for name in ("pandas", "numpy", "scipy", "requests", "exchange_calendars"):
        assert f"{name}=={env['versions'][name]} \\" in req, name
    pins = [ln for ln in req.splitlines() if "==" in ln]
    assert len(pins) >= 20 and req.count("--hash=sha256:") >= len(
        pins
    )  # every wheel pinned by hash
    boot = (REPO / "deploy/server_bootstrap.sh").read_text()
    assert "useradd --system --uid 10002" in boot and "/srv/bwrecord_shadow" in boot
    assert "healthchecks_record_url" in SH.read_text().split("TYPED_SECRETS=")[1].split("\n")[0]
    from trader.secrets import KNOWN_SECRETS

    assert "healthchecks_record_url" in KNOWN_SECRETS
    assert (
        f"REC_CLOUD={paths.CLOUD_ROOT}" in REC
    )  # the mount point is the path the frozen files name
    assert "record)" in SH.read_text() and "record_daily)" in SH.read_text()
    # the worker never passes a secret's value: the token is a read-only file mount
    assert 'cat "$SECRETS/eodhd_api_token"' not in REC and "-e EODHD" not in REC


# ---------------------------------------------------------------- review fixes (27 Nov 2026)
def test_BF_D93_host_tools_never_run_as_root(tmp_path: Path) -> None:
    """Review 1: every record tool call on the host goes through the record's user; root
    writes the timers from deploy code and calls one tool itself (the backup's PDF-free copy)."""
    src = REC.replace("\\\n", " ")  # join continued lines
    lines = [ln for ln in src.splitlines()
             if 'python3 -I "$REC_TOOLS"' in ln and not ln.lstrip().startswith("#")]  # fmt: skip
    direct = [ln for ln in lines if "rec_as" not in ln]
    assert len(lines) == 4 and len(direct) == 1 and "stage-light" in direct[0], direct
    assert 'python3 -I "$REC_UNITS" write' in REC and "units-sum" not in REC
    s = Server(tmp_path)
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    s.run("rec_export; rec_run_job intraday; rec_host_status; rec_status")
    tools = [c for c in s.calls("setpriv") if "bwrec.py" in c]
    assert len(tools) >= 6 and all("--reuid=10002 --regid=10002 --clear-groups" in c for c in tools)
    for cmd in ("gate intraday", "job intraday", "export", "status", "disk"):
        assert any(f"bwrec.py {cmd}" in c for c in tools), cmd


def test_BF_D93_trader_input_is_read_only_in_every_record_container(tmp_path: Path) -> None:
    """Review 2: the trader reads CORPORATE_ACTIONS.csv from the record folder; no record job
    (and so no record-class update) can change it. It changes only by an owner-confirmed request."""
    s = Server(tmp_path)
    s.mode("writer")
    rec = S.make_tree(s.tree, writer="server", epoch=2)
    (rec / "CORPORATE_ACTIONS.csv").write_text("code,ex_date,kind\n")
    s.run("rec_export")
    for job in ("daily", "intraday", "archive", "newsc-prepare"):
        s.log.unlink(missing_ok=True)
        s.run(f"rec_run_job {job}")
        run = next(c for c in s.calls("docker run"))
        want = f"-v {rec}/CORPORATE_ACTIONS.csv:{paths.CLOUD_ROOT}/{paths.REL_RECORD}/CORPORATE_ACTIONS.csv:ro"
        assert want in run, job
        s.run("rec_export")
    assert "CORPORATE_ACTIONS.csv" in (REPO / "config/bfast.yaml").read_text()  # the trader's input


def test_BF_D93_in_hours_jobs_are_small_and_builds_wait_for_the_close(tmp_path: Path) -> None:
    """Review 4: a 3.9 GB server with IB Gateway at 1.5 GB: nothing heavy while the ASX is open."""
    s = Server(tmp_path)
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    s.run("rec_export")
    open_ = "market_open() { return 0; }; "
    s.log.unlink()
    s.run(open_ + "rec_run_job intraday")
    run = next(c for c in s.calls("docker run"))
    assert (
        "--memory 600m --memory-swap 1200m" in run
        and "--cpus 0.5" in run
        and "--cpu-shares 256" in run
    )
    # even a heavy job started by hand in hours, and whatever the owner's override says
    (tmp_path / "etc" / "record_memory_mb").write_text("2000")
    assert s.run(open_ + "rec_mem 1500").stdout.strip() == "600"
    assert s.run("rec_mem 1500").stdout.strip() == "2000"  # evening: the override, at most 2000
    assert s.run("rec_mem 600").stdout.strip() == "600"  # small jobs are never raised
    (tmp_path / "etc" / "record_memory_mb").write_text("3000")
    assert s.run("rec_mem 1500").stdout.strip() == "1500"
    s.log.unlink()
    s.run("rec_run_job daily")  # evening
    run = next(c for c in s.calls("docker run"))
    assert "--memory 1500m" in run and "--cpus 1.0" in run and "--oom-score-adj 500" in run
    # a record update approved in hours ("do it anyway"): the image build waits for the close
    (tmp_path / "state" / "update_kind").write_text("record\n")
    s.log.unlink()
    r = s.run(open_ + "after_update")
    assert "rebuilt after the ASX close" in r.stdout and not any(
        "build" in c for c in s.calls("docker")
    )
    assert (tmp_path / "state" / "record" / "build_pending").is_file()
    s.run(open_ + "rec_run_job intraday")  # in hours: the old image keeps running
    assert not any(" build " in c for c in s.calls("docker"))
    s.run("rec_run_job archive")  # the first job after the close builds it
    assert any("build" in c and "record.Dockerfile" in c for c in s.calls("docker"))
    assert not (tmp_path / "state" / "record" / "build_pending").exists()
    compose = (REPO / "deploy/docker-compose.yml").read_text()
    assert compose.count("mem_reservation:") == 2 and compose.count("oom_score_adj: -500") == 2


def test_BF_D93_a_restored_older_record_never_overwrites_the_newer_one(tmp_path: Path) -> None:
    """Review (critical): restore brings back an older ledger and fence at the same epoch.
    It must not be exported over the newer ledger in OneDrive, must not set the shipped
    head, and no ledger job may book on top of it."""
    s = Server(tmp_path)
    s.mode("writer")
    rec = S.make_tree(s.tree, writer="server", epoch=2)
    S.book_day(s.tree, "2026-12-21")
    assert (
        s.run("rec_export 2026-12-21").returncode == 0
    )  # the first export: nothing in OneDrive yet
    backup = tmp_path / "backup"
    shutil.copytree(s.tree, backup)  # last night's backup
    S.book_day(s.tree, "2026-12-22")
    assert s.run("rec_export 2026-12-22").returncode == 0
    remote = tmp_path / "remote" / "Big Wins relay" / "outbox" / "record" / "LEDGER.jsonl"
    newer = remote.read_bytes()
    assert len(L.parse(newer.decode())) == 5
    # --- the server is restored from the backup; cmd_restore puts the record on hold
    shutil.rmtree(s.tree)
    shutil.copytree(backup, s.tree)
    sh = SH.read_text()
    assert (
        'rm -f "$RELAY/state/shipped_head"' in sh
        and '> "$REC_HOLD"' in sh
        and "record reconcile" in sh
    )
    (tmp_path / "relay" / "state" / "shipped_head").unlink()
    (tmp_path / "relay" / "state" / "HOLD").write_text("restored from a backup\n")
    r = s.run("rec_run_job daily")
    assert r.returncode == 1 and "on hold" in r.stdout and not s.calls("docker run")
    assert s.run("rec_export 2026-12-23").returncode == 1
    assert (
        remote.read_bytes() == newer
        and not (tmp_path / "relay" / "state" / "shipped_head").exists()
    )
    assert s.run("rec_run_job archive").returncode == 0  # collecting the announcements goes on
    # --- even WITHOUT the hold file (a copy made by hand): the export itself notices
    (tmp_path / "relay" / "state" / "HOLD").unlink()
    r = s.run("rec_export 2026-12-23")
    assert r.returncode == 1 and remote.read_bytes() == newer
    assert (tmp_path / "relay" / "state" / "HOLD").is_file()  # and puts the record on hold
    assert not (tmp_path / "relay" / "state" / "shipped_head").exists()
    hold = [e for e in s.events() if e["kind"] == "hold"]
    assert len(hold) == 1 and "AHEAD" in hold[0]["reason"]
    st = json.loads(s.run("rec_host_status").stdout)
    assert "not the start of this server's ledger" in st["hold"]
    assert len(L.read(rec / "LEDGER.jsonl")) == 4  # nothing was booked on the old head
    # --- reconcile refuses while the server is behind ...
    r = s.run("rec_reconcile")
    assert (
        r.returncode == 1
        and "NOT reconciled" in r.stdout
        and (tmp_path / "relay/state/HOLD").is_file()
    )
    # ... and releases once the server holds the newer record again (put back by the engineer)
    remote_state = tmp_path / "remote" / "Big Wins relay" / "outbox" / "state"
    (rec / "LEDGER.jsonl").write_bytes(newer)
    shutil.copytree(remote_state, s.tree / paths.REL_STATE, dirs_exist_ok=True)
    r = s.run("rec_reconcile")
    assert r.returncode == 0 and "Hold released" in r.stdout, r.stdout + r.stderr
    assert not (tmp_path / "relay" / "state" / "HOLD").exists()
    assert (tmp_path / "relay/state/shipped_head").read_text().strip() == L.head(
        rec / "LEDGER.jsonl"
    )
    assert (
        s.run(
            "rec_tool gate daily --shipped $RELAY/state/shipped_head --hold $REC_HOLD --free-gb 40"
        ).returncode
        == 0
    )


def test_BF_D93_export_sends_the_head_last(tmp_path: Path) -> None:
    s = Server(tmp_path)
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    assert s.run("rec_export").returncode == 0
    sends = [
        c for c in s.calls("rclone copy") if "/relay/outbox" in c and "Big Wins relay/outbox" in c
    ]
    assert (
        len(sends) == 2
        and "--exclude head.json" in sends[0]
        and sends[1].startswith("rclone copyto")
    )
    assert sends[1].split()[2].endswith("/outbox/head.json")
    # the parallel run's export never touches the record's own folder or the shipped head
    (tmp_path / "b").mkdir()
    s2 = Server(tmp_path / "b")
    s2.mode("shadow")
    S.make_tree(s2.shadow, writer="server", role="shadow")
    assert s2.run("rec_export").returncode == 0
    relay = tmp_path / "b" / "remote" / "Big Wins relay" / "outbox"
    assert (relay / "shadow" / "record" / "LEDGER.jsonl").is_file() and not (
        relay / "record"
    ).exists()
    assert not (tmp_path / "b" / "relay" / "state" / "shipped_head").exists()


def test_BF_D93_after_a_handback_the_server_still_collects_the_announcements(
    tmp_path: Path,
) -> None:
    """Review 3: handing the record back must not stop the archive (a missed ASX day is lost)."""
    s = Server(tmp_path)
    s.mode("writer")
    rec = S.make_tree(s.tree, writer="server", epoch=2)
    s.run("rec_export")
    out_dir = tmp_path / "relay" / "outbox" / "bundles"
    out_dir.mkdir(parents=True)
    today = subprocess.run(["date", "+%F"], capture_output=True, text=True, check=True,
                           env={"TZ": "Australia/Sydney"}).stdout.strip()  # fmt: skip
    (out_dir / f"bundle_{today}.tar").write_bytes(b"the evening's bundle")
    r = s.run("rec_handback", stdin="y\n")
    assert "first 12 characters" in r.stdout, r.stdout + r.stderr
    assert (tmp_path / "etc" / "record_mode").read_text().strip() == "archive"
    # the evening's bundle is not replaced: the hand-back writes its own
    assert (out_dir / f"bundle_{today}.tar").read_bytes() == b"the evening's bundle"
    assert (out_dir / f"bundle_{today}_handback.tar").is_file()
    assert L.read(rec / "LEDGER.jsonl")[-1]["kind"] == "handover"
    s.log.unlink()
    r = s.run("rec_chain morning")  # the next morning
    assert r.returncode == 0, r.stdout + r.stderr
    runs = s.calls("docker run")
    assert len(runs) == 1 and "run-job archive" in runs[0] and f"-v {s.tree}:" in runs[0]
    assert (
        "asx_notices " in runs[0] and f"{tmp_path}/info/asx_notices" in runs[0]
    )  # the live archive
    assert not any("Big Wins relay/outbox" in c for c in s.calls("rclone copy"))  # nothing exported
    for chain in ("daily", "intraday", "newsc", "collect", "multi"):
        assert "handed back" in s.run(f"rec_chain {chain}").stdout
    assert (
        len(s.calls("docker run")) == 1 and L.read(rec / "LEDGER.jsonl")[-1]["kind"] == "handover"
    )
    assert "writer fence" in s.run("rec_run_job daily").stdout  # a ledger job is still refused
    assert json.loads(s.run("rec_host_status").stdout)["mode"] == "archive"
    # the older host collector still stands down: one collector per server
    assert "paper record's own job" in s.run("info_enabled() { return 0; }; do_info_archive").stdout


def test_BF_D93_newsc_sends_the_ratings_before_the_drops_job_starts(tmp_path: Path) -> None:
    """Review 6: two ledger jobs in one chain: the first one's entry is shipped in between."""
    s = Server(tmp_path)
    s.mode("writer")
    S.make_tree(s.tree, writer="server", epoch=2)
    s.run("rec_export")
    day = "2026-12-14"
    inbox = tmp_path / "relay" / "inbox" / "validated" / "newsc" / day
    inbox.mkdir(parents=True)
    (inbox / "meta.json").write_text('{"model": "m", "model_source": "s"}')
    s.log.unlink()
    r = s.run(
        'date() { if [ "$1" = +%H%M ]; then echo 0850; else command date "$@"; fi; }; rec_newsc ""'
    )
    assert r.returncode == 0, r.stdout + r.stderr
    seq = [
        ("job", c.split("run-job ")[1].split()[0]) for c in s.calls() if c.startswith("docker run")
    ]
    order = [x for x in s.calls() if x.startswith("docker run") or "outbox/head.json" in x]
    kinds = ["job" if x.startswith("docker run") else "export" for x in order]
    assert [j for _, j in seq] == ["newsc-record", "newsc-drops-record"] and kinds == [
        "job",
        "export",
        "job",
        "export",
    ]
