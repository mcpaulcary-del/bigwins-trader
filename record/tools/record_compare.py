"""The parallel-run comparison (BF-D93; plan section 3.2): did the server's shadow
reproduce the cloud's day, byte for byte? Runs on the server at 21:30 Sydney on each
trading day of the parallel week; the cloud is the only writer during it.

Inputs: the cloud's manifest of the day (``sync_bundle.cloud_manifest``: content hashes
of its states, record outputs, archive and NEWS-C input files, and the ledger entries its
jobs appended; no data) and the shadow tree on this server.

| Class | What | Rule |
|---|---|---|
| A | engine states ``out/paper_state/**``, ``out/multi/**`` | hashes equal, no file on one side only |
| B | record outputs ``68_forward_record/paper/**`` (and ``multi/**`` in the rehearsal) | the same |
| C | the ledger entries the day's jobs appended | canonical JSON without the chain keys equal; none unpaired |
| D | archive and NEWS-C inputs | ``list.csv`` equal; PDF / text / batch hash sets equal; ``DONE``, ``DONE_PS`` on both; ASIC on decompressed bytes |
| E | fetch times, intraday files, things only one side produces | reported, never a pass or fail |

A ``.gz`` file is always compared on its decompressed bytes (``hashing.sha_content``).
PASS needs A, B, C and D fully identical, the record CODE identical on both machines (the
cloud's code hashes travel in its manifest), a ``daily`` entry booked by the cloud for the
day, and an archive day compared: a day on which nothing happened never counts. Nothing is waived here: a known, written
exception goes into ``record/COMPARE_ALLOW.json`` (frozen before the parallel week; an
addition after that is itself reported as a finding).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from record.tools import hashing, paths
from record.tools import ledgerlib as L

A_DIRS = (paths.REL_STATE + "/", paths.REL_MULTI_STATE + "/")
B_DIRS = (paths.REL_RECORD + "/paper/",)
B_MULTI = (paths.REL_RECORD + "/multi/",)
NOTICES = paths.REL_DATA + "/asx_notices/"
NEWSC = paths.REL_DATA + "/newsc/"
ASIC = paths.REL_DATA + "/asic_short/"
# class E by name: written by jobs the replay does not run (they need their own
# downloads), or carrying fetch times
INFO_NAMES = ("INTRADAY.md", "alerts.md", "alerts_latest.md", "NEWLIST.md", "US_FORWARD.md",
              "us_forward_latest.csv", "ps_state.json")  # fmt: skip
# cloud-only by design in the parallel week: the cloud records the ratings, the shadow dry-runs
NEWSC_CLOUD_ONLY = re.compile(r"/(incoming|drops_incoming|rater|rejected)/|/(ratings|codeday|drops_labels)\.jsonl$"
                              r"|/RELAY_[A-Z_]+$")  # fmt: skip
CHAIN_KEYS = ("seq", "prev_entry_sha256", "entry_sha256", "recorded_utc")
# further keys that cannot match between a real entry and a replay / dry run
DROP_BY_KIND: dict[str, tuple[str, ...]] = {
    "multi": ("api_credits",),  # the replay spends none
    "info_news": ("recorded_sydney",), "info_drops": ("recorded_sydney",),  # wall-clock stamps
}  # fmt: skip
HAND_KINDS = ("trials", "amendment", "code", "decision", "data", "registration", "note",
              "handover", "writer-takeover", "paper account opened")  # fmt: skip
ALLOW_FILE = Path(__file__).resolve().parent.parent / "COMPARE_ALLOW.json"


def job_entry(e: Mapping[str, Any]) -> bool:
    """An entry a scheduled job appended (not a hand-written research entry)."""
    k = str(e.get("kind", ""))
    return not k.startswith(HAND_KINDS) and not e.get("standby")


def canonical(e: Mapping[str, Any]) -> str:
    kind = str(e.get("kind", ""))
    drop = {*CHAIN_KEYS, "standby", "request_id"}
    for k, extra in DROP_BY_KIND.items():
        if kind == k or kind.startswith(k):
            drop.update(extra)
    return json.dumps({k: v for k, v in e.items() if k not in drop}, sort_keys=True)


def entry_key(e: Mapping[str, Any]) -> str:
    return f"{e.get('kind')}|{e.get('asof')}|{e.get('block') or e.get('line') or ''}"


def day_entries(entries: Iterable[Mapping[str, Any]], day: str) -> list[Mapping[str, Any]]:
    return [e for e in entries if e.get("asof") == day and job_entry(e)]


@dataclass
class ClassResult:
    name: str
    same: int = 0
    total: int = 0
    diffs: list[dict[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.diffs

    def add(self, key: str, cloud: str | None, server: str | None) -> None:
        self.total += 1
        if cloud == server and cloud is not None:
            self.same += 1
        else:
            self.diffs.append(
                {"path": key, "cloud": cloud or "missing", "server": server or "missing"}
            )

    def record(self) -> dict[str, Any]:
        return {"same": self.same, "total": self.total, "ok": self.ok, "diffs": self.diffs[:40]}


def _pick(m: Mapping[str, str], prefixes: Sequence[str]) -> dict[str, str]:
    return {k: v for k, v in m.items() if k.startswith(tuple(prefixes))}


def _is_info(path: str) -> bool:
    return path.rsplit("/", 1)[-1] in INFO_NAMES


def load_allow(path: Path = ALLOW_FILE) -> tuple[str, ...]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return tuple(str(x) for x in raw.get("informational", []))
    except (OSError, ValueError, AttributeError):
        return ()


def compare_files(name: str, cloud: Mapping[str, str], server: Mapping[str, str],
                  prefixes: Sequence[str], info: ClassResult,
                  allow: Sequence[str] = ()) -> ClassResult:  # fmt: skip
    res = ClassResult(name)
    c, s = _pick(cloud, prefixes), _pick(server, prefixes)
    for k in sorted(set(c) | set(s)):
        if _is_info(k) or k in allow:
            info.add(k, c.get(k), s.get(k))
        else:
            res.add(k, c.get(k), s.get(k))
    return res


def compare_ledger(cloud: Sequence[Mapping[str, Any]], server: Sequence[Mapping[str, Any]],
                   day: str) -> ClassResult:  # fmt: skip
    """Class C: the job entries of ``day`` on each side as multisets of canonical JSON."""
    res = ClassResult("C")
    cc = Counter(canonical(e) for e in day_entries(cloud, day))
    sc = Counter(canonical(e) for e in day_entries(server, day))
    keys = {
        canonical(e): entry_key(e) for e in [*day_entries(cloud, day), *day_entries(server, day)]
    }
    for blob in sorted(set(cc) | set(sc), key=lambda b: keys[b]):
        n_c, n_s = cc.get(blob, 0), sc.get(blob, 0)
        h = L.sha_bytes(blob.encode())[:16]
        for _ in range(min(n_c, n_s)):
            res.add(keys[blob], h, h)
        for _ in range(n_c - min(n_c, n_s)):
            res.add(keys[blob], h, None)
        for _ in range(n_s - min(n_c, n_s)):
            res.add(keys[blob], None, h)
    return res


def compare_archive(cloud: Mapping[str, str], server: Mapping[str, str], days: Sequence[str],
                    info: ClassResult, asic_days: int = 10, today: dt.date | None = None) -> ClassResult:  # fmt: skip
    res = ClassResult("D")
    for d in days:
        pre = [f"{NOTICES}{d}/", f"{NEWSC}{d}/"]
        c, s = _pick(cloud, pre), _pick(server, pre)
        for k in sorted(set(c) | set(s)):
            if NEWSC_CLOUD_ONLY.search(k) or _is_info(k):
                info.add(k, c.get(k), s.get(k))
            elif k.endswith(
                ("/DONE", "/DONE_PS")
            ):  # markers carry counts and a time: presence only
                res.add(k, "present" if k in c else None, "present" if k in s else None)
            else:
                res.add(k, c.get(k), s.get(k))
        for marker in ("DONE", "DONE_PS"):
            k = f"{NOTICES}{d}/{marker}"
            if k not in c and k not in s:
                res.add(k, None, None)
    # ASIC: the recent files, by decompressed content (older history is seeded, not compared)
    c, s = _pick(cloud, [ASIC]), _pick(server, [ASIC])
    cut = ((today or dt.date.today()) - dt.timedelta(days=asic_days)).strftime("%Y%m%d")  # noqa: DTZ011
    for k in sorted(set(c) | set(s)):
        m = re.search(r"/RR(\d{8})-", k)
        if m and m.group(1) >= cut:
            res.add(k, c.get(k), s.get(k))
    return res


def compare(cloud_manifest: Mapping[str, Any], server_files: Mapping[str, str],
            server_entries: Sequence[Mapping[str, Any]], day: str, multi: bool = False,
            allow: Sequence[str] = (), today: dt.date | None = None,
            server_code_files: Mapping[str, str] | None = None) -> dict[str, Any]:  # fmt: skip
    cf: Mapping[str, str] = cloud_manifest.get("files") or {}
    info = ClassResult("E")
    a = compare_files("A", cf, server_files, A_DIRS, info, allow)
    b = compare_files("B", cf, server_files, (*B_DIRS, *(B_MULTI if multi else ())), info, allow)
    c = compare_ledger(cloud_manifest.get("ledger_entries") or [], server_entries, day)
    d = compare_archive(
        cf, server_files, cloud_manifest.get("archive_days") or [], info, today=today
    )
    # K: the code itself. Both sides check their code against their own manifest; this is
    # the only place the CLOUD's code is compared with the server's.
    k = ClassResult("K")
    cc: Mapping[str, str] = cloud_manifest.get("code") or {}
    sc = server_code_files if server_code_files is not None else server_code()
    for key in sorted(set(cc) | set(sc)):
        k.add(key, cc.get(key), sc.get(key))
    missing: list[str] = []
    if not (a.total and b.total):
        missing.append("no states or outputs to compare")
    booked = [e for e in day_entries(cloud_manifest.get("ledger_entries") or [], day)
              if e.get("kind") == "daily"]  # fmt: skip
    if not booked:
        missing.append("the cloud booked no daily entry for this day")
    if not (cloud_manifest.get("archive_days") and d.total):
        missing.append("no archive day was compared")
    if not cc:
        missing.append("the cloud manifest lists no code")
    ok = all(x.ok for x in (a, b, c, d, k)) and not missing
    why = f" ({'; '.join(missing)})" if missing else ""
    when = dt.date.fromisoformat(day)
    code = "ok" if k.ok and cc else "DIFFERS" if cc else "not compared"
    line = (f"Shadow compare {when:%-d %b}: {'PASS' if ok else 'FAIL'} (A {a.same}/{a.total}, "
            f"B {b.same}/{b.total}, C {c.same}/{c.total}, "
            f"D {'ok' if d.ok else f'{len(d.diffs)} differ'}, code {code}){why}")  # fmt: skip
    return {"day": day, "pass": ok, "line": line, "allow": list(allow), "missing": missing,
            "classes": {x.name: x.record() for x in (a, b, c, d, k, info)}}  # fmt: skip


def shadow_files(root: Path, archive_days: Sequence[str]) -> dict[str, str]:
    """Content hashes of this machine's side. On the server the announcements archive is
    kept outside the tree (``BW_INFO_DIR``: it is mounted into the container at the code's
    path); its files are listed under the same names the cloud uses."""
    rels = [paths.REL_STATE, paths.REL_MULTI_STATE, paths.REL_RECORD + "/paper",
            paths.REL_RECORD + "/multi"]  # fmt: skip
    arch = ["asic_short"]
    for d in archive_days:
        rels.append(f"{paths.REL_DATA}/newsc/{d}")
        arch.append(f"asx_notices/{d}")
    out = hashing.tree(root, rels)
    info = os.environ.get("BW_INFO_DIR", "")
    base = Path(info) if info else root / paths.REL_DATA
    out.update({f"{paths.REL_DATA}/{k}": v for k, v in hashing.tree(base, arch).items()})
    return out


REPO_RECORD = Path(__file__).resolve().parent.parent
CODE_MAP = ((paths.REL_CODE, "code"), (paths.REL_DF_CODE, "data_foundation_code"))


def server_code(only: str = "") -> dict[str, str]:
    """The record code this checkout runs (``record/code`` ...), under the names it has in
    the tree (``bigwins_forward/code/...``): what the container mounts over the tree."""
    out: dict[str, str] = {}
    for rel, top in CODE_MAP:
        if only and rel != only:
            continue
        out.update({f"{rel}/{k}": v for k, v in hashing.tree(REPO_RECORD / top, ["."]).items()})
    return out


def shadow_entries(root: Path, day: str) -> list[Mapping[str, Any]]:
    """The shadow ledger's entries plus the entries its NEWS-C dry runs would have written."""
    es: list[Mapping[str, Any]] = list(L.read(paths.ledger(root)))
    L.verify(es)  # each side's own chain must verify
    for p in sorted((root / paths.REL_OUT / "sync").glob("dryrun_*.json")):
        try:
            e = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("asof"):
            es.append(e)
    return es


def streak(results: Sequence[Mapping[str, Any]], sessions: Sequence[str]) -> int:
    """Consecutive PASS days ending at the newest session (pass criterion 1 needs five);
    a missing or failed day resets the count."""
    by = {str(r.get("day")): bool(r.get("pass")) for r in results}
    n = 0
    for d in sorted(sessions, reverse=True):
        if not by.get(d):
            break
        n += 1
    return n
