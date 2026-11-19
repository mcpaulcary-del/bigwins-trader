# Big Wins forward PAPER record -- SHADOW line EMG2 v1.0 "emerging band, monthly momentum" (lead challenger; report 85 T4/T6; FD v3.0 s7.6-7.8)
# and the BANDSPREAD measurement line.  Governed by 68_forward_record/AMENDMENT_shadow_EMG2.md (+ EMG2_LIC_LIST.csv frozen with it),
# AMENDMENT_v1.5_old_symbols.md / AMENDMENT_v1.6_dup_returns.md (entities, A7(c) on every AU ordinary share) and AMENDMENT_adopt_rule_v3.md (gate).
# SHADOW = not adopted; tracked on paper.  PAPER ONLY: no real money, no broker orders, the AI never places trades.
# Own state file (STATE_DIR/emg2_state.json), own clock (first decision 2026-11-30, fills at the next session's close), own A$0 comparators,
# 100 random twins per size.  Universe = the forward store cut at the month-end with A4(b) and A7(c) (paper_shadow.bundle_for: the same bundle
# the SHADOW lines use; from 31 Dec 2026 the H82 bundle).  Never reads or writes the H82 state or another line's state.
# Idempotent and resumable: a day is booked once (last_processed); a later run catches up from the stored bulk files.
import os, re, json, math, traceback, warnings
warnings.filterwarnings('ignore', message='All-NaN slice encountered')
warnings.filterwarnings('ignore', message='Mean of empty slice')
import numpy as np, pandas as pd
import paper_lib as P, paper_score as PS

EM_START = '2026-11-30'
SIZES = (('100k', 100000.0, 8530000, 'top'), ('25k', 25000.0, 8540000, 'n25'))   # (tag, capital, twin seed base: seed = base + i, rule-12 kind)
NRAND = 100
REDRAW = 0.2
LIC_LIST = P.REC + '/EMG2_LIC_LIST.csv'                 # frozen with AMENDMENT_shadow_EMG2.md (ledger)
LIC_RE = re.compile(r'INVESTMENT|CAPITAL FUND|\bLIC\b', re.I)
OLD_RE = re.compile(r'^[A-Z0-9]{3}(_old[0-9]*)?$')
TAG = 'SHADOW EMG2 v1.0 (report 85 T6): lead challenger; not adopted; tracked on paper'
EXPECT = ('Back-test +4.9 a year after costs and yearly tax on seen data; forward estimate +1 to +3; zero is possible; '
          'falls of 40-60% are normal for this line.')


def state_path(): return P.STATE_DIR + '/emg2_state.json'
def out_dir(): return P.REC + '/shadow'
def zero(v): return 0.0
BROK = {'b0': zero, 'ibkr': P.brokerage}


# ---------------------------------------------------------------- state
def new_book(bid, kind, cap, rule, brok='b0', seed=None):
    return dict(id=bid, kind=kind, capital=cap, rule=rule, brok=brok, start=EM_START, cash=cap, seed=seed, rng_state=None, rs={},
                holdings={}, orders=[], E=None, parcel=None, trades=[], divs=[], ntrades=0, nav={EM_START: cap}, units=cap / 100.0,
                spread_paid=0.0, brok_paid=0.0, turnover=0.0, events=[])

def init_state():
    fill = P.next_session(EM_START); books = []; cmps = []
    for tag, cap, s0, rule in SIZES:
        books.append(new_book(f'EMG2_{tag}', 'EMG2', cap, rule))
        books.append(new_book(f'EMG2_{tag}_ibkr', 'EMG2_STRESS', cap, rule, brok='ibkr'))
        books += [new_book(f'EMG2_RND_{tag}_s{i:03d}', 'EMG2_RND', cap, rule, seed=s0 + i) for i in range(1, NRAND + 1)]
        cmps.append(PS.new_cmp0(f'EMG2_CMP_A200_{tag}', {'A200.AU': 1.0}, cap, 0.0, EM_START, fill))
    return dict(record='Big Wins forward paper record -- SHADOW EMG2 v1.0 emerging band monthly momentum + BANDSPREAD (PAPER ONLY; not adopted)',
                amendment='AMENDMENT_shadow_EMG2.md', start_decision=EM_START, fill_day=fill, last_processed=P.prev_session(EM_START),
                decisions=[], data_blocks=[], last={}, books=books, cmps=cmps, bs_open=[], bs_obs=[])

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- book arithmetic
def shares(h): return sum(l[1] for l in h['lots'])
def cost(h): return sum(l[2] for l in h['lots'])
def nav_of(b, last):
    return b['cash'] + sum(shares(h) * last[h['code']]['p'] for h in (b['holdings'][k] for k in sorted(b['holdings'])) if h['code'] in last)
