"""BF1: EMG2 decision engine (FD v3.0 §7.6, §7.9, §21.1 BF1)."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

from tests.bf_support import sessions, synthetic_panel, t6_reference_list
from trader.lines.emg2 import (
    BookState,
    Emg2_20Params,
    Emg2Input,
    Emg2Params,
    decide_emg2_20,
    emg2_list,
    select_band_c,
)
from trader.panel import PanelError, PricePanel

GOLDEN = os.environ.get("TRADER_EMG2_GOLDEN_DIR")


@pytest.fixture(scope="module")
def panel() -> PricePanel:
    return synthetic_panel()


def test_BW_STR_10_t6_reference_parity_synthetic(panel: PricePanel) -> None:
    """The native list equals a verbatim port of T6's code on the same data."""
    ref = t6_reference_list(panel)
    mine = emg2_list(panel, Emg2Params.t6_compat())
    assert len(ref) >= 30
    assert list(mine.targets) == ref
    for seed in (1, 2, 3):
        p = synthetic_panel(seed=seed, n_rows=280, n_ent=750)
        assert list(emg2_list(p, Emg2Params.t6_compat()).targets) == t6_reference_list(p)


def test_BW_SYS_10_pure_and_deterministic(panel: PricePanel) -> None:
    a = emg2_list(panel)
    b = emg2_list(synthetic_panel())
    assert a.digest == b.digest
    assert json.dumps(a.payload(), sort_keys=True, default=str) == json.dumps(
        b.payload(), sort_keys=True, default=str
    )
    d1 = decide_emg2_20(panel, BookState("B", Decimal(10000)))
    d2 = decide_emg2_20(panel, BookState("B", Decimal(10000)))
    assert d1.digest == d2.digest
    with pytest.raises(ValueError):
        panel.close[0, 0] = 1.0  # read-only input


def test_BW_SYS_12_truncation_invariance_20_dates(panel: PricePanel) -> None:
    """Changing every row after D never changes the list or the decision of D."""
    rng = np.random.default_rng(11)
    for k in rng.choice(np.arange(260, panel.n_sessions - 1), size=20, replace=False):
        d = panel.dates[k]
        base = panel.truncate(d)
        noisy = PricePanel(
            as_of=panel.as_of,
            dates=panel.dates,
            entities=panel.entities,
            close=np.vstack([panel.close[: k + 1], panel.close[k + 1 :] * 3.0]),
            ret=np.vstack([panel.ret[: k + 1], panel.ret[k + 1 :] + 0.5]),
            tv=np.vstack([panel.tv[: k + 1], panel.tv[k + 1 :] * 9.0]),
            sec_class=panel.sec_class,
        ).truncate(d)
        assert emg2_list(base).digest == emg2_list(noisy).digest
        book = BookState("B", Decimal(10000))
        assert decide_emg2_20(base, book).digest == decide_emg2_20(noisy, book).digest


def test_BW_SYS_12_panel_refuses_rows_after_as_of() -> None:
    d = sessions(3)
    a = np.ones((3, 1))
    with pytest.raises(PanelError, match="BW-SYS-12"):
        PricePanel(as_of=d[1], dates=d, entities=("X",), close=a, ret=a, tv=a)
    with pytest.raises(PanelError):
        PricePanel(
            as_of=d[2],
            dates=d,
            entities=("X", "X"),
            close=np.ones((3, 2)),
            ret=np.ones((3, 2)),
            tv=np.ones((3, 2)),
        )


def test_BW_UNI_11_rank_population_and_bands(panel: PricePanel) -> None:
    lst = emg2_list(panel)
    assert lst.band_c and all(301 <= r.tv_rank <= 600 for r in lst.band_c)
    # T is the top fifth of C, best first
    assert len(lst.targets) == sum(1 for r in lst.band_c if r.score_pct > 0.8)
    scores = {r.entity: r.score for r in lst.band_c}
    assert [scores[e] for e in lst.targets] == sorted(scores[e] for e in lst.targets)[::-1]


