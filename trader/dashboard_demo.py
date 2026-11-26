"""Demo data for the phone app (BF-D37, BF-D43): a short paper run of the real app on
synthetic prices (the mock gateway, the owner approving every batch by code), written
to a SQLite journal that the app then opens read-only. The run ends on a month-end
decision, so the demo shows a batch waiting for approval the next morning, and every
message the app sent is in the inbox. For screenshots and tests only; every screen says
DEMO, and the demo's actions are simulated (``demo_control``): nothing here touches a
broker, Telegram, Web Push, the server or a real journal.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import numpy as np

from trader.app_control import Control
from trader.app_notify import AppNotifier, classify
from trader.app_store import get_state, set_state
from trader.approval import ApprovalBot, FakeTransport, Markup, TotpVerifier
from trader.bf_app import AppSettings, BfApp, dry_run, mock_auction, owner_approves_all
from trader.broker.ibkr import IbkrPaperBroker, IbkrSettings
from trader.broker.mock_gateway import MockGateway
from trader.broker.paper_sim import SimBroker
from trader.constants import ASX_TZ
from trader.journal import Journal
from trader.lines.emg2 import Emg2_20Params
from trader.panel import PricePanel
from trader.secrets import SecretValue

DEMO_SEED = "JBSWY3DPEHPK3PXP"  # a public test seed (RFC 4648 example), demo only
DEMO_VERSION = {"version": "EMG2-18 C6 v1.0", "id": "demo0000v100", "config": "demo",
                "code": "demo", "commit": "demo"}  # fmt: skip


def _sessions(n: int, start: date = date(2023, 1, 2)) -> tuple[date, ...]:
    out: list[date] = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return tuple(out)


def synthetic_panel(n_rows: int = 330, n_ent: int = 800, seed: int = 7) -> PricePanel:
    """Random-walk prices and traded values (the same recipe as the app's tests)."""
    rng = np.random.default_rng(seed)
    drift = rng.normal(0.0003, 0.001, n_ent)
    vol = rng.uniform(0.01, 0.05, n_ent)
    r = rng.normal(drift, vol, (n_rows, n_ent))
    close = np.round(2.0 * np.exp(np.cumsum(r, axis=0)) * rng.uniform(0.2, 5.0, n_ent), 3)
    tv = np.exp(rng.normal(13.0, 1.6, n_ent)) * np.exp(rng.normal(0, 0.5, (n_rows, n_ent))) * 50
    ret = np.full_like(close, np.nan)
    ret[1:] = close[1:] / close[:-1] - 1
    ents = tuple(f"S{j:03d}" for j in range(n_ent))
    dts = _sessions(n_rows)
    return PricePanel(
        as_of=dts[-1], dates=dts, entities=ents, close=close, ret=ret, tv=tv,
        sec_class=dict.fromkeys(ents, "ORD"),
    )  # fmt: skip


@dataclass(frozen=True)
class Demo:
    journal_path: Path
    sessions: tuple[date, ...]
    last_day: date
    index: Callable[[], list[tuple[date, float]]]
    prices: Callable[[str], list[tuple[date, float]]] | None = None  # BF-D66 (synthetic)
    now: datetime = datetime(2024, 1, 1, tzinfo=ASX_TZ)  # the demo's "now": the morning after
    scorecard: Path | None = None  # BF-D75: a made-up research scorecard
    info_dir: Path | None = None  # BF-D78: a made-up announcements archive


class _InboxTransport(FakeTransport):
    """The demo's transport: as FakeTransport, and every message also goes to the inbox
    (as the phone app would get it)."""

    def __init__(self) -> None:
        super().__init__()
        self.notifier: AppNotifier | None = None

    def send(self, chat_id: int, text: str) -> None:
        super().send(chat_id, text)
        if self.notifier is not None:
            self.notifier.notify(text)

    def send_markup(self, chat_id: int, text: str, markup: Markup) -> int | None:
        n = super().send_markup(chat_id, text, markup)
        if self.notifier is not None:
            self.notifier.notify(text, "approval" if classify(text) != "page" else "page",
                                 "/orders")  # fmt: skip
        return n


def build_demo(path: Path, days: int = 45, random_twins: int = 20) -> Demo:
    """Run the app for about ``days`` sessions from a start decision, ending on a
    month-end decision, and keep the journal."""
    panel = synthetic_panel()
    path.unlink(missing_ok=True)

    def closes(day: date) -> dict[str, Decimal]:
        k = panel.dates.index(day)
        return {
            e: Decimal(repr(float(c)))
            for e, c in zip(panel.entities, panel.close[k], strict=True)
            if not np.isnan(c)
        }

    def panels(day: date) -> PricePanel:
        return panel.truncate(day)

    gw = MockGateway(cash=10000.0)
    broker = IbkrPaperBroker(IbkrSettings("gw-paper", 4004, 21, "DU1234567"), ib_factory=lambda: gw)
    broker.connect()
    j = Journal.sqlite(str(path))
    start = panel.dates[270]
    s = AppSettings(
        chats=frozenset({1}), start_date=start, params=Emg2_20Params(skip_lottery=False),
        random_twins=random_twins,
    )  # fmt: skip
    for book in (s.book, s.sim_book):
        j.add_cash(
            book,
            "DEPOSIT",
            Decimal(10000),
            "demo paper deposit",
            datetime.combine(start, time(9, 0), ASX_TZ),
        )  # dated the demo's first day
    sim = SimBroker(cash=Decimal(10000), half_spread=s.sim_half_spread)
    tr = _InboxTransport()
    app = BfApp(
        s, j, broker, sim, tr, TotpVerifier(SecretValue(DEMO_SEED)),
        panel.dates, panels, closes,
    )  # fmt: skip
    tr.notifier = AppNotifier(j, None, clock=lambda: app.now)
    app.strategy = dict(DEMO_VERSION)  # BF-D45: every decision is stamped
    run = list(panel.dates[270 : 270 + days])
    ends = [i for i, (a, b) in enumerate(pairwise(run)) if a.month not in (b.month, start.month)]
    if ends:  # end on a month-end decision: its batch waits for approval the next morning
        run = run[: ends[-1] + 1]
    dry_run(app, run, {}, owner_approves_all(app, DEMO_SEED), mock_auction(gw, closes))
    nxt = panel.dates[panel.dates.index(run[-1]) + 1]
    now = datetime.combine(nxt, time(10, 40), ASX_TZ)
    set_state(j, "heartbeat", {"ok": True, "error": "", "every_s": 300}, now - timedelta(minutes=2))
    set_state(j, "host-status", {
        "load1": 0.18, "cpus": 2, "mem_used_pct": 41, "disk_used_pct": 37,
        "uptime_s": 9 * 86400 + 3600, "tailscale": "connected",
        "code_version": "demo build", "asx": "open", "onedrive": True,
        "containers": [{"name": n, "state": "Up 9 days"}
                       for n in ("trader", "dashboard", "db", "gw-paper")],
        "log": ["DEMO log: scheduler idle, next job 14:30 remind",
                "DEMO log: decision batch planned, waiting for approval"],
    }, now - timedelta(seconds=40))  # fmt: skip
    set_state(j, "strategy-running", dict(DEMO_VERSION), now - timedelta(days=1))
    from trader.backups import record_result

    for k in range(3, 0, -1):  # BF-D64: a few nights of (DEMO) backups and a restore test
        local = {"archive": "bigwins-demo.tar.age", "size": 48_000_000 + k * 1_200_000,
                 "files": 1840}  # fmt: skip
        record_result(j, {"ok": True, "kind": "backup", "at": "demo", "local": local,
                          "remote": {"ok": True}, "onedrive": True},
                      now - timedelta(days=k, hours=-13))  # fmt: skip
    record_result(j, {"ok": True, "kind": "restore_test", "files": 1840, "ledger_files": 3,
                      "journal_dump": True}, now - timedelta(hours=10))  # fmt: skip
    set_state(j, "update-available", {
        "ahead": 2, "head": "a" * 40, "remote": "b" * 40, "previous": "c" * 40, "strategy": True,
        "reasons": ["strategy setting: live_emg2_20"], "files": ["config/bfast.yaml"],
        "subject": "DEMO: keep zone 45% (example)",
        "notes": {"version": "EMG2-18 C6 v1.1", "what": "Keep zone widened from the top "
                  "40% to the top 45% of band C (an example, DEMO).", "why": "Fewer sells of "
                  "names that are still strong (example).", "tested": "Full test suite and the "
                  "record replay (example).", "takes_effect": "Tonight's out-of-cycle decision "
                  "(immediate mode), orders for your approval."},
    }, now - timedelta(minutes=5))  # fmt: skip
    demo_dr(j, now, nxt)  # BF-D82..BF-D86
    held = sorted(c for c, q in j.positions(s.book).items() if q)
    vals = [(k.rsplit(":", 1)[1], str(r["value"])) for k, r in j.job_records(f"value:{s.book}:")]
    info_dir = path.parent / "demo_info"
    scorecard = path.parent / "demo_scorecard.csv"
    demo_ops(j, info_dir, scorecard, held, panel.dates, nxt, now, vals)
    j.engine.dispose()
    k0 = panel.dates.index(run[0])
    mean = np.nanmean(panel.close / panel.close[k0], axis=1)  # an equal-weight demo index
    lvl = [(d, float(x)) for d, x in zip(panel.dates, mean, strict=True)]
    col = {c: k for k, c in enumerate(panel.entities)}

    def prices(code: str) -> list[tuple[date, float]]:
        k = col.get(code)
        if k is None:
            return []
        return [(d, float(c)) for d, c in zip(panel.dates[: panel.dates.index(nxt) + 1],
                                               panel.close[:, k], strict=False)
                if np.isfinite(c) and c > 0]  # fmt: skip

    return Demo(path, panel.dates, run[-1], lambda: lvl, prices, now, scorecard, info_dir)


DEMO_HEADS = (  # made-up headlines (no real company); flags: raise, halt, takeover, director
    ("Quarterly Activities Report", 1),
    ("Change of Director's Interest Notice", 0),
    ("Trading Halt", 1),
    ("Proposed issue of securities - placement", 1),
    ("Investor Presentation", 0),
    ("Receipt of unsolicited proposal - non-binding indicative offer", 1),
    ("Change of Director's Interest Notice", 0),
    ("Annual General Meeting results", 0),
)
DEMO_3Y = (  # made-up Appendix 3Y texts in the layout pdftotext gives (synthetic)
    """                        Appendix 3Y
                        Change of Director's Interest Notice
                        Part 1 - Change of director's relevant interests in securities
                         Date of change                                     {d}
                         Class                                              Fully paid ordinary shares
                         Number acquired                                    {n:,}
                         Number disposed                                    Nil
                         Value/Consideration                                ${v:,.2f}
                         Nature of change                                   On-market trade
                         Example: on-market trade, off-market trade, exercise of options
                        Part 2 - Change of director's interests in contracts
""",
    """                        Appendix 3Y
                        Change of Director's Interest Notice
                        Part 1 - Change of director's relevant interests in securities
                         Date of change                                     {d}
                         Class                                              Performance Rights
                         Number acquired                                    {n:,}
                         Number disposed                                    Nil
                         Value/Consideration                                Nil
                         Nature of change                                   Issue of performance rights under the
                         Example: on-market trade, off-market trade,        employee incentive plan
                        Part 2 - Change of director's interests in contracts
""",
)


def demo_pdf(text: str) -> bytes:
    """A one-page PDF saying ``text`` (made up; nothing is fetched)."""
    safe_t = "".join(c for c in text if c.isalnum() or c in " :-.,")[:80]
    stream = f"BT /F1 14 Tf 40 780 Td ({safe_t}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]  # fmt: skip
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, xref)  # fmt: skip


