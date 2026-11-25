# Amendment: NEWS-C, an AI reading of price-sensitive announcements in band C (information only)

**Status: DRAFT, 25 Nov 2026. Not registered.** The owner registers it by hashing it (SHA-256) and appending it to `LEDGER.jsonl`
before the first rating, which falls on Tue 1 Dec 2026 for the announcements of Mon 30 Nov 2026. `newsc_record.py` refuses to
record anything until this file's name is in the ledger as an amendment.

**Basis:**
- Design review `review_news/REVIEW.md` (24 Nov 2026), verdict "build with changes". This amendment implements its draft spec
  "NEWS-C", with the changes stated in s10.
- Owner decision of 25 Nov 2026 (ledger seq 103), which widens the private ASX archive exception of seq 96.

**PAPER / INFORMATION ONLY.**
- NEWS-C feeds no paper line, no live trade and no strategy, and it changes no line.
- It is **never evidence for or against EMG2** or any other line.
- No real money and no broker orders. The AI never places trades.
- A reading that passes its bar earns only a separately pre-registered proposal, judged at the luck bar and under the line cap.
  It never changes anything automatically.
- The main line (EMG2-18 + band-trend shield + C6) stays frozen to 1 Jan 2027 (seq 88). This amendment changes no rule,
  parameter, code path, state or reading of any registered line.

**Line cap.** Ledger seq 96 (`AMENDMENT_retirement_jan2027.md` s4) allows no new paper line before the December 2028 review
unless one is retired, and **excludes information-only archives that feed no line** from that cap. NEWS-C is an information-only
reading of the archive and feeds no line. It is therefore outside the cap. No line is retired for it.

**Trial count.**
- No back-test is run, and registering NEWS-C adds no trial: it is a blind reading of data that does not exist yet.
- The number of trials is unchanged (N 3,172 at seq 102).

## 1. Universe

- **Codes.** The codes in `bigwins_forward/data/estimates_pit/bandC_universe.json` (band C: traded-value ranks 301–600) as they
  stand when the archive runs for the list-day. The archive copies the list into `asx_notices/<day>/ps_state.json`. The month-end
  rewrite of that file takes effect from the next list-day archived after it.
- **Announcements.** Those on the ASX previous-day list (`prevBusDayAnns.do`) with `price_sensitive = 1`, plus any headline that
  matches the halt or suspension list (`newsc_baselines.HALT_START` / `SUSP_START`).
- **Paper-line holdings.**
  - These are the codes in `paper/holdings_latest.csv`, plus the `holdings` of the paper books in
    `bigwins_forward/out/paper_state/*state.json`.
  - Random portfolios and twins are not holdings.
  - Holdings outside band C are rated and **reported separately, never in a bar** (group `H` in the manifest; group `C` = band C).
  - The holdings list is used only to choose which PDFs to download. It is never given to the rater.

## 2. Inputs and arms

**Archive (`info_archive.py` item 4, owner decision seq 103).**
- The archive downloads the PDFs of the price-sensitive announcements of band-C companies and paper-line holdings, from the
  previous-day list only.
- At most **60 a list-day**. Download attempts are counted, failures included, across re-runs.
- Order: holdings first, then band C, each by announcement time.
- One request every 2 seconds.
- **Never inside 10:00–16:12 Sydney on weekdays**: the step pauses, and a later run resumes it.
- Each PDF is written as `.part`, then renamed. Its text comes from `pdftotext -layout`.
- A PDF already stored by the director-interest / capital-raising step is reused, with no request.
- The step stops if free disk is under 1 GB.
- Private, personal use. Never shared.
- Run at about **08:30 Sydney** on trading days. At that time `prevBusDayAnns.do` shows the previous trading day. An evening
  re-run of the same list-day finds `DONE` and `DONE_PS`, reads only the list page, and writes nothing.
- Items 1–3 of the archive are unchanged (the old file is kept as `info_archive_pre_newsc.py`, SHA-256 in s12).

**Unit.** The **code-day**: one company on one announcement day.

**Arm H (headlines).** The code, the announcement day, and for each announcement its time and headline.

**Arm F (full text).** As arm H, plus each announcement's extracted text:
- whitespace compressed;
- cut to the **first 30,000 characters**, with a flag if it was cut;
- `text_available: false` when no text exists (cap reached, download failed, scanned PDF, or a non-price-sensitive halt
  headline).

