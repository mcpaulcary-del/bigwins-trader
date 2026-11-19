# Forward-record EODHD refresh (rules v1.3 Q1): symbol lists + eod/splits/div for every ACTIVE AU common-stock 3-letter code,
# AXJO.INDX and the comparator ETFs, into a separate append-only store (the research store data_foundation/out/eodhd is not touched).
# Delisted codes cannot gain rows; their latest raw files are taken from the research store.  Then builds panel_tr.pkl for the
# forward store with data_foundation's build_tr.symbol_frame (A3 exactly as coded).
#   python3 -I fwd_download.py [--tag YYYYMMDD] [--no-download]
import os, sys, json, gzip, time, argparse
import numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
sys.path.insert(0, S + '/data_foundation/code/eodhd'); sys.path.insert(0, S + '/data_foundation/code')
from client import Client, load_manifest
import download as DL, build_tr
OLD = S + '/data_foundation/out/eodhd'
NEW_ROOT = S + '/bigwins_forward/data'          # bw13_prep.DF is pointed here: NEW_ROOT/eodhd/...
NEW = NEW_ROOT + '/eodhd'
ETF = ['A200.AU', 'BGBL.AU', 'VAS.AU']
EXTRA = ['AXJO.INDX'] + ETF
OLD_RE = r'^[A-Z0-9]{3}_old[0-9]*$'   # Amendment v1.5 (ledger seq 17): vendor-renamed codes of delisted companies (A4(b))

def a4_mask(u):
    """A4 code test incl. Amendment v1.5 A4(b); bw13_prep decides by decision date whether the renamed codes are used"""
    c = u.Code.astype(str)
    return (c.str.len() == 3) | c.str.match(OLD_RE)

def latest(store):
    m = load_manifest(store)
    m = m[(m.http == '200') & (m.file != '') & m.kind.isin(['eod', 'splits', 'div'])].groupby(['kind', 'symbol']).tail(1)
    return {(k, s): os.path.join(store, f) for k, s, f in zip(m.kind, m.symbol, m.file)}

def run(download=True, workers=6, per_min=400, log=print, resume=False, since=None):
    """since (UTC 'YYYY-MM-DDTHH:MM'): refresh only symbols not already fetched at or after that time (idempotent month-end refresh)."""
    os.makedirs(NEW, exist_ok=True)
    cli = Client(NEW, per_min=per_min, daily_budget=20000, log=log)
    if download:
        u = DL.list_symbols(cli, refresh=not resume)
        act = u[(u.Type == 'Common Stock') & (u.Code.astype(str).str.len() == 3) & (u.delisted == 0)].api_symbol.tolist()
        have = latest(OLD); have.update(latest(NEW)); m0 = load_manifest(NEW); have.update({(k, x): '' for k, x, h in zip(m0.kind, m0.symbol, m0.http) if h == '404'})
        olds = [x for x in u[(u.Type == 'Common Stock') & u.Code.astype(str).str.match(OLD_RE)].api_symbol if ('eod', x) not in have]
        if olds: log(f'Amendment v1.5: {len(olds)} renamed _old symbols with no end-of-day file in either store, fetched once: {olds[:20]}')
        act = act + olds
        syms = EXTRA + act
        log(f'{time.strftime("%H:%M:%S")} refreshing {len(syms)} symbols x3')
        if since:
            m = load_manifest(NEW); m = m[(m.utc >= since) & m.http.isin(['200', '404'])]; have = set(zip(m.kind, m.symbol))
            todo = [s for s in syms if any((k, s) not in have for k in ('eod', 'splits', 'div'))]
            log(f'since {since}: {len(syms) - len(todo)} symbols already fresh, {len(todo)} to fetch')
            DL.download(cli, todo, workers=workers, log=log, refresh=True)
        else:
            DL.download(cli, syms, workers=workers, log=log, refresh=not resume)   # resume: skip symbols already fetched into the forward store
    u = pd.read_csv(NEW + '/symbols.csv')
    files = latest(OLD); files.update(latest(NEW))          # new store wins
    ok = set(u[(u.Type == 'Common Stock') & a4_mask(u)].api_symbol) | set(EXTRA)                  # A4 incl. v1.5 A4(b)
    import calendar_fix as CF
    sess = CF.xasx_sessions('1980-01-01', '2027-12-31')
    parts = []
    for s in sorted(x for (k, x) in files if k == 'eod' and x in ok):
        rd = lambda k: build_tr.read_js(files[(k, s)]) if (k, s) in files else []
        d = build_tr.symbol_frame(rd('eod'), rd('splits'), rd('div'))
        if d is None: continue
        if s.endswith('.AU'):
            d = d[d.date.isin(sess)].copy()
            c = d.close.where(d.close > 0); pc = c.shift(1)
            d['ret_pr'] = c * d.split / pc - 1; d['ret_tr'] = (c * d.split + d['div']) / pc - 1
        d.insert(0, 'symbol', s); parts.append(d)
    pan = pd.concat(parts, ignore_index=True)
    # disk budget: keep only what bw13_prep reads (A2 working file starts 2014-06-01; A3 returns were computed on full history above)
    pan = pan.loc[pan.date >= '2014-06-01', ['symbol', 'date', 'high', 'low', 'close', 'volume', 'split', 'div', 'ret_pr', 'ret_tr']].reset_index(drop=True)
    pan[pan.symbol.str.endswith('.AU') & ~pan.symbol.isin(ETF)].to_pickle(NEW + '/panel_tr.pkl.gz', compression='gzip')   # gzip: disk budget (paper_lib shims bw13_prep's reader)
    pan[pan.symbol.isin(ETF)].to_pickle(NEW + '/etf_tr.pkl')
    # AXJO raw file where bw13_prep.axjo() looks for it
    os.makedirs(NEW + '/raw/eod', exist_ok=True)
    log('panel', len(pan), 'rows; last date', pan.date.max().date(), '; symbols with last date', (pan.groupby('symbol').date.max() == pan.date.max()).sum())
    return pan

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--no-download', action='store_true'); ap.add_argument('--resume', action='store_true'); a = ap.parse_args()
    run(download=not a.no_download, resume=a.resume)
