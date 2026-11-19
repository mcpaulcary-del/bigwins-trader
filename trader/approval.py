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
``/pause`` and ``/kill`` act in one step without a code (they only reduce risk,
BW-RSK-30); ``/resume <code>`` re-arms and needs the second factor. ``<code>`` is a
6-digit TOTP (RFC 6238, SHA-1, 30 s) from the owner's authenticator; each code is
accepted once. Commands are accepted only from allow-listed Telegram chat ids
(BP-11). The TOTP seed and the bot token are Docker secrets, never config.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import struct
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any, Protocol

from trader.constants import ASX_TZ
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
    chat_id: int
    text: str
    at: datetime


class ChatTransport(Protocol):
    def send(self, chat_id: int, text: str) -> None: ...
    def poll(self) -> list[Incoming]: ...


@dataclass
class FakeTransport:
    """In-memory transport for tests and dry runs."""

    inbox: list[Incoming] = field(default_factory=list)
    outbox: list[tuple[int, str]] = field(default_factory=list)

    def send(self, chat_id: int, text: str) -> None:
        self.outbox.append((chat_id, text))

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

    def poll(self) -> list[Incoming]:
        res = self._call("getUpdates", {"offset": self._offset, "timeout": self._timeout})
        out: list[Incoming] = []
        for u in res:
            self._offset = max(self._offset, int(u["update_id"]) + 1)
            m = u.get("message") or {}
            if "text" in m:
                at = datetime.fromtimestamp(int(m["date"]), tz=ASX_TZ)
                out.append(Incoming(int(m["chat"]["id"]), str(m["text"]), at))
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


# ---------------------------------------------------------------- the bot


@dataclass
class ApprovalBot:
    journal: Journal
    transport: ChatTransport
    verifier: TotpVerifier
    allowed_chats: frozenset[int]
    on_kill: Callable[[], int] | None = None  # cancels open orders; returns the count

    def handle_all(self) -> int:
        n = 0
        for m in self.transport.poll():
            self.handle(m)
            n += 1
        return n

    def handle(self, m: Incoming) -> str:
        if m.chat_id not in self.allowed_chats:
            return "ignored"  # BP-11: silently ignore strangers
        reply = self._dispatch(m)
        self.transport.send(m.chat_id, reply)
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
            return "re-armed: NORMAL"
        if cmd in ("/ok", "/veto", "/approve", "/refuse"):
            return self._approval(cmd, args, actor, m.at)
        return f"unknown command {cmd}"

    def _approval(self, cmd: str, args: list[str], actor: str, at: datetime) -> str:  # noqa: PLR0911
        if len(args) < 2:
            return "usage: /ok <batch> <n|all> <code>; /veto <batch> <n> <code>"
        batch_id, code = args[0], args[-1]
        b = self.journal.batch(batch_id)
        if b is None:
            return f"unknown batch {batch_id}"
        if not self.verifier.verify(code, at):
            return "refused: invalid or reused code"
        if b["execution_date"] is not None and at > deadline(b["execution_date"]):
            return "refused: past the approval deadline (15:20); the batch lapses"
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
