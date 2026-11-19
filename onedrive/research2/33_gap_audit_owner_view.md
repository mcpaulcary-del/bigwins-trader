# Gap audit from the owner's point of view: what v2.10 leaves on the table

Report 33, 13 November 2026. Written against FD_FINAL.md (v2.10) and reports 11–21. General information only: not financial, tax or legal advice. Where a section touches the owner's personal position (super, debt, tax rate) it sets out trade-offs for the owner and a registered tax agent or licensed adviser; it does not recommend a personal course.

**Scope.** The owner wants the system to grow money as far as the evidence allows, not only avoid losses. Reports 31 (momentum, big winners, falls and rebounds) and 32 (decision frequency, daily crash brake) cover two of the owner's criticisms. This report lists every *other* material opportunity or expectation that v2.10 does not address, or addresses only by implication, and tests each against evidence.

**Tags.** **[2+]** two independent sources; **[1]** one source or one originating source; **[unverified]** inference, model memory or a figure not confirmed this session; **[computed]** my arithmetic from tagged inputs; **[primary]** read directly in the source document.

**Access limits.** Read in full this session: the ASX Investment Products report for October 2026 (PDF, primary; every ETF fee, spread and return below comes from it unless noted). Blocked in this session: ato.gov.au, interactivebrokers.com.au, reviewetf.com.au (and, per report 31, issuer and most publisher hosts). Consequences: IBKR's interest tiers, the ATO wash-sale ruling, super thresholds and the academic papers were read as search-engine extracts of the source pages, not the pages themselves. Each is tagged accordingly, and section 9 lists what to re-check before any of it is relied on.

**Planning assumptions used for the A$ figures** [all are assumptions, not evidence]: marginal tax rate 30% plus 2% Medicare; expected equity return 7% a year nominal (R11 uses 5–8%); cash rate near 4.2% (AAA and BILL returned 4.24% and 4.25% over the year to October 2026 [primary]); IBKR fixed commission max(A$6.60, 0.088%) as in RND-021; L1 in cash about 30% of the time (R15, one secondary source).

---

## 0. Answer in brief

1. **The largest gaps are not in the algorithm.** They are where the money sits (super against a personal account; debt against shares), which objective the system serves (growth or drawdown control), and what idle cash earns. Each is worth more than every ETF, fee and factor choice in this report combined.
2. **The spec is internally honest but aimed at a different goal from the owner's.** Section 30 already says L1 "is not expected to beat DHHF". For an owner whose stated goal is growth, the evidence-based default is STATIC mode (hold 40/60, no trend filter), with L1 run in paper. The spec has no place where the owner chooses between the two goals; it should.
3. **One defect found.** The trend literature that L1 rests on credits a cash return while out of the market, and R11's cost model for the candidate included a cash-ETF leg. v2.10 holds risk-off money at IBKR, which pays 0% on the first A$15,000 of AUD [1, extract]. L1 as specified is therefore about 1.2 points a year worse than the rule the evidence describes, before the fix in item 3.
4. **Nothing found adds reliable return without adding risk.** Factor tilts, small caps, emerging markets, equal weight, hedging, covered calls, geared funds, crypto and day trading are each assessed in sections 3 and 4. None earns a place in the live rule. Two cost-only changes do (cheaper ETFs; a later tranche threshold).

### Ranked summary (by expected impact)

