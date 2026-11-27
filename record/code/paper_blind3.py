# Big Wins forward PAPER record -- PAPER line BLIND3 = the frozen primary of blind build 3, BLEND_p6_U400_B2_N15_T1 (AMENDMENT_shadow_BLIND3.md;
# rules: blind3_build/PREREG_BLIND3.md s1). Information only: never evidence for or against EMG2-18; no live rule depends on it.
#   BLIND3_10k  (A$10,000, IBKR fixed brokerage max(A$6.60, 0.088%))  + 100 random twins (seeds 8780000+i)
#   BLIND3_100k (A$100,000, same rules)                                + 100 random twins (seeds 8790000+i)
# The decision rules are the builder's frozen code, copied byte for byte into code/blind3_frozen/ (strat.py, strategy.py and the kit's acct3.py,
# tools3.py; SHA-256 checked at import) and called UNMODIFIED: strategy.factory(E, None).sells(view, book) / .buys(view, book). This file only
# (1) presents the forward month-end bundle to that code as an acct3-shaped engine (fengine), and (2) books the orders on the forward daily
# closes with the kit's accounting (acct3.sim): fills at the next session's close, sells first, brokerage acct3.fee, the kit's half-spread
# curve acct3.half_spread on the decision-day cost rank, buys of at least A$500 and at most cash less A$50 and 5% of the 20-session median
# traded value, no buy of a share whose 60-session returns duplicate a holding (correlation > 0.98), at most 15 names, 32% tax on net
# realised gains at each June month-end (halved for parcels held 367 days or more, losses carried), FIFO parcels.
# A twin is the same Design with every ranking replaced by a persistent seeded random score (redrawn with probability 0.2101 a month, the
# builder's calibrated value) kept in this state file (forward equivalent of tools3.RandomScores, which needs the whole panel in advance).
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state file STATE_DIR/blind3_state.json; never reads or writes the
# H82 state or another line's state (reads emg2s_state.json for the combined reading only). Idempotent and resumable (last_processed).
import os, sys, json, math, hashlib, traceback, importlib.util, warnings
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM, paper_score as PS

B3_START = '2026-11-30'
SIZES = (('10k', 10000.0, 8780000), ('100k', 100000.0, 8790000))
NRAND = 100
WIN = 330                     # rows of the bundle handed to the frozen code (it reads at most 252 back; payout high 250 before the last close)
MIN_UNIVERSE = 300            # data block: fewer than this many valid ordinary shares in the top 400 -> no decision
TAG = 'PAPER line BLIND3 (blind build 3 frozen primary; information only)'
FROZEN = {'strat.py': '5f0f2ff91254debb0d102ec8cae8590afec45a4a33d7387e911826aac26011eb',
          'strategy.py': '943295f7c01b9c519f3812dcee6352fc8eb7863b5fb5764cbcf9a8fbfaa5601b',
          'acct3.py': '16486f501b156d0d3ee927491df6aad2fd33351290e63ffd9fb80aa7ca5571a7',
          'tools3.py': 'aae0a11b415701c0578eabb75ea7b8fc4f77403a57d0f3fe7297fb607e6c515c'}
FDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blind3_frozen')
NAME_RX = r'INVESTMENT|CAPITAL FUND|\bLIC\b|\bFUND\b|\bETF\b|\bETFS\b|INDEX|ISHARES|VANECK|BETASHARES|SPDR|VANGUARD'   # kit's exclusion (build_blind3.py)

