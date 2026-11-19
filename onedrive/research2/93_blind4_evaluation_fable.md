# 93. Blind build 4, judged: the two-member dividend set frozen on data to Dec 2017, run on Jan 2018 – Nov 2026

19 November 2026. Author: research agent (Fable), acting as evaluator. The builder never saw data after 29 Dec 2017. The evaluator changed nothing in the frozen rules.
Paper research only. General information, not financial or tax advice. Nothing here places an order. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. The ledger was not written.
Work folder: `scratchpad/deep93/` (`PROGRESS.md`, `code/`, `out/`). Every position of the December 2017 books with its outcome and its inferred dividend figures: `93_case_table_blind4.csv` (140 rows, four books).

How to read the figures: A$10,000 put in once. "After tax" = after brokerage (A$6.60 an order), the modelled buy/sell spread, 32% tax on realised gains each June (halved for parcels held 367 days or more), and everything sold and taxed at the end. Fund = ASX 200 with dividends, held throughout, taxed once at the end. Each book was started in 12 different months (December 2017 to November 2018) and run to the last valuation (decision 30 Oct 2026, sold 2 Nov 2026); "12-start mean" is the average of those 12. Twins = 100 books with the same structure that pick at random from the same shares. Two data sets: the research panel (dead companies included) and a second vendor's file. Figures are given as panel / vendor.

## 0. Answer first

**The set lost to the fund on both data sets. It is not a candidate to replace anything, and it does not earn a paper line. Keep the registered EMG2-18 rules; no v2 amendment is drafted.**

