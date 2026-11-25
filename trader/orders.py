"""Order building (FD v3.0 §7.9 L5-L7, §11; BF2). Pure.

``build_orders()`` turns an EMG2-20 decision into ``OrderIntent`` rows:

* whole shares, rounded down; sells first, then buys (EXE-08 carried);
* a buy is sized so that quantity x limit + estimated commission fits its planned
  value, and is **not generated** when quantity x reference price is under the
  A$500 first-purchase minimum (ASX minimum marketable parcel; L5, BW-PRT-03);
* order type ``LOC`` (limit-on-close, the closing single-price auction, BW-EXE-01)
  or the L7 fallback ``LMT`` (DAY limit sent at 15:30 at ask + one step / bid - one
  step, inside reference x 1.03 / 0.97). **[unverified, O-1]** whether IBKR accepts
  ``LOC`` on ASX through the API for these shares, and its cut-off, is decided by the
  reality spike; config ``bfast.execution.order_type`` selects the path;
* limit price = reference x (1 +/- band), rounded to a valid ASX price step towards
  the reference (buy down, sell up). The step table below is the ASX schedule
  stated in the FD; **[unverified]** against IBKR's market-rule ids for each contract
  (production must read the rule from IBKR contract details, SYS-29 carried);
* deterministic ``client_order_id`` = ``<book>-<D>-<entity>-<side>-<attempt>``
  (BW-EXE-06), sent to IBKR as ``orderRef``.

DAT-20's ``sentinel_floor`` (v2.10, ETF rule L1) is kept until the B0 re-base.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, Decimal
from enum import StrEnum

from trader.canonical import sha256_json
from trader.lines.emg2 import BT_FUND_BUY, E5_SWEEP_BUY, Emg2_20Decision

CENT = Decimal("0.01")


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    LOC = "LOC"  # limit-on-close (closing auction)
    LMT = "LMT"  # L7 fallback: DAY limit in continuous trading


# (upper bound exclusive, step). FD §7.6 rule 10: A$0.001 below A$0.10, A$0.005
# below A$2, A$0.01 from A$2. [unverified vs IBKR market rules]
PRICE_STEPS: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal("0.10"), Decimal("0.001")),
    (Decimal("2.00"), Decimal("0.005")),
    (Decimal("Infinity"), Decimal("0.01")),
)


def price_step(price: Decimal) -> Decimal:
    for bound, step in PRICE_STEPS:
        if price < bound:
            return step
    raise AssertionError("unreachable")


def round_to_step(price: Decimal, side: Side) -> Decimal:
    """Round to a valid step towards the reference: a buy limit down, a sell limit up."""
    if price <= 0:
        raise ValueError("price must be positive")
    step = price_step(price)
    units = (price / step).to_integral_value(ROUND_FLOOR if side is Side.BUY else ROUND_CEILING)
    return (units * step).normalize()


def is_valid_step(price: Decimal) -> bool:
    return (
        price > 0 and (price / price_step(price)) == (price / price_step(price)).to_integral_value()
    )


@dataclass(frozen=True)
class CommissionModel:
    """IBKR commission on an ASX order, incl. GST (review M1; config ``broker.pricing``).

    * ``fixed`` (the default here): max(A$6.60, 0.088%), i.e. A$6.00 / 0.08% + 10% GST
      (FD §11.2).
    * ``tiered`` (the owner's plan): (max(``minimum``, ``rate`` x value) + the exchange /
      clearing / regulatory pass-through ``fees_rate`` x value) x (1 + ``gst``). IBKR
      Australia's public schedule: 0.08% up to A$3m a month, minimum A$5.00, ex GST; the
      ASX pass-through fees are **[unverified]** (a config value, checked in the
      reality spike against real fills)."""

    minimum: Decimal = Decimal("6.60")
    rate: Decimal = Decimal("0.00088")
    pricing: str = "fixed"
    fees_rate: Decimal = Decimal(0)
    gst: Decimal = Decimal(0)

    def __call__(self, value: Decimal) -> Decimal:
        if value <= 0:
            return Decimal(0)
        if self.pricing == "tiered":
            base = max(self.minimum, value * self.rate) + value * self.fees_rate
            return (base * (1 + self.gst)).quantize(CENT, ROUND_CEILING)
        return max(self.minimum, (value * self.rate).quantize(CENT, ROUND_CEILING))


def tiered_commission(fees_rate: Decimal = Decimal("0.00005")) -> CommissionModel:
    """IBKR Australia tiered, tier I (public schedule): 0.08%, min A$5.00, + GST 10%."""
    return CommissionModel(Decimal("5.00"), Decimal("0.0008"), "tiered", fees_rate, Decimal("0.10"))


SLEEVE = "SLEEVE"  # BF-D90: an order of the sweep sleeve (flag; coid tag ``SW``)


def client_order_id(
    book: str, d: date, entity: str, side: Side, attempt: int = 1, tag: str = ""
) -> str:
    """``tag``: BF-D90's sweep-sleeve buy (``SW``) has its own id, so it never collides
    with the rules' own fund buy of the same decision; untagged ids are unchanged."""
    if attempt < 1:
        raise ValueError("attempt starts at 1")
    mid = f"{entity}-{tag}" if tag else entity
    return f"{book}-{d.isoformat()}-{mid}-{side.value}-{attempt}"


