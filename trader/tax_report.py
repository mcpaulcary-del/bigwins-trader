"""Australian financial-year tax report of a broker book (BF-D29; FD v3.0 BW-TAX-01/02).

**General information, not tax advice.** The report is prepared from the trading
system's journal for the owner's accountant, who decides how each item is treated.

For the year 1 July - 30 June it lists

* every parcel bought and sold (trade dates, quantities, cost base including brokerage,
  proceeds net of brokerage) and the capital gain or loss of each parcel slice sold,
  split into short-term and **discount-eligible** (held ``discount_days`` or more; the
  record uses **367 days** as a safety margin over the ATO's "at least 12 months");
* capital losses, the losses carried in from earlier years of this book (and any the
  owner enters) and the net capital loss carried forward;
* dividends (franked and unfranked amounts, franking credits where the franking is
  known), specials, withholding;
* fund (trust) distributions of ``fund_codes`` (A200) with the AMIT cost-base
  adjustments **from the annual tax statement - entered manually** (``amit_csv``);
* capital returns (cost-base reductions; any excess a G1 capital gain), demergers
  (cost base apportioned; demerged shares keep the original acquisition date),
  in-specie receipts, splits / consolidations and code changes;
* brokerage totals;
* a reconciliation of the journal against IBKR's Activity Flex records (trades, cash
  transactions, corporate actions, positions), every difference flagged.

Parcels are matched **FIFO** by default (``tax.parcel_method``); ``min_tax`` is a form
of specific identification, used only after the accountant confirms it (O-8).
Dates are Sydney trade (contract) dates: the CGT event of a sale happens at the contract,
not at settlement. Pure apart from ``write_report``; the journal is only read.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from trader.constants import ASX_TZ
from trader.corporate_actions import Booking, CaKind
from trader.data.flex import FlexCashTransaction, FlexStatement
from trader.journal import FillRecord, Journal
from trader.orders import Side

CENT = Decimal("0.01")
ZERO = Decimal(0)
DISCOUNT = Decimal("0.5")  # individuals: 50% CGT discount (ATO); the accountant confirms
SMALL_SHAREHOLDER_CREDITS = Decimal(5000)  # 45-day rule exemption threshold (all holdings)
NEAR_LINE_DAYS = 365  # held 365..discount_days-1: flagged "near the 12-month line"
NOT_ADVICE = "General information, not tax advice."
AMIT_MANUAL = "from the annual tax statement - enter manually"
Method = Literal["FIFO", "min_tax"]

FY_RE = re.compile(r"^(\d{4})-(\d{2})$")


class TaxReportError(ValueError):
    pass


def fy_bounds(text: str) -> tuple[date, date, str]:
    """``"2026-27"`` -> (1 Jul 2026, 30 Jun 2027, "2026-27")."""
    m = FY_RE.match(text.strip())
    if not m:
        raise TaxReportError(f"financial year {text!r}: use the form 2026-27")
    y = int(m.group(1))
    if (y + 1) % 100 != int(m.group(2)):
        raise TaxReportError(f"financial year {text!r}: the second year must follow the first")
    return date(y, 7, 1), date(y + 1, 6, 30), f"{y}-{(y + 1) % 100:02d}"


def fy_of(d: date) -> int:
    """The starting calendar year of the financial year holding ``d``."""
    return d.year if d.month >= 7 else d.year - 1


def fy_label(y: int) -> str:
    return f"{y}-{(y + 1) % 100:02d}"


def m2(x: Decimal) -> str:
    return str(x.quantize(CENT, ROUND_HALF_EVEN))


def qty_s(x: Decimal) -> str:
    return f"{x.normalize():f}" if x == x.to_integral_value() else f"{x:f}"


def sydney_date(t: datetime) -> date:
    return (t if t.tzinfo else t.replace(tzinfo=UTC)).astimezone(ASX_TZ).date()


def _at(d: date, hh: int = 0, mm: int = 0, ss: int = 0) -> datetime:
    return datetime.combine(d, time(hh, mm, ss), ASX_TZ).astimezone(UTC)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AmitEntry:
    """One fund's AMIT cost-base adjustment for a year, typed in by the owner from the
    fund's annual tax statement (net cost base increase / decrease for the units held)."""

    fy: int
    code: str
    increase: Decimal = ZERO
    decrease: Decimal = ZERO
    note: str = ""


def load_amit_csv(path: Path) -> list[AmitEntry]:
    """``fy,code,cost_base_increase,cost_base_decrease,note`` (``fy`` as 2026-27)."""
    out: list[AmitEntry] = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            try:
                start, _, _ = fy_bounds(r["fy"])
                inc = Decimal((r.get("cost_base_increase") or "0").strip() or "0")
                dec = Decimal((r.get("cost_base_decrease") or "0").strip() or "0")
                if inc < 0 or dec < 0:
                    raise TaxReportError("amounts are entered as positive numbers")
                out.append(
                    AmitEntry(start.year, r["code"].strip().upper(), inc, dec, r.get("note") or "")
                )
            except (KeyError, InvalidOperation, TaxReportError) as exc:
                raise TaxReportError(f"{path} line {i}: {exc}") from exc
    return out


@dataclass(frozen=True)
class TaxParams:
    method: Method = "FIFO"
    discount_days: int = 367
    fund_codes: frozenset[str] = frozenset()


# ---------------------------------------------------------------------------
# Parcels and events
# ---------------------------------------------------------------------------


@dataclass
class Parcel:
    pid: str
    code: str  # the code it is held under now (code changes followed)
    acquired: date  # for the discount test (demerged shares: the original date)
    qty0: Decimal  # at acquisition, in today's units
    cost0: Decimal  # at acquisition, incl. brokerage
    brokerage: Decimal
    origin: str  # BUY <exec id> | DEMERGER <key> | IN_SPECIE <key>
    traded_as: str
    qty: Decimal = ZERO  # still held
    cost: Decimal = ZERO  # cost base of what is still held
    adjusted: Decimal = ZERO  # cost-base changes so far (negative = reduced)
    closed: date | None = None

    def __post_init__(self) -> None:
        self.qty, self.cost = self.qty0, self.cost0


