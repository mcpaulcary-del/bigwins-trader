# Big Wins multi-market FORWARD paper record -- monthly job (AMENDMENT_forward_multimarket.md, 68_forward_record/).
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Nothing here reads or writes the H82 books, the M3/E3 shadow
# state or the ASX daily job's files; the only shared file is LEDGER.jsonl, to which one hash-chained entry per booked month is appended.
#
# What one run does (idempotent; safe to run every day; a month is booked once; an interrupted run resumes):
#   1. /api/user first; every request is paced at <= 280 API credits a minute and the run stops (and resumes on the next run) before the
#      day's usage would leave fewer than 15,000 credits spare.
#   2. For each market, the newest month-end ME whose next session F (the fill day) has closed: one bulk end-of-day file of the whole
#      exchange for ME (eod-bulk-last-day; finds every company traded heavily enough to matter), the vendor's symbol lists, then the
#      end-of-day rows of each candidate company and of the local index fund (one call each, incremental, adjusted closes re-based on the
#      overlap), and fundamentals (share counts) for universe companies whose file is missing or more than 85 days old (cap markets only).
#      Every raw response is archived gzip-compressed under fwd_multi/data/<market>/raw/.
#   3. Builds the market's decision-date pack with multi_build.py (the tested builder rules) cut at F, and runs the FROZEN engines
#      (multi_engine.py -> multi_frozen/sim6.py, ei6.py, capbuild_fwd.py) for M3, EI10I and CW at A$25,000 and A$100,000 from the first
#      decision (the November 2026 month-end) to ME: before tax and after tax at 32% (CL regime), the local fund on the same dollars,
#      and 100 random-portfolio controls per design (fixed seeds 1000-1099).
#   4. Writes 68_forward_record/multi/SCORECARD_MULTI.md, history_multi.csv (append-only), orders_<ME>.csv, and one ledger entry.
import os, sys, io, json, gzip, time, math, hashlib, argparse, pickle, traceback, fcntl
import numpy as np, pandas as pd
import requests

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
CODE = S + '/bigwins_forward/code'
sys.path.insert(0, CODE)
import multi_build as MB
import multi_engine as ME

DATA = S + '/fwd_multi/data'                                  # store + raw archive (owner keeps this)
REC = S + '/onedrive/research2/68_forward_record'
DAILY_LOCK = S + '/bigwins_forward/out/paper_state/.daily.lock'   # the ASX daily job's lock (paper_daily.py), held while a month is booked
K0_MONTH = '2026-11'                                         # first decision: each market's last session of November 2026
SIZES = (25000.0, 100000.0)
SEEDS = range(1000, 1100)
N_TRIALS = 1711                                              # information-only DSR (AMENDMENT_adopt_rule_v2: not part of the bar)
ADOPT_SIZE = 100000                                          # AMENDMENT_adopt_rule_v2 §2: adoption considered at A$100,000 only
CONTROLS = ('CW',)                                           # AMENDMENT_adopt_rule_v2 §2: controls, never adoptable
START_HIST = '2024-09-01'
NCAND = 350
REFRESH_DAYS = 85
CAP_MARKETS = [m for m, c in MB.MARKETS.items() if 'EI10I' in c['designs']]
HEADER = 'PAPER - Big Wins multi-market forward record. Not shown to beat the index. No real money; no broker orders; the AI never places trades.'


def utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


class Budget(RuntimeError):
    pass


# ---------------------------------------------------------------- API client: pacing, daily reserve, raw archive
class Api:
    BASE = 'https://eodhd.com/api'

    def __init__(self, log, per_min=280, spare=15000, offline=False):
        self.log = log; self.per_min = per_min; self.spare = spare; self.offline = offline
        self.s = requests.Session(); self.H = {'Authorization': 'Bearer proxy-injected', 'User-Agent': 'paper-record/1.0'}
        self.next_t = 0.0; self.spent = 0; self.since_check = 0; self.used = None; self.limit = None
        if not offline: self.check()

    def check(self):
        for _ in range(5):
            try:
                r = self.s.get(self.BASE + '/user', params={'fmt': 'json'}, headers=self.H, timeout=60)
                if r.status_code == 200:
                    j = r.json(); self.used = int(j['apiRequests']); self.limit = int(j['dailyRateLimit']); self.since_check = 0
                    return self.used
            except Exception:
                pass
            time.sleep(15)
        raise Budget('/api/user unavailable')

    def room(self): return self.limit - self.spare - self.used - self.since_check

    def get(self, path, params, cost, mkt, kind, name, fmt='json'):
        if self.offline: raise Budget('offline run: no downloads')
        if self.since_check >= 300: self.check()
        if self.room() < cost: raise Budget(f'daily reserve reached (used {self.used + self.since_check} of {self.limit}; keeping {self.spare} spare)')
        p = dict(params, fmt=fmt)
        for attempt in range(6):
            now = time.monotonic(); t = max(now, self.next_t); self.next_t = t + 60.0 * cost / self.per_min
            if t > now: time.sleep(t - now)
            try:
                r = self.s.get(f'{self.BASE}/{path}', params=p, headers=self.H, timeout=180)
            except requests.RequestException as e:
                self.log('net error', path, type(e).__name__); time.sleep(min(60, 2 ** attempt)); continue
            if r.status_code == 429: self.log('429; sleeping 60 s'); time.sleep(60); continue
            if r.status_code == 402: raise Budget('HTTP 402: daily limit')
            if r.status_code >= 500: time.sleep(min(60, 2 ** attempt)); continue
            break
        else:
            return None, None
        self.spent += cost; self.since_check += cost
        body = r.content
        if r.status_code == 200:
            d = f'{DATA}/{mkt}/raw/{time.strftime("%Y-%m-%d", time.gmtime())}'; os.makedirs(d, exist_ok=True)
            fn = f'{kind}__{name}.{fmt}.gz'.replace('/', '_')
            with gzip.open(f'{d}/{fn}', 'wb') as g: g.write(body)
            with open(f'{DATA}/{mkt}/raw/index.csv', 'a') as fi:
                fi.write(f'{utc()},{kind},{name},{path},{json.dumps({k: v for k, v in p.items()}, sort_keys=True).replace(",", ";")},{r.status_code},{cost},{len(body)},{sha_b(body)},{d[len(DATA) + 1:]}/{fn}\n')
        return r.status_code, body


