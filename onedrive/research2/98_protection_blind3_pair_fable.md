# Report 98 — Does the band-trend protection help BLIND3 or the PAIR? And which book for the mid-December money?

Fable, 20 November 2026. Research only: no live code, ledger, scheduled task or `/home/user/asx-trader` file was touched; no vendor request was made (data on disk only). Working folder `deep98/` (`PROGRESS.md`, `PREREG_98.md` hashed before any run, `PREREG_98b.md` and `PREREG_98c.md` for two additions outside the plan, hashes and logs in `out/`).

## 1. Answer

1. **The protection does not help BLIND3 or the PAIR. It costs them money and barely trims their falls.** A$10,000, 12 start months from Dec 2017, to Nov 2026, after IBKR tiered brokerage and tax: BLIND3 ends A$3,100–7,900 lower with the switch, the PAIR about A$8,000 lower. Their worst fall is the fast one of March 2020, which a month-end rule does not see in time. None of the four protected versions passed any of the first four lines of the bar set in advance. **No amendment is drafted.**
2. **A fault was found in the replay behind report 96's protection figures, and it changes them.** In that replay, when one share could not be sold on the day of a step-aside (suspended, usually a takeover), the engine refused the index-fund order and left the whole book in cash for a month. That happened at the February 2020 step-aside, so the replayed book sat in cash through the March 2020 crash and bought the fund near the low. The registered rule says the money goes to the fund the next day. Run as written, the protection on EMG2-18 gives:

| EMG2-18, mean of 12 starts | Plain | Protection, report 96 replay | **Protection as the rule is written** |
|---|---|---|---|
| Ends with, research panel | A$28,067 | A$30,485 | **A$28,277** |
| Ends with, vendor file | A$23,731 | A$26,443 | **A$23,927** |
| Worst fall (panel / vendor) | −56% / −58% | −32% / −40% | **−46% / −53%** |
| Value at Dec 2025 (panel / vendor) | A$35,028 / 31,254 | A$30,980 / 26,744 | **A$28,743 / 24,223** |
| Given back from peak to today (panel) | A$16,255 | A$7,272 | A$6,783 |

   So the switch, correctly run, ends with about the same money as plain EMG2-18 (A$200 more), with a worst fall 5 to 10 points shallower, not 18 to 24. It still halves the 2026 give-back, and it was still A$6,000–7,000 behind at the end of 2025. **The owner chose the protected live start on the report 96 figures; that choice should be re-confirmed on these.**
3. **Recommendation for mid-December: stay with the registered EMG2-18_BT, with eyes open; do not switch to BLIND3 or the PAIR now.** Nothing tested here clearly beats it on the terms fixed in advance, and neither BLIND3 nor the PAIR has live code or a month of paper running. If either is ever run with real money, run it **plain**, without the switch.
4. **The plain PAIR is the strongest book on paper** (A$33,049 panel / A$27,525 vendor; ahead of the corrected EMG2-18_BT from all 12 starts on both data sets). It is not recommended for December because it was assembled after both halves had been seen on these same years, it falls as far as EMG2-18 does (−47% / −54%), and it has not been built. It is a reason to bring its owner decision forward from June 2027 once it has paper months behind it.

## 2. The comparison in dollars

A$10,000, mean of 12 start months (Dec 2017 to Nov 2018), valued Nov 2026, everything sold and taxed. ASX 200 fund on the same basis: A$18,586, worst fall −36%.

