# 94. Review after blind build 4 — what four blind builds have taught, whether a fifth is worth doing, and what to do next

19 November 2026. Author: Fable, as reviewer (owner's cycle: blind build → review and learning → next blind build). Reviews report 93.
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. The ledger was not written. No vendor credits were used.
Work folder: `scratchpad/deep94/` (`PROGRESS.md`, `code/`, `out/`).

How to read the figures: as in report 93. A$10,000 once; "a year after tax" = after brokerage (A$6.60 an order), the modelled spread and 32% tax, everything sold at the end. Fund = ASX 200 with dividends, 7.7% a year after tax for January 2018 – November 2026. A figure is the mean of 12 start months (December 2017 to November 2018) unless stated. Research panel first, vendor file second.
**Every figure in section 1 is on data that has been seen before. None is a candidate and none is evidence for a rule.**

## 0. Answer first

1. **Do not run blind build 5 now. No kit was prepared.** A fifth build at the December 2017 cut-off, on the same price-and-volume data, would tell us almost nothing we cannot already read off the results in hand, and what it did tell us could no longer be trusted as blind. Reasons in sections 2 and 3.
2. **The 2018–2026 period is used up as a test.** 445 designs listed by four blind builders have now been run on it, plus EMG2's family. I can state the 2018–2026 result of nearly any price-only rule a fifth builder could propose, to within a couple of points, before it is run. A test whose answer the organiser already knows is not a test.
3. **The proposed fixes for build 5 are the leak.** "The set must span two families" and "leave dividend signals out" were both suggested because of what happened after 2017. I checked the first on builder 4's own list (section 1.3): a cross-family set there would have made 4.5% / 5.0% a year with two families and −0.1% / 2.7% with three, worse than the dividend set that was judged (5.5% / 6.0%). Spanning families gives the average of the families. It helps only when one of them happens to be a winner, and the design data could not say which.
4. **What four builds have taught is mostly negative, and it is settled enough to stop.**
   - Picking one design from past data: no skill among close designs, four times out of four.
   - A set of designs: the average of its members, as arithmetic says. Insurance against a bad draw; not a source of return.
   - Momentum: two particular constructions did well after 2017 (EMG2's, and calm momentum in the top 400). **Plain momentum did not**: builder 4's 36 momentum designs had a median of 1.9% / 2.2% a year, the worst of its four families, and the 2017 data had ranked the family last. "Momentum held up" is true of two books, not of the family.
   - Dividend yield and low volatility: 5–6% a year, behind the fund, in nearly every setting. 0 of 84 low-volatility designs across builds 3 and 4 beat the fund.
   - Three of four blind picks lost to the fund. One won, after a tie-break worth 0.2 points. With one design in ten to one in four of the builders' lists ahead of the fund, one winner in four tries is what chance alone gives (section 2.2).
5. **Learning now has to come forward.** The paper lines start on Monday 30 November and the live A$10,000 slice in mid-December. The first honest out-of-sample numbers, in the order they arrive (section 4): real trading costs against the model (about March 2027 for a first look, about November 2027 for 100 fills); whether the momentum score still sorts shares (first formal reading December 2028); book against random twins (weak for many years); analyst-estimate revisions (first reading December 2028, more likely December 2030).
6. **Blind builds stay in the tool-box for one use only: data that no earlier build had.** The candidate is a kit with a real dividend file, confirmed corporate actions, official delisting reasons, and point-in-time share counts from the ASIC files (which exist back to June 2010). Conditions in section 5. Even then the judged years are the same ones, so it would test the new data, not the method.
7. **Three small things to do before 30 November, all on paper** (section 3.3): write down now how the analyst-estimate data will be read; confirm the five pending corporate-action rows; make sure the live slice records the mid price at each order so costs can be measured from the first fill.
8. **Trials: N 2,644 → 2,788.** This review ran builder 4's 144 designs on the judged period (section 1.2). None is a candidate.

## 1. What four blind builds have taught

### 1.1 The four builds side by side

| | Build 1 (report 87) | Build 2 (report 89) | Build 3 (report 91b) | Build 4 (report 93) |
|---|---|---|---|---|
| Design data to; judged period | Dec 2017; 2018 – Oct 2026 | Dec 2020; 2021 – Nov 2026 | Dec 2017; 2018 – Nov 2026 | Dec 2017; 2018 – Nov 2026 |
| What the kit handed the builder | EMG2's score and a menu | A menu | No strategy | No strategy; must deliver a set |
| Designs listed | 72 | 81 | 148 | 144 |
| Middle design of the list, a year after tax | 13.0% / 10.3% | 0.1% / −2.1% | 3.9% / 4.0% | 5.2% / 5.2% |
| Designs ahead of the fund | 63 / 45 | 16 / 5 | 13 / 11 | 8 / 11 |
| What was delivered | Momentum, ranks 101–900, 10 names | Momentum, ranks 201–700 | Calm momentum, top 400 | Dividend-yield set, top 500 |
| Its return; the fund's | 1.5% / −3.8%; 7.4% | 4.7% / 6.5%; 7.1% | 12.1% / 8.6%; 7.7% | 5.5% / 6.0%; 7.7% |
| Rank in its own list | 65th / 63rd of 72 | 27th / 6th of 81 | 7th / 9th of 148 | pick 96th / 64th of 144 |
| Random twins beaten (of 100) | 61 / 41 | 100 / 100 | 94 / 99 | 65 / 82 |
| Ahead of the fund | No | No | Yes | No |
| The builder's reasoned default | — | −2.2% / −3.1% | 0.9% / 0.1% | 6.2% / 6.3% |

Build 1's list is a special case: the kit gave the builder EMG2's score, and EMG2's family was shaped with 2018–2026 in view. Its 63 of 72 is not a blind figure. Leaving it out, 21 / 22 of 292 designs listed blind at the 2017 cut-off beat the fund: about 7%.

### 1.2 New in this review: builder 4's whole list on the judged period

Report 93 judged four books. I ran all 144 designs of the builder's grid from the same 12 start months on both data sets (`deep94/code/grid94.py`, `out/grid_read_*.log`, `grid_judged_*.csv`). The reading was written down first (`PROGRESS.md`).

| Family (36 designs each) | What the 2017 data said (family score, points a year) | Kept or dropped by the builder | 2018–2026: middle design | Range | Designs ahead of the fund | Orders a year | Typical worst fall |
|---|---|---|---|---|---|---|---|
| Dividend yield | −2.7 | kept | 5.4% / 6.3% | 3.4 to 7.7 / 4.3 to 8.8 | 1 / 7 | 13 | −46% |
| Low volatility | −4.6 | kept | 5.5% / 5.9% | 3.6 to 6.6 / 4.2 to 6.9 | 0 / 0 | 4 | −39% |
| Rising traded value | −13.0 | dropped | 5.0% / 2.8% | −6.8 to 12.1 / −6.2 to 8.3 | 2 / 1 | 42 | −61% |
| Plain momentum | −11.2 | dropped | 1.9% / 2.2% | −10.6 to 13.1 / −12.7 to 11.6 | 5 / 3 | 38 | −72% |

What this shows:
- **The coarse sorting worked this time.** The two families the builder kept had the better middle and no disasters. The two it dropped had the worse middle and falls of 60–70%. Link between the 2017 score and the judged result across the whole list: +0.34 / +0.56. The ten designs with the best 2017 scores made 6.1% / 6.9%; the ten with the worst made 0.4% / 0.0%.
- **Inside the kept families the scores carried nothing.** Link −0.01 / +0.03 over 72 designs. The design with the best neighbourhood score in each family ranked 34th, 20th, 35th and 9th of 36 on the judged period.
- **Sorting bad from fair was not enough, because fair was below the fund.** Dividend and low-volatility designs made 5–6% against 7.7%. The 2017 data said so too: no design of the 144 had a positive score.
- **The only designs that beat the fund on both data sets** were three six-month momentum designs on the 500 most traded shares and one dividend design. The momentum three sat in a family whose 12-month members lost 8% to 13% a year and fell over 90%. Nobody could have picked them from the 2017 data, and the builder rightly did not.
- The two data sets rank the 144 designs alike (rank link 0.80) but agree on only 4 names ahead of the fund. Near the fund's level, which designs "beat" it depends on the file.

### 1.3 What has repeated across four builds

| Lesson | Build 1 | Build 2 | Build 3 | Build 4 | Standing |
|---|---|---|---|---|---|
| Choosing between close designs has no skill | Pick near the bottom of its list | Pick 5th of 6 in its family | Pick 3rd of 5; won on a tie-break | Pick was the worse member; best-scored neighbours ranked 34th and 35th of 36 | **Settled. 4 of 4.** |
| Coarse sorting (bad kinds from fair kinds) works | Yes | Yes | No | Yes | 3 of 4. Useful for dropping, not for winning |
| The signal beats random choice in the same shares | No | Yes | Yes | Barely (65th / 82nd percentile) | Momentum scores: yes in 2 of 3. Yield: 1–2 points |
| Random books at A$10,000 trail the fund | −7 | −12 | −6 to −8 | −3 (few orders) | **Settled.** 3 to 12 points a year, by turnover and place in the market |
| The builder's reasoned default loses to the fund | — | Yes | Yes | Yes | **Settled. 3 of 3.** |
| Every book lives on about five holdings | Yes | Yes | Yes | Less so (few orders, long holds) | Settled for momentum books |
| Nothing price-only worked inside the 200 most traded | Yes | Yes | Yes | Yes (1 / 2 of 72 ahead of the fund) | **Settled.** |

**On sets.** Report 92 proposed holding the tied designs in equal parts, and build 4 was the test. The set finished between its two members, as arithmetic says it must. Both members ranked the same list, so nothing was diversified. Would a set across families have done better? On builder 4's own list, taking the best-neighbourhood design of each family as full A$10,000 books and averaging:

| Set built from builder 4's list | 2018–2026 |
|---|---|
| The set that was delivered (two dividend designs, one account) | 5.5% / 6.0% |
| Dividend + low volatility (the two kept families) | 4.5% / 5.0% |
| Dividend + low volatility + momentum | −0.1% / 2.7% |
| All four families | 1.6% / 3.1% |
| Every design of the list, averaged | 4.2% / 4.1% |
| Fund | 7.7% |

So "a set helps if it spans families" needs correcting. On builder 3's list a cross-family set made 9.2% / 7.2% because one of its three families was the winner. On builder 4's list no kept family was, and adding the dropped ones made it worse. **A set delivers the average of the families that the builder happened to think of.** In builds 3 and 4 that average was below the fund.

**On momentum.** The honest wording:
- EMG2's construction (three measures, ranks 301–600, a filter on lottery-like shares, prompt selling): 12.5% / 9.9%. Never blind.
- Calm momentum in the top 400 (blind build 3): 12.1% / 8.6%. Blind, once, on a tie-break.
- Plain momentum on the top 200 or 500 (48 designs in build 3, 36 in build 4): middle 4.1% / 1.0% and 1.9% / 2.2%. Blind, and behind the fund.
- Before 2018, at A$10,000, EMG2's own rules lost to the fund (−0.6% a year against +3.4%, report 87 point 2), and the builders' momentum families scored −3 to −11 points a year on the design data.

So the post-2017 success of two momentum books is not something the pre-2018 data predicted. Either the market changed in their favour after 2017 or the two were the lucky constructions. A blind build cannot separate those two readings. Only new years can.

## 2. Is there useful information left in more blind builds at the 2017 cut-off?

### 2.1 What a fifth build could still add

| Question | Can a fifth build at 2017 on this data answer it? |
|---|---|
| Does choosing work? | Already answered four times. A fifth "no" adds nothing; a fifth "yes" would be read as luck. |
| Does a cross-family set work? | Computable today from the lists in hand (section 1.3). No build needed. |
| Is there a price-only family nobody has listed? | Four builders listed momentum (three kinds), 52-week high with a stop, low volatility, dividend yield, rising traded value. What is left on prices and traded value alone is short-term reversal and calendar effects, both of which trade far too often for A$6.60 an order. Small chance of anything new. |
| Is the builder calibrated? | Yes, three times running (reports 89, 91b, 93). Settled. |
| Is BLIND3 real or a lucky draw? | Not answerable by another build. Needs new years. |

### 2.2 The leak, assessed honestly

How information about 2018–2026 can reach a "blind" builder, and how much has:

| Channel | What has happened so far | How bad |
|---|---|---|
| **1. The briefing's method lessons.** Each briefing was written by a reviewer who had seen the results. | Briefing 4 was audited line by line (its section 9); every market fact in it is dated 2017 or earlier. Builder 4 then chose dividends, dropped momentum, and lost. A builder who had been steered to the answer would not have done that. | Small so far. This is real evidence that the briefings were clean. |
| **2. The shape of the protocol.** Menu removed after build 2. One pick replaced by a set after build 3. | Three changes to the rules of the game, each made because of a judged result on the same years. Each was defended on arithmetic or on pre-2018 folds. But the choice of *which* sound argument to act on was made with the answer in view. | Moderate, and growing with every round. |
| **3. The fixes proposed for build 5.** "Span at least two families." "Leave out dividend signals." | Both exist only because the dividend set lost after 2017. On the 2017 data the dividend family was the *best* of builder 4's four. Removing it takes away what an honest 2017 designer would choose. Forcing a second family pushes the set towards the families that I know did better. | **Large.** This is the step at which the loop would start learning the answer. |
| **4. Stopping when something wins.** Builds continue until one beats the fund; that one gets a paper line. | BLIND3 was registered after it won. With 7% to 23% of blind-listed designs ahead of the fund, the chance that at least one of four picks beats it by luck alone is 25% to 65%. One did. | Already present. It is why BLIND3's registration says "tracked, not evidence". |
| **5. The builder is the same model as the reviewer.** Its training runs to 2026. | Company names are hidden. But general knowledge (which years fell, that large companies led, that some styles did well) cannot be hidden, only forbidden by a rule that nobody can check. | Unknown and not measurable. Present in all four builds. |
| **6. The data.** The kit's total-return series carried a 2018 demerger factor into 2017 dividends (report 93). | One verified case (Wesfarmers). It favoured the family that then lost. | Small, but it shows "physically truncated" was not fully true. |

Reading: the first four builds were close to blind in what the builder was told. They were not blind in how the exercise was shaped, and each further round is shaped by more results. **The fifth build is the first one where the most natural improvements are themselves the leak.** If it then beat the fund, I could not tell the owner whether the method had improved or the answer had seeped in. If it lost, we would have learned what section 1.3 already shows.

There is also a plain statistical limit. All of these builds are judged on one stretch of nine years. That is one market history: one sharp fall, one long rise led by the largest companies, one mining and small-company boom. Four builds are four draws from the builders, not four draws from the market.

### 2.3 A different cut-off?

- **Later (for example December 2020, as build 2):** the judged period shrinks to under six years, inside the same history. Build 2's list is already run on it.
- **Earlier (for example December 2013):** two fewer design windows out of four, and the judged period 2014–2026 contains the years every build so far has used either for design or for judging. The reviewer knows which families led in each window (builder 4's fold table).
- **No cut-off gives years that nobody in this programme has looked at.** The data start in 2004 and every year since has been in someone's design windows or judged period.

So changing the cut-off does not restore blindness. It rearranges the same years.

## 3. Recommendation

### 3.1 Stop the blind-build cycle on this data. Switch to forward-only learning.

The cycle did its job. It showed that EMG2 could not have been found blind, that choosing among designs is drawing lots, that a default reasoned from costs loses, and that the builders forecast honestly. It produced one design worth tracking (BLIND3) and one way of holding two (PAIR). Those are registered. What remains unknown is whether any of it works in years nobody has seen, and from 30 November those years start arriving.

### 3.2 What the forward record is for, in order of how soon it can answer

1. **Costs.** The least certain number in every replay is the spread model, and EMG2-18 depends on it most (A$623 a year modelled; with the spread doubled its lead on the vendor file disappears). Real fills settle this within a year.
2. **Does the score still sort shares.** The registered measurement line (best fifth of ranks 301–600 against the whole band) had a monthly t near 5 over nine years. If it persists at full strength, t reaches 2 after about 17 months. At half strength it takes over five years.
3. **Book against twins.** One 18-name book differs from its twins' median by 14 to 17 points in a single year by luck alone (measured on the 100 twins of EMG2-18 and BLIND3 in the replays). A true lead of 10 points a year shows at z = 2 only after about nine years; at the 80th percentile, typically after about two.
4. **Book against the fund.** Decades (report 78; adopt rule v3 section 1). Not a test the owner should wait for.

### 3.3 Three things to do before 30 November (paper only; for the record keeper and the owner)

1. **Write down now how the analyst-estimate snapshots will be read**, before there is any return data to look at. This is a blind design with no leak at all, because the future has not happened. Proposed definition (for a draft amendment, information-only line, no money):
   - Universe: the 300 companies of the snapshot job, at each month-end from 26 February 2027.
   - Signal: change in the consensus earnings-per-share estimate for the current financial year over the last 63 sessions, divided by the share price at the start; companies with fewer than two estimates or a changed financial-year label are left out.
   - Measure: rank correlation between the signal and the next month's total return, one number a month; and the best fifth minus the whole 300, equal weight.
   - Readings: December 2028 (22 months), December 2030. Nothing is traded on it and nothing is tuned.
   - Counted as one trial at registration.
2. **Confirm the five pending rows of `CORPORATE_ACTIONS.csv`** (BHP, LNK, PMV, TAH, SBM). Until a row is confirmed, an in-specie distribution in a live holding will look like a crash (report 92 section 5).
3. **Make sure the live slice logs the mid price at the time of each order.** Adopt rule v3 defines the cost ratio from it. Without it the first 100 fills teach nothing about the spread model.

### 3.4 Two tests that use existing rules on data they have not touched (to scope, not to run yet)

These are not blind builds. They take rules that are already frozen and registered, and run them once somewhere new.
- **Other markets.** The multi-market packs of report 78 cover 14 markets. EMG2-18 and BLIND3, unchanged, run once per market, would be a real out-of-sample test of the two constructions. Before it is worth doing, someone must check that the packs hold dead companies and reach rank 600 by traded value; if they hold survivors only, the test is void. Report 76 has already run a momentum design on these packs, so the reviewer is not blind there either, but the two frozen rule sets have never met that data. Two trials per market.
- **ASX before 2004**, if a file with dead companies can be found. I do not know that one exists at a price inside the owner's budget.

## 4. Forward data now being collected: what it will allow, and when

| Data | Collected since; how much | First honest test | What it can and cannot show |
|---|---|---|---|
| **Paper lines** (EMG2 A$100k and A$25k with 100 twins each and the band-spread line; EMG2-18; BLIND3; PAIR; COMBO; H6; EARLY; CXL; M3; E3; 68 multi-market books) | First decision 30 Nov 2026, fills 1 Dec. First scorecard with returns: early January 2027 | Stop conditions: December 2027 (13 months). Signal spread and twins at step P2: **December 2028**. Full ladder P3: December 2030 | The first numbers in this programme on years nobody has seen. The signal spread is the sharpest; book against fund is not readable for decades |
| **Live fills, EMG2-18, A$10,000** | Mid-December 2026; 18 orders on day one, about 110 a year | Rough look at about 40 fills: **March 2027**. The 100 fills that rule v3 asks for: **about November 2027** | Whether real cost per trade is within 1.5 times the model. The single most useful early number. Needs the mid price logged at each order |
| **Analyst estimates, point in time** (`estimates_pit`) | 19 Nov 2026; one snapshot a day of 300 companies | First usable signal: end of February 2027 (three months of history, first results season). First reading: **December 2028**, which can detect only a strong effect (monthly rank correlation of about 0.05 or more, assuming the usual month-to-month swing of 0.10; that swing is my assumption, not a measurement). A typical effect of 0.03 needs to about **late 2030** | The only genuinely new kind of information being collected. The vendor's history of estimates was unusable (report 79), so there is no back-test and never will be. Register the reading now (3.3) |
| **New listings tracker** | Symbol-list diffs from 16 Nov 2026; 77 listings tracked back to about October 2025; about 70 a year | 150 listings each with a year of history: **about December 2028** | Confirms or contradicts report 84 on new years. Not new information in kind: the research panel already holds every past listing. What is new is sector and size at listing as they stood on the day |
| **ASIC short positions** | Daily archive from 28 Oct 2026 | No wait needed: ASIC publishes every daily file back to 16 June 2010, as issued | Already tested on that history (report 62): heavy short interest did not predict lower returns in the top 300. The useful part of these files is the **share count on each day**, which gives point-in-time company size and dilution back to 2010. That is new data for a future kit (section 5) |
| **Intraday looks** | 16 Nov 2026; delayed last prices every two hours for held names and the 300 | None | Delayed last-trade prices with no bid and ask. They cannot test an intraday rule or the spread model. Useful only as an early warning on a holding. If a spread record is wanted, it has to come from the broker at order time |

Plainly: **nothing being collected can give an honest answer on returns before December 2027, and the first reading with any strength is December 2028.** Costs are the exception and come within months.

## 5. When a blind build would be worth doing again, and what its kit must fix

A blind build earns its cost only when the builder is given information no earlier builder had. Conditions, all required:

1. **A real dividend file**: amount, type (ordinary, special, capital return, in-specie), ex-date, franking. Yield computed from cash amounts and the raw close, never from the gap between the return series and the price.
2. **Corporate actions confirmed** for the design years and the judged years: demergers and in-specie distributions booked as a distribution of the right value, not as a 0% day or a price fall.
3. **The return series rebuilt at the cut-off**, so that no adjustment factor from a later event sits in earlier rows. Check: recompute every pre-cut-off dividend as cash ÷ raw close on the ex-date and compare with the series; any difference above a tenth is a future factor (the Wesfarmers test of report 93, run for every company).
4. **Official delisting reasons after April 2020** loaded, and the renamed companies chained (Platinum → L1 Group; Vita Group to be checked).
5. **Point-in-time share counts from the ASIC files (2010 on)**, giving company size and the change in shares on issue.
6. **The briefing is the build-4 briefing unchanged** except for the description of the new data. No new rule about sets, families or signals. If dividends cannot be fixed, the kit says "inferred dividends are wrong at the top of the yield ranking" and leaves the series in; it does not remove the family.
7. **Stated in advance:** the judged years are the same 2018–2026. The result tests whether the new data adds anything over builds 3 and 4. It is not a fifth test of the method, and it cannot promote a design to money.

Even this carries a leak I cannot remove: I know from report 62 that companies whose share count grew fast did worse in 2017–2023. Supplying share counts is itself a hint chosen by someone who has seen that. It would be stated in the briefing's residual risks.

Until items 1–5 exist, a fifth build would be a re-run of the fourth.

## 6. For the record keeper

1. **Trials: N = 2,788** (2,644 + 144: builder 4's whole grid on the judged period, 12 starts, both data sets; no twins). Seen data; no candidate. Ledger not written by me.
2. **No blind build 5.** No kit, no briefing, no label map was made. `deep92/blind4_kit` and `deep92/private/idmap_blind4.csv` stay as they are.
3. **Correction to report 92 section 1.4 / the working summary "sets help if they span families":** on builder 4's list a cross-family set would have made 4.5% / 5.0% (two families) and −0.1% / 2.7% (three), against 5.5% / 6.0% for the single-family set delivered. Suggested note beside the PAIR amendment: a set gives the average of its members; no more is claimed.
4. **Correction of wording, "momentum held up out of sample":** true of two constructions (EMG2-18, never blind; BLIND3, blind once). Plain momentum on the top 200 / 500, listed blind in builds 3 and 4 (84 designs), had a middle result of 1% to 4% a year and was behind the fund.
5. **Proposed, for the owner to decide:** an information-only forward line for analyst-estimate revisions, registered before February 2027 with the definition of section 3.3 (one trial at registration).
6. **To do before 30 November:** confirm or strike the five pending corporate-action rows; check that the live order log stores the mid price at order time.
7. **Data faults carried forward from report 93**, still open: Platinum → L1 Group not chained; Vita Group zero payout; demerger days booked as 0%; the return series back-adjusts old dividends by later demerger factors; no delisting reasons after April 2020.
8. **Dates for the diary:** first paper scorecard early January 2027; cost look about March 2027; 100 live fills about November 2027; stop readings December 2027; first signal-spread and twins reading at step P2, December 2028; estimates line first reading December 2028.
9. **To scope, not run:** whether the multi-market packs hold dead companies and reach rank 600 (section 3.4).

## 7. Files

`deep94/PROGRESS.md`; `code/grid94.py`, `read94.py`; `out/grid_panel.pkl`, `grid_vendor.pkl`, `grid_read_panel.log`, `grid_read_vendor.log`, `grid_judged_panel.csv`, `grid_judged_vendor.csv`, `build94.log`, `hashes_94.txt`. `deep93/full/panel.npz` was rebuilt for the run and deleted again (rebuild: `deep93/code/build93.py`, one minute).
