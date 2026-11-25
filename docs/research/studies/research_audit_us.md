---
id: research_audit_us
title: "Audit of all the US research"
date: 2026-11-25
kind: review
market: US
verdict: mixed
verdict_note: "no hidden edge"
question: "Did a mistake in our US tests hide a winning strategy?"
answer: "One real bug, takeovers counted as total losses, was found and fixed. No verdict changed. Super contributions are the biggest lever we had undersold."
trials: 9
n_total: 3238
ledger_seq: 105
confidence: solid
report: null
---
## Summary
- Some companies that were taken over were counted as if shareholders lost everything. Fixing it moved results by 0 to 0.45 points a year.
- No strategy passed after the fix. Insider buying came closest, but still shows no lead after 2010.
- Most other small biases favoured the strategies, not the index fund.
- A dollar of salary into super becomes about 70 cents; paid to you and invested, about 53 cents.

## Key numbers
| What | Number |
|---|---|
| Change from fixing the takeover bug | 0.0 to 0.45 points a year |
| Largest US t on any rule | 2.3, a control added afterwards |
| Luck bar counting only US tests | t 2.7 |
| Salary dollar in super v invested personally | about 70c v 53c |

## What it means for you
Your super is the first place for new money: salary sacrifice up to the cap, in your fund's index option. Invest the rest in an Australian-listed index fund, in lumps of $2,000 or more. Ask your accountant about the cap.

## How sure are we?
The auditor read the actual code and re-ran every affected test once, with the fix locked in first. Nothing it found would have turned a loser into a winner.
