# Big Wins forward PAPER record -- information readings EST-C and DIL-C on band C (AMENDMENT_shadow_sidelines_v1.md s1-s3, ledger seq 91).
# INFORMATION ONLY: no book, no order, no decision of any line uses this; never evidence for or against the main line.
#   EST-C  the registered EST revision signal (AMENDMENT_info_EST_revisions.md) on ranks 301-600 with >= 2 analysts: at each month-end M,
#          top third minus bottom third of next-month total return. Bar: 24 measures, t >= 2, both 12-month halves positive.
#   DIL-C  band-C names (paper_emg2.table C) whose shares on issue rose > 20% in 12 months (vendor quarterly history in the band-C snapshot):
#          flagged minus unflagged total return at 6 and 12 month-ends. Bar: both negative, Newey-West t <= -2 (lags 5 / 11) at 24 months.
#   Band-C list for the snapshot job (est_snapshot.py): codes with traded-value rank 301-600 in the month-end table -> estimates_pit/bandC_universe.json.
# Reads the band-C snapshots read-only (SHA-256 checked against est_C_manifest.csv) and the paper bulk files; vendor values stay in
# bigwins_forward/data (per-code readings in data/info_c/); the state (STATE_DIR/info_c_state.json) holds code lists, prices and aggregates only.
# PAPER ONLY: no real money, no broker orders, the AI never places trades. Idempotent and resumable.
import os, json, gzip, math, hashlib, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_emg2 as EM

IC_START = '2026-11-30'
EST_DIR = P.DATA_ROOT + '/estimates_pit'
MAN_C = EST_DIR + '/est_C_manifest.csv'
BANDC_LIST = EST_DIR + '/bandC_universe.json'
DATA_OUT = P.DATA_ROOT + '/info_c'
S_LAG = 63; NEAR = 5; MIN_AN = 2; MIN_EST = 30                                  # EST definitions (+ EST-C minimum of 30 codes)
DIL_G = 0.20; DIL_H = (6, 12); DIL_MIN_F, DIL_MIN_U = 5, 20; DIL_TOL = 62
TAG = 'information only (AMENDMENT_shadow_sidelines_v1.md); no book, no trades; never evidence for or against the main line'


def state_path(): return P.STATE_DIR + '/info_c_state.json'
def month_end(d): return P.is_month_end(d)                                     # (tests patch this name only)

def init_state():
    return dict(record='Big Wins forward paper record -- information readings EST-C and DIL-C on band C (information only)', amendment='AMENDMENT_shadow_sidelines_v1.md',
                start=IC_START, last_processed=P.prev_session(IC_START), cohorts=[], months=[], est=[], dil6=[], dil12=[])

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- band-C list for the snapshot job
def write_list(R, d, src):
    """Codes with traded-value rank 301-600 in table R (class rule of R; LICs/funds out), best rank first. Rewritten only by a later table."""
    rows = sorted((r for r in R['rows'].values() if r.get('tv_rank') is not None and 301 <= r['tv_rank'] <= 600), key=lambda r: r['tv_rank'])
    codes = [r['code'] for r in rows]
    if os.path.exists(BANDC_LIST):
        old = json.load(open(BANDC_LIST))
        if old.get('asof', '') > d: return P.L.sha(BANDC_LIST)
    doc = dict(note='INFORMATION ONLY - band-C code list (traded-value ranks 301-600) for est_snapshot.py; AMENDMENT_shadow_sidelines_v1.md s3',
               asof=d, class_rule=R['class_rule'], source=src, n=len(codes), codes=codes)
    os.makedirs(EST_DIR, exist_ok=True); tmp = BANDC_LIST + '.tmp'
    json.dump(doc, open(tmp, 'w'), indent=0); os.replace(tmp, BANDC_LIST)
    return P.L.sha(BANDC_LIST)


# ---------------------------------------------------------------- snapshots (read-only)
def _manifest():
    if not os.path.exists(MAN_C): return {}
    t = pd.read_csv(MAN_C, dtype=str)
    return dict(zip(t['date'], t['sha256']))

