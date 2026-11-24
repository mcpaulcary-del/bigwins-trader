# Big Wins forward PAPER record -- aggressive side lines EMG2_MOON_TOP5, EMG2_MOON_NOLOT5, MOON_LEG2 (AMENDMENT_shadow_moon_v1.md, ledger seq 94;
# information only, never evidence for or against EMG2; no proposal before the December 2028 review).
#   common: EMG2_18_SIM engine (paper_emg2s: table, fills, costs, L1 cap, A$500 minimum, payout, A7, BID_PEG, rule-14 data block), NO shield,
#           n = min(NMAX, floor(min(acct, 10k) / 550)), each buy = min(parcel, 4.5% x 20-session median traded value), cut parcel < A$520 skipped
#           (next candidate), proportional scale-down when the cash is short; month-end counter as C6.
#   TOP5   NMAX 5, lottery filter kept, L4 (off T sold); twins stratified (seq 83), seeds 8830000+i.
#   NOLOT5 the same without the lottery filter; twins seeds 8830000+i (paired with TOP5 on purpose).
#   LEG2   ranks 301-1000 eligible, not lottery-lap, not BID_PEG; buy if 252-session TR >= +100% (150 priced sessions) and s3 >= 0.75, nearest
#          the high first, NMAX 10; sell if s3 < 0.70 (or missing) or age >= 12 month-ends; twins: top fifth of persistent random scores over the
#          pool (redraw p 0.2), sold when out of it, seeds 8820000+i.
# Frozen functions are CALLED, never changed. PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state files
# STATE_DIR/moon_<line>_state.json; never writes another line's state (reads emg2s_state.json read-only for the gap to EMG2_18_REF). Idempotent.
import os, json, math, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM, paper_emg2s as ES, paper_emg2bt as BT, paper_sidelines as SL

MOON_START = '2026-11-30'
CAP = ES.CAP; RESERVE = ES.RESERVE; MIN_ORDER = ES.MIN_ORDER; SLOT_UNIT = ES.SLOT_UNIT
LIQ = 0.045; LIQ_MIN = 520.0; M20 = 20; M20_MIN = 10
LEG_LO, LEG_HI = 301, 1000; LEG_RET = 1.0; LEG_NV = 150; LEG_BUY_S3 = 0.75; LEG_SELL_S3 = 0.70; LEG_AGE = 12
NRAND = 100; REDRAW = 0.2
TAG = 'aggressive side line (AMENDMENT_shadow_moon_v1.md; information only; never evidence for or against EMG2; no proposal before Dec 2028)'

LINES = {
    'top5': dict(key='moon_top5', name='MOON_TOP5', book='EMG2_MOON_TOP5', twin='MOON_TOP5_RND', kind='MOON_TOP5', nmax=5, mode='T', lot='frozen', seed0=8830000,
                 what='EMG2_18_SIM at n = 5, lottery filter kept, no shield'),
    'nolot5': dict(key='moon_nolot5', name='MOON_NOLOT5', book='EMG2_MOON_NOLOT5', twin='MOON_NOLOT5_RND', kind='MOON_NOLOT5', nmax=5, mode='T', lot='none', seed0=8830000,
                   what='EMG2_18_SIM at n = 5, no lottery filter, no shield'),
    'leg2': dict(key='moon_leg2', name='MOON_LEG2', book='MOON_LEG2', twin='MOON_LEG2_RND', kind='MOON_LEG2', nmax=10, mode='LEG2', lot='none', seed0=8820000,
                 what='second leg after a doubling, ranks 301-1000, n <= 10, no shield'),
}


def state_path(cfg): return P.STATE_DIR + f"/{cfg['key']}_state.json"
def out_dir(): return P.REC + '/shadow'
def month_end(d): return P.is_month_end(d)                                                     # (tests patch this name only)

