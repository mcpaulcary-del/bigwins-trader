# Big Wins forward PAPER record -- SHADOW lines M3 (report 76 §6, R1-R11) and E3 (report 73 §6, T1-T11).
# Governed by 68_forward_record/AMENDMENT_shadow_M3_E3.md and AMENDMENT_shadow_M3_v1.1.md (M3 as tested: improve5 sim5.py/look5.py).  SHADOW = not adopted; tracked for information.
# Also AMENDMENT_v1.5_old_symbols.md (A4(b) XXX_old codes admitted from the first shadow decision) and AMENDMENT_scoring_v2.md (own-clock comparators at A$0 brokerage).
# Also AMENDMENT_v1.6_dup_returns.md (A7(c) daily-return duplicate test from the first shadow decision; from 31 Dec 2026 the H82 bundle carries it).
# PAPER ONLY: no real money, no broker orders, the AI never places trades.  Nothing here touches the H82 state (read only).
# Own state file (STATE_DIR/shadow_state.json), own clock (first decision 2026-11-30, fills next session's close), own comparators.
# Idempotent and resumable: a day is booked once (shadow last_processed); a later run catches up from the stored bulk files.
import os, json, math, time, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_score as PS

SH_START = '2026-11-30'
OLD_FROM = '2026-12-31'            # Amendment v1.5: from this decision the H82 bundle already admits A4(b) codes and is reused
LINES = ('M3', 'E3')
SIZES = (('lifecycle_5k', 5000.0, 500.0), ('25k', 25000.0, 0.0), ('100k', 100000.0, 0.0))
FUND = 'A200'                      # index fund (EODHD A200.AU + distributions; EODHD proxy)
FUND_HS = 0.0003                   # J3 half-spread for fund trades
TAG = 'SHADOW: not adopted; tracked for information'


def state_path(): return P.STATE_DIR + '/shadow_state.json'
def out_dir(): return P.REC + '/shadow'


# ---------------------------------------------------------------- state
def new_book(line, tag, cap, con):
    return dict(id=f'SHADOW_{line}_{tag}', line=line, kind=f'SHADOW_{line}', capital=cap, contrib=con, start=SH_START, cash=cap, contributed=0.0,
                fund_units=0.0, fund_cost=0.0, mode=('fund_only' if cap < 25000 else 'active'), nmin=4, n=None, T=None, holdings={}, orders=[], E=None,
                trades=[], divs=[], flows=[], nav={}, units=cap / 100.0, events=[])

