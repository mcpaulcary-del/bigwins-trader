# Big Wins forward PAPER record -- SHADOW line EARLY "young companies that have started well, held while they keep working" (report 84).
# Governed by 68_forward_record/AMENDMENT_shadow_EARLY.md.  SHADOW, INFORMATION ONLY, UNPROVEN: not shown to beat the index.
# PAPER ONLY: no real money, no broker orders, the AI never places trades.
# Rules: early_ref.py (frozen copy of deep84/code/early_ref.py: PARAMS, features, passes, decide's candidate table, half_spread, fund/res flags).
# Universe and decision-day features: early_live.load() (frozen copy of deep84/code/early_live.py) on the new-listings tracker's files (read only).
# Booking: the record's conventions (bulk EODHD closes, dividends, splits; whole shares; A200 held as a parcel book), own state
# STATE_DIR/early_state.json, own clock (first decision 2026-11-30 with the start-up catch-up, fills at the next session's close).
# Y8: a month-end decision waits for the tracker's prices of that day (paths.csv.gz); if they are still missing when the bulk file of the second
# session after it exists, that month has no decision.  Never reads or writes the H82 state or another line's state.
# Idempotent and resumable: a day is booked once (last_processed); a later run catches up from the stored bulk files.
import os, re, json, math, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_score as PS
import early_ref as ER

EA_START = '2026-11-30'
NL = P.S + '/bigwins_forward/data/newlist'                # the tracker's own folder (read only)
FUND = 'A200'; FUND_HS = 0.0003
BOOKS = (('EARLY_100k_b0', 'EARLY', 100000.0, 0.04, 25, 'b0'), ('EARLY_25k_b0', 'EARLY', 25000.0, 0.10, 10, 'b0'),
         ('EARLY_100k_e1', 'EARLY_STRESS', 100000.0, 0.04, 25, 'e1'))
NRAND = 100; SEED_C1 = 8410000; SEED_C2 = 8420000
TAG = 'SHADOW EARLY (report 84): INFORMATION ONLY, UNPROVEN; not shown to beat the index'
EXPECT = 'About level with the index fund, with a much bumpier ride; a small chance of one large winner.'


def state_path(): return P.STATE_DIR + '/early_state.json'
def out_dir(): return P.REC + '/shadow'
def zero(v): return 0.0
BROK = {'b0': zero, 'e1': P.brokerage}


# ---------------------------------------------------------------- state
def new_book(bid, kind, cap, pct, nmax, brok, seed=None):
    return dict(id=bid, kind=kind, capital=cap, pct=pct, nmax=nmax, brok=brok, seed=seed, rng_state=None, start=EA_START, cash=cap,
                holdings={}, orders=[], E=None, bought=[], trades=[], divs=[], ntrades=0, nav={EA_START: cap}, units=cap / 100.0,
                spread_paid=0.0, brok_paid=0.0, events=[], log=[])

def init_state():
    fill = P.next_session(EA_START); books = [new_book(*x) for x in BOOKS]
    books += [new_book(f'EARLY_C1_100k_s{i:03d}', 'EARLY_C1', 100000.0, 0.04, 25, 'b0', SEED_C1 + i) for i in range(1, NRAND + 1)]
    books += [new_book(f'EARLY_C2_100k_s{i:03d}', 'EARLY_C2', 100000.0, 0.04, 25, 'b0', SEED_C2 + i) for i in range(1, NRAND + 1)]
    for b in books: b['orders'] = [dict(type='fund_in', code=FUND, reason='start: all capital into A200')]; b['E'] = fill
    cmps = [PS.new_cmp0(f'EARLY_CMP_A200_{t}', {'A200.AU': 1.0}, c, 0.0, EA_START, fill) for t, c in (('100k', 100000.0), ('25k', 25000.0))]
    return dict(record='Big Wins forward paper record -- SHADOW EARLY (report 84; PAPER ONLY; information only; unproven)', amendment='AMENDMENT_shadow_EARLY.md',
                start_decision=EA_START, fill_day=fill, last_processed=P.prev_session(EA_START), decisions=[], data_blocks=[], last={}, tv={},
                books=books, cmps=cmps)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- book arithmetic
