# 87. EMG2-18 for real money: a blind build from pre-2018 data, replayed on 2018–Oct 2026 against what happened

19 November 2026. Author: research agent (Fable). Owner request: "Let's keep working on the ASX ones and make them better" and "let's try again from a blind build."
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. No vendor credits were used.
Work folder: `scratchpad/deep87/` (`PREREG_87A.md`, `PREREG_87B.md`, hashes in `out/prereg87_hash.txt`, `code/`, `out/`, `PROGRESS.md`). Every position of both books with its outcome: `87_case_table_blind_build.csv` (659 rows).

How to read the figures: A$10,000 put in once. "After tax" = after IBKR brokerage (A$6.60 an order), the modelled buy/sell spread, 32% tax on realised gains each June (halved only for holdings over 12 months) and everything sold and taxed at the end. Index = ASX 200 with dividends, held throughout, taxed once at the end: **7.4% a year after tax for 2018–Oct 2026**. t = mean ÷ standard error of the monthly gap to the index; about 2 is "probably not luck". Twins = 100 books with the same structure that pick at random from the same band.

## 0. Answer first

**Keep the registered EMG2-18 rules for the December go-live. Nothing built here beats them. No live amendment is drafted.**

| 2018–Oct 2026, A$10,000, all costs and tax | Registered EMG2-18 | Blind-built book | ASX 200 fund |
|---|---|---|---|
| Return a year after tax (research panel / vendor file) | **+11.3% / +9.2%** | +1.5% / −3.8% | +7.4% |
| A$10,000 became (after selling and tax) | A$25,800 / A$21,700 | A$11,400 / A$7,100 | A$18,800 |
| Lead over the fund, points a year | +3.9 / +1.7 | −5.9 / −11.3 | — |
| t against the fund | 0.7 / 0.5 | 0.0 / −0.4 | — |
| Random twins beaten (of 100) | 100 / 99 | 61 / 41 | — |
| Worst fall (month-end values) | −48% / −47% | −64% / −57% | −23% |
| Trades a year; brokerage a year; spread a year | 110; A$724; A$611 | 31; A$207; A$161 | — |
| Return with the 3 best holdings removed | +6.7% / +4.2% | −11.6% / −16.2% | — |

1. **The blind build failed.** A design chosen mechanically from data that stopped on 29 Dec 2017 (10 companies, ranks 101–900 by traded value, same three-part momentum score, 6-month minimum hold) made +1.5% a year in 2018–Oct 2026, behind the fund, behind the registered rules in 11 of 12 start months, and no better than picking at random. All five conditions of the pre-set bar failed.
2. **A designer without knowledge of 2018–26 would not have arrived at EMG2-18.** On pre-2018 data at A$10,000 the registered rules ranked about 20th of 32 choices of band and score and made −0.6% a year (fund +3.4%). EMG2's band was found by looking at 2018–26 (report 85). Its 2018–26 result is therefore still "seen" data and stays unproven.
3. **What does hold in both periods is the signal, not the small book.** The best fifth of band C by score beat the band average by 2.1 points a month before 2018 (t 5.4) and 1.8 points a month after (t 4.8), before costs. A A$100,000 book with no brokerage made 17.6% a year in 2010–2017 and 13.1% in 2018–26 on the research panel. The registered rules at A$10,000 lost before 2018 because the lottery filter left 3 to 17 names to buy (7 of 18 slots filled on average) and fees ate the rest.
4. **Expected cost drag at A$10,000:** about 105–110 orders and **A$690–725 brokerage a year** (replay; the account averaged about A$17,000, so plan on about A$700 from the start, 7% of A$10,000), plus about A$530–610 of spread. Brokerage alone cost **4.0–4.7 points a year**; with no brokerage the same book made 15.3% / 13.9%. With double the modelled spread: 8.6% / 7.4%, level with the fund.
5. **The result leans on a few companies.** 509 positions, 193 made money, the typical one lost 4%. Five holdings (Azure Minerals, MTM, Vulcan, Clarity, Ora Banda) are 69% of the profit. Without the best three the book made 6.7% (fund 7.4%); without the best five, 4.0%.
6. **No crash rule helps.** "All cash while the ASX 200 is below its 10-month average" cut the worst fall from 48% to 38% and the return from 11.3% to 6.0% (vendor file: 47% to 44%, 9.2% to 4.3%). It was rejected on pre-2018 data by the pre-set rule and failed again after. Expect falls near 50%.
7. **The replay breached the registered loss limits.** A$10,000 was A$7,600 at the end of 2018, A$6,500 on 2 Mar 2020 and A$5,200 on 1 Apr 2020 (vendor file A$6,000): under rule L11 buys halt at A$6,000 and the owner decides. It was back above A$10,000 by December 2020. As of November 2026 the replay is 37% below its March 2026 peak (2026 so far −22%).
8. **Young companies should stay out.** Best-fifth names listed under two years lagged the band by 1.0 point a month in 2018–26 (seasoned names led by 2.0). The age rule of the lottery filter is supported. The EARLY signal cannot be used inside EMG2: about a fifth of EARLY's purchases ever reached EMG2's list, nearly all before their second anniversary, where the age rule blocks them.
9. **One candidate for a paper twin, not for money:** a 6-month minimum hold on the registered rules cut brokerage to about A$405 a year (61 orders) and returned 14.2% against 11.3% on the research panel, but 9.5% against 9.2% on the vendor file and lower on the mean of 12 start months there (9.3% against 10.2%). Not a clear improvement. Draft: `deep87/AMENDMENT_shadow_EMG2_18_H6.DRAFT.md`.

