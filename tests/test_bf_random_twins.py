"""BF-D18: the 100 random twins of the simulated EMG2-18 book (L13; L11 test (b))."""

from __future__ import annotations

import os
import random
from dataclasses import replace
from datetime import date
from decimal import Decimal

import numpy as np
import pytest

from tests.bf_support import real_config
from tests.test_bf_app import D0, DAYS, PANEL, SEED, _app, _closes, _panel
from trader.bf_app import BfApp, at, dry_run, mock_auction, owner_approves_all
from trader.bfast_config import BfastConfig
from trader.lines.emg2 import (
    BookState,
    Emg2_20Params,
    Emg2List,
    decide_emg2_20,
    emg2_list,
    lottery_flags,
)
from trader.loss_rule import percentile_rank
from trader.random_twins import (
    BUYABLE_FROM,
    REDRAW,
    SEED_BASE,
    RandomOrder,
    month_index,
    random_score,
    twin_books,
    uniform,
)


def test_BF_D18_twin_names_and_seeds_are_the_registered_ones() -> None:
    books = twin_books("EMG2_18_RND")
    assert len(books) == 100 and SEED_BASE == 8550000
    assert books[0] == ("EMG2_18_RND_s001", 8550001)
    assert books[-1] == ("EMG2_18_RND_s100", 8550100)
    assert len({b for b, _ in books}) == 100


def test_BF_D18_draws_are_pinned_and_platform_independent() -> None:
    """Golden values: the SHA-256 draw must never change (it defines the twins)."""
    assert 0.0 <= uniform(8550100, "KAN", 24322, "redraw") < 1.0
    a = [uniform(8550001, f"E{k:03d}", 0, "score") for k in range(4000)]
    assert abs(np.mean(a) - 0.5) < 0.02 and min(a) >= 0.0 and max(a) < 1.0


def test_BF_D18_golden_draw_value() -> None:
    assert month_index(date(2026, 10, 30)) == 24321
    assert f"{uniform(8550001, 'BHP', 24321, 'score'):.12f}" == "0.087139881343"


def test_BF_D18_score_is_persistent_and_redrawn_with_probability_0_2_a_month() -> None:
    origin = month_index(date(2026, 10, 30))
    ents = [f"E{k:04d}" for k in range(3000)]
    changed, total = 0, 0
    for m in range(origin + 1, origin + 13):
        for e in ents:
            a = random_score(8550007, e, m - 1, origin)
            b = random_score(8550007, e, m, origin)
            redrawn = uniform(8550007, e, m, "redraw") < REDRAW
            assert (a != b) == redrawn  # unchanged unless redrawn that month
            changed += redrawn
            total += 1
    assert abs(changed / total - REDRAW) < 0.01
    # different twins draw different scores
    assert random_score(8550001, "E0001", origin, origin) != random_score(
        8550002, "E0001", origin, origin
    )


def _list() -> Emg2List:
    return emg2_list(_panel(D0))


def test_BF_D18_random_order_same_count_from_band_c_without_pegged_names() -> None:
    lst = _list()
    c = [r.entity for r in lst.band_c]
    assert lst.targets and len(c) > len(lst.targets)
    m = month_index(D0)
    pegged = frozenset(c[:5])
    t1 = RandomOrder(8550001, m, m)(lst, pegged)
    assert len(t1) == len(lst.targets) and set(t1) <= set(c) and not set(t1) & pegged
    assert t1 == RandomOrder(8550001, m, m)(lst, pegged)  # deterministic
    assert t1 != RandomOrder(8550002, m, m)(lst, pegged)
    assert t1 != lst.targets  # the order of rule 3 is replaced
    # the order does not depend on how band C is ordered (restart / data order safe)
    rows = list(lst.band_c)
    random.Random(1).shuffle(rows)
    assert RandomOrder(8550001, m, m)(replace(lst, band_c=tuple(rows)), pegged) == t1