_M = {}
def frozen():
    """(acct3, strategy) loaded from blind3_frozen/ after a SHA-256 check of every file; the modules are the builder's code unchanged."""
    if _M: return _M['acct3'], _M['strategy']
    for f, h in FROZEN.items():
        got = hashlib.sha256(open(os.path.join(FDIR, f), 'rb').read()).hexdigest()
        if got != h: raise RuntimeError(f'blind3_frozen/{f} sha256 {got[:12]} != frozen {h[:12]}')
    path0 = list(sys.path); saved = {k: sys.modules.get(k) for k in ('acct3', 'tools3', 'strat', 'strategy')}
    try:
        for k in ('acct3', 'tools3', 'strat', 'strategy'):
            sp = importlib.util.spec_from_file_location(k, os.path.join(FDIR, k + '.py')); m = importlib.util.module_from_spec(sp)
            sys.modules[k] = m; sp.loader.exec_module(m); _M[k] = m
    finally:
        sys.path[:] = path0                                                                    # strat.py inserts the kit folder: undo
        for k, v in saved.items():
            if v is None: sys.modules.pop(k, None)
            else: sys.modules[k] = v
    for k in ('acct3', 'tools3'):
        assert _M['strat'].__dict__[k] is _M[k], 'strat.py bound a different ' + k
    assert _M['strategy'].CONFIG['PRIMARY'] == ('BLEND', 6, 400, 15, 2, 1, 0.2101)
    return _M['acct3'], _M['strategy']

def twin_p(): return frozen()[1].CONFIG['PRIMARY'][6]
def NMAX(): return frozen()[1].CONFIG['PRIMARY'][3]


# ---------------------------------------------------------------- the bundle as an acct3-shaped engine (only the last WIN rows)
class FEngine:
    """Duck-typed acct3.Engine at one decision row i (= last row): idx, cols, R, L, Rz, CR, TV, ok, first, delist, xi, clff, rank(i), m20.
    Kit conventions: a session is TRADED when the raw close exists and volume > 0 (the kit's CR is NaN on no-trade days); RET on a traded
    session = total return since the previous traded close (prices from the bundle's split-adjusted closes, cash dividends from DIVD), 0 on
    sessions without a trade after the first trade, NaN before it; days outside (-0.95, 10] are NaN as in acct3; TV = traded value
    (split-adjusted close x volume as paper_emg2.table), 0 on sessions without a trade once started, NaN before."""
    def __init__(s, D, nm, lic, win=WIN):
        A = frozen()[0]
        dates = pd.DatetimeIndex(D['dates']); cols = list(D['cols']); n = len(dates); i0 = max(0, n - win)
        Pv = D['Pv']; C = D['Craw']; V0 = D['V0']; asof = str(dates[-1].date())
        with np.errstate(all='ignore'):
            vol = np.where(np.isfinite(C) & (C > 0), V0 / C, 0.0) if asof < '2026-12-31' else np.where(np.isfinite(Pv) & (Pv > 0), V0 / Pv, 0.0)
        trd = np.isfinite(C) & np.isfinite(Pv) & (np.nan_to_num(vol) > 0) & (np.nan_to_num(V0) > 0)
        div = np.zeros(Pv.shape)
        for r_, lst in D.get('DIVD', {}).items():
            if r_ < n:
                for j, v in lst: div[r_, j] += v
        Pf = pd.DataFrame(Pv).ffill().values
        with np.errstate(all='ignore'):
            g = np.ones(Pv.shape); g[1:] = np.where(np.isfinite(Pv[1:]) & np.isfinite(Pf[:-1]) & (Pf[:-1] > 0), (Pv[1:] + div[1:]) / Pf[:-1], 1.0)
            g = np.where(np.isfinite(g) & (g > 0), g, 1.0)
        LT = np.cumsum(np.log(g), axis=0)                                                           # log total-return index on every row
        lt_tr = np.where(trd, LT, np.nan); lt_prev = pd.DataFrame(lt_tr).ffill().shift(1).values    # index at the previous traded session
        started = np.cumsum(trd, axis=0) > 0
        with np.errstate(all='ignore'):
            R = np.where(trd, np.expm1(LT - lt_prev), np.where(started, 0.0, np.nan))
            R = np.where(trd & ~np.isfinite(lt_prev), np.nan, R)                                    # first traded session: no return
            R[(R < -0.95) | (R > 10)] = np.nan
            TVf = np.where(trd, np.nan_to_num(V0 * Pv / C) if asof < '2026-12-31' else np.nan_to_num(V0), 0.0)
        TVf = np.where(started, TVf, np.nan)
        sl = slice(i0, n)
        s.idx = dates[sl]; s.cols = cols; s.n = len(s.idx); s.i = s.n - 1; s.asof = asof
        s.R = R[sl]; s.Rz = np.nan_to_num(s.R); s.L = np.log1p(s.Rz).cumsum(0)
        s.CR = np.where(trd, C, np.nan)[sl]; s.TV = TVf[sl]; s.clff = pd.DataFrame(s.CR).ffill().values
        code = [c.split('#')[0] for c in cols]; rx = __import__('re').compile(NAME_RX)
        s.code = code
        s.ok = np.array([len(c) == 3 and c not in lic and not rx.search(str(nm.get(c, '')).upper()) for c in code])
        fi = np.where(trd.any(0), trd.argmax(0), -1)
        s.first = np.array([dates[k].to_datetime64() if k >= 0 else np.datetime64('NaT') for k in fi]).astype('datetime64[D]')
        s.delist = pd.DataFrame(dict(eid=[], delist_date=pd.to_datetime([]), reason=[]))
        s.xi = np.full(s.n, np.nan)
        lastv_full = np.maximum.accumulate(np.where(trd, np.arange(n)[:, None], -1), axis=0)
        s.lastv = lastv_full[sl] - i0                                                               # may be negative (traded before the window)
        i = s.i; w = s.TV[max(0, i - 251):i + 1]; w20 = s.TV[max(0, i - 19):i + 1]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            s.m252 = np.where(np.isfinite(w).sum(0) >= 120, np.nanmedian(w, axis=0), np.nan)        # = pandas rolling(252, min_periods=120).median()
            s.m20 = np.where(np.isfinite(w20).sum(0) >= 10, np.nanmedian(w20, axis=0), np.nan)
        s._rk = {}
        s.full_C = np.where(trd, C, np.nan); s.full_lastv = lastv_full[-1]; s.cix = {c: j for j, c in enumerate(cols)}

    def rank(s, i):
        assert i == s.i, 'forward engine ranks the decision row only'
        if i not in s._rk:
            s._rk[i] = pd.Series(np.where(s.ok & (s.lastv[i] >= i - 4), s.m252, np.nan)).rank(ascending=False).values
        return s._rk[i]

    def payout(s, j):
        """kit rule for a holding that stopped trading, class 'not recorded' (no delisting class in the forward data): last close if within
        30% of its 250-session high, else zero. Returns (term, last_close, last_date)."""
        l0 = int(s.full_lastv[j])
        if l0 < 0: return None
        lp = s.full_C[l0, j]; hh = np.nanmax(s.full_C[max(0, l0 - 250):l0 + 1, j])
        return (1.0 if lp >= 0.7 * hh else 0.0), float(lp), l0


