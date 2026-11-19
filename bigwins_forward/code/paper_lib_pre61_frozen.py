# Big Wins forward PAPER record -- shared engine (rules v1.3 parts B-E, I, J3, Q; amendment AMENDMENT_start_now.md).
# PAPER ONLY: no real money, no broker orders. Nothing here places a trade anywhere; it books simulated fills in a JSON state file.
# Price convention: raw (as-traded) EODHD closes and raw share counts; vendor splits multiply share counts (Q7); dividends are the
# vendor's unadjusted cash per share on the ex-date (I1, A6 in raw units). At a decision day the adjusted close of the cut file equals
# the raw close, so C-rule arithmetic is the same as in the engine.
import os, sys, json, gzip, math, hashlib, time, copy
import numpy as np, pandas as pd

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
FW = S + '/bigwins_forward'
CODE = FW + '/code'
REC = S + '/onedrive/research2/68_forward_record'        # canonical record folder (ledger lives here)
PAPER = REC + '/paper'                                    # owner-facing CSV/markdown outputs
STATE_DIR = FW + '/out/paper_state'                       # engine state (hashed into the ledger)
STATE = STATE_DIR + '/state.json'
DEC_DIR = STATE_DIR + '/decisions'
BULK = FW + '/data/bulk'                                  # daily EODHD bulk files (eod, dividends, splits) per trading day
DATA_ROOT = FW + '/data'
STORE = DATA_ROOT + '/eodhd'                              # forward full-history store (fwd_download.py)
sys.path.insert(0, CODE)
import fwd_ledger as L

RULES_SHA = 'b38abcd773a800392da37af79aaa62dd848a204088ddcd94287565bd628a54b0'
START_DECISION = '2026-11-16'; START_FILL = '2026-11-17'
FALLBACK_DECISION = '2026-11-13'; FALLBACK_FILL = '2026-11-16'
NSEEDS = 200
ETF = ['A200.AU', 'BGBL.AU']
BUNDLE = {}                                               # last decision bundle, read by the SHADOW lines (paper_shadow.py); cleared by paper_daily
HEADER = 'PAPER - Big Wins. Not shown to beat the index. No real money; no broker orders; the AI never places trades.'


# ---------------------------------------------------------------- calendar (A1 for past days; XASX schedule for future days)
_SESS = None
def sessions():
    global _SESS
    if _SESS is None:
        import exchange_calendars as xc
        _SESS = [str(x.date()) for x in xc.get_calendar('XASX', start='2014-01-01', end='2028-12-31').sessions]
    return _SESS

def next_session(d):
    s = sessions(); i = np.searchsorted(s, d, side='right'); return s[i]

def prev_session(d):
    s = sessions(); i = np.searchsorted(s, d, side='left'); return s[i - 1]

def is_month_end(d):
    return next_session(d)[:7] != d[:7]

def is_review(d, book_start):
    return d == book_start or (is_month_end(d) and d[5:7] == '12')

def sessions_between(a, b):
    """sessions strictly after a, up to and including b"""
    return [x for x in sessions() if a < x <= b]

def first_session_on_or_after(d):
    s = sessions(); return s[np.searchsorted(s, d, side='left')]


# ---------------------------------------------------------------- costs (E1, E2)
def brokerage(v): return max(6.60, 0.00088 * v)

def tick(p): return 0.001 if p < 0.10 else (0.005 if p < 2.0 else 0.01)

def half_spread(rank, price):
    base = 0.0010 if (rank is not None and rank <= 100) else (0.0025 if (rank is not None and rank <= 300) else 0.0050)
    return max(base, 0.5 * tick(price) / price)


