# Big Wins forward PAPER record -- SHADOW line ACC: "buy on the signal, keep the winners" (68_forward_record/AMENDMENT_shadow_ACC_keep_winners.md).
# SHADOW = not adopted; tracked for information.  PAPER ONLY: no real money, no broker orders, the AI never places trades.
# Own state file (STATE_DIR/accum_state.json), own clock (first decision 2026-11-30, fills at the next session's close), own A$0 comparators.
# Ranking = the SHADOW M3 table that paper_shadow writes at the same month-end (shadow/forward_M3_snapshot_<date>.csv); no table = no decision (K7).
# Never reads or writes the H82 books beyond the month's A7 list in decisions/decision_<date>.json; never touches shadow_state.json.
# Idempotent and resumable: a day is booked once (last_processed); a later run catches up from the stored bulk files.
import os, json, math, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_score as PS

AC_START = '2026-11-30'
CAP, CONTRIB, TRANCHE = 5000.0, 500.0, 500.0
BOOKS = (('SHADOW_ACC_5k_b0', 'zero'), ('SHADOW_ACC_5k_e1', 'v13'))          # primary at A$0; cost stress at v1.3 E1
TAG = 'SHADOW ACC: not adopted; tracked for information; illustration only (A$5k)'


def state_path(): return P.STATE_DIR + '/accum_state.json'
def out_dir(): return P.REC + '/shadow'
def snap_path(d): return f'{out_dir()}/forward_M3_snapshot_{d}.csv'

def fee(b, v): return 0.0 if b['fee'] == 'zero' else P.brokerage(v)


# ---------------------------------------------------------------- state
def init_state():
    fill = P.next_session(AC_START)
    books = [dict(id=i, kind='SHADOW_ACC', fee=f, capital=CAP, contrib=CONTRIB, start=AC_START, cash=CAP, contributed=0.0, holdings={}, orders=[], E=None,
                  trades=[], divs=[], flows=[], nav={AC_START: CAP}, units=CAP / 100.0, events=[]) for i, f in BOOKS]
    cmps = [PS.new_cmp0('SHADOW_ACC_CMP_A200_5k', {'A200.AU': 1.0}, CAP, CONTRIB, AC_START, fill),
            PS.new_cmp0('SHADOW_ACC_CMP_4060_5k', {'A200.AU': 0.4, 'BGBL.AU': 0.6}, CAP, CONTRIB, AC_START, fill)]
    return dict(record='Big Wins forward paper record -- SHADOW ACC buy on the signal, keep the winners (PAPER ONLY; not adopted; tracked for information)',
                amendment='AMENDMENT_shadow_ACC_keep_winners.md', start_decision=AC_START, fill_day=fill, last_processed=P.prev_session(AC_START),
                decisions=[], data_blocks=[], last={}, books=books, cmps=cmps)

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

def credit(b, d, last):                                                             # K2 (as the lifecycle books)
    if b['contrib'] <= 0 or d <= b['start']: return
    nav = nav_of(b, last); price = nav / b['units'] if b['units'] > 0 else 100.0
    b['cash'] += b['contrib']; b['contributed'] += b['contrib']; b['units'] += b['contrib'] / price; b['flows'].append([d, b['contrib']])


# ---------------------------------------------------------------- decision (month-end, after the close)
def read_table(d):
    p = snap_path(d)
    if not os.path.exists(p): return None
    t = pd.read_csv(p)
    if not len(t): return []
    t = t.sort_values('rank', kind='stable')
    return [dict(cid=r.cid, code=r.code, rank=int(r.rank), vrank=int(r.vrank), med=float(r.median_traded_value),
                 close=(None if pd.isna(r.close) else float(r.close)), traded=bool(r.traded_on_day)) for r in t.itertuples()]

def duplog_for(d):
    p = f'{P.DEC_DIR}/decision_{d}.json'
    try: return json.load(open(p)).get('duplog', [])
    except Exception: return []

