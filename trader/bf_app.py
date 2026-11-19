"""B-fast application: the daily jobs, the simulated twin, the canary flow and the
dry-run harness (FD v3.0 §4, §7.9 L6-L8, L13-L14, §21.1 BF3-BF4). PAPER ONLY.

One ``BfApp`` runs two books through the same code:

* the **broker book** (``EMG2_18_PAPER``) on an IBKR paper gateway (or the mock
  gateway in a dry run), per-order approval by the owner (L8);
* the **simulated twin** (``EMG2_18_SIM``, L13) in ``SimBroker``, auto-approved,
  filled at the session's close with the L9 spread and IBKR commission.

Jobs (Australia/Sydney, ASX sessions; ``trader.scheduler`` runs them):

====== ============ =========================================================
time   job          what
====== ============ =========================================================
10:30  ``tick``     Telegram commands (/ok, /veto, /pause, /kill, /resume...)
12:30  ``tick``
14:30  ``tick``
15:20  ``tick``     the approval deadline passes (L8)
15:45  ``submit``   send approved orders of active batches; unapproved ones lapse;
                    held buys retried up to ``buy_funds_wait_sessions`` (L7)
16:20  ``collect``  broker executions -> journal (once each); statuses
16:30  ``reconcile`` ledger vs broker to the unit and the cent; a break latches
                    HALTED_INTEGRITY and pages; after a reconciled canary the
                    remaining start buys are planned for the next session (L6)
22:15  ``sim``      the twin's auction at the day's closes; L13 comparison
22:20  ``decide``   month-end (or the start decision): EMG2-18 decision for both
                    books, orders, plan-time breaker, approval request
22:45  ``report``   daily report (L14 banners) to Telegram
====== ============ =========================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Protocol

from trader.approval import (
    ApprovalBot,
    ChatTransport,
    Incoming,
    TotpVerifier,
    broadcast,
    render_batch,
    totp,
)
from trader.broker.base import Broker
from trader.broker.paper_sim import SimBroker
from trader.constants import ASX_TZ
from trader.execution import Executor
from trader.journal import Journal, Status
from trader.lines.emg2 import BookState, Emg2_20Decision, Emg2_20Params, decide_emg2_20
from trader.orders import OrderParams, build_orders
from trader.panel import PricePanel
from trader.reconcile import compare_books
from trader.report import DailyInputs, daily_report
from trader.risk import RiskContext, RiskLimits, SafetyLevel, evaluate_book, worst
from trader.runner import reconcile_and_page
from trader.universe import liquidity_table

PanelProvider = Callable[[date], PricePanel]
CloseProvider = Callable[[date], Mapping[str, Decimal]]

DAY_JOBS: tuple[tuple[str, str], ...] = (
    ("10:30", "tick"),
    ("12:30", "tick"),
    ("14:30", "tick"),
    ("15:20", "tick"),
    ("15:45", "submit"),
    ("16:20", "collect"),
    ("16:30", "reconcile"),
    ("22:15", "sim"),
    ("22:20", "decide"),
    ("22:45", "report"),
)


def at(day: date, hhmm: str) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(day, time(h, m), ASX_TZ)


@dataclass(frozen=True)
class AppSettings:
    book: str = "EMG2_18_PAPER"
    sim_book: str = "EMG2_18_SIM"
    line: str = "EMG2_18"
    capital_aud: Decimal = Decimal(10000)
    params: Emg2_20Params = field(default_factory=Emg2_20Params)
    order_params: OrderParams = field(default_factory=OrderParams)
    limits: RiskLimits = field(default_factory=RiskLimits)
    approval_mode: str = "per_order"
    approval_deadline: str = "15:20"
    buy_funds_wait_sessions: int = 4
    sim_half_spread: Decimal = Decimal("0.005")
    chats: frozenset[int] = frozenset()
    start_date: date | None = None  # L6 start decision (canary); None = month-ends only


@dataclass
class StartState:
    decision: Emg2_20Decision
    tv20: dict[str, Decimal]
    canary_batch: str


class BfApp:
    def __init__(
        self,
        s: AppSettings,
        journal: Journal,
        broker: Broker,
        sim: SimBroker,
        transport: ChatTransport,
        verifier: TotpVerifier,
        sessions: Sequence[date],
        panels: PanelProvider,
        closes: CloseProvider,
    ) -> None:
        self.s = s
        self.j = journal
        self.broker = broker
        self.sim = sim
        self.transport = transport
        self.sessions = sorted(sessions)
        self.panels = panels
        self.closes = closes
        self.now = datetime.now(UTC)
        self.ex = Executor(
            journal, broker, s.book, limits=s.limits, approval_deadline=s.approval_deadline
        )
        self.ex_sim = Executor(journal, sim, s.sim_book, limits=s.limits, approval_deadline="23:59")
        self.bot = ApprovalBot(journal, transport, verifier, s.chats, on_kill=self._kill)
        self.start: StartState | None = None
        self.log: list[str] = []
        self.last_px: dict[str, Decimal] = {}
        self.peak = s.capital_aud
        self.prev_value: Decimal | None = None

    # ------------------------------------------------------------ calendar helpers
    def is_session(self, d: date) -> bool:
        return d in self.sessions

    def next_session(self, d: date) -> date:
        later = [x for x in self.sessions if x > d]
        if not later:
            raise ValueError(f"no session after {d} in the calendar")
        return later[0]

    def sessions_between(self, a: date, b: date) -> int:
        return sum(1 for x in self.sessions if a < x <= b)

    def is_month_end(self, d: date) -> bool:
        later = [x for x in self.sessions if x > d]
        return bool(later) and later[0].month != d.month

    def decision_kind(self, d: date) -> str | None:
        if self.s.start_date is not None and d == self.s.start_date:
            return "S"
        return "R" if self.is_month_end(d) else None

    # ------------------------------------------------------------ plumbing
    def _say(self, text: str) -> None:
        broadcast(self.transport, self.s.chats, text)
        self.log.append(text.splitlines()[0] if text else "")

    def _kill(self) -> int:
        return self.ex.kill(self.now)

    def _ctx(
        self,
        book: str,
        broker: Broker,
        day: date,
        decision_date: date,
        now: datetime,
        start_day: bool,
    ) -> RiskContext:
        d0 = at(day, "00:00").astimezone(UTC)
        n, buys = self.j.sent_between(book, d0, d0 + timedelta(days=1))
        return RiskContext(
            now=now.astimezone(UTC),
            session=day,
            expected_data_date=decision_date,
            data_as_of=decision_date,
            safety=SafetyLevel.NORMAL,
            start_day=start_day,
            positions=broker.positions(),
            settled_cash=broker.account().settled_cash,
            holdings_cost=self.j.holdings_cost(book),
            orders_sent_today=n,
            buys_sent_today_aud=buys,
        )

    def _books(self) -> tuple[tuple[str, Executor, Broker, str], ...]:
        return (
            (self.s.book, self.ex, self.broker, self.s.approval_mode),
            (self.s.sim_book, self.ex_sim, self.sim, "auto"),
        )

    # ------------------------------------------------------------ jobs
    def run_job(self, name: str, day: date, now: datetime) -> None:
        self.now = now
        getattr(self, f"job_{name}")(day, now)

    def job_tick(self, day: date, now: datetime) -> None:
        self.bot.handle_all()

    def job_decide(self, day: date, now: datetime, kind: str | None = None) -> None:
        kind = kind or self.decision_kind(day)
        if kind is None:
            return
        panel = self.panels(day)
        liq = liquidity_table(panel)
        tv20 = {
            e: Decimal(repr(float(liq.tv_med20[j]))).quantize(Decimal(1))
            for j, e in enumerate(panel.entities)
            if liq.tv_med20[j] == liq.tv_med20[j]
        }
        x = self.next_session(day)
        for book, ex, broker, mode in self._books():
            state = BookState(book, self.j.cash(book), self.j.positions(book))
            dec = decide_emg2_20(panel, state, self.s.params)
            canary = kind == "S" and book == self.s.book
            batch = build_orders(
                dec,
                line=self.s.line,
                params=self.s.order_params,
                kind=kind,
                canary=canary,
                tv_med20=tv20,
            )
            ex.plan(batch, mode, x, self._ctx(book, broker, x, day, now, kind == "S"))
            if canary:
                self.start = StartState(dec, tv20, batch.batch_id)
            if book == self.s.book:
                head = f"Decision {day} ({'start, canary first' if canary else 'regular'}); "
                head += f"list {dec.list_digest[:12]}; {len(batch.intents)} order(s)"
                self._say(head + "\n" + render_batch(self.j, batch.batch_id, "PAPER"))

    def _active(self, book: str, day: date) -> list[tuple[str, bool]]:
        out = []
        for bid, xd in self.j.batches_of(book):
            if xd is None or xd > day:
                continue
            waited = self.sessions_between(xd, day)
            if waited > self.s.buy_funds_wait_sessions:
                continue
            open_ = [
                st
                for _, st in self.j.intents_of(bid)
                if st in (Status.RISK_OK, Status.APPROVED, Status.HELD)
            ]
            if open_:
                out.append((bid, waited >= self.s.buy_funds_wait_sessions))
        return out

    def job_submit(self, day: date, now: datetime) -> None:
        for book, ex, broker, _ in self._books():
            for bid, final in self._active(book, day):
                b = self.j.batch(bid)
                assert b is not None
                start_day = bid.endswith(("-S", "-C"))
                rep = ex.submit(
                    bid,
                    self._ctx(book, broker, day, b["decision_date"], now, start_day),
                    now,
                    final_day=final,
                )
                if book == self.s.book:
                    if rep.sent or rep.not_approved or rep.rejected:
                        self._say(
                            f"{bid}: sent {len(rep.sent)}, not approved {len(rep.not_approved)}, "
                            f"held/rejected {len(rep.rejected)}"
                        )
                    for p in rep.pages:
                        self._say("PAGE " + p)

    def job_collect(self, day: date, now: datetime) -> None:
        self.ex.collect_fills(now, session_closed=True)

    def job_reconcile(self, day: date, now: datetime) -> None:
        r = reconcile_and_page(self.j, self.broker, self.s.book, self.transport, self.s.chats, now)
        if not r.ok:
            self.log.append("RECON BREAK " + "; ".join(r.breaks))
        st = self.start
        if st is None or not r.ok:
            return
        canary = self.j.intents_of(st.canary_batch)
        if canary and all(s == Status.FILLED for _, s in canary):
            rest = replace(st.decision, buys=st.decision.buys[1:], sells=())
            batch = build_orders(
                rest, line=self.s.line, params=self.s.order_params, kind="S", tv_med20=st.tv20
            )
            x = self.next_session(day)
            d = date.fromisoformat(st.decision.as_of)
            self.ex.plan(
                batch, self.s.approval_mode, x, self._ctx(self.s.book, self.broker, x, d, now, True)
            )
            self._say(
                f"Canary filled and reconciled to the cent. Remaining {len(batch.intents)} start "
                f"buys for {x}:\n" + render_batch(self.j, batch.batch_id, "PAPER")
            )
            self.start = None
        elif canary and any(
            s
            in (
                Status.EXPIRED,
                Status.REJECTED,
                Status.RISK_REJECTED,
                Status.LAPSED,
                Status.NEEDS_REVIEW,
            )
            for _, s in canary
        ):
            self._say(
                "PAGE canary did not fill; the start stops here (L6). Review before a new start."
            )
            self.start = None

    def job_sim(self, day: date, now: datetime) -> None:
        closes = dict(self.closes(day))
        self.sim.advance(day, closes)
        self.ex_sim.collect_fills(now, session_closed=True)
        r = compare_books(
            self.j.positions(self.s.sim_book), self.j.positions(self.s.book), self._explained()
        )
        if not r.ok:
            lvl = worst(self.j.safety_level(), SafetyLevel.HALTED_INTEGRITY)
            self.j.set_safety(lvl, "L13: " + "; ".join(r.breaks)[:180], "l13", now)
            self._say(
                "PAGE L13 sim/broker holdings differ without an explanation:\n"
                + "\n".join(r.breaks)
            )

    def _explained(self) -> set[str]:
        """L13: names whose difference between the books an order explains: an order of
        either book that did not fill (unapproved, vetoed, held, expired, rejected), or a
        fill one book has and the other book's decision of the same day did not make
        (the books' states had already diverged for an explained reason)."""
        filled: dict[str, set[tuple[str, str, str]]] = {}
        out: set[str] = set()
        for book in (self.s.book, self.s.sim_book):
            filled[book] = set()
            for bid, _ in self.j.batches_of(book):
                for it, st in self.j.intents_of(bid):
                    if st == Status.FILLED:
                        filled[book].add((str(it.decision_date), it.entity, it.side.value))
                    else:
                        out.add(it.entity)
        out |= {e for _, e, _ in filled[self.s.book] ^ filled[self.s.sim_book]}
        return out

    def job_report(self, day: date, now: datetime) -> None:
        self.last_px.update(self.closes(day))  # a holding with no trade today keeps its last close
        px = dict(self.last_px)
        pos = self.j.positions(self.s.book)
        cash = self.j.cash(self.s.book)
        value = cash + sum((px.get(e, Decimal(0)) * q for e, q in pos.items()), Decimal(0))
        reading = evaluate_book(
            value, self.peak, self.prev_value, self.s.capital_aud, self.s.limits
        )
        if reading.level is not SafetyLevel.NORMAL:
            self.j.set_safety(
                worst(self.j.safety_level(), reading.level), "book monitor", "risk", now
            )
        self.peak = max(self.peak, value)
        self.prev_value = value
        d0 = at(day, "00:00").astimezone(UTC)
        fills = [
            f
            for f in self.j.fills(self.s.book)
            if d0
            <= (f.executed_at if f.executed_at.tzinfo else f.executed_at.replace(tzinfo=UTC))
            < d0 + timedelta(days=1)
        ]
        orders = [
            (it.client_order_id, st)
            for bid, _ in self.j.batches_of(self.s.book)
            for it, st in self.j.intents_of(bid)
            if st not in (Status.FILLED,)
        ]
        sim_pos = self.j.positions(self.s.sim_book)
        sim_value = self.j.cash(self.s.sim_book) + sum(
            (px.get(e, Decimal(0)) * q for e, q in sim_pos.items()), Decimal(0)
        )
        x = DailyInputs(
            book=self.s.book,
            session=day,
            real_money=False,
            cash=cash,
            positions=pos,
            prices=px,
            capital_in=self.s.capital_aud,
            fills_today=fills,
            commission_to_date=sum((f.commission for f in self.j.fills(self.s.book)), Decimal(0)),
            orders_today=orders[-30:],
            safety=self.j.safety_level().value,
            flags=list(reading.alerts),
            sim_value=sim_value,
        )
        self._say(daily_report(x))

    # ------------------------------------------------------------ one session
    def run_day(
        self,
        day: date,
        *,
        decision: str | None = None,
        owner: Callable[[date, str], Sequence[str]] | None = None,
        auction: Callable[[date], None] | None = None,
    ) -> None:
        """Every job of a session in time order (the dry-run harness and tests).
        ``owner(day, hhmm)`` returns the owner's messages for that tick; ``auction(day)``
        stands in for the exchange's closing auction at 16:10."""
        for hhmm, name in DAY_JOBS:
            now = at(day, hhmm)
            if name == "tick" and owner is not None:
                for k, text in enumerate(owner(day, hhmm)):
                    t = now + timedelta(seconds=31 * k)
                    self.transport_inject(Incoming(next(iter(self.s.chats)), text, t))
            if name == "collect" and auction is not None:
                auction(day)
            if name == "decide":
                self.now = now
                if decision is not None or self.decision_kind(day):
                    self.job_decide(day, now, decision)
                continue
            self.run_job(name, day, now)

    def transport_inject(self, m: Incoming) -> None:
        inbox = getattr(self.transport, "inbox", None)
        if inbox is None:
            raise RuntimeError("owner messages can be injected only into an in-memory transport")
        inbox.append(m)


# ---------------------------------------------------------------- dry-run harness


def owner_approves_all(app: BfApp, seed: str) -> Callable[[date, str], Sequence[str]]:
    """The simulated owner: at 10:30 approves every order of each batch executing today,
    typing a fresh code from the authenticator (``seed``)."""

    def owner(day: date, hhmm: str) -> list[str]:
        if hhmm != "10:30":
            return []
        out: list[str] = []
        for bid, xd in app.j.batches_of(app.s.book):
            if xd == day:
                t = at(day, hhmm) + timedelta(seconds=31 * len(out))
                out.append(f"/ok {bid} all {totp(seed, t)}")
        return out

    return owner


class _Auctioneer(Protocol):
    def auction(self, closes: dict[str, float]) -> int: ...


def mock_auction(gateway: _Auctioneer, closes: CloseProvider) -> Callable[[date], None]:
    """The exchange's closing auction, played by the mock gateway at the day's closes."""

    def run(day: date) -> None:
        gateway.auction({e: float(c) for e, c in closes(day).items()})

    return run


@dataclass(frozen=True)
class DryRunSummary:
    days: int
    batches: dict[str, dict[str, int]]
    positions: dict[str, int]
    sim_positions: dict[str, int]
    cash: Decimal
    broker_cash: Decimal
    safety: str
    messages: int
    pages: list[str]


def dry_run(
    app: BfApp,
    days: Sequence[date],
    decisions: Mapping[date, str],
    owner: Callable[[date, str], Sequence[str]],
    auction: Callable[[date], None],
) -> DryRunSummary:
    for d in days:
        app.run_day(d, decision=decisions.get(d), owner=owner, auction=auction)
    batches: dict[str, dict[str, int]] = {}
    for bid, _ in app.j.batches_of(app.s.book):
        counts: dict[str, int] = {}
        for _, st in app.j.intents_of(bid):
            counts[st] = counts.get(st, 0) + 1
        batches[bid] = counts
    return DryRunSummary(
        days=len(days),
        batches=batches,
        positions=app.j.positions(app.s.book),
        sim_positions=app.j.positions(app.s.sim_book),
        cash=app.j.cash(app.s.book),
        broker_cash=app.broker.account().ledger_cash,
        safety=app.j.safety_level().value,
        messages=len(getattr(app.transport, "outbox", [])),
        pages=[x for x in app.log if x.startswith(("PAGE", "RECON"))],
    )
