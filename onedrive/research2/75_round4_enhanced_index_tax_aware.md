# 75. Round 4 — enhanced index, tax-aware selling and core-satellite: nine more fresh markets, none beat the index

17 November 2026. Research and paper only. General information, not financial or tax advice. Nothing here can place an order.
Work folder: `scratchpad/improve4/` (`PREREG_75_R1.md`, `_R2.md`, `_R3.md`, `cands_extra.json`, `code/`, `out/`, `PROGRESS.md`). Trial ledger: `out/trials_75.csv` (cumulative count 951 → 1,197). Nothing was written to `68_forward_record/` or `bigwins_forward/`.

## 0. Plain-English verdict

**Question.** Rounds 1–3 changed the share-picking signal and lost. Does changing the *structure* (weights that follow the index, the index fund as the core, tax-aware selling) turn the same picking skill into a lead over a cheap index fund, after costs and Australian tax?

**Answer: no. Three structural designs were frozen and each was given one look at three markets never used before. None passed. All nine remaining fresh markets on the data plan are now used up.**

1. **How it was tested.** Each design was built only on ASX 2001–2015 and US 2001–2013, written down and hashed, then run once on fresh markets: Netherlands, Korea, Brazil (round 1); Denmark, Spain, Switzerland (round 2); South Africa, Norway, Taiwan (round 3). Window 29 Dec 2017 – 30 Oct 2026. The benchmark is a real, listed local index fund in each market. Bar (unchanged from report 73): a lead of at least 1 point a year after costs and tax at both A$25,000 and A$100,000 in two of the three markets, with no market worse than −2.
2. **Result.** The lead met the bar in **1 of 3, 1 of 3 and 0 of 3** markets. Every round also had cells below −2.

| Round | Design | Lead over the local fund, points a year after tax (A$25k / A$100k) | Verdict |
|---|---|---|---|
| 1 | **EI** enhanced index: the 50 most-traded shares at index-like weights, minus trend laggards, with loss harvesting | Netherlands +2.6 / +1.5; Korea −5.8 / −2.4; Brazil +0.1 / −1.6 | fail |
| 2 | **CSL** core-satellite: 50% index fund + the 15 best trend names among the 100 most traded | Denmark +1.2 / +2.7; Spain −2.4 / +0.7; Switzerland −3.2 / −2.1 | fail |
| 3 | **EI2**: EI allowed up to 20 names at A$25,000 | South Africa −3.0 / −1.6; Norway −4.2 / −2.7; Taiwan −5.4 / −4.5 | fail |

3. **What came closest.** Half (or 30%) in the index fund plus a short list of the strongest-trend large companies. Over all nine markets it averaged +0.3 to +0.8 points a year, but that average includes markets the design had already seen. Counting only markets that were fresh for it, CSL averaged **−0.2**. It beat the bar in 4 of 9 markets and was below −2 in 3 of 9. That is a coin toss, not an edge.
4. **Enhanced index did not work as hoped, for a reason that cannot be fixed with the data on hand.** No legal point-in-time source of share counts exists on the plan outside Australia (the vendor refuses both fundamentals and historical market cap). Traded value had to stand in for market cap. A book weighted that way with *no* picking trails the fund by about 2 points a year on ASX. With the trend filter added, the nine-market average was −1.5. At A$25,000 the book holds about ten names and cannot follow an index (−5.8 in Korea).
5. **Tax-aware selling helps a little and is not a source of return in Australia.** Harvesting losses and holding winners past 12 months added about **+0.5 point a year** to the plain engine (E3) and **0.0** to the core-satellite design. The US studies that report about 1 point a year assume the investor has other gains taxed at a higher rate to absorb the losses. An Australian investor whose only gains are in this account just pays the same tax later.
6. **The index funds were hard to beat for the same reason as before.** Korea's fund earned 14% a year after tax and Taiwan's 22%, on two or three very large companies. Any book that holds less of them than the index falls behind, whatever it picks.
7. **The picking signal is real, again.** Trend quality sorted shares in all nine markets (t between 1.3 and 4.0; above 2.9 in six). Skill is not the missing piece. The conversion of skill into an after-tax lead over a cap-weighted fund is.
8. **The owner's account (A$5,000 + A$500 a month, A$57,500 paid in).** Every design starts in the index fund and switches on at A$25,000. EI finished behind the fund in 8 of 9 markets. CSL finished ahead in 6 of 9 (for example A$165k against A$143k in Korea) and behind in 3 (A$183k against A$200k in Taiwan); three of the six wins were markets it was tuned on.
9. **Account size.** Below A$25,000: index fund only. Core-satellite works mechanically from A$25,000 (five or more names of A$2,500). A direct enhanced index needs about A$50,000 for 20 names and A$250,000 or more for 40–50 names at real index weights. Brokerage of A$3 instead of A$6.60 moves results by 0.0–0.3 points.
10. **Data errors were found and fixed before any look.** (a) The vendor lists the South African index fund's distributions twice, which overstated that fund's return by about 3 points a year. (b) Three benchmark funds reinvest or pay lumpy distributions; a normal dividend was imputed so that fund and shares are taxed alike (without it the fund is under-taxed by about 0.5 point a year). (c) Placeholder prices, the same company under two codes, unrecorded splits and vendor garbage days were removed. Unlike report 73's errors, (a) and (c) had worked *against* the engine; they were fixed on data facts alone, before any engine return was computed, and the engine still failed.
11. **Against the 40/60 plan.** Nothing here changes report 73's conclusion. Real money stays in the plan.
12. **Confidence.** High that none of these designs clears the bar: twenty fresh market sets across four rounds, 1,197 counted trials, the same answer each time. The remaining untested idea is a true cap-weighted direct index with real share counts on ASX (ASIC "Total Product in Issue", 2010+), which cannot be validated on fresh data because ASX after 2015 is spent.