def new_book(bid, kind, seed=None):
    b = ES.new_book(bid, kind, None, seed); b['nav'] = {MOON_START: CAP}; return b

def init_state(cfg):
    books = [new_book(cfg['book'], cfg['kind'])] + [new_book(f"{cfg['twin']}_s{i:03d}", cfg['kind'] + '_RND', seed=cfg['seed0'] + i) for i in range(1, NRAND + 1)]
    return dict(record=f"Big Wins forward paper record -- aggressive side line {cfg['name']} ({cfg['what']}) (PAPER ONLY; information only)",
                amendments=['AMENDMENT_shadow_moon_v1.md', 'AMENDMENT_twins_buyable_set.md'], line=cfg['name'], start_decision=MOON_START,
                fill_day=P.next_session(MOON_START), last_processed=P.prev_session(MOON_START), decisions=[], data_blocks=[], me=0, last={}, books=books)

def load(cfg):
    p = state_path(cfg)
    return json.load(open(p)) if os.path.exists(p) else None

def save(cfg, s):
    p = state_path(cfg); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- month-end context (once per day for the three lines)
def context(D, blocked):
    R = EM.table(D); rows = R['rows']; asof = R['asof']
    Pv, Cr, V0 = D['Pv'], D['Craw'], D['V0']; has = np.isfinite(Pv); i = Pv.shape[0] - 1; col = {c: j for j, c in enumerate(D['cols'])}
    with np.errstate(all='ignore'):
        TV = V0 if asof >= '2026-12-31' else np.where(np.isfinite(Cr) & (Cr > 0), V0 * Pv / Cr, 0.0)       # as paper_emg2.table
    started = np.cumsum(has, axis=0) > 0
    TVz = np.where(has, np.nan_to_num(TV, nan=0.0), np.where(started, 0.0, np.nan))[i - M20 + 1:i + 1]     # no trade after the first price = 0 (acct3)
    with np.errstate(all='ignore'):
        m20 = np.where(np.isfinite(TVz).sum(0) >= M20_MIN, np.nanmedian(TVz, axis=0), np.nan)
    L = BT.tr_log(D); nv = np.cumsum(has, axis=0)
    r252 = np.where(nv[i] - nv[i - 252] >= LEG_NV, np.expm1(L[i] - L[i - 252]), np.nan)
    lap = SL.lottery_wide(D, R)
    pool = sorted((c for c, r in rows.items() if r.get('tv_rank') is not None and LEG_LO <= r['tv_rank'] <= LEG_HI and (r.get('close_5') or 0) >= 0.10
                   and (r.get('tv_med63') or 0) >= 100000 and None not in (r.get('s1'), r.get('s2'), r.get('s3')) and not lap.get(c, True) and not r['bid_peg']),
                  key=lambda c: (rows[c]['tv_rank'], c))
    ret = {c: float(r252[col[c]]) for c in pool if c in col and np.isfinite(r252[col[c]])}
    cand = sorted((c for c in pool if ret.get(c, -1) >= LEG_RET and rows[c]['s3'] >= LEG_BUY_S3), key=lambda c: (-rows[c]['s3'], c))
    return dict(R=R, why=('market-wide verdict failed (H82 Q4 data block of the day)' if blocked else R['blocked_reason']), lot=ES.lottery(D, R),
                m20={c: float(m20[j]) for c, j in col.items() if np.isfinite(m20[j])}, pool=pool, cand=cand, ret252=ret, duplog=D.get('duplog', []))


def leg2_twin_list(b, pool):
    rng = np.random.default_rng(b['seed'])
    if b['rng_state'] is not None: rng.bit_generator.state = b['rng_state']
    rs = b['rs']
    for c in pool:
        if c not in rs or rng.random() < REDRAW: rs[c] = float(rng.random())
    b['rng_state'] = rng.bit_generator.state; b['rs'] = {c: rs[c] for c in pool}
    return sorted(pool, key=lambda c: (-rs[c], c))[:int(math.floor(0.2 * len(pool) + 1e-9))]


