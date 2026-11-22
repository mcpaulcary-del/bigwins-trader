"""bigwins worker (BF-D45): the version bookkeeping of the host worker.

    python3 gitops.py record <state_dir> <head>     before an update: remember the commit
    python3 gitops.py target <state_dir> <head>     the rollback target, or exit 1
    python3 gitops.py done <state_dir>              after a rollback: forget it (no ping-pong)

The rollback target is only ever the commit this worker recorded before the last update
(never a commit from the app or a user), and only if it differs from the running one.
Standard library only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
NAME = "previous_commit"


def record(state: Path, head: str) -> None:
    if not SHA.fullmatch(head):
        raise ValueError("not a full commit id")
    state.mkdir(parents=True, exist_ok=True)
    (state / NAME).write_text(head + "\n", encoding="utf-8")


def target(state: Path, head: str) -> str | None:
    p = state / NAME
    if not p.is_file():
        return None
    t = p.read_text(encoding="utf-8").strip()
    return t if SHA.fullmatch(t) and t != head else None


def done(state: Path) -> None:
    (state / NAME).unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    op, state = argv[1], Path(argv[2])
    if op == "record":
        record(state, argv[3])
        return 0
    if op == "target":
        t = target(state, argv[3])
        if t is None:
            return 1
        print(t)
        return 0
    if op == "done":
        done(state)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