---

## 1. What was done

| Step | What | Counted trials |
|---|---|---|
| Engine | `code/sim4.py` = report 73's `sim.py` (reproduced to the cent, `code/reg.py`) plus: targets weighted by a market-cap proxy and normalised over the names held, weight cap, May loss harvest, purchase bar after a loss sale, no-gain-sale-before-12-months switch, A$3 brokerage tier, imputed fund distributions | — |
| Development | ASX 2001–15 and US 2001–13 (declared development): universe size, weighting, tilt, harvest, deferral, core weight, account size (`out/dev1.log`–`dev6.log`); includes 7 for the machinery test | 100 |
| Fresh data | Nine exchanges downloaded (6,800 series, live and dead), cleaned, checked for coverage and for errors before any engine return (`out/coverage_*.csv`, `out/qa*.log`) | 0 |
| Round 1 | EI frozen (`out/prereg75_R1_hash.txt`, N = 1,051); one look at AS, KO, SA; four descriptive designs beside it | 15 + 12 |
| Round 2 | Design step on ASX + round-1 sets (16); CSL frozen (N = 1,094); one look at CO, MC, SW; six descriptive designs | 16 + 21 + 12 |
| Round 3 | Design step on ASX + six sets (13); EI2 frozen (N = 1,140); one look at JSE, OL, TW; eight descriptive designs | 13 + 27 + 12 |
| After | Every design on every set for the ranking table (18 cells computed after the fact, marked ~) | 18 |

Cumulative count for the deflated Sharpe ratio: **1,197**.

## 2. The designs

All use the trend-quality score of report 73 (t-statistic of the 12-month log-price slope), month-end decisions, next-day-close execution, the owner's cost schedule and 32% tax.

| | EI / EI2 (enhanced index, direct) | CSL / CSLt / CSL30 (core-satellite, large companies) | CS50 / CS70 (core + E3) | TA | E3 |
|---|---|---|---|---|---|
| Index fund share | 0 | 50% (CSL30: 30%) | 50% / 70% | 0 | 0 |
| Share universe | 50 most traded (held while rank ≤ 75) | 100 most traded (held while ≤ 150) | 300 most traded | 300 | 300 |
| Buy | not below trend rank 35; largest weights first | trend rank ≤ 15 | rank ≤ 30 | rank ≤ 30 | rank ≤ 30 |
| Sell | two months below rank 42 | two months below rank 50 | two months below 200 | as E3 | two months below 200 |
| Weights | traded-value share over the names held, cap 20% | equal | equal | equal | equal |
| Names | up to 30; position ≥ A$2,500 (EI2: ≥ A$1,250) | up to 30 of A$2,500+ | same | same | same |
| Tax-aware rules | May loss harvest against realised gains; 6-month purchase bar after a loss sale; winners 300–365 days old wait | CSLt only: harvest, bar, no sale at a gain before 12 months | none beyond E3's | harvest, bar, no sale at a gain before 12 months | 12-month wait for winners near the mark; May loss sale |
| Small account | fund until A$25,000, then sold and replaced | fund until A$25,000, then sold down to the core weight | same | as EI | as EI |

**Weight proxy, and why not real market cap.** EODHD answers "Forbidden" for fundamentals and for historical market capitalisation. ASIC's "Total Product in Issue" gives legal daily share counts for ASX from 2010, but ASX after 2015 is spent and 2010–2015 is too short. The proxy used everywhere is the median daily traded value over 252 days (adjusted close × volume, report 74's correction). In the fresh markets the largest proxy weights are the real index heavyweights (ASML 19–32%, Samsung 18–30%, Novo 18–38%, TSMC 12–25%, Nestlé/Roche/Novartis 12–14% each). A live ASX version could use ASIC share counts × price, or the fund's published holdings.

## 3. Development (ASX 2001–15 and US 2001–13)

After-tax lead over the fund, points a year, A$25k / A$100k, mean of four start months.

