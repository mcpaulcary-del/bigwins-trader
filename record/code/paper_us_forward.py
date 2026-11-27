# US FROZEN-RULES MONTHLY FORWARD TRACKER -- INFORMATION ONLY (ledger seq 107, AMENDMENT_info_US_FROZEN_READ_2028.md;
# monthly snapshots per the draft AMENDMENT_info_US_FORWARD_monthly.md). PAPER ONLY: no real money, no broker orders, the AI never places
# trades. No line, no slot. Nothing here reads or writes any other paper job's state; the only shared file is LEDGER.jsonl.
#
# What one run does (idempotent; resumable; safe to run every day; a month is booked once):
#   1. Due month = the oldest month from November 2026 whose fill day (first US session after its last session) has closed and that is
#      not booked yet. Nothing due -> exit 0.
#   2. Data (EODHD, personal licence, stays in the scratchpad). Never calls the account endpoint. Every call is checked against the job's own
#      credit book (CREDITS: <= 10,000 a UTC day; <= 36,000 over any 365 days outside the one-off bootstrap = 3,000 a month on average):
#        - one-off bootstrap: the research_us panel (no credits) trimmed to 2022-06 -> store/boot.npz; then one end-of-day history call per
#          live company (about 2,700-3,200 credits once) for the 252-session traded-value window the frozen ranking needs (the panel keeps
#          month-end medians, not daily volume);
#        - the US bulk end-of-day file (100 credits) for every session since the last stored one, plus that last stored session again as an
#          anchor: the vendor re-adjusts past adjusted closes, so total-return links are taken inside one download batch only;
#        - the active US symbol list (1), four benchmark files (IVV.AU, VGS.AU, NDQ.AU, AUDUSD.FOREX; 1 each), insider Form-4 rows (10 per
#          1,000 rows, about 15-30 a month).
#   3. Assembles the point-in-time panel (research_us layout) and loads it through the studies' own loader (eng4.load -> eng.load), then
#      runs every frozen rule with its own study's engine from A$10,000 on 1 Dec 2026: A3 (eng2.sim + One), P1 LEAD20 and P8 TOPTV20
#      (eng2.sim + eng4.Leaders/TopTV), P6 B25-G3 (c5.build/c5.walk refit each December month-end, lib5.Book, eng2.sim), T1 insider with the
#      audit payout fix (eng3.signals/Event/sim, auditfix rule); personal 47% and super 15%; IVV.AU, VGS.AU and NDQ.AU on the same dollars.
#   4. Writes REC/paper/US_FORWARD.md and REC/paper/us_forward_latest.csv and one `info_us_forward` ledger entry (input hashes, values,
#      orders). Until the monthly amendment is registered in the ledger, months are computed but NOT entered; they are entered in order on the
#      first run after registration.
import os, sys, io, re, json, gzip, time, glob, math, hashlib, argparse, pickle, traceback, fcntl, contextlib, shutil
from unittest import mock
import numpy as np, pandas as pd

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
CODE = S + '/bigwins_forward/code'
REC = S + '/onedrive/research2/68_forward_record'
DATA = S + '/us_forward/data'                     # compact forward store (owner keeps; EODHD data, personal licence)
STATE = S + '/bigwins_forward/out/us_forward'     # job state, evaluations, log, work files
OUT = REC + '/paper'
PANEL = S + '/research_us/data/panel.npz'
BM = S + '/research_us/data/bm/'
ETF2 = S + '/research_us2/data/etf/'
NDQ_HIST = S + '/research_us4/data/etf/NDQ.AU.csv'
PRED = S + '/research_us5/data/pred_open.pkl.gz'
AMEND_107 = 'AMENDMENT_info_US_FROZEN_READ_2028.md'
AMEND_MONTHLY = 'AMENDMENT_info_US_FORWARD_monthly.md'
K0_MONTH = '2026-11'                              # first decision: last US session of November 2026; first fill 1 Dec 2026
SIZE = 10000.0
TRIM = '2022-06-01'                               # history kept from the panel (P6 needs 756 sessions and 37 month-ends before Oct 2025)
REBUILD_FROM = '2025-10'                          # P6 rows rebuilt each run from this month-end (labels of later rows still forming)
BOOT_FROM = '2023-06-01'                          # per-symbol bootstrap history start (1 credit per call whatever the length)
TV_FROM = '2025-10-01'                            # first row of the daily traded-value window kept from the bootstrap
DAY_CAP, YEAR_CAP, BOOT_CAP = 10000, 36000, 7000      # bootstrap: 3,163 credits were spent twice on 26 Nov 2026 (a parse bug voided the first pass)
KEEP_TV = 100e3                                   # a code not yet known is stored only if it traded >= US$100k on some day of the batch
ETFS = ('SPY', 'UPRO', 'BIL')                     # US funds the A3 rule needs (in the US bulk file)
BENCH = ('IVV.AU', 'VGS.AU', 'NDQ.AU', 'AUDUSD.FOREX')
LISTED = {'NYSE', 'NASDAQ', 'NYSE MKT', 'AMEX', 'NYSE ARCA', 'BATS', 'US'}
BADCODE = re.compile(r'-(WS|WT|W|UN|U|R|RT|CL|P)(-.*)?$')
BOOKS = ('A3', 'P1', 'P8', 'P6', 'T1')
BOOK_NAMES = {'A3': '3x S&P 500 trend (research_us2 A3)', 'P1': 'LEAD20 (research_us4 P1)', 'P8': 'TOPTV20 (research_us4 P8)',
              'P6': 'ML book B25-G3 (research_us5 P6)', 'T1': 'Insider T1 + payout fix (research_us3 / audit)'}
TAXES = ('personal', 'super', 'notax')
LABEL = 'INFORMATION ONLY — mostly luck at this stage; first reading Dec 2027'

for p in ('research_us/code', 'research_us2/code', 'research_us3/code', 'research_us4/code', 'research_us5/code', 'research_audit_us/code'):
    if S + '/' + p not in sys.path: sys.path.insert(0, S + '/' + p)
os.environ.setdefault('US5_SEAL', 'open')        # c5 module flag only; this job never uses c5.load or its seal
os.environ['AUDIT_PAYOUT'] = 'fix'
sys.path.insert(0, CODE)
FROZEN = {'eng.py': S + '/research_us/code/eng.py', 'eng2.py': S + '/research_us2/code/eng2.py', 'eng3.py': S + '/research_us3/code/eng3.py',
          'eng4.py': S + '/research_us4/code/eng4.py', 'c5.py': S + '/research_us5/code/c5.py', 'lib5.py': S + '/research_us5/code/lib5.py',
          'auditfix.py': S + '/research_audit_us/code/auditfix.py'}
FROZEN_SHA = {'eng.py': 'ceb5cb48aa2929807e0cf14c147453c1e05c19832145c52062753e3efae3ce7d', 'eng2.py': '4c697e7602aa9397599bc156606d813a1f550f69f869a60a7b84d16691a0e21f',
              'eng4.py': 'd591b3ba0f308c5ab5aa65fa72488da72b3f251a8174a8d13879ee8ed5b6edcb', 'c5.py': '46e75b6341984eaa0c9adaf2a2a19721e78cec11533774c6d50ee310a8984e5d',
              'lib5.py': '303e27896a7d6816479a291a6e9dc3a9f74a23a9ea642a9cd16e25ce0c896dbb'}


def utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def today_utc(): return time.strftime('%Y-%m-%d', time.gmtime())
def sha_b(b): return hashlib.sha256(b).hexdigest()
def sha_f(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def dint(s): return int(np.datetime64(s, 'D').astype(np.int64))
def dstr(i): return str(np.datetime64(int(i), 'D'))
def base_code(c): return str(c).split('#')[0].split('@')[0]


class Budget(RuntimeError):
    pass


def engines():
    """the frozen study engines, imported read-only; their hashes are checked against the frozen records"""
    import eng, eng2, eng3, eng4, c5, lib5, auditfix
    for k, h in FROZEN_SHA.items():
        assert sha_f(FROZEN[k]) == h, f'frozen engine {k} changed'
    return dict(eng=eng, eng2=eng2, eng3=eng3, eng4=eng4, c5=c5, lib5=lib5, auditfix=auditfix)


# ---------------------------------------------------------------- verbatim copies of research_us/code/build.py helpers (build.py runs on import)
def clean(d, cl, adj, vol):
    _, ui = np.unique(d[::-1], return_index=True); ui = np.sort(len(d) - 1 - ui); d, cl, adj, vol = d[ui], cl[ui], adj[ui], vol[ui]
    ok = (cl > 0) & (adj > 0) & np.isfinite(cl) & np.isfinite(adj); d, cl, adj, vol = d[ok], cl[ok], adj[ok], np.nan_to_num(vol[ok])
    if len(d) >= 3:   # bad ticks
        a = adj.astype(np.float64); r1 = a[1:-1] / a[:-2]; r2 = a[2:] / a[:-2]
        bad = ((r1 > 3) | (r1 < 1 / 3)) & (np.abs(r2 - 1) < 0.3); keep = np.r_[True, ~bad, True]
        d, cl, adj, vol = d[keep], cl[keep], adj[keep], vol[keep]
    return d, cl, adj, vol
def split_factor(cl, adj, vol):
    Rr = cl.astype(np.float64) / adj.astype(np.float64); F = np.ones(len(Rr))
    if len(Rr) < 2: return F, 0
    g = Rr[:-1] / Rr[1:]; lg = np.log(g); idx = np.flatnonzero(np.abs(lg) > np.log(1.12)); s = np.ones(len(g))
    for i in idx:
        a = vol[max(0, i - 19):i + 1]; b = vol[i + 1:i + 21]; a = a[a > 0]; b = b[b > 0]
        if len(a) >= 5 and len(b) >= 5:
            x = np.log(np.median(a) / np.median(b))
            if abs(x + lg[i]) < abs(x): continue          # volume not adjusted for this split
        if g[i] > 1: s[i] = g[i]                         # reverse splits (s < 1) never enter F
    F[:-1] = np.cumprod(s[::-1])[::-1]; return F, len(idx)
def norm(s):
    s = re.sub(r'[^A-Z0-9 ]', ' ', str(s).upper()); s = re.sub(r'\b(CLASS [A-Z]|CL [A-Z]|SERIES [A-Z]|COMMON STOCK|COM|INC|CORP|CORPORATION|CO|LTD|PLC|HOLDINGS|HOLDING|THE|NEW|ADR|SA|NV|AG)\b', ' ', s); return re.sub(r'\s+', ' ', s).strip()


def part_start(d, adj, vol):
    """index where the current part of a series starts under build.py: a gap of more than 200 days, a one-row rise of more than x3 (PREREG_d D1)
    or a scale-error fall to under 1/5 without a volume surge (D2) starts a new series; only the last part continues"""
    d = np.asarray(d, np.int64); a = np.asarray(adj, np.float64); v = np.asarray(vol, np.float64)
    gaps = np.flatnonzero(np.diff(d) > 200); start = int(gaps[-1]) + 1 if len(gaps) else 0; last = start
    r = a[start + 1:] / a[start:-1]
    for i in np.flatnonzero((r > 3) | (r < 0.2)):
        g = start + i + 1
        if r[i] > 3: last = g
        else:
            v0 = v[max(start, g - 20):g]; v1 = v[g:g + 20]; v0 = v0[v0 > 0]; v1 = v1[v1 > 0]
            if len(v0) == 0 or len(v1) == 0 or np.median(v1) < 3 * np.median(v0): last = g
    return last


def cut_extras(z, cal):
    """part_start applied to the bootstrap extras (dict of boot_tv.npz arrays; cal = boot calendar as int days): rows before the current part
    are removed and the series' first row moves to the start of the part (it then needs 252 sessions of its own, as in build.py)"""
    T = z['TRx'].shape[0]; w0 = int(z['w0']); notes = []
    for n in range(len(z['xcodes'])):
        tr = z['TRx'][:, n]; ok = np.flatnonzero(np.isfinite(tr))
        if len(ok) < 2: continue
        vol = np.zeros(T); hw = np.flatnonzero(z['HCx'][:, n]) + w0; vol[hw] = z['TVx'][hw - w0, n] / np.maximum(z['RCx'][hw, n], 1e-9)
        st = part_start(cal[ok], tr[ok], vol[ok])
        if st > 0:
            r0 = int(ok[st]); z['TRx'][:r0, n] = np.nan; z['RCx'][:r0, n] = np.nan; z['CDx'][:, n] = np.where(np.arange(T) >= r0, z['CDx'][:, n] - z['CDx'][r0, n], 0)
            if r0 > w0: z['TVx'][:r0 - w0, n] = 0; z['HCx'][:r0 - w0, n] = False
            z['firstx'][n] = int(cal[r0]); notes.append((str(z['xcodes'][n]), str(np.datetime64(int(cal[r0]), 'D'))))
    return notes


# ---------------------------------------------------------------- credit book (the account endpoint is never called)
class Credits:
    """The job's own record of credits spent, per UTC day and kind. Refuses a call that would take today's spend above DAY_CAP, the
    trailing-365-day spend outside the bootstrap above YEAR_CAP (3,000 a month on average), or the one-off bootstrap above BOOT_CAP."""
    def __init__(self, path, day_cap=DAY_CAP, year_cap=YEAR_CAP, boot_cap=BOOT_CAP, clock=today_utc):
        self.path, self.day_cap, self.year_cap, self.boot_cap, self.clock = path, day_cap, year_cap, boot_cap, clock
        self.d = json.load(open(path)) if os.path.exists(path) else dict(days={})
    def _day(self, d): return self.d['days'].setdefault(d, {})
    def today_total(self): return sum(self.d['days'].get(self.clock(), {}).values())
    def year_total(self):
        t = np.datetime64(self.clock()); return sum(v for d, x in self.d['days'].items() if (t - np.datetime64(d)).astype(int) < 365 for k, v in x.items() if k != 'boot')
    def boot_total(self): return sum(x.get('boot', 0) for x in self.d['days'].values())
    def check(self, cost, kind):
        if self.today_total() + cost > self.day_cap: raise Budget(f'day cap: {self.today_total()} + {cost} > {self.day_cap} credits today')
        if kind == 'boot':
            if self.boot_total() + cost > self.boot_cap: raise Budget(f'bootstrap cap {self.boot_cap} reached')
        elif self.year_total() + cost > self.year_cap: raise Budget(f'365-day cap: {self.year_total()} + {cost} > {self.year_cap}')
    def spend(self, cost, kind):
        x = self._day(self.clock()); x[kind] = x.get(kind, 0) + cost; self.save()
    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True); tmp = self.path + '.tmp'; json.dump(self.d, open(tmp, 'w'), indent=1, sort_keys=True); os.replace(tmp, self.path)
    def month_total(self, ym): return sum(v for d, x in self.d['days'].items() if d[:7] == ym for k, v in x.items() if k != 'boot')


