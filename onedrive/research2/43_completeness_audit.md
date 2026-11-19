# 43. Completeness audit of v2.10 against professional and regulatory standards

13 November 2026 · audits `FD_FINAL.md` (v2.10) · general information only, not legal, tax or financial advice

**Lens.** Reports 22–30 checked the spec against itself. Reports 33–35 checked it against the owner's goals, retail platforms and algorithm designs. This report checks it against what regulators and industry bodies require of firms that run automated trading, scaled down to one person with one retail account. None of these standards binds the owner (section 1.1). They are used as a checklist of things that go wrong.

**Source tags.** [2+] two or more independent sources agreed in this session. [1] one source. [unverified] taken from the auditor's prior knowledge of the document; the primary text could not be opened in this session. Section 8 lists what was and was not verified.

---

## 0. Answer in brief

- **No Critical gap.** The trade path, the stop, the breaker, idempotency, reconciliation, record keeping, data lineage, backup and the research process meet or exceed the adapted standards. Of 132 checklist items, 79 are covered, 36 partial, 11 missing and 6 not applicable.
- **Five High gaps**, all outside the logic that reports 22–30 walked:
  1. **CA-01** The order-intent, plan and broker-order status sets are never enumerated and have no transition table. The spec's most safety-critical state machine is defined only by scattered prose.
  2. **CA-02** Nothing independent of the server reports executions to the owner. Every detection control runs on the machine it is meant to check.
  3. **CA-03** Secrets at rest and container privilege are unspecified: no disk encryption, no rule on the Docker socket, no non-root rule. On the home mini PC, theft of the box exposes every credential and the TOTP seed together.
  4. **CA-04** One phone carries the IBKR login approval, the IBKR app kill, the Telegram kill and (by default) the authenticator. Its loss removes two of the three stop layers at once and no runbook covers it.
  5. **CA-05** Only the signal is independently re-implemented (RND-003). The breaker, the order lifecycle and the ledger are written and tested by the same builder agent, with no independent review.
- **Twelve Medium and eleven Low gaps** follow in section 5. The largest group is lifecycle management: back-out of a release, patching, an annual control review, an incident register, an expiry register and an offline rebuild kit.
- **Cross-cutting checks** (section 4): 2 of 13 state machines lack a transition table; 6 of 24 external dependencies have no stated failure mode or fallback; milestone coverage is complete (245 of 254 defined IDs, the other 9 deliberately unbuilt); acceptance tests are explicit for the 20 BP rows only; about 15 operating numbers carry only an `[A]` source.
- **One factual update for the spec:** ASIC made the trading-algorithm amendments on 15 September 2026, they commence on 18 March 2028, and ASIC is consulting (CS 63) on withdrawing RG 241, which section 22 still cites [2+].

Every proposed requirement (CA-01 to CA-28) has exact text, a milestone and an acceptance test in section 5.

---

## 1. Standards used and how they are adapted

### 1.1 Why none of them binds, and why they are still used

The owner trades their own account as a retail client of IBKR Australia. The ASIC Market Integrity Rules bind market participants (here IBKR), MiFID II RTS 6 binds EU investment firms, SEC Rule 15c3-5 binds US broker-dealers with market access, SR 26-2 addresses banks, and the FIA papers are industry guidance. The spec already says this for SR 26-2 (RND-035). What does bind the owner directly is the market-misconduct law (Corporations Act Part 7.10) and IBKR's client terms; items G-06 and G-07 cover them.

### 1.2 Sources

| Standard | What it contributes | Verification |
| --- | --- | --- |
| ASIC Market Integrity Rules (Securities Markets) 2017, Part 5.6 "Automated Order Processing — filters, conduct and infrastructure"; RG 241 Electronic trading (2 August 2022) | Filters, authorised persons, security, ability to suspend, review and certification before use and after a material change, annual review | Part title and review headings [2+]; rule-level text [unverified]. legislation.gov.au and asic.gov.au could not be opened |
| ASIC amendment instruments 2026/574 and 2026/575 (media release 26-226MR, 24 September 2026); CS 63 | Defined "Trading Algorithm"; testing before first use and before a material change; monitoring that identifies disruptive messages immediately; kill switch; technology-neutral manipulation rules covering agentic AI. Made 15 September 2026; commence 18 March 2028 after an 18-month transition. CS 63 proposes updating RG 265 and RG 266 and withdrawing RG 241 | Dates, scope and CS 63 [2+]; rule numbers 5.6.3A and 5.6.3B(2) [1]; whether a participant must impose anything on API clients [unverified] |
| MiFID II RTS 6, Commission Delegated Regulation (EU) 2017/589 | Governance, testing and controlled deployment (Arts 5–8), annual self-assessment (Art 9, Annex I), stress testing (Art 10), kill functionality (Art 12), surveillance (Art 13), business continuity (Art 14), pre-trade controls (Art 15), real-time monitoring (Art 16), post-trade controls and reconciliation (Art 17), security (Art 18), change records | Arts 9, 12, 13, 17 and the change-record rule [2+]; Art 15(6) override procedure [1]; the Art 15 control list and Arts 5–8, 10, 14, 18 [unverified]. **The "alert within five seconds" figure could not be confirmed in the adopted text** [unverified]; this report does not rely on it |
| SEC Rule 15c3-5 (release 34-63241, 2010) | Pre-set credit or capital thresholds; rejection of erroneous orders by price and size and of duplicative orders; access limited to authorised persons; immediate post-trade execution reports to surveillance; direct and exclusive control; regular review and annual CEO certification | Framework, review and certification, direct and exclusive control [2+]; the itemised control list [unverified] |
| FIA, Best Practices for Automated Trading Risk Controls and System Safeguards (18 July 2024); FIA Guide to the Development and Operation of Automated Trading Systems (2015); FIA PTG risk-control recommendations (2010) | Order size, intraday position, price tolerance, cancel-on-disconnect, kill switch, message and repeated-execution throttles, self-match prevention, market-data reasonability; drop copy reconciliation, post-trade credit controls, exchange error-trade policies; development, change management, testing, security | Publication, scope, and the three post-trade controls [2+]; price tolerance and cancel-on-disconnect sections [1]; the rest of the list [unverified]. fia.org could not be opened |
| CFTC Regulation AT (proposed 2015, supplemented 2016) | Message and execution throttles, price and size limits, order cancellation, connectivity monitoring, development and testing standards, source-code retention, annual compliance report | **Withdrawn 25 June 2020** and replaced by the principles-based Electronic Trading Risk Principles for exchanges [2+]. Element list [unverified]. Used as a checklist only |
| SR 26-2, Revised Guidance on Model Risk Management (Fed, OCC Bulletin 2026-13, FDIC; 17 April 2026) | Supersedes SR 11-7 and SR 21-8; rigour scaled to materiality; inventory, development, validation, effective challenge, ongoing monitoring, outcomes analysis, vendor models | Date and supersession [2+], which confirms RND-035. Whether generative and agentic AI are out of scope is contested across secondary sources [1] |
| NIST Cybersecurity Framework 2.0 (26 February 2024); ISO/IEC 27001:2022 Annex A | Six functions: Govern, Identify, Protect, Detect, Respond, Recover. 93 controls in four themes (37 organisational, 8 people, 14 physical, 34 technological) | [2+] |
| IOSCO final reports of 19 May 2025 on finfluencers, online imitative trading practices and digital engagement practices | Most regulators treat copy trading as likely investment advice or portfolio management; disclosure and suitability themes for retail investors | [2+] for publication and the copy-trading finding. An IOSCO 2025 AI report was not found [unverified] |
| Software engineering practice for financial systems | Idempotency, audit trail, time synchronisation, change management, incident response, DR/BCP, data lineage | Common practice; not tied to one document |

---

## 2. Master checklist

Status: **C** covered · **P** partial · **M** missing · **NA** does not apply (reason given). Severity applies to P and M only. "R34" means report 34 already proposes the fix and it is not re-counted here.

### A. Governance, roles and accountability

