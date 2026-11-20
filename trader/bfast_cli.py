"""``trader-bf``: B-fast commands for the EMG2-20 book (paper only).

    trader-bf validate-config [--config config/bfast.yaml]
    trader-bf emg2-list --asof 2026-11-30 [--config ...] [--store DIR] [--out DIR]
    trader-bf deposit --book B --amount A$ [--config ...] [--journal URL]
    trader-bf kill|pause [--config ...] [--journal URL]   # one step, no second factor
    trader-bf status [--config ...] [--journal URL]
    trader-bf tax-report --fy 2026-27 [--book B] [--journal URL] [--flex DIR] [--amit CSV]
                         [--prior-losses A$] [--out DIR]     # BF-D29, not tax advice

``emg2-list`` builds the panel from the forward store (read-only), prints the EMG2 list
T and the EMG2-20 picks for a fresh A$10,000 book, and writes
``emg2_list_<D>.json`` / ``emg2_20_picks_<D>.json`` with their SHA-256 digests (the
"written and hashed before the open" step of BF1). It never contacts a broker.

``deposit``, ``kill``, ``pause``, ``status`` and ``tax-report`` act on **the running
app's journal** (BF-D30): the database named by the config's ``journal.url_env``
(``TRADER_BF_JOURNAL_URL`` in the trader container: the server's Postgres, password from
the ``db_password`` Docker secret), exactly as ``trader-bf run`` does. There is no
implicit local SQLite file any more. ``--journal URL`` (or a ``sqlite`` URL in the
environment variable) names another database explicitly: tests and development only;
every command prints which journal it used (password-free).
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
    from trader.store_refresh import StoreRefresher

DEFAULT_CONFIG = Path("config/bfast.yaml")


def _sessions(until: date) -> list[date]:
    import exchange_calendars as xc

    cal = xc.get_calendar("XASX", start="2020-01-01", end=str(until.year + 1) + "-12-31")
    return [d.date() for d in cal.sessions]


def _journal(url: str) -> Journal:
    """An explicitly named journal database (``--journal URL``; tests and development)."""
    from sqlalchemy import create_engine

    return Journal(create_engine(url))


def cli_journal(args: argparse.Namespace) -> Journal:
    """BF-D30: the journal of the running app (config ``journal.url_env``, Postgres on the
    server), unless ``--journal URL`` names another one explicitly. Never a default file."""
    if getattr(args, "journal", None):
        j = _journal(args.journal)
    else:
        cfg = load_bfast_config(args.config)
        j = _journal_from_config(cfg.journal.url_env)
    print(f"journal: {j.engine.url.render_as_string(hide_password=True)}", file=sys.stderr)
    return j


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


def store_refresher(cfg: BfastConfig) -> StoreRefresher | None:
    """BF-D31: the daily EODHD bulk refresh of the price store, key from the Docker secret."""
    from trader.data.store import RawStore
    from trader.store_refresh import StoreRefresher

    sr = cfg.data.store_refresh
    if sr is None:
        return None
    return StoreRefresher(
        cfg.data.forward_store, RawStore(sr.raw_dir, "owner"), calls_per_day=sr.calls_per_day,
        bulk_call_cost=sr.bulk_call_cost, min_rows=sr.min_rows, min_share=float(sr.min_share),
        attempts=sr.attempts, backoff_s=sr.backoff_seconds,
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
    dr = cfg.paper_dry_run
    if dr is not None:  # BF-D32: paper only (schema + DU guard), and never left on
        from trader.broker.base import assert_paper

        assert_paper(
            mode=cfg.mode, account_id=cfg.broker.account_id, port=cfg.broker.port,
            allow_live=cfg.broker.allow_live,
        )  # fmt: skip
        if datetime.now(ASX_TZ).date() > dr.until:
            raise SystemExit(
                f"paper_dry_run ended on {dr.until}: remove it from the config (BF-D32)"
            )
        print(
            f"PAPER DRY RUN (BF-D32) until {dr.until}: forced decisions "
            + ", ".join(f"{d} {s}" for d, s in sorted(dr.decisions.items())),
            file=sys.stderr,
        )
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
        store_refresh=store_refresher(cfg),  # BF-D31: daily EODHD bulk into the store
    )
    run_forever(app)
    return 0


def cmd_tax_report(args: argparse.Namespace) -> int:
    """BF-D29: the financial year's CSV files and markdown summary for the accountant."""
    from trader.tax_report import (
        TaxParams,
        build_report,
        flex_statements,
        load_amit_csv,
        write_report,
    )

    cfg = load_bfast_config(args.config)
    j = cli_journal(args)
    flex_dir = args.flex if args.flex is not None else cfg.data.flex_inbox
    statements = None
    if flex_dir is not None and Path(flex_dir).is_dir():
        statements = flex_statements(sorted(Path(flex_dir).glob("*.xml")))
    amit_path = args.amit if args.amit is not None else cfg.tax.amit_csv
    amit = load_amit_csv(Path(amit_path)) if amit_path and Path(amit_path).is_file() else []
    params = TaxParams(cfg.tax.parcel_method, cfg.tax.discount_days, cfg.fund_codes())
    rep = build_report(
        j, args.book or cfg.book, args.fy, params, statements, amit, args.prior_losses,
        cfg.broker.account_id, paper=cfg.mode == "paper",
    )  # fmt: skip
    for p in write_report(rep, Path(args.out)):
        print(p)
    bad = [x for x in rep.recon if x.problem]
    print(
        f"FY {rep.fy}: net capital gain A${rep.summary.net_gain:.2f}, loss carried forward "
        f"A${rep.summary.carried_out:.2f}; reconciliation: "
        + ("not run (no Flex statements)" if statements is None else f"{len(bad)} difference(s)")
        + f"; {len(rep.flags)} item(s) to confirm. General information, not tax advice."
    )
    return 0


