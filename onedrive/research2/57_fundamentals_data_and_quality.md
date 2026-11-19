# 57 — Company fundamentals without hindsight, and whether quality + momentum is worth it on the ASX

Date: 2026-11-14. Status: desk research plus two small calculations on public factor files. No strategy was run on ASX company data; no trial was spent. Research use only; general information, not financial advice.
Working files (vendor pages as downloaded, factsheets, factor files, scripts): `scratchpad/r57/` (section 9). Builds on reports 19, 51, 53, 54 and 55.

Evidence tags: **[2+]** two or more independent sources, or a primary source plus my own calculation from primary data; **[1]** one source (a primary page I read directly is marked "primary"); **[unverified]** not confirmed in this session.
Exchange rate used throughout: A$1.543 per US$1, the rate implied by report 53's "US$19.99 a month ≈ A$370 a year". Vendor prices are in US dollars and move with the rate.

## 0. Answer first

**A personal investor cannot buy a hindsight-free history of ASX company fundamentals that includes the companies that later delisted. The data exists (Morningstar/SIRCA, LSEG, FactSet, S&P, Bloomberg) but is sold to institutions and universities at roughly A$18,000–50,000 a year, or is barred to individuals. The one affordable vendor, EODHD, states in its own documentation that it keeps only the current version of each figure and has fundamentals only for companies delisted after 2018. So an honest ASX back-test of quality + momentum from 2001 is not obtainable at this budget. The published evidence for quality in Australia is real but modest and has weakened since 2013; it would not be provable on a 10–30 stock paper book in the owner's lifetime. The cost is not justified at A$5,000–25,000. If the owner wants the exposure, an ETF gives it for about A$78 a year extra per A$25,000, and tracking the ETFs on paper costs nothing.**

| Question | Answer | Where |
|---|---|---|
| Is there a point-in-time ASX fundamentals history, with delisted companies, for an individual? | No. Not at any price near the current budget | Section 1 |
| What does EODHD's fundamentals feed give? | Statements for non-US companies "from 2000", but "minor companies have the last 6 years"; each report carries a `filing_date`; **no vintages** ("We provide only the current version of the data"); delisted companies: "Before 2018: EOD only". US$59.99 a month (≈ A$93), sold separately from the price plan the spec already buys [1, primary] | Section 1.1 |
| What would the real thing cost? | LSEG Worldscope point-in-time, FactSet, S&P Capital IQ: about US$12,000–30,000 a seat a year (third-party estimates; vendors quote privately) [1]. Bloomberg about US$32,000 [1]. SIRCA and Morningstar DatAnalysis: through universities and libraries only | Section 1.2 |
| Does quality/profitability work in Australia? | On paper, long–short, before costs: yes over 30 years (AQR's Australian quality factor +4.3% a year, t = 2.4), weaker since 2013 (+2.6%, t = 0.9) [2+, my calculation from AQR's file]. Australian papers: profitability matters in raw returns, mostly in very small companies, and does not survive strict data-mining tests [2+] | Section 2 |
| Does adding quality to momentum help? | Globally yes on paper; the two are nearly uncorrelated in Australia (0.18). But Australian momentum itself earned +10.8% a year long–short on paper in 2016–May 2024, the same years in which the Big Wins engine did not beat the index after costs. Paper factor returns have not carried over to a small long-only book here | Sections 2.2, 2.5 |
| Do the ETFs beat the index after fees? | Mixed. AQLT (quality, 0.35%) is 4.8 points a year ahead of the S&P/ASX 200 since April 2022. MTUM (momentum, 0.35%) is 3.9 points a year behind since July 2024. AUMF (multi-factor, 0.30%) is level over 2021–2025. A second Australian quality index (MSCI) underperformed [2+ for AQLT and MTUM, primary factsheets] | Section 3 |
| Cheapest credible path to a quality + momentum engine | Forward only: add one month of EODHD fundamentals twice a year, after each reporting season, and keep dated copies. About A$185 a year on top of the planned A$370. Its history starts the day the first copy is taken; there is no back-test | Section 4 |
| Is it worth it at this account size? | No. Data would cost 2.2% a year of a A$25,000 slice against a plausible edge of 0 to 1.5 points that cannot be shown in under about 35 years | Section 4.3 |
| Recommended now | (1) Spend nothing: add AQLT, MTUM, AQTY and a 50/50 AQLT + MTUM mix to the monthly paper scoreboard (card H97). (2) Optional, once, about A$93: test what EODHD's ASX fundamentals really contain (card H95). (3) Leave the quality + momentum engine as a parked card (H96) until the audit passes and the owner chooses to pay for the snapshots | Sections 4, 6 |

What this means, in one paragraph. Report 51 left fundamentals out because the only data to hand was survivors-only and restated. That was the right call, and this report finds that it cannot be fixed cheaply: the missing piece is not a better website, it is a database product that retail vendors do not sell for Australia. The academic studies that did have proper data (they used the university databases) say profitable, soundly financed companies have done somewhat better in Australia, mainly among small companies and mainly before costs, and that under strict tests only the market factor survives. The live ETFs say the same thing in a different way: one quality fund is well ahead, one momentum fund is behind, one multi-factor fund is level, and which design wins is not predictable in advance. None of that justifies paying several hundred to several thousand dollars a year for data on an account of this size.

## 0.1 Caveats