# ---------------------------------------------------------------- decision tables (B1-B6 via the frozen bw13 code)
def build_decision(asof, download_end, write_snapshot=True, log=print):
    """Runs bw13_prep on the forward store, cut at asof; writes the Q2 snapshot (scores csv, dupcodes, manifest) into REC.
    Returns (decision dict, manifest dict, manifest sha)."""
    import bw13_prep, bw13_snapshot as SN
    class _PD:                                       # bw13_prep reads panel_tr.pkl; the forward store keeps it gzip-compressed (disk budget)
        def __getattr__(self, k): return getattr(pd, k)
        def read_pickle(self, path, *a, **k): return pd.read_pickle(path if os.path.exists(path) else path + '.gz', *a, **k)
    bw13_prep.pd = _PD()
    bw13_prep.DF = DATA_ROOT                         # forward store: FW/data/eodhd/{panel_tr.pkl,symbols.csv,raw/eod/AXJO...}
    SN.DF = DATA_ROOT; SN.REC = REC
    SN.INPUTS = {'eodhd_panel_tr': STORE + ('/panel_tr.pkl' if os.path.exists(STORE + '/panel_tr.pkl') else '/panel_tr.pkl.gz'), 'eodhd_symbols': STORE + '/symbols.csv', 'eodhd_manifest': STORE + '/manifest.tsv',
                 'etp_list': S + '/bigwins_lab/data/etp_list.txt', 'asx_listed_companies_2026-11-14': S + '/bigwins_lab/data/ASXListedCompanies.csv',
                 'code_bw13_prep': CODE + '/bw13_prep.py', 'code_bw13_snapshot': CODE + '/bw13_snapshot.py', 'code_paper_lib': CODE + '/paper_lib.py'}
    if is_month_end(asof): SN.MONTH_ENDS = set(SN.MONTH_ENDS) | {asof}
    cache = {}
    orig = bw13_prep.build
    def build(a, **kw):
        if a not in cache:
            kw['download_end'] = download_end; cache[a] = orig(a, **kw)
        return cache[a]
    SN.bw13_prep = type('M', (), {'build': staticmethod(build), 'sha': staticmethod(bw13_prep.sha)})
    man, msha, top = SN.snapshot(asof)
    D = cache[asof]
    d, p, score, srank, order = SN.table(D, 1, 300)
    sym = pd.read_csv(STORE + '/symbols.csv'); name = dict(zip(sym.Code, sym.Name))
    cols = D['cols']; i = len(D['dates']) - 1
    rows = []
    for j in range(len(score)):
        e = cols[d['col'][j]]; code = e.split('#')[0]
        rows.append(dict(cid=e, code=code, name=str(name.get(code, '')), vrank=int(d['vrank'][j]), medval=float(d['medval'][j]),
                         close10=(None if np.isnan(d['price'][j]) else float(d['price'][j])),
                         rawclose=(None if np.isnan(d['rawclose'][j]) else float(d['rawclose'][j])),
                         sector=(d['sector'][j] or None), score=(None if np.isnan(score[j]) else float(score[j])),
                         p1=(None if np.isnan(p[j, 0]) else float(p[j, 0])),
                         M1=(None if np.isnan(d['M1'][j]) else float(d['M1'][j])), M2=(None if np.isnan(d['M2'][j]) else float(d['M2'][j])),
                         M3=(None if np.isnan(d['M3'][j]) else float(d['M3'][j])), M5=(None if np.isnan(d['M5'][j]) else float(d['M5'][j])),
                         srank=(None if np.isnan(srank[j]) else int(srank[j]))))
    # traded-value ranks of the whole stored table (E2 uses ranks 1-300) and last adjusted close of every company in the file (last())
    t = D['tabs'][max(D['tabs'])]
    ranks = {cols[c]: int(r) for c, r in zip(t['col'], t['vrank']) if r <= 300}
    import glob
    xjo_has = asof in {r['date'][:10] for r in json.load(gzip.open(sorted(glob.glob(STORE + '/raw/eod/AXJO.INDX__*.json.gz'))[-1]))}
    n_close = sum(r['rawclose'] is not None for r in rows)
    dec = dict(asof=asof, download_end=download_end, rows=rows, ranks=ranks, duplog=[list(x) for x in D['duplog']],
               q4=dict(axjo_row=xjo_has, universe=len(rows), with_close=n_close, blocked=(not xjo_has) or n_close < 285),
               manifest=f'manifest_{asof}.json', manifest_sha256=msha, scores_sha256=man['files_sha256'][f'scores_top300_{asof}.csv'])
    os.makedirs(DEC_DIR, exist_ok=True)
    json.dump(dec, open(f'{DEC_DIR}/decision_{asof}.json', 'w'), sort_keys=True)
    BUNDLE.clear(); BUNDLE.update(asof=asof, D=D, blocked=dec['q4']['blocked'])
    return dec, man, msha

