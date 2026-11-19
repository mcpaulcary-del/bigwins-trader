# Final review of FD v2.2 (13 Nov 2026)

**Verdict: not ready to build as written. Ready after one editing pass.** Milestones M0 and M1 can start now. M2 (decision core and breaker), M3 (harness) and M4 (execution) are blocked by one Critical and five High findings, plus rulings 1, 2 and 4 below. Every blocker is a text patch given in this report; none needs new research or a new owner decision beyond the five rulings.

Reviewed: `FD_v2.2.md` in full, against research reports 11–21 and the red-team review (report 22). I did not edit the spec and ran nothing. Figures tagged [computed] are arithmetic on numbers in the spec or the reports. Facts I use that are in no report are tagged [unverified].

## Counts

| Severity | New findings |
| --- | --- |
| Critical | 1 |
| High | 5 |
| Medium | 17 |
| Low | 20 |
| **Total** | **43** |

Previous findings: all 66 fix texts are present in v2.2 (54 applied, 12 applied-modified, as CL-E claims). None is missing. Five of the fixes are in the text but leave or create a defect: F-14 (see N-02), F-04 (N-05), F-28 and F-41 (N-01), F-34 (N-07).

## Blockers

1. **N-01 (Critical).** A carried risk-off sell loses its kind, so the buys-only halt can reject it. This reopens the exit-blocking path F-02 closed.
2. **N-02 (High).** The top-up rule buys the largest-shortfall sleeve up to 120% of target. On the first deployment that order breaks RSK-06 and latches `HALTED_INTEGRITY`.
3. **N-03 (High).** Orders come only from transitions, top-ups and bands. A sleeve that is OFF but still held is never sold.
4. **N-04 (High).** Open orders are read for the system's own API client only. A manual order from the order sheet is invisible, so a second order can be sent beside it.
5. **N-05 (High).** The 12-month order count includes top-ups, the canary and the initial deployment. An ordinary first year reaches the cost halt.
6. **N-06 (High).** H1 cannot run as written: at its A$50,000 default it needs three intra-month tranches on monthly data, and the production functions need unit prices and volumes that index proxies do not have.
7. **Rulings 1, 2 and 4** change text in sections 4, 7–11, 14 and 19.

## (a) Verification of the 66 previous findings

"Yes" means the fix text is in v2.2 and does what the finding asked. I read every Critical and High fix in full and every Medium and Low fix at its cited location.

| Finding | Claimed | Verified | Note |
| --- | --- | --- | --- |
| F-01 | Applied | Yes | RSK-03, RSK-06, RSK-12, BP-04 match. BP-04's acceptance test covers the drifted full exit |
| F-02 | Applied-modified | Yes | Two halt classes in §4, §10, RSK-01, RND-031, O3. Residual: carried sells (N-01); `KILLED` (ruling 1); `CORP_ACTION` scope (N-11) |
| F-03 | Applied-modified | Yes | Flex timing rule, LED-02, LED-04. Residual: announced withdrawals and GST are not listed as explained deficits (N-07, N-08) |
| F-04 | Applied | Yes, with a new defect | Order-count measure is in RSK-26 and §18, but it counts user-driven orders (N-05) |
| F-05 | Applied-modified | Yes | OPS-13, PAGE list, SYS-17 |
| F-06 | Applied-modified | Yes | `flex_pull` row, DAT-02 cases (a) and (b), I3, I14, token warning |
| F-07 | Applied | Yes | PRT-14, C4, O2, offsets for N = 4. A$9,375 is correct [computed]. Residual: N falling is undefined (N-18) |
| F-08 | Applied | Yes | DAT-22, DAT-11. Residual: detection depends on the vendor (N-10) |
| F-09 | Applied-modified | Yes | VAL-22, RND-011, `research.families` |
| F-10 | Applied | Yes | H12 row, VAL-23 |
| F-11 | Applied-modified | Yes | H11 row, O13. Residual: H11 now has two primary metrics (N-30) |
| F-12 | Applied | Yes | RND-012, H1 row, RSK-22, `mean_block_months: 12`. Residual: the p-value is still not computable from the text (N-17) |
| F-13 | Applied | Yes | §24 shared settings. Residual: H1 itself still implies N = 3 (N-06) |
| F-14 | Applied | Yes, with a new defect | PRT-16(b), RSK-13, O7 carry the fix text. The fix text conflicts with RSK-06 (N-02) |
| F-15 | Applied | Yes | PRT-19, G5, `cap_rise_staging`. Residual: top-up ignores uncommitted cash (N-02) |
| F-16 | Applied | Yes | RND-021, RND-024, H10 variant, I9 blocks G0 |
| F-17 | Applied | Yes | PRT-22 and `benchmarks` config |
| F-18 | Applied | Yes | RSK-24, RSK-26, G3 |
| F-19 | Applied | Yes | §11 steps 2 and 7, BP-03, `cancel_confirm_timeout_s` |
| F-20 | Applied | Yes | EXE-12, CLI list, "Before G4" row |
| F-21 | Applied | Yes | Manual fallback, RSK-33, BP-20. Residual: API barrier before Flex (N-21) |
| F-22 | Applied | Yes | Pricing steps 2–4, DAT-13, RSK-08, `max_quote_spread` |
| F-23 | Applied | Yes | §12 NAV, LED-04, PRT-22 |
| F-24 | Applied | Yes | Cost table and totals re-added correctly [computed]; §1; §30 item 4; `full_redownload`; §5.1; O6 |
| F-25 | Applied-modified | Yes | `tax` config, TAX-03, H11, OPS-12, T1, T2, T4, T5, P9. Residual: the YAML placeholder is not a number (N-25) |
| F-26 | Applied | Yes | PRT-16(c) |
| F-27 | Applied | Yes | DAT-20, PRT-19. Residual: harness and paper start without the unit (N-15) |
| F-28 | Applied | Yes, with a new defect | PRT-27; conflicting schedule phrases removed. `kind: 'carried'` hides the original kind (N-01) |
| F-29 | Applied | Yes | RSK-11, default 6 |
| F-30 | Applied | Yes | DAT-13 |
| F-31 | Applied | Yes | MON-01, BP-12, `heartbeat` row |
| F-32 | Applied | Yes | 07:00 retry, DAT-01 |
| F-33 | Applied | Yes | OPS-06 |
| F-34 | Applied | Yes, incomplete | PRT-28, PRT-20, `cashflow_expected`. Timing and double counting undefined (N-07) |
| F-35 | Applied | Yes | TAX-05, `parcels.source`, T12 |
| F-36 | Applied | Yes | TAX-07 |
| F-37 | Applied-modified | Yes | USR-09 as a standing rule with tests |
| F-38 | Applied | Yes | H2, PRT-25, RND-014, VAL-27 all say +0.5 pp |
| F-39 | Applied-modified | Yes | RND-025, VAL-21, VAL-23, `holdout open`. Residual: the lock also stops replay (N-12) |
| F-40 | Applied | Yes | H1 grid and battery row |
| F-41 | Applied | Yes, with a new defect | Signature, plan/send split, `OrderIntent`. `kind` and `client_order_id` do not support netting or carry (N-01) |
| F-42 | Applied | Yes | Run-state paragraph |
| F-43 | Applied | Yes | §11 step 5 |
| F-44 | Applied | Yes | §26 intro, Stage 2 row, M9 |
| F-45 | Applied | Yes | Containers table, `a.yaml`, USR-12 |
| F-46 | Applied | Yes | §30 item 4, §1. A$230–275 is correct [computed] |
| F-47 | Applied | Yes | RSK-30(3), RSK-27 |
| F-48 | Applied | Yes | `mode: STATIC`, OPS-12 |
| F-49 | Applied | Yes | DAT-02 |
| F-50 | Applied | Yes | G1 |
| F-51 | Applied | Yes | §27 Stage 1 |
| F-52 | Applied | Yes | T1 |
| F-53 | Applied | Yes | SYS-01 |
| F-54 | Applied | Yes | §30 Process lever, USR-13 |
| F-55 | Applied | Yes | CLI list, BP-05 |
| F-56 | Applied-modified | Yes | Milestone ranges exclude withdrawn IDs; BP-14 is defined once, in §28. I checked every live ID against §20: all are covered (USR-07 is in the wrong milestone, N-28) |
| F-57 | Applied-modified | Yes | All ten numbers are keys under `ops` or `tax_defaults`; turnover key renamed |
| F-58 | Applied | Yes | `spec_hash` and `card_set_hash` |
| F-59 | Applied | Yes | 01:30 |
| F-60 | Applied | Yes | BP-09, SYS-06 |
| F-61 | Applied | Yes | PRT-22 |
| F-62 | Applied | Yes | Time-in-force note, I15 |
| F-63 | Applied-modified | Yes | `owner_host`. See ruling 4 |
| F-64 | Applied | Yes | TAX-09, TAX-02 |
| F-65 | Applied | Yes | Calendar row, P5. The other 2026–27 dates and weekdays check out [computed] |
| F-66 | Applied | Yes | §21.7 |

