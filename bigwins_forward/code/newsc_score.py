# NEWS-C evaluation (draft amendment AMENDMENT_info_NEWSC_v1.md s6-s7). INFORMATION ONLY: feeds no paper line and no trade; never
# evidence for or against EMG2. THIS SCRIPT MUST NEVER BE USED TO CHANGE THE RUBRIC, the prompt, the baselines or any NEWS-C rule:
# it only reads the recorded days and writes a reading under newsc/readings/<asof>/.
#   python3 newsc_score.py [--asof YYYY-MM-DD] [--external EST-C=0.04,DIL-C=0.3] [--out DIR]
#   python3 newsc_score.py --drops [--asof YYYY-MM-DD] [--out DIR]        (the big-drop log reading; see below)
# Measurement (s6):
#   entry  = the close of the first ASX session that OPENS (10:00 Sydney) after the day's info_news ledger timestamp and in which
#            the share trades (close and volume > 0; a halted share enters at reinstatement). A day whose ledger timestamp is after
#            the open of the first session after the announcement day is LATE and excluded from every bar.
#   return = raw close to raw close, dividends and confirmed corporate-action values as cash (not reinvested), splits applied to the
#            share count, as EST-C; a share that stops trading keeps its last close plus cash. Excess return = return minus the
#            equal-weight return of the announcement day's band-C list over the same sessions (each band-C code with a close at the
#            entry session, tracked the same way).
#   "already in the price" = close before the announcement day -> entry close; reported, never an outcome.
# Readings (s7), group C code-days only (holdings outside band C are reported separately, never in a bar):
#   PRIMARY (drift): per announcement month Dec 2026 - Nov 2027, mean 20-session excess return of +2 code-days minus -2 code-days,
#            arm F; "present" iff t >= 2.0 over the monthly measures and the mean of each half (Dec-May, Jun-Nov) > 0.
#   SECONDARY A (wrecks): -2 vs 0 code-days, outcome = 252-session return <= -50%; B (winners): +2 vs 0, return >= +40%; cohorts
#            Dec 2026 - Nov 2028; coefficient with cohort fixed effects, SEs two-way clustered by company and month; t >= 2.0.
#   ADDED VALUE: each reading repeated within KEY type (fixed effects month x KEY type); the AI "adds" iff the within-type estimate
#            keeps the sign of the reading with t >= 1.5.
#   BASELINES: KEY (its own rating, read exactly like the AI), RAISE, HALT, DIR (flag vs no flag, expected sign -, -, +).
#   Benjamini-Hochberg at 10% across the information family (these readings plus EST-C and DIL-C p-values given with --external).
# BIG-DROP LOG (draft AMENDMENT_info_NEWSC_drops_v1.md; `--drops`; added 25 Nov 2026, the v1 file is kept as newsc_score_pre_drops.py
#   and every v1 function above is unchanged): events of the info_drops ledger entries (on time only), entry = the first close at
#   or after the session after D (within 5 sessions, else dropped and counted), horizons 21/63/126/252 sessions; excess over A200
#   tracked the same way; recovered = a split-adjusted close >= the close of D-1 within 252 sessions of D; further fall = a close
#   20% / 50% below the entry close within 252 sessions of D; month-clustered, lag-weighted t (research_dip PREREG s3), by cause
#   class (keyword primary, blinded rater secondary). No return is computed before the reading date: 'no reading' is printed until
#   at least 100 on-time events AND 1 Dec 2029, whichever is later.
import argparse, bisect, glob, hashlib, json, math, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
NEWSC = S + '/bigwins_forward/data/newsc'
SYD = ZoneInfo('Australia/Sydney')
H_DRIFT, H_LONG = 20, 252
WRECK, WINNER = -0.50, 0.40
PRIMARY_MONTHS = [f'{y}-{m:02d}' for y, m in [(2026, 12)] + [(2027, k) for k in range(1, 12)]]
COHORT_MONTHS = PRIMARY_MONTHS + [f'2027-12'] + [f'2028-{k:02d}' for k in range(1, 12)]
READ_PRIMARY, READ_SECONDARY = '2028-01-01', '2029-12-01'
MIN_EACH = 3                         # code-days needed on each side for a monthly drift measure
MIN_MEASURES = 6                     # monthly measures needed for a primary reading
T_BAR, T_ADD, BH_Q = 2.0, 1.5, 0.10
ENTRY_SEARCH = 60                    # sessions searched for a first trade after the entry session


