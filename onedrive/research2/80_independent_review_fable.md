# 80. Independent review of the Big Wins programme

19 November 2026. Reviewer: research agent (Fable), acting as an independent senior reviewer.
Scope (owner, 19 Nov): **Big Wins only** — the stock-picking algorithm (H82 v1.3/v1.4, M3, E3, EI10I, the all-information engine, round 8), its paper records, and what could make it beat the index after costs and tax.
Paper research only. General information, not financial or tax advice. Nothing here places an order; the AI never places trades.
Work folder: `scratchpad/review80/` (`PREREG_80.md`, `bt80.py`, `bt80b.py`, `d5k.py`, results `bt80.json`, `bt80b.json`). The live paper record, ledger, frozen code and scheduled jobs were read, never written. Frozen code was loaded and patched in memory only.

**Tags.** [code] read in the code at the line given. [run] re-run by me today. [report] quoted from an earlier report. [judgement] my opinion. [memory] from my own knowledge, not re-checked today — verify before relying on it.

---

## 0. Answer first

**The headline conclusion survives: no Big Wins design has been shown to beat the index after costs and tax, and I could not make one do so.** But the review found one new data bug, three faults in how the live paper record is scored, a cost model that is clearly too harsh for this owner, and a validation rule that can never say "yes". Fixing these makes the picture more accurate. It does not produce a winner.

### 0.1 What is wrong (ranked by how much it matters)

| # | Finding | Effect | Evidence |
|---|---|---|---|
| 1 | **New data bug: about 12 real top-300 companies are missing from every ASX test on EODHD data.** The vendor renames a delisted company's symbol to `XXX_old` when the code is re-used (Coca-Cola Amatil = `CCL_old`, Altium = `ALU_old`, Sirtex, Village Roadshow, Mantra, Propertylink, Sundance, Centuria Metropolitan). Rule A4 keeps only symbols of exactly three characters, so they are dropped | With them restored, H82 on 2018–2026 falls from 8.35% / 9.32% a year after costs (A$25k / A$100k) to **6.94% / 8.93%**, against 8.78% for the index fund. H82's small lead at A$100k is gone (+0.5 → +0.15). Every ASX result built on the same bundle inherits the hole: report 70, M3 on ASX, EI10I on ASX, round 8 | §1.1 [run] |
| 2 | **The live paper comparator pays brokerage the owner does not pay.** The A200 and 40/60 comparator books are charged A$6.60 per fund on every purchase, including each A$500 monthly contribution (A$13.20 a month = 2.6% of each contribution for 40/60). The owner's real plan pays A$0 | Flatters H82's lifecycle book against the plan by roughly 1–2 points a year in the early years | §1.2 [code] |
| 3 | **The cost model is too harsh for this owner, in the other direction.** It charges IBKR's A$6.60 minimum and a half-spread on fills "at the close". Report 44 records that the owner's own platform charges A$0 on 550+ ASX shares, and the ASX close is a single-price auction with no spread to cross | Costs are overstated by about 0.5–0.9 point a year at A$25k–100k and more at A$5k. This is the largest reliable improvement available to Big Wins, and it is still not enough to create a lead | §1.3 [run] |
| 4 | **The A$5,000 book is not a test of anything.** Four shares, tracking error about 16 points a year. Contributions sit in cash at 0% until a rule spends them, mostly at the December review. Report 73 itself concluded "index fund until A$25,000". In the back-test engine a A$5,000 account that falls below A$4,000 can never buy again (target A$875 is under the A$1,000 minimum order) and sat in cash for eight years | The owner's real-size book measures cash drag and luck, not the engine | §1.4 [run] |
| 5 | **The adopt rule cannot be met.** It applies a deflated Sharpe ratio with 1,649 back-test trials to forward results that were frozen before the data existed. That correction is for picking the best of many back-tests; a pre-registered forward line has not been picked from anything. The report itself says the bar needs about 30 years at best and "a century" for a 1-point edge | The forward record is a "never" rule. It should be replaced by a bar that corrects only for the number of forward lines | §2.2 [judgement] |
| 6 | **"Twenty fresh markets, same answer" is weaker than it sounds.** Nineteen of the market sets cover the same nine years, 2018–2026, when a handful of giant companies drove most indices. They are not twenty independent tests, and the "equal weight structurally trails cap weight" finding is a fact about that period, not a law | Confidence that *no* design works should be "moderate", not "high". Confidence that *these* designs have no demonstrated edge stays high | §2.3 [judgement] |
| 7 | **Each round's pass/fail test had little power.** With tracking error of 6–10 points over nine years, a design with a true +2 point edge would pass the "ahead by 1 in two of three markets, none below −2" bar only about one time in three, before the extra luck tests | Seven failures in a row are real evidence against a large edge and only weak evidence against a small one. The pooled averages (−1 to +1.5 points a year) are the informative numbers | §2.1 [judgement] |
| 8 | **The "top five positions under 50% of profit" test contradicts the goal.** A strategy meant to catch big winners will always have concentrated profits, and the ratio explodes whenever net profit is small (380% in Thailand) | Drop it or replace it with "result survives removing the best share" | §2.4 |
| 9 | Smaller points: franking credits are not counted on either side; both books are sold and taxed at the end, which hides the index's advantage of never selling; the 17 Nov start will be churned at the 31 Dec review; listed investment companies count as "picks" (Argo is in the A$100k book) | Each under about 0.5 point; listed in §1.5 | [code] |

