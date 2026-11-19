# Amendment v1.6: duplicate codes found by daily returns (rule A7(c))

Status: **ADOPTED 19 Nov 2026** (owner standing instruction "just do it, don't keep asking"; report 81 §3.1 and §0 item 9(i)). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before any live code is edited** and before the first forward decision it governs. PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence.
Rules: v1.3 (`67_FINAL_RULES_v1.3.md`, SHA-256 b38abcd7…54b0) + `AMENDMENT_start_now.md` + `AMENDMENT_intraday_look.md` + `AMENDMENT_v1.4_traded_value.md` + `AMENDMENT_v1.5_old_symbols.md`. Those files are not edited; this amendment adds one test to rule A7 from the dates in §3. Evidence: report 81 §3.1 (`81_algorithm_deep_dive_fable.md`); data checks `scratchpad/fix82/scan.py`, `diag_a7c.py`, `pairs8.py`, `live_check.py`, `live_h101.py` (outputs `a7c_research_2026-11-13_1.json`, `live_check.json`). No strategy return was computed for this amendment.

## 1. Defect
Rule A7 drops a renamed company's old code only when the two codes show the *same closing prices* (A7(a): every common day, volumes too; A7(b): 90% of 60 days). The vendor sometimes stores one copy of the history at a different price scale (Propertylink: `PLG` 1.326 and `PLG_old` 1.015 on the same day), or with a few stale or shifted rows, and then both tests fail. Report 81 found ten companies carried twice in the top-300 history: ALX/MQA (Atlas Arteria), HLS/PRY (Healius), KLS/SLK (Kelsian), JHG/HGG (Janus Henderson), COF/CMA_old (Centuria Office), RYZ/MNS, WNX/WHA, NGI/HFA, EXT/CVT, PLG/PLG_old (Propertylink). Effects: 228 company-months of the top 300 are a second copy; one company can be bought twice; a holding under the old code is paid out at the rename although the investor never sold.

## 2. Rule change: A7(c)
Added to A7, applied after (a) and (b), on the file as downloaded (same place in the procedure as (a) and (b); before the cut at the decision day and before A8):

