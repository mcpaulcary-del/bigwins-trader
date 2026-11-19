# INFORMATION ONLY - new ASX listings tracker for the Big Wins paper research.
# Makes NO trading decision, reads no paper state, writes nothing any paper/trading job reads, changes no frozen rule or code.
# Data: EODHD only (private, non-commercial use); NO automated access to the ASX website.  The proxy injects the EODHD key
# (same Client as fwd_download.py / est_snapshot.py).
#
#   python3 -I newlist_tracker.py                 daily run (idempotent; re-running the same day costs ~0 credits)
#   python3 -I newlist_tracker.py --backfill      offline baseline 2014+ from the local EODHD raw stores (0 credits)
#   options: --date YYYY-MM-DD  --min-left 25000  --per-min 150 (hard cap 150)
#
# Daily run:
#   1. EODHD credit check (aborts if the run would leave < --min-left credits).
#   2. AU exchange symbol list, active + delisted (2 credits), stored as a dated snapshot; diff vs the previous snapshot
#      (first run: vs bigwins_forward/data/eodhd/symbols.csv of 2026-11-16) -> new codes, codes gone from the active list, name changes.
#   3. New codes: end-of-day history fetched (1 credit each) -> first EODHD trading row; classified
#        new_listing     3-letter Common Stock whose EODHD history starts recently and with no matching predecessor
#        likely_rename   code change / relisting: same ISIN or similar name (token Jaccard >= 0.5) as a delisted / vanished code,
#                        or EODHD history that starts long before the code appeared (history carried over)
#        old_history     EODHD history starts > 30 days before the code first appeared in the list (vendor addition or code change)
#        (baseline only: eodhd_late_start / data_stub - see xcheck(); price continuity alone is recorded in `evidence` but not excluded)
#        etf_fund / other_security (rights, deferred settlement, notes, preferred, bonds, non-3-letter codes) - recorded, not tracked
#        pending_first_trade  in the list but no EODHD trading row yet (re-checked each run)
#   4. Every tracked new listing (first trade within the last 400 days, not delisted): full EOD history re-fetched (1 credit),
#      price path stored; fundamentals fetched ONCE per listing (10 credits) = the "at-listing" snapshot (sector, industry,
#      description, IPODate, shares, latest revenue / net income / cash / debt).  Bootstrapped listings get their snapshot
#      on the first run, so it is "at first observation", not strictly at listing (fund_days_after_listing says how late).
#   5. Outputs (data/newlist/): newlist_tracker.csv (one row per new listing, latest stats), newlist_other.csv (renames, ETFs,
#      other securities), registry.csv, paths.csv.gz, daily/px_<date>.csv.gz, snapshots/, fund.jsonl, run_log.csv;
#      and paper/NEWLIST.md in the forward record.
# Returns use EODHD adjusted_close (split- and dividend-adjusted) from the FIRST CLOSE (EODHD has no offer price).
import os, sys, re, json, gzip, time, argparse, datetime as dt
import numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
sys.path.insert(0, S + '/data_foundation/code/eodhd')
from client import Client, COST, load_manifest
import build_tr
OLD = S + '/data_foundation/out/eodhd'                 # research store (read-only)
FWD = S + '/bigwins_forward/data/eodhd'                # forward store (read-only here)
OUT = S + '/bigwins_forward/data/newlist'
PAPER = S + '/onedrive/research2/68_forward_record/paper'
MD = PAPER + '/NEWLIST.md'
COST['fundamentals'] = 10
TRACK_DAYS = 400
FUND_FILTER = ('General,Highlights,SharesStats,Financials::Balance_Sheet::yearly,Financials::Balance_Sheet::quarterly,'
               'Financials::Income_Statement::yearly,Financials::Income_Statement::quarterly')
GENERIC = set('LIMITED LTD ORDINARY ORD FPO FULLY PAID UNITS UNIT STAPLED SECURITIES SEC GROUP GRP. GRP HOLDINGS HLDGS HOLDING '
              'CORPORATION CORP CO NL THE AND OF TRUST FUND DEFERRED SETTLEMENT DEF SET CDI FOREIGN EXEMPT NEW PTY INC PLC'.split())
OTHER_NAME = re.compile(r'^(RIGHTS|ORDINARY FULLY PAID DEFERRED|OPTION|.*DEFERRED SETTLEMENT)', re.I)


# ------------------------------------------------------------------ helpers
def today_syd():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo('Australia/Sydney')).date().isoformat()
    except Exception:
        return dt.date.today().isoformat()

def name_tokens(s):
    if not isinstance(s, str): return set()
    return {x for x in re.findall(r'[A-Z0-9]+', s.upper()) if x not in GENERIC and len(x) > 1}

def name_sim(a, b):
    ta, tb = name_tokens(a), name_tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0

def base_code(c): return str(c).split('_old')[0]