@dataclass(frozen=True)
class CgtRow:
    fy: int
    event: str  # SALE | DISPOSAL | CASH_IN_LIEU | G1 | E10
    code: str
    pid: str
    acquired: date | None
    disposed: date
    qty: Decimal
    cost_base: Decimal
    proceeds: Decimal
    days_held: int | None
    long: bool  # discount eligible (held discount_days or more)
    near_line: bool  # held 365 .. discount_days - 1: the accountant checks the dates
    ref: str
    note: str = ""

    @property
    def gain(self) -> Decimal:
        return self.proceeds - self.cost_base


@dataclass(frozen=True)
class TradeRow:
    fy: int
    day: date
    code: str
    side: str
    qty: int
    price: Decimal
    gross: Decimal
    brokerage: Decimal
    net: Decimal  # buy: cost incl. brokerage; sell: proceeds less brokerage
    exec_id: str


@dataclass(frozen=True)
class IncomeRow:
    fy: int
    kind: str  # DIVIDEND | SPECIAL | IN_SPECIE | DISTRIBUTION | WITHHOLDING
    code: str
    ex_date: date | None
    pay_date: date | None
    held: int
    cash: Decimal
    income: Decimal
    franked_pct: Decimal | None
    franking_credit: Decimal
    ref: str
    note: str = ""

    @property
    def franked(self) -> Decimal | None:
        return None if self.franked_pct is None else self.income * self.franked_pct / 100

    @property
    def unfranked(self) -> Decimal | None:
        f = self.franked
        return None if f is None else self.income - f


@dataclass(frozen=True)
class AdjustRow:
    fy: int
    day: date
    kind: str  # CAPITAL_RETURN | DEMERGER | IN_SPECIE | SPLIT | CODE_CHANGE | AMIT
    code: str
    pid: str
    qty_before: Decimal
    qty_after: Decimal
    cost_before: Decimal
    cost_after: Decimal
    ref: str
    note: str = ""


