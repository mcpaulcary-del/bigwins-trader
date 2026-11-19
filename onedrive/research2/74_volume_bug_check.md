# 74. Does report 73's split-volume error touch the live Big Wins engine (v1.3, H82)?

17 November 2026. Research and paper only. General information, not financial advice. Nothing here places an order.
Work folder: `scratchpad/vbug/` (`ev.py`, `events.csv`, `patched.py`, `bt.py`, `bt_base.json`, `bt_fix.json`, `picks.py`, `picks.pkl`, `uni_*.pkl`). The frozen rules file (`67_FINAL_RULES_v1.3.md`, SHA-256 b38abcd7…) and the paper code were not edited; the correction was applied by loading `bw13_prep.py` with one line replaced in memory.

## 0. Verdict

1. **The error is present in the AU data and in the v1.3 code.** EODHD's AU `volume` is split-adjusted to the download date; its AU `close` is raw. v1.3 A5 and `bw13_prep.py` (`TV = (C * VOL)`) multiply the raw close by that adjusted volume. Before a consolidation of ratio s (new/old, s < 1) a day's traded value is understated by the factor s; before a split (s > 1) it is overstated by s. Rule A2's description of the volume as "as traded, not adjusted" is wrong.
2. **Back-test (unseen B, 29 Dec 2017–13 Nov 2026, A7(b), frozen engine).** Corrected traded value moves H82 from **8.27% / 9.96%** a year after costs (A$25k / A$100k) to **8.35% / 9.32%**. After tax A: 6.95 / 7.47 → 6.45 / 6.99. Index comparator unchanged at 8.78 after costs, 6.84 after tax A. The error flattered the engine by about 0.5 point a year after tax at both sizes, and by 0.6 point after costs at A$100,000. The excess over the comparator at A$100,000 falls from +1.5 to +0.9 points a year (t 0.49 → 0.30). The A$25,000 account still trails the comparator after costs. Report 67's verdict (not shown to beat the index) is unchanged; the case is weaker.
3. **Paper record, 16 Nov 2026 decision.** None of the 300 universe companies changes. Four change traded-value rank inside the 300 (PDI 243 → 123, LOT 262 → 252, AMC 58 → 55, SSM 237 → 239), and their neighbours shift by one place. Scores and score order do not change. **The A$5k, A$25k and A$100k pick lists are identical** (4, 10 and 30 names), and no pick crosses the rank-100 spread boundary, so the 17 Nov fills and their costs are not affected. In ranks 301–1000 (H100/H101 territory) 33 companies change value, some by large amounts (KAN 729 → 402, CEL 790 → 430).
4. **Recommendation.** Correct it from the 31 Dec 2026 review (draft amendment `68_forward_record/AMENDMENT_v1.4_traded_value.md`). Keep the 16 Nov orders and fills as booked; they would be the same under the correction. Quote the corrected back-test (8.3% / 9.3% after costs; 6.4% / 7.0% after tax A) wherever report 67's figures are cited. Real money stays in the 40/60 plan.
5. **Trial count.** One corrected re-run of the frozen H82 rule on used data: **N = 951**. The paper-record check is a data check, not a trial.

## 1. What the code multiplies

| Place | Close | Volume | Adjustment |
|---|---|---|---|
| v1.3 A2 | "eod … close, volume — as traded, not adjusted" | same | text claims neither is adjusted |
| v1.3 A5 | "Traded value of a day = raw close × volume" | vendor volume | none |
| `data_foundation/code/eodhd/build_tr.py` (called by `pipeline.py build`) | `close` passed through raw; A3's ratio enters only `ret_pr`/`ret_tr` | `volume` passed through as downloaded | none to either column |
| `bigwins_forward/code/bw13_prep.py` line 105 | `C` = raw close pivot | `VOL` = vendor volume pivot | `TV = (C * VOL)`; the median of TV over 252 days ranks the universe (B1), sets buy eligibility (B6 ≥ 100 × T) and the E2 spread tier |
| `bigwins_forward/code/paper_lib.py` | takes `medval`/`vrank` from the bw13 bundle; its own `vol` from the daily bulk file is read but not used for ranking | — | none |

`pipeline.py` itself only dispatches download/build; the arithmetic is in `build_tr.py` and `bw13_prep.py`. The forward store (`bigwins_forward/data/eodhd/panel_tr.pkl.gz`) is built the same way.

## 2. Is AU volume split-adjusted? (empirical)

`panel_tr.pkl` (download to 16 Nov 2026), Common Stock with three-letter codes, vendor-listed splits/consolidations dated 2018–2026: 1,373 listed events, 726 with |ln s| ≥ ln 1.5 and 40 rows each side (690 consolidations, 36 splits). Median over 40 rows after ÷ median over 40 rows before, expressed as an exponent of s:

| Events | n | Close jumps by | Volume jumps by | Raw close × volume jumps by |
|---|---|---|---|---|
| A3 applied (the vendor close is raw at the event) | 597 | s^−0.99 | s^−0.03 | **s^−1.00** |
| A3 not applied (the vendor close already adjusted) | 129 | s^0.00 | s^0.57 (mixed) | s^0.41 |

If the volume were raw it would jump by s^+1 at the event and traded value would be continuous. It does not: in the 597 events where the close is raw, the volume is continuous (233 within ±0.3 of 0; only 17 look like raw volume), and traded value jumps by the full 1/s. So the vendor's AU volume is split-adjusted. ASX events are 95% consolidations, so the usual effect is that a company that **later** consolidates looks less traded before the event than it was.

