# Big Wins forward PAPER record -- PAPER line PAIR (AMENDMENT_shadow_PAIR.md): the registered EMG2-18 rules and the frozen BLIND3 primary as
# two equal members of ONE A$10,000 account. Information only: never evidence for or against EMG2 or BLIND3; no live rule depends on it.
#   PAIR_10k (A$10,000, IBKR fixed brokerage max(A$6.60, 0.088%)) + 100 random twins PAIR_RND_10k_s001..s100 + A200 A$0 comparator
# Merging = tools4.Ensemble of the blind-4 kit, copied byte for byte into code/pair_frozen/tools4.py (SHA-256 checked at import) and called
# UNMODIFIED, with the members in the order of the seen-data run (deep92/code/ens92.py, C50U): member 0 = B (BLIND3), member 1 = E (EMG2-18).
#   Member B = the builder's frozen strategy (paper_blind3.frozen(): strat.py / strategy.py, unmodified) on paper_blind3.FEngine.
#   Member E = the EMG2-18 lists of paper_emg2.table on the same month-end bundle (target list T, bid peg, lottery class of paper_emg2s):
#              sell rule L4 (off T) and bid-peg sells; buys T best first skipping held / lottery / peg / no trade on the day / no close;
#              n = min(18, floor(share / A$550)), each order 1/n of the member's share (rule L3 read on its share; draft s2).
# Accounting = the kit's (acct3) exactly as paper_blind3: fills at the next session's close, sells first (open 5 sessions), brokerage acct3.fee,
# half-spread acct3.half_spread on the decision-day place for every order of either member, buys of at least A$500 and at most cash less A$50
# and 5% of the 20-session median traded value, duplicate-return refusal, buys stop at the Ensemble's cap, June tax 32% (367-day halving,
# losses carried), FIFO parcels, payout rule for a holding with no close for more than 20 sessions.
# Twins: member B's twin = BLIND3's twin rule (persistent random score over place <= 800, redraw 0.2101); member E's twin = paper_emg2s'
# twin rule (persistent random score over band C, redraw 0.2, top len(T)); member seeds 1000 x (8800000 + i) + {0 (B), 1 (E)}.
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state file STATE_DIR/pair_state.json; never writes the H82
# state or another line's state (reads emg2s_state.json and blind3_state.json for the reading only). Idempotent and resumable.
import os, sys, json, math, hashlib, traceback, importlib.util
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM, paper_emg2s as ES, paper_blind3 as B3, paper_score as PS

PAIR_START = '2026-11-30'
CAP = 10000.0; NRAND = 100; SEED0 = 8800000
SLOTS = 18; SLOT_UNIT = 550.0                                                                    # EMG2-18 L3, read on the member's share
TAG = 'PAPER line PAIR (EMG2-18 + BLIND3 in one A$10,000 account; information only)'
FROZEN_T4 = {'tools4.py': 'b70dcbb7dae5d92dacdfdedf9fb4847af90dd4f6267122897ce2c627a317acfe'}
PDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pair_frozen')
MB, ME_ = 0, 1                                                                                   # member numbers (ens92.py C50U order)
MNAME = {MB: 'B', ME_: 'E'}

_T4 = {}
def tools4():
    """tools4 module from pair_frozen/ after a SHA-256 check, bound to the frozen acct3 of blind3_frozen/ (byte-identical to the blind-4 kit's)."""
    if _T4: return _T4['m']
    for f, h in FROZEN_T4.items():
        got = hashlib.sha256(open(os.path.join(PDIR, f), 'rb').read()).hexdigest()
        if got != h: raise RuntimeError(f'pair_frozen/{f} sha256 {got[:12]} != frozen {h[:12]}')
    A, _ = B3.frozen(); saved = sys.modules.get('acct3')
    try:
        sys.modules['acct3'] = A
        sp = importlib.util.spec_from_file_location('tools4_pair', os.path.join(PDIR, 'tools4.py')); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    finally:
        if saved is None: sys.modules.pop('acct3', None)
        else: sys.modules['acct3'] = saved
    assert m.acct3 is A, 'tools4 bound a different acct3'
    _T4['m'] = m; return m