# ---------------------------------------------------------------- market data
class Market:
    """sessions(): sorted 'YYYY-MM-DD'; day(d): {'close','vol','div','split'} dicts by code, or None"""
    def __init__(self, sessions, loader):
        self.ss = list(sessions); self._load = loader; self._c = {}; self.asof = '9999-12-31'

    def day(self, d):
        if d not in self._c: self._c[d] = self._load(d) or dict(close={}, vol={}, div={}, split={})
        return self._c[d]


def bulk_market():
    import paper_lib as P
    return Market(P.sessions(), P.load_day)


def open_time(d): return datetime.fromisoformat(d + 'T10:00:00').replace(tzinfo=SYD)


def track(mk, i0, code, horizons, p0=None):
    """return of 1 share bought at the close of session i0 at each horizon (sessions after i0); None if not yet reached"""
    if p0 is None: p0 = mk.day(mk.ss[i0])['close'].get(code)
    if not p0: return {h: None for h in horizons}
    q, cash, last, out = 1.0, 0.0, p0, {}
    hmax = max(horizons)
    for j in range(1, hmax + 1):
        if i0 + j >= len(mk.ss) or mk.ss[i0 + j] > mk.asof:
            break
        m = mk.day(mk.ss[i0 + j])
        sp = m['split'].get(code)
        if sp and sp > 0: q *= sp
        dv = m['div'].get(code)
        if dv: cash += q * dv
        if code in m['close']: last = m['close'][code]
        if j in horizons: out[j] = (q * last + cash) / p0 - 1
    return {h: out.get(h) for h in horizons}


_BENCH = {}


def outcomes(rows, mk, rec_utc, bandc):
    """rows: list of dicts with day, code. rec_utc: {day: ISO UTC ledger time}. bandc: {day: [codes]}. Adds entry/late/returns."""
    bench = _BENCH.setdefault(id(mk), {})
    for r in rows:
        t = datetime.fromisoformat(rec_utc[r['day']].replace('Z', '+00:00')).astimezone(SYD)
        i_first = bisect.bisect_right(mk.ss, r['day'])                          # first session after the announcement day
        i0 = i_first
        while i0 < len(mk.ss) and open_time(mk.ss[i0]) <= t: i0 += 1             # first session opening after the ledger time
        r['late'] = int(i0 != i_first)
        r['entry'] = None; r['ret20'] = r['ret252'] = r['ex20'] = r['ex252'] = r['already'] = None
        for i in range(i0, min(i0 + ENTRY_SEARCH, len(mk.ss))):
            if mk.ss[i] > mk.asof: break
            m = mk.day(mk.ss[i])
            if m['close'].get(r['code']) and m['vol'].get(r['code'], 0) > 0: r['entry'] = i; break
        if r['entry'] is None: continue
        ie = r['entry']; R = track(mk, ie, r['code'], (H_DRIFT, H_LONG))
        r['ret20'], r['ret252'] = R[H_DRIFT], R[H_LONG]
        key = (ie, hashlib.sha256(' '.join(sorted(bandc.get(r['day'], []))).encode()).hexdigest())
        if key not in bench:
            br = [track(mk, ie, c, (H_DRIFT, H_LONG)) for c in bandc.get(r['day'], [])]
            bench[key] = {h: (float(np.mean([x[h] for x in br if x[h] is not None])) if any(x[h] is not None for x in br) else None)
                          for h in (H_DRIFT, H_LONG)}
        b = bench[key]
        r['ex20'] = None if r['ret20'] is None or b[H_DRIFT] is None else r['ret20'] - b[H_DRIFT]
        r['ex252'] = None if r['ret252'] is None or b[H_LONG] is None else r['ret252'] - b[H_LONG]
        ib = bisect.bisect_left(mk.ss, r['day']) - 1
        while ib >= 0 and r['code'] not in mk.day(mk.ss[ib])['close'] and ib > i_first - 20: ib -= 1
        p_before = mk.day(mk.ss[ib])['close'].get(r['code']) if ib >= 0 else None
        if p_before: r['already'] = mk.day(mk.ss[ie])['close'][r['code']] / p_before - 1
    return rows


