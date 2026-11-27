# Big Wins forward PAPER record -- side lines SWEEP, WIDE, FIP (AMENDMENT_shadow_sidelines_v1.md, ledger seq 91; information only, never
# evidence for or against the main line). Each book = EMG2_18_SIM_BT_C6 (paper_emg2bt6.py, frozen; its functions are CALLED here, never changed)
# with ONE change:
#   SWEEP  cash above A$10,000 (trading-book value at the decision close - A$10,000) buys A200 into a never-sold sleeve at each decision (A$500 min);
#   WIDE   lottery class = age < 504 sessions or close < A$0.20 only (the A$250k traded-value test dropped);
#   FIP    buy order within T = lowest information discreteness first, ID = sign(s1) x (%neg - %pos) over rows i-251..i-21 (research_gaps chk.py V2).
# A$10,000 each, first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; 100 random twins each from the line's own buyable set,
# seeds 8810000+i = the frozen twins' seeds (common random numbers: twin-pair difference i = side twin i - EMG2_18_BT_C6_RND_s{i}).
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Own state files STATE_DIR/sl_<line>_state.json; never reads or writes
# the H82 state or another line's state (reads emg2bt6_state.json read-only for the scorecard). Idempotent and resumable.
import os, json, math, traceback, contextlib
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM, paper_emg2s as ES, paper_emg2bt as BT, paper_emg2bt6 as BT6

SL_START = BT6.C6_START                                          # Mon 30 Nov 2026
CAP = BT6.CAP; FUND = BT6.FUND; FUND_CID = BT6.FUND_CID; RESERVE = ES.RESERVE; MIN_ORDER = ES.MIN_ORDER
NRAND = 100; SEED0 = BT6.SEED0                                   # 8810000 + i, the frozen twins' seeds on purpose (seq 91 s0)
ID_LAG0, ID_LAG1 = 251, 21                                       # FIP window: daily returns of rows i-251 .. i-21 (231 returns)
TAG = 'side line (AMENDMENT_shadow_sidelines_v1.md; information only; never evidence for or against the main line)'


def lottery_wide(D, R):
    """WIDE lottery class: paper_emg2s.lottery without its third test (tv_med63 < A$250k). Missing = lottery."""
    has = np.isfinite(D['Pv']); i = has.shape[0] - 1; col = {c: j for j, c in enumerate(D['cols'])}
    first = np.where(has.any(0), has.argmax(0), i + 1)
    out = {}
    for cid, r in R['rows'].items():
        j = col.get(cid)
        age = (i - first[j]) if j is not None else -1
        out[cid] = bool(age < ES.LOT_AGE or not ((r.get('close_5') or 0) >= ES.LOT_CLOSE))
    return out


def info_discreteness(D, R):
    """FIP ID per band-C entity at the bundle's last row (chk.py V2): sign(s1) * (share of negative - share of positive daily returns) over
    rows i-251..i-21. Daily return = the EMG2 table's total-return factor - 1 (A3/A6; no close = 0), |outliers| (< -95% or > +1000%) = 0."""
    Pv = D['Pv']; N = Pv.shape[1]; has = np.isfinite(Pv); Pf = pd.DataFrame(Pv).ffill().values; i = Pv.shape[0] - 1
    div = np.zeros_like(Pv)
    for r_, lst in D.get('DIVD', {}).items():
        if r_ < Pv.shape[0]:
            for j, v in lst: div[r_, j] += v
    with np.errstate(all='ignore'):
        g = np.where(has[1:] & np.isfinite(Pf[:-1]) & (Pf[:-1] > 0), (Pv[1:] + div[1:]) / Pf[:-1], 1.0)
        g = np.where(np.isfinite(g) & (g > 0), g, 1.0)
    r = g[i - ID_LAG0 - 1:i - ID_LAG1] - 1.0                                                      # g[k] = return of row k+1 -> rows i-251..i-21
    assert r.shape[0] == ID_LAG0 - ID_LAG1 + 1
    r = np.where((r < -0.95) | (r > 10), 0.0, r)
    pos = (r > 0).mean(0); neg = (r < 0).mean(0)
    col = {c: j for j, c in enumerate(D['cols'])}; out = {}
    for cid in R['C']:
        s1 = R['rows'][cid].get('s1'); j = col.get(cid)
        if s1 is None or j is None: continue
        out[cid] = float(np.sign(s1) * (neg[j] - pos[j]))
    return out


