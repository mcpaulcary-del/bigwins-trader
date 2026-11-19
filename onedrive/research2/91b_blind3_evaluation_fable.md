# 91b. Blind build 3, judged: the design frozen on data to Dec 2017, run on Jan 2018 – Nov 2026

19 November 2026. Author: research agent (Fable), acting as evaluator. The builder never saw data after 29 Dec 2017 and was given no list of strategies. The evaluator changed nothing in the frozen rules.
Paper research only. General information, not financial or tax advice. Nothing here places an order. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. The ledger was not written.
Work folder: `scratchpad/deep91/` (`PROGRESS.md`, `code/`, `out/`). Every position with its outcome: `91b_case_table_blind3.csv` (1,707 rows, seven books).

How to read the figures: A$10,000 put in once. "After tax" = after Interactive Brokers brokerage (A$6.60 an order), the modelled buy/sell spread, 32% tax on realised gains each June (halved for parcels held 367 days or more), and everything sold and taxed at the end. Fund = ASX 200 with dividends, held throughout, taxed once at the end. Each book was started in 12 different months (December 2017 to November 2018) and run to the last valuation (decision 30 Oct 2026, sold 2 Nov 2026); "12-start mean" is the average of those 12. Twins = 100 books with the same structure that pick at random from the same shares. Two data sets: the research panel (dead companies included) and a second vendor's file. All books, including EMG2-18, use the blind-3 kit's accounting (smooth spread curve, 367-day discount, order capped at 5% of traded value, worst fall measured on daily values).

## 0. Answer first

**Keep the registered EMG2-18 rules. No v2 amendment is drafted: the blind design tied EMG2-18 on return and did not clear the pre-set margin. But this is the first blind design that beat the fund and its random twins on unseen data, on both data sets, and it is a different kind of book from EMG2-18.**

| Jan 2018 – Nov 2026, A$10,000, all costs and tax (research panel / vendor file) | Blind-3 primary | Registered EMG2-18 | ASX 200 fund |
|---|---|---|---|
| Return a year after tax, mean of 12 start months | **+12.1% / +8.6%** | **+12.5% / +9.9%** | +7.7% |
| Range across the 12 start months | 8.7 to 14.7 / 4.7 to 10.3 | 11.5 to 14.3 / 9.0 to 11.9 | 7.2 to 8.4 |
| Start months ahead of the fund (of 12) | 12 / 10 | 12 / 12 | — |
| Start months in which the primary beat EMG2-18 | 5 / 3 | — | — |
| A$10,000 became (December 2017 start) | A$29,700 / A$21,300 | A$26,200 / A$21,500 | A$18,800 |
| Random twins beaten (of 100); twins' median return | 94 / 99; +2.0% / +0.4% | 100 / 100; −0.1% / −2.9% | — |
| Return with the 5 best holdings removed | +8.3% / +4.3% | +4.8% / +1.7% | — |
| Return with the spread doubled | +10.9% / +6.7% | +9.4% / +8.1% | — |
| Worst fall, daily values (worst of 12 starts) | −44% / −46% | −58% / −61% | −36% |
| Lowest account value (worst of 12 starts) | A$7,000 / A$6,200 | A$4,200 / A$4,600 | — |
| Orders a year; brokerage a year; spread a year | 46; A$307; A$101 | 110; A$727; A$623 | — |

