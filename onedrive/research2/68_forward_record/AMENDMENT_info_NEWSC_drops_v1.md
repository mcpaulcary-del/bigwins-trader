# Amendment: NEWS-C big-drop + cause log (information only)

**Status: DRAFT, 25 Nov 2026. Not registered.** The owner registers it by hashing it (SHA-256) and appending it to `LEDGER.jsonl`
before the first record, which falls on Tue 1 Dec 2026 (before 16:00 Sydney) for the ASX session of Mon 30 Nov 2026.
`newsc_drops_record.py` refuses to record anything until this file's name is in the ledger as an amendment.

**Basis:**
- `research_dip/REPORT.md` s10 (ledger seq 109): "I recommend [NEWS-C] logs 'big drop + cause' forward, as information only."
  The vendor's ASX news could not support a historical cause test; NEWS-C reads the ASX announcements directly.
- NEWS-C itself: `AMENDMENT_info_NEWSC_v1.md` (ledger seq 106). Owner approval of this log: 25 Nov 2026.

**PAPER / INFORMATION ONLY.**
- The log feeds no paper line, no live trade and no strategy, and it changes no line.
- It is **never evidence for or against EMG2** or any other line.
- No real money and no broker orders. The AI never places trades.
- A reading that passes its bar earns **at most a separately pre-registered paper-line proposal**, judged at the luck bar and
  under the line cap. It never changes anything automatically.
- The main line (EMG2-18 + band-trend shield + C6) stays frozen to 1 Jan 2027 (seq 88). This amendment changes no rule,
  parameter, code path, state or reading of any registered line, and no rule or reading of NEWS-C v1 (s7 below).

**Line cap.** Ledger seq 96 (`AMENDMENT_retirement_jan2027.md` s4) excludes information-only archives that feed no line from the
cap. This log is an information-only reading of the archive and the paper bulk files and feeds no line. It is therefore outside
the cap. No line is retired for it.

**Trial count.** No back-test is run, and registering the log adds no trial: it is a blind forward record of data that does not
exist yet. The research_dip trials are already counted (seq 109, N 3,285). The count is unchanged.

## 1. Scope (owner decisions seq 96 and seq 103)

- **No new download of any kind.** `newsc_drops.py` makes no network request. It reads:
  - the day's ASX previous-day list (`asx_notices/<day>/list.csv`), which the archive already stores for **every** company
    (seq 96, item 1);
  - PDF text **already stored** by the archive: director-interest and capital-raising notices (seq 96, item 2, any company) and
    price-sensitive PDFs of band C and paper-line holdings (seq 103, item 4, at most 60 a day);
  - the paper record's daily bulk price files (`bigwins_forward/data/bulk/<day>/`) and paper decision files.
- The log covers ASX top-100 companies. **Outside band C and the holdings, only headlines are used**, because no other PDF is
  downloaded. The 60-a-day cap and the order of seq 103 are unchanged; the archive is not changed.
- Private, personal use. Never shared.

## 2. Events (research_dip `PREREG.md` s2, "D1", applied forward; `newsc_drops.py`)

**Pool on session D.** The project's point-in-time traded-value ranking: the `rows` of the latest paper decision file
(`out/paper_state/decisions/decision_<asof>.json`, `bw13_prep`: 252-session median traded value, at least 200 traded sessions,
Common Stock, ETPs out) with asof **strictly before** D; traded-value rank 1–100 and that table's close at least A$1.

**Event.** On session D a pool member's one-day total return minus the ASX 200 total return is **−10 points or worse**, and
its raw close on the session before D is at least A$1.
- Total return = (split ratio × (close + cash distribution)) ÷ previous close, from `paper_lib.load_day` (raw closes, AUD
  distributions, confirmed `CORPORATE_ACTIONS.csv` cash, vendor split ratios). The index is A200.AU, measured the same way.
- Both closes must be on the two adjacent ASX sessions (a share with no close on either day has no event).
- **Excluded:** days on which the total-return ratio and the raw-close ratio differ by more than 12% in log (split, spin-off or
  capital return). A one-day total return below −95% or above +1,000% is treated as missing (research_dip `load_asx`).