| # | Item (source) | Adapted to one person | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- | --- |
| A-01 | Named accountable person for the algorithm (RTS 6 Art 1; 15c3-5(e)) | The owner | §23 roles; RND-002; USR-11 | C | — |
| A-02 | Segregation of development, validation and approval (RTS 6 Art 1; SR 26-2 effective challenge) | Builder agent, validator agent, owner with cooling-off | RND-002, RND-003, RND-005 | C | — |
| A-03 | Independent challenge of **all** trade-path code, not only the model (RTS 6 Art 5; FIA development) | A second agent in a fresh context reviews breaker, lifecycle and ledger | RND-003 covers the signal only; tests are the builder's own | P | High, CA-05 |
| A-04 | Compliance function (RTS 6 Art 2) | NA: no regulated entity. The own-account conduct rules are item G-06 | — | NA | — |
| A-05 | Staff competence and training (RTS 6 Art 3; Reg AT) | Owner drills | BP-05 quarterly kill drill; BP-16 restore drill; MON-05 | C | — |
| A-06 | Outsourcing and third-party accountability (RTS 6 Art 4; SR 26-2 vendor models) | Dependency list with failure modes | Dependencies named; several have no failure mode (section 4.2) | P | Medium, CA-10, CA-12 |
| A-07 | Annual self-assessment and validation of the whole arrangement (RTS 6 Art 9; 15c3-5(e); ASIC annual review) | A yearly owner review of controls with a record | Yearly tasks in §17 are data and N only; MON-07 re-runs the battery | P | Medium, CA-08 |
| A-08 | Senior-officer certification (15c3-5(e)(2); ASIC certification) | Owner signs the yearly review | Per-release approval pins (OPS-10) only | P | Medium, CA-08 |
| A-09 | Risk appetite stated and accepted | Expectations statement | §30; RND-034; USR-07; RSK-30 | C | (R33, R34 add the objective and policy record) |
| A-10 | Decision register | Decision log and owner decisions | §2 D1–D20; CL-D OD1–OD5; CL-J OD6–OD9; §21.1 | C | Reports 31–35 await a disposition (section 4.4) |
| A-11 | Key-person and succession planning (BCP) | Estate pack, owner silence | None | M | R34 OPS-14 |
| A-12 | Decommissioning | Clean retirement | None | M | R34 OPS-15 |

### B. Pre-trade risk controls

| # | Item (source) | Adapted | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- | --- |
| B-01 | Maximum order value (RTS 6 Art 15; 15c3-5(c)(1); FIA) | Per-order cap | RSK-06 (buys); sells capped by quantity | C | — |
| B-02 | Maximum order quantity (same) | Units against volume | RSK-07; RSK-03 | C | — |
| B-03 | Price collar (RTS 6 Art 15; FIA price tolerance) | Limit within a band of a validated reference | RSK-08; DAT-13; §11 pricing | C | — |
| B-04 | Pre-set credit or capital threshold (15c3-5(c)(1)(i)) | Settled cash only | RSK-10; PRT-19; BP-19; D4 | C | — |
| B-05 | Maximum position or exposure (FIA intraday position) | Sleeve weight cap, no leverage | RSK-13; PRT-15 | C | — |
| B-06 | Message throttle (RTS 6 Art 15; Reg AT) | Orders per day | RSK-11; message 162 | C | — |
| B-07 | Repeated automated execution throttle (RTS 6 Art 15; FIA) | One replacement a day | §11 step 7; RSK-11; RSK-12 | C | — |
| B-08 | Duplicate-order prevention (15c3-5(c)(1)(ii)) | Idempotent intent key | BP-17; BP-18; EXE-03; BP-03 | C | — |
| B-09 | Market-data reasonability (FIA) | Two-source close; quote sanity | DAT-02, DAT-04; `max_quote_spread` | C | — |
| B-10 | Stale or delayed quote rejected (FIA market data) | Quote age and data type checked | `Quote.ts` exists; no age rule; delayed data "unless a test shows it works" | P | Medium, CA-13 |
| B-11 | Self-match prevention (FIA; ASIC wash-trade rules) | No opposite orders; one account per person | RSK-04; USR-11 | C | — |
| B-12 | Regulatory pre-trade checks (15c3-5(c)(2)(i)): no naked short | Sell at most the held units | RSK-03 | C | — |
| B-13 | Only permitted instruments and order types (15c3-5(c)(2)(ii)) | Allow-list; limit orders only | RSK-02; EXE-01, EXE-02, EXE-06 | C | — |
| B-14 | Trading-phase restriction | No auctions, no open | EXE-07; OPS-03; OPS-09 | C | — |
| B-15 | Controls cannot be bypassed by the strategy; direct and exclusive control (15c3-5(d)) | Independent breaker | BP-04; §10; SYS-18 | C | — |
| B-16 | Procedure for a blocked order the firm still wants to send (RTS 6 Art 15(6)) | No override path; a block is cleared only by named, logged commands | DAT-17; §10 resume; "no command can raise a limit" | C | — |
| B-17 | Broker- or venue-side limits as a second layer (FIA) | IBKR order precautions | §10 second layer; I6 [unverified] | P | Already open item I6; no new gap |
| B-18 | Cancel-on-disconnect (FIA) | Orders must not outlive the runner | DAY orders; 15:30 cancel; gateway held to 16:12; LED-06; GTD is I15 | P | Accepted residual: a DAY limit order can reach the closing auction if every cancel fails. Low; no new text |
| B-19 | Intraday loss limit (FIA; RTS 6 Art 17) | NA by owner design: long-only, unlevered, monthly, no intra-month action (PRT-20). Month-end drawdown stands in | RSK-22 | NA | Recorded deviation |
| B-20 | Order-to-trade ratio limits | NA: at most 6 orders a day | RSK-11 | NA | — |

### C. Kill functionality and halts

| # | Item (source) | Adapted | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- | --- |
| C-01 | Immediate cancel of all unexecuted orders (RTS 6 Art 12; ASIC 2026 kill switch) | One-step kill | §10 KILLED; BP-05 | C | — |
| C-02 | Kill works without the trading system | Broker app | §10 manual layer | C | — |
| C-03 | Kill survives restart and restore | Persistent flag | `flags`; BP-16; OPS-02 | C | — |
| C-04 | Kill tested regularly | Quarterly drill | BP-05 | C | — |
| C-05 | Re-arm needs authentication and a clean state | Second factor, named clear | §10; §15; BP-05 | C | — |
| C-06 | Kill reachable when the usual device is lost | Second enrolled device; recovery runbook | Not addressed; one phone holds three of the four routes | M | High, CA-04 |
| C-07 | Graduated halts with defined exits | Two halt classes, freezes | §10; §4 | C | — |

### D. Monitoring and post-trade controls

| # | Item (source) | Adapted | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- | --- |
| D-01 | Real-time monitoring while orders work (RTS 6 Art 16; ASIC 5.6.3A) | Pages during the order window | §15 PAGE; MON-01 broker-day check-ins | C | — |
| D-02 | Monitoring independent of the trading process | External dead-man | MON-01; BP-12 | C | — |
| D-03 | **Execution reports that do not pass through the trading system** (15c3-5(c)(2)(iv); FIA drop copy) | Broker's own trade and login notices straight to the owner | None. Flex and API reconciliation both run on the server | M | High, CA-02 |
| D-04 | Reconcile own logs to broker records (RTS 6 Art 17(3)) | Positions, cash, fills, orders | LED-01 to LED-06; BP-02 | C | — |
| D-05 | Continuous exposure monitoring (RTS 6 Art 17) | Daily NAV and drawdown | §4 08:05 job; RSK-22 | C | — |
| D-06 | Transaction-cost analysis | Cost against model | RSK-26; EXE-09; PRT-21 | C | — |
| D-07 | Surveillance for market abuse (RTS 6 Art 13) | NA as a function. Design invariants replace it | See G-06 | NA | — |
| D-08 | Alert classes, runbooks, page budget | — | §15; MON-06; BP-13 | C | — |
| D-09 | Every alert tested end to end | — | MON-05 | C | — |
| D-10 | The monitor itself is tested and uses a second channel | Quarterly dead-man self-test | MON-05 tests once at build | P | Low, CA-22 |
| D-11 | Host health and capacity (RTS 6 Art 1 capacity; NIST DE.CM) | Disk, memory, database and backup size in the digest | Fault injection covers "disk full" (BP-15); no running measure | P | Low, CA-19 |
| D-12 | Model performance monitoring and decay (SR 26-2) | — | MON-07; RSK-24; RSK-29; RSK-30 | C | — |
| D-13 | Silent loss of the control itself | Escalate when evaluations keep being skipped | OPS-13 pages once per skipped month | P | Medium, CA-17 |

### E. Testing and deployment

| # | Item (source) | Adapted | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- | --- |
| E-01 | Defined test methodology (RTS 6 Art 5) | — | §20 code quality rules; G1 | C | — |
| E-02 | Conformance testing with the broker (RTS 6 Art 6; FIA) | Paper-account tests | EXE-10; I2–I5, I8, I14–I17; G3 | C | — |
| E-03 | Separate test environment (RTS 6 Art 7) | Paper account, `paper_sim`, account guard | EXE-12; §12 separate ledgers | C | — |
| E-04 | Controlled deployment (RTS 6 Art 8) | Paper, shadow, canary, full | BP-14; `deploy_freeze_hours` | C | — |
| E-05 | Back-out plan for every change (FIA change management) | Tested rollback | None; migrations are forward-only (§12) | M | Medium, CA-07 |
| E-06 | Emergency change procedure | Defect in the decision path | BP-14 covers fixes outside the decision path only | P | Medium, CA-07 |
| E-07 | Stress testing (RTS 6 Art 10) | NA for message volume. Fault injection and regime stress replace it | BP-15; RND-026 | C | — |
| E-08 | Testing after a material change (ASIC 5.6.3B) | — | BP-14; RND-032; ENG-03 golden file | C | — |
| E-09 | Record of each change: when, who, who approved, what (RTS 6) | — | git; OPS-10; `config_versions`; `audit_log` | C | — |
| E-10 | Source code retained (Reg AT) | — | D11; §19 | C | — |
| E-11 | Verification method stated for every requirement | CI, paper test, signed manual check or gate report | Explicit for the 20 BP rows; "CI-tested IDs" is not enumerated | P | Medium, CA-14 |
| E-12 | Every normative statement is traceable | An ID for each binding rule | Schedule rows, §11 lifecycle and pricing steps, the IBKR message table, the Flex timing rule, "KILLED means", the second factor, backups and NAV carry no ID | P | Medium, CA-14 |
| E-13 | Lifecycle state machines specified before build | Transition tables | Tranche and flags are complete; order intent and run are not | P | High CA-01; Medium CA-06 |