def ev(b, d, s):
    if b['kind'] != 'EMG2_RND': b['events'].append([d, s])

def realise(h, q, proceeds):
    """FIFO parcels (rule 11): returns [buy_date, q, cost, proceeds] parts"""
    out = []; rem = q
    for l in sorted(h['lots'], key=lambda l: l[0]):
        if rem <= 1e-9: break
        x = min(rem, l[1]); c = l[2] * x / l[1]
        out.append([l[0], x, c, proceeds * x / q]); l[1] -= x; l[2] -= c; rem -= x
    h['lots'] = [l for l in h['lots'] if l[1] > 1e-9]
    return out

def record(b, t):
    b['ntrades'] += 1
    if b['kind'] != 'EMG2_RND': b['trades'].append(t)


# ---------------------------------------------------------------- universe table at a month-end (rules 2, 3, 8; section 2 definitions)
_LIC = None
def lic_codes():
    global _LIC
    if _LIC is None:
        _LIC = set(pd.read_csv(LIC_LIST, dtype=str).code) if os.path.exists(LIC_LIST) else set()
    return _LIC

def names():
    s = pd.read_csv(P.STORE + '/symbols.csv', dtype={'Code': str})
    return dict(zip(s.Code.astype(str), s.Name.astype(str)))

def table(D, nm=None, lic=None):
    """EMG2 universe table at the bundle's last day. Returns dict(asof, rows (every class entity with a tv_rank), E, B, C, T, blocked_reason)."""
    nm = nm if nm is not None else names(); lic = lic if lic is not None else lic_codes()
    dates = D['dates']; asof = str(pd.Timestamp(dates[-1]).date()); cols = list(D['cols']); i = len(dates) - 1; N = len(cols)
    assert i >= 262, 'history too short'
    Pv = D['Pv']; C = D['Craw']; V0 = D['V0']; has = np.isfinite(Pv)
    with np.errstate(all='ignore'):
        TV = V0 if asof >= '2026-12-31' else np.where(np.isfinite(C) & (C > 0), V0 * Pv / C, 0.0)   # split-adjusted close x volume (Amendment v1.4)
    TV = np.where(has, np.nan_to_num(TV, nan=0.0), np.nan)
    code = [c.split('#')[0] for c in cols]
    cls_ok = np.array([bool(OLD_RE.match(c)) and c not in lic and not LIC_RE.search(nm.get(c, '')) for c in code])
    w252, w63 = slice(i - 251, i + 1), slice(i - 62, i + 1)
    with np.errstate(all='ignore'):
        n252 = has[w252].sum(0); n63 = has[w63].sum(0)
        m252 = np.where(n252 >= 120, np.nanmedian(TV[w252], axis=0), np.nan); m63 = np.where(n63 >= 30, np.nanmedian(TV[w63], axis=0), np.nan)
    traded5 = has[i - 4:i + 1].any(0)
    rk_ok = np.flatnonzero(cls_ok & traded5 & np.isfinite(m252))
    order = sorted(rk_ok, key=lambda j: (-m252[j], cols[j]))
    vr = np.full(N, np.nan); vr[order] = np.arange(1, len(order) + 1)
    # total-return index (A3/A6): daily (P_t + D_t) / P_prev on adjusted closes, forward-filled over days without a close
    Pf = pd.DataFrame(Pv).ffill().values
    div = np.zeros_like(Pv)
    for r_, lst in D.get('DIVD', {}).items():
        if r_ < len(dates):
            for j, v in lst: div[r_, j] += v
    with np.errstate(all='ignore'):
        g = np.where(has[1:] & np.isfinite(Pf[:-1]) & (Pf[:-1] > 0), (Pv[1:] + div[1:]) / Pf[:-1], 1.0)
        g = np.where(np.isfinite(g) & (g > 0), g, 1.0)
    L = np.vstack([np.zeros((1, N)), np.cumsum(np.log(g), axis=0)])
    nv = np.cumsum(has, axis=0)
    with np.errstate(all='ignore'):
        s1 = np.where(nv[i - 21] - nv[i - 252] >= 150, np.expm1(L[i - 21] - L[i - 252]), np.nan)
        s2 = np.where(nv[i] - nv[i - 126] >= 80, np.expm1(L[i] - L[i - 126]), np.nan)
        hi = np.max(np.where(has[w252], L[w252], -np.inf), axis=0)
        s3 = np.where((n252 >= 200) & np.isfinite(hi) & has[:i + 1].any(0), np.exp(L[i] - hi), np.nan)
        cff = pd.DataFrame(C[i - 5:i + 1]).ffill().values[-1]                                    # raw close on the day or within the previous 5 sessions
        cl_ok = np.isfinite(cff) & (cff >= 0.10)
        # BID_PEG: closes over the last 10 sessions span < 3% and a one-day total return >= +15% within the 30 sessions before that window or inside it
        c10 = C[i - 9:i + 1]; k10 = np.isfinite(c10).sum(0)
        span = np.nanmax(c10, axis=0) / np.nanmin(c10, axis=0) - 1
        jump = (np.where(has[i - 39:i + 1], g[i - 40:i], 1.0) >= 1.15).any(0)
        peg = (k10 >= 5) & (span < 0.03) & jump
    E = cls_ok & np.isfinite(vr) & (vr <= 600) & (m63 >= 100000) & cl_ok & traded5 & np.isfinite(s1) & np.isfinite(s2) & np.isfinite(s3)
    def pct(x, m):
        o = np.full(N, np.nan); k = np.flatnonzero(m)
        if len(k): o[k] = pd.Series(x[k]).rank(method='average').values / len(k)
        return o
    out = dict(asof=asof, rows={}, n_class_ranked=len(order))
    for band, lo, hi_ in (('B', 101, 300), ('C', 301, 600)):
        m = E & (vr >= lo) & (vr <= hi_)
        sc = (pct(s1, m) + pct(s2, m) + pct(s3, m)) / 3.0
        sp = pct(sc, m)
        ids = sorted(np.flatnonzero(m), key=lambda j: (-sc[j], -m252[j], cols[j]))
        out[band] = [cols[j] for j in ids]
        out[band + '_top'] = [cols[j] for j in ids if sp[j] > 0.8]
        out[band + '_bot'] = [cols[j] for j in ids if sp[j] <= 0.2]
        for j in ids: out['rows'][cols[j]] = dict(band=band, score=float(sc[j]), score_pct=float(sp[j]))
    for j in order:
        r = out['rows'].setdefault(cols[j], dict(band=None, score=None, score_pct=None))
        r.update(cid=cols[j], code=code[j], name=nm.get(code[j], ''), tv_rank=int(vr[j]), tv_med252=float(m252[j]), tv_med63=(float(m63[j]) if np.isfinite(m63[j]) else None),
                 close=(float(C[i, j]) if np.isfinite(C[i, j]) else None), close_5=(float(cff[j]) if np.isfinite(cff[j]) else None), traded_on_day=bool(has[i, j]),
                 s1=(float(s1[j]) if np.isfinite(s1[j]) else None), s2=(float(s2[j]) if np.isfinite(s2[j]) else None), s3=(float(s3[j]) if np.isfinite(s3[j]) else None),
                 eligible=bool(E[j]), bid_peg=bool(peg[j]))
    out['T'] = [c for c in out['C_top'] if not out['rows'][c]['bid_peg']]
    out['peg'] = sorted(c for c, r in out['rows'].items() if r['bid_peg'])
    out['blocked_reason'] = f"only {len(out['C'])} names in band C (< 150)" if len(out['C']) < 150 else None
    return out


