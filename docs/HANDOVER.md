# HANDOVER — read this first (state on 25 Nov 2026, disaster-recovery build BF-D82..D87, odds card BF-D88, research pages BF-D89, automatic app updates BF-D90)

Any Claude (on the server, in a research chat, or a new session) starts here, then reads
`CLAUDE.md`, `NEXT.md`, `docs/DECISIONS.md` and `docs/GO_LIVE_GUIDE.md`.

## What this is
"Big Wins": an automated ASX share strategy for one private owner (Australian, non-technical,
uses a phone). Goal: beat the ASX 200 after costs, or sit in cash/A200 when not worth investing.
**Paper only** until the go-live checklist passes; then A$10,000 of real money in an IBKR cash
account, starting around **March 2027** (owner decision 22 Nov 2026: paper trading until
about the end of February 2027). The owner approves every order.

## The strategy (EMG2-18 "Emerging Momentum")
- Universe: ASX ranks 301–600 by 252-day median traded value (band C), LICs excluded by the
  frozen list `config/lic_list.csv` (69 codes, SHA-256 pinned); ranks computed without LICs.
- Score: mean percentile of s1 (12-1 month momentum), s2 (6-month), s3 (near 52-week high);
  take the top fifth; hold 18 names at about A$550 each; lottery filter.
- Sell rule C6 "Patient Sell": sell only after 6 month-ends AND outside the top 40% of band C;
  forced sells: bid-peg, payout, and the trend-shield switch.
- Trend shield BT: if the equal-weight band 301–600 index is below its 10-month average, hold
  A200 instead.
- Loss rule L11 (daily close value): < A$7k alert + integrity check; < A$6k pause buys until the
  next month-end, then auto-resume unless integrity fails / twin below the 10th percentile of
  100 random twins / stop rule / owner says stop; < A$5k written confirm or wind down over two
  decisions.
- Comparison: 100 random twins drawn from the same buyable set; simulated twin `EMG2_18_SIM`.
- Other paper lines tracked for research (information only, never evidence for or against
  the main line): side lines SWEEP / WIDE / FIP (each the main line with one change,
  ledger seq 91-92) and the aggressive MOON_TOP5 / MOON_NOLOT5 / MOON_LEG2 (seq 94-95),
  all registered before the first decision of 30 Nov 2026 with their own 100 random twins.
  **Retirement list locked (owner, 24 Nov 2026, ledger seq 96)**: kept = BT_C6 main +
  twins, REF book, EMG2, H82, MOM, BLIND3, SWEEP, WIDE, FIP, MOON_TOP5, MOON_NOLOT5,
  MOON_LEG2 (info EST-C, DIL-C); retired at the 31 Dec 2026 close (history kept) = H6,
  COMBO, SIM_BT, PAIR, EARLY, ACC, M3, E3, CXL and the REF twins. No new paper line of any
  kind before the Dec 2028 review unless one is retired. Research trial count
  **N = 3,147** (ledger seq 101, after the ASX improvement round research_bw; the US
  large-cap round research_us4 is still running and will add more).
- Backtest honesty (gap review, seq 90): with the live A$10k cap and rule 14, 2018-26
  gives A$21.0k against A$18.6k for the fund, before fixed costs (not the uncapped
  A$34.5k).

## Where things live
| Thing | Where |
|---|---|
| Trading code | GitHub `mcpaulcary-del/bigwins-trader`, branch `bigwins-fast`; server `/srv/asx-trader` |
| Paper forward record (hash-chained LEDGER) | research environment; nightly backup to the orphan branch `paper-record`; moves to the server after 30 Nov 2026 (run in parallel for a week, then switch) |
| Research reports (up to 101), FD v3.0, owner decisions log | owner's OneDrive "Share Trading/Big Wins forward record" and research environment |
| Historical data (EODHD, personal non-commercial licence — never share) | OneDrive bundles; not on the server except the forward store |
| Server | BinaryLane, Singapore region, Sydney time zone, Ubuntu 24.04, 2 vCPU / 4 GB, 2 GB swap; Tailscale-only access (public SSH closed; Tailscale key expiry disabled) |

## Owner interface (decided 22 Nov 2026)
- **The Big Wins phone app does everything**: view, approve/refuse orders, pause/kill/stop/resume,
  alerts (inbox + Web Push), server jobs, strategy updates and rollback, tax screen.
  Telegram is off (`notify.channel: app`), kept as an option.
- Safety: 6-digit authenticator code for anything that adds risk or re-arms; 15:20 approval
  cut-off; Kill/Stop need confirm; only the owner's Tailscale login may act; lock-outs after
  wrong codes; root host worker runs only whitelisted, signed, commit-pinned jobs.
  Reviewed twice independently (BF-D46..BF-D61).
