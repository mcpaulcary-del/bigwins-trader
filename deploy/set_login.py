"""bigwins login (BF-D39): write the owner's Tailscale log-in into app.allowed_logins of
config/bfast.local.yaml (server only, not in git; laid over config/bfast.yaml).

Usage: python3 set_login.py <path of bfast.local.yaml> <login>
Standard library only (runs with the host's python3). Other lines of the file are kept.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADER = "# Server-only settings (not in git), laid over config/bfast.yaml (BF-D39).\n"
LOGIN_RE = re.compile(r"^[A-Za-z0-9._%+@:-]{1,200}$")


def set_login(text: str, login: str) -> str:
    """``text`` with ``app.allowed_logins`` set to ``[login]``."""
    if not LOGIN_RE.fullmatch(login):
        raise ValueError(f"not a Tailscale log-in: {login!r}")
    line = f"  allowed_logins: [{json.dumps(login)}]"
    lines = text.splitlines()
    try:
        start = next(i for i, x in enumerate(lines) if re.fullmatch(r"app:\s*(#.*)?", x))
    except StopIteration:
        body = text.rstrip("\n")
        return (body + "\n" if body else HEADER) + "app:\n" + line + "\n"
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or not lines[end].strip()):
        end += 1
    for i in range(start + 1, end):
        if re.match(r"\s+allowed_logins\s*:", lines[i]):
            lines[i] = line
            return "\n".join(lines) + "\n"
    lines.insert(start + 1, line)
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    path, login = Path(argv[1]), argv[2].strip()
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(set_login(text, login), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