class Api:
    BASE = 'https://eodhd.com/api'
    FORBIDDEN = ('user', 'internal-user')                # the account endpoint is never called

    def __init__(self, credits, log, transport=None, per_min=600, index=None):
        self.c, self.log, self.per_min, self.index = credits, log, per_min, index
        self.transport = transport; self.next_t = 0.0; self.spent = 0
        if transport is None:
            import requests
            self.s = requests.Session(); self.H = {'Authorization': 'Bearer proxy-injected', 'User-Agent': 'paper-record/1.0'}
            self.transport = self._http

    def _http(self, path, params):
        r = self.s.get(f'{self.BASE}/{path}', params=params, headers=self.H, timeout=180); return r.status_code, r.content

    def get(self, path, params, cost, kind):
        assert path.split('/')[0].split('?')[0] not in self.FORBIDDEN, 'account endpoint is never called'
        self.c.check(cost, kind)
        for attempt in range(6):
            now = time.monotonic(); t = max(now, self.next_t); self.next_t = t + 60.0 * cost / self.per_min
            if t > now: time.sleep(t - now)
            try: code, body = self.transport(path, dict(params))
            except Exception as e:
                self.log('net error', path, type(e).__name__); time.sleep(min(60, 2 ** attempt)); continue
            if code == 429: self.log('429; sleeping 60 s'); time.sleep(60); continue
            if code == 402: self.c.spend(cost, kind); raise Budget('HTTP 402: vendor daily limit')
            if code >= 500: time.sleep(min(60, 2 ** attempt)); continue
            break
        else:
            raise RuntimeError(f'{path}: no answer after 6 tries')
        self.c.spend(cost, kind); self.spent += cost
        if self.index:
            with open(self.index, 'a') as f: f.write(f'{utc()},{kind},{path},{json.dumps(params, sort_keys=True).replace(",", ";")},{code},{cost},{len(body)},{sha_b(body)}\n')
        return code, body


# ---------------------------------------------------------------- US calendar (planning only; the data decide)
_CAL = None
def sessions():
    global _CAL
    if _CAL is None:
        import exchange_calendars as xc
        try: c = xc.get_calendar('XNYS', start='2022-01-01', end='2030-12-31')
        except ValueError: c = xc.get_calendar('XNYS', start='2022-01-01')
        s = [str(x.date()) for x in c.sessions]
        s += [str(x.date()) for x in pd.bdate_range(pd.Timestamp(s[-1]) + pd.Timedelta(days=1), '2030-12-31')]
        _CAL = s
    return _CAL
def month_end(ym): s = [x for x in sessions() if x[:7] == ym]; return s[-1] if s else None
def next_session(d): s = sessions(); return s[int(np.searchsorted(s, d, side='right'))]
def next_month(ym): y, m = map(int, ym.split('-')); return f'{y + (m == 12)}-{(m % 12) + 1:02d}'


def due_month(today, booked):
    ym = K0_MONTH
    while ym <= today[:7]:
        if next_session(month_end(ym)) >= today: return None
        if ym not in booked: return ym
        ym = next_month(ym)
    return None


# ---------------------------------------------------------------- parsing
def parse_eod_csv(body):
    df = pd.read_csv(io.BytesIO(body))
    if 'Date' not in df or len(df) == 0: return None
    dt = pd.to_datetime(df.Date, errors='coerce'); ok = np.array(dt.notna().values, bool)
    cl = pd.to_numeric(df.Close, errors='coerce').values; adj = pd.to_numeric(df.Adjusted_close, errors='coerce').values
    vol = pd.to_numeric(df.Volume, errors='coerce').fillna(0).values; ok &= np.isfinite(cl) & np.isfinite(adj)
    return (dt[ok].values.astype('datetime64[D]').astype(np.int32), cl[ok].astype(np.float32), adj[ok].astype(np.float32), vol[ok].astype(np.float64))


def parse_bulk(body, day):
    out = {}
    for r in json.loads(body):
        if str(r.get('date', ''))[:10] != day: continue
        try: c, a, v = float(r['close']), float(r['adjusted_close']), float(r.get('volume') or 0)
        except (TypeError, ValueError, KeyError): continue
        if c > 0 and a > 0: out[str(r['code'])] = (c, a, v)
    return out


# ---------------------------------------------------------------- store
class Store:
    def __init__(self, root):
        self.root = root
        for d in ('batches', 'etf', 'insider', 'p6', 'bootchunks'): os.makedirs(f'{root}/{d}', exist_ok=True)
        self.credits_path = f'{root}/credits.json'; self.index = f'{root}/raw_index.csv'
        self.sym_path = f'{root}/symbols.json.gz'

    # symbols: code -> [name, exchange, type, isin, last list date]
    def symbols(self): return json.load(gzip.open(self.sym_path, 'rt')) if os.path.exists(self.sym_path) else {}
    def save_symbols(self, d):
        tmp = self.sym_path + '.tmp'
        with gzip.open(tmp, 'wt') as f: json.dump(d, f)
        os.replace(tmp, self.sym_path)

    def boot_done(self): return os.path.exists(f'{self.root}/boot.npz') and os.path.exists(f'{self.root}/boot_tv.npz')
    def batches(self): return sorted(glob.glob(f'{self.root}/batches/b_*.npz'))
    def last_day(self):
        b = self.batches()
        if b: return dstr(np.load(b[-1])['days'][-1])
        return str(json.load(open(f'{self.root}/boot_meta.json'))['panel_end'])
    def save_npz(self, path, **kw):
        tmp = path + '.tmp.npz'; np.savez_compressed(tmp, **kw); os.replace(tmp, path)
    def size_mb(self):
        return sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(self.root) for f in fs) / 1e6
    def input_hashes(self):
        out = {}
        for p in sorted(glob.glob(f'{self.root}/*.npz') + glob.glob(f'{self.root}/*.json*') + glob.glob(f'{self.root}/batches/*.npz') + glob.glob(f'{self.root}/etf/*') +
                        glob.glob(f'{self.root}/insider/*') + glob.glob(f'{self.root}/p6/*')):
            if p.endswith('credits.json') or p.endswith('.tmp'): continue
            out[os.path.relpath(p, self.root)] = sha_f(p)
        return out


# ---------------------------------------------------------------- bootstrap part 1: the research_us panel (no credits)
def fake_npz(arrays):
    class Z(dict):
        files = list(arrays)
    return Z(arrays)


def load_through_engine(E, arrays, workdir):
    """the studies' own loader (eng4.load -> eng.load) on an assembled panel: eng.R points at the work folder (benchmark csv files), and
    np.load inside eng returns the assembled arrays instead of reading panel.npz"""
    eng, eng4 = E['eng'], E['eng4']
    old = eng.R; eng.R = workdir.rstrip('/') + '/'
    real = np.load
    def fake(path, *a, **k):
        if str(path).endswith('panel.npz'): return fake_npz(arrays)
        return real(path, *a, **k)
    try:
        with mock.patch.object(eng.np, 'load', fake): A, F = eng4.load()
    finally:
        eng.R = old
    return A, F


def write_bm(workdir, series):
    """series: {sym: DataFrame(Date, Close, Adjusted_close)} -> workdir/bm/<sym>.csv (+ the same files flat for eng4.mini_panel)"""
    os.makedirs(workdir + '/bm', exist_ok=True)
    for sym, df in series.items():
        x = df[['Date', 'Close', 'Adjusted_close']].copy(); x.insert(1, 'Open', x.Close); x.insert(2, 'High', x.Close); x.insert(3, 'Low', x.Close); x['Volume'] = 0
        x.to_csv(f'{workdir}/bm/{sym}.csv', index=False)
        shutil.copy(f'{workdir}/bm/{sym}.csv', f'{workdir}/{sym}.csv')
    shutil.copy(ETF2 + 'DTB3.csv', workdir + '/DTB3.csv')


def hist_csv(path):
    df = pd.read_csv(path); df = df[(df.Close > 0) & (df.Adjusted_close > 0)]; return df[['Date', 'Close', 'Adjusted_close']].reset_index(drop=True)


