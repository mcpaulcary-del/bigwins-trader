"""Dead-man heartbeat (BF-D41): the trader pings a healthchecks.io check every few
minutes, so healthchecks.io emails / pushes the owner when the pings stop (the server,
Docker or the trader is down: the app itself cannot say so then).

The ping URL is the Docker secret ``healthchecks_url`` (it identifies the check, so it is
secret); ``none`` (or an empty value) keeps the heartbeat off. Only https URLs are used.
The trader's main loop calls ``tick`` on every poll; a ping is sent when ``every_s`` has
passed since the last one. The last result is kept in the journal (app state
``heartbeat``: time, ok, short error without the URL) for the app's Server screen; the
first failure of a streak is written to the owner's inbox (if pings cannot leave the
server, the app may be the only place to see it). The URL never appears in a log or
message.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

from trader.app_store import set_state
from trader.journal import Journal
from trader.secrets import SecretValue

Opener = Callable[..., Any]


def ping_url(secret: SecretValue | None) -> str | None:
    """The URL to ping, or None for "off" (``none`` / empty / not https)."""
    if secret is None:
        return None
    v = secret.reveal().strip()
    if not v or v.lower() == "none":
        return None
    if urlsplit(v).scheme != "https":
        raise ValueError("healthchecks_url must be an https URL or 'none'")
    return v


@dataclass
class Heartbeat:
    url: str | None
    journal: Journal | None = None
    notify: Callable[[str], object] | None = None
    opener: Opener = urllib.request.urlopen
    every_s: int = 300
    timeout_s: int = 10
    last_at: datetime | None = None
    last_ok: bool | None = None
    _streak_told: bool = field(default=False, repr=False)

    @property
    def enabled(self) -> bool:
        return self.url is not None

    def tick(self, now: datetime) -> str:
        """``off`` | ``wait`` | ``ok`` | ``fail``."""
        if self.url is None:
            return "off"
        if self.last_at is not None and now - self.last_at < timedelta(seconds=self.every_s):
            return "wait"
        self.last_at = now
        err = ""
        try:
            req = urllib.request.Request(  # noqa: S310 - https checked in ping_url
                self.url, method="GET", headers={"User-Agent": "bigwins-trader-heartbeat"}
            )
            with self.opener(req, timeout=self.timeout_s) as r:
                status = int(getattr(r, "status", 200))
            ok = 200 <= status < 300
            err = "" if ok else f"HTTP {status}"
        except urllib.error.HTTPError as e:
            ok, err = False, f"HTTP {e.code}"
        except (OSError, ValueError) as e:  # URLError, timeouts, DNS: never the URL itself
            ok, err = False, type(e).__name__
        self.last_ok = ok
        if self.journal is not None:
            set_state(self.journal, "heartbeat",
                      {"ok": ok, "error": err, "every_s": self.every_s}, now)  # fmt: skip
        if ok:
            self._streak_told = False
            return "ok"
        if not self._streak_told and self.notify is not None:
            self._streak_told = True
            self.notify(
                f"Heartbeat ping to healthchecks.io failed ({err}). If it keeps failing, "
                "healthchecks.io will warn you that the server is down. Check the "
                "server's internet connection."
            )
        return "fail"