def test_BF_D18_decide_with_the_list_order_is_the_registered_decision() -> None:
    panel = _panel(D0)
    lst = emg2_list(panel)
    p = Emg2_20Params(skip_lottery=False)
    book = BookState("X", Decimal(10000))
    base = decide_emg2_20(panel, book, p)
    same = decide_emg2_20(panel, book, p, lst=lst, target_order=lambda x, _peg, _lot: x.targets)
    assert same.digest == base.digest
    m = month_index(D0)
    rnd = decide_emg2_20(panel, book, p, lst=lst, target_order=RandomOrder(8550001, m, m))
    assert {b.entity for b in rnd.buys} != {b.entity for b in base.buys}
    assert len(rnd.buys) + len(rnd.skipped) >= 1


def _twins_app(n: int) -> tuple[BfApp, object]:
    app, gw, tr = _app(D0, random_twins=n)
    return app, gw


def _run(app: BfApp, gw: object, days: list[date]) -> None:
    dry_run(app, days, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))  # type: ignore[arg-type]


def test_BF_D18_a_twin_in_list_order_is_the_simulated_twin_to_the_cent() -> None:
    """Golden equivalence: the random twins run the simulated twin's code path and
    costs; with the order of rule 3 instead of the random score each twin ends with
    exactly the simulated twin's holdings and cash after two month-end decisions."""
    app, gw = _twins_app(3)
    app._random_order = lambda seed, day, now: (lambda lst, _peg, _lot: lst.targets)  # type: ignore[method-assign,assignment,return-value]
    _run(app, gw, DAYS)
    sim = app.s.sim_book
    for name, *_ in app.rnd:
        assert app.j.positions(name) == app.j.positions(sim)
        assert app.j.cash(name) == app.j.cash(sim)
        assert len(app.j.fills(name)) == len(app.j.fills(sim)) > 18
    pct = app.twin_percentile(DAYS[-1])
    assert pct == Decimal(50)  # all tied: ties count half


def test_BF_D18_random_twins_daily_record_report_and_restart() -> None:
    app, gw = _twins_app(4)
    _run(app, gw, DAYS[:20])
    # a restart: a new process rebuilds every twin from the journal alone
    app2, _, _ = _app(D0, random_twins=4, journal=app.j, gw=gw)  # type: ignore[arg-type]
    _run(app2, gw, DAYS[20:])
    ref, gw_r = _twins_app(4)
    _run(ref, gw_r, DAYS)
    for (name, *_), (n2, *_) in zip(app2.rnd, ref.rnd, strict=True):
        assert name == n2
        assert app2.j.positions(name) == ref.j.positions(name)
        assert app2.j.cash(name) == ref.j.cash(name)
    d = DAYS[-1]
    held = [set(ref.j.positions(n)) for n, *_ in ref.rnd]
    sim = set(ref.j.positions(ref.s.sim_book))
    assert all(h and h != sim for h in held)  # random books, different from the twin
    assert len({frozenset(h) for h in held}) == 4
    v = ref.twin_values(d)
    assert v is not None
    pct = ref.twin_percentile(d)
    assert pct == percentile_rank(v[0], v[1]) and pct is not None
    assert ref.twin_rank(d) == pct  # L11 test (b) reads the running twins
    rec = dict(ref.j.job_records(f"rnd:{d}"))[f"rnd:{d}"]
    assert rec["percentile"] == str(pct) and len(rec["values"]) == 4
    rep = [t for _, t in ref.transport.outbox if "random twins" in t]  # type: ignore[attr-defined]
    assert len(rep) == len(DAYS) and f"at the {pct} percentile of 4 random twins" in rep[-1]


def test_BF_D18_config_pins_100_twins_and_the_seed_base() -> None:
    cfg: BfastConfig = real_config()
    assert cfg.data.random_twins == 100
    assert cfg.data.random_seed_base == 8550000 and cfg.data.random_prefix == "EMG2_18_RND"
    raw = cfg.model_dump()
    raw["data"]["random_twins"] = 10
    with pytest.raises(ValueError, match="random_twins"):
        BfastConfig.model_validate(raw)


def test_BF_D18_no_twins_no_percentile() -> None:
    app, _, _ = _app(D0)
    assert app.twin_values(DAYS[0]) is None and app.twin_rank(DAYS[0]) is None
    assert PANEL.dates[0] < D0


