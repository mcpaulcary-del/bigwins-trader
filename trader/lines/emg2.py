"""EMG2 v1.0 list and the EMG2-20 real-money selection (FD v3.0 §7.6, §7.9). Pure.

Frozen rule texts: ``AMENDMENT_shadow_EMG2.md`` (rules 1-3, 8, 14 are used here)
and ``AMENDMENT_live_EMG2_20.md`` (rules L2-L5). Where this module and a frozen rule
file disagree, the rule file wins (FD §0.3) and the difference is a bug.

* ``emg2_list(panel, params)`` -> ``Emg2List``: eligible set E, band C, the in-band
  score and the target list T (top fifth of C, best first; ties by higher
  ``tv_med252``). Rule 14: fewer than ``min_names`` in C -> data block, no decision.
* ``decide_emg2_20(panel, book, params, live)`` -> ``Emg2_20Decision``: sells
  (holdings off T or ``BID_PEG``), buys (best-ranked names of T not held, lottery
  names and pegged names skipped, one parcel each, cash shared equally when short,
  orders under A$500 not sent).

Both are deterministic: same panel, book and params give the same canonical JSON
(BW-SYS-10); ``Emg2List.digest`` and ``Emg2_20Decision.digest`` are its SHA-256.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from typing import Any

import numpy as np

from trader.canonical import sha256_json
from trader.features import age_sessions, bid_peg, momentum, pct_rank, recent_close
from trader.panel import PricePanel
from trader.universe import RankScope, liquidity_table

CENT = Decimal("0.01")
LIST_CLASSES = frozenset({"ORD", "REIT"})


@dataclass(frozen=True)
class Emg2Params:
    """EMG2 v1.0 parameters (config ``lines.EMG2.params``; FD §20)."""

    top_fraction: float = 0.2
    band_lo: int = 301
    band_hi: int = 600
    min_names: int = 150  # rule 14
    min_tv_med63: float = 100_000.0
    min_close: float = 0.10
    close_lookback: int = 5  # "on the decision day (or within the previous 5 sessions)"
    traded_within: int = 5
    s3_min_valid: int = 200
    rank_scope: RankScope = "fd"
    # BF-D20: a session without a row is ignored in the medians, as the registered EMG2
    # table (``AMENDMENT_shadow_EMG2.md`` s2, ``paper_emg2.table``): the live list equals
    # the paper twins' list. (Zero-filling such sessions moved ranks near the band edges.)
    zero_fill_listed: bool = False
    class_filter: bool = True
    tie_break_tv: bool = True

    @classmethod
    def t6_compat(cls) -> Emg2Params:
        """Report 85 T6's list code (``deep85/code/t6.py``) for the golden test: rank
        over every entity, missing days ignored in medians, no class filter, no 200-day
        minimum for ``s3``, no rule 14 (T6 has no data block)."""
        return cls(
            min_names=0, s3_min_valid=0, rank_scope="all", zero_fill_listed=False,
            class_filter=False, tie_break_tv=False,
        )  # fmt: skip


@dataclass(frozen=True)
class Emg2Row:
    entity: str
    tv_rank: float
    tv_med252: float
    s1: float
    s2: float
    s3: float
    score: float
    score_pct: float


@dataclass(frozen=True)
class Emg2List:
    as_of: str
    eligible: tuple[str, ...]
    band_c: tuple[Emg2Row, ...]
    targets: tuple[str, ...]  # T, best first
    data_block: str | None  # reason, or None
    params: Emg2Params

    def payload(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of,
            "eligible": list(self.eligible),
            "band_c": [r.__dict__ for r in self.band_c],
            "targets": list(self.targets),
            "data_block": self.data_block,
            "params": self.params.__dict__,
        }

    @property
    def digest(self) -> str:
        return sha256_json(self.payload())


@dataclass(frozen=True)
class Emg2Input:
    """One member of the eligible set E with its selection inputs (rule 2)."""

    entity: str
    tv_rank: float
    tv_med252: float
    s1: float
    s2: float
    s3: float


def select_band_c(
    members: Sequence[Emg2Input], p: Emg2Params
) -> tuple[tuple[Emg2Row, ...], tuple[str, ...]]:
    """Rule 3 on the eligible set: band C, in-band score and T (best first)."""
    c = [m for m in members if m.tv_rank >= p.band_lo]
    if not c:
        return (), ()
    s1 = np.array([m.s1 for m in c])
    s2 = np.array([m.s2 for m in c])
    s3 = np.array([m.s3 for m in c])
    score = (pct_rank(s1) + pct_rank(s2) + pct_rank(s3)) / 3.0
    spct = pct_rank(score)
    rows = [
        Emg2Row(
            entity=m.entity,
            tv_rank=m.tv_rank,
            tv_med252=m.tv_med252,
            s1=m.s1,
            s2=m.s2,
            s3=m.s3,
            score=float(score[k]),
            score_pct=float(spct[k]),
        )
        for k, m in enumerate(c)
    ]
    top = [r for r in rows if r.score_pct > 1.0 - p.top_fraction]
    if p.tie_break_tv:
        top.sort(key=lambda r: (-r.score, -r.tv_med252, r.entity))
    else:  # T6 sorted by score only (numpy argsort); a stable sort keeps E's order on ties
        top.sort(key=lambda r: -r.score)
    rows.sort(key=lambda r: (-r.score, r.entity))
    return tuple(rows), tuple(r.entity for r in top)


def emg2_inputs(panel: PricePanel, p: Emg2Params) -> list[Emg2Input]:
    """Rule 2: the eligible set E with its inputs, in panel column order."""
    liq = liquidity_table(
        panel,
        rank_scope=p.rank_scope,
        zero_fill_listed=p.zero_fill_listed,
        traded_within_sessions=p.traded_within,
    )
    s1, s2, s3 = momentum(panel, s3_min_valid=p.s3_min_valid)
    close = recent_close(panel, p.close_lookback)
    rk = liq.tv_rank
    with np.errstate(invalid="ignore"):
        el = (
            (rk <= p.band_hi) & (liq.tv_med63 >= p.min_tv_med63) & (close >= p.min_close)
            & liq.traded5 & ~np.isnan(s1) & ~np.isnan(s2) & ~np.isnan(s3)
        )  # fmt: skip
    if p.class_filter:
        el &= np.array([panel.sec_class.get(e) in LIST_CLASSES for e in panel.entities])
    return [
        Emg2Input(
            panel.entities[j],
            float(rk[j]),
            float(liq.tv_med252[j]),
            float(s1[j]),
            float(s2[j]),
            float(s3[j]),
        )
        for j in np.flatnonzero(el)
    ]


def emg2_list(panel: PricePanel, params: Emg2Params | None = None) -> Emg2List:
    """EMG2 rules 2, 3 and 14 at the panel's session D."""
    p = params or Emg2Params()
    members = emg2_inputs(panel, p)
    band_c, targets = select_band_c(members, p)
    block = None
    if not band_c:
        block = "band C empty"
    elif len(band_c) < p.min_names:
        block = f"rule 14: {len(band_c)} names in band C < {p.min_names}"
    eligible = tuple(m.entity for m in members)
    return Emg2List(str(panel.as_of), eligible, band_c, targets, block, p)


