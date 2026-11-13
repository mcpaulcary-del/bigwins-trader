"""CLI skeleton (§3): every subcommand registered; unimplemented ones say so."""

from __future__ import annotations

import io
import subprocess
import sys

import pytest

from tests.conftest import REPO
from trader import cli

SPEC_COMMANDS = {
    "run", "backtest", "validate", "replay", "status", "plan", "veto", "kill", "resume",
    "fallback", "reconcile", "init", "cashflow", "corp-action", "secret", "migrate",
    "validate-config", "report", "mode",
}  # fmt: skip

ARGS = {
    "run": ["--user", "a"],
    "backtest": [],
    "validate": [],
    "replay": ["2026-11-13", "--user", "a"],
    "status": ["--user", "a"],
    "plan": ["--user", "a"],
    "veto": ["BHP", "--user", "a"],
    "kill": ["--user", "a"],
    "resume": ["--reason", "checked", "--user", "a"],
    "fallback": ["--confirm", "--user", "a"],
    "reconcile": ["--accept", "--note", "n", "--user", "a"],
    "cashflow": ["--expect", "+5000", "--user", "a"],
    "corp-action": ["apply", "BHP", "--user", "a"],
    "secret": ["set", "telegram_bot_token", "--user", "a"],
    "report": [],
    "mode": ["full", "--confirm", "--user", "a"],
}


def test_all_spec_subcommands_registered() -> None:
    parser = cli.build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    assert set(sub.choices) == SPEC_COMMANDS  # type: ignore[arg-type]
    assert set(cli.ALL_COMMANDS) == SPEC_COMMANDS


@pytest.mark.parametrize("command", sorted(ARGS))
def test_unimplemented_commands_exit_clearly(command: str) -> None:
    err = io.StringIO()
    rc = cli.main([command, *ARGS[command]], out=io.StringIO(), err=err)
    assert rc == cli.EXIT_NOT_IMPLEMENTED
    assert f"trader {command}: not implemented in M0" in err.getvalue()


def test_mode_full_requires_confirm() -> None:
    with pytest.raises(SystemExit):
        cli.main(["mode", "full", "--user", "a"], out=io.StringIO(), err=io.StringIO())


def test_validate_config_common_only() -> None:
    out = io.StringIO()
    rc = cli.main(
        ["validate-config", "--config-dir", str(REPO / "config")], out=out, err=io.StringIO()
    )
    assert rc == cli.EXIT_OK
    assert out.getvalue().startswith("OK ")


def test_validate_config_invalid_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "common.yaml").write_text("version: 2\n")
    err = io.StringIO()
    rc = cli.main(["validate-config", "--config-dir", str(tmp_path)], out=io.StringIO(), err=err)
    assert rc == cli.EXIT_CONFIG_INVALID
    assert "INVALID" in err.getvalue()


def test_console_script_entry_point() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "trader.cli", "kill", "--user", "a"],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=False,
    )
    assert r.returncode == cli.EXIT_NOT_IMPLEMENTED
    assert "not implemented in M0" in r.stderr