def snapshot_for(d):
    """(file date, data) of the band-C snapshot for date d: the file dated d, else the latest earlier within 5 ASX sessions; hash-checked."""
    if not os.path.isdir(EST_DIR): return None, None
    ds = sorted(f[6:16] for f in os.listdir(EST_DIR) if f.startswith('est_C_') and f.endswith('.json.gz') and f[6:16] <= d)
    if not ds: return None, None
    f = ds[-1]
    if f != d and len(P.sessions_between(f, d)) > NEAR: return None, None
    fp = f'{EST_DIR}/est_C_{f}.json.gz'
    if _manifest().get(f) != hashlib.sha256(open(fp, 'rb').read()).hexdigest(): return None, None       # hash mismatch = missing
    return f, json.load(gzip.open(fp))['data']

def _num(x):
    try: v = float(x)
    except (TypeError, ValueError): return None
    return v if math.isfinite(v) else None

def cy_estimate(rec):
    """(FY label, estimate, analyst count) of the current-year ('0y') trend entry with the latest date, else None."""
    t = rec.get('trend')
    if not isinstance(t, dict): return None
    e = [v for v in t.values() if isinstance(v, dict) and v.get('period') == '0y' and v.get('date')]
    if not e: return None
    e = max(e, key=lambda v: v['date'])
    return e['date'], _num(e.get('earningsEstimateAvg')), _num(e.get('earningsEstimateNumberOfAnalysts'))

def shares_growth(rec, M):
    """DIL-C g = N1 / N0 - 1 from outstandingShares::quarterly: N1 latest dateFormatted <= M, N0 nearest to 365 days before N1 (+-62 days, tie earlier)."""
    q = rec.get('outstanding_quarterly') or []
    pts = sorted((str(x.get('dateFormatted'))[:10], _num(x.get('shares'))) for x in q if isinstance(x, dict) and x.get('dateFormatted'))
    pts = [(a, v) for a, v in pts if v is not None and v > 0 and a <= M]
    if not pts: return None
    d1, n1 = pts[-1]; t1 = pd.Timestamp(d1); tgt = t1 - pd.Timedelta(days=365)
    c = [(abs((pd.Timestamp(a) - tgt).days), a, v) for a, v in pts[:-1] if abs((pd.Timestamp(a) - tgt).days) <= DIL_TOL]
    if not c: return None
    _, _, n0 = min(c)
    return n1 / n0 - 1


def close_on_or_before(day):
    """raw closes of the last ASX session on or before calendar day `day` (bulk file), else {}."""
    s = [x for x in P.sessions() if x <= day]
    m = P.load_day(s[-1]) if s else None
    return m['close'] if m else {}


