"""Build an adjusted total-return panel from the EODHD raw store (no network).

Per symbol, from the latest successful raw payloads:
  close      raw, as traded (EODHD docs: OHLC are not adjusted)
  split      ratio on the split date, new shares per old ("2.000000/1.000000" -> 2.0)
  div        unadjustedValue (cash per share actually paid, in the share count of the ex-date)
  ret_pr     price return, split-neutral:  close_t * split_t / close_{t-1} - 1
  ret_tr     total return (dividend reinvested on the ex-date, no franking):
             (close_t * split_t + div_t) / close_{t-1} - 1
  tri        cumulative TR index (1.0 at the first row); pri likewise for ret_pr
  adj_close  EODHD's own split+dividend adjusted close (kept for cross-checks)
Rows dated outside the XASX calendar are dropped (listed in build_removed_rows.csv).
"""
import os, sys, json, gzip
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from client import load_manifest


def parse_split(s):
    try:
        a, b = str(s).split('/')
        a, b = float(a), float(b)
        return a / b if a > 0 and b > 0 else np.nan
    except Exception:
        return np.nan


def latest_files(store):
    m = load_manifest(store)
    m = m[(m.http == '200') & (m.file != '') & m.kind.isin(['eod', 'splits', 'div'])]
    m = m.groupby(['kind', 'symbol']).tail(1)
    return {(k, s): os.path.join(store, f) for k, s, f in zip(m.kind, m.symbol, m.file)}


def read_js(fp):
    return json.loads(gzip.decompress(open(fp, 'rb').read()))


