"""External dead-man monitor check-ins (DAT-12, MON-01).

A silent pipeline must alert through the external monitor: every pipeline job
checks in when it runs, and reports failure explicitly, so that a missing
check-in is noticed by the monitor itself (healthchecks.io style: ``<url>`` on
success, ``<url>/fail`` on failure). The URL is a Docker secret
(``healthchecks_url``). Arming broker-day check-ins and the heartbeat are M5.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from trader.secrets import SecretValue

Pinger = Callable[[str], None]


@dataclass
class DeadManMonitor:
    base_url: Callable[[], SecretValue]
    ping: Pinger

    def checkin(self, check: str, *, ok: bool = True) -> None:
        url = f"{self.base_url().reveal().rstrip('/')}/{check}"
        self.ping(url if ok else f"{url}/fail")

    @contextmanager
    def job(self, check: str) -> Iterator[None]:
        """Check in when the job ends: success, or ``/fail`` if it raised."""
        try:
            yield
        except BaseException:
            self.checkin(check, ok=False)
            raise
        self.checkin(check)