# ---------------------------------------------------------------- EMG2-20 (§7.9)


TargetOrder = Callable[[Emg2List, frozenset[str]], Sequence[str]]


@dataclass(frozen=True)
class Emg2_20Params:  # noqa: N801 - the line's registered name
    slots: int = 18  # owner decision BF-D1 (19 Nov 2026): EMG2-18, about A$550 a name
    slot_unit_aud: Decimal = Decimal(550)  # EMG2-18 L3: n = min(18, floor(value / A$550))
    min_parcel_aud: Decimal = Decimal(500)  # L5: an order under A$500 is not sent
    cash_reserve_aud: Decimal = Decimal(50)
    capital_cap_aud: Decimal = Decimal(10000)
    skip_lottery: bool = True
    lottery_max_age_sessions: int = 504
    lottery_max_close: float = 0.20
    lottery_max_tv_med63: float = 250_000.0
    # Estimated sale cost used only to plan buys funded by the same decision's sells.
    est_commission_min_aud: Decimal = Decimal("6.60")
    est_commission_rate: Decimal = Decimal("0.00088")
    est_half_spread: Decimal = Decimal("0.005")
    payout_after_sessions: int = 20  # BW-UNI-21: valued at zero for sizing after 20 sessions


@dataclass(frozen=True)
class BookState:
    """A broker book as the line sees it at decision time (pure input)."""

    book: str
    cash: Decimal
    holdings: Mapping[str, int] = field(default_factory=dict)  # entity -> whole shares