- **(c)** [forward use; daily-return test, scale-free] A code has a *clean return* on day t when it has a row with close > 0 and volume > 0 on t **and** on the file's previous day; the return is the vendor's daily price return (`ret_pr`). For two codes X and Y left after (a) and (b), take every day of the file on which both have a clean return. X is dropped entirely as a duplicate of Y when: there are **at least 120** such days; X's return is **non-zero on at least 100** of them; the Pearson **correlation of the two returns is at least 0.995**; and Y's last close is after X's last close — or on the same day, with Y having more closes in the file (equal: Y is the earlier code in column (alphabetical) order). If several Y pass: the highest correlation, then column order. The test runs between every pair of codes, `XXX_old` and `XXX` included.
- The (X, Y, X's last close) pairs are added to the A7 pair list, which stays the engine's code-change map: a holding recorded under X continues as Y with its lots, dates and cost unchanged.
- Computation: a matrix estimate of every pair's correlation is used only to choose which pairs are computed exactly (estimate ≥ 0.99); the decision uses the exact value. Code: `bw13_prep.a7c()`.

**Why this form of the report-81 test (decided on data checks before the amendment; no return computed).** Report 81 §3.1 gave "correlation ≥ 0.995 over at least 120 common days with at least 100 non-zero returns" as an example. Computed naively on every common day of the raw vendor returns, it finds only six of the ten pairs (WNX/WHA 0.992, EXT/CVT 0.982, COF/CMA_old 0.79): a return after a gap spans a different number of days in the two series, and the vendor carried CMA_old at a stale close for 23 days after it stopped trading. Restricting to days on which both codes traded that day and the day before removes both effects. With that definition all ten pairs score 0.9996–1.0000 on 478–1,792 non-zero returns (the day counts match report 81's table to within 1–3%: e.g. MQA 932, SLK 1,628, PLG_old 478, HFA 759).

Report 81 also listed three pairs at 0.998–0.999 as "related funds, not the same company". The vendor's names show they are the same company renamed: CLQ/SRL (both "Sunrise Energy Metals"), VG1/RG1 ("VGI Partners Global Investments" → "Regal Partners Global Investments"), PMC/GLS ("Platinum Capital" → "L1 Global Long Short Fund"). A7(c) removes them, which is correct.

## 3. Effective dates
| Line | From | Before that date |
|---|---|---|
| **H82 books, momentum and random controls, H101 tracking line** | the **Thu 31 Dec 2026** decision (December review), the same date as Amendments v1.4 and v1.5 | The 16 Nov 2026 decision and 17 Nov fills stand as recorded; the 30 Nov 2026 month-end (C9 vacancies only) runs under A7(a)/(b) as frozen |
| **SHADOW M3, SHADOW E3** | their first decision, **Mon 30 Nov 2026** | — |
| **SHADOW ACC** (reads the M3 table) | its first decision, 30 Nov 2026 | — |
| **SHADOW CXL** (`AMENDMENT_shadow_CXL_D2.md`) | its first decision, 30 Nov 2026 | — |

Because the H82 decision of 30 Nov 2026 is still made under A7(a)/(b), the shadow lines' bundle for 30 Nov 2026 (already built separately under Amendment v1.5) is built with A7(c) as well; from 31 Dec 2026 the shadow lines again reuse the H82 bundle. On 30 Nov the shadow lines hold nothing, so the code-change map they read (ACC: the H82 decision file of the day) needs no A7(c) pairs; from 31 Dec the H82 decision file carries them. The frozen back-test procedure (`dup_rule='frozen'`) is unchanged; A7(c) is a forward rule like A7(b).

## 4. Would the live decisions so far have changed? (checked 19 Nov 2026; no returns computed)
The frozen preparation was re-run with and without A7(c) (`fix82/live_check.py`, `live_h101.py`):

| Decision table | Store (as used then) | Top 300 (members, order, every field) | Ranks 301–1,000 | H101 snapshot |
|---|---|---|---|---|
| 30 Oct 2026 (month-end snapshot) | research store, file to 13 Nov, A4 frozen | **identical** | two companies differ (KAN and EAU, see below) | **identical** (members and ranks) |
| 13 Nov 2026 (interim snapshot) | research store, A4 frozen | **identical** | two differ (KAN, EAU) | **identical** |
| **16 Nov 2026 (H82 start decision; orders for the 17 Nov close)** | forward store, file to 16 Nov | **identical** | **identical** | **identical** |
| 16 Nov 2026 with A4(b) `_old` codes admitted (as the shadow lines will run) | forward store | identical | identical | — |

**So no decision, list or order made so far would have differed, and nothing recorded is changed.** On the research store A7(c) finds 111 more pairs; 14 of the dropped codes were in the top 300 at some month-end since Nov 2015 (the ten pairs, CLQ, VG1, PMC and G79/NXE) and 20 were never in the stored top 1,000; the top 300 differs from the frozen tables only at month-ends up to Nov 2024 (RYZ/MNS to Sep 2023, VG1/RG1 to Nov 2024, and the ten pairs earlier). Two pairs are still trading on both codes at 13 Nov 2026 in the research store (KAN/HGO, EAU/C1X; ranks 301–1,000 only); the forward store does not carry them as duplicates at 16 Nov.

## 5. Knock-on not done here
Back-test figures built with A7(a)/(b) (reports 64–81) are not re-run by this amendment; report 81 already shows the H82 effect of removing the ten companies (A$100,000: 10.29 / 9.73 / 7.30 before costs / after costs / after tax; A$25,000: 9.21 / 7.17 / 6.47). Any future re-run that uses A7(c) is counted as a trial when it is done.

## 6. Trial count
A data rule; no strategy return computed. **N stays 1,729** (report 81). The verdict stands: not shown to beat the index.
