# Forward paper record: frozen score snapshot at a decision day (rules v1.3 part Q).   python3 -I bw13_snapshot.py <asof> [<asof> ...]
# Uses ONLY data dated on or before <asof> (bw13_prep cuts the panel first; A7 is applied to the file as downloaded).
import sys, os, json, math, hashlib, time, numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'; FW = S + '/bigwins_forward'; REC = FW + '/out/forward_record'
sys.path.insert(0, FW + '/code'); import bw13_prep
DF = S + '/data_foundation/out'
INPUTS = {'eodhd_panel_tr': DF + '/eodhd/panel_tr.pkl', 'eodhd_symbols': DF + '/eodhd/symbols.csv', 'eodhd_manifest': DF + '/eodhd/manifest.tsv',
          'etp_list': S + '/bigwins_lab/data/etp_list.txt', 'asx_listed_companies_2026-11-14': S + '/bigwins_lab/data/ASXListedCompanies.csv',
          'code_bw13_prep': FW + '/code/bw13_prep.py', 'code_bw13_snapshot': FW + '/code/bw13_snapshot.py'}
sha = bw13_prep.sha
def pr(x): return pd.Series(x).rank(pct=True).values
def fmt(v): return '' if (v is None or (isinstance(v, float) and np.isnan(v))) else (f'{v:.10g}' if isinstance(v, float) else str(v))

def table(D, lo, hi, extra_ok=None):
    k = max(D['tabs']); t = D['tabs'][k]; assert D['ME'][k] == len(D['dates']) - 1
    m = (t['vrank'] >= lo) & (t['vrank'] <= hi)
    if extra_ok is not None: m &= extra_ok(t)
    d = {a: v[m] for a, v in t.items()}
    p = np.column_stack([pr(d[c]) for c in ('M1', 'M2', 'M3', 'M5')])
    score = np.where(np.isnan(p).any(1), np.nan, p.mean(1)); ok = ~np.isnan(score)
    order = np.argsort(-np.where(ok, score, -1), kind='stable'); srank = np.full(len(score), np.nan); srank[order[:ok.sum()]] = np.arange(1, ok.sum() + 1)
    return d, p, score, srank, order

def target(d, score, order, n, T, cap=0.25):
    out = []; cnt = {}; c_ = math.ceil(cap * n)
    for j in order:
        if len(out) >= n or np.isnan(score[j]): break
        if not (d['price'][j] >= 0.5) or d['medval'][j] < 100 * T: continue
        s = d['sector'][j]
        if s:
            if cnt.get(s, 0) >= c_: continue
            cnt[s] = cnt.get(s, 0) + 1
        out.append(j)
    return out