@dataclass(frozen=True)
class OrderIntent:
    client_order_id: str
    batch_id: str
    seq: int  # 1-based number inside the batch (the owner approves "/ok <batch> <seq>")
    line: str
    book: str
    decision_date: date
    entity: str
    side: Side
    qty: int
    order_type: OrderType
    ref_price: Decimal
    limit_price: Decimal
    reason: str
    attempt: int = 1
    tv_med20: Decimal | None = None
    prev_close: Decimal | None = None
    flags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.qty <= 0 or int(self.qty) != self.qty:
            raise ValueError("qty must be a positive whole number of shares")
        if self.limit_price <= 0 or self.ref_price <= 0:
            raise ValueError("prices must be positive")
        for v in (self.ref_price, self.limit_price):
            if not isinstance(v, Decimal):
                raise TypeError("prices are Decimal (SYS-13)")

    @property
    def value_at_limit(self) -> Decimal:
        return (self.limit_price * self.qty).quantize(CENT)

    @property
    def value_at_ref(self) -> Decimal:
        return (self.ref_price * self.qty).quantize(CENT)


@dataclass(frozen=True)
class OrderParams:
    order_type: OrderType = OrderType.LOC
    limit_band: Decimal = Decimal("0.03")  # band C (BW-EXE-03 / L7)
    min_parcel_aud: Decimal = Decimal(500)
    commission: CommissionModel = field(default_factory=CommissionModel)


@dataclass(frozen=True)
class OrderBatch:
    batch_id: str
    book: str
    decision_date: date
    intents: tuple[OrderIntent, ...]
    skipped: tuple[tuple[str, str], ...]  # (entity, reason)
    decision_digest: str

    @property
    def digest(self) -> str:
        return sha256_json(
            {
                "batch_id": self.batch_id,
                "decision": self.decision_digest,
                "intents": [i.__dict__ for i in self.intents],
                "skipped": list(self.skipped),
            }
        )


def batch_id_for(book: str, d: date, kind: str = "R") -> str:
    """``kind``: R regular, S start, C canary, X carried/re-planned."""
    return f"{book}-{d.isoformat()}-{kind}"