# ---------------------------------------------------------------- calendars
_CAL = {}
def sessions(mkt):
    if mkt not in _CAL:
        import exchange_calendars as xc
        try: cal = xc.get_calendar(MB.MARKETS[mkt]['cal'], start='2024-01-01', end='2030-12-31')
        except ValueError: cal = xc.get_calendar(MB.MARKETS[mkt]['cal'], start='2024-01-01')      # holidays not yet published that far
        s = [str(x.date()) for x in cal.sessions]
        s += [str(x.date()) for x in pd.bdate_range(pd.Timestamp(s[-1]) + pd.Timedelta(days=1), '2030-12-31')]   # weekdays as a fallback (the data decide, see book_next)
        _CAL[mkt] = s
    return _CAL[mkt]

def month_end(mkt, ym):
    s = [x for x in sessions(mkt) if x[:7] == ym]; return s[-1] if s else None

def next_session(mkt, d):
    s = sessions(mkt); i = int(np.searchsorted(s, d, side='right')); return s[i]

def _unused_due_months(mkt, today, booked):
    """month-ends from K0 whose fill day is before today (UTC date) and not yet booked"""
    out = []; y, m = map(int, K0_MONTH.split('-'))
    while True:
        ym = f'{y}-{m:02d}'; me = month_end(mkt, ym)
        if me is None or next_session(mkt, me) >= today: break
        if me not in booked: out.append(me)
        m += 1
        if m == 13: y, m = y + 1, 1
    return out


# ---------------------------------------------------------------- store
def store_path(mkt): return f'{DATA}/{mkt}/store.pkl.gz'

def load_store(mkt):
    p = store_path(mkt)
    if os.path.exists(p): return pickle.load(gzip.open(p, 'rb'))
    return dict(series={}, info={}, exch={}, fund={}, fund_fetched={}, cand=[], lists_utc=None)

def save_store(mkt, st):
    p = store_path(mkt); tmp = p + '.tmp'; os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(tmp, 'wb') as g: pickle.dump(st, g, protocol=4)
    os.replace(tmp, p)


def parse_eod_csv(body):
    df = pd.read_csv(io.BytesIO(body))
    if 'Date' not in df or len(df) == 0: return None
    dt = pd.to_datetime(df.Date, errors='coerce'); ok = dt.notna().values & np.isfinite(df.Close.values) & np.isfinite(df.Adjusted_close.values)
    vol = np.nan_to_num(df.Volume.values.astype(np.float64))
    return (dt[ok].values.astype('datetime64[D]').astype(np.int32), df.Close.values[ok].astype(np.float32), df.Adjusted_close.values[ok].astype(np.float32), vol[ok])


def merge_series(old, new):
    """old/new: (d, cl, adj, vol). New rows win. Adjusted closes of old rows before the overlap are re-based by the overlap ratio.
    Returns merged or None when the overlap shows a restatement (raw closes differ or the adjustment ratio is not constant)."""
    d0, c0, a0, v0 = old; d1, c1, a1, v1 = new
    if len(d1) == 0: return old
    ov, i0, i1 = np.intersect1d(d0, d1, return_indices=True)
    if len(ov) == 0:
        return None if d1[0] > d0[-1] + 10 else None
    rc = c1[i1].astype(np.float64) / c0[i0].astype(np.float64); ra = a1[i1].astype(np.float64) / a0[i0].astype(np.float64)
    if np.nanmax(np.abs(rc - 1)) > 1e-4 or (np.nanmax(ra) / np.nanmin(ra) - 1) > 1e-4: return None
    f = float(np.median(ra)); keep = d0 < d1[0]
    return (np.r_[d0[keep], d1].astype(np.int32), np.r_[c0[keep], c1].astype(np.float32), np.r_[(a0[keep] * f), a1].astype(np.float32), np.r_[v0[keep], v1])