def names():
    try: return EM.names()
    except Exception: return {}

def lic_codes():
    out = set()
    for f in (P.REC + '/LIC_list_frozen.csv', P.REC + '/EMG2_LIC_LIST.csv'):
        if os.path.exists(f): out |= set(pd.read_csv(f, dtype=str).code)
    return out


# ---------------------------------------------------------------- state
def state_path(): return P.STATE_DIR + '/blind3_state.json'
def out_dir(): return P.REC + '/shadow'

def new_book(bid, kind, cap, seed=None):
    return dict(id=bid, kind=kind, capital=cap, seed=seed, rng_state=None, rs={}, cash=cap, holdings={}, orders=None, trades=[], divs=[], ntrades=0,
                nav={B3_START: cap}, spread_paid=0.0, brok_paid=0.0, tax_paid=0.0, fy=0.0, carry=0.0, events=[])

def init_state():
    books = []; cmps = []; fill = P.next_session(B3_START)
    for tag, cap, s0 in SIZES:
        books.append(new_book(f'BLIND3_{tag}', 'B3', cap))
        books += [new_book(f'BLIND3_RND_{tag}_s{i:03d}', 'B3_RND', cap, seed=s0 + i) for i in range(1, NRAND + 1)]
        cmps.append(PS.new_cmp0(f'BLIND3_CMP_A200_{tag}', {'A200.AU': 1.0}, cap, 0.0, B3_START, fill))
    return dict(record='Big Wins forward paper record -- PAPER line BLIND3, blind build 3 frozen primary BLEND_p6_U400_B2_N15_T1 (PAPER ONLY; information only)',
                amendment='AMENDMENT_shadow_BLIND3.md', design='BLEND_p6_U400_B2_N15_T1', frozen_sha256=FROZEN, start_decision=B3_START, fill_day=fill,
                last_processed=P.prev_session(B3_START), decisions=[], data_blocks=[], last={}, books=books, cmps=cmps)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)

