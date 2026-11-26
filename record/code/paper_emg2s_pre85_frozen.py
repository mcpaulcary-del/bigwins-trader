# Big Wins forward PAPER record -- PAPER TWINS of the live EMG2-18 rules (information only):
#   EMG2_18_SIM_H6    (AMENDMENT_shadow_EMG2_18_H6.md: sell off T only after >= 6 month-end decisions)        + 100 random twins (seeds 8760000+i)
#   EMG2_18_SIM_COMBO (AMENDMENT_shadow_EMG2_COMBO.md: sell only after >= 6 decisions AND outside the top 40%) + 100 random twins (seeds 8770000+i)
#   EMG2_18_REF       (same engine, registered sell rule L4; no twins; section R of both amendments)
# Rules L1-L3, L5, L9 of AMENDMENT_live_EMG2_20.md as amended by AMENDMENT_live_EMG2_18.md, mirrored from the trading system's
# decide_emg2_20 (L1 cap on sizing and buys, n = min(18, floor(min(NAV, 10k) / 550)), A$50 reserve, cash shared equally when short,
# orders under A$500 not sent, lottery class skipped). Month-end table = paper_emg2.table on paper_emg2.get_bundle (the EMG2 line's bundle).
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state file STATE_DIR/emg2s_state.json; never reads or writes
# the H82 state or another line's state. Idempotent and resumable: a day is booked once (last_processed); a later run catches up.
import os, json, math, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM

ES_START = '2026-11-30'
CAP = 10000.0; SLOTS = 18; SLOT_UNIT = 550.0; RESERVE = 50.0; MIN_ORDER = 500.0; HALF = 0.005   # L1, L3 (EMG2-18), L5, L9
LOT_AGE = 504; LOT_CLOSE = 0.20; LOT_TV63 = 250000.0                                             # FD s8.6 lottery class
HOLD = 6; KEEP = 0.60                                                                            # L4-H6 / L4-C
NRAND = 100; REDRAW = 0.2
LINES = (('REF', 'L4', None), ('H6', 'H6', 8760000), ('COMBO', 'C', 8770000))
TAG = 'PAPER twins of live EMG2-18 (information only; never evidence for or against EMG2)'


def state_path(): return P.STATE_DIR + '/emg2s_state.json'
def out_dir(): return P.REC + '/shadow'
def brok(v): return P.brokerage(v)                                                               # IBKR max(A$6.60, 0.088%)
def half(p): return max(HALF, 0.5 * P.tick(p) / p)                                               # L9 start: 0.50% a side, half-step floor


def new_book(bid, kind, rule, seed=None):
    return dict(id=bid, kind=kind, rule=rule, seed=seed, rng_state=None, rs={}, cash=CAP, holdings={}, orders=[], E=None,
                trades=[], divs=[], ntrades=0, nav={ES_START: CAP}, spread_paid=0.0, brok_paid=0.0, events=[])

def init_state():
    books = []
    for name, rule, s0 in LINES:
        books.append(new_book('EMG2_18_REF' if name == 'REF' else f'EMG2_18_SIM_{name}', name, rule))
        if s0: books += [new_book(f'EMG2_18_{name}_RND_s{i:03d}', name + '_RND', rule, seed=s0 + i) for i in range(1, NRAND + 1)]
    return dict(record='Big Wins forward paper record -- PAPER twins of live EMG2-18: H6, COMBO, same-engine REF (PAPER ONLY; information only)',
                amendments=['AMENDMENT_shadow_EMG2_18_H6.md', 'AMENDMENT_shadow_EMG2_COMBO.md'], start_decision=ES_START,
                fill_day=P.next_session(ES_START), last_processed=P.prev_session(ES_START), decisions=[], data_blocks=[], last={}, books=books)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)

def month_end(d): return P.is_month_end(d)                                                     # (tests patch this name only)
def rnd(b): return b['kind'].endswith('_RND')
def ev(b, d, x):
    if not rnd(b): b['events'].append([d, x])