def research_bm():
    s = {}
    for sym in ('SPY.US', 'AUDUSD.FOREX', 'IVV.AU', 'VGS.AU', 'A200.AU', 'STW.AU', 'EFA.US', 'VGTSX.US', 'URTH.US'): s[sym] = hist_csv(BM + sym + '.csv')
    s['QQQ.US'] = hist_csv(ETF2 + 'QQQ.US.csv'); s['UPRO.US'] = hist_csv(ETF2 + 'UPRO.US.csv'); s['BIL.US'] = hist_csv(ETF2 + 'BIL.US.csv'); s['NDQ.AU'] = hist_csv(NDQ_HIST)
    return s


def bootstrap_base(store, E, log, trim=TRIM, panel=PANEL):
    """research_us panel -> store/boot.npz (rows from `trim`, columns with data after it, kept at their panel index), with the full-history facts
    a trimmed panel cannot recompute: first row date, registered and audit-fix payouts, the eng4 earlier-copy guard. Also the P6 training table."""
    z = np.load(panel, allow_pickle=True); arrays = {k: z[k] for k in z.files}
    work = f'{store.root}/../work_boot'; os.makedirs(work, exist_ok=True); write_bm(work, research_bm())
    A, F = load_through_engine(E, arrays, work)
    pay_reg = A.payout.copy(); pay_fix = E['auditfix'].apply(A).payout.copy(); A.payout = pay_reg
    cal = arrays['cal']; r0 = int(np.searchsorted(cal, np.datetime64(trim))); me = arrays['me']; km = me >= r0
    TR = arrays['TR'][r0:]; keep = np.flatnonzero(np.isfinite(TR).any(0))
    first = np.where(A.firstrow < A.T, cal[np.minimum(A.firstrow, A.T - 1)].astype(np.int64), 2 ** 40)
    np.savez_compressed(f'{store.root}/boot.npz.tmp.npz', TR=arrays['TR'][r0:, keep], RC=arrays['RC'][r0:, keep], CD=arrays['CD'][r0:, keep], keep=keep, NT=A.NT,
                        MED=arrays['MED'][km], RK=arrays['RK'][km], me=me[km] - r0, cal=cal[r0:], code=arrays['code'], name=arrays['name'], otc=arrays['otc'],
                        delisted=arrays['delisted'], grp=arrays['grp'], exch=arrays['exch'], first=first, pay_reg=pay_reg, pay_fix=pay_fix, dropcopy=A.dropcopy,
                        k_off=int((~km).sum()))
    os.replace(f'{store.root}/boot.npz.tmp.npz', f'{store.root}/boot.npz')
    # P6 training table (research_us5 pred_open: features, labels, sealed-run predictions); k re-based to the trimmed month-end index
    D = pd.read_pickle(PRED); c5 = E['c5']
    cols = ['k', 'j'] + ['x_' + c for c in c5.PRICE + c5.INS] + ['y1', 'y3', 'y12', 'f1', 'f3', 'f12', 'wreck', 'm3', 'G3', 'W']
    D = D[cols].copy(); D['k'] = D.k - int((~km).sum()); D.to_pickle(f'{store.root}/p6/base_table.pkl.gz')
    meta = dict(created=utc(), panel_sha256=sha_f(panel), pred_sha256=sha_f(PRED), panel_end=str(cal[-1]), trim=trim, k_off=int((~km).sum()), ncols=int(len(keep)))
    json.dump(meta, open(f'{store.root}/boot_meta.json', 'w'), indent=1)
    shutil.rmtree(work, ignore_errors=True); log('bootstrap base written', meta)
    return meta


# ---------------------------------------------------------------- bootstrap part 2: daily traded value for the 252-session window
def boot_codes(store, first_bulk):
    """live panel columns (base code -> column) and codes outside the panel that are big enough to matter on the first bulk day"""
    b = np.load(f'{store.root}/boot.npz', allow_pickle=True); TR = b['TR']; keep = b['keep']; code = b['code']
    alive = keep[np.isfinite(TR[-6:]).any(0)]; alive = alive[alive < int(b['NT']) - 2]; live = {}
    for j in alive:
        c = base_code(code[j])
        if c not in live or j > live[c]: live[c] = int(j)
    med = b['MED'][-1]; rk = b['RK'][-1]; thr = np.sort(med[np.isfinite(rk) & (rk <= 2000)])[0] if np.isfinite(rk).any() else 1e6
    extra = sorted(c for c, (cl, a, v) in first_bulk.items() if c not in live and cl * v >= 0.3 * thr)
    return live, extra, float(thr)


def fetch_history(api, code, frm, kind):
    """one end-of-day history call; None when the vendor has no file (404/empty); a parse failure of a 200 answer stops the run at once"""
    st, body = api.get(f'eod/{code}.US', {'from': frm, 'fmt': 'csv'}, 1, kind)
    if st != 200 or len(body) < 60: return None
    return parse_eod_csv(body)


def bootstrap_tv(store, api, log, first_bulk, symbols):
    """one end-of-day history call per live company: daily traded value (close x volume / split factor, build.py rules) and closes for the
    rows from TV_FROM to the panel end; for companies outside the panel also their prices from BOOT_FROM. Resumable in chunks."""
    meta = json.load(open(f'{store.root}/boot_meta.json'))
    live, extra, thr = boot_codes(store, first_bulk)
    extra = [c for c in extra if c not in ETFS and accept_code(c, symbols.get(c))]
    todo = sorted(live) + extra; done = {}
    for f in sorted(glob.glob(f'{store.root}/bootchunks/c_*.pkl')): done.update(pickle.load(open(f, 'rb')))
    log('bootstrap traded value: codes', len(todo), 'already', len(done), 'rank-2000 median US$m', round(thr / 1e6, 2))
    buf = {}
    def flush():
        if buf: pickle.dump(dict(buf), open(f'{store.root}/bootchunks/c_{len(glob.glob(store.root + "/bootchunks/c_*.pkl")):04d}.pkl', 'wb')); done.update(buf); buf.clear()
    try:
        for c in todo:
            if c in done: continue
            buf[c] = fetch_history(api, c, BOOT_FROM, 'boot')
            if len(buf) >= 200: flush()
    finally:
        flush()
    got = sum(1 for c in live if done.get(c) is not None)
    if got < 0.9 * len(live): raise RuntimeError(f'bootstrap: only {got} of {len(live)} live companies have a history; chunks kept, nothing compacted')
    compact_boot_tv(store, live, extra, done, meta, symbols)
    z = np.load(f'{store.root}/boot_tv.npz', allow_pickle=True); share = float(np.mean(z['TVp'][-1][z['HCp'][-1]] > 0))
    if share < 0.9: os.replace(f'{store.root}/boot_tv.npz', f'{store.root}/boot_tv.rejected.npz'); raise RuntimeError(f'bootstrap: traded value missing for {1 - share:.0%} of live closes; chunks kept')
    log('bootstrap traded value written; live closes with traded value on the last day', round(share, 4)); shutil.rmtree(f'{store.root}/bootchunks', ignore_errors=True); os.makedirs(f'{store.root}/bootchunks', exist_ok=True)


def compact_boot_tv(store, live, extra, rows, meta, symbols):
    b = np.load(f'{store.root}/boot.npz', allow_pickle=True); cal = b['cal'].astype('datetime64[D]').astype(np.int64)
    w0 = int(np.searchsorted(cal, dint(TV_FROM))); cw = cal[w0:]; NW = len(cw)
    keep = b['keep']; pos = {int(j): n for n, j in enumerate(keep)}; RCp = b['RC']
    pc = sorted(live.values()); TVp = np.zeros((NW, len(pc)), np.float32); HCp = np.zeros((NW, len(pc)), bool); VRp = np.full(len(pc), np.nan)
    def tvrows(r):
        d, cl, adj, vol = clean(*r); F, ns = split_factor(cl, adj, vol); tv = cl.astype(np.float64) * vol / F; tv[tv > 150e9] = 0; return d, cl, adj, vol / F, tv, ns
    for n, j in enumerate(pc):
        r = rows.get(base_code(b['code'][j]))
        hc = np.isfinite(RCp[w0:, pos[j]]); HCp[:, n] = hc
        if r is None or len(r[0]) == 0: continue
        d, cl, adj, vr, tv, ns = tvrows(r); p = np.searchsorted(cw, d); ok = (p < NW) & (cw[np.minimum(p, NW - 1)] == d)
        x = np.zeros(NW); x[p[ok]] = tv[ok]; TVp[:, n] = np.where(hc, x, 0)
        v = np.full(NW, np.nan); v[p[ok]] = vr[ok]; VRp[n] = v[-1] if hc[-1] else np.nan
    # companies outside the panel: prices (build.py cleaning) from the trim, traded value and closes in the window
    ex = [c for c in extra if rows.get(c) is not None and len(rows[c][0]) >= 30]; T = len(cal)
    TRx = np.full((T, len(ex)), np.nan, np.float32); RCx = TRx.copy(); CDx = np.zeros((T, len(ex)), np.float32); TVx = np.zeros((NW, len(ex)), np.float32); HCx = np.zeros((NW, len(ex)), bool)
    firstx = np.zeros(len(ex), np.int64); VRx = np.full(len(ex), np.nan)
    for n, c in enumerate(ex):
        d, cl, adj, vr, tv, ns = tvrows(rows[c]); p = np.searchsorted(cal, d); ok = (p < T) & (cal[np.minimum(p, T - 1)] == d); p = p[ok]
        TRx[p, n] = adj[ok]; RCx[p, n] = cl[ok]; a = adj[ok].astype(np.float64); cc = cl[ok].astype(np.float64)
        q = (a[1:] / a[:-1]) / (cc[1:] / cc[:-1]) - 1; q = np.where(np.abs(q) <= 0.12, q, 0.0); cd = np.zeros(T); cd[p[1:]] = q; CDx[:, n] = np.cumsum(cd)
        firstx[n] = d[0] if d[0] > dint(BOOT_FROM) + 5 else -(2 ** 40)
        pw = np.searchsorted(cw, d); okw = (pw < NW) & (cw[np.minimum(pw, NW - 1)] == d); TVx[pw[okw], n] = tv[okw]; HCx[pw[okw], n] = True
        v = np.full(NW, np.nan); v[pw[okw]] = vr[okw]; VRx[n] = v[-1]
    info = [symbols.get(c, ['', '', '', '', '']) for c in ex]
    zz = dict(w0=w0, TRx=TRx, RCx=RCx, CDx=CDx, TVx=TVx, HCx=HCx, firstx=firstx, xcodes=np.array(ex, object).astype(str)); cut_extras(zz, cal)
    store.save_npz(f'{store.root}/boot_tv.npz', w0=w0, pcols=np.array(pc, np.int64), TVp=TVp, HCp=HCp, VRp=VRp, xcodes=np.array(ex, object).astype(str), TRx=TRx, RCx=RCx, CDx=CDx,
                   TVx=TVx, HCx=HCx, firstx=firstx, VRx=VRx, xname=np.array([i[0] for i in info]).astype(str), xexch=np.array([i[1] for i in info]).astype(str),
                   live_codes=np.array(list(live), object).astype(str), live_cols=np.array(list(live.values()), np.int64))


def accept_code(c, info):
    """research_us dl.py universe: common stocks; OTC 5-letter codes ending in F or Y are left out"""
    if c in ETFS: return True
    if info is None or info[2] != 'Common Stock': return False
    otc = info[1] not in LISTED
    return not (otc and len(c) == 5 and c[-1] in 'FY')


