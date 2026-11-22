#!/usr/bin/env bash
# bigwins - a simple menu for the owner on the server. PAPER ONLY.
# Install once:  ln -sf /srv/asx-trader/deploy/bigwins.sh /usr/local/bin/bigwins
# Then type:     bigwins          (menu)   or   bigwins status | logs | update | restart |
#                secret <name> | check | claude | remote | app | demo | login | vapid |
#                install-worker | worker | backup | restore-test | onedrive | restore |
#                start-trader <date> | ibkr | seed-data
# Server-only settings (your Tailscale log-in, tax rate, paper account id...) go in
# config/bfast.local.yaml: not in git, laid over config/bfast.yaml (BF-D39).
set -uo pipefail

REPO=/srv/asx-trader
DEPLOY=$REPO/deploy
SECRETS=$DEPLOY/secrets
CONFIG=$REPO/config/bfast.yaml
LOCAL=$REPO/config/bfast.local.yaml
# 8 typed + 3 made here = the 11 secret files (review F16; telegram_bot_token only with Telegram)
BASE_SECRETS="tws_password db_password totp_seed eodhd_api_token healthchecks_url ibkr_flex_token ibkr_flex_query_id db_dashboard_password"
APP_SECRETS="vapid_private_key app_proxy_key worker_job_key"  # BF-D40, BF-D46, BF-D48: made here
BACKUP_DIR=/var/backups/bigwins              # BF-D64: local backups (root only)
BKEY=/root/.bigwins-backup/backup.key         # the backup recovery key (age; root only)
OD_REMOTE=bigwins-onedrive                    # the rclone remote for OneDrive
OD_PATH="$OD_REMOTE:Big Wins server backups"
STATE=$DEPLOY/.worker  # BF-D45: the worker's own notes (the commit before the last update)
BRANCH=bigwins-fast
TYPED_SECRETS="tws_password db_password totp_seed eodhd_api_token healthchecks_url ibkr_flex_token ibkr_flex_query_id telegram_bot_token"

g() { printf '\033[32m%s\033[0m\n' "$*"; }
y() { printf '\033[33m%s\033[0m\n' "$*"; }
r() { printf '\033[31m%s\033[0m\n' "$*"; }

channel() {  # BF-D40: notify.channel (app | telegram | both); the local file wins
  local c=""
  [ -f "$LOCAL" ] && c=$(sed -n 's/^  channel: *\([a-z]*\).*/\1/p' "$LOCAL" | head -1)
  [ -n "$c" ] || c=$(sed -n 's/^  channel: *\([a-z]*\).*/\1/p' "$CONFIG" 2>/dev/null | head -1)
  echo "${c:-app}"
}

all_secrets() {  # the files the stack needs for the channel (the generated ones are made here)
  case "$(channel)" in
    telegram) echo "$BASE_SECRETS telegram_bot_token";;
    both) echo "$BASE_SECRETS $APP_SECRETS telegram_bot_token";;
    *) echo "$BASE_SECRETS $APP_SECRETS";;
  esac
}
ALL_SECRETS=$(all_secrets)

dc() {  # docker compose, with the Telegram file when Telegram is on (BF-D40)
  local f="-f docker-compose.yml"
  case "$(channel)" in telegram|both) f="$f -f docker-compose.telegram.yml";; esac
  # review F22: the image records the commit it was built from
  # shellcheck disable=SC2086
  (cd $DEPLOY && BUILD_SHA=$(git -C $REPO rev-parse HEAD 2>/dev/null) docker compose $f "$@")
}

market_open() {  # Mon-Fri 10:00-16:15 Sydney (the server clock is Sydney time)
  local d t; d=$(date +%u); t=$(date +%H%M)
  [ "$d" -le 5 ] && [ "$t" -ge 1000 ] && [ "$t" -le 1615 ]
}

confirm() { read -rp "$1 (y/n) " a; [ "$a" = y ] || [ "$a" = Y ]; }

guard_market() {
  if market_open; then
    y "The ASX is open now (10:00-16:15 Sydney). Changing the trader now could interrupt orders."
    confirm "Do it anyway?" || { echo "Cancelled."; return 1; }
  fi
}

actions_login() {  # the allowed log-in(s) in the local file, if any
  grep -A6 '^app:' "$LOCAL" 2>/dev/null | sed -n 's/^  allowed_logins: *\[\(.*\)\].*/\1/p' | head -1
}

cmd_status() {
  echo "== Big Wins server  $(date '+%a %d %b %Y %H:%M %Z')"
  if market_open; then echo "ASX: open"; else echo "ASX: closed"; fi
  echo "Code version: $(git -C $REPO log --oneline -1 2>/dev/null)"
  echo "Disk used: $(df -h / | awk 'NR==2{print $5" of "$2}')   Memory used: $(free -m | awk '/Mem/{printf "%d%%", $3*100/$2}')"
  echo "Tailscale: $(tailscale status >/dev/null 2>&1 && echo connected || echo NOT connected)"
  echo
  echo "== Secrets (names only, contents never shown)"
  local n=0 t=0 name
  for name in $ALL_SECRETS; do
    t=$((t+1))
    if [ -s "$SECRETS/$name" ]; then g "  ok       $name"; n=$((n+1)); else y "  missing  $name"; fi
  done
  echo "  $n of $t in place (messages go to: $(channel))"
  echo
  echo "== Trader"
  if [ -f "$DEPLOY/.env" ] && dc ps --format '{{.Service}}' 2>/dev/null | grep -q .; then
    dc ps --format '  {{.Service}}: {{.Status}}'
    grep -q '^TRADER_CMD=trader-bf run' "$DEPLOY/.env" 2>/dev/null \
      || y "  trader: idle (sleep) until: bigwins start-trader <date>"
  else
    y "  Not started yet (it starts after the IBKR details are in: GO_LIVE_GUIDE B8)."
  fi
  docker ps --format '{{.Names}}' 2>/dev/null | grep -qx bigwins-demo \
    && y "  DEMO app container running (made-up data): it stops when the real app starts"
  echo
  echo "== Phone app"
  if curl -fsS -m 3 http://127.0.0.1:8080/healthz >/dev/null 2>&1; then
    g "  app: running on 127.0.0.1:8080"
  else
    y "  app: not running"
  fi
  if tailscale serve status 2>/dev/null | grep -q 8080; then
    g "  on your phone: $(app_url)"
  else
    y "  not shared on Tailscale yet (menu option 9)"
  fi
  local who; who=$(actions_login)
  if [ -n "$who" ]; then g "  actions allowed for: $who"; else y "  actions: off - no log-in allowed yet (menu option 11)"; fi
  if systemctl is-active --quiet bigwins-worker.timer 2>/dev/null; then
    g "  server worker: running (app Server tab)"
  else
    y "  server worker: not installed (menu option 13)"
  fi
}

app_url() {  # the server's Tailscale name, e.g. https://bigwins.tailnet-name.ts.net
  local dns
  dns=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)
  [ -n "$dns" ] && echo "https://$dns"
}

