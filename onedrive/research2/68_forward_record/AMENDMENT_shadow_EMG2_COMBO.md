# Amendment: paper twin `EMG2_18_SIM_COMBO` (registered EMG2-18 buying rules; sell only after six months and only when out of the top 40%)

Status: **REGISTERED 19 Nov 2026 — PAPER ONLY, information only**, by the record keeper, before the first decision it governs (Mon 30 Nov 2026), on report 90 section 2 and section 4 item 5, at the coordinating session's request of 19 Nov 2026. Report 90 asks for the owner's agreement: no separate owner answer is recorded; the line is paper-only, information-only and costs nothing, and the owner may close it at any time by a later entry. Text below is the research agent's (Fable) draft `deep90/AMENDMENT_shadow_EMG2_COMBO.DRAFT.md` (SHA-256 3b8a7a0cb4161cedcb1fe6fadf245d6594132a43ab09a2a161fc58743149b41e) unchanged except this status line, the title and the added section R. **Recorded plainly: this design was assembled after both its parts had been seen on 2018–2026; it cannot be tested blind on that period, its back-test is not evidence, and no proposal for the live book may be made before the December 2028 review (section 4).** It changes nothing in `AMENDMENT_live_EMG2_18.md`, `AMENDMENT_live_EMG2_20.md`, `AMENDMENT_live_EMG2_18_loss_rule_v2.md`, `AMENDMENT_shadow_EMG2.md` or `AMENDMENT_shadow_EMG2_18_H6.md`. It is **not** a live amendment. The AI never places trades.

## 1. Why, stated plainly
- The live book's one certain cost is trading. In the January 2021 – November 2026 replay the registered rules sent about 115 orders a year: about A$757 of brokerage and A$620 of modelled spread a year on A$10,000.
- Blind build 2 (report 89) chose, from data to 2020 only, a book that sells a holding only after six months and only when it has left the top 40% of its list. That structure sent about 42 orders a year. Its signal and band did worse than EMG2's; its structure was cheap.
- COMBO puts that structure on EMG2-18's own signal, band and buy filter. On seen data it sent about 60 orders a year (brokerage about A$400, spread about A$276) and returned about the same as the registered rules (section 6).
- **This design was put together after its parts had been seen on 2018–2026. It cannot be tested blind on that period, and its back-test is not evidence.** A paper twin from 30 Nov 2026 is the only clean test. It costs nothing.

## 2. Rules
Everything as `EMG2_18_SIM` (rules L1–L3, L5–L7, L9 of `AMENDMENT_live_EMG2_20.md` as amended by `AMENDMENT_live_EMG2_18.md`: A$10,000 at the 30 Nov 2026 decision; band C, the three-measure score and the target list T of EMG2 v1.0 rules 2–3; the lottery filter on buys; n = min(18, floor(account value ÷ A$550)); buys from T best first; month-end clock; IBKR costs), with one change:

- **Rule L4-C (sell).** Define the **keep zone K** at a month-end decision as the members of band C whose score percentile is above 0.60 (the top 40% of band C by the EMG2 score; T, the top fifth, is inside K). A holding is sold in full at a month-end decision only if **both** hold:
  (a) it has been held for **six or more month-end decisions** since its purchase decision (the purchase decision counts as zero); and
  (b) it is **not in K** at this decision (its score percentile is 0.60 or lower, or it is no longer in band C, or it has left the eligible set E).
  A holding that fails only one of the two is kept and re-tested at each decision.
  **Exceptions, sold at once whatever the holding period:** a holding flagged `BID_PEG`; a payout arrives as cash. No trims, no top-ups, no stop-loss.
- Buying is unchanged: only names on T (top fifth) that pass the lottery filter are bought, best first, while fewer than n names are held.

## 3. Books
| Book | Start | Fills |
|---|---|---|
| `EMG2_18_SIM_COMBO` | A$10,000 at the 30 Nov 2026 decision | Next session's close, rule L9 costs |
| `EMG2_18_COMBO_RND_s001…s100` (100 random twins; seeds 8770000 + i) | same | same |

A twin replaces the EMG2 score by a seeded random score per entity that persists and is redrawn with probability 0.2 a month (as `EMG2_18_RND`). Its T is the top fifth of band C by that score, its K the top 40% by that score, and it applies rule L4-C and the same lottery filter, slots and costs.