# ---------------------------------------------------------------- downloads for one market and month-end
def refresh_market(api, mkt, st, me, fill, prior_rank, held, log, fund_ok=True):
    """bulk at ME -> candidates; symbol lists; incremental end-of-day rows; fundamentals. Raises Budget to stop (resumable)."""
    cfg = MB.MARKETS[mkt]; sc = 1.0 / cfg['fx']; notes = []
    # symbol lists (names, types, currencies) once a month
    if st.get('lists_me') != me:
        for ex in cfg['ex']:
            for dl in (0, 1):
                code, body = api.get(f'exchange-symbol-list/{ex}', {'delisted': dl} if dl else {}, 1, mkt, f'symbols{dl}', ex)
                if code == 200:
                    for x in json.loads(body):
                        if x.get('Type') == 'Common Stock':
                            st['info'][(x['Code'], dl)] = x
                            if dl == 0 or x['Code'] not in st['exch']: st['exch'][x['Code']] = ex
        st['lists_me'] = me; save_store(mkt, st)
    # bulk end-of-day file of the whole exchange for ME
    if st.get('bulk_me') != me:
        tv = []
        for ex in cfg['ex']:
            code, body = api.get(f'eod-bulk-last-day/{ex}', {'date': me}, 100, mkt, 'bulk_eod', f'{ex}_{me}')
            if code != 200: raise RuntimeError(f'{mkt} bulk {ex} {me}: HTTP {code}')
            for r in json.loads(body):
                c = r.get('code'); x = st['info'].get((c, 0))
                if not c or str(r.get('date', ''))[:10] != me or not MB.line_ok(mkt, c, x) or x is None: continue
                try: tv.append((float(r['close']) * float(r['volume']) * sc, c))
                except (TypeError, ValueError, KeyError): pass
        tv.sort(reverse=True); st['bulk_top'] = [c for _, c in tv[:NCAND]]; st['bulk_me'] = me; save_store(mkt, st)
    cand = sorted(set(st.get('bulk_top', [])) | set(c for c, r in prior_rank.items() if r <= NCAND + 50) | set(held))
    st['cand'] = cand
    # end-of-day rows: incremental per candidate (+ the fund); a candidate is done for this ME when its stored rows reach F
    today = time.strftime('%Y-%m-%d', time.gmtime())          # a series is fetched at most once a day until its rows reach the fill day
    need = lambda v: v.get('upto', '') < fill and v.get('fetched', '') != today
    todo = [c for c in cand if c not in st['series'] or need(st['series'][c])]
    etf = cfg['etf']; todo_etf = need(st['fund'])
    last_d = lambda rows: str(np.datetime64(int(rows[0][-1]), 'D'))
    log(mkt, me, 'candidates', len(cand), 'to refresh', len(todo) + int(todo_etf))
    def fetch(sym_full, prev):
        frm = START_HIST if prev is None else str((pd.Timestamp(int(prev[0][-1]), unit='D') - pd.Timedelta(days=40)).date())
        code, body = api.get(f'eod/{sym_full}', {'from': frm}, 1, mkt, 'eod', sym_full, fmt='csv')
        if code != 200: return None, code
        new = parse_eod_csv(body)
        if new is None: return None, 'empty'
        if prev is None: return new, 'new'
        m = merge_series(prev, new)
        if m is None:                                            # restatement: whole window again (one more call)
            code, body = api.get(f'eod/{sym_full}', {'from': START_HIST}, 1, mkt, 'eod_full', sym_full, fmt='csv')
            if code != 200: return None, code
            return parse_eod_csv(body), 'restated'
        return m, 'merged'
    if todo_etf:
        prev = st['fund'].get('rows'); m, how = fetch(etf, prev)
        if m is not None: st['fund'] = dict(rows=m, upto=last_d(m), fetched=today)
        else: st['fund']['fetched'] = today; notes.append(f'fund {etf}: {how}')
    nres = 0
    for i, c in enumerate(todo):
        ex = st['exch'].get(c, cfg['ex'][0]); prev = st['series'].get(c, {}).get('rows')
        m, how = fetch(f'{c}.{ex}', prev)
        if m is not None:
            dl = 0 if (c, 0) in st['info'] else (1 if (c, 1) in st['info'] else 0)
            st['series'][c] = dict(rows=m, upto=last_d(m), fetched=today, dl=dl); nres += how == 'restated'
        else:
            st['series'].setdefault(c, {})['fetched'] = today; notes.append(f'{c}: {how}')
        if i % 100 == 99: save_store(mkt, st)
    if nres: notes.append(f'{nres} series re-downloaded after a vendor restatement')
    save_store(mkt, st)
    return notes


def refresh_fundamentals(api, mkt, st, me, uni_codes, log):
    if mkt not in CAP_MARKETS: return []
    cfg = MB.MARKETS[mkt]; notes = []; n = 0; meT = pd.Timestamp(me)
    for c in uni_codes:
        f = st['fund_fetched'].get(c)
        if c in st['fundamentals'] and f and (meT - pd.Timestamp(f)).days <= REFRESH_DAYS: continue
        ex = st['exch'].get(c, cfg['ex'][0])
        code, body = api.get(f'fundamentals/{c}.{ex}', {}, 10, mkt, 'fundamentals', f'{c}.{ex}')
        st['fund_fetched'][c] = me
        if code == 200:
            try: st['fundamentals'][c] = ME.parse_fundamentals(json.loads(body)); n += 1
            except Exception as e: notes.append(f'fundamentals {c}: parse error {type(e).__name__}')
        elif code in (401, 403):
            notes.append(f'fundamentals not available on the current plan (HTTP {code}); share counts carried forward'); break
        if n % 25 == 24: save_store(mkt, st)
    save_store(mkt, st)
    if n: log(mkt, me, 'fundamentals refreshed', n)
    return notes


# ---------------------------------------------------------------- pack + engines for one market at one month-end
def build_pack(mkt, st, fill, out_dir):
    cfg = MB.MARKETS[mkt]
    ser = {c: (v.get('dl', 0), v['rows']) for c, v in st['series'].items() if v.get('rows') is not None}
    d, cl, adj, vol = st['fund']['rows']
    etf = pd.DataFrame(dict(Close=cl.astype(float), Adjusted_close=adj.astype(float)), index=pd.to_datetime(d.astype('datetime64[D]')))
    lg = {}; pk = MB.build(mkt, ser, st['info'], etf, ME.PL, end=fill, log=lg)
    os.makedirs(out_dir, exist_ok=True); p = f'{out_dir}/pack_{mkt}_{fill}.npz'; ME.PL.save_pack(pk, p)
    return p, lg


def fd_for(mkt, st, cols):
    if mkt not in CAP_MARKETS: return None
    last = {}
    for c in cols: last[str(c).split('#')[0]] = str(c)                     # fundamentals belong to the latest company under a code
    return {col: st['fundamentals'].get(code) for code, col in last.items()}


