# Platform gap analysis: v2.10 against robo-advisers, auto-invest brokers and serious DIY practice

Report 34, 13 November 2026. Written against FD_FINAL.md (v2.10) and reports 31–33. General information only: not financial, tax or legal advice. Where a section touches the owner's personal position (estate, household, tax) it sets out questions for the owner, a solicitor or a registered tax agent; it does not recommend a personal course.

**Scope.** The owner feels the spec still has "massive gaps". This report looks for them by comparing v2.10, feature by feature, with what real products and well-documented DIY systems do. Report 33 already covers super against a personal account, the growth/drawdown objective, cash interest, debt first, Stage 2, parcel selection, the tranche threshold, owner reporting (MON-09 to MON-12), cheaper ETFs and contribution batching. Those are not repeated; they appear in the matrix as "33" and are discussed only where a platform comparison changes the answer.

**Tags.** **[primary]** the page itself was read in full (added in the v2 pass). **[2+]** two or more independent publishers agree. **[1]** one publisher (for a platform's own behaviour this is usually the platform's own page, marked "issuer"). **[unverified]** sources conflict, are old, or the point is my inference. **[computed]** my arithmetic from tagged inputs or from the spec's own numbers.

**Access limits (important).** In the first pass direct page fetches were blocked for every host tried, so everything was read as search-engine extracts. In the v2 pass Betashares, Vanguard and IBKR Australia pages were read directly (see the changelog above); every other platform is still an extract. Fee schedules are the weakest part: several Australian platforms returned conflicting figures from different dates, and those are tagged [unverified]. Section 9 lists what to re-check before relying on any number. To read the primary pages those hosts would need to be allowed in the session's network settings. A second, deeper pass (about 30 further searches) resolved several of the conflicts; what it changed is folded into the text, and what remains open is in section 9.

## v2 verification changelog (13 November 2026, later the same day)

`curl` through the session proxy reached three issuer hosts that the fetch tool could not: betashares.com.au, vanguard.com.au and interactivebrokers.com.au (plus morningstar.com.au and raw.githubusercontent.com). Pages read in full are now tagged **[primary]**. Still blocked (proxy answered 403 to CONNECT): stockspot.com.au, sixpark.com.au, raizinvest.com.au, spaceship.com.au, pearler.com, investsmart.com.au, webull.com.au, cmcmarkets.com, hellostake.com, superhero.com.au, commsec.com.au, intercom.help, fund-docs.vanguard.com, nucleuswealth.com, finder.com.au, asic.gov.au, sharesight.com, betterment.com, wealthfront.com, bogleheads.org; ato.gov.au returned 403 from the site. Those rows stay as search extracts.

