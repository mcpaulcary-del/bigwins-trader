# Report 99 — A lower-turnover EMG2-18: does trading less leave more money? (and the same change on PAIR and BLIND3)

Fable, 20 November 2026. Research only: no live code, ledger, scheduled task or `/home/user/asx-trader` file was touched; no vendor request was made (data on disk only). Working folder `deep99/` (`PROGRESS.md`; `PREREG_99.md` and `PREREG_99b.md` hashed before any code ran; `FREEZE_99.md` hashed before any ASX run; `PREREG_99c.md` for one diagnostic outside the plan; hashes and logs in `out/`).

## 1. Answer

1. **Keep the current live rule (EMG2-18 with the protection) for the mid-December start. No live amendment is drafted.** The lower-turnover version chosen on overseas markets missed the bar set in advance on one line: on the research panel its worst fall was 5 points deeper (−51% against −46%). It passed every other line on both data sets.
2. **It is nevertheless the best book on paper in this report, and it should run on paper from 30 November.** The rule: *sell a holding only after six months, and only when it has dropped out of the top 40% of its band* (today: sell as soon as it leaves the top 20%). The protection switch is unchanged and overrides the six months. A$10,000, 12 start months from Dec 2017, to Nov 2026, after IBKR tiered brokerage, spread and tax:

| | Current EMG2-18_BT | Lower-turnover version | Difference |
|---|---|---|---|
| Ends with, research panel | A$28,277 | **A$34,520** | +A$6,243 |
| Ends with, vendor file | A$23,927 | **A$30,795** | +A$6,869 |
| Orders a year (panel / vendor) | 88 / 90 | 56 / 60 | −36% / −33% |
| Brokerage a year | A$505 / 516 | A$334 / 356 | −A$160 to −170 |
| Modelled spread a year | A$472 / 427 | A$321 / 313 | −A$115 to −150 |
| Worst fall | −46% / −53% | −51% / −42% | 5 points deeper / 11 shallower |
| Lowest value reached | A$5,769 / 5,890 | A$6,342 / 7,377 | higher |
| Start months ahead of the current rule | | 12 of 12 / 12 of 12 | |

3. **How much of the A$6,200–6,900 is real.** About A$275–320 a year is saved brokerage and spread: A$2,400–2,900 over the nine years. That part is arithmetic and will repeat. The other A$3,500–4,000 is which shares the rule happened to keep, most of it in 2019 and 2025, the same years for all 12 start months. That part is not evidence.
4. **Reasons not to act on it with real money yet:**
   - The overseas design was weak. The rule was the only one of 15 to pass the choice test, but it failed the fold test: leave out China, Malaysia or Korea and nothing passes.
   - Trading less helped where EMG2-18 loses money (Thailand, China, Malaysia: +A$1,700 to +4,600) and hurt where it makes money. In Taiwan (rank band), the one overseas market where EMG2-18 does well, it cut the result from A$42,985 to A$21,377.
   - Both parts of the rule (six-month hold, top-40% keep zone) had been seen on the ASX 2018–2026 before this test (reports 87 and 90). This was not a blind test on the ASX.
   - The same change inside the PAIR lost money (item 5).
