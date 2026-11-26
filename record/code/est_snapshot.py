# INFORMATION ONLY - point-in-time analyst-estimate snapshots for the Big Wins paper universe.
# Makes no trading decision, reads the paper state read-only (only the ranks keys = current ASX-300 paper universe), writes nothing
# the paper job reads.  EODHD data: private, non-commercial use.  The proxy injects the EODHD key (same Client as fwd_download.py).
#   python3 -I est_snapshot.py [--date YYYY-MM-DD] [--min-left 15000] [--per-min 280]
# Output: data/estimates_pit/est_YYYY-MM-DD.json.gz (one per day; skipped if it exists) + a line in data/estimates_pit/est_manifest.csv.
# Cost: one fundamentals call per ticker = 10 API credits each (about 300 x 10 = 3,000 credits per run).
# Band C (AMENDMENT_shadow_sidelines_v1.md s3, ledger seq 91): after the top-300 file, the same call for the codes with traded-value rank 301-600
# (estimates_pit/bandC_universe.json, written by the paper job at each month-end) with SharesStats + outstandingShares::quarterly added
# (shares-on-issue snapshot): data/estimates_pit/est_C_YYYY-MM-DD.json.gz (skipped if it exists) + est_C_manifest.csv; about 3,000 credits,
# same 15,000-credit floor, refuses a list of more than 320 codes. The top-300 snapshot, its filter, file and manifest are unchanged.
import os, sys, json, gzip, time, hashlib, argparse, datetime as dt
from concurrent.futures import ThreadPoolExecutor
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
sys.path.insert(0, S + '/data_foundation/code/eodhd')
from client import Client, COST
STATE = S + '/bigwins_forward/out/paper_state/state.json'
OUT = S + '/bigwins_forward/data/estimates_pit'
MAN = OUT + '/est_manifest.csv'
FILTER = 'General::Code,Highlights,Earnings::Trend,Earnings::History,AnalystRatings'
HL_KEYS = ['EPSEstimateCurrentYear', 'EPSEstimateNextYear', 'EPSEstimateCurrentQuarter', 'EPSEstimateNextQuarter',
           'WallStreetTargetPrice', 'EarningsShare', 'DilutedEpsTTM', 'PERatio', 'PEGRatio', 'MostRecentQuarter', 'MarketCapitalization']
CREDITS = 10
COST['fundamentals'] = CREDITS

def today_syd():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo('Australia/Sydney')).date().isoformat()
    except Exception:
        return dt.date.today().isoformat()

def universe():
    st = json.load(open(STATE))                       # read-only
    return sorted({c.split('#')[0] for c in st['ranks']})

def credits_left(cli):
    u = cli.user() or {}
    return int(u.get('dailyRateLimit', 0)) + int(u.get('extraLimit', 0) or 0) - int(u.get('apiRequests', 0)), u.get('apiRequests')

def keep(js):
    hl = js.get('Highlights') or {}
    hist = js.get('Earnings::History') or {}
    hist8 = dict(sorted(hist.items(), reverse=True)[:8]) if isinstance(hist, dict) else {}
    ar = js.get('AnalystRatings')
    return dict(code=js.get('General::Code'), trend=js.get('Earnings::Trend') or {}, history8=hist8,
                highlights={k: hl.get(k) for k in HL_KEYS if k in hl}, analyst_ratings=(ar if ar else None))

def run(date=None, min_left=15000, per_min=280, workers=4, log=print):
    date = date or today_syd()
    os.makedirs(OUT, exist_ok=True)
    fp = f'{OUT}/est_{date}.json.gz'
    if os.path.exists(fp):
        log(f'{fp} exists; skipping (idempotent)'); return None
    t0 = time.time()
    uni = universe()
    cli = Client(OUT + '/_client', per_min=per_min, daily_budget=len(uni) * CREDITS + 50, log=log)
    left, used = credits_left(cli)
    need = len(uni) * CREDITS
    log(f'{date}: {len(uni)} tickers, cost {need} credits; EODHD credits left today {left} (used {used})')
    if left - need < min_left:
        log(f'ABORT: would leave {left - need} < {min_left} credits'); return None
    res, fail = {}, []
    def one(code):
        try:
            http, js = cli.get(f'fundamentals/{code}.AU', {'filter': FILTER}, 'fundamentals', code + '.AU', save=False)
        except Exception as e:
            return code, None, f'{type(e).__name__}'
        if http != 200 or not isinstance(js, dict):
            return code, None, f'http {http}'
        return code, dict(keep(js), fetched_utc=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')), None
    with ThreadPoolExecutor(workers) as ex:
        for code, rec, err in ex.map(one, uni):
            if rec is None: fail.append([code, err])
            else: res[code] = rec
    n_trend = sum(1 for r in res.values() if any((v or {}).get('earningsEstimateAvg') not in (None, '', '0', '0.0000')
                                                 for v in (r['trend'].values() if isinstance(r['trend'], dict) else [])))
    doc = dict(note='INFORMATION ONLY - point-in-time EODHD analyst estimates; no trading decision; EODHD data private, non-commercial',
               date=date, created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), filter=FILTER, universe_n=len(uni),
               ok=len(res), failed=fail, with_trend_estimates=n_trend, credits_per_call=CREDITS, data=res)
    tmp = fp + '.tmp'
    with open(tmp, 'wb') as f: f.write(gzip.compress(json.dumps(doc, sort_keys=True).encode(), mtime=0))
    os.replace(tmp, fp)
    h = hashlib.sha256(open(fp, 'rb').read()).hexdigest()
    new = not os.path.exists(MAN)
    with open(MAN, 'a') as f:
        if new: f.write('date,created_utc,n_universe,n_ok,n_failed,n_with_trend,bytes,credits,sha256\n')
        f.write(f"{date},{doc['created_utc']},{len(uni)},{len(res)},{len(fail)},{n_trend},{os.path.getsize(fp)},{cli.spent},{h}\n")
    left2, _ = credits_left(cli)
    log(f'wrote {fp} ({os.path.getsize(fp)} bytes) ok {len(res)} failed {len(fail)} with trend estimates {n_trend}; '
        f'credits spent {cli.spent}; left {left2}; {time.time() - t0:.0f}s')
    if fail: log('failed:', fail[:20])
    return doc

