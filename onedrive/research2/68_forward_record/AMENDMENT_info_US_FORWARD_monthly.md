# Amendment (information only): US_FORWARD_monthly — monthly paper tracking of the frozen US rules of ledger seq 107

> Drafted 26 Nov 2026 and registered the same day as a ledger entry with `"amendment": "AMENDMENT_info_US_FORWARD_monthly.md"`. The monthly job writes no ledger entry without that entry.

Status: **REGISTERED 26 Nov 2026 (Sydney)**, by the record keeper on the owner's instructions ("Keep working on US", "Keep working on it", 25–26 Nov 2026). Every historical year has been seen, so forward tracking is the only clean evidence left. **Information only. No line, no slot, no twins, no real money; the AI never places trades.**

## 1. What is tracked
Every month, from the first decision (the last US session of November 2026; first fill 1 December 2026), the rules registered for dated readings in ledger seq 107 (`AMENDMENT_info_US_FROZEN_READ_2028.md`, SHA-256 `6579b12cffcc84997a70515d1148dc3b923baab2ce3149c6f6bea1bc54dfd926`), each exactly as frozen in its study and run with that study's own engine, each from A$10,000:
- the 3× trend rule A3 (`research_us2/PREREG.md`): eng2.sim with the One strategy on SPY / UPRO / T-bill fund;
- LEAD20 (P1) and TOPTV20 (P8) (`research_us4/PREREG.md`): eng4.Leaders / eng4.TopTV through eng2.sim;
- the ML book P6 B25-G3 (`research_us5/PREREG_final.md`): c5.build features, c5.walk refit at each December month-end (the January job) with the frozen hyper-parameters and seeds 1–3, lib5.Book through eng2.sim;
- the insider rule T1 (`research_us3/PREREG.md`) with the payout fix of `research_audit_us/PREREG.md` (fix F): eng3.signals / eng3.Event / eng3.sim. The EODHD insider feed costs about 150–300 credits a month (10 per 1,000 rows, re-reading 40 days for late filings), so it is affordable;
- IVV.AU, VGS.AU and NDQ.AU on the same dollars, distributions reinvested after tax (eng2.fund).
Costs, FX, US withholding and Australian tax as in each study's engine; **personal 47% and super 15%** (and before tax for reference). Each month's value is what the account would be worth if everything were sold at the close of the first US session after the month-end.

## 2. Status of the monthly figures
- **Information only; no line, no slot.** Nothing here is a paper line, a shadow line, a twin set or a trading decision. No order goes anywhere.
- **Excluded from the line cap of seq 96** (`AMENDMENT_retirement_jan2027.md`: the cap "excludes information-only archives that feed no line"). The monthly tracking feeds no line.
- **The readings and bars stay exactly as in seq 107**: facts-only interim reading at the first US session of December 2027, main reading at the first US session of December 2028, with the wording and the at-most-a-discussion bar of seq 107. **No proposal of any kind is made from these figures before the December 2028 reading.**
- **The monthly figures are folded in the owner's app** (shown collapsed, labelled "information only — mostly luck at this stage; first reading Dec 2027"); they are never shown as a leaderboard or ranked against the paper lines.
- **Trial count: registering adds no trial.** Each dated reading counts as in seq 107 (one trial per rule read, at the December 2027 and December 2028 readings only). **The monthly snapshots are not trials** and are not readings.

