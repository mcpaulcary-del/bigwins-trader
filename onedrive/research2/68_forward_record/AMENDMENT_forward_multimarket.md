# Amendment: multi-market FORWARD paper record (M3 v1.1, EI10I and CW in 14 markets)

Status: **PRE-REGISTERED 18 Nov 2026 01:02 UTC**, before the first decision of this record (the month-end of Mon 30 Nov 2026). This file is hashed (SHA-256) and the hash is appended to `LEDGER.jsonl` before any forward decision is computed. **PAPER ONLY. No real money, no broker orders. The AI never places trades.** Source: report 78 (`78_forward_multimarket.md`); designs from reports 76 and 77; record design from report 68.

Nothing in this amendment changes the H82 books, the M3/E3 shadow lines (`AMENDMENT_shadow_M3_E3.md`, `AMENDMENT_shadow_M3_v1.1.md`), their code, or the ASX daily job. This record has its own code, state and outputs and shares only the ledger.

## 1. Why

Six research rounds (reports 70–77, 1,649 counted trials) used up the clean historical tests; nothing beat the index with confidence. Only new data can add evidence. Running the same frozen designs forward in many markets at once gathers that evidence faster than ASX alone. Report 78 §1 measures how much faster: on the round-5/6 monthly lead series the markets' leads are only weakly correlated (mean pairwise correlation 0.05–0.16), so pooling 10–14 markets cuts the wait by about 3–7 times. The wait remains long (report 78 §1): this record can find a large edge (about +2 points a year or more for EI10I or CW at A$100,000) within roughly 6–15 years; it cannot find a +1 point edge in any useful time.

## 2. Designs (frozen exactly as tested)

| Design | What it is | Tested in | Engine (byte-identical copies in `bigwins_forward/code/multi_frozen/`) |
|---|---|---|---|
| **M3** (v1.1 behaviour) | 50% local index fund + up to 30 equal-sized names chosen by the M3 momentum score (mean percentile of 12-1-month return, 6-month return, distance from the 52-week high) among the 100 most traded companies; buy rank ≤ 15, hold while ranked ≤ 50 and in the top 100, sold after two bad month-ends, no gain sold before 12 months, May loss rule, trims, top-ups only when full | report 76 §4 (Thailand, China), §8.5; corrected and replicated in report 77 §1–2 | `sim6.py` with `wext` off (= `sim5.py` behaviour), ranks from `ei6.rank_score(mk,'M3')`, keywords `ei6.M3KW` |
| **EI10I** | No fund; up to 30 names (one per A$2,500); point-in-time market cap × (1 + (2p − 1)), p = percentile of the mean of the M3 score and low share issuance; 20% ceiling; sold after two month-ends below rank 45; no gain sold before 12 months | report 77 §3.3–4 | `sim6.py`, `ei6.CONF['EI10I']` |
| **CW** | The same book with no tilt (cap weights) | report 77 §3.3, 4.3 | `sim6.py`, `ei6.CONF['CW']` |

Frozen-engine SHA-256 (checked on every run by `multi_engine.py`):

| File | SHA-256 | Copied from |
|---|---|---|
| `multi_frozen/sim6.py` | `f9efc4bc01ecf5ebb4ed1cbdbbe167e2903e3b611a5468642b737b7d474e1692` | `improve6/code/sim6.py` |
| `multi_frozen/ei6.py` | `fe2365960e42a67f5ed60c571c1e038ab5d1be4d81f6616a0987845030d18a53` | `improve6/code/ei6.py` |
| `multi_frozen/capbuild.py` | `bf36db53ed495653e8c919e493682f1b78290f5da62ff97f32e863c76dbcc7a6` | `improve6/code/capbuild.py` |
| `multi_frozen/packlib.py` | `7609204f704c9e3be50a00fd2e3e41883d18745a697fffa654a5f6fae7d58093` | `improve5/code/packlib.py` |
| `multi_frozen/scores.py` | `9b54242c52ad17188a71c9f83acfc722217fb10eac1aa4ec35384b4152d4ebb0` | `improve5/code/scores.py` |
| `multi_frozen/dlf.py` | `f2e9f3d2f92cfeb66db416b0d5efd39af62ca848beffbe2d628aa4a6a39cb5e1` | `improve5/code/dlf.py` |