- **Reach.** Read directly through the session proxy: eodhd.com, norgatedata.com, asx.com.au, betashares.com.au (PDF factsheets only), vaneck.com.au, quantconnect.com, aqr.com, the Ken French data library, ideas.repec.org. **Blocked** (claims rest on search summaries and are tagged down): sirca.org.au, lseg.com, factset.com, spglobal.com, wrds, simfin.com, financialmodelingprep.com, stockopedia.com, marketindex.com.au, data.nasdaq.com, portfolio123.com, blackrock.com, dimensional.com, sl.nsw.gov.au, the university library guides, ssrn.com, wiley.com, sciencedirect.com.
- **No EODHD key in this session.** What EODHD's ASX fundamentals actually contain (how many delisted companies, how far back, how accurate) was not tested; only the vendor's own description was read. The demo key does not serve ASX symbols. Card H95 is that test.
- **Institutional prices are third-party estimates.** LSEG, FactSet and S&P do not publish prices. The figures are from comparison sites and should be read as "tens of thousands of dollars", not as quotes.
- **Paper factor returns are not investable returns.** The AQR and French figures are long–short, before all costs, include very small companies, and are in US dollars. They show whether an effect exists, not what a 30-stock long-only account would earn.
- **ETF records are short.** AQLT has 4.6 years of live history, MTUM 2.3 years, AQTY five months. Index histories before each fund's launch are back-tests chosen by the issuer.
- **Issuer research is marketing.** The VanEck paper criticising single-factor quality was published two months before VanEck launched a competing "quality plus" fund; the Betashares pieces promote AQLT.
- **Academic papers were read as abstracts only**, except where stated. Country-level tables (for example Australia's row in the quality-minus-junk paper) were not seen; I computed Australia's figures from AQR's published data file instead.

## 1. Data sources

### 1.1 What "point-in-time" needs, and what EODHD says it has

A back-test without hindsight needs four things: (a) every company that existed at each date, including those later delisted; (b) the figures as first reported, not as later restated; (c) the date each figure became public; (d) prices for the same companies. Report 51 had (d) only.

EODHD's own documentation, read directly [1, primary; pages saved in `r57/dl/`]:

| Item | EODHD's statement | Source |
|---|---|---|
| Plans | "EOD Historical … All-World $19.99/mo, $199.00/year"; "Fundamentals Data Feed $59.99/mo, $599.90/year"; "ALL-IN-ONE $99.99/mo, $999.90/year". "No long-term commitments, just a minimum of one month" | eodhd.com/pricing |
| Fundamentals plan excludes prices | "Company fundamentals, financial statements, calendar data …; does not include end-of-day prices". Plans can be combined on one key | eodhd.com/help/plans |
| History depth | "Major US companies are covered from 1985 …; non-US symbols from 2000 (25+ years) … Minor companies have the last 6 years and 20 quarters" | Fundamentals API page |
| Report dates | "Each yearly and quarterly report entry carries its own date and filing_date" | Fundamentals API page |
| Vintages | "Is the data versioned? Can I get the values as they were known on a past date (point-in-time vintages)? **No. We provide only the current version of the data.** A correction overwrites the existing record, and change timestamps are not stored. To reproduce what was available on a given date, keep dated snapshots of your downloads" | eodhd.com/help/methodology |
| Delisted companies | "Delisted … After 2018: EOD, Fundamentals, Dividends and Splits … **Before 2018: EOD only**" | Delisted data page |
| Delisted, non-US | "42,000+ non-US tickers (mostly within the latest 6–7 years)" | EODHD FAQ, delisted prices |
| No guarantee | "Coverage varies by ticker and may contain gaps or end before the last trading day … Fundamentals may also be available, depending on the ticker" | eodhd.com/help/methodology |
| Bulk download | Needs a separate "Extended Fundamentals" plan, price on request, and returns only "the last 4 quarters and last 4 years". Single-company requests cost 10 calls each against 100,000 a day, so about 2,500 ASX codes fit in one day without it | Bulk Fundamentals page; pricing page |
| Licence | Data may be kept after cancelling ("no deletion requirement and no deadline"); private back-testing and paper trading are personal use "as long as the data and results are not provided to anyone else"; sending data to a hosted AI service through the owner's own account is allowed; one person only | help/storage, help/personal-use, help/ai-tools |

Reading. Against the four needs: (a) fails before about 2018–2019; (b) fails (current values only); (c) partly met (`filing_date`, accuracy for ASX [unverified]); (d) met for survivors, and for delisted companies "mostly within the latest 6–7 years" — which also bears on report 53's open question BW-05 about delisted price history. The most EODHD can support is a back-test from about 2019, on restated figures, with unknown gaps. Seven years, half of them already inside every earlier report's "unseen" window, is not a test.

The useful line is EODHD's own advice: keep dated snapshots. A copy of the fundamentals taken today is, from today, a true point-in-time record. That is the basis of section 4.

### 1.2 All sources compared

Costs per year in Australian dollars at A$1.543 per US$1. "PIT" = as-first-reported values with the date they became known.

| Rank | Source | ASX coverage | PIT quality | Delisted | Price a year | Licence (personal use, keeping data, AI) | Access route | Tag |
|---|---|---|---|---|---|---|---|---|
| 1 | **Own snapshots of EODHD fundamentals, taken forward** | About 2,000 ASX codes claimed | True PIT from the first snapshot onward; nothing before | Captured as they happen | About A$185 (two single months at US$59.99) on top of the price plan | Keep forever; private use; AI tools allowed; no sharing of data or results | Self-serve, card payment | [1, primary] for terms and prices; data quality [unverified] |
| 2 | EODHD fundamentals, one-off history | Statements from 2000 for larger companies; "last 6 years" for minor ones | Not PIT. Current values; `filing_date` present | Fundamentals only for delistings after 2018 | A$93 once (one month); A$926 on the annual plan; A$1,543 for All-in-One | As above | Self-serve | [1, primary] |
| 3 | Morningstar DatAnalysis Premium | All ASX companies; financials from annual reports back to 1990; interim and delisted data from 1996; daily prices from 2000 | Annual-report figures as lodged, with the announcements attached; not a time-stamped quant feed [unverified] | Yes, "companies delisted since 1990" | No individual price found. Institutional subscription | Library and university licences are for study and research by members; bulk extraction for a private trading system is not what they license [unverified] | University libraries; State Library of NSW lists it (on-site or remote [unverified]) | [2+] for coverage (several library guides; a 2012 Morningstar brochure); [unverified] for terms |
| 4 | SIRCA (Morningstar fundamentals, ASX announcements, prices) | The Australian academic standard; what most of the papers in section 2 used | Good | Yes | Not sold to individuals | Access "part of your existing membership"; registration is by invitation through a university's SIRCA representative | Staff and research students of member universities | [1] (SIRCA's FAQ and a University of Melbourne page, via search; sirca.org.au blocked). No individual, alumni or paid public route found |
| 5 | LSEG Worldscope point-in-time / Datastream | Global, about 90,000 companies, "dating back to 1983, timestamped to the day" | The real thing | Yes | About US$12,000–24,000 a seat (A$18,500–37,000), estimate | Enterprise contract | LSEG sales; some universities | [1] |
| 6 | FactSet Fundamentals (point-in-time version exists) | Global; about 22,900 Asia-Pacific companies; non-US interim data from 2001 | Good in the PIT product | Yes | About US$12,000–24,000 a seat, estimate | Enterprise contract | FactSet sales | [1] |
| 7 | S&P Capital IQ / Compustat Global | Global annual data from 1987; the point-in-time "Snapshot" history is North America only; inactive companies may be dropped from some files | Not PIT for Australia [1] | Partly | About US$13,000–30,000 a seat, estimate; WRDS is university-only | Enterprise or university | S&P sales; WRDS | [1] |
| 8 | Bloomberg terminal | Global | Good, with care | Yes | About US$32,000 (A$49,000), two-year minimum | Terminal licence; no bulk export for systems | Bloomberg sales | [1] (several sites agree on the figure) |
| 9 | Norgate Data (ASX Platinum) | Prices: all ASX including delisted from 1992 | **Current fundamentals only**: "the last-reported (current) fundamentals only (historical data is not available)", supplied by FactSet | Prices yes; fundamentals no | A$346.50 for six months, A$630 for twelve, before GST | Personal use; any tool including hosted services; exported data **must be deleted** at expiry; derived results may be kept; Windows updater | Self-serve | [1, primary] (norgatedata.com) |
| 10 | Financial Modeling Prep | Claims 70,000+ securities; non-US coverage only on the top plan | PIT handling for ASX not documented | [unverified] | Top plan about US$139–149 a month (A$2,600–2,750 a year); sources disagree | [unverified] | Self-serve | [1], weak |
| 11 | Stockopedia (Australasia) | About 2,500 ASX and NZX reports; data from Refinitiv (LSEG); ready-made quality, value and momentum ranks | Screens and ranks, not a history. Old weekly reports as PDFs; table export limited to about 50 rows | n/a | A$575 (promotional page; another page shows A$1,150) | Personal viewing | Self-serve | [1] |
| 12 | ASX announcements (Appendix 4D and 4E, annual reports) | Every listed company; the legal source of record | Perfect: the document as lodged, with its release time | Past announcements of delisted companies on asx.com.au [unverified] | Free | "Market Announcements are freely available for investors' private and personal use only"; site content may be saved "for your own information purposes only, including research, study or other personal, non-commercial use" and not otherwise copied or downloaded | Browser, one document at a time. PDFs, not data. The spec already bars scraping asx.com.au | [1, primary] (ASX terms of use) |
| — | Sharadar; SimFin; QuantConnect's Morningstar feed; Portfolio123 | **No ASX.** Sharadar: US companies. QuantConnect: "8,000 US Equities", as originally reported, from 1998. Portfolio123: North America and Europe. SimFin: US focus | Good for the US | Yes for the US | n/a | n/a | n/a | QuantConnect [1, primary]; others [1] |
| — | Interactive Brokers fundamentals | Was LSEG (Reuters) data through the API | Current only | No | Free with account | The January 2026 Web API change log lists fundamental data tags as "deprecated and no longer available via API" | n/a | [1] |
| — | Market Index, Simply Wall St, other free sites | Current figures for listed companies, licensed from Morningstar and others | None | No | Free | Terms not read; licensed display data, not for harvesting [unverified] | Browser | [unverified] |