# ---------------------------------------------------------------- decisions (rules 4-9, 12)
def target_for(b, R, rng_sync=True):
    """ordered target list for a book: EMG2 / stress = T; twin = same count drawn by a persistent seeded random score over band C (redraw p=0.2 a month)"""
    if b['kind'] != 'EMG2_RND':
        return list(R['T'])
    rng = np.random.default_rng(b['seed'])
    if b['rng_state'] is not None: rng.bit_generator.state = b['rng_state']
    rs = b['rs']
    for c in R['C']:                                                                                # band C in score order: draw order fixed by the table
        if c not in rs or rng.random() < REDRAW: rs[c] = float(rng.random())
    b['rng_state'] = rng.bit_generator.state
    b['rs'] = {c: rs[c] for c in R['C']}                                                            # entities that left band C are forgotten
    pool = [c for c in R['C'] if not R['rows'][c]['bid_peg']]
    return sorted(pool, key=lambda c: (-rs[c], c))[:len(R['T'])]

def decide(b, R, d, last, E, duplog):
    rows = R['rows']; brok = BROK[b['brok']]; new = []
    for o in b['orders']: ev(b, d, f"order not filled, dropped: {o['type']} {o['code']}")
    b['orders'] = []
    for x_, y_, _ in duplog:                                                                        # A7 code change carries the holding
        for cid, h in sorted(b['holdings'].items()):
            if h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; ev(b, d, f'code change {x_}->{y_}')
    for cid, h in sorted(b['holdings'].items()):                                                    # rule 7 payout: no close for 20 sessions
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            q = shares(h); p = last[h['code']]['p']; v = q * p
            parts = realise(h, q, v); b['cash'] += v; del b['holdings'][cid]
            record(b, dict(date=d, side='payout', code=h['code'], shares=q, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='rule 7 payout', lots=parts))
            ev(b, d, f"payout {h['code']} at last close {p} ({lc})")
    T = target_for(b, R); tset = set(T); nav = nav_of(b, last)
    est = lambda cid, q, p: max(0.0, q * p * (1 - P.half_spread(rows.get(cid, {}).get('tv_rank'), p)) - brok(q * p))
    proceeds = 0.0; kept = {}
    for cid, h in sorted(b['holdings'].items()):
        p = last[h['code']]['p']; q = shares(h); r = rows.get(cid, {})
        why = 'rule 8 bid peg' if r.get('bid_peg') else ('rule 4 off the list' if cid not in tset else None)
        if why:
            new.append(dict(type='sell', cid=cid, code=h['code'], shares='all', vrank=r.get('tv_rank') or h.get('vrank'), reason=why)); proceeds += est(cid, q, p)
        else: kept[cid] = (h, q * p, p)
    for cid, (h, v, p) in kept.items():                                                             # rule 9 cap: > 10% of NAV -> 7.5%
        if nav > 0 and v > 0.10 * nav:
            k = int(math.floor((v - 0.075 * nav) / p))
            if k > 0:
                new.append(dict(type='sell', cid=cid, code=h['code'], shares=k, vrank=rows.get(cid, {}).get('tv_rank') or h.get('vrank'), reason='rule 9 trim to 7.5%'))
                proceeds += est(cid, k, p)
    nT = len(T)
    if b['rule'] == 'n25':                                                                          # rule 12: A$25k book, up to 25 names
        parcel = nav / 25.0; room = 25 - len(kept)
    else:
        parcel = nav / nT if nT else 0.0; room = nT
    b['parcel'] = parcel
    free = b['cash'] + proceeds
    for cid in T:                                                                                   # rule 5: best first
        if room <= 0: break
        if cid in b['holdings']: continue
        a = min(parcel, free)
        if a < 0.5 * parcel or a <= 0: continue
        r = rows[cid]
        new.append(dict(type='buy', cid=cid, code=r['code'], amount=a, min_amount=0.5 * parcel, vrank=r['tv_rank'], rank=T.index(cid) + 1, reason='rule 5 buy'))
        free -= a; room -= 1
    b['orders'] = new; b['E'] = E
    ev(b, d, f"decision: NAV {nav:.2f} T {nT} parcel {parcel:.2f} orders " + ', '.join(f"{o['type']} {o['code']}" for o in new))
    return new


