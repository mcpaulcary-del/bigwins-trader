"""BF-D27: the scheduled IBKR Flex Web Service download into the Flex inbox before the
16:30 reconciliation: retries, idempotency, a page when the statement is late or
missing, the token from the Docker secret only. Fully mocked: no request leaves."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.test_bf_app import DAYS, SEED, _app, _closes
from trader.approval import FakeTransport
from trader.bf_app import DAY_JOBS, BfApp, at, dry_run, mock_auction, owner_approves_all
from trader.bfast_cli import flex_puller
from trader.bfast_config import DataCfg, load_bfast_config
from trader.broker.mock_gateway import MockGateway
from trader.ca_book import flex_inbox
from trader.corporate_actions import CaKind
from trader.data.flex import GET_URL, SEND_URL
from trader.data.store import RawStore
from trader.flex_pull import FLEX_PAGE_SLOT, FLEX_PULL_SLOTS, FlexPuller, pull_window
from trader.risk import SafetyLevel
from trader.secrets import read_secret

TOKEN = "tok-NOT-A-REAL-TOKEN-41"  # a test value written to a temporary secrets dir
QUERY = "991122"
SEND_OK = b"""<FlexStatementResponse timestamp="x"><Status>Success</Status>
<ReferenceCode>5550001</ReferenceCode><Url>u</Url></FlexStatementResponse>"""
NOT_READY = b"""<FlexStatementResponse timestamp="x"><Status>Fail</Status>
<ErrorCode>1019</ErrorCode><ErrorMessage>Statement generation in progress.</ErrorMessage>
</FlexStatementResponse>"""
BAD_TOKEN = b"""<FlexStatementResponse timestamp="x"><Status>Fail</Status>
<ErrorCode>1012</ErrorCode><ErrorMessage>Token has expired.</ErrorMessage>
</FlexStatementResponse>"""


def _statement(fd: str, td: str, account: str, cash: str) -> bytes:
    return f"""<FlexQueryResponse queryName="t" type="AF"><FlexStatements count="1">
<FlexStatement accountId="{account}" fromDate="{fd}" toDate="{td}" period="" whenGenerated="{td};200000">
<CashTransactions>{cash}</CashTransactions><CorporateActions/>
</FlexStatement></FlexStatements></FlexQueryResponse>""".encode()


class FakeIbkr:
    """The Flex Web Service: ``not_ready`` SendRequests answer 1019 first; then the
    statement of the requested period (``fd``/``td``) with ``cash`` rows."""

    def __init__(
        self, not_ready: int = 0, account: str = "DU1234567", cash: str = "", send: bytes = b""
    ) -> None:
        self.not_ready, self.account, self.cash, self.send = not_ready, account, cash, send
        self.calls: list[tuple[str, dict[str, str], dict[str, str]]] = []
        self._period = ("", "")

    def __call__(self, url: str, params: Mapping[str, str], headers: Mapping[str, str]) -> bytes:
        self.calls.append((url, dict(params), dict(headers)))
        if url == SEND_URL:
            if self.send:
                return self.send
            if self.not_ready > 0:
                self.not_ready -= 1
                return NOT_READY
            self._period = (params["fd"], params["td"])
            return SEND_OK
        assert url == GET_URL and params["q"] == "5550001"
        return _statement(*self._period, self.account, self.cash)


class Clock:
    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.slept.append(s)
        self.t += s


def _secrets(tmp: Path, *, token: bool = True) -> Path:
    d = tmp / "run_secrets"
    d.mkdir()
    if token:
        (d / "ibkr_flex_token").write_text(TOKEN + "\n")
    (d / "ibkr_flex_query_id").write_text(QUERY)
    return d


def _puller(tmp: Path, ibkr: FakeIbkr, secrets: Path, clock: Clock | None = None) -> FlexPuller:
    c = clock or Clock()
    return FlexPuller(
        tmp / "inbox", RawStore(tmp / "raw", "owner"), ibkr,
        token=lambda: read_secret("ibkr_flex_token", secrets),
        query_id=lambda: read_secret("ibkr_flex_query_id", secrets),
        clock=c, sleep=c.sleep,
    )  # fmt: skip


def _started(tmp: Path, ibkr: FakeIbkr, token: bool = True) -> tuple[BfApp, MockGateway, str]:
    app, gw, _ = _app(DAYS[0])
    dry_run(app, DAYS[:6], {}, owner_approves_all(app, SEED), mock_auction(gw, _closes))
    app.flex_pull = _puller(tmp, ibkr, _secrets(tmp, token=token))
    app.flex = flex_inbox(tmp / "inbox")
    held = sorted(app.j.positions(app.s.book))
    return app, gw, held[0]


def _slots(app: BfApp, day: date) -> list[str]:
    """The day's pull slots, then the reconciliation; the pages sent."""
    tr = app.transport
    assert isinstance(tr, FakeTransport)
    n0 = len(tr.outbox)
    for hhmm in FLEX_PULL_SLOTS:
        assert app.run_job("flex_pull", day, at(day, hhmm))
    app.run_job("reconcile", day, at(day, "16:30"))
    return [t for _, t in tr.outbox[n0:] if t.startswith("PAGE")]