# ---------------------------------------------------------------- month-end: new cohort
def new_cohort(d, mkt, log):
    D, blocked, src = EM.get_bundle(d, log); R = EM.table(D); del D
    lsha = write_list(R, d, f'paper_emg2.table on the {d} month-end bundle ({src})')
    cl = mkt['close']; per = {}; info = dict(asof=d, list_sha256=lsha, list_n=sum(1 for r in R['rows'].values() if r.get('tv_rank') and 301 <= r['tv_rank'] <= 600))
    # EST-C
    fM, snapM = snapshot_for(d); ss = P.sessions(); S = ss[ss.index(d) - S_LAG]; fS, snapS = snapshot_for(S)
    sig = {}
    if snapM is not None and snapS is not None:
        c0 = close_on_or_before(fS)
        for code, rec in snapM.items():
            a = cy_estimate(rec); b = cy_estimate(snapS[code]) if code in snapS else None
            if a is None or b is None: continue
            (fy1, e1, n1), (fy0, e0, n0) = a, b
            if e1 is None or e0 is None or n1 is None or n0 is None or n1 < MIN_AN or n0 < MIN_AN or fy1 != fy0: continue
            p0 = c0.get(code)
            if p0 is None or p0 <= 0: continue
            sig[code] = (e1 - e0) / p0
    universe = [c for c, r in (snapM or {}).items() if isinstance(r.get('trend'), dict)]
    have = sorted((c for c in sig if c in cl), key=lambda c: (-sig[c], c)); k = len(have) // 3
    est_top, est_bot = (have[:k], have[-k:]) if len(have) >= MIN_EST else ([], [])
    info.update(est_snapshot_M=fM, est_snapshot_S=fS, est_S_session=S, est_universe=len(universe), est_with_signal=len(sig), est_signal_and_close=len(have),
                est_month='recorded' if est_top else f'missing (fewer than {MIN_EST} codes with signal and close)')
    for c in sig: per.setdefault(c, {})['est_signal'] = sig[c]
    # DIL-C
    flg, unf, out = [], [], 0
    for cid in R['C']:
        code = R['rows'][cid]['code']; rec = (snapM or {}).get(code)
        g = shares_growth(rec, d) if rec else None
        if g is None or code not in cl: out += 1; continue
        (flg if g > DIL_G else unf).append(code); per.setdefault(code, {})['dil_g'] = g
    info.update(dil_band_C=len(R['C']), dil_flagged=len(flg), dil_unflagged=len(unf), dil_left_out=out)
    track = {c: [1.0, cl[c], 0.0, cl[c]] for c in sorted(set(est_top) | set(est_bot) | set(flg) | set(unf))}       # [shares, last close, cash, close on M]
    os.makedirs(DATA_OUT, exist_ok=True)
    with open(f'{DATA_OUT}/info_c_{d}.json.gz.tmp', 'wb') as f: f.write(gzip.compress(json.dumps(dict(asof=d, note=TAG, info=info, per_code=per), sort_keys=True).encode(), mtime=0))
    os.replace(f'{DATA_OUT}/info_c_{d}.json.gz.tmp', f'{DATA_OUT}/info_c_{d}.json.gz')
    log('INFO-C', d, f"band-C list {info['list_n']}; EST-C {len(sig)} signals ({info['est_month']}); DIL-C flagged {len(flg)} unflagged {len(unf)} left out {out}")
    return dict(M=d, n_me=0, track=track, est_top=est_top, est_bot=est_bot, dil_f=sorted(flg), dil_u=sorted(unf)), info


def ret(tr, c):
    q, p, cash, p0 = tr[c]; return (q * p + cash) / p0 - 1

def step(s, d, mkt, log):
    out = dict(closed=[])
    for co in s['cohorts']:
        if d <= co['M']: continue
        for c, x in co['track'].items():
            sp = mkt['split'].get(c)
            if sp and sp > 0: x[0] *= sp
            v = mkt['div'].get(c)
            if v: x[2] += x[0] * v
            if c in mkt['close']: x[1] = mkt['close'][c]
    if d >= IC_START and month_end(d):
        keep = []
        for co in s['cohorts']:
            if d <= co['M']: keep.append(co); continue
            co['n_me'] += 1; tr = co['track']
            if co['n_me'] == 1:
                v = (float(np.mean([ret(tr, c) for c in co['est_top']])) - float(np.mean([ret(tr, c) for c in co['est_bot']]))) if co['est_top'] else None
                s['est'].append(dict(M=co['M'], closed=d, n_third=len(co['est_top']), top_minus_bottom=v)); out['closed'].append(['EST-C', co['M'], v])
            if co['n_me'] in DIL_H:
                ok = len(co['dil_f']) >= DIL_MIN_F and len(co['dil_u']) >= DIL_MIN_U
                v = (float(np.mean([ret(tr, c) for c in co['dil_f']])) - float(np.mean([ret(tr, c) for c in co['dil_u']]))) if ok else None
                s[f"dil{co['n_me']}"].append(dict(M=co['M'], closed=d, n_flagged=len(co['dil_f']), n_unflagged=len(co['dil_u']), flagged_minus_unflagged=v))
                out['closed'].append([f"DIL-C {co['n_me']}m", co['M'], v])
            dil = set(co['dil_f']) | set(co['dil_u'])
            if co['n_me'] < max(DIL_H) and dil:                                                     # EST-C is done after one month; DIL-C runs to 12
                co['track'] = {c: x for c, x in tr.items() if c in dil}; keep.append(co)
        s['cohorts'] = keep
        try:
            co, info = new_cohort(d, mkt, log); s['cohorts'].append(co); s['months'].append(info); out['month'] = info
        except Exception as e:
            log('INFO-C', d, 'month-end reading not recorded:', repr(e)); log(traceback.format_exc())
            s['months'].append(dict(asof=d, error=repr(e)[:200])); out['month'] = dict(asof=d, error=repr(e)[:200])
    s['last_processed'] = d
    return out if (out['closed'] or 'month' in out) else None


