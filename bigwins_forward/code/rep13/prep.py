"""Blind replication of report 64 (rules v1.2), data preparation.
Builds wide arrays (dates x company-parts) for the two sources:
  eod : EODHD total-return source, rules I1-I8
  v2  : data_foundation v2 panel (price only), company parts per I4 / v1.1 A2 as quoted in I4
Output: out/wide_<src>.npz + out/cols_<src>.csv + out/dates_<src>.csv
Run: python3 -I prep.py eod|v2
"""
import sys, gzip, json, glob, os
import numpy as np, pandas as pd

BASE = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
DF = f'{BASE}/data_foundation/out'
OUT = f'{BASE}/bigwins_forward/out/rep13'
CUT = pd.Timestamp('2026-11-13')
START = pd.Timestamp('2014-06-01')   # v1.3 A2: the working file starts on 2 Jun 2014


def calendar():
    # v1.3 A1: a trading day is a day on which the vendor's AXJO.INDX series has a row (identical to the official ASX
    # calendar for the whole file; it includes 31 Oct-4 Nov 2016 and 29 May 2020, which the v2-panel calendar file lacks)
    t = pd.read_pickle(f'{DF}/eodhd/panel_tr.pkl', )
    d = t.loc[t.symbol == 'AXJO.INDX', 'date']
    return pd.DatetimeIndex(sorted(d[(d <= CUT) & (d >= START)]))


def etp_list():
    s = set()
    for line in open(f'{BASE}/bigwins_lab/data/etp_list.txt'):
        line = line.strip()
        if line:
            s.add(line.split()[-1])
    return s


def split_parts(df, key):
    """I4: within one code (key), a gap > 200 calendar days between consecutive rows starts a new company."""
    df = df.sort_values([key, 'date']).reset_index(drop=True)
    gap = df.groupby(key).date.diff().dt.days
    newp = (gap > 200).astype(int)
    df['part'] = newp.groupby(df[key]).cumsum()
    df['cid'] = df[key] + '#' + df['part'].astype(str)
    return df


def to_wide(df, cols, dates):
    out = {}
    cids = sorted(df.cid.unique())
    ci = {c: i for i, c in enumerate(cids)}
    di = {d: i for i, d in enumerate(dates)}
    r = df.date.map(di).values
    k = df.cid.map(ci).values
    ok = ~pd.isna(r)
    r = r[ok].astype(int); k = k[ok]
    for c in cols:
        a = np.full((len(dates), len(cids)), np.nan)
        a[r, k] = df[c].values[ok]
        out[c] = a
    return out, cids


