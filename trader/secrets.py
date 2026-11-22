"""Secret access (OPS-11).

Secrets come only from Docker secrets: files under the secrets directory
(``/run/secrets`` inside the container, mapped from ``/opt/trader/secrets/<user>/``
on the host, mode 600). They are never read from config files or environment
variables. ``trader secret set`` (M5) writes them through a small root-owned
service; that path is not implemented in M0.
"""

from __future__ import annotations

import re
from pathlib import Path

from trader.constants import SECRETS_DIR_DEFAULT

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

# Secret names the system knows about (§15, §19). Unknown names are refused.
KNOWN_SECRETS: frozenset[str] = frozenset(
    {
        "telegram_bot_token",
        "smtp_password",
        "eodhd_api_token",
        "ibkr_flex_token",
        "ibkr_flex_query_id",  # not sensitive, but no §18 key exists for it (D-07)
        "db_password",
        "healthchecks_url",
        "object_store_token",
        "rclone_config",  # off-site backup remote (section 19)
        "totp_seed",  # second factor (section 15)
        "tws_password",
        "vapid_private_key",  # BF-D40: Web Push signing key of the phone app (PEM)
    }
)


class SecretError(Exception):
    pass


class SecretValue:
    """Wrapper whose ``repr``/``str`` never reveal the value (MON-03: no secrets in logs)."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretValue(***)"

    __str__ = __repr__


def read_secret(name: str, secrets_dir: Path = SECRETS_DIR_DEFAULT) -> SecretValue:
    """Read one Docker secret by name. Raises ``SecretError`` if missing."""
    if not _NAME_RE.fullmatch(name) or name not in KNOWN_SECRETS:
        raise SecretError(f"unknown secret name {name!r}")
    path = secrets_dir / name
    if not path.is_file():
        raise SecretError(
            f"secret {name!r} not found in {secrets_dir} (set it with `trader secret set`)"
        )
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise SecretError(f"secret {name!r} is empty")
    return SecretValue(value)
