"""BF-D32: the paper dry run while the book's real L15 state is FUND.

Extra decisions with the band-trend state forced to EMG2 make the paper sessions carry
real 18-share buy and sell flows; a ``REAL`` decision exercises the FUND switch. Paper
only: the schema, the DU/live guards and the app refuse anything else.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.test_bf_band_trend import APP_PANEL, BT, CHAT, DAYS, FUND, P18, SEED, _closes, _panel
from trader.approval import FakeTransport, TotpVerifier
from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
from trader.bfast_config import BfastConfig
from trader.broker.base import LiveTradingRefusedError
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.journal import Journal, Status
from trader.lines.band_trend import BandTrend, BandTrendParams
from trader.panel import PricePanel
from trader.secrets import SecretValue
from trader.yamlio import load_yaml

CFG = Path(__file__).resolve().parent.parent / "config" / "bfast.yaml"
D0 = DAYS[0]
D_SWITCH, D_BACK = DAYS[3], DAYS[8]  # the FUND switch (REAL), then EMG2 forced again
PLAN = ((D0, "EMG2"), (D_SWITCH, "REAL"), (D_BACK, "EMG2"))


def _always_fund(
    panel: PricePanel, params: BandTrendParams | None = None, **kw: object
) -> BandTrend:
    """The record's situation: the rule says FUND on every decision day."""
    return BandTrend(
        panel.as_of.isoformat(), "FUND", 0.9, 1.0, ((panel.as_of.isoformat(), 0.9, 200),)
    )