- **Re-fire:** a company cannot fire again within 20 sessions of its previous event (t − t_last ≤ 20: no event). A blocked day
  does not restart the count. The chain runs over every ASX session from 18 Nov 2026 (the first session with two bulk files),
  recomputed from the bulk files each day; a difference from an earlier day's `drops.jsonl` is reported as a failure.
- Market-wide falls do not create events by themselves.
- A day is refused when its list, its bulk files, the index close or a decision file is missing, or when fewer than 90 pool
  members have a close.

## 3. Cause (frozen classifiers)

**News of an event.** The company's headlines in the list of D (all) and in the list of D−1 filed at or after 16:00 Sydney
(late-filed). "Focused" headlines = price-sensitive ones plus trading-halt and suspension headlines (the NEWS-C universe rule),
de-duplicated on the first 60 lower-case characters as research_dip.

**PRIMARY: keyword classifier.** `newsc_drops_classify.py` is `research_dip/code/classify.py` copied byte for byte
(**SHA-256 `b7c98fbde718f3c4c5176ea205a2f56416820d95ba296f78d87980626cb2c4cc`**, PREREG s4a rules), applied to the focused
headlines:
- NONE if there is none → **no-news**;
- FUND if nF ≥ 1 and nF ≥ 0.25 nT and (nF ≥ 2 or n < 8) → **fundamental**;
- else TEMP if nT ≥ 1 → **temporary / fixable**;
- else OTHER → **other-news**.
- The sub-cause (T_EARN … F_BAN) with most headlines inside the winning class is recorded.

`newsc_drops.py` refuses to run, and `newsc_drops_record.py` to record, if the copy hashes otherwise. Its parity with
research_dip was tested on research_dip's saved sample: 732 events, 5,355 focused titles, labels identical to
`research_dip/data/keyword_labels.csv` in 732 of 732.

**SECONDARY: blinded rater.** The research_dip s4b rubric for the same categories, frozen in
`bigwins_forward/data/newsc/DROPS_RUBRIC_v1.md`, **SHA-256 `dbb9cef411e06882cd405df70c19dcad8f13df7d4da717ea474bcbf41f2a1ddc`**.
- Labels: T (temporary / fixable), F (fundamental), U (unclear / unrelated), with a fixed sub-cause list. An event with no
  headline at all is labelled N (no news) without a rater.
- **Masked dossier.** One per day, at `newsc/drops_blind/<first 16 hex of its SHA-256>.txt`, a path without the date. Per
  company: an opaque id (X1, X2, … in an order fixed by a hash, not by rank or size of the fall), "Company A" for the name words
  and code, day offsets (D-1, D0), Sydney times, the price-sensitive flag, up to 10 focused and 6 other headlines (200 characters
  each), and the first 1,500 characters of up to 3 stored texts. Dates become `[date]`, years `YYYY`, per-share money amounts
  `$[amount]`. **No price, return, volume, rank, holdings flag or calendar date.** Masking is imperfect (a project or person's
  name can reveal the company); the rubric says to label from the text alone, which is why the keyword classifier is primary.
- **Isolation and model** as NEWS-C v1 s3: two fresh Claude Code subagents (pass 1 and pass 2), Read tool only, the rubric and
  the dossier file only; the model fields are recorded; a change is flagged `MODEL CHANGE` and is a new stratum.
- **Two passes.** A cause both passes give is kept; a disagreement keeps U. The sub-cause is kept when both agree, else MIXED.
- History is never re-labelled for scoring.

## 4. Recording

**Daily morning task** (exact steps in `bigwins_forward/code/README_NEWSC.md`, steps 2b, 3b and 4b), after the archive step:
1. `newsc_drops.py` writes `newsc/<D>/drops.jsonl` (one row per event; an empty file on a day without events), `drops.sha256`,
   `drops_dossier.jsonl` (the masked canonical items), `drops_manifest.json` (pool file hash, bulk and list hashes, index return,
   events blocked by the re-fire rule or excluded, classifier, rubric and code hashes) and the blind dossier file. A re-run that
   would change anything is refused.
