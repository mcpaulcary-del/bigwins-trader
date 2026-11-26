"""Where the paper record lives (BF-D93). The research code names every file by ONE
absolute path, the cloud environment's scratchpad (``CLOUD_ROOT``); three hash-frozen
files contain it, so it is never edited. On the server the record tree
(``/srv/bwrecord``, or the shadow tree in the parallel week) is mounted at that same
path inside the record container: the code is byte-identical on both machines.

``BW_ROOT`` overrides the root for the tools themselves (tests, and host-side tools
that read ``/srv/bwrecord`` directly); it never changes what the research code reads.
"""

from __future__ import annotations

import os
from pathlib import Path

CLOUD_ROOT = "/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad"  # noqa: S108
REL_CODE = "bigwins_forward/code"
REL_DF_CODE = "data_foundation/code"
REL_RECORD = "onedrive/research2/68_forward_record"
REL_STATE = "bigwins_forward/out/paper_state"
REL_MULTI_STATE = "bigwins_forward/out/multi"
REL_DATA = "bigwins_forward/data"
REL_OUT = "bigwins_forward/out"
LEDGER = "LEDGER.jsonl"


def root() -> Path:
    return Path(os.environ.get("BW_ROOT") or CLOUD_ROOT)


def record_dir(base: Path | None = None) -> Path:
    return (base or root()) / REL_RECORD


def ledger(base: Path | None = None) -> Path:
    return record_dir(base) / LEDGER
