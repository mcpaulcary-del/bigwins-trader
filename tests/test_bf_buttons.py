"""BF-D38: Telegram buttons are shortcuts for the typed commands, with the same safety:
allow-listed chats only, the same approval deadline, the same batch identity and the
same one-time code for anything that adds risk or re-arms; Kill / Stop need a second tap."""

from __future__ import annotations

import io
import json
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qs

from tests.test_bf_execution import BOOK, CHAT, SEED, T_APPROVE, X, _batch, _ctx, _sim
from trader.approval import (
    CB_MAX,
    OPEN_FOR_APPROVAL,
    ApprovalBot,
    FakeTransport,
    Incoming,
    TelegramTransport,
    TotpVerifier,
    approved_seqs,
    batch_markup,
    broadcast_batch,
    menu_markup,
    totp,
)
from trader.constants import ASX_TZ
from trader.execution import Executor
from trader.journal import Journal
from trader.orders import OrderBatch
from trader.risk import SafetyLevel
from trader.secrets import SecretValue


def _setup(
    n_buys: int = 3, mode: str = "per_order"
) -> tuple[Journal, ApprovalBot, FakeTransport, OrderBatch, list[int]]:
    j, sim = Journal.sqlite(), _sim()
    b = _batch(n_buys)
    Executor(j, sim, BOOK).plan(b, mode, X, _ctx(sim))
    tr = FakeTransport()
    kills: list[int] = []

    def kill() -> int:
        kills.append(1)
        return 0

    bot = ApprovalBot(j, tr, TotpVerifier(SecretValue(SEED)), frozenset({CHAT}), on_kill=kill)
    return j, bot, tr, b, kills


def _tap(
    bot: ApprovalBot,
    data: str,
    at: datetime = T_APPROVE,
    chat: int = CHAT,
    user: int | None = CHAT,
    mid: int | None = 7,
) -> str:
    return bot.handle(
        Incoming(chat, "", at, callback_id=f"cb{at.timestamp()}", data=data, user_id=user,
                 message_id=mid, message_text="Batch message")
    )  # fmt: skip


def _code(bot: ApprovalBot, at: datetime, code: str | None = None) -> str:
    return bot.handle(Incoming(CHAT, code or totp(SEED, at), at))


def _approvals(j: Journal, batch_id: str) -> list[tuple[Any, str, str]]:
    return [(a["seq"], a["action"], a["actor"]) for a in j.approvals(batch_id)]


def test_BF_D38_callback_from_wrong_chat_or_user_is_ignored() -> None:
    j, bot, tr, b, _ = _setup()
    assert _tap(bot, f"bw:ok:{b.batch_id}:all", chat=999, user=999) == "ignored"
    assert _tap(bot, "bw:pa", chat=999, user=999) == "ignored"
    # the owner's private chat, tapped by someone else (a forwarded message): ignored
    assert _tap(bot, "bw:pa", chat=CHAT, user=555) == "ignored"
    assert j.safety_level() is SafetyLevel.NORMAL and not j.approvals(b.batch_id)
    assert tr.outbox == []  # strangers get no message ...
    assert [t for _, t in tr.answers] == ["", "", ""]  # ... only the spinner is stopped
    # and a stranger's tap leaves nothing waiting for the owner's code
    assert "No button is waiting" in _code(bot, T_APPROVE + timedelta(seconds=10))


def test_BF_D38_approve_all_button_then_code_equals_typed_ok_all() -> None:
    j, bot, tr, b, _ = _setup()
    reply = _tap(bot, f"bw:ok:{b.batch_id}:all")
    assert (
        reply
        == f"Send your 6-digit code to approve all 4 orders of {b.batch_id} (within 3 minutes)."
    )
    assert tr.markups[-1][2]["force_reply"] is True  # the phone opens the keyboard
    assert not j.approvals(b.batch_id)  # nothing approved by the tap alone
    t = T_APPROVE + timedelta(seconds=40)
    assert _code(bot, t) == f"approved all 4 orders of {b.batch_id}"
    # the same rows as the typed command on a twin journal
    j2, bot2, _, b2, _ = _setup()
    assert bot2.handle(Incoming(CHAT, f"/ok {b2.batch_id} all {totp(SEED, t)}", t)).startswith(
        "approved all"
    )
    assert (
        _approvals(j, b.batch_id)
        == _approvals(j2, b2.batch_id)
        == [(None, "OK", f"telegram:{CHAT}")]
    )
    assert approved_seqs(j, b.batch_id) == approved_seqs(j2, b2.batch_id) == {1, 2, 3, 4}
    # the batch message loses its buttons and shows the outcome
    assert tr.edits == [(CHAT, 7, f"Batch message\n\nDONE: approved all 4 orders of {b.batch_id}")]
    # the tap is used up: another code completes nothing
    assert "No button is waiting" in _code(bot, t + timedelta(seconds=31))


