# 82. Round 10: can the loser filter be made into a real edge? A higher-powered test, a better avoid list, execution and churn

19 November 2026. Author: research agent (Fable). Scope: Big Wins only. Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades.
Work folder: `scratchpad/deep82/` (`PREREG_82.md`, `PREREG_82b.md`, `code/`, `out/`, `PROGRESS.md`, `SPEC_avoid_list_measurement_line.md`). The live paper record, ledger, frozen code and scheduled tasks were not touched. No new data were downloaded (0 EODHD credits). Trial count: 1,729 → **1,759** (`out/trials_82.csv`).

How to read the figures: "gain" = points a year. "After tax" = A$0 brokerage, modelled half-spread, 32% tax, 50% discount after 12 months, everything sold at the end. t = the mean divided by its standard error; about 2 is "probably not luck", 3 is the adopt bar.

## 0. Answer first

**Nothing passed. I did not find an improvement that beats the index fund by the adopt bar, and this round shows why one is unlikely to exist in this family.**

1. **The loser filter is real. This is now the best-supported fact in the programme.** Selected on 2001–2012 and tested on 2013–2026, removing the weakest 30% of the 100 most traded shares lifted a size-weighted list by **+1.75 to +1.9 points a year** across 20 markets (t 2.9 to 3.2; ahead in 19–20 of 20 markets; positive in both halves and in every period since 2001). With the US set included the figure is +2.8 and t 4.4, but the US set is faulty (point 7) and I do not rely on it.
2. **On true index weights it is worth +0.7 to +0.9 before costs, and that is the ceiling.** Same test with market-cap weights: +0.9 (t 2.1) for the existing M3 screen, +0.7 (t 1.7) for the new one; positive in 16–17 of 18 markets. Losers are 14–19% of a cap-weighted 100, and the big ones lag less than the small ones. After the spread (0.1 to 0.2) it is +0.6 to +0.75.
3. **In a book a person can hold, almost none of it arrives.** The 30-name D2 book against the *same book with no screen*: **+0.2 at A$100,000 (t 0.4), −0.5 at A$25,000**. A 70-name version at A$1,000,000: +0.3 after tax (t 0.8). On ASX the screen *subtracted* 0.3 to 0.95 in 2018–2026. D2's small lead in report 81 came from holding the largest companies, not from the screen.
4. **A better avoid list was not found.** Five price scores at three depths, and three add-ons, pre-registered:
   - A new price score (residual momentum + nearness to high + low residual volatility) won in development and repeated on blunt size weights with half the turnover of M3. On cap weights it was no better than M3. Not confirmed by the pre-set rule.
   - **Share issuance** on top of the price screen: +0.1 (t 1.1). No use.
   - **Loss-makers** on top: **−0.3** (t −1.7). Harmful. It removes recovering companies.
   - **Short interest** (ASX, 2013–2026): +0.1 to +0.2 (t under 1). No use.
   - Underweighting instead of excluding earns the same per unit of risk: half the cut, 41% of the gain, same t. Depth of cut: gain rises in step with depth; there is no sweet spot.
5. **The buffer rule against January churn makes H82 worse.** Keeping a holding that is still in the best 60: turnover falls only from 0.54 to 0.47 and the result falls by 0.4 a year after tax at A$100,000 (t −2.2; ahead in 8 of 20 markets). On ASX: no change. Do not add it.
6. **Closing-auction fills: the saving is real for the 100 most traded and unproven below that.** Closing prices of the top 100 show no bid-ask bounce at all (section 7). For ranks 101–300 they show some. My "+0.8 at A$100,000" in report 81 was too high. The supportable figure is **+0.2 to +0.4 a year** for H82 and about +0.1 for a large-company book.
7. **Two new faults.** (a) The US back-test set ranks "most traded" on adjusted price × volume. In 93 of 106 months one reverse-split penny share carried over 20% of the list's raw traded value, and 5–12 of the "100 most traded US shares" in 2018–19 were under US$5. Every US back-test figure in rounds 3–8 used that list. The October 2026 list is clean. (b) The report-81 engine leaves money in cash when a cap-weighted book cannot fill its slots (17% of the account in my first 70-name run). The 30-name D2 as registered is not materially affected (0.4% cash on ASX).
8. **Why the bar cannot be reached this way.** The index fund holds 81–86% of its money in companies the screen does not flag. Removing the rest can add at most the +0.7 to +0.9 above. Tax, spread and the 30-name limit take most of that. To get more, a book must move money toward smaller companies, where the screen works better, and then it carries the size bet that cost H82 1.2 a year (report 81). There is no third route in price data.
9. **What forward data would settle it.** For an edge under one point: none of practical length. D2 against the fund on ASX needs centuries. D2 against its own no-screen twin across 17 markets needs about 18 years to see +1.0 and about 200 to see +0.3. The one thing a forward record can settle is whether the screen keeps separating losers on blunt size weights: about 6 years for t = 2 and 13 for t = 3. A spec for that measurement line is in section 9. It is a measurement, not a book.

