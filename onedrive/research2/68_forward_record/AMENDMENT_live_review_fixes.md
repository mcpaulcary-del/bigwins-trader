# AMENDMENT — live trader (B-fast) changes from the full independent review, 22 Nov 2026

Status: LIVE TRADER ONLY (the EMG2_18_PAPER broker book and its in-trader twins). The research paper
record's scripts in bigwins_forward/code/ are NOT changed by this amendment. Registered before the
first decision these rules govern (30 Nov 2026 month-end; the broker book has not started trading).
No new research trials (n_trials unchanged at 2964). Code: bigwins-trader branch bigwins-fast at b69c5ae7f891147b2ddba9042287c9320bcdfe24
(commits f53f767, 8e9b4b0, b69c5ae; DECISIONS BF-D69..BF-D72).

## Changes that alter registered live parameters (L10 / costs)
1. Daily limits (L10): normal limit 20 buy orders and A$10,500 of buys per day (was 16 orders /
   A$4,500); sell orders no longer count toward the per-day order limit; nothing latches HALTED at
   plan time (only the hard ceiling of 80 orders latches). Reason: the old limits could not fit a
   normal C6 month-end (all 18 holdings reaching 6 month-ends together) or the L11 wind-down.
2. Commission model: IBKR tiered (default, owner advised to choose tiered): (max(A$5, 0.08%) +
   exchange/clearing fees) x 1.10 GST; the exchange/clearing rate 0.005% is unverified and is checked in
   the reality spike. The L11 integrity test compares commission with a tolerance (A$0.50 or 15%).
3. Early-close sessions (24 and 31 Dec) are non-order days for new orders; orders carry to the next full
   session. Nothing is sent after 15:55 (or close minus 10 minutes). Stale approvals lapse.

## Changes that align the live trader to the registered paper/research rules (bug fixes)
4. Bid-peg flag needs 5 or more closes in the 10-session window (registered rule; live had 2). Pegged
   names are excluded from the twins' count as in paper. This changes the in-trader twins' draws.
5. Dividends and splits counted once per (code, ex-date), per-symbol file winning (live double-counted
   bulk events; paper never did).
6. Band-trend history: month-end band-index steps loaded from the paper record runs
   (config/band_trend_steps.csv) so delisted names are included, as in paper; newer steps live.
7. Codes first seen in the bulk feed get panel columns (new listings / ticker changes), as paper's
   per-symbol refresh provides.

## Known differences kept (documented, not changed)
Traded-value zero-fill convention vs the reports 87-100 engine (BF-D20/M1); small definitional
differences listed in DECISIONS BF-D72 (largest observed score difference 0.0035, identical lists).

## Open owner decisions (not changed here)
The A$10,000 capital cap (deposits vs total) and the cost question for a A$10k account.
