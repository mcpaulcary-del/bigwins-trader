"""Demo data for the phone app (BF-D37, BF-D43): a short paper run of the real app on
synthetic prices (the mock gateway, the owner approving every batch by code), written
to a SQLite journal that the app then opens read-only. The run ends on a month-end
decision, so the demo shows a batch waiting for approval the next morning, and every
message the app sent is in the inbox. For screenshots and tests only; every screen says
DEMO, and the demo's actions are simulated (``demo_control``): nothing here touches a
broker, Telegram, Web Push, the server or a real journal.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import numpy as np

from trader.app_control import Control
from trader.app_notify import AppNotifier, classify
from trader.app_store import set_state
from trader.approval import ApprovalBot, FakeTransport, Markup, TotpVerifier
from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.lines.emg2 import Emg2_20Params
from trader.panel import PricePanel
from trader.secrets import SecretValue

DEMO_SEED = "JBSWY3DPEHPK3PXP"  # a public test seed (RFC 4648 example), demo only
DEMO_VERSION = {"version": "EMG2-18 C6 v1.0 (DEMO)", "id": "demo0000v100", "config": "demo",
                "code": "demo", "commit": "demo"}  # fmt: skip


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
    prices: Callable[[str], list[tuple[date, float]]] | None = None  # BF-D66 (synthetic)
    now: datetime = datetime(2024, 1, 1, tzinfo=ASX_TZ)  # the demo's "now": the morning after


class _InboxTransport(FakeTransport):
    """The demo's transport: as FakeTransport, and every message also goes to the inbox
    (as the phone app would get it)."""

    def __init__(self) -> None:
        super().__init__()
        self.notifier: AppNotifier | None = None

    def send(self, chat_id: int, text: str) -> None:
        super().send(chat_id, text)
        if self.notifier is not None:
            self.notifier.notify(text)

    def send_markup(self, chat_id: int, text: str, markup: Markup) -> int | None:
        n = super().send_markup(chat_id, text, markup)
        if self.notifier is not None:
            self.notifier.notify(text, "approval" if classify(text) != "page" else "page",
                                 "/orders")  # fmt: skip
        return n


def build_demo(path: Path, days: int = 45, random_twins: int = 20) -> Demo:
    """Run the app for about ``days`` sessions from a start decision, ending on a
    month-end decision, and keep the journal."""
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
    tr = _InboxTransport()
    app = BfApp(
        s, j, broker, sim, tr, TotpVerifier(SecretValue(DEMO_SEED)),
        panel.dates, panels, closes,
    )  # fmt: skip
    tr.notifier = AppNotifier(j, None, clock=lambda: app.now)
    app.strategy = dict(DEMO_VERSION)  # BF-D45: every decision is stamped
    run = list(panel.dates[270 : 270 + days])
    ends = [i for i, (a, b) in enumerate(pairwise(run)) if a.month not in (b.month, start.month)]
    if ends:  # end on a month-end decision: its batch waits for approval the next morning
        run = run[: ends[-1] + 1]
    dry_run(app, run, {}, owner_approves_all(app, DEMO_SEED), mock_auction(gw, closes))
    nxt = panel.dates[panel.dates.index(run[-1]) + 1]
    now = datetime.combine(nxt, time(10, 40), ASX_TZ)
    set_state(j, "heartbeat", {"ok": True, "error": "", "every_s": 300}, now - timedelta(minutes=2))
    set_state(j, "host-status", {
        "load1": 0.18, "cpus": 2, "mem_used_pct": 41, "disk_used_pct": 37,
        "uptime_s": 9 * 86400 + 3600, "tailscale": "connected (DEMO)",
        "code_version": "demo build", "asx": "open (DEMO)", "onedrive": True,
        "containers": [{"name": n, "state": "Up 9 days (DEMO)"}
                       for n in ("trader", "dashboard", "db", "gw-paper")],
        "log": ["DEMO log: scheduler idle, next job 14:30 remind",
                "DEMO log: decision batch planned, waiting for approval"],
    }, now - timedelta(seconds=40))  # fmt: skip
    set_state(j, "strategy-running", dict(DEMO_VERSION), now - timedelta(days=1))
    from trader.backups import record_result

    for k in range(3, 0, -1):  # BF-D64: a few nights of (DEMO) backups and a restore test
        local = {"archive": "bigwins-demo.tar.age", "size": 48_000_000 + k * 1_200_000,
                 "files": 1840}  # fmt: skip
        record_result(j, {"ok": True, "kind": "backup", "at": "demo", "local": local,
                          "remote": {"ok": True}, "onedrive": True},
                      now - timedelta(days=k, hours=-13))  # fmt: skip
    record_result(j, {"ok": True, "kind": "restore_test", "files": 1840, "ledger_files": 3,
                      "journal_dump": True}, now - timedelta(hours=10))  # fmt: skip
    set_state(j, "update-available", {
        "ahead": 2, "head": "a" * 40, "remote": "b" * 40, "previous": "c" * 40, "strategy": True,
        "reasons": ["strategy setting: live_emg2_20"], "files": ["config/bfast.yaml"],
        "subject": "DEMO: keep zone 45% (example)",
        "notes": {"version": "EMG2-18 C6 v1.1 (DEMO)", "what": "Keep zone widened from the top "
                  "40% to the top 45% of band C (an example, DEMO).", "why": "Fewer sells of "
                  "names that are still strong (example).", "tested": "Full test suite and the "
                  "record replay (example).", "takes_effect": "Tonight's out-of-cycle decision "
                  "(immediate mode), orders for your approval."},
    }, now - timedelta(minutes=5))  # fmt: skip
    j.engine.dispose()
    k0 = panel.dates.index(run[0])
    mean = np.nanmean(panel.close / panel.close[k0], axis=1)  # an equal-weight demo index
    lvl = [(d, float(x)) for d, x in zip(panel.dates, mean, strict=True)]
    col = {c: k for k, c in enumerate(panel.entities)}

    def prices(code: str) -> list[tuple[date, float]]:
        k = col.get(code)
        if k is None:
            return []
        return [(d, float(c)) for d, c in zip(panel.dates[: panel.dates.index(nxt) + 1],
                                               panel.close[:, k], strict=False)
                if np.isfinite(c) and c > 0]  # fmt: skip

    return Demo(path, panel.dates, run[-1], lambda: lvl, prices, now)


def demo_control(j: Journal, demo: Demo) -> Control:
    """The demo's action screens: the real confirm screens on the demo journal (read
    only), every action simulated and labelled DEMO; nothing is written."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from trader.app_notify import b64url

    bot = ApprovalBot(j, FakeTransport(), TotpVerifier(SecretValue(DEMO_SEED)), frozenset(),
                      allowed_logins=frozenset({"demo"}))  # fmt: skip
    key = (
        ec.generate_private_key(ec.SECP256R1())
        .public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    )
    return Control(j, bot, frozenset({"demo"}), clock=lambda: demo.now, demo=True,
                   vapid_public=b64url(key), market_open=lambda now: False,
                   sessions=lambda: demo.sessions)  # fmt: skip