def positions(res, k):
    """names held at decision index k: positions closed by the final liquidation at k (value after costs)"""
    return {int(nn): float(p1) for nn, kb, ke, c0, p1 in res['closed'] if ke == k}


def evaluate(mkt, pack_path, st, me, k0date, log, controls=True):
    cfg = MB.MARKETS[mkt]
    mk0 = ME.S6.Mkt(pack_path, U=100, tick=cfg.get('tick', 'x'))
    fd = fd_for(mkt, st, mk0.cols)
    mk = ME.make_mkt(pack_path, mkt, cfg, fd=fd, today=me)
    k0 = mk.kof(k0date); k1 = mk.kof(me)
    assert str(mk.dd[k1].date()) == me, f'{mkt}: month-end {me} is not a decision row ({mk.dd[k1].date()})'
    assert str(mk.dd[k0].date()) == k0date, f'{mkt}: first decision {k0date} missing'
    kf = k1 + 1 if k1 + 1 < mk.K else None
    names = [str(c) for c in mk.cols]; out = dict(market=mkt, me=me, k0=k0date, months=k1 - k0, designs={}, fund={}, data={})
    with np.errstate(invalid='ignore'):
        out['data'] = dict(universe=int((mk.vrank[k1] <= 100).sum()), with_cap=(int(np.isfinite(mk.cap[k1][mk.vrank[k1] <= 100]).sum()) if fd is not None else None),
                           closes_on_me=int(np.isfinite(mk.px[k1][mk.vrank[k1] <= 100]).sum()), fills_on_F=int(np.isfinite(mk.pe[k1][mk.vrank[k1] <= 100]).sum()),
                           fund_close=bool(np.isfinite(mk.idx_tr[k1])), capstats=(mk.capst if fd is not None else None))
    for S0 in SIZES:
        if k1 > k0:
            f0 = ME.run_fund(mk, S0, k0, k1, 0.0); f1 = ME.run_fund(mk, S0, k0, k1, 0.32)
            out['fund'][str(int(S0))] = dict(navs=[float(x) for x in f0['navs']], final_pre=float(f0['final']), final_tax=float(f1['final']))
    for D in cfg['designs']:
        rk, kw = ME.ranks(mk, D)
        for S0 in SIZES:
            key = f'{D}_{int(S0)}'; o = dict()
            if k1 > k0:
                a0 = ME.run(mk, rk, kw, S0, k0, k1, 0.0); a1 = ME.run(mk, rk, kw, S0, k0, k1, 0.32)
                o.update(navs=[float(x) for x in a0['navs']], final_pre=float(a0['final']), final_tax=float(a1['final']), trades=int(a0['ntr']), costs=float(a0['costpaid']),
                         tax_paid=float(a1['taxpaid']), held={names[n]: round(v, 2) for n, v in sorted(positions(a0, k1).items(), key=lambda x: -x[1])})
            if kf is not None:                                   # the decision at ME, filled at F's close
                b = ME.run(mk, rk, kw, S0, k0, kf, 0.32)
                o['bought_at_me'] = [names[nn] for nn, k in b['entries'] if k == k1]
                o['sold_at_me'] = [names[nn] for nn, kb, ke, c0, p1 in b['closed'] if ke == k1]
                o['held_after_me'] = sorted(names[n] for n in positions(b, kf))
            out['designs'][key] = o
        if k1 > k0 and controls:
            base = ME.control_base(mk, f'{mkt}|{D}'); cv = {S0: [] for S0 in SIZES}
            for sd in SEEDS:
                rr, kw2 = ME.control_ranks(mk, D, sd, base)
                for S0 in SIZES: cv[S0].append(float(ME.run(mk, rr, kw2, S0, k0, k1, 0.32)['final']))
            for S0 in SIZES:
                o = out['designs'][f'{D}_{int(S0)}']; o['controls_final_tax'] = cv[S0]; o['control_pct'] = float(np.mean(np.array(cv[S0]) < o['final_tax']))
    return out


# ---------------------------------------------------------------- scoring
def lead_series(ev, key, S0):
    a = np.array(ev['designs'][key]['navs']); f = np.array(ev['fund'][str(int(S0))]['navs'])
    n = min(len(a), len(f)); ra = a[1:n] / a[:n - 1] - 1; rf = f[1:n] / f[:n - 1] - 1
    return list(ra - rf)


def pooled(evs, design, S0):
    """equal-weight mean across markets of the monthly lead (before tax, after costs); t, DSR at N trials; after-tax annualised lead;
    pooled random-control percentile (the design's mean after-tax excess among the 100 seeds' mean excess)"""
    key = f'{design}_{int(S0)}'; L = []; at = []; cx = []; dx = []
    for ev in evs:
        if key not in ev['designs'] or 'navs' not in ev['designs'][key]: continue
        L.append(lead_series(ev, key, S0))
        yrs = ev['months'] / 12.0; fT = ev['fund'][str(int(S0))]['final_tax']; dT = ev['designs'][key]['final_tax']
        at.append(((dT / S0) ** (1 / yrs) - (fT / S0) ** (1 / yrs)) * 100 if ev['months'] >= 12 else (dT - fT) / S0 * 100)     # under 12 months: cumulative points, not annualised
        if 'controls_final_tax' in ev['designs'][key]:
            cx.append(np.array(ev['designs'][key]['controls_final_tax']) / fT - 1); dx.append(dT / fT - 1)
    if not L: return None
    m = min(len(x) for x in L); P = np.mean([x[:m] for x in L], axis=0)
    o = dict(design=design, size=int(S0), markets=len(L), months=m, mean_lead_pts_yr=(float(P.mean() * 1200) if m >= 12 else float(np.sum(P) * 100)) if m else np.nan,
             after_tax_lead_pts_yr=float(np.nanmean(at)), markets_ahead_after_tax=int(np.sum(np.array(at) > 0)))
    if m >= 3:
        sd = P.std(ddof=1); o['t'] = float(P.mean() / sd * math.sqrt(m)) if sd > 0 else np.nan
        try: o['dsr'] = float(ME.S6.dsr(P, N_TRIALS)[0])
        except Exception: o['dsr'] = np.nan
    else:
        o['t'] = np.nan; o['dsr'] = np.nan
    if cx:
        C = np.mean(cx, axis=0); o['pooled_control_pct'] = float(np.mean(C < np.mean(dx))); o['mean_market_control_pct'] = float(np.mean([np.mean(c < d) for c, d in zip(cx, dx)]))
    return o


