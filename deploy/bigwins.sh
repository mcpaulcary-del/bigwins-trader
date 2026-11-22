#!/usr/bin/env bash
# bigwins - a simple menu for the owner on the server. PAPER ONLY.
# Install once:  ln -sf /srv/asx-trader/deploy/bigwins.sh /usr/local/bin/bigwins
# Then type:     bigwins          (menu)   or   bigwins status | logs | update | restart |
#                secret <name> | check | claude | remote
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
}

cmd_logs() {
  cd $DEPLOY || return 1
  docker compose logs --tail 40 trader 2>/dev/null || y "Trader not started yet."
}

cmd_update() {
  guard_market || return 1
  git -C $REPO pull --ff-only || { r "Update failed (no changes made)."; return 1; }
  if [ -f "$DEPLOY/.env" ] && [ "$(ls "$SECRETS" 2>/dev/null | wc -l)" -ge 8 ]; then
    (cd $DEPLOY && docker compose build && docker compose up -d) && g "Updated and restarted."
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
  echo "  0) Exit"
  read -rp "Choose: " c
  case $c in
    1) cmd_status;; 2) cmd_logs;; 3) cmd_update;; 4) cmd_restart;; 5) cmd_secret;;
    6) cmd_check;; 7) cmd_claude;; 8) cmd_remote;; *) echo "Bye.";;
  esac
}

case ${1:-} in
  status) cmd_status;; logs) cmd_logs;; update) cmd_update;; restart) cmd_restart;;
  secret) cmd_secret "${2:-}";; check) cmd_check;; claude) cmd_claude;; remote) cmd_remote;;
  ""|menu) menu;;
  *) echo "Usage: bigwins [status|logs|update|restart|secret <name>|check|claude|remote]";;
esac
