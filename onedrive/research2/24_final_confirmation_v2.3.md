# Final confirmation review of FD v2.3 (13 Nov 2026)

**Verdict: v2.3 was not final as written, but nothing in it is Critical. With the fixes in this report applied it is ready to build. They are applied in `FD_v2.4.md`, which is the final specification.**

Reviewed: `FD_v2.3.md` in full (change log, Part A, Part B), against research reports 11–21, the red-team review (report 22) and the final review of v2.2 (report 23). I ran the editor's check script (`verify_v23.py`): every check passed. I used no new research. Figures tagged [computed] are arithmetic on numbers already in the spec or the reports.

## Counts

| Severity | New findings |
| --- | --- |
| Critical | 0 |
| High | 3 |
| Medium | 6 |
| Low | 8 |
| **Total** | **17** (K-01 to K-17) |

Plus four resolutions of the items the v2.3 editor left open (items a to d). Item a was itself a High-level defect (a deadlock at go-live for an account with existing holdings).

Severity scale, as in report 23: **Critical** = a path to losing money or being unable to exit; **High** = a build agent must guess, a gate cannot be evaluated, or a halt fires in normal use; **Medium** = ambiguity or false alarm with a contained effect; **Low** = wording, labels, tidy-up.

## 1. Verification of report 23 (N-01 to N-43 and rulings 1–5)

"Yes" means the fix text is in v2.3 and does what the finding asked. I read every Critical and High fix in full, at every location the change log names, and every Medium and Low fix at its cited location.

| Finding | Sev | Claimed | Verified | Note |
| --- | --- | --- | --- | --- |
| N-01 | Critical | Applied | Yes | `OrderIntent.kind` keeps the original kind; `carried_from` added to `OrderIntent`, `plan_lines` and `order_intents`; RSK-01, PRT-27 and the `HALTED_BUYS` bullet pass carried transition and withdrawal sells; the netting paragraph is in §3. The exit path F-02 closed stays closed. Residual: same-side lines can be added twice (K-01) |
| N-02 | High | Applied | Yes | PRT-16(b) carries the fix text; PRT-19 subtracts `withdrawal_due`. First-day arithmetic re-checked: VGS buy about A$2,860, under the RSK-06 limit of A$3,150 [computed]. Residual: (b) does not see the buys step (a) planned (K-01) |
| N-03 | High | Applied-modified | Yes | PRT-16(a) state reconciliation and BP-03 are as written. The modification (listing the planning days) is needed and correct. Residual: one clearing path is missing from the list (K-02) |
| N-04 | High | Applied-modified | Yes | `open_orders()` reads the whole account; BP-02, `FOREIGN_ORDER`, I16 and the G3 criterion are present. Residual: other text still says "cancel every open order" (K-05) |
| N-05 | High | Applied | Yes | RSK-26(ii) counts only `transition` and `band`. Residual: drill orders are transitions (K-03) |
| N-06 | High | Applied-modified | Yes | Shared settings, RND-012, H1 row, RSK-07, RND-022, RND-023 and `adv20` agree. Residual: the proxy tax assumptions had no source (item d) |
| N-07 to N-23 | Medium | Applied (N-08 modified) | Yes | Each fix text found at its location. N-08's change (GST not read from `commissionReport`; accrual explained in either direction) is sound. N-15 residual: RSK-13 (K-04). N-20 residual: paper-mode start (K-16) |
| N-24 to N-43 | Low | Applied (N-28, N-30 modified) | Yes | N-28: the M8 list correctly leaves out USR-06 and USR-12. N-30: dropping the drawdown clause from H11's fail column is right; the same reasoning was not applied to H1 (item b) |
| Ruling 1 | — | Applied | Yes | `KILLED` paragraph, manual fallback, §15 row, BP-05, BP-12, O3 |
| Ruling 2 | — | Applied-modified | Yes | Sections 7–9 are stubs; the archive is a separate file; CI rule added. Withdrawn IDs appear only in stubs and withdrawal notes |
| Ruling 3 | — | Applied | Yes | USR-11 |
| Ruling 4 | — | Applied | Yes | `shared_host` is gone from USR-10, §12, §18, §19, O10, I11, M8; USR-06 and USR-12 withdrawn |
| Ruling 5 | — | Applied | Yes | Stale change-log lines corrected; `null` placeholder; TAX-10 to TAX-13 note |

