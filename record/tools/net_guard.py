"""Network guard for the announcements collector on the server (BF-D93; owner decision
27 Nov 2026: the research collector ``record/code/info_archive.py`` replaces
``deploy/info_archive.py`` on the server, on condition that it gets that copy's safety
checks first). The collector is NOT edited: ``launch.py`` installs this guard in the
process before the script runs, by replacing ``urllib.request.urlopen``, the one call the
collector makes. What the older server copy checked and the research copy did not:

1. **Hosts**: every request must be ``https`` to ``asx.com.au`` (or a sub-domain) or to
   ``download.asic.gov.au``. Anything else, ``http:``, ``file:``, ``ftp:`` included, is
   refused before a connection is made (the PDF address comes out of a fetched page).
2. **Redirects**: followed only to the same group of hosts (an ASX request never ends on
   another site).
3. **Size**: a response over 50 MB is refused, not stored.
4. **ASIC index**: only entries with an 8-digit date and a numeric version are passed on
   (the collector builds a file name from them), in their original order.

Already in the research copy, so not repeated here: the 50-row minimum for the list (a
changed page stores nothing), the ``%PDF`` check, the 2-second pacing, the cap of 60
price-sensitive PDFs and the ASX-hours pause. Not possible as a guard: writing the
director / capital-raising notice PDFs through a ``.part`` file (the research copy writes
them directly); ``steps.archive_check`` reports a cut-off PDF after each run instead.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

ASX_HOSTS = ("asx.com.au",)  # the owner's exception covers these hosts only
ASIC_HOSTS = ("download.asic.gov.au",)
GROUPS = (ASX_HOSTS, ASIC_HOSTS)
ASIC_INDEX = "https://download.asic.gov.au/short-selling/short-selling-data.json"
MAX_BYTES = 50_000_000


class RefusedError(ValueError):
    """The guard said no; nothing was requested or nothing is passed on."""


def host_ok(url: str, hosts: tuple[str, ...]) -> bool:
    """https on one of ``hosts`` (or a sub-domain of it), nothing else."""
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    h = (u.hostname or "").lower()
    return u.scheme == "https" and any(h == x or h.endswith("." + x) for x in hosts)


def group_of(url: str) -> tuple[str, ...] | None:
    return next((g for g in GROUPS if host_ok(url, g)), None)


class Pinned(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only to the hosts the request started on."""

    def __init__(self, hosts: tuple[str, ...]) -> None:
        self.hosts = hosts

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any,
                         newurl: str) -> Any:  # fmt: skip
        if not host_ok(newurl, self.hosts):
            raise urllib.error.HTTPError(newurl, code, "redirect to another host refused",
                                         headers, fp)  # fmt: skip
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def clean_index(data: bytes) -> bytes:
    """ASIC's index with only well-formed entries (date ``yyyymmdd``, numeric version)."""
    try:
        idx = json.loads(data)
    except ValueError as e:
        raise RefusedError("the ASIC index is not JSON") from e
    if not isinstance(idx, list):
        raise RefusedError("the ASIC index is not a list")
    good = [x for x in idx if isinstance(x, dict)
            and str(x.get("date", "")).isdigit() and len(str(x.get("date", ""))) == 8
            and str(x.get("version", "")).isdigit() and len(str(x.get("version", ""))) <= 4]  # fmt: skip
    if not good:
        raise RefusedError("the ASIC index has no usable entry")
    return json.dumps(good).encode()


class Body:
    """What the collector gets back: ``read()`` inside a ``with`` block."""

    def __init__(self, data: bytes, url: str) -> None:
        self._data, self.url, self.status = data, url, 200

    def read(self, n: int = -1) -> bytes:
        out = self._data if n is None or n < 0 else self._data[:n]
        self._data = self._data[len(out) :]
        return out

    def geturl(self) -> str:
        return self.url

    def __enter__(self) -> Body:
        return self

    def __exit__(self, *a: object) -> None:
        self._data = b""


def guarded(opener_for: Callable[[tuple[str, ...]], Any]) -> Callable[..., Body]:
    def urlopen(req: Any, data: Any = None, timeout: float = 60, **_kw: Any) -> Body:
        url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        hosts = group_of(url)
        if hosts is None or data is not None:
            host = urllib.parse.urlsplit(url).hostname if "://" in url else url[:40]
            raise RefusedError(f"not an allowed host or request: {host}")
        with opener_for(hosts).open(req, timeout=timeout) as r:
            body = bytes(r.read(MAX_BYTES + 1))
        if len(body) > MAX_BYTES:
            raise RefusedError(f"response over {MAX_BYTES // 1_000_000} MB refused")
        return Body(clean_index(body) if url == ASIC_INDEX else body, url)

    return urlopen


def install(opener_for: Callable[[tuple[str, ...]], Any] | None = None) -> None:
    """Replace ``urllib.request.urlopen`` for this process (the record container's job)."""
    build = urllib.request.build_opener  # the real one, before anything is replaced

    def default(hosts: tuple[str, ...]) -> Any:
        return build(Pinned(hosts))

    urllib.request.urlopen = guarded(opener_for or default)
