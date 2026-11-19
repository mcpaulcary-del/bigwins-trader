"""Dry-run harness on recorded data (BF3/BF4 acceptance rehearsal). PAPER ONLY.

Replays the record's EODHD forward store end to end against the mock IB gateway:
decisions (start with canary, regular), per-order approval by a simulated owner over
the Telegram interface (TOTP codes), the breaker at plan and send time, the closing
auction at each session's recorded close, fills, carried orders, reconciliation to the
cent, the simulated twin and the daily report. Nothing leaves the process; no broker is
reached. ``store_providers`` is shared with ``trader-bf run``.
"""

from __future__ import annotations

import base64
import secrets
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import numpy as np

from trader.approval import FakeTransport, TotpVerifier
from trader.bf_app import (
    AppSettings,
    BfApp,
    CloseProvider,
    DryRunSummary,
    PanelProvider,
    data_ready,
    dry_run,
    marks_from_panels,
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


def settings_from(
    cfg: BfastConfig, chats: frozenset[int], start: date | None, lic_note: str = ""
) -> AppSettings:
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
        lic_note=lic_note,
    )


def store_providers(
    cfg: BfastConfig,
    store: Path,
    sessions: Sequence[date],
    refresh_seconds: float | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[PanelProvider, CloseProvider, CloseProvider, str]:
    """Panels, the day's closes and valuation marks from the forward store, and the LIC
    list note. Panels are cached per day; with ``refresh_seconds`` (the live runner) a
    cached panel is rebuilt after that long, so data that arrives late is seen. The
    day's closes are empty until the day's data is in (``data_ready``)."""
    etp: frozenset[str] = frozenset()
    if cfg.data.etp_list.is_file():
        etp = frozenset(x.strip() for x in cfg.data.etp_list.read_text().splitlines() if x.strip())
    lic = lic_codes(cfg)
    fs = ForwardStore(store)
    cache: dict[date, tuple[float, PricePanel]] = {}

    def panel(d: date) -> PricePanel:
        hit = cache.get(d)
        if hit is None or (refresh_seconds is not None and clock() - hit[0] > refresh_seconds):
            p = fs.build_panel(
                d, sessions, history=cfg.data.history_sessions, etp_codes=etp, lic_codes=lic.codes
            )
            cache[d] = hit = (clock(), p)
        return hit[1]

    def closes(d: date) -> dict[str, Decimal]:
        p = panel(d)
        if not data_ready(p):
            return {}
        return {
            e: Decimal(repr(float(c)))
            for e, c in zip(p.entities, p.close[-1], strict=True)
            if not np.isnan(c)
        }

    return panel, closes, marks_from_panels(panel), lic.describe()


def forward_store_dry_run(
    cfg: BfastConfig,
    store: Path,
    sessions: Sequence[date],
    days: Sequence[date],
    decisions: Mapping[date, str],
    journal_path: str = ":memory:",
) -> tuple[DryRunSummary, BfApp, FakeTransport]:
    panel, closes, marks, note = store_providers(cfg, store, sessions)
    seed = base64.b32encode(secrets.token_bytes(10)).decode()  # the simulated owner's authenticator
    chat = 1
    gw = MockGateway(accounts=("DU0000001",), cash=float(cfg.live_emg2_20.capital_cap_aud))
    broker = IbkrPaperBroker(
        IbkrSettings(cfg.broker.host, cfg.broker.port, cfg.broker.client_id, "DU0000001"),
        ib_factory=lambda: gw,
    )
    broker.connect()
    j = Journal.sqlite(journal_path)
    start = min((d for d, k in decisions.items() if k == "S"), default=None)
    s = settings_from(cfg, frozenset({chat}), start, note)
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", s.capital_aud, "dry-run deposit")
    sim = SimBroker(cash=s.capital_aud, half_spread=s.sim_half_spread)
    tr = FakeTransport()
    app = BfApp(
        s, j, broker, sim, tr, TotpVerifier(SecretValue(seed)), sessions, panel, closes, marks
    )
    summ = dry_run(app, days, decisions, owner_approves_all(app, seed), mock_auction(gw, closes))
    return summ, app, tr
