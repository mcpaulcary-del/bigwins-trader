# Amendment: EMG2-18 random twins draw their list from the same buyable set as the real book (all paper lines with EMG2-18 twins)

Status: **REGISTERED 21 Nov 2026 — PAPER ONLY, information only**, by the record keeper, hashed (SHA-256) and appended to `LEDGER.jsonl` **before the code change** and before the first decision it governs (Mon 30 Nov 2026, the first decision of every line it touches). No real money, no broker orders. The AI never places trades.
Amends the random-twin definition (only) of: `AMENDMENT_shadow_EMG2_18_H6.md`, `AMENDMENT_shadow_EMG2_COMBO.md` (section "A twin replaces the EMG2 score ... Its T is the top fifth of band C by that score"), `AMENDMENT_shadow_EMG2_18_BT.md` (section R, "random list as the other EMG2-18 paper twins"), `AMENDMENT_shadow_EMG2_18_BT_C6.md` (twins) and `AMENDMENT_shadow_PAIR.md` (member E's twin). The real books, their rules, the twins' seeds, the random scores and their redraw rule, the keep zone K, costs, slots, the reading and every bar are unchanged. Does not change any live amendment or the trading system (`/home/user/asx-trader` is not touched; its own EMG2_18 random twins, if they draw the same way, are flagged for the owner).

## 1. Why (pre-flight of the 30 Nov 2026 decision, 21 Nov 2026, finding F4)
The EMG2-18 rules buy from the target list T (top fifth of band C by score, bid peg out) best first and **skip lottery-class names** (FD s8.6: under 504 sessions of history, close under A$0.20, or 63-session median traded value under A$250k). The registered twins take the top len(T) (34 on the forced 30 Nov run) of band C by a random score, but about half of band C is lottery class (~49% on the forced run), so a twin's list holds only ~17 names it may buy (forced run: band C 187 names, 92 of them lottery class; the real T has 34 names of which 21 are buyable). On the forced 30 Nov run 54 of 100 H6 twins and 61 of 100 COMBO twins held fewer than 18 names, with up to A$4,981 of A$10,000 idle in cash, while the real book held 18. A twin that cannot spend its cash is not the "same rules, random list" null that the twins are meant to be: it lowers the twins' risk and, in a rising market, their return, which **flatters the real book's percentile among its twins**. The same flaw sits in every line that uses `paper_emg2s.lists_for` for twins: EMG2_18_H6/COMBO twins, EMG2_18_SIM_BT twins, EMG2_18_SIM_BT_C6 twins and PAIR member E's twin.

Checked and **not** affected: the EMG2 A$100k/A$25k twins (`AMENDMENT_shadow_EMG2.md`): the EMG2 rules have no lottery filter, so the real book and its twins draw from the same set (band C, bid peg out). BLIND3 and PAIR member B twins: the frozen builder code applies the same buy set (ordinary, valid, place <= 400) to the real book and the twins; the twins cannot be starved of buyable names. (Recorded, not changed: in the frozen `strat.py` the BLEND family's low-volatility half filter applies to the real book only, so BLIND3 twins buy from a wider set than the real book. That is the builder's frozen and calibrated null, SHA-pinned, and does not leave cash idle; changing it would need the builder's own amendment.)

## 2. Rule (replaces "Its T is the top fifth of band C by that score" for every EMG2-18 twin listed above)
At each month-end decision from 30 Nov 2026 the twin keeps its persistent random scores over band C exactly as registered (same seeds, same draw order, redraw p = 0.2). Let T be the real book's list (top fifth of band C by the EMG2 score, bid peg out), and m the number of names in T that are **not** lottery class (the names the real book may buy). The twin's list is drawn **by stratum**:
- the m best random scores among the band-C names that are not bid peg and not lottery class, plus
- the len(T) − m best random scores among the band-C names that are not bid peg and are lottery class,

ordered by random score (best first). So the twin's list has the real list's length and exactly the real list's number of buyable names; the buy step (lottery, peg, no trade on the day, no close skipped; slots, parcel, A$500 minimum, A$50 reserve) is unchanged and identical for real book and twin. Sell rules apply to this list as registered: L4 / H6 "off T", L4-C / C6 "outside K" with K = band-C members whose random-score percentile is above 0.60 (unchanged). The lottery class is the one the real book uses at the same month-end (`paper_emg2s.lottery` on the same table).

## 3. Effective
From the 30 Nov 2026 decision, the first decision of every affected line: no twin has decided yet, so no state is restated. Tables dated before 30 Nov 2026 (tests, history) keep the old draw.

## 4. Mechanics (record keeper)
`paper_emg2s.lists_for(b, R, lot)` (used by `paper_emg2s.decide`, hence also by `paper_emg2bt.py` and `paper_emg2bt6.py`) and the member-E twin call in `paper_pair.py`. Old code kept as `*_pre85_frozen.py`. The code entry after this one records the tests.

## 5. Trial count
No back-test, no trial; N 2,958.