| Rank | Gap | Impact at A$5k | Impact at A$50k | Recommendation |
| --- | --- | --- | --- | --- |
| 1 | Super vs personal account as the place for new savings (§2.1) | About +A$1,500 a year per A$6,000 saved at a 32% rate; +A$145 at 17%; one-off +A$850 on the first A$5,000 [computed] | Same per dollar contributed, plus roughly 0.5–1.0% a year lower tax on earnings [unverified estimate] | Owner guidance; question for a tax agent or adviser. Cost: no access until age 60 |
| 2 | Objective mismatch: growth owner, drawdown-overlay rule (§2.2) | About A$68 a year (1.35%) expected cost of L1 vs STATIC [computed from R11's model] | About A$675 a year | Live rule: add an owner objective decision; growth → STATIC live, L1 in paper. Card HG2 |
| 3 | Risk-off cash earns 0% (§2.3) | About +A$34 a year net (0.7%) if L1 runs | About +A$510 a year net (1.0%) | Tested card HG1 (AAA while a sleeve is OFF); close open item I9 now |
| 4 | Debt, offset and emergency cash come before this account (§2.4) | A$5,000 in a 6% mortgage offset saves A$300 a year, tax-free and risk-free; expected shares return after system costs is lower | Scales | Owner guidance |
| 5 | Stage 2 lowers expected return (§2.5) | None until about A$15–20k | About −A$500 to −A$700 a year expected if 45% leaves equities [unverified estimate] | Live rule: Stage 2 becomes an explicit owner risk choice, never automatic |
| 6 | Tax-aware operation under the 1 July 2027 law (§2.6) | A$10–25 a year | A$100–250 a year [R11 model: 0.3–0.5%] | `min_tax` parcel method (spec text); card HG3; reject automated loss harvesting |
| 7 | Tranche threshold triples minimum-commission orders (§2.7) | None at A$5k; about −A$53 a year (0.56%) at A$9,375 | About A$4 a year | Live rule: raise the N = 3 threshold to about A$25,000, tested in H5 |
| 8 | Owner reporting: money-weighted return, attribution, plain-English reasons, projections (§2.8) | Not estimable; the measured investor behaviour gap is about 1.2% a year [1] | Same | Spec text MON-09 to MON-12 |
| 9 | Cheaper ETFs for the same exposure: A200 and BGBL (§2.9) | +A$3.60 a year | +A$36 a year | Owner decision before G0 (spec text) |
| 10 | Contributions: lump sum, batching, direction (§2.10) | Up to A$20 a year from batching; about A$175 once if a 12-month drip-feed were chosen instead of a lump sum | Scales | Owner guidance; the A$1,000 minimum is already close to optimal |

Lower-ranked items (IBKR tiered pricing, Stage 3 US ETFs, allocation split, hedging, factor tilts, custody, estate) are in sections 3, 5 and 7.

---

## 1. What the spec already covers (so it is not re-listed as a gap)

- Benchmarks B1 (DHHF) and B2 (static 40/60) tracked daily and shown on every report (PRT-22, SYS-07, MON-04).
- Contributions directed to the underweight sleeve before any sell (RND-033, PRT-16(b)); automatic capital cap (PRT-19).
- Franking 45-day test and the A$5,000 exemption counter (TAX-07); parcel ledger with FIFO or HIFO (TAX-01); the 1 July 2027 regime (TAX-04 to TAX-06).
- A cash-ETF variant inside H10, off by default (PRT-18); a hedged paper variant V3 (PRT-24).
- Static factor sleeves allowed inside paper strategy P1 (SIZ-14).
- Stage thresholds (section 27); the expectations statement (section 30).

What follows is where those are missing, implicit, or point away from the owner's goal.

---

## 2. Material gaps, ranked

### 2.1 Super versus a personal account (rank 1)

**What the spec says.** Nothing. The words "superannuation" and "concessional" do not appear in the spec or in reports 11–21. The spec assumes a personal account and optimises inside it.

**Evidence.**

- Concessional (before-tax) contributions are taxed at 15% on entry; the general cap is A$32,500 for 2026–27, and employer contributions count toward it [2+: SuperGuide; Morningstar AU, via search]. Above A$250,000 of income, Division 293 lifts the entry tax to 30% [1].
- Earnings in accumulation phase are taxed at up to 15% [2+: Betashares; Peakifi, via search].
- The 2026 CGT reform applies to individuals, trusts and partnerships. Complying super funds keep their one-third discount; nothing changes at fund level on 1 July 2027 [2+: Corrs; Baker McKenzie; austax.tools, via search]. The reform therefore widened the gap in super's favour for capital growth.
- Resident rates for 2026–27: 15% from A$18,201, 30% from A$45,001, 37% from A$135,001, 45% from A$190,001, plus 2% Medicare [2+, secondary tables].
- Access is the cost. Money in super is preserved until retirement after age 60 [unverified this session: one search result gave 65; check the ATO]. The First Home Super Saver scheme is a partial exception [unverified].

**Impact** [computed]. For A$6,000 a year of take-home pay saved (A$500 a month):

| Marginal rate incl. Medicare | Pre-tax equivalent | Lands in super after 15% | Gain over A$6,000 outside |
| --- | --- | --- | --- |
| 17% | A$7,229 | A$6,145 | +A$145 (+2%) |
| 32% | A$8,824 | A$7,500 | +A$1,500 (+25%) |
| 39% | A$9,836 | A$8,361 | +A$2,361 (+39%) |
| 47% | A$11,321 | A$9,623 | +A$3,623 (+60%); +A$1,925 if Division 293 applies |

A personal deductible contribution of the first A$5,000 at a 32% rate is worth about A$850 once. On top of the entry advantage, earnings bear 15% (10% on discounted gains) instead of the marginal rate and, from 1 July 2027, the 30% minimum on capital gains outside super. I estimate that at 0.5–1.0% of the balance a year [unverified estimate].

No other item in this report comes within a factor of ten of this at a 32% rate.

**Trade-offs for the owner (not advice).**

- For: the entry-tax advantage is certain and immediate; the same VAS/VGS-type index exposure is available inside large funds at low fees [1]; no system to run.
- Against: no access before about age 60; rules can change; the cap is shared with employer contributions; this trading system cannot run inside a retail super fund (that needs an SMSF, which is uneconomic at this size [unverified]); at a 17% rate the advantage almost disappears.
- A personal account remains the right place for money needed before 60, and for the learning purpose in section 30.

**Recommendation: owner guidance, plus one tax-agent question.** No rule change. Proposed text:

> **Section 30, new row in "What matters more than the algorithm":** *Where the money sits.* Before-tax contributions to super are taxed at 15% on entry and earnings at up to 15%, and super funds keep their CGT discount after 1 July 2027. At a marginal rate of 30% or more, a dollar saved through super starts about 25% larger than the same dollar saved in this account [computed, report 33]. The price is no access until retirement after age 60. This system cannot run inside a retail super fund. The split between super and this account is the owner's decision and can matter more than anything this system does.
>
> **Section 21.2, new item T14:** For money I do not need before age 60, how do concessional contributions compare with this account at my income, cap room and Division 293 position? (Not blocking.)

### 2.2 The system's objective does not match the owner's (rank 2)

**What the spec says.** L1 is "a drawdown overlay, not a return source" (PRT-25) and "is expected to cost return" (§9.1). SYS-03 puts L1 live if H1, a drawdown test, passes. STATIC mode is the fallback only if H1 fails. No requirement asks the owner which goal the account serves.

**Evidence.**

- The spec's own planning numbers: gross edge about −0.5% a year (range −2% to +1%), extra CGT 0.6%, slippage 0.15%, lost franking 0.1% [R11 model, as quoted in §1]. Sum: about −1.35% a year against STATIC [computed].
- R14 and R15, as cited in the spec: about even odds of lagging buy-and-hold over any 5–10 years; expect to lag by 5–15% in strong bull years.
- The honest case for L1 is behavioural: an owner who would sell at −40% is better off with a rule that caps the fall near −25%. Morningstar's latest study puts the average investor's shortfall against their own funds at about 1.2 points a year, wider for volatile funds [1, extract]. That is the same size as L1's expected cost, so the choice is genuinely the owner's.

**Impact** [computed from R11's model]: about A$68 a year at A$5,000 and A$675 a year at A$50,000 in favour of STATIC, in expectation, with a deeper worst drawdown (plan for −35% to −50% instead of −25%).

**Recommendation: add to the live rule as an owner decision; one card.** Proposed text:

> **Section 21.1, new item O23 (blocks G0):** Choose the account objective. `growth`: the aim is the highest expected after-tax wealth; the account runs STATIC live and L1 in paper. `drawdown`: the aim is a shallower worst loss at an expected cost in return; the account may run L1 live if H1 passes. The default is `growth`.
>
> **PRT-10, add:** `L1` may be selected only if hypothesis H1 passed at gate G2, the owner approved it, **and `objective: drawdown` is set (O23)**. With `objective: growth` the live mode is `STATIC`, and L1 runs in the paper account so its record accumulates.
>
> **Section 18, `config/a.yaml`:** `objective: growth | drawdown` (no default in code; `trader init` refuses to run without it).

Card HG2 (section 8) lets a growth-objective owner see, once and pre-registered, whether L1 would have left more or less after-tax wealth with contributions.

### 2.3 Risk-off cash earns nothing (rank 3)

**What the spec says.** PRT-18: out-of-market money stays as AUD cash at IBKR; a cash ETF "only if IBKR pays about zero on small balances [unverified]"; off in v2.10. RND-021: cash earns "zero until I9 is answered". Open item I9 is unanswered.

**Evidence.**

- IBKR's AUD schedule pays 0% on the first A$15,000 and benchmark minus 0.5% (about 4.1%) above it; accounts with net asset value under US$100,000 receive only a proportional share of that rate [1: IBKR interest-rate pages, several regional copies, read as search extracts; the Australian host was blocked]. A A$5,000–50,000 account therefore earns nothing, or close to nothing, on idle cash.
- Cash ETFs on the ASX [primary, ASX report October 2026]: AAA, fee 0.18%, spread 0.02%, 1-year return 4.24%, A$636m traded in the month; BILL, fee 0.07%, spread 0.01%, 1-year return 4.25%; ISEC, fee 0.12%, 4.31%.
- The published trend rules behind L1 credit a Treasury-bill return while out of the market [unverified: model memory of Faber 2007; R14 has the citation]. R11's cost model for this candidate counted "6 ASX trades a year, including a cash ETF leg" [primary, R11 §2]. v2.10 dropped the leg, so the live rule is worse than the modelled one by the cash yield.

**Impact** [computed].

| | A$5,000 | A$50,000 |
| --- | --- | --- |
| Average cash (30% of NAV) | A$1,500 | A$15,000 |
| Yield forgone at 4.2% | A$63 a year | A$630 a year |
| Two extra commissions per round trip, one round trip per sleeve | −A$26 | −A$88 |
| Two extra days out of the market at re-entry (T+2 settlement) | −A$3 | −A$28 |
| **Net gain from parking in AAA** | **about +A$34 (0.7%)** | **about +A$510 (1.0%)** |

Break-even length of a risk-off spell: 60 days for a A$2,000 sleeve, 40 days for A$3,000, 16 days for A$20,000 or more [computed]. Shorter spells lose money, which is why this needs a rule and a test, not a switch.

Other idle cash is small: the 20-trading-day canary wait forgoes about A$28 of expected return once at A$5,000; distributions waiting for the A$1,000 minimum forgo a few dollars a year [computed].

**Costs not in the table.** AAA pays monthly, so DAT-14 distribution entry rises from quarterly to monthly for that symbol, and DAT-22 would block on a missing amount. One more symbol on the EODHD call budget (DAT-23). Interest is taxed at the marginal rate with no franking.

**Recommendation.** (a) Close I9 now with "0% below A$15,000" once the owner reads the IBKR page. (b) Promote the H10 cash-ETF variant to its own card, HG1 (section 8); adopt by spec change only if it passes. (c) Until then, state the cost plainly:

> **Section 1, expectations table, new row:** *Cash while a sleeve is OFF* — earns 0% at IBKR on balances under A$15,000 [1]. At a 4.2% cash rate and 30% of the time in cash this is about 1.2 points a year of NAV that the published trend evidence assumes the rule earns and L1 as built does not [computed, report 33]. Card HG1 tests a cash ETF.

This item is moot in STATIC mode, where almost no cash is held.

### 2.4 What should come before this account (rank 4)

**What the spec says.** Nothing on the owner's wider position.

**Evidence and arithmetic.** A dollar in a mortgage offset account saves the mortgage rate, tax-free and without risk. At a 6% mortgage rate [assumption] that is A$300 a year on A$5,000, equal to an 8.8% pre-tax return at a 32% rate [computed]. Expected return on A$5,000 in this system is about A$350 before tax (7%), less A$164–209 of fixed running costs, with a planned −25% drawdown. Card debt at 15–20% is a larger gap still. HELP debt is different: it is indexed at the lower of CPI and the Wage Price Index (about 2.8% in June 2026 [1]), below the expected return on shares. Regulator guidance on emergency cash and debt before investing was not fetched this session [unverified].

**Recommendation: owner guidance.** Proposed text:

> **Section 30, expectations statement, new point 8:** *First things.* I hold enough at-call cash for emergencies outside this account, and I have no debt costing more than about 6% a year. If I have a mortgage with an offset account, I understand that money in the offset earns the mortgage rate tax-free and without risk, and that at A$5,000 this system is not expected to beat that after its running costs.

### 2.5 Stage 2 is a de-risking step, not a growth step (rank 5)

**What the spec says.** Stage 2 (sizing NAV above about A$15–20k, H6, H12 and H13 passed) replaces L1 with P1: equities 55%, real assets 10%, bonds 25%, gold 10% (SIZ-14). H13 tests P1 against its own static mix V0, not against the all-equity benchmarks on wealth.

**Evidence.** Five-year returns to October 2026 [primary]: VAF (Australian bonds) 0.81% a year; VGS 12.37%; VAS 8.95%; gold (PMGOLD) 18.89%. One five-year window proves nothing about the future, but the long-run direction is not disputed: bonds have returned several points a year less than shares [unverified: long-run equity premium of 3–4 points from model memory]. Moving 45% of the account out of shares lowers expected return by roughly 1.0–1.4 points a year [unverified estimate], in exchange for a shallower drawdown. A growth owner adding A$500 a month for decades is the investor for whom that trade is least obviously right.

**Recommendation: add to the live rule.** Proposed text:

> **Section 27, Stage 2 entry conditions, add:** "…and `objective: drawdown` (O23), or the owner's written choice of a lower-risk mix recorded with `trader stage 2 --confirm`." With `objective: growth` the account stays all-equity at every size; what changes with size is cost, tranching (PRT-14) and the items in report 33 §5, not the asset mix.
>
> **H13, add a reported (not tested) line:** terminal after-tax wealth of P1 against B1 and B2 with A$500 monthly contributions, so the owner sees the expected price of the lower drawdown before choosing.

### 2.6 Tax-aware operation under the 1 July 2027 law (rank 6)

**What the spec says.** The tax engine records everything correctly (section 13) but the trade path ignores tax. TAX-01 offers FIFO or HIFO. A "tax-aware minimum holding period" is listed in §21.7 as an unregistered idea. T7 asks about wash sales.

**Evidence.**

- The Act is law (No. 49 of 2026). Gains accrued before 1 July 2027 keep the 50% discount; later gains get indexation; a 30% minimum applies to post-reform gains [2+: ATO reform page, Corrs, KPMG, via search]. Per R18, both the discount on the pre-July slice and indexation need the parcel held 12 months from actual acquisition.
- So a parcel L1 sells inside 12 months loses the discount on its pre-July slice and all indexation, and pays at least 30%. With about one round trip per sleeve a year, most L1 disposals are of that kind. R11 put the extra CGT at 0.6% a year before the reform and 0.3–0.5% after [R11 model].
- Wash sales: Australia has no statutory 30-day rule. TR 2008/1 applies Part IVA to selling and reacquiring "the same or substantially the same asset" where the dominant purpose is the tax benefit; shares in a competitor are not substantially the same [1: ATO ruling, search extract]. The ATO has said it uses data analytics to find wash sales [2+, secondary]. Whether two ETFs on different indexes of the same market (VAS and A200) are "substantially the same" is not settled in anything I could read [unverified].

**Assessment.**

- *Automated tax-loss harvesting: reject.* The benefit is deferral only, it is small at this size (a A$500 loss is worth at most A$160 of deferred tax), and a program whose stated purpose is the tax benefit is exactly what TR 2008/1 addresses. L1's own exits realise losses for a recorded non-tax reason (TAX-09); that is enough.
- *Parcel selection: improve.* Under the new law the best parcel to sell in a partial sale is not simply the highest-cost one: a parcel past its 12-month date carries indexation and a discountable pre-July slice; one at 11 months does not. HIFO ignores that boundary. This matters for band rebalances, withdrawals and tranche sells; with N = 1 transitions sell everything and it does not matter.
- *12-month-aware exits: test, do not assume.* Delaying a trend exit to cross a 12-month date trades tax for drawdown. Card HG3.
- *Existing holdings:* if the owner tags existing VAS or VGS as `managed` (O16), L1 can sell parcels that would otherwise have kept their discount on gains to 30 June 2027. `trader init` already prints the realised gain; it should also print this.

**Impact.** A$10–25 a year at A$5,000; A$100–250 a year at A$50,000 if L1 runs (R11's 0.3–0.5% range; the parcel method alone is a small part of it) [model]. Zero in STATIC mode with no withdrawals.

**Recommendation.** Proposed text:

> **TAX-01, add:** `parcel_method: min_tax` (optional; default stays FIFO until the tax agent confirms parcel identification, T15). For each sale it selects parcels in the order that gives the lowest estimated tax under the user's `TaxRegime` and marginal rate: loss parcels first, then parcels past their 12-month date by lowest taxable gain per unit after indexation and discount, then parcels inside 12 months by lowest gain per unit. The 45-day LIFO view (TAX-07) is unchanged.
>
> **Every plan, add:** for each planned sell, the estimated tax under the user's flags and, where a parcel is within 30 calendar days of its 12-month date, the date and the tax difference. Information only; it does not change the order.
>
> **Section 21.2, new item T15:** May I choose which parcels are sold where my records identify them, and is a lowest-tax selection acceptable? (Blocks `parcel_method: min_tax`.)
>
> **T7, add:** Is a switch between two ETFs on different indexes of the same market (for example VAS to A200) a wash sale under TR 2008/1 if done at a loss?

### 2.7 The tranche threshold triples small orders (rank 7)

**What the spec says.** PRT-14: three tranches once min(base weight) × sizing NAV ÷ 3 ≥ 1.25 × A$1,000, i.e. from A$9,375.

**Finding** [computed from RND-021's commission model, one round trip per sleeve a year].

| Sizing NAV | N = 1 commissions | N = 3 commissions | Extra cost of tranching |
| --- | --- | --- | --- |
| A$9,375 | A$26 (0.28%) | A$79 (0.84%) | 0.56% a year |
| A$20,000 | A$35 (0.18%) | A$79 (0.40%) | 0.22% |
| A$25,000 | A$44 (0.18%) | A$79 (0.32%) | 0.14% |
| A$30,000 | A$53 (0.18%) | A$79 (0.26%) | 0.09% |
| A$50,000 | A$88 (0.18%) | A$92 (0.18%) | 0.01% |

Tranching buys lower timing luck, not return (H5). Between A$9,375 and about A$25,000 it costs 0.15–0.56% a year in extra minimum commissions. H5's fail line mentions cost "at A$5,000", where N = 1 anyway; the cost bites at the switch point, which is not tested.

**Recommendation: add to the live rule through H5.**

> **PRT-14, change:** N = `tranches_max` only if min(base weight) × sizing NAV ÷ `tranches_max` ≥ **3.3** × `min_order_value_aud` (a sizing NAV of about A$25,000 at the defaults [computed]) [design value — set by backtest, card H5].
>
> **H5, add to the fail column:** "…or added commission at the NAV where N first becomes 3 exceeds 0.15% a year."

### 2.8 Owner reporting and explanation (rank 8)

**What the spec says.** MON-04: holdings, unit-price curve against B1 and B2, drawdown, latest plan, alerts, last 30 runs. Reason codes exist on every order. SYS-07 forbids implying a return advantage.

**Gaps.**

- The unit-price curve is time-weighted. With contributions ten times a month's return, the owner's own experience is the money-weighted return and the dollar balance. Neither is shown.
- No attribution. The owner cannot see *why* the account differs from "doing nothing": trend decisions, commissions, cash drag, tax, running costs.
- No plain-English reason with each decision. "votes = 0 → OFF" is a reason code, not an explanation.
- No after-tax, after-all-costs comparison, although the tax engine and cost ledger hold everything needed.
- No projection. Section 30 says contributions matter most, but nothing shows the owner what A$500 against A$700 a month does over ten years.
- Nothing on inflation; all figures are nominal.

**Evidence.** The investor return gap is about 1.2 points a year, and narrowest in funds that are simple and automatic [1: Morningstar, extract]. Households that traded most earned 11.4% a year against 17.9% for the market, 1991–96 [1: Barber and Odean 2000, abstract via search]. Reporting that shows the cost of each override, and does not prompt trades, is on the right side of both findings. "Opportunity alerts" that prompt discretionary buying are on the wrong side; the only alert consistent with the evidence is one that prompts a *contribution*.

**Recommendation: spec text.**

> **MON-09 Owner return.** Every monthly report and the dashboard show, for the live account, B1 and B2 over the same cash flows: the dollar balance; total contributed; the money-weighted return (XIRR) since inception and over 12 months; and the same after estimated tax (TAX-10 method) and after running costs entered under PRT-21. Real (CPI-deflated) figures are shown beside nominal ones using the `cpi` table.
>
> **MON-10 Attribution.** The monthly report splits the difference between the live account and B2 since inception, in dollars, into: trend decisions (each OFF spell: the sleeve's return while out, less cash earned); commissions; spread and slippage (RSK-26); cash drag outside OFF spells; estimated tax; fixed running costs. The parts sum to the total; any residual is shown as "unexplained".
>
> **MON-11 Decision note.** Each plan and digest carries one or two sentences per order built from fixed templates, for example: "Selling VGS: it is below its level of 6 and 12 months ago and below its 10-month average (0 of 3 votes). Last time this happened (date) the sleeve was out for N days and the decision gained/cost A$X against staying in." No model-generated text (SYS-06).
>
> **MON-12 Projection and contribution note.** The dashboard has a calculator that takes the current balance, a monthly contribution and a horizon and shows the balance at 3%, 5% and 7% real returns, with the share that comes from contributions. It runs no strategy. The digest adds one line when a contribution of a stated size would bring a sleeve back to target in one minimum order. Neither feature names any security outside the user's universe or suggests a trade outside the rule.
>
> **RND-011, add:** the dashboard exposes no strategy what-if on real data. Any backtest run from any interface is logged as a trial.

### 2.9 Cheaper ETFs for the same exposure (rank 9)

**What the spec says.** VAS 0.07% and VGS 0.18%, each "[one source]"; P3 asks for fee verification. No alternative was compared.

**Evidence** [primary, ASX Investment Products report, October 2026; fee, time-weighted spread, funds under management].

| Role | Ticker | Fee | Spread | FUM (A$m) | Note |
| --- | --- | --- | --- | --- | --- |
| Australian shares | VAS | 0.07% | 0.02% | 26,993 | S&P/ASX 300 |
| | A200 | 0.04% | 0.02% | 11,430 | Solactive Australia 200 |
| | IOZ / STW | 0.05% | 0.04% / 0.03% | 9,775 / 6,648 | S&P/ASX 200 |
| | A300 | 0.03% | 0.11% | 23 | Too small; spread fails SYS-30 |
| Global shares | VGS | 0.18% | 0.02% | 18,630 | MSCI World ex Australia |
| | BGBL | 0.08% | 0.02% | 5,664 | Developed ex Australia; no 5-year history |
| | IWLD | 0.09% | 0.04% | 1,931 | ESG-screened index |
| US only | IVV / VTS | 0.04% / 0.03% | 0.02% / 0.03% | 14,846 / 7,284 | VTS is US-domiciled |
| Global hedged | VGAD / HGBL | 0.21% / 0.11% | 0.02% / 0.03% | 7,907 / 3,030 | For paper variant V3 |
| All-in-one | DHHF / VDHG | 0.19% / 0.27% | 0.05% / 0.03% | 1,694 / 4,149 | DHHF is benchmark B1 |

This closes open item P3 for VAS, VGS and DHHF: all three fees are confirmed from a primary source.

**Assessment.**

- 40% A200 + 60% BGBL costs 0.064% against 0.136% for VAS + VGS: a saving of 0.072% a year [computed], A$3.60 at A$5,000 and A$36 at A$50,000. Both pass the SYS-30 spread limit. The exposure differs only at the margin (top 200 against top 300 Australian companies; a different developed-markets index provider).
- Against: BGBL has under five years of history (needed for the E2 distribution check and the proxy tax assumptions), and Betashares could reprice. A fee can be changed by the issuer at any time.
- IVV or VTS in place of VGS is not a fee decision. It is a bet on one country, at the end of a decade in which that country won (IVV 13.71% against VGS 12.37% over five years [primary]). Reject. VTS also brings W-8BEN paperwork and US-situs exposure (MKT-04).
- DHHF holds US-domiciled funds for part of its overseas exposure, which can trap some foreign withholding tax [1: Betashares on the mechanism; one forum source on DHHF]. That supports the spec's two-fund structure over a single fund, and is a caution about B1 as a benchmark: B1 carries a small tax leak the live account does not.
- Switching after go-live realises gains; the choice belongs before G0.

**Recommendation: owner decision before G0.**

> **Section 21.1, new item O24 (blocks G0):** Choose the live pair: VAS + VGS (default; longest history, largest funds) or A200 + BGBL (0.072% a year cheaper [computed]; BGBL listed 2023). Either way the proxies, base weights and every card are unchanged. A200 + BGBL needs: the E1/E2 EODHD checks on those tickers; three complete financial years of BGBL distributions before E2 can close (else VGS distributions stand in, stated in the card); the SYS-30 spread check.
>
> **Section 5, instruments table:** replace "[one source]" on the VAS, VGS and DHHF fees with "[ASX report, October 2026]". Paper variant V3 uses HGBL (0.11%), not VGAD (0.21%).

### 2.10 Contributions: lump sum, batching, direction (rank 10)

**What the spec says.** Contributions are committed automatically and directed to the underweight sleeve (PRT-16(b), PRT-19); the A$1,000 minimum order; O7 notes larger, rarer contributions cost less per dollar. Lump sum against drip-feeding is not discussed.

**Evidence.** Vanguard's 2012 study: investing a lump sum at once beat spreading it over 12 months in about two-thirds of rolling periods; for Australia 1984–2011, 62% for all-equity and 66% for 60/40 [1: Vanguard paper, read as extract]. A drip-feed is a decision to hold cash, and at IBKR that cash earns 0% (§2.3), which makes it worse here than in the study.

**Arithmetic** [computed]. Yearly cost of batching a monthly contribution c into one order every n months = (12 ÷ n) × A$6.60 + c × 7% × (n − 1) ÷ 2.

| Monthly contribution | Cheapest batch | Yearly cost | Cost of investing every month |
| --- | --- | --- | --- |
| A$250 | every 3–4 months | A$44–46 | not allowed (below the minimum) |
| A$500 | every 2 months | A$57 | A$79 |
| A$1,000 | every 1–2 months | A$75–79 | A$79 |
| A$2,000 | every month | A$79 | A$79 |

The A$1,000 minimum order is within a few dollars of optimal across this range. No change. Spreading the initial A$5,000 over 12 months instead of investing at go-live would forgo about A$175 in expectation [computed: half the balance idle for a year at 7%].

**Assessment.** The spec's behaviour (deploy in full after the canary period if the trend is ON; top up when cash reaches the minimum) matches the evidence. Two additions are worth stating: do not hold contributions back to "wait for a dip" (report 31 covers the evidence on falls); and commission on contributions, about 1% of each dollar at A$500 a month, is the price of using IBKR's API and cannot be avoided inside D1.

**Recommendation: owner guidance; no rule change.**

> **O7, add:** Contributions are invested as soon as cash reaches the minimum order; the system never waits for a better price. At A$250–1,000 a month the A$1,000 minimum is within a few dollars a year of the cheapest batching [computed, report 33].

---

## 3. Lower-impact items and things the evidence does not support

### 3.1 Allocation split (40/60)

- Five years to October 2026: VAS 8.95%, VGS 12.37% [primary]. Thirty years to June 2024: Australian 9.1%, international 8.2% [1, R12]. The sign flips with the window; nothing predicts the next one.
- Franking is the measurable reason for an Australian overweight. VAS's distribution yield is 3.13% [primary]; at about 75% franking [unverified] the credits are about 1.0% a year on the Australian sleeve, 0.4% of the whole account: A$20 a year at A$5,000, A$200 at A$50,000 [computed]. These are safe under L1 only if the A$5,000 exemption covers a trust (T3, still open).
- **Recommendation: no change.** 40/60 is inside the defensible range. A different split is a new card under SYS-31 and I can find no evidence that would let such a card pass.

### 3.2 Small caps, emerging markets, equal weight

Five-year returns to October 2026 [primary]: Small Ordinaries accumulation index 0.64% a year against 8.00% for the ASX 200; VSO 5.39% (fee 0.30%); VISM 8.10% (0.32%); VGE 5.52% (0.48%); MVW equal weight 7.65% (0.35%) against VAS 8.95%. Longer studies also find no Australian small-cap index premium [2+, secondary: Morningstar AU; Leithner]. About 60% of active Australian small-cap funds still lagged their index over 15 years, the lowest rate of any category [1]. **Reject for live.** Each adds a sleeve below the economic order size, a higher fee, and no evidenced premium.

### 3.3 Value and quality tilts

- Academic premia are real in long-short portfolios before costs, but returns to published predictors fell 58% after publication [1: McLean and Pontiff 2016], and US smart-beta indexes went from about +3% a year in backtest to a CAPM alpha of −0.44% a year after their ETFs listed [1: Huang, Song and Xiang 2024].
- The ASX record shows rotation, not persistence [primary, 5 years]: VLUE 18.74% and VVLU 14.96% beat VGS 12.37%; QUAL 11.65% and QLTY 9.27% lost to it. Five years earlier the ranking was the other way round [unverified].
- Fees: 0.28–0.40% against 0.08–0.18%.
- The registry's return bar (t ≥ 3.0) cannot be met by a long-only tilt on 34 years of data, by the spec's own arithmetic (§24).
- **Reject for live. Keep as static sleeves inside paper P1 (SIZ-14), no timing.** Report 31 covers momentum and quality-growth vehicles in detail; nothing here changes its conclusion.

### 3.4 Currency hedging

R12 and R15 already settle it: long-run hedged and unhedged returns are close; it is a risk choice. **No change**; V3 stays a paper variant, on HGBL.

### 3.5 Cost items

- **IBKR tiered against fixed.** Tiered has an A$5 minimum against A$6, plus pass-through exchange fees [2+, R21]. The most it can save is A$1.10 an order while orders are under A$7,500: about A$5–11 a year at A$5,000, nothing at A$50,000 [computed]. The pass-through fees were not quantified [unverified]. **Owner guidance:** read the plan (O11) and leave it unless the first statements show tiered is cheaper.
- **Fixed running costs** (A$164–209 a year) are 3.3–4.2% of A$5,000 and remain the largest known drag until about A$30,000. The spec says so. The only lever is scale, which is §2.1 and §2.10 again.

---

## 4. Things that sound good and the evidence says to avoid

| Idea | Evidence | Verdict |
| --- | --- | --- |
| Selling options for income (covered calls, buy-write funds) | UMAX returned 11.14% a year over five years against 13.71% for IVV; JEPI 6.75% over three years against 19.71% [primary]. The US buy-write index compounded at 8.5% against 11.2% for the S&P 500 since 1986 [1, secondary]. It caps the upside, which is the opposite of capturing big winners, and the income is taxed without discount | **Reject.** Lower return for lower volatility; not a growth tool |
| Geared and leveraged ETFs | GEAR (fee 0.78%) returned 14.34% a year over five years against 9.58% for A200; GGUS 12.37% against 13.71% for unhedged IVV [primary]. GHHF (30–40% geared) has existed only since April 2024; its interest and fees cost 3.38% a year to June 2025 [1, issuer]. Gearing magnifies falls by more than it magnifies gains over a full cycle, and a five-year bull run is not evidence of an edge | **Reject for the system** (D4 stands). It is more risk, not more skill. If the owner ever wants more risk, it needs its own card and a decision outside this audit |
| Day trading | Under 1% of Taiwanese day traders were reliably profitable after costs; 3% of persistent Brazilian day traders made money [2+: Barber et al.; Chague et al.] | **Reject.** Already out of scope; report 32 covers frequency |
| CFDs and margin FX | 68% of retail CFD clients lost money in FY2024 [spec, MKT-03] | **Reject.** Already excluded |
| Crypto | No cash flows to value; no primary evidence read in any report; each disposal is a CGT event with the 30% floor (R18) | **Reject for the system.** MKT-05 stands |
| Picking active funds or stocks | 85–87% of Australian equity funds and 96% of global equity funds lagged their index over 15 years [2+: SPIVA, secondary coverage] | **Reject.** The index core is the evidence-based choice; report 31 covers single stocks |
| "Opportunity" alerts | The most active households lagged the market by 6.5 points a year [1: Barber and Odean 2000] | **Reject** as trade prompts; allow only the contribution note in MON-12 |
| Waiting for a dip with new money | Lump sum beat drip-feeding about two-thirds of the time [1] | **Reject.** Invest on arrival (§2.10) |
| US-only or Nasdaq tilt (IVV, NDQ) | A concentration bet after the fact; VGS is already mostly US shares [unverified] | **Reject** |

---

## 5. Growth path: what changes as the account grows

| Sizing NAV | What v2.10 does | What this audit finds | Recommendation |
| --- | --- | --- | --- |
| A$5,000 | L1 or STATIC, N = 1; fixed costs 3.3–4.2% | The account is a seed. Contributions, §2.1 and §2.4 dominate | Set `objective` (O23); choose ETFs (O24) |
| A$9,375 | N becomes 3 | Tranching costs 0.56% a year here (§2.7) | Move the switch to about A$25,000 |
| A$15,000 | — | Fixed costs fall to 1.1–1.4%; IBKR still pays nothing on cash | — |
| A$15–20k | Stage 2: P1 with bonds and gold | Lowers expected return (§2.5) | Owner risk choice only; growth objective stays all-equity |
| A$25,000 | Stage 3 may open: US-listed ETFs; cost kill criterion starts | The fee case has gone: BGBL at 0.08% and IVV at 0.04% trade on the ASX. VTS at 0.03% would save about A$15 a year on A$30,000 against BGBL, against FX costs, Division 775 records, a tax agent's fee and US-situs exposure [computed] | Keep USE-02 (no US strategy without a card) and add: "a fee saving alone is not a reason" |
| A$50,000 | — | Commission is 0.088% on most orders; fixed costs 0.3–0.4%; the cash-ETF fix is worth about A$510 a year; `min_tax` parcels start to matter | HG1 and TAX-01 change should be decided by here |
| A$100,000 | — | All holdings sit with one custodian (§7); super comparison still dominates at the margin | Owner review of custody concentration; no rule change |

**Are the thresholds right?** Stage 2's A$15–20k follows from order-size economics and is reasonable for an owner who wants it. The N = 3 threshold is too low (§2.7). Stage 3's A$25,000 is not wrong, but its rationale in R11 (cheaper US funds) no longer holds.

> **USE-02, add:** A lower management fee is not sufficient reason for a US venue: ASX-listed funds now offer the same exposures at 0.03–0.08% [ASX report, October 2026].

---

## 6. Owner features: summary of what to add

Covered in §2.8 (MON-09 to MON-12). In one list: money-weighted and after-tax results beside both benchmarks; a dollar attribution of the difference; a templated sentence explaining each order with the outcome of the last similar decision; a contribution projection; a contribution-sized top-up note. What not to add: strategy what-ifs on real data (they are untracked trials), any alert that suggests a trade outside the rule, any model-written text on the trade path.

---

## 7. Other blind spots

- **Custody.** IBKR Australia holds ASX shares in a custody account (sub-custodian BNP), not on a personal HIN; client money is held on trust [1: IBKR Australia, extract; R21 noted this from one snippet]. This is normal for the broker and not a reason to change D1, but the spec never tells the owner, and at A$100,000 it is a single-custodian concentration. *Owner guidance: add one sentence to section 30 point 7.*
- **If the owner cannot act.** The system keeps trading if the owner is ill or dies; halts need the owner's second factor to clear. O20 covers key recovery, not a successor. *Owner guidance: a one-page "how to stop it and where everything is" note for a trusted person, stored with the O20 materials.*
- **Tax file number.** Distributions paid without a TFN on file suffer withholding at the top rate [unverified]. *Add to the "Before G4" checks: confirm the TFN is recorded with IBKR.*
- **Whose name.** Income taxed in a lower-rate partner's name is taxed less, though the 30% minimum now narrows that for capital gains. This is a tax-agent question, not a system one. *Fold into T5.*
- **Existing holdings and the discount** (§2.6): `trader init` should say that tagging old parcels `managed` exposes their pre-July-2027 discount to L1 sells.
- **B1 is a slightly unfair benchmark in the system's favour** if DHHF's structure leaks withholding tax (§2.9), and against it on fees after a switch to A200 + BGBL. B2 is the cleaner comparison; reports should lead with B2.
- **Distribution reinvestment** is off (SYS-24), correctly, but at A$5,000 with no contributions about A$150 a year of distributions would wait a long time for the A$1,000 minimum. With monthly contributions this disappears. *No change; O7 should say that an account with no contributions will carry growing idle cash.*

---

## 8. Hypothesis cards (RND-010 format)

IDs are provisional (HG = "gap audit") to avoid clashing with H14–H17 in report 31 and any IDs in report 32; renumber at registration. All thresholds are [design value — set by backtest] and frozen before the first run.

### HG1 — Cash ETF while a sleeve is OFF

| Field | Value |
| --- | --- |
| ID / date registered / card hash | HG1 / at freeze / at freeze |
| Economic rationale | IBKR pays 0% on AUD balances under A$15,000 [1]. The trend evidence assumes cash earns the bill rate. A cash ETF restores that at the cost of two commissions and a settlement delay per round trip |
| Exact rule | L1 exactly as §9.1, plus: when a sleeve's target weight falls to zero and its sale has settled, buy AAA with the settled proceeds if they are at least `min_order_value_aud`. When any tranche of that sleeve turns ON, sell the matching share of AAA on the execution date and buy the sleeve on the first trading day the proceeds are settled. AAA is never bought with contribution cash that an ON sleeve can absorb. AAA units are ignored by the votes and by the band |
| Fixed parameters | Instrument AAA (fee 0.18%, spread 0.02% [ASX report, October 2026]); commissions and slippage per RND-021; settlement T+2; N = 1, offset `last` |
| Permitted perturbation grid | Instrument BILL; minimum parked amount A$1,000 / A$2,000 / A$5,000; "park only from the second consecutive OFF evaluation" |
| Data and proxy map | AAA total return from listing; before that, RBA cash rate target compounded monthly less 0.18% a year. Sleeves as H1 |
| Sample and holdout | As H1: 1990-01 to 2023-12 development; 2024-01 onward holdout |
| Benchmark | L1 with cash at 0% (the v2.10 rule) |
| Primary metric (one) | After-tax, after-cost CAGR difference at sizing NAV A$5,000 with A$500 monthly contributions |
| Secondary metrics | The same at A$50,000 with no contributions; maximum drawdown difference; count and mean length of OFF spells; share of spells shorter than break-even; days out of the market at re-entry |
| Pass / fail | Pass: ≥ +0.25 pp a year at A$5,000 **and** ≥ +0.50 pp at A$50,000 **and** maximum drawdown no more than 0.5 pp worse. Fail: below +0.10 pp at A$5,000. Between: not passed (RND-015) |
| Family and adjustment | A, design choice decided by threshold, no significance test (as H4, H10) |
| Trials consumed / result / decision / approver | At run / — / adoption needs a spec change to PRT-18, DAT-14 (monthly distributions) and DAT-23 (call budget) / owner |

### HG2 — Does L1 leave a growth-objective owner richer?

| Field | Value |
| --- | --- |
| ID / date registered / card hash | HG2 / at freeze / at freeze |
| Economic rationale | O23 makes STATIC the default for a growth objective. This card records, once, what L1 would have done to after-tax wealth for an investor who contributes monthly, so the default is tested and not assumed |
| Exact rule | L1 exactly as §9.1 (and, if HG1 has passed, with HG1), N = 1, offset `last` |
| Fixed parameters | Start A$5,000; A$500 a month, raised yearly with CPI; marginal rate 30% plus Medicare; both CGT regimes (RND-022); costs per RND-021; cash at 0% |
| Permitted perturbation grid | Contribution A$250 / A$1,000; marginal rates of H11; twelve start months |
| Data and proxy map | As H1 |
| Sample and holdout | As H1 |
| Benchmark | B2 (STATIC) with the same flows |
| Primary metric (one) | Ratio of after-tax terminal wealth, L1 ÷ B2, median across the twelve start months |
| Secondary metrics | Share of rolling 10-year windows in which L1 ends ahead; maximum drawdown of each in dollars; worst 10-year ratio |
| Pass / fail | Pass (L1 may be offered to a growth-objective owner): ratio ≥ 1.00 and L1 ahead in at least half of rolling 10-year windows. Fail: ratio < 0.97. Between: not passed; growth-objective accounts stay STATIC |
| Family and adjustment | A (control, like H2). A pass makes no return claim (PRT-25) and triggers the H2 look-ahead audit if the ratio exceeds 1.05 |
| Trials consumed / result / decision / approver | At run / — / sets the O23 default wording only / owner |

### HG3 — 12-month-aware exits

| Field | Value |
| --- | --- |
| ID / date registered / card hash | HG3 / at freeze / at freeze |
| Economic rationale | From 1 July 2027 a parcel sold inside 12 months gets no indexation and no discount on any pre-July slice (R18). A short delay to cross the date saves tax and costs drawdown protection. §21.7 lists this as an unregistered idea from R11 |
| Exact rule | L1 as §9.1, except: on an OFF transition, units in parcels whose 12-month date falls on or before the next evaluation date, and whose estimated tax saving from waiting exceeds 0.5% of their value, are held and sold on the first execution date after their 12-month date, unless the sleeve has turned ON again. All other units sell as normal |
| Fixed parameters | Marginal rate 30% plus Medicare; post-July-2027 regime; CPI per T9 setting (b); N = 1 |
| Permitted perturbation grid | Tax-saving threshold 0.25% / 1.0%; window of one or two evaluations; pre-reform regime as a control |
| Data and proxy map | As H1, with the section 25 tax model |
| Sample and holdout | As H1 |
| Benchmark | L1 unmodified, after tax |
| Primary metric (one) | After-tax CAGR difference at A$50,000 |
| Secondary metrics | Maximum drawdown difference; number of deferred sells; worst loss on a deferred parcel during its deferral |
| Pass / fail | Pass: ≥ +0.20 pp a year with maximum drawdown no more than 2 pp worse and H1 still passing with the change. Fail: drawdown more than 4 pp worse, or H1 no longer passes |
| Family and adjustment | A, design choice by threshold |
| Trials consumed / result / decision / approver | At run / — / spec change to PRT-16(a) if passed / owner, after T2 and T9 are answered |

No card is proposed for factor tilts, small caps, emerging markets, hedging or a different base split: I found no evidence that would let one pass, and each run would spend a trial for nothing. No card is needed for the ETF choice (O24) or the tranche threshold (it amends H5).

---

## 9. What could be wrong, and what to re-check

- **IBKR interest tiers** were read as search extracts of IBKR's own pages; the Australian page was blocked. The owner should read the AUD row on IBKR Australia's interest page and close I9. If IBKR pays a material rate on small AUD balances, §2.3 shrinks to nothing.
- **Super figures** (cap, Division 293, preservation age, earnings tax) are from secondary sites via search. The arithmetic in §2.1 is mine and assumes the contribution is deductible and within the cap. A tax agent or adviser must check it against the owner's facts.
- **TR 2008/1** was read as an extract. The ETF-swap question is open.
- **The 1.35% expected cost of L1** is R11's model, not evidence; the spec says so too. If L1's true gross edge is at the top of R11's range (+1%), L1 and STATIC are about level before the cash fix and L1 is ahead after it.
- **The 30% time-in-cash figure** rests on one secondary source (R15). HG1's secondary metrics measure it.
- **Franking percentage for VAS** (75%) is from memory; the yield is primary.
- **Five-year ETF returns** are one window ending October 2026 and are used only to show that no tilt has been persistent, never as a forecast.
- **Vanguard's lump-sum study** predates 2012; a 2023 update is reported with similar figures but I could not read it.
- **Mortgage rate of 6%** is an assumption; the owner's own rate replaces it.
- **Hosts to allow for a re-check:** ato.gov.au, interactivebrokers.com.au, vanguard.com.au, betashares.com.au, spglobal.com.

---

## 10. Consolidated list of proposed spec changes

| Where | Change | From section |
| --- | --- | --- |
| §18 config; PRT-10; O23 | `objective: growth | drawdown`; growth → STATIC live, L1 paper | 2.2 |
| §1 expectations table; PRT-18; I9 | State the 0% cash cost; close I9; card HG1 | 2.3 |
| §27 Stage 2; H13 | Stage 2 needs `objective: drawdown` or a written risk choice; report wealth against B1/B2 | 2.5 |
| TAX-01; plans; T7; T15 | `parcel_method: min_tax`; tax and 12-month date on each planned sell; two tax-agent questions | 2.6 |
| PRT-14; H5 | N = 3 from about A$25,000 (multiplier 3.3); cost test at the switch point | 2.7 |
| MON-09 to MON-12; RND-011 | Owner return, attribution, decision note, projection | 2.8 |
| §5 table; O24; P3 | Fees confirmed; A200 + BGBL option; HGBL for V3 | 2.9 |
| O7 | Invest on arrival; batching note | 2.10 |
| §30 | Rows and points on super, first things, custody | 2.1, 2.4, 7 |
| T14; T5 | Super comparison; whose name | 2.1, 7 |
| USE-02 | A fee saving alone is not a reason for a US venue | 5 |
| "Before G4" checks | TFN recorded with IBKR; successor note stored with O20 | 7 |
| Cards | HG1, HG2, HG3 | 8 |

---

## 11. Sources

**Read in full (primary)**

- ASX Investment Products report, October 2026 (period ending 30 October 2026): [PDF](https://www.asx.com.au/content/dam/asx/issuers/asx-investment-products-reports/2026/pdf/asx-investment-products-oct-2026.pdf). Fees, spreads, funds under management, distribution yields and 1-, 3- and 5-year returns for every ETF named.
- FD_FINAL.md v2.10 and reports 11, 12, 13, 15, 18, 21 in this folder.

**Read as search extracts (host blocked or paper behind a publisher)**

- IBKR interest rates: [interactivebrokers.com.au](https://www.interactivebrokers.com.au/en/accounts/fees/pricing-interest-rates.php?menu=B); [regional copy](https://investors.interactivebrokers.com/en/accounts/fees/pricing-interest-rates.php).
- IBKR Australia client protection: [interactivebrokers.com.au](https://www.interactivebrokers.com.au/en/general/security-investor-protection.php).
- ATO, capital gains tax reform: [ato.gov.au](https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/capital-gains-tax-reform); [Corrs](https://www.corrs.com.au/insights/capital-gains-tax-and-negative-gearing-amendments-key-changes-and-implications); [Baker McKenzie](https://www.bakermckenzie.com/en/insight/publications/2026/07/australia-major-changes-to-cgt-and-negative-gearing); [KPMG](https://kpmg.com/us/en/taxnewsflash/news/2026/06/australia-capital-gains-tax-reform.html); [austax.tools on super funds](https://austax.tools/tax-insights/cgt-discount-reform-smsf-super-2027/).
- ATO TR 2008/1 (wash sales): [PDF](https://www.ato.gov.au/law/view/pdf/pbr/tr2008-001.pdf); commentary: [InvestSMART](https://www.investsmart.com.au/investment-news/why-the-atos-interested-in-wash-sales-all-year-round/151454); [Bentleys](https://www.bentleys.com.au/insights/are-wash-sales-a-capital-idea-the-ato-doesnt-think-so/).
- Super caps and rates: [SuperGuide](https://www.superguide.com.au/superannuation-topics/concessional-contributions-cap); [Morningstar AU](https://www.morningstar.com.au/retirement/key-changes-202627-super-thresholds); [Betashares, super or invest](https://www.betashares.com.au/insights/contribute-to-super-or-invest/); [Peakifi](https://peakifi.com/superannuation/strategies/salary-sacrifice-vs-investing/).
- Resident tax rates 2026–27: [SuperGuide](https://www.superguide.com.au/how-super-works/income-tax-rates-brackets); [austax.tools tables](https://austax.tools/tax-tables-2026-27-australia/).
- Vanguard (2012), "Dollar-cost averaging just means taking risk later": [copy](https://militarymoneymanual.com/wp-content/uploads/2021/08/Dollar-Cost-Averaging-Just-Means-Taking-Risk-Later-Vanguard.pdf).
- Morningstar, Mind the Gap 2025: [morningstar.com](https://www.morningstar.com/business/insights/research/mind-the-gap-2025).
- Barber and Odean (2000), "Trading Is Hazardous to Your Wealth", Journal of Finance 55(2): [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:55:y:2000:i:2:p:773-806).
- Barber, Lee, Liu and Odean, day trading in Taiwan: [Berkeley](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf). Chague, De-Losso and Giovannetti, "Day Trading for a Living?": [Quantpedia summary](https://quantpedia.com/retail-day-trading-is-an-uphill-battle/).
- McLean and Pontiff (2016), Journal of Finance: [copy](https://www.gwern.net/doc/economics/2016-mclean.pdf).
- Huang, Song and Xiang (2024), "The Smart Beta Mirage", JFQA 59(6): [RePEc](https://ideas.repec.org/a/cup/jfinqa/v59y2024i6p2515-2546_2.html).
- SPIVA Australia, year-end 2025: [S&P](https://www.spglobal.com/spdji/en/spiva/article/spiva-australia-year-end-2025/); [Investor Daily](https://www.investordaily.com.au/markets/57821-long-term-fund-underperformance-driving-etf-adoption).
- Covered calls: [First Trust, update on covered call returns](https://www.ftportfolios.com/Commentary/MarketCommentary/2026/3/24/an-update-on-covered-call-returns).
- Geared funds: [Betashares GHHF FY25](https://www.betashares.com.au/insights/ghhf-performance-fy25/); [Morningstar AU](https://www.morningstar.com.au/personal-finance/young-invested-why-these-etfs-might-require-caution).
- Foreign-domiciled ETF tax drag: [Betashares](https://www.betashares.com.au/insights/watch-out-for-tax-drag-when-investing-in-foreign-domiciled-etfs/); [Pearler forum on DHHF](https://pearler.com/explore/ask/exchange/choosing-investments/dhhf-vs-vdhg-102).
- Australian small caps: [Morningstar AU](https://www.morningstar.com.au/stocks/should-you-invest-in-small-caps); [Livewire](https://www.livewiremarkets.com/wires/the-myth-of-small-cap-outperformance).
- HELP indexation: [Study Assist](https://www.studyassist.gov.au/node/253).