## (b) New findings

Severity: **Critical** = a path to losing money or being unable to exit; **High** = a build agent must guess, a gate cannot be evaluated, or a halt fires in normal use; **Medium** = ambiguity or false alarm with a contained effect; **Low** = wording, labels, tidy-up.

### Critical

| ID | Sev | Where | Problem | Evidence | Exact replacement text |
| --- | --- | --- | --- | --- | --- |
| N-01 | Critical | §3 `OrderIntent.kind`, `plan_lines.kind`, RSK-01, PRT-27, §11 `orderRef` | A carried intent has `kind = 'carried'`, so its original kind is lost. RSK-01 under `HALTED_BUYS` "passes transition sells and withdrawal sells"; a carried sell is neither. A literal build rejects it. The case is real: a drawdown halt is set at 08:05, the risk-off sell is held on E by `SNAPSHOT_GAP` (prices gapping more than 2%) or part-fills, and it carries to the next day as `carried`. Separately, `client_order_id` is `{user}-{E}-{symbol}-{side}-{attempt}`, so two plan lines in one symbol and side on one day (transition and withdrawal, or transition and top-up) collide, and a transition sell with a top-up buy in one symbol breaks RSK-04. | RSK-01 row; `OrderIntent` comment; PRT-27; §11 order construction | `OrderIntent`: `kind: str  # 'transition', 'top-up', 'band', 'withdrawal' or 'canary'; a carried intent keeps its original kind` and add `carried_from: date | None`. `plan_lines`: remove `carried` from the kind list; add column `carried_from`. RSK-01: "`HALTED_BUYS` rejects every buy and every band-rebalance sell, and passes transition sells and withdrawal sells, including carried ones." PRT-27 add: "A carried intent keeps its kind. Carried transition and withdrawal sells are sent under `HALTED_BUYS`." Add to §3 after "Plan time and send time": "**Netting.** `build_orders()` emits at most one intent per symbol per day. Plan lines of different kinds in one symbol are netted in units; the intent's `kind` is the kind of the largest line on the surviving side, and `plan_lines` keeps every line. Under `HALTED_BUYS` the buy and band lines are removed before netting, so a transition or withdrawal sell is never reduced by a blocked buy." |

### High

