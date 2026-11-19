# Erratum to report 76 (round 5, pooled learning)

17 Nov 2026. Source: report 77 (`77_round6_replication_capweight.md`, sections 1.3–2). Paper research only.

## 1. A data fault in the ASX development set
The ASX data set used in reports 73–76, `improve/data/pack_ASXv2_M.npz`, shows a traded value of **zero for every company from December 2024 onwards**. From that month its "100 most traded" were simply the first 100 codes in alphabetical order, nothing passed the purchase test, and the engine bought nothing for 23 months. Report 76's ASX figures came from this faulty file. Report 77 re-ran them on the EODHD total-return set, which does not have the fault. Do not use `pack_ASXv2_M.npz` for anything after November 2024.

## 2. Corrected M3 figures for ASX
Lead over the index fund, points a year, at A$25,000 / A$100,000:

| Period | Report 76 said | Corrected |
|---|---|---|
| 2016 – 2022 | +6.5 / +2.6 | **+5.5 / +1.1** |
| 2023 – Oct 2026 | +1.7 / +0.4 | **−5.3 / −2.5** |
| Whole window | +3.6 / +1.5 | **+1.3 / −0.5** |

So ASX is **not** a market where M3 was ahead. Over the last three years it trailed the fund at home.

## 3. The in-pool check
With ASX corrected, M3 was ahead in **12 of 18** market-sets in the 2023–26 check, not 13 of 18 as report 76 said (section 2.4 and the summary).

## 4. The hold rule (R7) described something that was never tested
Report 76's rule R7 says a holding may stay while it is among the **150** most traded companies. The code that produced every M3 result never ranked anything outside the 100 most traded, so that part of the rule had no effect. What was actually tested is: **a holding that leaves the top 100 (or ranks worse than 50) at two month-ends in a row is sold** (subject to the 12-month gain deferral). That is the rule that has a record. The 150 version, tested properly in report 77, is worse (China +1.0 instead of +2.2 points a year at A$100,000). The rule text now says 100 (`68_forward_record/AMENDMENT_shadow_M3_v1.1.md`).

## 5. What is not affected
- **The one look at Thailand and China** (report 76 section 4) used other data and is reproduced by report 77's independent rebuild. Its figures stand.
- **The owner-account figure** (A$5,000 plus A$500 a month on ASX, after tax: M3 A$78,220 against A$86,763 for the fund) was already computed on the correct data and stands. Report 77 adds that the size of the gap is uncertain (A$76,500–88,700 across reasonable settings), but M3 trails the fund either way.
- The overall verdict is unchanged: **M3 is not shown to beat the index.** It stays a shadow line only, tracked for information from its first decision on 30 Nov 2026.