1. **Against the index: ahead, not proven.** The primary made 12.1% a year on the panel and 8.6% on the vendor file against the fund's 7.7%. It led in 12 and 10 of the 12 start months. The lead is 4.4 and 1.0 points a year. On monthly returns the December 2017 panel book's lead has a t-value of 1.1, so one period cannot separate it from luck. The builder said the same in advance (uncertainty about 7 points a year). At a doubled spread it stayed ahead on the panel (10.9%) and fell behind on the vendor file (6.7%).
2. **Against its random twins: clearly ahead.** It beat 94 and 99 of 100 twins, by 10.1 and 8.3 points a year. With the five best holdings removed from every book it beat 98 and 99. This is the sharper test and it passed on both data sets.
3. **The builder's own bar: passed on the panel, failed by one line on the vendor file.** Conditions (a), (b), (c), (d) and (f) passed on both. Condition (e) needs four of the five family members ahead of the fund. The panel had four. The vendor file had three, because the 18-name member made 7.1% against 7.7%. The bar required both data sets, so the formal reading is "not passed".
4. **Against EMG2-18: a tie on return, so no amendment.** The gap was −0.4 points a year on the panel and −1.2 on the vendor file. The primary led in 5 and 3 of 12 starts. The pre-set condition was a lead of at least 2 points in at least 9 starts on both data sets. On the other two lines of that condition the primary was better: five-best-removed 8.3% against 4.8% (4.3 against 1.7), and worst fall 14 to 15 points shallower.
5. **This comparison is not fair to the blind design, and cannot be made fair.** 2018–2026 is not unseen data for EMG2-18. Its band was chosen in report 85 with these years in view. The blind design saw none of them. A tie under those terms favours the blind design more than the numbers show, but by an amount nobody can measure.
6. **It is a different family from EMG2-18.** Both rank by past price rise. Otherwise they differ: the primary buys calm shares among the 400 most traded (typical traded-value rank 161), EMG2-18 buys ranks 301–600 (typical 397). Only 7% of the primary's holding-months were also EMG2-18 holdings. Their monthly leads over the fund have a correlation of 0.33. The primary trades 46 times a year against 110 and paid A$1,500 tax over nine years against A$9,300.
7. **The builder's forecast was honest and too modest** (section 3). Lead over twins: forecast +5.8 (range −1.1 to +12.8), got +10.1 / +8.3. Return: forecast +2.5%, got 12.1% / 8.6%. Chance of beating the fund: 40%, and it did.
8. **The choice between neighbours again showed no skill.** The primary came third of five in its family on both data sets. The 12-month-lookback member (14.7% / 12.2%) and the wider-buffer member (14.5% / 11.3%) were better. The top-200 member (3.8% / 4.8%) and the builder's reasoned default D0 (0.9% / 0.1%) lost to the fund and were no better than their twins. The edge sat in ranks 201–400; inside the top 200 there was none.
9. **Trials.** N: 2,192 → 2,340 (the builder's 148-design grid) → **2,347** (seven judged books here: six frozen designs and EMG2-18 on the new start list under kit accounting). Twins, start months, halves, stresses and the vendor cross-check are not designs and are not counted.

## 1. What was done, in order

1. **Hashes checked before anything ran.** `sha256sum -c` on `blind3_build/out/hashes.txt` (rules, code, outputs, kit, briefing) and on `out/hashes_A.txt` (the plan hashed before the builder's first run). All matched (`deep91/out/hash_check.txt`). They were checked again at the end and still matched.
2. **Full panel built the same way as the kit.** Same source and code path (the survivorship-free panel of report 84, via `build87.py`), to 13 Nov 2026: the kit's 4,658 companies in the kit's order under the kit's labels, plus 937 listed later. Rows to 29 Dec 2017 are bit-for-bit identical to the kit for returns, closes and traded value. The exclusion flags, first dates, delisting classes and the fund are identical too (`out/build91.log`).
3. **The builder's in-sample books reproduced exactly.** The frozen primary, its four family members and D0, run on a truncation of my panel, match the builder's table on all 24 books and 22 statistics with a largest difference of zero. The primary's 30 twins match too (`out/repro91.log`).
4. **The reading was written down before the judged run** (`PROGRESS.md`): the bar (a)–(f) as frozen; the family for (e) is the primary and its four neighbours; "clearly beats EMG2-18" as in report 89; the payout bounds; the two halves; the test for "same family".
5. **Run.** Primary, four family members, D0 and EMG2-18, each from 12 start months, with 100 twins per book per start, at normal and doubled spread, on both data sets. The kit's engine `acct3.py` and tools were used unmodified. EMG2-18 was run through the strategy wrapper that report 90 validated against the old engine. Its December 2017 book gives 11.54% here, the figure in report 90.
6. **Look-ahead check on the judged period.** The kit's as-of audit was rerun for the primary and D0 on 2018–2026: every sampled decision was identical with later rows blanked (`out/audit91.log`).

One disclosure: a timing test before the run showed me one random twin's return (6.7% a year). No design number was seen before the reading was fixed.

## 2. The bar, line by line

| Condition (frozen in PREREG_BLIND3 section 6) | Research panel | Vendor file |
|---|---|---|
| (a) primary at or above the 75th percentile of twins | 94th: pass | 99th: pass |
| (b) primary ahead of the fund after tax, 12-start mean | 12.1 against 7.7: pass | 8.6 against 7.7: pass |
| (c) five best removed, above twins' median | 8.3 against −4.8: pass | 4.3 against −5.9: pass |
| (d) spread doubled, above twins' median | 10.9 against 0.9: pass | 6.7 against −0.4: pass |
| (e) family median ahead of twins; two-thirds of family ahead of fund | +10.1 pts; 4 of 5: pass | +8.3 pts; 3 of 5: **fail** |
| (f) lead over twins' median inside −1.1 to +12.8 | +10.1: pass | +8.3: pass |
| All | pass | **fail** |

Primary against EMG2-18 (report 89's definition of a clear win, all four lines needed on both data sets):

| Line | Research panel | Vendor file |
|---|---|---|
| Mean gap at least +2 points a year | −0.4: fail | −1.2: fail |
| Ahead in at least 9 of 12 starts | 5: fail | 3: fail |
| Not behind with five best removed | 8.3 against 4.8: pass | 4.3 against 1.7: pass |
| Worst fall no more than 5 points deeper | −44% against −58%: pass | −46% against −61%: pass |

## 3. Forecast against outcome

| Builder's forecast (made from 2006–2017 only) | Forecast | Outcome (panel / vendor) |
|---|---|---|
| Lead over twins' median | +5.8 points, 80% range −1.1 to +12.8 | +10.1 / +8.3 |
| Return a year after tax | about +2.5% | 12.1% / 8.6% |
| Lead over the fund | about −2 points; 40% chance of beating it | +4.4 / +1.0 |
| Orders a year; brokerage | 48; A$320 | 46; A$307 / 48; A$318 |
| Worst fall, daily values | about −30% (in-sample −20% to −54%) | −38% to −44% / −41% to −46% |
| Share of winning profit from five best holdings | about 55% | 31% / 35% |

The return forecast was low by 9.6 points on the panel. Three things account for it. The fund made 7.7% instead of the 5.0% assumed. Random twins trailed the fund by 5.7 points instead of 8.1. The lead over twins was 10.1 instead of the shrunk 5.8, close to the unshrunk in-sample 11.7. The forecast range for the lead held. The fall was deeper than forecast because of March 2020.

## 4. The family, the default and the comparators (12-start mean, % a year after tax)

| Book | Panel | Vendor | Ahead of fund (starts of 12) | Twins beaten | Worst daily fall | Orders a year |
|---|---|---|---|---|---|---|
| Primary: top 400, calmer half, 15 names, 6-month rise | 12.1 | 8.6 | 12 / 10 | 94 / 99 | −44% / −46% | 46 |
| Family: 12-month rise | 14.7 | 12.2 | 12 / 12 | 97 / 100 | −50% / −51% | 36 |
| Family: top 200 only | 3.8 | 4.8 | 0 / 0 | 54 / 71 | −43% / −39% | 45 |
| Family: sell when 60 rank above | 14.5 | 11.3 | 12 / 12 | 97 / 100 | −45% / −46% | 41 |
| Family: 18 names | 10.4 | 7.1 | 12 / 3 | 94 / 96 | −43% / −44% | 54 |
| D0 default: top 200, 12-month rise, no calm screen | 0.9 | 0.1 | 0 / 0 | 19 / 17 | −56% / −53% | 34 |
| Registered EMG2-18 | 12.5 | 9.9 | 12 / 12 | 100 / 100 | −58% / −61% | 110 |
| ASX 200 fund | 7.7 | 7.7 | — | — | −36% | — |

- Four of the five family members beat at least 94 of their 100 twins on both data sets. The top-200 member did not.
- Random twins of the primary made 2.0% / 0.4% a year, 5.7 and 7.3 points behind the fund. Only 16 and 3 of 100 twins beat the fund. A A$10,000 book of 15 parcels pays that much in brokerage and short-term tax before any skill shows. The builder measured the same shortfall in-sample (8.1 points).
- D0 lost again, as it did in blind build 2. In 2026 its December 2017 book fell 42%.

## 5. Robustness

- **Removing the best holdings** (12-start mean, panel / vendor). Primary: best one removed 11.1 / 7.6; best three 9.6 / 5.6; best five 8.3 / 4.3. EMG2-18: 10.8 / 8.1; 7.6 / 4.7; 4.8 / 1.7. Fund 7.7. On the panel the primary stays ahead of the fund with five winners removed. On the vendor file it falls behind once two or three are removed. EMG2-18 falls behind the fund at three removed on both.
- **Spread doubled.** Primary 10.9 / 6.7; EMG2-18 9.4 / 8.1. The primary pays about A$100 a year in modelled spread and EMG2-18 about A$620, so EMG2-18 depends far more on a spread model that no real fill has tested.
- **The two halves** (briefing section 8; 12 starts each).

| 12-start mean, panel / vendor | Primary | Twins' median; primary's percentile | EMG2-18 | Fund |
|---|---|---|---|---|
| First half: Dec 2017–Nov 2018 starts to May 2022 | 9.1 / 4.7 | 4.1 / 1.5; 71st / 72nd | 9.0 / 6.8 | 7.7 |
| Second half: May 2022–Apr 2023 starts to Nov 2026 | 14.6 / 12.2 | 1.7 / 0.8; 96th / 95th | 18.4 / 18.0 | 8.4 |

  The first half is weak evidence: ahead of the fund on the panel, behind on the vendor file, and below the 75th percentile of twins on both. Most of the result comes from 2019 and from 2023–2025.
- **Vendor cross-check.** The verdict is the same on both data sets. The primary's 12-start mean differs by 3.5 points (12.1 against 8.6). The data agree where the trades agree: on the 94 holdings bought and sold in the same months in both December 2017 books, returns differ by 0.5 points on average. But only 101 of the panel book's 217 purchases were also made in the vendor book. Small differences in traded-value ranks and volatility move a share across the top-400 line or the calm-half line, and the books then follow different paths. The vendor book held Codan and Fortescue for less profit and made nothing on Regis Healthcare and MMA Offshore. The spread between data sets is therefore a second measure of path luck, about as large as the lead over the fund.
- **Payout bounds for holdings that stopped trading.** The panel has no delisting reason after April 2020. The frozen rule pays such a holding at its last close if that was within 30% of its 250-session high, otherwise zero.
  - Upper bound (every such holding paid at last close): primary 12.1 / 8.6, unchanged. EMG2-18 12.5 / 11.7.
  - Lower bound (every such holding paid zero): primary 1.2 / −3.4, its twins −1.9 / −4.6 (74th / 63rd percentile); EMG2-18 −0.3 / −3.8.
  - The lower bound is not a plausible case for these books. About nine to eleven holdings a book are affected. The December 2017 panel book had 14 payouts, 12 of them with no recorded reason, and all 14 are known cash takeovers: Tox Free, Mantra, APN Outdoor, Scottish Pacific, Trade Me, AusNet, Senex, Crown, Tassal, Blackmores, Estia, MMA Offshore, Gold Road and SG Fleet. None was written to zero by the frozen rule. A calm, liquid share that stops trading near its high is nearly always a takeover. The bound shows how much the result rests on that being true: about 11 points a year.
- **One small data point against the panel.** BHP, held May to August 2022, shows −19.7% on the panel and −10.1% on the vendor file. The Woodside shares BHP distributed in June 2022 appear to be missing from the panel's return. This understates the panel result slightly and is worth a data check.

## 6. What the primary actually did (December 2017 start, research panel)

217 holdings, 70 made money, the typical one lost 4%. Gross wins A$37,200, gross losses A$16,000, net A$21,300 before tax of A$1,500.

| Year to the first session of December | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to 2 Nov) |
|---|---|---|---|---|---|---|---|---|---|
| Primary | +1% | +61% | +8% | +3% | −16% | 0% | +51% | +32% | 0% |
| EMG2-18 | −20% | +3% | +25% | +41% | −10% | +44% | +60% | +13% | −22% |
| Fund | −1% | +25% | −1% | +14% | +6% | 0% | +23% | +5% | +7% |

- **Best five:** Codan (bought A$12.81 Aug 2024, sold A$43.33 May 2026, +A$3,230), Fortescue (A$5.98 Mar 2019 to A$22.68 Mar 2021, +A$2,960), Pro Medicus (+A$1,810), Jumbo Interactive (+A$1,770), Regis Healthcare (+A$1,710). Together 31% of winning profit.
- **Worst five:** Yancoal (−A$630), Nickel Industries (−A$540), Perenti (−A$480), Sims (−A$375), Insignia (−A$370). No holding was written to zero.
- **Holding period decides the result.** The 52 holdings kept 367 days or more made A$33,000, and 50 of them were winners. The 165 sold sooner lost A$11,700 between them. The rule that keeps a profitable holding until day 367 and sells a losing one at once did what the builder designed it to do: 89% of winning profit was taxed at the halved rate. EMG2-18 held nothing for 367 days. Its 345 holdings of three months or less lost A$23,900 and its tax bill was A$9,300.
- **How holdings ended:** 189 sold on rank or on leaving the top 800 (+A$15,500; those shares then rose a median 2% in the next 12 months, so the sell rule was not throwing away winners); 14 taken over (+A$2,400); 14 still held at the end (+A$3,300).
- **Where the profit came from, by traded-value rank at purchase:** ranks 1–100: 57 purchases, +A$5,900. Ranks 101–200: 78, +A$1,800. Ranks 201–300: 44, +A$4,500. Ranks 301–400: 38, +A$9,050. The smaller half of the universe made 64% of the profit from 38% of the purchases, which is why the top-200 family member failed.
- **Falls.** Lowest value A$8,960 on 24 Dec 2018. In February–March 2020 the book fell 38% in a month (A$17,700 to A$10,900) against the fund's 36%. The calm-share screen did not protect it in a crash. EMG2-18's replay fell to A$4,290 on the same day.
- **2026.** The primary peaked at A$33,900 on 3 June, was at A$29,300 on 23 October (−14%) and A$30,350 at the end. EMG2-18 fell from A$41,700 on 2 March to A$25,070 on 30 July (−40%) and ended at A$26,470. The two books did not fall together this year.

Each row of `91b_case_table_blind3.csv` gives the book, code, company, buy and sell dates and prices, days held, cost, proceeds, profit, how the holding ended, its traded-value rank at purchase, and what the share did in the 12 months after the sale.

## 7. Did a builder with no menu find the same family?

The test was fixed before the run: overlap of holdings, the rank band held, co-movement of monthly leads, and the rules themselves.

| December 2017 books, research panel | Blind-3 primary | EMG2-18 |
|---|---|---|
| Idea | Shares that rose most over months 6 to 1, among the calmer half of the 400 most traded | Three-measure momentum among ranks 301–600 |
| Traded-value rank at purchase: middle; 10th to 90th percentile | 161; 34 to 341 | 397; 317 to 546 |
| Sell rule | 30 names outrank it; winners kept to day 367 | Leaves the top fifth; checked monthly |
| Typical holding period | 152 days | 63 days |
| Orders a year | 46 | 110 |
| Share of the primary's holding-months also held by EMG2-18 | 7% | — |
| Companies ever held; held by both at some time | 156 | 50 of those |
| Correlation of monthly lead over the fund | 0.33 | — |

**Same broad idea, different book.** Left alone, the builder wrote four families from published findings (momentum, low volatility, nearness to the high with a trailing stop, and momentum inside calm shares) and its choice rule landed on the last. So it reached price momentum independently, as EMG2 did. It applied it to larger, calmer companies, traded less than half as often, and built the tax rule into the exits. The two books share few holdings and move together only loosely. The one finding they share is that momentum paid in the smaller companies and not in the largest 200.

## 8. Verdict

- **(a) Against the index.** Ahead on both data sets and in 22 of 24 start-month books, with a wide margin over random twins. Not proven: the lead over the fund is within one period's noise, the first half was weak, the vendor result is behind the fund at a doubled spread, and the formal bar failed on one family member on the vendor file.
- **(b) Against EMG2-18.** A tie on return (−0.4 / −1.2 points a year), with less dependence on a few winners, a shallower worst fall, 58% fewer orders and a sixth of the spread cost. Not a clear win on the pre-set definition, so **EMG2-18 stays and no v2 amendment was drafted** (`AMENDMENT_live_EMG2_18_v2.DRAFT.md` not written). A fair head-to-head is impossible because 2018–2026 is not unseen for EMG2-18. The judgement of the blind design rests on (a) and on its twins.
- **(c) Family.** Different: mid-to-large calm momentum with slow, tax-aware exits, against small-company band momentum with fast exits. Low overlap.

## 9. What this means for the programme

1. **Go-live: EMG2-18 as registered.** Nothing here changes a live or shadow rule.
2. **For the owner to decide, not a proposal made here:** the blind-3 primary is a candidate for a paper twin beside EMG2-18. Reasons: it is the only design in the programme whose judged period was fully unseen and that finished ahead of the fund; it shares 7% of holdings with EMG2-18; and it did not fall with EMG2-18 in 2026. Reasons against: the builder's choice rule had no skill, two family members were better, and the first half was weak. If it is added, it should be the frozen primary exactly, not the better-looking 12-month member, which would be choosing after the result.
3. **The blind method worked better the third time, and one result does not show why.** The differences from builds 1 and 2 were no strategy menu, a 2017 cut-off giving nine judged years, and a builder who designed for low turnover and tax from the start. The lead over twins landed in the upper half of the builder's forecast range and the fund comparison is within noise, so some of the result is likely luck.
4. **What repeats across all three blind builds:** signals beat random choice by about 8 to 12 points a year; random books at A$10,000 trail the fund by 6 to 12 points after costs and tax; picking between neighbouring designs from past data does not work; the reasoned default loses.
5. **Not run here, for the reviewer if wanted:** the builder's other 142 grid designs on 2018–2026. They would show whether the in-sample ranking carried any information. Each would count as a trial.
6. **Record keeper:** N → 2,347; data checks on BHP's June 2022 distribution in the panel; no change to any rule.

## 10. Limits

- One judged period of 8.9 years. All 12 start months share the same end date and most of the same years.
- The spread is a model; no real fills exist. The primary's spread cost is small, so this matters less for it than for EMG2-18.
- EMG2-18 is not out of sample here (section 0, point 5).
- The panel has no delisting reasons after April 2020. The payout rule's treatment of those holdings was checked by name for one book only.
- The two data sets share a source after 2024, so the cross-check is independent mainly for 2018–2024.
- EMG2-18's figures here use the blind-3 kit's accounting, so they differ slightly from reports 87–90 (11.54% against 11.34% for the December 2017 book).
- Twins use the same universe, slots, sell buffer, tax-wait rule and costs as their book. A twin of the primary draws from the whole top 400, not the calm half, as the builder registered.
- The yearly table runs December to December because books are valued on the first session after each month-end decision.