| Variant | ASX | US large | US mid | US small | Note |
|---|---|---|---|---|---|
| E3 (reference) | +4.5 / +2.9 | +2.9 / +2.0 | +2.2 / −1.3 | −5.6 / −3.4 | mean +0.5 |
| E3 structure, random scores | −2.5 / −3.4 | −4.1 / −2.6 | −3.6 / −4.6 | −1.5 / −1.8 | the structure alone costs 3 points |
| E3 + harvest + 12-month deferral | +5.4 / +2.7 | +3.1 / +1.9 | +2.1 / +0.3 | −6.3 / −3.9 | +0.1 with a real signal; +1.0 with random picks |
| 70% fund + E3 | +2.9 / +1.5 | +1.2 / +0.4 | +0.8 / +0.6 | −1.3 / −1.4 | mean +0.6 |
| 50% fund + E3 (CS50) | +3.9 / +1.8 | +0.4 / +1.3 | +2.1 / +0.3 | −1.1 / −1.7 | mean +0.9 |
| Direct index on the proxy, no signal, 50 names | −1.6 / −1.8 | −6.9 / −5.4 | | | US set has vendor rows with absurd traded value (YRCW, warrants): not valid for weighted designs |
| EI | +0.7 / +0.8 | (invalid) | | | random scores: −1.5 / −1.2 |
| E3 with A$3 brokerage | +4.7 / +2.8 | +2.9 / +2.0 | +2.5 / −1.2 | −5.2 / −3.2 | +0.1 |

Account size on ASX development (EI): A$5k −4.8, A$10k −2.4, A$25k +0.7, A$50k +0.5, A$100k +0.8, A$250k +1.0, A$500k +1.0. Each pre-registration stated in advance that the expected fresh result was about zero.

## 4. Fresh markets: data, benchmarks, coverage

| Set | Market | Benchmark fund | Fund after tax, % a year (A$100k) | Dead companies in the file | Flag |
|---|---|---|---|---|---|
| AS | Netherlands | iShares AEX (IAEX) | 9.8 | 3–12% a year from 2017 | |
| KO | Korea (KOSPI) | KODEX 200 (069500) | 14.1 | 1.3–4% from 2018 | thin |
| SA | Brazil | iShares Ibovespa (BOVA11), distribution imputed | 8.0 | 3–10% from 2017 | preferred lines (PETR4, ITUB4) absent from the vendor's common-stock list |
| CO | Denmark | Sparindex OMX C25 (SPIC25KL), distribution imputed | 7.1 | 9–30% from 2018 | many renamed or fund lines |
| MC | Spain | Lyxor IBEX 35 (LYXIB) | 10.3 | 2–8% from 2017 | |
| SW | Switzerland | iShares SMI (CSSMI) | 7.8 | 2–8% from 2017 | |
| JSE | South Africa | Satrix 40 (STX40), total return rebuilt | 10.3 | 4–9% from 2018 | |
| OL | Norway | DNB OBX (OBXD), distribution imputed | 9.7 | 3–16% from 2017 | |
| TW | Taiwan | Yuanta Taiwan 50 (0050) | 22.4 | 0.4–2% from 2017 | thin |

Before 2017 none of the nine has dead companies in the file, so earlier years were not used. Prices were rescaled by one constant per exchange to A$-like units so that minimum brokerage, whole shares and liquidity tests mean the same as on ASX. Fund fee set to zero (favours the fund).

**Errors found before any look** (`out/qa.log`, `qa2.log`, `qa3.log`, `out/mk_*.log`):

| Error | Size | Direction if left in | Fix |
|---|---|---|---|
| STX40.JSE: 31 of 70 distributions listed twice | fund total return +3 points a year | against the engine | total return rebuilt from close and de-duplicated distributions |
| BOVA11, OBXD accumulate; SPIC25KL pays lumpy gains distributions | fund pays no yearly dividend tax | against the engine, about 0.5 | a distribution equal to the traded-value-weighted yield of the 30 most-traded companies is imputed and taxed |
| Placeholder closes (SIMH3 = 1,000,000 for ten years, 93–97% of "traded value") | one company would be the whole weighted book | either | runs of ≥ 120 identical closes with volume deleted |
| Vendor garbage days (Taiwan 29 Sep 2025 and five other dates; prices ×10–×100 with zero volume) | fake gains and losses | either | bad-tick window widened to 30 rows |
| Unrecorded splits (Georg Fischer 1:20, Wiwynn 3:1, Isu Specialty 5:1 and about 300 in Korea/Taiwan) | fake −67% to −95% for a holder | against the engine | removed (rule in `PREREG_75_R1.md` §4) |
| Same company under old and new code (34 in Norway, 22 in Brazil, SIK/SIKA, BVMF3/B3SA3 …) | a company counted twice | either | the dead line is dropped |
| Taiwan ETFs and a mis-mapped Alibaba line; Brazilian depositary receipts and property funds typed as common stock | wrong universe | either | excluded by code rule |
| Split factor applied where the vendor had not adjusted volume | wrong traded value | either | factor used only if it makes close × volume more continuous |

