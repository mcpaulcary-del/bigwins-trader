"""bigwins worker (BF-D93): the paper record's systemd timers. Root writes unit files
from THIS file only (deploy code: a change here is a trading / infrastructure update with
every guard of one), never from ``record/``. Standard library only (the host's python3).

A **unit** is a timer that runs one chain of record jobs (``bigwins record run <chain>``).
All times are Sydney: every timer carries ``Australia/Sydney`` like the existing ones (the
two cloud tasks that ran on UTC times are fixed to Sydney times here).

    python3 -I record_units.py write <unit dir> <path of bigwins.sh>    prints "name modes"
    python3 -I record_units.py sum <path of bigwins.sh>                 the set's fingerprint
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Unit:
    name: str  # systemd unit bigwins-<name>
    label: str
    calendars: tuple[str, ...]  # systemd OnCalendar (Australia/Sydney is appended)
    chain: str  # the ``bigwins record run <chain>`` argument
    modes: tuple[str, ...] = ("shadow", "writer")  # when the timer does work
    persistent: bool = True


UNITS: tuple[Unit, ...] = (
    Unit("rec-morning", "paper record: info archive and NEWS-C prepare (BF-D93)",
         ("*-*-* 07:40:00", "Mon..Fri *-*-* 08:10:00", "Mon..Fri *-*-* 20:50:00"), "morning"),
    Unit("rec-collect", "paper record: estimates, new listings, ASIC files (BF-D93)",
         ("Tue..Sat *-*-* 08:43:00",), "collect", modes=("writer",)),
    Unit("rec-newsc", "paper record: NEWS-C replies from the relay (BF-D93)",
         ("Mon..Fri *-*-* 08:35..59/3:00", "Mon..Fri *-*-* 09:00..57/3:00",
          "Mon..Fri *-*-* 10..15:05/10:00"), "newsc", persistent=False),
    Unit("rec-intraday", "paper record: intraday look (BF-D93)",
         ("Mon..Fri *-*-* 10,12,14,16:20:00",), "intraday", modes=("writer",), persistent=False),
    Unit("rec-daily", "paper record: daily close (BF-D93)",
         ("Mon..Fri *-*-* 20:27:00",), "daily"),
    Unit("rec-multi", "paper record: multi-market month (BF-D93)",
         ("*-*-01..08 15:17:00",), "multi", modes=("writer",)),
    Unit("rec-usfwd", "paper record: US forward tracker month (BF-D93)",
         ("*-*-02..05 18:13:00",), "usfwd", modes=("writer",)),
    Unit("rec-compare", "paper record: shadow compare (parallel run, BF-D93)",
         ("Mon..Fri *-*-* 21:30:00", "Mon..Fri *-*-* 22:15:00", "Mon..Fri *-*-* 23:00:00"),
         "compare", modes=("shadow",)),
    Unit("rec-relay", "paper record: relay pull (reports, requests, fence; BF-D93)",
         ("*-*-* *:02/10:00",), "relay", modes=("shadow", "writer", "view"), persistent=False),
)  # fmt: skip


def unit_files(u: Unit, script: str) -> tuple[str, str]:
    """(service text, timer text) of one unit, shaped like the worker's other units."""
    svc = (f"[Unit]\nDescription=Big Wins {u.label}\nAfter=docker.service\n\n[Service]\n"
           f"Type=oneshot\nExecStart={script} record run {u.chain}\n"
           "TimeoutStartSec=9000\n")  # fmt: skip
    cal = "".join(f"OnCalendar={c} Australia/Sydney\n" for c in u.calendars)
    keep = "true" if u.persistent else "false"
    tmr = (f"[Unit]\nDescription=Big Wins {u.label}\n\n[Timer]\n{cal}"
           f"Persistent={keep}\n\n[Install]\nWantedBy=timers.target\n")  # fmt: skip
    return svc, tmr


def fingerprint(script: str) -> str:
    blob = "".join("".join(unit_files(u, script)) + u.name for u in UNITS)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[0] == "write":
        for u in UNITS:
            svc, tmr = unit_files(u, argv[2])
            (Path(argv[1]) / f"bigwins-{u.name}.service").write_text(svc, encoding="utf-8")
            (Path(argv[1]) / f"bigwins-{u.name}.timer").write_text(tmr, encoding="utf-8")
            print(f"{u.name} {','.join(u.modes)}")
        return 0
    if len(argv) == 2 and argv[0] == "sum":
        print(fingerprint(argv[1]))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