def passes(o, t_min=3.0, months_min=36):
    """AMENDMENT_adopt_rule_v2 §2 (ledger seq 19): no DSR; A$100k only; controls (CW) never pass"""
    return (o is not None and o['design'] not in CONTROLS and int(o['size']) == ADOPT_SIZE and o['months'] >= months_min and np.isfinite(o['t']) and o['t'] >= t_min
            and np.isfinite(o['after_tax_lead_pts_yr']) and o['after_tax_lead_pts_yr'] >= 1.0 and o.get('pooled_control_pct', 0) >= 0.90
            and o['markets_ahead_after_tax'] * 2 > o['markets'])


def passes_staged(o):
    """AMENDMENT_adopt_rule_v2 §2 staged step: from 60 months, t >= 2.0 with the other conditions -> one capped A$50,000 slice may be proposed"""
    return passes(o, t_min=2.0, months_min=60)


def verdict(o, pool, me_tag):
    """pre-registered reading (AMENDMENT_forward_multimarket.md section 8). Formal only at a December month-end review."""
    if o is None: return ''
    review = me_tag[5:7] == '12'
    both = [q for q in pool if q and q['design'] == o['design']]
    if o['months'] >= 13 and np.isfinite(o['t']) and (o['t'] <= -2.0 or (o['months'] >= 60 and o['after_tax_lead_pts_yr'] <= -1.0)):
        return 'STOP bar met' + (' (December review: close the line)' if review else ' (formal at the December review)')
    if o['months'] < 36: return 'collecting (no formal reading before 36 months)' + (' [control: never adoptable]' if o['design'] in CONTROLS else '')
    if o['design'] in CONTROLS: return 'continue [control: never adoptable]'
    if int(o['size']) != ADOPT_SIZE: return 'continue [information: adoption is read at A$100,000 only]'
    if passes(o):
        return 'ADOPT bar met at A$100,000' + (' (December review: a real-money proposal may be written; the owner decides)' if review else ' (formal at the December review)')
    if passes_staged(o):
        return 'STAGED step met (capped A$50,000 slice)' + (' (December review: a capped-slice proposal may be written; the owner decides)' if review else ' (formal at the December review)')
    return 'continue'


