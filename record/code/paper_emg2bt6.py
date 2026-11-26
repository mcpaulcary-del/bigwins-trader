# Big Wins forward PAPER record -- PAPER line EMG2_18_SIM_BT_C6 (AMENDMENT_shadow_EMG2_18_BT_C6.md, ledger seq 80; information only):
#   EMG2_18_SIM_BT (paper_emg2bt.py: BT1-BT4, BT3a/BT3b of seq 75) with one change in state ON: sell rule L4-C ("C6", report 99's frozen X40_H6):
#   a holding is sold only if held >= 6 month-ends since its purchase decision (purchase = 0; every month-end session from the start counts,
#   data blocks included = deep99 eng99 / acct3 months_held) AND it is outside the top 40% of band C (score percentile <= 0.60, or not in band C /
#   the eligible set). BID_PEG sold at once, payout as cash; at an OFF decision every share is sold whatever its age; at an ON decision the fund
#   is always sold (BT4). Buys unchanged. EMG2_18_SIM_BT_C6 + 100 random twins EMG2_18_BT_C6_RND_s001..s100 (seeds 8810000+i), one state for all.
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state file STATE_DIR/emg2bt6_state.json; never reads or writes the
# H82 state or another line's state (reads emg2bt_state.json read-only for the BT_C6 - BT reading of the scorecard). Idempotent and resumable.
import os, json, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM, paper_emg2s as ES, paper_emg2bt as BT

C6_START = BT.BT_START                                           # first decision Mon 30 Nov 2026
CAP = BT.CAP; FUND = BT.FUND; FUND_CID = BT.FUND_CID
HOLD = ES.HOLD                                                   # 6 month-ends (L4-C (a)); keep zone ES.KEEP = 0.60 (L4-C (b))
NRAND = 100; SEED0 = 8810000                                     # seeds assigned by the record keeper (ledger seq 80)
TAG = 'PAPER line EMG2-18 + band-trend switch + sell rule C6 (information only; never evidence for or against EMG2)'


def state_path(): return P.STATE_DIR + '/emg2bt6_state.json'
def out_dir(): return P.REC + '/shadow'
def month_end(d): return P.is_month_end(d)                                                     # (tests patch this name only)


def new_book(bid, kind, seed=None):
    b = ES.new_book(bid, kind, 'C', seed); b['nav'] = {C6_START: CAP}; return b               # rule 'C' = L4-C in paper_emg2s.decide

def init_state():
    books = [new_book('EMG2_18_SIM_BT_C6', 'BT6')] + [new_book(f'EMG2_18_BT_C6_RND_s{i:03d}', 'BT6_RND', seed=SEED0 + i) for i in range(1, NRAND + 1)]
    return dict(record='Big Wins forward paper record -- PAPER line EMG2_18_SIM_BT_C6, EMG2-18 + band-trend switch into A200 + sell rule C6 (PAPER ONLY; information only)',
                amendments=['AMENDMENT_shadow_EMG2_18_BT.md', 'AMENDMENT_shadow_EMG2_18_BT_leftover.md', 'AMENDMENT_shadow_EMG2_18_BT_C6.md'], start_decision=C6_START,
                fill_day=P.next_session(C6_START), last_processed=P.prev_session(C6_START), decisions=[], data_blocks=[], bt=[], state=None, state_from=None,
                sessions_out=0, me=0, last={}, books=books)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)

def nav_of(b, last): return EM.nav_of(b, last)


# ---------------------------------------------------------------- decisions
def decide_on(b, R, lot, d, me, last, E, duplog):
    """State ON: paper_emg2s.decide with rule L4-C and the month-end count `me` as its clock (age = me - me at the purchase decision).
    BT4: the fund is always sold, whatever its age: it is marked ripe before the call (it is never in band C, so L4-C sells it), and the
    sale is labelled as BT4. Its value funds the same decision's buys like any sale (paper_emg2s.decide counts the estimated proceeds)."""
    if FUND_CID in b['holdings']: b['holdings'][FUND_CID]['k'] = me - HOLD - 10**6
    new = ES.decide(b, R, lot, d, me, last, E, duplog)
    for o in new:
        if o['cid'] == FUND_CID: o['reason'] = 'BT4 ON: fund sold'
        elif o['reason'].startswith('L4-C'): o['reason'] = o['reason'].replace(' decisions', ' month-ends')   # the age is counted in month-ends here
    return new