@dataclass(frozen=True)
class SellPlan:
    entity: str
    qty: int
    ref_close: Decimal
    reason: str  # EMG2_OFF_LIST | EMG2_BID_PEG


@dataclass(frozen=True)
class BuyPlan:
    entity: str
    t_rank: int  # 1 = best on T
    value_aud: Decimal
    ref_close: Decimal
    reason: str = "EMG2_NEW_ENTRY"


@dataclass(frozen=True)
class Skip:
    entity: str
    reason: str  # LOTTERY | BID_PEG | MIN_PARCEL | NO_CLOSE


@dataclass(frozen=True)
class Emg2_20Decision:  # noqa: N801
    book: str
    as_of: str
    list_digest: str
    data_block: str | None
    account_value: Decimal
    slots: int
    parcel: Decimal
    sells: tuple[SellPlan, ...]
    buys: tuple[BuyPlan, ...]
    skipped: tuple[Skip, ...]
    kept: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "book": self.book, "as_of": self.as_of, "list_digest": self.list_digest,
            "data_block": self.data_block, "account_value": self.account_value,
            "slots": self.slots, "parcel": self.parcel,
            "sells": [s.__dict__ for s in self.sells], "buys": [b.__dict__ for b in self.buys],
            "skipped": [s.__dict__ for s in self.skipped], "kept": list(self.kept),
        }  # fmt: skip

    @property
    def digest(self) -> str:
        return sha256_json(self.payload())


def _dec_price(x: float) -> Decimal:
    return Decimal(repr(float(x))).quantize(Decimal("0.0001"))


def lottery_flags(panel: PricePanel, p: Emg2_20Params) -> dict[str, bool]:
    """FD §8.6 lottery class: age < 504 sessions, close < A$0.20 or ``tv_med63`` < A$250k.
    ``tv_med63`` as the EMG2 table computes it (sessions without a row ignored; BF-D20)."""
    liq = liquidity_table(panel, zero_fill_listed=False)
    close = recent_close(panel, 5)
    age = age_sessions(panel)
    out: dict[str, bool] = {}
    for j, e in enumerate(panel.entities):
        m63 = liq.tv_med63[j]
        out[e] = bool(
            age[j] < p.lottery_max_age_sessions
            or not close[j] >= p.lottery_max_close
            or not m63 >= p.lottery_max_tv_med63
        )
    return out


def _sale_estimate(qty: int, px: Decimal, p: Emg2_20Params) -> Decimal:
    gross = px * qty
    comm = max(p.est_commission_min_aud, (gross * p.est_commission_rate).quantize(CENT))
    return gross * (1 - p.est_half_spread) - comm


@dataclass(frozen=True)
class _Ctx:
    panel: PricePanel
    p: Emg2_20Params
    col: Mapping[str, int]
    last_any: Any  # FloatArray: last close within the payout window
    peg: Any  # BoolArray
    lottery: Mapping[str, bool]

    def px(self, e: str) -> Decimal | None:
        j = self.col.get(e)
        if j is None or math.isnan(self.last_any[j]):
            return None
        return _dec_price(self.last_any[j])

    def pegged(self, e: str) -> bool:
        j = self.col.get(e)
        return j is not None and bool(self.peg[j])


def _plan_sells(
    ctx: _Ctx, book: BookState, targets: frozenset[str]
) -> tuple[list[SellPlan], list[str], Decimal]:
    """L4: sell in full every holding not on T or flagged ``BID_PEG``."""
    sells: list[SellPlan] = []
    kept: list[str] = []
    proceeds = Decimal(0)
    for e in sorted(book.holdings):
        q = book.holdings[e]
        price = ctx.px(e)
        if price is None:
            kept.append(e)  # no close for 20 sessions: payout path (BW-UNI-21), not an order
        elif e not in targets or ctx.pegged(e):
            reason = "EMG2_BID_PEG" if ctx.pegged(e) else "EMG2_OFF_LIST"
            sells.append(SellPlan(e, q, price, reason))
            proceeds += _sale_estimate(q, price, ctx.p)
        else:
            kept.append(e)
    return sells, kept, proceeds


