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
for n in tws_password db_password telegram_bot_token totp_seed eodhd_api_token \
         healthchecks_url ibkr_flex_token ibkr_flex_query_id; do
  f="secrets/$n"
  if [ ! -f "$f" ]; then echo "SECRET CHECK FAILED: $f is missing"; bad=1; continue; fi
  if [ ! -s "$f" ]; then echo "SECRET CHECK FAILED: $f is empty"; bad=1; fi
  m=$(stat -c %a "$f")
  if [ "$m" != "444" ]; then echo "SECRET CHECK FAILED: $f is mode $m, not 444; $FIX"; bad=1; fi
done
if [ "$bad" = 0 ]; then echo "ok: deploy/secrets is 700 and its 8 files are 444, none empty"; fi
exit $((bad * 2))