Two facts decide the ranking. First, Appendix 4D and 4E must be lodged within two months of period end [2+: ASX compliance updates; BDO], so a fixed lag (use figures no earlier than four months after the period end) removes the reporting-date problem without any vendor's dates. Restatement is a second-order problem for annual figures. Second, the problem no lag can fix is the missing companies: a back-test on survivors' fundamentals flatters every rule, because a holding that later failed is simply absent and its loss is never charged. It also makes a quality rule untestable: the claim for quality is that it avoids the companies that fail, and that claim can only be checked on data that contains them. No source ranked 1, 2, 9, 10, 11 or below has the dead companies' fundamentals before 2018.

University access, plainly. SIRCA and DatAnalysis are reached by being a current staff member or enrolled research student at a subscribing university. I found no alumni, public or paid individual route [1]. Enrolling in a degree to obtain data would put the data under an academic-research licence, not a personal-investing one [unverified]. A State Library of NSW card may allow DatAnalysis look-ups; that is enough to check a sample of EODHD's figures by hand (card H95) but not to build a database.

## 2. Evidence

### 2.1 What the original papers claim

- **Gross profitability** (Novy-Marx 2013, Journal of Financial Economics): gross profit ÷ assets predicts returns about as well as book-to-market, and is negatively correlated with value, so the two combine well [2+].
- **Quality minus junk** (Asness, Frazzini, Pedersen; Review of Accounting Studies): a composite of profitability, growth and safety earns significant risk-adjusted returns in the US and across 24 developed markets; positive in 23 of the 24 [1].
- **Fama–French five-factor model** (2015; international tests 2017): in North America, Europe and Asia Pacific (Australia, New Zealand, Hong Kong, Singapore) average returns rise with profitability and fall with investment; Japan shows little [2+].
- **Piotroski F-score**: in developed non-US markets 2000–2018, high-score companies beat low-score ones by about 10% a year (Walkshäusl 2020, abstract read) [1].
- **After publication**: across 97 US predictors, returns were 26% lower out of sample and 58% lower after publication (McLean and Pontiff 2016) [2+]. Across 241 anomalies in 39 markets, the United States was the only country with a reliable post-publication decline (Jacobs and Müller 2020) [2+]. So decay is established in the US and not established elsewhere; "not established" is not "absent".
- **Quality with momentum**: Novy-Marx's follow-up work reports that investors in value and profitability "can realize significant improvements by also incorporating momentum" [1]. Gray and Vogel's *Quantitative Momentum* adds a smoothness-of-path filter to momentum; the fund built on it (QMOM, US) has a mixed record against its benchmark, ahead in some five-year windows and behind in others [1]. Report 56's lab already tests that path filter on prices (candidate L3).

### 2.2 Australia in the published factor files (my calculation)

Monthly long–short factor returns, percent a year, with t-statistics. Source files: AQR "Quality Minus Junk Factors Monthly" and "Betting Against Beta" (data to August 2026) and Ken French's "Asia Pacific ex Japan 5 Factors" and momentum factor (to September 2026). Script: `r57/aqr.py`, `r57/ff.py`. [2+: primary data, computed here.]

| Factor | Whole history | To Dec 2012 | Jan 2013 on | Jan 2016 – May 2024 |
|---|---|---|---|---|
| AQR quality (QMJ), **Australia**, from Jul 1996 | +4.3 (t 2.4) | +5.8 (2.4) | **+2.6 (0.9)** | +2.5 (0.8) |
| AQR quality, global, from Jul 1989 | +4.8 (3.8) | +5.5 (3.5) | +3.7 (1.8) | +4.8 (1.8) |
| AQR quality, United States, from 1957 | +3.9 (4.0) | +4.2 (4.2) | +2.8 (1.0) | +4.2 (1.2) |
| French profitability (RMW), Asia Pacific ex Japan, from Jul 1990 | +3.9 (2.7) | +3.5 (1.6) | **+4.8 (2.5)** | +7.4 (3.2) |
| AQR momentum (UMD), Australia, from Nov 1986 | +18.0 (7.7) | +18.6 (6.2) | +16.7 (4.6) | +10.8 (2.6) |
| French momentum (WML), Asia Pacific ex Japan | +10.3 (4.3) | +8.7 (2.5) | +12.9 (4.5) | +7.6 (2.2) |
| AQR value (HML), Australia, from Jul 1990 | +9.5 (5.3) | +9.4 (4.6) | +9.5 (2.9) | +13.2 (3.1) |
| AQR low beta (BAB), Australia, from Dec 1988 | +14.3 (5.9) | +18.2 (5.4) | +7.5 (2.5) | +7.4 (1.9) |
| 50/50 Australian quality + momentum (AQR) | +11.4 (6.5) | — | +9.7 (3.8) | +6.6 (2.1) |

Correlation of Australian quality with Australian momentum: 0.18; with value: −0.14.

Reading.