@dataclass
class TaxEngine:
    """Parcels in time order; every sale matched to parcels by the method."""

    params: TaxParams
    parcels: list[Parcel] = field(default_factory=list)
    cgt: list[CgtRow] = field(default_factory=list)
    trades: list[TradeRow] = field(default_factory=list)
    income: list[IncomeRow] = field(default_factory=list)
    adjust: list[AdjustRow] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    # -- helpers
    def open_of(self, code: str) -> list[Parcel]:
        return [p for p in self.parcels if p.code == code and p.qty > 0]

    def _new(
        self, code: str, d: date, qty: Decimal, cost: Decimal, brk: Decimal, origin: str, tr: str
    ) -> Parcel:
        p = Parcel(f"P{len(self.parcels) + 1:04d}", code, d, qty, cost, brk, origin, tr)
        self.parcels.append(p)
        return p

    def _row(
        self,
        event: str,
        p: Parcel | None,
        code: str,
        d: date,
        qty: Decimal,
        cost: Decimal,
        proceeds: Decimal,
        ref: str,
        note: str = "",
    ) -> None:
        days = (d - p.acquired).days if p is not None else None
        long = days is not None and days >= self.params.discount_days
        near = days is not None and NEAR_LINE_DAYS <= days < self.params.discount_days
        self.cgt.append(
            CgtRow(
                fy_of(d),
                event,
                code,
                p.pid if p else "-",
                p.acquired if p else None,
                d,
                qty,
                cost,
                proceeds,
                days,
                long,
                near,
                ref,
                note,
            )
        )

    def _order(self, code: str, per_share: Decimal, d: date) -> list[Parcel]:
        ps = sorted(self.open_of(code), key=lambda p: (p.acquired, p.pid))
        if self.params.method == "FIFO":
            return ps

        def key(p: Parcel) -> tuple[int, Decimal]:
            unit = p.cost / p.qty
            if unit > per_share:
                return (0, -unit)  # losses first, the biggest first
            if (d - p.acquired).days >= self.params.discount_days:
                return (1, -unit)  # then discount-eligible gains
            return (2, -unit)  # then the highest-cost short-term parcel

        return sorted(ps, key=key)

    # -- events
    def buy(self, f: FillRecord, code: str, k: Decimal) -> None:
        d = sydney_date(f.executed_at)
        gross = f.price * f.qty
        self.trades.append(
            TradeRow(
                fy_of(d),
                d,
                f.entity,
                "BUY",
                f.qty,
                f.price,
                gross,
                f.commission,
                gross + f.commission,
                f.exec_id,
            )
        )
        self._new(
            code, d, f.qty * k, gross + f.commission, f.commission, f"BUY {f.exec_id}", f.entity
        )

    def sell(self, f: FillRecord, code: str, k: Decimal) -> None:
        d = sydney_date(f.executed_at)
        gross = f.price * f.qty
        net = gross - f.commission
        self.trades.append(
            TradeRow(
                fy_of(d), d, f.entity, "SELL", f.qty, f.price, gross, f.commission, net, f.exec_id
            )
        )
        self.dispose(code, f.qty * k, net, d, "SALE", f.exec_id)

    def dispose(
        self, code: str, qty: Decimal, proceeds: Decimal, d: date, event: str, ref: str
    ) -> None:
        if qty <= 0:
            return
        left, given = qty, ZERO
        for p in self._order(code, proceeds / qty, d):
            if left <= 0:
                break
            t = min(left, p.qty)
            c = p.cost * t / p.qty
            left -= t
            pr = proceeds - given if left <= 0 else proceeds * t / qty
            given += pr
            p.qty -= t
            p.cost -= c
            if p.qty <= 0:
                p.qty, p.cost, p.closed = ZERO, ZERO, d
            self._row(event, p, code, d, t, c, pr, ref)
        if left > 0:
            self._row(
                event,
                None,
                code,
                d,
                left,
                ZERO,
                proceeds - given,
                ref,
                "no parcel found for these shares: journal incomplete",
            )
            self.flags.append(f"{ref}: {qty_s(left)} {code} sold without a parcel in the journal")

    def reduce_cost(
        self, code: str, amount: Decimal, d: date, kind: str, ref: str, event: str
    ) -> None:
        """A capital return (or AMIT decrease) of ``amount`` over the open parcels by
        quantity; any part above a parcel's cost base is a capital gain (G1 / E10)."""
        ps = self.open_of(code)
        tot = sum((p.qty for p in ps), ZERO)
        if tot <= 0:
            self.flags.append(f"{ref}: {kind} of {code} with no parcel held")
            return
        for p in ps:
            share = amount * p.qty / tot
            cut = min(share, p.cost)
            self.adjust.append(
                AdjustRow(fy_of(d), d, kind, code, p.pid, p.qty, p.qty, p.cost, p.cost - cut, ref)
            )
            p.cost -= cut
            p.adjusted -= cut
            if share > cut:
                self._row(
                    event,
                    p,
                    code,
                    d,
                    p.qty,
                    ZERO,
                    share - cut,
                    ref,
                    "reduction above the cost base",
                )

    def increase_cost(self, code: str, amount: Decimal, d: date, ref: str) -> None:
        ps = self.open_of(code)
        tot = sum((p.qty for p in ps), ZERO)
        if tot <= 0:
            self.flags.append(f"{ref}: AMIT increase of {code} with no units held")
            return
        for p in ps:
            add = amount * p.qty / tot
            self.adjust.append(
                AdjustRow(
                    fy_of(d),
                    d,
                    "AMIT",
                    code,
                    p.pid,
                    p.qty,
                    p.qty,
                    p.cost,
                    p.cost + add,
                    ref,
                    "AMIT cost base increase",
                )
            )
            p.cost += add
            p.adjusted += add

    def rescale(self, code: str, new_total: Decimal, d: date, kind: str, ref: str) -> None:
        """A split / consolidation: the parcels' counts scaled to ``new_total`` (whole
        shares, the remainder on the last parcel), cost bases unchanged."""
        ps = sorted(self.open_of(code), key=lambda p: (p.acquired, p.pid))
        tot = sum((p.qty for p in ps), ZERO)
        if tot <= 0:
            return
        done = ZERO
        for i, p in enumerate(ps):
            q = (
                new_total - done
                if i == len(ps) - 1
                else (p.qty * new_total / tot).quantize(Decimal(1))
            )
            done += q
            self.adjust.append(
                AdjustRow(
                    fy_of(d),
                    d,
                    kind,
                    code,
                    p.pid,
                    p.qty,
                    q,
                    p.cost,
                    p.cost,
                    ref,
                    "count changed, cost base kept",
                )
            )
            p.qty = q

    def booking(self, b: Booking, code: str, new_code: str | None) -> None:  # noqa: PLR0912
        d = b.ex_date or b.pay_date
        if d is None:
            self.flags.append(f"{b.key}: corporate action without a date")
            return
        pay = b.pay_date or d
        if b.kind in (CaKind.DIVIDEND, CaKind.SPECIAL, CaKind.WITHHOLDING):
            kind = b.kind.value
            if code in self.params.fund_codes and b.kind is not CaKind.WITHHOLDING:
                kind = "DISTRIBUTION"
            self.income.append(
                IncomeRow(
                    fy_of(pay),
                    kind,
                    code,
                    b.ex_date,
                    b.pay_date,
                    b.held,
                    b.cash,
                    b.income,
                    b.franked_pct,
                    b.franking_credit,
                    b.key,
                    b.note[:120],
                )
            )
        elif b.kind is CaKind.CAPITAL_RETURN:
            self.reduce_cost(code, b.cost_reduction, d, "CAPITAL_RETURN", b.key, "G1")
        elif b.kind is CaKind.IN_SPECIE:
            self.income.append(
                IncomeRow(
                    fy_of(pay),
                    "IN_SPECIE",
                    code,
                    b.ex_date,
                    b.pay_date,
                    b.held,
                    b.cash,
                    b.income,
                    b.franked_pct,
                    b.franking_credit,
                    b.key,
                    b.note[:120],
                )
            )
            if b.cost_reduction:
                self.reduce_cost(code, b.cost_reduction, d, "IN_SPECIE", b.key, "G1")
            if new_code and b.new_shares:
                cost = b.child_cost if b.child_cost is not None else ZERO
                if b.child_cost is None:
                    self.flags.append(f"{b.key}: in-specie {new_code} without a value (cost 0)")
                p = self._new(
                    new_code, d, Decimal(b.new_shares), cost, ZERO, f"IN_SPECIE {b.key}", new_code
                )
                self.adjust.append(
                    AdjustRow(
                        fy_of(d),
                        d,
                        "IN_SPECIE",
                        new_code,
                        p.pid,
                        ZERO,
                        p.qty,
                        ZERO,
                        cost,
                        b.key,
                        f"received from {code}; acquired {d}",
                    )
                )
        elif b.kind is CaKind.DEMERGER:
            self.demerge(b, code, new_code, d)
        elif b.kind is CaKind.SPLIT:
            tot = sum((p.qty for p in self.open_of(code)), ZERO)
            self.rescale(code, tot + b.qty_change, d, "SPLIT", b.key)
        elif b.kind is CaKind.DISPOSAL:
            self.dispose(code, Decimal(-b.qty_change), b.cash, b.pay_date or d, "DISPOSAL", b.key)
        elif b.kind is CaKind.CODE_CHANGE:
            self.adjust.append(
                AdjustRow(
                    fy_of(d),
                    d,
                    "CODE_CHANGE",
                    b.code,
                    "-",
                    Decimal(b.held),
                    Decimal(b.held) * (b.ratio or 1),
                    ZERO,
                    ZERO,
                    b.key,
                    f"now {b.new_code}; cost base and dates kept",
                )
            )
            tot = sum((p.qty for p in self.open_of(code)), ZERO)
            frac = tot - tot.to_integral_value(ROUND_FLOOR)
            if frac > 0:  # the fraction left by the ratio goes for the cash in lieu
                self.dispose(code, frac, b.cash, pay, "CASH_IN_LIEU", b.key)
                return
        if b.kind in (CaKind.CASH_IN_LIEU, CaKind.CODE_CHANGE, CaKind.SPLIT) and b.cash:
            self._row(
                "CASH_IN_LIEU",
                None,
                code,
                pay,
                ZERO,
                ZERO,
                b.cash,
                b.key,
                "cash for a fraction of a share; its small cost base not separated",
            )
            self.flags.append(
                f"{b.key}: cash in lieu A${m2(b.cash)} of {code}: accountant to confirm treatment"
            )
        if b.tax_class:
            self.flags.append(f"{b.key} {b.kind.value} {b.code}: {b.tax_class} (confirm figures)")

    def demerge(self, b: Booking, code: str, new_code: str | None, d: date) -> None:
        ps = sorted(self.open_of(code), key=lambda p: (p.acquired, p.pid))
        tot = sum((p.qty for p in ps), ZERO)
        if new_code is None or not b.new_shares or tot <= 0:
            self.flags.append(f"{b.key}: demerger of {code} with nothing held or received")
            return
        pct = b.cost_moved_pct or ZERO
        done = 0
        for i, p in enumerate(ps):
            n = b.new_shares - done if i == len(ps) - 1 else int(b.new_shares * p.qty / tot)
            done += n
            moved = b.child_cost * p.qty / tot if b.child_cost is not None else p.cost * pct
            before = p.cost
            if b.child_cost is None:
                p.cost -= moved
                p.adjusted -= moved
            self.adjust.append(
                AdjustRow(
                    fy_of(d),
                    d,
                    "DEMERGER",
                    code,
                    p.pid,
                    p.qty,
                    p.qty,
                    before,
                    p.cost,
                    b.key,
                    f"{pct * 100:.4f}% of the cost base to {new_code}",
                )
            )
            c = self._new(
                new_code,
                p.acquired,
                Decimal(n),
                moved,
                ZERO,
                f"DEMERGER {b.key} from {p.pid}",
                new_code,
            )
            self.adjust.append(
                AdjustRow(
                    fy_of(d),
                    d,
                    "DEMERGER",
                    new_code,
                    c.pid,
                    ZERO,
                    c.qty,
                    ZERO,
                    moved,
                    b.key,
                    f"from {code} {p.pid}; acquisition date {p.acquired} kept (demerger roll-over)",
                )
            )

    def amit(self, e: AmitEntry, d: date) -> None:
        ref = f"AMIT {e.code} {fy_label(e.fy)}"
        if e.increase:
            self.increase_cost(e.code, e.increase, d, ref)
        if e.decrease:
            self.reduce_cost(e.code, e.decrease, d, "AMIT", ref, "E10")