def decide_off(b, R, d, me, last, E, duplog):
    """State OFF: exactly paper_emg2bt.decide_off (every share sold whatever its age; the fund bought / topped up)."""
    return BT.decide_off(b, R, d, me, last, E, duplog)


def step(s, d, mkt, log, bundle=None):
    last = s['last']
    watch = {FUND} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: BT.run_day(b, d, mkt)
    if s['state'] == 'OFF' and s['state_from'] is not None and d >= s['state_from']: s['sessions_out'] += 1
    info = None
    is_me = d >= C6_START and month_end(d)
    if s['state'] == 'OFF' and s['decisions'] and not is_me:                                       # BT3a/BT3b (seq 75, BF-D34), as paper_emg2bt
        since = max([s['decisions'][-1]] + [x[0] for x in s['data_blocks']]); E = P.next_session(d); orows = []
        for b in s['books']:
            new = BT.sweep(b, d, mkt, last, since, E, s['me'])
            if not ES.rnd(b):
                orows += [dict(book=b['id'], state='OFF', type=o['type'], code=o['code'], shares='all' if o['type'] == 'sell' else '', amount_AUD=o.get('amount'),
                               fill='close of ' + E, rule=o['reason']) for o in new]
        nb = sum(1 for b in s['books'] if b['orders'] and b['E'] == E)
        if nb:
            files = {}
            if orows:
                os.makedirs(out_dir(), exist_ok=True)
                files[f'shadow/emg2bt6_sweep_{d}.csv'] = P.write_csv(f'{out_dir()}/emg2bt6_sweep_{d}.csv', pd.DataFrame(orows, columns=['book', 'state', 'type', 'code', 'shares', 'amount_AUD', 'fill', 'rule']))
            info = dict(asof=d, sweep=True, fill_day=E, books_with_orders=nb, orders=len(orows), files_sha256=files)
            log('EMG2-18 BT_C6', d, 'fund sweep (BF-D34):', nb, 'books with orders;', len(orows), 'orders in EMG2_18_SIM_BT_C6')
    if is_me:
        s['me'] += 1                                                                               # L4-C (a): every month-end session counts, data blocks included
        D, blocked, src = EM.get_bundle(d, log) if bundle is None else bundle
        R = EM.table(D); lot = ES.lottery(D, R); duplog = D.get('duplog', [])
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else R['blocked_reason']
        if why:
            s['data_blocks'].append([d, f'EMG2 data block: {why}; no decision, holdings and state kept (counts as a month-end for the hold)']); log('EMG2-18 BT_C6', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src, me=s['me'])
        elif FUND not in last:
            s['data_blocks'].append([d, 'no A200 close known; no decision, holdings and state kept (counts as a month-end for the hold)']); log('EMG2-18 BT_C6', d, 'no A200 close')
            info = dict(asof=d, blocked=True, reason='no A200 close', source=src, me=s['me'])
        else:
            bt = BT.band_trend(D, d)
            for r in R['rows'].values():
                if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); me = s['me']; orows = []
            for b in s['books']:
                new = decide_on(b, R, lot, d, me, last, E, duplog) if bt['state'] == 'ON' else decide_off(b, R, d, me, last, E, duplog)
                if not ES.rnd(b):
                    for o in new:
                        orows.append(dict(book=b['id'], state=bt['state'], type=o['type'], code=o['code'], shares=o.get('shares', 'all' if o['type'] == 'sell' else ''),
                                          amount_AUD=o.get('amount'), list_rank=o.get('rank'), fill='close of ' + E, rule=o['reason']))
            if bt['state'] != s['state']: s['state_from'] = E
            s['state'] = bt['state']; s['bt'].append(dict(bt, fill_day=E)); s['decisions'].append(d)
            os.makedirs(out_dir(), exist_ok=True); files = {}
            files[f'shadow/emg2bt6_orders_{d}.csv'] = P.write_csv(f'{out_dir()}/emg2bt6_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'state', 'type', 'code', 'shares', 'amount_AUD', 'list_rank', 'fill', 'rule']))
            files[f'shadow/emg2bt6_band_{d}.csv'] = P.write_csv(f'{out_dir()}/emg2bt6_band_{d}.csv', pd.DataFrame([dict(month_end=m, level=v, members=n) for m, v, n in bt['levels']]))
            info = dict(asof=d, fill_day=E, source=src, state=bt['state'], me=me, level=round(bt['level'], 6), mean10=round(bt['mean'], 6), class_rule=bt['class_rule'],
                        files_sha256=files, orders=sum(1 for o in orows if o['book'] == 'EMG2_18_SIM_BT_C6'))
            log('EMG2-18 BT_C6', d, 'decision', len(s['decisions']) - 1, 'month-end', me, 'state', bt['state'], f"level {bt['level']:.4f} mean10 {bt['mean']:.4f}", info['orders'], 'orders')
        del D
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring the BT_C6 paper line up to trading day d (after paper_emg2bt.run, before the bundle is cleared). None before the start."""
    try:
        if d < C6_START: return None
        s = load()
        if s is None: s = init_state(); log('EMG2-18 BT_C6 paper line state created; first decision', C6_START)
        decs = []; sweeps = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('EMG2-18 BT_C6', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: (sweeps if info.get('sweep') else decs).append(info)
        out = dict(last_processed=s['last_processed'], state=s['state'], month_ends=s['me'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
        if sweeps: out['fund_sweeps'] = sweeps
        return out
    except Exception as e:
        log('EMG2-18 BT_C6 ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard
def worst_fall(b): return EM.worst_fall(b)

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        md.append(f'| **EMG2_18_SIM_BT_C6** (paper line, band trend -> A200, sell rule C6) | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$10,000, 100 random twins |')
        return rows, md, hold
    last = s['last']; f = lambda x: '' if x is None else f'{x:+.2%}'
    ret = lambda b: nav_of(b, last) / CAP - 1
    b = next(x for x in s['books'] if x['id'] == 'EMG2_18_SIM_BT_C6')
    bs = BT.load(); ref = None if bs is None else next((x for x in bs['books'] if x['id'] == 'EMG2_18_SIM_BT'), None)
    rref = None if ref is None else nav_of(ref, bs['last']) / CAP - 1
    r = ret(b); tw = np.array([ret(x) for x in s['books'] if x['kind'] == 'BT6_RND'])
    pr = float(np.mean(tw < r)) if len(tw) else None; med = float(np.median(tw)) if len(tw) else None
    st = {'ON': 'EMG2', 'OFF': 'FUND', None: 'not decided yet'}[s['state']]
    sv = '' if ref is None else (f"; saved vs BT: A$ {ref['brok_paid'] - b['brok_paid']:,.2f} brokerage, A$ {ref['spread_paid'] - b['spread_paid']:,.2f} spread, "
                                 f"{ref['ntrades'] - b['ntrades']} orders")
    rows.append(dict(asof=d, book=b['id'], kind='PAPER line EMG2-18 + band trend + C6 (information only)', capital=CAP, nav=round(nav_of(b, last), 2), cash=round(b['cash'], 2),
                     holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), pct_of_random=(None if pr is None else round(pr, 3)),
                     random_median_return=(None if med is None else round(med, 5)),
                     note=f"state: {st}; month-ends {s['me']}; FACT: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, modelled spread A$ {b['spread_paid']:,.2f}{sv}; "
                          f"MOSTLY LUCK: BT_C6 - BT {f(None if rref is None else r - rref)} (after costs; no tax modelled); worst fall (daily) {worst_fall(b):.1%}; {TAG}"))
    md.append(f"| **EMG2_18_SIM_BT_C6** (paper line) | {nav_of(b, last):,.2f} | {f(r)} | state: **{st}**; facts: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, "
              f"spread A$ {b['spread_paid']:,.2f}{sv}; mostly luck: BT_C6 - BT {f(None if rref is None else r - rref)}"
              + ('' if pr is None else f"; % of {len(tw)} twins below {pr:.2f} (median {f(med)})") + f"; worst fall {worst_fall(b):.1%} |")
    hs_ = ', '.join(f"{h['code']} {ES.shares(h):,.0f} (age {s['me'] - h['k']})" if h['code'] != FUND else f"{h['code']} {ES.shares(h):,.0f}" for h in b['holdings'].values())
    if hs_ or b['orders']: hold.append(f"- {b['id']} (state {st}): {hs_ or 'no holdings'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
