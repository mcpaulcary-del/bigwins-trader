# 83. Round 11: the traded-value fault — forward engine checked, overseas sets rebuilt, verdicts re-run; and one last structural test

19 November 2026. Author: research agent (Fable). Scope: Big Wins only. Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades.
Work folder: `scratchpad/deep83/` (`PROGRESS.md`, `PREREG_83.md`, `code/`, `out/`, `amend/`, `data/`). The live paper record, ledger, frozen code and scheduled tasks were not touched. EODHD: about 14,000 requests for the re-download (six exchanges, 1999–2026), paced under 280 a minute; the day's counter stood at 32,501 of 100,000 at the end (it includes any other job), so the 15,000 reserve was kept. Trial count: 1,759 → **1,761** (`out/trials_83.csv`); every re-run below is a re-run of an existing trial and adds nothing.

How to read the figures: "lead" = points a year over the local index fund, after costs and 32% tax with the 12-month discount, A$25,000 / A$100,000. t = the mean divided by its standard error; 3 is the adopt bar.

## 0. Answer first

**1. The forward engine does carry the fault in four markets, it is not active today, and a fix is drafted for registration before 30 November.**
- Germany, France, Sweden and Canada rank "most traded" with the round-3 rule, which divides every day's traded value by every later split ratio without checking whether the vendor restated the volume. In 19% of recent splits it had not. The other ten markets check each split step, but that check has a fault of its own (it breaks when the vendor's raw price flips units for a few days). I found the second fault while testing my first draft of the fix.
- On the stores as of 17 November the corrected rule gives **the same buy lists in all 14 markets**: the same 100 names everywhere except France (99 of 100: Eramet moves from rank 106 to 93), and the same M3, EI10I and CW lists. The worst overstatements today sit at ranks 190–420 (a Swedish share overstated 19 times, a Canadian one 43 times). One 1-for-100 consolidation in a mid-ranked share would put a penny stock in the list.
- Draft amendment, exact diff, patched file, unit tests and the before/after lists are in `deep83/amend/`. **It should be registered before the first decision.** Nothing booked so far depends on it.

**2. The overseas sets were rebuilt from fresh downloads and every dependent verdict was re-run. No verdict changes.**
- **M3**: in the 18-set pool it is ahead in 12 of 18 in 2023–26 before and after. In the four forward markets that had the faulty rule its whole-window lead is −0.6 / −0.4 as tested and **−0.2 / −0.5 corrected** (Germany +1.9 / +1.4, France −0.4 / −0.9, Sweden −2.5 / −2.0, Canada +0.3 / −0.4). M3 did not lead on these markets on either file. Not shown to beat the index, as before.
- **M3 against random books** weakens a little: at A$100,000 it is at or above the 90th percentile in 5 of the 8 rebuilt sets as tested and 3 of 8 corrected.
- **EI10I** and **CW**: unchanged within 0.6 point outside the US. The round-6 look still has EI10I at +1 or better at both sizes in 3 of 12 sets.
- **Report 79** (earnings surprise): +1 at both sizes in 4 of 12 before and after. **Report 81** D1–D3: pooled +0.9 / +0.5, +0.3 / +0.25, −0.5 / −0.2 (were +1.0 / +0.55, +0.2 / +0.3, −0.3 / −0.2). **Report 70** used ASX data only and is not affected.
- **One finding of mine weakens.** Report 82's loser screen on blunt size weights was +1.75 to +1.9 a year (t 2.9–3.2) outside the US. On corrected files it is **+1.5 to +1.7 (t 2.5–2.8)**; the UK figure fell from +5.5 to +1.7 because junk lines had flattered it. The cap-weighted figure, the one that matters for a real book, is unchanged at +0.8 to +1.0 (t about 2).
- **The US set is worse than report 82 said, and the correction does not fully repair it.** As tested, the "100 most traded US shares" held 10–11 shares under US$5 in a typical month before 2018; the corrected list holds about 2 and shares only 75–78% of its names with the old one before 2018 (94% after). A second fault remains: the vendor files 80-odd dead lines under US exchanges whose prices are in pence, pesos, roubles or dong (HSBA at 570, ISA at 7,350), and 7–16 of them sit in the "US 100" each month. With those removed as well the US verdicts still do not change. **US back-test rows should be read as indicative only.** The forward engine has no US market.

**3. One genuinely untested route was pre-registered and tested: the loser screen applied to mid and small companies (ranks 101–300), held as a sleeve beside the index. It failed.**
- The screen does work better there: **+2.6 a year (t 3.9), ahead in 17 of 17 markets**, 2013–2026.
- But the band itself trailed the 100 largest by 1.9 a year (4.9 a year in 2020–26). Screened band minus the 100 largest: **+0.7 (t 0.6)**; +3.2 in 2013–19, −2.3 in 2020–26; on ASX −1.1 (−1.6 on cap weights). The bar set in advance was +2.0 with t ≥ 2, positive in both halves and on ASX. No engine test was run and no forward line is proposed.

**4. My judgement: further mining of this history has no realistic chance of producing something that meets the bar.** Eleven rounds, 1,761 trials, 20-odd markets, two engines, corrected data: every route ends within about half a point of the index, and the route that looked best (drop the losers) is worth under one point on real index weights before tax. The adopt rule is forward-only in any case, so no back-test can adopt anything. What could change the answer is in section 5. **The index fund remains the thing to hold.**

**What to do.** (i) Register the traded-value amendment before 30 November. (ii) Use the corrected packs (`deep83/data/pack_*_new_M.npz`) for any future overseas back-test and drop the old ones from citation. (iii) Strike US rows from pooled figures unless the US set is rebuilt from a list filtered by ISIN. (iv) Change nothing in H82, M3, EI10I, CW or CXL. (v) Stop design rounds on price and volume data; let the forward record run.

---

## 1. Item 1(a): does the 14-market forward engine use the faulty definition?

### 1.1 What the code does (`bigwins_forward/code/multi_build.py`, read-only)
Traded value of a day = raw close × vendor volume ÷ F. F is the product of later split ratios, found as steps of more than 12% in raw close ÷ adjusted close. The assumption is that the vendor has restated all earlier volume into new-share units.

| Builder rules | Markets | What happens at a split step |
|---|---|---|
| r3 (round 3) | **DE, FR, SE, CA** | Every step is applied. No check. This is the faulty definition |
| r4, r5 (rounds 4–5) | ASX, SW, KO, TW, BK, SA, CN, HE, WAR, BR | Each step is checked on its own: is traded value more continuous with or without the correction? Steps with fewer than 5 traded rows either side are applied unchecked |

### 1.2 What the vendor does (forward stores, rows since 1 Sep 2024; `code/fwdcheck.py`, `out/fwd_events.csv`)
| | Steps beyond 2:1 that can be read | Volume restated | Volume left as traded |
|---|---|---|---|
| DE, FR, SE, CA | 84 | 67 | **17 (20%)** |
| The other ten | 109 | 90 | 19 (17%) |
| ASX alone | 18 | 17 | 1 (AUZ, rank 427) |

