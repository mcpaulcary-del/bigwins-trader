# Forecast bands (method fb1)

Files: `config/forecast_bands.csv` (benchmark: the equal-weight average of band C) and
`config/forecast_bands_a200.csv` (benchmark: the ASX 200 accumulation index, dividends in).
Both have the same columns: `score_bucket, months_since_entry, p10, p25, p50, p75, p90,
n_obs, period_start, period_end, method_version`. The values are decimals (0.034 = 3.4
percentage points ahead of the benchmark).

## For the owner

**This is a historical range, not a prediction.** For each share the strategy picks, the
bands show how shares with a similar score did against the market in the past, 1 to 12
months after they were bought, from January 2005 to October 2026. The middle line (p50)
is the typical result. Half of past picks did better than it and half did worse. The p10
to p90 range holds 8 in 10 past picks. The typical pick from the top fifth ended about
even with band C. The range is very wide. After 12 months, 1 pick in 10 was more than
60% behind and 1 in 10 was more than 90% ahead. The strategy's edge comes from the few
large winners, which is why the average is higher than the median. One share's line
tells you very little. The future can sit outside this range, and costs and tax are not
included.

## Method

* **Data.** The research panel of report 100 (`deep100/code/build100.py`). It covers
  every ASX company, dead ones included, from 23 Nov 2000 to 13 Nov 2026. Daily total
  returns include dividends and splits. The panel's EODHD and vendor rows stay in the
  research environment. Only the aggregate quantiles in these files left it.
* **Selection.** The trader's own code: `trader.lines.emg2.emg2_inputs` and
  `select_band_c` with the live `Emg2Params()` defaults. They are run on a `PricePanel`
  cut at each month-end close, so band C membership (ranks 301 to 600 by 252-day median
  traded value), the eligibility filters and the score match the live list exactly.
  LICs, funds and ETFs are left out of the ranks. The research panel's exclusion flag
  already contains every `config/lic_list.csv` company. Two codes on that list were
  used earlier by unrelated ordinary companies, which keep their ORD class.
  Rule 14 (fewer than 150 names means no decision) is not applied, because the EMG2
  backtests did not apply it either. Band C held between 12 and 236 names (median 125),
  and 176 of the 261 months had fewer than 150, so live trading would have blocked
  those months.
* **Buckets.** Score percentile inside band C: `top5` (> 95%), `top20` (80 to 95%, the
  rest of the buy list T), `20_40`, `40_60` and `60_100` (the bottom 40%). The lottery,
  bid-peg and duplicate filters of the buy step are not applied.
* **Entry and horizon.** Entry is at the close of the session after the month-end
  decision, the fill convention of the backtests (acct3). If a name has no close that
  day, the observation is dropped (393 cases). The stock is valued at the close of
  each of the next 1 to 12 month-ends. The excess return is the stock's cumulative
  total return minus the benchmark's cumulative return over the same days. The position
  is held for the whole horizon whether or not the name stays on the list.
* **Benchmark.** Band C equal weight, reset at each month-end close to that month's
  band C, bought and held within the month, with the same delisting rule applied to its
  members. Across all band C picks the mean excess is about 0 (−0.5% at 12 months), as
  it should be. The second file uses the ASX 200 accumulation index.
* **Delistings.** There is no survivorship bias. A share that has had no close for 20
  sessions and never trades again is valued by the backtests' payout rule
  (`acct3.Engine._payout`): its last close if the delisting record says takeover, zero
  if it says liquidation, and otherwise its last close only if that was within 30% of
  its 250-session high, else zero. Between 1.0% and 1.8% of the 12-month observations
  per bucket ended at zero.
* **Costs.** None are applied: no brokerage, no spread and no tax. These are excess paths
  per share, not book returns.
* **Period.** Entries are the month-ends from 31 Jan 2005 to 30 Sep 2026 (261 months).
  Returns run to 30 Oct 2026. The panel starts in Nov 2000, but before 2005 band C was
  very thin (often under 30 names), so 2001 to 2004 are left out. The 12-month rows
  need entries up to Oct 2025. Quantiles are numpy's linear ones.

## Sample sizes (n_obs, band C benchmark)

| bucket | 1 month | 3 months | 6 months | 12 months |
|---|---|---|---|---|
| top5 | 1,725 | 1,706 | 1,677 | 1,614 |
| top20 | 4,842 | 4,790 | 4,707 | 4,528 |
| 20_40 | 6,482 | 6,411 | 6,297 | 6,056 |
| 40_60 | 6,529 | 6,458 | 6,345 | 6,102 |
| 60_100 | 12,930 | 12,788 | 12,561 | 12,081 |

The sample covers 1,694 distinct shares. The observations are not independent:
entries in the same month share that month's market, and the 12-month windows of
consecutive months overlap. The effective sample is closer to the number of months
than to n_obs.

## Median and mean excess vs band C (whole period)

| bucket | p50 1m | p50 3m | p50 6m | p50 12m | mean 12m |
|---|---|---|---|---|---|
| top5 | +0.6% | +0.6% | +0.0% | −6.0% | +15.0% |
| top20 | −0.2% | −0.1% | −0.7% | −3.1% | +12.2% |
| 20_40 | −0.4% | −0.6% | −1.2% | −5.3% | +3.9% |
| 40_60 | −0.8% | −1.4% | −3.4% | −9.6% | −0.4% |
| 60_100 | −2.1% | −5.8% | −10.2% | −19.7% | −9.7% |

The medians are below the means because each stock's returns are skewed: most shares
trail an equal-weight average, and a few rise a great deal. The buckets stay in order
at every horizon.

## Stability check (two halves, split at Nov 2015)

| | H1 (2005-01 to 2015-10) | H2 (2015-11 to 2026-09) |
|---|---|---|
| top5 p50 at 1 / 3 / 6 / 12 m | +1.7% / +1.5% / −0.2% / −6.2% | −0.4% / +0.1% / +0.2% / −5.9% |
| top20 p50 at 1 / 3 / 6 / 12 m | −0.4% / +0.1% / −0.8% / −3.8% | −0.1% / −0.2% / −0.7% / −2.8% |
| top5 mean at 12 m | +10.8% | +18.3% |
| top20 mean at 12 m | +13.0% | +11.5% |
| 60_100 p50 at 12 m | −21.0% | −18.6% |

The medians differ by less than 2 points between the halves. The order of the buckets
and the p10 and p90 levels are similar in both halves. The tails are a little wider in
H2. The 12-month mean of `top5` moves more, because it depends on a few large winners.
At 12 months, the top fifth's average excess was positive in 72% of entry months and
the top 5%'s in 61%.

## Caveats

* The figures come from past data and will not repeat exactly. The selection rules were
  developed on part of this same history, so the top buckets may look somewhat better
  here than they will live.
* Before 2018 the research panel was the only source. The vendor file holds almost no
  dead companies before then, so it could not be used to cross-check those years.
* No costs or tax are included. Band C shares have modelled half-spreads of about
  0.35% to 0.6% per side.
* Use the bands for the bucket the share was in when it was bought. Its later bucket is
  not used.
