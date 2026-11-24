"""Owner presence and the incapacity default (BF-D82; owner decision 24 Nov 2026, option
(b)), renewal reminders (BF-D86) and the new-code alert (BF-D84).

**Owner action**, precisely: an action the trader's control server accepted from an
allowed log-in (an approval, refusal, veto, Pause / Kill / Stop / Status, Resume, a
code-change confirmation, a server job, alert or cost settings, Lock / Unlock, or the
explicit **I'm here** button on Home / Health), or a command from the owner's Telegram
chat when that channel is on. A request refused for a wrong code or passphrase does not
count. **Opening a page does not count**: pages are served by the read-only dashboard
(no write access to the journal), any device on the tailnet can view them, and the app
refreshes itself, so a phone left on a charger would keep "present" for ever.

**What happens** after ``app.presence_days`` (default 14) days without an owner action:
the safety level is raised to ``HALTED_BUYS`` with the ``risk.worst`` order (a stricter
level is never lowered, BF-D74), the owner gets a high-priority PAGE, and the host worker
stops pinging the optional outside check ``healthchecks_presence_url``, so healthchecks.io
alerts the second contact as well (also when the server is dead). Sells and the loss-rule
wind-down still need approval as before; nothing is sold automatically. At
``app.presence_warn_days`` (default 10) the owner gets a warning push. Resuming needs
``/resume`` with the 6-digit code (and the passphrase when it is set), like any re-arm.
The clock starts when the trader first runs this code (``presence-since``), so a fresh
install or an upgrade does not pause at once. In paper mode it runs the same way and the
messages say "paper".
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from trader.app_store import get_state, set_state
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.risk import SafetyLevel, worst

PRESENCE = "owner-presence"
SINCE = "presence-since"
TOLD = "presence-told"
REASON = "owner presence: no owner action for {days} days (BF-D82)"
ACTOR = "presence"
DEFAULT_DAYS = 14
DEFAULT_WARN = 10


def _ts(x: Any) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(x))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo is not None else None


def record_action(j: Journal, at: datetime, what: str) -> None:
    """An owner action (see the module text). ``what`` is a short label, never a code."""
    set_state(j, PRESENCE, {"last": at.isoformat(), "what": what[:60]}, at)


def start_tracking(j: Journal, now: datetime) -> datetime:
    """The clock's start (the first time the trader ran this code); kept once set."""
    st = get_state(j, SINCE)
    t = _ts(st[0].get("at")) if st and isinstance(st[0], Mapping) else None
    if t is None:
        set_state(j, SINCE, {"at": now.isoformat()}, now)
        t = now
    return t


@dataclass(frozen=True)
class Presence:
    tracking: bool  # False until the trader has started this clock
    last: datetime | None  # the last owner action (or the clock's start)
    what: str
    days: int
    warn_days: int

    @property
    def warn_at(self) -> datetime | None:
        return None if self.last is None else self.last + timedelta(days=self.warn_days)

    @property
    def pause_at(self) -> datetime | None:
        return None if self.last is None else self.last + timedelta(days=self.days)

    def days_since(self, now: datetime) -> int:
        return 0 if self.last is None else max(0, (now - self.last).days)

    def ok(self, now: datetime) -> bool:
        """Within the allowed days (or not tracking yet): the worker pings the outside check."""
        return not self.tracking or self.pause_at is None or now < self.pause_at


def status(j: Journal, days: int = DEFAULT_DAYS, warn_days: int = DEFAULT_WARN) -> Presence:
    st = get_state(j, PRESENCE)
    rec = st[0] if st and isinstance(st[0], Mapping) else {}
    last = _ts(rec.get("last"))
    sn = get_state(j, SINCE)
    since = _ts(sn[0].get("at")) if sn and isinstance(sn[0], Mapping) else None
    tracking = since is not None or last is not None
    newest = max((t for t in (last, since) if t is not None), default=None)
    what = str(rec.get("what") or "") if last is not None and newest == last else "clock started"
    return Presence(tracking, newest, what, days, min(warn_days, days - 1))


def raise_halt(j: Journal, now: datetime, days: int) -> tuple[bool, SafetyLevel]:
    """Raise the level to HALTED_BUYS unless a stricter level is in force (BF-D74 order).
    The same level is written again with this reason, so the L11 staged test (which clears
    only its own HALTED_BUYS) can never clear the presence pause. Returns (written, level)."""
    cur = j.safety_level()
    if worst(cur, SafetyLevel.HALTED_BUYS) is not SafetyLevel.HALTED_BUYS:
        return False, cur
    j.set_safety(SafetyLevel.HALTED_BUYS, REASON.format(days=days), ACTOR, now)
    return True, SafetyLevel.HALTED_BUYS


# ---------------------------------------------------------------- renewal reminders (BF-D86)

REMINDERS = (
    ("flex_token", "IBKR Flex token"),
    ("card", "Payment card (EODHD, Claude, healthchecks)"),
    ("binarylane_card", "BinaryLane card or prepaid credit"),
)
REMINDER_DAYS = (30, 7, 1, 0)


def reminder_dates(j: Journal) -> dict[str, date]:
    st = get_state(j, "reminders")
    raw = st[0] if st and isinstance(st[0], Mapping) else {}
    out: dict[str, date] = {}
    for k, _ in REMINDERS:
        try:
            out[k] = date.fromisoformat(str(raw.get(k) or ""))
        except ValueError:
            continue
    return out