def classify_type(typ, code, name):
    if typ in ('ETF', 'FUND') or (isinstance(name, str) and re.search(r'\bETF\b|\bFUND\b|ETMF|\bTRUST\b', name.upper())): return 'etf_fund'
    if typ != 'Common Stock' or len(str(code)) != 3 or (isinstance(name, str) and OTHER_NAME.match(name)): return 'other_security'
    return None

def latest_files(store):
    m = load_manifest(store)
    m = m[(m.http == '200') & (m.file != '') & m.kind.isin(['eod', 'splits', 'div'])].groupby(['kind', 'symbol']).tail(1)
    return {(k, s): os.path.join(store, f) for k, s, f in zip(m.kind, m.symbol, m.file)}

def local_files():
    f = latest_files(OLD); f.update(latest_files(FWD)); return f      # forward store (newer) wins

def symbols_local():
    u = pd.concat([pd.read_csv(FWD + '/symbols.csv'), pd.read_csv(OLD + '/symbols.csv')]).drop_duplicates('api_symbol', keep='first')
    return u

def stats_from_path(p, asof=None):
    """p: DataFrame date, open, close, adj_close, volume (one code, sorted). Returns dict of running stats from the first close."""
    p = p[p.close > 0].sort_values('date').reset_index(drop=True)
    if p.empty or not (p.volume > 0).any(): return {}
    p = p.loc[(p.volume > 0).idxmax():]                     # first trade = first row with volume
    a = p.adj_close.where(p.adj_close > 0, p.close).astype(float).values
    f = p.iloc[0]; d0 = pd.Timestamp(f.date)
    r = dict(listing_date=d0.date().isoformat(), first_open=float(f.open) if pd.notna(f.open) else np.nan, first_close=float(f.close),
             first_volume=float(f.volume), first_value=float(f.close * f.volume), last_date=pd.Timestamp(p.date.iloc[-1]).date().isoformat(),
             last_close=float(p.close.iloc[-1]), n_days=len(p), ret_since_first=a[-1] / a[0] - 1,
             max_gain=a.max() / a[0] - 1, max_drawdown=float((a / np.maximum.accumulate(a)).min() - 1),
             traded_value_total=float((p.close * p.volume).sum()), med_value_20d=float((p.close * p.volume).tail(20).median()))
    dts = pd.to_datetime(p.date).values
    asof = pd.Timestamp(asof) if asof else pd.Timestamp(dts[-1])
    for lab, days in (('r1m', 30), ('r3m', 91), ('r6m', 182), ('r12m', 365)):
        t = d0 + pd.Timedelta(days=days)
        if asof < t and pd.Timestamp(dts[-1]) < t: r[lab] = np.nan; continue
        j = np.searchsorted(dts, np.datetime64(t), side='right') - 1
        r[lab] = a[j] / a[0] - 1
    return r