| ID | Sev | Where | Problem | Evidence | Exact replacement text |
| --- | --- | --- | --- | --- | --- |
| N-02 | High | PRT-16(b), PRT-19, RSK-06, OPS-06, PRT-23 | (a) The top-up places "one buy of that amount" (all investable cash) in the largest-shortfall sleeve, limited only by weight ≤ target × 1.2. Initial deployment is a top-up, because a bootstrapped ON state is not a transition. After the canary, investable cash is about A$4,700; the VGS buy is limited to 72% of A$5,000 = A$3,600, so the order is about A$3,460. RSK-06 allows 1.05 × 0.60 × 5,000 = A$3,150, rejects it and latches `HALTED_INTEGRITY` on the first deployment day [computed; canary unit prices assumed]. If RSK-06 did not exist the account would start at about 72/27 instead of 60/40. The same happens in `STATIC` mode, which is the shipped default. (b) Investable cash does not subtract uncommitted cash (PRT-19) or an announced withdrawal, so money above `capital_cap_aud` is invested up to the band. (c) "Largest shortfall" is undefined when no sleeve is below target. | PRT-16(b); RSK-06; OPS-06 "Initial deployment follows the bootstrapped state" | PRT-16(b): "**Top-up.** Investable cash = settled cash − `cash_reserve_aud` − uncommitted cash (PRT-19) − `withdrawal_due` (PRT-28) − Σ over OFF tranches of (base weight ÷ N × sizing NAV). The shortfall of an ON sleeve = target value − current value − value of open buys; it may be negative. While investable cash ≥ `min_order_value_aud`: take the ON sleeve with the largest shortfall that has no top-up yet today. Buy amount = min(investable cash, max(shortfall, `min_order_value_aud`)). If the cash left after this buy would be below `min_order_value_aud`, it is added to this buy. The amount is then reduced so that the sleeve's post-trade weight ≤ target × (1 + `band_relative`) and the order value ≤ the RSK-06 limit. If the reduced amount is below `min_order_value_aud` the sleeve gets no top-up (`MIN_ORDER`). Subtract the amount and continue with the next ON sleeve. At most one top-up per sleeve per day. This is how initial deployment, contributions and distributions are invested, before any sell." [design value — set by backtest, card H4] |
| N-03 | High | PRT-16(a), BP-03, OPS-06, PRT-23, `/veto … SELL` | The spec has two order models. PRT-16 is event-driven: orders arise only from a state change, a top-up or a band. BP-03 is state-based: "order quantity is always target minus broker-actual". They differ whenever a sleeve is OFF but still held with no transition at this evaluation: a managed holding tagged at `trader init` whose bootstrapped state is OFF; a switch from `STATIC` to `L1`; a sell the user vetoed last month. Under PRT-16 nothing ever sells those units, so the account carries risk the rule says to exit. The build agent must guess which model wins. | PRT-16 "Only on the execution date … (a) for a sleeve whose tranche changed state"; BP-03 | PRT-16(a): "**Transition and state reconciliation.** Target units for every sleeve are computed from the latest tranche states (PRT-15, PRT-19). A sleeve whose tranche changed state at this evaluation is traded to its new target. In addition, on every execution date, and on the first full trading day after `trader init`, `trader resume` or a mode change, a sleeve whose target weight is zero and whose managed units exceed the sentinel floor is sold down to the floor (plan kind `transition`, exempt from the minimum order), whatever the reason the units are still held. A vetoed sell is therefore planned again at the next evaluation. A sleeve with at least one ON tranche that is above target is handled only by (c)." BP-03 add: "For buys, 'target' is the amount PRT-16 allows, not the full target weight." |
| N-04 | High | `Broker.open_orders()`, BP-02, RSK-03, RSK-04, §11 step 2, manual fallback | The manual order sheet is a designed route (missed login, integrity halt, and `KILLED` after ruling 1). The user enters the order in IBKR Mobile. R17 row 11 says `reqOpenOrders` "returns only the same clientId's orders". If the user's order is still working (a GTC order, or a DAY order on the same day the gateway recovers), the system's open-quantity terms do not see it, the next carried intent is sized from position alone, and both orders can fill. For a partial sell (N = 3, a withdrawal) or any buy this is a real duplicate. | R17 row 11; §11 step 2 "open buy quantity + open sell quantity … read at send time" | Interface: `def open_orders(self) -> list[BrokerOrder]: ...  # every open order in the account, from any API client or manual entry (reqAllOpenOrders)`. BP-02 add: "Open orders are read for the whole account, not only for this API client [R17]. An open order in a managed symbol that does not carry this system's `orderRef` is a foreign order: no system order is sent in that symbol while it is open, and the user is paged. The system never cancels a foreign order. Acceptance test: with a manual resting order in VAS, the system sends nothing in VAS." Manual fallback add: "The sheet tells the user to enter DAY orders only." New open item I16: "`reqAllOpenOrders` from client 11 returns orders entered in IBKR Mobile and Client Portal. Paper test. Blocks G3." |
| N-05 | High | RSK-26(ii), `order_count_12m`, §19 cost table | Below A$25,000 the cost halt counts every "intent with at least one fill". That includes the canary, the initial deployment and every top-up. First year with A$500 a month and R15's expected one round trip per sleeve: canary 2 + deployment 2 + top-ups 6 + round trips 4 = 14, above the halt at 12 [computed]. `COST_HALT` then blocks the next re-entry and the next contribution. F-04 set the thresholds for whipsaw (rule-driven) orders only. | RSK-26; PRT-16(b); R15 D3 "about one round trip or fewer per sleeve per year" | RSK-26(ii), replace the last sentence: "Below that, the measure is the count, over 12 months, of filled intents whose kind is `transition` or `band`. Top-up, withdrawal and canary orders are user-driven; they are not counted here and are covered by the commission WARN in PRT-21." |
| N-06 | High | H1, RND-012, RND-020, RND-024, RND-028, §24 shared settings | G2 cannot be evaluated as written. (a) H1 is "exactly section 9.1" at sizing NAV A$50,000. PRT-14 then gives N = 3 with offsets `[last, 7, 14]`, which monthly data cannot represent. (b) The harness must call the production `build_orders()` and `RiskManager.apply()`, which need a unit price (whole units), `adv20` (RSK-07), a verdict and a limit price. Index proxies have none of these. (c) The tax model needs distributions and franking; a total-return index has neither. Builder and validator will make different choices and G2's "two implementations agree" fails. | VAL-21 "monthly total-return index proxies"; PRT-14; `MarketSnapshot.adv20`; RND-022 | Add to §24 shared settings: "**Running the production functions on index proxies.** Each proxy becomes a unit-price series by rebasing the index level to the ETF's first validated raw close at the splice date. Units are whole. Every proxy bar has verdict `OK` and source `backfill`. `adv20` is not available: RSK-07 is skipped and logged as not evaluated. There is no quote: the limit price equals the fill price of RND-028, so DAT-13, RSK-08 and RSK-09 always pass. Development runs on monthly data use N = 1 and offset `last` at every NAV; tranche counts above 1 are tested only by H5 on daily data. For the tax model each card fixes, per proxy, an assumed cash distribution yield and franking percentage, paid quarterly out of the total-return series [design value — set by backtest; no report gives these values]." RND-012, H1 defaults, add: "N = 1, offset `last`." |

### Medium

