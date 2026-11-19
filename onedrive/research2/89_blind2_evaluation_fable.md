# 89. Blind build 2, judged: the design frozen on data to Dec 2020, run on Jan 2021 – Nov 2026

19 November 2026. Author: research agent (Fable), acting as evaluator. The builder never saw data after 31 Dec 2020; the evaluator changed nothing in the frozen rules.
Paper research only. General information, not financial or tax advice. Nothing here places an order. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. The ledger was not written.
Work folder: `scratchpad/deep89/` (`PROGRESS.md`, `code/`, `out/`). Every position with its outcome: `89_case_table_blind2.csv` (571 rows).

How to read the figures: A$10,000 put in once. "After tax" = after Interactive Brokers brokerage (A$6.60 an order), the modelled buy/sell spread, 32% tax on realised gains each June (halved for holdings over 12 months), and everything sold and taxed at the end. Fund = ASX 200 with dividends, held throughout, taxed once at the end. Each book was started in 12 different months (December 2020 to November 2021) and run to the last valuation (decision 30 Oct 2026, sold 2 Nov 2026); "12-start mean" is the average of those 12. Twins = 100 books with the same structure that pick at random from the same shares. Two data sets: the research panel (dead companies included) and a second vendor's file.

## 0. Answer first

**Keep the registered EMG2-18 rules for the mid-December go-live. The blind-built design did not beat the index and did not beat EMG2-18. No live amendment is drafted.**

| Jan 2021 – Nov 2026, A$10,000, all costs and tax (research panel / vendor file) | Blind-2 primary | Registered EMG2-18 | ASX 200 fund |
|---|---|---|---|
| Return a year after tax, mean of 12 start months | **+4.7% / +6.5%** | **+13.7% / +13.2%** | +7.1% |
| Range across the 12 start months | 0.7 to 7.7 / −0.7 to 10.5 | 12.4 to 14.8 / 11.2 to 16.0 | 6.2 to 7.9 |
| Start months ahead of the fund (of 12) | 3 / 7 | 12 / 12 | — |
| Start months in which the primary beat EMG2-18 | 0 / 0 | — | — |
| A$10,000 became (December 2020 start) | A$12,100 / A$16,600 | A$22,400 / A$20,200 | A$15,500 |
| Random twins beaten (of 100); twins' median return | 100 / 100; −4.9% / −5.5% | 100 / 100; −4.0% / −6.0% | — |
| Return with the 5 best holdings removed | −4.3% / −1.9% | +2.4% / +2.6% | — |
| Return with the spread doubled | +3.0% / +5.2% | +10.4% / +10.7% | — |
| Worst fall, month-end values (worst of 12 starts) | −41% / −39% | −38% / −35% | −12% |
| Orders a year; brokerage a year; spread a year | 42; A$278; A$114 | 115; A$757; A$620 | — |

