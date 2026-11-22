"""BF-D40 / BF-D41: the trader's messages reach the phone app (inbox + Web Push),
Telegram is optional, and the healthchecks.io heartbeat."""

from __future__ import annotations

import io
import json
import os
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import http_ece
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from trader.app_notify import (
    AppNotifier,
    ChannelTransport,
    WebPush,
    b64url,
    classify,
    push_host_ok,
)
from trader.app_store import add_push_sub, inbox_rows, push_sub_rows, set_state
from trader.approval import APP_CHAT, FakeTransport, broadcast, broadcast_batch
from trader.bfast_config import load_bfast_config
from trader.heartbeat import Heartbeat, ping_url
from trader.journal import Journal
from trader.report import PAPER_BANNER
from trader.secret_check import check_secrets, stack_secrets, trader_secrets
from trader.secrets import SecretValue

ROOT = Path(__file__).resolve().parent.parent
T0 = datetime(2026, 12, 1, 3, 0, tzinfo=UTC)


def _vapid_pem() -> SecretValue:
    k = ec.generate_private_key(ec.SECP256R1())
    pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                          serialization.NoEncryption())  # fmt: skip
    return SecretValue(pem.decode())


def _browser() -> tuple[ec.EllipticCurvePrivateKey, bytes, dict[str, str]]:
    ua = ec.generate_private_key(ec.SECP256R1())
    pub = ua.public_key().public_bytes(serialization.Encoding.X962,
                                       serialization.PublicFormat.UncompressedPoint)  # fmt: skip
    auth = os.urandom(16)
    return ua, auth, {"p256dh": b64url(pub), "auth": b64url(auth)}


class _Sender:
    def __init__(self, status: int = 201) -> None:
        self.sent: list[tuple[str, bytes, dict[str, str]]] = []
        self.status = status

    def __call__(self, url: str, body: bytes, headers: Any) -> int:
        self.sent.append((url, body, dict(headers)))
        return self.status


def _notifier(status: int = 201) -> tuple[Journal, AppNotifier, _Sender, Any]:
    j = Journal.sqlite()
    sender = _Sender(status)
    push = WebPush(_vapid_pem(), sender=sender)
    ua, auth, keys = _browser()
    add_push_sub(j, "https://fcm.googleapis.com/fcm/send/xyz", keys["p256dh"], keys["auth"],
                 "owner@example.com", T0)  # fmt: skip
    return j, AppNotifier(j, push, clock=lambda: T0), sender, (ua, auth)


def test_BF_D40_web_push_payload_encrypted_signed_and_sent() -> None:
    j, n, sender, (ua, auth) = _notifier()
    n.notify("PAGE HIGH PRIORITY L11 integrity check FAILED\ndetails")
    assert len(sender.sent) == 1
    url, body, h = sender.sent[0]
    assert url.startswith("https://fcm.googleapis.com/")
    assert h["Authorization"].startswith("vapid t=") and ",k=" in h["Authorization"]
    assert h["Content-Encoding"] == "aes128gcm" and h["Urgency"] == "high" and int(h["TTL"]) > 0
    data = json.loads(http_ece.decrypt(body, private_key=ua, auth_secret=auth, version="aes128gcm"))
    assert data["title"].startswith("PAGE") and data["kind"] == "page" and data["url"] == "/inbox"
    row = inbox_rows(j)[0]
    assert row["kind"] == "page" and row["push"] == "sent 1/1 high"


def test_BF_D40_reports_normal_urgency_and_switchable_pages_are_not() -> None:
    j, n, sender, _ = _notifier()
    report = f"{PAPER_BANNER}\nindex\n\nEMG2_18_PAPER - 2026-12-01 - safety NORMAL\nValue A$1"
    n.notify(report)
    assert sender.sent[-1][2]["Urgency"] == "normal"
    assert inbox_rows(j)[0]["title"] == "Daily report: EMG2_18_PAPER - 2026-12-01 - safety NORMAL"
    set_state(j, "alerts", {"report": False, "page": False, "approval": False}, T0)
    n.notify(report)
    n.notify("PAGE recon break")
    n.notify("Reminder: 3 order(s) of X are not approved")
    assert [r["kind"] for r in inbox_rows(j)[:3]] == ["approval", "page", "report"]
    assert [s[2]["Urgency"] for s in sender.sent[1:]] == ["high", "high"]  # report not pushed


