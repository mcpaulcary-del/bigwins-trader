# 50. Second independent full read: FD v2.12

Report 50, Saturday 14 November 2026. General information, not personal financial advice.

## 0. Result

**FD v2.12 can be frozen. The read found 0 Critical and 0 High findings, 6 Medium and 9 Low (15 in all).** Fourteen are corrected in `FD_v2.13.md`; one Low finding is left as it is. Because no Critical or High finding was found, v2.13 carries the status **Final — v2.13 (frozen), ready to build (Live-Core profile); owner open items in §21**, and the same text is issued as `FD_FINAL_LATEST.md`.

Both High corrections of report 49 were found correct:

- **W-01, the user's stop.** After a first `/kill` no order can leave: every open order of the system is cancelled and nothing is sent or replaced until the choice is made. A `/kill` read at a start is applied in one step and is not lost. Silence ends in `KILLED`. Four edges of the pending state were not written down (V-01). None of them lets an order out under a reasonable reading, so the finding is Medium.
- **W-02, real money.** No rule in an open mode produces a buy or sell line for the index account, and every paper order sheet says it is for the paper login only. Two gaps remain in the wording, both Medium: the paper marking was listed for five kinds of message and not for every message (V-02), and a shadow sell line in advisory mode had no sentence saying it is not advice (V-03).

## 1. What was read

Every line of `FD_v2.12.md` (3,109 lines), start to finish, in order: the header and "How to read"; change logs CL-T, CL-Q, CL-R (all 400 rows), CL-S and CL-P to CL-A; Part A sections 1 to 22; Part B sections 23 to 31. Also all of report 49, targeted searches of reports 44, 47, 48, 34 and 42 for the decisions and figures the owner guidance quotes, and the header of the archive file. No earlier spec version was opened.

`verify_v212.py` passed on v2.12 before the read (0 fails), so every finding below is something a string and count check cannot see.

## 2. The questions asked

| # | Question | Answer |
| --- | --- | --- |
| 1 | Can anything be sent between the first `/kill` and `KILLED`? | No. RSK-34 cancels every open order and "sends or replaces no order of any kind" from the first `/kill`; BP-05's acceptance test sends a sell and a buy and expects neither. The breaker's input had no field for the pending state, which V-01 closes by making `RunContext.killed` true while a kill is pending |
| 2 | Can a `/kill` be lost at a restart? | No. OPS-02 applies a `/kill` found at a start in one step; the out-of-touch rule sets the flag itself after 24 hours; the pending state is in `flags`. Not said: what a restart after the window does, and that a command is acknowledged only after it is committed (V-01) |
| 3 | Does silence end in `KILLED`? | Yes. Not said: what happens when the window ends while the runner is down, or when a `/pause` stamped in time is read after `KILLED` was set (V-01) |
| 4 | Can a paper or advisory message read as an instruction to trade the real holding? | Not an order sheet, a plan or a page. A command reply that names sells was outside the listed kinds (V-02). A shadow sell line under the word "ADVISORY" carried nothing that says it is not advice (V-03). The rule against trade lines for the index account was written for advisory mode only (V-03) |
| 5 | Real-money guard | Holds. SYS-33 refuses `sheet`, `live_auto`, `ibkr.mode: live` and a live cap above 0 unconditionally in the group A and B builds; EXE-12 stops unless the account id starts `DU`; no live gateway or live credential exists. One comment in section 18 said otherwise (V-11); OPS-18 had a rule that could hold on one day only, which fails closed (V-13) |
| 6 | Advisory release without `[LC-X]` | Buildable. The W-06 note is right. The run records of advisory mode had no stated home (V-05); group B needs the paper `trader init` from OPS-06 in the same way (V-15) |
| 7 | Section 18 against the prose and section 3 | Consistent: `flex_pull` 16:30 with retries to 19:00, `kill_confirm_window_min` 10, the order-count multiples, the real-money keys, the review dates, the stop date. `RunContext` had no pending state (V-01). Five numbers have no key (V-14, not changed) |
| 8 | CA-01 status table | The nine corrections of W-09 are right. One row disagrees with RSK-34 on a same-day sell after `/pause` (V-07) |
| 9 | Flex timing | Choice (a) is consistent through section 4, DAT-01, DAT-02, DAT-04, LED-01, TAX-05 and BP-16. One window still assumed the morning pull: an order-sheet line can be closed before the statement that would match it arrives (V-06) |
| 10 | Ledgers | The three-ledger split is right. The backup list and the `postgres` row left out the external ledger (V-04); notional paper cash broke LED-04 (V-08); a late-imported contribution could back-date a paper flow (V-09) |
| 11 | Tax | The engine rules and the 30 June 2027 snapshot read correctly, including for units outside IBKR. A notional book could have reached the facts bundle (V-10) |
| 12 | Owner guidance | Accurate. Checked in the reports: A$172,039, A$2,707, A$144,630, 11.55% and 12.34%, 28.1% and 19.4%, 98.5% and 97.0%, A$150,000, A$12,900, A$11,000, A$43,000 and A$96,000 (recomputed), September 2032 (recomputed), 0.064%, A$9.50, "three times in four", "three periods in ten", 0.71 and 0.88, 2.5 to 4.4 points, "one time in four". Every date and weekday in sections 5, 17.1, 20.2 and 21 was recomputed and is right |

