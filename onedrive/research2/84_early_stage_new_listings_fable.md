# 84. Investing early in new ASX companies: does it work, which signs matter, and is it the best approach?

19 November 2026. Author: research agent (Fable). Owner request: "I want to invest early... surely the market has indicators if [new companies] are going to be big or not? ... make sure that's the best approach", then: "I need this ready by the end of the month."
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. EODHD data are used under a private, non-commercial licence. No automated access to asx.com.au.
Work folder: `scratchpad/deep84/` (`PREREG_84.md`, `PREREG_84b.md`, hashes in `out/prereg84_hash.txt`, `code/`, `out/`, `PROGRESS.md`). The live paper code, ledger and scheduled jobs were read, never written.
Companion: `scratchpad/deep84/AMENDMENT_shadow_EARLY.DRAFT.md` (the paper line, ready to register for the 30 Nov 2026 decision) and reference code `deep84/code/early_ref.py`, `early_live.py`, `early_hist.py`.

How to read the figures: "lead" = the book's compound return minus the ASX 200 index fund's, points a year. Unless stated: A$100,000, A$0 brokerage, modelled half-spread, 32% tax with the 50% discount after 12 months, everything sold at the end. t = the mean divided by its standard error; about 2 is "probably not luck", 3 is the adopt bar.

## 0. Answer first

**1. Buying new ASX companies early, as a group, loses to the index fund, and it is not close.** Of 2,221 ordinary companies that listed in 2001–2022 (the dead ones included), the typical one was **down 43–54% three years after its first day's close**. Only one in four or five beat the ASX 200. About half had halved. One in five to one in eight had lost 90% or more. A capped book that simply bought new listings six months in trailed the index fund by 2 to 10 points a year after costs.

**2. The big winners are real, and rare.** About 1 new listing in 8–10 doubled over three years; 1 in 30–50 went up five-fold; **1 in 100 went up ten-fold**. Those few carry everything: for 2013–2022 listings the best 5% made +346 (in units of "one stake"), the other 95% lost −321.

**3. Does the market give signs? It gives better signs of who will lose than of who will be big.**
- No sign I pre-registered predicted *average* returns in both test periods. Not size, not sector, not the first-day move, not early price strength, not volume.
- Signs of **trouble** were clear in 2013–2022 (not confirmed in 2001–2012): very jumpy price in the first six months (61% later halved, against 33% for the calmest third); a share price under 20 cents; issuing more than 10% new shares in the first year (72% halved against 25%); making a loss (57% halved against 30% for profit-makers).
- One sign of a **possible big winner** held in both periods: being above its first-day close and ahead of the index after six months. Later five-fold winners were 2–3 times as common in that group. But that still means 6–8 in 100, against 2 in 100.
- Profit cuts the disasters and also cuts the jackpots: among 128 profit-making 2016–2022 listings **none** went up five-fold in the next two years.

**4. The best rule I found is not proven.** "Buy a non-resources new listing at six months if it trades A$100,000+ a day, is 20 cents or more, is above its first-day close and ahead of the index; sell only if it falls 35% from its best month-end, or after three years." After costs and tax it led the index fund by **+1.4 to +2.9 points a year on 2001–2012 listings and +1.7 to +3.3 on 2013–2022** (the range is two ways of timing the same rule). It beat 84–96% of random books. But t is 0.6 to 1.4 against a bar of 3.0; with the single best company removed (Zinifex; a2 Milk) the lead is +0.3 to +0.7; with the best three removed it is negative; at A$25,000 it was +0.6 and −2.2. **It did not pass. I did not find a rule that beats the index by the adopt bar.**

**5. Is investing early the best approach? No.** For the stated aim (own the companies that become big) the index fund still does it at lower cost: it buys every winner on the way up, and the small-company index, the "all new listings" basket and "wait until it reaches the top 300" all did worse than the ASX 200 fund. Among the things tested in this programme, the early rule has the highest *possible* upside and by far the widest uncertainty; the Big Wins loser-screen has the best evidence (+0.2 a year, most likely) and almost no upside. Neither is shown to beat the fund.

