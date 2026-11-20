"""Daily refresh of the price store on the server (BF-D31). PAPER ONLY.

The decision engine reads the forward store (``data.forward_store``,
``trader.data.forward_store.ForwardStore``): per-symbol histories plus one EODHD bulk
file a session under ``raw/bulk_eod``, ``raw/bulk_div`` and ``raw/bulk_splits``
(``AU_<date>__<stamp>.json.gz``). On the research machine the record's scripts append
those files; on the server this module does it, as a scheduled job of the app
(``bf_app.DAY_JOBS``, ``STORE_REFRESH_SLOTS`` after the ASX close and before the
22:15 twin / 22:20 decision):

* **requests**: ``eod-bulk-last-day/AU?date=D`` (closes), ``&type=dividends`` and
  ``&type=splits`` (EODHD's bulk API; one request each);
* **counted call budget** (as DAT-23): every request is recorded in the journal,
  committed, *before* it is sent, at its vendor cost (``bulk_call_cost``; EODHD counts a
  bulk request as 100 calls), per GMT day (EODHD resets at midnight GMT). A request
  that would pass ``calls_per_day`` is not sent: the refresh fails closed and the
  owner is paged;
* **complete or nothing**: the closes are kept only when at least ``min_rows`` rows are
  dated D and at least ``min_share`` of the previous bulk day's count (EODHD's bulk
  file returns each code's *last* row, so an early call holds yesterday's rows);
  otherwise nothing is written and the next slot tries again. Only rows dated D go
  into the store's bulk file (the store appends bulk rows by file date); the vendor's
  response is kept unchanged in the raw store (``raw_dir``, DAT-09);
* **idempotent**: a complete bulk file for D already in the store, or a refresh
  already recorded for D, is not fetched again; files are written atomically
  (temporary name, then rename) and a ``manifest.tsv`` row is appended as the
  record's scripts do;
* **fail closed if stale**: ``last_day()`` is the newest bulk day in the store; the
  app makes **no decision** while it is before the decision day
  (``BfApp._store_stale``: retried until ``RETRY_UNTIL``, then a rule-14 data block
  with a page), and the owner is paged once a day when D is still missing at the last
  slot, or at once on an error the next slot will not fix (no key, budget used up,
  key refused).

The key is read **only from the Docker secret** ``eodhd_api_token``
(``trader.secrets.read_secret``) at each refresh; it never appears in a message, a log
line, the journal, the manifest or an error (transport errors are re-raised without
the URL).
"""

from __future__ import annotations

import contextlib
import gzip
import hashlib
import json
import os
import time as _time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from trader.data.eodhd import BASE_URL, USER_AGENT
from trader.data.store import RawStore, RawStoreError
from trader.journal import Journal
from trader.secrets import SecretError, SecretValue, read_secret
from trader.timeutil import ensure_utc

# After the ASX close (16:10) and before the twin (22:15) / decision (22:20); the last
# slot pages when the day is still missing
STORE_REFRESH_SLOTS: tuple[str, ...] = ("17:35", "18:35", "19:35", "20:35", "21:35", "22:05")
STORE_PAGE_SLOT = STORE_REFRESH_SLOTS[-1]
KINDS: tuple[tuple[str, str | None], ...] = (
    ("bulk_eod", None),
    ("bulk_div", "dividends"),
    ("bulk_splits", "splits"),
)
BUDGET_PREFIX = "eodhd-call:"  # journal job records: <prefix><gmt day>:<n>
MANIFEST_HEAD = "utc\tkind\tsymbol\thttp\tcost\tbytes\tpayload_sha256\tfile\tfile_sha256\turl"

Transport = Callable[[str, Mapping[str, str]], bytes]


class StoreRefreshError(Exception):
    pass


class BudgetError(StoreRefreshError):
    """The request would pass the day's EODHD budget: not sent (fail closed)."""


