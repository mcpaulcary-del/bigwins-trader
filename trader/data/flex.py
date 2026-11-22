"""IBKR Activity Flex connector: parser, Web Service client, mark ingestion (§4, §6, DAT-02).

The Activity Flex statement gives the second-source close (Open Positions
"Mark Price"), positions, cash transactions and trades. This module

* parses a statement (XML) into typed records with ``Decimal`` amounts; the
  trade ``orderReference`` is optional - it is present only with Audit Trail
  fields enabled and never on paper accounts (v2.10 + R37 correction);
* fetches statements through the Flex Web Service with an injected transport:
  ``SendRequest`` (with ``fd``/``td`` for an explicit date range, never with
  ``p``) then ``GetStatement``, a ``User-Agent`` header on every request, and a
  rate limit of 1 request a second and 10 a minute per token (R37);
* stores every raw statement unchanged (``RawStore``, source ``flex``) and the
  marks as bitemporal ``raw_bar`` rows (source ``flex``, close only), dated by
  the statement's report date;
* maps a trading day D to its mark (``mark_for_day``): the mark in the
  statement dated D, else in the first later statement with no ASX session in
  between (§4, ``flex_pull`` row).

Flex for D is normally published only in the Sydney afternoon of the next day
(R37), so at 08:00 a missing mark is the expected case and DAT-02 gives
``SINGLE_SOURCE`` (see ``quality``); the verdict is re-issued when it arrives.

Booking cash transactions and trades into the ledger is M5 (BP-20); this module
only parses them. The B-fast journal books dividends, capital returns and corporate
actions from them (``trader.corporate_actions``, BF-D23).
"""

from __future__ import annotations

import re
import time as _time
import xml.etree.ElementTree as ET
from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.calendar import AsxCalendar
from trader.data.instruments import current_instrument
from trader.data.models import RawBar
from trader.data.store import RawFile, RawStore
from trader.secrets import SecretValue, read_secret
from trader.timeutil import ensure_utc

SEND_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
GET_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/GetStatement"
USER_AGENT = "asx-trader/0.1 (Flex Web Service client)"
API_VERSION = "3"
RETRY_CODES = frozenset(
    {"1001", "1004", "1005", "1006", "1007", "1008", "1009", "1018", "1019", "1021"}
)

# (url, params, headers) -> body
FlexTransport = Callable[[str, Mapping[str, str], Mapping[str, str]], bytes]


class FlexError(Exception):
    pass


class FlexNotReadyError(FlexError):
    """The statement is still being generated, or none exists yet for the period."""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _d(s: str | None) -> date | None:
    if not s:
        return None
    s = s.split(";")[0].replace("-", "")
    if not re.fullmatch(r"\d{8}", s):
        raise FlexError(f"Flex: bad date {s!r}")
    return date(int(s[:4]), int(s[4:6]), int(s[6:]))


def _dt(s: str | None) -> str | None:
    return s or None


def _num(s: str | None, *, required: bool = False) -> Decimal | None:
    if s is None or s == "":
        if required:
            raise FlexError("Flex: missing number")
        return None
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise FlexError(f"Flex: bad number {s!r}") from exc


@dataclass(frozen=True)
class FlexPosition:
    symbol: str
    con_id: str | None
    asset_category: str
    currency: str
    position: Decimal
    mark_price: Decimal
    report_date: date


@dataclass(frozen=True)
class FlexCashTransaction:
    transaction_id: str
    type: str
    amount: Decimal
    currency: str
    date_time: str | None
    settle_date: date | None
    symbol: str | None
    description: str
    # The dividend's ex-date and payment date where the Flex query includes them (BF-D23;
    # optional in IBKR's field list, so absent on older queries)
    ex_date: date | None = None
    pay_date: date | None = None
    report_date: date | None = None


@dataclass(frozen=True)
class FlexCorporateAction:
    """One row of the Flex "Corporate Actions" section (BF-D23). An action on several
    securities (an issue change: the old code out, the new code in) has one row per
    security with the same ``action_id``. ``type`` is IBKR's action code (SO spin-off,
    IC issue change, RS/FS split, SD stock dividend, DI/ED rights, TC/TO tender, DW
    delisted worthless...); ``quantity`` is signed (shares in > 0, out < 0)."""

    transaction_id: str
    action_id: str
    type: str
    symbol: str
    con_id: str | None
    quantity: Decimal
    amount: Decimal  # cash credited (cash in lieu, a cash merger); 0 when none
    value: Decimal | None
    report_date: date | None
    date_time: str | None
    description: str


