"""The memorised passphrase (BF-D83, disaster-recovery review M2): a second secret for the
riskiest app actions (re-arm / resume, continue, approve an update, roll back, show the
backup recovery key, start Claude remote control, unlock the app's actions).

Why: the app trusts the Tailscale log-in plus the 6-digit code, and both live on the
owner's phone. Whoever has the unlocked phone has both. A passphrase the owner keeps in
their head is the one factor a thief with the phone does not have.

The owner sets it on the server with ``bigwins secret app_passphrase`` (typed, never shown).
The server stores only a salted PBKDF2-SHA256 hash in ``deploy/secrets/app_passphrase``
(``deploy/secret_tool.py passphrase``, the same format as here); until it is set the file
holds ``none`` and the passphrase is not asked (Health nags; it is a go-live checklist
item). A wrong passphrase counts in the same wrong-code lock-out as a wrong 6-digit code
(BF-D47 / BF-D58). The passphrase is never logged, journaled, pushed or put in the inbox.
"""

from __future__ import annotations

import hashlib
import hmac

from trader.secrets import SecretValue

PREFIX = "pbkdf2_sha256"
ITERATIONS = 310_000
MIN_LENGTH = 12
MAX_LENGTH = 200


def stored_hash(secret: SecretValue | None) -> str | None:
    """The stored hash, or None when the passphrase is not set (``none`` / empty / any
    value that is not a hash of this format)."""
    if secret is None:
        return None
    v = secret.reveal().strip()
    if not v or v.lower() == "none":
        return None
    parts = v.split("$")
    if len(parts) != 4 or parts[0] != PREFIX or not parts[1].isdigit():
        return None
    return v


def hash_passphrase(passphrase: str, salt: bytes, iterations: int = ITERATIONS) -> str:
    """The stored form (tests; the server uses ``deploy/secret_tool.py``, same format)."""
    dk = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations)
    return f"{PREFIX}${iterations}${salt.hex()}${dk.hex()}"


def verify(stored: str | None, given: str) -> bool:
    """True when ``given`` matches ``stored``. Unset (None) never verifies: callers ask
    for a passphrase only when one is set."""
    if stored is None or not given or len(given) > MAX_LENGTH:
        return False
    try:
        _, it, salt_hex, want_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", given.encode("utf-8"), bytes.fromhex(salt_hex),
                                 int(it))  # fmt: skip
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk.hex(), want_hex)
