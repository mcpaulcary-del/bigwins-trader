"""Demo data for the phone dashboard (BF-D37): a short paper run of the real app on
synthetic prices (the mock gateway, the owner approving every batch by code), written
to a SQLite journal that the dashboard then opens read-only. For screenshots and
tests only; the page says DEMO. Nothing here touches a broker, Telegram or the server.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np

from trader.approval import FakeTransport, TotpVerifier
from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.journal import Journal
from trader.lines.emg2 import Emg2_20Params
from trader.panel import PricePanel
from trader.secrets import SecretValue

DEMO_SEED = "JBSWY3DPEHPK3PXP"  # a public test seed (RFC 4648 example), demo only


def _sessions(n: int, start: date = date(2023, 1, 2)) -> tuple[date, ...]:
    out: list[date] = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return tuple(out)


def synthetic_panel(n_rows: int = 330, n_ent: int = 800, seed: int = 7) -> PricePanel:
    """Random-walk prices and traded values (the same recipe as the app's tests)."""
    rng = np.random.default_rng(seed)
    drift = rng.normal(0.0003, 0.001, n_ent)
    vol = rng.uniform(0.01, 0.05, n_ent)
    r = rng.normal(drift, vol, (n_rows, n_ent))
    close = np.round(2.0 * np.exp(np.cumsum(r, axis=0)) * rng.uniform(0.2, 5.0, n_ent), 3)
    tv = np.exp(rng.normal(13.0, 1.6, n_ent)) * np.exp(rng.normal(0, 0.5, (n_rows, n_ent))) * 50
    ret = np.full_like(close, np.nan)
    ret[1:] = close[1:] / close[:-1] - 1
    ents = tuple(f"S{j:03d}" for j in range(n_ent))
    dts = _sessions(n_rows)
    return PricePanel(
        as_of=dts[-1], dates=dts, entities=ents, close=close, ret=ret, tv=tv,
        sec_class=dict.fromkeys(ents, "ORD"),
    )  # fmt: skip


@dataclass(frozen=True)
class Demo:
    journal_path: Path
    sessions: tuple[date, ...]
    last_day: date
    index: Callable[[], list[tuple[date, float]]]


def build_demo(path: Path, days: int = 45, random_twins: int = 20) -> Demo:
    """Run the app for ``days`` sessions from a start decision and keep the journal."""
    panel = synthetic_panel()
    path.unlink(missing_ok=True)

    def closes(day: date) -> dict[str, Decimal]:
        k = panel.dates.index(day)
        return {
            e: Decimal(repr(float(c)))
            for e, c in zip(panel.entities, panel.close[k], strict=True)
            if not np.isnan(c)
        }

    def panels(day: date) -> PricePanel:
        return panel.truncate(day)

    gw = MockGateway(cash=10000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    j = Journal.sqlite(str(path))
    start = panel.dates[270]
    s = AppSettings(
        chats=frozenset({1}), start_date=start, params=Emg2_20Params(skip_lottery=False),
        random_twins=random_twins,
    )  # fmt: skip
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", Decimal(10000), "demo paper deposit")
    sim = SimBroker(cash=Decimal(10000), half_spread=s.sim_half_spread)
    app = BfApp(
        s, j, broker, sim, FakeTransport(), TotpVerifier(SecretValue(DEMO_SEED)),
        panel.dates, panels, closes,
    )  # fmt: skip
    run = list(panel.dates[270 : 270 + days])
    dry_run(app, run, {}, owner_approves_all(app, DEMO_SEED), mock_auction(gw, closes))
    j.engine.dispose()
    k0 = panel.dates.index(run[0])
    mean = np.nanmean(panel.close / panel.close[k0], axis=1)  # an equal-weight demo index
    lvl = [(d, float(x)) for d, x in zip(panel.dates, mean, strict=True)]
    return Demo(path, panel.dates, run[-1], lambda: lvl)
