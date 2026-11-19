# 42. Pre-mortem: it is November 2031 and the system has failed. Why?

Report 42, 13 November 2026. Written against `FD_FINAL.md` (v2.10), research reports 11–35 (36–41 do not exist in `research2/`), and the plain-English guide. General information only: not financial, tax or legal advice.

**Method.** Assume the failure has already happened, then work backwards to the most plausible causes. "Failed" means any of: ended behind simply holding DHHF; was abandoned; caused a tax problem; blew up operationally. For each story: likelihood over the five years to November 2031, impact, an early-warning signal the system could detect, what v2.10 already does (requirement IDs), and what is missing (new text PM-01 to PM-23, or owner guidance).

**Tags.** **[2+]** two or more independent sources. **[1]** one source. **[unverified]** my inference, model memory, or a figure nobody confirmed. **[computed]** my arithmetic or simulation from stated inputs. **[spec]** read directly in v2.10. Where a research report already tagged a claim, I carry its tag and cite the report.

**Scoring.** Likelihood H = more likely than not (3), M = roughly 20–60% (2), L = under 20% (1). Impact 1–5: 1 = nuisance or under A$250; 2 = A$250–1,000; 3 = A$1,000–3,000 or months of outage; 4 = A$3,000–10,000 or abandonment of the project; 5 = above A$10,000, the whole balance, or a legal problem. Rank = likelihood × impact. Dollar figures assume A$5,000 at the start plus A$500 a month, which reaches about A$43,000–45,000 by late 2031 at 8% a year [computed].

**What I did not verify.** I did not re-read primary pages for IBKR, EODHD, the ATO or the 2026 CGT Act; those facts are as reports 11–19 found them, with their tags. Four web searches were run for this report (ib_async lineage, IBKR minimum versions, ASX T+1, the post-2009 record of the 10-month rule); results are cited in section 8 and were read as search summaries, not pages. The simulation in section 1 is a model, not evidence.

---

## 0. Answer in brief

1. **The most likely 2031 "failure" is not a tail event. It is the system working exactly as designed.** In a simulation of rule L1 on this account's cash flows, L1 ends behind a zero-cost static 40/60 holding in 75–90% of five-year paths before fixed costs and tax, and in 79–94% after fixed costs. The median shortfall is about A$3,100–3,900 on a balance of about A$43,000–45,000 [computed, section 1]. The spec says this honestly (§1, §30). The plan is not organised around it: there is no place where the owner chooses to pay that premium, no budget for it, and no date on which it is reviewed.
2. **The next three are about people and the project, not markets.** The build is never finished and the money sits idle meanwhile; the owner, who asked for "more" on the same day the spec was declared final (reports 31–35), switches strategy after a lagging stretch; or the owner tires of roughly 60 manual chores a year for a A$5,000 account and the system freezes in whatever state it was in.
3. **One defect found in v2.10.** The cost-halt order count (`order_count_12m: {review: 8, halt: 12}`, RSK-26) does not scale with the tranche count. Once N = 3 (from A$9,375), one ordinary exit and re-entry of both sleeves is 12 counted events; a thirteenth event sets `HALTED_BUYS`, which blocks every later buy until the owner clears it on the server [computed from the spec]. Fix: PM-07.
4. **The two cheapest, highest-value actions need no code.** Invest the money now by hand rather than leaving it idle while the system is built (PM-01), and make the objective and venue decision that reports 33 and 34 proposed, using the numbers in section 1 (PM-04).
5. **The largest structural change I recommend: go live in "sheet mode" first.** At about six trades a year the IB Gateway, IBC, `ib_async` and login-approval machinery is the most fragile and most expensive part of the system per trade, and the owner already has to touch the phone on every broker day. A mode where the system plans, the owner types one or two limit orders into the IBKR app, and Flex reconciles the next morning removes the biggest operational failure surface and about a third of the build (PM-03).

### Ranked list (likelihood × impact)

| Rank | # | Failure story | L | I | Score | v2.10 covers it? | Main mitigation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F-01 | Base case: L1 works as designed and still ends behind DHHF | H | 4 | 12 | Disclosed, not managed | PM-04, PM-05, PM-06 |
| 2 | F-02 | Never finished; money idle or never invested | H | 4 | 12 | No | PM-01, PM-02, PM-03 |
| 3 | F-03 | Owner "wants more", switches strategy after a lagging stretch | H | 4 | 12 | Partly (RND-032, PRT-26) | PM-04, PM-13 |
| 4 | F-04 | Owner disengages; chores lapse; system freezes in place | H | 4 | 12 | Pages only | PM-08, PM-09, PM-15 |
| 5 | F-05 | IBKR gateway / API / `ib_async` change breaks execution | H | 3 | 9 | Partly (D12, BP-07) | PM-03, PM-10 |
| 6 | F-06 | Maintainer gone: nobody can change the code in 2029 | H | 3 | 9 | No | PM-02, PM-03, PM-15 |
| 7 | F-07 | Fixed costs at small scale; STATIC mode dominated by a free account | H | 3 | 9 | Reported, not acted on | PM-16, PM-04 |
| 8 | F-08 | Wrong CGT schedule under a one-year-old law | H | 3 | 9 | Partly (TAX-04, provisional flags) | PM-14 |
| 9 | F-09 | Repeated whipsaws, then the cost halt blocks re-entry | M | 4 | 8 | Partly; one defect | PM-07, PM-09 |
| 10 | F-10 | Panic override: kill or veto at the bottom, or manual selling | M | 4 | 8 | Partly (RSK-30(5), RSK-33) | PM-22 |
| 11 | F-11 | Cash earns 0% while a sleeve is OFF or waiting | H | 2 | 6 | No (PRT-18 off, I9 open) | PM-06 |
| 12 | F-12 | Contributions stop; account stays tiny | M | 3 | 6 | No | PM-16, PM-23 |
| 13 | F-13 | H1 fails or cannot be tested; 18 months of build yields STATIC | M | 3 | 6 | Yes for the outcome; not the cost | PM-04, PM-16 |
| 14 | F-14 | H1 "passes" on two famous bear markets; the benefit does not recur | M | 3 | 6 | Partly (H12, battery) | PM-12 |
| 15 | F-15 | Builder and validator agents share the same wrong reading | M | 3 | 6 | Partly (RND-003, G1) | PM-11 |
| 16 | F-16 | A lucky challenger is promoted (report 35 library) | M | 3 | 6 | Not in v2.10; R35 proposes rules | PM-13 |
| 17 | F-17 | Fast crash: sells late, re-buys higher | M | 3 | 6 | Disclosed; H8, regime row | R32 H14/H15, no new text |
| 18 | F-18 | EODHD plan, price or licence change | H | 2 | 6 | Partly (DAT-23(4)) | PM-17 |
| 19 | F-19 | IBKR terms, fees or ASIC's 2028 algorithm rules end retail API use | M | 3 | 6 | P8 open item only | PM-03, PM-18 |
| 20 | F-20 | Latent spec defects: the reviews have not converged | H | 2 | 6 | No | PM-21 |
| 21 | F-21 | The 2024+ "holdout" is not blind; multiple-testing leaks | H | 2 | 6 | Partly (VAL-22, RND-025) | PM-12 |
| 22 | F-22 | Death, incapacity or long absence | L | 5 | 5 | No | PM-15 |
| 23 | F-23 | Account or server compromise | L | 5 | 5 | Server yes; accounts no | PM-19 |
| 24 | F-24 | Backups unreadable: key, TOTP seed or secrets lost | L | 4 | 4 | Mostly (BP-16, O20) | PM-14 (plain export) |
| 25 | F-25 | Minimum-tax or short-term-gain bill with no provision | M | 2 | 4 | Estimator only (TAX-06) | PM-14 |
| 26 | F-26 | 30 June 2027 arrives before the system is live | M | 2 | 4 | Partly (TAX-05 late-entry rule) | PM-14 |
| 27 | F-27 | AUD shock | M | 2 | 4 | Reported (PRT-24) | Owner guidance |
| 28 | F-28 | Giving the software to others becomes a legal problem | L | 4 | 4 | Structure only; no legal review | PM-20 |
| 29 | F-29 | A real bear market, then a halt keeps the account in cash through the recovery | L | 3 | 3 | Partly (re-arm, idle-cash page) | PM-09 |
| 30 | F-30 | Server dies | H | 1 | 3 | Yes (INF-01, BP-16, MON-01) | — |
| 31 | F-31 | Missed login approvals | H | 1 | 3 | Yes (PRT-27, OPS-07) | PM-03 |
| 32 | F-32 | ETF closure, index change, or cheaper rivals | L | 2 | 2 | Mostly (SYS-23, SYS-30 to SYS-32) | PM-18 |
| 33 | F-33 | Australian shares lag global for a decade | M | 1 | 2 | By design (B1 tracked) | Owner guidance |
| 34 | F-34 | ATO treats the owner as a share trader | L | 2 | 2 | Yes (TAX-03, T1) | — |
| 35 | F-35 | Price-data error causes a wrong trade | L | 2 | 2 | Yes (DAT-02, DAT-04, DAT-11) | — |
| 36 | F-36 | Telegram change, ban or account takeover | M | 1 | 2 | Mostly (BP-11, email backup) | PM-19 |
| 37 | F-37 | Market-structure change: T+1, trading hours, CHESS | M | 1 | 2 | Yes (OPS-09, P4) | — |
| 38 | F-38 | Wash-sale challenge under Part IVA | L | 1 | 1 | Yes (TAX-09, T7) | — |