# ---------------------------------------------------------------- outputs
def write_outputs(out_root, ledger_mod, me_tag, evs, notes, calls, code_hashes, log, ledger=True):
    os.makedirs(out_root, exist_ok=True)
    hist = f'{out_root}/history_multi.csv'; rows = []
    for ev in evs:
        for key, o in ev['designs'].items():
            D, S0 = key.split('_'); f = ev['fund'].get(S0, {})
            lead_m = lead_series(ev, key, float(S0))[-1] if 'navs' in o else np.nan
            rows.append(dict(asof=ev['me'], market=ev['market'], design=D, size=int(S0), months=ev['months'], nav_pre=o.get('navs', [np.nan])[-1], fund_nav_pre=f.get('navs', [np.nan])[-1],
                             lead_month_pts=lead_m * 100 if np.isfinite(lead_m) else np.nan, value_after_tax=o.get('final_tax'), fund_value_after_tax=f.get('final_tax'),
                             control_pct=o.get('control_pct'), n_held=len(o.get('held', {})), bought_at_me=' '.join(o.get('bought_at_me', [])), sold_at_me=' '.join(o.get('sold_at_me', [])),
                             recorded_utc=utc()))
    pool = [pooled([ev for ev in evs], D, S0) for D in ME.DESIGNS for S0 in SIZES]
    for o in pool:
        if o: rows.append(dict(asof=me_tag, market='POOLED', design=o['design'], size=o['size'], months=o['months'], lead_month_pts=np.nan, control_pct=o.get('pooled_control_pct'),
                               nav_pre=np.nan, recorded_utc=utc(), **{k: o[k] for k in ('mean_lead_pts_yr', 'after_tax_lead_pts_yr', 't', 'dsr')}))
    df = pd.DataFrame(rows)
    if os.path.exists(hist):
        old = pd.read_csv(hist)
        if (old['asof'] == me_tag).any(): log('history already holds', me_tag, '- not rewritten'); df = None
        else: df = pd.concat([old, df], ignore_index=True)
    if df is not None: df.to_csv(hist, index=False, lineterminator='\n')
    orows = []
    for ev in evs:
        for key, o in ev['designs'].items():
            for c in o.get('bought_at_me', []): orows.append(dict(market=ev['market'], book=key, action='buy', code=c, fill=f'close of the next session after {ev["me"]}'))
            for c in o.get('sold_at_me', []): orows.append(dict(market=ev['market'], book=key, action='sell', code=c, fill=f'close of the next session after {ev["me"]}'))
    op = f'{out_root}/orders_{me_tag}.csv'; pd.DataFrame(orows, columns=['market', 'book', 'action', 'code', 'fill']).to_csv(op, index=False, lineterminator='\n')
    L = [HEADER, '', f'# Multi-market forward record: scorecard for the month-end of {me_tag}', '',
         f'Updated {utc()}. First decision: the November 2026 month-end (30 Nov 2026); fills at the next session\'s close. Designs frozen as tested (M3 v1.1 behaviour, EI10I, CW; report 77); amendment `AMENDMENT_forward_multimarket.md`.', '',
         '## Plain English', '',
         '- Each line is a paper book that follows a frozen rule in one market, compared with that market\'s index fund on the same dollars. Nothing is traded with real money.',
         '- No formal reading is made before 36 months. Until then the table is information only: one or two years of results say almost nothing (see report 78 for the expected wait).', '']
    L += ['## Pooled across markets (equal weight)', '', '| Design | Size | Markets | Months | Mean lead before tax, pts a year (cumulative pts before 12 months) | After-tax lead, pts a year (cumulative pts before 12 months; mean of markets) | Markets ahead after tax | t | DSR (information only, N = 1,711) | Pooled control percentile | Reading |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for o in pool:
        if not o: continue
        f_ = lambda x, d=2: '' if x is None or not np.isfinite(x) else f'{x:.{d}f}'
        L.append(f"| {o['design']} | A${o['size']:,} | {o['markets']} | {o['months']} | {f_(o['mean_lead_pts_yr'])} | {f_(o['after_tax_lead_pts_yr'])} | {o['markets_ahead_after_tax']} of {o['markets']} | {f_(o['t'])} | {f_(o['dsr'])} | {f_(o.get('pooled_control_pct'))} | {verdict(o, pool, me_tag)} |")
    if not any(pool): L.append('| (no month has been booked yet: the first decision has no return until the following month-end) | | | | | | | | | | |')
    L += ['', '## By market', '', '| Market | Fund | Months | Design | Size | Value before tax | Fund before tax | Lead this month, pts | After-tax value | Fund after tax | Control pct | Names held | Bought at this month-end |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        if r['market'] == 'POOLED': continue
        g = lambda x, d=0: '' if x is None or (isinstance(x, float) and not np.isfinite(x)) else f'{x:,.{d}f}'
        L.append(f"| {r['market']} | {MB.MARKETS[r['market']]['etf']} | {r['months']} | {r['design']} | A${r['size']:,} | {g(r['nav_pre'])} | {g(r['fund_nav_pre'])} | {g(r['lead_month_pts'], 2)} | {g(r['value_after_tax'])} | {g(r['fund_value_after_tax'])} | {g(r['control_pct'], 2)} | {r['n_held']} | {r['bought_at_me'][:120]} |")
    L += ['', '## Data notes', '']
    for ev in evs: L.append(f"- {ev['market']}: universe {ev['data']['universe']}, with a usable cap {ev['data']['with_cap']}, closes on the month-end {ev['data']['closes_on_me']}, fill-day closes {ev['data']['fills_on_F']}, fund close {ev['data']['fund_close']}.")
    for n in notes: L.append(f'- {n}')
    L += ['', f'API credits this run: {calls}. Code SHA-256: ' + ', '.join(f'{k} {v[:12]}' for k, v in sorted(code_hashes.items())) + '.', '',
          'Adopt / stop rule (AMENDMENT_adopt_rule_v2.md, ledger seq 19; replaces amendment section 8 adopt bar): a real-money proposal may be written only when, at a December review after at least 36 months, one design (M3 or EI10I; CW is a control and cannot be adopted) meets ALL of these at the A$100,000 size: pooled monthly lead t >= 3.0; after-tax lead >= +1 point a year; pooled random-control percentile >= 0.90; more than half the markets ahead after tax. No deflated Sharpe ratio or back-test trial count enters the bar (the DSR column is information only). Staged step: from 60 months, t >= 2.0 with the other conditions allows a proposal for one capped A$50,000 slice of 25+ names. No real money in 4- or 10-share books or below a A$50,000 slice; the owner decides. A design and size is closed at a December review from 13 months on when its pooled t <= -2.0, or from 60 months on when its after-tax lead is -1 point a year or worse (this closes a no-edge design 12-30% of the time and a +1 point design up to about 1 time in 6).']
    sp = f'{out_root}/SCORECARD_MULTI.md'; open(sp, 'w').write('\n'.join(L) + '\n')
    files = {'SCORECARD_MULTI.md': sha_f(sp), 'history_multi.csv': sha_f(hist), f'orders_{me_tag}.csv': sha_f(op)}
    e = None
    if ledger:
        e = ledger_mod.append(event=f'multi-market forward record: month-end {me_tag} booked (PAPER ONLY)', asof=me_tag, amendment='AMENDMENT_forward_multimarket.md',
                              files_sha256=files, code_sha256=code_hashes, markets=[ev['market'] for ev in evs], api_credits=calls,
                              pooled={f"{o['design']}_{o['size']}": {k: (None if (isinstance(v, float) and not np.isfinite(v)) else v) for k, v in o.items() if k not in ('design', 'size')} for o in pool if o})
    return files, e


def code_hashes():
    fs = ['paper_multi.py', 'multi_build.py', 'multi_engine.py'] + [f'multi_frozen/{f}' for f in ('sim6.py', 'ei6.py', 'capbuild_fwd.py', 'packlib.py', 'scores.py', 'dlf.py')]
    return {f: sha_f(f'{CODE}/{f}') for f in fs}


# ---------------------------------------------------------------- bootstrap
def bootstrap(mkt, st):
    """first run only: candidate seeds from the tested packs (companies ranked <= 400 at the Oct 2026 month-end) and fundamentals parsed in
    rounds 5-6 (files downloaded 17 Nov 2026), keyed by code"""
    P = {'ASX': 'improve5/data/pack_ASXeodTRv14_M.npz', 'DE': 'improve/data/pack_XETRA_M.npz', 'FR': 'improve/data/pack_PA_M.npz', 'SE': 'improve/data/pack_ST_M.npz',
         'CA': 'improve/data/pack_TO_M.npz', 'SW': 'improve4/data/pack_SW_M.npz', 'KO': 'improve4/data/pack_KO_M.npz', 'TW': 'improve4/data/pack_TW_M.npz', 'SA': 'improve4/data/pack_SA_M.npz',
         'BK': 'improve5/data/pack_BK_M.npz', 'CN': 'improve5/data/pack_CN_M.npz', 'HE': 'improve5/data/pack_HE_M.npz', 'WAR': 'improve5/data/pack_WAR_M.npz', 'BR': 'improve5/data/pack_BR_M.npz'}
    F = {'ASX': 'improve5/data/fund/AU.pkl', 'DE': 'improve5/data/fund/XETRA.pkl', 'FR': 'improve5/data/fund/PA.pkl', 'SE': 'improve5/data/fund/ST.pkl', 'CA': 'improve5/data/fund/TO.pkl',
         'SW': 'improve5/data/fund/SW.pkl', 'KO': 'improve6/data/fund/KO.pkl', 'TW': 'improve6/data/fund/TW.pkl', 'BK': 'improve6/data/fund/BK.pkl', 'SA': 'improve6/data/fund/SA.pkl'}
    z = np.load(f'{S}/{P[mkt]}', allow_pickle=True); dd = pd.DatetimeIndex(z['dec_dates']); k = int(dd.searchsorted(pd.Timestamp('2026-10-30'), side='right') - 1)
    vr = z['vrank'][k]; st['seed_rank'] = {str(c).split('#')[0]: float(v) for c, v in zip(z['cols'], vr) if np.isfinite(v) and v <= 400}
    st['fundamentals'] = {}
    if mkt in F:
        fd = pickle.load(open(f'{S}/{F[mkt]}', 'rb'))
        for c, v in fd.items():
            if v: st['fundamentals'][c.split('#')[0]] = v; st['fund_fetched'][c.split('#')[0]] = '2026-11-17'
    st['bootstrapped'] = utc()


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=REC + '/multi', help='owner-facing outputs (scorecard, history, orders)')
    ap.add_argument('--state', default=S + '/bigwins_forward/out/multi', help='job state, packs, evaluations')
    ap.add_argument('--ledger', default=None, help='ledger file (default: 68_forward_record/LEDGER.jsonl)')
    ap.add_argument('--k0', default=None, help='TEST ONLY: first-decision month (YYYY-MM) instead of 2026-11')
    ap.add_argument('--today', default=None, help='TEST ONLY: pretend the UTC date is this day')
    ap.add_argument('--markets', default=','.join(MB.MARKETS))
    ap.add_argument('--offline', action='store_true', help='no downloads: use the store as it is')
    ap.add_argument('--no-controls', action='store_true')
    ap.add_argument('--data', default=None, help='TEST ONLY: store / raw-archive folder instead of fwd_multi/data')
    a = ap.parse_args()
    global K0_MONTH, DATA
    if a.k0: K0_MONTH = a.k0
    if a.data: DATA = a.data
    os.makedirs(a.state, exist_ok=True); logf = open(f'{a.state}/paper_multi.log', 'a')
    def log(*x):
        s = utc() + ' ' + ' '.join(str(v) for v in x); print(s, flush=True); logf.write(s + '\n'); logf.flush()
    import fwd_ledger as L
    if a.ledger: L.LED = a.ledger
    L.verify()
    today = a.today or time.strftime('%Y-%m-%d', time.gmtime())
    stp = f'{a.state}/state.json'; state = json.load(open(stp)) if os.path.exists(stp) else dict(booked={}, evaluated={}, created=utc(), k0_month=K0_MONTH)
    assert state.get('k0_month', K0_MONTH) == K0_MONTH, 'state belongs to another first-decision month'
    mkts = [m for m in a.markets.split(',') if m]
    try:
        api = Api(log, offline=a.offline)
        log('start', 'today', today, 'API used today', api.used, 'limit', api.limit, 'room', None if a.offline else api.room())
    except Budget as e:
        log('STOP before any download:', e); return 0
    while True:
        r = book_next(a, state, stp, mkts, today, api, log, L)
        if r != 'booked': return 0


def due_month(mkts, today, booked):
    """oldest month (YYYY-MM) from the first decision whose fill day has passed in every market and that is not yet booked"""
    y, m = map(int, K0_MONTH.split('-'))
    while True:
        ym = f'{y}-{m:02d}'
        if ym > today[:7]: return None
        fills = [next_session(x, month_end(x, ym)) for x in mkts if month_end(x, ym)]
        if not fills or max(fills) >= today: return None
        if ym not in booked: return ym
        m += 1
        if m == 13: y, m = y + 1, 1


def book_next(a, state, stp, mkts, today, api, log, L):
    me_tag = due_month(mkts, today, set(state.get('months', [])))
    if me_tag is None: log('nothing due'); return 'idle'
    log('booking month', me_tag)
    notes = []; evs = []; calls0 = api.spent
    for m in mkts:
        me = month_end(m, me_tag); fill = next_session(m, me); k0d = month_end(m, K0_MONTH)
        evp = f'{a.state}/eval/{m}_{me}.json'
        if os.path.exists(evp):
            evs.append(json.load(open(evp))); continue
        st = load_store(m)
        if 'bootstrapped' not in st: bootstrap(m, st); save_store(m, st)
        prior = state['evaluated'].get(m, {}).get('ranks') or st.get('seed_rank', {})
        held = state['evaluated'].get(m, {}).get('held', [])
        try:
            if not a.offline: notes += [f'{m}: {n}' for n in refresh_market(api, m, st, me, fill, prior, held, log)]
            # the data decide the month-end and the fill day: last session of the month in the store, and the next session after it
            probe = str(min(pd.Timestamp(me) + pd.Timedelta(days=12), pd.Timestamp(today) - pd.Timedelta(days=1)).date())
            pk, lg = build_pack(m, st, probe, f'{a.state}/probe'); z = ME.S6.Mkt(pk, U=100); dd_ = pd.DatetimeIndex(z.pk['dates_daily'])
            inm = np.flatnonzero(dd_.strftime('%Y-%m') == me_tag)
            if len(inm) == 0 or inm[-1] + 1 >= len(dd_):
                notes.append(f'{m}: data for {me_tag} / its fill day not complete yet; market not booked this run'); log(m, 'not complete', me_tag); continue
            me_d = str(dd_[inm[-1]].date()); fill_d = str(dd_[inm[-1] + 1].date())
            if (me_d, fill_d) != (me, fill): notes.append(f'{m}: exchange calendar said {me} / {fill}; the data say {me_d} / {fill_d}; the data were followed')
            me, fill = me_d, fill_d; evp = f'{a.state}/eval/{m}_{me}.json'
            if me_tag == K0_MONTH: state.setdefault('k0', {})[m] = me
            k0d = state.get('k0', {}).get(m, k0d)
            pk, lg = build_pack(m, st, fill, f'{a.state}/packs'); z = ME.S6.Mkt(pk, U=100); k1 = z.kof(me)
            assert str(z.dd[k1].date()) == me and k1 + 1 < z.K
            uni = [str(c).split('#')[0] for c, v in zip(z.cols, z.vrank[k1]) if np.isfinite(v) and v <= 100]
            if not a.offline:
                fn = refresh_fundamentals(api, m, st, me, uni, log); notes += [f'{m}: {n}' for n in fn]
            ev = evaluate(m, pk, st, me, k0d, log, controls=not a.no_controls)
            ev['pack_sha256'] = sha_f(pk); ev['build_log'] = lg
            os.makedirs(f'{a.state}/eval', exist_ok=True); json.dump(ev, open(evp, 'w'), default=float)
            with np.errstate(invalid='ignore'):
                state['evaluated'][m] = dict(me=me, ranks={str(c).split('#')[0]: float(v) for c, v in zip(z.cols, z.vrank[k1]) if np.isfinite(v) and v <= NCAND + 50},
                                             held=sorted(set(x.split('#')[0] for o in ev['designs'].values() for x in o.get('held_after_me', []))))
            json.dump(state, open(stp, 'w'), indent=1)
            evs.append(ev); log(m, me, 'evaluated', {k: (round(v.get('final_tax', 0)), round(v.get('control_pct', -1), 2)) for k, v in ev['designs'].items()})
        except Budget as e:
            log('STOP (resumes on the next run):', e); json.dump(state, open(stp, 'w'), indent=1); return 'stopped'
        except Exception as e:
            log(m, 'ERROR', repr(e)); log(traceback.format_exc()); notes.append(f'{m}: error {type(e).__name__}; market not booked this run')
    done = [ev['market'] for ev in evs]
    missing = [m for m in mkts if m not in done]
    # book the month when every market is in, or on the 8th calendar day of the following month with what is there (missing ones flagged)
    nxt = (pd.Timestamp(f'{me_tag}-01') + pd.offsets.MonthBegin(1)); late = pd.Timestamp(today) >= nxt + pd.Timedelta(days=7)
    if missing and not late:
        log('waiting for', missing); json.dump(state, open(stp, 'w'), indent=1); return 'waiting'
    if not evs:                                                     # preflight fix F1 (ledger seq 84): never book a month with no market in it
        state.setdefault('data_block_waits', {}).setdefault(me_tag, []).append(today)
        log('DATA BLOCK', me_tag, ': no market complete by the 8th; month NOT booked (no ledger entry); retried on the next run')
        json.dump(state, open(stp, 'w'), indent=1); return 'waiting'
    for m in missing: notes.append(f'{m}: no complete data by the 8th; month not booked for this market (data block)')
    calls = api.spent - calls0
    # preflight fix F2 (ledger seq 84): book under the ASX daily job's .daily.lock (taken in the same order as paper_daily: .daily.lock, then
    # the ledger lock inside fwd_ledger.append), and re-check the state on disk so a second run never books the same month twice
    with open(DAILY_LOCK, 'a') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        disk = json.load(open(stp)) if os.path.exists(stp) else {}
        if me_tag in disk.get('months', []):
            log('month', me_tag, 'already booked by another run; nothing written'); return 'idle'
        files, e = write_outputs(a.out, L, me_tag, evs, notes, calls, code_hashes(), log)
        for ev in evs: state['booked'].setdefault(ev['market'], []).append(ev['me'])
        state.setdefault('months', []).append(me_tag)
        state.setdefault('runs', []).append(dict(utc=utc(), month=me_tag, markets=done, credits=calls, ledger_seq=e['seq'] if e else None))
        json.dump(state, open(stp, 'w'), indent=1)
    log('booked', me_tag, 'markets', len(done), 'credits', calls, 'ledger seq', e['seq'] if e else None)
    return 'booked'


if __name__ == '__main__':
    sys.exit(main())