| Book | Ends with, panel | Ends with, vendor | Worst fall, panel / vendor | At Dec 2025, panel | Given back since peak, panel | Orders; brokerage a year | Starts ahead of fund, panel / vendor |
|---|---|---|---|---|---|---|---|
| EMG2-18 plain | 28,067 | 23,731 | −56% / −58% | 35,028 | 16,255 | 110; A$613 | 12 / 12 |
| **EMG2-18_BT, report 96 replay (registered reference)** | 30,485 | 26,443 | −32% / −40% | 30,980 | 7,272 | 89; A$517 | 12 / 12 |
| EMG2-18_BT as written (corrected, outside the plan) | 28,277 | 23,927 | −46% / −53% | 28,743 | 6,783 | 88; A$505 | 12 / 12 |
| BLIND3 plain | 27,213 | 21,010 | −42% / −44% | 25,760 | 3,457 | 47; A$258 | 12 / 11 |
| BLIND3 + switch on the 301–600 band (B3_a) | 20,796 | 16,796 | −40% / −40% | 20,723 | 3,521 | 46; A$266 | 12 / 0 |
| BLIND3 + switch on its own top-400 index (B3_b) | 19,295 | 17,896 | −40% / −40% | 18,663 | 1,905 | 53; A$305 | 9 / 3 |
| PAIR plain | **33,049** | **27,525** | −47% / −54% | 35,034 | 10,595 | 132; A$735 | 12 / 12 |
| PAIR, each half on its own switch (PAIR_c) | 24,835 | 19,399 | −42% / −54% | 24,449 | 4,088 | 113; A$637 | 12 / 10 |
| PAIR, both halves on the band switch (PAIR_a) | 25,396 | 19,167 | −41% / −54% | 25,312 | 4,465 | 111; A$627 | 12 / 7 |
| PAIR, only the EMG2 half switched (PAIR_e, outside the plan) | 29,907 | 22,036 | −44% / −54% | 29,392 | 5,717 | 109; A$609 | 12 / 12 |

Range across the 12 starts (panel): EMG2-18_BT replay 29,254–31,926; corrected 26,875–29,367; BLIND3 plain 20,999–33,900 (it depends heavily on the start month); PAIR plain 30,005–37,730.

Other checks (panel, vendor in brackets):

- **Five best holdings removed:** EMG2-18_BT replay 23,306 (19,276); corrected 21,716 (17,220); BLIND3 plain 20,383 (15,031); PAIR plain 23,905 (18,630); every protected BLIND3 or PAIR 15,700–20,000 (13,500–14,300).
- **Spread doubled:** EMG2-18_BT replay 25,974 (22,362); corrected 24,327 (20,864); BLIND3 plain 25,163 (17,641); PAIR plain 29,205 (25,314).
- **Random twins:** each plain book and each EMG2 version beat 98–100 of its 100 twins. Protected BLIND3 fell to the 71st–91st place: the switch is the part doing the damage, its twins with the same switch nearly catch it.
- **2006–2017 (research panel only, a decade BLIND3 was designed on, so it flatters BLIND3):** fund 18,081; EMG2-18 plain 12,129; EMG2-18_BT 11,819 (worst fall −59%); BLIND3 plain 23,458; B3_a 26,216; B3_b 22,021; PAIR plain 20,718; PAIR_c 14,984; PAIR_a 16,389. The band switch helped BLIND3 in that decade (11 of 12 starts) and hurt it in 2018–2026 (0 of 12): no steady effect.
- **January 2020 start (panel):** EMG2-18_BT replay 31,184; corrected 28,633; BLIND3 plain 17,101 (fund 15,869); B3_a 17,113; PAIR plain 30,580; PAIR_c 21,515; PAIR_a 22,621.

## 3. Why the switch hurts BLIND3 and the PAIR

- **It is out of the shares 35–41% of the time**, and BLIND3's shares kept rising through most of those months. BLIND3 buys the calmer names of the top 400; its plain book fell only 19–21% in 2026, against 39–40% for plain EMG2-18. There was little to protect.
- **It does not catch the fall that matters.** BLIND3's and the PAIR's worst fall is February–March 2020. The switch turned OFF at the end of February; the shares were sold on 2 March and the money went into the index fund, which then fell with everything else. Worst fall with the switch: −40% against −42% to −44% plain.
- **It returns late.** After the 2020 crash the switches stayed OFF until July/August; plain BLIND3 and plain PAIR made most of their 2020 gain in those months.
- **It turns long holdings into taxed sales.** Plain BLIND3 holds for years and paid about A$1,280 of tax over the run (panel); with the switch it sells everything at each step-aside (eight or nine in nine years) and paid A$2,800–3,160, losing the 12-month discount.
- **Only the EMG2 half switched (PAIR_e)** was tried afterwards as the obvious repair. It still ends A$3,100 (panel) and A$5,500 (vendor) below the plain PAIR, with nearly the same worst fall.

## 4. The fault in the report 96 replay

