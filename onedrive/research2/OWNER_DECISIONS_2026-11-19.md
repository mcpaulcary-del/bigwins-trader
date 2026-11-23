# Owner decisions — 19 Nov 2026 (in response to report 85 §6.4)

Recorded by the coordinating assistant from the owner's answers in the session chat.

| # | Decision | Owner answer |
|---|---|---|
| D-1 | Lift the v2.13 freeze; FD v3.0 becomes the build document | **Yes** |
| D-2 | EMG2 (ranks 301–600, monthly) is the lead challenger, paper from the 30 Nov 2026 decision; H82 becomes the control | **Yes** |
| D-3 | Adopt rule v3 (staged ladder P0–P3 with stop rules, report 85 §6.3) for high-swing lines; v2 stays for index-like lines | **Yes** |
| D-4 | Pilot cap: lower of A$10,000 and 5% of investable assets | **A$10,000** |
| D-5 | Broker for band-C shares | Not asked separately; default IBKR (paper first), as previously chosen |
| D-6 | Licensed ASX announcements feed | **Yes, if lawful and under ~A$50/month — confirm with owner before any purchase** |
| D-7 | Running budget ~A$700–900 a year | **Yes** |

Standing rules unchanged: paper only until the ladder's gates pass; the AI never places real trades without a later explicit owner change; secrets via secure forms only.