**Blinding.** The rater receives **nothing else**:
- no prices, returns, volumes, holdings flags, groups, ranks, baseline values or earlier ratings;
- no date other than the announcement day.

The code is kept, as the spec's arm H specifies. The announcement type is **not** given: the ASX list carries none, and the KEY
type is the baseline the AI is measured against (s7, "Added value"). The rater assigns its own type.

**Files (`newsc_prepare.py`).** `newsc/<day>/` holds:
- `input.jsonl` (all items, both arms, canonical) and `input.sha256`;
- `batches/<arm>_<nn>.jsonl`, and its plain-text rendering `.txt` (lines of at most 500 characters), which is the file the rater
  reads. Arms H and F are never in the same batch;
- `manifest.json`: groups, the band-C list, the hash of each announcement's full text, archive statuses and KEY per
  announcement. It is never given to the rater;
- `baselines.jsonl`.

Preparation is deterministic. A re-run that would change the input is refused.

## 3. Rater

**Rubric and prompt.** Frozen in `bigwins_forward/data/newsc/RUBRIC_v1.md`,
**SHA-256 `ed23cd805e4fd6b2d8483ba61e3b3e5cee829432dd418394d228527aa93ed680`**. `newsc_record.py` refuses any day if the file
hashes otherwise.

**Scale −2…+2**, as in the spec:

| Rating | Meaning |
|---|---|
| +2 | A concrete, quantified event that plausibly changes value by 20% or more (binding funded contract, resource well above prior, approval, cash takeover). |
| +1 | Concrete good news of smaller size. |
| 0 | Routine, procedural, promotional or unquantified. |
| −1 | Concrete bad news, or a discounted raising. |
| −2 | Survival in doubt: under two quarters of cash; a raising at a discount above 20% or of more than 25% of shares; covenant breach; suspension; failed trial; auditor doubt. |

- Adjectives in headlines count for nothing.
- There is **no separate wreck flag**: −2 is the wreck warning, as in the spec.
- The rater also gives one of 14 fixed types, and a reason of at most 20 words.

**Isolation.**
- Each batch is rated by a fresh Claude Code subagent, started by the scheduled morning task.
- Its prompt names only the rubric and the batch file. It may use only the Read tool, and only on those two files.
- The task holding prices and holdings never rates.
- Batches hold at most 60,000 characters of items, and an item is never split. This replaces the spec's one call per
  announcement (s10).

**Two independent ratings.** Each batch is rated twice (pass 1 and pass 2) by separate fresh subagents that see neither each
other nor any other context.
- Disagreement is recorded.
- The rating nearer 0 is kept. Equal distance with opposite signs gives 0.
- The code-day rating is the kept rating furthest from 0. A tie between signs gives 0.

**Model.**
- Each day's ledger entry records:
  - the model ID reported by the claude-code-remote `get_session` tool (`session_context.model` and
    `external_metadata.last_served_model` of the task session);
  - the subagent's model setting;
  - each rater's own `model_self_report`.
- Sampling is Claude Code's default; the temperature cannot be set.
- **A change of the recorded model is a new stratum.** `newsc_record.py` flags it, and the owner registers it with a ledger entry.
  The spec's 20 sessions of double rating are met automatically, since every day is double-rated.
- **History is never re-rated for scoring**, by this or any later model.

## 4. Baselines (no AI; `newsc_baselines.py`)

These are computed by script from the archive's `list.csv` files and the stored notice texts, and stored with each day's record
(`baselines.jsonl`, hashed in the ledger).

**KEY.** Frozen regular expressions on the headline give one of the 14 types and a rating from −2 to +2:
- −2: suspension, administration, receivership, going concern, covenant breach;
- +2: takeover offer or scheme;
- −1: any capital raising, trading halt, downgrade, impairment, termination;
- +1: contract, approval, high-grade, record and similar;
- else 0.

The KEY code-day uses the same "furthest from 0" rule as the AI.

**RAISE.** A capital-raising notice for the code on any of the trailing 63 archived list-days (including the day). It counts
when either:
- the headline is a placement, entitlement, SPP, capital raising, cleansing notice, prospectus and similar; or
- an Appendix 3B "Proposed issue of securities" text shows a cash consideration, an SPP or a pro rata offer.