Checked and found sound [run / code]: report 74's corrected back-test reproduces to the last digit (8.3468% / 9.3204%); the ledger chain and amendments are dated before the data they govern; the report 78 power arithmetic is right; the split-volume and zero-traded-value bugs are real and fixed as described; Blue Sky (−94% in the 2018 book) is a real collapse, not a data error.

### 0.2 What is missing

1. **An honest cost and tax model for the owner's real set-up** (A$0 brokerage, closing-auction fills, franking, never-sell comparison). §3.1–3.2.
2. **A low-turnover "buy winners and keep them" form.** Every design sells most of the book each year (turnover 0.8–0.9). The one result that looked good (report 70 on 2016–2024) came from five shares bought early and held for years, and was rejected for exactly that. Nobody tested holding as the rule. §3.3.
3. **An accumulation form that fits A$500 a month:** each month's money buys the best-ranked share not yet held, nothing is sold except failures and tax losses. §3.3.
4. **Signals not yet tried that are specific to ASX and to small investors:** the run-up before franked dividends; share purchase plans on shares already held; director buying; analyst revisions (collection started today). All have low odds. §3.4.
5. **A decision rule in dollars.** At A$25,000 a +1 point edge is A$250 a year, and the price data costs about A$370 a year. §3.5.

### 0.3 What to do next for Big Wins, ranked

| Rank | Action | Expected value | Certainty |
|---|---|---|---|
| 1 | **Fix the `_old` bug** in the back-test bundle and in rule A4 (new amendment, effective at the next decision), and quote 6.9% / 8.9% for H82 wherever 8.3% / 9.3% appears. Re-run the ASX rows of reports 70, 76, 77 and 79 as corrections | No dollars; stops a wrong number being relied on | Certain |
| 2 | **Fix the paper scoring, without touching the frozen rules:** add comparator books at A$0 brokerage; add an after-tax line; report "kept, not sold" value beside "sold" value; flag the 31 Dec churn | No dollars; the record then answers the owner's real question | Certain |
| 3 | **Re-cost Big Wins for the owner's real broker.** Confirm the platform's share list, order types and whether orders can join the closing auction. Then run H82 and M3 forward with that cost model as an official parallel line | +0.5 to +0.9 point a year on any Big Wins book [run]; more at small sizes | High for the saving; it does not create a lead on its own |
| 4 | **Keep real money out of share-picking below about A$50,000 in the slice, and never in a 4- or 10-share book.** Retire or relabel the A$5,000 lifecycle book as "illustration only" | Avoids an expected loss of 1–2 points a year plus large luck | High |
| 5 | **Replace the adopt rule** (owner decision): pooled t ≥ 3 across forward lines, after-tax lead ≥ +1 point, ≥ 90th percentile of random books, more than half of markets ahead; no back-test trial count. Add a staged step: at 5 years, t ≥ 2 and a lead ≥ +1 allows a *capped* trial slice | Makes a "yes" possible in about 12–14 years instead of 30+ for a +2 edge, 5–7 years for the staged step | Certain as method; outcome most likely still "level" |
| 6 | **One pre-registered test of the hold-winners / accumulation form** on ASX 2001–2015 for design, then forward only (ASX after 2015 is spent). Bar: after tax and "kept" value, not less than the index fund by more than 0.5 point, with tracking error reported | Most likely "level with the index at lower tax and cost than H82". Its value is that it cannot lose much, and it matches what the owner asked for (own the winners) | Moderate |
| 7 | **Forward-only collection** of the four untried signal families (§3.4), as columns in the monthly snapshot. No back-test claims | Low odds each (my estimate 5–15% that any one yields a usable after-tax edge) | Low |
| 8 | **Stop spending on more history.** Eight rounds, 1,710 trials. More back-tests on the same nine years add trial count, not information | Saves effort | High |