1. Australian quality is positive over 30 years at about 4 points a year, with a t-statistic near 2.4 — below the t ≥ 3 bar the spec uses for return claims — and since the papers were published it is +2.6 with t under 1. Calendar 2025 was −24.6%; 2023 and 2024 were +7.9% and +12.5%. It is not a steady premium.
2. The two files disagree about the last decade. French's profitability factor for the region is stronger after 2013; AQR's broader quality composite for Australia is weaker. They differ in definition (profitability alone against profitability, growth and safety), in countries, and in weighting. An effect whose sign-of-change depends on the definition is not one to pay for.
3. The row that matters most for this project is momentum. On paper, long–short, Australian momentum earned +10.8% a year in January 2016 – May 2024. In the same window the Big Wins engine, a long-only, top-300, after-cost momentum-family rule, earned 1.6–4.3% against the index's 4.6% (reports 53 and 55). The paper premium sits largely in small companies and in the short side. A long-only book of 10 to 30 large companies does not collect it. There is no reason to expect quality, a premium a quarter the size, to transfer better.

### 2.3 Australian studies

| Study | Data | Finding | Tag |
|---|---|---|---|
| Zhong, Limkriangkrai and Gray (2014), *International Review of Financial Analysis* 35 | Australian companies | Raw-return anomalies exist for size, momentum, book-to-market and **profitability**; "after adjusting for exposure to risk, convincing evidence only remains for the size premium"; anomaly returns are concentrated in a few months of the year | [1, abstract read] |
| Dou, Gallagher and Schneider (2013), *Australian Journal of Management* 38(2) | Australian companies split into micro, small and big | None of eight anomalies is pervasive across sizes. Size, value, **profitability**, asset growth and accruals are "primarily attributable to micro-cap stocks". **Momentum and asset growth** predict the returns of big companies | [2+, abstract in several repositories] |
| Chiah, Chai, Zhong and Li (2016), *International Review of Finance* | 1982–2013 | The five-factor model explains more Australian anomalies than its rivals; value keeps its power alongside profitability and investment | [2+, abstract and secondary summary] |
| Chai, Chiah and Gharghori (2019), *Pacific-Basin Finance Journal* 55 | Largest 300–500 Australian companies, 35 years | Five-factor model is best for large companies; "profitability and investment factors help to explain the cross-section" | [1, abstract read] |
| "Choosing factors: Australian evidence" (2019), *Pacific-Basin Finance Journal* 58 | Australian companies | All five factors and momentum are useful in pricing Australian shares | [1, abstract read] |
| **Hoang, Cannavan, Gaunt and Huang (2019)**, *Pacific-Basin Finance Journal* 57 | 91 factors, 1992–2017 | Allowing for data mining, "the market factor is the only factor in the Australian market that consistently survives"; robust to excluding small companies | [1, abstract read] |
| Hyde (2018), *Accounting & Finance* 58(2) | S&P/ASX 200 and smaller | Long high F-score, short low: 0.8% a month in the ASX 200, 1.4% in smaller companies. But four-factor alphas are significant only for equal-weighted small companies, where "most of the alpha comes from the short side" and capacity is too small for institutions | [1, abstract read] |
| "Characteristics versus covariance …: Australian evidence" (2024), *Accounting & Finance* 64(4) | Australian companies | Size, book-to-market, profitability and investment characteristics explain return differences beyond factor loadings; pure-characteristic portfolios "generate economically significant trading profits" (before costs) | [1, abstract read] |
| 52-week-high momentum in Australia (ANU-listed study) | Australian companies | Among liquid companies the strategy "fails to produce significant dollar profits once short-sale restrictions, transaction costs and liquidity constraints are accounted for" | [1, search summary] |
| Earnings announcement drift in Australia (Taylor and Tong 2020; Bird, Choi and Yeung 2014; others) | Half-yearly results | Drift exists and varies with sentiment and with the kind of news. No Australian study of analyst-revision momentum was found | [1, search summary] |

Not found: any published Australian test of quality combined with momentum in large companies after costs. Earnings revisions and surprises need a history of analyst forecasts (I/B/E/S, FactSet), which is institutional; EODHD's earnings-surprise fields for ASX companies are [unverified].

Taken together. The Australian literature says three things consistently: profitability and investment carry information about returns; the effect is strongest where an individual with A$1,000 orders could in principle trade but where spreads are widest and delistings most common; and in the large companies the Big Wins engine uses, momentum is the anomaly with the best support, which is the one the engine already has. Under a strict multiple-testing standard — the standard this project applies to itself — nothing but the market survives.

### 2.4 Issuer research on Australia

