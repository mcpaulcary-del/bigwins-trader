# Report 66 — Optimising the index plan (the money that is actually invested)

16 November 2026. Author: research agent (Fable). General information, not personal financial or tax advice.
Code, logs and tables: `scratchpad/indexplan/` (`code/`, `out/`, `PREREG_66.md`).
Pre-registration SHA-256 `7f20d576…22db34`, hashed before any return was computed (`out/prereg_hash.txt`).
Trials run: 57 (45 pre-registered specifications, 4 of them run again on a second data set, plus 8 labelled [added]); log in `out/trials_66.csv`.

**Evidence tags.** [sim-L] = my simulation on the long monthly proxies, Jan 1975–Sep 2026 (Ken French / RBA, extended with issuer data). [sim-A] = my simulation on actual ETF prices and issuer distributions to 13 Nov 2026. [boot] = block-bootstrap forward ranges. [arith] = deterministic arithmetic (7% a year before fees, 2.5% inflation). [R18], [R37], [R44] etc. = an earlier report. [unverified] = nobody confirmed it. Dollar figures are after fund fees, a 0.05% buying spread, tax on distributions each year and, where marked "if sold", capital gains tax under the rules that start 1 July 2027.

---

## 0. Answer first

**The plan is right. Change one rule, add two, and leave the rest alone.**

| # | Item | Verdict | Expected dollar effect (A$5k + A$500/month, 32% tax rate) |
|---|---|---|---|
| 1 | 40% Australia / 60% global | **Keep.** No split from 30/70 to 50/50 can be told apart on return | 50/50 instead of 40/60 after 20 years: median +A$1,600, range −A$13,500 to +A$13,300 [boot]. Not a decision you can make from data |
| 2 | A200 + BGBL | **Keep.** Cheapest pair; no rival beats it by a measurable amount | Against one-fund DHHF: about +A$500 / +A$3,100 / +A$11,700 after 10 / 20 / 30 years (fee only) [arith]. Against VAS + VGS: +A$400 / +A$2,800 / +A$10,800 (fee plus smaller taxable distributions) [boot] |
| 3 | Steering rule | **Change.** Replace "each November, if outside 35–45%, steer new money" with a once-a-year formula that sets the split (section 3) | No measurable change in wealth (median +A$260 after 20 years, range −A$2,800 to +A$2,900 [boot]). The gain is control: worst Australian weight in the first five years 49% instead of 69%, and time outside 35–45% falls from 17% to 6–8% of months [sim-L] |
| 4 | Never sell to rebalance | **Keep.** Confirmed | Selling once a year to restore 40/60 costs about A$2,200 after 20 years and A$10,300 after 30 (median; A$45,300 at the 10th percentile) [boot]; A$10,100 of tax paid along the way in the historical median [sim-L] |
| 5 | Monthly, automatic, on arrival | **Keep.** Line the auto-invest date up with payday | Saving up and investing quarterly: −A$2,900 after 20 years. Yearly: −A$15,300 [sim-L] |
| 6 | Lump sums (A$50k / A$200k case) | **Invest at once, by the same formula** | Spreading over 12 months lost in 67% of historical start months; mean cost 1.8% = A$900 on A$50,000, A$3,700 on A$200,000 [sim-L] |
| 7 | **New: parcel rule if you ever sell** | Sell parcels held over 12 months, highest cost first, and write the choice down | On a sale of one fifth of the account after 20 years (about A$87,000): tax A$700 instead of A$11,800 under first-in-first-out. This is tax deferred, not tax removed [sim-L] |
| 8 | **New: 30 June 2027 record** | Save a holdings statement showing units and closing prices at 30 June 2027. No trade is needed | Protects the 50% discount on gains earned before that date; without the record the split cannot be proved |
| 9 | Geared funds (GHHF, GEAR) | **No.** Failed two of four pre-registered tests | GHHF-style gearing on one fifth of contributions: median +A$10,000 after 20 years but −A$5,300 at the 10th percentile and a 58% worst fall instead of 40% [boot, sim-L] |
| 10 | What actually moves the result | Your savings rate and where the money sits | +A$100 a month: +A$60,700 after 20 years. Skipping 2 months in 12: −A$51,700. Super at a 32% rate: about 25–30% more per pre-tax dollar, locked until 60 [boot, arith] |

**What the plan is expected to produce** (both funds assumed to earn 7% a year before fees, 2.5% inflation; 10th–90th percentile range) [boot]:

| After | Paid in | Value, never sold (median) | After tax if sold (median) | Range if sold | Median in today's dollars |
|---|---|---|---|---|---|
| 10 years | A$74,000 | A$108,000 | A$104,000 | A$75,000–135,000 | A$81,000 |
| 20 years | A$167,000 | A$346,000 | A$324,000 | A$204,000–488,000 | A$198,000 |
| 30 years | A$293,000 | A$832,000 | A$776,000 | A$448,000–1,296,000 | A$370,000 |

With a A$50,000 start the 20-year median if sold is A$479,000 (A$276,000–766,000); with A$200,000 it is A$1,006,000 (A$514,000–1,751,000). If returns repeat 1975–2026 instead (6.9–7.5% a year above inflation), the 20-year median for the base plan is A$416,000. These are models, not forecasts.

**The honest summary.** I tested 57 variations of allocation, fund, steering, timing, tax handling and gearing. None of the return-seeking ones passed the bar set in advance. Everything that survives is about costs, tax mechanics and not making mistakes, and together those are worth a few thousand dollars over 20 years. That is small against the two things that are not algorithm questions: how much goes in each month, and whether some of it belongs in super.

---

## 1. Method and rules set in advance

- **Hash before results.** `PREREG_66.md` lists every comparison, the account model and five decision rules. Its hash was recorded before any figure was produced.
- **Decision rules.**
  - D-a: a "structural" change (fees, spreads, tax mechanics) is recommended if its sign is certain at all four tax rates and it adds no recurring effort.
  - D-b: a return-based change needs all three: paired monthly t ≥ 3.0; ahead in at least 75% of rolling 10-year windows and in both halves of the sample; and a walk-forward test (stand at 1990, 1995 … 2020, pick the past winner, be ahead of 40/60 over the next five years in at least 5 of 7).
  - D-c: anything that raises risk must also leave the 10th-percentile 20-year outcome no worse than the plan's.
  - D-d: differences under 0.10 points a year or 1% of final wealth are "no measurable difference", and the lower-effort rule wins.
  - D-e: nothing is chosen for having the best full-sample result.
