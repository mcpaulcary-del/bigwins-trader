# Wave 0 economics gate — cost drag, benchmark, edge, tiers (13 Nov 2026)

**Verdict:** on expected return, neither candidate beats a buy-and-hold benchmark net of costs and tax at A$5k, A$25k or A$100k. The only defensible case is drawdown reduction, and at A$5k this is a learning system at minimum size.

**Verification limits.** WebFetch was blocked for `www.interactivebrokers.com.au`, `treasury.gov.au` and `concretumgroup.substack.com`, so every figure rests on search-result excerpts. Those hosts need allowing in the session's network settings to check primary pages. Figures tagged [model] are my assumptions, not evidence. AUD/USD 0.65 is assumed [unverified].

## 1. Verified inputs

| Input | Value | Tag | Source and quote |
|---|---|---|---|
| IBKR ASX fixed | 0.08%, min A$6 | [2+ sources] | invezz.com/au/reviews/interactive-brokers-review-australia: "start from AUD 6.00 per trade or 0.08% of trade value". interactivebrokers.ie/en/pricing/commissions-bonds-asia-pacific.php: "0.08% of trade value AUD 6 None" |
| GST on ASX commission | Added on top, so 0.088% | [1 source] | interactivebrokers.com.au/en/pricing/commissions-stocks-asia-pacific.php: "400 Shares @ AUD 50 … = AUD 17.60" GST-inclusive |
| ASX minimum incl. GST | A$6.60 | [unverified] | My inference from the row above; confirm in Client Portal |
| IBKR ASX tiered | Not confirmed | [unverified] | An A$5 minimum appeared only for bonds and CFDs |
| US fixed | US$0.005/share, min US$1, max 1% | [2+ sources] | IBKR commissions page; Invezz: "US$0.005 per share with a US$1 minimum" |
| US tiered | US$0.0035/share, min US$0.35, plus exchange/regulatory fees | [1 source] | interactivebrokers.com.au/en/pricing/commissions-home.php |
| FX manual | 0.002%, min US$2, no added spread | [1 source] | IBKR AU: "standalone FX conversion commissions are 0.002%, with a minimum of USD 2.00"; the blogs repeat IBKR |
| FX automatic | 0.03%; cheaper below about US$6,667 | [1 source] | Same IBKR page; breakeven is arithmetic |
| ASX data at IBKR | A$37.50/month non-professional (not the A$25 in the brief); snapshots "$0.03" per quote, capped at the streaming price | [1 source] | interactivebrokers.com/ibis/marketData.php; ibkb.interactivebrokers.com/node/2830 |
| ASX ETF fees | VAS 0.07%, VGS 0.18%, DHHF 0.19%, VDHG 0.27% | [1 source each] | stockwirex.com/?p=34082; investsmart.com.au VDHG page |
| US ETF fees | VTI 0.03%, VEA 0.03%, VNQ 0.13%, GLDM 0.10%, BIL 0.1356% | [2+ sources] | zacks.com low-cost ETF guide; seekingalpha.com/symbol/GLDM/expenses; double.finance |
| PDBC, SGOV fees | PDBC 0.59% (another source says 0.51%); SGOV 0.09% (another says 0.06%) | [conflicting] | Check issuer pages |
| ASX spreads | VAS and VGS about 0.02% | [1 source] | stockwirex; peakifi says "0.01–0.02%" |
| US ETF spreads | Not found | [unverified] | Modelled at 0.03% per side |
| CGT reform enacted | Treasury Laws Amendment (Tax Reform No. 1) Act 2026, assent 26 June 2026, starts 1 July 2027 | [2+ sources] | accountantsdaily.com.au (22595): "passed both houses"; Nexia Aug 2026 PDF: Act No 49 of 2026; bakermckenzie.com July 2026 |
| CGT content | 50% discount replaced by CPI indexation plus a 30% minimum tax; pre-1 July 2027 gains keep the discount | [2+ sources] | ato.gov.au capital-gains-tax-reform; mallesons.com; pwc.com.au |
| Indexation holding period | Only if "held for at least 12 months" | [1 source] | corrs.com.au CGT amendments article |
| 30% floor exemption | Income-support recipients only; low income alone is not exempt | [2+ sources] | fsc.org.au fact sheet; hrblock.com.au |
| US withholding | 15% with W-8BEN, 30% without; offset in Australia; no franking | [2+ sources] | betashares.com.au tax-drag article; expattaxes.com.au |
| US estate tax | Applies to US-situs assets above US$60,000, at 18–40% | [2+ sources, commercial] | quantroutine.com; roopon.com; treaty relief not confirmed |
| EODHD personal licence | One person only | [1 source, primary] | eodhd.com/help/personal-use: "Not if other people can access the data or a service built on it" |