def test_BF_D38_per_order_button_approves_that_order_only() -> None:
    j, bot, _, b, _ = _setup()
    assert "approve order 3 (BUY" in _tap(bot, f"bw:ok:{b.batch_id}:3")
    assert _code(bot, T_APPROVE + timedelta(seconds=5)).startswith("approved 3: BUY")
    assert approved_seqs(j, b.batch_id) == {3}
    # an order already approved, or not in the batch, gets no prompt
    assert "not waiting for approval" in _tap(
        bot, f"bw:ok:{b.batch_id}:3", T_APPROVE + timedelta(seconds=40)
    )
    assert "not waiting for approval" in _tap(
        bot, f"bw:ok:{b.batch_id}:9", T_APPROVE + timedelta(seconds=41)
    )


def test_BF_D38_wrong_reused_or_expired_code_is_refused() -> None:
    j, bot, _, b, _ = _setup()
    # wrong code: refused by the typed handler; the tap is used up
    _tap(bot, f"bw:ok:{b.batch_id}:all")
    assert (
        _code(bot, T_APPROVE + timedelta(seconds=5), "000000") == "refused: invalid or reused code"
    )
    assert "No button is waiting" in _code(bot, T_APPROVE + timedelta(seconds=6))
    # reused code: a code already used for a typed command is refused after a tap too
    t = T_APPROVE + timedelta(seconds=90)
    used = totp(SEED, t)
    assert bot.handle(Incoming(CHAT, f"/ok {b.batch_id} 2 {used}", t)).startswith("approved 2")
    _tap(bot, f"bw:ok:{b.batch_id}:all", t + timedelta(seconds=1))
    assert _code(bot, t + timedelta(seconds=2), used) == "refused: invalid or reused code"
    # expired: a code more than 3 minutes after the tap
    t2 = T_APPROVE + timedelta(minutes=10)
    _tap(bot, f"bw:ok:{b.batch_id}:all", t2)
    assert "No button is waiting" in _code(bot, t2 + timedelta(seconds=181))
    assert approved_seqs(j, b.batch_id) == {2}  # only the typed approval


def test_BF_D38_late_approval_after_cut_off_is_refused() -> None:
    j, bot, tr, b, _ = _setup()
    late = datetime(2026, 12, 1, 15, 21, tzinfo=ASX_TZ)
    reply = _tap(bot, f"bw:ok:{b.batch_id}:all", late)
    assert "past the approval deadline" in reply and not tr.markups  # no code prompt
    # tapped before the cut-off, code after it: refused by the typed handler's deadline
    _tap(bot, f"bw:ok:{b.batch_id}:all", datetime(2026, 12, 1, 15, 19, 30, tzinfo=ASX_TZ))
    assert "deadline" in _code(bot, datetime(2026, 12, 1, 15, 20, 30, tzinfo=ASX_TZ))
    assert not j.approvals(b.batch_id) and not tr.edits


def test_BF_D38_stale_unknown_or_refused_batch_is_refused() -> None:
    j, bot, tr, b, _ = _setup()
    assert (
        _tap(bot, "bw:ok:EMG2_20_PAPER-2026-10-30-R:all")
        == "unknown batch EMG2_20_PAPER-2026-10-30-R"
    )
    assert _tap(bot, "bw:ok") == "unknown button" and _tap(bot, "xx:pa") == "unknown button"
    # refuse button: needs the code, like /refuse <batch> <code>
    assert "refuse batch" in _tap(bot, f"bw:rf:{b.batch_id}")
    assert _code(bot, T_APPROVE + timedelta(seconds=3)).startswith("refused batch")
    assert tr.edits[-1][2].endswith("nothing will be sent")
    assert "already refused" in _tap(
        bot, f"bw:ok:{b.batch_id}:all", T_APPROVE + timedelta(seconds=40)
    )
    assert approved_seqs(j, b.batch_id) == set()