cmd_app() {  # BF-D37: the phone app, on your tailnet only (HTTPS, 127.0.0.1:8080 behind it)
  if ! tailscale status >/dev/null 2>&1; then r "Tailscale is not connected on the server."; return 1; fi
  tailscale serve --bg 8080 || { r "tailscale serve failed (is HTTPS on in the Tailscale admin page?)."; return 1; }
  local url; url=$(app_url)
  g "The Big Wins app is on: ${url:-https://<server>.<tailnet>.ts.net}"
  echo "Open it on your phone (Tailscale app on, same account), then Add to Home screen."
  echo "Only devices on your tailnet can open it. Turn it off with: tailscale serve reset"
}

cmd_demo() {  # the phone app with DEMO data, before the trader has started (no secrets, no database)
  cd $REPO || return 1
  git pull --ff-only -q || y "Could not update the code; using the version already here."
  echo "Building the app (a few minutes the first time)..."
  docker build -q -t asx-trader-bfast-trader:local -f deploy/Dockerfile . >/dev/null || { r "Build failed."; return 1; }
  docker rm -f bigwins-demo >/dev/null 2>&1
  docker run -d --name bigwins-demo --restart unless-stopped -p 127.0.0.1:8080:8080 \
    -v $REPO/config:/app/config:ro --read-only --tmpfs /tmp --cap-drop ALL \
    --security-opt no-new-privileges:true -e TZ=Australia/Sydney \
    asx-trader-bfast-trader:local trader-bf dashboard --demo --host 0.0.0.0 --port 8080 >/dev/null \
    || { r "Could not start the demo app."; return 1; }
  g "Demo app running (made-up numbers, marked DEMO; its buttons are simulated)."
  cmd_app
}

cmd_logs() {
  dc logs --tail 40 trader 2>/dev/null || y "Trader not started yet."
}

secrets_ready() {
  local name
  for name in $ALL_SECRETS; do [ -s "$SECRETS/$name" ] || return 1; done
}

do_update() {  # no questions asked (the app's server worker uses it too)
  if ! git -C $REPO diff --quiet -- config/bfast.yaml 2>/dev/null; then
    r "config/bfast.yaml was edited on this server. Move those settings to config/bfast.local.yaml"
    r "(git -C $REPO diff config/bfast.yaml shows them), then: git -C $REPO checkout config/bfast.yaml"
    return 1
  fi
  local before; before=$(git -C $REPO rev-parse HEAD 2>/dev/null)
  git -C $REPO pull --ff-only || { r "Update failed (no changes made)."; return 1; }
  if [ "$(git -C $REPO rev-parse HEAD)" != "$before" ]; then
    python3 "$DEPLOY/gitops.py" record "$STATE" "$before"  # BF-D45: the rollback target
  fi
}

after_update() {  # secrets the new code needs, then rebuild and restart
  ALL_SECRETS=$(all_secrets)
  make_keys || { r "Update stopped before the restart: fix the message above, then: bigwins update"; return 1; }
  if [ -f "$DEPLOY/.env" ] && secrets_ready; then
    docker rm -f bigwins-demo >/dev/null 2>&1  # F4: the demo never runs beside the real app
    dc build || { r "Build failed: nothing restarted."; return 1; }
    if ! golden_checks; then  # batch 3 M2: refuse to restart the trader on a failed check
      r "The record-data checks failed: the trader was NOT restarted (it runs the old code)."
      printf '%s' '{"ok":false,"kind":"golden","error":"record-data checks failed after the update; trader not restarted"}' \
        | dc exec -T trader trader-bf server-jobs backup >/dev/null 2>&1
      return 1
    fi
    dc up -d && g "Updated and restarted."
    # F3: the output volume belongs to the trader's user (once; a no-op afterwards)
    dc exec -T -u 0 trader chown -R 10001:10001 /app/out >/dev/null 2>&1
    docker image prune -f >/dev/null 2>&1  # F11
  else
    g "Code updated. (The trader is not started yet, so nothing to restart.)"
  fi
}

make_keys() {  # BF-D40/D46/D48/D52: generated secrets, made here once, never shown
  command -v openssl >/dev/null || { r "openssl is missing (apt install openssl): no keys made."; return 1; }
  [ -s "$SECRETS/vapid_private_key" ] || make_vapid || return 1
  if command -v age-keygen >/dev/null && [ ! -s "$BKEY" ]; then  # BF-D64: the backup key
    if ls "$BACKUP_DIR"/bigwins-*.tar.age >/dev/null 2>&1; then  # security review M3
      r "Backups exist but the recovery key file is missing: NO new key made (the old backups"
      r "need the old key). Restore it with: bigwins restore (paste the key), or rotate"
      r "deliberately: bigwins new-backup-key."
    else
      python3 "$DEPLOY/backup.py" keygen "$BKEY" >/dev/null && g "Made the backup recovery key (root only)."
    fi
  fi
  local n tmp
  for n in app_proxy_key worker_job_key db_dashboard_password; do
    [ -s "$SECRETS/$n" ] && continue
    mkdir -p "$SECRETS" && chmod 700 "$SECRETS"
    tmp="$SECRETS/.$n.new"
    if openssl rand -hex 32 > "$tmp" && [ "$(wc -c < "$tmp")" -ge 64 ]; then
      chmod 444 "$tmp" && mv -f "$tmp" "$SECRETS/$n" && g "Made $n."
    else
      rm -f "$tmp"; r "Could not make $n: nothing changed."; return 1  # never a zero-byte key
    fi
  done
}