**What to do.** (i) Change nothing in H82. (ii) Read the new D2 (CXL) shadow line against the median of its 100 random-exclusion books, never against the fund alone; that difference is the screen's own contribution, and the expectation is about zero. (iii) Keep "bottom 30% by price strength" on the red-flag panel. Do not add loss-maker, issuance or short-interest rules to any size-weighted book. (iv) If orders are ever placed, use the closing auction for the 100 most traded names. (v) Repair the traded-value ranking of the non-ASX packs the way v1.4 repaired ASX. (vi) My estimate of the true after-tax edge of the best Big Wins construction at A$100,000 narrows from "−0.5 to +1, most likely +0.3" to **"−0.3 to +0.6, most likely +0.2"**. The index fund remains the thing to hold.

---

## 1. Plan and why

Report 81 found one working part: the score detects losers. It also found that leads under 1.5 points were inside the noise of the test. So the order of work was: (1) build a test with less noise; (2) try to sharpen the loser list, judged only on how well it separates the worst names on a size-weighted base, out of sample; (3) carry any survivor into the engine with costs and tax; (4) check the two cost ideas (closing auction, buffer rule). Everything was written down and hashed before it was run (`out/prereg82_hash.txt`, 05:04 UTC; addendum 05:40 and repair note 05:50).

## 2. A test with less noise

**Method.** Report 81 compared a 30-name book with the local index fund. The gap between any 30-name book and the fund swings 3 to 7 points a year, so 17 markets over nine years gave a standard error of 0.4 to 0.5. This round compares a size-weighted list of the 100 most traded shares with **the same list minus the avoided names**. Only the avoided names differ, so most of the noise cancels. Monthly; returns from the next day's close to the next day's close; no costs inside the measure (extra turnover is reported and costed). 20 market-sets plus ASX; 2001–2026 (ASX: source-V pack to 2017, EODHD v1.4 pack after).

**Weights.** W1 (all sets, all years): median traded value, capped at ten times the list's median, so no name holds more than about 5%. This is a blunt size weight, between equal and cap weight. The cap was needed because raw traded value is corrupted in several sets (section 8). W2 (the real thing, where data exist): market cap, 15% limit per name, months with at least 60 caps.

**Noise floor found** (`out/noise0.csv`, `out/stageB.json`, `out/summ82.json`):

| What is compared | Swing of the difference, points a year | Standard error over 2013–2026 |
|---|---|---|
| Report 81: 30-name book against the fund, 17–20 sets, 2018–2026 | 3–7 per set | 0.36–0.50 |
| Random 30% removed, against own list, pooled (W1) | 0.74 | 0.20 |
| **Momentum losers removed, against own list, pooled (W1)** | **2.3–2.4** | **0.6** |
| Momentum losers removed, pooled (W2, cap weights) | 1.5–1.6 | 0.4 |
| Engine: D2 against its no-screen twin, pooled, 17 sets | 2.1 | 0.7 (2018–2026) |

The third row is the lesson. Random exclusions average out across 21 markets. Loser exclusions do not, because losers in every market rebound together (2003, 2009, late 2020). Adding markets buys little. **The remaining noise is the momentum factor itself, and only time reduces it.**

