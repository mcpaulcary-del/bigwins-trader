# Big Wins forward PAPER record -- scoring add-ons (68_forward_record/AMENDMENT_scoring_v2.md).  SCORING ONLY.
# PAPER ONLY: no real money, no broker orders, the AI never places trades.  Never writes the H82 state (state.json is only read).
#  * A$0-brokerage twins of the J3 comparator books (CMP_*_b0), own state file STATE_DIR/score_state.json, re-computed from the
#    account's first fill from the stored daily bulk files and brought forward by the daily job (idempotent; a day is booked once).
#  * After-tax "kept" and "sold" values for engine books (paper_lib / paper_accum format) and for the A$0 comparators.
#  * Helpers used by paper_shadow (shadow comparators at A$0), paper_accum (ACC comparators) and paper_costalt.
import os, json, math
import numpy as np
import paper_lib as P

TAX = 0.32            # F3 marginal rate
DISC = 0.5            # regime A: 50% discount, parcels held 367 days or more
LONG = 367
FUND_HS = 0.0003      # J3 half-spread for fund purchases


def state_path(): return P.STATE_DIR + '/score_state.json'


# ---------------------------------------------------------------- A$0 comparator books
def new_cmp0(bid, weights, capital, contrib, start, fill):
    c = P.new_cmp(bid, weights, capital, contrib, start=start)
    c.update(fee='zero', lots={f: [] for f in weights}, dist=[])
    c['pending'].append(dict(date=fill, amount=float(capital), reason='initial (J3, A$0 brokerage)')); c['nav'][start] = float(capital)
    return c

def cmp_day0(c, d, mkt, brok=None):
    """J3 comparator day at A$0 brokerage (brok: TEST ONLY, a brokerage function to reproduce the frozen J3 books).
    Same order and arithmetic as paper_lib.run_cmp_day; each purchase and each reinvested distribution is a tax parcel."""
    cl = mkt['close']
    for f in c['fund_units']:
        code = f[:-3]; v = mkt['div'].get(code); px = cl.get(code)
        if v and px and c['fund_units'][f] > 0:
            cash = c['fund_units'][f] * v; du = c['fund_units'][f] * (v / px)
            c['fund_units'][f] *= (1 + v / px); c['lots'][f].append([d, du, cash]); c['dist'].append([d, code, cash])
            c['events'].append([d, f'{code} distribution {v} reinvested (EODHD proxy)'])
    keep = []
    for p in c['pending']:
        if p['date'] > d: keep.append(p); continue
        if not all(cl.get(f[:-3]) for f in c['weights']): keep.append(p); continue
        for f, w in c['weights'].items():
            amt = p['amount'] * w; b = brok(amt) if brok else 0.0; net = (amt - b) / 1.0003; px = cl[f[:-3]]
            c['fund_units'][f] += net / px; c['cash'] -= amt; c['lots'][f].append([d, net / px, amt])
            c['trades'].append(dict(date=d, side='buy', code=f[:-3], units=net / px, price=px, brokerage=b, cash=round(-amt, 2), reason=p['reason']))
    c['pending'] = keep

def cmp_day(c, d, mkt):
    """dispatch: A$0 comparators (fee 'zero') here, frozen J3 comparators in paper_lib"""
    if c.get('fee') == 'zero': cmp_day0(c, d, mkt)
    else: P.run_cmp_day(c, d, mkt)


def init_state(st):
    fill = st['fill_day']
    cmps = [new_cmp0(c['id'] + '_b0', c['weights'], c['capital'], c['contrib'], c['start'], fill) for c in st['cmps']]
    return dict(record='Big Wins forward paper record -- A$0-brokerage comparator books (SCORING ONLY; AMENDMENT_scoring_v2.md)',
                amendment='AMENDMENT_scoring_v2.md', start_decision=st['start_decision'], fill_day=fill, last_processed=st['start_decision'], last={}, cmps=cmps)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)

def step(s, d, mkt):
    for code in ('A200', 'BGBL'):
        if code in mkt['close']: s['last'][code] = dict(p=mkt['close'][code], d=d)
    for c in s['cmps']: cmp_day0(c, d, mkt)
    if P.is_month_end(d):
        for c in s['cmps']: P.credit_contribution(c, d, s['last'])
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, s['last']), 2)
    s['last_processed'] = d