def shares(h): return sum(l[1] for l in h['lots'])
def nav_of(b, last):
    return b['cash'] + sum(shares(h) * last[h['code']]['p'] for h in (b['holdings'][k] for k in sorted(b['holdings'])) if h['code'] in last)
def fund_value(b, last):
    h = b['holdings'].get(FUND); return shares(h) * last[FUND]['p'] if h and FUND in last else 0.0
def ev(b, d, s):
    if b['kind'] not in ('EARLY_C1', 'EARLY_C2'): b['events'].append([d, s])
def record(b, t):
    b['ntrades'] += 1
    if b['kind'] not in ('EARLY_C1', 'EARLY_C2'): b['trades'].append(t)

def realise(h, q, proceeds):
    out = []; rem = q
    for l in sorted(h['lots'], key=lambda l: l[0]):
        if rem <= 1e-9: break
        x = min(rem, l[1]); c = l[2] * x / l[1]
        out.append([l[0], x, c, proceeds * x / q]); l[1] -= x; l[2] -= c; rem -= x
    h['lots'] = [l for l in h['lots'] if l[1] > 1e-9]
    return out

def tv63(s, code):
    v = s['tv'].get(code) or []
    return float(np.median(v[-63:])) if v else 0.0

def fund_sell(b, d, amount, p, why):
    h = b['holdings'].get(FUND)
    if not h or amount <= 0: return 0.0
    q = min(shares(h), amount / p); brok = BROK[b['brok']]; bk = brok(q * p)
    pr = q * p * (1 - FUND_HS) - bk; b['cash'] += pr; b['brok_paid'] += bk
    parts = realise(h, q, pr)
    if not h['lots']: del b['holdings'][FUND]
    record(b, dict(date=d, side='sell', code=FUND, shares=q, price=p, half_spread=FUND_HS, brokerage=bk, cash=round(pr, 2), reason=why, lots=parts))
    return pr

def fund_buy(b, d, p, why):
    a = b['cash']; brok = BROK[b['brok']]
    if a < (100.0 if b['brok'] == 'b0' else 500.0): return
    bk = brok(a); q = (a - bk) / (p * (1 + FUND_HS))
    if q <= 0: return
    b['cash'] -= a; b['brok_paid'] += bk
    h = b['holdings'].setdefault(FUND, dict(code=FUND, lots=[])); h['lots'].append([d, q, a])
    record(b, dict(date=d, side='buy', code=FUND, shares=q, price=p, half_spread=FUND_HS, brokerage=bk, cash=round(-a, 2), reason=why))