- **What happens.** At an OFF decision the report 96 engine allows the book one holding, the fund. If a share cannot be sold that day (no trade for five sessions), that leftover counts as the one holding, the fund order is refused, and the book waits in cash until the next month-end.
- **When it happened** (Dec-2017 book, research panel): June 2018 (VLA stuck), February 2020 (QMS and WBA stuck), September 2023. The February 2020 accident also happened on the vendor file. Because every start month held the stuck shares, all 12 starts had the same accident.
- **What it was worth.** March 2020 in cash instead of the fund, then the fund bought on 1 April 2020 at 11,740 instead of 2 March at 14,157: about 17% of the book. That one month is the whole of the A$2,400–2,700 lead report 96 gave the switch over plain EMG2-18, and most of the smaller worst fall.
- **Check.** Two independent codings of the rule as written agree (Dec-2017 start, panel): A$26,875 and A$26,988, worst fall −46.6% and −46.5%. The report 96 replay gives A$29,254 and −32.2%.
- **What is not affected.** Plain EMG2-18, the "to cash" versions of report 96, and every BLIND3 and PAIR figure here (their switch code buys the fund even when a share is stuck). The 2006–2017 figure is unchanged (no share was stuck at an exit in that run).
- **With the corrected rule the Dec-2017 book's lowest value is A$5,769 (panel)** in March 2020, below the A$6,000 step of the staged loss rule; in the report 96 replay it was A$7,289.
- **For the build:** the live system must have a stated behaviour for a share that cannot be sold on a switch day. The rule as registered implies: buy the fund with the cash that is available, and sell the stuck share when it trades. This needs confirming in the build document before go-live; nothing was changed here.

## 5. Overseas check (BLIND3 only; plain, B3_a, B3_b)

Thailand, China and Malaysia, in the rank and percentile versions of report 95 (six market-versions; the engine reproduces report 95's plain BLIND3 figures exactly). Korea and Taiwan could only be rebuilt from their main boards (the second boards' files are lost), so they are shown apart.

| A$10,000, 12 starts from Dec 2017 | BLIND3 plain | + band switch | + own-index switch | Local fund |
|---|---|---|---|---|
| Thailand, rank / pct | 10,716 / 6,979 | 12,517 / 11,790 | 12,014 / 10,725 | 11,166 |
| China, rank / pct | 6,685 / 4,910 | 10,547 / 9,698 | 11,062 / 10,839 | 11,801 |
| Malaysia, rank / pct | 20,577 / 26,099 | 11,026 / 12,694 | 11,093 / 13,064 | 11,399 |
| Middle of the six | 8,847 | 11,408 | 11,078 | 11,399 |
| Worst fall, middle of the six | −51% | −40% | −40% | −38% |
| Korea main board, rank / pct (partial) | 18,113 / 20,845 | 11,397 / 16,270 | 10,466 / 14,438 | 32,054 |
| Taiwan main board, rank / pct (partial) | 23,182 / 26,753 | 38,953 / 31,518 | 33,407 / 28,287 | 56,188 |

The switch "passed" its overseas line (more money in 4 of 6, shallower fall in 6 of 6), for the reason written down beforehand: where plain BLIND3 lost money (Thailand, China) holding it less helped; where it worked (Malaysia, Korea) the switch cut the result by a fifth to a half. The overseas switches were OFF 46–64% of the time in the three main markets. This is the same pattern as on the ASX: the switch helps a losing book and hurts a working one.

## 6. The bar, as fixed in advance

Against EMG2-18_BT (report 96 replay), on both ASX data sets: (1) at least 5% more money and ahead in 9 of 12 starts; (2) worst fall no more than 2 points deeper; (3) value at Dec 2025 at least equal; (4) at least equal with the five best holdings removed; (5) 75th place or better among its twins; (6) ahead of the fund in 10 of 12 starts; (7) overseas not worse than plain.

| Candidate | Money against EMG2-18_BT, panel / vendor | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| B3_a | 68% / 64% | ✗ ✗ | ✗ ✓ | ✗ ✗ | ✗ ✗ | ✓ ✗ | ✓ ✗ | ✓ |
| B3_b | 63% / 68% | ✗ ✗ | ✗ ✓ | ✗ ✗ | ✗ ✗ | ✓ ✓ | ✗ ✗ | ✓ |
| PAIR_c | 81% / 73% | ✗ ✗ | ✗ ✗ | ✗ ✗ | ✗ ✗ | ✓ ✓ | ✓ ✓ | ✓ |
| PAIR_a | 83% / 72% | ✗ ✗ | ✗ ✗ | ✗ ✗ | ✗ ✗ | ✓ ✓ | ✓ ✗ | ✓ |

