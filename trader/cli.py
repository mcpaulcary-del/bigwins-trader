"""``trader`` command line (spec v2.10 §3).

Every §3 command is registered. Implemented so far: ``validate-config``,
``migrate``, the config checks of ``init`` (M0) and the data-pipeline commands
``fetch``, ``distribution enter``, ``qc override`` and the builder-named
``import`` sub-command for hand-entered reference data (M1). Every other
command exits with "not implemented yet (planned for Mx)" and code 69.
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
    parse_common,
    sha256_bytes,
)
from trader.constants import COMMON_CONFIG_NAME, CONFIG_DIR_DEFAULT

EXIT_OK: Final = 0
EXIT_FAILED: Final = 1
EXIT_CONFIG_INVALID: Final = 2
EXIT_PIN_MISMATCH: Final = 3
EXIT_NOT_IMPLEMENTED: Final = 69  # EX_UNAVAILABLE

# Command -> milestone that implements it (spec §20).
PLANNED: Final[dict[str, str]] = {
    "run": "M5",
    "backtest": "M3",
    "replay": "M5",
    "status": "M5",
    "plan": "M5",
    "veto": "M5",
    "kill": "M5",
    "resume": "M5",
    "mode": "M5",
    "stage": "M9",
    "reconcile": "M5",
    "init": "M5",
    "cashflow": "M5",
    "corp-action": "M4",
    "recover": "M5",
    "drill": "M4",
    "canary": "M4",
    "golive": "M4",
    "expectations": "M6",
    "secret": "M5",
    "report": "M6",
    "hypothesis": "M3",
    "holdout": "M3",
}
ALL_COMMANDS: Final = (
    "run",
    "backtest",
    "replay",
    "status",
    "plan",
    "veto",
    "kill",
    "resume",
    "mode",
    "stage",
    "reconcile",
    "init",
    "cashflow",
    "corp-action",
    "distribution",
    "qc",
    "fetch",
    "recover",
    "drill",
    "canary",
    "golive",
    "expectations",
    "secret",
    "migrate",
    "validate-config",
    "report",
    "hypothesis",
    "holdout",
    "import",
)


def _decimal(text: str) -> Decimal:
    try:
        d = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"not a decimal amount: {text!r}") from exc
    if not d.is_finite() or d <= 0:
        raise argparse.ArgumentTypeError("amount must be a positive number")
    return d


def _signed_decimal(text: str) -> Decimal:
    try:
        d = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"not a decimal amount: {text!r}") from exc
    if not d.is_finite() or d == 0:
        raise argparse.ArgumentTypeError("amount must be a non-zero number")
    return d


def _user_opts(p: argparse.ArgumentParser, *, required: bool = True) -> None:
    p.add_argument("--user", required=required, help="user tag, e.g. 'a' (config/<user>.yaml)")
    p.add_argument("--config-dir", type=Path, default=CONFIG_DIR_DEFAULT)


def build_parser() -> argparse.ArgumentParser:  # noqa: PLR0915 - one flat registry
    parser = argparse.ArgumentParser(
        prog="trader", description="Automated ASX ETF trader (spec v2.10)"
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def add(name: str, help_: str) -> argparse.ArgumentParser:
        return sub.add_parser(name, help=help_, description=help_)

    _user_opts(add("run", "Start the live job runner (scheduler)"))
    _user_opts(add("backtest", "Run the research harness"), required=False)
    p = add("replay", "Replay a day from recorded data (replication kind 'replay')")
    p.add_argument("date", type=date.fromisoformat)
    _user_opts(p)
    _user_opts(add("status", "Show run state, flags and holdings"))
    _user_opts(add("plan", "Show the latest plan"))
    p = add("veto", "Veto buys for E (a sell needs SELL CONFIRM)")
    p.add_argument("symbol", help="symbol or ALL")
    p.add_argument("side", nargs="?", choices=["SELL"])
    p.add_argument("confirm", nargs="?", choices=["CONFIRM"])
    _user_opts(p)
    _user_opts(add("kill", "Set KILLED: no order of any kind is sent"))
    p = add("resume", "Clear the kill flag or a halt (second factor)")
    p.add_argument("--clear", required=True, choices=["kill", "integrity", "buys", "all"])
    p.add_argument("--reason", required=True)
    _user_opts(p)
    p = add("mode", "Switch to static mode (second factor)")
    p.add_argument("target", choices=["static"])
    p.add_argument("--confirm", action="store_true", required=True)
    _user_opts(p)
    p = add("stage", "Move to a later stage (second factor)")
    p.add_argument("n", type=int)
    p.add_argument("--confirm", action="store_true", required=True)
    _user_opts(p)
    p = add("reconcile", "Run reconciliation; --accept --note clears a RECON_BREAK halt")
    p.add_argument("--accept", action="store_true")
    p.add_argument("--note")
    _user_opts(p)
    p = add("init", "Onboarding: config checks (OPS-10, OPS-12), then IBKR import (M5)")
    p.add_argument("--sizing-nav", type=_decimal, help="sizing NAV in AUD for the OPS-12 check")
    _user_opts(p)
    p = add("cashflow", "Pre-announce a deposit or withdrawal")
    p.add_argument("--expect", type=_signed_decimal, required=True, help="signed AUD, e.g. -500")
    _user_opts(p)
    p = add("corp-action", "Corporate actions")
    ca = p.add_subparsers(dest="action", required=True)
    pa = ca.add_parser("apply", help="Apply a non-cash corporate action and unfreeze the symbol")
    pa.add_argument("symbol")
    _user_opts(pa)

    p = add("distribution", "Issuer distribution entry (DAT-14, DAT-22)")
    ds = p.add_subparsers(dest="action", required=True)
    pe = ds.add_parser("enter", help="Enter an issuer distribution or an expected ex-date")
    pe.add_argument("--symbol", required=True)
    pe.add_argument("--ex-date", required=True, type=date.fromisoformat)
    pe.add_argument("--status", required=True, choices=["expected", "estimated", "final"])
    pe.add_argument("--amount", type=Decimal, help="cash per unit, AUD (not for expected)")
    pe.add_argument("--franking", type=Decimal, default=None, help="franking credit per unit")
    pe.add_argument("--record-date", type=date.fromisoformat)
    pe.add_argument("--pay-date", type=date.fromisoformat)
    pe.add_argument("--period-end", type=date.fromisoformat)
    pe.add_argument("--source-note", required=True, help="issuer announcement reference")
    _user_opts(pe)

    p = add("qc", "Data-quality overrides (DAT-17)")
    qs = p.add_subparsers(dest="action", required=True)
    po = qs.add_parser("override", help="Clear a BLOCK by naming the validated close")
    po.add_argument("--symbol", required=True)
    po.add_argument("--date", required=True, type=date.fromisoformat)
    g = po.add_mutually_exclusive_group(required=True)
    g.add_argument("--use", choices=["eodhd", "flex"])
    g.add_argument("--price", type=_decimal)
    po.add_argument("--reason", required=True, help="typed reason (recorded in qc_event)")
    _user_opts(po)

    p = add("fetch", "Fetch named EODHD bars by hand, inside the call budget (DAT-23)")
    p.add_argument("--symbol", required=True)
    p.add_argument("--from", dest="from_", required=True, type=date.fromisoformat)
    p.add_argument("--to", required=True, type=date.fromisoformat)
    p.add_argument(
        "--history",
        action="store_true",
        help="history download: bars are validated on DAT-03/04/10/11 and marked backfill",
    )
    _user_opts(p)

    p = add("recover", "Rebuild lost records from Flex after a restore (second factor)")
    p.add_argument("--from-flex", action="store_true", required=True)
    _user_opts(p)
    p = add("drill", "Forced-signal drill (paper mode only)")
    p.add_argument("--sleeve")
    p.add_argument("--to", choices=["ON", "OFF"])
    p.add_argument("--end", action="store_true")
    _user_opts(p)
    p = add("canary", "Plan the canary buys (live mode only)")
    p.add_argument("--confirm", action="store_true", required=True)
    _user_opts(p)
    p = add("golive", "Go-live checks (live mode only)")
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--record")
    p.add_argument("--note")
    _user_opts(p)
    p = add("expectations", "Record acceptance of the expectations statement (USR-07)")
    p.add_argument("action", choices=["accept"])
    _user_opts(p)
    p = add("secret", "Manage this user's Docker secrets")
    sp = p.add_subparsers(dest="action", required=True)
    ps = sp.add_parser("set", help="Set a secret (value read from stdin, never from argv)")
    ps.add_argument("name")
    _user_opts(ps)
    p = add("migrate", "Apply Alembic migrations (forward-only) to one database")
    p.add_argument("--db", required=True, choices=["market", "ledger"])
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
    p = add("hypothesis", "Hypothesis registry")
    p.add_argument("action", choices=["register", "freeze", "result"])
    _user_opts(p, required=False)
    p = add("holdout", "Open the holdout once per family")
    p.add_argument("action", choices=["open"])
    p.add_argument("--family", required=True, choices=["L1", "P1"])
    p.add_argument("--confirm", action="store_true", required=True)
    _user_opts(p, required=False)

    p = add("import", "Load hand-entered reference data (insert-only, audited; §3)")
    p.add_argument("kind", choices=["calendar", "spread"])
    p.add_argument("file", type=Path, help="CSV file (see docs/DECISIONS.md X-03)")
    p.add_argument("--source", required=True, help="where the figures come from")
    _user_opts(p)
    return parser


def _not_implemented(command: str, out: TextIO) -> int:
    print(
        f"trader {command}: not implemented yet (planned for {PLANNED[command]}).",
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
        # validate-config is the check run on any config change: OPS-12 is hard.
        nav = args.sizing_nav if args.sizing_nav is not None else default_sizing_nav(loaded.user)
        res = ops12_check(loaded.common, loaded.user, nav)
        enforce_ops12(res)
        print(res.message, file=out)
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
        res = ops12_check(loaded.common, loaded.user, nav)
        enforce_ops12(res)  # OPS-12: hard at trader init
        print(res.message, file=out)
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
        x=[
            f"url={url if isinstance(url, str) else url.render_as_string(hide_password=False)}",
            f"db={args.db}",
        ]
        + ([f"app_role={args.app_role}"] if args.app_role else [])
    )
    command.upgrade(cfg, f"{args.db}@head")
    print(f"migrations applied ({args.db}@head)", file=out)
    return EXIT_OK


def _data_handler(name: str) -> Callable[[argparse.Namespace, TextIO, TextIO], int]:
    def run(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
        from trader.data import commands

        handler: Callable[[argparse.Namespace, TextIO, TextIO], int] = getattr(commands, name)
        return handler(args, out, err)

    return run


HANDLERS: Final[dict[str, Callable[[argparse.Namespace, TextIO, TextIO], int]]] = {
    "validate-config": cmd_validate_config,
    "init": cmd_init,
    "migrate": cmd_migrate,
    "fetch": _data_handler("cmd_fetch"),
    "distribution": _data_handler("cmd_distribution"),
    "qc": _data_handler("cmd_qc"),
    "import": _data_handler("cmd_import"),
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
