# 86. Blind replay of the EARLY rule on old companies: re-modelled decisions against what actually happened

19 November 2026. Author: research agent (Fable). Owner request: "Run your algorithm on old companies and re-model them and then compare against actuals and prove the algorithm please for early investments."
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades. EODHD data under a private, non-commercial licence. The live paper code, the ledger and the scheduled jobs were read, never written.
Work folder: `scratchpad/deep86/` (`PREREG_86.md`, `PREREG_86b.md`, `PREREG_86c.md`, hashes in `out/prereg86_hash.txt`, `RULES_Y1-Y9_frozen.md`, `code/`, `out/`, `PROGRESS.md`). Every pick with its outcome: section 6 and `86_case_table_all_picks.csv` (1,315 rows, all windows).

How to read the figures: "lead" = the book's compound return minus the local index fund's, points a year. A$100,000-equivalent book, modelled half-spread, A$0 brokerage, 32% tax with the 50% discount after 12 months, everything sold at the end. t = mean ÷ standard error of the monthly gap; about 2 is "probably not luck", 3 is the adopt bar. "Unseen" = companies the rule was not chosen on.

## 0. Answer first

**The algorithm is not proven. On the unseen overseas companies it is rejected.** The rule (Y1–Y9, frozen and hashed before any run) was replayed month by month, seeing only the data that existed on each decision day.

| Test | Companies looked at | Bought | Book a year | Index fund a year | Lead after tax | t | Random new-listing books beaten |
|---|---|---|---|---|---|---|---|
| ASX 2001–2012 listings (rule was built on these) | 950 | 56 | +8.2% | +7.7% | +1.1 | 0.5 | 89 of 100 |
| ASX 2013–2022 listings (rule was built on these) | 764 | 77 | +12.0% | +9.1% | +3.3 | 1.0 | 78 of 100 |
| **ASX 2023–2025 listings (unseen)** | 88 | **6** | +12.9% | +10.9% | **+1.9** | 0.9 | 92 of 100 |
| **Canada, TSX + TSXV, 2018+ listings (unseen)** | 879 | **37** | +8.6% | +13.1% | **−3.9** | −1.8 | 36 of 100 |
| **UK, LSE + AIM, 2021+ listings (unseen)** | 247 | **20** | +6.7% | +12.3% | **−5.0** | −3.5 | 19 of 100 |
| **US, 1-in-3 sample of NYSE/NASDAQ, 2017+ listings (unseen)** | 1,351 | **127** | +4.4% | +14.7% | **−8.8** | −1.5 | 45 of 100 |

1. **Unseen results, ASX + Canada + UK together: 63 companies bought. 19 made money (30%). The typical one lost 33%. 4 at least doubled; 18 lost 40% or more.** Of the 46 that have three years of history, 4 beat the local index fund (9%), 22 had halved (48%), 2 had doubled. The unseen books averaged **2.4 points a year behind the fund after tax**; the pooled monthly t is **−2.05** (101 months). The bar for "proven" was +1.0 and t ≥ 3.0. **The US sample (run last, a 1-in-3 sample of NYSE/NASDAQ listings from 2017) agrees: 127 bought, 45 made money, typical result −18%, book 8.8 points a year behind the S&P 500 fund after tax**, although it did buy Okta, MongoDB, DocuSign and Carvana. All four unseen sets together: 190 purchases, 64 made money (34%), 15 at least doubled, 55 lost 40% or more.
2. **The ASX result held up on its only unseen data, but that data is six purchases.** +1.9 a year after tax over 3.4 years; one company (Tasmea, +270%) is all of it — without it the lead is −0.4. Six purchases cannot prove or disprove anything.
3. **In Canada, the UK and the US the rule did not even beat picking new listings at random.** It beat 36, 19 and 45 of 100 random books. A$100,000 became A$198,000 (Canada, fund A$279,000) and A$142,000 (UK, fund A$187,000). Removing the best companies makes it worse, not better, so this is not bad luck with one name. In the UK not one of the 13 picks with three years of history beat the fund.
4. **Why it failed there.** The rule buys what has gone up in its first six months. In 2021 that meant buying 17 Canadian and 8 UK listings at the top of a new-listings boom; almost all hit the 35% stop within a year. The stop limited each loss to about a third, but 46 of the 63 unseen purchases ended at the stop.
5. **What the rule still does on the ASX, and did not do overseas:** avoid the worst of new listings. On the ASX the typical company it rejected did far worse than the typical one it bought (halved within two years: 37–50% of the rejected, 20–26% of the bought). In Canada and the UK the bought group did slightly *worse* than the rejected group (halved: 46% against 41%; 62% against 49%).
6. **Against adopt rule v3:** a back-test cannot pass any step (the ladder needs registered paper months). As an analogue: ASX would sit at the P1 numbers (twins 78–92nd percentile; signal spread positive, t about 1); Canada and the UK would fail P1 on the twins test (36th and 19th percentile; P1 needs 60th) and on the signal spread (negative), and the UK is past the after-tax P2 limit (5.0 behind; limit 5). No market is near P2 (spread t ≥ 2) or P3 (t ≥ 3).
7. **What should happen now: nothing with money.** SHADOW EARLY is registered as paper-only and information-only; this report says keep it exactly there. It gives no reason to raise its status and one strong reason not to: the first out-of-country test went against it.
8. **How much unseen data would settle it.** For the ASX alone: about 225 unseen purchases to show a +10-point 12-month edge per pick at t = 2. The ASX has produced 2–8 qualifying companies a year, so that is **30 to 100 years**. For the book against the fund: a true +2 a year needs 50–160 years on the ASX; a true +5 needs 9–26 years (t = 2). The paper line cannot prove the rule this decade; it can only disprove it (the stop conditions of rule v3 can trigger from month 13).

## 1. What was done, and what makes it blind

- **Frozen first.** Rules Y1–Y9 were copied verbatim to `RULES_Y1-Y9_frozen.md`; the reference code `early_ref.py` (the same file hashed in the ledger, SHA-256 1c27de98…) is imported unmodified. The plan, markets, thresholds, costs, controls, readings and the words "proven / promising / rejected" were written in `PREREG_86.md` and hashed at 06:59 UTC, before any run. The overseas start years were fixed from symbol counts alone in `PREREG_86b.md`, hashed at 08:34 UTC before any Canadian or UK return was computed.
- **The rule (plain words).** At each month-end look at every ordinary company that has just completed 126 trading sessions (six months) since listing. Buy it next day if all five hold: not a resources company; median traded value at least A$100,000 a day; price at least 20 cents; above its first-day close; ahead of the index since listing. Put 4% of the book in each, at most 25 names, rest in the index fund. Sell only if it closes a month 35% below its best month-end since purchase, or after three years, or when it leaves the list.
- **As-of replay.** At decision row *i* the code is handed price, volume and index arrays cut off at row *i*; it cannot read later rows. Fills are at the next session's close with the modelled spread. A takeover or failure enters only as the cash received when the holding stops trading.
- **Audit of blindness.** The cut-off replay was compared with report 84's run on full arrays: identical purchase lists for 2013–2022 and 2023–2025; one company differs in 2001–2012 (OTR), moving that lead from +1.4 to +1.1. The adapter otherwise reproduces report 84 exactly (1.4 / 3.3 / 1.95).
- **Overseas data.** Vendor symbol lists, active and delisted, ordinary shares, local currency. New listing = first price row in 2005 or later; mass first-row days, cross-venue duplicates, funds, trusts, SPACs, capital-pool shells and warrants removed by rules fixed in advance. Thresholds converted at fixed rates (C$90,000 and C$0.18; £53,000 and 10.6p). Local index for the "ahead of the index" test (S&P/TSX Composite; FTSE 100 fund price), local index fund as the benchmark (XIC; ISF). Local tick sizes in the spread. Traded value by the corrected definition of report 83 (the lower of raw and split-adjusted price × volume).
- **Controls.** 100 random books per test: at every decision the same number of purchases, drawn at random from the ordinary listings in the same six-month window, same sizing and same exit rules.
- **Survivorship.** The vendor's delisted histories begin in 2017 (Canada) and are only complete from 2021 (UK). Earlier windows miss the dead companies and flatter any rule. Primary overseas tests therefore start where the dead are present: **Canada listings from 2018, UK listings from 2021.** The longer windows are shown in section 3 with that warning.

## 2. Results

Local currency books of 100,000; "final" is before tax.

| Set | Looked at | Passed | Bought | Years | Book %/yr | Fund %/yr | Lead pre-tax | Lead after tax | t | Random books beaten | Median random lead | Worst fall book / fund | Final A$100k -> book / fund |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ASX 2001–2012 (re-model) | 950 | 56 | 56 | 14.5 | +8.2 | +7.7 | +0.5 | +1.1 | 0.47 | 89% | -1.5 | -59% / -51% | 314,448 / 295,777 |
| ASX 2013–2022 (re-model) | 764 | 87 | 77 | 13.4 | +12.0 | +9.1 | +2.8 | +3.3 | 1.02 | 78% | -0.8 | -39% / -36% | 455,349 / 323,207 |
| **ASX 2023–2025 (unseen)** | 88 | 6 | 6 | 3.4 | +12.9 | +10.9 | +2.0 | +1.9 | 0.87 | 92% | -0.6 | -8% / -13% | 151,056 / 142,086 |
| ASX 2023–Apr 2026, tracker universe (check) | 118 | 7 | 7 | 3.4 | +12.8 | +10.9 | +2.0 | +1.8 | 0.84 | 93% | -0.7 | -8% / -13% | 150,804 / 142,086 |
| **Canada 2018+ (unseen)** | 879 | 37 | 37 | 8.3 | +8.6 | +13.1 | -4.6 | -3.9 | -1.80 | 36% | -3.1 | -33% / -37% | 198,250 / 279,330 |
| **UK 2021+ (unseen)** | 247 | 20 | 20 | 5.4 | +6.7 | +12.3 | -5.7 | -5.0 | -3.48 | 19% | -4.8 | -19% / -13% | 141,569 / 187,210 |
| **US 1-in-3 sample (unseen)** | 1351 | 226 | 127 | 9.3 | +4.4 | +14.7 | -10.3 | -8.8 | -1.50 | 45% | -9.9 | -52% / -34% | 149,099 / 359,852 |
| Canada 2017+ (secondary) | 995 | 48 | 48 | 9.3 | +8.9 | +12.8 | -4.0 | -3.3 | -1.53 | 50% | -3.0 | -33% / -37% | 220,697 / 308,084 |
| UK 2018+ (secondary) | 412 | 44 | 44 | 8.4 | +4.2 | +8.1 | -3.9 | -3.4 | -1.69 | 42% | -3.7 | -28% / -34% | 140,814 / 192,014 |
| Canada 2005+ (survivorship) | 2243 | 105 | 100 | 21.3 | +8.3 | +9.2 | -0.9 | -0.5 | -0.60 | 42% | +11.2 | -41% / -48% | 544,985 / 650,658 |
| UK 2005+ (survivorship) | 1088 | 155 | 133 | 21.4 | +6.5 | +7.2 | -0.8 | -0.3 | -0.26 | 48% | -0.3 | -36% / -45% | 382,738 / 446,362 |
| US sample 2005+ (secondary) | 2449 | 524 | 253 | 21.3 | +6.0 | +11.0 | -5.1 | -4.3 | -1.16 | 42% | -3.6 | -57% / -55% | 345,410 / 932,962 |

`AU_T1b` is the same unseen ASX period rebuilt from the new-listings tracker and fresh vendor prices (the universe the paper line will really use): 7 purchases, +1.8. It is the same trial as ASX 2023–2025, shown as a check of the vendor pipeline. The same pipeline on 2014–2022 ASX listings gives +3.9 against +3.3 from the research panel.