- **Disaster recovery (24 Nov 2026, BF-D82..BF-D87)**: owner decision, option (b): after
  14 days without an owner action buying pauses (HALTED_BUYS, never lowers a stricter
  level; nothing sold) and a second contact is emailed by healthchecks.io ("owner
  presence" check, secret `healthchecks_presence_url`); I'm here button; a memorised
  passphrase (`app_passphrase`) for re-arm / update / rollback / backup key / Claude
  remote; one-tap Lock actions; `bigwins new-totp`; update signatures checked on the
  server (warn until `bigwins signing enforce`); Claude remote stops after 2 hours.
  Emergencies: GO_LIVE_GUIDE part F; printable card `docs/EMERGENCY_CARD.md`.
- Strategy updates: `update_mode: immediate` while paper (owner wants fast iteration); every
  decision is stamped with its version; rollback in the app. **Research must still pass the full
  tests before a change reaches the app** — fast mode speeds applying, not testing.
- Claude on the server: via the official Claude app (Remote Control). Code changes go
  GitHub → tests → owner approval in the app; never edit the live trader in place.
- The owner's partner may get view-only access by Tailscale machine sharing (pending).

## Strategy freeze (owner, 23 Nov 2026)
The main strategy (EMG2-18 + band-trend shield + C6) is FROZEN until the start of January 2027:
no rule or parameter changes, in the live trader or its paper line. Engineering work continues.
New ideas run as separate pre-registered paper lines with their own random twins ("side lines").
Real money around March 2027.

## Status / next steps
1. IBKR application submitted 22 Nov; flagged "wholesale investor" — owner to ask IBKR to
   assess as **retail** (answer experience questions truthfully). Do not fund until resolved.
2. After approval: paper account set-up (tiered pricing, order value limit above A$10k, Flex
   query + token), secrets `tws_password`, `ibkr_flex_token`, `ibkr_flex_query_id`, account id
   in `config/bfast.local.yaml`; then the app upgrade sequence (GO_LIVE_GUIDE C7), reality
   spike, five paper dry runs, go-live checklist.
3. 30 Nov 2026: first month-end decisions for all paper lines (research environment).
4. Built since: nightly encrypted backups (server + OneDrive) with a weekly restore test
   (BF-D64, BF-D70). **24 Nov 2026 (BF-D75..BF-D80)**: the honest scoreboard as the Home
   headline (main line after all costs v the same money in A200; research lines unranked,
   "mostly luck at this stage"); running-costs tracker (Server > Running costs, amounts
   editable in the app); Server > Health; the missed-job alarm (one push per incident)
   and an optional outside daily-cycle check (`healthchecks_daily_url`); announcements,
   director trades and short positions on each share's page from the private info
   archive (host job, **off** until after 30 Nov); the weekly digest in the Inbox
   (Fridays after the close); the previous-version simulated twin (runs after the next
   strategy update). Review fixes BF-D81 (one scoreboard for app and digest, "before tax"
   when no tax rate, cash-flow-dated A200, exact research book names, safer archive and
   twin jobs). Deploy before the paper trader's first decision (GO_LIVE_GUIDE C7).
   **25 Nov 2026 (BF-D88)**: each share page shows "Odds for shares like this
   (history)" from `config/odds_table_v1.csv` (aggregated counts by size band and score
   quintile, 2005-2025; descriptive, not a trial, no strategy change); rebuild at most
   yearly with `research/odds_table/build_odds_table.py` (`docs/ODDS_TABLE.md`).
   **25 Nov 2026 (BF-D89)**: Research in the app (Home › "What we know", `/research`:
   Highlights, Library, Testing, Dates, Glossary) from `docs/research/`; the live trial
   count from the record's `LEDGER.jsonl` once the record is on the server. This build is
   a trading / infrastructure update (Dockerfile, config, classifiers): deploy before the
   first decision (C7). Later content-only commits are app-only.
   **25 Nov 2026 (BF-D90, owner request "Need to auto update")**: automatic app updates.
   The host timer `bigwins-autoupdate` (every 30 min, :07/:37; installed and repaired by
   the worker like the other timers) applies **app-only** commits of `bigwins-fast` by
   itself (allow-list: the display-only `UI_ONLY` files, `docs/`, `tests/`, `research/`,
   top-level `*.md` except CLAUDE.md; `deploy/autoupdate.py`) outside ASX hours (09:30-
   16:30 Sydney on trading days blocked; weekends and holidays allowed), fast-forward only,
   after GitHub CI passed for that exact commit (public Actions API; optional
   `github_ci_token` if the repo goes private), at least 1 h old here (24 h live), signed
   when enforced, and on a live book only with signing enforced (off by default when live).
   It rebuilds and restarts only the app (dashboard, or the demo container), never the
   trader; health check, else automatic rollback + PAGE. Everything else (trading code,
   config, deploy scripts, the worker and the auto-updater itself, timers, compose,
   Dockerfile, secrets handling) gets one "Update ready: <title> — tap to review and
   approve" push and the existing approval flow; in demo mode (no trader) the demo app
   shows "Update ready on the server" and the owner runs `bigwins update`. Switch:
   `bigwins autoupdate on|off|status` or Settings > Automatic app updates (code). Health
   shows the last applied update and the next check; the Inbox gets each one. This build
   itself is infrastructure: the owner applies it once by hand (GO_LIVE_GUIDE C7 step 9).
   Note: CLAUDE.md still says code changes need owner approval in the app; app-only
   changes now auto-apply by owner decision (BF-D90). CLAUDE.md is the owner's to amend.
   **26 Nov 2026 (BF-D91, owner request "the report display needs a lot more work")**: the
   report screens were rebuilt for the phone, display only: Home's scoreboard as two bars and a
   gap chart with "mostly luck at this stage" while the record is under 24 months, the approval
   card and a "Needs you" card directly under it; daily reports and approval requests open in
   the Inbox as cards (the stored text is kept under "Original message"); the weekly digest,
   Running costs, Health and the research pages put the answer and the action first. App-only
   (`UI_ONLY` files), so it applies by itself (BF-D90). The daily report's text
   (`trader/report.py`) and the share pages (`trader/share_pages.py`, `trader/app_viz.py`,
   `trader/app_more.py`) were not touched: those files need the owner's approval.
