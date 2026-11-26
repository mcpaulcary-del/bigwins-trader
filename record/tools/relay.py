"""The OneDrive relay (BF-D93, owner decision D1): the AI steps stay in the cloud and
exchange small files with the server through one OneDrive folder. Store and forward: the
server only makes outbound ``rclone`` calls (as the nightly backup does); nothing can
reach into it. This module is the server's (and the cloud helper's) file handling; the
copying to and from OneDrive is ``deploy/record.sh`` (rclone) on the server and the
OneDrive connector on the cloud.

Folder "Big Wins relay" (names from the server's point of view)::

    outbox/head.json                         ledger head, seq, epoch (ledger shipping)
    outbox/record/**                         the record folder (ledger, fence, paper/, multi/, amendments)
    outbox/state/**                          engine states (for the GitHub mirror and the standby)
    outbox/newsc/<D>/**                      NEWS-C batches, manifest, rubrics, drop dossier
    outbox/daily/<D>/**                      the day's numbers, gap check, movers list, status
    outbox/intraday/**                       alerts_latest.md, INTRADAY.md
    outbox/bundles/bundle_<D>.tar            the day's raw inputs (for the standby replay)
    inbox/newsc/<D>/<batch>_p[12].json, drops_p[12].json, meta.json     the raters' replies
    inbox/reports/<D>/report.json, report.md nightly report and Big movers (for the app)
    inbox/ledger_requests/<id>.json (+ AMENDMENT_*.md, CORPORATE_ACTIONS.csv)  research entries
    inbox/bundles/bundle_<D>.tar, manifest_<D>.json   Phase 1: the cloud's inputs and hashes
    inbox/fence.json                         a takeover's fence (a higher epoch stops this server)

**Nothing pulled is ever executed, unpacked here or used to build a path.** ``validate``
accepts only the fixed name patterns below, each under a size cap, JSON parsed with the
standard library, text decoded as UTF-8; everything else is left in ``rejected/`` and
reported. Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from record.tools import fence, hashing, paths
from record.tools import ledgerlib as L

DAY = r"\d{4}-\d{2}-\d{2}"
KB = 1024
# (pattern of the path under inbox/, size cap in bytes, kind)
ACCEPT: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (re.compile(rf"^newsc/{DAY}/[A-Z]{{1,3}}_\d{{2}}_p[12]\.json$"), 256 * KB, "json"),
    (re.compile(rf"^newsc/{DAY}/drops_p[12]\.json$"), 256 * KB, "json"),
    (re.compile(rf"^newsc/{DAY}/meta\.json$"), 16 * KB, "json"),
    (re.compile(rf"^reports/{DAY}/report\.json$"), 256 * KB, "json"),
    (re.compile(rf"^reports/{DAY}/report\.md$"), 256 * KB, "text"),
    (re.compile(r"^ledger_requests/[0-9]{8}-[0-9]{3}-[a-z]{1,12}\.json$"), 64 * KB, "json"),
    (re.compile(r"^ledger_requests/AMENDMENT_[A-Za-z0-9_.-]{1,80}\.(md|sha256)$"), 512 * KB, "text"),
    (re.compile(r"^ledger_requests/CORPORATE_ACTIONS\.csv$"), 512 * KB, "text"),
    (re.compile(rf"^bundles/bundle_{DAY}\.tar$"), 400 * KB * KB, "bytes"),
    (re.compile(rf"^bundles/manifest_{DAY}\.json$"), 4 * KB * KB, "json"),
    (re.compile(r"^fence\.json$"), 4 * KB, "json"),
)  # fmt: skip
REQUEST_KINDS = ("trials", "amendment", "code", "data", "note")
CHAIN_KEYS = ("seq", "prev_entry_sha256", "entry_sha256")
RESERVED_KINDS = ("handover", "handover-accepted", "handover-cancelled", "writer-takeover")
ATTACH = re.compile(r"^(AMENDMENT_[A-Za-z0-9_.-]{1,80}\.(md|sha256)|CORPORATE_ACTIONS\.csv)$")


@dataclass
class Pulled:
    accepted: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)

    def record(self) -> dict[str, Any]:
        return {
            "accepted": len(self.accepted),
            "rejected": [f"{n}: {w}" for n, w in self.rejected][:20],
        }


def classify(rel: str, size: int) -> tuple[str, str]:
    """(kind, "") of an acceptable inbox path, or ("", why not)."""
    if ".." in rel.split("/") or rel.startswith("/") or "\\" in rel or len(rel) > 200:
        return "", "bad path"
    for pat, cap, kind in ACCEPT:
        if pat.match(rel):
            return (kind, "") if size <= cap else ("", f"too large ({size} bytes)")
    return "", "not an expected file name"


def _content_ok(p: Path, kind: str) -> str:
    try:
        if kind == "json":
            json.loads(p.read_text(encoding="utf-8"))
        elif kind == "text":
            t = p.read_text(encoding="utf-8")
            if "\x00" in t:
                return "binary data in a text file"
    except (OSError, ValueError) as e:
        return f"unreadable ({type(e).__name__})"
    return ""


def validate(  # noqa: PLR0912 - one branch per reason to refuse
    raw: Path, validated: Path, rejected: Path | None = None, consume: bool = True
) -> Pulled:
    """Move (``consume``) or copy what the puller fetched (``raw``) into ``validated`` if it
    passes. On the server ``raw`` is rclone's mirror of the OneDrive inbox and is kept (so
    nothing is downloaded twice): a rejected file stays there, untouched and unused. A file
    already validated with other content is never replaced (replies and requests are
    write-once), except the fence copy and report files, which the newest version wins."""
    out = Pulled()
    for p in sorted(raw.rglob("*")) if raw.is_dir() else []:
        if p.is_dir():
            continue
        rel = p.relative_to(raw).as_posix()
        why = "a link, not a file" if p.is_symlink() or not p.is_file() else ""
        kind = ""
        if not why:
            kind, why = classify(rel, p.stat().st_size)
        if not why:
            why = _content_ok(p, kind)
        dst = validated / rel
        if not why and dst.exists():
            if hashing.sha_file(dst) == hashing.sha_file(p):
                if consume:
                    p.unlink()
                continue
            if not (rel == "fence.json" or rel.startswith(("reports/", "bundles/"))):
                why = "a different file with this name was already accepted"
        if why:
            out.rejected.append((rel, why))
            if not consume:
                continue
            if rejected is not None and not p.is_symlink():
                (rejected / rel).parent.mkdir(parents=True, exist_ok=True)
                os.replace(p, rejected / rel)
            else:
                p.unlink(missing_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if consume:
            os.replace(p, dst)
        else:
            tmp = dst.with_name(dst.name + ".part")
            shutil.copyfile(p, tmp)
            os.replace(tmp, dst)
        os.chmod(dst, 0o644)
        out.accepted.append(rel)
    return out


def relay_fence(validated: Path) -> fence.Fence | None:
    p = validated / "fence.json"
    try:
        return fence.parse(json.loads(p.read_text(encoding="utf-8"))) if p.is_file() else None
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- export (server -> cloud)
def _copy_changed(src: Path, dst: Path) -> bool:
    if dst.is_file() and dst.stat().st_size == src.stat().st_size \
            and hashing.sha_file(dst) == hashing.sha_file(src):  # fmt: skip
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".part")
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)
    return True


def _tree(src: Path, dst: Path, skip: Iterable[str] = ()) -> int:
    n = 0
    for p in sorted(src.rglob("*")) if src.is_dir() else []:
        rel = p.relative_to(src).as_posix()
        if (
            p.is_symlink()
            or not p.is_file()
            or not hashing.wanted(rel)
            or rel.endswith(tuple(skip))
        ):
            continue
        n += _copy_changed(p, dst / rel)
    return n


READABLE_SKIP = (".gz", ".pkl", ".npz", ".zip", ".parquet")  # vendor data never goes out readable


def export(root: Path, outbox: Path, status: Mapping[str, Any] | None = None,
           day: str = "", now: float | None = None) -> dict[str, Any]:  # fmt: skip
    """Stage the readable record for the cloud (changed files only) and write
    ``head.json`` LAST: a head in the outbox means everything up to it is staged."""
    rec = paths.record_dir(root)
    es = L.read(rec / "LEDGER.jsonl")
    head = L.verify(es)
    n = _tree(rec, outbox / "record", READABLE_SKIP)
    n += _tree(root / paths.REL_STATE, outbox / "state", READABLE_SKIP)
    n += _tree(root / paths.REL_MULTI_STATE, outbox / "state_multi", READABLE_SKIP)
    newsc = root / paths.REL_DATA / "newsc"
    for name in ("RUBRIC_v1.md", "DROPS_RUBRIC_v1.md"):
        if (newsc / name).is_file():
            n += _copy_changed(newsc / name, outbox / "newsc" / name)
    if (newsc / "drops_blind").is_dir():
        n += _tree(newsc / "drops_blind", outbox / "newsc" / "drops_blind")
    for d in sorted(p for p in newsc.iterdir() if p.is_dir() and re.fullmatch(DAY, p.name))[-3:] \
            if newsc.is_dir() else []:  # fmt: skip
        for sub in ("batches",):
            n += _tree(d / sub, outbox / "newsc" / d.name / sub)
        for name in ("manifest.json", "drops_manifest.json"):
            if (d / name).is_file():
                n += _copy_changed(d / name, outbox / "newsc" / d.name / name)
    if day:
        dd = outbox / "daily" / day
        for src in (root / paths.REL_OUT / "sync" / "gaps.json",
                    root / paths.REL_OUT / "movers" / f"movers_{day}.md",
                    root / paths.REL_OUT / "sync" / f"compare_{day}.json"):  # fmt: skip
            if src.is_file():
                n += _copy_changed(src, dd / src.name)
        if status is not None:
            (dd).mkdir(parents=True, exist_ok=True)
            _write(dd / "status.json", dict(status))
    f = fence.load(rec)
    info = {"head": head, "seq": len(es), "epoch": f.epoch if f else None,
            "writer": f.writer if f else None, "role": f.role if f else None,
            "exported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))}  # fmt: skip
    _write(outbox / "head.json", info)
    return {**info, "files_changed": n}


def _write(p: Path, obj: Mapping[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".part")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def gate(head: str, shipped: str, max_unshipped_jobs: int = 0) -> tuple[bool, str]:
    """Ledger shipping (plan 5): a ledger-writing job may start only when the previous
    head reached OneDrive, so at most one job's entries can ever exist only on the
    server. ``shipped`` is the head the last successful upload carried."""
    if head in (shipped, L.ZERO) or max_unshipped_jobs > 0:
        return True, "the ledger head is shipped"
    return False, ("the last ledger entries have not reached OneDrive yet (head "
                   f"{head[:12]}, shipped {shipped[:12] or 'none'}): this job waits")  # fmt: skip


# ---------------------------------------------------------------- research ledger requests (6.4)
class RequestError(ValueError):
    pass


@dataclass(frozen=True)
class Request:
    id: str
    kind: str
    fields: dict[str, Any]
    attachments: tuple[tuple[str, str], ...]  # (name, sha256)
    requested_utc: str = ""

    def summary(self) -> str:
        ev = str(self.fields.get("event", ""))[:160]
        extra = f"; n_trials {self.fields['n_trials']}" if "n_trials" in self.fields else ""
        att = f"; files: {', '.join(n for n, _ in self.attachments)}" if self.attachments else ""
        return f"{self.id} [{self.kind}] {ev}{extra}{att}"


def parse_request(name: str, raw: object) -> Request:
    if not isinstance(raw, Mapping) or raw.get("schema") != 1:
        raise RequestError("not a schema-1 request")
    rid = name.removesuffix(".json")
    kind = raw.get("kind")
    fields = raw.get("fields")
    if raw.get("id") != rid or kind not in REQUEST_KINDS or not rid.endswith("-" + str(kind)):
        raise RequestError("the id, file name and kind do not agree, or the kind is not allowed")
    if not isinstance(fields, dict) or not isinstance(fields.get("event"), str) \
            or not isinstance(fields.get("asof"), str):  # fmt: skip
        raise RequestError("fields need at least asof and event")
    if any(k in fields for k in CHAIN_KEYS) or fields.get("standby"):
        raise RequestError("a request may not set chain fields")
    fk = str(fields.get("kind", kind))
    if fk in RESERVED_KINDS or fk.split(" ")[0].rstrip("+") not in (
        *REQUEST_KINDS,
        "registration",
        "decision",
    ):
        raise RequestError(f"entry kind '{fk}' is not allowed in a request")
    att: list[tuple[str, str]] = []
    for a in raw.get("attachments") or []:
        if not isinstance(a, Mapping) or not ATTACH.match(str(a.get("name", ""))) \
                or not re.fullmatch(r"[0-9a-f]{64}", str(a.get("sha256", ""))):  # fmt: skip
            raise RequestError("bad attachment")
        att.append((str(a["name"]), str(a["sha256"])))
    if any(n == "CORPORATE_ACTIONS.csv" for n, _ in att) and kind != "data":
        raise RequestError("CORPORATE_ACTIONS.csv travels only with a data request")
    if len(json.dumps(fields)) > 32 * KB:
        raise RequestError("fields too large")
    return Request(
        rid, str(kind), {**fields, "kind": fk}, tuple(att), str(raw.get("requested_utc", ""))[:20]
    )


def pending(validated: Path, done: Path) -> tuple[list[Request], list[tuple[str, str]]]:
    """Requests waiting for the owner, oldest first, and the unreadable ones."""
    good: list[Request] = []
    bad: list[tuple[str, str]] = []
    d = validated / "ledger_requests"
    for p in sorted(d.glob("*.json")) if d.is_dir() else []:
        if (done / p.name).exists():
            continue
        try:
            good.append(parse_request(p.name, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, ValueError) as e:
            bad.append((p.name, str(e)))
    return good, bad


def apply_request(root: Path, validated: Path, done: Path, req: Request, me: str,
                  now: float | None = None) -> L.Entry:  # fmt: skip
    """Append ONE owner-confirmed request (attachments first, hashes checked; an existing
    amendment file is never changed). The entry notes that it came through the relay."""
    rec = paths.record_dir(root)
    d = fence.decide(fence.load(rec), me, relay_fence(validated))
    if not d.ok or d.standby:
        raise RequestError(f"this machine may not append: {d.reason}")
    src = validated / "ledger_requests"
    for name, sha in req.attachments:
        p = src / name
        if not p.is_file() or hashing.sha_file(p) != sha:
            raise RequestError(f"attachment {name} is missing or its hash differs")
        dst = rec / name
        if dst.exists() and name != "CORPORATE_ACTIONS.csv" and hashing.sha_file(dst) != sha:
            raise RequestError(f"{name} already exists in the record with other content")
    for name, _ in req.attachments:
        _copy_changed(src / name, rec / name)
    fields = dict(req.fields)
    fields.setdefault("source", "research request through the relay, confirmed by the owner")
    fields["request_id"] = req.id
    e = L.append(rec / "LEDGER.jsonl", fields, now)
    done.mkdir(parents=True, exist_ok=True)
    _write(
        done / f"{req.id}.json", {"id": req.id, "seq": e["seq"], "entry_sha256": e["entry_sha256"]}
    )
    return e