| ID | Sev | Where | Problem | Evidence | Exact replacement text |
| --- | --- | --- | --- | --- | --- |
| N-07 | Medium | PRT-28, Flex timing rule, PRT-19 | (a) "From the next execution date" means the day after the next monthly evaluation, so a withdrawal can wait a month. (b) Committed capital falls by X on announcement and cumulative net flows fall by X again when Flex books the transfer. (c) When the user makes the transfer, IBKR cash is below ledger cash until Flex arrives: an "unexplained deficit", so `HALTED_INTEGRITY` at once. (d) A typing error (`-5000` for `-500`) liquidates the account; sells "proceed regardless" of plan delivery. | PRT-28; Flex timing rule; OPS-04 | PRT-28: "**Withdrawals.** `trader cashflow --expect -X` prints the sells it would plan and needs a typed confirmation. An announced withdrawal sets `withdrawal_due` = X at once; X is excluded from investable cash (PRT-16(b)) and from sizing NAV. If settled cash less `cash_reserve_aud` is below X, sells are planned for the next full trading day, pro rata to current value across the sleeves that hold units above the sentinel floor, rounded up to whole units (plan kind `withdrawal`, exempt from the minimum order). When Flex books a withdrawal it is matched to the oldest open `cashflow_expected` row; the row is closed and `withdrawal_due` falls by the booked amount, so the flow is counted once. An announced withdrawal not booked within 10 trading days [design value — operational] lapses with a WARN. Withdrawal sells are allowed under `HALTED_BUYS` and blocked under `HALTED_INTEGRITY` and `KILLED`. The system never moves money out of IBKR; the user makes the transfer." Flex timing rule, deficit bullet, add: "A deficit that is at most an open announced withdrawal (PRT-28) is `PENDING_FLEX`, not a break." |
| N-08 | Medium | §11 step 6, `Fill.gst`, LED-02, I1 | Fills are recorded "from `execDetails` and `commissionReport` (… commission, GST)". `commissionReport` has no GST field [unverified — not in any report]. If IBKR charges GST as a separate line, ledger cash is high by 10% of commission after every trade, which is an unexplained deficit above A$0.01, so `HALTED_INTEGRITY` at 15:45 on every broker day, including the day a part-filled exit must carry. I1 leaves the GST treatment open until "the first real statement". | R13 "GST treatment conflicts"; LED-02 tolerance A$0.01; `flex_pending_fee_types` | §11 step 6 add: "`fills.gst` is filled from Flex. Until I1 is answered the ledger accrues GST at `execution.commission.gst_rate` of each commission as a pending fee of type `commission_gst`, confirmed or reversed by Flex." Config: `commission: {…, gst_rate: 0.10}` and `flex_pending_fee_types: [snapshot_fee, withholding, commission_gst]`. I1 "Blocks": "the canary reconciliation (Before G4)". |
| N-09 | Medium | DAT-13, RSK-08, §11 pricing step 3 | The 2% test compares the limit with the last close. On an ex-date the price opens lower by the distribution. With the default offset `last`, E is the first trading day of the month, which is where VAS ex-dates usually fall [unverified]. A sell on that day is held by a 1–2% distribution plus a small market move. v2.0 handled this ("reference price = close minus any cash dividend going ex on E") and v2.2 dropped it. | v2.0 §9 step 5 (archive); DAT-13 | DAT-13 add: "The reference for DAT-13 and RSK-08 is the last validated raw close minus any cash distribution per unit with an ex-date after that close and on or before today [A]." |
| N-10 | Medium | DAT-22, §5 Distributions, DAT-14 | §5 says "an ex-date that arrives with no entered amount blocks the sleeve". DAT-22 only detects this when the vendor reports the dividend or the adjusted/raw ratio moves. If the vendor is late too, `tr_net` drops by the distribution and can flip a vote. Nothing stores the expected ex-date. | DAT-22; §17 "Before each ex-date" | DAT-22 add: "Each quarter the user enters the next expected ex-date of every live ETF as a `distribution` row with status `expected` and no amount. From an expected ex-date onward, a row with no amount blocks the sleeve (`DIST_MISSING`) whether or not the vendor has reported the dividend. A WARN is raised when a live ETF has no future `expected` row." `distribution.status`: `expected`, `estimated` or `final`. |
| N-11 | Medium | §4 reason codes, §10 halt classes, SYS-23, RSK-02 | SYS-23 freezes the symbol. §4 and §10 list `CORP_ACTION` as a reason for `HALTED_INTEGRITY`, which stops every order in the account. A corporate action in VGS would then block a risk-off sell of VAS, whose position and price are not in doubt. | SYS-23 "the symbol is frozen"; §10 first bullet | Remove `CORP_ACTION` from the `HALTED_INTEGRITY` reasons in §4 and §10. Add to §10: "A corporate action freezes its own symbol only (RSK-02, `CORP_ACTION`); the other sleeve trades normally. The PAGE names any blocked sell in the frozen symbol and attaches an order-sheet line for it. A unit-count mismatch against the broker is a reconciliation break (LED-01) and does set `HALTED_INTEGRITY`." |
| N-12 | Medium | RND-025, RSK-24, G3, MON-07, RND-029 | The harness "refuses to load any date from 2024-01 onward" until the holdout is opened. The G3 fidelity test, the monthly tracking replay and the CUSUM all run the harness on 2026–27 dates. If H1 cannot be tested (no licensed history, RND-029) the account runs static mode, the holdout is never opened, and G3 cannot run. | RND-025; RSK-24 "Replay = the harness run over the same dates" | RND-025 add: "The lock applies to card runs. Replay runs (`trader replay`, RSK-24, the G3 fidelity test, MON-07) and the live bootstrap replay of `decide()` (OPS-06) may read data after 2024-01 without opening the holdout. They use recorded decisions and fills, compute no card metric, are logged with replication kind `replay`, and are not trials. A test shows a card run cannot be started through the replay path." |
| N-13 | Medium | RSK-22, OPS-12, PRT-23, RND-029 | OPS-12 refuses any live account without `backtest_max_drawdown` "from the G2 report". In static mode after an untestable or failed H1 there may be no such figure. And `DRAWDOWN_HALT` in static mode only blocks contributions during a fall; a static holding has no exit for the halt to protect. No report supports that. | OPS-12; RSK-22; R14 D8 "a review trigger, not a kill switch" | RSK-22 add: "In `STATIC` mode RSK-22 has review triggers only (PAGE at a 25% drawdown and at each further 10 points [design value — operational]) and never sets `DRAWDOWN_HALT`." OPS-12: replace "or `risk_defaults.backtest_max_drawdown` is unset for a live account" with "or `risk_defaults.backtest_max_drawdown` is unset for a live account in `mode: L1`". |
| N-14 | Medium | OPS-06, §4 Execution date, G4 | "Initial deployment … on the first execution date after the canary." An execution date exists only after an evaluation, so A$5,000 can sit in cash for up to a month for no reason the evidence supports. | OPS-06; §4 definition of E | OPS-06, replace the last sentence: "Initial deployment is planned from the bootstrapped state as PRT-16(b) top-up buys on the first full trading day after the canary fills are reconciled; it does not wait for the next evaluation date. A managed holding in a sleeve whose bootstrapped state is OFF is sold under PRT-16(a). The harness starts every run the same way." |
| N-15 | Medium | EXE-12, PRT-17, DAT-20, §17 "Before G4" | (a) The canary is a buy of about A$100–150 [unit prices unverified]. PRT-17 skips buys below A$1,000 and exempts only transition and withdrawal sells. (b) ASX brokers commonly refuse a first purchase below the A$500 minimum marketable parcel [unverified — not in any report]; R17 lists "IBKR Australia … minimum order sizes" as unverified, and the spec has no open item for it. (c) Live starts with one unit per sleeve; the harness and paper account start with none, so they are not identical when a sleeve starts OFF. | PRT-17; R17 "Still [unverified]" list; DAT-20 "so harness, paper and live behave identically" | PRT-17: "Transition sells, withdrawal sells (PRT-28) and canary buys (EXE-12) are exempt." EXE-12 add: "If IBKR refuses a buy below the ASX minimum marketable parcel (I17), `canary_units` is set per sleeve to the smallest whole number of units worth at least A$500. The harness and the paper account start each run by buying `canary_units` of each live sleeve at the modelled cost." New open item I17: "IBKR accepts a first ASX buy of one ETF unit (below A$500). Support, paper test. Blocks the canary." |
| N-16 | Medium | §4 `KILLED`, BP-05, BP-11, RND-032, `reconcile --accept` | "A second factor" is required for `trader resume` and limit changes but is never defined. `trader reconcile --accept --note`, which writes a balancing cash or parcel row and clears an integrity halt, needs none. | BP-11; §12 last paragraph | Add to §15: "The second factor is a 6-digit TOTP code (RFC 6238) from an authenticator app enrolled at `trader init`; its seed is a Docker secret readable only by `trader-<user>` [design value — operational]. `trader resume`, `trader reconcile --accept`, `trader mode`, `trader stage` and any config change that loosens a limit require it." |
| N-17 | Medium | RND-012 H1 defaults, RND-003 | The null and statistic are stated but not how p is computed, and no seed is fixed. Builder and validator can both be right and disagree. | RND-012; G2 "the two implementations agree" | RND-012 add: "p = the share of the 10,000 bootstrap paths in which (B2 maximum drawdown − L1 maximum drawdown) ≤ 0. Each path resamples the paired monthly return rows of L1 and B2 with the same indices. The random seed is recorded in the card. Builder and validator must agree on p within 0.01." |
| N-18 | Medium | PRT-14, PRT-17, OPS-12 | N = 3 starts at A$9,375, where the smallest tranche buy is A$1,250. A 20% fall in sizing NAV puts it below A$1,000; the re-entry buy is then skipped every month and that tranche stays in cash until the yearly review. What happens when N must fall is not defined. Not relevant at A$5,000. | PRT-14 "never in between"; PRT-17 | PRT-14 add: "If at a yearly review the condition no longer holds, N returns to 1 from the next evaluation: a sleeve is ON if at least two of its three tranches are ON, otherwise OFF, and the resulting trade is a transition. Between reviews a transition buy is skipped only below half of `min_order_value_aud` [design value — set by backtest, card H5]." |
| N-19 | Medium | PRT-19, §11 step 2, BP-03 | Two buy-quantity formulas. PRT-19: floor(cash-limited value ÷ limit price). §11 step 2: target units − position − open buys + open sells, where target units use the close. With the ask up to 2% above the close the second can exceed the first. | PRT-19; §11 step 2 | PRT-19, replace the two buy-quantity sentences: "Buy quantity = floor(buy amount ÷ limit price). The buy amount comes from PRT-16(a) or (b) and is recomputed at send time from the broker-reported position, open orders and settled cash (BP-03); it never exceeds settled cash − `cash_reserve_aud`." §11 step 2 add: "For sells. For buys the same broker-reported values feed the PRT-19 buy amount." |
| N-20 | Medium | EXE-12, G3, CLI, SYS-17 | `trader drill` is required by G3 but has no behaviour: how a forced signal enters insert-only tranche state, how it is undone, and how the replay treats it. For `canary`, `resume`, `mode` and `cashflow --expect` the spec does not say whether an order is placed when the command is typed, which OPS-03 forbids outside 11:30–15:00. | EXE-12; G3 row; OPS-03 | EXE-12 add: "`trader drill --sleeve S --to ON|OFF` inserts a `tranche_state` revision flagged `drill` for the next full trading day and plans the resulting transition through the normal cycle. `trader drill --end` inserts a revision that restores the state `decide()` gives from the data. Drill revisions are passed to the replay as recorded decisions (RSK-24). `tranche_state` gains a `drill` boolean. No command places an order when it is typed: `canary`, `drill`, `resume`, `mode` and `cashflow --expect` only create plan lines for the next full trading day's normal cycle (plan, veto window, 11:30)." |
| N-21 | Medium | Manual fallback, BP-02, LED-01 | A manual order-sheet trade is booked "from Flex". If the next API reconciliation (a carried intent's barrier) runs before that Flex report, the position differs from the ledger and LED-01 sets `HALTED_INTEGRITY`. Unmatched lines never close. | §11 manual fallback; LED-01 "Exact" | Manual fallback add: "While a `MANUAL_PENDING` line is open, a position and cash difference at an API reconciliation that is consistent with a fill of that line (same symbol and side, quantity ≤ the sheet quantity) is `PENDING_FLEX`, not a break; the next Flex report confirms it or makes it a break. A line not matched within `manual_match_days` is closed as `skipped`." |
| N-22 | Medium | §14 own-account statement, D10 | "The rules below are built so that none of those acts happens" and D10's "the structure contains none of those acts" are legal conclusions. R18 marks the business test [unverified] and asks a lawyer whether "supplying the software free to up to five people" is advice or arranging; R11 asks whether "default parameters amount to financial product advice". The release ships the rule, weights and defaults to every user. The owner may decide not to ask a lawyer; the spec may not state the answer. | R18 lawyer Q1; R11 §8 Q2; USR-11 "obtains the tagged release" | §14: replace that sentence with "The rules below are intended to keep each of those acts out of the structure. Whether they succeed is a legal question no report answers. R11 and R18 both ask, and neither answers, whether supplying the software free, with its default rule and settings, to up to five people is itself advice or arranging." D10 "Why": replace "so the structure contains none of those acts" with "so the structure is designed to avoid those acts (not confirmed by a lawyer)". Add the same sentence to §21.7. |
| N-23 | Medium | §19 cost table, §1 expectations, §30 item 4 | The cost statement omits costs the spec itself requires. Every top-up is A$6.60; at A$500 a month that is about six more trades, +A$39.60 a year (0.8%) [computed]. One-off: the canary (2 × A$6.60); rented index history if O5 takes the Norgate route, A$346.50 ex GST = about A$381 (7.6% of A$5,000) [computed]; and a tax agent's written advice, required before G4 (fee not researched). R13's mini-PC price of A$280 comes from expired deals; it lists retail at A$390–490. | R13 §1, §5; R19 Norgate prices; "Before G4" row | Cost table, add rows: "Top-ups of contributions (PRT-16(b)), A$6.60 each: about 6 a year at A$500 a month | +39.60 | +39.60" and "One-off before go-live: canary 13.20; index-history rental if O5 chooses it, about 381; tax agent's written advice (fee not researched) | not in the totals | not in the totals". Mini-PC row note: add "A$280 is from expired deals; retail is A$390–490 [R13]". §30 item 4 add: "Each contribution top-up costs A$6.60. One-off set-up costs (rented index history of about A$381 if that route is chosen, the canary, a tax agent's fee) can exceed a year of running costs." |

### Low

| ID | Sev | Where | Problem | Exact replacement text |
| --- | --- | --- | --- | --- |
| N-24 | Low | TAX-01 | `MIN_TAX` parcel method has no definition; R18 asks only for "a CGT parcel-selection method". | "…using `parcel_method` (FIFO default; HIFO optional)." Delete `MIN_TAX`. |
| N-25 | Low | §18 `research.marginal_rates` | `lowest_nonzero_resident` is a word in a list of numbers; pydantic validation and the OPS-12 comparison fail at M0. | `marginal_rates: [0.00, null, 0.30, 0.37, 0.45]   # null is filled from open item P9 before G0; OPS-12 ignores null` |
| N-26 | Low | §18, §12 | Numbers and stores used in prose with no key or table: the Medicare levy (H1, H11 "plus Medicare"); the franking "realisable rate" in `tr_gross`; the CPI series for TAX-04; the EODHD call counter (DAT-23 must survive a restart); the 33-snapshot allowance (EXE-11). User `tranche_offsets` and common `tranche_offsets_by_n` overlap. | Add `tax_defaults.medicare_levy: 0.02   # [R13 mention only; confirm with T2]`, `tax.franking_realisable_rate: 1.0`, `execution.snapshot_free_per_month: 33`. Add tables `cpi (quarter, value, source, fetch time)` and `vendor_call_log (ts, vendor, endpoint, gmt_date)` to `market_<user>`. USR-13: "With N = 1 the user's `tranche_offsets` overrides the common default; with N = 3 the common offsets apply." |
| N-27 | Low | ENG-02 vs OPS-05 | ENG-02 says session dates "come from" the library; OPS-05 says they come from the hand-loaded table and the library is a cross-check. | ENG-02: "XASX session dates follow OPS-05. For XNYS the pinned library is the source, cross-checked each run against IBKR `ContractDetails` trading hours." |
| N-28 | Low | §20 M8 | USR-07 (acceptance of the expectations statement) is required before G4 but sits in M8, which "is not needed for the owner's A$5,000 live system". | Move USR-07 to M6. M8 accepts "USR-01, USR-03 to USR-06, USR-08 to USR-14". |
| N-29 | Low | §1 first paragraph | "At a small, known cost in expected return" is not true at A$5,000: the spec's own all-in shortfall is 4.6–5.5% a year and the range is wide. | "…against a buy-and-hold benchmark, at a cost in expected return that is uncertain and, at A$5,000, large (see the expectations table)." |
| N-30 | Low | H11, T9 | H11's primary metric has two conditions (RND-010 allows one). T9 (CPI source) is asked of the tax agent but H11 setting (b) needs it for G2. | H11 primary metric: "After-tax CAGR no more than 1.5 pp below B2 after tax at the rate tested, under both regimes. Secondary: maximum drawdown reduction (H1's metric), terminal-wealth ratio." T9 "Blocks": "G2 for H11 setting (b); the card names the CPI series used until the agent answers". |
| N-31 | Low | §6 total-return formula | The formula has no split term, so a consolidation or split breaks `tr_net` after `corp-action apply`. | "TR_t = TR_{t−1} × (P_t × s_t + D_t) ÷ P_{t−1}, where s_t is the unit ratio of any split or consolidation effective on t (1 otherwise)." |
| N-32 | Low | §4, BP-07, MON-01, §15 | Small undefined timings. | §4: "A `NEEDS_REVIEW` intent still unresolved at 15:45 sets `HALTED_INTEGRITY`." BP-07: "After a restart later than 08:30 the 3-hour rule does not apply; OPS-02's 11:30–15:00 window does." MON-01: "The Flex check-in is sent when the job runs, whether or not the report has arrived." Daily digest: "NAV is as at the last validated close, and the digest shows that date." §4 Execution date: "An evaluation whose E would be an early-close day is decided on the morning of the next full trading day." |
| N-33 | Low | §21.2 | Two tax questions that follow from R18 but are not asked: how capital-gain components attributed by VAS and VGS (AMIT) are treated after 1 July 2027, and whether the Medicare levy counts toward the tax "already borne" in the 30% floor. | Add T13: "How are capital-gain components attributed by VAS and VGS treated from 1 July 2027 (discount at trust level, minimum tax)? Blocks the 2027–28 tax report." T2 add: "Does the Medicare levy count toward the tax the gain already bears?" |
| N-34 | Low | OPS-05, DAT-08 | The January evaluation needs next year's calendar; nothing warns if it is not loaded. | OPS-05 add: "A WARN is raised when the `calendar` table covers fewer than 60 days ahead." |
| N-35 | Low | RND-021 | "The fund's management fee" is in the cost model for every run; ETF prices already carry it. | "…the fund's management fee on proxy-era data only (RND-024)…" |
| N-36 | Low | §11 pricing step 3, DAT-17 | A sell held by `SNAPSHOT_GAP` or stopped by a BLOCK verdict pages the user but gives no order-sheet line. | Step 3 and DAT-17 add: "If the held or blocked intent is a sell, the PAGE attaches an order-sheet line saved as `MANUAL_PENDING`." |
| N-37 | Low | EXE-08 vs I4 | EXE-08 says the settled-cash test is "before G4"; I4 and the G3 row say G3. | EXE-08: "A paper test before G3 confirms…" |
| N-38 | Low | PRT-27, PRT-20, OPS-04 | Whether a vetoed intent carries is not stated. PRT-20's exception list omits catch-up evaluations and post-resume planning. | PRT-27 add: "A vetoed intent is not carried; it is planned again at the next evaluation." PRT-20: add "a catch-up evaluation (OPS-13) and the plan made after `trader resume`" to the exceptions. |
| N-39 | Low | §12 `instrument`, SYS-20, SYS-32 | Table is `instrument` in §12 and `instruments` in SYS-20 and SYS-32. | Use `instrument` in SYS-20 and SYS-32. |
| N-40 | Low | I14 | G3 needs an ex-distribution date in paper; whether the IBKR paper account books distributions is not listed. | I14 add: "…and whether the paper account books cash distributions." |
| N-41 | Low | OPS-01, §19 | Nothing stops two runner processes for one user (a manual `trader run` beside the scheduler). Client ID 12 "for tools" has no stated limit. | OPS-01 add: "The runner holds a PostgreSQL advisory lock per user; a second runner exits." §19: "Client ID 12 is read-only: tools have no import path to `Broker.place` (SYS-18)." |
| N-42 | Low | Flex timing rule | A provisional distribution must "equal" units × announced amount. Rounding or an estimate-to-final change leaves a few cents of deficit, which halts at once if the pay date is a broker day. | "A cash difference within `ops.distribution_match_tolerance` (the larger of A$1.00 and 2% [design value — operational]) of an expected distribution…" Add the key to `ops`. |
| N-43 | Low | Change log, D9 | Stale lines. CL-B §2 row says "1–5 users with gates". CL-C says EXE-05's fill rules are "in RND-020/021"; they are in RND-028. C9 says "no automatic de-risking", but `DRAWDOWN_HALT` blocks re-entry buys until the owner resumes. D9 lists "separate machine per user" as a rejected alternative while USR-10 makes it the default for users 2–5. | CL-B: "…1–5 users under the self-run structure, no gates". CL-C: "Fill rules now in RND-028". C9: "L1 never sells on drawdown. A drawdown beyond the envelope triggers a review or a buys-only halt, which holds back re-entry and top-up buys until the owner resumes; the digest lists them daily." D9 "Rejected": "Always-on streaming data". |