Totals in CL-G (37 applied, 6 applied-modified) are correct. No fix is missing and none was applied wrongly.

## 2. New findings

### High

| ID | Sev | Where | Problem | Evidence | Fix |
| --- | --- | --- | --- | --- | --- |
| K-01 | High | PRT-16 (a) and (b), §3 netting, PRT-27 | The steps of a planning day do not see each other. Step (a) plans a re-entry buy to target. Step (b) then computes investable cash and the sleeve's shortfall from the book alone, where that buy is neither held nor an "open buy", and plans the same money again. The netting rule adds same-side lines. Example at A$5,000: VAS turns ON with VGS already held; (a) plans a A$2,000 VAS buy; (b) finds A$1,950 investable and a A$2,000 VAS shortfall and plans it again [computed]. RSK-13 or RSK-06 then rejects, and an RSK-06 rejection latches `HALTED_INTEGRITY` on a re-entry day. The same doubt exists between a carried line and a new line in one symbol and side. The breaker stops the order, so this is High, not Critical | PRT-16(b) "shortfall = target value − current value − value of open buys"; §3 "netted in units"; RSK-06 "latch" | PRT-16 intro: "each step sees what the earlier steps planned today: a buy planned earlier today counts as already held at the reference price, and its value is taken out of investable cash; the proceeds of a sell planned today are never counted as cash. Target minus actual is computed once per symbol and side, so on a planning day the new plan replaces a carried line in the same symbol and side and is never added to it." (b): subtract "the value of the buys planned in (a)" from investable cash and from the shortfall. §3 netting: one sentence saying same-side lines are never added twice |
| K-02 | High | PRT-16, PRT-20, §10, §12 | `HALTED_INTEGRITY` is cleared by `trader resume` or by `trader reconcile --accept`. Only `resume` makes the next day a planning day. After `reconcile --accept` the daily blocked-sell page stops, and a sleeve that is OFF but still held is not sold until the next execution date, up to a month later. This is the N-03 gap on one path | §4 "persists until `trader reconcile --accept --note` or `trader resume`"; §10 "On `trader resume` …"; PRT-16 list of planning days | Add "after `trader reconcile --accept` clears a halt" to the planning days in PRT-16, PRT-20, §10 and §12, and to the commands that only create plan lines (EXE-12, §4) |
| K-03 | High | RSK-26(ii), G3, EXE-12 | G3 needs at least 40 order events and allows forced-signal drills to reach them. A drill "plans the resulting transition", so its orders are kind `transition`. RSK-26(ii) halts buys above 12 filled transition or band intents in 12 months. G3 as written sets `COST_HALT` after the twelfth drill order and cannot be completed [computed] | G3 row; EXE-12; RSK-26 | RSK-26(ii): "Orders planned from a drill revision (EXE-12) are not counted either." EXE-12: the `--end` revision is also flagged `drill`, and plan lines from a drill revision are marked (`plan_lines.drill`) |

### Medium