| # | What changed | Before | After |
| --- | --- | --- | --- |
| 1 | Gap 1 headline | "A$204–288 a year against A$0" | A$204–288 holds only against plain self-directed auto-invest. Against a platform that also rebalances automatically it is **A$156–252** (Betashares custom portfolio costs A$36–48 a year under A$10,000) or **A$192–276** (Stockspot, A$12 a year). At A$50,000 the gap against a Betashares custom portfolio is about **0.2–0.4%**, not 0.4–0.6% |
| 2 | "Zero brokerage" is not zero cost | Stated as A$0 | Vanguard: A$0 to buy, **A$9 to sell**, **whole ETF units** in Auto Invest, A$200 a cycle, fortnightly, monthly or quarterly [primary]. Betashares Direct: A$0 both ways, but **it keeps all interest on the cash wallet**, and free auto-invest covers **Betashares ETFs only** [primary] |
| 3 | Betashares Direct minimum and fees | "Recurring from A$100"; custom portfolio "0.20% p.a." | Minimum **A$10** with fractional units; custom portfolio **A$3 a month under A$10k** (Betashares ETFs only) or **A$4–4.50 a month** (any ETFs or shares), then 0.20–0.30% p.a. tiering down; transfer out up to A$9.50 a security [primary] |
| 4 | CMC Invest | "then 0.11%" | A$0 on the first ASX buy up to A$1,000 a day, then **A$11 or 0.10%** [2+, Betashares' comparison table as at 19 March 2026] |
| 5 | Stake, Superhero, Pearler, Selfwealth | [1] or conflicting | Stake A$3 to A$30,000; Superhero A$2 to A$20,000, custodial; Pearler A$6.50, A$650 minimum per holding in autoinvest; Selfwealth A$9.50 [2+] |
| 6 | Stockspot fee | [1 issuer] | A$1 a month under A$20,000; 0.66% from A$20,000 to A$200,000 **[2+]** (Morningstar AU read in full agrees). Morningstar also says Stockspot harvests tax losses "through the algorithm" [1]; still not confirmed on Stockspot's pages |
| 7 | Raiz fee | A$4.50–5.50 under A$20k [unverified] | Morningstar AU: **A$5.50 a month under A$26,000, 0.275% above**, ETF costs extra; rebalances on drift, not on a schedule [1, read in full]. Other extracts give other thresholds; still unconfirmed on Raiz's site |
| 8 | IBKR Australia | Search extracts | **[primary]**: fixed commission 0.08%, minimum A$6.00 before GST (A$6.60 with GST, as the spec assumes); 0% interest on the first A$15,000 of AUD, 3.85% above; recurring investments and fractional shares cover US, Canadian and European stocks only; third-party deposits generally rejected; up to five power-of-attorney users and a second user; PortfolioAnalyst has a free standalone version; ASX holdings sit with sub-custodian BNP Paribas, and the page warns this may affect access to the National Guarantee Fund |
| 9 | Betashares article on CGT and one-fund ETFs (§5.16(b)) | Read by title; I guessed the argument was about rebalancing inside the fund | Read in full. The argument is about **indexation applying asset by asset**: an asset that grows slower than inflation wastes its indexation, and a loss gets none, so two ETFs held separately can be taxed on more than their combined real gain. The article itself says in-fund rebalancing distributes some gains. Section rewritten |
| 10 | AUST | A$32m (March 2026) | **A$26.5m** net assets at 13 November 2026; fee 0.49%; 5-year return 4.25% a year [primary] |
| 11 | pysystemtrade reports | Headings only | Nine scheduled reports confirmed: roll, P&L, status, trade, reconcile, strategy, risk, liquidity, costs; plus trade limits, position limits and overrides [primary] |

No ranking changed. Gap 1 stays first: the smallest version of it (A$156 a year at A$5,000, 3.1%) is still larger than any other in-system item.

---

## 0. Answer in brief

1. **The algorithm is not where the gaps are.** On signals, execution safety, reconciliation, audit, kill switches, backup and a parcel-level tax ledger, v2.10 is at or above every retail platform reviewed and in line with the best-documented DIY practice (pysystemtrade). No platform reviewed has a pre-registered test regime or a 2027-CGT engine.
2. **The gaps are in everything a product wraps around the algorithm.** Platforms are built around the owner's life: money arrives automatically, the risk level is chosen by questionnaire, the household and the estate are handled by account types, tax statements come from a second party, and nobody has to keep a server alive. v2.10 treats most of these as out of scope or as one line in §21.
3. **The largest single finding is a cost one.** If the account ends up in STATIC mode (H1 fails at G2, or the owner picks the growth objective as report 33 recommends), the system holds two Vanguard ETFs and tops them up. Vanguard Personal Investor does exactly that with A$0 brokerage on buys (A$9 on sells) and Auto Invest from A$200 a cycle [primary]; Betashares Direct does the A200/BGBL equivalent with A$0 brokerage both ways [primary]; Webull Australia lists A$0 brokerage on Australian ETFs with CHESS sponsorship and auto-invest [2+, extracts]. Even a full robo-adviser is cheaper at this size: Stockspot charges A$1 a month under A$20,000 [2+]. Against plain auto-invest, STATIC mode on this system costs about A$204–288 a year more at A$5,000 (4.1–5.8%) for the same holdings; against a platform that also rebalances for the owner, about A$156–276 more [computed from §1 and §19 of the spec and the platform fees]. The spec says DHHF-and-nothing is better for wealth, but it has no benchmark, kill criterion or exit path that acts on it.
4. **Three gaps cost nothing to close and matter more than any signal change:** automatic contributions with a missed-contribution alert; a one-page successor note plus an executor-readable tax export; a recorded goal, horizon and tolerable loss with a yearly review.
5. **Two popular platform features should stay out:** automated tax-loss harvesting (confirming report 33, with the platform evidence added) and direct indexing.

### Top 15 gaps, ranked by impact

| Rank | Gap | Evidence of value | Recommendation |
| --- | --- | --- | --- |
| 1 | STATIC mode is dominated by a zero-brokerage auto-invest account; no benchmark or rule acts on it (§5.1) | A$204–288 a year at A$5,000 (4.1–5.8%) against plain auto-invest; A$156–276 against a platform that also rebalances; 0.2–0.6% at A$50,000 [computed] | Live spec: benchmark B3, RSK-30 criterion 6, PRT-23 notice, §30 point 1. Owner decision before G4 |
| 2 | Contributions are not automated, tracked or escalated (§5.2) | Missing two of twelve A$500 contributions a year: about A$12,900 less after 10 years; a 3% yearly rise: about A$10,300 more [computed, 5% return] | Live spec: MON-13. Owner guidance: standing bank transfer |
| 3 | Death, incapacity and long absence: no successor path, tax records locked behind the owner's key (§5.3) | Not a %/yr item; the whole balance and its cost-base records | Live spec: OPS-14; "Before G4" check. Owner guidance: will, enduring power of attorney |
| 4 | No risk profile, goal, horizon or review; one 100%-equity mix for every user (§5.4) | Investor return gap 0.4 pp a year in the least volatile funds against 2.1 pp in the most volatile [2+] | Live spec: USR-15 (record and warnings only). Owner guidance |
| 5 | The account is run blind to the household: super, partner, other holdings; other entity types refused (§5.5) | Allocation across the household outweighs anything inside a A$5,000 account; not estimable | Live spec: MON-14 (information only). Reject a multi-entity engine now |
| 6 | Tax output has no independent check, no return mapping and no running tax provision (§5.6) | One wrong CGT schedule under a new law costs more than a year of running costs; a tracker check is free for up to 10 holdings [1] | Live spec: TAX-16, TAX-17; tax-agent item T16 |
| 7 | Behavioural design: NAV pushed to the phone daily; a veto costs one message (§5.7) | Traders shown prices less often took 33% more risk and earned 53% more [1 paper]; behavioural coaching valued near 150 bps [1] | Live spec: MON-15 |
| 8 | Band rebalancing ignores the 12-month date; Betterment will not sell short-term lots to rebalance (§5.8) | About 0 at A$5,000; up to roughly 0.1–0.2% a year at A$50,000 [unverified estimate] | Tested card HP1 |
| 9 | No retirement or hibernation path; one maintainer; third-party API churn (§5.9) | Avoids A$164–209 a year on an unattended system and an orphaned live trader | Live spec: OPS-15 |
| 10 | Withdrawals sell pro rata; M1 and Betterment sell the overweight holding first (§5.10) | Saves an occasional band sell (A$6.60 plus brought-forward CGT) | Live spec: PRT-28 amendment |
| 11 | Broker-account hardening is not in the go-live checks (§5.11) | Tail risk on the whole balance | "Before G4" checklist text |
| 12 | Custody and investor-protection facts are not disclosed to the owner (§5.12) | Tail risk; grows with the balance | Owner guidance: §30 point 7 (extends report 33 §7) |
| 13 | A$1,000 minimum order and whole units against platform minimums of A$5–500 (§5.13) | About A$10 a year of cash drag at A$500 a month [computed] | Reject fractional units; handled by rank 1 and report 33 §2.3, §2.10 |
| 14 | Automated tax-loss harvesting and direct indexing (§5.14) | US claims of 0.5–1.3% a year rest on US rules that do not exist here [2+] | Reject (confirms report 33 §2.6) |
| 15 | Projections with a range, and a first-month owner pack (§5.15) | Not estimable | Small extension to MON-12 (report 33); owner guidance |

---

## 1. What v2.10 already does as well as or better than the platforms

So these are not re-listed as gaps.

| Area | v2.10 | Best comparable |
| --- | --- | --- |
| Cash-flow rebalancing (new money to the underweight sleeve before any sell) | PRT-16(b) | Stockspot, Betterment, Wealthfront, M1 all do this [1 issuer each] |
| Threshold (not calendar) rebalancing with a wide relative band | ±20% relative, PRT-16(c), card H4 | Daryanani found 20% relative bands best, with frequent looks [2+]; the "5/25" rule is the common DIY form [2+]; Betterment uses 3% total drift [1 issuer] |
| Rebalance timing luck | Tranches, card H5 | Newfound: timing luck often above 100 bps a year in rules-based indexes; remedy is tranching [2+] |
| No-trade buffer and minimum trade | A$1,000 minimum, band | Carver: about a 10% buffer around the target; it cuts cost, not return [2+ secondary] |
| One code path for backtest and live; trial log; frozen cards | SYS-11, RND-010 to RND-016 | QuantConnect/LEAN shares code between backtest and live and documents reconciliation [1 issuer]; no retail platform pre-registers |
| Reconciliation to the unit and cent; idempotent orders; restore drill | SYS-02, BP-16 to BP-20 | pysystemtrade production: reconcile, status, risk, costs and five other reports; trade limits, position limits, overrides [primary] |
| Kill switch, veto, dead-man monitor, zero inbound ports | §15, BP-09 | QuantConnect cloud: Telegram/email/SMS notifications, auto-restart [1 issuer]. No robo gives the client a kill switch |
| Parcel ledger, 45-day franking test, 2027 CGT regime, AMIT adjustments | §13 | Australian platforms issue annual tax statements; none found that documents parcel-level 2027 handling |
| Benchmarks on every report; no return claim | SYS-07, PRT-25 | Stockspot publishes comparisons; most platforms show no benchmark |

---

## 2. Australian platforms

All rows are search extracts. "Issuer" = the platform's own page.

| Platform | Portfolio construction | Rebalancing | Contributions | Tax features | Cash | Fees | Custody and accounts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Stockspot** (robo, personal advice under an MDA [1 issuer]) | Questionnaire on goals, experience and risk capacity maps to one of five ETF portfolios of shares, bonds and gold [1 issuer]. Optional themes | Threshold: assets that move "a certain distance" from target are rebalanced automatically; the distance is not published in what I could read. Deposits, withdrawals and distributions are used first [1 issuer]. Client can set always rebalance, buy only, or pause; buy only is the default in its super product, to limit CGT [1 issuer]. ETFs must have at least A$25m and a track record [1] | Top-ups invested once they reach A$500 (A$2,000 for A$200k+) [1 issuer] | Annual tax documents [1 issuer]. Tax-loss harvesting: Morningstar AU lists "tax loss harvesting through the algorithm" in Stockspot's proposition [1, read in full]; not confirmed on Stockspot's pages | "Stockspot Savings" holds a cash ETF, minimum A$1,000 [1 issuer] | A$1 a month under A$20,000; 0.66% p.a. for A$20k–200k [2+: issuer extracts and Morningstar AU read in full]; 0.528% above A$200k; 0.396% above A$2m; minimum A$1,000 [1 issuer]. An older third-party review quotes A$5.50 a month, taken as out of date | Individual HIN per account [1 issuer]. Individual, joint, kids, company, trust, SMSF, plus a super product [1 issuer] |
| **Six Park** (robo) | Five portfolios, up to seven ASX ETFs; investment committee [1, old] | "Periodic rebalancing" included [1] | Not found | Reporting included; no harvesting found | Not found | About A$10–11 a month on small balances, 0.5% above, tiering to 0.35% [unverified; sources several years old] | Not found |
| **Raiz** (micro-investing) | Preset and custom ETF portfolios | Automatic when the portfolio strays too far from target, not on a schedule; no extra charge [2+] | Round-ups, recurring, minimum A$5 [1] | Annual statement. In October 2026 Raiz told the ATO and ASIC of a historical tax withholding and reporting issue and began remediation [1: a competitor's blog] | — | A$5.50 a month under A$26,000, 0.275% above, ETF costs extra [1: Morningstar AU, read in full]; other extracts give A$4.50 and a A$20k threshold [unverified] | Custodian model [1]. Kids and super products |
| **Spaceship Voyager** | Managed funds (unit trusts), not client-held ETFs | Inside the fund | Recurring, tiny minimums | Fund tax statement | — | A$2 a month per issuer help page; other sources A$2.50 or 0.10% above A$5k [unverified] | Unit trust |
| **InvestSMART** | Managed ETF portfolios (PMA) | Managed | — | Statements | — | Percentage fee to a dollar cap; cap quoted as A$451, A$550 and A$880 in pages of different dates [unverified]; brokerage and ETF fees extra | — |
| **Pearler** | Self-chosen ETFs with target weights | Autoinvest buys toward target weights on deposit or schedule [1] | Autoinvest; A$650 minimum per holding per run [2+] | Reports; integrates with trackers | — | A$6.50 per trade [2+], A$5.50 prepaid [1]; Pearler Plus A$3 a month [1] | CHESS-sponsored [2+]; Micro, kids ("Headstart") and super products |
| **Betashares Direct** | Any ASX ETF or share; "AutoPilot" pre-built or custom portfolios | Custom portfolios rebalance automatically, can be switched off; no threshold published [primary] | Auto-invest: recurring orders into up to five **Betashares** ETFs, free; other issuers' ETFs or shares need a custom portfolio. Minimum A$10, fractional units. Direct debit or the portfolio's own BSB [primary] | CGT and income reporting [primary] | Cash wallet: **Betashares keeps the interest** [primary] | A$0 brokerage on all ASX ETFs and 550+ shares, auto-invest, account, deposit, withdrawal. Custom portfolio: A$3 a month under A$10k then 0.20% tiering to 0.14% (Betashares ETFs only); A$4 a month then 0.25% (1–10 holdings of any kind); A$4.50 then 0.30% (11–50). Transfer out up to A$9.50 a security [primary] | Custodial [primary]. Individual, joint, trust, SMSF, company, kids [primary] |
| **Vanguard Personal Investor** | Vanguard ETFs and funds, incl. VAS and VGS | None for self-chosen ETFs [unverified]; diversified funds rebalance internally | Auto Invest: A$200 per cycle, at least one whole unit per ETF, fortnightly, monthly or quarterly, into one or several Vanguard funds and ETFs [primary] | Annual statement | Cash account | A$0 to buy Vanguard ETFs, A$9 flat to sell; no account fee on Vanguard ETFs and funds; 0.10% p.a. and A$9 a trade on ASX direct shares [primary] | Custodial, no HIN [2+] |
| **Superhero** | Self-directed | None | Auto Invest into ASX shares and ETFs [1 issuer] | Statements | — | A$2 up to A$20,000, then 0.01% [2+] | Custodial [2+]; super product |
| **Stake** | Self-directed | None | ASX recurring buys: sources conflict [unverified] | Statements | — | A$3 up to A$30,000, then 0.01% [2+] | CHESS for ASX [2+] |
| **CommSec Pocket** | Seven to ten themed ETFs | None | Recurring | CommSec statements | CBA account | A$2 to A$1,000, 0.20% above [2+] | CHESS |
| **Webull Australia** (added) | Self-directed | None | Auto-invest into Australian and US shares and ETFs [1] | Statements | — | A$0 brokerage on Australian and US ETFs per its own site; about A$1 on ASX shares [2+] | CHESS, individual HIN [1] |
| **CMC Invest** (added) | Self-directed | None | Not found | Statements | — | A$0 on the first ASX buy up to A$1,000 a day, then A$11 or 0.10% [2+] | CHESS |
| **Nucleus Wealth** (added; managed accounts held at IBKR Australia) | Tactical multi-asset and direct-indexed portfolios run by the manager | Manager's discretion | Deposits to the IBKR account | Statements | — | 0.165% passive, 0.64% active on one page; 0.33% and 0.80% on another; minimum A$10,000 [1 issuer; conflicting] | Same custody as this system |

**What the Australian set shows.**

- Every one of them moves money in by direct debit or recurring order. None needs the client to approve a login.
- The two robo-advisers start from a questionnaire and offer a range from conservative to aggressive. The auto-invest brokers leave the mix to the client.
- Where rebalancing is described, it is threshold-plus-cash-flows, as in v2.10. No Australian platform publishes its drift number in anything I could read.
- Tax help is a year-end statement. Automated loss harvesting is at most a claim about one platform [unverified].
- Brokerage for small regular buys has fallen to A$0–2 at six of the eight brokers listed. IBKR's A$6.60 minimum is now the outlier for A$500 orders.
- Stockspot's default for its super product is buy-only rebalancing, to avoid realising gains [1 issuer]. That is the same idea as card HP1.
- A manager already runs tactical portfolios on IBKR Australia for a percentage fee (Nucleus Wealth). At A$10,000 its quoted active fee is A$64–80 a year against this system's A$164–209 fixed cost. It is discretionary, not L1, so it is a cost reference and not a substitute.

---

## 3. Global platforms with a documented method

| Platform | Documented method (source tag) | Relevance to v2.10 |
| --- | --- | --- |
| **Betterment** | Three rebalancing methods: cash-flow, sell/buy, allocation change. Drift = half the sum of absolute deviations; default trigger 3% for ETF portfolios. A portfolio is left drifted if only short-term lots could be sold. Lot choice "TaxMin": losses first, then long-term gains from smallest; short-term gains avoided [1 issuer, two documents]. Tax Loss Harvesting+ headline estimate 0.77% a year, disputed by an outside analyst as assumption-driven [2+]. Goals with a time horizon get a glide path ("auto-adjust") that de-risks toward the date; Tax Impact Preview shows estimated tax before an allocation change; Tax Coordination places assets across account types [1 issuer] | Tax-aware band (card HP1); goal and horizon record (USR-15); tax provision (TAX-17) |
| **Wealthfront** | Risk score 0.5–10 from a questionnaire on age, income, net worth and tolerance; client asked to update yearly [1 issuer]. Rebalances with deposits and dividends first; threshold-based otherwise [2+]. Daily loss-harvesting scan; "harvesting yield" 3.10% in 2025, 5.45% a year since inception (losses harvested ÷ assets, not after-tax return) [1 issuer]. Direct indexing from US$100,000 [2+] | Yearly review of the risk record; harvesting rejected (§5.14) |
| **Schwab Intelligent Portfolios** | Cash allocation in every portfolio, about 6–10% in one comparison [1]; loss harvesting opt-in from US$50,000, daily review; rebalancing can be blocked 30+ days by wash-sale avoidance [2+] | Shows a harvesting programme delays rebalancing; supports rejecting it |
| **Wealthfront Autopilot / Betterment Two-Way Sweep** (added) | The platform watches the client's bank balance and moves cash above a chosen cushion into savings or investments, cancelling a transfer if the balance has fallen [2+] | The far end of contribution automation (§5.2). Not possible with IBKR, which will not pull money |
| **M1 Finance** | "Dynamic rebalancing": new money buys the most underweight slices; withdrawals sell the most overweight; changing a target triggers no trade [2+] | Withdrawal sourcing (PRT-28 amendment) |
| **Composer** | Rebalance by schedule or by threshold ("corridor"): no trade until weights leave the band [1 issuer] | Same as PRT-16(c) |
| **QuantConnect / LEAN** | Cloud live trading with Telegram, email, SMS and webhook notifications, automatic restart, a documented live-versus-backtest reconciliation; notification services are not available on local LEAN [1 issuer] | v2.10 builds these itself (MON-01, MON-07) |
| **Alpaca** | Free paper environment; fractional and notional orders; a Rebalancing API with drift-band and calendar triggers [1 issuer]. US securities only | Fractional/notional is the feature v2.10 lacks; not available for ASX through the IBKR API (§5.13) |
| **Portfolio Visualizer** | Backtests with rebalancing bands (default 5% absolute / 25% relative), Monte Carlo with contributions and withdrawals [2+] | Range projections (§5.15) |
| **Passiv; IBKR's own tools** (added) | Passiv links to an IBKR account, computes the trades that restore a target mix, and notifies when cash arrives or the portfolio drifts; one-click trading is a paid tier [1: IBKR partner page; Australian availability not confirmed]. Trader Workstation has a Rebalance Portfolio window [1 issuer]. PortfolioAnalyst links outside accounts and hand-entered "offline" assets into one net-worth view [1 issuer; super funds not named] | A static 40/60 with drift alerts can be had on IBKR without this system (§5.1). PortfolioAnalyst may already give the household view (§5.5) |
| **Singapore and Canadian robos** (added) | StashAway re-optimises on a macro-regime model; Syfe rebalances about six-monthly; Wealthsimple rebalances automatically and harvests losses above C$100,000 [1, comparison sites] | Nothing new for v2.10 |
| **ASIC RG 255** (added; what a licensed Australian robo must do) | Monitor and test the algorithm; have people review samples of its output; filter out clients it does not suit; explain its scope [2+] | v2.10 meets the algorithm controls by its own design (Part B, §28). The "filter out clients it does not suit" step is the missing one (§5.4) |

## 4. Serious DIY practice

| Source | Practice | v2.10 |
| --- | --- | --- |
| **pysystemtrade / Carver** | Production stack with nine scheduled reports (roll, P&L, status, trade, reconcile, strategy, risk, liquidity, costs), trade limits, position limits, trade overrides, and four kinds of backup [primary: production.md]. Buffering around the target [2+ secondary]. Maintainer changed in 2024 and the repository moved to a new organisation in January 2026 [1] | Has the controls. The maintainer change is evidence for §5.9: even the reference DIY system needed a succession |
| **Newfound Research** | Rebalance timing luck; tranching [2+] | Has (H5) |
| **Alpha Architect** | Robust Asset Allocation: each sleeve half on a 12-month time-series momentum rule and half on a moving-average rule, out to bills otherwise; DIY weights published monthly [1 issuer] | Has (L1 is the same family, with a third vote and hysteresis; R14, R15) |
| **Vanguard research** | Threshold 200 bps with a destination 175 bps from target beat calendar rebalancing by about 5–22 bps a year in target-date funds; lowest cost per event [2+]. Adviser's Alpha: behavioural coaching about 150 bps, rebalancing 0–51 bps, not additive [1] | Band has; "destination" is in card HP1's grid; coaching is §5.7 |
| **Bogleheads** | Wiki: an investment policy statement sets targets, the 5%-absolute or 25%-relative bands, a review at least yearly, and new money directed to the targets first; all accounts are treated as one portfolio [1 wiki, two pages]. Chapter material: a letter of instruction for the surviving spouse or executor [1] | Missing: policy statement (§5.4), household view (§5.5), letter of instruction (§5.3) |

---

## 5. The gaps

### 5.1 STATIC mode is dominated by a zero-brokerage account (rank 1)

**What the spec says.** PRT-23: if H1 does not pass, or a kill criterion is confirmed, the account holds 40/60 with no trend filter. Report 33 §2.2 goes further and recommends STATIC as the live mode for a growth objective. Section 30 point 1 says DHHF-and-nothing is the better choice for wealth at A$5,000. RSK-30 criterion 2 (costs above 3% a year) applies only from A$25,000.

**What platforms do.** Vanguard Personal Investor: A$0 to buy Vanguard ETFs, A$9 flat to sell, no account fee on Vanguard ETFs, Auto Invest of A$200 a cycle in whole units, fortnightly to quarterly [primary]. Betashares Direct: A$0 brokerage both ways, fractional units from A$10, free auto-invest into its own ETFs, and an optional auto-rebalanced custom portfolio at A$3 a month under A$10,000 (its own ETFs) or A$4 a month (any ETFs), then 0.20–0.25% a year; it keeps the interest on uninvested cash [primary]. Report 33 §2.9 already prefers A200 and BGBL, which are Betashares funds; Betashares' free auto-invest covers only its own funds [2+]. Webull Australia: A$0 brokerage on Australian ETFs of any issuer, CHESS-sponsored, with auto-invest [2+; affiliate-style reviews plus its own site; one review notes poor customer ratings]. CMC Invest: A$0 on the first buy up to A$1,000 per stock per day [2+]. Stockspot: A$12 a year under A$20,000 for advice, rebalancing, an individual HIN and tax statements, with bonds and gold in the mix [1 issuer].

**Evidence of value** [computed from the spec's own figures].

| | This system in STATIC mode | Zero-brokerage auto-invest |
| --- | --- | --- |
| Fixed running cost | A$164–209 a year (§1) | A$0 |
| Top-ups at A$500 a month | A$39.60–79.20 a year (6 or 12 buys at A$6.60) | A$0 |
| Total at A$5,000 | A$204–288 a year, 4.1–5.8% | A$0 self-directed; A$12 Stockspot; A$36–48 Betashares custom portfolio with auto-rebalance |
| **Gap at A$5,000** | — | **A$204–288** against self-directed; **A$192–276** against Stockspot; **A$156–252** against a Betashares custom portfolio |
| Total at A$50,000 | A$204–288, 0.4–0.6% | A$0 self-directed; about A$100 (0.20%) Betashares custom portfolio; about A$330 (0.66%) Stockspot |
| Selling | A$6.60 minimum | A$9 at Vanguard; A$0 at Betashares |
| Idle cash | 0% under A$15,000 at IBKR [primary] | Betashares keeps the interest [primary]; Vanguard not checked |
| Ten years of the A$204–288, invested at 5% | About A$2,600–3,600 | — |

**What the platform does not give.** No trend overlay; no API; custodial holding (as IBKR is); platform-generated tax records only; no contribution-to-underweight logic at Vanguard for self-chosen ETFs [unverified], and whole units there; rebalancing sells cost A$9 at Vanguard; a fee appears at Betashares once automatic rebalancing is wanted; at Stockspot the fee passes this system's cost at roughly A$31,000–44,000 [computed: A$204–288 ÷ 0.66%]; no learning value. In L1 mode the comparison does not apply: no platform runs L1.

**Applicability in Australia.** Direct. Moving holdings between brokers without a change of beneficial owner is generally not a disposal [unverified this session]. IBKR Australia holds through a custodian, so a move to a HIN broker goes through the receiving broker's transfer form; some receiving brokers charge nothing, and IBKR Australia's outbound fee was not found [unverified].

**Cost and complexity.** One more benchmark series in code that already tracks two; one kill-criterion line; two sentences of text.

**Recommendation: add to the live spec, and an owner decision before G4.**

> **PRT-22, add:** B3 = the zero-brokerage benchmark: static 40% VAS / 60% VGS; each external flow invested in full at the next close in the underweight sleeve, whole units, no commission on buys, no fixed running cost, uninvested cash at 0%; rebalanced yearly as B2 with a modelled fee of `benchmarks.b3_sell_fee_aud` (A$9) per sell [design value — operational]. B3 is tracked daily in the ledger and shown wherever B1 and B2 are shown (SYS-07). It is the cost of running this system instead of an auto-invest account, not a strategy.
>
> **RSK-30, add criterion (6):** the account has been in `STATIC` mode for 12 months and its all-in cost over those months (fixed running costs entered under INF-10 plus commissions) exceeds `kill.static_cost_pct` (1.0%) of average NAV [design value — operational]. As with every criterion, the owner continues only with a written reason; "I am running it to learn" is an acceptable reason and is recorded.
>
> **PRT-23, add:** the page that announces static mode states the trailing 12-month all-in cost in dollars and says that the same two funds can be held in a zero-brokerage auto-invest account without this system.
>
> **Section 30, point 1, add:** "In static mode this system holds what a zero-brokerage auto-invest account holds, at a cost of about A$160–290 a year more at A$5,000, depending on the account compared. I am paying that for the trend overlay if it is on, for my own records, and to learn."
>
> **Section 21.1, new item O25:** before G4, decide what happens if G2 puts the account in static mode: run static here; or hold the money in an auto-invest account and run this system in paper until L1 is eligible or the account is large enough that RSK-30 (6) no longer bites. Blocks G4.

### 5.2 Contributions are not automated, tracked or escalated (rank 2)

**What the spec says.** Section 30 names contributions as the largest lever. O7 records a planned amount for backtests. PRT-19 commits a deposit when Flex books it. Nothing notices a contribution that does not arrive, and nothing prompts a rise.

**What platforms do.** Every Australian platform in §2 pulls money by direct debit or recurring order. IBKR does not pull: a deposit notification "does not move money", the holder must send it by bank transfer or BPAY, which takes 1–2 business days [1 issuer]. IBKR Australia's recurring-investment page offers "US, Canadian and European shares" only [primary]. IBKR "strongly discourages and, generally, rejects third-party deposits" [primary]; whether a joint bank account counts as third-party in Australia is not stated (its Hong Kong entity says it does) [1].

**Evidence of value.**

- Automatic escalation: in the first Save More Tomorrow plan, saving rates went from 3.5% to 13.6% over 40 months for those who joined [2+]. The US Labor Department's evidence review rates the causal strength as low (no control for self-selection), so treat it as direction, not size.
- A$5,000 start, 5% return, 10 years [computed, assumptions]: A$500 every month ends near A$85,300. Missing two months a year ends near A$72,500 (−A$12,900). Raising the amount 3% a year ends near A$95,600 (+A$10,300); 5% a year, near A$103,300.
- For comparison, report 33's largest in-system item (rank 2) is about A$68 a year at A$5,000.

**Applicability.** Direct. A scheduled transfer from the owner's bank on pay day does the pulling; the system only has to notice.

**Cost and complexity.** Low: one config block, one check on Flex cash rows, one digest line.

**Recommendation: add to the live spec; owner guidance.**

> **MON-13 Contribution tracker.** Config `contributions: {amount_aud, frequency, day, escalation_pct}` holds the plan the owner gave under O7. If no deposit of at least 80% of `amount_aud` is booked from Flex within 5 trading days after a planned date, the digest carries WARN `CONTRIBUTION_MISSED` once [design value — operational]. The monthly report shows contributions planned and made for the financial year and since inception. On the first business day of July the digest carries one line: the current amount, the amount after `escalation_pct` (default 3%), and the MON-12 projection for each. The system never moves money (PRT-28) and the line names no security.
>
> **O7, add:** set a standing transfer to IBKR, from a bank account in your own name alone, for the planned amount on the day after pay day. Allow two business days for it to be booked. If the amount is below A$1,000, every second transfer triggers the buy (PRT-17).

### 5.3 Death, incapacity and long absence (rank 3)

**What the spec says.** Nothing: no occurrence of estate, successor, attorney or incapacity. O20 covers key recovery by the owner. Report 33 §7 gives one bullet (a "how to stop it" note). This section works the case through.

**What happens today if the owner dies or cannot act** [inference from the spec].

- Every broker day needs an IBKR login approval on the owner's phone (SYS-01). So no order is sent. A risk-off sell carries and pages every day (PRT-27, §15). In effect the account freezes at its current holdings. That is a safe failure, but it is nowhere stated, and the pages go to a phone nobody reads.
- The dead-man monitor pages the same phone. Server, data, domain and monitor subscriptions keep billing.
- The only complete record of parcels, cost bases and the 30 June 2027 valuations is in a database and in backups encrypted with a key only the owner holds.

**What the law and the broker need.**

- Once told of a death, a broker locks a sole-name account until the executor produces a death certificate and a grant of probate or letters of administration [2+: CommSec, Macquarie, Bell Direct for Australian practice; secondary sources for IBKR]. IBKR's own FAQ says that on receipt of a certified death certificate it starts estate processing, that the steps vary by account type and jurisdiction, that a non-US resident's account is classed as deceased with trading and transfers generally prohibited until legal authority is shown, and it gives an Asia-Pacific estate mailbox for Australian accounts [1 issuer]. IBKR Australia's individual-account page offers "up to five optional Power of Attorney users" and an optional second user [primary].
- Assets acquired after 20 September 1985 pass to a beneficiary at the deceased's cost base; the beneficiary pays the CGT on a later sale [1: ATO guide, several years' editions]. The executor therefore needs the parcel records this system holds. Under the 2027 law they also need the 30 June 2027 values (TAX-05).
- An enduring power of attorney ends at death; the will and the executor take over [2+: NSW Government, SA Law Handbook]. It covers incapacity, which is the more likely case. There is often a gap of months before a grant issues, during which nobody can trade the account.

**What platforms do.** Robo and broker platforms offer joint accounts (survivorship), trust and company accounts, and publish an estate process. They hold the tax records themselves, so an executor can ask for them. Bogleheads practice adds a plain-language letter of instruction [2+ secondary].

**Applicability.** Direct. Australian non-super investments have no beneficiary nomination; they pass by will or intestacy [unverified this session].

**Cost and complexity.** One export command and one page of text. No change to the trade path.

**Recommendation: add to the live spec; owner guidance.**

> **OPS-14 Successor pack and owner silence.** (a) `trader estate-pack` writes, to a location the user names, a bundle that contains no secret: the latest TAX-10 reports; the full parcel ledger with acquisition dates, cost bases, AMIT adjustments and `valuations_2027` as CSV and PDF; the list of holdings and the IBKR account number's last three digits; and a one-page letter built from a fixed template. The letter says: what this system is; that if it is left alone it sends no order, because each trading day needs the owner's phone approval; that switching the server off is safe and leaves the holdings at IBKR; that IBKR must be told of a death and will ask for a grant of probate or letters of administration; where the tax records are and why the executor needs them; and which subscriptions to cancel (server, data, domain, monitor, object store). The pack is refreshed automatically after each financial-year report and after any sale. The user stores a copy where their executor and attorney can reach it without a password (paper, or a solicitor's file). (b) Config `ops.trusted_contact_email` (optional). If no plan acknowledgement, login approval or command has been received from the user for `ops.owner_silent_days` (45) [design value — operational], the instance emails the trusted contact once, and again at 90 days, with a fixed text that names the letter and carries no plan, signal, holding or balance (so USR-09 is not engaged). No run state changes: orders already cannot be sent without the owner. (c) Section 4 states this behaviour in one sentence so that it is a designed property, not an accident.
>
> **"Before G4" checks, add:** the estate pack has been generated and a copy placed with the O20 materials; the user has recorded who holds it.
>
> **Owner guidance (not spec):** a current will; an enduring power of attorney that covers financial accounts; ask IBKR Australia whether it will register the attorney now; tell the executor that this account exists. Before an absence of more than a month with no phone coverage, decide in advance whether a missed risk-off sell is acceptable; if not, the choices are static mode or cash before leaving.

### 5.4 No risk profile, goal, horizon or review (rank 4)

**What the spec says.** One mix, 100% equities, for every user. RND-034 is an expectations statement about the system, not about the user. Report 33 §2.2 adds a growth/drawdown switch. Neither asks when the money is needed or what fall the user can sit through in dollars.

**What platforms do.** Stockspot: a questionnaire on goals, experience and risk capacity selects one of five portfolios [1 issuer]. Wealthfront: a 0.5–10 risk score, re-asked yearly [1 issuer]. Betterment: each goal has a horizon and de-risks toward its date [1 issuer]. Bogleheads: write the policy down first [2+ secondary].

**Evidence of value.** Morningstar's 2026 study: investors earned 1.2 points a year less than their funds over ten years; the gap was 0.4 points in the least volatile funds and 2.1 in the most volatile, and smallest in all-in-one allocation funds [2+]. The mechanism is selling after falls. A holding that fits the stated tolerance is the cheapest defence. The spec's own planning drawdown is −25% under L1 and −35% to −50% in static mode (§1). On horizon: about 7 of roughly 142 rolling five-year periods in 146 years of Australian share data were negative, and none of eight years or longer [1 originator, two outlets; price or accumulation basis not stated]. A five-year floor is the usual rule of thumb and that record is why. ASIC's guide for licensed digital advice expects a provider to filter out clients its product does not suit [2+]; v2.10 has no such step, by design, because it gives no advice. Selling takes T+2 and the transfer out one to two business days more, so the money is about a week away.

**Applicability.** Direct. The system gives no advice (§30 point 7), so it must not choose a mix for the user. It can record the user's own answers and say when they conflict with the configured mode.

**Cost and complexity.** Low: a stored record and three comparisons. No trade-path change.

**Recommendation: add to the live spec (record and warnings only).**

> **USR-15 Investment policy record.** At `trader init`, and each July, the user records in their own ledger: the purpose of the money; the earliest date any of it is needed; the largest fall in dollars they state they would hold through; whether cash for emergencies is held elsewhere (yes/no); and the contribution plan (MON-13). The instance then checks and reports, without changing any order: (a) WARN if the earliest date is less than `policy.min_horizon_years` (5) away; (b) WARN if the stated fall, as a share of NAV plus 12 months of planned contributions, is smaller than the planning drawdown of the configured mode (25% for `L1`, 35% for `STATIC`; section 1) [design value — operational]; (c) from `policy.notice_months` (24) before the earliest date, one line in each monthly report giving the date and the balance. The messages name no product and propose no trade; a different mix is a spec change (SYS-31). The record is stored beside the RND-034 acceptance, and the yearly re-entry is the user's review.

### 5.5 The account is run blind to the household (rank 5)

**What the spec says.** TAX-03 refuses any entity but a resident individual. The dashboard shows this account only. Report 33 §2.1 treats super as a competing destination, and §7 notes "whose name" as a tax-agent question.

**What platforms do.** Stockspot offers individual, joint, kids, company, trust and SMSF accounts and sets the fee tier on the combined balance [1 issuer]. IBKR Australia itself offers individual, joint, trust, company and (cash-only) SMSF accounts [1 issuer]. Betterment coordinates asset placement across account types [1 issuer]. Bogleheads practice treats every account as one portfolio [2+ secondary].

**Why it matters.** For most working Australians super is many times A$5,000 and already holds Australian and global shares. A 40% VAS sleeve here may double an existing home bias; the trend overlay protects a small slice while the large slice rides every fall. None of that is visible to the owner from this system.

**Applicability in Australia.**

- Joint or partner accounts: a tax question first (33 §7).
- Children: unearned income of a minor above A$416 is taxed at 66% of the excess, and at 45% on the whole once above A$1,307 [2+]. A child's instance is therefore not a sensible build target; the usual forms are a parent as trustee or an investment bond.
- Trusts, companies, SMSFs: each needs a different tax engine (no discount for companies; 15% and a one-third discount in super).

- An SMSF is commonly put at cost-effective from about A$200,000, with running costs of roughly A$1,300–5,000 a year for a simple fund [1–2, secondary]. It is not a route for this account.
- IBKR's PortfolioAnalyst links outside brokerage, bank, card, mortgage and loan accounts into one net-worth view and has a free standalone version [primary]; super funds are not named. If it can hold a super balance as an offline asset, the owner has a household view today without any build.

**Recommendation.** Reject a multi-entity engine now (cost high, no user). The owner tries PortfolioAnalyst first. If it cannot show the split below, add the information-only view; either way keep the door open in the schema.

> **MON-14 Household view (information only).** A table `external_holdings` holds rows the user types in: label, wrapper (`super`, `personal`, `joint`, `cash`, `offset`), value, as-at date, and percentages in Australian shares, international shares and defensive assets. The dashboard shows the combined split with this account as one row, and this account's share of the total. Rows older than 12 months are marked stale. No module on the trade path can read the table (import test, as SYS-18). The view names no product and suggests no trade.
>
> **TAX-03, add one sentence:** the `tax.entity` field and the parcel schema carry the entity type so that joint, trust or super accounts can be added by a later spec change without a migration; v2.10 still refuses every value but `individual`.

### 5.6 Tax output: no second opinion, no return mapping, no provision (rank 6)

**What the spec says.** One tax engine, written for this system, implements a law that takes effect on 1 July 2027 and that no one has yet lodged a return under. TAX-10 exports CSV and PDF. TAX-08 applies AMMA statements. Report 33 adds a tax estimate on each planned sell.

**What platforms do, and how they fail.** Platforms issue a year-end statement that the client can check against ATO pre-fill. The ATO's own guidance is that pre-filled managed-fund data can differ from the fund's statement and that the fund's statement prevails [1: ATO, two pages]. A platform's statement can also be wrong: Raiz began a remediation programme in October 2026 for historical tax withholding and reporting errors [1: competitor's blog]. Betterment shows the estimated tax before a client confirms a change [1 issuer].

Brokers, registries and fund managers have had to report share and unit transactions to the ATO since 1 July 2017, and the ATO matches them against returns [1: ATO]. Pre-fill itself is narrower: distributions usually appear, disposals usually do not, so the capital gain is the investor's own figure [1].

**Why it matters.** The ATO can see the disposals this system makes. A single-source tax calculation is the one place in v2.10 where the two-source principle (D8, DAT) is not applied. An independent tracker exists: Sharesight's free plan covers 10 holdings, connects to IBKR and produces an Australian CGT report, and it has published a calculator for the CGT reform [1 issuer]. It will not match the engine line for line, but a large difference is a flag worth an hour.

**Tax provision.** L1 realises gains about once a year per sleeve. The tax falls due up to 16 months later, from money outside the account. Separately, the ATO enters individuals into PAYG instalments when the last return shows A$4,000 or more of gross investment or business income, tax payable of A$1,000 or more and notional tax of A$500 or more; capital gains are excluded from instalment income [1: ATO via extract]. At a 4% distribution yield that is an account near A$100,000, so it is a growth-path item.

**Recommendation: add to the live spec.**

> **TAX-16 Independent check.** The financial-year report (TAX-10) is marked `cross-checked` only when all three are recorded: (a) every distribution component agrees with the fund's AMMA statement (TAX-08); (b) proceeds, quantities and trade dates of every disposal agree with IBKR's annual statement, and the difference between the engine's realised gain and IBKR's own realised figure is explained by parcel method and the regime slices; (c) the user has entered the ATO pre-fill figures for each fund once available, and each difference is listed with the note that the fund's statement prevails. `trader tax export --generic` writes all trades and distributions in a plain CSV that a third-party tracker can import, so that the user or the agent can recompute the CGT schedule independently. The report says which checks are open.
>
> **TAX-17 Tax provision.** The monthly report shows, for the current financial year under the user's flags and marginal rate: realised net capital gain by slice, distributions and franking credits to date, and the estimated tax attributable to the account (TAX-06 method), labelled "set aside outside this account". WARN `PAYG_LIKELY` when gross distributions plus interest for the year pass `tax.payg_income_threshold` (A$4,000) [design value — operational; T16].
>
> **Section 21.2, new item T16:** Which return labels does each line of the TAX-10 report feed? Is the PAYG instalment entry test as TAX-17 states it? (Blocks nothing; sets the report's label column.)

### 5.7 Behavioural design: what is pushed, and how easy an override is (rank 7)

**What the spec says.** A digest at 20:00 every trading day with NAV, unit price, holdings and the result against B1 and B2 (§15). `/veto SYMBOL` blocks a buy with one message. Overrides are counted (RSK-30 criterion 5) and limited by a pledge (§30 point 6).

**Evidence.**

- A field experiment on professional traders: those shown prices less often put 33% more into the risky asset and earned 53% more [1 paper: Larson, List and Metcalfe, NBER 22605]. Short-horizon traders, so direction only.
- Morningstar's gap of 1.2 points a year (§5.4) [2+]. Vanguard values "staying the course" coaching near 150 bps, the largest single item in its framework, and warns the items are not additive [1].
- Report 33 §2.8 covers what reports should contain. It does not cover how often a balance is pushed or what a veto costs the user to send.

**What platforms do.** Betterment puts a tax-cost screen between the client and an allocation change [1 issuer]. Stockspot lets a client pause rebalancing but not pick trades [1 issuer]. None pushes a daily balance by default [unverified].

**Recommendation: add to the live spec.**

> **MON-15 Quiet default and override friction.** (a) Config `digest.level`: `quiet` (default) or `full`. In `quiet` the daily digest carries the status line, WARN items, blocked orders and the next evaluation date; NAV, unit price and the comparison with the benchmarks appear in the plan, the fills message, the monthly report and on `/status`. Every MON-01 delivery rule is unchanged. (b) `/veto` needs a reason in the same message (`/veto VGS because …`); a veto without one is answered with the format and is not applied. The reply to an applied veto states how many vetoes the user has made in the trailing 12 months and, for each earlier one, the dollar difference to date between what happened and the vetoed plan, computed by replay. `/kill` is unchanged: one step, no reason.

### 5.8 Band rebalancing ignores the 12-month date (rank 8)

**What the spec says.** PRT-16(c): a sleeve more than 20% (relative) above target is sold to target. Which parcels go is set by `parcel_method`; the sale happens whatever their age.

**What platforms and research do.** Betterment leaves a portfolio drifted when the only lots it could sell are short-term [1 issuer]. Vanguard's target-date work found that stopping short of target (175 bps from it after a 200 bps trigger) lowers cost [2+]. Stockspot uses cash flows first to avoid "avoidable capital gains" and lets a client set buy-only [1 issuer].

**Value.** Under both regimes a parcel sold inside 12 months gets neither the discount on its pre-July slice nor indexation, and from 1 July 2027 pays at least 30% (TAX-04, R18). The two sleeves are both equities, so a few months of extra drift carries little risk. At A$5,000 with monthly contributions a band sell is rare: about nil. At A$50,000 with no contributions, roughly 0.1–0.2% a year at most [unverified estimate; the card measures it].

**Recommendation: tested hypothesis card.** It changes the trade path, so it is not spec text.

**Card HP1 — Tax-aware band rebalance** (ID provisional; renumber at registration. Thresholds are [design value — set by backtest], frozen before the first run.)

| Field | Value |
| --- | --- |
| ID / date registered / card hash | HP1 / at freeze / at freeze |
| Economic rationale | A band sell of a parcel inside its 12-month date gives up the discount or indexation for a small risk benefit, because the two sleeves are highly correlated. Betterment's documented rule defers such sells; Vanguard's research finds a destination short of target cheaper |
| Exact rule | The active mode exactly as §9.1, except PRT-16(c): a band sell may use only parcels at or past their 12-month date (TAX-02). If those parcels cannot bring the sleeve to target, the sell is for what they can supply and the remainder waits. The deferral ends, and any parcel may be sold, once the sleeve's weight exceeds target × (1 + 2 × `band_relative`). Transition sells, withdrawal sells and top-ups are unchanged |
| Fixed parameters | `band_relative` 20%; escape at 2× band; destination = target; parcel method as configured; costs and tax per RND-021 and RND-022, both CGT regimes; N = 1, offset `last` |
| Permitted perturbation grid | Escape multiple 1.5 / 2 / 3; destination = target, or target × (1 + ½ band); defer only when the parcel is within 3 / 6 / 12 months of its date |
| Data and proxy map | As H1 and H4 |
| Sample and holdout | As H1: 1990-01 to 2023-12 development; 2024-01 onward holdout |
| Benchmark | The same mode with PRT-16(c) as in v2.10 |
| Primary metric (one) | After-tax, after-cost CAGR difference at sizing NAV A$50,000 with no contributions, at the 30% rate |
| Secondary metrics | The same at A$5,000 with A$500 a month; maximum drawdown difference; tracking error to B2; number of deferred sells; longest deferral; largest sleeve weight reached |
| Pass / fail | Pass: at least +0.05 pp a year at A$50,000 **and** maximum drawdown no more than 0.5 pp worse **and** the largest sleeve weight never above target × (1 + 2.5 × band). Fail: below 0 pp, or drawdown more than 1 pp worse. Between: not passed (RND-015) |
| Family and adjustment | A, design choice decided by threshold, no significance test (as H4, H10) |
| Trials consumed / result / decision / approver | At run / — / adoption is a spec change to PRT-16(c) / owner |

### 5.9 No retirement path; one maintainer; third-party churn (rank 9)

**What the spec says.** Images and dependencies are pinned; a restore drill runs quarterly (BP-16). Nothing says how the system is shut down for good, or what happens when the owner stops maintaining it. No occurrence of retire, hibernate or decommission.

**Evidence.** pysystemtrade, the reference DIY system, changed primary maintainer in 2024 and moved to a group organisation in January 2026 [1]. A commercial platform absorbs broker API and gateway changes for its clients; here the owner does. A live trader that nobody updates is an operational risk; one that nobody uses still costs A$164–209 a year.

**Recommendation: add to the live spec.**

> **OPS-15 Retirement.** `trader retire --confirm` (second factor) ends an instance cleanly: it cancels this system's open orders; runs the final reconciliation; writes the estate pack (OPS-14) and the tax reports for the current and all earlier years; takes and verifies a final backup; disables the scheduler and the gateway containers; and prints the list of subscriptions to cancel. Holdings and cash stay at IBKR untouched. After it, the runner refuses to start without a fresh `trader init`. The monthly kill-criteria report (RSK-30) includes one line: the months since the last code or dependency update was promoted, with a WARN above `ops.max_months_without_update` (12) [design value — operational].

### 5.10 Withdrawals sell pro rata (rank 10)

**What the spec says.** PRT-28: withdrawal sells are "pro rata to current value across the sleeves".

**What platforms do.** M1 sells the most overweight slices first [2+]. Betterment and Stockspot treat a withdrawal as a rebalancing opportunity [1 issuer each].

**Value.** Small: a withdrawal that also trims the overweight sleeve removes a later band sell and its commission, and avoids selling the underweight sleeve only to buy it back with the next contribution.

**Recommendation: add to the live spec.**

> **PRT-28, change:** withdrawal sells are taken first from the sleeve that is furthest above its target weight, down to target; any remainder is taken pro rata to target weights across sleeves that hold units above the sentinel floor. A sleeve whose target weight is zero is sold first. The rounding, the floor, the buffer and the exemption from the minimum order are unchanged. (M2 test: a withdrawal fixture with one overweight sleeve sells that sleeve only.)

### 5.11 Broker-account hardening is not in the go-live checks (rank 11)

**What the spec says.** The server is hardened in detail (§19, BP-09, INF-02 to INF-08). The IBKR account, the email behind it and the Telegram account are not: no occurrence of IP restriction or Secure Login in the spec.

**What exists.** IBKR's Client Portal has IP restrictions, which take one to two business days to apply [1 issuer]. Withdrawal limits depend on the second-factor method under its Secure Login System [1 issuer]. Commands come only from an allow-listed chat ID (§15), so whoever controls the owner's Telegram account can veto buys or kill; a kill blocks exits until cleared on the server.

**Recommendation: checklist text.**

> **"Before G4" checks, add:** (a) IBKR two-factor login is the mobile authenticator, not SMS; (b) where the server's outbound address is fixed, IBKR IP restrictions are set to it and a broker day is run in paper afterwards (allow two business days); where it is not fixed, this is recorded as not applied; (c) the IBKR withdrawal instruction names one bank account in the owner's name; (d) the email address on the IBKR account has its own second factor and is not used elsewhere as a login; (e) Telegram two-step verification is on; (f) the mobile carrier account has a port-out lock where the carrier offers one. Each is a dated line in the "Before G4" record.

### 5.12 Custody and investor protection (rank 12)

Report 33 §7 notes that IBKR Australia is custodial. The platform comparison adds:

- Stockspot, Pearler, Stake (ASX) and CommSec hold on an individual HIN; Betashares Direct, Vanguard Personal Investor, Raiz, Spaceship and IBKR are custodial [2+ for the split; 1 for some names].
- IBKR Australia [primary]: client money is reconciled at least daily; ASX and Cboe Australia holdings are held by sub-custodian BNP Paribas on a HIN sponsored by BNP, with the client as beneficial owner; "this custodial arrangement may impact whether or not you would be entitled to access compensation available under the National Guarantee Fund"; securities custodied with its US affiliate are covered by SIPC to US$500,000.
- The Compensation Scheme of Last Resort pays up to A$150,000 on an unpaid AFCA determination about personal advice, securities dealing for retail clients, credit or credit intermediation [2+]. It needs an AFCA determination first, so it is not a deposit guarantee and not a custody guarantee.

**Recommendation: owner guidance.** Extend report 33's proposed sentence in §30 point 7: "My holdings are held for me by IBKR's sub-custodian, not on a HIN in my name, and that may affect any claim on the National Guarantee Fund. I keep each IBKR statement off the server (TAX-10), because it is my evidence of what I own." No build.

### 5.13 Minimum order and whole units (rank 13)

Platforms invest A$5 (Raiz [1]), A$10 with fractional units (Betashares Direct [primary]), A$200 in whole units (Vanguard [primary]) or A$500 (Stockspot [1]) at a time. v2.10 waits for A$1,000 and buys whole units. At A$500 a month, on average about A$250 extra sits idle; at 4.2% that is about A$10 a year [computed]. IBKR Australia's fractional trading covers US, Canadian and European stocks, not ASX [primary], and the A$1,000 minimum exists because of the A$6.60 commission (H4), not by choice. **Reject** fractional units. The real remedy for small regular amounts is rank 1 (a zero-brokerage account) or report 33 §2.10 (larger, less frequent transfers).

### 5.14 Automated tax-loss harvesting and direct indexing (rank 14)

Report 33 §2.6 rejects automated harvesting. The platform evidence supports that:

- Betterment's 0.77% a year and Vanguard's 0.47–1.27% assume US rules: losses offset US$3,000 of ordinary income a year and short-term gains taxed at income rates [2+]. An outside review found the figure highly sensitive to assumptions and partly captured by ordinary tax-aware rebalancing [1]. Wealthfront's 3–5% "harvesting yield" is losses realised over assets, not return [1 issuer]. Betterment itself calls harvesting "primarily a tax deferral strategy" [1 issuer].
- In Australia a capital loss offsets only capital gains. There is no statutory 30-day rule; TR 2008/1 applies Part IVA to a sale and reacquisition of the same or substantially the same asset where the tax benefit is the dominant purpose, and the ATO says it finds wash sales with registry data [2+]. A scheduled harvesting programme is that purpose written down.
- Schwab discloses that harvesting can block rebalancing for 30 days or more [1 issuer].

Direct indexing starts at US$100,000 at Wealthfront [2+] and needs hundreds of positions; it has no place in a two-ETF account. **Reject both.** L1's own loss-making exits, with their recorded non-tax reason (TAX-09), already bank losses when the rule sells.

### 5.15 Projections with a range; a first-month owner pack (rank 15)

Portfolio Visualizer and the robo planners show a range of outcomes with contributions and withdrawals [2+]. Report 33's MON-12 shows three fixed return lines. **Small extension:** MON-12 also shows a 10th–90th percentile band from a block bootstrap of B2's monthly returns, labelled "range of past outcomes, not a forecast", with no strategy input. On education, platforms run learning hubs; v2.10 has the owner's guide and the expectations statement, which is enough. **Owner guidance:** read the guide again after the first drawdown review, not only before go-live.

---

### 5.16 Smaller items from the deeper pass (not ranked in the top 15)

**(a) Yearly instrument review.** Stockspot screens its ETFs on size (at least A$25m), track record and cost, and publishes a yearly ETF report [1]. v2.10 checks spreads monthly (SYS-30) and treats a replacement as a new card (SYS-31), but nothing asks each year whether a sleeve's fund is still the right one. Report 33 §2.9 does this once (A200, BGBL). *Add to the live spec:*

> **SYS-30, add:** each July the user records, for every live ETF and for the cheapest fund on the same or an equivalent index: management fee, funds under management, the year's average reported spread, and tracking difference against the index for the year, all from the ASX monthly report and the issuers' pages. A WARN is raised if a live ETF's funds under management are below A$100 million, or if an equivalent fund is cheaper by more than `instrument_review.fee_gap_pct` (0.05% a year) [design value — operational]. The WARN starts a review; it changes nothing by itself (SYS-31).

**(b) One fund against two, under indexation; and switching inside a fund.** Two separate points.

*Indexation is applied asset by asset.* Betashares' article of 20 October 2026 [primary] shows that from 1 July 2027 an asset that grows more slowly than inflation wastes part of its indexation, and a loss gets none. Its example: two A$10,000 ETFs, 15% inflation over five years, combined sale value A$24,000. Held separately the taxable gain is A$2,500; held as one diversified ETF it is A$1,000; under the old discount both were A$2,000. The issuer is selling its own funds, and it concedes that rebalancing inside a diversified ETF distributes some gains. The mechanism is nonetheless the law as TAX-04 implements it, and it applies to this system: VAS and VGS are separate assets, and so is every parcel. A sleeve that lags inflation over its holding period gets indexation it cannot use, while the other sleeve is taxed in full. L1 makes this worse, because most of its disposals are inside 12 months and get no indexation at all (report 33 §2.6).

*Switching inside a fund is not a disposal by the holder.* One listed fund manages equity risk internally: Betashares Managed Risk Australian Share Fund (AUST), the 200 largest shares with an overlay that sells index futures, fee 0.49%, A$26.5 million in net assets at 13 November 2026, five-year return 4.25% a year, and by its own description limited in rising markets [primary].

Neither is a recommendation: AUST is small and costs seven times VAS's fee; one-fund ETFs carry the structure questions in report 33 §2.9. *Recommendation: reject as live holdings now; make the comparison visible, because under the 2027 law the one-fund question is a real after-tax effect and not only a convenience.*

> **PRT-22, add (reference series, paper only):** the monthly report shows AUST's total return beside the VAS sleeve's L1 return since go-live, labelled "a listed fund that manages risk inside the fund; reference only". The G2 report states the after-tax terminal value of B1 (one fund) against B2 (two funds held separately) under both CGT regimes at the user's rate, with the part of the difference that comes from indexation that could not be used shown as its own line. Neither series is a benchmark for any hypothesis, and neither can be traded without a new card (SYS-31).
>
> **Section 21.2, T13, add:** from 1 July 2027, is indexation applied parcel by parcel, so that a parcel sold for less than its indexed cost base but more than its cost gives neither gain nor loss, as TAX-04 assumes?

**(c) The first month in cash.** After the canary the money waits about 20 trading days (OD6). Platforms invest the next day. At a 7% expected return the wait costs about A$29 once at A$5,000 [computed], plus the 0% cash rate in report 33 §2.3. It is a deliberate safety step and stays. *No change.*

**(d) A drift-alert tool on the same broker.** Passiv and IBKR's own Rebalance Portfolio window (§3) mean that a static 40/60 with alerts needs no custom system even at IBKR. This adds weight to §5.1 and needs no further text.

---

## 6. Feature matrix

Columns: **AU robo** = Stockspot, Six Park, Raiz, Spaceship, InvestSMART. **AU auto-invest** = Pearler, Betashares Direct, Vanguard Personal Investor, Superhero, Stake, CommSec Pocket. **Global robo** = Betterment, Wealthfront, Schwab, M1. **DIY** = Composer, QuantConnect, Alpaca, Portfolio Visualizer, pysystemtrade, Bogleheads practice. "Yes" means at least one platform in the group documents it (see §2–§4 for which, and the tag). **v2.10**: has / partial / missing. **Where**: this report's section, "33 §x" for report 33, or the spec ID.

| Area | Feature | AU robo | AU auto-invest | Global robo | DIY | v2.10 | Where |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Portfolio | Diversified ETF core | Yes | Yes (client picks) | Yes | Yes | has | PRT-11 |
| Portfolio | Risk-graded choice of mix | Yes | No | Yes | Policy statement | missing | §5.4 |
| Portfolio | Bonds, gold, defensive sleeve | Yes | Client picks | Yes | Yes | partial (Stage 2) | 33 §2.5 |
| Portfolio | Ethical or themed option | Yes | Client picks | Yes | — | missing; owner preference, via SYS-31 | — |
| Portfolio | Direct indexing | No | No | Yes (US$100k+) | — | missing; reject | §5.14 |
| Portfolio | Yearly review of the funds held | Yes | No | Yes | — | partial (monthly spread check) | §5.16(a) |
| Portfolio | Risk managed inside a fund (no disposal by the holder) | Diversified funds | AUST, diversified ETFs | Yes | — | missing by design; reference only | §5.16(b) |
| Signals | Trend or other tactical overlay | No | No | No | Yes | has | §9.1 |
| Signals | Pre-registered tests, trial log | No | No | No | Partly (QC) | has | Part B |
| Execution | Automatic orders, no client step | Yes | Yes | Yes | Yes | partial (daily phone approval) | SYS-01 |
| Execution | Limit orders, spread checks, order caps | Not disclosed | Not disclosed | Not disclosed | Yes | has | §10, §11 |
| Execution | Fractional or dollar orders | Yes | Some | Yes | Alpaca | missing; reject | §5.13 |
| Execution | Zero or near-zero brokerage on small buys | In fee | Yes (A$0–2) | Yes | — | missing (A$6.60) | §5.1 |
| Rebalancing | Cash flows first | Yes | Pearler | Yes | Yes | has | PRT-16(b) |
| Rebalancing | Drift threshold | Yes | Betashares (periodic) | Yes (3%) | Yes | has (±20% relative) | PRT-16(c) |
| Rebalancing | Tax-aware (defer short-term lots; buy-only switch) | Stockspot | No | Betterment | — | missing | §5.8, HP1 |
| Rebalancing | Timing-luck control | No | No | No | Newfound | has | PRT-14, 33 §2.7 |
| Cash | Interest on idle or risk-off cash | Some | Some | Yes | — | missing | 33 §2.3 |
| Contributions | Direct debit or recurring order | Yes | Yes | Yes | — | missing | §5.2 |
| Contributions | Missed-contribution notice, escalation prompt | Some | Some | Yes | — | missing | §5.2 |
| Contributions | Sweep of spare bank cash above a cushion | No | No | Wealthfront, Betterment | — | missing; not possible at IBKR | §3 |
| Contributions | Round-ups | Raiz | No | Some | — | missing; reject (needs fractional) | §5.13 |
| Tax | Parcel-level CGT ledger | Statement | Statement | Yes | Trackers | has | TAX-01 to TAX-05 |
| Tax | Lowest-tax parcel choice | Not disclosed | No | Yes (TaxMin) | — | partial (FIFO/HIFO) | 33 §2.6 |
| Tax | Loss harvesting | Claimed for one [unverified] | No | Yes | — | missing; reject | §5.14, 33 §2.6 |
| Tax | Franking and 45-day test | Statement | Statement | n/a | — | has | TAX-07 |
| Tax | 2027 CGT regime | Not found | Not found | n/a | Sharesight calculator | has | TAX-04 to TAX-06 |
| Tax | Independent check; return mapping | Second party by nature | Second party | Second party | Trackers | missing | §5.6 |
| Tax | Tax estimate before a sale; running provision | No | No | Betterment | — | partial (33 adds per-sell estimate) | §5.6 |
| Reporting | Balance, holdings, benchmark | Yes | Yes | Yes | Yes | has | MON-04 |
| Reporting | Money-weighted return, attribution, plain reasons | Some | Some | Some | pysystemtrade P&L | missing | 33 §2.8 |
| Reporting | Projection with a range | Some | No | Yes | Portfolio Visualizer | missing | §5.15, 33 MON-12 |
| Risk profile and goals | Questionnaire, horizon, yearly review | Yes | No | Yes | Policy statement | missing | §5.4 |
| Risk profile and goals | De-risk toward a date | No | No | Betterment | — | missing; record and notice only | §5.4 |
| Withdrawals | Planned withdrawal with sells | Yes | Manual | Yes | — | has | PRT-28 |
| Withdrawals | Overweight-first, tax-aware | Stockspot | No | Yes | — | partial | §5.10, 33 §2.6 |
| Monitoring | Kill switch, veto, dead-man, alerts | No client control | No | No | QC, pysystemtrade | has | §15 |
| Monitoring | Quiet default; override friction | n/a | n/a | Tax preview | — | partial | §5.7 |
| Security | Server and secrets | Vendor | Vendor | Vendor | Own | has | §19 |
| Security | Broker account, email, messaging account | Vendor 2FA | Vendor 2FA | Vendor 2FA | Own | missing | §5.11 |
| Security | Custody model disclosed | Yes | Yes | Yes | — | partial | §5.12, 33 §7 |
| Recovery | Backup, restore drill, rebuild from broker | Vendor | Vendor | Vendor | pysystemtrade | has | BP-16 |
| Recovery | Clean shutdown; maintenance watch | Vendor | Vendor | Vendor | — | missing | §5.9 |
| User experience | Phone dashboard, plain messages | Yes | Yes | Yes | Varies | has | MON-04 |
| User experience | No infrastructure to run | Yes | Yes | Yes | QC cloud | missing by design | §5.1, §5.9 |
| Education | Guides, expectations | Yes | Yes | Yes | Wiki | has (guide, §30) | §5.15 |
| Multi-account | Joint, trust, company, SMSF, kids | Yes | Most | Yes | — | missing; reject for now | §5.5 |
| Multi-account | Household view across accounts | Fee tier only | No | Betterment | Bogleheads; IBKR PortfolioAnalyst | missing | §5.5 |
| Multi-account | Super as a wrapper | Stockspot, Raiz | Pearler, Superhero | n/a | — | missing | 33 §2.1 |
| Estate | Estate process, survivorship via joint account | Yes | Yes | Yes | Letter of instruction | missing | §5.3 |
| Estate | Executor-readable tax records | Vendor holds them | Vendor | Vendor | — | missing | §5.3 |
| Other | Build-or-buy cost shown to the owner | n/a | n/a | n/a | — | missing | §5.1 |
| Other | Personal advice and a complaints route (AFCA) | Yes | No | Yes (US) | No | missing by design (§30 point 7) | — |
| Other | Suitability filter (ASIC RG 255) | Yes | No | Yes | No | missing | §5.4 |
| Other | Algorithm monitoring, testing and change control (RG 255) | Yes (required) | n/a | Yes | QC, pysystemtrade | has | Part B, §28 |

---

## 7. Consolidated list of proposed changes

| Where | Change | From |
| --- | --- | --- |
| PRT-22; RSK-30 (6); PRT-23; §30 point 1; O25 | Benchmark B3; static-mode cost criterion; notice; owner decision | §5.1 |
| MON-13; O7 | Contribution tracker, missed-contribution WARN, July escalation line; standing transfer | §5.2 |
| OPS-14; §4; "Before G4" | Estate pack, trusted-contact email on owner silence, designed no-approval-no-order statement | §5.3 |
| USR-15 | Investment policy record with three checks and a yearly re-entry | §5.4 |
| MON-14; TAX-03 | Household view (information only); entity field kept open | §5.5 |
| TAX-16; TAX-17; T16 | Three-way tax check and generic export; tax provision and PAYG warning | §5.6 |
| MON-15 | Quiet digest by default; veto needs a reason and shows history | §5.7 |
| Card HP1 | Tax-aware band rebalance | §5.8 |
| OPS-15; RSK-30 report | `trader retire`; months-since-update line | §5.9 |
| PRT-28 | Overweight-first withdrawal sells | §5.10 |
| "Before G4" | Six broker-account hardening lines | §5.11 |
| §30 point 7 | Custody sentence (extends report 33) | §5.12 |
| MON-12 (report 33) | Percentile band on the projection | §5.15 |
| SYS-30 | Yearly instrument review with two WARNs | §5.16(a) |
| PRT-22 | Reference series: AUST beside the VAS sleeve; after-tax B1 against B2 in the G2 report | §5.16(b) |
| Rejected | Fractional units; round-ups; automated loss harvesting; direct indexing; multi-entity engine; child instances; a managed-risk or one-fund ETF as a live holding; a bank-balance sweep | §3, §5.5, §5.13, §5.14, §5.16 |

New IDs used here (OPS-14, OPS-15, USR-15, MON-13 to MON-15, TAX-16, TAX-17, O25, T16, B3, HP1) do not clash with v2.10 or with report 33's MON-09 to MON-12, O23, O24, T14, T15. Reports 31 and 32 both use H14 and H15; renumber all cards at registration.

**Interaction with report 33.** Report 33 §2.2 recommends STATIC live for a growth objective. Section 5.1 here shows that STATIC on this system is the same holding as a zero-brokerage account at A$156–288 a year more, depending on the account compared. Taken together the owner's real choice before G4 is three-way: L1 here (pays for the overlay); static here (pays to learn and for own records); or static elsewhere with this system in paper. O25 records it.

---

## 8. What is deliberately not recommended

- **Copying a robo-adviser's allocation.** The robo mixes include bonds and gold. Whether to add them is Stage 2 (33 §2.5) and a risk choice, not a platform feature to match.
- **A second broker for redundancy.** D12 stands; no other Australian retail API was found in this review either.
- **A cloud algo platform (QuantConnect) in place of the custom engine.** D2 stands: it would move secrets and the trade path to a third party for two instruments and a monthly decision.
- **Any feature that suggests a trade.** Platform "insights" and themes are marketing. SYS-06 and report 33's rule against opportunity alerts stand.

---

## 9. What could be wrong, and what to re-check

1. **Platform fees still read only as extracts:** Stockspot above A$200,000, Six Park, Raiz (two conflicting schedules), Spaceship, InvestSMART, Webull, and Pearler's prepaid rate. Vanguard, Betashares Direct and IBKR Australia were read directly in the v2 pass. Stake, CMC, Superhero, Pearler and Selfwealth brokerage are confirmed only by Betashares' own comparison table (19 March 2026), which is a competitor's summary.
2. **Vanguard Auto Invest** is confirmed for Vanguard ETFs at A$0 to buy in whole units [primary]; whether it can direct money to the underweight fund is unknown. **Webull's** A$0 ETF brokerage is from extracts of its own site and affiliate-style reviews; its host is blocked.
3. **In-kind transfer** out of IBKR Australia: the outbound fee and the tax treatment were not confirmed.
4. **IBKR Australia specifics still open:** the deceased-estate process for an Australian account (IBKR's FAQ page did not render; its text is an extract) and IP restrictions for a gateway login. Power-of-attorney users and the exclusion of ASX from fractional and recurring orders are now confirmed [primary].
5. **Stockspot and tax-loss harvesting:** one Morningstar AU extract says the algorithm does it; Stockspot's own pages in the extracts speak only of minimising gains. Unresolved.
6. **The Raiz October 2026 tax issue** comes from a competitor's blog. Confirm from Raiz's own notice before quoting it.
7. **PAYG instalment thresholds and the minors' rates** were read as extracts of ATO and adviser pages; the tax agent confirms (T16).
8. **CSLR scope** for a broker failure is unconfirmed.
9. **The A$ figures** in §5.1 and §5.2 are arithmetic on the spec's cost table and a 5% return assumption; they are not forecasts. The 0.1–0.2% in §5.8 is an estimate that card HP1 exists to measure.
10. **Behavioural evidence** is from US fund investors and professional traders. It supports the direction of §5.4 and §5.7, not a number for this owner.
11. **pysystemtrade's production document** was read directly in the v2 pass. Alpha Architect and the Bogleheads wiki were read as extracts of their own pages.
12. **The Betashares article on CGT and single diversified ETFs** was read in full in the v2 pass and §5.16(b) rewritten. Its examples are the issuer's hypotheticals; the parcel-by-parcel reading goes to the tax agent (T13).
13. **Stockspot's fee table** now rests on three of its own pages that agree; its drift threshold is still unpublished in anything I could read.

---

## 10. Sources

All read as search-engine extracts this session (direct fetch blocked). Grouped by topic.

**Australian platforms**

- Stockspot: [FAQ](https://www.stockspot.com.au/how-it-works/general-faqs/); [portfolios](https://www.stockspot.com.au/how-it-works/portfolios/); [MDA](https://www.stockspot.com.au/legal/mda/); [rebalancing and CGT help article](https://intercom.help/stockspot-7bbb0a48f2c0/en/articles/5160747-portfolio-rebalancing-capital-gains-tax-cgt); [fees help article](https://intercom.help/stockspot-7bbb0a48f2c0/en/articles/5160575-what-are-the-fees); [fee cut blog](https://blog.stockspot.com.au/stockspots-biggest-update-low-cost-investing/); [reinvesting dividends](https://blog.stockspot.com.au/guide-to-reinvesting-dividends/); [gold trim, October 2025](https://blog.stockspot.com.au/investment-update-gold-october2025/); [HIN or custody](https://blog.stockspot.com.au/investing-with-hin-or-custody/); [risk profile](https://blog.stockspot.com.au/what-is-your-risk-profile/); [joint accounts](https://stockspot.com.au/investing-joint); [kids FAQs](https://blog.stockspot.com.au/investing-for-kids-top-faqs/); [Raiz tax announcement](https://blog.stockspot.com.au/raiz-tax-announcement/). Morningstar AU on robo-advisers: [article](https://www.morningstar.com.au/personal-finance/young-invested-are-robo-advisers-worth-it).
- Six Park: [Finder interview](https://www.finder.com.au/six-park-interview); [Canstar](https://www.canstar.com.au/wealthbricks-news/six-park-allows-investors-create-globally-diversified-managed-portfolio/); [IFA, 2016 launch](https://www.ifa.com.au/new-robo-adviser-targets-neglected-investors); [Finder robo comparison 2026](https://www.finder.com.au/robo-advice).
- Raiz: [rebalancing blog](https://raizinvest.com.au/blog/the-portfolio-rebalancing-act/); [Finder on fees](https://www.finder.com.au/news/raiz-hiking-fees-is-it-worth-it).
- Spaceship: [fees help article](https://help.spaceship.com.au/en/articles/5694014-what-are-the-fees-for-spaceship-voyager); [fee change notice](https://www.spaceship.com.au/important-documents/fee-changes-290424/); [Investor Daily](https://investordaily.com.au/news/49996-spaceship-raises-account-fees-for-the-first-time).
- InvestSMART: [capped fees](https://investsmart.com.au/capped-fees); [fees help](https://www.investsmart.com.au/help-centre/what-are-the-fees/20); [Investor Daily](https://www.investordaily.com.au/investsmart-introduces-capped-fees).
- Pearler: [autoinvest help](https://pearler.com/help/4771917); [FSG](https://pearler.com/financial-services-guide); [review](https://quantroutine.com/brokers/pearler/).
- Betashares Direct: [pricing](https://www.betashares.com.au/direct/pricing); [FAQ](https://betashares.com.au/direct/faq); [custom portfolios](https://www.betashares.com.au/direct/custom-portfolios); [custom portfolio updates](https://www.betashares.com.au/direct/news/custom-portfolio-updates); [kids account](https://www.betashares.com.au/direct/account-types/kids-account); [CHESS or custodian](https://www.betashares.com.au/education/chess-sponsored-vs-custodial-holding/); [review](https://quantroutine.com/brokers/betashares-direct/).
- Vanguard Personal Investor: [fees and costs](https://www.vanguard.com.au/personal/invest-with-us/fees-and-costs); [Finder](https://www.finder.com.au/share-trading/vanguard-share-trading); [review](https://quantroutine.com/brokers/vanguard-aus/); [Morningstar AU on the fee change](https://www.morningstar.com.au/markets/investors-divided-on-vanguard-platform-fee-change).
- Superhero: [invest](https://www.superhero.com.au/invest/); [pricing](https://www.superhero.com.au/invest/pricing/); [review](https://peakifi.com/investing/platforms/superhero-review/). Stake: [recurring investments](https://hellostake.com/au/invest/recurring-investments); [CHESS](https://hellostake.com/au/invest/aus/chess); [Finder](https://www.finder.com.au/share-trading/stake). CommSec Pocket: [CommBank](https://www.commbank.com.au/investing/commsec-pocket.html); [rates and fees](https://static.commsec.com.au/support/rates-and-fees.html).
- Read directly in the v2 pass [primary]: Betashares Direct [pricing](https://www.betashares.com.au/direct/pricing), [auto-invest](https://www.betashares.com.au/direct/auto-invest), [custom portfolios](https://www.betashares.com.au/direct/custom-portfolios), [FAQ](https://www.betashares.com.au/direct/faq), [comparison, as at 19 March 2026](https://www.betashares.com.au/direct/comparison); Betashares ["Less is more"](https://www.betashares.com.au/advisers/insights/cgt-rules-diversified-etfs/) and [AUST](https://www.betashares.com.au/fund/managed-risk-australian-share-fund/); Vanguard [fees and costs](https://www.vanguard.com.au/personal/invest-with-us/fees-and-costs), [Auto Invest](https://www.vanguard.com.au/personal/invest-with-us/auto-invest), [ETF page](https://www.vanguard.com.au/personal/invest-with-us/etf?portId=8205); IBKR Australia [commissions](https://www.interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php), [interest rates](https://www.interactivebrokers.com.au/en/accounts/fees/pricing-interest-rates.php), [recurring investments](https://www.interactivebrokers.com.au/en/trading/recurring-investments.php), [fractional trading](https://www.interactivebrokers.com.au/en/trading/fractional-trading.php), [client protection](https://www.interactivebrokers.com.au/en/general/security-investor-protection.php), [funding](https://www.interactivebrokers.com.au/en/support/fund-my-account.php), [individual accounts](https://www.interactivebrokers.com.au/en/accounts/individual.php), [PortfolioAnalyst](https://www.interactivebrokers.com.au/en/portfolioanalyst/features.php); [Morningstar AU on robo-advisers](https://www.morningstar.com.au/personal-finance/young-invested-are-robo-advisers-worth-it); [pysystemtrade production.md](https://raw.githubusercontent.com/pst-group/pysystemtrade/master/docs/production.md).
- Added in the deeper pass. Stockspot: [pricing](https://www.stockspot.com.au/how-it-works/pricing/); [pricing help article](https://intercom.help/stockspot-7bbb0a48f2c0/en/articles/4786177-pricing-fees); [index funds page](https://www.stockspot.com.au/invest-in-index-funds/); [chosen ETFs](https://www.stockspot.com.au/how-it-works/our-chosen-etfs/); [ETF criteria interview](https://etfstream.com/articles/interview-chris-brycki-what-makes-a-good-etf); [super Q&A](https://blog.stockspot.com.au/stockspot-super-your-questions-answered/). Vanguard: [Personal Investor guide, part A](https://fund-docs.vanguard.com/AU-Vanguard_Personal_Investor_Guide_Part_A.pdf); [comparison review](https://quantroutine.com/brokers/vanguard-aus-vs-betashares-direct/). Betashares Direct: [app listing](https://apps.apple.com/au/app/betashares-direct-investing/id1669109591). Webull Australia: [Finder](https://www.finder.com.au/share-trading/webull-trading); [review](https://quantroutine.com/brokers/webull-aus/); [fee cut report](https://futurefive.com.au/story/webull-australia-cuts-fees-to-zero-across-key-markets). CMC Invest and others: [Mozo](https://mozo.com.au/best/best-share-trading-platforms.html); [Finder, CHESS brokers](https://www.finder.com.au/best-chess-sponsored-brokers). Nucleus Wealth: [fees](https://nucleuswealth.com/fees); [IBKR launch note](https://nucleuswealth.com/blog/new-product-lower-fees-nucleus-wealth). AUST: [issuer page](https://betashares.com.au/fund/managed-risk-australian-share-fund); [factsheet](https://www.betashares.com.au/files/factsheets/AUST-Factsheet.pdf). Diversified ETFs and CGT: [Betashares, "Less is more"](https://www.betashares.com.au/advisers/insights/cgt-rules-diversified-etfs/); [Morningstar AU on VDHG](https://www.morningstar.com.au/insights/funds/216840/vanguard-controversy-does-vdhg-lead-to-higher-taxes).
- Custody models: [Mozo](https://www.mozo.com.au/share-trading/guides/custodial-vs-chess-how-do-these-share-trading-models-differ); [Sharesight](https://www.sharesight.com/blog/what-are-custodial-vs-non-custodial-investments).

**Global platforms**

- Betterment: [rebalancing methods](https://betterment.com/help/portfolio-rebalancing-methods); [rebalancing and auto-adjust disclosure](https://www.betterment.com/legal/auto-adjust-disclosure); [auto-adjust help](https://betterment.com/help/how-automatic-allocations-work); [allocation methodology](https://www.betterment.com/resources/goals-advice-explained); [TLH methodology](https://www.betterment.com/resources/tax-loss-harvesting-methodology); [TLH+ white paper](https://www.betterment.com/resources/research/tax-loss-harvesting-white-paper); [Tax Coordination disclosure](https://www.betterment.com/legal/tax-coordination). Critique: [Advisor Perspectives, "The Tax Harvesting Oasis"](https://www.advisorperspectives.com/newsletters14/The_Tax_Harvesting_Oasis.php).
- Wealthfront: [TLH white paper](https://research.wealthfront.com/?p=7); [harvesting yield](https://support.wealthfront.com/hc/en-us/articles/115005589003-What-is-Harvesting-Yield); [TLH results 2025](https://www.wealthfront.com/blog/tlh-results-2025); [rebalancing and harvesting](https://support.wealthfront.com/hc/en-us/articles/209348586-How-does-tax-loss-harvesting-relate-to-rebalancing); [how often](https://support.wealthfront.com/hc/en-us/articles/209353766-How-often-do-you-rebalance-my-portfolio-); [risk score](https://www.wealthfront.com/blog/ask-wealthfront-risk-score-explainer); [direct indexing minimums](https://support.wealthfront.com/hc/en-us/articles/49518180999188-Wealthfront-Direct-Indexing-Accounts-Fees-Minimums).
- Schwab Intelligent Portfolios: [portfolio management FAQ](https://hg.schwab.com/page/faq/portfolio-management); [TLH disclosures](https://www.schwab.com/legal/institutional-intelligent-portfolios-tax-loss-harvesting-disclosures); [NerdWallet review](https://www.nerdwallet.com/investing/reviews/schwab-intelligent-portfolios); [Marotta critique](https://marottaonmoney.com/schwab-intelligent-portfolios-incomplete-rebalancing-algorithm/).
- Wealthfront Autopilot: [launch post](https://www.wealthfront.com/blog/meet-autopilot-a-new-service-that-automates-your-savings-strategy/); [Banking Dive](https://www.bankingdive.com/news/wealthfront-automatic-savings-investment/584683/). Passiv and IBKR tools: [IBKR partner page](https://interactivebrokers.co.uk/en/trading/providers/passiv.php); [Rebalance Portfolio window](https://www.interactivebrokers.eu/campus/trading-lessons/tws-rebalance-portfolio-window/); [PortfolioAnalyst features](https://www.interactivebrokers.com.au/en/portfolioanalyst/features.php). Other robos: [Singapore comparison](https://dollarbureau.com/blog/syfe-vs-stashaway-vs-endowus/); [Canada comparison](https://www.finder.com/ca/robo-advice). ASIC RG 255: [ASIC](https://asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-255-providing-digital-financial-product-advice-to-retail-clients/); [commentary](https://www.moneyandlife.com.au/professionals/focus/asic-guidance-on-digital-advice/).
- M1: [how M1 trades](https://help.m1.com/en/articles/9331916-how-m1-trades). Composer: [threshold trading](https://composer.trade/learn/threshold-trading). QuantConnect: [notifications](https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/notifications); [live trading](https://www.quantconnect.com/docs/v2/cloud-platform/live-trading.md). Alpaca: [portfolio rebalancing](https://docs.alpaca.markets/docs/portfolio-rebalancing); [fractional trading](https://docs.alpaca.markets/docs/trading/fractional-trading/). Portfolio Visualizer: [AAII](https://www.aaii.com/journal/article/536490-using-portfolio-visualizer-to-test-allocation-strategies); [My Money Blog](https://www.mymoneyblog.com/portfolio-visualizer-tool.html).

**DIY practice and research**

- pysystemtrade: [production.md](https://github.com/robcarver17/pysystemtrade/blob/master/docs/production.md); [repository](https://github.com/robcarver17/pysystemtrade). Carver on buffering: [CXO Advisory notes](https://www.cxoadvisory.com/big-ideas/a-few-notes-on-systematic-trading); [QuantConnect replication](https://www.quantconnect.com/research/15875/futures-fast-trend-following-with-trend-strength/).
- Newfound: [timing luck library](https://blog.thinknewfound.com/tag/rebalance-timing-luck/); [Advisor Perspectives](https://www.advisorperspectives.com/commentaries/2019/05/02/what-back-to-the-future-can-teach-us-about-portfolio-rebalancing).
- Vanguard: [The Rebalancing Edge](https://corporate.vanguard.com/content/dam/corp/research/pdf/the_rebalancing_edge_optimizing_target_date_fund_rebalancing_through_threshold_based_strategies.pdf); [research summary](https://corporate.vanguard.com/content/corporatesite/us/en/corp/articles/balancing-act-enhancing-target-date-fund-efficiency.html); [Rational rebalancing](https://corporate.vanguard.com/content/dam/corp/research/pdf/rational_rebalancing_analytical_approach_to_multiasset_portfolio_rebalancing.pdf); [Adviser's Alpha copy](https://www.firstlinks.com.au/uploads/wp/Vanguard_Advisers_Alpha.pdf).
- Daryanani, opportunistic rebalancing: [FA Magazine](https://www.fa-mag.com/news/optimal-rebalancing-with-tolerance-bands-29623.html?page=2); [Kitces handout](https://kitces.com/wp-content/uploads/2016/11/An-In-Depth-Look-At-Optimal-Rebalancing-Strategies-Webinar-Handouts.pdf). 5/25 rule: [White Coat Investor](https://www.whitecoatinvestor.com/rebalancing-the-525-rule/); [A Wealth of Common Sense](https://awealthofcommonsense.com/larry-swedroe-525-rebalancing-rule/).
- Alpha Architect: [Robust Asset Allocation index](https://alphaarchitect.com/the-robust-asset-allocation-raa-index/). Bogleheads wiki: [Investment policy statement](https://www.bogleheads.org/wiki/Investment_policy_statement); [Asset allocation in multiple accounts](https://www.bogleheads.org/wiki/Asset_allocation_in_multiple_accounts). Rolling returns: [Firstlinks](https://www.firstlinks.com.au/article/four-best-ever-charts-for-every-adviser-and-investor); [Livewire](https://livewiremarkets.com/wires/how-146-years-of-market-data-can-save-you-money-and-help-you-sleep).
- Bogleheads practice: [investor policy statement](https://www.whitecoatinvestor.com/you-need-an-investor-policy-statement/); [documenting finances for a surviving spouse or executor](https://boglecenter.net/bogleheads-chapter-series-documenting-financial-information-for-surviving-spouse-executor/).
- Behaviour: [Morningstar, Mind the Gap 2026 (PDF)](https://www.morningstar.com/content/cs-assets/v3/assets/blt9415ea4cc4157833/blt852a4301adc2f5db/6a7373d51f7b5ae2da78e1e8/US_Mind_the_Gap_2026.pdf); [WealthManagement summary](https://www.wealthmanagement.com/investing-strategies/investors-miss-out-on-12-of-fund-returns-over-decade); [Larson, List and Metcalfe, NBER 22605](https://www.nber.org/papers/w22605); [Thaler and Benartzi, Save More Tomorrow](https://www.chicagobooth.edu/research/rustandy/social-impact-research/research-papers/2004/save-more-tomorrow-using-behavioral-economics-to-increase-employee-saving); [US Labor Department evidence review](https://clear.dol.gov/study/save-more-tomorrow%E2%84%A2-using-behavioral-economics-increase-employee-saving-thaler-benartzi-2004).

**Australian tax, estate and protection**

- Wash sales: [ATO media release](https://www.ato.gov.au/media-centre/wash-sales-the-ato-is-cleaning-up-dirty-laundry); [Corrs](https://corrs.com.au/insights/when-is-a-capital-loss-susceptible-to-part-iva); [InvestSMART](https://www.investsmart.com.au/investment-news/why-the-atos-interested-in-wash-sales-all-year-round/151454); [Accountants Daily](https://www.accountantsdaily.com.au/tax-compliance/17223-if-you-asset-wash-you-ll-wear-it-warns-ato).
- Deceased estates: [ATO CGT guide 2026](https://www.ato.gov.au/forms-and-instructions/capital-gains-tax-guide-2026/about-capital-gains-tax/deceased-estates); [CommSec estates](https://www.commsec.com.au/support/help-centre/Estate-Management/How-to-manage-deceased-estates.html); [Macquarie](https://www.macquarie.com.au/help/brokers/managing-existing-clients/view-loan-and-client-information/deceased-estates.html); [Bell Direct](https://support.belldirect.com.au/hc/en-au/articles/59522946752921--How-do-I-transfer-shares-to-an-estate-account-and-sell-them-after-a-client-s-passing); IBKR after a death (secondary): [Swift Probate](https://www.swiftprobate.com/institutions/interactive-brokers); [forum](https://forum.mustachianpost.com/t/interactive-brokers-in-case-of-death/9441).
- IBKR on death: [FAQ](https://www.interactivebrokers.com/lib/cstools/faq/content/40349925). Powers of attorney: [NSW Government](https://www.nsw.gov.au/family-and-relationships/planning-for-end-of-life/make-power-of-attorney); [SA Law Handbook](https://www.lawhandbook.sa.gov.au/print/ch02s01.php). ATO share data matching: [programme overview](https://www.ato.gov.au/about-ato/commitments-and-reporting/in-detail/privacy-and-information-gathering/how-we-use-data-matching/share-transactions-data-matching-program-protocol/share-transactions-data-matching-program-overview). IBKR funding and third-party deposits: [fund your account](https://www.interactivebrokers.com.au/en/support/fund-my-account.php). SMSF costs: [SuperGuide](https://superguide.com.au/smsfs/smsf-setup-and-running-costs); [Morningstar AU](https://www.morningstar.com.au/personal-finance/how-do-low-cost-smsfs-compare). CSLR scope: [Money Management](https://www.moneymanagement.com.au/news/financial-planning/cslr-identifies-recurring-financial-advice-complaints).
- PAYG instalments: [ATO investor toolkit](https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/prepare-and-lodge/tax-time/tax-time-toolkits/tax-time-toolkit-for-investors/pay-as-you-go-payg-instalments); [ATO, stopping instalments](https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/payg-instalments/stopping-payg-instalments).
- Pre-fill: [ATO, recurring data issues](https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/prepare-and-lodge/pre-filling-service/recurring-data-issues); [ATO myTax, managed funds](https://ato.gov.au/individuals-and-families/your-tax-return/instructions-to-complete-your-tax-return/mytax-instructions/2024/income/managed-fund-or-trust-distributions/managed-funds).
- Minors: [AMP](https://amp.com.au/insights-hub/blog/investing/investing-on-behalf-of-kids); [BT facts and figures, July 2025](https://www.bt.com.au/content/dam/public/btfg-bt/documents/professional/knowledge-centre/client-strategies/facts-and-figures-jul-2025.pdf).
- Sharesight: [plans](https://help.sharesight.com/au/plans-overview); [IBKR help centre](https://help.sharesight.com/interactive-brokers-help-centre/); [CGT reform calculator](https://www.sharesight.com/australian-cgt-reform-calculator/).
- IBKR: [Australian account guide](https://www.interactivebrokers.com.au/en/accounts/account-guide.php); [individual accounts](https://www.interactivebrokers.com.au/en/accounts/individual.php); [SMSF account](https://www.interactivebrokers.com.au/en/accounts/self-managed-superannuation-fund.php); [client protection](https://www.interactivebrokers.com.au/en/general/security-investor-protection.php); [depositing AUD](https://ibkb.interactivebrokers.com/de/node/4840); [recurring investments](https://interactivebrokers.com.au/en/trading/recurring-investments.php); [fractional trading](https://interactivebrokers.com.au/en/trading/fractional-trading.php); [IP restrictions](https://www.interactivebrokers.com/docs/web-api/authentication/additional-security-features); [Secure Login System](https://interactivebrokers.ie/en/general/secure-login.php).
- CSLR: [ASIC FAQs](https://asic.gov.au/about-asic/dealing-with-asic/compensation-scheme-of-last-resort/faqs-cslr); [FAAA](https://faaa.au/compensation-scheme-of-last-resort).

**Internal**

- FD_FINAL.md v2.10 (§1, §2, §4, §9.1, §10, §13, §14, §15, §19, §21, §24, §27, §30); reports 31, 32 and 33 in this folder.
