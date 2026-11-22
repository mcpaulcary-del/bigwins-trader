"""Start-up check of the Docker secret files (BF-D33).

Compose passes ``deploy/secrets/<name>`` into each container as a bind mount with the
host's owner and mode. The trader runs as uid 10001, Postgres as uid 999 and the IB
Gateway as its own user, so every file must be readable by users other than its owner
(the guide's ``chmod 444`` files) while the folder ``deploy/secrets`` stays ``700`` on the
host (only root can list it). A file that is missing, empty, not readable by this
process or without the "others may read" bit fails here, with the fix spelled out,
before any service uses it; nothing else on the system notices until a job fails.

The check never reads a secret's contents: it uses ``stat`` and ``os.access`` only, so
the one-shot ``secrets-check`` service may look at the gateway's password file without
seeing it.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from trader.constants import SECRETS_DIR_DEFAULT
from trader.secrets import KNOWN_SECRETS

# deploy/docker-compose.yml: the files of the stack (the gateway's password included),
# and the trader's own. Which ones depends on ``notify.channel`` (BF-D40): the phone app
# needs ``vapid_private_key``, Telegram needs ``telegram_bot_token``.
BASE_SECRETS: tuple[str, ...] = (
    "tws_password", "db_password", "totp_seed", "eodhd_api_token",
    "healthchecks_url", "ibkr_flex_token", "ibkr_flex_query_id",
)  # fmt: skip


def stack_secrets(channel: str = "app") -> tuple[str, ...]:
    """Every secret file the stack needs for ``notify.channel`` = ``channel``."""
    extra: list[str] = []
    if channel in ("app", "both"):
        extra.append("vapid_private_key")
    if channel in ("telegram", "both"):
        extra.append("telegram_bot_token")
    return (*BASE_SECRETS, *extra)


def trader_secrets(channel: str = "app") -> tuple[str, ...]:
    return tuple(n for n in stack_secrets(channel) if n != "tws_password")


STACK_SECRETS: tuple[str, ...] = stack_secrets("app")
TRADER_SECRETS: tuple[str, ...] = trader_secrets("app")
FIX = (
    "on the server: cd /srv/asx-trader/deploy && chmod 700 secrets && chmod 444 secrets/* "
    "(docs/GO_LIVE_GUIDE.md B6), then docker compose up -d"
)


def check_secrets(
    names: tuple[str, ...] = TRADER_SECRETS, secrets_dir: Path | None = None
) -> list[str]:
    """Problems with the secret files ``names`` under ``secrets_dir`` (default
    ``/run/secrets``; empty: all fine)."""
    secrets_dir = SECRETS_DIR_DEFAULT if secrets_dir is None else secrets_dir
    out: list[str] = []
    uid = os.getuid() if hasattr(os, "getuid") else -1
    for name in names:
        if name not in KNOWN_SECRETS:
            out.append(f"secret {name!r}: not a known secret name")
            continue
        p = secrets_dir / name
        try:
            st = p.stat()
        except OSError:
            out.append(
                f"secret {name}: missing in {secrets_dir} - create deploy/secrets/{name} "
                "and list it under the service's secrets: in deploy/docker-compose.yml"
            )
            continue
        mode = stat.S_IMODE(st.st_mode)
        if not stat.S_ISREG(st.st_mode):
            out.append(f"secret {name}: not a regular file")
        elif not os.access(p, os.R_OK):
            out.append(
                f"secret {name}: not readable by uid {uid} (mode {mode:04o}, owner uid "
                f"{st.st_uid}) - {FIX}"
            )
        elif not mode & stat.S_IROTH:
            out.append(
                f"secret {name}: mode {mode:04o} is not readable by other users; the "
                f"containers run as other uids (trader 10001) - {FIX}"
            )
        elif mode & (stat.S_IWGRP | stat.S_IWOTH):
            out.append(f"secret {name}: mode {mode:04o} lets other users change it - {FIX}")
        elif st.st_size == 0:
            out.append(f"secret {name}: empty - type its value again (GO_LIVE_GUIDE B6)")
    return out