DEMO_BOOKS = {"REF": "EMG2_18_REF", "EMG2": "EMG2_10k", "H82": "H82_10k", "MOM": "MOM_10k",
              "BLIND3": "BLIND3_10k", "SWEEP": "EMG2_18_SIM_BT_C6_SWEEP",
              "WIDE": "EMG2_18_SIM_BT_C6_WIDE", "FIP": "EMG2_18_SIM_BT_C6_FIP",
              "MOON_TOP5": "EMG2_MOON_TOP5", "MOON_NOLOT5": "EMG2_MOON_NOLOT5",
              "MOON_LEG2": "MOON_LEG2"}  # fmt: skip


def demo_ops(j: Journal, info_dir: Path, scorecard: Path, held: list[str],
             sessions: tuple[date, ...], nxt: date, now: datetime,
             vals: list[tuple[str, str]]) -> None:  # fmt: skip
    """BF-D75..BF-D80 demo data, all made up: a research scorecard, an announcements
    archive for the held codes (headlines, two Appendix 3Y texts, ASIC short positions),
    the archive's last run (one day late, so the alarm shows) and a previous-version twin."""
    import csv
    import gzip

    from trader.ops_view import KEPT_LINES

    rng = np.random.default_rng(11)
    with scorecard.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["asof", "book", "kind", "capital", "nav", "return_since_start", "vs_a200"])
        for lid, _, _ in KEPT_LINES:
            r = float(rng.normal(0.01, 0.04))
            w.writerow([str(nxt), DEMO_BOOKS.get(lid, lid), "demo", 10000, round(10000 * (1 + r), 2),
                        round(r, 5), round(r - 0.012, 5)])  # fmt: skip
    k = sessions.index(nxt)
    days = list(sessions[max(0, k - 60) : k])
    for i, d in enumerate(days[:-1]):  # the last session is "not collected yet" (late)
        dd = info_dir / "asx_notices" / str(d)
        (dd / "pdf").mkdir(parents=True, exist_ok=True)
        rows = []
        for c_i, code in enumerate(held[:6]):
            if (i + c_i) % 7:
                continue
            head, ps = DEMO_HEADS[(i + c_i) % len(DEMO_HEADS)]
            ids = f"{9_000_000 + i * 100 + c_i:08d}"
            hr = 8 + c_i
            rows.append([code, f"{d:%d/%m/%Y}",
                         f"{hr - 12 * (hr > 12)}:{15 + i % 40:02d} {'pm' if hr >= 12 else 'am'}",
                         ps, head, ids, int("Interest" in head or "issue" in head)])  # fmt: skip
            if ps:  # BF-D92: a made-up one-page PDF, as the archive stores them
                (dd / "pdf" / f"{code}_{ids}.pdf").write_bytes(demo_pdf(f"DEMO: {head}"))
            if "Interest" in head:
                t = DEMO_3Y[(i + c_i) % 2].format(
                    d=f"{d:%d %B %Y}", n=10000 + 500 * i, v=5250.0 + i
                )
                (dd / "pdf" / f"{code}_{ids}.txt").write_text(t)
        if i == len(days) - 2:  # BF-D92: the News tab's latest day has something to show
            for c_i, (code, k) in enumerate(zip(held[6:9], (2, 5, 4), strict=False)):
                head, ps = DEMO_HEADS[k]
                ids = f"{9_500_000 + c_i:08d}"
                rows.append([code, f"{d:%d/%m/%Y}", f"{9 + c_i}:{5 + 20 * c_i:02d} am", ps, head,
                             ids, 0])  # fmt: skip
                if ps:
                    (dd / "pdf" / f"{code}_{ids}.pdf").write_bytes(demo_pdf(f"DEMO: {head}"))
        rows += [[f"Z{n:02d}", f"{d:%d/%m/%Y}", "9:00 am", 0, "Daily fund update", f"{n:08d}", 0]
                 for n in range(3)]  # fmt: skip
        with (dd / "list.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["code", "date", "time", "price_sensitive", "headline", "ids_id", "kept"])
            w.writerows(rows)
        (dd / "DONE").write_text("{}")
    sd = info_dir / "asic_short"
    sd.mkdir(parents=True, exist_ok=True)
    for d in (days[-35], days[-5]):
        body = "Product,Product Code,Reported Short Positions,Total Product in Issue," \
               "% of Total Product in Issue Reported as Short Positions\n" + "".join(
                   f"DEMO COMPANY {c},{c},{1000 * (n + 1)},{10**7},{(n + 1) * 0.37 + (d.day % 3) * 0.1:.4f}\n"
                   for n, c in enumerate(held))  # fmt: skip
        with gzip.open(sd / f"RR{d:%Y%m%d}-001-SSDailyAggShortPos.csv.gz", "wt") as f:
            f.write(body)
    set_state(j, "info-archive-last", {"ok": True, "day": str(days[-2]), "rows": 690, "pdfs": 118},
              now - timedelta(hours=26))  # fmt: skip
    if len(vals) > 5:
        since = vals[0][0]
        new = [[d, float(v)] for d, v in vals]
        prev = [[d, round(float(v) * (1 - 0.0004 * i), 2)] for i, (d, v) in enumerate(vals)]
        set_state(j, "prev-twin", {"ok": True, "since": since, "to": vals[-1][0], "capital": 10000,
                                   "new": new, "prev": prev, "new_label": "EMG2-18 C6 v1.1 (demo)",
                                   "prev_label": "EMG2-18 C6 v1.0 (demo)"},
                  now - timedelta(hours=9))  # fmt: skip


def demo_dr(j: Journal, now: datetime, nxt: date) -> None:
    """BF-D82..BF-D86 (DEMO): the presence clock, the passphrase state, renewal dates."""
    set_state(j, "presence-since", {"at": (now - timedelta(days=30)).isoformat()}, now)
    set_state(j, "owner-presence", {"last": (now - timedelta(days=3, hours=2)).isoformat(),
                                    "what": "Approve all (DEMO)"}, now)  # fmt: skip
    set_state(j, "app-passphrase", {"set": False}, now)
    set_state(j, "reminders", {"flex_token": (nxt + timedelta(days=21)).isoformat(),
                               "card": (nxt + timedelta(days=140)).isoformat()}, now)  # fmt: skip
    hs = get_state(j, "host-status")
    if hs is not None:
        set_state(j, "host-status", {**hs[0], "signing": "warn", "presence_ping_set": True,
                                     "presence_ping": str(nxt)}, hs[1])  # fmt: skip


def demo_control(j: Journal, demo: Demo) -> Control:
    """The demo's action screens: the real confirm screens on the demo journal (read
    only), every action simulated and labelled DEMO; nothing is written."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from trader.app_notify import b64url

    bot = ApprovalBot(j, FakeTransport(), TotpVerifier(SecretValue(DEMO_SEED)), frozenset(),
                      allowed_logins=frozenset({"demo"}))  # fmt: skip
    key = (
        ec.generate_private_key(ec.SECP256R1())
        .public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    )
    return Control(j, bot, frozenset({"demo"}), clock=lambda: demo.now, demo=True,
                   vapid_public=b64url(key), market_open=lambda now: False,
                   sessions=lambda: demo.sessions)  # fmt: skip