def test_BF_D40_gone_subscription_is_switched_off() -> None:
    j, n, sender, _ = _notifier(410)
    n.notify("PAGE x")
    assert push_sub_rows(j) == [] and "sent 0/1" in inbox_rows(j)[0]["push"]
    n.notify("PAGE y")
    assert inbox_rows(j)[0]["push"] == "no device" and len(sender.sent) == 1


def test_BF_D40_push_only_to_known_push_services() -> None:
    assert push_host_ok("https://web.push.apple.com/abc")
    assert push_host_ok("https://updates.push.services.mozilla.com/wpush/v2/x")
    for bad in ("http://fcm.googleapis.com/x", "https://evil.example/x",
                "https://fcm.googleapis.com.evil.example/x", "https://169.254.169.254/"):  # fmt: skip
        assert not push_host_ok(bad)
    push = WebPush(_vapid_pem(), sender=_Sender())
    with pytest.raises(ValueError, match="push service"):
        push.build({"endpoint": "https://evil.example/x", "p256dh": "a", "auth": "b"}, {}, "high")


def test_BF_D40_channel_transport_sends_trader_messages_to_the_app() -> None:
    from tests.test_bf_execution import BOOK, X, _batch, _ctx, _sim
    from trader.execution import Executor

    j, n, sender, _ = _notifier()
    tg = FakeTransport()
    tr = ChannelTransport(tg, n)
    broadcast(tr, frozenset({APP_CHAT, 7}), "PAGE job failed")
    assert tg.outbox == [(7, "PAGE job failed")] and inbox_rows(j)[0]["kind"] == "page"
    sim = _sim()
    b = _batch(2)
    Executor(j, sim, BOOK).plan(b, "per_order", X, _ctx(sim))
    broadcast_batch(tr, frozenset({APP_CHAT}), "Decision: 3 orders", j, b.batch_id)
    row = inbox_rows(j)[0]
    assert row["kind"] == "approval" and row["link"] == f"/orders/{b.batch_id}"
    assert "tap a button" not in row["body"]
    app_only = ChannelTransport(None, n)
    app_only.send(7, "to nobody")  # no Telegram: nothing, no error
    assert app_only.poll() == []


def test_BF_D40_classify() -> None:
    assert classify("PAGE x") == "page" and classify("RECON break") == "page"
    assert classify("Reminder: 2 order(s)") == "approval"
    assert classify(f"{PAPER_BANNER}\nrest") == "report"
    assert classify("re-armed: NORMAL") == "info"


def _cfg(tmp_path: Path, **changes: Any) -> Path:
    import yaml

    raw = yaml.safe_load((ROOT / "config/bfast.yaml").read_text())
    for k, v in changes.items():
        sec, key = k.split("__")
        raw.setdefault(sec, {})[key] = v
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(raw))
    return p


def _secrets(d: Path, names: tuple[str, ...]) -> Path:
    d.mkdir(mode=0o700)
    for n in names:
        (d / n).write_text("x")
        (d / n).chmod(0o444)
    return d


def test_BF_D40_telegram_off_passes_secret_checks_without_the_bot_token(tmp_path: Path) -> None:
    from trader.bfast_cli import main

    cfg = load_bfast_config(ROOT / "config/bfast.yaml")
    assert cfg.notify.channel == "app" and cfg.app.allowed_logins == []  # repo copy: empty
    assert "telegram_bot_token" not in stack_secrets("app")
    assert "vapid_private_key" in trader_secrets("app")
    d = _secrets(tmp_path / "s", stack_secrets("app"))
    assert check_secrets(stack_secrets("app"), d) == []
    assert (
        main(
            ["check-secrets", "--all", "--dir", str(d), "--config", str(ROOT / "config/bfast.yaml")]
        )
        == 0
    )
    tg = _cfg(tmp_path, notify__channel="telegram")
    assert main(["check-secrets", "--all", "--dir", str(d), "--config", str(tg)]) == 2