# ---------------------------------------------------------------- members
class MemberE:
    """EMG2-18 rules on a sub-book (book.nav = the member's share). Lists from paper_emg2.table (or a twin's random T)."""
    def __init__(s, FE, R, lot, T): s.FE = FE; s.R = R; s.lot = lot; s.T = list(T); s.tset = set(T)
    def decision_rows(s, dates): return []
    def sells(s, view, book):
        rows = s.R['rows']; out = []
        for j in sorted(book.holdings):
            cid = s.FE.cols[j]
            if rows.get(cid, {}).get('bid_peg') or cid not in s.tset: out.append(j)
        return out
    def buys(s, view, book):
        n = max(0, min(SLOTS, int(math.floor(book.nav / SLOT_UNIT + 1e-9))))
        if n == 0: return [], 0
        rows = s.R['rows']; o = []
        for cid in s.T:
            j = s.FE.cix.get(cid); r = rows.get(cid)
            if j is None or r is None or j in book.holdings or s.lot.get(cid, True) or r['bid_peg'] or not r['traded_on_day'] or r['close'] is None: continue
            o.append((j, 1.0 / n))
        return o, n

class Idle:
    """a member whose own data are blocked this month-end: sells nothing, buys nothing."""
    def decision_rows(s, dates): return []
    def sells(s, view, book): return []
    def buys(s, view, book): return [], 0

class Cap:
    """records what a member asked for (for the reading 'how often both wanted the same company'); changes nothing."""
    def __init__(s, m): s.m = m; s.want = []
    def decision_rows(s, dates): return s.m.decision_rows(dates)
    def sells(s, view, book): return s.m.sells(view, book)
    def buys(s, view, book):
        o, n = s.m.buys(view, book); s.want = [int(j) for j, w in o]; return o, n


# ---------------------------------------------------------------- state
def state_path(): return P.STATE_DIR + '/pair_state.json'
def out_dir(): return P.REC + '/shadow'

def new_book(bid, kind, i=None):
    b = dict(id=bid, kind=kind, capital=CAP, twin=i, cash=CAP, holdings={}, orders=None, trades=[], divs=[], ntrades=0, nav={PAIR_START: CAP},
             spread_paid=0.0, brok_paid=0.0, tax_paid=0.0, fy=0.0, carry=0.0, events=[], same_wanted=[])
    if i is not None:
        b['mB'] = dict(seed=1000 * (SEED0 + i) + MB, rng_state=None, rs={})
        b['mE'] = dict(kind='E_RND', seed=1000 * (SEED0 + i) + ME_, rng_state=None, rs={})
    return b

def init_state():
    fill = P.next_session(PAIR_START)
    books = [new_book('PAIR_10k', 'PAIR')] + [new_book(f'PAIR_RND_10k_s{i:03d}', 'PAIR_RND', i) for i in range(1, NRAND + 1)]
    return dict(record='Big Wins forward paper record -- PAPER line PAIR, EMG2-18 + BLIND3 as two members of one A$10,000 account (PAPER ONLY; information only)',
                amendment='AMENDMENT_shadow_PAIR.md', members={'0': 'B = BLIND3 frozen primary BLEND_p6_U400_B2_N15_T1', '1': 'E = EMG2-18 registered rules, L3 on its share'},
                frozen_sha256=dict(B3.FROZEN, **FROZEN_T4), start_decision=PAIR_START, fill_day=fill, last_processed=P.prev_session(PAIR_START),
                decisions=[], data_blocks=[], last={}, books=books, cmps=[PS.new_cmp0('PAIR_CMP_A200_10k', {'A200.AU': 1.0}, CAP, 0.0, PAIR_START, fill)])

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)

def month_end(d): return P.is_month_end(d)                                                       # (tests patch this name only)
def rnd(b): return b['kind'] == 'PAIR_RND'
def ev(b, d, x):
    if not rnd(b): b['events'].append([d, x])
def record(b, t):
    b['ntrades'] += 1
    if not rnd(b): b['trades'].append(t)
