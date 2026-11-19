# Amendment: paper line `PAIR` (registered EMG2-18 rules and the frozen BLIND3 primary as two equal members of ONE A$10,000 account)

Status: **REGISTERED 19 Nov 2026 — PAPER ONLY, information only**, by the record keeper, before the first decision it governs (Mon 30 Nov 2026), at the coordinating session's request of 19 Nov 2026 (report 92 section 7 item 3: register if the owner or the coordinating session agrees). Text = the research agent's draft `deep92/AMENDMENT_shadow_PAIR.DRAFT.md` (Fable, report 92 section 3; SHA-256 in `deep92/out/blind4_hashes.txt`) with sections 2–6 unchanged, a section 7 recording the owner decision proposed for June 2027, and the record keeper's implementation section R. It changes nothing in any live or paper amendment (`AMENDMENT_live_EMG2_18.md`, `AMENDMENT_live_EMG2_18_loss_rule_v2.md`, `AMENDMENT_shadow_EMG2_18_H6.md`, `AMENDMENT_shadow_EMG2_COMBO.md`, `AMENDMENT_shadow_BLIND3.md` stay as registered). It is not a candidate under the adopt rule. The owner may close the line at any time by a later entry. The AI never places trades.

## 1. Why
- The registered "50/50 reading" (`AMENDMENT_shadow_BLIND3.md` section 4) is the average of two A$10,000 books. That is a A$20,000 account. An owner with A$10,000 cannot hold it: half of each book is 9 names of each, and a 9-name book is not half of an 18-name book.
- `PAIR` is the book a A$10,000 owner could actually hold: one account, one cash balance, one tax account, each rule set deciding on half of it.
- **Recorded plainly: the pair was put together after both members had been seen on 2018–2026. Its back-test (report 92 section 3) is not evidence.** The forward record is the only clean test.

## 2. Rules
One account of A$10,000 from the 30 Nov 2026 decision. Month-end clock, fills at the next session's close, IBKR fixed brokerage, the modelled half-spread of the blind-3 kit (`acct3.py`), tax as the kit.

Two members. Each member is shown a sub-book: the holdings it bought itself, an account value equal to **half the whole account** (its share), and its own memory. Each decides by its own registered rules as if that sub-book were its whole account:
- **Member E** = the rules of `EMG2_18_SIM` (band, score, target list, buy filter, sell rule L4, takeover-pin rule) with rule L3 read on its share: n = min(18, floor(share ÷ A$550)), parcel = share ÷ n. At the start that is 9 names of about A$555.
- **Member B** = `BLIND3` (PREREG_BLIND3 section 1) unchanged: parcel = max(1/15, A$520 ÷ share) of its share, at most 15 names. At the start that is 9 names of A$520.

Merging (exactly `tools4.Ensemble` of `deep92/blind4_kit/tools4.py`, SHA-256 in `deep92/out/blind4_hashes.txt`):
1. Every member's sells go through unchanged.
2. A company held, or sold at this decision, by the other member is skipped and the member's next choice is taken.
3. Members claim companies in turn; the member that goes first alternates by calendar month.
4. A member's order is sent as a first order only while its share has room for at least half of it (room = share less the value of its holdings) and it holds fewer names than its own limit. Further orders are reserves that fill only if a first order is refused.
5. The halves are never traded back to equal. A member above its half cannot buy until it sells; a member below its half buys from the pooled cash.
6. One A$50 reserve; A$500 minimum buy; 5% of 20-session median traded value; duplicate-company refusal; payout rule: all as the kit engine.

## 3. Books
| Book | Start |
|---|---|
| `PAIR_10k` | A$10,000 at the 30 Nov 2026 decision |
| `PAIR_RND_10k_s001…s100` | same; member E's twin as `EMG2_18_RND` (redraw 0.2), member B's twin as `BLIND3_RND` (redraw 0.2101); member seeds 1000 × (8800000 + i) + {0, 1} |
| Comparator | A200 at A$0 brokerage, same clock |

## 4. Reading
- Monthly, beside `EMG2_18_REF`, `BLIND3_10k` and the registered 50/50 reading: value, percentile among its own twins, orders, brokerage, modelled spread, tax, worst fall on daily values, names held by each member, and how often the two members wanted the same company.
- Facts: orders and costs. Mostly luck, and labelled so: the value gaps to `EMG2_18_REF` and to `BLIND3_10k`.
- Never evidence for or against EMG2 or BLIND3. No proposal for real money without a separate owner decision (report 92 section 4 sets out what that decision would need).

## 5. Trial count
The pair's back-test is counted in report 92 (one design). Registering the line adds no trial.

## 6. Seen-data figures (report 92 section 3; `deep92/out/ensu_read_panel.log`, `ensu_read_vendor.log`)
See report 92 section 3, table "One account". They are on a period both members were chosen or judged on.

## 7. Owner decision in June 2027 (recorded here; nothing is automatic)
Report 92 section 4.3 proposes, and this entry records, that **in June 2027 the owner decides** whether to convert the live book to the pair at a month-end. It is put to the owner only if all four hold:
1. the trading system runs the two-member account and has matched this paper line order for order for at least three months;
2. the spread measured on live EMG2-18 fills is no more than 1.5 times the model;
3. `PAIR_10k` is at or above the median of its own twins since the start (a check that nothing is broken, not a test of skill);
4. blind build 4 has been judged, so the owner sees how a set fares on a list nobody chose with hindsight.

