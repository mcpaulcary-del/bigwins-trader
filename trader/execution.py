"""Execution: plan -> breaker -> approval -> persist -> send -> fills (FD §11; BF3).

Invariants (tested with crash injection):

* an intent is in the journal before it is checked, approved or sent;
* it is persisted as ``SENDING`` **before** ``Broker.place`` (persist-before-send);
* a timeout is never followed by a resend: the intent becomes ``NEEDS_REVIEW`` and
  ``recover()`` adopts the broker's order if one carries its ``orderRef``;
* so there is at most one broker order per intent, whatever crashes where;
* no intent is sent without an approval valid at the deadline (per-order or batch
  mode), and the breaker runs again at send time;
* ``kill()`` latches ``KILLED`` and cancels every open order of the book.
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
from trader.risk import RiskContext, RiskLimits, SafetyLevel, Verdict, check_intents, worst

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

    # ------------------------------------------------------------ plan time
    def plan(
        self, batch: OrderBatch, approval_mode: str, execution_date: object, ctx: RiskContext
    ) -> list[tuple[str, Verdict, tuple[str, ...]]]:
        """Persist the batch (PLANNED) and run the breaker at plan time."""
        if approval_mode not in ("per_order", "batch", "auto"):
            raise ValueError(f"unknown approval mode {approval_mode}")
        self.journal.add_batch(batch, approval_mode, execution_date)  # type: ignore[arg-type]
        rep = check_intents(batch.intents, ctx, self.limits)
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
            self.journal.set_safety(
                worst(self.journal.safety_level(), rep.latch), "breaker latch", "risk"
            )
        return out

    # ------------------------------------------------------------ send time
    def submit(
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
        level = self.journal.safety_level()
        ctx = RiskContext(**{**ctx.__dict__, "safety": worst(level, ctx.safety)})
        cut = deadline(b["execution_date"], self.approval_deadline) if b["execution_date"] else None
        ok = approved_seqs(self.journal, batch_id, cut)
        pending = [
            (it, st)
            for it, st in self.journal.intents_of(batch_id)
            if st in (Status.RISK_OK, Status.APPROVED, Status.HELD)
        ]
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
        risk = check_intents(to_send, ctx, self.limits)  # send-time breaker
        rep.pages.extend(risk.pages)
        if risk.latch is not None:
            self.journal.set_safety(worst(level, risk.latch), "breaker latch at send", "risk", now)
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
            self._send_one(r.intent, now, rep)
        return rep

    def _send_one(self, it: object, now: datetime, rep: SendReport) -> None:
        from trader.orders import OrderIntent

        assert isinstance(it, OrderIntent)
        coid = it.client_order_id
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
        new = 0
        for ex in self.broker.executions():
            if ex.client_order_id is None:
                continue  # a foreign order (BP-02): reported by reconciliation, never booked here
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
        for it, st in self.journal.intents_in([Status.SENT, Status.PARTIAL]):
            if it.book != self.book:
                continue
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
        return new

    # ------------------------------------------------------------ kill switch
    def kill(self, now: datetime, actor: str = "owner") -> int:
        """/kill: latch KILLED and cancel every open order this book sent (BW-RSK-30)."""
        self.journal.set_safety(SafetyLevel.KILLED, "kill", actor, now)
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