shares = B3.shares; cost = B3.cost; px = B3.px; days = B3.days; realise = B3.realise
def nav_of(b, last): return B3.nav_of(b, last)
def member_names(b): return {q: sum(1 for h in b['holdings'].values() if h.get('m') == q) for q in (MB, ME_)}


# ---------------------------------------------------------------- month-end decision
def decide(b, FE, R, lot, d, last, E, okB, okE):
    A, ST = B3.frozen(); T4 = tools4(); i = FE.i; rk = FE.rank(i); view = A.View(FE, i); new_s = []
    if b['orders']:
        for o in b['orders'].get('sells', []): ev(b, d, f"sell {o['code']} lapsed (no close in 5 sessions); decided again now")
    b['orders'] = None
    hv = {}; outside = []; own = {}
    for cid, h in sorted(b['holdings'].items()):
        j = FE.cix.get(cid); p = px(last, h['code'])
        if j is None or p is None: outside.append(cid); continue
        bd = min(l[0] for l in h['lots'])
        hv[j] = dict(value=shares(h) * p, cost=cost(h), first_buy_date=pd.Timestamp(bd), days_held=days(bd, d), months_held=None, parcels=len(h['lots']))
        own[j] = h['m']
    navd = b['cash'] + sum(v['value'] for v in hv.values()) + sum(shares(b['holdings'][c]) * (px(last, b['holdings'][c]['code']) or 0.0) for c in outside)
    if okB:
        mB = ST.factory(FE, None)
        if rnd(b): mB.rs = B3._RS(B3.twin_scores(b['mB'], FE, rk))
    else: mB = Idle()
    if okE:
        T = R['T'] if not rnd(b) else ES.lists_for(b['mE'], R)[0]
        mE = MemberE(FE, R, lot, T)
    else: mE = Idle()
    cB, cE = Cap(mB), Cap(mE); ens = T4.Ensemble([cB, cE])
    memo = {'own': own}
    book = A.Book(b['cash'], navd, hv, memo, [])
    sold = []
    for o in ens.sells(view, book):
        j, fr = (o if isinstance(o, tuple) else (o, 1.0)); j = int(j)
        if j in hv and fr > 0 and j not in sold: sold.append(j)
    for cid in outside:
        new_s.append(dict(cid=cid, code=b['holdings'][cid]['code'], m=b['holdings'][cid]['m'], rank=None, reason='forced: not in the month-end data'))
    for j in sold:
        cid = FE.cols[j]; q = own[j]
        new_s.append(dict(cid=cid, code=b['holdings'][cid]['code'], m=q, rank=float(rk[j]) if np.isfinite(rk[j]) else None,
                          reason=('member B: frozen BLIND3 sell (rule 4)' if q == MB else ('member E: bid peg' if R['rows'].get(cid, {}).get('bid_peg') else 'member E: L4 off T'))))
    book2 = A.Book(b['cash'], navd, {j: v for j, v in hv.items() if j not in sold}, memo, []); book2.sold = sorted(sold)
    orders, maxh = ens.buys(view, book2)
    keepj = [j for j in hv if j not in sold]; cand = [int(j) for j, w in orders]
    X = FE.Rz[i - 59:i + 1]; new_b = []
    for j, w in orders:
        j = int(j); dup = []
        if (X[:, j] != 0).sum() >= 40:
            with np.errstate(all='ignore'):
                for q in keepj + cand:
                    if q != j and np.corrcoef(X[:, j], X[:, q])[0, 1] > 0.98: dup.append(FE.cols[q])
        new_b.append(dict(cid=FE.cols[j], code=FE.code[j], m=int(memo['own'][j]), w=float(w), rank=float(rk[j]) if np.isfinite(rk[j]) else None,
                          cap5=float(0.05 * np.nan_to_num(FE.m20[j])), dup=dup))
    both = sorted(FE.code[j] for j in set(cB.want) & set(cE.want))
    if not rnd(b): b['same_wanted'].append([d, len(both), both])
    b['orders'] = dict(decision=d, E=E, maxh=maxh, sells=new_s, buys=new_b, sell_window=B3.window5(E)) if (new_s or new_b) else None
    ev(b, d, f"decision: NAV {navd:.2f}; members B/E ok {okB}/{okE}; sells {[o['code'] for o in new_s]}; buy list {[(o['code'], MNAME[o['m']]) for o in new_b]}; both wanted {both}")
    return new_s, new_b