---

## 1. Base rate: how often does L1 end behind doing nothing?

The spec's expectations table gives "about even odds of lagging over any 5–10 year window" [R14, R15]. That figure is for a trend rule against its own benchmark before this account's frictions. For this pre-mortem I simulated the actual arrangement.

**Model** [computed; script kept in the session scratchpad, not in the project]. 20,000 paths of 60 months. Two sleeves with expected total returns of 8.0% and 8.5% a year, volatility 14% and 12.5%, correlation 0.6. Rule L1 exactly as PRT-12 and PRT-13 (three votes, hysteresis, N = 1), bootstrapped on 14 months of prior history. A$5,000 at the start, A$500 a month. Commission max(A$6.60, 0.088%) plus 7 bp slippage; A$1,000 minimum buy; A$50 reserve. Benchmark: static 40/60, every dollar invested at once, no cost (a zero-brokerage DHHF-type holding). Fixed running cost A$185 a year, counted outside the account. No tax. Two return models: (a) a random walk, which is unkind to trend rules; (b) a bull/bear regime model with bear phases averaging ten months at −30% a year, which is kind to them.

| Return model | Cash rate while out | P(L1 ends behind), before fixed costs | P(behind), after fixed costs | Median L1 minus benchmark | 10th to 90th percentile | P(behind by more than 10% of the balance) |
| --- | --- | --- | --- | --- | --- | --- |
| Random walk | 0% | 90% | 94% | −A$2,950 | −A$5,490 to +A$50 | 38% |
| Random walk | 4% | 79% | 87% | −A$1,920 | −A$4,500 to +A$1,580 | 20% |
| Regimes (trend-friendly) | 0% | 75% | 79% | −A$2,190 | −A$4,830 to +A$5,040 | 21% |
| Regimes (trend-friendly) | 4% | 67% | 73% | −A$1,420 | −A$3,950 to +A$7,080 | 11% |

Add five years of fixed cost (about A$925) and the median shortfall with cash at 0% is about **A$3,100–3,900 by 2031**, 7–9% of the ending balance. R11's modelled tax drag of 0.3–0.6% a year would add roughly A$300–650 more [computed on an average balance of about A$22,000].

**What this shows.**

- With cash at 0% (v2.10 as written) the odds of ending behind are three in four even when the market contains the bear phases the rule is built for.
- Paying a cash rate on out-of-market money is worth about A$800–1,000 of median outcome over five years and cuts the chance of a large shortfall roughly in half. Report 33 §2.3 found the same gap by a different route.
- In the trend-friendly model L1's worst drawdown beats the benchmark's by ten points or more in only 27–30% of five-year windows. In the other 70% the owner has paid the premium and seen no claim.
- Real markets have fatter tails and more momentum than either model, and five years is short. The numbers are a planning base rate, not a forecast.

