# Odds table (method odds1, BF-D88)

File: `config/odds_table_v1.csv`. It holds aggregated percentages and counts only: no
prices, no company codes and no per-company rows. The app's share pages read it for the
card "Odds for shares like this (history)". The trader never reads it. It is descriptive
history, not a trial, and it changes no strategy rule or parameter.

## For the owner

Single big winners cannot be predicted, but the odds for a group of similar shares can be
counted. For each share, the card finds its group: its size (rank by traded value) and
its score (top fifth, second fifth and so on). It then says how often shares in that
group, from January 2005 to October 2025, rose 40% or more within a year, doubled, or
halved, and what the middle (median) result was. **These are odds, not a forecast. Past
patterns can change.** The fold-out shows the earlier years (2005–2015) and the later
years (2016–2025) side by side. If they differ a lot, trust the odds less.

## Method

* **Data.** The long survivorship-free ASX research panel of report 100
  (`deep100/code/build100.py`), every company including dead ones, daily total returns
  (dividends and splits in). The panel stays in the research environment.
* **Unit.** A stock-month: each share at each month-end from Jan 2005 to Oct 2025
  (250 month-ends).
* **Universe.** As research_big Study A (REPORT.md section 1): ordinary shares with a
  close on the entry session (the session after the month-end) and a 20-session median
  traded value of at least A$10,000 (TRADE). In addition, the share must be eligible
  for a score under the strategy's own filters (63-session median traded value at least
  A$100,000, close at least A$0.10, traded in the last five sessions, s1/s2/s3 defined),
  so that every row has a score quintile.
* **Size band.** Rank by 252-session median traded value (1 = largest): 1–100, 101–300,
  301–600 (band C, the strategy's band) and 601–1000.
* **Score quintile.** M3 = the mean of the within-band percentiles of s1 (12-1 month
  momentum), s2 (6-month momentum) and s3 (nearness to the 52-week high); then its
  percentile among the band's eligible names that month. Quintile 5 is above 80%, the
  same cut as the strategy's top fifth and the app's score percentile.
* **Outcome.** The total return over the next 252 sessions from the entry close. A share
  that stops trading is valued by the backtests' payout rule (takeover: last close;
  liquidation: zero; otherwise its last close only if within 30% of its 250-session
  high, else zero).
* **Third split.** A split by lottery class or by nearness to the 52-week high (top
  third) was allowed only if every cell kept at least 300 stock-months. Neither did
  (smallest cells 17 and 20), so the table has 4 bands x 5 quintiles = 20 cells.
* **Check.** Band C, top fifth: doublers 10.4% / 11.7% and halvings 19.6% / 13.9% in the
  two halves, as research_big reported (10.4% / 11.8%, 20% / 14%).

## Band C (ranks 301–600) by score quintile

| Quintile | n | Companies | +40% | Doubled | Halved | Median | +40% 05–15 / 16–25 | Doubled | Halved | Median |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 (top) | 6,018 | 1,162 | 26.9% | 11.1% | 16.4% | 0% | 27.0 / 26.7 | 10.4 / 11.7 | 19.6 / 13.9 | −3.5 / +1.9 |
| 4 | 5,958 | 1,162 | 20.3% | 7.4% | 15.5% | −0.7% | 20.4 / 20.2 | 7.2 / 7.5 | 19.6 / 12.3 | −3.3 / +0.7 |
| 3 | 5,971 | 1,116 | 16.8% | 5.7% | 15.9% | −5.9% | 17.2 / 16.4 | 6.0 / 5.4 | 20.1 / 12.7 | −9.2 / −3.8 |
| 2 | 5,968 | 1,068 | 17.0% | 5.5% | 20.2% | −10.6% | 14.3 / 19.0 | 5.3 / 5.7 | 24.5 / 17.0 | −15.0 / −6.4 |
| 1 (bottom) | 5,866 | 935 | 15.7% | 6.1% | 29.0% | −24.0% | 14.0 / 17.1 | 5.5 / 6.5 | 32.0 / 26.7 | −26.6 / −22.4 |

The other bands are in the CSV. Ranks 601–1000 have few score-eligible names (about
500–700 stock-months per quintile, 170–270 in the earlier half), so their odds are the
least reliable.

## Caveats

* Stock-months overlap: a share appears every month, and 12-month windows of nearby
  months share most of their days. The effective sample is much smaller than n.
* No costs or tax. The score was developed on part of this history.
* The app knows a share's size rank and score only while it is in band C (the decision
  records hold band C only). A share outside band C at the latest decision shows "Not
  enough data for odds".
* The research panel's share classes differ slightly from the live list (which also
  drops LICs before ranking).

## Rebuild (at most once a year, in the research environment)

1. Build the panel: `python deep100/code/build100.py` (writes `/dev/shm/p100/asxlong`;
   copy it to `/dev/shm/odds/asxlong` if another job is using it).
2. Rows (about 100,000 stock-months, kept in `/dev/shm`):
   `python -I research/odds_table/build_odds_table.py extract --panel /dev/shm/odds/asxlong --kit $B/blind3_clean/kit --kit $B/blind2_build --rows /dev/shm/odds/rows.csv.gz`
   (`$B` is the research scratch folder holding the frozen `acct3` and `eng88` engines).
3. Move the `LAST` formation month in the script forward (it must leave 252 sessions of
   outcome), then
   `python -I research/odds_table/build_odds_table.py aggregate --rows /dev/shm/odds/rows.csv.gz --out config/odds_table_v1.csv`.
4. Delete `/dev/shm/odds`. Check the halves, update this note and the DECISIONS entry,
   run the tests (`tests/test_bf_odds.py`) and push. A new method or new columns gets a
   new file name (`odds_table_v2.csv`) and a new DECISIONS entry.
