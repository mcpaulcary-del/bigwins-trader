# Big Wins forward PAPER record -- PAPER line EMG2_18_SIM_BT (AMENDMENT_shadow_EMG2_18_BT.md; information only):
#   registered EMG2-18 (as EMG2_18_REF of paper_emg2s.py: L1-L5, L9, lottery class, IBKR costs) + the band-trend switch of report 96:
#   BT1 equal-weight total-return index of band C (eligible traded-value ranks 301-600), re-formed at each month-end, buy-and-hold inside the month;
#   BT2 ON iff the index >= the mean of its last 10 month-end levels (this one included); BT3 OFF: sell every share at the next close and put the
#   cash less A$50 in the ASX 200 fund (A200), buy no share; BT4 ON: the fund is not on T, so rule L4 sells it; the registered rules run.
#   EMG2_18_SIM_BT + 100 random twins EMG2_18_BT_RND_s001..s100 (seeds 8780000+i), one state for all.
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state file STATE_DIR/emg2bt_state.json; never reads or writes the
# H82 state or another line's state (reads paper_emg2s' state for the BT - REF reading of the scorecard only). Idempotent and resumable.
import os, json, math, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM, paper_emg2s as ES

BT_START = '2026-11-30'
CAP, RESERVE, MIN_ORDER = ES.CAP, ES.RESERVE, ES.MIN_ORDER
FUND = 'A200'; FUND_CID = 'A200#FUND'; FUND_HALF = 0.0005      # report 96's fund model: 0.05% a side (+ IBKR brokerage)
MONTHS = 10; TOPUP = 0.10                                        # BT2 window; report 96's 10% band for a later fund top-up
NRAND = 100; SEED0 = 8780000
TAG = 'PAPER line EMG2-18 + band-trend switch into A200 (information only; never evidence for or against EMG2)'


def state_path(): return P.STATE_DIR + '/emg2bt_state.json'
def out_dir(): return P.REC + '/shadow'
def month_end(d): return P.is_month_end(d)                                                     # (tests patch this name only)
def half(code, p): return max(FUND_HALF, 0.5 * P.tick(p) / p) if code == FUND else ES.half(p)


def new_book(bid, kind, seed=None):
    b = ES.new_book(bid, kind, 'L4', seed); b['nav'] = {BT_START: CAP}; return b

def init_state():
    books = [new_book('EMG2_18_SIM_BT', 'BT')] + [new_book(f'EMG2_18_BT_RND_s{i:03d}', 'BT_RND', seed=SEED0 + i) for i in range(1, NRAND + 1)]
    return dict(record='Big Wins forward paper record -- PAPER line EMG2_18_SIM_BT, EMG2-18 + band-trend switch into A200 (PAPER ONLY; information only)',
                amendments=['AMENDMENT_shadow_EMG2_18_BT.md'], start_decision=BT_START, fill_day=P.next_session(BT_START),
                last_processed=P.prev_session(BT_START), decisions=[], data_blocks=[], bt=[], state=None, state_from=None, sessions_out=0,
                last={}, books=books)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)

def nav_of(b, last): return EM.nav_of(b, last)


# ---------------------------------------------------------------- BT1 / BT2: band index from the decision bundle
def cut(D, k, conv_v0):
    """The bundle as known at row k (inclusive). conv_v0: the decision bundle's V0 is already traded value (from 31 Dec 2026, see
    paper_emg2.table), so a cut dated before that is given V0 * Craw / Pv to keep the decision's traded value (section R)."""
    X = dict(D); X['dates'] = D['dates'][:k + 1]; X['Pv'] = D['Pv'][:k + 1]; X['Craw'] = D['Craw'][:k + 1]; X['V0'] = D['V0'][:k + 1]
    X['DIVD'] = {r: v for r, v in D.get('DIVD', {}).items() if r <= k}
    asof = str(pd.Timestamp(X['dates'][-1]).date())
    if conv_v0 and asof < '2026-12-31':
        with np.errstate(all='ignore'):
            X['V0'] = np.where(np.isfinite(X['Craw']) & (X['Craw'] > 0) & np.isfinite(X['Pv']) & (X['Pv'] > 0), X['V0'] * X['Craw'] / X['Pv'], X['V0'])
    return X