## 3. Findings

| ID | Severity | Disposition | Location | Problem | Fix in v2.13 |
| --- | --- | --- | --- | --- | --- |
| V-01 | Medium | Applied | RSK-34; RSK-01; §3 `RunContext` | The pending state is right but four edges are unsaid. (a) `RunContext` carries `killed` only, and RSK-01 names `KILLED` and `HALTED_INTEGRITY`, so where the pending state is enforced is left to the builder. (b) "A restart inside the window changes nothing" does not say what a restart after the window does. (c) "By Telegram's time stamps" leaves open whether a `/pause` stamped in time and read after `KILLED` was set undoes the kill. (d) Nothing says a command is acknowledged to Telegram only after its effect is stored, or that the flag is written before the cancels | `RunContext.killed` is true while a kill is pending; the flag is written first; at the end of the window, or at the first start after it, `KILLED` is set unless an answer stamped inside the window has been read; once set, only `trader resume --clear kill` clears it; acknowledge after commit; `/pause` keeps an earlier buys-halt reason |
| V-02 | Medium | Applied | §15 commands; "How to read"; BP-16 | The `PAPER` first line is required on "every plan, page, fills message, order sheet and digest". CL-T and the M5 test say every message. A reply to a command is none of the five: the reply to a first `/kill` names the sells of A200 and BGBL a kill would block. `/status`, `/plan`, the login prompt, the reports and email copies are in the same position. BP-16's `DRILL` first line could replace the `PAPER` line | Every message the system sends in `paper_auto` starts with the `PAPER` line, with the kinds listed; `DRILL` and the second runner's mark go in front and never replace it |
| V-03 | Medium | Applied | EXE-13; SYS-34; §4; §15 | In advisory mode the plan shows what the L1 shadow account did in the two funds the owner holds, under "ADVISORY — no order is placed". That says what the system does, not that the line is no recommendation, and the mode's name invites the other reading. It is a report of a virtual account and not an instruction, so it is not High. Separately, "no buy or sell line for the index account" is stated for advisory mode (EXE-13) and for "any plan" (SYS-34), not for a digest, page or report in `paper_auto` | A fixed sentence under the first line of any advisory message that shows the shadow line: not advice, not an instruction for the index account. The no-trade-line rule covers every message in every open mode |
| V-04 | Medium | Applied | §19 backups; `postgres` row | The nightly `pg_dump` list and the `postgres` row name `ledger_<user>_live`, `ledger_<user>_paper` and `market_<user>`. The paragraph above says the databases are those of section 12, but the list is what a backup script is copied from, and the external ledger holds the only tax records of the real holding | The list names every database of section 12 that exists, the external ledger first; the restore check reads it |
| V-05 | Medium | Applied | §12; §20.1 notes | The W-07 text lists what the external ledger holds and omits `runs`, `tranche_state`, `plans`, `flags`, `acceptances` and `incidents`, which in advisory mode have no other home. The table heading names two ledgers. From the paper stage two tranche-state stores exist and nothing says which the shadow line follows; a drill revision or a veto on the paper account would otherwise change the only out-of-sample record. A kill set in advisory mode is not in the new paper ledger | The three ledgers share a schema; the external ledger holds the run records in advisory mode; the shadow line keeps reading it; the paper `trader init` is refused while a kill or integrity halt is set there |
| V-06 | Medium | Applied | §11 manual fallback | A `MANUAL_PENDING` line is closed as `skipped` when "not matched within `manual_match_days`" (2 trading days). With Flex at 16:30 on the next day, the statement for a fill on the second day arrives after a clock-based close. The fill then matches no line and BP-20 books it as a manual trade, freezes the symbol and sets an integrity halt, which blocks exits | The window counts trade dates; the line is closed only after the statement for its last day is ingested |
| V-07 | Low | Applied | CA-01 table, `NOT_SENT` row | "Never on a day on which a kill, halt or freeze stopped it" against RSK-34 and BP-05, which send the sell the same day when `/pause` ends a pending kill. CA-01 says the sections win, but the row is what the ledger layer enforces | The row names the exception |
| V-08 | Low | Applied | PRT-19; LED-04 | Notional paper cash is outside NAV. LED-04 compares NAV with IBKR net liquidation within 0.1%, so it would page on every broker day. The buy ceiling A takes the lowest of the ledger figure and two IBKR figures, which on paper include the notional balance and so never bind | Added back for LED-04; taken out of the two IBKR figures in A |
| V-09 | Low | Applied | MON-13; PRT-19 | A contribution raises the paper cap "on the same date". A statement imported weeks later would back-date an external flow and revise unit prices and sizing that plans have already used | On paper it counts from the day it is recorded in the system |
| V-10 | Low | Applied | SYS-34 | With `external_account.enabled: false` the book is notional. The external ledger "is the only ledger whose records reach a tax report, the facts bundle or the estate pack", so notional parcels could be listed as the owner's holding | A notional book feeds none of them |
| V-11 | Low | Applied | §18; OPS-19; D25; RND-032; O31 | The `execution.mode` comment says `sheet` and `live_auto` "need the OPS-18 record", against SYS-33. OPS-19, D25 and RND-032 name v2.12 as the frozen text and allow "the status change that confirms the two High fixes". The owner's confirmation of the W-01 and W-14 readings had no line in section 21 | Reworded; O31 carries the confirmation at the first kill drill, which is report 44's own revisit trigger for kill semantics |
| V-12 | Low | Applied | §4; I22 | "In `paper_auto` no order can be sent without the owner's phone approval of the login" is stated as a designed property. Whether IBKR asks for an approval on a paper login is in no report. If it does not, a paper system left alone keeps trading paper; nothing real depends on it | Marked as a spike item |
| V-13 | Low | Applied | OPS-18 | Rows may not be older than 90 days "except conditions 1 and 2", and the row for condition 7 must be at least 90 days old. Both hold on one day only. The fault refuses real money, so it fails closed | Condition 7 joins the exception |
| V-14 | Low | Not changed | MON-13; OPS-14; CA-09; CA-12 | Five operating numbers have no config key: 80% of a contribution, the second email at 90 days, the 14-day reminder, the 7-day page, the 30-day incident WARN | Not changed. New keys would alter the section 18 schema for no gain in safety; the builder logs them under OPS-19 (c) |
| V-15 | Low | Applied | §20.1 notes | Group B needs the paper `trader init` (ledger, account id, bootstrap replay, canary), which EXE-12 describes and OPS-06, tagged L, defines | One clause in the W-06 note |

