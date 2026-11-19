# 44. Owner decisions, made under delegation

Report 44, Friday 13 November 2026. This is general information, not personal financial advice.

**Authority.** The owner decided three things: (1) the objective is **growth**; (2) the A$5,000 goes into an index account **now** while the system proves itself; (3) every remaining decision is delegated ("make all those decisions for the best"). This report makes those decisions and records them. It does not edit the spec.

**What I read.** `FD_FINAL.md` (v2.10) §17, §20, §21, §24, §30; reports 31, 32, 33, 34, 37, 40, 41 and 42; report 35 at summary level. Reports 36, 38 and 39 did not exist when this was written (checked 21:40 UTC). Report 43 landed at the end and was read at summary level (decision C14). Decisions that should be re-opened when they land are marked in the "Revisit when" column.

**What I checked today, directly, with `curl`.** Betashares Direct (pricing, auto-invest, FAQ, comparison, account types), the Betashares fund pages for DHHF, A200 and BGBL, the Betashares CGT article, Vanguard Personal Investor (fees and costs, Auto Invest), and IBKR Australia (recurring investments, free trial). The sites of Pearler, Stake, CMC, Superhero and Webull refused the connection, so their rows rest on Betashares' own comparison table (dated 19 March 2026) and report 34's extracts.

**Tags.** [primary] = I read the provider's own page today. [R37 primary] = report 37 read the primary page today. [2+] = two or more sources, not the provider's page. [1] = one source. [unverified] = nobody confirmed it. [computed] = my arithmetic.

**Owner facts I do not have:** income and marginal tax rate, age, debts, super balance, how much can be saved each month. I have not guessed them. Where a decision depends on one, there is a default and a rule you can apply yourself (section 1.4).

---

## 0. Plain-English summary for the owner

**The one-paragraph version.** Your A$5,000 goes into two very cheap index funds this week, with A$500 a month added automatically, at a broker that charges nothing. That is the money plan, and the evidence says it is the best growth plan available to you. The trading system carries no real money. It gets built in a small form, watches the same two funds, keeps your records, and runs its trend rule on paper so you can see what it would have done. It only ever gets real money if it runs cleanly for a year, the balance is large enough for its costs not to matter, and you decide in writing that you want what it actually offers, which is a smaller worst-case loss and not a higher return.

**The decisions, in plain words.**

1. **Where the money goes.** Open a **Betashares Direct** account in your own name. Buy **A$2,000 of A200** (Australian shares) and **A$3,000 of BGBL** (global shares). Brokerage is A$0 to buy and A$0 to sell. Combined fund fee is about 0.06% a year: about A$3 a year on A$5,000.
2. **Monthly.** Set a standing bank transfer of **A$500 a month** (default; use what you can sustain) and an Auto-invest of **A$200 into A200 and A$300 into BGBL**. Raise it 3% every July. Turn distribution reinvestment on. Then leave it alone.
3. **Never sell to tidy up.** Once a year, if the two funds have drifted far from 40/60, point new money at the smaller one. No selling.
4. **The trend rule (L1) does not run on real money.** Under a growth objective it is expected to cost return: in report 42's simulation it ends behind doing nothing in about three five-year periods out of four. It runs on paper only.
5. **The system is cut down and frozen.** One last amendment to the spec (v2.11), then no more spec versions and no more full reviews. About 155 of 254 requirements are in the build; 87 of those make the first release. Other users, the public website, bonds and gold, US shares and the forecast engine are out.
6. **The first release only advises.** It fetches prices, checks them, records your holdings, shows the benchmarks and tells you if a contribution was missed. It places no orders. Automatic ordering is built later, on IBKR's paper account only, and only if the first release has run cleanly.
7. **One week of reality tests first** (16–20 November): does the free data key work for ASX funds, and does IBKR's paper account behave as the design assumes.
8. **The search for a better algorithm stops.** Reports 36–39 are the last. Five test cards stay active; everything else is parked for 12 months.
9. **Costs.** Target A$0–31 a year while the system is on paper. Nothing is bought (no mini PC, no Norgate data rental, no A$306 data plan) unless a test shows it is needed.
10. **When real money could move to the system.** Not before **Monday 13 December 2027**, and only if every condition in section 4.1 holds, including a managed balance of at least A$50,000. At A$500 a month that is around **2032** [computed].

**Three checks only you can make, because I do not know your position** (section 1.4):

- **Home loan with an offset account at 6% or more?** Then the offset is the better home for the A$5,000 on the numbers. With the cash rate at 4.85% [R37 primary], most variable home loans are probably above that line [unverified]. You have decided to invest; this is the one thing I would ask you to look at before you transfer.
- **Any card or personal-loan debt above about 7%?** Pay that first.
- **Marginal tax rate 30% or more** (taxable income above A$45,000 [R37 primary]) **and money you will not need before age 60?** Extra super contributions start about 25% ahead of the same money invested outside super [R33, computed]. Ask your tax agent before the monthly amount is locked in.

**What to expect.** Long-run share returns of about 5–8% a year are the planning figure in the spec; single years can be anywhere from about −15% to +20% [spec §30], and a fall of 40–50% at some point is normal for a share index [R41]. At A$500 a month and 7% a year the account is about A$43,000 in five years and A$96,000 in ten [computed; a model, not a forecast]. No algorithm in the programme's research is expected to beat this.

Your to-do list with dates is in section 5.

---

## 1. Decision A: where the A$5,000 goes now

### 1.1 Platform comparison

| Platform | Buy fee | Sell fee | Auto-invest | Minimum | Holding model | Cash interest | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Betashares Direct** | A$0 on all ASX ETFs and 550+ shares | A$0 | Free, into up to five Betashares ETFs; fractional units, so every dollar is invested | A$10 | Custodial (an "IDPS-like scheme"; assets with an independent licensed custodian; you keep beneficial ownership) | Betashares keeps it | [primary] pricing, auto-invest, FAQ, comparison pages |
| **Vanguard Personal Investor** | A$0 on Vanguard ETFs | A$9 flat | A$200 per cycle, fortnightly, monthly or quarterly; at least one whole unit per ETF | A$200 a cycle | Custodial [2+] | Vanguard retains interest on the Cash Account | [primary] fees and Auto Invest pages |
| **IBKR Australia** | 0.08%, minimum A$6.00 plus GST (A$6.60) | Same | Not for ASX: recurring investments cover "US, Canadian and European shares" only | None stated | Custodial (sub-custodian BNP Paribas) [R34 primary] | 0% on the first A$15,000 | [primary] recurring page; [R37 primary] commission and interest |
| Pearler | A$6.50 | A$6.50 | Yes; minimum A$650 per holding per run | A$500 | CHESS | Not found | [2+] Betashares table of 19 Mar 2026; own site blocked today |
| Stake | A$3 up to A$30,000, then 0.01% | Same | Sources conflict | A$500 | CHESS | Not found | [2+], as above |
| CMC Invest | A$0 on the first ASX buy up to A$1,000 a day, then A$11 or 0.10% | A$11 or 0.10% | Not found | A$500 | CHESS | Not found | [2+], as above |
| Superhero | A$2 up to A$20,000, then 0.01% | Same | Yes [1] | A$10 | Custodial | Not found | [2+], as above |
| Webull Australia | A$0 on Australian ETFs | Not confirmed | Yes [1] | Not found | CHESS [1] | Not found | [2+] report 34 extracts; not checked today; one review notes poor customer ratings |