def test_BF_D27_slots_run_before_the_1630_reconciliation() -> None:
    times = [t for t, n in DAY_JOBS if n == "flex_pull"]
    rec = next(t for t, n in DAY_JOBS if n == "reconcile")
    assert times == list(FLEX_PULL_SLOTS) and all(t < rec for t in times)
    assert times[-1] == FLEX_PAGE_SLOT and [t for t, _ in DAY_JOBS] == sorted(
        t for t, _ in DAY_JOBS
    )


def test_BF_D27_pulled_once_into_the_inbox_and_booked_at_the_reconciliation(
    tmp_path: Path,
) -> None:
    """The statement to the previous session is fetched at the first slot (token from
    the Docker secret, fd/td), written atomically to ``flex_<fd>_<td>.xml``; later
    slots fetch nothing; the 16:30 reconciliation books IBKR's dividend from it and
    matches the broker; the token is nowhere but in the request to IBKR."""
    ibkr = FakeIbkr()
    app, gw, e = _started(tmp_path, ibkr)
    day, prev = DAYS[7], DAYS[6]
    q = app.j.positions(app.s.book)[e]
    amt = Decimal("0.04") * q
    ibkr.cash = (
        f'<CashTransaction currency="AUD" symbol="{e}" transactionID="T77" type="Dividends" '
        f'amount="{amt}" settleDate="{prev:%Y%m%d}" description="{e} CASH DIVIDEND AUD 0.04 '
        'PER SHARE - FULLY FRANKED"/>'
    )
    gw.cash += float(amt)  # IBKR credited it on the previous session
    pages = _slots(app, day)
    assert pages == []
    fd, td = pull_window(prev, None)
    files = sorted(p.name for p in (tmp_path / "inbox").iterdir())
    assert files == [f"flex_{fd:%Y%m%d}_{td:%Y%m%d}.xml"]  # no temporary file left
    assert len(ibkr.calls) == 2  # SendRequest + GetStatement, at the first slot only
    send = ibkr.calls[0][1]
    assert (send["t"], send["q"], send["fd"], send["td"]) == (
        TOKEN, QUERY, f"{fd:%Y%m%d}", f"{td:%Y%m%d}",
    )  # fmt: skip
    assert all(h["User-Agent"].startswith("asx-trader") for _, _, h in ibkr.calls)
    (b,) = [b for b in app.j.ca_bookings(app.s.book) if b.code == e]
    assert (b.kind, b.cash, b.franked_pct) == (CaKind.DIVIDEND, amt, Decimal(100))
    rec = dict(app.j.job_records(f"recon:{app.s.book}:{day}"))[f"recon:{app.s.book}:{day}"]
    assert rec["ok"] and app.j.safety_level() is SafetyLevel.NORMAL
    (_, pull), *_ = app.j.job_records(f"flex-pull:{day}")
    assert pull["status"] == "PULLED" and pull["to"] == str(td)
    # the token is in no file, journal record or message
    blobs = [p.read_bytes() for p in (tmp_path / "inbox").iterdir()]
    blobs += [str(r).encode() for _, r in app.j.job_records("")]
    blobs += [t.encode() for _, t in app.transport.outbox]  # type: ignore[attr-defined]
    assert not any(TOKEN.encode() in x for x in blobs)
    # next session: the window starts after the last pull; a rerun of a slot is a no-op
    n = len(ibkr.calls)
    assert app.run_job("flex_pull", day, at(day, "16:25")) and len(ibkr.calls) == n
    _slots(app, DAYS[8])
    assert len(ibkr.calls) == n + 2 and len(list((tmp_path / "inbox").iterdir())) == 2
    assert len(app.j.ca_bookings(app.s.book)) == 1  # the overlap books nothing twice


def test_BF_D27_late_statement_retried_each_slot_then_paged_once(tmp_path: Path) -> None:
    ibkr = FakeIbkr(not_ready=10**6)
    app, _, _ = _started(tmp_path, ibkr)
    clock = app.flex_pull.clock  # type: ignore[union-attr]
    assert isinstance(clock, Clock)
    tr = app.transport
    assert isinstance(tr, FakeTransport)
    day = DAYS[7]
    for hhmm in FLEX_PULL_SLOTS[:-1]:
        app.run_job("flex_pull", day, at(day, hhmm))
        assert not [t for _, t in tr.outbox if t.startswith("PAGE")]  # not yet late
    pages = _slots(app, day)  # the last slot (re-runs of earlier slots are no-ops)
    assert len(pages) == 1 and "late/missing" in pages[0] and "NOT_READY" in pages[0]
    assert len(ibkr.calls) == 2 * (len(FLEX_PULL_SLOTS) * 2 - 1)  # 2 tries a slot run
    assert 5.0 in clock.slept  # the backoff between the tries of a slot
    assert not list((tmp_path / "inbox").glob("*.xml"))
    rec = dict(app.j.job_records(f"recon:{app.s.book}:{day}"))[f"recon:{app.s.book}:{day}"]
    assert rec["ok"]  # the reconciliation still runs on the inbox as it is
    assert len(_slots(app, DAYS[8])) == 1  # paged again the next day, once