# ---------------------------------------------------------------- forward downloads
def refresh_symbols(store, api, log, force=False):
    sy = store.symbols(); stamp = sy.get('__fetched__', [''])[0]
    if not force and stamp[:7] == today_utc()[:7]: return sy
    st, body = api.get('exchange-symbol-list/US', {'fmt': 'json'}, 1, 'run')
    if st != 200: raise RuntimeError(f'symbol list HTTP {st}')
    for x in json.loads(body):
        c = x.get('Code')
        if not c: continue
        sy[c] = [x.get('Name') or '', x.get('Exchange') or '', x.get('Type') or '', x.get('Isin') or '', today_utc()]
    sy['__fetched__'] = [today_utc(), '', '', '', '']; store.save_symbols(sy); log('symbol list', len(sy) - 1)
    return sy


def ingest(store, api, log, upto, symbols, known, kind='run'):
    """US bulk end-of-day files for every XNYS session after the last stored day up to `upto`, plus the last stored day again (anchor).
    Saved as one batch file (also when the budget stops it part way: what was fetched is a valid shorter batch). Returns the new last day."""
    last = store.last_day(); days = [d for d in sessions() if last < d <= upto]
    if not days: return last
    got = {}; anchor = None
    try:
        st, body = api.get('eod-bulk-last-day/US', {'date': last, 'fmt': 'json'}, 100, kind)
        if st != 200: raise RuntimeError(f'bulk {last}: HTTP {st}')
        anchor = parse_bulk(body, last)
        for d in days:
            st, body = api.get('eod-bulk-last-day/US', {'date': d, 'fmt': 'json'}, 100, kind)
            if st != 200: raise RuntimeError(f'bulk {d}: HTTP {st}')
            rows = parse_bulk(body, d)
            if 'SPY' not in rows or len(rows) < 1000: log('bulk', d, 'not complete yet (rows', len(rows), ')'); break
            got[d] = rows
    except Budget as e:
        log('STOP downloads (resumes on the next run):', e)
    finally:
        if anchor is not None and got: write_batch(store, last, anchor, got, symbols, known)
    return store.last_day()


def write_batch(store, last, anchor, got, symbols, known):
    days = [last] + sorted(got); rows = [anchor] + [got[d] for d in sorted(got)]
    tv = {}
    for r in rows[1:]:
        for c, (cl, a, v) in r.items(): tv[c] = max(tv.get(c, 0.0), cl * v)
    codes = sorted(c for c in set().union(*[set(r) for r in rows[1:]]) if c in known or (accept_code(c, symbols.get(c)) and tv.get(c, 0) >= KEEP_TV))
    ix = {c: n for n, c in enumerate(codes)}; X = np.full((3, len(days), len(codes)), np.nan, np.float64)
    for t, r in enumerate(rows):
        for c, v in r.items():
            n = ix.get(c)
            if n is not None: X[:, t, n] = v
    store.save_npz(f'{store.root}/batches/b_{days[0]}_{days[-1]}.npz', days=np.array([dint(d) for d in days], np.int64), codes=np.array(codes).astype(str),
                   close=X[0].astype(np.float32), adj=X[1].astype(np.float32), vol=X[2])


def refresh_bench(store, api, log, frm='2026-10-01'):
    for sym in BENCH:
        p = f'{store.root}/etf/{sym}.csv'
        if os.path.exists(p) and time.strftime('%Y-%m-%d', time.gmtime(os.path.getmtime(p))) == today_utc(): continue
        st, body = api.get(f'eod/{sym}', {'from': frm, 'fmt': 'csv'}, 1, 'run')
        if st == 200 and len(body) > 60: open(p + '.tmp', 'wb').write(body); os.replace(p + '.tmp', p)
        else: log('benchmark', sym, 'HTTP', st)


def refresh_insider(store, api, log, upto, start='2026-09-15', overlap_days=40):
    """Form-4 rows (EODHD insider-transactions, by transaction date, newest first, 1,000 a page, 10 credits a page) from the last pull's end
    minus 40 days (late filings) to `upto`. Compact rows only (code, owner id, dates, code, shares, price, relationship, acquired flag)."""
    stp = f'{store.root}/insider/state.json'; st = json.load(open(stp)) if os.path.exists(stp) else {}
    frm = start if not st.get('upto') else str(np.datetime64(st['upto']) - np.timedelta64(overlap_days, 'D'))
    if st.get('upto', '') >= upto and st.get('pulled') == today_utc(): return 0
    to = upto; pages = []; n = 0
    while to >= frm:
        code, body = api.get('insider-transactions', {'from': frm, 'to': to, 'limit': 1000, 'fmt': 'json'}, 10, 'run')
        if code != 200: raise RuntimeError(f'insider HTTP {code}')
        d = json.loads(body); n += 1; pages += d
        if len(d) < 1000: break
        mn = min(x['date'] for x in d)
        to = str(np.datetime64(mn) - np.timedelta64(1, 'D')) if mn == to else mn
    rows = [(x.get('code'), x.get('ownerCik'), x.get('transactionDate'), x.get('transactionCode'), x.get('transactionAmount'), x.get('transactionPrice'),
             x.get('reportDate'), x.get('postTransactionAmount'), x.get('ownerRelationship'), x.get('transactionAcquiredDisposed')) for x in pages]
    new = pd.DataFrame(rows, columns=['code', 'own', 'td', 'tc', 'amt', 'price', 'rd', 'post', 'rel', 'acq'])
    p = f'{store.root}/insider/rows.csv.gz'
    old = pd.read_csv(p, dtype={'code': str, 'own': str}) if os.path.exists(p) else new.iloc[:0]
    allr = pd.concat([old, new.astype({'own': str})], ignore_index=True).drop_duplicates(['code', 'own', 'td', 'tc', 'amt', 'price', 'rd', 'post'], keep='last')
    allr.to_csv(p + '.tmp', index=False, compression='gzip'); os.replace(p + '.tmp', p)
    json.dump(dict(upto=upto, pulled=today_utc(), pages=n, rows=len(allr)), open(stp, 'w')); log('insider pages', n, 'rows now', len(allr))
    return n


# ---------------------------------------------------------------- assembly: boot panel + forward batches -> research_us panel layout
class Panel:
    pass