Live check against the API (`eod/PDI.AU`, `splits/PDI.AU`): PDI's 1-for-5 consolidation is listed for 26 Aug 2026. The close goes 0.89 → 4.475 on 21→24 Aug, while volume stays at 1–5 million shares a day on both sides, and raw close × volume goes from about A$1–4m to A$6–10m. The pre-event volume has been divided by 5.

For events A3 does not apply, the vendor close is already in new-share units, so raw close × adjusted volume is already consistent there. The correction below leaves those days unchanged.

## 3. The correction

Corrected traded value = P(d) × vendor volume(d), where P is v1.3's own adjusted close (A5, price-only, from A3's applied ratios). Because P(d) = raw close(d) ÷ F(d), with F(d) the product of the A3-applied ratios dated after d up to the file's end, this equals raw close × volume ÷ F, the same as report 73's rule T1. It also equals "raw close × raw volume". In code it is a one-line change in `bw13_prep.py`: `TV = (C * VOL)` → `TV = (P * VOL)`. Applied in memory only (`vbug/patched.py`).

## 4. Impact on the H82 back-test (unseen B, source E, A7(b))

The baseline re-run reproduces report 67 §S3 exactly (8.273 / 9.959).

| % a year | A$25k as frozen | A$25k corrected | A$100k as frozen | A$100k corrected | Comparator (J) |
|---|---|---|---|---|---|
| Before costs | 9.75 | 9.39 | 10.81 | 10.31 | — |
| **After costs** | **8.27** | **8.35** | **9.96** | **9.32** | 8.78 |
| After tax A | 6.95 | 6.45 | 7.47 | 6.99 | 6.84 |
| After tax B | 6.32 | 5.59 | 6.47 | 6.12 | 6.21 |
| Excess a year (t) | +0.1 (0.03) | +0.3 (0.07) | +1.5 (0.49) | +0.9 (0.30) | — |
| Max drawdown | −26.4 | −25.1 | −25.0 | −25.8 | −26.8 |
| Turnover | 0.85 | 0.85 | 0.80 | 0.80 | — |

**Universe.** The universe differs at 105 of 107 month-ends, by a mean of 6.9 of 300 companies (median 6, at most 14). The names most often added by the correction (AEL, ELV, MYX, VAU, IMU, AMA, SXL, LOT) are companies that later consolidated and so had been ranked too low. The names most often removed (PPH, AEF, TTT, IMD, WGB, DXI, MFF) had been ranked too high, mostly ahead of later share splits, which were often winners: the same look-ahead as the US case. On ASX the two directions partly offset, so the effect (−0.4 to −0.7 point a year) is far smaller than the US +10.9 → −1.2.

Not re-run: the frozen-A7(a) figures (9.61 / 9.75), source V (panel_v2 `val`, a different vendor and not affected by this EODHD field), the H100 June sleeve (part N, which uses ranks > 300 and median value ≥ A$50,000, so it is affected by the same error) and the G7 random control.

## 5. Impact on the paper record (decision 16 Nov 2026, forward store, A7(b))

The recomputation with the frozen code reproduces the recorded `targets_2026-11-16.csv` exactly for all three books.

| | As recorded | Corrected |
|---|---|---|
| Universe (300) membership | — | 0 in, 0 out |
| Traded-value rank changes inside 300 | — | 4 real (PDI 243→123, LOT 262→252, AMC 58→55, SSM 237→239); about 130 neighbours shift ±1 |
| A$5k book (n = 4) | QBE RHC CPU WOW | identical |
| A$25k book (n = 10) | + ANN FPH ALL CGF APA ASX | identical |
| A$100k book (n = 30) | + SOL IAG SUN DTL ANZ EVT MPL REH CWY STO BGA ARG CSL SDF CCP BOQ OML TWE ORG DDR | identical |
| Picks crossing the rank-100 spread tier | — | none (DTL, REH, BGA, ARG, CCP, DDR move one place, all stay within 101–300) |
| Ranks 301–1000 (H101 line) | — | 33 companies change value; 12 leave the 1,000-table and others enter |

The 16 Nov orders (filled at the 17 Nov close) stand. They are what the corrected rule would also have chosen. The error will matter again forward whenever a consolidation or split falls inside a company's trailing 252 days, which on ASX is several companies near the 300 boundary at most month-ends (§4: about 7 a month).

## 6. Caveats

- The volume behaviour was measured on events with clean 40-day windows; around 20% of A3-applied events show volume jumps that are neither 0 nor 1 (liquidity changes at consolidations). The median, the live API check and the traded-value jump of exactly s^−1 leave no doubt about the sign.
- The vendor adjusts volume to the date of the download. A back-test file and a forward file downloaded on different days can disagree for an event between the downloads. The P × volume form is right as long as P and the volume come from the same download, which Q2 already requires.
- One trial added (N = 951). Deflated Sharpe is ~0 at this N either way.
- Not replicated by a second agent.

## 7. Files

- `scratchpad/vbug/ev.py`, `events.csv`: event study of close/volume/traded value around 2018–2026 AU splits.
- `scratchpad/vbug/patched.py`: loads `bw13_prep.py` with `TV = (P * VOL)` in memory.
- `scratchpad/vbug/bt.py`, `bt_base.json`, `bt_fix.json`, `uni_base.pkl`, `uni_fix.pkl`: unseen-B re-run.
- `scratchpad/vbug/picks.py`, `picks.pkl`: 16 Nov decision as recorded and corrected.
- `68_forward_record/AMENDMENT_v1.4_traded_value.md`: draft correction, from the 31 Dec 2026 review.