# ---------------------------------------------------------------- decision
def decide(cfg, b, X, d, me, last, E):
    R = X['R']; rows = R['rows']; new = []
    for o in b['orders']: ES.ev(b, d, f"order not filled, dropped: {o['type']} {o['code']}")
    b['orders'] = []
    for x_, y_, _ in X['duplog']:                                                                     # A7 code change carries the holding
        for cid, h in sorted(b['holdings'].items()):
            if h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; ES.ev(b, d, f'code change {x_}->{y_}')
    for cid, h in sorted(b['holdings'].items()):                                                      # payout: no close for 20 sessions
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            q = ES.shares(h); p = last[h['code']]['p']; v = q * p
            parts = ES.realise(h, q, v); b['cash'] += v; del b['holdings'][cid]
            ES.record(b, dict(date=d, side='payout', code=h['code'], shares=q, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='payout (20 sessions without a close)', lots=parts))
    lot = X['lot'] if cfg['lot'] == 'frozen' else {}
    if cfg['mode'] == 'T':
        T, _ = ES.lists_for(b, R, lot if cfg['lot'] == 'frozen' else {c: False for c in rows}); keep = set(T)
    else:
        T = leg2_twin_list(b, X['pool']) if ES.rnd(b) else list(X['cand']); keep = set(T) if ES.rnd(b) else None
    nav = ES.nav_of(b, last); sizing = min(nav, CAP)
    n = max(0, min(cfg['nmax'], int(math.floor(sizing / SLOT_UNIT + 1e-9)))); parcel = sizing / n if n else 0.0
    proceeds = 0.0; kept = []
    for cid, h in sorted(b['holdings'].items()):
        p = last[h['code']]['p']; q = ES.shares(h); age = me - h['k']; r = rows.get(cid, {})
        if r.get('bid_peg'): why = 'bid peg'
        elif cfg['mode'] == 'T': why = 'L4 off T' if cid not in keep else None
        elif ES.rnd(b): why = 'LEG2 twin: out of the random top fifth' if cid not in keep else None
        elif r.get('s3') is None or r['s3'] < LEG_SELL_S3: why = f"LEG2: more than 30% below the 252-session high (s3 {r.get('s3')})"
        elif age >= LEG_AGE: why = f'LEG2: 12th month-end after purchase (age {age})'
        else: why = None
        if why: new.append(dict(type='sell', cid=cid, code=h['code'], reason=why)); proceeds += max(0.0, q * p * (1 - ES.half(p)) - ES.brok(q * p))
        else: kept.append(cid)
    kept_value = sum(ES.shares(b['holdings'][c]) * last[b['holdings'][c]['code']]['p'] for c in kept)
    cands = []; skipped = 0
    for rank, cid in enumerate(T, 1):
        if len(cands) >= n - len(kept): break
        r = rows.get(cid)
        if r is None or cid in b['holdings'] or lot.get(cid, cfg['lot'] == 'frozen') or r['bid_peg'] or not r['traded_on_day'] or r['close'] is None: continue
        amt = min(parcel, LIQ * X['m20'].get(cid, 0.0))
        if amt < LIQ_MIN: skipped += 1; continue                                                     # cut parcel under A$520: next candidate
        cands.append((rank, cid, amt))
    avail = min(b['cash'] + proceeds - RESERVE, CAP - kept_value); tot = sum(a for _, _, a in cands)
    sc = min(1.0, avail / tot) if tot > 0 else 0.0
    for rank, cid, amt in cands:
        each = math.floor(amt * sc * 100) / 100; ref = rows[cid]['close']
        if each < MIN_ORDER: ES.ev(b, d, f"buy {rows[cid]['code']} not sent: A${each:.2f} under A$500 after the cash scale-down"); continue
        q = int(math.floor((each - ES.brok(each)) / ref))
        if q > 0: new.append(dict(type='buy', cid=cid, code=rows[cid]['code'], shares=q, ref=ref, amount=each, rank=rank, k=me, vrank=rows[cid]['tv_rank'],
                                  reason=('L5 buy' if cfg['mode'] == 'T' else 'LEG2 buy') + ('' if each >= parcel - 0.01 else ' (cut to 4.5% of 20-session median value)' if sc >= 1 else ' (cash short)')))
    b['orders'] = new; b['E'] = E
    ES.ev(b, d, f"decision (month-end {me}): NAV {nav:.2f} n {n} parcel {parcel:.2f} liquidity-skipped {skipped} orders " + ', '.join(f"{o['type']} {o['code']}" for o in new))
    return new


