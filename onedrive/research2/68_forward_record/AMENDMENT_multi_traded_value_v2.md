# Amendment: multi-market forward record — traded value read once per split event, in every market (v2)

Status: **ADOPTED 19 Nov 2026** (owner standing instruction "just do it, don't keep asking"; report 83 §1, `83_round11_corrected_data_fable.md`; report 85 §6.5). Final rule as set by Fable (report 83): **one reading per split event; steps at most 20 rows apart are one event.** Hashed (SHA-256) and appended to `LEDGER.jsonl` **before the live builder is edited** and before the first decision of the multi-market record (Mon 30 Nov 2026 month-end). PAPER ONLY. No real money, no broker orders. The AI never places trades. EODHD data are used under a private, non-commercial licence. Text below is Fable's draft (`deep83/amend/AMENDMENT_multi_traded_value_v2.DRAFT.md`, SHA-256 80d5c42b4d05f21f6c7da8bb5299be276dac975505963e8330fda5a223e21cd4) with only this status line and the title changed.
Amends: `AMENDMENT_forward_multimarket.md` (ledger seq 14); builder `bigwins_forward/code/multi_build.py` (SHA-256 024d206e5d3c10d28e905855acbb9ee2e08482d9a1a5d18dfe0bd01b6f56fc44 as read on 19 Nov 2026).
Evidence: report 83 section 1; files in `scratchpad/deep83/amend/` and `deep83/out/fwd_events.csv`.

## 1. Defect
"Most traded" is the 252-day median of each day's traded value. The builder computes a day's traded value as raw close × vendor volume ÷ F, where F is the product of later split ratios, read from steps of more than 12% in raw close ÷ adjusted close. That is right only where the vendor has restated the old volume into new-share units. The vendor does this for most splits, not all.

1. In the forward stores (rows since 1 Sep 2024, 14 markets) there are 193 steps beyond 2:1 with enough rows to read. In 36 (19%; 17 of 84 in DE/FR/SE/CA) the old volume is still as traded. For those, ÷ F is wrong by the full ratio. After a 1-for-k consolidation with volume as traded, every earlier day's traded value is multiplied by k and a penny share looks heavily traded. This put reverse-split shells at the top of the US back-test list (June 2015: DRYS, PSTV, PACD, DCIX, APHB, DCAR, ONVO among the "100 most traded"; report 83 section 2).
2. Steps of 12% to 2:1 are mostly large dividends and rights issues, where volume is never restated. ÷ F understates those companies by the size of the step.
3. **The round-3 builder rules (`r3`: DE, FR, SE, CA) apply every step unread.** These four markets carry the faulty definition at the 30 Nov 2026 decision and after.
4. The round-4/5 rules (`r4`, `r5`: ASX, SW, KO, TW, BK, SA, CN, HE, WAR, BR) test each step separately ("V2 volume guard"). That test has its own fault: when the vendor's raw close flips between old and new units for a few days around a consolidation, each flip is a step, some are dropped and some kept, and the errors multiply. Stockholm WYLD has 45 such steps in 2024–25; the per-step test overstates its 2021–24 traded value about 1,500 times and would rank a share trading under SEK 1m a day among Sweden's 100 most traded. The guard also skips a step with fewer than 5 traded rows on either side and then assumes the volume was restated.

## 2. Rule change (effective from the first decision, the November 2026 month-end, all 14 markets)
Traded value of a day = raw close × vendor volume ÷ F, with F built as follows.
1. A step is a change of more than 12% in raw close ÷ adjusted close between consecutive rows (unchanged).
2. Steps with at most 20 rows between them form one **event**. Its ratio G is the product of its steps. An event with G within 12% of 1 is a vendor glitch that reverses and is ignored.
3. Each remaining event is read **once**: B = median raw close × volume over the last 20 traded rows before the event; A = the same over the first 20 traded rows after it (never reaching into a neighbouring event). If traded value is more continuous without the correction than with it, |ln(A/B)| < |ln(A·G/B)|, the vendor left the volume as traded and the event is ignored. Otherwise G enters F at the event's last step.
4. An event with no traded row on one side cannot be read. A consolidation (G < 1) is then ignored and a split (G > 1) applied. Both give the lower traded value, so an unread event cannot lift a company into the list.
Nothing else changes: adjusted prices, scores, engines, costs, tax, controls, fills, scorecard.