def run_engine(
    j: Journal, book: str, params: TaxParams, until: date, amit: Sequence[AmitEntry] = ()
) -> TaxEngine:
    """Fills, corporate actions and AMIT entries of ``book`` up to the end of ``until``
    in time order (a corporate action at the start of its ex-date, before that day's
    trades; an AMIT adjustment at the end of 30 June of its year)."""
    m = j.identity_ratios()
    eng = TaxEngine(params)
    end = _at(until + timedelta(days=1))
    stream: list[tuple[datetime, int, object]] = []
    for i, f in enumerate(j.fills(book)):
        t = f.executed_at if f.executed_at.tzinfo else f.executed_at.replace(tzinfo=UTC)
        stream.append((t, i, f))
    for i, b in enumerate(j.ca_bookings(book)):
        d = b.ex_date or b.pay_date
        stream.append((_at(d) if d else datetime.min.replace(tzinfo=UTC), -1_000_000 + i, b))
    for i, e in enumerate(amit):
        stream.append((_at(date(e.fy + 1, 6, 30), 23, 59, 59), 1_000_000 + i, e))
    for t, _, x in sorted(stream, key=lambda s: (s[0], s[1])):
        if t >= end:
            continue
        if isinstance(x, FillRecord):
            code, k = m.get(x.entity, (x.entity, Decimal(1)))
            (eng.buy if x.side is Side.BUY else eng.sell)(x, code, k)
        elif isinstance(x, Booking):
            code = m.get(x.code, (x.code, Decimal(1)))[0]
            new = m.get(x.new_code, (x.new_code, Decimal(1)))[0] if x.new_code else None
            eng.booking(x, code, new)
        elif isinstance(x, AmitEntry):
            eng.amit(x, date(x.fy + 1, 6, 30))
    return eng


# ---------------------------------------------------------------------------
# Capital gains summary (losses, carry-forward, discount)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CgtSummary:
    short_gains: Decimal
    long_gains: Decimal  # discount eligible, before the discount
    losses: Decimal  # this year's capital losses (positive number)
    carried_in: Decimal
    applied_short: Decimal
    applied_long: Decimal
    discount: Decimal
    net_gain: Decimal
    carried_out: Decimal


def summarise(rows: Iterable[CgtRow], carried_in: Decimal) -> CgtSummary:
    """Losses (this year's, then carried in) against short-term gains first, then
    against discount-eligible gains; the 50% discount on what is left of those."""
    rs = list(rows)
    short = sum((r.gain for r in rs if r.gain > 0 and not r.long), ZERO)
    long = sum((r.gain for r in rs if r.gain > 0 and r.long), ZERO)
    losses = -sum((r.gain for r in rs if r.gain < 0), ZERO)
    pool = losses + carried_in
    a_s = min(pool, short)
    pool -= a_s
    a_l = min(pool, long)
    pool -= a_l
    disc = (long - a_l) * DISCOUNT
    net = short - a_s + long - a_l - disc
    return CgtSummary(short, long, losses, carried_in, a_s, a_l, disc, net, pool)


# ---------------------------------------------------------------------------
# Reconciliation with IBKR Flex
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconLine:
    area: str  # TRADE | TOTAL | CASH | CORPORATE_ACTION | POSITION | COVERAGE
    ref: str
    journal: str
    flex: str
    status: str  # OK | DIFF | MISSING_IN_FLEX | MISSING_IN_JOURNAL | NOT_BOOKED | INFO
    note: str = ""

    @property
    def problem(self) -> bool:
        return self.status not in ("OK", "INFO")


def _cash_day(c: FlexCashTransaction) -> date | None:
    d = c.settle_date or c.pay_date or c.report_date
    if d is None and c.date_time:
        s = c.date_time.split(";")[0].replace("-", "")
        d = date(int(s[:4]), int(s[4:6]), int(s[6:8])) if len(s) >= 8 else None
    return d


_DIV_TYPES = ("dividends", "payment in lieu of dividends")


