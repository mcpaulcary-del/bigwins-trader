# Amendment: paper twin `EMG2_18_SIM_H6` (registered EMG2-18 rules with a 6-month minimum hold)

Status: **REGISTERED 19 Nov 2026 — PAPER ONLY, information only**, by the record keeper, before the first decision it governs (Mon 30 Nov 2026), on reports 87 (draft), 88 section 4.3 and 90 section 4 item 3. Text below is the research agent's (Fable) draft `deep87/AMENDMENT_shadow_EMG2_18_H6.DRAFT.md` (SHA-256 a2d156835a1ab91642a1c011961f53e359d15fe96ca1d14fbe9058e6f7bfb00c) unchanged except this status line, the title, **section 3, replaced by the reading of report 88 section 4.3** (the draft's 12-month test 'A$200 less brokerage and not more than 3% below' is withdrawn: the 12-month value gap has a standard deviation of about 15 points, so that test would pass or fail on luck), and the added section R. It changes nothing in `AMENDMENT_live_EMG2_18.md`, `AMENDMENT_live_EMG2_20.md`, `AMENDMENT_live_EMG2_18_loss_rule_v2.md` or `AMENDMENT_shadow_EMG2.md`. It is **not** a live amendment. The AI never places trades.

## 1. Why
Brokerage is the one certain cost of the live book: about A$700 a year at A$10,000 (report 87: 105–110 orders a year in the 2018–Oct 2026 replay). A 6-month minimum hold was part of the design chosen mechanically from pre-2018 data in report 87. Applied to the registered rules as an information run it cut orders to about 61 a year (brokerage about A$405) and returned 14.2% a year after tax against 11.3% on the research panel, 9.5% against 9.2% on the vendor file, and on the vendor file was lower on the mean of 12 start months (9.3% against 10.2%). Worst fall about the same (43–49%). **Not a clear improvement; one of six information runs; not judged against a pre-set bar.** A paper twin costs nothing and answers the question on forward data.

## 2. Rules
Everything as `EMG2_18_SIM` (rules L1–L7, L9 of `AMENDMENT_live_EMG2_20.md` as amended by `AMENDMENT_live_EMG2_18.md`: A$10,000 at the 30 Nov 2026 decision; candidates T with the lottery filter; n = min(18, floor(account ÷ 550)); buys; clock; IBKR costs), with one change:

- **Rule L4-H6 (sell).** A holding is sold in full at a month-end decision only if it is **not on T and has been held for six or more month-end decisions since its purchase decision** (the purchase decision counts as zero). A holding off T before that is kept and re-tested at each decision. **Exceptions, sold at once whatever the holding period:** a holding flagged `BID_PEG`; a payout arrives as cash. No trims, no top-ups, no stop-loss.

Books: `EMG2_18_SIM_H6`; 100 random twins `EMG2_18_H6_RND_s001…s100` (seeds 8760000 + i; the twin applies the same hold rule to its random list). Fills at the next session's close at rule L9 costs.

## 3. Reading (report 88 section 4.3; replaces the draft's section 3)
Reported monthly beside `EMG2_18_SIM`:
- **Fact:** orders and brokerage paid to date by each book, and the brokerage saved by H6.
- **Mostly luck, and labelled so:** value; the gap `EMG2_18_SIM_H6 − EMG2_18_SIM` after costs (over 68 quarterly starts the 12-month gap had a standard deviation of about 15 points, mean +6); percentile among its own 100 twins; holdings; worst fall.
- It is never evidence for or against EMG2.
- **No proposal to change the live book before the December 2028 review.** A proposal then needs both: (1) H6 not behind `EMG2_18_SIM` after costs over 24 months; and (2) a blind build that chose a minimum hold without being told to. Then an owner decision; no automatic change.
## 4. What is not changed
The live book, its loss limits (L11), approval rules (L8), stop rules (L12), the capital cap and the gate. The A$100,000 and A$25,000 paper books of `AMENDMENT_shadow_EMG2.md`.

## 5. Evidence (report 87, `scratchpad/deep87/out/post_b.log`)
| 2018–Oct 2026, A$10,000, after costs and tax | Registered rules | With 6-month hold |
|---|---|---|
| Research panel: return a year; mean of 12 starts; worst fall | 11.3%; 12.5%; −48% | 14.2%; 14.1%; −49% |
| Vendor file: return a year; mean of 12 starts; worst fall | 9.2%; 10.2%; −47% | 9.5%; 9.3%; −43% |
| Orders a year; brokerage a year | 105–110; A$690–725 | 61; A$405 |
| Dec 2007–Dec 2017, research panel (run after the freeze) | −0.6% | +4.0% |

## 6. Trial count
The back-tests above are counted in report 87 (N 1,919). Registering the twin adds no trial.

## R. Paper-record implementation (record keeper's addition; mechanics only, no rule above is changed)
- Run by the paper code (`bigwins_forward/code/paper_emg2s.py`, called by `paper_daily.py` after `paper_emg2.py`), own state file `emg2s_state.json`; never reads or writes the H82 state or another line's state. Same month-end universe table as the EMG2 paper line (`paper_emg2.table` on the bundle of that month-end; band C, score, score percentile, T, `BID_PEG`, rule-7 payout after 20 sessions without a close). A month-end with an EMG2 data block is no decision and does not count as a month-end decision for the hold.
- Rules of `EMG2_18_SIM` as the paper code applies them: lottery class (FD §8.6) = fewer than 504 sessions since the first price row of the bundle, close (on the day or within 5 sessions) under A$0.20, or `tv_med63` under A$250,000; n = min(18, floor(NAV ÷ 550)), parcel = NAV ÷ n; buy cash = cash + estimated sell proceeds − A$50, shared equally when it is less than the parcels; an order under A$500 is not sent; whole shares at the decision close; fills at the next session's close; IBKR max(A$6.60, 0.088%) a trade; half-spread 0.50% a side with the half-price-step floor (L9 start value); a buy that the fill-day cash cannot cover is cut to whole shares that fit and dropped if under A$500. No canary, no approvals, no IBKR paper mirror (those belong to the live system).
- A same-engine reference book `EMG2_18_REF` (registered sell rule L4, no twins) runs beside the two twins so that H6 − REF and COMBO − H6 are measured inside one engine; the trading system's `EMG2_18_SIM` stays the registered comparison. Values are recorded every session (worst fall on daily values).