### F. Model risk (SR 26-2)

| # | Item | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- |
| F-01 | Model inventory | Hypothesis registry (RND-010); cost, tax and data-quality models are specified but not listed as models | P | Low; folded into CA-08 |
| F-02 | Sound development with a stated rationale | RND-006; RND-004 | C | — |
| F-03 | Independent validation | RND-003; G2 | C | — |
| F-04 | Limitations and assumptions documented | §1 expectations; §21.7; RND-027 | C | — |
| F-05 | Ongoing monitoring and outcomes analysis | RSK-22, RSK-24; MON-07 | C | — |
| F-06 | Change control and versioning | RND-016; RND-032; `spec_hash` | C | — |
| F-07 | Use limits and retirement triggers | RSK-30; PRT-23 | C | — |
| F-08 | Rigour scaled to materiality | §1; VAL-25; §30 | C | — |
| F-09 | Validation of the tax model | TAX-12 uses one engine; no independent check | P | R34 TAX-16 |
| F-10 | Card lifecycle states defined | Result values are in prose (passed, failed, not passed, not testable, passed after audit); no status set | P | Low, CA-26 |

### G. Regulatory and conduct position

| # | Item | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- |
| G-01 | Licensing perimeter considered | §14; D10; §21.7 | C | — |
| G-02 | Future rule changes tracked | P8 (ASIC 2028); P4 (T+1) | P | Low, CA-24: P8 lacks the date and the RG 241 withdrawal; no standing watch list (CA-08) |
| G-03 | Tax law tracked | D19; §13; T1–T13 | C | — |
| G-04 | Data licences respected | DAT-15, DAT-16; USR-05 | C | — |
| G-05 | Record retention | TAX-11; MON-03; audit log permanent | C | — |
| G-06 | Market-misconduct law that binds the owner directly (Corporations Act Part 7.10; ASIC 2026 rules name agentic AI) | The design is clean (limit orders, tiny size, no self-trades, no cancels as signals) but no requirement states the invariants or tests them | P | Low, CA-23 |
| G-07 | Broker's client terms on automated trading | I11 covers market-data status only | P | Low, CA-24 (new open item) |
| G-08 | Copy-trading and advice risk when others use the software (IOSCO May 2025) | USR-04, USR-09; OD1 decided no lawyer gate; §21.7 records the open legal question | P | Low, CA-27 |
| G-09 | Retail suitability and disclosure (IOSCO) | §30 statement | C | (R34 USR-15 adds a policy record) |
| G-10 | Transaction reporting, best execution, client money | NA: obligations of the broker | NA | — |

### H. Security (NIST CSF 2.0, ISO/IEC 27001:2022)

| # | Item | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- |
| H-01 | Asset and account inventory (ID.AM; A.5.9) | Secrets list kept off the server (O20); no list of accounts, devices or renewals | P | Medium, CA-12 |
| H-02 | Network exposure minimised (PR.IR) | INF-02, INF-03; BP-09 | C | — |
| H-03 | Authentication for every privileged action (PR.AA) | §15 second factor; BP-11; SSH keys | C | — |
| H-04 | Second factor on every dependent account | Netlify, registrar and git only (§19); IBKR login | P | Medium, CA-16 (extends R34 §5.11) |
| H-05 | Least privilege at the broker | BP-08; ASX permission only | C | I7 open |
| H-06 | Least privilege on the host (A.8.2) | Database roles are separate. How the scheduler starts gateway containers is not said; a mounted Docker socket is root on the host. No non-root rule | M | High, CA-03 |
| H-07 | Secrets management (A.8.24) | OPS-11 Docker secrets; no secrets in logs | C | — |
| H-08 | Data at rest protected (PR.DS) | Backups and snapshots are encrypted. The server disk is not; Compose secrets are plain files | M | High, CA-03 |
| H-09 | Supply chain (GV.SC; A.5.19–5.22) | BP-10; images by digest | C | — |
| H-10 | Vulnerability and patch management (A.8.8) | `pip-audit` in CI. No rule for the host OS, Docker, Postgres or the gateway | P | Medium, CA-10 |
| H-11 | Key and secret rotation | Flex token expiry WARN only | P | Low, CA-28 |
| H-12 | Security logging and detection (DE.CM, DE.AE) | Spoofed Telegram ID alerts (BP-11). No alert on SSH login, blocked egress or a new tailnet device | P | Low, CA-20 |
| H-13 | Log integrity | `audit_log` INSERT-only; off-site backups | C | Low hardening in CA-28 |
| H-14 | Physical security (A.7) | Not addressed for the home option | P | Folded into CA-03 |
| H-15 | Security incident response (RS) | No runbook for a lost phone, leaked credential or compromised server | M | Medium, CA-09 |
| H-16 | Administrative access when the usual route fails | Tailscale is the only way in | P | Low, CA-21 |
| H-17 | AI kept out of the trade path | SYS-06; BP-09; RND-002 | C | — |
| H-18 | Dashboard isolation | INF-05 to INF-08; D13 | C | — |

### I. Resilience, DR and BCP

| # | Item | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- |
| I-01 | Backups: encrypted, off-site, tested (RTS 6 Art 14) | §19; BP-16 | C | — |
| I-02 | Stated recovery time and data-loss objectives | INF-01 (2 hours); BP-16 (24 hours) | C | — |
| I-03 | Rebuild does not depend on third-party registries still serving the pinned artefacts | Restore pulls the gateway image and wheels by digest from public registries | P | Medium, CA-11 |
| I-04 | State after a restore is safe | BP-16 starts halted; `recover --from-flex` | C | — |
| I-05 | Manual fallback for trading | D12 order sheet | C | — |
| I-06 | Daily records complete after an outage | Flex and vendor ranges catch up (S-06, S-13). `positions_eod`, `nav_eod` and `benchmark_nav` for the missed days are not addressed | P | Medium, CA-15 |
| I-07 | Component end-of-life | Pinned versions; I8 once | P | Medium, CA-10 |
| I-08 | Broker failure or account restriction | D12 (no second broker); custody note in R33, R34 | P | Accepted by D12; no new text |
| I-09 | Power and internet at home | Dead-man page; "server lost" runbook | C | — |
| I-10 | Expiry of tokens, keys, plans and payment methods | Flex token and calendar only | P | Medium, CA-12 |

### J. Incident management

| # | Item | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- |
| J-01 | Runbook per alert | BP-13; §17 | C | — |
| J-02 | Incident register | RSK-30(3) counts incidents, but no table or rule records them | M | Medium, CA-09 |
| J-03 | Post-incident review and a regression test per defect | None | M | Medium, CA-09 |
| J-04 | Erroneous-trade procedure (FIA error-trade policies) | None; BP-20 covers manual trades only | M | Medium, CA-09 |
| J-05 | External notification duties | NA: no regulator or client. Contacting IBKR is in CA-09 | NA | — |

### K. Software engineering for financial systems

| # | Item | v2.10 | Status | Gap |
| --- | --- | --- | --- | --- |
| K-01 | Idempotent jobs and orders | OPS-01; BP-17; EXE-03 | C | — |
| K-02 | Exactly-once booking of external events | `cash_ledger.external_id`; `fills.exec_id` | C | — |
| K-03 | Determinism and reproducibility | SYS-10, SYS-11, SYS-16 | C | — |
| K-04 | Audit trail of every decision and operator action | SYS-15; `audit_log`; EXE-04 | C | — |
| K-05 | Immutable, bitemporal data; lineage | DAT-18; DAT-09; §12 mutability rule | C | — |
| K-06 | Lineage of hand-entered data | §3 import rule; DAT-11, DAT-14 cross-checks | C | — |
| K-07 | Time: UTC storage, time-zone and DST handling | SYS-14; 01:30 backup note | C | — |
| K-08 | Clock synchronisation checked whenever time gates a decision (RTS 25 analogue) | Checked at 11:15 on broker days only | P | Low, CA-18 |
| K-09 | Money arithmetic | SYS-13 | C | — |
| K-10 | Configuration as controlled data | §18; OPS-10, OPS-12 | C | — |
| K-11 | Concurrency control | OPS-01 advisory lock | C | — |
| K-12 | Schema migration discipline | Alembic forward-only; no compatibility rule | P | In CA-07 |
| K-13 | Static analysis and coverage | §20 | C | — |
| K-14 | Each number has a recorded source | Row-level sources everywhere; about 15 numbers rest on `[A]` alone | P | Low, CA-25 |

