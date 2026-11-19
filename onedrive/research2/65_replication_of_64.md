# 65. Independent replication of report 64 (rules v1.2)

16 Nov 2026. Work folder: `scratchpad/replication_64/` (`code/`, `out/`, `out_frozen/`). Every script was run with `python3 -I`.

**Rules used**

* `research2/64_FINAL_RULES_v1.2.md`.
* `research2/64_FINAL_RULES_v1.1_parts_A-H.md` (SHA-256 `1be57c4a3d79f940…b9a1`). The coordinator supplied this file part-way through, after the permission policy had blocked reading it at `bigwins2/out/`.

**Data and reference files read**

* `data_foundation/out` (`panel_v2_long.pkl`, `index_v2.pkl`, `calendar_dates.csv`, `eodhd/panel_tr.pkl`, the EODHD symbol lists).
* The input files the rules name:
  * `bigwins_lab/data/etp_list.txt`
  * `company_study/data/delist.pkl`
  * `company_study/data/asx/ASXListedCompanies.csv` (A5)
  * `actuals/data/derived/*`

**What I did not read**

* No `bigwins*/` code or output, apart from the ETP list the rules name.
* No `deepdive/` code.
* Not `64_algorithm_deep_dive.md`.

`deepdive/out/` result files were opened only after each set of results had been frozen (H100 at 10:04 UTC, H82 at 10:11 UTC).

## Verdicts

| Item | Verdict | Largest difference |
|---|---|---|
| **H82 dev 2001–2015**, v2 panel, A$25k and A$100k, December start | **REPLICATED** (exact) | 0.000 pt on every measure: CAGR before costs, after costs, after tax A and B; index; drawdown; excess; turnover |
| **M2 robust score**: 8 accounts (2 sizes × 4 start months) | **REPLICATED** (exact) | All 8 cells 0.000 pt. RS 5.235% against 5.235% |
| **H82 unseen A** (31 Dec 2015 – 31 May 2024), v2, G3 comparator | **REPLICATED** (exact) | 0.000 pt |
| **H82 unseen B** (29 Dec 2017 – 13 Nov 2026), EODHD total return, J comparator | **REPLICATED** | 0.04 pt (A$100k before costs). J comparator −0.04 pt; cause found (ambiguity 2) |
| H82 side runs in `p0_v2` and `p0_eod` (overlap, whole period, EODHD price-only) | REPLICATED | A$100k: at most 0.13 pt. Exception: one A$25k side run differs by up to 0.83 pt (see below) |
| Monthly holdings, A$100k overlap 2018–May 2024 (`p0_holdings_overlap_*.csv`) | REPLICATED | v2: 77 of 77 months identical (NAV identical to machine precision). EODHD: 76 of 77 identical |
| **H100 v2**, price only, 2002–2023 | **REPLICATED** | As frozen: no sign flip, 2010 +1.35 pt. With the v1.1 C1 record window: largest difference 0.15 pt |
| **H100 EODHD** with dividends against J1 TR, 2016–2026 | **REPLICATED** | No sign flip. Largest difference 0.13 pt |

No difference above 1.0 pt a year at A$100,000 remains, and no H100 year changes sign.

Not replicated, as these are optional for this check:

* K: the H88 and H90 challengers.
* L: the F1 tranche form.
* G7: the random-portfolio percentiles.
* G8: the deflated Sharpe ratio.

The v2 results agree with the builder's to floating-point precision, often in all 16 digits; for example, dev A$100k after costs is 0.06340983264968303 on both sides. That is what two faithful implementations of a fully specified deterministic rule set should produce. It also means the written rules leave no free choice that affects the v2 runs.

## Frozen hashes

Each `SHA256SUMS.txt` file was written before the matching builder file was opened.

* H100: `out_frozen/SHA256SUMS.txt`
  * `h100_v2.csv` `7a5d3f79…`
  * `h100_eod.csv` `4b4afaad…`
  * `h100.py` `a035bbb3…`
  * `prep.py` `041a67ed…`
