# Big Wins rules v1.3 -- production data preparation (EODHD daily data only).
#   python3 -I bw13_prep.py <asof YYYY-MM-DD> [out.pkl]
# Implements v1.3 part A (inputs), B (signals).  No return after <asof> is read: the panel is cut at <asof> before
# anything else is computed, EXCEPT rule A7 (duplicate codes), which is applied to the file as downloaded (A7 says why).
# Output: a bundle the engine (engine_dd.py, frozen report-64 engine) can run, plus what the snapshot script needs.
# Nothing here reads the unlicensed price panel (panel_v2 / rs77 prices).  Two small static reference files are read:
#   the ETP exclusion list and the ASX listed-companies file (industry groups); the delisting-record list (to Apr 2020)
#   is used only by the back-test payout rule and is not needed for forward operation.
import sys, os, json, gzip, glob, csv, pickle, hashlib, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
DF = S + '/data_foundation/out'
FILE_START = '2014-06-01'      # A2: first day of the working file
NSTORE = 1000                  # ranks kept per month-end (engine uses 300; H101 tracking line uses 301-1000)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def axjo():
    f = sorted(glob.glob(DF + '/eodhd/raw/eod/AXJO.INDX__*.json.gz'))[-1]
    d = pd.DataFrame(json.load(gzip.open(f)))
    return pd.Series(d['close'].astype(float).values, index=pd.to_datetime(d['date'])).sort_index()


def sectors(path=S + '/bigwins_lab/data/ASXListedCompanies.csv'):
    sect = {}
    for r in csv.reader(open(path, errors='replace')):
        if len(r) >= 3 and len(r[1]) == 3: sect[r[1]] = r[2]
    return sect


def etf_tr():
    A = S + '/actuals/data/derived'
    nav = pd.read_csv(A + '/vanguard_nav_daily.csv', index_col=0, parse_dates=True)['VAS'].dropna()
    dist = pd.read_csv(A + '/dist_VAS.csv', parse_dates=['ex']).set_index('ex')['cash']
    r = nav.pct_change()
    for ex, c in dist.items():
        if ex in nav.index:
            i = nav.index.get_loc(ex)
            if i > 0: r.iloc[i] = (nav.iloc[i] + c) / nav.iloc[i - 1] - 1
    vas = (1 + r.fillna(0)).cumprod()
    a2 = pd.read_csv(A + '/betashares_total_return_index_daily.csv', index_col=0, parse_dates=True)['A200'].dropna()
    return vas, a2