@dataclass(frozen=True)
class FlexTrade:
    exec_id: str
    trade_id: str | None
    symbol: str
    side: str  # BUY or SELL
    quantity: Decimal
    price: Decimal
    commission: Decimal  # IBKR reports it negative; kept as reported
    trade_date: date
    date_time: str | None
    settle_date: date | None
    order_reference: str | None  # absent without Audit Trail fields, and on paper (R37)
    taxes: Decimal = Decimal(0)  # review M1 / tax F12: GST on brokerage, as reported


@dataclass(frozen=True)
class FlexStatement:
    account_id: str
    from_date: date
    to_date: date
    positions: tuple[FlexPosition, ...]
    cash_transactions: tuple[FlexCashTransaction, ...]
    trades: tuple[FlexTrade, ...]
    corporate_actions: tuple[FlexCorporateAction, ...] = ()


def _safe_xml(body: bytes) -> ET.Element:
    head = body[:4096].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in head:
        raise FlexError("Flex: DTDs and entities are refused")
    try:
        return ET.fromstring(body)  # noqa: S314 - no DTD/entities allowed (checked above)
    except ET.ParseError as exc:
        raise FlexError("Flex: response is not well-formed XML") from exc


def _corporate_actions(st: ET.Element) -> list[FlexCorporateAction]:
    """The statement's ``CorporateAction`` rows (BF-D23)."""
    actions = []
    for a in st.iter("CorporateAction"):
        if a.get("levelOfDetail", "DETAIL") not in ("DETAIL", "SUMMARY", ""):
            continue
        txn = a.get("transactionID") or ""
        aid = a.get("actionID") or txn
        if not aid:
            raise FlexError("Flex: corporate action without actionID/transactionID")
        aq = _num(a.get("quantity")) or Decimal(0)
        actions.append(
            FlexCorporateAction(
                transaction_id=txn or f"{aid}:{a.get('symbol', '')}",
                action_id=aid,
                type=a.get("type", "").upper(),
                symbol=a.get("symbol", ""),
                con_id=a.get("conid"),
                quantity=aq,
                amount=_num(a.get("amount")) or _num(a.get("proceeds")) or Decimal(0),
                value=_num(a.get("value")),
                report_date=_d(a.get("reportDate")),
                date_time=_dt(a.get("dateTime")),
                description=a.get("description") or a.get("actionDescription") or "",
            )
        )
    return actions