# ---------------------------------------------------------------- band C (ranks 301-600): estimates + shares on issue (seq 91)
BANDC_LIST = OUT + '/bandC_universe.json'
MAN_C = OUT + '/est_C_manifest.csv'
FILTER_C = FILTER + ',SharesStats,outstandingShares::quarterly'
MAX_C = 320
NQ = 16                                                # latest 16 quarterly shares-on-issue entries kept

def universe_c():
    doc = json.load(open(BANDC_LIST))
    codes = sorted(set(doc['codes']))
    return codes, doc.get('asof'), hashlib.sha256(open(BANDC_LIST, 'rb').read()).hexdigest()

def keep_c(js):
    q = js.get('outstandingShares::quarterly') or {}
    q = sorted((v for v in (q.values() if isinstance(q, dict) else q) if isinstance(v, dict)), key=lambda v: str(v.get('dateFormatted')), reverse=True)[:NQ]
    return dict(keep(js), shares_stats=(js.get('SharesStats') or None), outstanding_quarterly=q)

def run_c(date=None, min_left=15000, per_min=280, workers=4, log=print, codes=None):
    date = date or today_syd()
    os.makedirs(OUT, exist_ok=True)
    fp = f'{OUT}/est_C_{date}.json.gz'
    if os.path.exists(fp):
        log(f'band C: {fp} exists; skipping (idempotent)'); return None
    if not os.path.exists(BANDC_LIST):
        log(f'band C: SKIPPED, no list {BANDC_LIST}'); return None
    uni, lasof, lsha = universe_c()
    if codes is not None: uni = sorted(set(uni) & set(codes))                     # tests only
    if len(uni) > MAX_C:
        log(f'band C: ABORT, list has {len(uni)} codes (> {MAX_C})'); return None
    t0 = time.time()
    cli = Client(OUT + '/_client', per_min=per_min, daily_budget=len(uni) * CREDITS + 50, log=log)
    left, used = credits_left(cli)
    need = len(uni) * CREDITS
    if left - need < min_left:
        log(f'band C: ABORT, {len(uni)} tickers would leave {left - need} < {min_left} credits'); return None
    res, fail = {}, []
    def one(code):
        try:
            http, js = cli.get(f'fundamentals/{code}.AU', {'filter': FILTER_C}, 'fundamentals', code + '.AU', save=False)
        except Exception as e:
            return code, None, f'{type(e).__name__}'
        if http != 200 or not isinstance(js, dict):
            return code, None, f'http {http}'
        return code, dict(keep_c(js), fetched_utc=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')), None
    with ThreadPoolExecutor(workers) as ex:
        for code, rec, err in ex.map(one, uni):
            if rec is None: fail.append([code, err])
            else: res[code] = rec
    n_trend = sum(1 for r in res.values() if any((v or {}).get('earningsEstimateAvg') not in (None, '', '0', '0.0000')
                                                 for v in (r['trend'].values() if isinstance(r['trend'], dict) else [])))
    n_sh = sum(1 for r in res.values() if r['outstanding_quarterly'])
    doc = dict(note='INFORMATION ONLY - point-in-time EODHD analyst estimates and shares on issue, band C (ranks 301-600); no trading decision; EODHD data private, non-commercial',
               date=date, created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), filter=FILTER_C, universe_n=len(uni), list_asof=lasof, list_sha256=lsha,
               ok=len(res), failed=fail, with_trend_estimates=n_trend, with_shares_history=n_sh, credits_per_call=CREDITS, data=res)
    tmp = fp + '.tmp'
    with open(tmp, 'wb') as f: f.write(gzip.compress(json.dumps(doc, sort_keys=True).encode(), mtime=0))
    os.replace(tmp, fp)
    h = hashlib.sha256(open(fp, 'rb').read()).hexdigest()
    new = not os.path.exists(MAN_C)
    with open(MAN_C, 'a') as f:
        if new: f.write('date,created_utc,n_universe,n_ok,n_failed,n_with_trend,n_with_shares,bytes,credits,list_asof,list_sha256,sha256\n')
        f.write(f"{date},{doc['created_utc']},{len(uni)},{len(res)},{len(fail)},{n_trend},{n_sh},{os.path.getsize(fp)},{cli.spent},{lasof},{lsha},{h}\n")
    left2, _ = credits_left(cli)
    log(f'band C (ranks 301-600): wrote {fp} ok {len(res)} of {len(uni)} failed {len(fail)} with trend estimates {n_trend} with shares history {n_sh}; '
        f'credits spent {cli.spent}; left {left2}; {time.time() - t0:.0f}s' + (f'; failed: {fail[:10]}' if fail else ''))
    return doc

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--date'); ap.add_argument('--min-left', type=int, default=15000)
    ap.add_argument('--per-min', type=int, default=280); a = ap.parse_args()
    run(a.date, a.min_left, min(a.per_min, 280))
    try: run_c(a.date, a.min_left, min(a.per_min, 280))
    except Exception as e: print(f'band C (ranks 301-600) snapshot FAILED: {type(e).__name__}: {e}'); sys.exit(1)