## 3. Code patch
One function replaced (`split_factor`) and one call changed in `multi_build.py`:
```
-        d, cl, adj, vol = d[ui], cl[ui], adj[ui], vol[ui]; F = split_factor(cl, adj, None if r == 'r3' else vol)
+        d, cl, adj, vol = d[ui], cl[ui], adj[ui], vol[ui]; F = split_factor(cl, adj, vol)
```
- Full unified diff: `deep83/amend/multi_build_v2.diff` (SHA-256 3e1d56170cc773cc052b2fc1e9f3d7c8170981ce823b8f7778df80c7f564b503).
- Patched file, ready to copy: `deep83/amend/multi_build_v2_proposed.py` (SHA-256 08a6b613595b6096fee646b3969a0ae15cf25aaac6afda2703009a2ce0aaa4c6).
- Unit tests on synthetic series (restated / as-traded volume at ratios 100, 5 and 0.2; flip-flops; a 20% dividend; an unread last-row consolidation): `deep83/amend/test_split_factor_v2.py` (SHA-256 dd62f209283ce3954b075fd4ecc4ce65bbcd43e1d16a0b3eb2f7756e485335dd), all pass.
`paper_multi.py` needs only its code-hash list refreshed. `multi_frozen/` is untouched. Keep the current file as `multi_build_v1_frozen.py`.

## 4. Test: lists before and after (live forward stores, data to 17 Nov 2026; `deep83/code/fwd_test_v2.py` → `amend/test_lists_before_after.csv`, `test_traded_value_changes.csv`)
The 30 Nov lists will be built from this same history plus nine sessions. Buy lists are M3 ranks 1–15 and EI10I / CW ranks 1–30.

| Market | Rules | 100 most traded: same | M3 buy list | EI10I | CW | Names whose traded value moves > 5% | Best old rank among them |
|---|---|---|---|---|---|---|---|
| DE | r3 | 100 | 15/15 | 30/30 | 30/30 | 2 | 324 |
| FR | r3 | **99** | 15/15 | 30/30 | 30/30 | 8 | 74 |
| SE | r3 | 100 | 15/15 | 30/30 | 30/30 | 6 | 190 |
| CA | r3 | 100 | 15/15 | 30/30 | 30/30 | 1 | 280 |
| SA | r4 | 100 | 15/15 | 30/30 | 30/30 | 3 | 240 |
| ASX, SW, KO, TW, BK, CN, HE, WAR, BR | r4/r5 | 100 | 15/15 | 30/30 (where run) | 30/30 (where run) | 0 | — |

Names that move: FR ERA 106 → 93 (a 1.44 step on 16 Nov 2026, volume as traded; it enters the 100 and the old rank-100 name leaves), BOL 74 → 70, ALSRS 217 → 373, ALTOO 317 → 430, MHM 418 → 350; SE FRNT-B 190 → 406 (was overstated 19 times), CYNCA 230 → 398; CA AVL 280 → 410 (overstated 43 times); DE QBY 386 → 409. **No buy list changes on today's data. The fault is latent, not active.** One 1-for-100 consolidation with unrestated volume in a mid-ranked DE/FR/SE/CA share would put it in the 100.
History check of the same rule (report 83 section 2): on fresh 1999–2026 downloads the corrected "100 most traded" shares 99.2 (DE), 98.4 (FR), 98.3 (SE) and 97.7 (CA) of 100 names a month with the tested rule over 2018–26; the back-test verdicts of M3, EI10I and CW do not change.

## 5. What is not changed, and what to record
- Nothing booked so far depends on this: the first decision is 30 Nov 2026.
- The forward builder no longer "equals the tested builder" for any market. For r3 markets it equals the corrected builder whose back-test is in report 83. For r4/r5 markets the lists are identical on today's data.
- Each month the job should log, per market: events found, events ignored as glitches, events read as "volume as traded", events unread; and any universe name with a raw close under one local currency unit.
- The ASX H82 record (`bw13_prep.py`, v1.4: adjusted close × volume, every split assumed restated) rests on the same assumption. On the ASX store since Sep 2024, 17 of 18 steps beyond 2:1 were restated and the other (AUZ, rank 427) is far from the list. Outside this amendment; a guard of this kind is recommended at the next H82 amendment.
- Trial count: a data-rule correction, not a trial. N unchanged.
