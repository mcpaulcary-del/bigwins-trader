# Amendment: paper line `EMG2_18_SIM_BT` (registered EMG2-18 with a band-trend switch into the ASX 200 fund)

Status: **REGISTERED 19 Nov 2026 — PAPER ONLY, information only**, by the record keeper, before the first decision it governs (Mon 30 Nov 2026), on report 96 (`96_emg2_drawdown_fix_fable.md`, SHA-256 5893fd09...) and the owner's decision of the same day (`OWNER_DECISIONS_2026-11-19.md`, section "Live start with the band-trend protection"). Text below is the research agent's (Fable) draft `deep96/AMENDMENT_shadow_EMG2_18_BT.DRAFT.md` (SHA-256 921ea64fd531e324b4554c5116bad03fd99d088514b25163daec6941be1b71b9) unchanged except this status line, the title, the note to section 4 and the added section R. This paper line keeps its 100 random twins and is the record's own reference for the live book's switch. **Note to the draft's sentences "It changes nothing in `AMENDMENT_live_EMG2_18.md`" and "It is not a live amendment":** they remain true of THIS amendment; the owner has separately adopted the same switch for the live book, registered as `AMENDMENT_live_EMG2_18_BT.md` (owner override of report 96's failed bar). The AI never places trades.

## 1. Why
The registered book gave back about A$16,000 of a A$42,000 peak in 2026 because the whole 301–600 band fell. Report 96 designed step-aside rules on overseas markets only and judged them once on the ASX. One rule ended with more money than the registered rules on both ASX data sets (A$30,485 v A$28,067; A$26,443 v A$23,731; ahead from all 12 start months) with a worst fall of −32% / −40% against −56% / −58%. It was A$4,000 behind at December 2025 and it was the sibling of the rule the design chose, so it is recorded on paper, not traded.

## 2. Rules
Everything as `EMG2_18_SIM` (same start, capital, candidate list T, lottery filter, n = min(18, floor(account ÷ 550)), clock, IBKR costs), plus:

- **BT1 (band index).** At each month-end decision compute the equal-weight total-return index of the eligible names in traded-value ranks 301–600 (the rule's own band C, re-formed at each month-end, buy-and-hold inside the month).
- **BT2 (state).** ON if the index is at or above the mean of its last 10 month-end levels, this month-end included; otherwise OFF. With fewer than 10 levels the state is ON.
- **BT3 (OFF).** Sell every share at the next close and put the account (less the A$50 reserve) in the ASX 200 fund used as the benchmark. Buy no shares.
- **BT4 (ON).** Sell the fund at the next close and run the registered rules.
- No other change: no stops, no intra-month action.

Books: `EMG2_18_SIM_BT`; 100 random twins (same switch, random list). The state ON/OFF is printed in the monthly report beside the live book.

## 3. Reading
Reported monthly beside `EMG2_18_SIM`: value, state, days out, worst fall, give-back from peak, percentile among its twins, and the difference `BT − SIM` after costs and tax. It is never evidence for or against EMG2. **Review at the December 2027 review** and after any fall of 20% or more in the registered book: a live proposal would need a new pre-registered test; a paper lead alone does not make one.

## 4. What is not changed
The live book, its loss limits, approval rules, stop rules, the capital cap and the gate.

*Record keeper's note:* the live book's switch is registered separately (`AMENDMENT_live_EMG2_18_BT.md`, owner decision); this paper line does not depend on it and is run whatever the live book does.

## 5. Evidence (report 96, `scratchpad/deep96/out/readjM_panel.log`, `readjM_vendor.log`, `evt_panel.log`)
| 2018–Nov 2026, A$10,000, 12 starts, after costs and tax | Registered | Band trend → fund |
|---|---|---|
| Research panel: ends with; worst fall | A$28,067; −56% | A$30,485; −32% |
| Vendor file: ends with; worst fall | A$23,731; −58% | A$26,443; −40% |
| Value at Dec 2025 (panel / vendor) | A$35,028 / A$31,254 | A$30,980 / A$26,744 |
| Orders a year; brokerage a year | 110; A$613 | 89; A$517 |
| Dec 2005–Dec 2017, research panel | A$12,128; −44% | A$11,819; −59% |

## 6. Trial count
The back-tests are counted in report 96 (N 2,883). Registering the line adds no trial.

## R. Paper-record implementation (record keeper's addition; mechanics only, no rule above is changed)
- Run by `bigwins_forward/code/paper_emg2bt.py`, called by `paper_daily.py` after `paper_emg2s.py` (and in its catch-up line), own state file `emg2bt_state.json`; never reads or writes the H82 state or another line's state. Same month-end bundle as the EMG2 line (`paper_emg2.get_bundle`), same table (`paper_emg2.table`), same lottery class and same rules and costs as `EMG2_18_REF` of `paper_emg2s.py` (section R of `AMENDMENT_shadow_EMG2_18_H6.md`; its `decide` is called unchanged in the ON state). A month-end with an EMG2 data block is no decision: holdings and state are kept.
- **BT1 as computed.** At the decision month-end d the bundle of d is cut at each of the last 10 month-ends m (last session of each calendar month in the bundle, d included); band C(m) = `paper_emg2.table(bundle cut at m, class rule of d)['C']` (the eligible names of traded-value ranks 301–600; class rule of the decision date, so all 10 levels use the rules in force at d; traded value on the convention of d's bundle). Daily total-return index per name as in `table` (A3/A6: (close + dividend) / previous close on adjusted closes, forward-filled over days without a close). Level(m_next) = Level(m) × mean over C(m) of TR(m_next) / TR(m) (equal weight at m, buy-and-hold to the next month-end; an empty band = no change). The first of the 10 levels is 1; the test is scale-free. All 10 levels come from the bundle's history, so the state is defined from the first decision (the draft's "fewer than 10 levels = ON" applies only if the bundle is shorter).
- **BT2.** ON iff Level(d) >= mean of the 10 levels (d included). Levels, means, member counts and the state are written to `shadow/emg2bt_band_<d>.csv` and the ledger.
- **BT3 (OFF).** Every share holding is sold at the next session's close (L9 costs); no share is bought. The fund (A200, the benchmark fund of the paper record) is bought at the same close with the cash after the sales, less the A$50 reserve, in whole units, IBKR max(A$6.60, 0.088%), half-spread 0.05% a side (report 96's fund model), the A$500 minimum applies. At a later OFF month-end the fund is topped up only if cash less reserve is at least 10% of the account and at least A$500 (report 96's 10% band); payouts and dividends otherwise stay as cash. A share sale not filled (no close) is decided again at the next month-end, as for every paper twin.
- **BT4 (ON).** The fund holding is not on T, so the registered sell rule L4 sells it at the next close (fund costs as above); the registered buys use the estimated proceeds as for any sale.
- Books: `EMG2_18_SIM_BT`; 100 random twins `EMG2_18_BT_RND_s001…s100` (seeds 8780000 + i; random list as the other EMG2-18 paper twins: persistent seeded score over band C, redrawn p = 0.2 a month), all on the same state. Fills at the next session's close. No tax is modelled by the paper engine (as for `EMG2_18_REF`); the monthly reading states BT − REF after costs and the tax note of report 96.
- Reading in the scorecard every session: value, state, sessions out (state OFF), worst fall (daily), give-back from peak, percentile among its 100 twins, BT − `EMG2_18_REF` (same engine).