**Honest odds [judgement].** Chance that a top-300 ASX share-picking rule of the kinds tested has a true edge of +1 point a year or more over the ASX index fund after realistic costs and tax: about 10–15%. Chance it beats the owner's 40/60 plan by that margin: under 5%, because that needs about +3 points over the local index. Fixing costs (items 2–3) moves Big Wins from "probably 1 point behind" to "probably level". Nothing found here moves it to "ahead".

(One line on what is out of scope: the levers outside share-picking — savings rate, super, the index plan itself — were reviewed in report 66 and are not covered here.)

---

## 1. Correctness

### 1.1 New bug: companies with `_old` symbols are dropped (survivorship hole)

**What.** `bigwins_forward/code/bw13_prep.py` line 58 (and the frozen copy `bw13_prep_v13_frozen.py` line 58, `deepdive/code/prep_dd.py` line 56, `bigwins_forward/code/rep13/prep.py` line 74, `allinfo/code/feat.py` line 114, `fwd_download.py` lines 29 and 41):

`ok = sym[(sym.Type == 'Common Stock') & (sym.Code.str.len() == 3)]   # A4`

EODHD's AU symbol list has 77 symbols ending `_old` (`data_foundation/out/eodhd/symbols.csv`; 68 with data ending 2018 or later in `qa/eodhd_symbol_table.csv`). They are delisted companies whose three-letter code was later given to another company: `CCL_old` Coca-Cola Amatil (to May 2021; `CCL` is now Cuscal), `ALU_old` Altium (to July 2024; `ALU` is now Alurion), `SRX_old` Sirtex, `VRL_old` Village Roadshow, `MTR_old` Mantra, `PLG_old` Propertylink, and others. Rule A4 ("code is exactly three characters", report 67) removes all of them. No report from 64 to 79 mentions `_old` for ASX (report 76 handles it for Thailand only).

**Who was missing from the top 300** [run, `review80/bt80b.py`]: CCL (Nov 2015–Jun 2021), ALU (Nov 2015–Sep 2024), SRX (to Nov 2018), VRL (to Aug 2019), MTR (to Jul 2018), SEA (to Dec 2019), PLG (May 2017–May 2019), CMA (Feb 2019–May 2020), plus four small ones before 2018. Renamed companies (`ORE_old`→AKE, `SCP_old`→RGN, `CYB_old`→VUK, `ASL_old`→PRN) are correctly merged by the existing duplicate test once admitted.

**Effect on H82, unseen B, 29 Dec 2017–13 Nov 2026** (frozen engine, v1.4 traded value, A7(b); pre-registered in `review80/PREREG_80.md` before the run; counted as one trial, N = 1,710):

| % a year | A$25k as reported (R74) | A$25k with `_old` restored | A$100k as reported | A$100k restored | Index fund |
|---|---|---|---|---|---|
| Before costs | 9.39 | 9.20 | 10.31 | 9.59 | — |
| **After costs** | **8.35** | **6.94** | **9.32** | **8.93** | 8.78 |
| After tax A | 6.45 | 6.45 | 6.99 | 6.79 | 6.84 |
| After tax B | 5.59 | 5.94 | 6.12 | 6.01 | 6.21 |
| Monthly excess, points a year (t) | +0.3 (0.07) | −1.1 (−0.27) | +0.9 (0.30) | +0.5 (0.17) | |

With the companies restored, the engine held CCL (both sizes), ALU, PLG and VRL (A$100k). The A$25k row moves by amounts that have little to do with the fix: a 10-share book changes path when any one purchase changes (before costs it moved 0.2; after costs 1.4). That is the programme's own "one-point noise floor" at work, and it is a reason not to read A$25k results at all.

**Reading.** The verdict "not shown to beat the index" stands and is a little firmer. The bug did not flatter the engine in one obvious direction; it simply made the tested universe wrong.