update_to() {  # BF-D48: fast-forward to exactly the approved commit, nothing else
  local commit=$1 flags=$2 before kind
  [[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "refused: no exact commit in the job"; return 1; }
  if ! git -C $REPO diff --quiet -- config/bfast.yaml 2>/dev/null; then
    echo "refused: config/bfast.yaml was edited on this server (move those settings to config/bfast.local.yaml)"; return 1
  fi
  git -C $REPO fetch -q origin "$BRANCH" || { echo "refused: git fetch failed"; return 1; }
  before=$(git -C $REPO rev-parse HEAD)
  git -C $REPO merge-base --is-ancestor "$before" "$commit" || { echo "refused: the approved commit does not follow the running one"; return 1; }
  git -C $REPO merge-base --is-ancestor "$commit" "origin/$BRANCH" || { echo "refused: the approved commit is not on origin/$BRANCH"; return 1; }
  kind=$(git -C $REPO diff --name-only "$before" "$commit" | python3 "$DEPLOY/classify.py")
  if [ "$kind" = strategy ] && [ $((flags & 4)) = 0 ]; then
    echo "refused: this commit changes trading code but was approved as app-only; approve it again"; return 1
  fi
  if [ "$kind" = strategy ] && market_open; then
    echo "refused: a trading update is applied outside ASX hours"; return 1
  fi
  git -C $REPO merge --ff-only -q "$commit" || { echo "refused: fast-forward failed (no changes made)"; return 1; }
  python3 "$DEPLOY/gitops.py" record "$STATE" "$before"
  echo "now at $(git -C $REPO log --oneline -1)"
  bash "$DEPLOY/bigwins.sh" after-pull  # BF-D61: the new script's steps, not this shell's
}

cmd_update() {
  guard_market || return 1
  do_update || return 1
  # BF-D61 (N4): the steps after the pull come from the NEW script (this shell still holds
  # the old functions in memory), so new secrets and service changes apply at once
  exec bash "$DEPLOY/bigwins.sh" after-pull
}

cmd_restart() {
  guard_market || return 1
  docker rm -f bigwins-demo >/dev/null 2>&1  # F4: the demo frees 127.0.0.1:8080
  dc up -d && dc restart trader dashboard && g "Trader and app restarted."
}

cmd_new_backup_key() {  # security review M3: a key rotation is an explicit action
  y "A new recovery key: backups made from now on need the NEW key; old backups still need"
  y "the OLD one (keep both). The app shows the new key's fingerprint until you have saved it."
  confirm "Make a new backup recovery key?" || return 0
  [ -s "$BKEY" ] && mv "$BKEY" "$BKEY.$(date +%Y%m%d%H%M%S).old"
  python3 "$DEPLOY/backup.py" keygen "$BKEY" >/dev/null && g "New key made (fingerprint $(key_fp)). Show it once in the app and save it."
}

cmd_secret() {
  local name=${1:-}
  if [ -z "$name" ]; then
    echo "Which secret?"; select name in $TYPED_SECRETS; do [ -n "$name" ] && break; done
  fi
  if [ "$name" = vapid_private_key ]; then cmd_vapid; return; fi
  case " $TYPED_SECRETS " in *" $name "*) ;; *) r "Unknown secret: $name"; return 1;; esac
  if [ "$name" = db_password ] && [ -s "$SECRETS/db_password" ] && docker volume ls -q 2>/dev/null | grep -q pgdata; then
    r "db_password is already set and the database exists: Postgres keeps the original"
    r "password, so a new one would lock the trader out. Not changed (review F17)."
    return 1
  fi
  mkdir -p "$SECRETS" && chmod 700 "$SECRETS"
  echo "Paste the value for $name and press Enter (nothing will show on screen):"
  local v; read -rs v; echo
  [ -n "$v" ] || { r "Nothing entered; $name not changed."; return 1; }
  [ -f "$SECRETS/$name" ] && chmod 600 "$SECRETS/$name"
  printf '%s' "$v" > "$SECRETS/$name"; unset v
  chmod 444 "$SECRETS/$name"
  g "Saved $name ($(wc -c < "$SECRETS/$name") characters)."
}

make_vapid() {  # BF-D40: the phone app's Web Push key, made here, never typed or shown
  command -v openssl >/dev/null || { r "openssl is missing (apt install openssl)."; return 1; }
  mkdir -p "$SECRETS" && chmod 700 "$SECRETS"
  [ -f "$SECRETS/vapid_private_key" ] && chmod 600 "$SECRETS/vapid_private_key"
  openssl ecparam -name prime256v1 -genkey -noout 2>/dev/null \
    | openssl pkcs8 -topk8 -nocrypt -out "$SECRETS/vapid_private_key" || { r "Key not made."; return 1; }
  chmod 444 "$SECRETS/vapid_private_key"
  g "Made the phone-alert key (vapid_private_key)."
}

cmd_vapid() {
  if [ -s "$SECRETS/vapid_private_key" ]; then
    y "The phone-alert key exists. A new key means every phone must tap 'Turn on alerts' again."
    confirm "Make a new key?" || { echo "Kept the old key."; return 0; }
  fi
  make_vapid && y "Restart the trader to use it (menu option 4)."
}

cmd_login() {  # BF-D39: allow your own Tailscale log-in to act from the phone app
  local who
  who=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(d["User"][str(d["Self"]["UserID"])]["LoginName"])' 2>/dev/null)
  if [ -z "$who" ]; then
    read -rp "Could not read your Tailscale log-in. Type it (as the Tailscale app shows it): " who
  fi
  [ -n "$who" ] || { r "No log-in given; nothing changed."; return 1; }
  echo "The phone app will let this Tailscale log-in approve, refuse, pause, kill and resume:"
  echo "    $who"
  confirm "Allow it?" || { echo "Nothing changed."; return 0; }
  local host; host=$(app_url | sed 's#^https://##')
  python3 "$DEPLOY/set_login.py" "$LOCAL" "$who" "$host" || { r "Could not write $LOCAL."; return 1; }
  g "Saved in config/bfast.local.yaml (this server only, not in git)."
  y "Restart the trader and the app to use it (menu option 4)."
}

do_rollback() {  # BF-D45/D49: back to the commit recorded before the last update, then restart
  local want=${1:-} flags=${2:-0} head prev
  head=$(git -C $REPO rev-parse HEAD)
  prev=$(python3 "$DEPLOY/gitops.py" target "$STATE" "$head") || { r "No previous version recorded."; return 1; }
  [ -z "$want" ] || [ "$want" = "$prev" ] || { r "refused: the job's commit is not the recorded previous one"; return 1; }
  git -C $REPO merge-base --is-ancestor "$prev" "$head" || { r "The recorded commit is not an earlier version."; return 1; }
  # a rollback does not undo database migrations: across one only when the owner ticked it
  if [ -n "$(git -C $REPO diff --name-only "$prev" "$head" -- migrations/)" ] && [ $((flags & 16)) = 0 ]; then
    r "refused: the rollback crosses a database migration (tick the box in the app to do it anyway)"; return 1
  fi
  git -C $REPO reset --keep "$prev" || { r "Rollback failed (no changes made)."; return 1; }
  python3 "$DEPLOY/gitops.py" done "$STATE"
  dc build && dc up -d && g "Back on $(git -C $REPO log --oneline -1)."
}

