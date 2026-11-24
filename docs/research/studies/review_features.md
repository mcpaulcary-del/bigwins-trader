---
id: review_features
title: "App review: scoreboard, costs, health, digest"
date: 2026-11-24
kind: app_review
market: app
verdict: closed
verdict_note: "fixed"
question: "Are the new honest-scoreboard screens correct and safe to install?"
answer: "Safe: nothing in them can place an order or leak a secret. Four small faults were found and fixed before installing."
trials: 0
n_total: null
ledger_seq: null
confidence: solid
report: null
---
## Summary
- Nothing in the new screens can place an order, touch the broker or leak a secret.
- The scoreboard's sums were right, but it said "after all costs" while leaving out tax. It now says "after running costs, before tax" until your tax rate is set.
- The running-costs verdict blamed trading when the server and data bills were about 80% of the cost. Fixed.
- Paper lines were not ranked or highlighted, as intended.
- 837 automated tests passed.

## Key numbers
| What | Number |
|---|---|
| Must-fix items found | 4 |
| Automated tests passed | 837 |
| Paper lines ranked or highlighted | none |

## What it means for you
The scoreboard on Home can be trusted to be honest about what it counts. Set your tax rate in the app so it can show the after-tax figure.

## How sure are we?
An independent read of the code and a full test run. Fixes are recorded as BF-D81.
