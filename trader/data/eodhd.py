"""EODHD connector: daily raw OHLCV and dividends inside a counted call budget (DAT-23).

* Every request is counted in ``vendor_call_log`` *before* it is sent, in its own
  committed transaction, so the count survives a crash or restart. The budget is
  ``data.eodhd.calls_per_day`` per GMT day (EODHD resets at midnight GMT) and
  ``calls_per_minute``. A request that would exceed either does not call the API:
  it raises ``BudgetExceededError`` and the job fails closed with a WARN
  (``DATA_BUDGET``) - ``on_budget_exceeded: fail_closed``.
* A request for data older than the plan's history depth (``history_years``) is
  refused the same way, without a call.
* Per instrument the daily fetch makes **one** end-of-day range request from the
  day after the last stored bar to the latest close that may be read (16:25 rule,
  §4), so a bar missed on an earlier day is fetched by the next successful run.
* The key is read from the Docker secret ``eodhd_api_token`` (OPS-11), only for
  the user named as ``licensee`` (DAT-15); it never appears in a log, an error or
  a stored file. Raw responses are stored unchanged (``RawStore``) and parsed into
  bitemporal ``raw_bar`` / ``vendor_dividend`` rows stamped with the fetch time.
* Lookbacks are never fetched: they are read from the local store (DAT-23 (3)).

No network is used in tests: the HTTP transport is injected.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from trader.calendar import AsxCalendar
from trader.config import EodhdPlan
from trader.constants import ASX_TZ
from trader.data.instruments import require_instrument
from trader.data.models import QcEvent, RawBar, VendorCallLog, VendorDividend
from trader.data.store import RawFile, RawStore, last_stored_bar_date, latest_bars
from trader.enums import ReasonCode
from trader.secrets import SecretValue, read_secret
from trader.timeutil import ensure_utc

VENDOR = "eodhd"
BASE_URL = "https://eodhd.com/api"
EXCHANGE_SUFFIX = "AU"  # EODHD exchange code for the ASX
USER_AGENT = "asx-trader/0.1"

Transport = Callable[[str, Mapping[str, str]], bytes]


class EodhdError(Exception):
    pass


class LicenceError(EodhdError):
    """Vendor data may be fetched only with the licensee's own key (DAT-15, USR-05)."""

    reason = ReasonCode.LICENCE


class BudgetExceededError(EodhdError):
    """The call would exceed the plan's budget: fail closed, WARN DATA_BUDGET (DAT-23)."""

    reason = ReasonCode.DATA_BUDGET


class HistoryDepthError(BudgetExceededError):
    """The request needs data older than the plan serves: fail closed (DAT-23)."""


def gmt_date(now: datetime) -> date:
    return ensure_utc(now).astimezone(UTC).date()


