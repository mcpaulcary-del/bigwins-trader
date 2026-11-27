# Big Wins trader (EMG2-18) — rules for Claude Code on this server

- PAPER ONLY until the owner passes the go-live checklist (docs/GO_LIVE_GUIDE.md part E).
  Never change `LIVE_TRADING_ENABLED`, `allow_live`, the live port or account guards.
- Never read, print, copy or edit anything in `deploy/secrets/` or `deploy/.env`.
  The owner types secrets on the server; check them only with `deploy/check_secrets.sh`
  (it never reads the contents).
- Never place, approve or cancel an order. Orders go only through the trader, approved by
  the owner in the Big Wins app (or `/ok` in Telegram if that channel is switched on).
- No automated access to asx.com.au, with ONE exception (owner decision 24 Nov 2026, ledger seq 96): the
  private info archive may fetch the previous-day announcement list and the director-interest and
  capital-raising notice PDFs from asx.com.au hosts, slowly, for private personal use.
  Widened by the owner on 25 Nov 2026: it may also download the PDFs of PRICE-SENSITIVE announcements,
  from the previous-day list only, for band C companies and paper-line holdings; at most 60 a day, one
  request every 2 seconds, outside ASX hours. Its data is never shared and feeds no strategy.
  Owner decision 27 Nov 2026: the research collector replaces `deploy/info_archive.py` on the server; one
  collector per server. The collector that runs is `record/code/info_archive.py` (the research code,
  unedited), in the record container, behind the network guard `record/tools/net_guard.py` (https to
  asx.com.au and download.asic.gov.au hosts only, redirects pinned, responses capped), with the same
  limits as above. The old host job (`bigwins info-archive`, `deploy/info_archive.py`) stands down while
  the paper record is on the server and never runs beside it. EODHD data is personal and private: do not share it.
- Ask the owner before `docker compose down`, deleting volumes, or anything that stops the
  trader during ASX hours (10:00-16:12 Sydney).
- Scan for secrets before every push; never force-push.
- Read docs/HANDOVER.md first: the whole picture and current status.
- Code changes go GitHub -> tests -> owner approval in the app; never edit the live trader in place.
  Exception (owner decision 25 Nov 2026, BF-D90): app-only changes (display files, docs, tests, research
  content) auto-apply outside ASX hours after CI passes; anything touching trading, config or deploy still
  needs the owner's approval with the 6-digit code.
- Server set-up: deploy/server_bootstrap.sh, then docs/GO_LIVE_GUIDE.md part B.