Totals: 15 findings: 0 Critical, 0 High, 6 Medium, 9 Low. 14 applied, 1 not changed, 0 rejected.

## 4. Why no finding is High

The rubric: High is a silent or ambiguous text such that a reasonable builder could send an unintended real or paper order, sell units not held, trade on bad data or lose a stop; or a message the owner could reasonably act on as an instruction to trade the real holding.

- **V-01.** RSK-34 says without condition that no order is sent or replaced while the kill is pending and that no answer in the window sets `KILLED`. A builder who drops the pending state at a restart, or sends an order during it, contradicts those sentences and fails BP-05's test. The edges are unsaid, not ambiguous in a direction that sends an order.
- **V-02.** The M5 test requires the first line on every message template, and a `/plan` reply is the plan. The gap is that the list was narrower than the test. A reply to the owner's own `/kill` that names what the paper system would be stopped from selling is not an instruction.
- **V-03.** A line marked `shadow` that reports what a virtual account did is not an instruction to trade. The risk is one of reading, in a falling market, and one sentence closes it.
- **V-06.** The result is an integrity halt that should not have been set. That blocks orders; it does not send one. The owner would by then have traded by hand from a paper order sheet.

## 5. What was checked and found correct

- **Report 49's corrections.** W-01 to W-20 as applied: each is in the text where CL-T says, reads consistently with its neighbours, and brings no new defect beyond the edges listed above. W-21 and W-22 are rightly left.
- **No real order.** No configuration of the group A or B build validates a real-money mode, connects to an account whose id does not start `DU`, or defines a live gateway. `trader canary` and `trader golive` are live-mode commands and cannot be reached.
- **Kill paths other than V-01.** `KILLED` and `HALTED_INTEGRITY` block every order; `/pause` and `HALTED_BUYS` let exits run; the flags are independent; a resume never releases an order on the day it is typed; the out-of-touch kill, the restore rule and the drill-copy rule are intact.
- **Sells of units not held.** RSK-03 reads the managed position at send time; PRT-28 caps a withdrawal sell.
- **Bad data.** No order leaves on a single-source close without a valid quote inside 2%, and none on `NO_QUOTE`; a spike bar stays quarantined until the mark.
- **Section 17.1** against report 44 section 4.1, **section 20.2** against report 44 sections 3.3 and 5, and the **Live-Core counts** (116, 78, 60, 55; 309 requirements).

