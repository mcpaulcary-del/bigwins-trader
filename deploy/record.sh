# shellcheck shell=bash
# bigwins record ... : the Big Wins PAPER record on this server (BF-D93). Sourced by
# deploy/bigwins.sh (it uses its helpers: g y r confirm dc envval onedrive_ok market_open
# guard_market record_result info_dir STATE SECRETS ETC REPO DEPLOY OD_REMOTE OD_PATH
# BACKUP_DIR BKEY). PAPER ONLY: nothing here places, approves or cancels an order.
#
#   bigwins record status                 writer, epoch, head, jobs, disk, compare
#   bigwins record view on|off            show the record in the app from a read-only copy
#   sudo bigwins record seed              copy the record and its data from OneDrive, check every file
#   sudo bigwins record shadow on|off     the parallel run (the cloud stays the only writer)
#   sudo bigwins record cutover           take the record over (12 characters to compare)
#   sudo bigwins record handback          hand it back to the research environment
#   bigwins record requests               research entries waiting for your yes
#   bigwins record run <chain>            one timer's work now (morning collect newsc intraday
#                                         daily multi usfwd compare relay)
#
# The jobs run the research code UNEDITED in the record container (deploy/record.Dockerfile:
# the cloud's Python and libraries), with the record tree mounted at the cloud's own path.
# uid 10002, read-only root file system, no capabilities, no Docker socket; its own egress
# network only for the jobs that download, no network at all for the rest.

REC_TREE=/srv/bwrecord                       # the canonical record tree (after cut-over)
REC_SHADOW=/srv/bwrecord_shadow              # the parallel run's tree (never the record)
REC_MIRROR=/srv/bwrecord_cloudmirror         # read-only clone of the paper-record branch
REC_VIEW=/var/lib/bigwins/recordview         # what the app shows (a copy; display only)
RELAY=/var/lib/bigwins/relay                 # outbox, inbox/raw, inbox/validated, state
REC_IMAGE=bigwins-record                     # :local, built from deploy/record.Dockerfile
REC_UID=10002                                # the record's own user (not the trader's 10001)
REC_NET=bigwins_record_egress
REC_MODE_FILE=$ETC/record_mode               # off | view | shadow | writer (root-only, not in git)
REC_CLOUD=/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad  # the path the code names
REC_RECORD=onedrive/research2/68_forward_record
REC_BRANCH=paper-record
REC_TOOLS=$REPO/record/tools/bwrec.py
REC_UNIT_DIR=/etc/systemd/system

rec_mode() {  # off unless the owner switched it on (a pushed commit cannot change it)
  local m; m=$(head -c 12 "$REC_MODE_FILE" 2>/dev/null | tr -d '[:space:]')
  case "$m" in view|shadow|writer) echo "$m";; *) echo off;; esac
}

rec_set_mode() { mkdir -p "$ETC" && printf '%s\n' "$1" > "$REC_MODE_FILE" && chmod 644 "$REC_MODE_FILE"; }

rec_root() { if [ "$(rec_mode)" = writer ]; then echo "$REC_TREE"; else echo "$REC_SHADOW"; fi; }

rec_info() {  # where the announcements archive is written: the shadow's own folder until cut-over
  if [ "$(rec_mode)" = writer ]; then info_dir; else echo "$REC_SHADOW/info"; fi
}

rec_relay_remote() {  # the OneDrive folder both sides use (a second remote may be set by the owner)
  local v; v=$(head -c 200 "$ETC/relay_remote" 2>/dev/null | tr -d '\n')
  echo "${v:-$OD_REMOTE:Big Wins relay}"
}

rec_as() {  # run a command as the record's user (never root), no extra groups
  if [ "$(id -u)" = 0 ]; then setpriv --reuid="$REC_UID" --regid="$REC_UID" --clear-groups "$@"; else "$@"; fi
}

rec_tool() {  # the record tools on the host, reading only (root)
  BW_ROOT="${REC_ROOT_OVERRIDE:-$(rec_root)}" BW_RECORD_HOST=server python3 -I "$REC_TOOLS" "$@"
}

rec_tool_u() {  # the record tools writing into the tree: as the record's user
  rec_as env BW_ROOT="${REC_ROOT_OVERRIDE:-$(rec_root)}" BW_RECORD_HOST=server python3 -I "$REC_TOOLS" "$@"
}

rec_dirs() {  # the folders, once (root only)
  mkdir -p "$RELAY/outbox" "$RELAY/inbox/raw" "$RELAY/inbox/validated" "$RELAY/inbox/rejected" \
    "$RELAY/done" "$RELAY/state" "$REC_VIEW" "$STATE/record"
  chown -R "$REC_UID:$REC_UID" "$RELAY/inbox" "$RELAY/done" 2>/dev/null
  chmod 755 "$RELAY" "$RELAY/inbox" "$RELAY/inbox/validated" "$REC_VIEW" 2>/dev/null
  id -u bwrecord >/dev/null 2>&1 || useradd --system --uid "$REC_UID" --no-create-home --shell /usr/sbin/nologin bwrecord 2>/dev/null
  return 0
}

rec_build() {  # the record image; the build itself checks Python 3.13.18 and poppler 24.02.0
  (cd "$REPO" && docker build -q -t "$REC_IMAGE:local" -f deploy/record.Dockerfile . >/dev/null) \
    || { r "The record image did not build: the record jobs keep the previous image."; return 1; }
}

rec_ping() {  # job ok|fail|start: healthchecks.io, one check per job (slug), made on first ping
  local u; u=$(cat "$SECRETS/healthchecks_record_url" 2>/dev/null)
  case "$u" in https://*) ;; *) return 0;; esac
  local tail=""; case "$2" in fail) tail=/fail;; start) tail=/start;; esac
  curl -fsS -m 10 -o /dev/null "${u%/}/bigwins-$1$tail?create=1" || true
}