# ---------------------------------------------------------------- one trading day
def run_day(s, b, d, mkt):
    cl = mkt['close']; brok = BROK[b['brok']]
    for cid in sorted(b['holdings']):
        h = b['holdings'][cid]; sp = mkt['split'].get(h['code'])
        if sp and sp > 0:
            for l in h['lots']: l[1] *= sp
            ev(b, d, f"split {h['code']} x{sp:g}")
    for cid in sorted(b['holdings']):
        h = b['holdings'][cid]; v = mkt['div'].get(h['code'])
        if not v or not any(l[0] < d for l in h['lots']): continue
        q = sum(l[1] for l in h['lots'] if l[0] < d)
        if cid == FUND and cl.get(FUND):                                                    # A200 distributions reinvested (record's proxy)
            c = q * v; du = c / cl[FUND]; h['lots'].append([d, du, c]); b['divs'].append([d, FUND, q, v, round(c, 2)])
        else:                                                                               # Y7: company dividends are cash, into A200 at the next decision
            c = q * v; b['cash'] += c; h['dv'] = h.get('dv', 0.0) + c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    pf = cl.get(FUND)
    for o in [o for o in b['orders'] if o['type'] == 'sell']:                                # Y6 sells first; proceeds buy A200
        h = b['holdings'].get(o['code'])
        if h is None: continue
        if o.get('payout'):
            q = shares(h); p = s['last'].get(o['code'], {}).get('p', 0.0); v = q * p
            parts = realise(h, q, v); b['cash'] += v; del b['holdings'][o['code']]
            record(b, dict(date=d, side='payout', code=o['code'], shares=q, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason=o['reason'], lots=parts))
            b['log'].append([o['code'], h['fill'], d, h['in'], v + h.get('dv', 0.0), o['reason']]); continue
        p = cl.get(o['code'])
        if p is None: ev(b, d, f"sell {o['code']} not filled (no close); decided again next month-end"); continue
        q = shares(h); hh = ER.half_spread(p, tv63(s, o['code'])); bk = brok(q * p)
        pr = max(0.0, q * p * (1 - hh) - bk); b['cash'] += pr; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk
        parts = realise(h, q, pr); del b['holdings'][o['code']]
        record(b, dict(date=d, side='sell', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(pr, 2), reason=o['reason'], lots=parts))
        b['log'].append([o['code'], h['fill'], d, h['in'], pr + h.get('dv', 0.0), o['reason']])
    if any(o['type'] == 'fund_in' for o in b['orders']) and pf:
        fund_buy(b, d, pf, 'start: capital into A200')
    for o in [o for o in b['orders'] if o['type'] == 'buy']:                                 # Y5 buys: slice of the book's value at the fill close
        p = cl.get(o['code'])
        if p is None: ev(b, d, f"buy {o['code']} dropped: no close on the fill day"); continue
        cnt = sum(1 for c in b['holdings'] if c != FUND)
        if cnt >= b['nmax']: ev(b, d, f"buy {o['code']} dropped: {cnt} names held"); continue
        last = dict(s['last']); last[FUND] = dict(p=pf or last.get(FUND, {}).get('p', 0.0), d=d)
        for c in b['holdings']:
            if c in cl: last[c] = dict(p=cl[c], d=d)
        nav = nav_of(b, last); size = b['pct'] * nav; avail = fund_value(b, last) + b['cash']
        if avail < 1.02 * size or not pf: ev(b, d, f"buy {o['code']} dropped: A200 {avail:.2f} < 1.02 x slice {size:.2f}"); continue
        hh = ER.half_spread(p, o['tv63']); bk = brok(size); q = int(math.floor((size - bk) / (p * (1 + hh))))
        if q <= 0: ev(b, d, f"buy {o['code']} dropped: 0 shares"); continue
        paid = q * p * (1 + hh) + bk
        if b['cash'] < paid: fund_sell(b, d, (paid - b['cash']) / (1 - FUND_HS) + BROK[b['brok']](paid - b['cash']) + 1.0, pf, f"pays for {o['code']}")
        b['cash'] -= paid; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk
        b['holdings'][o['code']] = dict(code=o['code'], lots=[[d, q, paid]], fill=d, peak=1.0, dv=0.0, catchup=o.get('catchup', False))
        b['holdings'][o['code']]['in'] = q * p
        b['bought'].append(o['code'])
        record(b, dict(date=d, side='buy', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(-paid, 2), reason=o['reason']))
    if pf: fund_buy(b, d, pf, 'cash into A200 (Y5/Y6/Y7)')
    b['orders'] = []


# ---------------------------------------------------------------- decision (Y3-Y6)
def holding_tr(s, h):
    """total return since the fill (fill = 1.00): (shares x last close + dividends received) / value at the fill close"""
    p = s['last'].get(h['code'], {}).get('p')
    return (shares(h) * p + h.get('dv', 0.0)) / h['in'] if p and h['in'] > 0 else None

