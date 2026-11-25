"""Secret access (OPS-11; the closed list tidied in BF-D87 to match GO_LIVE_GUIDE B6).

Secrets come only from Docker secrets: files the owner types on the server into
``/srv/asx-trader/deploy/secrets/<name>`` (folder 700, files 444, BF-D33) with
``bigwins secret <name>`` (or that ``bigwins update`` makes), passed into the containers
by ``deploy/docker-compose.yml`` and read here from ``/run/secrets/<name>``. They are
never read from config files or environment variables, and never shown.

The closed list below is every name the system knows (guide B6). Some are read only by
the root host worker on the server and never mounted into a container
(``healthchecks_backup_url``, ``healthchecks_daily_url``, ``healthchecks_presence_url``);
they are listed so the app may show whether they are set (names only, BF-D63).
"""

from __future__ import annotations

import re
from pathlib import Path

from trader.constants import SECRETS_DIR_DEFAULT

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

# Secret names the system knows about (GO_LIVE_GUIDE B6). Unknown names are refused.
KNOWN_SECRETS: frozenset[str] = frozenset(
    {
        # typed by the owner (bigwins secret <name>)
        "tws_password",  # IBKR paper password (the gateway container only)
        "ibkr_flex_token",  # BF-D27: Flex Web Service token
        "ibkr_flex_query_id",  # the Activity Flex query id (not sensitive; no config key)
        "eodhd_api_token",  # BF-D31: the daily price-store refresh
        "healthchecks_url",  # BF-D41: the 5-minute heartbeat ("none" = off)
        "telegram_bot_token",  # only with notify.channel telegram|both (appendix T)
        "app_passphrase",  # BF-D83: hash of the memorised passphrase ("none" until set)
        # made on the server (bigwins update / guide B6), never typed or shown
        "db_password",
        "totp_seed",  # second factor (C4); a new one with `bigwins new-totp` (BF-D83)
        "vapid_private_key",  # BF-D40: Web Push signing key of the phone app (PEM)
        "app_proxy_key",  # BF-D46: dashboard -> trader request signatures
        "worker_job_key",  # BF-D48: trader -> host worker server-job signatures
        "db_dashboard_password",  # BF-D52: the dashboard's SELECT-only database role
        # read by the root host worker only (never mounted into a container)
        "healthchecks_backup_url",  # review F9: optional check pinged after each good backup
        "healthchecks_daily_url",  # BF-D77 (b): optional check pinged after each good daily cycle
        "healthchecks_presence_url",  # BF-D82: pinged daily while the owner is active
        "github_ci_token",  # BF-D90: optional read-only token for GitHub CI results (private repo)
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
            f"secret {name!r} not found in {secrets_dir} (on the server: bigwins secret {name})"
        )
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise SecretError(f"secret {name!r} is empty")
    return SecretValue(value)