_LISTS_FOR = ES.lists_for                                        # the frozen function, kept to restore it whatever happens

@contextlib.contextmanager
def fip_order(ID):
    """FIP: every book's list from paper_emg2s.lists_for is re-ordered by ID ascending (ties: the list's own order); K unchanged.
    The frozen function is wrapped for the duration of this line's decision only and always restored."""
    orig = _LISTS_FOR
    def lists_fip(b, R, lot=None):
        T, K = orig(b, R, lot); pos = {c: k for k, c in enumerate(T)}
        return sorted(T, key=lambda c: (ID.get(c, math.inf), pos[c])), K
    ES.lists_for = lists_fip
    try: yield
    finally: ES.lists_for = orig


LINES = {
    'sweep': dict(key='sl_sweep', name='SWEEP', book='EMG2_18_SIM_BT_C6_SWEEP', twin='EMG2_18_BT_C6_SWEEP_RND', kind='SL_SWEEP', lot='frozen', fip=False, sweep=True,
                  what='cash above A$10,000 buys A200 at each decision (A$500 min)', bar='arithmetic only, reported monthly, no bar'),
    'wide': dict(key='sl_wide', name='WIDE', book='EMG2_18_SIM_BT_C6_WIDE', twin='EMG2_18_BT_C6_WIDE_RND', kind='SL_WIDE', lot='wide', fip=False, sweep=False,
                 what='lottery class = close < A$0.20 or age < 504 only (A$250k test dropped)', bar='after 24 months: WIDE - BT_C6 > P80 of the twin-pair differences and measured spread <= 1.5x model'),
    'fip': dict(key='sl_fip', name='FIP', book='EMG2_18_SIM_BT_C6_FIP', twin='EMG2_18_BT_C6_FIP_RND', kind='SL_FIP', lot='frozen', fip=True, sweep=False,
                what='buy order = most continuous first (frog-in-the-pan ID)', bar='after 36 months: same test as WIDE; low prior'),
}


def state_path(cfg): return P.STATE_DIR + f"/{cfg['key']}_state.json"
def out_dir(): return P.REC + '/shadow'
def month_end(d): return P.is_month_end(d)                                                     # (tests patch this name only)

def new_book(bid, kind, seed=None, sweep=False):
    b = ES.new_book(bid, kind, 'C', seed); b['nav'] = {SL_START: CAP}
    if sweep: b['sleeve'] = dict(cash=0.0, lots=[], pending=None, ntrades=0, brok_paid=0.0, spread_paid=0.0, divs=0.0)
    return b

def init_state(cfg):
    books = [new_book(cfg['book'], cfg['kind'], sweep=cfg['sweep'])] + \
            [new_book(f"{cfg['twin']}_s{i:03d}", cfg['kind'] + '_RND', seed=SEED0 + i, sweep=cfg['sweep']) for i in range(1, NRAND + 1)]
    return dict(record=f"Big Wins forward paper record -- side line {cfg['name']}: EMG2_18_SIM_BT_C6 with one change ({cfg['what']}) (PAPER ONLY; information only)",
                amendments=['AMENDMENT_shadow_EMG2_18_BT.md', 'AMENDMENT_shadow_EMG2_18_BT_leftover.md', 'AMENDMENT_shadow_EMG2_18_BT_C6.md', 'AMENDMENT_twins_buyable_set.md',
                            'AMENDMENT_shadow_sidelines_v1.md'], line=cfg['name'], start_decision=SL_START, fill_day=P.next_session(SL_START),
                last_processed=P.prev_session(SL_START), decisions=[], data_blocks=[], bt=[], state=None, state_from=None, sessions_out=0, me=0, last={}, books=books)

def load(cfg):
    p = state_path(cfg)
    return json.load(open(p)) if os.path.exists(p) else None

def save(cfg, s):
    p = state_path(cfg); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- SWEEP sleeve (never seen by the frozen rules, never sold)
def sleeve_value(b, last):
    sv = b.get('sleeve')
    if sv is None: return 0.0
    q = sum(l[1] for l in sv['lots'])
    return sv['cash'] + (q * last[FUND]['p'] if q and FUND in last else 0.0)

def account_nav(b, last): return BT6.nav_of(b, last) + sleeve_value(b, last)

