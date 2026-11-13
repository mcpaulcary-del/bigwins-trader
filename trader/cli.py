"""``trader`` command line (spec §3).

All §3 subcommands are registered. In M0 only ``validate-config`` and
``migrate`` are implemented; ``init`` runs its config hard checks (OPS-10,
OPS-12) and then stops. Every other command exits with a clear
"not implemented in M0" message and exit code ``EXIT_NOT_IMPLEMENTED``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, TextIO

from trader.config import (
    ApprovalPinMismatchError,
    ConfigError,
    default_sizing_nav,
    deployed_git_sha,
    enforce_ops12,
    load_config,
    ops12_check,
    ops12_mode,
    parse_common,
    sha256_bytes,
)
from trader.constants import COMMON_CONFIG_NAME, CONFIG_DIR_DEFAULT

EXIT_OK: Final = 0
EXIT_CONFIG_INVALID: Final = 2
EXIT_PIN_MISMATCH: Final = 3
EXIT_NOT_IMPLEMENTED: Final = 69  # EX_UNAVAILABLE

# Subcommand -> milestone that implements it (spec §20).
PLANNED: Final[dict[str, str]] = {
    "run": "M5",
    "backtest": "M3",
    "validate": "M3",
    "replay": "M5",
    "status": "M5",
    "plan": "M5",
    "veto": "M5",
    "kill": "M5",
    "resume": "M5",
    "fallback": "M5",
    "reconcile": "M5",
    "init": "M5",
    "cashflow": "M5",
    "corp-action": "M4",
    "secret": "M5",
    "report": "M6",
    "mode": "M2",
}
ALL_COMMANDS: Final = (
    "run",
    "backtest",
    "validate",
    "replay",
    "status",
    "plan",
    "veto",
    "kill",
    "resume",
    "fallback",
    "reconcile",
    "init",
    "cashflow",
    "corp-action",
    "secret",
    "migrate",
    "validate-config",
    "report",
    "mode",  # §9.1 amendment: `trader mode full --confirm`
)


def _decimal(text: str) -> Decimal:
    try:
        d = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"not a decimal amount: {text!r}") from exc
    if not d.is_finite() or d <= 0:
        raise argparse.ArgumentTypeError("amount must be a positive number")
    return d


def _user_opts(p: argparse.ArgumentParser, *, required: bool = True) -> None:
    p.add_argument("--user", required=required, help="user tag, e.g. 'a' (config/<user>.yaml)")
    p.add_argument("--config-dir", type=Path, default=CONFIG_DIR_DEFAULT)


def build_parser() -> argparse.ArgumentParser:  # noqa: PLR0915 - one flat registry
    parser = argparse.ArgumentParser(prog="trader", description="Automated ASX trader (spec v1.2)")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def add(name: str, help_: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, help=help_, description=help_)

    _user_opts(add("run", "Start the live job runner (scheduler)"))
    _user_opts(add("backtest", "Run the backtester"), required=False)
    _user_opts(add("validate", "Run the validation protocol / Gate 1 report"), required=False)
    p = add("replay", "Replay a decision date from recorded snapshots")
    p.add_argument("date", type=date.fromisoformat)
    _user_opts(p)
    _user_opts(add("status", "Show run state, flags and holdings"))
    _user_opts(add("plan", "Show the plan for the next execution date"))
    p = add("veto", "Veto buys (or a sell, with SELL CONFIRM) for the next execution date")
    p.add_argument("symbol", help="symbol or ALL")
    p.add_argument("side", nargs="?", choices=["SELL"])
    p.add_argument("confirm", nargs="?", choices=["CONFIRM"])
    _user_opts(p)
    _user_opts(add("kill", "Set KILLED: cancel all open orders, send nothing new"))
    p = add("resume", "Clear KILLED (requires a typed reason)")
    p.add_argument("--reason", required=True)
    _user_opts(p)
    p = add("fallback", "Enter fallback mode (hold VAS)")
    p.add_argument("--confirm", action="store_true", required=True)
    _user_opts(p)
    p = add("reconcile", "Run reconciliation; --accept --note clears HALTED")
    p.add_argument("--accept", action="store_true")
    p.add_argument("--note")
    _user_opts(p)
    p = add("init", "Onboarding: import IBKR positions; config hard checks (OPS-12)")
    p.add_argument("--sizing-nav", type=_decimal, help="sizing NAV in AUD for the OPS-12 check")
    _user_opts(p)
    p = add("cashflow", "Pre-announce a deposit or withdrawal")
    p.add_argument("--expect", type=str, required=True, help="signed AUD amount, e.g. +5000")
    _user_opts(p)
    p = add("corp-action", "Corporate actions")
    ca = p.add_subparsers(dest="action", required=True)
    pa = ca.add_parser("apply", help="Apply a non-cash corporate action and unfreeze the symbol")
    pa.add_argument("symbol")
    _user_opts(pa)
    p = add("secret", "Manage this user's Docker secrets")
    sp = p.add_subparsers(dest="action", required=True)
    ps = sp.add_parser("set", help="Set a secret (value read from stdin, never from argv)")
    ps.add_argument("name")
    _user_opts(ps)
    p = add("migrate", "Apply Alembic migrations (forward-only) to this user's database")
    p.add_argument("--app-role", help="DB role granted app privileges (default trader_app)")
    p = add("validate-config", "Validate common.yaml (and <user>.yaml with --user)")
    _user_opts(p, required=False)
    p.add_argument("--sizing-nav", type=_decimal, help="sizing NAV in AUD for the OPS-12 check")
    p.add_argument(
        "--print-hashes",
        action="store_true",
        help="print the deployed git SHA and common.yaml hash to pin; skips the pin check",
    )
    _user_opts(add("report", "Generate reports"), required=False)
    p = add("mode", "Switch account mode (spec §9.1 amendment)")
    p.add_argument("target", choices=["full"], help="leave small-account mode")
    p.add_argument("--confirm", action="store_true", required=True)
    _user_opts(p)
    return parser


def _not_implemented(command: str, out: TextIO) -> int:
    print(
        f"trader {command}: not implemented in M0 (planned for {PLANNED[command]}).",
        file=out,
    )
    return EXIT_NOT_IMPLEMENTED


def cmd_validate_config(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    config_dir: Path = args.config_dir
    try:
        if args.user is None:
            data = (config_dir / COMMON_CONFIG_NAME).read_bytes()
            parse_common(data, str(config_dir / COMMON_CONFIG_NAME))
            print(f"OK {config_dir / COMMON_CONFIG_NAME} sha256={sha256_bytes(data)}", file=out)
            return EXIT_OK
        sha = deployed_git_sha()
        loaded = load_config(
            config_dir, args.user, deployed_sha=sha, check_pins=not args.print_hashes
        )
        if args.print_hashes:
            print(f"approved_git_sha: {sha}", file=out)
            print(f"approved_common_hash: {loaded.common_hash}", file=out)
        # validate-config is the check run on any config change: OPS-12 is hard here
        # (warning only in small-account mode, see docs/DECISIONS.md).
        nav = args.sizing_nav if args.sizing_nav is not None else default_sizing_nav(loaded.user)
        res = ops12_check(loaded.common, nav)
        mode = ops12_mode(
            is_init=False,
            config_hash=loaded.config_hash,
            known_hashes=(),
            small_account_enabled=loaded.user.small_account.enabled,
        )
        warning = enforce_ops12(res, mode)
        print(warning or res.message, file=out)
        print(f"OK user={loaded.user.user} config_hash={loaded.config_hash}", file=out)
        return EXIT_OK
    except ApprovalPinMismatchError as exc:
        print(f"REFUSED: {exc}", file=err)
        return EXIT_PIN_MISMATCH
    except (ConfigError, OSError) as exc:
        print(f"INVALID: {exc}", file=err)
        return EXIT_CONFIG_INVALID


def cmd_init(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    try:
        loaded = load_config(args.config_dir, args.user, deployed_sha=deployed_git_sha())
        nav = args.sizing_nav if args.sizing_nav is not None else default_sizing_nav(loaded.user)
        res = ops12_check(loaded.common, nav)
        mode = ops12_mode(
            is_init=True,
            config_hash=loaded.config_hash,
            known_hashes=(),
            small_account_enabled=loaded.user.small_account.enabled,
        )
        warning = enforce_ops12(res, mode)  # OPS-12: hard at trader init (full mode)
        print(warning or res.message, file=out)
    except ApprovalPinMismatchError as exc:
        print(f"REFUSED: {exc}", file=err)
        return EXIT_PIN_MISMATCH
    except (ConfigError, OSError) as exc:
        print(f"INVALID: {exc}", file=err)
        return EXIT_CONFIG_INVALID
    print("Config checks passed.", file=out)
    return _not_implemented("init", err)


def cmd_migrate(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    from alembic import command
    from alembic.config import Config

    from trader.db import database_url

    root = Path(__file__).resolve().parent.parent
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    url = database_url()
    cfg.cmd_opts = argparse.Namespace(
        x=[f"url={url if isinstance(url, str) else url.render_as_string(hide_password=False)}"]
        + ([f"app_role={args.app_role}"] if args.app_role else [])
    )
    command.upgrade(cfg, "head")
    print("migrations applied (head)", file=out)
    return EXIT_OK


HANDLERS: Final[dict[str, Callable[[argparse.Namespace, TextIO, TextIO], int]]] = {
    "validate-config": cmd_validate_config,
    "init": cmd_init,
    "migrate": cmd_migrate,
}


def main(
    argv: Sequence[str] | None = None, out: TextIO | None = None, err: TextIO | None = None
) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    handler = HANDLERS.get(args.command)
    if handler is None:
        return _not_implemented(args.command, err)
    return handler(args, out, err)


if __name__ == "__main__":
    raise SystemExit(main())