Some sources still describe the CGT reform as "not yet legislated"; they appear to pre-date assent.

## 2. Cost-drag model (% of capital per year)

Assumptions [model]:
- **Turnover:** about one round trip per sleeve per year. Candidate (a) makes 6 ASX trades a year, including a cash ETF leg. Candidate (b) makes 2 VAS trades and about 22 US trades, including SGOV legs and band rebalances.
- **Infrastructure:** VM at A$300 a year, snapshot data, no EODHD.
- **Tax:** 32% marginal rate including Medicare [unverified].
- **Slippage:** 0.05% per side on ASX, 0.03% per side in the US.

| Cost line | (a) 5k | (a) 25k | (a) 100k | (b) 5k | (b) 25k | (b) 100k | Benchmark |
|---|---|---|---|---|---|---|---|
| Brokerage (US tiered) | 0.79 | 0.26 | 0.26 | 0.53 | 0.11 | 0.05 | 0–0.13 |
| Brokerage (US fixed) | n/a | n/a | n/a | 0.94 | 0.19 | 0.08 | n/a |
| FX (2 conversions at US$2) | 0 | 0 | 0 | 0.12 | 0.02 | 0.01 | 0 |
| Spread and slippage | 0.15 | 0.15 | 0.15 | 0.11 | 0.11 | 0.11 | 0.02 |
| ETF fees | 0.11 | 0.11 | 0.11 | 0.14 | 0.14 | 0.14 | 0.13–0.27 |
| Infrastructure, 1 user | 6.00 | 1.20 | 0.30 | 6.00 | 1.20 | 0.30 | 0 |
| Infrastructure, 5 users | 1.20 | 0.24 | 0.06 | 1.20 | 0.24 | 0.06 | 0 |
| Extra CGT from realising gains | 0.6 | 0.6 | 0.6 | 0.6 | 0.6 | 0.6 | 0 |
| Lost franking vs 50/50 VAS/VGS | about 0.1 | about 0.1 | about 0.1 | 0.45 | 0.45 | 0.45 | 0 |
| Unrecoverable foreign tax (inside VEA) | 0 | 0 | 0 | 0.04 | 0.04 | 0.04 | 0 |
| **Total, 1 user** | **7.8** | **2.4** | **1.5** | **8.0** | **2.7** | **1.7** | **0.2–0.3** |
| **Total, 5 users** | **3.0** | **1.5** | **1.3** | **3.2** | **1.7** | **1.5** | **0.2–0.3** |

- **Optional data:** EODHD (about A$370 a year) adds 7.4%, 1.5% and 0.4% at the three levels. It cannot be shared across five users on a personal licence.
- **Streaming ASX data:** at A$37.50 a month it adds a further 9% at A$5k. Use snapshots.
- **CGT timing:** the 0.6% applies until 30 June 2027; I estimate 0.3–0.5% afterwards [model]. The reform narrows the tax penalty for trading, because buy-and-hold loses the 50% discount too. Holds under 12 months still miss indexation.
- **The 30% floor:** a low-income user can no longer realise gains at a low marginal rate.
- **US withholding:** the 15% is mostly recovered through the foreign income tax offset, so it is a cash-flow and paperwork cost, not a material drag.
- **Franking:** credits are worth roughly 1.1–1.3% a year on the Australian-share portion [unverified, my calculation]. Candidate (b) holds one-sixth in VAS against half in the benchmark.

## 3. Benchmark