def init_state():
    books = [new_book(l, t, c, k) for l in LINES for (t, c, k) in SIZES]
    for b in books: b['nav'][SH_START] = b['capital']
    cmps = []
    for t, c, k in SIZES:                                                              # AMENDMENT_scoring_v2 §2: A$0 brokerage
        cmps.append(PS.new_cmp0(f'SHADOW_CMP_A200_{t}', {'A200.AU': 1.0}, c, k, SH_START, P.next_session(SH_START)))
        cmps.append(PS.new_cmp0(f'SHADOW_CMP_4060_{t}', {'A200.AU': 0.4, 'BGBL.AU': 0.6}, c, k, SH_START, P.next_session(SH_START)))
    return dict(record='Big Wins forward paper record -- SHADOW lines M3 and E3 (PAPER ONLY; not adopted; tracked for information)',
                amendment='AMENDMENT_shadow_M3_E3.md', start_decision=SH_START, fill_day=P.next_session(SH_START),
                last_processed=P.prev_session(SH_START), decisions=[], data_blocks=[], last={}, books=books, cmps=cmps)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(sst):
    p = state_path(); tmp = p + '.tmp'
    json.dump(sst, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- book arithmetic
def shares(h): return sum(l[1] for l in h['lots'])
def cost(h): return sum(l[2] for l in h['lots'])
def px(last, code): return last.get(code, {}).get('p')

def fund_value(b, last): return b['fund_units'] * (px(last, FUND) or 0.0)

def nav_of(b, last):
    return b['cash'] + fund_value(b, last) + sum(shares(h) * last[h['code']]['p'] for h in (b['holdings'][k] for k in sorted(b['holdings'])) if h['code'] in last)

def tax_owed(b, d):
    """M3 R9: tax owed on the financial year's realised gains (50% discount for parcels held >= 367 days) and dividends at 32% (>= 0)."""
    fy0 = f'{int(d[:4]) - (1 if d[5:7] < "07" else 0)}-07-01'
    st_, lt = 0.0, 0.0
    for t in b['trades']:
        if t['side'] not in ('sell', 'payout') or t['date'] < fy0: continue
        for (bd, q, c, pr) in t.get('lots', []):
            if (pd.Timestamp(t['date']) - pd.Timestamp(bd)).days >= 367: lt += pr - c
            else: st_ += pr - c
    dv = sum(x[4] for x in b['divs'] if x[0] >= fy0)
    loss = min(0.0, st_) + min(0.0, lt); s2, l2 = max(0.0, st_), max(0.0, lt)
    s2 += loss; l2 += min(0.0, s2); s2 = max(0.0, s2); l2 = max(0.0, l2)
    return max(0.0, 0.32 * (s2 + 0.5 * l2) + 0.32 * dv)

def free_cash(b, d):
    return b['cash'] - (tax_owed(b, d) if b['line'] == 'M3' else 0.0)

def credit(b, d, last):
    if b['contrib'] <= 0 or d <= b['start']: return
    nav = nav_of(b, last); price = nav / b['units'] if b['units'] > 0 else 100.0
    b['cash'] += b['contrib']; b['contributed'] += b['contrib']; b['units'] += b['contrib'] / price; b['flows'].append([d, b['contrib']])

def realise(b, h, q, proceeds, d, order):
    """remove q shares from h's lots in the given lot order; returns realised [buy_date, q, cost, proceeds] parts"""
    out = []; rem = q
    for l in sorted(h['lots'], key=order):
        if rem <= 1e-9: break
        x = min(rem, l[1]); c = l[2] * x / l[1]
        out.append([l[0], x, c, proceeds * x / q]); l[1] -= x; l[2] -= c; rem -= x
    h['lots'] = [l for l in h['lots'] if l[1] > 1e-9]
    return out

def lot_order(line, d, trim):
    if not trim: return lambda l: l[0]                                                  # full sale: oldest first (D5)
    lim = 367                                                                           # R7(c) (M3 v1.1) and T6: parcels held 367 days or more first
    return lambda l: (not ((pd.Timestamp(d) - pd.Timestamp(l[0])).days >= lim), -(l[2] / l[1]), l[0])


# ---------------------------------------------------------------- rankings at a decision day (from the bw13_prep bundle)
def _ffill(X):
    T, N = X.shape
    idx = np.where(np.isfinite(X), np.arange(T)[:, None], -1); np.maximum.accumulate(idx, axis=0, out=idx)
    out = np.take_along_axis(X, np.maximum(idx, 0), axis=0); out[idx < 0] = np.nan
    return out, np.where(idx < 0, 10 ** 6, np.arange(T)[:, None] - idx)

def rankings(D):
    """M3 and E3 tables at the bundle's last day. Traded value = adjusted close x volume (Amendment v1.4) for both lines."""
    dates = D['dates']; asof = str(pd.Timestamp(dates[-1]).date()); cols = list(D['cols']); i = len(dates) - 1
    assert i >= 262, 'history too short'
    Pv = D['Pv']; C = D['Craw']; V0 = D['V0']
    with np.errstate(all='ignore'):
        TV = V0 if asof >= '2026-12-31' else np.where(np.isfinite(C) & (C > 0), V0 * Pv / C, 0.0)   # bundle TV before 31 Dec is raw close x volume
    TV = np.nan_to_num(TV, nan=0.0)
    w = slice(i - 251, i + 1); has = np.isfinite(Pv[w]); ncl = has.sum(0); med = np.median(TV[w], axis=0)
    el = np.flatnonzero(ncl >= 200)
    order = sorted(el, key=lambda j: (-med[j], cols[j]))                                 # ties: lower ASX code first
    vr = np.full(len(cols), np.nan); vr[order] = np.arange(1, len(order) + 1)
    Pff, age = _ffill(Pv); P10 = np.where(age <= 10, Pff, np.nan)
    traded = np.isfinite(Pv[i]); close = C[i]
    out = dict(asof=asof, vrank={cols[j]: int(vr[j]) for j in order[:1000]}, med={cols[j]: float(med[j]) for j in order[:1000]})
    def pct(x, m):
        o = np.full(len(x), np.nan); k = m & np.isfinite(x)
        if k.sum(): o[k] = pd.Series(x[k]).rank(method='average').values / k.sum()
        return o
    def table(uni, score, parts):
        m = np.flatnonzero(uni & np.isfinite(score))
        o = m[np.lexsort((vr[m], -score[m]))]
        rows = []
        for r, j in enumerate(o, 1):
            rows.append(dict(cid=cols[j], code=cols[j].split('#')[0], rank=r, score=float(score[j]), vrank=int(vr[j]), median_traded_value=float(med[j]),
                             close=(float(close[j]) if np.isfinite(close[j]) else None), traded_on_day=bool(traded[j]), **{k: float(v[j]) for k, v in parts.items()}))
        return rows
    with np.errstate(all='ignore'):
        u = np.isfinite(vr) & (vr <= 100)                                                 # M3 R4-R5
        s1 = P10[i - 21] / P10[i - 252] - 1; s2 = P10[i] / P10[i - 126] - 1
        hi = np.nanmax(np.where(has, Pv[w], -np.inf), axis=0); hi[~np.isfinite(hi)] = np.nan; s3 = P10[i] / hi
        sc = (pct(s1, u) + pct(s2, u) + pct(s3, u)) / 3.0; sc[~u] = np.nan
        out['M3'] = table(u, sc, dict(s1=s1, s2=s2, s3=s3))
        u3 = np.isfinite(vr) & (vr <= 300)                                                # E3 T2-T3
        lp = np.log(Pff[w]); tt = np.arange(252) - 125.5; ok = np.isfinite(lp).all(0) & u3
        lpm = lp - lp.mean(0); sl = (tt[:, None] * lpm).sum(0) / (tt ** 2).sum()
        rr = lpm - sl * tt[:, None]; se = np.sqrt((rr ** 2).sum(0) / 250 / (tt ** 2).sum())
        tq = np.where(ok, sl / se, np.nan)
        out['E3'] = table(u3, tq, dict(trendq=tq))
    out['universe_closes_300'] = int(sum(1 for j in order[:300] if traded[j]))
    return out


# ---------------------------------------------------------------- decisions (month-end, after the close)
def decide(b, R, d, last, E, duplog, log):
    line = b['line']; rows = R[line]; rk = {r['cid']: r['rank'] for r in rows}; vr = R['vrank']; new = []
    for o in b['orders']: b['events'].append([d, f"order not filled, dropped: {o['type']} {o.get('code', FUND)}"])
    b['orders'] = []
    for x_, y_, _ in duplog:                                                              # code change carries the holding (R10 / A7)
        for cid, h in sorted(b['holdings'].items()):
            if h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; b['events'].append([d, f'code change {x_}->{y_}'])
    for cid, h in sorted(b['holdings'].items()):                                            # R10 / C1 payout: no close for 20 trading days
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            sh = shares(h); p = last[h['code']]['p']; v = sh * p
            parts = realise(b, h, sh, v, d, lambda l: l[0]); b['cash'] += v; del b['holdings'][cid]
            b['trades'].append(dict(date=d, side='payout', code=h['code'], shares=sh, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='payout (R10/C1)', lots=parts))
            b['events'].append([d, f"payout {h['code']} at last close {p} ({lc})"])
    nav = nav_of(b, last); fv = fund_value(b, last); pf = px(last, FUND)
    hs = lambda cid, p: P.half_spread(vr.get(cid), p)
    est_sell = lambda cid, q, p: max(0.0, q * p * (1 - hs(cid, p)) - P.brokerage(q * p))
    switch = False
    if b['mode'] == 'fund_only':
        switch = nav >= 25000 and (line == 'M3' or d[5:7] == '12')                      # M3 R3; E3 T10 (December month-end only)
        if not switch:
            a = free_cash(b, d)
            lo = (1000.0 if b['fund_units'] > 0 else 10.0) if line == 'M3' else 100.0     # M3 v1.1 R3: orders >= A$1,000, the first any size
            if a >= lo: new.append(dict(type='fund_buy', amount=a, min_amount=lo, reason='R3 fund only' if line == 'M3' else 'T10 fund only'))
            b['orders'] = new; b['E'] = E; b['events'].append([d, f'fund only: NAV {nav:.2f}, fund buy {a:.2f}']); return new
        b['mode'] = 'active'; b['nmin'] = 10 if line == 'E3' else 4
        b['events'].append([d, f'small-account rule ends at NAV {nav:.2f} ({"R3" if line == "M3" else "T10"})'])
    kept = {}; proceeds = 0.0
    for cid, h in sorted(b['holdings'].items()):
        r = rk.get(cid); v_ = vr.get(cid); p = last[h['code']]['p']; sh = shares(h); val = sh * p; gain = val > cost(h)
        age = (pd.Timestamp(d) - pd.Timestamp(min(l[0] for l in h['lots']))).days
        if line == 'M3':
            bad = r is None or r > 50                                                     # R7(a) v1.1: no rank = outside the 100-name universe or a score input missing
            h['bad'] = h.get('bad', 0) + 1 if bad else 0
            sell = (h['bad'] >= 2 and not (gain and age < 366)) and 'R7(a)' or (d[5:7] == '05' and (r is None or r > 50) and not gain and 'R7(b)')
        else:
            bad = r is None or r > 200
            h['bad'] = h.get('bad', 0) + 1 if bad else 0
            wait = gain and 300 <= age <= 365 and r is not None and r <= 210
            sell = (h['bad'] >= 2 and not wait) and 'T5' or (d[5:7] == '05' and h['bad'] >= 1 and not gain and 'T5 May')
        if sell:
            new.append(dict(type='sell', cid=cid, code=h['code'], shares='all', vrank=v_, reason=sell)); proceeds += est_sell(cid, sh, p)
        else: kept[cid] = (h, r, val, p)
    fund_buy = fund_sell = 0.0
    if line == 'M3':
        if switch: fund_sell = max(0.0, fv - 0.5 * nav)                                    # R3: fund sold down to 50%
        elif fv < 0.5 * nav:                                                              # R2 (v1.1): sized from free cash before the day's sales, orders >= A$1,000
            fund_buy = min(0.5 * nav - fv, free_cash(b, d))
            if fund_buy < 1000: fund_buy = 0.0
        sat = nav - (fv - fund_sell + fund_buy)
        n = min(30, max(4, int(math.floor(sat / 2500.0)))); T = sat / n; base = sat
        hi_cap, hi_to = max(0.15 * sat, 2 * T), max(0.10 * sat, 4 * T / 3)
    else:
        if switch: fund_sell = fv                                                          # T10: fund sold
        n = min(30, max(b['nmin'], int(math.floor(nav / 2500.0)))); T = nav / n; base = nav
        hi_cap, hi_to = max(0.15 * nav, 2 * T), max(0.10 * nav, 4 * T / 3)
    b['n'] = n; b['T'] = T
    if fund_sell > 0 and pf:
        new.append(dict(type='fund_sell', units=min(b['fund_units'], fund_sell / pf), reason='R3 sell-down to 50%' if line == 'M3' else 'T10 fund sold'))
        proceeds += max(0.0, fund_sell * (1 - FUND_HS) - P.brokerage(fund_sell))
    for cid, (h, r, val, p) in kept.items():                                              # R7(c) / T6 trims
        if val > hi_cap:
            k = int(math.floor((val - hi_to) / p))
            if k > 0: new.append(dict(type='sell', cid=cid, code=h['code'], shares=k, vrank=vr.get(cid), reason='R7(c) trim' if line == 'M3' else 'T6 trim')); proceeds += est_sell(cid, k, p)
    if fund_buy > 0: new.append(dict(type='fund_buy', amount=fund_buy, min_amount=1000.0, reason='R2 fund core'))
    free = free_cash(b, d) + proceeds - fund_buy
    cnt = len(kept); zone = 15 if line == 'M3' else 30; mn = max(1000.0, 0.5 * T)
    for r in rows:                                                                        # R8 / T7 buys
        if cnt >= n or r['rank'] > zone: break
        if r['cid'] in b['holdings'] or not r['traded_on_day'] or (r['close'] or 0) < 0.5 or r['median_traded_value'] < 100 * T: continue
        a = min(T, free)
        if a < mn: break
        new.append(dict(type='buy', cid=r['cid'], code=r['code'], amount=a, min_amount=mn, vrank=r['vrank'], rank=r['rank'], reason='R8 buy' if line == 'M3' else 'T7 buy'))
        free -= a; cnt += 1
    if cnt >= n:                                                                          # R8 top-up (M3 v1.1) / T8: only when the book is full
        lim = 50 if line == 'M3' else 200; tops = []
        for cid, (h, r, val, p) in kept.items():
            if r is not None and r <= lim and val < 0.75 * T and T - val >= 1000: tops.append((val / T, cid, h['code'], T - val))
        for _, cid, code, amt in sorted(tops):
            a = min(amt, free)
            if a < 1000: continue
            new.append(dict(type='topup', cid=cid, code=code, amount=a, vrank=vr.get(cid), reason='R8 top-up' if line == 'M3' else 'T8 top-up')); free -= a
    b['orders'] = new; b['E'] = E
    b['events'].append([d, f"decision: NAV {nav:.2f} fund {fv:.2f} base {base:.2f} n {n} T {T:.2f} orders " +
                        ', '.join(f"{o['type']} {o.get('code', FUND)}" for o in new)])
    return new


# ---------------------------------------------------------------- one trading day
def run_day(b, d, mkt, last, log):
    cl = mkt['close']
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                                                      # Q7 splits
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] *= s
            b['events'].append([d, f"split {h['code']} x{s:g}"])
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                                                      # I1 dividends (held before d)
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    v = mkt['div'].get(FUND)
    if v and b['fund_units'] > 0:                                                         # fund distribution as cash (amendment §3)
        c = b['fund_units'] * v; b['cash'] += c; b['divs'].append([d, FUND, b['fund_units'], v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    rem = []
    def ev(s): b['events'].append([d, s])
    for o in [o for o in b['orders'] if o['type'] == 'sell']:
        h = b['holdings'].get(o['cid']); p = cl.get(o['code'])
        if h is None: continue
        if p is None: ev(f"sell {o['code']} not filled (no close); decided again next month-end"); continue
        sh = shares(h) if o['shares'] == 'all' else min(o['shares'], shares(h)); hh = P.half_spread(o.get('vrank'), p)
        pr = max(0.0, sh * p * (1 - hh) - P.brokerage(sh * p)); b['cash'] += pr
        parts = realise(b, h, sh, pr, d, lot_order(b['line'], d, o['shares'] != 'all'))
        b['trades'].append(dict(date=d, side='sell', code=o['code'], shares=sh, price=p, half_spread=hh, brokerage=P.brokerage(sh * p), cash=round(pr, 2), reason=o['reason'], lots=parts))
        if not h['lots']: del b['holdings'][o['cid']]
        else: h['bad'] = h.get('bad', 0)
    pf = cl.get(FUND)
    for o in [o for o in b['orders'] if o['type'] == 'fund_sell']:
        if pf is None: ev('fund sale not filled (no close)'); continue
        u = min(o['units'], b['fund_units']); g = u * pf; pr = max(0.0, g * (1 - FUND_HS) - P.brokerage(g))
        c = b['fund_cost'] * u / b['fund_units'] if b['fund_units'] > 0 else 0.0
        b['fund_units'] -= u; b['fund_cost'] -= c; b['cash'] += pr
        b['trades'].append(dict(date=d, side='sell', code=FUND, units=u, price=pf, half_spread=FUND_HS, brokerage=P.brokerage(g), cash=round(pr, 2), reason=o['reason'],
                                lots=[[b.get('fund_first') or d, u, c, pr]]))
    for o in [o for o in b['orders'] if o['type'] == 'fund_buy']:
        a = min(o['amount'], free_cash(b, d)); lo = o.get('min_amount', 1000.0 if o['reason'] == 'R2 fund core' else 100.0)
        if pf is None or a < lo: ev(f'fund buy dropped (close {pf}, amount {a:.2f})'); continue
        net = (a - P.brokerage(a)) / (1 + FUND_HS); b['fund_units'] += net / pf; b['fund_cost'] += a; b['cash'] -= a
        b.setdefault('fund_first', d)
        b['trades'].append(dict(date=d, side='buy', code=FUND, units=net / pf, price=pf, half_spread=FUND_HS, brokerage=P.brokerage(a), cash=round(-a, 2), reason=o['reason']))
    stop = False
    for o in [o for o in b['orders'] if o['type'] in ('buy', 'topup')]:
        if o['type'] == 'buy' and stop: ev(f"buy {o['code']} dropped (an earlier buy stopped)"); continue
        a = min(o['amount'], free_cash(b, d)); p = cl.get(o['code'])
        if a < (o.get('min_amount', 1000.0)):
            ev(f"{o['type']} {o['code']} dropped: free cash {a:.2f} below minimum")
            if o['type'] == 'buy': stop = True
            continue
        if p is None: ev(f"{o['type']} {o['code']} dropped: no close on the fill day"); continue
        h_ = b['holdings'].get(o['cid'])
        if o['type'] == 'topup' and h_ is None: continue
        hh = P.half_spread(o.get('vrank'), p); s = int(math.floor((a - P.brokerage(a)) / (p * (1 + hh))))
        if s <= 0: ev(f"{o['type']} {o['code']} dropped: 0 shares"); continue
        paid = s * p * (1 + hh) + P.brokerage(s * p); b['cash'] -= paid
        h = b['holdings'].setdefault(o['cid'], dict(code=o['code'], lots=[], bad=0)); h['lots'].append([d, s, paid])
        b['trades'].append(dict(date=d, side='buy', code=o['code'], shares=s, price=p, half_spread=hh, brokerage=P.brokerage(s * p), cash=round(-paid, 2), reason=o['reason']))
    b['orders'] = []


# ---------------------------------------------------------------- bundle for a decision day
_SB = {}                                                                              # preflight fix F5 (ledger seq 84): the rebuilt bundle of day d,
def clear_bundle_cache(): _SB.clear()                                                 # built once per decision day (paper_emg2.clear_bundle clears it)

def bundle_for(d, log):
    """(D, blocked, source).  Normally the bundle the H82 decision just built (paper_lib.BUNDLE); else rebuilt from the forward store cut at d
    (once per day: a second call for the same day returns the same object; blocked is read from paper_lib.BUNDLE on every call)."""
    B = getattr(P, 'BUNDLE', {})
    hb = bool(B.get('blocked')) if B.get('asof') == d else None                       # H82's Q4 test of the same day governs the shadow lines too
    if d >= OLD_FROM and B.get('asof') == d and B.get('D') is not None: return B['D'], hb, 'H82 decision bundle'
    if _SB.get('d') == d: return _SB['D'], hb, _SB['src']
    _SB.clear()
    # Amendments v1.5/v1.6: before 31 Dec 2026 the H82 bundle is built under the frozen A4 and A7(a)/(b), so the shadow lines rebuild it with A4(b) and A7(c) (same file, same cut)
    if B.get('asof') == d: B.pop('D', None)                                           # the H82 decision is done with it; free the memory first
    import bw13_prep
    class _PD:
        def __getattr__(self, k): return getattr(pd, k)
        def read_pickle(self, path, *a, **k): return pd.read_pickle(path if os.path.exists(path) else path + '.gz', *a, **k)
    bw13_prep.pd = _PD(); bw13_prep.DF = P.DATA_ROOT
    D = bw13_prep.build(d, download_end=d, dup_rule='A7b', verbose=False, admit_old=True, dup_ret=True)   # v1.5 A4(b) and v1.6 A7(c) from the first shadow decision
    log('SHADOW', d, 'bundle built from the forward store with A4(b) _old codes admitted (Amendment v1.5) and A7(c) duplicate test (Amendment v1.6)')
    src = 'forward store cut at ' + d + ', A4(b) admitted, A7(c) applied'
    _SB.update(d=d, D=D, src=src)
    return D, hb, src


def write_snapshot(R, d):
    os.makedirs(out_dir(), exist_ok=True); files = {}
    for line, zone, hold in (('M3', 15, 50), ('E3', 30, 200)):
        df = pd.DataFrame(R[line])
        if len(df):
            df.insert(0, 'date', d); df['buy_zone'] = df['rank'] <= zone; df['hold_zone'] = df['rank'] <= hold; df['price_ok_050'] = df['close'].fillna(0) >= 0.5
        f = f'{out_dir()}/forward_{line}_snapshot_{d}.csv'
        files[f'shadow/forward_{line}_snapshot_{d}.csv'] = P.write_csv(f, df)
    return files


def step(sst, d, mkt, log):
    last = sst['last']
    watch = {FUND, 'BGBL'} | {h['code'] for b in sst['books'] for h in b['holdings'].values()} | {o['code'] for b in sst['books'] for o in b['orders'] if 'code' in o}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in sst['books']: run_day(b, d, mkt, last, log)
    for c in sst['cmps']: PS.cmp_day(c, d, mkt)
    info = None
    if d >= SH_START and P.is_month_end(d):
        for b in sst['books']: credit(b, d, last)
        for c in sst['cmps']: P.credit_contribution(c, d, last)
        D, blocked, src = bundle_for(d, log)
        R = rankings(D)
        if blocked is None: blocked = R['universe_closes_300'] < 285
        if blocked:
            sst['data_blocks'].append([d, 'Q4 data block: no shadow decision']); log('SHADOW', d, 'data block: no decision')
            info = dict(asof=d, blocked=True, source=src)
        else:
            for x in ('M3', 'E3'):                                                         # last closes of every ranked company (decision-day raw close)
                for r in R[x]:
                    if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); orows = []
            files = write_snapshot(R, d)
            for b in sst['books']:
                for o in decide(b, R, d, last, E, D.get('duplog', []), log):
                    orows.append(dict(book=b['id'], type=o['type'], code=o.get('code', FUND), amount_AUD=round(o['amount'], 2) if 'amount' in o else None,
                                      shares=o.get('shares', o.get('units')), rank=o.get('rank'), tv_rank=o.get('vrank'), fill='close of ' + E, rule=o['reason']))
            files[f'shadow/orders_{d}.csv'] = P.write_csv(f'{out_dir()}/orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'type', 'code', 'amount_AUD', 'shares', 'rank', 'tv_rank', 'fill', 'rule']))
            sst['decisions'].append(d)
            info = dict(asof=d, fill_day=E, source=src, files_sha256=files, m3_top15=[r['code'] for r in R['M3'][:15]], e3_top30=[r['code'] for r in R['E3'][:30]])
            log('SHADOW', d, 'decision; M3 top 5', info['m3_top15'][:5], 'E3 top 5', info['e3_top30'][:5], 'orders', len(orows))
    for b in sst['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in sst['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    sst['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring the shadow lines up to trading day d (the day the H82 job just booked). Never touches the H82 state.
    Returns a small dict for the daily ledger entry (None before the shadow start)."""
    try:
        if d < SH_START: return None
        sst = load()
        if sst is None: sst = init_state(); log('SHADOW state created; first decision', SH_START)
        decs = []
        for x in P.sessions_between(sst['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('SHADOW', x, 'no bulk file; shadow stops here and resumes on a later run'); break
            info = step(sst, x, m, log)
            ssha = save(sst)
            if info: decs.append(info)
        return dict(last_processed=sst['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('SHADOW ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard rows (SHADOW)
def twr(b, nav): return (nav / b['units']) / 100.0 - 1 if b['units'] > 0 else float('nan')

def scorecard_rows(st, d):
    """(csv rows, markdown lines) for the H82 scorecard; uses only the scorecard's existing columns."""
    sst = load(); rows = []; md = []
    if sst is None:
        for line, rep in (('M3', 'report 76 §6, R1-R11'), ('E3', 'report 73 §6, T1-T11')):
            for t, c, k in SIZES:
                rows.append(dict(asof=d, book=f'SHADOW_{line}_{t}', kind=f'SHADOW_{line}', capital=c, note=f'{TAG}; not started: first decision {SH_START}, fills at the close of {P.next_session(SH_START)}'))
            md.append(f'| SHADOW {line} ({rep}) | — | — | {TAG}; own clock: first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026 (AMENDMENT_shadow_M3_E3.md) |')
        return rows, md, []
    last = sst['last']; cm = {c['id']: c for c in sst['cmps']}; t0 = sst['start_decision']
    rnd = {}
    for b in st['books']:
        if b['kind'] == 'random' and t0 in b['nav']:
            rnd.setdefault(int(b['capital']), []).append(P.nav_of(b, st['last']) / b['nav'][t0] - 1)
    for b in sst['books']:
        tag = b['id'].split('_', 2)[2]; nav = nav_of(b, last); r = twr(b, nav)
        a2, mix = cm[f'SHADOW_CMP_A200_{tag}'], cm[f'SHADOW_CMP_4060_{tag}']
        na, nm = P.nav_of(a2, last), P.nav_of(mix, last); ra, rm = twr(a2, na), twr(mix, nm)
        rv = rnd.get(int(b['capital'])) if b['contrib'] == 0 else None
        rows.append(dict(asof=d, book=b['id'], kind=b['kind'], capital=b['capital'], contributed=b['contributed'], nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2),
                         cash=round(b['cash'], 2), n=b['n'], T=round(b['T'] or 0, 2), holdings=len(b['holdings']), open_orders=len(b['orders']),
                         return_since_start=round(r, 5), a200_return=round(ra, 5), vs_a200=round(r - ra, 5), nav_minus_a200_AUD=round(nav - na, 2),
                         plan4060_return=round(rm, 5), vs_4060=round(r - rm, 5), nav_minus_4060_AUD=round(nav - nm, 2),
                         dividends_fy=round(sum(x[4] for x in b['divs']), 2),
                         pct_of_random=(round(float(np.mean(np.array(rv) < r)), 3) if rv else None),
                         note=f"{TAG}; own clock from {t0}; mode {b['mode']}; fund A$ {fund_value(b, last):,.2f}; random controls measured from {t0}"))
    for c in sst['cmps']:
        nav = P.nav_of(c, last)
        rows.append(dict(asof=d, book=c['id'], kind='SHADOW comparator', capital=c['capital'], contributed=c['contributed'], nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2),
                         cash=round(c['cash'], 2), holdings=sum(1 for u in c['fund_units'].values() if u > 0), open_orders=len(c['pending']),
                         return_since_start=round(twr(c, nav), 5), note=f'own clock from {t0}; EODHD proxy'))
    f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else (f'{x:+.2%}' if isinstance(x, float) else str(x))
    for r in rows:
        if r['kind'].startswith('SHADOW_'):
            md.append(f"| {r['book']} (SHADOW) | {r['nav']:,.2f} | {f(r['return_since_start'])} | A200 {f(r['a200_return'])} (vs {f(r['vs_a200'])}); 40/60 {f(r['plan4060_return'])} "
                      f"(vs {f(r['vs_4060'])}); holdings {r['holdings']}; % of random {'' if r['pct_of_random'] is None else r['pct_of_random']}; {r['note']} |")
    hold = []
    for b in sst['books']:
        hs = ', '.join(f"{h['code']} {shares(h):,.0f}" for h in b['holdings'].values())
        if hs or b['fund_units'] > 0 or b['orders']:
            hold.append(f"- {b['id']}: fund {FUND} {b['fund_units']:.2f} units; {hs or 'no shares'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