The issue price is kept when stated. The archive began on 23 Nov 2026, so the 63-day window is complete only from about
February 2027 (`window_complete`).

**HALT.** A halt, pause or suspension, tracked to reinstatement:
- a trading halt ends at the code's next price-sensitive non-halt announcement, or after 2 list-days;
- a suspension ends only at a reinstatement notice.

**DIR.** An on-market director purchase in the "Nature of change" of an Appendix 3Y text, with the form's own example text
removed. Recorded for the day and for the trailing 63 list-days.

## 5. Recording

**Daily morning task** (exact steps in `bigwins_forward/code/README_NEWSC.md`), before 10:00 Sydney:
1. Run the archive.
2. Prepare.
3. Rate: two fresh rater subagents per batch.
4. Record.
5. Report failures only.

**Recording (`newsc_record.py`).**
- It validates each reply:
  - JSON schema;
  - every announcement exactly once;
  - an integer rating from −2 to 2;
  - one of the 14 types;
  - a reason of 1–20 words;
  - the batch hash, the pass and the rubric identifier echoed back.
- It checks `input.jsonl` against `input.sha256` and the manifest, and each batch and its rendering against the manifest.
- It refuses if any check fails, or if the day is already recorded.
- It writes:
  - `rater/` (the replies, verbatim);
  - `ratings.jsonl` (per announcement and arm, both passes and the kept rating);
  - `codeday.jsonl` (both arms, joined with the baselines).
- It appends **one ledger entry per day**, kind `info_news`, through `fwd_ledger.py`, with:
  - hashes of the list, ps_state, input, manifest, batches and renderings, rater replies, ratings, code-days, baselines,
    rubric and code;
  - the model fields of s3;
  - counts, failures, a provisional on-time flag and the Sydney time.
- One schema-failed reply may be replaced once by a fresh rater call. The rejection is reported. Ratings are never replaced for
  their content.

**Missed days.** A day recorded after the open of the first session after the announcement day is **LATE**: flagged, and
excluded from every bar.

**Backup.** The archive (`bigwins_forward/data/asx_notices`) and `bigwins_forward/data/newsc` are to be added to the nightly
backup (`backup_paper_record.sh`). This is open; see s11.

## 6. Measurement (`newsc_score.py`, computed later)

**Entry.** The close of the first ASX session that **opens (10:00 Sydney) after the day's ledger timestamp** and in which the
share trades (a close, with volume above 0). A halted share therefore enters at reinstatement.

**Return.**
- Raw close to raw close, as EST-C: dividends and confirmed `CORPORATE_ACTIONS.csv` values as cash, not reinvested; splits
  applied to the share count; a share that stops trading keeps its last close plus cash.
- Prices come from the paper record's bulk files (`paper_lib.load_day`).

**Excess return.** The return minus the equal-weight return of the day's band-C list over the same sessions. Each band-C code
with a close at the entry session is tracked the same way.

**"Already in the price".** The move from the close before the announcement day to the entry close. It is reported and is
**never an outcome**.

## 7. Readings and bars (wording fixed now)

All bars use group C code-days that are not late. Arm F is primary. If arm F is ever refused, arm H takes its place.

**Primary (drift).**
- For each announcement month from December 2026 to November 2027 (12 months), the measure is the mean 20-session excess return
  of +2 code-days minus that of −2 code-days.
- A month needs at least 3 code-days on each side; otherwise it is missing, not filled.
- Read in **January 2028**. "**Present**" if and only if all three hold:
  - t = mean ÷ (sd ÷ √n) ≥ 2.0 over the monthly measures;
  - the mean of the first half (Dec–May) > 0;
  - the mean of the second half (Jun–Nov) > 0.
- With fewer than 6 monthly measures, the result is "not readable".

**Secondary A (wrecks).**
- Outcome: a **raw** 252-session return of −50% or worse.
- Compares −2 code-days with 0-rated code-days in the same cohort month, December 2026 to November 2028 (24 cohorts).
- Estimate: the coefficient of the −2 indicator, with cohort-month fixed effects. Standard errors are two-way clustered by
  company and month.
- Read in **December 2029**. "Present" if and only if t ≥ 2.0.

**Secondary B (winners).** The same as A, for +2 against 0 code-days, with an outcome of a raw 252-session return of +40% or
better.