1. **Against the index: no.** The primary made 4.7% a year (vendor file 6.5%) against the fund's 7.1%. It was ahead of the fund in 3 of 12 start months on the panel and 7 of 12 on the vendor file. The gap is well inside the noise (t −0.2 and 0.0), so "not shown to beat it" is the fair reading, not "shown to be worse".
2. **Against EMG2-18: no, clearly.** EMG2-18 was ahead in all 12 start months on both data sets, by 9.0 points a year on the panel and 6.7 on the vendor file. It was also ahead with the five best holdings removed and its worst fall was no deeper.
3. **The builder's own bar: failed.** Four of six conditions passed on both data sets (a, c, d, f). Condition (b), ahead of the fund after tax, failed on both. Condition (e), the family test, passed on the panel and failed on the vendor file.
4. **What did work, again: the signal picks better than chance.** The primary beat all 100 of its random twins on both data sets, by 9.6 and 12.0 points a year, still did with its five best holdings removed and with the spread doubled, and landed inside the builder's forecast range of +1 to +16. Random small companies from ranks 201–700 lost about 5% a year after costs at A$10,000, so the skill was spent climbing back to the fund's level. That is the same picture the builder reported in-sample.
5. **The builder's forecast was honest and close** (section 3): return forecast 7%, got 4.7–6.5%; orders 43, got 42; brokerage A$285, got A$278; worst fall −35% (−50% plausible), got −41%; chance of beating the fund 55%, and it lost narrowly.
6. **The choice between designs showed no skill, as the builder's own fold test warned.** The primary came 5th of its family of six on the panel. Two neighbours beat the fund on the panel: the three-measure momentum version (+12.1% / +10.6%) and the wider keep-zone version (+10.9% / +4.7%). Only the first did so on both data sets. Neither was the registered choice, so neither is a candidate. The builder's reasoned default D0 (top-300 companies) lost: −2.2% / −3.1%.
7. **A caution on EMG2-18's win.** EMG2-18's band was chosen in report 85 with 2018–2026 in view, so 2021–2026 is not unseen data for it. The blind design had no such help. This comparison says "nothing built blind has beaten it", for the second time (reports 87 and 89). It does not prove EMG2-18.
8. **Both books are in a fall now.** From 2 Mar 2026 to 2 Nov 2026 the EMG2-18 replay fell 38% (A$36,300 to A$22,600) and the primary 27%, while the fund rose. The go-live starts inside this fall.
9. **Trials.** N: 1,802 → 1,919 (report 87) → 2,026 (report 88) → 2,107 (the builder's 81-design grid) → **2,115** (8 judged books here: 7 frozen designs and EMG2-18 on the new start list). Twins, start months, the spread stress, the vendor cross-check and one accounting stress are not designs and are not counted.

## 1. What was done, in order

1. **Hashes checked before anything ran.** `sha256sum -c` on `blind2_build/out/hashes.txt`: the frozen rules, all the builder's code, and the four kit files all matched (`deep89/out/hash_check.txt`).
2. **Full panel built the same way as the kit.** Same source and code path as the kit (the survivorship-free panel of report 84, via `build87.py`), to 13 Nov 2026: 5,040 kit companies plus 555 listed later. Rows to 31 Dec 2020 are bit-for-bit identical to the kit (returns, closes, traded value, exclusion flags, first dates, the fund). The frozen primary and D0 re-run on the builder's 60 design books matched the builder's own table to 16 decimal places (`out/repro89.log`).
3. **The reading was written down before the judged run** (`PROGRESS.md`): the bar (a)–(f) as frozen, and "clearly beats EMG2-18" = ahead by at least 2 points a year on the 12-start mean, ahead in at least 9 of 12 starts, not behind with the five best holdings removed, worst fall no more than 5 points deeper, on both data sets.
4. **Run:** primary, its five family members, D0 and EMG2-18 (301–600 band, three-measure momentum, 18 names, sell outside the top fifth, age/price/traded-value filter), each from 12 start months, with 100 twins per book per start, at normal and doubled spread, on both data sets. Engine `eng88.py` unmodified.

## 2. The bar, line by line

| Condition (frozen in PREREG_BLIND2 section 7) | Research panel | Vendor file |
|---|---|---|
| (a) primary at or above the 75th percentile of twins | 100th: pass | 100th: pass |
| (b) primary ahead of the fund after tax, 12-start mean | 4.7 against 7.1: **fail** | 6.5 against 7.1: **fail** |
| (c) five best removed, above twins' median | −4.3 against −13.6: pass | −1.9 against −14.0: pass |
| (d) spread doubled, above twins' median | 3.0 against −6.1: pass | 5.2 against −6.5: pass |
| (e) family median ahead of twins; two-thirds of family ahead of fund | +12.3 pts; 4 of 6: pass | +10.9 pts; 2 of 6: **fail** |
| (f) lead over twins' median inside +1 to +16 | +9.6: pass | +12.0: pass |
| All | **fail** | **fail** |

Primary against EMG2-18: mean gap −9.0 / −6.7 points a year; ahead in 0 of 12 / 0 of 12; five-best-removed −4.3 against +2.4 / −1.9 against +2.6; worst fall −41% against −38% / −39% against −35%. Not a clear win on any line.

## 3. Forecast against outcome

| Builder's forecast (made from 2006–2020 only) | Forecast | Outcome (panel / vendor) |
|---|---|---|
| Return a year after tax | about 7% (window range −4 to +16) | 4.7% / 6.5% |
| Lead over twins' median | +8 points, 80% range +1 to +16 | +9.6 / +12.0 |
| Lead over the fund | about +1 point; 55% chance of beating it | −2.4 / −0.5 |
| Orders a year; brokerage | 43; A$285 | 42; A$278 / 40; A$263 |
| Worst fall | about −35%; −50% plausible | −41% / −39% |
| Share of winning profit from five best holdings | about 40% | 36% / 39% |

The method produced a calibrated forecast. It did not produce a design that beats the fund, and the builder said in advance that it probably could not tell (in-sample lead 2.8 points with a standard error of 2.3).

## 4. The family, the default and the comparators (12-start mean, % a year after tax)

| Book | Panel | Vendor | Ahead of fund (starts of 12) | Twins beaten | Worst fall | Orders a year |
|---|---|---|---|---|---|---|
| Primary: ranks 201–700, 52-week-high score, keep top 40%, hold 6 months | 4.7 | 6.5 | 3 / 7 | 100 / 100 | −41% / −39% | 42 |
| Family: band 101–500 | 0.1 | 1.5 | 0 / 0 | 100 / 100 | −37% / −41% | 38 |
| Family: three-measure momentum | 12.1 | 10.6 | 10 / 10 | 100 / 100 | −49% / −61% | 39 |
| Family: keep top 60% | 10.9 | 4.7 | 10 / 3 | 100 / 100 | −36% / −36% | 25 |
| Family: no minimum hold | 7.3 | 7.3 | 6 / 5 | 100 / 100 | −41% / −39% | 61 |
| Family: 13-month minimum hold | 7.6 | 5.1 | 6 / 5 | 100 / 100 | −42% / −44% | 26 |
| D0 default: top 300, three-measure momentum, hold 13 months | −2.2 | −3.1 | 0 / 0 | 2 / 0 | −64% / −56% | 21 |
| Registered EMG2-18 | 13.7 | 13.2 | 12 / 12 | 100 / 100 | −38% / −35% | 115 |
| ASX 200 fund | 7.1 | 7.1 | — | — | −12% | — |

Three things to take from the table. Every family member beat every one of its twins, so ranking by these scores inside small companies carries information. The result of one design swings by 5 to 20 points between start months (the 13-month-hold member ran from 0.8% to 20.2%), so no single-start number should be trusted. EMG2-18's spread across start months was only 12.4 to 14.8, because it trades so often that the starting month washes out.

## 5. Robustness

- **Removing the best holdings** (12-start mean, panel / vendor). Primary: best one removed 2.0 / 3.9; best three −1.3 / 0.9; best five −4.3 / −1.9. EMG2-18: 10.9 / 10.4; 5.8 / 5.9; 2.4 / 2.6. Fund 7.1. Both books fall below the fund once three winners are taken out. EMG2-18's five best (Azure Minerals, MTM, Clarity, Ora Banda, Dimerix on the panel) made A$14,100 of its A$19,700 net profit.
- **Vendor cross-check.** The verdict is the same on both data sets. The primary's December 2020 book differs a lot between them (A$12,100 against A$16,600) because one path bought Azure Minerals and the other did not; the 12-start means are closer (4.7 against 6.5). After 2024 the two data sets share a source, so the cross-check is independent mainly for 2021–2024.
- **Spread doubled.** Primary 3.0 / 5.2; EMG2-18 10.4 / 10.7. EMG2-18 pays about A$1,380 a year in brokerage and spread on a A$10,000 start and still led.
- **Payout rule for holdings that stopped trading (information only).** In the primary's December 2020 panel book four holdings were written to zero by the frozen rule, costing about A$2,900: AVZ Minerals and Firefinch (suspended in 2022, a real loss), New Energy Solar (a wind-up that returned capital, so zero is too harsh), and Trigg Minerals (last trade 6 Feb 2026, cause not verified, possibly a code change). Paying every such holding at its last close instead, an upper bound, lifts the primary's 12-start mean from 4.7% to 7.0%, level with the fund and still 6.7 points behind EMG2-18, which is unchanged at 13.7%. The verdict does not move. The four cases are worth a data check before any later use of the panel.

## 6. What the primary actually did (December 2020 start, research panel)

146 positions, 61 made money, the typical one lost 2%. Gross wins A$16,400, gross losses A$14,000, net A$2,500 before tax.

| Year to 1 December | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to 2 Nov) |
|---|---|---|---|---|---|---|
| Primary | +32% | −18% | −15% | +34% | +20% | −18% |
| EMG2-18 | +27% | −8% | +43% | +58% | +11% | −22% |
| Fund | +12% | +6% | 0% | +23% | +5% | +7% |