def assemble(store, upto=None, log=print, with_tv=True):
    """Returns a Panel with `arrays` (the panel.npz fields eng.load reads, cut at `upto`), the daily traded-value window, first rows, payouts,
    earlier-copy flags, the SPY/UPRO/BIL forward rows and notes. Column layout: panel series (their research index) | bootstrap extras | new
    forward codes | SPY, MTUM (as research_us: the last two columns)."""
    b = np.load(f'{store.root}/boot.npz', allow_pickle=True); NTp = int(b['NT']); NSp = NTp - 2; keep = b['keep']
    has_tv = os.path.exists(f'{store.root}/boot_tv.npz')
    bt = np.load(f'{store.root}/boot_tv.npz', allow_pickle=True) if has_tv else None
    cal_b = b['cal'].astype('datetime64[D]').astype(np.int64); Tb = len(cal_b); notes = []
    # forward batches
    bl = [np.load(p, allow_pickle=True) for p in store.batches()]
    fdays = []
    for z in bl:
        dd = z['days']; ci = list(z['codes'])
        if 'SPY' not in ci: continue
        spy = z['close'][:, ci.index('SPY')]
        for t in range(1, len(dd)):
            if np.isfinite(spy[t]) and dd[t] > (fdays[-1] if fdays else cal_b[-1]) and (upto is None or dd[t] <= dint(upto)): fdays.append(int(dd[t]))
    cal = np.r_[cal_b, np.array(fdays, np.int64)]; T = len(cal); rowof = {int(d): i for i, d in enumerate(cal)}
    # columns
    code = list(b['code'][:NSp]); name = list(b['name'][:NSp]); otc = list(b['otc'][:NSp]); dl = list(b['delisted'][:NSp]); grp = list(b['grp'][:NSp]); exch = list(b['exch'][:NSp])
    first = list(b['first'][:NSp]); pay_reg = list(b['pay_reg'][:NSp]); pay_fix = list(b['pay_fix'][:NSp]); drop = list(b['dropcopy'][:NSp]); dropc = [False] * NSp
    gmap = {}
    for g, n in zip(grp, name):
        gmap.setdefault(norm(n), g)
    gnext = [max(grp) + 1]
    def newcol(c, nm, ex, f0):
        code.append(c); name.append(nm); o = int(ex not in LISTED); otc.append(o); dl.append(0); exch.append(ex)
        k = norm(nm)
        if k not in gmap: gmap[k] = gnext[0]; gnext[0] += 1
        grp.append(gmap[k] if k else (gnext[0] + 10 ** 6)); first.append(f0); pay_reg.append(1.0); pay_fix.append(1.0); drop.append(False)
        dropc.append(bool(ex == 'US' or BADCODE.search(c))); return len(code) - 1
    live = {}
    if has_tv:
        for c, j in zip(bt['live_codes'], bt['live_cols']): live[str(c)] = int(j)
    else:
        TRb = b['TR']; alive = keep[np.isfinite(TRb[-6:]).any(0)]; alive = alive[alive < NSp]
        for j in alive:
            c = base_code(code[j])
            if c not in live or j > live[c]: live[c] = int(j)
    colof = dict(live)
    xcols = []
    if has_tv:
        for c, nm, ex, f0 in zip(bt['xcodes'], bt['xname'], bt['xexch'], bt['firstx']):
            colof[str(c)] = newcol(str(c), str(nm), str(ex), int(f0)); xcols.append(colof[str(c)])
    sy = store.symbols()
    # forward codes not yet in a column
    fwd_codes = []
    for z in bl:
        for c in z['codes']:
            c = str(c)
            if c not in colof and c not in ETFS and c not in fwd_codes: fwd_codes.append(c)
    # ticker-change links: a new code whose ISIN (or normalised name) matches a column that stopped within 5 sessions before its first row
    first_seen = {}; last_seen = {}
    for z in bl:
        dd = z['days']; cl = z['close']
        for n, c in enumerate(z['codes']):
            c = str(c); ok = np.flatnonzero(np.isfinite(cl[1:, n])) + 1
            if len(ok): first_seen[c] = min(first_seen.get(c, 1 << 62), int(dd[ok[0]])); last_seen[c] = max(last_seen.get(c, 0), int(dd[ok[-1]]))
    link = {}
    for c in fwd_codes:
        if c not in first_seen: continue
        info = sy.get(c); isin = info[3] if info else ''; nm = norm(info[0]) if info else ''
        for oc, j in list(colof.items()):
            if oc in fwd_codes or oc in link.values(): continue
            ls = last_seen.get(oc, int(cal_b[-1]) if j < NSp else 0)
            if not (0 < first_seen[c] - ls <= 8): continue
            oi = sy.get(oc)
            if (isin and oi and oi[3] == isin) or (nm and oi and norm(oi[0]) == nm):
                link[c] = oc; notes.append(f'ticker change linked: {oc} -> {c}'); break
    for c in fwd_codes:
        if c in link: colof[c] = colof[link[c]]
        else:
            info = sy.get(c, ['', '', '', '', '']); colof[c] = newcol(c, info[0], info[1], first_seen.get(c, 2 ** 40))
    NS = len(code); NT = NS + 2; iSPY = NS; iMT = NS + 1
    TR = np.full((T, NT), np.nan, np.float32); RC = TR.copy(); CD = np.zeros((T, NT), np.float32)
    TR[:Tb, keep[keep < NSp]] = b['TR'][:, keep < NSp]; RC[:Tb, keep[keep < NSp]] = b['RC'][:, keep < NSp]; CD[:Tb, keep[keep < NSp]] = b['CD'][:, keep < NSp]
    for src, dst in ((NTp - 2, iSPY), (NTp - 1, iMT)):
        if src in set(keep.tolist()):
            n = int(np.flatnonzero(keep == src)[0]); TR[:Tb, dst] = b['TR'][:, n]; RC[:Tb, dst] = b['RC'][:, n]; CD[:Tb, dst] = b['CD'][:, n]
    if xcols:
        TR[:Tb, xcols] = bt['TRx']; RC[:Tb, xcols] = bt['RCx']; CD[:Tb, xcols] = bt['CDx']
    # traded-value window
    w0 = int(bt['w0']) if has_tv else Tb; NWb = Tb - w0
    TV = np.zeros((T - w0, NT), np.float32); HC = np.zeros((T - w0, NT), bool); VR = np.full(NT, np.nan)
    if has_tv:
        pcs = bt['pcols']; TV[:NWb, pcs] = bt['TVp']; HC[:NWb, pcs] = bt['HCp']; VR[pcs] = bt['VRp']
        if xcols: TV[:NWb, xcols] = bt['TVx']; HC[:NWb, xcols] = bt['HCx']; VR[xcols] = bt['VRx']
    # histories fetched later for codes outside the bootstrap (guard_new_codes): prices before the forward rows, traded value in the window
    more = {}
    for p in sorted(glob.glob(f'{store.root}/more/*.npz')):
        c = os.path.basename(p)[:-4]; j = colof.get(c)
        if j is None or j < NSp: continue
        z = np.load(p); d, cl_, adj_, vol_ = clean(z['d'], z['cl'], z['adj'], z['vol']); d = d.astype(np.int64)
        s0 = part_start(d, adj_, vol_); d, cl_, adj_, vol_ = d[s0:], cl_[s0:], adj_[s0:], vol_[s0:]
        if len(d) == 0: continue
        F_, _ = split_factor(cl_, adj_, vol_); tv_ = cl_.astype(np.float64) * vol_ / F_; tv_[tv_ > 150e9] = 0
        pr = np.searchsorted(cal_b, d); okp = (pr < Tb) & (cal_b[np.minimum(pr, Tb - 1)] == d); pr = pr[okp]
        if len(pr) == 0: continue
        TR[pr, j] = adj_[okp]; RC[pr, j] = cl_[okp]; a_ = adj_[okp].astype(np.float64); c_ = cl_[okp].astype(np.float64)
        q_ = np.r_[0, (a_[1:] / a_[:-1]) / (c_[1:] / c_[:-1]) - 1]; q_ = np.where(np.abs(q_) <= 0.12, q_, 0.0); cd_ = np.zeros(Tb); cd_[pr] = q_; CD[:Tb, j] = np.cumsum(cd_)
        inw = pr >= w0; TV[pr[inw] - w0, j] = tv_[okp][inw]; HC[pr[inw] - w0, j] = True; VR[j] = (vol_ / F_)[okp][-1] if pr[-1] == Tb - 1 else np.nan
        first[j] = int(d[0]) if (d[0] > dint(BOOT_FROM) + 5 or s0 > 0) else -(2 ** 40); more[c] = j
    etf = {e: [] for e in ETFS}
    DQ = np.zeros((T - Tb, NT), np.float32)
    # forward rows, batch by batch (total-return links inside a batch only)
    for bi, z in enumerate(bl):
        dd = z['days']; codes = [str(c) for c in z['codes']]; cl = z['close'].astype(np.float64); ad = z['adj'].astype(np.float64); vo = z['vol']
        rows = [rowof.get(int(d)) for d in dd]
        for n, c in enumerate(codes):
            if c in ETFS:
                for t in range(len(dd)):
                    if np.isfinite(cl[t, n]) and np.isfinite(ad[t, n]) and (upto is None or dd[t] <= dint(upto)): etf[c].append((bi, int(dd[t]), cl[t, n], ad[t, n], t == 0))
                if c != 'SPY': continue
                j = iSPY
            else:
                j = colof.get(c)
                if j is None: continue
            okr = np.isfinite(cl[:, n]) & np.isfinite(ad[:, n]); ii = np.flatnonzero(okr)
            if len(ii) == 0 or (len(ii) == 1 and ii[0] == 0): continue
            # anchor of the total-return line: the stored value on the anchor day, re-based on this batch's adjusted close
            prev = np.flatnonzero(np.isfinite(TR[:rows[0] + 1 if rows[0] is not None else T, j]))
            if len(prev) and okr[0] and rows[0] is not None and prev[-1] == rows[0]: tr, pa, pc = float(TR[prev[-1], j]), ad[0, n], cl[0, n]
            elif len(prev): tr, pa, pc = float(TR[prev[-1], j]), None, float(RC[prev[-1], j]); notes.append(f'{c}: no anchor row in batch {dstr(dd[0])}; linked on raw closes')
            else: tr, pa, pc = None, None, None
            # traded value: split factor inside the batch (build.py rule) and the vendor's re-adjustment of volume since the anchor was stored
            F, ns = split_factor(cl[ii, n], ad[ii, n], np.nan_to_num(vo[ii, n])); U = 1.0
            if okr[0] and np.isfinite(VR[j]) and VR[j] > 0 and vo[0, n] > 0:
                u = vo[0, n] / (VR[j] * F[0])
                if abs(math.log(u)) > math.log(1.12): U = u; notes.append(f'{c}: volume re-adjusted by the vendor since the anchor (x{u:.3f})')
            vr = np.full(len(dd), np.nan); vr[ii] = np.nan_to_num(vo[ii, n]) / (F * U)
            for t in range(1, len(dd)):
                r = rows[t]
                if r is None or r < Tb or not okr[t]: continue
                if tr is None: tr = float(cl[t, n]); q = 0.0
                else:
                    ratio = ad[t, n] / pa if pa is not None else cl[t, n] / pc
                    q = ratio / (cl[t, n] / pc) - 1; q = q if abs(q) <= 0.12 else 0.0; tr *= ratio
                pa, pc = ad[t, n], cl[t, n]
                TR[r, j] = tr; RC[r, j] = cl[t, n]; DQ[r - Tb, j] = q
                x = cl[t, n] * vr[t]; TV[r - w0, j] = 0 if x > 150e9 else x; HC[r - w0, j] = True
            if np.isfinite(vr[-1]): VR[j] = vr[-1]
    CD[Tb:] = CD[Tb - 1] + np.cumsum(DQ, axis=0)
    # forward cleaning (build.py / PREREG_d rules on forward rows): bad ticks dropped; an up-break (x3) or a scale-error down-break (to under 1/5
    # without a volume surge) cuts the column: the old part ends there (delisting rule), the rest is a new series that needs its own 252 sessions
    breaks = []
    for j in range(NS):
        rr = np.flatnonzero(np.isfinite(TR[:, j]))
        if len(rr) < 2 or rr[-1] < Tb: continue
        rr = rr[max(0, int(np.searchsorted(rr, Tb)) - 2):]
        a = TR[rr, j].astype(np.float64)
        for m in range(1, len(rr) - 1):
            if rr[m] < Tb: continue
            r1 = a[m] / a[m - 1]; r2 = a[m + 1] / a[m - 1]
            if (r1 > 3 or r1 < 1 / 3) and abs(r2 - 1) < 0.3:
                TR[rr[m], j] = np.nan; RC[rr[m], j] = np.nan; HC[rr[m] - w0, j] = False; TV[rr[m] - w0, j] = 0; notes.append(f'{code[j]}: bad tick dropped {dstr(cal[rr[m]])}')
        rr = rr[np.isfinite(TR[rr, j])]; a = TR[rr, j].astype(np.float64)
        for m in range(1, len(rr)):
            if rr[m] < Tb: continue
            r = a[m] / a[m - 1]; cut = r > 3
            if r < 0.2:
                vol = np.where(HC[:, j], TV[:, j] / np.where(np.isfinite(RC[w0:, j]), RC[w0:, j], np.inf), 0.0); g = rr[m] - w0
                v0 = vol[max(0, g - 20):g]; v1 = vol[g:g + 20]; v0 = v0[v0 > 0]; v1 = v1[v1 > 0]
                cut = len(v0) == 0 or len(v1) == 0 or np.median(v1) < 3 * np.median(v0)
            if cut: breaks.append((j, int(rr[m]), float(r))); break
    if breaks:
        NS0 = NS; add = len(breaks)
        def widen(X, fill): return np.concatenate([X[:, :NS0], np.full((X.shape[0], add), fill, X.dtype), X[:, NS0:]], axis=1)
        TR, RC, CD, TV, HC = widen(TR, np.nan), widen(RC, np.nan), widen(CD, 0), widen(TV, 0), widen(HC, False); VR = np.r_[VR[:NS0], np.full(add, np.nan), VR[NS0:]]
        for j, r0, r in breaks:
            nj = newcol(f'{base_code(code[j])}@f{dstr(cal[r0])}', name[j], exch[j], int(cal[r0])); first[nj] = int(cal[r0])
            for X in (TR, RC): X[r0:, nj] = X[r0:, j]; X[r0:, j] = np.nan
            CD[r0:, nj] = CD[r0:, j] - CD[r0, j]; TV[r0 - w0:, nj] = TV[r0 - w0:, j]; HC[r0 - w0:, nj] = HC[r0 - w0:, j]; TV[r0 - w0:, j] = 0; HC[r0 - w0:, j] = False; VR[nj] = VR[j]
            notes.append(f'{code[j]}: break x{r:.2f} on {dstr(cal[r0])}; continues as new series {code[nj]}')
        NS = len(code); NT = NS + 2
    P = Panel(); P.notes = notes; P.cal = cal.astype('datetime64[D]'); P.Tb = Tb; P.w0 = w0; P.TV = TV; P.HC = HC
    P.first = np.r_[np.array(first, np.int64), [-(2 ** 40)] * 2]; P.pay_reg = np.r_[pay_reg, 1.0, 1.0]; P.pay_fix = np.r_[pay_fix, 1.0, 1.0]
    P.dropcopy = np.r_[drop, False, False].astype(bool); P.dropc = np.r_[dropc, True, True].astype(bool); P.k_off = int(b['k_off']); P.etf = etf; P.NSp = NSp
    P.colof = colof; P.more = set(more.values()); P.lastrow = np.where(np.isfinite(TR), np.arange(T)[:, None], -1).max(0)
    # month-ends (last session of each complete month) and ranks
    ym = P.cal.astype('datetime64[M]').astype(int); me_all = np.flatnonzero(np.r_[ym[1:] != ym[:-1], False]); me_b = b['me']
    me_f = me_all[me_all > me_b[-1]]
    MEDb = np.zeros((len(me_b), NT), np.float32); RKb = np.full((len(me_b), NT), np.nan, np.float32)
    MEDb[:, :NSp] = b['MED'][:, :NSp]; RKb[:, :NSp] = b['RK'][:, :NSp]
    isdel = np.r_[dl, 0, 0].astype(int)
    MEDf, RKf = ranks(P, me_f, isdel, NS) if len(me_f) else (np.zeros((0, NT), np.float32), np.zeros((0, NT), np.float32))
    P.arrays = dict(TR=TR, RC=RC, CD=CD, MED=np.r_[MEDb, MEDf], RK=np.r_[RKb, RKf], me=np.r_[me_b, me_f].astype(np.int64), cal=P.cal,
                    code=np.array(code + ['SPY.US', 'MTUM.US'], object), name=np.array(name + ['SPY.US', 'MTUM.US'], object), otc=np.r_[otc, 1, 1].astype(np.int64),
                    delisted=isdel.astype(np.int64), grp=np.r_[grp, -1, -2].astype(np.int64), exch=np.array(exch + ['x', 'x'], object))
    return P


