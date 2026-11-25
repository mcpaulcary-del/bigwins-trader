"""BF-D90 (PROPOSED, effective only on owner approval on or after 1 Jan 2027): research_bw's
"January engineering amendment" E5 for the live EMG2-18 book and its twins.

* Rule 14 amended: with fewer than 150 eligible band-C names, nothing is bought and the
  fund is not sold, but every sale the rules require still happens (BID_PEG, C6, and at
  state OFF every share, the proceeds buying the fund).
* Sweep: at each decision, after the rules' orders, X = the trading book's value - A$10,000;
  if X >= A$500, X (at most the cash less A$50) buys A200 into a sleeve the rules never
  count, size on or sell.

Fidelity is checked against a transcription of the research engine's E5 code
(``research_bw/code/bw.py`` ``BW.sells`` / ``BW.buys`` / ``plan_bw`` with ``r14='sellok'``,
``sweep=True``, and the kit sim's buy clip ``amt = min(amt, cash - RESERVE)``, under
``MIN_BUY`` skipped) applied to the frozen rules' own decision of the same book: the
frozen rules (C6 under L15) are already checked against the research engine (BF-D35)."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from datetime import date
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tests.bf_support import synthetic_panel
from trader.lines.emg2 import (
    BT_FUND_BUY,
    BT_FUND_SELL,
    BT_OFF_SELL,
    E5_SWEEP_BUY,
    BookState,
    Emg2_20Decision,
    Emg2_20Params,
    Emg2List,
    Emg2Params,
    decide_emg2_18_bt,
    emg2_list,
    keep_zone,
    rule14_thin,
)
from trader.orders import SLEEVE, OrderParams, Side, build_orders, client_order_id
from trader.panel import PricePanel
from trader.risk import RiskContext, RiskLimits, SafetyLevel, check_intents
from trader.sleeve import rules_positions, sleeve_cost

REPO = Path(__file__).resolve().parent.parent
FUND = "A200"
CAP = Decimal(10000)
OLD = Emg2_20Params(skip_lottery=False, sell_rule="C6")  # the frozen rules (bigwins-fast)
E5 = replace(OLD, rule14_sells=True, sweep=True, e5_from=date(2000, 1, 1))
THIN = Emg2Params(min_names=10**6)  # the same list, but rule 14 always blocks


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


PANEL = _with_fund(synthetic_panel(n_rows=520, n_ent=800, seed=11))
LST = emg2_list(PANEL)
LST_THIN = emg2_list(PANEL, THIN)
COL = {e: j for j, e in enumerate(PANEL.entities)}


def _px(e: str) -> Decimal:
    return Decimal(repr(float(PANEL.close[-1, COL[e]]))).quantize(Decimal("0.0001"))


def _random_book(rng: np.random.Generator, lst: Emg2List, fund_value: float, cash: float) -> tuple[
    BookState, dict[str, int | None]
]:  # fmt: skip
    """Shares from T, the keep zone and the rest of band C, random ages, some fund."""
    keep = keep_zone(lst, 0.40)
    ok = {e for e in COL if not np.isnan(PANEL.close[-1, COL[e]])}
    t = [e for e in lst.targets if e in ok]
    kk = [r.entity for r in lst.band_c if r.entity in keep and r.entity not in t and r.entity in ok]
    out = [r.entity for r in lst.band_c if r.entity not in keep and r.entity in ok]
    k = int(rng.integers(0, 16))
    names = list(rng.choice(t, size=min(k // 3, len(t)), replace=False))
    names += list(rng.choice(kk, size=k // 3, replace=False))
    names += list(rng.choice(out, size=k - 2 * (k // 3), replace=False))
    hold: dict[str, int] = {}
    for e in names:
        hold[str(e)] = max(1, int(float(rng.uniform(300, 800)) / float(_px(str(e)))))
    if fund_value > 0:
        hold[FUND] = max(1, int(fund_value / float(_px(FUND))))
    ages: dict[str, int | None] = {e: int(rng.integers(0, 10)) for e in hold}
    return BookState("B", Decimal(repr(round(cash, 2))), hold), ages


def _sale(qty: int, px: Decimal, p: Emg2_20Params) -> Decimal:
    gross = px * qty
    comm = max(p.est_commission_min_aud, (gross * p.est_commission_rate).quantize(Decimal("0.01")))
    return gross * (1 - p.est_half_spread) - comm


def research_e5(
    base: Emg2_20Decision, blk: bool, book: BookState, p: Emg2_20Params
) -> dict[str, Any]:
    """research_bw E5 (``r14='sellok'``, ``sweep=True``) on top of the frozen rules' own
    decision ``base`` (``super().sells`` / ``super().buys`` of ``BW``), transcribed:

    sells:  ``if blk and e>0 and F in sub.holdings: out=[o for o in out if o!=F]``
            (state ON: the fund is not sold; state OFF sells every share as BT3)
    buys:   ``if memo.get('blk'): o=[x for x in o if x[0]==F]`` (no share buy; the fund
            buy of state OFF stays)
    sweep:  ``X=sub.nav-ST['cap']; if X>=500: o=list(o)+[(F2,X)]``, then the sim's
            ``amt=min(amt, cash-RESERVE); if amt<MIN_BUY: skip`` after the sales and the
            earlier buys (cash after the decision's orders)."""
    sells = {(s.entity, s.qty) for s in base.sells if not (blk and s.entity == FUND)}
    buys = [(b.entity, b.value_aud) for b in base.buys if not blk or b.entity == FUND]
    sleeve = None
    x = base.account_value - CAP
    if x >= 500:
        proceeds = sum((_sale(q, _px(e), p) for e, q in sells), Decimal(0))
        cash = book.cash + proceeds - sum((v for _, v in buys), Decimal(0)) - p.cash_reserve_aud
        amt = min(x, cash).quantize(Decimal("0.01"), ROUND_DOWN)
        sleeve = amt if amt >= 500 else None
    return {"sells": sells, "buys": buys, "sleeve": sleeve}


def _live(dec: Emg2_20Decision) -> dict[str, Any]:
    sw = dec.sweep_buy
    return {
        "sells": {(s.entity, s.qty) for s in dec.sells},
        "buys": [(b.entity, b.value_aud) for b in dec.buys if b.reason != E5_SWEEP_BUY],
        "sleeve": None if sw is None else sw.value_aud,
    }


def _decide(lst: Emg2List, book: BookState, ages: dict[str, int | None], on: bool,
            p: Emg2_20Params) -> Emg2_20Decision:  # fmt: skip
    return decide_emg2_18_bt(PANEL, book, p, lst=lst, trend_on=on, fund=FUND, ages=ages)


# ------------------------------------------------------------------ fidelity to research E5


def test_BF_D90_the_thin_band_is_only_rule_14s_count_test() -> None:
    assert LST.data_block is None and not rule14_thin(LST)
    assert LST_THIN.data_block is not None and LST_THIN.data_block.startswith("rule 14")
    assert rule14_thin(LST_THIN)
    assert LST_THIN.band_c == LST.band_c and LST_THIN.targets == LST.targets


@pytest.mark.parametrize("on", [True, False])
def test_BF_D90_fidelity_to_the_research_engine_on_random_books(on: bool) -> None:
    """300 random books per state (shares from T, the keep zone and outside it, random
    ages, with and without the fund, cash from A$0 to A$6,000), in a normal month and in a
    rule-14 thin band: the live E5 decision is the research E5 decision."""
    rng = np.random.default_rng(90 + on)
    seen = {"thin_sale_no_buy": 0, "sleeve": 0, "thin_fund_kept": 0, "off_fund_buy_thin": 0}
    for _ in range(300):
        fv = float(rng.choice([0.0, 0.0, 3000.0, 9000.0]))
        book, ages = _random_book(rng, LST, fv, float(rng.uniform(0, 6000)))
        base = _decide(LST, book, ages, on, OLD)  # the frozen rules, unblocked
        assert base.data_block is None
        for blk, lst in ((False, LST), (True, LST_THIN)):
            got = _decide(lst, book, ages, on, E5)
            want = research_e5(base, blk, book, E5)
            assert _live(got) == want, (on, blk, book, ages)
            assert got.data_block is None and (got.thin_band is not None) == blk
            old = _decide(lst, book, ages, on, OLD)
            if blk:  # today's rule 14: no decision at all
                assert old.data_block is not None and not old.sells and not old.buys
                if any(x.entity != FUND for x in base.sells) and any(
                    b.entity != FUND for b in base.buys
                ):
                    # rule 14 blocks the buy but not the sale
                    assert got.sells and not any(
                        b.entity != FUND and b.reason != E5_SWEEP_BUY for b in got.buys
                    )
                    seen["thin_sale_no_buy"] += 1
                if on and FUND in book.holdings:
                    assert FUND in got.kept and FUND not in {s.entity for s in got.sells}
                    seen["thin_fund_kept"] += 1
                if not on and any(b.reason == BT_FUND_BUY for b in got.buys):
                    seen["off_fund_buy_thin"] += 1
            else:  # a normal month: E5 is the frozen decision plus the sweep only
                assert _live(old)["sells"] == want["sells"] and _live(old)["buys"] == want["buys"]
            seen["sleeve"] += want["sleeve"] is not None
    assert seen["sleeve"] > 20
    if on:
        assert seen["thin_sale_no_buy"] > 20 and seen["thin_fund_kept"] > 20
    else:
        assert seen["off_fund_buy_thin"] > 20


def test_BF_D90_thin_band_state_on_sells_bid_peg_and_c6_keeps_the_fund() -> None:
    """The defect research_bw found (rule 14 blocked share sales the rules wanted at 13
    month-ends): a ripe holding outside the keep zone is sold in a thin band; the fund
    (BT4 would sell it) and unripe holdings are kept; nothing is bought."""
    keep = keep_zone(LST, 0.40)
    out = [r.entity for r in LST.band_c if r.entity not in keep]
    hold = {out[0]: 100, out[1]: 100, FUND: 30}
    ages: dict[str, int | None] = {out[0]: 7, out[1]: 2, FUND: 9}
    book = BookState("B", Decimal(4000), hold)
    old = _decide(LST_THIN, book, ages, True, OLD)
    assert old.data_block and not old.sells and not old.buys  # today: nothing at all
    got = _decide(LST_THIN, book, ages, True, E5)
    assert [(s.entity, s.reason) for s in got.sells] == [(out[0], "EMG2_C6_EXIT")]
    assert set(got.kept) == {out[1], FUND} and not got.buys
    assert got.thin_band == LST_THIN.data_block and got.payload()["thin_band"]
    normal = _decide(LST, book, ages, True, E5)  # a normal month sells the fund (BT4)
    assert BT_FUND_SELL in {s.reason for s in normal.sells}


def test_BF_D90_thin_band_state_off_sells_every_share_and_buys_the_fund() -> None:
    t = list(LST.targets)
    hold = {t[0]: 100, t[1]: 100}
    book = BookState("B", Decimal(2000), hold)
    ages: dict[str, int | None] = {t[0]: 0, t[1]: 1}
    got = _decide(LST_THIN, book, ages, False, E5)
    assert {s.entity for s in got.sells} == set(hold) and {s.reason for s in got.sells} == {
        BT_OFF_SELL
    }
    assert [b.reason for b in got.buys if b.reason != E5_SWEEP_BUY] == [BT_FUND_BUY]


def test_BF_D90_sweep_amounts() -> None:
    """All cash A$11,000 in state OFF: the fund buy is capped at A$10,000 (L1), the sweep
    takes X = A$1,000 at most the cash less A$50 = A$950. In state ON a trading book of
    A$10,400 sweeps nothing (X < A$500)."""
    got = _decide(LST, BookState("B", Decimal(11000)), {}, False, E5)
    assert [(b.reason, b.value_aud) for b in got.buys] == [
        (BT_FUND_BUY, Decimal("10000.00")), (E5_SWEEP_BUY, Decimal("950.00"))
    ]  # fmt: skip
    assert got.sweep_buy is not None and got.sweep_buy.entity == FUND
    small = _decide(LST, BookState("B", Decimal(10400)), {}, False, E5)
    assert small.sweep_buy is None
    rich = _decide(LST, BookState("B", Decimal(10600), {FUND: 1}), {FUND: 1}, True, E5)
    assert rich.sweep_buy is not None and rich.sweep_buy.value_aud >= 500


# ------------------------------------------------------------------ nothing changes before approval


def test_BF_D90_off_or_before_the_effective_date_the_decision_is_unchanged() -> None:
    """The freeze: with E5 off, or at a decision before ``e5_from``, every decision (and
    its digest) is the frozen rules' one; a decision without a thin band or a sweep has
    the same payload with E5 on."""
    later = replace(E5, e5_from=date(2099, 1, 1))
    rng = np.random.default_rng(7)
    for _ in range(60):
        book, ages = _random_book(
            rng, LST, float(rng.choice([0.0, 5000.0])), float(rng.uniform(0, 3000))
        )
        for on in (True, False):
            for lst in (LST, LST_THIN):
                a = _decide(lst, book, ages, on, OLD)
                assert _decide(lst, book, ages, on, later).digest == a.digest
                assert (
                    _decide(
                        lst,
                        book,
                        ages,
                        on,
                        Emg2_20Params(
                            skip_lottery=False, sell_rule="C6", rule14_sells=True, sweep=True
                        ),
                    ).digest
                    == a.digest
                )  # no e5_from
                b = _decide(lst, book, ages, on, E5)
                if (
                    b.thin_band is None
                    and b.sweep_buy is None
                    and not any(s.reason == "SWEEP_CASH" for s in b.skipped)
                ):
                    assert b.digest == a.digest


def test_BF_D90_config_never_before_1_jan_2027_and_needs_the_fund() -> None:
    from pydantic import ValidationError

    from tests.bf_support import real_config
    from trader.bfast_config import BfastConfig

    cfg = real_config()
    e5 = cfg.live_emg2_20.e5
    assert e5 is not None and e5.rule14_sells and e5.sweep
    assert e5.effective_from >= date(2027, 1, 1) and e5.sweep_min_aud == 500
    p = cfg.emg2_20_params()
    assert p.e5("2026-12-31") == (False, False) and p.e5("2027-01-29") == (True, True)
    raw = cfg.model_dump(mode="json")
    raw["live_emg2_20"]["e5"]["effective_from"] = "2026-12-31"
    with pytest.raises(ValidationError):
        BfastConfig.model_validate(raw)


# ------------------------------------------------------------------ orders, risk, sleeve


def test_BF_D90_sleeve_order_has_its_own_id_and_flag() -> None:
    got = _decide(LST, BookState("B", Decimal(11000)), {}, False, E5)
    batch = build_orders(got, params=OrderParams(), kind="R")
    ids = [i.client_order_id for i in batch.intents]
    assert len(ids) == len(set(ids)) == 2
    fund_buy, sleeve = batch.intents
    assert "FUND" in fund_buy.flags and SLEEVE not in fund_buy.flags
    assert SLEEVE in sleeve.flags and "FUND" not in sleeve.flags and "-A200-SW-BUY-1" in ids[1]
    assert sleeve.reason == E5_SWEEP_BUY
    d = date(2027, 1, 29)
    assert client_order_id("B", d, FUND, Side.BUY) == "B-2027-01-29-A200-BUY-1"  # unchanged
    assert client_order_id("B", d, FUND, Side.BUY, 2, "SW") == "B-2027-01-29-A200-SW-BUY-2"


def _rctx(cash: Decimal, cost: Decimal) -> RiskContext:
    from datetime import UTC, datetime

    return RiskContext(
        now=datetime(2027, 2, 1, 4, 0, tzinfo=UTC), session=date(2027, 2, 1),
        expected_data_date=date(2027, 1, 29), data_as_of=date(2027, 1, 29),
        safety=SafetyLevel.NORMAL, start_day=False, positions={}, settled_cash=cash,
        holdings_cost=cost, fund_cost=cost,
    )  # fmt: skip


def test_BF_D90_risk_lets_the_sleeve_buy_above_the_cap_and_pages_it() -> None:
    """The sleeve holds only money above the cap: the capital cap and the day's buy-value
    limit do not apply to it (the order limit of the fund, cash and price checks do)."""
    got = _decide(LST, BookState("B", Decimal(11000)), {}, False, E5)
    batch = build_orders(got, params=OrderParams(), kind="B")
    sleeve = batch.intents[1]
    tv = Decimal(10**9)
    sl = replace(sleeve, tv_med20=tv)
    rep = check_intents([sl], _rctx(Decimal(5000), Decimal(9990)), RiskLimits())
    assert rep.results[0].verdict.value in ("PASS", "CLIP"), rep.results[0].reasons
    assert "SLEEVE_ABOVE_ORDER_LIMIT" in rep.results[0].reasons and rep.pages
    plain = replace(sl, flags=())  # the same order without the flag: refused as before
    rep2 = check_intents([plain], _rctx(Decimal(5000), Decimal(9990)), RiskLimits())
    assert rep2.results[0].reasons == ("MAX_ORDER_VALUE",)


def test_BF_D90_rules_positions_and_cost_leave_the_sleeve_out() -> None:
    assert rules_positions({FUND: 120, "X": 5}, FUND, 20) == {FUND: 100, "X": 5}
    assert rules_positions({FUND: 20, "X": 5}, FUND, 20) == {"X": 5}
    assert rules_positions({"X": 5}, FUND, 0) == {"X": 5}
    assert sleeve_cost(Decimal(12000), Decimal(120), 20) == Decimal("2000.00")
    assert sleeve_cost(Decimal(0), Decimal(0), 20) == 0


# ------------------------------------------------------------------ the strategy hash


def _strategy_hash_without_e5(tmp: Path) -> str:
    """The strategy hash of this tree with BF-D90 taken out: ``trader/lines/emg2.py`` as on
    bigwins-fast (``E5_BASE``) and ``live_emg2_20.e5`` removed from the config."""
    import shutil

    from trader.strategy_version import STRATEGY_FILES, strategy_hash

    for name in STRATEGY_FILES:
        src = REPO / name
        dst = tmp / name
        if name.endswith("/"):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    try:
        old = subprocess.run(["git", "-C", str(REPO), "show", f"{E5_BASE}:trader/lines/emg2.py"],
                             capture_output=True, check=True).stdout  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("the base commit is not in this checkout (shallow clone)")
    (tmp / "trader/lines/emg2.py").write_bytes(old)
    lines = (REPO / "config/bfast.yaml").read_text().splitlines(keepends=True)
    k = next(i for i, x in enumerate(lines) if x.startswith("  e5:"))
    m = next(i for i in range(k + 1, len(lines)) if not lines[i].startswith("    "))
    cfg = tmp / "config/bfast.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("".join(lines[:k] + lines[m:]))
    return strategy_hash(tmp, cfg)


E5_BASE = "89e9f95"  # bigwins-fast when jan2027-fixes was branched (the frozen strategy)
FROZEN_HASH = "a50dfa0b4eb1"  # strategy hash of bigwins-fast (BF-D72 .. BF-D89)
FROZEN_SETTINGS = "02589a19293b"


def test_BF_D90_strategy_hash_changes_only_by_e5(tmp_path: Path) -> None:
    """Take out the two BF-D90 changes (the line's code, the e5 settings) and the strategy
    hash and the settings hash are the frozen ones again: nothing else that decides moved.
    With them, the hash is the changelog's new top entry."""
    from trader.strategy_version import config_hash, load_changelog, strategy_hash
    from trader.yamlio import load_yaml

    assert _strategy_hash_without_e5(tmp_path) == FROZEN_HASH
    cfg = load_yaml((REPO / "config/bfast.yaml").read_text()) or {}
    cfg["live_emg2_20"].pop("e5")
    assert config_hash(cfg) == FROZEN_SETTINGS
    now = strategy_hash(REPO)
    assert now != FROZEN_HASH
    notes = load_changelog((REPO / "config/strategy_changelog.yaml").read_text())
    assert notes[0]["fingerprint"] == now and "E5" in notes[0]["version"]
    assert notes[1]["fingerprint"] == FROZEN_HASH


def test_BF_D90_only_the_expected_strategy_files_changed() -> None:
    from trader.strategy_version import STRATEGY_FILES

    try:
        files = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", E5_BASE],
                               capture_output=True, text=True, check=True).stdout.split()  # fmt: skip
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("the base commit is not in this checkout (shallow clone)")
    moved = sorted({f for f in files for s in STRATEGY_FILES if f.startswith(s)})
    assert moved == ["trader/lines/emg2.py"]


