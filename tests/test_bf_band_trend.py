"""BF-D28: rule L15, the band-trend switch of the EMG2-18 book (AMENDMENT_live_EMG2_18_BT.md,
rules BT1-BT4 of AMENDMENT_shadow_EMG2_18_BT.md). Paper only."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest

from tests.bf_support import asx_sessions, real_config, synthetic_panel
from trader.approval import FakeTransport, TotpVerifier
from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.journal import Journal, Status
from trader.lines import band_trend as bt_mod
from trader.lines.band_trend import BandTrend, BandTrendParams, band_trend, month_end_rows
from trader.lines.emg2 import (
    BT_FUND_BUY,
    BT_FUND_SELL,
    BT_OFF_SELL,
    BookState,
    Emg2_20Params,
    decide_emg2_18_bt,
    decide_emg2_20,
    emg2_list,
)
from trader.orders import build_orders
from trader.panel import PricePanel
from trader.report import PAPER_BANNER
from trader.risk import RiskContext, RiskLimits, SafetyLevel, Verdict, check_intents
from trader.secrets import SecretValue

FUND = "A200"
SEED = "JBSWY3DPEHPK3PXP"
CHAT = 77
BT = BandTrendParams(enabled=True)


def _with_fund(p: PricePanel, factor: np.ndarray | None = None) -> PricePanel:
    """The panel with every share scaled by ``factor`` (one value a row: a common move of
    the whole market) and an ASX 200 fund column ``A200`` (class FUND, very liquid)."""
    t = p.n_sessions
    f = np.ones(t) if factor is None else factor
    close = p.close * f[:, None]
    ret = np.full_like(close, np.nan)
    ret[1:] = close[1:] / close[:-1] - 1
    fund = 100.0 * np.exp(np.cumsum(np.full(t, 0.0003)))
    fret = np.r_[np.nan, fund[1:] / fund[:-1] - 1]
    cls = dict(p.sec_class)
    cls[FUND] = "FUND"
    return PricePanel(
        as_of=p.as_of, dates=p.dates, entities=(*p.entities, FUND),
        close=np.column_stack([close, fund]), ret=np.column_stack([ret, fret]),
        tv=np.column_stack([p.tv * 50, np.full(t, 2e7)]), sec_class=cls,
    )  # fmt: skip


def _fall(t: int, last: int, depth: float) -> np.ndarray:
    """A common fall of ``depth`` over the last ``last`` rows."""
    f = np.ones(t)
    f[t - last :] = np.linspace(1.0, 1.0 - depth, last)
    return f


BASE = synthetic_panel(n_rows=520, n_ent=800, seed=11)


# ------------------------------------------------------------------ BT1 / BT2


def test_BF_D28_month_end_rows_are_the_last_session_of_each_month() -> None:
    p = BASE
    rows = month_end_rows(p.dates, 10)
    assert len(rows) == 10 and rows[-1] == p.n_sessions - 1
    for r in rows[:-1]:
        assert p.dates[r + 1].month != p.dates[r].month


def test_BF_D28_band_index_falls_below_its_10_month_average_state_fund() -> None:
    """A common fall of the market in the last two months -> FUND; the same data without
    it, rising -> EMG2. The index is the equal-weight band-C total return (BT1)."""
    t = BASE.n_sessions
    down = band_trend(_with_fund(BASE, _fall(t, 40, 0.30)), BT)
    up = band_trend(_with_fund(BASE, 1 / _fall(t, 40, 0.30)), BT)
    assert down.state == "FUND" and down.level < down.mean and not down.on
    assert up.state == "EMG2" and up.level >= up.mean and up.on
    assert len(down.levels) == 10 and down.levels[0][1] == 1.0
    assert all(n > 0 for _, _, n in down.levels)  # band C formed at every month-end
    assert down.digest == band_trend(_with_fund(BASE, _fall(t, 40, 0.30)), BT).digest
    assert "state: FUND" in down.describe() and "below" in down.describe()


def test_BF_D28_band_index_equals_a_direct_equal_weight_computation() -> None:
    p = _with_fund(BASE, _fall(BASE.n_sessions, 40, 0.30))
    bt = band_trend(p, BT)
    rows = month_end_rows(p.dates, 10)
    lg = np.cumsum(np.log1p(np.nan_to_num(p.ret)), axis=0)
    lev = [1.0]
    for m, m1 in pairwise(rows):
        c = [p.entities.index(r.entity) for r in emg2_list(p.truncate(p.dates[m])).band_c]
        lev.append(lev[-1] * float(np.mean(np.exp(lg[m1, c] - lg[m, c]))))
    assert [round(v, 12) for _, v, _ in bt.levels] == [round(v, 12) for v in lev]
    assert bt.mean == pytest.approx(float(np.mean(lev)))


def test_BF_D28_fewer_than_10_levels_is_on() -> None:
    short = synthetic_panel(n_rows=170, n_ent=300, seed=3)  # about 8 months of sessions
    bt = band_trend(_with_fund(short, _fall(170, 40, 0.5)), BT)
    assert len(bt.levels) < 10 and bt.state == "EMG2"


def test_BF_D28_fund_is_left_out_of_band_c() -> None:
    p = _with_fund(BASE)
    lst = emg2_list(p)
    assert FUND not in {r.entity for r in lst.band_c} and FUND not in lst.targets


# ------------------------------------------------------------------ BT3 / BT4 decisions

P18 = Emg2_20Params(skip_lottery=False)


def _px(p: PricePanel, e: str) -> Decimal:
    return Decimal(repr(float(p.close[-1, p.entities.index(e)])))


def test_BF_D28_off_sells_every_share_and_buys_the_fund_once() -> None:
    p = _with_fund(BASE)
    on = decide_emg2_20(p, BookState("B", Decimal(10000)), P18)
    held = {b.entity: int((b.value_aud / b.ref_close).to_integral_value()) for b in on.buys}
    book = BookState("B", Decimal(150), held)
    off = decide_emg2_18_bt(p, book, P18, trend_on=False, fund=FUND)
    assert off.state == "FUND" and off.payload()["state"] == "FUND"
    assert {s.entity for s in off.sells} == set(held) and {s.reason for s in off.sells} == {
        BT_OFF_SELL
    }
    assert [(b.entity, b.reason) for b in off.buys] == [(FUND, BT_FUND_BUY)]
    est = sum((s.ref_close * s.qty for s in off.sells), Decimal(0))
    assert Decimal(9000) < off.buys[0].value_aud <= min(est + 100, Decimal(9950))
    # orders: one fund order, flagged FUND, sized at its limit; the shares are sold
    batch = build_orders(off, line="EMG2_18", kind="B")
    fund_orders = [i for i in batch.intents if i.entity == FUND]
    assert len(fund_orders) == 1 and fund_orders[0].flags == ("FUND",)
    assert len(batch.intents) == len(held) + 1
    assert batch.batch_id.endswith("-B")


def test_BF_D28_off_with_the_fund_held_tops_up_only_above_10_percent() -> None:
    p = _with_fund(BASE)
    px = _px(p, FUND)
    q = int(Decimal(9000) / px)
    small = decide_emg2_18_bt(
        p, BookState("B", Decimal(600), {FUND: q}), P18, trend_on=False, fund=FUND
    )
    assert not small.buys and not small.sells and small.kept == (FUND,)
    q8 = int(Decimal(8000) / px)
    big = decide_emg2_18_bt(
        p, BookState("B", Decimal(2000), {FUND: q8}), P18, trend_on=False, fund=FUND
    )
    assert [b.entity for b in big.buys] == [FUND]
    assert big.buys[0].value_aud <= Decimal(10000) - px * q8  # L1: never above the cap
    capped = decide_emg2_18_bt(
        p, BookState("B", Decimal(1500), {FUND: q}), P18, trend_on=False, fund=FUND
    )
    assert not capped.buys  # room under the cap (A$1,000) is under 10% of the account
    tiny = decide_emg2_18_bt(p, BookState("B", Decimal(400)), P18, trend_on=False, fund=FUND)
    assert not tiny.buys and [s.reason for s in tiny.skipped] == ["MIN_PARCEL"]


def test_BF_D28_on_sells_the_fund_and_runs_the_registered_rules() -> None:
    p = _with_fund(BASE)
    q = int(Decimal(9900) / _px(p, FUND))
    book = BookState("B", Decimal(10000) - _px(p, FUND) * q, {FUND: q})
    on = decide_emg2_18_bt(p, book, P18, trend_on=True, fund=FUND)
    assert on.state == "EMG2"
    assert [(s.entity, s.reason) for s in on.sells] == [(FUND, BT_FUND_SELL)]
    assert len(on.buys) == 18 and FUND not in {b.entity for b in on.buys}
    # the same as the registered decision apart from the relabelled fund sale
    reg = decide_emg2_20(p, book, P18)
    assert [b.entity for b in on.buys] == [b.entity for b in reg.buys]
    # without the switch the decision's payload (and digest) is unchanged
    assert "state" not in reg.payload()


def test_BF_D28_data_block_is_no_decision_in_either_state() -> None:
    p = _with_fund(synthetic_panel(n_rows=300, n_ent=200, seed=5))  # band C < 150: rule 14
    for on in (True, False):
        d = decide_emg2_18_bt(p, BookState("B", Decimal(10000)), P18, trend_on=on, fund=FUND)
        assert d.data_block and not d.buys and not d.sells


# ------------------------------------------------------------------ L10 for the fund order


def _ctx(cash: Decimal, start: bool = True) -> RiskContext:
    from datetime import UTC, datetime

    d = BASE.as_of
    return RiskContext(
        now=datetime(2025, 1, 1, tzinfo=UTC), session=d, expected_data_date=d, data_as_of=d,
        safety=SafetyLevel.NORMAL, start_day=start, positions={}, settled_cash=cash,
    )  # fmt: skip


def test_BF_D28_fund_order_has_its_own_limit_and_is_paged_share_buys_keep_800() -> None:
    p = _with_fund(BASE)
    off = decide_emg2_18_bt(p, BookState("B", Decimal(10000)), P18, trend_on=False, fund=FUND)
    tv = {FUND: Decimal(20000000)}
    batch = build_orders(off, line="EMG2_18", kind="S", tv_med20=tv)
    rep = check_intents(batch.intents, _ctx(Decimal(10000)), RiskLimits())
    assert [r.verdict for r in rep.results] == [Verdict.PASS]
    assert "FUND_ABOVE_ORDER_LIMIT" in rep.results[0].reasons
    assert any("fund buy A200" in x for x in rep.pages)
    low = check_intents(
        batch.intents, _ctx(Decimal(10000)), RiskLimits(fund_order_max_aud=Decimal(5000))
    )
    assert low.results[0].reasons == ("MAX_ORDER_VALUE",)
    # a share buy above A$800 is still rejected (L10 unchanged)
    from dataclasses import replace

    share = replace(batch.intents[0], entity="S001", flags=())
    r2 = check_intents([share], _ctx(Decimal(10000)), RiskLimits())
    assert r2.results[0].reasons == ("MAX_ORDER_VALUE",)


# ------------------------------------------------------------------ app replay: the switch flips

APP_PANEL = _with_fund(synthetic_panel(n_rows=330, n_ent=800, seed=7))


def _closes(day: date) -> dict[str, Decimal]:
    k = APP_PANEL.dates.index(day)
    return {e: Decimal(repr(round(float(c), 3))) for e, c in zip(APP_PANEL.entities, APP_PANEL.close[k], strict=True)
            if not np.isnan(c)}  # fmt: skip


def _panel(day: date) -> PricePanel:
    p = APP_PANEL.truncate(day)
    return PricePanel(as_of=p.as_of, dates=p.dates, entities=p.entities, close=np.round(p.close, 3),
                      ret=p.ret, tv=p.tv, sec_class=p.sec_class)  # fmt: skip


def _scripted(states: dict[date, str]) -> Callable[..., BandTrend]:
    """The switch's state by decision day (the computation itself is tested above)."""

    def f(panel: PricePanel, params: BandTrendParams | None = None) -> BandTrend:
        s = states[panel.as_of]
        return BandTrend(panel.as_of.isoformat(), s, 0.9 if s == "FUND" else 1.1, 1.0,  # type: ignore[arg-type]
                         ((panel.as_of.isoformat(), 1.0, 200),))  # fmt: skip

    return f