# ---------------------------------------------------------------- one trading day
def run_day(b, d, mkt):
    cl = mkt['close']; brok = BROK[b['brok']]
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                                    # splits
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] *= s
            ev(b, d, f"split {h['code']} x{s:g}")
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                                    # dividends as cash (shares held before d)
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    for o in [o for o in b['orders'] if o['type'] == 'sell']:                                       # rule 1: sells first
        h = b['holdings'].get(o['cid']); p = cl.get(o['code'])
        if h is None: continue
        if p is None: ev(b, d, f"sell {o['code']} not filled (no close); decided again next month-end"); continue
        q = shares(h) if o['shares'] == 'all' else min(o['shares'], shares(h)); hh = P.half_spread(o.get('vrank'), p); bk = brok(q * p)
        pr = max(0.0, q * p * (1 - hh) - bk); b['cash'] += pr; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk; b['turnover'] += q * p
        parts = realise(h, q, pr)
        if not h['lots']: del b['holdings'][o['cid']]
        record(b, dict(date=d, side='sell', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(pr, 2), reason=o['reason'], lots=parts))
    for o in [o for o in b['orders'] if o['type'] == 'buy']:
        a = min(o['amount'], b['cash']); p = cl.get(o['code'])
        if a < o['min_amount'] or a <= 0: ev(b, d, f"buy {o['code']} skipped: cash {a:.2f} under half a parcel"); continue
        if p is None: ev(b, d, f"buy {o['code']} skipped: no close on the fill day (may be bought at a later decision)"); continue
        hh = P.half_spread(o.get('vrank'), p); q = int(math.floor((a - brok(a)) / (p * (1 + hh))))
        if q <= 0: ev(b, d, f"buy {o['code']} skipped: 0 shares"); continue
        bk = brok(q * p); paid = q * p * (1 + hh) + bk; b['cash'] -= paid
        b['spread_paid'] += q * p * hh; b['brok_paid'] += bk; b['turnover'] += q * p
        h = b['holdings'].setdefault(o['cid'], dict(code=o['code'], lots=[], vrank=o.get('vrank'))); h['lots'].append([d, q, paid]); h['vrank'] = o.get('vrank')
        record(b, dict(date=d, side='buy', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(-paid, 2), reason=o['reason']))
    b['orders'] = []