All four also end below the corrected EMG2-18_BT in every one of the 12 starts on both data sets, so the result does not depend on which reference is used. Closest: PAIR_a on the panel, at 83%.

## 7. Recommendation for the mid-December real-money start

| Option | Verdict | Why |
|---|---|---|
| **EMG2-18_BT (registered)** | **Keep, after the owner re-confirms on the corrected figures** | The only book with live code and a paper month. Corrected replay: about the same money as plain EMG2-18, worst fall 46–53% in place of 56–58%, half the 2026 give-back; A$6,000–7,000 less than plain at the end of 2025. The switch is OFF now, so the book starts in the ASX 200 fund. |
| EMG2-18 plain | The alternative the owner may prefer | Same end money on the replay; deeper falls; no time spent in the fund. The case for the switch is now "a somewhat steadier ride resting on one fall (2026)", not "more money and a much smaller fall". |
| BLIND3 plain | Not for December | Less money than EMG2-18 on the vendor file (21,010 against 23,731), result depends on the start month, behind the local fund in most overseas markets, no live code, registered as paper-only for 24 months. Its strengths: half the orders, shallower falls, held up in 2026. |
| BLIND3 protected | No | A$3,100–7,900 worse than plain; behind the index fund on the vendor file in 9–12 of 12 starts. |
| PAIR plain | Not for December; strongest candidate for a later decision | Most money on both data sets, ahead of the fund from every start, also ahead in 2006–2017. But assembled with these years in view, falls as far as EMG2-18, 132 orders and A$735 of brokerage a year, no live code. |
| PAIR protected (any of three forms) | No | A$3,000–8,000 worse than plain PAIR with nearly the same worst fall. |

No `AMENDMENT_live_switch.DRAFT.md` was written: no candidate clearly beats the registered book on both data sets, and none is sturdier.

**Two things for the owner and the coordinator before go-live:**
1. Re-confirm the choice between EMG2-18_BT and plain EMG2-18 on the corrected figures of section 1.
2. Fix in the build document what the live system does when a share cannot be sold on a switch day (section 4).

## 8. Limits

- EMG2-18_BT itself did not pass report 96's bar, and its replay lead is now shown to have rested on an engine accident. The corrected run is outside the plan fixed for this report (written down and hashed before its 12-start run, but after the fault was seen on one start).
- 2018–2026 is not unseen for any of these books: EMG2's band was chosen with it in view, the PAIR was assembled after both halves were seen on it. BLIND3 was built blind to it.
- The research panel and the vendor file differ by A$4,000–6,000 for every book; the ordering of the books is the same on both except that BLIND3 plain drops below plain EMG2-18 on the vendor file.
- In the PAIR each half runs on A$5,000 and holds about nine names, so its results vary more with small changes than a whole-book result; the three protected PAIR forms differ from the sum of their halves for that reason.
- Costs are modelled; no real fill has yet been compared with the spread model. The fund's spread is set at 0.05% a side. Cash earns 0%.
- Overseas: three Asian markets of report 95's ten, plus two partial ones; no currency, stamp duty or withholding tax.
- The 2026 fall is unfinished, and both switches are OFF at the last month-end.

## 9. Trial count

N before: 2,883. This work: 4 ASX variants (B3_a, B3_b, PAIR_c, PAIR_a); 2 switch rules × 10 overseas market-versions run (6 planned, 4 partial extras) = 20; 1 outside the plan (PAIR_e); 1 for the corrected EMG2-18_BT (counted to be conservative). 26 in all. **N = 2,909.** Twins, start months, stresses, the Dec-2025 stop, the 2006–17 run and the plain re-costings are not counted. Ledger not written.

Files: `deep98/PREREG_98.md`, `PREREG_98b.md`, `PREREG_98c.md`; `deep98/out/read_panel.log`, `read_vendor.log` (planned tables and bar), `read_ov.log`, `go_ov.log` (overseas), `read_b.log` (PAIR_e), `read_c.log`, `table_all_panel.csv`, `table_all_vendor.csv` (all books incl. the corrected rule), `chk98b.log`, `chk98c.log` (the fault); code in `deep98/code/`.