A conversion would run through the normal rules: the EMG2 half shrinks to its share as holdings are sold by its own sell rule; nothing is sold to rebalance. Until the owner answers, the 24-month paper requirement of `AMENDMENT_shadow_BLIND3.md` section 4 stands for BLIND3 alone (report 92 s7 item 4: no owner answer recorded; "slow, not wrong"). No live rule changes by this entry: EMG2-18 goes live in December as registered.

## R. Paper-record implementation (record keeper's addition; mechanics only, no rule above is changed)
- Code `bigwins_forward/code/paper_pair.py`, called by `paper_daily.py` after `paper_blind3.py`; own state file `pair_state.json`; never writes the H82 state or another line's state (reads `emg2s_state.json` and `blind3_state.json` for the reading only). Same month-end bundle as the EMG2 paper lines (`paper_emg2.get_bundle`). Orders file `shadow/pair_orders_<date>.csv` (book, member, type, code, weight, cost rank, fill, rule).
- **Merging = `tools4.Ensemble` unmodified**: `deep92/blind4_kit/tools4.py` copied byte for byte to `code/pair_frozen/tools4.py` (b70dcbb7…, SHA-256-checked at import) and bound to the frozen `acct3.py` of `code/blind3_frozen/` (16486f50…, identical to the blind-4 kit's). Members in the order of the seen-data run (`deep92/code/ens92.py`, book C50U): **member 0 = B, member 1 = E**; so the member that claims first is E in odd-numbered calendar months (e.g. November) and B in even ones. Each holding remembers its member in the state file.
- **Member B** = the builder's frozen `strategy.factory(E, None)` on `paper_blind3.FEngine` (exactly as the BLIND3 line), shown its sub-book.
- **Member E** = the EMG2-18 lists of `paper_emg2.table` on the same bundle: sell a holding that is off the target list T (L4) or bid-pegged; buy T best first, skipping names held, in the lottery class (`paper_emg2s.lottery`), bid-pegged, without a trade on the decision day or without a close; n = min(18, floor(share ÷ A$550)), each order 1/n of its share (sent as 1/(2n) of the account, as the Ensemble does). L1's A$10,000 sizing cap is not applied to the share (draft section 2 and the seen-data run size on the share; it could bind only once the account passes A$20,000).
- **Accounting = the kit's, as `paper_blind3.py`** for both members: fills at the next session's close, sells first (a sell without a close stays open up to 5 sessions), `acct3.fee`, `acct3.half_spread` on the decision-day place for every order (so member E pays the kit's modelled spread, not L9's 0.50%), buys of at least A$500 and at most cash less A$50 and 5% of the 20-session median traded value, duplicate-return refusal (correlation > 0.98 over 60 sessions), buys stop at the Ensemble's cap, whole shares, June tax 32% (367-day halving, losses carried, FIFO), cash dividends and splits from the daily bulk file, payout of a holding with no close for more than 20 sessions by the kit's rule. A holding whose entity is missing from the month-end data is sold (as BLIND3; this includes a code change).
- **Data blocks.** H82 market-wide block, or a bundle not ending on the decision day: no decision, holdings kept. Member B's own block (fewer than 300 valid ordinary shares in the top 400) or member E's (fewer than 150 names in band C): that member sells and buys nothing that month-end; the other member decides as usual. Both blocked: no decision.
- **Twins** `PAIR_RND_10k_s001…s100`: member B's twin as `paper_blind3` (persistent random score over the ordinary shares placed ≤ 800, redrawn with probability 0.2101 a month), member E's twin as `paper_emg2s.lists_for` (persistent random score over band C, redrawn with probability 0.2, top len(T) non-pegged names as its T); member seeds 1000 × (8800000 + i) + 0 (B) and + 1 (E). Comparator `PAIR_CMP_A200_10k` (A200, A$0 brokerage).
- **Reading** on the scorecard after the BLIND3 rows: value, return, percentile among its twins and their median, A200 (A$0), "sold today after tax", orders, brokerage, modelled spread, tax, worst fall on daily values, names held by each member, how many companies both members wanted at the last decision (kept per decision in the state), and — labelled mostly luck — the gaps to `EMG2_18_REF`, `BLIND3_10k` and the registered 50/50 reading.
- Checks before registration (scratch copies only, `rk92/t/`): paper_daily current vs new code on a synthetic 20 Nov day — H82 state byte-identical (f0f6f215…), PAIR not started; PAIR forced to start 17 Nov with forced decisions 17–20 Nov on the 16 Nov forward bundle — straight run = resume after a crash before the 18 Nov save = rerun = a second straight run (pair state dc6d45c3…), H82 unchanged; 9 + 9 names on the first fill, first-day brokerage A$118.80 (report 92: A$119); rule checks (member E's L4 sell, a blocked member does nothing, each member's claims follow its own list, weights 0.052 and 1/18, month order) all pass.
- Known data risk as `AMENDMENT_shadow_BLIND3.md` section R: an in-specie distribution arrives as a price fall with no dividend or split row (see the corporate-action amendment of the same date).