- **Best five:** Codan (bought A$8.90 Dec 2023, sold A$30.40 Dec 2025, +A$1,430), New Hope (A$1.97 to A$5.45, +A$1,420), SRG Global (+A$1,130), Tuas (+A$1,100), TCI (+A$910). Parcels of about A$600 cap what any winner can add.
- **Worst:** the four write-offs above (−A$860, −A$740, −A$740, −A$560), Hawsons Iron (−A$690), Qoria (−A$530).
- **Why sold:** 98 of 146 because the score left the keep zone (total +A$4,800; those shares then lost a median 6% over the next 12 months, so the sell rule was not throwing away winners); 19 paid out near their high when they stopped trading (takeovers, +A$1,000); 5 sold on the pinned-price rule (+A$2,000); 4 written to zero (−A$2,900); 18 still held at the end (−A$2,200).
- **Holding period:** the 20 positions held 13 months or more made A$8,000; everything else together lost A$5,500. In EMG2-18 the same split is starker: 167 positions held two months or less lost A$15,800 between them, and the profit came from a handful that ran.
- **The low point:** A$8,400 on 1 Nov 2023 (vendor file A$9,300), above the A$6,000 level of loss-limit rule L11. EMG2-18's replay never went below A$9,800 in this period.
- **2026:** 21 positions opened in 2026, 3 made money, total −A$3,200.