## 1. What was done and what makes it blind

- **Truncated data.** `deep87/blind/` holds prices, traded value, listings, delistings and the index to 29 Dec 2017 only (4,658 companies; later listings and later delistings absent). The full panel was built only after the rules, the code and the bar were hashed (`PREREG_87B.md`, 11:33 UTC; hashes of data and code in `out/prereg87_hash.txt`).
- **Cut-off 29 Dec 2017:** the programme's standing split; 10 design years including 2008; 8.8 judged years.
- **Mechanical choice.** 107 designs were scored on pre-2018 data by one number fixed in advance: the lower of the two five-year halves' after-tax lead over the fund with the three best holdings removed ("J"). Among designs within 1.0 point of the best, the one with the fewest trades was taken, subject to beating 80% of 30 random twins.
- **Not blind:** the author had read report 85 and knew EMG2's 2018–26 result. The grid's ingredients (three published momentum measures, liquidity bands, buffers, holding periods, the 10-month average rule) were all public before 2018, and EMG2 was one cell of 32, not the starting point. The author's knowledge could still have shaped the grid.
- **As-of audit.** Target lists recomputed from panels cut at 30 Aug 2019 and 31 Mar 2023 were identical to the full-panel lists for both books.
- **Data.** Primary: the research panel of report 84 (every ASX company including the dead; 120–165 companies ending each year). Cross-check: the vendor file of report 85, the data family of the forward record.

**Two faults found in report 85's 2010–2017 figures for EMG2 (11.0% a year, worst fall 57%).** The vendor file holds almost no company that ended before 2017 (89 of 3,769). It also has glitch closes of A$0.0001 (AUR, LNR, AUC, AAU in 2011) which the back-test charged as a 500% spread. Those figures should not be quoted. The 2018–26 figure (13.3%) is reproduced here on the research panel (13.1%).

## 2. The design stage (data to 29 Dec 2017 only)

Structure tested at the owner's real size: A$10,000, IBKR max(A$6.60, 0.088%), half-spread 0.25–0.75% by liquidity with a half-price-step floor, A$500 minimum order, tax as above.

**Stage 1 — band, score, lottery filter (32 cells; registered structure: 18 names, sell when off the best fifth, monthly).**

