# Report 101 — Can a tax-aware delay of sales recover the 12-month CGT discount for the live C6 rule?

Fable, 21 November 2026. Research only: no live code, ledger, scheduled task or `/home/user/asx-trader` file was touched. Working folder `deep101/` (`PROGRESS.md`; `PREREG_101.md` hashed before any code; `FREEZE_101.md` hashed before any ASX run of the new rule). No vendor data request was made: everything ran from files on disk.

## 1. Answer

**No. The delay rule does nothing on the ASX and nothing reliable overseas. It fails the bar. No amendment is drafted. Keep the live C6 rule as it is.**

1. **On the ASX the chosen rule (wait up to 31 days for the 12-month date) never acted once.** Across both data sets, 12 start months and 8.9 years, not one sale was delayed. The result is identical to live C6 to the cent: **A$34,520 (research panel) and A$30,795 (vendor file), a gain of A$0** against a bar of +A$500.
2. **The longer waits lose money.** Waiting up to 62 or 92 days (shown for information only) ended **A$416 to A$606 lower** than live C6. They saved A$770–2,620 of tax and lost A$1,370–3,040 of return by holding shares the rule wanted to sell.
3. **Overseas the 31-day rule was a coin toss around zero.** In ten market-versions: higher in 3, lower in 3, no action in 4. Middle result A$0, average +A$0.10. Range −A$619 (China) to +A$496 (Canada).
4. **Why it cannot work for this strategy.** The discount needs a share held 12 months. C6 does not hold shares that long, for two separate reasons:
   - About 45% of all gains are realised when the protection switch steps aside and sells everything. Those shares had been held about two months in the middle case.
   - Of the gains sold by the C6 rule itself, 84–86% are sold at six to seven months, as soon as the six-month hold ends. Almost nothing reaches month ten.
   - Report 100 put this down to the switch alone. That was incomplete: the sell rule itself lets go of nearly everything by month seven.
5. **The tax "cost" in report 100 is not a lost discount that a rule can win back.** C6 paid A$4,400–7,500 more tax than the old rule because it made more money. The old rule earned no discount either.

## 2. What was tested

The idea comes from tax law, not from the data. A gain on a share held at least 12 months is taxed on half. A loss is worth the same whenever it is taken.