### Checked and found sound

- **Traceability.** I traced the numbers in §1, §2, §5, §6, §9.1, §10, §13, §16, §17, §19, §24–27 and §29 to reports 11–21, and the EODHD plan facts to the DAT-23 citation. No untraceable number was found other than those already tagged. The cost totals, the A$9,375 threshold, the all-in shortfall and the calendar weekdays are arithmetically correct [computed].
- **Tax against report 18.** Act number and dates, the discount cut-off, indexation (residents, 12 months, gains only), the deemed sale with the deferred slice and the unchanged 12-month clock, Division 119 scope and exemption, the 45-day LIFO test, the A$5,000 exemption with the trust caveat, residency and entity refusal, and the capital/revenue flag all match. Gaps are N-26, N-30 and N-33.
- **Data budget.** VAS, VGS and DHHF need 6 calls a day and at most 18 with every retry, inside one GMT day; the Sunday diff falls in a different GMT day [computed]. All lookbacks read the local store. The job fails closed.
- **Money safety, other than the findings above.** Sells have no value limit and are capped at broker-reported managed units; buys use settled cash only; a same-day sell never funds a buy; no market orders; never resend on a timeout; the cancel is confirmed before a replacement; the paper/live guard reads the account id; unmanaged holdings are never sold; a surplus is never spent before Flex explains it.
- **Deployment of money.** The spec says plainly that holding DHHF is the better choice for wealth at this size, ships `STATIC` as the default mode, and makes L1 conditional on H1. Idle cash is limited to OFF sleeves, the A$50 reserve and amounts below the A$1,000 minimum; the cash-ETF variant is tested in H10 and I9 blocks G0. N-02, N-05, N-13 and N-14 are the places where cash would sit idle without a reason.
- **Honesty.** No return claim was found. N-22, N-23 and N-29 are the three places where the text is kinder than the evidence.

