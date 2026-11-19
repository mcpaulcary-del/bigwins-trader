# Report 96 — Can EMG2-18 be made to step aside before it gives the money back?

Fable, 19 November 2026. Research only: no live code, ledger, scheduled task or `/home/user/asx-trader` file was touched; no vendor request was made. Working folder `deep96/` (`PROGRESS.md`, `PREREG_96.md`, `PREREG_96b.md`, `FREEZE_96.md`, `FREEZE_96b.md`, hashes in `out/`).

## 1. Answer

**No rule passed the bar set in advance, so there is no live amendment. One rule is worth running on paper from December: when the 301–600 band's own trend turns down, sell the shares and hold the ASX 200 fund until it turns up.**

- **Nothing got out before a drop.** Across the three big falls of the ASX replay (2018–20, 2022, 2026) no tested rule sold before the peak. The best ones sold 10 to 22 trading days after the March 2026 peak, when the book was already 15–19% down. They then avoided about half of the rest of the fall.
- **The fast early-warning signals lose money.** Rising volatility, rising dispersion, picks hitting new lows, the picks' momentum fading, and picks trailing their twins were each tested on four overseas markets first. Each left the account with less money than plain EMG2-18 in the typical market (6% to 50% less) and did not make the worst fall smaller. They were not taken to the ASX.
- **Stops and fortnightly checks lose money too** (overseas: 7% to 26% less in the typical market), as they did on the ASX earlier.
- **The slow band-trend switch into the index fund is the one that helped on the ASX.** A$10,000, 12 start months from Dec 2017, to Nov 2026, after IBKR tiered brokerage and tax:

| Mean of 12 starts | Registered EMG2-18 | Band trend → index fund | Band trend → cash | ASX 200 fund |
|---|---|---|---|---|
| Ends with, research panel | A$28,067 | **A$30,485** | A$22,176 | A$18,586 |
| Ends with, vendor file | A$23,731 | **A$26,443** | A$17,811 | A$18,586 |
| Worst fall (panel / vendor) | −56% / −58% | −32% / −40% | −33% / −39% | −36% |
| Given back from the peak to today (panel) | A$16,255 | A$7,272 | A$5,706 | — |
| Value at Dec 2025, before the 2026 fall (panel) | **A$35,028** | A$30,980 | A$23,010 | — |
| Orders a year; brokerage a year | 110; A$613 | 89; A$517 | 85; A$474 | — |

- **Why it still fails the bar:** the bar said the gain must not rest on one episode. Up to December 2025 the switch was A$4,000 behind the registered rules (12% less, on both data sets). All of its lead comes from the 2026 fall. It was also not the version the overseas design picked: the design picked "to cash", and "to cash" lost A$5,900 against the registered rules on the ASX.
- **Index fund or cash?** The index fund, clearly, on the ASX: A$8,300–8,600 more than cash at the end, on both data sets. Cash sat out 38% of the time earning nothing while the fund rose about 8% a year. Paying the RBA cash rate on idle cash closes only A$1,000–1,700 of that gap. Cash protected better only in a 2008-type crash (2006–17 run: worst fall −36% in cash against −59% in the fund).

## 2. What was done

The owner asked for the weak point to be fixed without fitting to the known ASX answer. So every rule was designed on overseas markets only, frozen with a hash, and then run once on the ASX.

- **Design markets:** Thailand, China, Malaysia and Korea (six market-versions, translated exactly as report 95). The UK and the other European and US panels of report 95 were lost in a container restart and could not be rebuilt without vendor credits. This is a weakness: the design set is all Asian, and plain EMG2-18 lost money in three of the four.
- **Money model:** the kit's engine, unchanged, with IBKR tiered brokerage of A$5.55 minimum an order (report 91's A$710 a year at 128 orders), the kit's spread model and tax. The index fund was added as a buyable line that pays brokerage, a small spread and tax like a share. Cash earns 0%, which is what IBKR pays on a balance this size.
- **Check:** the new engine reproduces report 95's twin books to six decimal places.
- **Candidates:** 55 rules, all written down before any was run. 31 were in the first plan (band-trend switches, account drawdown control, volatility targeting, stops, fortnightly checks; each defensive rule in a fund version and a cash version). 24 were added when the owner asked for early-warning exits.
- **Choice rule, fixed in advance:** a rule qualifies only if, in the typical market, it ends with at least as much money as EMG2-18, cuts the worst fall by five points or more, and still does both with any one market left out. The qualifier with the best middle rank on money is chosen.

