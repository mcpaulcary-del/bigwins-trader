# INFORMATION ONLY - re-scores the H82 paper books as if brokerage had been cheaper. Makes no trading decision and never writes
# state.json or score_state.json (both opened read-only; sha256 of state.json checked before and after).  Same trades, same fills,
# same half-spread; only the brokerage changes, and the saving is added back to cash and carried forward (not reinvested).
# AMENDMENT_scoring_v2.md §3 (ledger seq 18): every brokerage case is compared with the A$0-brokerage comparators (CMP_*_b0, the
# owner's platform), not with the frozen J3 comparators; cost_alt_history.csv is regenerated in full each run (one row per book per day).
#   python3 -I paper_costalt.py
# Output: onedrive/research2/68_forward_record/paper/COST_ALT.md and cost_alt_history.csv.
import os, sys, json, hashlib, time
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
sys.path.insert(0, S + '/bigwins_forward/code')
STATE = S + '/bigwins_forward/out/paper_state/state.json'
SCORE = S + '/bigwins_forward/out/paper_state/score_state.json'
PAPER = S + '/onedrive/research2/68_forward_record/paper'
MD = PAPER + '/COST_ALT.md'
HIST = PAPER + '/cost_alt_history.csv'
BOOKS = [('H82_lifecycle_5k', 'lifecycle_5k'), ('H82_25k', '25k'), ('H82_100k', '100k')]
ALTS = [('A$3', lambda v: 3.0), ('A$0', lambda v: 0.0)]

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def units_at(b, d):
    u = float(b['capital']) / 100.0
    for f, a in sorted(b.get('flows', [])):
        if f > d: break
        nb = b['nav'].get(f)
        if nb is None or u <= 0: continue
        u += a / ((nb - a) / u)
    return u

def ret_at(b, d): return b['nav'][d] / units_at(b, d) / 100.0 - 1

def alt_series(b, fee):
    """NAV and unit-index return per recorded day with brokerage replaced by fee(value); same trades, saving held as cash."""
    dates = sorted(b['nav']); units = float(b['capital']) / 100.0; flows = {}
    for d, a in b.get('flows', []): flows[d] = flows.get(d, 0.0) + float(a)
    out, prev_nav = {}, None
    for d in dates:
        save = sum(t['brokerage'] - fee(t['shares'] * t['price'] if 'shares' in t else abs(t.get('cash', 0)))
                   for t in b['trades'] if t['date'] <= d)
        nav = b['nav'][d] + save
        if d in flows:                                   # contribution priced at the alt NAV before it (time-weighted unit index)
            base = nav - flows[d]
            units += flows[d] / (base / units)
        out[d] = (nav, nav / units / 100.0 - 1, save); prev_nav = nav
    return out

def run(log=print):
    h0 = sha(STATE)
    with open(STATE, 'r') as f: st = json.load(f)
    with open(SCORE, 'r') as f: ps = json.load(f)
    asof = st['last_processed']
    books = {b['id']: b for b in st['books']}; c0 = {c['id']: c for c in ps['cmps']}
    rows = []
    for bid, tag in BOOKS:
        b = books[bid]; a2 = c0[f'CMP_A200_{tag}_b0']; mx = c0[f'CMP_4060_{tag}_b0']
        alts = {name: alt_series(b, fee) for name, fee in ALTS}
        for d in sorted(b['nav']):
            if d not in a2['nav'] or d not in mx['nav']: continue
            r = dict(asof=d, book=bid, n_trades=sum(1 for t in b['trades'] if t['date'] <= d),
                     brokerage_paid=round(sum(t['brokerage'] for t in b['trades'] if t['date'] <= d), 2),
                     nav_actual=round(b['nav'][d], 2), ret_actual=ret_at(b, d), a200_b0_return=ret_at(a2, d), plan4060_b0_return=ret_at(mx, d))
            for name, _ in ALTS:
                nav, ret, save = alts[name][d]; k = name.replace('A$', 'b')
                r[f'nav_{k}'] = round(nav, 2); r[f'ret_{k}'] = ret; r[f'saving_{k}'] = round(save, 2)
            for k in ('actual', 'b3', 'b0'):
                r[f'{k}_vs_a200_b0'] = r[f'ret_{k}'] - r['a200_b0_return']; r[f'{k}_vs_4060_b0'] = r[f'ret_{k}'] - r['plan4060_b0_return']
            rows.append(r)
    last = [r for r in rows if r['asof'] == max(x['asof'] for x in rows if x['book'] == r['book'])]
    pct = lambda x: f'{x * 100:+.2f}%'
    L = [f'# Cheaper-broker re-scoring (INFORMATION ONLY) - as of {asof}', '',
         '**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. '
         'No real money; the AI never places trades.**', '',
         'Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), '
         'then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). '
         'Returns are time-weighted (unit index), as in SCORECARD.md. **Every case is compared with the comparator books at A$0 brokerage** '
         '(A200 and the 40/60 plan as the owner holds them; AMENDMENT_scoring_v2.md). The frozen J3 comparators (A$6.60 per fund purchase) are not used here.', '',
         '| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 (A$0) | Actual vs A200 | A$3 vs A200 | A$0 vs A200 | 40/60 (A$0) | Actual vs 40/60 | A$0 vs 40/60 |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in last:
        L.append(f"| {r['book']} | {r['n_trades']} | {r['brokerage_paid']:,.2f} | {pct(r['ret_actual'])} | {pct(r['ret_b3'])} | {pct(r['ret_b0'])} | "
                 f"{pct(r['a200_b0_return'])} | {pct(r['actual_vs_a200_b0'])} | {pct(r['b3_vs_a200_b0'])} | {pct(r['b0_vs_a200_b0'])} | "
                 f"{pct(r['plan4060_b0_return'])} | {pct(r['actual_vs_4060_b0'])} | {pct(r['b0_vs_4060_b0'])} |")
    L += ['', f'Generated {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} by paper_costalt.py; state.json sha256 {h0}; score_state.json sha256 {sha(SCORE)}.',
          'History: cost_alt_history.csv, regenerated in full each run (one row per book per recorded day); the version written before AMENDMENT_scoring_v2 is kept as cost_alt_history_v1_frozen.csv.', '']
    open(MD, 'w').write('\n'.join(L))
    cols = list(rows[0]); tmp = HIST + '.tmp'
    with open(tmp, 'w') as f:
        f.write(','.join(cols) + '\n')
        for r in rows: f.write(','.join(f'{r[c]:.6f}' if isinstance(r[c], float) else str(r[c]) for c in cols) + '\n')
    os.replace(tmp, HIST)
    h1 = sha(STATE)
    assert h1 == h0, 'state.json changed during the run'
    log('\n'.join(L[8:8 + len(last)])); log(f'state.json sha256 unchanged: {h1}')
    return last

if __name__ == '__main__':
    run()
