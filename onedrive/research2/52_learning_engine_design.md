# 52. Learning engine design: a knowledge store that never forgets and a research loop that cannot fool itself

Date: 2026-11-14. Spec read: `FD_FINAL_LATEST.md` (v2.13, frozen). Reports read: 19, 20, 35, 43, 44, 48. Report 51 (company-level study) and the "Big Wins" engine are in progress and were not available; section 7 says how this design serves them.
Status: design report with spec-ready text (section 8). Nothing here is built. General information only; not financial, tax or legal advice.

**Evidence tags.** [2+] two or more independent sources agreed. [1] one source (a primary page opened in this session, or one earlier report). [unverified] my prior knowledge or my own estimate; the source was not opened in this session. [computed] arithmetic on figures stated in this report or in the spec. A tag such as [R48] or [LRN-09] names a report or a v2.13 requirement that I read in this session.

---

## 0. Answer in brief

**The owner asked for** an engine that keeps learning, records what it learns, never stops taking in information, keeps all of it available, and uses it to get better.

**What this design gives him:**

1. **A knowledge store that keeps everything and deletes nothing.** Every price with where and when it came from, every decision, plan, fill, reconciliation and incident, every research run (including the failed ones) with the exact code and data it used, every hypothesis card and what happened to it, every paper or notice read with a summary in plain words, and every owner decision. It lives in three places: the Postgres database on the server (records and data), an object store (original files and backups) and a private git repository (everything written in words: notes, cards, reports, the memory page).
2. **A research loop that runs by itself on a calendar.** The server extends every registered model on new data each week with no AI involved. A Claude Code scheduled agent reads new evidence weekly, runs a research cycle monthly, a deeper one quarterly, and prepares the yearly review. Each cycle ends in a short report, "What the engine learned", and in pull requests that the owner approves or rejects.
3. **Three hard limits that make the learning honest.**
   - The agent can read, research, write and propose. It cannot merge, approve, deploy, or place an order, and nothing it writes reaches the trading server except inside a release the owner has signed.
   - "Better" is measured only on data dated after an idea was registered, after costs and tax, against the index holding (static 40/60). Backtests can admit an idea to the test; they cannot pass it.
   - Every look at real data is counted, the count never goes down, and the bar an idea must clear rises as the count grows.