Forward adaptations (the only differences from the tested runs, each forced by running forward):
1. **`capbuild_fwd.py`** is `capbuild.py` with one line changed: the fixed cut "share reports dated on or before 17 Nov 2026" becomes "on or before the decision date". Without it no share count reported after 17 Nov 2026 could ever be used.
2. **Cap level anchor.** As tested, each company's share history is scaled to the vendor's current market cap in its latest fundamentals file against the pack's last row. Forward, that last row is the fill day of the month being booked and the file is the latest one held (refreshed every 85 days). On the one month tested both ways this moved EI10I and CW values by 0.02–0.4%.
3. **Packs** are built from the forward store by `multi_build.py`, a port of the three tested builders (round 3 rules for Germany, France, Sweden, Canada; round 4 for Switzerland, Korea, Taiwan, Brazil; round 5 for ASX, Thailand, China, Finland, Poland, Belgium). The store holds only candidate companies (section 6), not the 1,200-name prefilter. One constant A$ scale per market is applied to all prices (round 3 had left German, French, Swedish and Canadian prices in local units), so that books are A$ equivalents.
4. **ASX** uses the same builder and A200 (EODHD `A200.AU`, adjusted close) as its fund. The tested ASX pack was built from the deep-dive bundle with the ASX 200 total-return index as fund. The ASX shadow M3 line (daily booking, cash dividends) continues unchanged and remains the canonical ASX M3 record; the ASX rows here exist so that ASX is pooled on the same footing as the other markets.
5. **Random controls** use scores that depend only on (seed, market, design, decision date, company code), so a control's past decisions do not change when the pack gains a month.
6. As tested, dividends are reinvested at no cost through the total-return price, fills are at the next session's adjusted close, and a stock that stops trading is paid out at its last close at the first month-end at least 20 trading days later.

## 3. Markets

Included with all three designs: the ten sets where report 77's computed cap-weighted index tracked the local index fund with a tracking error of 4 points a year or less. Included with **M3 only**: the four markets of M3's round-5 fresh-market looks whose cap data were not validated (China) or never built (Finland, Poland, Belgium). Not included: the UK, the Netherlands, Denmark, Spain, Norway, South Africa and the US bands (caps not valid, and no M3 look there). Adding a market later is a new card with its own clock.

| Market | EODHD exchange | Fund (EODHD symbol) | Fund handling | Builder rules | Local units per A$1 (constant) | Designs | Calendar |
|---|---|---|---|---|---|---|---|
| Australia (ASX) | AU | A200 (BetaShares Australia 200) (`A200.AU`) | adjusted close (distributions reinvested) | r5 | 1 AUD | M3, EI10I, CW | XASX |
| Germany (Xetra) | XETRA | EXS1 (iShares Core DAX) (`EXS1.XETRA`) | adjusted close (distributions reinvested) | r3 | 0.61 EUR | M3, EI10I, CW | XETR |
| France (Paris) | PA | CAC 40 tracker (`CAC.PA`) | adjusted close (distributions reinvested) | r3 | 0.61 EUR | M3, EI10I, CW | XPAR |
| Sweden (Stockholm) | ST | XACT OMXS30 (`XACT-OMXS30.ST`) | adjusted close (distributions reinvested) | r3 | 6.5 SEK | M3, EI10I, CW | XSTO |
| Switzerland (SIX) | SW | CSSMI (iShares SMI) (`CSSMI.SW`) | adjusted close (distributions reinvested) | r4 | 0.58 CHF | M3, EI10I, CW | XSWX |
| Canada (Toronto) | TO | XIU (iShares S&P/TSX 60) (`XIU.TO`) | adjusted close (distributions reinvested) | r3 | 0.9 CAD | M3, EI10I, CW | XTSE |
| Korea (KRX) | KO | KODEX 200 (069500) (`069500.KO`) | adjusted close (distributions reinvested) | r4 | 900 KRW | M3, EI10I, CW | XKRX |
| Taiwan (TWSE) | TW | Yuanta Taiwan 50 (0050) (`0050.TW`) | adjusted close (distributions reinvested) | r4 | 21 TWD | M3, EI10I, CW | XTAI |
| Thailand (SET) | BK | ThaiDEX SET50 (TDEX) (`TDEX.BK`) | adjusted close (distributions reinvested) | r5 | 22 THB | M3, EI10I, CW | XBKK |
| Brazil (B3) | SA | iShares Ibovespa (BOVA11) (`BOVA11.SA`) | distributions imputed (accumulating fund), as tested | r4 | 3.5 BRL | M3, EI10I, CW | BVMF |
| China (Shanghai + Shenzhen) | SHG+SHE | Huatai-PB CSI 300 (510300) (`510300.SHG`) | adjusted close (distributions reinvested) | r5 | 4.7 CNY | M3 | XSHG |
| Finland (Helsinki) | HE | Seligson OMX Helsinki 25 (SLGOMXH25) (`SLGOMXH25.HE`) | distributions imputed (accumulating fund), as tested | r5 | 0.61 EUR | M3 | XHEL |
| Poland (Warsaw) | WAR | Beta WIG20TR (ETFBW20TR) (`ETFBW20TR.WAR`) | distributions imputed (accumulating fund), as tested | r5 | 2.6 PLN | M3 | XWAR |
| Belgium (Brussels) | BR | BEL 20 tracker (`BEL.BR`) | adjusted close (distributions reinvested) | r5 | 0.61 EUR | M3 | XBRU |

