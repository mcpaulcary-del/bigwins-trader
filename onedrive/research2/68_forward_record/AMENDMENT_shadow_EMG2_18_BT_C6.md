# Amendment: paper line `EMG2_18_SIM_BT_C6` (registered EMG2-18 with the band-trend switch; a holding is sold only after six months and only when out of the top 40%)

Status: **REGISTERED 20 Nov 2026 — PAPER ONLY, information only**, by the record keeper, before the first decision it governs (Mon 30 Nov 2026), on report 99 (`99_emg2_low_turnover_fable.md`, SHA-256 0f703985...), report 100 (`100_is_low_turnover_better_fable.md`, SHA-256 1795c501...) and the owner's decision of 20 Nov 2026 (`OWNER_DECISIONS_2026-11-19.md`, section "Live sell rule switched to C6": the live book adopts C6 and the current rule keeps running on paper beside it). Text below is the research agent's (Fable) draft `deep99/AMENDMENT_shadow_EMG2_18_BT_C6.DRAFT.md` (SHA-256 a6a22b9a2ba39cb9b4c8148e89ab368a0f03b452ea4f4ace7b281511e3a2fabd) unchanged except this status line, the title, the record keeper's notes to sections 2, 3 and 4 and the added section R. It changes nothing in `AMENDMENT_shadow_EMG2_18_BT.md` (and its leftover amendment), `AMENDMENT_shadow_EMG2_18_H6.md` or `AMENDMENT_shadow_EMG2_COMBO.md`. The AI never places trades.

## 1. Why
Trading is the live book's one certain cost: in the replay the protected book sends about 88–90 orders a year, A$505–516 of brokerage and A$430–470 of modelled spread on A$10,000. Report 99 chose a lower-turnover rule on five overseas markets and judged it once on the ASX. It sent 56–60 orders a year (brokerage A$334–356) and ended A$6,200–6,900 higher than the registered protected book on both ASX data sets, ahead from all 12 start months. About A$2,400–2,900 of that is saved brokerage and spread; the rest is which shares it happened to keep (most of it in 2019 and 2025) and is not evidence. The rule is the registered COMBO paper rule (L4-C) put under the registered switch (BT1–BT4); no new parameter.

## 2. Rules
Everything as `EMG2_18_SIM_BT` (rules BT1–BT4, BT3a/BT3b for a leftover share, section R; same start, capital, band C, target list T, lottery filter, n = min(18, floor(account ÷ 550)), clock, IBKR costs), with one change in state ON:

- **Rule L4-C (sell), as in `AMENDMENT_shadow_EMG2_COMBO.md`.** A holding is sold in full at a month-end decision only if **both**: (a) it has been held for six or more month-end decisions since its purchase decision (the purchase decision counts as zero); and (b) its score percentile in band C is 0.60 or lower, or it is no longer in band C, or it has left the eligible set. Exceptions, sold at once: a holding flagged `BID_PEG`; a payout arrives as cash.
- **The switch overrides the hold.** At an OFF decision every share is sold (BT3) whatever its holding period. After the switch turns ON the book buys from T as registered and the six months start again.
- Buying is unchanged (T = top fifth, lottery filter, best first, while fewer than n names are held).

Books: `EMG2_18_SIM_BT_C6`; 100 random twins `EMG2_18_BT_C6_RND_s001...s100` (seeds **8810000 + i**, assigned by the record keeper; same switch state, same sell rule on the random list).

*Record keeper's note to section 2:* "six or more month-end decisions since its purchase decision" is counted as the frozen engine counts it (`deep99/code/eng99.py` via `acct3` `months_held` = month-ends since the purchase decision): every month-end session counts, a month-end with a data block included (section R). This differs on purpose from `AMENDMENT_shadow_EMG2_COMBO.md` section R (which skips data-block month-ends) so that the paper line and the live book (`AMENDMENT_live_EMG2_18_C6.md` L4-C6.1, where the paper book's L6-skipped start month-end must count like its twin's) use one count.

## 3. Reading
Reported monthly beside `EMG2_18_SIM_BT`:
- **Fact:** orders, brokerage and modelled spread paid to date by each book, and the saving.
- **Mostly luck, labelled so:** value; `BT_C6 − BT` after costs; percentile among its twins; worst fall.
- *Record keeper's note:* superseded for the live book by the owner's decision of 20 Nov 2026 (`AMENDMENT_live_EMG2_18_C6.md`, registered just before this file): the live book uses C6, and `EMG2_18_SIM_BT` (rule L4 under the switch) keeps running on paper as the comparison. This line stays the record's clean, same-engine reading of C6; the conditions below are kept as written and are now the test for **keeping** C6 live at the December 2027 review.
- **No live proposal before the December 2027 review.** A proposal then needs: (1) BT_C6 not behind `EMG2_18_SIM_BT` after costs over at least 12 months of paper; (2) at least 30% fewer orders in the paper record; (3) the live book's measured spread no more than 1.5 times the model; (4) a new pre-registered test. Then an owner decision.

