"""bwrec: the paper record's tools on the server and in the record container (BF-D93).
Standard library only. ``deploy/record.sh`` (``bigwins record ...``) calls it; nothing
here is ever given a secret on the command line.

    bwrec.py run-job <job> [--dry-run]            in the record container
    bwrec.py status|gate|export|validate|requests|accept|handover|cancel|takeover|standby
             fence-init|manifest|bundle-make|bundle-apply|compare|units|job|disk
             pdf-plan|stage-light|code-manifest          on the host (BW_ROOT = the tree)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # the folder that holds record/

from record.tools import (
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
    view,
)
from record.tools import ledgerlib as L


def _out(obj: Any) -> None:
    print(json.dumps(obj, sort_keys=True))


def _me() -> str:
    return os.environ.get("BW_RECORD_HOST", "")


def _today() -> str:
    return dt.datetime.now(steps.SYD).date().isoformat()


def status(root: Path) -> dict[str, Any]:
    rec = paths.record_dir(root)
    out: dict[str, Any] = {"present": rec.is_dir()}
    try:
        es = L.read(rec / "LEDGER.jsonl")
        out.update(head=L.verify(es), seq=len(es), chain_ok=True)
        out["last_kind"] = str(es[-1].get("kind")) if es else ""
        out["last_asof"] = str(es[-1].get("asof")) if es else ""
    except L.ChainError as e:
        out.update(chain_ok=False, error=str(e))
    try:
        f = fence.load(rec)
        if f is not None:
            out.update(writer=f.writer, role=f.role, epoch=f.epoch)
    except fence.FenceError as e:
        out["fence_error"] = str(e)
    return out


def cmd_gate(a: argparse.Namespace, root: Path) -> int:
    """May this job start? Fence, relay epoch, shipped head, disk. Prints ok / refused."""
    job = jobs.JOBS.get(a.job)
    if job is None:
        print("refused: unknown job")
        return 1
    rec = paths.record_dir(root)
    d = fence.decide_dir(rec, _me(), relay.relay_fence(Path(a.relay)) if a.relay else None)
    if not d.ok:
        print(f"refused (writer fence): {d.reason}")
        return 1
    ok, why = ops.disk_gate(a.job, a.free_gb if a.free_gb is not None else ops.free_gb(root),
                            dt.datetime.now(steps.SYD).date())  # fmt: skip
    if not ok:
        print(f"refused (disk): {why}")
        return 1
    f = fence.load(rec)
    if job.ledger and f is not None and f.role == "writer" and a.shipped:
        try:
            shipped = Path(a.shipped).read_text(encoding="utf-8").strip()
        except OSError:
            shipped = ""
        ok, why = relay.gate(L.head(rec / "LEDGER.jsonl"), shipped)
        if not ok:
            print(f"refused (ledger shipping): {why}")
            return 1
    print(f"ok: {d.reason}; disk {why}")
    return 0


def cmd_requests(a: argparse.Namespace, root: Path) -> int:
    validated, done = Path(a.validated), Path(a.done)
    good, bad = relay.pending(validated, done)
    if a.apply:
        req = next((r for r in good if r.id == a.apply), None)
        if req is None:
            print("refused: no such waiting request")
            return 1
        try:
            e = relay.apply_request(root, validated, done, req, _me())
        except (relay.RequestError, L.ChainError) as ex:
            print(f"refused: {ex}")
            return 1
        print(f"appended seq {e['seq']} {fence.short(str(e['entry_sha256']))}")
        return 0
    for r in good:
        print(r.summary())
    for name, why in bad:
        print(f"UNREADABLE {name}: {why}")
    return 0


def cmd_compare(a: argparse.Namespace, root: Path) -> int:
    try:
        man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
        res = record_compare.compare(
            man, record_compare.shadow_files(root, man.get("archive_days") or []),
            record_compare.shadow_entries(root, a.day), a.day, multi=a.multi,
            allow=record_compare.load_allow())  # fmt: skip
    except (OSError, ValueError, L.ChainError) as e:
        res = {"day": a.day, "pass": False, "classes": {},
               "line": f"Shadow compare {a.day}: FAIL (could not compare: {type(e).__name__}: {e})"[:300]}  # fmt: skip
    out = root / paths.REL_OUT / "sync" / f"compare_{a.day}.json"
    steps.write_atomic(out, (json.dumps(res, indent=1, sort_keys=True) + "\n").encode())
    print(res["line"])
    return 0 if res["pass"] else 1


def cmd_handover(a: argparse.Namespace, root: Path) -> int:
    rec = paths.record_dir(root)
    try:
        if a.cmd == "fence-init":
            if fence.load(rec) is not None and not a.force:
                print("refused: a fence already exists")
                return 1
            head = L.head(rec / "LEDGER.jsonl")
            f = fence.save(
                rec, fence.Fence(a.epoch, a.writer, a.role, "" if head == L.ZERO else head)
            )
            _out(f.record())
        elif a.cmd == "accept":
            h = fence.check_incoming(rec, _me())
            if a.check:
                print(fence.short(str(h["entry_sha256"])))
                return 0
            extra = {"host": "bigwins server"} if _me() == "server" else {}
            e = fence.accept(rec, _me(), _today(), extra)
            print(f"accepted: seq {e['seq']} head {fence.short(str(e['entry_sha256']))}")
        elif a.cmd == "handover":
            extra = json.loads(a.extra) if a.extra else {}
            e = fence.handover(rec, _me(), _today(), extra)
            print(fence.short(str(e["entry_sha256"])))
        elif a.cmd == "cancel":
            e = fence.cancel(rec, _me(), _today())
            print(f"cancelled: seq {e['seq']} head {fence.short(str(e['entry_sha256']))}")
        elif a.cmd == "takeover":
            e = fence.takeover(rec, _me(), _today(), a.reason)
            print(f"takeover: seq {e['seq']} head {fence.short(str(e['entry_sha256']))}")
        elif a.cmd == "standby":
            _out(fence.to_standby(rec, _me(), a.head).record())
    except (fence.FenceError, L.ChainError, ValueError) as e:
        print(f"refused: {e}")
        return 1
    return 0


def compare_streak(root: Path) -> int:
    """Trading days in a row, up to the newest compared day, whose compare was a PASS
    (weekdays between the first and the last result; a day without a result breaks it)."""
    res = []
    for p in sorted((root / paths.REL_OUT / "sync").glob("compare_*.json")):
        try:
            res.append(json.loads(p.read_text(encoding="utf-8")))
        except ValueError:
            continue
    days = sorted(str(r.get("day")) for r in res if r.get("day"))
    if not days:
        return 0
    a, b = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
    have = set(days)
    # a weekday without a result counts as a session unless the exchange calendar says no
    sess = [str(d) for d in steps.sessions(a, b)] if len(days) > 1 else days
    return record_compare.streak(res, [d for d in sess if d in have or d > days[0]])


SAME_AS = (paths.REL_STATE, paths.REL_MULTI_STATE, paths.REL_RECORD + "/paper")


def cmd_same_as(root: Path, other: Path) -> int:
    """Cut-over gate: this tree's states and record outputs are byte-identical to the
    other tree's (the cloud's final commit). Informational files are left out."""
    mine, theirs = hashing.tree(root, SAME_AS), hashing.tree(other, SAME_AS)
    bad = [k for k in sorted(set(mine) | set(theirs))
           if mine.get(k) != theirs.get(k) and k.rsplit("/", 1)[-1] not in record_compare.INFO_NAMES]  # fmt: skip
    for k in bad[:20]:
        print(f"differs: {k} (here {str(mine.get(k))[:12]}, there {str(theirs.get(k))[:12]})")
    if not theirs:
        print("the other tree has no states or outputs")
        return 1
    print(f"{'same' if not bad else 'DIFFERENT'}: {len(theirs)} files compared, {len(bad)} differ")
    return 1 if bad else 0


def cmd_seed_verify(root: Path, manifest: Path) -> int:
    """Every file of the cloud's seed manifest is here with the same content hash."""
    try:
        want = json.loads(manifest.read_text(encoding="utf-8"))["files"]
    except (OSError, ValueError, KeyError, TypeError):
        print("no readable seed manifest")
        return 1
    bad = 0
    for rel, h in sorted(want.items()):
        p = root / rel
        if ".." in rel.split("/") or not p.is_file() or hashing.sha_content(p) != h:
            bad += 1
            if bad <= 20:
                print(f"missing or different: {rel}")
    print(f"seed: {len(want) - bad} of {len(want)} files match")
    return 1 if bad or not want else 0