def tr_log(D):
    """Daily total-return log index per column, exactly as paper_emg2.table (A3/A6)."""
    Pv = D['Pv']; N = Pv.shape[1]; has = np.isfinite(Pv); Pf = pd.DataFrame(Pv).ffill().values
    div = np.zeros_like(Pv)
    for r_, lst in D.get('DIVD', {}).items():
        if r_ < len(D['dates']):
            for j, v in lst: div[r_, j] += v
    with np.errstate(all='ignore'):
        g = np.where(has[1:] & np.isfinite(Pf[:-1]) & (Pf[:-1] > 0), (Pv[1:] + div[1:]) / Pf[:-1], 1.0)
        g = np.where(np.isfinite(g) & (g > 0), g, 1.0)
    return np.vstack([np.zeros((1, N)), np.cumsum(np.log(g), axis=0)])

def month_end_rows(dates, n):
    """Rows of the last n month-ends of the bundle (last session of each calendar month; the bundle's last row is the decision)."""
    s = pd.Series(np.arange(len(dates)), index=pd.DatetimeIndex(dates))
    rows = [int(v) for v in s.groupby([s.index.year, s.index.month]).last().values]
    assert rows[-1] == len(dates) - 1
    return rows[-n:]

def band_trend(D, d, nm=None, lic=None, months=MONTHS):
    """BT1/BT2 at decision d on the bundle of d. Returns dict(state 'ON'|'OFF', level, mean, levels [[date, level, members]])."""
    rule = EM.class_rule(d); conv = d >= '2026-12-31'
    nm = nm if nm is not None else EM.names()
    lic = lic if lic is not None else (EM.lic_codes_v2() if rule == 'v2' else EM.lic_codes())
    rows = month_end_rows(D['dates'], months); L = tr_log(D); col = {c: j for j, c in enumerate(D['cols'])}
    lev = [1.0]; out = []
    for q, m in enumerate(rows):
        C = EM.table(cut(D, m, conv), nm=nm, lic=lic, rule=rule)['C']; J = [col[c] for c in C]
        out.append([str(pd.Timestamp(D['dates'][m]).date()), None, len(J)])
        if q + 1 < len(rows):
            m1 = rows[q + 1]
            lev.append(lev[-1] * (float(np.mean(np.exp(L[m1, J] - L[m, J]))) if J else 1.0))
    for o, x in zip(out, lev): o[1] = round(x, 10)
    mean = float(np.mean(lev)); state = 'ON' if (len(lev) < months or lev[-1] >= mean) else 'OFF'
    return dict(asof=d, state=state, level=lev[-1], mean=mean, months=len(lev), class_rule=rule, levels=out)


# ---------------------------------------------------------------- decisions
def decide_off(b, R, d, k, last, E, duplog):
    """BT3: sell every share holding; buy (or top up) the fund with the cash after the sales less the reserve; no share bought."""
    new = []
    for o in b['orders']: ES.ev(b, d, f"order not filled, dropped: {o['type']} {o['code']}")
    b['orders'] = []
    for x_, y_, _ in duplog:                                                                        # A7 code change carries the holding
        for cid, h in sorted(b['holdings'].items()):
            if cid != FUND_CID and h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; ES.ev(b, d, f'code change {x_}->{y_}')
    for cid, h in sorted(b['holdings'].items()):                                                    # payout: no close for 20 sessions
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            q = ES.shares(h); p = last[h['code']]['p']; v = q * p
            parts = ES.realise(h, q, v); b['cash'] += v; del b['holdings'][cid]
            ES.record(b, dict(date=d, side='payout', code=h['code'], shares=q, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='payout (20 sessions without a close)', lots=parts))
    nav = nav_of(b, last); proceeds = 0.0
    for cid, h in sorted(b['holdings'].items()):
        if cid == FUND_CID: continue
        p = last[h['code']]['p']; q = ES.shares(h)
        new.append(dict(type='sell', cid=cid, code=h['code'], reason='BT3 OFF: share sold')); proceeds += max(0.0, q * p * (1 - half(h['code'], p)) - ES.brok(q * p))
    fh = b['holdings'].get(FUND_CID); fval = ES.shares(fh) * last[FUND]['p'] if fh else 0.0
    room = CAP - fval; avail = min(b['cash'] + proceeds - RESERVE, room)                           # L1: cash above the cap is never invested
    want = avail >= MIN_ORDER if fh is None else avail >= max(MIN_ORDER, TOPUP * nav)
    if want: new.append(dict(type='fund', cid=FUND_CID, code=FUND, amount=math.floor(avail * 100) / 100, room=round(room, 2), k=k,
                             reason='BT3 OFF: fund bought' if fh is None else 'BT3 OFF: fund topped up (cash >= 10% of the account)'))
    elif fh is None: ES.ev(b, d, f'fund buy not sent: A${avail:.2f} is under A$500')
    b['orders'] = new; b['E'] = E
    ES.ev(b, d, f"decision {k} (state FUND): NAV {nav:.2f} orders " + ', '.join(f"{o['type']} {o['code']}" for o in new))
    return new

