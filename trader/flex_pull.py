"""Scheduled IBKR Activity Flex download into the Flex inbox (BF-D27). PAPER ONLY.

The broker book's dividends and corporate actions are booked from IBKR's own records
(BF-D23): Activity Flex XML files in ``data.flex_inbox``, read before every 16:30
reconciliation. This module fetches them with the M1 Flex Web Service client
(``trader.data.flex.FlexClient``: ``SendRequest`` with ``fd``/``td`` then
``GetStatement``, a User-Agent, 1 request a second / 10 a minute) at the session's
``FLEX_PULL_SLOTS`` before the reconciliation:

* **target**: the statement up to the previous ASX session (IBKR publishes D's in the
  Sydney afternoon of D+1, R37), from the day after the last statement pulled (at most
  ``max_days`` back; at least ``lookback_days``, overlap is harmless because booking
  is idempotent by IBKR's transaction / action ids);
* **idempotent**: one file per period, ``flex_<fd>_<td>.xml``, written atomically
  (temporary name, then rename; the inbox reader only reads ``*.xml``); a file
  already there or a pull already recorded for the day is not fetched again;
* **retries**: ``attempts`` tries a slot with ``backoff_s`` between them, within
  ``budget_s`` a slot (the scheduler does not poll Telegram during a job, so a slot
  stays well under the 60 s ``/kill`` bound), then again at the next slot;
* **checks**: the statement must parse, every account must be a paper ``DU`` account
  (a statement of any other account is refused and paged) and it must reach the
  target date (else "not ready yet");
* **page**: the owner is paged once a day when the statement is still missing at the
  last slot before the reconciliation, or at once on an error that will not fix
  itself (the token or query id missing from the Docker secrets, a token IBKR
  refuses, a non-paper account).

The token and query id are read **only from the Docker secrets** (``ibkr_flex_token``,
``ibkr_flex_query_id`` under ``/run/secrets``; ``trader.secrets``), at each pull, never
from the configuration, the environment or the repository; they never appear in a
message, a log line or the journal (``SecretValue``).
"""

from __future__ import annotations

import os
import time as _time
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from trader.data.flex import (
    FlexClient,
    FlexError,
    FlexNotReadyError,
    FlexStatement,
    FlexTransport,
    RateLimiter,
    parse_statements,
)
from trader.data.store import RawStore, RawStoreError
from trader.secrets import SecretError, SecretValue, read_secret

# Before the 16:30 reconciliation (bf_app.DAY_JOBS); the last one pages when missing
FLEX_PULL_SLOTS: tuple[str, ...] = ("13:05", "14:05", "15:05", "16:05", "16:25")
FLEX_PAGE_SLOT = FLEX_PULL_SLOTS[-1]
REQUEST_TIMEOUT_S = 10.0


class FlexPullRefusedError(FlexError):
    """A statement the inbox must not take (not a paper account)."""


@dataclass(frozen=True)
class PullResult:
    status: str  # PULLED | PRESENT | NOT_READY | FAILED | REFUSED | NO_SECRET
    path: Path | None = None
    from_date: date | None = None
    to_date: date | None = None
    tries: int = 0
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("PULLED", "PRESENT")

    @property
    def fatal(self) -> bool:
        """An error the next slot will not fix by itself: page at once."""
        return self.status in ("REFUSED", "NO_SECRET") or (
            self.status == "FAILED" and "code 101" in self.note  # 1012/1015 token
        )


def inbox_name(fd: date, td: date) -> str:
    return f"flex_{fd:%Y%m%d}_{td:%Y%m%d}.xml"


def pull_window(
    target: date, last_pulled: date | None, lookback_days: int = 7, max_days: int = 30
) -> tuple[date, date]:
    """``(fd, td)``: up to ``target``, from the day after the last statement pulled,
    covering at least ``lookback_days`` and at most ``max_days`` days."""
    lo = target - timedelta(days=max_days - 1)
    fd = target - timedelta(days=lookback_days - 1)
    if last_pulled is not None and last_pulled + timedelta(days=1) < fd:
        fd = last_pulled + timedelta(days=1)
    return max(fd, lo), target