def test_BW_UNI_03_class_filter_excludes_lic_and_funds() -> None:
    p = synthetic_panel()
    base = emg2_list(p)
    victims = list(base.targets[:3])
    cls = dict(p.sec_class)
    cls[victims[0]] = "LIC"
    cls[victims[1]] = "FUND"
    cls[victims[2]] = "REIT"  # REIT stays in (EMG2 amendment §2)
    p2 = PricePanel(
        as_of=p.as_of,
        dates=p.dates,
        entities=p.entities,
        close=p.close,
        ret=p.ret,
        tv=p.tv,
        sec_class=cls,
    )
    t2 = emg2_list(p2).targets
    assert victims[0] not in t2 and victims[1] not in t2 and victims[2] in t2


def test_rule3_ties_broken_by_higher_tv_med252() -> None:
    mem = [Emg2Input(f"E{k}", 301.0 + k, 1e6 + k, k // 2, 0.1, 0.9) for k in range(10)]
    _, t = select_band_c(mem, Emg2Params())
    assert t == ("E9", "E8")  # the top pair ties on score -> higher tv_med252 first


def test_rule14_data_block_keeps_holdings() -> None:
    p = synthetic_panel(n_ent=500)  # band C has < 150 names
    lst = emg2_list(p)
    assert lst.data_block and "rule 14" in lst.data_block
    d = decide_emg2_20(p, BookState("B", Decimal(100), {"S001": 10}))
    assert d.data_block and not d.sells and not d.buys and d.kept == ("S001",)


# ---------------------------------------------------------------- EMG2-20 (L1-L5)

LOOSE = Emg2_20Params(slots=20, skip_lottery=False, cash_reserve_aud=Decimal(0))  # the 20-name text


def test_L3_L5_start_twenty_parcels(panel: PricePanel) -> None:
    d = decide_emg2_20(panel, BookState("B", Decimal(10500)), LOOSE)
    assert d.slots == 20 and d.parcel == Decimal("500.00")  # L1: sized on the A$10,000 cap
    assert len(d.buys) == 20 and all(b.value_aud == Decimal("500.00") for b in d.buys)
    skipped = {s.entity for s in d.skipped}
    assert skipped <= {s.entity for s in d.skipped if s.reason in ("BID_PEG", "NO_CLOSE")}
    want = [e for e in emg2_list(panel).targets if e not in skipped][:20]
    assert [b.entity for b in d.buys] == want


def test_L5_literal_reserve_makes_every_start_buy_too_small(panel: PricePanel) -> None:
    """Spec defect BF-D1 (docs/DECISIONS.md): with A$10,000, n = 20 and the A$50 reserve,
    the equal share is A$497.50 < A$500, so the 20-name text sends nothing at the start.
    The owner chose 18 names (EMG2-18) instead: see the tests below."""
    d = decide_emg2_20(
        panel, BookState("B", Decimal(10000)), replace(LOOSE, cash_reserve_aud=Decimal(50))
    )
    reasons = {s.reason for s in d.skipped}
    assert (
        not d.buys and "MIN_PARCEL" in reasons and reasons <= {"MIN_PARCEL", "NO_CLOSE", "BID_PEG"}
    )


def test_BF_D1_emg2_18_default_parcels_clear_500_after_costs(panel: PricePanel) -> None:
    """EMG2-18 (owner decision 19 Nov 2026): A$10,000, 18 names, A$50 reserve -> A$552.77
    each, and every order clears A$500 at the reference after A$6.60 and the +3% band."""
    from trader.orders import build_orders

    p = Emg2_20Params(skip_lottery=False)
    assert p.slots == 18
    d = decide_emg2_20(panel, BookState("B", Decimal(10000)), p)
    assert d.slots == 18 and d.parcel == Decimal("555.55")
    assert len(d.buys) == 18 and {b.value_aud for b in d.buys} == {Decimal("552.77")}
    assert sum(b.value_aud for b in d.buys) <= Decimal(10000) - Decimal(50)
    b = build_orders(d)
    assert len(b.intents) == 18 and not [s for s in b.skipped if s[1] == "MIN_PARCEL"]
    assert all(
        i.value_at_ref >= 500 and i.value_at_limit + Decimal("6.60") <= Decimal("552.77")
        for i in b.intents
    )


def test_L4_sell_only_when_off_T_or_pegged(panel: PricePanel) -> None:
    t = emg2_list(panel).targets
    off = next(e for e in panel.entities if e not in t)
    held = {t[30]: 10, off: 10}  # 31st on T is kept (whole top fifth counts)
    d = decide_emg2_20(panel, BookState("B", Decimal(1000), held), LOOSE)
    assert [s.entity for s in d.sells] == [off] and d.sells[0].reason == "EMG2_OFF_LIST"
    assert t[30] in d.kept
    assert all(b.entity not in held for b in d.buys)  # no top-ups


def test_L2_lottery_names_skipped_for_buying(panel: PricePanel) -> None:
    d = decide_emg2_20(
        panel,
        BookState("B", Decimal(10000)),
        replace(LOOSE, skip_lottery=True, lottery_max_age_sessions=10_000),
    )
    assert not d.buys and all(s.reason == "LOTTERY" for s in d.skipped)


def _priced(panel: PricePanel, names: tuple[str, ...]) -> list[str]:
    return [e for e in names if not np.isnan(panel.close[-1, panel.col(e)])]


def _hold(panel: PricePanel, names: list[str], value: float) -> dict[str, int]:
    return {e: int(value / float(panel.close[-1, panel.col(e)])) + 1 for e in names}


def test_L5_cash_shared_equally_and_min_parcel(panel: PricePanel) -> None:
    t = _priced(panel, emg2_list(panel).targets)
    held = _hold(panel, t[:17], 600)
    p = replace(LOOSE, capital_cap_aud=Decimal(12000))
    d = decide_emg2_20(panel, BookState("B", Decimal(1650), held), p)
    # 3 slots free; parcel ~ A$590 but only A$1,650 cash: equal shares of A$550
    assert d.slots == 20 and d.parcel > Decimal(580)
    assert len(d.buys) == 3 and {b.value_aud for b in d.buys} == {Decimal("550.00")}
    d2 = decide_emg2_20(panel, BookState("B", Decimal(1450), held), p)
    assert not d2.buys and sum(s.reason == "MIN_PARCEL" for s in d2.skipped) == 3


def test_L1_cash_above_cap_never_invested(panel: PricePanel) -> None:
    t = _priced(panel, emg2_list(panel).targets)
    held = _hold(panel, t[:19], 600)  # ~A$11,400 held, above the A$10,000 cap
    d = decide_emg2_20(panel, BookState("B", Decimal(3000), held), LOOSE)
    assert not d.buys and not d.sells


FWD = os.environ.get("TRADER_FORWARD_STORE")


@pytest.mark.skipif(not FWD, reason="set TRADER_FORWARD_STORE to the record's EODHD store")
def test_BF_D1_real_30_oct_list_every_pick_becomes_an_order_over_500() -> None:
    """The real 30 Oct 2026 list (forward store, FD defaults, EMG2-18): every pick becomes
    a whole-share order worth at least A$500 at the close after commission, band and reserve."""
    import exchange_calendars as xc

    from trader.data.forward_store import ForwardStore
    from trader.orders import build_orders

    assert FWD
    sess = [
        x.date() for x in xc.get_calendar("XASX", start="2022-01-01", end="2026-12-31").sessions
    ]
    panel = ForwardStore(Path(FWD)).build_panel(date(2026, 10, 30), sess)
    d = decide_emg2_20(panel, BookState("EMG2_18_PAPER", Decimal(10000)))
    assert len(d.buys) == 18 and len(emg2_list(panel).targets) >= 40
    b = build_orders(d)
    assert len(b.intents) == 18, b.skipped
    for i in b.intents:
        assert i.value_at_ref >= 500
        assert i.value_at_limit + Decimal("6.60") <= Decimal("552.77")
    assert sum(i.value_at_limit + Decimal("6.60") for i in b.intents) <= Decimal(9950)


@pytest.mark.skipif(not GOLDEN, reason="set TRADER_EMG2_GOLDEN_DIR to the T6 golden slabs")
class TestGoldenT6:
    """BF1 acceptance: report 85 T6's lists on 12 sampled month-ends 2010-2026.

    Built by ``scripts/golden/t6_extract.py`` from the research panel (vendor data;
    kept off the repository under the EODHD licence, DAT-15)."""

    def _exp(self) -> dict[str, dict]:  # type: ignore[type-arg]
        assert GOLDEN
        out: dict[str, dict] = json.loads((Path(GOLDEN) / "expected_lists.json").read_text())  # type: ignore[type-arg]
        return out

    def _panel(self, d: str) -> PricePanel:
        assert GOLDEN
        z = np.load(Path(GOLDEN) / f"slab_{d}.npz")
        dts = tuple(date.fromisoformat(str(x)) for x in z["dates"])
        syms = tuple(str(s) for s in z["symbols"])
        return PricePanel(
            as_of=dts[-1],
            dates=dts,
            entities=syms,
            close=z["close"],
            ret=z["r"],
            tv=z["tv"],
            sec_class=dict.fromkeys(syms, "ORD"),
        )

    def test_BW_STR_10_selection_step_exact_on_t6_inputs(self) -> None:
        """Rule 3 on T6's own inputs gives T6's T: same names, same order up to exact ties."""
        exp = self._exp()
        assert len(exp) == 12
        for d, v in exp.items():
            mem = [Emg2Input(s, x[0], x[1], x[3], x[4], x[5]) for s, x in v["E"].items()]
            _, t = select_band_c(mem, Emg2Params.t6_compat())
            assert set(t) == set(v["cand"]), d
            groups: dict[float, set[str]] = {}
            for s, sc in zip(v["cand"], v["score"], strict=True):
                groups.setdefault(round(sc, 12), set()).add(s)
            pos = {s: k for k, s in enumerate(t)}
            for k, s in enumerate(v["cand"]):  # same position up to its tie group
                g = groups[round(v["score"][k], 12)]
                assert any(pos[x] == k for x in g), (d, s)

    def test_BW_STR_10_features_and_sets_from_raw_data(self) -> None:
        """E and band C equal T6's on every date; features within T6's float32 precision."""
        for d, v in self._exp().items():
            lst = emg2_list(self._panel(d), Emg2Params.t6_compat())
            assert len(lst.eligible) == v["E_size"] and set(lst.eligible) == set(v["E"]), d
            assert len(lst.band_c) == v["C_size"], d
            for r in lst.band_c:
                x = v["E"][r.entity]
                assert r.tv_rank == x[0] and r.tv_med252 == pytest.approx(x[1], rel=1e-6)
                assert (
                    abs(r.s1 - x[3]) < 2e-4 and abs(r.s2 - x[4]) < 2e-4 and abs(r.s3 - x[5]) < 2e-4
                )

    def test_BW_STR_10_end_to_end_lists(self) -> None:
        """End to end, T equals T6's on >= 10 of 12 dates; elsewhere the only
        differences are boundary swaps from T6's float32 near-ties (<= 4 names)."""
        exact = 0
        for d, v in self._exp().items():
            t = emg2_list(self._panel(d), Emg2Params.t6_compat()).targets
            diff = set(t) ^ set(v["cand"])
            exact += not diff
            assert len(diff) <= 4, (d, diff)
            assert len(set(t) & set(v["cand"])) >= 0.9 * len(v["cand"]), d
        assert exact >= 10
