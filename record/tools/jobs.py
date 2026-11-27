"""The moved jobs (BF-D93): what each one runs, when, and by when it must have finished.

One table for the container runner (``runner.py``), the worker's gate and the app's
missed-job alarm (``trader/record_view.py`` holds the same expected times; a test keeps
the two equal). The systemd timers are NOT here: root writes them from
``deploy/record_units.py`` (deploy code, with a trading update's guards). Standard library only.

A **job** is a list of steps run one after another in one record container:
``py`` = a research script run as on the cloud (``-I`` where the cloud task uses it),
``tool`` = one of these tools.
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
    # RAM cap of the job's container. The server has 3.9 GB: IB Gateway (1.5 GB), the trader,
    # the app and the database must never be squeezed by a record job. The heavy jobs (daily
    # close, monthly) run in the evening with 1.5 GB; everything that runs in the morning or
    # in ASX hours gets 600-800 MB, and ANY job started while the ASX is open is held to
    # 600 MB and half a CPU (deploy/record.sh). Above its cap a job swaps (to twice the cap)
    # and is the first to be killed if the whole machine runs short.
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
    ), network=True, ledger=False, eodhd=True, memory_mb=600),
    # T3 (A) and (C), then (B) without a subagent: the CXL line's files from the archive
    Job("collect", "Estimates, new listings, ASIC files", (
        py("est_snapshot.py", isolated=True, timeout_s=1200, must=False),
        py("newlist_tracker.py", isolated=True, timeout_s=900, must=False),
        tool("asic_daily"),
    ), network=True, ledger=False, eodhd=True, memory_mb=800),
    # T4 step 1 and the evening archive run: the ONLY job that contacts asx.com.au
    Job("archive", "Info archive (ASX list, notices, shorts)", (
        py("info_archive.py", "asx", "asic", "--asic-limit=400", timeout_s=1500),
        tool("archive_check"),  # the stored day is sane (the older server copy's refusals)
    ), network=True, ledger=False, memory_mb=600),
    # T4 steps 2 and 2b: no network
    Job("newsc-prepare", "NEWS-C: prepare the batches", (
        py("newsc_prepare.py"),
        py("newsc_drops.py", must=False),
    ), network=False, ledger=False, memory_mb=600),
    # T4 steps 4 and 4b, from the cloud raters' replies pulled through the relay
    Job("newsc-record", "NEWS-C: record the ratings", (
        tool("newsc_record"),
    ), network=False, ledger=True, memory_mb=600),
    Job("newsc-drops-record", "NEWS-C: record the drop causes", (
        tool("newsc_drops_record"),
    ), network=False, ledger=True, memory_mb=600),
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
    "pdf-backup": ("Archive PDFs sent off-site", "every night with the backup", "after", "23:59"),
}