| ID | Sev | Where | Problem | Evidence | Fix |
| --- | --- | --- | --- | --- | --- |
| K-04 | Medium | RSK-13, EXE-12 | The canary buys one unit of each sleeve whatever its state. For a sleeve that is OFF the target weight is zero, so RSK-13 (post-trade weight ≤ target × 1.26) rejects the buy. Nothing says what happens if a canary buy does not fill, or where "once per account" is recorded | RSK-13; EXE-12; PRT-17 (exempts the canary from the minimum order only) | RSK-13: a canary buy of at most `canary_units` is exempt. EXE-12: the canary is complete when each buy is filled and reconciled; the ledger records it per account id; an unfilled canary carries under PRT-27 and may be repeated if it lapses |
| K-05 | Medium | §4 `cancel_unfilled`, §10 `KILLED`, §11 step 7, LED-06, BP-02 | N-04 made `open_orders()` return every order in the account. The text still says "cancel every open order" at 15:30, on `KILLED` and in LED-06, which now includes the user's own orders, in any instrument. BP-02 says the system never cancels a foreign order. Also, a foreign order that blocks a risk-off sell pages once and gives no order-sheet line | BP-02 against the three "every open order" sentences; N-36 gave the order-sheet line to the other blocked-sell cases | Say "every open order of this system (matched by `orderRef`)" in all four places. BP-02: if the blocked intent is a sell, the page repeats each trading day and attaches an order-sheet line; orders in symbols outside the universe are ignored |
| K-06 | Medium | §12 NAV and unit price, OPS-06 | NAV is total cash plus every position at its "validated raw close". Unmanaged holdings outside the universe have no validated close (the vendor fetch covers VAS, VGS and DHHF only), and the unit price, drawdown, RSK-22 and both benchmark comparisons then include holdings the system does not manage. A distribution from an unmanaged holding looks like a gain. A manual trade in another instrument on a broker day is a cash difference the system cannot explain before Flex | §12 NAV formula; `data.eodhd.instruments`; Flex timing rule | Unit price, drawdown and benchmark comparisons use managed NAV = NAV − unmanaged holdings (valued at the Flex mark). Cash caused by an unmanaged holding is an external flow. OPS-06 tells the user at init that manual trades in the account on a broker day can halt the system |
| K-07 | Medium | OPS-06 | A user who tags an existing VAS or VGS holding `managed` hands it to the rule. If the sleeve's bootstrapped state is OFF, the first plan sells the whole holding (PRT-16(a)), realising every gain in it. Nothing shows this before the tag is set. This is the largest single tax event the system can cause | OPS-06; PRT-16(a); R18 (no discount under 12 months; discount ends for events from 1 July 2027) | OPS-06: before a holding is tagged `managed`, `trader init` prints the sleeve's bootstrapped state, the sells the first plan would make and the estimated realised gain, and needs a typed confirmation. New owner item O16 |
| K-08 | Medium | PRT-19, §15, O7 | Cash above `capital_cap_aud` is "uncommitted" and is never invested. A user who contributes A$500 a month without raising the cap leaves every contribution idle, and nothing says so. Section 30 calls contributions the main lever | PRT-19; PRT-16(b) "− uncommitted cash" | PRT-19: while uncommitted cash is above zero, every plan and the daily digest show it with a WARN. O7 says the cap must cover planned contributions |
| K-09 | Medium | RND-012, RND-027, RSK-22 | (a) H1's statistic is "on monthly returns", but the account size, cost and tax basis are not stated; only the after-tax figures have defaults. Builder and validator can differ. (b) RSK-22 reads "the bootstrap distribution from the G2 report" by horizon, but no requirement makes the G2 report produce it | RND-012; RND-027 list; RSK-22 | RND-012: the statistic is on monthly unit-price returns net of the section 25 costs and before tax, at sizing NAV A$50,000 with no contributions; reported, not tested, at A$5,000. RND-027: the pack contains the drawdown envelope (95th and 99th percentiles of maximum drawdown for each horizon from 12 months) and it is stored with the H1 result |

### Low