def _app(start: date, rnd: int = 3) -> tuple[BfApp, MockGateway, FakeTransport]:
    gw = MockGateway(cash=10000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    j = Journal.sqlite()
    s = AppSettings(chats=frozenset({CHAT}), start_date=start, params=P18, random_twins=rnd,
                    band_trend=BT)  # fmt: skip
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", Decimal(10000), "paper deposit")
    sim = SimBroker(cash=Decimal(10000), half_spread=s.sim_half_spread)
    tr = FakeTransport()
    app = BfApp(
        s, j, broker, sim, tr, TotpVerifier(SecretValue(SEED)), APP_PANEL.dates, _panel, _closes
    )
    return app, gw, tr


D0 = APP_PANEL.dates[270]
DAYS = list(APP_PANEL.dates[270:310])  # two month-ends after the start


def _month_ends() -> tuple[date, date]:
    m1, m2 = (
        d for d in DAYS[:-1] if APP_PANEL.dates[APP_PANEL.dates.index(d) + 1].month != d.month
    )
    return m1, m2


def _reports(tr: FakeTransport) -> list[str]:
    return [t for _, t in tr.outbox if t.startswith(PAPER_BANNER)]


def test_BF_D28_replay_start_in_fund_then_switch_to_emg2(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start FUND (the canary is the one fund order), the month-end of the start month
    FUND (no top-up: cash < 10%), the next month-end EMG2: the fund is sold and the
    EMG2-18 picks are bought, in the broker book (owner approval per order), the
    simulated twin and every random twin; reconciled to the cent every session."""
    m1, m2 = _month_ends()
    monkeypatch.setattr("trader.bf_app.band_trend", _scripted({D0: "FUND", m1: "FUND", m2: "EMG2"}))
    app, gw, tr = _app(D0)
    summ = dry_run(app, DAYS, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    can = app.j.intents_of(f"EMG2_18_PAPER-{D0}-C")
    assert [(it.entity, it.flags, st) for it, st in can] == [
        (FUND, ("CANARY", "FUND"), Status.FILLED)
    ]
    assert app.j.batch(f"EMG2_18_PAPER-{D0}-S") is None  # nothing else to start
    sim0 = app.j.intents_of(f"EMG2_18_SIM-{D0}-S")
    assert [(it.entity, st) for it, st in sim0] == [(FUND, Status.FILLED)]
    assert not app.j.intents_of(f"EMG2_18_SIM-{m1}-R")  # FUND again, no top-up
    # m2: the switch back, a batch of kind B (start-day limits), approved per order
    out = app.j.intents_of(f"EMG2_18_PAPER-{m2}-B")
    assert out and [it.entity for it, _ in out if it.side.value == "SELL"] == [FUND]
    assert sum(1 for it, _ in out if it.side.value == "BUY") >= 15
    for book in ("EMG2_18_PAPER", "EMG2_18_SIM", "EMG2_18_RND_s001", "EMG2_18_RND_s003"):
        pos = app.j.positions(book)
        assert FUND not in pos and len(pos) >= 15, book
    # reconciled every session, nothing halted; pages only for the fund order sizes
    assert summ.safety == SafetyLevel.NORMAL.value and all(summ.recon.values())
    assert summ.positions == app.broker.positions()
    assert all("above the L10" in x for x in summ.pages)
    reps = _reports(tr)
    assert len(reps) == len(DAYS)
    assert "state: FUND" in reps[0] and "state: EMG2" in reps[-1]
    assert any("state: FUND" in t and t.startswith("Decision") for _, t in tr.outbox)


def test_BF_D28_replay_emg2_then_switch_to_fund(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start EMG2 (canary then 17 buys), the next regular month-end FUND: every share is
    sold and the fund bought once the sales settle; the twins hold the fund too."""
    m1, m2 = _month_ends()
    monkeypatch.setattr("trader.bf_app.band_trend", _scripted({D0: "EMG2", m1: "EMG2", m2: "FUND"}))
    app, gw, tr = _app(D0)
    summ = dry_run(app, DAYS, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    for book in ("EMG2_18_PAPER", "EMG2_18_SIM", "EMG2_18_RND_s002"):
        pos = app.j.positions(book)
        assert list(pos) == [FUND], (book, pos)
    out = app.j.intents_of(f"EMG2_18_PAPER-{m2}-B")
    sells = [it for it, _ in out if it.side.value == "SELL"]
    assert len(sells) >= 15 and {it.reason for it in sells} == {BT_OFF_SELL}
    assert [it.entity for it, _ in out if it.side.value == "BUY"] == [FUND]
    assert summ.safety == SafetyLevel.NORMAL.value and all(summ.recon.values())
    assert "state: FUND" in _reports(tr)[-1]


def test_BF_D28_switch_off_by_config_keeps_the_registered_book() -> None:
    cfg = real_config()
    assert cfg.band_trend is not None and cfg.band_trend.enabled
    assert cfg.band_trend.fund == FUND and cfg.band_trend.months == 10
    assert cfg.band_trend_params().enabled and cfg.risk_limits().fund_order_max_aud == 10000
    assert cfg.risk_limits().order_value_max_aud == 800  # L10 for share buys unchanged
    off = cfg.model_copy(update={"band_trend": None})
    assert not off.band_trend_params().enabled
    assert bt_mod.BandTrendParams().enabled is False  # the library default is off


# ------------------------------------------------------------------ the record's data

FWD = os.environ.get("TRADER_FORWARD_STORE")


@pytest.mark.skipif(not FWD, reason="set TRADER_FORWARD_STORE to the record's store")
def test_BF_D28_record_data_30_oct_and_18_nov_2026_state_is_fund() -> None:
    """On the record's data the band index is below its 10-month average on 30 Oct and
    18 Nov 2026 (report 96: OFF since 1 Jun 2026): the live book would hold A200. The
    paper record's own computation (paper_emg2bt) gives OFF on the same days."""
    from trader.bf_dryrun import store_providers

    assert FWD
    cfg, sess = real_config(), asx_sessions()
    panel = store_providers(cfg, Path(FWD), sess)[0]
    for d in (date(2026, 10, 30), date(2026, 11, 18)):
        p = panel(d)
        bt = band_trend(p, cfg.band_trend_params())
        assert bt.state == "FUND" and bt.level < bt.mean, (d, bt.payload())
        assert len(bt.levels) == 10 and min(n for _, _, n in bt.levels) >= 150
        assert FUND in p.entities and p.sec_class[FUND] == "FUND"
