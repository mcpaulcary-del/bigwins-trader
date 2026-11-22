"""BF-D39: actions in the phone app. The same rules as the Telegram commands (same
dispatcher, the same single-use TOTP verifier, the same 15:20 deadline and batch checks),
only for allow-listed Tailscale log-ins, POST + CSRF only, a lock-out after 5 wrong codes,
confirm screens, and every action journaled with its source."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pytest

from tests.test_bf_execution import BOOK, CHAT, SEED, T_APPROVE, X, _batch, _ctx, _sim
from trader.app_control import Control, same_origin
from trader.app_store import add_server_job, inbox_rows
from trader.approval import ApprovalBot, FakeTransport, Incoming, TotpVerifier, totp
from trader.constants import ASX_TZ
from trader.execution import Executor
from trader.journal import Journal
from trader.risk import SafetyLevel
from trader.secrets import SecretValue

OWNER = "owner@example.com"


def _setup(logins: frozenset[str] = frozenset({OWNER}), at: datetime = T_APPROVE) -> tuple[
    Journal, ApprovalBot, Control, str, list[str]
]:  # fmt: skip
    j, sim = Journal.sqlite(), _sim()
    b = _batch(3)
    Executor(j, sim, BOOK).plan(b, "per_order", X, _ctx(sim))
    pages: list[str] = []
    bot = ApprovalBot(j, FakeTransport(), TotpVerifier(SecretValue(SEED)), frozenset({CHAT}),
                      allowed_logins=logins)  # fmt: skip

    def notify(text: str, *a: Any, **k: Any) -> int:
        pages.append(text)
        return 0

    clock = {"t": at}
    ctl = Control(j, bot, logins, book=BOOK, notify=notify, clock=lambda: clock["t"], inline=True)
    ctl.clock_box = clock  # type: ignore[attr-defined]
    return j, bot, ctl, b.batch_id, pages


def _session(ctl: Control, login: str = OWNER) -> tuple[str, str]:
    """GET a page: the session cookie and the form token."""
    status, hdrs, body = ctl.respond("GET", "/act", {"Tailscale-User-Login": login})
    assert status == 200
    sid = hdrs["Set-Cookie"].split(";")[0].split("=", 1)[1]
    token = body.decode().split('name="csrf" value="')[1].split('"')[0]
    return sid, token


def _post(
    ctl: Control,
    form: dict[str, str],
    login: str = OWNER,
    session: tuple[str, str] | None = None,
    path: str = "/act/do",
    **extra: str,
) -> tuple[int, str]:
    sid, token = session or _session(ctl, login)
    form = {"csrf": token, **form}
    hdrs = {"Tailscale-User-Login": login, "Cookie": f"bw_sid={sid}",
            "Sec-Fetch-Site": "same-origin", **extra}  # fmt: skip
    status, _, body = ctl.respond("POST", path, hdrs, urlencode(form).encode())
    return status, body.decode()


def _rows(j: Journal, batch_id: str) -> list[tuple[Any, str]]:
    return [(a["seq"], a["action"]) for a in j.approvals(batch_id)]


def test_BF_D39_login_not_on_the_allow_list_is_refused() -> None:
    j, _, ctl, bid, _ = _setup()
    code = totp(SEED, T_APPROVE)
    st, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": code}, login="eve@example.com",
                     session=_session(ctl))  # fmt: skip
    assert st == 403 and "may not act" in page and j.approvals(bid) == []
    st, _, _ = ctl.respond("GET", "/act/confirm?a=pa", {"Tailscale-User-Login": "eve@example.com"})
    assert st == 403
    assert ctl.respond("POST", "/act/do", {}, b"a=pa")[0] == 403  # no header at all
    assert j.safety_level() is SafetyLevel.NORMAL
    # the bot re-checks the log-in itself (defence in depth)
    _, bot, _, _, _ = _setup()
    m = Incoming(0, "/pause", T_APPROVE, source="app", login="eve@example.com")
    assert bot.handle(m) == "ignored"


def test_BF_D39_empty_allow_list_disables_actions_viewing_explains() -> None:
    j, _, ctl, bid, _ = _setup(frozenset())
    st, _, body = ctl.respond("GET", "/act", {"Tailscale-User-Login": OWNER})
    assert st == 200 and "Actions are off" in body.decode() and "allowed_logins" in body.decode()
    st, _, body = ctl.respond("POST", "/act/do", {"Tailscale-User-Login": OWNER}, b"a=pa")
    assert st == 403 and j.safety_level() is SafetyLevel.NORMAL
    assert (
        ApprovalBot(j, FakeTransport(), TotpVerifier(SecretValue(SEED)), frozenset()).handle(
            Incoming(0, "/pause", T_APPROVE, source="app", login=OWNER)
        )
        == "ignored"
    )


def test_BF_D39_approve_all_in_app_writes_the_same_rows_as_typed_ok() -> None:
    j, _, ctl, bid, _ = _setup()
    code = totp(SEED, T_APPROVE)
    st, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": code})
    assert st == 200 and f"approved all 4 orders of {bid}" in page
    j2, bot2, _, bid2, _ = _setup()
    bot2.handle(Incoming(CHAT, f"/ok {bid2} all {code}", T_APPROVE))
    assert _rows(j, bid) == _rows(j2, bid2) == [(None, "OK")]
    assert j.approvals(bid)[0]["actor"] == f"app:{OWNER}"
    assert j2.approvals(bid2)[0]["actor"] == f"telegram:{CHAT}"
    act = [r for r in inbox_rows(j) if r["kind"] == "action"]
    assert act and act[0]["source"] == f"app:{OWNER}" and code not in act[0]["body"]


def test_BF_D39_code_is_single_use_across_app_and_telegram() -> None:
    j, bot, ctl, bid, _ = _setup()
    code = totp(SEED, T_APPROVE)
    assert "approved 1" in _post(ctl, {"a": "ok", "b": bid, "n": "1", "code": code})[1]
    assert bot.handle(Incoming(CHAT, f"/ok {bid} 2 {code}", T_APPROVE)) == (
        "refused: invalid or reused code"
    )
    later = T_APPROVE + timedelta(minutes=2)
    code2 = totp(SEED, later)
    assert bot.handle(Incoming(CHAT, f"/ok {bid} 2 {code2}", later)).startswith("approved 2")
    ctl.clock_box["t"] = later  # type: ignore[attr-defined]
    _, page = _post(ctl, {"a": "ok", "b": bid, "n": "3", "code": code2})
    assert "invalid or reused code" in page
    assert _rows(j, bid) == [(1, "OK"), (2, "OK")]


def test_BF_D39_five_wrong_codes_lock_code_actions_and_page() -> None:
    j, _, ctl, bid, pages = _setup()
    for _ in range(5):
        _, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": "000000"})
        assert "invalid or reused code" in page
    assert ctl.locked(T_APPROVE) is not None
    assert pages and pages[-1].startswith("PAGE app code actions LOCKED")
    _, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": totp(SEED, T_APPROVE)})
    assert "locked" in page and j.approvals(bid) == []
    assert "PAUSED" in _post(ctl, {"a": "pa"})[1]  # risk-reducing actions still work
    # restored after a restart (journaled), lifted after 15 minutes
    ctl2 = Control(j, ctl.bot, frozenset({OWNER}), book=BOOK, inline=True)
    assert ctl2.locked(T_APPROVE + timedelta(minutes=1)) is not None
    assert ctl2.locked(T_APPROVE + timedelta(minutes=16)) is None


def test_BF_D39_late_approval_is_refused() -> None:
    late = datetime(2026, 12, 1, 15, 21, tzinfo=ASX_TZ)
    j, _, ctl, bid, _ = _setup(at=late)
    st, _, body = ctl.respond("GET", f"/act/confirm?a=ok&b={bid}&n=all",
                              {"Tailscale-User-Login": OWNER})  # fmt: skip
    assert "past the approval deadline" in body.decode()
    _, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": totp(SEED, late)})
    assert "past the approval deadline" in page and j.approvals(bid) == []


def test_BF_D39_kill_and_stop_need_the_confirm_button_pause_is_one_tap() -> None:
    j, _, ctl, _, _ = _setup()
    _, page = _post(ctl, {"a": "ki"})
    assert "needs the Yes button" in page and j.safety_level() is SafetyLevel.NORMAL
    st, _, body = ctl.respond("GET", "/act/confirm?a=ki", {"Tailscale-User-Login": OWNER})
    assert "Yes, KILL" in body.decode() and 'name="confirm" value="yes"' in body.decode()
    assert "KILLED" in _post(ctl, {"a": "ki", "confirm": "yes"})[1]
    assert j.safety_level() is SafetyLevel.KILLED
    _post(ctl, {"a": "so"})
    assert "STOP recorded" in _post(ctl, {"a": "so", "confirm": "yes"})[1]
    j2, _, ctl2, _, _ = _setup()
    assert "PAUSED" in _post(ctl2, {"a": "pa"})[1] and j2.safety_level() is SafetyLevel.PAUSED
    assert any(
        e["detail"].get("actor") == f"app:{OWNER}" for e in j2.events() if e["kind"] == "safety"
    )


def test_BF_D39_resume_needs_a_valid_code() -> None:
    j, _, ctl, _, _ = _setup()
    _post(ctl, {"a": "pa"})
    assert "enter your 6-digit code" in _post(ctl, {"a": "re"})[1]
    assert "needs a valid one-time code" in _post(ctl, {"a": "re", "code": "123456"})[1]
    assert "re-armed" in _post(ctl, {"a": "re", "code": totp(SEED, T_APPROVE)})[1]
    assert j.safety_level() is SafetyLevel.NORMAL


def test_BF_D39_csrf_missing_or_wrong_token_or_cross_site_refused() -> None:
    j, _, ctl, _, _ = _setup()
    sid, token = _session(ctl)
    base = {"Tailscale-User-Login": OWNER, "Cookie": f"bw_sid={sid}"}
    assert ctl.respond("POST", "/act/do", base, b"a=pa")[0] == 403  # no token
    assert ctl.respond("POST", "/act/do", base, b"a=pa&csrf=" + b"0" * 40)[0] == 403
    no_cookie = {"Tailscale-User-Login": OWNER}
    assert ctl.respond("POST", "/act/do", no_cookie, f"a=pa&csrf={token}".encode())[0] == 403
    other = _session(ctl)  # another session's token does not fit this cookie
    assert ctl.respond("POST", "/act/do", base, f"a=pa&csrf={other[1]}".encode())[0] == 403
    cross = {**base, "Sec-Fetch-Site": "cross-site"}
    assert ctl.respond("POST", "/act/do", cross, f"a=pa&csrf={token}".encode())[0] == 403
    evil = {**base, "Origin": "https://evil.example", "Host": "bigwins.example.ts.net"}
    assert ctl.respond("POST", "/act/do", evil, f"a=pa&csrf={token}".encode())[0] == 403
    assert j.safety_level() is SafetyLevel.NORMAL
    good = {**base, "Origin": "https://bigwins.example.ts.net", "Host": "bigwins.example.ts.net"}
    assert ctl.respond("POST", "/act/do", good, f"a=pa&csrf={token}".encode())[0] == 200
    assert j.safety_level() is SafetyLevel.PAUSED
    assert not same_origin({"Origin": "null"})


def test_BF_D39_get_to_action_urls_changes_nothing() -> None:
    j, _, ctl, bid, _ = _setup()
    code = totp(SEED, T_APPROVE)
    for path in (f"/act/do?a=ok&b={bid}&n=all&code={code}", "/act/do?a=ki&confirm=yes",
                 "/act/confirm?a=pa", f"/act/confirm?a=ok&b={bid}&n=all", "/act/alerts",
                 "/act/push/subscribe", "/act"):  # fmt: skip
        ctl.respond("GET", path, {"Tailscale-User-Login": OWNER})
    assert j.approvals(bid) == [] and j.safety_level() is SafetyLevel.NORMAL
    assert inbox_rows(j) == []


def test_BF_D39_confirm_screen_shows_count_and_total() -> None:
    _, _, ctl, bid, _ = _setup()
    _, _, body = ctl.respond("GET", f"/act/confirm?a=ok&b={bid}&n=all",
                             {"Tailscale-User-Login": OWNER})  # fmt: skip
    page = body.decode()
    assert f"Approve all 4 orders of {bid}" in page and "total ≈ A$" in page
    assert 'name="code"' in page and "Approve all 4 orders" in page


def test_BF_D39_unknown_or_refused_batch_and_veto_of_a_sell() -> None:
    j, _, ctl, bid, _ = _setup()
    code = totp(SEED, T_APPROVE)
    assert "unknown batch" in _post(ctl, {"a": "ok", "b": "NOPE", "n": "all", "code": code})[1]
    sell = next(it.seq for it, _ in j.intents_of(bid) if it.side.value == "SELL")
    assert (
        "cannot be vetoed" in _post(ctl, {"a": "veto", "b": bid, "n": str(sell), "code": code})[1]
    )
    assert "refused batch" in _post(ctl, {"a": "rf", "b": bid, "code": code})[1]
    later = T_APPROVE + timedelta(minutes=1)
    ctl.clock_box["t"] = later  # type: ignore[attr-defined]
    _, page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": totp(SEED, later)})
    assert "already refused" in page


def test_BF_D39_queue_runs_in_the_main_loop(tmp_path: Path) -> None:
    import threading

    from sqlalchemy import create_engine

    j = Journal(create_engine(f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}"))
    bot = ApprovalBot(j, FakeTransport(), TotpVerifier(SecretValue(SEED)), frozenset({CHAT}),
                      allowed_logins=frozenset({OWNER}))  # fmt: skip
    ctl = Control(j, bot, frozenset({OWNER}), book=BOOK, clock=lambda: T_APPROVE)
    out: dict[str, Any] = {}
    th = threading.Thread(target=lambda: out.update(r=_post(ctl, {"a": "pa"})))
    th.start()
    for _ in range(200):
        if ctl.process():
            break
        ctl.wait(0.01)
    th.join(5)
    assert "PAUSED" in out["r"][1] and j.safety_level() is SafetyLevel.PAUSED


def test_BF_D42_server_job_needs_code_and_confirm_and_is_whitelisted() -> None:
    j, _, ctl, _, _ = _setup()
    assert "enter your 6-digit code" in _post(ctl, {"a": "srv:restart"})[1]
    assert "unknown server action" in _post(ctl, {"a": "srv:rm -rf", "code": "123456"})[1]
    ctl.market_open = lambda now: True
    _, page = _post(ctl, {"a": "srv:restart", "code": totp(SEED, T_APPROVE)})
    assert "Do it anyway" in page and "queued" not in page
    _, page = _post(ctl, {"a": "srv:restart", "code": totp(SEED, T_APPROVE), "force": "1"})
    assert "queued" in page
    from trader.app_store import server_job_rows

    rows = server_job_rows(j)
    assert [(r["action"], r["force"], r["status"]) for r in rows] == [("restart", 1, "PENDING")]
    with pytest.raises(ValueError, match="not a server action"):
        add_server_job(j, "shell", False, OWNER, T_APPROVE)


def test_BF_D40_push_subscription_saved_only_for_push_services() -> None:
    j, _, ctl, _, pages = _setup()
    sid, token = _session(ctl)
    hdrs = {"Tailscale-User-Login": OWNER, "Cookie": f"bw_sid={sid}", "X-CSRF-Token": token,
            "Content-Type": "application/json", "Sec-Fetch-Site": "same-origin"}  # fmt: skip
    bad = json.dumps({"endpoint": "https://intranet.local/x", "keys": {"p256dh": "a", "auth": "b"}})
    assert ctl.respond("POST", "/act/push/subscribe", hdrs, bad.encode())[0] == 400
    good = json.dumps({"endpoint": "https://fcm.googleapis.com/fcm/send/abc",
                       "keys": {"p256dh": "a", "auth": "b"}})  # fmt: skip
    assert ctl.respond("POST", "/act/push/subscribe", hdrs, good.encode())[0] == 200
    from trader.app_store import push_sub_rows

    assert [r["login"] for r in push_sub_rows(j)] == [OWNER]
    assert pages and "Alerts are on" in pages[-1]