Two engines still differ by up to 1.4 points on the same rules (report 81). The remedy used here is to run both arms of every comparison in the same engine and read only the difference.

## 3. The avoid list

### 3.1 Development, Dec 2000–Dec 2012 (16 trials; W1; 21 sets; `out/stageA.json`)

Scores (low = loser): **M3** = 12-to-1-month return, 6-month return, nearness to 52-week high (the current screen). **H82** = M3 + low volatility. **NH** = nearness to high only. **JL** = M3 + low residual volatility + no recent extreme up-days. **RM** = residual momentum (momentum after removing the market's move) + nearness to high + low residual volatility. **VL** = bottom 30% by M3 and top 30% by residual volatility.

| Rule, % cut | Gain | t | Sets ahead | Weight removed | Extra turnover a year |
|---|---|---|---|---|---|
| M3 10 / 20 / 30 | 0.62 / 1.09 / 1.49 | 1.27 / 1.29 / 1.27 | 15 / 18 / 15 | 9 / 18 / 28% | 0.25 / 0.54 / 0.84 |
| H82 10 / 20 / 30 | 0.72 / 1.27 / 1.55 | 1.45 / 1.46 / 1.28 | 17 / 19 / 20 | 8 / 17 / 27% | 0.21 / 0.42 / 0.70 |
| NH 10 / 20 / 30 | 0.58 / 0.96 / 0.94 | 1.15 / 1.08 / 0.74 | 15 / 16 / 17 | 8 / 17 / 27% | 0.18 / 0.43 / 0.80 |
| JL 10 / 20 / 30 | 0.86 / 1.13 / 1.69 | 1.75 / 1.33 / 1.40 | 17 / 20 / 20 | 8 / 17 / 26% | 0.18 / 0.37 / 0.59 |
| **RM 10 / 20 / 30** | 0.68 / 1.47 / **2.09** | 1.57 / 1.96 / **2.06** | 18 / 19 / **20** | 8 / 16 / 25% | 0.16 / 0.33 / 0.53 |
| VL | 0.85 | 1.27 | 16 | 11% | 0.20 |

Chosen by the pre-set rule (highest t with gain ≥ +0.3): **RM, 30%**. Every rule was positive; none was strong in this period alone. The gain rises roughly in step with the depth of the cut and t does not, so depth is a choice of size, not of quality.

### 3.2 Confirmation, Dec 2012–Oct 2026 (1 trial; `out/stageB.json`, `out/exUSL.json`)

| | RM 30% (new) | M3 30% (current screen; reference) |
|---|---|---|
| W1 gain, 21 sets | **+2.77**, t 4.37 | +2.83, t 4.40 |
| W1 gain without the US set | **+1.75**, t 2.90 | +1.94, t 3.18 |
| W1, median market each month | +1.95, t 3.47 | +2.23, t 3.92 |
| Sets ahead (W1) | 20 of 21 | 21 of 21 |
| 2013–2019 / 2020–2026 (W1) | +2.81 / +2.75 | +2.99 / +2.69 |
| Half weight instead of exclusion (W1) | +1.14, t 4.28 | +1.17, t 4.41 |
| **W2 (cap weights) gain, 18 sets** | **+0.66, t 1.66** | **+0.90, t 2.06** |
| Sets ahead (W2) | 16 of 18 | 17 of 18 |
| Weight removed, W1 / W2 | 25% / 14% | 27% / 19% |
| Extra turnover a year, W1 / W2 | 0.50 / 0.41 | 0.77 / 0.79 |
| W2 gain after the modelled spread | about +0.58 | about +0.74 |

Pre-set conditions for "confirmed": (1) W1 t ≥ 3.0: met with the US set, 2.90 without it. (2) More than half the sets ahead: met. (3) Both halves positive: met. (4) Cap-weight gain at least half the W1 gain: **not met** (0.66 against 2.77, or against 1.75 without the US). **Verdict: RM is not confirmed as an improvement on cap weights.** It is as good a loser list as M3 with about half the turnover, and no better where it matters.

By set, W1, 2013–2026, M3 / RM: US +20.6 / +23.2 (faulty, section 8); Canada +2.2 / +1.7; UK +5.5 / +6.1; Germany +2.0 / +1.6; France +0.9 / +0.9; Sweden +0.4 / +1.6; Netherlands +1.0 / −0.2; Denmark +1.8 / +1.8; South Africa +1.4 / +0.9; Korea +1.9 / +2.7; Spain +1.7 / +0.6; Norway +2.9 / +3.1; Brazil +4.1 / +4.4; Switzerland +2.2 / +1.7; Taiwan +1.4 / +0.6; Thailand +0.7 / +0.7; China +1.1 / +0.9; Finland +1.0 / +0.4; Poland +2.8 / +3.5; Belgium +2.3 / +1.4; **ASX +1.6 / +0.7**.
By set, W2: US +0.4 / +0.7; Canada +1.4 / +1.1; UK +1.2 / +0.9; Germany +1.1 / +0.7; France +0.5 / +0.2; Sweden 0.0 / +0.7; Netherlands +1.1 / +0.3; Denmark +1.5 / +2.8; South Africa +1.1 / +0.4; Korea +2.1 / +2.5; Spain +1.2 / −0.2; Norway 0.0 / +0.3; Brazil +0.3 / +0.7; Switzerland +1.0 / +0.3; Taiwan +1.7 / +0.8; Thailand +0.4 / 0.0; China +1.9 / +0.2; **ASX +0.9 / +0.3**.

Nearly every market is positive, but the markets are not independent trials here (section 2). The t-values, not the counts, carry the evidence. On its own data ASX is not significant (W1: t 1.6 for M3, 0.7 for RM).

### 3.3 Robustness (description; no new trials except where stated)

| Split | M3 30%, W1 | RM 30%, W1 | M3 30%, W2 | RM 30%, W2 |
|---|---|---|---|---|
| 2001–2008 | +2.9 (t 2.3) | +3.1 (2.9) | +1.3 (1.1) | +1.6 (1.8) |
| 2009–2017 | +1.5 (1.3) | +2.0 (1.9) | +0.2 (0.2) | +1.2 (1.9) |
| 2018–2026 | +2.7 (3.3) | +2.8 (3.5) | +1.1 (1.8) | +0.6 (1.2) |
| 2001–2026 | +2.2 (3.4) | +2.5 (4.2) | +0.8 (1.7) | +1.1 (2.9) |
| 300 most traded, 2013–2026 | +2.7 (4.2) | +2.6 (4.4) | +1.8 (2.8)* | +1.6 (2.7)* |
| ASX, 300 most traded, 2013–2026 | +2.2 | +1.8 | +0.9 | +0.8 |

W1 figures include the US set. *Only the few sets with 150 or more caps. Cap data before 2010 cover a minority of sets and are survivor-biased; read the early W2 cells loosely.
Start month: the measure re-forms every month, so there is no start-month luck in it. Engine runs below use four quarterly starts.
Sell delay (`code/lagdiag.py`): acting one month late leaves the W2 gain unchanged (+0.92). Requiring two month-ends running, as D2 does, cuts it to +0.73 and turnover to 0.51.
Sector-neutral variants were not run: no sector data outside ASX, and report 81 found industry was not the story.

**Where the cap-weighted gain sits** (M3 30%, W2, 2013–2026; `out/extras.json`):

| Losers removed only from cap rank | Gain | t | Weight removed | Losers' shortfall against the rest |
|---|---|---|---|---|
| 1–20 | +0.41 | 1.4 | 12.1% | about 3.0 a year |
| 21–50 | +0.26 | 2.5 | 4.7% | about 5.3 |
| 51–100 | +0.13 | 2.5 | 2.1% | about 5.9 |

The screen is statistically cleanest in ranks 21–100, where there is little index money (7%). Among the 20 largest it removes the most weight and is the least reliable. This is report 81's finding again, now measured across 18 markets: **the edge lives where the index has almost no money.**

**Against the fund** (2 trials; monthly, cost-free list with losers removed, minus the local fund's total return; `out/extras.json`):

| | 2001–2026 | 2018–2026 | The list itself, no screen, 2018–2026 |
|---|---|---|---|
| W1, M3 screen | +2.6 (t 4.1) | +1.0 (t 1.2) | −1.7 |
| W2 (cap), M3 screen | +1.0 (t 1.6) | +1.1 (t 1.7) | 0.0 |
| W2 (cap), RM screen | +1.3 (t 2.4) | +0.65 (t 1.3) | 0.0 |

A blunt-weighted list was 1.7 behind the fund in 2018–2026 (the giants led) and the screen brought it back to +1.0. The long-run +2.6 is mostly 2001–2008 (+5.5). These lists hold about 70 names with monthly trading and no tax; they are a ceiling, not a design.

## 4. Add-ons: accounts, issuance, short interest (6 trials; 2013–2026; `out/stageC.json`)

Each add-on avoids extra names on top of the price screen. The figure is the extra gain over the price screen alone.

| Add-on | On M3, W1 | On M3, W2 | On RM, W1 | On RM, W2 | Sets ahead (W2) | Verdict |
|---|---|---|---|---|---|---|
| Share count up more than 10% in the latest accounts | +0.13 (t 1.1) | +0.12 (1.2) | +0.11 (1.2) | +0.15 (1.6) | 12 of 18 | No use shown. First half −0.05, second +0.3 |
| Net loss in the latest accounts | −0.21 (−1.0) | **−0.32 (−1.7)** | −0.21 (−1.4) | **−0.30 (−1.9)** | 5–7 of 18 | **Harmful** |
| Short interest in the top tenth (ASX only; ASIC reports with a 7-day lag) | +0.18 (0.7) | +0.10 (0.4) | +0.15 (0.8) | +0.14 (0.6) | — | No use shown |

This agrees with reports 62, 77 and 81. Once price weakness is used, the accounts add nothing, and "no loss-makers" removes recovering companies. Fundamentals before 2018 exist mainly for companies that survived, which favours any accounts filter; it still failed. ASX accounts cover 2018–2026 only.

## 5. From the list to a book (engine `deep81/code/sim81.py`; 17 sets with caps + ASX; 2018–2026; four start months)

### 5.1 D2 against its own twin (a stress of report 81's D2; not a trial; `out/twin_*.json`, `out/summ82.json`)

The twin is the same 30-name cap-weighted book with nothing excluded. It has no skill in it.

| After tax, lead over the fund | A$25,000 | A$100,000 |
|---|---|---|
| D2 (M3 losers excluded), mean of 17 sets | +0.22 | +0.33 |
| Twin (no screen) | +0.72 | +0.14 |
| **D2 minus twin** | **−0.50** (t −1.1; ahead in 8 of 17) | **+0.19** (t 0.4; ahead in 12 of 17) |
| ASX: D2 / twin / difference | +1.27 / +2.22 / **−0.95** | +0.51 / +1.26 / **−0.75** |
| Turnover a year, D2 / twin | 0.34 / 0.05 | 0.35 / 0.04 |

D2 was "+0.2 / +0.3" against the fund in report 81. A book of the 30 largest companies with no screen did the same. On ASX the plain book led the fund by 1.3 to 2.2 after tax, because the 20 largest companies returned 10.0% a year against 8.8% for the index; the screen took 0.75 to 0.95 of that away. The pooled monthly difference between D2 and its twin is +0.06 a year with a swing of 2.1.

### 5.2 A wider book (4 trials; `PREREG_82b.md`; `out/summd2w.json`, `out/summd2wR.json`)

Question: is the 30-name limit what loses the +0.7 to +0.9? Same rules with up to 70 names, at A$1,000,000 (no lot-size limits) and A$100,000 (40 names).

*First run, void.* The engine sizes each target as weight × account × (names available ÷ 70). Where fewer than 70 screened names had a cap, the rest stayed in cash: 17% of the account on average, over 40% in Copenhagen and Oslo (`out/cashdiag.csv`). Result as run: −0.56 against the twin (t −2.1). It measures cash, not the screen. Both trials stay counted.

*Repaired run (post-hoc, labelled as such).* Targets = cap weight × account; top-ups whenever a holding is 5% under target. Cash 0.1–0.2%.

| After tax | A$100,000 (40 names) | A$1,000,000 (up to 70) |
|---|---|---|
| Twin (no screen), lead over fund | +0.09 | +0.09 |
| M3 screen, lead over fund | +0.20 (9 of 17 ahead) | +0.42 (11 of 17) |
| **M3 screen minus twin** | +0.11 (t 0.3) | **+0.33 (t 0.8; 11 of 17)** |
| RM screen minus twin | −0.02 (t −0.1) | +0.14 (t 0.4; 12 of 17) |
| ASX, M3 screen minus twin | −0.48 | −0.34 |
| Pooled monthly lead over the fund before tax, M3 | +0.6 (t 0.8) | +0.9 (t 1.3) |

Pre-set test for "a scalable gain exists" (≥ +0.5 against the twin with t ≥ 2 at A$1,000,000): **not met**. Adopt-rule-v2 standard read as a back-test (≥ +1.0 after tax at A$100,000, pooled t ≥ 3, more than half the sets ahead): **not met** (+0.2, t 0.8).

The wide book keeps roughly a third to a half of the list's +0.8 (the list with D2's two-month wait). The rest goes to the rule that a holding in profit is not sold inside 12 months, the spread on 0.35 turnover, and tax. With a standard error of 0.4, "+0.3" and "nothing" cannot be told apart.

## 6. The buffer rule against January churn (1 trial; `code/sim82.py`, `out/E_*.json`)

Rule: at the December review a holding stays if it is still among the best 2n by score (60 for a 30-name book); only the remaining places are filled from the top. All else as the H82 form of report 81. `sim82` without the option reproduces `sim81` exactly (checked).

| Buffer minus no buffer, 20 sets | A$25,000 | A$100,000 | ASX |
|---|---|---|---|
| After tax | −0.24 (t −1.0; 9 of 20 ahead) | **−0.37 (t −2.2; 8 of 20)** | −0.02 / +0.01 |
| Before tax | −0.12 | −0.53 (t −2.6) | −0.60 / +0.15 |
| Turnover | 0.72 → 0.67 | 0.54 → 0.47 | 0.91 → 0.86 / 0.88 → 0.67 |
| Spread paid over nine years | −A$47 | −A$316 | −A$50 / −A$738 |

Pre-set test (≥ +0.3 at A$100,000, t ≥ 2, more than half the sets): **failed, with the wrong sign**. The names it keeps are the ones the score has marked down, and report 81 showed that sold names trail by 2.3 points over the next year. The saving in spread is A$35 a year on A$100,000. The January swap cost in report 81 (−0.2) is timing luck, and a buffer does not remove luck.

## 7. Execution: does a closing-auction fill avoid the half-spread? (cost evidence; no trial)

**Mechanics** (from public ASX material as I recall it; I did not access the ASX website, and the owner should read the current "trading hours" and closing-auction pages by hand before relying on this). Normal trading stops at 4:00 pm Sydney. Orders can be entered, changed and cancelled until the Closing Single Price Auction, which runs at a random moment shortly after 4:10 pm. One price is set that matches the most volume. Every matched buyer and seller trades at that one price. It becomes the official close, which is the closing price EODHD publishes and the price the engine values and "trades" at. A buy order with a limit above the auction price is filled at the auction price, not at its limit.

So a small order in the auction pays no spread: there is no bid and ask, only one price. What it can still pay is its own push on that price. The engine's rule keeps each order under 1% of the median day's traded value, and for the 100 most traded names an A$3,300 order is under 0.02% of a day's value.

**What daily data can check** (`code/spread.py`, `code/spread2.py`, `out/spread_bands_mktadj.csv`; ASX, 2018–2026, raw EODHD open/high/low/close; 500 most traded). If closing prices sat at the bid or the ask, each share's daily return would tend to reverse the next day (the "bounce"). After removing the market's own move:

| Traded-value rank | Half a price tick, basis points | Modelled half-spread | Day-to-day correlation of closes | Shares with no bounce at all | Same for opening prices |
|---|---|---|---|---|---|
| 1–20 | 1.6 | 10 | +0.015 | 65% | +0.005 |
| 21–50 | 3.8 | 10 | −0.006 | 43% | −0.032 |
| 51–100 | 4.8 | 10 | +0.003 | 52% | −0.026 |
| 101–200 | 8.6 | 25 | −0.016 | 29% | −0.045 |
| 201–300 | 11.9 | 25 | −0.042 | 24% | −0.061 |
| 301–500 | 9.6 | 50 | −0.086 | 12% | −0.104 |

- **Top 100: no bounce.** The closes behave like single auction prices. The half-spread the engine charges there (10 basis points a side) is avoidable.
- **Ranks 101–300: some bounce**, growing with illiquidity. Either the auction often does not match in these names, so the "close" is the last trade at the bid or ask, or small auctions are pushed around. Either way an order there may not fill, or may move the price. I would not count the saving.
- Estimators that read the spread itself from daily highs and lows (Corwin–Schultz, Abdi–Ranaldo) gave 17–30 basis points for every band including the largest, where the true spread is one or two. They are measuring volatility. **End-of-day data cannot measure the spread; they can only show the absence of bounce.**

**Effect on the figures.** H82 at A$100,000 pays about 0.4 a year in spread (report 81), most of it in ranks 101–300. Avoidable with reasonable confidence: the top-100 part and perhaps half the rest, **+0.2 to +0.4 a year**. For D2-type books of large companies: about +0.1. Report 81's "+0.8" compared two runs that also differed by path. Withdraw it.
What would turn this into evidence: a log of real auction fills against the official close. The paper record has no fills, so it cannot supply that.

## 8. Faults found this round

| Fault | Where | Effect | Action |
|---|---|---|---|
| "Most traded" in the non-ASX packs is adjusted close × volume. After a reverse split the vendor scales old prices up and leaves old volume alone, so a penny share looks heavily traded | `improve*/data/pack_*_M.npz`, `medtv`, `vrank`; `out/tv_outliers.csv` | US set, 2018–2026: one junk name over 20% of the list's raw traded value in 93 of 106 months (VCIG, CHAI, XTIA); 5–12 of the "100 most traded" under US$5 in 2018–19, 2 in 2024, 0 in Oct 2026. Smaller cases: UK (BLT, RBS, SHP share-class and price-unit lines), Korea and Taiwan before 2010. US back-test figures in rounds 3–8 were on this list | Apply the v1.4 rule (raw close × volume) to every market pack before any further US back-test. Check the forward US list each month for names under US$5 |
| Cap-weighted targets are scaled by names available ÷ n; no top-up until the book is full or a holding is 25% under target | `deep81/code/sim81.py` lines 175–186 | 17% idle cash in a 70-name book; 3.5% against 2.7% for the twin in the 30-name D2 (UK 26%, thin caps); ASX D2 0.4% | None for the registered D2 on ASX. Any wider book needs the `fullinv` option of `sim82.py` |
| Raw traded-value weights are unusable as a size proxy | Reports 75 and 77 used "traded-value weights" as a proxy | One name carried 66% (France), 96% (Taiwan), 100% (Korea) of the weight in some months | Cap at 10 × the median, as here, or use caps |

## 9. What forward data would settle it

Years needed = (t wanted × swing ÷ true edge)².

| Question | Swing a year | If the true figure is | Years for t = 2 | Years for t = 3 |
|---|---|---|---|---|
| D2 beats the fund, ASX alone | 5.0 | +0.3 | over 1,000 | — |
| D2 beats the fund, 17 markets pooled | 2.2 | +0.3 | 215 | 480 |
| The screen adds to D2 (D2 minus twin), 17 markets | 2.1 | +0.3 / +1.0 | 196 / 18 | 440 / 40 |
| The screen adds on cap weights (list measure, W2) | 1.6 | +0.9 | 13 | 28 |
| **The screen separates losers on blunt weights (list measure, W1, no US)** | 2.3 | +1.9 | **6** | **13** |
| M3 beats the fund by the adopt bar (t 3), 20 markets pooled | about 2.2 (review 80) | +1.0 / +2.0 | — | 44 / 11 |

Plainly: **the forward record can confirm or kill the screen in about a decade. It cannot tell a +0.3 book from the index in a lifetime.** The adopt bar can only be met by a design whose true edge is near two points, and ten rounds have not produced one.

**Proposed measurement line** (full text `deep82/SPEC_avoid_list_measurement_line.md`; not registered by me; it is not a book and nothing in it can be bought): each month, in the 19 non-US sets and ASX, the return of the size-weighted 100 most traded with the bottom 30% by M3 removed, minus the return of the same list whole; W1 and W2; pooled; RM shown beside it. Kill if the pooled W1 mean is ≤ 0 after 60 months or t ≤ −2 at any December from month 13. "Confirmed" at t ≥ 3 from month 36. A confirmed reading keeps one line on the red-flag panel and changes no book.

**No shadow-line spec for a new book is offered, because nothing passed.** One reading rule for an existing line is recommended. The D2 line registered today (`AMENDMENT_shadow_CXL_D2.md`) carries 100 random-exclusion books. Its scorecard should lead with "D2 minus the median random-exclusion book", because a D2 lead over the fund will otherwise be read as the screen working when it is the large companies leading, as on ASX 2018–2026 (section 5.1). A no-exclusion twin would be cleaner still and costs one more book per size; that is the record keeper's call.

## 10. Honest limits

- No history here is fresh. The 2013–2026 window was unseen for the new RM score and for every cap-weighted, list-relative figure; it was not unseen for the M3 score, which was frozen with 2018–2026 in view.
- W1 is a made-up weighting. It is used because it exists for every market and year. Only W2 speaks to the index.
- Outside ASX a delisted share is paid out at its last price; failures are not marked. This understates what losers cost, so it works against the screen. Korea, Taiwan and China hold few dead companies before 2018.
- Cap data: ASX from ASIC share counts (sound; report 81). Other markets from vendor accounts, valid by the tracking test in about half (report 77); the UK has usable caps in 85 months only.
- ASX before 2018 is price-only (no dividends). Losers pay fewer dividends, so this also works against the screen, slightly.
- The repaired 70-name run is post-hoc. The void run is reported and counted.
- The closing-auction mechanics are from memory of public documents, not from a reading this session.

## 11. Trials and files

30 counted trials, N 1,729 → 1,759 (`out/trials_82.csv`): Stage A 16; Stage B 1; Stage C 6 (three add-ons on two base rules; pre-registered as 3, counted as 6 because both bases were run); buffer 1; lists against the fund 2; wide book 2 void + 2 repaired. Not counted: random-exclusion noise floor, regime and size-band splits of counted rules, the D2 twin, sell-delay and cash diagnostics, spread estimators.

| File | Content |
|---|---|
| `PREREG_82.md`, `PREREG_82b.md`, `out/prereg82_hash.txt` | Pre-registrations and hashes |
| `code/lib82.py`, `panel.py`, `rules.py` | The list-relative measure, weights, scores |
| `code/stageA.py`, `stageB.py`, `stageC.py`, `extras.py`, `lagdiag.py` | Avoid-list tests; `out/stageA.json`, `stageB.json`, `stageC.json`, `extras.json`, `exUSL.json` |
| `code/twin.py`, `d2w.py`, `d2wR.py`, `cashdiag.py`, `summ82.py`, `summd2w*.py` | Engine tests; `out/twin_*.json`, `d2w*_*.json`, `summ82.json`, `summd2w*.json`, `cashdiag.csv` |
| `code/sim82.py`, `stageE.py` | Engine copy with the buffer and full-investment options; `out/E_*.json` |
| `code/spread.py`, `spread2.py` | Execution evidence; `out/spread_bands.csv`, `spread_bands_mktadj.csv`, `spread_by_symbol.csv` |
| `code/noise0.py`, `out/noise0.csv`, `out/tv_outliers.csv` | Noise floor; traded-value outliers |
| `SPEC_avoid_list_measurement_line.md` | Proposed forward measurement line |
