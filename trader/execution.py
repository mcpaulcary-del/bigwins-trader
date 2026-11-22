"""Execution: plan -> breaker -> approval -> persist -> send -> fills (FD §11; BF3).

Invariants (tested with crash injection):

* an intent is in the journal before it is checked, approved or sent;
* it is persisted as ``SENDING`` **before** ``Broker.place`` (persist-before-send);
* a timeout is never followed by a resend: the intent becomes ``NEEDS_REVIEW`` and
  ``recover()`` adopts the broker's order if one carries its ``orderRef``;
* so there is at most one broker order per intent, whatever crashes where;
* no intent is sent without an approval valid at the deadline (per-order or batch
  mode), and the breaker runs again at send time;
* ``kill()`` latches ``KILLED`` and cancels every open order of the book;
* the broker's quote just before each send is journalled (``bf_order_quotes``,
  BF-D22); a missing or failed quote never blocks the order.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from trader.approval import approved_seqs, deadline
from trader.broker.base import (
    Broker,
    BrokerRejectedError,
    BrokerTimeoutError,
    OrderRequest,
)
from trader.journal import FillRecord, Journal, JournalError, Status
from trader.orders import OrderBatch, Side
from trader.risk import (
    Quote,
    RiskContext,
    RiskLimits,
    SafetyLevel,
    Verdict,
    check_intents,
    worst,
)

CrashHook = Callable[[str, str], None]  # (point, client_order_id); tests raise to simulate a crash


def _no_crash(point: str, coid: str) -> None:
    return None


@dataclass
class SendReport:
    sent: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)
    not_approved: list[str] = field(default_factory=list)
    review: list[str] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)


@dataclass
class Executor:
    journal: Journal
    broker: Broker
    book: str
    limits: RiskLimits = field(default_factory=RiskLimits)
    crash: CrashHook = _no_crash
    approval_deadline: str = "15:20"
    plan_pages: list[str] = field(default_factory=list)  # pages of the last plan() (BF-D3)
    # Which safety latch this book obeys and writes: "" = the broker book's (owner
    # /pause, /kill, L11, integrity); the simulated twin uses its own (BF-D16)
    safety_scope: str = ""
    _booked: set[str] = field(default_factory=set, repr=False)  # exec ids booked (cache)

    # ------------------------------------------------------------ plan time
    def plan(
        self, batch: OrderBatch, approval_mode: str, execution_date: object, ctx: RiskContext
    ) -> list[tuple[str, Verdict, tuple[str, ...]]]:
        """Persist the batch (PLANNED) and run the breaker at plan time."""
        if approval_mode not in ("per_order", "batch", "auto"):
            raise ValueError(f"unknown approval mode {approval_mode}")
        self.journal.add_batch(batch, approval_mode, execution_date)  # type: ignore[arg-type]
        rep = check_intents(batch.intents, ctx, self.limits)
        self.plan_pages = list(rep.pages)
        out = []
        for r in rep.results:
            coid = r.intent.client_order_id
            _, st = self.journal.intent(coid)
            if st != Status.PLANNED:
                continue  # idempotent re-plan
            if r.verdict in (Verdict.PASS, Verdict.CLIP):
                self.journal.set_status(
                    coid, Status.RISK_OK, {"reasons": list(r.reasons)}, qty=r.intent.qty
                )
            elif r.verdict is Verdict.HOLD or (
                r.intent.side is Side.BUY and "CASH_SHORT" in r.reasons
            ):  # L7: a buy waits for settled funds (or a gap) instead of failing
                self.journal.set_status(coid, Status.HELD, {"reasons": list(r.reasons)})
            else:
                self.journal.set_status(coid, Status.RISK_REJECTED, {"reasons": list(r.reasons)})
            out.append((coid, r.verdict, r.reasons))
        if rep.latch is not None:
            lvl = worst(self.journal.safety_level(self.safety_scope), rep.latch)
            self.journal.set_safety(lvl, "breaker latch", "risk", scope=self.safety_scope)
        return out

    # ------------------------------------------------------------ send time
    def submit(  # noqa: PLR0912 - one branch per send case
        self, batch_id: str, ctx: RiskContext, now: datetime, *, final_day: bool = True
    ) -> SendReport:
        """Send every approved, risk-OK intent of the batch once.

        Held intents (``GAP_HOLD``, or a buy short of settled cash while the day's sells
        settle: L7 / BW-EXE-05 / O-2) are retried on later sessions; on the batch's
        ``final_day`` anything still not sendable is rejected for good."""
        rep = SendReport()
        b = self.journal.batch(batch_id)
        if b is None:
            raise ValueError(f"unknown batch {batch_id}")
        level = self.journal.safety_level(self.safety_scope)
        ctx = RiskContext(**{**ctx.__dict__, "safety": worst(level, ctx.safety)})
        cut = deadline(b["execution_date"], self.approval_deadline) if b["execution_date"] else None
        ok = approved_seqs(self.journal, batch_id, cut)
        pending = [
            (it, st)
            for it, st in self.journal.intents_of(batch_id)
            if st in (Status.RISK_OK, Status.APPROVED, Status.HELD)
        ]
        xd = b["execution_date"]
        if xd is not None and xd < ctx.session:  # review H5: an approval is for its day only
            rest = []
            for it, st in pending:
                if st == Status.HELD:
                    rest.append((it, st))  # L7: a buy held for funds (or a gap) rolls
                    continue
                self.journal.set_status(
                    it.client_order_id, Status.LAPSED,
                    {"why": f"approved for {xd}, not sent that day; not carried"}, now,
                )  # fmt: skip
                rep.not_approved.append(it.client_order_id)
            pending = rest
        for it, st in pending:
            if it.seq not in ok:
                rep.not_approved.append(it.client_order_id)
                if cut is not None and now >= cut:
                    self.journal.set_status(
                        it.client_order_id, Status.LAPSED, {"why": "no approval"}, now
                    )
                continue
            if st == Status.HELD:
                self.journal.set_status(it.client_order_id, Status.RISK_OK, {"retry": True}, now)
            if st in (Status.HELD, Status.RISK_OK):
                self.journal.set_status(it.client_order_id, Status.APPROVED, at=now)
        to_send = [it for it, st in self.journal.intents_of(batch_id) if st == Status.APPROVED]
        quotes = (
            {it.entity: self._quote(it) for it in to_send}
            if getattr(self.broker, "quotes_for_breaker", True)
            else {}
        )
        live = {e: q for e, (q, _) in quotes.items() if q is not None}
        if live:  # review M3: the breaker's gap / stale / sanity checks see the real quote
            ctx = RiskContext(**{**ctx.__dict__, "quotes": {**ctx.quotes, **live}})
        risk = check_intents(to_send, ctx, self.limits)  # send-time breaker
        rep.pages.extend(risk.pages)
        if risk.latch is not None:
            self.journal.set_safety(
                worst(level, risk.latch), "breaker latch at send", "risk", now, self.safety_scope
            )
        for r in risk.results:
            coid = r.intent.client_order_id
            if not r.sendable:
                wait = r.verdict is Verdict.HOLD or (
                    r.intent.side is Side.BUY and "CASH_SHORT" in r.reasons
                )
                to = Status.HELD if wait and not final_day else Status.RISK_REJECTED
                self.journal.set_status(coid, to, {"reasons": list(r.reasons)}, now)
                rep.rejected.append((coid, ",".join(r.reasons)))
                continue
            self._send_one(r.intent, now, rep, quotes.get(r.intent.entity, (None, None))[1])
        return rep

    def _quote(self, it: object) -> tuple[Quote | None, object]:
        """The broker's quote before the send (review M3): the breaker's ``Quote`` (last
        and the decision's close, or the quote's close) and the raw quote (BF-D22)."""
        from trader.orders import OrderIntent

        assert isinstance(it, OrderIntent)
        try:
            q = self.broker.quote(it.entity)
        except Exception as e:  # the quote never blocks the order by failing
            return None, e
        if q is None or q.last is None or q.last <= 0:
            return None, q
        prev = it.prev_close if it.prev_close and it.prev_close > 0 else q.close
        if prev is None or prev <= 0:
            return None, q
        return Quote(q.last, prev, q.time), q

    def _send_one(self, it: object, now: datetime, rep: SendReport, raw: object = None) -> None:
        from trader.orders import OrderIntent

        assert isinstance(it, OrderIntent)
        coid = it.client_order_id
        self._record_quote(it, now, raw)
        self.journal.set_status(coid, Status.SENDING, {"qty": it.qty}, now, qty=it.qty)
        self.crash("after_persist", coid)
        req = OrderRequest(
            coid, self.broker.account_id, it.entity, it.side, it.qty, it.order_type, it.limit_price
        )
        try:
            st = self.broker.place(req)
        except BrokerTimeoutError as e:
            self.journal.set_status(coid, Status.NEEDS_REVIEW, {"error": str(e)}, now)
            rep.review.append(coid)
            rep.pages.append(f"{coid}: no broker acknowledgement; NOT resent; review")
            return
        except BrokerRejectedError as e:
            self.journal.set_status(coid, Status.REJECTED, {"error": str(e)}, now)
            rep.rejected.append((coid, str(e)))
            return
        self.crash("after_send", coid)
        self.journal.record_broker_order(
            coid, self.broker.account_id, st.broker_order_id, st.perm_id, st.status, now
        )
        self.journal.set_status(coid, Status.SENT, {"perm_id": st.perm_id}, now)
        rep.sent.append(coid)

    def _record_quote(self, it: object, now: datetime, raw: object = None) -> None:
        """Keep the broker's quote (bid, ask, mid) at the moment of the order (BF-D22).

        A quote that is missing or fails is recorded as such and never blocks the order."""
        from trader.broker.base import BrokerQuote
        from trader.orders import OrderIntent

        assert isinstance(it, OrderIntent)
        note = ""
        q: BrokerQuote | None
        if isinstance(raw, BrokerQuote):
            q = raw
        elif isinstance(raw, Exception):
            q, note = None, f"quote failed: {type(raw).__name__}: {raw}"
        else:
            try:
                q = self.broker.quote(it.entity)
            except Exception as e:  # the quote is information only: never block the order
                q, note = None, f"quote failed: {type(e).__name__}: {e}"
        if q is None:
            self.journal.record_order_quote(
                it, None, None, None, None, type(self.broker).__name__, note or "no quote", now
            )
            return
        self.journal.record_order_quote(
            it, q.bid, q.ask, q.last, q.time, type(self.broker).__name__, note, now
        )

    # ------------------------------------------------------------ after a crash or restart
    def recover(self, now: datetime) -> list[str]:
        """Adopt broker orders of intents left in SENDING / NEEDS_REVIEW. Never resends."""
        pages = []
        for it, st in self.journal.intents_in([Status.SENDING, Status.NEEDS_REVIEW]):
            if it.book != self.book:
                continue
            found = self.broker.find_order(it.client_order_id)
            if found is None:
                if st == Status.SENDING:
                    self.journal.set_status(
                        it.client_order_id,
                        Status.NEEDS_REVIEW,
                        {"why": "no broker order after restart; not resent"},
                        now,
                    )
                pages.append(f"{it.client_order_id}: no broker order found; not resent")
                continue
            self.journal.record_broker_order(
                it.client_order_id,
                self.broker.account_id,
                found.broker_order_id,
                found.perm_id,
                found.status,
                now,
            )
            self.journal.set_status(
                it.client_order_id, Status.SENT, {"adopted": found.perm_id}, now
            )
        return pages

    # ------------------------------------------------------------ fills
    def collect_fills(self, now: datetime, session_closed: bool = False) -> int:
        """Book broker executions once each; settle statuses; expire unfilled DAY orders."""
        from trader.broker.base import exec_base

        new = 0
        bases = self.journal.fill_bases()
        for ex in self.broker.executions():
            if ex.client_order_id is None:
                continue  # a foreign order (BP-02): reported by reconciliation, never booked here
            booked = bases.get(exec_base(ex.exec_id))
            if booked is not None:  # review L6: a correction (or a late commission report)
                if ex.commission > 0:
                    self.journal.correct_fill_commission(booked, ex.commission, "broker")
                continue
            if ex.exec_id in self._booked:
                continue  # booked by this process already (add_fill is idempotent anyway)
            try:
                it, _ = self.journal.intent(ex.client_order_id)
            except JournalError:
                continue
            if self.journal.add_fill(
                FillRecord(
                    ex.exec_id,
                    ex.client_order_id,
                    it.book,
                    ex.symbol,
                    ex.side,
                    ex.qty,
                    ex.price,
                    ex.commission,
                    ex.time,
                )
            ):
                new += 1
            self._booked.add(ex.exec_id)
        self.settle_statuses(now, session_closed)
        return new

    def settle_statuses(self, now: datetime, session_closed: bool = False) -> None:
        """SENT / PARTIAL intents to FILLED or PARTIAL by their booked fills; after the
        close, an order the broker no longer has is EXPIRED (review M6: also run after
        Flex trades are booked)."""
        for it, st in self.journal.intents_in([Status.SENT, Status.PARTIAL], self.book):
            done = sum(f.qty for f in self.journal.fills(coid=it.client_order_id))
            if done >= it.qty:
                self.journal.set_status(it.client_order_id, Status.FILLED, {"filled": done}, now)
            elif done > 0 and st == Status.SENT:
                self.journal.set_status(it.client_order_id, Status.PARTIAL, {"filled": done}, now)
            if session_closed and done < it.qty:
                bo = self.broker.find_order(it.client_order_id)
                if bo is None or bo.status in ("Cancelled", "ApiCancelled", "Inactive"):
                    self.journal.set_status(
                        it.client_order_id, Status.EXPIRED, {"filled": done}, now
                    )

    # ------------------------------------------------------------ kill switch
    def kill(self, now: datetime, actor: str = "owner") -> int:
        """/kill: latch KILLED and cancel every open order this book sent (BW-RSK-30)."""
        self.journal.set_safety(SafetyLevel.KILLED, "kill", actor, now, self.safety_scope)
        n = 0
        for o in self.broker.open_orders():
            try:
                it, _ = self.journal.intent(o.client_order_id)
            except JournalError:
                continue
            if it.book == self.book and self.broker.cancel(o.client_order_id):
                n += 1
        return n


def side_sign(side: Side) -> int:
    return 1 if side is Side.BUY else -1


def book_value(positions: dict[str, int], prices: dict[str, Decimal], cash: Decimal) -> Decimal:
    return cash + sum((prices.get(e, Decimal(0)) * q for e, q in positions.items()), Decimal(0))