## 6. What this read did not do

- It did not re-derive any figure of reports 36, 38 or 45 to 48 beyond finding it in the report or recomputing simple arithmetic.
- It did not test any claim about IBKR or Telegram. The paper account's balance, the paper login approval and the exec ID in paper Flex rows are for the spike.
- It did not read reports 31 to 48 in full.
- The fixes for V-01, V-05 and V-06 fill gaps where no report gives the rule. They are the editor's readings, on the side of fewer orders or of keeping a stop, and are marked as such in CL-U.
- The owner has still not confirmed the two readings of v2.12 that differ from reports 44 and 34 (silence after `/kill` ends in `KILLED`; a veto without a reason is applied). Both send fewer orders. O31 asks for the confirmation at the first kill drill.

## 7. Files

- `FD_v2.13.md`: v2.12 with the 14 fixes, change log CL-U first, status final and frozen.
- `FD_v2.13_ARCHIVE_not_for_build.md`: the archive with its header re-pointed; archived text unchanged.
- `FD_FINAL_LATEST.md` and `FD_FINAL_LATEST_ARCHIVE_not_for_build.md`: byte copies of the two files above. `FD_FINAL.md` is still the v2.10 copy and is not for build.
- `verify_v213.py` (scratchpad): `verify_v212.py` with CL-U, the status rule moved to the latest read, the copies check and a content check per finding. 0 fails.
