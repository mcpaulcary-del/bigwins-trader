"""B-fast order journal: intents, batches, approvals, broker orders, fills, safety state.

SQLAlchemy Core on its own ``MetaData`` (tables ``bf_*``), so it runs on SQLite in
tests and on the PostgreSQL 16 ledger database in the container. Moving these
tables into the v3.0 ledger schema (Alembic, grants, mutability guard) is B4 work
(``NEXT.md``).

Rules (BW-EXE-06, CA-01 carried):

* an intent is inserted with status ``PLANNED`` before anything else happens, and
  persisted as ``SENDING`` **before** any broker call (persist-before-send);
* status changes only along ``TRANSITIONS``; every change appends a ``bf_events``
  row (append-only audit); rows are never deleted;
* approvals, vetoes and safety-level changes are append-only rows; the current
  safety level is the latest ``bf_safety`` row.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Engine,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    func,
    insert,
    select,
    update,
)

from trader.canonical import canonical_json
from trader.orders import OrderBatch, OrderIntent, OrderType, Side
from trader.risk import SafetyLevel

md = MetaData()

intents = Table(
    "bf_intents",
    md,
    Column("client_order_id", String(96), primary_key=True),
    Column("batch_id", String(80), nullable=False, index=True),
    Column("seq", Integer, nullable=False),
    Column("line", String(32), nullable=False),
    Column("book", String(48), nullable=False),
    Column("decision_date", Date, nullable=False),
    Column("entity", String(24), nullable=False),
    Column("side", String(4), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("order_type", String(8), nullable=False),
    Column("ref_price", Numeric(18, 4), nullable=False),
    Column("limit_price", Numeric(18, 4), nullable=False),
    Column("reason", String(48), nullable=False),
    Column("attempt", Integer, nullable=False),
    Column("status", String(24), nullable=False),
    Column("tv_med20", Numeric(20, 2)),
    Column("prev_close", Numeric(18, 4)),
    Column("flags", JSON, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

batches = Table(
    "bf_batches",
    md,
    Column("batch_id", String(80), primary_key=True),
    Column("book", String(48), nullable=False),
    Column("decision_date", Date, nullable=False),
    Column("digest", String(64), nullable=False),
    Column("approval_mode", String(16), nullable=False),  # per_order | batch | auto
    Column("execution_date", Date),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)

approvals = Table(
    "bf_approvals",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("batch_id", String(80), nullable=False, index=True),
    Column("seq", Integer),  # NULL = whole batch
    Column("action", String(8), nullable=False),  # OK | VETO | REFUSE
    Column("actor", String(64), nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
)

broker_orders = Table(
    "bf_broker_orders",
    md,
    Column("client_order_id", String(96), primary_key=True),
    Column("broker_order_id", String(32)),
    Column("perm_id", String(32)),
    Column("account", String(16), nullable=False),
    Column("status", String(24), nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
)

fills = Table(
    "bf_fills",
    md,
    Column("exec_id", String(64), primary_key=True),
    Column("client_order_id", String(96), index=True),
    Column("book", String(48), nullable=False),
    Column("entity", String(24), nullable=False),
    Column("side", String(4), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("price", Numeric(18, 4), nullable=False),
    Column("commission", Numeric(18, 4), nullable=False),
    Column("executed_at", DateTime(timezone=True), nullable=False),
)

cash_moves = Table(
    "bf_cash",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("book", String(48), nullable=False),
    Column("kind", String(16), nullable=False),  # DEPOSIT | DIVIDEND | ADJUST
    Column("amount", Numeric(18, 4), nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
    Column("note", String(200), nullable=False),
)

safety = Table(
    "bf_safety",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("level", String(24), nullable=False),
    Column("reason", String(200), nullable=False),
    Column("actor", String(64), nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
    # "" = the broker book and the owner's commands; a book name = that book's own latch
    # (the simulated twin: it follows the registered rules only, BF-D16)
    Column("scope", String(40), nullable=False, server_default=""),
)

events = Table(
    "bf_events",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("at", DateTime(timezone=True), nullable=False),
    Column("kind", String(24), nullable=False),
    Column("ref", String(96), nullable=False),
    Column("from_status", String(24)),
    Column("to_status", String(24)),
    Column("detail", JSON, nullable=False),
)


class Status:
    PLANNED = "PLANNED"
    RISK_OK = "RISK_OK"
    RISK_REJECTED = "RISK_REJECTED"
    HELD = "HELD"
    APPROVED = "APPROVED"
    VETOED = "VETOED"
    LAPSED = "LAPSED_NO_APPROVAL"
    SENDING = "SENDING"
    SENT = "SENT"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


TERMINAL = frozenset(
    {
        Status.RISK_REJECTED,
        Status.VETOED,
        Status.LAPSED,
        Status.FILLED,
        Status.EXPIRED,
        Status.CANCELLED,
        Status.REJECTED,
    }
)
TRANSITIONS: Mapping[str, frozenset[str]] = {
    Status.PLANNED: frozenset({Status.RISK_OK, Status.RISK_REJECTED, Status.HELD}),
    Status.HELD: frozenset({Status.RISK_OK, Status.RISK_REJECTED, Status.LAPSED}),
    Status.RISK_OK: frozenset(
        {Status.APPROVED, Status.VETOED, Status.LAPSED, Status.RISK_REJECTED, Status.HELD}
    ),
    Status.APPROVED: frozenset({Status.SENDING, Status.RISK_REJECTED, Status.LAPSED, Status.HELD}),
    Status.SENDING: frozenset({Status.SENT, Status.REJECTED, Status.NEEDS_REVIEW}),
    Status.SENT: frozenset(
        {
            Status.PARTIAL,
            Status.FILLED,
            Status.EXPIRED,
            Status.CANCELLED,
            Status.REJECTED,
            Status.NEEDS_REVIEW,
        }
    ),
    Status.PARTIAL: frozenset(
        {Status.PARTIAL, Status.FILLED, Status.EXPIRED, Status.CANCELLED, Status.NEEDS_REVIEW}
    ),
    Status.NEEDS_REVIEW: frozenset(
        {
            Status.SENT,
            Status.FILLED,
            Status.PARTIAL,
            Status.CANCELLED,
            Status.EXPIRED,
            Status.REJECTED,
        }
    ),
}


class JournalError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class FillRecord:
    exec_id: str
    client_order_id: str | None
    book: str
    entity: str
    side: Side
    qty: int
    price: Decimal
    commission: Decimal
    executed_at: datetime


class Journal:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        md.create_all(engine)

    @classmethod
    def sqlite(cls, path: str = ":memory:") -> Journal:
        return cls(create_engine(f"sqlite+pysqlite:///{path}"))

    # ------------------------------------------------------------ events
    def _event(
        self,
        conn: Any,
        kind: str,
        ref: str,
        frm: str | None,
        to: str | None,
        detail: Mapping[str, Any] | None = None,
        at: datetime | None = None,
    ) -> None:
        conn.execute(
            insert(events).values(
                at=(at or utcnow()).astimezone(UTC),  # UTC: SQLite drops the zone
                kind=kind,
                ref=ref,
                from_status=frm,
                to_status=to,
                detail=dict(detail or {}),
            )
        )

    def events(self, ref: str | None = None) -> list[dict[str, Any]]:
        q = select(events).order_by(events.c.id)
        if ref is not None:
            q = q.where(events.c.ref == ref)
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(q)]

    # ------------------------------------------------------------ batches and intents
    def add_batch(
        self,
        batch: OrderBatch,
        approval_mode: str,
        execution_date: date | None,
        at: datetime | None = None,
    ) -> None:
        """Insert a batch and its intents as PLANNED (idempotent on batch id + digest)."""
        now = at or utcnow()
        with self.engine.begin() as c:
            old = c.execute(
                select(batches.c.digest).where(batches.c.batch_id == batch.batch_id)
            ).first()
            if old is not None:
                if old[0] != batch.digest:
                    raise JournalError(f"batch {batch.batch_id} exists with another digest")
                return
            c.execute(
                insert(batches).values(
                    batch_id=batch.batch_id,
                    book=batch.book,
                    decision_date=batch.decision_date,
                    digest=batch.digest,
                    approval_mode=approval_mode,
                    execution_date=execution_date,
                    created_at=now,
                    payload={"skipped": [list(s) for s in batch.skipped]},
                )
            )
            for it in batch.intents:
                c.execute(
                    insert(intents).values(**_intent_row(it), status=Status.PLANNED, created_at=now)
                )
                self._event(c, "intent", it.client_order_id, None, Status.PLANNED, at=now)
            self._event(c, "batch", batch.batch_id, None, "CREATED", {"digest": batch.digest}, now)

    def batch(self, batch_id: str) -> dict[str, Any] | None:
        with self.engine.connect() as c:
            r = c.execute(select(batches).where(batches.c.batch_id == batch_id)).first()
            return dict(r._mapping) if r else None

    def batches_for(self, execution_date: date) -> list[str]:
        with self.engine.connect() as c:
            q = select(batches.c.batch_id).where(batches.c.execution_date == execution_date)
            return [r[0] for r in c.execute(q.order_by(batches.c.batch_id))]

    def batches_of(self, book: str) -> list[tuple[str, date | None]]:
        with self.engine.connect() as c:
            q = select(batches.c.batch_id, batches.c.execution_date).where(batches.c.book == book)
            return [(r[0], r[1]) for r in c.execute(q.order_by(batches.c.batch_id))]

    def job_done(self, key: str) -> bool:
        with self.engine.connect() as c:
            q = select(events.c.id).where(events.c.kind == "job", events.c.ref == key)
            return c.execute(q).first() is not None

    def mark_job(
        self, key: str, detail: Mapping[str, Any] | None = None, at: datetime | None = None
    ) -> None:
        with self.engine.begin() as c:
            self._event(c, "job", key, None, "DONE", detail, at)

    def job_records(self, prefix: str) -> list[tuple[str, dict[str, Any]]]:
        """``(key, detail)`` of every job record whose key starts with ``prefix``, oldest
        first: the app's restart-safe memory (start state, book peak, L13 notes)."""
        with self.engine.connect() as c:
            q = (
                select(events.c.ref, events.c.detail)
                .where(events.c.kind == "job", events.c.ref.startswith(prefix, autoescape=True))
                .order_by(events.c.id)
            )
            return [(r[0], dict(r[1] or {})) for r in c.execute(q)]

    def intents_of(self, batch_id: str) -> list[tuple[OrderIntent, str]]:
        with self.engine.connect() as c:
            rows = c.execute(
                select(intents).where(intents.c.batch_id == batch_id).order_by(intents.c.seq)
            )
            return [(_intent_from(r._mapping), r.status) for r in rows]

    def intent(self, coid: str) -> tuple[OrderIntent, str]:
        with self.engine.connect() as c:
            r = c.execute(select(intents).where(intents.c.client_order_id == coid)).first()
        if r is None:
            raise JournalError(f"unknown intent {coid}")
        return _intent_from(r._mapping), r.status

    def intents_in(self, statuses: Iterable[str]) -> list[tuple[OrderIntent, str]]:
        with self.engine.connect() as c:
            rows = c.execute(select(intents).where(intents.c.status.in_(list(statuses))))
            return [(_intent_from(r._mapping), r.status) for r in rows]

    def set_status(
        self,
        coid: str,
        to: str,
        detail: Mapping[str, Any] | None = None,
        at: datetime | None = None,
        qty: int | None = None,
    ) -> None:
        with self.engine.begin() as c:
            r = c.execute(select(intents.c.status).where(intents.c.client_order_id == coid)).first()
            if r is None:
                raise JournalError(f"unknown intent {coid}")
            frm = r[0]
            if to not in TRANSITIONS.get(frm, frozenset()):
                raise JournalError(f"{coid}: {frm} -> {to} is not allowed")
            vals: dict[str, Any] = {"status": to}
            if qty is not None:  # breaker clip before send only
                if frm not in (Status.PLANNED, Status.HELD, Status.RISK_OK, Status.APPROVED):
                    raise JournalError("quantity can change only before send")
                vals["qty"] = qty
            c.execute(update(intents).where(intents.c.client_order_id == coid).values(**vals))
            self._event(c, "intent", coid, frm, to, detail, at)

    def sent_between(self, book: str, start: datetime, end: datetime) -> tuple[int, Decimal]:
        """Orders sent (SENDING) for ``book`` in [start, end) and the buy value at limit."""
        n, buys = 0, Decimal(0)
        with self.engine.connect() as c:
            q = select(events.c.ref, events.c.at).where(
                events.c.kind == "intent", events.c.to_status == Status.SENDING
            )
            rows = list(c.execute(q))
        for ref, raw in rows:
            at = raw if raw.tzinfo else raw.replace(tzinfo=UTC)
            if not ref.startswith(book + "-") or not (start <= at < end):
                continue
            it, _ = self.intent(ref)
            n += 1
            if it.side is Side.BUY:
                buys += it.value_at_limit
        return n, buys

    # ------------------------------------------------------------ approvals
    def add_approval(
        self, batch_id: str, seq: int | None, action: str, actor: str, at: datetime | None = None
    ) -> None:
        with self.engine.begin() as c:
            c.execute(
                insert(approvals).values(
                    batch_id=batch_id, seq=seq, action=action, actor=actor, at=at or utcnow()
                )
            )
            self._event(c, "approval", batch_id, None, action, {"seq": seq, "actor": actor}, at)

    def approvals(self, batch_id: str) -> list[dict[str, Any]]:
        with self.engine.connect() as c:
            q = select(approvals).where(approvals.c.batch_id == batch_id).order_by(approvals.c.id)
            return [dict(r._mapping) for r in c.execute(q)]

    # ------------------------------------------------------------ broker side
    def record_broker_order(
        self,
        coid: str,
        account: str,
        broker_order_id: str | None,
        perm_id: str | None,
        status: str,
        at: datetime | None = None,
    ) -> None:
        with self.engine.begin() as c:
            exists = c.execute(
                select(broker_orders.c.client_order_id).where(
                    broker_orders.c.client_order_id == coid
                )
            ).first()
            vals = {
                "broker_order_id": broker_order_id,
                "perm_id": perm_id,
                "account": account,
                "status": status,
                "at": at or utcnow(),
            }
            if exists:
                c.execute(
                    update(broker_orders)
                    .where(broker_orders.c.client_order_id == coid)
                    .values(**vals)
                )
            else:
                c.execute(insert(broker_orders).values(client_order_id=coid, **vals))
            self._event(c, "broker_order", coid, None, status, {"perm_id": perm_id}, at)

    def broker_order(self, coid: str) -> dict[str, Any] | None:
        with self.engine.connect() as c:
            r = c.execute(
                select(broker_orders).where(broker_orders.c.client_order_id == coid)
            ).first()
            return dict(r._mapping) if r else None

    def add_fill(self, f: FillRecord) -> bool:
        """Insert a fill once (idempotent on ``exec_id``). Returns True if new."""
        with self.engine.begin() as c:
            if c.execute(select(fills.c.exec_id).where(fills.c.exec_id == f.exec_id)).first():
                return False
            c.execute(
                insert(fills).values(
                    exec_id=f.exec_id,
                    client_order_id=f.client_order_id,
                    book=f.book,
                    entity=f.entity,
                    side=f.side.value,
                    qty=f.qty,
                    price=f.price,
                    commission=f.commission,
                    executed_at=f.executed_at,
                )
            )
            self._event(
                c,
                "fill",
                f.client_order_id or f.exec_id,
                None,
                None,
                {"exec_id": f.exec_id, "qty": f.qty, "price": str(f.price)},
            )
            return True

    def fills(self, book: str | None = None, coid: str | None = None) -> list[FillRecord]:
        q = select(fills).order_by(fills.c.executed_at, fills.c.exec_id)
        if book is not None:
            q = q.where(fills.c.book == book)
        if coid is not None:
            q = q.where(fills.c.client_order_id == coid)
        with self.engine.connect() as c:
            return [
                FillRecord(
                    r.exec_id,
                    r.client_order_id,
                    r.book,
                    r.entity,
                    Side(r.side),
                    r.qty,
                    Decimal(r.price),
                    Decimal(r.commission),
                    r.executed_at,
                )
                for r in c.execute(q)
            ]

    def add_cash(
        self, book: str, kind: str, amount: Decimal, note: str, at: datetime | None = None
    ) -> None:
        with self.engine.begin() as c:
            c.execute(
                insert(cash_moves).values(
                    book=book, kind=kind, amount=amount, note=note, at=at or utcnow()
                )
            )
            self._event(c, "cash", book, None, kind, {"amount": str(amount), "note": note}, at)

    # ------------------------------------------------------------ ledger views
    def positions(self, book: str) -> dict[str, int]:
        pos: dict[str, int] = {}
        for f in self.fills(book):
            pos[f.entity] = pos.get(f.entity, 0) + (f.qty if f.side is Side.BUY else -f.qty)
        return {e: q for e, q in sorted(pos.items()) if q != 0}

    def cash(self, book: str) -> Decimal:
        total = Decimal(0)
        with self.engine.connect() as c:
            s = c.execute(
                select(func.coalesce(func.sum(cash_moves.c.amount), 0)).where(
                    cash_moves.c.book == book
                )
            ).scalar_one()
            total += Decimal(str(s))
        for f in self.fills(book):
            gross = f.price * f.qty
            total += (-gross if f.side is Side.BUY else gross) - f.commission
        return total.quantize(Decimal("0.0001"))

    def holdings_cost(self, book: str) -> Decimal:
        """Average cost of open positions incl. commission (for the capital cap)."""
        cost: dict[str, Decimal] = {}
        qty: dict[str, int] = {}
        for f in self.fills(book):
            if f.side is Side.BUY:
                cost[f.entity] = cost.get(f.entity, Decimal(0)) + f.price * f.qty + f.commission
                qty[f.entity] = qty.get(f.entity, 0) + f.qty
            elif qty.get(f.entity):
                avg = cost[f.entity] / qty[f.entity]
                qty[f.entity] -= f.qty
                cost[f.entity] = avg * qty[f.entity]
        return sum(cost.values(), Decimal(0)).quantize(Decimal("0.01"))

    # ------------------------------------------------------------ safety
    def safety_level(self, scope: str = "") -> SafetyLevel:
        """The latched level of ``scope`` ("" = the broker book; BF-D16)."""
        with self.engine.connect() as c:
            q = select(safety.c.level).where(safety.c.scope == scope)
            r = c.execute(q.order_by(safety.c.id.desc()).limit(1)).first()
        return SafetyLevel(r[0]) if r else SafetyLevel.NORMAL

    def set_safety(
        self,
        level: SafetyLevel,
        reason: str,
        actor: str,
        at: datetime | None = None,
        scope: str = "",
    ) -> None:
        with self.engine.begin() as c:
            c.execute(
                insert(safety).values(
                    level=level.value, reason=reason, actor=actor, at=at or utcnow(), scope=scope
                )
            )
            self._event(
                c, "safety", scope or "book", None, level.value,
                {"reason": reason, "actor": actor}, at,
            )  # fmt: skip

    def digest_of(self, obj: Any) -> str:
        return canonical_json(obj)