def step(cfg, s, d, mkt, log, ctx):
    last = s['last']; nm = cfg['name']
    watch = {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: ES.run_day(b, d, mkt)
    info = None
    if d >= MOON_START and month_end(d):
        s['me'] += 1; X = ctx(d)
        if X['why']:
            s['data_blocks'].append([d, f"EMG2 data block: {X['why']}; no decision, holdings kept (counts as a month-end for the age)"]); log(nm, d, 'data block:', X['why'])
            info = dict(asof=d, blocked=True, reason=X['why'], me=s['me'])
        else:
            for r in X['R']['rows'].values():
                if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); me = s['me']; orows = []
            for b in s['books']:
                new = decide(cfg, b, X, d, me, last, E)
                if not ES.rnd(b):
                    orows += [dict(book=b['id'], type=o['type'], code=o['code'], shares=o.get('shares', 'all'), amount_AUD=o.get('amount'), list_rank=o.get('rank'),
                                   m20_AUD=(round(X['m20'].get(o['cid'], 0.0)) if o['type'] == 'buy' else None), fill='close of ' + E, rule=o['reason']) for o in new]
            s['decisions'].append(d); os.makedirs(out_dir(), exist_ok=True)
            fn = f"{cfg['key']}_orders_{d}.csv"
            f = P.write_csv(f'{out_dir()}/{fn}', pd.DataFrame(orows, columns=['book', 'type', 'code', 'shares', 'amount_AUD', 'list_rank', 'm20_AUD', 'fill', 'rule']))
            info = dict(asof=d, fill_day=E, me=me, files_sha256={f'shadow/{fn}': f}, orders=sum(1 for o in orows if o['book'] == cfg['book']),
                        list_n=(len(X['R']['T']) if cfg['mode'] == 'T' else len(X['cand'])), pool_n=(len(X['pool']) if cfg['mode'] == 'LEG2' else None))
            log(nm, d, 'decision', len(s['decisions']) - 1, 'month-end', me, info['orders'], 'orders')
    for b in s['books']: b['nav'][d] = round(ES.nav_of(b, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """The three lines up to trading day d (after the other side lines, before the bundle is cleared). {} before the start."""
    out = {}; cache = {}
    def ctx(x):
        if x not in cache:
            D, blocked, src = EM.get_bundle(x, log); cache.clear(); cache[x] = context(D, blocked); del D
        return cache[x]
    for cfg in LINES.values():
        try:
            if d < MOON_START: continue
            s = load(cfg)
            if s is None: s = init_state(cfg); log(cfg['name'], 'side line state created; first decision', MOON_START)
            decs = []
            for x in P.sessions_between(s['last_processed'], d):
                m = mkt if (x == d and mkt is not None) else P.load_day(x)
                if m is None: log(cfg['name'], x, 'no bulk file; stops here and resumes on a later run'); break
                info = step(cfg, s, x, m, log, ctx); save(cfg, s)
                if info: decs.append(info)
            out[cfg['key']] = dict(last_processed=s['last_processed'], month_ends=s['me'], state_sha256=P.L.sha(state_path(cfg)), decisions=decs or None)
        except Exception as e:
            log(cfg['name'], 'side line ERROR (no other line affected):', repr(e)); log(traceback.format_exc())
            out[cfg['key']] = dict(error=repr(e)[:300])
    return out


# ---------------------------------------------------------------- scorecard
def scorecard_rows(d):
    rows, md, hold = [], [], []
    es = ES.load(); ref = None if es is None else next((x for x in es['books'] if x['id'] == 'EMG2_18_REF'), None)
    rref = None if ref is None else ES.nav_of(ref, es['last']) / CAP - 1
    f = lambda x: '' if x is None else f'{x:+.2%}'
    tw5 = {}
    for cfg in LINES.values():
        s = load(cfg)
        if s is None:
            md.append(f"| **{cfg['name']}** `{cfg['book']}` | — | — | {cfg['what']}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$10,000, 100 twins (seeds {cfg['seed0']}+i); "
                      f"no proposal before the Dec 2028 review (five-part bar); {TAG} |")
            continue
        last = s['last']; ret = lambda b: ES.nav_of(b, last) / CAP - 1
        b = next(x for x in s['books'] if x['id'] == cfg['book']); r = ret(b)
        twr = {x['seed']: ret(x) for x in s['books'] if ES.rnd(x)}; tw = np.array(list(twr.values()))
        if cfg['mode'] == 'T': tw5[cfg['key']] = twr
        pr = float(np.mean(tw < r)) if len(tw) else None
        g = [ES.shares(h) * last[h['code']]['p'] / EM.cost(h) - 1 for h in b['holdings'].values() if h['code'] in last and EM.cost(h) > 0]
        up, dn = sum(x >= 1.0 for x in g), sum(x <= -0.5 for x in g)
        extra = ''
        if cfg['key'] == 'moon_nolot5' and 'moon_top5' in tw5:
            pd_ = [twr[k] - tw5['moon_top5'][k] for k in twr if k in tw5['moon_top5']]
            if pd_: extra = f"; filter effect on random 5-name books (twin i NOLOT5 - TOP5) median {f(float(np.median(pd_)))} (fact)"
        note = (f"{cfg['what']}; month-ends {s['me']}; FACT: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, modelled spread A$ {b['spread_paid']:,.2f}, holdings {len(b['holdings'])} "
                f"(>= +100%: {up}, <= -50%: {dn}), worst fall {EM.worst_fall(b):.1%}{extra}; MOSTLY LUCK: gap to EMG2_18_REF {f(None if rref is None else r - rref)}, "
                f"percentile among own twins {'' if pr is None else f'{pr:.2f}'}; {TAG}")
        rows.append(dict(asof=d, book=b['id'], kind=f"side line {cfg['name']} (information only)", capital=CAP, nav=round(ES.nav_of(b, last), 2), cash=round(b['cash'], 2),
                         holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), pct_of_random=(None if pr is None else round(pr, 3)),
                         random_median_return=(None if not len(tw) else round(float(np.median(tw)), 5)), note=note))
        md.append(f"| **{cfg['name']}** `{cfg['book']}` | {ES.nav_of(b, last):,.2f} | {f(r)} | {cfg['what']}; facts: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, "
                  f"spread A$ {b['spread_paid']:,.2f}, holdings {len(b['holdings'])} (>= +100%: {up}, <= -50%: {dn}), worst fall {EM.worst_fall(b):.1%}{extra}; mostly luck: "
                  f"vs REF {f(None if rref is None else r - rref)}" + ('' if pr is None else f", % of {len(tw)} own twins below {pr:.2f}") + "; no proposal before Dec 2028 |")
        hs_ = ', '.join(f"{h['code']} {ES.shares(h):,.0f} ({ES.shares(h) * last[h['code']]['p'] / EM.cost(h) - 1:+.0%}, age {s['me'] - h['k']})" for h in b['holdings'].values() if h['code'] in last)
        if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no holdings'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