# ---------------------------------------------------------------- one trading day (paper_blind3.run_day; the holding remembers its member)
def run_day(b, d, mkt, last):
    A = B3.frozen()[0]; cl = mkt['close']
    for h in (b['holdings'][x] for x in sorted(b['holdings'])):                                     # splits
        sp = mkt['split'].get(h['code'])
        if sp and sp > 0:
            for l in h['lots']: l[1] *= sp
            ev(b, d, f"split {h['code']} x{sp:g}")
    for h in (b['holdings'][x] for x in sorted(b['holdings'])):                                     # cash dividends
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    o = b['orders']
    if not o or d < o['E']: return
    keep_s = []
    for s_ in o['sells']:                                                                           # sells first
        h = b['holdings'].get(s_['cid']); p = cl.get(s_['code'])
        if h is None: continue
        if p is None:
            if d < o['sell_window'][-1]: keep_s.append(s_)
            else: ev(b, d, f"sell {s_['code']} lapsed: no close in 5 sessions")
            continue
        q = shares(h); V = q * p; cst = A.half_spread(s_['rank'] if s_['rank'] is not None else float('nan'), p); f = A.fee(V); pr = V * (1 - cst) - f
        b['cash'] += pr; b['spread_paid'] += V * cst; b['brok_paid'] += f
        parts = realise(b, h, q, pr, d); del b['holdings'][s_['cid']]
        record(b, dict(date=d, side='sell', code=s_['code'], member=MNAME[s_['m']], shares=q, price=p, half_spread=round(cst, 6), brokerage=round(f, 2), cash=round(pr, 2), reason=s_['reason'], lots=parts))
    if d == o['E']:
        navf = b['cash'] + sum(shares(h) * (cl.get(h['code']) or px(last, h['code']) or 0.0) for h in b['holdings'].values())
        for x in o['buys']:
            if o['maxh'] is not None and len(b['holdings']) >= o['maxh'] and x['cid'] not in b['holdings']: break
            p = cl.get(x['code']); why = None
            if p is None: why = 'no trade on the fill day'
            else:
                amt = min(x['w'] * navf, b['cash'] - A.RESERVE)
                if amt < A.MIN_BUY: ev(b, d, f"buys stop at {x['code']}: under A$500 or no cash"); break
                if not amt <= x['cap5']: why = 'over 5% of 20-session median traded value'
                elif any(c in b['holdings'] for c in x['dup']): why = 'same company as a holding (return correlation above 0.98)'
            if why: ev(b, d, f"buy {x['code']} refused: {why}"); continue
            cst = A.half_spread(x['rank'] if x['rank'] is not None else float('nan'), p)
            q = int(math.floor((amt - A.fee(amt)) / (p * (1 + cst))))
            if q <= 0: ev(b, d, f"buy {x['code']} refused: 0 shares"); continue
            f = A.fee(q * p); paid = q * p * (1 + cst) + f
            b['cash'] -= paid; b['spread_paid'] += q * p * cst; b['brok_paid'] += f
            b['holdings'][x['cid']] = dict(code=x['code'], lots=[[d, q, paid]], rank=x['rank'], m=x['m'])
            record(b, dict(date=d, side='buy', code=x['code'], member=MNAME[x['m']], shares=q, price=p, half_spread=round(cst, 6), brokerage=round(f, 2), cash=round(-paid, 2),
                           reason='member %s buy' % MNAME[x['m']], weight=x['w']))
    b['orders'] = dict(o, sells=keep_s, buys=[]) if keep_s else None

def june_tax(b, d):
    net = b['fy'] + b['carry']
    if net > 0: t = 0.32 * net; b['cash'] -= t; b['tax_paid'] += t; b['carry'] = 0.0; ev(b, d, f'June tax A$ {t:.2f} on net realised gains A$ {net:.2f}')
    else: b['carry'] = net
    b['fy'] = 0.0