def snapshot(asof):
    D = bw13_prep.build(asof, dup_rule='A7b', verbose=False)
    sym = pd.read_csv(DF + '/eodhd/symbols.csv'); name = dict(zip(sym.Code, sym.Name)); cols = D['cols']
    files = {}
    def write(fn, rows, header):
        path = f'{REC}/{fn}'
        with open(path, 'w', newline='\n') as f:
            f.write(','.join(header) + '\n')
            for r in rows: f.write(','.join('"' + fmt(x).replace('"', "'") + '"' if isinstance(x, str) and ',' in x else fmt(x) for x in r) + '\n')
        files[fn] = sha(path)
    # ---- H82: top 300
    d, p, score, srank, order = table(D, 1, 300)
    T25, T100 = 25000 / 10, 100000 / 30
    l25 = set(target(d, score, order, 10, T25)); l100 = set(target(d, score, order, 30, T100))
    rows = []
    for j in range(len(score)):
        e = cols[d['col'][j]]; code = e.split('#')[0]
        rows.append((int(d['vrank'][j]), code, e, name.get(code, ''), float(d['medval'][j]), float(d['price'][j]), int(not np.isnan(d['rawclose'][j])),
                     float(d['M1'][j]), float(d['M2'][j]), float(d['M3'][j]), float(d['M5'][j]), float(p[j, 0]), float(p[j, 1]), float(p[j, 2]), float(p[j, 3]),
                     float(score[j]), (int(srank[j]) if not np.isnan(srank[j]) else None), d['sector'][j] or '', int(j in l25), int(j in l100)))
    hdr = ['tv_rank', 'code', 'company_id', 'name', 'median_traded_value', 'close10', 'traded_on_day', 's1_mom12_1', 's2_mom6', 's3_near_high', 's4_neg_vol',
           'p1', 'p2', 'p3', 'p4', 'score', 'score_rank', 'industry_group', 'in_list_if_review_25k_n10', 'in_list_if_review_100k_n30']
    write(f'scores_top300_{asof}.csv', rows, hdr)
    top = sorted([r for r in rows if r[16] is not None], key=lambda r: r[16])[:15]
    # ---- H101 tracking line universe: ranks 301-1000, median value >= A$50,000, a close ON the day >= A$0.50
    d2, p2, sc2, sr2, or2 = table(D, 301, 1000, lambda t: (t['medval'] >= 50000) & (t['rawclose'] >= 0.50))
    npick = math.ceil(0.10 * int((~np.isnan(sc2)).sum())); pick = set(or2[:npick])
    rows2 = [(int(d2['vrank'][j]), cols[d2['col'][j]].split('#')[0], cols[d2['col'][j]], float(d2['medval'][j]), float(d2['rawclose'][j]), float(sc2[j]),
              (int(sr2[j]) if not np.isnan(sr2[j]) else None), int(j in pick)) for j in range(len(sc2))]
    write(f'scores_h101_{asof}.csv', rows2, ['tv_rank', 'code', 'company_id', 'median_traded_value', 'close', 'score', 'score_rank', 'top_tenth'])
    write(f'dupcodes_{asof}.csv', D['duplog'], ['dropped_old_code', 'kept_code', 'old_code_last_day'])
    i = len(D['dates']) - 1
    man = dict(record='Big Wins forward paper record', rules='v1.3', asof=asof, kind='month-end' if asof in MONTH_ENDS else 'interim (not a decision day)',
               created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), file_first_day=str(D['dates'][0].date()), download_end=D['download_end'],
               duplicate_rule='A7(a) or A7(b)', n_companies_in_file=len(cols), n_ranked=int(len(D['tabs'][max(D['tabs'])]['col'])), n_top300_scored=int((~np.isnan(score)).sum()),
               n_h101_universe=len(sc2), n_h101_top_tenth=npick, axjo_close=float(D['xjo'][i]), comparator_tr_level=float(D['xtr'][i]),
               n_review_list_25k=len(l25), n_review_list_100k=len(l100), inputs_sha256={k: sha(v) for k, v in INPUTS.items()}, files_sha256=files)
    mp = f'{REC}/manifest_{asof}.json'; json.dump(man, open(mp, 'w'), indent=1, sort_keys=True)
    return man, sha(mp), top

MONTH_ENDS = {'2026-10-30'}
if __name__ == '__main__':
    led = REC + '/LEDGER.jsonl'
    prev = json.loads(open(led).read().strip().splitlines()[-1])['entry_sha256'] if os.path.exists(led) and open(led).read().strip() else '0' * 64
    for asof in sys.argv[1:]:
        man, msha, top = snapshot(asof)
        e = dict(seq=(sum(1 for _ in open(led)) if os.path.exists(led) else 0) + 1, asof=asof, kind=man['kind'], event='score snapshot frozen (no trades)', manifest=f'manifest_{asof}.json',
                 manifest_sha256=msha, scores_sha256=man['files_sha256'][f'scores_top300_{asof}.csv'], recorded_utc=man['created_utc'], prev_entry_sha256=prev)
        e['entry_sha256'] = hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest(); prev = e['entry_sha256']
        open(led, 'a').write(json.dumps(e, sort_keys=True) + '\n')
        print(asof, 'manifest', msha, 'scores', e['scores_sha256'])
        for r in top: print('  ', r[16], r[1], r[3][:32], 'score', round(r[15], 4), 'tv_rank', r[0], 'close', r[5], r[17], 'list25k', r[18], 'list100k', r[19])