def build_orders(
    decision: Emg2_20Decision,
    *,
    line: str = "EMG2_20",
    params: OrderParams | None = None,
    kind: str = "R",
    canary: bool = False,
    tv_med20: dict[str, Decimal] | None = None,
) -> OrderBatch:
    """Intents for one decision. ``canary`` keeps only the first buy (L6) and no sells."""
    p = params or OrderParams()
    d = date.fromisoformat(decision.as_of)
    bid = batch_id_for(decision.book, d, "C" if canary else kind)
    tvm = tv_med20 or {}
    intents: list[OrderIntent] = []
    skipped: list[tuple[str, str]] = [(s.entity, s.reason) for s in decision.skipped]
    if decision.data_block:
        return OrderBatch(bid, decision.book, d, (), tuple(skipped), decision.digest)
    if not canary:
        for s in decision.sells:
            lim = round_to_step(s.ref_close * (1 - p.limit_band), Side.SELL)
            intents.append(
                OrderIntent(
                    client_order_id(decision.book, d, s.entity, Side.SELL),
                    bid,
                    0,
                    line,
                    decision.book,
                    d,
                    s.entity,
                    Side.SELL,
                    s.qty,
                    p.order_type,
                    s.ref_close,
                    lim,
                    s.reason,
                    tv_med20=tvm.get(s.entity),
                    prev_close=s.ref_close,
                )
            )
    buys = decision.buys[:1] if canary else decision.buys
    for b in buys:
        lim = round_to_step(b.ref_close * (1 + p.limit_band), Side.BUY)
        budget = b.value_aud - p.commission(b.value_aud)
        qty = int((budget / lim).to_integral_value(ROUND_DOWN))
        if qty <= 0 or b.ref_close * qty < p.min_parcel_aud:
            skipped.append((b.entity, "MIN_PARCEL"))
            continue
        sleeve = b.reason == E5_SWEEP_BUY  # BF-D90: the sweep sleeve's buy
        intents.append(
            OrderIntent(
                client_order_id(decision.book, d, b.entity, Side.BUY, tag="SW" if sleeve else ""),
                bid,
                0,
                line,
                decision.book,
                d,
                b.entity,
                Side.BUY,
                qty,
                p.order_type,
                b.ref_close,
                lim,
                b.reason,
                tv_med20=tvm.get(b.entity),
                prev_close=b.ref_close,
                flags=(
                    *(("CANARY",) if canary else ()),
                    *(("FUND",) if b.reason == BT_FUND_BUY else ()),  # L15 fund order (BF-D28)
                    *((SLEEVE,) if sleeve else ()),
                ),
            )
        )
    numbered = tuple(replace(it, seq=k) for k, it in enumerate(intents, start=1))
    return OrderBatch(bid, decision.book, d, numbered, tuple(skipped), decision.digest)


def fallback_limit(
    side: Side,
    *,
    bid: Decimal | None,
    ask: Decimal | None,
    ref: Decimal,
    band: Decimal = Decimal("0.03"),
) -> Decimal | None:
    """L7 fallback limit: buy at ask + one step capped at ref x (1 + band); sell at
    bid - one step floored at ref x (1 - band). None if the needed quote is missing."""
    if side is Side.BUY:
        if ask is None or ask <= 0:
            return None
        cap = round_to_step(ref * (1 + band), Side.BUY)
        return min(round_to_step(ask + price_step(ask), Side.BUY), cap)
    if bid is None or bid <= 0:
        return None
    floor_ = round_to_step(ref * (1 - band), Side.SELL)
    lo = bid - price_step(bid)
    return max(round_to_step(lo, Side.SELL) if lo > 0 else floor_, floor_)


def renumber(intents: Sequence[OrderIntent]) -> tuple[OrderIntent, ...]:
    return tuple(replace(it, seq=k) for k, it in enumerate(intents, start=1))


def sentinel_floor(target_units: int, *, sentinel_unit: bool) -> int:
    """DAT-20 (v2.10 rule L1): with ``l1.sentinel_unit`` on, a target of zero units
    becomes 1 unit. Kept until the B0 re-base removes rule L1."""
    if target_units < 0:
        raise ValueError("target units are never negative (long only)")
    if sentinel_unit and target_units == 0:
        return 1
    return target_units