def test_BF_D18_L11_stage2_resumes_automatically_with_the_twins_running() -> None:
    """Go-live blocker closed: with the random twins running (no injected rank) the
    staged test (b) has a percentile and buying resumes at the month-end decision."""
    from tests.test_bf_app import M2, _Marks
    from trader.risk import SafetyLevel

    app, gw = _twins_app(3)
    app._random_order = lambda seed, day, now: (lambda lst, _peg, _lot: lst.targets)  # type: ignore[method-assign,assignment,return-value]
    _run(app, gw, DAYS[:4])
    m = _Marks(app)
    m.walk("9000", "8100", "7200", "6400", "5990.00")
    assert app.j.safety_level() is SafetyLevel.HALTED_BUYS
    assert app.twin_rank(M2) == Decimal(50)
    app.job_decide(M2, at(M2, "22:20"))
    assert app.j.safety_level() is SafetyLevel.NORMAL
    out = [t for _, t in app.transport.outbox]  # type: ignore[attr-defined]
    assert any(t.startswith(f"L11 {M2}: staged test passed") and "percentile 50" in t for t in out)


# ---------------------------------------------------------------- BF-D36 buyable stratum

# A lottery class on the synthetic panel with both strata in band C: by traded value only
# (band C 284 names, 186 lottery class; T 57 names, 23 buyable). Under the old draw 23 of
# the 100 twins' lists hold fewer than 18 buyable names.
LOT36 = Emg2_20Params(lottery_max_age_sessions=0, lottery_max_tv_med63=1.7e7)
OLD = date(2100, 1, 1)  # buyable_from after the decision: the old (pre-BF-D36) draw
NEW = date.min  # buyable_from before the decision: the BF-D36 stratum draw


def _buyable(names: tuple[str, ...] | list[str], lot: dict[str, bool]) -> int:
    return sum(1 for e in names if not lot.get(e, True))


def test_BF_D36_twin_list_has_the_real_lists_length_and_buyable_count() -> None:
    panel = _panel(D0)
    lst = emg2_list(panel)
    lot = lottery_flags(panel, LOT36)
    m = month_index(D0)
    real_buy = _buyable(lst.targets, lot)
    assert 18 <= real_buy < len(lst.targets)  # both strata in T
    starved = 0
    for book, seed in twin_books("EMG2_18_RND"):
        new = RandomOrder(seed, m, m, NEW)(lst, frozenset(), lot)
        assert len(new) == len(lst.targets) and len(set(new)) == len(new), book
        assert _buyable(new, lot) == real_buy, book
        assert set(new) <= {r.entity for r in lst.band_c}
        # best first by the twin's random score, and each stratum is its own top slice
        sc = [random_score(seed, e, m, m) for e in new]
        assert sc == sorted(sc, reverse=True)
        pool = sorted(
            (r.entity for r in lst.band_c), key=lambda e: (-random_score(seed, e, m, m), e)
        )
        assert [e for e in new if not lot[e]] == [e for e in pool if not lot[e]][:real_buy]
        lots = [e for e in pool if lot[e]][: len(lst.targets) - real_buy]
        assert [e for e in new if lot[e]] == lots
        assert new == RandomOrder(seed, m, m, NEW)(lst, frozenset(), lot)  # deterministic
        old = RandomOrder(seed, m, m, OLD)(lst, frozenset(), lot)
        assert len(old) == len(lst.targets)
        starved += _buyable(old, lot) < 18
    assert starved == 23  # the flaw the amendment fixes, on these data


def test_BF_D36_pegged_names_stay_out_and_order_is_band_order_free() -> None:
    panel = _panel(D0)
    lst = emg2_list(panel)
    lot = lottery_flags(panel, LOT36)
    m = month_index(D0)
    c = [r.entity for r in lst.band_c]
    pegged = frozenset(c[:7])
    t = RandomOrder(8550001, m, m, NEW)(lst, pegged, lot)
    assert not set(t) & pegged and len(t) == len(lst.targets)
    assert _buyable(t, lot) == _buyable(lst.targets, lot)
    rows = list(lst.band_c)
    random.Random(3).shuffle(rows)
    assert RandomOrder(8550001, m, m, NEW)(replace(lst, band_c=tuple(rows)), pegged, lot) == t


