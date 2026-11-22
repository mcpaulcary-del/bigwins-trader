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
4. **Code lock-out**: 5 wrong codes in 15 minutes lock code actions from the app for 15
   minutes (journaled, and paged to the owner). Pause, Kill and Stop stay available.
5. **Confirm screens**: every action first shows what will happen ("Approve all 18 orders
   of <batch> - total about A$9,900") before the code is asked; Kill and Stop need the
   "Yes" button of their confirm screen.

Every action is journaled (the safety / approval rows carry the actor ``app:<login>``) and
written to the inbox with its outcome (source ``app:<login>``).
"""

from __future__ import annotations

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

from trader.app_store import (
    FORCE_MARKET,
    FORCE_MONTH_END,
    GUARDED_ACTIONS,
    IMMEDIATE,
    SERVER_ACTIONS,
    STRATEGY,
    add_inbox,
    add_push_sub,
    add_server_job,
    drop_push_sub,
    get_state,
    set_state,
)
from trader.approval import APP_CHAT, OPEN_FOR_APPROVAL, ApprovalBot, Incoming, approved_seqs
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.webui import SECURITY_HEADERS, e, page, section

CODE_ACTS = frozenset({"ok", "ap", "rf", "veto", "re", "co", "idmap", "idmap_reject"})
CONFIRM_ACTS = frozenset({"ki", "so"})
ONE_TAP = frozenset({"pa", "st"})
MAX_FAILS = 5
LOCK = timedelta(minutes=15)
BODY_MAX = 16384
WAIT_S = 45.0
COOKIE = "bw_sid"
LOGIN_HEADER = "tailscale-user-login"
ACTION_LABEL = {
    "ok": "Approve", "ap": "Approve batch", "rf": "Refuse batch", "veto": "Veto",
    "re": "Resume", "co": "Continue", "idmap": "Confirm code change",
    "idmap_reject": "Undo code change", "pa": "Pause", "ki": "KILL", "so": "STOP",
    "st": "Status",
}  # fmt: skip


def asx_open(now: datetime) -> bool:
    """Mon-Fri 10:00-16:15 Sydney (the bigwins menu's guard; holidays count as open)."""
    t = now.astimezone(ASX_TZ)
    return t.weekday() < 5 and time(10, 0) <= t.time() <= time(16, 15)


def header(headers: Mapping[str, str], name: str) -> str:
    return next((v for k, v in headers.items() if k.lower() == name), "").strip()


def same_origin(headers: Mapping[str, str]) -> bool:
    """Fetch metadata / Origin check for POSTs (CSRF defence in depth)."""
    site = header(headers, "sec-fetch-site").lower()
    if site and site != "same-origin":
        return False
    origin = header(headers, "origin")
    if origin and origin != "null":
        host = urlsplit(origin).netloc.lower()
        ok = {header(headers, "host").lower(), header(headers, "x-forwarded-host").lower()}
        return host in ok - {""}
    return origin != "null"


def _cookie(headers: Mapping[str, str], name: str) -> str:
    for part in header(headers, "cookie").split(";"):
        k, _, v = part.strip().partition("=")
        if k == name:
            return v
    return ""


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
    _key: bytes = field(default_factory=lambda: secrets.token_bytes(32), repr=False)
    _q: queue.Queue[_Req] = field(default_factory=queue.Queue, repr=False)
    _wake: threading.Event = field(default_factory=threading.Event, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _fails: list[datetime] = field(default_factory=list, repr=False)
    _locked_until: datetime | None = None

    def __post_init__(self) -> None:
        self.allowed_logins = frozenset(x.strip().lower() for x in self.allowed_logins if x.strip())
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
        n = 0
        while True:
            try:
                r = self._q.get_nowait()
            except queue.Empty:
                return n
            try:
                r.result = self._execute(r)
            except Exception as ex:  # an action never stops the trader
                r.result = f"failed: {type(ex).__name__}"
            r.done.set()
            n += 1

    def _submit(self, r: _Req) -> str | None:
        if self.inline:
            r.result = self._execute(r)
            return r.result
        self._q.put(r)
        self._wake.set()
        return r.result if r.done.wait(WAIT_S) else None

    def locked(self, now: datetime) -> datetime | None:
        with self._lock:
            u = self._locked_until
        return u if u is not None and now < u else None

    def _execute(self, r: _Req) -> str:  # noqa: PLR0911 - one branch per kind
        src = f"app:{r.login}"
        if r.kind == "bot":
            if self.bot is None:
                return "the trader's command handler is not running"
            before = self.bot.verifier.failures
            m = Incoming(APP_CHAT, str(r.data["command"]), r.at, source="app", login=r.login)
            reply = self.bot.handle(m)
            wrong = self.bot.verifier.failures > before
            shown = str(r.data["shown"])
            add_inbox(self.journal, self.clock(), "action", f"You (app): {shown}"[:200],
                      f"{shown}\n-> {reply}", "/inbox", src, "off")  # fmt: skip
            self._count(wrong, r.at, r.login)
            return reply
        if r.kind == "subscribe":
            d = r.data
            add_push_sub(self.journal, d["endpoint"], d["p256dh"], d["auth"], r.login, r.at)
            if self.notify is not None:
                self.notify("Alerts are on for this phone. Approvals and PAGE alerts arrive "
                            "here at high priority.", "info", "/settings", src, True)  # fmt: skip
            return "ok"
        if r.kind == "unsubscribe":
            return "ok" if drop_push_sub(self.journal, str(r.data["endpoint"])) else "not found"
        if r.kind == "alerts":
            set_state(self.journal, "alerts", dict(r.data), r.at)
            add_inbox(self.journal, self.clock(), "action", "You (app): alert settings changed",
                      json.dumps(r.data), "/settings", src, "off")  # fmt: skip
            return "alert settings saved"
        if r.kind in ("server", "refresh"):
            return self._server(r, src)
        return "unknown request"

    def _server(self, r: _Req, src: str) -> str:
        if self.bot is None or not self.bot.verifier.verify(str(r.data["code"]), r.at):
            self._count(True, r.at, r.login)
            reply = "refused: invalid or reused code"
        elif r.kind == "refresh":
            self._count(False, r.at, r.login)
            reply = self.refresh_prices(r.at) if self.refresh_prices else "no price refresher"
        else:
            self._count(False, r.at, r.login)
            act = str(r.data["action"])
            jid = add_server_job(self.journal, act, int(r.data["force"]), r.login, r.at)
            reply = (
                f"server job {jid} '{act}' queued: the server runs it within a minute "
                "(Server tab shows progress)"
            )
        shown = str(r.data["shown"])
        add_inbox(self.journal, self.clock(), "action", f"You (app): {shown}"[:200],
                  f"{shown}\n-> {reply}", "/server", src, "off")  # fmt: skip
        return reply

    def _count(self, wrong: bool, at: datetime, login: str) -> None:
        """BF-D39 lock-out: 5 wrong codes within 15 minutes lock code actions for 15
        minutes; journaled (app state + inbox) and paged."""
        page_text = None
        with self._lock:
            if not wrong:
                self._fails.clear()
                return
            self._fails = [t for t in self._fails if at - t < LOCK] + [at]
            if len(self._fails) >= MAX_FAILS:
                self._locked_until = at + LOCK
                self._fails.clear()
                page_text = (
                    f"PAGE app code actions LOCKED until "
                    f"{self._locked_until.astimezone(ASX_TZ):%H:%M} Sydney: {MAX_FAILS} wrong "
                    f"codes in 15 minutes (log-in {login}). Pause, Kill and Stop still work. "
                    "If this was not you, use Kill and check the server."
                )
        if page_text is not None:
            assert self._locked_until is not None
            set_state(self.journal, "app-lockout",
                      {"until": self._locked_until.isoformat(), "login": login}, at)  # fmt: skip
            if self.notify is not None:
                self.notify(page_text, "page", "/inbox")
            else:
                add_inbox(self.journal, at, "page", page_text[:200], page_text, "/inbox")

    # ------------------------------------------------------------ HTTP side
    def respond(  # noqa: PLR0911 - one return per route
        self, method: str, path: str, headers: Mapping[str, str], body: bytes = b""
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs = dict(SECURITY_HEADERS)
        url = urlsplit(path)
        p = url.path.rstrip("/") or "/act"
        qs = {k: v[-1] for k, v in parse_qs(url.query).items()}
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
            return self._do(form, login, hdrs)
        if p == "/act/alerts":
            return self._alerts_post(form, login, hdrs)
        if p == "/act/push/off":
            r = self._submit(
                _Req("unsubscribe", login, self.clock(), {"endpoint": form.get("endpoint", "")})
            )
            return self._html(200, hdrs, "Alerts", section("Alerts", f"<p>{e(r or 'queued')}</p>"))
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
        if not same_origin(headers):
            return "cross-site request refused"
        sent = header(headers, "x-csrf-token")
        if not sent:
            form = parse_qs(body.decode("utf-8", "replace")) if body[:1] != b"{" else {}
            sent = (form.get("csrf") or [""])[-1]
        if not _cookie(headers, COOKIE) or not hmac.compare_digest(sent, self._token(sid, login)):
            return "missing or stale form token: reload the page and try again"
        return None

    def _html(
        self, status: int, hdrs: dict[str, str], title: str, body: str, active: str = ""
    ) -> tuple[int, dict[str, str], bytes]:
        hdrs["Content-Type"] = "text/html; charset=utf-8"
        out = page(title, body, active, demo=self.demo, refresh=False)
        return status, hdrs, out.encode()

    # ------------------------------------------------------------ GET pages
    def _get(
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
            return self._html(200, hdrs, "Confirm", self._confirm(qs, token))
        if p == "/act/alerts":
            return self._html(200, hdrs, "Alerts", self._alerts_page(token), "server")
        return 404, hdrs, b"not found\n"

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
        out = [f"<h1>Controls</h1><p>Safety now: <b>{e(lvl)}</b></p>"]
        if self.demo:
            out.append('<p class="note">DEMO: buttons here are simulated; nothing is changed.</p>')
        if lock:
            out.append(
                f'<p class="note">Code actions are locked until {lock.astimezone(ASX_TZ):%H:%M} '
                "(too many wrong codes). Pause, Kill and Stop still work.</p>"
            )
        out.append(section(
            "Stop or slow the trader",
            self._form(token, {"a": "pa"},
                       '<button class="btn wide warnb">⏸ Pause buying now</button>')
            + '<p class="small muted">Pause is one tap: buys stop, registered sells go on.</p>'
            '<div class="btns"><a class="btn danger" href="/act/confirm?a=ki">🛑 Kill…</a>'
            '<a class="btn sec" href="/act/confirm?a=so">✋ Stop (L11)…</a></div>',
        ))  # fmt: skip
        out.append(section(
            "Re-arm (needs your code)",
            '<div class="btns"><a class="btn sec" href="/act/confirm?a=re">▶️ Resume…</a>'
            '<a class="btn sec" href="/act/confirm?a=co">✔️ Continue (L11)…</a></div>'
            + self._form(token, {"a": "st"}, '<button class="btn sec wide">📊 Status</button>'),
        ))  # fmt: skip
        waiting = self.waiting_batches(now)
        rows = "".join(
            f'<li><a class="rowlink" href="/act/confirm?a=ok&amp;b={e(b)}&amp;n=all">'
            f'<span class="grow"><b>{e(b)}</b><div class="sub">{n} order(s) waiting · '
            f"by {e(dl)}</div></span><span class='chev'>&rsaquo;</span></a></li>"
            for b, n, dl in waiting
        )
        out.append(section(
            "Waiting for your approval",
            f'<ul class="list">{rows}</ul>' if rows else '<p class="muted">Nothing waiting.</p>',
        ))  # fmt: skip
        out.append(section("Code changes (BF-D19)", self._idmap_html()))
        out.append(
            '<p class="small muted"><a href="/act/alerts">Alerts on this phone…</a> · '
            '<a href="/server" data-nav>Server</a></p>'
        )
        return "".join(out)

    def _idmap_html(self) -> str:
        recs = [r for r in self.journal.identity_records().values() if r["status"] == "PROPOSED"]
        items = "".join(
            f"<li><b>{e(r['old_code'])} → {e(r['new_code'])}</b>"
            + (f" ratio {e(r['ratio'])}" if r.get("ratio") else "")
            + f'<div class="btns"><a class="btn sec" href="/act/confirm?a=idmap&amp;old='
            f'{e(r["old_code"])}&amp;new={e(r["new_code"])}">Confirm…</a>'
            f'<a class="btn sec" href="/act/confirm?a=idmap_reject&amp;old={e(r["old_code"])}">'
            "Undo…</a></div></li>"
            for r in recs
        )
        manual = (
            '<form method="get" action="/act/confirm"><input type="hidden" name="a" value="idmap">'
            '<div class="btns"><input class="code" style="font-size:16px;letter-spacing:1px" '
            'name="old" placeholder="old code" maxlength="6" required>'
            '<input class="code" style="font-size:16px;letter-spacing:1px" name="new" '
            'placeholder="new code" maxlength="6" required></div>'
            '<input class="code" style="font-size:16px;letter-spacing:1px" name="ratio" '
            'placeholder="ratio, e.g. 1:10 (optional)" maxlength="12">'
            '<button class="btn sec wide" style="margin-top:8px">Record a code change…</button>'
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

    def _preview(self, qs: Mapping[str, str], now: datetime) -> tuple[str | None, str, str]:
        a = qs.get("a", "")
        if a.startswith("srv:"):
            act = a[4:]
            if act not in SERVER_ACTIONS:
                return "unknown server action", "", ""
            return None, "", SERVER_ACTIONS[act]
        if a == "refresh":
            return None, "", "refresh the price store now (the day's EODHD bulk file)"
        args = [x for x in (qs.get("b", ""), qs.get("n", "")) if x]
        if a in ("idmap", "idmap_reject"):
            args = [x for x in (qs.get("old", ""), qs.get("new", ""), qs.get("ratio", "")) if x]
            if a == "idmap_reject":
                args = args[:1]
        if self.bot is None:
            return "the trader's command handler is not running", "", ""
        return self.bot.preview(a, args, now)

    def _summary(self, qs: Mapping[str, str]) -> str:
        """The orders an approval / refusal covers, with the total value."""
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
            f"<tr><td>{it.seq}</td><td class='{'buy' if it.side.value == 'BUY' else 'sell'}'>"
            f"{e(it.side.value.lower())}</td><td><b>{e(it.entity)}</b><div class='sub'>{it.qty} "
            f"@ ≤ {e(it.limit_price)}</div></td>"
            f"<td class='r'>≈ A${Decimal(str(it.value_at_ref)):,.0f}</td></tr>"
            for it, _ in its
        )
        tot = f"buys ≈ A${buys:,.0f}" + (f", sells ≈ A${sells:,.0f}" if sells else "")
        return (
            f'<p class="muted">{len(its)} order(s): {e(tot)} (at the reference prices; '
            "limits shown)</p>"
            f"<table><tbody>{rows}</tbody></table>"
        )

    def _confirm(self, qs: Mapping[str, str], token: str) -> str:
        now = self.clock()
        a = qs.get("a", "")
        why, _cmd, what = self._preview(qs, now)
        if why is not None:
            return section(
                "Cannot do this", f"<p>{e(why)}</p><a class='btn sec' href='/act'>Back</a>"
            )
        fields = {k: qs.get(k, "") for k in ("a", "b", "n", "old", "new", "ratio")}
        head = f"<h1>{e(ACTION_LABEL.get(a, 'Confirm'))}</h1>"
        summary = self._summary(qs)
        if a == "ok" and qs.get("n") == "all" and qs.get("b"):
            its = self.journal.intents_of(qs["b"])
            total = sum((Decimal(str(it.value_at_ref)) for it, _ in its), Decimal(0))
            what = f"Approve all {len(its)} orders of {qs['b']} — total ≈ A${total:,.0f}"
        demo = (
            '<p class="note">DEMO: nothing will be changed; the result is simulated.</p>'
            if self.demo else ""
        )  # fmt: skip
        if a in ONE_TAP:
            inner = f'<button class="btn wide">{e(ACTION_LABEL[a])}</button>'
            return (
                head
                + demo
                + section(
                    "", f'<p class="summary">{e(what)}</p>' + self._form(token, fields, inner)
                )
            )
        if a in CONFIRM_ACTS:
            inner = (
                '<input type="hidden" name="confirm" value="yes">'
                f'<button class="btn wide danger">Yes, {e(ACTION_LABEL[a])}</button>'
            )
            return head + demo + section(
                "", f'<p class="summary">{e(what)}.</p>' + self._form(token, fields, inner)
                + '<a class="btn sec wide" style="margin-top:8px" href="/act">Cancel</a>',
            )  # fmt: skip
        lock = self.locked(now)
        if lock:
            return head + section(
                "Locked",
                f"<p>Code actions are locked until {lock.astimezone(ASX_TZ):%H:%M} "
                "(too many wrong codes).</p>",
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
        go = "Run on the server" if a.startswith("srv:") else ACTION_LABEL.get(a, "Confirm")
        if a == "ok" and qs.get("b"):
            n_all = len(self.journal.intents_of(qs["b"]))
            go = (
                f"Approve all {n_all} orders"
                if qs.get("n") == "all"
                else f"Approve order {qs.get('n')}"
            )
        inner = (
            extra
            + '<label class="small muted" for="code">Your 6-digit code (authenticator app)</label>'
            '<input class="code" id="code" name="code" inputmode="numeric" pattern="[0-9]{6}" '
            'maxlength="6" autocomplete="one-time-code" required autofocus>'
            f'<button class="btn wide" style="margin-top:10px">{e(go)}</button>'
        )
        return (
            head + demo
            + section("", f'<p class="summary">{e(what)}</p>{summary}'
                      + self._form(token, fields, inner)
                      + '<a class="btn sec wide" style="margin-top:8px" href="/act">Cancel</a>')
        )  # fmt: skip

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

    def _update_html(self, act: str, now: datetime) -> str:
        """BF-D45: what an update / rollback changes and when it takes effect."""
        from trader.strategy_version import update_block

        if act not in ("update", "rollback"):
            return ""
        u = self.update_state()
        strat = self._is_strategy(act)
        rows = []
        if act == "update":
            kind = "Strategy update" if strat else "App-only update (the strategy does not change)"
            rows.append(f"<p><b>{e(kind)}</b> · {int(u.get('ahead') or 0)} new commit(s)</p>")
            notes = u.get("notes") or {}
            for k, lab in (("version", "Version"), ("what", "What changes"), ("why", "Why"),
                           ("tested", "Tested"), ("takes_effect", "Takes effect")):  # fmt: skip
                if notes.get(k):
                    rows.append(f"<p class='small'><b>{lab}:</b> {e(notes[k])}</p>")
            if u.get("reasons"):
                rows.append("<p class='small muted'>" + e("; ".join(u["reasons"][:6])) + "</p>")
        else:
            prev = str(u.get("previous") or "")
            rows.append(
                f"<p>Back to the commit before the last update: <b>{e(prev[:10] or '?')}</b></p>"
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
                "screen icon first (Share &rsaquo; Add to Home Screen).</p>"
                '<button class="btn wide" id="alerts-on" type="button" '
                f'data-key="{e(self.vapid_public)}" data-csrf="{e(token)}">'
                "🔔 Turn on alerts</button>"
                '<p class="small muted" id="alerts-state"></p>',
            )
            + section(
                "Which alerts",
                "<p class='small'>PAGE alerts and approval requests always arrive (high "
                "priority); they cannot be turned off.</p>"
                f'<form method="post" action="/act/alerts"><input type="hidden" name="csrf" '
                f'value="{e(token)}">{boxes}<button class="btn sec wide">Save</button></form>',
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
        needs_code = a in CODE_ACTS or a.startswith("srv:") or a == "refresh"
        code = form.get("code", "").strip()
        if needs_code:
            if self.locked(now):
                return self._result(
                    hdrs, "Not done: code actions are locked (too many wrong codes).", False
                )
            if not (len(code) == 6 and code.isdigit()):
                return self._result(hdrs, "Not done: enter your 6-digit code.", False)
        if self.demo:
            return self._result(
                hdrs, f"DEMO: nothing was done. In the real app this would {what}.", True
            )
        if a.startswith("srv:") or a == "refresh":
            from trader.strategy_version import update_block

            act = a[4:] if a.startswith("srv:") else "refresh"
            strat = self._is_strategy(act)
            flags = FORCE_MARKET if form.get("force") == "1" else 0
            if strat:  # BF-D45: the worker waits for the close and for working orders
                flags |= STRATEGY | (IMMEDIATE if self.update_mode == "immediate" else 0)
                block = update_block(self.update_mode, True, self.sessions(), now,
                                     form.get("override") == "1")  # fmt: skip
                if block is not None:
                    return self._result(hdrs, f"Not done: {block}.", False)
                if form.get("override") == "1":
                    flags |= FORCE_MONTH_END
                if act == "rollback" and not self.update_state().get("previous"):
                    return self._result(hdrs, "Not done: no previous version is recorded.", False)
            elif act in GUARDED_ACTIONS and self.market_open(now) and not flags & FORCE_MARKET:
                return self._result(hdrs, "Not done: the ASX is open; tick 'Do it anyway'.", False)
            kind = "refresh" if a == "refresh" else "server"
            data = {"action": act, "force": flags, "code": code, "shown": what}
            reply = self._submit(_Req(kind, login, now, data))
        else:
            command = f"{cmd} {code}" if needs_code else cmd
            shown = what
            reply = self._submit(_Req("bot", login, now, {"command": command, "shown": shown}))
        if reply is None:
            return self._result(hdrs, "Sent to the trader, which is busy with a job; the answer "
                                "will be in your Inbox in a minute.", True)  # fmt: skip
        good = not reply.startswith(("refused", "unknown", "no order", "this batch", "failed",
                                     "nothing", "usage", "ignored"))  # fmt: skip
        return self._result(hdrs, reply, good)

    def _result(
        self, hdrs: dict[str, str], text: str, good: bool
    ) -> tuple[int, dict[str, str], bytes]:
        tone = "ok" if good else "bad"
        body = (
            f'<h1>{"Done" if good else "Not done"}</h1>'
            + section("", f'<p><span class="pill {tone}">{"OK" if good else "NO"}</span> '
                      f"{e(text)}</p>"
                      '<div class="btns"><a class="btn sec" href="/orders" data-nav>Orders</a>'
                      '<a class="btn sec" href="/act">Controls</a></div>')
        )  # fmt: skip
        return self._html(200, hdrs, "Result", body)

    def _alerts_post(
        self, form: Mapping[str, str], login: str, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        prefs = {k: form.get(k) == "1" for k in ("report", "info", "action")}
        if self.demo:
            return self._result(hdrs, "DEMO: alert settings not saved.", True)
        r = self._submit(_Req("alerts", login, self.clock(), prefs))
        return self._result(hdrs, r or "queued", True)

    def _subscribe(
        self, login: str, body: bytes, hdrs: dict[str, str]
    ) -> tuple[int, dict[str, str], bytes]:
        from trader.app_notify import push_host_ok

        hdrs["Content-Type"] = "text/plain; charset=utf-8"
        try:
            d = json.loads(body)
            data = {"endpoint": str(d["endpoint"]), "p256dh": str(d["keys"]["p256dh"]),
                    "auth": str(d["keys"]["auth"])}  # fmt: skip
        except (ValueError, KeyError, TypeError):
            return 400, hdrs, b"bad subscription\n"
        if not push_host_ok(data["endpoint"]) or len(data["endpoint"]) > 512:
            return 400, hdrs, b"not a known push service\n"
        if self.demo:
            return 200, hdrs, b"DEMO: not saved\n"
        r = self._submit(_Req("subscribe", login, self.clock(), data))
        return 200, hdrs, (r or "queued").encode()


ACTIONS_OFF = (
    "<p>Viewing works, but approving, pausing and the other actions are switched off "
    "because no Tailscale log-in is allowed to act yet.</p>"
    "<p>On the server, run <code>bigwins</code> and choose <b>Allow my phone to act</b> "
    "(it reads your Tailscale log-in and writes it to <code>app.allowed_logins</code> in "
    "config/bfast.yaml on the server), then restart the trader.</p>"
)


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