class JournalCallBudget:
    """DAT-23's counted budget kept in the B-fast journal: a request is recorded (and
    committed) at its vendor cost before it is sent, per GMT day."""

    def __init__(self, journal: Journal, calls_per_day: int) -> None:
        self.j = journal
        self.calls_per_day = calls_per_day

    def used(self, gmt_day: date) -> int:
        recs = self.j.job_records(f"{BUDGET_PREFIX}{gmt_day}:")
        return sum(int(r.get("cost", 1)) for _, r in recs)

    def reserve(self, endpoint: str, cost: int, now: datetime) -> None:
        day = ensure_utc(now).astimezone(UTC).date()
        recs = self.j.job_records(f"{BUDGET_PREFIX}{day}:")
        used = sum(int(r.get("cost", 1)) for _, r in recs)
        if used + cost > self.calls_per_day:
            raise BudgetError(
                f"DATA_BUDGET: {endpoint} refused, {used} of {self.calls_per_day} EODHD "
                f"calls already used on {day} (GMT); failing closed"
            )
        key = f"{BUDGET_PREFIX}{day}:{len(recs) + 1:05d}"
        self.j.mark_job(key, {"endpoint": endpoint, "cost": cost}, now)


@dataclass(frozen=True)
class RefreshResult:
    status: str  # REFRESHED | PRESENT | NOT_READY | FAILED | BUDGET | NO_SECRET | REFUSED
    day: date
    rows: int = 0
    calls: int = 0
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("REFRESHED", "PRESENT")

    @property
    def fatal(self) -> bool:
        """An error the next slot will not fix by itself: page at once."""
        return self.status in ("BUDGET", "NO_SECRET", "REFUSED")