# ---------------------------------------------------------------- BANDSPREAD (section 4): no book, no decision
def bs_open(s, R, d):
    me = d; x = P.next_session(d)
    while not P.is_month_end(x): x = P.next_session(x)
    per = dict(decision=d, start=P.next_session(d), end=P.next_session(x), groups={}, m={}, a200=None)
    for band in ('B', 'C'):
        per['groups'][band] = dict(TOP=[R['rows'][c]['code'] for c in R[band + '_top']], BOT=[R['rows'][c]['code'] for c in R[band + '_bot']],
                                   ALL=[R['rows'][c]['code'] for c in R[band]])
        for c in R[band]:
            r = R['rows'][c]; per['m'][r['code']] = dict(e=None, q=1.0, dv=0.0, p=r['close_5'])        # p = last known close (decision day or within 5 sessions)
    s['bs_open'].append(per)

def bs_day(s, d, mkt, log):
    cl = mkt['close']; done = []
    for per in s['bs_open']:
        if d < per['start']: continue
        for code, m in per['m'].items():
            if d > per['start']:
                sp = mkt['split'].get(code)
                if sp and sp > 0: m['q'] *= sp
                v = mkt['div'].get(code)
                if v: m['dv'] += m['q'] * v
            if code in cl: m['p'] = cl[code]
            if d == per['start']: m['e'] = m['p']                                                   # entry: the start session's close (else last known)
        a = per['a200'] = per['a200'] or dict(e=None, q=1.0, dv=0.0, p=None)
        if d > per['start'] and mkt['div'].get('A200'): a['dv'] += a['q'] * mkt['div']['A200']
        if 'A200' in cl: a['p'] = cl['A200']
        if d == per['start']: a['e'] = a['p']
        if d == per['end']:
            ret = lambda m: (m['q'] * m['p'] + m['dv']) / m['e'] - 1 if m['e'] and m['p'] else None
            o = dict(decision=per['decision'], start=per['start'], end=d)
            ra = ret(a)
            for band, gr in per['groups'].items():
                mean = {}
                for k, lst in gr.items():
                    v = [ret(per['m'][c]) for c in lst]; v = [x for x in v if x is not None]
                    mean[k] = float(np.mean(v)) if v else None; o[f'{band}_{k}_n'] = len(v)
                o[f'{band}_TOP_minus_ALL'] = None if None in (mean['TOP'], mean['ALL']) else mean['TOP'] - mean['ALL']
                o[f'{band}_BOT_minus_ALL'] = None if None in (mean['BOT'], mean['ALL']) else mean['BOT'] - mean['ALL']
                o[f'{band}_TOP_minus_A200'] = None if None in (mean['TOP'], ra) else mean['TOP'] - ra
            o['A200'] = ra; s['bs_obs'].append(o); done.append(per)
            log('EMG2 BANDSPREAD', per['decision'], '->', d, 'band C TOP-ALL', o.get('C_TOP_minus_ALL'))
    s['bs_open'] = [p for p in s['bs_open'] if p not in done]