def test_BF_D27_statement_late_then_arrives_at_a_later_slot_no_page(tmp_path: Path) -> None:
    ibkr = FakeIbkr(not_ready=3)  # slot 1: two tries not ready; slot 2: one more, then ok
    app, _, _ = _started(tmp_path, ibkr)
    day = DAYS[7]
    assert _slots(app, day) == []
    (_, pull), *_ = app.j.job_records(f"flex-pull:{day}")
    assert pull["tries"] == 2 and len(list((tmp_path / "inbox").glob("*.xml"))) == 1
    assert [r["status"] for _, r in app.j.job_records(f"flex-try:{day}")] == ["NOT_READY"]


@pytest.mark.parametrize(
    ("ibkr", "token", "status"),
    [(FakeIbkr(), False, "NO_SECRET"), (FakeIbkr(send=BAD_TOKEN), True, "FAILED"),
     (FakeIbkr(account="U7654321"), True, "REFUSED")],
)  # fmt: skip
def test_BF_D27_errors_that_will_not_fix_themselves_page_at_once(
    tmp_path: Path, ibkr: FakeIbkr, token: bool, status: str
) -> None:
    """No token in the Docker secrets (no request is made), a token IBKR refuses, a
    statement of a non-paper account (not written): paged at the first slot, once."""
    app, _, _ = _started(tmp_path, ibkr, token=token)
    tr = app.transport
    assert isinstance(tr, FakeTransport)
    day = DAYS[7]
    app.run_job("flex_pull", day, at(day, FLEX_PULL_SLOTS[0]))
    pages = [t for _, t in tr.outbox if t.startswith("PAGE")]
    assert len(pages) == 1 and status in pages[0]
    assert len(_slots(app, day)) == 0  # not paged again that day
    assert not list((tmp_path / "inbox").glob("*.xml"))
    if status == "NO_SECRET":
        assert ibkr.calls == []


def test_BF_D27_slot_time_budget_and_file_already_present(tmp_path: Path) -> None:
    clock = Clock()

    class Slow(FakeIbkr):
        def __call__(
            self, url: str, params: Mapping[str, str], headers: Mapping[str, str]
        ) -> bytes:
            clock.t += 38.0  # a slow answer: no time left for a second try
            return super().__call__(url, params, headers)

    ibkr = Slow(not_ready=10**6)
    p = _puller(tmp_path, ibkr, _secrets(tmp_path), clock)
    now = datetime(2026, 12, 4, 3, 5, tzinfo=UTC)
    r = p.pull(date(2026, 12, 3), None, now)
    assert r.status == "NOT_READY" and r.tries == 1 and clock.t <= p.budget_s
    fd, td = pull_window(date(2026, 12, 3), None)
    (tmp_path / "inbox").mkdir(exist_ok=True)
    (tmp_path / "inbox" / f"flex_{fd:%Y%m%d}_{td:%Y%m%d}.xml").write_bytes(b"<x/>")
    n = len(ibkr.calls)
    assert p.pull(date(2026, 12, 3), None, now).status == "PRESENT" and len(ibkr.calls) == n


def test_BF_D27_pull_window() -> None:
    t = date(2026, 12, 3)
    assert pull_window(t, None) == (date(2026, 11, 27), t)  # a week back at least
    assert pull_window(t, date(2026, 12, 2)) == (date(2026, 11, 27), t)
    assert pull_window(t, date(2026, 11, 20)) == (date(2026, 11, 21), t)  # gap covered
    assert pull_window(t, date(2026, 1, 1)) == (date(2026, 11, 4), t)  # at most 30 days


def test_BF_D27_config_has_no_token_and_needs_the_inbox(tmp_path: Path) -> None:
    cfg = load_bfast_config(Path("config/bfast.yaml"))
    assert cfg.data.flex_pull is not None and cfg.data.flex_inbox is not None
    fp = flex_puller(cfg)
    assert fp is not None and fp.inbox == cfg.data.flex_inbox and fp.attempts == 2
    base = cfg.data.model_dump()
    with pytest.raises(ValidationError):  # extra keys are refused: no token in config
        DataCfg.model_validate({**base, "flex_pull": {**base["flex_pull"], "token": "x"}})
    with pytest.raises(ValidationError, match="flex_inbox"):
        DataCfg.model_validate({**base, "flex_inbox": None})
    text = Path("config/bfast.yaml").read_text() + Path("deploy/docker-compose.yml").read_text()
    assert "ibkr_flex_token: {file: ./secrets/ibkr_flex_token}" in text  # a Docker secret
    for line in text.splitlines():
        assert not line.strip().startswith(("token:", "flex_token:", "query_id:"))
