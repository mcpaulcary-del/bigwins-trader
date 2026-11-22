"""Corporate actions of held names: dividends, capital returns, specials, demergers,
in-specie distributions and code changes (FD v3.0 §5.3 BW-UNI-20..23, §13 ledger
``dividends``, §14 BW-TAX-02; BF-D23..D25). PAPER ONLY. Pure: no I/O but the CSV read.

Two sources, one booking model:

* **Broker books** (the paper book; the live book later, same code) are booked from
  **IBKR's own records** only: the Activity Flex statement's cash transactions
  (``Dividends``, ``Payment In Lieu Of Dividends``, ``Withholding Tax``) and its
  corporate-action rows (``bookings_from_flex``). A calendar event (below) that IBKR has
  not yet reported is a *pending expectation*: it explains a reconciliation difference
  of the right size for a while (``expectations``), it is never booked from the calendar.
* **Simulated books** (the twin and its random twins) are booked from the **calendar**:
  the vendor's dividends merged with the record keeper's ``CORPORATE_ACTIONS.csv``,
  which overrides the vendor for the same code within a week (the vendor carries a
  capital return or a special as an ordinary dividend and has no in-specie or demerger
  rows). Cash and shares are booked on the ex-date (BW-UNI-23), on the holding at the
  close of the session before.

Tax classes (BW-TAX-02, ATO treatment as the build reads it; the tax agent confirms):

* ``DIVIDEND`` / ``SPECIAL``: assessable income; franked part and franking credit
  (``franked x 30/70``) counted when the franking percentage is known, else shown as
  "not counted";
* ``CAPITAL_RETURN``: not income; reduces the parcel's cost base; any excess over the
  cost base is a capital gain (CGT event G1), reported;
* ``DEMERGER`` (with roll-over, e.g. WOW -> EDV 2021, TAH -> TLC 2022): no income; the
  parent's cost base is apportioned to the new shares by the event's ``cost_base_pct``
  (the company's / ATO class ruling figure), else provisionally by market value on the
  ex-date, flagged until the figure is entered;
* ``IN_SPECIE`` (BHP -> WDS, PMV -> MYR): shares received as a distribution; the new
  shares' cost base is their value; the dividend part is income, the capital part
  reduces the parent's cost base (``capital_per_share``); without the split the event is
  booked ``UNCLASSIFIED`` for tax (cash and positions are exact either way);
* ``CODE_CHANGE``: a code (and share count, by ``ratio``) change of one company: the
  journal's identity map (``bf_identity`` with a ratio, BF-D19 / BF-D25), no booking
  effect; ``SPLIT`` a share-count change on the same code (a split, a consolidation;
  BF-D26: count x ratio, cost per share / ratio, the total cost base unchanged; the
  simulated books from the vendor's split rows or the CSV on the split date, the broker
  books from IBKR's Flex record); ``DISPOSAL`` shares removed for cash (a cash takeover,
  a buy-back); ``CASH_IN_LIEU`` cash for fractions.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path

from trader.data.flex import FlexCashTransaction, FlexCorporateAction, FlexStatement
from trader.reconcile import Expected

CENT = Decimal("0.01")
COMPANY_TAX_RATE = Decimal("0.30")  # franking credit gross-up; base-rate entities use 25%
TAKEOVER_NOTE = ("PROVISIONAL takeover - accountant to decide roll-over (Subdiv 124-M) and "
                 "apportion the cash")  # fmt: skip
OVERRIDE_DAYS = 7  # a CSV event replaces vendor dividends of the code within a week
CASH_MATCH_DAYS = 120  # a Flex cash row settles a calendar event with ex-date this far back
PENDING_DAYS = 60  # with no pay date: an expectation lasts this long after the ex-date
PENDING_GRACE_DAYS = 10  # after the pay date, IBKR's records have this long to arrive


class CaKind(StrEnum):
    DIVIDEND = "DIVIDEND"
    SPECIAL = "SPECIAL"
    CAPITAL_RETURN = "CAPITAL_RETURN"
    DEMERGER = "DEMERGER"
    IN_SPECIE = "IN_SPECIE"
    CODE_CHANGE = "CODE_CHANGE"
    SPLIT = "SPLIT"
    DISPOSAL = "DISPOSAL"
    CASH_IN_LIEU = "CASH_IN_LIEU"
    WITHHOLDING = "WITHHOLDING"


CASH_KINDS = frozenset({CaKind.DIVIDEND, CaKind.SPECIAL, CaKind.CAPITAL_RETURN})
SHARE_KINDS = frozenset({CaKind.DEMERGER, CaKind.IN_SPECIE})
COUNT_KINDS = frozenset({CaKind.SPLIT, CaKind.CODE_CHANGE})  # share count of one company
SPLIT_MATCH_DAYS = 10  # a Flex split row settles a calendar split this far around it


class CaError(ValueError):
    pass


@dataclass(frozen=True)
class CaEvent:
    """A calendar event (vendor, the record's CSV, or the owner): per share."""

    key: str
    kind: CaKind
    code: str
    ex_date: date
    pay_date: date | None = None
    per_share: Decimal | None = None  # cash per share; in-specie: value per share
    franked_pct: Decimal | None = None  # 0..100; None = unknown
    # tax F7: the company tax rate of the franking (0.30 or 0.25), from the statement;
    # None = not known: no franking credit is computed ("enter from statement")
    franking_rate: Decimal | None = None
    capital_per_share: Decimal | None = None  # in-specie: the capital-reduction part
    new_code: str | None = None
    ratio: Decimal | None = None  # new shares per parent share
    ratio_approx: bool = False
    cost_base_pct: Decimal | None = None  # demerger: share of the parent's cost base moved
    source: str = "VENDOR"  # VENDOR | CSV | OWNER
    status: str = "confirmed"
    note: str = ""


@dataclass(frozen=True)
class Booking:
    """The effect of one event on one book (``bf_corporate_actions`` row)."""

    key: str
    kind: CaKind
    code: str
    ex_date: date | None
    pay_date: date | None = None
    held: int = 0  # parent shares entitled (0 = not known)
    cash: Decimal = Decimal(0)  # credited to the book's cash
    income: Decimal = Decimal(0)  # assessable dividend
    franked_pct: Decimal | None = None
    franking_credit: Decimal = Decimal(0)
    cost_reduction: Decimal = Decimal(0)  # off the parent's cost base
    qty_change: int = 0  # shares of ``code`` (split, disposal)
    new_code: str | None = None
    new_shares: int = 0  # shares of ``new_code`` received
    child_cost: Decimal | None = None  # in-specie: the new shares' cost base
    cost_moved_pct: Decimal | None = None  # demerger: fraction of parent cost moved
    ratio: Decimal | None = None
    source: str = "FLEX"
    expected_key: str | None = None  # the calendar event a Flex row settles
    tax_class: str = ""  # "" | PROVISIONAL | UNCLASSIFIED
    note: str = ""


@dataclass(frozen=True)
class IdentityHint:
    """A code change reported by IBKR (issue change with a new code)."""

    old: str
    new: str
    ratio: Decimal
    key: str


def money(x: Decimal) -> Decimal:
    return x.quantize(CENT, ROUND_HALF_EVEN)


def _credit(amount: Decimal, fp: Decimal | None, rate: Decimal | None) -> Decimal:
    """Tax F7: the franking credit of a dividend only with a known rate (never an assumed
    30%); an unfranked dividend has none. 0 = none or not known (see ``franked_pct``)."""
    if fp is None or fp == 0 or rate is None:
        return Decimal(0)
    return franking_credit(amount * fp / 100, rate)


def franking_credit(franked_amount: Decimal, rate: Decimal = COMPANY_TAX_RATE) -> Decimal:
    return money(franked_amount * rate / (1 - rate))


def floor_shares(x: Decimal) -> int:
    return int(x.to_integral_value(ROUND_FLOOR))


def split_count(held: int, ratio: Decimal) -> int:
    """Shares after a split or consolidation of ``held`` shares at ``ratio`` (new per
    old): the fraction is dropped, as for a code change (BF-D25). IBKR's record gives the
    broker book's exact count (an issuer that rounds a fraction up shows one share
    more; reconciliation allows one share either way)."""
    return floor_shares(held * ratio)


# ---------------------------------------------------------------------------
# Calendar: CSV + vendor
# ---------------------------------------------------------------------------

_KIND_WORDS: tuple[tuple[str, CaKind], ...] = (
    ("in specie", CaKind.IN_SPECIE),
    ("in-specie", CaKind.IN_SPECIE),
    ("demerger", CaKind.DEMERGER),
    ("spin-off", CaKind.DEMERGER),
    ("spinoff", CaKind.DEMERGER),
    ("capital return", CaKind.CAPITAL_RETURN),
    ("return of capital", CaKind.CAPITAL_RETURN),
    ("capital reduction", CaKind.CAPITAL_RETURN),
    ("special", CaKind.SPECIAL),
    ("consolidation", CaKind.SPLIT),
    ("subdivision", CaKind.SPLIT),
    ("split", CaKind.SPLIT),
    ("code change", CaKind.CODE_CHANGE),
    ("name change", CaKind.CODE_CHANGE),
    ("rename", CaKind.CODE_CHANGE),
    ("dividend", CaKind.DIVIDEND),
)


def kind_of(text: str) -> CaKind:
    t = text.lower()
    for word, k in _KIND_WORDS:
        if word in t:
            return k
    raise CaError(f"unknown corporate-action kind {text!r}")


def _dec(s: str | None) -> Decimal | None:
    s = (s or "").strip().replace("%", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise CaError(f"bad number {s!r}") from exc


def _date(s: str | None) -> date | None:
    s = (s or "").strip()
    return date.fromisoformat(s) if s else None


def parse_ratio(text: str) -> Decimal:
    """``"1:10"`` (1 new for 10 old) or a decimal (new shares per old share)."""
    t = text.strip()
    try:
        if ":" in t:
            a, b = (Decimal(x) for x in t.split(":", 1))
            r = a / b
        else:
            r = Decimal(t)
    except (InvalidOperation, ZeroDivisionError) as exc:
        raise CaError(f"bad ratio {text!r}") from exc
    if not (Decimal("0.0001") <= r <= Decimal(1000)):
        raise CaError(f"ratio {text!r} out of range")
    return r


def ratio_from_note(note: str, parent: str, child: str) -> tuple[Decimal | None, bool]:
    """The share ratio stated in a CSV note, e.g. ``1 WDS per 5.5340 BHP``, ``7.2021 MYR
    per PMV``, ``~0.25 GMD per SBM``: (new per parent share, approximate)."""
    m = re.search(
        rf"(~)?(\d+(?:\.\d+)?)\s+{re.escape(child)}\s+per\s+(?:(\d+(?:\.\d+)?)\s+)?"
        rf"{re.escape(parent)}\b",
        note,
    )
    if not m:
        return None, False
    r = Decimal(m.group(2)) / Decimal(m.group(3) or "1")
    return r, bool(m.group(1))


def load_ca_csv(path: Path) -> list[CaEvent]:
    """The record keeper's ``CORPORATE_ACTIONS.csv``: ``code, ex_date, book_on, kind,
    value_per_share, distributed, source, entered, status, note``; optional columns
    ``pay_date, ratio, franked_pct, capital_per_share, cost_base_pct``. The ratio, when
    no column gives it, is read from the note (``1 WDS per 5.5340 BHP``)."""
    out: list[CaEvent] = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            try:
                code = r["code"].strip().upper()
                ex = _date(r["ex_date"])
                if not code or ex is None:
                    raise CaError("code and ex_date are required")
                k = kind_of(r.get("kind", ""))
                child = (r.get("distributed") or "").strip().upper() or None
                note = r.get("note", "") or ""
                ratio, approx = None, False
                if r.get("ratio"):
                    ratio = parse_ratio(r["ratio"])
                elif child:
                    ratio, approx = ratio_from_note(note, code, child)
                pct = _dec(r.get("cost_base_pct"))
                if pct is not None and pct > 1:
                    pct = pct / 100  # given as a percentage
                out.append(
                    CaEvent(
                        key=f"CSV:{code}:{ex}:{k.value}", kind=k, code=code, ex_date=ex,
                        pay_date=_date(r.get("pay_date")), per_share=_dec(r.get("value_per_share")),
                        franked_pct=_dec(r.get("franked_pct")),
                        franking_rate=_dec(r.get("franking_rate")),
                        capital_per_share=_dec(r.get("capital_per_share")), new_code=child,
                        ratio=ratio, ratio_approx=approx, cost_base_pct=pct, source="CSV",
                        status=(r.get("status") or "confirmed").strip().lower(), note=note[:200],
                    )
                )  # fmt: skip
            except (CaError, KeyError, ValueError) as exc:
                raise CaError(f"{path} line {i}: {exc}") from exc
    return out


def vendor_events(rows: Iterable[tuple[str, date, Decimal, date | None]]) -> list[CaEvent]:
    """Vendor dividends ``(code, ex_date, unadjusted value, pay date)`` as ordinary
    dividends with franking unknown (the vendor gives no franking and no kind)."""
    return [
        CaEvent(f"VENDOR:{c}:{ex}", CaKind.DIVIDEND, c, ex, pay, v, source="VENDOR")
        for c, ex, v, pay in rows
        if v > 0
    ]


def vendor_split_events(rows: Iterable[tuple[str, date, Decimal]]) -> list[CaEvent]:
    """Vendor splits and consolidations ``(code, date, new shares per old share)`` as
    ``SPLIT`` events on that date (BF-D26): 2-for-1 is 2, 1-for-10 is 0.1. A ratio of 1
    (no change) or out of ``parse_ratio``'s range is left out."""
    out = []
    for c, d, r in rows:
        if r == 1 or not (Decimal("0.0001") <= r <= Decimal(1000)):
            continue
        out.append(CaEvent(f"VENDOR:SPLIT:{c}:{d}", CaKind.SPLIT, c, d, ratio=r, source="VENDOR"))
    return out


def _family(e: CaEvent) -> bool:
    """True for a share-count event (split, consolidation, code change)."""
    return e.kind in COUNT_KINDS


@dataclass
class CaCalendar:
    """Vendor dividends and splits merged with the CSV (and owner) events; the CSV wins:
    a CSV share-count event (split, consolidation, code change) replaces the vendor's
    split rows of the code within a week, any other CSV event the vendor's dividends."""

    events: list[CaEvent] = field(default_factory=list)

    @classmethod
    def merged(cls, vendor: Iterable[CaEvent], owned: Iterable[CaEvent]) -> CaCalendar:
        own = list(owned)
        week = timedelta(days=OVERRIDE_DAYS)
        keep = [
            v
            for v in vendor
            if not any(
                o.code == v.code and abs(o.ex_date - v.ex_date) <= week and _family(o) == _family(v)
                for o in own
            )
        ]
        evs = sorted([*keep, *own], key=lambda e: (e.ex_date, e.code, e.key))
        return cls(evs)

    def on(self, day: date) -> list[CaEvent]:
        return [e for e in self.events if e.ex_date == day]

    def between(self, a: date, b: date) -> list[CaEvent]:
        return [e for e in self.events if a <= e.ex_date <= b]

    def cash_event_for(self, code: str, paid: date, ex: date | None) -> CaEvent | None:
        """The calendar event a Flex cash row of ``code`` paid on ``paid`` settles."""
        lo = paid - timedelta(CASH_MATCH_DAYS)
        cands = [
            e
            for e in self.events
            if e.code == code
            and e.kind in CASH_KINDS
            and (e.ex_date == ex if ex is not None else lo <= e.ex_date <= paid)
        ]
        return max(cands, key=lambda e: (e.source != "VENDOR", e.ex_date), default=None)

    def split_event_for(self, code: str, when: date | None) -> CaEvent | None:
        """The calendar split of ``code`` a Flex split row reported on ``when`` settles."""
        if when is None:
            return None
        span = timedelta(days=SPLIT_MATCH_DAYS)
        cands = [
            e
            for e in self.events
            if e.code == code and e.kind is CaKind.SPLIT and abs(e.ex_date - when) <= span
        ]
        return min(cands, key=lambda e: (abs(e.ex_date - when), e.source == "VENDOR"), default=None)

    def share_event_for(self, new_code: str, parent: str | None) -> CaEvent | None:
        cands = [
            e
            for e in self.events
            if e.kind in SHARE_KINDS and e.new_code == new_code and parent in (None, e.code)
        ]
        return max(cands, key=lambda e: e.ex_date, default=None)


# ---------------------------------------------------------------------------
# Calendar event -> booking (simulated books) and expectation (broker books)
# ---------------------------------------------------------------------------


def book_event(  # noqa: PLR0911 - one return per kind
    ev: CaEvent,
    held: int,
    px: Mapping[str, Decimal] | None = None,
    book_key: str | None = None,
) -> Booking | None:
    """The booking of calendar event ``ev`` on ``held`` parent shares (simulated books).
    ``px``: the ex-date closes, used for a demerger's provisional cost split. None for
    a code change (identity map) or nothing held."""
    if held <= 0 or ev.kind is CaKind.CODE_CHANGE:
        return None
    key = book_key or ev.key
    if ev.kind is CaKind.SPLIT:
        if ev.ratio is None:
            raise CaError(f"{ev.key}: a split needs its ratio")
        change = split_count(held, ev.ratio) - held
        if change == 0:
            return None
        return Booking(
            key, ev.kind, ev.code, ev.ex_date, ev.ex_date, held, qty_change=change,
            ratio=ev.ratio, source=ev.source, note=ev.note[:120],
        )  # fmt: skip
    if ev.kind in CASH_KINDS:
        if ev.per_share is None:
            return None
        cash = money(ev.per_share * held)
        if ev.kind is CaKind.CAPITAL_RETURN:
            return Booking(
                key, ev.kind, ev.code, ev.ex_date, ev.pay_date, held, cash=cash,
                cost_reduction=cash, source=ev.source, note=ev.note[:120],
            )  # fmt: skip
        fp = ev.franked_pct
        credit = _credit(cash, fp, ev.franking_rate)
        return Booking(
            key, ev.kind, ev.code, ev.ex_date, ev.pay_date, held, cash=cash, income=cash,
            franked_pct=fp, franking_credit=credit, source=ev.source, note=ev.note[:120],
        )  # fmt: skip
    if ev.new_code is None or ev.ratio is None:
        raise CaError(f"{ev.key}: a share distribution needs the new code and the ratio")
    n = floor_shares(held * ev.ratio)
    if ev.kind is CaKind.IN_SPECIE:
        value = money(ev.per_share * held) if ev.per_share is not None else None
        if value is not None and ev.capital_per_share is not None:
            cap = money(ev.capital_per_share * held)
            inc = value - cap
            fp = ev.franked_pct
            credit = _credit(inc, fp, ev.franking_rate)
            return Booking(
                key, ev.kind, ev.code, ev.ex_date, ev.pay_date, held, income=inc,
                franked_pct=fp, franking_credit=credit, cost_reduction=cap,
                new_code=ev.new_code, new_shares=n, child_cost=value, ratio=ev.ratio,
                source=ev.source, note=ev.note[:120],
            )  # fmt: skip
        return Booking(
            key, ev.kind, ev.code, ev.ex_date, ev.pay_date, held, new_code=ev.new_code,
            new_shares=n, child_cost=value, ratio=ev.ratio, source=ev.source,
            tax_class="UNCLASSIFIED", note="income/capital split not given; " + ev.note[:80],
        )  # fmt: skip
    pct, tax = ev.cost_base_pct, ""
    if pct is None:
        pct, tax = _value_split(ev, px or {}), "PROVISIONAL"
    return Booking(
        key, ev.kind, ev.code, ev.ex_date, ev.pay_date, held, new_code=ev.new_code,
        new_shares=n, cost_moved_pct=pct, ratio=ev.ratio, source=ev.source, tax_class=tax,
        note=("cost split by ex-date values, to confirm; " if tax else "") + ev.note[:80],
    )  # fmt: skip


def _value_split(ev: CaEvent, px: Mapping[str, Decimal]) -> Decimal:
    """Provisional demerger cost split: the new shares' value over the parent's ex-date
    value plus theirs (the per-share value of the event when the child has no close)."""
    assert ev.ratio is not None
    assert ev.new_code is not None
    parent = px.get(ev.code)
    child = px.get(ev.new_code)
    cv = ev.ratio * child if child is not None else ev.per_share
    if parent is None or cv is None or parent + cv <= 0:
        return Decimal(0)
    return (cv / (parent + cv)).quantize(Decimal("0.000001"))


def pending_until(ev: CaEvent) -> date:
    if ev.pay_date is not None:
        return ev.pay_date + timedelta(days=PENDING_GRACE_DAYS)
    return ev.ex_date + timedelta(days=PENDING_DAYS)


def expectations(
    events: Iterable[CaEvent],
    held_at: Callable[[str, date], int],
    settled: Iterable[str],
    today: date,
) -> list[Expected]:
    """Broker book: the calendar events IBKR's records have not yet settled, as
    expectations a reconciliation difference may match (cash to the cent band, new
    shares to the share). Expired ones (``pending_until``) explain nothing."""
    done = set(settled)
    out: list[Expected] = []
    for ev in events:
        if ev.key in done or ev.ex_date > today or today > pending_until(ev):
            continue
        if ev.kind is CaKind.CODE_CHANGE:
            continue  # the identity map (owner-confirmed) carries code changes
        held = held_at(ev.code, ev.ex_date)
        if held <= 0:
            continue
        if ev.kind is CaKind.SPLIT:  # BF-D26: IBKR may show the new count before Flex
            if ev.ratio is not None:
                d = split_count(held, ev.ratio) - held
                lbl = f"SPLIT {ev.code} x{ev.ratio.normalize():f} ex {ev.ex_date}"
                out.append(Expected(ev.key, lbl, Decimal(0), {ev.code: d}))
            continue
        if ev.kind in CASH_KINDS:
            if ev.per_share is not None:
                out.append(Expected(ev.key, f"{ev.kind.value} {ev.code} ex {ev.ex_date}",
                                    money(ev.per_share * held)))  # fmt: skip
            continue
        if ev.new_code is None:
            continue
        n = floor_shares(held * ev.ratio) if ev.ratio is not None else 0
        out.append(
            Expected(
                ev.key, f"{ev.kind.value} {ev.code}->{ev.new_code} ex {ev.ex_date}",
                Decimal(0), {ev.new_code: n}, approx=ev.ratio is None or ev.ratio_approx,
            )
        )  # fmt: skip
    return out


# ---------------------------------------------------------------------------
# IBKR Activity Flex -> bookings (broker books)
# ---------------------------------------------------------------------------

_CASH_TYPES = {
    "dividends": CaKind.DIVIDEND,
    "payment in lieu of dividends": CaKind.DIVIDEND,
    "withholding tax": CaKind.WITHHOLDING,
}
_PARENT_RE = re.compile(r"^\s*([A-Z0-9]{1,6})(?:\.[A-Z]{1,4})?\s*\(")
_FOR_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s+FOR\s+(\d+(?:\.\d+)?)\b", re.I)
_PER_SHARE_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s+PER\s+SHARE", re.I)


def franked_from_text(text: str) -> Decimal | None:
    t = text.upper()
    if "UNFRANKED" in t:
        return Decimal(0)
    if "FULLY FRANKED" in t:
        return Decimal(100)
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*FRANK", t)
    return Decimal(m.group(1)) if m else None


def cash_kind_from_text(text: str) -> CaKind | None:
    t = text.upper()
    if any(w in t for w in ("RETURN OF CAPITAL", "CAPITAL RETURN", "CAPITAL REDUCTION")):
        return CaKind.CAPITAL_RETURN
    if "SPECIAL" in t:
        return CaKind.SPECIAL
    return None


@dataclass(frozen=True)
class FlexBookings:
    bookings: tuple[Booking, ...]
    identity: tuple[IdentityHint, ...]
    skipped: tuple[str, ...]  # rows this module does not book (deposits, fees, ...)


def _cash_booking(
    c: FlexCashTransaction, cal: CaCalendar, held_at: Callable[[str, date], int]
) -> Booking | None:
    base = _CASH_TYPES.get(c.type.strip().lower())
    if base is None or c.symbol is None or c.currency not in ("AUD", ""):
        return None
    code = c.symbol.upper()
    paid = c.settle_date or c.pay_date or c.report_date
    if paid is None:
        raise CaError(f"Flex cash row {c.transaction_id} without a date")
    key = f"FLEX:CT:{c.transaction_id}"
    if base is CaKind.WITHHOLDING:
        return Booking(key, base, code, c.ex_date, paid, cash=c.amount, source="FLEX",
                       note=c.description[:200])  # fmt: skip
    ev = cal.cash_event_for(code, paid, c.ex_date)
    kind = cash_kind_from_text(c.description)
    if kind is None:  # the record's CSV classifies; the vendor calls everything a dividend
        kind = ev.kind if ev is not None and ev.source != "VENDOR" else CaKind.DIVIDEND
    ex = c.ex_date or (ev.ex_date if ev is not None else None)
    held = held_at(code, ex) if ex is not None else 0
    m = _PER_SHARE_RE.search(c.description)
    if held == 0 and m:
        held = int((c.amount / Decimal(m.group(1))).to_integral_value())
    if kind is CaKind.CAPITAL_RETURN:
        return Booking(
            key, kind, code, ex, paid, held, cash=c.amount, cost_reduction=c.amount,
            source="FLEX", expected_key=ev.key if ev else None, note=c.description[:200],
        )  # fmt: skip
    fp = franked_from_text(c.description)
    if fp is None and ev is not None:
        fp = ev.franked_pct
    if "IN LIEU" in c.type.upper():
        fp = Decimal(0)  # a payment in lieu carries no franking
    credit = _credit(c.amount, fp, ev.franking_rate if ev is not None else None)
    return Booking(
        key, kind, code, ex, paid, held, cash=c.amount, income=c.amount, franked_pct=fp,
        franking_credit=credit, source="FLEX", expected_key=ev.key if ev else None,
        note=c.description[:200],
    )  # fmt: skip


def _extra_shares_split(
    key: str,
    code: str,
    n: int,
    cash: Decimal,
    when: date | None,
    desc: str,
    cal: CaCalendar,
    held_at: Callable[[str, date], int],
) -> Booking:
    """BF-D26: a forward split (or bonus issue) shown as the extra shares of the code
    only: a ``SPLIT`` of +n shares, the cost base unchanged."""
    sev = cal.split_event_for(code, when)
    ex = sev.ex_date if sev else when
    held = held_at(code, ex) if ex is not None else 0
    fm = _FOR_RE.search(desc)
    fr = Decimal(fm.group(1)) / Decimal(fm.group(2)) if fm else None
    return Booking(key, CaKind.SPLIT, code, ex, when, held, cash=cash, qty_change=n,
                   ratio=fr, source="FLEX", expected_key=sev.key if sev else None,
                   note=desc[:200])  # fmt: skip


def _action_bookings(  # noqa: PLR0911, PLR0912, PLR0915 - one return per action shape
    rows: Sequence[FlexCorporateAction],
    cal: CaCalendar,
    held_at: Callable[[str, date], int],
    px: Mapping[str, Decimal],
) -> tuple[list[Booking], list[IdentityHint]]:
    aid = rows[0].action_id
    key = f"FLEX:CA:{aid}"
    when = next((r.report_date for r in rows if r.report_date), None)
    desc = rows[0].description
    cash = sum((r.amount for r in rows), Decimal(0))
    ins = [r for r in rows if r.quantity > 0]
    outs = [r for r in rows if r.quantity < 0]
    if outs and ins:  # issue change, split or consolidation (one company)
        old, new = outs[0].symbol.upper(), ins[0].symbol.upper()
        q_out = -sum((r.quantity for r in outs), Decimal(0))
        q_in = sum((r.quantity for r in ins), Decimal(0))
        fm = _FOR_RE.search(desc)  # "1 FOR 10": the stated ratio; the counts lose fractions
        ratio = (
            Decimal(fm.group(1)) / Decimal(fm.group(2))
            if fm
            else (q_in / q_out).quantize(Decimal("0.000001"))
        )
        if old == new:
            sev = cal.split_event_for(old, when)  # BF-D26: settles the calendar's split
            b = Booking(key, CaKind.SPLIT, old, sev.ex_date if sev else when, when,
                        int(q_out), cash=cash, qty_change=int(q_in - q_out), ratio=ratio,
                        source="FLEX", expected_key=sev.key if sev else None,
                        note=desc[:200])  # fmt: skip
            return [b], []
        if rows[0].type in ("TC", "TO") or "MERGED" in desc.upper() or "TENDER" in desc.upper():
            # tax F1: a takeover by another company (scrip, maybe cash): the old shares are
            # disposed of and the new ones acquired (PROVISIONAL: roll-over is the
            # accountant's call); no identity hint, the codes are different companies
            val = ins[0].value
            b = Booking(key, CaKind.DISPOSAL, old, when, when, int(q_out), cash=cash,
                        qty_change=-int(q_out), new_code=new, new_shares=int(q_in),
                        child_cost=money(val) if val is not None else None, ratio=ratio,
                        source="FLEX", tax_class=TAKEOVER_NOTE, note=desc[:200])  # fmt: skip
            return [b], []
        b = Booking(key, CaKind.CODE_CHANGE, old, when, when, int(q_out), cash=cash,
                    new_code=new, ratio=ratio, source="FLEX", note=desc[:200])  # fmt: skip
        return [b], [IdentityHint(old, new, ratio, key)]
    if outs:  # shares out for cash (cash takeover, buy-back) or delisted worthless
        code = outs[0].symbol.upper()
        q = -sum((r.quantity for r in outs), Decimal(0))
        b = Booking(key, CaKind.DISPOSAL, code, when, when, int(q), cash=cash,
                    qty_change=-int(q), source="FLEX", note=desc[:200])  # fmt: skip
        return [b], []
    if not ins:
        if cash:
            code = rows[0].symbol.upper()
            return [Booking(key, CaKind.CASH_IN_LIEU, code, when, when, cash=cash,
                            source="FLEX", note=desc[:200])], []  # fmt: skip
        return [], []
    child = ins[0].symbol.upper()
    n = int(sum((r.quantity for r in ins), Decimal(0)))
    m = _PARENT_RE.match(desc)
    if (m and m.group(1) == child) or rows[0].type in ("FS", "SD"):
        return [_extra_shares_split(key, child, n, cash, when, desc, cal, held_at)], []
    parent = m.group(1) if m and m.group(1) != child else None
    ev = cal.share_event_for(child, parent)
    if parent is None and ev is not None:
        parent = ev.code
    if parent is None:
        raise CaError(f"Flex action {aid}: shares of {child} received, parent not known")
    ex = ev.ex_date if ev is not None else when
    held = held_at(parent, ex) if ex is not None else 0
    fm = _FOR_RE.search(desc)
    share_ratio = (
        ev.ratio
        if ev is not None and ev.ratio is not None
        else (Decimal(fm.group(1)) / Decimal(fm.group(2)) if fm else None)
    )
    if ev is not None and ev.kind is CaKind.IN_SPECIE:
        got = book_event(replace(ev, ratio=share_ratio or ev.ratio), max(held, 1), px, key)
        assert got is not None
        got = replace(got, held=held, new_shares=n, cash=cash, pay_date=when, source="FLEX",
                      expected_key=ev.key)  # fmt: skip
        if got.child_cost is None and ins[0].value is not None:
            got = replace(got, child_cost=money(ins[0].value))
        return [got], []
    pct = ev.cost_base_pct if ev is not None else None
    tax = "" if pct is not None else "PROVISIONAL"
    if pct is None:
        pv, cv = px.get(parent), ins[0].value
        if pv is not None and cv is not None and held > 0 and pv * held + cv > 0:
            pct = (cv / (pv * held + cv)).quantize(Decimal("0.000001"))
        else:
            pct = Decimal(0)
    b = Booking(
        key, CaKind.DEMERGER, parent, ex, when, held, cash=cash, new_code=child, new_shares=n,
        cost_moved_pct=pct, ratio=share_ratio, source="FLEX",
        expected_key=ev.key if ev else None,
        tax_class=tax, note=(("cost split provisional; " if tax else "") + desc)[:200],
    )  # fmt: skip
    return [b], []


def bookings_from_flex(
    statements: Iterable[FlexStatement],
    cal: CaCalendar,
    held_at: Callable[[str, date], int],
    px: Mapping[str, Decimal] | None = None,
) -> FlexBookings:
    """IBKR's own records -> bookings (idempotent keys ``FLEX:CT:<transactionID>`` and
    ``FLEX:CA:<actionID>``; statements that overlap give the same keys)."""
    out: dict[str, Booking] = {}
    ids: dict[str, IdentityHint] = {}
    skipped: list[str] = []
    for st in statements:
        for c in st.cash_transactions:
            b = _cash_booking(c, cal, held_at)
            if b is None:
                skipped.append(f"{c.type} {c.transaction_id}")
            else:
                out.setdefault(b.key, b)
        groups: dict[str, list[FlexCorporateAction]] = {}
        for a in st.corporate_actions:
            groups.setdefault(a.action_id, []).append(a)
        for rows in groups.values():
            bs, hs = _action_bookings(rows, cal, held_at, px or {})
            for b in bs:
                out.setdefault(b.key, b)
            for h in hs:
                ids.setdefault(h.key, h)
    return FlexBookings(tuple(out.values()), tuple(ids.values()), tuple(skipped))


# ---------------------------------------------------------------------------
# Cost base with corporate actions (average cost, as the journal's capital cap)
# ---------------------------------------------------------------------------


@dataclass
class CostBook:
    """Average-cost holdings with corporate actions applied in time order; realised
    results kept for the tax view (``g1`` = capital returns above the cost base)."""

    cost: dict[str, Decimal] = field(default_factory=dict)
    qty: dict[str, Decimal] = field(default_factory=dict)
    g1: Decimal = Decimal(0)

    def buy(self, e: str, qty: Decimal, cost: Decimal) -> None:
        self.cost[e] = self.cost.get(e, Decimal(0)) + cost
        self.qty[e] = self.qty.get(e, Decimal(0)) + qty

    def sell(self, e: str, qty: Decimal) -> None:
        q = self.qty.get(e, Decimal(0))
        if q <= 0:
            return
        avg = self.cost[e] / q
        self.qty[e] = max(q - qty, Decimal(0))
        self.cost[e] = avg * self.qty[e]

    def apply(self, b: Booking, code: str, new_code: str | None) -> None:
        if b.cost_reduction:
            have = self.cost.get(code, Decimal(0))
            cut = min(have, b.cost_reduction)
            self.cost[code] = have - cut
            self.g1 += b.cost_reduction - cut
        if b.kind is CaKind.SPLIT:  # BF-D26: one company, more or fewer shares, same cost
            self.qty[code] = max(self.qty.get(code, Decimal(0)) + b.qty_change, Decimal(0))
        elif b.qty_change > 0:
            self.qty[code] = self.qty.get(code, Decimal(0)) + b.qty_change
        elif b.qty_change < 0:
            self.sell(code, Decimal(-b.qty_change))
        if new_code is not None and b.new_shares and b.kind is not CaKind.CODE_CHANGE:
            if b.child_cost is not None:
                moved = b.child_cost
            else:
                moved = self.cost.get(code, Decimal(0)) * (b.cost_moved_pct or Decimal(0))
                self.cost[code] = self.cost.get(code, Decimal(0)) - moved
            self.buy(new_code, Decimal(b.new_shares), moved)

    def total(self) -> Decimal:
        return sum((c for e, c in self.cost.items() if self.qty.get(e)), Decimal(0))