def parse_statements(body: bytes) -> list[FlexStatement]:
    """Parse a ``FlexQueryResponse`` (one or more ``FlexStatement`` elements)."""
    root = _safe_xml(body)
    if root.tag == "FlexStatementResponse":
        raise FlexError("Flex: a Web Service status response, not a statement")
    out: list[FlexStatement] = []
    for st in root.iter("FlexStatement"):
        from_date = _d(st.get("fromDate"))
        to_date = _d(st.get("toDate"))
        if from_date is None or to_date is None:
            raise FlexError("Flex: statement without fromDate/toDate")
        positions = []
        for p in st.iter("OpenPosition"):
            if p.get("levelOfDetail", "SUMMARY") not in ("SUMMARY", ""):
                continue  # lot-level rows repeat the summary
            mark = _num(p.get("markPrice"), required=True)
            pos = _num(p.get("position"), required=True)
            assert mark is not None
            assert pos is not None
            positions.append(
                FlexPosition(
                    symbol=p.get("symbol", ""),
                    con_id=p.get("conid"),
                    asset_category=p.get("assetCategory", ""),
                    currency=p.get("currency", ""),
                    position=pos,
                    mark_price=mark,
                    report_date=_d(p.get("reportDate")) or to_date,
                )
            )
        cash = []
        for c in st.iter("CashTransaction"):
            amount = _num(c.get("amount"), required=True)
            assert amount is not None
            txn = c.get("transactionID")
            if not txn:
                raise FlexError("Flex: cash transaction without transactionID")
            cash.append(
                FlexCashTransaction(
                    transaction_id=txn,
                    type=c.get("type", ""),
                    amount=amount,
                    currency=c.get("currency", ""),
                    date_time=_dt(c.get("dateTime")),
                    settle_date=_d(c.get("settleDate")),
                    symbol=c.get("symbol") or None,
                    description=c.get("description", ""),
                    ex_date=_d(c.get("exDate")),
                    pay_date=_d(c.get("payDate")),
                    report_date=_d(c.get("reportDate")),
                )
            )
        actions = _corporate_actions(st)
        trades = []
        for t in st.iter("Trade"):
            exec_id = t.get("ibExecID")
            if not exec_id:
                raise FlexError("Flex: trade without ibExecID")
            qty = _num(t.get("quantity"), required=True)
            price = _num(t.get("tradePrice"), required=True)
            trade_date = _d(t.get("tradeDate"))
            assert qty is not None
            assert price is not None
            if trade_date is None:
                raise FlexError("Flex: trade without tradeDate")
            side = t.get("buySell", "").upper()
            if side not in ("BUY", "SELL"):
                raise FlexError(f"Flex: unknown buySell {side!r}")
            trades.append(
                FlexTrade(
                    exec_id=exec_id,
                    trade_id=t.get("tradeID"),
                    symbol=t.get("symbol", ""),
                    side=side,
                    quantity=abs(qty),
                    price=price,
                    commission=_num(t.get("ibCommission")) or Decimal(0),
                    trade_date=trade_date,
                    date_time=_dt(t.get("dateTime")),
                    settle_date=_d(t.get("settleDateTarget")),
                    order_reference=t.get("orderReference") or None,
                    taxes=_num(t.get("taxes")) or Decimal(0),
                )
            )
        out.append(
            FlexStatement(
                account_id=st.get("accountId", ""),
                from_date=from_date,
                to_date=to_date,
                positions=tuple(positions),
                cash_transactions=tuple(cash),
                trades=tuple(trades),
                corporate_actions=tuple(actions),
            )
        )
    if not out:
        raise FlexError("Flex: no FlexStatement in response")
    return out


# ---------------------------------------------------------------------------
# Web Service client
# ---------------------------------------------------------------------------


@dataclass
class RateLimiter:
    """At most ``per_second`` requests a second and ``per_minute`` a minute (R37)."""

    per_second: int = 1
    per_minute: int = 10
    clock: Callable[[], float] = _time.monotonic
    sleep: Callable[[float], None] = _time.sleep
    _sent: deque[float] = field(default_factory=deque)

    def wait(self) -> None:
        while True:
            now = self.clock()
            while self._sent and now - self._sent[0] >= 60:
                self._sent.popleft()
            last_second = sum(1 for t in self._sent if now - t < 1)
            delay = 0.0
            if last_second >= self.per_second:
                delay = max(delay, 1 - (now - self._sent[-1]))
            if len(self._sent) >= self.per_minute:
                delay = max(delay, 60 - (now - self._sent[0]))
            if delay <= 0:
                self._sent.append(now)
                return
            self.sleep(delay)


def _status(body: bytes) -> dict[str, str]:
    root = _safe_xml(body)
    if root.tag != "FlexStatementResponse":
        return {}
    return {child.tag: (child.text or "").strip() for child in root}


@dataclass
class FlexClient:
    transport: FlexTransport
    store: RawStore
    limiter: RateLimiter = field(default_factory=RateLimiter)
    token: Callable[[], SecretValue] = field(default=lambda: read_secret("ibkr_flex_token"))
    query_id: Callable[[], SecretValue] = field(default=lambda: read_secret("ibkr_flex_query_id"))
    max_polls: int = 10

    def _get(self, url: str, params: dict[str, str]) -> bytes:
        self.limiter.wait()
        try:
            return self.transport(url, params, {"User-Agent": USER_AGENT})
        except Exception as exc:
            raise FlexError(f"Flex request failed ({type(exc).__name__})") from None

    def fetch(
        self, from_date: date, to_date: date, now: datetime
    ) -> tuple[RawFile, list[FlexStatement]]:
        """SendRequest for [from_date, to_date] (``fd``/``td``), then GetStatement."""
        if from_date > to_date:
            raise ValueError("from_date after to_date")
        tok = self.token().reveal()
        params = {
            "t": tok,
            "q": self.query_id().reveal(),
            "v": API_VERSION,
            "fd": from_date.strftime("%Y%m%d"),
            "td": to_date.strftime("%Y%m%d"),
        }
        st = _status(self._get(SEND_URL, params))
        if st.get("Status") != "Success" or not st.get("ReferenceCode"):
            code = st.get("ErrorCode", "?")
            if code in RETRY_CODES:
                raise FlexNotReadyError(f"Flex SendRequest not ready (code {code})")
            raise FlexError(f"Flex SendRequest failed (code {code}): {st.get('ErrorMessage', '')}")
        ref = st["ReferenceCode"]
        for _ in range(self.max_polls):
            body = self._get(GET_URL, {"t": tok, "q": ref, "v": API_VERSION})
            status = _status(body)
            if not status:
                statements = parse_statements(body)
                raw = self.store.put(
                    "flex", f"statement_{from_date:%Y%m%d}_{to_date:%Y%m%d}", body, now, ext="xml"
                )
                return raw, statements
            code = status.get("ErrorCode", "?")
            if code not in RETRY_CODES:
                raise FlexError(f"Flex GetStatement failed (code {code})")
        raise FlexNotReadyError("Flex statement still being generated")