def build(asof, download_end='2026-11-13', nstore=NSTORE, verbose=True, dup_rule='frozen'):
    """download_end: last complete day of the file as downloaded (A7 is applied on the file cut there);
    asof: decision day; everything after it is discarded before any signal is computed."""
    log = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    tr = pd.read_pickle(DF + '/eodhd/panel_tr.pkl')
    sym = pd.read_csv(DF + '/eodhd/symbols.csv')
    ok = sym[(sym.Type == 'Common Stock') & (sym.Code.str.len() == 3)]                       # A4
    etp = set(l.strip() for l in open(S + '/bigwins_lab/data/etp_list.txt'))
    oks = set(ok.api_symbol) - set(c + '.AU' for c in etp)
    tr = tr[tr.symbol.isin(oks) & (tr.date >= FILE_START) & (tr.date <= download_end)]
    tr = tr[tr.close > 0]                                                                    # A2
    C = tr.pivot(index='date', columns='symbol', values='close')
    VOL = tr.pivot(index='date', columns='symbol', values='volume').reindex_like(C)
    RP = tr.pivot(index='date', columns='symbol', values='ret_pr').reindex_like(C)
    RT = tr.pivot(index='date', columns='symbol', values='ret_tr').reindex_like(C)
    HI = tr.pivot(index='date', columns='symbol', values='high').reindex_like(C)
    LO = tr.pivot(index='date', columns='symbol', values='low').reindex_like(C)
    del tr
    # ---- A7 duplicate codes, on the file as downloaded
    Cv = C.values; Vv = VOL.values; n = Cv.shape[1]
    lastv0 = np.array([np.flatnonzero(~np.isnan(Cv[:, j]))[-1] if (~np.isnan(Cv[:, j])).any() else -1 for j in range(n)])
    drop = set(); duplog = []
    for j in range(n):
        l = lastv0[j]
        if l < 60 or l >= Cv.shape[0] - 1: continue
        a = Cv[l - 59:l + 1, j]; va = Vv[l - 59:l + 1, j]
        m = ~np.isnan(a)
        if m.sum() < 30: continue
        if True:                          # A7(a) as run in report 64
            cand = np.flatnonzero((np.abs(Cv[l] - Cv[l, j]) < 1e-9) & (lastv0 > l))
            for q in cand:
                b = Cv[l - 59:l + 1, q]; vb = Vv[l - 59:l + 1, q]
                mm = m & ~np.isnan(b)
                if mm.sum() >= 30 and np.allclose(a[mm], b[mm], rtol=1e-6) and np.allclose(va[mm], vb[mm], rtol=1e-6):
                    drop.add(j); duplog.append((C.columns[j][:-3], C.columns[q][:-3], str(C.index[l].date()))); break
        if dup_rule != 'frozen' and j not in drop:   # A7(b) forward rule: closes agree on >= 90% of >= 30 common days; >= 5 distinct closes
            Bw = Cv[l - 59:l + 1]; both = m[:, None] & ~np.isnan(Bw); nb = both.sum(0)
            ag = (both & (np.abs(Bw - a[:, None]) <= 1e-6 * np.abs(a[:, None]))).sum(0)
            cand = [q for q in np.flatnonzero((nb >= 30) & (ag >= 0.9 * nb) & (lastv0 > l)) if q != j and len(np.unique(a[both[:, q]])) >= 5]
            if cand:
                q = sorted(cand, key=lambda q: (-ag[q], q))[0]
                drop.add(j); duplog.append((C.columns[j][:-3], C.columns[q][:-3], str(C.index[l].date())))
    keep = [c for j, c in enumerate(C.columns) if j not in drop]
    C = C[keep]; VOL = VOL[keep]; RP = RP[keep]; RT = RT[keep]; HI = HI[keep]; LO = LO[keep]
    log('A7 duplicate codes dropped', len(drop))
    # ---- cut at the decision day (no later row is used from here on)
    asof = pd.Timestamp(asof)
    assert asof in C.index, 'asof must be a trading day of the file'
    C = C.loc[:asof]; VOL = VOL.loc[:asof]; RP = RP.loc[:asof]; RT = RT.loc[:asof]; HI = HI.loc[:asof]; LO = LO.loc[:asof]
    # ---- A3 adjusted close, A5 traded value, A6 dividend cash
    gr = (1 + RP.fillna(0)).cumprod().where(C.notna())
    lastc = C.ffill().iloc[-1]; lastg = gr.ffill().iloc[-1]
    P = gr * (lastc / lastg)
    TV = (C * VOL)
    dy = (RT - RP).where(lambda x: x.abs() > 1e-9)
    dcash = dy * P.ffill().shift(1)
    ren = lambda c: c[:-3] + '#E'
    for X in (P, TV, dcash, C, HI, LO): X.columns = [ren(c) for c in X.columns]
    # ---- A8 code re-use: a gap of more than 200 calendar days between consecutive closes starts a new company
    dn = P.index.values.astype('datetime64[D]').astype(int); new = {k: {} for k in 'P TV D C H L'.split()}; nsplit = 0
    srcs = dict(P=P, TV=TV, D=dcash, C=C, H=HI, L=LO)
    for c in list(P.columns):
        v = P[c].values; idx = np.flatnonzero(~np.isnan(v))
        if len(idx) < 2: continue
        cut = np.flatnonzero(np.diff(dn[idx]) > 200)
        if len(cut) == 0: continue
        nsplit += 1; bounds = [idx[0]] + [idx[q + 1] for q in cut] + [len(v)]
        for s_ in range(1, len(bounds) - 1):
            lo, hi = bounds[s_], bounds[s_ + 1]; nm = c + str(s_)
            for k, src_ in srcs.items():
                col = np.full(len(v), np.nan); col[lo:hi] = src_[c].values[lo:hi]; new[k][nm] = col
        lo = bounds[1]
        for src_ in srcs.values(): src_.iloc[lo:, src_.columns.get_loc(c)] = np.nan
    if new['P']:
        for k in srcs:
            srcs[k] = pd.concat([srcs[k], pd.DataFrame(new[k], index=P.index)], axis=1)
    P, TV, dcash, C, HI, LO = (srcs[k] for k in 'P TV D C H L'.split())
    log('A8 codes split at a >200-day gap', nsplit, 'new parts', len(new['P']))
    DIVD = {}
    ii, jj = np.nonzero(dcash.notna().values & (dcash.values > 0)); dv = dcash.values
    for i, j in zip(ii, jj): DIVD.setdefault(int(i), []).append((int(j), float(dv[i, j])))
    # ---- index and comparator
    xjo = axjo().reindex(P.index).ffill()
    vas, a2 = etf_tr()
    vas = vas.reindex(P.index).ffill(); a2 = a2.reindex(P.index).ffill()
    t0 = a2.first_valid_index()
    xtr = vas.copy()
    if t0 is not None: xtr.loc[t0:] = a2.loc[t0:] / a2.loc[t0] * vas.loc[t0]
    codes_last = {c: c.split('#')[0] for c in P.columns}
    dates = P.index; cols = list(P.columns); cix = {e: i for i, e in enumerate(cols)}
    Pv = P.values.astype(np.float64); Pf = P.ffill().values.astype(np.float64)
    has = ~np.isnan(Pv)
    lastv = np.array([(np.flatnonzero(has[:, j])[-1] if has[:, j].any() else -1) for j in range(Pv.shape[1])])
    firstv = np.array([(np.flatnonzero(has[:, j])[0] if has[:, j].any() else 10**9) for j in range(Pv.shape[1])])
    ym = pd.Series(np.arange(len(dates)), index=dates).groupby([dates.year, dates.month]).last()
    ME = ym.values.astype(int)
    Pf10 = P.ffill(limit=10); Pm_v = Pf10.iloc[ME].values; P10v = Pf10.values
    lrv = np.log(P).diff().values
    sect = sectors(); UNK = {'unknown', 'Not Applic', 'Class Pend', ''}
    def grp(e):
        s = sect.get(codes_last[e], 'unknown')
        return None if (s is None or s.strip() in UNK) else s
    sector_all = np.array([grp(e) for e in cols], dtype=object)
    V0 = TV.fillna(0.0).values.astype(np.float64)
    tabs = {}
    for k, i in enumerate(ME):
        t = dates[i]
        if t < pd.Timestamp('2015-11-01') or i < 260: continue
        w0 = i - 251
        traded = has[w0:i + 1].sum(0); medval = np.median(V0[w0:i + 1], axis=0)
        el = np.flatnonzero(traded >= 200)
        order = el[np.argsort(-medval[el], kind='stable')]
        uni = order[:nstore]
        def pm(lag): return Pm_v[k - lag][uni] if k - lag >= 0 else np.full(len(uni), np.nan)
        d = dict(col=uni.astype(int), vrank=np.arange(1, len(uni) + 1), medval=medval[uni], price=P10v[i][uni])
        with np.errstate(all='ignore'):
            d['M1'] = pm(1) / pm(12) - 1
            d['M2'] = pm(0) / pm(6) - 1
            d['M3'] = P10v[i][uni] / np.nanmax(np.where(has[w0:i + 1][:, uni], Pv[w0:i + 1][:, uni], -np.inf), axis=0)
            lr = lrv[w0:i + 1][:, uni]
            vol = np.where((~np.isnan(lr)).sum(0) >= 200, np.nanstd(lr, axis=0, ddof=1), np.nan)
            d['vol'] = vol; d['M5'] = -vol
        d['sector'] = sector_all[uni]
        d['rawclose'] = C.values[i][uni]            # as-quoted close ON the day (NaN if no close that day)
        tabs[k] = d
    # ---- delisting records (back-test payout rule C1 only)
    dl = pd.read_pickle(S + '/company_study/data/delist.pkl')
    bycode = {c: g.sort_values('date') for c, g in dl.groupby('code')}
    fail = np.zeros(len(cols), bool); take = np.zeros(len(cols), bool)
    for j, e in enumerate(cols):
        if lastv[j] < 0 or lastv[j] >= len(dates) - 1: continue
        g = bycode.get(codes_last[e])
        if g is None: continue
        lv = dates[lastv[j]]
        c = g[(g.date >= lv - pd.Timedelta(days=30)) & (g.date <= lv + pd.Timedelta(days=1500))]
        if c.empty: continue
        fail[j] = bool(c.iloc[0].failkw); take[j] = bool(c.iloc[0].takekw)
    nan1 = np.full(len(ME), np.nan)
    D = dict(dates=dates, cols=cols, cix=cix, Pv=Pv, Pf=Pf, lastv=lastv, firstv=firstv, ME=ME, M4full=None, xjo=xjo.values.astype(float),
             xtr=xtr.values.astype(float), mkt_up10=nan1, ret12=nan1, breadth=nan1, tabs=tabs, fail=fail, take=take, dv=None,
             sector_all=sector_all, DIVD=DIVD, src='eod', V0=V0, Craw=C.values.astype(np.float64), Hraw=HI.values.astype(np.float64),
             Lraw=LO.values.astype(np.float64), duplog=duplog, asof=str(asof.date()), download_end=download_end)
    log('bundle', Pv.shape, 'first/last day', dates[0].date(), dates[-1].date(), 'month-ends with a table', len(tabs), 'fail', int(fail.sum()), 'take', int(take.sum()))
    return D


if __name__ == '__main__':
    asof = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else S + f'/bigwins_forward/out/bundle13_{asof}.pkl'
    D = build(asof)
    pickle.dump(D, open(out, 'wb'), protocol=4)
    print('written', out)