def month_end(d): return P.is_month_end(d)                                                       # (tests patch this name only)
def rnd(b): return b['kind'] == 'B3_RND'
def ev(b, d, x):
    if not rnd(b): b['events'].append([d, x])
def record(b, t):
    b['ntrades'] += 1
    if not rnd(b): b['trades'].append(t)
def shares(h): return sum(l[1] for l in h['lots'])
def cost(h): return sum(l[2] for l in h['lots'])
def px(last, code): return last.get(code, {}).get('p')
def nav_of(b, last): return b['cash'] + sum(shares(h) * (px(last, h['code']) or 0.0) for h in (b['holdings'][k] for k in sorted(b['holdings'])))
def days(a, b_): return (pd.Timestamp(b_) - pd.Timestamp(a)).days

def realise(b, h, q, proceeds, d):
    """FIFO; adds the taxable gain of each part to the book's financial-year total (halved if held >= 367 days, acct3.discount_ok)."""
    out = []; rem = q
    for l in sorted(h['lots'], key=lambda l: l[0]):
        if rem <= 1e-9: break
        x = min(rem, l[1]); c = l[2] * x / l[1]; pr = proceeds * x / q; gn = pr - c
        b['fy'] += gn * 0.5 if (gn > 0 and days(l[0], d) >= 367) else gn
        out.append([l[0], x, round(c, 4), round(pr, 4)]); l[1] -= x; l[2] -= c; rem -= x
    h['lots'] = [l for l in h['lots'] if l[1] > 1e-9]
    return out


# ---------------------------------------------------------------- month-end decision (frozen code)
def twin_scores(b, FE, rk):
    """persistent random score per entity (tools3.RandomScores rule: keep last month's with probability 1 - p, else redraw) over the
    ordinary shares ranked inside the keep set (place <= 800: the only ones the Design can hold or buy); others NaN (= never ranked)."""
    A, ST = frozen(); keep_place = 2 * ST.CONFIG['PRIMARY'][2]
    rng = np.random.default_rng(b['seed'])
    if b['rng_state'] is not None: rng.bit_generator.state = b['rng_state']
    rel = sorted(FE.cols[j] for j in np.flatnonzero(FE.ok & np.isfinite(rk) & (rk <= keep_place)))
    rs = b['rs']
    for c in rel:
        if c not in rs or rng.random() < twin_p(): rs[c] = float(rng.random())
    b['rng_state'] = rng.bit_generator.state; b['rs'] = {c: rs[c] for c in rel}
    arr = np.full(len(FE.cols), np.nan)
    for c, v in b['rs'].items(): arr[FE.cix[c]] = v
    return arr

class _RS:
    def __init__(s, arr): s.arr = arr
    def at(s, view): return s.arr

def window5(E):
    w = [E]
    while len(w) < 5: w.append(P.next_session(w[-1]))
    return w

