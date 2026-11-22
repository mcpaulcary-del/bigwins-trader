# Big Wins trader (EMG2-18) — rules for Claude Code on this server

- PAPER ONLY until the owner passes the go-live checklist (docs/GO_LIVE_GUIDE.md part E).
  Never change `LIVE_TRADING_ENABLED`, `allow_live`, the live port or account guards.
- Never read, print, copy or edit anything in `deploy/secrets/` or `deploy/.env`.
  The owner types secrets on the server; check them only with `deploy/check_secrets.sh`
  (it never reads the contents).
- Never place, approve or cancel an order. Orders go only through the trader, approved by
  the owner in the Big Wins app (or `/ok` in Telegram if that channel is switched on).
- No automated access to asx.com.au. EODHD data is personal and private: do not share it.
- Ask the owner before `docker compose down`, deleting volumes, or anything that stops the
  trader during ASX hours (10:00-16:12 Sydney).
- Scan for secrets before every push; never force-push.
- Read docs/HANDOVER.md first: the whole picture and current status.
- Code changes go GitHub -> tests -> owner approval in the app; never edit the live trader in place.
- Server set-up: deploy/server_bootstrap.sh, then docs/GO_LIVE_GUIDE.md part B.