def reminders_due(dates: Mapping[str, date], today: date) -> list[tuple[str, str, date, int]]:
    """(key, label, date, days left) of every reminder within 30 days or past."""
    labels = dict(REMINDERS)
    out = [(k, labels[k], d, (d - today).days) for k, d in dates.items() if k in labels]
    return sorted((r for r in out if r[3] <= REMINDER_DAYS[0]), key=lambda r: r[3])


# ---------------------------------------------------------------- the hook

SIG_WORDS = {
    "good": "signed by the engineer's key",
    "bad": "NOT signed by the engineer's key",
    "none": "not signed (no signing key on the server yet)",
}


@dataclass
class PresenceHook:
    """The trader's loop hook (every few minutes): the presence warning and pause, the
    renewal reminders and the new-code alert. Each part is guarded on its own."""

    j: Journal
    notify: Callable[..., object]
    days: int = DEFAULT_DAYS
    warn_days: int = DEFAULT_WARN
    paper: bool = True

    def tick(self, now: datetime) -> list[str]:
        out: list[str] = []
        for part in (self._presence, self._reminders, self._new_code):
            try:
                out += part(now)
            except Exception as ex:  # an alarm never stops the trader
                out.append(f"failed: {type(ex).__name__}")
        return out

    def _say(self, text: str, kind: str, link: str) -> None:
        self.notify(text, kind, link)

    def _presence(self, now: datetime) -> list[str]:
        start_tracking(self.j, now)
        p = status(self.j, self.days, self.warn_days)
        if p.last is None or p.warn_at is None or p.pause_at is None:
            return []
        ep = p.last.isoformat()
        st = get_state(self.j, TOLD)
        told: dict[str, Any] = dict(st[0]) if st and isinstance(st[0], Mapping) else {}
        if told.get("episode") != ep:
            told = {"episode": ep}
        mode = "Paper account: this is the real-money safety rule running for practice. " \
            if self.paper else ""  # fmt: skip
        out: list[str] = []
        pause_day = p.pause_at.astimezone(ASX_TZ)
        if now >= p.pause_at and not told.get("paused"):
            written, lvl = raise_halt(self.j, now, self.days)
            what = ("buying is now PAUSED (HALTED_BUYS)" if written
                    else f"trading stays {lvl.value} (already stricter)")  # fmt: skip
            self._say(
                f"PAGE HIGH PRIORITY no owner action in the Big Wins app for {self.days} days: "
                f"{what}. Nothing is sold automatically; sells still need your approval. "
                f"{mode}When you are back: Controls > Resume with your 6-digit code. Your second "
                "contact is told by healthchecks.io.", "page", "/act")  # fmt: skip
            told["paused"] = told["warned"] = True
            out.append("paused")
        elif now >= p.warn_at and not told.get("warned"):
            self._say(
                f"PAGE no owner action in the Big Wins app for {p.days_since(now)} days. On "
                f"{pause_day:%a %d %b} at {pause_day:%H:%M} buying pauses automatically and your "
                f"second contact is told. {mode}If you are fine: open the app and tap I'm here "
                "(Home or Server > Health).", "page", "/health")  # fmt: skip
            told["warned"] = True
            out.append("warned")
        if out:
            set_state(self.j, TOLD, told, now)
        return out

    def _reminders(self, now: datetime) -> list[str]:
        today = now.astimezone(ASX_TZ).date()
        due = reminders_due(reminder_dates(self.j), today)
        st = get_state(self.j, "reminders-told")
        told = [str(x) for x in st[0]] if st and isinstance(st[0], list) else []
        out = []
        for key, label, d, left in due:
            # one push per step: 30 days, 7 days, 1 day, the day itself, then once when past
            step = min((t for t in REMINDER_DAYS if t >= left), default=REMINDER_DAYS[0])
            mark = f"{key}:{d.isoformat()}:{step if left >= 0 else 'past'}"
            if mark in told:
                continue
            when = ("expired" if left < 0 else "ends today" if left == 0
                    else f"ends in {left} day{'s' if left != 1 else ''}")  # fmt: skip
            self._say(f"Reminder: {label} {when} ({d:%d %b %Y}). Renew it, then change the "
                      "date in Server > Health > Renewal dates.", "info", "/health")  # fmt: skip
            told.append(mark)
            out.append(mark)
        if out:
            set_state(self.j, "reminders-told", told[-60:], now)
        return out

    def _new_code(self, now: datetime) -> list[str]:
        """BF-D84: one alert for every new commit the server sees on GitHub (not applied)."""
        st = get_state(self.j, "update-available")
        u = st[0] if st and isinstance(st[0], Mapping) else {}
        remote, head = str(u.get("remote") or ""), str(u.get("head") or "")
        if len(remote) != 40 or remote == head or not int(str(u.get("ahead") or 0) or 0):
            return []
        seen = get_state(self.j, "update-told")
        told = [str(x) for x in seen[0]] if seen and isinstance(seen[0], list) else []
        if remote in told:
            return []
        sig = str(u.get("signed") or "unknown")
        sig_txt = SIG_WORDS.get(sig, "signature not checked")
        kind = "page" if sig == "bad" else "info"
        subject = str(u.get("subject") or "")[:120]
        self._say(f"{'PAGE ' if sig == 'bad' else ''}New code on GitHub (not applied): "
                  f"{subject} ({remote[:10]}, {sig_txt}). Nothing changes until you approve it "
                  "in Server > Strategy. If you did not expect new code, do not approve it and "
                  "tell your engineer.", kind, "/strategy")  # fmt: skip
        set_state(self.j, "update-told", [*told[-19:], remote], now)
        return [remote]
