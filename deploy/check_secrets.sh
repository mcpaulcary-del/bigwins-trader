#!/bin/sh
# BF-D33: host-side check of deploy/secrets before `docker compose up` (run as root on
# the server from deploy/). Folder 700 (only root lists it), files 444 (each container
# runs as its own non-root uid: trader 10001, postgres 999, the gateway's user), none
# empty. Never prints a secret. The secrets-check service repeats the file check inside
# the stack, as uid 10001.
set -u
cd "$(dirname "$0")" || exit 2
FIX="fix: chmod 700 secrets && chmod 444 secrets/*   (docs/GO_LIVE_GUIDE.md B6)"
bad=0
if [ ! -d secrets ]; then echo "SECRET CHECK FAILED: deploy/secrets is missing (GO_LIVE_GUIDE B6)"; exit 2; fi
m=$(stat -c %a secrets)
if [ "$m" != "700" ]; then echo "SECRET CHECK FAILED: deploy/secrets is mode $m, not 700; $FIX"; bad=1; fi
# BF-D40: the phone app needs vapid_private_key; Telegram (notify.channel telegram|both)
# needs telegram_bot_token
channel=$(sed -n 's/^  channel: *\([a-z]*\).*/\1/p' ../config/bfast.yaml 2>/dev/null | head -1)
names="tws_password db_password totp_seed eodhd_api_token healthchecks_url ibkr_flex_token ibkr_flex_query_id db_dashboard_password"
# BF-D46/D48: app_proxy_key and worker_job_key (made by bigwins update) with the app
case "${channel:-app}" in app|both) names="$names vapid_private_key app_proxy_key worker_job_key";; esac
case "${channel:-app}" in telegram|both) names="$names telegram_bot_token";; esac
count=0
for n in $names; do
  count=$((count + 1))
  f="secrets/$n"
  if [ ! -f "$f" ]; then echo "SECRET CHECK FAILED: $f is missing"; bad=1; continue; fi
  if [ ! -s "$f" ]; then echo "SECRET CHECK FAILED: $f is empty"; bad=1; fi
  m=$(stat -c %a "$f")
  if [ "$m" != "444" ]; then echo "SECRET CHECK FAILED: $f is mode $m, not 444; $FIX"; bad=1; fi
done
if [ "$bad" = 0 ]; then echo "ok: deploy/secrets is 700 and its $count files are 444, none empty (channel ${channel:-app})"; fi
exit $((bad * 2))