def symbol_frame(eod, splits, divs):
    if not eod:
        return None
    d = pd.DataFrame(eod)
    if d.empty or 'close' not in d:
        return None
    d['date'] = pd.to_datetime(d['date'])
    d = d.sort_values('date').drop_duplicates('date', keep='last').reset_index(drop=True)
    sp = pd.Series(dtype=float)
    if splits:
        s = pd.DataFrame(splits)
        s['date'] = pd.to_datetime(s['date']); s['r'] = s['split'].map(parse_split)
        sp = s.groupby('date').r.prod()
    dv = pd.Series(dtype=float)
    if divs:
        v = pd.DataFrame(divs)
        v['date'] = pd.to_datetime(v['date'])
        col = 'unadjustedValue' if 'unadjustedValue' in v else 'value'
        v['amt'] = pd.to_numeric(v[col], errors='coerce')
        dv = v.groupby('date').amt.sum()
    d['split_listed'] = d.date.map(sp).fillna(1.0)
    d['div'] = d.date.map(dv).fillna(0.0)
    # events on non-trading dates: carry to the next trading row
    for ser, col, agg in ((sp, 'split_listed', np.prod), (dv, 'div', np.sum)):
        off = ser[~ser.index.isin(d.date)]
        for t, x in off.items():
            j = d.index[d.date > t]
            if len(j):
                d.loc[j[0], col] = d.loc[j[0], col] * x if col == 'split_listed' else d.loc[j[0], col] + x
    d['split'], d['split_check'] = reconcile_splits(d)
    c = d.close.where(d.close > 0)
    pc = c.shift(1)
    d['ret_pr'] = c * d.split / pc - 1
    d['ret_tr'] = (c * d.split + d['div']) / pc - 1
    d['tri'] = (1 + d.ret_tr.fillna(0)).cumprod()
    d['pri'] = (1 + d.ret_pr.fillna(0)).cumprod()
    d = d.rename(columns={'adjusted_close': 'adj_close'})
    return d[['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'split_listed', 'split', 'split_check', 'div', 'ret_pr', 'ret_tr', 'pri', 'tri']]


def reconcile_splits(d, before=3, after=5):
    """EODHD's AU `close` is usually raw at a split/consolidation date (the close jumps by 1/ratio), but
    for about a quarter of listed events there is no jump on the listed date: either the close was
    already back-adjusted or the event is dated a few sessions off. Apply each listed ratio on the
    session (within -before..+after) whose observed close jump best matches 1/ratio; when no session
    in the window matches, do not apply it (the price series is taken as already adjusted).
    Ratios within 10% of 1 (bonus/rights adjustments) are applied only when the listed-date jump is
    closer to 1/ratio than to 1."""
    split = np.ones(len(d)); chk = np.array([''] * len(d), dtype=object)
    c = d.close.where(d.close > 0).values
    jump = np.r_[np.nan, c[1:] / c[:-1]]
    for k in np.where(d.split_listed.values != 1)[0]:
        s = d.split_listed.values[k]
        ls = abs(np.log(s))
        if ls < np.log(1.10):
            j = jump[k]
            if np.isfinite(j) and abs(np.log(j * s)) < abs(np.log(j)):
                split[k] *= s; chk[k] = 'applied_small'
            else:
                chk[k] = 'skipped_small_no_jump'
            continue
        lo, hi = max(1, k - before), min(len(d) - 1, k + after)
        best, bk = np.inf, None
        for i in range(lo, hi + 1):
            if np.isfinite(jump[i]):
                e = abs(np.log(jump[i] * s))
                if e < best:
                    best, bk = e, i
        if bk is not None and best < 0.5 * ls:
            split[bk] *= s; chk[bk] = 'applied' if bk == k else f'applied_shifted_{bk - k:+d}'
        else:
            chk[k] = 'skipped_no_matching_jump'
    return split, chk


def main(store, log=print, sessions=None):
    files = latest_files(store)
    syms = sorted({s for k, s in files if k == 'eod'})
    if sessions is None:
        try:
            import calendar_fix as CF
            sessions = CF.xasx_sessions('1980-01-01', '2026-12-31')
        except Exception as e:
            log('no calendar:', e); sessions = None
    parts, removed, stats = [], [], []
    for s in syms:
        eod = read_js(files[('eod', s)])
        spl = read_js(files[('splits', s)]) if ('splits', s) in files else []
        dv = read_js(files[('div', s)]) if ('div', s) in files else []
        d = symbol_frame(eod, spl, dv)
        if d is None:
            stats.append(dict(symbol=s, rows=0)); continue
        if sessions is not None and s.endswith('.AU'):
            bad = ~d.date.isin(sessions)
            if bad.any():
                removed.append(d[bad].assign(symbol=s))
                d = d[~bad].copy()
                c = d.close.where(d.close > 0); pc = c.shift(1)
                d['ret_pr'] = c * d.split / pc - 1; d['ret_tr'] = (c * d.split + d['div']) / pc - 1
                d['tri'] = (1 + d.ret_tr.fillna(0)).cumprod(); d['pri'] = (1 + d.ret_pr.fillna(0)).cumprod()
        d.insert(0, 'symbol', s)
        parts.append(d)
        r = d.ret_pr
        stats.append(dict(symbol=s, rows=len(d), first=d.date.min(), last=d.date.max(), n_splits=int((d.split != 1).sum()),
                          n_divs=int((d['div'] > 0).sum()), zero_vol=int((d.volume == 0).sum()),
                          big_moves=int((np.abs(np.log1p(r)) > np.log(1.9)).sum())))
    pan = pd.concat(parts, ignore_index=True)
    out = os.path.join(store, 'panel_tr.pkl')
    pan.to_pickle(out)
    pd.DataFrame(stats).to_csv(os.path.join(store, 'symbol_stats.csv'), index=False)
    if removed:
        pd.concat(removed).to_csv(os.path.join(store, 'build_removed_rows.csv'), index=False)
    log(f'panel_tr: {len(pan)} rows, {pan.symbol.nunique()} symbols, {pan.date.min().date()}..{pan.date.max().date()}; '
        f'non-XASX rows dropped {sum(len(x) for x in removed)}')
    return pan