### L. Summary

| Group | Items | C | P | M | NA |
| --- | --- | --- | --- | --- | --- |
| A Governance | 12 | 5 | 4 | 2 | 1 |
| B Pre-trade | 20 | 15 | 3 | 0 | 2 |
| C Kill | 7 | 6 | 0 | 1 | 0 |
| D Monitoring | 13 | 8 | 3 | 1 | 1 |
| E Testing and deployment | 13 | 8 | 4 | 1 | 0 |
| F Model risk | 10 | 7 | 3 | 0 | 0 |
| G Regulatory | 10 | 5 | 4 | 0 | 1 |
| H Security | 18 | 8 | 7 | 3 | 0 |
| I Resilience | 10 | 5 | 5 | 0 | 0 |
| J Incidents | 5 | 1 | 0 | 3 | 1 |
| K Engineering | 14 | 11 | 3 | 0 | 0 |
| **Total** | **132** | **79** | **36** | **11** | **6** |

Counted by script from the rows above. Of the 47 partial or missing items, 6 need no new text: 3 are fixed by report 34 (A-11, A-12, F-09), 1 is an existing open item (B-17, I6) and 2 are accepted residuals (B-18, I-08). The other 41 map to the 28 proposed requirements in section 5; several items share one requirement.

---

## 3. What v2.10 does better than the standards ask

So that the gap list is read in proportion:

- **The stop.** Five reviews hardened `/kill` against a down runner, a paper runner, a restore drill and Telegram's message retention. RTS 6 Art 12 asks only that orders can be cancelled at once.
- **Idempotency.** Intent persisted before send, deterministic `orderRef`, no resend on timeout, resolution by broker lookup, crash-injection tests (BP-17, BP-18, EXE-03).
- **Two halt classes** with the reasoning recorded. No standard distinguishes a halt that must not block an exit from one that must.
- **Pre-registration.** Frozen cards, a trial log that counts discarded runs, a locked holdout, a negative control (H2) and a haircut (H12) go beyond SR 26-2.
- **Lineage.** Bitemporal append-only tables, hashed raw files, and `spec_hash`, `card_set_hash`, config hash and git SHA on every run.
- **No override path.** No command can raise a limit or place a discretionary order, which is stricter than RTS 6 Art 15(6).

---

## 4. Cross-cutting completeness checks

### 4.1 State machines

| Machine | Where | States enumerated | All transitions defined | Finding |
| --- | --- | --- | --- | --- |
| Tranche ON / OFF | PRT-13, SYS-17, OPS-13 | Yes | Yes: 0, 1, ≥ 2 votes; bootstrap; skipped month; revision | Complete |
| Kill and halt flags | §10, `flags` | Yes | Yes: set, clear by name, re-arm, restore | Complete |
| Symbol freeze | §10, SYS-23, BP-20 | Yes | Yes | Complete |
| Validation verdict | DAT-01 to DAT-04, DAT-17 | Yes | Yes, including re-issue and override | Complete |
| `MANUAL_PENDING` line | §11 manual fallback | Yes | Yes: matched, superseded, skipped | Complete |
| `cashflow_expected` | PRT-28 | Yes | Yes: open, closed, lapsed | Complete |
| `distribution.status` | DAT-14, DAT-22 | Yes | Yes: expected, estimated, final | Complete |
| Canary and go-live flags | EXE-12, OPS-06 | Yes | Yes | Complete |
| Mode `L1` / `STATIC` | PRT-10, PRT-23, OPS-12 | Yes | Yes; the return to `L1` is gated by OPS-12 | Complete |
| **Run** | §4 | Mostly | **No.** No transition table. `HALTED_FOR_DAY` is a run state but is absent from the digest statuses (§4 20:00 row, §15, BP-12). No state for an unhandled failure. Whether the three halts are run states or only flags is ambiguous: §4 lists them as "terminal and blocking states" and §10 holds them in `flags` | Medium, CA-06 |
| **Order intent, plan, broker order** | §3, §11, §12 | **No.** `order_intents.status` is "including `MANUAL_PENDING`, `RECOVERED`, `superseded`, `skipped`"; `SENDING`, `SUBMITTED`, `NEEDS_REVIEW`, `NOT_SENT`, `PLANNED`, `APPROVED` appear in prose; filled, partly filled, cancelled, rejected, vetoed, held and lapsed have no named status | **No** | High, CA-01 |
| Hypothesis card | RND-010, RND-015 | Results in prose | Mostly | Low, CA-26 |
| Stage 1 → 2 → 3 | §27, MKT-01 | Yes | Upward only; nothing says what happens if an account falls back below a stage threshold | Low, CA-26 |

### 4.2 External dependencies

| Dependency | Failure mode stated | Fallback stated | Finding |
| --- | --- | --- | --- |
| IB Gateway login and phone approval | Yes (`TWOFA_MISSED`) | Order sheet; carry | Complete |
| IBKR API during the order window | Yes (1100–1102, step 5) | Barrier; Flex next day | Complete |
| IBKR as broker (outage, restriction) | Partly | Order sheet needs IBKR; no second broker (D12) | Accepted |
| IBKR snapshot quote | Yes (`NO_QUOTE`, 10167) | Collar pricing | Complete; quote age missing (CA-13) |
| IBKR Activity Flex | Yes (`PENDING_FLEX`) | API reconciliation; token expiry WARN | Complete |
| IBKR order precautions | Unverified (I6) | — | Open item |
| EODHD | Yes (retry, BLOCK, budget) | `SINGLE_SOURCE` with the Flex mark; `qc override`; paid plan | Complete for an outage. A vendor that stops serving ASX for months leaves the overlay switched off with one page a month (CA-17) |
| RBA series | Carry-forward rule only | — | Not used by live L1; no gap at Stage 1 |
| Issuer announcements (manual) | Yes (`DIST_MISSING`) | Blocks the sleeve | Complete |
| ASX calendar (manual) | Yes (60-day WARN; `CALENDAR_MISMATCH`) | Library cross-check | Complete |
| Telegram | Yes | Email; out-of-touch kill | Complete (P10 open) |
| Email (SMTP provider) | Implied only (OPS-04) | No buy if the plan is not delivered | Low: both channels failing is safe but unstated; CA-22 says so |
| Dead-man monitor | **No** | — | Low, CA-22 |
| NTP | Yes at 11:15 (`CLOCK_SKEW`) | `HALTED_FOR_DAY` | Partial, CA-18 |
| Tailscale | **No** | — | Low, CA-21 |
| Backup store | Yes (PAGE) | Local data until fixed | Complete |
| Object store, Netlify, DNS | Yes (INF-08) | None needed | Complete |
| Image and package registries | **No** at restore time | — | Medium, CA-11 |
| `ib_async`, IBC, gateway image (volunteer-maintained); IBKR's minimum gateway version | **No** | — | Medium, CA-10 |
| Host OS, Docker, Postgres | **No** | — | Medium, CA-10 |
| The owner's phone | **No** | — | High, CA-04 |
| Home power and internet | Yes (dead-man) | Rebuild runbook | Complete |
| Server provider billing; domain; paid plans | **No** | — | Medium, CA-12 |
| The owner | No | — | R34 OPS-14 |

Six dependencies have neither a stated failure mode nor a fallback: the dead-man monitor, Tailscale, the registries at restore, the open-source broker stack, the host software and the phone. Two more (provider billing, the owner) are partly covered elsewhere.

### 4.3 Every number has a source

The spec's convention is a source on every requirement row, with tags for design values. A sample of about 120 numbers in sections 4, 6, 9–12, 15, 17 and 18 found the convention followed. The exceptions are operating numbers whose only source is `[A]` (carried from v2.0) and which carry no design-value tag: the 85% coverage floor (§20), the 2-hour recovery and 24-hour data-loss objectives (INF-01, BP-16), time to kill under 2 minutes (BP-05), page within 5 minutes (BP-20), clock within 2 s, dead-man grace of 30 minutes (MON-01), log retention of 90 days (MON-03), 30 daily and 24 monthly backups (§19), A$0.01 and 0.1% reconciliation tolerances (LED-02, LED-04), `flex_pending_days` 2 and the A$50 pending-fee cap (§12), the 3-minute login re-prompt (§4), `flex_token_warn_days` 30, and 10 significant digits (SYS-10). None is wrong; each is an untagged design choice. CA-25 tags them in one line. This audit did not re-open reports 11–21 to re-check that each cited report contains its number; reviews 22–30 did that.