# ------------------------------------------------------------------ baseline (offline)
def backfill(log=print, start='2014-01-01'):
    """Survivorship-aware history of ASX new listings since `start` from the local EODHD raw stores (no network)."""
    t0 = time.time()
    files = local_files(); u = symbols_local()
    st = pd.read_csv(OLD + '/symbol_stats.csv').set_index('symbol')
    cs = u[u.Type == 'Common Stock'].copy()
    cs['first'] = cs.api_symbol.map(st['first']); cs['last'] = cs.api_symbol.map(st['last'])
    cache = {}
    def frame(sym):
        if sym not in cache:
            rd = lambda k: build_tr.read_js(files[(k, sym)]) if (k, sym) in files else []
            cache[sym] = build_tr.symbol_frame(rd('eod'), rd('splits'), rd('div')) if ('eod', sym) in files else None
        return cache[sym]
    for s in cs.api_symbol:                                   # first/last from the files for symbols missing in symbol_stats
        if pd.isna(cs.loc[cs.api_symbol == s, 'first']).all() and ('eod', s) in files:
            d = frame(s)
            if d is not None and len(d): cs.loc[cs.api_symbol == s, ['first', 'last']] = [str(d.date.iloc[0].date()), str(d.date.iloc[-1].date())]
    cs = cs.dropna(subset=['first'])
    data_end = cs['last'].max()
    ax = frame('AXJO.INDX'); ax = ax.set_index('date').close
    cand = cs[(cs['first'] >= start) & (cs.Code.map(base_code).str.len() == 3) & ~cs.Name.fillna('').str.match(OTHER_NAME)]
    log(f'backfill: {len(cand)} Common Stock 3-letter codes with first EODHD row >= {start}; data end {data_end}')
    cs['fd'] = pd.to_datetime(cs['first']); cs['ld'] = pd.to_datetime(cs['last'])
    rows = []
    for _, c in cand.iterrows():
        F = pd.Timestamp(c['first']); d = frame(c.api_symbol)
        if d is None or d.empty: continue
        d = d[d.close > 0].reset_index(drop=True)
        if d.empty or not (d.volume > 0).any(): continue
        d = d.loc[(d.volume > 0).idxmax():].reset_index(drop=True)   # first EODHD row with a positive close AND volume = first trade
        F = d.date.iloc[0]
        if F < pd.Timestamp(start): continue
        # predecessors: codes whose EODHD history ends in [F-14d, F+3d] and started > 30 days before F, or any earlier code with same ISIN
        pr = cs[(cs.api_symbol != c.api_symbol) & (cs.fd < F - pd.Timedelta(days=30)) &
                (((cs.ld >= F - pd.Timedelta(days=14)) & (cs.ld <= F + pd.Timedelta(days=3))) |
                 ((cs.Isin == c.Isin) & cs.Isin.notna() & (cs.ld < F + pd.Timedelta(days=3))) |
                 ((cs.Code.map(base_code) == base_code(c.Code)) & (cs.ld < F)))]
        cls, pred, ev = 'new_listing', '', ''
        best = []
        for _, q in pr.iterrows():
            ns = name_sim(c.Name, q.Name); isin = isinstance(c.Isin, str) and c.Isin == q.Isin
            near = (q.ld >= F - pd.Timedelta(days=14)) and (q.ld <= F + pd.Timedelta(days=3))
            px = False
            if near:
                qd = frame(q.api_symbol)
                if qd is not None and len(qd) and qd.close.iloc[-1] > 0:
                    o = d.open.iloc[0] if d.open.iloc[0] > 0 else d.close.iloc[0]
                    px = (abs(o / qd.close.iloc[-1] - 1) <= 0.05 or abs(d.close.iloc[0] / qd.close.iloc[-1] - 1) <= 0.05) and \
                         (F - qd.date.iloc[-1]).days <= 5
            if isin or ns >= 0.5: best.append((2, ns, q.Code, f'isin={isin} name_sim={ns:.2f} price_cont={px}'))
            elif px and near: best.append((1, ns, q.Code, f'price_cont only (name_sim={ns:.2f})'))
        if best:
            best.sort(reverse=True); b = best[0]
            if b[0] == 2: cls, pred, ev = 'likely_rename', b[2], b[3]
            else: pred, ev = b[2], 'kept: ' + b[3]           # price continuity alone is too weak (many IPOs open at A$0.20)
        if cls == 'new_listing' and c.delisted == 1 and (d.volume > 0).sum() < 5: cls, ev = 'data_stub', 'delisted, < 5 EODHD rows with volume'
        end = F + pd.Timedelta(days=365)
        w = d[d.date <= end]; pri = w.pri.values / w.pri.values[0]
        complete = (pd.Timestamp(data_end) >= end) or (c.delisted == 1 and d.date.iloc[-1] < end)
        delisted_12m = bool(c.delisted == 1 and d.date.iloc[-1] < end)
        obs_end = w.date.iloc[-1]
        def at(days):
            t = F + pd.Timedelta(days=days)
            if pd.Timestamp(data_end) < t and not delisted_12m: return np.nan
            x = w[w.date <= t]; return x.pri.iloc[-1] / w.pri.iloc[0] - 1
        a0 = ax[ax.index <= F]; a1 = ax[ax.index <= obs_end]
        rows.append(dict(code=c.Code, name=c.Name, isin=c.Isin, delisted=int(c.delisted), first_date=F.date().isoformat(),
                         last_date=d.date.iloc[-1].date().isoformat(), year=F.year, cls=cls, predecessor=pred, evidence=ev,
                         first_open=d.open.iloc[0], first_close=d.close.iloc[0], first_volume=d.volume.iloc[0],
                         first_value=d.close.iloc[0] * d.volume.iloc[0], complete_12m=bool(complete), delisted_within_12m=delisted_12m,
                         r1m=at(30), r3m=at(91), r6m=at(182), r12m=(pri[-1] - 1) if complete else np.nan,
                         min_12m=pri.min() - 1, max_12m=pri.max() - 1,
                         halved_12m=bool(pri.min() <= 0.5), doubled_12m=bool(pri.max() >= 2.0),
                         axjo_12m=(a1.iloc[-1] / a0.iloc[-1] - 1) if (complete and len(a0) and len(a1)) else np.nan))
    b = pd.DataFrame(rows)
    b['excess_12m'] = b.r12m - b.axjo_12m
    b = xcheck(b)
    os.makedirs(OUT, exist_ok=True)
    b.to_csv(OUT + '/baseline_listings.csv.gz', index=False, float_format='%.6g', compression={'method': 'gzip', 'mtime': 0})
    g = b[b.cls_final == 'new_listing']
    def summ(x, lab):
        c12 = x[x.complete_12m]
        return dict(year=lab, n_new_listings=len(x), n_excluded=int(((b.cls_final != 'new_listing') & ((b.year == lab) if lab != 'all' else (b.year <= 2025))).sum()),
                    n_complete_12m=len(c12), still_listed_now=int((x.delisted == 0).sum()), delisted_within_12m=int(c12.delisted_within_12m.sum()),
                    pct_halved_12m=round(100 * c12.halved_12m.mean(), 1) if len(c12) else np.nan,
                    pct_doubled_12m=round(100 * c12.doubled_12m.mean(), 1) if len(c12) else np.nan,
                    pct_down50_at_12m=round(100 * (c12.r12m <= -0.5).mean(), 1) if len(c12) else np.nan,
                    pct_up100_at_12m=round(100 * (c12.r12m >= 1.0).mean(), 1) if len(c12) else np.nan,
                    median_r12m=round(100 * c12.r12m.median(), 1) if len(c12) else np.nan,
                    median_axjo_12m=round(100 * c12.axjo_12m.median(), 1) if len(c12) else np.nan,
                    median_excess_12m=round(100 * c12.excess_12m.median(), 1) if len(c12) else np.nan,
                    pct_beat_axjo_12m=round(100 * (c12.excess_12m > 0).mean(), 1) if len(c12) else np.nan)
    tab = pd.DataFrame([summ(g[g.year == y], y) for y in sorted(g.year.unique())] + [summ(g[g.year <= 2025], 'all')])
    tab.loc[tab.year == 'all', 'year'] = '2014-2025'
    tab.to_csv(OUT + '/baseline_by_year.csv', index=False)
    log(tab.to_string(index=False))
    log(f'backfill done in {time.time() - t0:.0f}s: {len(b)} candidates; EODHD-only classes {b.cls.value_counts().to_dict()}; '
        f'after cross-check {b.cls_final.value_counts().to_dict()}')
    return b, tab