def _intent_row(it: OrderIntent) -> dict[str, Any]:
    return {
        "client_order_id": it.client_order_id,
        "batch_id": it.batch_id,
        "seq": it.seq,
        "line": it.line,
        "book": it.book,
        "decision_date": it.decision_date,
        "entity": it.entity,
        "side": it.side.value,
        "qty": it.qty,
        "order_type": it.order_type.value,
        "ref_price": it.ref_price,
        "limit_price": it.limit_price,
        "reason": it.reason,
        "attempt": it.attempt,
        "tv_med20": it.tv_med20,
        "prev_close": it.prev_close,
        "flags": list(it.flags),
    }


def _intent_from(r: Any) -> OrderIntent:
    def dec(x: Any) -> Decimal | None:
        return None if x is None else Decimal(str(x))

    return OrderIntent(
        client_order_id=r["client_order_id"],
        batch_id=r["batch_id"],
        seq=r["seq"],
        line=r["line"],
        book=r["book"],
        decision_date=r["decision_date"],
        entity=r["entity"],
        side=Side(r["side"]),
        qty=r["qty"],
        order_type=OrderType(r["order_type"]),
        ref_price=Decimal(str(r["ref_price"])).normalize(),
        limit_price=Decimal(str(r["limit_price"])).normalize(),
        reason=r["reason"],
        attempt=r["attempt"],
        tv_med20=dec(r["tv_med20"]),
        prev_close=dec(r["prev_close"]),
        flags=tuple(r["flags"] or ()),
    )