def ranks(P, me_f, isdel, NS):
    """build.py pass 1 at forward month-ends: median daily traded value over the last 252 sessions (sessions without a row count as zero; at
    least 252 sessions since the series' first row; zero once the series has ended), ranked among series with a close on the day and at least
    200 closes in those sessions; delisted series above the third-largest live median are left out (PREREG_b B4); codes dropped by PREREG_b B3
    (venue label 'US', unit/warrant/right suffixes) are not ranked."""
    TV, HC, cal = P.TV, P.HC, P.cal.astype(np.int64); NT = TV.shape[1]; M = len(me_f)
    MED = np.zeros((M, NT), np.float32); RK = np.full((M, NT), np.nan, np.float32)
    for n, i in enumerate(me_f):
        w = i - P.w0
        if w < 251: raise RuntimeError('traded-value window too short for ' + str(P.cal[i]))
        X = TV[w - 251:w + 1, :NS].astype(np.float64); H = HC[w - 251:w + 1, :NS]
        old = P.first[:NS] <= cal[i - 251]; exists = P.lastrow[:NS] >= i
        MED[n, :NS] = np.where(old & exists, np.median(X, axis=0), 0.0)
        has = H[-1] & (H.sum(0) >= 200) & old & ~P.dropc[:NS]
        c = np.flatnonzero(has); live = c[isdel[c] == 0]
        if len(live) >= 3:
            cap3 = np.sort(MED[n, live])[-3]; c = c[(isdel[c] == 0) | (MED[n, c] <= cap3)]
        o = c[np.argsort(-MED[n, c], kind='stable')]; RK[n, o] = np.arange(1, len(o) + 1)
    return MED, RK


# ---------------------------------------------------------------- price files for the studies' loaders (research history + forward rows)
def chain_etf(hist, rows):
    """research csv history + forward bulk rows of one US fund; adjusted closes re-based on each batch's anchor row"""
    d = list(hist.Date.astype(str)); c = list(hist.Close.astype(float)); a = list(hist.Adjusted_close.astype(float)); idx = {x: n for n, x in enumerate(d)}
    by = {}
    for bi, day, cl, ad, anc in rows: by.setdefault(bi, []).append((day, cl, ad, anc))
    for bi in sorted(by):
        rs = sorted(by[bi]); an = [r for r in rs if r[3]]; scale = None
        if an and dstr(an[0][0]) in idx: scale = a[idx[dstr(an[0][0])]] / an[0][2]
        for day, cl, ad, anc in rs:
            s = dstr(day)
            if anc or s <= d[-1]: continue
            if scale is None: scale = (a[-1] / ad) * (cl / c[-1])          # no anchor: linked on the raw close (no distribution assumed)
            d.append(s); c.append(cl); a.append(ad * scale); idx[s] = len(d) - 1
    return pd.DataFrame(dict(Date=d, Close=c, Adjusted_close=a))


def merge_bench(hist, fwd_csv, notes, sym):
    if not os.path.exists(fwd_csv): notes.append(f'{sym}: no forward file'); return hist
    f = pd.read_csv(fwd_csv); f = f[(f.Close > 0) & (f.Adjusted_close > 0)][['Date', 'Close', 'Adjusted_close']]
    m = hist.merge(f, on='Date', suffixes=('', '_f'))
    if len(m) == 0: notes.append(f'{sym}: forward file does not overlap the history'); return hist
    last = m.iloc[-1]; sc = last.Adjusted_close / last.Adjusted_close_f
    if abs(last.Close / last.Close_f - 1) > 1e-3: notes.append(f'{sym}: raw close differs on the overlap ({last.Date}); re-based anyway')
    new = f[f.Date > hist.Date.iloc[-1]].copy(); new['Adjusted_close'] = new.Adjusted_close * sc
    return pd.concat([hist, new], ignore_index=True)


def price_files(store, P, notes, upto=None):
    s = research_bm()
    for e in ETFS:
        key = {'SPY': 'SPY.US', 'UPRO': 'UPRO.US', 'BIL': 'BIL.US'}[e]; s[key] = chain_etf(s[key], P.etf.get(e, []))
    for sym in BENCH: s[sym] = merge_bench(s[sym], f'{store.root}/etf/{sym}.csv', notes, sym)
    if upto:
        for k in s: s[k] = s[k][s[k].Date <= upto].reset_index(drop=True)
    return s


# ---------------------------------------------------------------- the studies' loader on the assembled panel
def load_A(E, P, series, workdir, provisional=True):
    """eng4.load (-> eng.load) on the assembled arrays, plus one provisional month-end on the last row (the fill day of the newest month-end),
    so that a run to it executes the newest month-end's decisions and a run to the month-end itself liquidates at the fill (the reading)."""
    arr = dict(P.arrays); me = arr['me']; T = arr['TR'].shape[0]
    if provisional and me[-1] < T - 1:
        arr['me'] = np.r_[me, T - 1]; arr['MED'] = np.r_[arr['MED'], arr['MED'][-1:]]; arr['RK'] = np.r_[arr['RK'], arr['RK'][-1:]]
    write_bm(workdir, series)
    A, F = load_through_engine(E, arr, workdir)
    reg = A.payout.copy()
    fix = E['auditfix'].apply(A).payout.copy()
    old = (np.arange(A.NT) < P.NSp) & (A.lastrow < P.Tb - 1)       # series that ended inside the bootstrap: full-history payout
    reg[old] = P.pay_reg[old]; fix[old] = P.pay_fix[old]; A.payout = reg; A.pay_reg = reg; A.pay_fix = fix
    A.dropcopy = A.dropcopy | P.dropcopy[:A.NT]; A.POOL = {}
    A.prov = provisional and me[-1] < T - 1; A.k1 = A.M - 2 if A.prov else A.M - 1
    A.KE = A.k1; A.KC = A.k1; A.sealed = False
    # NDQ.AU on the IVV/VGS fund rule (eng.fund_series 'au' branch, no extra fee)
    eng = E['eng']; old_r = eng.R; eng.R = workdir.rstrip('/') + '/'
    try:
        fi = A.fi; a, c, cd, d0 = eng.daily('NDQ.AU', A.cal); tr = a[fi[1:]] / a[fi[:-1]]; pr = c[fi[1:]] / c[fi[:-1]]; q = tr / pr - 1
        bad = ~((q > -0.001) & (q < 0.12)); pr = np.where(bad, tr, pr); df = np.where(bad, 0, np.maximum(q, 0)); F['NDQ'] = (pr, df / (1 + df))
    finally:
        eng.R = old_r
    return A, F


def etf_panel_a3(E, A, series, workdir):
    """research_us2 A3 instruments: SPY (1 bp), UPRO (3 bp) and the T-bill fund (1 bp; 3-month bill less 0.14% while DTB3 is on file, then the
    BIL.US total return, which is the same thing as a listed fund); built with eng4.mini_panel, the column-for-column equivalent of eng2.etf_panel"""
    Ep = E['eng4'].mini_panel(A, {'SPY': ('SPY.US', 1.0), 'UPRO': ('UPRO.US', 3.0)}, src=workdir.rstrip('/') + '/')
    rf = pd.read_csv(workdir + '/DTB3.csv'); rf.columns = ['d', 'r']; rf = rf[pd.to_numeric(rf.r, errors='coerce').notna()]
    tD = int(np.searchsorted(A.cal, np.datetime64(rf.d.iloc[-1]), side='right')) - 1
    b = series['BIL.US']; bs = pd.Series(b.Adjusted_close.values, index=pd.to_datetime(b.Date).values.astype('datetime64[D]'))
    bs = bs[~bs.index.duplicated(keep='last')].reindex(bs.index.union(A.cal)).ffill().reindex(A.cal).values
    j = Ep.cols['BILL']
    if tD < A.T - 1:
        g = bs[tD:] / bs[tD]; Ep.TR[tD:, j] = Ep.TR[tD, j] * g; Ep.CD[tD:, j] = Ep.CD[tD, j] + np.log(g); Ep.TRf = pd.DataFrame(Ep.TR).ffill().values
    C = Ep.cols; sma = pd.Series(Ep.TRf[:, C['SPY']]).rolling(200).mean().values; on = Ep.TRf[A.me, C['SPY']] > sma[A.me]
    return Ep, np.where(on, C['UPRO'], C['BILL']), on


class Rec:
    """records what a frozen strategy decides (no change to its decisions)"""
    def __init__(self, s, log): self.s, self.L = s, log; self.harvest = getattr(s, 'harvest', False)
    def has(self, t): return self.s.has(t)
    def decide(self, k, t, pos, cash, owed, eq, A, first):
        acts = self.s.decide(k, t, pos, cash, owed, eq, A, first)
        self.L.append(dict(k=int(k), t=int(t), held=sorted(int(j) for j in pos), acts=[(a[0], int(a[1])) for a in acts])); return acts


# ---------------------------------------------------------------- P6 (research_us5 PREREG_final): table, yearly refit, predictions cache
def p6_table(E, A, store, log):
    c5 = E['c5']; base = pd.read_pickle(f'{store.root}/p6/base_table.pkl.gz'); cols = list(base.columns)
    kr = A.K(REBUILD_FROM); Dn = c5.build(A, kr, A.k1, verbose=False)
    for c in cols:
        if c not in Dn: Dn[c] = np.nan
    D = pd.concat([base[base.k < kr], Dn[cols]], ignore_index=True)
    return D, base


def p6_scores(E, A, store, k0, k1, log):
    """G3 and W for every month-end k0..k1. A month's scores come from the model fitted at the last December month-end on or before it, with
    the frozen pipeline (c5.walk: LightGBM seeds 1-3, 3-month purge for G3, 12-month for W); each month's scores are computed once and kept."""
    c5 = E['c5']; p = f'{store.root}/p6/preds.csv.gz'
    cache = pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(columns=['month', 'code', 'j', 'G3', 'W', 'fit'])
    md = lambda k: str(A.cal[A.me[k]].astype('datetime64[M]'))
    need = [k for k in range(k0, k1 + 1) if md(k) not in set(cache.month)]
    D = None
    if need:
        D, base = p6_table(E, A, store, log)
        mon = A.dates[A.me].month
        fitof = {k: max(q for q in range(0, k + 1) if mon[q] == 12) for k in need}
        for kf in sorted(set(fitof.values())):
            ks = [k for k in need if fitof[k] == kf]; Dw = D.copy(); t0 = time.time()
            with contextlib.redirect_stdout(io.StringIO()): Dw, _ = c5.walk(A, Dw, kf, max(ks))
            log('P6 fit', md(kf), 'scored', [md(k) for k in ks], round(time.time() - t0), 's')
            for k in ks:
                g = Dw[Dw.k == k][['j', 'G3', 'W']].copy(); g['month'] = md(k); g['fit'] = md(kf); g['code'] = [str(A.code[j]) for j in g.j]
                cache = g[['month', 'code', 'j', 'G3', 'W', 'fit']] if len(cache) == 0 else pd.concat([cache, g[['month', 'code', 'j', 'G3', 'W', 'fit']]], ignore_index=True)
        cache.to_csv(p + '.tmp', index=False, compression='gzip'); os.replace(p + '.tmp', p)
    # rows for the book: column index by code (the same panel index for panel series)
    rows = []
    for k in range(k0, k1 + 1):
        g = cache[cache.month == md(k)]
        js = [A.colj.get(c, -1) for c in g.code]
        rows.append(pd.DataFrame(dict(k=k, j=np.array(js, int), G3=g.G3.values.astype(float), W=g.W.values.astype(float))))
    R = pd.concat(rows, ignore_index=True); R = R[R.j >= 0]
    return R