### 4.4 Every owner decision is recorded

- Recorded: D1–D20 (§2), OD1–OD5 (CL-D), OD6–OD9 (CL-J), reviewer rulings (CL-G), and 22 pending owner items with the gate each blocks (§21.1).
- Not yet recorded, because they post-date v2.10: the proposals of reports 31–35 and of this report. The document's own practice (CL-E, CL-G, CL-I, CL-K) is a disposition table for every finding before the next issue. That table is the outstanding item; nothing inside v2.10 is undecided without being listed.
- Owner decisions the proposals below need: whether to encrypt the home server's disk and how it is unlocked after a power cut (CA-03); which second device is enrolled (CA-04); the month of the annual review (CA-08).

### 4.5 Every requirement has an acceptance test and a milestone

- **Milestone.** A script matched the first-column IDs of every requirement table in sections 1–30 against the "Requirements accepted" column of §20. 254 IDs are defined; 245 are assigned to a milestone or gate; the other 9 (SIZ-02 to SIZ-09, SIZ-13) are reference design that §26 says is built only when a card uses it. No milestone names an undefined ID. **Complete.**
- **Acceptance test.** Only the BP table has an acceptance-test column (20 rows). For the rest, §20 says each ID appears in a test name or docstring and "CI fails if any CI-tested ID has no test", but no list says which IDs are CI-tested. Many cannot be: SYS-30 (monthly manual entry), TAX-11 (retention), BP-08 (quarterly evidence), PRT-26 (no re-tuning), MON-06 (page budget), USR-04 (what the owner never does). **Partial; CA-14.**
- **Untraced rules.** Binding text without an ID cannot appear in the coverage table: the 15 schedule rows, lifecycle steps 1–7, pricing steps 1–4, the 13 IBKR message rows, the Flex timing rule, "KILLED means", the second-factor paragraph, the mutability rule, NAV and unit price, the backup list and the dashboard steps. **Partial; CA-14.**

---

## 5. Ranked gap list with exact spec text

New IDs are `CA-01` to `CA-28`. They clash with nothing in v2.10 or in reports 31–35. Each entry gives severity, the checklist items it closes, the text, the milestone and the acceptance test. Thresholds are [design value — operational] unless stated.

### High

**CA-01 — Order, plan and broker-order status sets and transitions.** Closes E-13. *Why High:* the spec is "written so a build agent can implement it without guessing", and the builder must currently infer the status set of the object that sends money. Five reviews found lifecycle defects by reading prose; a table makes the next one mechanical.

> **CA-01 Order-intent lifecycle (section 11, after "Lifecycle and idempotency").** `order_intents.status` takes exactly these values; the status names may be refined, the set and the transitions are binding. One row is one attempt (`{attempt}` in `client_order_id`); a replacement or a carry is a new row that names its predecessor.
>
> | Status | Entered when | Leaves to | Terminal |
> | --- | --- | --- | --- |
> | `PLANNED` | `RiskManager.apply()` approves the intent at plan time (08:10) | `APPROVED`, `VETOED`, `NOT_SENT` | No |
> | `VETOED` | A `/veto` stamped by `veto_deadline` names it (OPS-04, OPS-02) | — | Yes; not carried (PRT-27) |
> | `APPROVED` | `approve_plan` at 11:15 | `HELD`, `SENDING`, `NOT_SENT`, `REJECTED_RISK` | No |
> | `HELD` | Pricing step 3 or 4, DAT-22 or DAT-02 holds it (`SNAPSHOT_GAP`, `NO_QUOTE`, `DIST_MISSING`, `SINGLE_SOURCE`) | `SENDING` at 13:00, else `NOT_SENT` | No |
> | `REJECTED_RISK` | A send-time RSK check rejects it | — | Yes; latches if RSK-03, 06, 11 or 12 |
> | `NOT_SENT` | Any cause in PRT-27 before `placeOrder`; a kill, halt or freeze set after planning (section 10) | — | Yes for this row; a successor row is planned under PRT-27 unless vetoed, killed or lapsed |
> | `SENDING` | Committed before `placeOrder` (step 1) | `SUBMITTED`, `NEEDS_REVIEW`, `NOT_SENT` (only when step 5 proves no broker order exists) | No |
> | `SUBMITTED` | Broker order id and `permId` stored (step 4) | `PARTIAL`, `FILLED`, `CANCELLED`, `CANCELLED_EXTERNAL`, `REJECTED_BROKER`, `NEEDS_REVIEW` | No |
> | `PARTIAL` | Executions sum to less than `qty` | `FILLED`, `CANCELLED`, `CANCELLED_EXTERNAL`, `NEEDS_REVIEW` | No |
> | `FILLED` | Executions sum to `qty` (BP-01) | — | Yes |
> | `CANCELLED` | This system's cancel is confirmed (step 7; 15:30) | — | Yes; the remainder is a successor row |
> | `CANCELLED_EXTERNAL` | Message 202 or a cancel found with none of this system's on record (step 7) | — | Yes; no replacement that day |
> | `REJECTED_BROKER` | Message 201, 109, 110, 163 or 200 | — | Yes; carries once (PRT-27), then freezes |
> | `NEEDS_REVIEW` | Unknown status, `Inactive`, or unresolved at a restart | Any broker-confirmed status; `HALTED_INTEGRITY` if unresolved at 15:45 (an intent waiting for Flex under step 5 stays `SENDING` or `SUBMITTED`) | No |
> | `LAPSED` | A carried buy passes `buy_carry_days`, or falls below its PRT-17 minimum | — | Yes |
> | `MANUAL_PENDING` | An order-sheet line is issued | `MATCHED`, `superseded`, `skipped` | No |
> | `MATCHED` | A Flex trade is booked against the line | — | Yes |
> | `RECOVERED` | Rebuilt by `trader recover --from-flex` (BP-16) | — | Yes |
>
> Any transition not in this table is refused by the ledger layer, sets the row `NEEDS_REVIEW` and pages. `plans.status` takes `PLANNED`, `APPROVED`, `SUPERSEDED` (a re-run under OPS-13 replaced it) and `CLOSED`. `broker_orders.status` stores IBKR's own status string unchanged and is advisory (BP-01). [design — the auditor's reading of sections 4, 10 and 11; the editor checks each row against them before issue]

Milestone M2 (table and ledger constraint), M4 (broker transitions). Acceptance test: a property-based test drives random event sequences and asserts that no transition outside the table is ever stored; a fixture for each row.

**CA-02 — Execution reports that do not pass through the server.** Closes D-03. *Why High:* every control that would reveal a wrong or hostile order (reconciliation, digest, dashboard) runs on the machine that sent it. The broker can tell the owner directly at no cost. This is the retail equivalent of a drop copy (FIA) and of 15c3-5's immediate post-trade reports.

> **CA-02 Broker-side notices.** Before G4 the user turns on, in the IBKR account itself and addressed to the user and not to the server: (a) a notice of every trade; (b) the daily activity statement by email; (c) notice of each login and of each change to account settings, where IBKR offers it. Which notices IBKR Australia offers for an individual account is [unverified] (new open item for IBKR). The server never reads or sends these messages. The runbook says: a trade notice on a day with no plan message, or for a symbol, side or size that the plan did not show, means `/kill`, then the IBKR app, then the "erroneous or unknown trade" runbook (CA-09). A dated "Before G4" record (`trader golive --record broker-notices`) is required by `trader golive --confirm` (OPS-06), and the quarterly kill drill confirms a notice arrived for the last real trade.

Milestone: "Before G4". Acceptance test: the canary fills produce a broker notice on the user's phone that the server did not send; the record names the date.

**CA-03 — Secrets at rest and privilege on the host.** Closes H-06, H-08, H-14. *Why High for the home option, Medium for a cloud server:* Docker Compose secrets are ordinary files on the host. A stolen mini PC yields the IBKR bot password, the Flex token, the Telegram token and the TOTP seed. A trader container that can reach the Docker socket is root on the host.