* H82: `out_frozen/h82/SHA256SUMS.txt`
  * `h82_results.json` `f4c4cf98…`
  * `engine.py` `e9cb6e70…`
  * `signals.py` `74f5b878…`
  * `run_h82.py` `e41abd9a…`
  * month-end NAV and trade files for the 12 accounts
* Comparison step: `out_frozen/post_compare/SHA256SUMS.txt`
  * the side runs, the C1-window rerun of H100 and the comparison table
  * the engine with a holdings log added. Only that logging differs from the frozen engine; checked by diff.

## H82 results (mine; builder identical unless noted), % a year

| Account | Before costs | After costs | Tax A | Tax B | Index after costs / A / B | Max DD | Excess/yr |
|---|---|---|---|---|---|---|---|
| Dev A$25k | 10.62 | 9.74 | 7.99 | 6.70 | 3.27 / 2.83 / 2.37 | −51.0 | +6.42 |
| Dev A$100k | 6.71 | 6.34 | 5.61 | 4.90 | 3.27 / 2.83 / 2.37 | −52.6 | +3.09 |
| Unseen A A$25k | 2.89 | 1.63 | 1.09 | 0.74 | 4.58 / 3.94 / 3.27 | −30.1 | −2.27 |
| Unseen A A$100k | 4.90 | 3.99 | 3.10 | 2.33 | 4.58 / 3.94 / 3.27 | −26.9 | −0.27 |
| Unseen B A$25k | 9.96 | 9.61 | 7.24 | 6.58 | 8.73 / 6.81 / 6.18 (builder 8.78 / 6.84 / 6.21) | −22.9 | +1.43 (builder 1.40) |
| Unseen B A$100k | 10.49 (10.45) | 9.77 (9.75) | 7.55 (7.54) | 6.69 (6.69) | as above | −25.5 | +1.31 (1.25) |

M2 cells, after tax B:

| Start | A$25k | A$100k |
|---|---|---|
| Dec 2000 | 6.70 | 4.90 |
| Mar 2001 | 4.82 | 4.44 |
| Jun 2001 | 2.98 | 4.96 |
| Sep 2001 | 6.60 | 6.47 |

**Robust score: 5.235%**, identical to `stageBC.json` B0.

The full table is in `out/compare_h82.csv`.

## Differences found and their causes (explained from the rules text, not from builder code)

1. **H100 v2 2010 (+1.35 pt, frozen run).**
   * Pick WFL last traded on 30 Jun 2010. Its failure record (unpaid listing fees) is dated 30 Aug 2011, 14 months later.
   * In the blind H100 pass I did not yet have v1.1 C1, so I guessed a −30..+365-day window. That missed the record and paid f = 0.7.
   * v1.1 C1 states −30..+1,500 days and the earliest record. Rerun with that window, 2010 becomes +0.136 against the builder's +0.13. No other year changes.
   * Part N does not refer to the C1 matching window. I list this as ambiguity 1.
2. **J comparator in unseen B (−0.04 pt) and the EODHD overlap TR index (−0.06 pt).**
   * Betashares' A200 TR index starts on 7 May 2018, so its first daily change is 8 May.
   * Read literally, J1 uses the A200 change from 7 May, and "missing days carry the last value" gives 7 May a zero return. That is what I did.
   * The builder evidently used VAS for 7 May. Rerun that way, my comparator gives 8.777% and 8.046%, matching theirs exactly.
3. **H82 EODHD A$100k (≤ 0.13 pt).**
   * The holdings differ in one month only: 4 Jan 2021, where the builder holds FBU and I hold NIC.
   * At the December 2020 review the two scores are 3 percentile steps apart: NIC 0.7750 (17th), FBU 0.7725 (20th).
   * In my run NIC is bought on 4 Jan 2021 with partial cash (A$2,022 ≥ 0.5 T, under D2), and FBU on 7 Jan.
   * A one-rank difference in one signal, from a vendor-data or I3/I4 edge case, would explain it. Not resolved; its effect is at most 0.13 pt.
