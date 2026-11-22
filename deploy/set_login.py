"""bigwins login (BF-D39): write the owner's Tailscale log-in into app.allowed_logins of
config/bfast.local.yaml (server only, not in git; laid over config/bfast.yaml).

Usage: python3 set_login.py <path of bfast.local.yaml> <login> [<app host name>]
Standard library only (runs with the host's python3). Other lines of the file are kept.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADER = "# Server-only settings (not in git), laid over config/bfast.yaml (BF-D39).\n"
LOGIN_RE = re.compile(r"^[A-Za-z0-9._%+@:-]{1,200}$")
HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


def set_login(text: str, login: str, host: str = "") -> str:
    """``text`` with ``app.allowed_logins`` set to ``[login]`` (and, with ``host``,
    ``app.public_host``: the only Origin accepted for actions, BF-D46)."""
    if not LOGIN_RE.fullmatch(login):
        raise ValueError(f"not a Tailscale log-in: {login!r}")
    if host:
        if not HOST_RE.fullmatch(host):
            raise ValueError(f"not a host name: {host!r}")
        text = _set(text, "public_host", json.dumps(host))
    return _set(text, "allowed_logins", f"[{json.dumps(login)}]")


def set_account(text: str, account: str) -> str:
    """Review F24: ``broker.account_id`` (a paper DU... id only)."""
    if not re.fullmatch(r"DU\d{5,10}", account):
        raise ValueError(f"not a paper account id: {account!r}")
    return _set(text, "account_id", account, "broker")


def _set(text: str, key: str, value: str, section: str = "app") -> str:
    line = f"  {key}: {value}"
    lines = text.splitlines()
    try:
        start = next(i for i, x in enumerate(lines) if re.fullmatch(rf"{section}:\s*(#.*)?", x))
    except StopIteration:
        body = text.rstrip("\n")
        return (body + "\n" if body else HEADER) + f"{section}:\n" + line + "\n"
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
        end += 1
    for i in range(start + 1, end):
        if re.match(rf"\s+{key}\s*:", lines[i]):
            lines[i] = line
            return "\n".join(lines) + "\n"
    lines.insert(start + 1, line)
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) > 3 and argv[1] == "--account":
        path = Path(argv[2])
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        path.write_text(set_account(text, argv[3].strip()), encoding="utf-8")
        return 0
    path, login = Path(argv[1]), argv[2].strip()
    host = argv[3].strip().lower() if len(argv) > 3 else ""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(set_login(text, login, host), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
