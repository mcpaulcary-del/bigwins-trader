"""The phone app's records in the journal (BF-D39..BF-D42): the inbox, Web Push
subscriptions, small app state and the server-job queue.

Only the trader process (``trader-bf run``) and the host worker's ``trader-bf
server-jobs`` command write here; the read-only dashboard reads the inbox, the state and
the jobs through its read-only engine.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, update

from trader.app_sign import sign_job
from trader.journal import Journal, app_state, inbox, push_subs, server_jobs

KINDS = ("page", "approval", "report", "info", "action")
# Server jobs the app may ask for (BF-D42): fixed names only, never arguments. The host
# worker (deploy/bigwins.sh worker) runs its own copy of this list and nothing else.
SERVER_ACTIONS: dict[str, str] = {
    "restart": "Restart the trader",
    "update": "Update to the latest code (pull, rebuild, restart)",
    "rollback": "Go back to the previous version (the commit before the last update)",
    "check": "Re-run the server checks (secret files, containers)",
    "claude_remote": "Start Claude remote control on the server (tmux session 'remote')",
    "claude_stop": "Stop Claude remote control on the server",
    "backup_now": "Back up now (server and OneDrive)",  # BF-D64
    "restore_test": "Restore test: unpack the latest backup in a throwaway place and check it",
    "backup_key": "Show the backup recovery key once",
    "fetch": "Check for updates now",  # BF-D65
    "hc_ping": "Send a test ping to healthchecks.io",
    "info_archive": "Collect the announcements now (private archive, if on)",  # BF-D78
    "prev_twin": "Run the previous-version twin now (after a strategy update)",  # BF-D80
    # BF-D90: the switch for automatic app-only updates (a root-only file on the server)
    "autoupdate_on": "Turn automatic app updates on (app-only changes, outside ASX hours)",
    "autoupdate_off": "Turn automatic app updates off (every update waits for your approval)",
}
GUARDED_ACTIONS = frozenset({"restart", "update", "rollback"})  # ASX open: refused unless forced
# bits of server_jobs.force (BF-D42, BF-D45)
FORCE_MARKET = 1  # "do it anyway" while the ASX is open (app-only updates, restart)
FORCE_MONTH_END = 2  # next_decision mode: override the 24-hour block before a decision
STRATEGY = 4  # the update changes the strategy: applied only when safe (BF-D45)
IMMEDIATE = 8  # update_mode immediate: an out-of-cycle decision follows
LONG_WAIT = frozenset({"update", "rollback"})  # may wait for the close
LONG_WAIT_S = 12 * 3600  # BF-D48: an approved update / rollback is applied within 12 hours
RUNNING_LIMIT_S = 2 * 3600  # BF-D49: a RUNNING job older than this is marked FAILED
FORCE_MIGRATION = 16  # BF-D49: roll back across a database migration (owner ticked it)
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _utc(t: datetime) -> datetime:
    return t.astimezone(UTC)


def aware(t: datetime | None) -> datetime | None:
    if t is None:
        return None
    return t if t.tzinfo else t.replace(tzinfo=UTC)


# ---------------------------------------------------------------- inbox


def add_inbox(
    j: Journal,
    at: datetime,
    kind: str,
    title: str,
    body: str,
    link: str = "",
    source: str = "trader",
    push: str = "",
) -> int:
    if kind not in KINDS:
        raise ValueError(f"unknown inbox kind {kind!r}")
    with j.engine.begin() as c:
        r = c.execute(
            insert(inbox).values(
                at=_utc(at),
                kind=kind,
                title=title[:200],
                body=body[:20000],
                link=link[:200],
                source=source[:64],
                push=push[:64],
            )
        )
        return int(r.inserted_primary_key[0])


def inbox_rows(
    j: Journal, limit: int = 200, kinds: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    q = select(inbox).order_by(inbox.c.id.desc()).limit(limit)
    if kinds is not None:
        q = q.where(inbox.c.kind.in_(list(kinds)))
    with j.engine.connect() as c:
        out = [dict(r._mapping) for r in c.execute(q)]
    for r in out:
        r["at"] = aware(r["at"])
    return out


# ---------------------------------------------------------------- Web Push subscriptions


def add_push_sub(
    j: Journal, endpoint: str, p256dh: str, auth: str, login: str, at: datetime
) -> None:
    with j.engine.begin() as c:
        old = c.execute(select(push_subs.c.id).where(push_subs.c.endpoint == endpoint)).first()
        vals = {"p256dh": p256dh, "auth": auth, "login": login, "active": 1, "last_error": ""}
        if old is None:
            c.execute(insert(push_subs).values(endpoint=endpoint, created_at=_utc(at), **vals))
        else:
            c.execute(update(push_subs).where(push_subs.c.id == old[0]).values(**vals))


def push_sub_rows(j: Journal, active_only: bool = True) -> list[dict[str, Any]]:
    q = select(push_subs).order_by(push_subs.c.id)
    if active_only:
        q = q.where(push_subs.c.active == 1)
    with j.engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(q)]


def set_push_sub(j: Journal, sub_id: int, active: bool, error: str = "") -> None:
    with j.engine.begin() as c:
        c.execute(
            update(push_subs)
            .where(push_subs.c.id == sub_id)
            .values(active=int(active), last_error=error[:200])
        )


def drop_push_sub(j: Journal, endpoint: str) -> bool:
    with j.engine.begin() as c:
        r = c.execute(update(push_subs).where(push_subs.c.endpoint == endpoint).values(active=0))
        return bool(r.rowcount)


# ---------------------------------------------------------------- app state


def get_state(j: Journal, key: str) -> tuple[Any, datetime] | None:
    with j.engine.connect() as c:
        r = c.execute(select(app_state.c.value, app_state.c.at).where(app_state.c.key == key))
        row = r.first()
    if row is None:
        return None
    at = aware(row[1])
    assert at is not None
    return row[0], at


def set_state(j: Journal, key: str, value: Any, at: datetime) -> None:
    with j.engine.begin() as c:
        old = c.execute(select(app_state.c.key).where(app_state.c.key == key)).first()
        if old is None:
            c.execute(insert(app_state).values(key=key, value=value, at=_utc(at)))
        else:
            c.execute(
                update(app_state).where(app_state.c.key == key).values(value=value, at=_utc(at))
            )


# ---------------------------------------------------------------- server jobs (BF-D42)


def created_text(t: datetime) -> str:
    """The requested-at time as signed (BF-D48): UTC, whole seconds."""
    a = aware(t)
    assert a is not None
    return a.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def add_server_job(
    j: Journal,
    action: str,
    force: bool | int,
    login: str,
    at: datetime,
    commit: str = "",
    key: bytes | None = None,
) -> int:
    """Queue a server job. ``commit``: the exact 40-hex commit the owner reviewed (update)
    or the recorded previous commit (rollback); ``key``: the worker key that signs the job
    (BF-D48; the host worker runs no unsigned job)."""
    if action not in SERVER_ACTIONS:
        raise ValueError(f"not a server action: {action!r}")
    if commit and not SHA40.fullmatch(commit):
        raise ValueError("commit must be a full 40-hex commit id")
    if action in ("update", "rollback") and not commit:
        raise ValueError(f"{action} needs the exact commit")
    t = _utc(at).replace(microsecond=0)
    with j.engine.begin() as c:
        r = c.execute(
            insert(server_jobs).values(
                action=action,
                force=int(force),
                login=login[:200],
                requested_at=t,
                status="PENDING",
                result="",
                commit=commit or None,
                sig=None,
            )
        )
        jid = int(r.inserted_primary_key[0])
        if key is not None:
            sig = sign_job(key, jid, action, commit, int(force), created_text(t))
            c.execute(update(server_jobs).where(server_jobs.c.id == jid).values(sig=sig))
        return jid


def cancel_server_job(j: Journal, job_id: int, login: str, at: datetime) -> bool:
    """BF-D49: the owner cancels a queued job (PENDING only; a running one finishes)."""
    with j.engine.begin() as c:
        r = c.execute(
            update(server_jobs)
            .where(server_jobs.c.id == job_id, server_jobs.c.status == "PENDING")
            .values(status="REFUSED", finished_at=_utc(at), result=f"cancelled by {login[:80]}")
        )
        return bool(r.rowcount)


def server_job_rows(j: Journal, limit: int = 20) -> list[dict[str, Any]]:
    q = select(server_jobs).order_by(server_jobs.c.id.desc()).limit(limit)
    with j.engine.connect() as c:
        out = [dict(r._mapping) for r in c.execute(q)]
    for r in out:
        for k in ("requested_at", "started_at", "finished_at"):
            r[k] = aware(r[k])
    return out


def claim_server_job(
    j: Journal,
    at: datetime,
    stale_s: int = 900,
    wait: Callable[[dict[str, Any]], str | None] | None = None,
) -> dict[str, Any] | None:
    """The oldest runnable PENDING job, marked RUNNING (one worker at a time).

    * A job requested more than ``stale_s`` ago (``LONG_WAIT_S`` = 12 hours for an update
      or rollback, which may wait for the close) is not run any more (REFUSED).
    * ``wait(job)``: why a job must wait (BF-D45: a strategy update while the ASX is open
      or orders are working); it stays PENDING with that reason as its result. A waiting
      update holds back later updates / rollbacks only; restart, check and the Claude
      jobs still run (BF-D49).
    * A RUNNING job older than ``RUNNING_LIMIT_S`` is marked FAILED (the worker died or
      hung; BF-D49) so it is reported and does not block the queue."""
    with j.engine.begin() as c:
        for r in c.execute(select(server_jobs).where(server_jobs.c.status == "RUNNING")).all():
            st = aware(r.started_at) or aware(r.requested_at)
            assert st is not None
            if (at - st).total_seconds() > RUNNING_LIMIT_S:
                c.execute(
                    update(server_jobs)
                    .where(server_jobs.c.id == r.id, server_jobs.c.status == "RUNNING")
                    .values(status="FAILED", finished_at=_utc(at),
                            result="the server worker did not report back within 2 hours")
                )  # fmt: skip
        rows = c.execute(
            select(server_jobs).where(server_jobs.c.status == "PENDING").order_by(server_jobs.c.id)
        ).all()
        held = False  # an earlier update / rollback is waiting
        for r in rows:
            m = dict(r._mapping)
            req = aware(m["requested_at"])
            assert req is not None
            limit = LONG_WAIT_S if m["action"] in LONG_WAIT else stale_s
            if (at - req).total_seconds() > limit:
                c.execute(
                    update(server_jobs)
                    .where(server_jobs.c.id == m["id"])
                    .values(status="REFUSED", finished_at=_utc(at), result="too old: not run")
                )
                continue
            if held and m["action"] in LONG_WAIT:
                continue
            why = wait(m) if wait is not None else None
            if why is not None:
                c.execute(
                    update(server_jobs).where(server_jobs.c.id == m["id"]).values(result=why[:4000])
                )
                held = held or m["action"] in LONG_WAIT
                continue
            done = c.execute(
                update(server_jobs)
                .where(server_jobs.c.id == m["id"], server_jobs.c.status == "PENDING")
                .values(status="RUNNING", started_at=_utc(at))
            )
            if done.rowcount:
                m["status"] = "RUNNING"
                return m
    return None


def finish_server_job(j: Journal, job_id: int, status: str, result: str, at: datetime) -> bool:
    if status not in ("DONE", "FAILED", "REFUSED"):
        raise ValueError(f"bad final status {status!r}")
    with j.engine.begin() as c:
        r = c.execute(
            update(server_jobs)
            .where(server_jobs.c.id == job_id, server_jobs.c.status == "RUNNING")
            .values(status=status, result=result[-4000:], finished_at=_utc(at))
        )
        return bool(r.rowcount)