# ---------------------------------------------------------------- statistics
def p_one_sided(t, df=None):
    if t is None or not np.isfinite(t): return None
    try:
        from scipy import stats
        return float(stats.t.sf(t, df)) if df else float(stats.norm.sf(t))
    except Exception:
        return 0.5 * math.erfc(t / math.sqrt(2))


def fe_cluster(y, d, fe, c1, c2):
    """OLS of y on indicator d with fixed effects fe; two-way cluster-robust SE (c1, c2). -> (b, se, t, n)"""
    y, d = np.asarray(y, float), np.asarray(d, float)
    fe, c1, c2 = np.asarray(fe), np.asarray(c1), np.asarray(c2)
    yt, dt = y.copy(), d.copy()
    for g in np.unique(fe):
        k = fe == g; yt[k] -= y[k].mean(); dt[k] -= d[k].mean()
    sxx = float(dt @ dt)
    if len(y) < 4 or sxx <= 1e-12: return None, None, None, len(y)
    b = float(dt @ yt) / sxx; e = yt - b * dt; s = dt * e

    def meat(cl):
        u = np.unique(cl); g = len(u)
        v = sum(float(s[cl == x].sum()) ** 2 for x in u)
        return v * (g / (g - 1) if g > 1 else 1.0)
    c12 = np.array([f'{a}|{b_}' for a, b_ in zip(c1, c2)])
    v = (meat(c1) + meat(c2) - meat(c12)) / sxx ** 2
    if v <= 0: v = max(meat(c1), meat(c2)) / sxx ** 2
    se = math.sqrt(v)
    return b, se, (b / se if se > 0 else None), len(y)


def bh(pvals, q=BH_Q):
    """Benjamini-Hochberg: {name: p} -> {name: survives}"""
    items = sorted((p, k) for k, p in pvals.items() if p is not None)
    m = len(items); k_max = 0
    for i, (p, _) in enumerate(items, 1):
        if p <= q * i / m: k_max = i
    return {k: (i < k_max) for i, (p, k) in enumerate(items)}