def reconcile_flex(  # noqa: PLR0912, PLR0915 - one block per record kind
    j: Journal,
    book: str,
    statements: Sequence[FlexStatement],
    start: date,
    end: date,
    account_id: str | None = None,
) -> list[ReconLine]:
    """The journal's year against IBKR's Activity Flex records, every difference listed."""
    out: list[ReconLine] = []
    other = sorted({s.account_id for s in statements if account_id and s.account_id != account_id})
    if other:
        out.append(
            ReconLine(
                "COVERAGE",
                "accounts",
                account_id or "",
                ",".join(other),
                "INFO",
                "statements of other accounts ignored",
            )
        )
    sts = [s for s in statements if not account_id or s.account_id == account_id]
    if not sts:
        return [
            *out,
            ReconLine(
                "COVERAGE",
                "statements",
                "",
                "none",
                "DIFF",
                "no IBKR Flex statement found: nothing reconciled",
            ),
        ]
    first = min(s.from_date for s in sts)
    last = max(s.to_date for s in sts)
    out.append(
        ReconLine(
            "COVERAGE", "statements", "", f"{first}..{last}", "INFO", f"{len(sts)} statement(s)"
        )
    )
    if last < end:
        out.append(
            ReconLine(
                "COVERAGE",
                "year end",
                str(end),
                str(last),
                "INFO",
                "IBKR's records end before 30 June: the year is not complete",
            )
        )
    # trades (one row per IBKR execution id; overlapping statements repeat rows)
    ft = {t.exec_id: t for s in sts for t in s.trades if start <= t.trade_date <= end}
    jf = {f.exec_id: f for f in j.fills(book) if start <= sydney_date(f.executed_at) <= end}
    for x in sorted(set(ft) | set(jf)):
        f, t = jf.get(x), ft.get(x)
        if t is None:
            assert f is not None
            out.append(
                ReconLine(
                    "TRADE",
                    x,
                    f"{f.side.value} {f.qty} {f.entity} @ {f.price}",
                    "",
                    "MISSING_IN_FLEX",
                    "in the journal, not in IBKR's records",
                )
            )
            continue
        if f is None:
            out.append(
                ReconLine(
                    "TRADE",
                    x,
                    "",
                    f"{t.side} {qty_s(t.quantity)} {t.symbol} @ {t.price}",
                    "MISSING_IN_JOURNAL",
                    "in IBKR's records, not in the journal",
                )
            )
            continue
        diffs = []
        if (f.side.value, Decimal(f.qty), f.entity) != (t.side, t.quantity, t.symbol):
            diffs.append("side/quantity/code")
        if f.price != t.price:
            diffs.append("price")
        if (f.commission - abs(t.commission)).copy_abs() >= CENT:
            diffs.append("brokerage")
        if diffs:
            out.append(
                ReconLine(
                    "TRADE",
                    x,
                    f"{f.side.value} {f.qty} {f.entity} @ {f.price} brk {f.commission}",
                    f"{t.side} {qty_s(t.quantity)} {t.symbol} @ {t.price} brk {abs(t.commission)}",
                    "DIFF",
                    ", ".join(diffs),
                )
            )
    for label, side in (("buys (gross)", "BUY"), ("sells (gross)", "SELL")):
        a = sum((f.price * f.qty for f in jf.values() if f.side.value == side), ZERO)
        b = sum((t.price * t.quantity for t in ft.values() if t.side == side), ZERO)
        out.append(_total("TOTAL", label, a, b))
    a = sum((f.commission for f in jf.values()), ZERO)
    b = sum((abs(t.commission) for t in ft.values()), ZERO)
    out.append(_total("TOTAL", "brokerage", a, b))
    # cash transactions
    fc = {c.transaction_id: c for s in sts for c in s.cash_transactions}
    fc = {k: c for k, c in fc.items() if (d := _cash_day(c)) is not None and start <= d <= end}
    keys = {b.key: b for b in j.ca_bookings(book)}
    by_type: dict[str, list[Decimal]] = {}
    for tx, c in sorted(fc.items()):
        ty = c.type.strip().lower()
        by_type.setdefault(c.type.strip() or "?", []).append(c.amount)
        if (ty in _DIV_TYPES or ty == "withholding tax") and f"FLEX:CT:{tx}" not in keys:
            out.append(
                ReconLine(
                    "CASH",
                    f"{c.type} {tx}",
                    "",
                    f"{c.symbol} {c.amount}",
                    "MISSING_IN_JOURNAL",
                    "not yet booked: the next 16:30 run books it",
                )
            )
    jdiv = [
        b
        for b in keys.values()
        if b.key.startswith("FLEX:CT:")
        and b.kind is not CaKind.WITHHOLDING
        and start <= (b.pay_date or b.ex_date or end) <= end
    ]
    jwh = [
        b
        for b in keys.values()
        if b.kind is CaKind.WITHHOLDING and start <= (b.pay_date or b.ex_date or end) <= end
    ]
    fdiv = sum((c.amount for c in fc.values() if c.type.strip().lower() in _DIV_TYPES), ZERO)
    fwh = sum((c.amount for c in fc.values() if c.type.strip().lower() == "withholding tax"), ZERO)
    out.append(
        _total("CASH", "dividends and distributions", sum((b.cash for b in jdiv), ZERO), fdiv)
    )
    out.append(_total("CASH", "withholding tax", sum((b.cash for b in jwh), ZERO), fwh))
    dep = sum(
        (
            Decimal(str(r["amount"]))
            for r in j.cash_moves_of(book)
            if r["kind"] in ("DEPOSIT", "WITHDRAWAL") and start <= sydney_date(r["at"]) <= end
        ),
        ZERO,
    )
    fdep = sum(
        (c.amount for c in fc.values() if c.type.strip().lower() == "deposits/withdrawals"), ZERO
    )
    out.append(_total("CASH", "deposits and withdrawals", dep, fdep))
    for ty, amts in sorted(by_type.items()):
        if ty.lower() in (*_DIV_TYPES, "withholding tax", "deposits/withdrawals"):
            continue
        out.append(
            ReconLine(
                "CASH",
                ty,
                "not booked",
                m2(sum(amts, ZERO)),
                "NOT_BOOKED",
                "IBKR cash item the journal does not book (interest, fees...): "
                "give it to the accountant",
            )
        )
    # corporate actions
    aids = {
        ca.action_id: ca
        for s in sts
        for ca in s.corporate_actions
        if ca.report_date is None or start <= ca.report_date <= end
    }
    for aid, ca in sorted(aids.items()):
        st = "OK" if f"FLEX:CA:{aid}" in keys else "MISSING_IN_JOURNAL"
        out.append(
            ReconLine(
                "CORPORATE_ACTION",
                aid,
                "booked" if st == "OK" else "",
                f"{ca.type} {ca.symbol} {qty_s(ca.quantity)}",
                st,
                ca.description[:80],
            )
        )
    # positions at the last statement of the year that carries them
    pst = [s for s in sts if s.positions and s.to_date <= end]
    if pst:
        s = max(pst, key=lambda x: x.to_date)
        fpos: dict[str, int] = {}
        for p in s.positions:
            if p.asset_category in ("STK", ""):
                fpos[p.symbol] = fpos.get(p.symbol, 0) + int(p.position)
        fpos = j.map_codes(fpos)
        jpos = j.positions(book, before=_at(s.to_date + timedelta(days=1)))
        for code in sorted(set(fpos) | set(jpos)):
            a_, b_ = jpos.get(code, 0), fpos.get(code, 0)
            out.append(
                ReconLine(
                    "POSITION",
                    f"{code} at {s.to_date}",
                    str(a_),
                    str(b_),
                    "OK" if a_ == b_ else "DIFF",
                )
            )
    else:
        out.append(
            ReconLine(
                "POSITION",
                "positions",
                "",
                "",
                "INFO",
                "no Flex statement of the year has an Open Positions section",
            )
        )
    return out