## (c) Rulings on the open items

### 1. `KILLED` blocks all sells, including risk-off exits

**Keep the block. Add the manual exit path that the integrity halt already has.**

- `KILLED` is the user's own stop, the third independent layer in §10. It has to work when the user no longer trusts the system's orders, and that includes its sells. A kill that still sends some orders is not a kill, and R17's Knight control asks for a one-step stop of everything.
- F-02's objection was to automatic halts that blocked exits without the user choosing it. `KILLED` is chosen by the user.
- The real gap is that a killed account gets no page naming blocked sells and no order sheet, and the spec does not say `decide()` keeps running. A user who kills and forgets stays in the market with no reminder.

Replace the "KILLED means" paragraph in §10 with:

> **KILLED means:** the flag is set first; then every open order is cancelled, retrying until IBKR confirms; then no new order of any kind, buy or sell, is sent until `trader resume` with a typed reason and the second factor. `KILLED` is the user's own stop and is deliberately absolute: it must work when the user no longer trusts the system's orders, including its sells. While `KILLED`: `decide()` keeps running and saving tranche state; the daily digest continues; and on every trading day on which the rule's target is below holdings, the user gets a PAGE that names each blocked sell and attaches the manual order sheet (D12). Each line is saved as `MANUAL_PENDING`, so a sell the user enters by hand is matched and is neither a break nor an override. On `trader resume` the difference between target and holdings is planned for the next full trading day, as after a halt [A], [R17], [R22 F-02].