def run(d, mkt, log):
    """Bring EST-C / DIL-C up to trading day d (after the paper lines, before the bundle is cleared). None before the start."""
    try:
        if d < IC_START: return None
        s = load()
        if s is None: s = init_state(); log('INFO-C state created; first month-end', IC_START)
        evs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('INFO-C', x, 'no bulk file; stops here and resumes on a later run'); break
            e = step(s, x, m, log); save(s)
            if e: evs.append(dict(asof=x, **e))
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), events=evs or None)
    except Exception as e:
        log('INFO-C ERROR (no paper line affected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- readings
def tstat(x):
    x = np.asarray([v for v in x if v is not None], float)
    return None if len(x) < 3 or x.std(ddof=1) == 0 else float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))

def est_reading(s):
    v = [o['top_minus_bottom'] for o in s['est'] if o['top_minus_bottom'] is not None]
    r = dict(n=len(v), mean=(float(np.mean(v)) if v else None), t=tstat(v))
    if len(v) >= 24:
        a, b = v[:12], v[12:24]; t24 = tstat(v[:24])
        r.update(t24=t24, half1=float(np.mean(a)), half2=float(np.mean(b)),
                 verdict='signal present (information only)' if (t24 is not None and t24 >= 2.0 and np.mean(a) > 0 and np.mean(b) > 0) else 'not detected')
    return r

def dil_reading(s):
    r = {}
    for h in DIL_H:
        v = [o['flagged_minus_unflagged'] for o in s[f'dil{h}'] if o['flagged_minus_unflagged'] is not None]
        r[h] = dict(n=len(v), mean=(float(np.mean(v)) if v else None), t_nw=EM.nw_t(v, lag=h - 1))
    return r

def scorecard_rows(d):
    s = load(); rows, md = [], []
    f = lambda x: '' if x is None else f'{x:+.2%}'
    ft = lambda x: '' if x is None else f'{x:+.2f}'
    if s is None:
        md.append(f'| **EST-C** (ranks 301-600, >= 2 analysts) | — | — | {TAG}; first signal month 26 Feb 2027 (band-C snapshots from 24 Nov 2026); top minus bottom third; bar: 24 months, t >= 2, both years positive |')
        md.append(f'| **DIL-C** (band C, shares on issue +20% in 12 months) | — | — | {TAG}; first month-end 30 Nov 2026; flagged minus unflagged at 6 and 12 months; bar: both negative, NW t <= -2 at 24 months |')
        return rows, md, []
    m = next((x for x in reversed(s['months']) if 'error' not in x), None)
    e = est_reading(s); dr = dil_reading(s)
    en = (f"latest month-end {m['asof']}: {m['est_with_signal']} of {m['est_universe']} codes with a signal ({m['est_month']})" if m else 'no month-end yet') + \
         f"; measures {e['n']}, mean top - bottom {f(e['mean'])}, t {ft(e['t'])}" + (f"; 24-month reading: {e['verdict']}" if 'verdict' in e else '; reading when 24 measures exist')
    dn = (f"latest month-end {m['asof']}: flagged {m['dil_flagged']}, unflagged {m['dil_unflagged']}, left out {m['dil_left_out']} of band C {m['dil_band_C']}" if m else 'no month-end yet') + \
         ''.join(f"; {h}m: cohorts {dr[h]['n']}, mean {f(dr[h]['mean'])}, NW t {ft(dr[h]['t_nw'])}" for h in DIL_H)
    rows.append(dict(asof=d, book='EST-C', kind='information only (band C estimates)', note=f'{en}; {TAG}'))
    rows.append(dict(asof=d, book='DIL-C', kind='information only (band C dilution)', note=f'{dn}; {TAG}'))
    md.append(f'| **EST-C** (ranks 301-600, >= 2 analysts) | — | — | {en}; bar: 24 months, t >= 2, both years positive |')
    md.append(f'| **DIL-C** (band C, shares on issue +20% in 12 months) | — | — | {dn}; bar: both negative, NW t <= -2 at 24 months |')
    return rows, md, []