Note on the four rows from Betashares' table: it is a competitor's comparison, eight months old. Treat those figures as indicative.

### 1.2 Decision: Betashares Direct

Reasons, in order of weight:

1. **It is the only platform confirmed today that is free in both directions and fully automatic with no cash left over.** Fractional units mean A$500 buys A$500 of funds. At Vanguard, whole units leave some cash idle each month and each sale costs A$9.
2. **Automatic matters more than any fee.** Missing two of twelve A$500 contributions a year costs about A$12,900 over ten years [R34, computed]. A manual platform (CMC's free first buy) is cheap but depends on you acting every month.
3. **It carries the two cheapest broad funds** (section 1.3), and its free Auto-invest covers exactly those.
4. **Leaving is cheap.** Transfer out costs up to A$9.50 per security [primary]: at most A$19 for two funds.

What you give up, stated plainly:

- **No HIN.** Your units are held by a custodian for you, not registered in your name on CHESS. IBKR, where the system would trade, is custodial too, so this is not a step down from the original plan. If you ever want CHESS registration, the fallback is CMC Invest (manual monthly buys) or Webull (not verified).
- **Interest on idle cash goes to Betashares.** With fractional auto-invest there should be almost no idle cash. Do not park money in the wallet.
- **Issuer and platform are the same company.** The funds themselves are trusts with their own custodian; the platform holding is custodial. This is a concentration of counterparty, not of investment risk.

### 1.3 Funds: A200 40%, BGBL 60%

| Option | Fee a year | What it is | For | Against |
| --- | --- | --- | --- | --- |
| **A200 + BGBL at 40/60 (chosen)** | 0.04% and 0.08%: **0.064% blended** [primary; computed] | Australia's 200 largest companies; developed-world shares outside Australia. A$11.7bn and A$6.0bn in the funds [primary] | Cheapest. Same exposure as the spec's VAS/VGS. Matches benchmark B2, so the system's records line up with what you really hold | Two lines to look at. BGBL only dates from 9 May 2023 [primary]. No emerging markets or small companies |
| DHHF, one fund | 0.19% [primary] | About 8,000 shares worldwide: Australia 37.9%, US 40.4%, other developed 15.0%, emerging 6.6% at 30 Oct 2026 [primary]. Rebalances itself | One line. Wider spread. A single asset for the 2027 tax rules (below) | Three times the fee. Holds some US-domiciled funds, which can leak a little foreign withholding tax [1, R33] |
| VAS + VGS at 40/60 (Vanguard platform) | 0.07% and 0.18%: 0.136% blended [R37 primary] | The spec's original pair | Largest funds, longest history | Dearer than A200/BGBL; whole units; A$9 to sell |
| VDHG | 0.27% [R33, ASX report] | 90% shares, 10% bonds | One line | Not all-growth; dearest |

**Fees in dollars** [computed: A$5,000 start, A$500 a month, 7% a year before fees]:

| After | A200 + BGBL ends ahead of DHHF by | Ahead of VAS + VGS by |
| --- | --- | --- |
| 5 years | A$160 | A$90 |
| 10 years | A$720 | A$410 |
| 20 years | A$4,400 | A$2,500 |
| 30 years | A$16,200 | A$9,300 |

**The 2027 tax point (report 34 §5.16(b)), checked against the Betashares article [primary].** From 1 July 2027 the 50% CGT discount is replaced by indexation, applied asset by asset. If one asset grows more slowly than inflation, its unused indexation is wasted, and a loss gets none. Betashares' example uses a share fund and a bond fund: held separately the taxable gain is A$2,500; held as one diversified fund it is A$1,000. That favours one fund over two **when one of the two is a slow grower such as bonds or cash**. Both of your funds are share funds, and over a long holding period both are expected to finish well above their inflation-indexed cost. The effect is real but small for an all-share pair, and it only bites when you sell. I judge it smaller than the certain fee saving. It would become a strong argument for a single fund if you ever added bonds.

**Why 40/60.** It is the spec's split [D3] and almost the same as DHHF's. Australian shares carry franking credits (A200: franking level 43.2%, cash yield 3.4%, 4.0% grossed up [primary]). I found no evidence that justifies a different split, and report 33 §3.1 reached the same view.

**Why not DHHF, since report 41 named it first.** Either is a good answer; the gap is a few hundred dollars over ten years. I chose the pair for three reasons: lower cost; the system's records, benchmark B2 and paper trading then describe exactly what you own; and the units can later move to the system's broker without being sold. **If you know you will tinker with two lines, buy DHHF alone instead.** One fund you leave alone beats two you fiddle with, and the fee difference is far smaller than the cost of one badly timed sale.

### 1.4 Rules for the facts I do not have

Apply these before transferring. They can change where the money goes; they do not change anything else in this report.

| Your situation | Rule | Why |
| --- | --- | --- |
| Less than about three months of living costs in at-call cash | Build that first; invest the rest | So a bill never forces a sale in a fall |
| Credit-card, car or personal-loan debt above about 7% | Pay it before investing | A certain saving larger than the planning return on shares |
| Home loan with an offset or free redraw at **6% or more** | The A$5,000 does better in the offset: about A$300 a year, tax-free and without risk [R33, computed]. Decide the monthly A$500 the same way | A 6% saving equals an 8.8% pre-tax return at a 32% rate [R33, computed] |
| Home loan under about 5%, or no home loan | Invest as planned | |
| HELP debt only | Invest as planned | Indexed at about 2.8% in June 2026 [1, R33], below the planning return |
| Marginal rate **30% or more** and money not needed before age 60 | Ask your tax agent about salary sacrifice or a personal deductible contribution for part of the monthly amount. General cap A$32,500 for 2026–27 including employer contributions [2+; figure not confirmed on a primary page, R37]. Above A$250,000 income the advantage is smaller [R37 primary] | Contributions are taxed at 15% going in [R37 primary]; about +25% per dollar at a 32% rate [R33, computed] |
| Marginal rate 15% or nil | Stay outside super for this money | Advantage is about 2% [R33, computed] and the money is locked to 60 |
| You expect to need the money within about five years | Do not put it in shares | Planning range for a single year is −15% to +20%; deep falls can last years |

Preservation age is 60 for anyone born after 30 June 1964 [R37 primary].

### 1.5 Exact steps

1. **Open the account.** betashares.com.au/direct → Open account → **Individual**, your own name. You need to be an Australian tax resident, 18 or over, with an Australian address and ID [primary]. Give your TFN when asked, or tax is withheld from distributions [unverified for this platform; standard practice].
2. **Fund it.** Transfer **A$5,000** from a bank account in your own name to the Cash Wallet by bank transfer or Osko [primary].
3. **Buy, on an ASX trading day, between about 10:30 am and 3:30 pm Sydney time** (away from the open and the close, where prices are jumpier [spec D5]):
   - **A200 — A$2,000**
   - **BGBL — A$3,000**
   Invest it all at once. Spreading a lump sum over a year has done worse about two times in three [1, Vanguard study via R33; not re-checked].
4. **Turn on distribution reinvestment** for both funds (the order screen offers "Enable reinvestments" [primary]).
5. **Standing bank transfer.** In your bank, schedule **A$500 monthly** to the wallet's BSB and account number, on the day after pay day. Fortnightly A$230 works equally well, because brokerage is A$0.
6. **Auto-invest.** In the app: Auto-invest → select A200 and BGBL → **A$200 to A200, A$300 to BGBL**, monthly, starting two business days after the bank transfer date [primary for the mechanism; the exact frequency options were not shown on the page: unverified].
7. **Save the confirmations** of the two purchases as PDFs in the folder you will use for tax records.
8. **Write down, in one line each:** the date, the amount, and "I will not sell in a fall. Review each November."

### 1.6 Running rules for the index account

| Rule | Detail |
| --- | --- |
| Raise the contribution | 3% every July (A$515 in July 2027). A 3% yearly rise is worth about A$11,000 over ten years at 7% [computed] |
| Rebalance without selling | Each November: if A200 is below 35% or above 45% of the total, set Auto-invest to send 100% to the smaller fund until it is back inside. Never sell to rebalance |
| No dip-buying, no holding back | Money is invested as it arrives [R31 D9, R33 §2.10] |
| Own picks | Nil from this account, ever. If the urge is real: a separate account, capped at a fixed dollar figure you write down today, never topped up from here [R41 D-H, R42 PM-13] |
| 30 June 2027 | Save the platform's holdings statement for that date and the closing price of each fund (section 3, O-TAX-1) |
| Panic rule | Wait 48 hours before any sale; re-read line 8 above [R42 PM-22] |
| Someone else knows | Tell one trusted person where the account is and where the records folder is [R34 §5.3] |

---

## 2. Decision B: FD_FINAL §21 owner items, and the related owner choices

"System" below means the trading system. It holds no real money (decision O23/O25), so many items now apply to its paper account only.

### 2.1 Owner items O1–O25

| ID | Decision | Rationale | Evidence | Revisit when |
| --- | --- | --- | --- | --- |
| **O23** (R33) | **`objective: growth`.** | Owner's decision | Owner instruction; R33 §2.2; R41 D-A | Only on a written change by the owner, with the loss figures in D-F |
| **O25** (R34) | **No real money in the system.** Real money sits in the index account (section 1). The system runs `advisory` on the real holdings and, later, `paper_auto` on IBKR's paper account. This replaces "growth → STATIC live" | STATIC on this system costs A$204–288 a year more than the same holdings held free [R34, computed]; L1 is expected to cost a growth owner return | R34 §5.1; R41 §5.3; R42 PM-01, PM-04 | Section 4.1 conditions |
| **L1 status** | **Paper only.** L1 is never the live rule while the objective is growth, whatever report 36 finds. If report 36 and its independent re-run show a clear fail (drawdown cut under 10% relative), L1 is kept only as a simulated shadow line and no further L1 plant is built | Expected cost about 1.35 points a year against static [R33, model]. Ends behind a free static holding in 75–90% of five-year paths before fixed costs with cash at 0% [R42 §1, simulation] | R33; R41 §1.3; R42 §1 | **Report 36** lands. A strong pass strengthens L1 as a later drawdown option; it does not change this |
| **O1** | **Confirmed:** R15's vote set (6-month return, 12-month return, 10-month average; on at 2 votes, off at 0). R20's version is a sensitivity row inside H1's pack, not a separate card | It is the specified rule; a second live candidate would only add a trial. R42 PM-12 asks that every proposed live rule count in the test family, so it stays visible | Spec §24 H1 grid; R42 PM-12 | Report 36 |
| **O2** | **One tranche. Tranching is not built.** If it is ever built, the threshold is about A$25,000, not A$9,375 | Tripling small orders costs 0.56% a year at the old threshold | R33 §2.7; R41 §2.2 | Managed balance ≥ A$25,000 and L1 chosen |
| **O3** | **Accepted:** integrity halts stop every order; drawdown and cost halts stop buys only; `KILLED` stops everything, including exits, until you resume | Already the owner's decision OD2; sound per R41 §6 | Spec §21 O3 | Never, unless a paper drill shows a fault |
| **Kill semantics** | `/kill` stays absolute. **Add `/pause`** (stop buys, let exits run) and the two-step confirm when a kill would block a planned sell. `/veto` by Telegram is deferred | Gives the common wish ("stop buying") without trapping an exit; reviews 6–8 each found a High defect in the kill/veto delivery path, so fewer parts | R42 PM-22; R41 §3.3, §4.5 | First kill drill on paper |
| **O4** | **Host: spend nothing yet.** Advisory release runs on a computer you already own, or a free cloud tier. For the paper gateway, test the free ARM tier in the spike; if the gateway does not run there, rent Hetzner CX23 by the month (about A$138 a year) and, if that cannot be ordered, BinaryLane 4 GB (about A$259 a year). **No mini PC is bought** | Cheapest adequate. The spec allows the free ARM tier for paper only | R13 lines 9–18, 85–87 [prices 2+ / 1; Hetzner availability unverified] | Spike result; any move to live needs x86 (INF-04) |
| **O5** | **No Norgate rental (A$381 saved). Accept the shorter-sample or free-proxy backtest** that report 36 produces | L1 is not going live; paying for 1990 history decides nothing for a growth owner | R41 §5.1; spec O5 option 3 | Owner chooses `drawdown` and the balance is ≥ A$50,000 |
| **O6** | **Test a free EODHD key on A200.AU, BGBL.AU, VAS.AU, VGS.AU and DHHF.AU first.** If it works: one paid month (US$19.99) for history, then the free plan. If it fails: **do not buy the US$199 year.** Pay month by month (minimum commitment one month [R37 primary]) only for the paper period, and name one alternative end-of-day source | Decides A$31 or A$306 a year. A paper system should not carry A$306 | R37 rows 45–48, §5 item 1; R42 PM-17 | Spike, 16–20 Nov |
| **O7** | **Contribution: A$500 a month by standing transfer (default), +3% each July, into the index account.** In backtests use A$500 a month | You gave no figure; A$500 is the planning figure in every report. The habit matters more than the number | R34 §5.2; R41 D-C | When you tell me the real figure |
| **O8** | **Accepted for the paper account** (one unit of each fund kept while a sleeve is off). Not relevant to real money now | Keeps the second price source alive; costs nothing on paper | Spec DAT-20 | Any move to live |
| **O9** | **No Stage 2. Bonds and gold are never added automatically at any size.** DHHF proxy for benchmark B1: the fund's allocation at 30 Oct 2026 (Australia 37.9%, US 40.4%, developed ex-US 15.0%, emerging 6.6%) until the issuer's strategic weights are read from the PDS | Moving 45% out of shares lowers expected return by roughly 1.0–1.4 points a year [R33, unverified estimate]; a growth owner does not buy that | R33 §2.5; DHHF page [primary] for weights | Owner chooses a lower-risk mix in writing |
| **O10** | **No other users.** M8 is struck from the plan | The only legal risk in the project | R41 §6 rank 11; R42 PM-20 | A lawyer's written opinion, and a reason |
| **O11** | **IBKR: individual cash account, "Investment" type, fixed pricing.** Read both from the account once it is open | Investment type matches the spec's T+2 settled-cash assumption; a "Trading" type releases proceeds at once | R37 row 30, correction F | Account opened |
| **O12** | **Not signed now** (no live trading). You sign the shorter statement in section 2.3 instead | The §30 statement describes a live L1 account | Spec §30 | Any move to live |
| **O13** | **1.5 points a year** (the spec default). H11 is information only under growth | Consistent with H1 and H2 | Spec §24 | Report 36 |
| **O14** | **No.** The Phaseco business domain is not used. M7 (public dashboard) is dropped for now. If a dashboard is ever built, it uses a personal address | Nothing public while unproven; keeps the business out of a personal investment record | Spec D13; R42 §5 item 4 | Owner asks for a dashboard |
| **O15** | **Confirmed, with three changes:** idle cash credited at **0%** (IBKR pays nothing under A$15,000); both CGT regimes; lowest rate 15% for 2026–27 and 14% after. H1's pack also shows the drawdown saving with 2000–02 removed and with 2008–09 removed | A backtest that credits interest the account would not earn is wrong | R37 rows 26, 61, corrections E, K; R41 §2.2; R42 PM-12 | Report 36 (check it used these settings) |
| **O16** | **`unmanaged`** stays the default. Nothing is imported now | No live `trader init` | Spec O16 | Any move to live |
| **O17** | **No go-live.** If it ever happens: sheet mode first (you type the orders), canary of one unit of each fund, then the amount in section 4.1 | The API path is the most fragile part and adds least at six trades a year | R41 §4.3; R42 PM-03 | Section 4.1 |
| **O18** | **Confirmed** as written: a cleared drawdown halt returns only 5 points deeper or after a new peak; cleared cost and tracking halts do not return on the same reading | The safe-side choice; no evidence for another number | Spec RSK-22 | Paper experience |
| **O19** | **Confirmed** both details. On paper the capital cap mirrors the real account: A$5,000 plus each recorded contribution. **Live capital cap: A$0** | Keeps the paper record comparable with what you really hold | Spec PRT-19 | Any move to live |
| **O20** | **Do it at the advisory release (11 Dec):** backup key and list of secrets in your password manager and on paper, off the server | Cheap; the restore drill depends on it | Spec BP-16 | — |
| **O21** | **Keep offset `last`.** The ex-dates of A200, BGBL, VAS and VGS do fall on the first trading day of the quarter or half-year (A200 and DHHF: 1 Jul and 1 Oct 2026; BGBL: 2 Jan and 1 Jul 2026 [primary]; VAS and VGS: 14 quarters checked [R37 primary]). The spec's rules already handle an ex-date order day | Changing the offset is a new parameter choice with no evidence behind it | R37 row 68; fund pages [primary] | Report 36, if it shows the offset matters |
| **O22** | **0** until your tax agent gives a figure | Default in the spec | Spec TAX-06 | First tax return |
| **O24** (R33) | **System's paper universe: A200 40% / BGBL 60%.** Proxies, weights and cards unchanged. VAS and VGS are the pre-registered successors for each sleeve | Same funds as the real account, so advisory records and paper results describe what you own. Cheaper by 0.072% a year. BGBL now has three complete financial years of distributions (2023–24 to 2025–26), which the data check needs | R33 §2.9; R37 rows 4, 5; R42 PM-18 | EODHD check on these tickers in the spike |

### 2.2 The eight decisions report 41 put first

| ID | Decision | Rationale | Evidence | Revisit when |
| --- | --- | --- | --- | --- |
| D-A | Growth | Owner | — | Owner |
| D-B | **Purpose: a platform for a possibly larger account later, and learning.** Wealth is served by the index account, not by the system | It is what "while the system proves itself" means; it makes the system's costs tuition, kept near zero | R41 §1.4, §5.2 | Nov 2027 review |
| D-C | A$500 a month, standing transfer, +3% each July | As O7 | R34 §5.2 | Your real figure |
| D-D | Rule in section 1.4; ask the tax agent | Depends on your rate and age | R33 §2.1; R37 rows 64–67 | When you know your rate |
| D-E | Rules in section 1.4 | Depends on your debts | R33 §2.4 | When you check your loan rate |
| D-F | **Planning assumption: you must be able to sit through a 50% fall: A$25,000 at A$50,000, A$50,000 at A$100,000.** If you read those figures and know you would sell, tell me; that is the one honest reason to revisit L1 | The only sound basis for ever choosing a drawdown rule | R41 §1.3, D-F | Each November; after any fall of 20% or more, but not acted on for 6 months (PM-13) |
| D-G | Index account now | Owner | — | Section 4.1 |
| D-H | Own picks: nil from this account; a separately capped account if you must | Bounded outlet beats an override | R41 D-H; R42 PM-13 | — |

### 2.3 What you sign now (in place of the §30 statement)

> 1. My goal is growth. My money is in two index funds, and I add to it automatically.
> 2. No trading rule in the research is expected to beat this. "Better" for the system will mean cheaper, safer and clearer, not higher returns [R41 §3.2].
> 3. I expect a fall of 40–50% at some point. I will not sell in it. I will wait 48 hours before any sale.
> 4. The trading system holds none of my money. It runs on paper. I will not move money to it unless the conditions in report 44 §4.1 are met.
> 5. If I ever chose the trend rule, I should expect to end five years behind a free static holding about three times in four, in exchange for a lower worst-case loss that shows up in about three periods in ten [R42 §1, simulation].
> 6. I will not act on any league table of rules or funds.

### 2.4 Tax, data, broker and public items I can close or steer

| ID | Decision or status | Evidence | Revisit when |
| --- | --- | --- | --- |
| **T1–T13 (tax agent)** | **The tax agent's letter is not a gate.** Ask at the normal return in Jul–Aug 2027. For a buy-and-hold index account most items do not arise. The three that do: **T4** (how holdings are valued at 30 June 2027), **T13** (how capital gains distributed by the funds are treated after 1 July 2027), and the super question in section 1.4 | R41 §3.3; R42 PM-14 | Before any sale; before any move to live |
| **O-TAX-1** (new) | **30 June 2027 checklist, whatever state the project is in:** download the platform's holdings and transaction statement for that date; record each fund's closing price; store both with the O20 materials. The platform's tax report is the primary record; the system's parcel ledger is the cross-check; a free independent tracker (up to 10 holdings free [1, R34]) is the third view. No return is lodged from the system's figures alone | R42 PM-14; R34 §5.6; R37 row 56 (deemed sale at market value just before 1 July 2027) | Wed 30 Jun 2027 |
| T9, P9, P3, P5, P10, I9 | **Closed** by report 37 on primary text: September quarter 2027 base, 3-decimal rounding, first-published All Groups CPI; lowest rate 15% then 14%; fund fees; 2026–27 calendar including Monday 26 April 2027 open; Telegram 24 hours; IBKR pays 0% on the first A$15,000 | R37 §3 | Tax agent countersigns T9 |
| T2 | Short-term gains are inside the 30% floor on the Act's text; Medicare sits on top. Agent to countersign | R37 rows 59–60 | Tax return |
| **I14 (Flex timing)** | **Choice (a):** the order-time quote is the second price source on the morning after; IBKR's statement becomes an after-the-fact reconciliation from 4:30 pm Sydney. Orders stay on the day after evaluation | IBKR says statements are ready around midnight US Eastern, 2–4 pm Sydney; the 7:30 am pull would normally find nothing [R37 row 35] | Spike and paper test |
| I3 | Match paper trades by execution ID. `orderRef` matching can only be proved on a live account | R37 row 34 | Any canary |
| I1, I2, I4–I8, I15–I17 | **Spike and paper tests.** None can be closed by reading | R37 row 36; R41 §4.6 | Spike |
| E1–E4 | Spike (E1, E4); advisory release (E2); E3 dropped with M9 | R37 row 47 | Spike |
| P1, P2 | Dropped with the Norgate decision (O5) | — | — |
| P4, P8 | Yearly review. ASX still settles T+2 [R37 row 41] | R37 | Each November |
| P6, P7 | P6 only if a cloud host is rented; P7 dropped with M7 | — | — |
| **Chore budget** | **At most 12 scheduled owner actions a year** once the system runs, excluding paper-login approvals. Distribution and calendar entries are automated with a vendor estimate; spreads quarterly; restore check scripted monthly | R42 PM-08; spec §17 lists about 60 a year | Nov 2027 review |

---

## 3. Decision C: programme decisions

### 3.1 Freeze

| ID | Decision | Rationale | Evidence | Revisit when |
| --- | --- | --- | --- | --- |
| C1 | **v2.11 is one amendment to v2.10, issued by Fri 27 Nov 2026, then frozen.** No v2.12 until the advisory release has run 20 trading days. After that, a change is admitted only if it fixes a logged defect, removes scope, or is text with no code | Ten versions and nine reviews in a day; the spec is moving faster than the code | R41 §3.4, §7.2; R42 PM-02, PM-21 | 20 trading days after 11 Dec (about 13 Jan 2027) |
| C2 | **No further full-document reviews.** From now a review is a test result, a paper-account transcript or a reconciled statement. Spec defects found while building go in a defect log | Review finding counts did not fall to zero (43, 16, 13, 6, 5, 10) | R41 §3.3; R42 §5 item 2 | — |
| C3 | **90-day cooling-off.** A change that adds an instrument, a signal, a frequency or a return claim takes effect no sooner than 90 days after it is written, and cannot be written within 6 months of a 15% fall or a 10-point lag | Protects against switching after a bad stretch | R42 PM-13 | — |

**Contents of the v2.11 amendment** (nothing else goes in):

1. `objective: growth | drawdown`; under growth, no live system money [R33 O23, R34 O25, this report].
2. `execution.mode: advisory | sheet | paper_auto | live_auto`. Advisory is release 1. Sheet is the first live mode. `live_auto` needs a separate promotion [R41 §4.4; R42 PM-03].
3. Benchmark B3 (zero-brokerage account) and the cost criteria RSK-30 (6) and (8) [R34 §5.1; R42 PM-16]. Overlay premium budget RSK-30 (7), 10%, applies only if L1 is ever live [R42 PM-05].
4. Idle cash stated at 0%; backtests credit what the account earns; card HG1 [R33 §2.3; R37 K].
5. Tranches deferred; threshold about A$25,000 if ever built. **Defect fix PM-07:** the cost-halt order counts scale with the tranche count (review above 2 × E, halt above 3 × E, E = 2 × N × sleeves). At N = 1 nothing changes; it is fixed now so it cannot bite later [R42 PM-07].
6. Universe A200/BGBL with VAS/VGS as registered successors [O24; R42 PM-18].
7. Contribution tracker and missed-contribution alert; quiet digest; `/pause` [R34 MON-13, MON-15; R42 PM-22, PM-23].
8. Owner chore budget of 12 a year with the automation in PM-08 [R42].
9. Exit paths: `HANDOVER.md` of two pages, `trader hibernate`, `trader retire`, estate note, broker-account hardening checklist [R34 OPS-14, OPS-15, §5.11; R42 PM-09, PM-15, PM-19].
10. Tax safeguards: facts bundle off the server, three-way check, 30 June 2027 checklist [R34 TAX-16; R42 PM-14].
11. Process: card cap of five, single ID register, 90-day cooling-off, 9-month stop date, G2 rule reworded for the five active cards (section 3.5) [R41; R42 PM-02, PM-13].
12. The Live-Core profile in section 3.2 and the dropped milestones (M7, M8, M9, M10).
13. Report 37's corrections A–O as an errata annex (facts and tags; the behaviour changes are A, B and F, decided in section 2.4).
14. Expectations: the sentence in section 2.3 point 2 and report 31's recovery sentence (D13).

### 3.2 Live-Core build profile

I scanned the requirement tables of v2.10 and found **254** requirement IDs (report 41 says "about 270"; report 43 independently counts 254 defined IDs). Each is placed in one of four groups. Report 41 estimated 100–120 for Live-Core; my enumeration gives **155** (87 + 68), because I kept every money-path safety requirement in the paper stage.

| Group | Meaning | Count |
| --- | --- | --- |
| **A — Advisory release** | Needed by 11 Dec 2026. Data, checks, the decision, records, benchmarks, digest, backups. No broker API | 87 |
| **B — Paper-auto** | The IBKR adapter and everything an order needs, on the paper account only. Built only if gate C6 passes | 68 |
| **L — Later** | Built at a named trigger: first tax report, a move to live, or 12 months of running | 44 |
| **X — Out** | Not in the profile. Returns only by a new spec version with a reason | 55 |

| Prefix | A — Advisory | B — Paper-auto | L — Later | X — Out |
| --- | --- | --- | --- | --- |
| SYS | 05–07, 10–16, 18, 30–31 | 01–04, 17, 20, 23–24, 29 | 32 | — |
| OPS | 01–02, 05, 08, 10–13 | 03–04, 07, 09 | 06 | — |
| DAT | 01–06, 08–12, 14–15, 17, 21–23 | 13, 20 | 18–19 | 07, 16 |
| PRT | 10–13, 15, 20, 22–23, 25–26 | 16–19, 21, 27 | 14, 28 | 24 |
| RSK | 25, 30 | 01–04, 06–13, 24, 26–28 | 22, 29, 31–33 | — |
| EXE | — | 01–04, 06–12 | — | — |
| LED | 01–02, 04–05 | 03, 06 | — | — |
| TAX | 01–03, 05, 07–09, 11 | — | 04, 06, 10, 12, 15 | 13–14 |
| MON | 01, 03, 08 | 02, 05–06 | 04, 07 | — |
| VAL | 22, 25, 27 | — | 20–21, 23–24, 26 | — |
| INF | 01–03, 09–10 | — | 04–08 | — |
| RND | 001–004, 006, 032–033 | 030–031 | 005, 010–016, 020–022, 024–025, 027–028, 034 | 023, 026, 029, 035 |
| BP | 06, 09–10, 12–13, 16, 20 | 01–05, 07–08, 11, 14–15, 17–19 | — | — |
| USR | — | — | — | 01, 03–05, 07–11, 13–14 |
| SIZ | — | — | — | 01–15 |
| MKT | — | — | — | 01–05 |
| ENG | — | — | — | 01–07 |
| USE | — | — | — | 01–08 |

Notes on the profile:

- **Group A is simplified where report 41 said so.** DAT-18 (bitemporal tables) becomes raw files plus a corrections log, so it sits in L. LED-01, 02, 04 and 05 reconcile against the platform's statement, imported by hand, because the real holdings are not at IBKR.
- **Never deferred** (all in A or B): reconciliation to the unit and the cent (SYS-02, LED), idempotent orders (OPS-01, BP-17), limit orders only (EXE-02), settled cash only (EXE-08, BP-19), the integrity halt (RSK-01, BP-20), `/kill` (BP-05), the outside dead-man monitor (DAT-12, MON-01), backups with one tested restore (BP-16), the paper/live guard (EXE-12) [R41 §4.5].
- **Group L triggers.** TAX-04, 06, 10, 12, 15: first tax report (Jul–Aug 2027). VAL-20–26 and the RND harness items: only if report 36's result needs a formal G2, or a move to live is proposed. MON-04 and INF-04–08 (dashboard, x86-only): a move to live. RSK-22, 29, 31–33, MON-07, USR-07/RND-034: live operation.
- **Group X.** Other users (USR, milestone M8), public dashboard (M7), Stage 2 engine (SIZ, M9), US venue (ENG, USE, MKT, TAX-13–14, M10), Norgate rental (DAT-16, RND-029), tranching simulation (RND-023), the full battery and vectorised twin (RND-026), the bank-regulation reference (RND-035), FX (DAT-07), hedging variant (PRT-24). MKT-02 and MKT-03 remain true as prohibitions; they need no code.
- **Not adopted from reports 31, 32 and 35 for at least 12 months** [R42 PM-13, §5 item 3]: the challenger library and LRN-01 to LRN-34, the daily shadow brake and daily decision record, the momentum paper sleeve, the "winners you already own" block. Each returns to the table at the November 2027 review at the earliest.
- **Repository.** The re-baseline removes the v1.2 remnants (`commodity.py`, `news.py`, `dip.py`, `regime.py`, the README) as part of the advisory release [R41 §4.2].

### 3.3 Order of work and gates

| ID | Decision | Rationale | Evidence | Revisit when |
| --- | --- | --- | --- | --- |
| C4 | **Reality spike, Mon 16 – Fri 20 Nov 2026**, before any more building. (1) Free EODHD key: end-of-day bars and dividends for A200.AU, BGBL.AU, VAS.AU, VGS.AU, DHHF.AU; publish time; whether a date-range request is one call. (2) IBKR paper: login through the gateway, one snapshot quote, one what-if order, one Activity Flex report and the time it appears, an order found by `orderRef` after a restart, a one-unit buy accepted. (3) The free ARM cloud tier runs the gateway, or not. Result: a one-page pass/fail list against O6, E1, E4, I2–I5, I14, I16, I17 | Facts only a test can settle; nine reviews did not settle them | R41 §4.6, §7.1 item 7; R37 §5 | Results on 20 Nov. Any "fail" changes the design before code is built on it |
| C5 | **Advisory release first, by Fri 11 Dec 2026.** Group A. No broker API anywhere | It cannot place a wrong order; it is useful on day one; it removes about a third of the build from the critical path | R41 §4.4; R42 PM-03 | — |
| C6 | **Paper-auto (Group B) is built only if all three hold on Fri 15 Jan 2027:** the advisory release has run 20 trading days with no unexplained break; the spike's IBKR items passed; report 36 and its independent re-run do not show a clear fail of H1. Otherwise the programme stops at advisory and is reviewed in November 2027 | If L1 fails and the objective is growth, an order adapter has nothing to do that the free account does not already do | R41 §4.6 item 2; R42 PM-02, §5 item 1 | **Report 36**; 15 Jan 2027 |
| C7 | **Paper period (G3) from Mon 18 Jan 2027; exit about Fri 16 Apr 2027** (60 trading days, 6 cycles including drills, 40 order events, zero unexplained breaks) | Report 41's date moved four weeks to make room for gate C6 | Spec §17 G3; [computed] trading days | — |
| C8 | **Stop date: Fri 27 Aug 2027.** If the paper period has not been passed by then (nine months from the first data-pipeline commit), you are shown the hours and dollars spent and choose in writing: continue with a new date, or stop. Stopping costs you nothing, because the money is already invested | The usual failure is never finishing | R42 PM-02 | — |
| C9 | **Running-cost budget while on paper: A$0–31 a year target, A$150 a year ceiling.** Above the ceiling, a written reason or hibernate | The scale-or-stop rule applied to a system with no money in it | R42 PM-16; R13 | Each November |
| C10 | **Dated reviews:** Fri 12 Nov 2027 (first annual), then November 2028, November 2029 and November 2031 (24, 36 and 60 months). Each looks at: cost against budget, chores overdue, months since the last software update, the parked list, and at most one change. Default at each is to continue | Decisions get made on a quiet day with numbers | R41 §3.4; R42 §5 item 6 | — |

### 3.4 Stop the strategy search

| ID | Decision | Rationale | Evidence | Revisit when |
| --- | --- | --- | --- | --- |
| C11 | **Reports 36, 37, 38 and 39 are the last strategy research. No new strategy card for 12 months after the last of them lands** | Five reports reached the same answer independently; a return claim needs t ≥ 3.0, which no long-only index rule will clear | R41 §2.4, §3.2; R40 §0 | Nov 2027 review |
| C12 | **Report 38 (tournament) is read only as a lesson in luck.** No ranking is shown to the owner without the luck band and the negative control. Nothing in it can be adopted | The best of ten no-edge rules leads by about 7.7 points in a year by chance | R35 via R41 §2.4 | **Report 38** lands: file it; no action |
| C13 | **Report 39 (Australia-specific signals):** anything it proposes goes to the parked table | No Australian out-of-sample evidence was found by R35 | R41 §2.4 | **Report 39** lands |
| C14 | **Report 43 (completeness audit) landed as this was finished; read at summary level.** It finds no Critical gap and five High gaps (CA-01 to CA-05), all in the automated live path: no transition table for order states; no execution report independent of the server; secrets at rest unspecified; one phone carries every stop layer; only the signal is independently re-implemented. Decision: **CA-01 is built with Group B as a defect fix. CA-02 to CA-05 become conditions before any real money (added to section 4.1, condition 6). Its 23 Medium and Low items go to the parked table for November 2027.** None is added to v2.11 as new scope | They are faults in the part that is on paper only; fixing them before live costs nothing now and the freeze allows defect fixes | R43 §0, §5 | A full read of R43 §5 by the builder before Group B starts (15 Jan 2027) |

### 3.5 Hypothesis cards: five active, one register

**The five active cards.**

| Slot | Card | Why it is in |
| --- | --- | --- |
| 1 | **H1** — the three-vote filter cuts drawdown | It decides whether L1 exists as an option at all |
| 2 | **H2** — trend is not a return source (control) | Runs on the same settings as H1; catches look-ahead bugs |
| 3 | **H11** — the rule survives tax, both CGT regimes | The 2027 law hits a switching rule hardest |
| 4 | **HG1** — cash ETF while a sleeve is off | IBKR pays 0%; worth about 0.9–1.2% a year to L1 if it ever runs [R33; R37 K] |
| 5 | **HG2** — does L1 leave a growth owner with contributions richer? | It is your question, answered once and pre-registered. Same rule as H1, different measure, so it adds no new rule to the search |

H12 (the haircut) is applied as arithmetic to H1's result and is not a separate run. H10's account-size rows are reported inside H1's pack; its cash-ETF variant is replaced by HG1. The G2 rule in VAL-23 is reworded in v2.11 to match: H1 passes after halving, H2 inside its band, H11 passes at the holder's rate. Under a growth objective G2 is information, not a go-live gate.

**Single register and the H14/H15 collision.** Reports 31 and 32 both used H14 and H15 for different rules. Rule: the spec owns H1–H13; after that, the earlier report keeps its numbers. Report 31 was written first (20:52 against 20:56).

| ID | Rule | Source | Status |
| --- | --- | --- | --- |
| H1, H2, H11 | As spec | Spec §24 | **Active** |
| H3–H10, H12, H13 | As spec | Spec §24 | Parked or folded in as above. H5 (tranches), H6, H7, H9, H13 (Stage 2) parked with their features |
| H14 | Australian momentum tilt (MTUM) | R31 | Parked |
| H15 | Direct ASX stock momentum | R31 | Parked (R31 itself holds it unregistered) |
| H16 | Drawdown-conditioned early re-entry | R31 | Parked |
| H17 | Contributions into a deep drawdown | R31 | Parked (R31 says do not register) |
| **H18** | Daily drawdown brake — **was "H14" in R32** | R32 | Parked. R32's "after card H14 passes" (F-D6) and R35 line 210 now read H18 |
| **H19** | Shadow-brake live record — **was "H15" in R32** | R32 | Parked |
| H8 (amended) | Monthly evaluation sufficient, weekly and daily arms | R32 | Parked; the spec's H8 text stands |
| HG1, HG2 | As above | R33 | **Active** |
| HG3 | 12-month-aware exits | R33 | Parked |
| HP1 | Band rebalancing aware of the 12-month date | R34 | Parked |
| H30–H42 | Report 35's library | R35 | Parked. H42 (steer contributions, never sell) is the first to look at in Nov 2027, because it needs no sale and no tax event |
| H43 | Managed-futures sleeve | R35 | Parked |
| H60 | Managed-futures diversifier sleeve | R40 | **Merged into H43** (same idea); H60 is retired as an alias |
| H61 | Pre-registered live expectation | R40 | Parked (measurement; no live account to measure) |
| H62 | Ledger of what each owner override cost or saved | R40 | **Not a card: adopted as a report feature** when any override is possible (sheet or live mode) |

Next free ID: **H63**. One agent owns the register; a card ID is allocated only by that agent. A parked idea costs no trial. H20–H29 and H44–H59 are left unused so no old reference changes meaning.

### 3.6 If real money ever moves: mode and exit paths

| ID | Decision | Rationale | Evidence |
| --- | --- | --- | --- |
| C15 | First live mode is **sheet** (the system writes the order; you type it; next day's statement confirms it). API ordering only after it has passed on paper and manual entry has shown itself to be the weak point | Removes the largest failure surface at six trades a year | R42 PM-03 |
| C16 | Units move **in specie** from Betashares Direct (up to A$9.50 a security [primary]). Whether that is "not a disposal" for tax is to be confirmed by the tax agent first | Reported as generally not a disposal where the owner does not change [unverified, R34; ATO site blocked] | R34 §5.1; R42 PM-18 |
| C17 | Exit paths exist before any live money: hibernate, retire, a two-page handover note, the order sheet as permanent fallback | A live trader nobody can repair is worse than none | R41 §6 rank 5; R42 PM-09, PM-15 |

---

## 4. Decision C, last part: when real money could move to the system

### 4.1 Conditions and date

**Earliest decision date: Monday 13 December 2027** (12 months after the advisory release). **All** of these must hold:

1. **Twelve months clean.** The advisory release has run since 11 Dec 2026; the paper period (G3) was passed; no unexplained reconciliation break in the last six months; two restore drills and two kill drills passed.
2. **Size.** The balance the system would manage is at least **A$50,000**. At A$500 a month and 7% that is about 70 months from now: **around September 2032** [computed]. Faster if you contribute more.
3. **Cost.** All-in running cost at or below 0.5% a year of the managed balance (that is A$250 at A$50,000), and under the 2.0% scale-or-stop line at every review [R42 PM-16].
4. **A written reason that is not "higher returns".** Either (a) you change the objective to `drawdown` in writing, having read the D-F loss figures and the sentence in section 2.3 point 5; or (b) you want your own automated platform for static holding and accept its cost.
5. **If the reason is (a):** H1 has passed, after the halving in H12, on an independent re-implementation, with idle cash at 0% (or HG1 adopted) and the post-2027 tax rules; and the 10% premium budget is set [R42 PM-05].
6. **Facts closed.** The IBKR items from the spike and paper tests are closed; the tax agent has confirmed the in-specie transfer and the 30 June 2027 valuation; report 43's High gaps CA-02 to CA-05 are fixed (C14).
7. **Timing.** Not within 6 months of a fall of more than 15%, and 90 days after the decision is written [R42 PM-13].

Then: sheet mode, a canary of one unit of each fund, 20 trading days, and half the intended amount for three months before the rest [spec G4, G5].

**Honest forecast.** Under a growth objective, condition 4(a) is never met and 4(b) buys nothing the free account does not give. The likely outcome is that the money stays where it is and the system remains a records-and-paper tool. That is a good outcome, not a failure.

---

## 5. Decision D: owner to-do list

Everything here is yours to do. Nothing else is needed from you.

| When | Do this | Time |
| --- | --- | --- |
| **This weekend, 14–15 Nov 2026** | Check the three rules in section 1.4: emergency cash, any debt above 7%, home-loan offset at 6% or more. If none applies, carry on | 15 min |
| **Mon 16 Nov** | Open a Betashares Direct individual account (ID and TFN ready) | 15 min |
| **By Wed 18 Nov** | Transfer A$5,000. On a trading day between 10:30 am and 3:30 pm, buy **A$2,000 A200** and **A$3,000 BGBL**. Turn on reinvestment. Save both confirmations | 15 min |
| **Same day** | Set the standing bank transfer (A$500 a month, day after pay day) and Auto-invest (A$200 A200, A$300 BGBL, two business days later) | 10 min |
| **By Fri 20 Nov** | Sign the six lines in section 2.3. Register a free EODHD account and pass the key to the builder. Start the IBKR Australia application: individual, cash account, "Investment" type; no money needs to go in for now [unverified: whether paper access needs a funded account; the spike will show. IBKR also offers a free trial login [primary]] | 45 min |
| **Fri 20 Nov** | Read the one-page spike result | 5 min |
| **Fri 27 Nov** | Read and approve the v2.11 amendment (target: two pages). Tell me your marginal rate and whether the super rule applies, if you want the monthly split changed | 20 min |
| **Fri 11 Dec** | Advisory release is running. Read the first monthly plan. Put the backup key and the list of secrets in your password manager and on paper | 20 min |
| **Fri 15 Jan 2027** | Read the gate result (section 3.3, C6): build the paper-order stage, or stop at advisory | 5 min |
| **From Mon 18 Jan 2027** (if the gate passes) | Approve a paper-account login on the phone on order days, about once a month | 1 min each |
| **Late Feb 2027** | Run one restore drill and one kill drill with the builder | 30 min |
| **About Fri 16 Apr 2027** | Read the paper-period report | 15 min |
| **Wed 30 Jun 2027** | Download the Betashares Direct holdings and transaction statement dated 30 June. Write down the closing price of A200 and BGBL. Store both with your tax records | 10 min |
| **July 2027, and every July** | Raise the standing transfer and Auto-invest by 3% (A$515: A$206 and A$309) | 5 min |
| **Jul–Aug 2027** | Tax return. Give the agent the platform's tax report and ask: (1) how are my holdings valued at 30 June 2027 and is the closing price acceptable evidence; (2) how are capital gains distributed by the funds treated now; (3) at my income, should part of the monthly amount go to super; (4) is a broker-to-broker transfer of the same units a disposal | With your return |
| **Fri 27 Aug 2027** | Only if the paper period has not been passed: continue or stop, in writing | 10 min |
| **Fri 12 Nov 2027, and every November** | Annual review, one sitting: is the standing transfer still running; is A200 between 35% and 45% (if not, redirect new money); system cost against the A$150 ceiling; the parked list; at most one change. Re-read your signed lines | 30 min |
| **Mon 13 Dec 2027** | Earliest date the "move real money" question may even be asked (section 4.1). Expected answer: no | — |
| **November 2028, 2029, 2031** | The 24, 36 and 60-month reviews, same agenda | 30 min each |
| **Any time, once** | Tell one trusted person where the account and the records folder are; check your will covers investments | 20 min |

Scheduled actions once things are running: about eight a year, inside the budget of 12.

---

## 6. What would change these decisions

| If | Then |
| --- | --- |
| You have a home-loan offset at 6% or more, or debt above 7% | Section 1.4 applies before section 1.5. Everything else stands |
| Your marginal rate is 30% or more and the money is for after 60 | Part of the monthly amount may belong in super. Tax agent |
| **Report 36** shows L1 cutting drawdown by well over half at an after-tax cost under 0.5 points with cash at 0% | L1 becomes a stronger option for a future `drawdown` choice. No change now |
| **Report 36** shows a clear fail | Gate C6 fails; the programme stops at advisory |
| **Report 43** (landed) | Its High gaps are handled by C14; nothing in its summary contradicts a fact used here. It notes ASIC made its trading-algorithm rules on 15 September 2026, starting 18 March 2028 [2+]: relevant only to live automated trading |
| **Report 37** (already landed) | Its corrections are adopted as the v2.11 errata. It confirmed IBKR's commission and 0% cash interest and the CGT Act; it did not overturn anything this report relies on |
| The spike shows the free data key does not serve ASX funds | Month-by-month data only for the paper period (O6); the A$150 ceiling may be reached; decide at C6 whether paper-auto is still worth it |
| Betashares Direct introduces a fee, drops free Auto-invest, or changes its custody model | Move the units in specie to the then-cheapest broker; nothing is sold. Check each November |
| You find you cannot leave two funds alone | Switch new contributions to DHHF and stop looking. Do not sell the existing units |
| You read the D-F figures and know you would sell in a 50% fall | Tell me. That, and only that, re-opens the trend rule |

---

## 7. Sources

**Read directly today (13 Nov 2026).**

- Betashares Direct: [pricing](https://www.betashares.com.au/direct/pricing/) · [auto-invest](https://www.betashares.com.au/direct/auto-invest/) · [FAQ](https://www.betashares.com.au/direct/faq/) · [comparison, as at 19 March 2026](https://www.betashares.com.au/direct/comparison/) · [account types](https://www.betashares.com.au/direct/account-types/)
- Betashares funds: [DHHF](https://www.betashares.com.au/fund/diversified-all-growth-etf/) · [A200](https://www.betashares.com.au/fund/australia-200-etf/) · [BGBL](https://www.betashares.com.au/fund/global-shares-etf/)
- Betashares, ["Less is more: why the new CGT rules may favour holding a single Diversified ETF"](https://www.betashares.com.au/advisers/insights/cgt-rules-diversified-etfs/) (claims dated 20 October 2026). The issuer is selling its own funds; the mechanism matches the Act as report 37 read it.
- Vanguard Personal Investor: [fees and costs](https://www.vanguard.com.au/personal/invest-with-us/fees-and-costs) · [Auto Invest](https://www.vanguard.com.au/personal/invest-with-us/auto-invest)
- IBKR Australia: [recurring investments](https://www.interactivebrokers.com.au/en/trading/recurring-investments.php) · [free trial](https://www.interactivebrokers.com.au/en/trading/free-trial.php)

**Not reachable today** (connection refused by the proxy): pearler.com, hellostake.com, cmcmarkets.com, superhero.com.au, webull.com.au. Their rows are [2+] at best.

**Not verified by me, carried with the source report's tag:** IBKR commission, interest tiers, account types and Flex behaviour, the CGT Act, tax rates, super rules, ASX calendar, VAS/VGS fees and ex-dates [R37 primary]; VDHG fee [R33, ASX report]; DHHF's underlying funds and withholding leak [1, R33]; Hetzner and BinaryLane prices [R13]; the lump-sum study [1, R33]; CGT treatment of a broker-to-broker transfer [unverified, R34]; the free tracker [1, R34]; mortgage rates relative to the cash rate [unverified].

**Internal.** `FD_FINAL.md` v2.10; reports 13, 31, 32, 33, 34, 35, 37, 40, 41, 42, and 43 (summary). Computations: compound growth at 7% a year with monthly contributions and the stated fund fees; trading-day counts from the ASX 2026–27 calendar as confirmed in report 37; requirement classification by a script over the spec's requirement tables (254 IDs, each placed once).