The constant scales are round figures. A constant does not change any return; it sets what "A$25,000" and the A$-denominated thresholds (A$2,500 a name, A$1,000 minimum order, A$6.60 minimum brokerage, A$0.50 minimum price) mean locally. Currency moves are not modelled; every return is in local currency.

## 4. Clock and books

- **First decision:** each market's last session of November 2026 (Mon 30 Nov 2026 in all 14 calendars). Orders fill at the close of the next session (Tue 1 Dec 2026). Then every month-end.
- **Books:** A$25,000 and A$100,000 equivalents, no contributions, for every design in every market where it runs: 14 M3 + 10 EI10I + 10 CW = 34 design-markets, 68 books. Each is compared with the local fund bought with the same dollars on the same day.
- **Costs and tax, as in the looks:** brokerage max(A$6.60, 0.088%); half-spread 0.10% (traded-value rank ≤ 100), 0.25% (≤ 300), 0.50% otherwise, and on ASX at least half a tick; the fund 0.03% a side; tax at 32% on Australian rules (CL regime: 50% discount after 367 days, losses carried, financial year to 30 June), dividends taxed as income; foreign withholding, franking and currency not modelled.
- **Month-end and fill day are read from the data:** the last session of the month and the next session present in the store (the exchange calendar is only a first guess; China's published holidays end in 2026).

## 5. Job

`bigwins_forward/code/paper_multi.py`, run by a scheduled task at 04:17 UTC on days 1–8 of each month. It is idempotent (a month is booked once), resumable (a stopped run continues on the next run) and books the oldest unbooked month first. A month is booked when all 14 markets are complete, or on the 8th day of the following month with the markets that are (the others are recorded as a data block for that month).

## 6. Data and call budget

- `/api/user` is read first and every 300 credits; requests are paced at ≤ 280 credits a minute; the run stops before the day's usage would leave fewer than 15,000 credits of the daily limit spare.
- Each month and market: the vendor's symbol lists (2 calls); one bulk end-of-day file of the whole exchange for the month-end (`eod-bulk-last-day`, 100 credits; China 200), used to find every company traded heavily enough to matter; then end-of-day rows of each candidate (1 call each, incremental from 40 days before the last stored row, adjusted closes re-based on the overlap; a restated series is fetched again in full) and of the fund. Candidates = the 350 most traded common-stock lines on the bulk day ∪ the companies ranked ≤ 400 by 252-day median traded value last month ∪ every company held.
- Fundamentals (10 credits a file) only for the 100 universe companies of the ten cap markets, when the file is missing or more than 85 days old. If the plan stops serving fundamentals, the last share counts are carried forward and the scorecard says so.
- Bulk dividend and split files are not needed: the frozen engines read dividends and splits from the adjusted closes of the per-company files, exactly as in the tested packs. Daily bulk files for every exchange would cost about 60,000–80,000 credits a month for no change in any number.
- Every raw response is archived gzip-compressed under `fwd_multi/data/<market>/raw/<date>/` with `index.csv` (UTC time, kind, symbol, URL path and parameters without credentials, HTTP status, credits, bytes, SHA-256).
- Expected cost: about 6,900 credits a month (bulk files 1,500; symbol lists 28; about 5,300 incremental end-of-day files), plus about 10,000 credits when the share-count files fall due (every 85 days; first due February 2027), about 10,000 a month on average and at most about 17,000 in one day (well under the 100,000 daily limit less the 15,000 kept spare). Measured in the live test of 18 Nov 2026: one-time bootstrap 7,046 credits (14 markets, already done; the store is kept), one further month 1,738.

## 7. Scoring (monthly)

For each design, size and market: the monthly lead = design book return − fund book return over the month, before tax and after costs; the after-tax value if both were sold at the month-end (32%, CL), and the after-tax lead (cumulative before 12 months, a year after); the percentile of the design's after-tax value among **100 random-portfolio controls** run through the same machine (seeds 1000–1099; M3: random scores in M3's structure; EI10I and CW: the cap-weighted book tilted by random scores).