- VanEck, "The limits of quality in Australia" (April 2026) [1, primary, read in full]: of the two Australian quality indices, the Solactive one (AQLT's) "has outperformed but has not been consistent on a risk-adjusted basis", and the MSCI Australia IMI Quality index "has underperformed" the S&P/ASX 200 over December 2010 – March 2026. Neither fell less than the market in the 2018, 2024 or 2025 sell-offs. Over April 2022 – March 2026 the Solactive index had a market beta of 1.14 and a growth tilt. VanEck's explanation: the top ten companies are about half the index, sectors are concentrated, and the starting universe is small. Two months later VanEck launched AQTY, which adds value, low volatility and momentum to quality.
- Betashares [1, search summary]: the largest 11 companies are close to half the S&P/ASX 200; a standard S&P/ASX quality index's excess returns were "more correlated with the size factor than with the quality factor itself", which is why AQLT splits its weight between large and smaller companies.

Both issuers agree on the fact that matters: in Australia a simple quality screen mostly re-weights banks, miners, CSL and Wesfarmers, and its result is driven by those few weights.

### 2.5 What the evidence supports

- Quality exists as a paper effect in Australia, at roughly half the strength needed to pass this project's own bar, and weaker since publication on one of two measures.
- It combines well with momentum on paper because the two are almost uncorrelated.
- It is concentrated where costs are highest; in large companies the support is thin.
- The one direct Australian comparison of two quality index designs split one each way.
- Nothing here shows that a 10–30 stock, long-only, after-cost, after-tax account would beat A200 by adding quality. Nothing shows it would not. The data that could settle it for the past is not available to the owner, and the forward record cannot settle it in useful time (section 4.3).

## 3. The cheaper proxy: ETFs

Fund returns after fees, from the issuers' factsheets dated 30 October 2026 [1, primary; AQLT, MTUM and A200 PDFs read directly]. Benchmark column is the S&P/ASX 200 as printed on the same factsheet.

| Fund | What it holds | Fee a year | Fund start | Since start, fund | Since start, S&P/ASX 200 | 1 year, fund / index | Tag |
|---|---|---|---|---|---|---|---|
| **AQLT** Betashares Australian Quality | 40 companies by return on equity, low leverage, earnings stability (Solactive index) | 0.35% | 4 Apr 2022 | **12.49%** a year | 7.69% | 9.69% / 3.69% | [1, primary] |
| **MTUM** Betashares Australian Momentum | 90 companies by risk-adjusted momentum (Solactive index) | 0.35% | 22 Jul 2024 | **5.04%** a year | 8.93% | −7.84% / 3.69% | [1, primary] |
| **AQTY** VanEck Australian Quality Plus | About 50 companies: quality with value, low volatility and momentum (MSCI index) | 0.35% | 29 May 2026 | no record yet | — | — | [1, primary] |
| **AUMF** iShares Edge MSCI Australia Multifactor | Value, momentum, quality, size | 0.30% | 14 Oct 2016 | see below | | | [1, search summary of BlackRock page] |
| **DACE** Dimensional Australian Core Equity (active ETF) | Whole market tilted to smaller, cheaper, more profitable companies [tilt unverified] | 0.28% | Listed Nov 2023 | not obtained | | | [1] |
| A200 Betashares Australia 200 | Largest 200 by size | 0.04% | 7 May 2018 | 8.74% a year | — | 3.95% | [1, primary] |
| QUAL VanEck MSCI International Quality | **Not Australian**: 300 companies from the world outside Australia | not read | 29 Oct 2014 | index ahead of its parent by 3.12% a year over Dec 1994 – Mar 2026 (includes back-tested years) | | | [1, primary, VanEck paper] |

Calendar years, percent:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 to Oct |
|---|---|---|---|---|---|---|---|---|
| AQLT fund | — | — | — | — | 17.42 | 23.30 | 12.97 | 12.28 |
| AQLT index (back-test before Apr 2022) | 28.55 | 6.61 | 20.71 | **−11.94** | 17.90 | 23.86 | 13.42 | 12.56 |
| MTUM fund | — | — | — | — | — | — | 10.10 | **−5.18** |
| MTUM index (back-test before Jul 2024) | 25.75 | 15.82 | 15.35 | −6.03 | 9.00 | 19.24 | 10.31 | −4.94 |
| AUMF fund | | | 11.33 | −0.95 | 9.45 | 13.75 | 18.15 | |
| A200 index | 23.33 | 1.27 | 18.08 | −0.73 | 12.44 | 11.55 | 10.33 | 5.38 |

Reading.

- **AQLT has beaten the index after fees in each of 2023, 2024, 2025 and 2026 to October**, by 5.0, 11.8, 2.6 and 6.9 points against the A200 index, and by 4.8 points a year against the S&P/ASX 200 since launch. That is a strong 4.6 years. Against it: the launch followed a back-test; the index lost 11 points to the market in 2022, the year the fund started; its beta has been above 1 in a rising market; and the other Australian quality index did the opposite. With yearly gaps this uneven, 4.6 years gives a t-statistic of roughly 1.5 to 2 [my estimate from the yearly gaps, not from monthly data].
- **MTUM is the cautionary case.** Its index showed 2.3–2.8 points a year over the ASX 200 from 2011 to mid-2024 [1]; the fund launched in July 2024 and is 3.9 points a year behind since. Report 55's survivors-only extension showed the engine's own rule ahead of the index over nearly the same months; a real momentum fund with real constituents was behind. That is a reason to weight the extension lightly.
- **AUMF**, the longest-lived Australian multi-factor fund, was 6.8 behind, level, 3.0 behind, 2.2 ahead and 7.8 ahead of the A200 index in 2021–2025: level over five years, after a 0.30% fee.
- Three funds, three different answers. That is what a premium of two or three points a year with eight to ten points of yearly noise looks like.

Cost of the ETF route against the data route:

| Slice | A200 fee | AQLT or AQTY fee | Extra for the tilt | Planned price data (A$370) as % of slice | Price + fundamentals snapshots (A$555) | Price + full fundamentals plan (A$1,233) |
|---|---|---|---|---|---|---|
| A$5,000 | A$2 | A$17.50 | A$15.50 | 7.4% | 11.1% | 24.7% |
| A$25,000 | A$10 | A$87.50 | A$77.50 | 1.5% | 2.2% | 4.9% |
| A$100,000 | A$40 | A$350 | A$310 | 0.4% | 0.6% | 1.2% |

An ETF also needs no brokerage on Betashares Direct [unverified here; as the spec assumes for A200], no monthly work, and no company-level tax records; its own internal turnover is paid for inside the fund and shows up in distributions.

Whether to hold one is the owner's decision, not something this evidence recommends. The frozen plan is A200 and BGBL, never sold. A quality ETF as a satellite is a bet that one index design keeps working; it would change the plan's Australian weight rules and would need its own owner decision. The step that costs nothing and changes nothing is to score the ETFs on paper beside the engine (card H97).

## 4. Recommendation

### 4.1 Options and yearly cost

| Option | What it gives | Data cost a year | Verdict |
|---|---|---|---|
| A. Do nothing more | Engine v0 on paper, price data only | A$370 (monthly) or A$307 (paid annually) | The plan as it stands |
| **B. Score the ETFs on paper** | A live, after-fee, survivorship-free read on quality, momentum and "quality plus" in Australia, from funds that own the proper data | A$0 extra | **Do this** (H97) |
| **C. One-off data audit** | Finds out what EODHD's ASX fundamentals contain; the download can be kept and becomes snapshot number one | About A$93, once | Optional; do it only if D is a real possibility (H95) |
| D. Forward quality + momentum engine | Snapshots each March and September; a paper book beside v0 | About A$185 extra: A$555 in all (A$492 if the price plan is paid annually) | Parked (H96). The cheapest credible path, but not worth it below about A$100,000 in the slice |
| E. Full EODHD fundamentals plan all year | Nothing D lacks for a yearly rule | A$926 extra (A$1,233 with annual prices; A$1,543 All-in-One) | No |
| F. Institutional point-in-time history | The only honest back-test | A$18,000–50,000 | No |
| G. University or library route | DatAnalysis look-ups for spot checks | Free with a library card [unverified] | Use for H95's hand check only |

### 4.2 Why forward-only is the credible version

Every other affordable route produces a back-test with at least one of: survivors only, restated numbers, or seven years of history. A back-test with those faults would look better than the truth, and this programme has already seen three clean back-test gains of 1.2 to 1.6 points reverse on later data (reports 53 and 55). A forward record built from dated snapshots has none of those faults. It is slow, and that is its only fault.

Australian companies report twice a year, mostly by the end of February and August. One month of the fundamentals plan in mid-March and one in mid-September captures every result once, soon after it is public. The engine reviews in December, so the August results are more than three months old when used, which is longer than any reporting lag.

### 4.3 Why it is still not worth paying for now

- **Size of the prize.** Section 2 puts the paper quality premium in Australia at 2.5 to 4.5 points a year long–short. A long-only tilt in large companies captures a fraction; 0 to 1.5 points a year over v0 is a generous range.
- **Cost against the prize.** A$185 extra is 0.7% a year of a A$25,000 slice; the full data bill of A$555 is 2.2%. At A$5,000 it is 11%.
- **It cannot be shown to work.** Report 53 section 7 measured about 8.5 points a year of difference (standard deviation) between a 30-stock book and the index, and found that a true 2.5-point edge would take about 31 years to show at ordinary confidence. For the *increment* of a quality + momentum book over v0, assume a smaller gap of 4.5 points a year between the two books [assumption, to be measured]. Years needed for t = 2 is (2 × 4.5 ÷ edge)²: 81 years at an edge of 1.0 point, 36 years at 1.5.
- **The cheaper substitute exists.** Funds with institutional data already run these rules for 0.35%.

So: B now; C if curious; D only if the audit passes, the slice is large enough that A$555 a year is under about half a percent of it (about A$100,000), and the owner accepts that it is a hobby record, not a proof.

## 5. Pre-registered design, to be frozen before any fundamentals are loaded

This is the design for H96 and H99. It is written now so that nothing in it is chosen after seeing data. It is to be hashed with the card.

**5.1 Data gate (H95) first.** No strategy run until H95 passes.

**5.2 Universe and mechanics.** Exactly `FINAL_RULES_v1.1.md` (report 55): 300 most-traded companies, December review, equal weights, n = min(30, max(4, floor(NAV ÷ 2,500))), 25% industry cap, the same cost and tax models, account sizes A$25,000 and A$100,000. Only the score changes.

**5.3 Fundamental timing rule.** A figure for a period ending on date E may be used at a formation date F only if F ≥ max(`filing_date`, E + 75 days) where a filing date exists, and F ≥ E + 122 days where it does not. In the forward test, a figure may be used only if it is in a snapshot dated before F. A company with no usable figure gets the universe-median quality rank (it is neither favoured nor excluded).

**5.4 Scores (fixed now).** All ranks are percentile ranks within the 300.

| ID | Quality measure | Notes |
|---|---|---|
| Q1 (primary) | Gross profit ÷ total assets (Novy-Marx). For GICS Financials and Real Estate, where gross profit is not defined: net profit ÷ shareholders' equity. Ranked within two groups (financial and property; all others) so that neither group is favoured | Latest full financial year |
| Q2 | Mean rank of: return on equity; low net debt ÷ total assets; low variability of yearly earnings-per-share growth over five years. The AQLT and MSCI definition | Needs five years of history per company |
| Q3 | Piotroski F-score, 0 to 9 | Nine yearly tests |

| Spec | Rule |
|---|---|
| QM-a (primary) | Score = mean of rank(H80 score) and rank(Q1) |
| QM-b | H80 score among companies in the top half by Q1 only |
| QM-c, QM-d | As QM-a with Q2, Q3 |
| QM-e, QM-f | As QM-b with Q2, Q3 |
| Q-solo-1, -2, -3 | Q1, Q2, Q3 alone (reference; no momentum) |

Nine specifications. No weights other than equal, no other thresholds, no three-way mixes.

**5.5 Samples.** Which case applies is decided by H95, not by results.

- **Case F (forward; the expected case).** No back-test is used for any choice. QM-a alone is run on paper from the first December after the second snapshot. Confirmatory sample: months after the card's freeze. QM-b to QM-f and the solo scores are not run.
- **Case S (EODHD history passes H95 part (b) for 2019 on only).** One sanity run of QM-a and v0 on December 2019 to the latest complete December, reported with the label "restated figures, about seven years, not evidence". No selection, no adoption, one trial.
- **Case H (a licensed point-in-time history from 2000 with delisted companies is ever obtained).** Development: decisions December 2000 to November 2015. Second sample: December 2015 to 31 May 2024. That window is spent for the H80 score (eight looks, report 55) but no fundamental has been seen on it; the quantity judged is **QM minus v0**, which nobody has seen. All nine specifications run on development only. The best one that beats v0 at both sizes after tax (no-discount regime) by at least 0.25 points a year, with a drawdown no more than 5 points deeper, gets one look at the second sample. June 2024 onward is reported and not used.

**5.6 Adoption (Cases H and F at a formal look).** All of:
1. After-tax return above v0's at both account sizes, by **at least 1.0 point a year on average** (report 55's noise floor).
2. At or above the 90th percentile of 200 random portfolios run through the same machinery.
3. Paired bootstrap of the monthly difference from v0: at least 0.90 of paths ahead.
4. **Shuffled-quality placebo:** at or above the 90th percentile of 100 versions in which the quality ranks are shuffled among companies of the same group (financial and property, or other) and the same size third. This asks whether the fundamentals add information or only noise that happens to help.
5. Deflated Sharpe ratio at least 0.95 with every trial counted.
6. Stop at the first look that fails. Nothing is chosen on the second sample.

