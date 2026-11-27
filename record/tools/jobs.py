"""The moved jobs (BF-D93): what each one runs, when, and by when it must have finished.

One table for the host worker (systemd timers, ``deploy/record.sh``), the container
runner (``runner.py``) and the app's missed-job alarm (``trader/record_view.py`` holds
the same expected times; a test keeps the two equal). Standard library only.

A **job** is a list of steps run one after another in one record container:
``py`` = a research script run as on the cloud (``-I`` where the cloud task uses it),
``tool`` = one of these tools. A **unit** is a systemd timer that runs a chain of jobs.
All times are Sydney (every timer carries ``Australia/Sydney``, like the existing ones;
the two cloud tasks that were on UTC times are fixed to Sydney times here).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    kind: str  # py | tool
    name: str  # script file in the code folder, or the tool's name
    args: tuple[str, ...] = ()
    isolated: bool = False  # python -I, as the cloud task runs it
    timeout_s: int = 3000
    must: bool = True  # False: a failure is reported but later steps still run


@dataclass(frozen=True)
class Job:
    key: str
    label: str
    steps: tuple[Step, ...]
    network: bool  # True: the record egress network (EODHD / ASX / ASIC); else --network none
    ledger: bool  # appends to the ledger (so: fence + shipped-head gate, export afterwards)
    eodhd: bool = False  # gets the EODHD token file
    # RAM cap of the job's container. The server has 3.9 GB: IB Gateway (about 1.5 GB), the
    # trader, the app and the database must never be squeezed by a record job; above the
    # cap the job uses swap (to twice the cap), and it is the first to be killed if the
    # whole machine runs short. /etc/bigwins/record_memory_mb overrides (deploy/record.sh).
    memory_mb: int = 1500


def py(name: str, *args: str, isolated: bool = False, timeout_s: int = 3000,
       must: bool = True) -> Step:  # fmt: skip
    return Step("py", name, tuple(args), isolated, timeout_s, must)


def tool(name: str, *args: str, must: bool = True) -> Step:
    return Step("tool", name, tuple(args), False, 900, must)


JOBS: dict[str, Job] = {j.key: j for j in (
    # T2 (daily close): the cloud task's commands, in its order; then the read-only helpers
    Job("daily", "Paper record: daily close", (
        py("paper_daily.py"),
        py("paper_costalt.py", isolated=True, must=False),
        py("movers.py", isolated=True, must=False),
        tool("gapcheck", must=False),
    ), network=True, ledger=True, eodhd=True),
    # T1 (intraday look; no decisions, no ledger)
    Job("intraday", "Paper record: intraday look", (
        py("paper_intraday.py", timeout_s=1500),
    ), network=True, ledger=False, eodhd=True),
    # T3 (A) and (C), then (B) without a subagent: the CXL line's files from the archive
    Job("collect", "Estimates, new listings, ASIC files", (
        py("est_snapshot.py", isolated=True, timeout_s=1200, must=False),
        py("newlist_tracker.py", isolated=True, timeout_s=900, must=False),
        tool("asic_daily"),
    ), network=True, ledger=False, eodhd=True),
    # T4 step 1 and the evening archive run: the ONLY job that contacts asx.com.au
    Job("archive", "Info archive (ASX list, notices, shorts)", (
        py("info_archive.py", "asx", "asic", "--asic-limit=400", timeout_s=1500),
        tool("archive_check"),  # the stored day is sane (the older server copy's refusals)
    ), network=True, ledger=False),
    # T4 steps 2 and 2b: no network
    Job("newsc-prepare", "NEWS-C: prepare the batches", (
        py("newsc_prepare.py"),
        py("newsc_drops.py", must=False),
    ), network=False, ledger=False),
    # T4 steps 4 and 4b, from the cloud raters' replies pulled through the relay
    Job("newsc-record", "NEWS-C: record the ratings", (
        tool("newsc_record"),
    ), network=False, ledger=True),
    Job("newsc-drops-record", "NEWS-C: record the drop causes", (
        tool("newsc_drops_record"),
    ), network=False, ledger=True),
    # T5 (multi-market, monthly; idempotent)
    Job("multi", "Multi-market record (monthly)", (
        py("paper_multi.py", timeout_s=7000),
    ), network=True, ledger=True, eodhd=True),
    # the sixth cloud task (26 Nov 2026): the US forward tracker, monthly, information only
    Job("usfwd", "US forward tracker (monthly)", (
        py("paper_us_forward.py", timeout_s=7000),
    ), network=True, ledger=True, eodhd=True),
    # Phase 1: replay of the cloud's day from its bundle; no downloads at all
    Job("replay", "Shadow replay of the cloud's day", (
        py("paper_daily.py", "--no-download"),
        py("paper_costalt.py", isolated=True, must=False),
        py("movers.py", isolated=True, must=False),
    ), network=False, ledger=True),
)}  # fmt: skip


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

# The missed-job alarm (BF-D77 extended): job key -> (label, cadence in words, kind of day,
# "HH:MM" Sydney by which the job must have finished well). Kinds of day: ``session`` = that
# ASX trading day; ``after`` = the calendar day after an ASX trading day (the archive of a
# session is collected the next morning). trader/record_view.py mirrors this table.
EXPECT: dict[str, tuple[str, str, str, str]] = {
    "daily": ("Paper record: daily close", "every ASX day by 21:30", "session", "21:30"),
    "intraday": ("Paper record: intraday look", "every ASX day, four looks", "session", "16:50"),
    "collect": ("Estimates and new listings", "the morning after each ASX day", "after", "09:30"),
    "archive": ("Paper record: info archive", "the morning after each ASX day", "after", "09:30"),
    "newsc-record": ("NEWS-C ratings recorded", "every ASX day before 10:00", "session", "10:00"),
    "export": ("Record sent to OneDrive (relay)", "after every record job", "session", "21:45"),
    "compare": ("Shadow compare (parallel run)", "every ASX day by 23:15", "session", "23:15"),
}


def unit_files(u: Unit, script: str) -> tuple[str, str]:
    """(service text, timer text) of one unit; the same shape as the worker's other units."""
    svc = (f"[Unit]\nDescription=Big Wins {u.label}\nAfter=docker.service\n\n[Service]\n"
           f"Type=oneshot\nExecStart={script} record run {u.chain}\nTimeoutStartSec=9000\n")  # fmt: skip
    cal = "".join(f"OnCalendar={c} Australia/Sydney\n" for c in u.calendars)
    tmr = (f"[Unit]\nDescription=Big Wins {u.label}\n\n[Timer]\n{cal}"
           f"Persistent={'true' if u.persistent else 'false'}\n\n[Install]\nWantedBy=timers.target\n")  # fmt: skip
    return svc, tmr
