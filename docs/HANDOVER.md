# HANDOVER — read this first (state on 22 Nov 2026)

Any Claude (on the server, in a research chat, or a new session) starts here, then reads
`CLAUDE.md`, `NEXT.md`, `docs/DECISIONS.md` and `docs/GO_LIVE_GUIDE.md`.

## What this is
"Big Wins": an automated ASX share strategy for one private owner (Australian, non-technical,
uses a phone). Goal: beat the ASX 200 after costs, or sit in cash/A200 when not worth investing.
**Paper only** until the go-live checklist passes; then A$10,000 of real money in an IBKR cash
account, planned for mid-December 2026. The owner approves every order.

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
- Other paper lines tracked for research: BLIND3 "Steady Momentum", PAIR "Combined",
  H82 "Large-Cap Core", EARLY (rejected). Research trial count N = 2,964.

## Where things live
| Thing | Where |
|---|---|
| Trading code | GitHub `mcpaulcary-del/bigwins-trader`, branch `bigwins-fast`; server `/srv/asx-trader` |
| Paper forward record (hash-chained LEDGER) | research environment; nightly backup to the orphan branch `paper-record`; moves to the server after 30 Nov 2026 (run in parallel for a week, then switch) |
| Research reports (up to 101), FD v3.0, owner decisions log | owner's OneDrive "Share Trading/Big Wins forward record" and research environment |
| Historical data (EODHD, personal non-commercial licence — never share) | OneDrive bundles; not on the server except the forward store |
| Server | BinaryLane, Singapore region, Sydney time zone, Ubuntu 24.04, 2 vCPU / 4 GB; Tailscale-only access (public SSH closed) |

## Owner interface (decided 22 Nov 2026)
- **The Big Wins phone app does everything**: view, approve/refuse orders, pause/kill/stop/resume,
  alerts (inbox + Web Push), server jobs, strategy updates and rollback, tax screen.
  Telegram is off (`notify.channel: app`), kept as an option.
- Safety: 6-digit authenticator code for anything that adds risk or re-arms; 15:20 approval
  cut-off; Kill/Stop need confirm; only the owner's Tailscale login may act; lock-outs after
  wrong codes; root host worker runs only whitelisted, signed, commit-pinned jobs.
  Reviewed twice independently (BF-D46..BF-D61).
- Strategy updates: `update_mode: immediate` while paper (owner wants fast iteration); every
  decision is stamped with its version; rollback in the app. **Research must still pass the full
  tests before a change reaches the app** — fast mode speeds applying, not testing.
- Claude on the server: via the official Claude app (Remote Control). Code changes go
  GitHub → tests → owner approval in the app; never edit the live trader in place.
- Partner (Bec) may get view-only access by Tailscale machine sharing (pending).

## Status / next steps
1. IBKR application submitted 22 Nov; flagged "wholesale investor" — owner to ask IBKR to
   assess as **retail** (answer experience questions truthfully). Do not fund until resolved.
2. After approval: paper account set-up (tiered pricing, order value limit above A$10k, Flex
   query + token), secrets `tws_password`, `ibkr_flex_token`, `ibkr_flex_query_id`, account id
   in `config/bfast.local.yaml`; then the app upgrade sequence (GO_LIVE_GUIDE C7), reality
   spike, five paper dry runs, go-live checklist.
3. 30 Nov 2026: first month-end decisions for all paper lines (research environment).
4. To build: nightly encrypted backup to OneDrive + restore drill; previous-version simulated
   twin; cost analysis (fixed costs ≈ 10% a year on A$10k is a real hurdle).
5. Owner to-dos: 2-step verification on Google/GitHub/BinaryLane/IBKR/Claude/EODHD; authenticator
   QR on the laptop with a backup of the seed; rotate the Telegram token or delete the bot;
   TFN to IBKR; IBKR mobile app as the emergency fallback; delete the old `bigwins-fast-wip`
   remote branch.
6. Final independent stress test of everything before real money (owner asked for it last).

## Rules that never change
Paper only until the checklist passes · never read or show secrets · no automated access to
asx.com.au · EODHD data private · scan for secrets before every push, never force-push ·
the owner's personal details stay out of the repo and out of external requests.