def _pick_buys(
    ctx: _Ctx, book: BookState, targets: Sequence[str], want: int
) -> tuple[list[tuple[int, str, Decimal]], list[Skip]]:
    """L2/L5: best-ranked names of T not held; lottery and pegged names skipped."""
    cands: list[tuple[int, str, Decimal]] = []
    skipped: list[Skip] = []
    for rank, e in enumerate(targets, start=1):
        if len(cands) >= want:
            break
        if e in book.holdings:
            continue
        j = ctx.col[e]
        if ctx.p.skip_lottery and ctx.lottery.get(e, True):
            skipped.append(Skip(e, "LOTTERY"))
        elif ctx.pegged(e):
            skipped.append(Skip(e, "BID_PEG"))
        elif math.isnan(ctx.panel.close[-1, j]):
            skipped.append(Skip(e, "NO_CLOSE"))
        else:
            cands.append((rank, e, _dec_price(ctx.panel.close[-1, j])))
    return cands, skipped


def decide_emg2_20(
    panel: PricePanel,
    book: BookState,
    params: Emg2_20Params | None = None,
    list_params: Emg2Params | None = None,
    *,
    lst: Emg2List | None = None,
    target_order: TargetOrder | None = None,
) -> Emg2_20Decision:
    """One EMG2-20 decision (rules L2-L5) for ``book`` at the panel's session D.

    ``lst``: the EMG2 list of this panel, if already computed (one list serves the
    simulated twin and its random twins). ``target_order(lst, pegged)``: replaces the
    order of rule 3 (T) for a random twin (``trader.random_twins``); None = T."""
    p = params or Emg2_20Params()
    if any(q <= 0 for q in book.holdings.values()):
        raise ValueError("holdings must be positive whole shares (long only)")
    lst = lst or emg2_list(panel, list_params)
    ctx = _Ctx(
        panel=panel, p=p, col={e: j for j, e in enumerate(panel.entities)},
        last_any=recent_close(panel, p.payout_after_sessions - 1), peg=bid_peg(panel),
        lottery=lottery_flags(panel, p),
    )  # fmt: skip
    held_value = sum(((ctx.px(e) or Decimal(0)) * q for e, q in book.holdings.items()), Decimal(0))
    account_value = (book.cash + held_value).quantize(CENT)
    sizing_value = min(account_value, p.capital_cap_aud)  # L1
    n = max(0, min(p.slots, int(sizing_value // p.slot_unit_aud)))  # L3 (EMG2-18)
    parcel = (sizing_value / n).quantize(CENT, ROUND_DOWN) if n else Decimal(0)
    if lst.data_block:  # rule 14: no decision, holdings kept
        return Emg2_20Decision(
            book.book, lst.as_of, lst.digest, lst.data_block, account_value, n, parcel,
            (), (), (), tuple(sorted(book.holdings)),
        )  # fmt: skip
    targets = lst.targets
    if target_order is not None:
        pegged = frozenset(e for e, j in ctx.col.items() if bool(ctx.peg[j]))
        targets = tuple(target_order(lst, pegged))
    sells, kept, proceeds = _plan_sells(ctx, book, frozenset(targets))
    cands, skipped = _pick_buys(ctx, book, targets, n - len(kept))
    kept_value = sum(((ctx.px(e) or Decimal(0)) * book.holdings[e] for e in kept), Decimal(0))
    available = min(
        book.cash + proceeds - p.cash_reserve_aud,  # L5 reserve
        p.capital_cap_aud - kept_value,  # L1: cash above the cap is never invested
    )
    buys: list[BuyPlan] = []
    if cands and available > 0:
        each = parcel if parcel * len(cands) <= available else available / len(cands)
        each = each.quantize(CENT, ROUND_DOWN)
        for rank, e, ref in cands:
            if each < p.min_parcel_aud:
                skipped.append(Skip(e, "MIN_PARCEL"))  # its cash waits for the next decision
            else:
                buys.append(BuyPlan(e, rank, each, ref))
    return Emg2_20Decision(
        book.book, lst.as_of, lst.digest, None, account_value, n, parcel,
        tuple(sells), tuple(buys), tuple(skipped), tuple(kept),
    )  # fmt: skip
