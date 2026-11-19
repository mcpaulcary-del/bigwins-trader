"""``trader-bf``: B-fast commands for the EMG2-20 book (paper only).

    trader-bf validate-config [--config config/bfast.yaml]
    trader-bf emg2-list --asof 2026-11-30 [--config ...] [--store DIR] [--out DIR]
    trader-bf kill|pause [--journal URL]           # one step, no second factor
    trader-bf status [--journal URL]

``emg2-list`` builds the panel from the forward store (read-only), prints the EMG2 list
T and the EMG2-20 picks for a fresh A$10,000 book, and writes
``emg2_list_<D>.json`` / ``emg2_20_picks_<D>.json`` with their SHA-256 digests (the
"written and hashed before the open" step of BF1). It never contacts a broker.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from trader.bfast_config import BfastConfig, LicListError, lic_codes, load_bfast_config
from trader.canonical import canonical_json
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.risk import SafetyLevel

if TYPE_CHECKING:
    from trader.flex_pull import FlexPuller

DEFAULT_CONFIG = Path("config/bfast.yaml")


def _sessions(until: date) -> list[date]:
    import exchange_calendars as xc

    cal = xc.get_calendar("XASX", start="2020-01-01", end=str(until.year + 1) + "-12-31")
    return [d.date() for d in cal.sessions]


def _journal(url: str | None) -> Journal:
    from sqlalchemy import create_engine

    return Journal(create_engine(url)) if url else Journal.sqlite("bf_journal.sqlite3")


def cmd_validate_config(args: argparse.Namespace) -> int:
    cfg = load_bfast_config(args.config)
    try:
        lic = lic_codes(cfg)  # BF-D21: the frozen LIC list must be there and match its pin
    except LicListError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    print(f"ok: book {cfg.book}, mode {cfg.mode}, cap A${cfg.live_emg2_20.capital_cap_aud}")
    print(lic.describe())
    return 0


def cmd_emg2_list(args: argparse.Namespace) -> int:
    from trader.data.forward_store import ForwardStore
    from trader.lines.emg2 import BookState, decide_emg2_20, emg2_list

    cfg = load_bfast_config(args.config)
    store = Path(args.store or cfg.data.forward_store)
    etp: frozenset[str] = frozenset()
    if cfg.data.etp_list.is_file():
        etp = frozenset(x.strip() for x in cfg.data.etp_list.read_text().splitlines() if x.strip())
    try:
        lic_list = lic_codes(cfg)  # BF-D21: no list, no picks (no fallback)
    except LicListError as e:
        raise SystemExit(f"REFUSED (BF-D21): {e}") from e
    lic = lic_list.codes
    print(lic_list.describe(), file=sys.stderr)
    panel = ForwardStore(store).build_panel(
        args.asof,
        _sessions(args.asof),
        history=cfg.data.history_sessions,
        etp_codes=etp,
        lic_codes=lic,
    )
    lst = emg2_list(panel)
    dec = decide_emg2_20(
        panel, BookState(cfg.book, cfg.live_emg2_20.capital_cap_aud), cfg.emg2_20_params()
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"emg2_list_{args.asof}.json").write_text(canonical_json(lst.payload()))
    (out / f"emg2_20_picks_{args.asof}.json").write_text(canonical_json(dec.payload()))
    print(
        json.dumps(
            {
                "as_of": str(args.asof),
                "eligible": len(lst.eligible),
                "band_c": len(lst.band_c),
                "targets": list(lst.targets),
                "data_block": lst.data_block,
                "list_sha256": lst.digest,
                "picks": [[b.entity, str(b.value_aud), str(b.ref_close)] for b in dec.buys],
                "skipped": [[s.entity, s.reason] for s in dec.skipped],
                "picks_sha256": dec.digest,
            },
            indent=1,
        )
    )
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    from trader.bf_dryrun import forward_store_dry_run

    cfg = load_bfast_config(args.config)
    sess = _sessions(args.to)
    days = [d for d in sess if args.start <= d <= args.to]
    decisions = {args.start: "S", **dict.fromkeys(args.decide, "R")}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summ, _, tr = forward_store_dry_run(
        cfg,
        Path(args.store or cfg.data.forward_store),
        sess,
        days,
        decisions,
        str(out / f"dryrun_{args.start}_{args.to}.sqlite3"),
    )
    (out / f"dryrun_{args.start}_{args.to}_telegram.txt").write_text(
        "\n\n----\n\n".join(t for _, t in tr.outbox)
    )
    print(
        json.dumps(
            {**summ.__dict__, "cash": str(summ.cash), "broker_cash": str(summ.broker_cash)},
            indent=1,
            default=str,
        )
    )
    return 0 if summ.safety == "NORMAL" and not summ.pages else 1


def _journal_from_config(url_env: str) -> Journal:
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    from trader.secrets import read_secret

    raw = os.environ.get(url_env)
    if not raw:
        raise SystemExit(f"{url_env} is not set (a password-free database URL)")
    url = make_url(raw)
    if url.drivername.startswith("postgresql") and url.password is None:
        url = url.set(password=read_secret("db_password").reveal())
    return Journal(create_engine(url))


def flex_puller(cfg: BfastConfig) -> FlexPuller | None:
    """BF-D27: the scheduled Flex download, token and query id from the Docker secrets."""
    from trader.data.store import RawStore
    from trader.flex_pull import FlexPuller

    fp, inbox = cfg.data.flex_pull, cfg.data.flex_inbox
    if fp is None or inbox is None:
        return None
    return FlexPuller(
        inbox, RawStore(fp.raw_dir, "owner"), lookback_days=fp.lookback_days,
        max_days=fp.max_days, attempts=fp.attempts, backoff_s=fp.backoff_seconds,
    )  # fmt: skip


def cmd_run(args: argparse.Namespace) -> int:
    """The long-running paper process: scheduler + Telegram + IBKR paper gateway."""
    from trader.approval import TelegramTransport, TotpVerifier
    from trader.bf_app import BfApp
    from trader.bf_dryrun import ca_source_from, settings_from, store_providers
    from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
    from trader.broker.paper_sim import SimBroker
    from trader.ca_book import flex_inbox
    from trader.scheduler import run_forever
    from trader.secrets import read_secret

    cfg = load_bfast_config(args.config)
    if cfg.broker.account_id is None:
        raise SystemExit("broker.account_id (the IBKR paper DU... id) is not set in the config")
    if not cfg.telegram.allowed_chat_ids:
        raise SystemExit("telegram.allowed_chat_ids is empty: nobody could approve an order")
    j = _journal_from_config(cfg.journal.url_env)
    for book in (cfg.book, cfg.data.sim_book):
        if j.cash(book) == 0 and not j.positions(book):
            raise SystemExit(f"book {book} has no deposit: run `trader-bf deposit` first")
    broker = IbkrPaperBroker(
        IbkrSettings(cfg.broker.host, cfg.broker.port, cfg.broker.client_id, cfg.broker.account_id)
    )
    broker.connect()
    sim = SimBroker.from_journal(j, cfg.data.sim_book, cfg.data.sim_half_spread)
    sess = _sessions(datetime.now(ASX_TZ).date())
    panel, closes, marks, note = store_providers(
        cfg, cfg.data.forward_store, sess, refresh_seconds=600
    )
    print(note, file=sys.stderr)
    app = BfApp(
        settings_from(cfg, frozenset(cfg.telegram.allowed_chat_ids), args.start, note),
        j,
        broker,
        sim,
        TelegramTransport(read_secret("telegram_bot_token")),
        TotpVerifier(read_secret("totp_seed")),
        sess,
        panel,
        closes,
        marks,
        lic_guard=lambda: lic_codes(cfg),  # BF-D21: checked before every decision and send
        ca_source=ca_source_from(cfg, cfg.data.forward_store),  # BF-D23
        flex=flex_inbox(cfg.data.flex_inbox) if cfg.data.flex_inbox else None,
        flex_pull=flex_puller(cfg),  # BF-D27
    )
    run_forever(app)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trader-bf", description="B-fast EMG2-20 (paper only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate-config")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p = sub.add_parser("emg2-list")
    p.add_argument("--asof", type=date.fromisoformat, required=True)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--store")
    p.add_argument("--out", default="out")
    p = sub.add_parser("dry-run", help="replay recorded data end to end against the mock gateway")
    p.add_argument(
        "--start", type=date.fromisoformat, required=True, help="start decision (canary)"
    )
    p.add_argument("--to", type=date.fromisoformat, required=True)
    p.add_argument(
        "--decide",
        type=date.fromisoformat,
        action="append",
        default=[],
        help="extra regular decision dates (month-ends run anyway)",
    )
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--store")
    p.add_argument("--out", default="out")
    p = sub.add_parser("run", help="scheduler + Telegram + IBKR paper gateway (paper only)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--start", type=date.fromisoformat, help="L6 start decision date (canary)")
    p = sub.add_parser("deposit", help="record a deposit into a book's journal (paper set-up)")
    p.add_argument("--book", required=True)
    p.add_argument("--amount", type=Decimal, required=True)
    p.add_argument("--journal")
    for name in ("kill", "pause", "status"):
        p = sub.add_parser(name)
        p.add_argument("--journal")
    a = ap.parse_args(argv)
    if a.cmd == "validate-config":
        return cmd_validate_config(a)
    if a.cmd == "emg2-list":
        return cmd_emg2_list(a)
    if a.cmd == "dry-run":
        return cmd_dry_run(a)
    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "deposit":
        _journal(a.journal).add_cash(a.book, "DEPOSIT", a.amount, "deposit via CLI")
        print(f"deposit A${a.amount} recorded for {a.book}")
        return 0
    j = _journal(a.journal)
    if a.cmd == "kill":
        j.set_safety(SafetyLevel.KILLED, "CLI kill", "cli")
        print("KILLED (open orders are cancelled by the runner's kill path; re-arm needs 2FA)")
    elif a.cmd == "pause":
        j.set_safety(SafetyLevel.PAUSED, "CLI pause", "cli")
        print("PAUSED")
    print(f"safety {j.safety_level().value}; cash/positions per book via the report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
