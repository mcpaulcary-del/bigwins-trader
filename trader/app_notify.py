"""Notifications to the owner's phone app (BF-D40): the in-app inbox and Web Push.

Everything the trader used to send to Telegram (daily report, approval requests and
reminders, PAGE alerts, confirmations) goes through ``ChannelTransport``: the app's
"chat" ``APP_CHAT`` writes the message to the journal's inbox (``bf_inbox``: the app shows
the history) and sends a Web Push notification to each subscribed, installed app;
Telegram chats (``notify.channel: telegram | both``) still get the text as before.

Web Push (RFC 8030) with the payload encrypted for the subscription (RFC 8291,
``aes128gcm``, the ``http_ece`` library) and signed with the server's VAPID key (RFC 8292,
``py_vapid``). The VAPID private key is the Docker secret ``vapid_private_key`` (PEM,
generated on the server by ``bigwins vapid``); the public key the browser needs is
derived from it. Only the trader sends pushes (it is the one container with an egress
network); the endpoint must be https on a known push service (no request to any other
host, even if a subscription names one).

PAGE alerts and approval requests are always pushed at high urgency and cannot be
switched off in the app; daily reports and other messages can (``alerts`` state).
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from trader.app_store import (
    add_inbox,
    get_state,
    push_sub_rows,
    set_push_sub,
)
from trader.approval import APP_CHAT, BUTTON_HINT, ButtonTransport, ChatTransport, Incoming, Markup
from trader.journal import Journal
from trader.report import L14_BANNER, PAPER_BANNER
from trader.secrets import SecretValue

PUSH_HOSTS = (  # the browsers' push services (Chrome/Android, Firefox, Safari/iOS, Edge)
    "fcm.googleapis.com",
    "updates.push.services.mozilla.com",
    "push.services.mozilla.com",
    "web.push.apple.com",
    "api.push.apple.com",
    "notify.windows.com",
)
ALWAYS_ON = frozenset({"page", "approval"})  # cannot be switched off (safety)
SWITCHABLE = ("report", "info", "action")
DEFAULT_SUBJECT = "mailto:bigwins-paper-trader@users.noreply.github.com"
PAYLOAD_MAX = 3000  # bytes of JSON before encryption (push services accept about 4 KB)
BATCH_RE = re.compile(r"^bw:(?:ok|ap|rf):([^:]+)")

Sender = Callable[[str, bytes, Mapping[str, str]], int]  # (url, body, headers) -> HTTP status


def classify(text: str, approval: bool = False) -> str:
    """The inbox kind of a trader message."""
    first = text.strip().splitlines()[0] if text.strip() else ""
    if first.startswith(("PAGE", "RECON")) or "HALTED" in first:
        return "page"
    if approval or first.startswith("Reminder:") or "waiting for approval" in first:
        return "approval"
    if first in (PAPER_BANNER, L14_BANNER):
        return "report"
    return "info"


def title_of(text: str, kind: str) -> str:
    lines = [x for x in text.strip().splitlines() if x.strip()]
    if not lines:
        return "Big Wins"
    if kind == "report":
        day = next((x for x in lines if " - safety " in x), "")
        return ("Daily report: " + day)[:200] if day else "Daily report"
    return lines[0][:200]


def push_host_ok(endpoint: str) -> bool:
    try:
        u = urlsplit(endpoint)
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    return u.scheme == "https" and any(host == h or host.endswith("." + h) for h in PUSH_HOSTS)


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def b64url_dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def urllib_sender(url: str, body: bytes, headers: Mapping[str, str]) -> int:
    req = urllib.request.Request(url, data=body, method="POST", headers=dict(headers))  # noqa: S310 - https push host only
    try:
        with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
            return int(r.status)
    except urllib.error.HTTPError as e:
        return int(e.code)


class WebPush:
    """Encrypts and signs one notification for one subscription and sends it."""

    def __init__(
        self,
        private_pem: SecretValue,
        subject: str = DEFAULT_SUBJECT,
        sender: Sender = urllib_sender,
    ) -> None:
        from py_vapid import Vapid02

        self._vapid = Vapid02.from_pem(private_pem.reveal().encode())
        self._subject = subject
        self.sender = sender

    @property
    def public_key(self) -> str:
        """The VAPID public key (base64url, uncompressed P-256 point) for the browser."""
        from cryptography.hazmat.primitives import serialization

        pk = self._vapid.public_key.public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        return b64url(pk)

    def build(
        self, sub: Mapping[str, Any], payload: Mapping[str, Any], urgency: str, ttl: int = 86400
    ) -> tuple[str, bytes, dict[str, str]]:
        """(endpoint, encrypted body, headers) for one subscription."""
        import http_ece
        from cryptography.hazmat.primitives.asymmetric import ec

        endpoint = str(sub["endpoint"])
        if not push_host_ok(endpoint):
            raise ValueError("push endpoint is not an https push service")
        data = json.dumps(payload, separators=(",", ":")).encode()
        body = http_ece.encrypt(
            data,
            salt=os.urandom(16),
            private_key=ec.generate_private_key(ec.SECP256R1()),
            dh=b64url_dec(str(sub["p256dh"])),
            auth_secret=b64url_dec(str(sub["auth"])),
            version="aes128gcm",
        )
        u = urlsplit(endpoint)
        claims = {"aud": f"{u.scheme}://{u.netloc}", "exp": int(time.time()) + 12 * 3600,
                  "sub": self._subject}  # fmt: skip
        headers = {
            **self._vapid.sign(claims),
            "Content-Encoding": "aes128gcm",
            "Content-Type": "application/octet-stream",
            "TTL": str(ttl),
            "Urgency": urgency,
        }
        return endpoint, body, headers


def public_key_of(pem: SecretValue) -> str:
    return WebPush(pem).public_key


@dataclass
class AppNotifier:
    """Writes every message to the inbox and pushes it to the subscribed apps."""

    journal: Journal
    push: WebPush | None = None
    clock: Callable[[], datetime] = field(default=lambda: datetime.now(UTC))
    log: list[str] = field(default_factory=list)
    label: str = "PAPER"  # BF-D50: push title prefix from the broker mode

    def enabled(self, kind: str) -> bool:
        if kind in ALWAYS_ON:
            return True
        st = get_state(self.journal, "alerts")
        prefs = st[0] if st and isinstance(st[0], dict) else {}
        return bool(prefs.get(kind, kind == "report"))  # default: reports on, others off

    def notify(
        self,
        text: str,
        kind: str | None = None,
        link: str = "",
        source: str = "trader",
        force: bool = False,
    ) -> int:
        """Inbox row + push. ``force``: push even if that kind is switched off (the
        "alerts are on" test message)."""
        kind = kind or classify(text)
        title = title_of(text, kind)
        status = "off"
        if self.push is not None and (force or self.enabled(kind)):
            try:
                status = self._push(kind, title, text, link)
            except Exception as e:  # a push problem never stops the trader
                status = f"error {type(e).__name__}"
        elif self.push is None:
            status = "no key"
        return add_inbox(self.journal, self.clock(), kind, title, text, link, source, status)

    def _push(self, kind: str, title: str, text: str, link: str) -> str:
        assert self.push is not None
        subs = push_sub_rows(self.journal)
        if not subs:
            return "no device"
        urgency = "high" if kind in ALWAYS_ON else "normal"
        body = text if len(text) < 1500 else text[:1500] + "..."
        payload: dict[str, Any] = {
            "title": (f"{self.label} " if not title.startswith(("PAGE", self.label)) else "")
            + title[:120],
            "body": body,
            "url": link or "/inbox",
            "kind": kind,
            "tag": kind if kind == "report" else f"{kind}-{int(time.time())}",
        }
        while len(json.dumps(payload)) > PAYLOAD_MAX:
            payload["body"] = payload["body"][: len(payload["body"]) // 2] + "..."
        ok = 0
        for s in subs:
            try:
                url, data, headers = self.push.build(s, payload, urgency)
                code = self.push.sender(url, data, headers)
            except (OSError, ValueError) as e:
                set_push_sub(self.journal, int(s["id"]), True, f"{type(e).__name__}")
                continue
            if code in (404, 410):  # the subscription is gone (app removed, alerts off)
                set_push_sub(self.journal, int(s["id"]), False, f"HTTP {code}")
            elif 200 <= code < 300:
                ok += 1
            else:
                set_push_sub(self.journal, int(s["id"]), True, f"HTTP {code}")
        return f"sent {ok}/{len(subs)} {urgency}"


def _batch_link(markup: Markup) -> str:
    for row in markup.get("inline_keyboard", []) or []:
        for b in row:
            m = BATCH_RE.match(str(b.get("callback_data", "")))
            if m:
                return f"/orders/{m.group(1)}"
    return "/orders"


class ChannelTransport:
    """The trader's one transport (BF-D40): ``APP_CHAT`` goes to the app (inbox + push),
    every other chat id to Telegram (when it is on). Commands come in only from
    Telegram here; app actions arrive through the control server (BF-D39)."""

    def __init__(self, telegram: ChatTransport | None, app: AppNotifier | None) -> None:
        self.telegram = telegram
        self.app = app

    def send(self, chat_id: int, text: str) -> None:
        if chat_id == APP_CHAT:
            if self.app is not None:
                self.app.notify(text)
        elif self.telegram is not None:
            self.telegram.send(chat_id, text)

    def send_markup(self, chat_id: int, text: str, markup: Markup) -> int | None:
        if chat_id == APP_CHAT:
            if self.app is not None:
                body = text.replace("\n" + BUTTON_HINT, "")
                approval = bool(markup.get("inline_keyboard"))
                link = _batch_link(markup) if approval else ""
                self.app.notify(body, "approval" if approval else None, link)
            return None
        if isinstance(self.telegram, ButtonTransport):
            return self.telegram.send_markup(chat_id, text, markup)
        if self.telegram is not None:
            self.telegram.send(chat_id, text)
        return None

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        if isinstance(self.telegram, ButtonTransport):
            self.telegram.answer_callback(callback_id, text)

    def edit_text(self, chat_id: int, message_id: int, text: str) -> None:
        if isinstance(self.telegram, ButtonTransport) and chat_id != APP_CHAT:
            self.telegram.edit_text(chat_id, message_id, text)

    def poll(self) -> list[Incoming]:
        return self.telegram.poll() if self.telegram is not None else []