**Pooled** (the main reading): the equal-weight mean across markets of the monthly lead, per design and size; its t-statistic and deflated Sharpe ratio (Bailey and López de Prado, the round-5/6 function) at **N = 1,649** trials; the mean after-tax lead across markets and the count of markets ahead; the pooled control percentile (the design's mean after-tax excess over the fund against the same mean for each control seed).

Outputs each month: `68_forward_record/multi/SCORECARD_MULTI.md` (first line: "PAPER … Not shown to beat the index"), `history_multi.csv` (append-only; a month is never rewritten), `orders_<YYYY-MM>.csv`, and one ledger entry with the SHA-256 of those files and of the code.

## 8. Adopt and stop rule

No formal reading before 36 months. Formal readings are made only at December month-ends (first possible: 31 Dec 2029).

**Adopt bar (all required, for one design, at BOTH A$25,000 and A$100,000):**
1. pooled monthly lead t ≥ 3.0;
2. deflated Sharpe ratio ≥ 0.95 at N = 1,649 (for normal returns this needs t ≈ 5.0 — the binding condition);
3. pooled after-tax lead ≥ +1.0 point a year;
4. pooled control percentile ≥ 0.90;
5. more than half the markets ahead of their fund after tax.

Meeting the bar allows a written real-money proposal only. Under the spec the owner decides; nothing is switched on by the record.

**Stop bar (per design and size):** at a December review from 13 months on, pooled t ≤ −2.0; or, from 60 months on, a pooled after-tax lead of −1.0 point a year or worse. A stopped line is closed and reported; it is not re-tuned (a changed design is a new card with its own clock).

**Record-level stops:** a broken ledger chain not explained within 20 trading days; two data blocks in 12 months for the same market (that market is dropped from the pool from then on, and says so); the owner no longer reads the scorecard.

## 9. Trial count

The 34 design-markets are pre-registered forward lines of designs already counted; they add no trials. N stays 1,649 for the deflated Sharpe ratio. Report 78's power analysis and builder checks are not trials.

## 10. Code hashes (SHA-256 at registration)

| File (under `bigwins_forward/code/`) | SHA-256 |
|---|---|
| `multi_build.py` | `024d206e5d3c10d28e905855acbb9ee2e08482d9a1a5d18dfe0bd01b6f56fc44` |
| `multi_engine.py` | `fea06dffd717e14f929b73d71e87ec5f255d416d99151d2e13ae0ed4ba1a6cb5` |
| `multi_frozen/capbuild_fwd.py` | `28c370b17ca95469fa94ff00bb4d49763d2820c7f0ea336f6b189f4f4171f3ba` |
| `multi_frozen/dlf.py` | `f2e9f3d2f92cfeb66db416b0d5efd39af62ca848beffbe2d628aa4a6a39cb5e1` |
| `multi_frozen/ei6.py` | `fe2365960e42a67f5ed60c571c1e038ab5d1be4d81f6616a0987845030d18a53` |
| `multi_frozen/packlib.py` | `7609204f704c9e3be50a00fd2e3e41883d18745a697fffa654a5f6fae7d58093` |
| `multi_frozen/scores.py` | `9b54242c52ad17188a71c9f83acfc722217fb10eac1aa4ec35384b4152d4ebb0` |
| `multi_frozen/sim6.py` | `f9efc4bc01ecf5ebb4ed1cbdbbe167e2903e3b611a5468642b737b7d474e1692` |
| `paper_multi.py` | `2892f30f5bf658300c301870bd0b66c707689aadfcdd6eeda102d7a04c231a75` |

A change to any of these files after registration is recorded in its own ledger entry with the reason; a change to a frozen engine file stops the job (it checks the hashes).