## 3. Forward adaptations (forced by running forward; nothing else differs from the frozen studies)
1. **Data.** The research_us panel (built 24 Nov 2026, last row 23 Nov 2026) is the history, trimmed to June 2022 (enough for every rule's look-back and for the P6 features). After it, one EODHD US bulk end-of-day file per session (100 credits). Because the vendor re-adjusts past adjusted closes, each download batch re-fetches the last stored session as an anchor, and total-return links are taken inside a batch only. The panel's daily traded volume is not on file, so the 252-session traded-value window of the frozen ranking was bootstrapped once (26 Nov 2026) with one end-of-day history call per live company; the forward ranking reproduces the panel's October 2026 medians (median difference 0, 95th percentile 1.2e-7; test `test_ranking_bootstrap_matches_panel`). Exact ranks are not identical: near-equal medians swap places (13% same rank, 84% within 5 ranks at the 26 Nov check). This is accepted as a forward adaptation. Codes outside the bootstrap that come to trade enough to matter get their history once (1 credit each).
2. **Data guards forward.** The build.py cleaning (bad ticks; ×3 up-breaks and scale-error down-breaks cut a series; venue and suffix exclusions; one line per company; the eng4 earlier-copy guard) is applied to forward rows. A new code that takes over a stopped code within 8 days with the same ISIN or vendor name is treated as a ticker change of the same company (the vendor's history showed such changes as one series).
3. **T-bill fund.** A3's T-bill fund and T1's idle-cash rate use the 3-month bill (FRED DTB3) less 0.14% while that file has data (to 20 Nov 2026); after that A3 holds the listed T-bill fund BIL.US (its total return; the fund is the bill less a 0.14% fee) and T1's idle cash earns BIL.US's mean daily total return over the last 21 sessions, never below zero. FRED is not downloaded.
4. **Payout rule.** A3, P1, P8 and P6 keep their studies' registered delisting payout; T1 uses fix F (seq 107).

## 4. Budget and storage
EODHD credits: at most 10,000 in any UTC day and at most 36,000 in any 365 days outside the one-off bootstrap (about 3,000 a month); a normal month uses about 2,400–2,700 (21–23 bulk files plus one anchor at 100 each, the symbol list, four benchmark files, 15–30 insider pages at 10 each). The account endpoint is never called; the job keeps its own credit book. The forward store stays in the scratchpad (personal licence), about 42 MB now and about 2 MB more a month.

## 5. Files (SHA-256 at drafting)
| File | SHA-256 |
|---|---|
| `onedrive/research2/68_forward_record/AMENDMENT_info_US_FROZEN_READ_2028.md` (the seq 107 amendment (rules and readings)) | `6579b12cffcc84997a70515d1148dc3b923baab2ce3149c6f6bea1bc54dfd926` |
| `bigwins_forward/code/paper_us_forward.py` (the monthly job) | `613f785a549c01b5f88a44aea9a118d47555cce53c57734b84d6b8af4c2645e9` |
| `bigwins_forward/code/test_us_forward.py` (its tests) | `6426707449964f05260e63fea55855607dea5d68cc24c6d9fe43468e48908e7f` |
| `bigwins_forward/code/fwd_ledger.py` (ledger helper (unchanged)) | `24559f2e3e5aa33a5e0d5be17b2ea0914bb68bc34c9b830cf38afa3cc43cf294` |
| `research_us/code/eng.py` (frozen engine (loader, costs, funds)) | `ceb5cb48aa2929807e0cf14c147453c1e05c19832145c52062753e3efae3ce7d` |
| `research_us2/code/eng2.py` (frozen engine (simulator, tax structures)) | `4c697e7602aa9397599bc156606d813a1f550f69f869a60a7b84d16691a0e21f` |
| `research_us3/code/eng3.py` (frozen engine (T1 daily simulator, insider signals)) | `56cbad9b360682a29372c1c770bab32913cd9e34710c998f7509a7201f0c3f20` |
| `research_us4/code/eng4.py` (frozen engine (LEAD20, TOPTV20, pools)) | `d591b3ba0f308c5ab5aa65fa72488da72b3f251a8174a8d13879ee8ed5b6edcb` |
| `research_us5/code/c5.py` (frozen pipeline (P6 features, walk-forward refit)) | `46e75b6341984eaa0c9adaf2a2a19721e78cec11533774c6d50ee310a8984e5d` |
| `research_us5/code/lib5.py` (frozen book rule (P6)) | `303e27896a7d6816479a291a6e9dc3a9f74a23a9ea642a9cd16e25ce0c896dbb` |
| `research_audit_us/code/auditfix.py` (payout fix F (T1)) | `e5b9393551b17d6fca8b4af63c4ab8e422d84607e94b992ba1e4cd79992c21db` |
| `research_us2/PREREG.md` (A3 registration) | `035c8b81c135dd857c4a3162c4810c943ea99d6934bc29c522294c3dd91af65b` |
| `research_us3/PREREG.md` (T1 registration) | `af7b3dc1940f20665ccb0ebc0cb58ea980ccaa1ca2c34e5e2212f44f0ad76743` |
| `research_us4/PREREG.md` (P1/P8 registration) | `e155ea982e03b3d11e84f6cd2476d7cc7f27f5f0b06e6d2af4c8b640375b61a1` |
| `research_us5/PREREG_final.md` (P6 frozen specification) | `09302efd7502e17182a2a9ae975c921b22e7f0e84c35a9b632fb66d47b2dc1a9` |
| `research_audit_us/PREREG.md` (fix F registration) | `b6787ba96d27bb15e062f44217716f62d3ee84b7661a574a7629b63feda75b39` |
| `research_us/data/panel.npz` (history the forward store was bootstrapped from) | `61a938955779c817c71e6c0ab11d9e90139e870929d60a366ef02e4c2123d83e` |
| `research_us5/data/pred_open.pkl.gz` (P6 training table and sealed-run scores) | `a886a1ad369c2b6d78f894c11af98b95aaf609b51ba1ba1dac49cbe02dc03aa8` |
| `us_forward/data/boot.npz` (forward store: trimmed panel (bootstrap)) | `4de1893c187a636bef7519349ca5f0dc483278eeacdc4366fd2f6287c1ca0593` |
| `us_forward/data/boot_tv.npz` (forward store: daily traded-value window (bootstrap)) | `9189eac332d965d4107e5b7c6d352cfda761a13755750d0bb8f04b4e4b0942f1` |
| `us_forward/data/p6/base_table.pkl.gz` (forward store: P6 table (bootstrap)) | `17e27315d43d9df5df74fb57a4dd2f08f38176bb4ac86ab2b59db70d2035bc8d` |