# ---------------------------------------------------------------- T1 (research_us3 + research_audit_us fix F)
def t1_events(E, A, store, log):
    eng3 = E['eng3']
    d = eng3.load_feed(); d = d[d.td >= pd.Timestamp(TRIM)]
    p = f'{store.root}/insider/rows.csv.gz'
    if os.path.exists(p):
        f = pd.read_csv(p, dtype={'code': str, 'own': str}, low_memory=False)
        f['own'] = f.own.astype(str).str.lstrip('0'); f['td'] = pd.to_datetime(f.td, errors='coerce'); f['rd'] = pd.to_datetime(f.rd, errors='coerce')
        f = f.dropna(subset=['td', 'rd', 'code']); f['lag'] = (f.rd - f.td).dt.days
        d = pd.concat([d, f[d.columns]], ignore_index=True).drop_duplicates(['code', 'own', 'td', 'tc', 'amt', 'price', 'rd', 'post']).reset_index(drop=True)
    st = {}; EV, POOL, ev = eng3.signals(A, d, stats=st)
    return EV, st


def prep3(E, A, workdir, series):
    """eng3.prep with the T-bill file taken from the work folder; after the last DTB3 day, idle cash earns BIL.US's mean daily total return over
    the last 21 sessions (>= 0), i.e. the 3-month bill less the fund's 0.14% fee, as registered"""
    eng3 = E['eng3']; real = pd.read_csv
    def rc(path, *a, **k): return real(workdir + '/DTB3.csv' if str(path).endswith('DTB3.csv') else path, *a, **k)
    with mock.patch.object(eng3.pd, 'read_csv', rc): eng3.prep(A)
    rf = real(workdir + '/DTB3.csv'); rf.columns = ['d', 'r']; rf = rf[pd.to_numeric(rf.r, errors='coerce').notna()]
    tD = int(np.searchsorted(A.cal, np.datetime64(rf.d.iloc[-1]), side='right')) - 1
    b = series['BIL.US']; bs = pd.Series(b.Adjusted_close.values, index=pd.to_datetime(b.Date).values.astype('datetime64[D]'))
    bs = bs[~bs.index.duplicated(keep='last')].reindex(bs.index.union(A.cal)).ffill().reindex(A.cal).values
    if tD < A.T - 1:                                       # mean daily total return of BIL over the last 21 sessions (BIL is the bill less its 0.14% fee), floored at 0
        g = bs / np.r_[np.full(21, np.nan), bs[:-21]]; r = (g ** (1 / 21.0)) - 1
        A.rcash[tD + 1:] = np.maximum(0.0, np.nan_to_num(r[tD + 1:], nan=float(A.rcash[tD])))


# ---------------------------------------------------------------- running the books
def evaluate(E, A, F, store, series, workdir, log, books=BOOKS, insider_ok=True):
    eng, eng2, eng3, eng4, lib5 = E['eng'], E['eng2'], E['eng3'], E['eng4'], E['lib5']
    k0 = A.K(K0_MONTH); k1 = A.k1; prov = A.M - 1 if A.prov else None
    out = dict(k0=str(A.cal[A.me[k0]]), me=str(A.cal[A.me[k1]]), fill=str(A.cal[A.fi[k1]]), months=int(k1 - k0), books={}, funds={}, notes=[])
    SHS = eng2.stock_hs(A); names = lambda js: [base_code(A.code[j]) for j in js]
    def series_runs(simf, mk, hs, payout=None):
        """value if everything were sold at each month-end fill k0..k1 (after costs; tax: personal, super; and before tax)"""
        r = {tax: [SIZE] for tax in TAXES}                  # at the first decision nothing has been bought yet: the A$10,000 itself
        for m in range(k0 + 1, k1 + 1):
            for tax in TAXES: r[tax].append(float(simf(mk(), m, tax)['final']))
        return r
    def monthly(name, Pn, mk, hs, names=names):
        simf = lambda s, ke, tax: eng2.sim(Pn, s, SIZE, k0, ke, tax=tax, hs=hs)
        vals = series_runs(simf, mk, hs); o = dict(values=vals)
        if prov is not None:
            L = []; eng2.sim(Pn, Rec(mk(), L), SIZE, k0, prov, tax='personal', hs=hs)
            x = [e for e in L if e['k'] == k1]
            if x:
                acts = x[-1]['acts']; sold = [j for a, j in acts if a == 'sell']; bought = [j for a, j in acts if a == 'buy']
                o.update(sell=names(sold), buy=names(bought), held_after=names(sorted((set(x[-1]['held']) - set(sold)) | set(bought))))
        return o
    t0 = time.time()
    if 'A3' in books:
        Ep, TGT, on = etf_panel_a3(E, A, series, workdir)
        inv = {v: k for k, v in Ep.cols.items()}
        o = monthly('A3', Ep, lambda: eng2.One(TGT), Ep.hs, names=lambda js: [inv[int(j)] for j in js])
        o['signal'] = 'UPRO (SPY above its 200-session average)' if on[k1] else 'T-bill fund (SPY below its 200-session average)'
        out['books']['A3'] = o; log('A3 done', round(time.time() - t0))
    if 'P1' in books or 'P8' in books:
        if 'P1' in books:
            ORD = eng4.score_lists(A, 'M3', k0, k1); out['books']['P1'] = monthly('P1', A, lambda: eng4.Leaders(ORD, 20, 'L25', gate=True), SHS)
            out['books']['P1']['gate'] = 'closed (no purchase: S&P 500 fund below its 10-month average)' if A.sh_on[k1] else 'open'
        if 'P8' in books:
            ORT = eng4.score_lists(A, 'RANK', k0, k1); out['books']['P8'] = monthly('P8', A, lambda: eng4.TopTV(ORT, 20, 40), SHS)
        log('P1/P8 done', round(time.time() - t0))
    if 'P6' in books:
        R = p6_scores(E, A, store, k0, k1, log); Lst = lib5.lists(R, 'G3', k0, k1); FW = lib5.flags(R, 'W', k0, k1)
        out['books']['P6'] = monthly('P6', A, lambda: lib5.Book(Lst, FW, 25, 13), SHS); out['books']['P6']['fit'] = sorted(set(pd.read_csv(f'{store.root}/p6/preds.csv.gz').fit))[-1]
        log('P6 done', round(time.time() - t0))
    if 'T1' in books:
        if not insider_ok: out['notes'].append('T1 not read this month: insider rows not complete to the fill day')
        else:
            prep3(E, A, workdir, series); EV, st = t1_events(E, A, store, log); HS3 = eng3.stock_hs(A); A.payout = A.pay_fix
            try:
                simf = lambda s, ke, tax: eng3.sim(A, s, SIZE, k0, ke, tax=tax, hs=HS3)
                vals = series_runs(simf, lambda: eng3.Event(EV, 20, 396), HS3); o = dict(values=vals)
                L = []
                if k1 > k0: eng3.sim(A, Rec(eng3.Event(EV, 20, 396), L), SIZE, k0, k1, tax='personal', hs=HS3)
                lo = A.fi[k1 - 1] if k1 > k0 else A.fi[k0]
                tr = [(str(A.cal[e['t']]), a, str(A.code[j])) for e in L if lo <= e['t'] < A.fi[k1] for a, j in e['acts']]
                o['trades'] = tr; o['held_after'] = names(L[-1]['held']) if L else []; o['signals_stats'] = {k: int(v) for k, v in st.items()}
                out['books']['T1'] = o
            finally:
                A.payout = A.pay_reg
            log('T1 done', round(time.time() - t0))
    for fk in ('IVV', 'VGS', 'NDQ'):
        out['funds'][fk] = {tax: [SIZE] + [float(eng2.fund(A, F[fk], SIZE, k0, m, tax)['final']) for m in range(k0 + 1, k1 + 1)] for tax in TAXES}
    return out


def worst_fall(v):
    v = np.asarray(v, float)
    if len(v) < 2: return 0.0
    return float((v / np.maximum.accumulate(v) - 1).min())


# ---------------------------------------------------------------- outputs
def summary_rows(ev):
    rows = []; f = ev['funds']
    for b, o in list(ev['books'].items()) + [(k, dict(values=v)) for k, v in f.items()]:
        v = o['values']; r = dict(asof=ev['me'], fill=ev['fill'], months=ev['months'], rule=b, name=BOOK_NAMES.get(b, {'IVV': 'IVV.AU (fund)', 'VGS': 'VGS.AU (fund)', 'NDQ': 'NDQ.AU (fund)'}.get(b, b)))
        for tax in TAXES: r[f'value_{tax}'] = round(v[tax][-1], 2)
        for tax in ('personal', 'super'):
            r[f'gap_IVV_{tax}'] = round(v[tax][-1] - f['IVV'][tax][-1], 2); r[f'gap_VGS_{tax}'] = round(v[tax][-1] - f['VGS'][tax][-1], 2); r[f'gap_NDQ_{tax}'] = round(v[tax][-1] - f['NDQ'][tax][-1], 2)
        r['worst_fall_personal'] = round(worst_fall(v['personal']), 4); r['worst_fall_before_tax'] = round(worst_fall(v['notax']), 4)
        r['label'] = 'information only - mostly luck'; rows.append(r)
    return rows