def decide_on(b, R, lot, d, k, last, E, duplog):
    """BT4: the registered rules (paper_emg2s.decide, rule L4); the fund is not on T and is sold by L4."""
    new = ES.decide(b, R, lot, d, k, last, E, duplog)
    for o in new:
        if o['cid'] == FUND_CID: o['reason'] = 'BT4 ON: fund sold'
    return new


def run_day(b, d, mkt):
    cl = mkt['close']
    for h in (b['holdings'][x] for x in sorted(b['holdings'])):                                     # splits
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] *= s
            ES.ev(b, d, f"split {h['code']} x{s:g}")
    for h in (b['holdings'][x] for x in sorted(b['holdings'])):                                     # dividends / distributions as cash
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    for o in [o for o in b['orders'] if o['type'] == 'sell']:                                       # sells first
        h = b['holdings'].get(o['cid']); p = cl.get(o['code'])
        if h is None: continue
        if p is None: ES.ev(b, d, f"sell {o['code']} not filled (no close); decided again next month-end"); continue
        q = ES.shares(h); hh = half(o['code'], p); bk = ES.brok(q * p); pr = max(0.0, q * p * (1 - hh) - bk)
        b['cash'] += pr; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk
        parts = ES.realise(h, q, pr); del b['holdings'][o['cid']]
        ES.record(b, dict(date=d, side='sell', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(pr, 2), reason=o['reason'], lots=parts))
    for o in [o for o in b['orders'] if o['type'] in ('buy', 'fund')]:
        p = cl.get(o['code'])
        if p is None: ES.ev(b, d, f"{o['type']} {o['code']} not filled: no close on the fill day"); continue
        hh = half(o['code'], p)
        if o['type'] == 'fund':                                                                     # BT3: the cash after the sales, less the reserve, within the cap
            spend = min(b['cash'] - RESERVE, o['room']); q = int(math.floor(max(spend, 0.0) / (p * (1 + hh)))); q0 = None
        else: q = o['shares']; q0 = q
        while q > 0 and q * p * (1 + hh) + ES.brok(q * p) > b['cash'] - RESERVE + 1e-9: q -= 1         # cut to what the cash covers
        if q <= 0 or q * p < MIN_ORDER and (q0 is None or q < q0):
            ES.ev(b, d, f"{o['type']} {o['code']} dropped at the fill: cash covers {q} units (under A$500)"); continue
        bk = ES.brok(q * p); paid = q * p * (1 + hh) + bk; b['cash'] -= paid; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk
        if o['cid'] in b['holdings']: b['holdings'][o['cid']]['lots'].append([d, q, paid])
        else: b['holdings'][o['cid']] = dict(code=o['code'], lots=[[d, q, paid]], vrank=o.get('vrank'), k=o['k'])
        ES.record(b, dict(date=d, side='buy', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(-paid, 2), reason=o['reason']))
    b['orders'] = []