Matching edits:

- §11 manual fallback, first sentence: "If the gateway cannot be authenticated by 11:15, or the account is `KILLED` or in `HALTED_INTEGRITY` with sells blocked, the user gets an order sheet…"
- §15 messages table: rename the row to "Integrity-halt and kill page"; When: "Each trading day while `HALTED_INTEGRITY`, or `KILLED` with a sell blocked".
- BP-05 acceptance test, add: "the kill drill shows the blocked-sell page and the order sheet arrive".
- O3, add: "`KILLED` stops every order, including exits, until the user resumes."

### 2. Archive sections 7–9 inside the build spec

**Move them out. Do not leave them in the document a build agent reads.**

- The spec's own rule is "every requirement is MUST unless it says SHOULD or MAY". The archive contains requirement tables and MUST sentences (STR-01 to STR-05, STR-10 to STR-12, PRT-01 to PRT-05, "the classifier MUST be backtested…").
- The archive contradicts live text. Step 0 still gives "Sizing NAV = min(NAV − unmanaged holdings, `capital_cap_aud`)", the formula F-15 removed. It describes an LLM classifier that feeds `decide()`, which SYS-06 forbids, and a `trader/shadow/` package.
- §20 tells CI to fail when a requirement ID has no test. A builder who greps for IDs will find the archived ones.
- The document stays self-contained without the archive: nothing live refers into it.

Action: move the v2.0 text of §7.1–7.6, §8.1–8.3 and §9 steps 0–5 (with their requirement tables and the "BHP and peers" and "Strategy research" source lists in §22) to a separate file, `FD_v2.2_appendix_A_v2.0_archive.md`, headed "Not part of the specification. Not for build." Keep the three section numbers as stubs so numbering holds. Replacement text:

> **## 7. Strategy specification (shares) — withdrawn**
>
> Not built. The v2.0 share strategy (trend, dip-buying, commodity trend, composite score, filters; STR-01 to STR-05) is withdrawn. Dip-buying and the chandelier stop are rejected outright [R12 decisions 8, 9], [R14 R1, R5], [R16]. The v2.0 text is kept only in Appendix A (`FD_v2.2_appendix_A_v2.0_archive.md`). Appendix A is not part of this specification, is not covered by `spec_hash`, and is never given to a build agent. Any future share strategy starts as a new hypothesis card (section 24) and must use point-in-time index constituents including delisted stocks.
>
> **## 8. External signals — withdrawn**
>
> Not built. The news classifier, the director-trade and downgrade vetoes and all shadow modules (STR-10 to STR-12) are withdrawn: AI may not sit in the trade path [R20 RND-002], and no automatic optimisation, online learning or regime-switching model may run live [R14 R2, R3]. The v2.0 benchmark dashboard is replaced by PRT-22 and MON-04. The v2.0 text is in Appendix A.
>
> **## 9. Portfolio construction**
>
> The v2.0 steps 0–5 and PRT-01 to PRT-05 are withdrawn; the text is in Appendix A. NAV, sizing NAV and the unit price are defined only in section 9.1 (PRT-19) and section 12. The live rule is section 9.1. The sizing engine for later stages is section 26.

