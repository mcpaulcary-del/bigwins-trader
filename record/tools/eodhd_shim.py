"""EODHD token injection for the record container (BF-D93), without editing research code.

On the cloud every EODHD request carries ``Authorization: Bearer proxy-injected`` and the
environment's network proxy swaps in the real key; the code never sees it. Three
hash-frozen files have that placeholder hard-coded. On the server this shim does the
proxy's job inside the process: at the last moment before the bytes leave
(``requests.Session.send``) a request to an EODHD host that carries the placeholder gets
the real token (``header`` mode: the same header; ``query`` mode: ``api_token=`` in the
URL), and everything that comes back to the code (the response's URL and request,
redirect history, any exception text) has the placeholder again. So no log line, no
manifest row and no traceback the research code produces can contain the token.

The token is read from a file (``/run/secrets/eodhd_api_token``), never from the
environment or the command line. It is sent to EODHD hosts only, over https only.
"""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

PLACEHOLDER = "proxy-injected"
HOSTS = ("eodhd.com", "eodhistoricaldata.com")
MODES = ("header", "query")
REDACTED = "REDACTED"


def read_token(path: Path) -> str:
    """The token, or "" when the file is missing, empty, "none" or not a plausible key."""
    try:
        t = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if (
        t.lower() == "none"
        or not (8 <= len(t) <= 200)
        or not all(c.isalnum() or c in "._-" for c in t)
    ):
        return ""
    return t


def eodhd_url(url: str) -> bool:
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    h = (u.hostname or "").lower()
    return u.scheme == "https" and any(h == x or h.endswith("." + x) for x in HOSTS)


def redact(text: str, token: str) -> str:
    if not token:
        return text
    return text.replace(token, REDACTED).replace(urllib.parse.quote(token, safe=""), REDACTED)


def with_token(url: str, token: str) -> str:
    u = urllib.parse.urlsplit(url)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True)
         if k != "api_token"]  # fmt: skip
    q.append(("api_token", token))
    return urllib.parse.urlunsplit(u._replace(query=urllib.parse.urlencode(q)))


def without_token(url: str) -> str:
    try:
        u = urllib.parse.urlsplit(url)
    except ValueError:
        return url
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True)
         if k != "api_token"]  # fmt: skip
    return urllib.parse.urlunsplit(u._replace(query=urllib.parse.urlencode(q)))


def _scrub(obj: Any, token: str) -> None:
    """Put the placeholder back on a request / response object the code will see."""
    url = getattr(obj, "url", None)
    if isinstance(url, str) and token in url:
        obj.url = without_token(url)
    headers = getattr(obj, "headers", None)
    if headers is not None:
        try:
            if token in str(headers.get("Authorization", "")):
                headers["Authorization"] = "Bearer " + PLACEHOLDER
        except (AttributeError, TypeError):
            pass


def install(session_cls: Any, token: str, mode: str = "header") -> bool:
    """Wrap ``session_cls.send`` (``requests.Session``). False: nothing installed (no
    token: the placeholder goes out as on the cloud and EODHD answers 401)."""
    if not token or mode not in MODES or getattr(session_cls, "_bw_eodhd", False):
        return False
    orig = session_cls.send

    def send(self: Any, request: Any, **kw: Any) -> Any:
        url = str(getattr(request, "url", ""))
        auth = str(request.headers.get("Authorization", ""))
        mine = eodhd_url(url) and auth == "Bearer " + PLACEHOLDER
        if mine:
            if mode == "header":
                request.headers["Authorization"] = "Bearer " + token
            else:
                del request.headers["Authorization"]
                request.url = with_token(url, token)
        try:
            resp = orig(self, request, **kw)
        except Exception as e:
            _scrub(request, token)
            if mine and token in (str(e) + repr(e)):
                # the same exception class when it takes a message, else a plain error:
                # the token never travels in a traceback
                try:
                    clean: Exception = type(e)(redact(str(e), token))
                except Exception:
                    clean = RuntimeError(redact(str(e), token))
                raise clean from None
            raise
        if mine:
            _scrub(request, token)
            for r in [resp, *list(getattr(resp, "history", []) or [])]:
                _scrub(r, token)
                _scrub(getattr(r, "request", None), token)
        return resp

    session_cls.send = send
    session_cls._bw_eodhd = True
    return True