**Added value.**
- Each reading is repeated within KEY type, with fixed effects for month × KEY code-day type, and the same clustering.
- The AI "adds" only if the within-type estimate keeps the sign of the reading with t ≥ 1.5.

**Baselines,** read the same way:
- KEY with its own rating: +2 against −2 drift; −2 against 0 for wrecks; +2 against 0 for winners;
- RAISE, HALT and DIR as flag against no flag, with expected signs −, − and +, over every group-C code-day in `baselines.jsonl`.

**Benjamini–Hochberg at 10%** across the information family: EST-C, DIL-C (their own registered readings, as one-sided
p-values) and every reading above that exists at the reading date.

**Descriptive tables.** At each December review there are descriptive tables with no bar: counts by month and rating, the "already
in the price" move, holdings outside band C, and model strata. **No other cut is evidence.**

## 8. Owner screens

Monthly counts only. **No per-share ratings** anywhere the owner looks, including failure reports.

## 9. Dates

- **First ratings:** Tue 1 Dec 2026, for the announcements of Mon 30 Nov 2026. That day falls outside the primary months and is
  descriptive only.
- **First honest readings:**
  - **January 2028:** drift (primary).
  - **December 2029:** wrecks and winners (secondaries A and B).

## 10. Changes from the review's draft spec, stated so

1. **Rater calls.** The rater is a Claude Code subagent of the scheduled task, not a direct API call with an explicit dated model
   ID. Calls are per batch (at most 60,000 characters of items), not per announcement.
2. **File names.** The ratings file is `newsc/<day>/ratings.jsonl` (plus `codeday.jsonl`), not `news_c/ratings_<day>.csv`. The
   per-text SHA-256 values are kept in `manifest.json`, which the ledger hashes.
3. **Clarifications** the spec left open:
   - the month of a code-day is its announcement month;
   - at least 3 code-days a side for a monthly measure, and at least 6 measures for a primary reading;
   - the halves are Dec–May and Jun–Nov;
   - the wreck and winner thresholds apply to the raw return, not the excess return;
   - secondaries use cohort fixed effects, and added value uses month × KEY-type fixed effects.

## 11. Limits

**Model pinning.**
- The subagent runs on the task session's model unless a rater agent definition sets one. A `model:` alias (for example `opus`)
  is not a pin.
- `get_session` reports the **session's** model, not the subagent's. The rater's own self-report is recorded but cannot be
  verified.
- Exact pinning to a dated model ID is therefore **not guaranteed**. What is known is recorded every day, and a change is
  flagged and becomes a new stratum.
- The pinned model will be retired inside the three-year study.

**Isolation.**
- Isolation depends on the subagent's prompt and on restricting it to the Read tool. A subagent could in principle read other
  files.
- The recommended agent definition with `tools: Read` reduces this risk but does not remove it.

**Batching.** Several announcements share a rater call, so a rating may be influenced by its neighbours. The rubric says to rate
each one alone.

**Text.**
- Scanned PDFs have no extractable text.
- More than 60 qualifying announcements on a heavy day (quarterly-report season) leaves the excess with headline-only text in
  arm F.

**Storage.**
- Price-sensitive PDFs are larger than the notices: presentations and reports run to several MB, so roughly 50–200 MB a heavy
  day.
- The archive sits in a scratch folder that is not backed up yet. A lost PDF makes its rating unauditable.

**ASX terms.** The terms question in `review_approach/REVIEW.md` is still open. The practical risk is being blocked.

**KEY is crude by design.** It is a dumb checklist and is frozen with this amendment.

**Power** (review issue 2):
- Only a one-month drift above about 4 points shows in year one.
- Wrecks need about 3 years.
- The prior for a usable winner signal is about 1 in 10, and for a wreck flag about 1 in 4.

## 12. Files (SHA-256 at drafting; the registering entry records the hashes of the installed files)

| File | SHA-256 |
|---|---|
| `bigwins_forward/data/newsc/RUBRIC_v1.md` | `ed23cd805e4fd6b2d8483ba61e3b3e5cee829432dd418394d228527aa93ed680` |
__CODE_TABLE__

**Statement.** Information only. NEWS-C feeds no paper line and no trade. It is never evidence for or against EMG2. It changes no
line.
