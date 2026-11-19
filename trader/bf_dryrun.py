"""Dry-run harness on recorded data (BF3/BF4 acceptance rehearsal). PAPER ONLY.

Replays the record's EODHD forward store end to end against the mock IB gateway:
decisions (start with canary, regular), per-order approval by a simulated owner over
the Telegram interface (TOTP codes), the breaker at plan and send time, the closing
auction at each session's recorded close, fills, reconciliation to the cent, the
simulated twin and the daily report. Nothing leaves the process; no broker is reached.
"""

from __future__ import annotations

import base64
import secrets
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from functools import cache
from pathlib import Path

import numpy as np

from trader.approval import FakeTransport, TotpVerifier
from trader.bf_app import (
    AppSettings,
    BfApp,
    DryRunSummary,
    dry_run,
    mock_auction,
    owner_approves_all,
)
from trader.bfast_config import BfastConfig, lic_codes
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.data.forward_store import ForwardStore
from trader.journal import Journal
from trader.panel import PricePanel
from trader.secrets import SecretValue


def settings_from(cfg: BfastConfig, chats: frozenset[int], start: date | None) -> AppSettings:
    return AppSettings(
        book=cfg.book,
        sim_book=cfg.data.sim_book,
        line=cfg.line,
        capital_aud=cfg.live_emg2_20.capital_cap_aud,
        params=cfg.emg2_20_params(),
        order_params=cfg.order_params(),
        limits=cfg.risk_limits(),
        approval_mode=cfg.execution.approval_mode,
        approval_deadline=cfg.execution.approval_deadline,
        buy_funds_wait_sessions=cfg.execution.buy_funds_wait_sessions,
        sim_half_spread=cfg.data.sim_half_spread,
        chats=chats,
        start_date=start,
    )


def forward_store_dry_run(
    cfg: BfastConfig,
    store: Path,
    sessions: Sequence[date],
    days: Sequence[date],
    decisions: Mapping[date, str],
    journal_path: str = ":memory:",
) -> tuple[DryRunSummary, BfApp, FakeTransport]:
    etp: frozenset[str] = frozenset()
    if cfg.data.etp_list.is_file():
        etp = frozenset(x.strip() for x in cfg.data.etp_list.read_text().splitlines() if x.strip())
    lic, _ = lic_codes(cfg)
    fs = ForwardStore(store)

    @cache
    def panel(d: date) -> PricePanel:
        return fs.build_panel(
            d, sessions, history=cfg.data.history_sessions, etp_codes=etp, lic_codes=lic
        )

    last = panel(days[-1])

    def closes(d: date) -> dict[str, Decimal]:
        k = last.dates.index(d)
        return {
            e: Decimal(repr(float(c)))
            for e, c in zip(last.entities, last.close[k], strict=True)
            if not np.isnan(c)
        }

    seed = base64.b32encode(secrets.token_bytes(10)).decode()  # the simulated owner's authenticator
    chat = 1
    gw = MockGateway(accounts=("DU0000001",), cash=float(cfg.live_emg2_20.capital_cap_aud))
    broker = IbkrPaperBroker(
        IbkrSettings(cfg.broker.host, cfg.broker.port, cfg.broker.client_id, "DU0000001"),
        ib_factory=lambda: gw,
    )
    broker.connect()
    j = Journal.sqlite(journal_path)
    s = settings_from(cfg, frozenset({chat}), None)
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", s.capital_aud, "dry-run deposit")
    sim = SimBroker(cash=s.capital_aud, half_spread=s.sim_half_spread)
    tr = FakeTransport()
    app = BfApp(s, j, broker, sim, tr, TotpVerifier(SecretValue(seed)), sessions, panel, closes)
    summ = dry_run(app, days, decisions, owner_approves_all(app, seed), mock_auction(gw, closes))
    return summ, app, tr