Single-fund DHHF (0.19%) or VDHG (0.27%), or 50/50 VAS/VGS (0.125%), with regular contributions.
- **Brokerage:** one A$6.60 buy a year at IBKR is 0.13% at A$5k. A zero-brokerage ETF platform would make it nil [unverified].
- **Tax:** no realisation; distributions are taxed the same as in the candidates.
- **Expected drag:** 0.2–0.3% a year at every capital level, with no infrastructure and no operational risk.

## 4. Gross edge and net expected value

Evidence:
- **Faber's 5-asset 10-month SMA rule, out of sample:** 2006 to March 2025 gave "CAGR of 6.05%, a Sharpe Ratio of 0.68, and a maximum drawdown of 11.7%". In sample (1972–2005) it was 11.7%, 0.81 and 9.5%. Drawdowns use monthly data, so they are understated. [1 source: concretumgroup.com/global-tactical-asset-allocation]
- **Same-asset buy-and-hold over 2006–2025:** not found. [unverified]
- **Long-run SMA timing on US equities:** 1871–2012 monthly return 0.75% against 0.79% for buy-and-hold; 1990–2019 8.4% against 8.0% CAGR. This is roughly return-neutral with a better Sharpe ratio. [1 source: cxoadvisory.com]
- **Decay after publication:** out-of-sample Sharpe "deteriorated by 33% (on average) or 44% (median)" across replicated strategies. [1 source: quantpedia.com/in-sample-vs-out-of-sample-analysis-of-trading-strategies]
- **Live implementation gap:** in 2011 the paper GTAA portfolio "returned 2.49%, the ETF lost 7.29%". [1 source: canadiancouchpotato.com]
- **Drawdown benefit:** buy-and-hold fell more than 40% in 2008–09 while the timing models stayed near 10%. [1 source: capitalspectator.com]

My central estimates against an all-equity benchmark returning 7–8% nominal [model]:

| | Gross return edge, % a year | Worst drawdown to expect |
|---|---|---|
| Benchmark | 0 | −35% to −50% |
| (a) VAS/VGS trend | −0.5 (range −2 to +1) | −20% to −25% |
| (b) 6-sleeve trend | −1.5 (range −3 to +0.5) | −12% to −20% |

Candidate (b) lags mainly because a third of it sits in gold, commodities and property trusts.

Net expected value against the benchmark, in % a year (A$ a year in brackets):

| Capital | (a), 1 user | (a), 5 users | (b), 1 user | (b), 5 users |
|---|---|---|---|---|
| A$5k | −8.0 (−A$400) | −3.2 (−A$160) | −9.2 (−A$460) | −4.4 (−A$220) |
| A$25k | −2.6 (−A$650) | −1.7 (−A$420) | −3.9 (−A$980) | −3.0 (−A$740) |
| A$100k | −1.7 (−A$1,700) | −1.5 (−A$1,500) | −2.9 (−A$2,900) | −2.7 (−A$2,700) |

- **Break-even:** none at any capital level. The variable cost floor of about 1.2–1.5% (brokerage, slippage, tax) exceeds a gross edge that is zero or negative.
- **What the owner buys:** roughly half the drawdown, for an expected 1.5–3% a year at scale.
- **At A$5k:** frame it as tuition of about A$400–460 a year for one user, of which A$300 is the VM.

## 5. Capital tiers

| Tier | What is unlocked | Condition |
|---|---|---|
| A$5k | Candidate (a) only, two ASX sleeves, snapshot data, no paid feeds. Purpose is to prove automation, reconciliation and tax records. | Cost is tuition; no return expectation |
| A$25k | Add candidate (b) on IBKR tiered pricing, with FX batched to at most two conversions a year | 12 months of clean operation, and fixed costs at or under 1.2% |
| A$100k | Full system. US-situs holdings would be about US$54k, near the US$60k estate-tax threshold. | Tax-agent sign-off; keep the benchmark as the core holding and trend as a risk overlay |

## 6. Draft expectations statement (one page)