def record(b, t):
    b['ntrades'] += 1
    if not rnd(b): b['trades'].append(t)
shares = EM.shares; realise = EM.realise
def nav_of(b, last): return EM.nav_of(b, last)


# ---------------------------------------------------------------- month-end lists
def lottery(D, R):
    """FD s8.6: sessions since the first price row of the bundle < 504, close (day or 5 sessions) < A$0.20, or tv_med63 < A$250k. Missing = lottery."""
    has = np.isfinite(D['Pv']); i = has.shape[0] - 1; cols = list(D['cols']); col = {c: j for j, c in enumerate(cols)}
    first = np.where(has.any(0), has.argmax(0), i + 1)
    out = {}
    for cid, r in R['rows'].items():
        j = col.get(cid)
        age = (i - first[j]) if j is not None else -1
        out[cid] = bool(age < LOT_AGE or not ((r.get('close_5') or 0) >= LOT_CLOSE) or not ((r.get('tv_med63') or 0) >= LOT_TV63))
    return out

def lists_for(b, R):
    """(T best first, K keep zone) for a book: score-based, or a twin's persistent seeded random score over band C (redraw p=0.2)."""
    C = R['C']
    if not rnd(b):
        return list(R['T']), {c for c in C if R['rows'][c]['score_pct'] is not None and R['rows'][c]['score_pct'] > KEEP}
    rng = np.random.default_rng(b['seed'])
    if b['rng_state'] is not None: rng.bit_generator.state = b['rng_state']
    rs = b['rs']
    for c in C:
        if c not in rs or rng.random() < REDRAW: rs[c] = float(rng.random())
    b['rng_state'] = rng.bit_generator.state; b['rs'] = {c: rs[c] for c in C}
    T = sorted((c for c in C if not R['rows'][c]['bid_peg']), key=lambda c: (-rs[c], c))[:len(R['T'])]
    pc = pd.Series([rs[c] for c in C], dtype=float).rank(method='average').values / len(C) if C else []
    return T, {c for c, x in zip(C, pc) if x > KEEP}


def decide(b, R, lot, d, k, last, E, duplog):
    rows = R['rows']; new = []
    for o in b['orders']: ev(b, d, f"order not filled, dropped: {o['type']} {o['code']}")
    b['orders'] = []
    for x_, y_, _ in duplog:                                                                        # A7 code change carries the holding
        for cid, h in sorted(b['holdings'].items()):
            if h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; ev(b, d, f'code change {x_}->{y_}')
    for cid, h in sorted(b['holdings'].items()):                                                    # payout: no close for 20 sessions -> cash at the last close
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            q = shares(h); p = last[h['code']]['p']; v = q * p
            parts = realise(h, q, v); b['cash'] += v; del b['holdings'][cid]
            record(b, dict(date=d, side='payout', code=h['code'], shares=q, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='payout (20 sessions without a close)', lots=parts))
    T, K = lists_for(b, R); tset = set(T)
    nav = nav_of(b, last); sizing = min(nav, CAP)                                                   # L1
    n = max(0, min(SLOTS, int(math.floor(sizing / SLOT_UNIT + 1e-9)))); parcel = sizing / n if n else 0.0   # L3 (EMG2-18)
    proceeds = 0.0; kept = []
    for cid, h in sorted(b['holdings'].items()):
        p = last[h['code']]['p']; q = shares(h); held = k - h['k']
        if rows.get(cid, {}).get('bid_peg'): why = 'bid peg'
        elif b['rule'] == 'L4': why = 'L4 off T' if cid not in tset else None
        elif b['rule'] == 'H6': why = f'L4-H6 off T, held {held} decisions' if (cid not in tset and held >= HOLD) else None
        else: why = f'L4-C outside top 40%, held {held} decisions' if (cid not in K and held >= HOLD) else None
        if why:
            new.append(dict(type='sell', cid=cid, code=h['code'], reason=why)); proceeds += max(0.0, q * p * (1 - half(p)) - brok(q * p))
        else: kept.append(cid)
    kept_value = sum(shares(b['holdings'][c]) * last[b['holdings'][c]['code']]['p'] for c in kept)
    cands = []
    for rank, cid in enumerate(T, 1):                                                               # L2 / L5: best first, lottery and peg skipped
        if len(cands) >= n - len(kept): break
        if cid in b['holdings'] or lot.get(cid, True) or rows[cid]['bid_peg'] or not rows[cid]['traded_on_day'] or rows[cid]['close'] is None: continue
        cands.append((rank, cid))
    avail = min(b['cash'] + proceeds - RESERVE, CAP - kept_value)
    if cands and avail > 0:
        each = math.floor((parcel if parcel * len(cands) <= avail else avail / len(cands)) * 100) / 100
        if each >= MIN_ORDER:
            for rank, cid in cands:
                ref = rows[cid]['close']; q = int(math.floor((each - brok(each)) / ref))
                if q > 0: new.append(dict(type='buy', cid=cid, code=rows[cid]['code'], shares=q, ref=ref, amount=each, rank=rank, k=k, vrank=rows[cid]['tv_rank'], reason='L5 buy'))
        else: ev(b, d, f'{len(cands)} buys not sent: A${each:.2f} each is under A$500')
    b['orders'] = new; b['E'] = E
    ev(b, d, f"decision {k}: NAV {nav:.2f} n {n} parcel {parcel:.2f} orders " + ', '.join(f"{o['type']} {o['code']}" for o in new))
    return new