2. Two rater subagents label the dossier (skipped on a day with no dossier).
3. `newsc_drops_record.py` validates the replies (schema; every company exactly once; cause T/F/U; a sub-cause of that cause;
   reason 1–20 words; rubric id, dossier hash and pass echoed back), checks every file against the manifest and re-renders the
   dossier, writes `drops_labels.jsonl` and the replies verbatim, and appends **one ledger entry per session, kind
   `info_drops`**, with all hashes, the model fields, counts and failures.
- A separate entry kind keeps NEWS-C v1's `info_news` entry and `newsc_record.py` (registered at seq 106) unchanged, and the
  two have different deadlines.
- **Deadline: before the close of D+1** (16:00 Sydney on the first session after D), which is the entry price of every reading.
  A day recorded later is flagged **LATE**, kept, and excluded from every reading. The keyword label is covered by the same
  timestamp.
- One schema-failed reply may be replaced once by a fresh rater call; the rejection is reported. Labels are never replaced for
  their content.
- **Owner screens:** counts only. No code, name or label anywhere the owner looks, including failure reports (as NEWS-C v1 s8).

## 5. Measurement (`newsc_score.py --drops`, computed later)

- **Entry:** the close of the first session after D at which the share trades (close and volume above 0), within 5 sessions;
  otherwise the event is dropped and counted.
- **Return:** raw close to raw close from the paper bulk files, with distributions and confirmed corporate-action values as cash
  (not reinvested) and splits applied to the share count, as NEWS-C v1 s6. **Excess** = that minus A200.AU tracked the same way.
- **Horizons:** 21, 63, 126 and 252 sessions after entry (1, 3, 6, 12 months).
- **Recovered:** a split-adjusted close at or above the close of D−1 within 252 sessions of D.
- **Further fall:** a close 20% / 50% below the entry close within 252 sessions of D.
- **Standard errors** (research_dip PREREG s3, "event-clustered"): events summed by calendar month of D, months without events
  count as zero; variance of the mean = [Σ S_m² + 2 Σ_{l=1..L} (1 − l/(L+1)) Σ S_m S_{m−l}] / n², L = 1, 3, 6, 12 months for the
  four horizons. The temporary-minus-fundamental difference is the slope of excess on a temporary dummy over temporary and
  fundamental events, with the same variance applied to its scores.
- Every measure is shown **by cause class**, keyword (primary) and rater (secondary), and for all events.

## 6. Reading plan and bar (wording fixed now)

**When.** The first reading is at **1 December 2029 or after at least 100 on-time events, whichever is later**. Before that,
`newsc_score.py --drops` prints "no reading", shows counts only, and **reads no price after any event**. Only events whose
horizon has ended count for that horizon.

**Bar** (keyword classifier, on-time events only):
1. temporary-cause drops show a **positive mean 252-session excess return over A200 with t ≥ 2.0** (s5 errors); **and**
2. they **beat fundamental-cause drops**: the temporary-minus-fundamental difference in 252-session excess return is positive.
   With no fundamental event the bar is not met.

"Present" if and only if both hold. The rater's classes, the other horizons, recovery and further-fall shares are
**description only**, never a second chance at the bar. A "present" reading earns at most a separately pre-registered
paper-line proposal; "not detected" ends nothing else. The log is not part of the NEWS-C v1 Benjamini–Hochberg family.

**Expected power.** A read-only check found 6 events in the 20 sessions to 24 Nov 2026 (about a month; stitched from the
forward store and the bulk files), above research_dip's long-run ASX rate of about 30 a year (653 events, 2005–26). 100 events
are therefore expected before Dec 2029, and the date binds. research_dip found fundamental causes rare in its top-100 universe
(16–21 US events in 5.6 years of vendor news), so the second leg of the bar may have little power.

## 7. Changes to installed files

- **New:** `newsc_drops.py`, `newsc_drops_classify.py`, `newsc_drops_record.py`, `test_newsc_drops.py`,
  `data/newsc/DROPS_RUBRIC_v1.md`.