## 4. Reading
Reported monthly beside `EMG2_18_SIM` and `EMG2_18_SIM_H6`:
- **Facts:** orders, brokerage and modelled spread paid to date by each of the three books; holdings; worst fall on daily values.
- **Mostly luck, and labelled so:** value; the differences COMBO − SIM and COMBO − H6 after costs; percentile among its own 100 twins. Over 68 quarterly starts the 12-month value gap between the registered rules and the H6 variant had a standard deviation of 15 points (report 88); COMBO's gap will be of the same order.
- It is never evidence for or against EMG2.
- **No proposal to change the live book before the December 2028 review.** A proposal then needs all four: (1) COMBO not behind `EMG2_18_SIM` after costs over at least 24 months; (2) COMBO at or above the 75th percentile of its own twins; (3) the spread measured on the live book's fills no more than 1.5 times the model, so that the saving is real; (4) a blind build given no menu (blind build 3 or later) that arrives by itself at a holding rule sending 70 orders a year or fewer. Then an owner decision; no automatic change.
- COMBO − H6 isolates the keep zone (top 40% against top fifth). H6 − SIM isolates the six-month hold. Neither difference is acted on alone.

## 5. What is not changed
The live book, its loss rule, approval rules (L8), stop rules (L12), the capital cap and the gate. The A$100,000 and A$25,000 paper books of `AMENDMENT_shadow_EMG2.md`. The H6 twin.

## 6. Evidence, all on seen data (report 90; `scratchpad/deep90/out/a1_grid_*.csv`, `a2_dd.json`)
| A$10,000, after brokerage, spread and tax | Registered EMG2-18 | H6 | COMBO |
|---|---|---|---|
| Jan 2021 – Nov 2026, mean of 12 start months, research panel / vendor file | 13.7% / 13.2% | 10.2% / 8.4% | 13.0% / 10.7% |
| Range across the 12 starts (panel) | 12.4 to 14.8 | 4.0 to 14.2 | 5.3 to 17.1 |
| Three best holdings removed (panel / vendor) | 5.8% / 5.9% | 3.4% / 1.6% | 7.2% / 6.1% |
| Worst fall, month-end values, worst of 12 starts (panel) | −38% | −39% | −34% |
| Orders a year; brokerage; modelled spread (panel) | 115; A$757; A$620 | 64; A$420; A$299 | 60; A$399; A$276 |
| Percentile among its own 100 twins (panel) | 100 | not run | 100 (twins' median 0.0% a year) |
| Lead over the fund in seven three-year windows 2006–2026, 6 starts each (panel), points a year | +5.4, −7.0, −14.8, −5.8, −4.3, +6.2, −1.3 | +11.1, +0.4, −8.9, −0.3, +4.2, +4.2, +3.8 | +8.7, +2.1, −9.0, +3.0, +5.8, +2.8, +7.2 |
| One book from December 2006 to November 2026 (panel) | 5.5% a year | 10.7% | 11.4% (fund 5.9%) |

Cautions. Before 2018 the registered rules' A$250,000 traded-value test left the book half empty (report 88 section 1.7), which flatters any rule that holds longer; the 2006–2017 columns say more about that test than about the hold. On the vendor file COMBO was 2.5 points a year behind the registered rules in 2021–2026. COMBO was ahead of the registered rules in 7 of the 12 start months on the panel. The fair reading is: about half the orders, no measured loss of return, not shown to be better.

## 7. Trial count
The COMBO back-test is counted in report 90 (one design; N 2,115 → 2,192 with that report's other 76). Registering the twin adds no trial.

## R. Paper-record implementation (record keeper's addition; mechanics only, no rule above is changed)
- Run by the paper code (`bigwins_forward/code/paper_emg2s.py`, called by `paper_daily.py` after `paper_emg2.py`), own state file `emg2s_state.json`; never reads or writes the H82 state or another line's state. Same month-end universe table as the EMG2 paper line (`paper_emg2.table` on the bundle of that month-end; band C, score, score percentile, T, `BID_PEG`, rule-7 payout after 20 sessions without a close). A month-end with an EMG2 data block is no decision and does not count as a month-end decision for the hold.
- Rules of `EMG2_18_SIM` as the paper code applies them: lottery class (FD §8.6) = fewer than 504 sessions since the first price row of the bundle, close (on the day or within 5 sessions) under A$0.20, or `tv_med63` under A$250,000; n = min(18, floor(NAV ÷ 550)), parcel = NAV ÷ n; buy cash = cash + estimated sell proceeds − A$50, shared equally when it is less than the parcels; an order under A$500 is not sent; whole shares at the decision close; fills at the next session's close; IBKR max(A$6.60, 0.088%) a trade; half-spread 0.50% a side with the half-price-step floor (L9 start value); a buy that the fill-day cash cannot cover is cut to whole shares that fit and dropped if under A$500. No canary, no approvals, no IBKR paper mirror (those belong to the live system).
- A same-engine reference book `EMG2_18_REF` (registered sell rule L4, no twins) runs beside the two twins so that H6 − REF and COMBO − H6 are measured inside one engine; the trading system's `EMG2_18_SIM` stays the registered comparison. Values are recorded every session (worst fall on daily values).