def decide(b, rows, d, last, E, duplog):
    for o in b['orders']: b['events'].append([d, f"order not filled, dropped: buy {o['code']}"])
    b['orders'] = []
    for x_, y_, _ in duplog:                                                          # K5(b) code change carries the holding
        for cid, h in sorted(b['holdings'].items()):
            if h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; b['events'].append([d, f'code change {x_}->{y_}'])
    for cid, h in sorted(b['holdings'].items()):                                        # K5(a) payout: no close for 20 trading days
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            sh = shares(h); p = last[h['code']]['p']; v = sh * p
            parts = [[l[0], l[1], l[2], v * l[1] / sh] for l in h['lots']]
            b['cash'] += v; del b['holdings'][cid]
            b['trades'].append(dict(date=d, side='payout', code=h['code'], shares=sh, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='K5(a) payout', lots=parts))
            b['events'].append([d, f"payout {h['code']} at last close {p} ({lc})"])
    F = b['cash']; k = int(math.floor(F / TRANCHE + 1e-9))
    new = []
    if k >= 1:
        amt = F / k
        for r in rows:                                                                  # K3
            if len(new) >= k: break
            if r['cid'] in b['holdings'] or not r['traded'] or (r['close'] or 0) < 0.5 or r['med'] < 100 * amt: continue
            new.append(dict(type='buy', cid=r['cid'], code=r['code'], amount=amt, vrank=r['vrank'], rank=r['rank'], reason='K3 buy'))
    b['orders'] = new; b['E'] = E
    b['events'].append([d, f"decision: NAV {nav_of(b, last):.2f} free cash {F:.2f} k {k} orders {', '.join(o['code'] for o in new) or 'none'}"])
    return new


# ---------------------------------------------------------------- one trading day
def run_day(b, d, mkt, last):
    cl = mkt['close']
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                       # Q7 splits
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] *= s
            b['events'].append([d, f"split {h['code']} x{s:g}"])
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                       # I1 dividends, shares held before d
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    for o in b['orders']:                                                               # K4 fills at the close
        p = cl.get(o['code']); a = min(o['amount'], b['cash'])
        if p is None: b['events'].append([d, f"buy {o['code']} dropped: no close on the fill day"]); continue
        hh = P.half_spread(o.get('vrank'), p); s = int(math.floor((a - fee(b, a)) / (p * (1 + hh))))
        if s <= 0: b['events'].append([d, f"buy {o['code']} dropped: 0 shares"]); continue
        paid = s * p * (1 + hh) + fee(b, s * p); b['cash'] -= paid
        h = b['holdings'].setdefault(o['cid'], dict(code=o['code'], lots=[], vrank=o.get('vrank'))); h['lots'].append([d, s, paid])
        b['trades'].append(dict(date=d, side='buy', code=o['code'], shares=s, price=p, half_spread=hh, brokerage=fee(b, s * p), cash=round(-paid, 2),
                                reason=o['reason'], rank=o.get('rank'), vrank=o.get('vrank')))
    b['orders'] = []