def _tax_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = sub.add_parser("tax-report", help="financial-year tax report (BF-D29; not tax advice)")
    p.add_argument("--fy", required=True, help="financial year, e.g. 2026-27")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--book", help="book (default: the config's broker book)")
    p.add_argument("--journal", help="journal URL (default: the config's url_env)")
    p.add_argument("--flex", type=Path, help="Flex XML directory (default: data.flex_inbox)")
    p.add_argument("--amit", type=Path, help="AMIT entries CSV (default: tax.amit_csv)")
    p.add_argument("--prior-losses", type=Decimal, default=Decimal(0),
                   help="net capital losses carried in from before this book (A$)")  # fmt: skip
    p.add_argument("--out", default="out/tax")


def _journal_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument(
        "--journal",
        help="journal URL, explicit (tests/dev); default: the running app's journal "
        "(the config's journal.url_env, Postgres on the server)",
    )


def cmd_journal(a: argparse.Namespace) -> int:
    """deposit / kill / pause / status on the running app's journal (BF-D30)."""
    j = cli_journal(a)
    if a.cmd == "deposit":
        if a.amount <= 0:
            raise SystemExit("a deposit must be positive")
        j.add_cash(a.book, "DEPOSIT", a.amount, "deposit via CLI")
        print(f"deposit A${a.amount} recorded for {a.book}; cash now A${j.cash(a.book)}")
        return 0
    if a.cmd == "kill":
        j.set_safety(SafetyLevel.KILLED, "CLI kill", "cli")
        print("KILLED (open orders are cancelled by the runner's kill path; re-arm needs 2FA)")
    elif a.cmd == "pause":
        j.set_safety(SafetyLevel.PAUSED, "CLI pause", "cli")
        print("PAUSED")
    print(f"safety {j.safety_level().value}")
    if a.cmd == "status":
        cfg = load_bfast_config(a.config) if a.config.is_file() else None
        for book in (cfg.book, cfg.data.sim_book) if cfg else ():
            pos = j.positions(book)
            held = dict(sorted(pos.items()))
            print(f"{book}: cash A${j.cash(book)}, {len(pos)} holding(s) {held}")
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
    _journal_args(p)
    _tax_parser(sub)
    for name in ("kill", "pause", "status"):
        _journal_args(sub.add_parser(name))
    a = ap.parse_args(argv)
    commands = {
        "validate-config": cmd_validate_config,
        "emg2-list": cmd_emg2_list,
        "dry-run": cmd_dry_run,
        "run": cmd_run,
        "tax-report": cmd_tax_report,
    }
    if a.cmd in commands:
        return commands[a.cmd](a)
    return cmd_journal(a)


if __name__ == "__main__":
    sys.exit(main())
