# Report 95 — The frozen EMG2-18 and BLIND3 rules run on other markets

Fable, 19 November 2026. Research only: no live code, ledger or scheduled task was touched. Working folder `deep95/`.

## 1. Answer

**The ranking travels; the profit does not.**

- In 10 overseas markets, over the same window as reports 89/91b (12 start months from December 2017, to October 2026), both rule sets picked better than chance. Pooled across markets, each book beat all 100 of its pooled random twins. The lead over the twins' middle was about +7 points a year for EMG2-18 and +6 for BLIND3. On the ASX the same leads were +12.5 and about +10.5.
- After the costs of an A$10,000 book and tax, the books still lost to the local index fund in most markets. EMG2-18 made 2.6% a year against 8.4% for the funds and was ahead in 2 of 9 markets. BLIND3 made 5.8% against 8.4% and was ahead in 3 of 9.
- By the rule fixed in advance, the verdict is **"weak / not shown"** for both rule sets in both translations. The twins tests were met; "ahead of the local fund in at least half the markets" was not.
- What this says about the ASX results: the selection effect is probably real, not an accident of the ASX file, but it is about half the size abroad. The ASX books' lead over the fund (+4 to +5 points a year) was not repeated anywhere as a rule. Abroad the typical result was 2 to 6 points behind. The ASX lead over the fund should be treated as the lucky end of the range.
- Canada, the closest market to the ASX in kind, is not in the result. Its build crashed on a data-handling fault, and its downloaded data was then lost in a container restart. It needs about 5,400 vendor requests after the daily reset (section 8).

## 2. What was run

