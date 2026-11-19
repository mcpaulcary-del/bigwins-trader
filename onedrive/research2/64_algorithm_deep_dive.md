# Report 64 — Algorithm deep dive: the Big Wins engine on clean data

16 November 2026. Author: research agent (Fable). Code, logs and frozen files: `scratchpad/deepdive/` (`code/`, `out/`, `PREREG_64.md`).
Pre-registration SHA-256 `665cffc3…23d8` (hashed before any phase-1 return was computed). Frozen rules v1.2 SHA-256 `895b8973…ada6a`.
Nothing here touches real money. Research and paper cards only.

## 0. Verdict in plain English

1. **No design beats the index on data it never saw, with any confidence.** Three candidates each got their one counted look on two unseen data sets (the fixed price panel 2016–May 2024, and licensed EODHD total-return data 2018–13 Nov 2026). All three failed the pre-declared bar. None is even close to it.
2. **The existing engine (H82, rules v1.1) is still the best thing found, and it is level with the index, not ahead of it.** On the licensed total-return data, 2018 to Nov 2026, it made 9.6–9.7% a year after costs against 8.8% for the A200/VAS comparator, and 7.2–7.5% against 6.8% after tax. That lead of about half a point to one point a year has a t-statistic of 0.3–0.4 and sits inside the one-point noise floor. Moving the review month turns it into a deficit in 4 of 8 cases. Honest reading: **no measurable difference from the index** — about a 2-in-3 chance the true edge is above zero, and no chance of proving it either way on paper within a decade.
3. **Every "improvement" again lost on unseen data.** The new tranche design gained 1.1 points a year in development and lost 1.5–3.8 points a year to the plain engine afterwards. H88 (frog-in-the-pan) and H90 (recency of the 52-week high), which had never been looked at after 2015, both failed. A development gain has now reversed on unseen data in every round of this programme (reports 53, 55, 59, 60, 62 and this one).
4. **Clean data changed almost nothing in the old conclusions** (section 2). The earlier price-only work was sound in its verdicts. Two things did change: dividends take about one point a year off the engine relative to the index (the engine's shares yield 3.1%, the index 4.1%), and the June tax-loss idea (H100) got weaker: the three new Junes 2024–2026, never seen before, averaged −0.3% against the index (1 win in 3).
5. **What goes to paper:** H82 v1.1 unchanged, now scored in total return under rules v1.2; H100 in June 2027 with report 63's guard rails; H101 as a tracking line. **What is retired:** H88, H90, the tranche form, six new signals, five construction levers.
6. **The owner's index plan stays the right place for the money.** Over the same 2018–Nov 2026 window, A$5,000 + A$500 a month: owner's 40/60 plan A$97,300 after a notional sale; A200 alone A$83,300; the engine A$87,200 (it started with four shares; random portfolios through the same machine ranged A$50,700–A$93,500, so the engine's figure is within luck).

## 1. What was done, and the rules it was done under

| Phase | Work | Counted trials |
|---|---|---|
| 0 | Re-ran the frozen rules (H82 v1.1, H88, H90, H100, H101) on the fixed panel (`panel_v2`) and on EODHD. H88/H90 were run on 2001–2015 only at this stage | 0 (replications) |
| 1A | Eight signals tested for information beyond the H80 score (2001–2015 only) | 8 |
| 1B | Scores compared on a start-month-robust measure (8 accounts) | 0 (existing specifications) |
| 1C | Six construction levers, each alone against the incumbent | 6 |
| 2 | One look each for H88, H90 and the new candidate F1, on both unseen sets | 3 |
| | **Library count for the deflated Sharpe ratio: 385 + 14 + 3 = 402** | |

Budget declared up front: at most 20 development trials and 4 looks; 14 and 3 were used. Every run is in `deepdive/out/trials_dd.csv`; the looks are in `out/holdout_looks_64.txt`.

**Data.**
- Development: `panel_v2` (survivorship-inclusive, price-only, renames and calendar fixed), 29 Dec 2000–31 Dec 2015, against the XJO price index. The 196 stale XJO days were replaced by EODHD's AXJO values (29 Dec 2000 = 3,206.2).
- Unseen A: `panel_v2`, 31 Dec 2015–31 May 2024, price-only.
- Unseen B: EODHD, 29 Dec 2017–13 Nov 2026, dividends paid as cash on the ex-date and taxed at 32%; comparator built from issuer figures (Vanguard VAS NAV + issuer distributions, then Betashares' own A200 total-return index from 7 May 2018), as addendum 3 requires.
- EODHD preparation found two things a user must handle: 327 renamed companies carried twice under old and new codes (for example WPL and WDS), and 113 codes re-used by a different company. Both are fixed in `code/prep_dd.py` and written into rules v1.2 (I3, I4).

**Order of work that protects the unseen years.** The phase-1 designs were pre-registered and hashed after seeing H88/H90 on 2001–2015 only. No H88/H90 figure after 2015 existed anywhere until phase 2. Code and development results were hashed (`out/freeze_before_unseen_hashes.txt`) before the looks.

**Literature.** Full texts reachable: Daniel & Moskowitz, *Momentum Crashes* (NBER w20439) and Hou, Xue & Zhang, *Replicating Anomalies* (NBER w23394); both read. SSRN returned HTTP 403 for every paper tried, so Da–Gurun–Warachka (frog-in-the-pan), Bhootra–Hur (recency), George–Hwang (52-week high), Barroso–Santa-Clara, Blitz–Huij–Martens (residual momentum), Novy-Marx (intermediate momentum) and Hoffstein (rebalance timing luck) are used **from memory [unverified]**. What the two read papers contribute: momentum's crashes come from the short (loser) side after market falls, which a long-only book does not hold, so no crash filter was designed; and 64% of 447 published anomalies fail once tiny companies are removed, 85% at t ≥ 3 — which is the base rate to hold in mind for everything below.

## 2. Phase 0 — how much the old conclusions change on clean data

### 2.1 Engine H82 (rules v1.1), A$25k / A$100k, % a year after costs

| Period and data | Earlier report | This report | Index | Change |
|---|---|---|---|---|
| Development 2001–2015, price-only | 9.4 / 6.3 (R55) | **9.7 / 6.3**; excess t 2.4 / 1.4; random pct 100 / 98.5; DSR 0.57 / 0.20 | 3.3 (was 3.2) | None of substance |
| Development, June start | 7.2 / 7.5 (R56) | 7.1 / 7.6 | 3.0 | None |
| Unseen 2016–May 2024, price-only | 1.6 / 4.0 (R55) | **1.6 / 4.0**; after tax A 1.1 / 3.1; random pct 36 / 62 | 4.6 (3.9 after tax) | Identical to a tenth |
| Whole 2001–May 2024 | — | 7.8 / 5.9; t 2.1 / 1.3 | 3.7 | — |
| 2018–May 2024 overlap, panel_v2, price-only | — | 2.0 / 4.2 | 3.8 | — |
| 2018–May 2024 overlap, EODHD, price-only | — | 4.2 / 4.8 | 3.8 | See 2.2 |
| 2018–May 2024 overlap, EODHD, total return | — | 6.6 / 8.3 | 8.1 | Dividends added |
| **2018–13 Nov 2026, EODHD, total return** | — (R55 survivors-only, price: 15.3 / 11.0 for Jun 2024–Nov 2026) | **9.6 / 9.7**; after tax A 7.2 / 7.5, B 6.6 / 6.7; excess +1.4 / +1.3 (t 0.3 / 0.4); random pct 87 / 92; DSR 0.08 / 0.10 | 8.8; after tax 6.8 / 6.2 | New |
| 2018–13 Nov 2026, EODHD, price-only | — | 6.4 / 6.3 | 4.6 | Price-only flatters by ~1 pt |

What changed with dividends: the engine's book paid 3.1% a year in dividends, the index 4.1%. Price-only comparisons therefore overstated the engine's lead by about one point a year. The earlier estimate (R53: engine 7.1–8.3% against index 8.9% with estimated dividends) pointed the right way.

### 2.2 Reconciling the two sources, 2018–May 2024

At A$100,000 the two sources give the same answer: 4.2% (panel_v2) and 4.8% (EODHD) a year, month-by-month return correlation 0.98, and 23–27 of the 26–30 January holdings identical each year. At A$25,000 they differ by 2.2 points a year (2.0% against 4.2%) from a handful of different picks out of ten — a direct measurement of how little a ten-share result means. The 0.6-point gap at A$100k comes from different split/rename handling in a few names and is inside the noise floor.

### 2.3 H88, H90 (development only at this stage), H100, H101

| Card | Earlier | This report | Change |
|---|---|---|---|
| H88 dev, Dec start | 8.4 / 9.5 (R56) | 8.3 / 9.2; excess t 2.0 / 2.7 | None |
| H88 dev, June start | 6.6 / 6.1 | 6.4 / 7.2 (engine 7.1 / 7.6) | Still not confirmed |
| H90 dev, Dec start | 5.0 / 8.5 | 4.8 / 7.8 | None |
| H90 dev, June start | — | 10.0 / 8.2 | Start-month luck of 5 points at A$25k |
| H100 dev 2004–2015 (12 Junes) | +2.5%, t 1.1 (R59); +2.4% (R63) | **+2.6%, t 1.2**, 8 of 12 | Replicated |
| H100 unseen 2016–2023 (8 Junes) | +6.0%, t 2.2 | **+5.9%, t 2.3**, 5 of 8 | Replicated |
| H100 2018–2023, EODHD total return | — | +6.2% (panel_v2 same years +5.7%) | Sources agree |
| **H100 new Junes 2024, 2025, 2026 (EODHD; never seen)** | — | **−8.2%, +11.6%, −4.5%: mean −0.3%, 1 of 3**; against the small-cap universe +1.8% | **Weaker** |
| H100 all 23 Junes 2004–2026 | — | +3.5%, t 2.1, 15 of 23; against the universe +3.0%, t 3.0 | Alive, thin |
| H101 (N4 form) dev | +13.5%, t 1.6 (R59); +12.4% (R63) | +9.5%, t 1.7, 11 of 15 | Lower; rename fix |
| H101 unseen Dec 2016–Dec 2022 | +3.7% / +5.6% | +3.0%, 4 of 7; median pick −5.9% | Not promising, as R63 said |
| H101 EODHD total return, Dec 2017–Dec 2024 (8 cohorts) | — | +4.7%, t 1.2; median pick −4.7% | Mean lives in a few winners |

(H100 figures are net of modelled costs of about 1.2–1.3% a side, minus the index over the same five weeks. H101 here uses a simplified cost and universe reading; it is a consistency check, not a second replication.)

**Bottom line of phase 0:** fixed renames, fixed calendar, a corrected index start and licensed prices move the headline figures by a few tenths of a point. The verdicts of reports 51–63 stand.

## 3. Phase 1 — design on development data only

### 3.1 Which signals carry information beyond the H80 score (stage A)

Each month from Dec 2000 to Dec 2014, the next-12-month return of the top 300 was regressed on the H80 score's rank and one extra signal's rank. The gate, set in advance: t ≥ 2.0 and the same sign in both halves.

| Signal | Extra return, top vs bottom rank (pts/yr) | t | First half / second half | Passes |
|---|---|---|---|---|
| H80 score itself (for scale) | +18 to +21 | 1.6–2.6 | — | — |
| Frog-in-the-pan (X_FIP, the H88 addition) | −3.2 | −1.7 | −4.1 / −2.4 | No — wrong sign |
| Recency of 52-week high (H90) | +1.1 | 0.3 | +4.7 / −2.5 | No |
| Residual momentum | +2.0 | 0.3 | +14.2 / −9.0 | No |
| Momentum ÷ volatility | +0.9 | 0.1 | +8.9 / −7.2 | No |
| Momentum months 12 to 7 | +4.5 | 1.2 | +4.1 / +4.9 | No |
| Low beta | −0.8 | −0.1 | −18.9 / +15.5 | No |
| Share of up months | +4.7 | 1.2 | +6.9 / +2.4 | No |
| Listed under two years (flag) | −4.0 | −1.3 | −4.7 / −3.4 | No |

**Nothing passes.** Once the four H80 parts are in, no other price signal adds anything reliable. H88's extra signal has a negative slope: its good development back-test at A$100,000 was a path effect, not information. Recency (H90) ranks well alone (positive in 92% of months) only because it repeats what "close to the 52-week high" already says.

Dilution and the LIC premium were not re-tested: share counts start in 2010 and LIC data in 2017, so neither can be developed on 2001–2015; report 62 already showed the dilution exclusion does nothing for this engine (its picks are rarely heavy issuers). They stay panel flags.

### 3.2 Scores on the robust measure (stage B)

A design is now judged on eight development accounts (two sizes × four start months), after tax B, not on the December path alone. This is the direct fix for the "worked in December, not in June" problem of report 56.

| Score | Robust score (% a year after tax B) | A$25k / A$100k | Accounts ahead of v1.1 (of 8) | Outcome |
|---|---|---|---|---|
| v1.1 (H82) | 5.23 | 5.28 / 5.19 | — | Incumbent |
| H88 | 5.13 | 5.67 / 4.59 | 3 | Not adopted |
| H90 | 3.79 | 2.94 / 4.63 | 3 | Not adopted |

On the December path alone H88 would have looked 99th-percentile against noise. Averaged over four start months it is behind v1.1. The spread between start months for v1.1 is 3.7 points a year at A$25k and 2.0 at A$100k — larger than any "improvement" this programme has ever claimed.

### 3.3 Construction levers (stage C), each alone against v1.1

| Lever | Robust score | Change | A$25k / A$100k change | Accounts ahead | Adopted |
|---|---|---|---|---|---|
| C1 Four quarterly tranches (3–8 shares each) | 6.31 | +1.08 | +1.17 / +0.98 | 6 | **Yes** |
| C2 Inverse-volatility weights | 5.01 | −0.22 | −0.14 / −0.31 | 3 | No |
| C3 Resources (Materials + Energy) capped at 30% | 5.24 | +0.01 | +0.02 / −0.01 | 1 | No (never binds) |
| C4 More shares (A$1,500 each, up to 40) | 5.71 | +0.48 | +0.56 / +0.39 | 5 | No (under 1 point) |
| C5 Keep-while-rank ≤ 90 (tax-aware selling) | 5.40 | +0.16 | +0.27 / +0.05 | 5 | No; turnover 53% vs 83% |
| C6 Universe of 500 | 5.66 | +0.42 | +0.67 / +0.18 | 6 | No (under 1 point) |

The only adopted lever was tranching, so the final candidate **F1 = v1.1 run as four quarterly tranches**. It removed start-month luck almost completely (range across starts 0.2–0.7 points instead of 2.0–3.7) and showed +1.1 points a year in development. I noted before the look that part of this gain probably came from concentration (each tranche holds only its top 3–8 shares), not from tranching as such.

Position sizing, risk balancing and holdings count therefore stay as v1.1 has them: equal weight, 25% per industry group, A$2,500 a share up to 30. Cost arithmetic confirms the size limits: at A$25,000 the tranche form lost 2.7 points a year to costs in development (A$2,080 parcels), v1.1 0.9.

## 4. Phase 2 — the one counted look

Pass rule (set in advance): at both sizes and on both unseen sets — after-tax return above the comparator; at least 1.0 point a year above v1.1; at or above the 90th percentile of 200 random portfolios; bootstrap ≥ 0.90; deflated Sharpe ≥ 0.95 at N = 402.

**Unseen A: panel_v2, 2016–May 2024, price-only, against the XJO price index (% a year)**

| Candidate | Size | Before costs | After costs | After tax A | After tax B | Excess/yr (t) | Tracking error | Max fall | Random pct | Bootstrap vs v1.1 | DSR | Beats index after tax |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Index | — | — | 4.6 | 3.9 | 3.3 | — | — | −27.7 | — | — | — | — |
| H82 v1.1 (reference) | 25k | 2.9 | 1.6 | 1.1 | 0.7 | −2.3 (−0.5) | 12.2 | −30.1 | 36 | — | 0.01 | no |
| H82 v1.1 (reference) | 100k | 4.9 | 4.0 | 3.1 | 2.3 | −0.3 (−0.1) | 7.9 | −26.9 | 62 | — | 0.04 | no |
| H88 | 25k | 6.0 | 4.8 | 3.5 | 2.4 | +1.1 (0.3) | 12.2 | −32.5 | 72 | 0.82 | 0.08 | no |
| H88 | 100k | 2.6 | 2.2 | 1.5 | 0.9 | −1.9 (−0.7) | 8.4 | −28.6 | 28 | 0.26 | 0.01 | no |
| H90 | 25k | 0.3 | −0.5 | −1.5 | −1.9 | −3.7 (−0.9) | 12.5 | −45.5 | 18 | 0.38 | 0.01 | no |
| H90 | 100k | 5.8 | 5.0 | 4.2 | 3.6 | +1.2 (0.3) | 10.4 | −34.7 | 78 | 0.75 | 0.09 | yes |
| F1 tranches | 25k | 1.1 | 0.2 | −0.5 | −1.1 | −4.3 (−1.2) | 10.2 | −32.9 | 23 | 0.24 | 0.00 | no |
| F1 tranches | 100k | 2.4 | 1.6 | 1.2 | 0.8 | −2.9 (−1.0) | 8.5 | −27.2 | 28 | 0.20 | 0.00 | no |

**Unseen B: EODHD, 2018–13 Nov 2026, total return, against the issuer A200/VAS total return (% a year)**

| Candidate | Size | Before costs | After costs | After tax A | After tax B | Excess/yr (t) | Tracking error | Max fall | Random pct | Bootstrap vs v1.1 | DSR | Beats index after tax |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Index | — | — | 8.8 | 6.8 | 6.2 | — | — | −26.8 | — | — | — | — |
| H82 v1.1 (reference) | 25k | 10.0 | 9.6 | 7.2 | 6.6 | +1.4 (0.3) | 12.5 | −22.9 | 87 | — | 0.08 | yes, by 0.4 |
| H82 v1.1 (reference) | 100k | 10.4 | 9.7 | 7.5 | 6.7 | +1.3 (0.4) | 8.7 | −25.5 | 92 | — | 0.10 | yes, by 0.5–0.7 |
| H88 | 25k | 9.0 | 7.6 | 6.0 | 5.5 | −0.3 (−0.1) | 11.6 | −27.1 | 72 | 0.31 | 0.04 | no |
| H88 | 100k | 7.0 | 6.5 | 4.7 | 4.1 | −1.7 (−0.6) | 8.3 | −29.2 | 56 | 0.12 | 0.01 | no |
| H90 | 25k | 5.2 | 4.5 | 2.6 | 2.5 | −2.8 (−0.6) | 14.0 | −32.0 | 42 | 0.18 | 0.01 | no |
| H90 | 100k | 11.1 | 10.4 | 8.1 | 7.0 | +2.3 (0.6) | 11.5 | −31.4 | 97 | 0.66 | 0.13 | yes |
| F1 tranches | 25k | 7.9 | 5.9 | 3.4 | 2.6 | −2.4 (−0.7) | 10.1 | −24.6 | 62 | 0.05 | 0.01 | no |
| F1 tranches | 100k | 7.9 | 7.4 | 5.6 | 4.8 | −1.3 (−0.5) | 8.1 | −24.4 | 77 | 0.17 | 0.01 | no |

**Results against the pass rule**

| Candidate | Development promise | Unseen A | Unseen B | Verdict |
|---|---|---|---|---|
| H88 (H80 + frog-in-the-pan) | +2.9 pts over v1.1 at A$100k (Dec path) | −1.8 pts vs v1.1 at A$100k; noise-placebo 25th pct | −3.3 pts vs v1.1 at A$100k; noise-placebo 21st pct | **Did not pass. Closed** |
| H90 (recency of the high) | Rank IC positive 15 of 15 years | A$100k +1.0 over v1.1; A$25k −2.1; behind index at A$25k by 5 pts | A$100k +0.7; A$25k −5.1 | **Did not pass. Closed** (ahead at one size, far behind at the other = noise) |
| F1 (v1.1 in four tranches) | +1.1 pts robust score | −1.5 / −2.4 pts vs v1.1 | −3.7 / −2.3 pts vs v1.1 | **Did not pass. Closed** |

Luck controls: no candidate reaches the 90th percentile of random portfolios at both sizes on either set; the highest deflated Sharpe ratio is 0.13 (bar 0.95). Stresses (costs × 1.5; unexplained delistings paid 70%) only lower the figures.

**The engine itself (not a new look — it has been read before).** On unseen B v1.1 is ahead of the index after tax by 0.4–0.7 points a year. Checks on that: started three, six or nine months later, it is ahead in 4 of 8 accounts and behind in 4 (A$25k June start: 3.6% against 6.9%). Year by year at A$100k it lagged in 5 of 9 years and led in 4 (2020, 2021, 2024, 2025). If every delisting without a record is paid at 70 cents in the dollar it falls to 6.7–7.8% after costs, below the index (a harsh bound: most are takeovers). With tracking error of 8.7 points, a true edge of 1.3 points a year would need about 180 years to show at t = 2.

### 4.1 Lifecycle against the owner's plan (A$5,000 + A$500 a month, 29 Dec 2017–13 Nov 2026, A$58,000 paid in)

| Plan | Value held | After a notional sale and tax |
|---|---|---|
| **Owner's plan: A200 40% / BGBL 60%** (VAS and VGS before each fund existed), never sold | A$103,500 | **A$97,300** |
| A200 only | A$86,400 | A$83,300 |
| Global only | A$115,000 | A$106,500 |
| Engine H82 v1.1 (starts with 4 shares) | A$88,600 | A$87,200 |
| Engine, H88 score | A$69,200 | A$68,600 |
| Engine, H90 score | A$61,200 | A$60,700 |
| Engine, F1 tranches | A$68,900 | A$68,300 |
| 200 random portfolios through the engine: 5th / 50th / 95th percentile | — | A$50,700 / A$71,400 / A$93,500 |

ETF legs use issuer distributions, taxed at 32% and reinvested, zero brokerage; the engine pays IBKR costs and yearly tax. The engine finished A$3,800 ahead of A200 alone and A$10,100 behind the owner's actual plan; its result sits between the median and the 95th percentile of random portfolios, i.e. within luck. Global shares, which the engine cannot hold, did the heavy lifting.

## 5. Phase 3 — frozen rules and how to reject this report

**Rules text:** `deepdive/out/FINAL_RULES_v1.2.md` = v1.1 unchanged plus parts I–O. It states, with no code reference: total-return inputs (security types, the duplicate-code test, code re-use, split-neutral returns, adjusted price, dividend cash per share, tax on dividends); the issuer-based comparator, day by day; the H88 and H90 scores; the tranche form; the eight-account robust score; and the H100 rule exactly as run, with each of report 63's ambiguities 1, 2, 3, 9, 13, 14, 16, 17 and 18 settled in words. Points that reports 54 and 63 show a second reader would guess are marked [guess-proof].

**What a blind validator should check first:** v1.1 on unseen B at A$100,000 (9.7% after costs; index 8.8%); the four H100 years 2023–2026; F1 on development (robust score 6.3%).

**What would make me reject my own result**
- A blind rebuild from the rule text that differs by more than 1.0 point a year at A$100,000, or flips the sign of any H100 year.
- The EODHD duplicate and re-use fixes (I3, I4) proving wrong for names the engine held; before the re-use fix one phantom −85% position appeared (PLG), so this class of error is real.
- Evidence that EODHD's dividend file is incomplete for the engine's holdings (it would understate the engine).
- For the "engine ≈ index" reading: it rests on one period. Any of the stresses above already flips its sign, which is why it is reported as "no difference", not as a lead.

**Limits that remain**
- Development is still price-only on an unlicensed panel; dividends before 2018 for dead companies do not exist in any source held. Norgate would close this.
- Industry groups come from today's ASX file, so dead companies have none (v1.1 A5). The resources cap could therefore not bind properly.
- Delisting reasons end in April 2020; later failures are paid in full in the main runs.
- Tranche sub-accounts are taxed separately (losses cannot cross), which is slightly harsh on F1 after tax; F1 also fails before tax.
- Franking credits are ignored on both sides.
- Deflated Sharpe formulas are still the programme's from-memory implementation.

**Deviations from the pre-registration**
1. A bug in my total-return comparator was found *after* the looks: it floored each day's (total − price) return at zero, which counted tracking noise as income and overstated the index by 1.1 points a year. It was fixed and the index columns re-run (pre-fix files kept as `*_before_comparator_fix.json`). No candidate figure changed. The fix is what turns v1.1 from "0.3 behind" to "0.8 ahead" after costs on unseen B; no pass/fail verdict changes.
2. The AGE signal was run only in its pre-registered flag form (8 stage-A trials, not 9).
3. In the lifecycle the engine's account received one extra A$500 on the last day; the table subtracts it.

## 6. Phase 4 — what goes to paper, what is retired

| Item | Decision | Why |
|---|---|---|
| **H82 engine v1.1** | Stays the single paper engine, unchanged. Score it in total return against A200 under rules v1.2 parts I–J | Best of everything tried; level with the index on clean data; no evidence of an edge (DSR 0.08–0.10) |
| **H100 June sleeve** | Paper in June 2027 under report 63's guard rails. Evidence downgraded | 23 Junes +3.5% (t 2.1), but the three never-seen Junes were −0.3%; costs equal the edge |
| H101 small-cap line | Tracking line only | Median pick loses; mean rests on a few winners |
| **H88 frog-in-the-pan** | **Closed** | Failed both unseen sets; its signal has the wrong sign in the cross-section |
| **H90 recency** | **Closed** | Ahead at A$100k, far behind at A$25k in both sets; adds nothing beyond the H80 score |
| **H138 (new) tranche form F1** | **Closed** | +1.1 in development, −1.5 to −3.8 unseen |
| H139 (new) six extra price signals | Closed on development | None passed the gate |
| H140 (new) weights, resources cap, more shares, keep buffer, universe 500 | Closed on development, no unseen look spent | None reached one point; the keep buffer halves turnover for no loss and may be reconsidered only for tax reasons |
| Dilution, listing age, LIC premium | Remain panel flags / guards, not engine rules | No development window; no effect on this engine |
| Next free card ID | H141 | |

**Confidence.** That no candidate beats the index: high — three independent failures on two data sets, consistent with five earlier reversals. That the engine has a positive edge after tax: roughly 60–65%, which is not usable; that it has an edge above one point a year: below 50%.

**What I would and would not do next**
- Do not run more price-signal or construction variants on this data. With 402 trials, a start-month spread of 2–4 points and a tracking error of 9–12 points, the data cannot tell a real one-point edge from luck. Further searching only adds trials.
- The only two sources of new information are time (the paper record of v1.1 and H100) and a different kind of data (point-in-time fundamentals with delisted companies; Norgate for pre-2018 total returns).
- Keep real money in the owner's 40/60 index plan. Nothing in this report supports moving any of it.

## 7. Files

| What | Path (under `scratchpad/deepdive/`) |
|---|---|
| Pre-registration and hash | `PREREG_64.md`, `out/prereg_64_hash.txt` |
| Frozen rules v1.2 and hash | `out/FINAL_RULES_v1.2.md`, `out/final_rules_v1.2_hash.txt` |
| Data preparation (both sources) | `code/prep_dd.py` → `data/bundle_v2.pkl`, `data/bundle_eod.pkl`; `out/eod_duplicate_codes.csv` |
| Engine (v1.1 engine + dividends, total-return comparator, extra scores) | `code/engine_dd.py`, `code/lib_dd.py`, `code/acct.py` |
| Phase 0 | `code/p0.py`, `code/p0_small.py`; `out/p0_v2.json`, `p0_eod.json`, `p0_small_*.json`, `p0_h100_*.csv`, `p0_h101_*.csv`, `p0_holdings_overlap_*.csv` |
| Phase 1 | `code/stageA.py`, `code/stageBC.py`; `out/stageA.csv`, `out/stageBC.json` |
| Phase 2 | `code/phase2.py`, `code/lifecycle.py`; `out/phase2_unseenA.json`, `phase2_unseenB.json`, `phase2_tables.md`, `lifecycle.json` |
| Trial and look logs, hashes | `out/trials_dd.csv`, `out/holdout_looks_64.txt`, `out/freeze_before_unseen_hashes.txt`, `out/code_hashes.txt`, `out/result_hashes.txt` |
| Papers read | `lit/nber_dm.pdf`, `lit/nber_hxz.pdf` |

EODHD data is licensed for the owner's personal, non-commercial use: the bundles and anything derived from them stay private.