def _total(area: str, ref: str, a: Decimal, b: Decimal) -> ReconLine:
    ok = (a - b).copy_abs() < CENT
    return ReconLine(
        area, ref, m2(a), m2(b), "OK" if ok else "DIFF", "" if ok else f"difference {m2(a - b)}"
    )


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaxReport:
    book: str
    fy: str
    start: date
    end: date
    params: TaxParams
    paper: bool
    parcels: tuple[Parcel, ...]
    cgt: tuple[CgtRow, ...]
    trades: tuple[TradeRow, ...]
    income: tuple[IncomeRow, ...]
    adjust: tuple[AdjustRow, ...]
    summary: CgtSummary
    recon: tuple[ReconLine, ...]
    amit_missing: tuple[str, ...]
    amit_entered: tuple[AmitEntry, ...]
    flags: tuple[str, ...]

    def totals(self) -> dict[str, Decimal | None]:
        inc = [r for r in self.income if r.kind in ("DIVIDEND", "SPECIAL", "IN_SPECIE")]
        known = [r for r in inc if r.franked_pct is not None]
        dist = [r for r in self.income if r.kind == "DISTRIBUTION"]
        return {
            "dividends": sum((r.income for r in inc if r.kind != "SPECIAL"), ZERO),
            "specials": sum((r.income for r in inc if r.kind == "SPECIAL"), ZERO),
            "franked": sum((r.franked or ZERO for r in known), ZERO),
            "unfranked": sum((r.unfranked or ZERO for r in known), ZERO),
            "franking_not_known": sum((r.income for r in inc if r.franked_pct is None), ZERO),
            "franking_credits": sum((r.franking_credit for r in known), ZERO),
            "withholding": sum((r.cash for r in self.income if r.kind == "WITHHOLDING"), ZERO),
            "distributions": sum((r.cash for r in dist), ZERO),
            "capital_returns": -sum(
                (a.cost_after - a.cost_before for a in self.adjust if a.kind == "CAPITAL_RETURN"),
                ZERO,
            ),
            "brokerage_buys": sum((t.brokerage for t in self.trades if t.side == "BUY"), ZERO),
            "brokerage_sells": sum((t.brokerage for t in self.trades if t.side == "SELL"), ZERO),
        }


def build_report(
    j: Journal,
    book: str,
    fy: str,
    params: TaxParams,
    statements: Sequence[FlexStatement] | None = None,
    amit: Sequence[AmitEntry] = (),
    prior_losses: Decimal = ZERO,
    account_id: str | None = None,
    paper: bool = True,
) -> TaxReport:
    start, end, label = fy_bounds(fy)
    eng = run_engine(j, book, params, end, amit)
    y = start.year
    first = min([r.fy for r in eng.cgt] + [y])
    carried = prior_losses
    for yy in range(first, y):
        carried = summarise([r for r in eng.cgt if r.fy == yy], carried).carried_out
    rows = tuple(r for r in eng.cgt if r.fy == y)
    summ = summarise(rows, carried)
    parcels = tuple(
        p
        for p in eng.parcels
        if p.acquired <= end
        and (p.closed is None or p.closed >= start)
        and (p.qty > 0 or any(r.pid == p.pid for r in rows) or p.closed is not None)
    )
    funds = sorted(params.fund_codes)
    entered = tuple(e for e in amit if e.fy == y)
    missing = tuple(
        c
        for c in funds
        if not any(e.code == c for e in entered)
        and (any(p.code == c for p in parcels) or any(r.code == c for r in eng.income if r.fy == y))
    )
    recon: tuple[ReconLine, ...] = ()
    if statements is not None:
        recon = tuple(reconcile_flex(j, book, statements, start, end, account_id))
    flags = list(eng.flags)
    flags += [
        f"parcels v journal at 30 June: {x}"
        for x in holdings_check(parcels, j.positions(book, before=_at(end + timedelta(days=1))))
    ]
    flags += [f"{c}: AMIT cost base adjustment for {label}: {AMIT_MANUAL}" for c in missing]
    flags += [
        f"{r.pid} {r.code} sold {r.disposed}: held {r.days_held} days, near the 12-month line"
        " (marked short-term by the 367-day margin): check the exact dates"
        for r in rows
        if r.near_line
    ]
    return TaxReport(
        book,
        label,
        start,
        end,
        params,
        paper,
        parcels,
        rows,
        tuple(t for t in eng.trades if t.fy == y),
        tuple(r for r in eng.income if r.fy == y),
        tuple(a for a in eng.adjust if a.fy == y),
        summ,
        recon,
        missing,
        entered,
        tuple(flags),
    )


# ---------------------------------------------------------------------------
# Output: CSV files and the markdown summary
# ---------------------------------------------------------------------------


def _d(x: date | None) -> str:
    return x.isoformat() if x else ""


def _opt(x: Decimal | None) -> str:
    return "not known" if x is None else m2(x)


