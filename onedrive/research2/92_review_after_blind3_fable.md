# 92. Review after blind build 3 — what three blind builds have taught, EMG2-18 and BLIND3 together, what to run in December, in-specie distributions, and the kit for blind build 4

19 November 2026. Author: Fable, as reviewer (owner's cycle: blind build → review and learning → next blind build). Reviews report 91b.
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. The ledger was not written. No vendor credits were used.
Work folder: `scratchpad/deep92/` (`PROGRESS.md`, `code/`, `out/`). Briefing and kit for the next builder: `deep92/METHOD_LESSONS_FOR_BLIND4.md`, `deep92/blind4_kit/`. Draft paper-line amendment: `deep92/AMENDMENT_shadow_PAIR.DRAFT.md`.

How to read the figures: as in report 91b. A$10,000 once; "a year after tax" = after Interactive Brokers brokerage (A$6.60 an order), the modelled spread and 32% tax, everything sold at the end. Fund = ASX 200 with dividends, 7.7% a year after tax for January 2018 – November 2026. Unless stated, a figure is the mean of 12 start months (December 2017 to November 2018) run to 2 Nov 2026. Two data sets: research panel first, vendor file second. Twins = 100 books with the same structure that pick at random.
**Every figure in sections 1 to 3 is on data that has been seen before. None is a candidate and none is evidence for a rule.**

## 0. Answer first

1. **Blind build 3's good result came down to a tie-break of 0.2 points a year.** I ran all 148 designs of the builder's list on 2018–2026. On the design data three kinds of strategy were tied (family scores −3.2, −3.5 and −3.5, each with a standard error near 3). The rule took the first. Its pick made 12.1% / 8.6% a year. Had the second come first, the same rule would have delivered a design that made **−3.5% / −2.7%** a year and ranked 144th / 140th of 148.
2. **The design-choice step has now shown no skill three times, and in build 3 it had none at the level of kinds of strategy either.** Only 13 / 11 of the 148 designs beat the fund. The ten designs with the best score on the design data made 1.5% / 0.7% a year; the ten with the worst made 1.1% / −1.8%.
3. **What to do about it: stop choosing one design. Hold the tied ones in equal parts.** On blind build 3's list that would have made 9.2% / 7.2% in one A$10,000 account: 1.4 to 2.9 points less than the pick that happened and 10 to 13 more than the pick that nearly happened. It beat 100 / 92 of 100 random twins. Against the fund it was ahead on the panel and behind on the vendor file (11 and 6 of 12 start months). This is insurance against a bad draw. It is not a way to earn more.
4. **EMG2-18 and BLIND3 are different books and hold up differently.** 7% of holdings shared; monthly returns correlate 0.59 / 0.56; BLIND3 trades 46 times a year against 110. One fact they share: both worked only outside the 200 most traded companies.
5. **Both in one A$10,000 account is workable.** Nine names from each set of rules, all parcels above A$500, first-day brokerage A$119, the same as EMG2-18 alone. On seen data it made 14.6% / 12.4% a year against 12.5% / 9.9% for EMG2-18 alone and led it in all 12 start months on both data sets. **This is not evidence**: both halves were chosen or judged on these years, and most of the extra came from the EMG2 half holding 9 names in place of 18.
6. **It does not save brokerage.** After the first year it sent 131 / 115 orders a year (A$864 / A$761) against 110 / 103 for EMG2-18 alone. What it gives is less reliance on one rule set and on five winners. The worst fall was shallower on the panel (−49% against −58%) and no better on the vendor file (−59% against −61%).
7. **December: run EMG2-18 as registered. No change to the live rules.** The trading system, the loss rule, the twins and the go-live checklist were built for it; a different book three weeks before the first order adds a risk larger than anything a back-test can offset. The first months answer one question only: do real fills and costs match the model. EMG2-18 is the book that depends most on that answer.
8. **The owner should know one thing plainly:** EMG2-18 has never been tested on data it had not seen, and cannot be. BLIND3 has, once, and section 1 shows that test was partly luck. Neither is proven. A fall to A$7,000 within a year has happened in about 1 start in 12, and to A$8,000 in 1 in 6 (report 90). Costs are about 13% of the capital a year before any gain.
9. **One decision for the owner (section 4.3):** the registered rule says BLIND3 needs 24 months of paper before real money, while EMG2-18 goes live after two weeks. That is inconsistent with the evidence each has. I propose a paper line for the pair now and a dated owner decision in June 2027, not an automatic change.
10. **In-specie distributions are a real fault in the data, in both directions.** BHP's Woodside shares (May 2022) are booked on the panel as a 10% loss. Link's PEXA shares (December 2022) as a 40% loss. Premier's Myer shares (January 2025) as a 27% loss in both data sets. About 40 such days in nine years among the 600 most traded shares. The replay books were barely touched (BHP cost the BLIND3 primary about A$125 once). Forward, an uncorrected event would look like a crash in one holding and can trigger a wrong sale. Section 5 gives the handling for the paper record and for the trading system.
11. **Blind build 4: the same cut-off (29 Dec 2017) and the same data, with one change: the builder must deliver a set of three designs held in equal parts in one account, named by rule, and not a pick.** Kit, briefing, label map, hashes and self-check are ready (section 6). A blind build of an EMG2 + BLIND3 book is not possible: the builder would have to be handed both signals.
12. **Trials: N 2,347 → 2,496.** This review ran 149 (section 7). None is a candidate.

## 1. What three blind builds have taught

### 1.1 The three builds side by side

| | Blind build 1 | Blind build 2 | Blind build 3 |
|---|---|---|---|
| Design data to; judged period | Dec 2017; 2018 – Oct 2026 | Dec 2020; 2021 – Nov 2026 | Dec 2017; 2018 – Nov 2026 |
| Strategy menu in the kit | Yes | Yes | No |
| Designs listed by the builder | 72 | 81 | 148 |
| Middle design of the list, return a year after tax | 13.0% / 10.3% | 0.1% / −2.1% | 3.9% / 4.0% |
| Designs of the list ahead of the fund | 63 / 45 | 16 / 5 | 13 / 11 |
| Chosen design's return | 6.0% / 3.5% | 4.7% / 6.5% | 12.1% / 8.6% |
| Rank of the chosen design in its list | 65th / 63rd of 72 | 27th / 6th of 81 | 7th / 9th of 148 |
| Rank link between the design-data score and the judged result, whole list | +0.46 / +0.40 (coarse), −0.13 / −0.09 (fine) | +0.84 / +0.80 | +0.17 / +0.32 |
| Same, inside the part of the list that was not clearly bad | — | +0.42 / +0.38 | −0.04 / −0.12 |
| The builder's reasoned default | — | −2.2% / −3.1% | 0.9% / 0.1% |

One pick near the bottom of a good list, one fair pick from a poor list, one pick near the top of a poor list. Three draws, three different stories. That is what no skill looks like.

### 1.2 New in this review: the whole blind-3 list on the judged period

The builder listed four kinds of strategy. Left column: what the design data said. Right columns: what happened (`deep92/out/grid_read_panel.log`, `grid_read_vendor.log`, `grid_judged_*.csv`).

| Kind of strategy (designs) | Family score on design data, points a year | 2018–2026: middle design | Designs ahead of the fund |
|---|---|---|---|
| Momentum among the calmer half of the most traded shares (16) | −3.2 | 8.3% / 6.1% | 8 / 7 |
| Near the 52-week high, sold on a trailing stop (36) | −3.5 | 2.1% / 2.3% | 0 / 0 |
| Lowest volatility (48) | −3.5 | 4.2% / 4.7% | 0 / 0 |
| Plain momentum (48) | −11.5 | 4.1% / 1.0% | 5 / 4 |

- **The three kinds the design data could not separate ended 2 to 6 points a year apart.** The one kind it marked as clearly worst (plain momentum) finished level with two of the others.
- **The designs with the best scores on the design data were the trailing-stop designs.** Three of them passed every gate, with leads over their twins of 12 to 17 points a year. On 2018–2026 they made −0.8% to −3.5% and ranked 136th to 144th of 148.
- **The pick was the first of three tied kinds.** The family scores were −3.25 and −3.46: a gap of 0.2 against a standard error near 3. The builder said so before the freeze ("the top three families are indistinguishable", and its own fold test "showed no skill"). Report 91b judged what the rule delivered. This review adds what the rule nearly delivered.
- **Inside the winning kind the result was broad, which counts for it.** All eight of its designs on the 400 most traded shares took the top eight places on the panel (10.4% to 16.0%). The same idea on the 200 most traded made 4.4% / 4.7%. Momentum on the top 400 without the calm screen made 2.5% / −1.4%. So the calm screen and the ranks 201–400 both mattered in these years.
- **Slow trading did not help by itself.** The low-volatility designs sent about 10 orders a year and none beat the fund.

### 1.3 What has repeated across all three builds, and what has not

Repeats:
1. **Picking between designs from past data does not work.** Fine choices in all three builds; in build 3 the choice between kinds as well.
2. **A signal beats random choice in the same shares by 8 to 13 points a year.** Every chosen design passed its twins.
3. **Random books at A$10,000 trail the fund by 6 to 12 points a year** after brokerage and short-term tax. A signal has to earn that back before it is level.
4. **The reasoned default loses.** Twice a builder reasoned from costs to "slow, in the largest companies", and twice that book lost to the fund and to its twins.
5. **Nothing worked inside the 200 to 300 most traded companies.** True of EMG2's family, of blind build 2's list and of blind build 3's list.
6. **Every book lives on a few holdings.** Take out five and most are below the fund.

Does not repeat:
1. **"Coarse choices can be read from past data"** (report 90). True in builds 1 and 2. In build 3 the coarse ranking carried nothing: link between family score and judged result 0.00 / +0.14.
2. **Whether a good list gets written.** Build 1's list was good, build 2's and build 3's were not (16 and 13 designs ahead of the fund out of 81 and 148). Removing the menu did not make the list better. It made it different.
3. **The verdict on blind build 3 itself.** Report 91b: "the first blind design that beat the fund and its twins". Still true. But the method that produced it would have produced a loss about as easily. The design is worth tracking on paper. The method is not yet shown to work.

### 1.4 What to do about it: hold a set, not a pick

The logic needs no back-test. If past data cannot separate designs A, B and C, then choosing one gives A's, B's or C's result at random. Holding all three gives the average. The average is never the best of the three and never the worst. The price is that it is never the best.

What that would have meant on blind build 3's list. The rule, written before I ran it (`deep92/PROGRESS.md`): one seat for each tied kind that has a design passing the gates; a kind with no passing design gives its seat to the best kind. That names the pick, its 12-month neighbour, and the best trailing-stop design. I already knew the first two results; the third was unseen.

| 2018–2026, A$10,000, after all costs and tax | Research panel | Vendor file |
|---|---|---|
| The pick that happened (BLIND3 primary) | 12.1% | 8.6% |
| The pick the same rule delivers if the tie goes the other way | −3.5% | −2.7% |
| The set, three full A$10,000 books averaged (a A$30,000 account) | 9.8% | 7.4% |
| The set, three separate sub-accounts of A$3,333 | 8.1% | 6.0% |
| **The set in one A$10,000 account** (kit wrapper, section 6) | **9.2%** (5.1 to 12.1) | **7.2%** (3.9 to 9.5) |
| — start months ahead of the fund (of 12) | 11 | 6 |
| — percentile among its own 100 twins; lead over their median | 100th; +7.8 points | 92nd; +6.6 points |
| — five best holdings removed | 6.1% | 3.4% |
| — worst fall on daily values; lowest value | −45%; A$6,990 | −44%; A$6,750 |
| — orders a year; brokerage; modelled spread | 74; A$488; A$101 | 74; A$486; A$98 |
| Fund | 7.7% | 7.7% |

- The set finished ahead of the fund on the panel, a little behind it on the vendor file, and well ahead of random choice on both. One of its three members lost money throughout.
- Three separate sub-accounts are worse than one account. A sub-account that loses shrinks below the size at which it can hold parcels of A$500 (the losing one fell to A$1,017), and each carries its own cash reserve. Random twins made 2.0% a year in a single A$10,000 book of this kind and −0.5% to −0.8% in a A$3,333 sub-account. The kit for blind build 4 therefore runs a set as **one account** (section 6.2).
- A set trades more than one member alone (74 orders against 46), because six names from each of three rules turn over faster than fifteen from one.
- **Honest reading:** on this list the set would have cost 1.4 to 2.9 points a year against the pick that happened. Its case rests on the pick that did not happen, and on logic. Blind build 4 tests it on a list nobody has seen.

## 2. EMG2-18 and BLIND3 as complementary lines

| December 2017 books unless stated | EMG2-18 (registered live rules) | BLIND3 (blind-3 primary, paper line) |
|---|---|---|
| Idea | Three-measure momentum, ranks 301–600 by traded value, sold when out of the top fifth | Six-month momentum among the calmer half of the top 400, winners kept to day 367 |
| How it was arrived at | Band chosen in report 85 with 2018–2026 in view | Builder saw nothing after 2017; one of three tied kinds |
| Return a year, 12-start mean | 12.5% / 9.9% | 12.1% / 8.6% |
| Random twins beaten (of 100) | 100 / 100 | 94 / 99 |
| Five best holdings removed | 4.8% / 1.7% | 8.3% / 4.3% |
| Spread doubled | 9.4% / 8.1% | 10.9% / 6.7% |
| Worst fall, daily values | −58% / −61% | −44% / −46% |
| Orders a year; brokerage; modelled spread | 110; A$727; A$623 | 46; A$307; A$101 |
| Tax paid over nine years | A$9,300 | A$1,500 |
| Typical traded-value rank at purchase | 397 | 161 |
| Swing of monthly returns, a year | 31% | 20% |
| Calendar years 2018 … 2026 (panel) | −23, −2, +40, +48, −19, +55, +47, +26, −28 | −7, +69, +13, +6, −23, +13, +37, +32, +2 |

- **Overlap is small.** 7% of BLIND3's holding-months were also EMG2-18 holdings. Monthly returns correlate 0.59 / 0.56 (both are share books; most of that is the market). Monthly leads over the fund correlate 0.33.
- **They had different bad years.** 2019 and 2026 were poor for EMG2-18 and fine for BLIND3. 2021 was the reverse. 2018 and 2022 were bad for both.
- **They fail in different ways.** EMG2-18 rests on a spread model no real fill has tested (A$623 a year). BLIND3 rests on holdings that stop trading being takeovers (report 91b: its lower payout bound is 1.2% a year).
- **They agree on one thing:** momentum paid outside the largest 200 companies and not inside.
- **Neither is proven.** EMG2-18's years are seen. BLIND3's are unseen, and section 1.2 shows how close that test came to a different answer.

## 3. Both in a A$10,000 account: is 9 + 9 viable?

Three ways to hold both were run, with no setting changed in either rule set (`deep92/out/combo_read_*.log`, `ensu_read_*.log`). Both rule sets already take their number of names from the account value, so on A$5,000 each gives 9 names.

| 2018–2026, panel / vendor | EMG2-18 alone, A$10,000 | BLIND3 alone, A$10,000 | Half of each full book (needs A$20,000) | Two sub-accounts of A$5,000 | **One account, equal parts** |
|---|---|---|---|---|---|
| Return a year, 12-start mean | 12.5% / 9.9% | 12.1% / 8.6% | 12.3% / 9.3% | 13.6% / 11.3% | **14.6% / 12.4%** |
| Range over the 12 starts | 11.5–14.3 / 9.0–11.9 | 8.7–14.7 / 4.7–10.3 | 10.9–13.9 / 7.4–10.9 | 11.5–15.4 / 9.2–14.2 | 13.2–17.1 / 11.0–14.9 |
| Starts ahead of the fund | 12 / 12 | 12 / 10 | 12 / 11 | 12 / 12 | 12 / 12 |
| Starts ahead of EMG2-18 alone | — | 5 / 3 | — | 11 / 11 | 12 / 12 |
| Five best holdings removed | 4.8% / 1.7% | 8.3% / 4.3% | 8.8% / 5.6% | 8.2% / 5.6% | 10.0% / 7.1% |
| Spread doubled | 9.4% / 8.1% | 10.9% / 6.7% | — | 11.2% / 10.6% | 13.3% / 11.3% |
| Worst fall, daily values | −58% / −61% | −44% / −46% | −47% / −52% | −49% / −61% | −49% / −59% |
| Lowest account value | A$4,215 / A$4,586 | A$7,038 / A$6,164 | A$5,785 / A$5,629 | A$5,833 / A$5,163 | A$6,519 / A$4,884 |
| Orders a year | 110 / 103 | 46 / 48 | 78 / 76 | 131 / 112 | 131 / 115 |
| Brokerage a year | A$727 / A$682 | A$307 / A$318 | A$517 / A$500 | A$867 / A$739 | A$864 / A$761 |
| Modelled spread a year | A$623 / A$520 | A$101 / A$91 | A$362 / A$306 | A$482 / A$364 | A$399 / A$319 |
| Random twins: median return; book's percentile | −0.1% / −2.9%; 100 / 100 | 2.0% / 0.4%; 94 / 99 | — | 0.1% / −2.3%; 100 / 100 | −0.4% / −0.9%; 100 / 100 |

**Parcels and fees at A$10,000.**
- EMG2 half: floor(A$5,000 ÷ A$550) = 9 parcels of A$555. BLIND3 half: 9 parcels of A$520. Every parcel is above the A$500 minimum. First day: 18 buys, A$119 brokerage, the same as EMG2-18 alone.
- The number of names follows the account. At A$8,000 each half holds 7. At A$20,000 the EMG2 half reaches its 18 and the BLIND3 half its 15.
- **There is no brokerage saving after the first year.** Both halves grow into more names, and the pair then trades more than EMG2-18 alone. Brokerage plus modelled spread comes to about A$1,260 a year against A$1,350: the same, within the error of the spread model.

**Why the pair beat both of its parts, and why that is not evidence.**
- Run alone on A$5,000, the EMG2 rules made 17.2% / 14.5% a year (9 names) against 12.5% / 9.9% on A$10,000 (18 names). The BLIND3 rules made 8.5% / 7.2% on A$5,000 against 12.1% / 8.6% on A$10,000. So the pair's extra return is the EMG2 half being more concentrated in its top-ranked names in these years. Nobody chose 9 names for a reason. Alone, that 9-name half fell 59% / 75%.
- Pooled cash helps a little: one reserve, and a sale by one half can fund a buy by the other.
- Both rule sets were selected, or judged and kept, on these same years. A pair of two survivors looks good on the period they survived.

**Verdict.** Holding both in one A$10,000 account is mechanically sound and costs about the same as EMG2-18 alone. What it buys is less reliance on a single rule set: steadier across start months, far less dependent on five winners (10.0% / 7.1% against 4.8% / 1.7%), half the trades in shares where the spread model matters little. It does not reliably shorten the worst fall.

**A single book that blends the two signals: not run.** There is no way to merge two scores and two parts of the market without choosing how, and any choice would be made after seeing both on 2018–2026. That would be a new design with a back-test and no test. The one-account pair above needs no such choice: each rule set runs unchanged on its half.

**Other splits.** A 50/50 split is the only one that needs no decision. A different weight would be picked from the table above, which is hindsight.

## 4. Real money in mid-December

### 4.1 Recommendation
**Run EMG2-18 as registered, A$10,000, with the staged loss rule as signed. Change nothing in the live rules.**

Reasons:
1. **The system is built and gated for this book.** Trading code, simulated twin, 100 random twins, loss rule, approval of each order, go-live checklist. The BLIND3 rules exist only in the paper record's code. A two-rule account would be new live code with no paper month. An operational fault in the first weeks costs more, and teaches less, than any difference between these books.
2. **Nothing in sections 1 to 3 is evidence that another book is better.** The pair's lead is on seen data and comes mostly from an accident of concentration.
3. **The live book's job in its first months is to test the costs.** EMG2-18 pays about A$620 a year in modelled spread, the least certain number in the programme. At a doubled spread its replay return falls from 12.5% / 9.9% to 9.4% / 8.1%, close to the fund. Real fills in these shares answer that. BLIND3 or the pair would answer it more slowly.
4. **Changing the book because a newer back-test looks better is the habit the blind builds were set up to break.**

### 4.2 The risk, stated honestly
- **Evidence.** The replay lead over the fund (4.8 / 2.2 points a year) is on the years the band was chosen on. EMG2-18 has not been, and cannot be, tested on unseen past data. With five holdings removed it is below the fund. Over March to November 2026 its picks did worse than 95 of 100 random books in the same shares.
- **Costs.** About 110 to 125 orders a year: A$730 to A$860 of brokerage, plus about A$620 of spread if the model is right. That is about 13% of the capital a year before any gain. Random books in these shares made −0.1% / −2.9% a year.
- **First year** (report 90, 76 past starts, month-end values): about 1 chance in 6 of being under A$9,000 within three months; 1 in 6 of touching A$8,000 within a year; 1 in 12 of touching A$7,000; middle outcome after a year about A$10,100 against A$11,100 for the fund; about an even chance of being behind the fund. Daily lows are deeper than month-end values.
- **Deep falls are normal for this book.** −58% / −61% in March 2020 (lowest value A$4,215). −40% between March and July 2026. A fall of 25% to 45% about once every three to four years.
- **What one year can show.** Whether fills and costs match the model. Not whether the signal works: the gap between two such books over 12 months has a standard deviation of about 15 points.
- **Plainly:** this is A$10,000 the owner can afford to see halved. The loss rule pauses buying at A$6,000 and needs the owner's written word to continue at A$5,000. It does not prevent the fall.

### 4.3 A decision for the owner, and what I propose
The registered BLIND3 amendment says a proposal to give it real money needs at least 24 months of paper record. EMG2-18 goes live after two weeks of paper. On the evidence that is the wrong way round: BLIND3 has one unseen test, EMG2-18 has none. Twenty-four months of paper would add little evidence on return in any case (15 points of noise a year). What paper time does add is proof that the code runs.

Proposal:
1. **Now:** register the one-account pair as a paper line with 100 twins from the 30 Nov 2026 decision (`deep92/AMENDMENT_shadow_PAIR.DRAFT.md`). It costs nothing. The registered "50/50 reading" is the average of two A$10,000 books, which a A$10,000 owner cannot hold; the pair is what could actually be held.
2. **June 2027, an owner decision, not an automatic change:** whether to convert the live book to the pair at a month-end. I would put it to the owner only if all of these hold:
   - the trading system runs the two-member account and has matched the paper line order for order for at least three months;
   - the spread measured on live EMG2-18 fills is no more than 1.5 times the model;
   - the paper pair is at or above the median of its own twins since the start (a check that nothing is broken, not a test of skill);
   - blind build 4 has been judged, so the owner sees how a set fares on a list nobody chose with hindsight.
3. **A conversion would run through the normal rules:** the EMG2 half shrinks to its share as holdings are sold by its own sell rule; nothing is sold to rebalance.
4. If the owner prefers to keep the 24-month rule, nothing here argues that it is unsafe. It is slow, not wrong.

## 5. In-specie distributions and demergers

### 5.1 What the data do today
An in-specie distribution hands shareholders shares in another company. The parent's price falls by their value. Nothing is lost, but a price file with no record of the event shows a loss. I compared the research panel with the vendor file on days when both have the same close, the price moved more than 7%, and their returns differ by more than 7 points, among the 600 most traded shares, 2018–2026 (`deep92/out/inspecie_events.csv`, `inspecie92.log`).

| Event | Research panel | Vendor file | What happened |
|---|---|---|---|
| BHP, 25 May 2022 (Woodside shares) | −10.0% | +1.1% | Panel books a loss that did not happen |
| Link, 30 Dec 2022 (PEXA shares) | −40.0% | +15.6% | Panel books a loss; the vendor's figure looks too high |
| Premier Investments, 21 Jan 2025 (Myer shares) | −26.7% | −26.7% | **Both** book a loss; the two files share a source after 2024 |
| Tabcorp, 24 May 2022 (Lottery Corporation) | 0.0% | +44.5% | Panel sets the day to zero; the vendor is wrong the other way (the true day was about +8%) |
| Wesfarmers Nov 2018, Woolworths Jun 2021, Iluka Oct 2020 | 0.0% | +1.6%, +4.8%, +1.8% | Formal demergers: the panel sets the day to zero, losing a small real move |
| St Barbara, 6 Jul 2023 (Genesis shares) | 0.0% | +19.0% | Unresolved |
| Large capital returns (New Energy Solar 2022–23, PointsBet 2023–24, Sunland 2023) | +27% to +32% | +2% to +8% | Panel appears to cap the adjustment; the two files disagree by 25 points |

- **101 such days in nine years**, about 40 of them falls of more than 7% in the raw price; 29 in the top 400, 79 in ranks 301–600 (some in both).
- **Neither file is right throughout.** The cross-check finds a disagreement; it does not say who is right. Premier 2025 shows that when the files share a source, the cross-check finds nothing.
- **Effect on the judged replays: small.** Of the seven books in report 91b's case table, the only holdings carried across such a day were BHP (the BLIND3 primary and three family members: a phantom loss of about A$70 to A$125 each, a tenth of the parcel, once in nine years) and two EMG2-18 holdings (Cardno and Fenix, where the two files disagree and the panel is the more favourable). The verdicts of report 91b do not move.
- **Effect going forward: larger than the dollars.** A 10% to 40% one-day "fall" drops a holding down its momentum ranking and raises its measured volatility. BLIND3 sells a losing holding at once and screens on volatility. A wrong event can cause a wrong sale and bar a re-entry for a year. Large calm companies are the ones that demerge, and that is BLIND3's universe.
- **Side finding** (`deep92/out/excl_check.log`): the name rule that marks funds also marks ordinary companies whose present or former name contains "Investment" or "Fund". Among the 700 most traded today: Electro Optic Systems (rank 74), Pinnacle, Premier Investments, Helia, Navigator Global, Australian Ethical, COG Financial. They cannot be bought by any kit book or paper line. Every kit has the same flags, so comparisons between builds are fair; the universe is slightly wrong.

### 5.2 Recommended handling: the paper record
1. **One table of manual corporate actions**, kept by the record keeper: code, ex-date, kind, value per share of what was distributed, source (the ASX announcement), date entered. Hashed and noted in the ledger at each change. It is a data correction under a registered procedure, not a rule change. The procedure itself needs a short amendment before first use.
2. **Detection, every session.** For every holding of every paper line and every name on a current target list: flag `CA_SUSPECT` when the raw close falls 8% or more in a session with no dividend or split row. Also flag any position that appears in an announcement titled with "in specie", "demerger", "scheme" or "return of capital" once the licensed announcements feed (owner decision D-6) exists. Until then the record keeper checks each flag by hand against the company's ASX announcements. Expect a few flags a month; nearly all are real falls and are cleared in a minute.
3. **Treatment when confirmed.** On the ex-date:
   - the holding receives cash equal to shares held × value per share of the distribution (the first close of the distributed share, or the company's stated value), less one A$6.60 brokerage if the paper book is taken to sell the new shares. The paper books do not hold the new shares;
   - the price history used for scores is adjusted by the factor (previous close − value) ÷ previous close before that date, so the ranking, the volatility screen and the profit test see no fall;
   - the entry is listed on the scorecard.
4. **Resolve before the next decision.** A `CA_SUSPECT` flag on a holding or target must be confirmed or cleared before the month-end decision. If it is not, the decision runs on the data as they are and the scorecard says so in its first line. A flag must not silently block a decision.
5. **Back-tests.** Judges report holdings carried across a disputed day, as section 5.1 does. The record keeper builds the table back to 2018 for the 40 large events in `inspecie_events.csv`, starting with BHP, Link, Premier, Tabcorp and St Barbara.

### 5.3 Recommended handling: the trading system
1. **Unmanaged positions.** The broker will deliver the new shares as a position the system did not open. Today that would fail the integrity check (live holdings = simulated twin), and under the loss rule a failed integrity check blocks buying. Add a class "unmanaged position": counted in the account value, shown to the owner, excluded from the strategy's slots and from the holdings comparison.
2. **Account value includes them.** The A$7,000 / A$6,000 / A$5,000 steps and the one-day 12% halt are tested on the account value. If the new shares are left out, a distribution looks like a loss and can trip a step.
3. **The simulated twin applies the same table** on the same day, so live and twin stay comparable.
4. **Disposal is the owner's call, with a default.** Default: propose a sell order for an unmanaged position at the next month-end decision if it is worth A$200 or more (A$6.60 is then 3% or less); below that, hold it and remind the owner quarterly, or use the company's sale facility if one is offered. Each such order needs the owner's approval like any other.
5. **No automatic sale of the parent.** If the parent holding carries an unresolved `CA_SUSPECT` flag at a decision, a sell order for it is sent for approval with the flag shown, never auto-approved.
6. **Tax records.** A distribution changes the cost base or is income, depending on its kind. The system records the event and the values; the treatment is for the owner's accountant. General information only.

## 6. Blind build 4

### 6.1 Which test, and why

| Option | What it would tell us | Decision |
|---|---|---|
| A different cut-off (end 2021, judge 2022–2026) with the blind-3 method unchanged | A second sample of the pick method on 4.9 years (uncertainty about 10 points a year). The pick step is already known to carry no skill | Not now |
| **A set, not a pick, at the same cut-off as builds 1 and 3** | Whether holding the tied designs in equal parts gives a result that beats random twins and does not depend on a tie-break. Same data and same judged years as builds 1 and 3, so the only things changed are the delivery rule and the builder | **Chosen** |
| A blind build of an EMG2 + BLIND3 book | Nothing blind: the builder would have to be handed two signals, one of them chosen with 2018–2026 in view. The paper pair from 30 Nov 2026 is the only clean test | Not possible |

Why the same cut-off:
- **One change at a time.** Builds 1, 3 and 4 then form a ladder on identical data and identical judged years: menu and pick; no menu and pick; no menu and set.
- **Longest design history that still leaves 8.9 judged years.**
- **A second no-menu builder shows how much the list depends on the builder.** Section 1.3: the list matters more than anything done to it afterwards.
- No cut-off supplies new years. 2018–2026 has been seen by every reviewer and judge. Only the builder is blind, and only the forward record is new evidence. After build 4, the same kit should be run unchanged at end 2014 and end 2021.

### 6.2 What changed from the blind-3 kit and briefing

| # | Change | Why |
|---|---|---|
| 1 | The builder delivers **a set of three designs in equal parts in one A$10,000 account**, not one design | Section 1.4 |
| 2 | Families whose score is within one noise unit of the best are **kept**; only families clearly behind are dropped | The scores are used to exclude, not to rank |
| 3 | **Three seats filled by rule**: one per kept family with a gate-passing design; with two such families 2 + 1; with one, all three; with none, the default alone | No judgement after results |
| 4 | Two comparators are frozen with the set: **PICK** (what the blind-3 rule would have delivered) and **ALT** (the set next door) | A paired reading of set against pick inside one build |
| 5 | The set is run as one account and **delivered whatever its own run shows** | Stops a second round of choosing |
| 6 | The fold test is run on the whole procedure, for the set and for PICK | The builder's own pre-2018 evidence on set against pick |
| 7 | Every design must take its order size and number of names from the account value it is shown | A member sees a third of the account |
| 8 | Bar (e): at least two of three members above their own twins, and ALT above its twins. The judge also runs the builder's whole list | Section 1.2 was only possible because the list was run afterwards |
| 9 | `tools4.py` = `tools3.py` unchanged plus `Ensemble` and `ensemble_factory` | The wrapper holds no rule about shares |

Unchanged: the data (bit-for-bit the blind-1 and blind-3 panels, under new labels `Q00001…` in a new order), the accounting engine (`acct3.py`, byte-identical to the one build 3 was judged with), the windows, the score, the gates, the 150-design budget, twins, the as-of audit, the forecast, the judged starts.

The one-account wrapper, in short: each member decides on a sub-book of its own holdings and a third of the account value; sells go through unchanged; a company held or sold today by another member is skipped; members claim names in turn; a member cannot spend past its share by more than half a parcel; the parts are never traded back to equal; one cash reserve and one tax account.

The briefing gives one piece of evidence for asking for a set, and it is dated 2017 or earlier: in two folds on design data, a rule that names one winner chose a family that was then not the better of its top two, and its picks ranked 122nd and 22nd of about 150. It does not say what the designs were or that anything was run after 2017.

### 6.3 Checks made (`deep92/out/`)
- **Self-check, all pass** (`selfcheck_blind4.log`). It tests: no row, first-price date, delisting record or fund value after 29 Dec 2017; labels only; label map outside the kit; no label or column position shared with the blind-2 or blind-3 kits; data identical to the blind-1 panel and flags, delistings and fund identical to the blind-3 kit; engine byte-identical to blind-3's; `tools4` equal to `tools3` below the header plus the wrapper; the wrapper reads no price, return or traded value; none of a list of family and setting words from EMG2 and from all three earlier builds in the kit code, the README or the briefing; no year after 2017 except the authoring year; no ASX code.
- **Smoke test** (`smoke_blind4.log`): a set of one member gives exactly that member's result (144 books × 22 statistics); a set of three random members runs and passes the as-of audit; a set with one member that reads tomorrow's prices fails it.
- **Wrapper on the judged period** (private, seen data): a one-member set of the BLIND3 primary reproduces report 91b's twelve start-month results exactly.
- Hashes of kit, briefing, label map, build and check code: `deep92/out/blind4_hashes.txt`.

### 6.4 How to run it
1. Record the hashes in `deep92/out/blind4_hashes.txt` in the ledger before the builder starts.
2. Copy `METHOD_LESSONS_FOR_BLIND4.md` and `blind4_kit/` to a clean folder and start the builder there with nothing else. The blind-3 builder's folder, the blind-3 kit (same data under other labels) and every report are on the same disk.
3. Never give the builder: this report, reports 87 to 91b, `deep92/private/`, `deep92/code/`, `deep92/out/`, `blind3_build/`, `deep90/`, `deep91/`.
4. The judge builds the full panel in the kit's column order from `deep92/private/idmap_blind4.csv` (as `deep91/code/build91.py` did for blind 3), checks the hashes, runs the frozen `FACTORIES` unchanged with 100 twins on both data sets, runs the builder's whole list, and runs EMG2-18 and the BLIND3 primary as undisclosed comparators.
5. The judge reports holdings carried across a disputed corporate-action day (section 5.2 item 5) and both payout bounds.

### 6.5 What to expect, so that the result is read fairly
- A set of three tied designs will usually land in the middle of its list. On blind build 3's list that was level with the fund. A result of "beats its twins, level with the fund" would be a normal outcome and not a failure of the method.
- One build cannot show that a set is better than a pick. When three designs are tied, the pick is the best of the three about one time in three, and then it beats the set. The useful readings are the set against its twins, and how far the set sits from the worst member.
- The kit's wrapper was written by someone who had seen that small separate sub-accounts do badly (section 1.4). That is a fact about parcel size, not about any signal, but it is hindsight.

## 7. For the record keeper (the ledger was not written)

1. **Trial count. N 2,347 → 2,496 (149 in this review).** All on seen data, none a candidate.
   - 142: the blind-3 builder's other grid designs on January 2018 – November 2026 (148 less the 6 run in report 91b).
   - 2: the BLIND3 primary and EMG2-18 each run on A$5,000.
   - 3: three blind-3 designs each run on A$3,333.
   - 1: the three-design set in one account.
   - 1: the EMG2-18 + BLIND3 pair in one account.
   - Not counted: twins, start months, spread stresses, the vendor cross-check, the smoke tests of the kit wrapper on random strategies, the data checks of section 5.
2. **Blind build 4.** Record the hashes of `deep92/METHOD_LESSONS_FOR_BLIND4.md` and the kit (`deep92/out/blind4_hashes.txt`) before the builder starts. Cut-off 29 Dec 2017. Bar fixed in section 8 of the briefing.
3. **Paper line for the one-account pair: register if the owner or the coordinating session agrees**, from `deep92/AMENDMENT_shadow_PAIR.DRAFT.md`, with 100 twins, before the 30 Nov 2026 decision. Paper only. No trial beyond item 1.
4. **Owner decision to record (section 4.3):** keep the 24-month paper requirement for BLIND3, or replace it by the June 2027 decision with the four conditions listed. No change is made by this report.
5. **Corporate actions.** (a) Draft and register a short data-procedure amendment for the manual corporate-action table and the `CA_SUSPECT` flag (section 5.2) before the first forward event. (b) Build the table back to 2018 from `deep92/out/inspecie_events.csv`; first BHP (May 2022), Link (Dec 2022), Premier Investments (Jan 2025), Tabcorp (May 2022), St Barbara (Jul 2023). (c) Note for the trading system's owner: unmanaged positions, account value, the simulated twin and the approval rule (section 5.3). This is a go-live checklist item to assess, not a blocker I can set.
6. **Wrong exclusions.** The fund name rule excludes ordinary companies (Electro Optic Systems, Pinnacle, Premier Investments, Helia, Navigator Global, Australian Ethical, COG Financial; list in `deep92/out/excl_check.log`). Decide whether to correct the forward "ordinary share" rule by amendment; if so, from a stated date and for all paper lines at once. Do not change any kit.
7. **Correction to the reading of report 91b, to be noted beside it:** its section 0 point 8 ("the choice between neighbours again showed no skill") is extended by section 1.2 here: the choice between kinds of strategy was a tie-break of 0.2 points, and the next kind's pick made −3.5% / −2.7%. Report 91b's figures stand.
8. **Uploads.** This report to the research folder. Do **not** upload `deep92/private/`, and do not place `METHOD_LESSONS_FOR_BLIND4.md` or the kit where a future builder could also see the reports.
9. **No live amendment is proposed.** EMG2-18 as registered for the mid-December go-live.

## 8. Limits

- Sections 1 to 3 are hindsight on a period seen many times. Section 1.2 shows what the list contained; it does not show that any rule would have found the best kind.
- "The pick the rule nearly delivered" assumes the tie between the first two kinds going the other way and everything else unchanged. It is one counterfactual, not a distribution.
- The set and the pair in one account use the new kit wrapper. It has been checked against single books and by the as-of audit, not against an independent implementation.
- In the one-account pair the EMG2 half sizes its parcels on its share at the decision close, where the registered rule sizes on the account at the fill. Its twins use the members' twin settings calibrated on A$10,000 books; the set's twins sent about a quarter fewer orders than the set (53 against 74), outside the one-fifth tolerance, so the set's percentile among twins is somewhat flattered.
- Sub-accounts and the one-account books were run from the same 12 start months as report 91b, all in 2018. First-year figures from them are one year's experience and are not quoted.
- The spread is a model; no real fill exists.
- The corporate-action comparison finds days where two files disagree. It cannot find events both files miss, and it does not decide which file is right. Codes that changed hands between companies were excluded by requiring the same close in both files.
- The panel has no delisting reasons after April 2020 (report 90). Payout bounds were not re-run here.
- The blind-4 briefing's number tells the builder that earlier briefings existed. It says nothing of what they contained.
- Intermediate files of the 148-design run are kept (`deep92/out/grid_*.pkl`, 0.3 MB each). No full panel was built in `deep92/`; the runs used `deep91/fullR` and `deep87/fullW`.

## 9. Files

| What | Path |
|---|---|
| This report | `onedrive/research2/92_review_after_blind3_fable.md` |
| Briefing for blind builder 4 | `scratchpad/deep92/METHOD_LESSONS_FOR_BLIND4.md` |
| Kit for blind builder 4 | `scratchpad/deep92/blind4_kit/` (`README.md`, `acct3.py`, `tools4.py`, `data/`) |
| Label map (never to the builder) | `scratchpad/deep92/private/idmap_blind4.csv` |
| Hashes; self-check; smoke test; kit build log | `deep92/out/blind4_hashes.txt`, `selfcheck_blind4.log`, `smoke_blind4.log`, `build_blind4.log` |
| Kit build and checks | `deep92/code/build_blind4.py`, `selfcheck_blind4.py`, `smoke_blind4.py` |
| Draft paper-line amendment for the pair | `scratchpad/deep92/AMENDMENT_shadow_PAIR.DRAFT.md` |
| 148 designs on the judged period | `deep92/code/run92.py`, `grid_read92.py`; `out/grid_judged_panel.csv`, `grid_judged_vendor.csv`, `grid_read_*.log` |
| Sub-accounts, one-account set and pair, twins | `deep92/code/run92.py`, `ens92.py`, `combo_read92.py`, `ensu_read92.py`; `out/combo_*.csv`, `combo_read_*.log`, `ensu_read_*.log` |
| Corporate-action and exclusion checks | `deep92/code/inspecie92.py`; `out/inspecie_events.csv`, `inspecie_events.log`, `inspecie92.log`, `excl_check.log` |
| Progress log | `deep92/PROGRESS.md` |