**Knock-on.** `improve5/code/mk_asx5tr.py` builds the ASX pack for rounds 5–8 from `deepdive/data/bundle_eod.pkl`, which has the same filter. So M3 on ASX (report 76 erratum: +1.3 / −0.5), EI10I and CW on ASX (report 77), and the round-8 ASX holdout (report 79, whose estimate files were requested for "every company among the 100 most traded", taken from the same pack) all ran without these companies. I did not re-run them.

**Live record.** `_old` companies are delisted, so no current purchase is affected. One exposure remains: if a held company delists and its code is re-used, the vendor will move its history to `XXX_old` and the book would start reading another company's prices under the old code. Rule A8 (a 200-day gap splits a code) partly covers it. Worth a written rule.

### 1.2 The paper comparator is charged brokerage the owner does not pay

`paper_lib.py` line 62 defines `brokerage(v) = max(6.60, 0.00088 * v)`. Lines 359–361 (`run_cmp_day`) apply it to every comparator purchase, once per fund:

`amt = p['amount'] * w; net = (amt - brokerage(amt)) / 1.0003`

Line 372 queues each monthly contribution as a new comparator purchase. So the 40/60 lifecycle comparator pays A$6.60 on A$200 of A200 and A$6.60 on A$300 of BGBL every month: A$158 a year on an account of A$5,000–11,000 in year one. The amendment says so openly ("one brokerage per fund"). Report 44 line 52 records that the owner's platform charges A$0 on all ASX ETFs. The comparator is therefore not the owner's plan; it is the owner's plan at a broker the owner does not use.

