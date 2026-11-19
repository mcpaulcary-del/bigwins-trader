# 90. Review and learning after blind build 2 — what it teaches, a paper twin for the combined design, and a stricter kit for blind build 3

19 November 2026. Author: Fable, as reviewer (owner's cycle: blind build → review and learning → next blind build). Reviews report 89.
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. The live code, the ledger, the scheduled jobs and `/home/user/asx-trader` were not touched. The ledger was not written. No vendor credits were used.
Work folder: `scratchpad/deep90/` (`PROGRESS.md`, `code/`, `out/`). Draft paper-twin amendment: `deep90/AMENDMENT_shadow_EMG2_COMBO.DRAFT.md`. Briefing and kit for the next builder: `deep90/METHOD_LESSONS_FOR_BLIND3.md`, `deep90/blind3_kit/`.

How to read the figures: as in report 89. A$10,000 once; "a year after tax" = after IBKR brokerage (A$6.60 an order), modelled spread and 32% tax, everything sold at the end. Fund = ASX 200 with dividends, 7.1% a year after tax for January 2021 – November 2026. Unless stated, a figure is the mean of 12 start months (December 2020 to November 2021) run to 2 Nov 2026. Two data sets: research panel first, vendor file second. Twins = 100 books with the same structure that pick at random. Every figure in sections 1 and 2 is on data that has been seen before; none is a candidate.

## 0. Answer first

1. **"The choice rule showed no skill twice" is half right.** Both times the rule could tell bad kinds of design from good ones. Both times it could not choose between good neighbours. In blind build 2 the pick was fair (27th / 6th of the 81 designs the builder listed). The list itself was poor: the middle design of the 81 made 0.1% / −2.1% a year, 16 / 5 of them beat the fund, and none beat EMG2-18. Blind build 1 was the reverse: a good list (middle design 13.0% / 10.3%) and nearly its worst member chosen.
2. **So the weight is on which kinds of strategy get listed, not on the choosing.** The blind-2 builder's list was shaped by the kit's example menu and by its own cost reasoning ("trade little, in the largest companies"). That reasoning produced its default, which made −2.2% / −3.1%. The owner's concern about the menu is supported.
3. **Signal.** Nearness to the 52-week high alone against the three-measure score: not settled. The three-measure score won by 7 to 10 points a year where holdings are sold promptly, and lost where they are allowed to drift. Twelve-month momentum alone was the worst in both periods. No reason to change EMG2-18's score.
4. **Band.** Ranks 1–300 were poor before 2021 and after. Ranks 301–600 did better than 201–700 in 2021–2026 by 0.4 to 6.8 points, but 301–600 was chosen with that period in view, so this is not evidence. The lower edge matters; the upper edge is unproven.
5. **Payout rule.** The panel has no recorded reason for any delisting after April 2020. Every holding that stopped trading in the judged period was paid by a price rule of thumb. Results must carry both bounds until official reasons are loaded.
6. **Concentration.** True of both books and of every random twin: take out three holdings and the book is below the fund. It is the shape of these shares, not a flaw of one design. It means long stretches below the fund are normal.
7. **The fall since March 2026.** About two-thirds of it is the market in these shares: companies ranked 301–600 fell 23% on average while the largest 100 fell 2%. The rest is EMG2-18's picks doing worse than random over those eight months (5th percentile of its twins). Falls of this size came about once every three to four years in the 20-year replays. It is normal for this kind of book. It is not yet evidence against the signal, and it is the item to watch.
8. **First months live, in plain numbers** (76 past starts of the registered rules): a 1-in-6 chance of being under A$9,000 within three months; 1-in-6 of touching A$8,000 within a year; 1-in-12 of touching A$7,000; after a year the middle outcome is about A$10,100 against A$11,100 for the fund, with a range of A$8,200 to A$13,900 for the middle 80%. About an even chance of being behind the fund after a year. Daily lows are deeper than month-end values.
9. **Combined design as a paper twin: yes.** EMG2-18's score, band and buy filter with blind-2's selling rule (hold six months, then sell only when out of the top 40%) sent 60 orders a year in place of 115 and saved about A$700 a year of brokerage and modelled spread, with about the same return on seen data. It cannot be tested blind on 2018–2026. Draft with 100 random twins: `deep90/AMENDMENT_shadow_EMG2_COMBO.DRAFT.md`. No proposal for the live book before the December 2028 review.
10. **Blind build 3: cut-off 31 December 2017, with a kit that holds no strategy at all.** Data, costs, tax, order mechanics, twins and evaluation tools only. The builder must propose at least three kinds of strategy itself. Reasons for the cut-off are in section 3.1.
11. **EMG2-18: keep for the December go-live.** Nothing here changes the live rules.
12. **Trials: N 2,115 → 2,192.** This review ran 77 designs on January 2021 – November 2026 that had not been run there before. None is a candidate.

## 1. What blind build 2 teaches

### 1.1 The choice rule: skill at the coarse level, none at the fine level, and a poor list

All 81 designs of the builder's grid were run on the judged period (`deep90/out/a1_grid_panel.csv`, `a1_grid_vendor.csv`).

| | Blind build 1 (report 88) | Blind build 2 (this report) |
|---|---|---|
| Designs listed by the builder | 72 | 81 |
| Judged period | 2018 – Oct 2026 | Jan 2021 – Nov 2026 |
| Middle design of the list, return a year after tax | 13.0% / 10.3% | 0.1% / −2.1% |
| Designs of the list ahead of the fund | 63 / 45 of 72 | 16 / 5 of 81 |
| Rank of the chosen design in its list | 65th / 63rd of 72 | 27th / 6th of 81 |
| Chosen design's return | 6.0% / 3.5% | 4.7% / 6.5% |
| Rank link between the design-data score and the judged result, whole list | coarse stage +0.46 / +0.40; fine stage −0.13 / −0.09 | +0.84 / +0.80 |
| Same, inside the better part of the list | — | +0.42 / +0.38 (36 designs: two better bands, two better scores); +0.40 / −0.01 (27 designs on the 52-week-high score) |
| The ten shortlisted designs, mean return | — | 6.9% / 4.3% |

What this says:

- **Coarse choices can be read from past data.** In blind build 2 the high link over the whole list comes from two things that were bad before 2021 and bad after: twelve-month momentum used alone (grid mean −8.2% / −10.5% a year after 2020), and the 300 largest companies (−3.3% / −4.7%).
- **Fine choices cannot.** Inside the 36 reasonable designs the link is weak, and on the vendor file it is nil among designs that share a score. The builder's own fold test said the same before the freeze (mean rank 37 of 81).
- **A fair pick from a poor list is a poor design.** The shortlist averaged level with the fund on the panel and below it on the vendor file. Nothing in a choice rule can repair the list.
- **Why the list was poor.** One-third of it was the 300 largest companies, one-third was twelve-month momentum alone, and one-third let holdings drift until they were out of the top 80% of their list. Those were the builder's own choices, made before any run, from the kit's example menu and from the arithmetic of A$6.60 an order. Its reasoned default (largest 300, hold 13 months) made −2.2% / −3.1%.
- **"Fewer trades is better" has now failed twice as a prior.** Across the 81 designs the link between orders a year and return was nil (+0.06 / −0.05). In blind build 1 it was +0.5 the wrong way. Brokerage is real and certain; it does not follow that the slow book is the better book.

### 1.2 Signal: 52-week-high score alone, or the three-measure score

| Return a year after tax, 2021 – Nov 2026 (panel / vendor) | 52-week high alone | Three-measure score |
|---|---|---|
| Blind-2 structure, ranks 201–700 (primary and its family member) | 4.7% / 6.5% | 12.1% / 10.6% |
| Same structure, ranks 301–600 (new cells) | 8.3% / 6.9% | 18.1% / 17.4% |
| Mean of all 27 grid designs on that score | 5.2% / 3.9% | 2.0% / −0.7% |
| Of those, the 9 that sell only when out of the top 80% | 5.5% / 3.9% | −2.0% / −2.8% |
| Mean worst fall of the 27 | −27% | −46% |
| Design data 2006–2020: mean lead over the fund, and its standard error | 0.0 points; 2.4 | +0.8 points; 4.1 |

- The three-measure score paid 7 to 10 points more **when holdings were sold promptly** (out of the top 40% or 60%). When holdings were left until they fell out of the top 80%, it was the worse of the two.
- The 52-week-high score is the steadier one: smaller falls, less difference between windows. The blind-2 score ("mean minus one standard error") rewards steadiness, which is why it leaned that way. On the plain mean the design data slightly preferred the three-measure score.
- Twelve-month momentum alone was the worst score in 2006–2020 and after.
- **Reading:** the choice between these two scores is inside the noise. EMG2-18 uses the three-measure score with a prompt sell, which is the corner where it did best. That corner was chosen with 2018–2026 in view. No change is supported either way.

### 1.3 Band: 201–700 or 301–600

- Same structure, same score, band changed: 301–600 was ahead by 3.6 / 0.4 points (52-week-high score) and 6.0 / 6.8 points (three-measure score) in 2021 – Nov 2026.
- This is not evidence for 301–600. That band was picked in report 85 with these years in view. In blind build 1's list, which was fixed on data to 2017, ranks 101–900 did about as well as 301–600 at 18 names over 2018–2026 (report 88 section 1.6).
- What repeats in both periods and both data sets: the 300 largest companies are the wrong place for these scores at A$10,000 (design data −3.8 points against the fund; judged period −3.3% / −4.7% a year).
- The buy filter cost return again. The combined design with EMG2-18's filter made 13.0% / 10.7%; the same band, score and selling rule without the filter made 18.1% / 17.4%. Report 88 found the same sign twice. The filter is a safety choice for real orders in thin shares and stays until live fills give a measured spread.

### 1.4 The payout rule for holdings that stop trading

- New finding (`deep90/out/a4_payout.log`): the delisting file has a recorded reason for about half the delistings up to April 2020 and **for none after it** (the official list could not be reached past that date; later entries were inferred from prices). In 2021–2026 every stopped holding was therefore paid by the fallback: last close if it was within 30% of its 250-day high, otherwise zero.
- Effect in report 89: four holdings of the blind-2 primary written to zero (A$2,900), at least one wrongly (New Energy Solar, a wind-up that returned capital). Paying all four at the last close moved the primary from 4.7% to 7.0%. EMG2-18 had no zero in either replay (21 and 33 payouts, all near the high, net +A$1,800 and +A$2,600), because it sells within a month or two of a fall.
- **A rule that makes a book hold longer makes it more exposed to this rule.** That applies to the H6 and COMBO paper twins.
- What to do:
  1. Data task for the record keeper: load official ASX delisting reasons for May 2020 onward, and check the four named cases (AVZ Minerals, Firefinch, New Energy Solar, Trigg Minerals; the last has no reason on file and may be a code change).
  2. Until then every judged result is reported twice: the frozen rule, and every "not recorded" case paid at its last close. The blind-3 briefing says the judge will do this.
  3. The forward books are not affected: a real payout arrives as cash.

### 1.5 Concentration

| Return a year after tax, 2021 – Nov 2026 (panel / vendor) | As run | Best 3 removed | Best 5 removed |
|---|---|---|---|
| EMG2-18 | 13.7% / 13.2% | 5.8% / 5.9% | 2.4% / 2.6% |
| Blind-2 primary | 4.7% / 6.5% | −1.3% / 0.9% | −4.3% / −1.9% |
| Combined design (section 2) | 13.0% / 10.7% | 7.2% / 6.1% | 3.9% / 3.3% |
| Random twins of EMG2-18, median | −4.0% / −6.0% | | −12.4% / −14.1% |
| Fund | 7.1% | | |

- Both books fall below the fund once three holdings are removed. So does every design tested in these shares.
- This is the nature of the shares, not a defect of one rule: a random book lives on a few winners too, and loses about 13% a year without its best five. Against twins, like for like, both books pass.
- What it means for the owner: the lead over the fund is five companies in six years, about one every 14 months. In a year without one, expect the book to trail the fund by something like its costs. The first year live may well be such a year.
- Parcels of A$550 cap what one winner can add. That is a consequence of the account's size and is not fixable by a rule.

### 1.6 The fall since March 2026: is it normal, and what to expect in the first months

**What happened** (December 2020 books, research panel; `deep90/out/a2_dd.json`, `a3_daily.log`):

| 2 Mar 2026 → 2 Nov 2026 | Change |
|---|---|
| Fund | −1% |
| 100 most-traded companies, equal weight, no costs | −2% |
| Ranks 101–300 | −12% |
| Ranks 201–700 | −19% |
| Ranks 301–600 | −23% |
| Random twins of EMG2-18: median; worst tenth | −26%; −36% or worse |
| EMG2-18 | −38% (A$36,300 → A$22,600); 5th percentile of its twins |
| Random twins of the blind-2 primary: median | −22% |
| Blind-2 primary | −27%; 34th percentile of its twins |
| Combined design | −32%; 12th percentile of its twins |

On daily values EMG2-18's low was A$21,500 on 30 Jul 2026, 41% below the March peak.

- **About 23 to 26 of EMG2-18's 38 points are the market in these shares.** Small companies fell while the large ones did not. A random book in the same shares lost a quarter.
- **The other 12 points are the picks.** Over these eight months the score chose worse than random. One eight-month stretch at the 5th percentile is within what luck does, and a momentum book is expected to fall harder than a random one when the leaders turn. It is still the number to watch: the owner's staged loss rule already tests the live book against the 10th percentile of its twins.
- The blind-2 primary's fall was ordinary for its shares.

**How often this has happened** (one book of each kind from December 2006 to November 2026, month-end values):

| | Falls of 25% or more from a peak in 20 years | Share of all 8-month stretches that lost 27% or more | Share of months spent 25% or more below the last peak |
|---|---|---|---|
| Combined design | 6 (2008 −51%, 2011 −44%, 2016–17 −31%, 2020 −46%, 2022–23 −32%, 2026 −25% so far) | 6% | 25% |
| EMG2-18 rules with a 6-month hold (H6) | 6 | 6% | 29% |
| Blind-2 primary | 4 | 4% | 13% |
| Fund | 1 (2008–09, −49%; March 2020 was −23% at month-ends) | 2% | — |

- A fall of 25% to 45% came about once every three to four years. Two of the six (2016–17 and 2022) came, like this one, while the fund fell 14% or less.
- New highs took 12 to 39 months to return.
- Over the six years of the judged period, 83% of EMG2-18's random twins had a fall of 35% or more.
- The registered rules' own 20-year book is not shown in the table: before 2018 its A$250,000 traded-value test left it half empty (report 88 section 1.7), and it sat below its 2008 peak until 2021. That history is a warning about dollar thresholds, not a forecast.
- **Daily lows are deeper than month-end values.** In the 2018–2026 replay of the registered rules the worst month-end fall was 48% and the worst daily fall 59%; the account's lowest daily value was A$4,262 on 23 Mar 2020, against A$5,231 at the month-end. The loss-rule figures of report 88 were month-end figures. On daily values the A$6,000 and A$5,000 steps will be reached more often than those figures say.

**What to expect in the first months live** (registered rules, 76 quarterly starts from December 2006 to September 2025, month-end values, A$10,000; `deep90/out/a2_firstyear.csv`):

| | All 76 starts | 32 starts since Dec 2017 |
|---|---|---|
| Cost of the first day (18 buys: brokerage about A$119, spread about A$50) | about −1.7% | |
| Under A$9,000 at some month-end in the first 3 months | 17% | 16% |
| Under A$8,000 in the first 12 months | 17% | 19% |
| Under A$7,000 in the first 12 months | 8% | 12% |
| Under A$6,000 in the first 12 months | 3% | 6% |
| Value after 12 months: low tenth / middle / high tenth | A$8,200 / A$10,100 / A$13,900 | A$8,900 / A$12,500 / A$15,300 |
| Fund after 12 months, middle | A$11,100 | A$11,200 |
| Behind the fund after 12 months | 54% | 34% |
| Behind the fund by more than 10 points / ahead by more than 10 points | 38% / 30% | 28% / 44% |

- The honest one-line expectation for the first year: **anywhere from A$8,000 to A$14,000, about an even chance of being behind the fund, and a real chance (1 in 6) of seeing A$8,000 on the way.** The years since 2017 look better than that; they are the years the band was chosen on.
- **Starting inside a fall has not been worse.** For starts made when the long book was already 20% or more below its peak, the 12-month outcome was no worse than for all starts (middle A$10,100 for the registered rules, A$11,500 for the combined design, A$11,900 for the blind-2 primary). The samples are small and overlap. It is no reason to delay and no reason to expect a rebound.
- One year of 18 names cannot show whether the signal works. The live book answers whether fills and costs match the model (report 88 section 4.5).

## 2. The combined design as a paper twin

**Recommendation: yes, register it as a paper twin from 30 Nov 2026, beside the H6 twin, with 100 random twins.** Exact rules: `deep90/AMENDMENT_shadow_EMG2_COMBO.DRAFT.md`.

What it is: EMG2-18 unchanged for what is bought (ranks 301–600, three-measure score, top fifth, the buy filter, 18 names). One change to selling: a holding is sold only after six month-ends, and only if it is then outside the top 40% of the band (or has left the band). Takeover-pinned holdings are still sold at once.

| A$10,000, after all costs and tax | EMG2-18 | H6 | Combined |
|---|---|---|---|
| 2021 – Nov 2026, panel / vendor | 13.7% / 13.2% | 10.2% / 8.4% | 13.0% / 10.7% |
| Range over 12 start months (panel) | 12.4 to 14.8 | 4.0 to 14.2 | 5.3 to 17.1 |
| Best 3 removed (panel / vendor) | 5.8% / 5.9% | 3.4% / 1.6% | 7.2% / 6.1% |
| Worst fall, month-end (panel) | −38% | −39% | −34% |
| Orders a year | 115 | 64 | 60 |
| Brokerage a year; modelled spread a year | A$757; A$620 | A$420; A$299 | A$399; A$276 |
| Percentile among its own twins | 100 | — | 100 |
| Three-year windows 2006–2026 ahead of the fund (of 7) | 2 | 5 | 6 |

- **The certain part:** about 55 fewer orders a year. That is A$360 of brokerage, plus about A$340 of spread if the model is right: A$700 a year, 7% of the capital.
- **The uncertain part:** the return. On the panel it was level with EMG2-18 (ahead in 7 of 12 start months); on the vendor file 2.5 points a year behind. Its result depends more on the start month, because fewer trades means each one counts for more.
- **Why not a live change:** the design was assembled after both its parts had been seen on 2018–2026. No test on that period can be blind. Its 2006–2017 advantage is partly an artefact of the registered traded-value test (section 1.6). It holds longer, so it is more exposed to the payout rule (section 1.4).
- **Why two twins and not one:** H6 against the live rules shows what the six-month hold does. Combined against H6 shows what the wider keep zone does. Both cost nothing. Neither difference is acted on by itself.
- **Reading rule (in the draft):** brokerage and spread saved are reported as facts; value gaps are labelled as mostly luck (the 12-month gap between two such books has a standard deviation of about 15 points). No proposal before the December 2028 review, and then only if four conditions hold, one of which is that a blind build with no menu arrives by itself at a slow-selling rule.

## 3. Blind build 3

### 3.1 The cut-off: 31 December 2017 (last session Fri 29 Dec 2017)

| | End 2017 | End 2021 |
|---|---|---|
| Unseen period | 8.9 years (Jan 2018 – Nov 2026) | 4.9 years |
| Uncertainty on the lead over the fund (tracking error about 22 points ÷ √years) | about 7 points a year | about 10 points a year |
| What the unseen period contains | the March 2020 fall, the 2022 fall, the 2026 fall, two recoveries | starts at a small-company peak (January 2022) and ends in a fall |
| Design history | 2006–2017: four three-year windows, with 2008 and 2011 | 2006–2021: five windows and a year |
| Compared with an earlier build | Same cut-off and same data as blind build 1: the two frozen designs can be laid side by side over identical years. The only things changed are the kit and the builder | No earlier build at this cut-off |

Chosen: **end 2017.**

- The owner's question for this round is whether the menu steered the builder. The cleanest test of that is the same cut-off and the same data with the menu removed. The blind-3 panel is bit-for-bit the blind-1 design panel under new labels (checked).
- The longer unseen period nearly halves the variance of the verdict.
- The cost is one window fewer of design history. Blind build 1 worked from the same history.
- **EMG2's knowledge of 2018–2026 contaminates the comparison with EMG2 at either cut-off.** Its band was chosen on those years. No cut-off repairs that; only the forward record from 30 Nov 2026 does. So, as in blind build 2, the bar is twins first, the fund second, and EMG2-18 only as an undisclosed comparator that has the home ground. The judge also reports the two halves of the period, so the 2021–2026 half can be read beside blind build 2.
- What the cut-off cannot fix: the reviewer and the judge have seen these years many times. Only the builder is blind. That is the point of the labels and the physical truncation.

Report 88 said the method should be frozen after blind build 2 and run unchanged at further cut-offs. This round changes the kit on the owner's instruction and keeps the scoring protocol. The changes to the protocol are the ones the no-menu design forces (section 3.3). After blind build 3 the same kit should be run unchanged at end 2014 and end 2021 before anything else is altered.

### 3.2 The kit: `deep90/blind3_kit/`

| Item | Blind-2 kit | Blind-3 kit |
|---|---|---|
| Engine | `eng88.py`: accounting plus an example selection menu (traded-value rank bands, three momentum measures, number of names, exit buffer, minimum hold, refresh, market switch, buy filter) | `acct3.py`: accounting only. The builder writes a strategy object with three methods (decision days, sells, buys). No universe rule, no signal, no ranking, no holding count, no holding period, no parameter |
| Briefing's fixed settings | About 18 names (12–20), month-end clock, an eligibility floor (A$100,000 a day, A$0.10) | None of these. Number of names, clock, eligibility, sizing and cash are the builder's. Only the owner's account rules remain (A$10,000, A$500 minimum buy, IBKR fees, tax) |
| Spread model | Steps at ranks 100, 300 and 600: the same numbers as EMG2's band edges | A smooth curve through 0.10% at place 50, 0.25% at 200, 0.50% at 450, 0.75% at 800, 1.50% at 1,500. No step for a design to sit beside. Thin shares cost more, and the briefing says the model there is extrapolation |
| Liquidity | A floor in the eligibility rule | An order mechanic: a buy may not exceed 5% of the 20-session median traded value (the live book's own limit, rule L10) |
| Tax | Halved after 13 month-ends | Halved at 367 days from fill to fill, first-in-first-out parcels; top-ups and part sales allowed |
| Look-ahead guard | By convention in the engine | The strategy is handed a view cut at the decision day and an account valued at the decision close; `tools3.asof_audit` reruns sampled decisions with every later row blanked (it passes an honest test strategy and fails one that reads the next day) |
| Worst fall | Month-end values | Daily values |
| Twins | Built into the engine for the menu's structure | `tools3.RandomScores`; the builder defines the twin of its own family under a written rule (same eligible set, same number of purchases, same selling clock; orders and holdings within one-fifth of the design's) |
| Families | One grid from the menu | At least three kinds of strategy proposed by the builder, each with a written reason why it should beat the fund after A$6.60 an order |
| Data | To 31 Dec 2020, labels E00001… | To 29 Dec 2017, 4,658 entities (1,887 already dead), labels K00001… in a new random order; map in `deep90/private/idmap_blind3.csv` |

Checks made (`deep90/out/`):

- **The new engine's accounting is the old one.** With its spread and discount functions set back to the earlier conventions, `acct3.py` reproduces `eng88.py` to 16 decimal places on four books (registered EMG2-18 2018–2026: 11.3374%; the blind-2 primary on two periods; the combined design), written as strategy objects in private code (`validate_acct3.log`). On the kit's own conventions the registered rules move from 11.34% to 11.54%.
- **Self-check, all pass** (`selfcheck_blind3.log`): no row, first-price date, delisting record or fund value after 29 Dec 2017; labels only, no names or codes; label map outside the kit; no label or column position shared with the blind-2 kit; data identical to the blind-1 panel; the kit code and the briefing contain none of a list of family and parameter words (momentum, 52-week, band, top fifth, minimum hold, exit buffer, the numbers 101, 201, 300, 301, 600, 700, 900, "18 names", EMG, M3, H6 and others), no year after 2017 except the authoring year, and no ASX code; the engine ranks nothing except traded value for the cost model.
- Hashes of the kit, the briefing, the label map and the build and check code: `deep90/out/blind3_hashes.txt`.

### 3.3 The briefing: `deep90/METHOD_LESSONS_FOR_BLIND3.md`

Kept from blind build 2: written plan and hashes before any run; a default design that wins ties; at most 150 designs; six start months per window; score = mean window lead minus one standard error; neighbourhood score; twins, concentration, cost and breadth gates; fold test of the choice rule; a frozen family; a forecast; the bar (a)–(f) with twins first.

Changed, each on logic or on data to 2017 only:

| # | Change | Why |
|---|---|---|
| 1 | The builder proposes at least three kinds of strategy, with reasons, before any run | Section 1.1: the list decides more than the choice |
| 2 | Families are ranked first, by the median score of their members; a design is then chosen inside the family | A family is better measured than one design. Both builds showed coarse choices are readable and fine ones are not |
| 3 | For each family, the random twins' result against the fund is reported as the family's baseline | Both builds beat their twins and lost to the fund. What a structure earns with no skill has to be seen before choosing it |
| 4 | No tie-break on trades and none on number of holdings | Section 1.1 |
| 5 | Four windows (2006–2017); gates read "3 of 4" | Forced by the cut-off |
| 6 | Worst fall and lowest account value on daily values | Section 1.6 |
| 7 | The judge reports the payout upper bound and the two halves of the period | Sections 1.4 and 3.1 |
| 8 | No mention that earlier builds existed, what they chose or how they fared | Blind-2's briefing told the builder a lessons file existed |

The briefing's own self-check table classes every statement as method, owner's rule, pre-2018 fact or kit property, and lists six residual risks. The main ones: the data are prices and traded value only, which limits what families are possible; costs pull every builder toward slow trading in liquid shares; and the protocol was written by someone who has seen the later years.

### 3.4 How to run it

1. Record the hashes in `deep90/out/blind3_hashes.txt` before the builder starts.
2. Give the builder `METHOD_LESSONS_FOR_BLIND3.md` and `blind3_kit/` and nothing else. Best: copy both to a clean folder and start the builder there, because the blind-2 kit on the same disk holds three more years of the same companies under other labels.
3. The builder must not be given this report, report 87, 88 or 89, `deep90/private/`, `deep90/code/` or `deep90/out/`.
4. The judge builds the full panel in the kit's column order from `deep90/private/idmap_blind3.csv`, checks the hashes, runs the frozen `factory` unchanged, and runs EMG2-18 through `deep90/code/validate_acct3.py`'s strategy object as the undisclosed comparator.

## 4. For the record keeper (the ledger was not written)

1. **Trial count.** N 2,026 → 2,107 (the blind-2 builder's 81-design grid) → 2,115 (report 89: 8 judged books) → **2,192** (this report: 77). The 77 are: 74 designs of the blind-2 grid run on January 2021 – November 2026 for the first time (81 less the 7 run in report 89); 2 new cells (ranks 301–600 with the blind-2 structure, on each of the two scores); 1 combined design. All diagnostic, all on seen data, none a candidate. Twins, start months, the 20-year and quarterly-start replays of designs already counted, and the engine validation runs are not trials.
2. **Erratum to report 85** (still open from reports 87 and 88): its 2010–2017 EMG2 figures (11.0% a year against 7.4%; worst falls 38% and 57%) came from a file with almost no dead companies and with A$0.0001 glitch closes. They appear in `FD_v3.0_BigWins.md` lines 91, 92 and 579 and in the evidence text of `AMENDMENT_shadow_EMG2.md`. Replacement (research panel, A$100,000, no brokerage): 2010–2017 17.6% a year against 7.4%, worst fall 40%; 2018–Oct 2026 13.1% against 8.5%, worst fall 45%.
3. **H6 paper twin: register** `EMG2_18_SIM_H6` from `deep87/AMENDMENT_shadow_EMG2_18_H6.DRAFT.md`, with its section 3 replaced by the reading of report 88 section 4.3 (monthly brokerage saved as a fact; value gap labelled as mostly luck; no proposal before the December 2028 review; a proposal needs H6 not behind over 24 months and a blind build that chose a minimum hold unprompted). Before the 30 Nov 2026 decision. No trial.
4. **Staged loss rule: write the amendment.** The owner has signed it; the text is in `OWNER_DECISIONS_2026-11-19.md`, section "Loss rule REPLACED". It supersedes rule L11's "halt buys, owner decides" at A$6,000. Two points to settle in the amendment text: (a) **the value the steps are tested on.** The base rates in report 88 are month-end values; daily values go lower (A$4,262 against A$5,231 in March 2020). State whether A$7,000 / A$6,000 / A$5,000 are tested on the daily close or the month-end, and tell the owner that on daily closes they are reached more often. (b) L11's one-day 12% fall and `/kill` are unchanged.
5. **Combined-design paper twin: register if the owner agrees** `EMG2_18_SIM_COMBO` with 100 twins (seeds 8770000 + i) from `deep90/AMENDMENT_shadow_EMG2_COMBO.DRAFT.md`, before the 30 Nov 2026 decision. Paper only. No trial beyond item 1.
6. **Data tasks.** (a) Official ASX delisting reasons for May 2020 onward: the panel has none. (b) Check AVZ Minerals, Firefinch, New Energy Solar and Trigg Minerals (the last is marked "gone by 2024" in the company table yet has prices to 6 Feb 2026). (c) Note on every later judged result: payout bounds reported both ways.
7. **Blind build 3.** Record the hashes of `deep90/METHOD_LESSONS_FOR_BLIND3.md` and the kit (`deep90/out/blind3_hashes.txt`) before the builder starts. Cut-off 29 Dec 2017. Bar fixed in section 8 of the briefing.
8. **Uploads.** Reports 87, 88, 89 and 90 with their case tables (`87_case_table_blind_build.csv`, `89_case_table_blind2.csv`) to the research folder. Do **not** upload `deep90/private/`, and do not place `METHOD_LESSONS_FOR_BLIND3.md` or the kit where a future builder could also see the reports.
9. **No live amendment is proposed.** EMG2-18 as registered for the mid-December go-live.

## 5. Limits

- Everything in sections 1 and 2 is hindsight on a period seen several times. The 81-design table shows what the list contained; it does not show that a better rule would have found the best design.
- The first-year base rates use the registered rules across 2006–2025. Before 2018 their traded-value test left the book half empty, which lowers both the falls and the gains in those years. Month-end values; daily lows are deeper.
- "Two-thirds market, one-third picks" for the 2026 fall rests on one book, one start month and 100 twins.
- The spread is a model; no real fill exists. The combined design's saving of A$340 a year in spread is the model's figure. Its A$360 of brokerage is arithmetic.
- The blind-3 kit removes the menu, not the reviewer. The protocol, the data on offer (prices and traded value only) and the cost facts still shape what a builder will propose.
- The new engine was validated against the old one on four books of one strategy family. Its part-sale and top-up paths have been exercised only by a random test strategy.
- `deep90/full/panel.npz` (the full panel in blind-2 kit order, 60 MB) was deleted after use; rebuild with `deep90/code/build90_full.py`.

## 6. Files

| What | Path |
|---|---|
| This report | `onedrive/research2/90_review_after_blind2_fable.md` |
| Draft paper-twin amendment | `scratchpad/deep90/AMENDMENT_shadow_EMG2_COMBO.DRAFT.md` |
| Briefing for blind builder 3 | `scratchpad/deep90/METHOD_LESSONS_FOR_BLIND3.md` |
| Kit for blind builder 3 | `scratchpad/deep90/blind3_kit/` (`README.md`, `acct3.py`, `tools3.py`, `data/`) |
| Label map (never to the builder) | `scratchpad/deep90/private/idmap_blind3.csv` |
| Hashes; self-check; engine validation; tool smoke test | `deep90/out/blind3_hashes.txt`, `selfcheck_blind3.log`, `validate_acct3.log`, `smoke_blind3.log` |
| Kit build, checks | `deep90/code/build_blind3.py`, `selfcheck_blind3.py`, `validate_acct3.py`, `smoke_blind3.py` |
| 81 designs and extra cells on the judged period | `deep90/code/a1_grid.py`; `out/a1_grid_panel.csv`, `a1_grid_vendor.csv` |
| Falls, twins, first-year base rates, combined design | `deep90/code/a2_dd.py`, `a3_daily.py`; `out/a2_dd.json`, `a2_firstyear.csv`, `a2_long_*.csv`, `a3_daily.log` |
| Delisting reasons by year | `deep90/out/a4_payout.log` |
| Progress log | `deep90/PROGRESS.md` |