def test_BF_D38_kill_and_stop_need_a_second_tap() -> None:
    j, bot, tr, _, kills = _setup()
    assert _tap(bot, "bw:ki").startswith("Tap again to confirm KILL")
    assert j.safety_level() is SafetyLevel.NORMAL and not kills
    confirm = tr.markups[-1][2]["inline_keyboard"][0][0]
    assert confirm["callback_data"] == "bw:ki!"
    # a confirm tap with no first tap, or too late, does nothing
    assert "Not confirmed" in _tap(bot, "bw:so!", T_APPROVE + timedelta(seconds=5))
    _tap(bot, "bw:ki", T_APPROVE + timedelta(seconds=10))
    assert "Not confirmed" in _tap(bot, "bw:ki!", T_APPROVE + timedelta(seconds=71))
    assert j.safety_level() is SafetyLevel.NORMAL and not kills
    _tap(bot, "bw:ki", T_APPROVE + timedelta(seconds=100))
    assert _tap(bot, "bw:ki!", T_APPROVE + timedelta(seconds=103)).startswith("KILLED")
    assert j.safety_level() is SafetyLevel.KILLED and kills == [1]
    # stop: the same two taps, recorded as the typed /stop
    _tap(bot, "bw:so", T_APPROVE + timedelta(seconds=200))
    assert _tap(bot, "bw:so!", T_APPROVE + timedelta(seconds=201)).startswith("STOP recorded")
    assert j.job_records("l11:stop:")
    # cancel clears a waiting confirmation
    _tap(bot, "bw:ki", T_APPROVE + timedelta(seconds=300))
    assert _tap(bot, "bw:cx", T_APPROVE + timedelta(seconds=301)).startswith("Cancelled")
    assert "Not confirmed" in _tap(bot, "bw:ki!", T_APPROVE + timedelta(seconds=302))


def test_BF_D38_pause_is_one_tap_resume_and_continue_need_the_code() -> None:
    j, bot, _, _, _ = _setup()
    assert _tap(bot, "bw:pa").startswith("PAUSED")
    assert j.safety_level() is SafetyLevel.PAUSED
    assert _tap(bot, "bw:st", T_APPROVE + timedelta(seconds=1)) == "safety PAUSED"
    assert "re-arm" in _tap(bot, "bw:re", T_APPROVE + timedelta(seconds=2))
    assert j.safety_level() is SafetyLevel.PAUSED  # the tap alone re-arms nothing
    assert _code(bot, T_APPROVE + timedelta(seconds=20), "123456").startswith("refused: /resume")
    assert j.safety_level() is SafetyLevel.PAUSED
    _tap(bot, "bw:re", T_APPROVE + timedelta(seconds=40))
    assert _code(bot, T_APPROVE + timedelta(seconds=45)) == "re-armed: NORMAL"
    _tap(bot, "bw:co", T_APPROVE + timedelta(seconds=70))
    assert _code(bot, T_APPROVE + timedelta(seconds=75)).startswith("confirmation recorded")
    assert j.job_records("l11:confirm:")


def test_BF_D38_typed_commands_unchanged_and_menu() -> None:
    j, bot, tr, b, _ = _setup()
    assert bot.handle(Incoming(CHAT, "/status", T_APPROVE)) == "safety NORMAL"
    assert bot.handle(Incoming(CHAT, "/foo", T_APPROVE)) == "unknown command /foo"
    assert "No button is waiting" in _code(bot, T_APPROVE)  # a bare code with no tap
    assert bot.handle(Incoming(999, "/menu", T_APPROVE)) == "ignored"
    bot.handle(Incoming(CHAT, "/menu", T_APPROVE))
    assert tr.markups[-1][2] == menu_markup()
    datas = [k["callback_data"] for row in menu_markup()["inline_keyboard"] for k in row]
    assert datas == ["bw:st", "bw:pa", "bw:ki", "bw:so", "bw:re", "bw:co"]


