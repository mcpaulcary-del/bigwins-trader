# Amendment (erratum): report 96's EMG2-18_BT replay figures rested on an engine fault

Status: **REGISTERED 20 Nov 2026 — erratum only**, by the record keeper, on report 98 (`98_protection_blind3_pair_fable.md`, section 1 item 2 and section 4) and the owner's re-confirmation (`OWNER_DECISIONS_2026-11-19.md`, last section "Protection re-confirmed on corrected figures (report 98), 20 Nov 2026"). Hashed (SHA-256) and appended to `LEDGER.jsonl`. **No rule, book, threshold, decision or code changes.** The original files are not edited: `96_emg2_drawdown_fix_fable.md`, `AMENDMENT_shadow_EMG2_18_BT.md` (ledger seq 70) and `AMENDMENT_live_EMG2_18_BT.md` (seq 71) stay byte-identical; this erratum is read alongside them. Paper record only. The AI never places trades.

## 1. What is wrong
Report 96's replay engine (`deep96/code/eng96.py`, the band trend → fund rule) allowed the book only one holding, the fund, at an OFF decision. When a share could not be sold on the step-aside day (no trade for five sessions; usually a takeover suspension), that leftover counted as the one holding, the fund order was refused and the whole book waited in cash until the next month-end. The registered rule (BT3) says the money goes into the fund at the next close. It happened in June 2018 (VLA), February 2020 (QMS, WBA) and September 2023 for the Dec-2017 book; every start month held the stuck shares, so all 12 starts had the February 2020 accident, on both data sets. The replayed book sat in cash through the March 2020 crash and bought the fund on 1 April 2020 (11,740) instead of 2 March (14,157). That one month is the whole of the A$2,400–2,700 lead report 96 gave the switch over plain EMG2-18, and most of its smaller worst fall. Two independent codings of the rule as written agree (Dec-2017 start, panel: A$26,875 / A$26,988, worst fall −46.6% / −46.5%; the report 96 replay gives A$29,254 / −32.2%).

## 2. Where the figures appear (not edited; read with this erratum)
| File (SHA-256 at registration in the ledger entry) | Place | Text affected |
|---|---|---|
| `96_emg2_drawdown_fix_fable.md` | section 1, table (lines 16–20) and the "Why it still fails the bar" item; section 3 table row "Band trend → fund (sibling)" (line 64) | A$30,485 / A$26,443; −32% / −40%; Dec 2025 A$30,980; give-back A$7,272; "A$4,000 behind" |
| `68_forward_record/AMENDMENT_shadow_EMG2_18_BT.md` | section 1 (line 6); section 5 table (lines 30–32) | the same figures; "with a worst fall of −32% / −40%" |
| `68_forward_record/AMENDMENT_live_EMG2_18_BT.md` | section 1 item 1 (line 7) | "up to December 2025 it was about A$4,000 (12%) behind" |

## 3. Replacement figures (report 98, rule as written; A$10,000, mean of 12 starts Dec 2017–Nov 2018, to Nov 2026, IBKR costs and tax)
| EMG2-18 | Plain (unchanged) | Report 96 replay (faulty) | **Protection as written** |
|---|---|---|---|
| Ends with, research panel | A$28,067 | A$30,485 | **A$28,277** |
| Ends with, vendor file | A$23,731 | A$26,443 | **A$23,927** |
| Worst fall (panel / vendor) | −56% / −58% | −32% / −40% | **−46% / −53%** |
| Value at Dec 2025 (panel / vendor) | A$35,028 / A$31,254 | A$30,980 / A$26,744 | **A$28,743 / A$24,223** |
| Given back from peak to today (panel) | A$16,255 | A$7,272 | **A$6,783** |
| Orders; brokerage a year | 110; A$613 | 89; A$517 | **88; A$505** |

Read: the switch, correctly run, ends with about the same money as plain EMG2-18 (A$210 / A$196 more), with a worst fall 5 to 10 points shallower (not 18 to 24); it still halves the 2026 give-back; at December 2025 it was **A$6,285 (18%) / A$7,031 (22%) behind** (not "about A$4,000, 12%"). With the corrected rule the Dec-2017 book's lowest value is A$5,769 (panel, March 2020), below the A$6,000 step of the staged loss rule L11 (replay: A$7,289). Also corrected: five best holdings removed 21,716 (17,220) in place of 23,306 (19,276); spread doubled 24,327 (20,864) in place of 25,974 (22,362); January 2020 start 28,633 in place of 31,184. Not affected: plain EMG2-18, report 96's "to cash" versions, the 2006–2017 figures (A$11,819; no share was stuck at an exit) and every BLIND3/PAIR figure of report 98.

## 4. Decisions
- Report 96's verdict stands and is stronger: its bar was not met.
- The owner was shown these figures and chose to **keep** the protection for the live book (`OWNER_DECISIONS_2026-11-19.md`, last section; SHA-256 in the ledger entry). Rule L15 and the paper line `EMG2_18_SIM_BT` are unchanged. The trading system's handling of a share that cannot be sold on a switch day is its build decision BF-D34 (buy the fund with the cash available; sell the leftover when it trades and put the proceeds in the fund); `GO_LIVE_GUIDE.md` line 418.
- The paper line's code (`bigwins_forward/code/paper_emg2bt.py`, SHA-256 de2df2fb..., seq 72) was checked for the same fault: it does **not** have it (no holdings cap at an OFF decision; the fund is bought at the next close with the cash after the sales that filled; a share without a close is decided again at the next month-end, as its section R says). No code change.

## 5. Trial count
The corrected run is counted in report 98 (1 of its 26; ledger seq 73, N 2,909). This erratum adds no trial.