def write_report(r: TaxReport, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pre = out_dir / f"tax_{r.book}_FY{r.fy}"
    files: list[Path] = []

    def put(suffix: str, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
        p = Path(f"{pre}_{suffix}.csv")
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    f"# {NOT_ADVICE} Book {r.book}, FY {r.fy} ({r.start}..{r.end})"
                    + (" PAPER ACCOUNT" if r.paper else "")
                ]
            )
            w.writerow(header)
            w.writerows(rows)
        files.append(p)

    sold = {p.pid: [c for c in r.cgt if c.pid == p.pid] for p in r.parcels}
    put(
        "parcels",
        [
            "parcel",
            "code",
            "traded_as",
            "acquired",
            "origin",
            "qty_acquired",
            "cost_incl_brokerage",
            "purchase_brokerage",
            "qty_sold_in_year",
            "cost_base_sold",
            "proceeds_in_year",
            "gain_loss_in_year",
            "qty_held_30_june",
            "cost_base_30_june",
            "cost_base_adjustments_to_date",
        ],
        [
            [
                p.pid,
                p.code,
                p.traded_as,
                _d(p.acquired),
                p.origin,
                qty_s(p.qty0),
                m2(p.cost0),
                m2(p.brokerage),
                qty_s(sum((c.qty for c in sold[p.pid]), ZERO)),
                m2(sum((c.cost_base for c in sold[p.pid]), ZERO)),
                m2(sum((c.proceeds for c in sold[p.pid]), ZERO)),
                m2(sum((c.gain for c in sold[p.pid]), ZERO)),
                qty_s(p.qty),
                m2(p.cost),
                m2(p.adjusted),
            ]
            for p in r.parcels
        ],
    )
    put(
        "capital_gains",
        [
            "event",
            "code",
            "parcel",
            "acquired",
            "disposed",
            "qty",
            "cost_base",
            "proceeds",
            "gain_loss",
            "days_held",
            "term",
            "note",
            "ref",
        ],
        [
            [
                c.event,
                c.code,
                c.pid,
                _d(c.acquired),
                _d(c.disposed),
                qty_s(c.qty),
                m2(c.cost_base),
                m2(c.proceeds),
                m2(c.gain),
                "" if c.days_held is None else c.days_held,
                ("DISCOUNT_ELIGIBLE" if c.long else "SHORT_TERM")
                + ("_NEAR_12_MONTHS" if c.near_line else ""),
                c.note,
                c.ref,
            ]
            for c in r.cgt
        ],
    )
    put(
        "trades",
        [
            "date",
            "code",
            "side",
            "qty",
            "price",
            "gross",
            "brokerage",
            "net_cost_or_proceeds",
            "ibkr_exec_id",
        ],
        [
            [
                _d(t.day),
                t.code,
                t.side,
                t.qty,
                f"{t.price.normalize():f}",
                m2(t.gross),
                m2(t.brokerage),
                m2(t.net),
                t.exec_id,
            ]
            for t in r.trades
        ],
    )
    put(
        "income",
        [
            "kind",
            "code",
            "ex_date",
            "pay_date",
            "shares",
            "cash",
            "assessable",
            "franked_pct",
            "franked",
            "unfranked",
            "franking_credit",
            "note",
            "ref",
        ],
        [
            [
                i.kind,
                i.code,
                _d(i.ex_date),
                _d(i.pay_date),
                i.held,
                m2(i.cash),
                m2(i.income),
                _opt(i.franked_pct) if i.kind != "DISTRIBUTION" else AMIT_MANUAL,
                _opt(i.franked),
                _opt(i.unfranked),
                m2(i.franking_credit),
                i.note,
                i.ref,
            ]
            for i in r.income
        ],
    )
    amit_rows = [
        [_d(r.end), "AMIT", c, "-", "", "", "", "", AMIT_MANUAL, "NOT ENTERED"]
        for c in r.amit_missing
    ]
    put(
        "cost_base_changes",
        [
            "date",
            "kind",
            "code",
            "parcel",
            "qty_before",
            "qty_after",
            "cost_before",
            "cost_after",
            "note",
            "ref",
        ],
        [
            *(
                [
                    _d(a.day),
                    a.kind,
                    a.code,
                    a.pid,
                    qty_s(a.qty_before),
                    qty_s(a.qty_after),
                    m2(a.cost_before),
                    m2(a.cost_after),
                    a.note,
                    a.ref,
                ]
                for a in r.adjust
            ),
            *amit_rows,
        ],
    )
    put(
        "reconciliation",
        ["area", "item", "journal", "ibkr_flex", "status", "note"],
        [[x.area, x.ref, x.journal, x.flex, x.status, x.note] for x in r.recon],
    )
    md = Path(f"{pre}_summary.md")
    md.write_text(render_summary(r, [p.name for p in files]), encoding="utf-8")
    return [*files, md]