Pooled reading fixed in advance (equal-weight average of the three unseen books' monthly gaps to their funds, 101 months, Jul 2018 – Nov 2026): **−3.2 points a year, t = −2.05**; mean after-tax lead −2.4, pre-tax −2.7. Canada and UK alone: −4.5 after tax, t = −2.33. The monthly gaps of the Canadian and UK books correlate 0.34; neither correlates with the ASX book. With the US sample added (four books, 113 months from Jul 2017): **−2.9 points a year, t = −1.06**; mean after-tax lead **−4.0**. The t is weaker with the US in because the US book swings much more (tracking error 16 points: +62 against the fund in 2020, −42 in 2021), not because the US result is better.

Secondary windows (survivorship warning; not the test): Canada all 2005+ listings −0.5 after tax (100 purchases, 21 years); UK all 2005+ −0.3 (133 purchases). Canada from 2017 (the literal count rule; contaminated by about 250 old companies whose stored history merely starts in 2017) −3.3. UK from 2018 −3.4. US, all 2005+ listings: −4.3 (253 purchases, 21 years). **No overseas window, of eight, is ahead of its fund.**

## 3. Robustness (same rule, no tuning)

Lead after tax, points a year.

| Set | Best 1 removed | Best 3 removed | Best 5 removed | A$25k book (10 names) | Start +12m | Start +24m | Clock -10 sessions | All delistings paid / written off | +0.25% cost a side |
|---|---|---|---|---|---|---|---|---|---|
| ASX 2001–2012 (re-model) | +0.5 | -1.1 | -1.7 | -0.4 | +1.3 | +1.0 | +2.1 | +1.1 / +1.1 | n/a |
| ASX 2013–2022 (re-model) | +0.3 | -2.1 | -3.6 | -2.2 | +3.5 | +0.8 | -0.0 | +3.3 / +1.6 | n/a |
| **ASX 2023–2025 (unseen)** | -0.4 | -1.4 | -0.4 | +4.4 | +3.1 | +0.9 | +1.9 | +1.9 / +1.9 | n/a |
| ASX 2023–Apr 2026, tracker universe (check) | -0.5 | -1.4 | -0.9 | +4.2 | +3.0 | +0.8 | +1.9 | +1.8 / +1.8 | +1.8 |
| **Canada 2018+ (unseen)** | -4.3 | -4.9 | -5.4 | -4.0 | -5.0 | -5.7 | -4.6 | -3.9 / -4.8 | -4.0 |
| **UK 2021+ (unseen)** | -5.1 | -5.1 | -5.1 | -14.0 | -1.2 | -0.9 | -4.7 | -5.0 / -5.0 | -5.1 |
| **US 1-in-3 sample (unseen)** | -10.1 | -13.5 | -13.3 | -11.6 | -12.5 | -11.0 | -11.1 | -8.4 / -15.6 | -9.1 |
| Canada 2017+ (secondary) | -4.0 | -4.6 | -5.1 | -4.9 | -3.9 | -5.0 | -3.6 | -3.3 / -4.1 | -3.4 |
| UK 2018+ (secondary) | -3.8 | -4.5 | -5.0 | -5.1 | -5.7 | -5.2 | -3.4 | -3.4 / -3.9 | -3.5 |
| Canada 2005+ (survivorship) | -1.1 | -1.8 | -2.1 | -0.2 | -0.3 | -0.3 | -1.2 | -0.5 / -0.8 | -0.6 |
| UK 2005+ (survivorship) | -1.5 | -1.8 | -2.1 | -1.8 | -0.4 | +0.2 | -0.7 | -0.3 / -0.9 | -0.4 |
| US sample 2005+ (secondary) | -4.4 | -6.4 | -6.5 | -8.6 | -5.0 | -5.4 | -6.3 | -4.0 / -9.4 | -4.3 |

- ASX: positive only while the best one company is in. Best three removed: negative in all three ASX periods. Same finding as report 84.
- Canada, UK and US: negative on every line. Removing winners, starting later, moving the decision day, changing the delisting assumption or adding UK stamp duty does not change the sign.
- **A$25,000 book (10 names at 10%):** ASX −0.4 / −2.2 / +4.4; Canada −4.0; US −11.6; UK −14.0 (ten places filled with 2021 listings that then fell). The small book is not safer.
- Worst fall of the book: −59% (ASX 2001–12), −39% (ASX 2013–22), −33% (Canada), −19% (UK). Similar to the fund's, because most of the book sits in the fund most of the time.

## 4. Does the rule sort companies? (the "signal spread")

12-month return after the fill, relative to the local fund. "Passed" = the rule said buy; "rejected" = looked at and not bought.

| Set | Passed: number | Passed: typical (median) | Passed: average | Rejected: number | Rejected: typical | Rejected: average* |
|---|---|---|---|---|---|---|
| ASX 2001–2012 | 56 | +0% | +11% | 894 | −21% | +2% |
| ASX 2013–2022 | 87 | −9% | +5% | 677 | −34% | −16% |
| ASX 2023–2025 (unseen) | 5 | +43% | +22% | 53 | −10% | +15% |
| Canada 2018+ (unseen) | 34 | −37% | −27% | 762 | −31% | −9% |
| UK 2021+ (unseen) | 17 | −55% | −50% | 204 | −36% | −33% |
| US 2017+ sample (unseen) | 210 | −32% | −21% | 1,043 | −23% | −14% |

*Averages cap any single 12-month return at +900% (11 rejected companies exceed it, some of them vendor unit errors).

- The pre-registered yearly spread (average of passed minus average of all looked at, by decision year): ASX +8 and +9 points (t 0.8 and 1.1); **Canada −14 (t −0.9, 5 years); UK −14 (t −1.9, 3 years)**; US not usable as registered (the all-companies average is swamped by a few vendor errors; on medians the yearly spread is +2 points, t 0.4). Positive in 1 of the 3 unseen sets at most (the ASX unseen set has no year with three passes, so it has no reading).
- On medians the passed group is well ahead of the rejected group on the ASX; it is behind in Canada and the UK. Halved within 24 months, passed against rejected: ASX 20% v 37% and 26% v 50%; Canada 46% v 41%; UK 62% v 49%.
- Five-fold winners within three years: among unseen overseas picks, 1 of 57 touched five-fold (Lightspeed, after the rule had already been stopped out of it at −48%); none was five-fold at the three-year mark. Among the rejected, 32 Canadian and 1 UK company were (many of them resources companies, which the rule excludes, and some of them data errors). In the US sample 8 of the 127 bought (6%) touched five-fold, against 6–7% of everything looked at: no enrichment. Report 84's one "sign of a big winner" did not carry over.

## 5. Verdict against the pre-registered words

| Condition | Needed | Got |
|---|---|---|
| PROVEN: pooled unseen after-tax lead | ≥ +1.0 | −2.4 |
| PROVEN: pooled t | ≥ 3.0 | −2.05 |
| PROVEN: beats 90 of 100 random books in every market | 3 of 3 | 1 of 3 |
| PROVEN: still ahead with best 3 removed in every market | 3 of 3 | 0 of 3 |
| PROMISING: pre-tax lead > 0 in at least 2 of 3 | 2 | 1 (ASX) |
| PROMISING: beats 80 of 100 random books in at least 2 of 3 | 2 | 1 (ASX) |
| REJECTED: pre-tax lead ≤ 0 in at least 2 of 3 | — | **yes: Canada −4.6, UK −5.7** |
| REJECTED: below the median random book in at least 2 of 3 | — | **yes: 36th and 19th percentile** |
| US sample (reported beside the three, as fixed in `PREREG_86c`) | — | pre-tax −10.3, after tax −8.8, 45th percentile, t −1.5; pooled t with it −1.06 |

**Verdict: REJECTED as a general way to beat the index fund with new listings.** For the ASX specifically: **unproven**, with a small unseen result in its favour (6 purchases, +1.9, t 0.9) that rests on one company.

Against adopt rule v3 (analogue only; no step can be met by a back-test):

| v3 step | Needs | ASX 2001–12 / 2013–22 / unseen | Canada | UK |
|---|---|---|---|---|
| P1 twins percentile | ≥ 60 | 89 / 78 / 92 | 36 | 19 |
| P1 signal spread | mean > 0 | +8 / +9 / no reading | −14 | −14 |
| P2 signal spread t | ≥ 2.0 | 0.8 / 1.1 / — | −0.9 | −1.9 |
| P2 after tax, behind fund (here: both sold) | ≤ 5 | ahead | 3.9 behind | 5.0 behind |
| P3 spread t; twins; after-tax lead | ≥ 3.0; ≥ 90; > 0 | no | no | no |
| Stop: spread t ≤ −1.0 or twins < 20 | — | no | no | **would stop (t −1.9; 19th)** |

## 6. The decisions against the actuals

Every company the rule said to buy, in date order. "Why it qualified" gives the three numbers the rule used that day: median traded value a day, price, and its return since the first day's close with the index's return over the same days in brackets. "If simply held" ignores the stop and the three-year limit (buy-and-hold from the fill; a delisting pays the last price if it was within 30% of its one-year high, otherwise zero). **BIG WIN** = the book at least doubled its money; **BIG LOSS** = the book lost 40% or more. UK prices in pounds.

**Biggest wins and losses on unseen data**

| Market | Company | Bought | Sold | Book result | What happened |
|---|---|---|---|---|---|
| US | Okta Inc (OKTA) | 2017-11-01 at 28.97 | 2020-12-01 at 236.99 (3-year limit) | **+714%** | simply held 12m +107%, 36m +620%; worst -13%, best +752%; still listed, +575% since purchase |
| US | Mongodb (MDB) | 2018-05-01 at 36.51 | 2021-06-01 at 289.74 (3-year limit) | **+690%** | simply held 12m +263%, 36m +688%; worst +1%, best +1058%; still listed, +740% since purchase |
| US | Docusign Inc (DOCU) | 2018-11-01 at 41.85 | 2021-12-01 at 230.79 (3-year limit) | **+449%** | simply held 12m +64%, 36m +577%; worst -11%, best +641%; still listed, +83% since purchase |
| ASX | Tasmea Limited (TEA) | 2024-11-01 at 2.90 | 2026-11-13 at 9.75 (still held) | **+270%** | simply held 12m +87%, 36m not yet; worst -22%, best +334%; still listed, +284% since purchase |
| US | Fastly, Inc. Class A Common Stoc (FSLY) | 2019-12-02 at 19.85 | 2021-04-01 at 70.31 (35% stop) | **+252%** | simply held 12m +312%, 36m -49%; worst -63%, best +549%; still listed, -10% since purchase |
| US | Carvana Co (CVNA) | 2017-11-01 at 14.01 | 2018-11-01 at 44.39 (35% stop) | **+215%** | simply held 12m +217%, 36m +1263%; worst -1%, best +1600%; still listed, +2462% since purchase |
| Canada | Dayforce Inc. (DAY) | 2018-11-01 at 50.64 | 2021-12-01 at 134.67 (3-year limit) | **+161%** | simply held 12m +30%, 36m +203%; worst -14%, best +219%; left the list, paid out |
| Canada | Definity Financial Corp (DFY) | 2022-06-01 at 35.19 | 2025-07-02 at 77.36 (3-year limit) | **+129%** | simply held 12m +6%, 36m +121%; worst -6%, best +129%; still listed, +116% since purchase |
| ASX | Cuscal Limited Ordinary (CCL) | 2025-06-02 at 2.94 | 2026-11-13 at 5.72 (still held) | **+100%** | simply held 12m +68%, 36m not yet; worst -4%, best +131%; still listed, +100% since purchase |
| Canada | Anaergia Inc (ANRG) | 2022-01-04 at 19.40 | 2022-03-01 at 11.78 (35% stop) | **-40%** | simply held 12m -76%, 36m -95%; worst -99%, best -2%; still listed, -91% since purchase |
| Canada | Brookfield Asset Management Rein (BAMR) | 2022-01-04 at 80.81 | 2023-01-03 at 43.53 (35% stop) | **-41%** | simply held 12m -40%, 36m -33%; worst -42%, best -3%; left the list, paid out |
| Canada | Eastwood Bio-Medical Canada Inc (EBM) | 2019-03-01 at 5.20 | 2019-06-03 at 3.20 (35% stop) | **-41%** | simply held 12m -67%, 36m -68%; worst -85%, best +10%; still listed, -68% since purchase |
| UK | Cordiant Digital Infrastructure  (CORD) | 2021-09-01 at 1.14 | 2023-11-01 at 0.63 (35% stop) | **-41%** | simply held 12m -3%, 36m -22%; worst -43%, best +1%; still listed, +32% since purchase |
| Canada | Brookfield Wealth Solutions Ltd. (BNT) | 2022-01-04 at 121.22 | 2023-01-03 at 65.30 (35% stop) | **-41%** | simply held 12m -40%, 36m +17%; worst -46%, best +20%; still listed, -20% since purchase |
| Canada | Verticalscope Holdings Inc (FORA) | 2022-01-04 at 29.30 | 2022-06-01 at 17.71 (35% stop) | **-41%** | simply held 12m -77%, 36m -66%; worst -90%, best -0%; still listed, -93% since purchase |
| UK | Darktrace Plc (DARK) | 2021-11-01 at 6.82 | 2022-01-04 at 3.91 (35% stop) | **-43%** | simply held 12m -47%, 36m -15%; worst -69%, best -5%; left the list, paid out |
| Canada | Banxa Holdings Inc (BNXA) | 2021-08-03 at 3.00 | 2022-06-01 at 1.72 (35% stop) | **-44%** | simply held 12m -63%, 36m -84%; worst -85%, best +44%; left the list, paid out |
| UK | Auction Technology Group Plc (ATG) | 2021-09-01 at 16.42 | 2022-03-01 at 9.30 (35% stop) | **-44%** | simply held 12m -53%, 36m -76%; worst -76%, best -8%; still listed, -72% since purchase |
| UK | Likewise Group Plc (LIKE) | 2022-03-01 at 0.35 | 2022-10-03 at 0.20 (35% stop) | **-45%** | simply held 12m -28%, 36m -43%; worst -59%, best +11%; still listed, +37% since purchase |
| Canada | Li-Ft Power Ltd. (LIFT) | 2023-01-03 at 10.40 | 2023-12-01 at 5.65 (35% stop) | **-47%** | simply held 12m -41%, 36m -49%; worst -87%, best -0%; still listed, -89% since purchase |
| UK | Saietta Group Plc (SED) | 2022-02-01 at 2.20 | 2022-10-03 at 1.20 (35% stop) | **-47%** | simply held 12m -78%, 36m -100%; worst -100%, best +0%; left the list, written off |
| Canada | Lightspeed Commerce Inc (LSPD) | 2019-10-01 at 30.22 | 2020-04-01 at 15.76 (35% stop) | **-48%** | simply held 12m +43%, 36m -12%; worst -60%, best +426%; still listed, -54% since purchase |
| Canada | Just Kitchen Holdings Corp (JK) | 2021-11-01 at 1.45 | 2022-04-01 at 0.76 (35% stop) | **-49%** | simply held 12m -90%, 36m -94%; worst -97%, best +6%; left the list, paid out |
| UK | Facilities By Adf Plc (ADF) | 2022-08-01 at 0.65 | 2024-12-02 at 0.31 (35% stop) | **-50%** | simply held 12m -30%, 36m -66%; worst -77%, best +3%; still listed, -85% since purchase |
| UK | Tinybuild Inc (TBLD) | 2021-10-01 at 2.42 | 2022-07-01 at 1.20 (35% stop) | **-52%** | simply held 12m -50%, 36m -99%; worst -99%, best +0%; still listed, -95% since purchase |
| UK | Trustpilot Group Plc (TRST) | 2021-10-01 at 3.78 | 2022-02-01 at 1.81 (35% stop) | **-52%** | simply held 12m -79%, 36m -42%; worst -86%, best +1%; still listed, -31% since purchase |
| UK | Bens Creek Group Plc (BEN) | 2022-05-03 at 0.89 | 2022-07-01 at 0.42 (35% stop) | **-53%** | simply held 12m -81%, 36m -100%; worst -100%, best +3%; left the list, written off |
| US | Inflarx N.V. (IFRX) | 2018-06-01 at 37.00 | 2019-07-01 at 3.43 (35% stop) | **-91%** | simply held 12m +1%, 36m -92%; worst -94%, best +39%; still listed, -97% since purchase |
| US | Landcadia Holdings Iii Inc (LCY) | 2021-07-01 at 12.45 | 2021-08-02 at 0.01 (35% stop) | **-100%** | simply held 12m -24%, 36m -24%; worst -100%, best -0%; left the list, paid out |
| US | Arclight Clean Transition Corp (ACTC) | 2021-06-01 at 18.77 | 2021-08-02 at 16.94 (left the list) | **-100%** | simply held 12m -100%, 36m -100%; worst -10%, best +2%; left the list, written off |
| US | Gs Acquisition Holdings Corp Ii (GSAH) | 2019-02-01 at 9.95 | 2022-02-01 at 9.94 (left the list) | **-100%** | simply held 12m +24%, 36m -100%; worst -1%, best +51%; left the list, written off |
| US | Pono Capital Three, Inc. Class A (PTHR) | 2023-11-01 at 10.59 | 2024-02-01 at 2.37 (35% stop) | **-100%** | simply held 12m -100%, 36m -100%; worst -78%, best +0%; left the list, written off |

What the table shows that the summary numbers do not:
- **The stop sold winners as well as losers.** Lightspeed (Canada) was stopped out at −48% in the March 2020 crash and then rose more than five-fold from the purchase price. Khiron was sold at +79% on the stop and later went to zero: there the stop saved the gain.
- **Several "new listings" overseas were spin-offs of large companies** (Nutrien, Brookfield Infrastructure Corp, Brookfield Renewable Corp, South Bow, Magnum Ice Cream, Sunbelt Rentals) or listed funds the name filter missed (Cordiant, Digital 9). The rule as written does not exclude them; none was a big win.
- **A few resources companies got through the name-based filter overseas** (Osisko Development, Li-FT Power, Bens Creek, Bradda Head). All four lost 33–53%. The ASX line uses a proper sector flag.
- On the ASX re-model (the periods the rule was built on) the pattern of report 84 is visible line by line: 23 big wins and 29 big losses in 133 purchases, and three companies per period (Zinifex, Worley, The Reject Shop; a2 Milk, Smartgroup, Uniti) make the whole lead.

### ASX 2001-2012 listings (re-model, not blind): 56 companies passed, 56 bought

| Code | Company | Decided | Why it qualified: traded value a day; price; return since first close (index) | Bought | Sold (reason) | Result in the book | If simply held: 6m / 12m / 24m / 36m | Fund over the same 36m | Worst / best point in 3 years | Later |
|---|---|---|---|---|---|---|---|---|---|---|
| AEO | Austereo Group Limited | 2001-09-28 | A$949k; 2.00; +16% (-8%) | 2001-10-01 at 1.95 | 2002-10-01 at 1.51 (35% stop) | -24% | -3% / -22% / -26% / -33% | +33% | -38% / +20% | left the list 2011-04-15 (paid out) |
| BRS | Broadspectrum Limited | 2001-10-31 | A$205k; 2.18; +31% (+1%) | 2001-11-01 at 2.20 | 2004-12-01 at 6.21 (3-year limit) | +177% **BIG WIN** | +18% / +20% / +105% / +189% | +31% | -0% / +195% | left the list 2016-05-30 (paid out) |
| CST | Cellestis Limited | 2001-10-31 | A$222k; 2.01; +644% (+1%) | 2001-11-01 at 2.51 | 2002-02-01 at 1.70 (35% stop) | -33% | -33% / -36% / -40% / +43% | +31% | -60% / +47% | left the list 2011-08-10 (paid out) |
| GLB | Globe International Limited | 2001-11-30 | A$305k; 2.25; +48% (+3%) | 2001-12-03 at 2.31 | 2002-10-01 at 1.43 (35% stop) | -38% | -17% / -80% / -80% / -80% | +30% | -93% / +4% | listed; since buy -56% |
| AWB | Awb Limited | 2002-03-28 | A$867k; 4.40; +27% (+6%) | 2002-04-02 at 4.33 | 2005-04-01 at 4.66 (3-year limit) | +6% | -18% / -18% / +17% / +8% | +34% | -23% / +19% | left the list 2010-11-19 (paid out) |
| JFG | James Fielding Group | 2002-05-31 | A$113k; 3.15; +26% (+3%) | 2002-06-03 at 3.13 | 2005-02-01 at 3.42 (left the list) | +8% | -2% / +3% / -11% / +9% | +35% | -16% / +13% | left the list 2004-12-29 (paid out) |
| AFG | Allco Finance Group Limited | 2002-11-29 | A$236k; 1.94; +8% (-10%) | 2002-12-02 at 1.97 | 2005-12-01 at 8.42 (3-year limit) | +321% **BIG WIN** | +39% / +59% / +201% / +331% | +68% | -6% / +331% | left the list 2008-10-31 (written off) |
| MCG | Macquarie Communications Infra | 2003-02-28 | A$443k; 2.43; +35% (-10%) | 2003-03-03 at 2.47 | 2006-03-01 at 5.48 (3-year limit) | +120% **BIG WIN** | +22% / +40% / +141% / +130% | +94% | -9% / +173% | left the list 2009-07-07 (paid out) |
| WOR | Worley Limited | 2003-06-30 | A$105k; 2.04; +20% (-1%) | 2003-07-01 at 2.04 | 2006-07-03 at 20.52 (3-year limit) | +976% **BIG WIN** | +62% / +48% / +288% / +927% | +83% | -0% / +1119% | listed; since buy +944% |
| PMN | Promina Group Limited | 2003-11-28 | A$17,737k; 3.31; +67% (+7%) | 2003-12-01 at 3.31 | 2006-12-01 at 6.50 (3-year limit) | +95% | +16% / +49% / +48% / +98% | +91% | -6% / +121% | left the list 2007-03-09 (paid out) |
| IPL | Dyno Nobel Limited | 2004-01-30 | A$126k; 16.00; +10% (+5%) | 2004-02-02 at 16.00 | 2007-02-01 at 35.30 (3-year limit) | +157% **BIG WIN** | +20% / +42% / +21% / +169% | +95% | -4% / +181% | listed; since buy +955% |
| JBH | Jb Hi-Fi Limited | 2004-04-30 | A$617k; 2.32; +5% (+4%) | 2004-05-03 at 2.29 | 2007-05-01 at 8.24 (3-year limit) | +275% **BIG WIN** | +53% / +46% / +126% / +283% | +103% | -6% / +283% | listed; since buy +8585% |
| IVC | Invocare Limited Ordinary | 2004-06-30 | A$524k; 2.39; +27% (+9%) | 2004-07-01 at 2.39 | 2007-07-02 at 6.03 (3-year limit) | +188% **BIG WIN** | +41% / +90% / +109% / +193% | +97% | -1% / +195% | left the list 2023-11-03 (paid out) |
| IFL | Insignia Financial Ordinary | 2004-06-30 | A$302k; 4.80; +21% (+9%) | 2004-07-01 at 4.76 | 2007-07-02 at 9.82 (3-year limit) | +122% **BIG WIN** | +69% / +44% / +87% / +129% | +97% | -1% / +167% | left the list 2026-04-29 (paid out) |
| ITF | Integrated Tree Cropping Limit | 2004-09-30 | A$104k; 1.35; +29% (+7%) | 2004-10-01 at 1.35 | 2005-11-01 at 1.00 (35% stop) | -28% | +7% / -21% / -1% / -1% | +100% | -32% / +11% | left the list 2006-07-17 (paid out) |
| PBG | Pacific Brands Limited | 2004-09-30 | A$5,624k; 2.89; +12% (+7%) | 2004-10-01 at 2.89 | 2006-06-01 at 2.15 (35% stop) | -26% | -14% / -1% / -12% / +7% | +100% | -28% / +28% | left the list 2016-06-28 (paid out) |
| ZFX | Zinifex Limited | 2004-10-29 | A$6,592k; 2.10; +15% (+9%) | 2004-11-01 at 2.14 | 2007-11-01 at 16.66 (3-year limit) | +675% **BIG WIN** | +39% / +127% / +622% / +769% | +100% | -2% / +896% | left the list 2008-06-20 (paid out) |
| JST | Just Group Limited | 2004-11-30 | A$3,049k; 3.02; +53% (+16%) | 2004-12-01 at 2.94 | 2005-06-01 at 1.86 (35% stop) | -37% | -32% / -16% / +22% / +74% | +82% | -39% / +100% | left the list 2008-09-02 (paid out) |
| TRS | The Reject Shop Ordinary | 2004-11-30 | A$150k; 2.60; +35% (+14%) | 2004-12-01 at 2.57 | 2007-12-03 at 12.89 (3-year limit) | +459% **BIG WIN** | +20% / +76% / +245% / +471% | +82% | -4% / +546% | left the list 2025-07-23 (paid out) |
| SUL | Super Retail Group Limited | 2004-12-31 | A$350k; 3.19; +36% (+14%) | 2005-01-04 at 3.20 | 2006-07-03 at 1.60 (35% stop) | -49% **BIG LOSS** | -10% / -12% / +3% / +46% | +74% | -50% / +69% | listed; since buy +1115% |
| BNB | Babcock & Brown Limited | 2005-04-29 | A$6,408k; 8.94; +12% (+8%) | 2005-05-02 at 9.32 | 2008-02-01 at 19.46 (35% stop) | +108% **BIG WIN** | +83% / +95% / +218% / +52% | +57% | -4% / +272% | left the list 2009-01-07 (paid out) |
| AZA | Anzon Australia Limited | 2005-06-30 | A$174k; 0.74; +41% (+8%) | 2005-07-01 at 0.71 | 2007-07-02 at 1.01 (35% stop) | +39% | +59% / +80% / +45% / +82% | +36% | -2% / +163% | left the list 2008-10-17 (paid out) |
| VEI | Vision Eye Institute Limited | 2005-06-30 | A$188k; 3.98; +28% (+7%) | 2005-07-01 at 3.74 | 2007-03-01 at 2.95 (35% stop) | -23% | +31% / +14% / -24% / -52% | +36% | -57% / +35% | left the list 2015-11-09 (paid out) |
| CWY | Cleanaway Waste Management Lim | 2005-10-31 | A$1,150k; 3.90; +46% (+12%) | 2005-11-01 at 3.81 | 2008-02-01 at 7.99 (35% stop) | +108% **BIG WIN** | +154% / +113% / +188% / -13% | -4% | -13% / +276% | listed; since buy -3% |
| SEK | Seek Limited | 2005-10-31 | A$652k; 2.84; +24% (+11%) | 2005-11-01 at 2.79 | 2008-04-01 at 5.48 (35% stop) | +104% **BIG WIN** | +58% / +94% / +240% / +19% | -4% | -1% / +248% | listed; since buy +695% |
| DMP | Domino'S Pizza Enterprises Lim | 2005-11-30 | A$134k; 3.19; +40% (+17%) | 2005-12-01 at 3.10 | 2008-12-01 at 2.70 (3-year limit) | -5% | +34% / +5% / +17% / -4% | -8% | -9% / +37% | listed; since buy +1322% |
| PSH | Penrice Soda Holdings Limited | 2005-12-30 | A$211k; 2.23; +13% (+11%) | 2006-01-03 at 2.20 | 2006-08-01 at 1.35 (35% stop) | -40% **BIG LOSS** | -36% / -12% / -36% / -45% | -14% | -54% / +3% | left the list 2014-04-08 (written off) |
| AUB | Aub Group Limited | 2006-05-31 | A$135k; 3.20; +48% (+8%) | 2006-06-01 at 3.20 | 2009-06-01 at 3.99 (3-year limit) | +37% | +30% / +56% / +43% / +35% | -16% | -16% / +72% | listed; since buy +1948% |
| MLI | Mintails Limited Ordinary | 2006-06-30 | A$175k; 0.23; +21% (+7%) | 2006-07-03 at 0.25 | 2006-11-01 at 0.20 (left the list) | -21% | +20% / +236% / +28% / -83% | -14% | -92% / +260% | left the list 2015-03-16 (written off) |
| REF | Reverse Corp Limited Ordinary | 2006-06-30 | A$209k; 2.60; +41% (+9%) | 2006-07-03 at 2.60 | 2008-02-01 at 3.60 (35% stop) | +45% | +49% / +141% / -41% / -64% | -14% | -68% / +143% | left the list 2020-01-14 (written off) |
| SWW | Solverdi Worldwide Limited | 2006-06-30 | A$158k; 1.15; +14% (+10%) | 2006-07-03 at 1.13 | 2006-10-02 at 0.59 (35% stop) | -49% **BIG LOSS** | -78% / -94% / -98% / -99% | -14% | -99% / +13% | left the list 2010-03-15 (written off) |
| WTF | Wotif.Com Holdings Limited | 2006-11-30 | A$541k; 4.59; +38% (+8%) | 2006-12-01 at 4.55 | 2008-07-01 at 2.86 (35% stop) | -38% | +12% / +28% / -26% / +36% | -5% | -40% / +43% | left the list 2014-11-06 (paid out) |
| AAX | Ausenco Limited | 2006-12-29 | A$123k; 3.48; +125% (+16%) | 2007-01-02 at 3.70 | 2008-11-03 at 5.03 (35% stop) | +34% | +153% / +311% / -44% / +20% | -4% | -49% / +354% | left the list 2016-08-29 (paid out) |
| BVA | Bravura Solutions Limited | 2006-12-29 | A$340k; 2.97; +140% (+15%) | 2007-01-02 at 2.97 | 2007-06-01 at 1.83 (35% stop) | -39% | -41% / -35% / -94% / -93% | -4% | -95% / +4% | left the list 2013-09-26 (paid out) |
| DWS | Dws Advanced Business Solution | 2006-12-29 | A$149k; 1.83; +81% (+16%) | 2007-01-02 at 1.99 | 2008-03-03 at 1.70 (35% stop) | -13% | +35% / +72% / -64% / -1% | -4% | -72% / +75% | left the list 2020-12-24 (paid out) |
| SRG | Sydney Roads Group | 2007-01-31 | A$6,344k; 1.33; +29% (+16%) | 2007-02-01 at 1.32 | 2007-07-02 at 1.41 (left the list) | +7% | +7% / +7% / +7% / +7% | -9% | -2% / +17% | left the list 2007-05-11 (paid out) |
| BLG | Bluglass Limited | 2007-03-30 | A$191k; 0.80; +152% (+20%) | 2007-04-02 at 0.80 | 2007-09-03 at 0.47 (35% stop) | -42% **BIG LOSS** | -50% / -46% / -70% / -83% | -6% | -84% / +7% | listed; since buy -99% |
| KBC | Keybridge Capital Ordinary | 2007-05-31 | A$550k; 2.50; +58% (+16%) | 2007-06-01 at 2.50 | 2007-09-03 at 1.66 (35% stop) | -35% | -32% / -67% / -96% / -96% | -20% | -97% / -1% | left the list 2019-07-15 (paid out) |
| OTR | Onterran Limited | 2007-05-31 | A$217k; 2.49; +78% (+17%) | 2007-06-01 at 2.50 | 2008-03-03 at 2.00 (35% stop) | -22% | +10% / -21% / -81% / -93% | -20% | -94% / +30% | left the list 2017-02-09 (written off) |
| VEA | Veda Advantage Limited | 2007-05-31 | A$2,322k; 3.55; +25% (+15%) | 2007-06-01 at 3.56 | 2007-08-01 at 3.60 (left the list) | +1% | +1% / +1% / +1% / +1% | -20% | -0% / +1% | left the list 2007-06-25 (paid out) |
| RPX | Rp Data Ltd | 2007-06-29 | A$230k; 2.30; +53% (+13%) | 2007-07-02 at 2.30 | 2008-02-01 at 1.35 (35% stop) | -42% **BIG LOSS** | -26% / -52% / -77% / -62% | -21% | -85% / -0% | left the list 2011-04-29 (paid out) |
| OCP | Oceania Capital Partners Limit | 2007-07-31 | A$356k; 4.42; +12% (+9%) | 2007-08-01 at 4.18 | 2008-02-01 at 2.55 (35% stop) | -40% **BIG LOSS** | -37% / -59% / -43% / -63% | -13% | -67% / +3% | left the list 2019-08-30 (paid out) |
| BLY | Boart Longyear Cdi 1:1 | 2007-10-31 | A$20,124k; 2.55; +42% (+11%) | 2007-11-01 at 2.61 | 2008-10-01 at 1.17 (35% stop) | -55% **BIG LOSS** | -25% / -83% / -89% / -83% | -22% | -97% / +1% | left the list 2024-04-05 (paid out) |
| CSV | Csg Limited | 2007-10-31 | A$133k; 1.63; +31% (+10%) | 2007-11-01 at 1.64 | 2008-04-01 at 0.95 (35% stop) | -42% **BIG LOSS** | -39% / -57% / -7% / +27% | -22% | -72% / +57% | left the list 2020-02-05 (paid out) |
| MSL | The Mac Services Group Limited | 2007-10-31 | A$173k; 3.15; +53% (+10%) | 2007-11-01 at 3.20 | 2008-08-01 at 2.23 (35% stop) | -32% | -17% / -50% / -37% / +21% | -22% | -77% / +21% | left the list 2010-12-15 (paid out) |
| NWH | Nrw Holdings Limited | 2008-03-31 | A$1,345k; 2.48; +5% (-14%) | 2008-04-01 at 2.33 | 2008-11-03 at 0.73 (35% stop) | -68% **BIG LOSS** | -17% / -77% / -16% / +34% | -1% | -94% / +35% | listed; since buy +518% |
| PAG | Primeag Australia Limited | 2008-06-30 | A$574k; 1.80; +6% (-18%) | 2008-07-01 at 1.80 | 2008-11-03 at 1.31 (35% stop) | -28% | -33% / -40% / -41% / -29% | -2% | -49% / +8% | left the list 2013-10-21 (paid out) |
| CAR | Car Group Limited | 2010-03-31 | A$1,783k; 5.38; +35% (+7%) | 2010-04-01 at 5.22 | 2013-04-02 at 8.99 (3-year limit) | +71% | -11% / -1% / +6% / +80% | +15% | -20% / +82% | listed; since buy +610% |
| AZJ | Aurizon Holdings Limited | 2011-05-31 | A$25,576k; 3.45; +30% (+1%) | 2011-06-01 at 3.44 | 2014-06-02 at 4.94 (3-year limit) | +49% | -5% / -3% / +28% / +50% | +34% | -15% / +59% | listed; since buy +134% |
| MLD | Maca Limited Ordinary | 2011-05-31 | A$339k; 2.50; +74% (-0%) | 2011-06-01 at 2.44 | 2013-07-01 at 1.79 (35% stop) | -23% | -19% / -13% / -15% / +2% | +34% | -27% / +31% | left the list 2022-10-21 (paid out) |
| NXT | Nextdc Limited | 2011-06-30 | A$218k; 1.70; +7% (-3%) | 2011-07-01 at 1.70 | 2014-07-01 at 1.67 (3-year limit) | -3% | -2% / +5% / +57% / +2% | +36% | -19% / +68% | listed; since buy +478% |
| AZG | Allmine Group Limited | 2011-08-31 | A$120k; 0.20; +21% (-11%) | 2011-09-01 at 0.20 | 2011-11-01 at 0.12 (35% stop) | -46% **BIG LOSS** | -2% / -22% / -100% / -100% | +48% | -83% / +7% | left the list 2013-05-23 (written off) |
| GNG | Gr Engineering Services Limite | 2011-10-31 | A$105k; 1.90; +3% (-10%) | 2011-11-01 at 1.90 | 2012-06-01 at 1.05 (35% stop) | -45% **BIG LOSS** | -28% / -45% / -58% / -47% | +47% | -77% / +8% | listed; since buy +1046% |
| CNU | Chorus Limited | 2012-05-31 | A$440k; 2.53; +10% (-2%) | 2012-06-01 at 2.55 | 2013-12-02 at 1.28 (35% stop) | -43% **BIG LOSS** | +9% / -8% / -28% / +34% | +60% | -46% / +39% | listed; since buy +422% |
| TME | Trade Me Group Limited | 2012-06-29 | A$122k; 2.92; +32% (-2%) | 2012-07-02 at 2.93 | 2015-07-01 at 3.01 (3-year limit) | +1% | +6% / +38% / +12% / +4% | +53% | -7% / +55% | left the list 2019-05-02 (paid out) |
| XRO | Xero Limited | 2013-05-31 | A$162k; 11.75; +162% (+10%) | 2013-06-03 at 11.70 | 2014-07-01 at 23.74 (35% stop) | +99% | +159% / +148% / +64% / +39% | +26% | -1% / +261% | listed; since buy +589% |

### ASX 2013-2022 listings (re-model, not blind): 87 companies passed, 77 bought

| Code | Company | Decided | Why it qualified: traded value a day; price; return since first close (index) | Bought | Sold (reason) | Result in the book | If simply held: 6m / 12m / 24m / 36m | Fund over the same 36m | Worst / best point in 3 years | Later |
|---|---|---|---|---|---|---|---|---|---|---|
| VRT | Virtus Health Ltd Ordinary | 2013-12-31 | A$1,173k; 8.74; +41% (+13%) | 2014-01-02 at 8.74 | 2015-07-01 at 5.35 (35% stop) | -36% | -2% / -7% / -22% / -20% | +22% | -45% / +4% | left the list 2022-08-01 (paid out) |
| SDF | Steadfast Group Limited | 2014-01-31 | A$791k; 1.62; +14% (+1%) | 2014-02-03 at 1.62 | 2017-03-01 at 2.49 (3-year limit) | +67% | -19% / -7% / -4% / +52% | +24% | -21% / +64% | listed; since buy +419% |
| OFX | Ofx Group Limited | 2014-04-30 | A$1,557k; 3.05; +19% (+5%) | 2014-05-01 at 2.99 | 2016-03-01 at 1.90 (35% stop) | -34% | -13% / -24% / -25% / -48% | +23% | -54% / +23% | listed; since buy -82% |
| AFJ | Affinity Education Group Limit | 2014-06-30 | A$292k; 1.25; +20% (+5%) | 2014-07-01 at 1.22 | 2015-07-01 at 0.82 (35% stop) | -34% | -2% / -36% / -25% / -25% | +21% | -56% / +21% | left the list 2015-12-01 (paid out) |
| CVO | Cover-More Group Limited | 2014-06-30 | A$1,420k; 1.88; +6% (+4%) | 2014-07-01 at 1.90 | 2016-03-01 at 1.47 (35% stop) | -23% | +1% / +25% / -37% / +2% | +21% | -38% / +32% | left the list 2017-04-03 (paid out) |
| LHC | Lifehealthcare Group Limited | 2014-06-30 | A$111k; 2.26; +12% (+4%) | 2014-07-01 at 2.30 | 2016-03-01 at 1.44 (35% stop) | -39% | -10% / +42% / -28% / -4% | +21% | -43% / +63% | left the list 2018-05-11 (paid out) |
| NEC | Nine Entertainment Co. Holding | 2014-06-30 | A$5,533k; 2.16; +9% (+4%) | 2014-07-01 at 2.09 | 2016-05-02 at 1.17 (35% stop) | -37% | -10% / -25% / -44% / -19% | +21% | -52% / +16% | listed; since buy +25% |
| VED | Veda Group Limited | 2014-06-30 | A$1,564k; 1.98; +13% (+4%) | 2014-07-01 at 2.00 | 2016-04-01 at 2.82 (left the list) | +41% | +13% / +10% / +41% / +41% | +21% | -7% / +41% | left the list 2016-02-11 (paid out) |
| VET | Vocation Limited | 2014-06-30 | A$1,206k; 3.05; +50% (+5%) | 2014-07-01 at 3.02 | 2014-11-03 at 0.81 (35% stop) | -73% **BIG LOSS** | -94% / -97% / -100% / -100% | +21% | -98% / +11% | left the list 2015-11-11 (written off) |
| SGF | Sg Fleet Group Ltd Deferred Se | 2014-09-30 | A$315k; 1.83; +14% (-2%) | 2014-10-01 at 1.83 | 2017-11-01 at 4.16 (3-year limit) | +176% **BIG WIN** | +40% / +81% / +153% / +166% | +22% | +0% / +199% | left the list 2025-05-15 (paid out) |
| BAP | Bapcor Limited | 2014-10-31 | A$413k; 2.47; +20% (-0%) | 2014-11-03 at 2.47 | 2017-12-01 at 5.72 (3-year limit) | +141% **BIG WIN** | +36% / +48% / +116% / +137% | +23% | -7% / +170% | listed; since buy -55% |
| SPO | Spotless Group Holdings Limite | 2014-11-28 | A$2,700k; 1.95; +13% (-3%) | 2014-12-01 at 1.89 | 2016-01-04 at 1.10 (35% stop) | -43% **BIG LOSS** | +11% / +15% / -52% / -40% | +31% | -62% / +30% | left the list 2019-08-27 (paid out) |
| AHY | Asaleo Care Limited Ordinary | 2014-12-31 | A$2,545k; 1.66; +1% (-1%) | 2015-01-02 at 1.69 | 2016-08-01 at 1.39 (35% stop) | -11% | +16% / -1% / +2% / +6% | +27% | -17% / +48% | left the list 2021-06-10 (paid out) |
| MTR | Mantra Group Limited | 2014-12-31 | A$250k; 2.90; +63% (-0%) | 2015-01-02 at 2.85 | 2016-09-01 at 3.00 (35% stop) | +4% | +24% / +78% / +6% / +37% | +27% | -9% / +78% | left the list 2018-05-23 (paid out) |
| SIQ | Smartgroup Corporation Ltd | 2014-12-31 | A$132k; 1.47; +1% (-1%) | 2015-01-02 at 1.47 | 2018-02-01 at 11.04 (3-year limit) | +749% **BIG WIN** | +62% / +276% / +376% / +772% | +27% | -3% / +793% | listed; since buy +1378% |
| HSO | Healthscope Limited. | 2015-01-30 | A$10,406k; 2.70; +22% (+0%) | 2015-02-02 at 2.67 | 2017-09-01 at 1.75 (35% stop) | -35% | +3% / -17% / -15% / -27% | +24% | -39% / +18% | left the list 2019-05-24 (paid out) |
| BAL | Bellamy'S Australia Limited | 2015-02-27 | A$294k; 2.24; +72% (+7%) | 2015-03-02 at 2.28 | 2017-01-03 at 6.68 (35% stop) | +191% **BIG WIN** | +157% / +408% / +89% / +703% | +13% | +0% / +706% | left the list 2019-12-10 (paid out) |
| REG | Regis Healthcare Limited | 2015-04-30 | A$1,851k; 5.60; +39% (+10%) | 2015-05-01 at 5.58 | 2017-09-01 at 3.35 (35% stop) | -33% | +5% / -4% / -15% / -19% | +19% | -34% / +14% | listed; since buy +42% |
| APO | Apn Outdoor Group Limited | 2015-05-29 | A$356k; 3.20; +21% (+5%) | 2015-06-01 at 3.23 | 2016-11-07 at 4.63 (35% stop) | +42% | +68% / +113% / +44% / +76% | +19% | -7% / +155% | left the list 2018-10-18 (paid out) |
| IPH | Iph Limited | 2015-05-29 | A$825k; 4.90; +59% (+8%) | 2015-06-01 at 5.00 | 2016-09-01 at 5.56 (35% stop) | +16% | +61% / +42% / +5% / +0% | +19% | -26% / +90% | listed; since buy +40% |
| SRF | Surfstitch Group Limited | 2015-06-30 | A$175k; 1.83; +83% (+6%) | 2015-07-01 at 1.83 | 2016-03-01 at 1.18 (35% stop) | -37% | +3% / -90% / -100% / -100% | +28% | -96% / +15% | left the list 2017-05-23 (written off) |
| OML | Ooh!Media Limited | 2015-06-30 | A$177k; 2.57; +35% (+6%) | 2015-07-01 at 2.55 | 2018-08-01 at 4.85 (3-year limit) | +104% **BIG WIN** | +89% / +97% / +66% / +104% | +28% | -5% / +135% | listed; since buy +26% |
| LOV | Lovisa Holdings Limited | 2015-06-30 | A$336k; 3.40; +63% (+5%) | 2015-07-01 at 3.35 | 2016-02-01 at 2.19 (35% stop) | -35% | +10% / -29% / +24% / +261% | +28% | -40% / +315% | listed; since buy +1069% |
| EHE | Estia Health Ltd Ordinary | 2015-06-30 | A$3,420k; 6.00; +27% (+2%) | 2015-07-01 at 6.06 | 2016-07-01 at 4.65 (35% stop) | -20% | +21% / -20% / -45% / -38% | +28% | -57% / +31% | left the list 2023-12-06 (paid out) |
| A2M | The A2 Milk Company Limited | 2015-09-30 | A$396k; 0.64; +13% (-15%) | 2015-10-01 at 0.64 | 2018-11-01 at 10.00 (3-year limit) | +1447% **BIG WIN** | +169% / +170% / +933% / +1391% | +37% | +2% / +1958% | listed; since buy +1146% |
| TCH | Touchcorp Limited | 2015-09-30 | A$132k; 1.70; +10% (-15%) | 2015-10-01 at 1.70 | 2017-01-03 at 1.05 (35% stop) | -39% | +19% / +21% / -2% / -2% | +37% | -42% / +59% | left the list 2017-06-28 (paid out) |
| FPR | Fleetpartners Group Limited | 2015-10-30 | A$595k; 3.54; +27% (-10%) | not filled (no place free or no trade) | | | -16% / +8% / +25% / -29% | +28% | -44% / +30% | |
| SLC | Superloop Limited | 2015-11-30 | A$115k; 2.05; +1% (-6%) | not filled (no place free or no trade) | | | +20% / +23% / +13% / -16% | +23% | -20% / +60% | |
| QMS | Qms Media Limited | 2015-12-31 | A$161k; 1.32; +86% (-2%) | not filled (no place free or no trade) | | | -5% / -15% / -25% / -37% | +22% | -39% / +6% | |
| AYS | Amaysim Aus Ltd Ordinary | 2016-01-29 | A$402k; 3.14; +65% (-11%) | not filled (no place free or no trade) | | | -41% / -38% / -28% / -69% | +33% | -76% / +0% | |
| CGC | Costa Group Holdings Deferred  | 2016-01-29 | A$1,759k; 2.46; +14% (-10%) | not filled (no place free or no trade) | | | +15% / +35% / +146% / +123% | +33% | -6% / +272% | |
| RFN | Reffind Limited Ordinary | 2016-01-29 | A$553k; 0.63; +142% (-9%) | not filled (no place free or no trade) | | | -85% / -94% / -96% / -99% | +33% | -99% / +2% | |
| BFC | Beston Global Ltd Ordinary | 2016-02-29 | A$363k; 0.43; +35% (-7%) | 2016-03-01 at 0.42 | 2017-02-01 at 0.31 (35% stop) | -29% | -1% / -32% / -47% / -64% | +43% | -73% / +17% | left the list 2025-08-29 (paid out) |
| LNK | Link Admin Hldg Defferred Sett | 2016-04-29 | A$4,205k; 8.00; +13% (-2%) | 2016-05-02 at 8.14 | 2019-06-03 at 5.57 (3-year limit) | -24% | -9% / -2% / +8% / +5% | +36% | -13% / +15% | left the list 2024-05-01 (paid out) |
| BBN | Baby Bunting Group Limited | 2016-04-29 | A$502k; 2.40; +31% (+1%) | 2016-05-02 at 2.42 | 2017-05-01 at 1.81 (35% stop) | -24% | +17% / -14% / -39% / +7% | +36% | -44% / +31% | listed; since buy -33% |
| BWX | Bwx Limited Ordinary | 2016-05-31 | A$1,112k; 4.55; +101% (+5%) | not filled (no place free or no trade) | | | -12% / +22% / +37% / -62% | +36% | -69% / +84% | |
| IEL | Idp Education Limited | 2016-05-31 | A$1,468k; 4.50; +32% (+3%) | 2016-06-01 at 4.59 | 2019-07-01 at 18.11 (3-year limit) | +317% **BIG WIN** | -10% / +1% / +122% / +277% | +36% | -17% / +297% | listed; since buy -32% |
| CL1 | Class Limited Ordinary | 2016-06-30 | A$398k; 3.30; +136% (+2%) | not filled (no place free or no trade) | | | -14% / -6% / -30% / -52% | +47% | -60% / +25% | |
| IGL | Ive Group Limited | 2016-06-30 | A$129k; 2.20; +11% (+4%) | not filled (no place free or no trade) | | | -0% / +6% / +17% / +16% | +47% | -5% / +25% | |
| AFY | Afterpay Holdings Limited | 2016-10-28 | A$195k; 2.50; +100% (+0%) | 2016-11-07 at 2.32 | 2017-08-01 at 2.74 (left the list) | +17% | +8% / +18% / +18% / +18% | +45% | -15% / +31% | left the list 2017-06-28 (paid out) |
| MTO | Motorcycle Holdings Limited | 2016-10-28 | A$122k; 4.22; +56% (+1%) | 2016-11-07 at 3.80 | 2018-05-01 at 3.15 (35% stop) | -15% | +0% / +39% / -32% / -35% | +45% | -71% / +42% | listed; since buy +23% |
| WTC | Wisetech Global Limited | 2016-10-28 | A$688k; 6.01; +54% (+7%) | 2016-11-07 at 5.92 | 2018-04-03 at 9.39 (35% stop) | +58% | +16% / +107% / +161% / +354% | +45% | -19% / +553% | listed; since buy +720% |
| GTN | Gtn Limited | 2016-12-30 | A$120k; 2.72; +28% (+6%) | 2017-01-03 at 2.69 | 2018-04-03 at 1.72 (35% stop) | -36% | -9% / +7% / -58% / -64% | +35% | -72% / +15% | listed; since buy -81% |
| NOX | Noxopharm Limited | 2017-02-28 | A$106k; 0.49; +165% (+3%) | 2017-03-01 at 0.47 | 2018-05-01 at 0.77 (35% stop) | +58% | -28% / +191% / -9% / -49% | +33% | -55% / +233% | listed; since buy -92% |
| A3D | Aurora Labs Limited | 2017-02-28 | A$149k; 2.80; +460% (+3%) | 2017-03-01 at 2.58 | 2017-05-01 at 1.38 (35% stop) | -48% **BIG LOSS** | -75% / -69% / -83% / -92% | +33% | -95% / +8% | listed; since buy -98% |
| FIG | Freedom Insurance Ordinary | 2017-06-30 | A$160k; 0.92; +145% (+4%) | 2017-07-03 at 0.90 | 2017-12-01 at 0.50 (35% stop) | -46% **BIG LOSS** | -48% / -51% / -100% / -100% | +16% | -98% / +2% | left the list 2019-02-04 (written off) |
| WHA | Wattle Health Au Ltd Ordinary | 2017-09-29 | A$155k; 0.92; +360% (-2%) | 2017-10-02 at 0.94 | 2018-06-01 at 1.47 (35% stop) | +53% | +120% / +15% / -100% / -100% | +17% | -61% / +198% | left the list 2019-09-27 (written off) |
| BIN | Bingo Industries Ltd Deferred  | 2017-10-31 | A$953k; 2.03; +15% (+0%) | 2017-11-01 at 2.05 | 2019-01-02 at 1.83 (35% stop) | -11% | +40% / +18% / +20% / +30% | +15% | -42% / +61% | left the list 2021-07-15 (paid out) |
| CAN | Cann Group Ltd Ordinary | 2017-10-31 | A$183k; 1.75; +171% (+1%) | 2017-11-01 at 1.85 | 2019-01-02 at 2.00 (35% stop) | +5% | +93% / +35% / -45% / -82% | +15% | -82% / +117% | left the list 2024-02-29 (written off) |
| MAF | Ma Financial Group Limited | 2017-10-31 | A$126k; 5.90; +87% (-0%) | 2017-11-01 at 5.94 | 2019-04-01 at 4.25 (35% stop) | -30% | +0% / -15% / -28% / -33% | +15% | -79% / +16% | listed; since buy -7% |
| PL8 | Plato Income Maximiser Limited | 2017-10-31 | A$305k; 1.10; +2% (+1%) | 2017-11-01 at 1.09 | 2020-11-02 at 1.07 (3-year limit) | +17% | -3% / -4% / +24% / +19% | +15% | -14% / +28% | listed; since buy +108% |
| APT | Afterpay Touch Group Limited | 2017-12-29 | A$2,777k; 5.97; +121% (+4%) | 2018-01-02 at 6.26 | 2020-04-01 at 20.66 (35% stop) | +228% **BIG WIN** | +58% / +98% / +381% / +1752% | +24% | -15% / +1822% | left the list 2022-01-19 (written off) |
| ELS | Elsight Limited | 2017-12-29 | A$136k; 1.47; +914% (+7%) | not filled (no place free or no trade) | | | -61% / -53% / -75% / -72% | +24% | -84% / +1% | |
| TTT | Titomic Limited | 2018-03-29 | A$524k; 1.34; +198% (+2%) | 2018-04-03 at 1.31 | 2018-10-01 at 1.62 (35% stop) | +22% | +27% / +63% / -59% / -60% | +33% | -65% / +129% | listed; since buy -94% |
| PPE | Peoplein Limited | 2018-05-31 | A$103k; 1.60; +23% (+0%) | 2018-06-01 at 1.62 | 2020-04-01 at 1.30 (35% stop) | -17% | +27% / +77% / +39% / +213% | +32% | -38% / +213% | listed; since buy -67% |
| NWL | Netwealth Group Limited | 2018-05-31 | A$1,573k; 9.05; +70% (+1%) | 2018-06-01 at 8.87 | 2021-06-01 at 14.68 (3-year limit) | +72% | -11% / +9% / -5% / +69% | +32% | -38% / +117% | listed; since buy +145% |
| WGN | Wagners Holding Company Limite | 2018-06-29 | A$632k; 4.35; +28% (+3%) | 2018-07-02 at 4.33 | 2019-02-01 at 2.67 (35% stop) | -39% | -22% / -59% / -76% / -49% | +33% | -86% / +12% | listed; since buy +11% |
| CPV | Clearvue Technologies Limited | 2018-11-30 | A$169k; 0.28; +36% (-6%) | 2018-12-03 at 0.32 | 2019-05-01 at 0.22 (35% stop) | -33% | -28% / -40% / -12% / -25% | +41% | -85% / +175% | listed; since buy -80% |
| HLF | Keytone Dairy Ordinary | 2019-01-31 | A$275k; 0.46; +26% (-6%) | 2019-02-01 at 0.44 | 2020-03-02 at 0.31 (35% stop) | -32% | +5% / -10% / -47% / -75% | +30% | -75% / +36% | left the list 2023-08-23 (written off) |
| AMS | Atomos Ordinary | 2019-07-31 | A$129k; 1.38; +175% (+20%) | 2019-08-01 at 1.34 | 2020-03-02 at 0.82 (35% stop) | -39% | +7% / -65% / -16% / -76% | +12% | -86% / +35% | left the list 2023-02-27 (written off) |
| SPT | Splitit Ordinary | 2019-07-31 | A$2,896k; 0.56; +47% (+16%) | 2019-08-01 at 0.57 | 2020-02-03 at 0.57 (35% stop) | -1% | +20% / +147% / -13% / -54% | +12% | -81% / +226% | left the list 2023-12-08 (written off) |
| UWL | Uniti Wireless Limited | 2019-08-30 | A$955k; 1.28; +495% (+9%) | 2019-09-02 at 1.35 | 2022-09-01 at 4.99 (left the list) | +269% **BIG WIN** | -6% / +5% / +209% / +271% | +19% | -40% / +271% | left the list 2022-07-21 (paid out) |
| EOF | Ecofibre Limited Ordinary | 2019-09-30 | A$564k; 3.04; +79% (+8%) | 2019-10-01 at 3.04 | 2020-04-01 at 1.78 (35% stop) | -42% **BIG LOSS** | -41% / -18% / -72% / -92% | +7% | -94% / +25% | left the list 2025-08-29 (written off) |
| NXS | Next Science Limited Ordinary | 2019-10-31 | A$902k; 2.45; +81% (+6%) | 2019-11-01 at 2.15 | 2020-04-01 at 1.23 (35% stop) | -44% **BIG LOSS** | -23% / -47% / -40% / -67% | +14% | -67% / +25% | left the list 2026-02-11 (paid out) |
| RPL | Regal Partners Limited | 2019-12-31 | A$181k; 13.00; +29% (+1%) | 2020-01-02 at 13.00 | 2020-07-01 at 7.70 (35% stop) | -42% **BIG LOSS** | -42% / -33% / -64% / -67% | +18% | -76% / -0% | listed; since buy -76% |
| PBH | Pointsbet Holdings Limited | 2019-12-31 | A$1,385k; 4.79; +114% (+2%) | 2020-01-02 at 4.90 | 2020-04-01 at 2.63 (35% stop) | -47% **BIG LOSS** | +19% / +142% / +48% / -71% | +18% | -76% / +260% | listed; since buy -6% |
| FCL | Fineos Corporation Holdings Pl | 2020-02-28 | A$293k; 3.72; +38% (+1%) | 2020-03-02 at 3.60 | 2022-03-01 at 3.15 (35% stop) | -14% | +46% / +4% / -8% / -63% | +26% | -66% / +57% | listed; since buy -40% |
| OPC | Opticomm Ltd Ordinary | 2020-02-28 | A$225k; 4.78; +55% (-1%) | 2020-03-02 at 4.85 | 2021-01-04 at 6.71 (left the list) | +37% | +6% / +38% / +38% / +38% | +26% | -28% / +39% | left the list 2020-11-13 (paid out) |
| OPY | Openpay Group Ordinary | 2020-06-30 | A$320k; 2.10; +58% (-14%) | 2020-07-01 at 2.28 | 2020-10-01 at 2.90 (35% stop) | +26% | +2% / -36% / -93% / -100% | +36% | -95% / +106% | left the list 2023-01-31 (written off) |
| TYR | Tyro Payments Limited | 2020-06-30 | A$5,382k; 3.50; +4% (-12%) | 2020-07-01 at 3.57 | 2022-02-01 at 2.27 (35% stop) | -37% | -13% / -1% / -78% / -69% | +36% | -83% / +20% | listed; since buy -80% |
| AL3 | Aml3D Limited | 2020-10-30 | A$178k; 0.43; +187% (+11%) | 2020-11-02 at 0.39 | 2021-05-03 at 0.23 (35% stop) | -41% **BIG LOSS** | -37% / -61% / -78% / -82% | +28% | -88% / +21% | listed; since buy -74% |
| ASM | Ausstratmaterials Ordinary | 2021-01-29 | A$1,749k; 5.00; +257% (+9%) | 2021-02-01 at 4.85 | 2022-02-01 at 8.79 (35% stop) | +80% | +79% / +71% / -61% / -79% | +29% | -80% / +191% | left the list 2026-09-03 (written off) |
| ABB | Aussie Broadband Limited | 2021-04-30 | A$1,052k; 3.06; +60% (+14%) | 2021-05-03 at 3.02 | 2022-07-01 at 3.28 (35% stop) | +8% | +52% / +32% / +6% / +23% | +23% | -35% / +97% | listed; since buy +55% |
| CCR | Credit Clear Limited | 2021-04-30 | A$225k; 0.66; +43% (+16%) | 2021-05-03 at 0.68 | 2022-01-04 at 0.41 (35% stop) | -40% **BIG LOSS** | -25% / -31% / -65% / -65% | +23% | -75% / +1% | listed; since buy -78% |
| UNI | Universal Store Holdings Limit | 2021-05-31 | A$233k; 7.90; +77% (+10%) | 2021-06-01 at 7.75 | 2022-06-01 at 4.44 (35% stop) | -42% **BIG LOSS** | +1% / -41% / -60% / -28% | +21% | -65% / +9% | listed; since buy +25% |
| DSK | Dusk Group Limited | 2021-05-31 | A$557k; 3.85; +140% (+20%) | 2021-06-01 at 3.90 | 2022-06-01 at 1.95 (35% stop) | -47% **BIG LOSS** | -22% / -45% / -67% / -78% | +21% | -78% / +3% | listed; since buy -71% |
| CTT | Cettire Limited | 2021-06-30 | A$1,387k; 2.64; +428% (+10%) | 2021-07-01 at 2.77 | 2022-03-01 at 2.19 (35% stop) | -22% | +30% / -86% / +12% / -58% | +21% | -87% / +75% | listed; since buy -89% |
| MGH | Maas Group Holdings Limited | 2021-06-30 | A$418k; 5.60; +108% (+10%) | 2021-07-01 at 5.60 | 2022-10-03 at 3.09 (35% stop) | -45% **BIG LOSS** | -10% / -34% / -51% / -21% | +21% | -59% / +1% | listed; since buy -25% |
| CHM | Chimeric Therapeutics Limited | 2021-07-30 | A$278k; 0.33; +12% (+11%) | 2021-08-02 at 0.34 | 2022-02-01 at 0.23 (35% stop) | -33% | -37% / -61% / -88% / -94% | +20% | -95% / +4% | listed; since buy -100% |
| DDH | Ddh Drill Ordinary | 2021-09-30 | A$260k; 1.24; +45% (+8%) | 2021-10-01 at 1.25 | 2022-07-01 at 0.74 (35% stop) | -40% **BIG LOSS** | -16% / -39% / -24% / -24% | +30% | -49% / -0% | left the list 2023-09-27 (paid out) |
| ACL | Australian Clinical Labs Limit | 2021-11-30 | A$1,742k; 4.25; +24% (+3%) | 2021-12-01 at 4.30 | 2022-10-03 at 3.49 (35% stop) | -10% | +14% / -12% / -28% / -1% | +31% | -40% / +44% | listed; since buy +5% |
| DGL | Dgl Group Limited | 2021-11-30 | A$581k; 2.45; +128% (+3%) | 2021-12-01 at 2.35 | 2022-08-01 at 2.52 (35% stop) | +6% | +19% / -37% / -65% / -76% | +31% | -81% / +77% | listed; since buy -88% |
| CHL | Camplify Holdings Limited | 2021-12-31 | A$185k; 4.44; +217% (+2%) | 2022-01-04 at 4.12 | 2022-04-01 at 2.35 (35% stop) | -44% **BIG LOSS** | -48% / -58% / -45% / -83% | +21% | -83% / -2% | listed; since buy -88% |
| PXA | Pexa Group Limited | 2021-12-31 | A$2,560k; 19.90; +16% (+2%) | 2022-01-04 at 20.35 | 2023-01-03 at 11.72 (35% stop) | -43% **BIG LOSS** | -28% / -41% / -47% / -36% | +21% | -50% / -1% | listed; since buy -65% |
| VSL | Vulcan Steel Limited | 2022-05-31 | A$553k; 8.43; +22% (-3%) | 2022-06-01 at 8.50 | 2025-06-02 at 6.56 (3-year limit) | -13% | -0% / -4% / -7% / -14% | +30% | -17% / +15% | listed; since buy -21% |
| VNT | Ventia Services Group Limited | 2022-05-31 | A$1,237k; 2.56; +23% (-3%) | 2022-06-01 at 2.61 | 2025-06-02 at 4.75 (3-year limit) | +113% **BIG WIN** | +5% / +10% / +51% / +113% | +30% | -12% / +116% | listed; since buy +143% |
| THL | Tourism Holdings Limited | 2023-06-30 | A$222k; 3.52; +0% (-1%) | 2023-07-03 at 3.59 | 2024-06-03 at 1.79 (35% stop) | -48% **BIG LOSS** | +3% / -51% / -39% / -29% | +34% | -63% / +7% | listed; since buy -26% |

### ASX 2023-2025 listings (unseen): 6 companies passed, 6 bought

| Code | Company | Decided | Why it qualified: traded value a day; price; return since first close (index) | Bought | Sold (reason) | Result in the book | If simply held: 6m / 12m / 24m / 36m | Fund over the same 36m | Worst / best point in 3 years | Later |
|---|---|---|---|---|---|---|---|---|---|---|
| LNW | Light & Wonder, Inc. | 2023-11-30 | A$6,403k; 130.68; +44% (-1%) | 2023-12-01 at 133.79 | 2025-11-03 at 112.03 (35% stop) | -17% | +8% / +12% / +14% /  |  | -23% / +36% | listed; since buy -10% |
| TEA | Tasmea Limited | 2024-10-31 | A$360k; 2.92; +78% (+6%) | 2024-11-01 at 2.90 | 2026-11-13 at 9.75 (still held 13 Nov 2026) | +270% **BIG WIN** | -8% / +87% / +263% /  |  | -22% / +334% | listed; since buy +284% |
| GYG | Guzman Y Gomez Ltd Ordinary | 2024-12-31 | A$5,164k; 40.57; +35% (+5%) | 2025-01-02 at 39.90 | 2025-09-01 at 25.50 (35% stop) | -36% | -30% / -45% /  /  |  | -62% / +14% | listed; since buy -29% |
| AAI | Alcoa Corporation Cdi 1:1 For. | 2025-01-31 | A$8,853k; 57.01; +11% (+7%) | 2025-02-03 at 54.60 | 2026-08-03 at 65.19 (35% stop) | +20% | -17% / +51% /  /  |  | -33% / +117% | listed; since buy +9% |
| CCL | Cuscal Limited Ordinary | 2025-05-30 | A$563k; 2.94; +27% (+0%) | 2025-06-02 at 2.94 | 2026-11-13 at 5.72 (still held 13 Nov 2026) | +100% **BIG WIN** | +35% / +68% /  /  |  | -4% / +131% | listed; since buy +100% |
| VGN | Virgin Australia Ordinary | 2025-12-31 | A$4,229k; 3.50; +8% (+2%) | 2026-01-02 at 3.48 | 2026-05-01 at 2.16 (35% stop) | -38% | -13% /  /  /  |  | -38% / -0% | listed; since buy -18% |

### Canada 2018+ listings (unseen): 37 companies passed, 37 bought

| Code | Company | Decided | Why it qualified: traded value a day; price; return since first close (index) | Bought | Sold (reason) | Result in the book | If simply held: 6m / 12m / 24m / 36m | Fund over the same 36m | Worst / best point in 3 years | Later |
|---|---|---|---|---|---|---|---|---|---|---|
| NTR | Nutrien Ltd | 2018-07-31 | C$54,148k; 70.65; +4% (+1%) | 2018-08-01 at 71.00 | 2020-07-02 at 44.10 (35% stop) | -33% | -2% / +3% / -28% / +18% | +37% | -46% / +24% | listed; since buy +80% |
| DAY | Dayforce Inc. | 2018-10-31 | C$109k; 50.03; +23% (-4%) | 2018-11-01 at 50.64 | 2021-12-01 at 134.67 (3-year limit) | +161% **BIG WIN** | +33% / +30% / +138% / +203% | +55% | -14% / +219% | left the list 2026-02-05 (paid out) |
| KHRN | Khiron Life Sciences Corp | 2018-11-30 | C$559k; 1.48; +25% (-6%) | 2018-12-03 at 1.43 | 2019-06-03 at 2.58 (35% stop) | +79% | +87% / -31% / -72% / -85% | +52% | -87% / +187% | left the list 2024-03-26 (written off) |
| XTRA | Xtract One Technologies Inc. | 2019-01-31 | C$1,594k; 2.10; +52% (-6%) | 2019-02-01 at 2.13 | 2019-10-01 at 1.44 (35% stop) | -33% | -6% / -30% / -72% / -78% | +48% | -84% / +31% | listed; since buy -83% |
| EBM | Eastwood Bio-Medical Canada In | 2019-02-28 | C$94k; 5.40; +116% (-2%) | 2019-03-01 at 5.20 | 2019-06-03 at 3.20 (35% stop) | -41% **BIG LOSS** | -43% / -67% / -61% / -68% | +43% | -85% / +10% | listed; since buy -68% |
| ACI | Trisummit Utilities Inc | 2019-04-30 | C$608k; 19.29; +37% (+11%) | 2019-05-01 at 19.36 | 2020-06-01 at 33.49 (left the list) | +78% | +77% / +80% / +80% / +80% | +35% | -0% / +80% | left the list 2020-04-16 (paid out) |
| LSPD | Lightspeed Commerce Inc | 2019-09-30 | C$6,759k; 30.64; +62% (+4%) | 2019-10-01 at 30.22 | 2020-04-01 at 15.76 (35% stop) | -48% **BIG LOSS** | -48% / +43% / +276% / -12% | +26% | -60% / +426% | listed; since buy -54% |
| CPX-PK | Capital Power Corp | 2019-11-29 | C$191k; 25.45; +4% (+4%) | 2019-12-02 at 25.55 | 2023-01-03 at 25.00 (3-year limit) | +15% | -7% / +6% / +15% / +17% | +27% | -31% / +21% | left the list 2024-07-02 (paid out) |
| AND | Andlauer Healthcare Gr | 2020-06-30 | C$525k; 36.71; +88% (-8%) | 2020-07-02 at 39.28 | 2023-08-01 at 42.29 (3-year limit) | +8% | +2% / -5% / +19% / +16% | +37% | -15% / +43% | left the list 2025-11-04 (paid out) |
| BIPC | Brookfield Infrastructure Corp | 2020-09-30 | C$6,586k; 73.80; +55% (+20%) | 2020-10-01 at 73.43 | 2023-11-01 at 39.41 (3-year limit) | -12% | +32% / +5% / +24% / +2% | +28% | -2% / +43% | listed; since buy +54% |
| GFL | Gfl Environmental Holdings Inc | 2020-09-30 | C$2,111k; 28.31; +27% (-2%) | 2020-10-01 at 29.07 | 2023-11-01 at 40.08 (3-year limit) | +38% | +54% / +60% / +28% / +54% | +28% | -12% / +82% | listed; since buy +106% |
| DOC | Cloudmd Software & Services In | 2020-12-31 | C$3,434k; 2.38; +222% (+12%) | 2021-01-04 at 2.37 | 2021-10-01 at 1.47 (35% stop) | -39% | -2% / -53% / -92% / -96% | +29% | -97% / +32% | left the list 2024-07-10 (written off) |
| BEPC | Brookfield Renewable Corp | 2021-01-29 | C$15,095k; 71.69; +88% (+8%) | 2021-02-01 at 72.25 | 2022-02-01 at 43.02 (35% stop) | -39% | -26% / -39% / -40% / -44% | +28% | -54% / +0% | listed; since buy -22% |
| DND | Dye & Durham Ltd | 2021-01-29 | C$4,498k; 40.50; +174% (+8%) | 2021-02-01 at 43.50 | 2022-03-01 at 29.14 (35% stop) | -33% | +8% / -28% / -49% / -69% | +28% | -82% / +21% | listed; since buy -98% |
| NVEI | Nuvei Corp | 2021-03-31 | C$6,484k; 75.70; +68% (+15%) | 2021-04-01 at 78.09 | 2022-01-04 at 81.09 (35% stop) | +3% | +98% / +24% / -29% / -43% | +27% | -76% / +124% | left the list 2024-11-18 (paid out) |
| ODV | Osisko Development Corp | 2021-06-30 | C$132k; 21.00; +180% (+16%) | 2021-07-02 at 20.34 | 2022-01-04 at 12.63 (35% stop) | -39% | -38% / -69% / -71% / -86% | +18% | -89% / -0% | left the list 2026-07-27 (written off) |
| BNXA | Banxa Holdings Inc | 2021-07-30 | C$498k; 3.04; +58% (+14%) | 2021-08-03 at 3.00 | 2022-06-01 at 1.72 (35% stop) | -44% **BIG LOSS** | -12% / -63% / -71% / -84% | +16% | -85% / +44% | left the list 2026-01-05 (paid out) |
| TOI | Topicus.Com Inc | 2021-08-31 | C$3,853k; 128.03; +102% (+15%) | 2021-09-01 at 124.84 | 2022-03-01 at 85.70 (35% stop) | -32% | -34% / -44% / -18% / +8% | +19% | -49% / +14% | listed; since buy -19% |
| NHHH | Fuelpositive Corp | 2021-08-31 | C$131k; 0.19; +39% (+14%) | 2021-09-01 at 0.18 | 2022-10-03 at 0.14 (35% stop) | -28% | -17% / -11% / -67% / -75% | +19% | -83% / +64% | listed; since buy -67% |
| NDA | Neptune Digital Assets Corp | 2021-08-31 | C$466k; 0.55; +96% (+12%) | 2021-09-01 at 0.58 | 2022-03-01 at 0.41 (35% stop) | -30% | -34% / -59% / -59% / -59% | +19% | -77% / +40% | listed; since buy -41% |
| PAY | Payfare Inc | 2021-09-30 | C$1,099k; 10.75; +79% (+6%) | 2021-10-01 at 10.42 | 2022-02-01 at 6.70 (35% stop) | -37% | -29% / -46% / -51% / -78% | +29% | -81% / +1% | left the list 2025-03-04 (written off) |
| JK | Just Kitchen Holdings Corp | 2021-10-29 | C$110k; 1.43; +35% (+9%) | 2021-11-01 at 1.45 | 2022-04-01 at 0.76 (35% stop) | -49% **BIG LOSS** | -66% / -90% / -96% / -94% | +24% | -97% / +6% | left the list 2024-01-30 (paid out) |
| MAGT | Magnet Forensics Inc | 2021-10-29 | C$1,265k; 38.50; +68% (+9%) | 2021-11-01 at 39.40 | 2022-02-01 at 25.03 (35% stop) | -37% | -41% / -38% / +12% / +12% | +24% | -61% / +14% | left the list 2023-04-11 (paid out) |
| DNTL | Dentalcorp Holdings Ltd | 2021-11-30 | C$1,019k; 16.41; +16% (+6%) | 2021-12-01 at 16.32 | 2022-09-01 at 10.45 (35% stop) | -37% | -24% / -48% / -65% / -45% | +36% | -67% / +4% | left the list 2026-01-16 (paid out) |
| NBLY | Neighbourly Pharmacy Inc | 2021-11-30 | C$309k; 34.07; +52% (+6%) | 2021-12-01 at 34.41 | 2022-05-02 at 25.70 (35% stop) | -26% | -27% / -28% / -48% / -45% | +36% | -64% / +16% | left the list 2024-03-21 (paid out) |
| BAMR | Brookfield Asset Management Re | 2021-12-31 | C$2,378k; 79.44; +13% (+5%) | 2022-01-04 at 80.81 | 2023-01-03 at 43.53 (35% stop) | -41% **BIG LOSS** | -27% / -40% / -33% / -33% | +29% | -42% / -3% | left the list 2023-02-14 (paid out) |
| FORA | Verticalscope Holdings Inc | 2021-12-31 | C$193k; 30.52; +33% (+5%) | 2022-01-04 at 29.30 | 2022-06-01 at 17.71 (35% stop) | -41% **BIG LOSS** | -59% / -77% / -85% / -66% | +29% | -90% / -0% | listed; since buy -93% |
| ANRG | Anaergia Inc | 2021-12-31 | C$870k; 20.20; +45% (+6%) | 2022-01-04 at 19.40 | 2022-03-01 at 11.78 (35% stop) | -40% **BIG LOSS** | -65% / -76% / -99% / -95% | +29% | -99% / -2% | listed; since buy -91% |
| BNT | Brookfield Wealth Solutions Lt | 2021-12-31 | C$2,378k; 119.16; +13% (+5%) | 2022-01-04 at 121.22 | 2023-01-03 at 65.30 (35% stop) | -41% **BIG LOSS** | -27% / -40% / -28% / +17% | +29% | -46% / +20% | listed; since buy -20% |
| FHYD | First Hydrogen Corp | 2022-04-29 | C$116k; 3.10; +114% (+4%) | 2022-05-02 at 3.15 | 2023-03-01 at 3.27 (35% stop) | +1% | +16% / -5% / -69% / -84% | +32% | -90% / +67% | listed; since buy -93% |
| DFY | Definity Financial Corp | 2022-05-31 | C$4,293k; 33.77; +25% (-4%) | 2022-06-01 at 35.19 | 2025-07-02 at 77.36 (3-year limit) | +129% **BIG WIN** | +14% / +6% / +27% / +121% | +39% | -6% / +129% | listed; since buy +116% |
| LIFT | Li-Ft Power Ltd. | 2022-12-30 | C$200k; 11.00; +267% (+2%) | 2023-01-03 at 10.40 | 2023-12-01 at 5.65 (35% stop) | -47% **BIG LOSS** | -17% / -41% / -71% / -49% | +80% | -87% / -0% | listed; since buy -89% |
| LMN | Lumine Group Inc. | 2023-09-29 | C$1,400k; 20.12; +20% (+0%) | 2023-10-02 at 19.85 | 2025-11-03 at 32.38 (35% stop) | +62% | +84% / +62% / +113% / +11% | +101% | -14% / +173% | listed; since buy +36% |
| SOBO | South Bow Corporation | 2025-03-31 | C$47,961k; 36.76; +28% (+4%) | 2025-04-01 at 36.62 | 2026-11-13 at 47.49 (still held 13 Nov 2026) | +42% | +11% / +35% /  /  |  | -15% / +62% | listed; since buy +41% |
| PALS | Paragon Advanced Labs Inc. | 2026-06-30 | C$92k; 2.20; +13% (+10%) | 2026-07-02 at 2.45 | 2026-11-13 at 1.90 (still held 13 Nov 2026) | -25% |  /  /  /  |  | -28% / +34% | listed; since buy -19% |
| KEEL | Keel Infrastructure Corp. | 2026-08-31 | C$22,830k; 4.34; +47% (+5%) | 2026-09-01 at 4.26 | 2026-11-02 at 2.66 (35% stop) | -38% |  /  /  /  |  | -46% / +37% | listed; since buy -40% |
| PAIN | Vector Science And Therapeutic | 2026-10-30 | C$263k; 1.97; +432% (+6%) | 2026-11-02 at 1.97 | 2026-11-13 at 2.89 (still held 13 Nov 2026) | +43% |  /  /  /  |  | +2% / +59% | listed; since buy +30% |

### UK 2021+ listings (unseen): 20 companies passed, 20 bought

| Code | Company | Decided | Why it qualified: traded value a day; price; return since first close (index) | Bought | Sold (reason) | Result in the book | If simply held: 6m / 12m / 24m / 36m | Fund over the same 36m | Worst / best point in 3 years | Later |
|---|---|---|---|---|---|---|---|---|---|---|
| ATG | Auction Technology Group Plc | 2021-08-31 | GBP 1,068k; 16.22; +103% (+8%) | 2021-09-01 at 16.42 | 2022-03-01 at 9.30 (35% stop) | -44% **BIG LOSS** | -43% / -53% / -57% / -76% | +30% | -76% / -8% | listed; since buy -72% |
| CORD | Cordiant Digital Infrastructur | 2021-08-31 | GBP 580k; 1.14; +15% (+6%) | 2021-09-01 at 1.14 | 2023-11-01 at 0.63 (35% stop) | -41% **BIG LOSS** | -7% / -3% / -30% / -22% | +30% | -43% / +1% | listed; since buy +32% |
| SUP | Supreme Plc | 2021-08-31 | GBP 261k; 2.00; +33% (+11%) | 2021-09-01 at 2.00 | 2022-05-03 at 1.49 (35% stop) | -26% | -0% / -54% / -33% / -10% | +30% | -62% / +23% | listed; since buy -27% |
| DGI9 | Digital 9 Infrastructure Plc | 2021-09-30 | GBP 830k; 1.07; +9% (+5%) | 2021-10-01 at 1.07 | 2023-04-03 at 0.61 (35% stop) | -38% | +6% / +3% / -59% / -83% | +31% | -83% / +13% | listed; since buy -96% |
| TBLD | Tinybuild Inc | 2021-09-30 | GBP 137k; 2.42; +11% (+4%) | 2021-10-01 at 2.42 | 2022-07-01 at 1.20 (35% stop) | -52% **BIG LOSS** | -33% / -50% / -96% / -99% | +31% | -99% / +0% | listed; since buy -95% |
| TRST | Trustpilot Group Plc | 2021-09-30 | GBP 2,143k; 3.86; +46% (+5%) | 2021-10-01 at 3.78 | 2022-02-01 at 1.81 (35% stop) | -52% **BIG LOSS** | -61% / -79% / -72% / -42% | +31% | -86% / +1% | listed; since buy -31% |
| DARK | Darktrace Plc | 2021-10-29 | GBP 8,374k; 8.03; +143% (+3%) | 2021-11-01 at 6.82 | 2022-01-04 at 3.91 (35% stop) | -43% **BIG LOSS** | -38% / -47% / -48% / -15% | +24% | -69% / -5% | left the list 2024-10-01 (paid out) |
| BELL | Belluscura Plc | 2021-11-30 | GBP 126k; 0.98; +86% (-0%) | 2021-12-01 at 0.97 | 2022-09-01 at 0.80 (35% stop) | -20% | -8% / -26% / -79% / -89% | +29% | -93% / +51% | left the list 2025-12-01 (written off) |
| SED | Saietta Group Plc | 2022-01-31 | GBP 87k; 2.15; +71% (+4%) | 2022-02-01 at 2.20 | 2022-10-03 at 1.20 (35% stop) | -47% **BIG LOSS** | -34% / -78% / -93% / -100% | +28% | -100% / +0% | left the list 2024-04-04 (written off) |
| BHL | Bradda Head Holdings Ltd | 2022-01-31 | GBP 62k; 0.15; +159% (+9%) | 2022-02-01 at 0.14 | 2022-06-01 at 0.10 (35% stop) | -33% | -46% / -50% / -90% / -91% | +28% | -93% / +19% | listed; since buy -93% |
| LIKE | Likewise Group Plc | 2022-02-28 | GBP 64k; 0.36; +22% (+4%) | 2022-03-01 at 0.35 | 2022-10-03 at 0.20 (35% stop) | -45% **BIG LOSS** | -33% / -28% / -43% / -43% | +34% | -59% / +11% | listed; since buy +37% |
| BEN | Bens Creek Group Plc | 2022-04-29 | GBP 697k; 0.88; +740% (+5%) | 2022-05-03 at 0.89 | 2022-07-01 at 0.42 (35% stop) | -53% **BIG LOSS** | -73% / -81% / -100% / -100% | +25% | -100% / +3% | left the list 2024-05-16 (written off) |
| ADF | Facilities By Adf Plc | 2022-07-29 | GBP 65k; 0.61; +12% (-1%) | 2022-08-01 at 0.65 | 2024-12-02 at 0.31 (35% stop) | -50% **BIG LOSS** | -14% / -30% / -11% / -66% | +38% | -77% / +3% | listed; since buy -85% |
| RPI | Raspberry Pi Holdings Plc | 2024-12-31 | GBP 1,487k; 6.25; +62% (-1%) | 2025-01-02 at 6.62 | 2025-04-01 at 4.71 (35% stop) | -29% | -29% / -55% /  /  |  | -61% / +59% | listed; since buy -25% |
| ROSE | Rosebank Industries Plc | 2025-01-31 | GBP 53k; 9.05; +89% (+5%) | 2025-02-03 at 8.60 | 2025-04-01 at 5.34 (35% stop) | -39% | -58% / -57% /  /  |  | -64% / -2% | listed; since buy -61% |
| OPT | Optima Health Plc | 2025-03-31 | GBP 180k; 1.71; +13% (+4%) | 2025-04-01 at 1.73 | 2026-11-13 at 2.45 (still held 13 Nov 2026) | +39% | +30% / +4% /  /  |  | -7% / +48% | listed; since buy +41% |
| MHA | Mha Ltd | 2025-10-31 | GBP 111k; 1.53; +49% (+17%) | 2025-11-03 at 1.53 | 2026-11-13 at 1.46 (still held 13 Nov 2026) | -3% | +2% / -4% /  /  |  | -22% / +15% | listed; since buy -2% |
| WVIA | Winvia Entertainment Plc | 2026-05-29 | GBP 76k; 2.55; +17% (+8%) | 2026-06-01 at 2.66 | 2026-11-13 at 2.92 (still held 13 Nov 2026) | +12% |  /  /  /  |  | -11% / +16% | listed; since buy +14% |
| MICC | The Magnum Ice Cream Company N | 2026-06-30 | GBP 7,121k; 13.12; +17% (+8%) | 2026-07-01 at 13.47 | 2026-11-13 at 15.06 (still held 13 Nov 2026) | +11% |  /  /  /  |  | -4% / +12% | listed; since buy +10% |
| SUNB | Sunbelt Rentals Holdings Cdi | 2026-09-30 | GBP 30,118k; 55.82; +6% (-2%) | 2026-10-01 at 54.84 | 2026-11-13 at 61.76 (still held 13 Nov 2026) | +12% |  /  /  /  |  | +2% / +15% | listed; since buy +12% |

### US 1-in-3 sample (unseen): 226 companies passed, 127 bought

| Code | Company | Decided | Why it qualified: traded value a day; price; return since first close (index) | Bought | Sold (reason) | Result in the book | If simply held: 6m / 12m / 24m / 36m | Fund over the same 36m | Worst / best point in 3 years | Later |
|---|---|---|---|---|---|---|---|---|---|---|
| BYSI | Beyondspring Inc | 2017-09-29 | US$96k; 36.87; +119% (+7%) | 2017-10-02 at 38.00 | 2018-03-01 at 20.39 (35% stop) | -48% **BIG LOSS** | -29% / -34% / -54% / -65% | +40% | -75% / +4% | listed; since buy -99% |
| GOOS | Canada Goose Holdings Inc | 2017-09-29 | US$12,418k; 20.55; +28% (+6%) | 2017-10-02 at 20.98 | 2019-01-02 at 43.86 (35% stop) | +108% **BIG WIN** | +66% / +182% / +88% / +58% | +40% | -29% / +234% | listed; since buy -61% |
| NODK | Ni Holdings Inc | 2017-09-29 | US$360k; 17.90; +21% (+6%) | 2017-10-02 at 18.01 | 2020-11-02 at 16.71 (3-year limit) | -9% | -8% / -5% / -5% / -9% | +40% | -43% / +4% | listed; since buy -17% |
| CVNA | Carvana Co | 2017-10-31 | US$9,215k; 14.18; +28% (+8%) | 2017-11-01 at 14.01 | 2018-11-01 at 44.39 (35% stop) | +215% **BIG WIN** | +82% / +217% / +492% / +1263% | +38% | -1% / +1599% | listed; since buy +2462% |
| OKTA | Okta Inc | 2017-10-31 | US$9,474k; 28.92; +23% (+9%) | 2017-11-01 at 28.97 | 2020-12-01 at 236.99 (3-year limit) | +714% **BIG WIN** | +58% / +107% / +270% / +620% | +38% | -13% / +752% | listed; since buy +575% |
| GBLIL | Global Indemnity Limited Sub N | 2017-10-31 | US$539k; 26.00; +9% (+9%) | 2017-11-01 at 26.05 | 2020-12-01 at 26.50 (3-year limit) | +26% | +2% / +6% / +19% / +26% | +38% | -26% / +32% | left the list 2021-12-31 (paid out) |
| PCSB | Pcsb Financial Corp | 2017-10-31 | US$1,199k; 18.72; +14% (+10%) | 2017-11-01 at 18.74 | 2020-06-01 at 13.26 (35% stop) | -29% | +8% / +0% / +9% / -21% | +38% | -40% / +17% | left the list 2023-01-06 (paid out) |
| IR | Ingersoll Rand Inc | 2017-11-30 | US$16,129k; 32.41; +59% (+11%) | 2017-12-01 at 32.08 | 2019-01-02 at 21.00 (35% stop) | -29% | +4% / -16% / +20% / +69% | +47% | -36% / +73% | listed; since buy +216% |
| SGH | Smart Global Holdings Inc | 2017-11-30 | US$3,940k; 29.99; +123% (+10%) | 2017-12-01 at 31.12 | 2018-07-02 at 31.77 (35% stop) | +2% | +53% / +12% / -6% / +4% | +47% | -45% / +75% | left the list 2024-10-15 (written off) |
| CGBD | Carlyle Secured Lending Inc | 2017-12-29 | US$1,267k; 20.04; +18% (+10%) | 2018-01-02 at 18.48 | 2020-04-01 at 4.95 (35% stop) | -65% **BIG LOSS** | -4% / -21% / -9% / -18% | +45% | -69% / +2% | listed; since buy +38% |
| ESQ | Esquire Financial Holdings Inc | 2017-12-29 | US$176k; 19.74; +29% (+11%) | 2018-01-02 at 18.91 | 2020-04-01 at 14.75 (35% stop) | -24% | +40% / +11% / +34% / -1% | +45% | -38% / +42% | listed; since buy +616% |
| CISN | Cision Ltd | 2017-12-29 | US$1,993k; 11.87; +15% (+10%) | 2018-01-02 at 12.13 | 2019-01-02 at 11.81 (35% stop) | -3% | +26% / -7% / -18% / -100% | +45% | -49% / +50% | left the list 2020-01-30 (written off) |
| RBB | Rbb Bancorp | 2018-01-31 | US$615k; 26.88; +16% (+14%) | 2018-02-01 at 26.75 | 2019-01-02 at 18.08 (35% stop) | -33% | +15% / -27% / -24% / -34% | +43% | -58% / +24% | listed; since buy +18% |
| HUSN | Hudson Capital Inc | 2018-02-28 | US$7,362k; 82.78; +206% (+10%) | 2018-03-01 at 80.48 | 2018-07-02 at 35.93 (35% stop) | -56% **BIG LOSS** | -67% / -86% / -98% / -99% | +51% | -100% / -0% | left the list 2022-05-26 (written off) |
| MDB | Mongodb | 2018-04-30 | US$8,436k; 35.99; +12% (+3%) | 2018-05-01 at 36.51 | 2021-06-01 at 289.74 (3-year limit) | +690% **BIG WIN** | +102% / +263% / +327% / +688% | +67% | +1% / +1058% | listed; since buy +740% |
| BAND | Bandwidth Inc | 2018-05-31 | US$2,278k; 37.31; +76% (+5%) | 2018-06-01 at 39.45 | 2019-11-01 at 57.05 (35% stop) | +44% | +13% / +82% / +192% / +190% | +62% | -11% / +389% | listed; since buy +2% |
| IFRX | Inflarx N.V. | 2018-05-31 | US$1,242k; 38.14; +154% (+4%) | 2018-06-01 at 37.00 | 2019-07-01 at 3.43 (35% stop) | -91% **BIG LOSS** | -18% / +1% / -78% / -92% | +62% | -94% / +39% | listed; since buy -97% |
| AAVL | Aavl | 2018-05-31 | US$418k; 0.62; +92% (+5%) | 2018-06-01 at 0.64 | 2018-11-01 at 0.46 (35% stop) | -29% | -43% / +75% / +87% / +87% | +62% | -55% / +87% | left the list 2019-06-28 (paid out) |
| ALNA | Allena Pharmaceuticals Inc | 2018-05-31 | US$691k; 14.34; +44% (+5%) | 2018-06-01 at 14.92 | 2018-11-01 at 8.50 (35% stop) | -44% **BIG LOSS** | -37% / -66% / -85% / -92% | +62% | -96% / +0% | left the list 2022-11-09 (written off) |
| APLS | Apellis Pharmaceuticals Inc | 2018-05-31 | US$2,531k; 20.41; +45% (+5%) | 2018-06-01 at 19.63 | 2018-11-01 at 14.99 (35% stop) | -24% | -23% / +8% / +69% / +185% | +62% | -42% / +195% | left the list 2026-05-13 (paid out) |
| SEND | Sendgrid Inc | 2018-05-31 | US$6,814k; 26.54; +47% (+5%) | 2018-06-01 at 26.97 | 2019-04-01 at 54.08 (left the list) | +100% **BIG WIN** | +65% / +101% / +101% / +101% | +62% | -7% / +101% | left the list 2019-01-31 (paid out) |
| NMRK | Newmark Group Inc | 2018-06-29 | US$4,546k; 14.23; +3% (+2%) | 2018-07-02 at 14.72 | 2018-12-03 at 8.70 (35% stop) | -40% **BIG LOSS** | -43% / -34% / -67% / -13% | +68% | -82% / +2% | listed; since buy -22% |
| AMEH | Astrana Health Inc. | 2018-06-29 | US$502k; 25.86; +159% (+3%) | 2018-07-02 at 25.38 | 2018-09-04 at 14.42 (35% stop) | -44% **BIG LOSS** | -23% / -38% / -35% / +161% | +68% | -62% / +161% | left the list 2024-04-26 (paid out) |
| CASA | Casa Systems Inc | 2018-06-29 | US$12,659k; 16.33; +13% (+2%) | 2018-07-02 at 16.39 | 2019-03-01 at 10.32 (35% stop) | -37% | -20% / -61% / -74% / -47% | +68% | -88% / +8% | left the list 2024-04-05 (written off) |
| FTNW | Fte Networks Inc | 2018-06-29 | US$440k; 19.30; +95% (+3%) | not filled (no place free or no trade) | | | -85% / -94% / -100% / -100% | +68% | -98% / +2% | |
| GRUB_old | Grubhub Inc | 2018-06-29 | US$141,244k; 209.82; +45% (+2%) | 2018-07-02 at 213.20 | 2018-11-01 at 189.26 (35% stop) | -12% | -29% / -28% / -100% / -100% | +68% | -69% / +38% | left the list 2019-12-13 (written off) |
| AGS | Playags Inc | 2018-07-31 | US$4,013k; 28.55; +54% (-2%) | not filled (no place free or no trade) | | | -9% / -36% / -88% / -73% | +66% | -96% / +13% | |
| BILI | Bilibili Inc | 2018-09-28 | US$52,203k; 13.48; +20% (+12%) | not filled (no place free or no trade) | | | +30% / -1% / +205% / +365% | +57% | -14% / +1021% | |
| IQ | Iqiyi Inc | 2018-09-28 | US$314,717k; 27.07; +74% (+10%) | not filled (no place free or no trade) | | | -11% / -42% / -14% / -71% | +57% | -71% / +7% | |
| QTTB | Q32 Bio Inc | 2018-09-28 | US$106k; 22.86; +23% (+12%) | not filled (no place free or no trade) | | | +31% / -23% / -50% / -65% | +57% | -73% / +37% | |
| RFL | Rafael Holdings, Inc. | 2018-09-28 | US$376k; 8.40; +71% (+12%) | not filled (no place free or no trade) | | | +64% / +148% / +90% / +286% | +57% | -8% / +671% | |
| BFST | Business First Bancshares Inc | 2018-10-31 | US$432k; 26.37; +5% (+3%) | 2018-11-01 at 26.73 | 2020-04-01 at 11.27 (35% stop) | -58% **BIG LOSS** | -5% / -5% / -31% / +8% | +79% | -63% / +8% | listed; since buy +41% |
| DOCU | Docusign Inc | 2018-10-31 | US$81,331k; 41.94; +6% (+2%) | 2018-11-01 at 41.85 | 2021-12-01 at 230.79 (3-year limit) | +449% **BIG WIN** | +27% / +64% / +398% / +577% | +79% | -11% / +641% | listed; since buy +83% |
| CDAY | Ceridian Hcm Holding Inc | 2018-10-31 | US$14,261k; 37.97; +22% (+2%) | 2018-11-01 at 38.73 | 2021-12-01 at 104.88 (3-year limit) | +169% **BIG WIN** | +28% / +29% / +125% / +231% | +79% | -17% / +236% | left the list 2024-01-31 (paid out) |
| SMAR | Smartsheet Inc | 2018-10-31 | US$8,946k; 23.66; +21% (+2%) | 2018-11-01 at 24.82 | 2021-12-01 at 59.49 (3-year limit) | +138% **BIG WIN** | +68% / +58% / +104% / +180% | +79% | -13% / +240% | left the list 2025-01-21 (paid out) |
| RILYH | B. Riley Financial Inc | 2018-11-30 | US$219k; 25.50; +5% (+2%) | 2018-12-03 at 25.50 | 2021-11-01 at 25.52 (left the list) | +21% | +5% / +10% / +15% / +22% | +71% | -38% / +23% | left the list 2021-09-07 (paid out) |
| FTSV | Forty Seven Inc | 2018-12-31 | US$1,276k; 15.72; +4% (-8%) | 2019-01-02 at 15.69 | 2019-06-03 at 11.30 (35% stop) | -29% | -33% / +155% / +509% / +509% | +100% | -64% / +509% | left the list 2020-04-06 (paid out) |
| KZR | Kezar Life Sciences Inc | 2018-12-31 | US$86k; 23.60; +33% (-9%) | 2019-01-02 at 22.74 | 2019-06-03 at 9.29 (35% stop) | -60% **BIG LOSS** | -70% / -84% / -77% / -26% | +100% | -89% / +4% | left the list 2026-05-11 (written off) |
| VRT | Vertiv Holdings Co | 2019-01-31 | US$104k; 9.87; +0% (-4%) | 2019-02-01 at 9.95 | 2022-03-01 at 12.59 (3-year limit) | +25% | +3% / +24% / +102% / +112% | +76% | -44% / +187% | listed; since buy +1865% |
| GSAH | Gs Acquisition Holdings Corp I | 2019-01-31 | US$112k; 9.87; +0% (-4%) | 2019-02-01 at 9.95 | 2022-02-01 at 9.94 (left the list) | -100% **BIG LOSS** | +3% / +24% / +22% / -100% | +76% | -1% / +51% | left the list 2021-12-22 (written off) |
| YMAB | Y Mabs Therapeutics | 2019-03-29 | US$1,407k; 26.21; +9% (-3%) | 2019-04-01 at 27.82 | 2021-04-01 at 30.28 (35% stop) | +8% | -6% / -6% / +9% / -57% | +69% | -76% / +95% | left the list 2025-09-16 (written off) |
| ARCE | Arco Platform | 2019-03-29 | US$1,186k; 32.29; +37% (-2%) | 2019-04-01 at 31.84 | 2021-02-01 at 33.87 (35% stop) | +6% | +59% / +33% / -20% / -36% | +69% | -48% / +86% | left the list 2023-12-15 (paid out) |
| SAF | Safeco Corp | 2019-03-29 | US$112k; 25.39; +4% (-3%) | 2019-04-01 at 25.44 | 2021-10-01 at 25.01 (left the list) | +13% | +6% / -15% / +14% / +15% | +69% | -46% / +16% | left the list 2021-08-30 (paid out) |
| GH | Guardant Health Inc | 2019-04-30 | US$22,479k; 65.51; +103% (+2%) | 2019-05-01 at 65.01 | 2022-01-03 at 100.49 (35% stop) | +54% | +9% / +18% / +145% / -5% | +48% | -26% / +175% | listed; since buy +123% |
| CTK | Cootek (Cayman) Inc | 2019-04-30 | US$611k; 11.04; +17% (+1%) | not filled (no place free or no trade) | | | -53% / -34% / -79% / -98% | +48% | -98% / -1% | |
| NMFCL | New Mountain Finance Corporati | 2019-04-30 | US$99k; 25.47; +5% (+1%) | not filled (no place free or no trade) | | | +5% / -6% / +10% / +10% | +48% | -26% / +12% | |
| SWI | Solarwinds Corp | 2019-04-30 | US$1,673k; 10.31; +30% (+6%) | not filled (no place free or no trade) | | | +4% / -12% / -13% / -34% | +48% | -42% / +23% | |
| ETRN | Equitrans Midstream Corp | 2019-05-31 | US$36,346k; 19.86; +6% (+1%) | 2019-06-03 at 19.79 | 2019-12-02 at 9.53 (35% stop) | -49% **BIG LOSS** | -46% / -53% / -45% / -45% | +57% | -77% / +6% | left the list 2024-07-19 (paid out) |
| ORTX | Orchard Therapeutics Plc | 2019-05-31 | US$932k; 18.91; +35% (+1%) | not filled (no place free or no trade) | | | -40% / -50% / -72% / -98% | +57% | -98% / -12% | |
| TW | Tradeweb Markets Inc | 2019-09-30 | US$23,967k; 36.98; +37% (+4%) | not filled (no place free or no trade) | | | +13% / +54% / +116% / +51% | +28% | -4% / +173% | |
| AVTR | Avantor Inc | 2019-11-29 | US$37,678k; 17.13; +22% (+9%) | 2019-12-02 at 16.93 | 2022-09-01 at 24.93 (35% stop) | +47% | +14% / +60% / +126% / +35% | +37% | -51% / +160% | listed; since buy -9% |
| FSLY | Fastly, Inc. Class A Common St | 2019-11-29 | US$18,174k; 20.41; +28% (+9%) | 2019-12-02 at 19.85 | 2021-04-01 at 70.31 (35% stop) | +252% **BIG WIN** | +142% / +312% / +82% / -49% | +37% | -63% / +549% | listed; since buy -10% |
| CIH | China Index Holdings Ltd | 2019-12-31 | US$247k; 3.64; +14% (+12%) | not filled (no place free or no trade) | | | -32% / -43% / -72% / -73% | +23% | -82% / -4% | |
| AKRO | Akero Therapeutics Inc | 2019-12-31 | US$1,903k; 22.19; +21% (+9%) | not filled (no place free or no trade) | | | +64% / +28% / +5% / +146% | +23% | -60% / +173% | |
| GO | Grocery Outlet Holding Corp | 2019-12-31 | US$16,893k; 32.45; +14% (+9%) | not filled (no place free or no trade) | | | +31% / +23% / -12% / -10% | +23% | -34% / +46% | |
| STOK | Stoke Therapeutics Inc | 2019-12-31 | US$3,363k; 28.32; +11% (+10%) | not filled (no place free or no trade) | | | -13% / +133% / -10% / -66% | +23% | -73% / +163% | |
| CHWY | Chewy Inc | 2019-12-31 | US$54,239k; 29.00; +32% (+12%) | not filled (no place free or no trade) | | | +59% / +203% / +99% / +20% | +23% | -23% / +301% | |
| AFYA | Afya Ltd | 2020-01-31 | US$3,995k; 29.86; +25% (+8%) | not filled (no place free or no trade) | | | -15% / -22% / -51% / -50% | +35% | -70% / -0% | |
| AMK | Assetmark Financial Holdings I | 2020-01-31 | US$3,511k; 29.33; +8% (+8%) | not filled (no place free or no trade) | | | -7% / -22% / -20% / -9% | +35% | -51% / +11% | |
| NEWTL | Newtek Business Services Corp | 2020-02-28 | US$68k; 26.14; +7% (-1%) | not filled (no place free or no trade) | | | -1% / +5% / +9% / +12% | +35% | -41% / +14% | |
| IGMS | Igm Biosciences Inc | 2020-03-31 | US$4,057k; 56.15; +131% (-14%) | 2020-04-01 at 51.30 | 2020-09-01 at 44.77 (35% stop) | -13% | +44% / +51% / -48% / -73% | +75% | -74% / +136% | left the list 2025-08-13 (written off) |
| STSA | Satsuma Pharmaceuticals Inc | 2020-03-31 | US$1,015k; 21.52; +27% (-14%) | not filled (no place free or no trade) | | | -76% / -63% / -76% / -95% | +75% | -96% / +117% | |
| PGNY | Progyny Inc | 2020-04-30 | US$15,096k; 23.43; +47% (-4%) | not filled (no place free or no trade) | | | +9% / +145% / +74% / +51% | +51% | -9% / +195% | |
| CCX-WS | Ccx-Ws | 2020-04-30 | US$794k; 2.38; +32% (-4%) | not filled (no place free or no trade) | | | +36% / +127% / +169% / +169% | +51% | -7% / +241% | |
| FREQ | Frequency Therapeutics Inc | 2020-04-30 | US$2,027k; 15.91; +16% (+0%) | not filled (no place free or no trade) | | | +39% / -28% / -92% / -98% | +51% | -98% / +256% | |
| KAHOT | Kahoot As | 2020-04-30 | US$6,635k; 64.00; +45% (-1%) | not filled (no place free or no trade) | | | -13% / +30% / -100% / -100% | +51% | -50% / +106% | |
| VIE | Viela Bio Inc | 2020-04-30 | US$3,221k; 40.63; +74% (+0%) | not filled (no place free or no trade) | | | -16% / -100% / -100% / -100% | +51% | -45% / +55% | |
| RAPT | Rapt Therapeutics Inc | 2020-05-29 | US$213k; 18.28; +41% (+0%) | not filled (no place free or no trade) | | | +13% / -2% / -26% / +1% | +45% | -48% / +106% | |
| OYST | Oyster Point Pharma Inc | 2020-05-29 | US$2,357k; 28.46; +52% (+0%) | not filled (no place free or no trade) | | | -26% / -39% / -87% / -62% | +45% | -88% / +12% | |
| SITM | Sitime Corporation | 2020-05-29 | US$1,739k; 29.81; +129% (-2%) | not filled (no place free or no trade) | | | +185% / +218% / +587% / +232% | +45% | +3% / +981% | |
| BMY-R | Bmy-R | 2020-05-29 | US$11,826k; 3.22; +55% (-2%) | not filled (no place free or no trade) | | | -100% / -100% / -100% / -100% | +45% | -8% / +9% | |
| BMY-RI | Bmy-Ri | 2020-05-29 | US$11,888k; 3.29; +75% (-2%) | not filled (no place free or no trade) | | | -62% / -100% / -100% / -100% | +45% | -80% / +14% | |
| JBI | Janus International Group Inc | 2020-06-30 | US$135k; 9.97; +2% (-4%) | not filled (no place free or no trade) | | | +7% / +37% / -9% / +2% | +49% | -19% / +56% | |
| XP | Xp Inc | 2020-06-30 | US$39,818k; 42.01; +22% (-1%) | not filled (no place free or no trade) | | | -7% / -2% / -59% / -46% | +49% | -75% / +18% | |
| JIH-WS | Juniper Industrial Holdings In | 2020-06-30 | US$109k; 9.97; +19% (-4%) | not filled (no place free or no trade) | | | +7% / +31% / +31% / +31% | +49% | -2% / +44% | |
| NBP | Novabridge Biosciences | 2020-07-31 | US$860k; 31.95; +156% (-2%) | not filled (no place free or no trade) | | | +110% / +157% / -71% / -91% | +42% | -91% / +178% | |
| REYN | Reynolds Consumer Products Inc | 2020-07-31 | US$18,661k; 34.06; +20% (+1%) | not filled (no place free or no trade) | | | -12% / -17% / -9% / -10% | +42% | -24% / +1% | |
| FREY | Freyr Battery Sa | 2020-07-31 | US$254k; 10.08; +3% (+0%) | not filled (no place free or no trade) | | | +26% / -10% / +7% / -21% | +42% | -35% / +61% | |
| VVNT-WS | Vvnt-Ws | 2020-07-31 | US$2,362k; 15.35; +51% (-1%) | not filled (no place free or no trade) | | | +24% / -20% / -100% / -100% | +42% | -47% / +58% | |
| CCXX-UN | Churchill Capital Corp Iii | 2020-08-31 | US$1,681k; 11.52; +10% (+4%) | 2020-09-01 at 11.44 | 2020-12-01 at 10.34 (left the list) | -10% | -10% / -10% / -10% / -10% | +33% | -12% / +1% | left the list 2020-10-08 (paid out) |
| GFL | Gfl Environmental Holdings Inc | 2020-09-30 | US$15,266k; 21.26; +27% (+12%) | not filled (no place free or no trade) | | | +63% / +71% / +18% / +45% | +32% | -13% / +92% | |
| ELVN | Enliven Therapeutics Inc. | 2020-09-30 | US$156k; 20.34; +36% (+36%) | not filled (no place free or no trade) | | | -61% / -80% / -89% / -83% | +32% | -95% / +42% | |
| CARR | Carrier Global Corp | 2020-09-30 | US$152,120k; 30.54; +155% (+40%) | not filled (no place free or no trade) | | | +39% / +72% / +23% / +85% | +32% | +1% / +102% | |
| DMYT-U | Dmyt-U | 2020-10-30 | US$2,534k; 11.14; +21% (+17%) | not filled (no place free or no trade) | | | +100% / +100% / +100% / +100% | +38% | -3% / +114% | |
| SKLZ | Skillz Platform Inc | 2020-10-30 | US$308k; 11.53; +16% (+14%) | not filled (no place free or no trade) | | | +40% / +5% / -91% / -97% | +38% | -98% / +295% | |
| KC | Kingsoft Cloud Holdings Ltd | 2020-11-30 | US$45,482k; 40.23; +69% (+24%) | 2020-12-01 at 40.46 | 2021-07-01 at 34.29 (35% stop) | -16% | -4% / -59% / -93% / -89% | +30% | -95% / +78% | listed; since buy -84% |
| LOAK-U | Loak-U | 2020-11-30 | US$660k; 12.50; +33% (+20%) | 2020-12-01 at 12.76 | 2021-02-01 at 24.20 (left the list) | +89% | +90% / +90% / +90% / +90% | +30% | +4% / +93% | left the list 2020-12-29 (paid out) |
| LOAK-WS | Loak-Ws | 2020-11-30 | US$660k; 12.50; +33% (+20%) | 2020-12-01 at 12.76 | 2021-02-01 at 24.20 (left the list) | +89% | +90% / +90% / +90% / +90% | +30% | +4% / +93% | left the list 2020-12-29 (paid out) |
| NARI | Inari Medical Inc | 2020-11-30 | US$16,935k; 69.07; +62% (+23%) | 2020-12-01 at 66.61 | 2022-02-01 at 74.67 (35% stop) | +12% | +20% / +25% / +13% / -6% | +30% | -27% / +89% | left the list 2025-02-19 (paid out) |
| FREEW | Whole Earth Brands Inc | 2020-12-31 | US$92k; 1.38; +24% (+20%) | not filled (no place free or no trade) | | | +65% / -3% / -81% / -94% | +33% | -96% / +89% | |
| IPOC-WS | Ipoc-Ws | 2020-12-31 | US$14,698k; 16.77; +64% (+24%) | not filled (no place free or no trade) | | | +3% / +3% / +3% / +3% | +33% | -7% / +3% | |
| IPOC-U | Ipoc-U | 2020-12-31 | US$14,698k; 16.77; +64% (+24%) | not filled (no place free or no trade) | | | +3% / +3% / +3% / +3% | +33% | -7% / +3% | |
| IPOC | Social Capital Hedosophia Hold | 2020-12-31 | US$14,731k; 16.77; +64% (+24%) | not filled (no place free or no trade) | | | +2% / +2% / +2% / +2% | +33% | -7% / +3% | |
| INVZ | Innoviz Technologies | 2020-12-31 | US$104k; 14.29; +46% (+23%) | not filled (no place free or no trade) | | | -30% / -55% / -72% / -83% | +33% | -90% / +3% | |
| AZEK | Azek Company Inc | 2020-12-31 | US$22,646k; 38.45; +42% (+24%) | 2021-01-04 at 37.60 | 2022-03-01 at 28.05 (35% stop) | -26% | +6% / +21% / -40% / -4% | +33% | -60% / +35% | left the list 2025-06-30 (paid out) |
| CLOV | Clover Health Investments Corp | 2020-12-31 | US$14,698k; 16.77; +64% (+24%) | not filled (no place free or no trade) | | | -36% / -74% / -94% / -94% | +33% | -95% / +42% | |
| GIK-WS | Gik-Ws | 2020-12-31 | US$253k; 13.18; +34% (+20%) | not filled (no place free or no trade) | | | +34% / -0% / -0% / -0% | +33% | -41% / +36% | |
| JWS-U | Jws-U | 2021-01-29 | US$5,713k; 13.01; +28% (+17%) | 2021-02-01 at 14.09 | 2021-08-02 at 14.75 (left the list) | +4% | +5% / +5% / +5% / +5% | +37% | -11% / +14% | left the list 2021-06-03 (paid out) |
| INZY | Inozyme Pharma Inc | 2021-01-29 | US$1,074k; 21.04; +20% (+16%) | not filled (no place free or no trade) | | | -28% / -70% / -89% / -76% | +37% | -95% / +3% | |
| MEG | Montrose Environmental Grp | 2021-01-29 | US$4,677k; 36.98; +68% (+15%) | 2021-02-01 at 37.17 | 2022-02-01 at 46.34 (35% stop) | +24% | +39% / +23% / +45% / -16% | +37% | -40% / +110% | left the list 2026-05-01 (paid out) |
| ALVR | Allovir Inc | 2021-01-29 | US$294k; 36.57; +44% (+14%) | not filled (no place free or no trade) | | | -47% / -78% / -84% / -98% | +37% | -98% / +21% | |
| ONT | Onterris | 2021-01-29 | US$4,676k; 36.98; +68% (+15%) | 2021-02-01 at 37.17 | 2022-02-01 at 46.34 (35% stop) | +24% | +39% / +23% / +45% / -16% | +37% | -40% / +110% | listed; since buy -36% |
| BFLY-WS | Bfly-Ws | 2021-01-29 | US$1,576k; 18.45; +86% (+18%) | not filled (no place free or no trade) | | | -45% / -100% / -100% / -100% | +37% | -67% / +39% | |
| OSH | Oak Street Health Inc | 2021-02-26 | US$18,521k; 53.03; +33% (+14%) | not filled (no place free or no trade) | | | -10% / -66% / -32% / -25% | +38% | -73% / +25% | |
| DCT | Duck Creek Technologies Inc | 2021-02-26 | US$18,890k; 47.30; +18% (+13%) | not filled (no place free or no trade) | | | -7% / -53% / -62% / -62% | +38% | -79% / +1% | |
| VGFC | Very Good Food Company Inc | 2021-02-26 | US$1,821k; 4.59; +309% (+17%) | not filled (no place free or no trade) | | | -48% / -89% / -100% / -100% | +38% | -100% / +1% | |
| QS-WT | Qs-Wt | 2021-02-26 | US$237,895k; 54.93; +455% (+13%) | not filled (no place free or no trade) | | | -63% / -100% / -100% / -100% | +38% | -67% / +11% | |
| CERE | Cerevel Therapeutics Holdings  | 2021-02-26 | US$2,168k; 15.16; +27% (+17%) | not filled (no place free or no trade) | | | +91% / +67% / +74% / +159% | +38% | -22% / +181% | |
| RXT_old | Rackspace Technology Inc | 2021-02-26 | US$21,598k; 21.02; +28% (+15%) | not filled (no place free or no trade) | | | +21% / +21% / +21% / +21% | +38% | -3% / +26% | |
| QS | Quantumscape Corporation Class | 2021-02-26 | US$237,895k; 54.93; +455% (+13%) | not filled (no place free or no trade) | | | -63% / -72% / -85% / -89% | +38% | -91% / +11% | |
| NNOX | Nano X Imaging Ltd | 2021-02-26 | US$65,977k; 45.27; +109% (+12%) | not filled (no place free or no trade) | | | -45% / -77% / -84% / -75% | +38% | -89% / +12% | |
| KYMR | Kymera Therapeutics Inc | 2021-02-26 | US$5,919k; 47.98; +44% (+12%) | not filled (no place free or no trade) | | | +24% / -18% / -34% / -10% | +38% | -77% / +38% | |
| ALVR | Allovir Inc | 2021-02-26 | US$294k; 36.56; +44% (+17%) | not filled (no place free or no trade) | | | -49% / -77% / -84% / -98% | +38% | -98% / -1% | |
| AOUT | American Outdoor Brands Inc | 2021-02-26 | US$2,865k; 20.01; +29% (+12%) | not filled (no place free or no trade) | | | +29% / -26% / -56% / -63% | +38% | -66% / +70% | |
| UTZ-WS | Utz-Ws | 2021-03-31 | US$11,824k; 24.79; +35% (+14%) | 2021-04-01 at 25.00 | 2021-10-01 at 16.35 (35% stop) | -35% | -31% / -100% / -100% / -100% | +34% | -45% / +20% | left the list 2021-12-17 (written off) |
| DFHT | Deerfield Healthcare Technolog | 2021-03-31 | US$412k; 12.12; +22% (+21%) | not filled (no place free or no trade) | | | +22% / +22% / +22% / +22% | +34% | +3% / +25% | |
| DEN | Denbury Inc. | 2021-03-31 | US$13,552k; 47.89; +165% (+21%) | 2021-04-01 at 50.87 | 2024-01-02 at 88.66 (left the list) | +74% | +38% / +54% / +78% / +74% | +34% | -10% / +97% | left the list 2023-11-03 (paid out) |
| ACTCU | Arclight Clean Transition Corp | 2021-03-31 | US$396k; 19.90; +99% (+23%) | not filled (no place free or no trade) | | | -100% / -100% / -100% / -100% | +34% | -27% / +8% | |
| U | Unity Software Inc | 2021-03-31 | US$311,919k; 100.31; +47% (+20%) | 2021-04-01 at 101.08 | 2022-02-01 at 107.80 (35% stop) | +6% | +25% / -2% / -68% / -75% | +34% | -79% / +99% | listed; since buy -52% |
| PRLD | Prelude Therapeutics Inc | 2021-03-31 | US$7,001k; 43.33; +65% (+20%) | not filled (no place free or no trade) | | | -24% / -83% / -84% / -89% | +34% | -96% / +7% | |
| PLBY | Playboy, Inc. | 2021-03-31 | US$2,467k; 19.59; +98% (+14%) | not filled (no place free or no trade) | | | +1% / -44% / -92% / -96% | +34% | -98% / +155% | |
| LCID | Lucid Group Inc | 2021-03-31 | US$2,351k; 23.18; +134% (+20%) | not filled (no place free or no trade) | | | +7% / +7% / -67% / -89% | +34% | -89% / +133% | |
| BNL | Broadstone Net Lease Inc | 2021-03-31 | US$5,938k; 18.30; +25% (+18%) | not filled (no place free or no trade) | | | +38% / +24% / +2% / -3% | +34% | -13% / +53% | |
| WE | Wework Inc | 2021-04-30 | US$2,850k; 12.20; +24% (+22%) | not filled (no place free or no trade) | | | -16% / -46% / -97% / -100% | +28% | -100% / +9% | |
| PSFE-WT | Paysafe Ltd. Wt | 2021-04-30 | US$4,061k; 4.57; +239% (+20%) | not filled (no place free or no trade) | | | -57% / -91% / -99% / -99% | +28% | -99% / -4% | |
| EAR | Eargo, Inc. | 2021-04-30 | US$15,209k; 57.24; +70% (+20%) | not filled (no place free or no trade) | | | -83% / -93% / -99% / -100% | +28% | -100% / -8% | |
| CDAK | Codiak Biosciences Inc | 2021-04-30 | US$2,626k; 19.80; +63% (+20%) | not filled (no place free or no trade) | | | -30% / -84% / -100% / -100% | +28% | -100% / +30% | |
| TARS | Tarsus Pharmaceuticals Inc | 2021-04-30 | US$1,149k; 30.72; +49% (+20%) | not filled (no place free or no trade) | | | -13% / -56% / -53% / +15% | +28% | -65% / +23% | |
| ASO | Academy Sports Outdoors Inc | 2021-04-30 | US$23,746k; 30.81; +137% (+25%) | not filled (no place free or no trade) | | | +37% / +23% / +101% / +87% | +28% | -11% / +144% | |
| MNSO | Miniso Group Holding Ltd | 2021-04-30 | US$20,582k; 26.90; +29% (+20%) | not filled (no place free or no trade) | | | -44% / -71% / -37% / -5% | +28% | -83% / +15% | |
| IMNM | Immunome Inc | 2021-04-30 | US$1,360k; 26.56; +97% (+25%) | not filled (no place free or no trade) | | | -6% / -85% / -80% / -37% | +28% | -91% / +11% | |
| EBC | Eastern Bankshares Inc | 2021-04-30 | US$16,723k; 21.33; +76% (+20%) | not filled (no place free or no trade) | | | -3% / -11% / -49% / -32% | +28% | -50% / +6% | |
| PSFE | Paysafe Ltd | 2021-04-30 | US$8,198k; 13.80; +39% (+20%) | not filled (no place free or no trade) | | | -44% / -79% / -92% / -91% | +28% | -94% / -2% | |
| LESL | Leslies Inc | 2021-05-28 | US$1,306k; 29.16; +34% (+27%) | not filled (no place free or no trade) | | | -30% / -33% / -66% / -80% | +31% | -86% / +7% | |
| PTRAW | Proterra Inc | 2021-05-28 | US$966k; 5.50; +355% (+16%) | not filled (no place free or no trade) | | | -100% / -100% / -100% / -100% | +31% | -96% / +12% | |
| MILEW | Metromile Inc | 2021-05-28 | US$422k; 2.06; +65% (+18%) | not filled (no place free or no trade) | | | -88% / -92% / -100% / -100% | +31% | -97% / +55% | |
| LICY-WT | Li-Cycle Holdings Corp. | 2021-05-28 | US$366k; 1.73; +137% (+16%) | not filled (no place free or no trade) | | | +109% / -100% / -100% / -100% | +31% | -21% / +137% | |
| ACTC | Arclight Clean Transition Corp | 2021-05-28 | US$13,299k; 18.15; +84% (+16%) | 2021-06-01 at 18.77 | 2021-08-02 at 16.94 (left the list) | -100% **BIG LOSS** | -100% / -100% / -100% / -100% | +31% | -10% / +2% | left the list 2021-06-15 (written off) |
| WGS | Genedx Holdings Corp. | 2021-05-28 | US$228k; 12.66; +29% (+22%) | not filled (no place free or no trade) | | | -48% / -84% / -98% / -95% | +31% | -100% / +10% | |
| TLS | Telos Corp | 2021-05-28 | US$19,198k; 32.88; +62% (+17%) | 2021-06-01 at 33.14 | 2021-12-01 at 15.57 (35% stop) | -53% **BIG LOSS** | -51% / -71% / -91% / -87% | +31% | -95% / +10% | listed; since buy -78% |
| PWP | Perella Weinberg Partners | 2021-05-28 | US$1,446k; 12.66; +28% (+18%) | not filled (no place free or no trade) | | | -9% / -41% / -36% / +26% | +31% | -56% / +32% | |
| ALGM | Allegro Microsystems Inc | 2021-05-28 | US$17,700k; 26.21; +48% (+27%) | 2021-06-01 at 26.22 | 2022-07-01 at 19.96 (35% stop) | -24% | +21% / -2% / +51% / +12% | +31% | -25% / +101% | listed; since buy +9% |
| AAN | The Aaron'S Company Inc. | 2021-05-28 | US$8,422k; 35.97; +36% (+16%) | not filled (no place free or no trade) | | | -33% / -45% / -64% / -75% | +31% | -79% / +3% | |
| OWL | Blue Owl Capital Inc | 2021-06-30 | US$6,094k; 12.88; +26% (+18%) | not filled (no place free or no trade) | | | +19% / -19% / -5% / +55% | +35% | -30% / +71% | |
| SPRY | Ars Pharmaceuticals, Inc | 2021-06-30 | US$5,059k; 30.89; +24% (+16%) | not filled (no place free or no trade) | | | -80% / -87% / -80% / -72% | +35% | -91% / +9% | |
| GHVIU | Gores Holdings Vi Inc | 2021-06-30 | US$265k; 17.02; +70% (+17%) | not filled (no place free or no trade) | | | -100% / -100% / -100% / -100% | +35% | -17% / +0% | |
| LCY | Landcadia Holdings Iii Inc | 2021-06-30 | US$7,010k; 12.40; +26% (+17%) | 2021-07-01 at 12.45 | 2021-08-02 at 0.01 (35% stop) | -100% **BIG LOSS** | -14% / -24% / -24% / -24% | +35% | -100% / -0% | left the list 2022-02-18 (paid out) |
| PDAC-WS | Pdac-Ws | 2021-06-30 | US$5,431k; 12.18; +25% (+17%) | not filled (no place free or no trade) | | | -8% / -8% / -8% / -8% | +35% | -22% / +1% | |
| TSIAW | Ts Innovation Acquisitions Cor | 2021-07-30 | US$200k; 3.85; +93% (+17%) | 2021-08-02 at 3.92 | 2021-10-01 at 4.39 (left the list) | +11% | +12% / +12% / +12% / +12% | +24% | +2% / +12% | left the list 2021-08-05 (paid out) |
| LTCHW | Latch Inc | 2021-07-30 | US$199k; 3.85; +93% (+17%) | not filled (no place free or no trade) | | | -63% / -97% / -98% / -100% | +24% | -100% / +26% | |
| ASAI | Sendas Distribuidora Sa | 2021-08-31 | US$2,646k; 16.39; +27% (+17%) | not filled (no place free or no trade) | | | -21% / +9% / -22% / -47% | +27% | -49% / +27% | |
| VZIO | Vizio Holding Corp | 2021-09-30 | US$14,837k; 21.24; +11% (+10%) | 2021-10-01 at 21.00 | 2022-03-01 at 13.51 (35% stop) | -36% | -57% / -57% / -75% / -46% | +38% | -77% / +5% | left the list 2024-12-03 (paid out) |
| SEMR | Semrush Holdings Inc | 2021-09-30 | US$5,094k; 23.06; +65% (+11%) | 2021-10-01 at 23.83 | 2022-03-01 at 13.55 (35% stop) | -43% **BIG LOSS** | -50% / -52% / -66% / -39% | +38% | -70% / +11% | left the list 2026-04-27 (paid out) |
| DOCN | Digitalocean Holdings Inc | 2021-09-30 | US$26,897k; 77.63; +83% (+11%) | 2021-10-01 at 81.07 | 2022-02-01 at 59.45 (35% stop) | -27% | -27% / -54% / -72% / -47% | +38% | -76% / +61% | listed; since buy -1% |
| ECCW | Eagle Point Credit Company Inc | 2021-09-30 | US$253k; 26.78; +11% (+8%) | not filled (no place free or no trade) | | | -1% / -8% / -5% / +14% | +38% | -12% / +15% | |
| APP | Applovin Corp | 2021-10-29 | US$71,275k; 98.25; +51% (+10%) | not filled (no place free or no trade) | | | -60% / -83% / -62% / +60% | +29% | -91% / +73% | |
| SKYT | Skywater Technology Inc | 2021-10-29 | US$7,024k; 34.24; +93% (+10%) | not filled (no place free or no trade) | | | -82% / -75% / -85% / -72% | +29% | -87% / -5% | |
| ZIP | Ziprecruiter Inc | 2021-11-30 | US$15,305k; 27.65; +31% (+9%) | 2021-12-01 at 26.94 | 2022-07-01 at 14.98 (35% stop) | -45% **BIG LOSS** | -28% / -38% / -50% / -69% | +41% | -73% / +3% | listed; since buy -76% |
| GGPIW | Gores Guggenheim Inc | 2021-11-30 | US$381k; 4.78; +624% (+10%) | not filled (no place free or no trade) | | | -52% / -100% / -100% / -100% | +41% | -64% / -3% | |
| SLDP | Solid Power Inc | 2021-11-30 | US$6,925k; 11.89; +19% (+11%) | 2021-12-01 at 11.60 | 2022-02-01 at 6.87 (35% stop) | -41% **BIG LOSS** | -23% / -70% / -87% / -91% | +41% | -91% / +16% | listed; since buy -87% |
| OWL-WS | Owl-Ws | 2021-11-30 | US$15,847k; 15.14; +54% (+10%) | 2021-12-01 at 14.76 | 2022-02-01 at 14.62 (left the list) | -1% | -1% / -1% / -1% / -1% | +41% | -2% / +8% | left the list 2021-12-17 (paid out) |
| FIGS | Figs Inc | 2021-11-30 | US$55,316k; 33.24; +11% (+9%) | 2021-12-01 at 30.89 | 2022-03-01 at 14.53 (35% stop) | -53% **BIG LOSS** | -70% / -75% / -76% / -83% | +41% | -86% / +9% | listed; since buy -31% |
| AUR | Aurora Innovation Inc | 2021-11-30 | US$4,253k; 13.12; +31% (+9%) | 2021-12-01 at 12.27 | 2022-02-01 at 5.00 (35% stop) | -59% **BIG LOSS** | -74% / -89% / -80% / -51% | +41% | -91% / +8% | listed; since buy -68% |
| FLYW | Flywire Corp | 2021-11-30 | US$12,457k; 40.64; +16% (+9%) | 2021-12-01 at 38.83 | 2022-06-01 at 19.46 (35% stop) | -50% **BIG LOSS** | -46% / -44% / -39% / -43% | +41% | -61% / +7% | listed; since buy -44% |
| MNDY | Monday.Com Ltd | 2021-12-31 | US$91,824k; 308.72; +73% (+12%) | 2022-01-03 at 301.21 | 2022-03-01 at 156.88 (35% stop) | -48% **BIG LOSS** | -64% / -63% / -41% / -25% | +29% | -75% / +8% | listed; since buy -75% |
| CFLT | Confluent Inc | 2021-12-31 | US$66,665k; 76.24; +69% (+12%) | not filled (no place free or no trade) | | | -61% / -71% / -68% / -59% | +29% | -77% / +7% | |
| DTM | Dt Midstream Inc | 2021-12-31 | US$26,003k; 47.98; +18% (+14%) | not filled (no place free or no trade) | | | +0% / +16% / +24% / +146% | +29% | -1% / +156% | |
| GHRS | Gh Research Plc | 2021-12-31 | US$1,092k; 23.33; +21% (+11%) | not filled (no place free or no trade) | | | -55% / -59% / -78% / -62% | +29% | -78% / -9% | |
| XPOF | Xponential Fitness Inc | 2022-01-31 | US$2,293k; 17.46; +45% (+3%) | 2022-02-01 at 17.47 | 2022-07-01 at 12.94 (35% stop) | -26% | -8% / +59% / -38% / +1% | +40% | -51% / +89% | listed; since buy -73% |
| DJT | Trump Media & Technology Group | 2022-03-31 | US$217,272k; 64.51; +548% (+5%) | 2022-04-01 at 63.25 | 2022-07-01 at 24.20 (35% stop) | -62% **BIG LOSS** | -71% / -78% / -36% / -74% | +15% | -81% / +5% | listed; since buy -94% |
| CLST | Catalyst Bancorp Inc | 2022-04-29 | US$65k; 13.80; +2% (-5%) | 2022-05-02 at 13.45 | 2025-06-02 at 11.85 (3-year limit) | -14% | -4% / -29% / -13% / -14% | +41% | -31% / +2% | listed; since buy +28% |
| PX | P10 Inc | 2022-04-29 | US$2,211k; 12.10; +0% (-9%) | 2022-05-02 at 12.24 | 2024-05-01 at 7.35 (35% stop) | -39% | -15% / -15% / -37% / -3% | +41% | -41% / +20% | left the list 2026-04-14 (written off) |
| AURA | Aura Biosciences Inc | 2022-05-31 | US$634k; 17.47; +18% (-10%) | 2022-06-01 at 16.41 | 2023-01-03 at 10.67 (35% stop) | -36% | -13% / -26% / -56% / -60% | +53% | -70% / +24% | listed; since buy -56% |
| LVLU | Lulu'S Fashion Lounge Holdings | 2022-05-31 | US$65k; 18.77; +44% (-11%) | 2022-06-01 at 19.68 | 2022-07-01 at 11.00 (35% stop) | -45% **BIG LOSS** | -80% / -87% / -91% / -98% | +53% | -98% / +0% | listed; since buy -98% |
| NVCT | Nuvectis Pharma Inc | 2022-08-31 | US$237k; 8.10; +149% (-12%) | 2022-09-01 at 8.11 | 2023-11-01 at 9.19 (35% stop) | +11% | +47% / +74% / -24% / -22% | +71% | -44% / +127% | listed; since buy +150% |
| CCLDO | Carecloud, Inc. | 2022-08-31 | US$90k; 25.05; +3% (-12%) | 2022-09-01 at 24.96 | 2023-11-01 at 11.84 (35% stop) | -48% **BIG LOSS** | +4% / -6% / -38% / +14% | +71% | -84% / +17% | left the list 2026-05-22 (paid out) |
| HLVX | Hillevax Inc | 2022-10-31 | US$1,074k; 21.38; +12% (-6%) | 2022-11-01 at 21.46 | 2023-09-01 at 12.93 (35% stop) | -40% **BIG LOSS** | -33% / -44% / -91% / -90% | +82% | -94% / -0% | left the list 2025-09-18 (paid out) |
| IE | Ivanhoe Electric Inc. | 2022-12-30 | US$974k; 12.15; +13% (+0%) | 2023-01-03 at 11.86 | 2023-11-01 at 10.32 (35% stop) | -14% | +17% / -15% / -38% / +39% | +88% | -60% / +43% | listed; since buy -50% |
| ECBK | Ecb Bancorp Inc. | 2023-01-31 | US$221k; 15.75; +12% (+0%) | 2023-02-01 at 15.78 | 2023-11-01 at 10.30 (35% stop) | -36% | -19% / -14% / -11% / +15% | +75% | -37% / +16% | listed; since buy +32% |
| MBLY | Mobileye Global Inc. Class A C | 2023-04-28 | US$75,094k; 37.64; +30% (+9%) | 2023-05-01 at 37.46 | 2024-02-01 at 25.80 (35% stop) | -31% | -10% / -23% / -61% / -76% | +84% | -82% / +24% | listed; since buy -86% |
| MBC | Masterbrand Inc. | 2023-06-30 | US$11,385k; 11.63; +16% (+13%) | 2023-07-03 at 11.60 | 2025-05-01 at 12.11 (35% stop) | +4% | +28% / +26% / -2% / -22% | +76% | -42% / +66% | listed; since buy -46% |
| SKWD | Skyward Specialty Insurance Gr | 2023-07-31 | US$3,520k; 23.69; +58% (+15%) | 2023-08-01 at 23.80 | 2026-09-01 at 57.42 (3-year limit) | +140% **BIG WIN** | +31% / +62% / +102% / +176% | +75% | -2% / +176% | listed; since buy +167% |
| NXT | Nextpower Inc. | 2023-08-31 | US$42,635k; 42.12; +38% (+10%) | 2023-09-01 at 43.13 | 2025-01-02 at 39.50 (35% stop) | -9% | +32% / -13% / +62% / +91% | +75% | -27% / +263% | listed; since buy +82% |
| ZJYL | Jin Medical International Ltd. | 2023-09-29 | US$868k; 23.40; +194% (+8%) | 2023-10-02 at 23.36 | 2023-11-01 at 8.89 (35% stop) | -62% **BIG LOSS** | +175% / +123% / -51% / -91% | +89% | -92% / +1082% | listed; since buy -86% |
| CLCO | Cool Company Ltd | 2023-09-29 | US$1,102k; 13.85; +10% (+9%) | 2023-10-02 at 13.24 | 2025-03-03 at 5.90 (35% stop) | -48% **BIG LOSS** | -7% / -3% / -16% / -15% | +89% | -59% / +8% | left the list 2026-01-08 (paid out) |
| ISPR | Ispire Technology Inc. Common  | 2023-10-31 | US$332k; 7.93; +5% (+2%) | 2023-11-01 at 8.16 | 2024-04-01 at 5.99 (35% stop) | -28% | -31% / -30% / -78% / -81% | +80% | -87% / +100% | listed; since buy -81% |
| PTHR | Pono Capital Three, Inc. Class | 2023-10-31 | US$73k; 10.59; +4% (+2%) | 2023-11-01 at 10.59 | 2024-02-01 at 2.37 (35% stop) | -100% **BIG LOSS** | -100% / -100% / -100% / -100% | +80% | -78% / +0% | left the list 2024-01-17 (written off) |
| FTRE | Fortrea Holdings Inc. | 2023-12-29 | US$34,095k; 34.90; +16% (+8%) | 2024-01-02 at 34.46 | 2024-06-03 at 24.85 (35% stop) | -28% | -32% / -46% / -49% /  |  | -88% / +17% | listed; since buy -41% |
| APGE | Apogee Therapeutics, Inc. Comm | 2024-01-31 | US$5,554k; 33.50; +97% (+7%) | 2024-02-01 at 33.99 | 2024-07-01 at 38.58 (35% stop) | +13% | +30% / +19% / +83% /  |  | -15% / +297% | left the list 2026-09-03 (paid out) |
| FEBO | Fenbo Holdings Limited Ordinar | 2024-06-28 | US$85k; 14.21; +220% (+20%) | 2024-07-01 at 16.38 | 2024-09-03 at 6.45 (35% stop) | -61% **BIG LOSS** | -90% / -93% / -95% /  |  | -97% / -0% | listed; since buy -97% |
| CORZ | Core Scientific, Inc. Common S | 2024-07-31 | US$15,527k; 9.75; +183% (+13%) | 2024-08-01 at 9.46 | 2025-03-03 at 10.14 (35% stop) | +7% | +30% / +49% / +123% /  |  | -32% / +208% | listed; since buy +49% |
| LPA | Logistic Properties Of The Ame | 2024-09-30 | US$795k; 9.57; +43% (+10%) | 2024-10-01 at 9.49 | 2025-05-01 at 6.80 (35% stop) | -30% | -15% / -54% / -68% /  |  | -76% / +38% | listed; since buy -76% |
| PACS | Pacs Group, Inc. | 2024-10-31 | US$12,739k; 42.68; +86% (+10%) | 2024-11-01 at 42.94 | 2024-12-02 at 15.90 (35% stop) | -63% **BIG LOSS** | -76% / -70% / +16% /  |  | -82% / +17% | listed; since buy +8% |
| ULS | Ul Solutions Inc. | 2024-10-31 | US$21,731k; 51.96; +50% (+11%) | 2024-11-01 at 51.60 | 2026-10-01 at 66.50 (35% stop) | +30% | +36% / +68% / +55% /  |  | -5% / +106% | listed; since buy +51% |
| LB | Landbridge Company Llc | 2024-12-31 | US$15,509k; 64.60; +179% (+8%) | 2025-01-02 at 64.80 | 2026-11-13 at 73.15 (still held 13 Nov 2026) | +14% | -2% / -29% /  /  |  | -31% / +40% | listed; since buy +11% |
| GRAL | Grail, Llc | 2024-12-31 | US$12,019k; 17.85; +31% (+8%) | 2025-01-02 at 17.92 | 2025-09-02 at 31.61 (35% stop) | +76% | +139% / +480% /  /  |  | -3% / +787% | listed; since buy +470% |
| SW | Smurfit Westrock Plc | 2025-01-31 | US$167,121k; 53.09; +16% (+8%) | 2025-02-03 at 53.52 | 2026-11-13 at 42.35 (still held 13 Nov 2026) | -15% | -16% / -14% /  /  |  | -36% / +4% | listed; since buy -18% |
| CURB | Curbline Properties Corp. | 2025-03-31 | US$12,406k; 24.19; +24% (-2%) | 2025-04-01 at 24.69 | 2026-11-13 at 29.15 (still held 13 Nov 2026) | +22% | -8% / +9% /  /  |  | -13% / +33% | listed; since buy +22% |
| FTW | Presidio Production Company | 2025-04-30 | US$282k; 10.18; +3% (-3%) | 2025-05-01 at 10.20 | 2026-11-13 at 10.45 (still held 13 Nov 2026) | +5% | +2% / +7% /  /  |  | -3% / +36% | listed; since buy +5% |
| SOBO | South Bow Corporation | 2025-04-30 | US$15,822k; 24.69; +15% (-2%) | 2025-05-01 at 24.91 | 2026-11-13 at 33.32 (still held 13 Nov 2026) | +47% | +8% / +51% /  /  |  | -1% / +69% | listed; since buy +44% |
| KYIV | Kyivstar Group Ltd. Common Sha | 2025-06-30 | US$3,570k; 10.97; +10% (+3%) | 2025-07-01 at 10.85 | 2026-11-13 at 12.47 (still held 13 Nov 2026) | +14% | +17% / +45% /  /  |  | -14% / +49% | listed; since buy +8% |
| MRLN | Merlin, Inc. | 2025-06-30 | US$130k; 10.31; +5% (+3%) | 2025-07-01 at 10.31 | 2026-07-01 at 5.65 (35% stop) | -46% **BIG LOSS** | +4% / -49% /  /  |  | -92% / +56% | listed; since buy -92% |
| TTAN | Servicetitan, Inc. Class A Com | 2025-06-30 | US$43,501k; 107.18; +51% (+2%) | 2025-07-01 at 109.26 | 2026-03-02 at 74.68 (35% stop) | -32% | -2% / -28% /  /  |  | -50% / +9% | listed; since buy -25% |
| YSXT | Ysx Tech. Co., Ltd Class A Ord | 2025-06-30 | US$211k; 5.43; +26% (+6%) | 2025-07-01 at 5.41 | 2025-08-01 at 2.99 (35% stop) | -46% **BIG LOSS** | -76% / -78% /  /  |  | -87% / +2% | listed; since buy -78% |
| AAPG | Ascentage Pharma Group Interna | 2025-07-31 | US$463k; 37.00; +113% (+4%) | 2025-08-01 at 37.20 | 2026-01-02 at 26.37 (35% stop) | -31% | -38% / -55% /  /  |  | -65% / +29% | listed; since buy -65% |
| CEPO | Cantor Equity Partners I, Inc. | 2025-07-31 | US$1,691k; 10.95; +9% (+7%) | 2025-08-01 at 10.90 | 2026-11-13 at 10.82 (still held 13 Nov 2026) | -1% | -4% / -2% /  /  |  | -19% / +2% | listed; since buy -1% |
| SFD | Smithfield Foods, Inc. Common  | 2025-07-31 | US$12,133k; 24.12; +25% (+4%) | 2025-08-01 at 24.32 | 2026-11-13 at 19.19 (still held 13 Nov 2026) | -15% | +2% / +9% /  /  |  | -21% / +26% | listed; since buy -15% |
| PUSA | Powerus Corporation | 2025-08-29 | US$138k; 4.34; +12% (+7%) | 2025-09-02 at 3.91 | 2026-01-02 at 2.95 (35% stop) | -26% | +28% / -2% /  /  |  | -66% / +100% | listed; since buy -66% |
| SION | Sionna Therapeutics, Inc. Comm | 2025-08-29 | US$2,156k; 24.62; +37% (+6%) | 2025-09-02 at 25.39 | 2026-09-01 at 6.46 (35% stop) | -75% **BIG LOSS** | +36% / -71% /  /  |  | -88% / +101% | listed; since buy -88% |
| CRWV | Coreweave, Inc. Class A Common | 2025-09-30 | US$2,297,823k; 136.85; +242% (+20%) | 2025-10-01 at 137.05 | 2025-12-01 at 77.06 (35% stop) | -44% **BIG LOSS** | -40% / -35% /  /  |  | -68% / +4% | listed; since buy -65% |
| HNGE | Hinge Health, Inc. | 2025-11-28 | US$42,554k; 48.91; +30% (+17%) | 2025-12-01 at 47.96 | 2026-11-13 at 115.39 (still held 13 Nov 2026) | +139% **BIG WIN** | +22% /  /  /  |  | -35% / +157% | listed; since buy +139% |
| CV | Capsovision, Inc. Common Stock | 2025-12-31 | US$143k; 10.69; +205% (+10%) | 2026-01-02 at 10.24 | 2026-02-02 at 5.47 (35% stop) | -48% **BIG LOSS** | -45% /  /  /  |  | -55% / -15% | listed; since buy -33% |
| EMPG | Empro Group Inc. Ordinary Shar | 2025-12-31 | US$291k; 17.36; +299% (+10%) | 2026-01-02 at 17.36 | 2026-09-01 at 17.36 (left the list) | -2% | +0% /  /  /  |  | +0% / +0% | left the list 2026-08-03 (paid out) |
| AMBQ | Ambiq Micro, Inc. | 2026-01-30 | US$4,313k; 30.39; +27% (+9%) | 2026-02-02 at 30.84 | 2026-11-02 at 43.31 (35% stop) | +40% | +119% /  /  /  |  | -23% / +193% | listed; since buy +49% |
| ANPA | Rich Sparkle Holdings Limited  | 2026-01-30 | US$382k; 83.00; +2258% (+11%) | 2026-02-02 at 77.00 | 2026-03-02 at 9.95 (35% stop) | -87% **BIG LOSS** | -95% /  /  /  |  | -99% / +6% | listed; since buy -98% |
| FIGR | Figure Technology Solutions, I | 2026-03-31 | US$124,673k; 33.95; +9% (-1%) | 2026-04-01 at 32.89 | 2026-11-02 at 21.79 (35% stop) | -34% | -13% /  /  /  |  | -36% / +32% | listed; since buy -21% |
| LBRX | Lb Pharmaceuticals Inc Common  | 2026-03-31 | US$3,898k; 24.66; +43% (-1%) | 2026-04-01 at 24.81 | 2026-11-13 at 43.01 (still held 13 Nov 2026) | +72% | +50% /  /  /  |  | -2% / +99% | listed; since buy +61% |
| MPLT | Maplight Therapeutics, Inc. Co | 2026-04-30 | US$3,766k; 31.87; +74% (+5%) | 2026-05-01 at 30.70 | 2026-08-03 at 12.55 (35% stop) | -59% **BIG LOSS** | -75% /  /  /  |  | -80% / +30% | listed; since buy -78% |
| Q | Qnity Electronics, Inc | 2026-04-30 | US$207,000k; 140.66; +48% (+5%) | 2026-05-01 at 143.33 | 2026-11-13 at 118.36 (still held 13 Nov 2026) | -18% | -19% /  /  /  |  | -24% / +23% | listed; since buy -19% |
| MICC | The Magnum Ice Cream Company N | 2026-06-30 | US$20,927k; 17.41; +17% (+10%) | 2026-07-01 at 18.09 | 2026-11-13 at 19.90 (still held 13 Nov 2026) | +9% |  /  /  /  |  | -6% / +13% | listed; since buy +8% |
| AGLT | Agility Robotics, Inc. | 2026-08-31 | US$182k; 13.38; +30% (+10%) | 2026-09-01 at 13.05 | 2026-11-02 at 9.29 (35% stop) | -29% |  /  /  /  |  | -48% / +6% | listed; since buy -48% |
| MPTI-R | Mpti-R | 2026-08-31 | US$8,101k; 76.16; +16% (+12%) | 2026-09-01 at 74.87 | 2026-11-13 at 64.43 (still held 13 Nov 2026) | -14% |  /  /  /  |  | -23% / +6% | listed; since buy -10% |
| MPTI-R-W | Mpti-R-W | 2026-08-31 | US$8,101k; 76.16; +16% (+12%) | 2026-09-01 at 74.87 | 2026-11-13 at 64.43 (still held 13 Nov 2026) | -14% |  /  /  /  |  | -23% / +6% | listed; since buy -10% |
| VGNT | Versigent Plc | 2026-09-30 | US$45,617k; 44.94; +49% (+20%) | 2026-10-01 at 46.26 | 2026-11-13 at 42.19 (still held 13 Nov 2026) | -9% |  /  /  /  |  | -13% / +2% | listed; since buy -8% |
| ALMR | Alamar Biosciences, Inc. Commo | 2026-10-30 | US$7,313k; 30.60; +80% (+8%) | 2026-11-02 at 28.94 | 2026-11-13 at 30.81 (still held 13 Nov 2026) | +6% |  /  /  /  |  | -7% / +10% | listed; since buy +5% |
| PS | Pershing Square Inc. | 2026-10-30 | US$9,977k; 45.66; +91% (+6%) | 2026-11-02 at 46.62 | 2026-11-13 at 44.71 (still held 13 Nov 2026) | -5% |  /  /  /  |  | -13% / +13% | listed; since buy -13% |


## 7. How much unseen data would be needed

- **Per pick.** The 12-month result of a pick relative to the fund has a spread (standard deviation) of about 70–80 points. To show an average edge of +10 points at t = 2 takes about (2 × 75 ÷ 10)² ≈ **225 unseen purchases**; at t = 3 about 500. Unseen ASX purchases so far: 6 (5 with a 12-month result). The ASX gave about 5 a year in 2001–2012, 8 a year in 2013–2022 and 2 a year since 2023. **30 to 100 years.**
- **The book against the fund.** t = lead ÷ tracking error × √years. ASX tracking error was 7.3 (2001–12), 12.7 (2013–22) and 3.8 (2023–26, only six holdings). A true lead of +2 a year needs 53–160 years for t = 2; a true +5 needs 9–26 years for t = 2 and 19–58 for t = 3.
- **The signal spread of rule v3.** Yearly spread about +8 points with a year-to-year spread of 25: t = 2 needs about 40 years of that; if the true spread were +20, about 6 years.
- **Pooling markets was the only way to get an answer in less than a decade, and the answer it gave is no:** three markets, 63 purchases, 8.4 years, t = −2.05; four markets with the US sample, 190 purchases, mean lead −4.0 a year, t = −1.06.
- What the forward paper line can do: trigger rule v3's stop (spread t ≤ −1.0, or below the 20th percentile of its twins) from its 13th month. It cannot reach P2 on ASX listings alone before the 2030s at the earliest, and most likely never.

## 8. Deviations, limits, and what could be wrong

1. **Canada start year.** The count rule in `PREREG_86` gives 2017. The quarterly counts showed that about 250 "first rows" in 2017 are old companies whose stored history starts that year, so the primary test was set to 2018 in `PREREG_86b` before any return was computed. The 2017 window is reported (−3.3) and counted as an extra trial.
2. **Classification looks ahead a little.** Overseas, company names are the vendor's latest names, and the resources and fund filters work on names. Spin-offs, cross-listings of foreign companies and some trusts are treated as new listings. This is a real difference from the ASX line, which uses the new-listings tracker's classification. It makes the overseas tests a test of the *rule*, not of the exact ASX universe.
3. **Vendor data errors.** Unit errors (prices 100× out for a period) survive in a few overseas histories. A fixed gate keeps any company with such a move *before* the decision out of the purchases and the random pool; errors *after* a decision can inflate a random book (the median random Canadian book over 2005+ shows +11 a year for that reason) and the "rejected: average" columns. The picks' own paths were read line by line in section 6; none shows a unit error. One vendor duplicate is among the Canadian picks: Brookfield Reinsurance appears under its old and new codes (BAMR, BNT) and was bought twice on the same day (both −41%); dropping one changes nothing material. The percentile figures for the primary windows are not driven by this: the rule's book is also below the *median* random book (−4.6 against −3.1; −5.7 against −4.8).
4. **Delisting cash is a heuristic** (paid out if the last price was within 30% of the one-year high, else zero). Both extremes are in section 3; the sign never changes.
5. **Currency ignored**: each book is measured against its local fund in local currency. Tax is the Australian model throughout.
6. **Two bad markets are still one episode.** Most of the Canadian and UK damage is the 2021 listings boom and the 2022 fall. Of the 63 unseen purchases, 25 were decided in 2021 (typical result −39%) and 8 in 2022 (−46%). The ASX had the same boom: its 15 picks of 2021–2022 in the re-model typically lost 33% and 4 made money (section 6). It is evidence that the rule buys heavily at listing-boom peaks, which is a property of the rule, not an accident.
7. **The ASX unseen period was not perfectly unseen**: report 84 printed its total (6 purchases, +2.0) after the rule was chosen. Nothing was changed after seeing it.
8. **US sample.** One symbol in three (chosen by a hash of the code, fixed in advance), listings from 2017 by the count rule (`PREREG_86c`, hashed before the run). 226 companies passed but only 127 were bought: the 25 places were full in 2020–2021. Companies that listed by merging with a SPAC carry the SPAC's listing date, so some picks are SPACs at about US$10 (the name filter removes only SPACs that never merged); three of them (ArcLight, GS Acquisition II, Landcadia III) are shown as "written off" when the code changed at the merger, which is the delisting heuristic being wrong, not a real loss. With every delisting paid out instead the US lead is −8.4 rather than −8.8; the sign does not depend on it. The US was run after the Canadian and UK results were known; its rules were not changed by them.

## 9. Trial count

Ledger N = **1,796** at seq 39 (read 19 Nov 2026). This study adds: ASX unseen (1), Canada 2018+ (1), Canada 2017+ variant (1), UK 2021+ (1), pooled reading (1), US sample (1) = 6 → **N = 1,802**. The ASX re-model, the secondary windows fixed in advance and the robustness runs are the same rule on data already counted or on supersets, and are not counted. For the record keeper to enter; this report does not write the ledger. Verdict for all lines unchanged: **not shown to beat the index.**

## 10. Files

- `86_case_table_all_picks.csv` (beside this report): every pick in every window with the numbers behind section 6 (the US 2005+ window's 524 passes are in this file only).
- `scratchpad/deep86/PREREG_86.md`, `PREREG_86b.md`, `RULES_Y1-Y9_frozen.md`, `out/prereg86_hash.txt`.
- `scratchpad/deep86/code/`: `early_ref.py` (frozen), `lib86.py` (as-of replay, controls, cases), `asx86.py`, `mk86.py` (vendor markets), `ovs86.py`, `y0.py`, `pool86.py`, `casetab.py`.
- `scratchpad/deep86/out/`: `<set>_decisions.csv` (every company looked at, pass or fail and why, with its later 6/12/24/36-month outcome), `<set>_cases.csv`, `<set>_nav.csv`, `<set>_res.json`.
