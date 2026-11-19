# Amendment: LIVE book EMG2-20 — A$10,000 real money by owner decision

Status: **REGISTERED 19 Nov 2026 — registration only** (owner decision of 19 Nov 2026, "Later the same day — real money", `OWNER_DECISIONS_2026-11-19.md`). No live trading code exists in the record; the build happens separately (FD v3.0 §21.1 B-fast) and must pass the go-live checklist (section 4) before any real order. Hashed (SHA-256) and appended to `LEDGER.jsonl` by the record keeper on 19 Nov 2026, before any code for it is installed and before the first decision of any line it governs (Mon 30 Nov 2026). Text below is the research agent's (Fable) draft `deep85/AMENDMENT_live_EMG2_20.md` (SHA-256 76fdd43cd34767a155956e23deb29e732c4edfc8de3ee1041c2a071b031accd9) unchanged except this status line and the title. The AI never places trades.

## 1. What this is, stated plainly
- **Real money on a line that is not adopted on evidence.** EMG2 failed its pre-set statistical bar (report 85 T6: t 1.0 against 2.0). Step P1 of adopt rule v3 (12 months of paper operation and its tests) is **waived by the owner** for this one slice; the conditions are recorded as not met.
- **Brokerage alone is about A$840–930 a year, 8–9% of the capital** (A$6.60 on every A$500 order, about 140 trades a year). The back-test lead was +4.9 points a year. **The expected result at this size is below the index even if the signal works.** The owner was shown this and chose it. What the slice can deliver is knowledge of real fills, real costs and the working of the system.
- The research agent's recommendation was 12 months of paper first. This amendment implements the owner's decision.
- Expect falls of 40–60% at some point; most of the slice can be lost.

## 2. Rules (EMG2-20 v1.0)
Section numbers and the codes BW-…, O-… in the table refer to FD v3.0 (`FD_v3.0_BigWins.md`); "session" = ASX trading day. Signal, eligible set, band-C list and score: EMG2 v1.0 rules 1–3. Lottery class: listed under 504 trading days, or raw close under A$0.20, or `tv_med63` under A$250,000.
| # | Rule |
|---|---|
| L1 | **Capital.** A$10,000 deposited once. `capital_cap_aud: 10000`: cash above the cap is never invested. No contributions are planned; any later deposit needs a new owner decision. |
| L2 | **Candidates.** T = EMG2's target list of the decision (top fifth of band C, best first). **Lottery-class names (section 8.6: listed under 504 sessions, close under A$0.20, or `tv_med63` under A$250,000) are skipped** for buying. *(A safety filter for real money; not in the back-test.)* |
| L3 | **Slots.** n = min(20, floor(account value ÷ A$500)). Parcel = account value ÷ n. |
| L4 | **Sell.** A holding is sold in full when it is **not on T** at a month-end decision (the whole top fifth, about 45 names, not just the best 20). So a holding that slips from 5th to 30th is kept. Also sold: a holding flagged `BID_PEG`; a payout arrives as cash. No trims, no top-ups, no stop-loss. |
| L5 | **Buy.** After the decision's sells, while fewer than n names are held: buy the best-ranked names of T that are not held and not skipped by L2, one parcel each. Order value = min(parcel, cash available − A$50 reserve) ÷ (1 for a single buy; cash is shared equally when several buys compete for less cash than their parcels). **An order under A$500 is not sent** (ASX minimum marketable parcel for a first purchase); its cash waits for the next decision. Whole shares, rounded down. |
| L6 | **Clock.** Regular decisions at each ASX month-end after the close, orders on the next session. **Start:** a start decision on the first session from Mon 14 Dec 2026 on which the go-live checklist (section 21.1) is signed, using that day's universe table and scores; a one-parcel canary buy of the top name on the next session; the other 19 buys the session after the canary reconciles. If the checklist is not signed by Fri 18 Dec, the start moves to the 31 Dec 2026 month-end decision (orders Mon 4 Jan 2027). After a December start before the 31st, the **31 Dec decision is skipped** for this book (holdings two weeks old); the first regular decision is Fri 29 Jan 2027. |
| L7 | **Execution.** Sells on session D+1. Buys on the first session, from D+1 to D+4, on which IBKR reports enough available funds for them (O-2); after D+4 a buy lapses. Order type: limit-on-close if the reality spike proves it for these shares (O-1); otherwise a DAY limit order sent at 15:30: buy at the ask plus one price step, not above reference × 1.03; sell at the bid minus one price step, not below reference × 0.97; reference = last trade at the 14:30 tick; unfilled at 15:58 is cancelled and carried one session (sells up to 3 sessions, then paged). |
| L8 | **Approval.** For the start and the first three regular decisions (to the April 2027 decision), **each order** needs the owner's `/ok <batch> <n> <code>` or `/ok <batch> all <code>` by 15:20 on the execution session; an order not approved is not sent. After that, batch approval (section 12) unless the owner extends per-order approval. |
| L9 | **Costs.** IBKR fixed pricing: max(A$6.60, 0.088%) a trade, so A$6.60 on every A$500 order (1.3% a side). Expected: about 140 trades and **A$840–930 a year**. The start costs about A$132. Spread as the learned table (start: 0.50% a side with the half-step floor). |
| L10 | **Hard limits (breaker, live book).** Order value ≤ A$800. Orders a day ≤ 24 on the start days, ≤ 16 otherwise. Buys a day ≤ A$10,500 on the start days, ≤ A$4,500 otherwise. Limit price inside the L7 band; reference more than 15% from the previous close: buy held one session. Order ≤ 5% of `tv_med20`. IBKR account precautions set to: maximum order value A$1,000, daily A$12,000. |
| L11 | **Loss limits.** Account value ≤ A$7,000: PAGE and review. **≤ A$6,000: `HALTED_BUYS`** (BW-RSK-29); the owner decides in writing to continue or close. ≤ A$5,000: line halted (BW-RSK-20). One-day fall of 12%: `HALTED_BUYS`. `/kill` stops everything in one step. A halt never sells by itself. |
| L12 | **Stop rules of adopt rule v3 apply** to this slice exactly as to the paper line: at a December review from 13 months after EMG2's registration, signal spread t ≤ −1.0, or the A$100k paper book below the 20th percentile of its twins, or (from 24 months) after tax more than 15 points a year behind A200: the slice is sold down over the next two decisions and closed. Scale-up beyond A$10,000 only by step P2 as written. |
| L13 | **Side by side.** A simulated twin `EMG2_20_SIM` runs the same rules from the 30 Nov 2026 decision at the same costs (the paper month), with 100 random twins; the IBKR paper account mirrors it from the first day the order path works. From the live start, live and simulated books are compared daily: fills, costs, holdings, value. A difference in holdings that is not explained by an unapproved or unfilled order is `HALTED_INTEGRITY`. |
| L14 | **Reporting.** Every report of this book carries: "Real money. Owner override of the 12-month paper step. Brokerage about 8–9% of capital a year. Expected result at this size is below the index even if the signal works." Monthly: value, deposits, brokerage paid to date in dollars and as a share of capital, realised and unrealised result, the same money in A200. |

