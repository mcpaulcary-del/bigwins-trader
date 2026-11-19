# 41. Strategic review of the whole programme: are we on the right track?

Report 41, 13 November 2026. Independent review. General information only: not financial, tax or legal advice.

**What I read.** `FD_FINAL.md` (v2.10: 2,147 lines, about 64,000 words, about 270 requirement IDs, 66 open items, 45 "[unverified]" tags); `How_the_trading_system_works.md`; reports 31–35 in detail; reports 11–30 at summary level; the `asx-trader` repository (read-only).

**What I could not read.** Reports 36–39 did not exist when this was written (checked twice). Two of them (36 real-data backtest of L1, 37 primary-source verification) bear directly on conclusions below; where a conclusion depends on them, it says so. Report 40 (profit-claims audit) appeared as this was being finished and was read at summary level. It agrees with this review: no retail-accessible method reliably beats the index, the system has no track record and makes no return claim, and at A$5,000 a zero-brokerage account gets the same return with less work. It adds three more cards (H60–H62).

**Tags.** [spec] and [Rnn] are figures taken from the spec or a report. [computed] is my arithmetic on those figures. [my estimate] is my judgment with no source. I ran no backtest and fetched no web page. I cannot independently confirm the 2026 CGT Act; I take it as the reports state it and rely on report 37.

---

## 0. Verdict

**Overall: adjust. The evidence work is honest and mostly right. The programme built on top of it is aimed at the wrong goal, is out of proportion to A$5,000, and is at real risk of never trading.**

| Area | Verdict | One-line reason |
| --- | --- | --- |
| 1. Goal fit | **Wrong track as framed** | The owner asked for growth. The system is a drawdown overlay that its own spec says costs return. Nobody has asked the owner to choose |
| 2. Strategy: core | **Right track** | Low-cost index core, no stock picking, no AI in the trade path. This is what the evidence supports |
| 2. Strategy: L1 as the live default | **Adjust** | Drawdown protection is worth least to a small account with contributions ahead of it. Make static the default; L1 opt-in |
| 2. Research agenda | **Adjust** | Too much searching for algorithms that the programme's own rules cannot adopt; too little closing of facts only a test can settle |
| 3. Process | **Adjust** | Right principles, too much ceremony. Nearly 40 hypothesis cards for a two-fund account |
| 4. Engineering | **Adjust, urgent** | Ten spec versions and nine reviews; the code is still an M0 skeleton written for the abandoned v1.2 share design |
| 5. Economics | **Wrong track at A$5,000 live; defensible from about A$50,000** | In expected dollars the system never pays for itself against DHHF, by the programme's own numbers |
| 6. Risk control inside the design | **Right track** | Reconciliation, halts, canary, cash account: sound. The risks that remain are outside the code |

The three things the owner should hear first:

1. **The programme's own research says no algorithm will make more money than buying DHHF and leaving it.** Five reports reached this independently (11, 31, 33, 34, 35). It is the main finding, and the owner's brief ("make as much money as the evidence allows") has not been reconciled with it. The levers that do make more money are outside the algorithm: how much is contributed, where it sits (super or personal), debt, cost and tax.
2. **As specified, the likely end state is an expensive way to hold two index funds.** If the owner picks growth (report 33's default), or the backtest gate fails, the account runs static 40/60. A zero-brokerage auto-invest account does that for A$0 against A$204–288 a year here [R34].
3. **"Fully automated" is not what has been specified.** The owner approves a broker login on his phone every order day, enters distributions before every ex-date, enters spread figures monthly and runs drills quarterly [spec §17]. An auto-invest account is more automated than this system.

---

## 1. Goal fit

### 1.1 Owner goals against what is being built

| Owner goal | What the programme delivers | Fit |
| --- | --- | --- |
| Make as much money as the evidence allows | A rule expected to return about 1.35 points a year less than doing nothing [R33, computed from R11], plus fixed costs of 3.3–4.2% at A$5,000 [spec §1] | **Poor** |
| "Does it all", automated | Automated orders, but recurring manual jobs and a phone approval per order day | **Partial** |
| Learns and gets better | Parameters are never tuned from live results [spec]; no return idea can pass the adoption bar (section 3.2) | **Poor as the owner means it; correct as the evidence means it** |
| No fuck ups | Very thorough controls. But every control is more code that can fail, and one person maintains it | **Good in design; unproven** |
| Doesn't miss big winners | A cap-weighted index holds every one of them, at index weight [R31] | **Met, but not in the sense the owner means** |
| The algorithm is the strongest part | The algorithm is three yes/no votes a month. The strongest parts are the safety and record-keeping | **Mismatch of expectations** |
| Done properly, not redone | The spec was rewritten ten times in one day and reports 31–35 already propose about 60 further changes | **At risk** |

### 1.2 The tensions

**Growth against the trend overlay.** L1 is a form of insurance. Its premium is paid in every bull year (expect to lag by 5–15% [spec §1]). Its payout is a shallower fall in a long bear market. An owner who wants maximum expected wealth does not buy this insurance. Report 33 said so and proposed an `objective: growth | drawdown` switch. I agree, and go further in 1.3.

**A$5,000 against the running cost.** Fixed costs of A$164–209 a year are 3.3–4.2% of the account. Long-run equity returns are planned at 5–8% [spec]. More than half the expected return is spent before the rule's own drag.

**"Doesn't miss winners" against an index.** Report 31 is right that the index cannot miss a listed winner and that nothing can hold a big weight before the win without prediction. But the owner will still watch one stock triple while his account moves 0.3%. That is a behavioural risk (section 6), and no report gives him an outlet for it.

**"Learns" against validation.** A monthly rule produces about 12 observations a year. The spec correctly says nothing about performance can be learned in under decades [spec §16]. So the system cannot learn in the sense the owner means. What it can improve is cost assumptions, operations and reporting. This should be said to the owner in those words.

### 1.3 A point the reports have not made: this owner is an accumulator

A A$5,000 account with A$500 a month going in is about A$43,000 after five years and A$97,000 after ten at 7% a year [computed]. Almost all of the final balance is money not yet contributed.

- A 50% fall on A$5,000 is A$2,500: five months of contributions.
- A fall early in the accumulation years is good for the final result, because later contributions buy at lower prices.
- Drawdown protection is worth most when the balance is large against future contributions, and close to being spent.

So L1 is aimed at the stage of life where it helps least. That does not make it wrong for ever. It makes it wrong as the live default now. The only strong argument for it at this stage is behavioural: an owner who would sell everything at −40% is better off with a rule that stops at −25%. Whether that describes this owner is something only he can say.

### 1.4 What the owner should decide explicitly

None of these is in the spec's open-items list as a decision. All of them outrank every item that is.

| # | Decision | Why it matters | Default if he does not decide |
| --- | --- | --- | --- |
| D-A | **Objective: growth or drawdown control** | Decides static against L1 | Growth → static |
| D-B | **Why build this: wealth, learning/hobby, or a platform for a larger account later** | If wealth only, do not run it live at A$5,000. If learning or platform, the costs are tuition and that is legitimate | Must be answered; no default |
| D-C | **Contribution plan** (amount, standing transfer, yearly increase) | Worth more than every algorithm choice combined [R34: two missed A$500 contributions a year is about A$12,900 over ten years] | A$500 a month by standing transfer |
| D-D | **Super or personal for money not needed before 60** | About +25% on each dollar at a 32% marginal rate [R33, computed]. The largest single number in the whole programme | Ask a tax agent or adviser |
| D-E | **Debt, offset and emergency cash first** | A 6% mortgage offset beats the after-cost expected return here, without risk [R33] | Owner states his position |
| D-F | **Worst loss he would sit through, in dollars, at A$50,000 and A$100,000** | The only honest basis for ever choosing L1 | Record it; revisit yearly |
| D-G | **Live at A$5,000 on this system, or in a zero-brokerage account while the system runs in paper** | Section 5 | Paper until the system has earned it |
| D-H | **A fixed "own picks" allowance outside the system (for example 5% or nil), written down** | Gives the NEXTDC urge a bounded outlet so it does not become an override of the system | Nil, in writing |

The owner's income, marginal rate, age, debts, super balance and horizon appear nowhere in 35 reports. Every recommendation about objective, tax and super depends on them. That is the largest gap in the research.

---

## 2. Strategy

### 2.1 Is the core choice right?

**Yes.** Broad, cheap, cap-weighted index funds, held long-term, no leverage, no single shares, no AI deciding trades. The evidence for this is the strongest in finance and the reports apply it correctly. The rejections in reports 31, 32, 33 and 35 (thematic ETFs, direct stock momentum at this size, buy-the-dip, daily brakes, covered calls, dual momentum, regime and ML models) are sound.

### 2.2 What is weak but included

| Item | Problem | Recommendation |
| --- | --- | --- |
| **L1 as the live default** | Expected cost about 1.35 points a year [R33]; mis-aimed at an accumulator (1.3); taxable switching under a law with a 30% minimum on gains | Static is the default. L1 only with `objective: drawdown`, and I would add a size condition: not before the account is large enough for the protection to matter (owner sets it; about A$50,000 is where fixed costs fall under 0.5% [computed]) |
| **Risk-off cash at 0%** | IBKR pays nothing on the first A$15,000 [R33]. The literature L1 rests on credits a cash return. About 1.2 points a year worse than the evidence describes [R33] | Fix before any L1 backtest is signed off. A backtest that credits cash interest the live account will not earn is wrong |
| **The H1 gate may fail anyway** | After the haircut, H1 needs a measured drawdown cut of at least 50% relative [spec §24]. L1 leaves only when all three votes are down, which is slow. A fail is a realistic outcome [my estimate] | Decide now what happens on a fail. Today the answer is "static mode on this system", which is the dominated case (section 5) |
| **Tranches from A$9,375** | Triples small orders; 0.56% a year at the switch point [R33] | Defer tranching until about A$25,000 or drop it from the first live build |
| **Stage 2 (bonds, gold) triggered by size** | Lowers expected return for a growth owner [R33] | Owner choice only, never automatic |

### 2.3 What has strong evidence and is missing

Listed by size of effect. None is an algorithm.

1. **Savings rate and automatic contributions.** Missing as a system function until report 34 proposed it.
2. **Account structure: super against personal.** Found by report 33; not in the spec.
3. **Cost.** A zero-brokerage account holds the same funds for nothing. Found by report 34; not acted on.
4. **Staying invested.** The measured gap between fund returns and investor returns is about 1.2 points a year [R33]. Quiet reporting and friction on overrides (R34 MON-15) address it and cost almost nothing to build.
5. **More market exposure (gearing).** This is the only lever inside investing that raises expected return, and it does so by raising risk, not by skill. Report 33 rejects it for the system and I agree for now: it has no place at A$5,000 or under a "no fuck ups" brief. I record it so the owner knows the honest list is complete. If he ever wants higher expected return than an all-share index, this is the evidence-based route, and it is a risk decision for him and an adviser.

Nothing with strong evidence is missing from the *algorithm*. That is the finding, not a gap.

### 2.4 Is the research agenda in flight the right one?

| Report | Value | Comment |
| --- | --- | --- |
| 36 Real-data backtest of L1 | **High** | It decides whether L1 exists at all. It should gate the build, not follow it. It must credit 0% on idle cash and model the post-2027 tax rules |
| 37 Primary-source verification | **High** | Reports 31, 34 and 35 each say most primary hosts were blocked and they read search extracts. "Verified against multiple sources" is weaker than the owner believes. There are 106 "[unverified]" tags in reports 31–35 alone |
| 40 Profit-claims audit | **High** (done) | The owner's expectation gap is the top risk (section 6). Give the owner its section 0 to read before he answers the decisions in 1.4. Of its three new cards, H62 (a ledger of what each owner override cost or saved) is cheap and useful; H60 and H61 go to the parked table |
| 34 Platform gaps | High (done) | Its rank-1 finding should change the plan, not just add a benchmark |
| 35 Algorithm survey and learning design | Medium (done) | Good survey. Its challenger library is a new subsystem with 38 more trials. Defer it (3.3) |
| 38 Real-data algorithm tournament | **Low, and risky** | A tournament is a multiple-testing machine. Under the spec's own rules its winner cannot be adopted (3.2). Report 35 computed that the best of 10 no-edge rules leads by about 7.7 points in a year by luck. Publishing a league table to an owner who wants to make money invites exactly the override the process exists to prevent. Run it only as a demonstration of selection luck, with the negative control |
| 39 Australia-specific signals | **Low** | Report 35 found no Australian out-of-sample evidence for any of them. Low prior, and anything found faces the same bar |

**Over-researched:** which algorithm. The answer has been the same since report 11.

**Under-researched:**

- The owner's own position (1.4).
- Facts only a test can settle: whether a free EODHD key serves ASX funds (decides A$31 or A$306 a year), and 17 IBKR behaviours (items I1–I17) on which the execution design rests. No document review can close these, and nine have been spent not closing them.
- Build or buy, treated as a decision.
- Who repairs the system at 11:20 on an order day if the owner is not a developer and no agent session is open.

**Recommendation.** Let 36 and 37 finish. Treat 38 and 39 as the last strategy research. Put a 12-month stop on new strategy cards after that.

---

## 3. Process

### 3.1 What is right

- Pre-registration, a trial log, a separate validator, and a hard split between "protects" claims and "earns more" claims. This is the right discipline, and it is the reason the programme has not fooled itself.
- Refusing to draw performance conclusions from paper trading or the first live years.
- Honest tagging of unverified facts.

### 3.2 Will the rules make it impossible to adopt anything?

**For return claims: yes, in practice.** A return claim needs t ≥ 3.0. On 34 years that needs a Sharpe improvement of about 0.51 [spec §24]. Reports 31 and 35 both state that their own candidates are expected to end "not passed". No long-only rule on index funds will clear it.

I think the bar is right. Most published edges are false or fade, and at this scale a false positive costs real money while a missed small edge costs a few dollars. But the consequence should be stated to the owner plainly, and the programme should stop behaving as if the question were open:

> Under the adopted rules, the live rule will almost never change because something "performed better". "Gets better" will mean cheaper, safer and clearer. It will not mean higher returns.

**For risk and cost changes: no.** Design choices are settled by stated thresholds without a significance test [spec §24]. Cheaper funds, a cash ETF, tax-aware parcel selection and a later tranche threshold can all be adopted.

**The gate that could mislead is the lenient one.** H1 is one test at 10% significance on a maximum-drawdown statistic, which is a noisy measure driven by two or three episodes in the sample. A pass will feel like proof. It is evidence that a slow trend rule avoided the long bear markets of 1990–2023, which is already known.

### 3.3 What is overkill

| Practice | Count | Assessment |
| --- | --- | --- |
| Hypothesis cards | H1–H13 in the spec; H14–H17 (R31); H14, H15 again (R32); HG1–HG3 (R33); HP1 (R34); H30–H41 (R35); H60–H62 (R40). Nearly 40 | Out of proportion. Most are written to record an expected "not passed". Each one is build and compute work and raises the trial count |
| Card ID collision | Reports 31 and 32 both define H14 and H15, for different rules | The registry is already inconsistent before it exists. Parallel agents need an ID allocator |
| Document reviews | Nine in one day, the last five "final" | Each round still found things. Rounds 6–8 each found a High defect in the same place (delivery of `/kill` and `/veto`). That pattern means the design in that area is too intricate, and more reading will not fix it. A tenth read is worth less than one hour against the IBKR paper account |
| Reviewer independence | All reviews are by AI agents of the same kind reading the same text | Errors are correlated. Real independence now comes from running code against the broker and the data vendor |
| Bank model-risk framework (SR 26-2), two-implementation rule, 7-day cooling-off | For one rule of three votes | Keep the two-implementation check for the decision core and tax arithmetic. It is cheap for agents. Drop the references to bank regulation |
| Tax-agent written advice as a go-live gate | For about two round trips a year in two index funds | Out of proportion at A$5,000 [my estimate]. Ask at the normal annual return. Keep the question list |

### 3.4 Recommended process, proportionate

1. **Freeze the spec.** v2.10 plus one short, numbered amendment (section 7.2). No v2.12 until the system has run in paper for 20 trading days.
2. **Cards: at most five active.** H1, H2, H11 (L1 decision); HG1 (cash while off); one spare. Everything else is parked in a single "ideas considered" table with a one-line reason and the source report. A parked idea costs no trial.
3. **Replace document reviews with test evidence.** From now, a "review" is a failing or passing test, a paper-account transcript, or a reconciled statement.
4. **One annual review** in a fixed month. That is when "learning" happens: cost model against actual costs, incidents, the parked list, and at most one change.
5. **One ID register**, owned by one agent, for requirements and cards.

---

## 4. Engineering

### 4.1 Proportion

The task: two funds, one decision a month, about 6–12 orders a year. The specification: 2,147 lines, about 270 requirement IDs, 18 prefixes, 11 milestones, six gates, 66 open items. Reports 31–35 propose roughly 60 more requirements and config changes.

This is specified like a small fund manager's order system. Some of that is right: the money path, reconciliation, the halts and the tax ledger must be exact. But a great deal of it serves cases that are years away or will never arrive (other users, US venue, multi-currency ledger, forecast engine, tranches, public dashboard).

### 4.2 Risk of never shipping: high

Evidence from the repository:

- 8 commits, all at 04:15 on 13 November. About 5,700 lines including tests. `strategy.py`, `orders.py`, `risk.py`, `execution.py`, `tax.py`, `runner.py` and every broker and data module are 3-line stubs.
- The README still describes "ASX shares … two independent users … spec v1.2". The stub signal modules are `commodity.py`, `news.py`, `dip.py`, `regime.py`: the abandoned BHP design.
- Since that commit the spec moved from v1.2 to v2.10 and five more reports proposed changes. The specification is moving faster than the code. No requirement in the money path has run.

The usual cause of failure in a project like this is that it is never finished: each review finds something, each finding becomes a requirement, and the first order never goes out. This project is on that path.

A second-order point: every safeguard added to the kill and veto path created a new edge case in the next review. The most reliable way to have "no fuck ups" is to have fewer parts.

### 4.3 The value of each part

| Part | Value at 6–12 orders a year | Risk and cost to build |
| --- | --- | --- |
| Data fetch, checks, monthly decision | High: this is the discipline | Low |
| Records, parcel ledger, benchmarks, reports | High | Medium |
| Reconciliation against the broker | High | Medium |
| **Automatic order placement through the IBKR API** | **Low**: it saves the owner typing a handful of orders a year, and he must approve a phone login on each of those days anyway | **Highest in the system**: gateway, 2FA, order states, restart recovery, kill delivery. Most of EXE, BP and RSK, and every High finding in reviews 6–9 |
| Telegram veto, two-factor resume, encrypted dashboard, public site | Low to medium | Medium to high |

So the most expensive and most dangerous component is also the one that adds least at this trading frequency. That suggests the order of work.

### 4.4 Minimum viable path to a safe live system

**Stage A — "Advisory" (about 2–3 weeks of build).** Data in; checks; decision; plan message; **order sheet**; the owner enters the few orders by hand; the system reads the broker's daily report, reconciles, keeps parcels, benchmarks and the monthly report. No broker API in the money path, so it cannot place a wrong order. The spec already has the order sheet as its contingency [spec D12]; this makes it the first release.

**Stage B — "Automatic on paper".** Add the IBKR adapter and run it against the paper account for the G3 period. Stage A keeps working beside it.

**Stage C — "Automatic live".** Canary, then live, when Stage B has passed and the account is large enough to justify it (section 5).

This gets a working, checked, useful system in weeks, lets the riskiest part mature on paper, and removes the pressure that leads to shortcuts.

If the owner insists on automatic orders from day one, the minimum is still much smaller than v2.10: M1 (one data source plus the broker's mark as the check), M2, M4, M5 without the items below.

### 4.5 What can be deferred without loss of safety

| Defer | Until |
| --- | --- |
| M7 public dashboard; M8 other users; M9 Stage 2 engine; M10 US venue; §26 forecast engine; all USR, ENG, USE, MKT, most SIZ requirements (about 50 IDs) | Asked for, with a reason |
| Tranches (N = 3), staggered evaluation dates | About A$25,000 |
| Challenger library (R35), daily shadow brake (R32), momentum paper sleeve (R31) | After 12 months live |
| Encrypted-snapshot phone dashboard | After go-live. The digest and monthly report are enough |
| `/veto` by Telegram | After go-live. `/kill` and the order-day approval are enough. The owner can already decline the login to stop that day's buys |
| Bitemporal data tables | Keep raw files and a simple corrections log |
| Full 2027 tax engine (indexation, minimum-tax estimate) | First tax report. **Keep now:** the parcel ledger and the 30 June 2027 valuation snapshot |
| Vectorised twin of the harness, full battery | Keep one harness and the independent re-implementation |

**Do not defer:** reconciliation to the unit and the cent; idempotent orders; limit orders only; settled cash only; the integrity halt; `/kill` with a confirmed reply; the outside dead-man monitor; backups with one tested restore; the canary.

### 4.6 Build order

The spec's order is M1 data → M2 decision → M3 harness and tax → M4 broker → M5 operations. Two changes:

1. **Week 1 is a spike against reality, before M1 is finished.** Free EODHD key on VAS, VGS, DHHF. IBKR paper login through the gateway, one snapshot quote, one what-if order, one Flex report. This closes or re-opens the facts that the data and execution design assume. If any is false, parts of the spec change. Better to know before building on them.
2. **The L1 decision comes before the plant.** Report 36, checked by a second implementation, should be accepted or rejected by the owner before M3–M5 are built in full. If the result is static, much of the system is not needed.

---

## 5. Costs and economics

### 5.1 Total cost of ownership

Assumptions: A$500 a month contributed in A$1,000 lots; commission the larger of A$6.60 and 0.088% [spec]; server A$93–138 a year; data A$31 a year if the free plan works [spec §1]; L1 trades six orders a year; L1's expected drag against static 1.35 points a year [R33 from R11's model; range roughly −2.9 to +0.2]; idle cash at 0% on the first A$15,000 while a fund is off, about 1.2 points on that money [R33]. The comparison is DHHF, or the same two funds, in a zero-brokerage auto-invest account at A$0 a year [R34].

| A$ a year | A$5,000 | A$25,000 | A$100,000 |
| --- | --- | --- | --- |
| **Static mode on this system:** running cost | 165–210 (3.3–4.2%) | 165–210 (0.7–0.8%) | 165–210 (0.2%) |
| **L1 on this system:** running cost | 205–250 (4.1–5.0%) | 230–275 (0.9–1.1%) | 430–475 (0.4–0.5%) |
| L1 expected drag (model, not evidence) | 68 | 338 | 1,350 |
| Idle cash at 0% (if not fixed) | about 60 | about 180 | about 180 |
| **L1 expected shortfall against the zero-cost alternative** | **about 330–380 (6.6–7.6%)** | **about 750–790 (3.0–3.2%)** | **about 1,960–2,000 (2.0%)** |
| What L1 buys | A planned worst fall of −25% instead of −35 to −50% [spec]: about A$500–1,250 less paper loss | A$2,500–6,250 | A$10,000–25,000 |

All [computed]. Add A$275 a year at every size if the free data plan does not serve ASX funds.

**One-off costs before the first live order:** index history rental about A$381 if that route is taken; mini PC A$280–490 if bought; canary A$13 [spec]; tax agent's written advice, unpriced in any report (A$200–600 [my estimate]). Together A$500–1,500: 10–30% of the account.

**Costs no report counts:** the owner's time on the recurring jobs (2–3 hours a month [my estimate]), and the cost of the agent sessions that produced ten spec versions and 35 reports and will build and maintain the code. If that second figure were known it would probably be the largest in this section.

### 5.2 When does it pay for itself?

**In expected dollars: never, at any size.** That is the programme's own evidence [R11], and nothing in reports 31–35 changes it. Fixed costs shrink with size, but L1's expected drag grows with the balance.

What changes with size is whether the cost is reasonable for what is bought:

| Account | Static on this system | L1 on this system |
| --- | --- | --- |
| A$5,000 | Dominated. Pays 3–4% a year for what is free elsewhere | Not defensible on money. About 7% a year for protection worth a few hundred dollars. Defensible only as tuition |
| A$25,000 | Still dominated (0.7–0.8% a year for nothing) | Weak. About 3% a year |
| About A$50,000 | Fixed costs under 0.5% [computed]. Tolerable if the owner values his own records and control | An owner choice. About 2–2.5% a year for a much shallower worst fall |
| A$100,000 | 0.2%. Fine | A fair question. About A$2,000 a year expected, against A$10,000–25,000 less loss in a major bear market, perhaps once in 10–15 years [my estimate]. Worth it only if it stops the owner selling at the bottom |

**The honest case for building it** is not at A$5,000. With A$500 a month the account is about A$43,000 in five years and A$97,000 in ten [computed]. A system proven on paper and at small size by then has real option value for an owner who, at that point, chooses drawdown control. That is a reasonable thing to build. It is a different thing from what the owner thinks he is getting.

### 5.3 Recommendation on the money

Unless the owner chooses "tuition" with open eyes (D-B, D-G):

- **The A$5,000 and the monthly contributions go into DHHF, or the same two funds, in a zero-brokerage auto-invest account.** That meets the wealth goal, is fully automatic and cannot miss a listed winner.
- **The system runs in advisory mode and on the IBKR paper account** against the same funds, with real records.
- **Real money moves to the system** when all three hold: it has run clean for 12 months; the account it would manage is at least about A$50,000 (owner sets the figure); and the owner has chosen `objective: drawdown` in writing, or has decided he wants his own automated platform for static holding and accepts about 0.4% a year for it.

Moving holdings between brokers later is reported as generally not a disposal [R34, unverified]; confirm before relying on it.

---

## 6. Biggest remaining risks, ranked

| Rank | Risk | Type | Why it ranks here | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | **Expectation gap.** The owner expects a money-making algorithm; he gets one built to lag in good years | Behavioural | It ends with an override or abandonment at the worst moment, which is the one outcome that reliably destroys wealth | Decisions D-A, D-B in writing now. Report 40's summary read by the owner. The plain sentence in 3.2 |
| 2 | **Never shipping.** Spec and research keep growing; no money-path code exists | Project | Current trajectory (4.2) | Freeze; staged path (4.4); dates (7.3) |
| 3 | **Paying 4–7% a year at A$5,000 for nothing** | Financial | Certain, not probabilistic | 5.3 |
| 4 | **Money in the wrong place.** Super, debt and contributions never get addressed because attention is on the algorithm | Financial | Largest dollar effect in the programme [R33] | Decisions D-C, D-D, D-E |
| 5 | **Single maintainer who depends on AI agents.** A fault on an order day; a library or API change; the owner unavailable | Operational | A live trader nobody can repair is worse than none | Advisory stage first; hibernation path and successor note [R34]; the order sheet as a permanent fallback |
| 6 | **Winner-chasing outside the system.** NEXTDC-type buying by hand, or a veto habit | Behavioural | The owner named it himself | D-H; "winners you already own" block [R31]; quiet reporting [R34] |
| 7 | **Facts assumed, not tested.** 45 unverified items in the spec; many "verified" claims rest on search extracts | Technical | One false assumption (data coverage, cash treatment, order recovery) forces redesign | Week-1 spike; report 37 |
| 8 | **Tax.** The 2027 regime as read by agents, not a professional; 30% minimum on gains; investor or trader status; cost-base errors | Legal and tax | Small in dollars at A$5,000, larger later. Static holding reduces it to almost nothing | Parcel ledger and 30 June 2027 snapshot now; agent at the normal return; an independent check of the first CGT schedule [R34] |
| 9 | **Selection-luck leaderboard.** Tournament and challenger tables show something "winning" every year | Behavioural and process | Report 35 quantified it: about 7.7 points by luck among ten | Defer the library; never show a ranking without the luck band and the negative control |
| 10 | **Broker and account security; custody.** API login, Telegram bot, one custodian | Operational | Low probability, whole balance | Account hardening checklist [R34]; login with no funding rights (if IBKR offers it) |
| 11 | **Other users.** Handing the software and its default rule to four more people | Legal | Unreviewed by a lawyer, as the spec says | Do not do it. M8 stays unbuilt until there is a reason and advice |
| 12 | **A real software defect that places a wrong order** | Operational | The spec's controls are strong; the cash account and limit orders cap the damage | Canary; reconciliation; keep those controls out of the deferral list |

Market risk is not on the list on purpose. A 40–50% fall in a share index is the known price of the return and is the same in DHHF.

---

## 7. Recommendations

### 7.1 Top 10 changes, in priority order

1. **Put the objective decision to the owner now, in writing (D-A, D-B, D-F).** Default `growth` → static. L1 becomes opt-in and conditional on size. Tell him plainly that no algorithm in the evidence beats the index and that "gets better" will mean cheaper, safer and clearer.
2. **Separate the money from the project (D-G).** Money and contributions into a zero-brokerage auto-invest account now. The system earns the right to manage real money (5.3).
3. **Deal with the bigger levers before more algorithm work (D-C, D-D, D-E).** Standing monthly transfer; super against personal; debt and emergency cash. Collect the owner's facts that every recommendation depends on.
4. **Freeze the specification.** v2.10 plus one short amendment (7.2). No further full-document reviews. Park every other proposal from reports 31–35 in one table.
5. **Cut a "Live-Core" build profile** from the frozen spec: about 100–120 of the 270 requirements. Defer the list in 4.5. Fix the repository's stale v1.2 identity as part of the re-baseline.
6. **Ship advisory mode first, automatic orders second (4.4).** The order sheet becomes release 1. The IBKR adapter matures on paper.
7. **Run a one-week reality spike before building on assumptions.** EODHD free key on the three funds; IBKR paper login, snapshot, what-if order, Flex report. Close or re-open items O6, I2–I5, I14, I16.
8. **Decide L1 before building its plant.** Accept or reject report 36 after an independent re-implementation, with idle cash at 0% and the post-2027 tax rules in the model. Decide in advance what a fail means: under these recommendations, nothing changes, because static is already the default.
9. **Stop the strategy search.** Finish 36 and 37. Treat 38 and 39 as the last, and present 38 only as a lesson in selection luck. Cap active cards at five. Fix the H14/H15 ID collision with one register. Defer the challenger library until 12 months after go-live.
10. **Make the operation survivable by one person.** Quiet daily digest; automatic-contribution tracking; successor note and readable tax export; hibernation command; broker-account hardening checklist. All from report 34, all cheap. Drop the tax-agent letter as a go-live gate at this size and ask at the normal return instead.

### 7.2 The one amendment to v2.10 (v2.11, then frozen)

| Change | Source |
| --- | --- |
| `objective: growth | drawdown`, no default in code; growth → static live, L1 paper | R33 §2.2; this report 1.3 |
| `execution.mode: advisory | paper_auto | live_auto`; advisory is release 1 | This report 4.4 |
| Benchmark B3 (zero-brokerage account) and the static-mode cost criterion | R34 §5.1 |
| Idle cash: state the 0% cost; backtests credit what the live account earns; card HG1 | R33 §2.3 |
| Tranche threshold moved to about A$25,000 or deferred | R33 §2.7 |
| Contribution tracking and missed-contribution alert | R34 §5.2 |
| Quiet digest default | R34 §5.7 |
| Successor note, hibernation path, hardening checklist | R34 §5.3, §5.9, §5.11 |
| "Live-Core" requirement list and the deferral list | This report 4.5 |
| Expectations statement: the sentence in 3.2, and R31's recovery sentence | This report; R31 D13 |

Everything else in reports 31–35 goes to the parked table.

### 7.3 Roadmap

Dates assume agent-speed building and that the owner acts within a few days on each of his steps. The binding constraints are calendar gates (60 trading days of paper, 20 days of canary), account opening and the owner's own time.

| By | Milestone | Owner must |
| --- | --- | --- |
| **Fri 20 Nov 2026** | Owner decisions D-A to D-H recorded. Reports 36 and 37 delivered. Spike started | Answer the eight decisions. Give his facts (marginal rate, debts, emergency cash, super room, horizon). Get a free EODHD key. Apply for the IBKR account (paper access comes with it) |
| **Fri 27 Nov 2026** | v2.11 amendment issued and frozen. Live-Core list cut. Spike results in. L1 decision made from report 36 plus its independent check | Approve the amendment. Accept or reject L1 for paper. Open the auto-invest account and set the standing transfer; invest the A$5,000 there (if D-G is "paper first") |
| **Fri 11 Dec 2026** | **Advisory release running**: daily data, checks, monthly decision, plan and order sheet, records, benchmarks B1–B3, digest. Repository re-baselined; no v1.2 remnants | Choose the host. Read the first plan. Store backup key off the server |
| **Mon 14 Dec 2026** | IBKR adapter on the paper account; paper period (G3) starts | Approve paper logins on order days |
| **Late Jan 2027** | First monthly report. Restore drill and kill drill passed | Run both drills once |
| **About Fri 19 Mar 2027** | G3 exit: 60 trading days, 6 cycles including drills, 40 order events, zero unexplained breaks | Review the G3 report |
| **March 2027** | **Decision point 1:** stay in advisory and paper, or run a canary. Canary only if the owner chose tuition or the account size condition is met | Decide |
| **About 23 Apr 2027** (if canary taken) | Canary plus 20 trading days complete. Go-live at the amount the owner chose | Run go-live |
| **Wed 30 Jun 2027** | Parcel valuation snapshot for the CGT change, whichever account holds the units | Confirm it ran; keep the closing prices |
| **Jul–Aug 2027** | First tax report; agent consulted at the normal return, with the question list | See the tax agent |
| **Nov 2027** | **First annual review.** Twelve months of record. Costs against model, incidents, parked ideas. At most one change. Decide whether real money moves to the system (5.3) | Decide |
| **When the managed balance reaches the owner's threshold (about A$50,000; about 2031–32 at A$500 a month)** | L1 becomes a live option if the owner chooses `drawdown` | Decide |

If the owner chooses "live at A$5,000 as tuition" on 20 November, the same dates apply and real money goes live about 23 April 2027, in static mode unless he has also chosen `drawdown`.

### 7.4 What would change this review

- **Report 36** shows L1 cutting drawdown by well over half with after-tax cost under 0.5 points, with idle cash at 0%. That strengthens L1 for a drawdown owner. It does not change the default for a growth owner, or the accumulator argument.
- **Report 37** overturns a load-bearing fact (the CGT regime, IBKR commission or cash interest, zero-brokerage offers). Section 5 would need redoing.
- **The owner's facts.** A large balance elsewhere that this account would later manage, a short horizon, or a known tendency to sell in falls would each move the L1 decision.
- **The owner's purpose.** If the answer to D-B is "I want to build and run this, and A$250 a year is a fair price for that", then going live at A$5,000 is a legitimate choice. The recommendations on freezing, cutting scope and staging still apply.

---

## 8. Sources

Internal only. `FD_FINAL.md` v2.10 (§1, §2, §9.1, §16, §17, §20, §21, §23, §24, §30); `How_the_trading_system_works.md`; reports 11, 13, 31, 32, 33, 34, 35 (sections cited inline) and 40 (summary); repository `/home/user/asx-trader` at commit `9156c2d`. No external source was fetched for this report; every external fact is inherited from the cited report with its original tag.