def sells_for(s, b, d):
    out = []
    for c in sorted(b['holdings']):
        if c == FUND: continue
        h = b['holdings'][c]; lc = s['last'].get(c, {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= ER.PARAMS['payout_days']:
            out.append(dict(type='sell', code=c, payout=True, reason=f"Y6(c) payout: no close for {ER.PARAMS['payout_days']} sessions (last {lc})")); continue
        w = holding_tr(s, h)
        if w is None: continue
        h['peak'] = max(h.get('peak', 1.0), w)
        if len(P.sessions_between(h['fill'], d)) >= ER.PARAMS['max_hold']: out.append(dict(type='sell', code=c, reason='Y6(b) time: 756 sessions'))
        elif w <= (1 - ER.PARAMS['stop_drop']) * h['peak']: out.append(dict(type='sell', code=c, reason=f"Y6(a) stop: {100 * (1 - w / h['peak']):.0f}% below best month-end"))
    return out

def band(tv):
    return 0 if tv >= 3e6 else 1 if tv >= 1e6 else 2 if tv >= 2.5e5 else 3 if tv >= 5e4 else 4

def older_pool(D, d):
    """C2s: companies listed more than five years (first close in the forward file > 5 years before d), traded on d; by 63-session traded-value band"""
    import paper_emg2 as EM
    nm = EM.names(); lic = EM.lic_codes(); cols = list(D['cols']); i = len(D['dates']) - 1
    Pv = D['Pv']; C = D['Craw']; V0 = D['V0']; has = np.isfinite(Pv)
    with np.errstate(all='ignore'):
        TV = np.where(np.isfinite(C) & (C > 0), V0 if d >= '2026-12-31' else V0 * Pv / C, 0.0)
        m63 = np.nanmedian(np.where(has[i - 62:i + 1], TV[i - 62:i + 1], 0.0), axis=0)
    t5 = pd.Timestamp(d) - pd.DateOffset(years=5); dates = D['dates']
    pool = {}
    for j, cid in enumerate(cols):
        code = cid.split('#')[0]
        if not has[i, j] or D['firstv'][j] >= len(dates) or dates[D['firstv'][j]] > t5: continue
        if code in lic or EM.LIC_RE.search(nm.get(code, '')) or ER.fund_flag(nm.get(code, '')): continue
        pool.setdefault(band(float(m63[j])), []).append((code, float(m63[j])))
    for k in pool: pool[k].sort()
    return pool

def rng_for(b):
    r = np.random.default_rng(b['seed'])
    if b['rng_state'] is not None: r.bit_generator.state = b['rng_state']
    return r

def decide_all(s, d, log, bundle_fn):
    import early_live as EL
    cal, cols, LIST, RET, CLOSE, TV, XJ, lasti = EL.load(pd.Timestamp(d))
    i = len(cal) - 1
    assert str(cal[i].date()) == d, f'tracker calendar ends {cal[i].date()}, not {d}'
    amax = 252 if d == EA_START else None
    E = P.next_session(d); orows = []; table = None; info = {}
    main = None
    for b in s['books']:
        sells = sells_for(s, b, d)
        S_ = dict(pos={}, bought=list(b['bought']) + [c for c in b['holdings'] if c != FUND])
        held = [c for c in b['holdings'] if c != FUND]
        if b['kind'] in ('EARLY', 'EARLY_STRESS'):
            Dn = ER.decide(S_, i, cols, LIST, RET, CLOSE, TV, XJ, lasti, dict(ER.PARAMS, max_pos=b['nmax']), catchup_age_max=amax)
            if table is None: table = Dn['table']
            tab = {t['code']: t for t in Dn['table']}
            free = b['nmax'] - (len(held) - len(sells))
            buys = [dict(type='buy', code=c, tv63=tab[c]['tv63'], tv=tab[c]['tv'], catchup=bool(amax and tab[c]['age'] > ER.PARAMS['age_max']), reason='Y5 buy' + (' (catch-up)' if amax and tab[c]['age'] > ER.PARAMS['age_max'] else ''))
                    for c in Dn['buys'][:max(free, 0)]]
            if b['id'] == 'EARLY_100k_b0': main = buys
        else:
            buys = []
        b['orders'] = [o for o in b['orders'] if o['type'] == 'fund_in'] + sells + buys; b['E'] = E
        if b['kind'] in ('EARLY', 'EARLY_STRESS'):
            for o in b['orders']: orows.append(dict(book=b['id'], type=o['type'], code=o.get('code', FUND), reason=o['reason'], fill='close of ' + E))
            ev(b, d, 'decision: ' + (', '.join(f"{o['type']} {o['code']}" for o in b['orders']) or 'nothing'))
    # controls: the same number of buys as EARLY_100k_b0, drawn at random (C1s: same age window, any that traded; C2s: listed > 5 years, same band)
    k = len(main or []); win = [t for t in (table or [])]
    pool2 = None
    if k and any(b['kind'] == 'EARLY_C2' for b in s['books']):
        D, _, _ = bundle_fn(d, log); pool2 = older_pool(D, d); del D
    for b in s['books']:
        if b['kind'] not in ('EARLY_C1', 'EARLY_C2'): continue
        r = rng_for(b); free = b['nmax'] - (len([c for c in b['holdings'] if c != FUND]) - len([o for o in b['orders'] if o['type'] == 'sell']))
        picks = []
        if b['kind'] == 'EARLY_C1':
            cand = sorted(t['code'] for t in win if t['code'] not in b['holdings'] and t['code'] not in b['bought'])
            if cand and k: picks = [dict(code=c, tv63=next(t['tv63'] for t in win if t['code'] == c)) for c in r.choice(cand, size=min(k, len(cand)), replace=False)]
        else:
            for o in (main or []):
                cand = [x for x in (pool2 or {}).get(band(o['tv63']), []) if x[0] not in b['holdings'] and x[0] not in b['bought'] and x[0] not in [p['code'] for p in picks]]
                if cand: x = cand[int(r.integers(len(cand)))]; picks.append(dict(code=x[0], tv63=x[1]))
        b['rng_state'] = r.bit_generator.state
        b['orders'] += [dict(type='buy', code=p['code'], tv63=p['tv63'], reason='control buy') for p in picks[:max(free, 0)]]
    os.makedirs(out_dir(), exist_ok=True); files = {}
    T = pd.DataFrame(table or [], columns=['code', 'ok', 'why', 'age', 'tv', 'close', 'mom', 'xmom', 'vola', 'tv63'])
    if len(T):
        T = T.join(LIST[['name', 'res', 'industry', 'listing_date']], on='code')
        T['catch_up'] = T.age > ER.PARAMS['age_max']
    T.insert(0, 'date', d)
    files[f'shadow/early_decision_{d}.csv'] = P.write_csv(f'{out_dir()}/early_decision_{d}.csv', T)
    files[f'shadow/early_orders_{d}.csv'] = P.write_csv(f'{out_dir()}/early_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'type', 'code', 'reason', 'fill']))
    sbp = f'{out_dir()}/early_scoreboard.csv'                                            # section 7: every ordinary new listing at its look (measurement)
    old = pd.read_csv(sbp) if os.path.exists(sbp) else pd.DataFrame()
    if len(old): old = old[old['date'].astype(str) != d]
    files['shadow/early_scoreboard.csv'] = P.write_csv(sbp, pd.concat([old, T], ignore_index=True))
    info = dict(asof=d, fill_day=E, looked_at=int(len(T)), passed=int(T.ok.sum()) if len(T) else 0, buys_100k=[o['code'] for o in (main or [])], files_sha256=files)
    log('SHADOW EARLY', d, f"decision; looked at {info['looked_at']}, passed {info['passed']}, buys {info['buys_100k']}")
    return info

def tracker_has(d):
    p = NL + '/paths.csv.gz'
    if not os.path.exists(p): return False
    try: return (pd.read_csv(p, usecols=['date']).date.astype(str).str[:10] == d).any()
    except Exception: return False


def step(s, d, mkt, log, bundle_fn):
    """returns (info, wait)"""
    if d >= EA_START and P.is_month_end(d) and not tracker_has(d):
        d2 = P.next_session(P.next_session(d))
        if not os.path.exists(f'{P.BULK}/{d2}/eod.json.gz'):
            log('SHADOW EARLY', d, 'waiting for the new-listings tracker prices of this month-end (Y8); resumes on a later run'); return None, True
    last = s['last']
    watch = {FUND} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders'] if 'code' in o}
    for c in watch:
        if c in mkt['close']:
            last[c] = dict(p=mkt['close'][c], d=d)
            if c != FUND: s['tv'].setdefault(c, []).append(mkt['close'][c] * mkt['vol'].get(c, 0.0)); s['tv'][c] = s['tv'][c][-63:]
        elif c != FUND: s['tv'].setdefault(c, []).append(0.0); s['tv'][c] = s['tv'][c][-63:]
    for b in s['books']: run_day(s, b, d, mkt)
    for c in s['cmps']: PS.cmp_day0(c, d, mkt)
    info = None
    if d >= EA_START and P.is_month_end(d):
        if not tracker_has(d):
            s['data_blocks'].append([d, 'Y8 data block: the new-listings tracker has no prices for this month-end; no EARLY decision; missed age windows not revisited'])
            log('SHADOW EARLY', d, 'Y8 data block'); info = dict(asof=d, blocked=True, reason='tracker prices missing (Y8)')
        else:
            info = decide_all(s, d, log, bundle_fn); s['decisions'].append(d)
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    s['tv'] = {c: v for c, v in s['tv'].items() if c in watch}
    s['last_processed'] = d
    return info, False


def run(d, mkt, log, bundle_fn=None):
    """Bring EARLY up to trading day d (after the other shadow lines). Returns a small dict for the ledger (None before the start)."""
    try:
        if d < EA_START: return None
        if bundle_fn is None:
            import paper_emg2 as EM; bundle_fn = EM.get_bundle
        s = load()
        if s is None: s = init_state(); log('SHADOW EARLY state created; first decision', EA_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('SHADOW EARLY', x, 'no bulk file; stops here and resumes on a later run'); break
            info, wait = step(s, x, m, log, bundle_fn)
            if wait: break
            save(s)
            if info: decs.append(info)
        if not os.path.exists(state_path()): save(s)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('SHADOW EARLY ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard rows
def twr(b, nav): return (nav / b['units']) / 100.0 - 1 if b['units'] > 0 else float('nan')

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        rows.append(dict(asof=d, book='EARLY_100k_b0', kind='SHADOW_EARLY', capital=100000.0, note=f'{TAG}; not started: first decision {EA_START}, fills at the close of {P.next_session(EA_START)}'))
        md.append(f'| SHADOW EARLY (report 84; AMENDMENT_shadow_EARLY.md) | — | — | {TAG}; first decision Mon 30 Nov 2026 (with start-up catch-up), fills Tue 1 Dec 2026; {EXPECT} |')
        return rows, md, hold
    last = s['last']; cm = {c['id']: c for c in s['cmps']}
    f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else (f'{x:+.2%}' if isinstance(x, float) else str(x))
    c1 = np.array([twr(x, nav_of(x, last)) for x in s['books'] if x['kind'] == 'EARLY_C1'])
    c2 = np.array([twr(x, nav_of(x, last)) for x in s['books'] if x['kind'] == 'EARLY_C2'])
    for b in [x for x in s['books'] if x['kind'] in ('EARLY', 'EARLY_STRESS')]:
        tag = '100k' if b['capital'] == 100000.0 else '25k'; a2 = cm[f'EARLY_CMP_A200_{tag}']
        nav = nav_of(b, last); r = twr(b, nav); ra = twr(a2, P.nav_of(a2, last))
        sale = lambda cid, code, q, p, b=b, s=s: q * p * (FUND_HS if cid == FUND else ER.half_spread(p, tv63(s, code))) + BROK[b['brok']](q * p)
        kept, sold = PS.after_tax_engine(b, last, s['last_processed'], sale); rk, rs = PS.at_return(kept, b['units']), PS.at_return(sold, b['units'])
        ak, _ = PS.after_tax_cmp0(a2, last, s['last_processed']); rak = PS.at_return(ak, a2['units'])
        young = sum(shares(h) * last[h['code']]['p'] for c, h in b['holdings'].items() if c != FUND and h['code'] in last)
        prim = b['id'] == 'EARLY_100k_b0'
        m2 = float(np.median(c2)) if prim and len(c2) else None
        rows.append(dict(asof=d, book=b['id'], kind='SHADOW_EARLY' if b['kind'] == 'EARLY' else 'SHADOW EARLY cost stress', capital=b['capital'], contributed=0.0, nav=round(nav, 2),
                         nav_q6_at_70pct=round(nav, 2), cash=round(b['cash'], 2), holdings=len(b['holdings']) - (1 if FUND in b['holdings'] else 0), open_orders=len(b['orders']),
                         return_since_start=round(r, 5), vs_random_median=(None if m2 is None else round(r - m2, 5)), random_median_return=(None if m2 is None else round(m2, 5)),
                         pct_of_random=(round(float(np.mean(c2 < r)), 3) if prim and len(c2) else None),
                         a200_b0_return=round(ra, 5), vs_a200_b0=round(r - ra, 5), after_tax_kept_AUD=round(kept, 2), after_tax_sold_AUD=round(sold, 2),
                         ret_after_tax_kept=round(rk, 5), ret_after_tax_sold=round(rs, 5), vs_a200_b0_after_tax_kept=round(rk - rak, 5), vs_a200_b0_engine_sold_fund_kept=round(rs - rak, 5),
                         note=(f"{TAG}; young companies {young / nav:.1%} of the book; spread paid A$ {b['spread_paid']:,.2f}; brokerage A$ {b['brok_paid']:,.2f}"
                               + (f"; % of C1s below {float(np.mean(c1 < r)):.3f}, % of C2s below {float(np.mean(c2 < r)):.3f}" if prim and len(c1) and len(c2) else ''))))
        if prim:
            md.append(f"| {b['id']} (SHADOW EARLY, unproven) | {nav:,.2f} | {f(r)} | **minus median C2s book {f(None if m2 is None else r - m2)}**; vs A200 (A$0) {f(r - ra)}; "
                      f"young companies {young / nav:.1%}; names {len(b['holdings']) - (1 if FUND in b['holdings'] else 0)}; % of C1s / C2s below "
                      f"{'' if not len(c1) else round(float(np.mean(c1 < r)), 3)} / {'' if not len(c2) else round(float(np.mean(c2 < r)), 3)}; {EXPECT} |")
        hs_ = ', '.join(f"{h['code']} {shares(h):,.0f}" for c, h in b['holdings'].items() if c != FUND)
        if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no young companies'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    for nm, v in (('C1s', c1), ('C2s', c2)):
        if len(v): rows.append(dict(asof=d, book=f'EARLY_{nm}_100k ({len(v)} seeds)', kind='SHADOW EARLY random control', capital=100000.0, return_since_start=round(float(np.median(v)), 5),
                                    note=f'median; 5th-95th pct {np.percentile(v, 5):.4f} to {np.percentile(v, 95):.4f}'))
    for c in s['cmps']:
        rows.append(dict(asof=d, book=c['id'], kind='SHADOW comparator', capital=c['capital'], nav=round(P.nav_of(c, last), 2), return_since_start=round(twr(c, P.nav_of(c, last)), 5),
                         note='own clock from 2026-11-30; A$0 brokerage; EODHD proxy'))
    return rows, md, hold
