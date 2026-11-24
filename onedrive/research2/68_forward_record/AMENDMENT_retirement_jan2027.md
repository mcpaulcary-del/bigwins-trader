# Amendment: paper-line retirement list for January 2027, fixed before any result

Status: **REGISTERED 24 Nov 2026 (Sydney) — PAPER ONLY**, by the record keeper on the owner's decision of that day ("lock in the cut list"). It is based on the independent approach review (`review_approach/REVIEW.md`, section 2) and the gap review (`research_gaps/REPORT.md`). It is registered **before the first month-end decision of any line named here** (30 Nov 2026), so no line's results can have influenced the list.

**Nothing here changes the main strategy.** EMG2-18 + band-trend shield + C6 (the live trader and `EMG2_18_SIM_BT_C6`) is frozen until 1 Jan 2027 (seq 88). This amendment changes no rule of any line. It only fixes which lines stop being booked.

## 1. Lines retired (9 strategies, plus the REF twins)
These lines are chosen on structure only: they duplicate another line, were already rejected, or the project's own reports say they cannot pass. None is chosen on results.

| Line | Reason |
|---|---|
| EMG2-18 H6 (paper twin) | superseded variant of the main line |
| EMG2-18 COMBO (paper twin) | superseded variant of the main line |
| EMG2_18_SIM_BT (band trend, without C6) | superseded by BT_C6 (the main line) |
| PAIR (EMG2-18 + BLIND3 in one account) | can be computed from its two members |
| EARLY | rejected (report 84) |
| ACC (keep winners) | shadow, not adopted |
| SHADOW M3 | index-like shadow; own reports say it cannot pass |
| SHADOW E3 | index-like shadow; own reports say it cannot pass |
| SHADOW CXL | index-like shadow; own reports say it cannot pass |
| the 100 random twins of `EMG2_18_REF` | **the REF book itself is kept** (comparison book of the MOON lines, AMENDMENT_shadow_moon_v1 s4) |

## 2. Lines kept (12 strategies)
- **Main line:** `EMG2_18_SIM_BT_C6`, with its 100 twins.
- **Comparisons:** `EMG2_18_REF` (book only), EMG2 (A$100k measurement line), H82 Large-Cap Core (A$5k / 25k / 100k), MOM (momentum comparison).
- **Candidate:** BLIND3.
- **Side lines (seq 91):** SWEEP, WIDE, FIP.
- **Aggressive side lines (seq 94):** MOON_TOP5, MOON_NOLOT5, MOON_LEG2.
- **Information lines (not strategies):** EST-C, DIL-C. The A200 and 40/60 comparators and the random portfolios of H82 also stay.

## 3. Timing and mechanics
- **The retired lines run unchanged until the 31 Dec 2026 review.** Their final values are booked at the close of the last ASX session of 2026 and reported in the 31 Dec review as information only.
- **From the first ASX session of 2027 they are no longer booked.** Their state files, orders and history stay in the record unchanged, and nothing is deleted.
- **The code change is made in January** (after the freeze) and recorded as its own code ledger entry. It must show that every kept line's output is byte-identical with and without the retired lines.
- **No line is added back.** A retired line can only return through a new amendment with a new name and a new start.

## 4. Cap on new lines (widens the moon amendment s5)
- **No new paper line of any kind is added before the December 2028 review unless an existing line is retired at the same time.** This covers trading lines, side lines and aggressive lines; it excludes information-only archives that feed no line.
- **Mid-way changes do not count:** retirements decided after seeing results must name the result-free reason in the ledger.

## 5. Readings
- **Owner-facing results:** the owner's screens show the main line against A200 after all costs (including fixed costs) as the headline. The other kept lines are shown as information only, labelled "mostly luck at this stage", and are never ranked as a leaderboard.
- **No go-live use:** no kept line other than the main line can be considered for real money before the December 2028 review, as registered (seq 91, seq 94).

## 6. Trial count
Registering adds no trial. **N 3,046.**