## 3. Books
| Book | Start | Fills |
|---|---|---|
| `EMG2_20_SIM` (simulated twin) | A$10,000 at the 30 Nov 2026 decision | Next trading day's close, rule L9 costs |
| `EMG2_20_RND_s001…s100` (random twins of the simulated book; seeds 8550000 + i) | same | same |
| IBKR **paper** account mirror | From the first session the order path works (target 1–4 Dec 2026), buying the 30 Nov EMG2-20 list | IBKR paper fills |
| `EMG2_20_LIVE` (real) | Rule L6: start decision from Mon 14 Dec 2026 once the go-live checklist is signed; else the 31 Dec 2026 decision | IBKR live fills |
| Comparator `EMG2_20_CMP_A200` | A$10,000 in A200 at the live start, A$0 brokerage, never sold | EODHD proxy |

## 4. Gate before the first live order
The go-live checklist of FD v3.0 section 21.1 (15 lines), every line evidenced, signed by the owner with the second factor, recorded as a ledger entry of kind `gate`. If any line fails, the start waits. The date is a target; the checklist is the gate.

## 5. Reading
Reported daily and monthly (rule L14). The live book is never read as evidence for or against EMG2: 20 names at 1.3% a side is a different, costlier thing than the registered A$100,000 book. Evidence about EMG2 comes from the paper book, its twins and the signal spread. The live book answers: are fills and costs as modelled; does the system do exactly what it decided.

## 6. End of the slice
By the stop rules of adopt rule v3 (rule L12), by the loss limits (L11) and the owner's decision, or by the owner at any time (`/kill`, then a sell instruction). Scale-up beyond A$10,000 only through step P2.

## 7. Trial count
No back-test of the 20-name variant has been run or looked at. Registering it adds no trial. No change to N.
