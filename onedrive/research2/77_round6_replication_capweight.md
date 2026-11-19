# 77. Round 6 — blind replication of M3, a true cap-weighted reference, and the twelve-set fundamentals look

17 November 2026. Research and paper only. General information, not financial or tax advice. Nothing here can place an order.
Work folder: `scratchpad/improve6/` (`PREREG_77.md`, `code/`, `out/`, `data/`, `PROGRESS.md`). Trial ledger: `out/trials_77.csv` (cumulative count 1,543 → 1,649). Nothing was written to `68_forward_record/` or `bigwins_forward/`.

## 0. Plain-English verdict

**Nothing passed. Real money stays in the 40/60 plan.** Three pieces of work were done; each has a clear answer.

1. **M3 was rebuilt blind from its written rules, and the engine is sound.** A second engine written from report 76's rule text alone, before the original code was opened, landed within 0.1 point of report 76 at A$100,000 in both Thailand and China. Once five modelling choices were lined up, the two engines agree to a dollar or two over nine years. No arithmetic bug was found. Report 76's look figures and the ASX owner-account figure (A$78,220 against A$86,763 for the fund) are reproduced.
2. **Three real faults were found around it.**
   - **The ASX development pack was broken, and it flattered M3 at home.** From December 2024 every company in it has a traded value of zero, so the engine bought nothing for 23 months. Report 76 showed M3 on ASX at +1.7 / +0.4 points a year over the fund for 2023–26. On the corrected pack it is **−5.3 / −2.5**, and over the whole window +1.3 / −0.5 instead of +3.6 / +1.5. ASX is no longer a market where M3 was ahead.
   - **Rule R7 does not describe what was tested.** The text says a holding may stay while it is among the 150 most traded. The code sells it once it leaves the top 100. The 150 version is worse (China +1.0 instead of +2.2 at A$100,000). The paper shadow line happens to follow the tested behaviour already; section 2 lists three smaller points where it does not.
   - The fund in the comparison paid its tax with interest-free borrowing, and dividends were reinvested at no cost. Both shortcuts work slightly against M3, so the round-5 look was not inflated by them.
3. **A true cap-weighted reference can now be built, and it works in about half the markets.** With share counts from the fundamentals files, a computed cap-weighted index tracked the local index fund within 1.9–3.1 points of tracking error a year in ASX, Germany, France, Switzerland, Canada, Korea and Taiwan (equal weighting: 6–17 points). It did not track in the UK, the Netherlands, Denmark, South Africa, China or any US band, because of missing or wrong share counts and survivor bias.
4. **The cap-weighted book removes the structural handicap.** A direct book of up to 30 names at cap weights, with no picking at all, was level with the fund on the eight development markets (+0.7 point a year over 2018–26, no cell below −2). Random equal-weighted picks lost about 2 points in round 5. This confirms round 4's diagnosis.
5. **The enhanced index built on it did not beat the fund in the look.** The design (EI10I: cap weights tilted by momentum and low share issuance, frozen and hashed before any fundamentals return on the twelve sets) led the fund by **+0.1 / +0.6** points a year on average. It met the +1 bar at both sizes in **3 of 12** sets (7 needed), beat 90% of random-tilt books in 4 of 12 (7 needed), and passed the top-five-names test in none. The tilt added nothing reliable to the plain cap-weighted book (ahead of it at both sizes in 4 of 12).
6. **The owner's account.** A$5,000 plus A$500 a month (A$57,500 paid in) ended ahead of the local fund in 8 of 12 sets, by A$4,000–15,000, and behind in 4. It ended above the 40/60 plan's A$98,662 only in the five sets where the local index fund alone also did (US large, Korea, Taiwan, Spain, Norway).
7. **Honest status of this look.** The prices of all twelve sets were development data; only the share counts were new. A mistake of mine left the US mid and small books empty in the frozen run; it was fixed after the look and both versions are shown. The verdict is the same either way.
8. **What to do.** (a) Amend rule R7 and three smaller points before the M3 shadow line's first decision on 30 November (section 2). (b) Do not start a paper line for the enhanced index. (c) The fundamentals subscription has done its job: all 5,648 raw company files are archived, and neither issuance nor quality has earned a place. (d) Only the forward paper record adds clean evidence from here.
9. **Confidence.** High that nothing here meets the bar. High that the M3 engine is arithmetically right and that the ASX pack fault is real. Moderate that cap weighting removes most of the structural drag (seven tracked markets, development prices). Low that any tilt tested so far adds to it.

---

## 1. Blind replication of M3

### 1.1 What was done

- A second engine was written from the rule text of report 76 section 6 and the cost and tax lines of `PREREG_76.md` alone (`code/blind_m3_v1_frozen.py`). Nothing in `improve5/code/` was opened until its first figures were on disk and hashed (`out/blind_look_v1.json`, `out/blind_owner_ASX_v1.json`, `out/blind_v1_hash.txt`).
- The original code was then opened. Each modelling choice on which the two engines differed became a switch in the new engine (`code/m3v2.py`), and the two were compared trade by trade (`code/cmp4.py`, `cmp5.py`; `code/sim5_dbg.py` is the original with a trade log added).
- The score inputs were recomputed from the raw Thai price download for six dates (`code/sigcheck.py`): the 6-month and 52-week-high figures match the pack for all 557 company-dates and the 12-month figure for 99% of them (median difference zero).

### 1.2 Result: the engine arithmetic is confirmed

Lead over the local fund, points a year after tax, A$25,000 / A$100,000 (mean of four start months); owner account in A$.

