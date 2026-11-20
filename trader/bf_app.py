"""B-fast application: the daily jobs, the simulated twin, the canary flow and the
dry-run harness (FD v3.0 §4, §7.9 L6-L8, L13-L14, §21.1 BF3-BF4). PAPER ONLY.

One ``BfApp`` runs two books through the same code:

* the **broker book** (``EMG2_18_PAPER``) on an IBKR paper gateway (or the mock
  gateway in a dry run), per-order approval by the owner (L8);
* the **simulated twin** (``EMG2_18_SIM``, L13) in ``SimBroker``, auto-approved,
  filled at the session's close with the L9 spread and IBKR commission.

Jobs (Australia/Sydney, ASX sessions; ``trader.scheduler`` runs each once a session):

====== ============ =========================================================
time   job          what
====== ============ =========================================================
10:30  ``tick``     Telegram commands (/ok, /veto, /pause, /kill, /resume...)
12:30  ``tick``
14:30  ``remind``   tick + a reminder for orders of today not yet approved (L8)
15:20  ``tick``     the approval deadline passes; later /ok is refused (L8)
15:45  ``submit``   send approved orders of active batches; unapproved ones lapse;
                    buys short of settled funds are held to D+4, then lapse (L7)
16:20  ``collect``  broker executions -> journal (once each); unfilled DAY orders
                    expire and are carried: buys one session, sells three (L7)
16:30  ``reconcile`` ledger vs broker to the unit and the cent; a break latches
                    HALTED_INTEGRITY and pages; after a reconciled canary fill the
                    remaining start buys are planned for the next session (L6)
22:15  ``sim``      the twin's auction at the day's closes; L13 comparison
22:20  ``decide``   month-end (or the start decision): EMG2-18 decision for both
                    books, orders, plan-time breaker, approval request
22:45  ``report``   daily report (L14 banners) to Telegram
====== ============ =========================================================

``sim`` and ``decide`` wait for the day's data: until 23:40 they report "not done" and
the scheduler retries them; after that a missing day is a rule-14 data block (paged;
no decision; holdings kept). Everything the app must remember across a restart (the
start decision, the book's peak value, the L13 notes, carried orders) is in the
journal, never only in memory.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_DOWN, Decimal
from itertools import pairwise
from typing import Any, Protocol

import numpy as np

from trader.approval import (
    ApprovalBot,
    ChatTransport,
    Incoming,
    TotpVerifier,
    approved_seqs,
    broadcast,
    render_batch,
    totp,
)
from trader.broker.base import Broker, LiveTradingRefusedError
from trader.broker.paper_sim import SimBroker
from trader.ca_book import (
    CaSource,
    book_calendar_day,
    describe,
    ingest_flex,
    pending_expectations,
)
from trader.canonical import sha256_json
from trader.constants import ASX_TZ
from trader.corporate_actions import CaCalendar, CaKind
from trader.data.flex import FlexError, FlexStatement
from trader.execution import Executor
from trader.flex_pull import FLEX_PAGE_SLOT, FLEX_PULL_SLOTS, FlexPuller
from trader.identity_change import code_changes
from trader.journal import TERMINAL, Journal, Status
from trader.lines.band_trend import BandTrend, BandTrendParams, band_trend
from trader.lines.emg2 import (
    BT_FUND_BUY,
    BT_FUND_SELL,
    BT_FUND_SWEEP,
    BT_LEFTOVER_SELL,
    BookState,
    BuyPlan,
    Emg2_20Decision,
    Emg2_20Params,
    Emg2List,
    TargetOrder,
    decide_emg2_18_bt,
    decide_emg2_20,
    emg2_list,
)
from trader.loss_rule import (
    ModelledFill,
    Outcome,
    StagedTest,
    at_decision,
    integrity_breaks,
    percentile_rank,
    wind_down_qty,
)
from trader.orders import (
    OrderBatch,
    OrderIntent,
    OrderParams,
    Side,
    batch_id_for,
    build_orders,
    client_order_id,
    round_to_step,
)
from trader.panel import PricePanel
from trader.random_twins import SEED_BASE, RandomOrder, month_index, twin_books
from trader.reconcile import Expected, compare_books
from trader.report import DailyInputs, daily_report
from trader.risk import (
    BLOCKS_ALL,
    BLOCKS_BUYS,
    BookReading,
    RiskContext,
    RiskLimits,
    SafetyLevel,
    evaluate_book,
    worst,
)
from trader.runner import reconcile_and_page
from trader.store_refresh import STORE_PAGE_SLOT, STORE_REFRESH_SLOTS, StoreRefresher
from trader.universe import liquidity_table

PanelProvider = Callable[[date], PricePanel]
CloseProvider = Callable[[date], Mapping[str, Decimal]]

DAY_JOBS: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            ("10:30", "tick"),
            ("12:30", "tick"),
            ("14:30", "remind"),
            ("15:20", "tick"),
            ("15:45", "submit"),
            ("16:20", "collect"),
            ("16:30", "reconcile"),
            ("22:15", "sim"),
            ("22:20", "decide"),
            ("22:25", "fund_sweep"),  # BF-D34: leftover shares out, their cash into the fund
            ("22:45", "report"),
            *((t, "flex_pull") for t in FLEX_PULL_SLOTS),  # BF-D27: before the 16:30 recon
            *((t, "store_refresh") for t in STORE_REFRESH_SLOTS),  # BF-D31: after the close
        ),
        key=lambda j: j[0],
    )
)
RETRY_UNTIL = "23:40"  # sim / decide wait for the day's closes until then (rule 14)
OWNER_TICKS = frozenset({"tick", "remind"})


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
    buy_funds_wait_sessions: int = 4  # L7: a buy waits for funds D+1..D+4
    buy_carry_sessions: int = 1  # L7: an unfilled buy is carried one session
    sell_carry_sessions: int = 3  # L7: an unfilled sell is carried up to 3 sessions
    sim_half_spread: Decimal = Decimal("0.005")
    chats: frozenset[int] = frozenset()
    start_date: date | None = None  # L6 start decision (canary); None = month-ends only
    lic_note: str = ""  # which LIC list the panel used (BF-D6), shown with each decision
    # L13 / L11 test (b): random twins of the simulated book (BF-D18); 0 = not running
    random_twins: int = 0
    random_prefix: str = "EMG2_18_RND"
    random_seed_base: int = SEED_BASE
    # L15 band-trend switch (AMENDMENT_live_EMG2_18_BT.md; BF-D28); disabled by default
    band_trend: BandTrendParams = field(default_factory=BandTrendParams)
    # BF-D32 paper dry run: extra decisions with the L15 state forced ("EMG2" / "FUND")
    # or left to the rule ("REAL"); paper broker only; ignored after ``dry_run_until``
    forced_states: tuple[tuple[date, str], ...] = ()
    dry_run_until: date | None = None

    def forced(self, d: date) -> str | None:
        """The paper dry run's state for a decision on ``d`` (None: no dry-run decision)."""
        if self.dry_run_until is not None and d > self.dry_run_until:
            return None
        return dict(self.forced_states).get(d)


def data_ready(panel: PricePanel, min_share: float = 0.5) -> bool:
    """The panel's last session (the decision day) has closes for at least ``min_share``
    of the names that traded the session before: the day's data is in. (Half, not
    nearly all: the record's store covers about 1,790 names a day from per-symbol files
    and about 1,400 from the bulk feed since 16 Nov 2026; a missing day has none.)"""
    if len(panel.dates) < 2:
        return False
    last = int(np.count_nonzero(~np.isnan(panel.close[-1])))
    prev = int(np.count_nonzero(~np.isnan(panel.close[-2])))
    return prev > 0 and last >= min_share * prev


def marks_from_panels(panels: PanelProvider) -> CloseProvider:
    """The last valid close of every name in the panel of day d (holdings that did not
    trade today keep their last close; a name never valued at zero by a gap)."""

    def marks(d: date) -> dict[str, Decimal]:
        p = panels(d)
        out: dict[str, Decimal] = {}
        for j, e in enumerate(p.entities):
            col = p.close[:, j]
            ok = np.flatnonzero(~np.isnan(col))
            if ok.size:
                out[e] = Decimal(repr(float(col[ok[-1]])))
        return out

    return marks


def _decision_record(dec: Emg2_20Decision, tv20: Mapping[str, Decimal]) -> dict[str, Any]:
    return {
        "as_of": dec.as_of,
        "list_digest": dec.list_digest,
        "account_value": str(dec.account_value),
        "slots": dec.slots,
        "parcel": str(dec.parcel),
        "buys": [
            [b.entity, b.t_rank, str(b.value_aud), str(b.ref_close), b.reason] for b in dec.buys
        ],
        "tv20": {b.entity: str(tv20[b.entity]) for b in dec.buys if b.entity in tv20},
    }


