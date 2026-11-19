# Amendment v1.4: traded value from split-consistent units

Status: **ADOPTED 17 Nov 2026** (owner standing instruction "just do it, don't keep asking"); hashed and appended to `LEDGER.jsonl` before the 31 Dec 2026 decision is computed. The 16 Nov orders stand as recorded (report 74: no pick changes). PAPER ONLY. No real money, no broker orders. The AI never places trades.
Rules: v1.3 (`67_FINAL_RULES_v1.3.md`, SHA-256 b38abcd7…54b0). That file is not edited; this amendment overrides the clauses named below from its effective date. Evidence: report 74.

## 1. Defect
EODHD's AU `volume` is split-adjusted to the download date; its AU `close` is raw (report 74 §2: across 597 2018–2026 events where the close is raw, volume is continuous and raw close × volume jumps by 1/s). v1.3 A5 (and `bw13_prep.py`: `TV = (C * VOL)`) multiplies the two. Every day before a later consolidation is understated by its ratio, and every day before a later split is overstated. A2's phrase "volume — as traded, not adjusted" is wrong.

## 2. Rule change (effective from decision day Thu 31 Dec 2026)
- **A2**: read "`eod` (date, open, high, low, close as traded; volume as the vendor gives it, which is adjusted for splits and consolidations up to the download date)".
- **A5**, last sentences, replaced by: "Traded value of a day = P(d) × volume(d), where P is the adjusted close defined above (equivalently, raw close × volume ÷ the product of A3-applied ratios dated after d); zero on a day with no row." A ratio A3 did not apply (vendor close already adjusted) needs no correction, and none is made.
- This governs every use of traded value: B1 universe and order, B6 eligibility (≥ 100 × T), E2 spread tiers, N3 (H100, median ≥ A$50,000, rank > 300) and the H101 tracking line (ranks 301–1000).
- P and volume must come from the same download (Q2 already fixes one file per decision).

## 3. Code patch (described only; frozen code not edited by this draft)
`bigwins_forward/code/bw13_prep.py`, line 105: `TV = (C * VOL)` → `TV = (P * VOL)`. Nothing else changes. The new file gets a new SHA-256 in `code_hashes.txt` and the manifest. `paper_lib.py` needs no change (it takes `medval`/`vrank` from the bundle). A reference implementation that loads the patched line without touching the file is `scratchpad/vbug/patched.py`.

## 4. What is not changed
- **The 16 Nov 2026 decision and the 17 Nov fills are recorded as they stand.** Report 74 §5 recomputed that decision with the corrected traded value: the 300-company universe, every score and all three pick lists (A$5k: 4; A$25k: 10; A$100k: 30 names) are identical, and no pick changes spread tier. The only differences are traded-value ranks: PDI 243→123, LOT 262→252, AMC 58→55, SSM 237→239, with ±1 shifts for neighbours, plus 33 companies in ranks 301–1000. The difference is noted here and needs no booking.
- The 30 Nov 2026 month-end (C9 vacancy fills only) runs under v1.3 as frozen. Its snapshot should also record the corrected ranks beside the frozen ones, for information only.
- The random and momentum controls switch on the same date, so the comparison stays like for like.

## 5. Back-test figures to cite from now on (unseen B, 2018–13 Nov 2026, A7(b))
| % a year | A$25k | A$100k | Comparator |
|---|---|---|---|
| After costs (was 8.27 / 9.96) | 8.35 | 9.32 | 8.78 |
| After tax A (was 6.95 / 7.47) | 6.45 | 6.99 | 6.84 |
| After tax B (was 6.32 / 6.47) | 5.59 | 6.12 | 6.21 |

Counted as one trial (N = 951). The verdict stands: not shown to beat the index. The correction is a data fix, not a design change; no parameter moves.
