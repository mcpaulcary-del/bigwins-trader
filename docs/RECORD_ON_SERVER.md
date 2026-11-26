# The paper record on your server (BF-D93, BF-D94)

Your decision of 27 Nov 2026: "move as much as we can to server and automated". This page
replaces section 8 of the move plan. PAPER ONLY: nothing here places an order.

## What you do (from the phone)

| When | Where | What |
|---|---|---|
| **Now** | Termius | `df -h / ; free -m ; docker system df` and paste the output into the Claude chat (no secrets in it). The move needs **20 GB free** (10 GB is the bare minimum for the test week). |
| **Now** (optional, 1 minute) | Termius | `sudo bigwins record view on` : the app shows the **real** paper record from a read-only copy (Home > Paper record). Nothing else changes. |
| About **Thu 10 / Fri 11 Dec**, evening | App | Approve the update as usual (Server > the update card, your code). Outside ASX hours. |
| **Sat 12 Dec** | Termius | `sudo bigwins record seed` (waits about 10 minutes, ends with **PASS**), then `sudo bigwins record shadow on`. OneDrive must be connected on the server first (`bigwins onedrive`, guide C8). |
| **Mon 14 - Fri 18 Dec** | App | Nothing. One Inbox line each evening: "Shadow compare ...: PASS". |
| **Sat 19 Dec**, about 18:15 | Chat + Termius | When the chat shows 12 characters: `sudo bigwins record cutover`. It prints 12 characters. Type `yes` **only if they are the same**. |
| Then | App | Server > Health: "Paper record: written on this server". Done. |
| From January, when the app says entries are waiting | Termius | `bigwins record requests` : each research entry is shown; `y` adds it to the ledger. |

Only if Claude tells you to roll back: `sudo bigwins record handback` (prints 12
characters; read them to Claude). If the server is dead: switch it **off** in the
BinaryLane app first, then tell Claude "take over".

Optional (2 minutes, any time): an outside alarm for each record job. healthchecks.io >
your project > Settings > **Ping key** > copy the URL `https://hc-ping.com/<ping key>`,
then `bigwins secret healthchecks_record_url` and paste it. Each job makes its own check
the first time it runs.

**One thing needs your yes before Sat 12 Dec** (tell Claude): the announcements are then
collected on the server by the research record's own collector
(`record/code/info_archive.py`, unchanged, same limits: previous-day list, the notices,
at most 60 price-sensitive PDFs a day, one request every 2 seconds, never in ASX hours),
not by the older server copy `deploy/info_archive.py` that `CLAUDE.md` names. One
collector per server; the older one stands down. If you prefer the older one, say so and
the price-sensitive step will be ported into it first.

## What you see in the app

- **Home > Paper record**: the main line on paper against A200 (after the record's
  costs) first; then the research lines in their registered order, each with its value,
  change today, return against A200 and 40/60, and where it sits among its random twins.
  Information only, mostly luck at this stage, never ranked. Holdings with their day
  moves. "Full scorecard" is the record's own text.
- **Inbox, each trading evening**: "Paper record booked for ..." (plain numbers, written
  by the server at about 20:45), then "Nightly report for ... is ready" (the short report
  the cloud task writes, with **Big movers**). Read it first thing in the morning.
- **News tab**: "Big movers" with the one-line why and the source links.
- **Server > Health**: who writes the record, the ledger head, the record jobs (a late
  or failed one sends one alert), the record disk, the parallel run's result.

## What runs where after Sat 19 Dec

| On your server, by itself | Still in the cloud (needs Claude) |
|---|---|
| Announcements archive and ASIC shorts (07:40 daily; retries 08:10 and 20:50) | NEWS-C ratings (08:29): the raters read the batches the server prepared and send the replies back |
| NEWS-C: prepare the batches, find the big drops, **record** the ratings in the ledger | Intraday: the "why it moved" for a real alert on a held share (:32) |
| Estimates, new listings, the CXL line's ASIC files (Tue-Sat 08:43) | The nightly report: news and the reasons for the big movers (about 20:50) |
| Intraday looks (10:20, 12:20, 14:20, 16:20) | The GitHub copy of the record (the server has no write access to GitHub, on purpose) |
| **Daily close 20:27**: every paper line booked, cost comparison, the movers list, the gap check, the ledger entry | A second, independent replay of each day until Fri 8 Jan (the standby) |
| Multi-market month (days 1-8, 15:17) and the US forward tracker (days 2-5, 18:13) | Research entries: the cloud asks, you confirm on the server |
| Backups: the record nightly; the archive's PDFs one encrypted file a day (60 days off-site); big data sets when they change | |