Another 279 readable steps lie between 12% and 2:1. Many are large dividends and rights issues, for which volume is never restated, yet the r3 rule divides by every one.

### 1.3 A second fault, found while testing the fix
My first draft simply switched the r4/r5 check on for the four r3 markets. On the rebuilt Swedish history it put WYLD, a share trading under SEK 1m a day, in the "100 most traded" for 45 months. WYLD's raw close ÷ adjusted close has 45 steps since 2024, most of them the raw close flipping between old and new units. Each flip is a step; the per-step check keeps some and drops others, and the errors multiply to about 1,500 times. The registered r4/r5 guard has exactly this behaviour. It has not misfired on the ten stores so far.

The rule I propose instead reads each split **event** once: steps within 20 rows of each other are one event with one net ratio; a net ratio within 12% of 1 is a glitch and is ignored; otherwise one continuity test decides whether the volume was restated; an event that cannot be read never raises a company's traded value. Seven synthetic unit tests pass (`amend/test_split_factor_v2.py`).

### 1.4 Before and after on the live stores (data to 17 Nov 2026; `code/fwd_test_v2.py`)
| Market | Rules | 100 most traded: same names | M3 buy list (15) | EI10I (30) | CW (30) | Names whose traded value moves > 5% | Best old rank among them |
|---|---|---|---|---|---|---|---|
| DE | r3 | 100 | same | same | same | 2 | 324 |
| FR | r3 | 99 | same | same | same | 8 | 74 |
| SE | r3 | 100 | same | same | same | 6 | 190 |
| CA | r3 | 100 | same | same | same | 1 | 280 |
| SA | r4 | 100 | same | same | same | 3 | 240 |
| ASX, SW, KO, TW, BK, CN, HE, WAR, BR | r4/r5 | 100 | same | same where run | same where run | 0 | — |

France: Eramet (a 1.44 step on 16 Nov 2026, volume as traded) moves from rank 106 to 93 and enters the 100. Overstated today: FRNT-B (Stockholm) 19 times, rank 190 → 406; AVL (Toronto) 43 times, 280 → 410; ALSRS (Paris) 8 times, 217 → 373. None is near a buy list.

**Answer to 1(a): yes, the faulty definition is in the code for DE, FR, SE and CA at 30 November and after. It changes no list today. It should be fixed before the first decision because one event can change that.** Draft: `deep83/amend/AMENDMENT_multi_traded_value_v2.DRAFT.md`, with `multi_build_v2.diff`, `multi_build_v2_proposed.py`, `test_lists_before_after.csv`, `test_traded_value_changes.csv`.

### 1.5 Two related observations (no action proposed in the amendment)
- **ASX H82** (`bw13_prep.py`, v1.4) assumes every split was restated. On the ASX store 17 of 18 were, and the exception is far from the list. A guard of the same kind is worth adding at the next H82 amendment.
- **The German "100 most traded" includes 9 US companies' Frankfurt lines** (Nvidia, AMD, Amazon, Apple, Meta, Microsoft and others) and 8 other foreign lines. The tested design kept every common-stock line, so the back-test had them too (Nvidia is M3's third-largest German winner). The DAX fund does not hold them. This is the tested design and I leave it, but a German M3 result is partly a bet on US shares.

## 2. Item 1(b): rebuilt overseas sets and re-run verdicts

### 2.1 What was rebuilt
- Fresh EODHD downloads, 1 June 1999 to 17 Nov 2026: every common-stock line, live and delisted, on Xetra, Paris, Stockholm, Toronto and London (about 9,900 series), and the 4,041 lines of the old US pack. The round-3 raw files no longer existed.
- Each set was built twice with the round-3 builder itself (`code/mk83.py` runs `improve/code/mk_fresh.py` with only the paths and the traded-value rule changed): once with the rule as tested ("fresh, as tested") and once with the corrected rule. The first isolates what the vendor has revised since October; the second isolates the correction.
- The round-4 and round-5 sets (Korea, Taiwan, Switzerland, Brazil, Thailand, China and the rest) already used the per-step check and were not rebuilt. They are exposed to the flip-flop fault of 1.3; I did not find a case in their forward stores.

### 2.2 How much the lists change (`out/cmp83_*.json`)
Names in common, of 100, per month:

| Set | Published file vs fresh download, same rule, 2018–26 | Tested rule vs corrected: 2001–12 | 2013–17 | 2018–26 | Shares under one currency unit in the 100 (US: under $5), 2013–17: tested → corrected |
|---|---|---|---|---|---|
| Germany | 100.0 | 97.4 | 98.4 | 99.2 | 0.0 → 0.0 |
| France | 94.1 (the old download missed six large companies) | 97.7 | 98.0 | 98.4 | 0.8 → 1.3 |
| Sweden | 98.7 | 96.1 | 96.9 | 98.3 | 0.2 → 0.2 |
| Canada | 99.9 | 89.5 | 91.5 | 97.7 | 1.5 → 0.2 |
| UK | 98.8 | 89.8 | 90.3 | 97.2 | 3.4 → 0.0 (under 50p) |
| US large (ranks 1–100) | 98.5 | **77.8** | **75.0** | 93.6 | **11.1 → 1.6** |
| US mid (301–400) | 98.7 | 66.0 | 59.5 | 85.0 | |
| US small (601–700) | 97.7 | 65.0 | 51.4 | 79.6 | |

US large, June 2015, top of the list as tested: DRYS (60 cents), PSTV (56 cents), PACD, then Weatherford. Corrected: the penny shares are gone and FedEx, GE, Honeywell, PepsiCo, Morgan Stanley, Lowe's and Costco come back in.

### 2.3 The US set has a second fault that the correction cannot fix
The vendor's US delisted list holds lines filed as US-dollar NYSE or NASDAQ shares whose prices are plainly another market's: HSBA at 570 (pence), SBER at 72–238 (roubles), ISA at 7,350 and CELSIA at 4,235 (Colombian pesos), CMPC at 1,739 (Chilean pesos), several at 3,500–42,000. Their "traded value" is in those units. A mechanical flag (delisted line that out-trades the busiest live share, or with a median price above 1,000; `code/usx.py`) marks 80 lines; 14–16 of them sat in the "US 100" each month before 2018 and 7 since. I built a sensitivity pack without them (`pack_US_newx_M.npz`). The flag is crude and will miss some.

### 2.4 Results
"Published" = the file used in reports 73–82. Differences between "published" and "fresh, as tested" are vendor revisions and path noise; they reach 1.5 points at A$25,000 (US large 2023–26: +3.5 → +5.2). Treat any correction effect below that as noise.

