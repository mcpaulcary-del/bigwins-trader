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
from dataclasses import replace
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
from trader.bfast_config import BfastConfig, LicListError, corporate_actions_csv, lic_codes
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.ca_book import CaSource, calendar_source
from trader.data.forward_store import ForwardStore
from trader.journal import Journal
from trader.lines.emg2 import SellRule
from trader.panel import PricePanel
from trader.secrets import SecretValue


def settings_from(
    cfg: BfastConfig,
    chats: frozenset[int],
    start: date | None,
    lic_note: str = "",
    random_twins: int | None = None,
    band_trend: bool | None = None,
    sell_rule: SellRule | None = None,
) -> AppSettings:
    """``random_twins`` overrides the configured count, ``band_trend`` switches the L15
    band-trend switch on or off (BF-D28) and ``sell_rule`` replaces the configured sell
    rule (BF-D35): tests and short replays only."""
    bt = cfg.band_trend_params()
    if band_trend is not None:
        bt = replace(bt, enabled=band_trend)
    params = cfg.emg2_20_params()
    if sell_rule is not None:
        params = replace(params, sell_rule=sell_rule)
    return AppSettings(
        book=cfg.book,
        sim_book=cfg.data.sim_book,
        line=cfg.line,
        capital_aud=cfg.live_emg2_20.capital_cap_aud,
        params=params,
        order_params=cfg.order_params(),
        limits=cfg.risk_limits(),
        approval_mode=cfg.execution.approval_mode,
        approval_deadline=cfg.execution.approval_deadline,
        buy_funds_wait_sessions=cfg.execution.buy_funds_wait_sessions,
        sim_half_spread=cfg.data.sim_half_spread,
        chats=chats,
        start_date=start,
        lic_note=lic_note,
        random_twins=cfg.data.random_twins if random_twins is None else random_twins,
        random_prefix=cfg.data.random_prefix,
        random_seed_base=cfg.data.random_seed_base,
        band_trend=bt,
        forced_states=(
            tuple(sorted(cfg.paper_dry_run.decisions.items())) if cfg.paper_dry_run else ()
        ),
        dry_run_until=cfg.paper_dry_run.until if cfg.paper_dry_run else None,
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
    try:
        note = lic_codes(cfg).describe()
    except LicListError as e:  # BF-D21: the app starts, pages and refuses to decide
        note = f"LIC list REFUSED (BF-D21): {e}"
    fs = ForwardStore(store)
    bt = cfg.band_trend_params()
    protect = frozenset({bt.fund}) if bt.enabled else frozenset()  # BF-D28: A200 stays priceable
    cache: dict[date, tuple[float, PricePanel, str]] = {}
    bulk_dir = Path(store) / "raw" / "bulk_eod"

    def version() -> str:  # BF-D31: a new bulk file (the daily refresh) rebuilds the panel
        return max((p.name for p in bulk_dir.glob("AU_*.json.gz")), default="")

    def panel(d: date) -> PricePanel:
        hit = cache.get(d)
        v = version()
        if (
            hit is None
            or hit[2] != v
            or (refresh_seconds is not None and clock() - hit[0] > refresh_seconds)
        ):
            lic = lic_codes(cfg)  # BF-D21: re-checked on every build; raises, never falls back
            p = fs.build_panel(
                d, sessions, history=cfg.data.history_sessions, etp_codes=etp,
                lic_codes=lic.codes, protect=protect,
            )  # fmt: skip
            cache[d] = hit = (clock(), p, v)
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

    return panel, closes, marks_from_panels(panel), note


Providers = tuple[PanelProvider, CloseProvider, CloseProvider, str]


def ca_source_from(cfg: BfastConfig, store: Path) -> CaSource:
    """BF-D23: the corporate-action calendar: the forward store's vendor dividends (and,
    BF-D26, splits / consolidations) of the held codes, corrected by the record's
    CORPORATE_ACTIONS.csv."""
    fs = ForwardStore(store)
    return calendar_source(fs.dividend_rows, corporate_actions_csv(cfg), fs.split_rows)


def mock_app(
    cfg: BfastConfig,
    providers: Providers,
    sessions: Sequence[date],
    start: date | None,
    journal_path: str = ":memory:",
    gw: MockGateway | None = None,
    seed: str | None = None,
    random_twins: int | None = None,
    ca_source: CaSource | None = None,
    band_trend: bool | None = None,
    sell_rule: SellRule | None = None,
) -> tuple[BfApp, MockGateway, str]:
    """A ``BfApp`` on the mock gateway with a simulated owner's authenticator. Passing
    the same ``gw``, ``journal_path`` and ``seed`` again is a restart: the new app has
    only what the journal and the broker hold (nothing in memory carries over)."""
    panel, closes, marks, note = providers
    seed = seed or base64.b32encode(secrets.token_bytes(10)).decode()
    chat = 1
    fresh = gw is None
    gw = gw or MockGateway(accounts=("DU0000001",), cash=float(cfg.live_emg2_20.capital_cap_aud))
    broker = IbkrPaperBroker(
        IbkrSettings(cfg.broker.host, cfg.broker.port, cfg.broker.client_id, "DU0000001"),
        ib_factory=lambda: gw,
    )
    broker.connect()
    j = Journal.sqlite(journal_path)
    s = settings_from(cfg, frozenset({chat}), start, note, random_twins, band_trend, sell_rule)
    sim = SimBroker(cash=s.capital_aud, half_spread=s.sim_half_spread)
    if fresh:
        for book in (s.book, s.sim_book):
            j.add_cash(book, "DEPOSIT", s.capital_aud, "dry-run deposit")
    else:  # restart: the twin's simulated broker is rebuilt from the journal
        sim = SimBroker.from_journal(j, s.sim_book, s.sim_half_spread)
    app = BfApp(
        s, j, broker, sim, FakeTransport(), TotpVerifier(SecretValue(seed)), sessions, panel,
        closes, marks, lic_guard=lambda: lic_codes(cfg), ca_source=ca_source,
    )  # fmt: skip
    return app, gw, seed


def forward_store_dry_run(
    cfg: BfastConfig,
    store: Path,
    sessions: Sequence[date],
    days: Sequence[date],
    decisions: Mapping[date, str],
    journal_path: str = ":memory:",
    providers: Providers | None = None,
    random_twins: int | None = None,
    band_trend: bool | None = None,
    sell_rule: SellRule | None = None,
) -> tuple[DryRunSummary, BfApp, FakeTransport]:
    providers = providers or store_providers(cfg, store, sessions)
    start = min((d for d, k in decisions.items() if k == "S"), default=None)
    app, gw, seed = mock_app(
        cfg, providers, sessions, start, journal_path, random_twins=random_twins,
        ca_source=ca_source_from(cfg, store), band_trend=band_trend, sell_rule=sell_rule,
    )  # fmt: skip
    tr = app.transport
    assert isinstance(tr, FakeTransport)
    summ = dry_run(
        app, days, decisions, owner_approves_all(app, seed), mock_auction(gw, providers[1])
    )
    return summ, app, tr
