"""The writer fence (BF-D93): ONE machine may append to the paper record's ledger.

``WRITER.json`` sits beside ``LEDGER.jsonl``::

    {"epoch": 2, "writer": "server", "role": "writer", "head": "<entry hash>", "set_utc": "..."}

* ``writer``: which machine may append (``cloud`` = the research environment, ``server``).
  The machine's own name comes from ``BW_RECORD_HOST``, set by whoever starts the job.
* ``role``: ``writer`` (the canonical record), ``shadow`` (the parallel week's separate
  tree: never the record, its entries are compared and thrown away) or ``standby`` (the
  old writer's copy after a handover: every entry it appends carries ``"standby": true``).
* ``epoch`` goes up by one at every handover, cancellation and takeover. A copy of the
  fence in the relay with a HIGHER epoch means somebody else took over: stop writing.
* No fence file, an unreadable one, a different writer: refuse. There is no override.

A handover is two chained entries: the old writer's ``handover`` (its last entry; it
then sets the fence to the new writer) and the new writer's ``handover-accepted``,
whose ``prev_entry_sha256`` is the handover entry. The owner compares the first 12
characters of the handover entry's hash on both machines before the second is written.
Standard library only.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from record.tools import ledgerlib as L

FENCE = "WRITER.json"
HOSTS = ("cloud", "server")
ROLES = ("writer", "shadow", "standby")


class FenceError(ValueError):
    """The fence or a handover step is not acceptable; nothing was written."""


@dataclass(frozen=True)
class Fence:
    epoch: int
    writer: str
    role: str = "writer"
    head: str = ""
    set_utc: str = ""

    def record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Decision:
    ok: bool
    reason: str
    standby: bool = False


def parse(raw: object) -> Fence:
    if not isinstance(raw, Mapping):
        raise FenceError("the fence is not a JSON object")
    epoch, writer, role = raw.get("epoch"), raw.get("writer"), raw.get("role", "writer")
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
        raise FenceError("the fence has no valid epoch")
    if writer not in HOSTS or role not in ROLES:
        raise FenceError("the fence names an unknown writer or role")
    head = raw.get("head", "")
    if not isinstance(head, str) or (head and (len(head) != 64 or not _hex(head))):
        raise FenceError("the fence's head is not an entry hash")
    return Fence(epoch, str(writer), str(role), head, str(raw.get("set_utc", ""))[:20])


def _hex(s: str) -> bool:
    return all(c in "0123456789abcdef" for c in s)


def load(record_dir: Path) -> Fence | None:
    """The fence of ``record_dir`` (None: no fence file). Raises FenceError if unreadable."""
    p = record_dir / FENCE
    if not p.exists():
        return None
    try:
        return parse(json.loads(p.read_text(encoding="utf-8")))
    except (OSError, ValueError) as e:
        raise FenceError(f"the fence cannot be read: {e}") from e


def save(record_dir: Path, f: Fence, now: float | None = None) -> Fence:
    f = Fence(f.epoch, f.writer, f.role, f.head,
              time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))  # fmt: skip
    parse(f.record())  # never write a fence this module would refuse
    tmp = record_dir / (FENCE + ".part")
    tmp.write_text(json.dumps(f.record(), sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, record_dir / FENCE)
    return f


def decide(f: Fence | None, me: str, relay: Fence | None = None) -> Decision:
    """May ``me`` append to the ledger this fence guards? Default: no."""
    if me not in HOSTS:
        return Decision(False, "this machine has no record name (BW_RECORD_HOST)")
    if f is None:
        return Decision(False, "no WRITER.json beside the ledger: nobody may append")
    if relay is not None and relay.epoch > f.epoch:
        return Decision(False, f"the relay shows a newer writer (epoch {relay.epoch}, "
                        f"{relay.writer}) than this machine's fence (epoch {f.epoch}): stopped")  # fmt: skip
    if f.writer != me:
        return Decision(False, f"the writer is {f.writer} (epoch {f.epoch}), not {me}")
    return Decision(True, f"{f.role} at epoch {f.epoch}", standby=f.role == "standby")


def decide_dir(record_dir: Path, me: str, relay: Fence | None = None) -> Decision:
    try:
        return decide(load(record_dir), me, relay)
    except FenceError as e:
        return Decision(False, str(e))


def other(host: str) -> str:
    return "server" if host == "cloud" else "cloud"


# ---------------------------------------------------------------- handover steps
def _last(es: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    if not es:
        raise FenceError("the ledger is empty")
    return es[-1]


def _chain(ledger: Path) -> list[L.Entry]:
    try:
        es = L.read(ledger)
        L.verify(es)
    except L.ChainError as e:
        raise FenceError(f"the ledger does not verify: {e}") from e
    return es


def handover(record_dir: Path, me: str, asof: str, extra: Mapping[str, Any] | None = None,
             now: float | None = None) -> L.Entry:  # fmt: skip
    """The current writer's LAST entry: hand the record to the other machine. The fence
    then names the new writer, so this machine's next append is refused."""
    f = load(record_dir)
    d = decide(f, me)
    if f is None or not d.ok or f.role != "writer":
        raise FenceError(f"only the writer hands over: {d.reason}")
    ledger = record_dir / "LEDGER.jsonl"
    _chain(ledger)
    to = other(me)
    fields: dict[str, Any] = {
        "kind": "handover", "asof": asof, "from": me, "to": to, "epoch": f.epoch + 1,
        "event": f"Writer handover: {_name(me)} stops writing; {_name(to)} becomes the only writer.",
    }  # fmt: skip
    fields.update({k: v for k, v in (extra or {}).items() if k not in fields})
    e = L.append(ledger, fields, now)
    save(record_dir, Fence(f.epoch + 1, to, "writer", str(e["entry_sha256"])), now)
    return e