def _decision_from(book: str, r: Mapping[str, Any], skip_first: int) -> Emg2_20Decision:
    buys = tuple(
        BuyPlan(str(e), int(k), Decimal(v), Decimal(ref), str(why))
        for e, k, v, ref, why in r["buys"][skip_first:]
    )
    return Emg2_20Decision(
        book, str(r["as_of"]), str(r["list_digest"]), None, Decimal(r["account_value"]),
        int(r["slots"]), Decimal(r["parcel"]), (), buys, (), (),
    )  # fmt: skip


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
        marks: CloseProvider | None = None,
        twin_rank: Callable[[date], Decimal | None] | None = None,
        l12_stop: Callable[[date], str | None] | None = None,
        lic_guard: Callable[[], object] | None = None,
        ca_source: CaSource | None = None,
        flex: Callable[[date], Sequence[FlexStatement]] | None = None,
        flex_pull: FlexPuller | None = None,
        store_refresh: StoreRefresher | None = None,
    ) -> None:
        """``closes(d)``: the closes of session d (empty while the day's data is not in);
        ``marks(d)``: the last known close of every name at d (valuation; defaults to
        the panel's last valid close of each name). L11 staged test inputs:
        ``twin_rank(d)``: the twin's percentile among its 100 random twins since the
        start (None, the default, while the random twins are not running: the test
        then fails safe and buys stay paused); ``l12_stop(d)``: the L12 stop rule met
        at d, if any (default: none). ``lic_guard()``: BF-D21, re-reads and checks the
        frozen LIC list against its pin and raises when it is missing or changed; it runs
        before every decision and every send (``trader-bf run`` and the dry run pass
        ``lic_codes``; None, unit tests only, checks nothing). BF-D23 corporate actions:
        ``ca_source(codes, start, end)``: the calendar (vendor dividends + the record's
        CORPORATE_ACTIONS.csv) for those codes; ``flex(d)``: IBKR Activity Flex statements
        available on d (the broker book's dividends and corporate actions). BF-D27:
        ``flex_pull`` downloads the Flex statement into the inbox at ``FLEX_PULL_SLOTS``
        before the 16:30 reconciliation (None: the inbox is filled by hand). BF-D31:
        ``store_refresh`` appends the day's EODHD bulk files to the price store at
        ``STORE_REFRESH_SLOTS``; with it, no decision is made while the store's newest
        day is before the decision day (fail closed; None: the store is filled
        elsewhere and only rule 14's closes test applies)."""
        self.s = s
        self.lic_guard = lic_guard
        self.j = journal
        self.broker = broker
        self.sim = sim
        fund_hs: dict[str, Decimal] = {}
        if s.band_trend.enabled:  # BF-D28: the twins' fund spread (report 96's fund model)
            fund_hs[s.band_trend.fund] = Decimal(repr(s.band_trend.fund_half_spread))
            sim.half_spread_by.update(fund_hs)
        self.transport = transport
        self.sessions = sorted(sessions)
        self.panels = panels
        self.closes = closes
        self.marks = marks or marks_from_panels(panels)
        self.l12_stop = l12_stop or (lambda d: None)
        self.ca_source = ca_source
        self.flex = flex
        self.flex_pull = flex_pull
        self._forced_from: dict[date, str] = {}  # BF-D32: the rule's state of a forced day
        self.store_refresh = store_refresh
        self.now = datetime.now(UTC)
        self.ex = Executor(
            journal, broker, s.book, limits=s.limits, approval_deadline=s.approval_deadline
        )
        self.ex_sim = Executor(
            journal,
            sim,
            s.sim_book,
            limits=s.limits,
            approval_deadline="23:59",
            safety_scope=s.sim_book,  # BF-D16: the owner's halts of the paper book stay there
        )
        # BF-D18: the random twins of the simulated book, each a simulated book of its own
        # in the journal (own latch, auto-approved, the sim's costs and code path).
        self.rnd: list[tuple[str, int, Executor, SimBroker]] = []
        for name, seed in twin_books(s.random_prefix, s.random_twins, s.random_seed_base):
            if not journal.has_cash_moves(name):
                journal.add_cash(name, "DEPOSIT", s.capital_aud, "random twin (simulated)")
            rb = SimBroker.from_journal(
                journal, name, s.sim_half_spread, exec_prefix=f"RND{seed}", half_spread_by=fund_hs
            )
            ex = Executor(
                journal, rb, name, limits=s.limits, approval_deadline="23:59", safety_scope=name
            )
            self.rnd.append((name, seed, ex, rb))
        self._idmap_seen = journal.identity_ratios()  # BF-D19/D25: code changes applied so far
        if twin_rank is None and self.rnd:
            twin_rank = self.twin_percentile
        self.twin_rank = twin_rank or (lambda d: None)
        self.bot = ApprovalBot(
            journal, transport, verifier, s.chats, self._kill, s.approval_deadline
        )
        if s.forced_states and not getattr(broker, "is_paper", False):  # BF-D32
            raise LiveTradingRefusedError("the forced-state dry run is for a paper broker only")
        if s.approval_mode not in ("per_order", "batch"):  # L8: the broker book never
            raise ValueError(f"approval_mode {s.approval_mode!r}: owner approval required")
        self.log: list[str] = []
        self._month_ends: frozenset[date] | None = None  # BF-D35: cached calendar month-ends

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

    def decision_kind(self, d: date, book: str | None = None) -> str | None:
        """S = the L6 start decision, R = a regular month-end decision, None = no decision.
        After a start inside a month, that month's month-end is skipped for the broker
        book (L6: "the 31 Dec decision is skipped"; holdings two weeks old)."""
        st = self.s.start_date
        if st is not None and d == st:
            return "S"
        if self.s.forced(d) is not None:  # BF-D32: a paper dry-run decision, every book
            return "R"
        if not self.is_month_end(d):
            return None
        if (
            book in (None, self.s.book)
            and st is not None
            and st < d
            and (st.year, st.month) == (d.year, d.month)
        ):
            return None
        return "R"

    # ------------------------------------------------------------ plumbing
    def say(self, text: str) -> None:
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
        data_as_of: date | None = None,
    ) -> RiskContext:
        d0 = at(day, "00:00").astimezone(UTC)
        n, buys = self.j.sent_between(book, d0, d0 + timedelta(days=1))
        return RiskContext(
            now=now.astimezone(UTC),
            session=day,
            expected_data_date=decision_date,
            data_as_of=data_as_of or decision_date,
            safety=SafetyLevel.NORMAL,  # the Executor adds the journal's latched level
            start_day=start_day,
            positions=self.j.map_codes(broker.positions()),  # BF-D19: a code change
            settled_cash=broker.account().settled_cash,
            holdings_cost=self.j.holdings_cost(book),
            # BF-D34: a fund buy is capped on the fund's own cost; the shares still held
            # in FUND state are being sold and never block it
            fund_cost=(
                self.j.cost_book(book).cost.get(self.s.band_trend.fund, Decimal(0))
                if self.s.band_trend.enabled
                else None
            ),
            orders_sent_today=n,
            buys_sent_today_aud=buys,
        )

    def lic_list_refused(self, day: date, now: datetime, step: str) -> str | None:
        """BF-D21: None when the frozen LIC list is present and is the registered file.
        Otherwise the reason: the broker book is latched HALTED_INTEGRITY (no order of
        any kind until the owner re-arms) and the owner is paged once per day and step.
        There is no fallback list; the caller makes no decision and sends no order."""
        if self.lic_guard is None:
            return None
        try:
            self.lic_guard()
        except Exception as e:  # any failure to read or check the list fails closed
            why = f"{type(e).__name__}: {e}"[:240]
        else:
            return None
        key = f"bfd21:{day}:{step}"
        if not self.j.job_done(key):
            self.j.mark_job(key, {"why": why}, now)
            lvl = worst(self.j.safety_level(), SafetyLevel.HALTED_INTEGRITY)
            self.j.set_safety(lvl, f"BF-D21 LIC list refused: {why}"[:180], "bfd21", now)
            self.say(
                f"PAGE BF-D21 the frozen LIC list is refused ({step}, {day}): {why}. "
                "No decision is made and no order is sent (fail closed; there is no "
                "fallback list). Restore the registered LIC_list_frozen_v2.csv (SHA-256 "
                "pinned as data.lic_list_sha256), then re-arm."
            )
        return why

    def _decision_refused(
        self, day: date, now: datetime, kinds: Mapping[str, str | None]
    ) -> bool | None:
        """None to go on; else the job's result: True when no book has a decision due.
        BF-D21: when the frozen LIC list is refused, False (retried until
        ``RETRY_UNTIL``, the owner may restore the file), then True (no decision today,
        recorded for every book that had one due)."""
        if not any(kinds.values()):
            return True
        why = self.lic_list_refused(day, now, "decision")
        if why is None:
            return None
        if now < at(day, RETRY_UNTIL):
            return False
        for book, *_ in self._books():
            key = f"decide:{book}:{day}"
            if kinds[book] is not None and not self.j.job_done(key):
                self.j.mark_job(key, {"refused": "BF-D21 LIC list: " + why}, now)
        return True

    def _books(self) -> tuple[tuple[str, Executor, Broker, str], ...]:
        return (
            (self.s.book, self.ex, self.broker, self.s.approval_mode),
            (self.s.sim_book, self.ex_sim, self.sim, "auto"),
            *((name, ex, rb, "auto") for name, _, ex, rb in self.rnd),
        )

    def _all_intents(self, book: str) -> list[tuple[OrderIntent, str]]:
        return self.j.intents_of_book(book)

    # ------------------------------------------------------------ jobs
    def run_job(self, name: str, day: date, now: datetime) -> bool:
        """Run one job; False means "not done yet, run me again later" (data not in)."""
        self.now = now
        done: bool | None = getattr(self, f"job_{name}")(day, now)
        return done is not False

    def job_tick(self, day: date, now: datetime) -> None:
        self.bot.handle_all()

    def job_remind(self, day: date, now: datetime) -> None:
        """14:30: commands, then a reminder for today's orders still unapproved (L8)."""
        self.bot.handle_all()
        for bid, xd in self.j.batches_of(self.s.book):
            b = self.j.batch(bid)
            if xd != day or b is None or b["approval_mode"] == "auto":
                continue
            ok = approved_seqs(self.j, bid)
            waiting = [
                it.seq
                for it, st in self.j.intents_of(bid)
                if st in (Status.RISK_OK, Status.HELD) and it.seq not in ok
            ]
            if waiting:
                self.say(
                    f"Reminder: {len(waiting)} order(s) of {bid} are not approved "
                    f"({', '.join(map(str, waiting))}). Deadline {self.s.approval_deadline}; "
                    "an order not approved is not sent (L8)."
                )

    def job_decide(self, day: date, now: datetime, kind: str | None = None) -> bool:
        kinds = {book: kind or self.decision_kind(day, book) for book, *_ in self._books()}
        refused = self._decision_refused(day, now, kinds)  # BF-D21: before any panel
        if refused is not None:
            return refused
        stale = self._store_stale(day)  # BF-D31: never decide on a stale price store
        panel = self.panels(day)
        ready = stale is None and data_ready(panel)
        liq = liquidity_table(panel)
        tv20 = {
            e: Decimal(repr(float(liq.tv_med20[j]))).quantize(Decimal(1))
            for j, e in enumerate(panel.entities)
            if liq.tv_med20[j] == liq.tv_med20[j]
        }
        x = self.next_session(day)
        acted: dict[str, set[tuple[str, str]]] = {}
        lst = emg2_list(panel) if ready else None  # one list for every book
        trend = self._band_trend(panel, day, now, lst)  # L15: one state for every book
        seeds = {name: seed for name, seed, _, _ in self.rnd}
        for book, ex, broker, mode in self._books():
            k = kinds[book]
            key = f"decide:{book}:{day}"
            if k is None or self.j.job_done(key):
                continue
            dec = None
            block = stale or (None if ready else "the day's closes are missing")
            if block is None:
                state = BookState(book, self.j.cash(book), self._book_positions(book, day))
                order = self._random_order(seeds.get(book), day, now)
                ages = (
                    self.holding_ages(book, day, state.holdings)
                    if self.s.params.sell_rule == "C6"
                    else None
                )
                dec = self._decide_book(panel, state, lst, order, trend, ages)
                block = dec.data_block
            if block is not None or dec is None:
                if now < at(day, RETRY_UNTIL):
                    return False  # the day's data may still arrive: retried
                self._data_block(book, key, day, now, block or "no decision")
                continue
            if book == self.s.book:  # L11 staged test; a stage-3 wind-down replaces the decision
                wind = self._l11_decide(day, now, x, panel.as_of, tv20, key, dec.digest)
                if wind is not None:
                    acted[book] = wind
                    continue
            canary = k == "S" and book == self.s.book
            # BF-D28: a decision that switches the book into or out of the fund replaces
            # the whole book, like the start: batch kind "B", L10's start-day limits
            kind = "B" if k == "R" and self._switches(dec, state.holdings) else k
            batch = build_orders(
                dec,
                line=self.s.line,
                params=self.s.order_params,
                kind=kind,
                canary=canary,
                tv_med20=tv20,
            )
            ctx = self._ctx(book, broker, x, day, now, kind in ("S", "B"), data_as_of=panel.as_of)
            ex.plan(batch, mode, x, ctx)
            self.j.mark_job(key, {"digest": dec.digest, "batch": batch.batch_id}, now)
            if book in seeds:
                continue  # random twins: not part of the L13 comparison
            acted[book] = {(i.entity, i.side.value) for i in batch.intents}
            if canary:  # the other start buys follow the canary: count the whole list
                acted[book] |= {(b.entity, Side.BUY.value) for b in dec.buys}
                self.j.mark_job(f"start:{book}:{day}", _decision_record(dec, tv20), now)
            if book == self.s.book:
                self._announce(
                    day, canary, dec.list_digest, batch.batch_id, ex.plan_pages,
                    None if trend is None else self._describe_trend(day, trend),
                )  # fmt: skip
        if acted:
            self._note_decision_difference(day, now, acted)
        return True

    # ------------------------------------------------------------ BF-D34 fund sweep
    def _book_state(self, book: str, day: date) -> str | None:
        """The L15 state of ``book``'s own latest decision at or before ``day`` (the books
        can decide on different days: L6 skips the start month-end for the paper book
        only). None: the switch is off or the book has not decided under it."""
        if not self.s.band_trend.enabled:
            return None
        days = [
            k.rsplit(":", 1)[1]
            for k, r in self.j.job_records(f"decide:{book}:")
            if "digest" in r and k.rsplit(":", 1)[1] <= str(day)
        ]
        if not days:
            return None
        recs = dict(self.j.job_records(f"bt:{max(days)}"))
        rec = recs.get(f"bt:{max(days)}")
        return None if rec is None else str(rec["state"])

    def job_fund_sweep(self, day: date, now: datetime) -> bool:
        """BF-D34 (report 98): in FUND state, after the switch, a share the switch could
        not sell (no trade, halted, limit not met; L7's three carries over) is offered
        again every session it trades, and cash from such sales (or a fund buy cut to
        the cash settled at the time) goes into the fund at once, not at the next
        month-end. Every book alike: the paper book (owner approval, L8), the twin and
        the random twins (auto). A book with a decision today is left to the decision."""
        fund = self.s.band_trend.fund
        if not self.s.band_trend.enabled or not any(
            self._book_state(book, day) == "FUND" for book, *_ in self._books()
        ):
            return True
        closes = dict(self.closes(day))
        if not closes:
            return now >= at(day, RETRY_UNTIL)  # the day's closes may still come
        panel = self.panels(day)
        liq = liquidity_table(panel)
        tv20 = {
            e: Decimal(repr(float(liq.tv_med20[j]))).quantize(Decimal(1))
            for j, e in enumerate(panel.entities)
            if liq.tv_med20[j] == liq.tv_med20[j]
        }
        x = self.next_session(day)
        for book, ex, broker, mode in self._books():
            key = f"sweep:{book}:{day}"
            if self.j.job_done(key) or self.j.job_done(f"decide:{book}:{day}"):
                continue
            if self._book_state(book, day) != "FUND":
                continue
            batch = self._sweep_batch(book, day, closes, tv20, fund)
            if batch is None:
                self.j.mark_job(key, {"orders": 0}, now)
                continue
            ctx = self._ctx(book, broker, x, day, now, True, data_as_of=panel.as_of)
            ex.plan(batch, mode, x, ctx)
            self.j.mark_job(key, {"batch": batch.batch_id, "orders": len(batch.intents)}, now)
            if book == self.s.book:
                self.say(
                    f"Fund sweep {day} (BF-D34, state: FUND): leftover shares sold and their "
                    "cash put into the fund\n" + render_batch(self.j, batch.batch_id, "PAPER")
                )
                for p in ex.plan_pages:
                    self.say("PAGE " + p)
        return True

    def _sweep_batch(
        self,
        book: str,
        day: date,
        closes: Mapping[str, Decimal],
        tv20: Mapping[str, Decimal],
        fund: str,
    ) -> OrderBatch | None:
        open_ = [it for it, st in self._all_intents(book) if st not in TERMINAL]
        selling: dict[str, int] = {}
        for it in open_:
            if it.side is Side.SELL:
                selling[it.entity] = selling.get(it.entity, 0) + it.qty
        band = self.s.order_params.limit_band
        bid = batch_id_for(book, day, "F")
        out: list[OrderIntent] = []
        for e, q in sorted(self._book_positions(book, day).items()):
            rest = q - selling.get(e, 0)
            ref = closes.get(e)
            if e == fund or rest <= 0 or ref is None or ref <= 0:
                continue  # no trade today (halted): offered again the next session
            out.append(
                OrderIntent(
                    client_order_id(book, day, e, Side.SELL),
                    bid,
                    len(out) + 1,
                    self.s.line,
                    book,
                    day,
                    e,
                    Side.SELL,
                    rest,
                    self.s.order_params.order_type,
                    ref,
                    round_to_step(ref * (1 - band), Side.SELL),
                    BT_LEFTOVER_SELL,
                    tv_med20=tv20.get(e),
                    prev_close=ref,
                )
            )
        decided = [k.rsplit(":", 1)[1] for k, _ in self.j.job_records(f"decide:{book}:")]
        last = max(decided, default="")
        sold = any(
            f.side is Side.SELL and f.entity != fund and str(f.executed_at.date()) >= last
            for f in self.j.fills(book)
        )
        ref = closes.get(fund)
        buying = any(it.side is Side.BUY for it in open_)
        if sold and not buying and ref is not None and ref > 0:
            p = self.s.params
            fund_cost = self.j.cost_book(book).cost.get(fund, Decimal(0))
            cash = min(self.j.cash(book) - p.cash_reserve_aud, p.capital_cap_aud - fund_cost)
            lim = round_to_step(ref * (1 + band), Side.BUY)
            qty = int((cash / lim).to_integral_value(ROUND_DOWN)) if cash > 0 else 0
            if qty > 0 and ref * qty >= p.min_parcel_aud:
                out.append(
                    OrderIntent(
                        client_order_id(book, day, fund, Side.BUY),
                        bid,
                        len(out) + 1,
                        self.s.line,
                        book,
                        day,
                        fund,
                        Side.BUY,
                        qty,
                        self.s.order_params.order_type,
                        ref,
                        lim,
                        BT_FUND_SWEEP,
                        tv_med20=tv20.get(fund),
                        prev_close=ref,
                        flags=("FUND",),
                    )
                )
        if not out:
            return None
        return OrderBatch(
            bid, book, day, tuple(out), (), sha256_json([i.client_order_id for i in out])
        )

    def _band_trend(
        self, panel: PricePanel, day: date, now: datetime, lst: Emg2List | None
    ) -> BandTrend | None:
        """L15 (BF-D28): the band-trend state of the decision, recorded once a day in the
        journal (``bt:<day>``). None when the switch is off or the day's data is not in
        (then the decision is a rule-14 data block anyway)."""
        if not self.s.band_trend.enabled or lst is None:
            return None
        trend = band_trend(panel, self.s.band_trend)
        forced = self.s.forced(day)
        if forced in ("EMG2", "FUND") and forced != trend.state:
            self._forced_from[day] = trend.state  # BF-D32: the rule's own state, shown
            trend = replace(trend, state=forced)  # type: ignore[arg-type]
        key = f"bt:{day}"
        if not self.j.job_done(key):
            rec = trend.payload()
            if day in self._forced_from:
                rec["forced_from"] = self._forced_from[day]
            self.j.mark_job(key, rec, now)
        return trend

    def _describe_trend(self, day: date, trend: BandTrend) -> str:
        """``BandTrend.describe`` with the BF-D32 dry-run override made plain."""
        real = self._forced_from.get(day)
        if real is None:
            return trend.describe()
        rel = "at or above" if real == "EMG2" else "below"
        return (
            f"state: {trend.state} FORCED (paper dry run, BF-D32; the L15 rule says {real}: "
            f"band 301-600 index {trend.level:.4f} {rel} its {len(trend.levels)}-month "
            f"average {trend.mean:.4f}, {trend.as_of})"
        )

    def _decide_book(
        self,
        panel: PricePanel,
        state: BookState,
        lst: Emg2List | None,
        order: TargetOrder | None,
        trend: BandTrend | None,
        ages: Mapping[str, int | None] | None = None,
    ) -> Emg2_20Decision:
        """Rules L2-L5, under L15 when the band-trend switch is on (BF-D28), with the sell
        rule of the config (L4, or C6 with ``ages``: BF-D35)."""
        # a random twin's keep zone is its random score's; any other order: the EMG2 score's
        keep = order.keep_zone if isinstance(order, RandomOrder) else None
        if trend is None:
            return decide_emg2_20(
                panel, state, self.s.params, lst=lst, target_order=order, ages=ages,
                keep_order=keep,
            )  # fmt: skip
        return decide_emg2_18_bt(
            panel, state, self.s.params, lst=lst, target_order=order, trend_on=trend.on,
            fund=self.s.band_trend.fund, top_up_fraction=self.s.band_trend.top_up_fraction,
            ages=ages, keep_order=keep,
        )  # fmt: skip

    def month_ends(self) -> frozenset[date]:
        """Month-end sessions of the calendar (the last session of each calendar month)."""
        if self._month_ends is None:
            ss = self.sessions
            self._month_ends = frozenset(
                a for a, b in pairwise(ss) if (a.year, a.month) != (b.year, b.month)
            )
        return self._month_ends

    def holding_ages(
        self, book: str, day: date, holdings: Mapping[str, int]
    ) -> dict[str, int | None]:
        """BF-D35 rule L4-C6.1: each holding's age at a decision on ``day``, in month-ends:
        the month-end sessions after the decision session of its latest filled buy, up to
        and including ``day`` (the purchase decision counts as zero). Every month-end
        counts, a data block or L6's skipped start month-end included, so the paper book
        and its twin see the same age. Computed from the journal only (fills and their
        intents, old codes followed through code changes), so a restart changes nothing.
        EMG2 never buys a name it holds, so the latest buy is the one that opened the
        holding (a name sold in full and bought again starts from zero). None: no buy of
        its own (a corporate-action share): counted as old enough."""
        imap = self.j.identity_map()
        when = {it.client_order_id: it.decision_date for it, _ in self.j.intents_of_book(book)}
        bought: dict[str, date] = {}
        for f in self.j.fills(book):  # in execution order: the latest buy wins
            if f.side is not Side.BUY or f.client_order_id not in when:
                continue
            d0 = when[f.client_order_id]
            if d0 <= day:
                bought[imap.get(f.entity, f.entity)] = d0
        me = self.month_ends()
        out: dict[str, int | None] = {}
        for e in sorted(holdings):
            first = bought.get(e)
            out[e] = None if first is None else sum(1 for m in me if first < m <= day)
        return out

    def _switches(self, dec: Emg2_20Decision, holdings: Mapping[str, int]) -> bool:
        """The decision moves the book into the fund (a first fund buy) or out of it."""
        fund = self.s.band_trend.fund
        first_in = any(b.reason == BT_FUND_BUY for b in dec.buys) and not holdings.get(fund)
        return first_in or any(s.reason == BT_FUND_SELL for s in dec.sells)

    def state_line(self, day: date) -> str | None:
        """L14 + L15: "state: EMG2" / "state: FUND" from the latest decision's band-trend
        record at or before ``day`` (None when the switch is off or none is recorded)."""
        if not self.s.band_trend.enabled:
            return None
        recs = [r for k, r in self.j.job_records("bt:") if k.split(":", 1)[1] <= str(day)]
        if not recs:
            return "state: not decided yet (L15 band-trend switch)"
        r = recs[-1]
        if r.get("forced_from"):  # BF-D32
            return (
                f"state: {r['state']} FORCED (paper dry run, BF-D32; the L15 rule said "
                f"{r['forced_from']}, {r['as_of']})"
            )
        rel = "at or above" if r["state"] == "EMG2" else "below"
        return (
            f"state: {r['state']} (band 301-600 index {float(r['level']):.4f} {rel} its "
            f"{len(r['levels'])}-month average {float(r['mean']):.4f}, {r['as_of']})"
        )

    def _announce(
        self,
        day: date,
        canary: bool,
        list_digest: str,
        batch_id: str,
        pages: Sequence[str],
        state: str | None = None,
    ) -> None:
        head = f"Decision {day} ({'start, canary first' if canary else 'regular'}); "
        head += f"list {list_digest[:12]}; {len(self.j.intents_of(batch_id))} order(s)"
        if state is not None:
            head += "\n" + state
        if self.s.params.sell_rule == "C6":  # BF-D35
            head += (
                "\nsell rule C6: a share is sold after >= 6 month-ends held and only outside "
                "the top 40% of band C (BID_PEG and the L15 switch at once)"
            )
        if self.s.lic_note:
            head += "\n" + self.s.lic_note
        lvl = self.j.safety_level()
        if lvl in BLOCKS_BUYS:
            head += f"\nSafety {lvl.value}: the buys below are not sent unless you " + (
                "/resume <code> before they go; sells proceed"
                if lvl not in BLOCKS_ALL
                else "re-arm; sells wait for the re-arm too"
            )
        self.say(head + "\n" + render_batch(self.j, batch_id, "PAPER"))
        for p in pages:  # BF-D3: a sell above A$800 goes through, paged
            self.say("PAGE " + p)

    def _data_block(self, book: str, key: str, day: date, now: datetime, why: str) -> None:
        self.j.mark_job(key, {"data_block": why}, now)
        if book == self.s.book:
            self.say(f"PAGE rule 14 data block on {day}: {why}. No decision; holdings kept.")

    def _note_decision_difference(
        self, day: date, now: datetime, acted: Mapping[str, set[tuple[str, str]]]
    ) -> None:
        """L13: record (and tell the owner) where the twin's orders of a decision differ
        from the broker book's: their states differ after an unfilled or unapproved
        order, their cash differs by fills and spread (a parcel then falls under A$500 in
        one book only), or one book made no decision (L6 skip, data block). Only these
        names, and names of orders that did not fill, explain a holdings difference."""
        mine = acted.get(self.s.book, set())
        twin = acted.get(self.s.sim_book, set())
        diff = sorted({e for e, _ in mine ^ twin})
        self.j.mark_job(f"l13:{day}", {"diff": diff}, now)
        if diff:
            self.say(
                f"L13 note {day}: the twin's orders differ from the paper book's on "
                f"{', '.join(diff)} (their holdings or cash differ)."
            )

    # ------------------------------------------------------------ send time
    def _active(self, book: str, day: date) -> list[tuple[str, bool]]:
        """Batches with sendable intents today, and whether today is their last chance.
        Intents of batches past the L7 window are closed here (held buys lapse)."""
        out = []
        for bid, xd in self.j.batches_of(book):
            if xd is None or xd > day:
                continue
            waited = self.sessions_between(xd, day)
            open_ = [
                (it, st)
                for it, st in self.j.intents_of(bid)
                if st in (Status.RISK_OK, Status.APPROVED, Status.HELD)
            ]
            if not open_:
                continue
            if waited > self.s.buy_funds_wait_sessions:
                for it, st in open_:
                    to = Status.RISK_REJECTED if st == Status.HELD else Status.LAPSED
                    self.j.set_status(
                        it.client_order_id, to, {"why": "L7 window D+4 is over"}, self.now
                    )
                continue
            out.append((bid, waited >= self.s.buy_funds_wait_sessions))
        return out

    def job_submit(self, day: date, now: datetime) -> None:
        if self.lic_list_refused(day, now, "send") is not None:
            return  # BF-D21: no order of any book is sent (the twins stay in step)
        for book, ex, broker, _ in self._books():
            for bid, final in self._active(book, day):
                b = self.j.batch(bid)
                assert b is not None
                start_day = bid.endswith(
                    ("-S", "-C", "-B", "-F")
                )  # BF-D28/D34: a switch as the start
                rep = ex.submit(
                    bid,
                    self._ctx(book, broker, day, b["decision_date"], now, start_day),
                    now,
                    final_day=final,
                )
                if book == self.s.book:
                    if rep.sent or rep.not_approved or rep.rejected:
                        self.say(
                            f"{bid}: sent {len(rep.sent)}, not approved {len(rep.not_approved)}, "
                            f"held/rejected {len(rep.rejected)}"
                        )
                    for p in rep.pages:
                        self.say("PAGE " + p)

    # ------------------------------------------------------------ after the close
    def job_collect(self, day: date, now: datetime) -> None:
        self.ex.collect_fills(now, session_closed=True)
        self._carry(self.s.book, self.ex, self.broker, self.s.approval_mode, day, now)

    def _carry(
        self, book: str, ex: Executor, broker: Broker, mode: str, day: date, now: datetime
    ) -> None:
        """L7: an order unfilled at the close is carried to the next session at a new
        reference (the day's close) inside the band: buys once, sells up to three
        times, then a sell is paged. A carried order needs approval again (L8)."""
        closes: Mapping[str, Decimal] | None = None  # read only when an order is carried
        band = self.s.order_params.limit_band
        idmap = self.j.identity_ratios()  # BF-D19/D25: an old code's order goes on the new
        new: list[OrderIntent] = []
        keys: list[str] = []
        for it, st in self._all_intents(book):
            key = f"carry:{it.client_order_id}"
            if st != Status.EXPIRED or self.j.job_done(key):
                continue
            rest = it.qty - sum(f.qty for f in self.j.fills(coid=it.client_order_id))
            sell = it.side is Side.SELL
            limit_n = self.s.sell_carry_sessions if sell else self.s.buy_carry_sessions
            if it.attempt > limit_n or rest <= 0:
                self.j.mark_job(key, {"carried": False, "attempt": it.attempt}, now)
                if sell and rest > 0 and book == self.s.book:
                    self.say(
                        f"PAGE sell {rest} {it.entity} unfilled after {it.attempt} sessions "
                        "(L7); review"
                    )
                continue
            if closes is None:
                closes = self.closes(day)
            ent, ratio = idmap.get(it.entity, (it.entity, Decimal(1)))
            ref = closes.get(ent) or it.ref_price
            if sell:
                lim = round_to_step(ref * (1 - band), Side.SELL)
                qty = int(rest * ratio)  # shares of the new code (fractions dropped)
            else:
                lim = round_to_step(ref * (1 + band), Side.BUY)
                qty = int(rest * it.limit_price // lim)  # never above the original value
                if qty <= 0 or ref * qty < self.s.order_params.min_parcel_aud:
                    self.j.mark_job(key, {"carried": False, "why": "MIN_PARCEL"}, now)
                    continue
            new.append(
                replace(
                    it,
                    client_order_id=client_order_id(
                        book, it.decision_date, ent, it.side, it.attempt + 1
                    ),
                    entity=ent,
                    qty=qty,
                    ref_price=ref,
                    limit_price=lim,
                    prev_close=ref,
                    attempt=it.attempt + 1,
                    flags=(*[f for f in it.flags if f != "CARRIED"], "CARRIED"),
                )
            )
            keys.append(key)
        if not new:
            return
        bid = batch_id_for(book, day, "X")
        intents = tuple(replace(it, batch_id=bid, seq=k) for k, it in enumerate(new, start=1))
        batch = OrderBatch(
            bid, book, day, intents, (), sha256_json([i.client_order_id for i in intents])
        )
        x = self.next_session(day)
        ex.plan(batch, mode, x, self._ctx(book, broker, x, day, now, False))
        for key in keys:
            self.j.mark_job(key, {"carried": True, "batch": bid}, now)
        if book == self.s.book:
            self.say(
                f"Carried to {x} (L7): {len(intents)} order(s)\n"
                + render_batch(self.j, bid, "PAPER")
            )

    def job_flex_pull(self, day: date, now: datetime) -> None:
        """BF-D27: the paper account's Activity Flex statement to the previous session,
        downloaded into the inbox once a day (each slot until it is there); paged once
        a day when still missing at the last slot before the reconciliation, or at once
        on an error the next slot would not fix (no secret, refused token, not paper)."""
        if self.flex_pull is None or self.j.job_done(f"flex-pull:{day}"):
            return
        prev = max((d for d in self.sessions if d < day), default=day - timedelta(days=1))
        last = max(
            (date.fromisoformat(str(r["to"])) for _, r in self.j.job_records("flex-pull:")),
            default=None,
        )
        res = self.flex_pull.pull(prev, last, now)
        info = {
            "status": res.status, "from": str(res.from_date), "to": str(res.to_date),
            "tries": res.tries, "note": res.note,
        }  # fmt: skip
        if res.ok:
            assert res.path is not None
            self.j.mark_job(f"flex-pull:{day}", {**info, "file": res.path.name}, now)
            self._ca_note(
                day, now,
                f"INFO Flex statement {res.from_date}..{res.to_date} in the inbox "
                f"({res.path.name}, {res.status.lower()})",
            )  # fmt: skip
            return
        self.j.mark_job(f"flex-try:{day}", info, now)
        last_slot = now >= at(day, FLEX_PAGE_SLOT)
        if (res.fatal or last_slot) and not self.j.job_done(f"flex-page:{day}"):
            self.j.mark_job(f"flex-page:{day}", info, now)
            what = "late/missing" if res.status in ("NOT_READY", "FAILED") else "refused"
            self.say(
                f"PAGE IBKR Flex statement to {res.to_date} {what} ({res.status}: "
                f"{res.note}). The 16:30 reconciliation runs on the inbox as it is (pending "
                "corporate actions stay expectations). Check the Flex token / query (Docker "
                "secrets) or put the statement XML in the inbox by hand."
            )

    def _store_stale(self, day: date) -> str | None:
        """BF-D31: why the price store is stale for a decision on ``day`` (None: fresh,
        or no refresher configured)."""
        if self.store_refresh is None:
            return None
        last = self.store_refresh.last_day()
        if last is not None and last >= day:
            return None
        return (
            f"price store stale: newest bulk day {last or 'none'} is before {day} "
            "(BF-D31; no decision on stale data)"
        )

    def job_store_refresh(self, day: date, now: datetime) -> None:
        """BF-D31: the day's EODHD bulk closes, dividends and splits into the price store
        the decision reads, once a day (each slot until it is there); the owner is paged
        once a day when it is still missing at the last slot, or at once on an error the
        next slot will not fix (no key, budget used up, key refused)."""
        if self.store_refresh is None or self.j.job_done(f"store-refresh:{day}"):
            return
        res = self.store_refresh.refresh(day, self.j, now)
        info = {"status": res.status, "rows": res.rows, "calls": res.calls, "note": res.note}
        if res.ok:
            self.j.mark_job(f"store-refresh:{day}", info, now)
            return
        self.j.mark_job(f"store-try:{day}", info, now)
        last_slot = now >= at(day, STORE_PAGE_SLOT)
        if (res.fatal or last_slot) and not self.j.job_done(f"store-page:{day}"):
            self.j.mark_job(f"store-page:{day}", info, now)
            self.say(
                f"PAGE price store not refreshed for {day} ({res.status}: {res.note}). "
                "No decision is made on stale data (BF-D31); the twins wait for the "
                "day's closes. Check the EODHD key (Docker secret eodhd_api_token), the "
                "call budget, or EODHD's status; the refresh can be re-run by hand."
            )

    def job_reconcile(self, day: date, now: datetime) -> None:
        self._ingest_flex(day, now)
        pending: tuple[Expected, ...] = ()
        cal = self._calendar(self.j.positions(self.s.book), day)
        if cal is not None:  # BF-D23: IBKR may show an event before its Flex record
            pending = tuple(pending_expectations(self.j, self.s.book, cal, day))
        r = reconcile_and_page(
            self.j, self.broker, self.s.book, self.transport, self.s.chats, now, pending
        )
        self.j.mark_job(
            f"recon:{self.s.book}:{day}",
            {
                "ok": r.ok,
                "breaks": list(r.breaks),
                "explained": list(r.explained),
                "cash": str(self.j.cash(self.s.book)),
            },
            now,
        )
        if not r.ok:
            self.log.append("RECON BREAK " + "; ".join(r.breaks))
        for x in r.explained:
            self._ca_note(day, now, f"INFO reconciled with a pending corporate action: {x}")
        self._start_followup(day, now, r.ok)

    # ------------------------------------------------------------ corporate actions (BF-D23)
    def _held_codes(self) -> frozenset[str]:
        books = (self.s.book, *(b for b, _ in self._sim_brokers()))
        return frozenset(e for b in books for e in self.j.positions(b))

    def _calendar(self, codes: Mapping[str, int] | frozenset[str], day: date) -> CaCalendar | None:
        if self.ca_source is None:
            return None
        return self.ca_source(frozenset(codes), day - timedelta(days=120), day)

    def _book_positions(self, book: str, day: date) -> dict[str, int]:
        """Holdings for valuation, decisions and sizing (BF-D26): the journal's, and for
        the broker book a calendar split or consolidation of a held code whose date has
        come and that IBKR's Flex record has not yet settled at its expected count (the
        broker already trades the new count; the booking still waits for IBKR's record,
        which normally comes the next afternoon). The simulated books are booked on the
        date itself, so theirs are the journal's."""
        pos = dict(self.j.positions(book))
        if book != self.s.book:
            return pos
        cal = self._calendar(pos, day)
        if cal is None:
            return pos
        for x in pending_expectations(self.j, book, cal, day):
            if x.label.startswith("SPLIT "):  # trader.corporate_actions.expectations
                for e, d in x.shares.items():
                    if e in pos:
                        pos[e] = max(pos[e] + d, 0)
        return {e: q for e, q in pos.items() if q}

    def _ca_note(self, day: date, now: datetime, line: str) -> None:
        """A line for the day's report (kept in the journal: ``ca-note:<day>``)."""
        if line not in self._ca_lines(day):
            self.j.mark_job(f"ca-note:{day}", {"line": line}, now)

    def _ca_lines(self, day: date) -> list[str]:
        return [str(r["line"]) for k, r in self.j.job_records(f"ca-note:{day}") if "line" in r]

    def _ingest_flex(self, day: date, now: datetime) -> None:
        """The broker book's dividends, capital returns and corporate actions from IBKR's
        own records (Activity Flex), once each; a code change IBKR reports is applied as
        PROPOSED with its ratio and the owner is paged to confirm (``/idmap``)."""
        if self.flex is None:
            return
        try:
            sts = list(self.flex(day))
        except (FlexError, OSError) as e:  # Flex for D-1 arrives in the afternoon (R37)
            self._ca_note(day, now, f"INFO Flex statements not read today: {e}")
            return
        if not sts:
            return
        cal = self._calendar(self._held_codes(), day) or CaCalendar()
        px = dict(self.marks(day)) if any(st.corporate_actions for st in sts) else {}
        res = ingest_flex(self.j, self.s.book, sts, cal, px, now)
        for b in res.booked:
            self._ca_note(day, now, f"INFO {self.s.book} booked from IBKR: {describe(b)}")
        if res.booked:
            self.say(
                f"{self.s.book}: corporate actions booked from IBKR's records:\n"
                + "\n".join(describe(b) for b in res.booked)
            )
        for x in res.identity:
            old, new = x.split(" -> ")[0], x.split(" -> ")[1].split()[0]
            self.say(
                f"PAGE code change reported by IBKR: {x}. Holdings are carried under {new} "
                f"(share count by the ratio, cost kept). Confirm: /idmap {old} {new} "
                f"<ratio> <code>. Undo: /idmap_reject {old} <code>."
            )

    def _ca_sim(self, day: date, now: datetime, closes: Mapping[str, Decimal]) -> None:
        """The simulated books' corporate actions of the day from the calendar (vendor
        dividends + the record's CSV; BW-UNI-23: on the ex-date, on the holding at the
        close before); an event on a non-session date is booked on the next session."""
        held = self._held_codes()
        cal = self._calendar(held, day)
        if cal is None:
            return
        prev = max((d for d in self.sessions if d < day), default=day - timedelta(days=1))
        evs = cal.between(prev + timedelta(days=1), day)
        known = self.j.identity_records()
        for ev in evs:
            if (
                ev.kind is CaKind.CODE_CHANGE
                and ev.new_code
                and ev.code in held
                and ev.code not in known
            ):
                self.j.add_identity(
                    ev.code, ev.new_code, "PROPOSED", ev.source[:8], None, "calendar",
                    f"{ev.key}: {ev.note}"[:200], now, ratio=ev.ratio,
                )  # fmt: skip
                self.say(
                    f"PAGE code change {ev.code} -> {ev.new_code} (ratio "
                    f"{ev.ratio or 1}) from the corporate-action calendar; carried as "
                    f"{ev.new_code}. Confirm: /idmap {ev.code} {ev.new_code} "
                    f"{ev.ratio or 1} <code>. Undo: /idmap_reject {ev.code} <code>."
                )
            if ev.kind is CaKind.DIVIDEND and ev.source == "VENDOR" and ev.per_share:
                c = closes.get(ev.code)
                if ev.code in held and c and ev.per_share >= c / 10:
                    self._ca_note(
                        day, now,
                        f"WARN vendor dividend {ev.code} A${ev.per_share} is "
                        f"{ev.per_share / c * 100:.0f}% of its close: a special or a capital "
                        "return? Classify it in CORPORATE_ACTIONS.csv",
                    )  # fmt: skip
        rest = [e for e in evs if e.kind is not CaKind.CODE_CHANGE]
        sims = dict(self._sim_brokers())
        got = book_calendar_day(self.j, list(sims), rest, closes, now)
        for book in {b for b, _ in got}:
            sb = sims[book]
            sb.cash += sum((x.cash for b, x in got if b == book), Decimal(0))
            sb.holdings = dict(self.j.positions(book))
        for b, x in got:
            if b == self.s.sim_book:
                self._ca_note(day, now, f"INFO {b} booked from the calendar: {describe(x)}")
        n_rnd = len({b for b, _ in got if b != self.s.sim_book})
        if n_rnd:
            self._ca_note(day, now, f"INFO corporate actions booked in {n_rnd} random twin(s)")
        split = {ev.code for ev in rest if ev.kind is CaKind.SPLIT}
        open_ = sorted({
            it.entity
            for bk in (self.s.book, *sims)
            for it, st in self._all_intents(bk)
            if it.entity in split and st not in TERMINAL
        })  # fmt: skip
        if open_:  # BF-D26: an order sized before the split is not re-sized
            self.say(
                f"PAGE split/consolidation of {', '.join(open_)} on {day} with an order still "
                "open: its quantity and limit are pre-split; review (cancel and re-plan)"
            )

    def _start_followup(self, day: date, now: datetime, recon_ok: bool) -> None:
        """L6: the other start buys go the session after the canary fills and the book
        reconciles to the cent; a canary that ends unfilled stops the start (paged)."""
        for key, rec in self.j.job_records(f"start:{self.s.book}:"):
            done_key = "start-done:" + key.split(":", 1)[1]
            if self.j.job_done(done_key):
                continue
            sd = date.fromisoformat(key.rsplit(":", 1)[1])
            can = [
                (it, st)
                for it, st in self._all_intents(self.s.book)
                if "CANARY" in it.flags and it.decision_date == sd
            ]
            if any(st == Status.FILLED for _, st in can):
                if not recon_ok:
                    continue  # waits for a clean reconciliation
                rest = _decision_from(self.s.book, rec, skip_first=1)
                if not rest.buys:  # BF-D28: the canary was the whole start (the fund order)
                    self.j.mark_job(done_key, {"batch": None}, now)
                    self.say("Canary filled and reconciled to the cent; no other start orders.")
                    continue
                tv = {e: Decimal(v) for e, v in rec["tv20"].items()}
                batch = build_orders(
                    rest, line=self.s.line, params=self.s.order_params, kind="S", tv_med20=tv
                )
                x = self.next_session(day)
                ctx = self._ctx(self.s.book, self.broker, x, sd, now, True)
                self.ex.plan(batch, self.s.approval_mode, x, ctx)
                self.j.mark_job(done_key, {"batch": batch.batch_id}, now)
                self.say(
                    f"Canary filled and reconciled to the cent. Remaining {len(batch.intents)} "
                    f"start buys for {x}:\n" + render_batch(self.j, batch.batch_id, "PAPER")
                )
            elif can and all(st in TERMINAL for _, st in can):
                self.j.mark_job(done_key, {"stopped": [st for _, st in can]}, now)
                self.say(
                    "PAGE canary did not fill; the start stops here (L6). "
                    "Review before a new start."
                )

    def job_sim(self, day: date, now: datetime) -> bool:
        closes = dict(self.closes(day))
        if not closes:
            if now < at(day, RETRY_UNTIL):
                return False
            self.say(f"PAGE no closes for {day}: the twin is not advanced today")
            return True
        self._ca_sim(day, now, closes)  # BF-D23: before the auction, on yesterday's holdings
        self._code_changes(day, now, closes)
        self.sim.advance(day, closes)
        self.ex_sim.collect_fills(now, session_closed=True)
        self._carry(self.s.sim_book, self.ex_sim, self.sim, "auto", day, now)
        for name, _, ex, rb in self.rnd:  # BF-D18: the random twins, same auction and costs
            rb.advance(day, closes)
            ex.collect_fills(now, session_closed=True)
            self._carry(name, ex, rb, "auto", day, now)
        r = compare_books(
            self.j.positions(self.s.sim_book), self.j.positions(self.s.book), self._explained(day)
        )
        if not r.ok:
            lvl = worst(self.j.safety_level(), SafetyLevel.HALTED_INTEGRITY)
            self.j.set_safety(lvl, "L13: " + "; ".join(r.breaks)[:180], "l13", now)
            self.say(
                "PAGE L13 sim/broker holdings differ without an explanation:\n"
                + "\n".join(r.breaks)
            )
        return True

    def _explained(self, day: date | None = None) -> set[str]:
        """L13: names whose holdings difference an order explains: an order of either
        book that did not fill (unapproved, vetoed, held, expired, rejected, pending),
        or a name on which the two books' decisions differed (recorded at decide); and
        (BF-D23) the codes of a corporate action of the last 70 days, which the twin
        books on the ex-date and the broker book when IBKR's records arrive."""
        out = {
            it.entity
            for book in (self.s.book, self.s.sim_book)
            for it, st in self._all_intents(book)
            if st != Status.FILLED or "L11_WIND_DOWN" in it.flags  # L11: only the live book
        }
        for _, rec in self.j.job_records("l13:"):
            out.update(rec.get("diff", []))
        if day is not None:
            lo = day - timedelta(days=70)
            for book in (self.s.book, self.s.sim_book):
                for b in self.j.ca_bookings(book):
                    if b.new_code and (b.ex_date or b.pay_date or day) >= lo:
                        out.update({b.code, b.new_code})
            cal = self._calendar(self._held_codes(), day)
            for ev in cal.between(lo, day) if cal is not None else ():
                if ev.new_code:
                    out.update({ev.code, ev.new_code})
        planned = {k.split(":", 1)[1] for k, r in self.j.job_records("start-done:") if "batch" in r}
        for key, rec in self.j.job_records(f"start:{self.s.book}:"):
            if key.split(":", 1)[1] not in planned:  # L6: the other start buys wait for the
                out.update(str(b[0]) for b in rec["buys"])  # canary (or the start stopped)
        return out

    # ------------------------------------------------------------ code changes (BF-D19)
    def _sim_brokers(self) -> list[tuple[str, SimBroker]]:
        return [(self.s.sim_book, self.sim), *((name, rb) for name, _, _, rb in self.rnd)]

    def _code_changes(self, day: date, now: datetime, closes: Mapping[str, Decimal]) -> None:
        """A held code with no close today that A7 maps to a code trading today changed
        its code: carried under the new code (PROPOSED), owner paged to confirm."""
        books = (self.s.book, *(b for b, _ in self._sim_brokers()))
        held: dict[str, dict[str, int]] = {}
        for b in books:
            for e, q in self.j.positions(b).items():
                held.setdefault(e, {})[b] = q
        changes = code_changes(held, self.panels(day), closes, self.j.identity_records())
        for c in changes:
            score = Decimal(repr(c.score)).quantize(Decimal("0.000001"))
            self.j.add_identity(
                c.old, c.new, "PROPOSED", c.rule, score, "system",
                f"no close for {c.old} on {day}; A7 maps it to {c.new}", now,
            )  # fmt: skip
            mine = held[c.old].get(self.s.book, 0)
            twin = held[c.old].get(self.s.sim_book, 0)
            self.say(
                f"PAGE code change {day}: {c.old} has no close today and {c.new} carries the "
                f"same prices ({c.rule} {c.score:.4f}); {c.new} closed at {closes[c.new]}. "
                f"Holdings of {c.old} (paper book {mine}, twin {twin}) are carried as "
                f"{c.new} at its price; {c.old} and {c.new} are one company (never bought "
                f"twice). Confirm: /idmap {c.old} {c.new} <code>. Undo: /idmap_reject "
                f"{c.old} <code>."
            )
        m = self.j.identity_ratios()
        if m != self._idmap_seen:  # applied, confirmed or undone: simulated books follow
            for b, sb in self._sim_brokers():
                sb.holdings = dict(self.j.positions(b))
            self._idmap_seen = m

    def _ca_tax_flags(self) -> list[str]:
        """Bookings whose tax treatment waits for a figure (a demerger's cost split, an
        in-specie distribution's income/capital split): flagged until superseded."""
        return [
            f"WARN tax: {b.kind.value} {b.code}->{b.new_code} is {b.tax_class}; enter the "
            "class-ruling figure in CORPORATE_ACTIONS.csv (cost_base_pct / capital_per_share)"
            for b in self.j.ca_bookings(self.s.book)
            if b.tax_class
        ]

    def _code_change_flags(self) -> list[str]:
        return [
            f"PAGE: code change {o} -> {r['new_code']} not confirmed: "
            f"/idmap {o} {r['new_code']} <code> (or /idmap_reject {o} <code>)"
            for o, r in sorted(self.j.identity_records().items())
            if r["status"] == "PROPOSED"
        ]

    # ------------------------------------------------------------ random twins (BF-D18)
    def _rnd_origin(self, day: date, now: datetime) -> int:
        """Month index of the random twins' first decision (the origin of their scores),
        recorded once in the journal so a restart keeps the same scores."""
        rec = self.j.job_records("rnd-origin")
        if rec:
            return int(rec[0][1]["month"])
        self.j.mark_job("rnd-origin", {"month": month_index(day), "day": str(day)}, now)
        return month_index(day)

    def _random_order(self, seed: int | None, day: date, now: datetime) -> RandomOrder | None:
        if seed is None:
            return None  # the paper book and the simulated twin: T in score order
        return RandomOrder(seed, self._rnd_origin(day, now), month_index(day))

    def _book_value(self, book: str, px: Mapping[str, Decimal]) -> Decimal:
        pos = self.j.positions(book)
        return self.j.cash(book) + sum(
            (px.get(e, Decimal(0)) * q for e, q in pos.items()), Decimal(0)
        )

    def twin_values(self, day: date) -> tuple[Decimal, list[Decimal]] | None:
        """Values at ``day`` of the simulated twin and of its random twins (marks of the
        day; a held name with no mark at its last recorded mark). None without twins."""
        if not self.rnd:
            return None
        px = dict(self.marks(day))
        last = self._last_marks()
        for e, (_, v) in last.items():
            px.setdefault(e, Decimal(v))
        sim = self._book_value(self.s.sim_book, px)
        return sim, [self._book_value(name, px) for name, *_ in self.rnd]

    def twin_percentile(self, day: date) -> Decimal | None:
        """L11 test (b): the simulated twin's percentile (0-100, ties half) among its
        random twins by value since the common start (all start with the same capital,
        so value order is return order). None while the twins are not running."""
        v = self.twin_values(day)
        if v is None:
            return None
        return percentile_rank(v[0], v[1])

    def _rnd_line(self, day: date, now: datetime) -> str | None:
        """The report's random-twin line (L13); the values go to the journal (``rnd:``)."""
        v = self.twin_values(day)
        if v is None:
            return None
        sim, vals = v
        pct = percentile_rank(sim, vals)
        q = sorted(vals)
        med = (q[(len(q) - 1) // 2] + q[len(q) // 2]) / 2
        if not self.j.job_done(f"rnd:{day}"):
            self.j.mark_job(
                f"rnd:{day}",
                {"sim": str(sim), "percentile": str(pct), "values": [str(x) for x in vals]},
                now,
            )
        return (
            f"Simulated twin at the {pct} percentile of {len(vals)} random twins "
            f"(their median A${med.quantize(Decimal('0.01'))}; L11 test (b) needs >= 10)"
        )

    def _last_marks(self) -> dict[str, tuple[str, str]]:
        last: dict[str, tuple[str, str]] = {}
        for key, rec in self.j.job_records("marks:"):
            for e, v in rec.items():
                last[e] = (key.split(":", 1)[1], v)
        return last

    def job_report(self, day: date, now: datetime) -> None:
        px = dict(self.marks(day))
        stale = self._carry_marks(px, day, now)
        pos = self._book_positions(self.s.book, day)
        cash = self.j.cash(self.s.book)
        value = cash + sum((px.get(e, Decimal(0)) * q for e, q in pos.items()), Decimal(0))
        value = value.quantize(Decimal("0.01"))
        prior = [
            r
            for k, r in self.j.job_records(f"value:{self.s.book}:")
            if k.rsplit(":", 1)[1] < str(day)
        ]
        peak = max([self.s.capital_aud, *(Decimal(r["peak"]) for r in prior[-1:])])
        prev = Decimal(prior[-1]["value"]) if prior else None
        reading = evaluate_book(value, peak, prev, self.s.capital_aud, self.s.limits)
        before = prior[-1] if prior else {}
        self._l11_stage_change(reading, int(before.get("stage", 0)), value, day, now)
        self._latch_book_halts(reading, set(before.get("halts", [])), day, now)
        self.j.mark_job(
            f"value:{self.s.book}:{day}",
            {
                "value": str(value),
                "peak": str(max(peak, value)),
                "halts": list(reading.halts),
                "stage": reading.stage,
            },
            now,
        )
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
            for bid, xd in self.j.batches_of(self.s.book)
            if xd == day
            for it, st in self.j.intents_of(bid)
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
            orders_today=orders,
            safety=self.j.safety_level().value,
            flags=[
                *stale,
                *reading.alerts,
                *self._code_change_flags(),
                *self._ca_lines(day),
                *self._ca_tax_flags(),
            ],
            sim_value=sim_value,
            random_twins=self._rnd_line(day, now),
            state=self.state_line(day),
        )
        self.say(daily_report(x))

    def _carry_marks(self, px: dict[str, Decimal], day: date, now: datetime) -> list[str]:
        """A held name with no mark today (suspended, missing from the day's feed, an
        identity change) is valued at its last recorded mark, never at zero, so a data
        gap cannot fake an L11 stage; the report flags it. Marks of held names are kept
        in the journal (``marks:<day>``) for this."""
        shown = set(self.j.positions(self.s.book)) | set(self.j.positions(self.s.sim_book))
        held = shown | {e for name, *_ in self.rnd for e in self.j.positions(name)}
        flags: list[str] = []
        missing = sorted(e for e in held if e not in px)
        if missing:
            last = self._last_marks()
            for e in missing:
                if e in last:
                    px[e] = Decimal(last[e][1])
                    if e in shown:  # random twins' names are carried without a flag
                        flags.append(
                            f"WARN: no mark for {e} on {day}; valued at its last mark "
                            f"{last[e][1]} of {last[e][0]}"
                        )
                elif e in shown:
                    flags.append(f"PAGE: no mark ever recorded for held {e}; valued at zero")
        if not self.j.job_done(f"marks:{day}"):
            fresh = {e: str(px[e]) for e in sorted(held) if e in px and e not in missing}
            self.j.mark_job(f"marks:{day}", fresh, now)
        return flags

    def _latch_book_halts(
        self, reading: BookReading, before: set[str], day: date, now: datetime
    ) -> None:
        """Book monitors latch once, on the day a halt rule is first breached (nothing
        here lowers the level); the latch pages the owner at high priority. A breach that
        continues after a resume is not re-latched; a rule that clears and is breached
        again latches again. A halt never sells: holdings are kept and sells go on under
        ``HALTED_BUYS``. Inside an L11 episode (stage 2/3) buying comes back at the next
        month-end decision by the staged test (``_l11_at_decision``), otherwise only by
        the owner's ``/resume <code>``."""
        new = [h for h in reading.halts if h not in before]
        if not new:
            return
        lvl = worst(self.j.safety_level(), reading.level)
        self.j.set_safety(lvl, "book monitor: " + ",".join(new), "risk", now)
        why = "; ".join(a.removeprefix("PAGE: ") for a in reading.alerts if a.startswith("PAGE"))
        nxt = self._next_decision(day)
        if reading.stage >= 3:
            how = (
                f"Reply /continue <code> before the {nxt} decision to keep the book; "
                "without it the book is sold over that decision and the next (L11 stage 3)."
            )
        elif reading.stage == 2:
            how = (
                f"Buys resume automatically at the {nxt} decision unless (a) the integrity "
                "check fails, (b) the twin is below the 10th percentile of its random "
                "twins, (c) an L12 stop rule is met, or (d) you /stop. /resume <code> "
                "resumes now."
            )
        else:
            how = "Buying resumes only on your /resume <code>."
        self.say(
            f"PAGE HIGH PRIORITY {self.s.book}: {why}. Safety now {lvl.value}: no new buys are "
            "sent; holdings are kept and sells continue. " + how
        )

    # ------------------------------------------------------------ L11 staged loss rule
    def _next_decision(self, day: date) -> date | None:
        later = [d for d in self.sessions if d > day and self.decision_kind(d, self.s.book)]
        return later[0] if later else None

    def _integrity_breaks(self) -> tuple[str, ...]:
        """L11 stage 1 integrity check: live holdings equal the simulated twin (orders
        that did not fill and recorded decision differences explain a difference); each
        fill inside its limit and charged the modelled commission."""
        fills = []
        for f in self.j.fills(self.s.book):
            if f.client_order_id is None:
                continue
            it, _ = self.j.intent(f.client_order_id)
            mf = ModelledFill(
                f.client_order_id, f.entity, f.side, f.qty, f.price, f.commission, it.limit_price
            )
            fills.append(mf)
        return integrity_breaks(
            self.j.positions(self.s.sim_book),
            self.j.positions(self.s.book),
            self._explained(),
            fills,
            self.s.order_params.commission,
        )

    def _l11_stage_change(
        self, reading: BookReading, before: int, value: Decimal, day: date, now: datetime
    ) -> None:
        """A deeper L11 stage than the day before: run the integrity check (a failure
        latches ``HALTED_INTEGRITY``); stage 1 pages here, stages 2-3 open an episode
        (paged by the halt latch)."""
        if reading.stage <= before:
            return
        breaks = self._integrity_breaks()
        if reading.stage >= 2:
            self.j.mark_job(f"l11:breach:{day}", {"stage": reading.stage, "value": str(value)}, now)
        if breaks:
            lvl = worst(self.j.safety_level(), SafetyLevel.HALTED_INTEGRITY)
            self.j.set_safety(lvl, "L11 integrity: " + "; ".join(breaks)[:170], "l11", now)
        verdict = "FAILED: " + "; ".join(breaks) if breaks else "passed"
        if reading.stage == 1:
            self.say(
                f"PAGE HIGH PRIORITY {self.s.book}: value A${value} < "
                f"A${self.s.limits.value_review_aud} (L11 stage 1). Integrity check {verdict}."
            )
        elif breaks:
            self.say(f"PAGE HIGH PRIORITY L11 integrity check {verdict}")

    def _l11_episode(self) -> dict[str, Any] | None:
        """The open stage-2/3 episode, from the journal: since when, deepest stage,
        written confirmation, owner stop, wind-down step done."""
        ep: dict[str, Any] | None = None
        for key, rec in self.j.job_records("l11:"):
            kind = key.split(":")[1]
            if kind == "breach":
                if ep is None:
                    ep = {"since": key.rsplit(":", 1)[1], "stage": 0, "confirmed": False,
                          "stop": False, "wind": 0}  # fmt: skip
                ep["stage"] = max(ep["stage"], int(rec["stage"]))
            elif ep is None:
                continue
            elif kind == "end":
                ep = None
            elif kind == "confirm":
                ep["confirmed"] = True
            elif kind == "stop":
                ep["stop"] = True
            elif kind == "wind":
                ep["wind"] = int(rec["step"])
        return ep

    def _l11_decide(
        self,
        day: date,
        now: datetime,
        x: date,
        as_of: date,
        tv20: Mapping[str, Decimal],
        key: str,
        digest: str,
    ) -> set[tuple[str, str]] | None:
        wind = self._l11_at_decision(day, now, tv20)
        if wind is None:
            return None
        ctx = self._ctx(self.s.book, self.broker, x, day, now, False, data_as_of=as_of)
        self.ex.plan(wind, self.s.approval_mode, x, ctx)
        self.j.mark_job(key, {"digest": digest, "batch": wind.batch_id}, now)
        self.say(
            f"PAGE HIGH PRIORITY L11 wind-down {day}: {len(wind.intents)} sell(s)\n"
            + render_batch(self.j, wind.batch_id, "PAPER")
        )
        return {(i.entity, i.side.value) for i in wind.intents}

    def _l11_at_decision(
        self, day: date, now: datetime, tv20: Mapping[str, Decimal]
    ) -> OrderBatch | None:
        """The staged test at the broker book's decision. Returns a wind-down batch
        that replaces the decision, or None (the decision goes ahead; its buys are sent
        only if buying resumed)."""
        ep = self._l11_episode()
        if ep is None:
            return None
        lvl = self.j.safety_level()
        if ep["wind"] >= 1:  # step 2: the rest, then the episode closes
            self.j.mark_job(f"l11:wind:{day}", {"step": 2}, now)
            self.j.mark_job(f"l11:end:{day}", {"why": "wind-down complete"}, now)
            return self._wind_down(day, 2, tv20)
        test = StagedTest(
            integrity=self._integrity_breaks(),
            twin_percentile=self.twin_rank(day),
            l12_stop=self.l12_stop(day),
            owner_stop=bool(ep["stop"]) or lvl in (SafetyLevel.PAUSED, SafetyLevel.KILLED),
        )
        outcome, why = at_decision(int(ep["stage"]), test, bool(ep["confirmed"]))
        self.j.mark_job(f"l11:test:{day}", {"outcome": outcome.value, "why": list(why)}, now)
        if outcome is Outcome.RESUME:
            self.j.mark_job(f"l11:end:{day}", {"why": "staged test passed"}, now)
            if lvl is SafetyLevel.HALTED_BUYS:
                self.j.set_safety(SafetyLevel.NORMAL, "L11 staged test passed", "l11", now)
            self.say(
                f"L11 {day}: staged test passed (integrity, twin percentile "
                f"{test.twin_percentile}, no L12 stop, no owner stop): buys resume with this "
                f"decision. Safety {self.j.safety_level().value}."
            )
            return None
        if outcome is Outcome.STAY_PAUSED:
            self.say(
                f"PAGE HIGH PRIORITY L11 {day}: buys stay paused: "
                + "; ".join(why)
                + ". Re-tested at the next decision; /resume <code> resumes now."
            )
            return None
        self.j.mark_job(f"l11:wind:{day}", {"step": 1}, now)
        return self._wind_down(day, 1, tv20)

    def _wind_down(self, day: date, step: int, tv20: Mapping[str, Decimal]) -> OrderBatch:
        """L11 stage 3 without confirmation: sell half of each holding (rounded up) at
        this decision, the rest at the next (less sells still open, e.g. a step-1 sell
        carried under L7). Sells at the L7 band; each needs approval (L8)."""
        px = dict(self.marks(day))
        band = self.s.order_params.limit_band
        bid = batch_id_for(self.s.book, day, "W")
        pending: dict[str, int] = {}  # sells still open (a carried step-1 sell, an EMG2 sell)
        for it, st in self._all_intents(self.s.book):
            if it.side is Side.SELL and st not in TERMINAL:
                done = sum(f.qty for f in self.j.fills(coid=it.client_order_id))
                pending[it.entity] = pending.get(it.entity, 0) + it.qty - done
        out: list[OrderIntent] = []
        for e, q in sorted(self._book_positions(self.s.book, day).items()):
            qty = wind_down_qty(q - pending.get(e, 0), step)
            ref = px.get(e)
            if qty <= 0 or ref is None or ref <= 0:
                continue
            it = OrderIntent(
                client_order_id(self.s.book, day, e, Side.SELL), bid, len(out) + 1,
                self.s.line, self.s.book, day, e, Side.SELL, qty,
                self.s.order_params.order_type, ref,
                round_to_step(ref * (1 - band), Side.SELL), f"L11_WIND_DOWN_{step}",
                tv_med20=tv20.get(e), prev_close=ref, flags=("L11_WIND_DOWN",),
            )  # fmt: skip
            out.append(it)
        return OrderBatch(
            bid, self.s.book, day, tuple(out), (), sha256_json([i.client_order_id for i in out])
        )

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
        stands in for the exchange's closing auction at 16:10. A job that is not done
        (data not in) runs once more at ``RETRY_UNTIL``."""
        for hhmm, name in DAY_JOBS:
            now = at(day, hhmm)
            if name in OWNER_TICKS and owner is not None:
                for k, text in enumerate(owner(day, hhmm)):
                    t = now + timedelta(seconds=31 * k)
                    self.transport_inject(Incoming(next(iter(self.s.chats)), text, t))
            if name == "collect" and auction is not None:
                auction(day)
            if name == "decide":
                self.now = now
                if not self.job_decide(day, now, decision):
                    self.now = at(day, RETRY_UNTIL)
                    self.job_decide(day, self.now, decision)
                continue
            if not self.run_job(name, day, now):
                self.run_job(name, day, at(day, RETRY_UNTIL))

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
    def auction(self, closes: dict[str, float], when: datetime | None = None) -> int: ...


def mock_auction(gateway: _Auctioneer, closes: CloseProvider) -> Callable[[date], None]:
    """The exchange's closing auction, played by the mock gateway at the day's closes."""

    def run(day: date) -> None:
        gateway.auction({e: float(c) for e, c in closes(day).items()}, at(day, "16:12"))

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
    recon: dict[str, bool] = field(default_factory=dict)  # session -> reconciled to the cent
    l13_notes: dict[str, list[str]] = field(default_factory=dict)  # decision -> names


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
        recon={
            k.rsplit(":", 1)[1]: bool(r["ok"]) for k, r in app.j.job_records(f"recon:{app.s.book}:")
        },
        l13_notes={k.split(":", 1)[1]: list(r["diff"]) for k, r in app.j.job_records("l13:")},
    )