rec_event() {  # json: to the app (Health, missed-job alarm, Inbox); kept while the trader is down
  mkdir -p "$STATE/record"
  printf '%s\n' "$1" >> "$STATE/record/outbox.jsonl"
  rec_flush
}

rec_flush() {  # each event once, oldest first
  local f="$STATE/record/outbox.jsonl" line keep=""
  [ -s "$f" ] && [ -f "$DEPLOY/.env" ] || return 0
  dc exec -T trader true >/dev/null 2>&1 || return 0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    printf '%s' "$line" | dc exec -T trader trader-bf server-jobs record >/dev/null 2>&1 || keep="$keep$line"$'\n'
  done < "$f"
  printf '%s' "$keep" > "$f"
}

rec_job_event() {  # job rc json-or-text: one "job" event from a job's last output line
  JOB="$1" RC="$2" RES="$3" MODE="$(rec_mode)" python3 -c 'import json,os,time
e=os.environ
try: r=json.loads(e["RES"])
except ValueError: r={"error":e["RES"][-300:]}
if not isinstance(r,dict): r={}
ev={"kind":"job","job":e["JOB"],"ok":e["RC"]=="0" and bool(r.get("ok",True)),"mode":e["MODE"],
    "at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"day":time.strftime("%Y-%m-%d")}
for k in ("error","seconds","peak_mb","head","failed_steps","entries","line","pass","role"):
    if k in r: ev[k]=r[k]
print(json.dumps(ev))'
}

rec_run_job() {  # job [--dry-run]: one job in the record container; prints its JSON summary
  local job=$1 dry=${2:-} root info gate net led eod mem res rc ro=":ro"
  root=$(rec_root); info=$(rec_info)
  # a job that writes the ledger looks at the relay first: a newer fence there (a takeover,
  # or this server restored from an old backup) must stop it before it appends anything
  case "$job" in daily|multi|usfwd) [ "$(rec_mode)" = writer ] && rec_pull >/dev/null 2>&1;; esac
  gate=$(rec_tool gate "$job" --shipped "$RELAY/state/shipped_head" --relay "$RELAY/inbox/validated") || {
    res=$(rec_job_event "$job" 1 "{\"ok\":false,\"error\":\"$(printf '%s' "$gate" | tr -d '"\\' | head -c 240)\"}")
    rec_event "$res"; rec_ping "$job" fail; echo "$gate"; return 1; }
  read -r net led eod mem < <(rec_tool job "$job") || { echo "unknown job $job"; return 1; }
  docker image inspect "$REC_IMAGE:local" >/dev/null 2>&1 || rec_build || return 1
  [ "$job" = archive ] && ro=""  # only the archive job writes the announcements archive
  mkdir -p "$info/asx_notices" "$info/asic_short" && chown "$REC_UID:$REC_UID" "$info" "$info/asx_notices" "$info/asic_short"
  local a=(run --rm --name "bwrec-$job" -u "$REC_UID:$REC_UID" --read-only --tmpfs /tmp --cap-drop ALL
    --security-opt no-new-privileges:true --memory "${mem}m" --cpus 1.0 --pids-limit 256
    -e TZ=UTC -e HOME=/tmp -e BW_RECORD_HOST=server -e PYTHONDONTWRITEBYTECODE=1
    -e BW_RELAY_INBOX=/relay/inbox -e BW_RELAY_FENCE=/relay/inbox/fence.json
    -v "$root:$REC_CLOUD"
    -v "$REPO/record/code:$REC_CLOUD/bigwins_forward/code:ro"
    -v "$REPO/record/data_foundation_code:$REC_CLOUD/data_foundation/code:ro"
    -v "$info/asx_notices:$REC_CLOUD/bigwins_forward/data/asx_notices$ro"
    -v "$info/asic_short:$REC_CLOUD/bigwins_forward/data/asic_short$ro"
    -v "$REPO/record:/opt/bwrecord/record:ro" -v "$RELAY/inbox/validated:/relay/inbox:ro")
  if [ "$net" = 1 ]; then
    docker network inspect "$REC_NET" >/dev/null 2>&1 || docker network create "$REC_NET" >/dev/null
    a+=(--network "$REC_NET")
  else
    a+=(--network none)
  fi
  if [ "$eod" = 1 ]; then  # the token file is mounted, never read here, never on a command line
    a+=(-v "$SECRETS/eodhd_api_token:/run/secrets/eodhd_api_token:ro"
        -e "BW_EODHD_MODE=$(head -c 6 "$ETC/eodhd_auth_mode" 2>/dev/null | tr -cd 'a-z' | grep -E '^(header|query)$' || echo header)")
  fi
  rec_ping "$job" start
  mkdir -p "$STATE/record"
  # shellcheck disable=SC2086
  docker "${a[@]}" "$REC_IMAGE:local" python3 -I /opt/bwrecord/record/tools/bwrec.py run-job "$job" $dry \
    > "$STATE/record/$job.out" 2>> "$STATE/record/$job.log"; rc=$?
  res=$(tail -1 "$STATE/record/$job.out")
  case "$res" in "{"*) ;; *) res='{"ok":false,"error":"the job ended without a result (see deploy/.worker/record/'"$job"'.log)"}';; esac
  cat "$STATE/record/$job.out" >> "$STATE/record/$job.log"
  if [ "$(stat -c %s "$STATE/record/$job.log" 2>/dev/null || echo 0)" -gt 2097152 ]; then
    tail -c 400000 "$STATE/record/$job.log" > "$STATE/record/$job.log.new" && mv -f "$STATE/record/$job.log.new" "$STATE/record/$job.log"
  fi
  rec_event "$(rec_job_event "$job" "$rc" "$res")"
  if [ "$rc" = 0 ]; then rec_ping "$job" ok; else rec_ping "$job" fail; fi
  echo "$res"
  return $rc
}