## 5. Results

X = after-tax return of the design minus after-tax return of the local fund, points a year, mean of four start months. CL = current law (50% discount after 12 months); AN = announced July-2027 design (indexation, no discount). "Random pct" = percentile among 100 runs of the same structure with random scores, after tax. Franking does not exist outside Australia. \* = the design eligible in that round.

### 5.1 The three pre-registered looks

| Round | Cand | Set | X_CL 25k | X_CL 100k | X_AN 25k | X_AN 100k | X before tax 25k/100k | eng/fund after tax 100k | random pct 25k/100k | top5 100k | TE 100k | t | DSR | maxDD eng/fund | turnover | names 25k/100k | life engine / fund (paid in) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | EI* | AS | +2.6 | +1.5 | +1.6 | +1.0 | +2.6 / +3.0 | 11.4 / 9.8 | 81 / 91 | 87% | 5.4 | 2.3 | 0.16 | -19 / -20 | 0.42 | 10 / 21 | 93.0k / 95.5k (57.5k) |
| R1 | EI* | KO | -5.8 | -2.4 | -4.1 | -2.3 | -5.5 / -0.3 | 11.7 / 14.1 | 62 / 82 | 101% | 10.1 | 0.5 | 0.00 | -35 / -34 | 0.57 | 12 / 27 | 115.0k / 143.4k (57.5k) |
| R1 | EI* | SA | +0.1 | -1.6 | -0.7 | -2.0 | -0.4 / -1.0 | 6.3 / 8.0 | 85 / 34 | 172% | 9.2 | -0.7 | 0.00 | -35 / -38 | 0.44 | 14 / 27 | 75.6k / 81.8k (57.5k) |
| R2 | CSL* | CO | +1.2 | +2.7 | +1.2 | +2.2 | +2.9 / +3.1 | 9.8 / 7.1 | 98 / 100 | 50% | 5.0 | 1.8 | 0.07 | -27 / -26 | 0.31 | 8 / 18 | 96.8k / 76.1k (57.5k) |
| R2 | CSL* | MC | -2.4 | +0.7 | -2.2 | +0.5 | -2.3 / +1.0 | 11.0 / 10.3 | 75 / 100 | 63% | 7.2 | 0.5 | 0.00 | -25 / -33 | 0.34 | 5 / 20 | 100.7k / 115.2k (57.5k) |
| R2 | CSL* | SW | -3.2 | -2.1 | -3.1 | -2.2 | -2.9 / -2.3 | 5.7 / 7.8 | 24 / 74 | 165% | 4.8 | -1.0 | 0.00 | -30 / -18 | 0.33 | 4 / 19 | 77.2k / 83.2k (57.5k) |
| R3 | EI2* | JSE | -3.0 | -1.6 | -3.2 | -1.6 | -2.9 / -1.1 | 8.7 / 10.3 | 68 / 58 | 77% | 6.2 | -0.5 | 0.00 | -20 / -20 | 0.46 | 17 / 28 | 93.4k / 98.5k (57.5k) |
| R3 | EI2* | OL | -4.2 | -2.7 | -4.4 | -3.0 | -4.1 / -2.4 | 7.0 / 9.7 | 43 / 26 | 88% | 7.7 | -0.4 | 0.00 | -27 / -26 | 0.46 | 14 / 26 | 88.8k / 99.8k (57.5k) |
| R3 | EI2* | TW | -5.4 | -4.5 | -5.1 | -4.2 | -4.5 / -1.6 | 17.9 / 22.4 | 80 / 51 | 54% | 14.0 | 0.2 | 0.00 | -43 / -29 | 0.72 | 21 / 29 | 163.8k / 200.4k (57.5k) |

| Bar | Round 1 (EI) | Round 2 (CSL) | Round 3 (EI2) |
|---|---|---|---|
| X_CL ≥ +1.0 at both sizes in two of three sets | 1 of 3 | 1 of 3 | 0 of 3 |
| No set below −2.0 at either size | fail (Korea) | fail (Spain, Switzerland) | fail (all three) |
| X_AN > 0 at both sizes in two of three | 1 of 3 | 1 of 3 | 0 of 3 |
| ≥ 90th percentile of random-score runs at both sizes, two of three | 0 of 3 | 1 of 3 | 0 of 3 |
| Top five positions < 50% of profit (A$100k), two of three | 0 of 3 | 1 of 3 | 0 of 3 |
| Deflated Sharpe at N ≈ 1,100–1,200 (need ≥ 0.95) | 0.16, 0.00, 0.00 | 0.07, 0.00, 0.00 | 0.00, 0.00, 0.00 |
| **Verdict** | **fail** | **fail** | **fail** |

All 63 look rows (eligible and descriptive, with drawdown, turnover, tracking error and lifecycle): `improve4/out/summary_table.md`.

### 5.2 Every design on every fresh set (X_CL, A$25k / A$100k)