XC = S + '/data_foundation/out'
def xcheck(b, tol=20):
    """Cross-check against the ALREADY-HELD local research price history (data_foundation entity_map_v2 / code_history_v2, 1997 to
    2024-05-31; no new data access).  EODHD often starts a delisted company's history late (e.g. AHR from 2017 although listed 2007),
    which would make an old company look like a new listing.  For first dates <= 2024-05-10:
      eodhd_late_start  the same code traded in the research history >= tol days before the EODHD first date, in a run reaching F-200d
      likely_rename     the research history links the code's segment starting near F to an earlier code (code change)
      confirmed / unconfirmed  a research segment of the code starts within tol days of F / no such segment
    Later first dates keep the EODHD-only class (xcheck = 'after research history')."""
    e = pd.read_csv(XC + '/entity_map_v2.csv'); h = pd.read_csv(XC + '/code_history_v2.csv')
    e['f'] = pd.to_datetime(e['first']); e['l'] = pd.to_datetime(e['last'])
    linked = set(h.loc[h.from_code.notna() & h.link_confidence.isin(['high', 'medium']), 'eid'])
    eg = {k: v for k, v in e.groupby('code')}
    xc, fin = [], []
    for r in b.itertuples():
        F = pd.Timestamp(r.first_date); x = 'after research history'
        if F <= pd.Timestamp('2024-05-10'):
            g = eg.get(base_code(r.code))
            if g is None: x = 'unconfirmed'
            else:
                pre = g[(g.f <= F - pd.Timedelta(days=tol)) & (g.l >= F - pd.Timedelta(days=200))]
                near = g[(g.f - F).abs() <= pd.Timedelta(days=tol)]
                if len(pre): x = 'eodhd_late_start'
                elif len(near):
                    n = near.iloc[0]
                    x = 'likely_rename' if (n.eid_v2 != n.orig_segment or n.eid_v2 in linked) else 'confirmed'
                else: x = 'unconfirmed'
        xc.append(x)
        fin.append(r.cls if r.cls != 'new_listing' else ('new_listing' if x in ('confirmed', 'unconfirmed', 'after research history') else x))
    b['xcheck'] = xc; b['cls_final'] = fin
    return b