5. **PAIR and BLIND3 (coordinator's addition).** The same change did not improve the PAIR: on the EMG2 half alone it ended A$5,695 (panel) and A$2,979 (vendor) below plain PAIR; on both halves A$745 and A$1,019 below. For BLIND3 (wider sell buffer and a six-month hold) it added A$4,502 on the panel and A$1,719 on the vendor file with 34 orders a year instead of 47, but was ahead in only 7 of 12 starts on the vendor file, so it does not meet the "better than its plain book" test either.
6. **Most money after costs, on paper:** the lower-turnover EMG2-18_BT (A$34,520 / 30,795), then plain PAIR (A$33,049 / 27,525). The ASX 200 fund on the same basis: A$18,586.

## 2. All books side by side

A$10,000, mean of 12 start months (Dec 2017 to Nov 2018), valued Nov 2026, everything sold and taxed, IBKR tiered brokerage max(A$5.55, 0.088%). Panel / vendor.

| Book | Ends with | Orders a year | Brokerage a year | Worst fall | At Dec 2025 | Five best holdings removed | Spread doubled | Starts ahead of current |
|---|---|---|---|---|---|---|---|---|
| ASX 200 fund | 18,586 | – | – | −36% | | | | |
| **EMG2-18_BT, current (corrected engine)** | 28,277 / 23,927 | 88 / 90 | 505 / 516 | −46% / −53% | 28,743 / 24,223 | 21,716 / 17,220 | 24,327 / 20,864 | – |
| **EMG2-18_BT, lower turnover (chosen)** | **34,520 / 30,795** | 56 / 60 | 334 / 356 | −51% / −42% | 33,022 / 27,857 | 27,534 / 24,381 | 31,201 / 27,472 | 12 / 12 |
| EMG2-18_BT, 12 names (information only) | 34,524 / 22,931 | 65 / 64 | 383 / 370 | −45% / −63% | 36,467 / 23,706 | 24,751 / 15,420 | 29,036 / 19,766 | 12 / 0 |
| EMG2-18 plain (no protection) | 28,067 / 23,731 | 110 / 104 | 613 / 575 | −56% / −58% | 35,028 / 31,254 | 15,712 / 12,722 | 22,031 / 19,852 | |
| EMG2-18 plain, lower turnover (diagnostic) | 34,914 / 28,586 | 60 / 57 | 332 / 318 | −59% / −59% | 39,793 / 29,792 | | | |
| PAIR plain | 33,049 / 27,525 | 132 / 116 | 735 / 646 | −47% / −54% | 35,034 / 29,576 | 23,905 / 18,630 | 29,205 / 25,314 | 12 / 12 |
| PAIR, lower turnover on the EMG2 half | 27,355 / 24,546 | 87 / 84 | 481 / 467 | −53% / −51% | 27,969 / 25,803 | 20,532 / 18,021 | 24,983 / 23,419 | 6 / 8 |
| PAIR, lower turnover on both halves | 32,305 / 26,506 | 77 / 74 | 427 / 410 | −50% / −48% | 32,161 / 26,566 | 24,710 / 19,790 | 30,594 / 23,433 | 10 / 11 |
| BLIND3 plain | 27,213 / 21,010 | 47 / 48 | 258 / 267 | −42% / −44% | 25,760 / 20,529 | 20,383 / 15,031 | 25,163 / 17,641 | |
| BLIND3, lower turnover | 31,715 / 22,729 | 34 / 34 | 187 / 189 | −43% / −42% | 29,703 / 21,103 | 22,668 / 16,645 | 30,625 / 22,323 | 9 / 4 |

Other checks:

- **Random twins (same structure, random share list), 100 per start month:** the lower-turnover EMG2-18_BT beat 100 of 100 on both data sets (twins' middle A$15,835 / 16,038); PAIR versions 100 of 100; BLIND3 lower turnover 99 / 100.
- **Range across the 12 starts (panel):** current 26,875–29,367; lower turnover 30,637–36,105. Vendor: 23,376–25,096 against 28,664–32,091. The start months share the same years, so "12 of 12" is one result seen 12 times, not 12 confirmations.
- **2006–2017, research panel (information; the six-month hold was first found on this decade):** current 11,819; lower turnover 22,746 (fund 18,081); PAIR plain 20,718; PAIR lower turnover 33,610 (EMG2 half) and 31,024 (both); BLIND3 23,458 and 27,372.
- **Where the gain came from (Dec-2017 start, panel):** end 2019 A$10,484 against A$8,765; end 2025 A$35,083 against A$29,266. The deeper percentage fall on the panel is March 2020 measured from a higher October 2019 peak (A$14,555 to A$7,078, against A$10,801 to A$5,769). In 2026 it fell 25% against 32%.
- **Tax and the 12-month discount:** the lower-turnover book's holdings lasted a median of about 125 days (61 for the current rule). Almost no gain earned the 12-month discount in either, because the protection switch sells everything at each step-aside. Versions built to reach 12 months (H12) did worse overseas (item 4 of section 3).
- **The 12-name version shows the size of the noise.** It was A$6,247 ahead on the panel and A$995 behind on the vendor file, from the same rule. A difference of a few thousand dollars on one data set is not a finding.

## 3. How the rule was chosen (overseas only, frozen before the ASX)

Fifteen candidates in five families were written down first: exit buffers (sell below the top 30/40/50%), minimum holds (3/6/12 months), quarterly refresh, fewer names (15/12), replace-on-a-margin (two), and four fixed combinations. Each is the current protected rule plus that one change.

Design markets: Thailand, Malaysia, China (two band versions), Korea main board (two), Taiwan main board (two): eight market-versions, five markets. The raw files for the UK, US, Sweden, France, Germany, KOSDAQ and Taiwan's second board are gone, so those were skipped.

Choice test: at least 30% fewer orders (median), more money than the current rule in more than half the market-versions, worst fall no more than 2 points deeper; then best median rank on money.

| Candidate | Median rank of 16 | Orders, share of current | More money than current in | Worst fall, points | Passes |
|---|---|---|---|---|---|
| Six-month hold + top-40% keep zone | 4.0 | 65% | 6 of 8 | −1.7 | **yes** |
| Six-month hold | 4.5 | 68% | 5 of 8 | −2.6 | no (fall) |
| Margin 0.40 | 6.0 | 82% | 4 of 8 | +2.6 | no |
| 12 names | 6.5 | 74% | 6 of 8 | +0.4 | no (orders) |
| Top-50% exit buffer | 7.0 | 80% | 5 of 8 | +3.6 | no (orders) |
| 12-month hold | 10.0 | 48% | 4 of 8 | +2.0 | no (money) |
| Quarterly refresh | 9.5 | 81% | 5 of 8 | +0.3 | no (orders) |
| Current rule | 12.0 | 100% | – | 0 | – |

1. One candidate passed. No single change cut orders by 30% without a cost.
2. Fold test (leave one market out): the chosen rule passes in 2 of 5 folds. **Not robust.** Written into the freeze before the ASX run.
3. Exit buffers and margins alone cut only 10–20% of orders, because the switch and the buy side still trade.
4. Holding for the 12-month tax discount cut orders in half and ended with less money than the current rule in four of eight market-versions. The signal fades well inside a year.
5. Applied to BLIND3 and the PAIR overseas, the change gave more money than the plain book in 7 of 8 (BLIND3) and 6 of 8 (PAIR) market-versions, again mainly where the plain book loses money.

## 4. The bar, as fixed in advance

Chosen rule against the current EMG2-18_BT, on both data sets.

| Line | Panel | Vendor |
|---|---|---|
| At least A$1,000 more | +A$6,243 ✓ | +A$6,869 ✓ |
| At least 30% fewer orders | −36% ✓ | −33% ✓ |
| Worst fall not deeper | −51.4% against −46.2% ✗ | −42.2% against −53.3% ✓ |
| Ahead in 8 of 12 starts | 12 ✓ | 12 ✓ |

Not met. For PAIR and BLIND3 the test "at least A$1,000 more than its plain book, 8 of 12 starts, fall not deeper, on both data sets" was failed by all three new rules.

## 5. Recommendation

| Item | Action |
|---|---|
| Live book, mid-December | **No change.** Registered EMG2-18_BT as it stands. |
| Paper line | Register `EMG2_18_SIM_BT_C6` from 30 Nov 2026 (draft: `deep99/AMENDMENT_shadow_EMG2_18_BT_C6.DRAFT.md`). It is the registered COMBO sell rule under the registered switch; no new parameter. Its order count and brokerage are facts from month one; its value is mostly luck for at least a year. |
| Review | December 2027: a live proposal needs 12 paper months not behind, 30% fewer orders on paper, the live book's measured spread within 1.5 times the model, and a new pre-registered test. |
| PAIR, BLIND3 | No change to either paper line. The lower-turnover change is not recommended for them. |
| 12-name book | Not recommended: opposite results on the two data sets, and A$833 parcels would exceed the live A$800 per-buy limit. |

## 6. Limits

- The replay retries a stuck share at the next month-end; the live system's daily re-offer (BF-D34) is not modelled. This affects the current and the new rule alike.
- Overseas runs use A$10,000 with A$ brokerage on local prices; no currency, stamp duty or withholding tax.
- Costs are modelled; no real fill has yet been compared with the spread model. Cash earns 0%.
- The two ASX data sets share most of their history; agreement between them is weaker evidence than it looks.
- Trials: 15 design candidates, 3 PAIR/BLIND3 rules, 1 diagnostic = 19. **N 2,909 → 2,928** (ledger not written).
- Files: `deep99/out/design_read.log`, `ovb_read.log`, `readj_panel.log`, `readj_vendor.log`, `judgec.log`, `dd_panel.log`, `table_*.csv`, `starts_*.csv`, `twins_*.csv`.