- **Rules.** The registered code, unmodified: the kit engine `acct3.py`, `tools3.py`, the builder's `strat.py`, and `eng88.py` with the EMG2-18 strategy class of report 91b. Hashes are in `deep95/PREREG_95.md`.
- **Harness check.** The same script run on the ASX panel gives EMG2-18 12.47% a year (100th place, worst fall −58%, 110 orders) and BLIND3 12.09% (worst fall −44%, 46.5 orders). These are report 91b's figures.
- **Pre-registration.** `PREREG_95.md` was hashed before any overseas design return existed (SHA-256 `14bc374ec468f3d2f2bf0ede37d425514853e239aacc058768ad8ad7726cb80c`). Later entries in `out/prereg95_hash.txt` record four small code changes, none touching a rule: the rule list as an argument, the Taiwan numeric-code filter, and two edits for entity codes that the table reader takes as missing.
- **Two translations, both fixed in advance.**
  - *Same rank*: EMG2 band 301–600; BLIND3 top 400, keep 800.
  - *Same percentile*: the ASX kit ranks 1,589 ordinary shares at December 2017 (the brief's "about 2,000" is listed shares). The band and universe are scaled by each market's own count at December 2017.
- **Money.** A$10,000 of local currency at a fixed end-2017 rate. Kit costs in A$ equivalents: brokerage max(A$6.60, 0.088%), modelled spread, A$500 minimum order. Kit tax: 32%, halved after 367 days. Local-currency returns, no currency effect.
- **Comparators.** The local index fund's total return, taxed by the kit's formula, and 100 random twins per book.
- **Admission.** A market entered a version only if it passed count tests at December 2017 (table in section 7).

## 3. Scope: which data could carry the test

| Source | Dead companies | Traded value | Dividends | Usable |
|---|---|---|---|---|
| Report 83 corrected packs (`deep83/data`) | Yes, but monthly features of names ever in the top ~1,200 only; daily rows deleted | Corrected | In the return series | Not directly: the rules need daily rows. Re-downloaded |
| Round 4/5 raw files (`improve4`, `improve5`) | Yes, whole exchange | Corrected here with the report 83 rule | Yes | Yes |
| Forward stores (`fwd_multi`) | Rows from September 2024 only | — | — | No |
| `improve6` | Share counts and fundamentals, no prices | — | — | No |

- **Outside the US the vendor's dead companies start in about 2017–2018.** Before that the files hold survivors only (0–20 ended companies a year per exchange, then tens to hundreds). So no 2010–2017 run is honest on these files, and none was made. The only window is December 2017 to October 2026.
- **Run (10):** UK, US, Sweden, France, Germany, Korea (KOSPI + KOSDAQ), Taiwan (TWSE + TPEx), Thailand, China (Shanghai + Shenzhen), Malaysia.
- **US:** corrected set only: US-dollar lines on NYSE/NASDAQ/AMEX, report 83's mislabelled-line flags, corrected traded value. It holds pack names only, so it supports the same-rank version and not the percentile version.
- **Excluded on counts:** Vietnam, Poland, Indonesia, Pakistan (band traded value of a few thousand A$ a day); Brazil, Mexico, South Africa (under 300 ranked shares); 13 small exchanges.
- **Not run:** Canada (section 8).

## 4. Results by market

Returns are % a year after costs and tax, mean of 12 start months. "Place" is the share of the 100 twins the book beat. Bar: (a) place at least 75; (b) ahead of the fund; (c) five best holdings removed, above the twins' middle; (d) spread doubled, above the twins' middle. "Dead holdings paid zero" is the lower bound if every holding that stopped trading had paid nothing.

ASX reference (report 91b, research panel): EMG2-18 12.5 against fund 7.7, twins −0.1, 100th place, worst fall −58%. BLIND3 12.1, twins 1.2 to 2.0, 94th–97th place, worst fall −44%.

**EMG2-18, same-percentile version**

| Market | Book, % a year | Local fund | Book − fund | Starts ahead of fund (of 12) | Twins: middle (10th–90th) | Place among 100 twins | Best 1 / 3 / 5 removed | Place with 5 removed | Spread ×2 (place) | Worst fall, daily (fund; twins) | Orders a year | Dead holdings paid zero | Bar a b c d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UK (London) | 2.8 (1.6 to 3.5) | 7.3 | -4.5 | 0 | -3.1 (-7.9 to 0.8) | 95 | 1.8 / 0.4 / -0.9 | 97 | 1.0 (95) | -45% (-34%; -59%) | 84 | -13.7 | ✓ ✗ ✓ ✓ |
| Sweden | 6.3 (5.3 to 7.5) | 10.8 | -4.4 | 0 | -1.2 (-5.2 to 5.0) | 95 | 4.2 / 0.9 / -2.3 | 83 | 5.0 (95) | -63% (-32%; -55%) | 94 | 1.4 | ✓ ✗ ✓ ✓ |
| France | 5.2 (4.0 to 6.7) | 7.0 | -1.8 | 0 | -5.8 (-14.2 to 1.1) | 99 | 3.4 / 1.6 / -0.1 | 100 | 4.2 (98) | -51% (-38%; -70%) | 72 | -1.2 | ✓ ✗ ✓ ✓ |
| Germany (XETRA) | 13.8 (10.8 to 15.5) | 7.6 | +6.1 | 12 | 1.8 (-3.5 to 4.8) | 100 | 12.6 / 11.2 / 10.0 | 100 | 12.7 (100) | -35% (-39%; -44%) | 84 | 8.9 | ✓ ✓ ✓ ✓ |
| Korea (KOSPI + KOSDAQ) | -9.5 (-14.4 to -8.1) | 14.9 | -24.5 | 0 | -12.1 (-19.0 to -6.3) | 67 | -12.5 / -21.9 / -29.8 | 43 | -13.6 (54) | -94% (-42%; -79%) | 59 | -12.8 | ✗ ✗ ✗ ✓ |
| Taiwan (TWSE + TPEx) | 16.5 (13.6 to 21.8) | 22.9 | -6.4 | 0 | 1.8 (-2.7 to 5.7) | 100 | 14.7 / 11.8 / 9.1 | 100 | 12.6 (100) | -51% (-34%; -48%) | 122 | 15.7 | ✓ ✗ ✓ ✓ |
| Thailand | -3.6 (-4.8 to -2.8) | 1.3 | -5.0 | 0 | -8.6 (-12.5 to -3.6) | 90 | -5.1 / -7.3 / -9.7 | 86 | -6.8 (86) | -59% (-38%; -67%) | 77 | -3.6 | ✓ ✗ ✓ ✓ |
| China (Shanghai + Shenzhen) | -11.6 (-14.4 to -10.3) | 2.0 | -13.6 | 0 | -10.5 (-15.4 to -4.3) | 35 | -15.4 / -25.3 / -66.7 | 0 | -15.4 (39) | -85% (-43%; -73%) | 98 | -11.8 | ✗ ✗ ✗ ✗ |
| Malaysia | 4.0 (3.0 to 4.9) | 1.6 | +2.4 | 12 | -3.3 (-6.7 to -0.1) | 100 | 1.2 / -0.9 / -3.1 | 92 | 0.5 (98) | -45% (-28%; -40%) | 92 | 2.6 | ✓ ✓ ✓ ✓ |

**EMG2-18, same-rank version**

| Market | Book, % a year | Local fund | Book − fund | Starts ahead of fund (of 12) | Twins: middle (10th–90th) | Place among 100 twins | Best 1 / 3 / 5 removed | Place with 5 removed | Spread ×2 (place) | Worst fall, daily (fund; twins) | Orders a year | Dead holdings paid zero | Bar a b c d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UK (London) | 4.6 (3.2 to 6.4) | 7.3 | -2.7 | 0 | -3.4 (-8.6 to -0.1) | 99 | 3.8 / 2.5 / 1.2 | 99 | 2.2 (99) | -46% (-34%; -59%) | 85 | -10.1 | ✓ ✗ ✓ ✓ |
| US (pack names) | 4.7 (3.1 to 7.4) | 12.9 | -8.2 | 0 | 0.1 (-4.5 to 3.8) | 97 | 1.4 / -0.9 / -3.1 | 47 | 2.6 (94) | -46% (-34%; -48%) | 94 | 0.3 | ✓ ✗ ✗ ✓ |
| Korea (KOSPI + KOSDAQ) | -5.8 (-12.5 to 0.0) | 14.9 | -20.8 | 0 | -11.0 (-19.0 to -5.5) | 89 | -8.2 / -12.9 / -20.2 | 57 | -10.9 (67) | -91% (-42%; -79%) | 69 | -6.5 | ✓ ✗ ✓ ✓ |
| Taiwan (TWSE + TPEx) | 15.4 (12.8 to 18.7) | 22.9 | -7.5 | 0 | 1.5 (-3.1 to 5.6) | 100 | 14.3 / 11.9 / 9.4 | 100 | 11.6 (100) | -54% (-34%; -51%) | 124 | 14.6 | ✓ ✗ ✓ ✓ |
| China (Shanghai + Shenzhen) | -7.8 (-9.0 to -5.8) | 2.0 | -9.8 | 0 | -8.1 (-12.5 to -4.4) | 54 | -12.3 / -42.1 / -66.7 | 0 | -9.4 (64) | -82% (-43%; -70%) | 96 | -7.8 | ✗ ✗ ✗ ✓ |

**BLIND3, same-percentile version**

| Market | Book, % a year | Local fund | Book − fund | Starts ahead of fund (of 12) | Twins: middle (10th–90th) | Place among 100 twins | Best 1 / 3 / 5 removed | Place with 5 removed | Spread ×2 (place) | Worst fall, daily (fund; twins) | Orders a year | Dead holdings paid zero | Bar a b c d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UK (London) | 1.3 (-0.2 to 3.8) | 7.3 | -6.0 | 0 | -0.0 (-6.4 to 2.5) | 70 | 0.8 / -0.1 / -1.0 | 85 | -0.6 (58) | -44% (-34%; -52%) | 54 | -10.6 | ✗ ✗ ✓ ✓ |
| Sweden | 13.5 (12.2 to 16.8) | 10.8 | +2.7 | 12 | 5.6 (1.0 to 10.8) | 96 | 12.6 / 11.2 / 10.0 | 97 | 13.2 (96) | -44% (-32%; -47%) | 40 | 9.4 | ✓ ✓ ✓ ✓ |
| France | 2.4 (0.9 to 3.2) | 7.0 | -4.5 | 0 | -3.6 (-8.3 to 1.8) | 92 | 1.5 / 0.4 / -0.5 | 97 | 1.8 (92) | -36% (-38%; -57%) | 50 | -0.5 | ✓ ✗ ✓ ✓ |
| Germany (XETRA) | 6.7 (1.6 to 8.3) | 7.6 | -1.0 | 3 | 4.5 (-0.5 to 10.5) | 65 | 5.7 / 4.5 / 3.5 | 77 | 5.7 (63) | -41% (-39%; -46%) | 43 | -3.0 | ✗ ✗ ✓ ✓ |
| Korea (KOSPI + KOSDAQ) | 17.0 (12.2 to 23.4) | 14.9 | +2.0 | 9 | -3.4 (-10.7 to 3.8) | 99 | 14.7 / 12.7 / 10.6 | 100 | 15.5 (99) | -51% (-42%; -67%) | 49 | 16.0 | ✓ ✓ ✓ ✓ |
| Taiwan (TWSE + TPEx) | 12.3 (8.0 to 17.7) | 22.9 | -10.7 | 0 | 11.6 (6.3 to 16.8) | 57 | 11.1 / 9.1 / 7.6 | 66 | 9.8 (45) | -40% (-34%; -45%) | 49 | 12.1 | ✗ ✗ ✓ ✗ |
| Thailand | -4.1 (-5.4 to -2.7) | 1.3 | -5.4 | 0 | -7.2 (-11.4 to -2.5) | 80 | -5.3 / -7.0 / -8.1 | 91 | -6.2 (80) | -52% (-38%; -68%) | 41 | -5.3 | ✓ ✗ ✓ ✓ |
| China (Shanghai + Shenzhen) | -8.5 (-11.3 to -5.0) | 2.0 | -10.5 | 0 | -3.5 (-8.0 to 2.1) | 8 | -12.6 / -18.5 / -29.5 | 1 | -9.8 (8) | -75% (-43%; -64%) | 64 | -8.5 | ✗ ✗ ✗ ✗ |
| Malaysia | 11.5 (9.6 to 14.5) | 1.6 | +9.9 | 12 | -6.2 (-11.0 to 0.3) | 100 | 9.6 / 7.3 / 5.8 | 100 | 11.1 (100) | -49% (-28%; -66%) | 49 | 9.8 | ✓ ✓ ✓ ✓ |

**BLIND3, same-rank version**

| Market | Book, % a year | Local fund | Book − fund | Starts ahead of fund (of 12) | Twins: middle (10th–90th) | Place among 100 twins | Best 1 / 3 / 5 removed | Place with 5 removed | Spread ×2 (place) | Worst fall, daily (fund; twins) | Orders a year | Dead holdings paid zero | Bar a b c d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UK (London) | 0.2 (-1.0 to 3.3) | 7.3 | -7.1 | 0 | -0.5 (-5.7 to 3.1) | 59 | -0.3 / -1.2 / -2.1 | 77 | -0.5 (61) | -43% (-34%; -54%) | 53 | -11.9 | ✗ ✗ ✓ ✓ |
| US (pack names) | 4.6 (2.8 to 6.9) | 12.9 | -8.3 | 0 | 6.9 (3.4 to 12.8) | 22 | 4.0 / 2.8 / 2.0 | 38 | 3.5 (21) | -38% (-34%; -43%) | 50 | 1.3 | ✗ ✗ ✗ ✗ |
| Sweden | 17.3 (14.3 to 21.5) | 10.8 | +6.5 | 12 | -0.1 (-5.3 to 6.6) | 100 | 16.2 / 14.0 / 12.6 | 100 | 15.9 (100) | -47% (-32%; -60%) | 48 | 16.3 | ✓ ✓ ✓ ✓ |
| France | 5.4 (3.5 to 7.0) | 7.0 | -1.6 | 0 | -4.8 (-10.6 to 1.0) | 97 | 4.1 / 2.6 / 1.4 | 100 | 5.2 (98) | -37% (-38%; -64%) | 55 | -2.0 | ✓ ✗ ✓ ✓ |
| Germany (XETRA) | 11.3 (8.7 to 12.6) | 7.6 | +3.7 | 12 | 5.3 (-0.3 to 10.1) | 92 | 10.4 / 9.1 / 8.1 | 96 | 10.5 (91) | -42% (-39%; -46%) | 48 | 5.5 | ✓ ✓ ✓ ✓ |
| Korea (KOSPI + KOSDAQ) | 9.0 (6.3 to 11.9) | 14.9 | -5.9 | 0 | -1.1 (-8.2 to 5.0) | 98 | 7.6 / 5.7 / 3.9 | 99 | 8.3 (98) | -58% (-42%; -66%) | 49 | 9.0 | ✓ ✗ ✓ ✓ |
| Taiwan (TWSE + TPEx) | 14.6 (11.3 to 17.5) | 22.9 | -8.3 | 0 | 12.3 (6.5 to 17.4) | 66 | 13.4 / 11.7 / 10.2 | 84 | 13.8 (69) | -38% (-34%; -45%) | 49 | 14.5 | ✗ ✗ ✓ ✓ |
| Thailand | 0.7 (-0.8 to 1.9) | 1.3 | -0.7 | 2 | -9.7 (-14.5 to -3.5) | 96 | -0.4 / -2.3 / -4.0 | 100 | -2.6 (95) | -45% (-38%; -76%) | 54 | -0.8 | ✓ ✗ ✓ ✓ |
| China (Shanghai + Shenzhen) | -5.9 (-8.5 to -2.2) | 2.0 | -7.9 | 0 | -2.5 (-6.9 to 4.3) | 14 | -9.2 / -14.4 / -20.1 | 6 | -7.3 (13) | -73% (-43%; -62%) | 61 | -5.9 | ✗ ✗ ✗ ✗ |
| Malaysia | 8.7 (6.4 to 12.5) | 1.6 | +7.1 | 12 | -6.2 (-10.9 to 0.4) | 99 | 6.4 / 4.0 / 2.4 | 100 | 5.6 (99) | -63% (-28%; -66%) | 51 | 5.8 | ✓ ✓ ✓ ✓ |

## 5. Pooled

Each market counts once, equal weight. A pooled twin is the mean of one twin seed across the markets. The primary pool is the percentile version.

| Rule set | Version | Pool (markets) | Book | Twins middle | Pooled place | Fund | Book − fund | Markets ≥ 75th place | Markets ahead of fund | Markets passing a–d | Best 1 / 3 / 5 removed (place) | Mean lead over twins (t across markets) | Verdict by the pre-set rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMG2-18 | pct | all (9: BK CN DE FR KLSE KO SE TW UK) | 2.6 | -4.6 | 100 | 8.4 | -5.7 | 7 of 9 | 2 of 9 | 2 of 9 | 0.5 (100) / -3.3 (100) / -10.4 (82) | +7.2 (4.4) | weak / not shown |
| EMG2-18 | pct | developed (4: DE FR SE UK) | 7.0 | -1.9 | 100 | 8.2 | -1.2 | 4 of 4 | 1 of 4 | 1 of 4 | 5.5 (100) / 3.5 (100) / 1.7 (100) | +9.1 (6.3) |  |
| EMG2-18 | pct | asia (5: BK CN KLSE KO TW) | -0.9 | -6.7 | 100 | 8.6 | -9.4 | 3 of 5 | 1 of 5 | 1 of 5 | -3.4 (100) / -8.7 (94) / -20.0 (21) | +5.7 (2.1) |  |
| EMG2-18 | rank | all (5: CN KO TW UK US) | 2.2 | -4.6 | 100 | 12.0 | -9.8 | 4 of 5 | 0 of 5 | 0 of 5 | -0.2 (100) / -8.3 (65) / -15.9 (24) | +6.5 (2.9) | weak / not shown |
| EMG2-18 | rank | developed (2: UK US) | 4.7 | -1.9 | 100 | 10.1 | -5.4 | 2 of 2 | 0 of 2 | 0 of 2 | 2.6 (100) / 0.8 (100) / -1.0 (95) | +6.3 (n/a) |  |
| EMG2-18 | rank | asia (3: CN KO TW) | 0.6 | -6.6 | 100 | 13.3 | -12.7 | 2 of 3 | 0 of 3 | 0 of 3 | -2.1 (100) / -14.4 (29) / -25.8 (15) | +6.5 (1.6) |  |
| BLIND3 | pct | all (9: BK CN DE FR KLSE KO SE TW UK) | 5.8 | -0.2 | 100 | 8.4 | -2.6 | 5 of 9 | 3 of 9 | 3 of 9 | 4.2 (100) / 2.2 (100) / -0.2 (100) | +6.0 (2.2) | weak / not shown |
| BLIND3 | pct | developed (4: DE FR SE UK) | 6.0 | 1.4 | 94 | 8.2 | -2.2 | 2 of 4 | 1 of 4 | 1 of 4 | 5.2 (98) / 4.0 (99) / 3.0 (99) | +4.3 (2.8) |  |
| BLIND3 | pct | asia (5: BK CN KLSE KO TW) | 5.6 | -1.3 | 100 | 8.6 | -2.9 | 3 of 5 | 2 of 5 | 2 of 5 | 3.5 (100) / 0.7 (100) / -2.7 (100) | +7.4 (1.5) |  |
| BLIND3 | rank | all (10: BK CN DE FR KLSE KO SE TW UK US) | 6.6 | 0.1 | 100 | 8.8 | -2.2 | 6 of 10 | 3 of 10 | 3 of 10 | 5.2 (100) / 3.2 (100) / 1.4 (100) | +6.7 (3.0) | weak / not shown |
| BLIND3 | rank | developed (5: DE FR SE UK US) | 7.8 | 1.2 | 100 | 9.1 | -1.4 | 3 of 5 | 2 of 5 | 2 of 5 | 6.9 (100) / 5.5 (100) / 4.4 (100) | +6.4 (1.8) |  |
| BLIND3 | rank | asia (5: BK CN KLSE KO TW) | 5.4 | -1.1 | 100 | 8.6 | -3.1 | 3 of 5 | 1 of 5 | 1 of 5 | 3.5 (100) / 0.9 (100) / -1.5 (100) | +6.9 (2.1) |  |

- **Selection against chance.** Pooled place is 100 in all four pools. The lead over twins was positive in 8 of 9 markets for both rule sets (percentile version), every market but China.
- **Size of the effect.** EMG2-18's mean lead over twins is +7.2 points (ASX +12.5). BLIND3's is +6.0 (ASX about +10.5). BLIND3's builder forecast +5.8 before seeing 2018–2026.
- **Against the fund.** Behind in 7 of 9 (EMG2-18) and 6 of 9 (BLIND3). The twins' middle abroad was −4.6% and −0.2% a year, against about 0% and +1 to +2% on the ASX. The shares these books fish in did worse than the large-company index nearly everywhere in this period, and an A$10,000 book pays 4–9% of itself a year in brokerage and spread.
- **Few winners.** With the five best holdings removed, EMG2-18's pooled place drops to 82 (percentile) and 24 (rank). In Asia it drops to 21 and 15. Its developed-market result does not depend on a few names (place 100). BLIND3 stays at 100 with five removed.
- **Where it failed.** China: both rule sets at or below their twins, falls of 73–85%. Korea: EMG2-18 lost 6–10% a year with a 91–94% fall, while BLIND3 did well there. US: BLIND3 at the 22nd place; EMG2-18 at the 97th but the 47th with five removed. UK and Taiwan: BLIND3 in the middle of its twins.
- **Where it worked on every line of the bar.** EMG2-18: Germany, Malaysia. BLIND3: Sweden, Malaysia, Korea (percentile), Germany (rank).
- **Worst falls.** Middle market −51% for EMG2-18 and −44% for BLIND3, close to the ASX figures. The worst were −85% to −94% (China, Korea).

## 6. Verdict

1. **Does momentum as built in EMG2-18 and BLIND3 travel?** As a way of ranking shares inside a band, yes, in most markets, at roughly half to two-thirds of the ASX strength. As a book that beats an index fund after the costs of A$10,000, no: 2–3 markets of 9.
2. **How much of the ASX result is luck or hindsight?**
   - The part that is "better than random picks from the same shares" looks mostly real. It showed up in markets neither design was built on, and BLIND3's realised lead abroad matches what its builder forecast.
   - The part that is "beats the fund by 4–5 points" looks mostly ASX-specific or lucky. An honest forward expectation for the ASX books is a lead over twins of perhaps +6 rather than +10 to +12. At A$10,000 that is about what the costs take.
   - This agrees with what is already on the scorecard for the live slice: expected result at this size is below the index even if the signal works.
3. **EMG2-18 against BLIND3.** EMG2-18 had the steadier lead over twins (t across markets 4.4 against 2.2) but the worse money result, the deeper falls, and it leans on a few winners outside Europe. BLIND3 is cheaper to run (49 orders a year against 87) and came closer to the funds. Neither is promoted by this test.

## 7. Limits

- **I was not blind to these markets.** Reports 76–83 ran other designs on some of them. The two rule sets themselves had never met this data.
- **Dead companies after 2017 may be incomplete** in the vendor file, and there are no delisting reasons abroad. Almost no dead holding was paid zero by the kit rule. If every one had been, the UK books would fall to −10% to −14% a year; UK takeovers are common, so that bound is not realistic.
- **The fund is a large-company index** in a period that favoured large companies (US, Taiwan, Korea especially). That is why the twins comparison was made primary.
- **Costs are flattering in places.** No stamp duty (UK) or sales tax (Korea, Taiwan) is charged, and there are no currency costs. The ASX price-step floor on the spread is applied to A$-equivalent prices.
- **Germany** is XETRA as the vendor lists it, which includes foreign companies' lines.
- **Admission thresholds** (90 names in the band, 150 in the universe) were written after seeing Thailand's and Malaysia's counts, which pass narrowly. This is stated in the pre-registration.
- **Korea and Taiwan** include the second boards (KOSDAQ, TPEx), downloaded for this test. The Korea panel was rebuilt and checked after the restart; the Taiwan panel could not be re-checked.
- **One window.** 2018–2026 is the only period available, and it is the same calendar period as the ASX judged window.

Admission counts at December 2017:

| market | N0 | C rank | C pct | U rank valid | U pct valid | pct band / U | admitted |
|---|---|---|---|---|---|---|---|
| CN | 3045 | 276 | 538 | 359 | 684 | 577-1150 / 767 | rank: EMG2_18,BLIND3; pct: EMG2_18,BLIND3 |
| BK | 622 | 28 | 97 | 390 | 153 | 118-235 / 157 | rank: BLIND3; pct: EMG2_18,BLIND3 |
| KLSE | 869 | 30 | 90 | 396 | 215 | 165-328 / 219 | rank: BLIND3; pct: EMG2_18,BLIND3 |
| UK | 1769 | 284 | 313 | 392 | 434 | 335-668 / 445 | rank: EMG2_18,BLIND3; pct: EMG2_18,BLIND3 |
| US | 2035 | 299 | 384 | 398 | 510 | 385-768 / 512 | rank: EMG2_18,BLIND3; pct: none |
| SE | 755 | 30 | 124 | 375 | 184 | 143-285 / 190 | rank: BLIND3; pct: EMG2_18,BLIND3 |
| FR | 777 | 24 | 137 | 391 | 192 | 147-293 / 196 | rank: BLIND3; pct: EMG2_18,BLIND3 |
| DE | 803 | 110 | 152 | 395 | 199 | 152-303 / 202 | rank: BLIND3; pct: EMG2_18,BLIND3 |
| KO | 2025 | 295 | 379 | 386 | 496 | 384-765 / 510 | rank: EMG2_18,BLIND3; pct: EMG2_18,BLIND3 |
| TW | 1778 | 299 | 335 | 399 | 447 | 337-671 / 448 | rank: EMG2_18,BLIND3; pct: EMG2_18,BLIND3 |

## 8. For the record keeper

1. **Trials: 33** (one per market, version and rule set run). **N = 2,788 + 33 = 2,821.** Twins, start months, the spread stress, payout bounds and the ASX harness check are not counted. Canada would add up to 4.
2. **Canada is pending.** `deep95/code/go_ca.sh` downloads TSX and TSX Venture (about 5,400 requests at 140 a minute), builds, applies the admission tests and runs. Then `read95.py` and `tables95.py` refresh the tables. It must wait for the vendor's daily reset. No Canadian return has been seen.
3. **Vendor requests used by this work: about 26,000 (the day's count went from 49,248 to about 75,700).** About 3,200 of them were wasted: after a container restart I re-downloaded KOSDAQ and part of TPEx before noticing both markets had already been run. The coordinator's stop was obeyed from 21:45 UTC.
4. **Scope finding to keep:** outside the US the vendor's files are survivor-only before about 2017–2018. Any overseas back-test starting earlier is biased.
5. No candidate, no amendment, nothing for the ledger from me.

## 9. Files

`deep95/PROGRESS.md`, `PREREG_95.md`, `out/prereg95_hash.txt`; `code/` (scope95, dl95, dl95b, build95, count95, admit95, run95, read95, tables95, qa95, go_ca.sh); `out/run_*.pkl` (one per market-version, about 1 MB each), `summary95.csv`, `pools95.csv`, `tables95.md`, `count_table.md`, `build_*.json`, `count_*.json`, `qa95.log`. Raw downloads and panels are deleted (rebuild: `dl95.py`, `build95.py`).
