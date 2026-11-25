# DRAFT — NOT REGISTERED. Amendment: LIVE book EMG2-18 and its paper line `EMG2_18_SIM_BT_C6` adopt the January engineering amendment E5 (rule 14 never blocks a sale; cash above the cap is swept into A200)

> **DRAFT, 25 Nov 2026.** Not hashed, not in `LEDGER.jsonl`, governs nothing. It is registered only by the record keeper, and only after the owner says yes on or after 1 Jan 2027 (the main strategy is frozen until then: ledger seq 88). If the owner says no, this file is withdrawn unregistered. Until registration the live book and `EMG2_18_SIM_BT_C6` run exactly as registered.

Status (to be filled at registration): **REGISTERED <date> (Sydney)**, by the record keeper, on the owner's decision of <date> (decision sheet `jan2027/DECISION_SHEET.md`, question 1). Amends `AMENDMENT_live_EMG2_20.md` (seq 37) as amended by `AMENDMENT_live_EMG2_18.md` (seq 39), `..._loss_rule_v2.md`, `AMENDMENT_class_rule_fix.md` (seq 62), `AMENDMENT_live_EMG2_18_BT.md` (seq 71, L15) and `AMENDMENT_live_EMG2_18_C6.md` (L4-C6); and the paper line `AMENDMENT_shadow_EMG2_18_BT_C6.md` (with `AMENDMENT_shadow_EMG2_18_BT.md` rules BT1–BT4 and `..._leftover.md`, which it inherits). **Effective at the first decision after the owner's approval** (the trading system's first decision with the update applied; for the paper line, the first month-end decision after registration). The go-live checklist remains the gate. Paper only until the owner's separate live enablement; **the AI never places trades.**

Implementation (already built, not deployed): trading system `/home/user/asx-trader`, branch **`jan2027-fixes`**, commit `16896cc` (`docs/DECISIONS.md` BF-D90, tests `tests/test_bf_d90_e5.py`). The branch is not merged into `bigwins-fast`; the server's update path offers only commits on `origin/bigwins-fast`, so it cannot be applied before the owner's approval and the merge. The code acts only at decisions on or after `live_emg2_20.e5.effective_from` (2027-01-01).

## 1. Why
- **Rule 14 as it runs today is the largest fixable drag on the main line** (`research_grand` s3, the edge decomposition). "Band C has fewer than 150 names: no decision" switched the live rule off in most months: it was in cash **53% of months over 2002–2026**, and the live rule (M0, A$10k cap + rule 14) **trailed A200 by about 1.7 points a year** over 25 years (untaxed −1.1, SE 2.7). Rule 14 alone cost −2.2 points a year; the cap and idle cash −2.8.
- **Rule 14 also blocks sales** (`research_gaps` finding 2; `research_bw` s2). It is checked before the L15 fund-state sales, so a thin band also stops `BID_PEG`, C6 and the shield's sales. In the 2019–Oct 2026 hold-out it blocked share sales the frozen rules wanted at **13 month-ends (179 holding-months)**; band C was under 150 in 12 of 18 shield-OFF switch months since 2002, all of 2008 and March 2020. It blocked all trading in 42 of the last 95 month-ends (Dec 2018 – Jun 2020 entirely). Band C holds 164 names today.
- **Idle cash above the cap earns nothing.** The A$10,000 cap means any gain above it sits in cash.
- `research_bw` s2 tested the two engineering fixes as **E5** (and separately): the sale fix alone **lost** A$663 (buys stay blocked so the book runs down; blocked sales had accidentally become long holds with the tax discount); the sweep added about A$1,710; the package was **+A$1,047** (FULL), **−A$283** in 2019–2022 (H1; the engineering no-harm tolerance was A$250, missed by A$33), +A$353 in 2023–2026 (H2).

## 2. Rule text (exactly as `research_bw` s5 tested it in E5)
Replaces EMG2 v1.0 rule 14 for the live book (and its twins) and for `EMG2_18_SIM_BT_C6` (and its 100 twins); adds the sweep. Everything not listed here is unchanged.

> **Rule 14 (amended).** At a month-end decision where band C holds fewer than 150 eligible names, no share is bought and the fund is not sold. Every sale the rules require still happens: a `BID_PEG` holding, a C6 sale (held six or more month-ends and score percentile 0.60 or lower, or out of band C, or not eligible), and at state OFF every share, with the proceeds buying the fund as in BT3. Month-end ages count as before.
>
> **Sweep.** At each month-end decision, after the rules' own orders, X = value of the trading book at the decision close − A$10,000. If X ≥ A$500, X (at most the cash less A$50) buys A200 at the fill close, in a sleeve the rules never count, size on or sell.

Clarifications (mechanics, not rule changes; how the trading system implements the text, BF-D90):
- **Which blocks are narrowed.** Only rule 14's count test (band C holds names, fewer than 150). An empty band C, the H82 market-wide verdict failing (paper line), a stale price store or missing closes (trading system) stay full data blocks: no decision, holdings kept, no sweep.
- **"Trading book"** = cash plus every holding except the sleeve, valued at the decision close as the rules value them. The sleeve is never part of the account value, slot count n, parcel size, the A$10,000 room (L1), the 10% fund top-up test (BT3) or any sale.
- **"The cash"** for the sweep = the cash after the decision's own sales and buys (the trading system estimates sale proceeds as for every buy; the paper engine uses its fills). Under A$500 the sleeve buy is not sent.
- **Every decision** includes the trading system's out-of-cycle decision after an update (BF-D45) and the start decision; the sweep is part of the same batch and needs the owner's approval like any other order (L8).
- **One A200 position.** The broker holds the rules' A200 and the sleeve in one position. The sleeve is the units bought by sleeve orders; at state ON (BT4) only the rules' units are sold. Only the owner's own wind-down (L11 stage 3 / stop) sells the sleeve.
- **Risk limits.** The sleeve buy has the fund order's limit (A$10,000, paged above A$800); the capital cap and the day's buy-value limit do not apply to it (it only holds money above the cap). A sleeve buy above A$10,000 (a trading book above A$20,000) would be refused and paged.
- **Readings count the sleeve.** The scoreboard ("main line after all costs against the same money in A200"), L11's values, the twin percentile and L13 use the whole book, sleeve included.
- **Books.** The simulated twin `EMG2_18_SIM`, the 100 random twins `EMG2_18_RND_s001…s100`, `EMG2_18_SIM_BT_C6` and its twins `EMG2_18_BT_C6_RND_s001…s100` all follow the amended rule 14 and the sweep at the same decisions, so the comparisons stay like for like.
- **Paper engine** (record keeper's section R, to be written at registration): `paper_emg2bt6.py` gains (a) the thin-band path (C6/`BID_PEG` sales in state ON with the fund kept; BT3 in state OFF) where it now records "EMG2 data block: no decision" for `R['blocked_reason']` of rule 14 only, and (b) a sleeve kept as its own A200 lot in the state file (`sleeve_units`), bought after the decision's orders at the fill close with 0.05% half-spread and IBKR costs, never sold, valued in NAV. The code change is its own code ledger entry, hashed before the first decision it governs, with a test that every other line's output is byte-identical.

## 3. Expected effect, with honest uncertainty
From `research_grand` s3 (2002–2026, five fresh 5-year books, A$10k) and `research_bw` s2 (hold-out 2019–Oct 2026, mean of 12 starts, 47% tax, before fixed costs):

| | Live rule today (M0) | With E5 | A200 |
|---|---|---|---|
| Lead over A200, untaxed, 2002–2026 (points a year) | −1.1 (SE 2.7) | **+3.3 (SE 1.9)** | — |
| Lead in super (15%) / personally (47%), before fixed costs | — | +2.8 / **+1.4 (SE 2.3)** | — |
| Net lead personally after A$650 a year fixed costs, A$10k / A$50k | −6.9 / −2.5 | −3.8 / +0.4 | — |
| Hold-out A$10k, 47% tax, before fixed costs | A$18,198 | A$19,246 | A$16,248 |
| Hold-out A$50k, 47% tax, before fixed costs | A$94,351 | A$99,204 | A$81,368 |
| Months in cash (hold-out cash share) | 41% | 12% | 0% |
| Worst fall (mean / worst start) | −31% / −31% | −33% / −36% | −36% / −36% |

What this does **not** show:
- **The edge is not proven.** E5 against the main line: **t = 0.75** over 94 monthly gaps; Bonferroni p 1.0; deflated Sharpe about 0.001–0.005. The expected best t of ~3,170 null trials is 3.57. A true lead of 2 points a year would need about 8.5 points a year to reach t = 2 in eight years (`research_bw` s2). No paper record of any realistic length can confirm it (`research_grand` s3, s8).
- **The hold-out is not clean.** The base rule was built on 2018–2026; the 25-year column is the one to read. The 2019–2026 hold-out is effectively one path (all 12 main-line starts sat in cash until Aug 2020 because of rule 14).
- **The main line missed the March 2020 crash by accident** (rule 14 held it in cash). E5 holds A200 in that situation and falls with it: the worst start's fall is about 5 points deeper (−36% against −31%). Removing rule 14 outright (M1) gave −47% / −53% in the hold-out; E5 keeps the "stand aside from buying" part.
- **The sale fix alone loses money** (−A$663 FULL); the package depends on the sweep. E5 missed the no-harm tolerance in 2019–2022 by A$33.
- **At A$10k, after fixed costs, every version trails A200** (E5 about −A$400–500 a year; the live rule about −A$700–800). Fixed costs (about A$650 a year) are in no back-test book.
- Dividends and franking are not taxed in any research book.

## 4. The open decision on rule 14
This amendment keeps rule 14 as a deliberate **"thin band, stand aside from buying"** rule with sales unblocked. A count of 150 is not a data check; whether to replace it by a real data-completeness test is the owner's separate decision. The information-only draft `drafts/AMENDMENT_info_rule14_datacheck.md` reads such a test forward without trading it; any later change to the live rule needs its own amendment.

## 5. Unchanged
The capital cap (L1, A$10,000 for the rules), slots and parcels (L3), the A$500 minimum and A$50 reserve (L5), the canary (L6), clock and carry (L7), owner approval of every broker-book order (L8), costs (L9), the hard limits (L10, except the sleeve buy's limits above), the staged loss rule (L11 v2), the stop rules (L12), reporting (L14), the band-trend switch (L15) and BF-D34, sell rule C6, the lottery filter, the list T, the twins' seeds, reconciliation and the gate. The retirement list (`AMENDMENT_retirement_jan2027.md`) and the line cap are unchanged: no line is added (this changes an existing line's rules).

## 6. Reading
Reported monthly beside the current figures: the sleeve's value, the months with a thin band and the sales made in them (fact); the value difference against the pre-E5 rules is not computed forward (no second book) and is not claimed. Reviewed at the December 2027 C6 review and the December 2028 review. The live book is never evidence for or against E5.

## 7. Trial count
E5 was counted in `research_bw` (seq 101) and on 2002–2026 in `research_grand` (N 3,332). Registering adds **no trial**.