def decide(b, FE, d, last, E):
    A, ST = frozen(); i = FE.i; rk = FE.rank(i); view = A.View(FE, i); new_s = []
    if b['orders']:
        for o in b['orders'].get('sells', []): ev(b, d, f"sell {o['code']} lapsed (no close in 5 sessions); decided again now")
    b['orders'] = None
    hv = {}; outside = []
    for cid, h in sorted(b['holdings'].items()):
        j = FE.cix.get(cid)
        p = px(last, h['code'])
        if j is None or p is None: outside.append(cid); continue
        bd = min(l[0] for l in h['lots'])
        hv[j] = dict(value=shares(h) * p, cost=cost(h), first_buy_date=pd.Timestamp(bd), days_held=days(bd, d), months_held=None, parcels=len(h['lots']))
    navd = b['cash'] + sum(v['value'] for v in hv.values()) + sum(shares(b['holdings'][c]) * (px(last, b['holdings'][c]['code']) or 0.0) for c in outside)
    strat = ST.factory(FE, None)
    if rnd(b): strat.rs = _RS(twin_scores(b, FE, rk))
    book = A.Book(b['cash'], navd, hv, {}, [])
    sold = []
    for o in strat.sells(view, book):
        j, fr = (o if isinstance(o, tuple) else (o, 1.0)); j = int(j)
        if j in hv and fr > 0 and j not in sold: sold.append(j)
    for cid in outside:
        new_s.append(dict(cid=cid, code=b['holdings'][cid]['code'], rank=None, reason='forced: not in the month-end data'))
    valid = _M['strat'].sig(view)['valid']; kp = 2 * ST.CONFIG['PRIMARY'][2]
    for j in sold:
        cid = FE.cols[j]; inkeep = bool(FE.ok[j] and valid[j] and np.isfinite(rk[j]) and rk[j] <= kp)
        new_s.append(dict(cid=cid, code=b['holdings'][cid]['code'], rank=float(rk[j]) if np.isfinite(rk[j]) else None,
                          reason='rule 4(b) 30+ buy-set names rank above' if inkeep else 'rule 4(a) left the keep set (place > 800, no close today or < 200 priced sessions)'))
    book2 = A.Book(b['cash'], navd, {j: v for j, v in hv.items() if j not in sold}, {}, []); book2.sold = sorted(sold)
    orders, maxh = strat.buys(view, book2)
    keepj = [j for j in hv if j not in sold]; cand = [int(j) for j, w in orders]
    X = FE.Rz[i - 59:i + 1]; new_b = []
    for j, w in orders:
        j = int(j); dup = []
        if (X[:, j] != 0).sum() >= 40:
            with np.errstate(all='ignore'):
                for q in keepj + cand:
                    if q != j and np.corrcoef(X[:, j], X[:, q])[0, 1] > 0.98: dup.append(FE.cols[q])
        new_b.append(dict(cid=FE.cols[j], code=FE.code[j], w=float(w), rank=float(rk[j]) if np.isfinite(rk[j]) else None,
                          cap5=float(0.05 * np.nan_to_num(FE.m20[j])), dup=dup))
    b['orders'] = dict(decision=d, E=E, maxh=maxh, sells=new_s, buys=new_b, sell_window=window5(E)) if (new_s or new_b) else None
    ev(b, d, f"decision: NAV {navd:.2f}; sells {[o['code'] for o in new_s]}; buy list {[o['code'] for o in new_b]}")
    return new_s, new_b


# ---------------------------------------------------------------- one trading day
def run_day(b, d, mkt, last):
    A = frozen()[0]; cl = mkt['close']
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
        record(b, dict(date=d, side='sell', code=s_['code'], shares=q, price=p, half_spread=round(cst, 6), brokerage=round(f, 2), cash=round(pr, 2), reason=s_['reason'], lots=parts))
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
            b['holdings'][x['cid']] = dict(code=x['code'], lots=[[d, q, paid]], rank=x['rank'])
            record(b, dict(date=d, side='buy', code=x['code'], shares=q, price=p, half_spread=round(cst, 6), brokerage=round(f, 2), cash=round(-paid, 2), reason='rule 5 buy', weight=x['w']))
    b['orders'] = dict(o, sells=keep_s, buys=[]) if keep_s else None


def june_tax(b, d):
    net = b['fy'] + b['carry']
    if net > 0: t = 0.32 * net; b['cash'] -= t; b['tax_paid'] += t; b['carry'] = 0.0; ev(b, d, f'June tax A$ {t:.2f} on net realised gains A$ {net:.2f}')
    else: b['carry'] = net
    b['fy'] = 0.0