def check_incoming(record_dir: Path, me: str) -> L.Entry:
    """A tree offered to ``me`` as the canonical record: the chain verifies, the last
    entry is a ``handover`` to ``me``, and the fence names ``me`` at that epoch and head.
    A shadow or standby ledger, an already-accepted or cancelled handover, all fail."""
    f = load(record_dir)
    if f is None:
        raise FenceError("no WRITER.json in the offered record")
    es = _chain(record_dir / "LEDGER.jsonl")
    last = _last(es)
    if last.get("kind") != "handover":
        raise FenceError(f"the last entry is '{last.get('kind')}', not a handover")
    if last.get("to") != me or last.get("from") != other(me):
        raise FenceError("the handover is not addressed to this machine")
    if f.writer != me or f.role != "writer" or f.epoch != last.get("epoch"):
        raise FenceError("the fence does not match the handover entry (writer, role or epoch)")
    if f.head != last.get("entry_sha256"):
        raise FenceError("the fence's head is not the handover entry")
    if any(e.get("standby") for e in es):
        raise FenceError("the offered ledger contains standby entries: not a canonical record")
    return dict(last)


def accept(record_dir: Path, me: str, asof: str, extra: Mapping[str, Any] | None = None,
           now: float | None = None) -> L.Entry:  # fmt: skip
    """The new writer's first entry, chained directly onto the handover entry."""
    h = check_incoming(record_dir, me)
    fields: dict[str, Any] = {
        "kind": "handover-accepted", "asof": asof, "from": h["from"], "epoch": h["epoch"],
        "accepted_head": h["entry_sha256"],
        "event": f"{_name(me).capitalize()} accepted the handover and is the only writer "
                 "from this entry.",
    }  # fmt: skip
    for k in ("tree_manifest_sha256", "record_code_commit"):
        if k in h:
            fields[k] = h[k]
    fields.update({k: v for k, v in (extra or {}).items() if k not in fields})
    e = L.append(record_dir / "LEDGER.jsonl", fields, now)
    save(record_dir, Fence(int(h["epoch"]), me, "writer", str(e["entry_sha256"])), now)
    return e


def cancel(record_dir: Path, me: str, asof: str, now: float | None = None) -> L.Entry:
    """The OLD writer takes the record back before the new one accepted (plan 4.4): its
    own handover is still the last entry; one more entry, a higher epoch, no fork."""
    f = load(record_dir)
    es = _chain(record_dir / "LEDGER.jsonl")
    last = _last(es)
    if f is None or last.get("kind") != "handover" or last.get("from") != me:
        raise FenceError("nothing to cancel: the last entry is not this machine's handover")
    if f.epoch != last.get("epoch") or f.head != last.get("entry_sha256"):
        raise FenceError("the fence moved on since the handover: not cancelled")
    e = L.append(record_dir / "LEDGER.jsonl", {
        "kind": "handover-cancelled", "asof": asof, "epoch": f.epoch + 1, "writer": me,
        "cancelled_head": last["entry_sha256"],
        "event": f"Handover cancelled before acceptance: {_name(me)} remains the only writer.",
    }, now)  # fmt: skip
    save(record_dir, Fence(f.epoch + 1, me, "writer", str(e["entry_sha256"])), now)
    return e


def takeover(record_dir: Path, me: str, asof: str, reason: str,
             now: float | None = None) -> L.Entry:  # fmt: skip
    """Emergency (plan 5.2): the writer is dead and POWERED OFF. Built on the last ledger
    it shipped; at most one later entry can exist on the dead machine, and it is filed as
    an orphan when the machine returns, never merged."""
    f = load(record_dir)
    if f is None:
        raise FenceError("no WRITER.json: a takeover starts from a shipped record with its fence")
    if f.writer == me and f.role == "writer":
        raise FenceError("this machine is already the writer")
    es = _chain(record_dir / "LEDGER.jsonl")
    if any(e.get("standby") for e in es):
        raise FenceError(
            "standby entries present: take over from the shipped ledger, not the standby copy"
        )
    built_on = L.verify(es)
    e = L.append(record_dir / "LEDGER.jsonl", {
        "kind": "writer-takeover", "asof": asof, "epoch": f.epoch + 1, "writer": me,
        "built_on_head": built_on, "reason": reason[:300],
        "event": f"Emergency takeover: {_name(me)} is the only writer from this entry.",
        "note": "at most one later entry may exist on the previous writer; if found it is "
                "filed as an orphan, never merged",
    }, now)  # fmt: skip
    save(record_dir, Fence(f.epoch + 1, me, "writer", str(e["entry_sha256"])), now)
    return e


def to_standby(record_dir: Path, me: str, accepted_head: str, now: float | None = None) -> Fence:
    """The old writer, once it has READ BACK the new writer's acceptance: its copy becomes
    a standby (appends allowed again, every one marked ``standby``)."""
    f = load(record_dir)
    if f is None or f.writer != other(me) or f.role != "writer":
        raise FenceError("standby is only for the machine that handed the record over")
    if len(accepted_head) != 64 or not _hex(accepted_head):
        raise FenceError("the acceptance entry's hash is needed")
    return save(record_dir, Fence(f.epoch, me, "standby", accepted_head), now)


def _name(host: str) -> str:
    return "the research environment" if host == "cloud" else "the owner's server"


def short(h: str) -> str:
    """The 12 characters the owner compares on the phone."""
    return h[:12]
