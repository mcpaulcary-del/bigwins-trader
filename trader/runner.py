"""B-fast jobs that tie the pieces together (FD §4.2, §21.1 BF4).

Only the reconciliation-and-page job lives here in B-fast; the APScheduler wiring of
every daily job (16:30 reconcile, 22:20 decide, 22:45 report, 15:45 submit) is listed
in ``NEXT.md``.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from trader.approval import ChatTransport, broadcast
from trader.broker.base import Broker
from trader.journal import Journal
from trader.reconcile import ReconResult, reconcile
from trader.risk import SafetyLevel, worst


def reconcile_and_page(
    journal: Journal,
    broker: Broker,
    book: str,
    transport: ChatTransport,
    chats: Iterable[int],
    now: datetime,
) -> ReconResult:
    """Positions to the unit, cash to the cent; any break latches HALTED_INTEGRITY and
    pages the owner in the same call (BW-RSK-27; BF4: "halts and pages within 5 minutes")."""
    r = reconcile(
        journal.positions(book),
        journal.cash(book),
        journal.map_codes(broker.positions()),  # BF-D19: a broker still on an old code
        broker.account().ledger_cash,
    )
    if not r.ok:
        level = worst(journal.safety_level(), SafetyLevel.HALTED_INTEGRITY)
        journal.set_safety(
            level, "reconciliation break: " + "; ".join(r.breaks)[:180], "recon", now
        )
        broadcast(transport, chats, "PAGE " + book + ": HALTED_INTEGRITY\n" + "\n".join(r.breaks))
    return r
