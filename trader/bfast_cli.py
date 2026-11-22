"""``trader-bf``: B-fast commands for the EMG2-20 book (paper only).

    trader-bf validate-config [--config config/bfast.yaml]
    trader-bf emg2-list --asof 2026-11-30 [--config ...] [--store DIR] [--out DIR]
    trader-bf deposit --book B --amount A$ [--config ...] [--journal URL]
    trader-bf kill|pause [--config ...] [--journal URL]   # one step, no second factor
    trader-bf status [--config ...] [--journal URL]
    trader-bf dashboard [--host 127.0.0.1] [--port 8080] [--demo] [--snapshot FILE]
                         # BF-D37: the read-only phone page (Tailscale only)
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
import os
import sys
from collections.abc import Callable, Sequence
from dataclasses import replace
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
    from trader.app_notify import AppNotifier, ChannelTransport
    from trader.bf_app import BfApp
    from trader.flex_pull import FlexPuller
    from trader.secrets import SecretValue
    from trader.store_refresh import StoreRefresher

DEFAULT_CONFIG = Path("config/bfast.yaml")


def _sessions(until: date) -> list[date]:
    import exchange_calendars as xc

    cal = xc.get_calendar("XASX", start="2020-01-01", end=str(until.year + 1) + "-12-31")
    return [d.date() for d in cal.sessions]


def _early_closes(until: date) -> dict[date, str]:
    """Review H4: the exchange's early closes (24 / 31 Dec), local close time HH:MM."""
    import exchange_calendars as xc

    cal = xc.get_calendar("XASX", start="2020-01-01", end=str(until.year + 1) + "-12-31")
    out: dict[date, str] = {}
    for d in cal.early_closes:
        close = cal.schedule.loc[d, "close"].tz_convert("Australia/Sydney")
        out[d.date()] = f"{close:%H:%M}"
    return out


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
    print(
        f"ok: book {cfg.book}, mode {cfg.mode}, cap A${cfg.live_emg2_20.capital_cap_aud}, "
        f"sell rule {cfg.live_emg2_20.sell_rule}"  # BF-D35
    )
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
    """The long-running paper process: scheduler + the phone app's actions and alerts
    (and/or Telegram, ``notify.channel``) + IBKR paper gateway + heartbeat."""
    from trader.approval import TotpVerifier
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
    if cfg.notify.telegram and not cfg.telegram.allowed_chat_ids:  # BF-D40
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
    from trader.secret_check import check_secrets, trader_secrets

    # BF-D33: a clear error at start-up, not a failed job later; BF-D40: which secrets
    # depends on notify.channel (vapid_private_key for the app, the bot token for Telegram)
    bad = check_secrets(trader_secrets(cfg.notify.channel))
    if bad:
        raise SystemExit("SECRET CHECK FAILED: " + "; ".join(bad))
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
    transport, notifier, chats = _channels(cfg, j)
    app = BfApp(
        replace(
            settings_from(cfg, chats, args.start, note),
            early_closes=_early_closes(datetime.now(ASX_TZ).date()),  # review H4
        ),
        j,
        broker,
        sim,
        transport,
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
    hooks, sleep = _app_wiring(cfg, j, app, notifier, args.config)
    run_forever(app, sleep=sleep, hooks=hooks)
    return 0


def _channels(
    cfg: BfastConfig, j: Journal
) -> tuple[ChannelTransport, AppNotifier | None, frozenset[int]]:
    """BF-D40: the trader's transport for ``notify.channel``: the phone app (inbox + Web
    Push), Telegram, or both."""
    from trader.app_notify import AppNotifier, ChannelTransport, WebPush
    from trader.approval import APP_CHAT, TelegramTransport
    from trader.secrets import read_secret

    tg = None
    if cfg.notify.telegram:  # a short long-poll when the app's actions share the loop
        tg = TelegramTransport(
            read_secret("telegram_bot_token"), timeout=2 if cfg.notify.app else 20
        )
    notifier = None
    if cfg.notify.app:
        push = WebPush(read_secret("vapid_private_key"), cfg.app.push_subject)
        notifier = AppNotifier(j, push, label="PAPER" if cfg.mode == "paper" else "LIVE")
    chats = frozenset(cfg.telegram.allowed_chat_ids if tg is not None else ())
    if notifier is not None:
        chats |= {APP_CHAT}
    return ChannelTransport(tg, notifier), notifier, chats


def _app_wiring(
    cfg: BfastConfig, j: Journal, app: BfApp, notifier: AppNotifier | None, config: Path
) -> tuple[list[Callable[[datetime], object]], Callable[[float], None]]:
    """BF-D39 the app's control server (actions), BF-D41 the heartbeat, BF-D42 the
    server-job results: hooks of the scheduler loop and its sleep."""
    import time as _time

    from trader.app_control import Control
    from trader.constants import BUILD_SHA_FILE
    from trader.heartbeat import Heartbeat, ping_url
    from trader.secrets import read_secret
    from trader.server_status import page_host
    from trader.strategy_runtime import StrategyRuntime
    from trader.strategy_version import fingerprint

    commit = BUILD_SHA_FILE.read_text().strip()[:40] if BUILD_SHA_FILE.is_file() else ""
    fp = fingerprint(config, Path(__file__).resolve().parent.parent, commit)
    rt = StrategyRuntime(app, fp, cfg.strategy.update_mode, app.say)  # BF-D45
    print(f"strategy {fp.label} ({rt.start(datetime.now(ASX_TZ))})", file=sys.stderr)
    hooks: list[Callable[[datetime], object]] = [rt.tick]
    sleep: Callable[[float], None] = _time.sleep
    if notifier is not None:
        ctl = Control(
            j, app.bot, frozenset(cfg.app.allowed_logins), book=cfg.book, notify=notifier.notify,
            vapid_public=notifier.push.public_key if notifier.push else None,
            refresh_prices=app.refresh_prices_now, update_mode=cfg.strategy.update_mode,
            sessions=lambda: app.sessions,
            proxy_key=key_bytes(read_secret("app_proxy_key")),  # BF-D46
            public_host=cfg.app.public_host,
            worker_key=key_bytes(read_secret("worker_job_key")),  # BF-D48
            live=cfg.mode != "paper",  # BF-D50
        )  # fmt: skip
        start_control_when_resolvable(ctl, cfg.app.control_bind_host, cfg.app.control_port)
        hooks.append(lambda now: ctl.process())
        hooks.append(lambda now: tell_server_jobs(j, notifier))
        hooks.append(lambda now: tell_backups(j, notifier))  # BF-D64
        hooks.append(lambda now: page_host(j, app.say, now))  # review F9
        sleep = ctl.wait
    hb = Heartbeat(ping_url(read_secret("healthchecks_url")), j, app.say,
                   every_s=cfg.heartbeat.every_seconds)  # fmt: skip
    print(f"heartbeat: {'on' if hb.enabled else 'off (healthchecks_url is none)'}", file=sys.stderr)
    hooks.append(hb.tick)
    return hooks, sleep


def key_bytes(secret: SecretValue) -> bytes:
    """A shared HMAC key from its secret file (hex or text, at least 32 characters)."""
    v = secret.reveal().strip()
    if len(v) < 32:
        raise SystemExit("an app key secret is shorter than 32 characters: run `bigwins update`")
    return v.encode()


def wait_for_address(
    host: str,
    resolve: Callable[[str], str] | None = None,
    sleep: Callable[[float], None] | None = None,
    max_wait_s: float = 60.0,
) -> str:
    """BF-D60 (N9): the control alias may resolve a moment after the container starts;
    retry with a growing pause (logged) instead of stopping the trader."""
    import socket
    import time as _time

    res = resolve or socket.gethostbyname
    pause = 1.0
    while True:
        try:
            return res(host)
        except OSError as e:
            print(f"app actions: {host} not resolvable yet ({e}); retrying in {pause:.0f} s",
                  file=sys.stderr)  # fmt: skip
            (sleep or _time.sleep)(pause)
            pause = min(pause * 2, max_wait_s)


def start_control_when_resolvable(ctl: object, host: str, port: int) -> None:
    """Serve the app's actions once the control address resolves; until then the app
    shows "actions unavailable" (the dashboard cannot reach the trader) and the trader
    keeps trading. Runs in a background thread."""
    import threading

    from trader.app_control import Control, serve_control

    assert isinstance(ctl, Control)

    def run() -> None:
        bind = control_bind_address(host, wait_for_address(host))
        serve_control(ctl, bind, port)
        print(f"app actions on {bind}:{port} (control network); "
              f"{len(ctl.allowed_logins)} log-in(s) allowed", file=sys.stderr)  # fmt: skip

    threading.Thread(target=run, name="app-control-bind", daemon=True).start()


def control_bind_address(host: str, addr: str | None = None) -> str:
    """BF-D46: the address of the trader's ``control``-network alias; never a wildcard."""
    import ipaddress
    import socket

    addr = addr or socket.gethostbyname(host)
    ip = ipaddress.ip_address(addr)
    if ip.is_unspecified:
        raise SystemExit(f"control_bind_host {host!r} resolves to {addr}: refused")
    return addr


def tell_backups(j: Journal, notifier: AppNotifier) -> int:
    """BF-D64: a failed backup or restore test is paged once (a good one is quiet: the
    Backups screen shows it)."""
    from trader.app_store import get_state, set_state

    told = get_state(j, "backup-told")
    seen = str(told[0]) if told and isinstance(told[0], str) else ""
    n = 0
    for key, what in (("backup-last", "Backup"), ("restore-test-last", "Restore test")):
        st = get_state(j, key)
        if not st or not isinstance(st[0], dict):
            continue
        mark = f"{key}@{st[1].isoformat()}"
        if mark in seen.split("|"):
            continue
        if not st[0].get("ok"):
            err = st[0].get("error") or "see the Backups screen"
            notifier.notify(f"PAGE {what} FAILED: {err}", "page", "/backups")
            n += 1
        seen = "|".join([*seen.split("|")[-5:], mark])
        set_state(j, "backup-told", seen, st[1])
    return n


def tell_server_jobs(j: Journal, notifier: AppNotifier) -> int:
    """BF-D42: push the result of each server job once (after a restart too)."""
    from trader.app_store import get_state, server_job_rows, set_state

    st = get_state(j, "server-jobs-told")
    told = int(st[0]) if st and isinstance(st[0], int) else 0
    n = 0
    for r in sorted(server_job_rows(j, 20), key=lambda r: int(r["id"])):
        if int(r["id"]) <= told or r["status"] in ("PENDING", "RUNNING"):
            continue
        result = str(r["result"]).strip().splitlines()[-1:] or [""]
        kind = "info" if r["status"] == "DONE" else "page"
        prefix = "" if r["status"] == "DONE" else "PAGE "
        text = f"{prefix}Server job {r['id']} '{r['action']}': {r['status']}. {result[0][:300]}"
        notifier.notify(text, kind, "/server")
        set_state(j, "server-jobs-told", int(r["id"]), datetime.now(ASX_TZ))
        n += 1
    return n


def cmd_check_secrets(args: argparse.Namespace) -> int:
    """BF-D33: the Docker secret files are there, non-empty and readable by this uid
    (and by other users: 444 files in a 700 folder). Contents are never read. BF-D40:
    the list follows ``notify.channel`` of the config (app: vapid_private_key; telegram:
    telegram_bot_token)."""
    from trader.secret_check import check_secrets, stack_secrets, trader_secrets

    channel = load_bfast_config(args.config).notify.channel if args.config.is_file() else "app"
    names = stack_secrets(channel) if args.all else trader_secrets(channel)
    bad = check_secrets(names, args.dir)
    for b in bad:
        print(f"SECRET CHECK FAILED: {b}", file=sys.stderr)
    if bad:
        return 2
    uid = os.getuid() if hasattr(os, "getuid") else -1
    print(f"ok: {len(names)} secret file(s) in {args.dir} readable by uid {uid}")
    return 0


def cmd_daily_summary(args: argparse.Namespace) -> int:
    """BF-D64: the readable daily page for OneDrive (read-only journal; no secrets)."""
    from trader.app_store import inbox_rows
    from trader.backups import daily_summary
    from trader.dashboard import Sources, collect

    cfg = load_bfast_config(args.config)
    j = _read_only_journal(cfg, args.journal)
    v = collect(Sources(j, cfg.book, cfg.data.sim_book))
    try:
        inbox = inbox_rows(j, 200)
    except Exception:
        inbox = []
    page = daily_summary(v, inbox, "PAPER" if cfg.mode == "paper" else "LIVE")
    if args.out == "-":
        sys.stdout.write(page)
    else:
        Path(args.out).write_text(page, encoding="utf-8")
    return 0


def cmd_vapid_public(args: argparse.Namespace) -> int:
    """BF-D40: print the public key of the VAPID private key (it never prints the key)."""
    from trader.app_notify import public_key_of
    from trader.secrets import SecretValue

    print(public_key_of(SecretValue(args.key.read_text(encoding="utf-8"))))
    return 0


def cmd_server_jobs(args: argparse.Namespace) -> int:
    """BF-D42: the host worker's side of the server-job queue (``deploy/bigwins.sh
    worker``, root on the host, through ``docker compose exec trader``). ``claim``
    prints the next job as JSON (``{}`` when none) and marks it RUNNING; ``finish``
    records the result read from stdin; ``status`` stores the host's status snapshot
    (JSON on stdin; log lines are cleaned of anything secret-looking); ``list`` prints
    the latest jobs."""
    from trader.app_store import (
        FORCE_MARKET,
        FORCE_MIGRATION,
        IMMEDIATE,
        SERVER_ACTIONS,
        STRATEGY,
        claim_server_job,
        created_text,
        finish_server_job,
        server_job_rows,
        set_state,
    )
    from trader.server_status import clean_status

    j = cli_journal(args)
    now = datetime.now(ASX_TZ)
    if args.op == "claim":
        r = claim_server_job(j, now, wait=lambda m: _job_wait(j, args, m, now))
        if r is not None and r["action"] not in SERVER_ACTIONS:  # never: add_server_job checks
            finish_server_job(j, int(r["id"]), "REFUSED", "unknown action", now)
            r = None
        print(json.dumps({} if r is None else {
            "id": r["id"], "action": r["action"], "force": bool(r["force"] & FORCE_MARKET),
            "strategy": bool(r["force"] & STRATEGY), "immediate": bool(r["force"] & IMMEDIATE),
            "migration": bool(r["force"] & FORCE_MIGRATION), "flags": int(r["force"]),
            "commit": r.get("commit") or "", "created": created_text(r["requested_at"]),
            "sig": r.get("sig") or "",
        }))  # fmt: skip
        return 0
    if args.op == "finish":
        if args.id is None or args.status is None:
            raise SystemExit("finish needs --id and --status")
        text = clean_status({"log": sys.stdin.read()[-8000:].splitlines()})["log"]
        ok = finish_server_job(j, args.id, args.status, "\n".join(text), now)
        print("recorded" if ok else "not running (already finished?)")
        return 0 if ok else 1
    if args.op == "status":
        raw = json.loads(sys.stdin.read() or "{}")
        set_state(j, "host-status", clean_status(raw), now)
        if isinstance(raw.get("update"), dict):  # BF-D45: what an incoming update changes
            old = args.config.read_text(encoding="utf-8") if args.config.is_file() else None
            set_state(j, "update-available", update_info(raw["update"], old), now)
        print("status stored")
        return 0
    if args.op == "backup":  # BF-D64: the worker's backup / restore-test result
        from trader.backups import record_result

        r = record_result(j, json.loads(sys.stdin.read() or "{}"), now)
        print("backup result stored: " + ("ok" if r["ok"] else "FAILED"))
        return 0
    if args.op == "reveal":  # BF-D64: the sealed recovery key, for one view in the app
        import re

        sealed = sys.stdin.read().strip()
        if not re.fullmatch(r"[0-9a-f]{100,4000}", sealed):
            raise SystemExit("not a sealed key")
        set_state(j, "backup-key-sealed", {"sealed": sealed}, now)
        print("sealed key stored (shown once in the app, cleared after 10 minutes)")
        return 0
    for r in server_job_rows(j, 10):
        print(
            f"{r['id']} {r['action']} {r['status']} {r['requested_at']} {str(r['result'])[-80:]!r}"
        )
    return 0


def update_info(u: dict[str, object], old_config: str | None) -> dict[str, object]:
    """BF-D45: the host worker's ``git fetch`` result, classified here (strategy or
    app-only, with reasons) and with the incoming release notes; cleaned of anything
    secret-looking."""
    import re

    from trader.server_status import clean_line
    from trader.strategy_version import classify_update, load_changelog

    sha = re.compile(r"^[0-9a-f]{7,40}$")

    def h(x: object) -> str:
        v = str(x or "")
        return v if sha.fullmatch(v) else ""

    files = [str(f)[:200] for f in u.get("files") or [] if isinstance(f, str)][:300]  # type: ignore[attr-defined]
    new_cfg = u.get("new_config") if isinstance(u.get("new_config"), str) else None
    cls = classify_update(files, old_config, new_cfg)  # type: ignore[arg-type]
    notes = load_changelog(str(u.get("new_changelog") or ""))[:1]
    try:
        ahead = int(str(u.get("ahead") or 0))
    except ValueError:
        ahead = 0
    return {
        "ahead": ahead, "head": h(u.get("head")), "remote": h(u.get("remote")),
        "previous": h(u.get("previous")), "strategy": cls["strategy"], "reasons": cls["reasons"],
        "previous_migrations": bool(u.get("previous_migrations")),
        "files": files[:40], "subject": clean_line(str(u.get("subject") or ""))[:200],
        "notes": {k: clean_line(str(v))[:600] for k, v in notes[0].items()} if notes else {},
    }  # fmt: skip


def working_orders(j: Journal, book: str) -> int:
    """Orders of ``book`` at the broker now (BF-D45: an update never interrupts them)."""
    from trader.strategy_version import WORKING

    return sum(1 for _, st in j.intents_of_book(book) if st in WORKING)


def _job_wait(
    j: Journal, args: argparse.Namespace, m: dict[str, object], now: datetime
) -> str | None:
    """BF-D45: a strategy update or a rollback waits for the close and for working orders."""
    from trader.app_control import asx_open
    from trader.app_store import STRATEGY
    from trader.strategy_version import apply_wait

    if m["action"] not in ("update", "rollback"):
        return None
    strat = m["action"] == "rollback" or bool(int(str(m["force"])) & STRATEGY)
    book = load_bfast_config(args.config).book if args.config.is_file() else "EMG2_18_PAPER"
    return apply_wait(strat, asx_open(now), working_orders(j, book))


def cmd_tax_report(args: argparse.Namespace) -> int:
    """BF-D29: the financial year's CSV files and markdown summary for the accountant."""
    from trader.tax_report import (
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
    params = cfg.tax.params(cfg.fund_codes())
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


def _read_only_journal(cfg: BfastConfig, explicit: str | None) -> Journal:
    """BF-D37: the running app's journal (or ``--journal URL``) on a read-only engine."""
    from sqlalchemy.engine import make_url

    from trader.journal import read_only_engine
    from trader.secrets import read_secret

    raw = explicit or os.environ.get(cfg.journal.url_env)
    if not raw:
        raise SystemExit(f"{cfg.journal.url_env} is not set (a password-free database URL)")
    url = make_url(raw)
    if url.drivername.startswith("postgresql") and url.password is None:
        # BF-D52: the dashboard's own SELECT-only role and its password secret
        name = os.environ.get("TRADER_BF_DB_PASSWORD_SECRET", "db_password")
        url = url.set(password=read_secret(name).reveal())
    return Journal.read_only(read_only_engine(url))


def cmd_dashboard(args: argparse.Namespace) -> int:
    """BF-D37 / BF-D43: serve the phone app (or write the Home screen with --snapshot).
    Its own screens are read-only; ``/act/...`` goes to the trader's control server
    (BF-D39) or, with ``--demo``, to a simulated one that changes nothing."""
    import tempfile

    from trader.dashboard import (
        ActionsFn,
        Dashboard,
        Limits,
        Sources,
        collect,
        proxy_to,
        render,
        serve,
        store_index,
        store_prices,
    )
    from trader.journal import read_only_engine

    cfg = load_bfast_config(args.config)
    tax = cfg.tax.params(cfg.fund_codes())
    actions: ActionsFn | None = None
    if args.demo:
        from trader.dashboard_demo import build_demo, demo_control

        demo = build_demo(Path(tempfile.mkdtemp()) / "demo_journal.sqlite")
        j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
        src = Sources(
            j, cfg.book, cfg.data.sim_book, index=demo.index, index_label="Index (demo)",
            sessions=lambda: demo.sessions, today=lambda: demo.last_day, clock=lambda: demo.now,
            out_dir=Path(args.out) if args.out else None, index_note="synthetic", demo=True,
            tax_params=tax, prices=demo.prices, forecast_dir=args.config.parent,
        )  # fmt: skip
        import secrets as _secrets

        from trader.dashboard import signed_local

        demo_key = _secrets.token_hex(32).encode()  # BF-D55: the demo signs like production
        ctl = demo_control(j, demo)
        ctl.proxy_key = demo_key
        actions = signed_local(ctl.respond, demo_key)
    else:
        j = _read_only_journal(cfg, args.journal)
        store = Path(args.store) if args.store else cfg.data.forward_store
        idx = cfg.dashboard.index_code
        src = Sources(
            j, cfg.book, cfg.data.sim_book,
            Limits(cfg.risk.value_review_aud, cfg.risk.value_halt_buys_aud,
                   cfg.risk.value_line_halt_aud),
            index=store_index(store, idx) if (store / "manifest.tsv").is_file() else None,
            index_label=idx, store_root=store if store.is_dir() else None,
            out_dir=Path(args.out) if args.out else None,
            sessions=lambda: _sessions(datetime.now(ASX_TZ).date()),
            approval_deadline=cfg.execution.approval_deadline, tax_params=tax,
            marginal_rate=cfg.tax.marginal_rate, live=cfg.mode != "paper",
            prior_losses=cfg.tax.prior_losses_aud, amit_csv=cfg.tax.amit_csv,
            prices=store_prices(store) if (store / "manifest.tsv").is_file() else None,
            forecast_dir=args.config.parent,
        )  # fmt: skip
        if cfg.notify.app and not args.snapshot:
            from trader.secrets import read_secret

            actions = proxy_to(cfg.app.control_url, key_bytes(read_secret("app_proxy_key")))
    if args.snapshot:
        Path(args.snapshot).write_text(render(collect(src)), encoding="utf-8")
        print(f"wrote {args.snapshot}")
        return 0
    logins = frozenset(x.strip().lower() for x in cfg.dashboard.allowed_logins)
    acting = frozenset({"demo"}) if args.demo else frozenset(
        x.strip().lower() for x in cfg.app.allowed_logins if x.strip()
    )  # fmt: skip
    from trader.strategy_version import CHANGELOG, load_changelog

    cl = args.config.parent / Path(CHANGELOG).name

    def changelog() -> list[dict[str, object]]:
        return load_changelog(cl.read_text(encoding="utf-8")) if cl.is_file() else []

    app = Dashboard(
        src, logins, actions, acting, cfg.notify.channel, _version(), lambda: _checklist(cfg, j),
        cfg.strategy.update_mode, changelog,
        trusted_peers=frozenset() if args.demo else frozenset(cfg.dashboard.trusted_proxies),
        live=cfg.mode != "paper",
        setup_facts=lambda: {"account_id": cfg.broker.account_id},  # BF-D63 (form only)
    )  # fmt: skip
    httpd = serve(app, args.host, args.port)
    print(f"phone app on http://{args.host}:{args.port}", file=sys.stderr)
    httpd.serve_forever()
    return 0


def _version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("asx-trader")
    except PackageNotFoundError:
        return "dev"


def _checklist(cfg: BfastConfig, j: Journal) -> list[tuple[str, bool | None]]:
    """The go-live checklist items the app can see (GO_LIVE_GUIDE part E); the rest is
    the owner's own sign-off."""
    from trader.broker.base import LIVE_TRADING_ENABLED

    started = bool(j.job_records(f"value:{cfg.book}:")) if _has_tables(j) else False
    return [
        (
            "Paper mode (mode: paper, allow_live false)",
            cfg.mode == "paper" and not cfg.broker.allow_live,
        ),
        ("Live trading switched off in the code", not LIVE_TRADING_ENABLED),
        ("Paper account id set", cfg.broker.account_id is not None),
        ("Trader has run at least one trading day", started),
        ("Phone app can act (allowed log-in set)", bool(cfg.app.allowed_logins)),
        ("Go-live checklist signed (part E)", None),
    ]


def _has_tables(j: Journal) -> bool:
    from sqlalchemy import inspect

    try:
        return "bf_events" in inspect(j.engine).get_table_names()
    except Exception:
        return False


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


def main(argv: Sequence[str] | None = None) -> int:  # noqa: PLR0915 - one parser per command
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
    p = sub.add_parser("run", help="scheduler + app/Telegram + IBKR paper gateway (paper only)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--start", type=date.fromisoformat, help="L6 start decision date (canary)")
    p = sub.add_parser("check-secrets", help="the Docker secret files are readable (BF-D33)")
    p.add_argument("--all", action="store_true", help="every file of the stack (secrets-check)")
    p.add_argument("--dir", type=Path, default=Path("/run/secrets"))
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p = sub.add_parser("daily-summary", help="the day's readable summary as HTML (BF-D64)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--journal", help="journal URL, explicit (tests/dev; opened read-only)")
    p.add_argument("--out", default="-", help="file, or - for stdout")
    p = sub.add_parser("vapid-public", help="the phone app's Web Push public key (BF-D40)")
    p.add_argument("--key", type=Path, default=Path("/run/secrets/vapid_private_key"))
    p = sub.add_parser("server-jobs", help="the host worker's queue (BF-D42; root on the host)")
    p.add_argument("op", choices=["claim", "finish", "status", "list", "backup", "reveal"])
    p.add_argument("--id", type=int)
    p.add_argument("--status", choices=["DONE", "FAILED", "REFUSED"])
    _journal_args(p)
    p = sub.add_parser("deposit", help="record a deposit into a book's journal (paper set-up)")
    p.add_argument("--book", required=True)
    p.add_argument("--amount", type=Decimal, required=True)
    _journal_args(p)
    _tax_parser(sub)
    p = sub.add_parser("dashboard", help="read-only phone page of the paper book (BF-D37)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--host", default="127.0.0.1", help="bind address (container: 0.0.0.0)")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--journal", help="journal URL, explicit (tests/dev; opened read-only)")
    p.add_argument("--store", help="price store (default: the config's data.forward_store)")
    p.add_argument("--out", default="/app/out", help="the trader's output folder (disk free)")
    p.add_argument("--demo", action="store_true", help="synthetic demo data (screenshots)")
    p.add_argument("--snapshot", help="write the page to this file and exit")
    for name in ("kill", "pause", "status"):
        _journal_args(sub.add_parser(name))
    a = ap.parse_args(argv)
    commands = {
        "validate-config": cmd_validate_config,
        "emg2-list": cmd_emg2_list,
        "dry-run": cmd_dry_run,
        "run": cmd_run,
        "tax-report": cmd_tax_report,
        "check-secrets": cmd_check_secrets,
        "dashboard": cmd_dashboard,
        "vapid-public": cmd_vapid_public,
        "daily-summary": cmd_daily_summary,
        "server-jobs": cmd_server_jobs,
    }
    if a.cmd in commands:
        return commands[a.cmd](a)
    return cmd_journal(a)


if __name__ == "__main__":
    sys.exit(main())
