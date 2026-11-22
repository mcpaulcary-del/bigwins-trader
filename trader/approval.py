"""Approval queue and owner commands (FD v3.0 §12, EMG2-20 L8; BF2).

Deterministic code only: no AI component reads or writes approvals (BW-APR-06).

Approval modes per batch:

* ``per_order`` (L8, the default for the EMG2-20 book through April 2027 and for the
  B-fast paper dry runs): each order needs ``/ok <batch> <n> <code>`` or
  ``/ok <batch> all <code>`` before the deadline (15:20 Sydney on the execution
  session). An order not approved is not sent;
* ``batch`` (§12 BW-APR-03): ``/approve <batch> <code>`` approves every order;
* ``auto`` (BW-APR-02, paper modes): approved at creation; the owner is still told.

``/veto <batch> <n> <code>`` removes a single **buy** (BW-APR-04; sells of a registered
line are refused one by one, the owner can ``/refuse <batch> <code>`` the whole batch).
``/pause``, ``/kill`` and ``/stop`` (L11 (d): no automatic resume) act in one step
without a code (they only reduce risk, BW-RSK-30); ``/resume <code>`` re-arms and needs
the second factor, as does ``/continue <code>`` (L11 stage 3 written confirmation). ``<code>`` is a
6-digit TOTP (RFC 6238, SHA-1, 30 s) from the owner's authenticator; each code is
accepted once. Commands are accepted only from allow-listed Telegram chat ids
(BP-11). The TOTP seed and the bot token are Docker secrets, never config.

Buttons (BF-D38): an approval request carries Telegram inline buttons ("Approve all",
"Refuse batch", one per order, "Status", "Pause"); ``/menu`` shows Status, Pause, Kill,
Stop, Resume and Continue. A tap is only a shortcut for the typed command: it is turned
into the same text and handled by the same code (``ApprovalBot._dispatch``), from the same
allow-listed chats, with the same deadline and the same one-time code. A tap that adds
risk or re-arms (approve, refuse, resume, continue) asks for the 6-digit code; the next
code message from that chat within ``code_window_s`` (3 minutes) completes it, exactly as
``/ok <batch> all <code>`` would. Pause needs nothing; Kill and Stop need a second
confirming tap within ``confirm_window_s``. Typed commands work as before.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import json
import re
import struct
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from trader.constants import ASX_TZ
from trader.corporate_actions import CaError, parse_ratio
from trader.journal import Journal, Status
from trader.orders import Side
from trader.risk import SafetyLevel
from trader.secrets import SecretValue

# ---------------------------------------------------------------- TOTP (second factor)


def totp(secret_b32: str, at: datetime, step: int = 30, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32.upper() + "=" * (-len(secret_b32) % 8))
    counter = int(at.timestamp()) // step
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    code = (struct.unpack(">I", mac[off : off + 4])[0] & 0x7FFFFFFF) % 10**digits
    return f"{code:0{digits}d}"


class TotpVerifier:
    """Verifies codes within +/- ``window`` steps; each (step, code) is accepted once."""

    def __init__(self, secret: SecretValue, window: int = 1) -> None:
        self._secret = secret
        self._window = window
        self._used: set[tuple[int, str]] = set()

    def verify(self, code: str, at: datetime) -> bool:
        if not (len(code) == 6 and code.isdigit()):
            return False
        base = int(at.timestamp()) // 30
        for k in range(-self._window, self._window + 1):
            t = datetime.fromtimestamp((base + k) * 30, tz=at.tzinfo)
            if hmac.compare_digest(totp(self._secret.reveal(), t), code):
                if (base + k, code) in self._used:
                    return False
                self._used.add((base + k, code))
                return True
        return False


# ---------------------------------------------------------------- transport


@dataclass(frozen=True)
class Incoming:
    """A typed message, or (``callback_id`` set) a tap on an inline button (BF-D38)."""

    chat_id: int
    text: str
    at: datetime
    callback_id: str | None = None  # Telegram callback_query id: a button tap
    data: str = ""  # the tapped button's callback data
    user_id: int | None = None  # who tapped (Telegram ``from.id``)
    message_id: int | None = None  # the message that carries the button
    message_text: str = ""  # its text (to show the outcome when the batch is decided)


Markup = Mapping[str, Any]  # a Telegram ``reply_markup`` object


class ChatTransport(Protocol):
    def send(self, chat_id: int, text: str) -> None: ...
    def poll(self) -> list[Incoming]: ...


@runtime_checkable
class ButtonTransport(Protocol):
    """A transport that can also show buttons (BF-D38); others get plain text."""

    def send(self, chat_id: int, text: str) -> None: ...
    def poll(self) -> list[Incoming]: ...
    def send_markup(self, chat_id: int, text: str, markup: Markup) -> int | None: ...
    def answer_callback(self, callback_id: str, text: str = "") -> None: ...
    def edit_text(self, chat_id: int, message_id: int, text: str) -> None: ...


@dataclass
class FakeTransport:
    """In-memory transport for tests and dry runs."""

    inbox: list[Incoming] = field(default_factory=list)
    outbox: list[tuple[int, str]] = field(default_factory=list)
    markups: list[tuple[int, str, Markup]] = field(default_factory=list)
    answers: list[tuple[str, str]] = field(default_factory=list)
    edits: list[tuple[int, int, str]] = field(default_factory=list)

    def send(self, chat_id: int, text: str) -> None:
        self.outbox.append((chat_id, text))

    def send_markup(self, chat_id: int, text: str, markup: Markup) -> int | None:
        self.outbox.append((chat_id, text))
        self.markups.append((chat_id, text, markup))
        return len(self.outbox)  # a message id

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self.answers.append((callback_id, text))

    def edit_text(self, chat_id: int, message_id: int, text: str) -> None:
        self.edits.append((chat_id, message_id, text))

    def poll(self) -> list[Incoming]:
        out, self.inbox = self.inbox, []
        return out


class TelegramTransport:
    """Telegram Bot API over HTTPS (``sendMessage`` / ``getUpdates`` long polling).

    The token is a Docker secret (``telegram_bot_token``) and never appears in logs.
    """

    def __init__(
        self,
        token: SecretValue,
        opener: Callable[..., Any] = urllib.request.urlopen,
        timeout: int = 20,
    ) -> None:
        self._token = token
        self._open = opener
        self._timeout = timeout
        self._offset = 0

    def _call(self, method: str, params: dict[str, Any]) -> Any:
        url = f"https://api.telegram.org/bot{self._token.reveal()}/{method}"
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, method="POST")  # noqa: S310 - fixed https host
        with self._open(req, timeout=self._timeout + 5) as r:
            body = json.loads(r.read().decode())
        if not body.get("ok"):
            raise RuntimeError(f"telegram {method} failed: {body.get('description')}")
        return body["result"]

    def send(self, chat_id: int, text: str) -> None:
        self._call("sendMessage", {"chat_id": chat_id, "text": text[:4000]})

    def send_markup(self, chat_id: int, text: str, markup: Markup) -> int | None:
        res = self._call(
            "sendMessage",
            {"chat_id": chat_id, "text": text[:4000], "reply_markup": json.dumps(markup)},
        )
        return int(res["message_id"]) if isinstance(res, dict) and "message_id" in res else None

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self._call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text[:200]})

    def edit_text(self, chat_id: int, message_id: int, text: str) -> None:
        # no reply_markup: Telegram removes the message's inline buttons
        self._call(
            "editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text[:4000]}
        )

    def poll(self) -> list[Incoming]:
        res = self._call("getUpdates", {"offset": self._offset, "timeout": self._timeout})
        out: list[Incoming] = []
        for u in res:
            self._offset = max(self._offset, int(u["update_id"]) + 1)
            m = u.get("message") or {}
            if "text" in m:
                at = datetime.fromtimestamp(int(m["date"]), tz=ASX_TZ)
                out.append(Incoming(int(m["chat"]["id"]), str(m["text"]), at))
            cq = u.get("callback_query") or {}
            cm = cq.get("message") or {}
            if cq.get("id") and "chat" in cm:  # BF-D38: a button tap, stamped on arrival
                out.append(
                    Incoming(
                        int(cm["chat"]["id"]),
                        "",
                        datetime.now(ASX_TZ),
                        callback_id=str(cq["id"]),
                        data=str(cq.get("data") or ""),
                        user_id=int((cq.get("from") or {}).get("id", 0)) or None,
                        message_id=int(cm["message_id"]) if "message_id" in cm else None,
                        message_text=str(cm.get("text") or ""),
                    )
                )
        return out


# ---------------------------------------------------------------- approval rules


def deadline(execution_date: Any, hhmm: str = "15:20") -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(execution_date, time(h, m), ASX_TZ)


def approved_seqs(journal: Journal, batch_id: str, until: datetime | None = None) -> set[int]:
    """Sequence numbers approved (and not vetoed) by ``until`` under the batch's mode."""
    b = journal.batch(batch_id)
    if b is None:
        return set()
    seqs = {it.seq for it, _ in journal.intents_of(batch_id)}
    if b["approval_mode"] == "auto":
        return seqs
    ok: set[int] = set()
    veto: set[int] = set()
    refused = False
    for a in journal.approvals(batch_id):
        at = a["at"] if a["at"].tzinfo else a["at"].replace(tzinfo=ASX_TZ)
        if until is not None and at > until:
            continue
        if a["action"] == "OK":
            ok |= seqs if a["seq"] is None else {a["seq"]}
        elif a["action"] == "VETO" and a["seq"] is not None:
            veto.add(a["seq"])
        elif a["action"] == "REFUSE":
            refused = True
    return set() if refused else (ok & seqs) - veto