def render_summary(r: TaxReport, files: Sequence[str] = ()) -> str:
    t = r.totals()
    s = r.summary
    method = (
        "FIFO (first in, first out: the oldest parcel is sold first)"
        if r.params.method == "FIFO"
        else "min_tax (specific identification: loss parcels first, then discount-eligible "
        "gains, then the highest-cost short-term parcel)"
    )
    lines = [
        f"# Tax report FY {r.fy} (1 July {r.start.year} - 30 June {r.end.year}), book {r.book}",
        "",
        f"**{NOT_ADVICE}** Prepared by the trading system from its journal for the owner's "
        "accountant, who decides the treatment of every item. It covers this IBKR account "
        "only; other investments and the owner's own carried-forward losses are added by the "
        "accountant.",
        "",
    ]
    if r.paper:
        lines += [
            "**PAPER ACCOUNT**: simulated trades in IBKR's paper account. No real money, "
            "nothing to declare; this run checks the report's format and arithmetic.",
            "",
        ]
    lines += [
        "## How the figures are worked out",
        "",
        f"- Parcel matching: **{method}**. Specific identification of parcels is also "
        "possible for shares when the records show which parcel was sold; the owner should "
        "confirm the method with the accountant before the first real sale "
        "(config `tax.parcel_method`).",
        "- Cost base = price x quantity + purchase brokerage; proceeds = price x quantity "
        "less sale brokerage. Dates are Sydney trade (contract) dates, not settlement dates.",
        f"- 12-month discount: a parcel held **{r.params.discount_days} days or more** is marked "
        'discount eligible. The ATO test is "at least 12 months" (not counting the days of '
        f"purchase and sale); the record uses {r.params.discount_days} days as a safety "
        "margin, so a parcel held 365-366 days is marked short-term and flagged for a check.",
        "- Losses are taken off short-term gains first, then off discount-eligible gains; "
        "the 50% discount (individuals) applies to what is left of the latter.",
        "- Capital returns lower the parcel's cost base (above it: a capital gain, CGT event "
        "G1). Demerged shares take the share of the cost base the company / ATO ruling gives "
        "and keep the original acquisition date (demerger roll-over: accountant to confirm "
        "the choice). Splits and code changes keep cost bases and dates.",
        "",
        "## Capital gains (this account)",
        "",
        "| Item | A$ |",
        "| --- | ---: |",
        f"| Short-term gains (held < {r.params.discount_days} days) | {m2(s.short_gains)} |",
        f"| Discount-eligible gains (before discount) | {m2(s.long_gains)} |",
        f"| Capital losses this year | {m2(s.losses)} |",
        f"| Losses carried in (earlier years of this book + entered) | {m2(s.carried_in)} |",
        f"| Losses applied to short-term / discount-eligible gains | {m2(s.applied_short)} / "
        f"{m2(s.applied_long)} |",
        f"| 50% discount | {m2(s.discount)} |",
        f"| **Net capital gain** | **{m2(s.net_gain)}** |",
        f"| **Net capital loss carried forward** | **{m2(s.carried_out)}** |",
        "",
        f"Sales: {sum(1 for c in r.cgt if c.event == 'SALE')} parcel slices; parcels in the "
        f"year: {len(r.parcels)}.",
        "",
        "## Dividends",
        "",
        "| Item | A$ |",
        "| --- | ---: |",
        f"| Dividends (incl. in-specie income) | {m2(t['dividends'] or ZERO)} |",
        f"| Special dividends | {m2(t['specials'] or ZERO)} |",
        f"| Franked amount | {m2(t['franked'] or ZERO)} |",
        f"| Unfranked amount | {m2(t['unfranked'] or ZERO)} |",
        f"| Franking not known (not counted above) | {m2(t['franking_not_known'] or ZERO)} |",
        f"| Franking credits (where known) | {m2(t['franking_credits'] or ZERO)} |",
        f"| Withholding tax | {m2(t['withholding'] or ZERO)} |",
        "",
        f"45-day rule: the small-shareholder exemption applies when the owner's franking "
        f"credits from all holdings are under A${SMALL_SHAREHOLDER_CREDITS:,} for the year "
        f"(this account: A${m2(t['franking_credits'] or ZERO)}); the accountant checks.",
        "",
        "## Fund distributions",
        "",
        f"Funds: {', '.join(sorted(r.params.fund_codes)) or 'none'}. Cash received: "
        f"A${m2(t['distributions'] or ZERO)}. Their components (franked / unfranked income, "
        "capital gains, foreign income, franking credits) and the AMIT cost base "
        f"adjustment are **{AMIT_MANUAL}** (each fund publishes it after 30 June).",
        "",
    ]
    for e in r.amit_entered:
        lines.append(
            f"- {e.code}: AMIT entered: cost base +A${m2(e.increase)} / -A${m2(e.decrease)}"
            + (f" ({e.note})" if e.note else "")
        )
    for c in r.amit_missing:
        lines.append(
            f"- {c}: AMIT cost base adjustment **NOT ENTERED** ({AMIT_MANUAL}: "
            "`tax.amit_csv`, then run the report again)"
        )
    kinds: dict[str, int] = {}
    for a in r.adjust:
        kinds[a.kind] = kinds.get(a.kind, 0) + 1
    lines += [
        "",
        "## Cost base changes",
        "",
        f"Capital returns (cost base reduced, not income): A${m2(t['capital_returns'] or ZERO)}. "
        "Rows: " + (", ".join(f"{k} {n}" for k, n in sorted(kinds.items())) or "none") + ".",
        "",
        "## Brokerage",
        "",
        f"Buys A${m2(t['brokerage_buys'] or ZERO)}, sells A${m2(t['brokerage_sells'] or ZERO)}, "
        f"total A${m2((t['brokerage_buys'] or ZERO) + (t['brokerage_sells'] or ZERO))} "
        "(already inside the cost bases and proceeds above; not a separate deduction).",
        "",
        "## Reconciliation with IBKR's records (Activity Flex)",
        "",
    ]
    if not r.recon:
        lines.append("Not run: no Flex statements given.")
    else:
        bad = [x for x in r.recon if x.problem]
        lines.append(
            "All checked items agree."
            if not bad
            else f"**{len(bad)} difference(s)** (file `reconciliation`):"
        )
        lines += [
            f"- {x.area} {x.ref}: journal {x.journal or '-'}, IBKR {x.flex or '-'} "
            f"({x.status}{'; ' + x.note if x.note else ''})"
            for x in bad[:20]
        ]
        if len(bad) > 20:
            lines.append(f"- ... and {len(bad) - 20} more")
    lines += ["", "## To confirm with the accountant", ""]
    lines += [f"- {f}" for f in r.flags] or ["- nothing flagged"]
    if files:
        lines += ["", "## Files", "", *[f"- `{f}`" for f in files]]
    lines += ["", f"_{NOT_ADVICE}_", ""]
    return "\n".join(lines)


def flex_statements(paths: Iterable[Path]) -> list[FlexStatement]:
    from trader.data.flex import parse_statements

    out: list[FlexStatement] = []
    for p in paths:
        out += parse_statements(p.read_bytes())
    return out


def holdings_check(parcels: Iterable[Parcel], positions: Mapping[str, int]) -> list[str]:
    """Parcels still held against the journal's positions (an internal check)."""
    held: dict[str, Decimal] = {}
    for p in parcels:
        if p.qty > 0:
            held[p.code] = held.get(p.code, ZERO) + p.qty
    out = []
    for c in sorted(set(held) | set(positions)):
        if int(held.get(c, ZERO)) != positions.get(c, 0):
            out.append(f"{c}: parcels {qty_s(held.get(c, ZERO))}, journal {positions.get(c, 0)}")
    return out
