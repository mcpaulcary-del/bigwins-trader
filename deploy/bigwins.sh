#!/usr/bin/env bash
# bigwins - a simple menu for the owner on the server. PAPER ONLY.
# Install once:  ln -sf /srv/asx-trader/deploy/bigwins.sh /usr/local/bin/bigwins
# Then type:     bigwins          (menu)   or   bigwins status | logs | update | restart |
#                secret <name> | check | claude | remote | app
set -uo pipefail

REPO=/srv/asx-trader
DEPLOY=$REPO/deploy
SECRETS=$DEPLOY/secrets
ALL_SECRETS="tws_password db_password telegram_bot_token totp_seed eodhd_api_token healthchecks_url ibkr_flex_token ibkr_flex_query_id"

g() { printf '\033[32m%s\033[0m\n' "$*"; }
y() { printf '\033[33m%s\033[0m\n' "$*"; }
r() { printf '\033[31m%s\033[0m\n' "$*"; }

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

cmd_status() {
  echo "== Big Wins server  $(date '+%a %d %b %Y %H:%M %Z')"
  if market_open; then echo "ASX: open"; else echo "ASX: closed"; fi
  echo "Code version: $(git -C $REPO log --oneline -1 2>/dev/null)"
  echo "Disk used: $(df -h / | awk 'NR==2{print $5" of "$2}')   Memory used: $(free -m | awk '/Mem/{printf "%d%%", $3*100/$2}')"
  echo "Tailscale: $(tailscale status >/dev/null 2>&1 && echo connected || echo NOT connected)"
  echo
  echo "== Secrets (names only, contents never shown)"
  local n=0 name
  for name in $ALL_SECRETS; do
    if [ -s "$SECRETS/$name" ]; then g "  ok       $name"; n=$((n+1)); else y "  missing  $name"; fi
  done
  echo "  $n of 8 in place"
  echo
  echo "== Trader"
  if [ -f "$DEPLOY/.env" ] && (cd $DEPLOY && docker compose ps --format '{{.Service}}' 2>/dev/null | grep -q .); then
    (cd $DEPLOY && docker compose ps --format '  {{.Service}}: {{.Status}}')
  else
    y "  Not started yet (it starts after the IBKR details are in: GO_LIVE_GUIDE B8)."
  fi
  echo
  echo "== Phone app (read-only dashboard)"
  if curl -fsS -m 3 http://127.0.0.1:8080/healthz >/dev/null 2>&1; then
    g "  dashboard: running on 127.0.0.1:8080"
  else
    y "  dashboard: not running"
  fi
  if tailscale serve status 2>/dev/null | grep -q 8080; then
    g "  on your phone: $(app_url)"
  else
    y "  not shared on Tailscale yet (menu option 9)"
  fi
}

app_url() {  # the server's Tailscale name, e.g. https://bigwins.tailnet-name.ts.net
  local dns
  dns=$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null)
  [ -n "$dns" ] && echo "https://$dns"
}

cmd_app() {  # BF-D37: the read-only phone page, on your tailnet only
  if ! tailscale status >/dev/null 2>&1; then r "Tailscale is not connected on the server."; return 1; fi
  tailscale serve --bg 8080 || { r "tailscale serve failed (is HTTPS on in the Tailscale admin page?)."; return 1; }
  local url; url=$(app_url)
  g "The Big Wins app is on: ${url:-https://<server>.<tailnet>.ts.net}"
  echo "Open it on your phone (Tailscale app on, same account), then Chrome menu > Add to Home screen."
  echo "Only devices on your tailnet can open it. Turn it off with: tailscale serve reset"
}

cmd_demo() {  # the phone page with DEMO data, before the trader has started (no secrets, no database)
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
  g "Demo app running (made-up numbers, marked DEMO)."
  cmd_app
}

cmd_logs() {
  cd $DEPLOY || return 1
  docker compose logs --tail 40 trader 2>/dev/null || y "Trader not started yet."
}

cmd_update() {
  guard_market || return 1
  git -C $REPO pull --ff-only || { r "Update failed (no changes made)."; return 1; }
  if [ -f "$DEPLOY/.env" ] && [ "$(ls "$SECRETS" 2>/dev/null | wc -l)" -ge 8 ]; then
    (docker rm -f bigwins-demo >/dev/null 2>&1; cd $DEPLOY && docker compose build && docker compose up -d) && g "Updated and restarted."
  else
    g "Code updated. (The trader is not started yet, so nothing to restart.)"
  fi
}

cmd_restart() {
  guard_market || return 1
  cd $DEPLOY && docker compose up -d && docker compose restart trader && g "Trader restarted."
}

cmd_secret() {
  local name=${1:-}
  if [ -z "$name" ]; then
    echo "Which secret?"; select name in $ALL_SECRETS; do [ -n "$name" ] && break; done
  fi
  case " $ALL_SECRETS " in *" $name "*) ;; *) r "Unknown secret: $name"; return 1;; esac
  mkdir -p "$SECRETS" && chmod 700 "$SECRETS"
  echo "Paste the value for $name and press Enter (nothing will show on screen):"
  local v; read -rs v; echo
  [ -n "$v" ] || { r "Nothing entered; $name not changed."; return 1; }
  [ -f "$SECRETS/$name" ] && chmod 600 "$SECRETS/$name"
  printf '%s' "$v" > "$SECRETS/$name"; unset v
  chmod 444 "$SECRETS/$name"
  g "Saved $name ($(wc -c < "$SECRETS/$name") characters)."
}

cmd_check() { cd $DEPLOY && ./check_secrets.sh; }

cmd_claude() {
  tmux has-session -t claude 2>/dev/null || tmux new -d -s claude -c $REPO claude
  tmux attach -t claude
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
  echo "  0) Exit"
  read -rp "Choose: " c
  case $c in
    1) cmd_status;; 2) cmd_logs;; 3) cmd_update;; 4) cmd_restart;; 5) cmd_secret;;
    6) cmd_check;; 7) cmd_claude;; 8) cmd_remote;; 9) cmd_app;; 10) cmd_demo;; *) echo "Bye.";;
  esac
}

case ${1:-} in
  status) cmd_status;; logs) cmd_logs;; update) cmd_update;; restart) cmd_restart;;
  secret) cmd_secret "${2:-}";; check) cmd_check;; claude) cmd_claude;; remote) cmd_remote;;
  app) cmd_app;; demo) cmd_demo;;
  ""|menu) menu;;
  *) echo "Usage: bigwins [status|logs|update|restart|secret <name>|check|claude|remote|app|demo]";;
esac