def payouts(b, FE, d, last):
    """kit rule (as paper_blind3.payouts): a holding without a close for more than 20 sessions is paid out at the decision."""
    i = FE.i
    for cid, h in sorted(b['holdings'].items()):
        j = FE.cix.get(cid)
        if j is None:
            lc = last.get(h['code'], {}).get('d')
            if lc is None or len(P.sessions_between(lc, d)) < 20: continue
            term, lp = 1.0, last[h['code']]['p']
        else:
            if FE.lastv[i, j] >= i - 20: continue
            po = FE.payout(j)
            if po is None: continue
            term, lp, l0 = po
        q = shares(h); v = q * lp * term
        b['cash'] += v; parts = realise(b, h, q, v, d); del b['holdings'][cid]
        record(b, dict(date=d, side='payout', code=h['code'], member=MNAME[h['m']], shares=q, price=lp * term, half_spread=0.0, brokerage=0.0, cash=round(v, 2),
                       reason='payout (no close for more than 20 sessions): ' + ('last close, within 30% of its 250-session high' if term else 'ZERO, last close below 70% of its 250-session high'), lots=parts))
        ev(b, d, f"payout {h['code']} {'at last close ' + str(lp) if term else 'at ZERO'}")


def step(s, d, mkt, log, bundle=None):
    last = s['last']
    watch = {'A200'} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {x['code'] for b in s['books'] if b['orders'] for x in b['orders']['buys'] + b['orders']['sells']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: run_day(b, d, mkt, last)
    for c in s['cmps']: PS.cmp_day0(c, d, mkt)
    info = None
    if d >= PAIR_START and month_end(d):
        if pd.Timestamp(d).month == 6:
            for b in s['books']: june_tax(b, d)
        D, blocked, src = EM.get_bundle(d, log) if bundle is None else bundle
        FE = B3.FEngine(D, B3.names(), B3.lic_codes())
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else None
        if FE.asof != d: why = f'bundle ends {FE.asof}, not {d}'
        R = lot = None; whyB = whyE = None
        if not why:
            R = EM.table(D); lot = ES.lottery(D, R); whyE = R['blocked_reason']
            rk = FE.rank(FE.i); A, ST = B3.frozen(); U = ST.CONFIG['PRIMARY'][2]
            g = B3._M['strat'].sig(A.View(FE, FE.i)); nuni = int((FE.ok & g['valid'] & (rk <= U)).sum())
            whyB = f'only {nuni} valid ordinary shares in the top {U} (< {B3.MIN_UNIVERSE})' if nuni < B3.MIN_UNIVERSE else None
            if whyB and whyE: why = f'member B: {whyB}; member E: {whyE}'
        del D
        if why:
            s['data_blocks'].append([d, f'PAIR data block: {why}; no decision, holdings kept']); log('PAIR', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src)
        else:
            if whyB or whyE: s['data_blocks'].append([d, 'PAIR member data block (that member decides nothing; its holdings kept): ' + ('B: ' + whyB if whyB else 'E: ' + whyE)])
            for b in s['books']: payouts(b, FE, d, last)
            E = P.next_session(d); orows = []
            for b in s['books']:
                sl, bl = decide(b, FE, R, lot, d, last, E, whyB is None, whyE is None)
                if not rnd(b):
                    orows += [dict(book=b['id'], member=MNAME[o['m']], type='sell', code=o['code'], weight=None, cost_rank=o['rank'], fill='close of ' + E, rule=o['reason']) for o in sl]
                    orows += [dict(book=b['id'], member=MNAME[o['m']], type='buy', code=o['code'], weight=round(o['w'], 6), cost_rank=o['rank'],
                                   fill='close of ' + E + ' (in order until the cap is held)', rule='member %s buy list' % MNAME[o['m']]) for o in bl]
            os.makedirs(out_dir(), exist_ok=True)
            f = P.write_csv(f'{out_dir()}/pair_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'member', 'type', 'code', 'weight', 'cost_rank', 'fill', 'rule']))
            s['decisions'].append(d)
            info = dict(asof=d, fill_day=E, source=src, files_sha256={f'shadow/pair_orders_{d}.csv': f}, member_blocks=[whyB, whyE] if (whyB or whyE) else None,
                        orders={b['id']: sum(1 for o in orows if o['book'] == b['id']) for b in s['books'] if not rnd(b)})
            log('PAIR', d, 'decision', info['orders'])
        del FE
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring PAIR up to trading day d (after paper_blind3.run, before the bundle is cleared). None before the start."""
    try:
        if d < PAIR_START: return None
        B3.frozen(); tools4()
        s = load()
        if s is None: s = init_state(); log('PAIR paper state created; first decision', PAIR_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('PAIR', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('PAIR ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard
def blind3_return():
    try:
        s = B3.load()
        if s is None: return None
        b = next(x for x in s['books'] if x['id'] == 'BLIND3_10k'); return B3.nav_of(b, s['last']) / 10000.0 - 1
    except Exception: return None

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        md.append(f'| **PAIR (EMG2-18 + BLIND3 in one A$10,000 account; AMENDMENT_shadow_PAIR.md)** | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; '
                  '100 random twins; members claim names in turn |')
        return rows, md, hold
    last = s['last']; f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x:+.2%}'
    b = next(x for x in s['books'] if x['id'] == 'PAIR_10k'); a2 = s['cmps'][0]
    nav = nav_of(b, last); r = nav / CAP - 1; ra = P.nav_of(a2, last) / CAP - 1; rsold = B3.sold_after_tax(b, last, s['last_processed']) / CAP - 1
    tw = np.array([nav_of(x, last) / CAP - 1 for x in s['books'] if rnd(x)])
    pr = float(np.mean(tw < r)) if len(tw) else None; med = float(np.median(tw)) if len(tw) else None
    re_ = B3.emg2_ref_return(); rb = blind3_return(); c50 = 0.5 * (re_ + rb) if (re_ is not None and rb is not None) else None
    mn = member_names(b); sw = b['same_wanted'][-1] if b['same_wanted'] else None
    gaps = f"vs EMG2_18_REF {f(None if re_ is None else r - re_)}, vs BLIND3_10k {f(None if rb is None else r - rb)}, vs 50/50 reading {f(None if c50 is None else r - c50)}"
    rows.append(dict(asof=d, book=b['id'], kind='PAPER PAIR (information only)', capital=CAP, nav=round(nav, 2), cash=round(b['cash'], 2), holdings=len(b['holdings']),
                     open_orders=0 if not b['orders'] else len(b['orders']['sells']) + len(b['orders']['buys']), return_since_start=round(r, 5),
                     pct_of_random=(None if pr is None else round(pr, 3)), random_median_return=(None if med is None else round(med, 5)),
                     vs_random_median=(None if med is None else round(r - med, 5)), a200_b0_return=round(ra, 5), vs_a200_b0=round(r - ra, 5), ret_after_tax_sold=round(rsold, 5),
                     note=f"FACT: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, modelled spread A$ {b['spread_paid']:,.2f}, tax paid A$ {b['tax_paid']:,.2f}; "
                          f"names held B {mn[MB]} / E {mn[ME_]}; both members wanted the same company at the last decision: {'' if sw is None else sw[1]}; "
                          f"worst fall (daily) {B3.worst_fall(b):.1%}; MOSTLY LUCK: {gaps}; {TAG}"))
    md.append(f"| **{b['id']}** (paper; EMG2-18 + BLIND3, one account) | {nav:,.2f} | {f(r)} | vs A200 (A$0) {f(r - ra)}; % of {len(tw)} twins below {'' if pr is None else round(pr, 2)} (median {f(med)}); "
              f"sold today after tax {f(rsold)}; facts: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, spread A$ {b['spread_paid']:,.2f}, tax A$ {b['tax_paid']:,.2f}; "
              f"names B {mn[MB]} / E {mn[ME_]}; same company wanted by both {'' if sw is None else sw[1]}; worst fall {B3.worst_fall(b):.1%}; mostly luck: {gaps} |")
    hs_ = ', '.join(f"{h['code']}({MNAME[h['m']]}) {shares(h):,.0f}" for h in b['holdings'].values())
    if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no shares'}" + (f"; paper orders for the close of {b['orders']['E']}" if b['orders'] else ''))
    return rows, md, hold