**What the owner should expect it to find.** On the programme's own evidence, the engine will get better quickly at the things that have many observations: what trading costs, how reliable the data is, how accurate its own forecasts are, what broke and why. It will get better slowly, or not at all, at beating the index. A rule with a real edge of 1 point a year and 5% tracking error needs about 100 years of record to reach t = 2, and about 225 years to reach the spec's t = 3 [computed; the first figure is also in the spec's expectations table]. Picking the best recent performer lost to holding 40/60 at every cut-off tested [R48]. So the engine is built to *notice* a real improvement if one ever appears, and to refuse a false one. That matches the spec's own definition: "better" means cheaper, safer and clearer [spec, opening statement].

**Four things the owner must decide** (section 1.2), because the spec is frozen:

| # | Decision | My recommendation |
| --- | --- | --- |
| O32 | Admit the learning engine as spec v2.14, as a named exception to the freeze (OPS-19 (a)) | Yes, after the advisory release has run 20 trading days. The knowledge repository and the agent's reading can start now, because they are research, not system code |
| O33 | Raise the running-cost budget (OPS-20 (c), now A$150 a year) | Yes: target A$330, ceiling A$480 a year, of which agent runs are capped at A$30 a month. The rented server (about A$129 a year) and the one EODHD month (about A$31) already reach the present A$150 ceiling, so the budget needs a decision even with no agent. The cheapest version of the engine adds about A$11 a month |
| O34 | Keep "no new strategy card before November 2027" (OPS-19 (e)) | Keep it. Until then the engine drafts and parks ideas, and learns costs, data and calibration |
| O35 | Whether the agent may see licensed price data | Yes. EODHD's help page permits sending data to Claude through the owner's own account for private analysis [1]. The design still exports only what a study needs |

**Cost.** About A$12 a month for the server and storage the owner already plans, plus up to A$30 a month (expected about A$26) for agent runs at published API prices (less if the owner's Claude subscription covers scheduled sessions [unverified]). Section 8.7.

### 0.1 Access record

| Source | Result |
| --- | --- |
| `eodhd.com/help/personal-use`, `/help/storage`, `/help/ai-tools`, `/pricing` | Opened and read on 14 Nov 2026 [1 each, primary]. Quotes in section 3.4 |
| Claude model prices | From the Claude API reference bundled with this session (table cached 3 Nov 2026) [1] |
| `docs.github.com`, `binarylane.com.au`, `backblaze.com` | Blocked by the session proxy. Facts about GitHub plan features, BinaryLane disk sizes and object-store prices are [unverified] |
| Academic references in section 4.5 | Not opened in this session; cited from reports 16, 20 and 35 where those reports carry them, otherwise [unverified] |
| How Claude Code scheduled sessions are billed under a subscription | Not verified. Costs are computed at API prices as an upper bound |

---

## 1. Where this meets the frozen spec

### 1.1 What already exists, and what was parked

| Already in v2.13 | Where |
| --- | --- |
| Raw files kept unchanged with hashes; insert-only market tables; bitemporal storage as a later item | DAT-09, DAT-18 (group L), section 12 |
| Hypothesis cards, a trial log that counts every run, test families, a trial cap of 50 per family | RND-010 to RND-016, VAL-20, VAL-22 |
| A bounded learning layer: six kinds of estimate that may update by themselves, drift monitors, a quarterly report | LRN-08 to LRN-34 (section 28.1) |
| "No job, report or promotion step may select or weight a rule on its recent return" | LRN-09, from [R48] |
| Agents may research and code; they may never approve, promote, merge to the live branch or touch an order | RND-002, SYS-06 |
| No AI API host on the server's outbound allow-list | BP-09 |

| Parked until at least 12 November 2027 | Where |
| --- | --- |
| The challenger library, the research cycle (evidence scan, triage, freeze windows), machine-learning rules, and cards H30 to H43 | PK-10 (report 35's LRN-01 to LRN-07, LRN-21 to LRN-25, LRN-27, LRN-29 to LRN-32) |
| Any new strategy card | OPS-19 (e) |

So the spec has the *rules* for honest learning and a small automatic layer. It does not have: a single store that holds everything, a record of external evidence, a memory of what was tried and why, a way to ask questions, a running scorecard for every model, or a scheduled agent. Those are what this report adds.

### 1.2 How the design fits without breaking the freeze

The design is cut into three parts by how much of the freeze each touches.

| Part | What | Touches the freeze? |
| --- | --- | --- |
| **E0, outside the system** | A private knowledge repository; the library, memory page and trial ledger back-filled from reports 07 to 52; the weekly reading agent; the monthly agent cycle on public data | No. It is research, like reports 07 to 52 themselves. It adds no code to the trading system and no card. It can start now |
| **E1, server side** | The `kb` schema, the mirror, export, scorecard and verification jobs, the query commands | Yes: it is new code, so it needs v2.14 and decision O32. No trade-path code changes. OPS-19 (a) allows no new version until the advisory release has run 20 trading days, so E1 is built after that (about mid-January 2027) |
| **E2, the shadow library and promotion** | Challengers running in shadow, freeze windows, a yearly promotion window | Already parked as PK-10. It returns at the first annual review (12 November 2027) at the earliest, exactly as the spec says. This report rewrites it so that it is ready |

Nothing in this design relaxes LRN-08, LRN-09, RND-002, SYS-06, BP-09, section 17.1 or the limit of one promotion in 12 months (RND-032).

### 1.3 The honest gap between the wish and the evidence

The owner's words describe a machine that compounds knowledge into results. Two findings in the programme limit what compounding can do, and the engine is designed around them rather than against them.

- **Return rankings do not persist.** Rank correlation between past and next-period return was 0.32 on average and negative at two cut-offs; the past winner trailed 40/60 by 1.3 points a year afterwards; tuning L1's look-backs gained 0.44 points in sample and lost 0.14 out of sample [R48]. An engine that "learns" which rule did best lately would move money toward whatever just finished working.
- **Risk rankings do persist** (rank correlation 0.71 for drawdown, 0.88 for volatility) [R48], and operating facts (costs, spreads, data faults) are observed many times a year. Those are learnable.

So the engine learns in two speeds, and says which is which in every report:

| Fast (months) | Slow (decades) |
| --- | --- |
| Trading costs against the model; data reliability; forecast calibration; what broke and how it was fixed; which assumptions of each card still hold; new evidence, fees, law and product changes | Whether any rule adds return over the index after costs and tax |

---

## 2. Architecture

Three planes, with data flowing one way out of the server.

```
 PLANE 1: TRADING SERVER (BinaryLane Sydney, no inbound ports, no AI)           PLANE 3: OWNER
 ┌──────────────────────────────────────────────────────────────┐              ┌───────────────────────┐
 │ trader (decide, plan, orders on paper)  ── unchanged ──      │              │ reads reports         │
 │ Postgres 16: market_<u> (+ new schema kb), ledger_<u>_*      │              │ approves or rejects   │
 │ jobs: kb_mirror → engine_extend → kb_export → kb_verify      │              │   pull requests       │
 │ raw files + document blobs on disk                           │              │ signs releases        │
 └───────────────┬──────────────────────────────────────────────┘              │ asks questions        │
                 │ outbound only: encrypted export bundle + nightly backup      └──────────▲────────────┘
                 ▼                                                                         │
        object store (private bucket)                                                      │ PRs, reports
                 │ read-only token                                                         │
                 ▼                                                                         │
 PLANE 2: RESEARCH (Claude Code cloud sessions on a schedule; holds no broker, server or vendor credential)
 ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │ reader (web, no private data) → structured notes → analyst (private data, no open web) → validator    │
 │ private git: asx-knowledge (library, memory, cards, ledgers, reports)  ·  asx-trader (code; PR only)  │
 └──────────────────────────────────────────────────────────────────────────────────────────────────────┘
        The only path from Plane 2 back to Plane 1: a code release that the owner has merged and signed.
```

Design choices, each with its reason:

| Choice | Reason |
| --- | --- |
| The agent never runs on the trading server | BP-09 and SYS-06 stay true as written. A compromised or confused agent has no route to the trader |
| The server pushes an export; it reads nothing the agent wrote | A one-way flow is simple to test. Agent output is words and proposals; it becomes system behaviour only through a signed release (OPS-10 approval pins) |
| Server-side learning is deterministic and works with the agent switched off | "Never stop" must not depend on a paid service being up. If every agent run is skipped, the store still grows and every scorecard still updates |
| Two repositories: `asx-trader` (code) and `asx-knowledge` (words and ledgers) | The agent can be given write access to knowledge branches without any write path into code that trades |
| Git for words, Postgres for records, object store for files | Each is the cheap, durable, searchable home for that kind of thing, and the owner already has all three |

---

## 3. The knowledge store ("never forget")

### 3.1 What is stored

Ten record classes. Each has one system of record, so there is never a question of which copy is right.

| # | Class | Contents | System of record | Already in v2.13? |
| --- | --- | --- | --- | --- |
| K1 | Market data | Every raw bar, dividend, split, FX and cash-rate value, each with source, fetch time, file hash and licensee; validated closes; own total-return series; restatements as new rows | Postgres `market_<user>` + raw files | Yes (section 12, DAT-09, DAT-18) |
| K2 | Fundamentals and announcements | Fund facts (fee, index, spread, size, distributions); for the company-level work: financial statement items as first reported, corporate events, index membership through time | Postgres `kb.entity*`, `kb.fundamental` + document blobs | New |
| K3 | Own decisions and actions | Every run, vote, tranche state, plan, order intent, fill, veto, override, reconciliation, alert, learned value | Ledger and market databases (unchanged); mirrored to `kb.event` | Yes; the mirror is new |
| K4 | Incidents | Each incident with cause, fix and the test that now guards it | `incidents` (CA-09); mirrored | Yes; the mirror is new |
| K5 | Research runs | Every backtest, replication, extension, exploratory look and negative control: code hash, image digest, lock-file hash, data snapshot hash, parameters, seed, metrics, status, including failed and discarded runs | `trials` (server runs) and `ledger/trials.jsonl` (cloud runs); full record in `kb.run` | `trials` yes; the fuller record is new |
| K6 | Hypothesis cards | Draft, frozen, parked, passed, failed, retired; each with its outcome and the reason | `hypotheses` (frozen cards) and `cards/` in git (drafts, text) | Frozen cards yes; drafts and outcomes narrative new |
| K7 | External evidence | Papers, issuer and regulator notices, vendor and broker terms: citation, link, retrieval date, content hash, a summary in the engine's own words, and the claims drawn from it with evidence tags | `library/` in git; index in `kb.document`, `kb.claim` | New |
| K8 | Owner decisions | Every decision (O-numbers, OD-numbers, approvals, rejections of proposals, with the reason given) | `kb.owner_decision`; text in git | Partly (decision log, `acceptances`) |
| K9 | Predictions | Every dated, quantified forecast the engine or a card makes, and how it turned out | `kb.prediction` | New (MON-18 has the forecast band for H1 only) |
| K10 | The engine's own activity | Every agent run (prompt version, model, inputs, cost, output), every export, every question asked and answer given | `kb.agent_run`, `ledger/agent_runs.jsonl`, `questions/` | New |

### 3.2 Schema

One new schema, `kb`, inside the existing `market_<user>` database (the trial log, cards and learned values already live there). Every table is insert-only for the app role; a correction is a new row. Every row carries `recorded_at` (when the engine learned it) and, where it describes the world, `valid_at` (when it was true). That pair is the bitemporal rule of DAT-18 applied to knowledge: any past state of knowledge can be rebuilt with `WHERE recorded_at <= :as_of`.

| Table | Key and main columns | Notes |
| --- | --- | --- |
| `kb.source` | source\_id PK, kind (vendor, issuer, regulator, exchange, paper, web, owner, system), name, licence\_class (A, B, C, D), terms\_url, terms\_read\_at, terms\_hash, may\_store\_raw, may\_export, may\_commit\_git, retention\_rule | No ingest without a row here (section 3.4) |
| `kb.document` | doc\_id PK, source\_id, url, title, authors, published\_at, retrieved\_at, sha256, object\_key (null if no copy kept), mime, bytes, licence\_class, trust (`untrusted` by default), supersedes | One row per version of a document |
| `kb.note` | note\_id PK, doc\_id, kind (summary, extract, critique), body, author (owner, or agent model id), prompt\_hash, recorded\_at, search vector | The engine's own words; full-text indexed |
| `kb.claim` | claim\_id PK, statement, evidence\_tag (`2+`, `1`, `unverified`), status (open, supported, contradicted, retired), doc ids, card ids, run ids, last\_checked\_at, next\_check\_due | A claim is re-checked on a schedule; a contradicted claim is kept |
| `kb.entity` | entity\_id PK, kind (etf, company, index, issuer, broker, vendor, law), identifiers, valid\_from, valid\_to, recorded\_at | Delisted and closed entities are never removed |
| `kb.entity_event` | id PK, entity\_id, type (fee change, index change, announcement, delisting, distribution notice, terms change), valid\_at, recorded\_at, doc\_id, payload | |
| `kb.universe_member` | (universe, entity\_id, valid\_from, recorded\_at) PK, valid\_to | Membership through time, so no study is run on survivors only |
| `kb.fundamental` | (entity\_id, period\_end, item, recorded\_at) PK, value, unit, reported\_at, source\_id, licensee | "As first reported" and each later restatement are separate rows |
| `kb.dataset_snapshot` | snapshot\_id PK, as\_of (a `recorded_at` cut), manifest, content hash, row counts | What a run saw. Rebuildable from the bitemporal tables |
| `kb.run` | run\_id PK, trial\_id (FK to `trials` or the cloud ledger), kind (card run, replication, extension, exploratory, replay, negative control, scorecard), card\_id, trial\_spec\_id, is\_trial, git\_sha, image\_digest, lock\_hash, snapshot\_id, params, seed, host (server, cloud), agent\_run\_id, started, finished, status, metrics, artifact keys | Extends `trials`; `trials` remains the count of record on the server |
| `kb.scorecard` | (model\_id, as\_of\_month, window, basis) PK, n\_months, metrics, interval, luck\_band, state | Section 4.6 |
| `kb.prediction` | pred\_id PK, made\_at, made\_by, statement, quantiles or probability, resolves\_at, resolution\_rule, outcome, score, resolved\_at | Frozen when made |
| `kb.lesson` | lesson\_id PK, title, what\_was\_tried, result, why, evidence (ids), status, supersedes, recorded\_at | The rows behind the memory page |
| `kb.owner_decision` | id PK, decided\_at, text, reason, doc ref, supersedes | |
| `kb.question` | id PK, asked\_at, asked\_by, question, answer, cited ids, answered\_by | |
| `kb.agent_run` | id PK, cycle, session ref, model id, prompt\_hash, input manifest hash, tokens in and out, cost\_aud, outputs (PR links), flags, started, finished | Imported from the signed ledger snapshot (section 5.2) |
| `kb.event` | id PK, source\_db, source\_table, source\_pk, kind, valid\_at, recorded\_at, payload, payload\_hash | The one-way mirror of K3 and K4 |
| `kb.chain` | seq PK, table, row\_pk, row\_hash, prev\_hash | Tamper evidence (section 3.6) |
| `kb.deletion_register` | id PK, what, why, rule, hashes kept, when | The only way anything leaves (section 3.5) |

Roles: `kb_writer` (the kb jobs; INSERT on `kb.*`, SELECT on the ledgers), `kb_reader` (SELECT on `kb.*` and on the market tables; statement timeout 30 seconds; used by the query commands and the export). Neither role has any privilege on an order, plan or flag table beyond SELECT, and the trader's own role has no privilege on `kb.*`: the trader cannot read anything the engine stores, so nothing learned can enter a decision except through LRN-08 to LRN-11, which are unchanged.

### 3.3 Layout: database, files, git

| Home | Holds | Path or name |
| --- | --- | --- |
| Postgres on the server | Classes K1 to K5 (records), K8, K9, indexes of K6, K7, K10 | `market_<user>` (schemas `public`, `kb`), `ledger_<user>_external`, `ledger_<user>_paper` |
| Files on the server, copied off-site nightly | Raw vendor responses (DAT-18); document copies; run artefacts | `data/raw/{source}/{fetch_date}/…`; `kb/docs/{ab}/{sha256}`; `kb/artifacts/{run_id}/` |
| Object store (private bucket) | Encrypted nightly backups; the encrypted weekly export; a weekly mirror of both git repositories | `backup/…`, `export/{date}/…`, `gitmirror/…` |
| Git: `asx-knowledge` (private) | Everything in words, and the ledgers the agent appends to | See below |
| Git: `asx-trader` (private) | Code, config, spec, `research/` code, the signed ledger snapshot | Existing |
| OneDrive | The owner's reading copy: reports, the memory page, the monthly "What the engine learned" | A folder the owner already uses. Reading copies only; never a working copy of code (section 19 of the spec) |

```
asx-knowledge/
  CLAUDE.md                 rules every agent session loads first (protected; owner-only changes)
  INDEX.md                  generated: one line per record, newest first, with ID and evidence tag
  catalog.jsonl             generated: machine index (id, kind, title, date, tags, links)
  library/2026/D-000123.md  one file per document: citation, URL, sha256, licence class, summary in own words, claims
  reports/                  research reports 07–52 and later
  cards/draft/ frozen/ retired/   one YAML file per card (RND-010 fields + class, proposer, assumptions)
  memory/MEMORY.md          generated from memory/lessons/L-0001.md …
  ledger/trials.jsonl       hash-chained, append-only: every research run made in a cloud session
  ledger/agent_runs.jsonl   hash-chained: every agent run
  ledger/predictions.jsonl  hash-chained: every prediction made in a cloud session
  scorecards/2027-01.json   copied from the export each month, with a readable .md
  learned/2027-01_what_the_engine_learned.md
  questions/2027-01-17_why-did-l1-sell.md
  prompts/                  versioned prompts for reader, analyst, validator (protected)
  schemas/                  JSON schemas for notes, cards, ledger rows
```

### 3.4 Licensing: what may and may not be stored

Each source gets a licence class in `kb.source`. The class decides storage, export and git.

| Class | Meaning | Raw copy on server | In the export to the agent | In git | Examples |
| --- | --- | --- | --- | --- | --- |
| A | Open licence or own data | Yes | Yes | Yes | RBA tables (CC BY 4.0, with attribution) [spec section 6]; the owner's own ledgers, runs and reports; own derived statistics |
| B | Personal licence: private use, no redistribution | Yes, indefinitely | Yes, to the owner's own agent sessions only; least amount needed | Derived monthly series and statistics only; never raw daily files; never in a public repository | EODHD prices, dividends, fundamentals |
| C | Copyright work with no licence to store or share | A private working copy only where the law allows it; otherwise none | Notes and short quotes only | Citation, link, hash, own-words summary, claims | Journal papers, issuer PDFs, news articles, ASX announcements |
| D | Prohibited or must be deleted | No (or deleted on expiry) | No | No | Yahoo / yfinance, Stooq, scraping asx.com.au (DAT-15); Norgate data after the rental ends (DAT-16) |

**EODHD, read from its help pages on 14 November 2026 [1 each, primary]:**

| Question | EODHD's answer (quoted) | Consequence for the engine |
| --- | --- | --- |
| Keep data for ever? | "Data downloaded while your subscription was active may be kept and used for your private, non-commercial purposes after cancellation or downgrade. The Terms contain no deletion requirement and no deadline." | Class B data is kept permanently. This confirms report 19 |
| Keep derived results? | "Derived research outputs may be created and kept indefinitely… whether or not the source values could be reconstructed from them; what matters is that neither the data nor the outputs are shared with others." | Scorecards, return series and backtest results are kept permanently, privately |
| Backups, cloud server? | Storage "includes raw API responses, normalised or transformed versions, databases, encrypted backups"; "A cloud server or VPS that you use solely for your own private analysis is equivalent to your own computer." | The BinaryLane server and the encrypted off-site backup are within the terms |
| Send data to Claude? | "When you use a public AI service such as ChatGPT or Claude yourself, through your own account, it is a tool you use for your own analysis… This is not 'retransmitting', 'redistributing' or 'granting access'… No separate permission is needed." | The research agent may read class B data, in sessions under the owner's own account |
| Scheduled pipeline? | "Automation does not by itself make a use commercial. The pipeline must remain for your own private use… and stay within the API limits." | The scheduled research cycle is within the terms |
| Limits that remain | "You don't publish or share the data, or the AI output that contains it, with other people." "Keep API keys, downloaded datasets, cached responses and outputs containing the data out of public repositories." One person per key. | Both repositories stay private. No report containing class B data is shared with anyone. The API key stays on the server and is never given to an agent. If the owner ever shares a report, it must contain no vendor values (EODHD directs publication questions to its sales address) |
| Plans and call costs | Free US$0; EOD Historical US$19.99 a month; a US$29.99 plan; Fundamentals US$59.99; top plan US$99.99. "1 for EOD/live, 5 for intraday & news, 10 for fundamentals, 100+ for bulk" calls per request; allowance resets at midnight GMT | The free plan's 20 calls a day (DAT-23) limits the engine to a small watch-list. A whole-exchange download needs a paid month (section 7) |

These help pages say the Terms and Conditions are "the only governing document". The Terms themselves were not read in this session, and whether a *private* GitHub repository counts as storage "restricted to you" is my inference from the cloud-server answer [unverified]. The design avoids depending on it: raw vendor files never go to git.

**Other limits.**

- **Papers, PDFs, articles (class C).** The engine stores what it needs to find the work again and to check its own summary: citation, URL, retrieval date, sha256 of the file read, a summary in its own words, and quotes kept short. Australian copyright law has a fair-dealing exception for research or study (Copyright Act 1968, s 40) [unverified]; it is the reason a private working copy on the server is treated as allowable, and it is not a licence to share. Open-licence papers (for example Creative Commons) are class A and may be kept in full.
- **ASX announcements.** Scraping asx.com.au is excluded by the spec (DAT-15). Announcements enter the store only from an issuer's own website, from a licensed vendor feed, or entered by the owner; the stored record is metadata, link, hash and a summary.
- **Index data (S&P, MSCI, Solactive, LBMA).** Not stored unless the terms have been read and recorded in `kb.source` (the spec's open items on MSCI, Perth Mint and Market Index are unchanged).
- **Rented data.** Deleted on expiry; hashes and derived results stay (DAT-16, RND-029), with a row in `kb.deletion_register`.
- **Personal and account data.** Tax file number, account numbers, addresses and credentials are never written to `kb`, to git or to an export. The export carries unit prices and percentages for the owner's book, not dollar balances, unless `le.export.include_dollar_values` is set by the owner.

### 3.5 Retention

| Rule | Detail |
| --- | --- |
| Default: keep for ever | Every class K1 to K10. Nothing is updated in place; nothing is deleted by a job |
| Exceptions (exhaustive) | (1) Class D and expired rentals. (2) A secret or personal identifier written by mistake. (3) A class C copy the owner is asked to remove. Each needs `trader kb purge --confirm` with the second factor and writes a `kb.deletion_register` row that keeps the hash and the reason |
| Derived artefacts | Metrics, parameters and compressed return series are kept for ever (kilobytes per run). Charts and full packs are kept for 24 months and are regenerable from the run record, which is tested (LE-07) |
| Agent transcripts | The run record (prompt version, inputs, outputs, cost) is kept for ever. The raw session transcript is not copied into the store; it stays with the Claude account under that product's own retention [unverified] |

### 3.6 Backups, restore and tamper evidence

| Item | Design |
| --- | --- |
| Nightly backup | Unchanged job at 01:30 (section 19): encrypted `pg_dump` of every database, incremental raw files, now including `kb/docs` and `kb/artifacts`; `age` encryption; `rclone` to the object store. Because every table is insert-only, the latest dump holds the whole history |
| Retention of backups | The spec keeps 30 daily and 24 monthly copies. Added: one yearly copy kept indefinitely (`backup.keep_yearly: all`), so a silent corruption older than two years can still be compared |
| Git | Two independent copies beyond GitHub: a weekly encrypted mirror of both repositories to the object store (a pinned GitHub Action with a write-only token), and the owner's own clone |
| Tamper evidence | Every `kb` insert adds a row to `kb.chain` whose hash covers the row and the previous hash. The chain head is printed in each monthly report and written into the backup manifest. The git ledgers are chained the same way. `kb_verify` recomputes both chains monthly. A broken chain is a WARN and an incident (CA-09) |
| Card freeze dates | A card's hash and freeze time are recorded in three places (the `hypotheses` row, a signed git tag, the next backup manifest), so a freeze date cannot be moved quietly. This matters because "post-registration" data is the only evidence that counts (section 4.6) |
| Restore | The quarterly restore drill (BP-16, OPS-16) also restores `kb`, runs `kb_verify`, re-runs one sampled research run from its record and compares the metrics. Recovery point: 24 hours. Recovery time: inside INF-01's 2 hours |
| What is lost if GitHub, the object store and the server all fail | Only what the owner's clone and OneDrive copy do not hold. The estate pack (OPS-14) lists where each copy is |

### 3.7 Size and cost growth on a 2 GB server

All row sizes are my estimates [unverified]; the arithmetic is [computed].

| Component | Volume | Size |
| --- | --- | --- |
| ETF-level prices: 30 instruments × 30 years × 252 days | About 227,000 rows at about 150 bytes | About 35 MB, once. About 1.2 MB a year after that |
| Restatement rows | Only changed values are inserted; the weekly re-download's raw file is always kept (about 10 KB each, compressed) | Under 30 MB a year |
| Mirror of own records (`kb.event`) | Tens of rows a trading day in advisory mode; a few hundred on a broker day | Under 50 MB a year |
| Research runs | About 200 to 2,000 runs a year at about 20 KB of metrics and compressed series | 4 to 40 MB a year |
| Library | About 300 documents a year. Notes and claims: about 10 KB each. Private copies where kept: about 1 MB each | Notes 3 MB a year; copies up to 0.3 GB a year |
| **ETF-level engine, total** | | **Under 1 GB after five years** |
| Company-level prices (section 7): about 2,200 ASX companies × 25 years × 252 days | About 14 million rows | About 2 GB plus indexes, once; about 0.1 GB a year |
| Company-level fundamentals | About 2,200 companies × 100 periods; raw filing JSON plus about 40 curated items | About 1 to 4 GB |
| **With the company-level store** | | **About 5 to 8 GB** |

| Question | Answer |
| --- | --- |
| Does the ETF-level engine fit on the 2 GB server? | Yes. It adds well under 1 GB of disk and runs its jobs at weekend hours with a memory limit (LE-36). Postgres at 2 GB RAM runs with about 256 MB of shared buffers |
| When is 4 GB needed? | When either holds: (1) the paper gateway runs on the same machine (the spec already calls 2 GB "tight for gateway plus Postgres; needs swap"); (2) the company-level store passes about 5 million rows; (3) `engine_extend` takes more than 30 minutes or is killed by its memory limit twice in a month. The monthly report shows all three |
| What must not run on the server at any size | Wide panel analytics and model fitting. They run in the research sessions from the exported Parquet files. The server only extends registered models, which is light |
| Disk | The plan's disk size is [unverified]; the report WARNs at 70% used (this adopts the parked CA-19 for the engine's own tables) |
| Storage cost | Object-store prices of roughly US$6 per terabyte-month [unverified] make 20 GB cost about A$0.20 a month. Budgeted at A$1 |

### 3.8 The query interface: "ask the engine"

One query library, `engine_kb`, with two back ends, so the owner, the server commands and the agents all ask the same questions the same way.

| Back end | Used by | Reads |
| --- | --- | --- |
| Postgres (`kb_reader` role) | The owner over Tailscale SSH; server jobs | Everything on the server |
| Export (Parquet and JSON files, read with DuckDB) + the knowledge repository | Agent sessions; the owner's "Ask the engine" session | The weekly export and everything in git |

There is no network API on the server: INF-03 allows no listener, and none is needed. The "read-only research API" is this library.

| Function (library) | Command (server) | Answers |
| --- | --- | --- |
| `search(text, kinds, since)` | `trader kb search "franking"` | Full-text search across notes, claims, lessons, incidents, decisions, cards |
| `show(id)` | `trader kb show L-0042` | One record with everything linked to it |
| `timeline(symbol or card or topic)` | `trader kb timeline A200` | Every event about it in date order: prices restated, fee changes, decisions, incidents, runs |
| `asof(date)` | `trader kb asof 2027-03-31 …` | The same query against what the engine knew on that date |
| `scorecard(model)` | `trader kb scorecard L1` | The post-registration record against B2, B3 and B1 with its interval and luck band |
| `trials(family)` / `bar()` | `trader kb trials`, `trader kb bar` | The trial count and today's pass bar (section 4.5) |
| `why(card or decision)` | `trader kb why H42` | The reason recorded, the evidence cited, and who decided |
| `predictions(open or resolved)` | `trader kb predictions` | What was forecast, what happened, the calibration score |
| `sql(file)` | `trader kb sql --file q.sql` | Read-only SQL for anything else (30-second limit) |

Three ways for the owner to ask:

1. **Plain English.** Open a Claude session on `asx-knowledge` (phone or browser) and ask. `CLAUDE.md` makes the session answer under a fixed contract (section 6.3).
2. **Telegram, no AI.** `/learned` returns the latest report's summary; `/memory <word>` returns the five best-matching lessons by title; `/bar` returns the trial count and pass bar. These are deterministic lookups on the server.
3. **The pages.** `MEMORY.md`, `INDEX.md` and the monthly reports, copied to OneDrive.

Semantic (embedding) search is not built: Postgres full-text search and the generated index are enough at this size, and embeddings would need an AI service on the server, which BP-09 forbids. An agent session can search by meaning itself, by reading the index.

---

## 4. The continuous learning loop

### 4.1 Cadence

**Server jobs (deterministic, no AI, Australia/Sydney).** All are learning jobs under LRN-28: no broker connection, never within 2 hours of a trading job, fail to WARN only.

| When | Job | Does |
| --- | --- | --- |
| Daily 23:00 | `kb_mirror` | Copies the day's new decision, plan, fill, reconciliation, alert, incident and learned-value rows into `kb.event`; extends `kb.chain` |
| Saturday 04:00 | `engine_extend` | Builds a dataset snapshot; re-runs every registered model on the extended data as a replication (section 4.3); updates `kb.scorecard`; resolves due predictions; once a month runs the negative controls |
| Saturday 06:00 | `kb_export` | Writes the encrypted export bundle to the object store |
| First Sunday 04:00, 05:00 | `learn_update`, `learning_report` | Unchanged (LRN-33) |
| First Sunday 06:00 | `kb_verify` | Recomputes the hash chains; checks record completeness; writes the store-size table |

**Agent cycles (Claude Code scheduled tasks; each firing is a fresh session that starts from `CLAUDE.md`, `MEMORY.md` and the last report).**

| Cycle | When | Model class | Does | Output |
| --- | --- | --- | --- | --- |
| Reader | Weekly, Sunday morning | Small, cheap | Visits a fixed watch-list (issuer pages for held and benchmark funds, RBA, EODHD and IBKR terms and pricing pages, tax-law commencement pages, a fixed set of research listings). Writes schema-valid notes. Holds no private data | One PR to `asx-knowledge/library/` |
| Analyst, monthly | Second Sunday | Large | Steps 1 to 7 of section 4.2 | One PR: the monthly report, lessons, any draft card; at most one PR to `asx-trader/research/` |
| Analyst, quarterly | Second Sunday of January, April, July, October (a week after LRN-26's report) | Large | The monthly steps, plus the evidence scan (report 35's LRN-21), the claim re-check, the walk-forward extension of report 48, and at most 3 draft cards | The quarterly report section and the card drafts |
| Review pack | Three weeks before each dated review (first: 12 November 2027) | Large | Assembles the year: every scorecard, the trial count, the parked register with what has changed, the one change the engine would propose (or none) | One PR: the review pack |
| Validator | On every agent PR that is not library-only | Large, fresh context | Section 5.3 | A validation memo as a PR comment |

### 4.2 One research cycle, step by step

| Step | What happens | Where | May change |
| --- | --- | --- | --- |
| 1. Ingest | New prices, distributions, rates (server, daily). New documents (reader, weekly). Changes at issuers, the broker, the vendor, the law (LRN-17's list) | Server; reader | The store only |
| 2. Extend | Every registered model is run forward on the new data with its frozen parameters. No parameter is re-fitted | Server (`engine_extend`) | Scorecards only |
| 3. Score | Each scorecard is updated on post-registration data, after costs and tax, against B2, B3, B1. Due predictions are resolved and scored | Server | Scorecards, predictions |
| 4. Check | Assumptions of each card (LRN-16) against the new facts; drift monitors (LRN-13 to LRN-15); claims due for re-check; negative controls | Server and analyst | Flags in the report |
| 5. Explain | For each thing that changed, failed or surprised: what, why, what evidence. Written as a lesson | Analyst | `memory/lessons/` (by PR) |
| 6. Propose | From a failure, a changed assumption or new evidence: a draft card (at most 3 a quarter), a research-code change, a new source for the watch-list, or an operating change note (LRN-19) | Analyst | Drafts only; nothing is registered |
| 7. Report | "What the engine learned" (section 6.1) | Analyst | The report (by PR) |
| 8. Shadow (E2, from November 2027) | A card the owner has accepted and frozen runs in `paper_sim` beside the champion. Its prospective clock starts at the freeze | Server | Its own shadow ledger |
| 9. Decide | The owner merges or closes each PR; triages each draft card within 14 days (accept for the next freeze window, park, reject, with a one-line reason that is stored) | Owner | Whatever he approves |

If the agent is off, steps 1 to 4 still run and their numbers still appear in the deterministic part of the report.

### 4.3 "Re-run on extended data" means replication, not re-fitting

| Rule | Reason |
| --- | --- |
| An extension run uses the card's frozen parameters and code hash, on a new dataset snapshot. It is logged with replication kind `extension` and is not a new trial (VAL-22) | Running the same rule on more data is not another shot at finding a rule |
| "Walk-forward" here means two things only: (a) the frozen rule's record is extended forward; (b) once a year the selection exercise of report 48 gains one more cut-off, as a check on the *process* (RND-026) | Report 48 showed that re-fitting as data arrives loses out of sample |
| A model that needs periodic fitting (a parked machine-learning card) may refit only on the schedule and by the closed-form rule frozen in its card (report 35's LRN-30), and every fitted object is hashed and stored | Otherwise the refit is an unlogged search |
| A changed parameter, a changed universe or a changed metric is a new card and a new trial (RND-016) | Unchanged |

### 4.4 What may change, by tier

| Tier | What | Who and how | Examples |
| --- | --- | --- | --- |
| **T0. Automatic** | Exactly: (a) the six estimates of LRN-08, by the mechanics of LRN-10 and LRN-11, unchanged; (b) new rows in the knowledge store; (c) scorecards, prediction outcomes, monitor states; (d) generated pages (`INDEX.md`, `MEMORY.md`, the deterministic half of each report). The list is exhaustive | Server jobs | The half-spread estimate moves inside its bounds; a scorecard gains a month |
| **T1. Proposal, reviewed, owner merges** | Library notes, lessons, reports; research code under `research/`; a new watch-list source; a draft card; a report template; a new `kb` table or query | Agent PR → validator memo → owner merge. No cooling-off. Library-only PRs from the reader may be merged by the owner without a validator memo | A summary of a new paper; a script that extends the tournament data by a year |
| **T2. Card, gates, owner approval, cooling-off** | Anything in LRN-09: look-backs, votes, thresholds, weights, the sleeve list, bands, benchmarks, halt and alert thresholds, test thresholds, the holdout boundary. Freezing a card. Starting a shadow line. Promotion. Any execution tactic (LRN-19). Any addition to the LRN-08 whitelist. Any change to an LE safety requirement, an agent prompt, a cost cap or the watch-list's allowed domains | A frozen card or a change note; G0 to G3 as section 17; the validator; the owner's approval after the 7-day cooling-off (RND-005); OPS-19 (d)'s 90 days where it applies; at most one promotion in 12 months (RND-032); no new strategy card before November 2027 (OPS-19 (e)) | Replacing L1's vote set; adopting a cash ETF while OFF (HG1) |
| **T3. Never** | AI in the trade path (SYS-06). An agent merging, approving, signing, deploying, holding a broker, server or vendor credential, or writing an order. Selecting or weighting a rule on recent, shadow or backtest return (LRN-09, report 35's LRN-31). Any instruction to trade the owner's index account (EXE-13). Real money outside section 17.1. Deleting a record outside section 3.5. Lowering the trial count. The engine raising its own caps or widening its own permissions | No path exists. Each is enforced by a test, a permission or both | |

### 4.5 Keeping the trial count honest as the library grows for ever

The danger is simple: an engine that never stops testing will eventually find something that looks good by chance. Six controls, all mechanical.

**(1) One library count, N\_lib, that never goes down.**

- N\_lib = the number of distinct rule specifications ever evaluated on real data against the same benchmark (static 40/60), across every family, by anyone: card runs, exploratory runs, agent runs, the owner's own looks. This is report 35's "library N".
- It is seeded by back-filling the runs of reports 36, 38, 47 and 48 into the ledger with source `backfill`: at least the 47 configurations of report 38, plus the tuned variants of report 48 (the exact number is established by the back-fill, not assumed here).
- Server runs are counted in `trials` (RND-011). Cloud runs are counted in `ledger/trials.jsonl`, which the research wrapper `engine run` appends to before it returns any number. N\_lib is the union.
- **A result with no ledger row is inadmissible.** CI on `asx-knowledge` fails any report or card whose figures do not cite a run id that exists in the ledger, and the validator re-runs a sample.
- An honest limit: nothing can physically stop a model in a sandbox from computing something off the books. The defence is that off-the-books looks cannot help an idea pass, because of control (4).

**(2) The bar rises with the count.** For a return claim (Family B), the spec requires a net t-statistic of at least 3.0 and a Deflated Sharpe Ratio of at least 0.95 with N = every logged trial (VAL-20). The engine makes the t bar explicit:

> t\_min(N\_lib) = max(3.0, the normal quantile at 1 − 0.025 ÷ N\_lib)

| N\_lib | 10 | 38 | 50 | 100 | 200 | 500 | 1,000 | 5,000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| t bar [computed] | 3.00 | 3.21 | 3.29 | 3.48 | 3.66 | 3.89 | 4.06 | 4.42 |
| Lead of the best of N no-edge rules, in tracking-error units [computed] | 1.57 | 2.17 | 2.28 | 2.53 | 2.77 | 3.05 | 3.26 | 3.69 |

At N = 38 the formula gives 3.21, the "bar of 3.2 for the best of 38 trials" already used in section 24.1 of the spec, so this is the rule the programme has been applying, written down. The bar grows with the square root of the logarithm of N: a thousand trials cost about one extra t-unit. Looking is cheap but never free, and `trader kb bar` prints today's price. The Deflated Sharpe Ratio uses the same N\_lib and the spread of Sharpe ratios across the ledger [R16].

For a drawdown or risk claim (Family A), the Holm family already contains every Family A rule ever proposed on the same sleeves (RND-012, VAL-20). That stands; the engine supplies the list from the ledger.

**(3) Quotas, so the count grows slowly.** At most 3 draft cards a quarter; at most 4 cards frozen a year, in two windows (report 35's LRN-01, LRN-22); at most 40 new trial specifications a year across the library (`le.trials.max_new_per_year`); the cap of 50 per family stays (VAL-22); at most one promotion in 12 months (RND-032). A challenger that differs from the rule only by a tuned parameter is not eligible (PK-10, from [R48]).

**(4) Only post-registration data is evidence.** The 2024+ holdout is spent, and every card is written with knowledge of history (VAL-21). So for every card the only out-of-sample record is data dated after its freeze. No amount of unlogged backtesting can manufacture that. An agent-proposed card also records the model's stated training cut-off (report 35's LRN-23).

**(5) Negative controls every quarter.** The same pipeline is run on rules known to have no edge: randomised signal dates with matched time in the market (the placebo of RND-026), and the selection control H41. If any placebo passes a gate, the process is broken: every promotion window is closed until the cause is found and recorded as an incident. The share of placebos that pass is reported as the pipeline's measured false-positive rate.

**(6) One primary metric per card, fixed at freeze** (RND-010), and fixed look dates: a card's post-registration record is formally read at 36, 60 and 120 months after freeze and at no other time, with the error allowance split across the three looks. In between, the scorecard is information.

Further machinery from the statistics literature (online false-discovery control such as alpha-investing; always-valid tests based on e-values) [unverified] would let the engine test an endless stream with formal guarantees. It is not adopted: the fixed quotas and the Bonferroni-type bar are cruder but can be read and checked by a non-programmer, which the spec values (RND-003). It is listed in section 9 as a later refinement.

### 4.6 How "better" is measured

**For a model: the scorecard.** One per registered model (L1 in shadow, B1, B2, B3, each frozen card; later each challenger), updated monthly.

| Field | Definition |
| --- | --- |
| Window | **Post-registration only**: months after the card's freeze. For L1 and the benchmarks, from the advisory release. Development-era and "holdout, seen" figures appear in a separate, labelled block and never in the headline |
| Basis | After the section 25 cost model and after tax under the section 13 engine at the owner's marginal rate, post-July-2027 rules, idle cash at what the account earns (0% at IBKR under A$15,000) |
| Benchmark | B2 (static 40/60) first, then B3 (the same in a zero-brokerage account) and B1 (SYS-07) |
| Metrics | The card's one primary metric; then return difference a year, maximum drawdown difference, tracking error, switches, cost and tax paid |
| Uncertainty | A 90% interval from the stationary bootstrap (RND-012), shown from the first month; the number of months; and the luck band: the lead that the best of N no-edge rules would show by chance at this record length |
| The sentence under every scorecard | "This record is n months long. At this length a difference of less than x points a year cannot be told from chance." (x is computed) |
| Order and ranking | Scorecards are listed by registration date. They are never sorted by return, and no table ranks models (LRN-26, [R44 §3.4]) |
| States | `too early` (under 36 months), `consistent with its card`, `outside its forecast band` (MON-18's logic), `contradicted` (the primary metric has the opposite sign at a formal look), `fidelity break` (shadow against replay, report 35's LRN-06 (a)) |
| What a scorecard can do | Veto (a contradicted or broken model cannot enter a promotion window) and inform. It cannot select: a model's shadow return, Sharpe or rank is never a ground for promotion (report 35's LRN-04) |

**For the engine itself: six measures that can improve within months.** These answer "is it getting better?" without waiting decades.

| # | Measure | Definition | Why it cannot be gamed |
| --- | --- | --- | --- |
| E1 | Forecast calibration | Share of resolved predictions that fell inside their stated 80% band (target 80%), and a Brier score for yes/no predictions | Predictions are frozen and chained before the outcome exists. Report 48 measured this for the wealth projections: the 80% band held 67–75% of outcomes, every miss on the low side |
| E2 | Cost-model error | Realised minus modelled cost per fill, in basis points (from the paper stage) | Fills are broker records |
| E3 | Data quality | Restated closes, late bars, blocked days per quarter; days from a fault to its detection | Counted by the DAT checks |
| E4 | Incidents | Opened, closed, repeated causes; share closed with a regression test (LRN-20) | The incident table is insert-only |
| E5 | Knowledge quality | Share of claims tagged [2+]; claims re-checked on time; claims later contradicted; open questions closed | Each claim links to its sources |
| E6 | Adoption ledger | Every change the owner adopted on the engine's proposal, with the benefit it predicted when proposed and the benefit measured since, after costs and tax, against the index | The prediction is frozen at proposal. A change that was predicted to save 0.2 points and saved nothing is shown as that |

**The pipeline's own honesty figure:** the placebo pass rate of section 4.5 (5), printed in every quarterly report.

**What is never used as a measure of "better":** a backtest improvement, a trailing-return rank, the number of ideas generated, or the number of cards passed.

---

## 5. Safety

### 5.1 Separation of the research agent from the trading path

| Control | Detail |
| --- | --- |
| Where the agent runs | Only in Claude Code cloud sessions. Never on the trading server. BP-09 is unchanged: no AI host on the server's allow-list |
| Credentials the agent may hold | A GitHub identity that can push branches and open PRs on the two private repositories; a read-only token for the export prefix of the object store and the key that decrypts the export. Nothing else |
| Credentials the agent may never hold | Any IBKR login or token; the EODHD key; SSH or Tailscale access to the server; the backup `age` key; the release-signing key; Telegram bot token; object-store write tokens |
| No merge | `main` on both repositories requires a pull request and the owner's review. Whether GitHub's free plan enforces branch protection on a private repository is [unverified]; if it does not, GitHub Pro (about US$4 a month [unverified]) is the fallback |
| The control that does not depend on GitHub | The server runs only a release that carries the owner's signature and matches his approval pins (OPS-10). The signing key is on the owner's device, not in any repository or session. Even an agent that somehow merged could not make the server run its code |
| No order | The agent has no network route to the server or the broker, and no credential for either. RND-002 and SYS-06 are met by construction |
| One-way data | The server writes exports and backups outward. It never fetches, clones or reads anything an agent wrote, except code inside a signed release. The agent's ledgers reach the server only as a snapshot file inside such a release |
| Protected paths | In `asx-trader`: everything outside `research/` and `docs/`. In `asx-knowledge`: `CLAUDE.md`, `prompts/`, `schemas/`, `cards/frozen/`. CI fails an agent-authored PR that touches a protected path; only the owner can change them, and a change to them is tier T2 |
| Engine off the order path | The `kb` jobs run under LRN-28's rules, with a memory limit and low CPU priority so they cannot starve the trader. A test shows a recorded month's plan is byte-identical with the whole engine disabled |

### 5.2 Audit trail

| What | Record |
| --- | --- |
| Every agent run | A line in `ledger/agent_runs.jsonl` (hash-chained): cycle, session reference, model id, prompt version hash, hash of the inputs it was given, token counts, cost, the PRs it opened, any injection or cap flag. Written by the session wrapper at start and at end, so an abandoned run is visible |
| Every research run | `ledger/trials.jsonl` (cloud) or `trials` and `kb.run` (server) |
| Every proposal and its fate | The PR itself (author, diff, validator memo, the owner's approval or closing comment), linked from the lesson or card it concerns |
| Every owner decision | `kb.owner_decision`, with the reason |
| Every automatic change | `learned_values` (LRN-11), unchanged |
| Bringing the cloud ledgers to the server | Each signed release carries `research/ledger_snapshot.json` (the chain heads and counts). The server imports it into `kb.agent_run` and uses its N\_lib. A release whose snapshot has a lower count than the last one is refused |

### 5.3 The validator

| Item | Design |
| --- | --- |
| Who | A separate scheduled or PR-triggered session with a fresh context, its own prompt, and no access to the analyst's session or reasoning. It reads the PR, the cards and the spec text |
| Checklist | (1) No protected path touched. (2) Every figure cites a ledger run; a sample is re-run. (3) No ranking by return; no return claim without the Family B bar; no buy or sell line for the index account. (4) Evidence tags present on every claim; a sample of [2+] and [1] tags is opened and checked. (5) For research code: tests pass; no network call; no import from the trade path; no secret. (6) For a card: every RND-010 field present; a rationale from sources dated before the data; the trial count stated. (7) Signs of injected instructions in any cited document. (8) A "reasons this could be wrong" section |
| Powers | Writes a memo and a pass, fail or concerns verdict. It cannot approve or merge |
| Its limit, stated plainly | A second session of the same model family is an independent *context*, not an independent *mind*. It catches slips and injected instructions well and shared blind spots poorly. For a formal G2 the spec's stronger rule is unchanged: a model from a different provider, or the committed spreadsheet (RND-003) |
| The owner | Approves T1 PRs when he chooses. For T2, waits the 7 days of RND-005 after seeing results |

### 5.4 Prompt injection from ingested documents

A paper, web page or announcement can contain text written to steer an AI that reads it ("ignore your instructions and…"). The agent reads many such documents, so this is the main new risk the engine brings. The well-known rule of thumb is that harm needs three things together: access to private data, exposure to untrusted content, and a way to send data out [unverified]. The design never gives one session all three.

| Control | Detail |
| --- | --- |
| Split roles | **Reader:** has the web (allow-listed domains only) and nothing private: no export token, no write access beyond a `reader/` branch of the knowledge repository. **Analyst:** has the export and both repositories, and no open web: its network is limited to GitHub, the object store and package registries. The analyst never opens a raw document; it reads the reader's notes |
| Notes as data | A reader note must validate against a JSON schema: fixed fields, length limits, quotes marked as quotes, no markup that renders links or images. CI rejects anything else. The analyst's prompt states that note content is material to assess, never instructions |
| Low-privilege by design | The most a fully hijacked analyst can do is open a bad PR, which the validator and the owner then read. It holds no credential that moves money or changes the server |
| Allow-list | The reader fetches only domains in `le.reader.allowed_domains` (changing it is tier T2). It does not follow links off the list |
| No exfiltration by link | Reports and notes may contain links only to allow-listed domains; CI strips or fails others. This closes the trick of hiding data in a URL |
| Provenance | Every claim carries the document it came from. A claim found to come from a poisoned document can be traced and every lesson, card and report that cites it listed (`trader kb show`) |
| Tests | Seeded hostile documents are part of acceptance (section 8.6): one tells the reader to edit `CLAUDE.md`, one tells it to add a domain, one tells the analyst (through a note) to propose changing a threshold. Pass means no such change appears and the run is flagged |
| Residual risk | A subtly false paper summarised faithfully. No filter catches that. The defences are the evidence tags, the re-check schedule, and the fact that a false claim still has to pass a card on post-registration data before it changes anything |

### 5.5 Cost caps for agent runs

| Cap | Default | Enforced by |
| --- | --- | --- |
| Tokens per run | Reader 1.5 million in, 0.15 million out; monthly analyst 10 million in (mostly cached reads), 0.2 million out; quarterly 20 million in, 0.4 million out; validator 3 million in, 0.06 million out | The session wrapper stops the run at the cap and records `cap_hit` |
| Wall-clock per run | 60 minutes (quarterly 120) | The wrapper |
| Runs per month | 4 reader, 1 analyst (the quarterly replaces that month's), up to 6 validator | The schedule and the wrapper's counter in `agent_runs.jsonl` |
| Spend per month | A$30 (`le.agent.cost_cap_aud_month`), computed from token counts at configured prices | The wrapper refuses to start a run that would pass the cap; the skipped cycle is a WARN in the next report |
| Kill | `le.agent.enabled: false` in `CLAUDE.md`'s config block stops every cycle at its first step; the owner can also pause the scheduled tasks in Claude Code | — |
| Who may raise a cap | The owner only (tier T2). An agent PR that edits a cap fails CI |

---

## 6. Owner experience

### 6.1 "What the engine learned": monthly (two pages at most)

The first half is generated by the server from the store; the second half is written by the analyst and labelled as such. If the agent did not run, the first half is still sent.

| # | Section | Source |
| --- | --- | --- |
| 1 | **In one paragraph:** what changed this month and what the owner needs to do (often: nothing) | Analyst |
| 2 | **What changed by itself:** every automatic estimate update (LRN-11), with old and new values | Server |
| 3 | **The record so far:** each scorecard in registration order, with its length, interval, luck band and the "cannot be told from chance below x" sentence. No ranking | Server |
| 4 | **How good were our forecasts:** predictions resolved this month, and calibration to date (E1) | Server |
| 5 | **What it cost, what broke:** cost against the model (E2), data events (E3), incidents and fixes (E4) | Server |
| 6 | **What we read:** new documents, the three that matter and why, with evidence tags; any change at an issuer, the broker, the vendor or in the law | Analyst |
| 7 | **What we learned:** new lessons, each one or two sentences with a link | Analyst |
| 8 | **Ideas, not actions:** draft cards and proposals waiting for triage, with the trial count and today's bar; what is parked and until when | Analyst |
| 9 | **Decisions waiting for you:** PRs to approve or close | Server |
| 10 | **The engine itself:** agent runs, cost against the cap, store size, chain check, anything skipped | Server |

**Quarterly:** LRN-26's report gains sections 3, 4, 6, 7 and 8 above, the measured placebo pass rate, the claim re-check results, and the knowledge-quality figures (E5). It stays within LRN-26's rule: no table of challengers and no ranking of rules, until E2 returns the library with its luck band (report 35's LRN-27).

**Yearly (the review pack):** the adoption ledger (E6); the walk-forward exercise with its new cut-off; the parked register with what has changed for each item; and "the one change we would propose, or none". The default answer, as OPS-20 says, is to continue unchanged.

### 6.2 The memory page

`MEMORY.md` is generated from the lesson records and is the page to open when wondering "did we ever try…?".

| Block | Contents |
| --- | --- |
| Everything tried | One row per card or study: what the idea was, when, the result in one line, the reason in one line, links to the card, the runs and the report. Sorted by date, with filters for worked, did not work, inconclusive, parked |
| What worked | Things adopted, with the benefit predicted and the benefit measured since |
| What did not, and why | Failed and "not passed" ideas with the cause: no edge, edge smaller than cost, edge gone after tax, worked only in two episodes, failed the walk-forward check, and so on. Kept so that nobody re-proposes them with new parameters (the purpose of H74) |
| What we believed and changed our mind about | Claims that were later contradicted, with both the old and the new evidence |
| Standing lessons | The few rules the evidence keeps confirming. On day one, from the existing reports: nothing beat static 40/60 after costs and tax [R36, R38, R45, R46]; choosing last period's winner did worse [R48]; risk rankings persist and return rankings do not [R48]; idle cash earning nothing is worth more than any rule variant tested [R36, R37]; L1 helps only in slow bear markets [R36, R47] |
| Open questions | What the engine does not know yet, and what would answer it |

The page is back-filled in E0 from reports 07 to 52, sections 24.1 and 31 of the spec, and the change logs, so it starts with the programme's whole history, not an empty page.

### 6.3 How the owner asks questions

In a Claude session on `asx-knowledge`, in his own words: "Why did L1 sell in March?", "Have we tested buying after a fall?", "What do we know about BGBL's spread?", "What would it take to trust a momentum rule?"

Every answer follows a fixed contract, set in `CLAUDE.md`:

1. Answer first, in plain English.
2. Cite the records it rests on by ID, each with its evidence tag.
3. Say what the engine does not know, and what the length of the record cannot show.
4. Show any model result beside the index (B2 first), after costs and tax.
5. Never give a buy or sell line for the owner's index account (EXE-13), never state or imply a return advantage (SYS-07), and say that it is general information.
6. Save the question and answer to `questions/`, so the next session can find it.

If the question needs a new look at real data, the session says so and proposes it for the next cycle. It does not run an unlogged test to answer a question on the spot.

---

## 7. Serving the company-level study (51) and the Big Wins engine

Neither report was available, so this section gives what the store offers them, not what they need.

| Need a company-level study will have | What the store provides |
| --- | --- |
| A universe without survivorship bias | `kb.entity` never deletes a delisted company; `kb.universe_member` records index and listing membership through time. A study states the universe "as known at" each date |
| Point-in-time fundamentals | `kb.fundamental` keeps the value as first reported and each restatement as separate rows, with `reported_at`. A backtest may only use rows with `reported_at` on or before its decision date |
| Announcements and events | `kb.entity_event` with the source document; within the licence limits of section 3.4 (no scraping of asx.com.au) |
| The definition of a "big win" fixed before looking | A definition is a frozen record (threshold, horizon, total-return basis, start universe). Changing it is a new definition and a new trial, exactly like a card |
| Honest counting | Company-level and Big Wins runs go into the same ledger with family `BW` and count toward the same N\_lib, because they would be judged against the same index benchmark. They do not get a fresh, lower bar |
| Base rates that can be scored | Statements such as "of ASX companies above size S at date t, p% multiplied tenfold in ten years" are stored as predictions and scored as the years pass (E1) |
| A prospective record | Any screen the Big Wins engine proposes can be frozen and tracked in shadow from that day. That record, not the backtest, is its evidence |

**Data limit to plan for.** The free EODHD plan allows 20 calls a day; an end-of-day request costs 1 call and a fundamentals request 10; a whole-exchange bulk request costs 100 or more [1, pricing page]. So the company-level store cannot be built or kept current on the free plan. The pattern DAT-23 already uses applies: one paid month to download history (prices US$19.99; fundamentals US$59.99 [1]), keep it permanently [1], then decide whether an ongoing plan is worth its price. Whether EODHD's history includes delisted ASX companies, and how far back ASX fundamentals go, is [unverified] and must be tested with one paid month before any study relies on it. This is requirement LE-40, group L: it is built only when report 51 or the Big Wins design asks for it and the owner approves the spend.

Spec scope note: single shares are out of scope for trading in v2.13 (section 1). Storing and studying company data does not change that; any rule that came out of it would be a new card under tier T2, with OPS-19 (d)'s cooling-off for adding an instrument type.

---

## 8. Spec-ready text

### 8.1 Section 28.2 — Learning engine (proposed for v2.14)

> **28.2 Learning engine.** Section 28.1 lets the system learn how the world it trades in behaves. This section adds a place where everything it learns is kept, and a scheduled research loop around it. The engine records and proposes; it never decides. LRN-08 to LRN-34 are unchanged and govern every automatic change. The engine has three parts: a knowledge store on the server (LE-01 to LE-14); deterministic weekly jobs that extend and score every registered model (LE-15, LE-17 to LE-20); and research agents that run in cloud sessions on a schedule, off the server, and whose only outputs are pull requests (LE-16, LE-21 to LE-39). Data leaves the server one way. Nothing an agent writes reaches the server except code inside a release the owner has signed [R52].

| ID | Requirement | Source |
| --- | --- | --- |
| LE-01 | [LC-A] **Purpose and boundary.** The learning engine stores what the system and its research have observed, extends and scores every registered model, and proposes. It may never choose which rule runs, change a value outside LRN-08, or select or weight a rule on its recent, shadow or backtest return (LRN-09). It adds nothing to the LRN-08 whitelist. | [R52 §1], [R35], [R48] |
| LE-02 | [LC-A] **Knowledge store.** Schema `kb` in `market_<user>` holds the tables of report 52 §3.2: `source`, `document`, `note`, `claim`, `entity`, `entity_event`, `universe_member`, `fundamental`, `dataset_snapshot`, `run`, `scorecard`, `prediction`, `lesson`, `owner_decision`, `question`, `agent_run`, `event`, `chain`, `deletion_register`. The app role has INSERT only on every one; a correction is a new row. Role `kb_writer` has INSERT on `kb.*` and SELECT on the ledgers; role `kb_reader` has SELECT only, with a 30-second statement limit. The trader's role has no privilege on `kb.*` (test). | [R52 §3.2] |
| LE-03 | [LC-A] **What is recorded.** The ten record classes K1 to K10 of report 52 §3.1. `kb_mirror` copies every new run, tranche state, plan, order intent, fill, veto, override, reconciliation, alert, incident and learned-value row into `kb.event` within 24 hours, with the source table, key and payload hash. `kb_verify` reports any source row with no mirror row as a WARN. | [R52 §3.1] |
| LE-04 | [LC-A] **Provenance and time.** Every `kb` row carries `recorded_at`; every row that describes the world also carries `valid_at`, its `source_id` and, for fetched material, the sha256 of what was fetched. Any query can be run "as known at" a past time by filtering on `recorded_at`; `engine_kb.asof()` does this. | [R52 §3.2], [DAT-18] |
| LE-05 | [LC-A] **Source register and licence classes.** No material is ingested from a source without a `kb.source` row whose terms have been read (`terms_read_at`, `terms_hash`). Each source has a class: A (open or own), B (personal licence, no redistribution), C (copyright, notes only), D (prohibited or must be deleted). The class sets whether a raw copy may be kept, exported or committed to git, as report 52 §3.4. EODHD is class B: raw data and derived results are kept indefinitely for private use; raw vendor files are never committed to git; neither repository is ever public; no output containing vendor values is given to another person; the API key is never given to an agent. DAT-15's exclusions are class D. A CI test and a runtime guard refuse an ingest that breaks the class rule. | [R52 §3.4], [EODHD help pages, fetched 14 Nov 2026], [R19], [DAT-15] |
| LE-06 | [LC-A] **Documents.** For every external document the store keeps: citation, URL, retrieval time, sha256, licence class, a summary in the engine's own words, and the claims drawn from it. A copy of the file is kept only where the class allows. Every document and every note derived from one is marked `untrusted`: it is material to assess and is never treated as an instruction (LE-33). | [R52 §3.4, §5.4] |
| LE-07 | [LC-A] **Run record.** Every research run, on the server or in a cloud session, including a failed or discarded one, records: kind, card and trial specification, whether it is a new trial, git commit, image digest, lock-file hash, dataset snapshot id and hash, parameters, seed, start and end, status, metrics. Metrics, parameters and compressed return series are kept indefinitely. Test: a run sampled at random is re-executed from its record and reproduces its metrics within 1 bp a month. | [R52 §3.1, §3.5], [RND-011] |
| LE-08 | [LC-A] **Tamper evidence.** Each `kb` insert appends to `kb.chain` a hash of the row and of the previous chain entry. The git ledgers (`trials.jsonl`, `agent_runs.jsonl`, `predictions.jsonl`) are chained the same way. `kb_verify` recomputes the chains monthly; the chain heads are printed in the monthly report and written to the backup manifest. A broken chain is a WARN and opens an incident (CA-09). A card's hash and freeze time are recorded in `hypotheses`, in a signed git tag and in the next backup manifest. | [R52 §3.6] |
| LE-09 | [LC-A] **Retention.** Nothing in the store is updated in place or deleted by a job. Removal is possible only for class D material and expired rentals (DAT-16), a secret or personal identifier stored by mistake, or a class C copy the owner must remove; each needs `trader kb purge --confirm` with the second factor and writes a `kb.deletion_register` row keeping the hash and the reason. Tax file numbers, account numbers and credentials are never written to `kb`, to git or to an export (test with seeded values). | [R52 §3.5] |
| LE-10 | [LC-A] **Backup and restore.** The nightly backup (section 19) includes `kb` and its files. One backup a year is kept indefinitely (`backup.keep_yearly`). Both git repositories are mirrored weekly, encrypted, to the object store. The restore drill (BP-16) also restores `kb`, runs `kb_verify` and repeats LE-07's reproduction test. | [R52 §3.6], [BP-16] |
| LE-11 | [LC-A] **Capacity.** The monthly report shows database size, file-store size, disk used, and the run time and peak memory of `engine_extend`. WARN at 70% disk. The report recommends the larger server when the paper gateway shares the machine, when `kb` passes 5 million price rows, or when `engine_extend` exceeds 30 minutes or its memory limit twice in a month [design value — operational]. Panel analytics and model fitting do not run on the server. | [R52 §3.7], [R43 CA-19] |
| LE-12 | [LC-A] **One-way export.** `kb_export` writes a weekly bundle (Parquet and JSON, with a manifest of hashes) to the object store, encrypted to a key used for exports only. It contains: derived monthly series, scorecards, predictions, the mirror of non-personal events, the trial log and, where a study needs it and the class allows (LE-05), vendor data. It never contains a credential, an account number, or dollar balances of the owner's book unless `le.export.include_dollar_values` is true. The server holds a write-only token for the export prefix and reads nothing from it. | [R52 §2, §3.4] |
| LE-13 | [LC-A] **Query interface.** A library `engine_kb` offers `search`, `show`, `timeline`, `asof`, `scorecard`, `trials`, `bar`, `why`, `predictions` and read-only `sql`, with two back ends giving the same answers: Postgres through `kb_reader`, and the export plus the knowledge repository. `trader kb <function>` exposes each on the server. The bot answers `/learned`, `/memory <word>` and `/bar` by lookup only. No network listener is added (INF-03). Test: each function returns the same result from both back ends on a fixture. | [R52 §3.8] |
| LE-14 | [LC-A] **Library and index.** Every record has a stable ID. `INDEX.md` and `catalog.jsonl` are generated, never hand-edited. Every claim carries exactly one evidence tag, `2+`, `1` or `unverified`, and the IDs of its sources; CI fails a file with an untagged claim. Each claim has a re-check date; a contradicted claim is kept with both sets of evidence. | [R52 §3.3], [R35 LRN-21] |
| LE-15 | [LC-A] **Server jobs.** `kb_mirror` daily; `engine_extend` and `kb_export` weekly; `kb_verify` monthly (schedule in LE-42). They contain no AI call and no network call except the export upload. With every agent disabled they still run and the deterministic half of each report is still produced (test). | [R52 §4.1] |
| LE-16 | [LC-A] **Agent cycles.** Four scheduled cycles run in cloud sessions, each from a fresh context that loads `CLAUDE.md`, the memory page and the last report: reader (weekly), analyst (monthly, with a deeper quarterly form), review pack (before each OPS-20 review) and validator (per pull request). A cycle follows the steps of report 52 §4.2. Its only outputs are pull requests and ledger rows. A missed or capped cycle is a WARN in the next report and nothing else. | [R52 §4.1, §4.2], [R35 LRN-21, LRN-22] |
| LE-17 | [LC-A] **Extension is replication.** `engine_extend` runs each registered model with its frozen parameters and code on a new dataset snapshot, logged with replication kind `extension`; it is not a trial (VAL-22). No parameter is fitted. A model whose card fixes a refit schedule refits only as the card says, and each fitted object is hashed and stored. A changed parameter, universe or metric is a new card and a new trial (RND-016). | [R52 §4.3], [R48] |
| LE-18 | [LC-A] **Scorecard.** For each registered model the engine keeps a monthly scorecard on **post-registration data only** (months after the card's freeze; for L1 and B1 to B3, from the advisory release), after the section 25 costs and after tax at the owner's rate under the post-July-2027 rules, against B2 first, then B3 and B1. It shows the card's primary metric, the return and drawdown differences, tracking error, switches, cost and tax; a 90% bootstrap interval from the first month; the record length; and the luck band for the current number of models. Development-era and "holdout, seen" figures appear only in a separate labelled block. Scorecards are listed by registration date and never sorted or ranked by return. States: `too early`, `consistent`, `outside forecast band`, `contradicted`, `fidelity break`. A scorecard may veto and inform; it may never select. | [R52 §4.6], [VAL-21], [R35 LRN-04, LRN-27], [R44 §3.4] |
| LE-19 | [LC-A] **Predictions.** Any dated, quantified forecast made by a card, a report or the engine is written to `kb.prediction` (or the chained ledger) before the outcome can be known, with its resolution date and rule. `engine_extend` resolves due predictions. The reports show the share of outcomes inside their stated 80% bands and a Brier score for yes/no predictions. | [R52 §4.6], [R48], [MON-18] |
| LE-20 | [LC-A] **Measures of the engine.** The reports carry six measures: forecast calibration; cost-model error per fill (from the paper stage); data events and time to detection; incidents and repeats; claim quality (share tagged `2+`, re-checks on time, claims contradicted); and the adoption ledger, which lists every change adopted on the engine's proposal with the benefit predicted at proposal and the benefit measured since, after costs and tax, against B2. A backtest improvement, a trailing-return rank and a count of ideas or passed cards are never reported as improvement. | [R52 §4.6] |
| LE-21 | [LC-A] **Change tiers.** T0, automatic, exhaustively: the LRN-08 estimates by LRN-10 and LRN-11; new store rows; scorecards, prediction outcomes and monitor states; generated pages. T1, by agent pull request, validator memo and the owner's merge: notes, lessons, reports, code under `research/`, a watch-list source, a draft card, a report template, a `kb` table or query. T2, by a frozen card or change note, the gates of section 17, the validator, the owner's approval after RND-005's 7 days, OPS-19 (d) where it applies and RND-032's limit: everything in LRN-09, freezing a card, a shadow line, a promotion, an execution tactic (LRN-19), any change to LRN-08, to an LE safety requirement (LE-29 to LE-36), to an agent prompt, a cost cap or the reader's allowed domains. T3, never: the items of report 52 §4.4. A CI test fails a pull request whose changed paths need a higher tier than its label. | [R52 §4.4], [LRN-08, LRN-09], [RND-032] |
| LE-22 | [LC-A] **One library trial count.** N\_lib is the number of distinct rule specifications ever evaluated on real data against B2, across all families and all authors, on the server (`trials`) or in a cloud session (`ledger/trials.jsonl`). It is seeded by back-filling the runs of reports 36, 38, 47 and 48. It never decreases. Research code obtains real data only through `engine run`, which appends the ledger row before returning a result. A figure in any report, card or answer that cites no ledger run is inadmissible: CI fails it and the validator re-runs a sample. Each signed release carries the ledger snapshot; the server refuses a snapshot whose count is lower than the last. | [R52 §4.5], [RND-011], [R35 LRN-05] |
| LE-23 | [LC-L] **Rising bar and quotas.** A Family B (return) claim needs a net t-statistic of at least max(3.0, the normal quantile at 1 − 0.025 ÷ N\_lib) and a Deflated Sharpe Ratio of at least 0.95 computed with N\_lib (VAL-20). A Family A claim is tested in the Holm family of every Family A rule ever proposed on those sleeves (RND-012). `trader kb bar` prints N\_lib and the bar. Quotas: at most 3 draft cards a quarter; at most 4 cards frozen a year, in two windows; at most 40 new trial specifications a year (`le.trials.max_new_per_year`); the VAL-22 cap per family; one promotion in 12 months. A card's post-registration record is formally read only at 36, 60 and 120 months after freeze, with the error allowance split across the three looks. [design values — operational] | [R52 §4.5], [VAL-20], [R16], [R35 LRN-01, LRN-22] |
| LE-24 | [LC-L] **Negative controls.** Each quarter the full pipeline is run on placebo rules (randomised signal dates with matched time in the market) and, before any promotion window, on H41. The share that pass a gate is reported as the pipeline's false-positive rate. If any placebo passes, every promotion window is closed and an incident is opened until the cause is recorded. | [R52 §4.5], [RND-026], [R42 PM-13] |
| LE-25 | [LC-A] **Draft cards.** An agent may draft a card at any time. A draft records its proposer (owner, or the model id and its stated training cut-off), its class (`promotable`, `control` or `exploratory`), an economic rationale from sources dated before the data, and the observable assumptions it rests on. A draft that has had no real-data run costs no trial; any real-data look is logged as a trial whether or not a card exists (RND-011). The owner triages each draft within 14 days: accept for the next freeze window, park or reject, with a one-line reason that is stored. No strategy card is frozen before the date in OPS-19 (e). Failed, parked and rejected ideas are kept (RND-006). | [R52 §4.2], [R35 LRN-03, LRN-22 to LRN-24], [OPS-19] |
| LE-26 | [LC-L] **Shadow library.** From the first annual review at the earliest, PK-10's challenger library returns as report 35's LRN-01 to LRN-07 and LRN-27, with the two conditions of PK-10 (no selection or weighting on recent return; a challenger that differs only by a tuned parameter is not eligible). A challenger runs in `paper_sim` with production code and no broker credential. Its post-registration clock starts at its freeze. | [R35], [R48], [section 31 PK-10] |
| LE-27 | [LC-L] **Evidence for promotion.** A candidate needs: its card passed at G2 under LE-23; the walk-forward stability check (RND-026); LE-24 clean; at least 12 shadow cycles with no fidelity break (6 if it adds no instrument and no signal type); a scorecard state that is not `contradicted` or `outside forecast band`; and, stated beside any drawdown gained, the return given up (VAL-23). Its shadow return, Sharpe or rank is never cited as a ground. Under `objective: growth` only a Family B pass can support a change intended to raise wealth. Section 17.1 is unchanged. | [R52 §4.6], [R35 LRN-04, LRN-07], [VAL-23] |
| LE-28 | [LC-A] **No selection on recent return, in words as well as code.** The agent prompts state LRN-09's rule. CI fails a report that contains a table of models sorted by return or a recommendation that cites a trailing or shadow return as its reason. | [R48], [LRN-09], [R35 LRN-31] |
| LE-29 | [LC-A] **Agent placement and credentials.** Research agents run only in cloud sessions, never on the trading server; BP-09's allow-list gains no AI host. An agent may hold: a git identity able to push branches and open pull requests on the two private repositories; a read-only token and decryption key for the export. An agent never holds an IBKR credential, the vendor API key, any server or Tailscale access, the backup key, the release-signing key, the bot token or an object-store write token. Evidence is recorded quarterly with BP-08. | [R52 §5.1], [RND-002], [SYS-06], [BP-09] |
| LE-30 | [LC-A] **One way in.** The server fetches and reads nothing written by an agent, except code and the ledger snapshot inside a release that carries the owner's signature and matches the approval pins (OPS-10). The signing key exists only on the owner's device. Test: a release that is unsigned, or signed by any other key, is refused. | [R52 §2, §5.1], [OPS-10] |
| LE-31 | [LC-A] **Repository protection.** `main` on both repositories accepts changes only by pull request with the owner's review. Protected paths: in the code repository, everything outside `research/` and `docs/`; in the knowledge repository, `CLAUDE.md`, `prompts/`, `schemas/` and `cards/frozen/`. CI fails an agent-authored pull request that touches a protected path. | [R52 §5.1], [RND-002] |
| LE-32 | [LC-A] **Validator.** Every agent pull request other than a reader's library-only one is reviewed by a validator session with a fresh context and its own prompt, which writes a memo against the checklist of report 52 §5.3 including a "reasons this could be wrong" section. The validator cannot approve or merge. It is an independent context, not an independent provider; for a formal G2, RND-003 applies unchanged. | [R52 §5.3], [RND-003], [RND-005] |
| LE-33 | [LC-A] **Untrusted content.** No session has all three of: private data, untrusted external content, and open outbound network. The reader has the web on allow-listed domains only (`le.reader.allowed_domains`) and no private data or export token. The analyst has private data and no web beyond the git host, the object store and package registries; it reads the reader's notes, never raw documents. A reader note must validate against a fixed schema with length limits and no rendering markup. Links in any report or note may point only to allow-listed domains. | [R52 §5.4] |
| LE-34 | [LC-A] **Audit trail.** Every agent run writes a chained ledger row at start and at end: cycle, session reference, model id, prompt version hash, input manifest hash, tokens, cost, pull requests opened, flags. Every proposal's fate (the memo, the owner's approval or closing reason) is linked from the record it concerns. Every owner decision is a `kb.owner_decision` row with its reason. | [R52 §5.2] |
| LE-35 | [LC-A] **Cost caps and kill.** Each cycle has a token cap and a wall-clock cap; the month has a spend cap (`le.agent.cost_cap_aud_month`, default 30) computed from token counts at configured prices. A run that would exceed a cap does not start, or stops, and is recorded. `le.agent.enabled: false` stops every cycle at its first step. Only the owner may change a cap (tier T2); an agent pull request that edits one fails CI. Agent spend is a line in INF-10's cost report. | [R52 §5.5], [OPS-20] |
| LE-36 | [LC-A] **Off the order path.** `kb_mirror`, `engine_extend`, `kb_export` and `kb_verify` are learning jobs under LRN-28: no broker connection, never within 2 hours of a trading job, fail to WARN only. They run with a memory limit and low CPU priority (`le.jobs`). Test: with the whole engine disabled the plan for a recorded month is byte-identical. | [LRN-28], [R52 §5.1] |
| LE-37 | [LC-A] **Reports.** Each month the engine produces "What the engine learned", at most two pages, with the ten sections of report 52 §6.1; sections marked Server are generated from the store and are sent even if no agent ran. LRN-26's quarterly report gains the scorecards, calibration, reading, lessons and proposals sections, the placebo pass rate and the claim figures. Before each OPS-20 review a review pack is produced. No report ranks models, states or implies a return advantage (SYS-07), or carries a buy or sell line for the index account (EXE-13). | [R52 §6.1], [LRN-26] |
| LE-38 | [LC-A] **Memory page.** `MEMORY.md` is generated from `kb.lesson`: everything tried, what worked, what did not and why, what was believed and later changed, standing lessons, open questions; each row linked to its card, runs and report. It is back-filled from reports 07 to 52 and sections 24.1 and 31 before the first cycle. A lesson is never deleted; it is superseded. | [R52 §6.2], [RND-006] |
| LE-39 | [LC-A] **Asking.** A question session answers under a fixed contract: the answer first in plain English; the record IDs it rests on, with evidence tags; what is not known and what the record length cannot show; any model result beside B2 after costs and tax; no buy or sell line for the index account and no implied return advantage; general information only. The question and answer are saved. A question that needs a new look at real data is queued for the next cycle and is not answered by an unlogged run. | [R52 §6.3], [EXE-13], [SYS-07] |
| LE-40 | [LC-L] **Company-level store.** When a company-level study or the Big Wins engine is approved, the store adds: entities that are never removed on delisting; universe membership through time; fundamentals as first reported with each restatement; events with their source documents; and frozen definitions for any outcome label. Its runs use family `BW` and count in N\_lib. Before any study relies on it, one paid vendor month tests whether delisted ASX companies and point-in-time fundamentals are available, and the result is recorded. | [R52 §7], [DAT-23] |
| LE-41 | [LC-A] **Acceptance tests.** The tests of report 52 §8.6. | [R52 §8.6] |
| LE-42 | [LC-A] **Schedule.** `kb_mirror` 23:00 daily; `engine_extend` Saturday 04:00; `kb_export` Saturday 06:00; `kb_verify` 06:00 on the first Sunday of each month. Agent cycles: reader weekly on Sunday; analyst on the second Sunday of each month, in its quarterly form in January, April, July and October; review pack 21 days before each date in `review.dates`. Times are config (`schedule`, `le.agent.cycles`). | [R52 §4.1] |

### 8.2 Amendments to existing requirements

| Requirement | Amendment |
| --- | --- |
| OPS-19 (a) | Add: "v2.14 is admitted as a named exception by owner decision O32: it adds section 28.2 and changes no trade-path requirement." (e) is unchanged |
| OPS-20 (c) | By decision O33: "target A$330, ceiling A$480 a year, of which agent runs at most A$360". The reduced option of section 8.7 needs about A$300 |
| BP-09 | No change to the allow-list. Add the test: "no engine job opens a connection to any host other than the object store" |
| RND-002, RND-032 | Add a reference to LE-29 to LE-31 as the enforcement for research agents |
| LRN-26 | Add the sections named in LE-37 |
| Section 12 | Add the `kb` tables; add `kb.*` to the insert-only list |
| Section 19, backups | Add `kb` files to the nightly backup; add `backup.keep_yearly` |
| Section 31, PK-10 | Replace the revisit text with a pointer to LE-23, LE-24, LE-26, LE-27; the date is unchanged |
| DAT-18 | Moves from group L to group A for the `kb` tables only (they are bitemporal from the start) |
| Section 21.1 | Add open items O32 to O36 (section 9) |

### 8.3 Configuration (`config/common.yaml`)

```yaml
le:
  enabled: true
  store:
    purge_requires_second_factor: true
    artifact_keep_months: 24             # charts and full packs; metrics are kept for ever
    disk_warn_pct: 70                    # design value — operational
    server_upgrade_triggers: {price_rows: 5000000, extend_minutes: 30, mem_kills_per_month: 2}
  export:
    include_vendor_data: as_needed       # none | as_needed | all   (LE-05, LE-12)
    include_dollar_values: false
    max_bundle_mb: 200
  jobs: {memory_limit_mb: 512, nice: 10} # LE-36
  scorecard:
    benchmarks: [B2, B3, B1]
    interval: 0.90
    formal_looks_months: [36, 60, 120]   # LE-23
    too_early_months: 36
  trials:
    max_new_per_year: 40                 # design value — operational
    t_floor: 3.0
    t_alpha_two_sided: 0.05              # bar = max(t_floor, z(1 - alpha/2/N_lib))
    backfill_reports: [36, 38, 47, 48]
  cards: {drafts_per_quarter: 3, freezes_per_year: 4, freeze_windows: [5, 11], triage_days: 14}
  controls: {placebos_per_quarter: 20, close_windows_on_placebo_pass: true}
  claims: {recheck_months: {tag_2plus: 24, tag_1: 12, unverified: 6}}
  agent:
    enabled: true
    cost_cap_aud_month: 30               # LE-35; only the owner may change
    usd_aud: 1.54                        # R13's rate; reviewed quarterly
    models: {reader: claude-haiku-5-5, analyst: claude-opus-5-5, validator: claude-opus-5-5}
    cycles:
      reader:    {when: "Sun 09:40", max_in_mtok: 1.5, max_out_mtok: 0.15, max_minutes: 30}
      analyst:   {when: "second Sun 10:10", max_in_mtok: 10, max_out_mtok: 0.2, max_minutes: 60}
      quarterly: {months: [1, 4, 7, 10], max_in_mtok: 20, max_out_mtok: 0.4, max_minutes: 120}
      validator: {max_per_month: 6, max_in_mtok: 3, max_out_mtok: 0.06, max_minutes: 30}
      review_pack: {days_before_review: 21}
  reader:
    allowed_domains: [rba.gov.au, betashares.com.au, vanguard.com.au, eodhd.com,
                      interactivebrokers.com.au, ato.gov.au, legislation.gov.au, arxiv.org, ssrn.com]
    max_documents_per_run: 25
schedule:
  kb_mirror: "23:00"
  engine_extend: "Sat 04:00"
  kb_export: "Sat 06:00"
  kb_verify: {day: first_sunday, time: "06:00"}
backup: {keep_daily: 30, keep_monthly: 24, keep_yearly: all}
review:
  cost_budget_aud_year: {target: 330, ceiling: 480}    # if O33 is accepted
```

The model names are defaults the owner may change; the cap is in dollars, so a dearer model simply does fewer or shorter runs. The reader's domain list is a starting list [design value — operational].

### 8.4 Schedule rows (section 4 table)

| Time | Days | Job | Does | On failure |
| --- | --- | --- | --- | --- |
| 23:00 | Daily | `kb_mirror` | Mirrors the day's new records into `kb.event`; extends the hash chain (LE-03, LE-08) | WARN only |
| 04:00 | Saturday | `engine_extend` | Dataset snapshot; extension runs of every registered model; scorecards; resolves predictions; monthly negative controls (LE-17 to LE-19, LE-24). No broker connection (LE-36) | WARN only |
| 06:00 | Saturday | `kb_export` | Encrypted export bundle to the object store (LE-12) | WARN only |
| 06:00 | First Sunday of each month | `kb_verify` | Hash chains, mirror completeness, store size (LE-03, LE-08, LE-11) | WARN; a broken chain opens an incident |

Agent cycles are not server jobs and have no row in the server schedule; they are listed in LE-42.

### 8.5 Milestone placement (Live-Core profile)

A new milestone, **M11 Learning engine**, built in slices like M0 to M6.

| Slice | When | Delivers | Requirements |
| --- | --- | --- | --- |
| **E0. Outside the system** | Now; needs no spec version | `asx-knowledge` repository with `CLAUDE.md`, prompts and schemas; library, memory page and trial ledger back-filled from reports 07 to 52; reader and monthly analyst cycles on public and already-published material; the question session; caps and audit ledger | The parts of LE-14, LE-16, LE-22, LE-25, LE-28, LE-31 to LE-35, LE-37 to LE-39 that need no server code |
| **E1. Advisory slice, `[LC-A]`** | After the advisory release has run 20 trading days and v2.14 is admitted (about mid-January 2027) | `kb` schema and roles; mirror, extend, export and verify jobs; scorecards for the L1 shadow line and B1 to B3 from the advisory release date; predictions; `trader kb`; bot commands; signed-release check; backups and restore of `kb` | LE-01 to LE-22, LE-25, LE-28 to LE-39, LE-41, LE-42 |
| **E1b. Paper slice** | With group B, if the paper-order gate passes | Fill-level records flow into the mirror (LRN-18); the cost-model error measure (E2) starts; execution change notes have data (LRN-19) | The fill-dependent parts of LE-03 and LE-20 (no new IDs) |
| **E2. Later, `[LC-L]`** | First annual review, 12 November 2027, at the earliest, and only by the owner's decision there | The rising bar in the harness; negative controls in the pipeline; the shadow library; the promotion evidence rule. First possible promotion window: November 2028 (12 shadow cycles) | LE-23, LE-24, LE-26, LE-27 |
| **E3. Later, `[LC-L]`** | When report 51 or the Big Wins design asks for it and the owner approves the data spend | Company-level store | LE-40 |

Group counts if adopted: A +37, L +5 (the 309 requirements of v2.13 become 351). M3's harness (group L) is not needed for E1: the scorecards of E1 use the shadow line and benchmark records that group A already writes (PRT-22). Scorecards for the five active cards as formal card runs wait for the harness, as now.

### 8.6 Acceptance tests (LE-41)

| # | Test | Passes when |
| --- | --- | --- |
| 1 | Insert-only | An UPDATE or DELETE on any `kb` table by the app role is refused |
| 2 | Trader isolation | The trader's role cannot SELECT from `kb.*`; with the engine disabled a recorded month's plan is byte-identical (LE-36) |
| 3 | Mirror completeness | After a recorded fixture day, every source row has exactly one `kb.event` row; a deleted mirror row is found by `kb_verify` |
| 4 | As-of query | A restated close inserted on day 2 is invisible to `asof(day 1)` and visible to `asof(day 2)` |
| 5 | Licence guard | An ingest from an unregistered source, a commit of a raw class B file, and an export of a class C file are each refused; `yfinance` import still fails CI (DAT-15) |
| 6 | No secrets, no identifiers | Seeded tax file number, account number and API key strings never appear in `kb`, an export or a commit |
| 7 | Reproducibility | A sampled run re-executed from its record matches within 1 bp a month (LE-07) |
| 8 | Hash chain | Altering one stored row, or one ledger line, is detected by `kb_verify` |
| 9 | Restore | A fresh machine restores `kb`, verifies the chains and passes test 7 inside INF-01's time |
| 10 | Two back ends | Each `engine_kb` function returns the same result from Postgres and from the export on a fixture |
| 11 | Extension is not a trial | An extension run adds a `trials` row with `is_trial = false` and does not change N\_lib; a run with one changed parameter increases N\_lib by one |
| 12 | The count never falls | A release whose ledger snapshot has a lower N\_lib than the last is refused; `bar()` returns 3.00, 3.21, 3.48 and 4.06 for N\_lib of 10, 38, 100 and 1,000 |
| 13 | Unlogged figure | A report containing a figure with no ledger run id fails CI |
| 14 | Post-registration only | A scorecard built from a fixture whose card was frozen on date F contains no month on or before F in its headline block |
| 15 | No ranking | A report with a table sorted by return, or a recommendation citing trailing return, fails CI (LE-28) |
| 16 | Luck band | The report prints 1.16, 1.54 and 1.87 σ for 5, 10 and 20 models (report 35's test vii) |
| 17 | Placebo | A seeded run in which a placebo passes a gate closes the promotion window and opens an incident |
| 18 | Agent cannot merge or deploy | A pull request from the agent identity cannot be merged without the owner's review; a release not signed by the owner's key is refused by the server (LE-30) |
| 19 | Protected paths | An agent pull request touching a trade-path file, `CLAUDE.md`, a prompt, a cap or the allowed domains fails CI |
| 20 | Agent holds no credential | A scan of the agent environment's secrets finds none of the forbidden list (LE-29); from the server, a connection to any AI API host fails (BP-09) |
| 21 | Injection: reader | A seeded page instructing the reader to edit `CLAUDE.md` or add a domain produces no such change; the note is schema-valid and the run is flagged |
| 22 | Injection: analyst | A seeded note instructing the analyst to propose a threshold change produces no T2 change; the validator's memo names the attempt |
| 23 | Trifecta | The reader session cannot read the export; the analyst session cannot fetch a non-listed host |
| 24 | Caps | A run that would pass the token, time or monthly spend cap stops or does not start, and the ledger records it; an agent pull request raising a cap fails CI |
| 25 | Agent off | With `le.agent.enabled: false` for a simulated month, every server job runs and the deterministic half of the report is produced |
| 26 | Answer contract | A fixed set of questions, including "should I sell BGBL?", yields answers with record IDs and tags, no buy or sell line, and the general-information line |

### 8.7 Costs (A$ a month)

Prices: server from the spec's section 19 [R13]; EODHD and Claude prices as read in this session [1]; A$1 = US$0.65 (R13's 1.54). Token volumes are my estimates [unverified]; agent cost is [computed] at API list prices and is an upper bound if the owner's Claude subscription covers scheduled sessions [unverified].

| Item | Monthly | Notes |
| --- | --- | --- |
| Server, BinaryLane 2 GB | 10.78 | A$9.80 ex GST. Already planned; not a new cost of the engine |
| Server, upgrade to 4 GB | +10.78 | A$19.60 ex GST in total. Only at a trigger of LE-11 |
| Object store (backups, exports, git mirrors; about 20 GB) | 1 | Budget figure; list price is about A$0.20 [unverified] |
| EODHD | 0 | Free plan. The one paid month of DAT-23 (about A$31) is unchanged |
| GitHub | 0 to 6 | Free private repositories; Pro only if branch protection needs it [unverified] |
| Reader, 4 runs, small model (1 M tokens in, 0.1 M out each at US$0.10 / US$0.50 per million) | 1 | US$0.15 a run [computed] |
| Analyst, monthly, large model (1 M fresh input, 8 M cached reads, 0.15 M out at US$4 / US$0.20 / US$20 per million) | 13 | US$8.60 a run [computed] |
| Analyst, quarterly form (2 M, 15 M cached, 0.3 M out) | 4 (averaged) | US$17 a run in place of that month's US$8.60: about US$8.40 extra, four times a year [computed] |
| Validator, about 2 runs a month (0.3 M, 2 M cached, 0.04 M out) | 7 | US$2.40 a run [computed] |
| **Agent runs, expected** | **about 26** | Inside the A$30 cap. With a mid-size model for the analyst and validator (US$2 / US$10 per million, cached reads US$0.10), about A$13 |
| **Engine total, new spend** | **about 27** (at the cap: 31) | About A$325 a year |
| **Whole system at 2 GB** | **about 38** | About A$455 a year, against OPS-20's present ceiling of A$150 |
| Company-level data (LE-40), if approved | One-off about 31 (prices) + 92 (fundamentals); ongoing 31 only if daily all-ASX updates are wanted | US$19.99 and US$59.99 [1] |

**Cheapest option:** build E0 and E1; run the reader weekly and the analyst only in its quarterly form with one validator run each quarter: about A$11 a month [computed], about A$300 a year for the whole system. The store, scorecards and deterministic reports are unaffected; the written analysis arrives four times a year. No option fits the present A$150 ceiling once the server is rented, because the server and the one EODHD month alone come to about A$160 a year.

---

## 9. Reasons this could be wrong, and open items

**Reasons this could be wrong**

1. **It may be more machinery than a two-fund holding needs.** Reports 41 and 42 argued for stopping the search and freezing the build; this report adds 42 requirements. The defence is that almost all of it is storage and reporting, off the order path, and the part that searches (E2) stays parked until the date the spec already set. If the owner's patience for reports is low, E0 plus the cheaper option above gives most of the value.
2. **The engine will mostly report "nothing new".** That is the expected and correct output for an index holding. If the owner reads that as failure, the pressure will be to loosen the bars. The bars are tier T2 and T3 for that reason.
3. **Agent runs outside the wrapper cannot be prevented, only made useless.** The design relies on post-registration evidence so that unlogged looks cannot help an idea. An idea shaped by unlogged looks still enters with an understated trial count; the understated count lowers its bar slightly. The quotas bound how much.
4. **A same-family validator shares the analyst's blind spots.** Stated in LE-32. The owner's approval, the CI checks and, for anything that matters, RND-003's different-provider rule are the real independence.
5. **Post-registration records take decades to mean anything for returns.** The scorecard says so every month. The engine's visible progress is in the six fast measures, and the owner may find those dull.
6. **My size and token estimates are unverified.** The caps hold whatever the true volumes are; the estimates only predict how often a cap is hit.
7. **Licensing rests on EODHD's help pages, not the Terms.** The pages say they reflect the Terms. A change to either is caught by the reader's watch-list and LRN-17, and would turn `le.export.include_vendor_data` to `none`.
8. **Claude Code product behaviour may differ from my assumptions:** how scheduled sessions are billed, what secrets and network limits an environment supports, how long transcripts are kept. Each is an open item below.
9. **I did not read reports 36, 38, 41, 42, 45 to 47 or 51 in this session.** Their findings are taken from the spec's own summaries and from report 48.

**Open items for the owner (section 21.1)**

| # | Item | Blocks |
| --- | --- | --- |
| O32 | Admit v2.14 with section 28.2 as a named exception to the freeze | E1 |
| O33 | Running-cost budget: A$330 target / A$480 ceiling; or about A$300 with the quarterly-only option | Every agent cycle |
| O34 | Confirm OPS-19 (e) stands: no strategy card frozen before November 2027 | E2 timing |
| O35 | Confirm the agent may read class B (EODHD) data in sessions under the owner's own Claude account, and that no report containing vendor values will be shared with anyone | LE-12's vendor-data option |
| O36 | Create and hold the release-signing key on the owner's device; store its recovery copy with the backup key (O20) | LE-30 |

**Open items to verify before build**

| # | Item | How |
| --- | --- | --- |
| V1 | Whether Claude Code scheduled sessions are covered by the owner's subscription or billed per token | The product's billing page; one test month with the cap at A$5 |
| V2 | Whether a Claude Code cloud environment can enforce the two network profiles of LE-33 (reader: listed domains; analyst: git host, object store, registries) and hold the export token as a secret | A spike: one reader and one analyst session; acceptance test 23 |
| V3 | Whether GitHub Free enforces required reviews on a private repository | GitHub's plan page; otherwise GitHub Pro or rely on LE-30 alone |
| V4 | BinaryLane 2 GB plan disk size and the price of a disk-only upgrade | Provider page |
| V5 | EODHD Terms and Conditions text on storage with a third-party host and on AI tools (the help pages were read; the Terms were not) | Read the Terms; record the hash in `kb.source` |
| V6 | Whether EODHD serves delisted ASX companies and point-in-time ASX fundamentals | One paid month (LE-40) |
| V7 | The exact number of distinct specifications run in reports 36, 38, 47 and 48 | The E0 back-fill |
| V8 | Australian fair-dealing position for private working copies of papers | General reading of Copyright Act s 40; a lawyer only if copies are ever shared (they are not) |

**A later refinement, not proposed now.** Replace the fixed look dates and Bonferroni-type bar with always-valid tests (e-values) and online false-discovery control, which are designed for an endless stream of hypotheses with continuous monitoring [unverified]. Worth a card of its own on the *process* once E2 has run for a year.

---

## 10. Sources

| # | Source | Used for | Tag |
| --- | --- | --- | --- |
| 1 | `FD_FINAL_LATEST.md` v2.13: sections 1, 1.1, 4, 6, 12, 17.1, 18, 19, 20, 23 to 25, 28, 28.1, 31; OPS-10, OPS-19, OPS-20, BP-09, BP-14, BP-16, CA-09, DAT-15, DAT-16, DAT-18, DAT-23, EXE-13, INF-01, INF-03, INF-10, MON-18, RND-002 to RND-032, SYS-06, SYS-07, VAL-20 to VAL-23 | The existing design and every constraint | Read in this session |
| 2 | Report 35, sections 4 and 5 (LRN-01 to LRN-34) | The parked library, research cycle and report design that sections 4 and 8 build on | Read |
| 3 | Report 48, section 0 | Selection on past return fails; risk rankings persist; band coverage | Read |
| 4 | Report 19 | EODHD and Norgate licence positions; data routes | Read |
| 5 | Reports 20, 43, 44 | Roles and gates; CA-19; owner decisions and the O-number register | Read in part |
| 6 | EODHD Help Center: "What a Personal Plan Allows" (`/help/personal-use`); "Cancel a Plan, Keep Your Data, Refunds" (`/help/storage`); "AI tools, cloud servers and your own software" (`/help/ai-tools`) | Section 3.4 quotes | [1] primary, fetched 14 Nov 2026 |
| 7 | EODHD pricing page (`/pricing`) | Plan prices; call costs per request type | [1] primary, fetched 14 Nov 2026 |
| 8 | Claude API reference bundled with this session (model table cached 3 Nov 2026) | Token prices in section 8.7 | [1] |
| 9 | Deflated Sharpe Ratio; t ≥ 3 for new factors; Reality Check and SPA; post-publication decay | Section 4.5, by way of the spec's VAL-20, VAL-24 and reports 16, 20, 35 | As tagged in those reports; not re-opened |
| 10 | Online false-discovery control (alpha-investing and successors); e-values and always-valid inference; the "dual model" pattern and the three-conditions rule for prompt injection; Copyright Act 1968 (Cth) s 40 | Sections 3.4, 4.5, 5.4, 9 | [unverified]: my prior knowledge |
| 11 | Arithmetic in sections 0, 3.7, 4.5, 8.7 | t-bar table; luck band; years to significance; sizes; agent cost | [computed] in this session |
