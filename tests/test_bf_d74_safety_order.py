"""BF-D74: risk-reducing commands (pause, stop) never lower a stricter safety level.

Only /resume with a valid one-time code lowers the level (owner-approved fix, 23 Nov 2026)."""

from __future__ import annotations

from datetime import timedelta

from tests.test_bf_buttons import _setup
from tests.test_bf_execution import CHAT, SEED, T_APPROVE
from trader.approval import Incoming, totp
from trader.risk import SafetyLevel


def _cmd(bot, text, at=T_APPROVE):  # type: ignore[no-untyped-def]
    return bot.handle(Incoming(CHAT, text, at))


def test_BF_D74_kill_then_pause_stays_killed() -> None:
    j, bot, *_ = _setup()
    _cmd(bot, "/kill")
    reply = _cmd(bot, "/pause", T_APPROVE + timedelta(seconds=5))
    assert j.safety_level() is SafetyLevel.KILLED
    assert reply.startswith("already KILLED")


def test_BF_D74_kill_then_stop_stays_killed() -> None:
    j, bot, *_ = _setup()
    _cmd(bot, "/kill")
    reply = _cmd(bot, "/stop", T_APPROVE + timedelta(seconds=5))
    assert j.safety_level() is SafetyLevel.KILLED
    assert "stays KILLED" in reply


def test_BF_D74_pause_then_kill_becomes_killed() -> None:
    j, bot, *_ = _setup()
    _cmd(bot, "/pause")
    assert j.safety_level() is SafetyLevel.PAUSED
    _cmd(bot, "/kill", T_APPROVE + timedelta(seconds=5))
    assert j.safety_level() is SafetyLevel.KILLED


def test_BF_D74_resume_with_code_from_killed_returns_to_normal() -> None:
    j, bot, *_ = _setup()
    _cmd(bot, "/kill")
    at = T_APPROVE + timedelta(seconds=40)
    assert _cmd(bot, "/resume 000000", at).startswith("refused")
    assert j.safety_level() is SafetyLevel.KILLED
    assert _cmd(bot, f"/resume {totp(SEED, at)}", at) == "re-armed: NORMAL"
    assert j.safety_level() is SafetyLevel.NORMAL


def test_BF_D74_pause_from_normal_still_pauses() -> None:
    j, bot, *_ = _setup()
    assert _cmd(bot, "/pause").startswith("PAUSED")
    assert j.safety_level() is SafetyLevel.PAUSED