def urllib_transport(url: str, params: Mapping[str, str]) -> bytes:  # pragma: no cover - network
    import urllib.parse
    import urllib.request

    if not url.startswith("https://"):
        raise StoreRefreshError("EODHD is reached over https only")
    req = urllib.request.Request(  # noqa: S310 - https checked above
        f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        body: bytes = resp.read()
    return body


def _rows_of(body: bytes, what: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(body)
    except (ValueError, UnicodeDecodeError) as e:
        raise StoreRefreshError(f"{what}: not JSON ({type(e).__name__})") from None
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise StoreRefreshError(f"{what}: not a list of rows")
    return data


def _gz_rows(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


@dataclass
class StoreRefresher:
    """Append the day's EODHD bulk files to the forward store (BF-D31)."""

    root: Path  # the forward store (bigwins_forward/data/eodhd layout)
    raw: RawStore  # unchanged vendor responses (DAT-09)
    calls_per_day: int = 100000
    bulk_call_cost: int = 100
    min_rows: int = 1000
    min_share: float = 0.9
    attempts: int = 2
    backoff_s: float = 5.0
    transport: Transport = urllib_transport
    token: Callable[[], SecretValue] = field(default=lambda: read_secret("eodhd_api_token"))
    sleep: Callable[[float], None] = _time.sleep

    # ------------------------------------------------------------ the store
    def files(self, kind: str, day: date | None = None) -> list[Path]:
        d = self.root / "raw" / kind
        pat = f"AU_{day}__*.json.gz" if day else "AU_*.json.gz"
        return sorted(d.glob(pat)) if d.is_dir() else []

    def last_day(self) -> date | None:
        """The newest session with a bulk close file in the store (staleness test)."""
        days = [p.name[3:13] for p in self.files("bulk_eod")]
        try:
            return max((date.fromisoformat(x) for x in days), default=None)
        except ValueError:
            return None

    def _prev_count(self, day: date) -> int:
        """Rows of the newest earlier bulk close file (completeness reference)."""
        prev = [p for p in self.files("bulk_eod") if p.name[3:13] < str(day)]
        return len(_gz_rows(prev[-1])) if prev else 0

    def complete(self, day: date) -> bool:
        have = self.files("bulk_eod", day)
        return bool(have) and self._enough(len(_gz_rows(have[-1])), day)

    def _enough(self, n: int, day: date) -> bool:
        return n >= self.min_rows and n >= self.min_share * self._prev_count(day)

    def _write(self, kind: str, day: date, rows: list[dict[str, Any]], now: datetime) -> None:
        stamp = ensure_utc(now).strftime("%Y%m%dT%H%M%S%fZ")
        rel = f"raw/{kind}/AU_{day}__{stamp}.json.gz"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(rows, separators=(",", ":")).encode()
        data = gzip.compress(payload, mtime=0)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.part")
        tmp.write_bytes(data)
        os.replace(tmp, path)  # atomic: the store reader never sees half a file
        typ = dict(KINDS)[kind]
        url = f"{BASE_URL}/eod-bulk-last-day/AU?date={day}" + (f"&type={typ}" if typ else "")
        man = self.root / "manifest.tsv"
        line = "\t".join(
            [
                ensure_utc(now).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), kind, f"AU_{day}", "200",
                str(self.bulk_call_cost), str(len(payload)),
                hashlib.sha256(payload).hexdigest(), rel, hashlib.sha256(data).hexdigest(),
                url + "&fmt=json",  # never the key
            ]
        )  # fmt: skip
        new = not man.is_file()
        with man.open("a", encoding="utf-8") as f:
            if new:
                f.write(MANIFEST_HEAD + "\n")
            f.write(line + "\n")

    # ------------------------------------------------------------ the vendor
    def _get(
        self, typ: str | None, day: date, key: str, budget: JournalCallBudget, now: datetime
    ) -> bytes:
        endpoint = f"bulk:AU:{day}:{typ or 'eod'}"
        budget.reserve(endpoint, self.bulk_call_cost, now)  # counted before it is sent
        params = {"date": str(day), "fmt": "json", "api_token": key}
        if typ:
            params["type"] = typ
        try:
            body = self.transport(f"{BASE_URL}/eod-bulk-last-day/AU", params)
        except Exception as e:  # never let the URL (with the key) into a message
            name = type(e).__name__
            code = getattr(e, "code", None)
            raise StoreRefreshError(
                f"EODHD {endpoint}: request failed ({name}{f' {code}' if code else ''})"
            ) from None
        with contextlib.suppress(RawStoreError):  # the same instant twice: first copy kept
            self.raw.put("eodhd", f"bulk_AU_{typ or 'eod'}_{day:%Y%m%d}", body, now)
        return body

    def refresh(self, day: date, journal: Journal, now: datetime) -> RefreshResult:
        """Fetch D's closes, dividends and splits into the store (idempotent)."""
        if self.complete(day):
            return RefreshResult("PRESENT", day, note="the day's bulk file is in the store")
        try:
            key = self.token().reveal()  # the Docker secret only; no key, no request
        except SecretError as e:
            return RefreshResult("NO_SECRET", day, note=str(e)[:200])
        budget = JournalCallBudget(journal, self.calls_per_day)
        calls, status, note = 0, "NOT_READY", ""
        for k in range(self.attempts):
            if k:
                self.sleep(self.backoff_s)
            try:
                calls += 1
                eod = _rows_of(self._get(None, day, key, budget, now), "bulk eod")
                rows = [r for r in eod if str(r.get("date", ""))[:10] == str(day)]
                if not self._enough(len(rows), day):
                    status = "NOT_READY"
                    note = (
                        f"{len(rows)} of {len(eod)} rows dated {day} (need >= {self.min_rows} "
                        f"and >= {self.min_share:.0%} of the previous day's)"
                    )
                    continue
                events: dict[str, list[dict[str, Any]]] = {}
                for kind, typ in KINDS[1:]:
                    calls += 1
                    events[kind] = _rows_of(self._get(typ, day, key, budget, now), kind)
                for kind, xs in events.items():
                    self._write(kind, day, xs, now)
                self._write("bulk_eod", day, rows, now)  # last: closes mark the day done
                return RefreshResult(
                    "REFRESHED", day, len(rows), calls,
                    f"{len(rows)} closes, {len(events['bulk_div'])} dividend(s), "
                    f"{len(events['bulk_splits'])} split(s)",
                )  # fmt: skip
            except BudgetError as e:
                return RefreshResult("BUDGET", day, 0, calls - 1, str(e)[:200])
            except StoreRefreshError as e:
                msg = str(e)[:200]
                if " 401" in msg or " 403" in msg:
                    return RefreshResult("REFUSED", day, 0, calls, msg)
                status, note = "FAILED", msg
            except OSError as e:
                status, note = "FAILED", f"{type(e).__name__}: {e}"[:200]
        return RefreshResult(status, day, 0, calls, note)