`COST_ALT.md` (today's re-scoring) makes the mirror-image mistake: it sets the H82 books to A$3 and A$0 brokerage and compares them with a comparator still paying A$6.60. Its "+0.58% vs A200" for the A$5k book at A$0 would be about +0.45% against a comparator also at A$0.

**Fix (no frozen rule changes):** add comparator books `CMP_*_b0` at A$0 brokerage and quote them as the primary benchmark for the lifecycle size.

### 1.3 Costs are overstated for this owner

Brokerage stress on the same frozen run (my re-run; `_old` not restored so the rows compare with report 74) [run, `review80/bt80.json`]:

| H82, 2018–2026 | Trades | Total cost paid | After costs, % a year | Index fund |
|---|---|---|---|---|
| A$25k, max(A$6.60, 0.088%) | 202 | A$2,449 | 8.35 | 8.78 |
| A$25k, A$3 flat | 204 | A$1,670 | 8.65 | 8.80 |
| A$25k, A$0 | 205 | A$1,021 | 9.25 | 8.80 |
| A$100k, max(A$6.60, 0.088%) | 467 | A$7,573 | 9.32 | 8.78 |
| A$100k, A$3 flat | 467 | A$5,785 | 9.44 | 8.80 |
| A$100k, A$0 | 465 | A$4,368 | 9.89 | 8.80 |

- Brokerage alone is about A$160 a year at A$25k (about 0.5 point) and A$360 a year at A$100k (about 0.3 point). The return column moves a little more than that because of path noise.
- What remains at A$0 is the assumed half-spread (0.10% for the 100 most-traded, 0.25% for ranks 101–300; rule E2), about 0.3–0.4 point a year.
- Rule D1/D2 fills at the close. The ASX close is set in a single-price auction; an order that takes part in it trades at the closing price with no spread to cross [memory]. Report 76 rule R1 already says "closing auction". If the owner's broker lets orders join it, the half-spread charge is mostly not a real cost. If the broker instead batches or delays orders, the real cost could be higher than modelled. **This must be checked with the broker; it is the single most valuable fact to establish.**
- After-tax caution: at A$25k the after-tax figure went *down* at A$0 brokerage (6.45 → 6.23) while after-costs went up. That is path noise again, not an effect.

Taken together: realistic friction for this owner is probably 0.1–0.5 point a year, not the 1.0 the back-tests charge. With `_old` restored that puts H82 at A$100k at roughly 9.2–9.5% against 8.8% before tax, and about level after tax. Better, and still not an edge (t under 0.5).

### 1.4 The A$5,000 lifecycle book

- Four shares. My A$5,000 run of the frozen engine shows tracking error 16 points a year [run].
- In that run the Dec 2017 list was Elders, Abacus, Blue Sky and one more; Blue Sky lost 94%; NAV fell to A$3,499; target per share became A$875; rule D2 needs A$1,000; the account never bought again and held cash from January 2019 to 2026 [run, `review80/d5k.py`]. The live lifecycle book is protected from this by its monthly A$500, but the dead end exists in the rules.
- In the live book, contributions are cash until C7/C8/C9 spend them; top-ups need a gap of A$1,000 and happen only at December reviews. In year one roughly a third of the account will be idle cash at 0%. The amendment says this is "reported, not fixed".
- Report 73 §0 item 5 and report 75 item 9 both concluded: below A$25,000, index fund only.

The book is honest about what the rules do. It should not be read as "Big Wins at the owner's size"; the designs that were actually tested at that size start in the index fund.

### 1.5 Smaller points

| Point | Where | Effect |
|---|---|---|
| Franking credits are not counted for the engine or the comparator (rule F3: 32% × dividends; J3 the same) | 67 §F, §J | Neutral against A200 to a first approximation. H82's holdings (banks, insurers, staples) are probably more fully franked than the index, so the engine is understated by perhaps 0.1–0.3 point. Against the 40/60 plan the omission understates any ASX share book by about 0.5 point a year. Report 70's patched engine has a franking switch; use it in formal readings |
| Both sides are liquidated at the end (G1, J3) | 67 §G, §J | The owner never sells the index fund. On a "kept" basis the fund's after-tax return is about 7.4% (8.78 less tax on distributions), not 6.84%, while the engine still pays capital gains tax every year. The convention hides about 0.5 point a year of the index's advantage, and the gap grows with the horizon |
| Start on 16 Nov, full review on 31 Dec | AMENDMENT_start_now §2 | Rule C5 will sell every holding not on the December list after six weeks: an extra round trip (about 0.3–0.7% of the book) and short-term gains. Flag it in the scorecard so it is not read as the engine's normal cost |
| Listed investment companies and trusts are "common stock" (A4) | Scorecard: Argo in H82_100k | A low-volatility score will always like an LIC. It is a closet index holding at a fee; harmless, but it is not a pick |
| Failures after April 2020 are paid out at the full last price (C1; no failure records after that date) | 67 §C1 | Flatters engine and random controls alike; small in the top 300 |
| Dividends missing for some pre-2018 delistings in the vendor file (DUE, TTS show none) | `symbol_stats.csv` | Outside the 2018+ window used for claims; no action |
| Intraday job every two hours | AMENDMENT_intraday_look | Makes no decision; no research value under close-only rules. Harmless; costs credits |
| 405 paper books | Ledger entry "paper account opened" | Fine as controls. Only the pre-named lines should ever be read formally |

---

## 2. Method

### 2.1 Pre-registration, one look, random controls: right in kind, and the bars had low power

Hashing rules before computing returns, one look per design, random portfolios through the same machinery, and blind replication are all good practice and were done properly as far as I could check. The weak spot is the pass/fail bar used in rounds 1–8.

Rough arithmetic [judgement]: nine years, tracking error 6 points (A$100k) to 10 points (A$25k), so the standard error of a market's annual lead is about 2.0 and 3.4 points. For a design with a true +2 point edge, "lead ≥ +1 at both sizes" happens in about half of markets; "two of three markets and no cell below −2" in about 35% of looks; adding "≥ 90th percentile of random in both markets" takes it to perhaps 15–20%. For a design with no edge the pass rate is about 3–5%.

So a fail is roughly a 0.85 likelihood ratio against a +2 edge. Seven or eight fails multiply to about 0.3. That is real evidence, and it is not "high confidence that no price-and-volume design can work". The pooled leads are the better summary: −4.8, −1.5, −0.6 (report 73), −1.5 and −0.2 (report 75), +1.3 / +1.6 for M3 on five fresh markets (report 76), +0.1 / +0.6 for EI10I (report 77), −1.4 / −1.5 on ASX (report 79). The centre is about −1 to 0 with a spread of about ±1.5.

### 2.2 Deflated Sharpe with N ≈ 1,700 on forward data is the wrong tool

On back-tests, counting every trial and deflating is correct and, if anything, generous to nobody: nothing came near the bar, so the exact N never mattered (reports 59 and 62 showed this at N = 400 and 1,000).

On the forward record it is a category error. The deflated Sharpe ratio answers "how good must the best of N tried strategies look before I believe it?". A forward line was frozen and hashed before its data existed; nothing is being selected after the fact. The only multiplicity is the number of forward lines that could trigger adoption — about a dozen (three designs × two sizes pooled, H82 at two sizes, M3 and E3 shadows). A Bonferroni correction for twelve one-sided tests at 5% needs t ≈ 2.6. The existing "t ≥ 3" condition already covers that with room to spare.

Report 78 states that the DSR condition is "the binding condition" and needs t ≈ 5: 27–32 years for a +2 edge in the best line, about a century for +1. The other four conditions (t ≥ 3, lead ≥ +1 after tax, ≥ 90th percentile of random, more than half the markets ahead) are a sound and strict bar on their own: about 12–14 years for a +2 edge in EI10I/CW at A$100k (report 78 table 1.3, which I re-derived: ((1.96 + 0.84) × 1.9 ÷ 2)² = 7.1 years at t ≥ 1.96; 14 at t ≥ 3).

Prior scepticism from eight failed rounds is legitimate. It belongs in the size of the first real-money slice, not in a significance bar that cannot be reached in a working lifetime.

**Two further problems with the adopt rule:**
- It requires **both** A$25k and A$100k. The A$25k books are far noisier (pooled tracking error 2.6–4.7 against 1.8–3.7), so the smaller book decides. A design that only works with 30 shares is a legitimate finding; the rule should allow adoption "at A$100k and above only".
- **CW has no picking in it.** If CW "passes", the finding is that a self-built cap-weighted book tracks its fund, not that Big Wins works. It should be a control, not an adoptable design.

**Stop rule.** "Pooled t ≤ −2 from 13 months" is fine. "After-tax lead ≤ −1 from 60 months" will stop a design with no edge 12–30% of the time and a +1 design up to one time in six (standard error at five years 0.85–2.1 points). Acceptable for a retail record, but say so.

### 2.3 One period, many markets

Report 73: fresh sets were 2018–2026 except US 2001–2013. Reports 75–77: all 29 Dec 2017–30 Oct 2026. Report 78 measures the correlation of monthly leads across markets (0.05–0.16) and correctly says 10–14 markets act like 3–7. The summaries of reports 73, 75 and 76 do not apply the same discount when they say "twenty fresh market sets … the same answer each time".

Two consequences:
- **"Equal weight trails cap weight by about 2 points" is a 2018–2026 fact.** Over most longer histories equal-weighted large-company portfolios have matched or beaten cap-weighted ones [memory]. The last decade's dominance of a few giants (report 75 item 6 names Korea and Taiwan; report 73 names US large) is the regime in which that reverses. The diagnosis in report 77 is right for the window and should not be written as structural.
- **M3 was chosen on 18 market-sets of the same period it was then "freshly" tested on.** Fresh companies, same years. Momentum's global return in 2018–2026 is common to both. The +1.3 / +1.6 on five fresh markets is therefore partly in-sample in time. The only clean test is the forward record, which is the conclusion report 77 reached.

### 2.4 The profit-concentration test

PREREG_76's "top five positions under 50% of profit" failed M3 at 380% and 205%. The ratio is profit of five positions ÷ net profit, and net profit was small, so it explodes. More basically, the owner's stated aim (briefing §1.1: "stocks like NEXTDC are the ones I don't want to miss") is a concentrated-profit aim; in any share portfolio a few names make most of the money. A better test of fragility is the one report 76 already ran informally: does the lead survive deleting the best share, or changing one purchase? (At A$25k it did not: China +2.6 → −1.8.)

### 2.5 Is the validation too strict or too lenient for a retail decision?

- **Back-test stage: about right in conclusion, too binary in form.** Nothing passed; nothing was close on a pooled basis; the pre-registration discipline is the reason these results can be trusted at all.
- **Forward stage: too strict to ever say yes** (§2.2), and at the same time too loose on what is scored (before tax, comparator costs wrong, §1.2).
- **Missing entirely: the economic test.** See §3.5.

---

## 3. What is missing

### 3.1 Execution and brokerage

- Establish the real cost at the owner's broker: which shares are A$0, whether limit orders can rest in the closing auction, minimum order size, whether shares are held under the owner's own HIN or in custody (report 44 line 52 says custodial; that matters for share purchase plans and corporate actions).
- Run an official parallel line "H82 at owner's-broker costs" and the same for M3, with matching comparators. This is information, not a rule change.
- At A$0 brokerage the A$2,500 minimum position (rule C3) and A$1,000 minimum order (D2) lose their reason. Smaller positions mean more names and lower tracking error at small sizes. That is a rule change and needs its own card and clock.

### 3.2 Tax inside Big Wins

- **Turnover is the tax problem.** H82 sells 80–85% of the book each year. The 12-month deferral (C6) earns the discount under current law; under the post-1 July 2027 rules used as regime B/AN in the reports (indexation, no discount; I did not re-verify the law) the cost of yearly selling rises: H82 A$100k is 6.99% under A and 6.12% under B, the index 6.84% and 6.21%.
- **Count franking** in every formal reading (§1.5).
- **Report "kept" value as well as "sold" value** (§1.5). On the owner's real horizon the index fund is never sold.
- **Parcel choice.** Rule D5 sells oldest first. For trims, selling the highest-cost parcel held over 12 months first is free money in timing terms (report 66 item 7 found the same for the index plan). Small.
- **Loss harvesting** adds about 0.5 point to a high-turnover engine and nothing to a low-turnover one (report 75 item 5). I agree with that finding; an investor with no other gains only defers.
- A lower-taxed holder for the slice would change the arithmetic; outside this review.

### 3.3 Portfolio construction and holding period: the untested "keep the winners" form

What was tried: equal weight, cap weight with tilts, index-fund core plus satellite, 10–50 names, yearly/monthly/weekly review, hold bands, sell rules. All of them *re-rank and replace*.

What was not tried: **buy on the signal, then hold.** Reasons to think it is the better form for this owner [judgement]:
- Momentum's information lasts about a year. After that, selling a holding is a cost and a tax event with no expected benefit. Report 64 found a keep-band "halved turnover at no loss" in development and it was not pursued (report 72 table row 7).
- A book that never sells winners drifts towards cap weight by itself, because winners grow. That removes most of the equal-weight gap of §2.3 without needing share counts.
- Tax falls to dividends plus occasional loss sales.
- It is the direct form of the owner's goal: the shares that become NEXTDC are kept.
- Report 70's only strong result (9.5% against 4.6% on 2016–May 2024) had this shape by accident and was rejected for concentration.

**Accumulation variant for A$500 a month:** each month, the new money buys the best-ranked eligible share not already held (or tops up the smallest holding); nothing is sold except payouts and tax-loss sales in June. After five years that is about 40–60 holdings. At A$0 brokerage it costs the spread once.

**Honest expectation:** index-like return with 5–8 points of tracking error at first, falling as names accumulate; an entry edge worth perhaps +0.1 to +0.5 point a year on the whole book; cost and tax drag near the index fund's. Most likely "level with the index". Its merit is that the expected shortfall is close to nil, where H82's is 1–2 points. It cannot be validated on ASX history after 2015 (spent), so: design on 2001–2015, one pre-registered description, then forward only. Count it as trials.

### 3.4 Signals and data not yet tried

Everything on the standard list has been run: momentum in six forms, low volatility, 52-week high, reversal, seasonality, beta, lottery, value, quality, accruals, issuance, short interest level, commodity drivers, earnings surprise, tax-loss June, index changes, spin-offs, LIC discounts. I have nothing to add there. What remains is specific to ASX and to small accounts:

| Idea | Why it might exist | Why it probably will not pay | Data | My odds of a usable after-tax edge |
|---|---|---|---|---|
| **Run-up before franked dividends** (buy 30–45 days before the expected ex-date, sell before or after) | Demand for franking credits from low-tax holders; documented in Australian studies [memory] | Short holding means full-rate tax on gains; 45-day rule (small holders under A$5,000 of credits a year are exempt [memory]); effect may have faded | EODHD dividends and ex-dates are already held for 2018+; expected dates can be predicted from last year's | 10–15% |
| **Share purchase plans on shares already held** | A small holder can buy up to A$30,000 at a discount when the market price is above the offer; funds cannot | Only helps on shares already owned at the record date; scale-backs; needs shares in the owner's own name; not a selection signal | Forward only (report 59: issue prices not obtainable for history) | 50% that it adds something, and the something is about 0.1–0.3 point a year |
| **Director buying** (Appendix 3Y) | Best-supported "informed trader" signal in small companies | Mostly outside the top 300; needs ASX announcements, which may not be fetched automatically | Forward, by hand | 5–10% |
| **Analyst revisions** | Strongest published non-price signal | Vendor's ASX estimates are poor (report 79: median miss 40%, 22% wrong sign) | `est_snapshot.py` registered today; forward only | 10% |
| **Change in short interest** | Level failed; change never tested (report 72 row 18) | Report 70 found short data added nothing | ASIC files held | 5% |

None of these justifies delaying the fixes in §0.3. All are cheap to log.

### 3.5 The decision in dollars

| Slice | A true +1 point edge is worth | A true +2 point edge | Price data cost |
|---|---|---|---|
| A$5,000 | A$50 a year | A$100 | about A$370 a year (report 68) |
| A$25,000 | A$250 | A$500 | same |
| A$100,000 | A$1,000 | A$2,000 | same |

Below about A$40,000 in the slice, even a real +1 point edge does not pay for the data that the monthly process needs. H82 itself needs fresh data only at the December review and when a vacancy opens, so a real-money version could run on one or two paid months a year; the continuous subscription is a cost of the *research record*, not of the strategy. This should be written into any future real-money proposal, and it is another reason for §0.3 item 4.

### 3.6 Other objectives

- **Risk-adjusted.** H82's worst fall was −25.8% against −26.8% for the index (my run): no drawdown benefit to offset its tracking error. No design in rounds 1–8 was built for lower risk, and the owner's stated objective is growth (briefing §1.1), so I do not recommend reopening this.
- **"Catch the big winners" as the objective itself.** Report 72's finding stands: predicting +50% winners selects the most dangerous shares. The reliable way to hold every big winner is to hold the whole market; the next most reliable is §3.3 (never sell what is working).

---

## 4. The best realistic plan for Big Wins

1. **Correct the record** (§0.3 items 1–2): `_old`, comparator costs, after-tax and "kept" lines, franking. A week of work, no new claims.
2. **Find out the real trading cost** at the owner's broker (item 3) and run the parallel line.
3. **Keep H82, M3 and the multi-market lines running unchanged** as the hindsight-free record. They are cheap and they are the only clean evidence.
4. **Change the adopt rule** (item 5) so that a real edge could be recognised in 5–14 years.
5. **Add one new design only: hold-winners / accumulation** (item 6), pre-registered, forward.
6. **Log the four untried signals** (item 7) as snapshot columns.
7. **No real money in Big Wins** until a forward line meets the revised bar, and then only in a slice of A$50,000 or more with 25–30 names or more.

What I would tell the owner plainly: the search was not missing an obvious signal. It was missing accuracy about costs, one set of companies, and a rule that could ever say yes. After fixing those, Big Wins looks like a portfolio that roughly matches the ASX index with extra noise. The form most likely to serve the wish behind it — owning the big winners and not selling them — has not been tested, and its realistic best case is "level with the index, with the winners visibly yours".

---

## 5. Limits of this review

- I read the summaries of reports 61–79 in full and the bodies in part; reports 01–60 through the briefing only.
- I re-ran one back-test (H82 unseen B) in four variants. I did not re-run M3, E3, EI10I, report 70 or report 79, and did not open the multi-market engines beyond `improve/code/sim.py` lines 1–140 and the pack builder for ASX.
- The `_old` re-run admits every `XXX_old` common stock; I did not check each of the 43 admitted columns by hand. CMA_old (renamed COF) was not caught by the duplicate test and may be counted twice for 16 months in 2019–2020.
- Statements about the closing auction, zero-brokerage conditions, the franking small-holder exemption and long-run equal-weight returns are from my own knowledge and are tagged [memory]. The post-July-2027 tax rules are taken from the earlier reports as given.
- Power figures in §2.1 are rough normal approximations, not simulations.
- Trial count after this review: **1,710** (one corrected re-run; the brokerage stresses and the A$5,000 diagnostic are cost and size stresses under the programme's convention).

## 6. Files

| What | Path |
|---|---|
| Pre-run note and hash | `scratchpad/review80/PREREG_80.md`, `prereg80_hash.txt` |
| Brokerage stress (baseline reproduces report 74) | `scratchpad/review80/bt80.py`, `bt80.json` |
| `_old` correction run | `scratchpad/review80/bt80b.py`, `bt80b.json` |
| A$5,000 diagnostic | `scratchpad/review80/d5k.py` |
| Filter at fault | `scratchpad/bigwins_forward/code/bw13_prep.py:58`, `deepdive/code/prep_dd.py:56` |
| Comparator brokerage | `scratchpad/bigwins_forward/code/paper_lib.py:62, 359–361, 372` |
| Vendor symbol table | `scratchpad/data_foundation/out/eodhd/symbols.csv`, `qa/eodhd_symbol_table.csv` |
| Adopt rule | `68_forward_record/AMENDMENT_forward_multimarket.md` §8 |