## 3. Overseas design results

Seven of the first 31 qualified, all slow: the band index above its 10-month or 6-month average, and the paper book 15% below its one-year high. Two of the 24 early-warning rules qualified, both breadth rules (share of band names above their own 100-day or 50-day average). Chosen by the fixed rule: **band 10-month average, to cash**, and **100-day breadth, to the fund**.

| Typical overseas market, against plain EMG2-18 | Ending money | Worst fall, points better |
|---|---|---|
| Band 10-month average → cash (chosen) | +67% | 17 |
| Band 10-month average → fund | +46% | 12 |
| Paper book 15% down, weekly → fund | +31% | 15 |
| 100-day breadth → fund (chosen early-warning rule) | +33% | 12 |
| Picks trailing twins 6 weeks → cash | +1% | 1 |
| Momentum of momentum, 21 days → fund | −12% | −2 |
| New lows among the picks, 63 days → fund | −19% | −4 |
| Volatility up → fund | −32% | −4 |
| Dispersion up → fund | −47% | −3 |
| Trailing stop 20% | −21% | −4 |
| Fortnightly checks | −26% | −6 |

These gains need a caution, written in the freeze file before the ASX run. Plain EMG2-18 lost money in Thailand, China and Korea, so any rule that holds it less looked good there. In Malaysia, the one design market where EMG2-18 made money (A$14,689 against the fund's A$11,399), the chosen rule cut the ending value to A$8,019.

## 4. The ASX judgement

Seven frozen rules were run on the ASX: the two chosen, their two siblings, the two paper-drawdown extras, and the registered rules as the base. The table shows the mean of 12 starts on the research panel, with the vendor file in brackets.

| Rule | Ends with | Worst fall | Ahead of EMG2-18 | Ahead of fund | Bar |
|---|---|---|---|---|---|
| Registered EMG2-18 | A$28,067 (23,731) | −56% (−58%) | — | 12 of 12 (12) | — |
| Band trend → cash (chosen) | A$22,176 (17,811) | −33% (−39%) | 0 of 12 (0) | 12 (2) | fails: less money |
| Band trend → fund (sibling) | A$30,485 (26,443) | −32% (−40%) | 12 of 12 (12) | 12 (12) | fails: one episode |
| Breadth → fund (chosen early-warning) | A$25,477 (19,829) | −35% (−39%) | 0 (0) | 12 (12) | fails: less money |
| Breadth → cash | A$15,336 (12,700) | −43% (−52%) | 0 (0) | 0 (0) | fails |
| Paper book −15%, weekly → fund | A$19,975 (15,658) | −46% (−51%) | 0 (0) | 9 (0) | fails |
| Paper book −15%, weekly → cash | A$14,067 (10,274) | −41% (−50%) | 0 (0) | 0 (0) | fails |

Further checks on the band-trend-to-fund rule:

- **Twins:** it beat all 100 of its random twins on both data sets.
- **Five best holdings removed:** A$23,306 against A$15,712 for the registered rules (panel).
- **Spread doubled:** A$25,974 against A$22,031.
- **January 2020 start, the owner's replay (panel):** the registered rules peaked at A$49,740 on 2 March 2026 and stand at A$31,657, a give-back of A$18,083. The switch peaked at A$38,942 and stands at A$31,505, a give-back of A$7,437. The two end level; the switch never reached the high the registered rules reached.
- **2006–2017 (survivorship-free panel):** A$11,819 against A$12,128 for the registered rules and A$18,081 for the fund; worst fall −59% against −44%, because it sat in the index fund through 2008. Neither version of EMG2 beat the fund in that decade at A$10,000.

## 5. How early did the rules get out, and what did false exits cost?

Dec-2017 book on the research panel. "Days" are trading days from the registered book's peak to the rule's sale.

| Fall of the registered book | Band trend → fund | Breadth → fund | Paper book −15% → fund |
|---|---|---|---|
| Jan 2018 – Mar 2020, −59% | sold 137 days after the peak, book 17% down; saved A$3,328 | 200 days after, 21% down; saved A$2,369 | 49 days after, 16% down; saved A$1,308 |
| Apr – Jul 2022, −36% | 8 days after, 3% down; saved A$2,147 | already out before the peak; saved A$1,638 | 18 days after, 14% down; saved A$1,840 |
| Mar – Jul 2026, −41% | 22 days after, 19% down; saved A$7,929 | 10 days after, 15% down; saved A$6,416 | 15 days after, 32% down; saved A$4,087 |

On the vendor file the pattern is the same; neither chosen rule sold at all during the fast fall of early 2020.

| Step-asides, 2018–2026 (panel) | Band trend → fund | Band trend → cash | Breadth → fund | Paper book −15% → fund |
|---|---|---|---|---|
| Number; share of days out | 8; 38% | 8; 38% | 12; 28% | 9; 49% |
| Helpful ones | 4, +A$8,856 | 2, +A$5,358 | 5, +A$9,624 | 4, +A$4,707 |
| False exits (EMG2-18 did better while out) | 4, −A$5,578 | 6, −A$9,612 | 7, −A$6,161 | 5, −A$9,391 |
| Net | +A$3,278 | −A$4,254 | +A$3,463 | −A$4,684 |

The costliest false exit was April–July 2020: the band-trend rule sold on 1 April 2020, after the crash, and the registered book rose 68% before it came back. In the fund that cost A$4,190; in cash A$4,997. These figures compare book values over each period out and include any June tax bill paid while out; they leave out the extra brokerage of leaving and returning, which is why the breadth rule's net is positive while its ending value is lower than the registered rules'.

**Why cash failed here:** these rules exit late and return late. While out, the index fund usually recovers part of what was missed; cash recovers nothing.

## 6. What this means for the owner's two instructions

- **"Better than the index, or hold the money."** On the ASX replay the registered rules and the band-trend-to-fund rule both beat the index fund from every start month, on both data sets. The cash versions did not beat it reliably: band-trend-to-cash was ahead of the fund in only 2 of 12 starts on the vendor file. Holding cash until "it's worth re-investing" cost money against holding the index fund in the meantime.
- **"Pull out before the drop."** Not found. Every signal that reacts fast enough to act near a peak also fires in ordinary dips, and the missed rebounds cost more than the falls avoided. What can be had is a smaller fall after a late exit: roughly a 32–40% worst fall in place of 56–58%, and about A$9,000 less given back in 2026.
- **The trade-off in dollars.** Had the band-trend-to-fund rule been running, the account would have been about A$4,000 lower at the end of 2025 and about A$2,400–2,700 higher today. Its value to the owner is a steadier account, and that result rests on one fall.

## 7. Recommendation

1. **No live change before the mid-December go-live.** The bar was fixed before the ASX run and was not met. Registered EMG2-18 stays.
2. **Register the band-trend-to-fund rule as a paper line** beside the live book from the first decision. Draft: `deep96/AMENDMENT_shadow_EMG2_18_BT.DRAFT.md`. It needs no new data, only the band's own index, and it gives a monthly "band trend ON/OFF" flag the owner can see.
3. **Use the flag as information now.** On the replay the band trend was OFF at the Nov 2026 valuation (the rule has been out since 1 June 2026). If it is still OFF at go-live, the paper line starts in the index fund while the live book buys shares. The owner should know that before funding.
4. **Do not pursue** stops, fortnightly checks, volatility or new-low signals, or account-drawdown triggers. All lost money out of sample.

## 8. Limits

- Design markets were four Asian markets, three of them losing ones for EMG2-18; the choice rule picked the cash version, which failed on the ASX. The fund version's result is therefore a sibling's result, one of six rules judged on the ASX.
- 2018–2026 is not unseen for EMG2-18 itself (its band was chosen with that period in view), so the registered rules' own numbers are flattered.
- Costs are modelled: no real fill has been compared with the spread model; the fund's spread was set at 0.05% a side.
- Overseas panels end at different dates and carry no currency, stamp duty or withholding tax (as report 95).
- The 2026 fall is unfinished: the registered book had not recovered by the last valuation.

## 9. Trial count

N before: 2,822 (2,789 + report 95's 33; report 95's own text says 2,821). This work: 31 + 24 overseas design candidates, and 6 frozen rules run on the ASX (two chosen, two siblings, two declared extras) = 61. **N = 2,883.** Twins, start months, stresses, the cash-rate sensitivity and the 2006–17 run of the same frozen rules are not counted. Ledger not written.

Files: `deep96/out/design_read.log`, `designE_read.log` (overseas); `readjM_panel.log`, `readjM_vendor.log` (ASX tables and bar); `evt_panel.log`, `evt_vendor.log` (event study); `prereg96_hash.txt`, `prereg96b_hash.txt`, `freeze96_hash.txt`, `freeze96b_hash.txt`.
