"""BF-D45: the running strategy version in the trader process, and the out-of-cycle
decision after an update in ``immediate`` mode.

At start-up the trader compares its strategy fingerprint with the one it ran before
(``strategy-running`` app state). A different one is journaled (``strategy-change:``)
and told to the owner; in ``immediate`` mode it is marked pending: on the next ASX
session at or after 22:20 (after the twin's 22:15 run, when the day's prices are in) the
trader makes an out-of-cycle decision for every book through the month-end decision
path (``BfApp.job_decide`` with kind "R": the same list, sizing, cash, risk, LIC-list,
loss-rule and data checks). Its batch for the paper book needs the owner's approval in
the app like any other, by 15:20 of the next session. On a month-end session the
regular decision already uses the new version. ``next_decision`` mode: no out-of-cycle
decision; the new rules first act at the next month-end decision.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from trader.app_store import get_state, set_state
from trader.bf_app import BfApp, at
from trader.constants import ASX_TZ
from trader.strategy_version import DECISION_AT, Fingerprint

DECIDE_HHMM = DECISION_AT.strftime("%H:%M")


@dataclass
class StrategyRuntime:
    app: BfApp
    fp: Fingerprint
    mode: str = "immediate"
    notify: Callable[[str], object] | None = None

    def start(self, now: datetime) -> str:
        """Record the running version; ``changed`` | ``same`` | ``first``."""
        j = self.app.j
        self.app.strategy = self.fp.record()
        prev = get_state(j, "strategy-running")
        set_state(j, "strategy-running", self.fp.record(), now)
        if prev is None or not isinstance(prev[0], dict):
            return "first"
        old: dict[str, Any] = prev[0]
        if old.get("id") == self.fp.id:
            return "same"
        j.mark_job(f"strategy-change:{self.fp.id}:{now.isoformat()}",
                   {"from": old, "to": self.fp.record(), "mode": self.mode}, now)  # fmt: skip
        if self.mode == "immediate":
            set_state(j, "strategy-pending", {"id": self.fp.id, "since": now.isoformat()}, now)
            when = "tonight at 22:20 (after the day's prices)" if self.app.is_session(
                now.astimezone(ASX_TZ).date()) else "at 22:20 on the next trading day"  # fmt: skip
            text = (f"Strategy {self.fp.version} ({self.fp.id}) is now running (was "
                    f"{old.get('version', '?')}). An out-of-cycle decision follows {when}; "
                    "its orders wait for your approval.")  # fmt: skip
        else:
            text = (f"Strategy {self.fp.version} ({self.fp.id}) is now running; its rules first "
                    "act at the next month-end decision.")  # fmt: skip
        if self.notify is not None:
            self.notify(text)
        return "changed"

    def tick(self, now: datetime) -> str:  # noqa: PLR0911 - one outcome per return
        """``idle`` | ``wait`` | ``decided`` | ``covered`` (the regular decision did it)."""
        j = self.app.j
        st = get_state(j, "strategy-pending")
        pend = st[0] if st and isinstance(st[0], dict) else None
        if pend is None or pend.get("id") != self.fp.id or pend.get("done"):
            return "idle"
        day = now.astimezone(ASX_TZ).date()
        if not self.app.is_session(day) or now < at(day, DECIDE_HHMM):
            return "wait"
        book = self.app.s.book
        if self.app.decision_kind(day, book) is not None:  # a month-end: the scheduler's job
            if not j.job_done(f"decide:{book}:{day}"):
                return "wait"
            set_state(j, "strategy-pending", {**pend, "done": str(day)}, now)
            return "covered"
        if j.job_done(f"decide:{book}:{day}"):
            set_state(j, "strategy-pending", {**pend, "done": str(day)}, now)
            return "covered"
        if not self.app.job_decide(day, now, "R"):  # the day's data are not in yet
            return "wait"
        set_state(j, "strategy-pending", {**pend, "done": str(day)}, now)
        j.mark_job(f"strategy-decision:{self.fp.id}:{day}", self.fp.record(), now)
        return "decided"
