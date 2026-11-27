# NEWS-C daily morning task (information only)

NEWS-C feeds no paper line and no trade. It is never evidence for or against EMG2. Rules: `AMENDMENT_info_NEWSC_v1.md`.
Rubric: `bigwins_forward/data/newsc/RUBRIC_v1.md` (frozen; `newsc_record.py` refuses to record if its hash changes).

`S=/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad`, `C=$S/bigwins_forward/code`,
`N=$S/bigwins_forward/data/newsc`.

**When:** ASX trading days at about 08:30 Sydney. Everything must finish before 10:00 Sydney. A day recorded after 10:00 is
flagged LATE and left out of every bar.

**Report only failures.** A failure is any non-zero exit code, any line containing `REFUSED`, `PAUSED`, `FAIL`, `LATE` or
`MODEL CHANGE`, or a failures list that is not empty. On a normal day, report nothing.

## Steps

1. **Archive.**
   `cd $C && python3 info_archive.py asx`
   - The output has two lines: `asx <D>: ...` and `asx <D> price-sensitive: ...`. `<D>` is the list-day, which should be the
     previous ASX session.
   - Failure: an exception, `PAUSED`, or a `<D>` that is not the previous session. Report it and stop.
   - `already stored` on both lines is not a failure if the day was archived earlier, for example by the evening job.
   - Use `asx` only, not ASIC, so the run stays short. The evening job keeps its full run, and for a day already stored that
     run is a no-op.

2. **Prepare.**
   `python3 newsc_prepare.py`
   - With no `--day`, it uses the ASX session before today. It prints the number of code-days and the batches.
   - Exit 0 with `already prepared` means a re-run on an unchanged day. Continue.
   - Exit 2 or `REFUSED` is a failure. Report it and stop.
   - If it reports `0 code-days`, skip step 3 and go to step 4 with an empty replies folder.

3. **Rate: spawn the blinded rater subagents.**
   - Read `$N/<D>/manifest.json`. For each entry in `batches` (fields `batch` and `sha256`), and for pass 1 and pass 2:
     - Start a **new, separate subagent**. Never reuse one, and never let one see another's output.
     - Give it exactly the prompt below, with no other text, context or file. Fill in only the parts in angle brackets.
     - Write its reply **byte for byte** to `$N/<D>/incoming/<batch>_p<pass>.json`. Do not edit, reformat or repair it.
   - Subagents may run in parallel.

   ```
   You are the NEWS-C rater. Use only the Read tool. Read these two files in full and no other file:
   1. /tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins_forward/data/newsc/RUBRIC_v1.md
   2. /tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins_forward/data/newsc/<D>/batches/<batch>.txt
   Then follow the rubric (file 1) and rate every announcement in the batch (file 2).
   HEADER
   batch: <batch>
   batch_sha256: <sha256>
   pass: <1 or 2>
   Reply with the JSON object only.
   ```

   - The task itself must not read the batch files, give the subagent any other information, or change any rating.
   - **Schema failures:** if step 4 refuses one reply for its schema (not valid JSON, a missing announcement, a bad type or
     rating, a reason over 20 words), do this once:
     1. Move that reply to `$N/<D>/rejected/`.
     2. Spawn one **fresh** subagent for that batch and pass, with the same prompt.
     3. Run step 4 again.
     4. Report the rejection.
   - Never re-spawn because of the ratings' content.
   - Recommended: install a rater agent with only the Read tool and a pinned model (see "Model pinning" below), and spawn it
     with that agent type.

4. **Record.**
   - First call the claude-code-remote tool `get_session` (no arguments) and note:
     - `session_context.model`
     - `external_metadata.last_served_model`
     - the model setting the subagents ran with: `inherit`, or the rater agent's `model:` value.
   - Then run:

   ```
   python3 newsc_record.py --day <D> --ratings-dir $N/<D>/incoming \
     --model "<the subagents' model: the rater agent's pinned ID if set, else last_served_model>" \
     --model-source "get_session: session_context.model=<...>; last_served_model=<...>; rater agent model setting=<...>" \
     --session-id "<this session's id>" --subagent-model "<inherit | the rater agent's model: value>" \
     [--failures "<any rejection or other problem, separated by ;>"]
   ```

   - It prints `recorded <D>: ledger seq <n>; ...; failures: none` on a normal day.
   - `REFUSED`, exit 2, or a failures list other than `none` is a failure. Report it.
   - It refuses on any of these:
     - the amendment is not registered;
     - the rubric's hash changed;
     - the input or batch hash does not match;
     - a reply is missing or invalid;
     - the day is already recorded.

5. **Report only failures.** Report only the lines that failed. Never report per-share ratings, not even inside a failure report
   (amendment s8: the owner sees monthly counts only).

## Model pinning (open limit)

- A Claude Code subagent runs on the session's model (`inherit`) unless the agent definition sets one.
- `get_session` reports the **task session's** model. It does not report the subagent's. Each reply also carries the rater's
  own `model_self_report`, and the record stores both.
- To pin the model, install this agent file, then spawn the rater as subagent type `newsc-rater`. The file goes in
  `.claude/agents/newsc-rater.md` in the scheduled task's working directory, or in `~/.claude/agents/`.

```
---
name: newsc-rater
description: NEWS-C blinded announcement rater (information only). Reads only the rubric and one batch file named in the prompt; replies with JSON.
tools: Read
model: <exact model ID if this Claude Code version accepts one, else an alias such as opus>
---
You are the NEWS-C rater. Read only the two files named in the prompt, follow the rubric, reply with the JSON object only.
```

- An alias such as `opus` is not a pin, because the alias moves to newer models.
- If the reported model changes, `newsc_record.py` flags `MODEL CHANGE`. The owner then registers a ledger entry for the new
  stratum (amendment s3).

## Other commands

- `python3 test_newsc.py`: the test suite. It works on scratch copies only and needs no network.
- `python3 newsc_score.py [--asof D] [--external EST-C=p,DIL-C=p]`: the reading. It shows descriptive tables only until
  January 2028 (drift) and December 2029 (wrecks and winners). It writes only to `$N/readings/<asof>/`, and it is never used to
  change the rubric.
