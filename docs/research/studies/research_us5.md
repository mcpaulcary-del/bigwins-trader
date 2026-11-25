---
id: research_us5
title: "Every signal and machine learning on big US companies"
date: 2026-11-25
kind: study
market: US
verdict: closed
question: "Can a machine-learning model that combines every signal, news included, beat an S&P 500 fund after tax on years it has never seen?"
answer: "No. News did not help, no model beat the fund in development, and the final model lost by about 3 points a year on the sealed years."
trials: 57
n_total: 3229
ledger_seq: 104
confidence: solid
report: null
---
## Summary
- The models used 17 price signals, insider buying, news sentiment and market conditions, with 12 model types including if-then rule sets.
- News sentiment only exists from 2021 and did not predict returns.
- No model or mix beat the S&P 500 fund after tax on 2010-2023. Extra if-then logic made results worse, not better.
- The final model, tested once on the sealed years 2023-2026, made 10.1% a year after tax against 12.7% for the fund.
- The models did pick slightly better than random shares, but the index's biggest companies did better still.

## Key numbers
| What | Number |
|---|---|
| Sealed years, personal: model v S&P 500 fund v Nasdaq-100 fund | 10.1% v 12.7% v 13.7% a year |
| Sealed years, in super: model v S&P 500 fund | 11.8% v 15.1% a year |
| Best development lead over the fund (personal) | -0.1 points a year |
| Chance the best development result was luck (overfitting) | 66%; 88-93% for the if-then versions |
| Pass marks met | none |

## What it means for you
This closes the US share-picking research after five rounds and over 150 tests. Keep your index fund as the core, inside super where possible, held for more than 12 months.

## How sure are we?
The final test was locked in before it ran and used years no model had seen. The best development result had a t of 0.76 against a pass mark of 2.0.
