# Big Wins - paper record backup (branch `paper-record`)

This orphan branch is a durable backup of the Big Wins **paper** (no real money) forward record. It shares no
history with the trading code on `main` / `bigwins-fast` and must never be merged into them.

Contents (paths mirror the session scratchpad layout, i.e. relative to the scratchpad root `$B`):

- `bigwins_forward/code/` - all paper/forward-record code incl. `*_frozen.py` copies and `blind3_frozen/`, `multi_frozen/`,
  `pair_frozen/`, `rep13/` (no `__pycache__`).
- `onedrive/research2/68_forward_record/` - `LEDGER.jsonl`, every `AMENDMENT_*.md` with its `.sha256`, LIC lists,
  `CORPORATE_ACTIONS.csv`, `paper/` scorecards, holdings, histories, alerts, manifests.
- `bigwins_forward/out/paper_state/` - engine `state.json`, `score_state.json`, `decisions/`, and every per-line state file
  the paper code writes there (`shadow_state.json`, `accum_state.json`, `cxl_state.json`, `early_state.json`,
  `emg2_state.json`, `emg2s_state.json`, `emg2bt_state.json`, `blind3_state.json`, `pair_state.json`) once created;
  `bigwins_forward/out/multi/` (paper_multi job state) once created; small text outputs of `bigwins_forward/out/`.
- `onedrive/research2/*.md` - research reports and `OWNER_DECISIONS_*.md`.
- `MANIFEST.sha256` - sha256 of every file in this branch (except itself); verify with `sha256sum -c MANIFEST.sha256`.

**Excluded:** licensed vendor data - everything under `bigwins_forward/data/` (EODHD prices, estimates, new-list price
files), all `*.npz`, `*.pkl`, `*.gz` (incl. intraday snapshots), raw downloads, panels, lock files, and any file > 5 MB.
EODHD data is re-downloadable with the project's download scripts (`fwd_download.py`, the data_foundation EODHD code)
using the owner's own EODHD key, which is never stored here.

**Restore:** clone this branch and copy the files back into the scratchpad layout, e.g.

    git clone -b paper-record --single-branch https://github.com/mcpaulcary-del/bigwins-trader rec
    cd rec && sha256sum -c MANIFEST.sha256
    rsync -a --exclude .git --exclude README.md --exclude MANIFEST.sha256 ./ "$B"/    # or cp -a

then re-download EODHD data before re-running any paper job. Updated daily by
`bigwins_forward/code/backup_paper_record.sh` (additive: files deleted from the scratchpad are kept here).
