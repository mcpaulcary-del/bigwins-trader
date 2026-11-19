# 85. Full review of Big Wins, the whole FD, the gap register, and the direction from here

19 November 2026. Author: research agent (Fable). Owner instruction: full review of everything, Big Wins only, no long game, rewrite the FD, no gaps, learn every 2 hours or every day; then: review the entire FD and close gaps in the algorithm.
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades.
Work folder: `scratchpad/deep85/` (`PREREG_85.md`, `85b`, `85c`, `85d`, hashes in `out/prereg85_hash.txt`, `code/`, `out/`, `PROGRESS.md`). The live paper record, ledger, frozen code and scheduled jobs were read, never written. No data were downloaded.
Companion document: `FD_v3.0_BigWins.md` (the new functional design).
**Update, same day:** the owner answered the decisions of section 6.4 (`OWNER_DECISIONS_2026-11-19.md`): D-1 yes, D-2 yes, D-3 yes, D-4 A$10,000, D-5 IBKR paper first, D-6 yes if lawful and under about A$50 a month (owner confirms before purchase), D-7 yes. FD v3.0 is written on that basis. Drafts for registration: `scratchpad/deep85/AMENDMENT_shadow_EMG2.md` and `AMENDMENT_adopt_rule_v3.md`.
**Reports 83 and 84 landed after this report was written.** Report 83: no verdict changes on corrected overseas data; the loser screen on blunt weights weakens to +1.5 to +1.7 (t 2.5–2.8); the screened ranks-101–300 sleeve failed (+0.7, t 0.6; −1.1 on ASX), which agrees with T4's band B row below. Report 84: new listings as a group trail the index by 2–10 points a year; no indicator predicted average returns in both periods; no rule passed; its EARLY line is an unproven shadow whose lead rests on one to three companies. Sections 2.4 (items 5–6) and 5 below were written before those results and are consistent with them; FD v3.0 section 8.5 carries the detail.
**Second update, same day:** the owner overrode the 12-month paper step of section 6.3: **A$10,000 of real money in a 20-company version of EMG2, automated through IBKR, from mid-December 2026 after one paper month.** My recommendation in this report was 12 months of paper first, and it has not changed: at A$10,000 IBKR's A$6.60 minimum costs about A$840–930 a year (8–9% of the capital), more than the back-test lead, so the expected result of that slice is below the index even if the signal works. It is the owner's decision; FD v3.0 implements it with a fast build path, a go-live checklist, per-order approval, hard loss limits and the v3 stop rules (FD sections 7.9, 18.4, 21.1; draft `scratchpad/deep85/AMENDMENT_live_EMG2_20.md`).

**Tags.** [run] computed by me today. [report n] from report n. [code] read in code. [judgement] my opinion. [memory] from my own knowledge, not re-checked today.

---

## 0. Answer first

### 0.1 The verdict in eight lines

1. **Big Wins has been fishing in the wrong pond.** About 1,760 counted trials were spent on price rules inside the 100–300 most-traded ASX shares. That work is sound and its answer is final: there, share-picking is worth about +3 points a year and the way the book must be built costs it all back. True edge after costs and tax: about +0.2 a year [reports 80–82]. More work there is waste.
2. **The big winners are not born there.** Of all ASX shares that rose five-fold within three years (2010–2023 starts), **97% started outside the 100 most traded, and 78% outside the 300** [run, test T1]. The baseline engine (H82) today holds Computershare, QBE, Ramsay, Woolworths, APA and ASX Ltd. That is a low-volatility large-company book. It is not a big-winner engine and never could be.
3. **Outside the top 300 the same momentum score is three to five times stronger.** In traded-value ranks 301–600 the best fifth by score beat that band's average by **+17 points a year in 2018–2026 (t 4.5) and +27 in 2010–2017 (t 3.5)**. Inside ranks 101–300 the figure for 2018–2026 is +5 (t 1.4) [run, T4].
4. **A book built on it is the largest lead this programme has found, and it still fails the statistical bar.** "EMG2" (hold the best fifth of ranks 301–600, refresh monthly; about 45 names): **13.3% a year after spreads and after tax paid each year, against 8.5% for the ASX 200 total-return index, 2018–Oct 2026**; 11.0% against 7.4% in 2010–2017. It beat all 100 random twin books in both periods. It caught real multi-baggers while they were small (Clarity, MTM, EOS, Ora Banda, Lindian; earlier Pilbara, Northern Star, Senex). **But its monthly t against the index is 1.0**, because it swings 20–25 points a year around the index, and it fell 38% and 57% at its worst [run, T6]. By the bar I wrote before running it, it is a fail on statistical strength, not on size.
5. **"Buy and keep the winners" does not work in that band.** The slow version (EMG1: buy the strongest, sell only when it becomes a loser) made 5.9% against 8.5% [run, T5]. Down there the signal has to be refreshed monthly. The owner's instinct (look often, act) is right for this band; my earlier keep-winners suggestion is wrong for it.
6. **Three popular ideas are now closed by direct test:** buying the day after a big jump on heavy volume (no further gain; T2); selling the day after a big fall (not supported at 60 days; the monthly loser test already catches these; T3); and fishing among small or young companies without a score (their average three-year return is 8–19% against 31% for the top 100, and a third to a half of them halve; T1).
7. **The adopt rule now in force can never approve the one promising line.** Adopt rule v2 needs t ≥ 3 against the index. A book that swings 20 points a year around the index with a true +5 edge needs about 140 years for that. The owner has to choose: keep v2 and accept that Big Wins is a permanent paper exercise, or accept a different evidence ladder for high-swing lines (section 6.3). I recommend the second, with the money capped at what the owner can lose.
8. **The process, not the ideas, is why the work kept going backwards.** Seven data or code faults each forced earlier numbers to be withdrawn (section 2.3). All came from research run on one-off scripts over unverified vendor data. The fix is in the new FD: one tested data layer, one engine of record, and a prediction ledger that scores every signal every day.

### 0.2 What the owner should expect, plainly