def run_day(b, d, mkt):
    cl = mkt['close']
    for h in (b['holdings'][x] for x in sorted(b['holdings'])):                                     # splits
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] *= s
            ev(b, d, f"split {h['code']} x{s:g}")
    for h in (b['holdings'][x] for x in sorted(b['holdings'])):                                     # dividends as cash
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    for o in [o for o in b['orders'] if o['type'] == 'sell']:                                       # sells first
        h = b['holdings'].get(o['cid']); p = cl.get(o['code'])
        if h is None: continue
        if p is None: ev(b, d, f"sell {o['code']} not filled (no close); decided again next month-end"); continue
        q = shares(h); hh = half(p); bk = brok(q * p); pr = max(0.0, q * p * (1 - hh) - bk)
        b['cash'] += pr; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk
        parts = realise(h, q, pr); del b['holdings'][o['cid']]
        record(b, dict(date=d, side='sell', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(pr, 2), reason=o['reason'], lots=parts))
    for o in [o for o in b['orders'] if o['type'] == 'buy']:
        p = cl.get(o['code'])
        if p is None: ev(b, d, f"buy {o['code']} not filled: no close on the fill day"); continue
        hh = half(p); q = o['shares']; q0 = q
        while q > 0 and q * p * (1 + hh) + brok(q * p) > b['cash'] - RESERVE + 1e-9: q -= 1               # cut to what the cash covers
        if q <= 0 or (q < q0 and q * p < MIN_ORDER):                                                # the A$500 test applies to the order as sent (decision)
            ev(b, d, f"buy {o['code']} dropped at the fill: cash covers {q} shares (under A$500)"); continue
        bk = brok(q * p); paid = q * p * (1 + hh) + bk; b['cash'] -= paid; b['spread_paid'] += q * p * hh; b['brok_paid'] += bk
        b['holdings'][o['cid']] = dict(code=o['code'], lots=[[d, q, paid]], vrank=o.get('vrank'), k=o['k'])
        record(b, dict(date=d, side='buy', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=bk, cash=round(-paid, 2), reason=o['reason']))
    b['orders'] = []


