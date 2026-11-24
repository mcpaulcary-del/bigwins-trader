"""The phone app's action endpoints (BF-D39): the owner approves, refuses, vetoes,
pauses, kills, stops, resumes, continues and confirms code changes from the app, with
exactly the rules of the Telegram commands.

Where it runs: inside the trader process (``trader-bf run``), the component that already
owns the owner's commands, as a small HTTP server on the trader's private ``control``
network (port 8081, never published on the host). The read-only dashboard forwards
``/act/...`` requests to it unchanged (it holds no write access itself); this server
checks everything again:

1. **Who**: the ``Tailscale-User-Login`` header (added by ``tailscale serve``) must be in
   ``app.allowed_logins``; an empty list switches every action off (viewing still works).
2. **CSRF**: POST only (GET pages never change anything); a per-session cookie
   (``HttpOnly; SameSite=Strict``) plus a form token bound to the cookie and the log-in
   (HMAC with a per-process key); a cross-site ``Sec-Fetch-Site`` or a foreign ``Origin`` is
   refused.
3. **Same handler**: the action becomes the typed command (``/ok <batch> all <code>``...)
   and is handled by ``ApprovalBot._dispatch`` in the trader's main loop (the HTTP thread
   only queues it), so the TOTP verifier (single use, shared with Telegram), the 15:20
   deadline and the batch checks are the very same code. Nothing here approves anything.
4. **Code lock-out** (BF-D47): 3 wrong codes in 15 minutes lock code actions from the app
   for 15 minutes (journaled, and paged to the owner); every wrong code also leaves a
   quiet inbox note. The count is kept in the journal, cleared only by a correct code, and
   checked when the code is verified (in the main loop); only one code-bearing request
   may be queued at a time. Pause, Kill and Stop stay available.
6. **Signed forwarding** (BF-D46): in production the trader accepts a request only with
   the dashboard's signature (``app_sign``); the log-in comes from the signed headers, and
   the server listens only on its ``control``-network address.
5. **Confirm screens**: every action first shows what will happen ("Approve all 18 orders
   of <batch> - total about A$9,900") before the code is asked; Kill and Stop need the
   "Yes" button of their confirm screen.

Every action is journaled (the safety / approval rows carry the actor ``app:<login>``) and
written to the inbox with its outcome (source ``app:<login>``).
"""

from __future__ import annotations

import contextvars
import hashlib
import hmac
import json
import queue
import secrets
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

from trader.app_sign import NonceCache, verify_proxy
from trader.app_store import (
    FORCE_MARKET,
    FORCE_MIGRATION,
    FORCE_MONTH_END,
    GUARDED_ACTIONS,
    IMMEDIATE,
    SERVER_ACTIONS,
    SHA40,
    STRATEGY,
    add_inbox,
    add_push_sub,
    add_server_job,
    cancel_server_job,
    drop_push_sub,
    get_state,
    push_sub_rows,
    server_job_rows,
    set_state,
)
from trader.approval import APP_CHAT, OPEN_FOR_APPROVAL, ApprovalBot, Incoming, approved_seqs
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.webui import SECURITY_HEADERS, chev, e, icon, page, plural, section

CODE_ACTS = frozenset({"ok", "ap", "rf", "veto", "re", "co", "idmap", "idmap_reject"})
CONFIRM_ACTS = frozenset({"ki", "so", "cancel"})
RISK_REDUCING = frozenset({"pa", "ki", "so", "lock"})
# BF-D64 / BF-D65: low-risk server jobs: a confirm screen, no code (they change nothing the
# trader trades with); still signed for the worker, still only for allowed log-ins
NO_CODE_SERVER = frozenset(
    {"backup_now", "restore_test", "fetch", "hc_ping", "info_archive", "prev_twin"}
)  # allowed even when the app's address changed
ONE_TAP = frozenset({"pa", "st", "here", "lock"})
# BF-D83 (DR review M2): the riskiest actions also need the memorised passphrase (once set)
PASS_ACTS = frozenset({"re", "co", "srv:update", "srv:rollback", "srv:backup_key",
                       "srv:claude_remote", "unlock"})  # fmt: skip
LOCK_STATE = "actions-lock"  # BF-D83: "Lock actions" (approvals and re-arms need Unlock first)
CONFIRM_TITLE = {
    "ok": "Approve orders", "ap": "Approve orders", "rf": "Refuse orders", "veto": "Veto order",
    "re": "Resume trading", "co": "Continue (loss rule)", "idmap": "Code change",
    "idmap_reject": "Undo code change", "pa": "Pause buying", "ki": "Kill switch",
    "so": "Stop (loss rule)", "st": "Status", "cancel": "Cancel job",
    "here": "I'm here", "lock": "Lock actions", "unlock": "Unlock actions",
}  # fmt: skip
# BF-D73: the Kill screen says exactly what /kill does (execution.kill + risk BLOCKS_ALL):
# the KILLED latch refuses every new order (buys and sells) at the send-time check and asks
# the broker to cancel this book's open orders; it never sells anything. /resume with a code
# re-arms (NORMAL). Wording reviewed against the code (REVIEW_AFTER section 3).
KILL_COPY = (
    ("What happens", (
        "The trader sends no orders at all: no buys and no sells. That includes orders you "
        "have approved that have not gone to the broker yet.",
        "It asks the broker to cancel every order of this book that is still open. The result "
        "screen tells you how many were cancelled.",
    )),
    ("What does not happen", (
        "Nothing is sold. Your shares and cash stay as they are.",
        "Fills that have already happened, including part-fills, are kept.",
    )),
    ("To undo", (
        "Controls, then Resume, with your 6-digit code. Nothing else re-arms it: Pause and "
        "Stop leave it killed.",
        "Approved orders are checked when they are due to be sent. Resume before then and they "
        "still go; if the trader is still killed at that time they are dropped and Resume does "
        "not bring them back.",
        "The trader keeps making its month-end decision and will ask for approval, but sends "
        "nothing until you resume.",
    )),
)  # fmt: skip
# per-job confirm titles and button verbs (review item 14)
SRV_TITLE = {
    "restart": ("Restart trader", "Restart now"), "update": ("Update trader", "Update now"),
    "rollback": ("Roll back", "Roll back now"), "check": ("Server checks", "Run checks"),
    "claude_remote": ("Claude remote", "Start it"), "claude_stop": ("Claude remote", "Stop it"),
    "backup_now": ("Back up now", "Back up now"), "restore_test": ("Restore test", "Run the test"),
    "backup_key": ("Recovery key", "Ask for the key"), "fetch": ("Check for updates", "Check now"),
    "hc_ping": ("Healthchecks ping", "Send the ping"),
    "info_archive": ("Collect announcements", "Collect now"),
    "prev_twin": ("Previous-version twin", "Run it now"),
}  # fmt: skip
_ACT: contextvars.ContextVar[str] = contextvars.ContextVar("bw_act", default="")
MAX_FAILS = 3
LOCK = timedelta(minutes=15)
DAY_FAILS = 6  # BF-D58 (N6): slow guessing
DAY_LOCK = timedelta(hours=24)
MAX_DEVICES = 5  # BF-D46 / L3: phones that may receive alerts
BODY_MAX = 16384
WAIT_S = 45.0
COOKIE = "bw_sid"
LOGIN_HEADER = "tailscale-user-login"
ACTION_LABEL = {
    "ok": "Approve", "ap": "Approve batch", "rf": "Refuse batch", "veto": "Veto",
    "re": "Resume", "co": "Continue", "idmap": "Confirm code change",
    "idmap_reject": "Undo code change", "pa": "Pause", "ki": "KILL", "so": "STOP",
    "st": "Status", "cancel": "Cancel the queued job",
    "here": "I'm here", "lock": "Lock actions now", "unlock": "Unlock",
}  # fmt: skip


def asx_open(now: datetime) -> bool:
    """Mon-Fri 10:00-16:15 Sydney (the bigwins menu's guard; holidays count as open)."""
    t = now.astimezone(ASX_TZ)
    return t.weekday() < 5 and time(10, 0) <= t.time() <= time(16, 15)


def header(headers: Mapping[str, str], name: str) -> str:
    return next((v for k, v in headers.items() if k.lower() == name), "").strip()


def same_origin(headers: Mapping[str, str], pinned: str = "") -> bool:
    """Fetch metadata / Origin check for POSTs (CSRF defence in depth). ``pinned``: the
    app's own host name (``app.public_host``, BF-D46); with it the Origin must be exactly
    that host, or, without an Origin, ``Sec-Fetch-Site`` must say same-origin."""
    site = header(headers, "sec-fetch-site").lower()
    if site and site != "same-origin":
        return False
    origin = header(headers, "origin")
    if origin == "null":  # BF-D55: a same-origin POST from a page with a strict referrer policy
        return site == "same-origin"
    if pinned:
        if origin:
            return urlsplit(origin).netloc.lower() == pinned.lower()
        return site == "same-origin"
    if origin:
        host = urlsplit(origin).netloc.lower()
        ok = {header(headers, "host").lower(), header(headers, "x-forwarded-host").lower()}
        return host in ok - {""}
    return True


def _cookie(headers: Mapping[str, str], name: str) -> str:
    for part in header(headers, "cookie").split(";"):
        k, _, v = part.strip().partition("=")
        if k == name:
            return v
    return ""


class _RefusedError(Exception):
    """A request refused before it is queued (the message is shown)."""


@dataclass
class _Req:
    kind: str  # bot | subscribe | unsubscribe | alerts | server | refresh
    login: str
    at: datetime
    data: dict[str, Any]
    done: threading.Event = field(default_factory=threading.Event)
    result: str | None = None