def load_decision(asof):
    return json.load(open(f'{DEC_DIR}/decision_{asof}.json'))

def score_order(dec, kind, book):
    """Returns list of (row index, score) in decision order for the book's score: H82 = B4 score; momentum = s1 percentile;
    random = uniform draws from the book's persistent numpy default_rng(seed) stream, one per scored company in table order."""
    rows = dec['rows']
    if kind == 'momentum':
        sc = [r['p1'] for r in rows]
    elif kind == 'random':
        rng = np.random.default_rng(book['seed'])
        if book.get('rng_state'): rng.bit_generator.state = book['rng_state']
        idx = [j for j, r in enumerate(rows) if r['score'] is not None]
        u = rng.random(len(idx)); book['rng_state'] = rng.bit_generator.state
        sc = [None] * len(rows)
        for j, x in zip(idx, u): sc[j] = float(x)
    else:
        sc = [r['score'] for r in rows]
    ok = [j for j in range(len(rows)) if sc[j] is not None]
    ok.sort(key=lambda j: (-sc[j], j))                 # B5: highest first; ties in table (traded-value rank) order
    return ok, sc

def eligible(r, T): return r['close10'] is not None and r['close10'] >= 0.5 and r['medval'] >= 100 * T     # B6 (score checked by caller)


# ---------------------------------------------------------------- daily market data (bulk files)
def load_day(d):
    """{'close': {code: close}, 'vol': {code: volume}, 'div': {code: cash}, 'split': {code: ratio new/old}} for trading day d (codes without .AU)."""
    p = f'{BULK}/{d}'
    if not os.path.exists(p + '/eod.json.gz'): return None
    eod = json.load(gzip.open(p + '/eod.json.gz'))
    out = dict(close={}, vol={}, div={}, split={})
    for r in eod:
        if str(r.get('date', ''))[:10] != d: continue           # bulk returns the last row per code; keep rows dated d only
        c = r.get('close')
        if c is None or c <= 0: continue
        out['close'][r['code']] = float(c); out['vol'][r['code']] = float(r.get('volume') or 0)
    if os.path.exists(p + '/div.json.gz'):
        for r in json.load(gzip.open(p + '/div.json.gz')):
            v = r.get('unadjustedValue') or r.get('value') or r.get('dividend')
            try: v = float(v)
            except (TypeError, ValueError): continue
            if v > 0 and str(r.get('date', ''))[:10] == d and (r.get('currency') in (None, 'AUD')): out['div'][r['code']] = out['div'].get(r['code'], 0) + v
    if os.path.exists(p + '/splits.json.gz'):
        for r in json.load(gzip.open(p + '/splits.json.gz')):
            try:
                a, b = str(r['split']).split('/'); out['split'][r['code']] = float(a) / float(b)
            except Exception: pass
    return out


# ---------------------------------------------------------------- book state
def new_book(bid, kind, capital, contrib=0.0, seed=None, n_fixed=None, start=START_DECISION):
    return dict(id=bid, kind=kind, capital=float(capital), contrib=float(contrib), seed=seed, rng_state=None, n_fixed=n_fixed, start=start,
                cash=float(capital), contributed=0.0, n=None, T=None, holdings={}, orders=[], window_end=None, E=None,
                trades=[], divs=[], flows=[], nav={}, units=float(capital) / 100.0, events=[])

def new_cmp(bid, weights, capital, contrib=0.0, start=START_DECISION):
    return dict(id=bid, kind='comparator', weights=weights, capital=float(capital), contrib=float(contrib), start=start, cash=float(capital),
                contributed=0.0, fund_units={k: 0.0 for k in weights}, pending=[], trades=[], flows=[], nav={}, units=float(capital) / 100.0, events=[])

def live(h): return {c: x for c, x in h.items() if not x.get('awaiting_sale')}

def shares_of(x): return sum(l[1] for l in x['lots'])

def cost_of(x): return sum(l[2] for l in x['lots'])

def nav_of(book, last):
    if book['kind'] == 'comparator':
        return book['cash'] + sum(u * last.get(f[:-3], {}).get('p', 0) for f, u in book['fund_units'].items())
    return book['cash'] + sum(shares_of(x) * last[x['code']]['p'] for x in book['holdings'].values() if x['code'] in last)