- **Purpose:** learn to run a rules-based system safely. It is not expected to beat DHHF or VDHG.
- **Return, gross:** (a) 5–8% a year over the long run; (b) 4–7%. Single years from −15% to +20%. Expect to lag the benchmark by 5–15% in strong bull years.
- **Worst drawdown:** plan for −25% on (a) and −20% on (b). Published figures near −12% are monthly and understated.
- **Costs:** about A$300 a year fixed, plus 1.2–1.5% of capital in trading and tax drag. That is about 8% in total at A$5k and 1.5–1.7% at A$100k.
- **Kill criteria — stop and hold the benchmark if any occurs:**
  1. Trailing 36-month return lags the benchmark by more than 10 percentage points without a drawdown saving of at least 10 points.
  2. Drawdown exceeds −30%, which would mean the rule is not working as modelled.
  3. Realised all-in costs exceed 3% of capital a year once capital is at A$25k or more.
  4. More than two operational incidents a year (missed or duplicate orders, reconciliation breaks).
  5. Legal or tax advice says the multi-user arrangement needs a licence the owner will not obtain.
  6. The owner overrides signals more than once a year.

## 7. Questions for a registered tax agent

1. Is this investing on capital account or trading on revenue account, given automation and monthly turnover?
2. How do the transition rules apply to parcels straddling 1 July 2027, and is the 12-month condition for indexation as Corrs describes?
3. How does the 30% minimum tax apply to each user, and are short-term losses offset before the floor?
4. Do the 45-day franking rule and the A$5,000 small-shareholder exemption protect franking when VAS is switched monthly?
5. How should the foreign income tax offset be claimed on US ETF distributions, and how are PDBC, GLDM and SGOV distributions characterised?
6. Is there US estate-tax exposure above US$60k, and does the Australia–US estate tax treaty give relief?
7. Are the VM and data costs deductible, and how should they be apportioned across five users?
8. What records are needed for AUD cost base on USD trades and for gains on USD cash balances?
9. Do wash-sale or anti-avoidance rules apply to trend exits and re-entries?

## 8. Questions for a lawyer

1. Does operating software that places orders in other people's IBKR accounts amount to "dealing", "arranging" or a managed discretionary account service requiring an AFS licence? ASIC states you "generally need to hold an Australian financial services (AFS) licence". [1 source: asic.gov.au do-you-need-an-afs-licence]
2. Do signals or default parameters amount to financial product advice, and is there any exemption for unpaid family and friends? I found none. ASIC has acted against an unlicensed person trading pooled money for "family members or friends". [1 source: moneymanagement.com.au and ifa.com.au report the same ASIC action]
3. Which structure is lowest risk: each user self-hosting, a software licence with user-controlled keys and parameters, or cost-sharing only?
4. Does holding users' API credentials on a shared VM breach IBKR's customer agreement or create custody obligations?
5. Can market data be shared across users? EODHD's personal plan cannot; does IBKR non-professional status survive use by a multi-user system, and do ASX redistribution rules apply?
6. What liability does the owner carry for software errors, and what disclaimers, insurance and privacy obligations follow?

## Spec-ready decisions

1. Gate result: proceed only as a learning system at A$5k; do not present it to users as return-enhancing.
2. Launch with candidate (a) only; defer (b) until A$25k or more.
3. Benchmark is DHHF (or 50/50 VAS/VGS), tracked daily in the same ledger, and kill criteria are computed automatically.
4. Budget the ASX commission at 0.088% with a A$6.60 minimum until confirmed in Client Portal.
5. Use IBKR tiered pricing for US trades; fixed roughly doubles US brokerage at small size.
6. FX: use automatic conversion below about US$6,667 and manual above; at most two conversions a year.
7. Data: IBKR snapshots only. No EODHD and no streaming ASX subscription in live operation.
8. Infrastructure cap: A$25 a month for the VM. Multi-user cost-sharing is blocked until legal questions 1–5 are answered.
9. One IBKR account and one credential set per user, with no pooling of money.
10. The tax ledger must store parcel-level acquisition dates, the 1 July 2027 market value per parcel, AUD cost base on USD trades, and withholding per distribution.
11. Add a "hold at least 12 months" tax-aware flag as a later research item, since indexation needs 12 months.
12. Cap US-situs holdings at US$50k per user pending estate-tax advice.
13. Re-verify before go-live: IBKR ASX tiered rates and GST, ASX data price (A$25 vs A$37.50), PDBC and SGOV fees, the personal tax rate, and same-asset buy-and-hold returns for 2006–2025.