**5.7 Diagnostic, counted as a trial.** In Case H only: QM-a re-run with the timing rule switched off (figures used from the period end). The gap between the two runs is the measured value of hindsight in this data and is reported; it informs no choice.

**5.8 Trial count.**

| Item | Rows |
|---|---|
| Report 51's log | 303 |
| Reports 53 and 55: loop versions | 17 |
| Report 55: walk-forward procedures | 5 |
| **N_lib after report 55** | **325** |
| Report 56 (idea lab): 11 specifications logged in `bigwins_lab/out/trials_lab.csv`; report not yet filed when this was written | +11 → 336 |
| This design, if run in full (Case H): 9 specifications + 1 diagnostic | +10 → 346 |
| Case F: QM-a only | +1 |
| Case S: one sanity run | +1 |

This report itself adds no trial. The two factor-file calculations in section 2.2 are descriptive statistics of published series over periods fixed before looking (whole history; the publication year 2013; and report 53's unseen window), not strategy tests.

**5.9 What is declared about power.** The forward test is not expected to reach the bar for a return claim (section 4.3). Its uses are: to confirm the machinery, to measure the gap between the two books, to rule out a disaster, and to build a hindsight-free fundamentals archive that will be worth more each year.

## 6. Cards (RND-010 format)

Common fields as report 53 section 9: date registered on freezing; card hash, trials consumed, result, decision and approver blank until frozen and run. Costs and tax: section 25 models with the BW half-spread table.

### H95 — Data audit: what do EODHD's ASX fundamentals contain?

| Field | Content |
|---|---|
| ID / family | H95 / measurement (no rule; no trial) |
| Question | Can EODHD's ASX fundamentals support (a) a forward quality score, (b) any back-test at all |
| Method | In one paid month of the Fundamentals Data Feed (about A$93): list ASX symbols with `delisted=1`; download the fundamentals object for every live and delisted ordinary share (10 calls each; about 25,000–40,000 calls); store raw responses with retrieval time and hash (LE-05 class B). Tabulate by year: companies with a yearly income statement and balance sheet; delisted companies with the same, by delisting year; share with a `filing_date`; median days from period end to `filing_date`. Hand-check 30 randomly drawn company-years (10 delisted) against the lodged Appendix 4E or annual report, read one at a time on asx.com.au or in DatAnalysis at a library: revenue, net profit, total assets, total equity |
| Pass (a), forward use | Of the current top 300 by traded value, at least 95% have the last two financial years of the fields Q1 needs, and at least 27 of the 30 hand-checked company-years agree within 2% on all four items |
| Pass (b), back-test use from year Y | For each year from Y: at least 90% of that year's top 300 (from the licensed price store, delisted included) have fundamentals; and at least 80% of companies delisted in that year or later are present with fundamentals. Expected result from the vendor's own statements: Y no earlier than 2019 |
| Fail | (a) fails → H96 stays parked and no further fundamentals are bought. (b) fails for every Y → Case F only |
| Also record | Whether delisted price history before 2018 is present (answers BW-05); whether half-year reports appear and how they are labelled; whether the earnings-surprise fields are populated for ASX |
| Decision it informs | Which case of section 5.5 applies; whether option D is possible |

### H96 — Parked: quality + momentum Big Wins book (forward paper test)

| Field | Content |
|---|---|
| ID / family | H96 / `BW`, Family B; parked until H95 (a) passes and the owner approves the data cost (owner decision; PK list) |
| Economic rationale | Profitable, soundly financed companies have earned more than weak ones in Australian and global data (section 2), the effect is nearly uncorrelated with momentum (0.18), and a quality screen removes momentum names whose rise is not backed by earnings. Australian evidence is weaker in large companies and fails strict multiple-testing standards (Hoang et al. 2019) |
| Exact rule | `FINAL_RULES_v1.1.md` with the score replaced by QM-a of section 5.4; timing rule 5.3 |
| Fixed parameters | As H82; Q1 as defined; equal weight of the two ranks |
| Permitted perturbation grid | None |
| Data | Licensed price store of BW-04; fundamentals from the owner's own dated snapshots (each March and September) |
| Sample | Months after the freeze only. No back-test is used (Case F). Case S's sanity run, if H95 allows it, is reported as a secondary item |
| Benchmark | Primary: H82 (v0) on the same dates and dollars. Secondary: A200 total return; AQLT and the H97 mix |
| Primary metric → pass | Mean monthly return minus v0's, after costs and tax, at A$100,000: section 5.6 conditions 1 to 5 at a formal look (36, 60, 120 months). Not expected to be met |
| Fail | At a formal look: more than 10 points in total behind v0 after costs, or drawdown more than 15 points deeper than v0's → close the card and stop buying snapshots unless the owner records a reason |
| Secondary metrics | Gap between the two books (standard deviation of the monthly difference); turnover; overlap of holdings with v0 and with AQLT; share of holdings using the median-rank fallback |
| Multiple-testing family | `BW`; adds 1 to N_lib at registration (2 with Case S) |

### H97 — Measurement: Australian factor ETFs against A200 on the paper scoreboard

| Field | Content |
|---|---|
| ID / family | H97 / measurement (no rule of the system's; no trial) |
| Null | After fees, AQLT, MTUM, AQTY and a 50/50 AQLT + MTUM mix rebalanced each December earn no more than A200, total return, same dollars and dates |
| Data | ETF prices and distributions from the price plan already bought. Start: fund inception for the descriptive table; **the card's freeze date for the measurement** |
| Primary metric | Total return minus A200's, each line; with the monthly standard deviation of the difference |
| Read | At 36, 60 and 120 months after the freeze. Before 36 months the report prints "too early to tell" |
| Printed beside it | H82's line, so the owner can see the engine, the funds and the index on one page |
| Decision it informs | Only whether the owner wishes to raise a satellite as an owner decision. It never moves money and never changes a cap |
| Note | History before the freeze (section 3) is context. It was seen before this card was written and is not evidence for the card |

### H98 — Negative control for H96: shuffled quality

| Field | Content |
|---|---|
| ID / family | H98 / `BW` control; runs only if H96 runs |
| Exact rule | H96's machinery with the Q1 ranks shuffled among companies of the same group and size third, 100 seeds |
| Pass (behaves as a control) | The median shuffled book is within 1 point a year of v0 after costs at a formal look |
| Fail | The median shuffled book is more than 1 point a year ahead of v0 → the mixing rule itself, not the fundamentals, is changing the result (for example by diluting momentum); audit before reading H96 |
| Secondary | H96's percentile among the 100 (condition 4 of section 5.6) |

### H99 — Parked draft: quality + momentum back-test on a licensed point-in-time history

| Field | Content |
|---|---|
| ID / family | H99 / `BW`, parked draft. Costs no trial until run |
| Trigger | Only if a point-in-time ASX fundamentals history from 2000 with delisted companies is obtained under a licence that permits this use (section 1.2 rows 3 to 8). Not expected |
| Content | Section 5.5 Case H in full: nine specifications on development, one look at the second sample for one candidate, the hindsight diagnostic of 5.7 |
| Rule for running it | Budget, stop rule and N_lib declared and hashed first; every specification counted (up to 10) |
| Note | Recorded so that nobody runs the nine specifications on survivors-only or restated data and reports the best |

### H100 — Closed without a run: quality or earnings signals on data with hindsight

| Field | Content |
|---|---|
| ID / family | H100 / `BW`, closed (data-blocked) |
| Rules covered | Any quality, profitability, value, investment, accruals, F-score, earnings-surprise or analyst-revision rule tested on (i) fundamentals of companies still listed today, (ii) current or restated values without the timing rule of 5.3, or (iii) a history shorter than ten years |
| Reason | Report 51 section 1.6 and section 1 of this report: the result would be biased upward by an unknown amount and could not be told from a real effect |
| Decision | Not to be run. Analyst-revision rules stay blocked until a dated estimates history is licensed |
| Trials consumed | 0 |

## 7. Owner decisions this raises

| # | Decision | Default if no answer |
|---|---|---|
| O-57a | Add card H97 (ETF scoreboard) to the monthly paper report | Yes: no cost, no money moved |
| O-57b | Spend about A$93 once on the H95 audit | No, until the owner is seriously considering H96 |
| O-57c | Run H96 (about A$185 a year extra) | No, below a A$100,000 slice |
| O-57d | Hold a quality or "quality plus" ETF as a real-money satellite | Not proposed here. It would amend the frozen plan and needs its own review |

## 8. Reasons this could be wrong

- **EODHD may hold more than it promises.** Its documentation is a floor. H95 could find usable ASX fundamentals for companies delisted before 2018; then Case S widens. It would still not be point-in-time.
- **A retail route I could not reach may exist.** SIRCA, LSEG, FactSet, S&P, FMP, Stockopedia and Morningstar's own sites were blocked. An individual product for Australian history (for example a DatAnalysis personal subscription) would change rows 3 and 4. I found no sign of one.
- **Quality may matter more for the engine than the factor tables suggest.** Report 53 found the engine "held none of them during their collapses"; a quality screen aims at exactly that. The effect on a 10–30 stock book could be larger than a diversified factor's. It could also be smaller. Only H96 would show which, slowly.
- **AQLT's lead may be real skill in index design.** Four out of four calendar years is unusual. The evidence is still one fund over one cycle.
- **The 4.5-point gap assumed in section 4.3 is a guess.** If the quality + momentum book tracks v0 more closely, proof comes sooner; at 2.5 points and a 1.5-point edge it is still about 11 years.
- **Factor files end in August–September 2026** and are revised by their authors; small changes in the figures of section 2.2 are possible.

## 9. Files and sources

Working directory: `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/r57/`

- `dl/eod_*.html|txt`: EODHD pricing, plans, methodology, storage, personal use, AI tools, limits, fundamentals API, bulk fundamentals, delisted data, ASX page, delisted FAQ (downloaded 2026-11-14).
- `dl/norgate_*.html|txt`: Norgate packages, FAQ, data content tables.
- `dl/asx_terms.html|txt`: ASX terms of use.
- `dl/AQLT.pdf`, `MTUM.pdf`, `A200.pdf`, `QOZ.pdf`, `HQLT.pdf`: Betashares factsheets dated 30 October 2026 (SHA-256 prefixes 612342ec…, a048f367…, 0799affb…).
- `dl/vaneck_limits.pdf` (bb38eb48…): VanEck, "The limits of quality in Australia", April 2026; `dl/va.html`, `dl/aqty.txt`: AQTY fund page.
- `dl/aqr/*.xlsx`: AQR Quality Minus Junk (d26f09cd…), Betting Against Beta, HML Devil monthly files; `dl/ff/*.zip`: Ken French Asia Pacific ex Japan five factors and momentum.
- `aqr.py`, `ff.py`: the calculations of section 2.2. `abs.py`, `totext.py`: page-to-text helpers. `dl/ideas_*.html`: paper abstracts.

Primary pages read directly:
- https://eodhd.com/pricing · https://eodhd.com/help/plans · https://eodhd.com/help/methodology · https://eodhd.com/help/storage · https://eodhd.com/help/personal-use · https://eodhd.com/help/ai-tools · https://eodhd.com/help/limits
- https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds · https://eodhd.com/financial-apis/bulk-fundamentals-api · https://eodhd.com/financial-apis/delisted-stock-companies-data · https://eodhd.com/financial-academy/financial-faq/historical-stock-prices-for-delisted-companies · https://eodhd.com/asx-data
- https://norgatedata.com/stockmarketpackages.php · https://norgatedata.com/data-content-tables.php · https://norgatedata.com/faq.php
- https://www.asx.com.au/legals/terms-of-use
- https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/morningstar/us-fundamental-data
- https://www.betashares.com.au/files/factsheets/AQLT-Factsheet.pdf · …/MTUM-Factsheet.pdf · …/A200-Factsheet.pdf
- https://www.vaneck.com.au/globalassets/home.au/media/managedassets/library/assets/white-papers/vaneck_the-limits-of-quality-in-australia.pdf · https://www.vaneck.com.au/etf/equity/aqty/snapshot/
- https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-Factors-Monthly.xlsx · …/Betting-Against-Beta-Equity-Factors-Monthly.xlsx
- https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html (Asia_Pacific_ex_Japan_5_Factors, Asia_Pacific_ex_Japan_Mom_Factor)
- Abstracts: https://ideas.repec.org/a/eee/finana/v35y2014icp207-218.html · https://ideas.repec.org/a/eee/pacfin/v57y2019ics0927538x1930304x.html · https://ideas.repec.org/a/eee/pacfin/v55y2019icp182-191.html · https://ideas.repec.org/a/eee/pacfin/v58y2019ics0927538x19303476.html · https://ideas.repec.org/a/bla/acctfi/v64y2024i4p3781-3802.html · https://ideas.repec.org/a/bla/acctfi/v58y2018i2p423-444.html · https://ideas.repec.org/a/pal/assmgt/v21y2020i2d10.1057_s41260-020-00157-2.html · https://ideas.repec.org/a/sae/ausman/v37y2012i2p261-281.html · https://ideas.repec.org/a/bla/acctfi/v56y2016i2p393-421.html

Reached through search summaries only (hosts blocked or not fetched):
- SIRCA: https://www.sirca.org.au/faq · https://fbe.unimelb.edu.au/research/facilities-and-resources/research-databases/sirca-gateway
- DatAnalysis: https://eresources.sl.nsw.gov.au/morningstar-datanalysis · https://fbe.unimelb.edu.au/research/facilities-and-resources/research-databases/datanalysis · https://datanalysis.morningstar.com.au/licensee/datpremium/html/DatPremiumFinancialData2012.pdf · https://libraryguides.griffith.edu.au/az/morningstar-datanalysis-premium
- LSEG: https://www.lseg.com/en/data-analytics/financial-data/company-data/fundamentals-data/worldscope-fundamentals · Compustat: https://libguides.princeton.edu/econ-finance/FundamentalsInternational
- Terminal prices: https://www.costbench.com/software/financial-data-terminals/bloomberg-terminal/ · https://multiples.vc/compare/pricing/md
- FMP: https://multiples.vc/compare/fmp-api-alternatives · Stockopedia: https://why.stockopedia.com/sfb · https://www.stockopedia.com/learn/our-data/data-process-462798 · Sharadar: https://quantrocket.com/sharadar · IBKR: https://www.interactivebrokers.com/docs/web-api/changelog/2026/1/6
- ASX reporting deadlines: https://www.bdo.com.au/en-au/blogs/corporate-reporting/asx-to-strictly-enforce-lodgement-deadline-rules · https://asx.com.au/content/dam/asx/documents/listings/compliance-updates/2021/listed-compliance-update-feb-0121.pdf
- Papers: https://econpapers.repec.org/RePEc:eee:jfinec:v:108:y:2013:i:1:p:1-28 (Novy-Marx) · https://papers.ssrn.com/abstract=2312432 (Asness, Frazzini, Pedersen) · https://econpapers.repec.org/RePEc:eee:jfinec:v:123:y:2017:i:3:p:441-463 (Fama and French) · https://econpapers.repec.org/RePEc:eee:jfinec:v:135:y:2020:i:1:p:213-230 (Jacobs and Müller) · McLean and Pontiff (2016), *Journal of Finance* · https://ideas.repec.org/a/sae/ausman/v38y2013i2p353-373.html (Dou, Gallagher, Schneider) · https://research.monash.edu/en/publications/a-better-model-an-empirical-investigation-of-the-famafrench-five-/ (Chiah et al.)
- ETFs: https://www.blackrock.com/au/products/284664/ishares-edge-msci-australia-multi-factor-etf · https://pearler.com/invest/asx/asset/DACE · https://betashares.com.au/insights/quality-investing-australia