| ID | Sev | Where | Problem | Fix |
| --- | --- | --- | --- | --- |
| K-10 | Low | PRT-16(c) | "The matching buy" of a band rebalance is not defined (which sleeve, what amount, what if the other sleeve is OFF) | The matching buy is the sale proceeds bought in the ON sleeve or sleeves below target, sized as in (b), on the day the proceeds settle; with no such sleeve the rebalance is skipped |
| K-11 | Low | SYS-03, PRT-23, VAL-23 | "If H1 fails" leaves out "not passed" (RND-015) and "not testable" (RND-029). OPS-12 already refuses L1 in those cases; the prose should agree | "If H1 does not pass (failed, not passed or not testable)…" |
| K-12 | Low | H12, O15 | H12 halves the measured benefit and then requires H1 to pass. H1 needs 25%, so L1 needs a measured drawdown reduction of at least 50% [computed]. This is R20's design and is right to keep, but the owner should see the real bar before freezing the cards | State the 50% in the H12 row and in O15 |
| K-13 | Low | PRT-28 | The amount a withdrawal sell must raise is not stated | "X − settled cash + `cash_reserve_aud` − sale proceeds not yet settled, plus the modelled commission of the sells" |
| K-14 | Low | TAX-01 | With FIFO, a system sale could be matched to an older unmanaged parcel of the same ETF | "A system sale is matched only to parcels flagged `managed`" |
| K-15 | Low | §12 mutability | `hypotheses` holds status, result, decision and approver, which must change after a card is frozen, but the table is not in the list of updatable columns | Add those four fields; card content and hash never change |
| K-16 | Low | EXE-12, G3, I14 | "The paper account starts each run by buying `canary_units`" does not say how (the canary command is live-only). G3 needs an ex-distribution date in paper, and I14 asks whether the paper account books distributions, with no fallback | In paper mode `trader init` plans the canary buys. If the paper account books no distributions, the ex-distribution case runs in `paper_sim` and the G3 report says so |
| K-17 | Low | §3 `RunContext` | The pure `build_orders()` has no input that tells it why today is a planning day or that a canary was requested | Add `RunContext.requests` |

## 3. Resolutions of the four open items

### (a) Canary when the user tags existing VAS/VGS holdings as managed

**Resolution: the canary runs once in every live account before the first live plan, whether or not managed units are already held. Drop "while managed units are zero"; keep "once per account", now recorded in the ledger.**

- In v2.3 this was a deadlock. EXE-12 allowed the canary only with zero managed units, and OPS-06 and PRT-16 made the first live plan wait for the canary. An account with tagged holdings could never trade.
- The other option, skipping the canary for such accounts, removes the control exactly where the first order is largest. With an existing holding in a sleeve that is OFF, the first live order is a sale of the whole holding.
- The research supports the canary as a step, not as a property of an empty account: R17's BP-OPS-03 is "paper, shadow and canary gate", and BP-14 says "a canary at minimum size, then full". Report 22 F-20 added "while managed units are zero" only to stop the command being used as a way to place repeated orders; "once per account" already does that.
- Cost: two minimum commissions (A$13.20, already in the cost table). The extra units join the holding. If the sleeve is OFF they are sold with it on the next day.
- Needed with it: K-04 (RSK-13 exemption, completion record) and K-07 (the user sees the sells and the estimated gain before tagging).

### (b) H1's fail column still fails on after-tax CAGR

**Resolution: align with the primary-metric design. H1's fail column is "drawdown reduction below 10% (relative)" only.**

- RND-010 allows exactly one primary metric, and RND-015 needs pass and fail to be exclusive. With the after-tax clause, a run could meet the pass rule (drawdown) and the fail rule (after-tax cost) at once. Report 23 N-30 removed the same conflict from H11.
- Nothing is lost. H2 runs at H1's settings and fails if the after-tax CAGR difference is below −1.5 pp. H11 tests the same 1.5 pp at the account holder's rate under both regimes. VAL-23 requires both at G2.
- R20's original H1 row had the clause. The departure is recorded in the H1 row and in CL-I.

### (c) §9.1 says L1 "is expected to cost a little return"

**Resolution: "L1 is a drawdown overlay, not a return source: it is expected to cost return, by an amount that is uncertain (section 1, expectations table), in exchange for smaller worst losses."** Section 30's "cost some return" is changed the same way.