def nw_t(x, lag=1):
    x = np.asarray([v for v in x if v is not None], float); n = len(x)
    if n < 3: return None
    m = x.mean(); e = x - m; g0 = (e @ e) / n; v = g0
    for k in range(1, lag + 1): v += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(m / math.sqrt(v / n)) if v > 0 else None

def bs_summary(s):
    out = {}
    for k in ('C_TOP_minus_ALL', 'C_BOT_minus_ALL', 'C_TOP_minus_A200', 'B_TOP_minus_ALL', 'B_BOT_minus_ALL', 'B_TOP_minus_A200'):
        v = [o.get(k) for o in s['bs_obs'] if o.get(k) is not None]
        out[k] = dict(n=len(v), mean_a_year=(float(np.mean(v)) * 12 if v else None), t_nw1=nw_t(v))
    return out


# ---------------------------------------------------------------- month-end
_BC = {}
def get_bundle(d, log):
    """(D, blocked, source) of month-end d: paper_shadow.bundle_for (the SHADOW lines' bundle: forward store cut at d, A4(b), A7(c); from
    31 Dec 2026 the H82 bundle), cached for the day so EARLY's C2 controls reuse it; paper_daily clears it with clear_bundle()."""
    if _BC.get('d') == d: return _BC['v']
    import paper_shadow as SH
    _BC.clear(); v = SH.bundle_for(d, log); _BC.update(d=d, v=v); return v

def clear_bundle(): _BC.clear()

def write_list(R, d):
    rows = []
    T = {c: k for k, c in enumerate(R['T'], 1)}
    for cid, r in R['rows'].items():
        rows.append(dict(date=d, cid=cid, code=r['code'], name=r['name'][:40], tv_rank=r['tv_rank'], tv_med252=r['tv_med252'], tv_med63=r['tv_med63'], close=r['close'],
                         close_within_5=r['close_5'], traded_on_day=r['traded_on_day'], s1=r['s1'], s2=r['s2'], s3=r['s3'], eligible=r['eligible'], band=r['band'],
                         score=r['score'], score_pct=r['score_pct'], bid_peg=r['bid_peg'], target_rank=T.get(cid)))
    df = pd.DataFrame(rows).sort_values('tv_rank')
    os.makedirs(out_dir(), exist_ok=True)
    return P.write_csv(f'{out_dir()}/emg2_list_{d}.csv', df)