def sync(st, log=print):
    """bring the A$0 comparators up to the H82 state's last processed day (reads stored bulk files; never writes state.json)"""
    try:
        s = load()
        if s is None: s = init_state(st); log('SCORE state created (A$0 comparators re-computed from', s['fill_day'], ')')
        for x in P.sessions_between(s['last_processed'], st['last_processed']):
            m = P.load_day(x)
            if m is None: log('SCORE', x, 'no bulk file; A$0 comparators stop here and resume on a later run'); break
            step(s, x, m)
        return dict(last_processed=s['last_processed'], state_sha256=save(s))
    except Exception as e:
        import traceback
        log('SCORE ERROR (H82 unaffected):', repr(e)); log(traceback.format_exc()); return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- unit index and returns at a past day
def units_at(b, d):
    """time-weighted units on day d, rebuilt from the stored NAVs and flows (contribution priced at the NAV before it)"""
    u = float(b['capital']) / 100.0
    for f, a in sorted(b.get('flows', [])):
        if f > d: break
        nb = b['nav'].get(f)
        if nb is None or u <= 0: continue
        u += a / ((nb - a) / u)
    return u

def ret_at(b, d):
    nav = b['nav'].get(d)
    if nav is None: return float('nan')
    return nav / units_at(b, d) / 100.0 - 1


# ---------------------------------------------------------------- after tax
def _tax(st_, lt):
    """tax on net short-term and long-term gains (losses offset short-term first; regime A discount)"""
    loss = min(0.0, st_) + min(0.0, lt); s2, l2 = max(0.0, st_), max(0.0, lt)
    s2 += loss; l2 += min(0.0, s2); s2 = max(0.0, s2); l2 = max(0.0, l2)
    return TAX * (s2 + l2 * (1 - DISC))

def _age(a, b):
    import pandas as pd
    return (pd.Timestamp(b) - pd.Timestamp(a)).days

def after_tax_engine(b, last, d, sale_cost):
    """(kept, sold) A$ for a share book in paper_lib / paper_accum format. sale_cost(cid, code, shares, price) -> A$."""
    st_ = lt = 0.0
    for t in b['trades']:
        if t['side'] not in ('sell', 'payout'): continue
        for (bd, q, c, pr) in t.get('lots', []):
            if _age(bd, t['date']) >= LONG: lt += pr - c
            else: st_ += pr - c
    dv = sum(x[4] for x in b['divs'])
    nav = b['cash'] + sum(sum(l[1] for l in h['lots']) * last[h['code']]['p'] for h in b['holdings'].values() if h['code'] in last)
    kept = nav - TAX * dv - _tax(st_, lt)
    ust, ult, costs = st_, lt, 0.0
    for cid in sorted(b['holdings']):
        h = b['holdings'][cid]
        if h['code'] not in last: continue
        p = last[h['code']]['p']; sh = sum(l[1] for l in h['lots'])
        if sh <= 0: continue
        sc = sale_cost(cid, h['code'], sh, p); costs += sc
        for (bd, q, c) in h['lots']:
            g = q * p - sc * q / sh - c
            if _age(bd, d) >= LONG: ult += g
            else: ust += g
    sold = nav - costs - TAX * dv - _tax(ust, ult)
    return kept, sold

def after_tax_cmp0(c, last, d):
    """(kept, sold) A$ for an A$0 comparator: distributions taxed when paid; sold = all parcels sold at the close (0.03% half-spread)"""
    dv = sum(x[2] for x in c['dist'])
    nav = P.nav_of(c, last)
    kept = nav - TAX * dv
    st_ = lt = 0.0; costs = 0.0
    for f, lots in c['lots'].items():
        p = last.get(f[:-3], {}).get('p')
        if not p: continue
        for (bd, q, cost) in lots:
            g = q * p * (1 - FUND_HS) - cost; costs += q * p * FUND_HS
            if _age(bd, d) >= LONG: lt += g
            else: st_ += g
    sold = nav - costs - TAX * dv - _tax(st_, lt)
    return kept, sold

def engine_sale_cost(ranks, brok=P.brokerage):
    return lambda cid, code, sh, p: sh * p * P.half_spread(ranks.get(cid), p) + brok(sh * p)

def at_return(value, units):
    return value / units / 100.0 - 1 if units > 0 else float('nan')