def step(s, d, mkt, log, bundle=None):
    last = s['last']
    watch = {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: run_day(b, d, mkt)
    info = None
    if d >= ES_START and month_end(d):
        D, blocked, src = EM.get_bundle(d, log) if bundle is None else bundle
        R = EM.table(D); lot = lottery(D, R); duplog = D.get('duplog', [])
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else R['blocked_reason']
        if why:
            s['data_blocks'].append([d, f'EMG2 data block: {why}; no decision, holdings kept']); log('EMG2-18 twins', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src)
        else:
            for r in R['rows'].values():
                if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); k = len(s['decisions']); orows = []
            for b in s['books']:
                for o in decide(b, R, lot, d, k, last, E, duplog):
                    if not rnd(b):
                        orows.append(dict(book=b['id'], type=o['type'], code=o['code'], shares=o.get('shares', 'all'), amount_AUD=o.get('amount'),
                                          list_rank=o.get('rank'), fill='close of ' + E, rule=o['reason']))
            os.makedirs(out_dir(), exist_ok=True)
            f = P.write_csv(f'{out_dir()}/emg2s_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'type', 'code', 'shares', 'amount_AUD', 'list_rank', 'fill', 'rule']))
            s['decisions'].append(d)
            info = dict(asof=d, fill_day=E, source=src, files_sha256={f'shadow/emg2s_orders_{d}.csv': f},
                        orders={x: sum(1 for o in orows if o['book'] == x) for x in ('EMG2_18_REF', 'EMG2_18_SIM_H6', 'EMG2_18_SIM_COMBO')})
            log('EMG2-18 twins', d, 'decision', k, info['orders'])
        del D
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring the EMG2-18 paper twins up to trading day d (after paper_emg2.run, before the bundle is cleared). None before the start."""
    try:
        if d < ES_START: return None
        s = load()
        if s is None: s = init_state(); log('EMG2-18 paper twins state created; first decision', ES_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('EMG2-18 twins', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('EMG2-18 twins ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard
def worst_fall(b): return EM.worst_fall(b)

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        md.append(f'| **EMG2-18 paper twins H6 / COMBO (+ REF)** | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$10,000 each, 100 random twins each |')
        return rows, md, hold
    last = s['last']; f = lambda x: '' if x is None else f'{x:+.2%}'
    bk = {b['id']: b for b in s['books'] if not rnd(b)}
    ret = lambda b: nav_of(b, last) / CAP - 1
    ref = bk['EMG2_18_REF']
    for b in bk.values():
        r = ret(b); tw = np.array([ret(x) for x in s['books'] if x['kind'] == b['kind'] + '_RND'])
        pr = float(np.mean(tw < r)) if len(tw) else None; med = float(np.median(tw)) if len(tw) else None
        rows.append(dict(asof=d, book=b['id'], kind='PAPER twin EMG2-18 (information only)', capital=CAP, nav=round(nav_of(b, last), 2), cash=round(b['cash'], 2),
                         holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), pct_of_random=(None if pr is None else round(pr, 3)),
                         random_median_return=(None if med is None else round(med, 5)),
                         note=f"FACT: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, modelled spread A$ {b['spread_paid']:,.2f}; "
                              f"MOSTLY LUCK: value vs REF {f(r - ret(ref))}; worst fall (daily) {worst_fall(b):.1%}; {TAG}"))
        md.append(f"| **{b['id']}** (paper twin) | {nav_of(b, last):,.2f} | {f(r)} | facts: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, spread A$ {b['spread_paid']:,.2f} "
                  f"(saved vs REF A$ {ref['brok_paid'] - b['brok_paid']:,.2f} brokerage); mostly luck: vs REF {f(r - ret(ref))}"
                  + ('' if pr is None else f", % of {len(tw)} twins below {pr:.2f} (median {f(med)})") + f"; worst fall {worst_fall(b):.1%} |")
        hs_ = ', '.join(f"{h['code']} {shares(h):,.0f}" for h in b['holdings'].values())
        if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no shares'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