# ------------------------------------------------------------------ daily run
class Run:
    def __init__(self, date, min_left, per_min, log=print):
        self.date, self.min_left, self.log = date, min_left, log
        os.makedirs(OUT + '/snapshots', exist_ok=True); os.makedirs(OUT + '/daily', exist_ok=True)
        self.cli = Client(OUT + '/_client', per_min=min(per_min, 150), daily_budget=3000, log=log)

    def credits_left(self):
        u = self.cli.user() or {}
        return int(u.get('dailyRateLimit', 0)) + int(u.get('extraLimit', 0) or 0) - int(u.get('apiRequests', 0))

    def guard(self, need):
        left = self.credits_left()
        if left - need < self.min_left:
            raise SystemExit(f'ABORT: {left} credits left today; this step needs ~{need}; would leave < {self.min_left}')
        return left

    def snapshot(self):
        fp = f'{OUT}/snapshots/symbols_{self.date}.csv.gz'
        if os.path.exists(fp): return pd.read_csv(fp), False
        parts = []
        for dl in (0, 1):
            code, js = self.cli.get('exchange-symbol-list/AU', {'delisted': dl}, 'exchange-symbol-list', f'AU_delisted{dl}', save=False)
            if code != 200 or not js: raise RuntimeError(f'symbol list delisted={dl}: HTTP {code}')
            d = pd.DataFrame(js); d['delisted'] = dl; parts.append(d)
        u = pd.concat(parts, ignore_index=True); u['api_symbol'] = u.Code.astype(str) + '.AU'
        u = u.sort_values(['api_symbol', 'delisted']).drop_duplicates('api_symbol', keep='first')
        u[['Code', 'Name', 'Type', 'Isin', 'delisted', 'api_symbol']].to_csv(fp + '.tmp', index=False, compression={'method': 'gzip', 'mtime': 0})
        os.replace(fp + '.tmp', fp)
        return pd.read_csv(fp), True

    def previous(self):
        snaps = sorted(f for f in os.listdir(OUT + '/snapshots') if f.startswith('symbols_') and f[8:18] < self.date)
        if snaps: return pd.read_csv(f'{OUT}/snapshots/{snaps[-1]}'), snaps[-1][8:18]
        return pd.read_csv(FWD + '/symbols.csv'), '2026-11-16 (seed: forward-store symbols.csv)'

    def eod(self, code, since=None):
        params = {'from': since} if since else {}
        h, js = self.cli.get(f'eod/{code}.AU', params, 'eod', code, save=False)
        if h != 200 or not isinstance(js, list): return None
        d = pd.DataFrame(js)
        if d.empty: return d
        d = d.rename(columns={'adjusted_close': 'adj_close'})
        d['code'] = code
        return d[['code', 'date', 'open', 'close', 'adj_close', 'volume']]

    def fundamentals(self, code):
        h, js = self.cli.get(f'fundamentals/{code}.AU', {'filter': FUND_FILTER}, 'fundamentals', code, save=False)
        if h != 200 or not isinstance(js, dict): return None
        g = js.get('General') or {}; hl = js.get('Highlights') or {}; ss = js.get('SharesStats') or {}
        def last(k, fields):
            x = js.get(k) or {}
            if not isinstance(x, dict) or not x: return {}
            dte = max(x); return dict(period=dte, **{f: x[dte].get(f) for f in fields})
        bs = last('Financials::Balance_Sheet::quarterly', ['cash', 'cashAndShortTermInvestments', 'shortLongTermDebtTotal', 'totalAssets', 'totalStockholderEquity', 'commonStockSharesOutstanding']) or \
             last('Financials::Balance_Sheet::yearly', ['cash', 'cashAndShortTermInvestments', 'shortLongTermDebtTotal', 'totalAssets', 'totalStockholderEquity', 'commonStockSharesOutstanding'])
        isy = last('Financials::Income_Statement::yearly', ['totalRevenue', 'netIncome', 'ebit'])
        f = lambda v: float(v) if v not in (None, '', 'None') else None
        return dict(code=code, fetched=self.date, name=g.get('Name'), type=g.get('Type'), isin=g.get('ISIN'), sector=g.get('Sector'),
                    industry=g.get('Industry'), gic_sector=g.get('GicSector'), ipo_date=g.get('IPODate'),
                    description=(g.get('Description') or '')[:400], shares_out=f(ss.get('SharesOutstanding')),
                    mcap_vendor=f(hl.get('MarketCapitalization')), revenue_ttm=f(hl.get('RevenueTTM')),
                    bs_period=bs.get('period'), cash=f(bs.get('cash') or bs.get('cashAndShortTermInvestments')), debt=f(bs.get('shortLongTermDebtTotal')),
                    total_assets=f(bs.get('totalAssets')), equity=f(bs.get('totalStockholderEquity')), bs_shares=f(bs.get('commonStockSharesOutstanding')),
                    is_period=isy.get('period'), revenue_fy=f(isy.get('totalRevenue')), net_income_fy=f(isy.get('netIncome')))

    # -------------------------------------------------------------- main
    def run(self):
        t0 = time.time(); log = self.log
        left0 = self.guard(200)
        snap, fetched = self.snapshot(); prev, prev_tag = self.previous()
        new_codes = sorted(set(snap.api_symbol) - set(prev.api_symbol))
        pa = set(prev[prev.delisted == 0].api_symbol); na = set(snap[snap.delisted == 0].api_symbol)
        gone = sorted(pa - na)
        nm = snap.merge(prev[['api_symbol', 'Name']], on='api_symbol', suffixes=('', '_prev'))
        renamed_same_code = nm[(nm.Name != nm.Name_prev) & nm.Name_prev.notna()][['Code', 'Name_prev', 'Name']]
        log(f'{self.date}: snapshot {"fetched" if fetched else "reused"} ({len(snap)} codes; {len(na)} active); vs {prev_tag}: '
            f'{len(new_codes)} new codes, {len(gone)} left the active list, {len(renamed_same_code)} name changes')

        regp = OUT + '/registry.csv'
        if os.path.exists(regp): reg = pd.read_csv(regp, dtype={'code': str})
        else: reg = self.bootstrap(snap)
        paths = pd.read_csv(OUT + '/paths.csv.gz') if os.path.exists(OUT + '/paths.csv.gz') else pd.DataFrame(columns=['code', 'date', 'open', 'close', 'adj_close', 'volume'])
        snap_i = snap.set_index('Code')

        # new codes (+ pending ones from earlier runs)
        todo = [c[:-3] for c in new_codes if c[:-3] not in set(reg.code)] + reg.loc[reg.cls == 'pending_first_trade', 'code'].tolist()
        self.guard(len(todo) + 10)
        dead = snap[snap.delisted == 1]
        for code in todo:
            s = snap_i.loc[code] if code in snap_i.index else None
            name, typ, isin = (s.Name, s.Type, s.Isin) if s is not None else ('', '', '')
            cls = classify_type(typ, code, name); first = ''; pred = ev = ''
            if cls is None:
                d = self.eod(code)
                if d is None or d.empty: cls = 'pending_first_trade'
                else:
                    first = str(d.date.iloc[0])[:10]
                    pdate = prev_tag[:10]
                    pr = [(name_sim(name, q.Name), q.Code, isinstance(isin, str) and isin == q.Isin) for q in
                          pd.concat([dead, snap[snap.api_symbol.isin(gone)]]).itertuples() if q.Code != code]
                    pr = [x for x in pr if x[2] or x[0] >= 0.5]
                    if pr:
                        x = max(pr, key=lambda x: (x[2], x[0])); cls, pred, ev = 'likely_rename', x[1], f'isin={x[2]} name_sim={x[0]:.2f}'
                    elif first < (pd.Timestamp(pdate) - pd.Timedelta(days=30)).date().isoformat():
                        cls, ev = 'old_history', f'EODHD history starts {first}, long before the code appeared (carried-over history)'
                    else:
                        cls = 'new_listing'
                        paths = pd.concat([paths[paths.code != code], d], ignore_index=True)
            row = dict(code=code, name=name, type=typ, isin=isin, cls=cls, first_date=first, detected_on=self.date, source=f'diff vs {prev_tag[:10]}',
                       predecessor=pred, evidence=ev, status='active')
            reg = pd.concat([reg[reg.code != code], pd.DataFrame([row])], ignore_index=True)
            log(f'  new code {code} ({typ}; {name}): {cls} {first} {ev}')

        # delisting status
        dl = set(snap[snap.delisted == 1].Code); act = set(snap[snap.delisted == 0].Code)
        reg.loc[reg.code.isin(dl - act), 'status'] = 'delisted'
        reg.loc[reg.code.isin(act), 'status'] = 'active'

        # tracked new listings: refresh full EOD path (1 credit each), fundamentals once (10 credits)
        lim = (pd.Timestamp(self.date) - pd.Timedelta(days=TRACK_DAYS)).date().isoformat()
        tr = reg[(reg.cls == 'new_listing') & (reg.status == 'active') & (reg.first_date.astype(str) >= lim)].code.tolist()
        funds = self.fund_index()
        nf = [c for c in reg[reg.cls == 'new_listing'].code if c not in funds]
        self.guard(len(tr) + 10 * len(nf) + 5)
        man = load_manifest(self.cli.store)
        done_today = set(man[(man.kind == 'eod') & (man.http == '200') & man.utc.str[:10].isin([self.date, dt.datetime.now(dt.timezone.utc).date().isoformat()])].symbol) if fetched is False else set()
        n_ref = 0
        for code in tr:
            if code in done_today and (paths.code == code).any(): continue
            fd = reg.loc[reg.code == code, 'first_date'].iloc[0]
            d = self.eod(code, str(fd)[:10] if isinstance(fd, str) and fd else None)
            if d is None or d.empty: continue
            paths = pd.concat([paths[paths.code != code], d], ignore_index=True); n_ref += 1
        for code in nf:
            r = self.fundamentals(code)
            if r is None: continue
            with open(OUT + '/fund.jsonl', 'a') as f: f.write(json.dumps(r, sort_keys=True) + '\n')
            funds[code] = r
        paths['date'] = paths.date.astype(str).str[:10]
        paths = paths.sort_values(['code', 'date']).drop_duplicates(['code', 'date'], keep='last')
        paths.to_csv(OUT + '/paths.csv.gz.tmp', index=False, float_format='%.6g', compression={'method': 'gzip', 'mtime': 0}); os.replace(OUT + '/paths.csv.gz.tmp', OUT + '/paths.csv.gz')
        reg.to_csv(regp + '.tmp', index=False); os.replace(regp + '.tmp', regp)

        # tables
        rows = []
        for _, r in reg[reg.cls == 'new_listing'].iterrows():
            p = paths[paths.code == r.code]
            st = stats_from_path(p, self.date if r.status == 'active' else None)
            fu = funds.get(r.code, {})
            x = dict(code=r.code, name=r['name'], status=r.status, tracked=r.code in tr, detected_on=r.detected_on, source=r.source, **st)
            for k in ('sector', 'industry', 'ipo_date', 'shares_out', 'revenue_ttm', 'revenue_fy', 'net_income_fy', 'is_period', 'cash', 'debt',
                      'total_assets', 'equity', 'bs_period', 'description'):
                x[k] = fu.get(k)
            x['fund_asof'] = fu.get('fetched')
            x['fund_days_after_listing'] = (pd.Timestamp(fu['fetched']) - pd.Timestamp(st['listing_date'])).days if fu.get('fetched') and st else None
            sh = fu.get('shares_out') or None
            x['mcap_now'] = sh * st['last_close'] if sh and st else None
            x['mcap_at_first_close'] = sh * st['first_close'] if sh and st else None
            x['flag'] = ('large at listing (> A$1bn at first close x current shares): likely secondary/dual listing, demerger or merger vehicle'
                         if (x['mcap_at_first_close'] or 0) > 1e9 else '')
            rows.append(x)
        tab = pd.DataFrame(rows)
        if len(tab): tab = tab.sort_values('listing_date', ascending=False)
        tab.to_csv(OUT + '/newlist_tracker.csv', index=False, float_format='%.6g')
        reg[reg.cls != 'new_listing'].to_csv(OUT + '/newlist_other.csv', index=False)
        # daily price file: latest row per tracked code
        lt = paths[paths.code.isin(tr)].groupby('code').tail(1).copy()
        if len(tab): lt = lt.merge(tab[['code', 'ret_since_first', 'mcap_now']], on='code', how='left')
        lt['value'] = lt.close * lt.volume
        lt.to_csv(f'{OUT}/daily/px_{self.date}.csv.gz', index=False, float_format='%.6g', compression={'method': 'gzip', 'mtime': 0})
        self.write_md(tab, reg, prev_tag, len(new_codes), len(gone), renamed_same_code)
        left1 = self.credits_left()
        sec = time.time() - t0
        new = not os.path.exists(OUT + '/run_log.csv')
        with open(OUT + '/run_log.csv', 'a') as f:
            if new: f.write('date,utc,seconds,credits_spent,credits_left_after,new_codes,tracked,refreshed,fund_fetched\n')
            f.write(f'{self.date},{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},{sec:.0f},{self.cli.spent},{left1},{len(new_codes)},{len(tr)},{n_ref},{len(nf)}\n')
        log(f'done in {sec:.0f}s; credits spent {self.cli.spent} (left {left1}); tracked {len(tr)}, refreshed {n_ref}, fundamentals {len(nf)}')
        return tab

    def fund_index(self):
        out = {}
        if os.path.exists(OUT + '/fund.jsonl'):
            for l in open(OUT + '/fund.jsonl'):
                r = json.loads(l); out.setdefault(r['code'], r)       # first snapshot = "at listing" (or first observation)
        return out

    def bootstrap(self, snap):
        """First run: seed the registry from the offline baseline (codes first traded within TRACK_DAYS) plus ETFs/other securities
        whose EODHD history (research-store symbol_stats) starts within the window."""
        bp = OUT + '/baseline_listings.csv.gz'
        if not os.path.exists(bp): backfill(self.log)
        b = pd.read_csv(bp, dtype={'code': str})
        lim = (pd.Timestamp(self.date) - pd.Timedelta(days=TRACK_DAYS)).date().isoformat()
        b = b[b.first_date >= lim]
        reg = pd.DataFrame(dict(code=b.code, name=b['name'], type='Common Stock', isin=b.isin, cls=b.cls_final, first_date=b.first_date,
                                detected_on=self.date, source='bootstrap (baseline)', predecessor=b.predecessor.fillna(''),
                                evidence=b.evidence.fillna(''), status=np.where(b.delisted == 1, 'delisted', 'active')))
        st = pd.read_csv(OLD + '/symbol_stats.csv')
        u = symbols_local().merge(st, left_on='api_symbol', right_on='symbol')
        o = u[(u['first'] >= lim) & ~u.Code.isin(reg.code)]
        o = o.assign(cls=[classify_type(t, c, n) or 'excluded_by_name' for t, c, n in zip(o.Type, o.Code, o.Name)])
        reg2 = pd.DataFrame(dict(code=o.Code, name=o.Name, type=o.Type, isin=o.Isin, cls=o.cls.replace({'excluded_by_name': 'other_security'}),
                                 first_date=o['first'], detected_on=self.date, source='bootstrap (symbol_stats)', predecessor='', evidence='',
                                 status=np.where(o.delisted == 1, 'delisted', 'active')))
        reg = pd.concat([reg, reg2], ignore_index=True)
        self.log(f'bootstrap registry: {len(reg)} codes first traded since {lim} ({(reg.cls == "new_listing").sum()} new listings)')
        return reg

    def write_md(self, tab, reg, prev_tag, n_new, n_gone, renamed):
        pct = lambda v: '' if v is None or pd.isna(v) else f'{100 * v:+.0f}%'
        m = lambda v: '' if v is None or pd.isna(v) else f'{v / 1e6:,.0f}'
        d30 = (pd.Timestamp(self.date) - pd.Timedelta(days=30)).date().isoformat()
        t = tab if len(tab) else pd.DataFrame(columns=['listing_date', 'code', 'name', 'status', 'ret_since_first', 'n_days'])
        L = [f'# New ASX listings tracker - {self.date}', '',
             'INFORMATION ONLY. Makes no trading decision; feeds nothing in the paper record. EODHD data (private, non-commercial use); '
             'no ASX-website access. Returns from the FIRST EODHD CLOSE (no offer price available), EODHD adjusted close. '
             'Code: bigwins_forward/code/newlist_tracker.py; data: bigwins_forward/data/newlist/.', '',
             f'- Symbol-list diff vs {prev_tag}: {n_new} new codes, {n_gone} codes left the active list, {len(renamed)} same-code name changes.',
             f'- Genuine new listings (3-letter ordinary shares) tracked: {int(t.status.eq("active").sum()) if len(t) else 0} active, '
             f'{int(t.status.eq("delisted").sum()) if len(t) else 0} already delisted; first traded in the last 30 days: '
             f'{int((t.listing_date >= d30).sum()) if len(t) else 0}.',
             f'- Excluded from the table: {int(reg.cls.isin(["likely_rename", "old_history", "eodhd_late_start", "data_stub"]).sum())} renames / carried-over histories / data stubs, '
             f'{int((reg.cls == "etf_fund").sum())} ETFs/funds, {int((reg.cls == "other_security").sum())} other securities '
             f'(rights, deferred settlement, notes...), {int((reg.cls == "pending_first_trade").sum())} pending first trade (see newlist_other.csv).', '']
        if len(renamed): L += ['Same-code name changes this run: ' + '; '.join(f'{r.Code}: {r.Name_prev} -> {r.Name}' for r in renamed.head(10).itertuples()), '']
        L += ['## Latest listings', '', '| listed | code | name | sector | first close | last | since first close | mcap A$m | status |', '|---|---|---|---|---|---|---|---|---|']
        for r in t.head(15).itertuples():
            L.append(f'| {r.listing_date} | {r.code}{"*" if r.flag else ""} | {str(r.name)[:38]} | {getattr(r, "sector", "") or ""} | {r.first_close:.3g} | {r.last_close:.3g} | {pct(r.ret_since_first)} | {m(r.mcap_now)} | {r.status} |')
        L += ['', '\\* large at listing (> A$1bn): likely a secondary/dual listing, demerger or merger vehicle rather than an IPO (kept, flagged). '
              'EODHD gives no IPODate/offer price for AU codes, so returns start at the first close.']
        q = t[(t.n_days >= 5)] if len(t) else t
        for lab, asc in (('Best since listing', False), ('Worst since listing', True)):
            L += ['', f'## {lab} (tracked window, >= 5 trading days)', '', '| code | name | listed | since first close | max drawdown |', '|---|---|---|---|---|']
            for r in q.sort_values('ret_since_first', ascending=asc).head(5).itertuples():
                L.append(f'| {r.code} | {str(r.name)[:38]} | {r.listing_date} | {pct(r.ret_since_first)} | {pct(r.max_drawdown)} |')
        bp = OUT + '/baseline_by_year.csv'
        if os.path.exists(bp):
            by = pd.read_csv(bp)
            L += ['', '## Baseline 2014+ (descriptive only; survivorship-aware; no strategy test)', '',
                  'Per first-trade year: new listings (3-letter ordinary shares, renames/relistings excluded); over the first 365 days from the first close '
                  '(price return, split-adjusted; delisted names to their last EODHD close): share that ever halved / ever doubled, median 12-month return '
                  'vs the S&P/ASX 200 price index over the same window. 2026 is incomplete.', '',
                  '| year | listed | 12m complete | delisted <12m | halved % | doubled % | median 12m | median ASX200 | median excess | beat ASX200 % |',
                  '|---|---|---|---|---|---|---|---|---|---|']
            for r in by.itertuples():
                L.append(f'| {r.year} | {r.n_new_listings} | {r.n_complete_12m} | {r.delisted_within_12m} | {r.pct_halved_12m} | {r.pct_doubled_12m} | '
                         f'{r.median_r12m} | {r.median_axjo_12m} | {r.median_excess_12m} | {r.pct_beat_axjo_12m} |')
        os.makedirs(PAPER, exist_ok=True)
        open(MD + '.tmp', 'w').write('\n'.join(L) + '\n'); os.replace(MD + '.tmp', MD)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--date'); ap.add_argument('--min-left', type=int, default=25000); ap.add_argument('--per-min', type=int, default=150)
    ap.add_argument('--backfill', action='store_true')
    a = ap.parse_args()
    if a.backfill: backfill()
    else: Run(a.date or today_syd(), a.min_left, min(a.per_min, 150)).run()