| Jan 2018 – Nov 2026, A$10,000, all costs and tax (panel / vendor) | Blind-4 set | Member 1 alone (the pick) | Member 2 alone | D0 = ALT (low volatility) | BLIND3 primary | EMG2-18 | Fund |
|---|---|---|---|---|---|---|---|
| Return a year after tax, 12-start mean | **+5.5% / +6.0%** | +4.5 / +5.6 | +6.4 / +7.0 | +6.2 / +6.3 | +12.1 / +8.6 | +12.5 / +9.9 | +7.7% |
| Range over the 12 starts | 2.6 to 7.8 / 3.8 to 8.9 | 1.7 to 10.4 / 3.9 to 11.0 | 4.3 to 9.6 / 5.0 to 8.7 | 5.2 to 7.0 / 5.3 to 7.7 | 8.7 to 14.7 / 4.7 to 10.3 | 11.5 to 14.3 / 9.0 to 11.9 | 7.2 to 8.4 |
| Starts ahead of the fund (of 12) | **1 / 3** | 1 / 1 | 2 / 3 | 0 / 0 | 12 / 10 | 12 / 12 | — |
| A$10,000 became (December 2017 start) | A$17,000 / A$19,400 | A$13,600 / A$14,300 | A$18,500 / A$19,400 | A$16,200 / A$16,700 | A$29,700 / A$21,300 | A$26,200 / A$21,500 | A$18,800 |
| Twins' median return; twins beaten (of 100) | +4.5 / +4.2; **65 / 82** | +4.4 / +3.8; 51 / 74 | +4.5 / +4.1; 82 / 89 | +5.8 / +5.7; 63 / 70 | +2.0 / +0.4; 94 / 99 | −0.1 / −2.9; 100 / 100 | — |
| Lead over twins' median, points a year | **+1.0 / +1.9** | +0.1 / +1.9 | +1.9 / +2.9 | +0.3 / +0.6 | +10.1 / +8.3 | +12.5 / +12.8 | — |
| Return with the 5 best holdings removed (twins' median) | +2.3 / +3.3 (−0.4 / −0.7) | +1.1 / +2.7 | +3.3 / +4.0 | +3.4 / +3.6 | +8.3 / +4.3 | +4.8 / +1.7 | — |
| Return with the spread doubled | +5.3 / +6.0 | +4.3 / +5.5 | +6.3 / +6.9 | +6.1 / +6.3 | +10.9 / +6.7 | +9.4 / +8.1 | — |
| Worst fall, daily values (worst of 12 starts) | −50% / −51% | −52 / −49 | −47 / −49 | −39 / −38 | −44 / −46 | −58 / −61 | −36% |
| Lowest account value (worst of 12 starts) | A$5,900 / A$6,600 | A$5,600 / A$6,300 | A$6,400 / A$6,300 | A$7,600 / A$7,700 | A$7,000 / A$6,200 | A$4,200 / A$4,600 | — |
| Orders a year; brokerage a year | 6.4; A$42 / 6.6; A$44 | 4.9; A$33 | 7.5; A$49 | 3.0; A$20 | 46; A$307 | 110; A$727 | — |

1. **Against the fund: behind.** 5.5% and 6.0% a year against 7.7%. The set led in 1 and 3 of the 12 start months. The gap is −2.2 and −1.6 points a year. The December 2017 panel book's monthly lead over the fund has a t-value of −0.3, so this is "no lead", not "a proven loss"; but nothing in nine years suggests a lead.
2. **Against its random twins: slightly ahead, not enough.** It beat 65 and 82 of 100 twins, by 1.0 and 1.9 points a year. The bar asked for 75. With the five best holdings removed it beat 94 and 100 of the twins, so the small edge over random is not one lucky share. The dividend ranking seems to add one to two points a year over random picking from the same shares.
3. **The structure costs more than the ranking adds.** A random 18-name equal-dollar book from the 500 most traded shares, traded this rarely, made 4.5% / 4.2% a year: about 3.3 points behind the fund. Brokerage is only A$42 a year, so this is not a trading cost. It is what equal dollars across 500 shares earned against a fund weighted to the largest companies in these years, plus a small account's cash and parcel limits. The dividend ranking recovered about half of it.
4. **The builder's bar: failed on both data sets.** Panel: (a) and (b) fail. Vendor: (b) fails. Section 2.
5. **Against EMG2-18: far behind (−7.0 / −3.9 points a year; ahead in 0 of 12 starts on both).** Against BLIND3: −6.6 / −2.6; ahead in 0 and 1 of 12. Note again that 2018–2026 is not unseen data for EMG2-18.
6. **Uncorrelated, yes. A useful complement, no.** The set's monthly lead over the fund has a correlation of 0.09 with EMG2-18's and 0.26 with BLIND3's (December 2017 books, panel). It shares 1% and 4% of its holding-months with them. It trades six times a year. But an uncorrelated book only helps if it earns its keep or cushions falls. This one earned less than the fund and fell further than the fund (−50% against −36% in March 2020; it moves one-for-one with the market). The index fund itself has, by definition, zero correlation of lead with both lines, costs nothing to run and made more. Section 5.
7. **The builder's forecast was honest and close** (section 3). Return forecast 5.8% a year: got 5.5 / 6.0. Lead over twins forecast +2.8 (80% range −3.9 to +9.5): got +1.0 / +1.9. It gave a 54% chance of beating the fund and wrote "more likely to fail the bar than to pass it"; the failed fold tests were the better guide. The fund made 7.7% a year in the judged period against 5.0% in the design windows; the set's own return was as forecast.
8. **The choice between the two members again showed no skill.** The pick (member 1, monthly review, loose band) was the worse of the two on both data sets (4.5 / 5.6 against 6.4 / 7.0) and finished behind the set in 8 of 12 starts. The default D0, which failed the builder's gates in-sample, made 6.2 / 6.3: more than the set, with the shallowest fall (−39%) and three orders a year. It also lost to the fund in all 12 starts.
9. **The dividend data has faults that matter for this family** (section 4): demerger days booked as a zero-return day are read as a dividend (Woolworths was bought as a "14.8% yielder" in 2021; its real yield was about 3%), capital returns count as yield, and the total-return series inflates the pre-2018 dividends of at least one company by a later demerger factor (Wesfarmers: 7.4% in the kit, 5.3% in fact). The last one is future information inside the frozen design data. None of these changes the verdict.
10. **Trials.** N: 2,496 → 2,640 (the builder's 144-design grid) → **2,644** (four judged books here: the set, each member alone, D0). EMG2-18 and BLIND3 figures are reused from report 91b (same start list, same data, same engine file) and are not counted again. Twins, start months, halves, stresses and the vendor cross-check are not designs.

## 1. What was done, in order

1. **Hashes checked before anything ran.** `sha256sum -c` on `blind4_build/out/hashes.txt` and `out/hashes_A.txt` (the plan hashed before the builder's first run): all matched (`deep93/out/hash_check.txt`), and again at the end.
2. **Full panel built the same way as the kit.** Same source (the survivorship-free panel of report 84, via `build87.py`), to 13 Nov 2026, with the kit's 4,658 companies in the kit's column order under the kit's labels (private map `deep92/private/idmap_blind4.csv`) plus 937 listed later. Rows to 29 Dec 2017 are bit-for-bit identical to the kit for returns, closes and traded value; exclusion flags, first dates, delisting classes and the fund are identical (`out/build93.log`).
3. **The builder's in-sample books reproduced exactly.** Member 1, member 2 and D0 match the builder's grid on all 24 books and 22 statistics; the set at normal and doubled spread, the set's 30 twins and each single design's 30 twins match the builder's result cache. Largest difference: zero (`out/repro93.log`).
4. **The reading was written down before the judged run** (`PROGRESS.md`): the bar; the forecast lines; "clearly beats EMG2-18" as in report 89; the payout bounds; the two halves; the test for "uncorrelated" and the five conditions for a paper line; the dividend-data check.
5. **Run.** Set, member 1, member 2 and D0 from 12 start months, 100 twins per book per start (the builder's frozen twin bands), normal and doubled spread, on both data sets, on the kit's `acct3.py` and `tools4.py` unmodified. EMG2-18 and the BLIND3 primary: the runs of report 91b (`deep91/out`), which used the same 12 starts, the same two data sets and an engine file that is byte-identical to this kit's (`cmp` checked).
6. **Look-ahead check on the judged period.** The kit's as-of audit for the set and for D0 on 2018–2026: every sampled decision identical with later rows blanked (`out/audit93.log`).

## 2. The bar, line by line

| Condition (frozen in PREREG_BLIND4 section 6) | Research panel | Vendor file |
|---|---|---|
| (a) set at or above the 75th percentile of its twins | 65th: **fail** | 82nd: pass |
| (b) set ahead of the fund after tax, 12-start mean | 5.5 against 7.7: **fail** | 6.0 against 7.7: **fail** |
| (c) five best removed, above twins' median | 2.3 against −0.4: pass | 3.3 against −0.7: pass |
| (d) spread doubled, above twins' median | 5.3 against 4.3: pass | 6.0 against 4.0: pass |
| (e) both members above their own twins' median, and D0 above its twins' median | +0.1, +1.9, +0.3: pass (barely) | +1.9, +2.9, +0.6: pass |
| (f) lead over twins' median inside −3.9 to +9.5 | +1.0: pass | +1.9: pass |
| All | **fail** | **fail** |

Set against the two existing lines (report 89's definition of a clear win; all four lines needed on both data sets):

| | against EMG2-18 | against BLIND3 |
|---|---|---|
| Mean gap, points a year (needs +2.0) | −7.0 / −3.9: fail | −6.6 / −2.6: fail |
| Starts ahead (needs 9 of 12) | 0 / 0: fail | 0 / 1: fail |
| Five best removed, not behind | 2.3 v 4.8 fail / 3.3 v 1.7 pass | 2.3 v 8.3 / 3.3 v 4.3: fail |
| Worst fall not more than 5 points deeper | −50 v −58 / −51 v −61: pass | −50 v −44 / −51 v −46: fail (6 points deeper) |

Halves (report only). First half (the 12 starts ended May 2022): set 7.8% / 8.8% against the fund's 7.7%, ahead in 7 of 12 starts on both, 87th / 95th percentile of twins. Second half (12 starts May 2022 – April 2023 to the end): 6.6% / 5.8% against 8.4%, ahead in 3 and 0 of 12, 79th / 57th percentile. The set kept pace with the fund to 2022 and fell behind afterwards; 2024 is the year that did it (set +2%, fund +23%).

By calendar year, December 2017 panel book, before the final tax (%):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 to Nov |
|---|---|---|---|---|---|---|---|---|---|
| Set | 2.0 | 40.5 | −5.2 | 15.3 | −4.5 | 0.9 | 2.2 | 22.8 | −6.2 |
| Fund | −0.9 | 24.6 | −1.0 | 14.0 | 6.3 | 0.3 | 23.2 | 4.8 | 6.8 |
| D0 | 1.5 | 21.7 | −0.9 | 17.8 | −3.2 | −3.0 | 24.2 | 2.6 | 0.1 |
| BLIND3 | 0.8 | 60.5 | 7.6 | 3.3 | −16.0 | 0.4 | 51.1 | 32.2 | 0.3 |
| EMG2-18 | −20.3 | 2.5 | 25.2 | 41.2 | −10.0 | 44.2 | 60.4 | 12.5 | −21.8 |

## 3. The builder's forecast against what happened

| Forecast (PREREG_BLIND4 section 5) | Forecast | Panel | Vendor | Reading |
|---|---|---|---|---|
| Lead of the set over its twins' median, points a year | +2.8 (80%: −3.9 to +9.5) | +1.0 | +1.9 | inside the range, below the centre, as the builder warned |
| Lead over the fund | +0.8 | −2.2 | −1.6 | wrong sign |
| Chance of beating the fund | 54% | no | no | the fold tests (both failed) were the better guide |
| Return a year after tax | 5.8% | 5.5% | 6.0% | right |
| Orders a year; brokerage | 10; A$67 | 6.4; A$42 | 6.6; A$44 | lower, because a nine-year book spreads its first 18 buys over more years |
| Share of winning profit from the five best holdings | 74% | 56% | 48% | lower (longer books, more holdings) |
| Worst fall on daily values | 27% typical, 53% in a 2008-like market | −44% (Dec 2017 book), −50% worst start | −51% | March 2020 was close to the stated worst case |
| Chance that the pick finishes ahead of the set | 49% | pick behind by 1.0; ahead in 4 of 12 | behind by 0.4; ahead in 4 of 12 | about a coin toss, as said |
| Builder's own expectation | "more likely to fail the bar than to pass" | failed | failed | right |

The forecast of the set's own return was accurate. The error was in the fund: it made 7.7% a year after tax in the judged period against 5.0% in the four design windows. The builder's in-sample lead of +1.6 points had a standard error of 1.8 and R of −0.2, and the builder said so. This is the honest outcome of a design that was never distinguishable from the fund in-sample.

## 4. Case table against actual events, and the quality of the dividend data

**Prices.** Spot checks of the December 2017 panel book against known prices: Wesfarmers bought 2 Jan 2018 at A$44.47, Telstra A$3.66, Fortescue A$4.93, Bank of Queensland A$12.68, Rio Tinto 2 Mar 2020 at A$86.27, Woolworths 1 Oct 2021 at A$38.70. All agree with the market record as I know it.

**What the December 2017 set book did (panel).** 36 holdings in nine years, 15 still held at the end, median holding 3.5 years, 56% winners, A$677 tax. Best: IGL (+A$3,423, bought April 2020), SIQ (+1,546), JIN (+1,364), RIO (+1,314), FMG (+946). Worst: GRR (−806), SNT (−493), ENN (−400), VTG (−384), SHM (−363). Typical buy: an inferred yield of 9.0% (10th–90th percentile 7.1% to 13.3%) against 3.6% for the median dividend payer in the universe; traded-value rank 198 (10th–90th: 8 to 408). It is a book of banks, miners at the top of their payout cycle, small financials and retailers.

**Holdings that stopped trading (all 12 starts, four books; `out/payouts_panel.csv`).** 13 names. Paid at the last close, and right or reasonable by name: AusNet (Brookfield, cash), DWS (HCL, cash), Gold Road (Gold Fields, cash), RXP (Capgemini, cash), SG Fleet (private equity, cash), WPP AUNZ (WPP plc, cash), Link (MUFG, cash), Henderson/Janus Henderson (ASX listing removed, shares continued in New York), Alumina (Alcoa scrip), Redcape (delisted with a buy-back offer), National Storage (2026 cash offer; I cannot confirm the last one from my own knowledge). **Paid zero, and wrong or doubtful:** Platinum Asset Management (stops 3 Oct 2025 at A$0.695; it became L1 Group and holders kept their shares; the new code is not chained on the panel) and Vita Group (August 2023; as far as I can tell a merger and renaming, not a failure; not confirmed). The set has one zero payout in its 12 books (Vita), member 2 has four. Payout bounds for the set: every unrecorded death paid zero 3.9% / 4.1%; every one paid at the last close 5.5% / 6.1% (the base case). The bounds do not move the verdict.

**Corporate-action table.** `68_forward_record/CORPORATE_ACTIONS.csv` has five rows (BHP, LNK, PMV, TAH, SBM). All are marked "pending" with no confirmed value, so **nothing was applied**. Exposure, for the record: the set held BHP across 25 May 2022 in 3 of 12 starts (the panel books the Woodside distribution as a 10% loss, about A$92 a book) and Link across 30 Dec 2022 in one start (A$112). Adding all of it back would raise the set's 12-start mean by about 0.03 points a year. Demerger days that the panel books as a 0% day (Wesfarmers 2018 in 8 starts, Iluka 2020 in 4) are close to the truth on the day itself.

**Dividend data.** The members rank on dividends inferred from the gap between total return and the raw close. Checks (`code/divq93.py`, `out/divq.log`, `divq_*.csv`, `lookahead_div.log`):

1. *The two files agree, but they are not independent.* Across every month-end 2017–2026 the inferred yield has a rank correlation of 0.99 between panel and vendor file and 99% of names are within a tenth of each other. Of the 18 highest yielders on a decision day, 13 on average are the same on both. Agreement mostly shows a shared source.
2. *A demerger day booked as a zero-return day is read as a dividend.* On the panel Woolworths' Endeavour demerger (24 June 2021, raw close −11.2%, return booked 0%) became an 11.9% "dividend". Woolworths then scored a 14.8% yield (vendor file: 3.0%) and the set bought it on 1 Oct 2021 and still holds it. Of 63 single-day inferred payouts of 8–15% among universe names in 2017–2026, 47 agree between the files and 16 do not; in 8 the vendor file has no payout at all.
3. *Capital returns and specials count as yield.* Incitec Pivot, February 2024: 14.6% on the panel (capital return plus special) against 5.5% on the vendor file. Real cash, but not a yield that repeats. Of the 36 buys of the December 2017 set book, 17 carry my pre-set "one-off" flag (largest single payout at least 5% and 60% of the year's total, or a yield above 10%). They did not do worse: +44% on cost against +21% for the rest in the set (IGL and RIO are among them); in member 1 alone they did worse (+5% against +30%). No clear pattern.
4. *Future information in the kit's pre-2018 yields.* Wesfarmers went ex a A$1.20 dividend on 22 Aug 2017 at A$42.60, which is 2.8%. The total-return series implies 4.0%. The difference is the factor of the November 2018 Coles demerger: the source divides the old dividend by a price already adjusted for the later demerger. So in the frozen kit Wesfarmers showed a 7.4% yield at December 2017 when the true figure was 5.3%, because of an event eleven months in the future. The set bought it in 8 of 12 starts, and it is member 1's best holding in the December 2017 book (+A$1,420). I verified this for Wesfarmers only; Tabcorp's 2016–17 yield does not look inflated, so the fault is not uniform. The same fault can sit in the design windows for companies that demerged before 2018. It favours the dividend family by an amount I cannot measure. It is a kit fault, not a builder fault.
5. *In-specie distributions* (BHP/Woodside, Link/PEXA) are booked on the panel as price falls, so they are not counted as dividends; they cost the holder a small phantom loss instead (above).
6. Of the set's 36 buys, 26 have the same inferred yield on both files, 8 differ by more than a tenth (WOW, IPL, HVN, SMR higher on the panel; WHC, GRR, GDI lower; SNT has no dividends on the vendor file) and 2 are not on the vendor file.

Reading: the inferred yield is good enough to rank ordinary payers, and wrong at the top of the list, which is exactly where this design buys. A dividend-family design should use a real dividend file (amount, type, ex-date), not the inferred one.

## 5. Is the dividend-yield family a useful, low-turnover, uncorrelated complement?

Measured on the December 2017 books, panel, 106 months (the vendor value paths of the two existing lines were not kept by report 91b, so the vendor check of the correlations could not be made):

| | Set | BLIND3 | EMG2-18 |
|---|---|---|---|
| Correlation of monthly lead over the fund with the set | — | 0.26 (halves: 0.33, 0.20) | 0.09 (halves: 0.16, 0.02) |
| Share of the set's holding-months also held there | — | 4% | 1% |
| Monthly lead over the fund: information ratio (t) | −0.11 (−0.3) | +0.38 (+1.1) | +0.25 (+0.7) |
| Tracking error against the fund, a year | 10% | 14% | 27% |
| Sensitivity to the fund (beta) | 1.00 | 0.93 | 1.06 |
| Mean month when the fund fell (40 months; fund −3.07%) | −2.91% | −2.58% | −1.93% |
| Orders a year | 6 | 46 | 110 |

Arithmetic mixes of the separate A$10,000 December 2017 books (no new run; values before the final tax):

| Mix | Return a year | Worst fall, daily | Information ratio v fund |
|---|---|---|---|
| Half BLIND3 + half EMG2-18 | 12.5% | −41.7% | 0.30 |
| One third each: set, BLIND3, EMG2-18 | 10.9% | −42.6% | 0.23 |
| Half set + half BLIND3 | 10.4% | −39.4% | 0.22 |
| Half set + half EMG2-18 | 9.4% | −48.0% | 0.14 |
| Set alone / BLIND3 alone / EMG2-18 alone | 6.7% / 13.4% / 11.7% | −44.5% / −38.4% / −58.4% | −0.11 / 0.38 / 0.25 |

Against the five conditions fixed before the run for "merits a paper line":

| Condition | Result |
|---|---|
| (i) bar (a)–(d) pass on both data sets | **fail** ((a) on the panel, (b) on both) |
| (ii) not behind the fund on both data sets | **fail** (−2.2 / −1.6) |
| (iii) both correlations below 0.3 | pass (0.26, 0.09) |
| (iv) at most 15 orders a year | pass (6) |
| (v) thirds mix: shallower worst fall than the pair, information ratio not lower | **fail** (−42.6% v −41.7%; 0.23 v 0.30) |

**Low turnover: yes. Uncorrelated: yes. Useful: no.** Adding the set as a third of the money took 1.6 points a year off the pair and did not make the worst fall shallower, because the set fell 44–51% in March 2020, more than the fund. It does not cushion: in the fund's falling months it lost almost as much as the fund. Low correlation of lead is easy to get from anything that tracks the market with noise; what matters is a positive lead or a shallower fall, and this has neither. If the aim is a calm, cheap, uncorrelated third leg, the index fund does that job better on every line in this table.

Two things worth keeping from this build:
- **Member 2's rule** (look only at 13, 26, 39 months; keep the top 30% by yield) was the better half on both data sets (6.4 / 7.0, 82nd / 89th percentile of its twins, ahead with the five best removed at the 98th / 99th). It is still behind the fund.
- **Random twins at six orders a year lose about 3.3 points a year to the fund.** That is the cost of holding 18 equal parcels from the top 500 in a period led by the largest companies. Any low-turnover large-and-mid-cap design starts from that deficit and needs a ranking worth more than 3 points to draw level. The dividend rank was worth 1–2.

## 6. Verdict

| Question | Answer |
|---|---|
| Against the fund | Behind on both data sets: 5.5 / 6.0 against 7.7; ahead in 1 / 3 of 12 starts. Bar failed. |
| Against EMG2-18 | −7.0 / −3.9 points a year, ahead in 0 of 12. Not a clear win; a clear loss. **Keep EMG2-18. No v2 drafted.** (2018–26 is not unseen for EMG2-18.) |
| Against BLIND3 | −6.6 / −2.6 points a year, ahead in 0 / 1 of 12. BLIND3 remains the only blind design that beat the fund on unseen data. |
| Dividend-yield family as a complement | Low turnover and uncorrelated (0.09 and 0.26), but behind the fund and with a deeper fall than the fund. **No paper line.** |
| D0 (low volatility, top 200) | 6.2 / 6.3, behind the fund in all 12 starts; shallowest fall (−39%). Not a candidate. |
| Did the ensemble help? | The set finished between its two members. Sharing one account cost nothing and gained nothing; both members rank the same list. |
| Was the builder calibrated? | Yes. Return forecast right, range held, warned of failure. The 54% was too high given two failed folds. |

For the record keeper:
1. N = 2,644 (2,496 + 144 + 4). Ledger not written by me.
2. Data faults to log: (a) Platinum (PTM) → L1 Group not chained; paid zero on the panel; (b) Vita Group (VTG) August 2023 paid zero, to be checked; (c) demerger days booked as 0% (WES 2018, ILU 2020, WOW 2021, TAH 2022, SBM 2023, OML and RRR 2020) are read as dividends by any return-minus-price method when the fall is under 15%; (d) the total-return series back-adjusts old dividends by later demerger factors (verified: Wesfarmers 2017) — future information in every truncated kit built from it; (e) the corporate-action table still has no confirmed values, so nothing could be applied.
3. For a future kit: give the builder a real dividend file, or state plainly that inferred dividends are contaminated at the top of the yield ranking.

## 7. Files

`deep93/PROGRESS.md`; `code/build93.py`, `repro93.py`, `eval93.py`, `read93.py`, `detail93.py`, `divq93.py`, `payouts93.py`, `corp93.py`, `audit93.py`; `out/eval_panel.pkl`, `eval_vendor.pkl`, `summary_*.csv/json`, `read_*.log`, `detail_*.json`, `cases_*.csv`, `nav_panel.csv`, `navdaily_*.csv`, `divq*.{log,csv,json}`, `lookahead_div.log`, `payouts_panel.*`, `corp_exposure.*`, `audit93.log`, `hash_check.txt`. `deep93/full/panel.npz` was deleted to save disk (rebuild: `code/build93.py`, one minute).
