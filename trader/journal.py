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
  safety level is the latest ``bf_safety`` row;
* the broker's bid/ask (and mid) just before each send is kept in ``bf_order_quotes``
  (BF-D22), so live costs can be measured against the model from the first fill;
* dividends, capital returns, demerged shares and other corporate actions are
  append-only ``bf_corporate_actions`` rows, one per (book, key) (BF-D23); positions,
  cash and the cost base include them, and a code change may carry a share ratio
  (``bf_identity.ratio``, BF-D25).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import ROUND_FLOOR, Decimal
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
    UniqueConstraint,
    create_engine,
    event,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import URL, make_url

from trader.canonical import canonical_json
from trader.constants import ASX_TZ
from trader.corporate_actions import Booking, CaKind, CostBook
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

identity = Table(
    "bf_identity",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("old_code", String(24), nullable=False, index=True),
    Column("new_code", String(24), nullable=False),
    # PROPOSED (applied, owner to confirm) | CONFIRMED | REJECTED; the latest row wins
    Column("status", String(12), nullable=False),
    Column("rule", String(8), nullable=False),  # A7b | A7c | OWNER | FLEX
    Column("score", Numeric(8, 6)),
    Column("actor", String(64), nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
    Column("note", String(200), nullable=False),
    # new shares per old share (BF-D25); NULL = 1 (a plain code change)
    Column("ratio", Numeric(18, 8)),
)

# Corporate actions booked per book (BF-D23): IBKR's Flex records for broker books, the
# vendor + record calendar for simulated books. Append-only; (book, key) unique.
corporate_actions = Table(
    "bf_corporate_actions",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("book", String(48), nullable=False),
    Column("key", String(120), nullable=False),
    Column("kind", String(16), nullable=False),
    Column("code", String(24), nullable=False, index=True),
    Column("ex_date", Date),
    Column("pay_date", Date),
    Column("held", Integer, nullable=False),
    Column("cash", Numeric(18, 4), nullable=False),
    Column("income", Numeric(18, 4), nullable=False),
    Column("franked_pct", Numeric(7, 4)),
    Column("franking_credit", Numeric(18, 4), nullable=False),
    Column("cost_reduction", Numeric(18, 4), nullable=False),
    Column("qty_change", Integer, nullable=False),
    Column("new_code", String(24)),
    Column("new_shares", Integer, nullable=False),
    Column("child_cost", Numeric(18, 4)),
    Column("cost_moved_pct", Numeric(9, 6)),
    Column("ratio", Numeric(18, 8)),
    Column("source", String(12), nullable=False),
    Column("expected_key", String(120)),
    Column("tax_class", String(16), nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
    Column("note", String(200), nullable=False),
    UniqueConstraint("book", "key", name="uq_bf_corporate_actions_book_key"),
)

# The broker's quote at the moment each order is sent (BF-D22): the mid against which
# AMENDMENT_adopt_rule_v3 measures the realised cost per trade ("fill price against the
# mid at order time"). Append-only; one row per send attempt; a missing or failed quote
# is recorded as such (mid NULL) and never blocks the order.
order_quotes = Table(
    "bf_order_quotes",
    md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("client_order_id", String(96), nullable=False, index=True),
    Column("book", String(48), nullable=False),
    Column("entity", String(24), nullable=False),
    Column("side", String(4), nullable=False),
    Column("bid", Numeric(18, 4)),
    Column("ask", Numeric(18, 4)),
    Column("last", Numeric(18, 4)),
    Column("mid", Numeric(18, 6)),
    Column("quote_time", DateTime(timezone=True)),
    Column("at", DateTime(timezone=True), nullable=False),
    Column("source", String(40), nullable=False),  # broker class, e.g. IbkrPaperBroker
    Column("note", String(200), nullable=False),
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


def read_only_engine(url: str | URL) -> Engine:
    """An engine whose sessions are read-only in the database (BF-D37): PostgreSQL
    ``default_transaction_read_only = on`` for every connection; SQLite
    ``PRAGMA query_only = ON``. A write then fails in the database, whatever the code."""
    u = make_url(url)
    if u.drivername.startswith("postgresql"):
        return create_engine(u, connect_args={"options": "-c default_transaction_read_only=on"})
    eng = create_engine(u)
    if u.drivername.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _query_only(dbapi_conn: Any, _rec: Any) -> None:
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA query_only = ON")
            cur.close()

    return eng


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

    @classmethod
    def read_only(cls, engine: Engine) -> Journal:
        """A reader's view (the dashboard, BF-D37): no ``create_all`` (no DDL); the
        engine should come from ``read_only_engine`` so that every write is refused by
        the database itself."""
        j = cls.__new__(cls)
        j.engine = engine
        return j

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

    def intents_of_book(self, book: str) -> list[tuple[OrderIntent, str]]:
        """Every intent of a book in one query, by batch then seq (as ``batches_of``)."""
        with self.engine.connect() as c:
            rows = c.execute(
                select(intents)
                .where(intents.c.book == book)
                .order_by(intents.c.batch_id, intents.c.seq)
            )
            return [(_intent_from(r._mapping), r.status) for r in rows]

    def intent(self, coid: str) -> tuple[OrderIntent, str]:
        with self.engine.connect() as c:
            r = c.execute(select(intents).where(intents.c.client_order_id == coid)).first()
        if r is None:
            raise JournalError(f"unknown intent {coid}")
        return _intent_from(r._mapping), r.status

    def intents_in(
        self, statuses: Iterable[str], book: str | None = None
    ) -> list[tuple[OrderIntent, str]]:
        q = select(intents).where(intents.c.status.in_(list(statuses)))
        if book is not None:
            q = q.where(intents.c.book == book)
        with self.engine.connect() as c:
            return [(_intent_from(r._mapping), r.status) for r in c.execute(q)]

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

    def cash_moves_of(self, book: str) -> list[dict[str, Any]]:
        """The book's cash records (deposits, withdrawals, adjustments) in time order."""
        q = select(cash_moves).where(cash_moves.c.book == book).order_by(cash_moves.c.id)
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(q)]

    # ------------------------------------------------------------ quote at order time (BF-D22)
    def record_order_quote(
        self,
        it: OrderIntent,
        bid: Decimal | None,
        ask: Decimal | None,
        last: Decimal | None,
        quote_time: datetime | None,
        source: str,
        note: str = "",
        at: datetime | None = None,
    ) -> Decimal | None:
        """Append the broker's quote taken just before ``it`` is sent; returns the mid
        (``mid_of(bid, ask)``; None when there is no usable two-sided quote)."""
        mid = mid_of(bid, ask)
        if mid is None and not note:
            note = "no two-sided quote"
        with self.engine.begin() as c:
            c.execute(
                insert(order_quotes).values(
                    client_order_id=it.client_order_id, book=it.book, entity=it.entity,
                    side=it.side.value, bid=bid, ask=ask, last=last, mid=mid,
                    quote_time=None if quote_time is None else quote_time.astimezone(UTC),
                    at=(at or utcnow()).astimezone(UTC), source=source[:40], note=note[:200],
                )
            )  # fmt: skip
        return mid

    def order_quotes(self, coid: str | None = None) -> list[dict[str, Any]]:
        q = select(order_quotes).order_by(order_quotes.c.id)
        if coid is not None:
            q = q.where(order_quotes.c.client_order_id == coid)
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(q)]

    def mid_at_order(self, coid: str) -> Decimal | None:
        """The mid of the latest quote recorded when ``coid`` was sent (None if none)."""
        rows = self.order_quotes(coid)
        if not rows or rows[-1]["mid"] is None:
            return None
        return Decimal(str(rows[-1]["mid"])).normalize()

    # ------------------------------------------------------------ identity (code changes)
    def add_identity(
        self,
        old: str,
        new: str,
        status: str,
        rule: str,
        score: Decimal | None,
        actor: str,
        note: str,
        at: datetime | None = None,
        ratio: Decimal | None = None,
    ) -> None:
        """Record a code change ``old -> new`` (PROPOSED / CONFIRMED / REJECTED);
        ``ratio`` new shares per old share (None = 1; BF-D25)."""
        if status not in ("PROPOSED", "CONFIRMED", "REJECTED") or old == new:
            raise JournalError(f"bad identity record {old}->{new} {status}")
        if ratio is not None and ratio <= 0:
            raise JournalError(f"bad ratio {ratio} for {old}->{new}")
        r = None if ratio is None or ratio == 1 else ratio
        with self.engine.begin() as c:
            c.execute(
                insert(identity).values(
                    old_code=old, new_code=new, status=status, rule=rule, score=score,
                    actor=actor, at=at or utcnow(), note=note[:200], ratio=r,
                )
            )  # fmt: skip
            detail = {"new": new, "rule": rule} | ({"ratio": str(r)} if r is not None else {})
            self._event(c, "identity", old, None, status, detail, at)

    def identity_records(self) -> dict[str, dict[str, Any]]:
        """The latest identity record of every old code."""
        with self.engine.connect() as c:
            rows = c.execute(select(identity).order_by(identity.c.id)).all()
        return {r.old_code: dict(r._mapping) for r in rows}

    def identity_ratios(self) -> dict[str, tuple[str, Decimal]]:
        """Old code -> (the code it trades as now, new shares per old share), applied
        records (PROPOSED or CONFIRMED), chains followed (ratios multiply)."""
        step = {
            o: (str(r["new_code"]), Decimal(str(r["ratio"])) if r.get("ratio") else Decimal(1))
            for o, r in self.identity_records().items()
            if r["status"] in ("PROPOSED", "CONFIRMED")
        }
        out: dict[str, tuple[str, Decimal]] = {}
        for o, first in step.items():
            n, k = first
            seen = {o}
            while n in step and n not in seen:
                seen.add(n)
                n2, k2 = step[n]
                n, k = n2, k * k2
            out[o] = (n, k)
        return out

    def identity_map(self) -> dict[str, str]:
        """Old code -> the code it trades as now (applied: PROPOSED or CONFIRMED),
        chains followed. Positions and holdings cost are reported under the new code."""
        return {o: n for o, (n, _) in self.identity_ratios().items()}

    def map_codes(self, positions: Mapping[str, int]) -> dict[str, int]:
        """Positions under the current codes (e.g. a broker that still shows the old),
        share counts by the code change's ratio (fractions dropped)."""
        return _fold(positions.items(), self.identity_ratios())

    # ------------------------------------------------------------ corporate actions (BF-D23)
    def add_ca(self, book: str, b: Booking, at: datetime | None = None) -> bool:
        """Book a corporate action once per (book, key); False when already booked."""
        with self.engine.begin() as c:
            q = select(corporate_actions.c.id).where(
                corporate_actions.c.book == book, corporate_actions.c.key == b.key
            )
            if c.execute(q).first() is not None:
                return False
            c.execute(
                insert(corporate_actions).values(
                    book=book, key=b.key, kind=b.kind.value, code=b.code, ex_date=b.ex_date,
                    pay_date=b.pay_date, held=b.held, cash=b.cash, income=b.income,
                    franked_pct=b.franked_pct, franking_credit=b.franking_credit,
                    cost_reduction=b.cost_reduction, qty_change=b.qty_change,
                    new_code=b.new_code, new_shares=b.new_shares, child_cost=b.child_cost,
                    cost_moved_pct=b.cost_moved_pct, ratio=b.ratio, source=b.source[:12],
                    expected_key=b.expected_key, tax_class=b.tax_class,
                    at=(at or utcnow()).astimezone(UTC), note=b.note[:200],
                )
            )  # fmt: skip
            self._event(
                c, "corporate_action", book, None, b.kind.value,
                {"key": b.key, "code": b.code, "cash": str(b.cash), "new_code": b.new_code,
                 "new_shares": b.new_shares, "qty_change": b.qty_change}, at,
            )  # fmt: skip
        return True

    def ca_bookings(self, book: str | None = None) -> list[Booking]:
        q = select(corporate_actions).order_by(corporate_actions.c.id)
        if book is not None:
            q = q.where(corporate_actions.c.book == book)
        with self.engine.connect() as c:
            rows = c.execute(q).all()

        def dec(x: Any) -> Decimal | None:
            return None if x is None else Decimal(str(x))

        return [
            Booking(
                key=r.key, kind=CaKind(r.kind), code=r.code, ex_date=r.ex_date,
                pay_date=r.pay_date, held=r.held, cash=Decimal(str(r.cash)),
                income=Decimal(str(r.income)), franked_pct=dec(r.franked_pct),
                franking_credit=Decimal(str(r.franking_credit)),
                cost_reduction=Decimal(str(r.cost_reduction)), qty_change=r.qty_change,
                new_code=r.new_code, new_shares=r.new_shares, child_cost=dec(r.child_cost),
                cost_moved_pct=dec(r.cost_moved_pct), ratio=dec(r.ratio), source=r.source,
                expected_key=r.expected_key, tax_class=r.tax_class, note=r.note,
            )
            for r in rows
        ]  # fmt: skip

    def ca_settled(self, book: str) -> set[str]:
        """Calendar keys a booking of ``book`` settles (its own key or ``expected_key``)."""
        out: set[str] = set()
        for b in self.ca_bookings(book):
            out.add(b.key)
            if b.expected_key:
                out.add(b.expected_key)
        return out

    def known_codes(self) -> set[str]:
        """Every code any book has traded or received (for an owner's ``/idmap``)."""
        with self.engine.connect() as c:
            out = {r[0] for r in c.execute(select(fills.c.entity).distinct())}
            for r in c.execute(select(corporate_actions.c.code, corporate_actions.c.new_code)):
                out.update(x for x in r if x)
        return out

    def held_at(self, book: str, code: str, ex_date: date) -> int:
        """Shares of ``code`` (or the code it trades as now) held at the close of the
        session before ``ex_date``: the entitlement to an event with that ex-date."""
        pos = self.positions(book, before=_sydney_midnight(ex_date))
        return pos.get(code) or pos.get(self.identity_map().get(code, code), 0)

    # ------------------------------------------------------------ ledger views
    def positions(self, book: str, before: datetime | None = None) -> dict[str, int]:
        """Shares by current code: fills, corporate actions (new shares, splits,
        disposals) and code changes with their ratio. ``before``: as of that time."""
        raw: list[tuple[str, Decimal]] = []
        for f in self.fills(book):
            if before is not None and _utc(f.executed_at) >= before:
                continue
            raw.append((f.entity, Decimal(f.qty if f.side is Side.BUY else -f.qty)))
        for b in self.ca_bookings(book):
            if before is not None and _effective(b) >= before:
                continue
            if b.qty_change:
                raw.append((b.code, Decimal(b.qty_change)))
            if b.new_code and b.new_shares and b.kind is not CaKind.CODE_CHANGE:
                raw.append((b.new_code, Decimal(b.new_shares)))
        return _fold(raw, self.identity_ratios())

    def has_cash_moves(self, book: str) -> bool:
        """Whether the book has any deposit or other cash record (it has been set up)."""
        with self.engine.connect() as c:
            q = select(cash_moves.c.book).where(cash_moves.c.book == book).limit(1)
            return c.execute(q).first() is not None

    def cash(self, book: str) -> Decimal:
        total = Decimal(0)
        with self.engine.connect() as c:
            s = c.execute(
                select(func.coalesce(func.sum(cash_moves.c.amount), 0)).where(
                    cash_moves.c.book == book
                )
            ).scalar_one()
            total += Decimal(str(s))
            s = c.execute(
                select(func.coalesce(func.sum(corporate_actions.c.cash), 0)).where(
                    corporate_actions.c.book == book
                )
            ).scalar_one()
            total += Decimal(str(s))
        for f in self.fills(book):
            gross = f.price * f.qty
            total += (-gross if f.side is Side.BUY else gross) - f.commission
        return total.quantize(Decimal("0.0001"))

    def cost_book(self, book: str) -> CostBook:
        """Average cost by current code, fills and corporate actions in time order: a
        capital return lowers the cost base (above it: G1), a demerger moves its share
        of the parent's cost to the new shares, in-specie shares come in at their value,
        a code change keeps the cost (one company; ratio applied to the count)."""
        m = self.identity_ratios()
        cb = CostBook()
        stream: list[tuple[datetime, int, Any]] = []
        for i, f in enumerate(self.fills(book)):
            stream.append((_utc(f.executed_at), i, f))
        for i, b in enumerate(self.ca_bookings(book)):
            stream.append((_effective(b), -1_000_000 + i, b))  # before that day's fills
        for _, _, x in sorted(stream, key=lambda t: (t[0], t[1])):
            if isinstance(x, Booking):
                if x.kind is CaKind.CODE_CHANGE:
                    continue
                code = m.get(x.code, (x.code, Decimal(1)))[0]
                new = m.get(x.new_code, (x.new_code, Decimal(1)))[0] if x.new_code else None
                cb.apply(x, code, new)
                continue
            e, k = m.get(x.entity, (x.entity, Decimal(1)))
            if x.side is Side.BUY:
                cb.buy(e, x.qty * k, x.price * x.qty + x.commission)
            else:
                cb.sell(e, x.qty * k)
        return cb

    def holdings_cost(self, book: str) -> Decimal:
        """Average cost of open positions incl. commission (for the capital cap)."""
        return self.cost_book(book).total().quantize(Decimal("0.01"))

    def tax_view(self, book: str, fy_end: date) -> dict[str, Any]:
        """BW-TAX-02 corporate-action lines of the year to 30 June ``fy_end``: dividends
        and specials (income), franked amount and franking credits where the franking
        is known (else "not counted"), capital returns (cost-base reductions; any part
        above the cost base is a G1 capital gain), demergers / in-specie receipts and
        what is still provisional or unclassified for the tax agent."""
        start = date(fy_end.year - 1, 7, 1)
        rows = [
            b for b in self.ca_bookings(book)
            if start <= (b.pay_date or b.ex_date or fy_end) <= fy_end
        ]  # fmt: skip
        z = Decimal(0)

        def tot(xs: Iterable[Decimal]) -> str:
            return str(sum(xs, z).quantize(Decimal("0.01")))

        divs = [b for b in rows if b.kind in (CaKind.DIVIDEND, CaKind.IN_SPECIE)]
        spec = [b for b in rows if b.kind is CaKind.SPECIAL]
        inc = [*divs, *spec]
        known = [b for b in inc if b.franked_pct is not None]
        return {
            "book": book,
            "year": f"{start.isoformat()}..{fy_end.isoformat()}",
            "dividends": tot(b.income for b in divs),
            "specials": tot(b.income for b in spec),
            "franked_amount": tot(b.income * (b.franked_pct or z) / 100 for b in known),
            "franking_credits": tot(b.franking_credit for b in known),
            "franking_not_counted": tot(b.income for b in inc if b.franked_pct is None),
            "capital_returns": tot(b.cost_reduction for b in rows),
            "withholding": tot(b.cash for b in rows if b.kind is CaKind.WITHHOLDING),
            "g1_gains": str(self.cost_book(book).g1.quantize(Decimal("0.01"))),
            "share_receipts": [
                f"{b.kind.value} {b.code}->{b.new_code} {b.new_shares}"
                for b in rows if b.new_code and b.kind is not CaKind.CODE_CHANGE
            ],
            "to_confirm": [
                f"{b.key} {b.kind.value} {b.code}: {b.tax_class}" for b in rows if b.tax_class
            ],
        }  # fmt: skip

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


def mid_of(bid: Decimal | None, ask: Decimal | None) -> Decimal | None:
    """(bid + ask) / 2 for a usable two-sided quote (both > 0, ask >= bid), else None."""
    if bid is None or ask is None or bid <= 0 or ask <= 0 or ask < bid:
        return None
    return (bid + ask) / 2


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


def _utc(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def _sydney_midnight(d: date) -> datetime:
    return datetime.combine(d, time(0, 0), ASX_TZ).astimezone(UTC)


def _effective(b: Booking) -> datetime:
    """A corporate action takes effect at the start of its ex-date (Sydney); without one,
    of its pay or report date."""
    d = b.ex_date or b.pay_date
    return _sydney_midnight(d) if d is not None else datetime.min.replace(tzinfo=UTC)


def _fold(
    items: Iterable[tuple[str, Decimal | int]], ratios: Mapping[str, tuple[str, Decimal]]
) -> dict[str, int]:
    """Sum shares under the current codes; an old code's shares by the code change's
    ratio, fractions dropped (cash in lieu comes as its own booking)."""
    acc: dict[str, Decimal] = {}
    for e, q in items:
        n, k = ratios.get(e, (e, Decimal(1)))
        acc[n] = acc.get(n, Decimal(0)) + Decimal(q) * k
    out = {e: int(q.to_integral_value(ROUND_FLOOR)) for e, q in acc.items()}
    return {e: q for e, q in sorted(out.items()) if q != 0}