~ = computed after that set had been opened (the design was frozen later), so not a fresh look.

| Candidate | AS | KO | SA | CO | MC | SW | JSE | OL | TW | mean | sets ≥ +1 at both sizes | cells < −2 | cells ≥ +1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EI | +2.6 / +1.5 | -5.8 / -2.4 | +0.1 / -1.6 | +2.6 / +3.7 | -3.2 / +1.3 | -1.2 / +0.4 | -3.4 / -1.6 | -4.1 / -3.0 | -8.0 / -4.2 | -1.46 | 2 of 9 | 8 of 18 | 5 of 18 |
| EI2 | +1.6 / +0.7~ | -2.9 / -1.5~ | -0.5 / -1.6~ | +3.4 / +4.2~ | -1.7 / +0.7~ | +0.2 / +0.6~ | -3.0 / -1.6 | -4.2 / -2.7 | -5.4 / -4.5 | -1.01 | 1 of 9 | 6 of 18 | 3 of 18 |
| CSL | +1.0 / -0.2~ | +1.2 / +1.0~ | +2.0 / +1.8~ | +1.2 / +2.7 | -2.4 / +0.7 | -3.2 / -2.1 | -0.5 / +0.1 | +5.2 / +4.5 | -5.1 / -3.4 | +0.25 | 4 of 9 | 5 of 18 | 8 of 18 |
| CSLt | +0.5 / -0.5~ | +1.4 / +0.6~ | +1.0 / +3.1~ | +2.2 / +2.4 | -2.3 / +0.7 | -2.4 / -1.8 | +0.1 / +0.3 | +3.4 / +4.2 | -4.1 / -3.4 | +0.29 | 3 of 9 | 4 of 18 | 7 of 18 |
| CSL30 | +1.8 / -0.3~ | +2.8 / +0.7~ | +3.6 / +2.4~ | +3.9 / +3.3~ | -2.5 / +0.7~ | -3.6 / -2.7~ | -0.9 / +0.0 | +9.4 / +5.8 | -5.9 / -4.5 | +0.78 | 3 of 9 | 5 of 18 | 8 of 18 |
| CS50 | -0.5 / +0.7 | -5.2 / -3.5 | -0.7 / +2.7 | -0.4 / -0.4 | -2.6 / -2.4 | -1.4 / -1.6 | -1.8 / -1.1 | -0.5 / +0.8 | -5.3 / -4.9 | -1.56 | 0 of 9 | 6 of 18 | 1 of 18 |
| CS70 | +0.2 / -0.5 | -3.4 / -1.9 | -0.3 / +1.6 | -1.1 / -0.5 | -1.9 / -1.5 | -0.4 / -1.0 | -1.7 / -0.9 | -0.2 / +0.6 | -2.8 / -2.8 | -1.03 | 0 of 9 | 3 of 18 | 1 of 18 |
| TA | -0.7 / +0.3 | -10.0 / -4.9 | +4.4 / +5.4 | -2.0 / +3.2 | -5.9 / -5.2 | -3.0 / -2.6 | -3.1 / -0.9 | +1.2 / +1.8 | -10.2 / -11.2 | -2.42 | 2 of 9 | 10 of 18 | 5 of 18 |
| E3 | -1.0 / +0.5 | -11.7 / -6.3 | +3.7 / +4.1 | -2.0 / +1.5 | -7.3 / -5.2 | -3.7 / -2.5 | -2.3 / -1.3 | +2.5 / +2.0 | -11.7 / -11.2 | -2.89 | 2 of 9 | 10 of 18 | 5 of 18 |

Means that count only sets fresh for the design: EI −1.5 (9 sets), E3 −2.9 (9), TA −2.4 (9), CS50 −1.6 (9), CS70 −1.0 (9), CSL −0.2 (6), CSLt −0.1 (6), CSL30 +0.7 (3; Norway +9.4 / +5.8 carries it, Taiwan −5.9 / −4.5), EI2 −3.6 (3).

### 5.3 Ranking of what came closest

| Rank | Candidate | Mean X_CL | Mean X_AN | Sets passing | Cells below −2 | Worst cell |
|---|---|---|---|---|---|---|
| 1 | CSL30 | +0.78 | +0.32 | 3 of 9 | 5 | -5.9 |
| 2 | CSLt | +0.29 | -0.08 | 3 of 9 | 4 | -4.1 |
| 3 | CSL | +0.25 | +0.00 | 4 of 9 | 5 | -5.1 |
| 4 | EI2 | -1.01 | -1.20 | 1 of 9 | 6 | -5.4 |
| 5 | CS70 | -1.03 | -1.09 | 0 of 9 | 3 | -3.4 |
| 6 | EI | -1.46 | -1.67 | 2 of 9 | 8 | -8.0 |
| 7 | CS50 | -1.56 | -1.56 | 0 of 9 | 6 | -5.3 |
| 8 | TA | -2.42 | -2.53 | 2 of 9 | 10 | -11.2 |
| 9 | E3 | -2.89 | -3.01 | 2 of 9 | 10 | -11.7 |