# ---------------------------------------------------------------- decisions at a decision day (C3-C9) for engine books
def decide(book, dec, d, last, E, window_end, log):
    kind = book['kind']; rows = dec['rows']; idx = {r['cid']: j for j, r in enumerate(rows)}
    # A7 code-change map: a holding under X continues as Y (lots unchanged)
    for x_, y_, _ in dec['duplog']:
        for cid, h in list(book['holdings'].items()):
            if h['code'] == x_:
                book['holdings'][y_ + '#E'] = dict(h, code=y_); del book['holdings'][cid]; book['events'].append([d, f'A7 code change {x_}->{y_}'])
    # lapse open buys / top-ups (D2)
    lapsed = [o for o in book['orders'] if o['type'] in ('buy', 'topup')]
    for o in lapsed: book['events'].append([d, f"lapsed {o['type']} {o['code']} A${o['amount']:.2f}"])
    book['orders'] = [o for o in book['orders'] if o['type'] == 'sell']
    nav = nav_of(book, last)
    order, sc = score_order(dec, kind, book)
    review = is_review(d, book['start'])
    if review:
        n = book['n_fixed'] or min(30, max(4, int(math.floor(nav / 2500.0))))
        book['n'] = n
    n = book['n']; T = nav / n; book['T'] = T
    cap = math.ceil(0.25 * n); new = []
    lastp = lambda code: last[code]['p']
    if review:
        lst = []; cnt = {}
        for j in order:                                                      # C4
            if len(lst) >= n: break
            r = rows[j]
            if not eligible(r, T): continue
            g = r['sector']
            if g:
                if cnt.get(g, 0) >= cap: continue
                cnt[g] = cnt.get(g, 0) + 1
            lst.append(j)
        lcids = [rows[j]['cid'] for j in lst]
        topups = []
        for cid, h in book['holdings'].items():
            if h.get('awaiting_sale'): continue
            sh = shares_of(h); val = sh * lastp(h['code'])
            if cid not in lcids:                                             # C5 / C6
                q_sell = E
                if val > cost_of(h):
                    qs = []
                    for l in h['lots']:
                        q = first_session_on_or_after(str((pd.Timestamp(l[0]) + pd.Timedelta(days=367)).date()))
                        if E < q <= str((pd.Timestamp(E) + pd.Timedelta(days=31)).date()): qs.append(q)
                    if qs: q_sell = max(qs)
                h['awaiting_sale'] = True
                new.append(dict(type='sell', cid=cid, code=h['code'], shares='all', date=q_sell, decided=d, reason='C5' if q_sell == E else 'C5/C6 deferred'))
            else:                                                            # C7
                if val - 2 * T >= 1000:
                    k = int(math.floor((val - 2 * T) / lastp(h['code'])))
                    if k > 0: new.append(dict(type='sell', cid=cid, code=h['code'], shares=k, date=E, decided=d, reason='C7 trim'))
                elif val < 0.75 * T and T - val >= 1000:
                    topups.append((val / T, cid, h['code'], T - val))
        for j in lst:                                                        # C8
            r = rows[j]
            if r['cid'] not in book['holdings']:
                new.append(dict(type='buy', cid=r['cid'], code=r['code'], name=r['name'], sector=r['sector'], amount=T, decided=d, reason='C8', score=sc[j]))
        for _, cid, code, amt in sorted(topups):
            new.append(dict(type='topup', cid=cid, code=code, amount=amt, decided=d, reason='C7 top-up'))
        book['events'].append([d, f'review: NAV {nav:.2f} n {n} T {T:.2f} list {[rows[j]["code"] for j in lst]}'])
    else:                                                                    # C9
        lv = live(book['holdings']); vac = n - len(lv)
        cnt = {}
        for h in lv.values():
            g = h.get('sector')
            if g: cnt[g] = cnt.get(g, 0) + 1
        for j in order:
            if vac <= 0: break
            r = rows[j]
            if r['cid'] in book['holdings'] or not eligible(r, T): continue
            g = r['sector']
            if g:
                if cnt.get(g, 0) >= cap: continue
                cnt[g] = cnt.get(g, 0) + 1
            new.append(dict(type='buy', cid=r['cid'], code=r['code'], name=r['name'], sector=r['sector'], amount=T, decided=d, reason='C9 vacancy', score=sc[j])); vac -= 1
        book['events'].append([d, f'month-end: NAV {nav:.2f} n {n} T {T:.2f} vacancies filled {[o["code"] for o in new]}'])
    book['orders'] += new; book['E'] = E; book['window_end'] = window_end
    return new