- **Account model.** A$0 brokerage, fractional units, 0.05% half-spread. Distributions taxed when paid at the marginal rate, with franking credits and foreign tax offsets counted, and the net amount reinvested. Three plans: A$5,000, A$50,000 and A$200,000 at the start, each plus A$500 a month rising 3% every July. Tax rates 16%, 32% (base), 39% and 47% including Medicare.
- **Sale tax.** The post-1 July 2027 rules applied throughout: each parcel held 12 months or more has its cost indexed by CPI (factor to three decimals, gains only); the net gain is taxed at the marginal rate with a floor of 32% (30% minimum tax plus Medicare on top, R37's reading).
- **Tax settings measured from issuer data, 2015–2026** [sim-A]: VAS franking credits are 33.3% of the cash distribution; VGS foreign tax offsets 9.3%; realised capital gains are 5% of VAS's distributions, 32% of VGS's and 45% of VDHG's.
- **Data checks.** Long proxies against actual funds: Australia 9.67% a year against VAS 9.35% over 199 months (correlation 0.993); global 13.06% against VGS 13.24% over 133 months [sim-A]. Engine unit tests pass (`code/t0_tests.py`).

**Limits that matter.**
1. The long history applies today's tax rules, franking levels and fees to 1975–2026 returns. It answers "what would these rules have done", not "what happened".
2. BGBL has 41 months of history. Before June 2023 it is modelled as VGS plus the 0.10-point fee difference.
3. Betashares does not publish tax components in the data I hold; A200, BGBL and DHHF use the VAS/VGS ratios [unverified].
4. How capital gains distributed by a fund are taxed after 1 July 2027 (whether any discount or indexation passes through) is not settled in R18 or R37. I treated them as fully taxable [unverified].
5. betashares.com.au returned HTTP 403 today. Platform mechanics come from R44's saved pages (13 Nov 2026). Three things are not confirmed: the day of the month auto-invest runs, whether the Betashares Direct tax report lets you choose parcels, and the price used for reinvested distributions [unverified].
6. The bootstrap gives both funds the same expected return. That is an assumption, and it is the reason its allocation rows centre on zero.

---

## 2. Question 1 — Is 40/60 right?

### 2.1 Allocation

Final after-tax wealth if sold, relative to 40/60, across every start month 1975–2026, A$5k + A$500/month, 32% rate [sim-L]:

| Australia share | 10 years: median (10th–90th) | ahead in | 20 years: median (10th–90th) | ahead in | Volatility a year |
|---|---|---|---|---|---|
| 0% | 1.005 (0.866–1.078) | 52% | 0.955 (0.760–1.079) | 36% | 14.2% |
| 30% | 1.002 (0.966–1.019) | 53% | 0.991 (0.948–1.021) | 40% | 12.80% |
| **40%** | 1.000 | — | 1.000 | — | **12.75%** |
| 50% | 0.996 (0.980–1.035) | 45% | 1.010 (0.979–1.051) | 59% | 12.94% |
| 100% | 0.963 (0.877–1.233) | 43% | 1.056 (0.868–1.371) | 57% | 16.7% |

- **Paired test.** Australia minus global, monthly, 621 months: t = 0.03 (first half +0.44, second half −0.73). The two have returned the same to within noise: 12.0% and 12.7% a year [sim-L].
- **Walk-forward.** Picking the best of 30/40/50 on past after-tax wealth beat 40/60 in the next five years 2 of 7 times (3 of 7 with a 15-year look-back). It "promised" +2.5% and delivered −0.5%. With seven allocations to choose from: 2 of 7, and it picked 100% Australia in 2010, 2015 and 2020, each time just before global shares led [sim-L]. This is report 48's finding again.
- **By era** (% a year): 1975–89 Australia 19.7, global 23.5. 1990–99: 11.9, 12.9. 2000–09: 8.1, −2.0. 2010–19: 7.7, 12.6. 2020–26: 8.4, 12.8 [sim-L]. Leadership swaps by decade.
- **Risk does persist** (R48), and 40/60 is within 0.05 points of the lowest-volatility mix. That is a reason to keep it that does not depend on forecasting.

**Franking.** If the two funds earned the same return before tax, the Australian fund would be worth more after tax, because franking credits pay part or all of the tax on its distributions [arith]:

| Tax rate | Yearly tax on distributions: Australian fund (3.8% yield) | Global fund (2.2% yield) | Australia could earn this much less before tax and still tie over 20 years |
|---|---|---|---|
| 16% | −0.46 points (a refund) | +0.18 | 1.2 points a year |
| 32% | +0.36 | +0.57 | 0.8 |
| 39% | +0.71 | +0.73 | 0.7 |
| 47% | +1.12 | +0.93 | 0.7 |

Most of the tie-break at 32% and above comes from the sale tax, not the yearly tax: the Australian fund's reinvested distributions raise its cost base. Whether the market already prices franking into Australian shares (so that their pre-tax return is lower by about this much) cannot be settled from 51 years of data. At 10 points of extra Australian weight the effect is worth about A$2,200 after 20 years at a 32% rate and A$4,100 at 16% **if** pre-tax returns are equal [arith].

**Verdict: keep 40/60.** Fails D-b on all three tests in both directions. One conditional note, not a recommendation: for an investor taxed at 16% (income under A$45,000), a 50/50 split has the stronger structural case, because franking refunds are largest there and the 30% minimum tax falls only on capital gains.

### 2.2 Tilts

| Tilt | Long history [sim-L] | Actual ETFs [sim-A] | D-b result |
|---|---|---|---|
| US only in place of world | +0.96 pts/yr, t 1.55, 1975–2026 | IVV: +2.6 pts/yr, t 3.3, 2009–2026 | Fails. The t above 3 exists only in the 17 years everyone already knows about. Walk-forward picked it in 2000 and it then lost 3.8% in five years |
| 10% global small companies | −0.11 pts/yr, t −1.0 (1990–2026); ahead in 73% of windows in the first half, 21% in the second | — | Fails |
| 10% Australian small (VSO) | — | −0.19 pts/yr, t −0.8, 2011–2026; behind from all 150 start months | Fails |
| 10% emerging markets | — | IEM: −0.60 pts/yr, t −2.0, 2009–2026. VGE: −0.60, t −1.9, 2013–2026 | Fails |
| Global half hedged | +0.44 pts/yr, t 0.95 | VGAD: −0.47 pts/yr, t −0.5, 2014–2026 | Fails |
| Global fully hedged | +0.87 pts/yr, t 0.95; volatility 14.2% against 12.75% | −1.0 pts/yr | Fails |

The hedged proxy's long-run lead is the Australian-over-US interest-rate gap of the 1980s and 1990s. It is an approximation (hedged ≈ US-dollar return plus the rate gap), and hedging raised portfolio volatility. **No tilt.** Unhedged stays, as R39 concluded.

---

## 3. Question 3 — Steering rule (the one change)

The spec's rule is: "Each November, if A200 is outside 35–45%, steer new money only." Read literally (all new money to the smaller fund for a year), it has two faults [sim-L]:

1. **It overshoots while the account is small.** In year one A$6,000 of new money meets a A$5,000 balance. From November starts, the Australian weight reached 69% within five years in the worst case, against 49% under the formula below.
2. **It stops working when the account is large.** With A$200,000, new money is under 3% of the balance a year. The account spent 40–50% of months outside 35–45% under every contribution-only rule.

Rules compared, 20-year windows, A$5k plan; wealth relative to the spec's rule [sim-L]:

| Rule | Final wealth if sold: median (10th–90th) | Average distance from 40% | Months outside 35–45% | Setting changes a year |
|---|---|---|---|---|
| S0 Fixed A$200/A$300 forever | 0.995 (0.985–1.007) | 5.3 pts | 46% | 0 |
| S2 Spec rule (all-or-nothing after a November check) | 1.000 | 3.6 | 27% | 0.4 |
| **S3 Yearly formula (below)** | 1.005 (0.993–1.016) | 2.9 | 19% | 0.7 |
| S7 Yearly formula + distributions paid to the smaller fund | 1.002 (0.991–1.017) | 2.2 | 9% | 0.8, plus 4–6 manual buys |
| S1 Re-split every month | 0.999 (0.990–1.014) | 1.7 | 8% | 12 |
| S4 Buy only the smaller fund, every month | 0.999 (0.990–1.014) | 1.8 | 8% | 3.2 |
| S6 Sell once a year back to 40/60 | 0.990 (0.964–0.998) | 1.4 | 4% | 1 sale; A$10,100 tax (median) |
| S6 Sell every month | 0.969 (0.921–0.983) | 0 | 0% | 12 sales; A$20,300 tax |

- **Wealth:** every no-sell rule is within 1% of every other. By D-d that is no measurable difference. Band width (3, 5, 7.5 or 10 points) changes the median by less than 1% [sim-L, added].
- **Selling** is the only rule that reliably costs money: behind the spec rule in 93% of 20-year windows when done yearly and in all of them when done monthly.
- **On actual ETFs** (VAS/VGS from Dec 2014; A200/BGBL from Jun 2018) the no-sell rules finish within 0.9% of each other at every account size [sim-A].
- **Check month:** July or November makes no difference to wealth. July had slightly less drift (2.6 against 3.0 points) and lets one sitting do both jobs [sim-L, added].

**The new rule (S3).** Once a year, in the same sitting as the 3% rise:

> A200 share of next year's contributions = ( 0.40 × (A200 value + BGBL value + next 12 months of contributions) − A200 value ) ÷ next 12 months of contributions.
> Below 0, use 0. Above 1, use 1. Round to the nearest 5%. BGBL gets the rest.

Worked example. A200 A$5,400, BGBL A$6,600, new monthly amount A$515 (A$6,180 a year). Share = (0.40 × 18,180 − 5,400) ÷ 6,180 = 0.30. Set A$155 to A200 and A$360 to BGBL. If both funds sit at target, the formula returns 40% and nothing changes.

**When the account outgrows the rule.** Once the formula has returned 0% or 100% two years running (expect this somewhere above A$100,000–150,000; R47 found the same threshold), do not sell. Optionally switch distributions to cash and add them to the smaller fund. For the A$200,000 plan over 20 years this cut the typical worst drift from 15 points to 10 and months outside the band from 43% to 23% [sim-L]. Otherwise accept the drift: both funds are share funds, the cost is about 1 point a year of tracking difference from a perfect 40/60 with no expected loss of return, and the historical range under this rule was 23% to 61% Australian.

---

## 4. Question 2 — Fund choice

### 4.1 Australian fund [sim-A]

| Fund | Fee | Return since Jun 2018 | Against A200 | Distribution yield |
|---|---|---|---|---|
| **A200** | 0.04% | 8.90% | — | 3.75% |
| VAS | 0.07% | 8.64% | −0.26 pts/yr, t −0.8 | 4.07% |
| IOZ | 0.05% [unverified] | 8.69% | −0.21, t −0.4 | 4.05% |
| STW | 0.05% [unverified] | 8.79% | −0.11, t −0.3 | 4.27% |

All differences are inside noise; A200 finished ahead from almost every start month, but only by 0.2–1.2% of final wealth. The fee gap is the only certain part. A200 is also the only one of the four that Betashares' free auto-invest covers. **Keep A200.**

### 4.2 Global fund [sim-A]

| Fund | Fee | Return since Jun 2023 | Against BGBL | Distribution yield |
|---|---|---|---|---|
| **BGBL** | 0.08% | 16.85% | — | 1.20% |
| VGS | 0.18% | 16.60% | −0.25 pts/yr, t −0.9 | 2.62% |
| IWLD | 0.09% [unverified] | 16.42% | −0.44, t −0.2 | 1.76% |
| IVV 70 + VEU 30 | about 0.04% [unverified] | 17.01% | +0.16, t 0.2 | 1.9% |
| VTS 70 + VEU 30 | about 0.04% [unverified] | 17.04% | +0.18, t 0.3 | 2.1% |

- BGBL tracks VGS with a tracking difference of 0.46% a year. Its lead of 0.22 points matches the fee gap plus noise.
- VGS pays out more, and a third of it is realised capital gains. At a 32% rate that is about 0.25 points a year of extra tax now instead of later. BGBL's low yield may rise as the fund ages; check it each July.
- The IVV/VTS + VEU pairs are level with BGBL (t 0.2–0.3). They need two more lines, VTS and VEU are US-domiciled (W-8BEN form, US estate-tax exposure; R18), and none is in free auto-invest. More effort for no measurable gain.
- **Keep BGBL.**

### 4.3 One fund instead of two

| Test | Result |
|---|---|
| DHHF against A200 37 / BGBL 63, Jan 2020–Oct 2026 [sim-A] | −1.20 pts/yr, t −1.3. Final wealth if sold 3.2% lower. Most of the gap is DHHF's emerging-market and small-company holdings, which is luck of the period, not a flaw |
| VDHG, same period [sim-A] | −2.25 pts/yr, t −2.1; 5.3% lower. It holds 10% bonds and distributes 4.4% a year, 45% of it capital gains: about 0.84 points a year of tax at a 32% rate against 0.46 for a DHHF-like fund [arith] |
| Same mix in one self-rebalancing fund at the same fee as the pair, 1975–2026 [sim-L, added] | Median 1.001 of the pair's wealth at 20 years (0.963–1.049). Structure alone is worth nothing measurable |
| Same, at DHHF's 0.19% fee | 0.989 at 20 years; behind in 72% of windows. This is the fee |
| Per-asset indexation after July 2027: extra sale tax from holding two funds [sim-L] | Median 0.00–0.05% of the account. 90th percentile 0.15–0.41%. Worst case 2.8% (a 10-year window with a A$200,000 start). Nil in about 40% of windows |

The Betashares article's point (R34 §5.16(b)) is real: indexation is applied asset by asset, so a fund that lags inflation wastes it. For two share funds held for a decade or more the cost is, in the median, a few hundred dollars at most. The fee difference is certain and larger: A$3,100 after 20 years and A$11,700 after 30 on the base plan; A$14,600 and A$44,400 with a A$200,000 start [arith]. Two funds also let you choose which fund and which parcel to sell (section 6). **Keep the pair.** R44's caveat stands: if you would tinker with two lines, one DHHF line you never touch is better than two you fiddle with.

---

## 5. Question 4 — Timing

| Question | Evidence | Verdict |
|---|---|---|
| Which day of the month? | Buying on trading day 1, 6, 11 or 16: final wealth within ±0.75% and the order changes between samples (VAS/VGS 2014–26, STW/IVV 2007–26, A200/BGBL 2023–26) [sim-A]. The last third of the month has slightly higher average daily returns (STW 6.0 bp, t 2.6), which favours having money in early over waiting for month-end | No day is better. Set auto-invest for the day after pay lands, so nothing sits in the wallet (Betashares keeps the interest, R44) |
| Batch contributions? | Quarterly with cash at 0%: 0.7% less after 20 years (median −A$2,900), never ahead. Yearly: 3.8% less (−A$15,300). Even with cash earning the cash rate, yearly was behind in 91% of windows [sim-L] | Monthly, as now |
| Lump sum at once or spread? | Spread over 12 months: mean 1.8% behind (t −1.65), ahead in 33% of start months, range −10.7% to +8.8% (10th–90th). Over 6 months: 0.9% behind, ahead in 36% [sim-L] | At once. If that would cost you sleep, six equal monthly parts written down in advance costs about A$450 per A$50,000 on average |
| Reinvest distributions in the same fund, or direct them to the smaller fund? | No wealth difference (ratio 1.000–1.003). Directing them only helps control drift in a large account (section 3) [sim-L] | Reinvestment on, as now |

Nothing changes except aligning the date.

---

## 6. Question 5 — Tax

### 6.1 What the 2027 rules do to this plan

- **Sale tax as a share of the account** [arith]: about 2% after 10 years, 4% after 20, 6% after 30 at a 32% rate. At 16% it is 4% after 20 years, because the 30% floor applies.
- **Old rules against new** [arith, sim-L]: at 7% return and 2.5% inflation the new rules are slightly kinder at 32% and above (+A$2,400 after 20 years) and harsher at 16% (−A$5,500). On actual 1975–2026 paths, where capital growth ran further ahead of inflation, the new rules left 2–3% less after a sale (median). The sign depends on how much of the return arrives as capital growth above inflation.
- **Share of the nominal gain that is taxed under indexation:** 64–76% in the historical median, against 50% under the discount [sim-L].
- **Never selling is worth more than before.** The gap between "never sold" and "sold" is A$22,000 at 20 years and A$56,000 at 30 on the base plan [boot].

### 6.2 Parcel rule (new)

If money ever has to come out, which units are sold matters a great deal. Selling one fifth of the account [sim-L, 32% rate]:

| After | Sale | Tax, oldest parcels first | Tax, highest-cost eligible parcels first | Saved (10th–90th) |
|---|---|---|---|---|
| 10 years | A$25,600 | A$3,070 | about A$0 | A$2,700 (A$90–5,900) |
| 20 years | A$86,800 | A$11,800 | A$660 | A$9,500 (A$3,200–29,900) |
| 30 years | A$213,700 | A$35,100 | A$1,700 | A$31,400 (A$25,800–93,900) |

With A$200,000 at the start the 20-year saving is A$30,300 on a A$276,000 sale. Three cautions:
1. It is deferral. The parcels left behind carry lower costs. It becomes a permanent saving only for money that is never sold, sold in a low-income year (subject to the 30% floor) or passed on.
2. Only parcels held 12 months or more get indexation, or the discount on their pre-July-2027 slice. Selling younger parcels gets neither [R18].
3. The right to nominate identifiable parcels is from memory of ATO guidance [unverified], and I could not confirm what the Betashares Direct tax report does by default [unverified]. Keep your own record of the choice, made on the day of the sale. One question for the tax agent.

### 6.3 30 June 2027

- Units held across 1 July 2027 are treated as sold and re-bought at market value just before that date. The gain to that date is deferred and keeps the 50% discount when the units are finally sold, provided actual purchase to actual sale is 12 months or more. Later growth gets indexation from the September quarter 2027 [R18, R37].
- **Action:** in the first week of July 2027 download a holdings statement dated 30 June 2027 (units and closing price for A200 and BGBL) and the full transaction history. Keep both permanently, in two places.
- **No trade helps.** Selling before July gains nothing (the deferred slice keeps its discount anyway, and units bought since July 2026 are under 12 months old). Rushing extra money in gains nothing either. By then the account holds about eight months of contributions; the slice is small.
- A parcel below cost on 30 June 2027 carries a deferred loss, recognised at the real sale [R37].

### 6.4 Low marginal rate

Below the 30% bracket, post-July-2027 capital gains are taxed at 30% at least, while franked income still earns a refund [R18, R37]. Two consequences: realising gains in a low-income year saves less than it used to, and for a low-rate holder income-heavy Australian shares are relatively better treated than growth-heavy global shares (section 2.1). The floor also covers gains a fund distributes, so funds that distribute fewer realised gains are preferable; BGBL and A200 are at the low end today [sim-A].

### 6.5 Super against a personal account (rules of thumb, not advice)

A$1,000 of pre-tax pay a year, same 40/60 index mix, 7% before fees. Assumptions: super charges 0.3 points more in fees and loses 0.3 points to fund-level tax; tax-free after 60 [arith; fee and tax drag are my estimates, unverified]:

| Marginal rate | Head start per dollar | After 20 years: super | Personal, if sold | Super ahead by |
|---|---|---|---|---|
| 16% | none (1.19 only if the low-income offset refunds the 15% [unverified]) | A$53,500 with the offset | A$46,100 | 0–16% |
| 32% | 1.25 | A$45,500 | A$35,000 | 30% |
| 39% | 1.39 | A$45,500 | A$30,300 | 50% |
| 47% | 1.60 | A$45,500 | A$25,200 | 81% |

- At 30% and above, for money not needed before 60, super beats this account by more than every other finding in this report combined.
- At 16% the case is thin without the offset.
- The price is access. The cap is A$32,500 a year including employer contributions [R33]. Division 293 applies above A$250,000 [R33].
- This account remains the right place for money that must stay reachable.

---

## 7. Question 6 — More growth without borrowing, and gearing

**Already at 100% shares.** The only ways left to raise expected growth are more risk through gearing or concentration, or more money in.

### 7.1 Geared funds, modelled honestly

Model: a fund that borrows to hold 1.54 times its capital (gearing 35%, GHHF's middle), pays cash rate plus 0.5–2% on the loan and 0.35% on gross assets, and resets monthly. Check against real funds [sim-A]:

| Fund | Actual | Model at 0.5% loan margin | Gap |
|---|---|---|---|
| GEAR, 2014–2026 (gearing 57.5%, fee 0.80%) | 10.5% a year | 10.5% | 0.0 |
| G200, 30 months | 11.8% | 11.9% | −0.1 |
| GHHF, 30 months (against DHHF as the base) | 17.8% | 16.2% | +1.6 |

The GHHF gap is above my 1.5-point limit, so GHHF figures below are less certain than the table suggests (its holdings differ from DHHF's and the window is short).

GHHF-style gearing against the plain 40/60, 1975–2026 [sim-L]:

| Test set in advance | Result | Pass? |
|---|---|---|
| Paired monthly t ≥ 3 | t 3.4–3.6. This is the share premium over cash (5.8% a year in this sample), taken 1.54 times | Yes |
| Ahead in ≥ 75% of 10-year windows, both halves | 84% (92% / 75%) at a 0.5% margin; 72% (71% / 73%) at 2% | Yes at low margins |
| Walk-forward ≥ 5 of 7 | 4 of 7. Behind in the five years from 1990, 2000 and 2005 | **No** |
| 10th-percentile 20-year outcome not below the plan's | Whole account geared: A$260,700 against A$264,600. One fifth of contributions: A$263,700 against A$264,600. Bootstrap: A$200,900 against A$204,100 | **No** (narrowly for the one-fifth version) |

What it would have meant:
- **Whole account geared, 20 years:** median 1.19 times the plain plan (0.99–1.41) [sim-L]; forward at 7% returns, median +A$53,600, 10th percentile −A$23,800 [boot].
- **One fifth of contributions, 20 years:** median 1.04 times (1.00–1.08) [sim-L]; forward median +A$10,200, 10th percentile −A$5,300 [boot].
- **Worst fall:** 58% against 40% on month-ends. **2000–2009:** −1.4% a year against +2.0% for the plain mix, a lost decade made worse.
- **Break-even:** gearing only pays if shares beat cash by more than about 3 points a year (2.6 at a 0.5% loan margin, 3.1 at 1%) [arith]. At a 4-point premium the edge is +0.5 to +0.7 points a year; at 2 points it is −0.3 to −0.6.
- **GEAR-style (2.5 times, Australian shares only):** the monthly model is wiped out in October 1987. The real fund fell 66.5% in March 2020 against 34.3% for the index [sim-A]. Its 20-year 10th percentile is A$225,000 against A$265,000.

**Verdict: no geared fund in this account.** The historical median is better and the evidence for a share premium is the strongest return evidence in this report. But it fails two tests I set before looking, it adds 18 points to the worst fall, and the largest risk it adds is the one the owner named: a mistake under stress. If the owner ever wants it regardless, the least-bad form is GHHF for at most one fifth of new contributions, never GEAR, and never sold in a fall. That is a description, not a recommendation.

### 7.2 What does raise the result

20-year median after tax if sold, base plan A$324,000 [boot]:

| Change | Result | Difference |
|---|---|---|
| A$600 a month instead of A$500 | A$384,000 | +A$60,700 (A$32,500 of it extra money paid in) |
| Raise 5% a year instead of 3% | A$383,000 | +A$59,200 |
| A$750 a month | A$477,000 | +A$152,800 |
| No yearly rise | A$257,000 | −A$66,600 |
| Pay 10 months in 12 | A$272,000 | −A$51,700 |

A fund charging 1% a year would cost A$22,000 over the same 20 years [arith]. The plan's 0.064% is already at the floor.

---

## 8. Exact rules, as they should now read

Changes from spec §1.1 / R44 are marked **[changed]** or **[new]**.

1. **Funds and target.** A200 40%, BGBL 60%, Betashares Direct, individual account. Distribution reinvestment on.
2. **Monthly.** Automatic transfer and auto-invest, dated the day after pay arrives **[changed: date only]**. No batching.
3. **Yearly sitting, first week of July [changed: replaces the November band check].**
   - a. Raise the monthly amount by 3%, or more if you can.
   - b. Set the split with the formula in section 3 (A200 share = (0.40 × (total + next 12 months of contributions) − A200 value) ÷ next 12 months of contributions; clip to 0–100%; round to 5%).
   - c. Download the annual tax statement and the transaction history. File them in two places.
   - d. Check BGBL's distribution over the year against its June price. Above about 2.5%, note it; nothing to do yet.
4. **Never sell to rebalance.** Any Australian weight from 25% to 55% needs no action beyond rule 3. No dip-buying, no own picks, 48-hour wait before any sale (unchanged).
5. **Large account [new].** When the formula has returned 0% or 100% two Julys in a row, you may switch distributions to cash and add them to the smaller fund when they arrive. Still no selling.
6. **Lump sums [new].** Invest on arrival. Split it with the same formula, using the lump as "next 12 months of contributions".
7. **If a sale is ever unavoidable [new].** Sell only parcels held 12 months or more. Choose the highest-cost parcels first, across both funds. Write down date, fund, parcel dates and units on the day. Ask the tax agent first if the sale is above A$10,000.
8. **30 June 2027 [new].** In the first week of July 2027 save a holdings statement dated 30 June 2027 with units and closing prices, plus the full history. No trade.
9. **No geared, hedged, small-company, emerging-market or US-only fund in this account.** Revisit only at the November 2027 review, and only with new evidence that passes rule D-b.
10. **Before raising the monthly amount** apply R44 §1.4: emergency cash first; debts above about 7% first; an offset at 6% or more; and at a 30% or higher tax rate, ask about super for money not needed before 60.

**Effort.** One sitting a year of about 15 minutes, in place of a July change plus a November check. Ten minutes more in July 2027.

**For the advisory release.** The system already reads exported statements (SYS-34). It can print the July split from rule 3b and the 30 June 2027 reminder without touching the account. That is a display change, not a strategy card.

---

## 9. What I could not verify, and what would change the answer

| Item | Status | Effect if wrong |
|---|---|---|
| Tax components of A200, BGBL, DHHF distributions | Assumed from VAS/VGS [unverified] | Shifts section 4 by a few hundredths of a point a year |
| Treatment of fund-distributed capital gains after 1 July 2027 | Treated as fully taxable [unverified] | If a discount or indexation passes through, VGS and VDHG look slightly less bad |
| Parcel choice permitted, and the platform's default method | [unverified] | If only first-in-first-out is available, section 6.2's saving is not available at this platform |
| Auto-invest execution day and reinvestment price at Betashares Direct | [unverified]; site returned 403 today | None on the conclusions; affects rule 2's wording |
| Low-income super offset and current caps | From R33 / memory [unverified] | Changes the 16% row of section 6.5 only |
| GHHF fee (0.35% of gross assets) and gearing band (30–40%) | From memory and R33 [unverified] | Model missed actual GHHF by 1.6 points over 30 months; the verdict rests on the tests, not this figure |
| Marginal rate of the owner | Unknown; 32% used | Every dollar figure scales; none of the verdicts changes between 16% and 47%, except the notes in sections 2.1 and 6.4 |

Not done: no blind replication of this report. A validator could re-implement `PREREG_66.md` from the text; the engine is 150 lines.

## 10. Files

| File | Content |
|---|---|
| `indexplan/PREREG_66.md`, `out/prereg_hash.txt` | Pre-registration and its hash |
| `code/data.py`, `engine.py`, `common.py`, `t0_tests.py` | Data build, account and tax engine, tests |
| `code/q1_alloc.py` → `out/q1_windows.csv`, `q1_tstats.csv`, `q1_walkforward.csv`, `q1_eras.csv` | Allocation and long-history tilts |
| `code/q2_funds.py`, `q2b_onefund.py` → `out/q2_funds.csv`, `q2_yields.csv`, `q2b_onefund.csv` | Fund choice, actual-ETF tilts, one fund against two |
| `code/q3_steer.py`, `q3b_early.py` → `out/q3_steer.csv`, `q3_bands.csv`, `q3_actual.csv`, `q3b_early.csv` | Steering rules |
| `code/q4_timing.py` → `out/q4_dayofmonth.csv`, `q4_batching.csv`, `q4_lump.csv` | Timing |
| `code/q5_tax.py` → `out/q5_indexation.csv`, `q5_parcels.csv` | Per-asset indexation, parcel choice, old against new rules |
| `code/q6_gear.py` → `out/q6_validation.csv`, `q6_gear.csv`, `q6_walkforward.csv`, `q6_analytic.csv` | Gearing |
| `code/q7_forward.py` → `out/q7_forward.csv`, `q7_variants.csv` | Forward ranges and plan variants |
| `code/q8_struct.py` → `out/q8_franking.csv`, `q8_regime.csv`, `q8_fees.csv`, `q8_super.csv` | Franking, regime, fees, super arithmetic |
| `out/trials_66.csv`, `out/log_*.txt` | Trial log and run logs |