The index fund is rank 0. Ranks 1–3 are one idea (fund core plus a short list of strong-trend large companies) at three settings, and their means are flattered by the sets they were tuned on. No design passed in more than 4 of 9 markets and every design has cells below −2.

### 5.4 The owner's account

Lifecycle A$5,000 + A$500 a month (paid in A$57,500), final value after tax, engine / fund, A$k:
| Candidate | AS | KO | SA | CO | MC | SW | JSE | OL | TW | sets ahead of the fund |
|---|---|---|---|---|---|---|---|---|---|---|
| EI | 93 / 96 | 115 / 143 | 76 / 82 | 89 / 76 | 112 / 115 | 77 / 83 | 80 / 98 | 99 / 100 | 142 / 200 | 1 of 9 |
| EI2 | 95 / 96 | 139 / 143 | 75 / 82 | 84 / 76 | 114 / 115 | 93 / 83 | 93 / 98 | 89 / 100 | 164 / 200 | 2 of 9 |
| CSL | 98 / 96 | 165 / 143 | 89 / 82 | 97 / 76 | 101 / 115 | 77 / 83 | 103 / 98 | 123 / 100 | 183 / 200 | 6 of 9 |
| CSLt | 93 / 96 | 163 / 143 | 90 / 82 | 97 / 76 | 101 / 115 | 78 / 83 | 101 / 98 | 112 / 100 | 179 / 200 | 5 of 9 |
| CSL30 | 98 / 96 | 157 / 143 | 80 / 82 | 101 / 76 | 95 / 115 | 79 / 83 | 101 / 98 | 133 / 100 | 164 / 200 | 5 of 9 |
| CS50 | 87 / 96 | 121 / 143 | 83 / 82 | 79 / 76 | 91 / 115 | 74 / 83 | 100 / 98 | 95 / 100 | 166 / 200 | 3 of 9 |
| CS70 | 85 / 96 | 118 / 143 | 78 / 82 | 77 / 76 | 96 / 115 | 81 / 83 | 97 / 98 | 91 / 100 | 168 / 200 | 1 of 9 |
| TA | 69 / 96 | 114 / 143 | 70 / 82 | 96 / 76 | 73 / 115 | 77 / 83 | 103 / 98 | 108 / 100 | 140 / 200 | 3 of 9 |
| E3 | 68 / 96 | 113 / 143 | 70 / 82 | 89 / 76 | 73 / 115 | 77 / 83 | 100 / 98 | 113 / 100 | 143 / 200 | 3 of 9 |

### 5.5 What tax-aware selling added

| | AS | KO | SA | CO | MC | SW | JSE | OL | TW | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| TA − E3 | +0.3 / -0.2 | +1.7 / +1.4 | +0.7 / +1.3 | +0.0 / +1.7 | +1.3 / +0.0 | +0.7 / -0.0 | -0.8 / +0.4 | -1.3 / -0.2 | +1.5 / -0.0 | +0.47 |
| CSLt − CSL | -0.4 / -0.4 | +0.2 / -0.4 | -1.0 / +1.3 | +1.0 / -0.3 | +0.0 / -0.1 | +0.7 / +0.3 | +0.6 / +0.2 | -1.8 / -0.4 | +1.1 / +0.1 | +0.04 |

Loss-harvest sales averaged about one a year at A$100,000. Total tax paid over the window was similar for engine and fund (for example A$36k against A$37k for EI). The gain from the rules is timing only.

### 5.6 The signal and the funds

t = t-statistic of the monthly slope of next-month return on the signal's percentile inside the 300 most traded (or all, where fewer).

| Set | Fund before tax, % a year | Fund after tax | Trend quality t | High recency t | H80 t |
|---|---|---|---|---|---|
| Netherlands | 11.4 | 9.8 | 1.9 | 2.0 | 0.2 |
| Korea | 15.9 | 14.1 | 1.3 | 1.6 | 1.3 |
| Brazil | 9.7 | 8.0 | 4.0 | 4.2 | 3.0 |
| Denmark | 8.4 | 7.1 | 3.2 | 4.4 | 3.0 |
| Spain | 11.9 | 10.3 | 3.1 | 3.9 | 1.0 |
| Switzerland | 9.4 | 7.8 | 2.9 | 3.1 | 2.6 |
| South Africa | 12.1 | 10.3 | 1.5 | 0.7 | -2.0 |
| Norway | 11.6 | 9.7 | 4.0 | 3.5 | 3.4 |
| Taiwan | 24.8 | 22.4 | 3.3 | 3.8 | 2.7 |

Trend quality is positive in nine of nine and above 2.9 in six. H80, the score behind H82, is weaker (above 2 in five, negative in South Africa).

### 5.7 Account size and brokerage on fresh sets (December start, mean over sets, X_CL)

