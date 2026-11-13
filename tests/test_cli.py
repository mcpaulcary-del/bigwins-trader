"""CLI (spec v2.10 §3): every command registered; unimplemented ones say so."""

from __future__ import annotations

import io
import subprocess
import sys

import pytest

from tests.conftest import REPO
from trader import cli

SPEC_COMMANDS = {
    "run", "backtest", "replay", "status", "plan", "veto", "kill", "resume", "mode", "stage",
    "reconcile", "init", "cashflow", "corp-action", "distribution", "qc", "fetch", "recover",
    "drill", "canary", "golive", "expectations", "secret", "migrate", "validate-config",
    "report", "hypothesis", "holdout",
    "import",  # builder-named import sub-command for hand-entered reference data (§3)
}  # fmt: skip

ARGS = {
    "run": ["--user", "a"],
    "backtest": [],
    "replay": ["2026-11-13", "--user", "a"],
    "status": ["--user", "a"],
    "plan": ["--user", "a"],
    "veto": ["VAS", "--user", "a"],
    "kill": ["--user", "a"],
    "resume": ["--clear", "kill", "--reason", "checked", "--user", "a"],
    "mode": ["static", "--confirm", "--user", "a"],
    "stage": ["2", "--confirm", "--user", "a"],
    "reconcile": ["--accept", "--note", "n", "--user", "a"],
    "cashflow": ["--expect", "-500", "--user", "a"],
    "corp-action": ["apply", "VAS", "--user", "a"],
    "recover": ["--from-flex", "--user", "a"],
    "drill": ["--sleeve", "VAS", "--to", "OFF", "--user", "a"],
    "canary": ["--confirm", "--user", "a"],
    "golive": ["--user", "a"],
    "expectations": ["accept", "--user", "a"],
    "secret": ["set", "telegram_bot_token", "--user", "a"],
    "report": [],
    "hypothesis": ["register"],
    "holdout": ["open", "--family", "L1", "--confirm"],
}


def test_all_spec_subcommands_registered() -> None:
    parser = cli.build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    assert set(sub.choices) == SPEC_COMMANDS  # type: ignore[arg-type]
    assert set(cli.ALL_COMMANDS) == SPEC_COMMANDS


def test_withdrawn_v1_commands_are_gone() -> None:
    parser = cli.build_parser()
    sub = next(a for a in parser._actions if a.dest == "command")
    for gone in ("fallback", "validate"):
        assert gone not in sub.choices  # type: ignore[operator]


@pytest.mark.parametrize("command", sorted(ARGS))
def test_unimplemented_commands_exit_clearly(command: str) -> None:
    err = io.StringIO()
    rc = cli.main([command, *ARGS[command]], out=io.StringIO(), err=err)
    assert rc == cli.EXIT_NOT_IMPLEMENTED
    assert f"trader {command}: not implemented yet" in err.getvalue()


@pytest.mark.parametrize(
    "argv",
    [
        ["mode", "static", "--user", "a"],
        ["resume", "--reason", "x", "--user", "a"],
        ["resume", "--clear", "everything", "--reason", "x", "--user", "a"],
        ["holdout", "open", "--family", "L2", "--confirm"],
        ["migrate"],
    ],
)
def test_required_confirmations_and_choices(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(argv, out=io.StringIO(), err=io.StringIO())


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
    assert "not implemented yet" in r.stderr
