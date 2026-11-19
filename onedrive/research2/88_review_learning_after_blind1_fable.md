# 88. Review and learning after blind build 1 — what went wrong, what it tells us about EMG2-18, and how blind build 2 will be run

19 November 2026. Author: Fable, as reviewer (step 2 of the owner's cycle: blind build → review and learning → next blind build at a later cut-off). Reviews report 87.
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. No vendor credits were used.
Work folder: `scratchpad/deep88/` (`PROGRESS.md`, `code/`, `out/`). Briefing for the next builder: `deep88/METHOD_LESSONS_FOR_BLIND2.md`. Kit for the next builder: `deep88/blind2_kit/`.

How to read the figures: as in report 87. A$10,000 once; "a year after tax" = after IBKR brokerage, modelled spread and 32% tax, everything sold at the end. Fund = ASX 200 with dividends, 7.4% a year after tax for 2018–Oct 2026. Two data sets: the research panel (dead companies included) first, the vendor file second. Twins = books with the same structure that pick at random.

## 0. Answer first

1. **Blind build 1 did not fail because the idea failed. It failed because its choice rule picked nearly the worst design of its own list.** The builder scored 72 structures in ranks 101–900 on pre-2018 data. Run on 2018–Oct 2026, the middle one of those 72 made **13.0% / 10.3% a year after tax**; 63 / 45 of the 72 beat the fund. The one the rule chose made 6.0% / 3.5% and ranked **65th / 63rd of 72** (three start months each).
2. **The first stage of the build was right and the second stage undid it.** Stage 1 chose "ranks 101–900, three-part momentum score, age-and-price filter" at the plain structure (18 names, sell when off the best fifth, monthly). That design made **18.4% a year** on the mean of 12 start months (panel; 16.4% / 15.3% on three starts), against 12.5% / 10.2% for the registered EMG2-18. Stage 2 then changed it to 10 names with a 6-month minimum hold. That one corner cost 12 points a year.
3. **Why stage 2 went wrong: the score could not tell structures apart, and the tie-break then chose by a side effect.** On the design data itself the score's ranking of the 72 structures did not repeat when the start months were changed (rank correlation −0.2). Out of sample it had no link to results (−0.13 / −0.09). The rule "among near-ties take the fewest trades" then picked the most concentrated, slowest book, and in 2018–26 fewer trades went with worse results (+0.5 correlation between trades and return).
4. **So the comparison "blind-built +1.5% against registered +11.3%" overstates what was learned.** It is one design, from one cut-off, on one period. The fair reading of report 87 is: the signal family held up out of sample at the owner's real size; the fine structure (how many names, how long to hold) cannot be chosen from ten years of data at A$10,000; and EMG2-18's own band is not special.
5. **EMG2-18: keep for the December go-live.** Nothing here is a reason to change live rules. Its result leans on five companies against the fund, but not against random picking: with its five best holdings removed it still made 4.0% a year, above 90 of its 100 twins as they stand and above every twin with its own five best removed.
6. **The A$6,000 loss limit will be reached in an ordinary bad patch, and "halt buys and wait" is the worst way to sit there.** 31 of 100 random twins touched A$6,000 at a month-end in 2018–26. The owner should sign a default now (section 4.2).
7. **Register the H6 paper twin, with a changed reading rule.** The draft's test (value within 3% after 12 months) cannot work: the two books differ by 15 points after a year from luck alone.
8. **The method changes for blind build 2** are in section 3 and in the briefing: score on five separate windows with many start months, choose the centre of a good neighbourhood and not the best single design, a pre-declared default that wins ties, concentration and cost tested against twins like for like, the choice rule tested on earlier folds before it is trusted, and a family of designs frozen and judged, not one.
9. **Trials: 1,919 → 2,026.** This review ran 107 designs on 2018–Oct 2026 that had not been run there before. None is a candidate; all are counted.

## 1. What blind build 1 got wrong, in order of damage

### 1.1 One design, one cut-off, one period
The experiment had a sample of one. Its own numbers show how wide the luck is: the chosen book made between 1.5% and 13.1% a year depending only on which of 12 months it started. A comparison of single books cannot separate method from luck. Report 87 said so in its limits; the headline did not.

### 1.2 The score J
J was "the worse of the two five-year halves' after-tax lead over the fund, with the three best holdings removed", from three start months. Measured on the design data alone (pre-2018, `out/e1_noise.log`):

| Test of J on 2008–2017, 72 stage-2 designs | Result |
|---|---|
| Spread of one design's half-score across 12 start months | 4 to 8 points a year |
| Spread of J between the 72 designs | 3.8 points (three starts); 2.2 points (12 starts) |
| Rank correlation, J from six start months against J from the other six | −0.20 |
| Rank correlation, first half against second half, across designs | −0.32 |
| The design that was best on another set of three start months: its rank on all 12 | 65th of 72 |
| Chosen design's J on 12 starts; its rank | −3.1; 11th of 72 |
| Average J on 12 starts: 18 names against 10 names | −3.9 against −6.6 |

The noise from the start month was larger than the differences the rule acted on. Taking the worse of two noisy halves and removing three holdings from books of 10 made it worse, not safer. With 12 start months the same data would have leaned to 18 names.

Out of sample (`out/diag88.log`, `out/e2w.log`):

| Does the design score predict 2018–Oct 2026? (rank correlation; panel / vendor) | Stage 1: band, score, filter (32) | Stage 2: structure (72) |
|---|---|---|
| J | +0.46 / +0.40 | −0.13 / −0.09 |
| Plain after-tax return over the whole design window | +0.71 / +0.64 | +0.06 |

Coarse choices (which score, which part of the market) could be read from pre-2018 data, and a simpler score read them better. Fine structure could not be read at all.

### 1.3 The tie-break "fewest trades"
Among designs within 1.0 point of the best J the rule took the one with the fewest trades. The 1.0-point band was far inside the noise, so the tie-break made the choice. Brokerage was already inside every return, so the cost was counted twice. Fewer trades is reached by fewer names and longer holds, which is where the risk is.

### 1.4 One stage at a time, and a check that could not fail
Band and score were fixed at stage 1 on a margin of 0.3 points (101–900 against 101–600), then structure was searched only inside that band. The twin check used 30 twins, one start month and the same data that had chosen the design; a design picked for doing well on those data passes it by construction (it scored 100%).

### 1.5 Ten names and the 6-month hold
The 16 combinations of band, names, hold and filter, 2018–Oct 2026, mean of 12 start months, panel (`out/e3_factorial.csv`):

| Return a year after tax (with three best removed) | 18 names, no hold | 18 names, 6-month hold | 10 names, no hold | 10 names, 6-month hold |
|---|---|---|---|---|
| Ranks 301–600, registered filter | **12.5% (7.5)** registered | 14.1% (9.4) | 19.8% (10.1) | 19.5% (10.1) |
| Ranks 301–600, age-and-price filter | 18.8% (13.9) | 15.9% (10.9) | 17.0% (11.1) | 14.3% (5.7) |
| Ranks 101–900, registered filter | 12.5% (6.1) | 12.3% (7.2) | 11.4% (−0.1) | 5.2% (−12.1) |
| Ranks 101–900, age-and-price filter | **18.4% (12.1)** stage-1 winner | 11.8% (4.9) | 11.7% (2.3) | **5.9% (−12.7)** chosen |

Averages: 18 names 14.5% (9.0 without three best) against 10 names 13.1% (1.8); no hold 15.3% against 6-month hold 12.4%; worst fall 47% against 54% for 10 names. Ten names did not lower the average much; it made the result depend on three holdings. The 6-month hold helped in ranks 301–600 with the registered filter and hurt in the wide band. Neither effect is consistent enough to act on. The chosen corner was the worst of the 16.

### 1.6 The band 101–900
Not the main fault. At 18 names the wide band did about as well as 301–600. In the chosen 10-name book the loss came from the larger companies: 52 purchases in ranks 101–300 lost A$6,600 in total; 98 purchases in ranks 301–900 made A$8,400. The thin end (601–900) was 16% of purchases and made money on the modelled spread. That spread (0.75% a side) has never been tested against a real fill, so the wide band's result is the least certain number in this report.

### 1.7 The thin-band filter
The registered filter skips any company trading under A$250,000 a day. In 2010–2016 the 300th most-traded company traded A$185,000–310,000 a day, so in the design data the rule emptied band C (7 of 18 slots filled). That is why the registered rules scored badly before 2018 and why the builder moved away from them. It was a dollar threshold meeting a smaller market, not evidence about band C. Dollar thresholds should be ranks or percentiles in any design test.

### 1.8 The bar
The blind-built book was judged against the registered rules on the very period that had chosen the registered band. The registered book had the home ground; losing to it says little. Against the fund the test had almost no power: with a tracking error of 27–35 points a year, the uncertainty on an 8.8-year lead is 9–12 points a year. The only sharp test available is the percentile among twins, and that should be the first condition.

### 1.9 Data hygiene
Good: physical truncation, hashes before the full panel existed, the as-of audit, dead companies included, two data sets, a case table. Found by report 87: the vendor file's missing dead companies and A$0.0001 closes behind report 85's 2010–17 figures. Found in this review:

- **The "12 start months" were not 12 months in a row.** The list was December 2017, then February to December 2018; January 2018 was skipped (`eval87.py`, the same pattern in my first diagnostic). No figure changes materially. An erratum line for report 87 is in section 5.
- **Names in the design data were today's names** (for example a 2023 name on a company cut at 2017). A builder who knows later history could recognise survivors. Harmless in a mechanical grid; not acceptable for the next builder. The new kit uses labels.
- **The engine carried the registered EMG2 rules as its defaults.** The next kit has no defaults.
- Returns below −95% or above +1,000% in a day are treated as missing: 45 cases in the panel. Acceptable; now a stated rule.
- The two data sets disagree by 2 points a year for the registered book and 5 for the chosen blind book. The design ranking survives (rank correlation 0.90 across the 72 designs), the levels do not.

## 2. What the out-of-sample comparison really tells us about EMG2-18

**2.1 It is not an out-of-sample test of EMG2-18.** EMG2's band was found on 2018–26 (report 85). Its 11.3% / 9.2% there, and its place ahead of 99–100 twins, are in-sample.

**2.2 What is out of sample, and it is the good news.** The blind builder's list of designs was fixed on pre-2018 data. Taken as a whole, without choosing among them, the 72 structures made a median 13.0% / 10.3% a year after every cost and tax at A$10,000, against 7.4% for the fund and about 0% for random twins in the same shares. The three-part score was the best of four before 2018 and after on the panel; on the vendor file 6-month momentum alone was level with it after 2018 (9.7% against 8.5%). That is evidence, from data the designs never saw, that this family of rules worked at the owner's size in 2018–26. It is one period, and one in which a few very large winners appeared.

**2.3 EMG2-18 is an ordinary member of that family.** It sits a little below the middle of the blind list (11.7% / 9.5% against a median of 13.0% / 10.3% on the same three starts). Its band is not what makes it work: the wide band did about as well at 18 names. Its traded-value filter costs it (panel, 12 starts: 12.5% → 18.8% without that leg; vendor file, one start: 9.2% → 13.6%; before 2018: −0.6% → +4.1%). That leg is a safety choice for real orders and stays.

**2.4 Concentration.**

| Registered EMG2-18, 2018–Oct 2026, panel | |
|---|---|
| Positions; total gains; total losses; net | 509; +A$75,100; −A$50,200; +A$24,900 |
| Five best holdings | A$17,100: 69% of the net, 23% of all gains |
| Five best holdings of a random twin (median; 90th percentile) | A$5,900; A$9,600 |
| Return a year without the five best | 4.0% (fund 7.4%) |
| Random twins as they stand: median; 90th percentile | 0.2%; 3.9% |
| Random twins without their own five best: median | −6.1% |
| Holdings kept 2 months or less | 278; −A$25,000 in total |
| Holdings kept 6 months or more | 49; +A$26,500 in total |

Two true statements. Against the fund, the lead is five companies; without them the book trails. Against picking at random in the same shares, the lead is not five companies: every book in this band lives on a few winners, and this score found bigger ones than chance did. The second statement is the test of the signal. The first is the owner's risk: in a stretch with no such winners the book will trail the fund and still pay its costs.

The last two rows are the shape of the strategy: more than half of all purchases leave within two months at a loss, and one in ten stays half a year and pays for everything. Any future rule change should be judged on whether it keeps the second group, not on whether it trims the first.

**2.5 Costs.** Brokerage about A$700 a year, 4.0–4.7 points; spread about A$530–610 on the model. The same rules at A$100,000 made 13.0% / 14.3%. The handicap is the size of the account, not the rules.

**2.6 The H6 twin.** A 6-month hold on the registered rules: 14.1% against 12.5% on the panel (12 starts), 9.3% against 10.2% on the vendor file, +4.0% against −0.6% before 2018. Across 68 quarterly starts from 2007 to 2024 on the panel, H6 was ahead after 24 months in 74% of starts. In the wide band the same hold lowered returns by 0 to 7 points. It saves A$250–330 of brokerage a year for certain and its effect on return is unknown.

**2.7 Expectation.** Unchanged from report 87: about level with the fund, plus or minus a lot, with falls near half the account. What this review adds is the reason to hold that view with slightly more confidence in the signal and no more confidence in the particular book.

## 3. What changes in the blind build method

Each change is justified on logic or on pre-2018 data, because the reviewer has seen 2018–26 and every lesson drawn from it is suspect (section 6).

| # | Blind build 1 | Blind build 2 | Why |
|---|---|---|---|
| 1 | Two five-year halves, 3 start months | Five separate three-year windows (2006–08 … 2018–20), 6 start months each, 30 books per design | The start month alone moved a design 4–8 points |
| 2 | Score = worse half, three best removed | Score = mean of the five window leads minus one standard error | A minimum of noisy numbers is noisier than their mean; pre-2018 reliability −0.2 |
| 3 | Best single design | Neighbourhood score: a design is ranked by the average of itself and its one-step neighbours | A good design next to bad ones is noise |
| 4 | Near-ties broken by fewest trades | A default design written before any run wins ties; no tie-break on trades | Costs are already in the return |
| 5 | Band and score first, then structure | One full grid, at most 150 designs, declared in advance | No choice on a 0.3-point margin feeding the next stage |
| 6 | Three best holdings removed, compared with the fund | Five best removed from the design and from each twin, compared like for like | Separates "few winners" (true of every book in small companies) from "lucky winners" |
| 7 | Twin check in-sample, 30 twins, one start | Twins on the shortlist in every window; must beat the twins' median in 4 of 5 windows | The sharpest test available |
| 8 | Cost stress after the choice | Doubled spread as a gate before the choice | No real fills exist |
| 9 | Free choice of N | N below 15 must beat N = 18 by more than the noise floor | Owner's number is 18; on 12 starts pre-2018 data preferred 18 |
| 10 | Dollar liquidity thresholds | Rank or percentile thresholds; slots filled ≥ two-thirds in every window | The A$250,000 test emptied the band in 2010–16 |
| 11 | Choice rule trusted | Choice rule run on earlier folds first (choose on 2006–14, read 2015–17; choose on 2006–17, read 2018–20); if its picks land in the lower half of the grid, the default is delivered | Tests the method inside the design data |
| 12 | One frozen design | A frozen primary design, its family of one-step neighbours, and the default | The judge reads a family, so one corner cannot decide the verdict |
| 13 | No forecast | The builder states an 80% range for the lead over twins before the freeze | Honesty of the forecast can be scored |
| 14 | Bar: beat the registered book | Bar: percentile among twins first, fund second, family third; the registered book is an undisclosed comparator | The registered book has the home ground |
| 15 | Real company names, engine with EMG2 defaults | Labels only, no defaults, builder sees the kit and the briefing and nothing else | The builder is an AI that knows later history |
| 16 | 12 starts with a month skipped | 12 start months in a row, printed and checked | Section 1.9 |

**Multiple cut-offs.** One blind build is one draw. The programme now has cut-offs at December 2017 and December 2020. After blind build 2 the method should be frozen and run unchanged at further cut-offs (December 2014 and December 2023 are the natural ones), and the method judged on the set. Changing the method after every build, as this review does, is itself a way of fitting to 2018–26. This is the last revision that should be made on the strength of that period.

**What blind build 2 cannot do.** Its judged period (2021–Oct 2026, 5.8 years) lies inside the period already seen twice. It is a fairer test of the method than blind build 1, not new evidence about the market. New evidence starts with the forward record on 30 November 2026.

**The kit** (`deep88/blind2_kit/`): the research panel cut at 31 Dec 2020 (5,040 entities, 2,325 of them already dead), labels instead of codes and names, delisting text reduced to a class, column order shuffled; `eng88.py`, the report-87 accounting with no default strategy (it reproduces report 87's 11.3374% on the full panel). The label map is in `deep88/private/` and must not be given to the builder. Built by `code/build_blind2.py`, checked by `code/test_kit.py`.

## 4. Recommendations for the live EMG2-18

### 4.1 Keep the registered rules for the December go-live
No change to `AMENDMENT_live_EMG2_18.md`. The wide band, the 10-name version and the filter without its traded-value leg all look better on 2018–26 in this report. All three have now been seen on that period and none came through a bar set in advance. They are observations.

### 4.2 The loss limit at A$6,000 (rule L11): decide the answer now
What the replays say:

| | |
|---|---|
| Random twins of EMG2-18 touching A$7,000 / A$6,000 / A$5,000 at a month-end, 2018–Oct 2026 | 62% / 31% / 8% |
| Registered rules, 64 quarterly starts 2007–2023, touching A$7,000 / A$6,000 within three years | 25% / 14% |
| How many separate events those were | One: March 2020 |
| Account at the low; 12 months later; back above A$10,000 | A$5,200–5,800; +135% to +149% (fund +34%); 5–8 months |
| Sold at the A$6,000 breach and moved to the fund, value at October 2026 | about A$11,200 |
| Kept running | A$26,100 |

Month-end values understate daily lows, so the real limits are reached more often than this. A fall to A$6,000 is inside the normal range for these shares whether or not the signal works. It is therefore not evidence about the signal. One event is also no proof that holding on is right.

What L11 does as written: buys stop, sells continue, the owner "decides in writing". With a typical holding of two months, a book that sells and does not buy is mostly cash within a quarter. That is the "go to cash" rule that report 87 tested and rejected (11.3% → 6.0%), entered at the low.

Recommended owner decision before go-live, as a signed default so that nothing is decided in the bad week:

1. At A$7,000: page, and an integrity check (live holdings equal the simulated twin; fills and costs as modelled).
2. At A$6,000: buys pause until the next month-end decision at the latest. **They resume automatically unless** (a) the integrity check fails; or (b) the live book's simulated twin is below the 10th percentile of its 100 random twins since the start, meaning the loss is the picks and not the market; or (c) a stop rule of L12 is met; or (d) the owner says stop.
3. At A$5,000: the same test, but the owner must confirm in writing to continue. If he does not within one decision, the book is sold over the next two decisions.
4. The owner should ask himself now whether losing half of A$10,000 on paper, and continuing, is acceptable. If it is not, the remedy is not a tighter limit, which would simply fire. It is not to start, or to hold the fund.

This needs an owner decision and a short amendment by the record keeper. It is not drafted here.

### 4.3 The H6 paper twin: register it, change how it is read
Register `EMG2_18_SIM_H6` as drafted in `deep87/AMENDMENT_shadow_EMG2_18_H6.DRAFT.md`, with section 3 of that draft replaced:

- The draft allows a proposal after 12 months if H6 has saved A$200 of brokerage and its value is no more than 3% lower. Over 68 quarterly starts the 12-month value gap between the two books had a standard deviation of **15 points** (mean +6). The 3% test would pass or fail on luck.
- Proposed reading: report monthly the brokerage saved (a fact) and the value gap (labelled as mostly luck). No proposal to change the live book before the December 2028 review. A proposal then needs both: H6 not behind over 24 months, and a blind build that chose a minimum hold without being told to.
- One twin is enough for now. A second twin for the filter without its traded-value leg has the more consistent back-test (+3 to +6 points in both periods and both data sets) but tests thin shares where the modelled spread is least trustworthy. Add it only after the first live fills give a measured spread for ranks 301–600.

### 4.4 The statement on every live report (L14)
Report 87's wording stands: "about level with the fund, plus or minus a lot, falls near half the account". Add the cost in dollars: about A$700 brokerage a year.

### 4.5 What the live book will teach, and what it will not
It will teach whether fills and spreads match the model, which is the largest open number. It will not show whether the signal works; 18 names for a year cannot. That evidence comes from the A$100,000 paper book, its twins and the band spread, as registered.

## 5. For the record keeper

1. **Trial count.** Report 87: N 1,802 → 1,919 (107 design cells on pre-2018 data, 8 judged or information runs on 2018–Oct 2026, 2 post-freeze runs). Not yet in the ledger. This report adds **107**: 100 of report 87's design cells run on 2018–Oct 2026 for the first time (103 distinct cells less the 3 already run there) and 7 new cells of the 16-cell table in section 1.5. **N: 1,919 → 2,026.** Diagnostic, none a candidate, all on seen data. Start-month repeats, twins, the vendor cross-check and the quarterly-start replays of the registered and H6 rules are not trials.
2. **Erratum to report 85** (as report 87 section 6.5): its 2010–2017 EMG2 figures (11.0% a year against 7.4%; worst falls 38% and 57%) came from a file with almost no dead companies and with A$0.0001 glitch closes. They should not be quoted. They appear in `FD_v3.0_BigWins.md` lines 91, 92 and 579 and in the evidence text of `AMENDMENT_shadow_EMG2.md`. Replacement (research panel, A$100,000, no brokerage): 2010–2017 17.6% a year against 7.4%, worst fall 40%; 2018–Oct 2026 13.1% against 8.5%, worst fall 45%. The 50% drawdown setting of BW-RSK-20 cites the old figures; the setting itself is still reasonable.
3. **Erratum to report 87, minor.** "12 start months (Dec 2017 … Nov 2018)" were December 2017 and February to December 2018. Section 0 item 1 ("the blind build failed") should carry a pointer to this report: the chosen design ranked 65th of the 72 it was chosen from; the median of the 72 made 13.0% / 10.3%.
4. **H6 paper twin: register**, with the reading of section 4.3 in place of the draft's section 3. No trial.
5. **Owner decision needed on L11** (section 4.2), then a short amendment.
6. **Blind build 2.** Record the hashes of `deep88/METHOD_LESSONS_FOR_BLIND2.md` and the kit (`deep88/out/blind2_hashes.txt`) before the builder starts. The builder gets the briefing and the kit only. The judge's bar is section 8 of the briefing and is fixed.
7. **No live amendment is proposed.**

## 6. Limits

- The reviewer is not blind. I have now seen 103 designs on 2018–Oct 2026. Every method lesson was checked against the question "would this be right if I had not seen the result"; the briefing keeps only rules that pass, and lists the residual risks. The choice of which rules to write is still mine.
- Section 0 items 1 and 2 are hindsight about one grid. They show the family held up; they do not show that a better choice rule would have found the best design.
- The grid results use three start months (December 2017, February and March 2018); the 16-cell table uses 12. Month-end clock; daily lows are deeper. No real fills.
- Loss-limit base rates rest on one event for the registered rules and on random twins for the rest.
- The wide-band results depend on a spread model for ranks 601–900 that has never met a real order.
- The kit's results differ from report 87's truncated panel by about 0.1 point a year for the same rules, because the shuffled column order changes tie-breaks.

## 7. Files

| What | Path |
|---|---|
| This report | `onedrive/research2/88_review_learning_after_blind1_fable.md` |
| Briefing for blind builder 2 | `scratchpad/deep88/METHOD_LESSONS_FOR_BLIND2.md` |
| Kit for blind builder 2 | `scratchpad/deep88/blind2_kit/` (`data/`, `eng88.py`); hashes `deep88/out/blind2_hashes.txt` |
| Label map (not for the builder) | `scratchpad/deep88/private/idmap_blind2.csv` |
| All 103 design cells out of sample, both data sets | `deep88/code/diag88.py`, `e2w.py`, `e9.py`; `out/e2_cells_oos.csv`, `diag88.log`, `e2w.log`, `e9.log` |
| 16-cell table | `out/e3_factorial.csv` |
| Noise of the score on pre-2018 data | `code/e1_noise.py`, `e1b.py`; `out/e1_noise.csv`, `e1_noise.log` |
| Concentration, twins, loss limits, H6 gap | `code/e4.py`, `e6.py`; `out/e4.log`, `e4_twins.csv`, `e5_losslimit.csv`, `e6.log`, `e6_h6diff.csv` |
| Kit build and check | `code/build_blind2.py`, `code/test_kit.py` |
| Progress log | `deep88/PROGRESS.md` |