def check_paper(statements: list[FlexStatement], target: date) -> None:
    """A statement of a paper (``DU``) account that reaches ``target``."""
    for st in statements:
        if not st.account_id.startswith("DU"):
            raise FlexPullRefusedError(
                f"statement of account {st.account_id[:2]}... is not a paper (DU) account"
            )
    if max(st.to_date for st in statements) < target:
        raise FlexNotReadyError(f"statement ends before {target}")


def urllib_transport(
    url: str, params: Mapping[str, str], headers: Mapping[str, str]
) -> bytes:  # pragma: no cover - network
    """The production transport (stdlib; proxy and CA bundle from the environment)."""
    if not url.startswith("https://"):
        raise FlexError("Flex is reached over https only")
    req = urllib.request.Request(  # noqa: S310 - https checked above
        f"{url}?{urllib.parse.urlencode(params)}", headers=dict(headers)
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:  # noqa: S310
        body: bytes = resp.read()
    return body


@dataclass
class FlexPuller:
    """Fetch the paper account's Activity Flex statement into ``inbox`` (BF-D27)."""

    inbox: Path
    raw: RawStore  # every response kept unchanged (DAT-09), as the M1 client does
    transport: FlexTransport = urllib_transport
    token: Callable[[], SecretValue] = field(default=lambda: read_secret("ibkr_flex_token"))
    query_id: Callable[[], SecretValue] = field(default=lambda: read_secret("ibkr_flex_query_id"))
    attempts: int = 2
    backoff_s: float = 5.0
    budget_s: float = 40.0
    max_polls: int = 5
    lookback_days: int = 7
    max_days: int = 30
    clock: Callable[[], float] = _time.monotonic
    sleep: Callable[[float], None] = _time.sleep

    def _client(self, deadline: float) -> FlexClient:
        def bounded(url: str, params: Mapping[str, str], headers: Mapping[str, str]) -> bytes:
            if self.clock() > deadline:
                raise FlexNotReadyError("time budget of the slot used up")
            return self.transport(url, params, headers)

        return FlexClient(
            bounded, self.raw, RateLimiter(clock=self.clock, sleep=self.sleep),
            token=self.token, query_id=self.query_id, max_polls=self.max_polls,
        )  # fmt: skip

    def pull(self, target: date, last_pulled: date | None, now: datetime) -> PullResult:
        fd, td = pull_window(target, last_pulled, self.lookback_days, self.max_days)
        path = self.inbox / inbox_name(fd, td)
        if path.is_file():
            return PullResult("PRESENT", path, fd, td, 0, "already in the inbox")
        try:  # the secrets first: without them no request is made
            self.token()
            self.query_id()
        except SecretError as e:
            return PullResult("NO_SECRET", None, fd, td, 0, str(e)[:200])
        deadline = self.clock() + self.budget_s
        note, status = "", "NOT_READY"
        tries = 0
        for k in range(self.attempts):
            if k:
                if self.clock() + self.backoff_s > deadline:
                    break
                self.sleep(self.backoff_s)
            tries += 1
            try:
                raw, sts = self._client(deadline).fetch(fd, td, now)
                check_paper(sts, td)
                body = RawStore.read(raw.path)
                parse_statements(body)  # the inbox reader must read it back
                self._write(path, body)
                return PullResult("PULLED", path, fd, td, tries, f"{len(sts)} statement(s)")
            except FlexPullRefusedError as e:
                return PullResult("REFUSED", None, fd, td, tries, str(e)[:200])
            except FlexNotReadyError as e:
                status, note = "NOT_READY", str(e)[:200]
            except (FlexError, OSError, RawStoreError) as e:
                status, note = "FAILED", f"{type(e).__name__}: {e}"[:200]
        return PullResult(status, None, fd, td, tries, note)

    def _write(self, path: Path, body: bytes) -> None:
        self.inbox.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.part")
        tmp.write_bytes(body)
        os.replace(tmp, path)  # atomic: the reader sees no half file
