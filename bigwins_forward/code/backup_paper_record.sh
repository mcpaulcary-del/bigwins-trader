#!/usr/bin/env bash
# backup_paper_record.sh - back up the Big Wins PAPER record (code, ledger, amendments, paper state, reports) to the
# orphan branch `paper-record` of the owner's private repo. Text/code only: no EODHD/vendor data, no *.npz/*.pkl/*.gz,
# nothing over 5 MB. Additive: a file that disappears from the scratchpad is KEPT in the backup (never deleted).
# Safe to run daily: copies, rebuilds MANIFEST.sha256, scans for secrets, commits only if something changed, pushes
# (one retry after 5 s on HTTP 429; never force-pushes). Exit 0 = backed up or nothing to do; non-zero = failed.
# Usage: bash backup_paper_record.sh [--no-push]
set -euo pipefail
B=${BW_SCRATCH:-/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad}
R=${BW_BACKUP_REPO:-/home/user/paper-record-backup}
URL=https://github.com/mcpaulcary-del/bigwins-trader
BR=paper-record
MAX=$((5*1024*1024))
PUSH=1; [ "${1:-}" = "--no-push" ] && PUSH=0
log(){ echo "[backup_paper_record $(date -u +%FT%TZ)] $*"; }

# --- sources must exist (a wiped scratchpad must never produce a commit) ---
for d in "$B/bigwins_forward/code" "$B/onedrive/research2/68_forward_record" "$B/bigwins_forward/out/paper_state"; do
  [ -d "$d" ] || { log "FATAL: source missing: $d"; exit 2; }
done

# --- backup working copy: separate clone, orphan branch, never the trading tree ---
if [ ! -d "$R/.git" ]; then
  log "cloning $URL -> $R"
  git clone --depth 1 --no-checkout "$URL" "$R"
  cd "$R"
  if git ls-remote --exit-code --heads origin "$BR" >/dev/null; then
    git fetch --depth 1 origin "$BR:$BR" && git checkout "$BR"
  else
    git checkout --orphan "$BR"; git rm -rq --cached . || true
    find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  fi
fi
cd "$R"
cur=$(git symbolic-ref --short HEAD)
[ "$cur" = "$BR" ] || { log "FATAL: $R is on '$cur', expected $BR"; exit 3; }

# --- copy (relative layout = scratchpad layout) ---
excluded(){  # $1 = path relative to $B
  case "$1" in
    bigwins_forward/data/*|*/__pycache__/*|*.npz|*.pkl|*.gz|*.zip|*.parquet|*.feather|*.h5|*.lock|*.tmp|*/.daily.lock|*/.intraday.lock) return 0;;
  esac
  return 1
}
n=0; skipped=0
copy_tree(){  # $1 = dir relative to $B, $2.. = find name filters (optional)
  local rel=$1; shift
  [ -d "$B/$rel" ] || return 0
  while IFS= read -r -d '' f; do
    local p=${f#"$B/"}
    if excluded "$p"; then continue; fi
    local sz; sz=$(stat -c %s "$f")
    if [ "$sz" -gt "$MAX" ]; then skipped=$((skipped+1)); log "skip >5MB: $p"; continue; fi
    mkdir -p "$R/$(dirname "$p")"
    if ! cmp -s "$f" "$R/$p"; then cp -p "$f" "$R/$p"; fi
    n=$((n+1))
  done < <(find "$B/$rel" -type f "$@" -print0)
}
copy_tree bigwins_forward/code \( -name '*.py' -o -name '*.sh' -o -name '*.md' -o -name '*.txt' -o -name '*.yaml' -o -name '*.json' \)
copy_tree onedrive/research2/68_forward_record
copy_tree bigwins_forward/out/paper_state
copy_tree bigwins_forward/out/multi \( -name '*.json' -o -name '*.md' -o -name '*.csv' -o -name '*.log' -o -name '*.txt' \)
copy_tree bigwins_forward/out \( -name '*.md' -o -name '*.txt' -o -name '*.csv' -o -name '*.json' -o -name '*.jsonl' -o -name '*.log' \)
while IFS= read -r -d '' f; do  # research reports (top level of research2 only)
  p=${f#"$B/"}; sz=$(stat -c %s "$f")
  if [ "$sz" -gt "$MAX" ]; then skipped=$((skipped+1)); log "skip >5MB: $p"; continue; fi
  mkdir -p "$R/$(dirname "$p")"; cmp -s "$f" "$R/$p" || cp -p "$f" "$R/$p"; n=$((n+1))
done < <(find "$B/onedrive/research2" -maxdepth 1 -type f -name '*.md' -print0)
log "sources seen: $n files (skipped >5MB: $skipped)"

# --- README (only written if absent; edit it in the repo if needed) ---
if [ ! -f README.md ]; then cat > README.md <<'EOF'
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
EOF
fi

# --- manifest ---
find . -type f ! -path './.git/*' ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256

# --- secret scan (staged candidates = whole tree) ---
pat='(api_token=[A-Za-z0-9.]{12,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|gho_[A-Za-z0-9]{30,}|\bsk-[A-Za-z0-9_-]{20,}|\bsk-ant-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(api[_-]?key|secret|password|passwd|token)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9._/+-]{16,}["'"'"'])'
if hits=$(grep -rIEn --exclude-dir=.git --exclude=MANIFEST.sha256 "$pat" . | head -20) && [ -n "$hits" ]; then
  log "FATAL: possible secrets found - nothing committed:"; echo "$hits"; exit 4
fi
log "secret scan clean"

# --- commit only if changed ---
git add -A
if git diff --cached --quiet; then log "no changes; nothing to commit"; else
  cnt=$(git ls-files | wc -l)
  git commit -q -m "paper-record backup $(date -u +%F) ($cnt files)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_018hu5E9BZNjhiJCsGY2xZJu"
  log "committed $(git rev-parse --short HEAD)"
fi

# --- push (never force) ---
[ "$PUSH" = 1 ] || { log "--no-push: done"; exit 0; }
if [ "$(git rev-parse HEAD)" = "$(git ls-remote origin "refs/heads/$BR" 2>/dev/null | cut -f1)" ]; then
  log "origin/$BR up to date"; exit 0; fi
for i in 1 2; do
  if out=$(git -c push.negotiate=true push -u origin "$BR" 2>&1); then echo "$out" | tail -2; log "pushed"; exit 0; fi
  echo "$out" | tail -5
  if [ $i = 1 ] && echo "$out" | grep -q '429'; then log "HTTP 429; retry in 5 s"; sleep 5; else break; fi
done
log "FATAL: push failed"; exit 5
