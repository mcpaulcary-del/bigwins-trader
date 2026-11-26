# INFORMATION ONLY - point-in-time analyst-estimate snapshots for the Big Wins paper universe.
# Makes no trading decision, reads the paper state read-only (only the ranks keys = current ASX-300 paper universe), writes nothing
# the paper job reads.  EODHD data: private, non-commercial use.  The proxy injects the EODHD key (same Client as fwd_download.py).
#   python3 -I est_snapshot.py [--date YYYY-MM-DD] [--min-left 15000] [--per-min 280]
# Output: data/estimates_pit/est_YYYY-MM-DD.json.gz (one per day; skipped if it exists) + a line in data/estimates_pit/est_manifest.csv.
# Cost: one fundamentals call per ticker = 10 API credits each (about 300 x 10 = 3,000 credits per run).
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

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--date'); ap.add_argument('--min-left', type=int, default=15000)
    ap.add_argument('--per-min', type=int, default=280); a = ap.parse_args()
    run(a.date, a.min_left, min(a.per_min, 280))