- R20's own sentence is "this overlay is expected to cost return in exchange for shallower drawdowns". No report says the cost is small. R11's estimate is −0.5% a year with a range of −2% to +1%, and N-29 already removed "small, known" from section 1.

### (d) Proxy distribution yield and franking assumptions with no source

**Resolution: the values are measured from stored distribution data, not chosen, and each card records the source.**

- No report gives usable values. R13's "roughly 3% blended distributions" and R11's franking estimate are tagged [unverified]; R12's "about 1.5% a year" has one source. Putting any of them in the spec as a default would break the rule that every number is traceable.
- The spec already has a sourced route: issuer distribution amounts are the truth (DAT-14), the vendor's dividend rows carry franking credits (R19), and E2 checks three years of them against issuer figures.
- Rule, added to the section 24 shared settings. Each card fixes two values per proxy before it is frozen: a cash distribution yield and a franking-credit ratio (franking credits ÷ cash distributions). They are computed from the stored `distribution` rows of the ETF the proxy stands for, over every complete financial year in the store and at least the three years checked under E2. Yield = the year's cash distributions per unit ÷ the mean month-end raw close, averaged across years. The values are constant over the proxy era. The card lists the values, the years, the row count, the share of issuer-entered rows and the data hash, and shows the VAS figures beside R19's 64–88% franking and R12's 1.5% with a reason for any disagreement.
- H2 and H11 are also reported, not tested, with the yield at zero and with the ratio at zero, so the reader sees how much the result depends on the assumption.
- The ratio is used instead of a "franking percentage" so that no company tax rate, which is in no report, is needed to turn a percentage into a credit.

## 4. Checked and found sound

- **Traceability.** I re-traced the numbers I changed or relied on (R11 −0.5% and 5–8%; R20 H1 row; R19 franking 64–88%; R12 1.5%; R13 3% [unverified]; R18 Priority 2 and 3; R17 BP-OPS-03; report 22 F-12 and F-20). The cost totals, A$9,375, the worked example and the all-in shortfall are arithmetically right [computed]. I found no number without a source or a tag.
- **Tax against report 18.** Act number and dates, the discount cut-off, indexation (residents, 12 months, gains only), the deemed sale with the deferred slice, Division 119 scope and exemption, the 45-day LIFO test, the A$5,000 exemption with the trust caveat, and the capital/revenue flag all match R18. Gaps found: K-07 and K-14.
- **Money safety.** Sells are capped at broker-reported managed units; buys use settled cash only; a same-day sell never funds a buy; limit orders only; never resend on a timeout; cancel confirmed before a replacement; whole-account open orders; paper/live guard on the account id. Every state that blocks a sell now gives the user a daily page and an order-sheet line (integrity halt, `KILLED`, missed login, held order, BLOCK verdict, corporate action, and after K-05 a foreign order).
- **Idle cash.** Limited to OFF sleeves, the A$50 reserve, amounts below the A$1,000 minimum, and uncommitted cash above the cap, which is now shown (K-08).
- **Honesty.** No return claim. Item c and K-12 were the two places where the text was kinder than the evidence.

## 5. Verdict

**No Critical finding. `FD_v2.4.md` is written with every fix above applied and is final: ready to build.**

- v2.3 as written would have stopped at three points a build agent or the owner would hit: a re-entry day (K-01), G3 drills (K-03) and go-live with existing holdings (item a). None could lose money; each halts or blocks.
- No new requirement ID, config key or reason code is added in v2.4. The changes are to existing requirement text, two table columns, one flag, one interface field and one owner item (O16).
- `verify_v24.py` (adapted from the editor's script) passes every check on `FD_v2.4.md`.
- What remains open is listed in section 21 of the spec. None of it is a spec defect; each item needs the owner, a tax agent, EODHD, IBKR or a public source.
