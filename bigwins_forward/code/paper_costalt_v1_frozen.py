# INFORMATION ONLY - re-scores the H82 paper books as if brokerage had been cheaper. Makes no trading decision and never writes
# state.json (opened read-only; its sha256 is checked before and after).  Same trades, same fills, same half-spread; only the
# brokerage changes, and the saving is added back to cash and carried forward (not reinvested - simple, conservative approach).
#   python3 -I paper_costalt.py
# Output: onedrive/research2/68_forward_record/paper/COST_ALT.md and a row per book in cost_alt_history.csv (once per as-of day).
import os, sys, json, hashlib, time
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
STATE = S + '/bigwins_forward/out/paper_state/state.json'
PAPER = S + '/onedrive/research2/68_forward_record/paper'
MD = PAPER + '/COST_ALT.md'
HIST = PAPER + '/cost_alt_history.csv'
BOOKS = [('H82_lifecycle_5k', 'CMP_A200_lifecycle_5k'), ('H82_25k', 'CMP_A200_25k'), ('H82_100k', 'CMP_A200_100k')]
ALTS = [('A$3', lambda v: 3.0), ('A$0', lambda v: 0.0)]

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

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
            base = prev_nav if prev_nav is not None else nav - flows[d]
            units += flows[d] / (base / units)
        out[d] = (nav, nav / units / 100.0 - 1, save); prev_nav = nav
    return out

def run(log=print):
    h0 = sha(STATE)
    with open(STATE, 'r') as f: st = json.load(f)
    asof = st['last_processed']
    books = {b['id']: b for b in st['books']}; cmps = {c['id']: c for c in st['cmps']}
    rows = []
    for bid, cid in BOOKS:
        b = books[bid]; c = cmps[cid]; d = max(b['nav'])
        act = b['nav'][d] / b['units'] / 100 - 1
        a200 = c['nav'][max(c['nav'])] / c['units'] / 100 - 1
        r = dict(asof=asof, book=bid, nav_date=d, n_trades=len(b['trades']), brokerage_paid=round(sum(t['brokerage'] for t in b['trades']), 2),
                 nav_actual=round(b['nav'][d], 2), ret_actual=act, a200_return=a200)
        for name, fee in ALTS:
            nav, ret, save = alt_series(b, fee)[d]
            k = name.replace('A$', 'b')
            r[f'nav_{k}'] = round(nav, 2); r[f'ret_{k}'] = ret; r[f'saving_{k}'] = round(save, 2)
        rows.append(r)
    pct = lambda x: f'{x * 100:+.2f}%'
    L = [f'# Cheaper-broker re-scoring (INFORMATION ONLY) - as of {asof}', '',
         '**PAPER - information only. Not part of the frozen rules; makes no trading decision; the paper state is read, never written. '
         'No real money; the AI never places trades.**', '',
         'Same trades, same fills, same half-spread (v1.3 E2) as the official record; only brokerage differs: actual = max(A$6.60, 0.088%), '
         'then A$3.00 flat per trade, then A$0. The saving is added back to cash and carried forward (not reinvested). '
         'Returns are time-weighted (unit index), as in SCORECARD.md. A200 = the EODHD-proxy comparator book of the same size.', '',
         '| Book | Trades | Brokerage paid A$ | Actual-cost return | A$3 return | A$0 return | A200 TR | Actual vs A200 | A$3 vs A200 | A$0 vs A200 |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        a = r['a200_return']
        L.append(f"| {r['book']} | {r['n_trades']} | {r['brokerage_paid']:,.2f} | {pct(r['ret_actual'])} | {pct(r['ret_b3'])} | {pct(r['ret_b0'])} | "
                 f"{pct(a)} | {pct(r['ret_actual'] - a)} | {pct(r['ret_b3'] - a)} | {pct(r['ret_b0'] - a)} |")
    L += ['', f'Generated {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())} by paper_costalt.py; state.json sha256 {h0}.', '']
    open(MD, 'w').write('\n'.join(L))
    cols = list(rows[0])
    seen = set()
    if os.path.exists(HIST):
        seen = {l.split(',')[0] for l in open(HIST).read().splitlines()[1:]}
    if asof not in seen:
        new = not os.path.exists(HIST)
        with open(HIST, 'a') as f:
            if new: f.write(','.join(cols) + '\n')
            for r in rows: f.write(','.join(f'{r[c]:.6f}' if isinstance(r[c], float) else str(r[c]) for c in cols) + '\n')
    else:
        log(f'{asof} already in cost_alt_history.csv; history not appended')
    h1 = sha(STATE)
    assert h1 == h0, 'state.json changed during the run'
    log('\n'.join(L[8:8 + len(rows)])); log(f'state.json sha256 unchanged: {h1}')
    return rows

if __name__ == '__main__':
    run()