**Outside evidence for the same pattern.** After 2008–09 the published 10-month timing rule trailed buy-and-hold in each of 2009–2012 by its own author's updated figures, and "in six of the following eight years" in one adviser's summary [2+, search summaries: Canadian Couch Potato on Faber's update; Swedroe via ETF.com]. R14 reaches the same conclusion from the literature: long-only trend filters "cut drawdown but do not reliably raise return" [2+].

---

## 2. Failure stories, in rank order

### Tier 1 — score 12

**F-01. The base case: L1 works as designed and ends behind DHHF (markets).**
*Story.* 2027–2031 is mostly a rising market with two or three sharp corrections. L1 exits late in each, sits in cash at 0%, re-buys higher. No slow bear arrives. By 2031 the dashboard shows L1 about 8% behind B1.
*Likelihood: H.* 75–90% of simulated paths (section 1) [computed]; expectation of lagging 5–15% in strong bull years [R11 model]; post-2009 record of the 10-month rule [2+].
*Impact.* Median about A$3,100–3,900; one path in five is worse than 10% of the balance [computed].
*Early warning.* RSK-29 (36-month lag above 10 points with no drawdown saving) fires a review page. Earlier: cumulative L1 − B2 after modelled tax, as a share of B2.
*v2.10.* Disclosed in §1 and §30; SYS-07 shows both benchmarks; RSK-29 pages but "None" as action; RSK-32 says do nothing. There is no owner decision about the objective and no budget.
*Missing.* PM-04 (objective and venue decision before G0), PM-05 (premium budget), PM-06 (cash yield).

**F-02. Never finished (project).**
*Story.* The spec is 382 KB, about 250 numbered requirements, eleven milestones, 17 unverified IBKR items, 13 tax-agent questions and 22 owner decisions [spec]. Only M0 exists. The owner and build agent spend 2027 in M3 and M4; the Norgate rental (O5) needs a Windows PC and A$381; IBKR paper tests contradict three assumptions; the spec goes to v2.14. The A$5,000 and each month's A$500 wait in a bank account or at IBKR at 0%. In 2028 the repository goes quiet.
*Likelihood: H* (my estimate 40–50% that there is no live trading by end-2027, lower for "never") [unverified]. Evidence: ten spec versions in one day; five further research reports the same evening proposing about 45 more requirement IDs [spec, R33–R35]; earliest realistic go-live is mid-2027 even if nothing slips (build, then 60 trading days of paper, then 20 trading days of canary) [computed from §17].
*Impact.* Idle money: about 7% a year forgone on A$5,000 plus contributions, roughly A$600–900 by end-2027 and rising [computed]. Sunk cost and time. Abandonment.
*Early warning.* Weeks since the last passed milestone; spec edits per code commit.
*v2.10.* Nothing. Milestones have an order but no dates, budget or stop rule. The system refuses to invest before `golive`.
*Missing.* PM-01 (invest now by hand), PM-02 (scope freeze, minimum viable live, stop date), PM-03 (sheet mode removes M4's hardest parts).

**F-03. The owner wants more and switches after a lagging stretch (behaviour).**
*Story.* By mid-2028 L1 is 9 points behind B2. The monthly report (or the report-35 library table) shows a rotation rule 8 points ahead. The owner, as sole approver, amends the spec: a momentum satellite, a daily brake, a NEXTDC-type stock sleeve. The new rule is adopted near the top of its run, trades more, raises the trader-classification question, and lags in turn.
*Likelihood: H.* The strongest evidence is in the folder: reports 31, 32, 33, 34 and 35 exist because, hours after v2.10 was declared final, the owner asked about capturing big winners, faster decisions, "massive gaps" and "more algorithm" [R31–R35 scope statements]. The investor behaviour gap is about 1.2% a year [1, R33]; investors in the most volatile funds lose 2.1 points a year to timing [2+, R34].
*Impact.* Chasing typically costs more than the original lag: 1–3% a year plus realised tax on each switch; A$3,000–8,000 by 2031 [unverified estimate].
*Early warning.* A spec or card change proposed within six months of a 12-month lag above 10 points or a drawdown above 15%; more than one new card a quarter.
*v2.10.* PRT-26 (no re-tuning on live results), RND-032 (one promotion a year, 7-day cooling-off), RND-005. All are enforced by the same person they restrain, and none covers a *spec* change.
*Missing.* PM-04, PM-13 (cooling-off on spec changes, library shown yearly, sandbox cap).

**F-04. The owner disengages and the system freezes where it stands (behaviour, operations).**
*Story.* The runbook in §17 asks, each year, for about 12 distribution amounts and 12 expected ex-date rows (VAS, VGS, DHHF), 12 monthly spread entries, 12 commission reconciliations, 12 call-budget checks, four restore drills, four kill drills, four funding-rights records, four cost-model checks, a calendar load, AMMA statements and a battery re-run: roughly 60 scheduled actions, plus a phone approval on every broker day and about two pages a month [counted from §17, MON-06]. In 2028 the owner misses a distribution entry. DAT-22 blocks the evaluation; after five days OPS-13 skips the month and carries the state. It happens again. The system is now a frozen portfolio with A$164–485 a year of running costs.
*Likelihood: H.* A A$5,000 account earns about A$350 a year; the chores are worth more than that at any hourly rate [computed].
*Impact.* Benign if frozen while invested (it becomes buy-and-hold with costs). Malign if frozen while a sleeve is OFF: the money stays in cash through a recovery, which is the single most expensive thing a trend rule can do. Abandonment either way.
*Early warning.* Count of overdue runbook items; days since the last owner action of any kind; a `DIST_MISSING` or `DATA_STALE` page not cleared in five days.
*v2.10.* Pages for each blocked item; `IDLE_CASH` weekly for cash that should be invested (PRT-19); dead-man monitor for a silent *system*, not a silent *owner*.
*Missing.* PM-08 (chore budget, automated distribution and calendar entry), PM-09 (stuck-in-cash escalation, hibernate), PM-15 (owner-silence and retirement, from R34).

### Tier 2 — score 8–9

**F-05. IBKR gateway, API or `ib_async` change breaks execution (operations).**
*Story.* IBKR raises its minimum Gateway version; the image "pinned by digest" stops logging in; the matching `ib_async` release changes an event the order-state code relies on; or IBKR changes how headless second-factor approval works.
*Likelihood: H* that at least one breaking change needs code work in five years. IBKR raised the minimum supported TWS/Gateway version to 10.30 on 20 March 2025 and will not support older builds [1, IBKR changelog via search]. `ib_insync` was archived in March 2024 after its author died; `ib_async` is a community fork, and maintenance signals conflict [2+, IBKR docs and project pages via search]. Weekly manual re-login cannot be bypassed [2+, R17].
*Impact.* No automated orders until fixed. D12's manual order sheet covers the gap if the owner is attentive. Weeks of outage and, with F-06, abandonment.
*Early warning.* OPS-07's 35-day connectivity check failing; months since the last dependency update; an IBKR notice of a version cut-off.
*v2.10.* BP-07 (authentication checked before orders), OPS-07, D12, BP-14 (deploy sequence), I8. Pinning (BP-10) protects against supply-chain risk but makes forced upgrades more likely to be abrupt.
*Missing.* PM-03 (execution without a gateway), PM-10 (scheduled upgrade rehearsal).

**F-06. Maintainer gone (project).**
*Story.* The code was written by an AI build agent in 2027 from a 2,100-line spec. In 2029 something breaks. The owner cannot debug it; the agent tooling has changed; the "validator" context no longer exists.
*Likelihood: H.* pysystemtrade, the best-documented DIY system, changed primary maintainer in 2024 and moved to a group in 2026 [1, R34].
*Impact.* The first breaking change ends the project. Tax records are safe only if exports exist outside the database.
*Early warning.* R34's proposed "months since the last promoted update" line.
*v2.10.* INF-01 (rebuild in two hours) restores the *same* code; nothing addresses changing it.
*Missing.* PM-02 (smaller code), PM-03 (a mode with far fewer moving parts), PM-15 (retire command and handover pack).

**F-07. Fixed costs at small scale; STATIC mode is dominated (economics).**
*Story.* Costs are A$164–209 a year, or A$440–485 if the paid data plan is needed [spec §19]. Over five years that is A$820–2,400, plus set-up (index rental about A$381, tax-agent advice). If the account is in STATIC mode it holds what a zero-brokerage auto-invest account holds for nothing.
*Likelihood: H* (certain for the cost; M that the account is STATIC, see F-13).
*Impact.* A$1,500–3,000 by 2031 [computed].
*Early warning.* INF-10 already reports fixed cost as a share of NAV.
*v2.10.* INF-10 reports; RSK-30(2) acts only from A$25,000. R34 §5.1 proposes benchmark B3 and RSK-30(6).
*Missing.* PM-16 (adopt B3; cost criterion at every size; scale-or-stop gate), PM-04.

**F-08. Wrong CGT schedule under a new law (tax).**
*Story.* The 2027–28 return is the first under indexation, the deemed 30 June 2027 sale and the 30% minimum tax. The engine's rules for loss ordering (T2), valuation method (T4), CPI base quarter (T9), trade date versus settlement date (T12) and AMIT allocation (T13) are the editor's readings; the spec says so [spec §13, §21.2]. The agent takes the PDF at face value, or the owner self-lodges. An amendment follows in 2030.
*Likelihood: H* that some figure is wrong in the first two years: five engine rules rest on unanswered questions and one ministerial instrument is unverified [spec]. *M* that a wrong figure is lodged.
*Impact.* A$300–1,500 in agent time, interest and possibly a penalty; more if the law is amended again after the next election and the engine lags [unverified].
*Early warning.* Open T-items at the date of the first tax report; a difference between the engine's realised gain and IBKR's own annual statement.
*v2.10.* Pluggable `TaxRegime` (TAX-04); provisional marking (TAX-05, TAX-08, TAX-10); "estimate for the tax agent" labelling. R34 proposes TAX-16 (three-way check) and TAX-17 (provision).
*Missing.* PM-14.

**F-09. Repeated whipsaws, then the cost halt blocks re-entry (markets, software).**
*Story.* A sideways 2028 like 2015–16 gives each sleeve two round trips. Each costs commission, spread, tax on any gain and the price gap between exit and re-entry. The account is now above A$9,375, so N = 3. The thirteenth counted event sets `COST_HALT`; buys are blocked; the owner is travelling; the market recovers 12% before `trader resume --clear buys` is typed on the server with the TOTP code.
*Likelihood: M* for a whipsaw year in five [unverified; 2015–16 is the spec's own named whipsaw regime, RND-026]; *H* that the halt then fires, because of the defect below.
*Defect [computed from spec].* RSK-26(ii) counts one event per (symbol, side, first-planned date) and halts above 12. With N = 1 and two sleeves a full round trip is 4 events, so the halt means "more than three round trips": sensible. With N = 3 a full round trip is 12 events, so one ordinary exit and re-entry plus a single band rebalance trips the halt, and the review page (above 8) fires part-way through the re-entry. After a clear, the halt returns at "one more counted event" (§10), so the owner must resume after every tranche order.
*Impact.* 3–5% of the sleeve per whipsaw; a blocked re-entry can cost 5–10% of NAV in one episode [unverified estimate].
*Early warning.* RSK-27; the order count itself; `IDLE_CASH`.
*v2.10.* Hysteresis (PRT-13), bands (PRT-16(c)), H4, RSK-26, `IDLE_CASH`.
*Missing.* PM-07 (scale the count), PM-09.

**F-10. Panic override (behaviour).**
*Story.* March 2029: markets fall 18% in three weeks. Either (a) the owner sends `/kill` to "stop it selling at the bottom"; `KILLED` blocks the exits as well, by design, and the fall continues; or (b) the owner sells everything by hand in the IBKR app, the system freezes the symbol and sets `HALTED_INTEGRITY` (BP-20), and the owner does not re-enter for a year.
*Likelihood: M.* Traders shown prices less often took more risk and earned more [1, R34]; the digest pushes NAV to the phone every trading day [spec §15].
*Impact.* One episode can cost 5–20% of NAV: A$2,000–8,000 at a 2029 balance [unverified estimate].
*Early warning.* A `/kill` or sell veto within five trading days of a drawdown page; a manual trade in a managed symbol.
*v2.10.* A sell veto needs `SELL CONFIRM`; RSK-30(5) and RSK-33 count overrides; expectations statement item 6; the kill page lists blocked sells daily. R34 proposes MON-15 (quiet digest, veto reason).
*Missing.* PM-22 (`/pause`, kill confirmation that names blocked exits, adopt MON-15).

### Tier 3 — score 6

**F-11. Cash earns 0% (economics).** *Story.* L1 is out of the market about 30% of the time [1, R15]; contributions wait for the A$1,000 minimum; the start-up keeps the whole balance in cash for about 20 trading days. IBKR pays 0% on the first A$15,000 of AUD [1, R33, search extract]. *Likelihood: H* (certain unless I9 comes back differently). *Impact.* About A$800–1,000 of median five-year outcome [computed, section 1]; R33 gives about 1.2 points a year. *Early warning.* Average cash share of NAV × the RBA cash rate, printed monthly. *v2.10.* PRT-18 keeps the cash ETF off; I9 is open; the H10 variant exists. *Missing.* PM-06.

**F-12. Contributions stop (economics).** *Story.* A house deposit, a job change or a child ends the A$500 a month in 2028. The account stays near A$12,000; N flips between 1 and 3; Stage 2 is never reached; fixed costs stay above 1.5%. *Likelihood: M.* Missing two of twelve contributions a year costs about A$12,900 over ten years [computed, R34]. *Impact.* The system never reaches the size at which its costs are tolerable; contributions matter more than the algorithm (§30). *Early warning.* A missed expected contribution. *v2.10.* O7 is a planning input only; PRT-19 handles the cap. *Missing.* PM-23 (adopt R34 MON-13), PM-16.

**F-13. H1 fails or cannot be tested (project, research).** *Story.* To go live as L1 the measured drawdown reduction must be at least 50% relative before the H12 haircut, with doubled costs and a one-month delay (O15) [spec]. Or no licensed index history to 1990 is obtained (O5, P1, P2) and H1 is "not testable". The account runs STATIC: the research harness, registry, validator and battery were built to hold two ETFs. *Likelihood: M* (my estimate 40–50%) [unverified]. *Impact.* A year of build and A$381 of data for a result a free account gives; then F-07. *Early warning.* O5 still open at M3. *v2.10.* PRT-23, VAL-23 and RND-029 handle the outcome correctly. *Missing.* PM-04 (decide now what happens if the answer is STATIC; R34's O25), PM-02 (build the live path before the research path).

**F-14. H1 passes on two famous bear markets and the benefit does not recur (research).** *Story.* The 1990–2023 development sample is the sample that made the 10-month rule famous: 2000–02 and 2008–09 supply nearly all the drawdown saving. The lookbacks 6, 12 and 10 months were taken from literature fitted on that history. Since 2009 falls have been fast and recoveries faster. *Likelihood: M.* Zakamulin reports substantial data-mining bias in published timing results [1, search summary]. *Impact.* As F-01. *Early warning.* The battery's regime-split row; the share of the drawdown saving that survives when 2008 is removed. *v2.10.* H12 haircut, placebo test, "must not rely on 2008 alone" (RND-026), perturbation grid. Good coverage. *Missing.* PM-12 (state plainly that the development sample is not independent of the rule's design).

**F-15. Builder and validator share the same wrong reading (software).** *Story.* Both agents are instances of the same model family reading the same spec. Both implement the 10-month SMA window, the ex-date handling in `tr_net` or the hysteresis bootstrap the same wrong way. G2's "the two implementations agree" passes. *Likelihood: M.* Correlated errors between same-model agents are expected; five "final" reads by the same kind of reviewer kept finding new defects (F-20). *Impact.* A wrong go-live decision, or a live rule that differs from the tested one in a way replay cannot see (replay uses the same code). *Early warning.* None at run time; only a third, different implementation shows it. *v2.10.* RND-003, G1's spreadsheet check of the static mix and a closed-form synthetic series, SYS-16 truncation test, H2 negative control. *Missing.* PM-11.

**F-16. A lucky challenger is promoted (research; applies if report 35's library is adopted).** *Story.* Twelve challengers run in shadow. With 5% tracking error the best of ten no-edge rules leads by 7.7 points a year by luck [computed, R35; I re-derived E[max of 10] = 1.54]. In the 2029 review window the owner promotes it. *Likelihood: M* if the library is built. *Impact.* As F-03, with tax on the transition. *Early warning.* A promotion memo that cites shadow rank or return. *v2.10.* Not present. R35's RND-040 to RND-048 are sound, but they bind only the person they restrain, and the library adds 38 trials and a monthly temptation table. *Missing.* PM-13.

**F-17. Fast crash (markets).** *Story.* A 1987- or 2020-style fall completes inside one month. L1 sells near the low at the month-end evaluation and re-buys 15–20% higher. *Likelihood: M* (about one such episode in five years) [unverified]. *Impact.* 5–10% of NAV against B2 in the episode. *Early warning.* None in time; that is the nature of the event. *v2.10.* Disclosed (§1); February–April 2025 is a required regime row; H8 tests weekly evaluation. Report 32 proposes a shadow-only daily brake (H14, H15). *Missing.* Nothing new; keep the brake in shadow.

**F-18. EODHD changes plan, price or licence (operations, economics).** *Story.* The free plan does not serve ASX tickers (E1 is unverified), or stops doing so in 2028, or the 20-call limit falls. Or the personal licence terms change. Or the vendor's adjusted series is restated. *Likelihood: H* that the data cost assumption (A$31 a year) does not hold for five years [unverified]. *Impact.* +A$275 a year, 5.5% of A$5,000; if the vendor is lost outright, evaluations block after five days (OPS-13) and the system freezes (F-04). *Early warning.* HTTP 402/403 on the daily fetch; `DATA_BUDGET` WARN; DAT-10 restatement count. *v2.10.* DAT-23(4) paid fallback; DAT-10; DAT-02 two-source check. There is no second end-of-day source for a sleeve when EODHD is absent. *Missing.* PM-17.

**F-19. IBKR terms, fees, or the 2028 algorithm rules (legal, operations).** *Story.* ASIC's 2026 trading-algorithm rules start in March 2028 (open item P8). IBKR Australia responds by requiring registration or attestation for API order flow, or by restricting it for retail accounts. Or the ASX minimum commission rises, or an activity fee returns. *Likelihood: M* [unverified]. *Impact.* Automated execution ends or costs more; holdings are unaffected. *Early warning.* An IBKR notice; EXE-09's commission reconciliation; INF-09's fee WARN. *v2.10.* P8 is "before March 2028" with no owner; D12 says there is no backup broker. *Missing.* PM-03 (manual entry is not algorithmic trading through an API), PM-18 (broker-exit runbook).

**F-20. Latent spec defects (software, project).** *Story.* A requirement that reads correctly produces a wrong result in a state nobody walked through. *Likelihood: H.* The successive reviews found 43, 16, 13, 6, 5 and then 10 findings [spec, document control]: the count rose on the last read, so the defect-discovery curve has not flattened. This report found one more on a first pass (F-09). *Impact.* Mostly small; occasionally an episode like F-09. *Early warning.* The build agent's question log; halts whose cause is "the spec says so". *v2.10.* Nine reviews, an ID-consistency script. *Missing.* PM-21.

**F-21. The holdout is not blind; multiple-testing leaks (research).** *Story.* VAL-21 locks 2024 onward as a holdout. But every card is written in November 2026 or later by people and models who know what markets did in 2024–2026, including the February–April 2025 fall that the spec names. The lock stops the *code* reading the data; it cannot stop the *designers* knowing it. Separately: design choices (band, minimum order, tranche count, offsets, carry days) are chosen by H3–H5, H8 and H9 on the development sample and H1 is then tested on that same sample with a Holm family of one; the literature search across 35 reports is an uncounted layer of trials; each new family in report 35 gets its own opening of the same 2024+ window. *Likelihood: H* (it is true today). *Impact.* The drawdown benefit is overstated by an unknown amount; H12's halving is the only buffer. *Early warning.* Not detectable at run time. *v2.10.* VAL-22 trial counting, RND-025 lock, H12. *Missing.* PM-12.

### Tier 4 — score 3–5

**F-22. Death, incapacity or long absence (other).** No order is sent without the owner's phone approval, so the account freezes safely, but the parcel and 30 June 2027 records sit behind a key only the owner holds. *L,* impact 5. v2.10 has nothing; R34 §5.3 works it through. *Missing.* PM-15 (adopt OPS-14).

**F-23. Account or server compromise (operations).** The server is hardened in detail (BP-09, BP-10, INF-02 to INF-08). The IBKR login, the email behind it, the Telegram account and the mobile number are not. A hijacked brokerage account can be used to buy a thin stock from the attacker even with no withdrawal rights; whether the bot username can be limited is unverified (I7, BP-08). *L,* impact 5. *Early warning.* A trade outside the universe (BP-20 books it with a WARN only). *Missing.* PM-19.

**F-24. Backups unreadable (operations).** The `age` key or TOTP seed is lost with a phone; the quarterly restore drill was skipped (F-04). *L,* impact 4: tax records must be rebuilt from Flex, whose history depth is unverified (I3). *v2.10.* BP-16, O20, backup check-in to the dead-man monitor. *Missing.* PM-14's plain-text yearly export held off the server.

**F-25. A tax bill with no provision (tax).** Short-term gains get neither discount nor indexation; a user under a 30% marginal rate pays the 30% floor (§13). A good year for the rule produces a bill payable from outside the account. *M,* impact 2. *v2.10.* TAX-06 estimates yearly, after the fact. *Missing.* PM-14 (running provision on every planned sell; R34 TAX-17).

**F-26. 30 June 2027 arrives before go-live (tax, project).** The snapshot job (TAX-05) assumes a running system. On the realistic timeline (F-02) the system is in paper or canary on that date, and anything bought by hand under PM-01 needs its 30 June 2027 value from another source. *M,* impact 2. *v2.10.* TAX-05 handles a parcel "that enters the ledger later" if a close is stored. *Missing.* PM-14 (owner checklist for that date regardless of project state).

**F-27. AUD shock (markets).** The Australian dollar rises 25%; unhedged VGS falls in AUD while world markets are flat; L1 exits VGS on a currency move and is whipsawed when it reverses. Against DHHF, which is also unhedged, the relative effect is small; in absolute terms 60% of the account takes the hit. *M,* impact 2. *v2.10.* PRT-24, currency stress row, hedged paper variant V3. *Missing.* Owner guidance only: the comparison with DHHF is unaffected; do not add a hedge in response to a move that has already happened.

**F-28. Giving the software to others (legal).** Up to four more people run copies (M8). One loses money and complains that the owner recommended a strategy. No lawyer has reviewed the structure, by owner decision (OD1) [spec §14, §21.7]. *L,* impact 4. *Missing.* PM-20.

**F-29. A halt keeps the account in cash through a recovery (markets, behaviour).** A real bear market arrives; L1 works; the drawdown passes the 99th percentile and `DRAWDOWN_HALT` blocks buys (RSK-22); the owner, shaken, does not clear it. *L,* impact 3. *v2.10.* Re-arm rule, `IDLE_CASH` names a halt as a cause. *Missing.* PM-09 (state the cost of waiting in each page).

**F-30. Server dies (operations).** A home mini PC loses power, its SSD or its internet; a cloud card expires. *H* over five years, impact 1 if INF-01 and BP-16 are real. Covered, provided the drills happen (F-04).

**F-31. Missed login approvals (operations).** The owner is at work, overseas or has a new phone. *H,* impact 1. Sells carry until filled and buys for five days (PRT-27); OPS-07 checks connectivity. Covered; PM-03 removes the approval window altogether.

### Tier 5 — score 1–2

**F-32. ETF closure, index change or cheaper rivals (markets).** VAS and VGS are among the largest ASX ETFs, so closure is unlikely; an index-provider change is possible; cheaper equivalents already exist (A200, BGBL: R33 §2.9). *L,* impact 2. SYS-23, SYS-30, SYS-31 and SYS-32 cover the mechanics. A forced switch realises the whole sleeve's gain and, under SYS-31, needs a new card. *Missing.* PM-18 (pre-registered successor table).

**F-33. Australian shares lag global for a decade (markets).** It happened from about 2010 to 2020 [unverified, model memory]. DHHF holds a similar Australian share, so against DHHF the effect is close to nil; against an all-global holding it is roughly 40% × the gap. *M,* impact 1 on the stated benchmark. Trend filters whipsaw more on a sideways sleeve, which adds to F-09. *Missing.* Owner guidance: the 40/60 split is a choice, reviewed yearly against B1, never changed after a bad stretch.

**F-34. ATO trader classification (tax).** A written rule set and business-like records point one way; 6–24 trades a year on A$5,000 points the other; "capital account is the likely position, not a certain one" [R18, 2+ for the test, unverified for automation]. Under the post-2027 rules short-term gains get no concession anyway, so the cost of reclassification is modest. *L,* impact 2. TAX-03 and T1 cover it. The risk rises sharply if F-03 adds a stock-momentum satellite.

**F-35. Price-data error (operations).** A bad close or a mistyped distribution flips a vote. *L* after DAT-02, DAT-04, DAT-10 and DAT-11; impact 2 (one wrong round trip).

**F-36. Telegram (operations).** A Bot API change, a regional block, or a SIM-swap takeover that lets an attacker veto or kill (never trade). *M,* impact 1. BP-11, email backup, OPS-02's lost-message rule. *Missing.* PM-19 (two-step verification).

**F-37. Market-structure change (operations).** ASX's T+1 move is sequenced after CHESS replacement Release 2 and looks unlikely before 2030 [1, ASX advisory-group communiqués via search]. The system assumes the longer cycle, which is the safe direction; OPS-09 cross-checks hours with IBKR. *M,* impact 1.

**F-38. Wash-sale challenge (tax).** A loss sale and a re-buy within weeks, driven by a recorded rule, is unlikely to attract Part IVA attention at this size. *L,* impact 1. TAX-09 and T7 cover it. Do not add automated loss harvesting (R33, R34 agree).

---

## 3. Mitigations: text for the spec, and owner guidance

IDs PM-01 to PM-23 are unused in v2.10 and in reports 31–35. Where a report has already drafted the text, PM adopts it by reference instead of repeating it.

**PM-01. Invest on day zero (owner guidance, plus one row in §17).**
> **§17, new row before G0, "Day zero":** The starting capital and each contribution are not held as idle cash while the system is built. The owner buys the benchmark holding by hand (VAS and VGS at 40/60 at IBKR, or the owner's chosen equivalent), keeps each contract note, and records the trade in a one-page log. `trader init` later imports these parcels as `managed` (OPS-06, O16). This row has no gate; it is the first action of the project.
>
> **Owner guidance:** ask the tax agent (T4) how parcels bought before 1 July 2027 are valued at that date, and keep the 30 June 2027 IBKR statement (PM-14).

Closes F-02's largest cost for two commissions (A$13.20). It also makes the comparison honest: the system must now beat what the owner already holds.

**PM-02. Scope freeze, minimum viable live, and a stop date.**
> **§20, new paragraph "Build budget":** v2.10 is frozen for build. A change is admitted before G4 only if it (a) fixes a defect logged under PM-21, (b) removes scope, or (c) is checklist or owner-guidance text with no code. Proposals from reports 31–35 that add code wait in a backlog until 12 months after go-live, except those this report adopts by name. **Minimum viable live** is: M0; M1; the decision core of M2; sheet-mode execution (PM-03); the ledger, Flex ingestion, reconciliation, alerts and benchmarks of M5; tax records and reports of M6; backups. M3 (research harness and registry) is built after go-live in STATIC mode and decides whether L1 is ever switched on. M7, M8, M9 and M10 are not scheduled. **Stop date:** if G3 has not been passed within 9 months of the first M1 commit [design value — operational], the owner is shown the hours and dollars spent and chooses in writing: continue with a new date, or stop and hold the PM-01 portfolio.

Reordering M3 behind go-live is safe because STATIC needs no H1 pass (PRT-10, PRT-23).

**PM-03. Sheet mode: a first-class execution mode with no gateway.**
> **§11, new requirement PM-03:** `execution.mode` is `sheet` or `api`. In `sheet` mode no gateway container exists. On a planning day the 08:10 plan carries, for each approved intent, an order-sheet line: symbol, side, whole units, limit price rule (the DAT-13 reference ± the configured offset, as a price), earliest and latest entry time (11:30–15:00), and the intent key. Each line is saved as `MANUAL_PENDING`. The owner enters the order in the IBKR app. Next morning's Flex is matched to the pending lines by symbol, side and quantity (section 11, BP-20); a match books the fill with its real price and commission; a quantity or side mismatch is a reconciliation break; a line not filled is carried under PRT-27. Every RSK check runs on the sheet lines at plan time; RSK-03, RSK-06 and RSK-10 are re-checked against Flex before a line is carried. `/veto` removes a line. A filled line is never an override (RSK-33). Go-live (OPS-06) is permitted in `sheet` mode. A move to `api` mode is a code promotion under BP-14. In `api` mode, a failed login or gateway fault on two consecutive broker days issues the same sheet automatically.

Why: about six trades a year; SYS-01 already needs a phone action on each broker day; the gateway, IBC, `ib_async`, order lifecycle, crash-injection, `orderRef` recovery and login-window logic are the largest and least verifiable part of the build (I2, I4–I8, I15–I17 are all unverified). Sheet mode removes F-05, F-19 and F-31 as failure modes, shrinks F-06 and F-02, and keeps the ledger, the rule, the tax records and the discipline of a written plan. The cost: a typing error is possible (limit orders and next-day reconciliation bound it), and the owner could decline to enter a sell, which is the same freedom `/veto … SELL CONFIRM` gives today.

**PM-04. Objective and venue decision before G0, with the numbers in front of the owner.**
> Adopt report 33's `objective: growth | drawdown` (O23) and report 34's O25. **Add to the decision record:** the table in section 1 of report 42, and this sentence signed by the owner: "Running L1 with cash at 0% I should expect to end five years behind a free static holding about three times in four, by a median of about A$3,000–4,000 including running costs. I am buying a lower worst-case loss, which shows up in about three windows in ten." The choice is three-way: L1 here; STATIC here; STATIC in a zero-brokerage account with this system in paper or shadow. Blocks G0.

This is the single most important mitigation: it converts F-01 from a failure into a chosen cost, and it is the only real defence against F-03.

**PM-05. Overlay premium budget.**
> **RSK-30, new criterion (7):** in `L1` mode the monthly report shows the *premium paid*: B2 value minus L1 value on the same flows, after modelled tax, as a percentage of B2, since go-live; and the *claims received*: the largest drawdown saving against B2 in any completed B2 drawdown of 15% or more. If premium paid exceeds `overlay.premium_budget_pct` (10%) [design value — operational] with no claim received, the owner is paged and continues in `L1` only with a written reason and a new budget; otherwise `trader mode static --confirm`. This is a budget, not a performance test: no parameter changes (PRT-26), and the page says that leaving after a long premium-only stretch gives up the claim the premiums were paid for.

**PM-06. Close the cash question before G0.**
> **I9 moves from "G0" to "before any card is frozen"** and is read from the owner's own account, not a rates page. **§1 expectations table, new row:** "Cash while out of the market: IBKR pays [I9] on this balance. At 0%, L1 gives up about 1.2 points a year against the rule the literature describes [R33], about A$800–1,000 of the five-year median [R42 §1]." If I9 is about zero, report 33's card HG1 (cash ETF while a sleeve is OFF) is frozen with H1 and decided at the same G2, not later.

**PM-07. Cost-halt thresholds scale with the tranche count (defect fix).**
> **RSK-26(ii), replace the fixed counts:** let E = 2 × N × (number of live sleeves), the counted events in one full exit and re-entry of every tranche. Below `applies_from_nav_aud`, review at more than 2 × E and halt at more than 3 × E events in 12 months (`order_count_12m: {review_round_trips: 2, halt_round_trips: 3}`). At N = 1 with two sleeves this is the present 8 and 12; at N = 3 it is 24 and 36. M2 test: at N = 3, one full round trip of both sleeves plus one band rebalance sets no review and no halt.

**PM-08. Owner chore budget; automate the entries that can block the rule.**
> **§17, new requirement PM-08:** scheduled owner actions, excluding broker-day approvals, are at most 12 a year [design value — operational]. (a) **Distributions.** If an evaluation would be blocked by `DIST_MISSING` and the vendor reports an amount for that ex-date that agrees within 1% with the amount implied by the adjusted/raw ratio (DAT-11), the vendor amount is stored with status `estimated_vendor`, a WARN is raised and the evaluation runs. The issuer figure, when entered, supersedes it; if it would have changed a vote the owner is paged and the evaluation is re-run as a new revision (SYS-17). Expected ex-date rows are created automatically from the previous year's dates. (b) **Calendar.** Next year's `calendar` rows are generated from the pinned library and checked on every broker day against IBKR trading hours (OPS-09); the hand-load becomes a yearly confirmation. (c) **Spreads** (SYS-30) are entered quarterly. (d) **Restore check.** A scripted restore into a scratch container runs monthly with no owner action and checks row counts and the latest parcel hash; the full drill on a clean machine is yearly. (e) The digest shows the number of overdue owner actions; more than three overdue for 30 days is a PAGE.

A distribution is about 1% of price, so a 10% error in an estimated amount moves the total-return series by about 0.1% [computed]; that can change a vote only on a knife-edge, whereas the block skips the whole month.

**PM-09. Stuck-in-cash escalation and hibernation.**
> **PRT-19, add:** when cash that the rule says should be invested has stayed uninvested for more than one evaluation cycle for any cause (lapsed buys, a halt, a blocked evaluation), every `IDLE_CASH` page states the amount, the date since which it has waited and the benchmark's return over that time in dollars. **New command `trader hibernate --confirm`** (second factor): the instance stops planning rule orders, holds what it holds, and keeps Flex ingestion, reconciliation, tax records, benchmarks, backups and a monthly digest. It refuses while any sleeve's target is ON and its holding is below target by more than the minimum order, and prints the order sheet that would restore the base weights first. Hibernation is the documented state for a long absence.

**PM-10. Dependency rehearsal.**
> **§28, new requirement PM-10:** each quarter in which `execution.mode` is `api`, a scripted job builds a staging image with the newest stable IB Gateway, IBC and `ib_async` releases older than 14 days (BP-10) and runs one paper broker day and the recorded-session replay against it. A failure is a WARN with the diff; a pass makes the image a candidate for BP-14. The monthly report shows months since the last promoted update and the IBKR minimum supported version as last checked (WARN above 6 months).

**PM-11. A validator that cannot share the builder's blind spot.**
> **RND-003, add:** the G2 validator is either a model from a different provider than the builder, or a committed spreadsheet that computes PRT-12 votes and PRT-13 states for both sleeves over the whole development sample from the same monthly series. G2 requires the harness, the validator and the spreadsheet to agree on every state. **§20 code quality, add:** mutation testing on `rules/`, `strategy.py`, `orders.py`, `risk.py` and `tax.py`; CI fails below a 90% mutant kill rate [design value — operational].

L1 is "a one-page rule the owner could run by hand" (§30), so a spreadsheet reference is cheap and is the only check a non-programmer owner can read.

**PM-12. Say what the evidence is and is not.**
> **VAL-21, add:** the 2024+ window is a *code-blind* holdout, not a *designer-blind* one: every card is written with knowledge of 2024–2026. A holdout pass is reported as "consistent", never as out-of-sample confirmation. The only out-of-sample record is data dated after a card's freeze; it is reported separately with its confidence interval from the first month. **RND-012, add:** the Holm family for a go-live decision contains every Family A rule ever proposed as the live rule on these sleeves (H1, R20's alternative vote set, and any later candidate), not only the one under promotion. **RND-027, add:** the pack shows H1's drawdown saving with 2000–02 removed and with 2008–09 removed.

**PM-13. Cooling-off on changes; keep the library quiet.**
> **RND-032, add:** a spec change that adds a live instrument, a signal type, an evaluation frequency or a return claim takes effect no sooner than 90 days after it is written, and may not be written within 6 months of a drawdown above 15% or of a 12-month lag against B2 above 10 points [design values — operational]. **If report 35's library is adopted:** it is built no earlier than 12 months after go-live; its table (RND-047) appears only in the yearly review, never in a monthly report or the dashboard; at most two cards are `promotable` at once; H41 (the negative control on the selection process) has run before any promotion window opens.
>
> **Owner guidance:** if the urge to pick stocks or themes is real, fence it: a separate account, capped at a fixed dollar amount decided now, never topped up from this account. It is cheaper than changing the system.

**PM-14. Tax: facts first, a second opinion, a provision, and one date.**
> Adopt report 34's TAX-16 (three-way check against IBKR's statement and an independent tracker) and TAX-17 (running provision). **Add PM-14:** (a) after each financial year, and after any sale, the instance writes a plain, unencrypted-to-the-owner bundle of facts (every trade, distribution, AMIT amount, 30 June 2027 value and broker statement) to a location off the server; the tax agent is given the facts and the engine's schedule and is asked to confirm the schedule, not to trust it. (b) No return is lodged from the engine's figures while any of T2, T4, T9, T12 or T13 is open; the report header says so. (c) Every planned sell shows the estimated tax and the provision balance. (d) **30 June 2027 checklist, whatever state the project is in:** download the IBKR activity statement for that date; record the closing price of each holding; store both with the O20 materials. (e) Each June the owner confirms that the 2026 Act and its instruments are unchanged (a yearly action under PM-08).

**PM-15. Succession, retirement and handover.**
> Adopt report 34's OPS-14 (estate pack, trusted contact on owner silence) and OPS-15 (`trader retire`). **Add:** the repository holds a `HANDOVER.md` of at most two pages, regenerated at each release: what runs where, how to stop it safely, how to export the tax facts, which subscriptions to cancel, and how to run in sheet or hibernate mode with no code change.

**PM-16. Scale or stop.**
> Adopt report 34's benchmark B3 and RSK-30(6). **Add RSK-30 criterion (8):** at each yearly review, all-in cost (fixed costs under INF-10, commissions, and set-up costs spread over four years) as a share of average NAV. Above `kill.all_in_cost_pct` (2.0%) [design value — operational] at the 24-month review or any later one, the owner continues only with a written reason; the alternatives printed are hibernate (PM-09) and retire (OPS-15). RSK-30(2) is unchanged above A$25,000.

**PM-17. A way to keep deciding without the price vendor.**
> **DAT-01, add case (d):** if no vendor bar has been received for five trading days, the Flex Mark Price for D (available for every held sleeve, including the sentinel unit, DAT-20) may stand as the evaluation close with verdict `SINGLE_SOURCE_FLEX`; the order-time quote (DAT-13) is the second source; DHHF's benchmark series pauses and is back-filled later. The owner is paged once. **O6, add:** before G4 the owner names one alternative end-of-day source whose licence has been read, and the `DataSource` interface has a recorded-response test for it.

**PM-18. Exit runbooks for the broker and for an instrument.**
> **Runbook, two entries.** *Leaving IBKR:* holdings move in specie to another broker (not a disposal where beneficial ownership is unchanged — to be confirmed by the tax agent); the instance continues in sheet mode with statements imported by hand, or is retired (OPS-15). *Replacing an ETF:* `config` carries a pre-registered successor for each live sleeve tracking the same or a near-identical index (decided at G0 with report 33's O24). On a closure notice, an index change, or a SYS-30 spread breach, the successor is adopted without a new H1 card if its tracking difference to the sleeve's proxy index is inside the splice tolerance of RND-024; the switch is made while the sleeve is OFF where possible, otherwise by directing contributions, and a forced sale shows its estimated tax first.

**PM-19. Harden the accounts, not only the server.**
> Adopt report 34 §5.11's six "Before G4" lines (authenticator not SMS, IP restriction, one withdrawal bank account, email second factor, Telegram two-step, port-out lock). **Add:** IBKR trading permissions are limited to ASX shares and ETFs and this is re-checked quarterly with BP-08; a Flex trade in any symbol outside the universe that the owner did not announce is a PAGE, not a WARN (BP-20).

**PM-20. Additional users.**
> **M8 and O10:** struck from the plan. They return only with a one-off written opinion from a lawyer on whether supplying the software with its default rule is advice or arranging (the question R11 and R18 both leave open).

**PM-21. Stop reading; start logging.**
> **§20, add:** no further full-document review of this spec is commissioned. During build, any requirement the builder cannot implement without a choice is logged as a spec defect with the choice made; the log is reviewed weekly and is the only source of spec edits before G4 (PM-02). Each scenario in report 25 becomes an executable fixture; a fixture, not prose, settles a disagreement.

**PM-22. A panic button that does not trap the owner.**
> Adopt report 34's MON-15 (quiet digest by default; a veto needs a typed reason and shows the history of past vetoes). **§15, add:** `/pause` sets a user-requested `HALTED_BUYS` (reason `USER_PAUSE`) in one step: buys stop, the rule's own exits continue; it is cleared like any buys halt and is not counted as an override. When `/kill` is sent while a transition sell is planned or carried, the reply names the sells it blocks and offers `/pause`; the kill takes effect on a second `/kill` within 10 minutes. **Runbook, "panic protocol":** wait 48 hours before any manual trade in a managed symbol; read the expectations statement; the system's exits are the plan.

`KILLED` stays absolute (OD2). `/pause` gives the owner the other, more common wish: "stop buying, but let it get out".

**PM-23. Contributions.**
> Adopt report 34's MON-13 (contribution tracker, missed-contribution WARN, yearly escalation line). **Owner guidance:** a standing bank transfer, set once.

---

## 4. The ten mitigations that matter most

| # | Mitigation | Stories it addresses | Cost |
| --- | --- | --- | --- |
| 1 | **PM-04** Objective and venue decision before G0, signed against the section 1 numbers | F-01, F-03, F-07, F-13 | One decision |
| 2 | **PM-01** Invest by hand on day zero | F-02, F-26 | A$13.20 |
| 3 | **PM-03** Sheet mode as the first live execution mode | F-02, F-05, F-06, F-19, F-31 | Removes build work |
| 4 | **PM-02** Scope freeze, minimum viable live, research harness after go-live, stop date | F-02, F-06, F-20 | Removes build work |
| 5 | **PM-08** Chore budget of 12 a year; automated distribution and calendar entries | F-04, F-30, F-24 | Small build |
| 6 | **PM-13** 90-day cooling-off on spec changes; library deferred and shown yearly | F-03, F-16 | Text only |
| 7 | **PM-06** Close the cash-rate question and decide the cash ETF with H1 | F-11, F-01 | One lookup, one card |
| 8 | **PM-14** Tax facts export, second opinion, provision, 30 June 2027 checklist | F-08, F-24, F-25, F-26 | Small build |
| 9 | **PM-16** with **PM-05** Scale-or-stop cost criterion and overlay premium budget | F-01, F-07, F-12 | Two report lines |
| 10 | **PM-15** with **PM-09** Retire, hibernate, estate pack, handover page | F-04, F-06, F-22, F-29 | Small build |

**Fix regardless of ranking:** PM-07 (the cost-halt count at N = 3). It is a defect, not a judgment.

---

## 5. What should change in the overall plan

1. **Re-order the plan around the modal outcome.** Today the sequence is: build everything, prove L1, then invest. The pre-mortem says the likely end states are "L1 runs and lags", "STATIC runs at a cost" or "never finished". A sequence that is robust to all three: invest now by hand (PM-01); decide the objective (PM-04); build the ledger, tax records, signals and sheet mode (PM-02, PM-03); go live in STATIC; run L1 in shadow from the freeze date, which starts the only genuinely out-of-sample record (PM-12); build the research harness and decide G2 afterwards; add API execution only if manual entry proves to be the weak point.
2. **Treat the spec as finished enough.** Six successive reviews have not driven the finding count to zero (43, 16, 13, 6, 5, 10). More reading will not either. Code, fixtures and a defect log will (PM-21).
3. **Do not adopt report 35's challenger library, report 31's satellite or report 32's brake before 12 months of live operation.** Each is defensible alone. Together they roughly double the research surface of a system whose live rule has not yet placed an order, and they are the mechanism of F-03 and F-16. The shadow L1 record gives the owner "what would X have done?" for the one rule that matters.
4. **Drop M8 (other users) and M7 (public dashboard); leave M9 and M10 unscheduled.** None helps the owner's account, and M8 carries the only legal risk in the project (F-28).
5. **Give 30 June 2027 its own checklist.** It is 7½ months away, the system will probably not be live, and the valuation on that date follows every parcel for life (PM-14(d)).
6. **Add three dated reviews to the calendar now:** 24, 36 and 60 months after go-live. At each: premium paid and claims received (PM-05), all-in cost (PM-16), chores overdue (PM-08), months since the last update (PM-10). The default at each is to continue; the point is that the decision is made on a quiet day with numbers, not on a bad day without them.
7. **Keep what is already right.** The independent breaker, reconciliation barrier, two halt classes, parcel ledger, benchmarks on every report, no-AI trade path and honest expectations statement are stronger than anything a retail platform offers (R34 §1). None of the failure stories above comes from those parts. The failures come from the size of the build, the cost of running it at A$5,000, and the person in the loop.

---

## 6. Reasons this report could be wrong

- The simulation uses assumed returns, volatilities and regime lengths. A decade containing a slow, deep bear market would reverse F-01's verdict for that decade; the model gives that about one chance in four over five years.
- My likelihoods for F-02, F-03, F-04 and F-13 are judgments, tagged [unverified]. The evidence for F-03 (the owner's own follow-up questions) could equally be read as healthy curiosity that reports 31–35 have now satisfied.
- Sheet mode gives up some of the discipline that full automation provides. If the owner would in practice decline to type an exit, API mode is safer. The spec's `/veto … SELL CONFIRM` already allows the same refusal, so I judge the difference small.
- PM-08(a) trades a small accuracy risk for liveness. If the tax agent wants issuer figures only, the vendor estimate still never reaches a tax report (it is superseded before year end).
- The F-09 defect is my reading of RSK-26(ii) and the `order_count_12m` comment in §18. If "event" was meant to be per sleeve and not per tranche, the text needs clarifying and not the number.
- I did not re-verify the 2026 CGT Act or any IBKR or EODHD term. Everything tax-related here inherits R18's limits.

---

## 7. New IDs and where they land

| ID | Where | Kind |
| --- | --- | --- |
| PM-01 | §17 new row; owner guidance | Text |
| PM-02 | §20 build budget | Text, re-ordered milestones |
| PM-03 | §11, §18 `execution.mode` | Build (replaces most of M4 for first go-live) |
| PM-04 | §21.1 (with R33 O23, R34 O25); §30 | Owner decision |
| PM-05 | RSK-30(7); §18 `overlay.premium_budget_pct` | Report line |
| PM-06 | I9; §1 table; card HG1 timing | Text, one card |
| PM-07 | RSK-26(ii); §18 `order_count_12m` | Defect fix |
| PM-08 | §17; DAT-22; OPS-05; SYS-30; BP-16 | Small build |
| PM-09 | PRT-19; new `trader hibernate` | Small build |
| PM-10 | §28 | Scripted job |
| PM-11 | RND-003; §20 | Process, CI |
| PM-12 | VAL-21; RND-012; RND-027 | Text, two report rows |
| PM-13 | RND-032; R35 RND-040/047 if adopted | Text |
| PM-14 | §13 (with R34 TAX-16, TAX-17); runbook | Small build, checklist |
| PM-15 | §17 (with R34 OPS-14, OPS-15) | Small build |
| PM-16 | RSK-30(8) (with R34 B3, RSK-30(6)) | Report line |
| PM-17 | DAT-01; O6 | Small build |
| PM-18 | Runbook; §18 successor table | Text, config |
| PM-19 | "Before G4"; BP-20 | Checklist |
| PM-20 | M8, O10 | Scope removal |
| PM-21 | §20 | Process |
| PM-22 | §15 (with R34 MON-15); runbook | Small build |
| PM-23 | (R34 MON-13); owner guidance | Adopt |

---

## 8. Sources

Project documents: `FD_FINAL.md` v2.10 (sections cited inline); `research2/11`, `13`–`18`, `20`, `25`, `31`–`35` (cited as R11 and so on, with their own tags).

Web searches run for this report (read as search summaries, not pages):

- `ib_insync` archived March 2024 after its author's death; `ib_async` is the fork IBKR's documentation points to; maintenance ratings conflict. [IBKR: ib_insync and ib_async](https://www.interactivebrokers.com/docs/tws-api/doc/third-party-api-platforms/non-standard-tws-api-languages-and-packages/ib-insync-and-ib-async) · [ib-api-reloaded](https://github.com/ib-api-reloaded) · [ib_async on PyPI](https://pypi.org/project/ib_async) · [Snyk Advisor](https://snyk.io/advisor/python/ib_async)
- IBKR raised the minimum supported TWS and IB Gateway version to 10.30 from 20 March 2025. [IBKR TWS API changelog, 13 January 2025](https://www.interactivebrokers.com/docs/tws-api/changelog/2025/1/13) · [IBKR version control](https://www.interactivebrokers.com/docs/third-party-integrations/version-control)
- ASX T+1 is sequenced after CHESS replacement Release 2; no date set. [ASX T+1 page](https://asx.com.au/markets/clearing-and-settlement-services/t1-settlement-cycle) · [Advisory Group communiqué, 25 September 2025](https://www.asx.com.au/content/dam/asx/about/advisory-group/advisory-group-communique-20250925.pdf) · [Finadium](https://finadium.com/?p=142632)
- Post-2009 record of the 10-month timing rule. [Canadian Couch Potato, "The failed promise of market timing"](https://canadiancouchpotato.com/2013/12/30/the-failed-promise-of-market-timing/) · [Swedroe, ETF.com](https://www.etf.com/sections/index-investor-corner/swedroe-why-financial-trends-persist) · [Mutual Fund Observer, on Zakamulin](https://www.mutualfundobserver.com/?p=4056)

Simulation: 20,000 paths × 60 months, parameters as stated in section 1; E[max of N standard normals] re-derived by simulation as 1.16 (N = 5), 1.54 (N = 10), 1.63 (N = 12), matching R35 §6.2.