def sleeve_day(b, d, mkt):
    """After the trading book's own fills of the session: A200 distributions to the sleeve's cash; on/after the planned fill day, at the first
    A200 close: move min(X, trading cash - A$50) (>= 0) to the sleeve and buy whole units with the sleeve's cash if worth >= A$500."""
    sv = b['sleeve']
    v = mkt['div'].get(FUND)
    if v:
        q = sum(l[1] for l in sv['lots'] if l[0] < d)
        if q: sv['cash'] += q * v; sv['divs'] += q * v
    pd_ = sv['pending']
    if pd_ is None or d < pd_['E']: return
    p = mkt['close'].get(FUND)
    if not p: return                                                                                # no A200 close: tried again next session
    t = max(0.0, min(pd_['x'], b['cash'] - RESERVE))
    b['cash'] -= t; sv['cash'] += t; sv['pending'] = None
    hh = BT.half(FUND, p); q = int(math.floor(max(sv['cash'], 0.0) / (p * (1 + hh))))
    while q > 0 and q * p * (1 + hh) + ES.brok(q * p) > sv['cash'] + 1e-9: q -= 1
    if q <= 0 or q * p < MIN_ORDER:
        ES.ev(b, d, f'SWEEP: A${sv["cash"]:.2f} in the sleeve, under A$500 of units; waits for the next decision'); return
    bk = ES.brok(q * p); paid = q * p * (1 + hh) + bk
    sv['cash'] -= paid; sv['lots'].append([d, q, paid]); sv['ntrades'] += 1; sv['brok_paid'] += bk; sv['spread_paid'] += q * p * hh
    ES.ev(b, d, f'SWEEP: moved A${t:.2f} above the cap; bought {q} A200 for A${paid:.2f}')

def plan_sweep(b, last, E):
    """At a month-end decision (after the frozen rules' orders): X = trading-book value - A$10,000; planned if X + sleeve cash >= A$500."""
    sv = b['sleeve']; x = max(0.0, BT6.nav_of(b, last) - CAP)
    sv['pending'] = dict(E=E, x=round(x, 2)) if x + sv['cash'] >= MIN_ORDER else None
    return sv['pending']