def _app(forced: tuple[tuple[date, str], ...] = PLAN, until: date | None = None) -> Any:
    gw = MockGateway(cash=10000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    j = Journal.sqlite()
    s = AppSettings(chats=frozenset({CHAT}), start_date=D0, params=P18, random_twins=3,
                    band_trend=BT, forced_states=forced, dry_run_until=until or DAYS[-1])  # fmt: skip
    for book in (s.book, s.sim_book):
        j.add_cash(book, "DEPOSIT", Decimal(10000), "paper deposit")
    sim = SimBroker(cash=Decimal(10000), half_spread=s.sim_half_spread)
    tr = FakeTransport()
    app = BfApp(s, j, broker, sim, tr, TotpVerifier(SecretValue(SEED)), APP_PANEL.dates,
                _panel, _closes)  # fmt: skip
    return app, gw, tr


def test_BF_D32_forced_emg2_dry_run_gives_share_flows_and_the_fund_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("trader.bf_app.band_trend", _always_fund)
    app, gw, tr = _app()
    days = DAYS[:14]
    summ = dry_run(app, days, {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    book = app.s.book
    # start, forced EMG2: the canary is a share, then the other 17 shares
    can = app.j.intents_of(f"{book}-{D0}-C")
    assert len(can) == 1 and can[0][0].entity != FUND and can[0][1] == Status.FILLED
    rest = app.j.intents_of(f"{book}-{D0}-S")
    assert len(rest) == 17 and all(it.side.value == "BUY" and it.entity != FUND for it, _ in rest)
    # REAL on D_SWITCH: the rule's FUND: every share sold, the fund bought (the switch)
    sw = app.j.intents_of(f"{book}-{D_SWITCH}-B")
    sells = [(it, st) for it, st in sw if it.side.value == "SELL"]
    assert len(sells) == 18 and sum(st == Status.FILLED for _, st in sells) >= 10
    assert all(st in (Status.FILLED, Status.EXPIRED) for _, st in sells)  # L7 carries the rest
    assert [it.entity for it, _ in sw if it.side.value == "BUY"] == [FUND]
    # EMG2 forced again: the fund sold, the EMG2-18 picks bought
    back = app.j.intents_of(f"{book}-{D_BACK}-B")
    assert [it.entity for it, _ in back if it.side.value == "SELL"] == [FUND]
    assert sum(1 for it, _ in back if it.side.value == "BUY") >= 15
    pos = app.j.positions(book)
    assert FUND not in pos and len(pos) >= 15
    # sessions with orders filled, reconciled to the cent every session (go-live item 2)
    filled_days = {f.executed_at.date() for f in app.j.fills(book)}
    assert len(filled_days) >= 5
    assert summ.safety == "NORMAL" and summ.recon and all(summ.recon.values())
    assert summ.positions == app.broker.positions()
    # the twins take the same forced decisions (L13 comparison intact)
    for d in (D_SWITCH, D_BACK):
        for twin in (app.s.sim_book, "EMG2_18_RND_s001"):
            assert app.j.intents_of(f"{twin}-{d}-B"), (twin, d)
    # every forced decision says so; the REAL one shows the rule's state
    heads = [t for _, t in tr.outbox if t.startswith("Decision")]
    assert sum("FORCED (paper dry run, BF-D32; the L15 rule says FUND" in t for t in heads) == 2
    assert any("state: FUND (band" in t for t in heads)
    assert app.state_line(D_BACK).startswith("state: EMG2 FORCED")


def test_BF_D32_no_forcing_after_until_or_without_the_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trader.bf_app.band_trend", _always_fund)
    app, _, _ = _app(until=DAYS[1])  # the plan's later dates are past ``until``
    assert app.decision_kind(D_SWITCH) is None and app.decision_kind(D_BACK) is None
    assert app.decision_kind(D0) == "S"
    plain, _, _ = _app(forced=())
    assert plain.decision_kind(D_SWITCH) is None
    s = AppSettings(forced_states=PLAN, dry_run_until=DAYS[-1])
    assert s.forced(D_SWITCH) == "REAL" and s.forced(DAYS[1]) is None


def test_BF_D32_refused_for_a_non_paper_broker() -> None:
    sim = SimBroker(cash=Decimal(10000), half_spread=Decimal("0.005"))
    live_like = replace(sim, is_paper=False)
    s = AppSettings(chats=frozenset({CHAT}), band_trend=BT, forced_states=PLAN)
    with pytest.raises(LiveTradingRefusedError):
        BfApp(s, Journal.sqlite(), live_like, sim, FakeTransport(), TotpVerifier(SecretValue(SEED)),
              APP_PANEL.dates, _panel, _closes)  # fmt: skip


def _raw() -> dict[str, Any]:
    out: dict[str, Any] = load_yaml(CFG.read_text())
    out["paper_dry_run"] = {
        "until": "2026-12-31",
        "decisions": {"2026-12-01": "EMG2", "2026-12-04": "REAL", "2026-12-10": "EMG2"},
    }
    return out


def test_BF_D32_config_paper_only_and_bounded(tmp_path: Path) -> None:
    cfg = BfastConfig.model_validate(_raw())
    assert (
        cfg.paper_dry_run is not None and cfg.paper_dry_run.decisions[date(2026, 12, 4)] == "REAL"
    )
    from trader.bf_dryrun import settings_from

    s = settings_from(cfg, frozenset({1}), date(2026, 12, 1))
    assert s.forced(date(2026, 12, 10)) == "EMG2" and s.dry_run_until == date(2026, 12, 31)
    for path, value in [
        (("broker", "account_id"), "U1234567"),  # a live account id: the DU guard
        (("broker", "allow_live"), True),
        (("mode",), "live"),
        (("band_trend", "enabled"), False),  # nothing to force
        (("paper_dry_run", "decisions"), {"2027-01-04": "EMG2"}),  # after until
        (("paper_dry_run", "decisions"), {"2026-12-01": "SHARES"}),
        (("paper_dry_run", "decisions"), {}),
    ]:
        raw = _raw()
        node = raw
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = value
        with pytest.raises(ValidationError):
            BfastConfig.model_validate(raw)


def test_BF_D32_run_refuses_an_expired_dry_run(tmp_path: Path) -> None:
    import json

    from trader.bfast_cli import main

    raw = json.loads(json.dumps(_raw(), default=str))
    raw["broker"]["account_id"] = "DU1234567"
    raw["telegram"]["allowed_chat_ids"] = [1]
    raw["paper_dry_run"] = {"until": "2026-01-31", "decisions": {"2026-01-05": "EMG2"}}
    p = tmp_path / "c.yaml"
    p.write_text(json.dumps(raw))
    with pytest.raises(SystemExit, match="paper_dry_run ended on 2026-01-31"):
        main(["run", "--config", str(p)])