## 4. What is not changed
The live book (rules L1–L15), its loss rule, approvals, stop rules, capital cap and the gate.

*Record keeper's note:* the live book's sell rule is changed separately by the owner (`AMENDMENT_live_EMG2_18_C6.md`); this paper line does not depend on it and is run whatever the live book does.

## 5. Evidence (report 99; `scratchpad/deep99/out/readj_panel.log`, `readj_vendor.log`, `design_read.log`)
| 2018–Nov 2026, A$10,000, mean of 12 starts, after IBKR tiered brokerage, spread and tax | `EMG2-18_BT` (registered, corrected engine) | With L4-C |
|---|---|---|
| Research panel: ends with; worst fall; lowest value | A$28,277; −46%; A$5,769 | A$34,520; −51%; A$6,342 |
| Vendor file: ends with; worst fall; lowest value | A$23,927; −53%; A$5,890 | A$30,795; −42%; A$7,377 |
| Orders a year; brokerage; spread (panel / vendor) | 88 / 90; A$505 / 516; A$472 / 427 | 56 / 60; A$334 / 356; A$321 / 313 |
| Value at Dec 2025 (panel / vendor) | A$28,743 / 24,223 | A$33,022 / 27,857 |
| Five best holdings removed (panel / vendor) | A$21,716 / 17,220 | A$27,534 / 24,381 |
| Random twins beaten (panel / vendor) | 100 / 99 (report 98) | 100 / 100 |
| Dec 2005–Dec 2017, research panel | A$11,819 | A$22,746 |
| Overseas design (8 market-versions): median orders; more money than the reference in | 86 | 55; 6 of 8 (Taiwan rank: A$21,377 against A$42,985) |

Caveats: both parts (six-month hold, top-40% keep zone) had been seen on ASX 2018–2026 before this test (reports 87, 90); the overseas choice did not survive leaving one market out; the same change on the PAIR's EMG2 half lost A$3,000–5,700.

## 6. Trial count
Counted in report 99 (N 2,928). Registering the line adds no trial.

## R. Paper-record implementation (record keeper's addition; mechanics only, no rule above is changed)
- Run by `bigwins_forward/code/paper_emg2bt6.py`, called by `paper_daily.py` right after `paper_emg2bt.py` (same bundle, same day), own state file `emg2bt6_state.json`; never reads or writes the H82 state or another line's state (reads `emg2bt_state.json` read-only for the `BT_C6 − BT` reading of the scorecard). Everything as `paper_emg2bt.py` (seq 72, 76): BT1/BT2 `band_trend` on the decision bundle (the same function; one state computed per line), BT3 OFF sells and the fund buy / 10% top-up, BT3a/BT3b leftover sale and fund sweep on non-month-end sessions of state OFF, BT4, fills at the next close, IBKR max(A$6.60, 0.088%), half-spread 0.50% a side for shares and 0.05% for A200, payout after 20 sessions without a close, A7 code changes, splits and dividends as cash. Same month-end table (`paper_emg2.table`), lottery class and sizing as `EMG2_18_REF` / `EMG2_18_SIM_COMBO` of `paper_emg2s.py`.
- **Age (section 2 (a)).** The line counts month-end sessions from its start: at every month-end session on or after 30 Nov 2026 the counter `me` goes up by one before anything is decided, whether the session is a decision or a data block (EMG2 data block, or no A200 close). A share bought by the decision at counter value m has age `me − m` at a later decision (purchase = 0); ripe at 6.
- **Sell in state ON (section 2).** `paper_emg2s.decide` with rule L4-C (keep zone K = band-C members with score percentile above 0.60; a twin's K = band-C members whose persistent seeded random score, redrawn with probability 0.2 a month, has a percentile above 0.60; `BID_PEG` sold at once; payout as cash), with the age above. The fund is always sold at an ON decision (BT4) whatever its age: the code marks the fund holding as ripe before the call, and the sale is labelled `BT4 ON: fund sold`; its value then funds the buys of the same decision as any sale.
- **State OFF:** exactly `paper_emg2bt.py` (every share sold whatever its age; the switch overrides the hold).
- Orders `shadow/emg2bt6_orders_<d>.csv`, levels `shadow/emg2bt6_band_<d>.csv` (identical to `emg2bt_band_<d>.csv`), sweep orders `shadow/emg2bt6_sweep_<d>.csv`; ledger block `emg2bt6` of each daily entry; scorecard row after `EMG2_18_SIM_BT` with the facts (orders, brokerage, modelled spread, saving against `EMG2_18_SIM_BT`) and, labelled mostly luck, value, `BT_C6 − BT`, percentile among its twins, worst fall.