# ---------------------------------------------------------------- one session (= paper_emg2bt6.step with the line's one change)
def step(cfg, s, d, mkt, log, bundle=None):
    last = s['last']; nm = cfg['name']
    watch = {FUND} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']:
        BT.run_day(b, d, mkt)
        if cfg['sweep']: sleeve_day(b, d, mkt)
    if s['state'] == 'OFF' and s['state_from'] is not None and d >= s['state_from']: s['sessions_out'] += 1
    info = None
    is_me = d >= SL_START and month_end(d)
    if s['state'] == 'OFF' and s['decisions'] and not is_me:                                       # BT3a/BT3b (seq 75), as paper_emg2bt6
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
                fn = f"{cfg['key']}_sweep_{d}.csv"
                files[f'shadow/{fn}'] = P.write_csv(f'{out_dir()}/{fn}', pd.DataFrame(orows, columns=['book', 'state', 'type', 'code', 'shares', 'amount_AUD', 'fill', 'rule']))
            info = dict(asof=d, sweep=True, fill_day=E, books_with_orders=nb, orders=len(orows), files_sha256=files)
            log(nm, d, 'fund sweep (BF-D34):', nb, 'books with orders;', len(orows), 'orders in', cfg['book'])
    if is_me:
        s['me'] += 1                                                                               # C6 clock: every month-end session counts
        D, blocked, src = EM.get_bundle(d, log) if bundle is None else bundle
        R = EM.table(D); lot = lottery_wide(D, R) if cfg['lot'] == 'wide' else ES.lottery(D, R); duplog = D.get('duplog', [])
        why = 'market-wide verdict failed (H82 Q4 data block of the day)' if blocked else R['blocked_reason']
        if why:
            s['data_blocks'].append([d, f'EMG2 data block: {why}; no decision, holdings and state kept (counts as a month-end for the hold)']); log(nm, d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, source=src, me=s['me'])
        elif FUND not in last:
            s['data_blocks'].append([d, 'no A200 close known; no decision, holdings and state kept (counts as a month-end for the hold)']); log(nm, d, 'no A200 close')
            info = dict(asof=d, blocked=True, reason='no A200 close', source=src, me=s['me'])
        else:
            bt = BT.band_trend(D, d)
            for r in R['rows'].values():
                if r['close'] is not None and r['traded_on_day']: last[r['code']] = dict(p=r['close'], d=d)
            E = P.next_session(d); me = s['me']; orows = []
            ID = info_discreteness(D, R) if cfg['fip'] else None
            ctx = fip_order(ID) if cfg['fip'] else contextlib.nullcontext()
            nsw = 0
            with ctx:
                for b in s['books']:
                    new = BT6.decide_on(b, R, lot, d, me, last, E, duplog) if bt['state'] == 'ON' else BT6.decide_off(b, R, d, me, last, E, duplog)
                    pl = plan_sweep(b, last, E) if cfg['sweep'] else None
                    nsw += pl is not None
                    if not ES.rnd(b):
                        for o in new:
                            orows.append(dict(book=b['id'], state=bt['state'], type=o['type'], code=o['code'], shares=o.get('shares', 'all' if o['type'] == 'sell' else ''),
                                              amount_AUD=o.get('amount'), list_rank=o.get('rank'), fill='close of ' + E, rule=o['reason']))
                        if pl is not None:
                            orows.append(dict(book=b['id'], state=bt['state'], type='sweep', code=FUND, shares='', amount_AUD=pl['x'], list_rank=None, fill='close of ' + E,
                                              rule='SWEEP: cash above A$10,000 to A200 (sleeve)'))
            if bt['state'] != s['state']: s['state_from'] = E
            s['state'] = bt['state']; s['bt'].append(dict(bt, fill_day=E)); s['decisions'].append(d)
            os.makedirs(out_dir(), exist_ok=True); files = {}
            fn = f"{cfg['key']}_orders_{d}.csv"
            files[f'shadow/{fn}'] = P.write_csv(f'{out_dir()}/{fn}', pd.DataFrame(orows, columns=['book', 'state', 'type', 'code', 'shares', 'amount_AUD', 'list_rank', 'fill', 'rule']))
            info = dict(asof=d, fill_day=E, source=src, state=bt['state'], me=me, level=round(bt['level'], 6), mean10=round(bt['mean'], 6), class_rule=bt['class_rule'],
                        files_sha256=files, orders=sum(1 for o in orows if o['book'] == cfg['book']))
            if cfg['lot'] == 'wide':
                info['buyable_in_T'] = dict(wide=sum(1 for c in R['T'] if not lot.get(c, True)), frozen=sum(1 for c in R['T'] if not ES.lottery(D, R).get(c, True)), T=len(R['T']))
            if cfg['fip']: info['id_known'] = sum(1 for c in R['T'] if c in ID)
            if cfg['sweep']: info['books_with_sweep'] = nsw
            log(nm, d, 'decision', len(s['decisions']) - 1, 'month-end', me, 'state', bt['state'], info['orders'], 'orders')
        del D
    for b in s['books']: b['nav'][d] = round(account_nav(b, last), 2)
    s['last_processed'] = d
    return info