def payouts(b, FE, d, last):
    """kit rule (acct3 Engine._payout): a holding without a close for more than 20 sessions is paid out at the decision."""
    i = FE.i
    for cid, h in sorted(b['holdings'].items()):
        j = FE.cix.get(cid)
        if j is None:                                                                               # entity gone from the month-end data
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
        record(b, dict(date=d, side='payout', code=h['code'], shares=q, price=lp * term, half_spread=0.0, brokerage=0.0, cash=round(v, 2),
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
    if d >= B3_START and month_end(d):
        if pd.Timestamp(d).month == 6:
            for b in s['books']: june_tax(b, d)
        D, blocked, src = EM.get_bundle(d, log) if bundle is None else bundle
        FE = FEngine(D, names(), lic_codes()); del D
        rk = FE.rank(FE.i); A, ST = frozen(); U = ST.CONFIG['PRIMARY'][2]
        g = _M['strat'].sig(A.View(FE, FE.i)); nuni = int((FE.ok & g['valid'] & (rk <= U)).sum())
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else (f'only {nuni} valid ordinary shares in the top {U} (< {MIN_UNIVERSE})' if nuni < MIN_UNIVERSE else None)
        if FE.asof != d: why = f'bundle ends {FE.asof}, not {d}'
        if why:
            s['data_blocks'].append([d, f'BLIND3 data block: {why}; no decision, holdings kept']); log('BLIND3', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src)
        else:
            for b in s['books']: payouts(b, FE, d, last)
            E = P.next_session(d); orows = []
            for b in s['books']:
                sl, bl = decide(b, FE, d, last, E)
                if not rnd(b):
                    orows += [dict(book=b['id'], type='sell', code=o['code'], weight=None, cost_rank=o['rank'], fill='close of ' + E, rule=o['reason']) for o in sl]
                    orows += [dict(book=b['id'], type='buy', code=o['code'], weight=round(o['w'], 6), cost_rank=o['rank'], fill='close of ' + E + ' (in order until 15 held)', rule='rule 5 buy list') for o in bl]
            os.makedirs(out_dir(), exist_ok=True)
            f = P.write_csv(f'{out_dir()}/blind3_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'type', 'code', 'weight', 'cost_rank', 'fill', 'rule']))
            s['decisions'].append(d)
            info = dict(asof=d, fill_day=E, source=src, universe=nuni, files_sha256={f'shadow/blind3_orders_{d}.csv': f},
                        orders={b['id']: sum(1 for o in orows if o['book'] == b['id']) for b in s['books'] if not rnd(b)})
            log('BLIND3', d, 'decision', info['orders'])
        del FE
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring BLIND3 up to trading day d (after paper_emg2s.run, before the bundle is cleared). None before the start."""
    try:
        if d < B3_START: return None
        frozen()
        s = load()
        if s is None: s = init_state(); log('BLIND3 paper state created; first decision', B3_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('BLIND3', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('BLIND3 ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard
def worst_fall(b):
    v = np.array([b['nav'][k] for k in sorted(b['nav'])], float)
    return float(np.min(v / np.maximum.accumulate(v) - 1)) if len(v) > 1 else 0.0

def sold_after_tax(b, last, d):
    """value if every holding were sold at the last close (kit spread and brokerage) and all tax settled (acct3 end-of-book rule)."""
    A = frozen()[0]; v = b['cash']; fy = b['fy']
    for h in b['holdings'].values():
        p = px(last, h['code'])
        if p is None: continue
        q = shares(h); V = q * p; pr = V * (1 - A.half_spread(h.get('rank') if h.get('rank') is not None else float('nan'), p)) - A.fee(V); v += pr
        for l in h['lots']:
            gn = pr * l[1] / q - l[2]; fy += gn * 0.5 if (gn > 0 and days(l[0], d) >= 367) else gn
    net = fy + b['carry']
    return v - (0.32 * net if net > 0 else 0.0)

def emg2_ref_return():
    """EMG2-18 paper book on A$10,000 (EMG2_18_REF of paper_emg2s: registered sell rule, same start) - for the combined reading."""
    try:
        import paper_emg2s as ES
        s = ES.load()
        if s is None: return None
        b = next(x for x in s['books'] if x['id'] == 'EMG2_18_REF'); return ES.nav_of(b, s['last']) / ES.CAP - 1
    except Exception: return None

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        md.append(f'| **BLIND3 (blind build 3 frozen primary; AMENDMENT_shadow_BLIND3.md)** | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; '
                  'A$10,000 (IBKR fixed) and A$100,000, 100 random twins each; plus the 50/50 EMG2-18 + BLIND3 reading |')
        return rows, md, hold
    last = s['last']; f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else f'{x:+.2%}'
    cm = {c['id']: c for c in s['cmps']}; r10 = None
    for tag, cap, _ in SIZES:
        b = next(x for x in s['books'] if x['id'] == f'BLIND3_{tag}'); a2 = cm[f'BLIND3_CMP_A200_{tag}']
        nav = nav_of(b, last); r = nav / cap - 1; ra = P.nav_of(a2, last) / cap - 1; rsold = sold_after_tax(b, last, s['last_processed']) / cap - 1
        tw = np.array([nav_of(x, last) / cap - 1 for x in s['books'] if rnd(x) and x['capital'] == cap])
        pr = float(np.mean(tw < r)) if len(tw) else None; med = float(np.median(tw)) if len(tw) else None
        if tag == '10k': r10 = r
        rows.append(dict(asof=d, book=b['id'], kind='PAPER BLIND3 (information only)', capital=cap, nav=round(nav, 2), cash=round(b['cash'], 2), holdings=len(b['holdings']),
                         open_orders=0 if not b['orders'] else len(b['orders']['sells']) + len(b['orders']['buys']), return_since_start=round(r, 5),
                         pct_of_random=(None if pr is None else round(pr, 3)), random_median_return=(None if med is None else round(med, 5)),
                         vs_random_median=(None if med is None else round(r - med, 5)), a200_b0_return=round(ra, 5), vs_a200_b0=round(r - ra, 5),
                         ret_after_tax_sold=round(rsold, 5),
                         note=f"FACT: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, modelled spread A$ {b['spread_paid']:,.2f}, tax paid A$ {b['tax_paid']:,.2f}; "
                              f"worst fall (daily) {worst_fall(b):.1%}; {TAG}"))
        md.append(f"| **{b['id']}** (paper; blind-3 frozen primary) | {nav:,.2f} | {f(r)} | vs A200 (A$0) {f(r - ra)}; % of {len(tw)} twins below {'' if pr is None else round(pr, 2)} (median {f(med)}); "
                  f"sold today after tax {f(rsold)}; orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, spread A$ {b['spread_paid']:,.2f}; holdings {len(b['holdings'])}; worst fall {worst_fall(b):.1%} |")
        hs_ = ', '.join(f"{h['code']} {shares(h):,.0f}" for h in b['holdings'].values())
        if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no shares'}" + (f"; paper orders for the close of {b['orders']['E']}" if b['orders'] else ''))
    re_ = emg2_ref_return()
    if r10 is not None and re_ is not None:
        c = 0.5 * (r10 + re_)
        rows.append(dict(asof=d, book='COMBINED_50_50_EMG2_18_BLIND3', kind='PAPER reading (information only; no trades)', capital=10000.0, return_since_start=round(c, 5),
                         note=f'average of the returns of EMG2_18_REF (paper_emg2s, A$10k) {re_:+.4f} and BLIND3_10k {r10:+.4f}; no separate book, no rebalancing'))
        md.append(f"| 50/50 EMG2-18 + BLIND3 (reading only, no trades) | — | {f(c)} | average of EMG2_18_REF {f(re_)} and BLIND3_10k {f(r10)} (A$10k books, same start) |")
    return rows, md, hold