@dataclass
class Control:
    """The action pages and endpoints. ``respond`` is called from the HTTP threads and
    only reads the journal; every change is queued for ``process`` (the trader's main
    loop). ``inline`` (tests) runs the queue at once in the calling thread."""

    journal: Journal
    bot: ApprovalBot | None
    allowed_logins: frozenset[str]
    book: str = "EMG2_18_PAPER"
    notify: Callable[..., int] | None = None  # AppNotifier.notify
    vapid_public: str | None = None
    refresh_prices: Callable[[datetime], str] | None = None
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    market_open: Callable[[datetime], bool] = asx_open
    update_mode: str = "immediate"  # BF-D45 strategy.update_mode
    sessions: Callable[[], Sequence[date]] = field(default=lambda: [])
    demo: bool = False
    inline: bool = False
    proxy_key: bytes | None = None  # BF-D46: app_proxy_key; None = unsigned (tests, demo)
    public_host: str = ""  # BF-D46 / L2: the app's host name for the Origin check
    worker_key: bytes | None = None  # BF-D48: signs server jobs for the host worker
    live: bool = False  # BF-D50: labels from the broker mode (always paper in this build)
    max_devices: int = MAX_DEVICES
    passphrase: str | None = None  # BF-D83: the stored passphrase hash; None = not set
    presence_days: int = 14  # BF-D82: app.presence_days (for the I'm-here answer)
    _key: bytes = field(default_factory=lambda: secrets.token_bytes(32), repr=False)
    _q: queue.Queue[_Req] = field(default_factory=queue.Queue, repr=False)
    _wake: threading.Event = field(default_factory=threading.Event, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _locked_until: datetime | None = None
    _code_busy: bool = False
    _nonces: NonceCache = field(default_factory=NonceCache, repr=False)

    def __post_init__(self) -> None:
        self.allowed_logins = frozenset(x.strip().lower() for x in self.allowed_logins if x.strip())
        # security review L2: the session that asked for the recovery key, and one-time views
        self._key_sessions: dict[str, str] = {}
        self._key_views: dict[str, tuple[str, str, datetime]] = {}
        if not self.demo:
            st = get_state(self.journal, "app-lockout")
            if st and isinstance(st[0], dict) and st[0].get("until"):
                self._locked_until = datetime.fromisoformat(str(st[0]["until"]))

    # ------------------------------------------------------------ main loop side
    def wait(self, seconds: float) -> None:
        """The scheduler's sleep: returns early when an app action arrives."""
        self._wake.wait(seconds)
        self._wake.clear()

    def process(self) -> int:
        self._expire_sealed()  # security review L2: an unclaimed sealed key does not linger
        n = 0
        while True:
            try:
                r = self._q.get_nowait()
            except queue.Empty:
                return n
            self._run(r)
            n += 1

    def _run(self, r: _Req) -> None:
        try:
            r.result = self._execute(r)
            self._presence(r)
        except Exception as ex:  # an action never stops the trader
            r.result = f"failed: {type(ex).__name__}"
        finally:
            if r.data.get("code_bearing"):
                with self._lock:
                    self._code_busy = False
            r.done.set()

    def _submit(self, r: _Req) -> str | None:
        if self.inline:
            self._run(r)
            return r.result
        self._q.put(r)
        self._wake.set()
        return r.result if r.done.wait(WAIT_S) else None

    def _claim_code_slot(self) -> bool:
        """H2: one code-bearing request in the queue at a time."""
        with self._lock:
            if self._code_busy:
                return False
            self._code_busy = True
            return True

    def _presence(self, r: _Req) -> None:
        """BF-D82: an action the server accepted is an owner action (a request refused for
        a wrong code or passphrase, or by a lock, is not)."""
        from trader.presence import record_action

        res = str(r.result or "")
        if self.demo or res.startswith(("refused", "failed", "unknown", "ignored")):
            return
        if r.kind == "bot" and res.startswith("refused"):
            return
        record_action(self.journal, self.clock(), str(r.data.get("shown") or r.kind)[:60])

    def actions_locked(self) -> bool:
        """BF-D83: "Lock actions" is on (code actions refused until Unlock)."""
        if self.demo:
            return False
        st = get_state(self.journal, LOCK_STATE)
        return bool(st and isinstance(st[0], dict) and st[0].get("locked"))

    def _verify_pass(self, r: _Req) -> str | None:
        """BF-D83: the passphrase, checked in the main loop before the code; a wrong one
        counts in the same lock-out as a wrong code (BF-D47 / BF-D58). Never logged."""
        if not r.data.get("needs_pass") or self.passphrase is None:
            return None
        from trader.passphrase import verify

        if self.locked(self.clock()):
            return "refused: code actions are locked (too many wrong codes)"
        if not verify(self.passphrase, str(r.data.get("pp") or "")):
            self._count(True, r.at, r.login)
            return "refused: wrong passphrase"
        return None

    def telegram_gate(self, cmd: str) -> str | None:
        """BF-D83: Telegram (when on) follows the lock and the passphrase rule: with a
        passphrase set, re-arming is done in the app only (a passphrase is never typed into a
        chat); while actions are locked, no code command is taken."""
        coded = {"/ok", "/veto", "/approve", "/refuse", "/resume", "/continue", "/idmap",
                 "/idmap_reject"}  # fmt: skip
        if cmd in coded and self.actions_locked():
            return "refused: actions are locked in the app; unlock there (Controls > Unlock)"
        if cmd in ("/resume", "/continue") and self.passphrase is not None:
            return "refused: with a passphrase set, re-arm in the app (Controls > Resume)"
        return None

    def locked(self, now: datetime) -> datetime | None:
        with self._lock:
            u = self._locked_until
        return u if u is not None and now < u else None

    def _execute(self, r: _Req) -> str:  # noqa: PLR0911, PLR0912, PLR0915 - one branch per kind
        src = f"app:{r.login}"
        if r.kind == "bot":
            if self.bot is None:
                return "the trader's command handler is not running"
            coded = bool(r.data.get("code_bearing"))
            if coded and self.locked(self.clock()):  # checked again where the code is used
                return "refused: code actions are locked (too many wrong codes)"
            if coded and self.actions_locked():  # BF-D83: checked again in the main loop
                return "refused: actions are locked; unlock first (Controls > Unlock)"
            why = self._verify_pass(r)
            if why is not None:
                return why
            before = self.bot.verifier.failures
            ok_before = self.bot.verifier.successes
            m = Incoming(APP_CHAT, str(r.data["command"]), r.at, source="app", login=r.login)
            reply = self.bot.handle(m)
            shown = str(r.data["shown"])
            add_inbox(self.journal, self.clock(), "action", f"You (app): {shown}"[:200],
                      f"{shown}\n-> {reply}", "/inbox", src, "off")  # fmt: skip
            if coded:  # BF-D56 (N2): only a code the verifier actually checked counts
                if self.bot.verifier.failures > before:
                    self._count(True, r.at, r.login)
                elif self.bot.verifier.successes > ok_before:
                    self._count(False, r.at, r.login)
            return reply
        if r.kind == "subscribe":
            if self.actions_locked():
                return "refused: actions are locked; unlock first (Controls > Unlock)"
            return self._subscribe_exec(r, src)
        if r.kind in ("here", "lock", "unlock"):
            return self._lock_exec(r, src)
        if r.kind == "unsubscribe":
            return "ok" if drop_push_sub(self.journal, str(r.data["endpoint"])) else "not found"
        if r.kind == "unsubscribe_all":
            n = 0
            for sub in push_sub_rows(self.journal):
                n += drop_push_sub(self.journal, str(sub["endpoint"]))
            add_inbox(self.journal, self.clock(), "action", "You (app): alerts off on all devices",
                      f"{n} device(s) switched off", "/settings", src, "off")  # fmt: skip
            return f"alerts switched off on {n} device(s)"
        if r.kind == "cancel":
            jid = int(r.data["job"])
            ok = cancel_server_job(self.journal, jid, r.login, r.at)
            reply = f"server job {jid} cancelled" if ok else f"server job {jid} is not queued"
            add_inbox(self.journal, self.clock(), "action", f"You (app): cancel job {jid}",
                      reply, "/server", src, "off")  # fmt: skip
            return reply
        if r.kind == "alerts":
            set_state(self.journal, "alerts", dict(r.data), r.at)
            add_inbox(self.journal, self.clock(), "action", "You (app): alert settings changed",
                      json.dumps(r.data), "/settings", src, "off")  # fmt: skip
            return "alert settings saved"
        if r.kind == "reminders":  # BF-D86: renewal dates (reminders only; nothing trades)
            set_state(self.journal, "reminders", dict(r.data), r.at)
            add_inbox(self.journal, self.clock(), "action", "You (app): renewal dates changed",
                      json.dumps(r.data), "/health", src, "off")  # fmt: skip
            return "renewal dates saved"
        if r.kind == "costs":  # BF-D76: display only (the scoreboard and Costs screens)
            # BF-D81 (N1): each change applies from the day it was made; history is kept
            st = get_state(self.journal, "running-costs")
            old = st[0] if st and isinstance(st[0], dict) else {}
            hist = list(old.get("history") or []) if isinstance(old.get("history"), list) else []
            if not hist and any(k in old for k in ("server", "data", "other")):
                hist = [{**{k: old.get(k, "0") for k in ("server", "data", "other")},
                         "from": "1970-01-01"}]  # fmt: skip
            frm = r.at.astimezone(ASX_TZ).date().isoformat()
            hist = [h for h in hist if isinstance(h, dict) and h.get("from") != frm]
            hist.append({**r.data, "from": frm} if r.data else {"cleared": True, "from": frm})
            set_state(self.journal, "running-costs", {"history": hist[-24:]}, r.at)
            add_inbox(self.journal, self.clock(), "action", "You (app): running costs changed",
                      json.dumps(r.data), "/costs", src, "off")  # fmt: skip
            return "running costs saved"
        if r.kind == "server_nocode":
            act = str(r.data["action"])
            if act not in NO_CODE_SERVER:
                return "refused: this server job needs your code"
            jid = add_server_job(self.journal, act, 0, r.login, r.at, "", self.worker_key)
            reply = f"server job {jid} '{act}' queued: the server runs it within a minute"
            add_inbox(self.journal, self.clock(), "action", f"You (app): {r.data['shown']}"[:200],
                      reply, "/server", src, "off")  # fmt: skip
            return reply
        if r.kind == "reveal":
            return self._reveal(r)
        if r.kind in ("server", "refresh"):
            return self._server(r, src)
        return "unknown request"

    def _verify_code(self, r: _Req) -> str | None:
        """Lock check, code check and failure count, all at verification time (H2)."""
        if self.locked(self.clock()):
            return "refused: code actions are locked (too many wrong codes)"
        if self.bot is None or not self.bot.verifier.verify(str(r.data["code"]), r.at):
            self._count(True, r.at, r.login)
            return "refused: invalid or reused code"
        self._count(False, r.at, r.login)
        return None

    def _subscribe_exec(self, r: _Req, src: str) -> str:
        d = r.data
        why = self._verify_code(r)
        if why is not None:
            return why
        subs = push_sub_rows(self.journal)
        if len(subs) >= self.max_devices and all(x["endpoint"] != d["endpoint"] for x in subs):
            return (f"refused: alerts are already on for {len(subs)} devices (the limit); "
                    "turn alerts off on all devices first")  # fmt: skip
        add_push_sub(self.journal, d["endpoint"], d["p256dh"], d["auth"], r.login, r.at)
        add_inbox(self.journal, self.clock(), "action", "You (app): alerts on for a new device",
                  f"device {str(d['endpoint'])[:40]}...", "/settings", src, "off")  # fmt: skip
        if self.notify is not None:
            self.notify("Alerts are on for this phone. Approvals and PAGE alerts arrive "
                        "here at high priority.", "info", "/settings", src, True)  # fmt: skip
        return "ok"

    def _lock_exec(self, r: _Req, src: str) -> str:
        """BF-D82 I'm here; BF-D83 Lock (one tap, risk-reducing) and Unlock (code, and the
        passphrase when set)."""
        at = self.clock()
        if r.kind == "here":
            until = (at + timedelta(days=self.presence_days)).astimezone(ASX_TZ)
            reply = (f"Thank you: noted. The automatic pause would now start on {until:%a %d %b} "
                     "if there is no other action before then.")  # fmt: skip
            add_inbox(self.journal, at, "action", "You (app): I'm here", reply, "/health", src,
                      "off")  # fmt: skip
            return reply
        if r.kind == "lock":
            set_state(self.journal, LOCK_STATE, {"locked": True, "by": r.login}, at)
            reply = ("Actions locked: approvals, refusals, re-arming and server jobs are refused "
                     "until you unlock (Controls > Unlock, with your code"
                     + (" and passphrase" if self.passphrase else "") + "). Pause, Kill and Stop "
                     "still work.")  # fmt: skip
            add_inbox(self.journal, at, "action", "You (app): actions locked", reply, "/act", src,
                      "off")  # fmt: skip
            return reply
        why = self._verify_pass(r) or self._verify_code(r)
        if why is not None:
            return why
        set_state(self.journal, LOCK_STATE, {"locked": False, "by": r.login}, at)
        add_inbox(self.journal, at, "action", "You (app): actions unlocked",
                  "Approvals and re-arming work again.", "/act", src, "off")  # fmt: skip
        return "unlocked: approvals and re-arming work again"

    def _server(self, r: _Req, src: str) -> str:
        why = None
        if self.actions_locked():
            why = "refused: actions are locked; unlock first (Controls > Unlock)"
        why = why or self._verify_pass(r) or self._verify_code(r)
        if why is not None:
            reply = why
        elif r.kind == "refresh":
            reply = self.refresh_prices(r.at) if self.refresh_prices else "no price refresher"
        else:
            act = str(r.data["action"])
            jid = add_server_job(self.journal, act, int(r.data["force"]), r.login, r.at,
                                 str(r.data.get("commit") or ""), self.worker_key)  # fmt: skip
            reply = (
                f"server job {jid} '{act}' queued: the server runs it within a minute "
                "(Server tab shows progress)"
            )
        shown = str(r.data["shown"])
        add_inbox(self.journal, self.clock(), "action", f"You (app): {shown}"[:200],
                  f"{shown}\n-> {reply}", "/server", src, "off")  # fmt: skip
        return reply

    def _fails(self) -> list[datetime]:
        st = get_state(self.journal, "app-code-fails")
        raw = st[0] if st and isinstance(st[0], list) else []
        return [datetime.fromisoformat(str(x)) for x in raw]

    def _count(self, wrong: bool, at: datetime, login: str) -> None:
        """BF-D47 / BF-D58 lock-out (main loop only): the wrong codes of the last 24 hours
        are kept in the journal (``app-code-fails``) and cleared only by a code the verifier
        accepted. 3 in 15 minutes lock code actions for 15 minutes; 6 in 24 hours (slow
        guessing) lock them for 24 hours at high priority. Each wrong code before a lock
        leaves a quiet inbox note. Pause, Kill and Stop never need a code."""
        if not wrong:
            if self._fails():
                set_state(self.journal, "app-code-fails", [], at)
            return
        fails = [t for t in self._fails() if at - t < DAY_LOCK] + [at]
        recent = [t for t in fails if at - t < LOCK]
        page_text = None
        with self._lock:
            if len(fails) >= DAY_FAILS:
                self._locked_until = at + DAY_LOCK
                fails = []
                page_text = (
                    f"PAGE HIGH PRIORITY app code actions LOCKED for 24 hours (until "
                    f"{self._locked_until.astimezone(ASX_TZ):%a %H:%M} Sydney): {DAY_FAILS} wrong "
                    f"codes in 24 hours (log-in {login}). Someone may be guessing. Pause, Kill "
                    "and Stop still work; check the server."
                )
            elif len(recent) >= MAX_FAILS:
                self._locked_until = at + LOCK
                page_text = (
                    f"PAGE app code actions LOCKED until "
                    f"{self._locked_until.astimezone(ASX_TZ):%H:%M} Sydney: {MAX_FAILS} wrong "
                    f"codes in 15 minutes (log-in {login}). Pause, Kill and Stop still work. "
                    "If this was not you, use Kill and check the server."
                )
        set_state(self.journal, "app-code-fails", [t.isoformat() for t in fails], at)
        if page_text is None:
            add_inbox(self.journal, at, "info", "A wrong code was entered in the app",
                      f"Wrong 6-digit code from log-in {login} ({len(recent)} of {MAX_FAILS} in "
                      f"15 minutes, {len(fails)} of {DAY_FAILS} in 24 hours, before code actions "
                      "lock).", "/inbox", f"app:{login}", "off")  # fmt: skip
            return
        assert self._locked_until is not None
        set_state(self.journal, "app-lockout",
                  {"until": self._locked_until.isoformat(), "login": login}, at)  # fmt: skip
        if self.notify is not None:
            self.notify(page_text, "page", "/inbox")
        else:
            add_inbox(self.journal, at, "page", page_text[:200], page_text, "/inbox")

    # ------------------------------------------------------------ HTTP side
    def respond(  # noqa: PLR0911, PLR0912 - one return per route
        self, method: str, path: str, headers: Mapping[str, str], body: bytes = b""
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs = dict(SECURITY_HEADERS)
        url = urlsplit(path)
        p = url.path.rstrip("/") or "/act"
        qs = {k: v[-1] for k, v in parse_qs(url.query).items()}
        if self.proxy_key is not None:  # BF-D46: only signed requests (the demo signs too)
            signed = verify_proxy(self.proxy_key, headers, method, path, body, self._nonces)
            if signed is None:
                return 403, hdrs, b"unsigned or stale request\n"
            login = "demo" if self.demo else signed["login"]
            headers = {"Cookie": header(headers, "cookie"), "Origin": signed["origin"],
                       "Sec-Fetch-Site": signed["site"], "Host": signed["host"],
                       "X-CSRF-Token": header(headers, "x-csrf-token")}  # fmt: skip
        else:
            login = "demo" if self.demo else header(headers, LOGIN_HEADER).lower()
        sid = _cookie(headers, COOKIE)
        if len(sid) < 20:
            sid = secrets.token_urlsafe(24)
            hdrs["Set-Cookie"] = (
                f"{COOKIE}={sid}; Path=/act; HttpOnly; SameSite=Strict; Secure; Max-Age=86400"
            )
        token = self._token(sid, login)
        if method in ("GET", "HEAD"):
            return self._get(p, qs, login, token, hdrs)
        if method != "POST":
            hdrs["Allow"] = "GET, HEAD, POST"
            return 405, hdrs, b"method not allowed\n"
        why = self._post_refusal(headers, login, sid, body)
        if why is not None:
            return self._html(403, hdrs, "Refused", section("Not done", f"<p>{e(why)}</p>"))
        if p == "/act/push/subscribe":
            return self._subscribe(login, body, hdrs)
        form = {k: v[-1] for k, v in parse_qs(body.decode("utf-8", "replace")).items()}
        if p == "/act/do":
            if form.get("a") == "srv:backup_key":  # security review L2: this session only
                self._key_sessions[login] = hashlib.sha256(sid.encode()).hexdigest()
            _ACT.set(form.get("a", ""))  # the result page's way back (presentation)
            return self._do(form, login, hdrs)
        if p == "/act/alerts":
            return self._alerts_post(form, login, hdrs)
        if p == "/act/costs":
            return self._costs_post(form, login, hdrs)
        if p == "/act/reminders":  # BF-D86
            return self._reminders_post(form, login, hdrs)
        if p == "/act/backup-key":  # BF-D64: one view of the sealed recovery key
            if self.demo:
                return self._result(hdrs, "DEMO: there is no key to show.", True)
            want = self._key_sessions.get(login)
            if not want or not hmac.compare_digest(want, hashlib.sha256(sid.encode()).hexdigest()):
                return self._result(hdrs, "Not shown: open the key on the phone (and in "
                                    "the browser session) that asked the server for it.",
                                    False)  # fmt: skip
            r = self._submit(_Req("reveal", login, self.clock(), {}))
            if not r:
                return self._key_page(hdrs, r)
            # security review L2: POST-redirect-GET to a one-time view (a refresh re-POSTs
            # nothing and shows nothing again)
            t = secrets.token_urlsafe(24)
            self._key_views[t] = (r, login, self.clock())
            self._key_sessions.pop(login, None)
            hdrs["Location"] = f"/act/backup-key/view?t={t}"
            return 303, hdrs, b""
        if p == "/act/push/off":
            r = self._submit(
                _Req("unsubscribe", login, self.clock(), {"endpoint": form.get("endpoint", "")})
            )
            return self._html(200, hdrs, "Alerts", section("Alerts", f"<p>{e(r or 'queued')}</p>"))
        if p == "/act/push/off-all":  # risk-reducing: no code
            if self.demo:
                return self._result(hdrs, "DEMO: nothing was done.", True)
            r = self._submit(_Req("unsubscribe_all", login, self.clock(), {}))
            return self._result(hdrs, r or "queued", True)
        return 404, hdrs, b"not found\n"

    def _token(self, sid: str, login: str) -> str:
        return hmac.new(self._key, f"{sid}|{login}".encode(), hashlib.sha256).hexdigest()[:40]

    def _post_refusal(
        self, headers: Mapping[str, str], login: str, sid: str, body: bytes
    ) -> str | None:
        if not self.demo and not self.allowed_logins:
            return "Actions are off: no log-in is allowed yet (app.allowed_logins is empty)."
        if not self.demo and login not in self.allowed_logins:
            return "This Tailscale log-in may not act."
        if len(body) > BODY_MAX:
            return "request too large"
        form = parse_qs(body.decode("utf-8", "replace")) if body[:1] != b"{" else {}
        why = self._origin_refusal(headers, (form.get("a") or [""])[-1])
        if why is not None:
            return why
        sent = header(headers, "x-csrf-token")
        if not sent:
            sent = (form.get("csrf") or [""])[-1]
        if not _cookie(headers, COOKIE) or not hmac.compare_digest(sent, self._token(sid, login)):
            return "missing or stale form token: reload the page and try again"
        return None

    def _origin_refusal(self, headers: Mapping[str, str], action: str) -> str | None:
        """BF-D55 (N1, N1b): the Origin must be the app's own host: ``app.public_host``
        when it is set, else the host the dashboard received (signed). ``Origin: null`` is
        accepted only with ``Sec-Fetch-Site: same-origin``. When the request came from a
        real host that is not the pinned name (the server's Tailscale name changed), only
        Pause, Kill and Stop go through, with a message how to fix the address."""
        site = header(headers, "sec-fetch-site").lower()
        if site and site != "same-origin":
            return "cross-site request refused"
        req_host = header(headers, "host").lower()
        if same_origin(headers, self.public_host or req_host):
            return None
        origin = header(headers, "origin")
        o_host = urlsplit(origin).netloc.lower() if origin and origin != "null" else ""
        if self.public_host and o_host and o_host == req_host:
            if action in RISK_REDUCING:
                return None
            return (
                f"The app's address changed (this page came from {o_host}, the server expects "
                f"{self.public_host}). On the server run bigwins option 11 (Allow my phone "
                "to act) again, then restart. Pause, Kill and Stop still work meanwhile."
            )
        return "cross-site request refused"

    def _html(
        self,
        status: int,
        hdrs: dict[str, str],
        title: str,
        body: str,
        active: str = "",
        confirm: bool = False,
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs["Content-Type"] = "text/html; charset=utf-8"
        waiting = 0 if confirm else sum(n for _, n, _ in self._safe_waiting())
        latest = 0 if confirm else self._latest_inbox()
        out = page(title, body, active, demo=self.demo, refresh=False, live=self.live,
                   confirm=confirm, waiting=waiting, latest_inbox=latest)  # fmt: skip
        return status, hdrs, out.encode()

    def _safe_waiting(self) -> list[tuple[str, int, str]]:
        try:
            return self.waiting_batches(self.clock())
        except Exception:
            return []

    def _latest_inbox(self) -> int:
        from trader.app_store import inbox_rows

        try:
            rows = inbox_rows(self.journal, 1)
        except Exception:
            return 0
        return int(rows[0]["id"]) if rows else 0

    # ------------------------------------------------------------ GET pages
    def _get(  # noqa: PLR0911 - one return per page
        self, p: str, qs: dict[str, str], login: str, token: str, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        if not self.demo and not self.allowed_logins:
            return self._html(200, hdrs, "Actions off", section("Actions are off", ACTIONS_OFF))
        if not self.demo and login not in self.allowed_logins:
            msg = (
                f"<p>Your Tailscale log-in <b>{e(login or '(none)')}</b> is not on the list "
                "of log-ins allowed to act (<code>app.allowed_logins</code>). Viewing still "
                "works.</p>"
            )
            return self._html(403, hdrs, "Not allowed", section("Not allowed", msg))
        if p == "/act":
            return self._html(200, hdrs, "Controls", self._controls(token), "server")
        if p == "/act/confirm":
            title = CONFIRM_TITLE.get(qs.get("a", ""), "Confirm")
            if qs.get("a", "").startswith("srv:"):
                title = SRV_TITLE.get(qs.get("a", "")[4:], ("Server job", ""))[0]
            if qs.get("a") == "refresh":
                title = "Refresh prices"
            body = f'<div class="confirm">{self._confirm(qs, token)}</div>'
            return self._html(200, hdrs, title, body, confirm=True)
        if p == "/act/alerts":
            return self._html(200, hdrs, "Alerts", self._alerts_page(token), "server")
        if p == "/act/costs":  # BF-D76: the fixed running costs (no code: adds no risk)
            return self._html(200, hdrs, "Running costs", self._costs_page(token), "server")
        if p == "/act/reminders":  # BF-D86: renewal dates (no code: adds no risk)
            return self._html(200, hdrs, "Renewal dates", self._reminders_page(token), "server")
        if p == "/act/backup-key":
            return self._html(200, hdrs, "Recovery key", self._key_intro(token), "server")
        if p == "/act/backup-key/view":
            v = self._key_views.pop(qs.get("t", ""), None)  # one view only
            if v is None or v[1] != login or (self.clock() - v[2]).total_seconds() > 120:
                return self._key_page(hdrs, None)
            return self._key_page(hdrs, v[0])
        return 404, hdrs, b"not found\n"

    def _expire_sealed(self) -> None:
        """Clear a sealed recovery key the owner did not claim within its time (L2)."""
        from trader.app_store import get_state, set_state
        from trader.backups import REVEAL_TTL_S

        st = get_state(self.journal, "backup-key-sealed")
        if (st and isinstance(st[0], dict) and st[0].get("sealed")
                and (self.clock() - st[1]).total_seconds() > REVEAL_TTL_S):  # fmt: skip
            set_state(self.journal, "backup-key-sealed", {}, self.clock())

    # ------------------------------------------------------------ BF-D64 recovery key
    def _key_intro(self, token: str) -> str:
        from trader.backups import take_sealed

        fresh = None if self.demo else take_sealed(self.journal, self.clock())
        if fresh is None:
            return ("<h1>Backup recovery key</h1>" + section("", (
                "<p>The key that unlocks your backups is kept only on the server. To see it "
                "once, ask the server for it (needs your 6-digit code); then come back here "
                "within 10 minutes.</p>"
                '<a class="btn wide" href="/act/confirm?a=srv:backup_key">Ask the server for '
                "the key</a>")))  # fmt: skip
        return ("<h1>Backup recovery key</h1>" + section("", (
            "<p class='note'>The server has sent the key. It is shown <b>once</b>: have your "
            "password manager open, then tap the button.</p>"
            '<form method="post" action="/act/backup-key"><input type="hidden" name="csrf" '
            f'value="{e(token)}"><button class="btn wide">Show the key now</button>'
            "</form>")))  # fmt: skip

    def _reveal(self, r: _Req) -> str:
        from trader.backups import clear_sealed, take_sealed, unseal

        got = take_sealed(self.journal, self.clock())
        if got is None or self.worker_key is None:
            return ""
        key = unseal(self.worker_key, str(got["sealed"]))
        clear_sealed(self.journal, self.clock(), r.login, str(got.get("fp", "")))  # one view only
        add_inbox(self.journal, self.clock(), "action", "You (app): backup recovery key shown",
                  "The recovery key was shown once in the app (the key itself is never in "
                  "the inbox).", "/backups", f"app:{r.login}", "off")  # fmt: skip
        return key.decode("utf-8", "replace").strip() if key else ""

    def _key_page(self, hdrs: dict[str, str], key: str | None) -> tuple[int, dict[str, str], bytes]:
        if not key:
            return self._result(hdrs, "No key to show (it was already shown, or more than 10 "
                                "minutes passed). Ask the server for it again.", False)  # fmt: skip
        lines = [x for x in key.splitlines() if x.startswith("AGE-SECRET-KEY-")]
        body = ("<h1>Backup recovery key</h1>" + section("", (
            "<p class='note'><b>Save this in your password manager now.</b> It is shown only "
            "this once. Anyone with it and your backup files can read your backups.</p>"
            f"<p><code style='word-break:break-all;font-size:15px'>{e(lines[0] if lines else key)}"
            "</code></p><p class='small muted'>To see it again, ask the server again (needs "
            "your code).</p>")))  # fmt: skip
        return self._html(200, hdrs, "Recovery key", body, "server")

    def _form(self, token: str, fields: Mapping[str, str], inner: str, cls: str = "") -> str:
        hidden = "".join(
            f'<input type="hidden" name="{e(k)}" value="{e(v)}">' for k, v in fields.items() if v
        )
        return (
            f'<form method="post" action="/act/do" class="{cls}">'
            f'<input type="hidden" name="csrf" value="{e(token)}">{hidden}{inner}</form>'
        )

    def _controls(self, token: str) -> str:
        now = self.clock()
        lvl = self.journal.safety_level().value
        lock = self.locked(now)
        tone = (
            "ok"
            if lvl == "NORMAL"
            else ("bad" if lvl in ("KILLED", "HALTED_INTEGRITY") else "wait")
        )
        out = [
            f'<h1>Controls</h1><p class="statusline"><span class="sd {tone}"></span>Safety now: '
            f"<b>{e(lvl)}</b></p>"
        ]
        if self.demo:
            out.append(
                '<p class="note info">Demo: buttons here are simulated; nothing is changed.</p>'
            )
        if lock:
            out.append(
                f'<p class="note">Code actions are locked until {lock.astimezone(ASX_TZ):%H:%M} '
                "(too many wrong codes). Pause, Kill and Stop still work.</p>"
            )
        locked = self.actions_locked()
        if locked:  # BF-D83
            out.append(
                f'<a class="note bad notelink" href="/act/confirm?a=unlock">{icon("lock")}'
                "Actions are locked: approvals and re-arming are refused. Tap to unlock.</a>"
            )

        def row(href: str, ic: str, label: str, desc: str, cls: str = "") -> str:
            return (
                f'<li><a class="mrow {cls}" href="{href}">{icon(ic)}<span class="mt">'
                f'<span class="ml">{e(label)}</span><span class="md">{e(desc)}</span></span>'
                f"{chev()}</a></li>"
            )

        pause = self._form(token, {"a": "pa"}, '<button class="btn sm warnb">Pause</button>')
        out.append(section(
            "Stop or slow",
            '<ul class="menu"><li><div class="mrow">' + icon("pause")
            + '<span class="mt"><span class="ml">Pause buying</span><span class="md">One tap: buys '
            "stop, registered sells go on.</span></span>" + pause + "</div></li>"
            + row("/act/confirm?a=so", "minus-circle", "Stop (loss rule)",
                  "Keeps buys paused; sells go on")
            + row("/act/confirm?a=ki", "stop-octagon", "Kill switch",
                  "Stops all orders and cancels open ones", "dangerrow")
            + "</ul>",
        ))  # fmt: skip
        status = self._form(
            token, {"a": "st"},
            f'<button class="mrow">{icon("activity")}<span class="mt"><span class="ml">Status'
            '</span><span class="md">Shows the safety level</span></span></button>',
        )  # fmt: skip
        out.append(section(
            "Re-arm · needs your code" + (" and passphrase" if self.passphrase else ""),
            '<ul class="menu">'
            + row("/act/confirm?a=re", "play", "Resume", "Back to normal trading")
            + row("/act/confirm?a=co", "check", "Continue (loss rule)",
                  "Stage 3 written confirmation")
            + "</ul>",
        ))  # fmt: skip
        waiting = self.waiting_batches(now)
        rows = "".join(
            f'<li><a class="mrow" href="/act/confirm?a=ok&amp;b={e(b)}&amp;n=all">{icon("clock")}'
            f'<span class="mt"><span class="ml">{plural(n, "order")} · by {e(dl)}</span>'
            f'<span class="md mono">{e(b)}</span></span>{chev()}</a></li>'
            for b, n, dl in waiting
        )
        out.append(section(
            "Waiting for approval",
            f'<ul class="menu">{rows}</ul>' if rows else '<p class="muted">Nothing waiting.</p>',
        ))  # fmt: skip
        lock_row = (
            row("/act/confirm?a=unlock", "lock", "Unlock actions",
                "Needs your code" + (" and passphrase" if self.passphrase else ""))
            if locked else
            row("/act/confirm?a=lock", "lock", "Lock actions",
                "One tap: approvals and re-arming need Unlock first")
        )  # fmt: skip
        out.append(section(
            "Phone safety",
            '<ul class="menu">' + lock_row
            + row("/act/confirm?a=here", "user-check", "I'm here",
                  f"Resets the {self.presence_days}-day automatic pause")
            + "</ul>",
        ))  # fmt: skip
        out.append(section(
            "More",
            '<ul class="menu">'
            + row("/act/alerts", "bell", "Alerts on this phone", "Turn on, choose which")
            + '<li><details class="srow"><summary class="mrow">' + icon("swap")
            + '<span class="mt"><span class="ml">Share code changes</span><span class="md">'
            "Confirm or record a code change</span></span>" + chev() + "</summary>"
            f'<div class="srbody">{self._idmap_html()}</div></details></li>'
            + row("/server", "server", "Server", "Health, jobs and updates")
            + f"<li>{status}</li></ul>",
        ))  # fmt: skip
        return "".join(out)

    def _idmap_html(self) -> str:
        recs = [r for r in self.journal.identity_records().values() if r["status"] == "PROPOSED"]
        items = "".join(
            f"<li><b>{e(r['old_code'])} → {e(r['new_code'])}</b>"
            + (f" ratio {e(r['ratio'])}" if r.get("ratio") else "")
            + f'<div class="btns"><a class="btn sec" href="/act/confirm?a=idmap&amp;old='
            f'{e(r["old_code"])}&amp;new={e(r["new_code"])}">Confirm</a>'
            f'<a class="btn sec" href="/act/confirm?a=idmap_reject&amp;old={e(r["old_code"])}">'
            "Undo</a></div></li>"
            for r in recs
        )
        manual = (
            '<form method="get" action="/act/confirm"><input type="hidden" name="a" value="idmap">'
            '<div class="btns"><input class="field" aria-label="Old code" '
            'name="old" placeholder="Old code" maxlength="6" required>'
            '<input class="field" aria-label="New code" name="new" '
            'placeholder="New code" maxlength="6" required></div>'
            '<input class="field" aria-label="Share ratio" name="ratio" '
            'placeholder="Ratio, e.g. 1:10 (optional)" maxlength="12">'
            '<button class="btn sec wide" style="margin-top:8px" aria-label="Record a code change">'
            "Record a code change</button>"
            "</form>"
        )
        return (f'<ul class="list">{items}</ul>' if items else
                '<p class="muted small">No code change waiting.</p>') + manual  # fmt: skip

    def waiting_batches(self, now: datetime) -> list[tuple[str, int, str]]:
        """(batch, orders waiting, deadline) of the book's batches still open now."""
        out = []
        dl = self.bot.approval_deadline if self.bot else "15:20"
        for bid, xd in self.journal.batches_of(self.book):
            b = self.journal.batch(bid)
            if b is None or b["approval_mode"] == "auto" or xd is None:
                continue
            h, mm = (int(x) for x in dl.split(":"))
            if now > datetime.combine(xd, time(h, mm), ASX_TZ):
                continue
            if any(a["action"] == "REFUSE" for a in self.journal.approvals(bid)):
                continue
            ok = approved_seqs(self.journal, bid)
            n = sum(
                1 for it, st in self.journal.intents_of(bid)
                if st in OPEN_FOR_APPROVAL and it.seq not in ok
            )  # fmt: skip
            if n:
                out.append((bid, n, f"{xd:%a %d %b} {dl}"))
        return out

    def _preview(  # noqa: PLR0911 - one refusal per rule
        self, qs: Mapping[str, str], now: datetime
    ) -> tuple[str | None, str, str]:
        a = qs.get("a", "")
        if a == "cancel":  # BF-D49: risk-reducing, confirm only
            job = qs.get("job", "")
            row = next((r for r in server_job_rows(self.journal, 50)
                        if job.isdigit() and int(job) == r["id"]), None)  # fmt: skip
            if row is None or row["status"] != "PENDING":
                return f"server job {job} is not queued", "", ""
            return None, "", f"cancel queued server job {job} ({row['action']})"
        if a.startswith("srv:"):
            act = a[4:]
            if act not in SERVER_ACTIONS:
                return "unknown server action", "", ""
            return None, "", SERVER_ACTIONS[act]
        if a == "refresh":
            return None, "", "refresh the price store now (the day's EODHD bulk file)"
        if a == "here":  # BF-D82
            return (
                None,
                "",
                (
                    f"tell the server you are here (the automatic pause after "
                    f"{self.presence_days} days without an owner action starts again)"
                ),
            )
        if a == "lock":  # BF-D83
            return None, "", ("lock approvals, refusals, re-arming and server jobs until you "
                              "unlock with your code" + (" and passphrase" if self.passphrase
                                                         else ""))  # fmt: skip
        if a == "unlock":
            if not self.actions_locked():
                return "the actions are not locked", "", ""
            return None, "", "unlock approvals and re-arming"
        args = [x for x in (qs.get("b", ""), qs.get("n", "")) if x]
        if a in ("idmap", "idmap_reject"):
            args = [x for x in (qs.get("old", ""), qs.get("new", ""), qs.get("ratio", "")) if x]
            if a == "idmap_reject":
                args = args[:1]
        if self.bot is None:
            return "the trader's command handler is not running", "", ""
        return self.bot.preview(a, args, now)

    def _summary(self, qs: Mapping[str, str]) -> str:
        """The orders an approval / refusal covers: a labelled table with totals."""
        b, n = qs.get("b", ""), qs.get("n", "")
        if qs.get("a") not in ("ok", "ap", "rf", "veto") or not b:
            return ""
        its = self.journal.intents_of(b)
        if n and n != "all":
            its = [(it, st) for it, st in its if str(it.seq) == n]
        buys = sum((Decimal(str(it.value_at_ref)) for it, _ in its if it.side.value == "BUY"),
                   Decimal(0))  # fmt: skip
        sells = sum((Decimal(str(it.value_at_ref)) for it, _ in its if it.side.value == "SELL"),
                    Decimal(0))  # fmt: skip
        rows = "".join(
            f"<tr><td class='sub'>{it.seq}</td><td><span class='side'>"
            f"{e(it.side.value.capitalize())}</span></td><td><b>{e(it.entity)}</b></td>"
            f"<td class='r'>{it.qty:,}</td><td class='r'>≤ {_px(it.limit_price)}</td>"
            f"<td class='r'>${Decimal(str(it.value_at_ref)):,.0f}</td></tr>"
            for it, _ in its
        )
        net = sells - buys
        sign = "+" if net >= 0 else "\u2212"
        return (
            '<div class="tscroll"><table class="otable"><thead><tr><th>#</th><th>Side</th>'
            '<th>Share</th><th class="r">Qty</th><th class="r">Limit</th><th class="r">≈ Value</th>'
            f"</tr></thead><tbody>{rows}"
            f'<tr class="tot"><td></td><td colspan="3">Sells ≈ ${sells:,.0f} · Buys ≈ ${buys:,.0f}'
            f'</td><td class="r" colspan="2">Net cash {"in" if net >= 0 else "out"} '
            f"{sign}${abs(net):,.0f}</td></tr>"
            "</tbody></table></div>"
            '<p class="caption">Values at the reference prices; each order is sent with the limit '
            "shown.</p>"
        )

    def _deadline(self, b: str) -> str:
        now = self.clock()
        for bid, _n, dl in self.waiting_batches(now):
            if bid == b:
                return dl
        return ""

    def _confirm(self, qs: Mapping[str, str], token: str) -> str:  # noqa: PLR0911, PLR0912, PLR0915
        now = self.clock()
        a = qs.get("a", "")
        why, _cmd, what = self._preview(qs, now)
        if why is not None:
            return section(
                "Cannot do this", f"<p>{e(why)}</p><a class='btn sec wide' href='/act'>Back</a>"
            )
        fields = {k: qs.get(k, "") for k in ("a", "b", "n", "old", "new", "ratio", "job")}
        if a == "srv:update":  # BF-D48: the exact commit shown here is what gets applied
            fields["commit"] = str(self.update_state().get("remote") or "")
        cancel = '<a class="btn sec wide" style="margin-top:8px" href="/act">Cancel</a>'
        demo = (
            '<p class="note info">Demo: nothing will be sent or changed. The result is '
            "simulated.</p>"
            if self.demo else ""
        )  # fmt: skip
        head = demo
        b = qs.get("b", "")
        if a in ("ok", "ap", "rf", "veto") and b:
            its = self.journal.intents_of(b)
            if qs.get("n") and qs.get("n") != "all":
                its = [(it, st) for it, st in its if str(it.seq) == qs.get("n")]
            total = sum((Decimal(str(it.value_at_ref)) for it, _ in its), Decimal(0))
            verb = {"ok": "approving", "ap": "approving", "rf": "refusing", "veto": "vetoing"}[a]
            dl = self._deadline(b)
            head += (
                f'<p class="caption">You are {verb}</p>'
                f"<h1>{plural(len(its), 'order')} · ≈ ${total:,.0f}</h1>"
                + ((f'<p class="cd">{icon("clock")}Approve by {e(dl)}. Not approved by then = not '
                    "sent.</p>" if a in ("ok", "ap") else
                    f'<p class="cd">{icon("clock")}Deadline {e(dl)}. Refusing now means '
                    f"{'this order is not sent' if a == 'veto' else 'none of these are sent'}.</p>")
                   if dl else "")
                + self._summary(qs)
                + f'<p class="mono">Batch {e(b)}</p>'
            )  # fmt: skip
        elif a == "ki":
            cons = "".join(
                f"<h3>{e(t)}</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"
                for t, items in KILL_COPY
            )
            head += (
                f'<span class="stop">{icon("stop-octagon")}</span><h1>Stop all trading now</h1>'
                f'<div class="cons">{cons}</div>'
            )
        else:
            head += f'<p class="summary">{e(what[:1].upper() + what[1:])}</p>' if what else ""
            if a == "srv:update" and fields.get("commit"):
                head += f'<p class="mono">Commit {e(fields["commit"][:10])}</p>'
        if a in ONE_TAP:
            inner = f'<button class="btn wide big">{e(ACTION_LABEL[a])}</button>'
            return head + section("", self._form(token, fields, inner) + cancel)
        if a.startswith("srv:") and a[4:] in NO_CODE_SERVER:
            inner = (
                '<input type="hidden" name="confirm" value="yes">'
                '<button class="btn wide big">Yes, run it</button>'
            )
            return head + section("", self._form(token, fields, inner) + cancel)
        if a in CONFIRM_ACTS:
            label = {"ki": "Kill trading", "so": "Stop: keep buys paused"}.get(
                a, f"Yes, {ACTION_LABEL[a]}"
            )
            inner = (
                '<input type="hidden" name="confirm" value="yes">'
                f'<button class="btn wide big danger">{e(label)}</button>'
            )
            return head + section("", self._form(token, fields, inner) + cancel)
        lock = self.locked(now)
        if lock:
            return head + section(
                "Locked",
                f"<p>Code actions are locked until {lock.astimezone(ASX_TZ):%H:%M} "
                "(too many wrong codes).</p>",
            )
        if a != "unlock" and self.actions_locked():  # BF-D83
            return head + section(
                "Actions are locked",
                "<p>You locked approvals, re-arming and server jobs. Unlock them first (needs "
                "your code" + (" and passphrase" if self.passphrase else "") + "). Pause, Kill "
                "and Stop work without unlocking.</p>"
                '<a class="btn wide" href="/act/confirm?a=unlock">Unlock</a>' + cancel,
            )
        extra = self._update_html(a[4:], now) if a.startswith("srv:") else ""
        if (
            a.startswith("srv:")
            and a[4:] in GUARDED_ACTIONS
            and self.market_open(now)
            and not (self._is_strategy(a[4:]))
        ):
            extra += (
                '<p class="note">The ASX is open now (10:00-16:15 Sydney). Restarting or '
                "updating could interrupt orders.</p>"
                '<label class="chk"><input type="checkbox" name="force" value="1" required> '
                "Do it anyway</label>"
            )
        go = (SRV_TITLE.get(a[4:], ("", "Run on the server"))[1] if a.startswith("srv:")
              else ACTION_LABEL.get(a, "Confirm"))  # fmt: skip
        cls = "btn wide big"
        if a == "srv:rollback":
            cls += " danger"
        if a == "ok" and b:
            n_all = len(self.journal.intents_of(b))
            go = (
                f"Approve all {n_all} orders"
                if qs.get("n") == "all"
                else f"Approve order {qs.get('n')}"
            )
        if a == "rf" and b:
            go = f"Refuse {plural(len(self.journal.intents_of(b)), 'order')}"
            cls += " dangerline"
        after = (
            '<p class="caption">Orders go to the broker at the close auction on the execution day. '
            "Changed your mind? Refuse the batch (or veto a buy) before the deadline; once orders "
            "are sent they cannot be recalled here.</p>"
            if a in ("ok", "ap") else ""
        )  # fmt: skip
        inner = (
            extra + '<label class="flabel" for="code">6-digit code from your authenticator</label>'
            '<input class="code" id="code" name="code" inputmode="numeric" pattern="[0-9]{6}" '
            'maxlength="6" autocomplete="one-time-code" required autofocus placeholder="••••••">'
            + (PP_INPUT_HTML if self.passphrase is not None and a in PASS_ACTS else "")
            + f'<button class="{cls}" style="margin-top:12px">{e(go)}</button>'
        )
        return head + section("", self._form(token, fields, inner) + cancel + after)

    def update_state(self) -> dict[str, Any]:
        st = get_state(self.journal, "update-available")
        return dict(st[0]) if st and isinstance(st[0], dict) else {}

    def _is_strategy(self, act: str) -> bool:
        """A rollback always counts as a strategy change; an update unless the worker's
        classification says app-only (unknown = strategy, the careful side)."""
        if act == "rollback":
            return True
        if act != "update":
            return False
        return bool(self.update_state().get("strategy", True))

    def _update_html(self, act: str, now: datetime) -> str:  # noqa: PLR0912 - one line per fact
        """BF-D45: what an update / rollback changes and when it takes effect."""
        from trader.strategy_version import update_block

        if act not in ("update", "rollback"):
            return ""
        u = self.update_state()
        strat = self._is_strategy(act)
        rows = []
        if act == "update":
            kind = "Strategy update" if strat else "App-only update (the strategy does not change)"
            rows.append(f"<p><b>{e(kind)}</b> · {plural(_ahead(u), 'new commit')}</p>")
            notes = u.get("notes") or {}
            for k, lab in (("version", "Version"), ("what", "What changes"), ("why", "Why"),
                           ("tested", "Tested"), ("takes_effect", "Takes effect")):  # fmt: skip
                if notes.get(k):
                    rows.append(f"<p class='small'><b>{lab}:</b> {e(notes[k])}</p>")
            if u.get("reasons"):
                rows.append("<p class='small muted'>" + e("; ".join(u["reasons"][:6])) + "</p>")
            sig = str(u.get("signed") or "")  # BF-D84: checked on the server, root-only key
            if sig == "good":
                rows.append("<p class='small'><b>Signed</b> by the engineer's key.</p>")
            elif sig == "bad":
                rows.append("<p class='warn'><b>Not signed by the engineer's key.</b> Approve only "
                            "if your engineer confirms this update.</p>")  # fmt: skip
        else:
            prev = str(u.get("previous") or "")
            rows.append(
                f"<p>Back to the commit before the last update: <b>{e(prev[:10] or '?')}</b></p>"
                "<p class='small muted'>A rollback does not undo database migrations.</p>"
            )
            if u.get("previous_migrations"):
                rows.append(
                    "<p class='warn'>The last update changed the database schema (a migration). "
                    "The older code must still work with it.</p>"
                    '<label class="chk"><input type="checkbox" name="migration" value="1" '
                    "required> Roll back across the migration anyway</label>"
                )
        if strat:
            if self.update_mode == "immediate":
                rows.append(
                    "<p class='note'>Mode <b>immediate</b>: applied once the ASX is closed and no "
                    "order is working (it waits, never interrupts orders); then the trader makes "
                    "an out-of-cycle decision with the new rules. Its orders wait for your "
                    "approval here, as always.</p>"
                )
            else:
                rows.append(
                    "<p class='note'>Mode <b>next decision</b>: applied outside ASX hours; the new "
                    "rules take effect at the next month-end decision. Holdings are not re-traded."
                    "</p>"
                )
                if update_block(self.update_mode, True, self.sessions(), now, False):
                    rows.append(
                        "<p class='warn'>A month-end decision is less than 24 hours away.</p>"
                        '<label class="chk"><input type="checkbox" name="override" value="1" '
                        "required> Apply before the decision anyway</label>"
                    )
        return "".join(rows)

    def _alerts_page(self, token: str) -> str:
        if self.vapid_public is None:
            body = (
                "<p>Alerts need the server's notification key (<code>vapid_private_key</code>). "
                "On the server: <code>bigwins vapid</code>, then restart the trader.</p>"
            )
            return section("Alerts on this phone", body)
        st = get_state(self.journal, "alerts") if not self.demo else None
        prefs = st[0] if st and isinstance(st[0], dict) else {}
        boxes = "".join(
            f'<label class="chk"><input type="checkbox" name="{k}" value="1"'
            f'{" checked" if prefs.get(k, k == "report") else ""}> {e(label)}</label>'
            for k, label in (("report", "Daily report (22:45)"), ("info", "Other messages"),
                             ("action", "My own app actions"))
        )  # fmt: skip
        return (
            "<h1>Alerts</h1>"
            + section(
                "Turn on alerts on this phone",
                "<p>Tap the button, then <b>Allow</b>. On iPhone, open Big Wins from the home "
                "screen icon first (Share &rsaquo; Add to Home Screen). A new device needs your "
                f"6-digit code (at most {self.max_devices} devices).</p>"
                '<input class="code" id="alerts-code" inputmode="numeric" pattern="[0-9]{6}" '
                'maxlength="6" autocomplete="one-time-code" placeholder="6-digit code">'
                '<button class="btn wide" style="margin-top:8px" id="alerts-on" type="button" '
                f'data-key="{e(self.vapid_public)}" data-csrf="{e(token)}">'
                "Turn on alerts</button>"
                '<p class="small muted" id="alerts-state"></p>',
            )
            + section(
                "Which alerts",
                "<p class='small'>PAGE alerts and approval requests always arrive (high "
                "priority); they cannot be turned off.</p>"
                f'<form method="post" action="/act/alerts"><input type="hidden" name="csrf" '
                f'value="{e(token)}">{boxes}<button class="btn sec wide">Save</button></form>',
            )
            + section(
                "Lost a phone?",
                '<form method="post" action="/act/push/off-all"><input type="hidden" name="csrf" '
                f'value="{e(token)}"><button class="btn sec wide">Turn alerts off on all '
                "devices</button></form>",
            )
        )

    # ------------------------------------------------------------ POST actions
    def _do(  # noqa: PLR0911, PLR0912 - one refusal per rule
        self, form: Mapping[str, str], login: str, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        now = self.clock()
        a = form.get("a", "")
        why, cmd, what = self._preview(form, now)
        if why is not None:
            return self._result(hdrs, f"Not done: {why}", False)
        if a in CONFIRM_ACTS and form.get("confirm") != "yes":
            return self._result(
                hdrs,
                f"Not done: {ACTION_LABEL[a]} needs the Yes button of its confirm screen.",
                False,
            )
        nocode_srv = a.startswith("srv:") and a[4:] in NO_CODE_SERVER
        if nocode_srv and form.get("confirm") != "yes":
            return self._result(hdrs, "Not done: it needs the Yes button of its confirm screen.",
                                False)  # fmt: skip
        needs_code = (a in CODE_ACTS or (a.startswith("srv:") and not nocode_srv)
                      or a in ("refresh", "unlock"))  # fmt: skip
        code = form.get("code", "").strip()
        if needs_code:
            if self.locked(now):
                return self._result(
                    hdrs, "Not done: code actions are locked (too many wrong codes).", False
                )
            if a != "unlock" and self.actions_locked():  # BF-D83
                return self._result(hdrs, "Not done: actions are locked. Unlock first: Controls "
                                    "> Unlock, with your code.", False)  # fmt: skip
            if not (len(code) == 6 and code.isdigit()):
                return self._result(hdrs, "Not done: enter your 6-digit code.", False)
        if self.passphrase is not None and a in PASS_ACTS and not form.get("pp", ""):
            return self._result(hdrs, "Not done: enter your passphrase as well.", False)
        if self.demo:
            return self._result(
                hdrs, f"DEMO: nothing was done. In the real app this would {what}.", True
            )
        if nocode_srv:
            reply = self._submit(_Req("server_nocode", login, now,
                                      {"action": a[4:], "shown": what}))  # fmt: skip
            return self._result(hdrs, reply or "queued", bool(reply and "queued" in reply))
        if a == "cancel":
            reply = self._submit(_Req("cancel", login, now, {"job": form.get("job", "0")}))
            return self._result(hdrs, reply or "queued", bool(reply and "cancelled" in reply))
        if a in ("here", "lock"):  # BF-D82 / BF-D83: one tap
            reply = self._submit(_Req(a, login, now, {"shown": what}))
            return self._result(hdrs, reply or "queued", bool(reply))
        if needs_code and not self._claim_code_slot():
            return self._result(hdrs, "Not done: another code request is still being checked; "
                                "wait for its answer.", False)  # fmt: skip
        return self._do_coded(a, form, login, hdrs, now, cmd, what, needs_code, code)

    def _do_coded(
        self, a: str, form: Mapping[str, str], login: str, hdrs: dict[str, str], now: datetime,
        cmd: str, what: str, needs_code: bool, code: str,
    ) -> tuple[int, dict[str, str], bytes]:  # fmt: skip
        """Holds the single code slot (H2) when ``needs_code``; it is released when the
        request has been executed (``_run``) or here when it is refused before queueing."""
        try:
            return self._do_queue(a, form, login, hdrs, now, cmd, what, needs_code, code)
        except _RefusedError as r:
            self._release_slot(needs_code)
            return self._result(hdrs, str(r), False)
        except Exception:  # BF-D57 (N3): never keep the slot after an unexpected error
            self._release_slot(needs_code)
            raise

    def _release_slot(self, needs_code: bool) -> None:
        """Free the code slot of a request that was refused or failed before it was
        queued (a queued one frees it in ``_run``)."""
        if needs_code:
            with self._lock:
                self._code_busy = False

    def _do_queue(  # noqa: PLR0912 - one rule per branch
        self, a: str, form: Mapping[str, str], login: str, hdrs: dict[str, str], now: datetime,
        cmd: str, what: str, needs_code: bool, code: str,
    ) -> tuple[int, dict[str, str], bytes]:  # fmt: skip
        pp = form.get("pp", "") if self.passphrase is not None and a in PASS_ACTS else ""
        need_pp = self.passphrase is not None and a in PASS_ACTS
        if a == "unlock":
            data = {"code": code, "pp": pp, "needs_pass": need_pp, "shown": what,
                    "code_bearing": True}  # fmt: skip
            reply = self._submit(_Req("unlock", login, now, data))
        elif a.startswith("srv:") or a == "refresh":
            from trader.strategy_version import update_block

            act = a[4:] if a.startswith("srv:") else "refresh"
            strat = self._is_strategy(act)
            flags = FORCE_MARKET if form.get("force") == "1" else 0
            if strat:  # BF-D45: the worker waits for the close and for working orders
                flags |= STRATEGY | (IMMEDIATE if self.update_mode == "immediate" else 0)
                block = update_block(self.update_mode, True, self.sessions(), now,
                                     form.get("override") == "1")  # fmt: skip
                if block is not None:
                    raise _RefusedError(f"Not done: {block}.")
                if form.get("override") == "1":
                    flags |= FORCE_MONTH_END
            elif act in GUARDED_ACTIONS and self.market_open(now) and not flags & FORCE_MARKET:
                raise _RefusedError("Not done: the ASX is open; tick 'Do it anyway'.")
            u = self.update_state()
            commit = ""
            if act == "update":  # BF-D48: exactly the commit the owner was shown
                commit = str(u.get("remote") or "")
                if not SHA40.fullmatch(commit) or form.get("commit") != commit:
                    raise _RefusedError("Not done: the update changed since you looked at it; "
                                   "open it again and check what it does.")  # fmt: skip
            if act == "rollback":
                commit = str(u.get("previous") or "")
                if not SHA40.fullmatch(commit):
                    raise _RefusedError("Not done: no previous version is recorded.")
                if u.get("previous_migrations"):
                    if form.get("migration") != "1":
                        raise _RefusedError("Not done: the rollback crosses a database migration; "
                                       "tick the box to do it anyway.")  # fmt: skip
                    flags |= FORCE_MIGRATION
            kind = "refresh" if a == "refresh" else "server"
            data = {"action": act, "force": flags, "code": code, "shown": what,
                    "commit": commit, "code_bearing": True, "pp": pp,
                    "needs_pass": need_pp}  # fmt: skip
            reply = self._submit(_Req(kind, login, now, data))
        else:
            command = f"{cmd} {code}" if needs_code else cmd
            data = {"command": command, "shown": what, "code_bearing": needs_code, "pp": pp,
                    "needs_pass": need_pp}  # fmt: skip
            reply = self._submit(_Req("bot", login, now, data))
        if reply is None:
            return self._result(hdrs, "Sent to the trader, which is busy with a job; the answer "
                                "will be in your Inbox in a minute.", True)  # fmt: skip
        good = not reply.startswith(("refused", "unknown", "no order", "this batch", "failed",
                                     "nothing", "usage", "ignored"))  # fmt: skip
        return self._result(hdrs, reply, good)

    def _result(
        self, hdrs: dict[str, str], text: str, good: bool
    ) -> tuple[int, dict[str, str], bytes]:
        tone = "up" if good else "down"
        act = _ACT.get()
        if act in ("ok", "ap", "rf", "veto"):
            back = (
                '<a class="btn wide" href="/orders" data-nav>Back to Orders</a>'
                '<a class="btn sec wide" style="margin-top:8px" href="/act">Controls</a>'
            )
        elif act.startswith("srv:") or act in ("refresh", "cancel"):
            back = (
                '<a class="btn wide" href="/server" data-nav>Back to Server</a>'
                '<a class="btn sec wide" style="margin-top:8px" href="/act">Controls</a>'
            )
        else:
            back = (
                '<a class="btn wide" href="/act">Back to Controls</a>'
                '<a class="btn sec wide" style="margin-top:8px" href="/orders" data-nav>'
                "Orders</a>"
            )
        body = (
            f'<div class="confirm"><span class="okmark {tone}">'
            f'{icon("check" if good else "x")}</span>'
            f'<h1>{"Done" if good else "Not done"}</h1>'
            + section("", f"<p>{e(text)}</p>"
                      + back)
            + "</div>"
        )  # fmt: skip
        return self._html(200, hdrs, "Result", body)

    def _costs_page(self, token: str) -> str:
        """BF-D76: edit the fixed running costs a year (server, price data, other). They
        only change what the Costs screen and the scoreboard show; nothing trades on them."""
        from trader.ops_view import COST_KEYS

        st = get_state(self.journal, "running-costs") if not self.demo else None
        cur = st[0] if st and isinstance(st[0], dict) else {}
        if isinstance(cur.get("history"), list) and cur["history"]:
            cur = cur["history"][-1] if isinstance(cur["history"][-1], dict) else {}
        fields = "".join(
            f'<label class="flabel" for="c-{k}">{e(lab)} ($ a year)</label>'
            f'<input class="field" id="c-{k}" name="{k}" inputmode="decimal" '
            f'pattern="[0-9]{{1,6}}([.][0-9]{{1,2}})?" value="{e(cur.get(k, ""))}" placeholder="0">'
            for k, lab in COST_KEYS
        )
        return (
            '<a class="back" href="/costs" data-nav>' + icon("chevron-left") + "Costs</a>"
            "<h1>Running costs</h1>"
            + section("Fixed costs a year", (
                "<p class='small'>What you pay each year to run Big Wins, whatever it trades. "
                "The scoreboard takes these off the account value. They change no trading "
                "rule, so no code is needed.</p>"
                f'<form method="post" action="/act/costs"><input type="hidden" name="csrf" '
                f'value="{e(token)}">{fields}<button class="btn wide" style="margin-top:16px">'
                "Save</button></form>"
                "<p class='caption'>New amounts count from today; earlier days keep the amounts "
                "that applied then. Leave all three empty or 0 to use the server's yearly total "
                "(costs.fixed_aud_per_year).</p>"))
        )  # fmt: skip

    def _costs_post(
        self, form: Mapping[str, str], login: str, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        from decimal import InvalidOperation

        from trader.ops_view import COST_KEYS, MIN_FIXED_TOTAL

        vals: dict[str, str] = {}
        for k, lab in COST_KEYS:
            raw = (form.get(k) or "0").strip().replace(",", "").replace("$", "") or "0"
            try:
                d = Decimal(raw)
            except InvalidOperation:
                return self._result(hdrs, f"Not saved: {lab} is not a number.", False)
            if not d.is_finite() or d < 0 or d > 100000:
                return self._result(hdrs, f"Not saved: {lab} must be between 0 and 100,000.", False)
            if 0 < d < 1:
                why = f"Not saved: {lab} is under $1 a year (enter 0 for none)."
                return self._result(hdrs, why, False)
            vals[k] = str(d.quantize(Decimal("0.01")))
        total = sum(Decimal(v) for v in vals.values())
        if 0 < total < MIN_FIXED_TOTAL:  # BF-D81 (N1): a typo cannot wipe the running costs
            return self._result(hdrs, f"Not saved: ${total} a year in all looks too small. Enter "
                                "the yearly amounts, or 0 in every box to use the server's "
                                "total.", False)  # fmt: skip
        if self.demo:
            return self._result(hdrs, "DEMO: running costs not saved.", True)
        if all(Decimal(v) == 0 for v in vals.values()):
            vals = {}
        r = self._submit(_Req("costs", login, self.clock(), vals))
        return self._result(hdrs, r or "queued", True)

    def _reminders_page(self, token: str) -> str:
        """BF-D86: the renewal dates (the Flex token, cards) for Health and reminders."""
        from trader.presence import REMINDERS, reminder_dates

        cur = {} if self.demo else reminder_dates(self.journal)
        fields = "".join(
            f'<label class="flabel" for="r-{k}">{e(lab)}</label>'
            f'<input class="field" id="r-{k}" name="{k}" type="date" value="{e(cur.get(k, ""))}">'
            for k, lab in REMINDERS
        )
        return (
            '<a class="back" href="/health" data-nav>' + icon("chevron-left") + "Health</a>"
            "<h1>Renewal dates</h1>"
            + section("When things run out", (
                "<p class='small'>The app reminds you 30 days, 7 days and 1 day before each date. "
                "Leave a box empty for no reminder. No code is needed: nothing trades on these.</p>"
                f'<form method="post" action="/act/reminders"><input type="hidden" name="csrf" '
                f'value="{e(token)}">{fields}<button class="btn wide" style="margin-top:16px">'
                "Save</button></form>"))
        )  # fmt: skip

    def _reminders_post(
        self, form: Mapping[str, str], login: str, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        from trader.presence import REMINDERS

        vals: dict[str, str] = {}
        for k, lab in REMINDERS:
            raw = (form.get(k) or "").strip()
            if not raw:
                continue
            try:
                d = date.fromisoformat(raw)
            except ValueError:
                return self._result(hdrs, f"Not saved: {lab} is not a date.", False)
            if not date(2020, 1, 1) <= d <= date(2100, 12, 31):
                return self._result(hdrs, f"Not saved: {lab} is out of range.", False)
            vals[k] = d.isoformat()
        if self.demo:
            return self._result(hdrs, "DEMO: renewal dates not saved.", True)
        r = self._submit(_Req("reminders", login, self.clock(), vals))
        return self._result(hdrs, r or "queued", True)

    def _alerts_post(
        self, form: Mapping[str, str], login: str, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        prefs = {k: form.get(k) == "1" for k in ("report", "info", "action")}
        if self.demo:
            return self._result(hdrs, "DEMO: alert settings not saved.", True)
        r = self._submit(_Req("alerts", login, self.clock(), prefs))
        return self._result(hdrs, r or "queued", True)

    def _subscribe(  # noqa: PLR0911 - one refusal per rule
        self, login: str, body: bytes, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        from trader.app_notify import push_host_ok

        hdrs["Content-Type"] = "text/plain; charset=utf-8"
        try:
            d = json.loads(body)
            sub = d.get("subscription", d)
            data = {"endpoint": str(sub["endpoint"]), "p256dh": str(sub["keys"]["p256dh"]),
                    "auth": str(sub["keys"]["auth"]), "code": str(d.get("code", "")).strip(),
                    "code_bearing": True}  # fmt: skip
        except (ValueError, KeyError, TypeError, AttributeError):
            return 400, hdrs, b"bad subscription\n"
        ep, code = str(data["endpoint"]), str(data["code"])
        if not push_host_ok(ep) or len(ep) > 512:
            return 400, hdrs, b"not a known push service\n"
        if not (len(code) == 6 and code.isdigit()):
            return 400, hdrs, b"enter your 6-digit code first\n"
        if self.demo:
            return 200, hdrs, b"DEMO: not saved\n"
        if self.locked(self.clock()):
            return 403, hdrs, b"code actions are locked (too many wrong codes)\n"
        if not self._claim_code_slot():
            return 429, hdrs, b"another code request is still being checked\n"
        r = self._submit(_Req("subscribe", login, self.clock(), data))
        status = 200 if r == "ok" or r is None else 403
        return status, hdrs, (r or "queued").encode()


# BF-D83: the memorised passphrase (never autofilled or stored by the browser)
PP_INPUT_HTML = (  # the HTML of the input field, not a password
    '<label class="flabel" for="pp" style="margin-top:12px">Your passphrase (the one you keep '
    "in your head)</label>"
    '<input class="field" id="pp" name="pp" type="password" autocomplete="off" '
    'autocapitalize="off" spellcheck="false" maxlength="200" required>'
)

ACTIONS_OFF = (
    "<p>Viewing works, but approving, pausing and the other actions are switched off "
    "because no Tailscale log-in is allowed to act yet.</p>"
    "<p>On the server, run <code>bigwins</code> and choose <b>Allow my phone to act</b> "
    "(it reads your Tailscale log-in and writes it to <code>app.allowed_logins</code> in "
    "config/bfast.yaml on the server), then restart the trader.</p>"
)


def _px(x: object) -> str:
    """A limit price: 2 dp at $2 and above, 3 dp below (BF-D73)."""
    try:
        q = Decimal(str(x))
    except ArithmeticError:
        return e(x)
    return f"${q.quantize(Decimal('0.01') if abs(q) >= 2 else Decimal('0.001')):,}"


def control_qs(**kw: str) -> str:
    return "/act/confirm?" + urlencode({k: v for k, v in kw.items() if v})


def make_handler(ctl: Control) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "BigWinsControl"
        sys_version = ""

        def _go(self) -> None:
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(min(n, BODY_MAX + 1)) if n > 0 else b""
            status, hdrs, out = ctl.respond(self.command, self.path, dict(self.headers), body)
            self.send_response(status)
            for k, v in hdrs.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(out)

        do_GET = do_HEAD = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _go  # noqa: N815

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve_control(ctl: Control, host: str, port: int) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((host, port), make_handler(ctl))
    threading.Thread(target=httpd.serve_forever, name="app-control", daemon=True).start()
    return httpd


def _ahead(u: Mapping[str, Any]) -> int:
    """Security review L5: the number of new commits, or 0 (never a stored string)."""
    v = str(u.get("ahead") or 0)
    return int(v) if v.isdigit() else 0
