"""bigwins secret helpers (BF-D83), run as root on the server with the host's python3
(standard library only). Nothing here prints a secret except the one QR payload that
``new-totp`` must show once.

    python3 secret_tool.py new-totp <secrets_dir>
        Make a new authenticator seed in <secrets_dir>/totp_seed (the old one stops working
        once the trader restarts) and print the otpauth:// URI on stdout (piped straight
        into qrencode by bigwins; never stored anywhere else).
    python3 secret_tool.py passphrase <file>
        Read the passphrase twice from stdin (two lines), check it, and store only its
        salted PBKDF2-SHA256 hash in <file> (the format of trader/passphrase.py).

Both write the file in place (same inode: the containers' bind mount keeps working) with
mode 444 at the end, as every secret file (BF-D33).
"""

from __future__ import annotations

import base64
import hashlib
import os
import sys
from pathlib import Path

PREFIX = "pbkdf2_sha256"
ITERATIONS = 310_000  # the same as trader/passphrase.py (a test keeps them equal)
MIN_LENGTH = 12
MAX_LENGTH = 200


def _write_in_place(p: Path, text: str) -> None:
    """Rewrite a 444 secret file in place (chmod 600, write, chmod 444)."""
    p.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(p.parent, 0o700)
    if p.exists():
        os.chmod(p, 0o600)
    with p.open("w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(p, 0o444)


def new_seed() -> str:
    return base64.b32encode(os.urandom(20)).decode()


def new_totp(secrets_dir: Path) -> str:
    """A new seed in totp_seed; returns the otpauth URI for the QR code."""
    seed = new_seed()
    _write_in_place(secrets_dir / "totp_seed", seed)
    return f"otpauth://totp/bigwins-trader?secret={seed}&issuer=bigwins"


def hash_passphrase(passphrase: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, ITERATIONS)
    return f"{PREFIX}${ITERATIONS}${salt.hex()}${dk.hex()}"


def check_passphrase(first: str, second: str) -> str | None:
    """Why the passphrase is not accepted, or None."""
    if first != second:
        return "the two entries differ"
    if len(first) < MIN_LENGTH:
        return f"too short: use at least {MIN_LENGTH} characters (three or four words)"
    if len(first) > MAX_LENGTH:
        return f"too long: at most {MAX_LENGTH} characters"
    if first.strip() != first:
        return "it starts or ends with a space"
    if first.lower() == "none":
        return "that word is reserved"
    return None


def main(argv: list[str]) -> int:
    op = argv[1] if len(argv) > 1 else ""
    if op == "new-totp" and len(argv) == 3:
        print(new_totp(Path(argv[2])))
        return 0
    if op == "passphrase" and len(argv) == 3:
        lines = sys.stdin.read().split("\n")
        first, second = [*lines, "", ""][:2]
        why = check_passphrase(first, second)
        if why is not None:
            print(f"not saved: {why}", file=sys.stderr)
            return 1
        _write_in_place(Path(argv[2]), hash_passphrase(first))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
