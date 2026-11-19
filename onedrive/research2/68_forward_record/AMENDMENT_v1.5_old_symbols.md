# Amendment v1.5: vendor `XXX_old` symbols admitted to the universe (rule A4)

Status: **ADOPTED 19 Nov 2026** (owner standing instruction "just do it, don't keep asking"; review 80 §0.3 item 1). Hashed (SHA-256) and appended to `LEDGER.jsonl` **before any code is edited** and before the first forward decision it governs. PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence.
Rules: v1.3 (`67_FINAL_RULES_v1.3.md`, SHA-256 b38abcd7…54b0) + `AMENDMENT_start_now.md` + `AMENDMENT_intraday_look.md` + `AMENDMENT_v1.4_traded_value.md`. Those files are not edited; this amendment overrides the clauses named below from the effective dates in §2. Evidence: report 80 §1.1 (`80_independent_review_fable.md`), work files `scratchpad/review80/bt80b.py`, `bt80b.json`; live check `scratchpad/fix81/live_old_check.py`, `live_old_check.json`.

## 1. Defect
When EODHD gives a delisted company's three-character code to a new company, it renames the old company's history to `XXX_old` (a second re-use gives `XXX_old2`, and so on). Rule A4 ("Type = Common Stock and code of exactly three characters"; `bw13_prep.py` line 58, and the same filter in `fwd_download.py` lines 29 and 41) drops every such symbol. In the vendor's AU list there are 73 common-stock symbols of the form three characters + `_old` (+ digits). Real top-300 companies were missing from every back-test on EODHD data: Coca-Cola Amatil (`CCL_old`, to 2021), Altium (`ALU_old`, to Aug 2024), Sirtex, Village Roadshow, Mantra, Sundance, Propertylink, Centuria Metropolitan and four smaller ones. With them restored, H82 on unseen B (29 Dec 2017–13 Nov 2026) is **6.94% / 8.93% a year after costs at A$25k / A$100k**, not 8.35% / 9.32%; the index fund is 8.78% (report 80 §1.1). These are the figures to cite from now on.

## 2. Rule change
**A4** is read: "Ordinary shares: Type = Common Stock and either (a) a code of exactly three characters, or (b) a vendor-renamed code of exactly three letters or digits followed by `_old` and optionally digits (pattern `^[A-Z0-9]{3}_old[0-9]*$`). Codes of other lengths stay out (4-character codes such as `AQLT_old` are not ordinary shares under A4)." Everything downstream is unchanged: ETP exclusion, A7(b) duplicate codes (a renamed company whose history the vendor also kept under its new code is merged by A7 exactly as other duplicates are), A8 code re-use split, B1–B6.

Effective dates:
| Line | From | Before that date |
|---|---|---|
| **H82 books, momentum and random controls, H101 tracking line** | the **Thu 31 Dec 2026** decision (December review), the same date as Amendment v1.4 | The 16 Nov 2026 decision and 17 Nov fills stand as recorded; the 30 Nov 2026 month-end (C9 vacancies only) runs under A4 as frozen |
| **SHADOW M3 and SHADOW E3** (`AMENDMENT_shadow_M3_E3.md`, v1.1) | their **first decision, Mon 30 Nov 2026** | (no earlier decision exists) |
| **SHADOW ACC** (`AMENDMENT_shadow_ACC_keep_winners.md`) | its first decision, 30 Nov 2026 (it reads the M3 table) | — |

Because the H82 decision of 30 Nov 2026 is still made on the frozen A4, the shadow lines' bundle for 30 Nov 2026 is built separately with the admitted symbols (same file, same cut, same A7(b)); from 31 Dec 2026 the shadow lines again reuse the H82 bundle.

Smaller points, written so nothing is left to judgement:
- **Industry group (A11, C4 cap):** A11 looks up the vendor code literally, so `XXX_old` is not found and the company's group is unknown (C4: never refused). It never takes the group of the company that now uses the plain code.
- **Names** in snapshots are the vendor's names for the `_old` symbol (e.g. "Altium Ltd").
- **Data refresh (Q1, `fwd_download.py`):** the forward panel includes these symbols from the research store and the forward store. At the month-end refresh, any such symbol that has no end-of-day file in either store is downloaded once (end-of-day, splits, dividends), so a code the vendor renames after 19 Nov 2026 is also picked up. Active-code downloads are unchanged.

## 3. New written rule A9: a held code that is renamed or re-used
A holding belongs to a company, not to a code. If a paper book holds a code and the vendor later moves that company's history to `XXX_old` (or a new company starts trading under the code), then: (a) prices for the holding are read from the `XXX_old` series; (b) any close under the plain code dated after the old company's last close is ignored for that holding; (c) the scorecard flags it and a person checks it against the company announcement before the next decision. In practice v1.3 Q6/C1 (no close for 20 trading days → paid out at the last close) settles almost every case before the vendor re-uses the code. **Automation of (a)–(b) is pending**; until then the check is by hand when Q6 or a price jump of more than ×3 or ÷3 in one day flags a held code.

## 4. Is the forward (live) universe affected? (checked 19 Nov 2026, no returns computed)
- **Forward store:** the forward panel used by the paper record (`bigwins_forward/data/eodhd/panel_tr.pkl.gz`) holds **no** `_old` symbol today (`fwd_download.py` filtered them), so no decision made so far could have seen one.
- **Effect on the decision tables:** the frozen preparation was run on the research store cut at 13 Nov 2026 with and without the change (`fix81/live_old_check.py`). The top-300 universe and its order are **identical at every month-end from 31 Oct 2024 to 13 Nov 2026**, and no `_old` company is in the top 1,000. The last differences are Altium (`ALU_old`), in the top 300 until Sep 2024 (one company displaced each month), and TASK Group / Silk Laser in ranks 301–1,000 in 2024.
- Reason: the universe needs at least 200 closes in the last 252 trading days, and every `_old` company is delisted. The three with the latest data (American Pacific Borates to 21 Nov 2025, GBM Gold to 28 Nov 2025, Absolute Equity Performance Fund to 5 Jan 2026) are merged into their current codes by A7(b) or have too few recent closes.
- **So the 30 Nov and 31 Dec 2026 decisions are expected to be unchanged by this amendment.** It matters for the back-test record (report 80) and for any company renamed in future while it is still in the 252-day window.
- Not affected: the multi-market ASX line (`multi_build.py` takes candidates from the day's bulk file of traded codes and has no length filter; delisted `_old` codes never appear there).

## 5. Knock-on not done here (pending)
Report 80 §1.1 lists the ASX results built on the same filtered bundle: report 70, M3/EI10I/CW on ASX (reports 76–77) and the round-8 ASX holdout (report 79). They are not re-run by this amendment; each re-run would be counted as a trial when it is done.

## 6. Trial count
No return is computed for this amendment. The corrected H82 re-run was counted by review 80 (N = 1,710). **N stays 1,710.** The verdict stands: not shown to beat the index.
