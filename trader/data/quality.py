"""Data-quality checks, per-symbol verdicts and overrides (§6: DAT-01 to DAT-13, DAT-17, DAT-19).

Every symbol gets a verdict for the previous trading day's close: ``OK``,
``WARN``, ``SINGLE_SOURCE`` or ``BLOCK``. A symbol with a BLOCK verdict does not
trade; the others proceed. Thresholds come from ``data.*`` in common.yaml.

* Each failing check writes a ``qc_event`` (check id, level, detail); each
  verdict writes a ``qc_event`` with check id ``VERDICT``. A verdict that is not
  BLOCK writes the close to the validated set (``validated_close``); a BLOCKed or
  quarantined bar is never written there until ``trader qc override`` names the
  close to use (DAT-17).
* The verdict also says which actions it allows: ``buy_ok``, ``sell_ok`` and
  ``evaluate_ok`` implement DAT-02 cases (a), (b), (c) and the DAT-22 hold.
* Levels (DAT-17): INFO goes to the log, WARN to the digest, BLOCK refuses the
  symbol.

The functions take ``now`` explicitly (no hidden clock) so that each rule can be
tested at the times the schedule runs it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from trader.calendar import AsxCalendar
from trader.config import DataConfig
from trader.data.flex import Mark, latest_mark, mark_for_day
from trader.data.instruments import require_instrument, tick_size
from trader.data.issuer import DistBlock, effective_distributions, missing_distributions
from trader.data.models import CorpAction, Distribution, QcEvent, RawBar, ValidatedClose
from trader.data.store import RawStore, latest_bar, latest_bars, validated_closes
from trader.enums import ReasonCode, Verdict
from trader.timeutil import asx_local_to_utc, ensure_utc

_RANK = {Verdict.OK: 0, Verdict.SINGLE_SOURCE: 1, Verdict.WARN: 2, Verdict.BLOCK: 3}


class NotATradingDayError(ValueError):
    """DAT-08: the day is not a trading day in ``calendar`` (whole run)."""


@dataclass
class SymbolVerdict:
    symbol: str
    trade_date: date
    level: Verdict
    close: Decimal | None = None
    close_source: str | None = None
    reasons: list[str] = field(default_factory=list)
    buy_ok: bool = False
    sell_ok: bool = False
    evaluate_ok: bool = False
    backfill: bool = False
    quarantined: bool = False
    detail: dict[str, Any] = field(default_factory=dict)

    def raise_to(self, level: Verdict, reason: str) -> None:
        if _RANK[level] > _RANK[self.level]:
            self.level = level
        self.reasons.append(reason)


@dataclass(frozen=True)
class Schedule:
    """The schedule times the DAT-01 rule depends on (Australia/Sydney)."""

    warn_at: time  # 21:30 retry: WARN if a bar is still missing
    validate_at: time  # 08:00 next trading day: BLOCK if still missing

    @classmethod
    def from_config(cls, schedule: Any) -> Schedule:
        return cls(warn_at=schedule.fetch_vendor_data[1], validate_at=schedule.validate_data)


# ---------------------------------------------------------------------------
# Single checks (pure)
# ---------------------------------------------------------------------------


def dat01_missing_level(now: datetime, day: date, cal: AsxCalendar, sched: Schedule) -> str:
    """DAT-01: a missing bar is pending until 21:30 on D, WARN from then, BLOCK from the
    08:00 validation on the next trading day."""
    now = ensure_utc(now)
    block_at = asx_local_to_utc(cal.next_trading_day(day), sched.validate_at)
    if now >= block_at:
        return "BLOCK"
    if now >= asx_local_to_utc(day, sched.warn_at):
        return "WARN"
    return "INFO"


def is_late(bar: RawBar, day: date, cal: AsxCalendar, sched: Schedule) -> bool:
    """A bar fetched after the 08:00 deadline of its day arrived late (DAT-01)."""
    return ensure_utc(bar.fetch_time) >= asx_local_to_utc(
        cal.next_trading_day(day), sched.validate_at
    )


def dat03_sanity(bar: RawBar) -> list[str]:
    """DAT-03: prices > 0; high >= max(open, close); low <= min(open, close); volume >= 0."""
    problems: list[str] = []
    prices = [p for p in (bar.open, bar.high, bar.low, bar.close) if p is not None]
    if any(p <= 0 for p in prices):
        problems.append("price <= 0")
    if bar.high is not None and bar.high < max(p for p in (bar.open, bar.close) if p is not None):
        problems.append("high < max(open, close)")
    if bar.low is not None and bar.low > min(p for p in (bar.open, bar.close) if p is not None):
        problems.append("low > min(open, close)")
    if bar.volume is not None and bar.volume < 0:
        problems.append("volume < 0")
    if bar.high is not None and bar.low is not None and bar.high < bar.low:
        problems.append("high < low")
    return problems


def within_ok(close: Decimal, mark: Decimal, ok: Decimal, tick: Decimal | None) -> bool:
    diff = abs(close - mark)
    return diff <= ok * mark or (tick is not None and diff <= tick)


def dat02_level(close: Decimal, mark: Decimal, cfg: DataConfig, tick: Decimal | None) -> Verdict:
    """DAT-02: within 0.1% or one tick OK; 0.1-0.5% WARN; above 0.5% BLOCK."""
    if within_ok(close, mark, cfg.cross_source.ok, tick):
        return Verdict.OK
    if abs(close - mark) <= cfg.cross_source.block * mark:
        return Verdict.WARN
    return Verdict.BLOCK


def dat04_is_spike(
    close: Decimal,
    last_validated: Decimal,
    recent_validated: Sequence[Decimal],
    cfg: DataConfig,
) -> tuple[bool, Decimal]:
    """DAT-04: |return vs last validated close| > 8 x 60-day mean absolute change of
    validated closes, or > 15%. Returns (spike, absolute return)."""
    ret = abs(close / last_validated - 1)
    if ret > cfg.spike.abs_return:
        return True, ret
    changes = [abs(b / a - 1) for a, b in pairwise(recent_validated)]
    changes = changes[-60:]
    if len(changes) >= 2:
        mean = sum(changes, Decimal(0)) / len(changes)
        if mean > 0 and ret > cfg.spike.mult_of_mean_abs_60d * mean:
            return True, ret
    return False, ret


def dat06_stale(bars: Sequence[RawBar], sessions: int) -> bool:
    """DAT-06: identical close with zero volume for ``sessions`` or more sessions."""
    if len(bars) < sessions:
        return False
    last = bars[-sessions:]
    return all(b.volume == 0 for b in last) and len({b.close for b in last}) == 1


# ---------------------------------------------------------------------------
# DAT-11 total-return checks (pure)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrFlag:
    day: date
    check: str
    level: str  # WARN or BLOCK
    detail: str


def dat11_checks(
    closes: Mapping[date, Decimal],
    adjusted: Mapping[date, Decimal],
    tr_net: Mapping[date, Decimal],
    issuer_amounts: Mapping[date, Decimal],
    split_dates: set[date],
    cfg: DataConfig,
    *,
    missing_amount_dates: set[date] | None = None,
    restated_dates: set[date] | None = None,
) -> list[TrFlag]:
    """Daily DAT-11 checks over aligned series.

    * daily return gap own ``tr_net`` vs vendor adjusted close: > 5 bp on a
      non-ex-date or > 25 bp on an ex-date flags;
    * the adjusted/raw ratio may change only on ex or split dates and must not
      fall as dates advance;
    * implied dividend within 1% of the issuer amount.

    Level WARN (``TR_CHECK``), BLOCK only if the gap is on a date with no issuer
    amount (DAT-22) or whose stored raw close changed (DAT-10).
    """
    missing = missing_amount_dates or set()
    restated = restated_dates or set()
    out: list[TrFlag] = []
    days = sorted(d for d in closes if d in adjusted and d in tr_net)
    bp = Decimal("0.0001")
    for prev, d in pairwise(days):
        is_ex = d in issuer_amounts or d in split_dates or d in missing
        own = tr_net[d] / tr_net[prev] - 1
        vend = adjusted[d] / adjusted[prev] - 1
        gap = abs(own - vend)
        limit = (cfg.tr_gap_bp.ex if is_ex else cfg.tr_gap_bp.non_ex) * bp
        if gap > limit:
            level = "BLOCK" if (d in missing or d in restated) else "WARN"
            out.append(TrFlag(d, "return_gap", level, f"gap {gap} > {limit}"))
        r_prev = adjusted[prev] / closes[prev]
        r = adjusted[d] / closes[d]
        if r != r_prev:
            if not is_ex:
                level = "BLOCK" if d in missing else "WARN"
                out.append(TrFlag(d, "ratio_change_off_ex", level, f"{r_prev} -> {r}"))
            if r < r_prev:
                out.append(TrFlag(d, "ratio_fell", "WARN", f"{r_prev} -> {r}"))
            if d in issuer_amounts and d not in split_dates:
                implied = closes[prev] * (1 - r_prev / r)
                amt = issuer_amounts[d]
                if amt > 0 and abs(implied - amt) / amt > cfg.implied_dividend_tolerance:
                    out.append(TrFlag(d, "implied_dividend", "WARN", f"implied {implied} vs {amt}"))
    return out


def dat11_distribution_count(
    vendor_ex_dates: Iterable[date], issuer_ex_dates: Iterable[date], year: int
) -> TrFlag | None:
    """Distributions per year match the issuer schedule (DAT-11)."""
    v = sum(1 for d in vendor_ex_dates if d.year == year)
    i = sum(1 for d in issuer_ex_dates if d.year == year)
    if v != i:
        return TrFlag(
            date(year, 12, 31), "distributions_per_year", "WARN", f"vendor {v} issuer {i}"
        )
    return None


def dat11_yearly_return(
    own_return: Decimal, issuer_return: Decimal, cfg: DataConfig, year_end: date
) -> TrFlag | None:
    """Yearly total return within 0.5% of the issuer's published fund return (DAT-11).

    The issuer's figure has no table in §12 (docs/DECISIONS.md D-12): it is passed in.
    """
    if abs(own_return - issuer_return) > cfg.yearly_tr_tolerance:
        return TrFlag(year_end, "yearly_return", "WARN", f"own {own_return} issuer {issuer_return}")
    return None


# ---------------------------------------------------------------------------
# DAT-13 order-time reference and checks (pure)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Reference:
    price: Decimal
    adjusted: bool
    dist_missing: bool  # an ex-date in the window has no amount: buys are held (DAT-22)


def dat13_reference(
    last_close: Decimal,
    last_close_date: date,
    distributions: Mapping[date, Decimal | None],
    today: date,
) -> Reference:
    """Last validated raw close minus any cash distribution per unit with an ex-date
    after that close and on or before today (DAT-13). A missing amount leaves the
    reference unadjusted and holds buys (DAT-22)."""
    in_window = {ex: amt for ex, amt in distributions.items() if last_close_date < ex <= today}
    if any(a is None for a in in_window.values()):
        return Reference(last_close, adjusted=False, dist_missing=True)
    total = sum((a for a in in_window.values() if a is not None), Decimal(0))
    return Reference(last_close - total, adjusted=bool(in_window), dist_missing=False)


def dat13_held(limit: Decimal, reference: Decimal, cfg: DataConfig) -> bool:
    """An order whose limit is more than 2% from the reference is held (SNAPSHOT_GAP)."""
    return abs(limit - reference) > cfg.snapshot_gap_hold * reference


def dat13_confirmed_exit(
    *,
    side: str,
    kind: str,
    bid_1130: Decimal | None,
    bid_1300: Decimal | None,
    quote_1300_valid: bool,
    halted: bool | None,
    limit: Decimal,
    reference: Decimal,
    cfg: DataConfig,
) -> bool:
    """DAT-13 confirming snapshot for exits: a transition or withdrawal sell may be sent
    at the 13:00 limit (SNAPSHOT_GAP_CONFIRMED). A buy never uses this path."""
    if side != "SELL" or kind not in ("transition", "withdrawal"):
        return False
    if bid_1130 is None or bid_1300 is None or not quote_1300_valid or halted is not False:
        return False
    if abs(bid_1300 - bid_1130) > cfg.snapshot_confirm_tolerance * bid_1130:
        return False
    return limit >= reference * (1 - cfg.snapshot_gap_sell_max)


# ---------------------------------------------------------------------------
# DAT-19 mark-price trial (pure)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarkTrial:
    days: int
    max_abs_rel: Decimal
    mean_abs_rel: Decimal
    days_equal: int
    complete: bool


def dat19_trial(
    pairs: Sequence[tuple[date, Decimal, Decimal]], required_days: int = 20
) -> MarkTrial:
    """Flex Mark Price vs EODHD close over the canary units (DAT-19).

    ``pairs`` = (trading day, EODHD close, Flex mark). The trial is complete after
    ``required_days`` trading days; its result is a "Before G4" record (OPS-06)
    and sets the DAT-02 tolerances by change control.
    """
    rels = [abs(e - m) / m for _, e, m in pairs]
    if not rels:
        return MarkTrial(0, Decimal(0), Decimal(0), 0, False)
    return MarkTrial(
        days=len(pairs),
        max_abs_rel=max(rels),
        mean_abs_rel=sum(rels, Decimal(0)) / len(rels),
        days_equal=sum(1 for _, e, m in pairs if e == m),
        complete=len({d for d, _, _ in pairs}) >= required_days,
    )


# ---------------------------------------------------------------------------
# DAT-09 run integrity
# ---------------------------------------------------------------------------


def dat09_integrity(store: RawStore) -> list[str]:
    """Every raw file is in the sha256 manifest with an unchanged hash. Any problem is a
    whole-run BLOCK."""
    return store.verify()


# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------


def _record(
    session: Session, now: datetime, inst_id: int | None, day: date | None, check: str, level: str,
    detail: Mapping[str, Any],
) -> QcEvent:  # fmt: skip
    ev = QcEvent(
        ts=ensure_utc(now), instrument_id=inst_id, trade_date=day, check_id=check, level=level,
        detail=dict(detail),
    )  # fmt: skip
    session.add(ev)
    session.flush()
    return ev


def _unresolved_restatement(session: Session, inst_id: int, now: datetime) -> QcEvent | None:
    """The latest DAT-10 event for the symbol, if no override came after it."""
    ev = session.execute(
        select(QcEvent)
        .where(QcEvent.instrument_id == inst_id, QcEvent.check_id == "DAT-10",
               QcEvent.ts <= ensure_utc(now))
        .order_by(QcEvent.ts.desc(), QcEvent.id.desc())
        .limit(1)
    ).scalar_one_or_none()  # fmt: skip
    if ev is None:
        return None
    override = session.execute(
        select(QcEvent.id)
        .where(QcEvent.instrument_id == inst_id, QcEvent.check_id == "DAT-17",
               QcEvent.ts >= ev.ts)
        .limit(1)
    ).scalar_one_or_none()  # fmt: skip
    return None if override is not None else ev


@dataclass(frozen=True)
class SymbolContext:
    role: str  # 'sleeve', 'benchmark' or 'paper'
    held: bool = False
    history: bool = False  # bar of the one-off history download (DAT-02 last paragraph)


def validate_symbol_day(  # noqa: PLR0912, PLR0915 - the DAT rules in order
    session: Session,
    symbol: str,
    day: date,
    now: datetime,
    cal: AsxCalendar,
    cfg: DataConfig,
    sched: Schedule,
    ctx: SymbolContext,
) -> SymbolVerdict:
    """Issue the verdict for ``symbol``'s close on trading day ``day``.

    Applies DAT-01 to DAT-06, DAT-10 and DAT-22 in order (DAT-11 runs on the built
    series, ``dat11_checks``).
    """
    # DAT-08 (whole run). History-download bars are checked on DAT-03, DAT-04, DAT-10
    # and DAT-11 alone (DAT-02, last paragraph), so they may predate the calendar table.
    if not ctx.history and not cal.is_trading_day(day):
        raise NotATradingDayError(f"DAT-08: {day} is not a trading day in the calendar table")
    inst = require_instrument(session, symbol)
    v = SymbolVerdict(symbol, day, Verdict.OK)
    bar = latest_bar(session, inst.id, day, "eodhd", as_of=now)
    two_source = ctx.role == "sleeve" and not ctx.history
    mark: Mark | None = mark_for_day(session, inst.id, day, cal, as_of=now) if two_source else None
    if two_source and mark is None:
        lm = latest_mark(session, inst.id, day, as_of=now)
        if lm is not None:  # R37: the latest available mark, tagged with its date
            v.detail["latest_flex_mark"] = {"date": lm.statement_date.isoformat(),
                                            "price": str(lm.price)}  # fmt: skip

    # --- DAT-01 / DAT-02 case (c): no EODHD bar --------------------------------
    if bar is None:
        if two_source and ctx.held and mark is not None:
            v.level = Verdict.SINGLE_SOURCE
            v.close, v.close_source = mark.price, "flex"
            v.reasons.append("DAT-02(c)")
            v.sell_ok = True  # a transition or withdrawal sell on a valid quote (DAT-13)
            v.detail["case"] = "c"
            return _finish(session, inst.id, v, now, signals_ok=False)
        level = dat01_missing_level(now, day, cal, sched)
        v.level = Verdict.BLOCK if level == "BLOCK" else Verdict.WARN
        v.reasons.append(f"DAT-01 {ReasonCode.DATA_STALE.value} ({level})")
        v.detail["missing"] = level
        if level == "INFO":
            return v  # before 21:30 a missing bar is still pending: no verdict yet
        _record(session, now, inst.id, day, "DAT-01", level, {"reason": "bar missing"})
        _record(session, now, inst.id, day, "VERDICT", v.level.value, _verdict_detail(v))
        return v

    v.close, v.close_source = bar.close, "eodhd"
    v.backfill = ctx.history

    # --- DAT-03 sanity -----------------------------------------------------------
    problems = dat03_sanity(bar)
    if problems:
        v.raise_to(Verdict.BLOCK, "DAT-03")
        v.quarantined = True
        _record(session, now, inst.id, day, "DAT-03", "BLOCK", {"problems": problems})
        return _finish(session, inst.id, v, now)

    # --- DAT-04 spike ------------------------------------------------------------
    prior = validated_closes(session, inst.id, end=day - timedelta(days=1), as_of=now)
    tick = tick_size(inst, bar.close)
    if prior:
        hist = [r.close for _, r in sorted(prior.items())][-61:]
        last_close = hist[-1]
        has_ca = session.execute(
            select(CorpAction.id).where(CorpAction.instrument_id == inst.id,
                                        CorpAction.ex_date == day)
        ).first() is not None  # fmt: skip
        spike, ret = dat04_is_spike(bar.close, last_close, hist, cfg)
        if spike and not has_ca:
            confirmed = (
                mark is not None
                and within_ok(bar.close, mark.price, cfg.cross_source.ok, tick)
                and ret <= cfg.spike.abs_return
            )
            if confirmed:
                v.raise_to(Verdict.WARN, f"DAT-04 {ReasonCode.DATA_SPIKE.value}")
                _record(session, now, inst.id, day, "DAT-04", "WARN", {"return": str(ret)})
            else:
                v.raise_to(Verdict.BLOCK, f"DAT-04 {ReasonCode.DATA_SPIKE.value}")
                v.quarantined = True
                _record(session, now, inst.id, day, "DAT-04", "BLOCK",
                        {"return": str(ret), "quarantined": True})  # fmt: skip
                return _finish(session, inst.id, v, now)

    # --- DAT-02 cross-source -------------------------------------------------------
    if ctx.history:
        v.buy_ok = v.sell_ok = v.evaluate_ok = True
    elif not two_source:
        # Benchmark-only symbols and the paper universe: single source by design, no WARN.
        v.raise_to(Verdict.SINGLE_SOURCE, "DAT-02 single source by design")
        v.evaluate_ok = True
    elif mark is not None:
        lvl = dat02_level(bar.close, mark.price, cfg, tick)
        v.detail["flex_mark"] = {"date": mark.statement_date.isoformat(), "price": str(mark.price)}
        if lvl is not Verdict.OK:
            v.raise_to(lvl, f"DAT-02 {ReasonCode.DATA_MISMATCH.value}")
            _record(session, now, inst.id, day, "DAT-02", lvl.value,
                    {"close": str(bar.close), "mark": str(mark.price)})  # fmt: skip
        v.buy_ok = v.sell_ok = v.evaluate_ok = lvl is not Verdict.BLOCK
    else:
        v.raise_to(Verdict.SINGLE_SOURCE, f"DAT-02 {ReasonCode.SINGLE_SOURCE.value}")
        v.evaluate_ok = True
        v.sell_ok = True  # on a valid quote that passes DAT-13
        v.buy_ok = not ctx.held  # case (a) yes; case (b): a buy waits for two sources
        v.detail["case"] = "b" if ctx.held else "a"
        if not ctx.history and is_late(bar, day, cal, sched):
            v.backfill = True  # a late bar with no stored mark (DAT-01)

    # --- DAT-06 stale --------------------------------------------------------------
    recent = latest_bars(session, inst.id, "eodhd", end=day, as_of=now)
    tail = [recent[d] for d in sorted(recent)][-cfg.stale_sessions :]
    if dat06_stale(tail, cfg.stale_sessions):
        v.raise_to(Verdict.WARN, "DAT-06 stale")
        _record(session, now, inst.id, day, "DAT-06", "WARN", {"sessions": cfg.stale_sessions})

    # --- DAT-10 restatement ----------------------------------------------------------
    ev = _unresolved_restatement(session, inst.id, now)
    if ev is not None:
        lvl = Verdict.BLOCK if ev.level == "BLOCK" else Verdict.WARN
        v.raise_to(lvl, f"DAT-10 {ReasonCode.DATA_RESTATED.value}")

    # --- DAT-22 missing distribution ---------------------------------------------------
    blocks: list[DistBlock] = missing_distributions(session, inst.id, day, as_of=now)
    if blocks:
        v.evaluate_ok = False
        v.buy_ok = False
        v.reasons.append(ReasonCode.DIST_MISSING.value)
        v.detail["dist_missing"] = [b.ex_date.isoformat() for b in blocks]
        detail = {"ex_dates": v.detail["dist_missing"], "causes": [b.cause for b in blocks]}
        _record(session, now, inst.id, day, "DAT-22", "BLOCK", detail)

    if v.level is Verdict.BLOCK:
        v.buy_ok = v.sell_ok = v.evaluate_ok = False
    return _finish(session, inst.id, v, now)


def _verdict_detail(v: SymbolVerdict) -> dict[str, Any]:
    return {
        "close": None if v.close is None else str(v.close),
        "close_source": v.close_source,
        "reasons": v.reasons,
        "buy_ok": v.buy_ok,
        "sell_ok": v.sell_ok,
        "evaluate_ok": v.evaluate_ok,
        "backfill": v.backfill,
        "quarantined": v.quarantined,
        **v.detail,
    }


def _finish(
    session: Session, inst_id: int, v: SymbolVerdict, now: datetime, *, signals_ok: bool = True
) -> SymbolVerdict:
    ev = _record(session, now, inst_id, v.trade_date, "VERDICT", v.level.value, _verdict_detail(v))
    if v.level is not Verdict.BLOCK and v.close is not None and not v.quarantined:
        session.add(
            ValidatedClose(
                instrument_id=inst_id,
                trade_date=v.trade_date,
                validated_at=ensure_utc(now),
                close=v.close,
                source=v.close_source or "eodhd",
                verdict=v.level.value,
                backfill=v.backfill,
                signals_ok=signals_ok and v.evaluate_ok,
                override_id=None,
                detail={"verdict_event": ev.id},
            )
        )
        session.flush()
    return v


def latest_verdict(
    session: Session, inst_id: int, day: date, as_of: datetime | None = None
) -> QcEvent | None:
    q = select(QcEvent).where(
        QcEvent.instrument_id == inst_id,
        QcEvent.trade_date == day,
        QcEvent.check_id.in_(("VERDICT", "DAT-17")),
    )
    if as_of is not None:
        q = q.where(QcEvent.ts <= ensure_utc(as_of))
    return session.execute(q.order_by(QcEvent.ts.desc(), QcEvent.id.desc()).limit(1)).scalar()


# ---------------------------------------------------------------------------
# DAT-17 override
# ---------------------------------------------------------------------------


class OverrideError(ValueError):
    pass


def qc_override(
    session: Session,
    symbol: str,
    day: date,
    now: datetime,
    *,
    reason: str,
    actor: str,
    use: str | None = None,
    price: Decimal | None = None,
    cal: AsxCalendar | None = None,
) -> ValidatedClose:
    """``trader qc override --symbol S --date D --use eodhd|flex`` or ``--price P``.

    Clears a BLOCK (and a DAT-10 restatement block) with a typed reason recorded as a
    ``qc_event``; the named close is written to the validated set with the override id.
    """
    if not reason.strip():
        raise OverrideError("a typed reason is required (DAT-17)")
    if (use is None) == (price is None):
        raise OverrideError("name exactly one close: --use eodhd|flex or --price P")
    inst = require_instrument(session, symbol)
    if use == "eodhd":
        bar = latest_bar(session, inst.id, day, "eodhd", as_of=now)
        if bar is None:
            raise OverrideError(f"no EODHD bar stored for {symbol} on {day}")
        close, source = bar.close, "eodhd"
    elif use == "flex":
        if cal is None:
            raise OverrideError("the calendar is needed to find the Flex mark")
        mark = mark_for_day(session, inst.id, day, cal, as_of=now)
        if mark is None:
            raise OverrideError(f"no Flex mark stored for {symbol} on {day}")
        close, source = mark.price, "flex"
    else:
        assert price is not None
        if price <= 0:
            raise OverrideError("price must be positive")
        close, source = price, "override"
    ev = QcEvent(
        ts=ensure_utc(now), instrument_id=inst.id, trade_date=day, check_id="DAT-17",
        level="WARN", detail={"use": use, "price": None if price is None else str(price),
                              "close": str(close)},
        override_by=actor, override_reason=reason,
    )  # fmt: skip
    session.add(ev)
    session.flush()
    row = ValidatedClose(
        instrument_id=inst.id,
        trade_date=day,
        validated_at=ensure_utc(now),
        close=close,
        source=source,
        verdict=Verdict.WARN.value,
        backfill=False,
        signals_ok=True,
        override_id=ev.id,
        detail={"override_reason": reason},
    )
    session.add(row)
    session.flush()
    return row


# ---------------------------------------------------------------------------
# Helpers for reporting
# ---------------------------------------------------------------------------


def issuer_amounts(session: Session, inst_id: int) -> dict[date, Decimal]:
    return {
        ex: r.cash_amount
        for ex, r in effective_distributions(session, inst_id).items()
        if r.cash_amount is not None
    }


def distribution_amounts(session: Session, inst_id: int) -> dict[date, Decimal | None]:
    rows: dict[date, Distribution] = effective_distributions(session, inst_id)
    return {ex: r.cash_amount for ex, r in rows.items()}