def step(s, d, mkt, log):
    last = s['last']
    watch = {'A200', 'BGBL'} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: run_day(b, d, mkt, last)
    for c in s['cmps']: PS.cmp_day0(c, d, mkt)
    info = None
    if d >= AC_START and P.is_month_end(d):
        for b in s['books']: credit(b, d, last)
        for c in s['cmps']: P.credit_contribution(c, d, last)
        rows = read_table(d)
        if rows is None:
            s['data_blocks'].append([d, 'no SHADOW M3 table for this month-end: no ACC decision (K7)']); log('SHADOW ACC', d, 'no M3 table: no decision')
            info = dict(asof=d, blocked=True)
        else:
            for r in rows:
                if r['close'] is not None and r['traded']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); orows = []
            for b in s['books']:
                for o in decide(b, rows, d, last, E, duplog_for(d)):
                    orows.append(dict(book=b['id'], type='buy', code=o['code'], amount_AUD=round(o['amount'], 2), rank=o['rank'], tv_rank=o['vrank'], fill='close of ' + E, rule=o['reason']))
            os.makedirs(out_dir(), exist_ok=True)
            fp = f'{out_dir()}/acc_orders_{d}.csv'
            files = {f'shadow/acc_orders_{d}.csv': P.write_csv(fp, pd.DataFrame(orows, columns=['book', 'type', 'code', 'amount_AUD', 'rank', 'tv_rank', 'fill', 'rule']))}
            s['decisions'].append(d)
            info = dict(asof=d, fill_day=E, files_sha256=files, orders={b['id']: [o['code'] for o in b['orders']] for b in s['books']})
            log('SHADOW ACC', d, 'decision', info['orders'])
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring ACC up to trading day d (after the H82 day and the M3/E3 shadow step). Returns a small dict for the ledger (None before the start)."""
    try:
        if d < AC_START: return None
        s = load()
        if s is None: s = init_state(); log('SHADOW ACC state created; first decision', AC_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('SHADOW ACC', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('SHADOW ACC ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard rows
def twr(b, nav): return (nav / b['units']) / 100.0 - 1 if b['units'] > 0 else float('nan')

def tracking_error(b, c):
    """annualised std of monthly unit-index excess returns vs the comparator; None before 12 monthly returns"""
    me = [x for x in sorted(b['nav']) if x >= AC_START and P.is_month_end(x) and x in c['nav']]
    if len(me) < 13: return None
    rb = [PS.ret_at(b, x) for x in me]; rc = [PS.ret_at(c, x) for x in me]
    ex = [(1 + rb[i]) / (1 + rb[i - 1]) - (1 + rc[i]) / (1 + rc[i - 1]) for i in range(1, len(me))]
    return float(np.std(ex, ddof=1) * math.sqrt(12))

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        rows.append(dict(asof=d, book='SHADOW_ACC_5k_b0', kind='SHADOW_ACC', capital=CAP, note=f'{TAG}; not started: first decision {AC_START}, fills at the close of {P.next_session(AC_START)}'))
        md.append(f'| SHADOW ACC (keep winners; AMENDMENT_shadow_ACC_keep_winners.md) | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026 |')
        return rows, md, hold
    last = s['last']; cm = {c['id']: c for c in s['cmps']}; a2, mx = cm['SHADOW_ACC_CMP_A200_5k'], cm['SHADOW_ACC_CMP_4060_5k']
    ra, rm = twr(a2, P.nav_of(a2, last)), twr(mx, P.nav_of(mx, last))
    a_kept, a_sold = PS.after_tax_cmp0(a2, last, s['last_processed'])
    rak, ras = PS.at_return(a_kept, a2['units']), PS.at_return(a_sold, a2['units'])
    f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else (f'{x:+.2%}' if isinstance(x, float) else str(x))
    for b in s['books']:
        nav = nav_of(b, last); r = twr(b, nav)
        kept, sold = PS.after_tax_engine(b, last, s['last_processed'], lambda cid, code, sh, p, b=b: sh * p * P.half_spread(b['holdings'][cid].get('vrank'), p) + fee(b, sh * p))
        rk, rs = PS.at_return(kept, b['units']), PS.at_return(sold, b['units'])
        te = tracking_error(b, a2)
        rows.append(dict(asof=d, book=b['id'], kind='SHADOW_ACC', capital=b['capital'], contributed=b['contributed'], nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2),
                         cash=round(b['cash'], 2), holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5),
                         a200_b0_return=round(ra, 5), vs_a200_b0=round(r - ra, 5), plan4060_b0_return=round(rm, 5), vs_4060_b0=round(r - rm, 5),
                         after_tax_kept_AUD=round(kept, 2), after_tax_sold_AUD=round(sold, 2), ret_after_tax_kept=round(rk, 5), ret_after_tax_sold=round(rs, 5),
                         a200_b0_ret_after_tax_kept=round(rak, 5), a200_b0_ret_after_tax_sold=round(ras, 5), vs_a200_b0_after_tax_kept=round(rk - rak, 5),
                         vs_a200_b0_after_tax_sold=round(rs - ras, 5), dividends_fy=round(sum(x[4] for x in b['divs']), 2),
                         tracking_error=(None if te is None else round(te, 4)),
                         note=f"{TAG}; brokerage {'A$0' if b['fee'] == 'zero' else 'max(A$6.60, 0.088%)'}; own clock from {s['start_decision']}; M3 ranking; never sold"))
        md.append(f"| {b['id']} (SHADOW ACC) | {nav:,.2f} | {f(r)} | A200 (A$0) {f(ra)} (vs {f(r - ra)}); 40/60 (A$0) {f(rm)} (vs {f(r - rm)}); after tax kept vs A200 kept {f(rk - rak)}; "
                  f"holdings {len(b['holdings'])}; cash {b['cash']:,.2f}; TE {'n/a (<12 months)' if te is None else f'{te:.1%}'}; brokerage {'A$0' if b['fee'] == 'zero' else 'v1.3 E1'} |")
        hs = ', '.join(f"{h['code']} {shares(h):,.0f}" for h in b['holdings'].values())
        if hs or b['orders']: hold.append(f"- {b['id']}: {hs or 'no shares'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    for c in s['cmps']:
        nav = P.nav_of(c, last)
        rows.append(dict(asof=d, book=c['id'], kind='SHADOW comparator', capital=c['capital'], contributed=c['contributed'], nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2),
                         cash=round(c['cash'], 2), holdings=sum(1 for u in c['fund_units'].values() if u > 0), open_orders=len(c['pending']),
                         return_since_start=round(twr(c, nav), 5), note=f"own clock from {s['start_decision']}; A$0 brokerage; EODHD proxy"))
    return rows, md, hold
