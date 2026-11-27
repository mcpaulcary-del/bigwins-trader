"""Run ONE research script inside the record container, unedited, behind the guards
(BF-D93). Started by ``runner.py`` as ``python -I launch.py [--isolated] <script> [args]``.

1. The writer fence: refuse (exit 75) unless ``WRITER.json`` lets this machine append
   (``--no-ledger``, for jobs that never write the ledger such as the archive: the script
   runs whoever the writer is, and guard 2 still refuses any append it might try).
2. ``fwd_ledger.append`` is wrapped: the fence is checked again at every append (the
   ledger a script points ``LED`` at decides which fence), and a standby copy marks its
   entries. The entry format and hashing are the research module's own, untouched.
3. The EODHD token shim (``eodhd_shim``) when a token file is mounted.
4. The network guard (``net_guard``): ``urllib`` reaches only the ASX and ASIC hosts of
   the owner's archive exception, over https, redirects pinned, responses capped.
5. The script then runs as ``__main__`` with its own arguments, as on the cloud:
   ``python3 script.py`` has the script's folder first on ``sys.path``; ``python3 -I
   script.py`` (``--isolated``) does not.
"""

from __future__ import annotations

import importlib.util
import os
import runpy
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2]))  # the read-only mount that holds record/tools

from record.tools import eodhd_shim, fence, net_guard, paths  # noqa: E402

REFUSED = 75  # EX_TEMPFAIL: the fence said no; nothing ran


def relay_fence() -> fence.Fence | None:
    p = os.environ.get("BW_RELAY_FENCE", "")
    if not p or not Path(p).is_file():
        return None
    try:
        import json

        return fence.parse(json.loads(Path(p).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None  # an unreadable relay copy never blocks the writer of record (plan 5.2)


def guard_ledger(code_dir: Path, me: str) -> Any:
    """Load the research ``fwd_ledger`` and wrap its ``append`` with the fence."""
    spec = importlib.util.spec_from_file_location("fwd_ledger", code_dir / "fwd_ledger.py")
    if spec is None or spec.loader is None:
        raise SystemExit("REFUSED: fwd_ledger.py is missing from the code folder")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fwd_ledger"] = mod
    spec.loader.exec_module(mod)
    orig: Any = mod.append

    def append(**fields: Any) -> Any:
        d = fence.decide_dir(Path(mod.LED).parent, me, relay_fence())
        if not d.ok:
            raise SystemExit(f"REFUSED (writer fence): {d.reason}")
        if d.standby:
            fields["standby"] = True
        return orig(**fields)

    mod.append = append  # type: ignore[attr-defined]
    return mod


def main(argv: list[str]) -> int:
    ledger = not (bool(argv) and argv[0] == "--no-ledger")
    if not ledger:
        argv = argv[1:]
    isolated = bool(argv) and argv[0] == "--isolated"
    if isolated:
        argv = argv[1:]
    if not argv:
        print("usage: launch.py [--isolated] <script.py> [args]", file=sys.stderr)
        return 2
    root = paths.root()
    code = root / paths.REL_CODE
    script = (code / argv[0]).resolve()
    if code.resolve() not in script.parents or not script.is_file():
        print(f"REFUSED: {argv[0]} is not a script of the record code", file=sys.stderr)
        return 2
    me = os.environ.get("BW_RECORD_HOST", "")
    d = fence.decide_dir(paths.record_dir(root), me, relay_fence())
    if ledger and not d.ok:
        print(f"REFUSED (writer fence): {d.reason}")
        return REFUSED
    guard_ledger(code, me)
    # the collector's safety checks (hosts, redirects, size): around it, not in it. Every
    # record script gets it: none but the collector uses urllib, and none may reach another host
    net_guard.install()
    tok = eodhd_shim.read_token(
        Path(os.environ.get("BW_EODHD_TOKEN_FILE", "/run/secrets/eodhd_api_token"))
    )
    try:
        import requests
    except ImportError:  # no requests here (a test environment): nothing to guard
        requests = None
    if requests is not None:
        # every record script: requests may reach EODHD over https and nothing else
        eodhd_shim.install_allowlist(requests.Session)
        if tok:
            eodhd_shim.install(requests.Session, tok, os.environ.get("BW_EODHD_MODE", "header"))
    del tok
    os.chdir(code)
    sys.argv = [str(script), *argv[1:]]
    if not isolated:
        sys.path.insert(0, str(code))
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