def render_batch(journal: Journal, batch_id: str, banner: str) -> str:
    b = journal.batch(batch_id)
    if b is None:
        return f"unknown batch {batch_id}"
    lines = [
        banner,
        f"Batch {batch_id} ({b['approval_mode']}), decision {b['decision_date']},"
        f" execution {b['execution_date']}:",
    ]
    for it, st in journal.intents_of(batch_id):
        lines.append(
            f"{it.seq:>2}. {it.side.value} {it.qty} {it.entity} {it.order_type.value} "
            f"lim {it.limit_price} (ref {it.ref_price}, ~A${it.value_at_ref}) "
            f"{it.reason} [{st}]"
        )
    if b["approval_mode"] == "per_order":
        lines.append(f"Reply /ok {batch_id} <n> <code> or /ok {batch_id} all <code> by 15:20.")
    elif b["approval_mode"] == "batch":
        lines.append(f"Reply /approve {batch_id} <code> by 15:30.")
    return "\n".join(lines)


# ---------------------------------------------------------------- buttons (BF-D38)

CB_PREFIX = "bw"  # callback data "bw:<action>[:<batch>[:<n>|all]]", at most 64 bytes
CB_MAX = 64
CODE_RE = re.compile(r"\d{6}")
OPEN_FOR_APPROVAL = (Status.PLANNED, Status.RISK_OK, Status.HELD)
PER_ORDER_BUTTONS_MAX = 24  # beyond this the message keeps "Approve all" and typed /ok n
# Replies of the typed handlers that mean the whole batch is decided (its buttons go)
DECIDED = ("approved all ", "approved batch ", "refused batch ")
BUTTON_HINT = "Or tap a button below, then send your 6-digit code (within 3 minutes)."