**Rule D-N** (N = 31, 62 or 92 days; modelled on H82's registered rule C6, which uses 31):
- When C6 would sell a holding that is **in profit** and its 12-month date (367 days after purchase) is within N days, the sale waits until that date. It is then sold on the first session on or after day 367.
- **The mirror:** a holding **in loss** is never kept for tax. It is sold as usual.
- Forced sales are unchanged and override the wait: a pinned takeover price, a payout, and the protection switch moving to the fund.
- At each month-end before the date the holding is tested again: back in the keep zone, it is kept; in loss, it is sold.

Everything else is live C6 (`AMENDMENT_live_EMG2_18_C6`, paper line `EMG2_18_SIM_BT_C6`). A$10,000 start, IBKR tiered brokerage, modelled spread, tax at 32% with the gain halved after 367 days, losses carried forward, everything sold and taxed at the end.

**Check before any test:** the engine was extended so a book can sell on a day inside the month. With the delay switched off it reproduces C6 exactly on both ASX data sets (A$34,519.80 and A$30,795.23) and in all ten overseas market-versions.

**Bar, fixed in advance:** at least A$500 more than live C6 on both ASX data sets; not worse overseas in the middle case; worst fall not more than 2 points deeper.

## 3. Choosing N overseas

Ten market-versions from files on disk: Thailand, Malaysia, China (two versions), Korea main board (two), Taiwan main board (two), Canada (two). Twelve start months, December 2017 to October 2026.

| Market-version | C6 ends with | 31 days | 62 days | 92 days | Sales delayed per book (31 days) |
|---|---|---|---|---|---|
| Canada, same rank | 29,431 | +496 | +1,236 | +1,908 | 1.0 |
| Korea, same percentile | 13,353 | +417 | +1,010 | +1,391 | 1.0 |
| Malaysia | 13,820 | +118 | +118 | +3 | 1.0 |
| Canada, same percentile | 12,173 | 0 | 0 | 0 | none |
| Korea, same rank | 11,970 | 0 | 0 | −9 | none |
| China, same percentile | 6,366 | 0 | −601 | −601 | none |
| Taiwan, same percentile | 20,754 | 0 | −385 | −354 | none |
| Thailand | 14,295 | −99 | −55 | +28 | 1.5 |
| Taiwan, same rank | 21,377 | −312 | −312 | −835 | 1.4 |
| China, same rank | 15,316 | −619 | −1,128 | −1,625 | 2.0 |
| **Middle result** | | **0** | **−27** | **−4** | |

- **31 days was chosen** by the rule fixed in advance: the only one not worse than C6 in more than half the market-versions (7 of 10, four of them because it did nothing). It held with any one market left out. It is robust at zero.
- 62 and 92 days failed (not worse in only 5 of 10; middle result below zero).
- Worst fall: unchanged in the middle case for all three.
- Every delayed sale at 31 days reached its date. The tax saved was real (Canada rank: A$2,332) but what the share did in the extra weeks was just as large and of either sign (Canada rank: −A$1,837; China rank: −A$797).

## 4. The ASX result

Research panel (includes dead companies) and vendor file, 12 start months December 2017 to November 2018, to November 2026. A200 fund over the same period: A$18,586.

| | Live C6 | Wait 31 days (chosen) | Wait 62 days (information) | Wait 92 days (information) |
|---|---|---|---|---|
| **Research panel: ends with** | A$34,520 | A$34,520 (**0**) | A$33,914 (−606) | A$33,952 (−568) |
| Start months ahead / behind | | 0 / 0 | 3 / 9 | 3 / 9 |
| Sales delayed per book | | 0 | 1.0 | 1.9 |
| Tax paid | A$11,285 | A$11,285 | A$10,997 | A$10,921 |
| Tax saved / return lost | | 0 / 0 | +769 / −1,374 | +1,165 / −1,734 |
| Worst fall | −51.4% | −51.4% | −51.4% | −51.4% |
| Five best holdings removed | A$27,534 | A$27,534 | A$27,005 | A$27,034 |
| **Vendor file: ends with** | A$30,795 | A$30,795 (**0**) | A$30,379 (−416) | A$30,379 (−416) |
| Start months ahead / behind | | 0 / 0 | 0 / 12 | 0 / 12 |
| Sales delayed per book | | 0 | 3.0 | 4.0 |
| Tax paid | A$9,786 | A$9,786 | A$9,049 | A$9,049 |
| Tax saved / return lost | | 0 / 0 | +2,620 / −3,037 | +2,620 / −3,037 |
| Worst fall | −42.2% | −42.2% | −42.2% | −42.2% |
| Five best holdings removed | A$24,381 | A$24,381 | A$24,048 | A$24,048 |

- **Bar:** +A$0 on both data sets against +A$500 needed. **Failed** on item 1. Items 2 and 3 are met only because nothing happens.
- **Why 31 days never acted.** C6's longest holding was 306 days on the panel. On the vendor file one share (CTM) reached 365 days with a A$304 gain, two days short of the discount, and was sold by the protection switch, which the rule must obey.
- **Control without the "in profit" test:** also no action, A$0.
- **Random twins.** The real book beats 100 of 100 twins on both data sets, exactly as C6 does. More useful: the same 100 random books run with and without the 31-day wait. Half were unchanged; the rest split 25 higher / 25 lower (panel) and 28 / 21 (vendor). Average difference −A$6 and +A$15. A random book delays less than one sale in 8.9 years.
- "Tax saved / return lost" is measured by re-running each rule with tax switched off; the two parts add up to the difference.

## 5. Where C6's gains are realised (why the discount is out of reach)

Average per start month, live C6, 2018 to November 2026:

| How the share left the book | Research panel: gains | Vendor file: gains | Days held, middle case | Longest |
|---|---|---|---|---|
| Sold by the protection switch (forced) | A$23,214 | A$21,291 | 62 | 274 / 365 |
| Sold by rule C6 (or pinned price) | A$28,093 | A$23,862 | 182–185 | 306 / 332 |
| Payout | A$438 | A$994 | 90 | 184 / 306 |

- The switch stepped aside 8 times (panel) and 9 times (vendor) in 8.9 years. Each time it sold every share, most of them recently bought.
- Of the gains sold by rule C6, 84–86% were sold within 214 days and none after 335 days.
- If every gain had earned the discount the tax bill would have been A$8,000 lower on paper. That is not a target: it would need every winner held past 12 months, through every step-aside, which is a different strategy with different results.
- One real exception: the A200 fund holding. On the panel A$1,079 of fund gains per start already earned the discount, because the book sat in the fund for more than a year. On the vendor file none did (longest 303 days). This was not tested and is not proposed.

## 6. Verdict in dollars

| | Research panel | Vendor file | Overseas, middle of ten |
|---|---|---|---|
| Wait 31 days (chosen) against live C6 | A$0 | A$0 | A$0 (−619 to +496) |
| Wait 62 days | −A$606 | −A$416 | −A$27 |
| Wait 92 days | −A$568 | −A$416 | −A$4 |

- **No draft amendment was written.** The live rule, the paper lines and the code stay as they are.
- A delayed sale saves 16 cents of tax per dollar of gain. A typical gain in this book is A$300–500, so the prize is A$50–80. The share being held is one the rule wants out of, worth about A$1,000, and it moves more than that in a month in either direction. The tax saving is real but smaller than the noise it buys.
- The 12-month discount should not be counted in any forecast for this book.

## 7. Limits

- The 31-day rule produced no event on the ASX, so the ASX says only "it does not arise", not "it is harmful". The 62- and 92-day results rest on one to four names per book.
- Overseas runs apply Australian tax and A$ brokerage to local prices; no currency, stamp duty or withholding tax.
- The overseas markets had been used before for C6 itself (reports 99, 100), though never for holding periods.
- Start months share the same years: "9 of 12 behind" is one result seen several times.
- The sale on the 12-month date assumes the daily job can place one sell order inside the month. Not built, and not needed now.
- Trials: 3 candidates overseas, 1 control, 2 non-chosen waits shown on the ASX = 6. **N 2,958 → 2,964** (ledger not written).
- Files: `deep101/PREREG_101.md`, `FREEZE_101.md`, `out/prereg101_hash.txt`, `out/freeze101_hash.txt`, `out/design_read.log`, `out/readj_panel.log`, `out/readj_vendor.log`, `out/why_panel.log`, `out/why_vendor.log`, `out/twins_read.log`, `code/eng101.py`. Overseas panels deleted.
