# DRAFT — NOT REGISTERED. Amendment (information only, scoring): the main paper line `EMG2_18_SIM_BT_C6` reported after 15% super tax beside 47% personal tax

> **DRAFT, 25 Nov 2026.** Not hashed, not in `LEDGER.jsonl`, governs nothing. The record keeper registers it only after the owner approves, on or after 1 Jan 2027, before the first scorecard it changes.

Status (to be filled at registration): **REGISTERED <date>**, by the record keeper, on `research_grand` s6 item 2 ("the same paper line scored in super-tax terms; no new rule") and the owner's decision of <date>. **Information only; a change of reporting, not of any rule.** No order, decision, book, twin, comparator or reading of any line changes; the registered readings (`AMENDMENT_shadow_EMG2_18_BT_C6.md` s3, `AMENDMENT_retirement_jan2027.md` s5) stay as written. Not a paper line, so the line cap is not touched. The AI never places trades.

## 1. Why
- After 47% tax most of the edge is gone: over 2002–2026 the January version led A200 by 3.3 points a year untaxed, **2.8 in super and 1.4 personally** (`research_grand` s3). The strategy realises nearly all gains within 12 months; the index fund defers them.
- The only structure question that matters for the owner is "personal or super". `research_grand` s3–s6: super is the right home in principle, but an SMSF only pays above about A$110k in the strategy; until then the forward record should at least show both numbers on the same paper line, every month, from the same orders.
- The scorecard of `EMG2_18_SIM_BT_C6` today says "after costs; no tax modelled". This entry adds two after-tax columns, without changing anything else.

## 2. Definition (fixed now)
For `EMG2_18_SIM_BT_C6` and for its A200 comparator (the same money in A200 from the line's start, cash flows dated as the line's, as the app's scoreboard), each month-end, two after-tax readings computed from the line's own fills, dividends and corporate actions (no new order):

| | Personal | Super (accumulation) |
|---|---|---|
| Tax rate on realised gains and income | **47%** (top marginal incl. Medicare) | **15%** |
| Discount for a parcel held 12 months or more (367+ days, as the H82 scorecard) | 50% | one-third (effective 10%) |
| Realised losses | carried forward against later gains, never refunded | same |
| When tax is paid | each 30 June, from the book's cash, on that financial year's net realised gains and dividends | same |
| Franking credits | not counted (as every research book; understates super, see s4) | not counted |
| Parcels | the record's cost method (average cost for A200; first in, first out for shares, as the engine) | same |

Two numbers each, as the H82 scorecard (`PS.after_tax_engine`, `PS.after_tax_cmp0`) already does at 32%: **"kept"** (tax on income and realised gains paid to date; open positions untaxed) and **"sold"** (as if everything were sold at the month-end close, tax at the rates above). The comparator is taxed the same way in the same structure. The existing functions are given the rate and discount as parameters (today they are fixed at 32% and 50%); the 32% H82 readings are unchanged.

## 3. What is reported
Rows added to the `EMG2_18_SIM_BT_C6` block of the monthly scorecard, labelled **"information only — mostly luck at this stage"**: value after tax kept / sold, the same for A200, and the line minus A200, each at 47% and at 15%, after all costs, before fixed costs; and the same less the record's fixed-cost estimate (A$650 a year, `costs.fixed_aud_per_year`), as the app's headline. No ranking, no test statistic, no verdict. The owner's app may show the two figures side by side (a separate, app-only change).

## 4. Limits stated now
- Franking credits are refunded in super and largely offset tax personally; leaving them out understates super's advantage (`research_grand` s3 "two model limits").
- Super contributions, the transfer-balance cap, Division 293 / 296 and SMSF running costs (A$2,000–4,000 a year extra) are outside the reading. The SMSF break-even is about A$74k–129k in the strategy (`research_grand` s3); this reading does not change it.
- A 15% figure does not mean the owner can hold the strategy in super; the owner's current funds do not offer it.

## 5. Implemented now, and not (TODO)
Nothing is computed now. **TODO before the first month-end after registration**: in `paper_daily.py`, call the existing after-tax functions for `EMG2_18_SIM_BT_C6` and its A200 comparator with (0.47, 0.5) and (0.15, 1/3); hashed as a code ledger entry before its first run, with a test that every other line's output and every existing scorecard figure is byte-identical. Back-filling the months since 30 Nov 2026 from the stored fills, under this definition, is allowed (no decision depends on it).

## 6. Trial count
A change of reporting, not a trial (as `AMENDMENT_scoring_v2.md`). **N unchanged.**
