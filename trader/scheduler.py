"""Scheduler for the B-fast jobs (FD v3.0 §4; BW-OPS-01 idempotent jobs).

A small deterministic loop instead of APScheduler: every ASX session it runs the jobs
of ``trader.bf_app.DAY_JOBS`` whose time has come, each once (the journal records
``<day>:<hh:mm>:<job>`` as done, so a restart never repeats a job), and it polls
Telegram between jobs so that ``/pause`` and ``/kill`` act within seconds.

* A job that reports "not done" (the day's data is not in yet) is retried on the next
  poll; the job itself decides when to give up (``bf_app.RETRY_UNTIL``).
* A job that raises is recorded as done with the error and paged once: it is never
  retried blindly (the owner re-runs it by hand after a look). Sending is safe to
  re-run anyway (persist-before-send, one broker order per intent).
* Only today's jobs run: a missed day is not replayed after a long outage (orders of
  that day would be stale); the next session's jobs pick up held and carried orders.
* At start-up ``Executor.recover`` adopts broker orders of intents left in SENDING
  (never resends).
Non-session days run nothing but the Telegram poll, the phone app's actions and the
heartbeat ping.

The day, as wired in ``bf_app.DAY_JOBS``: owner ticks at 10:30 and 12:30, a reminder of
unapproved orders at 14:30, the IBKR Flex statement download into the inbox at 13:05,
14:05, 15:05, 16:05 and 16:25 until it is there (BF-D27; paged at 16:25 when late or
missing), the approval deadline at 15:20 (a later ``/ok`` is refused),
``submit`` at 15:45 sends only orders the owner approved -- every other order of the
day lapses (``LAPSED_NO_APPROVAL``) and is never sent later or automatically (L8; the
config schema has no ``auto`` mode for the broker book) -- fills at 16:20, reconciliation
at 16:30, the twin at 22:15, the decision at 22:20 on an ASX month-end (or the L6 start
day) with its orders for the next session (the order day), and the report at 22:45.
"""

from __future__ import annotations

import time as _time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from trader.bf_app import DAY_JOBS, BfApp, at
from trader.broker.base import BrokerDisconnectedError
from trader.constants import ASX_TZ

GATEWAY_EXIT = 3  # review H1: the process exits with this; Docker restarts it


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


Hook = Callable[[datetime], object]


def _hooks(hooks: Sequence[Hook], now: datetime, app: BfApp) -> None:
    for h in hooks:
        try:
            h(now)
        except Exception as e:  # an app action, a push or a heartbeat never stops the jobs
            app.log.append(f"hook failed: {type(e).__name__}")


def run_once(app: BfApp, now: datetime, hooks: Sequence[Hook] = ()) -> list[str]:
    """Poll Telegram, run the hooks (BF-D39 the phone app's queued actions, BF-D41 the
    heartbeat), then run every due job in order. Returns the job keys completed.
    Stops at the first job that is not done yet, so later jobs keep their order."""
    day = now.astimezone(ASX_TZ).date()
    app.now = now
    app.bot.handle_all()
    _hooks(hooks, now, app)
    ran = []
    for key, name in due_jobs(app, now):
        if name == "submit" and now > app.latest_send_at(day):  # review H3: never late
            app.submit_missed(day, now)
            app.j.mark_job(key, {"skipped": "after the latest send time"}, now)
            ran.append(key)
            continue
        try:
            done = app.run_job(name, day, now)
        except BrokerDisconnectedError as e:  # review H1: page, then exit for a restart
            app.say(f"PAGE gateway down: {e}. The trader restarts; jobs resume after.")
            raise
        except Exception as e:  # paged and recorded, never silently retried
            app.j.mark_job(key, {"error": f"{type(e).__name__}: {e}"[:300]}, now)
            app.say(f"PAGE job {name} of {day} failed: {type(e).__name__}: {e}"[:400])
            ran.append(key)
            continue
        if not done:
            break
        app.j.mark_job(key, None, now)
        ran.append(key)
    return ran


def start_up(app: BfApp, now: datetime) -> list[str]:
    """After a (re)start: adopt broker orders of intents left mid-send; page what is odd."""
    pages = app.ex.recover(now)
    for p in pages:
        app.say("PAGE " + p)
    why = app.lic_list_refused(now.astimezone(ASX_TZ).date(), now, "start-up")  # BF-D21
    if why is not None:
        pages.append("BF-D21 LIC list refused: " + why)
    return pages


def run_forever(
    app: BfApp,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = _time.sleep,
    poll_seconds: float = 20.0,
    stop: Callable[[], bool] = lambda: False,
    hooks: Sequence[Hook] = (),
) -> None:
    """``sleep``: the phone app's control server passes one that returns early when an
    action arrives (BF-D39), so an app action is handled within a second or two."""
    start_up(app, clock())
    pump = getattr(app.broker, "pump", None)
    try:
        while not stop():
            run_once(app, clock(), hooks)
            _hooks(hooks, clock(), app)
            sleep(poll_seconds)
            if callable(pump):  # review H2: the ib_async loop runs between jobs
                pump()
    except BrokerDisconnectedError as e:
        raise SystemExit(GATEWAY_EXIT) from e
