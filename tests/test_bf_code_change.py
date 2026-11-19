"""BF-D19: a held code that stops trading and continues under a new code (the HGO ->
KAN case of Nov 2026) is carried under the new code, never as two companies, and the
owner is paged to confirm."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import numpy as np

from tests.test_bf_app import CHAT, D0, DAYS, SEED, _app, _closes, _panel
from trader.approval import Incoming, totp
from trader.bf_app import BfApp, at, dry_run, marks_from_panels, mock_auction, owner_approves_all
from trader.broker.mock_gateway import MockGateway
from trader.data.forward_store import resolve_aliases
from trader.data.identity import DupPair
from trader.identity_change import code_changes
from trader.journal import Journal
from trader.orders import Side
from trader.panel import PricePanel
from trader.risk import SafetyLevel

NEW = "KAN"
X = DAYS[6]  # first session the old code has no close


def _renamed(old: str) -> tuple[object, object]:
    """Providers where ``old`` stops after the session before X and ``NEW`` carries its
    prices (vendor history under both codes; the A7 drop keeps the living code)."""

    def panel(d: date) -> PricePanel:
        p = _panel(d)
        if d < X:
            return p
        j = p.entities.index(old)
        keep = [k for k in range(len(p.entities)) if k != j]

        def move(a: np.ndarray) -> np.ndarray:
            return np.column_stack([a[:, keep], a[:, j]])

        ents = (*[p.entities[k] for k in keep], NEW)
        cls = {e: p.sec_class.get(e, "ORD") for e in ents if e != NEW} | {NEW: "ORD"}
        return PricePanel(
            as_of=p.as_of, dates=p.dates, entities=ents, close=move(p.close),
            ret=move(p.ret), tv=move(p.tv), sec_class=cls,
            aliases={old: (NEW, "A7b", 1.0)},
        )  # fmt: skip

    def closes(d: date) -> dict[str, Decimal]:
        c = _closes(d)
        if d >= X and old in c:
            c[NEW] = c.pop(old)
        return c

    return panel, closes


def _started(random_twins: int = 0) -> tuple[BfApp, MockGateway, str]:
    app, gw, _ = _app(D0, random_twins=random_twins)
    dry_run(app, DAYS[:6], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    held = set(app.j.positions(app.s.book)) & set(app.j.positions(app.s.sim_book))
    old = sorted(held)[0]
    panel, closes = _renamed(old)
    app.panels, app.closes = panel, closes  # type: ignore[assignment]
    app.marks = marks_from_panels(panel)  # type: ignore[arg-type]
    return app, gw, old


def _owner(app: BfApp, d: date, text: str, hhmm: str = "12:00") -> str:
    t = at(d, hhmm)
    app.transport_inject(Incoming(CHAT, text.replace("<code>", totp(SEED, t)), t))
    app.job_tick(d, t)
    return str([t for _, t in app.transport.outbox][-1])  # type: ignore[attr-defined]


def test_BF_D19_held_code_that_stops_is_carried_under_its_new_code() -> None:
    app, gw, old = _started(random_twins=2)
    book, sim = app.s.book, app.s.sim_book
    q_book, q_sim = app.j.positions(book)[old], app.j.positions(sim)[old]
    cost = app.j.holdings_cost(book)
    twins = {n: app.j.positions(n).get(old, 0) for n, *_ in app.rnd}
    owner = owner_approves_all(app, SEED)
    days = [d for d in DAYS if d >= X]
    auction = mock_auction(gw, app.closes)
    first = dry_run(app, days[:1], {}, owner, auction)
    rec = app.j.identity_records()[old]
    assert (rec["new_code"], rec["status"], rec["rule"]) == (NEW, "PROPOSED", "A7b")
    pages = [p for p in first.pages if p.startswith(f"PAGE code change {X}")]
    assert len(pages) == 1 and f"/idmap {old} {NEW} <code>" in pages[0]
    # one company: the position moved under the new code, same shares, cost kept
    assert app.j.positions(book)[NEW] == q_book and old not in app.j.positions(book)
    assert app.j.positions(sim)[NEW] == q_sim and app.sim.holdings[NEW] == q_sim
    assert app.j.holdings_cost(book) == cost
    for n, q in twins.items():
        assert old not in app.j.positions(n) and app.j.positions(n).get(NEW, 0) == q
    summ = dry_run(app, days[1:], {}, owner, auction)
    pos = app.j.positions(book)
    assert old not in pos
    for b in (book, sim, *(n for n, *_ in app.rnd)):
        buys = [
            it
            for it, _ in app.j.intents_of_book(b)
            if it.entity in (old, NEW) and it.side is Side.BUY and it.decision_date >= X
        ]
        assert not buys  # never a second holding of the same company
    # the broker still shows the old code: reconciliation maps it, no break, no halt
    assert summ.safety == SafetyLevel.NORMAL.value and first.safety == summ.safety
    assert all(summ.recon.values()) and all(first.recon.values())
    reports = [t for _, t in app.transport.outbox if t.startswith("PAPER")]  # type: ignore[attr-defined]
    last = reports[-1]
    assert f"code change {old} -> {NEW} not confirmed" in last and f"no mark for {old}" not in last
    # the owner confirms from the phone (2FA): the flag goes
    assert _owner(app, days[-1], f"/idmap {old} {NEW} <code>").endswith("confirmed")
    assert app.j.identity_records()[old]["status"] == "CONFIRMED"
    assert app.j.positions(book).get(NEW) == pos.get(NEW)
    # a restart rebuilds the simulated books under the new code from the journal
    app2, _, _ = _app(D0, random_twins=2, journal=app.j, gw=gw)
    assert app2.sim.holdings == app.j.positions(sim)


def test_BF_D19_owner_can_undo_a_code_change_and_a_bad_code_is_refused() -> None:
    app, gw, old = _started()
    dry_run(app, [X], {}, owner_approves_all(app, SEED), mock_auction(gw, app.closes))
    assert NEW in app.j.positions(app.s.book)
    assert _owner(app, X, f"/idmap {old} XYZ <code>").startswith("refused")
    assert _owner(app, X, f"/idmap_reject {old} 000000", "12:05").startswith("refused")
    assert "undone" in _owner(app, X, f"/idmap_reject {old} <code>", "12:10")
    assert old in app.j.positions(app.s.book) and NEW not in app.j.positions(app.s.book)
    # the rejection stands: the next session does not raise it again
    n = len(app.j.identity_records())
    app.job_sim(DAYS[7], at(DAYS[7], "22:15"))
    assert len(app.j.identity_records()) == n
    assert app.sim.holdings == app.j.positions(app.s.sim_book)


def test_BF_D19_code_changes_rule() -> None:
    p = _panel(D0)
    p = PricePanel(
        as_of=p.as_of, dates=p.dates, entities=p.entities, close=p.close, ret=p.ret, tv=p.tv,
        sec_class=p.sec_class, aliases={"OLD": (p.entities[0], "A7c", 0.9991), "GONE": ("ZZZ", "A7b", 1.0)},
    )  # fmt: skip
    new = p.entities[0]
    got = code_changes({"OLD", "GONE", new}, p, {new})
    assert [(c.old, c.new, c.rule) for c in got] == [("OLD", new, "A7c")]
    assert code_changes({"OLD"}, p, {new, "OLD"}) == []  # still trading: no change
    assert code_changes({"OLD"}, p, {new}, {"OLD": {}}) == []  # already recorded
    assert p.truncate(p.dates[-2]).aliases["OLD"][0] == new


def test_BF_D19_alias_chains_and_journal_mapping() -> None:
    codes = ["AAA", "BBB", "CCC"]
    pairs = [DupPair(0, 1, "A7b", 1.0), DupPair(1, 2, "A7c", 0.999)]
    assert resolve_aliases(codes, pairs) == {
        "AAA": ("CCC", "A7b", 1.0),
        "BBB": ("CCC", "A7c", 0.999),
    }
    j = Journal.sqlite()
    j.add_identity("AAA", "BBB", "PROPOSED", "A7b", Decimal(1), "system", "t")
    j.add_identity("BBB", "CCC", "CONFIRMED", "OWNER", None, "owner", "t")
    assert j.identity_map() == {"AAA": "CCC", "BBB": "CCC"}
    assert j.map_codes({"AAA": 5, "CCC": 2, "DDD": 1}) == {"CCC": 7, "DDD": 1}
    j.add_identity("AAA", "BBB", "REJECTED", "OWNER", None, "owner", "t")
    assert j.identity_map() == {"BBB": "CCC"}
