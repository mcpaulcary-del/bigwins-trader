"""CLI handlers for the data-pipeline commands (M1): ``fetch``, ``distribution enter``,
``qc override`` and ``import calendar|spread`` (spec v2.10 §3, DAT-14, DAT-17, DAT-23)."""

from __future__ import annotations

import argparse
import csv
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TextIO

from sqlalchemy.orm import Session

from trader.calendar import AsxCalendar, VenueTimes
from trader.config import ConfigError, LoadedConfig, deployed_git_sha, load_config
from trader.constants import DATA_DIR_DEFAULT, XASX
from trader.data.eodhd import CallBudget, EodhdClient, EodhdError, fetch_by_hand, urllib_transport
from trader.data.instruments import InstrumentError, require_instrument
from trader.data.issuer import DistributionError, enter_distribution
from trader.data.models import CalendarDay, write_market_audit
from trader.data.quality import (
    OverrideError,
    Schedule,
    SymbolContext,
    qc_override,
    validate_symbol_day,
)
from trader.data.spreads import enter_spread
from trader.data.store import RawStore, latest_bars
from trader.dbtypes import install_mutability_guard
from trader.enums import DistributionStatus
from trader.secrets import SecretError
from trader.timeutil import parse_hhmm, utc_now

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_CONFIG_INVALID = 2


def _data_dir() -> Path:
    return Path(os.environ.get("TRADER_DATA_DIR", str(DATA_DIR_DEFAULT)))


@contextmanager
def market_session(user: str) -> Iterator[Session]:
    from trader.db import make_engine, market_database_url

    engine = make_engine(market_database_url(user))
    try:
        with Session(engine) as s:
            install_mutability_guard(s)
            yield s
    finally:
        engine.dispose()


def _load(args: argparse.Namespace) -> LoadedConfig:
    return load_config(args.config_dir, args.user, deployed_sha=deployed_git_sha())


def _guard(
    fn: Callable[[argparse.Namespace, TextIO, TextIO], int],
) -> Callable[[argparse.Namespace, TextIO, TextIO], int]:
    def run(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
        try:
            return fn(args, out, err)
        except ConfigError as exc:
            print(f"INVALID: {exc}", file=err)
            return EXIT_CONFIG_INVALID
        except (
            EodhdError,
            InstrumentError,
            DistributionError,
            OverrideError,
            SecretError,
            ValueError,
        ) as exc:
            print(f"FAILED: {exc}", file=err)
            return EXIT_FAILED

    return run


@_guard
def cmd_fetch(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    """``trader fetch --symbol S --from D --to D [--history]`` inside the call budget."""
    loaded = _load(args)
    now = utc_now()
    with market_session(args.user) as s:
        engine = s.get_bind()
        budget = CallBudget(engine, loaded.common.data.eodhd)  # type: ignore[arg-type]
        store = RawStore(_data_dir(), loaded.user.eodhd.licensee)
        client = EodhdClient(urllib_transport, budget, store, args.user, loaded.user.eodhd.licensee)
        res = fetch_by_hand(s, client, args.symbol, args.from_, args.to, now)
        if res.warnings:
            s.commit()
            for w in res.warnings:
                print(f"WARN {w}", file=err)
            return EXIT_FAILED
        if args.history:
            cal = AsxCalendar.from_session(s, VenueTimes.from_config(loaded.common.venue.XASX))
            sched = Schedule.from_config(loaded.common.schedule)
            role = "sleeve" if args.symbol in loaded.common.sleeves else "benchmark"
            inst = require_instrument(s, args.symbol)
            for d in sorted(latest_bars(s, inst.id, "eodhd", args.from_, args.to)):
                validate_symbol_day(s, args.symbol, d, now, cal, loaded.common.data, sched,
                                    SymbolContext(role=role, history=True))  # fmt: skip
        s.commit()
    print(f"OK {args.symbol}: {res.bars_stored} bars stored", file=out)
    return EXIT_OK


def _dec(text: str | None) -> Decimal | None:
    if text is None:
        return None
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"not a number: {text!r}") from exc


@_guard
def cmd_distribution(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    _load(args)
    with market_session(args.user) as s:
        row = enter_distribution(
            s, args.symbol, args.ex_date, DistributionStatus(args.status), utc_now(),
            amount=args.amount, franking=args.franking, record_date=args.record_date,
            pay_date=args.pay_date, period_end=args.period_end, note=args.source_note,
        )  # fmt: skip
        s.commit()
        print(f"OK distribution {args.symbol} ex {row.ex_date} {row.status}", file=out)
    return EXIT_OK


@_guard
def cmd_qc(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    loaded = _load(args)
    with market_session(args.user) as s:
        cal = AsxCalendar.from_session(s, VenueTimes.from_config(loaded.common.venue.XASX))
        row = qc_override(
            s, args.symbol, args.date, utc_now(), reason=args.reason, actor=args.user,
            use=args.use, price=args.price, cal=cal,
        )  # fmt: skip
        s.commit()
        print(f"OK override {args.symbol} {args.date}: close {row.close} ({row.source})", file=out)
    return EXIT_OK


def import_calendar(session: Session, path: Path, source: str, now: datetime) -> int:
    """CSV ``venue,date,is_trading,close_time`` (close_time HH:MM, empty when closed)."""
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            venue = row["venue"].strip() or XASX
            is_trading = row["is_trading"].strip().lower() in ("1", "true", "yes")
            ct: time | None = parse_hhmm(row["close_time"].strip()) if is_trading else None
            if is_trading and ct is None:
                raise ValueError(f"{row['date']}: a trading day needs a close_time")
            session.add(
                CalendarDay(
                    venue=venue,
                    date=date.fromisoformat(row["date"].strip()),
                    is_trading=is_trading,
                    close_time=ct,
                    source=source,
                    fetch_time=now,
                )
            )  # fmt: skip
            n += 1
    session.flush()
    write_market_audit(session, actor="user", action="import.calendar",
                       payload={"rows": n, "source": source, "file": path.name})  # fmt: skip
    return n


def import_spreads(session: Session, path: Path, source: str, now: datetime) -> int:
    """CSV ``symbol,month,spread`` (spread as a fraction, 0.0002 = 0.02%)."""
    n = 0
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            spread = _dec(row["spread"].strip())
            assert spread is not None
            enter_spread(session, row["symbol"].strip(), row["month"].strip(), spread, source, now)
            n += 1
    return n


@_guard
def cmd_import(args: argparse.Namespace, out: TextIO, err: TextIO) -> int:
    _load(args)
    with market_session(args.user) as s:
        fn = import_calendar if args.kind == "calendar" else import_spreads
        n = fn(s, args.file, args.source, utc_now())
        s.commit()
    print(f"OK imported {n} {args.kind} rows", file=out)
    return EXIT_OK