def build_eod():
    dates = calendar()
    t = pd.read_pickle(f'{DF}/eodhd/panel_tr.pkl')
    # I12 index
    ix = t[t.symbol == 'AXJO.INDX'][['date', 'close']].set_index('date').close
    ix.to_pickle(f'{OUT}/axjo.pkl')
    # I1 securities
    typ = {}
    for f in sorted(glob.glob(f'{DF}/eodhd/raw/exchange-symbol-list/*.json.gz')):
        for r in json.load(gzip.open(f)):
            typ[r['Code'] + '.AU'] = r['Type']
    etp = etp_list()
    t['code'] = t.symbol.str.replace('.AU', '', regex=False)
    keep = t.symbol.map(typ).eq('Common Stock') & (t.code.str.len() == 3) & ~t.code.isin(etp) & t.symbol.str.endswith('.AU')
    t = t[keep]
    # I2 days
    t = t[t.date.isin(dates) & (t.date <= CUT) & (t.date >= START) & (t.close > 0)].copy()
    t = t[['code', 'date', 'high', 'low', 'close', 'volume', 'split', 'div']].sort_values(['code', 'date']).reset_index(drop=True)
    # I3 duplicate codes
    last_day = t.groupby('code').date.max()
    file_last = t.date.max()
    dup = {}
    cl = t.pivot(index='date', columns='code', values='close').reindex(dates)
    vo = t.pivot(index='date', columns='code', values='volume').reindex(dates)
    codes = sorted(cl.columns)
    lastclose_day = {c: last_day[c] for c in codes}
    pos = {d: i for i, d in enumerate(dates)}
    cl = cl[codes]; vo = vo[codes]
    CL = cl.values; cpos = {c: i for i, c in enumerate(codes)}
    LD = np.array([lastclose_day[c] for c in codes], dtype='datetime64[ns]')
    lastclose_day = {c: np.datetime64(lastclose_day[c], 'ns') for c in codes}
    for x in codes:
        lx = lastclose_day[x]
        if lx >= np.datetime64(file_last, 'ns'):
            continue
        ix_ = pos[pd.Timestamp(lx)]
        cx = cl[x].values
        rowx = cl.iloc[ix_]
        cand = [y for y in codes if y != x and lastclose_day[y] > lx and not np.isnan(rowx[y]) and abs(rowx[y] - cx[ix_]) < 1e-9]
        for y in sorted(cand):
            w0 = max(0, ix_ - 59)
            a = cl[x].values[w0:ix_ + 1]; b = cl[y].values[w0:ix_ + 1]
            va = vo[x].values[w0:ix_ + 1]; vb = vo[y].values[w0:ix_ + 1]
            both = ~np.isnan(a) & ~np.isnan(b)
            if both.sum() < 30:
                continue
            def agree(p, q):
                den = np.maximum(np.abs(p), np.abs(q))
                return np.all((np.abs(p - q) <= 1e-6 * np.where(den > 0, den, 1)))
            if agree(a[both], b[both]) and agree(va[both], vb[both]):
                dup[x] = y
                break
    pd.Series(dup, name='dup_of').to_csv(f'{OUT}/eod_I3_duplicates.csv')
    del cl, vo
    t = t[~t.code.isin(dup.keys())]
    # I4 parts
    t = split_parts(t, 'code')
    # I5 r, I6 P, I8 D
    g = t.groupby('cid')
    pc = g.close.shift()
    s = t.split.fillna(1.0)
    r = t.close * s / pc - 1
    first = pc.isna()
    r[first] = 0.0
    t['r'] = r
    G = (1 + t.r).groupby(t.cid).cumprod()
    lastc = g.close.transform('last'); lastG = G.groupby(t.cid).transform('last')
    t['P'] = G * lastc / lastG
    Pprev = t.groupby('cid').P.shift()
    D = ((t.close * s + t['div'].fillna(0)) / pc - 1 - r) * Pprev
    D[first] = 0.0
    D[D <= 1e-9 * t.P] = 0.0
    t['D'] = D.fillna(0.0)
    t['TV'] = t.close * t.volume
    t = t.rename(columns={'close': 'C', 'high': 'H', 'low': 'L'})
    w, cids = to_wide(t, ['C', 'H', 'L', 'TV', 'P', 'D'], dates)
    w['D'] = np.nan_to_num(w['D']); w['TV'] = np.nan_to_num(w['TV'])
    meta = t.groupby('cid').agg(code=('code', 'first'), first=('date', 'min'), last=('date', 'max')).reindex(cids)
    meta['code_at'] = meta.code
    np.savez_compressed(f'{OUT}/wide_eod.npz', **w)
    meta.to_csv(f'{OUT}/cols_eod.csv')
    pd.Series(dates).to_csv(f'{OUT}/dates_eod.csv', index=False)
    print('eod parts', len(cids), 'dups', len(dup))


def build_v2():
    dates = calendar()
    p = pd.read_pickle(f'{DF}/panel_v2_long.pkl')
    p = p[['eid', 'code', 'date', 'h', 'l', 'c', 'v', 'p', 'val']]
    p = p[p.date.isin(dates) & (p.c > 0)].copy()
    p = split_parts(p, 'eid')
    # code per (cid,date) -> wide code index
    codes = sorted(p.code.unique()); cmap = {c: i for i, c in enumerate(codes)}
    p['codei'] = p.code.map(cmap).astype(float)
    p = p.rename(columns={'c': 'C', 'h': 'H', 'l': 'L', 'val': 'TV', 'p': 'P'})
    w, cids = to_wide(p, ['C', 'H', 'L', 'TV', 'P', 'codei'], dates)
    w['TV'] = np.nan_to_num(w['TV']); w['D'] = np.zeros_like(w['C'])
    meta = p.sort_values('date').groupby('cid').agg(code=('code', 'last'), first=('date', 'min'), last=('date', 'max')).reindex(cids)
    np.savez(f'{OUT}/wide_v2.npz', **w)
    meta.to_csv(f'{OUT}/cols_v2.csv')
    pd.Series(codes).to_csv(f'{OUT}/codes_v2.csv', index=False)
    pd.Series(dates).to_csv(f'{OUT}/dates_v2.csv', index=False)
    print('v2 parts', len(cids))


if __name__ == '__main__':
    {'eod': build_eod, 'v2': build_v2}[sys.argv[1]]()