# ---------------------------------------------------------------------------
# Ingestion and mark mapping
# ---------------------------------------------------------------------------


def statement_dates_to_pull(last_ingested: date | None, today: date, first: date) -> list[date]:
    """Every calendar day from the day after the last ingested statement to yesterday (§4)."""
    start = first if last_ingested is None else last_ingested + timedelta(days=1)
    out: list[date] = []
    d = start
    while d < today:
        out.append(d)
        d += timedelta(days=1)
    return out


def ingest_marks(
    session: Session,
    statements: Iterable[FlexStatement],
    raw: RawFile,
    licensee: str,
    symbols: Iterable[str],
) -> int:
    """Store each statement's ASX stock marks as ``raw_bar`` rows (source ``flex``)."""
    wanted = set(symbols)
    n = 0
    for st in statements:
        for p in st.positions:
            if p.asset_category not in ("STK", "") or p.symbol not in wanted:
                continue
            inst = current_instrument(session, p.symbol)
            if inst is None:
                continue
            session.add(
                RawBar(
                    instrument_id=inst.id,
                    trade_date=p.report_date,
                    source="flex",
                    fetch_time=raw.fetch_time,
                    close=p.mark_price,
                    file_hash=raw.sha256,
                    licensee=licensee,
                )
            )
            n += 1
    session.flush()
    return n


@dataclass(frozen=True)
class Mark:
    price: Decimal
    statement_date: date


def mark_for_day(
    session: Session,
    instrument_id: int,
    day: date,
    cal: AsxCalendar,
    as_of: datetime | None = None,
) -> Mark | None:
    """The Flex mark DAT-02 uses for trading day ``day`` (§4 ``flex_pull`` row).

    The mark in the statement dated ``day``; if IBKR issued none for it, the mark
    in the first later statement with no ASX session in between.
    """
    q = select(RawBar).where(
        RawBar.instrument_id == instrument_id,
        RawBar.source == "flex",
        RawBar.trade_date >= day,
    )
    if as_of is not None:
        q = q.where(RawBar.fetch_time <= ensure_utc(as_of))
    by_date: dict[date, RawBar] = {}
    for r in session.execute(q.order_by(RawBar.trade_date, RawBar.fetch_time)).scalars():
        by_date[r.trade_date] = r
    if day in by_date:
        return Mark(by_date[day].close, day)
    for d in sorted(by_date):
        # no ASX session in (day, d]: otherwise the mark is for a later close
        if cal.covers(d) and cal.trading_days(day + timedelta(days=1), d):
            return None
        if cal.covers(d):
            return Mark(by_date[d].close, d)
    return None


def latest_mark(
    session: Session, instrument_id: int, before: date, as_of: datetime | None = None
) -> Mark | None:
    """The latest available Flex mark on or before ``before`` (tagged with its date)."""
    q = select(RawBar).where(
        RawBar.instrument_id == instrument_id,
        RawBar.source == "flex",
        RawBar.trade_date <= before,
    )
    if as_of is not None:
        q = q.where(RawBar.fetch_time <= ensure_utc(as_of))
    r = session.execute(
        q.order_by(RawBar.trade_date.desc(), RawBar.fetch_time.desc()).limit(1)
    ).scalar_one_or_none()
    return None if r is None else Mark(r.close, r.trade_date)