def write_outputs(out_dir, state_dir, ev, notes, credits_month, store_mb):
    os.makedirs(out_dir, exist_ok=True); rows = summary_rows(ev)
    lp = f'{out_dir}/us_forward_latest.csv'; pd.DataFrame(rows).to_csv(lp, index=False, lineterminator='\n')
    hp = f'{state_dir}/us_forward_history.csv'; h = pd.DataFrame(rows)
    if os.path.exists(hp):
        old = pd.read_csv(hp); h = pd.concat([old[old['asof'] != ev['me']], h], ignore_index=True)
    h.to_csv(hp, index=False, lineterminator='\n')
    g = lambda x: f'{x:,.0f}'
    L = [f'# US frozen rules — monthly forward tracking ({ev["me"][:7]})', '', f'**{LABEL}.**', '',
         'Paper only: no real money, no orders sent anywhere; the AI never places trades. No line, no slot (ledger seq 107 and the monthly amendment). '
         'Each rule is run exactly as frozen in its study, with its study\'s engine, from A$10,000 placed on 1 Dec 2026. Values are what the account would '
         'be worth if everything were sold at the close of the first US session after the month-end, after costs, FX, US withholding and Australian tax. '
         'The dated readings stay as registered: first US session of December 2027 (interim, facts only) and of December 2028 (main). '
         'Nothing can be concluded from these monthly figures.', '',
         f'Month-end {ev["me"]}; values at the fill {ev["fill"]}; months tracked: {ev["months"]}.', '',
         '<details><summary>Monthly figures — information only, mostly luck (folded)</summary>', '',
         '| Rule | Value, personal 47% (A$) | Value, super 15% (A$) | Before tax (A$) | vs IVV.AU personal | vs VGS.AU personal | vs NDQ.AU personal | vs IVV.AU super | Worst fall (personal) |',
         '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append(f"| {r['name']} | {g(r['value_personal'])} | {g(r['value_super'])} | {g(r['value_notax'])} | {r['gap_IVV_personal']:+,.0f} | {r['gap_VGS_personal']:+,.0f} | {r['gap_NDQ_personal']:+,.0f} | {r['gap_IVV_super']:+,.0f} | {r['worst_fall_personal'] * 100:.1f}% |")
    L += ['', '### Orders for the fill after this month-end (paper; personal account)', '']
    for b, o in ev['books'].items():
        if b == 'T1':
            L.append(f"- **{BOOK_NAMES[b]}**: trades during the month: {', '.join(f'{d} {a} {c}' for d, a, c in o.get('trades', [])[:40]) or 'none'}; holding {len(o.get('held_after', []))} names.")
        else:
            extra = f" ({o['signal']})" if 'signal' in o else (f" (buy gate {o['gate']})" if 'gate' in o else '')
            L.append(f"- **{BOOK_NAMES[b]}**{extra}: sell {', '.join(o.get('sell', [])) or 'nothing'}; buy {', '.join(o.get('buy', [])) or 'nothing'}; holding {len(o.get('held_after', []))} after the fill.")
    L += ['', '</details>', '', '## Notes', '']
    L += [f'- {n}' for n in (ev.get('notes', []) + notes)[:60]]
    L += [f'- EODHD credits this calendar month (this job): {credits_month:,}. Forward store size: {store_mb:.0f} MB.', '',
          'Definitions: worst fall = largest drop of the month-end "sold now, after tax" value from its earlier peak. Funds are bought once, distributions reinvested '
          'after tax (eng2.fund). A$ gaps are rule minus fund at the same tax.']
    mp = f'{out_dir}/US_FORWARD.md'; open(mp, 'w').write('\n'.join(L) + '\n')
    return {'paper/US_FORWARD.md': sha_f(mp), 'paper/us_forward_latest.csv': sha_f(lp)}, rows


def code_hashes():
    h = {'paper_us_forward.py': sha_f(os.path.abspath(__file__))}
    for k, p in FROZEN.items(): h[k] = sha_f(p)
    return h


def ledger_registered(L):
    return any(e.get('amendment') == AMEND_MONTHLY for e in L.entries())


def ledger_entry(L, ev, rows, files, inputs, credits_used):
    vals = {r['rule']: {k: r[k] for k in ('value_personal', 'value_super', 'value_notax', 'gap_IVV_personal', 'gap_IVV_super', 'worst_fall_personal')} for r in rows}
    orders = {}
    for b, o in ev['books'].items():
        orders[b] = dict(trades=o.get('trades', [])[:60]) if b == 'T1' else dict(sell=o.get('sell', []), buy=o.get('buy', []), held_after=o.get('held_after', []))
    return L.append(event=f'info_us_forward: month-end {ev["me"]} tracked (INFORMATION ONLY - mostly luck; no line, no slot; not a trial)', kind='info_us_forward',
                    asof=ev['me'], fill=ev['fill'], months=ev['months'], amendment=AMEND_MONTHLY, governed_by=[AMEND_107, AMEND_MONTHLY], values=vals, orders=orders,
                    inputs_sha256=inputs, files_sha256=files, code_sha256=code_hashes(), api_credits_month=credits_used, notes=ev.get('notes', [])[:20])


# ---------------------------------------------------------------- main
@contextlib.contextmanager
def job_lock(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit('another run holds the lock')
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)


def prepare_data(store, api, E, log, upto, insider=True):
    """bootstrap (once) and forward downloads up to `upto`; raises Budget to stop (resumable)"""
    if not os.path.exists(f'{store.root}/boot.npz'): bootstrap_base(store, E, log)
    sy = refresh_symbols(store, api, log)
    known = set(); b = np.load(f'{store.root}/boot.npz', allow_pickle=True)
    kk = b['keep'][np.isfinite(b['TR'][-6:]).any(0)]; known |= {base_code(c) for c in b['code'][kk[kk < int(b['NT']) - 2]]}
    if os.path.exists(f'{store.root}/boot_tv.npz'): known |= set(np.load(f'{store.root}/boot_tv.npz', allow_pickle=True)['xcodes'])
    for p in store.batches(): known |= set(np.load(p)['codes'])
    if not store.batches():
        ingest(store, api, log, sessions()[int(np.searchsorted(sessions(), store.last_day(), side='right'))], sy, known)
    if not os.path.exists(f'{store.root}/boot_tv.npz'):
        z = np.load(store.batches()[0]); first = {str(c): (float(z['close'][1, n]), float(z['adj'][1, n]), float(z['vol'][1, n])) for n, c in enumerate(z['codes']) if np.isfinite(z['close'][1, n])}
        bootstrap_tv(store, api, log, first, sy); known |= set(np.load(f'{store.root}/boot_tv.npz', allow_pickle=True)['xcodes'])
    last = ingest(store, api, log, upto, sy, known)
    refresh_bench(store, api, log)
    ins = False
    if insider:
        try: refresh_insider(store, api, log, upto); ins = True
        except Budget: raise
        except Exception as e: log('insider pull failed:', repr(e))
    return last, ins


def guard_new_codes(P, A, k1):
    """codes whose history before the forward store is unknown (first seen after the bootstrap window started) and that already trade enough
    to matter: median of their traded value on the forward days they traded >= 50% of the rank-2000 median"""
    rk = A.RK[k1]; ok = np.isfinite(rk) & (rk <= 2000)
    if not ok.any(): return []
    thr = float(np.sort(A.MED[k1][ok])[0]); w = A.me[k1] - P.w0; X = P.TV[max(0, w - 251):w + 1]; cand = []
    for j in range(P.NSp, A.NT - 2):
        if j in P.more or P.first[j] < dint(TV_FROM) or np.isfinite(rk[j]) and rk[j] <= 2000: continue
        x = X[:, j]; x = x[x > 0]
        if len(x) and np.median(x) >= 0.5 * thr: cand.append(str(A.code[j]))
    return cand[:300]


def fetch_more(store, api, log, codes):
    """one end-of-day history call per code (1 credit), kept compact in store/more/; assemble() puts it in front of the forward rows"""
    os.makedirs(f'{store.root}/more', exist_ok=True); n = 0
    for c in codes:
        r = fetch_history(api, c, BOOT_FROM, 'run')
        if r is not None and len(r[0]): store.save_npz(f'{store.root}/more/{c}.npz', d=r[0], cl=r[1], adj=r[2], vol=r[3]); n += 1
    log('history fetched for', n, 'codes outside the bootstrap'); return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT); ap.add_argument('--state', default=STATE); ap.add_argument('--data', default=DATA)
    ap.add_argument('--ledger', default=None); ap.add_argument('--today', default=None, help='TEST ONLY: pretend the UTC date')
    ap.add_argument('--offline', action='store_true', help='no downloads; use the store as it is')
    ap.add_argument('--prefetch', action='store_true', help='bootstrap and download up to yesterday; book nothing')
    ap.add_argument('--books', default=','.join(BOOKS))
    a = ap.parse_args(argv)
    global today_utc
    if a.today: today_utc = (lambda d=a.today: d)
    os.makedirs(a.state, exist_ok=True); logf = open(f'{a.state}/us_forward.log', 'a')
    def log(*x):
        s = utc() + ' ' + ' '.join(str(v) for v in x); print(s, flush=True); logf.write(s + '\n'); logf.flush()
    import fwd_ledger as L
    if a.ledger: L.LED = a.ledger
    with job_lock(f'{a.state}/.us_forward.lock'):
        return run(a, log, L)


def run(a, log, L, transport=None):
    L.verify(); E = engines(); store = Store(a.data); today = today_utc()
    stp = f'{a.state}/state.json'; state = json.load(open(stp)) if os.path.exists(stp) else dict(created=utc(), months={}, k0_month=K0_MONTH)
    credits = Credits(store.credits_path, clock=today_utc)
    api = None if a.offline else Api(credits, log, transport=transport, index=store.index)
    registered = ledger_registered(L)
    # months computed earlier but not yet in the ledger (amendment registered since): enter them in order
    if registered:
        for ym in sorted(state['months']):
            m = state['months'][ym]
            if m.get('ledger_seq') is None and m.get('booked'):
                ev = json.load(open(f'{a.state}/eval/{ym}.json'))
                e = ledger_entry(L, ev, m['rows'], m['files'], m['inputs'], m['credits']); m['ledger_seq'] = e['seq']; json.dump(state, open(stp, 'w'), indent=1)
                log('ledger entry for', ym, 'seq', e['seq'])
    ym = due_month(today, {k for k, v in state['months'].items() if v.get('booked')})
    if a.prefetch:
        upto = sessions()[int(np.searchsorted(sessions(), today, side='left')) - 1]
        try: prepare_data(store, api, E, log, upto, insider=False); log('prefetch done to', store.last_day(), 'store MB', round(store.size_mb(), 1))
        except Budget as e: log('STOP (resumes on the next run):', e)
        return 0
    if ym is None: log('nothing due', today); return 0
    me = month_end(ym); fill = next_session(me); log('due month', ym, 'month-end', me, 'fill', fill)
    ins = True
    if api is not None:
        try: _, ins = prepare_data(store, api, E, log, fill)
        except Budget as e: log('STOP (resumes on the next run):', e); return 0
    else:
        ist = f'{store.root}/insider/state.json'; ins = os.path.exists(ist) and json.load(open(ist)).get('upto', '') >= fill
    if store.last_day() < fill: log('data not complete to the fill day', fill, '(store has', store.last_day(), '); waiting'); return 0
    P = assemble(store, upto=fill, log=log)
    if str(P.cal[-1]) != fill: log('fill day', fill, 'not in the data (last', P.cal[-1], '); waiting'); return 0
    notes = list(P.notes)
    work = f'{a.state}/work'; shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    series = price_files(store, P, notes, upto=fill)
    A, F = load_A(E, P, series, work)
    A.colj = {str(c): j for j, c in enumerate(A.code)}; A.NSp = P.NSp
    k1 = A.k1; assert str(A.cal[A.me[k1]]) == me, (A.cal[A.me[k1]], me)
    extra = guard_new_codes(P, A, k1)
    if extra and api is not None:
        try:
            if fetch_more(store, api, log, extra):
                P = assemble(store, upto=fill, log=log); notes = list(P.notes); series = price_files(store, P, notes, upto=fill)
                shutil.rmtree(work, ignore_errors=True); os.makedirs(work); A, F = load_A(E, P, series, work)
                A.colj = {str(c): j for j, c in enumerate(A.code)}; A.NSp = P.NSp; k1 = A.k1
                notes.append(f'history fetched for {len(extra)} codes that traded enough to matter: {", ".join(extra[:20])}')
        except Budget as e: log('STOP (resumes on the next run):', e); return 0
    elif extra: notes.append(f'{len(extra)} codes outside the bootstrap may be under-ranked this month (offline): {", ".join(extra[:20])}')
    books = tuple(b for b in a.books.split(',') if b)
    ev = evaluate(E, A, F, store, series, work, log, books=books, insider_ok=ins)
    ev['notes'] = ev.get('notes', []) + notes[:40]
    os.makedirs(f'{a.state}/eval', exist_ok=True); json.dump(ev, open(f'{a.state}/eval/{ym}.json', 'w'), indent=1, default=float)
    cm = credits.month_total(today[:7]); inputs = store.input_hashes()
    files, rows = write_outputs(a.out, a.state, ev, [], cm, store.size_mb())
    m = dict(booked=utc(), files=files, rows=rows, inputs=inputs, credits=cm, ledger_seq=None)
    if registered:
        e = ledger_entry(L, ev, rows, files, inputs, cm); m['ledger_seq'] = e['seq']
    else:
        log('monthly amendment not registered in the ledger: outputs written, NO ledger entry (entered after registration)')
    state['months'][ym] = m; json.dump(state, open(stp + '.tmp', 'w'), indent=1); os.replace(stp + '.tmp', stp)
    shutil.rmtree(work, ignore_errors=True)
    log('SUMMARY', ym, ' | '.join(f"{r['rule']} {r['value_personal']:,.0f}" for r in rows), '| ledger seq', m['ledger_seq'], '| credits this month', cm)
    return 0


if __name__ == '__main__':
    sys.exit(main())