def _cb(*parts: str) -> str:
    return ":".join((CB_PREFIX, *parts))


def _button(label: str, *parts: str) -> dict[str, str] | None:
    data = _cb(*parts)
    return {"text": label, "callback_data": data} if len(data.encode()) <= CB_MAX else None


def _rows(*rows: list[dict[str, str] | None]) -> dict[str, Any]:
    return {"inline_keyboard": [[b for b in r if b] for r in rows if any(r)]}


def menu_markup() -> dict[str, Any]:
    """``/menu``: the owner's one-tap commands."""
    return _rows(
        [_button("📊 Status", "st"), _button("⏸ Pause", "pa")],
        [_button("🛑 Kill", "ki"), _button("✋ Stop", "so")],
        [_button("▶️ Resume", "re"), _button("✔️ Continue", "co")],
    )


def batch_markup(journal: Journal, batch_id: str) -> dict[str, Any] | None:
    """The buttons of an approval request; None for an auto batch (nothing to approve)."""
    b = journal.batch(batch_id)
    if b is None or b["approval_mode"] not in ("per_order", "batch"):
        return None
    tools = [_button("📊 Status", "st"), _button("⏸ Pause", "pa")]
    refuse = _button("❌ Refuse batch", "rf", batch_id)
    if b["approval_mode"] == "batch":
        return _rows([_button("✅ Approve batch", "ap", batch_id), refuse], tools)
    seqs = [it.seq for it, st in journal.intents_of(batch_id) if st in OPEN_FOR_APPROVAL]
    each: list[list[dict[str, str] | None]] = []
    if 1 < len(seqs) <= PER_ORDER_BUTTONS_MAX:
        btns = [_button(f"✅ {n}", "ok", batch_id, str(n)) for n in seqs]
        each = [btns[i : i + 6] for i in range(0, len(btns), 6)]
    return _rows([_button("✅ Approve all", "ok", batch_id, "all"), refuse], *each, tools)


