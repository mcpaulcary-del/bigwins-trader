# Amendment: LIVE book EMG2-20 becomes EMG2-18 (18 companies at about A$550 each; A$10,000 kept)

Status: **REGISTERED 19 Nov 2026 — registration only**, by the record keeper, on the owner's build decision BF-D1 (`OWNER_DECISIONS_2026-11-19.md`, section "Build decisions (B-fast)"). Amends `AMENDMENT_live_EMG2_20.md` (ledger seq 37). Hashed (SHA-256) and appended to `LEDGER.jsonl` before any code for the live book exists and before the first decision of its paper month (Mon 30 Nov 2026). No live trading code exists in the record; the go-live checklist of `AMENDMENT_live_EMG2_20.md` section 4 remains the gate. The AI never places trades.

## 1. Why
With A$10,000, a A$50 cash reserve and A$6.60 brokerage, 20 equal parcels fall below the ASX minimum marketable parcel of A$500 for a first purchase as soon as the account dips a little, so orders would be skipped from the start. The owner chose 18 companies at about A$550 each and kept the A$10,000 capital.

## 2. Changes (everything not listed here is unchanged)
- The live book and its simulated twin are renamed **EMG2-18**: `EMG2_18_LIVE`, `EMG2_18_SIM`, `EMG2_18_RND_s001…s100` (seeds 8550000 + i, unchanged), comparator `EMG2_18_CMP_A200`. Every reference to "EMG2-20" or "20 names" in `AMENDMENT_live_EMG2_20.md` reads "EMG2-18" / "18 names".
- **Rule L3 (slots) becomes:** n = min(18, floor(account value ÷ A$550)). Parcel = account value ÷ n.
- **Rule L5:** "while fewer than n names are held" uses the n of L3 above; the A$500 minimum order, the A$50 reserve and whole-share rounding are unchanged.
- **Rule L6 (start):** a one-parcel canary buy of the top name, then the other 17 buys the session after the canary reconciles.
- **Rule L10:** the order-value limit of A$800 and the other hard limits are unchanged.
- Expected brokerage: about 125–130 trades and about A$825–860 a year (8–9% of the capital). The statement of L14 is unchanged in substance.

## 3. What is not changed
The paper books of `AMENDMENT_shadow_EMG2.md` (EMG2_100k, EMG2_25k, their twins, stress books, comparators and BANDSPREAD) are unchanged. The capital cap (A$10,000), approval rules (L8), loss limits (L11), the v3 stop rules (L12) and the gate (section 4) are unchanged. The live book is never read as evidence for or against EMG2.

## 4. Trial count
No back-test of the 18-name variant has been run or looked at. Not a trial. No change to N.
