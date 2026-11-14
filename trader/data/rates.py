"""RBA series (F11.1 AUD/USD, F1.1 cash rate target) and the CPI table (§6, DAT-07, TAX-04).

* The RBA statistical-table CSVs are fetched with an injected transport, stored
  unchanged (``RawStore``, source ``rba``) and parsed into the bitemporal ``fx``
  and ``cash_rate`` tables. A date is appended only if it is new or its value
  changed; nothing is updated in place.
* The RBA does not publish on NSW public and bank holidays, so the FX calendar
  differs from the ASX one: ``value_on`` carries the last published value
  forward (§5).
* DAT-07: a move of more than ``data.fx_move_warn`` (3%) between consecutive
  published rates raises a WARN (``qc_event`` DAT-07).
* CPI (v2.10 + R37 correction, loader stub): All Groups CPI, weighted average of
  the eight capital cities, first-published values, entered per quarter into
  ``cpi``. The indexation factor is rounded to 3 decimal places half-up and no
  indexation applies when it is <= 1 (TAX-04; the engine is M3).
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from itertools import pairwise
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.data.models import CashRate, Cpi, Fx, QcEvent, write_market_audit
from trader.data.store import RawFile, RawStore
from trader.timeutil import ensure_utc

F11_URL = "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv"
F1_URL = "https://www.rba.gov.au/statistics/tables/csv/f1.1-data.csv"
AUDUSD = "FXRUSD"
CASH_RATE_TARGET = "FIRMMCRTD"
SOURCE_F11 = "RBA F11.1 (CC BY 4.0)"
SOURCE_F1 = "RBA F1.1 (CC BY 4.0)"

RbaTransport = Callable[[str], bytes]


class RbaError(Exception):
    pass


_DATE_RE = re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}$")
_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
)}  # fmt: skip


def _rba_date(s: str) -> date:
    day, mon, year = s.split("-")
    return date(int(year), _MONTHS[mon.title()], int(day))


def parse_rba_csv(body: bytes, series_id: str) -> dict[date, Decimal]:
    """Parse one series from an RBA statistical-table CSV (``Series ID`` header row)."""
    text = body.decode("utf-8-sig", errors="strict")
    rows = list(csv.reader(io.StringIO(text)))
    header = next((r for r in rows if r and r[0].strip() == "Series ID"), None)
    if header is None:
        raise RbaError("RBA CSV: no 'Series ID' row")
    try:
        col = [c.strip() for c in header].index(series_id)
    except ValueError as exc:
        raise RbaError(f"RBA CSV: series {series_id} not found") from exc
    out: dict[date, Decimal] = {}
    for r in rows:
        if not r or not _DATE_RE.match(r[0].strip()) or len(r) <= col:
            continue
        cell = r[col].strip()
        if not cell:
            continue  # no publication that day
        try:
            out[_rba_date(r[0].strip())] = Decimal(cell)
        except InvalidOperation as exc:
            raise RbaError(f"RBA CSV: bad value {cell!r}") from exc
    if not out:
        raise RbaError(f"RBA CSV: no values for {series_id}")
    return out


SeriesModel = Any  # type[Fx] | type[CashRate]


def _known(session: Session, model: SeriesModel, series: str) -> dict[date, Decimal]:
    latest: dict[date, Decimal] = {}
    q = select(model).where(model.series == series).order_by(model.date, model.fetch_time)
    for row in session.execute(q).scalars():
        latest[row.date] = row.value
    return latest


def store_series(
    session: Session,
    model: SeriesModel,
    series: str,
    values: Mapping[date, Decimal],
    raw: RawFile,
    source: str,
) -> int:
    """Append rows for new dates or changed values (bitemporal, DAT-18)."""
    known = _known(session, model, series)
    n = 0
    for d, v in sorted(values.items()):
        if known.get(d) == v:
            continue
        session.add(model(series=series, date=d, fetch_time=raw.fetch_time, value=v, source=source))
        n += 1
    session.flush()
    return n


def value_on(
    session: Session, model: SeriesModel, series: str, d: date, as_of: datetime | None = None
) -> tuple[date, Decimal] | None:
    """The last published value on or before ``d`` (carried forward over RBA holidays)."""
    q = select(model).where(model.series == series, model.date <= d)
    if as_of is not None:
        q = q.where(model.fetch_time <= ensure_utc(as_of))
    row = session.execute(q.order_by(model.date.desc(), model.fetch_time.desc()).limit(1)).scalar()
    return None if row is None else (row.date, row.value)


@dataclass(frozen=True)
class FxMove:
    day: date
    prev_day: date
    move: Decimal


def fx_moves_above(values: Mapping[date, Decimal], threshold: Decimal) -> list[FxMove]:
    """DAT-07: consecutive published rates that moved by more than ``threshold``."""
    out: list[FxMove] = []
    days = sorted(values)
    for prev, cur in pairwise(days):
        move = abs(values[cur] / values[prev] - 1)
        if move > threshold:
            out.append(FxMove(cur, prev, move))
    return out


def fetch_rba(
    session: Session,
    transport: RbaTransport,
    store: RawStore,
    now: datetime,
    *,
    fx_move_warn: Decimal,
) -> list[FxMove]:
    """19:30 job part: RBA F11.1 AUD/USD and F1.1 cash rate target (§4)."""
    body = transport(F11_URL)
    raw = store.put("rba", "f11.1", body, now, ext="csv")
    fx = parse_rba_csv(body, AUDUSD)
    known_before = _known(session, Fx, AUDUSD)
    store_series(session, Fx, AUDUSD, fx, raw, SOURCE_F11)
    body = transport(F1_URL)
    raw1 = store.put("rba", "f1.1", body, now, ext="csv")
    store_series(session, CashRate, CASH_RATE_TARGET, parse_rba_csv(body, CASH_RATE_TARGET), raw1,
                 SOURCE_F1)  # fmt: skip
    merged = {**known_before, **fx}
    new_days = {d for d in fx if d not in known_before}
    moves = [m for m in fx_moves_above(merged, fx_move_warn) if m.day in new_days]
    for m in moves:
        session.add(
            QcEvent(
                ts=ensure_utc(now),
                instrument_id=None,
                trade_date=m.day,
                check_id="DAT-07",
                level="WARN",
                detail={"series": AUDUSD, "prev_day": m.prev_day.isoformat(), "move": str(m.move)},
            )
        )
    session.flush()
    return moves


# ---------------------------------------------------------------------------
# CPI (TAX-04; v2.10 + R37 correction) - table and loader stub
# ---------------------------------------------------------------------------

CPI_SERIES_NOTE = "ABS All Groups CPI, weighted average of eight capital cities, first published"
_QUARTER_RE = re.compile(r"^\d{4}Q[1-4]$")


def load_cpi(
    session: Session, rows: Iterable[tuple[str, Decimal]], source: str, now: datetime
) -> int:
    """Insert first-published CPI values per quarter (insert-only, audited)."""
    n = 0
    for quarter, value in rows:
        if not _QUARTER_RE.fullmatch(quarter):
            raise ValueError(f"quarter must look like 2027Q3, got {quarter!r}")
        if not isinstance(value, Decimal) or value <= 0:
            raise ValueError("CPI value must be a positive Decimal")
        session.add(Cpi(quarter=quarter, fetch_time=ensure_utc(now), value=value, source=source))
        n += 1
    session.flush()
    write_market_audit(
        session, actor="user", action="import.cpi", payload={"rows": n, "source": source}
    )
    return n


def indexation_factor(cpi_event: Decimal, cpi_base: Decimal) -> Decimal | None:
    """Factor rounded to 3 decimal places half-up; ``None`` (no indexation) if <= 1."""
    factor = (cpi_event / cpi_base).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return None if factor <= 1 else factor
