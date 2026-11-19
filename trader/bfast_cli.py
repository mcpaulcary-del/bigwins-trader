"""``trader-bf``: B-fast commands for the EMG2-20 book (paper only).

    trader-bf validate-config [--config config/bfast.yaml]
    trader-bf emg2-list --asof 2026-11-30 [--config ...] [--store DIR] [--out DIR]
    trader-bf kill|pause [--journal URL]           # one step, no second factor
    trader-bf status [--journal URL]

``emg2-list`` builds the panel from the forward store (read-only), prints the EMG2 list
T and the EMG2-20 picks for a fresh A$10,000 book, and writes
``emg2_list_<D>.json`` / ``emg2_20_picks_<D>.json`` with their SHA-256 digests (the
"written and hashed before the open" step of BF1). It never contacts a broker.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from trader.bfast_config import load_bfast_config
from trader.canonical import canonical_json
from trader.journal import Journal
from trader.risk import SafetyLevel

DEFAULT_CONFIG = Path("config/bfast.yaml")


def _sessions(until: date) -> list[date]:
    import exchange_calendars as xc

    cal = xc.get_calendar("XASX", start="2020-01-01", end=str(until.year + 1) + "-12-31")
    return [d.date() for d in cal.sessions]


def _journal(url: str | None) -> Journal:
    from sqlalchemy import create_engine

    return Journal(create_engine(url)) if url else Journal.sqlite("bf_journal.sqlite3")


def cmd_emg2_list(args: argparse.Namespace) -> int:
    from trader.data.forward_store import ForwardStore
    from trader.lines.emg2 import BookState, decide_emg2_20, emg2_list

    cfg = load_bfast_config(args.config)
    store = Path(args.store or cfg.data.forward_store)
    etp: frozenset[str] = frozenset()
    if cfg.data.etp_list.is_file():
        etp = frozenset(x.strip() for x in cfg.data.etp_list.read_text().splitlines() if x.strip())
    lic: frozenset[str] = frozenset()
    if cfg.data.lic_list.is_file():
        lic = frozenset(
            r.split(",")[0] for r in cfg.data.lic_list.read_text().splitlines()[1:] if r
        )
    panel = ForwardStore(store).build_panel(
        args.asof,
        _sessions(args.asof),
        history=cfg.data.history_sessions,
        etp_codes=etp,
        lic_codes=lic,
    )
    lst = emg2_list(panel)
    dec = decide_emg2_20(
        panel, BookState(cfg.book, cfg.live_emg2_20.capital_cap_aud), cfg.emg2_20_params()
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"emg2_list_{args.asof}.json").write_text(canonical_json(lst.payload()))
    (out / f"emg2_20_picks_{args.asof}.json").write_text(canonical_json(dec.payload()))
    print(
        json.dumps(
            {
                "as_of": str(args.asof),
                "eligible": len(lst.eligible),
                "band_c": len(lst.band_c),
                "targets": list(lst.targets),
                "data_block": lst.data_block,
                "list_sha256": lst.digest,
                "picks": [[b.entity, str(b.value_aud), str(b.ref_close)] for b in dec.buys],
                "skipped": [[s.entity, s.reason] for s in dec.skipped],
                "picks_sha256": dec.digest,
            },
            indent=1,
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trader-bf", description="B-fast EMG2-20 (paper only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate-config")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p = sub.add_parser("emg2-list")
    p.add_argument("--asof", type=date.fromisoformat, required=True)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--store")
    p.add_argument("--out", default="out")
    for name in ("kill", "pause", "status"):
        p = sub.add_parser(name)
        p.add_argument("--journal")
    a = ap.parse_args(argv)
    if a.cmd == "validate-config":
        cfg = load_bfast_config(a.config)
        print(f"ok: book {cfg.book}, mode {cfg.mode}, cap A${cfg.live_emg2_20.capital_cap_aud}")
        return 0
    if a.cmd == "emg2-list":
        return cmd_emg2_list(a)
    j = _journal(a.journal)
    if a.cmd == "kill":
        j.set_safety(SafetyLevel.KILLED, "CLI kill", "cli")
        print("KILLED (open orders are cancelled by the runner's kill path; re-arm needs 2FA)")
    elif a.cmd == "pause":
        j.set_safety(SafetyLevel.PAUSED, "CLI pause", "cli")
        print("PAUSED")
    print(f"safety {j.safety_level().value}; cash/positions per book via the report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
