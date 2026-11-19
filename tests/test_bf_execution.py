"""BF2/BF3: approval queue, persist-before-send, crash injection, kill switch, paper dry run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from ib_async import Contract, Ticker

from tests.bf_support import synthetic_panel
from tests.fake_ib import FakeIB
from trader.approval import ApprovalBot, FakeTransport, Incoming, TotpVerifier, approved_seqs, totp
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.paper_sim import SimBroker
from trader.constants import ASX_TZ
from trader.execution import Executor
from trader.journal import Journal, Status
from trader.lines.emg2 import (
    BookState,
    BuyPlan,
    Emg2_20Decision,
    Emg2_20Params,
    SellPlan,
    decide_emg2_20,
)
from trader.orders import OrderBatch, build_orders
from trader.risk import RiskContext, SafetyLevel
from trader.secrets import SecretValue

SEED = "JBSWY3DPEHPK3PXP"
CHAT = 4242
D = date(2026, 11, 30)
X = date(2026, 12, 1)
T_APPROVE = datetime(2026, 12, 1, 14, 0, tzinfo=ASX_TZ)
T_SEND = datetime(2026, 12, 1, 15, 45, tzinfo=ASX_TZ)
BOOK = "EMG2_20_PAPER"


def _batch(n_buys: int = 3, sells: int = 1, d: date = D) -> OrderBatch:
    dec = Emg2_20Decision(
        BOOK,
        str(d),
        "d" * 64,
        None,
        Decimal(10000),
        20,
        Decimal(500),
        tuple(SellPlan(f"S{k}", 400, Decimal("2.00"), "EMG2_OFF_LIST") for k in range(sells)),
        tuple(BuyPlan(f"B{k}", k + 1, Decimal("600"), Decimal("1.00")) for k in range(n_buys)),
        (),
        (),
    )
    tv = {f"B{k}": Decimal(10**6) for k in range(n_buys)} | {
        f"S{k}": Decimal(10**6) for k in range(sells)
    }
    return build_orders(dec, tv_med20=tv)


def _ctx(broker: SimBroker | IbkrPaperBroker, now: datetime = T_SEND) -> RiskContext:
    return RiskContext(
        now=now.astimezone(UTC),
        session=X,
        expected_data_date=D,
        data_as_of=D,
        safety=SafetyLevel.NORMAL,
        start_day=False,
        positions=broker.positions(),
        settled_cash=broker.account().settled_cash,
    )


def _sim() -> SimBroker:
    return SimBroker(cash=Decimal(10000), holdings={"S0": 400})


def _bot(j: Journal, ex: Executor | None = None) -> tuple[ApprovalBot, FakeTransport]:
    tr = FakeTransport()
    kill = (lambda: ex.kill(T_APPROVE)) if ex else None
    return ApprovalBot(j, tr, TotpVerifier(SecretValue(SEED)), frozenset({CHAT}), on_kill=kill), tr


def _say(bot: ApprovalBot, text: str, at: datetime = T_APPROVE) -> str:
    return bot.handle(Incoming(CHAT, text.replace("<code>", totp(SEED, at)), at))


def test_BW_APR_03_unapproved_orders_are_never_sent() -> None:
    j, sim = Journal.sqlite(), _sim()
    ex = Executor(j, sim, BOOK)
    b = _batch()
    ex.plan(b, "per_order", X, _ctx(sim))
    rep = ex.submit(b.batch_id, _ctx(sim), T_SEND)  # approval table empty
    assert sim.place_calls == 0 and not rep.sent and len(rep.not_approved) == 4
    assert {st for _, st in j.intents_of(b.batch_id)} == {Status.LAPSED}


def test_L8_per_order_approval_sends_only_approved_orders() -> None:
    j, sim = Journal.sqlite(), _sim()
    ex = Executor(j, sim, BOOK)
    b = _batch()
    ex.plan(b, "per_order", X, _ctx(sim))
    bot, tr = _bot(j)
    assert _say(bot, f"/ok {b.batch_id} 2 <code>").startswith("approved 2")
    assert "invalid or reused" in _say(bot, f"/ok {b.batch_id} 3 <code>")  # code used once
    rep = ex.submit(b.batch_id, _ctx(sim), T_SEND)
    assert sim.place_calls == 1 and rep.sent == [b.intents[1].client_order_id]


def test_BW_APR_05_approval_after_deadline_is_refused_and_ignored() -> None:
    j, sim = Journal.sqlite(), _sim()
    ex = Executor(j, sim, BOOK)
    b = _batch()
    ex.plan(b, "per_order", X, _ctx(sim))
    bot, _ = _bot(j)
    late = datetime(2026, 12, 1, 15, 25, tzinfo=ASX_TZ)
    assert "deadline" in _say(bot, f"/ok {b.batch_id} all <code>", late)
    j.add_approval(
        b.batch_id, None, "OK", "forged-late", late
    )  # even if written, it is past the cut
    assert approved_seqs(j, b.batch_id, datetime(2026, 12, 1, 15, 20, tzinfo=ASX_TZ)) == set()
    ex.submit(b.batch_id, _ctx(sim), T_SEND)
    assert sim.place_calls == 0


def test_BW_APR_04_veto_buys_only_and_strangers_ignored() -> None:
    j, sim = Journal.sqlite(), _sim()
    ex = Executor(j, sim, BOOK)
    b = _batch()
    ex.plan(b, "per_order", X, _ctx(sim))
    bot, tr = _bot(j)
    assert "cannot be vetoed" in _say(bot, f"/veto {b.batch_id} 1 <code>")  # seq 1 is the sell
    t2 = T_APPROVE + timedelta(seconds=31)
    assert _say(bot, f"/veto {b.batch_id} 2 <code>", t2).startswith("vetoed 2")
    t3 = T_APPROVE + timedelta(seconds=62)
    _say(bot, f"/ok {b.batch_id} all <code>", t3)
    assert approved_seqs(j, b.batch_id) == {1, 3, 4}
    assert bot.handle(Incoming(999, f"/ok {b.batch_id} all 000000", T_APPROVE)) == "ignored"
    assert all(c == CHAT for c, _ in tr.outbox)


def test_BW_RSK_30_kill_cancels_open_orders_and_blocks_sends() -> None:
    j, sim = Journal.sqlite(), _sim()
    ex = Executor(j, sim, BOOK)
    b = _batch()
    ex.plan(b, "auto", X, _ctx(sim))
    ex.submit(b.batch_id, _ctx(sim), T_SEND)
    assert len(sim.open_orders()) == 4
    bot, tr = _bot(j, ex)
    assert "4 open order(s) cancelled" in _say(bot, "/kill")
    assert not sim.open_orders() and j.safety_level() is SafetyLevel.KILLED
    b2 = _batch(1, 0, date(2026, 11, 27))
    ex.plan(b2, "auto", X, _ctx(sim))
    rep = ex.submit(b2.batch_id, _ctx(sim), T_SEND)
    assert sim.place_calls == 4 and not rep.sent
    assert "refused" in _say(bot, "/resume 123456")
    assert _say(bot, "/resume <code>", T_APPROVE + timedelta(seconds=40)) == "re-armed: NORMAL"


def test_BW_RSK_30_pause_lets_sells_through() -> None:
    j, sim = Journal.sqlite(), _sim()
    ex = Executor(j, sim, BOOK)
    b = _batch()
    ex.plan(b, "auto", X, _ctx(sim))
    bot, _ = _bot(j)
    _say(bot, "/pause")
    rep = ex.submit(b.batch_id, _ctx(sim), T_SEND)
    assert [c.split("-")[-2] for c in rep.sent] == ["SELL"]


@pytest.mark.parametrize("point", ["after_persist", "after_send"])
def test_BW_EXE_06_crash_injection_exactly_one_broker_order_per_intent(point: str) -> None:
    j, f = Journal.sqlite(), FakeIB()
    broker = IbkrPaperBroker(IbkrSettings("gw", 4004, 11, "DU1234567"), ib_factory=lambda: f)
    broker.connect()
    f.cash = 10000.0

    class CrashError(Exception):
        pass

    def hook(p: str, coid: str) -> None:
        if p == point and coid.endswith("B1-BUY-1"):
            raise CrashError

    ex = Executor(j, broker, BOOK, crash=hook)
    b = _batch(3, 0)
    ex.plan(b, "auto", X, _ctx(broker))
    with pytest.raises(CrashError):
        ex.submit(b.batch_id, _ctx(broker), T_SEND)
    # the process restarts: a new executor, the same journal, the gateway restarted too
    f.restart()
    ex2 = Executor(j, broker, BOOK)
    pages = ex2.recover(T_SEND)
    ex2.submit(b.batch_id, _ctx(broker), T_SEND)
    ex2.submit(b.batch_id, _ctx(broker), T_SEND)  # idempotent
    refs = [o.orderRef for _, o in f.placed]
    assert len(refs) == len(set(refs))  # never two broker orders for one intent
    crashed = next(i for i in b.intents if i.entity == "B1").client_order_id
    _, st = j.intent(crashed)
    if point == "after_persist":
        assert crashed not in refs and st == Status.NEEDS_REVIEW and pages
    else:
        assert refs.count(crashed) == 1 and st == Status.SENT
    assert refs.count(next(i for i in b.intents if i.entity == "B0").client_order_id) == 1


def test_EXE_10_timeout_goes_to_review_and_is_not_resent() -> None:
    j, f = Journal.sqlite(), FakeIB(ack="never")
    t = [0.0]

    def clock() -> float:
        t[0] += 5
        return t[0]

    broker = IbkrPaperBroker(
        IbkrSettings("gw", 4004, 11, "DU1234567"), ib_factory=lambda: f, clock=clock
    )
    broker.connect()
    ex = Executor(j, broker, BOOK)
    b = _batch(1, 0)
    ex.plan(b, "auto", X, _ctx(broker))
    rep = ex.submit(b.batch_id, _ctx(broker), T_SEND)
    assert rep.review and rep.pages and len(f.placed) == 1
    ex.submit(b.batch_id, _ctx(broker), T_SEND)
    assert len(f.placed) == 1
    f.gateway_trades[0].orderStatus.status = "Submitted"  # the ack arrives late
    ex.recover(T_SEND)
    assert j.intent(b.intents[0].client_order_id)[1] == Status.SENT


def test_BF3_paper_dry_run_engine_to_fills_reconciled() -> None:
    """Decision -> orders -> breaker -> per-order approval -> send -> auction -> fills."""
    from trader.reconcile import reconcile

    p = synthetic_panel()
    dec = decide_emg2_20(
        p,
        BookState(BOOK, Decimal(10000)),
        Emg2_20Params(skip_lottery=False),
    )
    tv = {e: Decimal(10**7) for e in p.entities}
    batch = build_orders(dec, tv_med20=tv)
    assert batch.intents
    j, sim = Journal.sqlite(), SimBroker(cash=Decimal(10000))
    j.add_cash(BOOK, "DEPOSIT", Decimal(10000), "paper deposit")
    ex = Executor(j, sim, BOOK)
    ctx = RiskContext(
        now=T_SEND.astimezone(UTC),
        session=X,
        expected_data_date=D,
        data_as_of=D,
        safety=SafetyLevel.NORMAL,
        start_day=True,
        positions={},
        settled_cash=Decimal(10000),
    )
    ex.plan(batch, "per_order", X, ctx)
    bot, _ = _bot(j)
    _say(bot, f"/ok {batch.batch_id} all <code>")
    rep = ex.submit(batch.batch_id, ctx, T_SEND)
    assert len(rep.sent) == len(batch.intents)
    closes = {it.entity: it.ref_price for it in batch.intents}
    sim.advance(X, closes)
    assert ex.collect_fills(T_SEND, session_closed=True) == len(batch.intents)
    assert {st for _, st in j.intents_of(batch.batch_id)} == {Status.FILLED}
    r = reconcile(j.positions(BOOK), j.cash(BOOK), sim.positions(), sim.account().settled_cash)
    assert r.ok, r.breaks


@dataclass
class _QuoteIB(FakeIB):
    """Mock gateway with a chosen bid/ask, or a market-data failure (BF-D22)."""

    bid: float = 0.995
    ask: float = 1.005
    fail: bool = False

    def reqTickers(self, *cs: Contract, regulatorySnapshot: bool = False) -> list[Ticker]:  # noqa: N803
        if self.fail:
            raise TimeoutError("no market data")
        out = super().reqTickers(*cs)
        for t in out:
            t.bid, t.ask = self.bid, self.ask
        return out


def _ibkr(f: FakeIB) -> IbkrPaperBroker:
    broker = IbkrPaperBroker(IbkrSettings("gw", 4004, 11, "DU1234567"), ib_factory=lambda: f)
    broker.connect()
    return broker


def test_BF_D22_mid_at_order_time_is_journalled_for_every_send() -> None:
    """The broker's bid/ask just before each send is kept with its mid (cost ratio of
    AMENDMENT_adopt_rule_v3: fill price against the mid at order time)."""
    j, f = Journal.sqlite(), _QuoteIB(bid=0.995, ask=1.005)
    broker = _ibkr(f)
    ex = Executor(j, broker, BOOK)
    b = _batch(2, 0)
    ex.plan(b, "auto", X, _ctx(broker))
    rep = ex.submit(b.batch_id, _ctx(broker), T_SEND)
    assert len(rep.sent) == 2 == len(f.placed)
    for it in b.intents:
        (r,) = j.order_quotes(it.client_order_id)
        assert (r["book"], r["entity"], r["side"]) == (BOOK, it.entity, it.side.value)
        assert r["source"] == "IbkrPaperBroker" and r["note"] == ""
        assert j.mid_at_order(it.client_order_id) == Decimal("1")
        assert r["at"].replace(tzinfo=UTC) == T_SEND.astimezone(UTC)
        assert j.intent(it.client_order_id)[1] == Status.SENT


def test_BF_D22_missing_or_failed_quote_never_blocks_the_order() -> None:
    j, f = Journal.sqlite(), _QuoteIB(fail=True)
    broker = _ibkr(f)
    ex = Executor(j, broker, BOOK)
    b = _batch(1, 0)
    ex.plan(b, "auto", X, _ctx(broker))
    rep = ex.submit(b.batch_id, _ctx(broker), T_SEND)
    coid = b.intents[0].client_order_id
    assert rep.sent == [coid] and len(f.placed) == 1
    (r,) = j.order_quotes(coid)
    assert r["mid"] is None and r["note"].startswith("quote failed: TimeoutError")
    assert j.mid_at_order(coid) is None
    # a crossed quote gives no mid either, and the order still goes
    f.fail, f.bid, f.ask = False, 1.01, 1.00
    b2 = _batch(1, 0, d=date(2026, 12, 31))
    ex.plan(b2, "auto", X, _ctx(broker))
    rep2 = ex.submit(b2.batch_id, _ctx(broker), T_SEND)
    (r2,) = j.order_quotes(b2.intents[0].client_order_id)
    assert rep2.sent and r2["mid"] is None and r2["note"] == "no two-sided quote"
    assert Decimal(str(r2["bid"])) == Decimal("1.01")


def test_BF_D22_simulated_books_record_their_reference_quote() -> None:
    j, sim = Journal.sqlite(), _sim()
    sim.last_close = {"B0": Decimal("1.00"), "S0": Decimal("2.00")}
    ex = Executor(j, sim, BOOK)
    b = _batch(1, 1)
    ex.plan(b, "auto", X, _ctx(sim))
    ex.submit(b.batch_id, _ctx(sim), T_SEND)
    got = {r["entity"]: (r["mid"], r["source"]) for r in j.order_quotes()}
    assert got == {"B0": (Decimal(1), "SimBroker"), "S0": (Decimal(2), "SimBroker")}