4. **Side run "EODHD unseen 2016–May 2024 price-only" at A$25k (−0.83 pt before costs; −0.22 pt tax B).**
   * The A$100k run agrees within 0.11 pt.
   * The builder itself labels this run survivor-biased. At A$25k one different pick moves the result a lot.
   * It falls outside the A$100k tolerance and is not one of the M accounts. Not pursued.

## Rule ambiguities (places where a second reader had to choose)

1. **N5 delisting-record matching.** Part N gives f values (failure 0, takeover 1, otherwise 0.7) but does not say which records count. The v1.1 C1 window (−30..+1,500 days, earliest record) reproduces the builder; any other window gives a different 2010.
   * Unstated: whether a "failure record" is decided by the C1 reason keywords or by `delist.pkl`'s `failkw`. They agree on WFL.
   * Unstated: which wins when both failure and takeover match.
   * N5's "otherwise 0.7" and I11's "after April 2020 … f = 1" overlap. No H100 pick tested this.
2. **J1 on 7 May 2018**: the A200 TRI change on its first day does not exist, and J1 does not say whether VAS fills that day (see difference 2).
3. **v1.2 is not self-contained.** Parts A–H, the core of H82, were incorporated only by reference to a file inside `bigwins2/out/`, which a blind validator is told not to open. Embed the v1.1 text in v1.2, or ship it as a separate rules file, as the coordinator eventually did.
4. **N6 tick price.** N6 says "raw close" without saying which day (S or B for the buy). v1.1 E2 says the adjusted close of the trade. I used the raw close of the trade day; H100 results match regardless.
5. **N6 Abdi–Ranaldo details.**
   * whether day-pairs that straddle the 64-day window edge count (I used only pairs inside it);
   * what to do with zero or negative highs and lows in the vendor files (I treated them as missing);
   * whether to adjust for splits inside the window (I did not).
6. **N3 traded-value rank ties**: "code order" does not say which code applies to a renamed company. I used the code on S. v1.1 B1 uses column order, which is the company identifier; v2 names each company after its first code. The builder labels holdings that way too, for example ABG#1, which trades as ABP in 2018.
7. **v2 rows with a raw close but no adjusted close** (3,905 `bad_tick` rows, where `p` is NaN). I treated them as having no close for every adjusted-price purpose and kept their traded value. Results match exactly, so the builder evidently did the same, but the rules do not say.
8. **J1 distribution amount**: `cash` or `gross` in `dist_VAS.csv`. `cash` reproduces the builder; `gross` adds about 0.04 pt a year.
9. **H100 year range**: part N names no years. The builder reports 2002–2023 on v2 and 2016–2026 on EODHD. I also produced 2000–2001 on v2, using AXJO where XJO is missing (I12 covers only stale days), and 2015 on EODHD.
10. **I3 "relative 1e-6"**: the denominator is unstated. I used max(|a|, |b|), and equal zero volumes count as agreeing. My test drops 333 codes and the results match.
11. **I4 on the v2 panel**: I4 sits in part I (EODHD). v1.1 A2 gives the same 200-day rule, so I applied it to both sources.
12. **Second H100 benchmark count**: the builder's `universe` n counts names with a close on B. My `n_universe` counts the whole universe on S, which explains differences of 1–5 names in the counts.

## Files

* Code:
  * `replication_64/code/prep.py` (I1–I8, v2 wide arrays)
  * `signals.py` (part B)
  * `engine.py` (parts C–G, I9–I10, J3)
  * `run_h82.py`
  * `run_extra.py`
  * `h100.py` and `h100_c1window.py`
  * `compare_h82.py`
* Results:
  * `replication_64/out_frozen/` (H100)
  * `out_frozen/h82/` (H82)
  * `out_frozen/post_compare/` (comparison step)
