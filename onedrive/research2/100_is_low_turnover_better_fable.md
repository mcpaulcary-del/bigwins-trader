# Report 100 — Is the lower-turnover EMG2-18 ("C6") really better? And is the band-trend protection confirmed overseas?

Fable, 20 November 2026. Research only: no live code, ledger, scheduled task or `/home/user/asx-trader` file was touched. Working folder `deep100/` (`PROGRESS.md`; `PREREG_100.md` hashed before any new run; logs in `out/`). Both rules were run exactly as frozen (C6: `FREEZE_99`; protection: report 96's freeze, run as written per report 98). **This report also serves as the overseas confirmation of the band-trend protection that report 97 asked for (section 5).**

Vendor use: 15,369 EODHD requests by this work (UK, Germany, Sweden, France, US, KOSDAQ, Taipei Exchange), started only after the new-listings tracker and the Canada leg had finished, at 140 a minute. Canada was not downloaded again: the coordinator's files were reused. Usage at the end: 21,708 of 100,000 for the day. Nothing is pending and nothing was scheduled.

## 1. Answer

1. **Yes, C6 is probably better, but by much less than report 99's A$6,200–6,900.** What can be relied on is the saving in brokerage and spread: **about A$250–320 a year on a A$10,000 start** (about a third fewer orders). The rest of the gain shown on the ASX is not reliable: tested overseas, C6's share-picking was no better than the current rule's, and slightly worse.
2. **C6 passed every test fixed in advance for this report**, so by that rule a live switch is supported:
   - ASX before 2018 (2002–2009 and 2010–2017): ahead of the current rule from all 12 start months in both, and in 12 of 12 five-year windows.
   - Eight new overseas market-versions: more money than the current rule in 5 of 8, middle result +A$1,682 over 8.4 years, worst fall 0.4 points deeper.
   - Worst fall across all independent data: 1.8 points deeper in the middle case (the limit was 2).
3. **The risk is concentrated where EMG2-18 works best.** In Canada, the market most like the ASX and the one overseas market where plain EMG2-18 made a lot of money, C6 ended 28% below the current rule (A$29,431 against A$40,821). Taiwan (same-rank version) −13%. On the ASX this did not happen in any period tested, but it is the reason the expected gain should be read as the cost saving only.
4. **The 5-point deeper fall in report 99 is noise.** A resampling test puts the difference anywhere between 9 points deeper and 12 points shallower. Across 16 data sets C6's fall was deeper in 9 and shallower in 7. In dollars its lowest point was higher than the current rule's on the ASX.
5. **The band-trend protection is only partly confirmed overseas.** In ten new market-versions it made the worst fall shallower in 7 (middle case 5.6 points). It ended with less money than plain EMG2-18 in 5 of 10, and in every market where plain EMG2-18 did well it cost a great deal: Canada −43%, Taiwan −34% to −45%, US −34%, Germany −23%. It protects a book that is losing and taxes one that is working.
6. **Recommendation.** Switching the live book to C6 is supported by the evidence and I recommend it, on the cost saving alone. Keeping the current rule live with C6 on paper is the cautious alternative; its expected price is about A$250–300 a year. Either way the choice changes nothing until the protection switch turns back on and the first shares have been held a month, because the two rules buy the same shares and differ only in when they sell. The live sell rule should not be changed until the new code has been built and tested.

## 2. Test 1 — the ASX before 2018

Research panel (includes dead companies) rebuilt from 23 November 2000, the first day the index series exists. A$10,000, 12 start months per window, IBKR tiered brokerage, spread and tax. Check: on this longer panel the 2018–2026 figures reproduce exactly (A$28,277 and A$34,520). The vendor file cannot be used before 2018 (it holds almost no dead companies).

| Window | C6 | Current (EMG2-18_BT) | Plain EMG2-18 | ASX 200 fund | C6 ahead of current | Worst fall, C6 / current |
|---|---|---|---|---|---|---|
| Starts Dec 2001–Nov 2002, to Dec 2009 | A$11,696 | A$8,218 | A$9,486 | A$18,603 | 12 of 12, +A$3,478 | −62% / −58% |
| Starts Dec 2009–Nov 2010, to Dec 2017 | A$21,745 | A$14,233 | A$11,424 | A$17,061 | 12 of 12, +A$7,512 | −35% / −33% |
| Starts Dec 2001–Nov 2002, to Dec 2017 (16 years) | A$28,719 | A$12,940 | A$11,082 | A$31,689 | 12 of 12 | −62% / −59% |
| Five-year windows, each December 2001–2012 | A$13,302 | A$10,292 | A$10,709 | A$14,436 | 12 of 12 | −44% / −40% |

- Orders a year: 30–44 for C6 against 48–56. Brokerage and spread: A$283 against A$435 a year in the first window, A$471 against A$533 in the second.
- **Three cautions.**
  - This period is not untouched for C6. Its sell rule (six months, then out of the top 40%) was chosen by the blind-2 builder on ASX data from 2004 to 2017, for a different share list. Only 2002–2003 had never been opened, and there the two rules were level.
  - The band was thin before about 2013. The current rule held 5 names on average and sat 35% in cash; C6 held 7–8 and sat 18–24% in cash. Part of C6's lead here is simply being more invested, which matters less now that the band holds about 30 buyable names.
  - Neither rule beat the index fund over 2002–2009 or over the full 16 years. C6 beat it in 2010–2017 only.
- The protection in this period: from the 2001–02 starts it ended A$1,268 below plain EMG2-18 with a worst fall 16 points deeper (it moved a mostly-cash book into the index fund before the 2008 crash). From the 2009–10 starts it ended A$2,810 above plain with the same fall.

## 3. Test 2 — overseas, C6 against the current rule

Markets re-downloaded and rebuilt exactly as report 95; 12 start months from December 2017 to October 2026; A$10,000 of local currency, A$ costs, no currency effect. Check: plain EMG2-18 at report 95's fixed fee reproduces report 95 (Germany 13.8% a year, France 5.2, Sweden 6.3, Korea −9.5 / −5.8, Taiwan 16.5 / 15.4; UK 3.0 / 4.0 against 2.8 / 4.6 and US 4.6 against 4.7 after a month more data). Canada matches the coordinator's run (25.8 / 4.9).

| Market-version | C6 | Current | Plain | Local fund | C6 − current | Starts ahead | Worst fall C6 / current | Orders a year C6 / current |
|---|---|---|---|---|---|---|---|---|
| **New for C6** | | | | | | | | |
| Canada, same rank | 29,431 | 40,821 | 71,872 | 26,119 | **−11,390** | 0 | −38% / −35% | 54 / 76 |
| Canada, same percentile | 12,173 | 16,203 | 15,433 | 26,119 | −4,030 | 0 | −42% / −38% | 35 / 57 |
| Germany | 26,926 | 23,501 | 30,669 | 18,501 | +3,425 | 12 | −38% / −38% | 46 / 80 |
| Sweden | 30,250 | 23,782 | 18,207 | 23,580 | +6,468 | 12 | −44% / −47% | 59 / 97 |
| France | 16,975 | 16,766 | 15,854 | 17,584 | +209 | 11 | −36% / −28% | 34 / 48 |
| UK, same rank | 15,853 | 16,036 | 15,015 | 18,031 | −183 | 2 | −33% / −33% | 53 / 80 |
| UK, same percentile | 18,081 | 14,926 | 13,649 | 18,031 | +3,154 | 12 | −35% / −34% | 48 / 76 |
| US, same rank | 13,717 | 10,313 | 15,664 | 27,692 | +3,405 | 12 | −38% / −42% | 59 / 90 |
| **Partly seen (main boards were in report 99's design)** | | | | | | | | |
| Taiwan, both boards, rank | 20,554 | 23,638 | 35,581 | 56,188 | −3,084 | 0 | −47% / −58% | 61 / 104 |
| Taiwan, both boards, percentile | 27,663 | 20,476 | 36,897 | 56,188 | +7,187 | 12 | −50% / −51% | 61 / 105 |
| Korea, both boards, rank | 13,065 | 8,556 | 7,250 | 32,054 | +4,509 | 12 | −51% / −46% | 52 / 74 |
| Korea, both boards, percentile | 4,032 | 6,899 | 4,461 | 32,054 | −2,867 | 0 | −70% / −63% | 42 / 58 |

- **Test as fixed in advance (eight new market-versions):** more money in 5 of 8 (needed more than half); middle difference +A$1,682 (needed above zero); middle worst fall 0.4 points deeper (limit 2). **Passed.**
- **Damage check:** of the three new market-versions where the current rule beat its local fund (Canada rank, Germany, Sweden), C6 was more than 10% below it in one (Canada rank, −28%). The flag needed half or more, so it was not raised. It was close, and Canada is the market that most resembles the ASX.
- **Orders:** 35% fewer in the middle case, the same as on the ASX. Brokerage and spread saved: A$268 a year in the middle case (A$105 to A$398).
- **Share-picking alone (all costs and tax removed), C6 minus current:** −1.3% a year pooled over the eight new market-versions, −1.8% a year over all twelve. It was zero or negative in about 8 of 10 resampled histories for the eight, and 9 of 10 for the twelve. Overseas, C6's lead is the cost saving and nothing else.
- Against the local index fund, C6 was ahead in 4 of the 8 new market-versions, the current rule in 3, plain EMG2-18 in 2.

## 4. Test 3 — where the ASX gain of 2018–2026 came from

Each rule was re-run with costs and tax switched off in steps (same rules, accounting only).

| A$10,000, mean of 12 starts, C6 minus current | Research panel | Vendor file |
|---|---|---|
| Reported difference | +A$6,243 | +A$6,869 |
| (a) Brokerage and spread saved, with its compounding, before tax | +A$4,129 | +A$2,593 |
| (c) Which shares were held, before costs and tax | +A$9,638 | +A$8,680 |
| (b) Extra tax paid on those two gains | −A$7,523 | −A$4,404 |
| After tax, shared pro rata: cost part / share-picking part | +A$1,872 / +A$4,371 | +A$1,580 / +A$5,289 |
| Plain arithmetic: brokerage + spread saved a year | A$171 + A$151 = A$322 | A$160 + A$114 = A$275 |

- **(a) The certain part.** About 32 fewer orders a year at the A$5.55 minimum is A$170 of brokerage a year at any account size. The spread saving is modelled (A$115–150 a year on a book that averaged about A$20,000; about half that at A$10,000) and has not yet been checked against a real fill. Over the 8.4 years: A$2,300–2,700 before tax, A$1,600–1,900 after.
- **(b) Tax: there is no tax benefit.** No share in either rule was held for 12 months (longest holding 306 days), because the protection switch sells everything at each step-aside. No gain earned the discount. C6 paid more tax (A$11,285 against A$8,383 on the panel) only because it made more.
- **(c) Share-picking: not distinguishable from zero.** Monthly differences before costs, resampled in six-month blocks: +1.7% a year on the panel (90% range −2.9% to +6.4%; chance it is zero or less 28%) and +1.3% on the vendor file (−4.6% to +7.8%; 38%). The test needed under 5% on both. Almost all of it came from 2019 and 2025; in 2024 C6 lost 13 points to the current rule on the panel.
  - For 2002–2017 the same figure is +5.6% a year (chance of zero or less 2%). That is the period the sell rule was designed on and the period of the thin band.
  - Overseas it is −1.3% a year.
  - By the rule fixed in advance, the share-picking part is not counted as reliable.
- **The worst fall.** Daily returns of the two books resampled together (blocks of 63 sessions): on the panel C6's fall was deeper in 44% of resampled histories, with a 90% range from 9 points deeper to 12 shallower. Not a real difference.

| Worst fall, C6 minus current (points; minus = deeper) | |
|---|---|
| ASX 2018–26, panel / vendor | −5.2 / +11.1 |
| ASX 2002–09 / 2010–17 | −4.0 / −1.8 |
| Eight new overseas market-versions | −8.0, −3.2, −2.8, −1.0, +0.3, +0.5, +3.0, +4.3 |
| Middle of the independent set (panel, two older windows, eight new) | −1.8 (limit −2) |
| Lowest value reached from A$10,000, C6 / current | panel 6,342 / 5,769; vendor 7,377 / 5,890 |

C6's fall is deeper more often than not, by about 2 points in the middle case. It passed the limit narrowly.

## 5. The band-trend protection overseas (report 97's question)

Current rule (EMG2-18 with the protection) against plain EMG2-18, in the ten market-versions that were not among report 96's design markets.

| Market-version | Plain | With protection | Money kept | Worst fall, plain → protected | Share of months out |
|---|---|---|---|---|---|
| Canada, rank | 71,872 | 40,821 | 57% | −43% → −35% | 48% |
| Canada, percentile | 15,433 | 16,203 | 105% | −42% → −38% | 45% |
| Germany | 30,669 | 23,501 | 77% | −33% → −38% | 33% |
| Sweden | 18,207 | 23,782 | 131% | −62% → −47% | 36% |
| France | 15,854 | 16,766 | 106% | −41% → −28% | 61% |
| UK, rank | 15,015 | 16,036 | 107% | −41% → −33% | 41% |
| UK, percentile | 13,649 | 14,926 | 109% | −42% → −34% | 45% |
| US, rank | 15,664 | 10,313 | 66% | −42% → −42% | 24% |
| Taiwan, rank | 35,581 | 23,638 | 66% | −53% → −58% | 29% |
| Taiwan, percentile | 36,897 | 20,476 | 55% | −51% → −51% | 28% |

- **Protection test:** fall shallower in 7 of 10 (needed two-thirds), middle improvement 5.6 points (needed 3). **Met.**
- **Cost test:** at least as much money as plain in 5 of 10 (needed half: met), middle money kept 91% (needed 95%: **not met**).
- **Verdict by the rule fixed in advance: partly confirmed.** It reduces falls in most markets. It is not free.
- **The pattern is the one reports 96 and 98 warned of.** Where plain EMG2-18 made good money (Canada rank, Germany, Taiwan, US) the protection removed 23–45% of the ending value and in four of those five market-versions did not make the fall shallower. Where plain EMG2-18 was weak (UK, France, Sweden) it added 6–31% and cut the fall by 8–16 points.
- On the ASX 2018–2026 it ended level with plain (A$28,277 against A$28,067) with a fall 5–10 points shallower. That sits between the two overseas groups.
- **For the owner:** the protection is insurance with a real premium. If EMG2-18 keeps working on the ASX as it has, expect it to cost money over time. If EMG2-18 stops working, it limits the damage. The overseas result does not overturn the owner's choice of the protected start, and it does not support it as strongly as report 96's first figures did.

## 6. Verdict against the rule fixed in advance

| Condition for recommending a live switch to C6 | Result |
|---|---|
| ASX before 2018: at least A$500 ahead in both windows, 8 of 12 starts each, 8 of 12 five-year windows | +A$3,478 and +A$7,512; 12, 12 and 12 ✓ |
| Overseas, new market-versions: ahead in more than half, middle difference above zero, fall no more than 2 points deeper | 5 of 8; +A$1,682; −0.4 ✓ |
| Damage flag not raised | 1 of 3 ✓ (close) |
| Middle fall difference across independent data not below −2 points | −1.8 ✓ (close) |
| Reliable dollars | Cost part only: about A$250–320 a year |
| Share-picking part reliable? | No: not distinguishable from zero on the ASX; negative overseas |

**What the owner is choosing between:**

| | Switch the live book to C6 | Keep current live, C6 on paper |
|---|---|---|
| Expected gain | About A$250–320 a year in lower costs; anything beyond that is unproven | Gives that up for another year of evidence |
| Chance it does better than the current rule | ASX history: every start month in every period. Overseas: 5 of 8 | – |
| What could go wrong | In a strong run for EMG2-18 it holds stale names and trails (Canada: −28% over 8 years). Falls about 2 points deeper in the middle case | Paying about A$500 a year in brokerage where A$330 would do |
| Practical | The live sell rule must be rebuilt and tested. Buying is unchanged | Nothing to build |

My recommendation is the switch, for the cost saving, with two conditions: (1) the code change is tested before it sells a real share; (2) the paper line of the current rule is kept running beside it, so the Canada-type shortfall would be seen if it appears. If the owner prefers to wait for paper months, the cost is small and the December 2027 review in report 99 stands.

## 7. Limits

- The ASX before 2018 was the design period of C6's sell rule and had a thin band. The overseas test is the only fully new evidence, and there the gain was A$1,700 in the middle case, with two markets strongly against.
- Overseas runs carry no currency, stamp duty or withholding tax; A$ brokerage is applied to local prices.
- Costs are modelled. No real fill has yet been compared with the spread model; the brokerage part of the saving does not depend on it.
- Canada's plain result (26% a year, same-rank version) falls to 14% if every holding that stopped trading had paid nothing. It was not examined name by name here.
- The replay retries a stuck share at the next month-end; the live daily re-offer is not modelled (same for both rules).
- The start months share the same years. "12 of 12" is one result seen 12 times.
- Trials: 4 on the ASX before 2018 (two comparisons, two new windows), 24 overseas (two comparisons, 12 market-versions), 2 statistical tests = 30. **N 2,928 → 2,958** (ledger not written).
- Files: `deep100/PREREG_100.md`, `out/prereg100_hash.txt`, `out/t1.log`, `read_t1.log`, `t1_boot.log`, `t3run.log`, `t3.log`, `read_ov.log`, `ov_table.csv`, `final100.log`, `run_all.log`, `run_all2.log`, `run_CA.log`, `dl_all2.log`, `dl_all3.log`. Raw downloads and panels deleted.