Each row of `89_case_table_blind2.csv` gives the code, company, buy and sell dates and prices, the traded-value rank and score at purchase, why it was bought and sold, profit, and what the share did in the 12 months after the sale, for the primary, EMG2-18 and D0.

## 7. What this means for the programme

1. **Go-live: EMG2-18 as registered.** No v2 amendment. `AMENDMENT_live_EMG2_18_v2.DRAFT.md` was not written because the pre-set conditions for it were not met.
2. **Expect the live book to depend on a few holdings and to fall hard at times.** Without its three best holdings EMG2-18 made 5.8% a year here, below the fund. It is 38% off its March 2026 peak in the replay.
3. **Two blind builds have now failed to pick a better design than EMG2-18, and both showed that picking between neighbouring designs from past data does not work at this sample size.** What repeats across 2006–2020 and 2021–2026 is narrower: momentum-type scores beat random choice inside small companies by roughly 10 points a year, and random small companies trail the fund by about that much after costs at A$10,000.
4. **One observation for the paper record only, not a proposal:** the three-measure momentum family member in the wider 201–700 band with a 6-month hold made 12.1% / 10.6% with 39 orders a year against EMG2-18's 13.7% / 13.2% with 115. It was not the registered pick, its worst fall was deeper (−49% / −61%), and choosing it now would be choosing after the result. It is close in spirit to the H6 paper twin already drafted in report 87.
5. **Record keeper:** N → 2,115; note the payout-rule data check (New Energy Solar, Trigg Minerals); no change to any live or shadow rule.

## 8. Limits

- One judged period of 5.8 years, ending inside a small-company fall. A 12-start mean smooths the start month but every book shares the same end date.
- The spread is a model; no real fills exist.
- EMG2-18 is not out of sample here (point 7 of section 0).
- The yearly table runs December to December because books are valued on the first session after each month-end decision.
- Twins use the same eligibility, slots and costs as their book; a twin of EMG2-18 keeps its buy filter and fast exit.
