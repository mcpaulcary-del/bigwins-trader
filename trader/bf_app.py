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
from decimal import Decimal
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
from trader.broker.base import Broker
from trader.broker.paper_sim import SimBroker
from trader.canonical import sha256_json
from trader.constants import ASX_TZ
from trader.execution import Executor
from trader.journal import TERMINAL, Journal, Status
from trader.lines.emg2 import BookState, BuyPlan, Emg2_20Decision, Emg2_20Params, decide_emg2_20
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
from trader.reconcile import compare_books
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
from trader.universe import liquidity_table

PanelProvider = Callable[[date], PricePanel]
CloseProvider = Callable[[date], Mapping[str, Decimal]]

DAY_JOBS: tuple[tuple[str, str], ...] = (
    ("10:30", "tick"),
    ("12:30", "tick"),
    ("14:30", "remind"),
    ("15:20", "tick"),
    ("15:45", "submit"),
    ("16:20", "collect"),
    ("16:30", "reconcile"),
    ("22:15", "sim"),
    ("22:20", "decide"),
    ("22:45", "report"),
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
    ) -> None:
        """``closes(d)``: the closes of session d (empty while the day's data is not in);
        ``marks(d)``: the last known close of every name at d (valuation; defaults to
        the panel's last valid close of each name)."""
        self.s = s
        self.j = journal
        self.broker = broker
        self.sim = sim
        self.transport = transport
        self.sessions = sorted(sessions)
        self.panels = panels
        self.closes = closes
        self.marks = marks or marks_from_panels(panels)
        self.now = datetime.now(UTC)
        self.ex = Executor(
            journal, broker, s.book, limits=s.limits, approval_deadline=s.approval_deadline
        )
        self.ex_sim = Executor(journal, sim, s.sim_book, limits=s.limits, approval_deadline="23:59")
        self.bot = ApprovalBot(journal, transport, verifier, s.chats, on_kill=self._kill)
        self.log: list[str] = []

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

    def _all_intents(self, book: str) -> list[tuple[OrderIntent, str]]:
        return [x for bid, _ in self.j.batches_of(book) for x in self.j.intents_of(bid)]

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
        if not any(kinds.values()):
            return True
        panel = self.panels(day)
        liq = liquidity_table(panel)
        tv20 = {
            e: Decimal(repr(float(liq.tv_med20[j]))).quantize(Decimal(1))
            for j, e in enumerate(panel.entities)
            if liq.tv_med20[j] == liq.tv_med20[j]
        }
        x = self.next_session(day)
        acted: dict[str, set[tuple[str, str]]] = {}
        for book, ex, broker, mode in self._books():
            k = kinds[book]
            key = f"decide:{book}:{day}"
            if k is None or self.j.job_done(key):
                continue
            dec = None
            block = None if data_ready(panel) else "the day's closes are missing"
            if block is None:
                state = BookState(book, self.j.cash(book), self.j.positions(book))
                dec = decide_emg2_20(panel, state, self.s.params)
                block = dec.data_block
            if block is not None or dec is None:
                if now < at(day, RETRY_UNTIL):
                    return False  # the day's data may still arrive: retried
                self._data_block(book, key, day, now, block or "no decision")
                continue
            canary = k == "S" and book == self.s.book
            batch = build_orders(
                dec,
                line=self.s.line,
                params=self.s.order_params,
                kind=k,
                canary=canary,
                tv_med20=tv20,
            )
            ctx = self._ctx(book, broker, x, day, now, k == "S", data_as_of=panel.as_of)
            ex.plan(batch, mode, x, ctx)
            acted[book] = {(i.entity, i.side.value) for i in batch.intents}
            if canary:  # the other start buys follow the canary: count the whole list
                acted[book] |= {(b.entity, Side.BUY.value) for b in dec.buys}
                self.j.mark_job(f"start:{book}:{day}", _decision_record(dec, tv20), now)
            self.j.mark_job(key, {"digest": dec.digest, "batch": batch.batch_id}, now)
            if book == self.s.book:
                head = f"Decision {day} ({'start, canary first' if canary else 'regular'}); "
                head += f"list {dec.list_digest[:12]}; {len(batch.intents)} order(s)"
                if self.s.lic_note:
                    head += "\n" + self.s.lic_note
                lvl = self.j.safety_level()
                if lvl in BLOCKS_BUYS:
                    head += f"\nSafety {lvl.value}: the buys below are not sent unless you " + (
                        "/resume <code> before they go; sells proceed"
                        if lvl not in BLOCKS_ALL
                        else "re-arm; sells wait for the re-arm too"
                    )
                self.say(head + "\n" + render_batch(self.j, batch.batch_id, "PAPER"))
                for p in ex.plan_pages:  # BF-D3: a sell above A$800 goes through, paged
                    self.say("PAGE " + p)
        if acted:
            self._note_decision_difference(day, now, acted)
        return True

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
        closes = self.closes(day)
        band = self.s.order_params.limit_band
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
            ref = closes.get(it.entity) or it.ref_price
            if sell:
                lim, qty = round_to_step(ref * (1 - band), Side.SELL), rest
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
                        book, it.decision_date, it.entity, it.side, it.attempt + 1
                    ),
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

    def job_reconcile(self, day: date, now: datetime) -> None:
        r = reconcile_and_page(self.j, self.broker, self.s.book, self.transport, self.s.chats, now)
        if not r.ok:
            self.log.append("RECON BREAK " + "; ".join(r.breaks))
        self._start_followup(day, now, r.ok)

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
        self.sim.advance(day, closes)
        self.ex_sim.collect_fills(now, session_closed=True)
        self._carry(self.s.sim_book, self.ex_sim, self.sim, "auto", day, now)
        r = compare_books(
            self.j.positions(self.s.sim_book), self.j.positions(self.s.book), self._explained()
        )
        if not r.ok:
            lvl = worst(self.j.safety_level(), SafetyLevel.HALTED_INTEGRITY)
            self.j.set_safety(lvl, "L13: " + "; ".join(r.breaks)[:180], "l13", now)
            self.say(
                "PAGE L13 sim/broker holdings differ without an explanation:\n"
                + "\n".join(r.breaks)
            )
        return True

    def _explained(self) -> set[str]:
        """L13: names whose holdings difference an order explains: an order of either
        book that did not fill (unapproved, vetoed, held, expired, rejected, pending),
        or a name on which the two books' decisions differed (recorded at decide)."""
        out = {
            it.entity
            for book in (self.s.book, self.s.sim_book)
            for it, st in self._all_intents(book)
            if st != Status.FILLED
        }
        for _, rec in self.j.job_records("l13:"):
            out.update(rec.get("diff", []))
        planned = {k.split(":", 1)[1] for k, r in self.j.job_records("start-done:") if "batch" in r}
        for key, rec in self.j.job_records(f"start:{self.s.book}:"):
            if key.split(":", 1)[1] not in planned:  # L6: the other start buys wait for the
                out.update(str(b[0]) for b in rec["buys"])  # canary (or the start stopped)
        return out

    def job_report(self, day: date, now: datetime) -> None:
        px = dict(self.marks(day))
        pos = self.j.positions(self.s.book)
        cash = self.j.cash(self.s.book)
        value = cash + sum((px.get(e, Decimal(0)) * q for e, q in pos.items()), Decimal(0))
        prior = [
            r
            for k, r in self.j.job_records(f"value:{self.s.book}:")
            if k.rsplit(":", 1)[1] < str(day)
        ]
        peak = max([self.s.capital_aud, *(Decimal(r["peak"]) for r in prior[-1:])])
        prev = Decimal(prior[-1]["value"]) if prior else None
        reading = evaluate_book(value, peak, prev, self.s.capital_aud, self.s.limits)
        self._latch_book_halts(reading, set(prior[-1].get("halts", [])) if prior else set(), now)
        self.j.mark_job(
            f"value:{self.s.book}:{day}",
            {"value": str(value), "peak": str(max(peak, value)), "halts": list(reading.halts)},
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
            flags=list(reading.alerts),
            sim_value=sim_value,
        )
        self.say(daily_report(x))

    def _latch_book_halts(self, reading: BookReading, before: set[str], now: datetime) -> None:
        """L11 / owner loss rule: a halt rule latches once, on the day it is first breached
        (it stays latched; nothing here lowers the level). The latch pages the owner at
        high priority. A breach that continues after the owner's ``/resume`` is not
        re-latched: resuming is the owner's decision. A rule that clears and is breached
        again latches again. A halt never sells: holdings are kept and the registered
        sells go on under ``HALTED_BUYS``."""
        new = [h for h in reading.halts if h not in before]
        if not new:
            return
        lvl = worst(self.j.safety_level(), reading.level)
        self.j.set_safety(lvl, "book monitor: " + ",".join(new), "risk", now)
        why = "; ".join(a.removeprefix("PAGE: ") for a in reading.alerts if a.startswith("PAGE"))
        self.say(
            f"PAGE HIGH PRIORITY {self.s.book}: {why}. Safety now {lvl.value}: no new buys are "
            "sent; holdings are kept and the registered EMG2 sells continue"
            + (" (HALTED_LINE: sells stop too)" if lvl is SafetyLevel.HALTED_LINE else "")
            + ". Buying resumes only on your /resume <code>."
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