def years_before(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:  # 29 Feb
        return d.replace(year=d.year - years, day=28)


def urllib_transport(url: str, params: Mapping[str, str]) -> bytes:  # pragma: no cover - network
    """The production transport (stdlib only; proxy and CA bundle from the environment)."""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    if not full.startswith("https://"):
        raise EodhdError("EODHD is reached over https only")
    req = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        body: bytes = resp.read()
    return body


# ---------------------------------------------------------------------------
# Call budget (DAT-23)
# ---------------------------------------------------------------------------


class CallBudget:
    """Counts every vendor request in ``vendor_call_log`` (committed before the call)."""

    def __init__(self, engine: Engine, plan: EodhdPlan, vendor: str = VENDOR) -> None:
        self.engine = engine
        self.plan = plan
        self.vendor = vendor

    def used(self, day: date) -> int:
        with Session(self.engine) as s:
            n = s.execute(
                select(func.count())
                .select_from(VendorCallLog)
                .where(VendorCallLog.vendor == self.vendor, VendorCallLog.gmt_date == day)
            ).scalar_one()
        return int(n)

    def remaining(self, now: datetime) -> int:
        return max(0, self.plan.calls_per_day - self.used(gmt_date(now)))

    def reserve(self, endpoint: str, now: datetime) -> None:
        """Record one call, or raise ``BudgetExceededError`` without recording it."""
        now = ensure_utc(now)
        day = gmt_date(now)
        with Session(self.engine) as s, s.begin():
            used = s.execute(
                select(func.count())
                .select_from(VendorCallLog)
                .where(VendorCallLog.vendor == self.vendor, VendorCallLog.gmt_date == day)
            ).scalar_one()
            if used + 1 > self.plan.calls_per_day:
                raise BudgetExceededError(
                    f"DATA_BUDGET: {endpoint} refused, {used} of {self.plan.calls_per_day} "
                    f"EODHD calls already used on {day} (GMT); failing closed"
                )
            minute = s.execute(
                select(func.count())
                .select_from(VendorCallLog)
                .where(
                    VendorCallLog.vendor == self.vendor,
                    VendorCallLog.ts > now - timedelta(minutes=1),
                )
            ).scalar_one()
            if minute + 1 > self.plan.calls_per_minute:
                raise BudgetExceededError(
                    f"DATA_BUDGET: {endpoint} refused, per-minute limit "
                    f"{self.plan.calls_per_minute} reached; failing closed"
                )
            s.add(VendorCallLog(ts=now, vendor=self.vendor, endpoint=endpoint, gmt_date=day))

    def calls_since(self, endpoint_prefix: str, since: datetime) -> list[str]:
        with Session(self.engine) as s:
            return list(
                s.execute(
                    select(VendorCallLog.endpoint).where(
                        VendorCallLog.vendor == self.vendor,
                        VendorCallLog.endpoint.startswith(endpoint_prefix),
                        VendorCallLog.ts >= ensure_utc(since),
                    )
                ).scalars()
            )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


def _parse_json(body: bytes, what: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(body, parse_float=Decimal, parse_int=Decimal)
    except ValueError as exc:
        raise EodhdError(f"EODHD {what}: response is not JSON") from exc
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise EodhdError(f"EODHD {what}: unexpected response shape")
    return data


def _dec(v: Any, *, required: bool = True) -> Decimal | None:
    if v is None or v == "":
        if required:
            raise EodhdError("EODHD: missing numeric field")
        return None
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except ArithmeticError as exc:
        raise EodhdError(f"EODHD: bad number {v!r}") from exc


@dataclass(frozen=True)
class EodBar:
    trade_date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    adjusted_close: Decimal | None
    volume: int | None


@dataclass(frozen=True)
class VendorDiv:
    ex_date: date
    value: Decimal
    unadjusted_value: Decimal | None
    currency: str | None
    record_date: date | None
    payment_date: date | None


def parse_eod(body: bytes) -> list[EodBar]:
    out: list[EodBar] = []
    for r in _parse_json(body, "eod"):
        try:
            d = date.fromisoformat(str(r["date"]))
        except (KeyError, ValueError) as exc:
            raise EodhdError("EODHD eod: bad or missing date") from exc
        close = _dec(r.get("close"))
        assert close is not None
        vol = _dec(r.get("volume"), required=False)
        out.append(
            EodBar(
                trade_date=d,
                open=_dec(r.get("open"), required=False),
                high=_dec(r.get("high"), required=False),
                low=_dec(r.get("low"), required=False),
                close=close,
                adjusted_close=_dec(r.get("adjusted_close"), required=False),
                volume=None if vol is None else int(vol),
            )
        )
    return out


def _opt_date(v: Any) -> date | None:
    if v in (None, "", "0000-00-00"):
        return None
    return date.fromisoformat(str(v))


def parse_dividends(body: bytes) -> list[VendorDiv]:
    out: list[VendorDiv] = []
    for r in _parse_json(body, "div"):
        value = _dec(r.get("value"))
        assert value is not None
        out.append(
            VendorDiv(
                ex_date=date.fromisoformat(str(r["date"])),
                value=value,
                unadjusted_value=_dec(r.get("unadjustedValue"), required=False),
                currency=r.get("currency"),
                record_date=_opt_date(r.get("recordDate")),
                payment_date=_opt_date(r.get("paymentDate")),
            )
        )
    return out


@dataclass
class EodhdClient:
    """One user's EODHD access (their own licence, DAT-15)."""

    transport: Transport
    budget: CallBudget
    store: RawStore
    user: str
    licensee: str
    token: Callable[[], SecretValue] = field(default=lambda: read_secret("eodhd_api_token"))

    def __post_init__(self) -> None:
        if self.licensee != self.user or self.store.licensee != self.user:
            raise LicenceError(
                f"LICENCE: EODHD data for user {self.user} may only be fetched with that "
                "user's own key and stored under that user as licensee (DAT-15)"
            )

    def _check_depth(self, start: date, now: datetime) -> None:
        oldest = years_before(gmt_date(now), self.budget.plan.history_years)
        if start < oldest:
            raise HistoryDepthError(
                f"DATA_BUDGET: {start} is older than the {self.budget.plan.plan} plan's "
                f"{self.budget.plan.history_years}-year history ({oldest}); not calling the API"
            )

    def _call(
        self, endpoint: str, path: str, params: dict[str, str], now: datetime, name: str
    ) -> tuple[RawFile, bytes]:
        token = self.token().reveal()  # a missing key fails before any call is counted
        self.budget.reserve(endpoint, now)  # counted before the request is sent
        try:
            body = self.transport(
                f"{BASE_URL}/{path}", {**params, "api_token": token, "fmt": "json"}
            )
        except Exception as exc:
            # Never let a transport error carry the URL with the key.
            raise EodhdError(f"EODHD {endpoint}: request failed ({type(exc).__name__})") from None
        raw = self.store.put("eodhd", name, body, now)
        return raw, body

    def eod(
        self, symbol: str, start: date, end: date, now: datetime, *, kind: str = "eod"
    ) -> tuple[RawFile, list[EodBar]]:
        """One end-of-day range request (counts as one call, DAT-23)."""
        if start > end:
            raise ValueError("start after end")
        self._check_depth(start, now)
        raw, body = self._call(
            f"{kind}:{symbol}",
            f"eod/{symbol}.{EXCHANGE_SUFFIX}",
            {"from": start.isoformat(), "to": end.isoformat()},
            now,
            f"eod_{symbol}_{start:%Y%m%d}_{end:%Y%m%d}",
        )
        return raw, parse_eod(body)

    def dividends(self, symbol: str, start: date, now: datetime) -> tuple[RawFile, list[VendorDiv]]:
        self._check_depth(start, now)
        raw, body = self._call(
            f"div:{symbol}",
            f"div/{symbol}.{EXCHANGE_SUFFIX}",
            {"from": start.isoformat()},
            now,
            f"div_{symbol}_{start:%Y%m%d}",
        )
        return raw, parse_dividends(body)


# ---------------------------------------------------------------------------
# Storing parsed rows (append-only, bitemporal)
# ---------------------------------------------------------------------------


def store_bars(
    session: Session,
    instrument_id: int,
    bars: Iterable[EodBar],
    raw: RawFile,
    licensee: str,
    *,
    only_dates: set[date] | None = None,
) -> int:
    n = 0
    for b in bars:
        if only_dates is not None and b.trade_date not in only_dates:
            continue
        session.add(
            RawBar(
                instrument_id=instrument_id,
                trade_date=b.trade_date,
                source="eodhd",
                fetch_time=raw.fetch_time,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                vendor_adjusted_close=b.adjusted_close,
                file_hash=raw.sha256,
                licensee=licensee,
            )
        )
        n += 1
    session.flush()
    return n


def store_dividends(
    session: Session, instrument_id: int, divs: Iterable[VendorDiv], raw: RawFile, licensee: str
) -> int:
    n = 0
    for d in divs:
        session.add(
            VendorDividend(
                instrument_id=instrument_id,
                ex_date=d.ex_date,
                fetch_time=raw.fetch_time,
                value=d.value,
                unadjusted_value=d.unadjusted_value,
                currency=d.currency,
                record_date=d.record_date,
                payment_date=d.payment_date,
                file_hash=raw.sha256,
                licensee=licensee,
            )
        )
        n += 1
    session.flush()
    return n


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@dataclass
class FetchOutcome:
    symbol: str
    requested: tuple[date, date] | None = None
    bars_stored: int = 0
    dividends_stored: int = 0
    raw_files: list[RawFile] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)  # DATA_BUDGET etc.

    @property
    def budget_blocked(self) -> bool:
        return any(w.startswith("DATA_BUDGET") for w in self.warnings)


def fetch_vendor_data(
    session: Session,
    client: EodhdClient,
    cal: AsxCalendar,
    symbols: Iterable[str],
    now: datetime,
    *,
    include_dividends: bool = True,
) -> list[FetchOutcome]:
    """The 19:30 job and its retries (§4): one range request per instrument.

    The range runs from the day after the last stored bar to the latest close
    that may be read now (never before 16:25 on its day, §4). The 21:30 and 07:00
    retries pass ``include_dividends=False``: only the bars are retried.
    """
    end = cal.latest_readable_close(now)
    out: list[FetchOutcome] = []
    for symbol in symbols:
        res = FetchOutcome(symbol)
        out.append(res)
        inst = require_instrument(session, symbol)
        if end is None:
            continue
        last = last_stored_bar_date(session, inst.id, "eodhd")
        start = (
            last + timedelta(days=1)
            if last is not None
            else years_before(gmt_date(now), client.budget.plan.history_years)
        )
        try:
            if start <= end:
                res.requested = (start, end)
                raw, bars = client.eod(symbol, start, end, now)
                res.raw_files.append(raw)
                res.bars_stored = store_bars(
                    session, inst.id, [b for b in bars if start <= b.trade_date <= end], raw,
                    client.licensee,
                )  # fmt: skip
                session.commit()  # progress is durable; a rerun resumes from here (OPS-01)
            if include_dividends and "dividends" in client.budget.plan.daily_requests:
                div_start = years_before(gmt_date(now), client.budget.plan.history_years)
                raw, divs = client.dividends(symbol, div_start, now)
                res.raw_files.append(raw)
                res.dividends_stored = store_dividends(session, inst.id, divs, raw, client.licensee)
                session.commit()
        except BudgetExceededError as exc:
            res.warnings.append(str(exc))
    return out


def fetch_by_hand(
    session: Session,
    client: EodhdClient,
    symbol: str,
    start: date,
    end: date,
    now: datetime,
) -> FetchOutcome:
    """``trader fetch --symbol S --from D --to D`` inside the same budget (DAT-23)."""
    inst = require_instrument(session, symbol)
    res = FetchOutcome(symbol, requested=(start, end))
    try:
        raw, bars = client.eod(symbol, start, end, now, kind="eod_manual")
    except BudgetExceededError as exc:
        res.warnings.append(str(exc))
        return res
    res.raw_files.append(raw)
    res.bars_stored = store_bars(
        session, inst.id, [b for b in bars if start <= b.trade_date <= end], raw, client.licensee
    )
    session.commit()
    return res


# ---------------------------------------------------------------------------
# Sunday re-download and restatement diff (DAT-10)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Restatement:
    trade_date: date
    old_close: Decimal
    new_close: Decimal

    @property
    def rel_change(self) -> Decimal:
        return abs(self.new_close - self.old_close) / self.old_close


@dataclass
class RedownloadResult:
    symbol: str
    compared: int = 0
    restated: list[Restatement] = field(default_factory=list)
    new_dates: int = 0
    level: str = "OK"  # OK, WARN or BLOCK (DAT-10)
    deferred: bool = False  # did not fit in today's budget; spread to a later day
    warnings: list[str] = field(default_factory=list)


def restatement_level(
    restated: list[Restatement], compared: int, block_rows: int, block_pct: Decimal
) -> str:
    """DAT-10: any change is WARN; more than ``block_rows`` rows or more than
    ``block_pct`` is BLOCK. "More than 0.5%" is read as a stored close that moved
    by more than 0.5% (docs/DECISIONS.md D-10: reading it as 0.5% of the compared
    rows would make a single changed row a BLOCK in any window under 200 rows,
    which leaves the five-row rule with no effect). ``compared`` is reported only."""
    del compared
    if not restated:
        return "OK"
    if len(restated) > block_rows:
        return "BLOCK"
    if any(r.rel_change > block_pct for r in restated):
        return "BLOCK"
    return "WARN"


def last_redownload_anchor(now: datetime, cal_weekday: int = 6) -> datetime:
    """Start of the current re-download week: the latest Sunday 00:00 Australia/Sydney."""
    local = ensure_utc(now).astimezone(ASX_TZ)
    d = local.date() - timedelta(days=(local.weekday() - cal_weekday) % 7)
    return datetime(d.year, d.month, d.day, tzinfo=ASX_TZ).astimezone(UTC)


def pending_redownloads(budget: CallBudget, symbols: Iterable[str], now: datetime) -> list[str]:
    """Instruments whose weekly re-download has not run since the latest Sunday."""
    done = {
        e.split(":", 1)[1] for e in budget.calls_since("redownload:", last_redownload_anchor(now))
    }
    return [s for s in symbols if s not in done]


def full_redownload(
    session: Session,
    client: EodhdClient,
    cal: AsxCalendar,
    symbols: Iterable[str],
    now: datetime,
    *,
    block_rows: int,
    block_pct: Decimal,
    keep_calls: int = 0,
) -> list[RedownloadResult]:
    """The Sunday 03:00 job (DAT-10, DAT-23): re-download the plan's window and diff it
    against the stored raw closes. Instruments that do not fit in the budget (after
    keeping ``keep_calls`` for scheduled calls) are deferred to a later day; call
    this again daily with the pending list until it is empty."""
    end = cal.latest_readable_close(now)
    results: list[RedownloadResult] = []
    for symbol in pending_redownloads(client.budget, symbols, now):
        res = RedownloadResult(symbol)
        results.append(res)
        if end is None:
            continue
        if client.budget.remaining(now) <= keep_calls:
            res.deferred = True
            continue
        inst = require_instrument(session, symbol)
        start = years_before(gmt_date(now), client.budget.plan.history_years)
        before = latest_bars(session, inst.id, "eodhd", start, end)
        try:
            raw, bars = client.eod(symbol, start, end, now, kind="redownload")
        except BudgetExceededError as exc:
            res.deferred = True
            res.warnings.append(str(exc))
            continue
        changed: set[date] = set()
        for b in bars:
            old = before.get(b.trade_date)
            if old is None:
                if start <= b.trade_date <= end:
                    res.new_dates += 1
                    changed.add(b.trade_date)
                continue
            res.compared += 1
            if b.close != old.close:
                res.restated.append(Restatement(b.trade_date, old.close, b.close))
                changed.add(b.trade_date)
        # Raw data is stored unchanged: the response file is kept, and the restated or
        # new bars are appended as new rows with this fetch time (nothing is updated).
        store_bars(session, inst.id, bars, raw, client.licensee, only_dates=changed)
        res.level = restatement_level(res.restated, res.compared, block_rows, block_pct)
        if res.level != "OK":
            session.add(
                QcEvent(
                    ts=raw.fetch_time,
                    instrument_id=inst.id,
                    trade_date=max(r.trade_date for r in res.restated),
                    check_id="DAT-10",
                    level=res.level,
                    detail={
                        "reason": ReasonCode.DATA_RESTATED.value,
                        "compared": res.compared,
                        "restated": [
                            {"date": r.trade_date.isoformat(), "old": str(r.old_close),
                             "new": str(r.new_close)}
                            for r in res.restated
                        ],
                        "file_hash": raw.sha256,
                    },
                )
            )  # fmt: skip
        session.commit()
    return results
