# Tax and regulatory research: automated ETF system via IBKR Australia (as at 13 Nov 2026)

## Verification limits

- **Read directly (primary):** legislation.gov.au (Tax Reform No. 1 Act 2026, ITAA 1997, Corporations Act 2001, Digital Assets Framework Act 2026, Estate Duty Convention Act 1953) and irs.gov (income tax treaty, Form 706-NA and W-8BEN instructions, estate tax page).
- **Not fetchable from this session:** ato.gov.au (returns "Access Denied"), www.asic.gov.au, IBKR Australia pages, aph.gov.au, austrac.gov.au, finra.org. Anything cited to those is from search-result extracts only, and I mark it "(via search)".
- **Tags:** [2+ sources] means two independent sources, at least one primary. [1 source] and [unverified] are as named.
- This is research, not tax or legal advice.

## Priority 1: Investor or trader for a monthly automated switch

- **No bright line; it is a multi-factor test.** [2+ sources] ATO (via search): factors are "the nature and purpose of your activities; the repetition, volume and regularity of your activities; if your activities are organised in a business-like way; the amount of capital invested". "The higher the volume of your share transactions, the more likely it is that you are carrying on a business." [ATO: share investing versus share trading](https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/shares-and-similar-investments/share-investing-versus-share-trading). Second source: [PwC on Greig's case](https://www.pwc.com.au/tax/tax-alerts/tax-alert-capital-vs-revenue.html) ("all about the facts").
- **Consequences.** [2+ sources] Investor: CGT on disposal. Trader: gains are ordinary income, losses deductible, shares treated like trading stock (same ATO page).
- **Automation.** [unverified] I found no ATO guidance on automated or algorithmic trading. A written rule-set and systematic records are "business-like" indicators, while about 12–24 trades a year on A$5,000 is low volume. Capital account is the likely position, not a certain one. The ATO says a change of status changes the treatment, so each user should get this confirmed in writing by a tax agent.
- **Why it matters more from 1 July 2027.** [1 source, my reading of the Act] The 30% minimum tax applies only to capital gains, so capital versus revenue now changes the rate for anyone whose marginal rate is under 30%.

## Priority 2: The 2026 CGT Act

- **Existence and status.** [2+ sources] Treasury Laws Amendment (Tax Reform No. 1) Act 2026, No. 49 of 2026, Royal Assent 26 June 2026, in force. [Act on legislation.gov.au](https://www.legislation.gov.au/C2026A00049/asmade/text); [ATO: capital gains tax reform](https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/capital-gains-tax-reform) (via search). The rate is set by the companion Income Tax Rates Amendment (Tax Reform No. 1) Act 2026, which Act 49's commencement table names; "No. 50" is from secondary sources only.
- **Discount ends.** [2+ sources] New s 115-100(aa): the discount is "50% if: (i) the gain is made by an individual from a CGT event happening before 1 July 2027".
- **Indexation replaces it, for residents, after 12 months.** [2+ sources] s 110-36(1A) applies if "the CGT event happens on or after 1 July 2027", and "does not extend to foreign residents or temporary residents". s 114-10(1): "You only index expenditure … if you … had acquired the asset at least 12 months before the time of the CGT event." Indexation applies to gains only: costs are indexed "in working out a capital gain … but not in working out a capital loss".
- **Parcels held across 1 July 2027.** [2+ sources] s 112-155(2): you are taken "to have sold the asset just before 1 July 2027" and "to have acquired the asset again just after that sale".
  - Proceeds are "the asset's market value just before 1 July 2027", or an amount under a ministerial "apportioning method" (s 112-185).
  - The pre-July gain is "disregarded (and deferred) until the income year in which the realisation event happens".
  - The 12-month tests ignore the deemed sale (ss 112-160(3)(c), (5), 114-10(9)). A parcel bought March 2027 and sold April 2028 gets the discount on the pre-July slice and indexation on the post-July slice.
  - [unverified] I could not confirm whether the s 112-185 instrument has been made.
- **30% minimum tax.** [2+ sources for existence and exemptions; 1 source for scope] Division 119 ensures "before applying offsets, a rate of tax of 30%" for resident individuals.
  - It covers "residential" and "non-residential" capital gains, which are gains other than the deferred pre-July slice (s 102-6), "remaining after applying step 6" (so after capital losses).
  - Extra tax is 30% of that gain less the tax the gain already bears (s 119-10(2)).
  - Recipients of listed payments (age pension, JobSeeker, family tax benefit, parental leave pay and others) are exempt (s 119-15).
  - My reading: there is no 12-month condition and no asset-type carve-out. Short-term gains on ASX ETFs, US ETFs, crypto and capital-account futures are all inside it.
- **Effect on a monthly switcher.** [1 source, inference] Holdings under 12 months get no discount now and no indexation later. A user with a marginal rate under 30% pays the floor on net post-July capital gains. Interaction with franking offsets is a tax-agent question.

## Priority 3: Franking, the 45-day rule and the $5,000 exemption

- **Holding period rule.** [2+ sources] ATO (via search): hold "at risk" for at least 45 days, not counting acquisition or disposal days; last-in-first-out identifies the parcel sold, for this test only. [ATO: You and your shares 2026](https://www.ato.gov.au/forms-and-instructions/you-and-your-shares-2026/franking-tax-offsets-and-franking-credits/franking-tax-offsets); [Rivkin](https://rivkin.com.au/education/franking-credits-the-45-day-holding-rule/). ITAA 1997 still tests whether the recipient "is a qualified person … for the purposes of Division 1A of former Part IIIAA of the Income Tax Assessment Act 1936".
- **Small shareholder exemption.** [2+ sources] Individuals with total franking credit entitlement of $5,000 or less in the year may claim without meeting the rule (same two sources). Rivkin says exceeding it loses the exemption entirely. On A$5,000 in VAS, credits are tens of dollars a year (my estimate), so the exemption should cover a monthly switcher.
- **Disagreement to flag.** One ATO passage says the exemption "doesn't apply where the dividend flows indirectly to you through an interest in a trust"; the search extract places that in the dividend-washing context. VAS is a trust, so confirm with the tax agent.
- **System impact.** Monthly switching will often hold VAS for fewer than 45 days around a quarterly distribution. The ledger needs a 45-day LIFO test and a running franking total per user.

## Priority 4: Division 775 on USD cash (stage 2 onward)

- **Assessable outside CGT.** [2+ sources] s 775-15(1): "Your assessable income … includes a forex realisation gain". The private-or-domestic exception is switched off where the gain "would, apart from this Division, be taken into account under Part 3-1 or 3-3". [ITAA 1997](https://www.legislation.gov.au/C2004A05138/latest/text); [ATO: foreign exchange gains and losses](https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses) (via search).
- **FIFO.** [1 source] s 775-145(1): events apply to foreign currency "on a first-in first-out basis".
- **$250,000 election.** [2+ sources] s 775-250(1): gains or losses from forex realisation event 2 or 4 are "disregarded" for an elected account that passes the test. The test is credit balances "not more than the foreign currency equivalent of $250,000" (s 775-245). The election "must be in writing" (s 775-230). [ATO: forex elections](https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses/in-detail/forex-elections) (via search).
- **Does an IBKR balance qualify?** [unverified] A qualifying forex account is one "denominated in a particular foreign currency" that "has the primary purpose of facilitating transactions". Whether a multi-currency brokerage cash balance fits is a tax-agent question.
- **Sale proceeds received in USD.** [1 source] Under s 775-70, if the currency fell due within 12 months of the sale, the forex gain "is not included in your assessable income under section 775-15" and "CGT event K10 happens".
- **Translation.** [2+ sources] s 960-50(6) item 5: CGT amounts are translated "at the exchange rate applicable at the time of the transaction or event". ATO (via search) permits "an appropriate exchange rate provided by a banking institution operating in Australia, or another reliable external source". RBA rates specifically: [1 source], an ATO Community reply.

## Priority 5: US withholding, FITO and estate tax

- **15% treaty dividend rate.** [1 primary source] Article 10: tax "shall not exceed 15 percent of the gross amount of the dividends". [IRS treaty text](https://www.irs.gov/pub/irs-trty/aus.pdf). This is the 1982 text; I did not read the 2001 protocol.
- **W-8BEN.** [1 primary source] "Failure to provide a Form W-8BEN when requested may lead to withholding at the foreign-person withholding rate of 30%". [IRS W-8BEN instructions](https://www.irs.gov/instructions/iw8ben). The three-year validity is from memory [unverified].
- **FITO.** [2+ sources] s 770-75(2): "Your offset limit is the greater of: (a) $1,000; and (b)" a calculated amount. [ATO myTax 2026 FITO](https://www.ato.gov.au/individuals-and-families/your-tax-return/instructions-to-complete-your-tax-return/mytax-instructions/2026/tax-offsets/foreign-income-tax-offset) (via search).
- **US estate tax.** [2+ sources]
  - US-situs assets include "Stock of corporations organized in or under U.S. law … even if … registered … in the name of a nominee". Form 706-NA is required if they exceed $60,000. [IRS: nonresidents with US assets](https://www.irs.gov/individuals/international-taxpayers/some-nonresidents-with-us-assets-must-file-estate-tax-returns).
  - "the maximum unified credit is $13,000", and the Australian treaty is one of those that modify it. [IRS 706-NA instructions](https://www.irs.gov/instructions/i706na).
  - Treaty Article IV(2)(a) gives an exemption bearing "the same proportion to any specific exemption … as the value of the property subjected to that tax bears to" the worldwide property. [Estate Duty Convention Act 1953](https://www.legislation.gov.au/C1953A00083/asmade/1953-12-11/text/original/epub/OEBPS/document_1/document_1.html).
  - One law-firm page claims a full exemption; the treaty text is pro-rata. That US-listed ETFs count as US corporate stock is my inference.
- **ASX-listed VAS and VGS.** [unverified] Being Australian-domiciled, they should carry no W-8BEN, US estate or Division 775 exposure for the holder. I did not check the Vanguard disclosure documents.

## Priority 6: Licensing when others use the owner's software

- **Own-account trading.** [2+ sources] s 766C(3): "A person is taken not to deal in a financial product if the person deals in the product on their own behalf". [Corporations Act 2001](https://www.legislation.gov.au/C2004A00818/latest/text); [AFSL House](https://afslhouse.com.au/insights/afsl-dealing-in-financial-product/).
- **Acting for others.** [1 primary source] s 766C(3A): an agent dealing for a principal "is not taken to deal in the product on the agent's own behalf". s 766C(2): "Arranging for a person to engage in" dealing is itself dealing. If the owner's infrastructure places orders in other users' accounts or holds their credentials, the exemption does not obviously cover it.
- **Advice.** [2+ sources] s 766B(1): advice is "a recommendation or a statement of opinion … intended to influence a person … in making a decision in relation to a particular financial product". A "switch to VGS" output could fit. [ASIC: do you need an AFS licence](https://asic.gov.au/regulatory-resources/financial-services/financial-advice/your-obligations-when-giving-financial-advice/do-you-need-an-afs-licence) (via search).
- **Business test.** s 911A(1) applies to "a person who carries on a financial services business". [unverified] No fees and five or fewer users helps, but I could not read RG 36 to confirm how ASIC applies the test.
- **Pooling.** [1 primary source] A managed investment scheme needs contributions "to be pooled, or used in a common enterprise" and members without "day-to-day control". Separate accounts avoid the first limb; user control addresses the second.

## Per-market tables

### ASX shares and ETFs (stage 1, live)

| Item | Position |
|---|---|
| Tax | Likely capital account. No discount or indexation under 12 months. 30% floor on post-1 July 2027 capital gains. Franking via the $5,000 exemption. |
| Key risks | Trader reclassification; 45-day rule if credits exceed $5,000; minimum tax for low-income users. |
| Licences / permissions | None for own-account trading. IBKR cash account, AUD base, ASX permission only. |
| Records | Parcel ledger; ETF annual tax statements; 30 June 2027 closing prices; 45-day LIFO test. |

### US-listed ETFs and stocks (stage 2)

| Item | Position |
|---|---|
| Tax | CGT in AUD at trade-date rates; 15% US withholding with FITO; Division 775 on USD cash; US estate tax above US$60,000. |
| Key risks | Forex events on every USD movement. Cash-account free-riding: IBKR's knowledge base (via search) says a violation means 90 days of "Cash Up Front" [1 source]. |
| Licences / permissions | W-8BEN; US stock permission. The pattern-day-trader rule and its $25,000 minimum were removed effective 4 June 2026: [FINRA Notice 26-10](https://www.finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf), [King & Spalding](https://www.kslaw.com/Insights/Articles/finra-adopts-sweeping-changes-to-margin-requirements-for-day-trading) [2+ via search]. |
| Records | USD lot ledger (FIFO); withholding per dividend; written s 775-230 election if available. |

### CME micro futures (stage 3)

| Item | Position |
|---|---|
| Tax | TOFA excluded: s 230-455(1), "This Division does not apply … if: (a) you are: (i) an individual", subject to para (e) [1 primary source]. Revenue versus capital is unsettled; only secondary sources found [unverified]. Margin payments are not deductible under TD 2006/25 (via search) [1 source]. |
| Key risks | Leverage; losses and Division 35 (not researched); forex on USD margin. |
| Licences / permissions | Margin account and futures permission. IBKR Australia pages (via search, old) show a A$50,000 retail margin-loan cap and A$2,000 minimum [1 source, may be stale]. Knowledge-test and target-market details [unverified]. The CFD intervention order (expires 23 May 2027; extension proposed in [ASIC CS 64](https://asic.gov.au/regulatory-resources/find-a-document/consultations/cs-64-protecting-retail-investors-proposed-extension-and-amendments-to-the-cfd-product-intervention-order), via search) targets CFDs, not exchange-traded futures. |
| Records | Per-contract realised P&L in USD and AUD; daily variation margin; commissions. |

### Crypto (optional)

| Item | Position |
|---|---|
| Tax | Each disposal, including crypto-to-crypto, is a CGT event: [ATO: crypto asset investments](https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/prepare-and-lodge/tax-time/tax-time-toolkits/tax-time-toolkit-for-investors/tax-and-crypto-asset-investments) (via search), [CoinJar](https://www.coinjar.com/au/learn/australian-crypto-tax-eofy) [2+]. The 30% floor applies on my reading. |
| Key risks | ATO data-matching with exchanges (secondary only) [1 source]; platform risk. |
| Licences / permissions | None for the user. The [Digital Assets Framework Act 2026](https://www.legislation.gov.au/C2026A00038/asmade/text) commences "8 April 2027" per its commencement table; secondary sources say 9 April ([Gilbert + Tobin](https://www.gtlaw.com.au/insights/key-topics/australia-passes-highly-anticipated-digital-asset-regulation)) [2+]. AUSTRAC's virtual-asset regime from 31 March 2026 is from secondary sources only [1 source type]. IBKR Australia crypto availability [unverified]. |
| Records | Per-asset records for every swap, with AUD value at the time. |

## DECISIONS for the spec

1. **Regime flag per user:** `capital | revenue`, default capital, set by that user's tax agent and never inferred by the system.
2. **Parcel ledger, not averages:** store trade currency, AUD at trade-time rate, rate source and timestamp. Support a CGT parcel-selection method and a separate LIFO view for the 45-day test.
3. **1 July 2027 transition:** snapshot each open parcel's 30 June 2027 closing price. Compute the deferred pre-July slice and the post-July slice separately, with a pluggable "apportioning method" pending the s 112-185 instrument.
4. **Indexation engine:** quarterly CPI from 1 July 2027, gains only, 12-month condition measured from actual acquisition.
5. **Minimum-tax estimator:** per-user flag for exempt-payment recipients; output is an estimate for the tax agent, not a liability.
6. **Franking module:** per-user running franking total against $5,000, and a 45-day at-risk test per distribution.
7. **Forex module (stage 2):** FIFO USD lots; realisation events on conversions, purchases and withdrawals; flags for the s 775-230 election and the K10 short-term rule; balance monitor against A$250,000.
8. **Foreign income module:** gross dividend, US tax withheld, AUD translation and FITO total against the $1,000 threshold.
9. **Architecture for licensing risk:** one instance per user with their own IBKR credentials and their own order approval or configuration. No pooled funds, no fees, and no owner-side execution on others' accounts until a lawyer signs off.
10. **Account defaults:** stage 1 is a cash account, AUD base, ASX only. Enable margin and futures only at stage 3.
11. **Exports:** yearly per-user CGT schedule in AUD, forex schedule, distribution and franking summary, and broker statements retained (retention period to be confirmed).

## Questions for a registered tax agent

1. Is a monthly automated VAS/VGS/cash switch on about A$5,000 on capital account, and what would tip it to revenue?
2. Does the Division 119 floor apply to short-term post-July 2027 gains as I read it, and how do franking and other offsets interact with "before applying offsets"?
3. Does the $5,000 exemption cover credits received through VAS, a trust?
4. Market value or the apportioning method at 1 July 2027, and has the instrument been made?
5. Is an IBKR USD balance a "qualifying forex account", and should each user make the s 775-230 election?
6. Which exchange-rate source should be used, and is a daily RBA rate acceptable?
7. Would futures gains be revenue or capital, and do Division 35 loss rules apply?
8. Is the wash-sale risk under Part IVA relevant to monthly switching at a loss?

## Questions for a lawyer

1. Does supplying the software free to up to five people amount to financial product advice or arranging, and to "carrying on a financial services business"?
2. Does it matter whether signals are shown to users or executed automatically, and who hosts the instance and credentials?
3. Does the architecture stay outside the managed investment scheme definition?
4. What disclaimers or user agreement are needed, and does IBKR's customer agreement permit this API use across accounts?
5. Will the digital asset platform regime touch the system if crypto is added?

The downloaded statute text is in `/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/dl` (for example `act49.txt`, `itaa_9.txt`, `corp_4.txt`).