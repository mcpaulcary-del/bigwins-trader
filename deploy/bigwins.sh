#!/usr/bin/env bash
# bigwins - a simple menu for the owner on the server. PAPER ONLY.
# Install once:  ln -sf /srv/asx-trader/deploy/bigwins.sh /usr/local/bin/bigwins
# Then type:     bigwins          (menu)   or   bigwins status | logs | update | restart |
#                secret <name> | check | claude | remote | app | demo | login | vapid |
#                install-worker | worker
# Server-only settings (your Tailscale log-in, tax rate, paper account id...) go in
# config/bfast.local.yaml: not in git, laid over config/bfast.yaml (BF-D39).
set -uo pipefail

REPO=/srv/asx-trader
DEPLOY=$REPO/deploy
SECRETS=$DEPLOY/secrets
CONFIG=$REPO/config/bfast.yaml
LOCAL=$REPO/config/bfast.local.yaml
BASE_SECRETS="tws_password db_password totp_seed eodhd_api_token healthchecks_url ibkr_flex_token ibkr_flex_query_id db_dashboard_password"
APP_SECRETS="vapid_private_key app_proxy_key worker_job_key"  # BF-D40, BF-D46, BF-D48: made here
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
  # shellcheck disable=SC2086
  (cd $DEPLOY && docker compose $f "$@")
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
  else
    y "  Not started yet (it starts after the IBKR details are in: GO_LIVE_GUIDE B8)."
  fi
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
  after_update
}

after_update() {  # secrets the new code needs, then rebuild and restart
  ALL_SECRETS=$(all_secrets)
  make_keys
  if [ -f "$DEPLOY/.env" ] && secrets_ready; then
    docker rm -f bigwins-demo >/dev/null 2>&1
    dc build && dc up -d && g "Updated and restarted."
  else
    g "Code updated. (The trader is not started yet, so nothing to restart.)"
  fi
}

make_keys() {  # BF-D40/D46/D48/D52: generated secrets, made here once, never shown
  [ -s "$SECRETS/vapid_private_key" ] || make_vapid
  local n
  for n in app_proxy_key worker_job_key db_dashboard_password; do
    if [ ! -s "$SECRETS/$n" ]; then
      mkdir -p "$SECRETS" && chmod 700 "$SECRETS"
      openssl rand -hex 32 > "$SECRETS/$n" && chmod 444 "$SECRETS/$n" && g "Made $n."
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
  after_update
}

cmd_update() {
  guard_market || return 1
  do_update
}

cmd_restart() {
  guard_market || return 1
  dc up -d && dc restart trader dashboard && g "Trader and app restarted."
}

cmd_secret() {
  local name=${1:-}
  if [ -z "$name" ]; then
    echo "Which secret?"; select name in $TYPED_SECRETS; do [ -n "$name" ] && break; done
  fi
  if [ "$name" = vapid_private_key ]; then cmd_vapid; return; fi
  case " $TYPED_SECRETS " in *" $name "*) ;; *) r "Unknown secret: $name"; return 1;; esac
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
  UPD_PREV_MIG=""
  [ -n "$UPD_PREV" ] && UPD_PREV_MIG=$(git -C $REPO diff --name-only "$UPD_PREV" "$UPD_HEAD" -- migrations/ 2>/dev/null)
  export UPD_HEAD UPD_REMOTE UPD_AHEAD UPD_FILES UPD_CFG UPD_LOG UPD_SUBJECT UPD_PREV UPD_PREV_MIG
}

host_status() {  # BF-D42: a small JSON snapshot for the app's Server tab (no secrets)
  local ts cv asx ps logs
  update_check
  ts=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("BackendState","?"))' 2>/dev/null)
  cv=$(git -C $REPO log --oneline -1 2>/dev/null | cut -c1-60)
  if market_open; then asx=open; else asx=closed; fi
  ps=$(dc ps --format '{{.Service}}|{{.Status}}' 2>/dev/null)
  logs=$(dc logs --tail 30 --no-color trader 2>/dev/null | tail -30)
  TS="$ts" CV="$cv" ASX="$asx" PS="$ps" LOGS="$logs" python3 "$DEPLOY/host_status.py"
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
  host_status 2>/dev/null | dc exec -T trader trader-bf server-jobs status >/dev/null 2>&1
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
    check|claude_remote|claude_stop) ;;
    *) finish_job "$id" REFUSED "refused: not an allowed server action"; return 0;;
  esac
  case "$action" in  # the fixed list only; nothing from the app is ever run as a command
    restart) out=$(dc up -d 2>&1 && dc restart trader 2>&1); rc=$?;;
    update) out=$(update_to "$commit" "$flags" 2>&1); rc=$?;;
    rollback) out=$(do_rollback "$commit" "$flags" 2>&1); rc=$?;;
    claude_remote) out=$(claude_remote_status start 2>&1); rc=$?;;
    claude_stop) out=$(tmux kill-session -t remote 2>&1 && echo "Claude remote control stopped."); rc=$?;;
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
  if systemctl daemon-reload && systemctl enable --now bigwins-worker.timer; then
    g "Server worker installed. The app's Server tab fills in within a minute."
  else
    r "Could not start the worker."
  fi
}

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
  echo " 13) Install the server worker (app Server tab)"
  echo "  0) Exit"
  read -rp "Choose: " c
  case $c in
    1) cmd_status;; 2) cmd_logs;; 3) cmd_update;; 4) cmd_restart;; 5) cmd_secret;;
    6) cmd_check;; 7) cmd_claude;; 8) cmd_remote;; 9) cmd_app;; 10) cmd_demo;;
    11) cmd_login;; 12) cmd_vapid;; 13) cmd_install_worker;; *) echo "Bye.";;
  esac
}

case ${1:-} in
  status) cmd_status;; logs) cmd_logs;; update) cmd_update;; restart) cmd_restart;;
  secret) cmd_secret "${2:-}";; check) cmd_check;; claude) cmd_claude;; remote) cmd_remote;;
  app) cmd_app;; demo) cmd_demo;; login) cmd_login;; vapid) cmd_vapid;;
  install-worker) cmd_install_worker;; worker) cmd_worker;;
  ""|menu) menu;;
  *) echo "Usage: bigwins [status|logs|update|restart|secret <name>|check|claude|remote|app|demo|login|vapid|install-worker|worker]";;
esac