## Later the same day — real money (owner overrides the 12-month paper step of D-3)
- **Real money in EMG2 by end of 2026: A$10,000**, 20-company version (A$500 ASX minimum parcel per first buy).
- **Start: mid-December 2026**, after one month of paper (30 Nov list on paper first).
- **Execution: automated via Interactive Brokers.** Owner was shown that IBKR brokerage at A$10k is about A$840 a year (≈8.4% of capital, larger than EMG2's estimated +1–3 point edge) and chose IBKR automation anyway.
- Safety defaults kept unless the owner changes them: owner approval of each order for the first months, hard loss limits and kill switch, paper and live run side by side, stop rules of adopt rule v3 still apply.
- Owner actions needed: open the IBKR account now (IBKR Pro, cash, Australian stocks), enable the paper account, provide an always-on machine (cloud server or home mini PC).

## Build decisions (B-fast, asx-trader branch bigwins-fast)
- **BF-D1 (owner): live slice holds 18 companies at ~A$550 each (A$10,000 kept)** instead of 20 — 20 parcels fall under the A$500 ASX minimum after reserve and commission. Live variant becomes "EMG2-18".
- BF-D2/BF-D3 (coordinator, owner may override): A$10,000 cap applies to new buys; A$800 per-order limit applies to buys; sells above A$800 go through and page the owner. IBKR's precautionary order-value settings must be raised above the largest expected sell before go-live (checklist item).
- BF-D6: the record keeper fills and freezes config/lic_list.csv (FGG, FGX, PGF, WAR, PCX and other LICs) with the EMG2 amendment.

## Loss limit for the live EMG2-18 slice (after report 87)
- **Owner: if the account falls below A$6,000 (rule L11), PAUSE new buys and alert the owner; KEEP existing holdings; the owner decides whether to resume.** No forced liquidation. (Report 87 replay: the slice fell to ~A$5,231 in Apr 2020 and recovered to A$10,000 by Dec 2020.)
- Registered EMG2-18 rules stay for go-live (report 87: the blind build did not beat them).

## Loss rule REPLACED (after report 88 §4.2) — owner signs Fable's staged rule
Supersedes "pause buys, keep holdings" above (which drifts the book to cash at the low).
1. A$7,000: alert + integrity check (live holdings = simulated twin; fills and costs as modelled).
2. A$6,000: buys pause until the next month-end decision at the latest, then RESUME AUTOMATICALLY unless (a) the integrity check fails, (b) the live book's simulated twin is below the 10th percentile of its 100 random twins since the start, (c) an L12 stop rule is met, or (d) the owner says stop.
3. A$5,000: same test, and the owner must confirm in writing to continue; if not within one decision, the book is sold over the next two decisions.

## Share-list fixes (20 Nov 2026, owner: "Yes, fix both")
1. Class rule: exclude listed investment companies/funds by an exact frozen code list (add the 23 missing traded LICs such as AFI, ARG, MFF, BKI), and stop excluding by name words — real companies PNI, PMV, NGI, AEF, RG1, NZK, CIW come back in. Draft: deep92b/AMENDMENT_class_rule_fix.DRAFT.md.
2. Ranking: traded-value ranks are computed with LICs/funds LEFT OUT, as in the registered EMG2 amendment; the trading system (FD BW-UNI-11) is changed to match, so paper twins and the live book use identical lists.
Both locked in before the 30 Nov decision.

## Live start with the band-trend protection (after report 96), 20 Nov 2026
- Owner chose: the real A$10,000 EMG2-18 book follows the band-trend switch (report 96, draft deep96/AMENDMENT_shadow_EMG2_18_BT.DRAFT.md): at each month-end, if the equal-weight index of the traded-value 301–600 band is below its 10-month average, hold the ASX 200 fund (A200) instead of EMG2 shares; when it is back above, return to EMG2-18 picks. Index fund, not cash.
- Owner was told: the rule did not pass report 96's pre-set bar (its whole lead came from the 2026 fall; it was A$4,000 behind at Dec 2025), it was designed on only 4 overseas markets, and it is currently OFF (hold the fund since 1 Jun 2026), so the live book will likely start in the ASX 200 fund.
- All other live rules (caps, approvals, staged loss rule, stop rules) unchanged.

## Switch mechanics (BF-D28 open point 7), owner approved all three
1. The A200 fund buy is ONE order (exempt from the A$800 per-buy cap; owner is paged); IBKR's max order value setting must be above A$10,000 (go-live checklist).
2. A switch decision uses the start-day limits (24 orders, A$10,500 of buys).
3. If the book starts in FUND state, the canary is the single fund order.

## Protection re-confirmed on corrected figures (report 98), 20 Nov 2026
Report 98 found a replay fault in report 96 (a blocked fund order sat in cash through Mar 2020). Corrected EMG2-18_BT: A$28,277 / A$23,927 (worst fall −46% / −53%) vs plain EMG2-18 A$28,067 / A$23,731 (−56% / −58%). Owner shown these and chose: KEEP the protection for the live book. Build fix BF-D34 handles unsellable shares on a switch day.

## Live sell rule switched to C6 (after report 100), 20 Nov 2026
Owner chose: the live EMG2-18 book (with the band-trend protection unchanged) uses the low-turnover sell rule C6 from report 99/100: a holding is sold only after it has been held at least 6 month-ends AND it is out of the top 40% of band C (plus the existing forced sells: bid-peg, leaving the eligible set/band downward, payouts, protection switch). Buys unchanged. Owner was told: reliable gain ≈ A$250–320/yr fee saving at A$10k only; the rest of report 99's +A$6k is likely luck; overseas C6 won 5 of 8 but lost badly in Canada (−28%); deeper fall on one dataset is noise; no tax-discount benefit (no holding reaches 12 months). The current rule (EMG2-18_BT) keeps running on paper beside it. Code must be tested on paper before any real sell.

## Clarification (coordinator), 20 Nov 2026
The C6 entry above wrongly listed "leaving the eligible set/band downward" as a forced sell. The tested, frozen C6 rule (deep99 FREEZE_99) sells such a holding only once it has been held 6 month-ends. The live and paper books follow the frozen, tested rule (BF-D35, AMENDMENT_live_EMG2_18_C6.md). Forced sells at any time remain: bid-peg (takeover price pinned), payouts/delistings, and the protection switch to FUND.

## 22 Nov 2026 — Run everything through the phone app (owner)
- Owner chose: the Big Wins phone app (private, Tailscale only) does everything: viewing,
  approvals, refuse, pause/kill/stop/resume, and alerts (in-app inbox + phone notifications).
  Telegram is switched off (kept in the code as an option).
- Same safety as before: 6-digit authenticator code for anything that adds risk or re-arms,
  15:20 approval cut-off, Kill/Stop need a confirm, only the owner's Tailscale login may act.
- Known trade-off accepted: app notifications can be delayed by Android and there is no second
  channel; a healthchecks.io "server down" email is added as the backup alarm.

## 22 Nov 2026 — Longer paper soak (owner)
- Paper trading continues to about the end of February 2027 (three month-end decisions plus the
  Christmas/New Year half days); real money (A$10k) around March 2027 instead of mid-December.
  Prompted by a friend's review and the operations review's timeline finding.

## 23 Nov 2026 — Strategy freeze and side variations (owner)
- The main strategy (EMG2-18 + band-trend shield + C6 patient sell, as in the live trader and
  the paper line EMG2_18_SIM_BT_C6) is FROZEN until the start of January 2027: no rule or
  parameter changes to it. Engineering (app, server, backups, reliability, tax) continues.
- New strategy ideas run ON THE SIDE as separate, pre-registered paper lines with their own
  100 random twins; they never change the main line mid-soak.
- Real money still around March 2027, after the paper soak to about end of February.