| Line | What history says, after costs and tax | My forward estimate [judgement] | Ride |
|---|---|---|---|
| H82 and every top-300 line (M3, E3, CXL, ACC) | Level with the ASX 200 fund, ±1.5 | −0.3 to +0.6 a year, most likely +0.2 | Like the index, a little bumpier |
| **EMG2 (ranks 301–600, monthly)** | +4.9 a year (2018–26), +3.6 (2010–17), on data that had been seen | **+1 to +3 a year if it holds up; zero is quite possible.** Halve history and double the spread (the programme's own haircut) and the 2018–26 lead is +1.2. Chance the true edge is +1 or more: about 35–40% | Rough. A 40–60% fall at some point. Years 25 points behind the index (2022, 2026) and years 25 ahead (2019, 2021, 2024). About 310 trades a year |
| Young companies (new listings), unselected | Median −18% in the first year against +3% for the index; 36% halve; 18% double [tracker baseline] | Negative unless report 84 finds a filter that works | Lottery |

No line promises "big wins" as a result. EMG2 is the only one in which big winners actually show up while they are still small, and the only one whose historical lead is larger than the costs and the noise of the machinery. It is a bet with roughly one-in-three odds of a real edge, not a proven edge.

### 0.3 The single best direction

**Move Big Wins down-market and make it learn at the level of predictions.**

1. **Make EMG2 the lead challenger.** Register it before 30 November as a forward paper line with random twins, at A$100,000, on the IBKR paper account as soon as the system can place paper orders. H82 stays as the registered baseline; M3, E3, ACC and CXL keep running because they cost nothing, but no more research goes into the top 300.
2. **Measure the signal, not just the book.** The band-C spread (best fifth minus band average) is a much quieter measurement than book-against-index. If history repeats it reaches t = 2 in about 21 months and t = 3 in about 4 years; at half strength, 7 and 16 years. That is the fastest honest evidence available, and it is updated every month, with a daily prediction ledger underneath it (FD section 15).
3. **Replace "prove it for decades, then invest" with "risk little, learn fast".** Proposed adopt rule v3 for high-swing lines: a small capped pilot after 12 months of clean paper operation, growing only as the forward spread evidence accumulates (section 6.3). Owner decision.
4. **New listings get their own module and their own line**, fed by report 84 when it lands. Until then they are tracked and alerted daily, and a young company can enter EMG2 only through the same door as any other (enough history for the score). Lottery-size caps apply.
5. **Stop** multi-market back-tests of top-100 price rules, further variants of H82, fast breakout/stop rules, and further full-document "final reads" of the FD.

### 0.4 What must be registered and built first

| # | Item | Who | When |
|---|---|---|---|
| 1 | Owner decisions D-1 to D-7 (section 6.4): accept EMG2 as lead challenger; adopt rule v3 or not; pilot cap; broker for small shares; data budget; announcements source; freeze lifted for FD v3.0 | Owner | Before 30 Nov |
| 2 | `AMENDMENT_shadow_EMG2.md`: rules exactly as FD v3.0 §7.6, books A$100k and A$25k, 100 random twins each, band-spread measurement line; hash and ledger before the 30 Nov decision | Record keeper | Before 30 Nov |
| 3 | Note in the ledger: report 85 trials T1–T6 (+6), with results, so the count stays honest | Record keeper | Now |
| 4 | Fix the new-listings tracker's ISIN column (`registry.csv` stores a Python method name, not the ISIN, so the rename test by ISIN is not working) [code/data] | Tracker owner | This week |
| 5 | Move the forward record out of the scratchpad to durable storage with a daily off-site copy. The disk is 98% full and the scratchpad can be cleared by a restart | Whoever runs the server | This week |
| 6 | FD v3.0 milestone B1 (data layer for all ASX shares, daily, tested) and B2 (prediction ledger) | Build agent | First |

---

## 1. Six tests run today on data already held

All pre-registered and hashed before the run (`deep85/out/prereg85_hash.txt`). Data: EODHD ASX end-of-day history including delisted and `_old` companies (the file built for report 84), ordinary shares only. Traded value = split-adjusted close × volume. Bands by 252-day median traded value: **A** ranks 1–100, **B** 101–300, **C** 301–600, **D** 601 and below. **Trial count: +6** (85-T1 to T6). Reports 83 and 84 are still running and will add their own; the record keeper should assign final numbers (1,761 after report 83, +28 for report 84, +6 here: 1,795).

### 1.1 T1: where the big winners are born, and what fishing there costs (descriptive)

Every June and December 2010–2023: each liquid company's total return over the next three years (`out/t1.txt`).

| Band at the start | Company-starts | Median 3-year return | Mean | Doubled or better | **5× or better** | Halved or worse | Lost 90% | Share of all 5× outcomes |
|---|---|---|---|---|---|---|---|---|
| A (1–100) | 2,674 | +23% | +31% | 11% | **0.3%** | 8% | 1.5% | 3% |
| B (101–300) | 5,269 | +4% | +19% | 12% | **1.0%** | 23% | 5.5% | 19% |
| C (301–600) | 7,318 | −13% | +14% | 12% | **1.9%** | 34% | 9% | 49% |
| D (601+, ≥ A$50k a day) | 3,462 | −33% | +8.5% | 11% | **2.4%** | 42% | 11% | 29% |

- The pre-set reading "the hunting ground is outside the top 100" is **supported** (97% of five-baggers; rate 3–8 times band A's).
- The price is steep. Without selection, each step down loses return: the average falls from 31% to 8.5% over three years, the typical company goes from +23% to −33%, and the chance of halving goes from 8% to 42%.
- **Nothing in the price history marks the future five-bagger.** Companies that had fallen over the prior three years produced five-baggers at 1.8%; those that had already tripled, at 2.2%. The already-tripled group had the worst average of all (+4.6%, typical −38%). Chasing a share after it has multiplied is the worst entry in the table.
- **Age.** In bands C and D, companies listed 2–5 years did worst (mean −10% over three years); under 2 years +5%; over 5 years +18%. Young is a handicap on average, which matches the new-listings baseline.

### 1.2 T2 and T3: catalyst days (event level)

Event: a one-day move of 15% or more on at least three times normal volume, liquid shares, 2010–Oct 2025. Entry or exit at the next day's close. Outcome measured against the average share of the same band (`out/t23.log`).

| | Events | 60-day result vs band, development 2010–17 | Confirmation 2018–Oct 2025 | Bar | Verdict |
|---|---|---|---|---|---|
| **T2 buy after a big up-day** (bands B+C) | 1,010 / 1,627 | −3.0% (t −1.3) | +0.6% per event; −1.0% by month (t −0.9) | ≥ +3%, t ≥ 3 | **Fail. Closed.** No drift after the day. At 250 days the development result was −12% (t −4.1). In the top 100 it is reliably negative |
| **T3 sell after a big down-day** (bands A–C) | 731 / 1,222 | −5.2% (t −2.9) | +0.6% per event; −2.9% by month (t −2.2) | ≤ −3%, t ≤ −3 | **Not supported at 60 days. Rule not added.** Over 250 days these shares do lag (−11%, t −4.3), which is the momentum-loser effect the monthly loser test already acts on |

Plain reading: by the close of the next day the news is in the price. A price-and-volume "catalyst" is not an entry rule and a bad-news day is not an urgent exit rule. The owner's intraday alerts are useful for attention (read the announcement), not as triggers.

### 1.3 T4: the momentum score inside each band (signal level)

Monthly, equal weight, best fifth / worst fifth / band without its worst 30% / whole band, against the ASX 200 total-return index (XTR). Costs: half-spread 0.25% (B), 0.50% (C), 1.0% (D) per side on the names replaced (`out/t4.txt`, `out/t4s.txt`).

| 2018–Oct 2026, % a year | Whole band | Best fifth, before costs | Best fifth, after costs | XTR | Lead | t vs XTR | Best fifth minus band (t) | Worst fifth minus band (t) |
|---|---|---|---|---|---|---|---|---|
| B (101–300) | 4.7 | 9.8 | 7.7 | 8.5 | −0.7 | 0.0 | +4.9 (1.4) | −7.5 (−1.6) |
| **C (301–600)** | 4.4 | **22.3** | **17.4** | 8.5 | **+9.0** | 1.7 | **+16.9 (4.5)** | −16.0 (−3.7) |
| D (601+) | 3.7 | 3.1 | −8.8 | 7.7 | −16.5 | −0.7 | +3.8 (0.5) | −11.7 (−1.4) |

- 2010–2017: band C best fifth 34.6% before costs, lead +20.9 (t 2.1); best fifth minus band +26.7 (t 3.5).
- **Bar** (lead ≥ +3 with t ≥ 2.0, positive in both halves, survives the delisting stress): band C met everything except t (1.66). **Formally a fail.** Bands B and D fail outright.
- Stress, after the run and labelled as such: with a half-tick floor on the spread (a 0.5-cent tick on a 20-cent share is 1.25% a side) the band C lead is +7.4 (t 1.4); capping any share's monthly gain at +100% gives +6.0; the 29 months of data nobody had seen before (June 2024–Oct 2026) give +2.6; removing the three best months gives +3.2; ahead of the index in 12 of 17 calendar years.
- Band B is where H82 lives. This table is the whole diagnosis of reports 81–82 in one row, and band C is the row nobody had tested on licensed data. Report 59's card H101 ("neglected small caps") found the same on the old unlicensed file (+6 a year unseen, t 1.2).

### 1.4 T5 and T6: two books in band C (engine level, A$100,000, costs and tax)

Same monthly engine for both; A$0 brokerage; half-spread 0.50% with the tick floor; 32% tax on net realised gains paid every June (gains held under a year taxed in full); 100 random twin books each (`out/t5.log`, `out/t6.log`). The index is XTR.

| | **T5 EMG1 keep-winners** (40 names; sell only after two months as a loser) | **T6 EMG2 monthly refresh** (hold the best fifth, about 45 names) |
|---|---|---|
| 2018–Oct 2026: return after costs and yearly tax | 5.9% | **13.3%** |
| XTR (before tax / taxed once at the end) | 8.5% / 7.4% | 8.5% / 7.4% |
| Lead | −2.5 | **+4.9** |
| t of the monthly lead | 0.0 | 1.0 |
| Tracking error, points a year | 19 | 20 |
| Percentile among 100 random twins | 81 | **100** (twins' median 0.9%) |
| Worst fall (index −23%) | −39% | −38% |
| Without the single best holding | 4.9% | 12.3% |
| Spread × 2 / A$6.60 brokerage | 4.7% / 5.6% | 9.7% / 12.1% |
| Trades; typical holding | 448; 11 months | 2,777; 2 months |
| Positions that made about 4× or more | 4 | 12 |
| 2010–2017 (printed, not used for choice) | 11.6% vs 7.4%; t 1.0; 92nd percentile | 11.0% vs 7.4%; t 0.8; 100th percentile; worst fall −57% |
| **Verdict by the pre-set bar** | **Fail** | **Fail on t alone** (needed 2.0); every other condition met |

Year by year, EMG2 against XTR: 2019 +55 / +25; 2020 +3 / −1; 2021 +48 / +14; 2022 −18 / +6; 2023 +13 / 0; 2024 +52 / +23; 2025 +23 / +5; 2026 to October −18 / +7. Ahead in six of eight years, far behind in two.

**Honesty about my own bar.** I set t ≥ 2.0 against the index. For a book with 20 points of tracking error, nine years can only give t = 2 if the lead is 13 points a year. So that condition could not have been met by any realistic edge. The quieter evidence is the within-band spread (t 4.5 and 3.5 in two separate periods) and the twins (100th percentile twice). I report the fail as written and I do not move the bar after the fact. Its consequence is that EMG2 goes forward as a challenger on paper, not as a proven rule.

**What could be wrong with it.**
- Both periods had been looked at before in some form (H101 on other data); only mid-2024 onward is new, and there the lead is small (+2.6 in the signal test).
- Real spreads and market impact in A$500,000-a-day shares may be worse than modelled. Doubling the spread takes the lead to +1.2.
- EODHD small-company data have errors I have not audited name by name. The winners listed are real companies with real rises; the 2010–2017 result is sensitive to outliers (capping monthly gains cuts that period's best-fifth return from 26% to 16%).
- Renamed-company duplicates were not removed in these runs.
- It is a size bet as well: band C as a whole trailed the index by about 4 points a year in both periods, and the score has to out-run that.
- Tax is approximate (dividends untaxed on both sides; franking ignored).

---

## 2. Review of the whole programme

### 2.1 What has been learned and is solid

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| 1 | Timing two index funds (rule L1 and 46 others) does not beat holding them | Reports 36, 38, 45–48 | High. Outside the owner's brief now; it is only the benchmark |
| 2 | Inside the top 300, price momentum sorts shares but works as a **loser detector**: the worst tenth returns −13% a year, the rest are alike | Report 81 §2; report 82 (+1.75 to +1.9 on blunt weights, t about 3, 19–20 of 20 markets) | High |
| 3 | In a top-300 book the picking gain (+3) is cancelled by the size handicap against a cap-weighted index (−1.2), cash, bumpiness, costs and tax | Report 81 §1 | High for 2018–2026; the size handicap is a fact about that period, not a law |
| 4 | Every structural fix in the top 300 (cap weights, index core, keep-winners, buffers, tax-aware selling, weekly decisions) moves the result by under half a point | Reports 73, 75–77, 81, 82 | High |
| 5 | Fast breakout-and-stop trading touches nearly every big winner and keeps a median 4% of the rise | Report 81 §6 | High |
| 6 | A price jump on volume has no follow-through; a price crash is not an urgent sell | T2, T3 today | High |
| 7 | Accounts-based filters, loss-makers, share issuance, short interest, commodity drivers, earnings "surprise" on vendor estimates: no use shown, some harmful | Reports 60, 62, 76, 79, 81 §5, 82 | Moderate to high (vendor fundamentals are poor) |
| 8 | Big winners start small; unselected small or young companies are a losing pool | T1 today; tracker baseline; report 84 base rates so far | High |
| 9 | **Momentum is several times stronger in ranks 301–600 than in 101–300, and needs monthly refresh there** | T4–T6 today; report 59 H101 | Moderate: two periods, both seen; fails t against the index |
| 10 | Realistic costs for this owner are lower than the back-tests charged (A$0 brokerage where available; no spread in the closing auction for the top 100) | Reports 80, 82 §7 | High for the top 100; unproven below |
| 11 | Two faithful engines of the same rules differ by up to 1.5 points a year; any smaller lead is noise | Report 81 §3.2 | High |
| 12 | The June tax-loss rebound in small caps (H100) is still alive: +6% in five weeks unseen, t 2.2 | Reports 59, 63 | Low to moderate; one observation a year |

### 2.2 What was wasted

| Item | Why it was waste | Cost |
|---|---|---|
| Reports 07–30 and 49–50, FD v1.2 to v2.13: fourteen FD versions in two days and six "final reads" | A 640 KB specification for a two-fund timing product the owner does not want, whose own research said the rule loses money | Most of week one |
| Rounds 3–8 across 20 foreign markets | Repeated the same top-100 price rules on the same nine years in markets the owner will never trade, on vendor data that turned out faulty in several of them | About 1,300 of the 1,760 trials |
| The deflated-Sharpe bar on forward lines | A rule that could never say yes; replaced only on 19 Nov | Framed every result as hopeless |
| A$5,000 four-share books and 405 paper books | Measure luck and cash drag | Noise on the scorecard |
| The two-hourly intraday job as built | It archives quotes and prints alerts. It makes no forecast and scores nothing, so nothing is learned from it | Credits; the owner's patience |
| My own keep-winners recommendation (report 80, the ACC line) | Reasonable for the top 100, wrong where the big winners are; T5 shows the slow form loses in band C | One shadow line that will read "level with the index" |
| Thirteen amendments in four days | Each was honest, but the record now has rules spread over fourteen files | Hard to audit; the FD consolidates them |

### 2.3 Why it kept going backwards

Seven faults, each found after results had been reported:

| Fault | Found in | Effect |
|---|---|---|
| Vendor volume split-adjusted, close not: "most traded" favoured future winners | Report 73/74 | One test fell from +10.9 to −1.2 |
| ASX pack had zero traded value from Dec 2024 | Report 77 | M3 on ASX fell from +3.6/+1.5 to +1.3/−0.5 |
| `_old` symbols dropped (12 real top-300 companies missing) | Report 80 | H82 8.35/9.32 → 6.94/8.93 |
| Ten renamed companies counted twice | Report 81 | H82 A$100k moved +0.8 |
| US pack ranked on adjusted price × volume (penny shares in the "top 100") | Report 82 | Every US figure in rounds 3–8 suspect |
| Foreign packs lack the volume guard; flip-flop split data | Report 83 (running) | Four more markets being rebuilt |
| Rule text and code disagree (M3 R7; paper comparator brokerage; engines differ by 1.5 points) | Reports 77, 80, 81 | Readings restated |

One root cause: **research was run on throw-away scripts over vendor files nobody had tested, in a scratch folder.** Every new round rebuilt its own data pack. The cure is not more review; it is one data layer with tests, one engine of record, and results that are recomputed automatically when a data fix lands. That is what FD v3.0 specifies (sections 6, 13, 16).

A second cause is in the brief the agents were given: the benchmark and the universe were fixed early (top 300, yearly or monthly, beat the cap-weighted index) and each round varied the signal or the structure inside that box. Nobody was asked whether the box was right. The owner kept asking for big winners; the programme kept answering about large companies.

### 2.4 Where the direction is wrong today

1. **The baseline is mis-named.** H82 buys steady large companies. Keep it as the registered control; stop calling its results "Big Wins".
2. **All five running lines are in the top 100–300.** None can hold a big winner while it is small.
3. **The adopt rule is tied to book-against-index t**, which only low-swing, index-like books can ever satisfy. It selects for exactly the lines that cannot produce big wins.
4. **The learning loop does not exist.** Jobs run daily and two-hourly, but nothing is forecast, scored or compared automatically.
5. **Report 83's question** (a screened mid/small sleeve in ranks 101–300) is answered by T4's band B row for ASX: the screen adds +2 a year there and the best fifth is level with the index. Worth finishing as the pooled measurement; do not expect a line from it.
6. **Report 84's question** (young companies) is the right kind of question. Its base rates so far (2001–2012 listings: median −36% over two years; 27% beat the index) say the unselected pool loses, so it will stand or fall on its indicators. The FD gives it a slot; it must not be allowed to become another twenty-round programme.

---

## 3. Review of the entire FD (v1.2 to v2.13)

I read v2.13 section by section at requirement level (sections 1–31, change logs, open items), with the version history and the repository built from it (`/home/user/asx-trader`, M0 and M1; 304 tests pass per the paused gap analysis).

### 3.1 Verdict

**The engineering in v2.13 is good and most of it carries over. The product it specifies is the wrong one, and five of its rules forbid Big Wins outright.** It is also far too long to build from: 640 KB, with requirement text rewritten through fourteen versions and six full reads, each of which found new defects. v3.0 keeps the trade-path engineering by reference, replaces the strategy, universe, data, execution and learning sections, and deletes the rest.

### 3.2 Section by section

| v2.13 section | Quality | Disposition in v3.0 |
|---|---|---|
| 1 Scope, 1.1 objective and modes | Clear, honest; wrong product (two ETFs, L1; shares excluded; AI/ML and intraday excluded) | **Replaced.** Modes kept as a ladder: `advisory` → `paper_auto` → `pilot` → `live` |
| 2 Decision log | Fine | Restarted for v3.0; v2.13's log archived |
| 3 Architecture, interfaces | Strong: pure `decide()`/`build_orders()`, same code in harness and live, Decimal money, UTC, audit record, truncation invariance (SYS-10 to SYS-18) | **Carried.** Interfaces widened from 2 sleeves to N names and several lines |
| 4 Schedule, run states (OPS-01 to 13) | Sound, monthly cadence, limit orders 11:30–15:00 | Idempotency, advisory lock, restart rules **carried**; the clock **replaced** (after-close decision, closing-auction execution, two-hourly jobs) |
| 5 Instruments, calendar (SYS-20 to 32) | Sound for ETFs | Calendar, conId, tick rules **carried**; corporate actions **extended** for shares (renames, `_old`, consolidations, takeovers, suspensions) |
| 6 Data (DAT-01 to 23) | Good checks; built for 2–5 instruments, 20 vendor calls a day, IBKR Flex as second source | Raw store, hashes, bitemporal rule, verdicts **carried**; connector, budget, QC thresholds and second source **replaced** for about 2,000 shares |
| 7 Shares, 8 External signals | Withdrawn | **Re-opened** as v3.0 §5–§8 |
| 9 Portfolio (PRT-10 to 28) | L1 only | **Replaced** |
| 10 Risk (RSK-01 to 34) | Good breaker design; limits are sleeve-based; 6 orders a day; no loss halt | Kill/pause/halts, no-short, no buy-and-sell together, price band, reconciliation halt **carried**; limits **rewritten** per name, per band, per line; loss and drawdown halts added |
| 11 Execution (EXE-01 to 14) | Careful; **forbids auctions (EXE-07) and uses 33 free snapshots a month** | Idempotent intents, crash tests, paper/live guard, whole units **carried**; order type **replaced** by limit-on-close with a continuous-session fallback |
| 12 Ledger (LED-01 to 06), two databases | Strong | **Carried**; tables added (universe, features, forecasts, lines, books, approvals, hash chain) |
| 13 Tax (TAX-01 to 18) | Thorough; the post-July-2027 rules it encodes were taken from reports and never verified against the law | Parcels, 45-day franking test, reason codes, year reports **carried**; regime B stays a switch marked **[unverified]** |
| 14 Users | Out of profile | Dropped. One owner |
| 15 Monitoring (MON) | Good | **Carried**; alert catalogue extended |
| 16 Validation, 23–25 Research, registry, harness (VAL, RND) | Right principles (pre-registration, trial log, builder/validator split, AI cannot promote). Tied to index proxies and to t ≥ 3 with DSR | Principles **carried**; bar replaced by adopt rule v2 (in force) and proposed v3; harness re-specified for share lines and the prediction ledger |
| 17 Gates, 17.1 real-money conditions, OPS-19 freeze, OPS-20 budget | Real money not before Dec 2027 and A$50,000; spec frozen; no new card before Nov 2027; cost ceiling A$150 a year | **Replaced** by v3.0 §18–§19. These four rules are why Big Wins had to run outside the spec in a scratch folder |
| 18 Config | Good pattern (YAML, hashes, pins) | Pattern **carried**; schema new |
| 19 Infrastructure (INF), 29 Bulletproofing (BP, CA) | Strong and mostly broker-agnostic | **Carried** nearly whole |
| 20 Milestones | M0, M1 built to v2.10 | New milestones B0–B8; M0/M1 reused (FD §21) |
| 21 Open items | 22 IBKR items still open, none tested | The ones Big Wins needs are carried and put first (limit-on-close cut-off, paper Flex, `orderRef`) |
| 26 Sizing engine, 27 Multi-market, 28.1 Learning layer (LRN) | Sizing and multi-market unbuilt and unneeded. The learning layer is honest but learns only costs and slippage, monthly | Sizing and multi-market **dropped**. LRN whitelist and "never automatic" rules **carried** and widened into v3.0 §15 |
| 30 Statements, 31 Parked register | Fine | Statement rewritten for Big Wins risk; parked items dropped |

### 3.3 What is wrong or missing in v2.13 for Big Wins

1. No share universe, no delisted-company handling, no rename/duplicate rules (the forward record has them as amendments v1.4–v1.6; the FD has none).
2. Data budget of 20 calls a day; the lines need the daily bulk file for about 2,000 codes and about 80–110 credits a day for new listings.
3. Execution cannot join the closing auction, which every paper line assumes.
4. Risk limits cannot express "2.5% per name, 45 names, 30 orders in a day".
5. Approval is veto-by-default. Big Wins with real money needs approve-by-default-off.
6. Nothing learns faster than monthly, and nothing scores a forecast.
7. No place for a challenger to live beside a champion, and no promotion rule that a high-swing line can meet.
8. No new-listings handling at all.
9. The cost ceiling (A$150 a year) is below the data bill (about A$370 a year) the forward record already pays.
10. It was never validated against reality: the "reality spike" of 16–20 Nov (IBKR paper login, snapshot, Flex timing, `orderRef` after restart) has not been done [gap analysis]. Six paper reads are not one real test.

---

## 4. Gap register for the Big Wins algorithm

Status: **Closed** = answered by evidence; **Open-T** = open, closable by a test on data held; **Open-F** = open, forward data only; **Open-D** = needs an owner decision or an outside fact; **Fix** = known defect to repair. EV = my ranking of expected value of closing it (1 = highest). Every open row is carried into FD v3.0 §16.4 (research backlog) with the same ID.

### 4.1 Universe

| ID | Gap | Evidence so far | Status | Test or fix | EV |
|---|---|---|---|---|---|
| U1 | The engine hunts in the top 300, where 22% of five-baggers start | T1 | **Closed today**: the pond is wrong | EMG2 line in ranks 301–600 | 1 |
| U2 | Is the score usable below rank 600? | T4 band D: no (thin, costs −12 a year) | Closed for now | Re-measure yearly in the prediction ledger | 6 |
| U3 | Exact lower liquidity floor for band C (A$100k a day used) | One value tested; median holding A$520k a day | Open-F | Ledger records fill quality by traded value; floor raised if slippage > 1.5× model | 3 |
| U4 | Renamed-company duplicates and `_old` codes in bands C–D | Fixed for the top 300 (v1.5, v1.6); not applied in my T4–T6 runs | Fix | Apply A7(c) returns test to the whole ASX list in the data layer; re-run T4/T6 as a correction | 2 |
| U5 | Listed investment companies, trusts, CDIs, dual listings counted as "shares" | Argo was in H82; Glencore CDI in the tracker | Fix | Security-class table; LICs and funds excluded from every pick list | 3 |
| U6 | Sector and industry come from today's file (look-ahead for dead companies) | Report 81 §3.3 | Fix | Store sector with fetch date from now on; history marked "as known today" | 6 |

### 4.2 Signals

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| S1 | Price signals in the top 300 | 1,760 trials | Closed. Stop | — | — |
| S2 | Which momentum form is best in band C (M3, residual momentum, 6-month only) | Only M3 tested there (T4) | Open-F | Three forecasters side by side in the prediction ledger from day one; no back-test shopping | 2 |
| S3 | Catalyst day up / down | T2, T3 | **Closed today** | Kept in the ledger as negative controls | — |
| S4 | Analyst estimate revisions | Vendor history unusable (report 79); daily snapshots since 19 Nov | Open-F | Forecaster F-REV once 6 months of snapshots exist | 5 |
| S5 | Company announcements (guidance, quarterly cash flow, contracts, placements, director buying) | Never tested: no dated history; ASX website fetch forbidden by old DAT-15 | **Open-D** | Owner decision D-6 on a lawful source; then forward-only event forecasters | 2 |
| S6 | Share issuance / dilution | No use on a size-weighted top-100 book (report 82); untested in band C where dilution is the main killer | Open-T | One pre-registered test: band C best fifth with and without names whose share count rose > 20% in 12 months (ASIC shares on issue, 2010+) | 2 |
| S7 | Change in short interest | Level failed; change untested | Open-T | One pre-registered test on ASIC files, bands B–C | 6 |
| S8 | June tax-loss rebound (H100) | Alive, weak | Open-F | Paper sleeve each June from 2027; one observation a year | 4 |
| S9 | Franked-dividend run-up, share purchase plans | Untested; small | Open-F | Logged as forecaster / panel items only | 7 |
| S10 | Fundamentals (profit, debt, cash runway) | No use in the top 300; EODHD accounts are current-version, not as first reported | Open-F | Snapshot fundamentals of band C monthly from now (point-in-time archive); test in 2028 | 5 |

### 4.3 Timing and decision frequency

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| T1g | Yearly vs monthly vs weekly in the top 300 | No difference (reports 70, 73, 76) | Closed | — | — |
| T2g | Refresh speed in band C | Monthly works (+4.9), slow hold fails (−2.5) (T5, T6) | **Closed today** for those two; weekly untested | Open-T: one test of weekly refresh with a hold band; costs will decide | 3 |
| T3g | Intraday decisions | No intraday history held; archive began 17 Nov | Open-F | Two-hourly forecasters scored in the ledger; no intraday trading until one passes §15.6 | 5 |
| T4g | Review-month luck (January swap −4.5 to +2.2 in a year) | Report 81 | Closed as diagnosis | Monthly lines have none; H82 is frozen and keeps it | — |

### 4.4 Entries

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| E1 | Breakout entry | Lottery (report 81 §6) | Closed | — | — |
| E2 | Entry after a catalyst day | T2 | Closed today | — | — |
| E3 | Buying shares that have already multiplied | Worst group in T1 | Closed as a warning; shown on the panel | — | — |
| E4 | Entry at the next close vs the next open | All tests use the next close | Open-F | Paper fills record both prices; learned in §15 | 6 |

### 4.5 Exits and sell rules

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| X1 | Trailing stops, time stops | Hurt (reports 53, 70, 81) | Closed | — | — |
| X2 | Keep winners until they become losers | Level in the top 100; fails in band C (T5) | **Closed today** | — | — |
| X3 | Sell on a bad-news day | T3 | Closed today | — | — |
| X4 | Hold band for EMG2 (sell only below the best 40% instead of the best 20%) to cut turnover and tax | Untested; report 82's buffer hurt H82 | Open-T | One pre-registered test; adopt only if after-tax result is not worse and turnover falls by a third | 2 |
| X5 | Graduates: an EMG2 holding that rises into the top 300 is sold when it leaves the band-C list, just as it becomes a mid-cap winner | By construction in T6 | Open-T | One test: keep graduates while their score is in the top half of band B | 2 |
| X6 | Takeover bids: a bid target sits at the bid price and blocks a slot | Report 81 §6.3 | Fix | Rule in EMG2: a holding whose 10-day range is under 3% after a +15% day is sold at the next decision | 5 |

### 4.6 Sizing and concentration

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| Z1 | Fewer than 30 names | Coin toss (reports 76, 80, 81) | Closed: 30 is the floor; EMG2 holds about 45 | — | — |
| Z2 | Equal vs cap weights in the top 300 | Closed (report 81) | — | — | — |
| Z3 | Adding to winners (pyramiding) | Never tested | Open-T, low | Not pursued unless X5 passes | 7 |
| Z4 | How much of the account goes to EMG2 vs an index core | Untested as a mix; EMG2 alone falls 40–60% | Open-D | Owner decision; FD default: the Big Wins account is 100% lines, the owner's index account is separate | 3 |
| Z5 | Single-name cap in a book where a holding can triple in a month | T6 had none | Fix | Cap 10% of the book; trim to 7.5% above it (design value, untested) | 4 |
| Z6 | Idle cash (0.4 a year in H82) | Report 81 | Fix for new lines: full investment; residual cash under 2% | 5 |

### 4.7 Costs and execution

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| C1 | Real spread and impact in band C | Modelled 0.5% a side with tick floor; doubling it leaves +1.2 | **Open-F, critical** | IBKR paper fills plus recorded quotes at order time; then a A$500-a-name live probe under the pilot gate | 1 |
| C2 | Does the closing auction work for A$500k-a-day shares? | Shown for the top 100 only (report 82) | Open-F | Paper: limit-on-close fill rate and price vs the last continuous trade | 1 |
| C3 | Which broker: the owner's A$0 platform lists about 550 shares, probably not band C; IBKR charges A$6.60 a trade (−1.2 a year at A$100k) | T6 stress; report 44 | **Open-D** | Owner confirms the platform's share list and order types; alternatives priced | 2 |
| C4 | IBKR facts never tested: limit-on-close cut-off, paper Flex, `orderRef` after restart | v2.13 open items I5, I10, I14, I18 | Open-D | The reality spike, first week of the build | 1 |

### 4.8 Tax

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| X-1 | EMG2 realises nearly all gains inside 12 months | T6 charges full-rate tax yearly and still leads | Closed as modelled | Tax engine reports it monthly | — |
| X-2 | Post-1 July 2027 capital-gains rules ("regime B") used in the reports | Never verified against legislation by any report | **Open-D** | Tax agent or primary source; engine keeps both regimes behind a switch | 3 |
| X-3 | Franking credits not counted on either side | Report 80 | Fix | Count in the tax engine and scorecard | 6 |
| X-4 | Loss harvesting in a fast book | Small for an investor with no other gains (report 75) | Closed | — | — |

### 4.9 New listings

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| N1 | Young companies are excluded for about a year (200 traded days of history) | Rule B1; tracker now running | By design, justified by T1 and the baseline | Kept until N2 passes | — |
| N2 | Is there an early indicator that picks the good ones? | Report 84 running (10 indicators, 8 rules pre-registered) | Open-T (in progress) | FD §8 slot: line EARLY, placeholder until report 84 | 2 |
| N3 | No offer price or IPO date from the vendor; fundamentals captured at first sight, not at listing; debt mostly missing | Tracker notes | Open-D | Accept, or allow one lawful source for prospectus facts | 6 |
| N4 | Tracker's ISIN field is broken | `registry.csv` | Fix | One-line repair; re-run the rename classification | 3 |

### 4.10 Risk

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| R1 | No stop for the whole account | v2.13 chose none; EMG2 fell 38–57% in back-test | Fix | FD §10: line-level halt on drawdown beyond the back-test worst × 1.25, and on tracking far outside its band; owner decides to resume | 3 |
| R2 | Suspensions and failures in small companies (money locked) | 9–11% of band C–D companies lose 90% in three years | Fix | Per-name cap at cost 2.5%; holdings suspended over 20 days valued at zero for sizing | 3 |
| R3 | Liquidity at exit in a crash | Not modelled | Open-F | Order ≤ 5% of 20-day median traded value; measured in paper | 4 |

### 4.11 Learning loop and validation

| ID | Gap | Evidence | Status | Test or fix | EV |
|---|---|---|---|---|---|
| L1 | Nothing is forecast and scored; the two-hourly job learns nothing | §2.2 | Fix | Prediction ledger (FD §15) | 1 |
| L2 | No automatic champion/challenger comparison | — | Fix | FD §15.5 | 1 |
| L3 | No pipeline for new ideas; ideas arrive from the owner and are tested ad hoc | — | Fix | FD §16: backlog (this register), two pre-registered cards a month, results into the ledger | 2 |
| V1 | Adopt rule v2 cannot pass a high-swing line | §0.1 item 7; arithmetic in §6.3 | **Open-D** | Adopt rule v3 proposal | 1 |
| V2 | Engines disagree by 1.5 points | Report 81 | Fix | One engine of record in the repository; every line replayed by it; twins in the same engine | 2 |
| V3 | Back-tests on spent data keep being run | All ASX history is spent | Fix | Rule: no back-test may promote; a back-test only admits a line to forward test | 2 |
| V4 | Data faults found late | §2.3 | Fix | Data layer tests (FD §6.4); nightly recompute of every registered result when data change | 1 |
| V5 | The forward record lives in a scratch folder on a disk that is 98% full | `df` today | **Fix now** | Durable storage, off-site copy, restore test | 1 |

**Closed today by test:** U1, S3, T2g (two forms), E2, E3, X2, X3. **Highest-value open items:** C1/C2/C4 (can EMG2 actually be traded at the modelled cost), V1 (adopt rule), L1/L2 (learning loop), S5/S6 (announcements; dilution), X4/X5 (turnover and graduates), U4 (duplicates in band C).

---

## 5. New listings: where they stand

- **Tracker** (`bigwins_forward/code/newlist_tracker.py`, daily, about 80–110 credits; outputs in `bigwins_forward/data/newlist/` and `paper/NEWLIST.md`). It finds genuine new listings from the vendor's symbol list, stores their price path and one fundamentals snapshot. Limits: no offer price or IPO date; the snapshot is "at first sight"; debt mostly missing; renames after May 2024 are detected by name only until the ISIN field is fixed.
- **Baseline 2014–2025** [tracker]: 1,089 listings; within 12 months 36.5% halved and 18.2% doubled; median 12-month return −17.9% against +3.2% for the ASX 200; 30% beat the index.
- **My T1 agrees:** in the small bands, companies listed under 5 years do worse than seasoned ones.
- **Meaning.** Buying new listings as a group loses. A rule has to find the 18% that double without the 36% that halve. Report 84 is testing ten indicators and eight rules for exactly that. Until it reports, the honest position is: tracked, alerted, not bought.
- **FD v3.0 §8** gives new listings a full module: data, daily alert, admission to the universe, the EARLY research line with placeholders tied to report 84's outputs, lottery caps, wide spreads.

---

## 6. Direction, decisions and registrations

### 6.1 The line-up I recommend

| Role | Line | Status |
|---|---|---|
| Baseline (registered champion, by seniority not merit) | H82 v1.3 + amendments, A$100k | Unchanged. Reported as "large-company control" |
| Shadows, top 100 | M3 v1.1, E3, ACC, CXL v1.1 with twin and random books | Unchanged; no further research |
| **Lead challenger** | **EMG2 v1.0** (FD §7.6) with 100 twins, A$100k and A$25k | To register before 30 Nov |
| Measurement | Band-spread line (best fifth minus band, bands B and C, monthly); avoid-list line (registered, pending) | To register with EMG2 |
| Research slot | EARLY (new listings), from report 84 | Placeholder |
| Seasonal | H100 June rebound, paper sleeve | June 2027 |
| Multi-market record | M3 / EI10I / CW in 14 markets | Keep running as is; do not port into the system; no more research |

### 6.2 Why this and not something safer

The safer answer (hold the index, track Big Wins as a hobby record) is what reports 80–82 said, and for the top 300 it stands. The owner has ruled it out as the product. Inside the owner's brief, EMG2 is the only candidate where (a) big winners are actually in the book, (b) the measured effect is several times the cost and the machinery noise, (c) a small account has a real advantage (funds cannot trade A$500,000-a-day shares in size), and (d) the evidence can grow at a useful speed through the band spread. Its weaknesses are stated in §1.4 and are the reason the money stays small until the forward record speaks.

### 6.3 Proposed adopt rule v3 (owner decision; not registered by me)

Why v2 cannot work here: t = lead ÷ tracking error × √years. With a tracking error of 20 and a true lead of 5, t = 3 needs 144 years and t = 2 needs 64. For CXL (tracking error 5, lead 0.3) it also needs centuries. V2 can only ever pass a large edge in a quiet book, and the evidence says no such thing exists.

V3 keeps v2 for index-like lines and adds a ladder for lines with tracking error above 10 points a year:

| Step | Evidence required | Money allowed |
|---|---|---|
| P0 Paper | Registered, hashed, running with twins | None |
| **P1 Pilot** | 12 months on the IBKR paper account with: every decision executed and reconciled; realised cost per trade ≤ 1.5 × the model; book ≥ 60th percentile of its twins; band spread positive; no halt outstanding. Owner signs the risk statement | One slice, the lower of **A$10,000** and 5% of the owner's investable assets, 20 names |
| **P2 Scale** | 24 months from registration: forward band spread t ≥ 2.0; book ≥ 80th percentile of twins; after-tax result not behind the A200 fund by more than 5 points a year; pilot costs within 1.5 × model | Up to A$50,000, 45 names |
| P3 Full | 48 months: forward band spread t ≥ 3.0; book ≥ 90th percentile of twins; after-tax lead over the A200 fund (kept basis) positive; owner sign-off | Owner's choice, with the line-level halts of FD §10 |
| Stop | At any December review after 13 months: band spread t ≤ −1.0, or book below the 20th percentile of twins, or after-tax result more than 15 points a year behind the fund over 24 months or more | Line closed, not re-tuned |

It gives up statistical proof that the book beats the index (unobtainable) in exchange for proof that the signal still sorts shares, that the book beats chance in its own pond, and that it can be traded at the modelled cost. The honest risk: a signal can keep sorting shares inside a band that as a whole keeps losing to the index. P2 and P3 carry an index condition for that reason.

### 6.4 Decisions needed from the owner

| # | Decision | My recommendation | Default if no answer |
|---|---|---|---|
| D-1 | Lift the v2.13 freeze (OPS-19) and the "no new card before Nov 2027" rule; adopt FD v3.0 as the build document | Yes | Build proceeds on paper only |
| D-2 | EMG2 as lead challenger; H82 demoted to control in reports | Yes | Registered as one more shadow |
| D-3 | Adopt rule v3 for high-swing lines | Yes, with the caps in §6.3 | v2 stays; no real money path |
| D-4 | Pilot cap in dollars | A$10,000 | A$0 |
| D-5 | Broker for band-C shares: confirm the A$0 platform's list; otherwise IBKR | IBKR first, as instructed | IBKR paper |
| D-6 | A lawful source of ASX announcements (headline, time, price-sensitive flag) | Yes if a licensed feed costs under about A$50 a month; otherwise defer | None; announcement signals stay closed |
| D-7 | Data and running budget: about A$370 a year now; about A$700–900 a year with a small server and the fundamentals month twice a year | Yes | Current plan only |

### 6.5 To register (by the record keeper, in this order)

1. Ledger note: report 85, trials 85-T1 to T6 (+6), hashes of the four pre-registration files, verdicts (T1 descriptive; T2 fail; T3 not supported; T4 fail on t; T5 fail; T6 fail on t).
2. `AMENDMENT_shadow_EMG2.md` = FD v3.0 §7.6 verbatim, plus books, twins and the band-spread measurement; before the 30 Nov decision.
3. `AMENDMENT_adopt_rule_v3.md` only after the owner's decision D-3.
4. Correction notes: tracker ISIN field; A7(c) duplicate test to be applied to the full ASX list before EMG2's first decision.
5. When report 84 lands: its draft `AMENDMENT_shadow_EARLY` reviewed against FD §8.5 caps before registration.

---

## 7. Limits of this review

- I read v2.13 at requirement level in every section, the change logs in outline, and earlier FD versions through those logs; I did not re-read each earlier version in full.
- Reports 80–82 are my own and I relied on them. Reports 53–79 I read in summary and in part; 07–52 through the briefing and the FD's dispositions.
- T1–T6 use one vendor file. No duplicate removal, no name-by-name audit of small-company prices, approximate tax, a monthly clock. T5 and T6 returns are after tax paid each June and before tax on the holdings at the end (shown separately in the logs).
- The EMG2 periods are not unseen. Nothing in ASX history is. Only the forward record can confirm it.
- Reports 83 and 84 were unfinished when this was written; their results may change §2.4 items 5–6 and §5.
- Broker facts (A$0 share list, limit-on-close for small shares, IBKR cut-offs) are unverified and are the first thing to establish.
- Odds and forward estimates are judgement.

## 8. Files

| What | Path |
|---|---|
| Pre-registrations and hashes | `scratchpad/deep85/PREREG_85.md`, `PREREG_85b.md`, `PREREG_85c.md`, `PREREG_85d.md`, `out/prereg85_hash.txt` |
| Data build | `deep85/code/build85.py` → `data/W.pkl` |
| T1 | `code/t1.py`, `out/t1.txt` |
| T2, T3 | `code/t23.py`, `out/t23.log`, `t2.csv`, `t3.csv` |
| T4 and stresses | `code/t4.py`, `out/t4.txt`; `code/t4s.py`, `out/t4s.txt` |
| T5, T6 | `code/t5.py`, `out/t5.log`, `t5.json`; `code/t6.py`, `out/t6.log`, `t6.json` |
| New FD | `onedrive/research2/FD_v3.0_BigWins.md` |