| Design | A$10k | A$25k | A$50k | A$100k | A$250k | A$500k | A$3 brokerage instead of A$6.60 (25k / 100k) | Trades a year (25k / 100k) |
|---|---|---|---|---|---|---|---|---|
| EI (9 sets) | −1.8 | −1.2 | −0.6 | −0.5 | −0.7 | −0.9 | +0.2 / +0.1 | 12 / 28 |
| CSL (6 sets) | −2.6 | −0.1 | +0.5 | +0.4 | +0.1 | −0.4 | −0.2 / +0.1 | 12 / 37 |
| CS70 (9 sets) | −2.3 | −1.0 | −1.1 | −0.7 | −0.4 | −0.6 | 0.0 / +0.2 | 4 / 12 |
| E3 (9 sets) | −3.3 | −3.0 | −1.5 | −1.7 | −1.4 | −2.0 | −0.2 / −0.1 | 10 / 20 |

| Design | Smallest account at which it does what it says | Why |
|---|---|---|
| Index fund | any | one holding |
| Core-satellite (CSL) | A$25,000 | five satellite names of A$2,500; A$6.60 is 0.26% of each trade |
| Enhanced index, 20 names | A$50,000 | ten names cannot follow an index (A$25k cells: −5.8, −3.2, −8.0) |
| Enhanced index at real index weights, 40–50 names | A$250,000 or more | the 30th name of a 50-name index weighs under 1%, i.e. under A$1,000 in A$100,000 |

Stress (A$100k, December start, mean over sets): costs × 1.5 changes the after-tax return by 0.0 to −0.4 points; paying every delisting at 70% by −0.1 to −1.0; a 0.3% transaction tax on purchases by 0.0 to −0.3.

## 6. Tax-loss harvesting: what the literature says and what applies in Australia

- Chaudhuri, Burnham and Lo (Financial Analysts Journal, 2020) measure a tax alpha of 1.08% a year for a harvested portfolio of the 500 largest US shares over 1926–2018, and 0.82% with the US 30-day wash-sale rule. The figure is before trading costs and assumes US rates of 35% on short-term and 15% on long-term gains, with the harvested losses usable at once.
- Israelov and Lu (Journal of Beta Investment Strategies, 2023) compare direct indexing with funds for harvesting; practitioner papers from AQR and Parametric make the same general point: the benefit depends on having other gains to offset, on the tax rates, on regular new money and on volatility, and it fades as the book fills with locked-in winners. (Titles checked; their figures were not re-derived here.)
- **Australia.** A capital loss can only be set against capital gains. It reduces the gross gain before the 50% discount, and it carries forward without limit. So a harvested loss is worth 32 cents in the dollar against a short-term gain and 16 cents against a discounted gain, and the lower cost base of the replacement gives the tax back when that is sold. For an investor with no gains outside this account the benefit is deferral only. That is what the simulations show: +0.1 on development, +0.5 and 0.0 on fresh markets. Under the announced July-2027 design (indexation, no discount) the answer is the same (X_AN columns).
- **Wash sales.** Taxation Ruling TR 2008/1 says Part IVA can cancel a loss where the taxpayer sells an asset and, at the same time or shortly before or after, buys the same or a substantially the same asset, so that economic exposure does not really change. The ruling says shares in a competitor carrying on a similar business are not substantially the same asset. The designs here comply by construction: (i) a loss sale is never followed by a purchase of the same company for at least six months; (ii) the replacement is a different company chosen by the standing trend rule, not picked to mirror the one sold; (iii) no derivatives, no related-party transfers, no sale-and-buy-back; (iv) harvesting is limited to gains already realised. Swapping one index fund for a near-identical one to bank a loss is the pattern the ruling is aimed at and is not used. This is a description of the rules, not tax advice; there is no safe-harbour period in Australian law.
- **Franking.** On ASX the fund and a direct book both receive franking credits, so the comparison is unchanged in kind. A tilt towards franked dividends could help a 32% taxpayer but cannot be tested on foreign markets and ASX after 2015 is spent.

## 7. Why structure did not rescue the picking skill

1. **The proxy is not the index.** Traded value over-weights whatever is being traded hardest. On US 2001–13 that meant technology after the bubble and banks in 2008. On the round-1 markets the proxy book with no signal (30% cap) scored Netherlands +1.6 / +1.6, Korea −5.0 / +1.0, Brazil −0.3 / −1.7 against the fund: several points of tracking noise before any picking.
2. **Concentrated indices.** Where one or two companies drove the index (Korea, Taiwan), a 20% cap and a 10–30-name book held less of them than the fund did. EI lost 2.4 to 8.0 points a year there.
3. **The fund as core removes the handicap and the upside together.** With 50–70% in the fund the lead is roughly the satellite's lead times 30–50%. The satellite would need to beat the fund by 2–3 points a year after tax for the whole to clear +1. It did so in four of nine markets (Norway, Denmark, Brazil, Korea) and not in the others.
4. **Tax-aware rules save tenths of a point.** The gap to close was 1–3 points.
5. **Noise.** The same design moved by ±3 points between markets and by 1–6 points between start months. Nine markets over the same nine years are fewer than nine independent tests.