def step(s, d, mkt, log, bundle=None):
    last = s['last']
    watch = {'A200'} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: run_day(b, d, mkt)
    for c in s['cmps']: PS.cmp_day0(c, d, mkt)
    bs_day(s, d, mkt, log)
    info = None
    if d >= EM_START and P.is_month_end(d):
        D, blocked, src = get_bundle(d, log) if bundle is None else bundle
        R = table(D); duplog = D.get('duplog', []); del D
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else R['blocked_reason']
        files = {f'shadow/emg2_list_{d}.csv': write_list(R, d)}
        if why:
            s['data_blocks'].append([d, f'EMG2 data block: {why}; no decision, holdings kept']); log('EMG2', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src, files_sha256=files)
        else:
            for r in R['rows'].values():
                if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); orows = []
            for b in s['books']:
                for o in decide(b, R, d, last, E, duplog):
                    if b['kind'] != 'EMG2_RND':
                        orows.append(dict(book=b['id'], type=o['type'], code=o['code'], amount_AUD=round(o['amount'], 2) if 'amount' in o else None,
                                          shares=o.get('shares'), list_rank=o.get('rank'), tv_rank=o.get('vrank'), fill='close of ' + E, rule=o['reason']))
            files[f'shadow/emg2_orders_{d}.csv'] = P.write_csv(f'{out_dir()}/emg2_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'type', 'code', 'amount_AUD', 'shares', 'list_rank', 'tv_rank', 'fill', 'rule']))
            bs_open(s, R, d)
            s['decisions'].append(d)
            info = dict(asof=d, fill_day=E, source=src, files_sha256=files, band_C=len(R['C']), T=[R['rows'][c]['code'] for c in R['T']], bid_peg=R['peg'])
            log('EMG2', d, f"decision; band C {len(R['C'])}, T {len(R['T'])}: {info['T'][:8]} ...; orders (100k) {sum(1 for o in orows if o['book'] == 'EMG2_100k')}")
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring EMG2 up to trading day d (after the H82 day and the M3/E3, ACC and CXL steps). Returns a small dict for the ledger (None before the start)."""
    try:
        if d < EM_START: return None
        s = load()
        if s is None: s = init_state(); log('SHADOW EMG2 state created; first decision', EM_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('SHADOW EMG2', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('SHADOW EMG2 ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard rows (placed first: owner decision D-2)
def twr(b, nav): return (nav / b['units']) / 100.0 - 1 if b['units'] > 0 else float('nan')

def worst_fall(b):
    v = [b['nav'][k] for k in sorted(b['nav'])]
    if len(v) < 2: return 0.0
    v = np.array(v, float); return float(np.min(v / np.maximum.accumulate(v) - 1))

def tracking_error(b, c):
    me = [x for x in sorted(b['nav']) if x >= EM_START and P.is_month_end(x) and x in c['nav']]
    if len(me) < 13: return None
    rb = [PS.ret_at(b, x) for x in me]; rc = [PS.ret_at(c, x) for x in me]
    ex = [(1 + rb[i]) / (1 + rb[i - 1]) - (1 + rc[i]) / (1 + rc[i - 1]) for i in range(1, len(me))]
    return float(np.std(ex, ddof=1) * math.sqrt(12))

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        for tag, cap, _, _ in SIZES:
            rows.append(dict(asof=d, book=f'EMG2_{tag}', kind='SHADOW_EMG2', capital=cap, note=f'{TAG}; not started: first decision {EM_START}, fills at the close of {P.next_session(EM_START)}'))
        md.append(f'| **EMG2 (lead challenger; AMENDMENT_shadow_EMG2.md)** | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; '
                  f'A$100k and A$25k, 100 random twins each, BANDSPREAD measurement line. Expectation: {EXPECT} |')
        return rows, md, hold
    last = s['last']; cm = {c['id']: c for c in s['cmps']}; bs = bs_summary(s)
    f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else (f'{x:+.2%}' if isinstance(x, float) else str(x))
    sc = bs['C_TOP_minus_ALL']
    md.append(f"| **BANDSPREAD band C (EMG2 signal spread)** | — | {f(sc['mean_a_year'])} a year | t {'' if sc['t_nw1'] is None else round(sc['t_nw1'], 2)} over {sc['n']} months (Newey-West lag 1); "
              f"band B TOP-ALL {f(bs['B_TOP_minus_ALL']['mean_a_year'])} a year; history +16.9 a year, t 4.5 (2018-Oct 2026) |")
    rows.append(dict(asof=d, book='EMG2_BANDSPREAD_C', kind='SHADOW_EMG2 measurement', return_since_start=sc['mean_a_year'],
                     note=f"band C TOP-ALL mean a year; t(NW1) {sc['t_nw1']}; months {sc['n']}; " + json.dumps({k: v['mean_a_year'] for k, v in bs.items()})))
    for tag, cap, _, _ in SIZES:
        b = next(x for x in s['books'] if x['id'] == f'EMG2_{tag}'); a2 = cm[f'EMG2_CMP_A200_{tag}']; st_ = next(x for x in s['books'] if x['id'] == f'EMG2_{tag}_ibkr')
        nav = nav_of(b, last); r = twr(b, nav); ra = twr(a2, P.nav_of(a2, last))
        rv = np.array([twr(x, nav_of(x, last)) for x in s['books'] if x['kind'] == 'EMG2_RND' and x['capital'] == cap])
        sale = lambda cid, code, q, p, b=b: q * p * P.half_spread(b['holdings'][cid].get('vrank'), p)
        kept, sold = PS.after_tax_engine(b, last, s['last_processed'], sale); rk, rs = PS.at_return(kept, b['units']), PS.at_return(sold, b['units'])
        ak, as_ = PS.after_tax_cmp0(a2, last, s['last_processed']); rak, ras = PS.at_return(ak, a2['units']), PS.at_return(as_, a2['units'])
        te = tracking_error(b, a2); pr = float(np.mean(rv < r)) if len(rv) else None; rmed = float(np.median(rv)) if len(rv) else None
        rst = twr(st_, nav_of(st_, last))
        rows.append(dict(asof=d, book=b['id'], kind='SHADOW_EMG2', capital=cap, contributed=0.0, nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2), cash=round(b['cash'], 2),
                         holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), pct_of_random=(None if pr is None else round(pr, 3)),
                         random_median_return=(None if rmed is None else round(rmed, 5)), vs_random_median=(None if rmed is None else round(r - rmed, 5)),
                         a200_b0_return=round(ra, 5), vs_a200_b0=round(r - ra, 5), after_tax_kept_AUD=round(kept, 2), after_tax_sold_AUD=round(sold, 2),
                         ret_after_tax_kept=round(rk, 5), ret_after_tax_sold=round(rs, 5), a200_b0_ret_after_tax_kept=round(rak, 5), a200_b0_ret_after_tax_sold=round(ras, 5),
                         vs_a200_b0_after_tax_kept=round(rk - rak, 5), vs_a200_b0_after_tax_sold=round(rs - ras, 5), vs_a200_b0_engine_sold_fund_kept=round(rs - rak, 5),
                         dividends_fy=round(sum(x[4] for x in b['divs']), 2), tracking_error=(None if te is None else round(te, 4)),
                         note=f"{TAG}; brokerage A$0; IBKR-cost stress book {f(rst)}; turnover A$ {b['turnover']:,.0f}; spread paid A$ {b['spread_paid']:,.2f}; worst fall {worst_fall(b):.1%}; {EXPECT}"))
        rows.append(dict(asof=d, book=st_['id'], kind='SHADOW EMG2 cost stress', capital=cap, nav=round(nav_of(st_, last), 2), cash=round(st_['cash'], 2), holdings=len(st_['holdings']),
                         return_since_start=round(rst, 5), note=f"IBKR brokerage max(A$6.60, 0.088%); brokerage paid A$ {st_['brok_paid']:,.2f}"))
        if len(rv):
            rows.append(dict(asof=d, book=f'EMG2_RND_{tag} ({len(rv)} seeds)', kind='SHADOW EMG2 random twins', capital=cap, return_since_start=round(rmed, 5),
                             note=f'median; 5th-95th pct {np.percentile(rv, 5):.4f} to {np.percentile(rv, 95):.4f}; random order inside band C, same count of names'))
        rows.append(dict(asof=d, book=a2['id'], kind='SHADOW comparator', capital=cap, contributed=0.0, nav=round(P.nav_of(a2, last), 2), nav_q6_at_70pct=round(P.nav_of(a2, last), 2),
                         cash=round(a2['cash'], 2), holdings=sum(1 for u in a2['fund_units'].values() if u > 0), open_orders=len(a2['pending']),
                         return_since_start=round(ra, 5), note=f"own clock from {s['start_decision']}; A$0 brokerage; EODHD proxy"))
        md.append(f"| **{b['id']} (EMG2, lead challenger)** | {nav:,.2f} | {f(r)} | % of {len(rv)} twins below: {'' if pr is None else round(pr, 3)} (twin median {f(rmed)}); "
                  f"vs A200 (A$0) {f(r - ra)}; after tax sold vs A200 kept {f(rs - rak)}; holdings {len(b['holdings'])}; cash {b['cash']:,.2f}; worst fall {worst_fall(b):.1%}; "
                  f"TE {'n/a (<12 months)' if te is None else f'{te:.1%}'}; IBKR-cost book {f(rst)} |")
        hs_ = ', '.join(f"{h['code']} {shares(h):,.0f}" for h in b['holdings'].values())
        if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no shares'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    md.append(f'| EMG2 expectation | | | {EXPECT} |')
    return rows, md, hold
