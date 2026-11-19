# 59 — Niche Australian edges that big funds can't or won't take: six ideas tested on real data

Date: 14 November 2026. Work folder: `scratchpad/niche/` (`code/`, `raw/`, `out/`, `PREREG_59.md`).
Pre-registration hash (SHA-256, taken before any return was computed): `dcabd05eacef23b46637d11241446f40d261ac3d9d51d1564f720686e7d5e56a`.

## 0. Answer first

**Nothing passed the pre-registered bar. Two ideas are worth a paper forward test; one gives a firm "don't" rule; three are closed.**

| Rank | Idea | Unseen result after costs | Development result | Verdict |
|---|---|---|---|---|
| 1 | **June tax-loss rebound, small caps** (buy the year's worst small caps 4 days before 30 June, sell end of July) | +6.0% over the index in about 5 weeks, t = 2.2, 6 of 8 years ahead (2016–2023) | +2.5%, t = 1.1, 7 of 12 years ahead (2004–2015) | **Not passed, promising.** Paper card H100. Best of the six |
| 2 | **Neglected small caps with the "steady winners" score** (ranks 301–1000 by traded value) | +6.0 points a year over the index, t = 1.2, 3 of 7 years ahead; zero if unexplained delistings are counted as total losses | +18.8 points a year, t = 3.4, 14 of 16 years ahead | **Not passed, promising.** Paper card H101. Decays like the top-300 version did |
| 3 | **LICs: avoid premiums** (a guard, not a strategy) | Premium fifth lagged the average LIC by 0.28% a month (2021–24) and 0.98% a month (2024–26) | Lagged by 0.32% a month (2017–20) | **Firm avoid rule** (pooled t = −4.0 before costs, 111 months). Card H102 |
| 4 | LICs: buy the deepest discounts | +0.17% a month over the average LIC, t = 0.8 | −0.43% a month | **Not passed.** Costs eat it. Parked in H102 |
| 5 | Share purchase plans | Could not be tested for profit: issue prices unreachable | — | **Untested.** Data card H103 |
| 6 | Index additions and deletions (S&P/ASX 200 and 300) | All four trades lose after costs | All four lose | **Closed** |
| 7 | Spin-offs | Demerged companies lost 17% against the index in 12 months (n = 14) | Gained 27% (n = 18) | **Closed** (sign flipped) |

What this means. The owner asked for something no one else looks at. The June rebound is the closest: it sits in stocks trading about A$100,000 a day, where a A$10,000 order is already too big, so no fund can do it. It showed up in both periods before costs and ranked first of the twelve calendar months in both. After costs it is clear only in 2016–2023, the deflated Sharpe ratio is 0.38 to 0.72 against a bar of 0.95, and it is 20 one-a-year observations. That is a paper test, not a reason to commit money.

Two things would change the conclusions: issue prices for share purchase plans (needs `announcements.asx.com.au` or `maynereport.com` allowed), and licensed price data to replace the unlicensed files used here.

## 0.1 Caveats that apply throughout

- **Same price data as reports 51–55**, same defects: unlicensed third-party daily prices to 31 May 2024, no dividends, about one in five splits of delisted companies probably missed, no delisting reasons after April 2020. All small-cap tests stop at May 2024.
- **Benchmarks are price-only** on both sides (XJO price index), except LICs, which use the total returns in ASX's own reports.
- **Costs**: IBKR commission max(A$6.60, 0.088%) on A$2,500 positions, plus a half-spread per side of the largest of half a tick, half the Abdi–Ranaldo spread estimated from each stock's own daily high, low and close over 63 days, and a floor of 0.10% / 0.25% / 0.50% by size. For the June losers this came to a median 1.15% per side.
- **Tax** is approximate: 32% of gains, no discount (all holds are short).
- **Deflated Sharpe ratio** uses 358 trials (325 after report 55, 11 from the idea lab, about 20 here). Reports 56 and 57 may have added more; at 1,000 trials the June figure falls from 0.38 to 0.28.
- **Blindness**: idea 4's direction was known to me from the README of the event file's author; idea 6 is the report-51 score moved to a new universe. Ideas 1, 3 and 5 were blind.
- **Literature**: full texts on UTS, Monash, SAGE, ScienceDirect and SSRN hosts are not reachable from this session. Paper findings below come from search-result summaries and are tagged [unverified] unless I read the source.

## 1. June tax-loss selling in small caps (trials T1, T2)

**Evidence.** Brown, Ferguson and Sherry (2010, *Accounting & Finance*): significant tax-loss selling of losers in June and a July rebound on all ASX companies 1994–2007, concentrated in small mining stocks [unverified: abstract via search]. Brown, Keim, Kleidon and Marsh (1983): July–August seasonal in Australia [unverified]. A broker note quoted by Finance News Network says the trade worked 72% of years since 2000 [unverified].

**Rule (registered).** On the fourth-last trading day of June, take companies ranked below 300 by traded value, with median daily traded value of at least A$50,000 and price of at least 5 cents. Buy the fifth with the worst 12-month return. Sell at the last close of July (T1) or August (T2).

| | Development 2004–2015 (12 Junes) | Unseen 2016–2023 (8 Junes) | Pooled (20) |
|---|---|---|---|
| Stocks per year | 40 | 60 | 48 |
| Gross return, about 5 weeks | +7.9% | +12.2% | +9.6% |
| XJO same days | +2.3% | +2.9% | +2.5% |
| Gross minus XJO (t) | +5.7% (2.4) | +9.4% (3.1) | — |
| Gross minus all small caps in the universe (t) | +2.5% (2.2) | +5.4% (2.4) | +3.7% (3.2) |
| **Net of costs minus XJO (t)** | **+2.5% (1.1)** | **+6.0% (2.2)** | **+3.9% (2.2)** |
| Years ahead of XJO after costs | 7 of 12 | 6 of 8 | 13 of 20 |
| June's rank among 12 months (same rule started each month) | 1st | 1st | — |
| June minus the other 11 months (t) | +4.5% (3.5) | +6.9% (2.7) | — |
| Deflated Sharpe ratio (bar 0.95) | 0.21 | 0.72 | 0.38 |
| Net after tax, about | +2.9% | +5.9% | +4.1% |
| Hold to end of August instead (T2), net minus XJO (t) | +1.1% (0.4) | +4.8% (1.7) | +2.6% (1.2) |

**Controls.**
- In the other eleven months the same losers *lagged* the small-cap universe by 1.5 to 2 points a month. June is the only month where they lead, in both periods.
- Random June picks of the same number from the same small-cap universe made +3.4% net; the losers made +6.4% and beat all 2,000 random draws. About half the raw gain is small caps in July generally; the rest is specific to losers.
- The same rule in the top 300, where funds can trade: +1.7% gross over XJO, t about 0.9 in both periods, negative after costs. The effect is only where funds are absent.
- Winners in the same universe: nothing in development, +1.5% net in unseen.
- Winsorising at the 1st and 99th percentile leaves +2.4% and +4.4% over the universe. The largest single stock return was +137%; no data-error flags.

**What weakens it.**
- Net of costs the development t is 1.1; the registered bar wanted 1.5. Strictly it is "not passed".
- Restricting to prices of 20 cents or more removes the development result (−0.1%) and leaves +3.7% (t = 1.4) in unseen. Much of the gain is in sub-20-cent stocks, where the tick alone is 1–5%.
- Worst years after costs against XJO: −13.3% (2012), −2.9% (2009, 2021), −2.8% (2015).
- A 10-stock sample of the list, which is what a A$25,000 account can buy: mean +3.9% over XJO, ahead in 65% of years, median worst year −14%.
- Losers here have fallen a median 51% in the year. Four of 958 delisted inside the hold.

**Capacity.** Median daily traded value A$104,000 (quartiles A$71,000 to A$169,000). At 5% of a day's value: A$2,500 fits every name, A$10,000 fits 10% (development) to 29% (unseen), A$50,000 fits none. The whole list absorbs roughly A$125,000 to A$250,000 once a year. That is the edge and its ceiling.

**Verdict.** Not passed; the strongest candidate here. Paper card H100.

## 2. Neglected small caps with quality and momentum (trials N1–N4)

**Limit.** No point-in-time fundamentals exist for delisted companies, so "quality" is price-based: low volatility and steadiness. "Neglected" is ranks 301–1000 by traded value; there are no share counts, so true turnover is unavailable.

**Rule.** Each December, among ranks 301–1000 with median daily traded value of at least A$20,000 and price of at least 20 cents, hold the top tenth by report 51's composite (12-1 momentum, 6-month momentum, closeness to the 52-week high, low volatility). Hold 12 months. Delistings: failures at zero, takeovers at last price, unexplained at 70% of last price.

| December cohorts | N1 composite: dev (16) | N1: unseen (7) | N4 composite, price ≥ 50c and A$50k a day: dev (13) | N4: unseen (7) |
|---|---|---|---|---|
| Names held | 19 | 32 | 10 | 18 |
| Top tenth, 12 months | +25.9% | +12.9% | +21.6% | +10.5% |
| All of the universe | +8.1% | +1.9% | +9.6% | +0.8% |
| XJO | +5.0% | +4.9% | +6.1% | +4.9% |
| Minus universe (t) | +17.8 (3.4) | +11.0 (2.3) | +12.0 (1.7) | +9.7 (2.2) |
| **Net of costs minus XJO (t)** | **+18.8 (3.4)** | **+6.0 (1.2)** | +13.5 (1.6) | +3.7 (0.9) |
| Years ahead of XJO | 14 of 16 | 3 of 7 | 10 of 13 | 4 of 7 |
| Median stock minus XJO | +11.8 | −3.8 | +8.1 | −3.9 |
| Unexplained delistings at zero instead: net minus XJO | +18.3 | 0.0 | +12.8 | +0.2 |
| Deflated Sharpe ratio | 0.90 | 0.40 | 0.27 | 0.27 |

Other trials: momentum alone (N2) +14.2 then +3.0 net, with 16–22% of picks losing more than half. Low volatility alone (N3) −1.1 then −7.7 (t = −3.9): calm small caps were poor.

All monthly formations (Newey–West t): N1 net minus XJO +15.0 (4.8) in development, +1.6 (0.9) in unseen.

**Reading.** The score sorts small caps well against each other in both periods (+11 points over the universe in unseen). But the small-cap universe itself returned +1.9% a year against XJO's +4.9% in 2016–2023, so being long the best tenth netted +6 with t = 1.2, the median pick lagged the index, and the result is zero under the harshest delisting rule (11% of unseen picks stopped trading, reasons unknown). This is the report-51 pattern again: strong before 2016, modest after.

**Capacity.** Median pick trades A$80,000 to A$125,000 a day. About A$5,000 a name; 20–30 names; ceiling near A$150,000.

**Verdict.** Not passed; promising. Paper card H101.

## 3. LIC and LIT discounts to NTA (trials L1–L5)

**Evidence.** Bell Potter's quarterly LIC reports rank funds by a z-score of the discount against its 3-year average; Firstlinks warns that discounts revert to a fund's own norm, not to par [unverified: search summaries; hosts not reachable]. No peer-reviewed Australian study was found.

**Data.** ASX Investment Products spreadsheets, January 2017 to October 2026, 118 files from `www.asx.com.au`: about 73 funds a month after filters (market cap ≥ A$30m, monthly traded value ≥ A$250,000). Nothing earlier is reachable, so the split is development 2017–2020, unseen 2021–2023 signals, flagged 2024–2026. Signals lag one full month. 83 funds left the panel; they are counted at 0% in the exit month.

| Monthly excess over the average LIC | Dev (45 months) gross / net | Unseen (36) gross / net | Flagged (30) gross / net | Pooled gross (t) |
|---|---|---|---|---|
| L1 deepest-discount fifth, re-formed monthly | +0.26% / −0.43% | +0.52% / +0.17% | +0.58% / +0.25% | +0.43% (2.7) |
| L2 discount 1.5 s.d. below own 3-year average | +0.21% / −0.11% | −0.01% / −0.66% | +0.72% / +0.10% | +0.28% (1.5) |
| L3 both | −0.04% / −0.33% | +0.35% / −0.25% | +1.19% / +0.63% | +0.42% (1.8) |
| L4 discount ≥ 10% with a buy-back running | +0.47% / +0.18% | 0.00% / −0.32% | +0.10% / −0.22% | +0.22% (1.3) |
| L5 deepest fifth, each tranche held 12 months (added after dev) | +0.14% / +0.03% | +0.28% / +0.17% | +0.08% / −0.04% | +0.17% (1.4) |
| **Premium fifth** (not a trial) | −0.32% / — | −0.28% / — | −0.98% / — | **−0.49% (−4.0)** |

- Discounts do mean-revert: about a third of the gap closes in 12 months (slope −0.30 to −0.34, correlation −0.4 in development and unseen; weaker, −0.13, in 2024–26).
- That does not become profit. A fund at a deep discount usually stays at one, and a A$2,500 trade costs about 0.6–0.8% a side.
- No rule passed. L1 net over 111 months is −0.05% a month. Unseen t after costs is 0.8.
- The buy-back catalyst added nothing. Buy-back headlines cover surviving funds only.
- The premium result is the consistent one: negative in all three periods, 62%, 61% and 80% of months.

**Capacity.** Not the constraint; costs are.

**Verdict.** Deep discounts: not passed. Premiums: an avoid rule (H102).

## 4. Share purchase plans (trials S1–S3)

**Evidence.** Brown, Ferguson and Stone (2008, *Australian Journal of Management*): negative announcement reaction; the bigger the discount, the worse the long-run performance [unverified]. HSF Kramer's 2023 review: average discount 12.4% to last close for placement-plus-SPP [unverified]. OnMarket's "SPP Harvester" sells exactly this trade [unverified, self-reported].

**Data.** ASX's headline search lists every announcement by date, but only for companies listed today, and the PDFs are on a host this session cannot reach. I harvested all 4,533 weekdays from July 2009 (1.26 million headlines) and found 1,228 SPP events. **Only 4 had an issue price in a headline**, so the take-up profit (S3) could not be computed.

| What could be measured (survivors only) | Dev 2009–2015 | Unseen 2016–Feb 2024 |
|---|---|---|
| Events with a results date | 204 | 675 |
| Announcement-day move against XJO | −2.0% (t = −2.6) | −3.8% (t = −14.6) |
| Close after announcement → results date, against XJO | +0.7% (0.6) | −1.9% (−3.4), median −2.5% |
| Share of offers where the price fell more than 5% / 10% / 15% in the offer period | 35% / 21% / 13% | 38% / 21% / 10% |
| 60 trading days after allotment, against XJO (S1) | +2.2% (0.7), median −0.8% | +1.7% (0.9), median −3.7% |
| Offer period, scaled-back offers only | +12.0% (1.9), n = 20 | +4.2% (3.1), n = 132 |
| Offer period, offers that were extended | +0.8% | −4.5% (−4.0) |

**Reading.** If the typical discount is near 10% of the pre-announcement price, then after a 2–4% announcement fall and a further median 2% slide, something like 4–6% is left for the typical survivor, and one offer in five loses the whole discount. Popular offers are scaled back, so the good ones give the smallest allocation. No post-allotment drift either way: no case for holding on, none for a quick sale beyond locking in the discount. These are survivors; failed raisers are missing, which flatters every number.

**Practical rule (unverified by data here).** Decide on the last day, apply only if the market price is clearly above the issue price, expect scale-back. A holder must own shares before the record date, which is usually the day before the announcement.

**Verdict.** Untested for profit. Data card H103.

## 5. Index additions and deletions (trials I1–I4)

**Evidence.** Zhao, Schmidt and Terry (2016): price pressure between announcement and implementation, partly reversing over 20 days [unverified]. The event file's author reports +1.8% around announcement for ASX 200 additions, then full reversal [1: README read].

**Data.** 2,230 quarterly-review events matched to prices, September 2012 to March 2024, from S&P announcement PDFs parsed by `Taff1887/asx-index-rebalance` (MIT). 129 events did not match a code. I read one PDF against the file (September 2019: 12 of 12 ASX 200 rows agree); the planned 12-event random check was not done. Pre-2012 was not tested.

| Trade, excess over XJO | Dev gross (t) / net | Unseen gross (t) / net (t) |
|---|---|---|
| I1 ASX 300 additions: buy next open, sell at the effective close | +1.4% (1.5) / −0.5% | +1.8% (3.7) / −0.6% (−1.4) |
| I2 ASX 300 deletions: buy the effective close, hold 20 days | −3.6% (−1.1) / −6.9% | −1.0% (−1.0) / −3.8% (−3.8) |
| I3 ASX 200 additions: as I1 | −2.5% (−2.4) / −4.0% | +0.3% (0.3) / −1.6% (−1.7) |
| I4 ASX 200 deletions: as I2 | −3.5% (−0.7) / −5.9% | −0.1% (−0.1) / −2.0% (−1.1) |

- ASX 300 additions do rise 1.8% before the effective date, and beat matched random stocks by 2.3 points (t = 3.9). Round-trip costs in these stocks are about 2.4%. The median addition gained 0.4%.
- A further 1.0% (ASX 300) and 1.2% (ASX 200) is the overnight gap after the announcement, which cannot be bought.
- Deletions do not rebound. ASX 300 deletions fell a further 10% in 60 days in development and 2.8% in unseen.
- ASX 200 additions fell 2.2% in the five days after the effective date in unseen (t = −2.0).

**Verdict.** Closed. Useful only as a "don't buy the new index entrant on the day" note.

## 6. Spin-offs and demergers (trials D1, D2)

**Evidence.** Chai, Lin and Veld (2018, *Australian Journal of Management*): positive long-run excess up to 24 months, driven by focus-increasing spin-offs [unverified]. Macquarie, quoted by FNArena: child underperforms early, parent outperforms from about 18 months [unverified].

**Data.** 36 demergers listed from memory before prices were read, child first-trade dates confirmed in the price file. 32 usable (three in 2000 predate the index series; one not in the price panel). A memory list over-represents large, well-known cases. Entry on the fifth day after listing.

| 12-month excess over XJO | Dev 2002–2015 | Unseen 2016–2022 |
|---|---|---|
| Demerged company (D1) | +27.2% (t = 2.8), n = 18, 72% ahead | −17.0% (t = −1.6), n = 14, 36% ahead |
| Parent (D2) | +0.6% (0.1), n = 14 | +5.8% (0.7), n = 12 |
| Demerged company, 6 months | +4.9% | −23.4% (t = −3.8) |
| Demerged company, 24 months | +33.9% (2.5) | −25.5% (−2.4), n = 12 |

The unseen sample includes five small resource spin-offs (2021–22) that lost 30–64% (a sixth, Leo Lithium, gained 83%), but the large ones were also weak (Domain −25%, United Malt −40%, Deterra −26%).

**Verdict.** Closed. The sign flipped.

## 7. Ranked list of what survives

1. **June small-cap loser rebound**: promising, not passed. Paper only.
2. **Neglected small-cap steady winners**: promising, not passed. Paper only.
3. **Never buy a LIC at a premium**: a guard worth adopting now; it costs nothing.
4. Everything else: closed or untestable.

No idea met "t ≥ 2 unseen, t ≥ 1.5 development, both after costs". No deflated Sharpe ratio reached 0.95.

## 8. Engine rules and cards for paper forward testing

Common to all cards: paper only on the IBKR paper account; family `NICHE`; N_lib 358 at registration; costs and tax as section 0.1; data must be the licensed company store, not these files.

### H100 — June tax-loss rebound in small caps

| Field | Content |
|---|---|
| Rationale | Individuals sell losers before 30 June to realise losses; funds cannot supply liquidity in stocks trading A$100,000 a day |
| Exact rule | On the 4th-last trading day of June: companies with ≥ 200 traded days in 252, traded-value rank worse than 300, median daily traded value ≥ A$50,000, close ≥ A$0.05. Rank by 252-day price return to the previous close; take the worst fifth. Buy equal dollars at the close with limit orders. Sell at the last close of July |
| Fixed parameters | Fifth; 4th-last day; end-July exit; A$2,500 a name; no stop |
| Permitted grid | None. Reported alongside, not selectable: price ≥ A$0.20 version; end-August exit |
| Sample | Development 2004–2015, seen holdout 2016–2023 (this report). Confirmatory: Junes from 2027 |
| Benchmark | A200 over the same days; secondary, a random same-size draw from the same universe |
| Pass | After real fills, mean excess over A200 > 0 with t ≥ 3.0 and DSR ≥ 0.95. Not expected within 10 years (10 observations) |
| Review trigger | After 5 Junes: if 4 or 5 are behind A200 after costs, close |
| Fail | Cumulative net result more than 15 points behind A200 at any review |
| Secondary | Realised spread against the 1.15% model; fill rate; share of names not purchasable; the price ≥ A$0.20 line |
| Reference numbers | Net minus XJO +2.5% (dev), +6.0% (unseen); DSR 0.38 pooled |

### H101 — Steady winners in ranks 301–1000

| Field | Content |
|---|---|
| Rationale | Same under-reaction as H80, in a size band funds do not hold |
| Exact rule | Last trading day of December: ranks 301–1000 by median traded value, ≥ A$50,000 a day, close ≥ A$0.50 (the N4 form, chosen for tradability, weaker in back-test than N1). Top tenth by the H80 composite ranked inside this universe. Hold 12 months and one day |
| Fixed parameters | As stated; equal weight; no stop |
| Sample | Development 2000–2015, seen holdout 2016–2022 cohorts. Confirmatory: cohorts from December 2026 |
| Benchmark | A200 total return; secondary, the equal-weight universe and H82 |
| Pass | t ≥ 3.0 and DSR ≥ 0.95 after costs |
| Fail | More than 15 points behind A200 cumulatively at a 36-month look |
| Reference numbers | N4 net minus XJO +13.5 (dev), +3.7 (unseen); N1 +18.8, +6.0 |
| Note | Report whether delisted picks were takeovers or failures; the back-test could not tell after 2020 |

### H102 — LIC premium guard and discount tracker

| Field | Content |
|---|---|
| Rule (guard, adoptable now) | Never buy a LIC or LIT trading in the top fifth of the sector by premium to pre-tax NTA at the latest month-end |
| Rule (paper tracker) | L1: hold the deepest-discount fifth, re-formed monthly, against the equal-weight sector |
| Data | ASX Investment Products monthly spreadsheet (free, published mid-month) |
| Reference numbers | Premium fifth −0.49% a month against the sector over 111 months (t = −4.0, before costs). L1 +0.43% gross, −0.05% net |
| Pass for the tracker | Net t ≥ 3.0; not expected |

### H103 — Share purchase plans: data card

| Field | Content |
|---|---|
| Blocker | Issue price, closing date and scale-back are in PDFs on `announcements.asx.com.au`, or in the Mayne Report's lists; neither host is reachable |
| What exists | `out/spp_events.csv`: 1,228 events with announcement and results dates and flags, survivors only |
| Test once data exists | Close 5 days after allotment ÷ issue price − 1, after scale-back, with the last-day "in the money by 5%" rule against "always apply" |

### Closed (so they are not re-proposed)

- H104: index additions and deletions, S&P/ASX 200 and 300, 2012–2024. All four long trades lose after costs.
- H105: demerged companies and parents, 12 months. Sign flipped after 2015.
- H106: LIC own-history z-score, combined rule, buy-back catalyst. Nothing after costs.

## 9. How the survivors would combine with the Big Wins engine

- **Separate sleeve, not a change to H82.** H82 holds 10–30 of the top 300 for a year. H100 holds about 50 micro-caps for five weeks; H101 holds 10–30 names from ranks 301–1000.
- **Size.** On paper: A$25,000 for H101 and up to A$25,000 for H100 (10 names at A$2,500), both inside the existing 20% slice cap. H100's cash sits in the index for the other 47 weeks.
- **Overlap.** H100 picks stocks with the worst 12-month returns; H82 and H101 pick the best. They do not hold the same names. H101 and H82 use the same score on non-overlapping size bands, so they will rise and fall together; treat them as one bet when sizing.
- **Scoring.** Each sleeve printed monthly beside the same dollars in A200, plus a random-draw control for H100.
- **Guard.** H102's premium rule applies to any LIC the owner picks in the tracked book.
- **Real money.** Nothing here supports it. Section 17.3's conditions apply unchanged.

## 10. Scope additions from report 61

- **Typed event table**: `scratchpad/niche/out/events.csv.gz`, 1,256,400 headlines, 1 July 2009 to 13 November 2026. Columns: date, time, code, price-sensitive flag, document type, headline, pages, ASX document id. Types are a headline pattern match, not ASX's categories: 4E 23,251; 4D 25,564; 4C 19,268; 3Y 84,673; 604 50,836; 603 28,279; 2A 42,713; 3B 51,569; others in `events_README.md`.
- **Survivorship of the harvest**: only companies listed on 14 November 2026 are returned. Share of codes trading in each year that appear:

| 2009 | 2011 | 2013 | 2015 | 2017 | 2019 | 2021 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|
| 22% | 25% | 29% | 35% | 42% | 50% | 62% | 73% | 80% |

  Full table: `out/harvest_survivorship_by_year.csv`. A results-day test on this table is survivor-biased, heavily before 2018.
- **ETF flows**: `out/etf_flows_monthly.csv`, 32,330 fund-months, January 2017 to October 2026: funds under management, monthly net flow, traded value, spread, returns. Yearly net flow sums run from A$8.1bn (2017) to A$54.1bn (2026 to October); I have not checked these totals against a second source.

## 11. Reasons this could be wrong

- June: 20 observations, one a year; the modelled spread may be too low at the close on thin days; missed splits in delisted micro-caps.
- Neglected small caps: post-2020 delisting reasons are unknown and move the unseen result between +8.6 and 0.
- LICs: 9.8 years, one cycle of widening discounts; exit months at 0% is a guess.
- SPPs: survivor-only, no prices.
- Demergers: my list, from memory.
- The trial count excludes whatever reports 56 and 57 added.

## 12. Files

| File (under `scratchpad/niche/`) | Content |
|---|---|
| `PREREG_59.md`, `out/PREREG_59_frozen.md`, `out/prereg_hash.txt` | Registration, deviations (section 10), hash |
| `raw/manifest.tsv` | Every download: time, status, size, SHA-256, URL (118 ASX spreadsheets, 4,533 headline pages) |
| `code/lic.py`, `june.py`, `neglect.py`, `index_ev.py`, `demerge.py`, `spp.py`, `px.py`, `lib.py` | Tests |
| `code/parse_ann.py`, `etf_parse.py`, `lic_parse.py` | Parsers |
| `out/trials_59.csv`, `out/looks.csv` | Every specification run; every look at unseen data |
| `out/june_*.csv`, `neglect_*.csv`, `lic_*.csv`, `index_events.pkl`, `demerge_events.csv`, `spp_*.csv` | Results |
| `out/events.csv.gz`, `events_README.md`, `etf_flows_monthly.csv`, `harvest_survivorship_by_year.csv` | Scope additions |

Unseen-data looks: one per idea, except LIC (three: first run, a cost bug fix affecting L5 only, and L4 after the headline harvest) and demergers (run twice with identical code).

Hosts that would need allowing to finish the open items: `announcements.asx.com.au`, `www.maynereport.com`, `opus.lib.uts.edu.au`, `www.firstlinks.com.au`.