## 8. Deviations, caveats, reasons this could be wrong

- **Weight proxy.** A true cap-weighted direct index was not tested because the data do not exist on the plan. The EI result is a result about the proxy.
- **Brazil** lacks the preferred share lines; **Korea and Taiwan** have thin dead-company coverage; **Denmark** has many dead lines. Results there carry less weight. Leaving out all four leaves Netherlands, Spain, Switzerland, South Africa, Norway: EI passes 1 of 5, CSL 1 of 5.
- **Data corrections favoured the engine** (section 4). They were made before any engine return was computed and are listed in the pre-registration. Unrecorded reverse splits (fake gains) were not removed outside Korea and Taiwan; one was seen (Meyer Burger, Dec 2024).
- **US large 2001–13 was found unfit for weighted designs** during development, so EI's development case rested on ASX alone.
- **CSL and EI2 were designed after earlier fresh sets had been opened**; those sets are development for them and are marked ~.
- **Small stock dividends are taxed as cash dividends** (against the engine, mainly Taiwan). **Local transaction taxes and currency** are not in the base case. Costs and tax are the owner's Australian schedule in local units.
- **Imputed fund distributions** are an approximation; the Danish fund's real distributions are larger and partly capital gains.
- **Loss harvesting was modelled with no outside gains.** An investor who regularly realises other capital gains would get more from it (up to 16–32 cents per dollar of loss, once).
- **Deflated Sharpe** uses report 73's formula; at N ≈ 1,200 every figure is 0.00–0.16.
- **Each look was run once.** No candidate or data rule was changed after its look. Not replicated by a second agent.

## 9. Frozen definition of the closest design (CSL) — it did not pass and is not a paper rule

Parts A, C1, E, F, G of rules v1.3 and T1, T3, T9 of report 73 §6 apply.
- **C1.** At every month-end, after payouts: NAV = cash + fund + shares at last price. Fund target = 50% of NAV; free cash goes to the fund whenever the fund is A$1,000 or more below target.
- **C2. Universe.** Companies with a close on ≥ 200 of the last 252 trading days, ordered by median daily traded value (T1); the first 100. A holding keeps a rank while its traded-value rank is ≤ 150 (its score is placed among the 100).
- **C3. Score and rank.** Trend quality (T3) inside the 100; rank 1 = highest; ties in traded-value order.
- **C4. Book.** Satellite = NAV − fund. n = min(30, max(4, floor(satellite ÷ 2,500))); T = satellite ÷ n.
- **C5. Sales.** A holding ranked worse than 50 or unranked at two month-ends in a row is sold in full, except a holding above cost whose first lot is 300–365 days old and whose rank is 70 or better: it waits. At the May month-end a holding below the line once and at or under cost is sold.
- **C6. Trim / buys / top-up.** As T6–T8 of report 73 with buy line rank ≤ 15.
- **C7. Small accounts.** Fund only until NAV ≥ A$25,000; then the fund is sold down to 50% and C4 applies.
- Status: closed for promotion. If a shadow line is wanted it can be computed monthly from the same file as the v1.3 snapshot with `improve4/code/look4.py` candidate `CSL`; no forward-snapshot procedure was written because nothing passed.

## 10. Files

- Pre-registrations and hashes: `improve4/PREREG_75_R1.md`, `_R2.md`, `_R3.md`, `cands_extra.json`; `out/prereg75_R1_hash.txt`, `_R2_`, `_R3_` (SHA-256 of the pre-registration, every code file, every pack and the ledger).
- Code: `code/sim4.py`, `lib4.py`, `look4.py`, `mk_fresh4.py`, `packlib.py`, `scores.py`, `dl4.py`, `qa.py`, `dev1.py`–`dev8.py`, `reg.py`, `freeze4.py`, `summ4.py`, `final4.py`.
- Data: `data/raw/*.pkl` (vendor downloads, 450 MB), `data/pack_*_M.npz`, `data/etf/*.csv` (including `STX40FIX.JSE.csv`), `data/lists/`.
- Results: `out/look_R{1,2,3}_<design>_<set>.json`, `out/fm_*.json`, `out/summary_table.md`, `out/final_table.md`, `out/dev*.log`, `out/coverage_*.csv`, `out/qa*.log`, `out/mk_*.log`, `out/trials_75.csv`, `PROGRESS.md`.

Sources for section 6: [ATO TR 2008/1](https://www.ato.gov.au/law/view/pdf/pbr/tr2008-001.pdf); [Chaudhuri, Burnham, Lo — An Empirical Evaluation of Tax-Loss-Harvesting Alpha](https://rpc.cfainstitute.org/research/financial-analysts-journal/2020/empirical-evaluation-tax-loss-harvesting-alpha) ([working paper](https://dspace.mit.edu/handle/1721.1/135992)).