**6. What is ready for 30 November.** A complete, frozen paper line (EARLY), with entry, exit, sizing, costs, controls, a daily indicator scoreboard and tested reference code. It can run on paper from the 30 Nov / 1 Dec decision. It is labelled **unproven**, and it can never be proven by a forward record of practical length (a +2 point edge at this bumpiness needs over a century to reach t = 3). What the forward record will show quickly is what the rule buys, what it costs, and whether the trouble signs keep working: about 100 new listings a year, a first proper reading at the end of 2028.

**7. If real money goes in anyway** (the owner's decision; the record does not support it): treat it as a lottery sleeve with a hard cap. Not more than 10% of the account in total, not more than 4% in one company, nothing trading under A$100,000 a day or under 20 cents, sell on the 35% rule without exception, and expect two of every three purchases to be sold at a loss.

| Approach, A$100,000, after costs and tax, lead against the ASX 200 fund | 2001–2012 listings | 2013–2022 listings | Verdict |
|---|---|---|---|
| Hold the ASX 200 fund | 0 | 0 | the benchmark |
| Small-company index (Small Ords / VSO) | about −1.5 to −2 | −0.3 (VSO from 2011) | behind |
| All new listings at six months, 2 years each (25 places) | −2.3 | −10.4 | fail |
| Same, non-resources only | −7.7 | −15.7 | fail |
| Wait until it reaches the 300 most traded, 2 years | −2.5 | −3.7 | fail |
| Profit-makers at twelve months (2016+ only) | | −3.6 | fail |
| Quality screen at six months, hold 2 years (R1) | 0.0 | −0.4 | fail |
| Same screen, sell on a 35% fall, up to 3 years (R4) | −0.2 | +3.4 (t 1.1) | fail |
| **EARLY: R4 with a A$100,000-a-day floor (the paper line)** | **+2.9 (t 1.4)** | **+1.7 (t 0.6)** | **not passed; unproven** |
| Big Wins H82 / D2 / loser screen (reports 81–82) | | −0.05 / +0.5 / +0.2 most likely | not passed |

## 1. What was built

**Data** (`code/build84a–d.py`, `link84.py`). The research price panel of every ASX company from 1997 to May 2024 (`data_foundation`, delisted companies included), extended to November 2026 with EODHD total returns, EODHD dividends added where the code matches, and 271 broken company histories re-joined across code changes. A "listing" is a company whose first price row falls in 2000–2025.

| First price rows 2001–2022 | Count | Treatment |
|---|---|---|
| **Ordinary new listings** | **2,221** (1,291 in 2001–2012; 930 in 2013–2022) | the study |
| Relistings: name change at the start, back-door listing into a shell, return after a long halt, demerger child, vendor history shows it traded before | 1,014 | reported separately (section 2.5) |
| ETFs, listed funds, investment companies, trusts, notes | 314 | excluded |
| Stubs (under 20 price rows) and unnamed | 295 | excluded |

59% of 2001–2012 listings and 35% of 2013–2022 listings were resources companies by name (mostly explorers); the name flag agrees with the vendor's industry for 93% of the 2016+ names where both exist.

**What happens to money when a company leaves the list.** Takeover or scheme (official reason): paid at the last price. Failure (official reason): −100%. No official reason (the delisting file stops in April 2020): paid at the last price if that was within 30% of its one-year high, otherwise −100%. Every headline was re-run with "all paid out" and "all non-takeovers written off"; the three-year mean for 2013–2022 moves from +7% to −3% (base +2%), the medians and rates do not move.

**Rules written before the outcomes were looked at.** `PREREG_84.md` (10 indicators, 8 rules; development = 2001–2012 listings, held-out = 2013–2022). `PREREG_84b.md` (6 more rules, 3 more indicators, written after the first stage and therefore **exploratory**, plus the rule for choosing the paper line). Trials added: **28**. With report 85's count of about 1,785 the programme stands at about 1,813.

**Limits to hold in mind.**
- The issue price is not in the data. "First-day move" here is open to close, which averaged zero. The pop from issue price to first trade (about 20% on average in the published studies, more for mining) goes to people with an allocation, not to an on-market buyer.
- Market value at listing exists only for a minority (share counts come from ASIC short-sale files from 2010). Size is therefore measured by traded value.
- Company accounts come from EODHD's current file, for 2016+ listings only, and are not point-in-time. I used the latest annual report ending at least four months before the decision.
- Returns before 2018 for companies that later died carry no dividends (the vendor has none). Young companies pay little; the effect is small and runs against them.
- 2000 listings were dropped: the accumulation index starts in November 2000.

## 2. Base rates: what happens to a new listing

### 2.1 From the first day's close (ordinary new listings; `out/an1.txt`)

| | Listed 2001–2012 (1,291) | Listed 2013–2022 (930) |
|---|---|---|
| **After 1 year:** typical (median) return | −18% | −20% |
| average return / ASX 200 | +6% / +7% | +6% / +8% |
| **After 3 years:** typical return | **−43%** | **−54%** |
| average return / ASX 200 | +16% / +25% | +2% / +27% |
| beat the ASX 200 | 26% | 20% |
| lost money | 69% | 73% |
| halved or worse | 47% | 53% |
| lost 90% or more | 12% | 21% |
| doubled or better | 13.5% | 10.1% |
| five-fold or better | 3.7% | 1.8% |
| ten-fold or better | 0.7% | 1.0% |
| **After 5 years:** typical return | −60% | −65% (806 with five years) |
| average return / ASX 200 | +20% / +34% | +17% / +52% |
| five-fold / ten-fold | 4.6% / 1.3% | 3.6% / 1.2% |
| Touched double at some point within 3 years | 37% | 31% |
| Touched ten-fold within 5 years | 4.6% | 3.7% |
| Was down by half at some point within 3 years | 71% | 70% |

Two things stand out. The average is far above the typical outcome because of a handful of very large winners, and even the average is behind the index. And more than a third of listings *touch* a double at some point, while only one in eight to ten *keeps* it to year three: a paper gain in a young company usually does not last.

### 2.2 Resources against the rest
Three-year typical return: resources −47% and −67% (the two periods), others −35% and −45%. Averages are similar, and resources were slightly *ahead* on average in 2001–2012 (the mining boom). Ten-fold winners occur in both groups at about the same rate. Excluding explorers lowers the disaster rate, not the average.

### 2.3 Year of listing matters more than anything about the company
Listings of 2001–2004 did well (typical three-year return +2% to +33%); those of 2006–2012 and of 2020–2022 did badly (typical −41% to −75%; 45–71% halved). Every one of the 22 listing years had a negative *typical* return against the index. The "hot market" test (many listings in the previous year) gave opposite answers in the two periods and is not a usable signal (section 3).

### 2.4 Since 2023, and a check against the tracker
95 ordinary listings from 2023 to mid-2025: typical one-year return −17%, average +0.5%, index +10%; 27% halved, 10% doubled. The same picture.
The new-listings tracker's 2014–2025 baseline (1,089 listings, typical one-year return −17.9%) agrees with mine where the two overlap (748 listings matched on code and date; typical difference in one-year return 1 point). The tracker's list is built from the vendor's symbol file, which misses most companies delisted before 2018: 158 of my 2014–2023 listings are not in it, and 58% of those have since left the list against 38% of the matched ones. Its base rates are therefore a little too kind.

### 2.5 Back-door listings and relistings (1,014, reported apart)
Typical three-year return −37% and −48%; average +23% and +33% against the index's +32% and +29%. A slightly fatter right tail (5% five-fold in 2013–2022, the years of the technology back-door listings) and the same poor typical outcome. These were not part of any rule: the join between the old shell and the new company is often unpriced in the data.

## 3. Which early signs separate winners from losers

Test: at six months after listing (126 sessions), rank the listings of each year on the sign, and compare the top third with the bottom third (or flagged with not flagged) on the return over the next two years minus the index. t is across listing years. A sign passes if it has the predicted direction with t ≥ 2 in 2001–2012 and t ≥ 1.5 in 2013–2022. (`out/indicators.csv`, `out/an3.txt`.)

| Sign at six months | Predicted | 2001–2012: gap in average (t) | 2013–2022: gap in average (t) | Halved within 2 years, 2013–2022: sign / opposite | Result |
|---|---|---|---|---|---|
| Size (traded value), largest third against smallest | better | −4 points (−0.4) | −23 (−0.6) | 42% / 49% | **no** |
| Resources company | worse | +19 (1.3) | +7 (0.4) | 55% / 44% | **no** (wrong sign on average) |
| First-day move (open to close), highest third | none | +7 (0.5) | 0 (0.0) | 50% / 53% | nothing |
| Ahead of the index since listing, top third | better | −18 (−0.7) | −24 (−0.7); typical +11 | 40% / 58% | **no** on averages; fewer disasters |
| Volume rising after the first three months | none | 0 (0.0) | −33 (−1.0) | 46% / 49% | nothing |
| Most volatile third | worse | +9 (0.5) | **−37 (−4.0)** | **61% / 33%** | **one period only** |
| Close under A$0.20 | worse | +12 (0.7) | −17 (−1.5) | 56% / 45% | one period only |
| Shares on issue up >10% in year one (2010+; 191 names) | worse | no data | −36 (−1.2); typical −41 (−5.2) | **72% / 25%** | one period, small |
| Profit-making at 12 months (2016+; 687 names) | better | no data | +2 (0.1); typical **+34 (4.3)** | **30% / 57%** | one period; fewer disasters, no extra winners |
| Revenue over A$1m at 12 months (2016+) | better | no data | −22 (−0.7) | 47% / 56% | no |
| Hot market (many listings in prior year) | worse | +44 (1.8) | −10 (−0.5) | 52% / 43% | **no** (signs disagree) |
| Small, loss-making, non-resources (2016+) | worse | no data | −17 (−1.1); typical −24 (−4.3) | 60% / 49% | one period |
| Big first-day jump, non-resources | worse | +19 (1.6) | **−21 (−3.5)** | 44% / 44% | one period (signs disagree) |

**No sign passed in both periods.** The pattern is consistent though: in the 2013–2022 listings the *typical* outcome and the *halving rate* separate clearly on volatility, price level, share issuance and profit, while the *average* does not, because the few enormous winners turn up in every group. None of those four was confirmed on 2001–2012, when the mining boom rewarded exactly the jumpy penny explorers the signs warn against.

**What the big winners looked like at six months** (five-fold or more five years after listing: 60 of 1,282, and 28 of 801):

| At six months | All listings | Later five-fold winners | Later −90% losers |
|---|---|---|---|
| Above the first-day close | 39% / 36% | **68% / 64%** | 24% / 24% |
| In the top third for return against the index | 34% / 34% | **65% / 61%** | 24% / 23% |
| In the top third for traded value | 34% / 34% | 48% / 57% | 28% / 28% |
| Resources | 59% / 31% | 60% / 25% | 58% / 28% |
| Most volatile third | 34% / 34% | 33% / 25% | 37% / 46% |
(first figure 2001–2012, second 2013–2022)

So the owner's instinct is half right. A company that will be big has usually *started* well: two-thirds of the later winners were already above their first-day close at six months. But most companies that start well do not become big: of those above their first close at six months, 6–8% went on to five-fold, against 2% of the rest. And waiting costs little: the typical winner had risen only 9–18% by month six, and went on to make 250–310% in the following three years. **There is no need to buy on day one.** The average new listing returned +1.5% in its first six months, level with the index, and the typical one fell 11–13%.

## 4. Rules a person could follow, after costs and tax

Books (`code/simlib.py`, `rules84b.py`): the account sits in the ASX 200 fund; each buy takes 4% of the account (25 places), funded by selling the fund; proceeds go back to the fund. Half-spread per side: the larger of half a price tick and 0.25% to 2.5% by traded value. Controls, 200 random books each: C1 = random young companies of the same age in the same months (same exit rule); C2 = random companies listed over five years, same traded-value band, same months (same exit rule).

| Rule | Listings 2001–2012: buys / lead after tax (t) / percentile among C1, C2 | Listings 2013–2022: buys / lead after tax (t) / percentile among C1, C2 | Share of trades that halved |
|---|---|---|---|
| R0 every listing at 6 months, hold 2 years | 158 / −2.3 (0.3) / –, 56 | 123 / −10.4 (−1.6) / –, 3 | 37% / 50% |
| R0n same, non-resources | 149 / −7.7 (−1.5) / 20, 7 | 127 / −15.7 (−3.2) / 14, 0 | 32% / 50% |
| R1 quality screen¹, hold 2 years | 26 / 0.0 (−0.5) / 73, 82 | 56 / −0.4 (−0.1) / 95, 75 | 19% / 25% |
| R2 same screen at 12 months | 27 / −1.0 (−1.5) / 54, 46 | 54 / −2.7 (−1.1) / 92, 24 | 19% / 39% |
| R3 R1 with resources allowed | 36 / −0.7 (−1.0) / 74, 76 | 62 / −1.3 (−0.3) / 94, 63 | 25% / 29% |
| R4 R1, sell on a 35% fall from the best month-end, up to 3 years | 26 / −0.2 (−0.5) / 51, 78 | 58 / **+3.4 (1.1)** / 98, 98 | 12% / 7% |
| R5 wait until in the 300 most traded, hold 2 years | 138 / −2.5 (−0.4) / –, 78 | 116 / −3.7 (−0.4) / –, 17 | 28% / 21% |
| R6 profit-makers at 12 months (2016+) | | 79 / −3.6 (−1.5) / 77, 37 | 33% |
| *Second stage, exploratory:* | | | |
| **E1 R4 with the traded-value floor at A$100,000** | 54 / **+2.9 (1.4)** / 92, 96 | 81 / **+1.7 (0.6)** / 84, 91 | 9% / 6% |
| E2 R4, calm names only | 26 / −0.2 / 51, 77 | 45 / +3.7 (1.2) / 100, 100 | 12% / 4% |
| E3 R4 with resources allowed | 36 / −0.4 / 51, 68 | 64 / +2.6 (0.8) / 97, 96 | 11% / 8% |
| E4 R4's exit on 12-month entries | 27 / −0.7 / 41, 48 | 54 / −1.5 / 83, 30 | 4% / 20% |
| E5 R4 held up to 5 years | 26 / −0.8 / 42, 45 | 58 / +4.2 (1.1) / 93, 99 | 12% / 7% |
| E6 every listing over A$50,000 a day, same exit | 128 / −2.0 / 55, 46 | 153 / −4.2 / 55, 21 | 12% / 12% |
¹ non-resources; A$250,000+ a day; 20 cents or more; above the first-day close; ahead of the index since listing.

What the table says:
- **Buying the group loses** (R0, R0n, E6), with or without a stop.
- **The screen alone gets to about level** (R1): it removes most of the disasters (19–25% halved against 37–50%) and still trails slightly.
- **The exit rule is what turns "level" into "possibly ahead"** (R4 against R1 in 2013–2022: +3.4 against −0.4). Cutting a holding at −35% and letting the rest run kept a2 Milk for the full three years and sold the 2021 listings early. The same exit on random older companies (C2) made nothing, so it is not the exit alone.
- **Twelve months is too late** (R2, E4), and **waiting for the top 300 is worse** (R5), which agrees with report 62: by then the easy part is over and one in four still halves.
- **The result is one or two companies.** In 2013–2022 R4 made A$146,000 on 58 trades; A$138,000 of it came from three (a2 Milk +1,400%, Afterpay +420%, IDP Education +310%). The typical trade lost 14%. Only 41% of trades made money. a2 Milk was also not a young company: it had been listed in New Zealand since 2004.

**Choosing the paper line.** The rule written in `PREREG_84b.md` before the second stage ran: the design with the best *worse period* among those ahead of the median C2 book in both periods. That is **E1** (+2.9 / +1.7). Stress tests of E1, using the month-end version that the paper line will run (`early_hist.py`, `loo.py`):

| E1, month-end clock, A$100,000 | 2001–2012 | 2013–2022 | 2023–May 2025 |
|---|---|---|---|
| Lead after tax (t) | +1.4 (0.6) | +3.3 (1.0) | +2.0 (6 buys) |
| Buys / of which sold on the stop | 55 / 34 | 77 / 61 | 6 / 4 |
| Best company removed | +0.7 | +0.3 | |
| Best three removed | −0.9 | −2.1 | |
| All non-takeover delistings written off | +1.4 | +1.6 | |
| A$25,000, 10 places | +0.6 | −2.2 | +4.6 |
| Tracking error against the fund | 7% a year | 13% a year | |
| Average share of the account in young companies | 23% | 28% | |

The same rule with two equally reasonable timings (buy the day after the 126th session, or at the next month-end) gives +2.9 or +1.4 in one period and +1.7 or +3.3 in the other. That spread *is* the uncertainty. Against the adopt bar: t 0.6–1.4 (needs 3.0); lead above +1 (met); 90th percentile of controls (met in one period, 84th–91st in the other). **Not passed.**

## 5. Is this the best approach?

| Question | Answer |
|---|---|
| Against the ASX 200 fund | The fund wins on evidence. It already holds every company that becomes big, from the day it enters the index, and its weight grows with the company at no cost and no tax (report 31). Of the 28 five-fold winners among 2013–2022 listings, the larger ones (a2 Milk, Afterpay, WiseTech, IDP) entered the ASX 200 within about one to three years of listing (index dates from memory, not re-checked). |
| Against a small-company index fund | Small Ords price index: +1.7% a year in the first window and +3.7% in the second, against +3.5% and +4.7% for the ASX 200 before dividends. VSO since 2013: 8.8% a year against 9.1%. The small-company fund is the cheap way to hold young companies and it has been behind for 25 years. |
| Against holding all new listings | Worse than either fund: typical holding down by half; −2 to −10 points a year in a capped book. |
| Against waiting for the top 300 | Worse than buying the screened names at six months (−2.5 / −3.7). Report 62's finding stands: young top-300 names halve about one time in four. |
| Against Big Wins (H82, M3, D2) | Big Wins works where the evidence is good and the prize is small: its loser-screen is the best-supported fact in the programme, worth +0.2 a year in a real book (report 82). EARLY is the reverse: weak evidence, larger possible prize, three times the bumpiness. They do not overlap: Big Wins needs 200 trading days and a calm year, so it almost never holds a company in its first 18 months. They can run side by side on paper. |
| Is "early" the right idea at all? | For *owning* big winners, no: the index does that. For *owning more of them than the index*, the only version with any support is narrow: **not at the float, not explorers, not illiquid, only the ones already working at six months, and sold without argument when they stop working.** That is closer to "buy the early leaders and cut the losers" than to "invest early". |

### What cannot be tested with the data held
| Item | Why it matters | Can the owner collect it? |
|---|---|---|
| Issue price and allocation | The published first-day gain (about 20% on average; far more for mining floats in old studies) goes to those with an allocation. Retail investors mostly get allocations in the floats nobody else wants. Not testable here. | Issue price: yes, from the prospectus, 2 minutes. Allocation: no rule can secure one. |
| Escrow release dates | US lock-up expiries cost 1–2% over three days; no ASX study exists. Releases on small ASX floats can be a large share of the tradable shares. | Yes, from the prospectus and Appendix 3B notices; 5 minutes a company. |
| Prospectus forecast against first result | Earnings surprises drift (report 79); no ASX IPO test. Industrials only. | Yes; 5 minutes at the first result. |
| Cornerstone, venture or private-equity backing; retained founder stake; underwriter options | Mixed published evidence, partly from conflicted industry studies. Bird and Yeung (2010): the floats with the most institutional interest and biggest pops did worst later. | Yes; 5–10 minutes. Subjective. |
| Oversubscription | Not disclosed reliably. | No. |
**Is manual collection worth it?** For all 100 or so listings a year, no: 20–30 hours a year for signs with no ASX evidence. For the 15–25 a year that pass the size, price and non-resources tests, about 4 hours a year: yes, as a record beside the paper line, starting now, because the only way these can ever be tested is forward. No rule should use them yet.

## 6. What is delivered for 30 November

1. **`deep84/AMENDMENT_shadow_EARLY.DRAFT.md`** — the paper line, written to the format of the existing shadow amendments: books (A$100,000 primary, A$25,000 information, a brokerage stress), rules Y1–Y9 (month-end clock; universe from the new-listings tracker; the five tests; 4% slices; the three reasons to sell; data-block rule; nothing tuned), comparators, two sets of random controls, scoring, the adopt and stop bars, the daily indicator scoreboard, known gaps, trial count. **It is a draft: it has not been hashed or added to the ledger, and no live code was changed.**
2. **Reference code**: `early_ref.py` (the rules as pure functions), `early_live.py` (reads the tracker's files and prints the decision table), `early_hist.py` (history test; reproduces section 4's stress table and, with the floor at A$250,000, R4 to within 0.2 points). Hashes in `deep84/out/early_code_hashes.txt`.
3. **Dry run** on the tracker's data as of 18 Nov 2026, with the one-off start-up window (companies between 6 and 12 months old): 22 looked at, 2 passed. This shows the mechanics only. It is not a registered decision and not a recommendation.
4. **Daily learning**: the tracker already refreshes every new listing each day. The amendment adds a record of each listing's six-month indicator values and scores them at +12 and +24 months. This is where a forward record has real power (about 100 new cases a year), and it is the honest route to a better rule: first reading 31 Dec 2028.

### Proven and not proven
| Statement | Standing |
|---|---|
| New listings as a group trail the index; the typical one halves | **Proven** on 2,221 listings over 22 listing years, both periods, all delisting assumptions; agrees with the published Australian studies |
| Big winners exist at about 1 in 100 (ten-fold) and carry the group's whole return | **Proven** (descriptive) |
| Buying on day one is not needed; winners can be bought at six months | **Supported** in both periods (descriptive) |
| High volatility, sub-20-cent price, heavy share issuance and losses mark the likely disasters | **One period only**; to be scored forward |
| Early strength marks the likely big winners | Both periods, but 6–8 in 100 against 2 in 100 |
| The EARLY rule beats the index fund after costs and tax | **Not proven.** Positive in three samples, t 0.6–1.4, rests on one to three companies per period, sensitive to timing and account size |
| Any early-investing rule meets the adopt bar | **No** |

## 7. Files
`deep84/PREREG_84.md`, `PREREG_84b.md`, `out/prereg84_hash.txt`; `code/build84a.py` (daily matrices), `build84b.py`, `build84c.py` (classification), `build84d.py` (features and outcomes), `link84.py` (re-joined histories), `fetch_fund.py`, `fundfeat.py` (752 EODHD fundamentals files, 7,520 credits), `an1.py`, `an2.py`, `an3.py`, `simlib.py`, `rules84b.py`, `loo.py`, `early_ref.py`, `early_live.py`, `early_hist.py`, `early_dryrun.py`; `out/an1.txt`, `base_by_year.csv`, `base_rates.json`, `indicators.csv`, `an3.txt`, `rules_main.csv`, `rules_r6.log`, `log_*.csv` (every trade), `vals_*.csv`, `early_hist.json`, `early_decision_2026-11-18.csv`; `data/F.pkl` (the listing table: class, flags, features, outcomes), `data/links84.csv`. Literature: `deep84/LIT_ASX_IPO.md` (separate agent; abstracts only, not re-verified here).