5. **Costs (review, 22 Nov 2026)**: fixed costs about **A$650 a year (6.5% of A$10k)**:
   server, price data, Claude-side tools; with IBKR tiered commissions about **A$1,360 a year
   (13.6%)**, more with an ASX market-data subscription. In the fund (A200) state the book
   pays these fixed costs just to hold an index fund. The EODHD price in these figures is
   **unverified** (check the current plan). The L14 cost statement and the app's "same money
   in A200" comparison include `costs.fixed_aud_per_year` (default A$600).
6. **The research record moves to the server after 30 Nov 2026** (the coordinator does it);
   the golden checks of each update need it there (BF-D71).
7. **Disaster-recovery set-up from the phone (GO_LIVE_GUIDE F0)**: passphrase, the
   owner-presence check with the second contact, Tailscale device approval and SSH limit
   (F10), break-glass root password tested (F3), `bigwins offsite2`, renewal dates in
   Health, the emergency card filled in by hand. Before real money also: signing enforced
   (F5b, needs the engineer's key), the timed second-server drill from the phone (F4), an
   IBKR trading-only gateway user (F7). Then deploy with C7 step 8.
   Owner to-dos: 2-step verification on Google/GitHub/BinaryLane/IBKR/Claude/EODHD; authenticator
   QR on the laptop with a backup of the seed; rotate the Telegram token or delete the bot;
   TFN to IBKR; IBKR mobile app as the emergency fallback; delete the old `bigwins-fast-wip`
   remote branch.
8. Final independent stress test of everything before real money (owner asked for it last).

## Owner decision 24 Nov 2026: the private info archive
Automated access to asx.com.au is allowed **only** for the private info archive
(`deploy/info_archive.py`, server copy of the research script `bigwins_forward/code/
info_archive.py`): the previous trading day's announcement list and the director-interest
(Appendix 3Y/3X/3Z) and capital-raising notice PDFs, plus ASIC's daily short positions.
Personal, non-commercial use, never shared, feeds no paper line and no trading decision
(ledger seq 96). The trader and the app themselves never contact asx.com.au. On the
server the archive is a host job, off until the research record moves (after 30 Nov;
GO_LIVE_GUIDE C10).

## Research content (BF-D89): after every study
Claude updates `docs/research/` in ONE commit at the end of each study: the study card
`studies/<id>.md` (front matter + Summary / Key numbers / What it means for you / How sure
are we?, with `trials`, `n_total` and the ledger entry), `highlights.yaml` if a slot
changes (bump `version`, `checked`, `trials_total`, `trials_ledger_seq`), `testing.yaml` /
`dates.yaml` if a line or date changes. A pre-registered study is committed first as
`placeholder: true`. Aggregated numbers and plain text only: no vendor price rows, no
per-company series, no paths, names, emails or account ids; full reports stay on OneDrive
(`report: null`). Run `tests/test_bf_d89_research.py` (limits, traceability, privacy).
A content-only commit is an app update; since BF-D90 the server applies it by itself
(outside ASX hours, after CI passes, at least an hour after the push); keep such commits
content-only (never mix in deploy, config or trading files, or the whole commit waits for
approval).

## Rules that never change
Paper only until the checklist passes · never read or show secrets · no automated access to
asx.com.au (the one exception above) · EODHD data private · scan for secrets before every push, never force-push ·
the owner's personal details stay out of the repo and out of external requests.