def test_BF_D36_effective_from_the_30_nov_2026_decision() -> None:
    """Before 30 Nov 2026 the old draw (record tables before that date keep it); without a
    lottery class (the buy step skips none) one draw."""
    assert date(2026, 11, 30) == BUYABLE_FROM
    panel = _panel(D0)
    lst = emg2_list(panel)
    lot = lottery_flags(panel, LOT36)
    m = month_index(D0)
    o = RandomOrder(8550004, m, m)  # default: BUYABLE_FROM; D0 is in 2024
    assert o(lst, frozenset(), lot) == RandomOrder(8550004, m, m, OLD)(lst, frozenset(), lot)
    assert o(lst, frozenset(), lot) == o(lst, frozenset())
    late = replace(lst, as_of="2026-11-30")
    assert RandomOrder(8550004, m, m)(late, frozenset(), lot) == RandomOrder(8550004, m, m, NEW)(
        lst, frozenset(), lot
    )
    assert RandomOrder(8550004, m, m, NEW)(lst, frozenset(), None) == o(lst, frozenset())


def test_BF_D36_twins_hold_18_names_like_the_real_book() -> None:
    """Each of the 100 twins, from cash, buys 18 names (the real book's count) with the
    stratum draw; under the old draw the starved twins left cash idle."""
    panel = _panel(D0)
    lst = emg2_list(panel)
    m = month_index(D0)
    book = BookState("X", Decimal(10000))
    real = decide_emg2_20(panel, book, LOT36, lst=lst)
    assert real.slots == 18 and len(real.buys) == 18
    short_old = 0
    for _, seed in twin_books("EMG2_18_RND"):
        new = decide_emg2_20(panel, book, LOT36, lst=lst, target_order=RandomOrder(seed, m, m, NEW))
        fails = [s for s in new.skipped if s.reason in ("NO_CLOSE", "MIN_PARCEL")]
        assert len(new.buys) == 18 or fails, seed  # cash-check failures only
        assert sum(b.value_aud for b in new.buys) == sum(b.value_aud for b in real.buys)
        again = decide_emg2_20(
            panel, book, LOT36, lst=lst, target_order=RandomOrder(seed, m, m, NEW)
        )
        assert again.digest == new.digest  # deterministic
        old = decide_emg2_20(panel, book, LOT36, lst=lst, target_order=RandomOrder(seed, m, m, OLD))
        short_old += len(old.buys) < 18
    assert short_old == 26  # 23 starved lists, 3 more with a skipped name (peg, no close)


@pytest.mark.skipif(
    not os.environ.get("TRADER_FORWARD_STORE"),
    reason="set TRADER_FORWARD_STORE to the record's store",
)
def test_BF_D36_record_data_twins_hold_18_names_with_the_stratum_draw() -> None:
    """The record's store, 30 Oct and 18 Nov 2026, forced to the BF-D36 draw: every twin's
    list has T's length and buyable count, and every twin buys 18 names from A$10,000 like
    the real book; under the old draw 14 and 32 twins bought fewer (up to A$2,778 and
    A$3,333 idle), the flaw ``AMENDMENT_twins_buyable_set.md`` s1 found in the record."""
    from pathlib import Path

    from tests.bf_support import asx_sessions
    from trader.bf_dryrun import store_providers

    cfg = real_config()
    panels = store_providers(cfg, Path(os.environ["TRADER_FORWARD_STORE"]), asx_sessions())[0]
    params = cfg.emg2_20_params()
    assert params.skip_lottery
    book = BookState("X", Decimal(10000))
    for ds, t_len, t_buy, starved in (("2026-10-30", 40, 28, 14), ("2026-11-18", 37, 26, 32)):
        day = date.fromisoformat(ds)
        p = panels(day)
        lst = emg2_list(p)
        lot = lottery_flags(p, params)
        assert (len(lst.targets), _buyable(lst.targets, lot)) == (t_len, t_buy), ds
        m = month_index(day)
        assert len(decide_emg2_20(p, book, params, lst=lst).buys) == 18
        short = 0
        for _, seed in twin_books("EMG2_18_RND"):
            new = RandomOrder(seed, m, m, NEW)
            assert len(t := new(lst, frozenset(), lot)) == t_len and _buyable(t, lot) == t_buy
            assert len(decide_emg2_20(p, book, params, lst=lst, target_order=new).buys) == 18
            old = RandomOrder(seed, m, m)  # before 30 Nov 2026: the old draw
            short += len(decide_emg2_20(p, book, params, lst=lst, target_order=old).buys) < 18
        assert short == starved, ds