def code_manifest(repo_record: Path) -> str:
    lines = []
    for top in ("code", "data_foundation_code"):
        for p in sorted((repo_record / top).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                lines.append(f"{hashing.sha_file(p)}  {p.relative_to(repo_record).as_posix()}\n")
    return "".join(lines)


def main(argv: list[str]) -> int:  # noqa: PLR0911, PLR0912, PLR0915 - one branch a command
    ap = argparse.ArgumentParser(prog="bwrec")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run-job")
    p.add_argument("job")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    p = sub.add_parser("gate")
    p.add_argument("job")
    p.add_argument("--shipped", default="")
    p.add_argument("--relay", default="")
    p.add_argument("--free-gb", type=float, default=None)
    p = sub.add_parser("export")
    p.add_argument("outbox")
    p.add_argument("--day", default="")
    p.add_argument("--status", default="")
    p = sub.add_parser("validate")
    p.add_argument("raw")
    p.add_argument("validated")
    p.add_argument("--rejected", default="")
    p.add_argument("--keep-raw", action="store_true")
    p = sub.add_parser("requests")
    p.add_argument("validated")
    p.add_argument("done")
    p.add_argument("--apply", default="")
    p = sub.add_parser("fence-init")
    p.add_argument("--writer", required=True, choices=fence.HOSTS)
    p.add_argument("--role", required=True, choices=fence.ROLES)
    p.add_argument("--epoch", type=int, default=1)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("accept")
    p.add_argument("--check", action="store_true")
    p = sub.add_parser("handover")
    p.add_argument("--extra", default="")
    sub.add_parser("cancel")
    p = sub.add_parser("takeover")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("standby")
    p.add_argument("--head", required=True)
    p = sub.add_parser("manifest")
    p.add_argument("day")
    p.add_argument("--archive-day", action="append", default=[])
    p.add_argument("--out", default="")
    p = sub.add_parser("bundle-make")
    p.add_argument("day")
    p.add_argument("out")
    p.add_argument("--mark-only", action="store_true")
    p.add_argument("--with-panels", action="store_true")
    p = sub.add_parser("bundle-apply")
    p.add_argument("bundle")
    p = sub.add_parser("compare")
    p.add_argument("day")
    p.add_argument("manifest")
    p.add_argument("--multi", action="store_true")
    p = sub.add_parser("units")
    p.add_argument("out")
    p.add_argument("script")
    p = sub.add_parser("job")
    p.add_argument("job")
    p = sub.add_parser("newsc-pending")
    p.add_argument("inbox")
    p.add_argument("which", choices=("record", "drops"))
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("units-sum")
    p.add_argument("script")
    sub.add_parser("streak")
    p = sub.add_parser("same-as")
    p.add_argument("other")
    p = sub.add_parser("seed-verify")
    p.add_argument("manifest")
    p = sub.add_parser("seed-manifest")
    p.add_argument("out")
    p.add_argument("rels", nargs="+")
    p = sub.add_parser("disk")
    p.add_argument("path")
    p = sub.add_parser("pdf-plan")
    p.add_argument("info_dir")
    p.add_argument("remote_listing")
    p = sub.add_parser("stage-light")
    p.add_argument("src")
    p.add_argument("dst")
    p = sub.add_parser("pdf-hashes")
    p.add_argument("day_dir")
    p = sub.add_parser("view-copy")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("source")
    p.add_argument("note")
    p = sub.add_parser("code-manifest")
    p.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = paths.root()

    if a.cmd == "run-job":
        res = runner.run_job(a.job, steps.TOOLS, a.dry_run, root,
                             checks=os.environ.get("BW_SKIP_CHECKS") != "test-only")  # fmt: skip
        _out(res)
        return 0 if res["ok"] else 1
    if a.cmd == "status":
        _out(status(root))
        return 0
    if a.cmd == "gate":
        return cmd_gate(a, root)
    if a.cmd == "export":
        st = json.loads(Path(a.status).read_text(encoding="utf-8")) if a.status else None
        _out(relay.export(root, Path(a.outbox), st, a.day))
        return 0
    if a.cmd == "validate":
        _out(relay.validate(Path(a.raw), Path(a.validated),
                            Path(a.rejected) if a.rejected else None,
                            consume=not a.keep_raw).record())  # fmt: skip
        return 0
    if a.cmd == "requests":
        return cmd_requests(a, root)
    if a.cmd in ("fence-init", "accept", "handover", "cancel", "takeover", "standby"):
        return cmd_handover(a, root)
    if a.cmd == "manifest":
        m = sync_bundle.cloud_manifest(root, a.day, a.archive_day)
        out = Path(a.out) if a.out else root / paths.REL_OUT / "sync" / f"manifest_{a.day}.json"
        steps.write_atomic(out, (json.dumps(m, sort_keys=True) + "\n").encode())
        print(f"manifest {a.day}: {len(m['files'])} files, {len(m['ledger_entries'])} entries, "
              f"sha256 {hashing.manifest_sha(m['files'])}")  # fmt: skip
        return 0
    if a.cmd == "bundle-make":
        _out(sync_bundle.make(root, a.day, Path(a.out), with_panels=a.with_panels,
                              mark_only=a.mark_only))  # fmt: skip
        return 0
    if a.cmd == "bundle-apply":
        try:
            _out(sync_bundle.apply(Path(a.bundle), root))
        except sync_bundle.BundleError as e:
            print(f"refused: {e}")
            return 1
        return 0
    if a.cmd == "compare":
        return cmd_compare(a, root)
    if a.cmd == "units":
        for u in jobs.UNITS:
            svc, tmr = jobs.unit_files(u, a.script)
            (Path(a.out) / f"bigwins-{u.name}.service").write_text(svc, encoding="utf-8")
            (Path(a.out) / f"bigwins-{u.name}.timer").write_text(tmr, encoding="utf-8")
            print(f"{u.name} {','.join(u.modes)}")
        return 0
    if a.cmd == "newsc-pending":  # the day whose replies wait in the relay, or nothing
        marker = {("record", False): "RELAY_RECORDED", ("record", True): "RELAY_DRYRUN",
                  ("drops", False): "RELAY_DROPS_RECORDED", ("drops", True): "RELAY_DROPS_DRYRUN"}  # fmt: skip
        day = steps.pending_day(
            Path(a.inbox), root / paths.REL_DATA / "newsc", marker[(a.which, a.dry_run)]
        )
        print(day or "")
        return 0 if day else 1
    if a.cmd == "units-sum":
        blob = "".join("".join(jobs.unit_files(u, a.script)) + u.name for u in jobs.UNITS)
        print(L.sha_bytes(blob.encode())[:16])
        return 0
    if a.cmd == "streak":
        print(compare_streak(root))
        return 0
    if a.cmd == "same-as":
        return cmd_same_as(root, Path(a.other))
    if a.cmd == "seed-verify":
        return cmd_seed_verify(root, Path(a.manifest))
    if a.cmd == "seed-manifest":  # on the cloud: the files the seed carries, with content hashes
        files = hashing.tree(root, a.rels)
        steps.write_atomic(
            Path(a.out), (json.dumps({"schema": 1, "files": files}, sort_keys=True) + "\n").encode()
        )
        print(f"seed manifest: {len(files)} files, sha256 {hashing.manifest_sha(files)}")
        return 0
    if a.cmd == "job":
        j = jobs.JOBS.get(a.job)
        if j is None:
            return 1
        print(f"{int(j.network)} {int(j.ledger)} {int(j.eodhd)} {j.memory_mb}")
        return 0
    if a.cmd == "disk":
        g = ops.free_gb(Path(a.path))
        print(f"{ops.disk_level(g)} {g:.1f}")
        return 0
    if a.cmd == "pdf-plan":
        names = Path(a.remote_listing).read_text(encoding="utf-8").split()
        up, rm = ops.pdf_plan(ops.finished_days(Path(a.info_dir)), names,
                              dt.datetime.now(steps.SYD).date())  # fmt: skip
        for d in up:
            print(f"upload {d}")
        for n in rm:
            print(f"delete {n}")
        return 0
    if a.cmd == "stage-light":
        _out(ops.stage_light(Path(a.src), Path(a.dst)))
        return 0
    if a.cmd == "pdf-hashes":
        sys.stdout.write(ops.pdf_hashes(Path(a.day_dir)))
        return 0
    if a.cmd == "view-copy":
        res = view.view_copy(Path(a.src), Path(a.dst), a.source, a.note)
        _out(res)
        return 0 if res["ok"] else 1
    if a.cmd == "code-manifest":
        here = Path(__file__).resolve().parents[1]
        text = code_manifest(here)
        if a.check:
            same = (here / "MANIFEST.sha256").read_text(encoding="utf-8") == text
            print("ok" if same else "MANIFEST.sha256 does not match record/code")
            return 0 if same else 1
        (here / "MANIFEST.sha256").write_text(text, encoding="utf-8")
        print(f"{text.count(chr(10))} files")
        return 0
    return 2


if __name__ == "__main__":
    t0 = time.monotonic()
    sys.exit(main(sys.argv[1:]))