rec_pull() {  # OneDrive inbox -> raw -> validated (fixed names and sizes only; nothing is run)
  onedrive_ok || { echo "relay: OneDrive is not connected (bigwins onedrive)"; return 1; }
  rec_dirs
  rclone copy "$(rec_relay_remote)/inbox" "$RELAY/inbox/raw" --max-age 21d --max-size 400M >/dev/null 2>&1 \
    || { echo "relay: the pull from OneDrive failed"; return 1; }
  chown -R "$REC_UID:$REC_UID" "$RELAY/inbox/raw"
  local res sum
  res=$(rec_as python3 -I "$REC_TOOLS" validate "$RELAY/inbox/raw" "$RELAY/inbox/validated" --keep-raw) || return 1
  sum=$(printf '%s' "$res" | python3 -c 'import hashlib,json,sys
print(hashlib.sha256(json.dumps(json.load(sys.stdin).get("rejected", [])).encode()).hexdigest()[:16])' 2>/dev/null)
  case "$res" in *'"rejected": []'*) ;; *)  # a file that should not be there: tell the owner once
    if [ "$(cat "$RELAY/state/rejected_told" 2>/dev/null)" != "$sum" ]; then
      rec_event "$(RES="$res" python3 -c 'import json,os,time
r=json.loads(os.environ["RES"]); print(json.dumps({"kind":"relay","ok":False,"at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"rejected":r.get("rejected",[])[:5]}))')"
      printf '%s' "$sum" > "$RELAY/state/rejected_told"
    fi;;
  esac
  rec_reports
  echo "relay: $res"
}

rec_reports() {  # a new nightly report in the relay: one Inbox message for it
  local d day told
  for d in "$RELAY"/inbox/validated/reports/*/; do
    [ -s "$d/report.json" ] || continue
    day=$(basename "$d"); told="$RELAY/state/report_told_$day"
    [[ "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || continue
    [ -f "$told" ] && [ "$(cat "$told")" = "$(sha256sum < "$d/report.json" | cut -c1-16)" ] && continue
    rec_event "{\"kind\":\"report\",\"ok\":true,\"day\":\"$day\",\"at\":\"$(date +%Y-%m-%dT%H:%M:%S%z)\"}"
    sha256sum < "$d/report.json" | cut -c1-16 > "$told"
  done
  find "$RELAY/state" -name 'report_told_*' -mtime +40 -delete 2>/dev/null
  return 0
}

rec_export() {  # [day]: stage the readable record, send it to OneDrive, note the shipped head
  local day=${1:-$(date +%F)} st res root ob="$RELAY/outbox" rem; root=$(rec_root)
  [ -f "$root/$REC_RECORD/LEDGER.jsonl" ] || return 0
  rec_dirs
  rem="$(rec_relay_remote)/outbox"
  # the parallel run's files go under outbox/shadow: never where the record's own files are
  [ "$(rec_mode)" = shadow ] && { ob="$ob/shadow"; rem="$rem/shadow"; }
  st=$(mktemp) || return 1
  DISK="$(rec_tool disk "$root" 2>/dev/null)" MODE="$(rec_mode)" COMMIT="$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" \
    python3 -c 'import json,os,time
d=(os.environ.get("DISK") or "? 0").split()
print(json.dumps({"mode":os.environ["MODE"],"disk_level":d[0],"disk_free_gb":float(d[1]),"code_commit":os.environ["COMMIT"],
 "made":time.strftime("%Y-%m-%dT%H:%M:%S%z")}))' > "$st"
  res=$(rec_tool export "$ob" --day "$day" --status "$st"); rm -f "$st"
  case "$res" in "{"*) ;; *) rec_event '{"kind":"job","job":"export","ok":false,"error":"the export could not be staged"}'; rec_ping export fail; return 1;; esac
  if onedrive_ok && rclone copy "$ob" "$rem" >/dev/null 2>&1; then
    printf '%s' "$res" | python3 -c 'import json,sys; print(json.load(sys.stdin)["head"])' > "$RELAY/state/shipped_head.new" \
      && mv -f "$RELAY/state/shipped_head.new" "$RELAY/state/shipped_head"
    rec_event "$(rec_job_event export 0 "$res")"; rec_ping export ok
    rec_view_refresh
    return 0
  fi
  rec_event '{"kind":"job","job":"export","ok":false,"error":"the record could not be sent to OneDrive; the next record job waits for it"}'
  rec_ping export fail
  rec_view_refresh
  return 1
}

rec_view_copy() {  # src-tree source note: the display copy the app reads (never the ledger or data)
  mkdir -p "$REC_VIEW" && chmod 755 "$REC_VIEW"
  python3 -I "$REC_TOOLS" view-copy "$1" "$REC_VIEW" "$2" "$3" >/dev/null
}

rec_mirror_fetch() {  # the cloud's nightly paper-record push, with the existing READ-ONLY key
  local url; url=$(git -C "$REPO" remote get-url origin 2>/dev/null) || return 1
  if [ ! -d "$REC_MIRROR/.git" ]; then
    git -c core.sshCommand="$(git -C "$REPO" config core.sshCommand 2>/dev/null || echo ssh)" \
      clone -q --depth 5 --single-branch -b "$REC_BRANCH" "$url" "$REC_MIRROR" 2>/dev/null || return 1
    git -C "$REC_MIRROR" config core.sshCommand "$(git -C "$REPO" config core.sshCommand 2>/dev/null || echo ssh)"
  fi
  git -C "$REC_MIRROR" fetch -q --depth 5 origin "$REC_BRANCH" 2>/dev/null \
    && git -C "$REC_MIRROR" reset -q --hard "origin/$REC_BRANCH" 2>/dev/null
}

rec_view_refresh() {  # writer: this server's record; before that: the cloud's nightly copy
  case "$(rec_mode)" in
    writer) rec_view_copy "$REC_TREE" "this server" "the record is written on this server";;
    view|shadow)
      rec_mirror_fetch || { echo "view: the paper-record branch could not be fetched"; return 1; }
      rec_view_copy "$REC_MIRROR" "the research environment (nightly copy $(git -C "$REC_MIRROR" log -1 --format=%h 2>/dev/null))" \
        "read-only copy; the record is still written in the research environment";;
    *) return 0;;
  esac
}

rec_today_session() { [ "$(date +%u)" -le 5 ]; }  # weekdays; the jobs themselves know the holidays

rec_chain() {  # chain: what one timer does, under the one record lock
  local chain=${1:-} mode rc=0 day res
  mode=$(rec_mode)
  [ "$mode" = off ] && { echo "the paper record is not on this server yet (bigwins record status)"; return 0; }
  mkdir -p "$STATE/record"
  exec 6>"$STATE/record/chain.lock"
  flock -w "${REC_LOCK_WAIT:-5400}" 6 || { echo "another record job is still running"; return 1; }
  day=$(date +%F)
  case "$chain:$mode" in
    relay:*) rec_pull; rec_view_refresh; return 0;;
    *:view) echo "view only: the record's jobs still run in the research environment"; return 0;;
    morning:*)
      rec_run_job archive >/dev/null || rc=1
      if rec_today_session && [ "$(date +%H%M)" -lt 1000 ]; then rec_run_job newsc-prepare >/dev/null || rc=1; fi
      rec_export "$day" || rc=1;;
    collect:writer) rec_run_job collect >/dev/null || rc=1;;
    newsc:shadow) rec_pull >/dev/null; rec_newsc --dry-run || rc=1;;
    newsc:writer) rec_pull >/dev/null; rec_newsc "" || rc=1;;
    intraday:writer) rec_run_job intraday >/dev/null || rc=1; rec_export "$day" || rc=1;;
    daily:writer)
      rec_run_job daily >/dev/null || rc=1
      rec_bundle_out "$day"
      rec_export "$day" || rc=1;;
    daily:shadow) rec_shadow_day "$day" || rc=1;;
    multi:writer|usfwd:writer) rec_run_job "$chain" >/dev/null || rc=1; rec_export "$day" || rc=1;;
    compare:shadow) rec_compare "$day" || rc=1;;
    *) echo "nothing to do for '$chain' in mode $mode";;
  esac
  return $rc
}

rec_newsc() {  # [--dry-run]: record what the raters sent, only when a day is waiting in the relay
  local dry=${1:-} rc=0 did=0
  if [ "$(date +%H%M)" -lt 1000 ] && rec_tool newsc-pending "$RELAY/inbox/validated" record $dry >/dev/null; then
    rec_run_job newsc-record $dry >/dev/null || rc=1; did=1
  fi
  if rec_tool newsc-pending "$RELAY/inbox/validated" drops $dry >/dev/null; then
    rec_run_job newsc-drops-record $dry >/dev/null || rc=1; did=1
  fi
  [ "$did" = 1 ] && [ -z "$dry" ] && { rec_export "$(date +%F)" || rc=1; }
  return $rc
}

rec_bundle_out() {  # day: the day's raw inputs for the standby replay (owner's own OneDrive only)
  local day=$1 f="$RELAY/outbox/bundles/bundle_$1.tar"
  mkdir -p "$RELAY/outbox/bundles" && chown "$REC_UID:$REC_UID" "$RELAY/outbox/bundles"
  rec_tool_u bundle-make "$day" "$f" >/dev/null 2>&1 || return 1
  rec_tool_u manifest "$day" --archive-day "$(rec_prev_day "$day")" --out "$RELAY/outbox/bundles/manifest_$day.json" >/dev/null 2>&1
  find "$RELAY/outbox/bundles" -name 'bundle_*.tar' -mtime +10 -delete 2>/dev/null
  return 0
}

rec_prev_day() { date -d "$1 -$([ "$(date -d "$1" +%u)" = 1 ] && echo 3 || echo 1) day" +%F; }  # the weekday before

rec_shadow_day() {  # day: apply the cloud's bundle of the day, then replay it (no downloads)
  local day=$1 b="$RELAY/inbox/validated/bundles/bundle_$1.tar" done="$STATE/record/replayed_$1"
  [ -f "$done" ] && return 0
  rec_pull >/dev/null
  [ -f "$b" ] || { echo "shadow: the cloud's bundle for $day has not arrived yet"; return 1; }
  rec_tool_u bundle-apply "$b" || return 1
  rec_run_job replay >/dev/null || return 1
  date > "$done"; find "$STATE/record" -name 'replayed_*' -mtime +30 -delete 2>/dev/null
  return 0
}

rec_compare() {  # day: the 21:30 comparison (retried by the timer until the cloud's files are here)
  local day=$1 man="$RELAY/inbox/validated/bundles/manifest_$1.json" out res rc
  [ -f "$STATE/record/compared_$day" ] && return 0
  rec_shadow_day "$day" || { [ "$(date +%H%M)" -ge 2300 ] && rec_event "{\"kind\":\"compare\",\"ok\":false,\"pass\":false,\"day\":\"$day\",\"line\":\"Shadow compare $day: NOT RUN (the cloud's files or the replay are missing)\"}"; return 1; }
  [ -f "$man" ] || { rec_mirror_fetch; man="$REC_MIRROR/bigwins_forward/out/sync/manifest_$day.json"; }
  [ -f "$man" ] || { echo "compare: no cloud manifest for $day yet"; return 1; }
  out=$(rec_tool_u compare "$day" "$man"); rc=$?
  res=$(cat "$(rec_root)/bigwins_forward/out/sync/compare_$day.json" 2>/dev/null)
  rec_event "$(DAY="$day" RES="$res" LINE="$out" python3 -c 'import json,os
try: r=json.loads(os.environ["RES"])
except ValueError: r={}
c=r.get("classes") or {}
print(json.dumps({"kind":"compare","ok":bool(r.get("pass")),"pass":bool(r.get("pass")),"day":os.environ["DAY"],
 "line":(r.get("line") or os.environ["LINE"])[:300],
 "diffs":[d.get("path","")[-120:] for k in "ABCD" for d in (c.get(k) or {}).get("diffs",[])][:8]}))')"
  date > "$STATE/record/compared_$day"
  rec_export "$day" >/dev/null  # the line travels to the cloud's daily report
  if [ "$rc" = 0 ]; then rec_ping compare ok; else rec_ping compare fail; fi
  echo "$out"
  return $rc
}

# ---------------------------------------------------------------- timers (version-aware, plan E4)
rec_units_sum() { python3 -I "$REC_TOOLS" units-sum "$DEPLOY/bigwins.sh" 2>/dev/null; }

rec_units_names() { ls "$REC_UNIT_DIR" 2>/dev/null | sed -n 's/^\(bigwins-rec-[a-z]*\)\.timer$/\1/p'; }

rec_ensure_timers() {  # write the record timers when missing OR when this version's set differs
  [ "$(id -u)" = 0 ] && [ -f "$REC_UNIT_DIR/bigwins-worker.timer" ] || return 0
  local want have n; want=$(rec_units_sum); have=$(cat "$REC_UNIT_DIR/.bigwins-rec-units" 2>/dev/null)
  [ -n "$want" ] && [ "$want" = "$have" ] && return 0
  for n in $(rec_units_names); do systemctl disable --now "$n.timer" >/dev/null 2>&1; rm -f "$REC_UNIT_DIR/$n.timer" "$REC_UNIT_DIR/$n.service"; done
  python3 -I "$REC_TOOLS" units "$REC_UNIT_DIR" "$DEPLOY/bigwins.sh" >/dev/null || return 1
  systemctl daemon-reload
  for n in $(rec_units_names); do systemctl enable --now "$n.timer" >/dev/null 2>&1; done
  printf '%s' "$want" > "$REC_UNIT_DIR/.bigwins-rec-units"
}

rec_timer_states() {  # "rec-daily:1 ..." for Health
  local n out=""
  for n in $(rec_units_names); do
    if systemctl is-enabled "$n.timer" >/dev/null 2>&1; then out="$out ${n#bigwins-}:1"; else out="$out ${n#bigwins-}:0"; fi
  done
  echo "$out"
}

rec_host_status() {  # JSON for the app's Health screen (no secrets, no data)
  local mode root; mode=$(rec_mode); root=$(rec_root)
  MODE="$mode" ST="$( [ "$mode" = shadow ] || [ "$mode" = writer ] && rec_tool status 2>/dev/null)" \
  DISK="$(python3 -I "$REC_TOOLS" disk "$( [ -d "$root" ] && echo "$root" || echo / )" 2>/dev/null)" \
  SHIPPED="$(head -c 64 "$RELAY/state/shipped_head" 2>/dev/null)" \
  VIEW="$(head -c 400 "$REC_VIEW/source.json" 2>/dev/null)" \
  PING_SET="$(case "$(cat "$SECRETS/healthchecks_record_url" 2>/dev/null)" in https://*) echo 1;; *) echo 0;; esac)" \
  WAITING="$(ls "$RELAY/inbox/validated/ledger_requests"/*.json 2>/dev/null | wc -l) $(ls "$RELAY/done"/*.json 2>/dev/null | wc -l)" \
  TIMERS="$(rec_timer_states)" python3 -c 'import json,os
e=os.environ
def j(k):
    try: return json.loads(e.get(k) or "{}")
    except ValueError: return {}
d=(e.get("DISK") or "? 0").split(); w=(e.get("WAITING") or "0 0").split()
print(json.dumps({"mode":e["MODE"],"status":j("ST"),"disk_level":d[0],"disk_free_gb":float(d[1]) if len(d)>1 else None,
 "shipped_head":e.get("SHIPPED",""),"view":j("VIEW"),"ping_set":e.get("PING_SET")=="1",
 "requests_waiting":max(int(w[0])-int(w[1]),0),"timers":{k:v=="1" for k,_,v in (x.partition(":") for x in e.get("TIMERS","").split())}}))'
}

# ---------------------------------------------------------------- owner commands
rec_status() {
  local mode; mode=$(rec_mode)
  echo "== Paper record on this server: mode $mode"
  case "$mode" in
    off) echo "  Not here yet. The record is written in the research environment."
         echo "  Show it in the app from a read-only copy: sudo bigwins record view on";;
    view) echo "  Display only: the app shows the research environment's nightly copy."
          python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("  source:", d.get("source"), "| refreshed", d.get("refreshed"))' "$REC_VIEW/source.json" 2>/dev/null;;
    *) rec_tool status | python3 -c 'import json,sys
d=json.loads(sys.stdin.read() or "{}")
print(f"  writer = {d.get(\"writer\",\"?\")} ({d.get(\"role\",\"?\")}), epoch {d.get(\"epoch\",\"?\")}, {d.get(\"seq\",0)} entries, head {str(d.get(\"head\",\"\"))[:12]}, chain {\"ok\" if d.get(\"chain_ok\") else \"BROKEN\"}")';;
  esac
  echo "  disk: $(python3 -I "$REC_TOOLS" disk "$( [ -d "$(rec_root)" ] && rec_root || echo / )" 2>/dev/null | awk '{print $2" GB free ("$1")"}')"
  echo "  relay: $(onedrive_ok && echo "OneDrive connected" || echo "OneDrive NOT connected (bigwins onedrive)") · shipped head $(head -c 12 "$RELAY/state/shipped_head" 2>/dev/null || echo none)"
  echo "  timers: $(rec_timer_states)"
  ls "$STATE"/record/compared_* >/dev/null 2>&1 && echo "  last compare: $(python3 -c 'import json,sys,glob
fs=sorted(glob.glob(sys.argv[1]+"/bigwins_forward/out/sync/compare_*.json"))
print(json.load(open(fs[-1])).get("line","") if fs else "none")' "$(rec_root)" 2>/dev/null)"
  return 0
}

rec_view() {  # on|off: the app shows the record from a read-only copy (no job runs here)
  [ "$(id -u)" = 0 ] || { r "Run as root (sudo bigwins record view $1)."; return 1; }
  case "${1:-}" in
    on) case "$(rec_mode)" in shadow|writer) g "Already on: the record is on this server."; return 0;; esac
        rec_dirs; rec_set_mode view; rec_ensure_timers
        if rec_view_refresh; then g "The app now shows the paper record (the research environment's nightly copy, read-only)."
        else y "Switched on, but the copy could not be fetched yet; it retries every 10 minutes."; fi;;
    off) [ "$(rec_mode)" = view ] && rec_set_mode off && g "Off: the app shows no record copy.";;
    *) echo "Usage: bigwins record view on|off";;
  esac
}

rec_seed() {  # the record tree and its private data from OneDrive, every file checked
  [ "$(id -u)" = 0 ] || { r "Run as root (sudo bigwins record seed)."; return 1; }
  onedrive_ok || { r "Connect OneDrive first: bigwins onedrive (guide C8)."; return 1; }
  [ "$(rec_mode)" = writer ] && { r "The record is already written on this server: no seed."; return 1; }
  local free; free=$(python3 -I "$REC_TOOLS" disk / | awk '{print int($2)}')
  [ "${free:-0}" -ge 10 ] || { r "Only ${free} GB free: the parallel week needs at least 10 GB (20 GB to go live)."; return 1; }
  [ "${free:-0}" -ge 20 ] || y "Only ${free} GB free: enough for the parallel week, not for a year of the archive (plan 2.3)."
  rec_dirs
  mkdir -p "$REC_SHADOW" && chown "$REC_UID:$REC_UID" "$REC_SHADOW"
  y "Copying 'Big Wins seed data/record_tree' from OneDrive to $REC_SHADOW (this can take a while)..."
  rclone copy "$OD_REMOTE:Big Wins seed data/record_tree" "$REC_SHADOW" --exclude 'bigwins_forward/code/**' \
    --exclude 'data_foundation/code/**' || { r "The copy failed; nothing was switched on."; return 1; }
  chown -R "$REC_UID:$REC_UID" "$REC_SHADOW"
  if ! REC_ROOT_OVERRIDE="$REC_SHADOW" rec_tool seed-verify "$REC_SHADOW/SEED_MANIFEST.json"; then
    r "FAIL: the seed does not match the cloud's manifest (lines above). Nothing was switched on."; return 1
  fi
  [ -f "$REC_SHADOW/$REC_RECORD/WRITER.json" ] && mv -f "$REC_SHADOW/$REC_RECORD/WRITER.json" "$REC_SHADOW/$REC_RECORD/WRITER.cloud.json"
  REC_ROOT_OVERRIDE="$REC_SHADOW" rec_tool_u fence-init --writer server --role shadow --epoch 1 >/dev/null \
    || { r "Could not write the shadow's fence."; return 1; }
  rec_build || return 1
  docker run --rm --network none "$REC_IMAGE:local" pdftotext -v 2>&1 | grep -q 'version 24.02.0' \
    || { r "FAIL: the record image's pdftotext is not 24.02.0 (the cloud's)."; return 1; }
  g "PASS: seed in place and checked. Next: sudo bigwins record shadow on"
}

rec_shadow() {  # on|off: the parallel run
  [ "$(id -u)" = 0 ] || { r "Run as root (sudo bigwins record shadow $1)."; return 1; }
  case "${1:-}" in
    on) [ "$(rec_mode)" = writer ] && { r "The record is already written on this server."; return 1; }
        [ -f "$REC_SHADOW/$REC_RECORD/LEDGER.jsonl" ] || { r "No seed yet: sudo bigwins record seed"; return 1; }
        rec_set_mode shadow; rec_ensure_timers
        g "Parallel run ON. The cloud stays the only writer; one Inbox line each evening: Shadow compare: PASS.";;
    off) [ "$(rec_mode)" = shadow ] && rec_set_mode view && g "Parallel run off (the app still shows the read-only copy).";;
    *) echo "Usage: bigwins record shadow on|off";;
  esac
}

rec_set_env() {  # KEY VALUE in deploy/.env (the owner's file; the same way start-trader sets TRADER_CMD)
  python3 - "$DEPLOY/.env" "$1" "$2" <<'PY'
import sys
p, k, v = sys.argv[1:4]
lines = [x for x in open(p).read().splitlines() if not x.startswith(k + "=")]
lines.append(k + "=" + v)
open(p, "w").write("\n".join(lines) + "\n")
PY
}

rec_cutover() {  # plan 4.2 steps 3-5: the owner's one command on Saturday evening
  [ "$(id -u)" = 0 ] || { r "Run as root (sudo bigwins record cutover)."; return 1; }
  [ "$(rec_mode)" = shadow ] || { r "The parallel run is not on (mode $(rec_mode)): nothing to take over."; return 1; }
  market_open && { r "Not while the ASX is open."; return 1; }
  mkdir -p "$STATE/record"; exec 6>"$STATE/record/chain.lock"; flock -w 600 6 || { r "A record job is running; try again in a few minutes."; return 1; }
  local streak; streak=$(rec_tool streak 2>/dev/null || echo 0)
  if [ "${streak:-0}" -lt 5 ] && [ "${REC_FORCE:-}" != 1 ]; then
    r "Only $streak trading day(s) in a row compared identical; the rule is 5. Not taking over."
    r "(The engineer may override after writing down why: REC_FORCE=1 sudo -E bigwins record cutover.)"; return 1
  fi
  y "Fetching the research environment's final record (the handover commit)..."
  rec_mirror_fetch || { r "Could not fetch the paper-record branch; nothing changed."; return 1; }
  rec_pull >/dev/null
  local stage="$REC_SHADOW.cutover" head rec="$REC_RECORD"
  rm -rf "$stage" && mkdir -p "$stage/$rec" && cp -a "$REC_MIRROR/$rec/." "$stage/$rec/" && chown -R "$REC_UID:$REC_UID" "$stage"
  # 1. the offered record: chain verifies, last entry is the cloud's handover to this server, fence matches
  head=$(REC_ROOT_OVERRIDE="$stage" rec_tool accept --check) || { r "$head"; r "This is not a handover to this server. Nothing changed."; rm -rf "$stage"; return 1; }
  # 2. the cloud's final states and outputs are byte-identical to the shadow's
  if ! REC_ROOT_OVERRIDE="$REC_SHADOW" rec_tool same-as "$REC_MIRROR"; then
    r "The shadow's states or outputs differ from the cloud's final ones (above). Nothing changed."
    r "Tell Claude: the cloud cancels the handover and stays the writer (plan 4.4)."; rm -rf "$stage"; return 1
  fi
  echo
  echo "    Handover head, first 12 characters:   $head"
  echo
  local a; read -rp "Do they match the 12 characters in the Claude chat? Type yes to take over: " a
  [ "$a" = yes ] || { echo "Nothing changed."; rm -rf "$stage"; return 0; }
  # 3. install: the shadow's tree with the cloud's final record files laid over its record
  #    folder (ledger, fence, amendments, outputs), then the acceptance entry
  mkdir -p "$REC_SHADOW/shadow_kept" && cp -a "$REC_SHADOW/$rec/LEDGER.jsonl" "$REC_SHADOW/$rec/WRITER.json" "$REC_SHADOW/shadow_kept/" 2>/dev/null
  cp -a "$stage/$rec/." "$REC_SHADOW/$rec/" || { r "Could not install the record files; nothing was accepted."; return 1; }
  rm -rf "$stage"
  [ -e "$REC_TREE" ] && mv "$REC_TREE" "$REC_TREE.before-cutover.$(date +%s)"
  mv "$REC_SHADOW" "$REC_TREE" || { r "Could not move the tree to $REC_TREE."; return 1; }
  if ! REC_ROOT_OVERRIDE="$REC_TREE" rec_tool_u accept; then
    r "The acceptance entry was NOT written. The cloud is still the writer by its own ledger;"
    r "tell Claude to cancel the handover (plan 4.4)."; return 1
  fi
  # 4. the app (GO_LIVE_GUIDE C10): archive, RECORD_DIR, the switch, checks, restart, backup
  local info; info=$(info_dir)
  mkdir -p "$info" && cp -an "$REC_TREE/info/." "$info/" 2>/dev/null; chown -R "$REC_UID:$REC_UID" "$info"; chmod -R a+rX "$info"
  rec_set_mode writer
  if [ -f "$DEPLOY/.env" ]; then
    rec_set_env RECORD_DIR "$REC_TREE/$rec"
    python3 "$DEPLOY/set_login.py" --info-archive "$LOCAL" true || y "Could not switch info_archive.archive_enabled on in config/bfast.local.yaml."
    if golden_checks; then dc up -d && g "Trader and app restarted on the live record."
    else r "The record-data checks FAILED on the live record: the trader was not restarted. Tell Claude."; fi
  fi
  rec_ensure_timers
  rec_export "$(date +%F)" || y "The record could not be sent to OneDrive yet; it retries with the next job."
  do_backup >/dev/null 2>&1 && g "Backup made." || y "The backup did not finish; run: bigwins backup"
  g "Done. This server is the only writer of the paper record."
  rec_status
  echo "In the app: Server > Health shows 'Paper record: writer = this server'. Tell Claude: done."
}

rec_handback() {  # plan 5.1: a planned rollback; one more chained entry, no fork
  [ "$(id -u)" = 0 ] || { r "Run as root (sudo bigwins record handback)."; return 1; }
  [ "$(rec_mode)" = writer ] || { r "This server is not the writer."; return 1; }
  y "This hands the paper record back to the research environment. The record jobs here stop."
  confirm "Hand the record back?" || { echo "Nothing changed."; return 0; }
  mkdir -p "$STATE/record"; exec 6>"$STATE/record/chain.lock"; flock -w 1800 6 || { r "A record job is running; try again shortly."; return 1; }
  local head
  head=$(rec_tool_u handover) || { r "$head"; r "Nothing changed."; return 1; }
  rec_bundle_out "$(date +%F)"
  rec_export "$(date +%F)" || r "The export to OneDrive FAILED: run 'bigwins record run relay' and tell Claude before anything else."
  echo
  echo "    Handover head, first 12 characters:   $head"
  echo
  echo "Read these 12 characters to Claude. The server keeps collecting announcements; it no longer books the record."
}

rec_requests() {  # D6: research ledger entries wait for the owner's yes
  [ "$(rec_mode)" = writer ] || { echo "This server is not the writer: nothing to confirm here."; return 0; }
  rec_pull >/dev/null
  local list id a n=0
  list=$(rec_tool requests "$RELAY/inbox/validated" "$RELAY/done")
  [ -n "$list" ] || { echo "No research entries waiting."; return 0; }
  mkdir -p "$STATE/record"; exec 6>"$STATE/record/chain.lock"; flock -w 600 6 || { r "A record job is running; try again shortly."; return 1; }
  while IFS= read -r line; do
    case "$line" in UNREADABLE*) y "$line"; continue;; esac
    id=${line%% *}
    echo; echo "$line"
    read -rp "Add this entry to the ledger? (y = yes, n = leave it waiting) " a < /dev/tty
    if [ "$a" = y ] || [ "$a" = Y ]; then
      rec_tool_u requests "$RELAY/inbox/validated" "$RELAY/done" --apply "$id" && n=$((n+1))
    fi
  done <<<"$list"
  [ "$n" -gt 0 ] && { rec_export "$(date +%F)" && g "$n entr$([ "$n" = 1 ] && echo y || echo ies) added and sent; Claude sees the new head within minutes."; }
  return 0
}

# ---------------------------------------------------------------- backups (plan 2.4, D4)
rec_backup_sources() {  # "name|path" lines the nightly backup adds (small, daily-changing parts)
  local t; [ "$(rec_mode)" = writer ] && t=$REC_TREE || { [ "$(rec_mode)" = shadow ] && t=$REC_SHADOW; }
  [ -n "${t:-}" ] && [ -d "$t" ] || return 0
  local d
  for d in bigwins_forward/out bigwins_forward/data/bulk bigwins_forward/data/estimates_pit \
           bigwins_forward/data/newlist bigwins_forward/data/newsc asic_daily; do
    [ -d "$t/$d" ] && echo "record_$(echo "$d" | tr '/' '_')|$t/$d"
  done
  [ "$(rec_mode)" = shadow ] && [ -d "$t/$REC_RECORD" ] && echo "record_shadow|$t/$REC_RECORD"
  [ -d "$RELAY/done" ] && echo "record_relay_done|$RELAY/done"
  return 0
}

rec_info_light() {  # stage-dir: the info archive without its PDFs (lists, texts, markers, hashes)
  local info; info=$(rec_info)
  [ -d "$info" ] || info=$(info_dir)
  [ -d "$info" ] || return 1
  python3 -I "$REC_TOOLS" stage-light "$info" "$1" >/dev/null 2>&1 && echo "$1"
}

rec_backup_pdfs() {  # one encrypted file per finished archive day; 60 days kept off-site (D4)
  onedrive_ok && command -v age >/dev/null && [ -s "$BKEY" ] || return 0
  local info rcp list line day tmp; info=$(rec_info); [ -d "$info/asx_notices" ] || return 0
  rcp=$(age-keygen -y "$BKEY" 2>/dev/null) || return 1
  list=$(mktemp); rclone lsf "$OD_PATH/pdf" 2>/dev/null > "$list"
  python3 -I "$REC_TOOLS" pdf-plan "$info" "$list" | while read -r line day; do
    case "$line" in
      upload)
        tmp=$(mktemp /var/tmp/asxpdf.XXXXXX)
        if tar -C "$info/asx_notices/$day" -cf - pdf --exclude='*.txt' 2>/dev/null | age -r "$rcp" -o "$tmp" \
           && rclone copyto "$tmp" "$OD_PATH/pdf/asxpdf-$day.tar.age" >/dev/null 2>&1; then echo "pdf backup: $day sent"; fi
        rm -f "$tmp";;
      delete) rclone deletefile "$OD_PATH/pdf/$day" >/dev/null 2>&1 && echo "pdf backup: $day removed off-site (older than 60 days; kept on the server)";;
    esac
  done
  rm -f "$list"
}

rec_backup_set() {  # stores|base: the big, slowly-changing data as its own encrypted set (3 kept)
  onedrive_ok && command -v age >/dev/null && [ -s "$BKEY" ] || return 0
  [ "$(rec_mode)" = writer ] || return 0
  local set=$1 dirs sum rcp tmp name
  case "$set" in
    stores) dirs="bigwins_forward/data/eodhd fwd_multi/data";;
    base) dirs="data_foundation/out bigwins_lab company_study actuals deep84";;
    *) return 1;;
  esac
  local have=""; for d in $dirs; do [ -d "$REC_TREE/$d" ] && have="$have $d"; done
  [ -n "$have" ] || return 0
  # shellcheck disable=SC2086
  sum=$( (cd "$REC_TREE" && find $have -type f -printf '%P %s %T@\n' 2>/dev/null | sort | sha256sum | cut -c1-12) )
  [ "$(cat "$RELAY/state/set_$set" 2>/dev/null)" = "$sum" ] && return 0
  rcp=$(age-keygen -y "$BKEY" 2>/dev/null) || return 1
  name="bigwins-$set-$(date +%Y%m%d)-$sum.tar.age"; tmp=$(mktemp /var/tmp/bwset.XXXXXX)
  # shellcheck disable=SC2086
  if tar -C "$REC_TREE" -cf - $have 2>/dev/null | age -r "$rcp" -o "$tmp" && rclone copyto "$tmp" "$OD_PATH/sets/$name" >/dev/null 2>&1; then
    printf '%s' "$sum" > "$RELAY/state/set_$set"
    rclone lsf "$OD_PATH/sets" --include "bigwins-$set-*" 2>/dev/null | sort | head -n -3 | while read -r old; do
      rclone deletefile "$OD_PATH/sets/$old" >/dev/null 2>&1
    done
    echo "backup set $set: sent ($name)"
  fi
  rm -f "$tmp"
}

cmd_record() {
  case "${1:-status}" in
    status) rec_status;;
    view) rec_view "${2:-}";;
    seed) rec_seed;;
    shadow) rec_shadow "${2:-}";;
    cutover) rec_cutover;;
    handback) rec_handback;;
    requests) rec_requests;;
    run) rec_chain "${2:-}";;
    job) rec_run_job "${2:-}" "${3:-}";;  # the engineer: one job now
    build) rec_build && g "Record image built.";;
    timers) rec_ensure_timers && rec_timer_states;;
    *) echo "Usage: bigwins record [status|view on|off|seed|shadow on|off|cutover|handback|requests|run <chain>]";;
  esac
}