No Claude log-in and no API key is on the server for any of this. The two sides swap
small files through one OneDrive folder ("Big Wins relay"); the server only fetches.
The Friday data bundles stop: the server backs the private data up itself.

## The parallel week: when it counts as passed

All of these, decided Fri 18 Dec after the 21:30 comparison (`bigwins record status`):

1. Five trading days in a row with engine states, record outputs, ledger entries and the
   archive / NEWS-C inputs **identical** (the comparison's classes A, B, C, D). A
   difference resets the count to zero. The cut-over command refuses under five.
2. The month-end replay (30 Nov decision, 1 Dec fills) and the multi-market replay
   identical (the engineer runs both on 12-13 Dec).
3. Every server job on time and exit 0 (Health); the daily replay done by 21:15; the
   trader's own 22:20 decision job on time every day.
4. The server's archive complete (`DONE`, `DONE_PS`) by 09:30 each day.
5. The server reached EODHD with its own token (one intraday look on the shadow:
   `sudo bigwins record job intraday`, about 300 credits).
6. The NEWS-C round trip through the relay done by 09:45 on at least four days.
7. Peak memory of the daily job under 1.8 GB (each job's result carries it).
8. A backup and a restore test that include the record both OK.
9. At least 10 GB free at the end of the week.
10. A last-digit difference is not waved through: cause first, then a fix on both sides.

Fail on 18 Dec: the cloud stays the writer, the shadow keeps running, and the cut-over
moves to **Sat 9 Jan 2027**. No cut-over between 20 Dec and 8 Jan.

## Rolling back

- **Before you typed `yes`**: nothing changed on the server. The cloud cancels its
  handover (one more ledger entry) and carries on.
- **Planned** (the server works but something is wrong): `sudo bigwins record handback`.
  One more chained ledger entry, 12 characters, the cloud accepts. No fork.
- **Server dead**: power it off (BinaryLane app), tell Claude. The cloud takes over from
  the last ledger the server sent to OneDrive (the server sends it after every job and
  does not start the next ledger job until it has). When the server comes back it sees
  the newer writer in the relay and refuses to write; at most one day's entries are
  filed as an orphan, never merged.

---

## For the engineer

### Layout

| What | Where |
|---|---|
| Record code (byte-identical copy of the research code; `record/MANIFEST.sha256`) | `record/code`, `record/data_foundation_code` |
| Tools (fence, runner, relay, compare, bundle; standard library) | `record/tools` (`bwrec.py`) |
| Host commands, timers, container | `deploy/record.sh` (in `bigwins`), `deploy/record.Dockerfile`, `deploy/record_requirements.txt` |
| Canonical tree / shadow tree / cloud mirror | `/srv/bwrecord`, `/srv/bwrecord_shadow`, `/srv/bwrecord_cloudmirror` |
| Relay staging | `/var/lib/bigwins/relay/{outbox,inbox/raw,inbox/validated,done,state}` |
| Display copy for the app | `/var/lib/bigwins/recordview` (scorecards, holdings, movers; never the ledger) |
| Mode switch (root-only, not in git) | `/etc/bigwins/record_mode`: `off`, `view`, `shadow`, `writer` |

The research code is never edited for the server. The tree is mounted at the cloud's
absolute path inside the container; `record/tools/launch.py` puts the writer fence
around `fwd_ledger.append` and the EODHD token into `requests` at send time, so the three
hash-frozen files and every registered code hash stay as they are. The runner refuses
a job when the mounted code differs from `record/MANIFEST.sha256` or the Python /
library versions differ from `record/ENVIRONMENT.json`.

Update class `record` (`deploy/classify.py`): a change under `record/` (or of the two
image build files) needs your approval like any non-app change, rebuilds only the record
image, never restarts the trader and never changes the strategy version. After copying
new research code in: `python3 record/tools/bwrec.py code-manifest`.

### Relay files (OneDrive folder "Big Wins relay")

Server to cloud, `outbox/`: `head.json` (ledger head, seq, epoch: written last),
`record/**`, `state/**`, `newsc/<D>/batches/*.txt` with `manifest.json`,
`drops_manifest.json`, the rubrics and `drops_blind/`, `daily/<D>/` (`status.json`,
`gaps.json`, `movers_<D>.md`, `compare_<D>.json`), `bundles/bundle_<D>.tar` with
`manifest_<D>.json` (the day's raw inputs, for the standby replay).

Cloud to server, `inbox/` (anything else is refused and reported, nothing is executed):

- `newsc/<D>/<batch>_p1.json`, `<batch>_p2.json`, `drops_p1.json`, `drops_p2.json`: the
  raters' replies, byte for byte; and `meta.json`:
  `{"model": "...", "model_source": "get_session: ...", "session_id": "...",
  "subagent_model": "...", "failures": "a; b"}` (the recorder's arguments).
- `reports/<D>/report.md`: the short nightly report as written for the owner; and
  `reports/<D>/report.json`:
  ```json
  {"schema": 1, "day": "2026-12-15", "written_utc": "2026-12-15T09:40:00Z",
   "title": "Big Wins - Tue 15 Dec", "verdict": "one line",
   "needs_attention": ["one short line each"],
   "movers": [{"code": "AAA", "name": "Company Ltd", "move": 0.10, "no_close": false,
               "six_month": 0.38, "from_high": -0.09, "score_rank": 2,
               "held_by": ["H82_25k"], "why": "one line, or empty = no news found",
               "sources": [1]}],
   "sources": [{"n": 1, "title": "Publisher: headline", "url": "https://..."}]}
  ```
  Fractions, not percents (`0.10` = +10%). At most 15 movers and 40 sources; `https`
  links only; no HTML. Never a NEWS-C rating or label: the format has no field for one
  and unknown fields are dropped.
- `ledger_requests/<yyyymmdd>-<nnn>-<kind>.json` (kinds `trials`, `amendment`, `code`,
  `data`, `note`):
  `{"schema": 1, "id": "<the file name without .json>", "kind": "trials",
  "requested_utc": "...", "fields": {"asof": "...", "event": "...", ...},
  "attachments": [{"name": "AMENDMENT_x.md", "sha256": "..."}]}` with the attachment
  files beside it. The cloud reads `outbox/head.json` back before it treats anything as
  registered.
- `fence.json`: only after an emergency takeover (a higher epoch stops the server).
- Parallel week: `bundles/bundle_<D>.tar` and `bundles/manifest_<D>.json` from the cloud
  (`bwrec.py bundle-make <D> <tar>`, `bwrec.py manifest <D> --archive-day <previous
  session>`; both with `BW_RECORD_HOST=cloud`).

### Cloud tasks after the cut-over (the coordinator changes them, not this build)

- **NEWS-C (08:29)**: download `outbox/newsc/<D>/` to the usual local paths; rate
  exactly as `README_NEWSC.md` steps 3 and 3b; upload each reply byte for byte and
  `meta.json` to `inbox/newsc/<D>/`. Do not run steps 1, 2, 2b, 4, 4b: the server does.
- **Intraday (:32)**: read `outbox/record/paper/alerts_latest.md`; for a real alert on a
  held share find why (WebSearch) and tell the owner. If `outbox/head.json` is older
  than 30 minutes after a look: "the server did not run".
- **Nightly (20:50)**: read `outbox/daily/<D>/` and `outbox/record/paper/`; write the
  report in the owner's layout; upload `report.md` and `report.json`; mirror
  `outbox/record` and `outbox/state` to the `paper-record` branch; apply
  `outbox/bundles/bundle_<D>.tar` and replay the day in the standby tree (through 8 Jan).
- T3 (estimates / new listings / ASIC), T5 (multi-market) and the US forward tracker
  stay disabled.

Before the cut-over the cloud can already send `reports/<D>/` (the app shows them once
`record view on` is set) and must send the two `bundles/` files each evening of the
parallel week.

### Not done here, on purpose or for lack of access

See BF-D93 in `docs/DECISIONS.md` ("Open") for the full list: the image has not been
built (no container registry from the research environment; base images are not pinned
by digest yet), the dependency trace (plan E0) and the seed upload are the
coordinator's, the scheduled tasks are unchanged, and the two rehearsals are run by hand.