def run_line(cfg, d, mkt, log):
    try:
        if d < SL_START: return None
        s = load(cfg)
        if s is None: s = init_state(cfg); log(cfg['name'], 'side line state created; first decision', SL_START)
        decs = []; sweeps = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log(cfg['name'], x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(cfg, s, x, m, log); save(cfg, s)
            if info: (sweeps if info.get('sweep') else decs).append(info)
        out = dict(last_processed=s['last_processed'], state=s['state'], month_ends=s['me'], state_sha256=P.L.sha(state_path(cfg)), decisions=decs or None)
        if sweeps: out['fund_sweeps'] = sweeps
        return out
    except Exception as e:
        log(cfg['name'], 'side line ERROR (no other line affected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])
    finally:
        if ES.lists_for is not _LISTS_FOR: ES.lists_for = _LISTS_FOR                             # belt and braces: the frozen function is always back


def run(d, mkt, log):
    """All three side lines up to trading day d (after the registered lines, before the bundle is cleared). {} before the start."""
    out = {}
    for cfg in LINES.values():
        r = run_line(cfg, d, mkt, log)
        if r is not None: out[cfg['key']] = r
    return out


# ---------------------------------------------------------------- scorecard
def scorecard_rows(d):
    rows, md, hold = [], [], []
    s6 = BT6.load()
    ref = None if s6 is None else next((x for x in s6['books'] if x['id'] == 'EMG2_18_SIM_BT_C6'), None)
    r6 = lambda b: BT6.nav_of(b, s6['last']) / CAP - 1
    tw6 = {} if s6 is None else {x['seed']: r6(x) for x in s6['books'] if x['kind'] == 'BT6_RND'}
    f = lambda x: '' if x is None else f'{x:+.2%}'
    for cfg in LINES.values():
        s = load(cfg)
        if s is None:
            md.append(f"| **{cfg['name']}** `{cfg['book']}` | — | — | {cfg['what']}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$10,000, "
                      f"100 twins (seeds 8810000+i, paired with the BT_C6 twins); bar: {cfg['bar']}; {TAG} |")
            continue
        last = s['last']; ret = lambda b: account_nav(b, last) / CAP - 1
        b = next(x for x in s['books'] if x['id'] == cfg['book']); r = ret(b)
        dr = None if ref is None else r - r6(ref)
        pairs = np.array([ret(x) - tw6[x['seed']] for x in s['books'] if x['kind'].endswith('_RND') and x['seed'] in tw6])
        p80 = float(np.percentile(pairs, 80)) if len(pairs) else None
        pp = float(np.mean(pairs < dr)) if (len(pairs) and dr is not None) else None
        nt = int(np.sum(np.abs(pairs - dr) < 0.005 / CAP)) if (len(pairs) and dr is not None) else 0     # pair differences equal to D (within half a cent)
        tw = np.array([ret(x) for x in s['books'] if x['kind'].endswith('_RND')]); pr = float(np.mean(tw < r)) if len(tw) else None
        st = {'ON': 'EMG2', 'OFF': 'FUND', None: 'not decided yet'}[s['state']]
        extra = ''
        if cfg['sweep']:
            sv = b['sleeve']; q = sum(l[1] for l in sv['lots'])
            extra = (f"; sleeve A$ {sleeve_value(b, last):,.2f} ({q:,.0f} A200, cash A$ {sv['cash']:,.2f}; {sv['ntrades']} sweep orders, brokerage A$ {sv['brok_paid']:,.2f}, "
                     f"spread A$ {sv['spread_paid']:,.2f})" + ('' if ref is None else f"; SWEEP - BT_C6 A$ {account_nav(b, last) - BT6.nav_of(ref, s6['last']):+,.2f}"))
        note = (f"state: {st}; month-ends {s['me']}; {cfg['what']}; FACT: orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, modelled spread A$ {b['spread_paid']:,.2f}{extra}; "
                f"{cfg['name']} - BT_C6 {f(dr)} (after costs, no tax); twin-pair percentile {'' if pp is None else f'{pp:.2f}'} (P80 {f(p80)}; {nt} ties); bar: {cfg['bar']}; {TAG}")
        rows.append(dict(asof=d, book=b['id'], kind=f"side line {cfg['name']} (information only)", capital=CAP, nav=round(account_nav(b, last), 2), cash=round(b['cash'], 2),
                         holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), pct_of_random=(None if pr is None else round(pr, 3)),
                         random_median_return=(None if not len(tw) else round(float(np.median(tw)), 5)), note=note))
        md.append(f"| **{cfg['name']}** `{cfg['book']}` | {account_nav(b, last):,.2f} | {f(r)} | state **{st}**; {cfg['what']}; orders {b['ntrades']}, brokerage A$ {b['brok_paid']:,.2f}, "
                  f"spread A$ {b['spread_paid']:,.2f}{extra}; {cfg['name']} - BT_C6 {f(dr)}" + ('' if pp is None else f"; twin-pair percentile {pp:.2f} (P80 {f(p80)}" + (f"; {nt} of {len(pairs)} equal" if nt else '') + ')')
                  + ('' if pr is None else f"; % of {len(tw)} own twins below {pr:.2f}") + f"; bar: {cfg['bar']} |")
        hs_ = ', '.join(f"{h['code']} {ES.shares(h):,.0f}" + (f" (age {s['me'] - h['k']})" if h['code'] != FUND else '') for h in b['holdings'].values())
        if hs_ or b['orders']: hold.append(f"- {b['id']} (state {st}): {hs_ or 'no holdings'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