> **CA-03 Host protection.** (a) The volume that holds secrets, the databases and the raw store is encrypted at rest (LUKS or the provider's equivalent). On a machine in the user's home the whole disk is encrypted. How it is unlocked after a power cut (by hand, or by a key held off the machine) is the user's choice and is written in the runbook; while it is locked the dead-man monitor pages (MON-01). (b) No container of this system mounts the Docker socket. The scheduler starts and stops the gateway containers through a proxy or a host service that accepts only "start" and "stop" for the two named gateway containers. (c) Every container runs as a non-root user with a read-only root file system, apart from its named volumes. (d) The TOTP seed is readable only by the process that checks codes. The second factor protects against a stolen Telegram session and against haste; it does not protect against someone who already controls the server, and nothing in this document says it does.

Milestone M6 (hardening); (a) is a "Before G4" record. Acceptance test: `docker inspect` shows no socket mount and a non-root user in every container; a start request for any other container through the proxy is refused; the restore drill (BP-16) is run onto an encrypted volume.

**CA-04 — Loss of the phone.** Closes C-06 and the phone row of section 4.2. *Why High:* it concerns the user's stop, the criterion reviews 27–29 used. `/kill` and the IBKR app are on the phone; the third route, `trader kill`, needs a second device on the tailnet, which nothing requires.

> **CA-04 Second control device and phone-loss runbook.** Before G4 the user has: (a) a second device, not the phone, enrolled on the Tailscale network and able to run `trader kill`; (b) the authenticator for the section 15 second factor on a device other than the one that runs Telegram, or its recovery seed reachable without the phone (O20); (c) IBKR's own recovery route for a lost second-factor device read and written into the runbook [unverified — the user reads IBKR's current procedure]; (d) Telegram two-step verification on, so that a stolen SIM does not give the chat (report 34 §5.11). The runbook entry "phone lost or stolen" says, in order: `trader kill` from the second device; end the phone's Telegram sessions from another device; ask IBKR to disable the lost device; re-enrol; then `trader resume --clear kill`. Until IBKR login approval works again no order can be sent; that is the designed safe state, and blocked sells are paged with the order sheet by email (section 10). The quarterly kill drill (BP-05) is run once a year from the second device with the phone switched off.

Milestone: "Before G4" record; M6 for the runbook. Acceptance test: kill set from the second device with the phone off in under 2 minutes.

**CA-05 — Independent review of the trade path.** Closes A-03. *Why High:* SYS-04 ("no order ever breaks a risk limit") rests on tests written by the agent that wrote the code. RND-003 gives the signal an independent re-implementation but not the breaker that guards it.

> **CA-05 Trade-path review (section 23; exit criterion of G1 and of every later change to these files).** For `risk.py`, `orders.py`, `execution.py`, `reconcile.py`, `ledger.py` and `broker/ibkr.py`: (a) a reviewer agent in a fresh context, with the spec and the code but not the builder's tests or notes, writes a review memo that lists each requirement ID the file implements and any behaviour it finds that the spec does not state; (b) the reviewer writes its own tests for RSK-01 to RSK-13 and BP-01 to BP-03 from the spec text alone, and both test sets pass; (c) mutation testing on `risk.py` and on the quantity and status logic of `execution.py`: at least 90% of mutants are killed, and every survivor is listed in the memo with a reason. The owner reads the memo before approving the release (OPS-10). The reviewer has the builder's limits (RND-002).

Milestone M2 (`risk.py`, `orders.py`), M4 (execution, broker), M5 (ledger, reconcile). Acceptance test: the memo and the mutation report are stored with the release; CI fails below the mutation score.

### Medium

**CA-06 — Run-state transitions.** Closes the run row of section 4.1.

> **CA-06 Run states (section 4).** `runs.state` takes `SCHEDULED`, `DATA_READY`, `PLANNED`, `APPROVED`, `SUBMITTED`, `FILLED`, `PARTIAL`, `NONE`, `RECONCILED`, `SKIPPED`, `HALTED_FOR_DAY` and `FAILED`. `HALTED_INTEGRITY`, `HALTED_BUYS` and `KILLED` are flags (section 10), not run states: a run under them still moves through the states above, and `runs.reason_code` records the flag. `FAILED` is entered when a job raises an error it does not handle; it pages, sends no further order that day, runs `cancel_unfilled` and `reconcile_broker`, and clears the next trading day unless a flag was set. A transition table (state, event, next state) is part of this requirement and is delivered with M5; an event with no row is `FAILED`. The digest status is the strictest of `KILLED`, `HALTED_INTEGRITY`, `HALTED_BUYS`, `HALTED_FOR_DAY`, `FAILED`, `SKIPPED`, `OK`; `HALTED_FOR_DAY` and `FAILED` are added to the lists in the 20:00 row, section 15 and BP-12. `RECONCILED` is reached at 15:45 on a broker day; a day still `PENDING_FLEX` is `RECONCILED` with that reason and is re-checked when Flex arrives.

Milestone M5. Acceptance test: property test over the table; a fixture where a job raises mid-cycle ends `FAILED` with zero open orders.

**CA-07 — Back-out of a release and defects in the decision path.** Closes E-05, E-06, K-12.

> **CA-07 Back-out (added to BP-14).** (a) Every release keeps the previous image digest and config on the machine. `deploy --rollback` returns to them in under 15 minutes and is exercised in paper before the release is approved. (b) A schema migration is compatible with the previous release's code (add first, remove one release later), or the deploy takes a verified backup first and the back-out is a restore under BP-16. (c) A defect found in `decide()`, `build_orders()` or `RiskManager` after go-live: the user sets `/kill` or `trader mode static --confirm`; the fix is a release that passes the golden file, CA-05, and a replay over all history in which every decision is identical except those the defect report names; the cooling-off (RND-005) applies; the champion / challenger period and the one-promotion-a-year limit do not, because the rule on the card has not changed. A fix that changes what the card says is a new card (RND-016).

Milestone M6. Acceptance test: the deploy script refuses a release with no recorded rollback rehearsal; a rollback fixture restores the earlier digest and the runner starts.

**CA-08 — Annual control review.** Closes A-07, A-08, F-01, G-02.

> **CA-08 Annual review.** Once a year, in a month the user sets, `trader review --year` generates a report and the user records an acceptance (`acceptances`). The report lists: every limit in section 18 with its value, its headroom over the year and whether it bound; every open item of section 21 still open and every [unverified] tag; the incident register and its actions (CA-09); every override, resume and `qc override`; the expiry register (CA-12); component currency (CA-10); the dates of the last four kill and restore drills; the model list (the frozen cards, the cost model, the tax model, the data-quality thresholds and the drawdown envelope) with the date each was last checked; and a watch list the user fills in: changes in the year to ASX trading rules, IBKR's API and client terms, the tax law, vendor terms and ASIC's rules. A WARN is raised when the last acceptance is older than 13 months. The review changes nothing by itself; any change follows section 28.

Milestone M6 for the generator; G5 ongoing. Acceptance test: the report builds from a fixture ledger and names every section 18 limit.

**CA-09 — Incident register, review, and the missing runbooks.** Closes J-02, J-03, J-04, H-15.