**M3, whole window (2018 or the set's first year to Oct 2026), A$25k / A$100k**

| Market | Published | Fresh, as tested | **Corrected** | US: corrected, bad lines out |
|---|---|---|---|---|
| Germany | +2.1 / +1.3 | +2.1 / +1.4 | **+1.9 / +1.4** | |
| France | −1.0 / −0.6 | −0.3 / −0.9 | **−0.4 / −0.9** | |
| Sweden | −2.5 / −1.7 | −3.5 / −2.0 | **−2.5 / −2.0** | |
| Canada | −0.8 / −0.0 | −0.8 / +0.1 | **+0.3 / −0.4** | |
| UK | +1.4 / +0.0 | +2.0 / +0.2 | **+1.2 / +0.1** | |
| US large | +1.0 / −0.5 | +0.7 / −0.3 | **+1.3 / −0.1** | +0.6 / −0.7 |
| US mid | +1.1 / +0.0 | +1.9 / +0.5 | **+1.0 / +0.6** | +1.7 / +0.7 |
| US small | +0.4 / −0.6 | +0.3 / −0.2 | **+3.4 / +0.5** | +4.0 / +0.9 |
| Mean of the 8 | +0.2 / −0.3 | +0.3 / −0.2 | **+0.8 / −0.1** | |
| Four forward markets (DE, FR, SE, CA) | −0.6 / −0.3 | −0.6 / −0.4 | **−0.2 / −0.5** | |

**M3 in the round-5 pool of 18 sets** (`code/m3pool.py`; the ten other sets on their own files)

| Window | Published: mean; sets ahead | Fresh, as tested | **Corrected** |
|---|---|---|---|
| To Dec 2022 | +1.3 / +0.8; 12 of 18 | +1.3 / +0.8; 11 | **+1.5 / +0.9; 13** |
| 2023–26 (the in-pool check) | +1.6 / +1.2; 12 of 18 | +1.6 / +1.2; 12 | **+1.7 / +1.1; 12** |
| Whole | +0.6 / +0.4; 11 of 18 | +0.7 / +0.4; 12 | **+0.9 / +0.4; 12** |

M3's percentile among 100 random books moves in both directions (Germany 97 / 100 → 97 / 88; Sweden 45 / 66 → 86 / 49; US small 92 / 92 → 99 / 97). At A$100,000 it is at or above the 90th percentile in 5 of the 8 sets on the published files, 5 of 8 on the fresh download with the tested rule, and **3 of 8 corrected** (France, UK, US small). One start date each, so this is noisy, but the direction is against M3.

**EI10I and CW, whole window**

| Market | EI10I published | EI10I fresh, as tested | **EI10I corrected** | CW published | **CW corrected** |
|---|---|---|---|---|---|
| Germany | −0.3 / −0.9 | −0.4 / −1.1 | **−0.4 / −1.0** | −0.7 / −1.3 | **−0.7 / −1.2** |
| France | +1.4 / +0.8 | +1.6 / +0.6 | **+2.2 / +0.9** | +1.8 / +0.6 | **+1.9 / +0.6** |
| Sweden | +2.4 / +0.7 | +2.2 / +1.3 | **+1.9 / +1.1** | +2.0 / +0.6 | **+1.8 / +0.6** |
| Canada | −0.9 / −0.8 | −0.8 / −0.6 | **−1.4 / −0.6** | −1.2 / −0.8 | **−1.1 / −0.8** |
| UK | +1.1 / +2.0 | +1.8 / +2.2 | **+1.2 / +1.8** | −1.3 / −1.2 | **−1.2 / −1.3** |
| US large, 2020–26 (the round-6 look) | +2.4 / +1.9 | +2.2 / +1.4 | **+2.2 / +1.7** | +1.9 / +1.7 | **+2.0 / +1.3** |
| US mid, 2020–26 | +0.4 / +0.1 | +1.2 / +1.1 | **+0.9 / +0.1** | −4.8 / −2.9 | **−0.5 / −2.5** |
| US small, 2020–26 | −0.2 / −1.0 | −0.3 / −1.9 | **−0.5 / −1.9** | −3.3 / −3.8 | **−4.1 / −4.2** |

- Round-6 look (report 77): EI10I at +1 or better at both sizes in 3 of 12 sets (US large, Brazil, Denmark) before and after; 7 were needed. US large stays under the 90th percentile of random-tilt books (68 / 80 → 65 / 56).
- CW outside the US is identical to one decimal: it holds the largest companies by market cap, which were always in the 100. CW in the US mid and small bands moves by several points (US small, whole window: +1.0 / +1.9 → −4.6 / −2.9) because half the names in those bands change. CW is a control and was never adoptable.

**Report 79** (earnings surprise with M3; 12 markets, 2019–2026): the chosen design's six affected rows move by at most 1.4 points; the pooled mean is +0.6 / +0.6 → **+0.6 / +0.7**; +1 at both sizes in 4 of 12 before and after (7 needed). Failed then, fails now.

**Report 81** (my designs; six affected sets of 20):

| Design | Published: mean; +1 at both sizes; any cell under −2 | **Corrected** |
|---|---|---|
| D1 keep-winners | +1.02 / +0.55; 8 of 20; 5 | **+0.89 / +0.54; 8 of 20; 5** |
| D2 cap-weighted ex-losers (the CXL shadow line) | +0.22 / +0.33; 5 of 17; 3 | **+0.33 / +0.25; 5 of 17; 3** |
| D3 mid-cap satellite | −0.33 / −0.24; 4 of 20; 4 | **−0.48 / −0.21; 4 of 20; 6** |

D2 in US large falls from +3.1 / +2.2 to +2.8 / +1.6 and in Sweden from +2.5 / +2.6 to +2.5 / +1.7. None passed; none passes.

**Report 70** (all-information engine): ASX data only. Not affected.

Full tables, all windows: appendix A (`out/tables83.md`).

## 3. Report 82's loser screen on corrected data
Gain from removing the weakest 30% of the 100 most traded, against the list's own return, Jan 2013 – Oct 2026 (`code/rr82.py`):

| Screen and weights | Published files | Fresh, as tested | **Corrected** | Corrected, no US |
|---|---|---|---|---|
| M3 score, blunt size weights (21 sets) | +2.83 (t 4.4) | +2.60 (4.0) | **+1.83 (2.9)** | +1.70 (2.8) |
| M3 score, market-cap weights (18 sets) | +0.90 (2.1) | +0.86 (2.0) | **+0.96 (2.1)** | +0.88 (1.9) |
| Report 82's new score, blunt weights | +2.77 (4.4) | +2.56 (4.0) | **+1.66 (2.7)** | +1.46 (2.5) |
| Report 82's new score, cap weights | +0.66 (1.7) | +0.63 (1.6) | **+0.76 (1.8)** | +0.66 (1.6) |

By set on blunt weights (M3 score): US large +20.6 → +4.6; UK +5.5 → +1.7; Canada +2.2 → +1.8; Germany, France and Sweden within 0.7.

**Corrections to report 82.** (a) Point 1's "+1.75 to +1.9, t 2.9 to 3.2" becomes "+1.5 to +1.7, t 2.5 to 2.8". The screen is still ahead in 20–21 of 21 markets. (b) Report 82's new score would not have met its own t ≥ 3 confirmation test on blunt weights either; it was already "not confirmed". (c) Point 2, the cap-weighted ceiling of +0.7 to +0.9, stands (+0.8 to +1.0). (d) The measurement-line spec in report 82 section 9 assumed +1.9; at +1.6 it needs about 8 years for t = 2 instead of 6.

## 4. Priority 2: is there an untested, structurally different route?

### 4.1 The one candidate
Report 82 ended on: the screen is worth little on index weights because the index holds 81–86% of its money in names the screen never flags; it works better in smaller companies; moving money there is a size bet. The owner's suggestion, a mostly-index portfolio with a screened mid/small sleeve, is that bet made on purpose. It had not been measured. One number decides it: **per dollar moved from the 100 largest into the screened band, how much more does it earn before costs?**

### 4.2 Pre-registration (`PREREG_83.md`, SHA-256 db8c400c…eb26, hashed with the code before the run)
- Band: traded-value ranks 101–300. Avoid list: the weakest 30% of the band by the M3 score. No choice of score or depth. Monthly, no costs, blunt size weights; ASX also on ASIC cap weights. 17 of 21 sets have 100 names in the band. Primary window Jan 2013 – Oct 2026.
- T1: screened band minus band. T2: screened band minus the 100 most traded.
- Go to an engine test only if T1 ≥ +3.0 with t ≥ 3 and ahead in most sets, **and** T2 ≥ +2.0 with t ≥ 2, positive in both halves and on ASX. Why +2.0: about 0.5 of spread and 0.5 of tax drag must come off before the +1.0 adopt bar.

### 4.3 Result (`out/band83.json`, `out/band83.log`)

| | 2013–2026, 17 sets | 2013–19 | 2020–26 | 2001–2026 | ASX, blunt weights, 2013–26 | ASX, cap weights, 2018–26 |
|---|---|---|---|---|---|---|
| T1: screen gain inside the band | **+2.60 (t 3.9)**, ahead in 17 of 17 | +2.7 (3.1) | +2.6 (2.4) | +2.1 (3.0) | +2.6 | +0.9 (t 1.0) |
| Unscreened band minus the 100 largest (the size leg) | −1.94 (t −1.9), ahead in 4 of 17 | +0.5 | −4.9 (t −3.0) | −0.2 | −3.7 | −2.5 |
| T2: screened band minus the 100 largest | **+0.67 (t 0.6)**, ahead in 9 of 17 | +3.2 (2.2) | −2.3 (−1.4) | +1.9 (1.7) | **−1.1** | **−1.6** |

- T1 fails its size condition (+2.6 against +3.0) and passes the others. The screen is plainly stronger in smaller companies than in the 100 (+1.8).
- T2 fails all four conditions. The size leg takes back what the screen earns, and since 2020 much more.
- On ASX with true cap weights (2018–26) the screen gain inside the band is +0.9 and the screened band trailed the 100 largest by 1.6 a year. A 30% sleeve would have cost the whole portfolio about half a point a year before spread and tax.
- **Verdict: fail. No engine test, no forward line.** The screen is a way to hold smaller companies less badly. It is not a reason to hold them.

### 4.4 Other routes considered and why they were not run
- **Tax-loss harvesting / direct indexing**: tested in reports 75 and 76 (+0.0 to +0.5, timing only; no outside gains to absorb the losses). Not structurally new.
- **Mid/small satellite with picks** (D3, report 81): −0.5 / −0.2. The sleeve test above is its exclusion-only cousin and fails for the same reason.
- **Fundamentals, earnings surprise, short interest, issuance, loss-makers**: reports 57, 62, 70, 76, 77, 79, 82. Nothing added on size weights.
- **Share purchase plans** (report 59): the one edge that favours a small account over an index fund, because a A$30,000 application is the same size for everyone. It could not be tested: 1,228 events found, issue prices in only 4 headlines, and no automated ASX access. It needs data this project does not have.

### 4.5 Judgement
**Further history mining on price, volume and the fundamentals on this data plan has no realistic chance of producing a design that meets the bar.** Reasons:
1. *Arithmetic.* A long-only taxed book of 30 names starts about 2 points behind a cap-weighted fund (report 76); the best signal earns 2–3; the best exclusion earns under 1 on index weights. Every design lands within about half a point of zero, and corrected data moved nothing.
2. *Count.* 1,761 trials. Anything that now "passes" in history has to beat a selection effect of that size. The adopt rule (v2) rightly ignores back-tests: it reads only forward months.
3. *Power.* A true edge of +0.5 cannot be shown in any record of practical length; +2 takes 7 years pooled across 14 markets (report 78). Designs that might carry +2 do not exist in this evidence.
4. *This round.* The last structural idea with a mechanism behind it, tested with high power on 17 markets, failed on the size leg.

My estimate of the true after-tax edge of the best Big Wins construction at A$100,000 stays at **−0.3 to +0.6, most likely +0.2**, with the top of the range slightly less likely than a round ago.

## 5. What would change the answer
1. **Time on the forward record.** The 14-market record starts 30 Nov 2026. First formal reading Dec 2029. It is the only source of clean evidence left.
2. **Information that is not in prices and that a small account can use.** Share purchase plan terms, placement discounts, entitlement offers. This needs a hand-kept or purchased corporate-actions file; then one pre-registered test.
3. **Lower frictions, which are certain rather than estimated.** Fund fee, A$0 brokerage, never realising a gain before 12 months, using new contributions to rebalance. These are worth a few tenths of a point each and do not need a forecast.
4. **Not more markets, more signals or more engines on the same vendor files.** That road has been walked.

## 6. Faults found this round

| Fault | Where | Effect | Action |
|---|---|---|---|
| Round-3 rule applies every split step to traded value without reading the volume | `multi_build.py` (DE, FR, SE, CA); `improve/code/mk_fresh.py` and the six round-3 packs | Forward: no list changes today. History: US lists 22–25% wrong before 2018, UK and Canada 10% | Amendment drafted; corrected packs built |
| Per-step volume check multiplies errors when the vendor's raw close flips units | `multi_build.py` r4/r5 guard; the round-4/5 pack builders | WYLD overstated 1,500 times in the Swedish history under that check. No case in the ten forward stores today | Same amendment (one reading per event) |
| US set: 80-odd dead lines priced in other currencies under US exchange codes | Vendor US delisted list; `improve/data/pack_US_M.npz` | 7–16 of the "US 100" each month | US rows indicative only; rebuild from an ISIN-filtered list before any further use |
| Old Paris download missed six large companies | `improve/data/pack_PA_M.npz` | 94–96 of 100 names right | Use `pack_PA_new_M.npz` |
| Background jobs started with `nohup … &` freeze when the shell call returns | This environment | A stalled download, restarted | Use the tool's own background mode |

## 7. Files
| File | What |
|---|---|
| `deep83/amend/AMENDMENT_multi_traded_value_v2.DRAFT.md` | Draft amendment (not registered) |
| `deep83/amend/multi_build_v2.diff`, `multi_build_v2_proposed.py`, `test_split_factor_v2.py` | Exact patch, patched file, unit tests |
| `deep83/amend/test_lists_before_after.csv`, `test_traded_value_changes.csv` | Forward lists before and after, 14 markets, data to 17 Nov 2026 |
| `deep83/code/fwdcheck.py`, `fwd_test_v2.py` | Split-step audit of the stores; the list test |
| `deep83/code/dl83.py`, `dl83b.py`, `mk83.py`, `cmp83.py`, `usx.py` | Re-download, rebuild, list comparison, US sensitivity |
| `deep83/code/rerun83.py`, `m3pool.py`, `rr79.py`, `rr81.py`, `rr82.py`, `summ83.py` | Re-runs of reports 76/77, 79, 81, 82; tables |
| `deep83/data/pack_{XETRA,PA,ST,TO,LSE,US}_new_M.npz`, `pack_US_newx_M.npz` | Corrected packs (kept). Raw downloads and the "as tested" rebuilds were deleted for disk space (`DELETED_CACHES.log`) |
| `deep83/PREREG_83.md`, `out/prereg83_hash.txt`, `code/band83.py`, `out/band83.json` | The sleeve test |
| `deep83/out/tables83.md`, `out/rr_*.json`, `rr79_*.json`, `rr81_*.json`, `rr82_*.json`, `m3pool_*.json`, `cmp83_*.json`, `trials_83.csv` | Results |

Limits. (1) The US rebuild used the 4,041 lines of the old pack, not the whole exchange, so a US share wrongly ranked below 1,100 by the old rule in every year could be missing; the five other exchanges were downloaded whole. (2) Random-book percentiles were re-run for M3 and EI10I only; reports 79 and 81 were re-run without their random books. (3) The round-4/5 sets were not rebuilt. (4) The test of 1.4 uses data to 17 Nov; the 30 Nov lists will add nine sessions.

---

## Appendix A. Full re-run tables

### A. M3: after-tax lead over the local fund, points a year, A$25k / A$100k

| Market | Window | As published (old file) | Fresh download, rule as tested | **Corrected** | US: corrected + bad lines out | Change from correction (25k / 100k) |
|---|---|---|---|---|---|---|
| Germany | to Dec 2022 | -0.4 / +0.4 | -0.4 / +0.4 | **-1.3 / -0.2** |  | -0.9 / -0.6 |
| Germany | 2023-26 | +4.2 / +2.9 | +4.2 / +2.9 | **+5.5 / +3.2** |  | +1.3 / +0.2 |
| Germany | whole | +2.1 / +1.3 | +2.1 / +1.4 | **+1.9 / +1.4** |  | -0.2 / +0.0 |
| France | to Dec 2022 | -0.2 / -0.4 | +1.0 / -1.0 | **+0.7 / -1.2** |  | -0.3 / -0.1 |
| France | 2023-26 | -1.8 / -0.5 | -0.0 / -0.7 | **-0.3 / -0.4** |  | -0.2 / +0.3 |
| France | whole | -1.0 / -0.6 | -0.3 / -0.9 | **-0.4 / -0.9** |  | -0.1 / -0.0 |
| Sweden | to Dec 2022 | +2.2 / +0.7 | -0.2 / +0.1 | **+0.5 / +0.4** |  | +0.7 / +0.4 |
| Sweden | 2023-26 | -5.5 / -3.1 | -6.6 / -3.0 | **-6.6 / -3.2** |  | +0.0 / -0.2 |
| Sweden | whole | -2.5 / -1.7 | -3.5 / -2.0 | **-2.5 / -2.0** |  | +1.0 / -0.0 |
| Canada | to Dec 2022 | +1.5 / +1.0 | +1.5 / +1.2 | **+3.8 / +0.8** |  | +2.3 / -0.4 |
| Canada | 2023-26 | -2.8 / -0.7 | -2.8 / -0.7 | **-3.3 / -0.8** |  | -0.5 / -0.1 |
| Canada | whole | -0.8 / -0.0 | -0.8 / +0.1 | **+0.3 / -0.4** |  | +1.1 / -0.4 |
| UK | to Dec 2022 | +1.5 / -0.5 | +2.1 / -0.4 | **+0.6 / -0.2** |  | -1.5 / +0.2 |
| UK | 2023-26 | +6.3 / +1.5 | +4.8 / +1.6 | **+5.3 / +1.5** |  | +0.5 / -0.1 |
| UK | whole | +1.4 / +0.0 | +2.0 / +0.2 | **+1.2 / +0.1** |  | -0.8 / -0.1 |
| US large | to Dec 2022 | +0.6 / -0.4 | +0.4 / -0.2 | **+0.7 / +0.0** | +0.4 / -0.7 | +0.3 / +0.3 |
| US large | 2023-26 | +3.5 / +2.0 | +5.2 / +2.6 | **+4.5 / +2.6** | +4.5 / +2.6 | -0.7 / -0.1 |
| US large | whole | +1.0 / -0.5 | +0.7 / -0.3 | **+1.3 / -0.1** | +0.6 / -0.7 | +0.5 / +0.2 |
| US large | 2020-26 (round-6 look) | +2.1 / -0.8 | +1.9 / -0.7 | **+2.2 / -0.2** | +2.7 / -0.2 | +0.3 / +0.5 |
| US mid | to Dec 2022 | -1.1 / -1.0 | -0.6 / -0.7 | **-1.3 / -0.2** | -0.3 / -0.1 | -0.7 / +0.5 |
| US mid | 2023-26 | +7.5 / +5.9 | +9.0 / +5.0 | **+5.2 / +4.6** | +5.7 / +4.2 | -3.8 / -0.5 |
| US mid | whole | +1.1 / +0.0 | +1.9 / +0.5 | **+1.0 / +0.6** | +1.7 / +0.7 | -0.9 / +0.1 |
| US mid | 2020-26 (round-6 look) | +4.2 / +1.3 | +4.8 / +2.3 | **+3.7 / +1.9** | +3.2 / +1.8 | -1.1 / -0.4 |
| US small | to Dec 2022 | -1.6 / -2.0 | -1.4 / -1.2 | **+2.4 / +0.0** | +3.6 / +0.6 | +3.7 / +1.3 |
| US small | 2023-26 | +5.8 / +6.5 | +3.1 / +6.8 | **+8.6 / +5.9** | +6.4 / +5.4 | +5.5 / -0.9 |
| US small | whole | +0.4 / -0.6 | +0.3 / -0.2 | **+3.4 / +0.5** | +4.0 / +0.9 | +3.1 / +0.7 |
| US small | 2020-26 (round-6 look) | +2.3 / +0.7 | +2.3 / +1.0 | **+2.7 / +1.3** | +3.2 / +2.0 | +0.4 / +0.3 |
| **mean of the 8** | D | +0.3 / -0.3 | +0.3 / -0.3 | **+0.8 / -0.1** | | +0.4 / +0.2 |
| **mean of the 8** | C | +2.2 / +1.8 | +2.1 / +1.8 | **+2.4 / +1.7** | | +0.3 / -0.2 |
| **mean of the 8** | F | +0.2 / -0.3 | +0.3 / -0.2 | **+0.8 / -0.1** | | +0.5 / +0.1 |

### A. EI10I: after-tax lead over the local fund, points a year, A$25k / A$100k

| Market | Window | As published (old file) | Fresh download, rule as tested | **Corrected** | US: corrected + bad lines out | Change from correction (25k / 100k) |
|---|---|---|---|---|---|---|
| Germany | to Dec 2022 | +0.6 / +1.0 | +0.2 / +0.9 | **+0.3 / +0.9** |  | +0.1 / +0.0 |
| Germany | 2023-26 | -2.4 / -2.0 | -2.3 / -1.7 | **-2.5 / -1.9** |  | -0.1 / -0.2 |
| Germany | whole | -0.3 / -0.9 | -0.4 / -1.1 | **-0.4 / -1.0** |  | +0.0 / +0.1 |
| France | to Dec 2022 | +5.1 / +2.4 | +5.1 / +2.3 | **+5.6 / +2.8** |  | +0.5 / +0.4 |
| France | 2023-26 | -0.8 / -0.5 | -0.3 / -0.2 | **-0.2 / -0.1** |  | +0.1 / +0.1 |
| France | whole | +1.4 / +0.8 | +1.6 / +0.6 | **+2.2 / +0.9** |  | +0.6 / +0.3 |
| Sweden | to Dec 2022 | +3.6 / +2.3 | +3.1 / +2.8 | **+2.9 / +2.5** |  | -0.2 / -0.3 |
| Sweden | 2023-26 | +0.6 / -0.3 | +0.8 / -0.2 | **+0.8 / -0.0** |  | +0.0 / +0.2 |
| Sweden | whole | +2.4 / +0.7 | +2.2 / +1.3 | **+1.9 / +1.1** |  | -0.3 / -0.1 |
| Canada | to Dec 2022 | -0.2 / -0.2 | -0.2 / -0.2 | **-1.0 / +0.1** |  | -0.8 / +0.3 |
| Canada | 2023-26 | -1.6 / +0.4 | -1.8 / +0.4 | **-1.6 / +0.5** |  | +0.2 / +0.1 |
| Canada | whole | -0.9 / -0.8 | -0.8 / -0.6 | **-1.4 / -0.6** |  | -0.6 / +0.0 |
| UK | to Dec 2022 | +0.9 / +2.1 | +1.3 / +2.3 | **+1.2 / +2.2** |  | -0.2 / -0.1 |
| UK | 2023-26 | +3.8 / +3.8 | +4.0 / +3.9 | **+3.6 / +3.5** |  | -0.4 / -0.4 |
| UK | whole | +1.1 / +2.0 | +1.8 / +2.2 | **+1.2 / +1.8** |  | -0.6 / -0.4 |
| US large | to Dec 2022 | +1.5 / +1.5 | +1.7 / +1.4 | **+1.6 / +1.0** | +1.8 / +1.1 | -0.0 / -0.3 |
| US large | 2023-26 | +6.6 / +4.5 | +6.3 / +4.2 | **+6.0 / +4.3** | +6.0 / +4.3 | -0.3 / +0.2 |
| US large | whole | +2.6 / +2.2 | +2.7 / +2.3 | **+2.5 / +2.0** | +2.5 / +1.7 | -0.2 / -0.3 |
| US large | 2020-26 (round-6 look) | +2.4 / +1.9 | +2.2 / +1.4 | **+2.2 / +1.7** | +2.2 / +1.4 | +0.0 / +0.3 |
| US mid | to Dec 2022 | -1.0 / -0.7 | +1.2 / +0.3 | **+1.0 / +2.2** | +2.3 / +1.8 | -0.1 / +1.9 |
| US mid | 2023-26 | +4.1 / +2.9 | +4.1 / +2.8 | **+5.1 / +2.4** | +5.0 / +2.6 | +1.0 / -0.4 |
| US mid | whole | -0.5 / +0.1 | +1.0 / +0.1 | **+0.7 / +2.1** | +2.3 / +1.8 | -0.3 / +2.0 |
| US mid | 2020-26 (round-6 look) | +0.4 / +0.1 | +1.2 / +1.1 | **+0.9 / +0.1** | -0.7 / +0.4 | -0.4 / -1.1 |
| US small | to Dec 2022 | -1.1 / +1.1 | -0.3 / +1.9 | **-1.2 / +1.6** | +0.7 / -0.8 | -0.9 / -0.3 |
| US small | 2023-26 | +7.7 / +8.3 | +17.4 / +5.9 | **+14.4 / +6.5** | +18.3 / +7.4 | -3.1 / +0.6 |
| US small | whole | -0.4 / +2.6 | +0.6 / +3.1 | **-0.4 / +1.8** | +0.4 / -0.5 | -1.0 / -1.4 |
| US small | 2020-26 (round-6 look) | -0.2 / -1.0 | -0.3 / -1.9 | **-0.5 / -1.9** | -2.4 / -2.3 | -0.2 / -0.0 |
| **mean of the 8** | D | +1.2 / +1.2 | +1.5 / +1.5 | **+1.3 / +1.7** | | -0.2 / +0.2 |
| **mean of the 8** | C | +2.3 / +2.1 | +3.5 / +1.9 | **+3.2 / +1.9** | | -0.3 / +0.0 |
| **mean of the 8** | F | +0.7 / +0.8 | +1.1 / +1.0 | **+0.8 / +1.0** | | -0.3 / +0.0 |

### A. CW: after-tax lead over the local fund, points a year, A$25k / A$100k

| Market | Window | As published (old file) | Fresh download, rule as tested | **Corrected** | US: corrected + bad lines out | Change from correction (25k / 100k) |
|---|---|---|---|---|---|---|
| Germany | to Dec 2022 | +0.1 / -0.6 | +0.2 / -0.4 | **+0.2 / -0.4** |  | +0.0 / +0.0 |
| Germany | 2023-26 | -4.9 / -3.7 | -4.8 / -3.5 | **-4.8 / -3.5** |  | +0.0 / +0.0 |
| Germany | whole | -0.7 / -1.3 | -0.7 / -1.2 | **-0.7 / -1.2** |  | +0.0 / +0.0 |
| France | to Dec 2022 | +4.5 / +1.2 | +4.6 / +1.3 | **+4.6 / +1.3** |  | +0.0 / +0.0 |
| France | 2023-26 | -1.7 / -1.9 | -1.9 / -2.0 | **-1.9 / -2.0** |  | +0.0 / +0.0 |
| France | whole | +1.8 / +0.6 | +1.9 / +0.6 | **+1.9 / +0.6** |  | +0.0 / +0.0 |
| Sweden | to Dec 2022 | +2.7 / +3.5 | +2.8 / +3.6 | **+2.8 / +3.6** |  | +0.0 / +0.0 |
| Sweden | 2023-26 | -0.1 / -0.8 | -0.2 / -0.7 | **-0.2 / -0.7** |  | +0.0 / +0.0 |
| Sweden | whole | +2.0 / +0.6 | +1.8 / +0.6 | **+1.8 / +0.6** |  | +0.0 / +0.0 |
| Canada | to Dec 2022 | -2.2 / -1.3 | -2.3 / -1.5 | **-2.3 / -1.5** |  | +0.0 / +0.0 |
| Canada | 2023-26 | +0.5 / +0.6 | +1.0 / +0.8 | **+1.0 / +0.8** |  | +0.0 / +0.0 |
| Canada | whole | -1.2 / -0.8 | -1.1 / -0.8 | **-1.1 / -0.8** |  | +0.0 / +0.1 |
| UK | to Dec 2022 | -3.4 / -2.4 | -3.3 / -2.3 | **-3.0 / -2.6** |  | +0.3 / -0.3 |
| UK | 2023-26 | +1.3 / +0.7 | +1.2 / +0.5 | **+1.2 / +0.5** |  | +0.0 / +0.0 |
| UK | whole | -1.3 / -1.2 | -1.3 / -1.1 | **-1.2 / -1.3** |  | +0.1 / -0.1 |
| US large | to Dec 2022 | +2.7 / +1.3 | +2.4 / +1.3 | **+2.7 / +1.3** | +3.1 / +1.7 | +0.3 / +0.0 |
| US large | 2023-26 | +7.3 / +4.7 | +6.8 / +4.3 | **+6.8 / +4.3** | +6.8 / +4.3 | +0.0 / -0.1 |
| US large | whole | +3.5 / +1.9 | +3.2 / +1.8 | **+3.6 / +1.8** | +4.1 / +2.0 | +0.4 / +0.1 |
| US large | 2020-26 (round-6 look) | +1.9 / +1.7 | +2.0 / +1.9 | **+2.0 / +1.3** | +2.0 / +1.1 | +0.0 / -0.6 |
| US mid | to Dec 2022 | -3.6 / -1.4 | -3.5 / -0.7 | **-3.0 / -0.4** | -2.1 / -0.3 | +0.5 / +0.3 |
| US mid | 2023-26 | +2.5 / +3.1 | +2.3 / +4.8 | **+2.5 / +2.1** | +2.9 / +2.4 | +0.2 / -2.6 |
| US mid | whole | -4.7 / -3.2 | -4.2 / -3.1 | **-3.6 / -1.7** | -1.8 / -0.6 | +0.6 / +1.4 |
| US mid | 2020-26 (round-6 look) | -4.8 / -2.9 | -0.8 / -1.9 | **-0.5 / -2.5** | -0.9 / -1.8 | +0.2 / -0.7 |
| US small | to Dec 2022 | -0.9 / -0.2 | -1.2 / +0.0 | **-5.3 / -2.6** | -2.7 / -0.9 | -4.2 / -2.6 |
| US small | 2023-26 | +5.4 / +1.2 | +3.1 / +0.6 | **+3.7 / +0.4** | +3.4 / +0.3 | +0.6 / -0.2 |
| US small | whole | +1.0 / +1.9 | +0.9 / +2.5 | **-4.6 / -2.9** | -4.1 / -1.9 | -5.4 / -5.4 |
| US small | 2020-26 (round-6 look) | -3.3 / -3.8 | -2.1 / -4.3 | **-4.1 / -4.2** | -4.5 / -5.3 | -2.0 / +0.0 |
| **mean of the 8** | D | -0.0 / +0.0 | -0.0 / +0.2 | **-0.4 / -0.2** | | -0.4 / -0.3 |
| **mean of the 8** | C | +1.3 / +0.5 | +0.9 / +0.6 | **+1.0 / +0.2** | | +0.1 / -0.4 |
| **mean of the 8** | F | +0.0 / -0.2 | +0.1 / -0.1 | **-0.5 / -0.6** | | -0.6 / -0.5 |

### A. Percentile among 100 random books (after tax, first start; whole window, US bands 2020-26), A$25k / A$100k

| Market | M3 published file | M3 fresh, as tested | **M3 corrected** | EI10I published file | EI10I fresh, as tested | **EI10I corrected** |
|---|---|---|---|---|---|---|
| Germany | 97 / 100 | 95 / 98 | **97 / 88** | 91 / 55 | 91 / 64 | **92 / 54** |
| France | 76 / 100 | 66 / 91 | **72 / 95** | 63 / 66 | 68 / 59 | **73 / 84** |
| Sweden | 45 / 66 | 53 / 74 | **86 / 49** | 69 / 54 | 57 / 60 | **43 / 50** |
| Canada | 76 / 92 | 79 / 82 | **88 / 72** | 84 / 82 | 92 / 90 | **92 / 74** |
| UK | 92 / 97 | 97 / 95 | **80 / 91** | 100 / 100 | 100 / 100 | **100 / 100** |
| US large | 95 / 84 | 81 / 84 | **80 / 73** | 68 / 80 | 72 / 52 | **65 / 56** |
| US mid | 99 / 80 | 99 / 94 | **97 / 89** | 91 / 91 | 94 / 96 | **99 / 79** |
| US small | 92 / 92 | 65 / 98 | **99 / 97** | 92 / 78 | 98 / 81 | **87 / 89** |

### A. M3 in the round-5 pool of 18 market-sets

| Window | Files as published: mean 25k / 100k; sets ahead | Fresh download, as tested | **Corrected** |
|---|---|---|---|
| to Dec 2022 | +1.3 / +0.8; 12 of 18 | +1.3 / +0.8; 11 of 18 | **+1.5 / +0.9; 13 of 18** |
| 2023-26 (in-pool check) | +1.6 / +1.2; 12 of 18 | +1.6 / +1.2; 12 of 18 | **+1.7 / +1.1; 12 of 18** |
| whole | +0.6 / +0.4; 11 of 18 | +0.7 / +0.4; 12 of 18 | **+0.9 / +0.4; 12 of 18** |

### A. Report 79 replication rows (starts Dec 2018 - Sep 2019, to Oct 2026), after-tax lead, A$25k / A$100k

| Market | Design | Published | Fresh, as tested | **Corrected** |
|---|---|---|---|---|
| Germany | earnings surprise + M3 | -1.7 / -1.9 | -1.7 / -1.9 | **-1.4 / -0.9** |
| Germany | CW | -1.2 / -1.3 | -1.2 / -1.3 | **-1.2 / -1.3** |
| Germany | M3 | +2.3 / +1.0 | +2.3 / +1.0 | **+3.2 / +0.9** |
| Sweden | earnings surprise + M3 | -1.5 / -0.3 | -2.0 / -0.5 | **-2.1 / -0.5** |
| Sweden | CW | +2.0 / +0.6 | +1.8 / +0.6 | **+1.8 / +0.6** |
| Sweden | M3 | -2.5 / -1.7 | -3.5 / -2.0 | **-2.5 / -2.0** |
| Canada | earnings surprise + M3 | +3.2 / +1.8 | +3.2 / +1.9 | **+2.8 / +1.7** |
| Canada | CW | -1.2 / -1.2 | -1.0 / -1.3 | **-1.0 / -1.3** |
| Canada | M3 | +0.2 / +0.1 | +0.2 / +0.2 | **+0.7 / -0.2** |
| US large | earnings surprise + M3 | -0.1 / -0.9 | -0.3 / -1.0 | **+1.3 / -1.0** |
| US large | CW | +4.6 / +3.1 | +4.7 / +3.5 | **+4.7 / +1.8** |
| US large | M3 | -0.2 / -0.7 | +0.8 / -0.5 | **+2.2 / -0.4** |
| US mid | earnings surprise + M3 | +0.6 / +0.6 | +0.2 / +0.7 | **-0.8 / -0.2** |
| US mid | CW | -2.4 / -1.7 | -1.6 / -1.3 | **+1.2 / -1.7** |
| US mid | M3 | +4.4 / +1.1 | +5.0 / +1.6 | **+4.0 / +2.1** |
| US small | earnings surprise + M3 | +1.6 / +1.5 | +2.8 / +1.7 | **+3.1 / +2.2** |
| US small | CW | -3.5 / -2.3 | -2.4 / -2.3 | **-3.3 / -3.0** |
| US small | M3 | +5.2 / +1.2 | +4.6 / +1.6 | **+5.5 / +3.0** |
| **12 markets** | earnings surprise + M3 | mean +0.6 / +0.6; +1 at both sizes in 4 | | **mean +0.6 / +0.7; +1 at both sizes in 4** |
| **12 markets** | CW | mean +0.4 / +0.0; +1 at both sizes in 3 | | **mean +0.7 / -0.2; +1 at both sizes in 3** |
| **12 markets** | M3 | mean +2.0 / +1.2; +1 at both sizes in 6 | | **mean +2.3 / +1.4; +1 at both sizes in 6** |

### A. Report 81 designs D1-D3 (after tax, sold at end), A$25k / A$100k

| Market | Design | Published | Fresh, as tested | **Corrected** |
|---|---|---|---|---|
| US large | D1 | +0.3 / -2.1 | -1.0 / -2.2 | **-1.2 / -1.6** |
| US large | D2 | +3.1 / +2.2 | +2.9 / +2.0 | **+2.8 / +1.6** |
| US large | D3 | -0.6 / -1.4 | -1.1 / -1.4 | **-1.1 / -1.5** |
| US large | REF_M3 | -2.0 / -0.3 | -0.7 / -0.5 | **+1.1 / +0.0** |
| Canada | D1 | +1.7 / +0.2 | +1.7 / +0.2 | **+1.8 / +0.2** |
| Canada | D2 | -3.4 / +0.2 | -3.4 / +0.3 | **-2.8 / -0.1** |
| Canada | D3 | -0.2 / -0.2 | +0.1 / -0.4 | **-1.1 / -0.0** |
| Canada | REF_M3 | +0.8 / +0.6 | +1.5 / +0.7 | **+0.8 / +0.1** |
| UK | D1 | +2.7 / +0.6 | +2.3 / +0.5 | **+1.9 / +0.2** |
| UK | D2 | -0.3 / +0.3 | +0.4 / -0.1 | **+0.0 / -0.0** |
| UK | D3 | -1.4 / -1.4 | -1.5 / -1.5 | **-2.2 / -1.1** |
| UK | REF_M3 | +1.9 / +0.5 | +2.0 / +0.4 | **+1.6 / +0.6** |
| Germany | D1 | +0.5 / -0.6 | +0.5 / -0.6 | **+0.8 / -0.0** |
| Germany | D2 | -0.6 / -0.3 | +0.1 / -0.5 | **+0.5 / -0.2** |
| Germany | D3 | -1.3 / -0.3 | -1.3 / -0.1 | **-1.3 / +0.0** |
| Germany | REF_M3 | +3.1 / +1.3 | +3.1 / +1.3 | **+1.9 / +1.5** |
| France | D1 | -1.4 / -0.5 | -1.8 / -1.1 | **-2.0 / -0.9** |
| France | D2 | +2.2 / +1.0 | +2.6 / +1.3 | **+2.4 / +1.6** |
| France | D3 | -1.9 / -1.6 | -2.3 / -1.5 | **-2.3 / -1.4** |
| France | REF_M3 | -0.4 / -0.2 | +0.1 / -0.7 | **+0.1 / -0.5** |
| Sweden | D1 | -1.2 / -2.1 | -2.5 / -2.8 | **-1.3 / -2.7** |
| Sweden | D2 | +2.5 / +2.6 | +2.5 / +2.1 | **+2.5 / +1.7** |
| Sweden | D3 | -2.3 / -1.0 | -2.4 / -1.0 | **-2.7 / -1.1** |
| Sweden | REF_M3 | -2.7 / -1.3 | -3.0 / -1.5 | **-3.1 / -1.7** |
| **all 20 replication sets** | D1 | mean +1.02 / +0.55; +1 at both sizes in 8; any cell < -2 in 5 | | **mean +0.89 / +0.54; +1 at both sizes in 8; any cell < -2 in 5** |
| **all 17 replication sets** | D2 | mean +0.22 / +0.33; +1 at both sizes in 5; any cell < -2 in 3 | | **mean +0.33 / +0.25; +1 at both sizes in 5; any cell < -2 in 3** |
| **all 20 replication sets** | D3 | mean -0.33 / -0.24; +1 at both sizes in 4; any cell < -2 in 4 | | **mean -0.48 / -0.21; +1 at both sizes in 4; any cell < -2 in 6** |

### A. Report 82 loser screen (bottom 30% removed, gain against the list's own return, 2013-2026, points a year (t))

| Screen, weights | Published files | Fresh, as tested | **Corrected** | Corrected, without US |
|---|---|---|---|---|
| M3 score, capped traded-value weights (21 sets) | +2.83 (4.4); ahead in 21/21 | +2.60 (4.0) | **+1.83 (2.9)**; ahead in 21/21 | +1.70 (2.8) |
| M3 score, cap weights (18 sets) | +0.90 (2.1); ahead in 17/18 | +0.86 (2.0) | **+0.96 (2.1)**; ahead in 16/18 | +0.88 (1.9) |
| new score of report 82, capped traded-value weights | +2.77 (4.4); ahead in 20/21 | +2.56 (4.0) | **+1.66 (2.7)**; ahead in 20/21 | +1.46 (2.5) |
| new score, cap weights | +0.66 (1.7); ahead in 16/18 | +0.63 (1.6) | **+0.76 (1.8)**; ahead in 16/18 | +0.66 (1.6) |
| by set, M3 W1: | USL +20.6, CA +2.2, UK +5.5, DE +2.0, FR +0.9, SE +0.4 | USL +16.2, CA +2.2, UK +5.4, DE +2.0, FR +0.5, SE +0.4 | USL +4.6, CA +1.8, UK +1.7, DE +1.9, FR +0.2, SE +0.4 | |
