# 61 — Assessment gap review: what the programme has not looked at, ranked, with the next five tests

Date: 2026-11-14. Status: independent review of reports 31, 36/38/45–48, 39, 51–57 and of the work in progress for 58–60. No back-test was run for this report. Research use only; general information, not financial advice.

**Tags.** **[2+]** two or more independent sources agree; **[1]** one source, or several listings of one study; **[unverified]** model memory, or a search summary I could not check against a primary page; **[computed]** my own count from files in the scratchpad. As in report 56, "[2+]" here means abstracts and listings agree. No academic full text was opened.

## 0. Answer first

**The programme has tested prices thoroughly and almost nothing else. The largest untested area is the free, dated, public record of what companies and regulators file: short positions, shares on issue, capital raisings, results dates, director and substantial-holder notices. Two of those sources are point-in-time and one of them includes delisted companies, which is exactly what report 57 said could not be bought. None of this is likely to overturn the programme's main finding (the index wins at this account size). Its realistic value is as an "avoid" screen on the Big Wins paper book and as a red-flag panel beside the owner's own picks.**

1. **Best single gap: ASIC's daily short-position files.** Free, published since positions of 16 June 2010 [1], dated, and written each day for whatever was listed that day, so delisted companies are in them. International evidence that heavily shorted stocks underperform is strong [2+]; Australian stock-level evidence is thin [1]. The same file is reported to carry "total product in issue" for each stock [unverified until the first download]. If it does, it is also a free point-in-time share count, which gives net share issuance and market value without hindsight from 2010.
2. **Second: dilution.** The ASX's characteristic way of destroying small shareholders is repeated placements. Australian studies find issuers underperform for up to five years, worst after private placements [2+]; the international share-issuance effect holds in 41 countries [2+]. The programme has not tested it.
3. **Third: listing age.** Australian IPOs underperform over one to three years [2+, older samples]. The price panel already contains first-trade dates including delisted companies, so this is the only new test that is free, survivor-free and runnable today back to 2000.
4. **Fourth: real results dates.** Report 56's results-drift test failed on a proxy because it had no results calendar. Report 59's headline harvest now holds the release date and time of every Appendix 4E/4D from July 2009 (survivors only). The test can be re-done properly once.
5. **Fifth: start a forward archive today.** Director trades, substantial-holder changes, cash runway, consensus estimates and fundamentals cannot be bought historically at this budget. They can be collected from today for almost nothing, and every day not collected is lost. This also cures the survivorship in the headline source going forward.
6. **Most of the "alternative data" list should be rejected at this account size:** job postings, web traffic, app downloads, supply-chain links, options-implied measures, credit signals, ESG scores, HotCopper sentiment, Google Trends, ADR arbitrage. Either the data cost exceeds any plausible edge on A$25,000–100,000, or the signal lives at a daily horizon that A$6.60 brokerage on A$2,500 positions cannot survive (report 56's finding), or the evidence says the signal is contemporaneous and not predictive.
7. **The framing that follows from reports 51 and 53:** the usable information in prices was "mostly about which stocks to avoid", and the 30 biggest winners were not visible beforehand. Every top-ranked gap below is therefore tested as an exclusion rule on the frozen engine and as a base-rate flag, not as a new way of finding winners.

**Ranked top 15** (score = evidence × data × testability × expected value, each 0–3, maximum 81; section 2 has all 40 rows):

| Rank | Dimension | Score | Recommendation |
|---|---|---|---|
| 1 | Short interest (ASIC daily short positions) | 54 | **Test now** |
| 2 | Net share issuance / capital raisings / buy-backs (dilution) | 54 if ASIC share counts confirm, else 24 | **Test now** |
| 3 | Listing age (IPO seasoning, escrow) | 18 | **Test now** (free today) |
| 4 | Director trading (Appendix 3Y) | 16 | **Forward-collect**; paper card |
| 5 | Resources versus industrials as separate problems (sector at the time) | 16 | Park until a licensed data rental |
| 6 | Results-day reaction on real results dates | 12 | **Test once** (survivors only) |
| 7 | Announcement flow and price-sensitive news intensity | 12 | Build the event table now; test later |
| 8 | Liquidity, turnover and split-adjusted volume | 12 | Fix the data; add to 59's idea 6 |
| 9 | Cash runway and going-concern flags (Appendix 4C/5B) | 8 | **Forward-collect** |
| 10 | Seasonality of company events (reporting season, AGMs, "confession season") | 8 | Park; one descriptive table |
| 11 | Dividend initiations, cuts and omissions | 8 | Park until dividends are licensed |
| 12 | Trading halts and ASX price queries | 6 | Event table only |
| 13 | Substantial-holder notices and activists | 4 | **Forward-collect** |
| 14 | Takeover-target prediction | 4 | Park; one attribution table |
| 15 | Analyst coverage, revisions, target prices, consensus surprise | 3 | **Forward-collect** if a licensed feed is already paid for |

**Top five actions** (section 5 has the designs):

| # | Action | Data | Cost | Trials |
|---|---|---|---|---|
| A1 | Short-interest exclusion test | `download.asic.gov.au/short-selling/` daily files, 2010-06-16 on | A$0; the host must be allowed | 2 |
| A2 | Dilution exclusion test (and "shrinkers") | Same ASIC files ("total product in issue"); fallback: ASX headline counts | A$0 | 3 |
| A3 | Listing-age exclusion test | `company_study/data/stage1.pkl` (already held) | A$0 | 2 (+1 composite) |
| A4 | Results-day reaction on real dates | Report 59's headline harvest (`niche/raw/annday`, `ann`) | A$0 | 2 |
| A5 | Forward archive and red-flag panel | ASX announcement lists and PDFs, ASIC files, monthly snapshots | A$0 data; one to two days' build | 0 (measurement cards) |

Ten trials in total, pre-registered in one file, taking the programme count from about 358 to about 368.

**For the running agents now:** 58 should store a retrieval date on every figure and take dated monthly copies from today, and add share counts, listing date, accruals, asset growth and cash-runway fields. 59 should save its headline harvest as a clean event table (no new trials) and extract ETF flows from the ASX spreadsheets it already holds. 60 should add aggregate ASX short interest as a market-level predictor, a dated list of royalty and policy changes, and estimate exposure betas only on data before each test date. Details in section 6.

## 0.1 Caveats

- **No test was run.** Every expected value below is a judgement from published effect sizes halved (the spec's VAL-26 rule) and scaled to a long-only book of 10–30 names.
- **Reports 58, 59 and 60 do not exist yet.** I read 59's frozen pre-registration (`scratchpad/niche/PREREG_59.md`) and the directory listings of `company_db/` and `niche/`. I found no working directory for 60. Their results may change the ranking.
- **ASIC was not reachable from this session** (`asic.gov.au` and `download.asic.gov.au` returned no connection through the proxy). The file layout, the "total product in issue" column and the licence terms are from search listings and memory and must be confirmed on the first download. Rank 2's higher score depends on that.
- **Also blocked:** `hotcopper.com.au`, `trends.google.com`, `abs.gov.au`, `apra.gov.au`, `tenders.gov.au`, `accc.gov.au`, `shortman.com.au`; `marketindex.com.au` returned 403; the GDELT API returned 429 (rate limit). `asx.com.au` announcement lists and `rba.gov.au` worked.
- **Australian evidence is thinner than international evidence for almost every item**, and several Australian studies are from samples ending before 2010.
- **Power.** Report 53 showed that a true edge of 2.5 points a year needs decades to show at t ≥ 3. An exclusion rule that changes three names in thirty moves the book by well under a point a year. Most of the tests below will end "promising, parked" or "not passed", not "proven". They are worth doing because they cost nothing and the stand-alone versions (flagged stocks against the rest of the universe) have far more breadth than a ten-stock book.
- **Card numbers H110–H117 are provisional.** Report 57 used up to H100 and report 59 plans "H100+". Check for a clash before registering.

## 1. What has been covered, and what that implies

| Area | Reports | State |
|---|---|---|
| Index-level timing, allocation, trend, calendar, currency, RBA, commodities at monthly horizon | 36, 38, 39, 45–48 | Done. Nothing beats holding 40/60 after costs and tax |
| Company-level price signals: momentum family, 52-week high, low volatility, MAX, beta, reversal, same-month seasonality, frog-in-the-pan | 51, 53–56 | Done on unlicensed price-only data. H80 frozen; H88 a paper challenger |
| Sell rules, review frequency, self-adapting rules | 53, 55 | Done. All worse on unseen years |
| Quality and profitability | 57 | Evidence reviewed; no honest ASX back-test obtainable; ETFs on the scoreboard |
| Niche structural edges: LIC discounts, SPPs, demergers, index changes, tax-loss small caps, neglected small caps | 59 | In progress, pre-registered, 19–22 trials |
| Company database from stockanalysis | 58 | In progress; survivors only, restated figures |
| Drivers: commodities, macro, GDELT news, exposure betas | 60 | In progress |
| Knowledge store and research loop | 52 | Designed |

Four things follow for a gap review.

1. **The untested information is in filings, not prices.** The price panel has been worked hard (about 350 trials). The marginal trial on prices is worth little. The marginal trial on a new, independent data source is worth more.
2. **Honest history is the binding constraint, so rank data by whether it is dated and includes dead companies.** Only three free sources pass: the price panel itself (first-trade dates, delisting reasons to 2020), ASIC short-position files (2010 on), and any archive the owner starts today. The ASX headline lists are dated but list only companies still listed (report 59 checked: 72 of 75 codes on one day).
3. **Survivorship cuts one way for "avoid" rules.** If failed companies are missing, a red flag that predicts failure will look weaker than it is. So on survivor-only data a finding that flagged stocks underperform is conservative, and a null result is uninformative. Tests on that data can be "partly tested" at best, as report 59 already says for SPPs.
4. **The owner-picks book (report 53 section 6) can use flags without proof.** "This company has issued 35% more shares in a year, is 8% short and has two quarters of cash" is a factual statement with a base rate attached. It does not need a t-statistic to be worth printing beside a proposed pick.

## 2. All dimensions, scored

Scoring, each 0–3. **E** evidence (3 = strong international and some Australian; 2 = strong international or mixed Australian; 1 = weak or contemporaneous only). **D** data for a small investor (3 = free and dated; 2 = free with work or gaps; 1 = paid or forward-only; 0 = unaffordable). **T** honest testability now (3 = point-in-time and includes delisted; 2 = dated but survivors only; 1 = forward only). **V** expected value at A$25,000–100,000 after costs (3 = could plausibly add more than 1.5 points a year; 2 = 0.5–1.5; 1 = under 0.5 or only at the top of the size range; 0 = negative after costs).

| # | Dimension | E | D | T | V | Score | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Short interest (ASIC) | 3 | 3 | 3 | 2 | 54 | Test now |
| 2 | Net share issuance, placements, entitlement offers, buy-backs | 3 | 3* | 3* | 2 | 54* / 24 | Test now |
| 3 | Listing age, IPO seasoning, escrow release | 2 | 3 | 3 | 1 | 18 | Test now |
| 4 | Director trading (3Y) | 2 | 2 | 2 | 2 | 16 | Forward-collect |
| 5 | Sector at the time: resources against industrials, explorers excluded | 2 | 2 | 2 | 2 | 16 | Park (needs licensed data) |
| 6 | Results-day reaction, real dates | 3 | 2 | 2 | 1 | 12 | Test once |
| 7 | Announcement flow, price-sensitive intensity, news against no-news momentum | 2 | 3 | 2 | 1 | 12 | Event table now |
| 8 | Liquidity, turnover, split-adjusted volume, spreads | 2 | 2 | 3 | 1 | 12 | Data fix |
| 9 | Cash runway, going concern (4C/5B) | 2 | 2 | 1 | 2 | 8 | Forward-collect |
| 10 | Event seasonality (reporting season, AGMs, confession season, announcement-month premium) | 2 | 2 | 2 | 1 | 8 | Park |
| 11 | Dividend initiation, cut, omission, policy | 2 | 2 | 2 | 1 | 8 | Park |
| 12 | Trading halts, price queries ("speeding tickets") | 1 | 3 | 2 | 1 | 6 | Event table |
| 13 | Substantial-holder notices (603/604/605), activists | 1 | 2 | 2 | 1 | 4 | Forward-collect |
| 14 | Takeover-target prediction | 1 | 2 | 2 | 1 | 4 | Park |
| 15 | Management changes (CEO, CFO, chair) | 1 | 2 | 2 | 1 | 4 | Event table |
| 16 | Analyst coverage, revisions, targets, consensus surprise | 3 | 1 | 1 | 1 | 3 | Forward-collect if cheap |
| 17 | Guidance changes, profit warnings | 2 | 2 | 2 | 0–1 | 0–8 | Avoid-flag only |
| 18 | Accounting red flags (accruals, asset growth, auditor change, late lodgement) | 2 | 1 | 1 | 1 | 2 | Into 58, forward only |
| 19 | Valuation (value factor at stock level) | 2 | 1 | 1 | 1 | 2 | Into 58, forward only |
| 20 | Index-weight changes, ETF and super flows | 1 | 2 | 2 | 0–1 | 0–4 | 59/60 add-on |
| 21 | Aggregate short interest as a market signal | 2 | 3 | 3 | 0–1 | 0–18 | 60 add-on |
| 22 | Government contracts (AusTender) | 1 | 2 | 1 | 1 | 2 | Park |
| 23 | Regulation, royalties, critical-minerals policy | 1 | 2 | 1 | 1 | 2 | Risk register; 60 |
| 24 | Patents, R&D intensity | 2 | 1 | 1 | 1 | 2 | Park |
| 25 | Founder-led, insider ownership level, register concentration | 1 | 1 | 1 | 1 | 1 | Park |
| 26 | Governance events (remuneration "strikes", board spills) | 1 | 2 | 2 | 0–1 | 0–4 | Park |
| 27 | China trade data by commodity | 1 | 2 | 2 | 0–1 | 0–4 | 60 |
| 28 | Shipping and freight | 1 | 2 | 2 | 0 | 0 | 60, descriptive |
| 29 | Weather and climate for agricultural stocks | 1 | 3 | 2 | 0 | 0 | Reject |
| 30 | Google Trends / search attention | 2 | 2 | 1 | 0 | 0 | Reject |
| 31 | HotCopper and social media | 1 | 1 | 1 | 0 | 0 | Reject (hype flag only) |
| 32 | Options-implied information | 2 | 1 | 1 | 0 | 0 | Reject |
| 33 | Credit and bond signals | 2 | 1 | 1 | 0 | 0 | Reject at stock level |
| 34 | Supply-chain and customer links, US-peer lead–lag | 2 | 0–1 | 1 | 0 | 0 | Reject |
| 35 | Job postings, web traffic, app downloads | 2 | 0 | 0 | 0 | 0 | Reject |
| 36 | ESG controversies and scores | 1 | 1 | 1 | 0 | 0 | Reject |
| 37 | Dual listings, ADR arbitrage | 1 | 2 | 2 | 0 | 0 | Reject |
| 38 | Retail-flow proxies (broker "most traded" lists) | 1 | 1 | 1 | 0 | 0 | Reject |
| 39 | Delegation: small-cap managers and LICs in place of stock rules | 2 | 3 | 2 | 1 | 12 | With 59 (LIC idea) |
| 40 | Data quality itself: licensed, survivor-free prices with dividends and index membership | — | 2 | 3 | — | enabler | Already recommended (report 53, BW-04) |

\* 3 only if the ASIC file's share-count column is confirmed; otherwise D = 2, T = 2 (ASX headlines, survivors only).

## 3. The top fifteen in detail

### 3.1 Short interest (rank 1)

- **Why it might matter.** Short sellers are the one group paid only for finding overvalued or failing companies. Heavily shorted stocks earn lower later returns in US data (Diether, Lee and Werner 2009; cited second-hand) [1 here], short interest predicts bad news and negative surprises (Akbas et al., second-hand) [1], and aggregate short interest predicts market returns in 24 of 32 countries including Australia in the sample (Gorbenko, *Review of Asset Pricing Studies* 2023) [2+ listings of one study]. Australian stock-level work exists (a Melbourne working paper; "Down But Not Out") but I saw only listings [1]. Practitioner tests disagree: Livewire found top-ten shorted stocks did badly from July 2022; Firstlinks reports "wavering correlations"; Market Index says the data "does not provide tradable signals" [1 each].
- **Data.** ASIC publishes aggregated short positions per stock per day, four reporting days after the position date; the first report covered 16 June 2010 [1: ASIC media release 10-129AD and Hedgeweek, via search]. Daily files sit at `https://download.asic.gov.au/short-selling/RRyyyymmdd-001-SSDailyAggShortPos.pdf` [1: eight such URLs returned by search]; a `.csv` twin at the same path and the columns "Reported Short Positions", "Total Product in Issue", "% of Total Product in Issue Reported as Short Positions" are from memory [unverified]. ASIC's table page is described as covering 12 months, so older files may need the direct URL pattern [1]. Free. Licence: Commonwealth material; reuse terms to be read on the page [unverified]. ASX also publishes daily gross short sales at `asx.com.au/data/shortsell.txt` (returned a bot-check page here); gross sales are a weaker measure and I would not use them.
- **Honest test?** Yes. Each file was written on its date for the stocks then listed. No vendor has rewritten it. ASIC warns the totals depend on short sellers' own reports [1], so early files contain errors.
- **Expected value.** As a buy signal: none (it is a signal about what to avoid, and a long-only account cannot short). As an exclusion on a 10–30 name book: 0 to 1 point a year, A$0–250 a year at A$25,000 and A$0–1,000 at A$100,000, at no data cost and no extra trades. For the owner-picks panel: a fact worth showing.
- **Recommendation: test now.** Design in section 5, A1.

### 3.2 Net share issuance, capital raisings and buy-backs (rank 2)

- **Why.** The share-issuance effect holds across 41 countries, in small and large firms, driven outside the US mainly by low returns after share creation (McLean, Pontiff and Watanabe 2009, *JFE*) [2+]; a later paper argues it leans on financial firms and equal weighting (Lobe and Walkshäusl 2014) [1]. In Australia, firms issuing seasoned equity underperform for up to five years (Brown, Gallery and Goei 2006) [1]; underperformance is worst for private placements, in a sample of 11,055 placements and 1,828 rights issues [2+]; larger SPP discounts go with worse later performance [1]; rights-issue announcement days average −2.7% to −2.9% over 2000–2022 [1]. Buy-backs: positive announcement returns for on-market programmes 2000–2010 (Gould thesis; Ekanayake 2004) [2+]; no Australian long-run study found [unverified that none exists].
- **Data.** (a) If confirmed, ASIC's daily "total product in issue" gives a dated share count for every stock with a reported short position from June 2010, delisted names included. (b) ASX headline lists: in report 59's harvest so far (121 days, 33,148 headlines), "Appendix 3B / 2A / proposed issue" headlines run at 13 a day, "placement" at 2.4 a day and buy-back notices at 12 a day [computed]. Survivors only, and a headline gives no size. (c) Report 58's stockanalysis share counts: survivors only and restated.
- **Honest test?** With (a), yes from mid-2011. With (b) only, one-sided ("partly tested").
- **Expected value.** The largest of any item here for the 301–1,000 universe that report 59's idea 6 covers, where serial issuers are common. In the top 300, modest: 0 to 1 point a year as an exclusion.
- **Recommendation: test now**, A2. Report 59 covers SPP take-up, which is a different question (should a holder apply), so there is no overlap.

### 3.3 Listing age, IPO seasoning and escrow (rank 3)

- **Why.** Australian IPOs underperform the market in the first year (Dimovski and Brooks 2004, listings 1994–1999) and over three years (Lee, Taylor and Walter 1996) [2+, old samples]; a 2006–2011 sample points the same way [1]. Lock-up expiry is followed by negative abnormal returns in one study whose market I could not confirm [unverified]; no ASX escrow event study was found. Report 51's "NEXTDC-looking" screen (young, fast-rising) lost a median 18% over five years, which is consistent.
- **Data.** First-trade date per code in the price panel, delisted companies included. Free, already held. Weaknesses: the panel starts in 1997, so age is known only for later listings; a code change, relisting or demerger child looks like a new listing. Escrow release dates need prospectuses or "release from escrow" headlines (0.7 a day in the harvest [computed], survivors only).
- **Honest test?** Yes, on the standard 2000–2015 / 2016–2024 split.
- **Expected value.** Small in the top 300 (few names under two years old pass a low-volatility screen). Larger outside it. Mainly a flag for owner picks: "listed 14 months ago; the escrow on 40% of the register ends in March".
- **Recommendation: test now**, A3.

### 3.4 Director trading (rank 4)

- **Why.** Australian evidence exists and is mixed. Outsiders could earn abnormal returns by copying directors' trades, ignoring costs; 13% of trades were reported later than the ASX's five business days (Uylangco, Easton and Faff 2010) [2+ listings]. In 8,053 trades 2002–2006, small trades in small companies carried the largest abnormal returns and, unusually, sales were more informative than purchases [1]. A 2023 working paper finds that after costs only copying sales in large and mid caps pays [1]. So: information is there, mostly in small companies, and which side matters is disputed.
- **Data.** Appendix 3Y PDFs on the ASX announcements platform: free, due within five business days. The headline list gives only "Change of Director's Interest Notice" (22 a day in the harvest [computed]) with no direction, size or reason. Direction and value need the PDF, and most notices are option exercises, plan vestings and dividend reinvestment, not on-market trades. Announcement PDFs were not reachable in report 59's session; the owner's server should be able to fetch them. Market Index publishes a director-transactions table (403 to this session; terms unread).
- **Honest test?** Not backward at reasonable effort: survivors only, 2009 on, tens of thousands of PDFs to parse. Forward: yes.
- **Expected value.** 0 to 1.5 points a year on a small-cap book if the published pre-cost effects half-survive; unknowable until collected.
- **Recommendation: forward-collect**, A5, with a measurement card for clustered on-market buying.

### 3.5 Sector at the time: resources against industrials (rank 5)

- **Why.** Roughly a third of ASX companies by count are miners and explorers [unverified], whose returns depend on commodity prices, drilling outcomes and funding, not on the earnings momentum the anomaly literature describes. One study of junior miners' assay announcements found gains before and during the announcement week and losses afterwards, untradable after spreads [1, market and year not confirmed]. Report 56 could not test industry momentum, and report 53's industry cap uses today's labels. A rule that works in industrials and fails in explorers (or the reverse) is hidden in every pooled result so far.
- **Data.** Needs industry membership at the time, including delisted companies. Not free. Norgate's ASX Platinum rental (A$346.50 for six months before GST, report 19) carries delisted securities and classifications; whether its classifications are historical or current-only must be checked [unverified].
- **Recommendation: park** until the data rental that report 53 already recommends (BW-04 fallback). Then one pre-registered split: H80 inside "resources" and inside "everything else".

### 3.6 Results-day reaction on real dates (rank 6)

- **Why.** Post-earnings-announcement drift is among the best-documented anomalies internationally (report 56, rank 7). Australian work is indirect: drift after bad news is strongest when uncertainty is high (Bird, Choi and Yeung 2011) [1]; attention reduces drift in 2019 data [1]. Australia reports half-yearly, so there are two events a year, which suits a low-turnover book.
- **Data.** Report 59's harvest gives release date and time for Appendix 4E/4D and "half year / full year results" headlines from July 2009: 7.3 a day on average [computed], survivors only. The reaction itself comes from prices. No consensus is needed.
- **Honest test?** Partly: dated, but survivors only.
- **Expected value.** Small. Drift fades over three to six months and the engine reviews yearly. Possible use: one extra input to the December rank.
- **Recommendation: test once**, A4, mainly to close the question report 56 left open with a proxy.

### 3.7 Announcement flow and price-sensitive intensity (rank 7)

- **Why.** Momentum that arrives with public news tends to continue, and price moves without news tend to reverse (Chan 2003) [unverified]; frog-in-the-pan (report 56, the one survivor) is the price-only version of the same idea. The ASX marks announcements price-sensitive: 7,546 of 33,148 headlines in the harvest [computed].
- **Data.** Free, dated, survivors only.
- **Recommendation:** no trial now. Ask report 59 to save the harvest as an event table (code, date, time, headline, price-sensitive flag, type). One later pre-registered test: "H80 names whose 12-month rise came on price-sensitive days" against report 56's noise placebos.

### 3.8 Liquidity, turnover and volume (rank 8)

- **Why.** The small investor's one structural advantage is that A$2,500 fits in stocks no fund can buy. Report 56 could not build turnover, illiquidity or high-volume signals because volume in the panel is not split-adjusted. Trading-friction anomalies replicate worst of all families (Hou, Xue and Zhang, in report 56) [2+], so the prior is modest.
- **Data.** The split and consolidation factors already repaired in report 51 can adjust volume. With ASIC share counts, turnover (volume ÷ shares on issue) also becomes available from 2010.
- **Recommendation: data fix**, then let report 59's idea 6 (neglected small caps) carry the test. No separate trial.

### 3.9 Cash runway and going-concern flags (rank 9)

- **Why.** About 50–60% of microcap Appendix 4C reporters had under a year of cash in the September 2025 quarter and only about 20% had positive operating cash flow (Equitable Investors via Livewire) [1]. Going-concern notes appeared for 68% of resources and energy entities against 37% elsewhere (RSM) [1]. No returns study was found, but a company with two quarters of cash must issue shares, which leads back to 3.2.
- **Data.** Appendix 4C and 5B PDFs: free, quarterly, 7 a day in the harvest [computed]. The figures are in the PDF, not the headline.
- **Honest test?** Backward: no. The companies that ran out of cash are the ones missing.
- **Recommendation: forward-collect**, A5. Irrelevant to the top 300; relevant to owner picks and the 301–1,000 universe.

### 3.10 Seasonality of company events (rank 10)

- **Why.** Stocks earn more in months when they announce earnings (Frazzini and Lamont; international confirmation) [unverified]. Australia has two concentrated reporting seasons, an October–November AGM season with trading updates, and pre-season downgrades. Report 39 tested calendar effects at index level only.
- **Recommendation: park.** One descriptive table from the event table (average excess return by event window, 2009 on) costs no trial if nothing is chosen from it. Any rule would trade twice a year per stock and is unlikely to cover costs at A$2,500 a position.

### 3.11 Dividend changes (rank 11)

- **Why.** Cuts and omissions are followed by negative returns internationally, with the long-run size disputed [1]; one Australian study finds significant post-announcement drift only for interim omissions [1].
- **Data.** The panel has no dividends. Needs the licensed data set (BW-04).
- **Recommendation: park** until then; add "dividend cut in the last 12 months" to the red-flag panel when data arrives.

### 3.12 Trading halts and price queries (rank 12)

- **Why.** A halt "pending a capital raising" is a dated marker of dilution; an ASX price query is a dated marker of an unexplained run. 2.8 halts and 0.6 queries a day in the harvest [computed]. No study found.
- **Recommendation:** tag both in the event table. Use halts to date raisings in A2's fallback. No trial.

### 3.13 Substantial-holder notices and activists (rank 13)

- **Why.** Old Australian studies find 10–13% moves when a substantial holding is announced (Bishop 1991) [1], and that informed holders move in response to performance, not ahead of it (da Silva Rosa, Saverimuttu and Walter 2006) [1]. No study of activist stakes on the ASX was found. Australia has no quarterly fund-holdings filing like the US 13F [unverified], so these notices are the only public view of institutional ownership above 5%.
- **Data.** 22 notices a day in the harvest (becoming 6, change 11, ceasing 5) [computed]. Holder identity and percentages are in the PDF.
- **Recommendation: forward-collect** holder, before and after percentages. Possible later card: "a named small-cap specialist becomes substantial". Low priority.

### 3.14 Takeover-target prediction (rank 14)

- **Why.** Targets earn large premiums, but portfolios of predicted targets generally earn nothing abnormal (Danbolt, Siganos and Tunyi 2016, UK) [1]; one Sydney thesis claims gains on the ASX with tick data [1].
- **Recommendation: park.** One free attribution table is worth having: what share of H80's and of random portfolios' returns came from takeovers, using report 51's delisting reasons (2000–2020). It tells the owner how much "big wins" are in fact bids.

### 3.15 Analysts: coverage, revisions, targets, surprise (rank 15)

- **Why.** Revisions and surprise are strong signals internationally. In Australia the change in a recommendation matters more than its level (Brown, Melbourne) [1]; volume rises before public release, suggesting clients see changes first (Lepone, Wong and Lim) [1]; a consensus-recommendation strategy on the ASX 50 earned nothing after costs (He, Grant and Fabre) [1]. So the edge is front-run and concentrated where coverage exists, the large caps.
- **Data.** No free history. A consensus history costs institutional money (report 57). Snapshots can be taken forward from a feed already paid for; whether the IBKR account or EODHD's fundamentals month (card H95) includes ASX estimates and targets is unconfirmed [unverified].
- **Recommendation: forward-collect only if it comes free with something already bought.** Record analyst count as a "neglect" measure. Do not buy data for it.

## 4. The rest, briefly

| Dimension | Why it is not worth a test now |
|---|---|
| Guidance changes and profit warnings | International studies show −17% to −22% around the warning and some drift afterwards [1]; no ASX study found. A long-only book can only use it as "do not buy within six months of a downgrade". Tag in the event table; add to the red-flag panel |
| Accounting quality | Australian accrual anomaly: supported, significant only in year one (Gaunt et al. 2012) [1]. Asset growth: present (Gray and Johnson 2011) [1], absent when value-weighted (Bettman, Kosev and Sault 2011) [1], mostly micro-caps (Dou, Gallagher and Schneider 2013) [1]. Data is survivor-only and restated, so report 57's card H100 ("closed without a run") applies. Forward only, through 58 |
| Valuation | Same data problem. Forward only, through 58 |
| ETF, index and super flows | Report 39 found no index-level effect from rebalances or super due dates. ETF flows are in the ASX spreadsheets report 59 already downloaded; one descriptive series for 60. No stock-level use |
| Government contracts | AusTender is free [unverified reach]. No evidence of predictability found. Contract-win headlines run at 0.4 a day [computed] |
| Regulation and royalties | Events, not signals: they are risks to holdings. Belongs in the risk register (report 09) and as a dated list in 60 |
| Patents and R&D | IP Australia publishes open data [unverified]. US evidence on R&D intensity; no ASX test possible without dated fundamentals |
| Ownership structure | Founder and insider ownership sit in annual reports. No dated source |
| Governance events | Remuneration strikes are in "Results of Meeting" PDFs. No evidence found |
| China trade, shipping, freight | Report 39: commodities do not lead the ASX at a monthly horizon, and equities if anything lead commodities. Descriptive inputs for 60, not company signals |
| Weather | Fewer than a dozen listed agricultural companies. Not an engine |
| Google Trends | Attention spikes predict short-term rises then reversal in US data [unverified]. The series is re-sampled and re-scaled on every download, so history is not point-in-time. Daily horizon |
| HotCopper | Bullish small stocks outperform in the same days and months (Leung and Ton, 2003–2008, 2,000+ companies, 2.5 million messages) [2+ listings]; a 2023 paper finds little predictive content, with negative sentiment the informative side [1]; a 42-stock informal check of promoted stocks found negative returns beyond one day [1]. Site was blocked here; scraping terms unread. Use, if at all, as a hype flag on owner picks |
| Options-implied | ASX equity options cover only the larger companies [unverified]; history is paid; those are the stocks where the engine has least to add |
| Credit | Few ASX companies have traded bonds. Market-level credit spreads belong in 60 |
| Supply-chain links, US-peer lead–lag | Vendor data unaffordable; the free version is a daily signal |
| Job postings, web traffic, app downloads | Institutional pricing. Reject |
| ESG | No credible return evidence at this scale; paid data. Reject |
| Dual listings and ADRs | No arbitrage for a retail account after costs and currency. Reject |
| Delegation | If the aim is small-cap winners, buying specialist managers through LICs at a discount is an alternative to any rule. Report 59's LIC idea is the test |

## 5. The five actions, with pre-registerable designs

Common rules (to be frozen and hashed before any return is computed, as in `PREREG_59.md`): price panel D1 (`company_study/data/`), ending 2024-05-31; universe = report 51's top 300 by traded value at each formation; price-only returns against XJO price; delisting rule D30 with D0 and D100 as sensitivities; costs as in report 59; engine = `FINAL_RULES_v1.1.md` unchanged. Each idea has two primary trials. **X1 (stand-alone):** equal-weight flagged group minus equal-weight rest of the universe over the next 12 months, monthly formations, Newey–West with 11 lags, December formations as the headline. **X2 (exclusion):** the engine with flagged names skipped and the next-ranked name taken, paired difference against the unfiltered engine, at A$25,000 (10 names) and A$100,000 (30 names). Placebo for X2: 1,000 runs excluding the same number of randomly chosen names from the engine's candidate list. A flag "survives" only if, on unseen data, X1 is negative with t ≤ −2.0, X1 has the same sign on development data with t ≤ −1.5, and X2's paired difference is ≥ 0 and above the 90th percentile of its placebo. "Promising" (signs right, t between −1 and −2) may go on the paper book as a shadow challenger and onto the red-flag panel. Nothing here can change the live engine; that needs the spec's own gates.

Disclosure: the 2016–2024 period has been looked at eight or nine times for H80 (report 55). It is blind for each new flag, not for the engine.

### A1 — Short-interest exclusion (card H110, provisional)

- **Source.** `https://download.asic.gov.au/short-selling/RRyyyymmdd-001-SSDailyAggShortPos.csv` (or `.pdf`), every business day from 2010-06-16; index page `https://asic.gov.au/regulatory-resources/markets/short-selling/short-position-reports-table/`. Record URL, time and SHA-256 per file. First step, before the pre-registration is hashed: download three files (2010, 2017, 2024), confirm the columns, and write them into the pre-registration.
- **Timing.** A position dated d is usable from d + 5 business days (four-day lag plus one).
- **Signal.** SI = reported short positions ÷ total product in issue, averaged over the five most recent usable days to damp reporting errors. Flag = top decile of SI within the top 300 (about 30 names). Stocks absent from the file have SI = 0.
- **Split.** Development: formations 2010-07 to 2016-12. Unseen: 2017-01 to 2023-05 (12-month returns end by 2024-05).
- **Trials.** X1, X2. Secondary, not trials: SI ≥ 5% as an absolute flag; 3-month change in SI; flagged stocks' rate of −50% outcomes and delistings.
- **Expectation, stated in advance.** X1 negative by 2–6 points a year. X2 within ±0.5 points and probably not above its placebo band at 10 names.

### A2 — Dilution exclusion and "shrinkers" (card H111)

- **Source.** The share-count column of the A1 files. Split-adjust with report 51's factor table; any jump within five days of a recorded split or consolidation is reconciled by hand before returns are attached, and logged.
- **Signal.** NI = ln(shares on issue now ÷ shares 12 months earlier), split-adjusted. Flag = top quintile of NI within the top 300. Shrinker = NI ≤ −1%.
- **Split.** Development: 2011-07 to 2016-12. Unseen: 2017-01 to 2023-05.
- **Trials.** X1, X2 for the flag; one stand-alone trial for shrinkers (shrinkers minus rest; sign expected positive).
- **Fallback if the column is absent.** Count of "Appendix 3B / 2A / proposed issue / placement / entitlement / rights" headlines per code over 12 months from report 59's harvest, 2010-07 on, flag = top quintile of the count. Survivors only; verdict limited to "partly tested".
- **Secondary.** The same flag in the 301–1,000 universe of report 59's idea 6, reported for information only.

### A3 — Listing-age exclusion (card H112)

- **Source.** First row of each code in `stage1.pkl`. Codes whose first row is the panel's first month are "seasoned". Demerger children in `niche/code/demergers.csv` are excluded from the flag. Relistings and code changes cannot be identified; this is stated as a limit.
- **Signal.** Flag = fewer than 504 trading days since first trade.
- **Split.** Development: 2000-12 to 2015-12. Unseen: 2016-01 to 2023-05.
- **Trials.** X1, X2. One further trial on 2011 onward: **composite** = excluded if at least one of the A1, A2, A3 flags is set (X2 only). Three flags, one composite, no weights, no thresholds chosen after the fact.

### A4 — Results-day reaction on real dates (card H113)

- **Source.** Report 59's headline lists (`asx.com.au/asx/v2/statistics/announcements.do`, by release date and by code-year), 2009-07 on. Results headline: regex `appendix 4e|appendix 4d|preliminary final|half[- ]?year(ly)? (report|results|accounts)|full[- ]year (results|statutory)`. Event = the first such headline per code per half-year. If the release time is after 16:00, the event day is the next trading day.
- **Signal.** EAR = stock return minus XJO return over event days 0 to +2.
- **Trials.** (1) Stand-alone: top quintile of EAR minus the rest of that season's reporters, from the close of day +3 to day +126, clustered by season. (2) Combination in report 56's format: equal-weight rank of H80 and the most recent EAR at each December formation, against report 56's "H80 + noise" placebos.
- **Split.** Development: seasons 2009-08 to 2016-08. Unseen: 2017-02 to 2023-08.
- **Limit.** Survivors only. Best possible verdict: "partly tested". If trial (1) fails on development data, trial (2) is not run and the idea is closed with report 56's L4.

### A5 — Forward archive and red-flag panel (cards H114–H117, measurement only)

Start now, on the owner's server, inside report 52's knowledge store. Everything is stored with the time it was fetched and never overwritten.

| Item | Source | Cadence | What is kept |
|---|---|---|---|
| Short positions and shares on issue | ASIC daily file | Daily | Whole file |
| Announcement headlines | ASX announcement list by release date | Daily | Code, date, time, headline, price-sensitive flag. From today this includes companies that will later delist |
| Director trades | Appendix 3Y PDFs | Daily | Director, date of change, nature (on-market or other), number, consideration |
| Substantial holders | Forms 603/604/605 | Daily | Holder, previous and present voting power |
| Cash runway | Appendix 4C / 5B | Quarterly | Cash at quarter end, net operating cash flow, estimated quarters of funding |
| Issues and buy-backs | Appendix 3B / 2A / 3C and daily buy-back notices | Daily | Number, price, type |
| Fundamentals | Report 58's database | Monthly dated copy | Whole snapshot, so vintages accumulate |
| Consensus and targets | Only from a feed already licensed | Monthly | Mean estimate, target, analyst count |
| ETF funds under management and flows | ASX Investment Products monthly spreadsheet | Monthly | Whole file |

Licensing: facts extracted from ASX announcements and Commonwealth files for personal research are likely acceptable, but report 52 section 3.4's rules apply and the ASX and ASIC terms must be read before bulk storage of the PDFs themselves [unverified].

Measurement cards (scoreboard lines, no money, no gates): **H114** clustered director buying (two or more directors buying on-market, A$100,000 or more in total, within 30 days, in the top 500): 12-month excess return against the index and against a matched random stock. **H115** cash runway under four quarters: 12-month excess and share that raise capital. **H116** a new substantial holder from a fixed list of small-cap specialists (list written before collection starts). **H117** red-flag count on owner picks: for every pick, the flags set on the day (short interest in the top decile; shares on issue up more than 20% in a year; listed under two years; runway under four quarters; downgrade or halt for a raising in the last six months), and later the outcome by number of flags.

**The red-flag panel** is the practical product. It goes on the monthly "Your picks, honestly" page and on the Big Wins paper list as information only. It needs A5's data, not A1–A4's verdicts; those verdicts decide only whether any flag may become an exclusion on the paper challenger.

**Enabler, already recommended in report 53:** one six-month rental of licensed survivor-free ASX prices with dividends (A$346.50 before GST), with derived results kept. It would let A1–A3 be re-run with dividends and correct splits, and unlock ranks 5 and 11. It is not needed to start.

## 6. What reports 58, 59 and 60 should add now

**58 (company database).**
1. A fetch timestamp on every stored figure, and a dated full copy each month from today. This is the one change that turns a hindsight database into a point-in-time one going forward; it costs disk space only.
2. Shares on issue by period, and 12-month net issuance.
3. First listing date.
4. Total accruals and asset growth, marked "survivors only, restated, not for back-tests" (report 57, H100).
5. For cash-burning companies: cash, operating cash flow, quarters of runway.
6. Analyst count if the source shows it.
7. A reconciliation column against ASIC "total product in issue" once A1's files are down.

**59 (niche edges).** Its pre-registration is hashed; none of this should add or alter a trial.
1. Save the headline harvest as one event table (code, release date, time, headline, price-sensitive flag, pages) with typed flags: 3Y, 603/604/605, 3B/2A, placement, entitlement, SPP, buy-back, halt, price query, 4C/5B, 4E/4D, guidance, CEO/CFO change, auditor, escrow, takeover. A2's fallback, A4 and section 3's descriptive tables all read from it.
2. Extract ETF funds under management and net flows from the ASX Investment Products spreadsheets already downloaded (118 files).
3. In idea 6 (neglected small caps), report the share of each decile listed under two years and, if available, the count of issue headlines, as descriptive columns.
4. State in the report how many harvested codes are missing on each sampled day, by year, so later users know the survivorship rate of the event table.

**60 (drivers).**
1. Aggregate ASX short interest (sum of reported short positions ÷ sum of product in issue, top 200) from the A1 files as a market-level predictor, 2010 on. It is the one driver with published out-of-sample support in 24 of 32 countries [2+ listings of one study] and it is free and dated. One pre-registered monthly test, expected to fail the spec's bar like everything in report 39.
2. A dated list of royalty, tax and policy changes affecting listed sectors (state coal and gas royalties, critical-minerals incentives, bank levies, gaming and childcare regulation), as a risk-register input, not a signal.
3. Exposure betas estimated only on data before each test date, with the estimation window fixed in advance; betas fitted on the full sample would repeat the hindsight problem report 57 describes.
4. China customs volumes by commodity, port stocks and freight indices as descriptive series only, given report 39's finding that commodities do not lead equities monthly.
5. A check of whether GDELT history is point-in-time (its themes and tone are computed by code that has changed) before any news test is believed.

## 7. Trial budget

The programme count will be about 358 after report 59. This report proposes 10 (A1: 2, A2: 3, A3: 3 including the composite, A4: 2), in one pre-registration, giving about 368. The forward cards H114–H117 are measurements and add none. Everything else in section 2 is recorded as "rejected or parked without a run" so it is not re-proposed with new numbers. I recommend that the owner treat this as the last batch of back-tests on the 2000–2024 panel: after it, the remaining honest information is in the forward record.

## 8. Reasons this could be wrong

- **The ASIC file may not carry share counts, may start later than June 2010 in machine-readable form, or may be unreliable in its early years.** Then rank 2 falls to 24 and A2 becomes a survivors-only test.
- **Short interest in Australia is concentrated in large and mid caps** where stock can be borrowed. In the top 300 the flag may simply pick out lithium, retail or whatever sector was crowded in each period, and behave like a sector bet.
- **Exclusion rules may be redundant.** The low-volatility leg of H80 already avoids most lottery stocks (report 56's finding for MAX and beta). Heavily shorted, heavily diluting, newly listed stocks are mostly high-volatility stocks.
- **Fourteen years of short data is six or seven yearly cohorts per half.** The stand-alone tests have breadth; the exclusion tests do not.
- **My ranking is judgement.** A reader who weights evidence above data would put analyst revisions and results surprise higher; I have put them low because the history cannot be bought and the horizon is short.
- **Australian studies cited are mostly old and were read as abstracts.** Effects documented on 1990s and 2000s samples may have decayed.
- **A forward archive only pays off if it is kept running for years.** If the server is switched off, the collected history has gaps that cannot be filled.
- **None of this addresses the central result.** Reports 51 and 53 found that the index, which holds every future winner, beat every stock rule at this size after tax. Better avoidance of losers narrows that gap; it does not obviously close it.

## 9. Files and sources

Read in the scratchpad: `onedrive/research2/` reports 31, 39, 51, 53, 55, 56, 57 (answers, caveats, section lists); `niche/PREREG_59.md`; `niche/raw/annday/` (121 daily headline pages, 2009-10-07 to 2026-10-06, counted with a short script; no returns attached); directory listings of `company_db/` and `niche/`.

Reached directly on 14 November 2026: `www.asx.com.au/asx/v2/statistics/announcements.do` (200), `www.rba.gov.au/statistics/tables/` (200). Not reachable: see section 0.1.

Known through search summaries only:

- Short selling: https://asic.gov.au/short-position-reports · https://asic.gov.au/regulatory-resources/markets/short-selling/short-position-reports-table/ · https://asic.gov.au/about-asic/news-centre/find-a-media-release/2010-releases/10-129ad-asic-starts-reporting-of-short-positions/ · https://www.hedgeweek.com/asic-starts-reporting-short-positions/ · https://download.asic.gov.au/short-selling/RR20231227-001-SSDailyAggShortPos.pdf · https://www.livewiremarkets.com/wires/guilty-until-proven-innocent-how-we-treat-the-asx-s-most-shorted · https://www.firstlinks.com.au/article/ignore-the-rise-of-short-selling-at-your-peril · https://marketindex.com.au/short-selling · https://econpapers.repec.org/RePEc:oup:rasset:v:13:y:2023:i:4:p:691-733. · https://hal-audencia.archives-ouvertes.fr/hal-01964596
- Issuance and raisings: https://econpapers.repec.org/RePEc:eee:jfinec:v:94:y:2009:i:1:p:1-17 · https://www.econbiz.de/Record/does-market-misvaluation-help-explain-share-market-long-run-underperformance-following-a-seasoned-equity-issue-brown-philip/10005203383 · https://opus.lib.uts.edu.au/bitstream/10453/85369/2/JAS2016N002_006.pdf · https://ideas.repec.org/a/bla/acctfi/v64y2024i2p1311-1333.html · https://ideas.repec.org/a/bla/acctfi/v57y2017i3p907-933.html
- Buy-backs: https://eres.library.adelaide.edu.au/dspace/handle/2440/98155 · https://dro.deakin.edu.au/articles/journal_contribution/Information_signalling_of_common_stock_repurchase_announcements_Australian_evidence/20534652
- IPOs and escrow: https://www.econbiz.de/Record/initial-public-offerings-in-australia-1994-to-1999-recent-evidence-of-underpricing-and-underperformance/10005673933 · https://vuir.vu.edu.au/25676/ · https://www.emerald.com/insight/content/doi/10.1108/03074350410768859/full/html
- Director trading: https://ideas.repec.org/a/eme/arjpps/v23y2010i1p5-19.html · https://core.ac.uk/download/201345742.pdf · https://virtusinterpress.org/ARE-INSIDER-TRADES-PROFITABLE.html · https://doaj.org/article/31db1ad7063d42e2ac9f66e89bbbb192
- Substantial holders and takeovers: https://econpapers.repec.org/RePEc:sae:ausman:v:16:y:1991:i:1:p:1-33 · https://ideas.repec.org/a/bla/irvfin/v5y2005i3-4p113-147.html · https://www.austlii.edu.au/au/journals/SydLawRw/2015/2.html · https://eprints.whiterose.ac.uk/107571/ · https://ses.library.usyd.edu.au/handle/2123/9724
- Earnings drift, warnings, dividends: https://opus.lib.uts.edu.au/handle/10453/19406 · https://econpapers.repec.org/RePEc:bla:finrev:v:38:y:2003:i:4:p:497-513 · https://bridges.monash.edu/articles/Over_Under_Reactions_to_Dividend_Reductions_in_Long_Term_Returns/5090398/1
- Analysts: https://researchers.mq.edu.au/en/publications/economic-value-of-analyst-recommendations-in-australia-an-applica/ · https://ses.library.usyd.edu.au/handle/2123/4077
- Accounting anomalies: https://econpapers.repec.org/RePEc:eee:jbfina:v:35:y:2011:i:3:p:670-680 · https://ideas.repec.org/a/sae/ausman/v38y2013i2p353-373.html · https://opus.lib.uts.edu.au/handle/10453/18847
- Cash runway and going concern: https://www.livewiremarkets.com/wires/the-great-microcap-divide-4c-data-reveals · https://www.rsm.global/australia/insights/what-asx-resources-and-energy-disclosures-reveal
- Message boards: https://researchers.mq.edu.au/en/publications/the-impact-of-internet-stock-message-boards-on-cross-sectional-re/ · https://sbfc.sydney.edu.au/2023/papers/SBFC2023_6F1.pdf · https://www.thesentiment.com.au/do-hotcoppers-marketing-emails-influence-a-stock-price
- Mining announcements: https://www.sciencegate.app/document/10.1177/0148558x9300800309