update_check() {  # BF-D45: every 10 minutes, is the branch ahead, and what would change
  local stamp="$STATE/last_fetch" now; now=$(date +%s)
  mkdir -p "$STATE"
  if [ ! -f "$stamp" ] || [ $((now - $(cat "$stamp"))) -ge 600 ]; then
    git -C $REPO fetch -q origin "$BRANCH" 2>/dev/null && echo "$now" > "$stamp"
  fi
  UPD_HEAD=$(git -C $REPO rev-parse HEAD 2>/dev/null)
  UPD_REMOTE=$(git -C $REPO rev-parse "origin/$BRANCH" 2>/dev/null)
  UPD_AHEAD=$(git -C $REPO rev-list --count "HEAD..origin/$BRANCH" 2>/dev/null || echo 0)
  UPD_FILES=$(git -C $REPO diff --name-only HEAD "origin/$BRANCH" 2>/dev/null | head -300)
  UPD_CFG=$(git -C $REPO show "origin/$BRANCH:config/bfast.yaml" 2>/dev/null)
  UPD_LOG=$(git -C $REPO show "origin/$BRANCH:config/strategy_changelog.yaml" 2>/dev/null)
  UPD_SUBJECT=$(git -C $REPO log -1 --format=%s "origin/$BRANCH" 2>/dev/null)
  UPD_PREV=$(python3 "$DEPLOY/gitops.py" target "$STATE" "$UPD_HEAD" 2>/dev/null)
  UPD_CI=unknown  # review F13: the CI result of the target commit (tags CI pushes; read-only key)
  if [ -n "$UPD_REMOTE" ] && [ "$UPD_REMOTE" != "$UPD_HEAD" ]; then
    if git -C $REPO ls-remote -q origin "refs/tags/ci-ok/$UPD_REMOTE" 2>/dev/null | grep -q .; then UPD_CI=green
    elif git -C $REPO ls-remote -q origin "refs/tags/ci-fail/$UPD_REMOTE" 2>/dev/null | grep -q .; then UPD_CI=red; fi
  fi
  UPD_PREV_MIG=""
  [ -n "$UPD_PREV" ] && UPD_PREV_MIG=$(git -C $REPO diff --name-only "$UPD_PREV" "$UPD_HEAD" -- migrations/ 2>/dev/null)
  export UPD_HEAD UPD_REMOTE UPD_AHEAD UPD_FILES UPD_CFG UPD_LOG UPD_SUBJECT UPD_PREV UPD_PREV_MIG UPD_CI
}

host_status() {  # BF-D42: a small JSON snapshot for the app's Server tab (no secrets)
  local ts cv asx ps logs
  update_check
  ts=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("BackendState","?"))' 2>/dev/null)
  cv=$(git -C $REPO log --oneline -1 2>/dev/null | cut -c1-60)
  if market_open; then asx=open; else asx=closed; fi
  ps=$(dc ps --format '{{.Service}}|{{.Status}}' 2>/dev/null)
  logs=$(dc logs --tail 30 --no-color trader 2>/dev/null | tail -30)
  local n present="" missing=""  # BF-D63: secret names only (the files are never read)
  for n in $TYPED_SECRETS $APP_SECRETS db_dashboard_password healthchecks_backup_url; do
    if [ -s "$SECRETS/$n" ]; then present="$present $n"; else missing="$missing $n"; fi
  done
  TS="$ts" CV="$cv" ASX="$asx" PS="$ps" LOGS="$logs" SECRETS_PRESENT="$present" \
    SECRETS_MISSING="$missing" ONEDRIVE="$(onedrive_ok && echo 1 || echo 0)" \
    BACKUP_AGE_H="$(backup_age_h)" KEY_FP="$(key_fp)" \
    python3 "$DEPLOY/host_status.py"
}

envval() { sed -n "s/^$1=//p" "$DEPLOY/.env" 2>/dev/null | head -1; }

onedrive_ok() { command -v rclone >/dev/null && rclone listremotes 2>/dev/null | grep -qx "$OD_REMOTE:"; }

compose_json() {  # the docker compose command as JSON (for backup.py's pg_dump)
  local f="docker-compose.yml"
  case "$(channel)" in telegram|both) f="$f docker-compose.telegram.yml";; esac
  python3 -c 'import json,sys; d=sys.argv[1]; fs=sys.argv[2].split()
c=["docker","compose","--project-directory",d]
for f in fs: c+=["-f",d+"/"+f]
print(json.dumps(c))' "$DEPLOY" "$f"
}