# ---------------------------------------------------------------- one trading day for an engine book (D6 order)
def run_day(book, d, mkt, last, ranks, log):
    cl = mkt['close']; ex = []
    held_before = {cid for cid, h in book['holdings'].items() if any(l[0] < d for l in h['lots'])}
    # Q7 splits (share counts x ratio), recorded
    for cid, h in book['holdings'].items():
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] = l[1] * s
            book['events'].append([d, f"split {h['code']} x{s:g} applied to share count (check against announcement)"])
    # I1 dividends
    for cid in held_before:
        h = book['holdings'][cid]; v = mkt['div'].get(h['code'])
        if v:
            c = shares_of(h) * v; book['cash'] += c; book['divs'].append([d, h['code'], shares_of(h), v, round(c, 2)])
    sold_today = False
    # D1 sells (carried and scheduled)
    keep = []
    for o in book['orders']:
        if o['type'] != 'sell' or o['date'] > d: keep.append(o); continue
        h = book['holdings'].get(o['cid'])
        if h is None: continue
        px = cl.get(h['code'])
        if px is None: keep.append(o); continue                         # carried to the next day with a close
        sh = shares_of(h) if o['shares'] == 'all' else min(o['shares'], shares_of(h))
        hh = half_spread(ranks.get(o['cid']), px)
        proceeds = max(0.0, sh * px * (1 - hh) - brokerage(sh * px))
        book['cash'] += proceeds; sold_today = True
        rem = sh; realised = []
        for l in h['lots']:                                              # D5 oldest first
            if rem <= 0: break
            q = min(rem, l[1]); cpart = l[2] * q / l[1]
            realised.append([l[0], q, cpart, proceeds * q / sh]); l[1] -= q; l[2] -= cpart; rem -= q
        h['lots'] = [l for l in h['lots'] if l[1] > 1e-9]
        book['trades'].append(dict(date=d, side='sell', code=h['code'], shares=sh, price=px, half_spread=hh, brokerage=brokerage(sh * px),
                                   cash=round(proceeds, 2), reason=o['reason'], lots=realised))
        if not h['lots']: del book['holdings'][o['cid']]
    book['orders'] = keep
    # D2 buys on attempt days
    attempt = (book['E'] is not None and d >= book['E'] and d <= (book['window_end'] or d) and (d == book['E'] or sold_today))
    if attempt:
        keep = []; waiting = False
        for o in book['orders']:
            if o['type'] != 'buy': keep.append(o); continue
            a = min(o['amount'], book['cash'])
            if a < max(1000.0, 0.5 * o['amount']): keep.append(o); waiting = True; continue
            px = cl.get(o['code'])
            if px is None: book['events'].append([d, f"buy {o['code']} dropped: no close on attempt day"]); continue
            hh = half_spread(ranks.get(o['cid']), px)
            s = int(math.floor((a - brokerage(a)) / (px * (1 + hh))))
            if s <= 0: book['events'].append([d, f"buy {o['code']} dropped: 0 shares"]); continue
            paid = s * px * (1 + hh) + brokerage(s * px); book['cash'] -= paid
            h = book['holdings'].setdefault(o['cid'], dict(code=o['code'], name=o.get('name', ''), sector=o.get('sector'), lots=[]))
            h['lots'].append([d, s, paid])
            book['trades'].append(dict(date=d, side='buy', code=o['code'], shares=s, price=px, half_spread=hh, brokerage=brokerage(s * px),
                                       cash=round(-paid, 2), reason=o['reason']))
        book['orders'] = keep
        if not waiting:                                                  # D3 top-ups, once, together
            keep = []
            for o in book['orders']:
                if o['type'] != 'topup': keep.append(o); continue
                h = book['holdings'].get(o['cid']); a = min(o['amount'], book['cash']); px = cl.get(o['code'])
                if h is None or h.get('awaiting_sale') or a < 1000 or px is None: book['events'].append([d, f"top-up {o['code']} dropped"]); continue
                hh = half_spread(ranks.get(o['cid']), px); s = int(math.floor((a - brokerage(a)) / (px * (1 + hh))))
                if s <= 0: continue
                paid = s * px * (1 + hh) + brokerage(s * px); book['cash'] -= paid; h['lots'].append([d, s, paid])
                book['trades'].append(dict(date=d, side='buy', code=o['code'], shares=s, price=px, half_spread=hh, brokerage=brokerage(s * px),
                                           cash=round(-paid, 2), reason='C7 top-up'))
            book['orders'] = keep