def step(s, d, mkt, log, bundle=None):
    last = s['last']
    watch = {FUND} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: run_day(b, d, mkt)
    if s['state'] == 'OFF' and s['state_from'] is not None and d >= s['state_from']: s['sessions_out'] += 1
    info = None
    if d >= BT_START and month_end(d):
        D, blocked, src = EM.get_bundle(d, log) if bundle is None else bundle
        R = EM.table(D); lot = ES.lottery(D, R); duplog = D.get('duplog', [])
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else R['blocked_reason']
        if why:
            s['data_blocks'].append([d, f'EMG2 data block: {why}; no decision, holdings and state kept']); log('EMG2-18 BT', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src)
        elif FUND not in last:
            s['data_blocks'].append([d, 'no A200 close known; no decision, holdings and state kept']); log('EMG2-18 BT', d, 'no A200 close')
            info = dict(asof=d, blocked=True, reason='no A200 close', source=src)
        else:
            bt = band_trend(D, d)
            for r in R['rows'].values():
                if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); k = len(s['decisions']); orows = []
            for b in s['books']:
                new = decide_on(b, R, lot, d, k, last, E, duplog) if bt['state'] == 'ON' else decide_off(b, R, d, k, last, E, duplog)
                if not ES.rnd(b):
                    for o in new:
                        orows.append(dict(book=b['id'], state=bt['state'], type=o['type'], code=o['code'], shares=o.get('shares', 'all' if o['type'] == 'sell' else ''),
                                          amount_AUD=o.get('amount'), list_rank=o.get('rank'), fill='close of ' + E, rule=o['reason']))
            if bt['state'] != s['state']: s['state_from'] = E
            s['state'] = bt['state']; s['bt'].append(dict(bt, fill_day=E)); s['decisions'].append(d)
            os.makedirs(out_dir(), exist_ok=True); files = {}
            files[f'shadow/emg2bt_orders_{d}.csv'] = P.write_csv(f'{out_dir()}/emg2bt_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'state', 'type', 'code', 'shares', 'amount_AUD', 'list_rank', 'fill', 'rule']))
            files[f'shadow/emg2bt_band_{d}.csv'] = P.write_csv(f'{out_dir()}/emg2bt_band_{d}.csv', pd.DataFrame([dict(month_end=m, level=v, members=n) for m, v, n in bt['levels']]))
            info = dict(asof=d, fill_day=E, source=src, state=bt['state'], level=round(bt['level'], 6), mean10=round(bt['mean'], 6), class_rule=bt['class_rule'],
                        files_sha256=files, orders=sum(1 for o in orows if o['book'] == 'EMG2_18_SIM_BT'))
            log('EMG2-18 BT', d, 'decision', k, 'state', bt['state'], f"level {bt['level']:.4f} mean10 {bt['mean']:.4f}", info['orders'], 'orders')
        del D
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring the BT paper line up to trading day d (after paper_emg2s.run, before the bundle is cleared). None before the start."""
    try:
        if d < BT_START: return None
        s = load()
        if s is None: s = init_state(); log('EMG2-18 BT paper line state created; first decision', BT_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('EMG2-18 BT', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state=s['state'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('EMG2-18 BT ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard
def worst_fall(b): return EM.worst_fall(b)
def give_back(b):
    v = [b['nav'][k] for k in sorted(b['nav'])]
    return 0.0 if not v else float(v[-1] / max(v) - 1)

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        md.append(f'| **EMG2_18_SIM_BT** (paper line, band trend -> A200) | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$10,000, 100 random twins |')
        return rows, md, hold
    last = s['last']; f = lambda x: '' if x is None else f'{x:+.2%}'
    ret = lambda b: nav_of(b, last) / CAP - 1
    b = next(x for x in s['books'] if x['id'] == 'EMG2_18_SIM_BT')
    es = ES.load(); ref = None if es is None else next((x for x in es['books'] if x['id'] == 'EMG2_18_REF'), None)
    rref = None if ref is None else nav_of(ref, es['last']) / CAP - 1
    r = ret(b); tw = np.array([ret(x) for x in s['books'] if x['kind'] == 'BT_RND'])
    pr = float(np.mean(tw < r)) if len(tw) else None; med = float(np.median(tw)) if len(tw) else None
    st = {'ON': 'EMG2', 'OFF': 'FUND', None: 'not decided yet'}[s['state']]
    lb = s['bt'][-1] if s['bt'] else None
    lvl = '' if lb is None else f"; band index {lb['level']:.4f} v 10-month mean {lb['mean']:.4f} ({lb['asof']})"
    rows.append(dict(asof=d, book=b['id'], kind='PAPER line EMG2-18 + band trend (information only)', capital=CAP, nav=round(nav_of(b, last), 2), cash=round(b['cash'], 2),
                     holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), pct_of_random=(None if pr is None else round(pr, 3)),
                     random_median_return=(None if med is None else round(med, 5)),
                     note=f"state: {st}{lvl}; sessions out {s['sessions_out']}; orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}; worst fall (daily) {worst_fall(b):.1%}; "
                          f"give-back from peak {give_back(b):.1%}; BT - REF {f(None if rref is None else r - rref)} (after costs; no tax modelled); {TAG}"))
    md.append(f"| **EMG2_18_SIM_BT** (paper line) | {nav_of(b, last):,.2f} | {f(r)} | state: **{st}**{lvl}; sessions out {s['sessions_out']}; orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}; "
              f"BT - REF {f(None if rref is None else r - rref)}" + ('' if pr is None else f"; % of {len(tw)} twins below {pr:.2f} (median {f(med)})")
              + f"; worst fall {worst_fall(b):.1%}; give-back {give_back(b):.1%} |")
    hs_ = ', '.join(f"{h['code']} {ES.shares(h):,.0f}" for h in b['holdings'].values())
    if hs_ or b['orders']: hold.append(f"- {b['id']} (state {st}): {hs_ or 'no holdings'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