do_backup() {  # BF-D64: one encrypted backup, local + OneDrive, and the readable report
  local e
  if ! command -v age >/dev/null; then
    e='{"ok":false,"kind":"backup","error":"age is not installed (apt install age)"}'; record_backup "$e"; echo "$e"; return 1
  fi
  make_keys >/dev/null || true
  if [ ! -s "$BKEY" ]; then
    e='{"ok":false,"kind":"backup","error":"no backup key"}'; record_backup "$e"; echo "$e"; return 1
  fi
  local jdb stage res rc day remote=""
  jdb=$(envval JOURNAL_DB); jdb=${jdb:-ledger_bf_paper}
  mkdir -p "$BACKUP_DIR" && chmod 700 "$BACKUP_DIR"
  stage=$(mktemp -d /var/tmp/bigwins-stage.XXXXXX) || return 1
  chmod 700 "$stage"
  mkdir -p "$stage/worker_state" && cp -a "$STATE/." "$stage/worker_state/" 2>/dev/null  # F20: first
  dc exec -T trader sh -c 'tar -C /app/out -cf - .' > "$stage/trader_out.tar" 2>/dev/null
  dc exec -T db psql -U trader -d "$jdb" -At -F '|' -c "select 'bf_events',count(*) from bf_events union all select 'bf_fills',count(*) from bf_fills union all select 'bf_intents',count(*) from bf_intents union all select 'bf_approvals',count(*) from bf_approvals" > "$stage/counts.txt" 2>/dev/null
  onedrive_ok && remote="$OD_PATH/archives"
  COMPOSE="$(compose_json)" JDB="$jdb" STAGE="$stage" OUT="$BACKUP_DIR" KEY="$BKEY" REMOTE="$remote" \
  REPO="$REPO" DEPLOY="$DEPLOY" SECRETS="$SECRETS" STATE="$stage/worker_state" RECORD="$(envval RECORD_DIR)" \
  FSTORE="$(envval FORWARD_STORE)" REFDIR="$(envval REF_DIR)" FLEX="$(envval FLEX_INBOX)" \
  COMMIT="$(git -C $REPO rev-parse HEAD 2>/dev/null)" python3 - <<'PY'
import json, os
e = os.environ
counts = {}
try:
    for line in open(e["STAGE"] + "/counts.txt"):
        t, _, n = line.strip().partition("|")
        if t and n.isdigit():
            counts[t] = int(n)
except OSError:
    pass
src = [["config", e["REPO"] + "/config"], ["trader_out.tar", e["STAGE"] + "/trader_out.tar"],
       ["deploy_env", e["DEPLOY"] + "/.env"], ["secrets", e["SECRETS"]], ["worker_state", e["STATE"]]]
if e.get("RECORD"):
    src.append(["record", e["RECORD"]])
if e.get("FSTORE"):
    src.append(["forward_store", e["FSTORE"]])
if e.get("REFDIR"):  # security review M2
    src.append(["ref", e["REFDIR"]])
if e.get("FLEX"):
    src.append(["flex_inbox", e["FLEX"]])
plan = {"out_dir": e["OUT"], "key_file": e["KEY"], "remote": e.get("REMOTE") or None,
        "commit": e.get("COMMIT", ""), "local_keep": [7, 0],
        "pg_dump": json.loads(e["COMPOSE"]) + ["exec", "-T", "db", "pg_dump", "-U", "trader", "-d", e["JDB"]],
        "row_counts": counts, "sources": src, "work_dir": "/var/tmp"}
open(e["STAGE"] + "/plan.json", "w").write(json.dumps(plan))
PY
  res=$(python3 "$DEPLOY/backup.py" run "$stage/plan.json"); rc=$?
  day=$(date +%F)
  if dc exec -T dashboard trader-bf daily-summary --out - > "$stage/report.html" 2>/dev/null && [ -s "$stage/report.html" ]; then
    mkdir -p "$BACKUP_DIR/reports/${day:0:4}" && cp "$stage/report.html" "$BACKUP_DIR/reports/${day:0:4}/$day.html"
    onedrive_ok && rclone copyto "$stage/report.html" "$OD_PATH/reports/${day:0:4}/$day.html" >/dev/null 2>&1
  fi
  res=$(printf '%s' "$res" | python3 -c 'import json,sys
r=json.loads(sys.stdin.read() or "{}"); r["kind"]="backup"; r["onedrive"]=sys.argv[1]=="1"; print(json.dumps(r))' "$(onedrive_ok && echo 1 || echo 0)")
  record_backup "$res"
  [ "$rc" = 0 ] && hc_backup_ping
  rm -rf "$stage"
  echo "$res"
  return $rc
}

do_restore_test() {  # BF-D64 / review L3: unpack the latest backup once, check it, delete it
  local arch res cid="" tmp="" counts="" pw
  arch=$(python3 "$DEPLOY/backup.py" latest "$BACKUP_DIR") || {
    res='{"ok":false,"kind":"restore_test","error":"no backup yet"}'; record_backup "$res"; echo "$res"; return 1; }
  trap '[ -n "$cid" ] && docker rm -f "$cid" >/dev/null 2>&1; [ -n "$tmp" ] && rm -rf "$tmp"' RETURN
  res=$(python3 "$DEPLOY/backup.py" verify "$arch" "$BKEY" /var/tmp --keep)
  tmp=$(printf '%s' "$res" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read() or "{}").get("restore_dir",""))')
  pw=$(openssl rand -hex 16)
  if [ -n "$tmp" ] && [ -s "$tmp/journal/journal.sql" ] && \
     cid=$(docker run -d --network none -e POSTGRES_PASSWORD="$pw" -e POSTGRES_USER=trader -e POSTGRES_DB=rt postgres:16.10-bookworm@sha256:38471f330eb885e04de130b768d6db4e10469e2311879c7e5c699f6d2d8a1c74); then
    for i in $(seq 1 30); do docker exec "$cid" pg_isready -h 127.0.0.1 -U trader -d rt >/dev/null 2>&1 && break; sleep 2; done
    docker exec -i "$cid" psql -q -h 127.0.0.1 -U trader -d rt -v ON_ERROR_STOP=1 --single-transaction < "$tmp/journal/journal.sql" >/dev/null 2>&1
    counts=$(docker exec "$cid" psql -h 127.0.0.1 -U trader -d rt -At -F '|' -c "select 'bf_events',count(*) from bf_events union all select 'bf_fills',count(*) from bf_fills union all select 'bf_intents',count(*) from bf_intents union all select 'bf_approvals',count(*) from bf_approvals" 2>/dev/null)
  fi
  res=$(printf '%s' "$res" | COUNTS="$counts" python3 -c 'import json,os,sys
r=json.loads(sys.stdin.read() or "{}"); r.pop("restore_dir", None); got={}
for l in os.environ.get("COUNTS","").splitlines():
    t,_,n=l.partition("|")
    if n.strip().isdigit(): got[t]=int(n)
want=r.get("row_counts") or {}
r["kind"]="restore_test"
r["db_rows_match"]=bool(want) and bool(got) and all(got.get(k)==v for k,v in want.items())
r["ok"]=bool(r.get("ok")) and r["db_rows_match"]
if not r["db_rows_match"]: r["error"]=r.get("error") or "journal rows in the restored database differ from the backup (or none were counted)"
print(json.dumps(r))')
  record_backup "$res"
  echo "$res"
}

cmd_onedrive() {  # BF-D64: connect OneDrive once (the token stays root-only on this server)
  command -v rclone >/dev/null || { r "rclone is missing: apt install rclone"; return 1; }
  echo "Connect OneDrive for the backups (once). You need a computer with a web browser:"
  echo "  1. On that computer install rclone (rclone.org/downloads) and run:  rclone authorize \"onedrive\""
  echo "  2. Sign in to Microsoft in the browser that opens and allow access."
  echo "  3. rclone prints a token line starting with {\"access_token\": ... Copy all of it."
  echo "Now rclone asks its questions here. Answer:  n (new remote) > name: $OD_REMOTE >"
  echo "  storage: onedrive > client_id / secret: Enter > region: global > advanced: n >"
  echo "  auto config: n > paste the token > type: onedrive (personal) > drive: the first > y > q"
  confirm "Start?" || return 0
  rclone config
  chmod 600 /root/.config/rclone/rclone.conf 2>/dev/null
  if rclone mkdir "$OD_PATH" >/dev/null 2>&1; then g "OneDrive connected: backups go to 'Big Wins server backups'."; else r "OneDrive is not working yet: run bigwins onedrive again."; fi
}

cmd_restore() {  # BF-D64 / review F6 + security M1: disaster recovery that fails closed
  y "This restores the Big Wins server from a backup: journal, local config, record, price"
  y "store, ref, Flex inbox, the .env file and the secret files. It replaces what is here."
  confirm "Continue?" || return 0
  command -v age >/dev/null || { r "Install age first: apt install age"; return 1; }
  mkdir -p "$(dirname "$BKEY")" && chmod 700 "$(dirname "$BKEY")"
  if [ ! -s "$BKEY" ] || confirm "Paste a recovery key now (instead of the one on this server)?"; then
    echo "Paste the recovery key (AGE-SECRET-KEY-...) and press Enter:"
    local k; read -rs k; echo
    printf '%s\n' "$k" > "$BKEY.new"; unset k; chmod 600 "$BKEY.new"
    if ! age-keygen -y "$BKEY.new" >/dev/null 2>&1; then  # F6: a real age key, else nothing kept
      rm -f "$BKEY.new"; r "That is not a valid recovery key; nothing changed."; return 1
    fi
    mv -f "$BKEY.new" "$BKEY"
  fi
  mkdir -p "$BACKUP_DIR" && chmod 700 "$BACKUP_DIR"
  if onedrive_ok; then rclone copy "$OD_PATH/archives" "$BACKUP_DIR" --include 'bigwins-*' >/dev/null 2>&1; fi
  local arch tmp jdb man commit
  arch=$(python3 "$DEPLOY/backup.py" latest "$BACKUP_DIR") || { r "No backup found (connect OneDrive with: bigwins onedrive)."; return 1; }
  echo "Newest backup: $(basename "$arch") (made $(date -r "$arch" '+%a %d %b %Y %H:%M'))"
  confirm "Restore this one?" || return 0
  tmp=$(mktemp -d /var/tmp/bigwins-restore.XXXXXX); chmod 700 "$tmp"
  trap 'rm -rf "$tmp"' RETURN
  python3 "$DEPLOY/backup.py" restore "$arch" "$tmp" "$BKEY" || { r "Restore refused (see the message above); nothing changed."; return 1; }
  man=$(python3 "$DEPLOY/backup.py" check-manifest "$tmp" "$BKEY") || { r "The archive's signed manifest does not match: refused."; return 1; }
  jdb=$( (sed -n 's/^JOURNAL_DB=//p' "$tmp/deploy_env" 2>/dev/null | head -1) ); jdb=${jdb:-ledger_bf_paper}
  # the database first: fail closed before anything else is replaced
  cp "$tmp/deploy_env" "$DEPLOY/.env" && chmod 600 "$DEPLOY/.env"
  mkdir -p "$SECRETS" && cp -a "$tmp/secrets/." "$SECRETS/" && chmod 700 "$SECRETS" && chmod 444 "$SECRETS"/*
  dc up -d --wait db || { r "The database did not start: stopped before loading anything."; return 1; }
  dc exec -T db sh -c "pg_isready -h 127.0.0.1 -U trader" >/dev/null || { r "Database not ready: stopped."; return 1; }
  dc exec -T db psql -U trader -d postgres -Atc "select 1 from pg_database where datname='$jdb'" | grep -q 1 \
    || dc exec -T db createdb -U trader "$jdb" || { r "Could not create $jdb: stopped."; return 1; }
  if [ -n "$(dc exec -T db psql -U trader -d "$jdb" -Atc "select 1 from information_schema.tables where table_name like 'bf\_%' limit 1")" ]; then
    r "The database $jdb already has journal tables: refused (restore only into an empty server)."; return 1
  fi
  dc exec -T db psql -U trader -d "$jdb" -v ON_ERROR_STOP=1 --single-transaction -q < "$tmp/journal/journal.sql" \
    || { r "Loading the journal failed (errors above): nothing else was changed after the database."; return 1; }
  if ! printf '%s' "$man" | JDB="$jdb" python3 -c 'import json,os,subprocess,sys
m=json.loads(sys.stdin.read()); want=m.get("row_counts") or {}
bad=[]
for t,n in want.items():
    got=subprocess.run(sys.argv[1:]+["psql","-U","trader","-d",os.environ["JDB"],"-Atc",f"select count(*) from {t}"],capture_output=True,text=True).stdout.strip()
    if got!=str(n): bad.append(f"{t}: {got} vs {n}")
print("; ".join(bad)); sys.exit(1 if bad or not want else 0)' $(compose_json | python3 -c 'import json,sys; print(" ".join(json.load(sys.stdin)))') exec -T db; then
    r "Row counts differ from the backup's manifest: stopped before starting the stack."; return 1
  fi
  g "Journal restored and checked."
  commit=$(printf '%s' "$man" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit",""))')
  if [[ "$commit" =~ ^[0-9a-f]{40}$ ]]; then git -C $REPO fetch -q origin "$BRANCH" 2>/dev/null; git -C $REPO checkout -q "$commit" && g "Code at the backup's commit ${commit:0:12}."; fi
  # config: only the server's own files (never the tracked bfast.yaml)
  local f
  for f in "$tmp"/config/*; do
    [ -e "$f" ] || continue
    if git -C $REPO ls-files --error-unmatch "config/$(basename "$f")" >/dev/null 2>&1; then continue; fi
    cp -a "$f" "$REPO/config/"
  done
  [ -d "$tmp/worker_state" ] && mkdir -p "$STATE" && cp -a "$tmp/worker_state/." "$STATE/"
  local rec fs ref fx; rec=$(envval RECORD_DIR); fs=$(envval FORWARD_STORE); ref=$(envval REF_DIR); fx=$(envval FLEX_INBOX)
  [ -n "$rec" ] && [ -d "$tmp/record" ] && mkdir -p "$rec" && cp -a "$tmp/record/." "$rec/"
  [ -n "$fs" ] && [ -d "$tmp/forward_store" ] && mkdir -p "$fs" && cp -a "$tmp/forward_store/." "$fs/"
  [ -n "$ref" ] && [ -d "$tmp/ref" ] && mkdir -p "$ref" && cp -a "$tmp/ref/." "$ref/"
  [ -n "$fx" ] && [ -d "$tmp/flex_inbox" ] && mkdir -p "$fx" && cp -a "$tmp/flex_inbox/." "$fx/"
  [ -n "$fs" ] && chown -R 10001:10001 "$fs"; [ -n "$fx" ] && chown -R 10001:10001 "$fx"  # M2
  dc up -d && dc exec -T trader sh -c 'tar -C /app/out -xf -' < "$tmp/trader_out.tar" 2>/dev/null
  g "Restored. Then: bigwins 9 (phone app on Tailscale; the server's Tailscale name may be new),"
  g "bigwins 11 (allow my phone), sudo bigwins install-worker, and in the app: Turn on alerts again."
}

finish_job() {  # id status text: record a server job's result (retried while the trader restarts)
  local i
  for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
    printf '%s\n' "$3" | dc exec -T trader trader-bf server-jobs finish --id "$1" --status "$2" >/dev/null 2>&1 && return 0
    sleep 10
  done
  return 1
}

cmd_worker() {  # BF-D42: one pass of the host worker (systemd timer, every 30 s, as root)
  mkdir -p "$STATE" && chmod 700 "$STATE"  # the worker's own notes: root only
  host_status 2>/dev/null | dc exec -T trader trader-bf server-jobs status >/dev/null 2>&1
  if [ -s "$STATE/last_backup.json" ]; then  # a result recorded while the trader was down
    dc exec -T trader trader-bf server-jobs backup < "$STATE/last_backup.json" >/dev/null 2>&1 && rm -f "$STATE/last_backup.json"
  fi
  local job id action force out rc commit flags created sig
  job=$(dc exec -T trader trader-bf server-jobs claim 2>/dev/null) || return 0
  id=$(printf '%s' "$job" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
  [ -n "$id" ] || return 0
  jf() { printf '%s' "$job" | python3 -c "import json,sys; print(json.load(sys.stdin).get('$1', ''))"; }
  action=$(jf action); force=$(jf force); commit=$(jf commit); flags=$(jf flags)
  created=$(jf created); sig=$(jf sig)
  # BF-D48: only jobs the trader signed (key held by the trader and this root worker only)
  if ! python3 "$DEPLOY/gitops.py" verify "$SECRETS/worker_job_key" "$id" "$action" "$commit" "$flags" "$created" "$sig"; then
    finish_job "$id" REFUSED "refused: the job is not signed by the trader"
    return 0
  fi
  # BF-D59 (N8): each signed job id runs once only (this worker's own record, root only)
  if ! python3 "$DEPLOY/gitops.py" claim-id "$STATE" "$id"; then
    finish_job "$id" REFUSED "refused: this job id was already run"
    return 0
  fi
  case "$action" in
    restart|update)
      if market_open && [ "$force" != True ]; then
        finish_job "$id" REFUSED "refused: the ASX is open (10:00-16:15 Sydney) and 'do it anyway' was not ticked"
        return 0
      fi;;
    rollback)
      if market_open; then  # the trader already waits for the close; belt and braces
        finish_job "$id" REFUSED "refused: a rollback is applied outside ASX hours; ask again after 16:15"
        return 0
      fi;;
    check|claude_remote|claude_stop|backup_now|restore_test|backup_key|fetch|hc_ping) ;;
    *) finish_job "$id" REFUSED "refused: not an allowed server action"; return 0;;
  esac
  case "$action" in  # the fixed list only; nothing from the app is ever run as a command
    restart) out=$(dc up -d 2>&1 && dc restart trader 2>&1); rc=$?;;
    update) out=$(update_to "$commit" "$flags" 2>&1); rc=$?;;
    rollback) out=$(do_rollback "$commit" "$flags" 2>&1); rc=$?;;
    claude_remote) out=$(claude_remote_status start 2>&1); rc=$?;;
    claude_stop) out=$(tmux kill-session -t remote 2>&1 && echo "Claude remote control stopped."); rc=$?;;
    backup_now) out=$(do_backup 2>&1); rc=$?;;
    restore_test) out=$(do_restore_test 2>&1); rc=$?;;
    backup_key) out=$(python3 "$DEPLOY/gitops.py" seal "$SECRETS/worker_job_key" "$BKEY" | dc exec -T trader trader-bf server-jobs reveal --fp "$(key_fp)" 2>&1); rc=$?;;
    fetch) rm -f "$STATE/last_fetch"; out=$(host_status 2>/dev/null | dc exec -T trader trader-bf server-jobs status 2>&1); rc=$?;;
    hc_ping) out=$(u=$(cat "$SECRETS/healthchecks_url" 2>/dev/null); case "$u" in https://*) curl -fsS -m 10 -o /dev/null "$u" && echo "ping ok";; *) echo "heartbeat is off (healthchecks_url is none)";; esac 2>&1); rc=$?;;
    check) out=$({ cd $DEPLOY && ./check_secrets.sh; dc ps --format '{{.Service}}: {{.Status}}'; } 2>&1); rc=$?;;
  esac
  if [ "$rc" = 0 ]; then finish_job "$id" DONE "$out"; else finish_job "$id" FAILED "$out"; fi
}

cmd_install_worker() {  # BF-D42: the systemd timer that runs `bigwins worker` every 30 s
  [ "$(id -u)" = 0 ] || { r "Run as root (sudo bigwins install-worker)."; return 1; }
  echo "This installs a small service on this server (as root) that, every 30 seconds,"
  echo "sends the server's status to the app and runs the server jobs you ask for in the"
  echo "app (restart, update and checks only; each needs your 6-digit code in the app)."
  confirm "Install it?" || { echo "Nothing installed."; return 0; }
  cat > /etc/systemd/system/bigwins-worker.service <<EOF
[Unit]
Description=Big Wins server worker (app Server tab, BF-D42)
After=docker.service

[Service]
Type=oneshot
ExecStart=$DEPLOY/bigwins.sh worker
TimeoutStartSec=3600
EOF
  cat > /etc/systemd/system/bigwins-worker.timer <<'EOF'
[Unit]
Description=Run the Big Wins server worker every 30 seconds

[Timer]
OnBootSec=60
OnUnitActiveSec=30
AccuracySec=5

[Install]
WantedBy=timers.target
EOF
  cat > /etc/systemd/system/bigwins-backup.service <<EOF
[Unit]
Description=Big Wins nightly backup (server + OneDrive, BF-D64)
After=docker.service

[Service]
Type=oneshot
ExecStart=$DEPLOY/bigwins.sh backup
TimeoutStartSec=14400
EOF
  cat > /etc/systemd/system/bigwins-backup.timer <<'EOF'
[Unit]
Description=Big Wins nightly backup at 23:30 Sydney

[Timer]
OnCalendar=*-*-* 23:30:00 Australia/Sydney
Persistent=true

[Install]
WantedBy=timers.target
EOF
  cat > /etc/systemd/system/bigwins-weekly.service <<EOF
[Unit]
Description=Big Wins weekly restore test and Docker builder prune (review L4, F11)
After=docker.service

[Service]
Type=oneshot
ExecStart=$DEPLOY/bigwins.sh weekly
TimeoutStartSec=7200
EOF
  cat > /etc/systemd/system/bigwins-weekly.timer <<'EOF'
[Unit]
Description=Big Wins weekly checks (Sunday 03:17 Sydney)

[Timer]
OnCalendar=Sun *-*-* 03:17:00 Australia/Sydney
Persistent=true

[Install]
WantedBy=timers.target
EOF
  systemctl daemon-reload  # review F19: before enabling the new units
  systemctl enable --now bigwins-backup.timer bigwins-weekly.timer >/dev/null 2>&1 || y "Backup timers not started."
  if systemctl enable --now bigwins-worker.timer; then
    g "Server worker installed. The app's Server tab fills in within a minute."
  else
    r "Could not start the worker."
  fi
}

# ---------------------------------------------------------------- full review (BF-D70)
record_backup() {  # json: every backup result reaches the app, even an early failure (F9)
  printf '%s' "$1" | dc exec -T trader trader-bf server-jobs backup >/dev/null 2>&1 \
    || printf '%s\n' "$1" > "$STATE/last_backup.json"  # the trader is down: kept for later
}

hc_backup_ping() {  # F9: an optional second healthchecks check for good backups
  local u; u=$(cat "$SECRETS/healthchecks_backup_url" 2>/dev/null)
  case "$u" in https://*) curl -fsS -m 10 -o /dev/null "$u" || true;; esac
}

backup_age_h() {  # hours since the newest good local backup (for the 26-hour page)
  local a; a=$(python3 "$DEPLOY/backup.py" latest "$BACKUP_DIR" 2>/dev/null) || { echo 9999; return; }
  echo $(( ( $(date +%s) - $(stat -c %Y "$a") ) / 3600 ))
}

key_fp() { [ -s "$BKEY" ] && python3 "$DEPLOY/backup.py" fingerprint "$BKEY" 2>/dev/null; }

cmd_start_trader() {  # F5: set TRADER_CMD (deploy/.env) after a confirmation, then start it
  local d=${1:-}
  [[ "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || { r "Usage: bigwins start-trader YYYY-MM-DD (the L6 start decision date)"; return 1; }
  [ -f "$DEPLOY/.env" ] || { r "deploy/.env is missing (bigwins ibkr first)."; return 1; }
  secrets_ready || { r "Secrets are missing (bigwins status)."; return 1; }
  y "This starts the PAPER trader: scheduler, gateway and app actions; the start decision is $d."
  confirm "Start the paper trader?" || { echo "Nothing changed."; return 0; }
  python3 - "$DEPLOY/.env" "trader-bf run --start $d" <<'PY'
import sys
p, cmd = sys.argv[1], sys.argv[2]
lines = [x for x in open(p).read().splitlines() if not x.startswith("TRADER_CMD=")]
lines.append("TRADER_CMD=" + cmd)
open(p, "w").write("\n".join(lines) + "\n")
PY
  dc up -d trader && g "Paper trader started (start decision $d). Watch: bigwins logs"
}

cmd_ibkr() {  # F24: the paper user name (.env) and the DU account id (local config), safely
  local u du
  read -rp "IBKR PAPER user name (the paper login, not your live one): " u
  [[ "$u" =~ ^[A-Za-z0-9._-]{3,64}$ ]] || { r "That does not look like a user name; nothing changed."; return 1; }
  read -rp "Paper account id (DU followed by digits): " du
  [[ "$du" =~ ^DU[0-9]{5,10}$ ]] || { r "A paper account id starts with DU; nothing changed."; return 1; }
  touch "$DEPLOY/.env" && chmod 600 "$DEPLOY/.env"
  python3 - "$DEPLOY/.env" "$u" <<'PY'
import sys
p, u = sys.argv[1], sys.argv[2]
lines = [x for x in open(p).read().splitlines() if not x.startswith("IBKR_PAPER_USERID=")]
lines.append("IBKR_PAPER_USERID=" + u)
open(p, "w").write("\n".join(lines) + "\n")
PY
  python3 "$DEPLOY/set_login.py" --account "$LOCAL" "$du" || { r "Could not write $LOCAL."; return 1; }
  g "Saved: user name in deploy/.env, account id in config/bfast.local.yaml (this server only)."
  y "Type the paper password with: bigwins secret tws_password"
}

cmd_seed_data() {  # F23: the price store, ref and record from OneDrive (the research copy)
  onedrive_ok || { r "Connect OneDrive first: bigwins onedrive"; return 1; }
  local fs ref rec
  fs=$(envval FORWARD_STORE); ref=$(envval REF_DIR); rec=$(envval RECORD_DIR)
  [ -n "$fs" ] && [ -n "$ref" ] && [ -n "$rec" ] || { r "FORWARD_STORE, REF_DIR and RECORD_DIR must be set in deploy/.env"; return 1; }
  y "Copies from OneDrive 'Big Wins seed data': eodhd/ -> $fs, ref/ -> $ref, record/ -> $rec"
  confirm "Copy now (existing files are kept, newer ones replaced)?" || return 0
  rclone copy "$OD_REMOTE:Big Wins seed data/eodhd" "$fs" --progress || { r "eodhd copy failed"; return 1; }
  rclone copy "$OD_REMOTE:Big Wins seed data/ref" "$ref" --progress || { r "ref copy failed"; return 1; }
  rclone copy "$OD_REMOTE:Big Wins seed data/record" "$rec" --progress || { r "record copy failed"; return 1; }
  chown -R 10001:10001 "$fs" "$(envval FLEX_INBOX)" 2>/dev/null
  g "Seed data in place (owned by the trader's user)."
}

golden_checks() {  # batch 3 M2: the record-data checks must pass before a trader restart
  [ -n "$(envval RECORD_DIR)" ] && [ -d "$(envval RECORD_DIR)" ] || { echo "skipped (no record data)"; return 0; }
  dc run --rm --no-deps trader trader-bf golden-check
}

cmd_weekly() { do_restore_test >/dev/null; docker builder prune -f --filter until=168h >/dev/null 2>&1; }

cmd_check() { cd $DEPLOY && ./check_secrets.sh; }

cmd_claude() {
  tmux has-session -t claude 2>/dev/null || tmux new -d -s claude -c $REPO claude
  tmux attach -t claude
}

claude_remote_status() {  # for the app's server job: start (reuses cmd_remote), then report
  [ "${1:-}" = start ] && cmd_remote >/dev/null 2>&1
  if ! tmux has-session -t remote 2>/dev/null; then echo "Claude remote control is not running."; return 1; fi
  if tmux capture-pane -p -t remote 2>/dev/null | grep -qiE 'log ?in|sign ?in|authenticat|https://claude'; then
    echo "Claude remote control is running but needs a one-time sign-in: on the server (Termius) run: tmux attach -t remote"
  else
    echo "Claude remote control is running. Open the Claude app (claude.ai/code): the server shows as a session."
  fi
}

cmd_remote() {
  if tmux has-session -t remote 2>/dev/null; then
    g "Remote Control is already running. Open the Claude app: the server shows as a session."
  else
    tmux new -d -s remote -c $REPO "claude remote-control"
    g "Remote Control started. If it asks you to sign in, run: tmux attach -t remote"
    echo "Then open the Claude app on your phone or laptop: the server shows as a session."
  fi
}

menu() {
  cmd_status
  echo
  echo "What would you like to do?"
  echo "  1) Refresh status        2) Trader log         3) Update to the latest code"
  echo "  4) Restart the trader    5) Add/replace a secret  6) Check secret files"
  echo "  7) Open Claude here      8) Start Remote Control (use Claude from the app)"
  echo "  9) Turn on the phone app   10) Phone app with DEMO data (before IBKR)"
  echo " 11) Allow my phone to act (approve, pause...)   12) New phone-alert key"
  echo " 13) Install the server worker (app Server tab)   14) Connect OneDrive for backups"
  echo " 15) Back up now   16) Restore from a backup (disaster recovery)"
  echo "  0) Exit"
  read -rp "Choose: " c
  case $c in
    1) cmd_status;; 2) cmd_logs;; 3) cmd_update;; 4) cmd_restart;; 5) cmd_secret;;
    6) cmd_check;; 7) cmd_claude;; 8) cmd_remote;; 9) cmd_app;; 10) cmd_demo;;
    11) cmd_login;; 12) cmd_vapid;; 13) cmd_install_worker;; 14) cmd_onedrive;;
    15) do_backup;; 16) cmd_restore;; *) echo "Bye.";;
  esac
}

case ${1:-} in
  status) cmd_status;; logs) cmd_logs;; update) cmd_update;; restart) cmd_restart;;
  secret) cmd_secret "${2:-}";; check) cmd_check;; claude) cmd_claude;; remote) cmd_remote;;
  app) cmd_app;; demo) cmd_demo;; login) cmd_login;; vapid) cmd_vapid;;
  install-worker) cmd_install_worker;; worker) cmd_worker;;
  after-pull) after_update;;
  backup) do_backup;; restore-test) do_restore_test;; onedrive) cmd_onedrive;; restore) cmd_restore;;  # BF-D61: run by update after the pull (the new script)
  start-trader) cmd_start_trader "${2:-}";; ibkr) cmd_ibkr;; seed-data) cmd_seed_data;;
  weekly) cmd_weekly;; new-backup-key) cmd_new_backup_key;;
  ""|menu) menu;;
  *) echo "Usage: bigwins [status|logs|update|restart|secret <name>|check|claude|remote|app|demo|login|vapid|install-worker|worker|backup|restore-test|onedrive|restore|start-trader <date>|ibkr|seed-data|new-backup-key]";;
esac
