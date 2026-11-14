"""Monthly reported spreads (SYS-30) and the instrument-identity guard (SYS-31).

SYS-30: each month the reported spread of every live ETF is read from the ASX
monthly investment products report and entered (``trader import spread``). A
spread above ``data.spread_warn`` (0.04%) raises a WARN and a review; at
``data.spread_exclude`` (0.07%) or wider the ETF may not be a live sleeve.

SYS-31: replacing a live instrument, a base weight or a benchmark is a new
hypothesis card and goes through change control. The identity of the live
book is part of ``common.yaml``, so any such change alters
``approved_common_hash`` and the trader refuses to run until the user approves
it (OPS-10); ``instrument_identity`` is the fingerprint stored with the frozen
card set so that the registry (M3) can refuse a config whose identity differs
from the card's.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.config import CommonConfig
from trader.data.instruments import require_instrument
from trader.data.models import SpreadReport, write_market_audit
from trader.timeutil import ensure_utc

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class SpreadVerdict:
    symbol: str
    month: str
    spread: Decimal
    level: str  # OK, WARN (review) or EXCLUDE (may not be a live sleeve)


def enter_spread(
    session: Session, symbol: str, month: str, spread: Decimal, source: str, now: datetime
) -> SpreadReport:
    if not _MONTH_RE.fullmatch(month):
        raise ValueError(f"month must be YYYY-MM, got {month!r}")
    if not isinstance(spread, Decimal) or not 0 <= spread < 1:
        raise ValueError("spread is a Decimal fraction, e.g. 0.0002 for 0.02%")
    inst = require_instrument(session, symbol)
    row = SpreadReport(
        instrument_id=inst.id, month=month, fetch_time=ensure_utc(now), spread=spread, source=source
    )
    session.add(row)
    session.flush()
    write_market_audit(
        session, actor="user", action="import.spread",
        payload={"symbol": symbol, "month": month, "spread": spread, "source": source},
    )  # fmt: skip
    return row


def spread_level(spread: Decimal, warn: Decimal, exclude: Decimal) -> str:
    if spread >= exclude:
        return "EXCLUDE"
    if spread > warn:
        return "WARN"
    return "OK"


def spread_verdicts(session: Session, common: CommonConfig, month: str) -> list[SpreadVerdict]:
    """SYS-30 for every live sleeve; a sleeve with no figure for the month is a WARN."""
    out: list[SpreadVerdict] = []
    for sym in common.sleeves:
        inst = require_instrument(session, sym)
        row = session.execute(
            select(SpreadReport)
            .where(SpreadReport.instrument_id == inst.id, SpreadReport.month == month)
            .order_by(SpreadReport.fetch_time.desc())
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            out.append(SpreadVerdict(sym, month, Decimal(-1), "WARN"))
            continue
        lvl = spread_level(row.spread, common.data.spread_warn, common.data.spread_exclude)
        out.append(SpreadVerdict(sym, month, row.spread, lvl))
    return out


def instrument_identity(common: CommonConfig) -> str:
    """Fingerprint of the live sleeves, base weights and benchmarks (SYS-31)."""
    ident = {
        "rule": common.rule,
        "sleeves": {k: str(v.base_weight) for k, v in sorted(common.sleeves.items())},
        "B1": {k: str(v) for k, v in sorted(common.benchmarks.B1.weights.items())},
        "B2": {k: str(v) for k, v in sorted(common.benchmarks.B2.weights.items())},
    }
    return hashlib.sha256(json.dumps(ident, sort_keys=True).encode()).hexdigest()


def identity_change_needs_card(old: CommonConfig, new: CommonConfig) -> bool:
    """True if ``new`` replaces a live instrument, a base weight or a benchmark (SYS-31)."""
    return instrument_identity(old) != instrument_identity(new)
