"""The phone app's records in the journal (BF-D39..BF-D42): the inbox, Web Push
subscriptions, small app state and the server-job queue.

Only the trader process (``trader-bf run``) and the host worker's ``trader-bf
server-jobs`` command write here; the read-only dashboard reads the inbox, the state and
the jobs through its read-only engine.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert, select, update

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
}
GUARDED_ACTIONS = frozenset({"restart", "update", "rollback"})  # ASX open: refused unless forced
# bits of server_jobs.force (BF-D42, BF-D45)
FORCE_MARKET = 1  # "do it anyway" while the ASX is open (app-only updates, restart)
FORCE_MONTH_END = 2  # next_decision mode: override the 24-hour block before a decision
STRATEGY = 4  # the update changes the strategy: applied only when safe (BF-D45)
IMMEDIATE = 8  # update_mode immediate: an out-of-cycle decision follows
LONG_WAIT = frozenset({"update", "rollback"})  # may wait for the close: stale after a day


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


def add_server_job(j: Journal, action: str, force: bool | int, login: str, at: datetime) -> int:
    if action not in SERVER_ACTIONS:
        raise ValueError(f"not a server action: {action!r}")
    with j.engine.begin() as c:
        r = c.execute(
            insert(server_jobs).values(
                action=action,
                force=int(force),
                login=login[:200],
                requested_at=_utc(at),
                status="PENDING",
                result="",
            )
        )
        return int(r.inserted_primary_key[0])


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
    """The oldest PENDING job, marked RUNNING (one worker at a time). A job requested
    more than ``stale_s`` ago (a day for an update or rollback, which may wait for the
    close) is not run any more (REFUSED: too old to be what the owner wants now).
    ``wait(job)``: why a job must wait (BF-D45: a strategy update while the ASX is open
    or orders are working); it stays PENDING with that reason as its result."""
    with j.engine.begin() as c:
        rows = c.execute(
            select(server_jobs).where(server_jobs.c.status == "PENDING").order_by(server_jobs.c.id)
        ).all()
        for r in rows:
            m = dict(r._mapping)
            req = aware(m["requested_at"])
            assert req is not None
            limit = 86400 if m["action"] in LONG_WAIT else stale_s
            if (at - req).total_seconds() > limit:
                c.execute(
                    update(server_jobs)
                    .where(server_jobs.c.id == m["id"])
                    .values(status="REFUSED", finished_at=_utc(at), result="too old: not run")
                )
                continue
            why = wait(m) if wait is not None else None
            if why is not None:
                c.execute(
                    update(server_jobs).where(server_jobs.c.id == m["id"]).values(result=why[:4000])
                )
                return None  # in order: nothing after a waiting job runs first
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
