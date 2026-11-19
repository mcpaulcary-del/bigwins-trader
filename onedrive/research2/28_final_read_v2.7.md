# Report 28 — Third full final read of FD v2.7

13 November 2026 · reviewer: independent reader, also the v2.8 editor · subject: `FD_v2.7.md` (2,079 lines) · result: `FD_v2.8.md`

## 1. Headline

**This read found 1 High finding. It is a flaw in the report 27 fix for Q-01 (a `/kill` sent while the runner is down). It is fixed in v2.8. Because a full read has again found a High finding, v2.8 is not declared final: its status row reads "Final candidate" and asks for one more independent full read.**

6 findings in all: **0 Critical, 1 High, 1 Medium, 4 Low.** All 6 were edited in v2.8.

| ID | Severity | One line |
| --- | --- | --- |
| P-01 | High | Telegram keeps an unread bot message for a limited time (24 hours). A `/kill` sent to a runner that stays down longer than that is lost, and the runner sends the next day's orders. v2.7 says the opposite: "Telegram holds those messages" and "a `/kill` is applied whatever its age" |

Of the 13 report 27 fixes, 12 are correct as written and introduced no new defect. Q-01 is correct for an outage shorter than Telegram's retention and wrong for a longer one (P-01). Three other fixes left a small edge that this report picks up (P-04 for Q-06, P-05 for Q-08, P-06 for Q-01).

## 2. What was done

One reader read `FD_v2.7.md` from the title to the end of section 30: document control, "How to read", every change-log part (CL-M, CL-L, CL-J, CL-K, CL-H, CL-I, CL-A to CL-G) and sections 1 to 30, including the section 18 YAML, the key index, section 21 and section 22. No section was skipped or sampled. The long rows (OPS-02, OPS-06, PRT-16, PRT-19, EXE-12, TAX-05, the section 24 proxy paragraph, BP-16, BP-20) were read in full.

Report 27 was read in full. Reports 11 to 26 were searched only, for one question: whether any report says how long Telegram keeps an unread bot message, or how the bot is read. None does. No earlier spec version was opened. The archive file was not re-read; only its header was re-pointed.

**Method.** First, each report 27 fix was read where it sits and checked against the paragraphs around it. Then each path that can send, carry, retry, replace, cancel or block an order was walked by hand again: the 11:30 send, the 13:00 retry and its routes (held order, confirming snapshot, `NOT_SENT`), the late routes of OPS-02, the restart resolution of section 11 step 5, the carry rule, the order sheet, the canary, the drill and the withdrawal sell. Each halt, kill, freeze, veto, restore, restart and resume was checked for what sets it, what clears it, and what the same day and the next morning do with it. The Telegram command path was checked for order and loss: runner down, runner up but unable to reach the bot, two runners, a restore. The prose was checked against the section 18 YAML and the section 3 interfaces.

**Rules followed.** Smallest edit that removes the problem. No redesign. No owner decision (OD1 to OD9) and no editor's reading already recorded was reopened. No requirement ID, reason code, config key, command, table or column was added or withdrawn. One open item was added (P10), because the fix for P-01 rests on a fact that no report holds.

**One limit of this read.** The 24-hour figure comes from Telegram's Bot API documentation (the section on getting updates: updates are stored until the bot receives them, but not longer than 24 hours). The reviewer knows this text but could not fetch the page in this session, because the host `core.telegram.org` is outside the session's network allow-list. The figure is therefore tagged [unverified] in OPS-02 and carried as open item P10. The finding does not depend on the exact figure: whatever the period is, it is finite, and v2.7 treats it as unlimited.

## 3. Findings