| Band (traded-value ranks) | Score | Lottery filter | J | Dec 2007–Dec 2017 a year after tax |
|---|---|---|---|---|
| 101–900 | three-part | age and price only | **−5.4** | +9.0% |
| 101–600 | three-part | age and price only | −5.7 | +10.2% |
| 101–600 | three-part | registered | −6.2 | +6.5% |
| 101–300 | three-part | age and price only | −8.0 | +2.8% |
| **301–600 (EMG2's band)** | three-part | **registered** | **−13.0** | **−0.1%** |
| 301–600 | three-part | age and price only | −16.2 | +5.1% |
| Single measures (12-1, 6-month, 52-week high) | | | −9.6 to −25.0 | |

Fund after tax in the same window: +3.4%. Band C held only 61–149 eligible companies in 2010–2016; the registered filter's traded-value leg (under A$250,000 a day is skipped) left 3–17 of the best fifth buyable, because the 300th-ranked company traded only A$185,000–310,000 a day then (A$680,000–790,000 in 2022–2025).

**Stage 2 — structure (72 cells in ranks 101–900).** Best J −0.8. Three cells within 1.0 point; fewest trades: **best fifth, 6-month minimum hold, monthly, 10 names** (J −1.6; 31 trades a year; +13.4% a year; worst fall 61%; ahead of all 30 twins). What the grid showed about turnover:

| Change (others as chosen) | Trades a year | J |
|---|---|---|
| No minimum hold, 18 names (registered structure) | 72 | −5.4 |
| 6-month minimum hold, 18 names | 50 | −3.0 |
| 6-month minimum hold, 10 names (chosen) | 31 | −1.6 |
| 13-month minimum hold (tax discount), 10 names | 17 | −7.0 |
| Keep while in the best 50%, 13-month hold, quarterly, 10 names | 12–13 | −4.1 to −5.7 |
| Keep while in the best 35%, no minimum hold, 18 names | 47 | −1.4 |
| Quarterly instead of monthly (36 pairs) | 25 against 32 on average | worse in 19 of 36 |

Average J by setting, over all cells: minimum hold none −7.4, 6 months −5.6, 13 months −6.7; sell below the best 20% −5.4, 35% −7.1, 50% −7.2; monthly −6.4, quarterly −6.8; 18 names −6.3, 10 names −6.9. **Every turnover device cut trades (to as few as 12 a year) and none separated from the others by more than 2 points.** "Sell only when replaced" is the buffer with fixed slots and was not a separate cell. **J was negative in all 107 cells and noisy** (neighbouring cells differ by several points): with 10–18 names, removing three winners decides the ranking. Pre-2018 data cannot tell these structures apart at this size.

**Stage 3 — crash rule (4 cells).** ASX 200 below its 10-month average, all cash: worst fall 61% → 36%, J −1.6 → −5.0. Band index below its 10-month average, all cash: 33%, J −7.9. No-new-buys forms: 50–57%, J −8.1 and −21.6. The pre-set rule needed J to fall by no more than 1.0. **None added.**

## 3. Out of sample: 29 Dec 2017 – Oct 2026, decision by decision

Main table in section 0. More detail (research panel first, vendor file second):

| | Registered EMG2-18 | Blind-built |
|---|---|---|
| Mean of 12 start months, a year after tax | 12.5% / 10.2% | 5.9% / 1.9% |
| Range over 12 start months | 11.3–14.6% / 9.2–12.3% | 1.5–13.1% / −4.7–11.9% |
| Without best 1 / 3 / 5 holdings (panel) | 9.7 / 6.7 / 4.0% | −4.4 / −11.6 / −32% |
| Twins: 10th / median / 90th percentile (panel) | −5.3 / +0.2 / +3.9% | −5.1 / −0.3 / +6.8% |
| Spread doubled | 8.6% / 7.4% | −2.9% / −10.6% |
| No brokerage | 15.3% / 13.9% | 3.3% / 0.3% |
| Same rules at A$100,000 | 13.0% / 14.3% | 8.2% / −0.7% |
| Positions; made money; typical result | 509; 38%; −4% | 150; 39%; −8% |
| Slots filled on average; cash | 14.0 of 18; 11% | 9.3 of 10; 2% |
| Tracking error against the fund | 27 points | 35 points |

Registered EMG2-18 by year (panel): 2018 −24%, 2019 +2%, 2020 +24%, 2021 +42%, 2022 −10%, 2023 +44%, 2024 +61%, 2025 +12%, 2026 to October −22%. Fund: −3 (2018), +25, −1, +14, +6, 0, +23, +5, +7.

**Bar of PREREG_87B for a live amendment (all five needed):** (a) blind-built ahead by 2.0 points on the mean of 12 starts: −6.6, fail; (b) ahead in 9 of 12 starts: 1, fail; (c) 80th percentile of its twins: 61st, fail; (d) ahead with three best removed: fail; (e) worst fall no more than 5 points deeper: 16 deeper, fail. The vendor file gives the same five fails.

**Case table, registered EMG2-18 (panel).** 299 sold for falling off the list (average −10%); 154 sold for leaving the band, mostly upward (average +37%); 33 paid out in takeovers or stopped trading at about their last price; 7 bid-peg sales; 16 open at the end. In the 12 months after a sale the typical sold share fell 2%; 11% of them doubled. Best: Azure Minerals +646% (6 months), Vulcan +537%, De Grey +365%, MTM +273%, Clarity +272%. Worst: Terra Metals −48%, EZZ −48%, Starpharma −40%. Profit by purchase year: 2018 −A$2,150, 2019 −A$1,080, 2020 +A$6,660, 2021 +A$1,570, 2022 −A$640, 2023 +A$9,170, 2024 +A$10,530, 2025 +A$6,890, 2026 −A$6,050.

**Case table, blind-built.** 150 positions; 13 at least doubled (Vulcan +778%, Chalice +397%, Temple & Webster +339%); 35 lost 40% or more and four went to zero (AVZ, Firefinch among them). 2021's purchases lost A$8,100 in the 2022 fall. The 6-month hold kept it in falling shares; ten names made each loss count.

## 4. Falls and the crash rule

Falls of the registered book beyond 25% (panel, month-end values; daily lows are deeper): **−48%** Jan 2018 → Apr 2020 (recovered Sept 2020); **−28%** May 2022 → Jan 2023 (recovered Sept 2023); **−37%** Mar 2026 → Aug 2026, not recovered. Random twins had a median worst fall of 43%: the falls belong to the band, not to the score.

| "All cash while the ASX 200 is below its 10-month average" (information runs) | Return a year | Worst fall |
|---|---|---|
| Registered EMG2-18, without → with (panel) | 11.3% → 6.0% | −48% → −38% |
| Registered EMG2-18, without → with (vendor) | 9.2% → 4.3% | −47% → −44% |
| Blind-built, without → with (panel) | 1.5% → 0.5% | −64% → −49% |

The rule sells after the fall and misses the rebound (April–December 2020). It does not earn its place.

**Rule L11 against the replay.** The page at A$7,000 would have fired on 2 Mar 2020 (A$6,536) and the buy halt at A$6,000 on or before 1 Apr 2020 (A$5,231; the vendor-file replay touched A$5,959). The halt at A$5,000 was probably crossed on a day inside March 2020. The following nine months took the book to A$10,000 and the next year added 42%. The owner should decide now what he will do at A$6,000, because the replay says that moment arrives in a normal bad patch.

## 5. Young companies and EARLY inside EMG2 (measured, nothing tuned)

Best fifth of band C, next month's return minus the band average, no costs:

| Group | 2008–2017 | 2018–Oct 2026 |
|---|---|---|
| All | +2.1 a month (t 5.4) | +1.8 (t 4.8) |
| Listed under 504 sessions | +1.8 (t 1.7; 397 cases) | **−1.0 (t −0.9; 272 cases)** |
| Listed longer | +2.1 (t 5.0) | +2.0 (t 4.8) |
| Close under A$0.20 | +3.2 (t 1.5) | +3.7 (t 1.9) |
| Traded value under A$250,000 only | +2.4 (t 4.8) | +1.4 (t 2.5) |
| Passes the registered filter | +1.0 (t 1.7) | +1.8 (t 3.8) |

- **Age rule: keep.** Removing the age and price rules from the blind-built book cut its return from 1.5% to −4.5%.
- **Traded-value leg: it costs slots, not quality.** Names failing only that leg did as well as the rest. The registered book with age-and-price filtering only made 17.3% / 13.6% (against 11.3% / 9.2%), with 15 slots filled instead of 14. Before 2018 the same change gave +4.1% against −0.6% on the panel. It is a safety rule the owner chose for real money (thin shares, A$550 orders), and this was an information run among six, so it is reported, not recommended. On 30 Oct 2026 the list had 38 names, 26 buyable, none young: the filter does not bind today.
- **EARLY inside EMG2.** Of 149 EARLY purchases in the replays of report 86 (ASX, all windows), 73 were in band C at some month-end in the next three years, 30 were ever on EMG2's list, and 25 of those were there before session 504, where the age rule blocks them. So "young companies entering band C" is exactly the group that did worst on the list in 2018–26. EARLY's own evidence is six unseen purchases with the lead from one company. **No.** Keep EARLY as its separate paper line.

## 6. What this changes

1. **Go-live rules: unchanged.** `AMENDMENT_live_EMG2_18.md` stands. No `AMENDMENT_live_EMG2_18_v2` is drafted, because no variant passed the bar set before the data was opened.
2. **Statement of expectation, corrected with real-size numbers.** Replayed at A$10,000 with every cost and tax, the registered rules made 9–11% a year in 2018–Oct 2026 against 7.4% for the fund: +2 to +4 points, t 0.5–0.7, on a period that chose the rule. Before 2018 the same rules lost to the fund. The amendment's sentence "expected result at this size is below the index even if the signal works" was too pessimistic for 2018–26 and right for 2008–17. A fair forward statement: about level with the fund, plus or minus a lot, with falls near 50%.
3. **Evidence standing of EMG2.** Stronger on the signal (two periods, t about 5 each, dead companies included). Weaker on the book: its pre-2018 back-test in report 85 was faulty, and a blind designer would not have picked it.
4. **Offered as a paper twin only:** `EMG2_18_SIM_H6` (6-month minimum hold), draft in `deep87/`. It answers one question in a year or two: does holding longer save the A$300 a year without losing return.
5. **For the record keeper.** Report 85's 2010–2017 EMG2 figures and the amendment text that quotes them ("11.0% against 7.4% in 2010–2017", "worst falls 38% and 57%") need an erratum. Replacement on the research panel: A$100,000 book, no brokerage, 2010–2017 17.6% a year after yearly tax against 7.4%, worst fall 40%; 2018–Oct 2026 13.1% against 8.5%, worst fall 45%.

## 7. Trial count

Design cells on pre-2018 data: 107. Runs on 2018–Oct 2026: blind-built, registered EMG2-18 at real size, two crash-rule runs, two structure runs, two filter runs = 8. After the freeze, labelled as such: the 6-month hold, the 10-name and the filter variants on pre-2018 band C, and one combined variant = 2 more. Twins, cost stresses, start months, the vendor cross-check, the audit and the re-run of report 85's book are not trials. **N: 1,802 → 1,919.** The ledger was not written.

## 8. Limits

- The author was not blind (section 1). The registered rules' 2018–26 result is on the period that chose them.
- Month-end clock and month-end values; daily falls are deeper. Fills at the next close with a modelled spread; no real fills exist yet.
- Not modelled: whole-share rounding, the A$800 order limit, the 10% cap, owner approval delays, unfilled limit orders, interest on cash, dividends tax and franking.
- Tax at 32% from the book's own cash each June; the owner's rate and timing will differ.
- Two data families disagree by about 2 points a year for the same rules (11.3% against 9.2%); the vendor file is the one the live system uses.
- Company class uses today's names and the 2026 LIC list (a small look-ahead in the design stage). A stopped company with no recorded reason is valued at its last price if within 30% of its year high, else zero.
- The design score J is noisy at 10–18 names; a different fixed score could have picked a different design. That is a finding about how little pre-2018 data can say at this size.
- After the freeze `eng87.py` gained a statistics line and one option used only for the re-run of report 85's book; the frozen copy is `code/eng87_frozen.py` and both give identical results for the judged books.

## 9. Files

| What | Path |
|---|---|
| Pre-registrations and hashes | `scratchpad/deep87/PREREG_87A.md`, `PREREG_87B.md`, `out/prereg87_hash.txt` |
| Truncated and full panels | `deep87/blind/`, `deep87/full/`, vendor cross-check `deep87/fullW/` (`code/build87.py`, `code/mkW.py`) |
| Engine | `code/eng87.py` (frozen copy `code/eng87_frozen.py`) |
| Design stage | `code/design87.py`, `out/design.log`, `design_S1.csv`, `design_S2.csv`, `design_S3.csv`, `design_choice.json` |
| Out-of-sample runs | `code/eval87.py`, `out/eval.log`, `eval.json`, `eval_fullW.log`, `eval_fullW.json`, `cases_*.csv`, `nav_*.csv` |
| Audit, young companies, EARLY, cost table, variants | `code/post87.py`, `post87b.py`, `out/post.log`, `post_b.log`, `early_in_emg2.csv` |
| Case table | `onedrive/research2/87_case_table_blind_build.csv` |
| Draft paper twin | `deep87/AMENDMENT_shadow_EMG2_18_H6.DRAFT.md` |
