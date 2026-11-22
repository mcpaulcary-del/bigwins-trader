"""BF-D35: sell rule C6 of the live EMG2-18 book (AMENDMENT_live_EMG2_18_C6.md, owner decision
after report 100; report 99's frozen ``X40_H6``). Paper only.

A holding is sold only if it has been held six or more month-ends since its purchase
decision AND it is outside the top 40% of band C; ``BID_PEG`` and the payout path are
unchanged; under the L15 switch, FUND sells every share whatever its age and EMG2 always
sells the fund. The old rule L4 stays selectable by configuration."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from pydantic import ValidationError

from tests.bf_support import asx_sessions, real_config, synthetic_panel
from trader.approval import FakeTransport, TotpVerifier
from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
from trader.bfast_config import BfastConfig
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.journal import Journal
from trader.lines.band_trend import BandTrend, BandTrendParams
from trader.lines.emg2 import (
    BT_FUND_SELL,
    BT_OFF_SELL,
    EMG2_C6_EXIT,
    BookState,
    Emg2_20Decision,
    Emg2_20Params,
    Emg2List,
    c6_sells,
    decide_emg2_18_bt,
    decide_emg2_20,
    emg2_list,
    keep_zone,
)
from trader.panel import PricePanel
from trader.random_twins import RandomOrder
from trader.risk import SafetyLevel
from trader.secrets import SecretValue

FUND = "A200"
SEED = "JBSWY3DPEHPK3PXP"
C6 = Emg2_20Params(skip_lottery=False, sell_rule="C6")
L4 = Emg2_20Params(skip_lottery=False)
GOLDEN = Path(__file__).parent / "fixtures" / "emg2_c6_golden.json"


def frozen_gone_list(
    hold: Mapping[str, int], pct: Mapping[str, float], peg: Mapping[str, bool]
) -> list[str]:
    """deep99 ``eng99.gone_list`` with X40_H6 (xt 0.40, mh 6, q 0, m None), verbatim logic:
    pegged first (``det`` true), then every ripe holding whose percentile is not above
    0.60 (missing = -1)."""
    gone = [j for j in hold if peg.get(j, False)]
    for j, mh in hold.items():
        if j in gone or not mh >= 6:
            continue
        if not pct.get(j, -1.0) > 1 - 0.40:
            gone.append(j)
    return gone


# ------------------------------------------------------------------ the rule itself


def test_BF_D35_c6_sells_is_the_frozen_rule_on_every_case() -> None:
    """Age 0..9 or unknown x inside / outside K / out of band C x pegged or not."""
    rng = np.random.default_rng(35)
    for _ in range(200):
        names = [f"N{k}" for k in range(30)]
        pct = {e: float(rng.random()) for e in names[:24]}  # the last 6 are out of band C
        ages: dict[str, int | None] = {e: int(rng.integers(0, 10)) for e in names}
        ages[names[3]] = None
        peg = {e: bool(rng.random() < 0.1) for e in names}
        keep = frozenset(e for e, v in pct.items() if v > 0.60)
        got = c6_sells(names, ages, keep, peg.__getitem__)
        hold = {e: (10**6 if a is None else a) for e, a in ages.items()}
        assert sorted(e for e, _ in got) == sorted(frozen_gone_list(hold, pct, peg))
        assert all(r == "EMG2_BID_PEG" for e, r in got if peg[e])
        assert all(r == EMG2_C6_EXIT for e, r in got if not peg[e])


BASE = synthetic_panel(n_rows=520, n_ent=800, seed=11)


def _with_fund(p: PricePanel) -> PricePanel:
    t = p.n_sessions
    fund = 100.0 * np.exp(np.cumsum(np.full(t, 0.0003)))
    fret = np.r_[np.nan, fund[1:] / fund[:-1] - 1]
    cls = dict(p.sec_class)
    cls[FUND] = "FUND"
    return PricePanel(
        as_of=p.as_of, dates=p.dates, entities=(*p.entities, FUND),
        close=np.column_stack([p.close, fund]), ret=np.column_stack([p.ret, fret]),
        tv=np.column_stack([p.tv * 50, np.full(t, 2e7)]), sec_class=cls,
    )  # fmt: skip


def _book(p: PricePanel, lst: Emg2List) -> tuple[BookState, dict[str, int | None]]:
    """A book of 6 names of T, 6 of K outside T, 6 of band C outside K, ages cycling."""
    keep = keep_zone(lst, 0.40)
    t = list(lst.targets)
    kk = [r.entity for r in lst.band_c if r.entity in keep and r.entity not in t]
    out = [r.entity for r in lst.band_c if r.entity not in keep]
    names = t[:6] + kk[:6] + out[-6:]
    cycle: list[int | None] = [0, 2, 5, 6, 9, None]
    ages = {e: cycle[k % len(cycle)] for k, e in enumerate(names)}
    return BookState("B", Decimal(500), dict.fromkeys(names, 100)), ages


def test_BF_D35_decision_sells_only_ripe_holdings_outside_the_top_40_percent() -> None:
    p = _with_fund(BASE)
    lst = emg2_list(p)
    book, ages = _book(p, lst)
    keep = keep_zone(lst, 0.40)
    assert set(lst.targets) <= keep  # T (top fifth) is inside K (top 40%)
    assert keep == {r.entity for r in lst.band_c if r.score_pct > 0.60}
    dec = decide_emg2_20(p, book, C6, lst=lst, ages=ages)
    pct = {r.entity: r.score_pct for r in lst.band_c}
    hold = {e: (10**6 if a is None else a) for e, a in ages.items()}
    want = frozen_gone_list(hold, pct, {})
    assert sorted(s.entity for s in dec.sells) == sorted(want) and want
    assert {s.reason for s in dec.sells} == {EMG2_C6_EXIT}
    assert all(ages[s.entity] is None or (ages[s.entity] or 0) >= 6 for s in dec.sells)
    # unripe names outside K are kept; L4 would have sold every name off T
    unripe_out = [e for e, a in ages.items() if a is not None and a < 6 and e not in keep]
    assert unripe_out and set(unripe_out) <= set(dec.kept)
    l4 = decide_emg2_20(p, book, L4, lst=lst)
    assert {s.entity for s in l4.sells} == {e for e in book.holdings if e not in lst.targets}
    assert len(l4.sells) > len(dec.sells)
    # buys unchanged: the same names of T, fewer of them while more names are kept
    assert [b.entity for b in dec.buys] == [e for e in lst.targets if e not in book.holdings][
        : len(dec.buys)
    ]
    # the payload records the rule and the ages; an L4 payload is unchanged
    pl = dec.payload()
    assert pl["sell_rule"] == "C6" and dict(map(tuple, pl["ages"])) == ages
    assert "sell_rule" not in l4.payload() and "ages" not in l4.payload()


def test_BF_D35_bid_peg_and_payout_path_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    p = _with_fund(BASE)
    lst = emg2_list(p)
    book, ages = _book(p, lst)
    young_in_t = lst.targets[0]
    gone = lst.band_c[-1].entity  # outside K: ripe, but no close for 20 sessions
    ages[gone] = 9
    close = p.close.copy()
    close[-25:, p.entities.index(gone)] = np.nan
    p2 = replace(p, close=close)
    monkeypatch.setattr(
        "trader.lines.emg2.bid_peg",
        lambda panel: np.array([e == young_in_t for e in panel.entities]),
    )
    dec = decide_emg2_20(
        p2, replace(book, holdings={**book.holdings, gone: 50}), C6, lst=lst, ages=ages
    )
    assert (young_in_t, "EMG2_BID_PEG") in {(s.entity, s.reason) for s in dec.sells}
    assert ages[young_in_t] == 0  # sold at once whatever its age
    assert gone in dec.kept and gone not in {s.entity for s in dec.sells}  # payout path


def test_BF_D35_switch_overrides_the_hold() -> None:
    p = _with_fund(BASE)
    lst = emg2_list(p)
    book, ages = _book(p, lst)
    # FUND: every share sold, the youngest included
    off = decide_emg2_18_bt(p, book, C6, lst=lst, trend_on=False, fund=FUND, ages=ages)
    assert {s.entity for s in off.sells} == set(book.holdings)
    assert {s.reason for s in off.sells} == {BT_OFF_SELL}
    # EMG2 with the fund held (age 0): the fund is sold whatever its age, C6 for shares
    q = 40
    held = replace(book, holdings={**book.holdings, FUND: q})
    on = decide_emg2_18_bt(p, held, C6, lst=lst, trend_on=True, fund=FUND, ages={**ages, FUND: 0})
    plain = decide_emg2_20(p, book, C6, lst=lst, ages=ages)
    assert (FUND, BT_FUND_SELL) in {(s.entity, s.reason) for s in on.sells}
    assert {s.entity for s in on.sells} - {FUND} == {s.entity for s in plain.sells}
    # under L4 the switch's decisions are unchanged (digest of BF-D28's path)
    on4 = decide_emg2_18_bt(p, held, L4, lst=lst, trend_on=True, fund=FUND)
    assert "ages" not in on4.payload()
    assert (FUND, BT_FUND_SELL) in {(s.entity, s.reason) for s in on4.sells}


def test_BF_D35_random_twin_keep_zone_is_its_random_score_top_40_percent() -> None:
    p = _with_fund(BASE)
    lst = emg2_list(p)
    o = RandomOrder(seed=8550001, origin=24000, month=24005)
    k = o.keep_zone(lst, 0.40)
    n = len(lst.band_c)
    assert abs(len(k) - round(0.4 * n)) <= 1
    assert set(o(lst, frozenset())) <= k  # the twin's T is inside its K
    assert k == o.keep_zone(lst, 0.40)  # deterministic
    book, ages = _book(p, lst)
    dec = decide_emg2_20(p, book, C6, lst=lst, ages=ages, target_order=o, keep_order=o.keep_zone)
    for s in dec.sells:
        assert s.entity not in k and (ages[s.entity] is None or (ages[s.entity] or 0) >= 6)
    for e in dec.kept:
        assert e in k or (ages[e] is not None and (ages[e] or 0) < 6)


def test_BF_D35_config_selects_the_rule_and_c6_is_configured() -> None:
    cfg = real_config()
    assert cfg.live_emg2_20.sell_rule == "C6"
    params = cfg.emg2_20_params()
    assert (params.sell_rule, params.c6_min_months, params.c6_keep_fraction) == ("C6", 6, 0.40)
    old = cfg.model_copy(
        update={"live_emg2_20": cfg.live_emg2_20.model_copy(update={"sell_rule": "L4"})}
    )
    assert old.emg2_20_params().sell_rule == "L4"
    raw = cfg.model_dump(mode="json")
    raw["live_emg2_20"]["sell_rule"] = "C7"
    with pytest.raises(ValidationError):
        BfastConfig.model_validate(raw)
    del raw["live_emg2_20"]["sell_rule"]
    assert BfastConfig.model_validate(raw).live_emg2_20.sell_rule == "L4"  # default: old rule


# ------------------------------------------------------------------ multi-month replay in the app

APP_PANEL = _with_fund(synthetic_panel(n_rows=500, n_ent=800, seed=7))


def _closes(day: date) -> dict[str, Decimal]:
    k = APP_PANEL.dates.index(day)
    return {e: Decimal(repr(round(float(c), 3))) for e, c in zip(APP_PANEL.entities, APP_PANEL.close[k], strict=True)
            if not np.isnan(c)}  # fmt: skip


def _panel(day: date) -> PricePanel:
    p = APP_PANEL.truncate(day)
    return replace(p, close=np.round(p.close, 3))


def _scripted(states: Mapping[date, str]) -> Callable[..., BandTrend]:
    def f(panel: PricePanel, params: BandTrendParams | None = None, **kw: object) -> BandTrend:
        s = states.get(panel.as_of, "EMG2")
        return BandTrend(panel.as_of.isoformat(), s, 0.9 if s == "FUND" else 1.1, 1.0,  # type: ignore[arg-type]
                         ((panel.as_of.isoformat(), 1.0, 200),))  # fmt: skip

    return f


D0 = APP_PANEL.dates[262]
DAYS = list(APP_PANEL.dates[262:480])
MONTH_ENDS = [
    d for d in DAYS[:-1] if APP_PANEL.dates[APP_PANEL.dates.index(d) + 1].month != d.month
]


def _app(
    rule: str, j: Journal | None = None, gw: MockGateway | None = None
) -> tuple[BfApp, MockGateway]:
    fresh = gw is None
    gw = gw or MockGateway(cash=10000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    s = AppSettings(chats=frozenset({77}), start_date=D0, random_twins=2,
                    params=replace(L4, sell_rule=rule),  # type: ignore[arg-type]
                    band_trend=BandTrendParams(enabled=True))  # fmt: skip
    if j is None:
        j = Journal.sqlite()
        for book in (s.book, s.sim_book):
            j.add_cash(book, "DEPOSIT", Decimal(10000), "paper deposit")
    sim = (
        SimBroker(cash=Decimal(10000), half_spread=s.sim_half_spread)
        if fresh
        else SimBroker.from_journal(j, s.sim_book, s.sim_half_spread)
    )
    app = BfApp(
        s, j, broker, sim, FakeTransport(), TotpVerifier(SecretValue(SEED)), APP_PANEL.dates,
        _panel, _closes,
    )  # fmt: skip
    return app, gw


Captured = list[
    tuple[str, date, Emg2_20Decision, dict[str, int | None] | None, frozenset[str], dict[str, int]]
]


def _capture(app: BfApp, rec: Captured) -> None:
    orig = app._decide_book

    def wrapped(
        panel: PricePanel, state: BookState, lst: Any, order: Any, trend: Any, ages: Any = None
    ) -> Emg2_20Decision:
        dec = orig(panel, state, lst, order, trend, ages)
        k = order.keep_zone(lst, 0.40) if order is not None else keep_zone(lst, 0.40)
        rec.append((state.book, panel.as_of, dec, ages, k, dict(state.holdings)))
        return dec

    app._decide_book = wrapped  # type: ignore[method-assign]


def test_BF_D35_multi_month_replay_ages_restart_switch_and_turnover(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Start EMG2 (canary + 17), ten month-ends in state EMG2, one FUND, then EMG2 again:
    in the paper book, the twin and two random twins every sale is ripe and outside K
    (the frozen rule), the ages are the month-ends since each buy decision, a restart in
    the middle (a new app on the same journal and broker) gives the same ages, the FUND
    decision sells every share whatever its age, the paper book and its twin stay equal
    (L13), everything reconciles, and C6 sends fewer orders than L4 on the same data."""
    fund_me = MONTH_ENDS[-2]
    assert len(MONTH_ENDS) >= 9
    monkeypatch.setattr("trader.bf_app.band_trend", _scripted({fund_me: "FUND"}))
    rec: Captured = []
    app, gw = _app("C6")
    _capture(app, rec)
    cut = MONTH_ENDS[6]
    k = DAYS.index(cut)
    s1 = dry_run(app, DAYS[: k + 1], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    before = app.holding_ages(app.s.book, cut, app.j.positions(app.s.book))
    app2, _ = _app("C6", app.j, gw)  # restart: only the journal and the broker carry over
    _capture(app2, rec)
    assert app2.holding_ages(app2.s.book, cut, app2.j.positions(app2.s.book)) == before
    assert any(a is not None and a >= 5 for a in before.values())
    s2 = dry_run(app2, DAYS[k + 1 :], {}, owner_approves_all(app2, SEED), mock_auction(gw, _closes))
    for s in (s1, s2):
        assert s.safety == SafetyLevel.NORMAL.value and all(s.recon.values())
    books = {r[0] for r in rec}
    assert {"EMG2_18_PAPER", "EMG2_18_SIM", "EMG2_18_RND_s001", "EMG2_18_RND_s002"} <= books
    n_c6 = n_young_out = 0
    young_at_fund = 0
    for book, d, dec, ages, keep, holdings in rec:
        assert ages is not None and set(ages) == set(holdings)
        if dec.state == "FUND":  # every share sold whatever its age (BT3)
            assert d == fund_me
            assert {s.entity for s in dec.sells} == set(holdings) - {FUND}
            assert {s.reason for s in dec.sells} <= {BT_OFF_SELL}
            young_at_fund += sum(1 for e, a in ages.items() if a is not None and a < 6)
            continue
        held = sorted(holdings)
        # independent age check: month-ends since the decision of the entity's latest buy
        buys = sorted(
            (it.decision_date, it.entity)
            for it, _ in app2.j.intents_of_book(book)
            if it.side.value == "BUY" and it.decision_date < d
        )
        last_buy = {e: x for x, e in buys}
        for e in held:
            if e in last_buy and any(f.entity == e for f in app2.j.fills(book)):
                assert ages[e] == sum(1 for m in MONTH_ENDS if last_buy[e] < m <= d), (book, d, e)
        sold = {s.entity: s.reason for s in dec.sells}
        for e in held:
            if e == FUND:
                assert sold.get(e) == BT_FUND_SELL
                continue
            ripe = ages[e] is None or (ages[e] or 0) >= 6
            if sold.get(e) == EMG2_C6_EXIT:
                assert ripe and e not in keep
                n_c6 += 1
            elif e not in sold and e in dec.kept and e not in keep:
                assert not ripe
                n_young_out += 1
    assert n_c6 > 0 and n_young_out > 0 and young_at_fund > 0
    # paper book and twin (L13): a name both hold with the same age gets the same decision
    # (their name lists differ by the start month-end the paper book skips, L6, which L13
    # explains)
    by = {(r[0], r[1]): (r[2], r[3] or {}) for r in rec}
    same = 0
    for d in MONTH_ENDS:
        a, b = by.get(("EMG2_18_PAPER", d)), by.get(("EMG2_18_SIM", d))
        if a is None or b is None:
            continue
        sa, sb = {s.entity for s in a[0].sells}, {s.entity for s in b[0].sells}
        for e in set(a[1]) & set(b[1]):
            if a[1][e] == b[1][e]:
                assert (e in sa) == (e in sb), (d, e)
                same += 1
    assert same >= 50
    # turnover: the same data under L4 sends more orders
    app4, gw4 = _app("L4")
    dry_run(app4, DAYS, {}, owner_approves_all(app4, SEED), mock_auction(gw4, _closes))
    n6 = len(app2.j.fills(app2.s.book))
    n4 = len(app4.j.fills(app4.s.book))
    assert n6 < n4, (n6, n4)


# ------------------------------------------------------------------ golden: the frozen rule on the record's data

FWD = os.environ.get("TRADER_FORWARD_STORE")


def test_BF_D35_golden_fixture_is_the_frozen_rule() -> None:
    """The fixture's expected sells were computed by deep99's frozen ``eng99.gone_list``
    on the record's table; this repository's ``c6_sells`` gives the same on its inputs."""
    g = json.loads(GOLDEN.read_text())
    for _, x in sorted(g["dates"].items()):
        keep = frozenset(x["K"])
        got = c6_sells(x["holdings"], x["ages"], keep, set(x["bid_peg"]).__contains__)
        assert sorted(e for e, _ in got) == x["expected_sells"]
        assert set(x["T"]) <= keep


@pytest.mark.skipif(not FWD, reason="set TRADER_FORWARD_STORE to the record's store")
def test_BF_D35_record_data_30_oct_and_18_nov_2026_match_the_frozen_decisions() -> None:
    """On the record's store, 30 Oct and 18 Nov 2026: the trading system's T and keep zone
    equal the record's (paper_emg2.table, class rule v2) and its C6 sells for the fixture
    book equal deep99's frozen decisions; L4 would sell the names off T; under the switch
    in state EMG2 the fund is sold too."""
    from trader.bf_dryrun import store_providers

    assert FWD
    g = json.loads(GOLDEN.read_text())
    cfg, sess = real_config(), asx_sessions()
    panels = store_providers(cfg, Path(FWD), sess)[0]
    params = replace(cfg.emg2_20_params(), skip_lottery=False)
    assert params.sell_rule == "C6"
    for ds, x in sorted(g["dates"].items()):
        p = panels(date.fromisoformat(ds))
        lst = emg2_list(p)
        assert list(lst.targets) == x["T"], ds
        assert keep_zone(lst, 0.40) == set(x["K"]), ds
        book = BookState("G", Decimal(100), dict.fromkeys(x["holdings"], 100))
        dec = decide_emg2_20(p, book, params, lst=lst, ages=x["ages"])
        assert sorted(s.entity for s in dec.sells) == x["expected_sells"], ds
        l4 = decide_emg2_20(p, book, replace(params, sell_rule="L4"), lst=lst)
        assert sorted(s.entity for s in l4.sells) == x["expected_l4_sells"], ds
        held = replace(book, holdings={**book.holdings, FUND: 10})
        on = decide_emg2_18_bt(
            p, held, params, lst=lst, trend_on=True, fund=FUND, ages={**x["ages"], FUND: 0}
        )
        assert sorted(s.entity for s in on.sells) == sorted([*x["expected_sells"], FUND]), ds
