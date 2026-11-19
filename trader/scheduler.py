"""Scheduler for the B-fast jobs (FD v3.0 §4; BW-OPS-01 idempotent jobs).

A small deterministic loop instead of APScheduler: every ASX session it runs the jobs
of ``trader.bf_app.DAY_JOBS`` whose time has come, each exactly once (the journal
records ``<day>:<hh:mm>:<job>`` as done, so a restart never repeats a job), and it
polls Telegram between jobs so that ``/pause`` and ``/kill`` act within seconds.
Non-session days run nothing but the Telegram poll.
"""

from __future__ import annotations

import time as _time
from collections.abc import Callable
from datetime import UTC, datetime

from trader.bf_app import DAY_JOBS, BfApp, at
from trader.constants import ASX_TZ


def due_jobs(app: BfApp, now: datetime) -> list[tuple[str, str]]:
    day = now.astimezone(ASX_TZ).date()
    if not app.is_session(day):
        return []
    out = []
    for hhmm, name in DAY_JOBS:
        key = f"{day}:{hhmm}:{name}"
        if at(day, hhmm) <= now and not app.j.job_done(key):
            out.append((key, name))
    return out


def run_once(app: BfApp, now: datetime) -> list[str]:
    """Poll Telegram, then run every due job in order. Returns the job keys run."""
    day = now.astimezone(ASX_TZ).date()
    app.now = now
    app.bot.handle_all()
    ran = []
    for key, name in due_jobs(app, now):
        app.run_job(name, day, now)
        app.j.mark_job(key)
        ran.append(key)
    return ran


def run_forever(
    app: BfApp,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = _time.sleep,
    poll_seconds: float = 20.0,
    stop: Callable[[], bool] = lambda: False,
) -> None:
    while not stop():
        run_once(app, clock())
        sleep(poll_seconds)