def monthly_drift(rows, hi, lo, months, sign=1):
    """per month: mean ex20 of hi rows minus mean of lo rows (each side >= MIN_EACH), times sign. -> reading dict"""
    meas = {}
    for m in months:
        a = [r['ex20'] for r in rows if r['month'] == m and hi(r) and r['ex20'] is not None]
        b = [r['ex20'] for r in rows if r['month'] == m and lo(r) and r['ex20'] is not None]
        if len(a) >= MIN_EACH and len(b) >= MIN_EACH: meas[m] = sign * (float(np.mean(a)) - float(np.mean(b)))
    x = np.array(list(meas.values())); n = len(x)
    out = dict(measures=meas, n=n)
    if n < MIN_MEASURES: out.update(result='not readable (fewer than %d monthly measures)' % MIN_MEASURES, t=None, p=None); return out
    t = float(x.mean() / (x.std(ddof=1) / math.sqrt(n))) if x.std(ddof=1) > 0 else None
    h1 = [v for m, v in meas.items() if m in months[:len(months) // 2]]; h2 = [v for m, v in meas.items() if m in months[len(months) // 2:]]
    ok = t is not None and t >= T_BAR and h1 and h2 and np.mean(h1) > 0 and np.mean(h2) > 0
    out.update(mean=float(x.mean()), t=t, p=p_one_sided(t, n - 1), half1=float(np.mean(h1)) if h1 else None,
               half2=float(np.mean(h2)) if h2 else None, result='present' if ok else 'not detected')
    return out


def fe_reading(rows, hi, lo, outcome, months, within_type=False, bar=T_BAR, sign=1):
    s = [r for r in rows if r['month'] in months and (hi(r) or lo(r)) and outcome(r) is not None]
    if not s: return dict(n=0, result='not readable (no code-days)', t=None, p=None)
    fe = [r['month'] + ('|' + str(r.get('key_type')) if within_type else '') for r in s]
    b, se, t, n = fe_cluster([outcome(r) for r in s], [1.0 if hi(r) else 0.0 for r in s], fe, [r['code'] for r in s], [r['month'] for r in s])
    if t is None: return dict(n=n, n_hi=sum(1 for r in s if hi(r)), result='not readable (no variation)', t=None, p=None)
    t_s = sign * t
    return dict(n=n, n_hi=sum(1 for r in s if hi(r)), b=b, se=se, t=t, p=p_one_sided(t_s),
                result='present' if t_s >= bar else 'not detected')


def readings(rows, arm='F', asof='9999-12-31', primary_months=PRIMARY_MONTHS, cohort_months=COHORT_MONTHS,
             read_primary=READ_PRIMARY, read_secondary=READ_SECONDARY, external=None, base_rows=None):
    """rows: code-day dicts after outcomes(); only group C, not late, enter any bar."""
    for r in rows + (base_rows or []): r['month'] = r['day'][:7]
    C = [r for r in rows if r['group'] == 'C' and not r['late']]
    rk = f'rating_{arm}'
    wr = lambda r: (None if r['ret252'] is None else float(r['ret252'] <= WRECK))
    wn = lambda r: (None if r['ret252'] is None else float(r['ret252'] >= WINNER))
    ex = lambda r: r['ex20']
    out = dict(arm=arm, asof=asof, family={})
    if asof >= read_primary:
        P = monthly_drift(C, lambda r: r[rk] == 2, lambda r: r[rk] == -2, primary_months)
        P['added_value'] = fe_reading(C, lambda r: r[rk] == 2, lambda r: r[rk] == -2, ex, primary_months, True, T_ADD)
        if P.get('t') is not None and P['added_value'].get('b') is not None:
            P['added_value']['adds'] = bool(np.sign(P['added_value']['b']) == np.sign(P['mean']) and abs(P['added_value']['t']) >= T_ADD)
        out['primary'] = P; out['family']['NEWS-C AI drift'] = P.get('p')
    else: out['primary'] = dict(result=f'no reading before {read_primary}')
    if asof >= read_secondary:
        for nm, hi, ylab, oc in (('secondary_A_wrecks', -2, 'wreck', wr), ('secondary_B_winners', 2, 'winner', wn)):
            R = fe_reading(C, lambda r, h=hi: r[rk] == h, lambda r: r[rk] == 0, oc, cohort_months)
            R['added_value'] = fe_reading(C, lambda r, h=hi: r[rk] == h, lambda r: r[rk] == 0, oc, cohort_months, True, T_ADD)
            if R.get('b') is not None and R['added_value'].get('b') is not None:
                R['added_value']['adds'] = bool(np.sign(R['added_value']['b']) == np.sign(R['b']) and abs(R['added_value']['t']) >= T_ADD)
            out[nm] = R; out['family'][f'NEWS-C AI {ylab}s'] = R.get('p')
    else:
        out['secondary_A_wrecks'] = out['secondary_B_winners'] = dict(result=f'no reading before {read_secondary}')
    # baselines, read the same way (group C, not late)
    BC = [r for r in (base_rows or []) if r['group'] == 'C' and not r['late']]
    out['baselines'] = {}
    specs = [('KEY', lambda r: r.get('key_rating') == 2, lambda r: r.get('key_rating') == -2, lambda r: r.get('key_rating') == 0, 1),
             ('RAISE', lambda r: r.get('RAISE') == 1, lambda r: r.get('RAISE') == 0, None, -1),
             ('HALT', lambda r: r.get('HALT') == 1, lambda r: r.get('HALT') == 0, None, -1),
             ('DIR', lambda r: r.get('DIR') == 1, lambda r: r.get('DIR') == 0, None, 1)]
    for nm, a, b, z, sg in specs:
        res = {}
        if asof >= read_primary:
            res['drift'] = monthly_drift(BC, a, b, primary_months, sign=sg)
            out['family'][f'{nm} drift'] = res['drift'].get('p')
        if asof >= read_secondary:
            if nm == 'KEY':
                res['wrecks'] = fe_reading(BC, b, z, wr, cohort_months); res['winners'] = fe_reading(BC, a, z, wn, cohort_months)
            else:
                flag = a; none = b
                res['wrecks'] = fe_reading(BC, flag, none, wr, cohort_months, sign=(1 if sg < 0 else -1))
                res['winners'] = fe_reading(BC, flag, none, wn, cohort_months, sign=(1 if sg > 0 else -1))
            out['family'][f'{nm} wrecks'] = res['wrecks'].get('p'); out['family'][f'{nm} winners'] = res['winners'].get('p')
        out['baselines'][nm] = res or dict(result='no reading yet')
    for k, v in (external or {}).items(): out['family'][k] = v
    out['bh_10pct'] = bh(out['family']) if out['family'] else {}
    out['descriptive'] = describe(rows, arm)
    return out


def describe(rows, arm):
    d = dict(code_days=len(rows), late=sum(r['late'] for r in rows),
             by_group={g: sum(1 for r in rows if r['group'] == g) for g in ('C', 'H')}, by_month={})
    for r in rows:
        m = d['by_month'].setdefault(r['day'][:7], {str(k): 0 for k in (-2, -1, 0, 1, 2)})
        if r.get(f'rating_{arm}') is not None: m[str(r[f'rating_{arm}'])] += 1
    hold = [r for r in rows if r['group'] == 'H' and r.get('ex20') is not None]
    d['holdings_outside_bandC'] = dict(n=len(hold), note='reported separately, never in a bar',
                                       mean_ex20_by_rating={str(k): (float(np.mean([r['ex20'] for r in hold if r.get(f'rating_{arm}') == k]))
                                                                     if any(r.get(f'rating_{arm}') == k for r in hold) else None) for k in (-2, -1, 0, 1, 2)})
    al = [r['already'] for r in rows if r.get('already') is not None]
    d['already_in_price_mean'] = float(np.mean(al)) if al else None
    d['models'] = sorted({str(r.get('model')) for r in rows})
    return d


# ---------------------------------------------------------------- loading the record
def load(newsc, ledger_path):
    import fwd_ledger as L
    L.LED = ledger_path; es = L.entries(); L.verify()
    led = {e['asof']: e for e in es if e.get('kind') == 'info_news'}
    rows, base, rec, bandc, bad = [], [], {}, {}, []
    for day, e in sorted(led.items()):
        od = f'{newsc}/{day}'
        try:
            def chk(fn, key):
                with open(f'{od}/{fn}', 'rb') as f: b = f.read()
                if hashlib.sha256(b).hexdigest() != e[key]: raise ValueError(f'{fn} hash differs from the ledger')
                return [json.loads(l) for l in b.decode().splitlines() if l.strip()]
            cd = chk('codeday.jsonl', 'codeday_sha256'); bl = chk('baselines.jsonl', 'baselines_sha256')
            with open(f'{od}/manifest.json', 'rb') as f: mb = f.read()
            if hashlib.sha256(mb).hexdigest() != e['manifest_sha256']: raise ValueError('manifest hash differs from the ledger')
        except Exception as ex:
            bad.append(f'{day}: {ex}'); continue
        rec[day] = e['recorded_utc']; bandc[day] = json.loads(mb)['bandC_codes']
        rows += cd
        for b in bl: b['model'] = e['model']['reported_id']
        base += bl
    return rows, base, rec, bandc, bad


# ---------------------------------------------------------------- big-drop log (AMENDMENT_info_NEWSC_drops_v1.md)
DROPS_H = (21, 63, 126, 252)
DROPS_L = {21: 1, 63: 3, 126: 6, 252: 12}            # lag months of the clustered variance (PREREG s3: L = horizon in months)
DROPS_MIN_EVENTS, DROPS_READ = 100, '2029-12-01'
DROPS_INDEX = 'A200'
DROPS_ENTRY_WITHIN = 5
DROPS_BAR_T = 2.0
KW_CLASSES = ('temporary', 'fundamental', 'other-news', 'no-news')


def load_drops(newsc, ledger_path):
    """on-time and late event rows of the info_drops ledger entries; files are hash-checked against the ledger"""
    import fwd_ledger as L
    L.LED = ledger_path; es = L.entries(); L.verify()
    rows, bad = [], []
    for e in sorted((e for e in es if e.get('kind') == 'info_drops'), key=lambda e: e['asof']):
        od = f"{newsc}/{e['asof']}"
        try:
            with open(od + '/drops.jsonl', 'rb') as f: db = f.read()
            with open(od + '/drops_labels.jsonl', 'rb') as f: lb = f.read()
            if hashlib.sha256(db).hexdigest() != e['drops_sha256'] or hashlib.sha256(lb).hexdigest() != e['labels_sha256']:
                raise ValueError('drops.jsonl / drops_labels.jsonl hash differs from the ledger')
        except Exception as ex:
            bad.append(f"{e['asof']}: {ex}"); continue
        ev = {x['id']: x for x in (json.loads(l) for l in db.decode().splitlines() if l.strip())}
        for x in (json.loads(l) for l in lb.decode().splitlines() if l.strip()):
            r = dict(ev[x['id']]); r.update(rater=x['rater'], cause_rater=x['cause_rater'], late=int(not e['on_time']),
                                            recorded_utc=e['recorded_utc'], month=e['asof'][:7])
            rows.append(r)
    return rows, bad


def drops_outcomes(rows, mk):
    """adds entry, ret/idx/ex per horizon, recovered, fell20, fell50 (None while not yet observable)"""
    for r in rows:
        i = bisect.bisect_left(mk.ss, r['day'])
        r['entry'] = None
        for k in range(i + 1, min(i + 1 + DROPS_ENTRY_WITHIN, len(mk.ss))):
            if mk.ss[k] > mk.asof: break
            m = mk.day(mk.ss[k])
            if m['close'].get(r['code']) and m['vol'].get(r['code'], 0) > 0: r['entry'] = k; break
        for h in DROPS_H: r[f'ret{h}'] = r[f'idx{h}'] = r[f'ex{h}'] = None
        r['recovered'] = r['fell20'] = r['fell50'] = None
        if r['entry'] is None: continue
        ie = r['entry']; R = track(mk, ie, r['code'], DROPS_H); X = track(mk, ie, DROPS_INDEX, DROPS_H)
        for h in DROPS_H:
            r[f'ret{h}'], r[f'idx{h}'] = R[h], X[h]
            r[f'ex{h}'] = None if R[h] is None or X[h] is None else R[h] - X[h]
        end = i + 252
        if end >= len(mk.ss) or mk.ss[end] > mk.asof: continue
        q, rec, low = 1.0, False, None
        pe = mk.day(mk.ss[ie])['close'][r['code']]; qe = None
        for k in range(i + 1, end + 1):
            m = mk.day(mk.ss[k]); sp = m['split'].get(r['code'])
            if sp and sp > 0: q *= sp
            if k == ie: qe = q
            c = m['close'].get(r['code'])
            if c is None: continue
            if q * c >= r['close_prev']: rec = True                          # close_prev is in D-1 shares; q converts back
            if k > ie:
                rel = (q / qe) * c / pe
                low = rel if low is None else min(low, rel)
        r['recovered'] = int(rec); r['fell20'] = int(low is not None and low <= 0.80); r['fell50'] = int(low is not None and low <= 0.50)
    return rows


def _months(ms):
    a, b = min(ms), max(ms); y, m = int(a[:4]), int(a[5:7]); out = []
    while f'{y}-{m:02d}' <= b:
        out.append(f'{y}-{m:02d}'); m += 1
        if m == 13: y, m = y + 1, 1
    return out


def _hac(score, months, lags, denom):
    """[sum S_m^2 + 2 sum_l (1 - l/(L+1)) sum_m S_m S_{m-l}] / denom^2, S_m = score summed by calendar month (empty months 0)"""
    allm = _months(months); ix = {m: k for k, m in enumerate(allm)}; Sm = np.zeros(len(allm))
    for s_, m in zip(score, months): Sm[ix[m]] += s_
    v = float(Sm @ Sm)
    for l in range(1, lags + 1): v += 2 * (1 - l / (lags + 1)) * float(Sm[l:] @ Sm[:-l]) if l < len(Sm) else 0.0
    return v / denom ** 2


def clustered_mean(x, months, lags):
    """research_dip PREREG s3: mean, SE (month-clustered, lag-weighted), t"""
    x = np.asarray(x, float); n = len(x)
    if n < 2: return dict(n=n, mean=(float(x.mean()) if n else None), t=None)
    v = _hac(x - x.mean(), months, lags, n)
    se = math.sqrt(v) if v > 0 else None
    return dict(n=n, mean=float(x.mean()), median=float(np.median(x)), share_pos=float((x > 0).mean()), se=se,
                t=(float(x.mean() / se) if se else None))


def clustered_diff(y, d, months, lags):
    """OLS of y on a 0/1 dummy d: b = mean(d=1) - mean(d=0); HAC by month as above"""
    y, d = np.asarray(y, float), np.asarray(d, float)
    if d.sum() < 1 or (1 - d).sum() < 1: return dict(n1=int(d.sum()), n0=int((1 - d).sum()), b=None, t=None)
    dc = d - d.mean(); b = float(dc @ (y - y.mean()) / (dc @ dc)); e = y - y.mean() - b * dc
    v = _hac(dc * e, months, lags, float(dc @ dc)); se = math.sqrt(v) if v > 0 else None
    return dict(n1=int(d.sum()), n0=int((1 - d).sum()), b=b, se=se, t=(b / se if se else None))


def drops_reading(rows, mk, asof, read_from=DROPS_READ, min_events=DROPS_MIN_EVENTS):
    ok = [r for r in rows if not r['late']]
    head = dict(asof=asof, on_time_events=len(ok), late_events=len(rows) - len(ok),
                by_cause_kw={c: sum(1 for r in ok if r['cause_kw'] == c) for c in KW_CLASSES},
                by_cause_rater={c: sum(1 for r in ok if r['cause_rater'] == c) for c in KW_CLASSES})
    if asof < read_from or len(ok) < min_events:
        head['result'] = (f'no reading: needs at least {min_events} on-time events and {read_from} (whichever is later); '
                          f'{len(ok)} on-time events so far. No return is computed before then.')
        return head
    mk.asof = asof; drops_outcomes(ok, mk)
    head['no_entry_within_5_sessions'] = sum(1 for r in ok if r['entry'] is None)
    tab = {}
    for clf, key in (('keyword (primary)', 'cause_kw'), ('rater (secondary)', 'cause_rater')):
        tab[clf] = {}
        for c in ('all',) + KW_CLASSES:
            g = [r for r in ok if c == 'all' or r[key] == c]
            row = {}
            for h in DROPS_H:
                s = [r for r in g if r[f'ex{h}'] is not None]
                row[f'{h}s_excess'] = clustered_mean([r[f'ex{h}'] for r in s], [r['month'] for r in s], DROPS_L[h]) if s else dict(n=0)
            z = [r for r in g if r['recovered'] is not None]
            row['recovered_252'] = (float(np.mean([r['recovered'] for r in z])) if z else None)
            row['fell20_252'] = (float(np.mean([r['fell20'] for r in z])) if z else None)
            row['fell50_252'] = (float(np.mean([r['fell50'] for r in z])) if z else None)
            row['n'] = len(g); tab[clf][c] = row
        tf = [r for r in ok if r[key] in ('temporary', 'fundamental') and r['ex252'] is not None]
        tab[clf]['temporary_minus_fundamental_252s'] = clustered_diff([r['ex252'] for r in tf], [r[key] == 'temporary' for r in tf],
                                                                      [r['month'] for r in tf], 12) if tf else dict(b=None, t=None)
    head['tables'] = tab
    k = tab['keyword (primary)']; T = k['temporary']['252s_excess']; D = k['temporary_minus_fundamental_252s']
    a1 = T.get('n', 0) >= 2 and T.get('mean') is not None and T['mean'] > 0 and T.get('t') is not None and T['t'] >= DROPS_BAR_T
    a2 = D.get('b') is not None and D['b'] > 0
    head['bar'] = dict(temporary_12m_excess_positive_t_ge_2=bool(a1), temporary_beats_fundamental_12m=bool(a2),
                       result=('present: earns at most a separately pre-registered paper-line proposal' if a1 and a2 else 'not detected'),
                       note='keyword classifier is primary; the rater is reported, never a second chance at the bar')
    return head


def drops_sessions(end='2035-12-31'):
    """ASX sessions to `end` (paper_lib.sessions() stops at 2028-12-31, before the Dec 2029 reading; v1 code is left unchanged)"""
    import exchange_calendars as xc
    return [str(x.date()) for x in xc.get_calendar('XASX', start='2014-01-01', end=end).sessions]


def drops_main(a):
    import fwd_ledger as L
    import paper_lib as P
    rows, bad = load_drops(a.newsc, a.ledger or L.LED)
    mk = Market(drops_sessions(), P.load_day)
    R = drops_reading(rows, mk, a.asof); R['excluded_days'] = bad
    if 'tables' in R:
        out = a.out or f'{a.newsc}/readings/{a.asof}'
        os.makedirs(out, exist_ok=True)
        with open(f'{out}/drops_reading.json', 'w') as f: json.dump(R, f, indent=1, sort_keys=True, default=str)
        print(json.dumps(R['bar'], indent=1))
    else:
        print('drops:', R['result'])
        print('drops counts (descriptive, no returns):', json.dumps(dict(by_cause_kw=R['by_cause_kw'], by_cause_rater=R['by_cause_rater'],
                                                                           late_events=R['late_events'], excluded_days=bad)))
    print('INFORMATION ONLY. The big-drop log feeds no line; this reading never changes the classifier, the rubric or any rule.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--asof', default=datetime.now(SYD).strftime('%Y-%m-%d'))
    ap.add_argument('--external', default='', help='EST-C=p,DIL-C=p (one-sided p-values from their own readings)')
    ap.add_argument('--newsc', default=NEWSC); ap.add_argument('--ledger', default=None); ap.add_argument('--out', default=None)
    ap.add_argument('--arm', default='F', choices=['F', 'H'])
    ap.add_argument('--drops', action='store_true', help='the big-drop log reading (AMENDMENT_info_NEWSC_drops_v1.md) instead')
    a = ap.parse_args()
    if a.drops: return drops_main(a)
    import fwd_ledger as L
    rows, base, rec, bandc, bad = load(a.newsc, a.ledger or L.LED)
    mk = bulk_market(); mk.asof = a.asof
    outcomes(rows, mk, rec, bandc); outcomes(base, mk, rec, bandc)
    ext = {k: float(v) for k, v in (x.split('=') for x in a.external.split(',') if x.strip())}
    R = readings(rows, a.arm, a.asof, external=ext, base_rows=base); R['excluded_days'] = bad
    out = a.out or f'{a.newsc}/readings/{a.asof}'
    assert os.path.abspath(out).startswith(os.path.abspath(a.newsc) + '/readings') or a.out, 'readings only'
    os.makedirs(out, exist_ok=True)
    with open(f'{out}/reading.json', 'w') as f: json.dump(R, f, indent=1, sort_keys=True, default=str)
    print(json.dumps({k: (v.get('result') if isinstance(v, dict) else v) for k, v in R.items() if k not in ('descriptive', 'family', 'baselines')}, indent=1))
    print('INFORMATION ONLY. This reading never changes the rubric, the prompt or any NEWS-C rule.')


if __name__ == '__main__':
    main()