| | Report 76 | Blind build, first run (rule text only) | New engine with the original's modelling choices |
|---|---|---|---|
| Thailand, lead | +2.5 / +1.6 | +2.0 / +1.6 | +2.7 / +1.7 |
| Thailand, fund after tax, % a year | 1.01 | 0.87 | 1.01 |
| Thailand, owner account, design / fund | 62,034 / 67,643 | 57,059 / 67,994 | 62,035 / 67,129 |
| China, lead | +2.9 / +2.3 | +1.1 / +2.3 | +2.6 / +2.2 |
| China, fund after tax | 1.66 | 1.65 | 1.66 |
| China, owner account | 58,412 / 58,173 | 56,316 / 58,183 | 58,764 / 57,776 |
| ASX owner account, current law with franking, M3 / fund | 78,220 / 86,763 | 79,227 / 86,504 (franking guessed at 70%) | 79,876 / 86,763 (78,303 with the original's franking split) |
| ASX owner account, no franking, M3 / fund | 80,281 / 82,957 | 71,840 / 82,721 | 80,274 / 82,956 |
| ASX A$100,000 lump sum, no franking, M3 / fund | 171,936 / 185,145 | 183,602 / 179,316 | 171,936 / 185,145 |

- On account paths with no knife-edge event the two engines agree to a dollar or two over nine years: Thailand A$25,000 December start A$34,020 against A$34,022; Thailand owner account A$62,034 against A$62,035; ASX lump sum A$171,936 on both.
- At A$100,000 the blind first run was already within 0.1 point in both markets.
- **No bug was found in the original engine's arithmetic** (costs, parcels, the 12-month discount, loss carry-forward, the deferral rule, payouts).

### 1.3 Every difference above 0.2 point, and whose it was

| # | Difference | Size | Whose | What it is |
|---|---|---|---|---|
| 1 | Satellite size on the first day | Thailand A$25k: +0.4; pre-tax +2.2 | **mine** (rule text ambiguous) | R6 says "satellite = account − fund". On day one the fund is empty, so I sized positions on the whole account. The original buys the fund first and sizes on what is left. The original is the sensible reading; R6 needs the words "after the fund has been brought to 50%" |
| 2 | Dividends | Thailand +0.4 / +0.4, China +0.3 / +0.3 in the design's favour when paid in cash | modelling choice, **original** | The original reinvests every dividend in the same share at no cost and adds it to the cost base. In life a dividend arrives as cash and goes where the rules send cash. The rules do not say which. Paying cash raised M3's lead a little, so the original is the conservative version |
| 3 | The fund pays its tax with borrowed money | Thailand fund 1.01% → 0.83–0.88% a year; China no change | modelling shortcut, **original** | In the fund-only comparison the yearly tax bill is taken from a cash balance that is already zero, so cash goes negative, interest-free, to the end. This flatters the fund by 0.1–0.2 point a year where dividends are high. It works against the design, so no result was inflated |
| 4 | Fund bought before the month's share sales | under 0.1 | rule text, **original** | R2 "free cash goes to the fund first" is applied before that month's sales, so sale proceeds reach the fund a month later. Takeover proceeds do go to the fund first. I had the order wrong for takeover cash (mine) |
| 5 | Top-ups | under 0.1 at A$100k | rule text, **original** | The code tops up holdings only when the book is full. R8 does not say so |
| 6 | Takeover payout date | one position on ASX (OZ Minerals) | **mine** | I paid out more than 20 trading days after the last close; the rule says "at least 20" |
| 7 | Monthly contributions | A$500 | **mine** | I added one contribution too many (on the final day) |
| 8 | Fund half-spread 0.03% (original) against 0.10% (mine); whole shares; 367 days for the discount | under 0.1 each | choices; text silent | — |
| 9 | **"Holding may stay while it is among the 150 most traded"** | see 1.4 | **original: text and code disagree** | `PREREG_76.md` and R7 describe a 150-name hold zone. The code never ranks a company outside the 100 most traded (the extension in `lib5.rank_ext` receives no scores and does nothing), so a holding that leaves the top 100 is unranked and sold after two months. Every M3 number in report 76 is the 100-name version |
| 10 | Knife edges | A$25k cells: ±0.3–0.5; owner account ±A$3,000–5,000 | neither | n = floor(satellite ÷ A$2,500) changes by one name on an A$8 difference in valuation (China, January 2020: 6 or 7 names; one then bought a share the day before it fell 10%). The A$1,000 minimum order meets a balance of exactly A$1,000 after two A$500 contributions, and is decided by the last digit of a rounding error. These explain the remaining gaps at A$25,000 (China +2.6 against +2.9) and in the owner accounts |

### 1.4 What the replication changes

1. **The hold zone that was written down is worse than the one that was tested.** With holdings truly allowed to stay to traded-value rank 150 (as R7 and the pre-registration say), M3's lead falls at A$100,000 from +1.7 to +1.3 in Thailand and from +2.2 to +1.0 in China, and the ASX lump sum falls from A$190,000 to A$179,000. The tested rule ("leaves the 100 most traded → unranked → sold after two month-ends") is the one with a record. R7 must say 100, not 150. The ASX snapshots already list only the 100 universe names, so a paper record that follows the snapshot is consistent with the tested code.
2. **The most realistic settings do not hurt M3.** Dividends in cash and a fund that pays its own tax: Thailand +3.5 / +2.0, China +2.8 / +2.5 (report 76: +2.5 / +1.6 and +2.9 / +2.3). The round-5 look was not flattered by the engine.
3. **The owner-account figure is one draw from a wide range.** After tax the ASX owner account ended between A$76,500 and A$88,700 across six equally defensible settings (dividends cash or reinvested, franking on or off, hold zone 100 or 150). In five of the six it finished behind the fund (A$83,000–87,000). Report 76's A$78,220 is reproduced (A$78,303), and "M3 trails the fund in the owner's account" stands, but the A$8,500 gap is not a precise number.
4. **A data bug was found in the ASX development pack, and it flattered M3 at home.** `improve/data/pack_ASXv2_M.npz`, the ASX set of reports 73–76, has a traded value of zero for every company from December 2024. From then on its "100 most traded" are the first 100 codes in alphabetical order and nothing passes the purchase test, so the engine buys nothing for 23 months. Report 76's ASX rows reproduce exactly on that pack. On the EODHD total-return pack (v1.4 traded-value fix), which has no such fault:

| M3 on ASX, lead over the fund, A$25k / A$100k | Report 76 (faulty pack) | Corrected pack |
|---|---|---|
| 2016 – Dec 2022 | +6.5 / +2.6 | +5.5 / +1.1 |
| 2023 – Oct 2026 | +1.7 / +0.4 | **−5.3 / −2.5** |
| Whole window | +3.6 / +1.5 | +1.3 / −0.5 |
| Sep 2024 – Oct 2026 only | +2.6 / +1.2 | −11.4 / −2.9 |

   The bug is the original's (the pack was built in round 3 and reused). It does not touch any fresh-market look, the ASX owner-account figure (computed on the corrected pack) or any other market: all 20 other packs were checked (`out/asx_pack_check.log`). It does remove ASX from report 76's list of markets where M3 was "clearly ahead", and it lowers the in-pool check from 13 to 12 of 18 market-sets ahead.

## 2. Correction needed for the M3 paper shadow line

`bigwins_forward/code/paper_shadow.py` was read (not edited). It was built from report 76's rule text. The rule the shadow should follow, so that it matches what was tested on Thailand and China, is the behaviour of `improve5/code/sim5.py` with `look5.py`'s `M3` settings. Point by point:

| Rule | What was tested (the shadow should do this) | What `paper_shadow.py` does now | Change needed? |
|---|---|---|---|
| **R7(a) hold zone** | A holding is "bad" at a decision day if it is not among the 100 universe companies with a score, or its rank is worse than 50. Two bad decision days in a row → sold (subject to the 12-month gain deferral). There is no 150 zone | `bad = r is None or r > 50 or v_ is None or v_ > 150`. Because only the 100 universe names have a rank, a holding outside the top 100 already has `r is None` and is bad. The `> 150` clause can never bind | **No change in behaviour.** Delete the `v_ > 150` clause and correct the rule text so nobody later "fixes" the code to match the text |
| **R2 fund first** | On a decision day the fund order is sized from free cash before that day's share sales: min(50% of account − fund value, cash − tax owed), if A$1,000 or more. Takeover and delisting proceeds are already in cash and count. Sale proceeds of the same day go to shares, and reach the fund a month later | `fund_buy = min(0.5 × nav − fv, free_cash + proceeds)`: the day's sale proceeds are offered to the fund first | **Yes.** Use `free_cash(b, d)` without `proceeds` |
| **R6 satellite** | Satellite = account − fund value after the fund order above (and after the sell-down to 50% on the day the small-account rule ends). n and the target are set from that | Same (`sat = nav − (fv − fund_sell + fund_buy)`) | No. Rule text should say "after the fund has been brought towards 50%" |
| **R8 top-ups** | Only when the book is full after the day's purchases (names held ≥ n). Then holdings ranked 50 or better and under 75% of target are topped up, smallest first, if the top-up is A$1,000 or more | `if line == 'M3' or cnt >= n`: M3 tops up whether or not the book is full | **Yes.** Use `cnt >= n` for M3 too |
| **R3 fund-only phase** | While the account is below A$25,000 and no shares are held, free cash goes to the fund in orders of A$1,000 or more (the very first purchase may be any size) | orders of A$100 or more | **Yes** (A$1,000), minor |
| **R7(c) trim, parcel age** | parcels held 367 days or more are sold first | 366 | trivial; align to 367 |
| Dividends and fund distributions | reinvested at no cost in the back-test | paid as cash | **Keep the paper version.** Cash is what happens in life; the back-test shortcut cost M3 about 0.3 point |
| R7 gain deferral, R7(b) May rule, R8 purchase tests, R10 payout after 20 trading days, tax reserve, 367-day discount | — | same as tested | No |

Rule-text corrections for M3 v1.1 (no change to the tested design):
- **R2** add: "The fund order is sized before the day's share sales, from cash already in the account."
- **R6** replace the first sentence with: "Satellite = account value − fund value after the day's fund order."
- **R7(a)** replace "or that has no rank or has left the 150 most traded" with "or that has no rank (it is no longer among the 100 universe companies, or a score input is missing)".
- **R8** add before the top-up sentence: "If the book is full (n names held) …".

## 3. A true cap-weighted reference

### 3.1 How market caps were built (`code/capbuild.py`)

- Share count: the vendor's quarterly `outstandingShares`, annual rows where there is no quarterly row, balance-sheet share counts after the last such row. Usable 90 days after the period end; dropped after 800 days.
- **Splits.** Most share histories are restated to today's units, some are not, and some are mixed. Where the price file shows a split and the share history steps by the same factor, earlier counts are restated.
- **Garbage quarters.** Each count is replaced by the median of the last five reports known at the time (Royal Bank of Scotland's file reads 12.5, 3.2, 13.5, 7.4 bn in four consecutive quarters).
- **Wrong level.** A file whose latest cap is out by ×3 or more against the vendor's own current market cap is dropped (0–9 files a market; about 1.5% of live files). The others are scaled to it, which absorbs share classes.
- **Foreign lines and absurd counts.** A cap is void in any month in which yearly traded value ÷ cap is below 10% (Amazon's Frankfurt line carries Amazon's whole cap) or above 500%.
- Files that still hold an unexplained ×3 step between reports: 0–27% by market (ASX 23%, US 19%, Norway 27%, Taiwan under 1%). Report 76's "1–7%" was the share of live files with the wrong current level; the histories are worse than that.

### 3.2 Does the computed index track the fund? (Dec 2018 – Oct 2026; look sets Dec 2019 – Oct 2026)

Monthly-rebalanced cap-weighted book of the N largest among the 100 most traded, against the local fund's total return, before costs and tax.

**Development markets**

| Market | Files with share counts | Share of the 100 most traded with a usable cap | Fund, % a year | Cap-weighted top N (N) | Gap | Tracking error, cap-weighted | Equal weight | Traded-value weights (report 75 proxy) | Valid (TE ≤ 4.0)? |
|---|---|---|---|---|---|---|---|---|---|
| ASX | 257 of 268 | 92% | 10.1 | 11.3 (100) | +1.2 | 2.3 | 5.7 | 3.5 | yes |
| UK | 168 of 270 | 84% | 8.9 | 5.9 (100) | -3.0 | 5.7 | 6.7 | 14.6 | **no** |
| Germany | 187 of 197 | 85% | 11.4 | 10.9 (40) | -0.6 | 2.3 | 6.2 | 4.1 | yes |
| France | 149 of 170 | 93% | 9.9 | 9.2 (40) | -0.7 | 2.5 | 7.6 | 3.2 | yes |
| Sweden | 206 of 220 | 89% | 12.2 | 12.7 (30) | +0.6 | 3.6 | 8.2 | 4.3 | yes |
| Netherlands | 144 of 182 | 68% | 13.8 | 13.4 (25) | -0.3 | 5.0 | 10.2 | 6.2 | **no** |
| Switzerland | 151 of 161 | 92% | 10.8 | 10.4 (20) | -0.5 | 1.9 | 8.7 | 2.5 | yes |
| Canada | 200 of 243 | 96% | 15.6 | 14.7 (60) | -0.9 | 2.1 | 7.4 | 18.5 | yes |

**Look sets** (computed after the freeze)

| Market-set (fund) | Share of the 100 most traded with a usable cap | Fund, % a year | Cap-weighted top N (N) | Gap | Tracking error, cap-weighted | Equal weight | Traded-value weights | Validated (TE ≤ 4.0)? |
|---|---|---|---|---|---|---|---|---|
| US large | 75% | 16.9 | 19.9 (100) | +3.0 | 5.7 | 8.8 | n/a | **no** |
| US mid | 82% | 12.3 | 13.9 (100) | +1.6 | 6.9 | 6.3 | 6.3 | **no** |
| US small | 77% | 11.1 | 11.0 (100) | -0.0 | 10.1 | 8.4 | 8.5 | **no** |
| Korea | 90% | 19.4 | 18.4 (100) | -1.0 | 3.1 | 16.8 | 8.6 | yes |
| Taiwan | 77% | 28.4 | 29.0 (50) | +0.5 | 2.6 | 14.3 | 14.3 | yes |
| Thailand | 96% | 2.7 | 3.8 (50) | +1.0 | 3.8 | 9.7 | 4.7 | yes |
| China | 62% | 4.7 | 4.6 (100) | -0.1 | 7.3 | 16.2 | 17.1 | **no** |
| Brazil | 83% | 8.9 | 10.9 (80) | +1.9 | 3.9 | 9.2 | 5.5 | yes |
| Denmark | 61% | 10.8 | 10.4 (25) | -0.4 | 10.7 | 8.2 | 6.7 | **no** |
| Spain | 76% | 14.3 | 14.6 (35) | +0.4 | 5.3 | 9.2 | 5.4 | **no** |
| Norway | 82% | 13.7 | 15.4 (25) | +1.7 | 4.3 | 11.1 | 5.9 | **no** |
| South Africa | 86% | 13.9 | 16.2 (40) | +2.3 | 10.0 | 9.8 | 5.0 | **no** |

- **Valid (tracking error of 4 points or less): ASX, Germany, France, Sweden, Switzerland, Canada, Korea, Taiwan, Thailand, Brazil.** In seven of them the error is 1.9–3.1 points, against 6–17 for equal weights and 2.5–18 for report 75's traded-value proxy.
- **Not valid:** UK (share counts in 168 of 270 files), Netherlands (68% coverage; the AEX caps a company at 15%), Denmark (61%), South Africa (dual-listed giants), China (the 500% turnover ceiling voids a third of the most-traded names), Spain, Norway (4.3), and all three US bands. In US large the computed index earned 19.9% a year against 16.9% for the fund: only 4–6% of the companies that later left the file have share counts, so the US caps are a survivors' list.
- Full market cap is used; the funds use free float. That alone costs a point or two of tracking error.

### 3.3 The enhanced index: development (eight markets, `out/dev6v2.log`)

Structure: no fund; up to 30 names (one per A$2,500); the best-ranked by tilted weight among the 100 most traded; weights proportional to tilted cap, 20% ceiling; a holding is sold after two month-ends below rank 45; no gain sold before 12 months; no other rebalancing. Tilted weight = cap × (1 + a × (2p − 1)), p = score percentile. Lead over the fund after tax, points a year, mean of both sizes.

| Config | To Dec 2022: mean / markets ahead / cells below −2 | 2023–26: mean / ahead | Whole 2018–26: mean / ahead / cells below −2 | Tracking error | Turnover |
|---|---|---|---|---|---|
| M3 (round 5; 50% fund + 15 equal-weighted names) | +0.44 / 5 of 8 / 2 of 16 | +0.15 / 4 | −0.29 / 3 / 3 | 5.2 | 0.39 |
| **CW**: cap weights, no tilt | +0.56 / 4 / 3 | −0.30 / 5 | **+0.66 / 5 / 0** | 4.0 | 0.22 |
| EI10: cap × M3 tilt (a = 1) | +0.77 / 5 / 1 | +0.52 / 4 | +0.25 / 5 / 1 | 4.6 | 0.29 |
| EI20: a = 2 | +0.60 / 5 / 1 | +1.42 / 6 | +0.60 / 6 / 1 | 5.6 | 0.51 |
| **EI10I**: cap × tilt on M3 + low issuance | **+1.79 / 6 / 0** | +0.70 / 5 | +0.83 / 6 / 0 | 4.4 | 0.26 |
| EI10 with 50% fund | +0.35 / 5 / 2 | +0.20 / 5 | +0.06 / 4 / 0 | 2.6 | 0.14 |
| EI20 with 50% fund | +0.08 / 5 / 1 | +0.78 / 6 | +0.06 / 6 / 1 | 3.1 | 0.24 |
| M3 + low issuance (M3 structure) | +0.29 / 5 / 2 | +0.78 / 5 | +0.23 / 5 / 1 | 3.6 | 0.25 |

By market, A$25k / A$100k, whole window: CW — ASX +3.6 / +2.4, UK −1.3 / −1.2, Germany −0.7 / −1.3, France +1.8 / +0.6, Sweden +2.0 / +0.6, Netherlands +3.4 / +2.6, Switzerland +0.7 / −0.5, Canada −1.2 / −0.8. EI10I — ASX +2.2 / +1.1, UK +1.1 / +2.0, Germany −0.3 / −0.9, France +1.4 / +0.8, Sweden +2.4 / +0.7, Netherlands +2.0 / +1.4, Switzerland +1.1 / −0.1, Canada −0.9 / −0.8.

- **Cap weighting closes the gap that sank rounds 1–5.** With no picking, the direct book is within about ±1 of the fund on average and has no cell below −2 over the whole window. Random equal-weighted picks in M3's structure lost about 2 points.
- Part of CW's +0.7 is not real: where the computed index itself beats the fund (ASX +1.2 a year) the book inherits it from survivor bias and full-cap weights.
- **M3 on the corrected ASX pack is −0.3 over the whole window on these eight markets,** not ahead.
- EI10I was best on the windows to 2022 and was chosen. Its extra over CW was +1.2 to 2022, +1.0 in 2023–26 and +0.2 over the whole window. The pre-registration said to expect 0 to +0.5.
- Two faults of my own were caught by the data check on the first downloaded look markets, before any return there: the turnover screen mixed pack units with local currency (wrong on rescaled packs), and Korean share histories stop in 2020 unless balance-sheet counts extend them. Both were fixed and all ten configurations re-run (the first run is kept in `out/v1_unitbug/`; the choice did not change).

## 4. The twelve-set look (`PREREG_77.md`, SHA-256 `b98d914b…f08e8302`, frozen 09:15 UTC at N = 1,565)

### 4.1 What kind of test this is

- Sets: US large, mid and small, Korea, Taiwan, Thailand, China, Brazil, Denmark, Spain, Norway, South Africa. 3,246 fundamentals files were downloaded for them (every company among the 100 most traded at any month-end from December 2018).
- **Their prices are development data.** Every set was used in rounds 3–5, and M3's momentum score was frozen with all of them in view. What had never been computed on them is anything that needs a share count: market caps, cap weights, issuance. So the cap-weighted structure and the issuance half of the tilt are tested fresh here; the momentum half is not. This is weaker than a fresh-market look.
- Window: four starts (Dec 2019, Mar, Jun, Sep 2020) to 30 Oct 2026, as report 76 section 8.6 laid down. It is 6.8 years and starts just before the 2020 crash.
- One design, EI10I, frozen with its code, data and data-check table before any fundamentals-based return on these sets. Stated expectation: a lead of 0 to +0.5 with a spread of ±3, and the bar not met.
- **A mistake of mine in the frozen code.** For the two US band sets (mid, small) the ranking also counted companies traded above the band. They filled ranks 1–30 and cannot be bought, so the books stayed empty: the frozen run shows US mid −5.6 / −5.6 and US small −11.8 / −11.8, which is cash against the fund. The pre-registration text (universe = the band's own 100 names) was unambiguous, so the code was corrected after the look, the US large result was checked to be identical to the last digit, and the two sets were re-run. Both versions are given. The frozen files are in `out/look_asfrozen/` and the frozen code in `code/ei6_frozen.py`. The other ten sets were not touched.

### 4.2 Result

X = after-tax return of the design minus the fund's, points a year, mean of four starts. "Random-tilt percentile" = rank of the design's after-tax return among 100 books of the same structure whose tilt is driven by random scores. t and DSR are for the monthly lead before tax, December start, A$100,000.

| Market-set | Lead after tax 25k / 100k | Range over 4 starts (100k) | Lead before tax 25k / 100k | Design / fund, % a year after tax (100k) | Random-tilt percentile 25k / 100k | Top 5 share of profit | Tracking error | t | DSR | Worst fall, design / fund | Turnover | Names 25k / 100k | Cap index tracks fund? (TE) | Owner account: design / fund |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| US large | +2.4 / +1.9 | +1.1 to +3.3 | +2.5 / +2.1 | 16.6 / 14.7 | 68 / 80 | 66% | 6.3 | 1.6 | 0.03 | -30 / -24 | 0.34 | 11 / 24 | no (5.7) | 117.5k / 108.1k |
| US mid | +0.4 / +0.1 | -0.7 to +1.3 | +0.4 / +0.3 | 12.0 / 11.9 | 91 / 91 | 69% | 9.5 | 0.4 | 0.00 | -29 / -30 | 0.49 | 10 / 21 | no (6.9) | 92.4k / 88.5k |
| US small | -0.2 / -1.0 | -1.4 to -0.5 | -1.8 / -1.1 | 10.8 / 11.8 | 92 / 78 | 57% | 12.6 | -0.3 | 0.00 | -27 / -33 | 0.54 | 9 / 22 | no (10.1) | 90.7k / 84.8k |
| Korea | -1.3 / -0.7 | -1.5 to +0.7 | -2.3 / +0.5 | 19.4 / 20.0 | 98 / 100 | 88% | 5.8 | 0.8 | 0.00 | -31 / -34 | 0.50 | 10 / 27 | yes (3.1) | 137.8k / 143.4k |
| Taiwan | -1.9 / -1.9 | -3.1 to -0.5 | -1.2 / -0.8 | 25.3 / 27.2 | 93 / 98 | 76% | 7.0 | -0.0 | 0.00 | -29 / -29 | 0.47 | 10 / 23 | yes (2.6) | 182.0k / 200.4k |
| Thailand | +0.3 / +3.7 | +3.5 to +4.0 | +1.2 / +3.9 | 8.3 / 4.5 | 15 / 82 | 181% | 4.5 | 2.1 | 0.12 | -28 / -28 | 0.29 | 9 / 22 | yes (3.8) | 75.5k / 67.6k |
| China | -1.3 / +0.3 | -0.2 to +0.8 | -0.3 / +0.7 | 0.2 / -0.2 | 50 / 51 | n/a (no profit) | 9.6 | 0.3 | 0.00 | -41 / -38 | 0.39 | 9 / 20 | no (7.3) | 57.9k / 58.2k |
| Brazil | +5.4 / +3.1 | +2.1 to +5.2 | +7.2 / +4.2 | 11.1 / 8.0 | 100 / 100 | 129% | 8.3 | 1.6 | 0.04 | -35 / -39 | 0.31 | 10 / 19 | yes (3.9) | 91.5k / 81.8k |
| Denmark | +1.6 / +2.3 | +1.5 to +3.9 | +2.3 / +3.0 | 8.9 / 6.6 | 73 / 60 | 89% | 4.7 | 1.5 | 0.03 | -24 / -26 | 0.23 | 12 / 19 | no (10.7) | 83.5k / 76.1k |
| Spain | -1.8 / +0.6 | -0.2 to +1.6 | -1.2 / +1.8 | 17.4 / 16.8 | 5 / 91 | 67% | 6.4 | 0.7 | 0.00 | -26 / -32 | 0.32 | 10 / 23 | no (5.3) | 130.0k / 115.2k |
| Norway | -1.7 / -0.8 | -2.0 to +1.8 | -1.5 / +0.0 | 13.4 / 14.2 | 76 / 25 | 95% | 4.8 | -0.2 | 0.00 | -21 / -24 | 0.27 | 8 / 17 | no (4.3) | 106.8k / 99.8k |
| South Africa | -0.5 / -0.4 | -0.6 to -0.3 | -0.3 / +0.2 | 13.3 / 13.7 | 32 / 44 | 65% | 5.3 | 0.2 | 0.00 | -22 / -21 | 0.43 | 12 / 25 | no (10.0) | 95.8k / 98.5k |

| Bar (all required) | Result (US mid and small corrected) | Result as frozen | Met? |
|---|---|---|---|
| 1. X ≥ +1.0 at both sizes in 7 or more of 12 sets | 3 (US large, Brazil, Denmark) | 3 | **no** |
| 2. X below −2.0 in no more than one set | none | 2 (the two empty books) | yes / no |
| 3. At or above the 90th percentile of random-tilt books at both sizes in 7 or more | 4 (US mid, Korea, Taiwan, Brazil) | 4 | **no** |
| 4. Top five positions under 50% of profit (A$100,000) in 7 or more | 0 | 0 | **no** |
| 5. Deflated Sharpe ratio at N ≈ 1,570–1,650 (usual line 0.95) | highest 0.12 (Thailand); 0.00–0.04 elsewhere | same | far below |
| Mean lead, A$25k / A$100k | +0.1 / +0.6 | −1.3 / −0.7 | |
| **Verdict** | | | **not adopted** |

What the numbers say:

1. **The design did not beat the fund.** Ahead on average in 5 of 12 sets, at +1 or better at both sizes in 3. The three are US large (where the cap data are a survivors' list, see 3.2), Denmark (61% coverage, not validated) and Brazil.
2. **On the four sets with validated cap data** (Korea, Taiwan, Thailand, Brazil) the leads were −1.3 / −0.7, −1.9 / −1.9, +0.3 / +3.7 and +5.4 / +3.1. One of four met the +1 bar at both sizes.
3. **Giants still win where they drive the index.** Korea and Taiwan, the two markets round 5 named, are still behind (−1 and −2), even with the giants held at cap weight. The 20% ceiling on one name is the reason: TSMC is about half of the Taiwan fund and Samsung a quarter to a third of Korea's. A small direct book cannot hold them at index weight and stay diversified.
4. **The top-five test cannot be passed by a cap-weighted book.** The five largest profits are simply the largest companies (Apple, Nvidia, Alphabet twice and Microsoft made 66% of the US large profit). The test was written for equal-weighted pickers. It was pre-registered and it failed; it says little here.
5. **Risk was similar to the fund's.** Worst falls were within a few points of the fund's in 11 of 12 sets (US large: −30% against −24%). Tracking error 4.5–12.6 points; turnover 0.23–0.54 a year.
6. **By year** (mean lead before tax, A$100,000, December start): 2020 +3.0, 2021 +2.0, 2022 0.0, 2023 +2.9, 2024 +4.2, 2025 −0.1, 2026 +1.2. Before tax and before the other three start months the book looks better than it is: the after-tax mean over four starts is +0.6.

### 4.3 Did the tilt add anything? Did anything else?

After-tax lead, A$25k / A$100k. CW = the same cap-weighted book with no tilt. EI10 = momentum tilt only. M3 = round 5's design (in-sample on these prices). M3cap = M3 on names with a cap. M3I = M3 with the low-issuance percentile averaged in.

| Market-set | EI10I | CW | EI10 | M3 | M3cap | M3I | EI10I − CW | EI10I − M3 |
|---|---|---|---|---|---|---|---|---|
| US large | +2.4 / +1.9 | +1.9 / +1.7 | +0.7 / +1.7 | +2.1 / -0.8 | +1.9 / +0.1 | -1.8 / -1.6 | +0.5 / +0.2 | +0.2 / +2.7 |
| US mid | +0.4 / +0.1 | -4.8 / -2.9 | -2.6 / -1.9 | +4.2 / +1.3 | +4.9 / +1.2 | -1.8 / +0.9 | +5.2 / +3.0 | -3.8 / -1.2 |
| US small | -0.2 / -1.0 | -3.3 / -3.8 | -3.7 / -3.1 | +2.3 / +0.7 | +2.3 / -0.3 | +1.4 / +1.8 | +3.1 / +2.8 | -2.5 / -1.7 |
| Korea | -1.3 / -0.7 | +1.2 / +0.5 | +1.9 / -0.9 | +2.1 / +2.6 | +4.5 / +2.2 | +1.5 / +2.1 | -2.5 / -1.2 | -3.3 / -3.3 |
| Taiwan | -1.9 / -1.9 | -2.3 / -2.5 | -1.3 / -1.9 | -1.6 / -1.2 | +1.1 / -1.0 | -0.9 / -2.4 | +0.4 / +0.6 | -0.3 / -0.7 |
| Thailand | +0.3 / +3.7 | +1.3 / +0.1 | -0.0 / +1.4 | +1.2 / +1.1 | -1.5 / +0.8 | +2.3 / +1.7 | -1.0 / +3.6 | -0.9 / +2.6 |
| China | -1.3 / +0.3 | +0.5 / +0.2 | +1.1 / +0.7 | -0.2 / +1.2 | +1.0 / +0.4 | +1.3 / +0.5 | -1.8 / +0.1 | -1.1 / -0.8 |
| Brazil | +5.4 / +3.1 | +6.1 / +4.5 | +1.5 / +0.3 | -1.1 / +0.1 | -0.6 / -0.4 | +0.8 / -0.6 | -0.7 / -1.4 | +6.5 / +3.0 |
| Denmark | +1.6 / +2.3 | +1.6 / +2.4 | +2.3 / +2.1 | +2.5 / +3.3 | -0.8 / +2.3 | +4.0 / +3.2 | +0.0 / -0.1 | -0.9 / -1.0 |
| Spain | -1.8 / +0.6 | +0.8 / +0.6 | -2.6 / -1.2 | -2.9 / -0.8 | -0.7 / -0.4 | +0.7 / -0.5 | -2.6 / +0.0 | +1.2 / +1.4 |
| Norway | -1.7 / -0.8 | -0.6 / +0.1 | -0.8 / -1.0 | +1.8 / +2.0 | +1.4 / +0.9 | +3.5 / +1.4 | -1.1 / -0.9 | -3.5 / -2.7 |
| South Africa | -0.5 / -0.4 | +0.2 / +0.5 | +1.3 / -1.1 | -0.0 / -1.2 | -1.5 / -1.3 | -2.2 / -0.6 | -0.7 / -0.9 | -0.5 / +0.8 |
| **Mean** | +0.1 / +0.6 | +0.2 / +0.1 | -0.2 / -0.4 | +0.9 / +0.7 | +1.0 / +0.4 | +0.7 / +0.5 | -0.1 / +0.5 | -0.8 / -0.1 |
| At +1 or better at both sizes / sets with a cell below −2 | 3 / 0 | 3 / 3 | 1 / 3 | 5 / 1 | 2 / 0 | 5 / 2 | both sizes positive: 4 of 12 | both sizes positive: 3 of 12 |

- **The tilt added nothing reliable.** EI10I was ahead of the untilted book at both sizes in 4 of 12 sets; the mean difference is −0.1 / +0.5. The momentum-only tilt (EI10) was worse than no tilt.
- **Issuance again neither confirmed nor rejected.** Inside M3's structure, adding low issuance changed the mean from +0.9 / +0.7 to +0.7 / +0.5. Report 76's question is answered as far as this data can: it does not help.
- **Plain M3 over Dec 2019 – Oct 2026 on these twelve sets:** +0.9 / +0.7 on average, at +1 or better at both sizes in 5 of 12, one set with a cell below −2 (Spain). These prices chose M3, so this is in-sample and is shown only as the yardstick the new design had to beat. It did not.
- The untilted cap book was within about a point of the fund in the validated sets except Brazil (+6.1 / +4.5) and Taiwan (−2.3 / −2.5), and far behind in US mid and small (−4.8 / −2.9, −3.3 / −3.8), where "cap-weighted inside a traded-value band" is not what the mid- and small-cap funds hold.

### 4.4 The owner's account: A$5,000 + A$500 a month, 29 Dec 2017 – 30 Oct 2026, after tax, everything sold

Fund only until the account reaches A$25,000 (late 2020 to mid 2021), then the book. A$57,500 paid in. The 40/60 plan on the same contributions ended at **A$98,662** (report 70, to 13 Nov 2026, in Australian dollars with franking; the figures below are in local units without currency moves, so the comparison with the plan is loose).

| Market-set | Paid in | EI10I | CW | EI10 | M3 | M3cap | M3I | Local fund | First share purchase (EI10I) |
|---|---|---|---|---|---|---|---|---|---|
| US large | 57.5k | 117.5k | 118.5k | 113.8k | 120.8k | 118.3k | 96.0k | 108.1k | 2020-08-31 |
| US mid | 57.5k | 92.4k | 80.1k | 94.1k | 107.0k | 109.4k | 96.7k | 88.5k | 2020-11-30 |
| US small | 57.5k | 90.7k | 80.3k | 86.9k | 94.8k | 106.2k | 109.0k | 84.8k | 2020-11-30 |
| Korea | 57.5k | 137.8k | 143.8k | 142.3k | 180.3k | 196.8k | 158.1k | 143.4k | 2020-11-30 |
| Taiwan | 57.5k | 182.0k | 183.9k | 180.0k | 199.7k | 185.0k | 190.1k | 200.4k | 2020-07-31 |
| Thailand | 57.5k | 75.5k | 75.2k | 71.9k | 62.0k | 66.1k | 69.8k | 67.6k | 2021-08-31 |
| China | 57.5k | 57.9k | 57.4k | 60.1k | 58.4k | 57.1k | 65.1k | 58.2k | 2020-07-31 |
| Brazil | 57.5k | 91.5k | 98.0k | 81.6k | 82.6k | 77.4k | 80.4k | 81.8k | 2020-11-30 |
| Denmark | 57.5k | 83.5k | 76.8k | 78.8k | 89.1k | 80.9k | 84.7k | 76.1k | 2020-07-31 |
| Spain | 57.5k | 130.0k | 112.9k | 128.3k | 95.5k | 106.2k | 122.5k | 115.2k | 2021-03-31 |
| Norway | 57.5k | 106.8k | 101.3k | 96.8k | 108.0k | 101.8k | 101.8k | 99.8k | 2020-12-30 |
| South Africa | 57.5k | 95.8k | 94.4k | 100.8k | 99.1k | 101.2k | 93.4k | 98.5k | 2020-12-31 |

- EI10I ended ahead of the local fund in 8 of 12 sets (by A$4,000–15,000) and behind in 4 (Korea, Taiwan, China, South Africa).
- It ended above the plan's A$98,662 in five sets: US large, Korea, Taiwan, Spain and Norway. In each of those the local fund alone was also above the plan. In no set did the design lift an account over the plan that the fund would not have.
- On ASX the comparable figures are in section 1: M3 A$78,000 (range A$76,500–88,700), A200 fund A$86,763, 40/60 plan A$98,662, H82 A$88,671.

## 5. What came closest, all rounds (updated)

| Rank | Design | Test | Sets at +1 or better at both sizes | Cells below −2 | Mean lead |
|---|---|---|---|---|---|
| 0 | The local index fund | — | — | — | 0 |
| 1 | M3 (round 5) | 5 fresh markets (Thailand, China, Finland, Poland, Belgium) | 3 of 5 | 0 of 10 | +1.4 |
| 2 | EI10I (this round) | 12 sets, fresh share counts on development prices | 3 of 12 | 0 of 24 | +0.4 |
| 3 | CSL, EI, E3, E1/E2 (rounds 1–4) | 20 market tests | at most 1 of 3 | several | negative |

M3 keeps first place among the designs, with two corrections from this round: it was behind at home in 2023–26 (−5.3 / −2.5 on ASX), and its hold rule is "top 100", not "top 150".

## 6. Caveats and reasons this could be wrong

- **Development prices.** The look's prices were seen in rounds 3–5. Only the share-count side is new.
- **A post-look code fix** (US mid and small). Shown both ways; it does not change any bar item's answer except item 2.
- **Cap data.** Valid in 10 of 20 sets by the tracking test. US caps are survivor-biased (dead companies have no share counts), which flatters every US cap-weighted figure here (the computed US large index beat SPY by 3 points a year). 6–27% of files hold an unexplained ×3 step in the share history. Levels are tied to the vendor's current market cap, which uses today's figure to fix a past level.
- **Full cap against free float**, and a 20% ceiling on one name: the book cannot match an index that is half one company.
- **Window.** 6.8 years, starting weeks before the 2020 crash.
- **China** is not investable as modelled, and a third of its most-traded names have no cap under the turnover ceiling.
- **The blind replication used the original's packs.** The score inputs were recomputed from raw prices for Thailand only; pack construction for other markets was not rebuilt.
- **Knife edges.** At A$25,000 single purchases decide a cell; differences of A$10 in valuation moved one China cell by two points a year for one start month.
- **Local taxes, currency and franking** are not modelled outside Australia.
- **Selection.** 106 counted trials this round on top of 1,543. Deflated Sharpe ratios are at or near zero everywhere.

## 7. What is left that could change the answer

1. **Time.** The forward paper record (H82, E3, M3 shadow) from December 2026.
2. **Nothing else on this data.** Fresh exchanges are used up (report 76). Fundamentals have now been tried as quality, value, issuance (twice) and as cap weights. The one positive finding is structural: hold large companies at cap weight, which is what the index fund already does for 0.04–0.07% a year.

## 8. Data, quota and files

- **EODHD use this round: 32,460 fundamentals calls (3,246 files at 10) plus about 90 account checks, single thread at 270 calls a minute, no rate-limit errors.** `/api/user` read 51,697 before and 84,157 after, so 15,843 of the day's 100,000 were left spare.
- Every raw response is kept gzip-compressed: `improve6/data/fundamentals_raw/<SET>/<SYMBOL>.<EXCHANGE>.json.gz` (3,241 files, 150 MB) with `index.csv` (symbol, time, bytes). With round 5's 2,407 files the archive holds 5,648 company files. Disk free at the end: 3.9 GB.

| What | Where (under `scratchpad/improve6/`) |
|---|---|
| Progress log, pre-registration, hashes | `PROGRESS.md`, `PREREG_77.md`, `out/prereg77_hash.txt`, `out/prereg77_sha256.txt` |
| Trial ledger (1,544 → 1,649) | `out/trials_77.csv` |
| Blind replication | `code/blind_m3_v1_frozen.py`, `out/blind_look_v1.json`, `out/blind_owner_ASX_v1.json`, `out/blind_v1_hash.txt`; aligned engine `code/m3v2.py`; comparisons `code/cmp1.py`, `cmp_asx.py`, `cmp4.py`, `cmp5.py`, `sim5_dbg.py`; `out/replication_steps.log`, `out/replication_owner_ASX.log`, `out/sigcheck_BK.log` |
| ASX pack fault | `code/asxfix.py`, `out/asx_pack_check.log` |
| Market caps | `code/capbuild.py`, `code/lib6.py`, `code/capcheck.py`, `out/capcheck_dev.csv`, `out/capcheck_look.csv`, `out/qa6_look.csv`, `data/us_foreign.json` |
| Enhanced index | `code/sim6.py`, `code/ei6.py` (frozen version `ei6_frozen.py`), `code/dev6.py`, `out/dev6v2.log`, `out/res_dev6v2.json`, first run in `out/v1_unitbug/` |
| The look | `code/look6.py`, `code/run_look.sh`, `code/summ6.py`, `out/look_<design>_<set>.json`, `out/look.log`, `out/look_fix.log`, `out/look_asfrozen/`, `out/summary_look.json`, `rep/look_tables.md` |
| Downloads | `code/dlf6.py`, `data/names_look.json`, `data/fund/<SET>.pkl`, `data/fundamentals_raw/`, `out/dl_fund6.log` |