- **Changed:** `newsc_score.py` gains `--drops` and the s5–s6 functions; **every NEWS-C v1 function is unchanged** and its
  default command is unchanged. The registered v1 file is kept as `newsc_score_pre_drops.py`, SHA-256 `81494c82…6eadf5`, the
  value in seq 106's `depends_on_sha256`. `README_NEWSC.md` gains steps 2b, 3b, 4b (old file kept as `README_NEWSC_pre_drops.md`).
  `newsc_record.py` hashes `newsc_score.py` into every `info_news` entry, so those entries record the new hash from registration on.
- **Unchanged:** `info_archive.py`, `newsc_prepare.py`, `newsc_baselines.py`, `newsc_record.py`, `RUBRIC_v1.md`, every paper file.

## 8. Limits

- **Pool.** The decision file's ranking differs from research_dip's pool in two small ways: no explicit 252-session history
  test (bw13 needs 200 traded sessions of the last 252) and no "traded in the last 5 sessions" test at the month-end.
- **Index.** A200.AU (ETF close plus distributions) stands in for the ASX 200 total-return series research_dip used.
- **Non-AUD distributions** are dropped by `paper_lib.load_day`; a large foreign-currency distribution on its ex-date could
  look like a fall (none in the 20-session check).
- **Headlines are thin.** Top-100 companies outside band C and the holdings get headlines only; the keyword rules were built
  on vendor news titles, not ASX headlines ("Half Year Results" is T_EARN whatever the results say). This is why both a frozen
  keyword label and a blinded reader are kept, and why the bar is on the frozen one.
- **Batching.** All of a day's events share one rater call.
- **Calendar.** `paper_lib.sessions()` ends on 31 Dec 2028; the drop reading uses its own XASX calendar to 2035.

## 9. Files (SHA-256 at drafting; the registering entry records the hashes of the installed files)

| File | SHA-256 |
|---|---|
| `bigwins_forward/data/newsc/DROPS_RUBRIC_v1.md` | `dbb9cef411e06882cd405df70c19dcad8f13df7d4da717ea474bcbf41f2a1ddc` |
| `bigwins_forward/code/newsc_drops_classify.py` (= `research_dip/code/classify.py`) | `b7c98fbde718f3c4c5176ea205a2f56416820d95ba296f78d87980626cb2c4cc` |
| `bigwins_forward/code/newsc_drops.py` | `2abad8dc9253442b564faef1d89e88ae6406b30893a6b808a9c53416d38eee2d` |
| `bigwins_forward/code/newsc_drops_record.py` | `dc766981c560d8766204031473cdc7c7c4834d2ed63e90aff6c3cf97fcb61a57` |
| `bigwins_forward/code/newsc_score.py` | `2db72149adcbbb60a0d6d396bf7a91ad56c3f609ee7acd50b3862aeb1f297fb5` |
| `bigwins_forward/code/newsc_score_pre_drops.py` | `81494c8290eba560e8868e4a3cfa299f2deebbf0b1a5553ebc56430d2c6eadf5` |
| `bigwins_forward/code/test_newsc_drops.py` | `17e69d056208b4ee783187325feef4458fa3742ef1225ada2205181ce1b64052` |
| `bigwins_forward/code/README_NEWSC.md` | `6e7c20baad6ef9b7fac998dcca84ae4846cf8ee249e9a881cf741160e758086e` |
| `bigwins_forward/code/README_NEWSC_pre_drops.md` | `ef5869b4055966fd664820c0a71af63f8f06caa2b438b9c78d9182a09cfe14d3` |
| `bigwins_forward/code/paper_lib.py` (read only) | `25d0fa4566c1152cd495192520e437cd5ab054d60a0a3b75000947295475ad44` |
| `bigwins_forward/code/newsc_baselines.py` (read only) | `d2f71588c015affe5199ee45389465356e72e5aeb1f74d6ef614fc4bd96924c8` |
| `research_dip/PREREG.md` (source of the rules) | `be74f26f7b05d031df6e28f014f11aec5c31af6a71a53a79f487286d18812515` |

**Statement.** Information only. The big-drop log feeds no paper line and no trade. It is never evidence for or against EMG2.
It changes no line.