def test_BF_D38_batch_buttons_fit_telegram_limits() -> None:
    j, _, _, b, _ = _setup(n_buys=17)  # 18 orders: the EMG2-18 start
    mk = batch_markup(j, b.batch_id)
    assert mk is not None
    rows = mk["inline_keyboard"]
    assert [k["text"] for k in rows[0]] == ["✅ Approve all", "❌ Refuse batch"]
    per = [k["callback_data"] for r in rows[1:-1] for k in r]
    waiting = [it.seq for it, st in j.intents_of(b.batch_id) if st in OPEN_FOR_APPROVAL]
    assert len(waiting) > 6 and per == [f"bw:ok:{b.batch_id}:{n}" for n in waiting]
    assert all(len(r) <= 6 for r in rows)
    assert [k["text"] for k in rows[-1]] == ["📊 Status", "⏸ Pause"]
    assert all(len(k["callback_data"].encode()) <= CB_MAX for r in rows for k in r)
    # a batch approved as a whole, and an auto batch (nothing to approve)
    j2, _, _, b2, _ = _setup(mode="batch")
    mk2 = batch_markup(j2, b2.batch_id)
    assert (
        mk2 is not None and mk2["inline_keyboard"][0][0]["callback_data"] == f"bw:ap:{b2.batch_id}"
    )
    j3, _, _, b3, _ = _setup(mode="auto")
    assert batch_markup(j3, b3.batch_id) is None
    # the message carries the buttons; a plain transport gets the plain text
    tr = FakeTransport()
    broadcast_batch(tr, [CHAT], "req", j, b.batch_id)
    assert tr.markups[0][2] == mk and "tap a button" in tr.outbox[0][1]

    class Plain:
        sent: list[str] = []  # noqa: RUF012

        def send(self, chat_id: int, text: str) -> None:
            self.sent.append(text)

        def poll(self) -> list[Incoming]:
            return []

    pl = Plain()
    broadcast_batch(pl, [CHAT], "req", j, b.batch_id)
    assert pl.sent == ["req"]


def test_BF_D38_batch_mode_approve_button() -> None:
    j, bot, _, b, _ = _setup(mode="batch")
    assert "per-order" not in _tap(bot, f"bw:ap:{b.batch_id}")
    assert _code(bot, T_APPROVE + timedelta(seconds=3)) == f"approved batch {b.batch_id}"
    assert approved_seqs(j, b.batch_id) == {1, 2, 3, 4}


class _Resp(io.BytesIO):
    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *a: object) -> None:
        return None


def test_BF_D38_telegram_transport_buttons_and_callback_queries() -> None:
    calls: list[tuple[str, dict[str, list[str]]]] = []
    updates = [
        {"update_id": 5, "message": {"date": 1764558000, "chat": {"id": CHAT}, "text": "/status"}},
        {"update_id": 6, "callback_query": {
            "id": "q1", "from": {"id": CHAT}, "data": "bw:pa",
            "message": {"message_id": 11, "chat": {"id": CHAT}, "text": "Batch ..."}}},
    ]  # fmt: skip

    def opener(req: Any, timeout: int) -> _Resp:
        method = req.full_url.rsplit("/", 1)[1]
        calls.append((method, parse_qs(req.data.decode())))
        result: Any = {"message_id": 12} if method == "sendMessage" else True
        if method == "getUpdates":
            result = updates
        return _Resp(json.dumps({"ok": True, "result": result}).encode())

    t = TelegramTransport(SecretValue("123:abc"), opener=opener)
    got = t.poll()
    assert [m.text for m in got] == ["/status", ""]
    cb = got[1]
    assert (cb.callback_id, cb.data, cb.user_id, cb.message_id) == ("q1", "bw:pa", CHAT, 11)
    assert t.send_markup(CHAT, "hi", menu_markup()) == 12
    assert json.loads(calls[-1][1]["reply_markup"][0]) == menu_markup()
    t.answer_callback("q1", "ok")
    t.edit_text(CHAT, 11, "done")
    assert [c[0] for c in calls[-2:]] == ["answerCallbackQuery", "editMessageText"]
    assert "reply_markup" not in calls[-1][1]  # editing without markup removes the buttons


def test_BF_D38_app_approval_request_carries_the_buttons() -> None:
    from tests.test_bf_app import D0, _app

    app, _, tr = _app(D0)
    app.run_day(D0)
    canary = f"EMG2_18_PAPER-{D0}-C"
    sent = [mk for _, text, mk in tr.markups if f"Batch {canary}" in text]
    assert sent and sent[0] == batch_markup(app.j, canary)
    assert sent[0]["inline_keyboard"][0][0]["callback_data"] == f"bw:ok:{canary}:all"