> **CA-09 Incidents.** (a) An `incidents` table (insert-only): id, opened, closed, class, description, cause, orders or money affected, actions, linked test. A row is opened automatically by every `HALTED_INTEGRITY`, `FAILED` run, latched breaker trip, `NEEDS_REVIEW` unresolved at 15:45, missed order and dead-man page, and by hand with `trader incident open`. RSK-30(3) counts rows whose cause is a defect in this system. (b) Each row is closed only with a written cause and, where the cause is a defect, the name of a regression test that fails without the fix. A row open for more than 30 days is a WARN. (c) Runbook entries are added for: an erroneous or unknown trade (kill; do not trade to correct it; contact IBKR the same day, because cancellation of a trade is at the broker's and the exchange's discretion and is time-limited; record the tax effect); a lost phone (CA-04); a leaked or suspected-leaked credential (kill; revoke and replace every secret on the O20 list in a fixed order, the IBKR password first); a server believed compromised (kill from the second device; power off; rebuild under BP-16 with new secrets; never restore the old machine's volumes); and a stolen Telegram session.

Milestone M5 (table and automatic rows), M6 (runbooks). Acceptance test: each trigger opens exactly one row in fault injection; the alert-catalogue lint (BP-13) finds the new runbooks.

**CA-10 — Patching and component currency.** Closes H-10, I-07, A-06.

> **CA-10 Patching.** (a) The host applies security updates to the operating system and the container engine automatically, outside the BP-14 freeze windows; a pending restart is done on a non-broker day. (b) PostgreSQL minor versions, the gateway image, IBC and `ib_async` are checked each quarter; an update follows BP-14 as a change outside the decision path. (c) Each quarter the paper gateway is started once on the newest stable gateway image and a login, a `what_if` and an order lookup by `orderRef` are run, so that an IBKR-forced upgrade is not first met on a broker day. IBKR's minimum supported gateway version and its notice period are [unverified] (new open item for IBKR). (d) If the pinned gateway is refused at login the day is `HALTED_FOR_DAY`, the order sheet is sent, and the upgrade is an emergency change under (b). (e) The digest shows a WARN when any pinned component has had no update for `ops.max_months_without_update` (12; report 34 OPS-15 uses the same key).

Milestone M6. Acceptance test: the quarterly check writes a dated record; a refused-login fixture ends with the order sheet.

**CA-11 — Offline rebuild kit.** Closes I-03.

> **CA-11 Rebuild kit (added to INF-01 and the backup list).** Each release adds to the off-site backup the exact container images it runs (`docker save`, checked against their digests) and the wheel files named in the lock file. The restore drill (BP-16) builds the machine from the kit with the image and package registries blocked. Vendor data and secrets are not in the kit.

Milestone M6. Acceptance test: the drill passes with ghcr.io, Docker Hub and PyPI unreachable.

**CA-12 — Expiry and renewal register.** Closes H-01, I-10.

> **CA-12 Register of accounts and expiries.** `config/<user>.yaml` holds a list, with no secret in it, of every account, device, subscription and credential the instance depends on and the date each expires or renews: the Flex token, the IBKR bot password if IBKR ages it, Tailscale node keys, the server and its payment method, the domain, the EODHD plan, the monitor plan, the object and backup stores, the calendar table and the TOTP enrolment. The digest carries a WARN `ops.expiry_warn_days` (30) before each date and a PAGE 7 days before any whose lapse would stop the runner or lock the user out. The register is reviewed in CA-08.

Milestone M5. Acceptance test: a fixture date inside the window raises the WARN; inside 7 days, the PAGE.

**CA-13 — Quote freshness and data type.** Closes B-10.

> **CA-13 Quote age (added to pricing step 2 of section 11).** A quote is valid only if, in addition, its market-data type is live (IBKR type 1) or a type that the I2 test has shown to be current for ASX snapshots, and its timestamp is no more than `execution.max_quote_age_s` (30) seconds before the order is priced. A frozen or delayed quote, or one with no timestamp, is `NO_QUOTE`. The data type and age are stored with the intent.

Milestone M4. Acceptance test: recorded sessions with a delayed-type and an old-timestamp quote both take the `NO_QUOTE` path.

**CA-14 — Verification method and IDs for unnumbered rules.** Closes E-11, E-12.

> **CA-14 Traceability (section 20).** (a) The repository holds `requirements.csv` with one row per requirement ID: milestone, verification method (`ci`, `integration-paper`, `drill`, `manual-record` or `gate-report`), and the test name or the record that proves it. CI fails if an ID in this document has no row, or a `ci` row has no test. A `manual-record` or `drill` row names the `acceptances` record that the gate reads. (b) Binding text with no ID gets one in the next issue, by rule and without changing the text: `SCH-<job>` for each schedule row, `EXE-L1` to `EXE-L7` for the lifecycle steps, `EXE-P1` to `EXE-P4` for pricing, `IBM-<code>` for each message row, and one ID each for the Flex timing rule, "KILLED means", the second factor, the mutability rule, NAV and unit price, the backup list and the dashboard steps.

Milestone M0. Acceptance test: the CI check itself.

**CA-15 — Daily records after an outage.** Closes I-06.

> **CA-15 Catch-up of daily records (added to OPS-02).** When the runner starts and one or more trading days have no `nav_eod` row, `mark_and_reconcile` runs once for each missed day in date order, after the vendor and Flex ranges are in, using that day's validated close. It writes `positions_eod`, `nav_eod` and `benchmark_nav` for each day, so that month-end unit prices (RSK-22), benchmark flows (PRT-22) and units entitled (section 12) are computed on the right dates. Monitors that page are evaluated on the latest day only. A missed day opens an incident row (CA-09).

Milestone M5. Acceptance test: a three-day outage across a month-end and an ex-date gives the same `nav_eod` rows as an uninterrupted run.

**CA-16 — Second factor on every dependent account.** Closes H-04. Extends report 34 §5.11, which covers IBKR, the IBKR email, Telegram and the mobile carrier.

> **CA-16 Account baseline.** A "Before G4" record confirms that each of these accounts has its own second factor and a unique password held in the password manager: the server provider, Tailscale, the git host, the backup and object stores, the dead-man monitor, EODHD, the password manager itself, and the accounts in report 34 §5.11. Tailscale device approval is on, so that a new device cannot join without the user.

Milestone: "Before G4". Acceptance test: checklist record stored (as BP-08).

**CA-17 — The overlay silently off.** Closes D-13.

> **CA-17 Skipped evaluations (added to OPS-13).** The digest shows, per sleeve, the date of the last evaluation that used a validated close. When a sleeve's evaluation is skipped in two consecutive months the user is paged each week until one succeeds, the page says that the trend filter is not operating for that sleeve and names `trader qc override` (DAT-17) as the way to supply a close, and an incident row is opened (CA-09). No halt is set, because a halt would not restore the exit.

Milestone M5. Acceptance test: a two-month vendor outage fixture produces the weekly page and the digest line.

### Low

**CA-18 Clock at every job.** Closes K-08. > Every job checks the server clock against NTP before it runs and applies `ops.clock_skew_max_s`. On a breach a job that reads a close (OPS-08), issues a verdict, plans, or sends an order does not run and pages (`CLOCK_SKEW`); other jobs run and log it. A time-sync daemon runs on the host. Milestone M0, M5. Test: BP-15 clock-skew injection at 08:00 blocks `validate_data`.

**CA-19 Host health in the digest.** Closes D-11. > The digest carries a WARN when free disk is below 20%, when the last backup is more than 20% larger or smaller than the one before, or when memory in use at `gateway_start` exceeds 85%; the monthly report shows database and raw-store size and their growth. Milestone M5.

**CA-20 Security alerts.** Closes H-12. > A PAGE is sent, by the host and not by the trader process, for an SSH login to the server, a device joining the tailnet, and a container whose running image digest differs from the approved one; blocked outbound connections (BP-09) are counted in the digest. Milestone M6.

**CA-21 Access without Tailscale.** Closes H-16. > The runbook names one break-glass route to a shell that does not use Tailscale (the provider's console, or a keyboard on the home machine) and the restore drill uses it once a year. No inbound port is opened for it (INF-02). Milestone M6.

**CA-22 Dead-man self-test.** Closes D-10. > The dead-man monitor notifies by a channel that is neither the user's Telegram bot nor the SMTP provider the trader uses. Each quarter, with the kill drill, one heartbeat is withheld on purpose and the page is confirmed. If Telegram and email both fail, no buy is sent (OPS-04) and sells proceed; the runbook says so. Milestone M5.

**CA-23 Conduct invariants.** Closes G-06. > The system places an order only to trade it. It never places an order it intends to cancel, never has a buy and a sell working in one symbol (RSK-04), never trades in an auction (EXE-07) and never sends more than `max_orders_per_day`. A test asserts that every cancel in a recorded session follows the 13:00 or 15:30 rule, a kill, or an integrity halt. This restates existing behaviour as the own-account answer to the market-misconduct provisions; it is not legal advice. Milestone M4.

**CA-24 Regulatory references.** Closes G-02, G-07. > P8 is updated: the amendments were made on 15 September 2026 and commence on 18 March 2028; ASIC is consulting (CS 63) on updating RG 265 and RG 266 and withdrawing RG 241, so the RG 241 link in section 22 is marked "to be withdrawn". New IBKR open item: does IBKR Australia's client agreement or API terms place any condition on a retail client's automated orders, now or from March 2028? Blocks: nothing before March 2028.

**CA-25 Numbers sourced only from v2.0.** Closes K-14. > "How to read this spec" adds: a number whose only source is `[A]` is a [design value — operational].

**CA-26 Card states and stage fall-back.** Closes F-10 and two rows of section 4.1. > `hypotheses.status` takes `draft`, `frozen`, `run`, `decided`; `result` takes `passed`, `passed after audit`, `not passed`, `failed`, `not testable`. An account that falls below a stage's entry threshold keeps its stage until the yearly review, as PRT-14 does for N. Milestone M3, M9.

**CA-27 Re-confirm OD1 before M8.** Closes G-08. > M8 starts only after the owner re-reads section 21.7 and records that OD1 stands. The record notes that IOSCO's May 2025 report found most regulators treat copy trading as likely advice or portfolio management, and that USR-09 (no shared signals) is the rule that keeps the structure away from it. This re-opens nothing in v2.10.

**CA-28 Rotation and tamper evidence.** Closes H-11, H-13. > The Telegram bot token, the EODHD key and the object-store token are replaced yearly at the CA-08 review and after any CA-09 security incident. Each `audit_log` row stores the hash of the previous row; the nightly backup records the latest hash. Milestone M6.

### Counts

| Severity | Count | IDs |
| --- | --- | --- |
| Critical | 0 | — |
| High | 5 | CA-01 to CA-05 |
| Medium | 12 | CA-06 to CA-17 |
| Low | 11 | CA-18 to CA-28 |
| **Total** | **28** | |

Already proposed elsewhere and not re-counted: succession and owner silence (R34 OPS-14), retirement (R34 OPS-15), IBKR account hardening (R34 §5.11), tax-engine cross-check (R34 TAX-16), policy record (R34 USR-15).

---

## 6. Items that do not apply, with reasons

| Standard item | Why it does not apply |
| --- | --- |
| Compliance function, surveillance team (RTS 6 Arts 2, 13) | No regulated entity and no client orders. CA-23 states the conduct invariants instead |
| Direct electronic access provider duties (RTS 6 Arts 19–23; 15c3-5 for sponsored access) | The owner is the client, not the provider. IBKR carries these duties |
| Message-volume stress tests (RTS 6 Art 10) | At most 6 orders a day. Fault injection (BP-15) and regime stress (RND-026) are the scaled form |
| Intraday loss and exposure limits (FIA; RTS 6 Art 17) | Long-only, unlevered, cash account, no intra-month action by owner design (PRT-20). Month-end drawdown (RSK-22) is the stand-in. A recorded deviation, not an oversight |
| Order-to-trade ratios, exchange conformance certification | No exchange membership |
| CEO certification (15c3-5(e)(2)) | Replaced by the owner's approval pins (OPS-10) and the yearly acceptance (CA-08) |
| Regulatory notification of incidents | No regulator or client to notify. CA-09 names the broker contact |
| Business clocks to RTS 25 accuracy | No reporting duty. CA-18 keeps the 2-second rule and applies it wherever time gates a decision |

---

## 7. Reasons this could be wrong

- **Primary texts were not opened.** WebFetch failed for every host tried: asic.gov.au, legislation.gov.au, eur-lex.europa.eu, legislation.gov.uk, fia.org, federalreserve.gov, ecfr.gov and ashurstperkinscoie.com. Verification is from search results and the auditor's prior knowledge. Article-level citations tagged [unverified] should be checked before they are quoted in the spec. The proposed requirement texts do not depend on any article number.
- **The "five seconds" alert figure** commonly attributed to RTS 6 Art 16 could not be confirmed and is not used.
- **CA-01's table is a reading of prose**, written by an auditor and not walked scenario by scenario as report 25 did. It may contain a transition that contradicts section 11. The gap (no table) is certain; the proposed fill needs the same review the body had.
- **CA-02 and CA-04 assume IBKR features** (trade and login notices; a device-loss procedure) that were not confirmed for IBKR Australia.
- **Severity is judged on the reviews' own scale** (could it cause a wrong or missed order, or weaken the stop?). At A$5,000, long-only, with limit orders, the money at risk from any of these is small. CA-03 and CA-05 are rated High for what they protect as the account grows; an owner may reasonably rank them Medium today.
- Reports 36–42 did not exist when this was written, so overlap with them was not checked.

---

## 8. Verification log

| Claim | Tag | Basis |
| --- | --- | --- |
| SR 26-2 issued 17 April 2026 with the OCC (Bulletin 2026-13) and FDIC; supersedes SR 11-7 and SR 21-8 | [2+] | Federal Reserve letter page (via search); Sia Partners; Moody's |
| SR 26-2 leaves generative and agentic AI out of scope | [1], contested | Several vendor summaries say so; one says the opposite |
| ASIC amendment instruments made 15 September 2026, announced 24 September 2026 (26-226MR); commence 18 March 2028 | [2+] | ASIC CS 63 page and media release (via search); Allens; Finance Magnates |
| New "Trading Algorithm" definition; testing, governance and kill-switch duties; technology-neutral; manipulation rules cover agentic AI | [2+] | Same, plus Certrak and Policai summaries |
| Rule numbers 5.6.3A (monitoring) and 5.6.3B(2) (testing); seven-year record keeping | [1] | One secondary summary |
| CS 63 proposes withdrawing RG 241 and updating RG 265 and RG 266 | [2+] | ASIC CS 63 page title; ASIC Market Integrity Update 179; Allens |
| Part 5.6 is "Automated Order Processing — filters, conduct and infrastructure", with certification and annual review | [2+] | legislation.gov.au result titles; NSX Practice Note 19 |
| RTS 6 Art 12 kill functionality wording; Art 9 annual self-assessment against Annex I; Art 13 surveillance; Art 17 post-trade controls and reconciliation; record of material software changes | [2+] | legislation.gov.uk text (via search); ESMA Q&A; AFM self-assessment template |
| RTS 6 Art 15(6) procedure for blocked orders | [1] | legislation.gov.uk text (via search) |
| RTS 6 Art 15 control list; Arts 5–8, 10, 14, 18 content | [unverified] | Prior knowledge |
| RTS 6 Art 16 alerts "within five seconds" | [unverified] | Found only in an FIA proposed-amendment annex |
| SEC Rule 15c3-5: financial and regulatory risk controls; direct and exclusive control; regular review; annual CEO certification | [2+] | SEC release 34-63241 (via search); FINRA; WilmerHale |
| 15c3-5 itemised controls (erroneous and duplicative orders, authorised persons, immediate post-trade reports) | [unverified] | Prior knowledge |
| FIA paper published 18 July 2024; covers pre-trade controls, exchange volatility controls, post-trade analysis, conformance testing; post-trade controls are drop copy reconciliation, post-trade credit controls and error-trade policies | [2+] | FIA release; Global Trading; PostTrade 360 |
| FIA sections "Price Tolerance" and "Cancel-On-Disconnect" | [1] | PDF contents fragment in search |
| CFTC withdrew Regulation AT on 25 June 2020 and adopted Electronic Trading Risk Principles | [2+] | Davis Polk; Mayer Brown; CFTC release 8188-20 |
| NIST CSF 2.0 published 26 February 2024 with six functions; ISO/IEC 27001:2022 Annex A has 93 controls in four themes | [2+] | Multiple secondary sources |
| IOSCO final reports of 19 May 2025; most regulators class copy trading as likely advice or portfolio management | [2+] | A&O Shearman; Mondo Visione; IOSCO news release 768 (via search) |
| 254 requirement IDs defined; 245 mapped to a milestone | computed | Script over `FD_FINAL.md` lines 594–2147 |

## 9. Sources

- ASIC: [26-226MR](https://asic.gov.au/about-asic/news-centre/find-a-media-release/2026-releases/26-226mr-asic-strengthens-ai-trading-safeguards-and-streamlines-market-integrity-rules) · [CS 63](https://www.asic.gov.au/regulatory-resources/find-a-document/consultations/cs-63-proposed-updates-to-rg-265-and-rg-266-and-withdrawal-of-rg-241) · [CP 386](https://asic.gov.au/regulatory-resources/find-a-document/consultations/cp-386-proposed-amendments-to-the-asic-market-integrity-rules-trading-systems-and-automated-trading/) · [RG 241](https://download.asic.gov.au/media/qkgfookw/rg241-published-2-august-2022.pdf) · [Market Integrity Rules (Securities Markets) 2017](https://www.legislation.gov.au/F2017L01474/2024-10-15/2024-10-15/text/original/epub/OEBPS/document_1/document_1.html) · [Allens regulatory update, October 2026](https://www.allens.com.au/insights-news/insights/2026/10/financial-services-regulatory-update/) · [Finance Magnates](https://www.financemagnates.com/forex/asic-defines-the-algorithm-but-gives-the-market-until-2028-to-catch-up/) · [Policai](https://policai.org/analysis/asic-market-integrity-rules-ai-trading-2026)
- RTS 6: [EUR-Lex](https://eur-lex.europa.eu/eli/reg_del/2017/589/oj/eng) · [legislation.gov.uk](https://www.legislation.gov.uk/eur/2017/589/contents)
- SEC: [release 34-63241](https://www.sec.gov/rules/final/2010/34-63241.pdf) · [FINRA market access](https://www.finra.org/rules-guidance/key-topics/market-access)
- FIA: [2024 best practices](https://www.fia.org/sites/default/files/2024-07/FIA_WP_AUTOMATED%20TRADING%20RISK%20CONTROLS_FINAL_0.pdf) · [release](https://www.fia.org/fia/articles/fia-releases-best-practices-automated-trading-risk-controls-and-system-safeguards) · [2015 guide](https://www.fia.org/sites/default/files/2019-09/FIA-Guide-to-the-Development-and-Operation-of-Automated-Trading-Systems.pdf)
- CFTC: [Davis Polk on the withdrawal of Reg AT](https://www.davispolk.com/index%2Ephp/insights/client-update/cftc-withdraws-reg-proposal-proposes-principles-based-electronic-trading) · [Electronic Trading Risk Principles](https://regulations.justia.com/regulations/fedreg/2021/01/11/2020-27622.html)
- Model risk: [SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm) · [Sia Partners comparison](https://www.sia-partners.com/en/insights/publications/sr-11-7-vs-sr-26-2-model-risk-management-modernization) · [Moody's](https://www.moodys.com/web/en/us/insights/banking/from-sr117-to-sr262-managing-model-risk-when-models-dont-stand-still.html)
- Security: [NIST CSF 2.0 guide](https://www.saltycloud.com/blog/nist-csf-2-0-complete-guide-2026/) · [ISO 27001 to NIST mapping](https://www.konfirmity.com/blog/iso-27001-controls-mapped-to-nist-csf)
- IOSCO: [news release 768](https://www.iosco.org/news/pdf/IOSCONEWS768.pdf) · [A&O Shearman summary](https://finreg.aoshearman.com/iosco-publishes-final-reports-on-finfluencers-onl)