def test_BF_D40_telegram_on_still_needs_its_token_and_chats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from trader import secret_check
    from trader.bfast_cli import main

    both = stack_secrets("both")
    assert "telegram_bot_token" in both and "vapid_private_key" in both
    assert "vapid_private_key" not in stack_secrets("telegram")
    p = _cfg(tmp_path, notify__channel="telegram", broker__account_id="DU1234567")
    with pytest.raises(SystemExit, match="allowed_chat_ids is empty"):
        main(["run", "--config", str(p)])
    p = _cfg(tmp_path, notify__channel="both", broker__account_id="DU1234567",
             telegram__allowed_chat_ids=[1])  # fmt: skip
    d = _secrets(tmp_path / "s2", trader_secrets("app"))
    monkeypatch.setattr(secret_check, "SECRETS_DIR_DEFAULT", d)
    with pytest.raises(SystemExit, match="telegram_bot_token: missing"):
        main(["run", "--config", str(p)])


def test_BF_D40_telegram_on_bot_and_buttons_unchanged() -> None:
    """With Telegram on, typed commands and buttons go through the same bot (BF-D38)."""
    from tests.test_bf_buttons import _setup, _tap

    j, bot, tr, b, _ = _setup()
    reply = _tap(bot, f"bw:ok:{b.batch_id}:all")
    assert "Send your 6-digit code" in reply


def test_BF_D40_compose_and_host_script(tmp_path: Path) -> None:
    import yaml

    dc = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    svc = dc["services"]
    assert "telegram_bot_token" not in dc["secrets"]
    assert sorted(svc["secrets-check"]["secrets"]) == sorted(stack_secrets("app"))
    assert sorted(svc["trader"]["secrets"]) == sorted(trader_secrets("app"))
    assert "control" in svc["trader"]["networks"] and "control" in svc["dashboard"]["networks"]
    assert dc["networks"]["control"]["internal"] is True
    assert "ports" not in svc["trader"]
    tg = yaml.safe_load((ROOT / "deploy/docker-compose.telegram.yml").read_text())
    assert tg["services"]["trader"]["secrets"] == ["telegram_bot_token"]
    host = (ROOT / "deploy/check_secrets.sh").read_text()
    assert "vapid_private_key" in host and "telegram|both" in host


# ---------------------------------------------------------------- heartbeat (BF-D41)


class _Resp(io.BytesIO):
    status = 200

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *a: object) -> None:
        return None


def test_BF_D41_heartbeat_none_is_off() -> None:
    assert ping_url(SecretValue("none")) is None and ping_url(SecretValue("  ")) is None
    assert ping_url(None) is None
    with pytest.raises(ValueError, match="https"):
        ping_url(SecretValue("http://hc-ping.com/x"))
    calls: list[Any] = []
    hb = Heartbeat(None, opener=lambda *a, **k: calls.append(a))
    assert hb.tick(T0) == "off" and calls == []


def test_BF_D41_heartbeat_pings_every_interval_and_records() -> None:
    j = Journal.sqlite()
    calls: list[str] = []

    def opener(req: Any, timeout: int) -> _Resp:
        calls.append(req.full_url)
        return _Resp(b"OK")

    url = "https://hc-ping.com/00000000-0000-0000-0000-000000000000"
    hb = Heartbeat(url, j, opener=opener, every_s=300)
    assert hb.tick(T0) == "ok" and hb.tick(T0 + timedelta(seconds=100)) == "wait"
    assert hb.tick(T0 + timedelta(seconds=301)) == "ok" and calls == [url, url]
    from trader.app_store import get_state

    st = get_state(j, "heartbeat")
    assert st is not None and st[0]["ok"] is True and url not in json.dumps(st[0])


def test_BF_D41_heartbeat_failure_told_once_without_the_url() -> None:
    j = Journal.sqlite()
    told: list[str] = []
    url = "https://hc-ping.com/secret-uuid"

    def down(req: Any, timeout: int) -> _Resp:
        raise urllib.error.URLError("no route")

    hb = Heartbeat(url, j, told.append, opener=down, every_s=60)
    assert hb.tick(T0) == "fail" and hb.tick(T0 + timedelta(seconds=61)) == "fail"
    assert len(told) == 1 and "secret-uuid" not in told[0] and "URLError" in told[0]

    def err(req: Any, timeout: int) -> _Resp:
        raise urllib.error.HTTPError(url, 500, "x", {}, None)  # type: ignore[arg-type]

    hb.opener = err
    assert hb.tick(T0 + timedelta(seconds=200)) == "fail"
    hb.opener = lambda req, timeout: _Resp(b"OK")
    assert hb.tick(T0 + timedelta(seconds=300)) == "ok"
    hb.opener = down
    hb.tick(T0 + timedelta(seconds=400))
    assert len(told) == 2  # a new streak is told again