Matching edits:

- "How to read", first bullet, last sentence: "`STR` and `PRT-01` to `PRT-05` are withdrawn and do not appear in this document."
- Document-control "Version" row: delete "v2.0 Part A archive sections 7–9,".
- CL-B rows for §7, §8 and §9: "status change: moved to Appendix A, not built".
- §20 code-quality rules, add: "CI fails if any code or test refers to a withdrawn requirement ID (CL-C)."

### 3. USR-02 withdrawn (no cross-user order board)

**Acceptable.**

- The board needed users to share planned orders. USR-09 forbids that, and the two cannot both stand.
- The board's purpose was to stop accounts trading against each other. Separate people with separate accounts are different beneficial owners, each order is a small marketable limit order in a deep ETF, and RSK-07 caps each at 1% of volume.
- I searched v2.2 for `USR-02`, `shared_board`, `CROSS_USER`, `users.max_live` and `data_entitlement`; they appear only in the change log and the withdrawal note.

One sentence to add, because the argument fails if one person holds two accounts:

> USR-11 add: "One person runs at most one live instance. Two accounts with the same beneficial owner are not supported, because nothing stops their orders matching each other."

### 4. `shared_host` allowed under conditions

**Not acceptable as an owner-accepted risk. Withdraw `shared_host` from v2.2. Each additional user self-hosts.** This adds no gate; it removes an option.

- OD1 allows a shared host "only if the data-licence and isolation rules hold". They cannot hold on a machine one person administers for another. USR-06 concedes "the administrator could technically reach other users' files". EODHD's personal terms fail "if other people can access the data or a service built on it" [R11] and forbid "sharing your account or API key with anyone" [R19]. USR-10 condition (b) is therefore not met by any shared host.
- R18 says that where "the owner's infrastructure places orders in other users' accounts or holds their credentials, the exemption does not obviously cover it". A shared host is exactly that case: the other user's IBKR password is a secret on the owner's machine, and the orders leave from it. R11's question on IBKR's customer agreement is also unanswered.
- The risk is not only the owner's. The other user's account, credentials and data licence are exposed, so the owner cannot accept it alone.
- `self_hosted` is already the default and is what the cost section assumes. Dropping `shared_host` also removes the gateway queue, the shared Postgres container (itself a shared dependency, against USR-03 and USR-09) and the untested five-gateway question.

Replacement text:

> **USR-10 Hosting modes** (config `hosting` per user): `owner_host` (the owner's own instance on the owner's machine) and `self_hosted` (any other user runs their instance on their own machine). There is no shared host in v2.2: config validation refuses any other value. Reasons: on a machine one person administers for another, the administrator can reach the other user's files (so the EODHD personal-licence terms cannot be met), and R18 notes that where the owner's infrastructure holds another user's credentials or places their orders the own-account exemption "does not obviously cover it". A shared host needs a spec change. [OD1], [R18], [R19], [R11]

Matching edits:

- USR-01: delete the second sentence ("On a shared host…").
- USR-06 and USR-12: withdrawn. Remove `host: {max_concurrent_gateways: 2}` from §18 and "on a shared host, of USR-06" from the `acceptances` table.
- §19 `postgres` row: "One Postgres per instance, holding `market_<user>` and `ledger_<user>`."
- §19 "Additional users": delete ", including for a shared host".
- `a.yaml` comment: `hosting: owner_host   # owner_host or self_hosted (USR-10)`.
- O10: "Whether additional users are wanted at all (each self-hosts)". I11: delete "whether five gateway sessions fit on one machine".
- §21.7, lawyer bullet: replace the last sentence with "v2.2 has no shared host, so that point does not arise."
- M8 delivers: delete "hosting modes, shared-host capacity queue".

If the owner overrules this and keeps `shared_host`, the minimum honest text is: both the owner and the user record acceptance that the EODHD personal-licence terms and the own-account exemption may not hold; each instance gets its own Postgres container; and USR-10 says "accepted risk of the owner and of that user", not of the owner alone.

### 5. Anything else unresolved in the change log

- **Stale or inexact change-log lines:** N-43 (CL-B "with gates", CL-C EXE-05 pointer, C9 wording, D9).
- **CL-E F-25:** the placeholder marginal rate breaks config validation at M0 (N-25).
- **CL-E F-14 and F-04:** applied as written, but the fix texts conflict with RSK-06 and with the contribution design (N-02, N-05).
- **CL-C ID reuse:** TAX-10 to TAX-13 are listed as void (v2.0 Part B) and are live again in §13 with new meanings. Add to that row: "The TAX-10 to TAX-13 in section 13 are new requirements, not the voided ones."
- **Owner inputs still open, correctly tracked, none a spec defect:** O1, O2, O7, O9, O13 and O15, with I9, P3 and P9, all block G0. O5 (index history) blocks G2 and decides whether H1 can be tested at all. None blocks M0–M2 code.
- **VF1 / O6 / E1:** whether the free EODHD plan serves ASX tickers is the one open fact that moves the running cost by A$275 a year. It blocks M1. The owner can settle it with one free key before M1 starts.
- **OD2 / O3:** the acceptance should also name `KILLED` (ruling 1).

## (d) Verdict

**Not ready to build as written.** It is close: the document is traceable, honest, and all 66 earlier fixes are in place.

**Blockers before M2, M3 or M4 start:**

1. N-01 (Critical): carried sells and netting.
2. N-02, N-03 (High): the two halves of PRT-16.
3. N-04 (High): whole-account open orders.
4. N-05 (High): what the cost halt counts.
5. N-06 (High): running the production functions on index proxies, and N for H1.
6. Ruling 1 (`KILLED` order sheet), ruling 2 (archive moved out), ruling 4 (`shared_host` withdrawn).

**May start now:** M0 and M1, with N-25 and N-26 applied to the config schema and N-10 to the distribution table.

**Fix with the milestone they touch:** N-07 to N-21 (M2, M4, M5), N-22 and N-23 before the expectations statement is signed, and the Low items in one editing pass.

**Suggested order of repair:** rulings 1, 2 and 4, then N-01 to N-05 in one pass over §3, §9.1, §10 and §11; then N-06, N-12 and N-17 before any card is frozen at G0; then the rest.
