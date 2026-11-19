# Amendment (erratum): report 85's 2010–2017 EMG2 back-test figures are not to be quoted

Status: **REGISTERED 19 Nov 2026 — erratum only**, by the record keeper, on reports 87 (section 1 and section 6 item 5), 88 (section 5 item 2) and 90 (section 4 item 2). Hashed (SHA-256) and appended to `LEDGER.jsonl`. **No rule, book, threshold, decision or code changes.** The original files are not edited: `85_full_review_and_direction_fable.md`, `FD_v3.0_BigWins.md` and `AMENDMENT_shadow_EMG2.md` (ledger seq 36) stay byte-identical; this erratum is read alongside them. Paper record only. The AI never places trades.

## 1. What is wrong
Report 85 (test T6, "2010–2017, printed, not used for choice") gave EMG2 (ranks 301–600, monthly refresh, A$100,000, A$0 brokerage) **11.0% a year after spreads and yearly tax against 7.4%** for the index, worst fall **−57%**, from the vendor (EODHD) file. Two faults were found in report 87:
1. The vendor file holds almost no company that ended before 2017 (89 of 3,769 companies): the 2010–2017 period has survivorship bias.
2. It has glitch closes of **A$0.0001** (AUR, LNR, AUC, AAU in 2011), which the back-test charged as a 500% spread.

The **2018–Oct 2026** return reproduces: 13.3% (report 85, vendor file) against 13.1% on the research panel (report 87), with dead companies included. The worst fall for that period on the research panel is −45% (report 85 printed −38%).

## 2. Where the unreliable figures appear (not edited; read with this erratum)
| File (SHA-256 at registration in the ledger entry) | Place | Text affected |
|---|---|---|
| `FD_v3.0_BigWins.md` | line 91 (section 1.5, row "EMG2") | "11.0% against 7.4% (2010–2017)" |
| `FD_v3.0_BigWins.md` | line 92 (section 1.5, row "EMG2 ride") | "worst falls 38% and 57% in back-test" |
| `FD_v3.0_BigWins.md` | line 579 (section 10.2, BW-RSK-20) | "50% for EMG2 and EARLY (back-test worst 38% and 57%)" — the **50% setting itself stands** (report 88: still reasonable); only the cited figures are replaced |
| `68_forward_record/AMENDMENT_shadow_EMG2.md` | status/evidence paragraph (line 8) | "(11.0% against 7.4% in 2010–2017)" and "worst falls 38% and 57%" |
| `85_full_review_and_direction_fable.md` | section 0 item 4; section 1.4 T6 table, row "2010–2017" | the same figures |

## 3. Replacement figures (research panel, dead companies included; A$100,000; no brokerage; spreads and yearly tax; report 87)
| Period | EMG2 a year after tax | Index | Worst fall |
|---|---|---|---|
| 2010–2017 | **17.6%** | 7.4% | **−40%** |
| 2018–Oct 2026 | **13.1%** | 8.5% | **−45%** |

Read the 2010–2017 figure with care as well: before 2018 band C held only 61–149 eligible companies (report 87). These are back-tests on data seen before; they are not evidence of a forward edge and do not change EMG2's status (paper lead challenger, not adopted on evidence). The within-band signal spread was also re-measured on the panel in report 87 (best fifth minus band: 2.1 points a month before 2018, t 5.4; 1.8 after, t 4.8, before costs); report 85's 2010–2017 band-spread figures (+26.7, t 3.5) came from the same vendor file and should be read with the same caution, although the reviewers' erratum names only the book figures.

## 4. Trial count
No new run. The panel figures are report 87's, already counted (N 1,919 at report 87; 2,192 now). No change to N.
