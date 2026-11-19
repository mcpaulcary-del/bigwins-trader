# 81. Inside the Big Wins algorithm: where the return goes, and what a better one can and cannot do

19 November 2026. Author: research agent (Fable). Scope: Big Wins only (H82 rules v1.3/v1.4, M3, and new designs). Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades.
Work folder: `scratchpad/deep81/` (`PREREG_81.md`, `PREREG_81H.md`, `code/`, `out/`, `PROGRESS.md`). The live paper code, ledger and `68_forward_record/` were read, never written. Trial count: 1,710 → **1,729** (`out/trials_81.csv`).

How to read the figures: "lead" = the design's compound return minus the index fund's, in points a year. Unless stated, A$0 brokerage (the owner's platform), half-spread as modelled, 32% tax, 50% discount after 12 months. "Sold" = everything sold and taxed at the end (programme convention). "Kept" = nothing sold at the end.

## 0. Answer first

**1. Why H82 does not beat the index.** Its share-picking is worth about +3 points a year. All of it is spent paying for the way the book is built. On ASX 2018–2026 at A$100,000 (frozen rules, `_old` companies restored; arithmetic points a year against the ASX 200 fund, section 1.2):

| Cause | Points a year | Comment |
|---|---|---|
| Picking better shares inside each size band | **+3.1** | Real. Almost all of it comes from *not owning the worst fifth* of the 300 |
| Holding 14% in the 20 largest companies when the index holds 55% | **−1.2** | Equal weights in a period when the giants led (largest 20: 10.0% a year; the rest: 7.0%) |
| Swapping the whole list each January | −0.2 | Ranges from −4.5 to +2.2 in a single year; pure timing luck |
| Idle cash (3% of the account) and odd lots | −0.4 | |
| A bumpier ride (30 shares, 4.7% monthly swings against 4.0%) | −0.35 | Lowers the compound return |
| **Lead before costs** | **+0.8** | 9.6% against 8.8% |
| Costs | −0.7 | Brokerage 0.2 (A$0 for the owner), spread 0.4 (about 0 if orders join the closing auction) |
| Tax, both sold at the end | −0.2 | Engine loses 2.1 to tax, the fund 1.9. If the fund is never sold it loses only 1.35 |
| **Lead after costs and tax** | **−0.05** | 6.79% against 6.84%. With A$0 brokerage +0.2; at the closing auction +0.8 |

At A$25,000 the same picking is worth as much, but ten shares cost more: January swap −1.4, idle cash −0.6, bumpier ride −0.7, costs −2.3 at A$6.60 brokerage (spread alone is about 0.4; the A$0-brokerage re-run still reads −1.7 because a ten-share book takes a different path). Result after tax: 6.45% against 6.84%.

**2. The big winners.** The engine did own most of them. It owned too little, for too short a time. The 25 companies that made 63 of the index's 83 points over the period carried 56% of the index. H82 held 17.5% in them on average (3.3% each, 12 months at a time) and got 27 points from them. It held CBA for 28 of 107 months, WiseTech for 12, Pro Medicus for 24, Xero for 24, Altium for 12, BHP never. Nothing in a 12-month momentum score keeps a company for nine years (section 1.4).

**3. The signal works as a loser-detector, not a winner-detector.** The worst tenth by score returned −13% a year; tenths 3 to 10 returned between 5% and 10%, no better than the index (8.6%). And the losers it avoids are small: the worst fifth by score is only 5% of the market's value. Removing them from an equal-weight list adds 2.9 points. Removing them from a cap-weighted list adds 0.4. That is the whole problem in one line: **the edge lives where the index has almost no money** (section 2).

**4. What I built, and the plain result.** Five pre-registered designs, each aimed at a diagnosed loss. **None beats the index by the pre-set bar. I did not find a winner.**

| Design | Aimed at | 20 other markets, lead after tax (A$25k / A$100k) | ASX 2018–26 (not a clean test) | Verdict |
|---|---|---|---|---|
| **D1 keep-winners**: buy the strongest, never trim, sell only when it becomes a loser | selling winners after 12 months; turnover; tax | +1.0 / +0.55 (s.e. 0.8 / 0.5); ahead in 11 of 20 | +0.1 / −1.3 | fail |
| **D2 cap-weighted, losers excluded** | the size handicap | +0.2 / +0.3 (s.e. 0.5 / 0.4); ahead in 8 of 17 | +1.3 / +0.5 | fail; closest to "index-like, slightly ahead" |
| **D3 index core + mid-cap picks** | use the picks where they work | −0.3 / −0.2 | −2.6 / −1.7 | fail |
| **F1 accounts filter** (no loss-makers, no heavy share issuers) on D3 | blow-ups | +0.1 / −0.1 against D3; blow-ups not reduced | +1.3 / +0.4 against D3 | no use shown |
| **H fast big-winner hunter**: weekly breakouts, 20% trailing stop, all liquid ASX shares | "buy and sell quick like NEXTDC" | (ASX only) | **+4.7 at A$25k, −3.8 at A$100k** | fail; a lottery (section 6) |

For reference, the existing M3 shadow design, re-run in my own third engine, scored +1.1 / +1.2 on the same 20 markets (it was designed on them) and +1.6 / −0.5 on ASX.

**5. Does the best design beat the index, and how confident am I?** No. The best new construction (D2) is an index-like book that sits 0 to +1 point from the fund, with a tracking error of 3–7 points a year, so its sign cannot be told apart from luck in nine years. Confidence that none of the five meets the bar: high. My estimate of the true after-tax edge of the best Big Wins construction at A$100,000: **between −0.5 and +1 point a year; most likely about +0.3.** At A$25,000 it is negative once the ten-share bumpiness is counted.

**6. Fundamentals, commodities, news: "are we sure these should be cut?"** Mostly yes, and for a stated reason (section 5). Among the shares the engine actually buys, loss-makers and heavy share issuers did *better* than the rest on ASX (10.7% against 9.1% over the next year), because momentum has already removed the bad ones. A filter there throws away winners such as Xero and Galaxy. One audit finding: the ASX row of the earlier fundamentals development (report 76 §8.3) ran on the faulty zero-traded-value pack and should be disregarded. Verdicts: accounts-based quality and debt: keep out. Share issuance: keep as a printed red flag, not a rule. Commodity trend: forward-log only. News and announcements: never tested (no dated history); forward-log only.

**7. The NEXTDC question.** A rule that buys breakouts and sells quickly was tested directly. Over 2010–2026 it traded 197 of the 205 ASX shares that rose five-fold or more, and kept a median of **4%** of each rise. It held NEXTDC eight times during its 13-fold run and came out with a small loss. The fast exits that limit losses are the same exits that throw the winner back. 59% of trades lost money; the best 1% of trades made 72% of the profit. At A$25,000 one share (Vulcan, +817%) made the result; at A$100,000 the line lost to 93 of 100 random versions of itself. Small-cap spreads and short-term gains taxed in full cost 4 to 6 points a year between them.

**8. New faults found in this dive** (section 3): (a) ten renamed companies are carried twice in the top-300 history and rule A7(b) does not catch them (Atlas Arteria/Macquarie Atlas, Healius/Primary, Kelsian/SeaLink, Janus Henderson, Propertylink and five more); the `_old` fix as run in report 80 *added* one of these (Propertylink held twice). With them removed H82 at A$100,000 reads 10.3% before costs, 9.7% after, 7.3% after tax, against 8.8 / 8.8 / 6.8 for the fund. (b) Two faithful implementations of the same H82 rule text differ by up to 1.4 points a year at A$100,000. Both facts say the same thing: **any lead smaller than about 1.5 points is inside the noise of the machinery itself.**

**9. What to do.** (i) Give the fix for the duplicate test to whoever is repairing rule A4 (section 3.1). (ii) If one new shadow line is wanted, add D2 (spec in section 4.5); it is the only new design that removes the size handicap, and it costs almost nothing to track. Do not fund it. (iii) Do not start a fast-trading line. (iv) Keep the red-flag panel; do not put accounts into the score.


---

## 1. Diagnosis: where each point goes

No new trial was run for this section. It uses the frozen report-64 engine (`deep81/code/engine_dd.py`, a byte copy), the frozen M3 code (`improve5/code/sim5.py`, imported read-only), and universe averages. Data: EODHD, 29 Dec 2017–13 Nov 2026, `_old` symbols restored, v1.4 traded value. Market caps: ASIC "total product in issue" from the daily short-position files (as published, delisted companies included) × close (`code/mk_caps_asic.py`). A cap-weighted top-300 built this way tracks the issuer's A200 total-return index with a tracking error of 0.96 points a year (−0.14 mean), so the caps are sound.

### 1.1 H82 rebuilt, with the owner's real costs (`out/h82_runs.pkl`, `code/run_h82.py`)

| % a year | A$25,000 | A$100,000 | Index fund |
|---|---|---|---|
| Before costs | 9.20 | 9.59 | — |
| After costs, A$6.60 brokerage + half-spread (as report 80) | 6.94 | 8.93 | 8.78 |
| After costs, **A$0 brokerage** + half-spread | 7.48 | 9.16 | 8.80 |
| After costs, A$0 brokerage, closing auction (no spread) | 9.20 | 9.59 | 8.80 |
| After tax, A$6.60 | 6.45 | 6.79 | 6.84 |
| After tax, A$0 brokerage | 6.22 | 7.07 | 6.85 |
| After tax, A$0, closing auction | 6.34 | 7.61 | 6.85 |
| Same, **ten duplicate companies removed** (section 3.1): before / after costs (A$6.60) / after tax | 9.21 / 7.17 / 6.47 | 10.29 / 9.73 / 7.30 | 8.78 / 6.84 |

The A$25,000 column goes *down* after tax when brokerage is removed (6.45 → 6.22). That is not an effect; it is a ten-share book taking a different path. Read the A$25,000 column as ±2.

Review-month stress (rule M1, A$0 brokerage, lead after tax): A$100,000: +0.2 (Dec), −1.6 (Mar), +0.2 (Jun), −0.4 (Sep). A$25,000: −0.6, −0.5, −2.5, **+3.5** (`out/timing.json`).

### 1.2 The split, year by year (A$100,000)

Building blocks, total return, no costs (`out/diag3.md`):

| % | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026* | CAGR |
|---|---|---|---|---|---|---|---|---|---|---|
| A200 total-return index (issuer) | -2.7 | 23.2 | 1.2 | 18.0 | -0.8 | 12.4 | 11.5 | 10.4 | 7.7 | 8.8 |
| top-300 cap-weighted (my build) | -3.4 | 23.9 | 4.1 | 17.6 | -2.6 | 13.0 | 11.4 | 9.8 | 5.9 | 8.64 |
| top-300 equal-weighted | -10.5 | 23.6 | 12.7 | 19.1 | -12.8 | 6.0 | 9.1 | 20.1 | -6.8 | 6.01 |
| top-100 cap-weighted | -2.7 | 24.5 | 2.6 | 17.1 | -0.4 | 13.4 | 11.8 | 8.9 | 7.7 | 9.04 |
| top-100 equal-weighted | -7.5 | 27.3 | 5.3 | 16.1 | -5.0 | 9.1 | 9.3 | 17.9 | 3.5 | 8.05 |
| largest 20 by cap, cap-weighted | 0.3 | 23.5 | 5.7 | 15.7 | 2.3 | 14.3 | 11.4 | 7.0 | 10.6 | 10.03 |
| cap rank 21-100, cap-weighted | -7.7 | 24.7 | -1.2 | 18.7 | -5.1 | 12.7 | 12.3 | 9.1 | 3.1 | 7.02 |
| cap rank 101-300, cap-weighted | -6.1 | 22.9 | 11.4 | 22.0 | -15.5 | 7.4 | 8.8 | 25.4 | -7.4 | 6.85 |
| largest 20 EW | 0.9 | 26.2 | 6.3 | 15.1 | -3.0 | 16.2 | 14.8 | 5.3 | 10.4 | 10.07 |
| cap rank 21-100 EW | -8.1 | 24.5 | 2.7 | 18.4 | -3.5 | 11.6 | 8.8 | 11.9 | 2.7 | 7.35 |
| cap rank 101-300 EW | -10.9 | 25.3 | 17.0 | 20.2 | -17.5 | 3.4 | 8.9 | 25.4 | -12.4 | 5.46 |
| H82 score top decile, EW | 3.4 | 22.0 | 0.4 | 33.7 | -7.7 | 3.7 | 27.3 | 19.2 | -11.4 | 9.18 |
| H82 score top decile, cap-weighted | 7.2 | 14.0 | 15.2 | -8.0 | -11.2 | -0.7 | 27.3 | 15.4 | 4.0 | 6.47 |
| H82 score top half, cap-weighted | 1.6 | 24.2 | 2.4 | 19.4 | -3.1 | 11.9 | 14.6 | 12.7 | 7.6 | 9.97 |
| top-300 cap-weighted ex bottom 20% by H82 score | -2.8 | 24.3 | 3.3 | 17.1 | -2.0 | 12.8 | 12.3 | 10.5 | 7.9 | 9.08 |
| top-300 cap-weighted ex bottom 20% by M3 score | -2.7 | 24.2 | 3.4 | 17.0 | -2.5 | 12.7 | 12.4 | 11.0 | 7.4 | 9.02 |
| bottom 20% by H82 score, cap-weighted | -12.6 | 12.6 | 18.2 | 22.7 | -14.2 | 17.7 | -9.3 | 0.8 | -9.8 | 1.96 |
| bottom 20% by H82 score, EW | -24.0 | 12.3 | 22.2 | -3.1 | -28.6 | -11.6 | -6.3 | 16.0 | -18.4 | -6.2 |
| top-300 EW ex bottom 20% by H82 score | -7.3 | 26.9 | 10.0 | 25.0 | -9.1 | 10.4 | 13.1 | 21.0 | -3.9 | 8.9 |

What the blocks say:
- **Equal weight against cap weight.** Top-300 equal-weighted: 6.0%. Cap-weighted: 8.6%. A random equal-weight book starts 2.6 points behind. The gap is the giants: the 20 largest returned 10.0%, ranks 21–100 7.0%, ranks 101–300 6.9% (5.5% equal-weighted).
- **The score.** The best 30 by H82 score, equal-weighted: 9.2%. That is +3.2 over the equal-weight list and only +0.4 over the index.
- **Cap-weighting the picks does not rescue it.** The top tenth by score, cap-weighted: 6.5%. Momentum among the giants did not pay in this period.
- **Losers.** The worst fifth by score: −6.2% equal-weighted, +2.0% cap-weighted. Leaving them out lifts the equal-weight list from 6.0 to 8.9, and the cap-weighted list from 8.6 to 9.1.

Brinson split of the engine's actual month-end holdings against the cap-weighted top 300 (arithmetic points a year; `code/diag3.py`):

| Size band (by market cap) | H82 weight % | Index weight % | Being in the band | Names chosen inside it |
|---|---|---|---|---|
| Largest 20 | 14.0 | 55.3 | −0.54 | −0.28 |
| 21–50 | 19.6 | 18.4 | +0.10 | +0.43 |
| 51–100 | 23.7 | 13.9 | −0.08 | +0.53 |
| 101–200 | 29.7 | 9.7 | −0.45 | +1.58 |
| 201–300 | 8.8 | 2.7 | −0.25 | +0.63 |
| No cap / outside | 4.3 | 0.0 | 0.00 | +0.17 |
| **Total** | | | **−1.22** | **+3.06** |

By industry the same total splits +0.6 allocation, +1.2 selection: the engine was underweight banks (3% against 20%) and materials (12% against 18%), which cost 0.7, and overweight technology hardware and software, which earned 1.2. Industry is not the story; size is.

| Year | Index % | H82 before costs % | Size tilt | Picking | January swap (new list minus old list in January) |
|---|---|---|---|---|---|
| 2018 | −2.7 | −9.6 | −3.9 | −2.7 | — |
| 2019 | 23.2 | 13.4 | −0.2 | −3.8 | **−4.5** |
| 2020 | 1.2 | 21.1 | +1.4 | +15.3 | −0.6 |
| 2021 | 18.0 | 31.6 | +2.2 | +9.8 | +0.6 |
| 2022 | −0.8 | −11.9 | −5.7 | −5.4 | +1.2 |
| 2023 | 12.4 | 5.9 | −1.9 | −3.3 | −1.4 |
| 2024 | 11.5 | 19.1 | −0.1 | +6.8 | +2.0 |
| 2025 | 10.4 | 19.7 | +4.4 | +6.4 | −1.4 |
| 2026 to Nov | 7.7 | 3.8 | −6.8 | +4.1 | +2.2 |

The picking gain is not steady: it is +15 and +10 in 2020–21 and negative in four of nine years. The January swap column is new: the frozen engine sells last year's list on the first trading days of January and buys the new one. In January 2019 the old list rose 5.4% and the new list 0.9%. Over eight Januaries the swap cost 0.2 a year at A$100,000 and 1.4 a year at A$25,000, with single years between −7.4 and +3.7. It is luck, and a ten-share book has a lot of it.

Costs (A$100,000, nine years): A$7,446 in all at A$6.60 brokerage, of which spread A$4,179. Turnover 0.8 a year, 467 trades. Tax: the engine realises nearly every gain each year; 98% of positions are closed within two years (median holding exactly 12 months).

### 1.3 What the buys and sells did next (`out/diag2.md`)

| A$100,000 book | Number | Next 12 months against the index | Next 24 months against the index |
|---|---|---|---|
| Shares bought | 228 | **+2.6** | −1.6 |
| Shares sold | 183 | −2.3 | −1.8 |

The buy and the sell are both right for a year. After that the advantage is gone, and by month 24 the bought shares are behind the index. So the yearly swap is not the mistake it looks like, and holding the same picks longer does not add return (this is why D1 below does not win). 257 positions: 141 gains, 116 losses; median result +2.2%; the five best made 44% of the profit, the ten best 70%.

Sold and then rose most over the next two years: Perenti +201%, Fisher & Paykel +164%, Mineral Resources +157%, Technology One +136%, a2 Milk +121%, Goodman +115% (sold Jan 2023) and +99% (sold Jan 2020), NextDC +108% (sold Jan 2019), Qantas +103%.

### 1.4 The index's big winners, and what H82 and M3 did with them

Top 25 contributors to the cap-weighted top-300 return (107 months):

| company | mean index weight % | total return % | points of index return | months H82 held (of 107) | H82 mean weight when held % | points it gave H82 | mean H82 score percentile | M3 holdings (from, to, return) |
|---|---|---|---|---|---|---|---|---|
| BHP | 7.08 | 318 | 10.2 | 0 | 0.0 | 0.0 | 72 | [('2017-12', '2019-09', 0.22), ('2021-02', '2021-09', -0.26), ('2022-02', '2023-06', 0.09), ('2026-05', '2026-10', -0.08)] |
| CBA | 7.79 | 207 | 9.6 | 28 | 3.3 | 1.0 | 76 | [('2021-09', '2023-04', 0.0), ('2024-08', '2025-09', 0.17)] |
| FMG | 2.13 | 663 | 4.2 | 36 | 3.9 | 3.5 | 58 | [('2019-03', '2021-09', 0.92), ('2023-02', '2024-06', -0.03)] |
| WES | 2.62 | 290 | 3.8 | 36 | 3.4 | 2.2 | 81 | [('2019-12', '2021-10', 0.38), ('2024-04', '2026-03', 0.09)] |
| MQG | 2.68 | 241 | 3.5 | 36 | 3.3 | 0.9 | 76 | [('2018-09', '2019-08', -0.01), ('2026-07', '2026-10', -0.01)] |
| NAB | 4.00 | 107 | 3.3 | 25 | 3.4 | 0.8 | 72 | [('2021-04', '2023-04', 0.06), ('2024-05', '2025-03', -0.01)] |
| ANZ | 3.50 | 125 | 2.9 | 10 | 3.4 | 0.4 | 71 | [('2021-04', '2022-05', -0.13)] |
| CSL | 5.14 | 61 | 2.7 | 30 | 3.4 | -0.3 | 62 | [('2018-05', '2021-02', 0.44)] |
| WBC | 4.11 | 91 | 2.5 | 28 | 3.2 | 1.2 | 68 | [('2024-06', '2026-09', 0.22)] |
| RIO | 1.81 | 261 | 2.5 | 31 | 3.2 | 0.2 | 72 | [('2017-12', '2019-09', 0.18), ('2022-03', '2022-08', -0.23), ('2023-03', '2023-05', -0.1), ('2026-03', '2026-10', -0.12)] |
| GMG | 1.71 | 281 | 2.2 | 48 | 3.6 | 3.1 | 70 | [('2018-11', '2020-01', 0.43), ('2023-12', '2025-03', 0.16)] |
| WOW | 1.78 | 142 | 1.7 | 12 | 3.6 | 1.4 | 74 | [('2020-01', '2022-02', -0.0), ('2026-06', '2026-10', 0.02)] |
| TLS | 1.96 | 115 | 1.5 | 19 | 3.3 | 0.2 | 73 | [('2023-04', '2023-09', -0.12)] |
| ALL | 1.10 | 216 | 1.4 | 12 | 2.9 | -0.9 | 65 | [('2020-01', '2020-05', -0.12), ('2021-06', '2022-03', -0.14), ('2024-09', '2025-10', 0.1)] |
| QBE | 0.89 | 236 | 1.2 | 36 | 3.2 | -0.7 | 68 | [('2018-11', '2020-04', -0.33), ('2023-02', '2024-09', 0.06), ('2025-03', '2025-10', -0.12), ('2026-07', '2026-10', 0.05)] |
| TCL | 1.71 | 73 | 1.1 | 0 | 0.0 | 0.0 | 72 | [('2023-04', '2023-09', -0.15)] |
| APT | 0.33 | 1013 | 1.0 | 0 | 0.0 | 0.0 | 56 | [('2019-08', '2021-06', 2.79)] |
| NST | 0.58 | 405 | 1.0 | 12 | 3.4 | 1.4 | 56 | [('2017-12', '2019-12', 0.8), ('2020-05', '2020-12', -0.12), ('2022-12', '2024-07', 0.28), ('2025-11', '2026-04', -0.22)] |
| WDS | 1.77 | 64 | 1.0 | 0 | 0.0 | 0.0 | 56 | [('2018-09', '2019-08', -0.17), ('2022-02', '2023-12', 0.06), ('2026-03', '2026-10', -0.05)] |
| BXB | 0.87 | 189 | 1.0 | 36 | 3.7 | 2.2 | 72 | [('2023-03', '2024-05', 0.06), ('2024-09', '2026-05', -0.12)] |
| PME | 0.35 | 2309 | 0.9 | 24 | 3.9 | 6.0 | 64 | [('2023-09', '2025-11', 2.11)] |
| EVN | 0.41 | 506 | 0.9 | 12 | 3.3 | -0.1 | 53 | [('2018-12', '2020-01', 0.04), ('2020-04', '2021-02', -0.12), ('2023-11', '2024-02', -0.27), ('2025-03', '2026-07', 0.56)] |
| REA | 0.80 | 151 | 0.9 | 24 | 3.1 | 1.1 | 63 | [('2019-09', '2021-12', 0.55), ('2023-05', '2025-07', 0.71)] |
| SUN | 0.76 | 182 | 0.9 | 24 | 3.4 | 1.0 | 71 | [('2023-02', '2025-11', 0.61)] |
| RMD | 0.66 | 247 | 0.9 | 24 | 4.1 | 2.8 | 67 | [('2018-04', '2021-04', 0.95), ('2024-08', '2025-10', 0.05)] |

The 25 names: 62.8 of the index's 82.7 points, on a mean index weight of 56.5%. H82's mean weight in them: 17.5%; points from them: 27.3 of its 99.4.

| Company | When H82 (A$100k) held it | Why not longer |
|---|---|---|
| CBA | 2023; Sep 2024–Dec 2025 | Score in the 45th–84th percentile until 2022. A bank drifting up 8% a year is never a top-30 momentum name. Index weight 7.8%, H82 weight 3.3% when held |
| WiseTech | 2018 only | Score dropped from the 97th to the 51st percentile by the December 2018 review; sold; then +87% in two years |
| Pro Medicus | 2021; 2024 | Score at the 65th–66th percentile in Dec 2021 and Dec 2022; sold Jan 2022; re-bought Jan 2024; sold Jan 2025 at +163% when it ranked just outside the list |
| Xero | 2020–2021 | Sold Jan 2022 (34th percentile); the score was right, it was at the 9th percentile a year later |
| Altium | 2018 only | 56th percentile in Dec 2018 |
| Goodman | 2019; 2021–22; 2024 | In and out three times; 48 months in all |
| BHP | never | Score at the 85th–97th percentile in four Decembers, but never inside the final list of 30 |

The pattern is the same each time. A long winner has flat or falling years inside its run. A 12-month score drops it in those years, and takes it back only after it has risen again. And when it is held, it is 1/30 of the book, while the index lets a winner grow to 5–8%.

### 1.5 M3 (50% index fund + 15 momentum names from the 100 most traded), frozen code, corrected data (`out/m3_runs.pkl`)

| % a year, to 30 Oct 2026 | A$25,000 | A$100,000 | Fund |
|---|---|---|---|
| Before costs | 11.47 | 8.28 | 8.54 |
| After costs (A$6.60) | 10.26 | 7.98 | 8.54 |
| After costs (A$0) | 11.38 | 8.19 | |
| After tax (A$6.60 / A$0) | 7.42 / 8.69 | 6.55 / 6.61 | 6.97 |
| Without `_old` names (as report 77): before costs | 12.85 | 8.56 | |

At A$100,000 M3 is 0.3 behind before costs. Its satellite is drawn from the 100 most traded, where the score sorts worst (section 2), and it is equal-weighted against a cap-weighted top 100 (8.05% against 9.04%). The ideal monthly top 15 made 9.2%; the real satellite, which waits two months to sell and never sells a gain inside a year, made about 8.0%. The A$25,000 book holds five or six shares, so its +2.9 before costs is not evidence. Even in the A$100,000 book the two best positions (Afterpay +279%, Pro Medicus +211%) decide the sign.


---

## 2. What the score ranks on, and whether the signal works

**What it is.** H82 (also called H80) ranks the 300 most-traded shares on the mean of four percentiles: return over months 12 to 1 (s1), return over the last 6 months (s2), closeness to the 52-week high (s3), and low volatility of daily returns (s4). M3 is the first three, inside the 100 most traded. Three of the four terms are the same thing measured three ways: recent price strength. There is no term for size, value, profit or anything long-run.

**Forward returns by tenth, ASX top 300, Dec 2017–Oct 2026** (monthly re-sort, equal weight, no costs, compound % a year; index 8.6; `out/signal_study.md`):

| signal | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | universe EW | top-bottom (t) | top - EW (t) | bottom - EW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s1 12-1m return | -10.4 | 4.6 | 3.7 | 7.1 | 7.4 | 5.2 | 5.1 | 6.4 | 10.7 | 12.1 | 5.6 | 22.4 (2.55) | 5.9 (1.0) | -16.5 |
| s2 6m return | -11.7 | 6.5 | 6.3 | 4.6 | 6.5 | 6.3 | 7.6 | 6.3 | 9.2 | 11.8 | 5.7 | 23.5 (2.59) | 5.5 (1.23) | -18.0 |
| s3 near 52w high | -16.1 | 1.6 | 10.1 | 8.6 | 6.7 | 11.8 | 10.1 | 9.3 | 4.9 | 6.9 | 5.7 | 24.2 (2.43) | 1.1 (0.3) | -23.1 |
| s4 low volatility | -8.6 | 3.3 | 6.4 | 7.8 | 8.4 | 6.1 | 7.8 | 5.5 | 8.4 | 5.5 | 5.7 | 14.4 (1.27) | -0.2 (-0.05) | -14.6 |
| H82 score (s1+s2+s3+s4) | -12.9 | -0.9 | 8.3 | 9.1 | 4.7 | 9.9 | 8.5 | 9.3 | 8.2 | 9.2 | 5.7 | 22.6 (2.25) | 3.3 (0.83) | -19.3 |
| M3 score (s1+s2+s3) | -13.0 | 7.2 | 1.1 | 8.6 | 5.0 | 6.0 | 9.0 | 9.7 | 9.3 | 10.5 | 5.6 | 24.0 (2.6) | 4.5 (1.02) | -19.4 |

- Every component has the same shape: one terrible bottom tenth (−9 to −16%), then a flat line. For the H82 score, tenths 3 to 10 run 8.3, 9.1, 4.7, 9.9, 8.5, 9.3, 8.2, 9.2. The top tenth is no better than the fourth.
- Top minus bottom is large (22–24 points, t about 2.5). Top minus the universe average is small (3–6 points, t about 1). A long-only book earns only the second.
- Inside the 100 most traded the sort is weaker still: H82 top tenth 8.1% against 7.7% for the equal-weight 100; M3 top tenth 7.1%. Low volatility is negative there (top tenth 2.2%).
- 2001–2015 (price-only panel): the M3 top tenth made 19.5% against 3.8% for the list. That era is where every design in this programme was born, and it has not repeated since 2016.

**Does construction waste the signal?** Partly, and not in the way usually assumed.

| Question | Evidence | Answer |
|---|---|---|
| Is the hold period wrong? | Monthly re-pick 9.18%; December pick held 12 months 9.24%; buys lead for 12 months and not after (1.3) | No. Yearly is fine; longer is worse |
| Is the position count wrong? | 30 names: tracking error 8 points; 10 names: 16 points, January swap −1.4, bumpiness −0.7 | 10 is too few. 30 is the floor |
| Are the sell rules wrong? | Sold shares lag the index by 2.3 over the next year | No |
| Is equal weighting wrong? | Costs 1.2 against the index; but cap-weighting the top tenth gives 6.5% | Equal weight is the cost of holding the names where the signal works. There is no free fix |
| Is the universe wrong? | Picking gain by band: largest 20 −0.3; 21–100 +1.0; 101–300 +2.2 | The signal works in mid and small names. The index is 55% in the largest 20 |

So the signal is real and the construction is not careless. The two do not fit the benchmark. A loser-detector for small companies cannot move a cap-weighted yardstick, because losers are 5% of it.


---

## 3. Code and data audit

Read line by line this time: `bw13_prep.py` (production data preparation), `engine_dd.py` and `lib_dd.py` (frozen report-64 engine), `packlib.py`, `sim5.py`/`sim6.py` (M3 engine). I also wrote a separate simulator from the rule text (`code/sim81.py`) and compared it with the frozen engine position by position. The live paper scripts were reviewed in report 80 and are being edited by another agent today; I did not re-read them.

### 3.1 New: ten renamed companies are carried twice, and the `_old` fix adds one

Rule A7 drops a renamed company's old code when the two codes show the *same closing prices*. The vendor sometimes stores the old code's history at a different scale (Propertylink: `PLG` 1.326, `PLG_old` 1.015 on the same day), and then the test fails. A scan for pairs of top-300 companies whose daily returns correlate above 0.97 over 120 or more common days finds (`deep81/PROGRESS.md`, scan in the session log):

| Pair (same company) | Common days | Correlation |
|---|---|---|
| ALX / MQA (Atlas Arteria) | 932, to May 2018 | 1.000 |
| HLS / PRY (Healius) | 1,043, to Dec 2018 | 1.000 |
| JHG / HGG (Janus Henderson) | 724, to Jun 2017 | 1.000 |
| KLS / SLK (Kelsian) | 1,628, to Jan 2022 | 1.000 |
| COF / CMA_old (Centuria Office) | 987, to Mar 2020 | 1.000 |
| RYZ / MNS | 1,793, to Dec 2023 | 1.000 |
| PLG / PLG_old (Propertylink) | 478, to Mar 2019 | 1.000 |
| WNX / WHA | 522, to Jul 2021 | 1.000 |
| NGI / HFA | 759, to Nov 2017 | 0.9999 |
| EXT / CVT | 829, to Jan 2019 | 0.9996 |

(Three more pairs at 0.998–0.999, CLQ/SRL, GLS/PMC and RG1/VG1, look like related funds, not the same company; not removed.)

Effects: 228 company-months of the top 300 are a second copy; a company with a high score can be bought twice (the A$100,000 book held Propertylink under both codes in 2018–19, 6.7% of the account); and a holding under the old code is treated as delisted and paid out at the rename (Macquarie Atlas, June 2018), a sale the real investor never made. In forward use the same miss would make the engine "sell" a renamed company and perhaps buy it back.

Removed, the frozen H82 result moves to **9.21 / 7.17 / 6.47** (A$25,000: before costs / after costs / after tax) and **10.29 / 9.73 / 7.30** (A$100,000), against 6.94 / 6.45 and 8.93 / 6.79 with the duplicates in (`code/dedup_check.py`). The +0.8 at A$100,000 is not an edge discovered; it is what happens when 0.7% of the universe changes.

**Fix for whoever is repairing rule A4:** test duplicates on daily *returns* (scale-free), for example correlation ≥ 0.995 over at least 120 common days with at least 100 non-zero returns, and apply it between every `XXX_old` and `XXX` as well as between different codes. Report 80's `_old` re-run and its figures (6.94 / 8.93) contain the Propertylink double.

### 3.2 New: the machinery's own noise is larger than the lead being measured

My independent simulator, given the H82 rule text, holds 25–28 of the same 30 names at each March and has scores that correlate 0.99 with the frozen engine's. Its nine-year result at A$100,000 is 7.96% before costs against the frozen engine's 9.59% (and 9.59% against 9.20% at A$25,000). The differences are a monthly instead of a daily clock, dividends reinvested instead of paid as cash, and three to five different names a year. Report 54 called this "one point of path noise". On this evidence it is 1.5.

### 3.3 Other points

| Point | Where | Effect |
|---|---|---|
| Historical rebuilds through the production prep still use close × volume unless patched; the v1.4 traded value only switches on for decisions from 31 Dec 2026 | `bw13_prep.py:105` | A trap for any future re-run. Report 80 and this report patch it in memory |
| Industry group comes from today's ASX file. Dead companies have none and are never refused by the 25% cap | `bw13_prep.py:150–154`; 49 of 257 purchases (A$100,000) had no group; 16% of the book's weight | Mild look-ahead, documented in A11. Direction unknown, small |
| The A$0.50 price floor uses the adjusted price, so a penny share that later consolidated passes | `engine_dd.py:63`, rule B6 | Documented; rare in the top 300 |
| A share that stops trading is known at once never to trade again, and is paid in full after April 2020 | `engine_dd.py:216–222` | 17 payouts at A$100,000; all were at 92–100% of their 12-month high, so they are takeovers, not failures. No bias found here |
| The comparator carries no fund fee (A200 0.04%) | `engine_dd.py:441` | 0.04 in the fund's favour |
| M3 engine: fund pays tax from negative cash; dividends reinvested free; dividend above 8% in a month not taxed | `sim5.py`, `packlib.py:112` | Known from report 77 except the last, which is trivial |
| Report 76 §8.3 (fundamentals development): the ASX set was `pack_ASXv2_M.npz`, the pack with zero traded value from Dec 2024 | `improve5/code/lib5.py:10`, `devF.py:5` | The ASX row of that table, including "quality stayed ahead on ASX in 2023–26", is not reliable. The other seven markets are unaffected |

No look-ahead was found in the signal or decision code: every score at a month-end uses closes up to that day, and every trade is made at the next day's close.


---

## 4. Three designs aimed at the diagnosed losses

### 4.1 Honest status of the test data

The designs come from the diagnosis in section 1, which was done on ASX 2018–2026. **That window is therefore not a clean test for them** and is shown as description. The 20 other market-sets (2018–Oct 2026) were test or development sets for earlier rounds, so none is fresh, but no rule below was fitted on them. Nothing in this programme has unused history left; the only clean evidence from here is forward. `PREREG_81.md` was hashed before any 2018–2026 return of these designs existed (`out/prereg81_hash.txt`, 04:29 UTC).

### 4.2 The designs (code `deep81/code/designs.py`, engine `sim81.py`)

Common to all: monthly decisions at the month-end close, trades at the next day's close; a holding in profit is never sold inside 12 months; **no trims, ever**; price ≥ A$0.50; median traded value ≥ 100 × the order; minimum order A$1,000; up to 30 names (A$2,500 each as a floor).

| | D1 keep-winners (KW) | D2 cap-weighted, losers excluded (CXL) | D3 index core + mid-cap picks (MidSat) |
|---|---|---|---|
| Loss it targets | Winners sold at 12 months; 0.8 turnover; tax | The −1.2 size handicap | Picks only where the score works; giants through the fund at no cost or tax |
| Universe | 100 most traded | 100 most traded, with a market cap | 50% index fund; the rest from traded-value ranks 21–300 |
| Score | M3 | M3, used only to exclude the bottom 30% | H82 |
| Buy | Best-ranked not held (rank ≤ 15), equal parcels | The n largest remaining companies, at cap weights (15% cap on one name) | Best-ranked in the band (rank ≤ 30), equal parcels |
| Sell | Only after two month-ends in the bottom 30% (or unranked) | After two month-ends outside the largest 1.5 × n of the screened list | Only after two month-ends in the bottom 30% of the band |
| Turnover found | 0.3–0.5 | 0.2–0.4 | 0.1–0.2 |

### 4.3 Development (ASX 2001–2015 price-only, US large 2001–2013; 9 counted trials)

Lead over the index, points a year, before tax / after tax sold / after tax kept (`out/dev1.json`, `code/dev2.py`):

| Setting | ASX A$25k | ASX A$100k | US A$25k | US A$100k |
|---|---|---|---|---|
| Reference: H82 form in the same engine | +5.5 / +4.3 / +4.0 | +2.8 / +2.8 / +2.5 | +3.9 / +2.6 / +2.4 | +2.1 / +1.9 / +1.8 |
| Reference: M3 band book, no fund | +2.6 / +2.1 / +1.8 | +2.6 / +2.5 / +2.3 | +2.8 / +2.3 / +2.4 | +0.9 / +0.9 / +0.9 |
| **KW, sell at bottom 30% (chosen before the run)** | +2.7 / +2.2 / +1.9 | +2.4 / +1.8 / +1.6 | +2.9 / +3.1 / +3.3 | +0.6 / +0.7 / +0.8 |
| KW, sell at bottom 50% | +3.0 / +2.4 / +2.2 | +2.6 / +2.2 / +1.9 | +3.0 / +2.7 / +2.7 | +1.6 / +1.3 / +1.2 |
| KW, sell at bottom 20% | +1.8 / +1.3 / +1.0 | +2.3 / +2.3 / +2.2 | +2.6 / +2.9 / +3.0 | −0.9 / −0.4 / −0.4 |
| KW from the top 300 | +2.0 / +1.8 / +1.4 | +3.7 / +3.6 / +3.4 | −0.6 / −0.3 / −0.4 | −0.9 / −0.6 / −0.7 |
| KW with the H82 score | −0.6 / −0.5 / −0.7 | +1.3 / +1.2 / +1.0 | −2.8 / −2.6 / −3.0 | −0.6 / −0.6 / −0.7 |
| **MidSat, H82 score (chosen)** | +0.7 / +0.4 / +0.2 | +2.0 / +1.6 / +1.6 | +1.6 / +1.2 / +1.2 | +1.0 / +0.7 / +0.8 |
| MidSat, M3 score | −0.7 / −0.6 / −1.0 | +2.4 / +2.2 / +2.0 | −1.3 / −1.0 / −1.1 | +0.8 / +0.8 / +0.9 |

Already visible in development: keeping winners halves turnover (0.47 against 0.75) and adds nothing to return. D2 has no development run on ASX (no market caps before 2010). Its machinery test on US 2001–2013 gave −3.3 / −1.5 on a cap file that covers only 29 of the 100 names a month, which says nothing either way.

### 4.4 The look (`out/look_*.json`, `out/look_tables.md`; 100 random books per design, set and size)

Bar, written first: mean lead ≥ +1.0 at both sizes on the 20 sets; ahead at both sizes in more than half and ≥ +1 at both in at least half; at or above the 90th percentile of random books in at least half; no more than one set in five below −2; ASX not worse than −0.5.

**D1 keep-winners**

| set | before tax | after tax, sold at end | after tax, kept | range over 4 starts (100k) | percentile of random books | turnover | tracking error (100k) | top-5 share of profit (100k) | positions losing >50% |
|---|---|---|---|---|---|---|---|---|---|
| ASX | -0.1 / -2.0 | **+0.1 / -1.3** | -0.4 / -1.7 | -1.8 to -0.9 | 71 / 39 | 0.45 / 0.45 | 11.1 | 106% | 1% / 1% |
| ASX, duplicates removed | -0.1 / -1.9 | **+0.1 / -1.4** | -0.4 / -1.8 | -2.0 to -0.9 | 62 / 42 | 0.45 / 0.45 | 11.1 | 106% | 1% / 1% |
| USL | -0.2 / -2.3 | **+0.3 / -2.1** | -0.3 / -2.5 | -2.6 to -1.4 | 62 / 50 | 0.32 / 0.36 | 11.7 | 73% | 4% / 2% |
| CA | +1.9 / -0.0 | **+1.7 / +0.2** | +1.3 / -0.2 | -0.5 to +1.1 | 73 / 81 | 0.43 / 0.44 | 9.8 | 51% | 3% / 2% |
| UK | +3.2 / +0.6 | **+2.7 / +0.6** | +3.0 / +0.7 | -0.0 to +1.0 | 93 / 86 | 0.47 / 0.47 | 7.4 | 68% | 2% / 3% |
| DE | +0.5 / -0.3 | **+0.5 / -0.6** | -0.2 / -1.1 | -1.4 to -0.2 | 63 / 69 | 0.39 / 0.41 | 11.9 | 120% | 0% / 1% |
| FR | -1.3 / -0.5 | **-1.4 / -0.5** | -1.7 / -0.6 | -1.1 to -0.1 | 88 / 100 | 0.34 / 0.29 | 9.4 | 56% | 4% / 1% |
| SE | -2.1 / -1.7 | **-1.2 / -2.1** | -1.9 / -2.9 | -3.1 to -0.6 | 94 / 92 | 0.38 / 0.37 | 10.7 | 54% | 2% / 1% |
| AS | -0.8 / +1.6 | **-0.4 / +0.9** | -0.7 / +0.6 | +0.4 to +1.3 | 55 / 97 | 0.38 / 0.33 | 8.8 | 59% | 0% / 0% |
| CO | +6.3 / +6.2 | **+5.8 / +5.6** | +6.1 / +5.7 | +5.1 to +5.9 | 84 / 96 | 0.35 / 0.32 | 9.4 | 43% | 0% / 1% |
| JSE | -0.3 / +0.1 | **-1.2 / -0.2** | -1.7 / -0.6 | -1.7 to +2.0 | 76 / 70 | 0.39 / 0.42 | 9.3 | 62% | 3% / 3% |
| KO | +1.6 / +1.0 | **+1.6 / +1.0** | +1.0 / +0.6 | +0.5 to +1.4 | 97 / 100 | 0.40 / 0.39 | 17.9 | 67% | 1% / 1% |
| MC | +4.8 / +2.6 | **+3.8 / +2.1** | +3.9 / +2.2 | +1.6 to +3.5 | 96 / 100 | 0.27 / 0.27 | 11.8 | 63% | 4% / 4% |
| OL | +1.0 / +4.0 | **+0.1 / +2.1** | -0.5 / +1.6 | +1.5 to +2.6 | 77 / 85 | 0.43 / 0.39 | 11.5 | 65% | 3% / 2% |
| SA | +7.1 / +4.2 | **+6.0 / +3.1** | +5.2 / +2.2 | +2.1 to +4.3 | 100 / 100 | 0.34 / 0.34 | 12.4 | 81% | 3% / 2% |
| SW | -6.7 / -3.5 | **-5.6 / -3.1** | -6.3 / -3.4 | -3.5 to -2.5 | 25 / 67 | 0.44 / 0.42 | 10.3 | 76% | 0% / 1% |
| TW | -6.8 / -3.1 | **-6.1 / -3.0** | -6.8 / -3.6 | -4.8 to +0.5 | 53 / 46 | 0.52 / 0.50 | 20.5 | 45% | 3% / 3% |
| BK | +3.7 / +1.7 | **+3.4 / +1.3** | +3.6 / +1.3 | +0.9 to +2.1 | 90 / 95 | 0.36 / 0.37 | 11.3 | n/a | 0% / 2% |
| CN | +0.7 / +3.6 | **+1.1 / +2.7** | +1.0 / +2.6 | +1.8 to +4.8 | 45 / 49 | 0.53 / 0.52 | 25.3 | 237% | 5% / 1% |
| HE | -1.4 / -1.8 | **-2.6 / -2.1** | -3.4 / -2.7 | -2.8 to -1.5 | 74 / 89 | 0.35 / 0.30 | 8.2 | 57% | 2% / 1% |
| WAR | +8.2 / +4.1 | **+6.8 / +2.9** | +7.0 / +3.1 | +2.6 to +3.1 | 88 / 68 | 0.31 / 0.28 | 14.1 | 44% | 0% / 0% |
| BR | +5.7 / +2.5 | **+5.1 / +2.3** | +5.1 / +2.1 | +1.6 to +2.7 | 100 / 100 | 0.32 / 0.31 | 8.7 | 82% | 0% / 0% |
| **replication sets (n=20)** | +1.26 / +0.94 | **+1.02 / +0.55** (s.e. 0.80 / 0.51) | +0.69 / +0.25 | | ahead both sizes 11/20; >= +1 both sizes 8/20; any cell < -2: 5/20; >= 90th pct both sizes: 6/20 | | | | |
pooled monthly excess before tax, A$100k, all replication sets stacked: mean +1.18 points a year, Sharpe 0.09, deflated Sharpe at N=1,729: 0.000
ASX cost variants, after tax sold (25k / 100k): A$0 brokerage +0.07 / -1.33; A$6.60 brokerage -0.30 / -1.51; closing auction, no spread -0.08 / -1.27. Kept: -0.38 / -1.74

Fails four of five tests. Mean +1.0 / +0.55 with standard errors 0.8 / 0.5; ≥ +1 at both sizes in 8 of 20; above the 90th percentile of random in 6 of 20; five sets with a cell below −2 (Switzerland, Taiwan, Finland, Sweden, US); ASX −1.3 at A$100,000. It leads where the local index did badly (Brazil, Poland, Spain, Denmark, Thailand) and trails where giants led (Taiwan, Switzerland, US). That is the M3 pattern again.

**D2 cap-weighted, losers excluded**

| set | before tax | after tax, sold at end | after tax, kept | range over 4 starts (100k) | percentile of random books | turnover | tracking error (100k) | top-5 share of profit (100k) | positions losing >50% |
|---|---|---|---|---|---|---|---|---|---|
| ASX | +1.5 / +0.7 | **+1.3 / +0.5** | +1.3 / +0.5 | -0.1 to +1.0 | 69 / 78 | 0.28 / 0.31 | 5.0 | 62% | 2% / 1% |
| ASX, duplicates removed | +1.5 / +0.9 | **+1.3 / +0.7** | +1.3 / +0.7 | +0.0 to +1.0 | 66 / 79 | 0.28 / 0.31 | 5.0 | 62% | 2% / 1% |
| USL | +3.4 / +2.5 | **+3.1 / +2.2** | +2.8 / +2.0 | +2.1 to +2.4 | 52 / 88 | 0.26 / 0.27 | 6.7 | 56% | 0% / 1% |
| CA | -3.2 / +0.4 | **-3.4 / +0.2** | -3.8 / -0.1 | -0.0 to +0.4 | 22 / 97 | 0.36 / 0.36 | 3.7 | 38% | 0% / 1% |
| UK | -0.3 / +0.0 | **-0.3 / +0.3** | -0.3 / +0.3 | +0.1 to +0.4 | 95 / 100 | 0.34 / 0.43 | 5.3 | 62% | 4% / 2% |
| DE | +0.3 / +0.5 | **-0.6 / -0.3** | -1.1 / -0.7 | -0.6 to +0.0 | 54 / 72 | 0.31 / 0.34 | 3.5 | 76% | 0% / 0% |
| FR | +2.3 / +1.2 | **+2.2 / +1.0** | +2.1 / +1.0 | +0.9 to +1.3 | 97 / 94 | 0.21 / 0.26 | 3.1 | 62% | 0% / 2% |
| SE | +3.7 / +3.4 | **+2.5 / +2.6** | +2.1 / +2.1 | +2.4 to +2.8 | 70 / 99 | 0.28 / 0.34 | 4.5 | 42% | 0% / 0% |
| AS | +0.2 / -0.9 | **-0.3 / -1.2** | -0.6 / -1.5 | -1.5 to -0.9 | 44 / 32 | 0.39 / 0.41 | 5.1 | 71% | 0% / 2% |
| CO | +2.7 / +2.5 | **+2.7 / +2.5** | +2.7 / +2.5 | +2.0 to +3.3 | 100 / 97 | 0.40 / 0.40 | 7.0 | 73% | 0% / 0% |
| JSE | +2.0 / +1.6 | **+1.7 / +1.4** | +1.5 / +1.1 | +0.8 to +2.2 | 90 / 85 | 0.42 / 0.42 | 7.2 | 71% | 0% / 4% |
| KO | -1.7 / -2.0 | **-1.2 / -1.6** | -1.3 / -1.8 | -2.1 to -1.0 | 53 / 60 | 0.39 / 0.40 | 6.4 | 95% | 0% / 2% |
| MC | +2.8 / +1.3 | **+2.5 / +0.9** | +2.5 / +0.8 | +0.5 to +1.1 | 100 / 97 | 0.21 / 0.24 | 6.8 | 81% | 0% / 4% |
| OL | -0.7 / +0.5 | **-2.2 / -0.9** | -2.7 / -1.3 | -1.1 to -0.5 | 31 / 30 | 0.35 / 0.33 | 5.1 | 60% | 0% / 1% |
| SA | +2.2 / +2.1 | **+0.6 / +1.0** | -0.5 / +0.1 | -0.0 to +1.5 | 61 / 55 | 0.41 / 0.34 | 7.7 | 101% | 1% / 3% |
| SW | +0.8 / +0.2 | **+0.5 / -0.0** | +0.6 / -0.0 | -0.4 to +0.4 | 82 / 97 | 0.29 / 0.30 | 4.3 | 82% | 0% / 0% |
| TW | -3.5 / -2.4 | **-3.4 / -2.5** | -3.6 / -2.6 | -2.8 to -2.0 | 88 / 100 | 0.22 / 0.27 | 7.3 | 69% | 0% / 1% |
| BK | +1.0 / +1.5 | **+0.8 / +1.3** | +0.9 / +1.4 | +0.3 to +1.9 | 12 / 79 | 0.25 / 0.28 | 4.4 | 509% | 0% / 2% |
| CN | -1.0 / -0.6 | **-1.5 / -1.4** | -1.7 / -1.5 | -2.2 to -0.6 | 7 / 1 | 0.63 / 0.63 | 10.4 | n/a | 1% / 1% |
| **replication sets (n=17)** | +0.65 / +0.69 | **+0.22 / +0.33** (s.e. 0.50 / 0.36) | -0.02 / +0.11 | | ahead both sizes 8/17; >= +1 both sizes 5/17; any cell < -2: 3/17; >= 90th pct both sizes: 4/17 | | | | |
pooled monthly excess before tax, A$100k, all replication sets stacked: mean +0.75 points a year, Sharpe 0.12, deflated Sharpe at N=1,729: 0.003
ASX cost variants, after tax sold (25k / 100k): A$0 brokerage +1.27 / +0.51; A$6.60 brokerage +1.07 / +0.33; closing auction, no spread +1.32 / +0.52. Kept: +1.26 / +0.48

Fails. Mean +0.2 / +0.3. It does what it was built to do: tracking error falls to 3–7 points and no ASX start month is worse than −0.1. But excluding momentum losers from a cap-weighted book beat excluding a *random* 30% in only 4 of 17 sets at both sizes. On ASX it is +1.3 / +0.5 (+1.3 / +0.7 without the duplicate companies), at the 66th–79th percentile of random exclusions. An index-like book that is slightly ahead of the index is what a cap-weighted book of 30 large companies is; the screen adds little.

**D3 index core + mid-cap picks**

| set | before tax | after tax, sold at end | after tax, kept | range over 4 starts (100k) | percentile of random books | turnover | tracking error (100k) | top-5 share of profit (100k) | positions losing >50% |
|---|---|---|---|---|---|---|---|---|---|
| ASX | -3.1 / -2.0 | **-2.6 / -1.7** | -2.9 / -2.0 | -2.1 to -1.1 | 17 / 37 | 0.14 / 0.13 | 4.1 | 934% | 5% / 2% |
| ASX, duplicates removed | -2.6 / -2.0 | **-2.2 / -1.7** | -2.5 / -2.0 | -2.2 to -1.1 | 30 / 18 | 0.13 / 0.13 | 4.1 | n/a | 5% / 3% |
| USL | -0.6 / -1.5 | **-0.6 / -1.4** | -0.7 / -1.6 | -1.7 to -1.2 | 62 / 84 | 0.10 / 0.10 | 3.7 | 52% | 0% / 0% |
| CA | -0.2 / -0.2 | **-0.2 / -0.2** | -0.5 / -0.4 | -0.5 to +0.2 | 54 / 64 | 0.15 / 0.14 | 3.9 | 42% | 0% / 0% |
| UK | -1.7 / -1.5 | **-1.4 / -1.4** | -1.6 / -1.5 | -2.1 to -0.7 | 25 / 85 | 0.16 / 0.14 | 3.6 | 100% | 0% / 1% |
| DE | -1.0 / -0.0 | **-1.3 / -0.3** | -1.6 / -0.4 | -0.9 to +0.1 | 72 / 49 | 0.07 / 0.10 | 5.5 | 113% | 8% / 6% |
| FR | -2.2 / -1.8 | **-1.9 / -1.6** | -2.1 / -1.8 | -2.5 to -1.1 | 80 / 83 | 0.08 / 0.09 | 3.8 | n/a | 0% / 2% |
| SE | -2.3 / -0.9 | **-2.3 / -1.0** | -2.8 / -1.4 | -4.1 to +0.6 | 57 / 96 | 0.10 / 0.10 | 8.9 | 48% | 8% / 3% |
| AS | +0.3 / +0.5 | **-0.1 / +0.4** | -0.1 / +0.3 | -0.2 to +0.8 | 91 / 96 | 0.09 / 0.15 | 5.6 | 74% | 0% / 0% |
| CO | +0.8 / +1.9 | **+0.8 / +1.7** | +1.0 / +1.7 | +1.1 to +1.9 | 57 / 49 | 0.09 / 0.15 | 4.9 | 57% | 0% / 0% |
| JSE | -2.2 / -2.1 | **-2.2 / -2.1** | -2.4 / -2.3 | -2.9 to -1.5 | 27 / 24 | 0.08 / 0.10 | 5.5 | 154% | 7% / 7% |
| KO | -1.6 / -4.1 | **-1.9 / -3.8** | -2.2 / -4.2 | -4.4 to -3.1 | 51 / 50 | 0.11 / 0.12 | 8.8 | 165% | 0% / 7% |
| MC | -0.3 / -1.8 | **-0.5 / -1.7** | -0.8 / -1.9 | -2.6 to -1.2 | 68 / 73 | 0.13 / 0.12 | 5.6 | 75% | 0% / 1% |
| OL | +2.2 / +2.0 | **+1.4 / +1.3** | +1.1 / +1.0 | +1.0 to +1.7 | 58 / 84 | 0.08 / 0.09 | 6.3 | 74% | 0% / 4% |
| SA | +2.7 / +2.4 | **+2.0 / +1.5** | +1.5 / +1.1 | +1.1 to +1.9 | 98 / 99 | 0.10 / 0.10 | 5.6 | 65% | 0% / 4% |
| SW | +0.4 / -1.2 | **+0.3 / -1.1** | +0.3 / -1.1 | -1.4 to -0.6 | 95 / 98 | 0.08 / 0.10 | 5.0 | 64% | 0% / 0% |
| TW | -4.7 / -4.6 | **-4.4 / -4.3** | -4.8 / -4.6 | -5.2 to -3.7 | 68 / 62 | 0.13 / 0.10 | 6.7 | 48% | 4% / 2% |
| BK | +0.5 / +0.6 | **+0.2 / +0.3** | +0.2 / +0.3 | -0.4 to +0.8 | 49 / 79 | 0.10 / 0.12 | 6.5 | n/a | 12% / 6% |
| CN | +0.3 / +3.4 | **-0.0 / +2.9** | -0.2 / +2.8 | +1.9 to +3.7 | 44 / 100 | 0.17 / 0.22 | 7.9 | 137% | 0% / 2% |
| HE | -0.8 / +0.2 | **-0.8 / -0.4** | -1.2 / -0.7 | -0.6 to -0.1 | 84 / 99 | 0.08 / 0.13 | 4.8 | 110% | 7% / 1% |
| WAR | +5.5 / +5.4 | **+4.1 / +4.6** | +3.9 / +4.7 | +4.4 to +5.0 | 87 / 100 | 0.12 / 0.11 | 7.6 | 48% | 0% / 0% |
| BR | +3.0 / +1.8 | **+2.3 / +1.7** | +2.0 / +1.6 | +1.5 to +2.0 | 85 / 100 | 0.14 / 0.17 | 5.2 | 103% | 0% / 1% |
| **replication sets (n=20)** | -0.11 / -0.08 | **-0.33 / -0.24** (s.e. 0.42 / 0.48) | -0.55 / -0.44 | | ahead both sizes 6/20; >= +1 both sizes 4/20; any cell < -2: 4/20; >= 90th pct both sizes: 3/20 | | | | |
pooled monthly excess before tax, A$100k, all replication sets stacked: mean -0.25 points a year, Sharpe -0.04, deflated Sharpe at N=1,729: 0.000
ASX cost variants, after tax sold (25k / 100k): A$0 brokerage -2.56 / -1.71; A$6.60 brokerage -2.15 / -1.80; closing auction, no spread -2.52 / -1.65. Kept: -2.90 / -1.97

Fails. −0.3 / −0.2, and −2.6 / −1.7 on ASX. The mid-cap picks beat other mid-caps, as the diagnosis said. Mid-caps as a group trailed the index, and a long-only book cannot own the first without the second.

**The existing M3 design in the same engine (reference, not a new trial)**

| set | before tax | after tax, sold at end | after tax, kept | range over 4 starts (100k) | percentile of random books | turnover | tracking error (100k) | top-5 share of profit (100k) | positions losing >50% |
|---|---|---|---|---|---|---|---|---|---|
| ASX | +1.4 / -0.6 | **+1.6 / -0.5** | +1.3 / -0.8 | -0.7 to -0.3 | - | 0.42 / 0.39 | 5.1 | 96% | 1% / 1% |
| ASX, duplicates removed | +1.4 / -0.7 | **+1.9 / -0.6** | +1.5 / -0.8 | -0.7 to -0.3 | - | 0.43 / 0.39 | 5.1 | 96% | 3% / 1% |
| USL | -1.9 / -0.1 | **-2.0 / -0.3** | -2.4 / -0.7 | -0.6 to +0.1 | - | 0.31 / 0.34 | 7.7 | 51% | 2% / 1% |
| CA | +1.4 / +0.8 | **+0.8 / +0.6** | +0.3 / +0.2 | -0.1 to +1.4 | - | 0.37 / 0.36 | 6.1 | 46% | 3% / 1% |
| UK | +2.5 / +0.4 | **+1.9 / +0.5** | +1.9 / +0.4 | -0.0 to +0.7 | - | 0.38 / 0.35 | 3.9 | 67% | 0% / 1% |
| DE | +3.0 / +1.8 | **+3.1 / +1.3** | +2.7 / +1.0 | +0.9 to +1.5 | - | 0.37 / 0.31 | 5.8 | 73% | 0% / 0% |
| FR | -0.5 / -0.3 | **-0.4 / -0.2** | -0.7 / -0.4 | -0.4 to -0.1 | - | 0.30 / 0.29 | 5.1 | 74% | 0% / 1% |
| SE | -3.2 / -1.0 | **-2.7 / -1.3** | -3.4 / -1.8 | -1.8 to -0.7 | - | 0.39 / 0.35 | 5.8 | 56% | 0% / 0% |
| AS | +2.9 / +1.6 | **+1.6 / +1.3** | +1.5 / +1.1 | +0.8 to +1.7 | - | 0.35 / 0.29 | 4.5 | 52% | 0% / 0% |
| CO | +6.1 / +4.4 | **+5.9 / +4.0** | +5.8 / +4.0 | +3.5 to +4.3 | - | 0.34 / 0.29 | 5.2 | 36% | 0% / 0% |
| JSE | +4.8 / +2.1 | **+3.3 / +1.6** | +2.9 / +1.3 | +0.9 to +2.1 | - | 0.38 / 0.33 | 6.6 | 44% | 0% / 1% |
| KO | +4.7 / +2.1 | **+4.7 / +2.0** | +4.1 / +1.4 | +1.5 to +2.6 | - | 0.47 / 0.41 | 10.3 | 80% | 5% / 4% |
| MC | -0.4 / +1.7 | **-0.5 / +1.5** | -0.8 / +1.3 | +1.2 to +2.0 | - | 0.31 / 0.29 | 6.9 | 47% | 2% / 1% |
| OL | +4.7 / +3.8 | **+3.4 / +2.6** | +3.0 / +2.3 | +2.1 to +3.2 | - | 0.35 / 0.34 | 6.0 | 44% | 0% / 2% |
| SA | +3.0 / +2.2 | **+2.3 / +1.6** | +1.7 / +1.0 | +1.0 to +2.5 | - | 0.33 / 0.33 | 6.6 | 82% | 3% / 2% |
| SW | -4.6 / -1.4 | **-3.6 / -1.1** | -4.0 / -1.4 | -1.6 to -0.6 | - | 0.35 / 0.33 | 4.9 | 111% | 0% / 1% |
| TW | -1.7 / +0.2 | **-2.6 / -0.1** | -3.1 / -0.4 | -1.2 to +0.9 | - | 0.39 / 0.40 | 10.9 | 35% | 2% / 1% |
| BK | +2.5 / +2.4 | **+0.7 / +2.3** | +0.7 / +2.3 | +2.0 to +2.6 | - | 0.34 / 0.33 | 7.4 | 373% | 3% / 1% |
| CN | +2.6 / +3.0 | **+3.3 / +2.4** | +3.0 / +2.3 | +1.3 to +4.0 | - | 0.43 / 0.44 | 16.7 | 106% | 0% / 2% |
| HE | +1.6 / +0.3 | **+0.8 / +0.0** | +0.4 / -0.3 | -0.3 to +0.2 | - | 0.31 / 0.28 | 4.3 | 62% | 0% / 1% |
| WAR | +2.1 / +3.2 | **+0.6 / +2.7** | +0.2 / +2.6 | +2.4 to +2.9 | - | 0.39 / 0.30 | 7.6 | 44% | 3% / 1% |
| BR | +1.4 / +2.2 | **+0.9 / +1.9** | +0.7 / +1.7 | +1.5 to +2.2 | - | 0.33 / 0.28 | 5.0 | 75% | 0% / 0% |
| **replication sets (n=20)** | +1.54 / +1.47 | **+1.07 / +1.16** (s.e. 0.57 / 0.31) | +0.73 / +0.89 | | ahead both sizes 14/20; >= +1 both sizes 8/20; any cell < -2: 3/20; >= 90th pct both sizes: n/a of 20 | | | | |
pooled monthly excess before tax, A$100k, all replication sets stacked: mean +1.44 points a year, Sharpe 0.19, deflated Sharpe at N=1,729: 0.022
ASX cost variants, after tax sold (25k / 100k): A$0 brokerage +1.63 / -0.54; A$6.60 brokerage +1.51 / -0.62; closing auction, no spread +1.56 / -0.40. Kept: +1.27 / -0.81

M3 was designed on these 20 sets, so +1.1 / +1.2 is in-sample. Its value here is as a check: a third independent engine, at A$0 brokerage, reproduces report 76's pooled figure. On ASX it is +1.6 at A$25,000 and −0.5 at A$100,000.

**The owner's account** (A$5,000 + A$500 a month, ASX, Dec 2017–Oct 2026, A$57,500 paid in, after tax, sold; `out/owner.json`): index fund **A$81,074** (A$83,737 if not sold). D1 A$81,081 (A$77,039 without the duplicates); D2 A$79,434; D3 A$74,329; H82 form A$80,677. Thirty random versions of D1 ranged A$65,600–88,000 (10th–90th percentile). Nothing is ahead of the fund.

### 4.5 Spec of the best new design, for a shadow line (not adopted; for information only)

No design earned a place on merit. If one new shadow line is wanted, D2 is the one to track: it is the only construction that removes the size handicap, it has the lowest tracking error (5 points on ASX) and turnover (0.3), and its forward record would test the diagnosis directly. Expect it to sit within a point of the fund.

**CXL v1.0 (shadow; paper only)**
1. **Clock.** Decide at each month-end close. Trade at the next trading day's close: sells first, then buys.
2. **Universe.** The 100 most-traded companies (rules v1.3 B1, v1.4 traded value, duplicates removed by a *returns* test, `_old` symbols admitted) that have a market cap.
3. **Market cap.** Latest ASIC "total product in issue" on or before the decision day (not older than 45 days) × the day's close. A cap is ignored if yearly traded value ÷ cap is outside 0.02–20.
4. **Loser screen.** M3 score = mean of the percentiles (inside the 100) of: close(ME−1) ÷ close(ME−12) − 1; close ÷ close(ME−6) − 1; close ÷ highest close of 252 days. A company in the bottom 30% of the scored companies, or without a score, is out.
5. **List.** Order the rest by market cap. n = min(30, max(4, floor(account ÷ A$2,500))).
6. **Buy.** When fewer than n names are held: buy the largest listed companies not held, down to rank n, each at its share of the combined market cap of holdings plus purchases (no name above 15%; excess spread pro rata), scaled to the account. Order = min(target, free cash); skipped if under A$1,000 or under half the target. Price ≥ A$0.50; median traded value ≥ 100 × order.
7. **Top-up.** When a purchase is made and n names are held, a holding below 75% of its cap-weight target, by at least A$1,000, is topped up from free cash, smallest first.
8. **Sell.** A holding is sold in full when it has been outside the largest 1.5 × n of the list (rule 5, after the loser screen) at two month-ends running. If it is in profit and its oldest parcel is under 12 months old, the sale waits. **No trims; no other sell rule.**
9. **Payouts, tax reserve, dividends:** as rules v1.3 C1, F, I. Free cash = cash − tax owed.
10. **Record:** A$25,000 and A$100,000 books; comparator A200 at A$0 brokerage; reported sold and kept; 100 random-exclusion books beside it.

---


## 5. "Are we sure these should be cut?" — profits, debt, news and commodities

The Big Wins score uses prices only. The owner asked whether the earlier decisions to leave everything else out were sound. I audited how each family was tested, then tested the one role the diagnosis leaves open.

### 5.1 Audit of the earlier tests

| Family | Where tested | Data | How it was used | Costs | Could the "no" be an artefact? |
|---|---|---|---|---|---|
| Quality, profitability, low debt, value (accounts) | Report 76 §8, 77 | EODHD accounts, annual, 4-month lag imposed (the vendor's "filing date" is the period end). Dead companies thin before 2018. ASX development row ran on the **faulty zero-traded-value pack** | Added to the M3 score; alone; as a "top 60% by quality" filter; as a cap-weight tilt (EI10I) | A$6.60 | ASX row: yes, disregard it. The other seven markets and the 12-set look are unaffected. Never tested on the top 300 or as a narrow "avoid" rule |
| Share issuance (dilution) | 62, 70, 76, 77 | ASIC shares on issue: dated, includes dead companies | Stand-alone; exclusion on H82; tilt | A$6.60 | No. Stand-alone effect confirmed twice (−3.5 points, t −2.2 unseen); exclusion changed the engine by −0.15, because the engine already avoids most issuers |
| Short interest, listing age | 62, 70 | ASIC; price panel | Stand-alone; exclusion | A$6.60 | No. Short interest had the wrong sign unseen |
| Commodity and currency exposure | 60, 70 | Unlicensed price panel 2001–May 2024 (not affected by the `_old` or pack faults) + free driver series | Exposure × commodity momentum as a signal; a "resources only while commodities rise" switch; risk cap | A$6.60; monthly versions lost 6–11 points to turnover at A$25,000 | The return test, no: it adds nothing once the share's own momentum is known (t 0.3–1.4), which is a cost-free statement. The switch (H121) failed its development gate and then led by 3–7 points unseen (t 1.0–1.3): untested forward |
| Results-day reaction | 62 | Headline dates, survivors only | Combined with the score | A$6.60 | Passed in December accounts, failed in June accounts. Fragile, not an artefact |
| Analyst surprise | 79 | Vendor estimates of poor quality (median "miss" 40%) | Tilt on M3 | A$6.60 | The data, not the idea, failed. ASX holdout lacked the `_old` names |
| News, announcements, director trades | 60 (attempt), 61 | **None.** The free news source failed; the ASX site is off limits; no dated archive exists | — | — | Never tested. There is no verdict to overturn |

Two general points. First, A$6.60 brokerage did not decide any of these: the tests that failed did so on ranking power or against random controls, before costs mattered. Second, every one was tested as *more score* or *a tilt*. Only one small filter (top 60% by quality) was tried.

### 5.2 Is there a role for an avoid rule? (description, ASX top 300, 2018–2025 formations; `out/diag4.md`)

Accounts were on file for 99% of top-300 company-months after today's download of 442 more files. Across the whole 300, the flags work as folklore says: loss-makers fell by half or more in the next year 18% of the time against 4% for the rest; heavy share issuers 16% against 5%.

But the engine does not buy from the whole 300. Among the top fifth by H82 score:

| flag | share flagged % | flagged: mean / median 12m return % | not flagged: mean / median % | flagged fell >50% % | not flagged fell >50% % | flagged doubled % | not flagged doubled % | t of mean difference (by month) |
|---|---|---|---|---|---|---|---|---|
| net loss (latest annual accounts) | 14 | 10.7 / 6.5 | 9.3 / 5.1 | 5.6 | 1.5 | 3.7 | 2.0 | 0.2 |
| share count up > 10% in the year | 13 | 10.4 / 5.6 | 9.3 / 5.3 | 4.3 | 1.7 | 4.1 | 2.0 | 0.6 |
| top fifth by debt / assets (non-financials) | 18 | 6.2 / 3.1 | 10.2 / 5.7 | 0.8 | 2.3 | 0.5 | 2.6 | -1.8 |
| operating cash flow negative | 9 | 8.5 / 3.7 | 9.6 / 5.4 | 7.1 | 1.5 | 4.2 | 2.0 | 0.0 |
| net loss OR share count up > 10% (F1 rule) | 24 | 10.7 / 5.7 | 9.1 / 5.2 | 4.3 | 1.3 | 3.8 | 1.8 | 0.6 |
| interest cover below 1.5 | 18 | 10.6 / 7.8 | 9.2 / 4.9 | 3.3 | 1.8 | 2.9 | 2.1 | 0.2 |

Among the names the engine buys, flagged companies fell by half more often (4.3% against 1.3%) and also doubled more often (3.8% against 1.8%), and their mean return was *higher*. In the frozen A$100,000 book, the 52 positions that the rule would have blocked returned 16.1% on average against 5.6% for the other 205, and made A$35,750 of the A$84,100 profit. None of the 15 worst positions (Blue Sky −94%, Perenti −56%, Audinate −55%, James Hardie −51%, Reliance −51%) was a loss-maker or a heavy issuer when bought. The blow-ups in this book are profitable companies that disappointed; accounts do not see them coming. The one flag with the right sign is high debt (top fifth by debt ÷ assets: 6.2% against 10.2%, t −1.8), and it marks dull shares, not blow-ups.

### 5.3 The pre-registered test: accounts as an avoid rule (F1)

D3 buys mid and small companies, where blow-ups live. F1 = D3 that may not buy a company with a net loss in its latest annual accounts or a share count up more than 10% (holdings are never sold on it). Difference F1 − D3, lead after tax, A$25k / A$100k:

| ASX | +1.26 / +0.38 | accounts on file 99% | flagged 36% | positions losing >50%: F1 1.1% vs D3 2.3% |
| ASX, duplicates removed | +0.90 / +0.25 | accounts on file 99% | flagged 36% | positions losing >50%: F1 1.1% vs D3 3.5% |
| USL | -0.99 / -0.45 | accounts on file 84% | flagged 22% | positions losing >50%: F1 0.0% vs D3 0.0% |
| CA | +1.03 / -0.20 | accounts on file 52% | flagged 18% | positions losing >50%: F1 0.0% vs D3 0.0% |
| UK | +0.08 / +0.28 | accounts on file 43% | flagged 9% | positions losing >50%: F1 0.0% vs D3 1.2% |
| DE | +1.38 / +0.27 | accounts on file 50% | flagged 10% | positions losing >50%: F1 5.7% vs D3 5.7% |
| FR | +0.37 / +0.18 | accounts on file 42% | flagged 13% | positions losing >50%: F1 3.4% vs D3 1.8% |
| SE | +0.27 / -0.24 | accounts on file 52% | flagged 14% | positions losing >50%: F1 3.1% vs D3 2.9% |
| AS | -0.48 / +0.16 | accounts on file 95% | flagged 34% | positions losing >50%: F1 0.0% vs D3 0.0% |
| CO | -0.02 / -0.57 | accounts on file 50% | flagged 15% | positions losing >50%: F1 1.1% vs D3 0.0% |
| JSE | +0.35 / +0.01 | accounts on file 44% | flagged 10% | positions losing >50%: F1 12.7% vs D3 7.1% |
| KO | +0.00 / +0.04 | accounts on file 57% | flagged 13% | positions losing >50%: F1 6.9% vs D3 6.8% |
| MC | -0.42 / -0.29 | accounts on file 70% | flagged 23% | positions losing >50%: F1 3.9% vs D3 1.5% |
| OL | +0.48 / +0.73 | accounts on file 53% | flagged 26% | positions losing >50%: F1 3.2% vs D3 4.3% |
| SA | +0.07 / -0.19 | accounts on file 45% | flagged 14% | positions losing >50%: F1 6.8% vs D3 4.3% |
| SW | -0.04 / +0.21 | accounts on file 60% | flagged 12% | positions losing >50%: F1 0.0% vs D3 0.0% |
| TW | -0.18 / -0.07 | accounts on file 66% | flagged 9% | positions losing >50%: F1 1.1% vs D3 2.1% |
| BK | +0.00 / -0.38 | accounts on file 49% | flagged 10% | positions losing >50%: F1 10.0% vs D3 5.9% |
| CN | +0.12 / -0.41 | accounts on file 66% | flagged 11% | positions losing >50%: F1 2.6% vs D3 1.6% |
| HE | -0.13 / -0.83 | accounts on file 82% | flagged 30% | positions losing >50%: F1 1.3% vs D3 1.2% |
| WAR | +0.02 / -0.88 | accounts on file 62% | flagged 20% | positions losing >50%: F1 0.0% vs D3 0.0% |
| BR | -0.43 / +0.07 | accounts on file 92% | flagged 29% | positions losing >50%: F1 1.1% vs D3 1.1% |
mean (replication) 0.07 -0.13 F1 ahead of D3 at both sizes in 5 of 20 ; blow-ups F1 3.15 D3 2.37

Mean across the 20 sets +0.07 / −0.13; F1 ahead of D3 at both sizes in 5 of 20; share of positions losing more than half: 3.2% with the filter, 2.4% without. **Not useful.** On ASX it added +1.3 / +0.4 (+0.9 / +0.25 without the duplicates), which is in-sample and inside the noise. Outside ASX the test is weak: accounts were on file for only 42–66% of the band in most markets, because files were bought only for the 100 most traded.

### 5.4 Verdict by family

| Family | Verdict | Evidence in one line |
|---|---|---|
| Profitability, quality, value from accounts | **Keep out** of the score and the buy rule | Added nothing to 2022 and cost 2–3 points after (7 clean markets); as an avoid rule it blocks the engine's best positions |
| Debt / leverage | **Keep out**; print as a fact | Right sign on ASX (t −1.8, in-sample), no link to blow-ups, one market |
| Share issuance | **Red-flag panel only** (already there) | Real across the 300; no effect inside the engine's picks |
| Commodity trend for resource shares | **Forward-log only** (H121 observation card stays) | No ranking power beyond own momentum; the regime switch has one good unseen period and no clean test |
| Analyst estimates and surprise | **Forward-log only** (collection began 19 Nov) | Historical file unusable |
| News, announcements, director trades | **Forward-log only**; never tested | No dated history can be had legally at this budget |

So the answer to "are we sure" is: yes for accounts, with a better reason than before. The reason is not that profits do not matter. It is that a share already in the top fifth by 12-month price strength has had its bad accounts priced out, and what is left of the flag points at the fast growers.

---


## 6. The fast "big-winner hunter": buy the breakout, sell quickly

The owner's question: if a big win can be caught by buying and selling quickly, as with NEXTDC, why does Big Wins not look at these? Reports 31 and 32 answered from the literature. This section tests it directly. `PREREG_81H.md` was hashed before any EODHD return of the rule existed (`out/prereg81H_hash.txt`, 04:35 UTC). Six counted trials (five development settings, one look).

### 6.1 The rule (H; code `deep81/code/hunter.py`)

- **Universe, each week:** every ASX common stock (not just the top 300) with median traded value of at least A$250,000 a day over 63 days, traded on at least 55 of them, price at least A$0.20. For a purchase, also at least 100 × the order (A$250,000 a day at A$25,000; A$500,000 at A$100,000).
- **Entry** (decided at the week's last close, bought at the next day's close): the close is within 2% of a 52-week closing high set in the last five days; the 6-month return is positive and in the top fifth of the universe; the week's traded value is at least 1.5 times normal. Strongest first.
- **Size:** 10 equal slots at A$25,000, 20 at A$100,000, so one total loss costs 10% or 5% of the account. No adding.
- **Exits:** a daily trailing stop 20% below the highest close since entry; or, at a week-end, 6-month strength below the universe median; or 26 weeks held with less than +10%. All executed at the next day's close. No re-entry for four weeks after a stop.
- **Costs:** A$0 brokerage. Half-spread per side: 0.10% for shares trading A$5m a day or more, 0.25% from A$1m, 0.50% from A$250,000, 1.0% below, and never less than half a tick (0.5 cent on a 50-cent share is 0.5%).
- **Tax:** gains on anything held under 12 months taxed in full at 32%. 98% of its positions are.
- Earnings or revenue acceleration is **not** in the rule: the accounts on file are half-yearly, dated at period end and exist only for companies that reached the top 300. It cannot be tested honestly for small caps.

### 6.2 Development (ASX price-only panel, 2001–2015)

All five settings were far ahead of the price index: after tax +9.5 / +9.7 (base), +6.5 / +5.9 (15% stop), +8.9 / +7.7 (30% stop), +9.2 / +9.8 (no volume test), +8.2 / +9.9 (no new-high test) at A$25,000 / A$100,000 (`out/hdev.log`). The base, written before the run, was kept. Three warnings were written into the pre-registration: the same era gave H82 +3 to +5; the panel has no dividends, so the index is understated by about 4 points; and its small-cap prices are the weakest data in the programme.

### 6.3 The look: EODHD, 31 Dec 2015–13 Nov 2026 (`out/hlook.json`)

| | A$25,000 | A$100,000 | Index fund |
|---|---|---|---|
| Before costs, % a year | 18.0 | 7.8 | 9.4 |
| After spreads | 15.4 | 6.1 | 9.4 |
| After tax | 12.0 | 3.5 | 7.3 |
| **Lead after costs and tax** | **+4.7** | **−3.8** | |
| Percentile among 100 random-entry books (same exits, sizing, costs, tax) | 94 | **7** | |
| Random books, after tax: 10th / median / 90th percentile | 1.6 / 7.0 / 11.0 | 4.1 / 6.2 / 8.6 | 7.3 |
| Trades; share that made money | 434; 42% | 726; 43% | |
| Median trade; mean trade | −4.8%; +4.5% | −2.8%; +1.8% | |
| Median days held; share held under a year | 56; 99% | 71; 98% | |
| Turnover a year | 3.8 × | 3.3 × | |
| Spread paid over 11 years | A$28,000 | A$41,800 | |
| Five best trades as a share of all profit | 176% | 236% | |
| Worst fall | −35% | −31% | |
| Tracking error against the fund, points a year | 30 | 18 | |
| First half (2016–20) / second half (2021–26), after tax | 11.9 / 12.0 | 8.2 / −0.4 | 8.6 / 9.9 |
| Stress: spread × 2 (lead) | +1.7 | −5.4 | |
| Stress: brokerage A$6.60 (lead) | +3.8 | −4.2 | |
| Year by year after costs | 15, 53, 1, 13, 5, **110**, −16, 14, 49, 2, −30 | 8, 18, 0, 8, 20, 41, −19, −9, 30, 16, −31 | 12, 12, −3, 23, 1, 18, −1, 12, 12, 10, 8 |

**Verdict: fail.** The bar needed +2 at both sizes and the 90th percentile of random at both. The A$25,000 result is one share: Vulcan Energy, bought 14 Sep 2020 and stopped out 27 Jan 2021 at **+817%**. The A$100,000 book bought Vulcan two months later, when it passed the larger liquidity test, and made +333% on a slot half the relative size; it then lost to 93 of 100 books that bought at random among strong shares. Two accounts running the same rule, differing only in size, ended 8.5 points a year apart. That is what a lottery looks like.

The stress with unexplained delistings paid at 70 cents in the dollar turns both results negative (−0.6 / −8.4). I do not read much into it: 24 to 42 of the exits are shares that stopped trading, and most are takeover targets. A bid makes a new high on a volume surge, the rule buys it, and the share then sits at the bid price until it is paid out. The rule cannot tell a bid from a breakout, so a tenth of its slots are spent on shares with nothing left to give.

### 6.4 When would it have caught the big winners, and how much did it keep? (`out/hcapture.md`)

Every signal taken, A$2,500 a time, no slot limit, 2010–Nov 2026 (price panel; survivors-only after May 2024). "Share of the run kept" compares the compounded result of the rule's trades in that share with the size of the run, on a log scale.

| company | run (low -> high) | size of run | first entry | trades during the run | won / lost | money multiple from those trades, compounded | share of the run kept (log scale) | best single trade | days in the share of days in the run |
|---|---|---|---|---|---|---|---|---|---|
| NXT | 2011-09-26 -> 2024-07-09 | 13x | 2013-06-11 (already 2.0x off the low) | 8 | 4 / 4 | 0.83x | -7% | 23% | 989 of 4670 |
| PME | 2011-06-28 -> 2025-07-17 | 1944x | 2017-11-20 (already 42.6x off the low) | 6 | 5 / 1 | 2.55x | 12% | 100% | 978 of 5133 |
| WTC | 2016-04-12 -> 2024-11-21 | 36x | 2016-11-07 (already 1.5x off the low) | 6 | 1 / 5 | 0.89x | -3% | 48% | 786 of 3145 |
| ALU | 2011-06-16 -> 2024-05-31 | 817x | 2014-09-01 (already 37.2x off the low) | 7 | 5 / 2 | 5.73x | 26% | 127% | 1492 of 4733 |
| DRO | 2020-04-23 -> 2025-10-09 | 77x | 2024-01-29 (already 4.9x off the low) | 2 | 2 / 0 | 2.34x | 20% | 59% | 76 of 1995 |
| ZIP | 2015-09-21 -> 2021-02-16 | 49x | 2019-02-18 (already 5.0x off the low) | 4 | 2 / 2 | 1.36x | 8% | 106% | 163 of 1975 |
| APT | 2017-06-29 -> 2021-02-10 | 59x | 2018-03-12 (already 2.9x off the low) | 6 | 2 / 4 | 0.93x | -2% | 79% | 310 of 1322 |
| XRO | 2012-11-08 -> 2025-06-24 | 43x | 2013-07-08 (already 3.6x off the low) | 6 | 4 / 2 | 1.78x | 15% | 35% | 1114 of 4611 |
| A2M | 2015-05-29 -> 2020-07-30 | 43x | 2015-11-23 (already 2.2x off the low) | 4 | 2 / 2 | 5.67x | 46% | 273% | 666 of 1889 |
| PLS | 2013-10-23 -> 2026-06-01 | 842x | 2015-09-21 (already 33.1x off the low) | 7 | 4 / 3 | 1.97x | 10% | 52% | 444 of 4604 |
| LYC | 2015-09-30 -> 2026-04-14 | 69x | 2015-11-23 (already 2.9x off the low) | 7 | 3 / 4 | 1.37x | 7% | 45% | 434 of 3849 |
| TNE | 2010-02-09 -> 2025-06-10 | 59x | 2013-02-18 (already 2.5x off the low) | 7 | 5 / 2 | 1.67x | 13% | 23% | 1250 of 5600 |
| FMG | 2016-01-21 -> 2024-01-31 | 21x | 2016-11-07 (already 3.8x off the low) | 4 | 1 / 3 | 0.93x | -2% | 27% | 500 of 2932 |
| MIN | 2016-01-14 -> 2023-01-24 | 28x | 2016-09-05 (already 3.2x off the low) | 5 | 2 / 3 | 1.00x | 0% | 53% | 747 of 2567 |
| REA | 2010-02-08 -> 2025-02-12 | 32x | 2010-03-01 (already 1.2x off the low) | 4 | 3 / 1 | 2.03x | 21% | 65% | 926 of 5483 |
| CAR | 2011-08-08 -> 2024-11-27 | 10x | 2012-06-25 (already 1.4x off the low) | 3 | 2 / 1 | 1.82x | 26% | 74% | 862 of 4860 |
| JBH | 2012-06-26 -> 2025-08-20 | 15x | 2013-03-04 (already 1.7x off the low) | 5 | 3 / 2 | 1.42x | 13% | 41% | 942 of 4803 |
| PNV | 2010-10-18 -> 2020-12-17 | 182x | 2017-12-04 (already 19.3x off the low) | 3 | 2 / 1 | 2.33x | 16% | 99% | 368 of 3713 |

- **NEXTDC:** 13-fold from September 2011 to July 2024. First entry June 2013, with the price already doubled. Eight trades, four gains and four losses, best +23%. Compounded: **0.83×, a loss.** In the share for 989 of 4,670 days.
- **Pro Medicus:** nearly 2,000-fold. First entry November 2017, 43-fold off the low. Six trades, 2.55×.
- **WiseTech:** 36-fold. Six trades, five losses, 0.89×.
- **Altium:** 817-fold. Seven trades, 5.7×, the best of the famous names.
- **DroneShield:** 77-fold. Two trades, 76 days in all, 2.3×.
- **Zip:** 49-fold. Four trades, 1.36×. **Afterpay:** 59-fold. Six trades, 0.93×.

Across all **205** ASX shares that rose five-fold or more while liquid: the rule traded 197 of them at some point; **median share of the run kept 4%** (mean 6%); it kept more than half the run in 3; it *lost money* on 73 of them despite the rise. Of 2,166 trades, 671 were inside such a run and averaged +11.4%; the other 1,495, the false breakouts and ordinary moves, averaged −0.6%. The best 1% of trades made 72% of the profit; the losing trades together cost 2.6 times the net profit.

### 6.5 Plain answer: why doesn't Big Wins look at these?

It did, here, and the test shows why it does not help.

1. **Finding them is not the problem.** A breakout rule touches almost every big winner. So does H82: it held NEXTDC, WiseTech, Pro Medicus, Xero and Altium.
2. **Keeping them is the problem, and fast exits make it worse.** Every long winner falls 20% or more several times on the way up; the rule was shaken out of NEXTDC eight times. A 20% stop sells each time. The rule then waits for a new 52-week high to get back in, which is above where it sold. Quick selling is exactly the feature that turns a 13-fold rise into a small loss.
3. **The winners cannot be told from the false breakouts at entry.** Seven in ten signals were not the start of a five-fold run, and those lost a little each. With hindsight NEXTDC is obvious; on the day, it looked the same as 1,495 others.
4. **Fast trading has the worst costs and the worst tax.** Small-cap spreads took 2 to 3 points a year, and nearly every gain was short-term and taxed in full, another 3. H82 turns over 0.8 times a year; this turns over 3.5 times.
5. **What is left is a few enormous trades.** Whether an account gets one depends on the week, the account size and the liquidity cut. That cannot be relied on and cannot be tested to any confidence: with a tracking error of 18–30 points a year, a century of data would not settle it.

What the result does *not* say: that nobody can do this. A person who knows a company, holds through the falls and adds on evidence is doing something a price rule cannot copy. The rule-based version, at this size, after spread and tax, is not worth a paper line.

---


## 7. Trial count, caveats, files

**Count.** 1,710 at the start. Keep-winners development 6, mid-cap satellite development 2, D2 machinery test 1 (not foreseen in `PREREG_81.md`, counted), hunter development 5, hunter look 1, looks D1, D2, D3, F1 = 4. **Total 1,729.** Random controls, cost and tax variants, the review-month stress, the duplicate-removal re-run and the owner-account form are stresses of frozen rules and are not counted (programme convention). The deflated Sharpe ratio at N = 1,729 on pooled monthly excess is 0.00 for every new design (0.02 for M3); the cross-trial variance used is a stand-in of the right order, not report 64's exact figure.

**Caveats.**
- ASX 2018–2026 is in-sample for the diagnosis and therefore for the designs. The 20 other sets are re-used. Nothing here is a clean out-of-sample test; only the forward record is.
- All 20 other sets cover the same nine years, in which a few giant companies led most indices. "Equal weight trails cap weight" is a fact about that period. If mid and small companies lead for a decade, as they did in 2001–2010, H82 and D1 would look good again, and that would be a size bet paying off, not skill.
- After the pre-registration I found the ten duplicate companies. The ASX rows are shown both ways. `markets.py` and `look81.py` gained an "ASXd" branch after the hash; no design rule changed.
- My engine works on month-ends. A gain is treated as long-term after 360 days, not 367, to stand in for the frozen engine's few-day wait. Dividends are reinvested at no cost and taxed out of the dividend.
- Funds in markets with accumulating index funds are not charged tax on an imputed distribution; this favours the fund slightly.
- F1 outside ASX had accounts for only about half the mid-cap band.
- The hunter's delisting results after April 2020 are paid at the last price; the 70% stress is shown. Its capture table uses the price-only panel, which has no delisted companies after May 2024.
- The Brinson split uses month-end holdings; the January swap is measured separately as the engine's January return minus the old list's.
- Fundamentals for 442 more ASX companies were downloaded today (4,420 EODHD calls; total used today about 8,000 of 100,000). Parsed files only are kept (`deep81/data/fundAU_extra.pkl`).

**Files** (all under `scratchpad/deep81/`)

| What | Path |
|---|---|
| Pre-registrations and hashes | `PREREG_81.md`, `PREREG_81H.md`, `out/prereg81_hash.txt`, `out/prereg81H_hash.txt` |
| Trial ledger | `out/trials_81.csv` |
| Data build (`_old` restored, v1.4 traded value), ASIC market caps, duplicate-free pack | `code/mk_bundle.py`, `code/mk_caps_asic.py`, `code/mk_pack_dedup.py`; `data/pack_ASX81_M.npz`, `pack_ASX81d_M.npz`, `cap_ASX81.npy` |
| Frozen H82 re-run, cost variants, review months, duplicates removed | `code/run_h82.py`, `timing.py`, `dedup_check.py`; `out/h82_runs.pkl`, `timing.json` |
| M3 re-run | `code/run_m3.py`; `out/m3_runs.pkl` |
| Diagnosis tables | `code/diag1.py`–`diag4.py`, `signal_study.py`; `out/diag1.md`–`diag4.md`, `signal_study.md` |
| Own engine, designs, market loader, accounts flags | `code/sim81.py`, `designs.py`, `markets.py`, `lib81.py`, `fundfeat.py`, `ev81.py` |
| Development | `code/dev1.py`, `dev2.py`; `out/dev1.json` |
| Look | `code/look81.py`, `summ81.py`, `owner.py`; `out/look_<SET>.json`, `out/look_tables.md`, `out/owner.json` |
| Hunter | `code/hunter.py`, `hdev.py`, `hlook.py`, `hcapture.py`; `out/hdev.log`, `hlook.json`, `hcapture.md`, `hcapture_trades.csv`, `hcapture_runs.csv` |
| Report builder | `rep/build_report.py`, `rep/p0.md`–`p7.md` |
| Deleted at the end to save disk (rebuild with `code/mk_bundle.py`, about one minute) | `data/bundle_old.pkl`, `TV_daily.npy`, `Craw.npy`, `_hF_v2dev.pkl` |