# ------------------------------------------------------------------ the app: every book alike


def test_BF_D90_app_sleeve_is_kept_through_the_switch_and_counted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A$11,000 books starting in state FUND, then EMG2 from the first month-end: the start
    puts A$10,000 in the fund (the rules') and about A$950 in the sweep sleeve; the switch
    to EMG2 sells exactly the rules' fund units (BT4) and never the sleeve; the paper book,
    the simulated twin and the random twins do the same; the book value (the scoreboard's
    and the twins') counts the sleeve."""
    from tests.test_bf_band_trend import (
        APP_PANEL,
        BT,
        CHAT,
        DAYS,
        P18,
        SEED,
        _closes,
        _month_ends,
        _panel,
    )
    from trader.approval import FakeTransport, TotpVerifier
    from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
    from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
    from trader.broker.mock_gateway import MockGateway
    from trader.broker.paper_sim import SimBroker
    from trader.journal import Journal
    from trader.lines.band_trend import BandTrend
    from trader.secrets import SecretValue

    m1, _m2 = _month_ends()

    def bt(panel: PricePanel, params: object = None, **kw: object) -> BandTrend:
        s = "FUND" if panel.as_of < m1 else "EMG2"
        return BandTrend(panel.as_of.isoformat(), s, 0.9 if s == "FUND" else 1.1, 1.0,  # type: ignore[arg-type]
                         ((panel.as_of.isoformat(), 1.0, 200),))  # fmt: skip

    monkeypatch.setattr("trader.bf_app.band_trend", bt)
    p = replace(P18, sell_rule="C6", rule14_sells=True, sweep=True, e5_from=date(2000, 1, 1))
    gw = MockGateway(cash=11000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    j = Journal.sqlite()
    s = AppSettings(chats=frozenset({CHAT}), start_date=DAYS[0], params=p, random_twins=2,
                    band_trend=BT, capital_aud=Decimal(11000))  # fmt: skip
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", Decimal(11000), "paper deposit")
    sim = SimBroker(cash=Decimal(11000), half_spread=s.sim_half_spread)
    app = BfApp(s, j, broker, sim, FakeTransport(), TotpVerifier(SecretValue(SEED)),
                APP_PANEL.dates, _panel, _closes)  # fmt: skip
    dry_run(app, DAYS[:35], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    for book in (s.book, s.sim_book, "EMG2_18_RND_s001", "EMG2_18_RND_s002"):
        its = [(it, st) for it, st in app.j.intents_of_book(book) if it.entity == FUND]
        ids = [it.client_order_id for it, _ in app.j.intents_of_book(book)]
        assert len(ids) == len(set(ids)), book
        rules_in = sum(it.qty for it, st in its if it.reason == BT_FUND_BUY and st == "FILLED")
        rules_out = sum(it.qty for it, st in its if it.reason == BT_FUND_SELL and st == "FILLED")
        sw = [it for it, st in its if it.reason == E5_SWEEP_BUY and st == "FILLED"]
        assert sw and all(SLEEVE in it.flags for it in sw), book
        assert rules_in > 0 and rules_out == rules_in, book  # BT4 sold the rules' units only
        units = app.sleeve_units(book)
        assert units == sum(it.qty for it in sw) > 0
        assert app.j.positions(book).get(FUND) == units  # only the sleeve is left in A200
        assert FUND not in app._rules_positions(book, DAYS[34])
        px = {FUND: Decimal(100)}
        with_sleeve = app._book_value(book, px)
        assert with_sleeve - app.j.cash(book) >= Decimal(100) * units  # counted


def test_BF_D90_owner_wording_for_the_sleeve() -> None:
    from types import SimpleNamespace

    from trader.app_more import reason_words
    from trader.app_pages import sleeve_note

    w = reason_words(E5_SWEEP_BUY)
    assert "sweep sleeve" in w and "never sell" in w and "scoreboard" in w
    h = SimpleNamespace(code=FUND, qty=100, value=Decimal(12000))
    txt = sleeve_note(SimpleNamespace(sleeve=(FUND, 10), holdings=[h]))
    assert "Sweep sleeve" in txt and "10 of your A200 units" in txt and "$1,200" in txt
    assert "never sell" in txt and "scoreboard counts them" in txt
    assert sleeve_note(SimpleNamespace(sleeve=None, holdings=[])) == ""
    assert "<script>" not in sleeve_note(SimpleNamespace(sleeve=("<script>", 1), holdings=[]))