| ID | Severity | Location (v2.7) | Problem | Fix applied in v2.8 |
| --- | --- | --- | --- | --- |
| P-01 | High | OPS-02 "Commands sent while the runner was down"; section 15 commands; BP-05 | The Q-01 fix says "Telegram holds those messages, and the runner never discards pending messages. A `/kill` is applied whatever its age". Telegram does not hold them without limit: an update the bot has not fetched is kept for 24 hours and then dropped. So the fix closes the gap for a short outage and leaves it open for a long one, while the text and section 15 promise the user that it is closed. Example: a power cut stops a home mini PC on Friday at 21:00. The dead-man monitor pages. On Saturday the user sends `/kill`. Power returns on Monday at 06:00 and the machine restarts by itself. Telegram dropped the `/kill` on Sunday. If Friday was the evaluation date, the runner plans at 08:10 and sends an ON→OFF sell of a whole sleeve at 11:30; a sell needs no plan confirmation (OPS-04). The user believes the system is stopped. The same loss happens when the runner is up but cannot reach the bot for more than a day. The kill drill (BP-05) stops the runner for minutes, so it cannot find this. Rated High, like Q-01: it can send an order the user had stopped. Not Critical: it needs an outage of more than a day, the user gets no kill page (which section 15 names as the confirmation), and the 08:10 plan message arrives about three hours before the order | OPS-02: the text now says Telegram keeps the messages for a limited time (24 hours, [unverified], open item P10). New rule "Out of touch for longer than Telegram keeps a message": the runner that reads the bot keeps the time of its last successful read across restarts. If its next read comes after a gap longer than Telegram's retention, it sets the kill flag itself, with that reason, before any job that plans, sends or replaces an order, and pages the user. The user clears it with `trader resume --clear kill` and the second factor, as for any kill. Section 15 adds that a `/kill` which brings no kill page is not in force. BP-05's acceptance test adds a start after such a gap. Open item P10 asks the builder to read the current figure. No config key: the figure is a fact about Telegram, not a design value |
| P-02 | Medium | OPS-02; section 4, 11:15 row | Q-01 says what happens when the pending commands cannot be read "at a start". Nothing covers a runner that is up but cannot reach the bot at the veto deadline (a Telegram outage, or a DNS or network fault on the server while the user's phone still works). The plan can be confirmed as delivered by email, so OPS-04 lets the buys go, although a `/veto` or `/kill` the user sent cannot arrive | OPS-02: the same split as at a start applies while the runner is up. If the bot cannot be read at the 11:15 `pre_trade_check`, no buy is sent until it has been read again (the buys are `NOT_SENT` and carry under PRT-27), sells proceed as OPS-04 allows, and the user is paged by email. The 11:15 row of section 4 lists the check. This extends the editor's reading that report 27 recorded for Q-01; it does not change it |
| P-03 | Low | Section 10, halt list ("On `trader resume` …") | A kill or an integrity halt that is set after the 08:10 plan and cleared the same day before 15:00 has no rule for that day's approved intents. Read literally, the send-time check (RSK-01) passes again, and the 11:30 or 13:00 job sends them minutes after the resume. The resume prints only "the orders the next plan would contain", and EXE-12 says no command places an order on the day it is typed. The user has just resumed on purpose, so the harm is small, but a builder must guess | Section 10: an intent of today's plan that a kill, an integrity halt or a freeze stopped is not sent later the same day when the flag is cleared; the next plan holds it. Editor's reading, on the side of fewer orders, and the one EXE-12 already implies |
| P-04 | Low | Section 11 step 7 (Q-06) | The "not replaced that day" rule is keyed to message 202. If the user cancels an order in the IBKR app while the runner is down or disconnected, the runner never sees message 202; after the restart it finds the order cancelled. Step 5 already builds no fresh intent in that case (a broker order exists), but the 13:00 job "always replaces" a sell remainder | Step 7: an order the runner finds cancelled after a restart or a reconnect, with no cancel of its own on record, is treated like one cancelled by message 202 |
| P-05 | Low | TAX-05 (Q-08) | The 30 June 2027 snapshot is re-run only "if the runner was down that morning". If the disk is lost later on 1 July 2027 and the ledger is restored from the 01:30 backup, the `valuations_2027` rows are gone although the runner was not down, and the job has no rule to run again | TAX-05: the job also runs at the next `mark_and_reconcile` when a restore has brought back a ledger without these rows |
| P-06 | Low | OPS-02 (Q-01) | Pending commands are read "before any job that plans, sends or replaces an order". The fresh intent that section 11 step 5 may build while it resolves a restart is not a scheduled job, so a literal reading lets it go before the commands are read | OPS-02: "and before the restart resolution of section 11 step 5 builds a fresh intent" |

## 4. What the owner should know

- **P-01 changes what happens after a long outage.** If the system has been out of touch with Telegram for more than a day, it comes back stopped (`KILLED`) and pages. The owner resumes it with `trader resume --clear kill` and the second factor. This is the editor's reading: no report gives the rule. The lighter alternative, a page that asks the owner to send `/kill` again, was not taken, because it fails open in exactly the case the rule is for. An outage of more than a day is already an incident (the dead-man monitor has paged), so the extra step is rare.
- **P-01 rests on one fact that this session could not re-check** (section 2). Open item P10 carries it to the build (M5).
- **P-02:** if the bot cannot be reached at 11:15, buys wait and sells go. This is the split report 27 already chose for a start.
- **P-03:** a resume never releases an order on the day it is typed.

None of these needs a decision before the build.

## 5. The report 27 fixes (Q-01 to Q-13)

Each was checked against the v2.7 text.

- **Q-01** (commands sent while the runner is down): correct for an outage shorter than Telegram's retention. Wrong beyond it, and the text states the opposite as fact (P-01). The step 5 restart resolution is not named (P-06). The "cannot be read at a start" clause has no twin for a runner that is up (P-02).
- **Q-02** (two runners, one bot): correct. Only the live runner reads the bot; the paper runner is stopped with `trader kill` under its own config and marks its messages `PAPER`. OPS-01, section 15 and the section 19 container row agree. During G3, with no live runner, the paper runner reads the bot, so the kill drill still works.
- **Q-03** (`approve_plan` and `pre_trade_check` after a late start): correct.
- **Q-04** (managed position in PRT-19): correct; PRT-19, section 11 step 2, BP-03, RSK-03 and `Book.positions` now agree.
- **Q-05** (a cleared cost or tracking halt does not return on the same reading): correct, adds no number, and is carried in O18.
- **Q-06** (an order cancelled in the IBKR app is not replaced that day): correct. One edge: the cancel made while the runner is down (P-04).
- **Q-07** (a manual sale takes managed parcels first): correct; BP-20, TAX-01 and the external-flow rule of section 12 agree.
- **Q-08** (snapshot parcels, a missed job, a late value): correct. One edge: rows lost by a restore (P-05).
- **Q-09** (a parcel imported after 30 June 2027): correct.
- **Q-10** (restore on a day already traded): correct.
- **Q-11** (`--clear all` lifts freezes): correct.
- **Q-12** (no withdrawal sell before `golive`): correct.
- **Q-13** (LED-02 follows the I4 convention): correct.

## 6. Things checked and found consistent

- **Duplicate orders.** A missed login with an order sheet and a carried intent; a login approved after 11:15 with the 13:00 `NOT_SENT` route; a partial fill with a 13:00 replacement; a crash between commit and send, and between send and acknowledgement; a restore followed by a re-used `orderRef`; a restore drill beside production. In each, the send-time quantity (target minus managed position minus open orders), the foreign-order rule and the BP-02 barrier prevent a second order.
- **Halts, kill, freezes.** What sets and clears each of `killed`, `halt_integrity`, `halt_buys` and a symbol freeze; the latching breaker codes; the re-arm rules after a resume; the planning day after a resume, an accept or a lifted freeze; the halt after every restore. No path was found that clears a stop without the second factor, and none that sends an order while a stop is set. The only same-day gap is P-03.
- **Telegram commands.** The allow-listed chat, the veto deadline by Telegram's stamp, a late plan, two runners, a restore. The gaps are P-01, P-02 and P-06.
- **Paper and live.** Separate ledgers, the `DU` account check, the account id stored in each ledger, the mode in `orderRef`, `drill` refused in live mode, `canary` and `golive` refused in paper mode, the bot read by the live runner only.
- **Managed and unmanaged units.** RSK-03, RSK-06, `Book.positions`, PRT-19, section 11 step 2, BP-03, BP-20, TAX-01 and the unit price agree.
- **Settled cash.** `Book.settled_cash`, the three-figure minimum in PRT-19, the buy ceiling A, the canary followed by deployment, a sell on T with a buy on T, a pending surplus, an announced deposit and an announced withdrawal: no path sizes a buy from unsettled or unexplained cash.
- **Data fail-closed.** A missing bar, a missing Flex mark, a spike, a restatement, a missing distribution amount and an exhausted call budget each block the buy and let the rule's own sell through on a valid quote, or block the symbol.
- **EODHD budget.** At most 6 calls a run (3 end-of-day, 3 dividend) and at most 18 with both retries, all inside one GMT day; the Sunday 03:00 re-download falls in a GMT day (Saturday) with no other scheduled fetch. The count is stored and survives a restart. The limit of 20 is not exceeded [computed].
- **Tax ledger.** Parcel matching for system, manual and unmanaged sales; the two slices and the 30 June 2027 snapshot (which runs whatever the halt or kill state); the 12-month and 45-day tests; units entitled by trade date; the income year of a distribution; the capital-loss order. The one gap found is P-05.
- **Prose against the section 18 YAML, the key index and the section 3 interfaces.** No difference found. The verify script checks the YAML and the key index mechanically.

## 7. Verification

`verify_v28.py` (adapted from `verify_v27.py`) checks, in addition to everything the v2.7 script checked: the CL-N table (P-01 to P-06 present once each); that every `[R28 P-xx]` citation resolves and every applied finding is cited in Part A or B; that the text each fix promises is present and the replaced phrases are gone; that the CL-N totals and the version row match the severities in this report; that the status row does not say "Final" or "ready to build" while CL-N holds a Critical or High finding; that open item P10 exists; the v2.8 title, version row and status row; that Parts A and B no longer call themselves v2.7; and the re-issued archive file. The run result is in the hand-over note.