def broadcast_batch(
    transport: ChatTransport, chats: Iterable[int], text: str, journal: Journal, batch_id: str
) -> None:
    """An approval request with its buttons where the transport shows them (BF-D38)."""
    markup = batch_markup(journal, batch_id)
    if markup is None or not isinstance(transport, ButtonTransport):
        broadcast(transport, chats, text)
        return
    for c in chats:
        transport.send_markup(c, text + "\n" + BUTTON_HINT, markup)


@dataclass(frozen=True)
class _Pending:
    """A tap waiting for the owner's 6-digit code: the typed command it completes."""

    command: str  # e.g. "/ok EMG2_18_PAPER-2026-11-30-R all" (the code is appended)
    what: str
    at: datetime
    message_id: int | None = None
    message_text: str = ""


# ---------------------------------------------------------------- the bot


@dataclass
class ApprovalBot:
    journal: Journal
    transport: ChatTransport
    verifier: TotpVerifier
    allowed_chats: frozenset[int]
    on_kill: Callable[[], int] | None = None  # cancels open orders; returns the count
    approval_deadline: str = "15:20"  # L8, config ``execution.approval_deadline``
    code_window_s: int = 180  # BF-D38: a code completes a tap within 3 minutes
    confirm_window_s: int = 60  # BF-D38: Kill / Stop need a second tap within 1 minute
    _pending: dict[int, _Pending] = field(default_factory=dict, init=False, repr=False)
    _confirm: dict[int, tuple[str, datetime]] = field(default_factory=dict, init=False, repr=False)

    def handle_all(self) -> int:
        n = 0
        for m in self.transport.poll():
            self.handle(m)
            n += 1
        return n

    def handle(self, m: Incoming) -> str:
        if m.callback_id is not None:
            return self._tap(m)
        if m.chat_id not in self.allowed_chats:
            return "ignored"  # BP-11: silently ignore strangers
        text = m.text.strip()
        cmd = text.split()[0].lower().split("@")[0] if text else ""
        if cmd in ("/menu", "/start") and isinstance(self.transport, ButtonTransport):
            reply = "Big Wins (PAPER). Tap a button; approvals and re-arming ask for your code."
            self.transport.send_markup(m.chat_id, reply, menu_markup())
            return reply
        reply = self._with_code(m, text) if CODE_RE.fullmatch(text) else self._dispatch(m)
        self.transport.send(m.chat_id, reply)
        return reply

    # ------------------------------------------------------------ taps (BF-D38)
    def _say(self, chat_id: int, text: str, markup: Markup | None = None) -> None:
        if markup is not None and isinstance(self.transport, ButtonTransport):
            self.transport.send_markup(chat_id, text, markup)
        else:
            self.transport.send(chat_id, text)

    def _quiet(self, fn: Callable[[], None]) -> None:
        """Answer / edit calls are cosmetic: a Telegram error there changes nothing."""
        with contextlib.suppress(RuntimeError, OSError):
            fn()

    def _tap(self, m: Incoming) -> str:
        """A button tap: the same allow-list as typed commands (BP-11), and in a private
        chat the tapper must be that chat's owner. The query is always answered (the
        phone stops its spinner); a stranger gets an empty answer and nothing else."""
        bt = self.transport if isinstance(self.transport, ButtonTransport) else None
        cid = m.callback_id or ""
        stranger = m.chat_id not in self.allowed_chats or (
            m.chat_id > 0 and m.user_id is not None and m.user_id != m.chat_id
        )
        if stranger:
            if bt is not None:
                self._quiet(lambda: bt.answer_callback(cid, ""))
            return "ignored"
        reply, toast, markup = self._tap_action(m)
        if bt is not None:
            self._quiet(lambda: bt.answer_callback(cid, toast))
        self._say(m.chat_id, reply, markup)
        return reply

    def _tap_action(self, m: Incoming) -> tuple[str, str, Markup | None]:  # noqa: PLR0911
        parts = m.data.split(":")
        if len(parts) < 2 or parts[0] != CB_PREFIX:
            return "unknown button", "unknown button", None
        act, args = parts[1], parts[2:]
        if act == "st":
            return self._dispatch(replace(m, text="/status")), "status", None
        if act == "pa":  # risk-reducing: one tap, like /pause
            return self._dispatch(replace(m, text="/pause")), "paused", None
        if act in ("ki", "so"):  # Kill / Stop: a second tap confirms (no fat-finger)
            self._confirm[m.chat_id] = (act, m.at)
            name = "KILL" if act == "ki" else "STOP"
            what = (
                "stops all new orders and cancels open orders at the broker"
                if act == "ki"
                else "buys stay paused with no automatic resume; sells go on (L11 d)"
            )
            confirm = _rows(
                [_button(f"{'🛑' if act == 'ki' else '✋'} Yes, {name}", act + "!"),
                 _button("Cancel", "cx")]
            )  # fmt: skip
            return f"Tap again to confirm {name}: {what}.", "tap again to confirm", confirm
        if act in ("ki!", "so!"):
            want, at = self._confirm.pop(m.chat_id, ("", m.at))
            fresh = timedelta(0) <= m.at - at <= timedelta(seconds=self.confirm_window_s)
            if want != act[:2] or not fresh:
                return "Not confirmed (too late or not asked): tap the button again.", "", None
            cmd = "/kill" if act == "ki!" else "/stop"
            return self._dispatch(replace(m, text=cmd)), "done", None
        if act == "cx":
            self._confirm.pop(m.chat_id, None)
            self._pending.pop(m.chat_id, None)
            return "Cancelled. Nothing changed.", "cancelled", None
        if act in ("re", "co"):
            cmd, what = ("/resume", "re-arm (resume buying)") if act == "re" else (
                "/continue", "confirm continuing (L11 stage 3)")  # fmt: skip
            return self._ask_code(m, cmd, what)
        if act in ("ok", "ap", "rf") and args:
            return self._tap_batch(m, act, args)
        return "unknown button", "unknown button", None

    def _tap_batch(  # noqa: PLR0911 - one refusal per rule
        self, m: Incoming, act: str, args: list[str]
    ) -> tuple[str, str, Markup | None]:
        """Approve / refuse buttons: the batch must exist, be open and before its deadline
        now; the code message is checked again by the typed handler (same rules)."""
        batch_id = args[0]
        b = self.journal.batch(batch_id)
        if b is None:
            return f"unknown batch {batch_id}", "refused", None
        if b["execution_date"] is not None and m.at > deadline(
            b["execution_date"], self.approval_deadline
        ):
            return (
                f"refused: past the approval deadline ({self.approval_deadline}) of {batch_id}; "
                "unapproved orders lapse",
                "refused: too late",
                None,
            )
        if any(a["action"] == "REFUSE" for a in self.journal.approvals(batch_id)):
            return f"refused: batch {batch_id} was already refused", "refused", None
        if act == "rf":
            return self._ask_code(m, f"/refuse {batch_id}", f"refuse batch {batch_id}")
        if act == "ap":
            if b["approval_mode"] != "batch":
                return "this batch needs per-order approval", "refused", None
            return self._ask_code(m, f"/approve {batch_id}", f"approve batch {batch_id}")
        target = args[1] if len(args) > 1 else ""
        done = approved_seqs(self.journal, batch_id)
        open_ = {
            it.seq: it
            for it, st in self.journal.intents_of(batch_id)
            if st in OPEN_FOR_APPROVAL and it.seq not in done
        }
        if b["approval_mode"] != "per_order":
            return "this batch is approved as a whole", "refused", None
        if not open_:
            return f"nothing left to approve in {batch_id}", "nothing to approve", None
        if target == "all":
            n = len(self.journal.intents_of(batch_id))
            return self._ask_code(m, f"/ok {batch_id} all", f"approve all {n} orders of {batch_id}")
        if not target.isdigit() or int(target) not in open_:
            return f"order {target} of {batch_id} is not waiting for approval", "refused", None
        it = open_[int(target)]
        return self._ask_code(
            m,
            f"/ok {batch_id} {target}",
            f"approve order {target} ({it.side.value} {it.qty} {it.entity}) of {batch_id}",
        )

    def _ask_code(self, m: Incoming, command: str, what: str) -> tuple[str, str, Markup | None]:
        self._pending[m.chat_id] = _Pending(command, what, m.at, m.message_id, m.message_text)
        mins = self.code_window_s // 60
        return (
            f"Send your 6-digit code to {what} (within {mins} minutes).",
            "send your code",
            {"force_reply": True, "input_field_placeholder": "6-digit code"},
        )

    def _with_code(self, m: Incoming, code: str) -> str:
        """A bare 6-digit message completes the chat's waiting tap through the typed
        command's own handler (same TOTP check, single use, same deadline at this
        message's time). The waiting tap is used up either way."""
        p = self._pending.pop(m.chat_id, None)
        late = p is None or not (
            timedelta(seconds=-5) <= m.at - p.at <= timedelta(seconds=self.code_window_s)
        )
        if p is None or late:
            return (
                "No button is waiting for a code (a code counts for "
                f"{self.code_window_s // 60} minutes after a tap). Tap the button again."
            )
        reply = self._dispatch(replace(m, text=f"{p.command} {code}"))
        bt = self.transport if isinstance(self.transport, ButtonTransport) else None
        if bt is not None and p.message_id is not None and reply.startswith(DECIDED):
            body = p.message_text or p.what
            mid = p.message_id
            self._quiet(lambda: bt.edit_text(m.chat_id, mid, f"{body}\n\nDONE: {reply}"))
        return reply

    def _dispatch(self, m: Incoming) -> str:  # noqa: PLR0911 - one return per command
        parts = m.text.strip().split()
        if not parts:
            return "empty command"
        cmd, args = parts[0].lower().split("@")[0], parts[1:]
        actor = f"telegram:{m.chat_id}"
        if cmd == "/pause":
            self.journal.set_safety(SafetyLevel.PAUSED, "owner /pause", actor, m.at)
            return "PAUSED: buys stop, registered sells proceed. /resume <code> to re-arm."
        if cmd == "/kill":
            self.journal.set_safety(SafetyLevel.KILLED, "owner /kill", actor, m.at)
            n = self.on_kill() if self.on_kill else 0
            return f"KILLED: no new orders; {n} open order(s) cancelled. /resume <code> to re-arm."
        if cmd == "/status":
            return f"safety {self.journal.safety_level().value}"
        if cmd == "/resume":
            if len(args) != 1 or not self.verifier.verify(args[0], m.at):
                return "refused: /resume needs a valid one-time code"
            self.journal.set_safety(SafetyLevel.NORMAL, "owner /resume (2FA)", actor, m.at)
            self.journal.mark_job(f"l11:end:{m.at.isoformat()}", {"why": "owner /resume"}, m.at)
            return "re-armed: NORMAL"
        if cmd == "/stop":  # L11 (d): the owner says stop; buys stay paused, sells go on
            self.journal.set_safety(SafetyLevel.PAUSED, "owner /stop (L11)", actor, m.at)
            self.journal.mark_job(f"l11:stop:{m.at.isoformat()}", {"actor": actor}, m.at)
            return "STOP recorded (L11 d): buys stay paused, sells go on. /resume <code> re-arms."
        if cmd == "/continue":  # L11 stage 3: the owner's written confirmation to continue
            if len(args) != 1 or not self.verifier.verify(args[0], m.at):
                return "refused: /continue needs a valid one-time code"
            self.journal.mark_job(f"l11:confirm:{m.at.isoformat()}", {"actor": actor}, m.at)
            return (
                "confirmation recorded (L11 stage 3): buys resume at the next decision "
                "if the staged test passes"
            )
        if cmd in ("/idmap", "/idmap_reject"):  # BF-D19: confirm or undo a code change
            return self._idmap(cmd, args, actor, m.at)
        if cmd in ("/ok", "/veto", "/approve", "/refuse"):
            return self._approval(cmd, args, actor, m.at)
        return f"unknown command {cmd}"

    def _idmap(self, cmd: str, args: list[str], actor: str, at: datetime) -> str:  # noqa: PLR0911
        """``/idmap OLD NEW [RATIO] <code>`` confirms a code change, or records one the
        vendor data do not link (a rename such as Platinum -> L1 Group) with the share
        ratio (``1:10`` = 1 new for 10 old; default 1; BF-D25); ``/idmap_reject OLD
        <code>`` undoes one. Both need a valid one-time code."""
        arity = len(args) in (3, 4) if cmd == "/idmap" else len(args) == 2
        if not arity or not self.verifier.verify(args[-1], at):
            return f"refused: {cmd} needs the codes and a valid one-time code"
        old = args[0].upper()
        rec = self.journal.identity_records().get(old)
        if cmd == "/idmap_reject":
            if rec is None:
                return f"refused: no code change recorded for {old}"
            new = str(rec["new_code"])
            self.journal.add_identity(old, new, "REJECTED", "OWNER", None, actor, "owner undo", at)
            return (
                f"code change {old} -> {new} undone: {old} is carried again at its last mark "
                "(review the holding)"
            )
        new = args[1].upper()
        try:
            ratio = parse_ratio(args[2]) if len(args) == 4 else None
        except CaError as e:
            return f"refused: {e}"
        if new == old or not re.fullmatch(r"[A-Z0-9]{1,6}", new):
            return f"refused: bad new code {new!r}"
        if rec is None and old not in self.journal.known_codes():
            return f"refused: {old} is not held or traded by any book"
        applied = rec is not None and rec["status"] in ("PROPOSED", "CONFIRMED")
        if applied and rec is not None and rec["new_code"] != new:
            return (
                f"refused: the recorded change is {old} -> {rec['new_code']}; "
                f"/idmap_reject {old} <code> first"
            )
        if ratio is None and applied and rec is not None and rec.get("ratio"):
            ratio = Decimal(str(rec["ratio"]))  # confirming as proposed
        note = "owner"
        if applied and rec is not None and Decimal(str(rec.get("ratio") or 1)) != (ratio or 1):
            note = f"owner; ratio replaces the {rec['status']} {rec.get('ratio') or 1}"
        self.journal.add_identity(old, new, "CONFIRMED", "OWNER", None, actor, note, at, ratio)
        k = f" ratio {ratio.normalize():f}" if ratio is not None and ratio != 1 else ""
        return f"code change {old} -> {new}{k} confirmed"

    def _approval(self, cmd: str, args: list[str], actor: str, at: datetime) -> str:  # noqa: PLR0911
        if len(args) < 2:
            return "usage: /ok <batch> <n|all> <code>; /veto <batch> <n> <code>"
        batch_id, code = args[0], args[-1]
        b = self.journal.batch(batch_id)
        if b is None:
            return f"unknown batch {batch_id}"
        if not self.verifier.verify(code, at):
            return "refused: invalid or reused code"
        if b["execution_date"] is not None and at > deadline(
            b["execution_date"], self.approval_deadline
        ):
            return (
                f"refused: past the approval deadline ({self.approval_deadline}); "
                "unapproved orders lapse"
            )
        intents = {it.seq: (it, st) for it, st in self.journal.intents_of(batch_id)}
        if cmd == "/approve":
            if b["approval_mode"] != "batch":
                return "this batch needs per-order approval: /ok <batch> <n|all> <code>"
            self.journal.add_approval(batch_id, None, "OK", actor, at)
            return f"approved batch {batch_id}"
        if cmd == "/refuse":
            self.journal.add_approval(batch_id, None, "REFUSE", actor, at)
            return f"refused batch {batch_id}: nothing will be sent"
        target = args[1] if len(args) == 3 else ""
        if cmd == "/ok" and target == "all":
            self.journal.add_approval(batch_id, None, "OK", actor, at)
            return f"approved all {len(intents)} orders of {batch_id}"
        if not target.isdigit() or int(target) not in intents:
            return f"no order {target!r} in {batch_id}"
        seq = int(target)
        it, st = intents[seq]
        if cmd == "/veto":
            if it.side is not Side.BUY:
                return "refused: a sell cannot be vetoed alone (/refuse <batch> <code>)"
            self.journal.add_approval(batch_id, seq, "VETO", actor, at)
            return f"vetoed {seq}: {it.entity}"
        if st not in (Status.PLANNED, Status.RISK_OK, Status.HELD):
            return f"order {seq} is {st}; nothing to approve"
        self.journal.add_approval(batch_id, seq, "OK", actor, at)
        return f"approved {seq}: {it.side.value} {it.qty} {it.entity}"


def broadcast(transport: ChatTransport, chats: Iterable[int], text: str) -> None:
    for c in chats:
        transport.send(c, text)