def run_cmp_day(c, d, mkt):
    cl = mkt['close']
    for f in c['fund_units']:                                           # J3: distribution reinvested on the ex-date (TR)
        code = f[:-3]; v = mkt['div'].get(code); px = cl.get(code)
        if v and px and c['fund_units'][f] > 0:
            c['fund_units'][f] *= (1 + v / px); c['events'].append([d, f'{code} distribution {v} reinvested (EODHD proxy)'])
    keep = []
    for p in c['pending']:
        if p['date'] > d: keep.append(p); continue
        ok = all(cl.get(f[:-3]) for f in c['weights'])
        if not ok: keep.append(p); continue
        for f, w in c['weights'].items():
            amt = p['amount'] * w; net = (amt - brokerage(amt)) / 1.0003; px = cl[f[:-3]]
            c['fund_units'][f] += net / px; c['cash'] -= amt
            c['trades'].append(dict(date=d, side='buy', code=f[:-3], units=net / px, price=px, brokerage=brokerage(amt), cash=round(-amt, 2), reason=p['reason']))
    c['pending'] = keep


def credit_contribution(b, d, last):
    """Lifecycle: A$500 cash credited at the month-end, before C2's NAV. Unit (time-weighted) index keeps returns honest."""
    if b['contrib'] <= 0 or d <= b['start']: return
    nav = nav_of(b, last); price = nav / b['units'] if b['units'] > 0 else 100.0
    b['cash'] += b['contrib']; b['contributed'] += b['contrib']; b['units'] += b['contrib'] / price
    b['flows'].append([d, b['contrib']])
    if b['kind'] == 'comparator':
        b['pending'].append(dict(date=next_session(d), amount=b['contrib'], reason='contribution'))


# ---------------------------------------------------------------- state io + hashing
def save_state(st):
    os.makedirs(STATE_DIR, exist_ok=True); tmp = STATE + '.tmp'
    json.dump(st, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, STATE)
    return L.sha(STATE)

def load_state(): return json.load(open(STATE))

def write_csv(path, df):
    df.to_csv(path, index=False, lineterminator='\n'); return L.sha(path)


# ---------------------------------------------------------------- downloads used by the daily job
def client(log=print):
    sys.path.insert(0, S + '/data_foundation/code/eodhd')
    from client import Client
    return Client(STORE, per_min=300, daily_budget=20000, log=log)

def fetch_bulk(d, cli=None, log=print):
    """Bulk end-of-day file of every AU code for day d, plus that day's dividends and splits (3 requests, 100 API credits each)."""
    cli = cli or client(log); os.makedirs(f'{BULK}/{d}', exist_ok=True); n = {}
    for kind, params in (('eod', {'date': d}), ('div', {'date': d, 'type': 'dividends'}), ('splits', {'date': d, 'type': 'splits'})):
        code, js = cli.get('eod-bulk-last-day/AU', params, 'bulk_' + kind, f'AU_{d}')
        if code != 200 or js is None: raise RuntimeError(f'bulk {kind} {d}: HTTP {code}')
        tmp = f'{BULK}/{d}/{kind}.json.gz.tmp'
        with gzip.open(tmp, 'wt') as f: json.dump(js, f)
        os.replace(tmp, f'{BULK}/{d}/{kind}.json.gz'); n[kind] = len(js)
    return n

def fetch_axjo(since, cli=None, log=print):
    cli = cli or client(log)
    code, js = cli.get('eod/AXJO.INDX', {'from': since}, 'axjo_recent', 'AXJO.INDX')
    if code != 200 or js is None: raise RuntimeError(f'AXJO: HTTP {code}')
    return {r['date'][:10]: float(r['close']) for r in js}
