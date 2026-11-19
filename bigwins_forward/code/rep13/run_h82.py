"""Run H82 v1.2 accounts (parts M2/M3) and comparators. Writes out/h82_results.json, out/h82_nav_*.csv, out/h82_trades_*.csv"""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins_forward/code/rep13')
import engine as E

OUT = E.OUT
ACC = []
for cap in (25000, 100000):
    for st, m in (('2000-12-29', 12), ('2001-03-30', 3), ('2001-06-29', 6), ('2001-09-28', 9)):
        ACC.append(('dev', 'v2', cap, st, '2015-12-31', m, 'G3'))
    ACC.append(('unseenA', 'v2', cap, '2015-12-31', '2024-05-31', 12, 'G3'))
    ACC.append(('unseenB', 'eod', cap, '2017-12-29', '2026-11-13', 12, 'J3'))
only = sys.argv[1] if len(sys.argv) > 1 else None
res = []
for per, src, cap, st, en, m, ck in ACC:
    if only and per != only:
        continue
    row = dict(period=per, src=src, capital=cap, start=st, end=en, review_month=m)
    for mode in ('bc', 'ac', 'A', 'B'):
        r = E.run_account(src, cap, st, en, m, mode, record=(mode == 'ac'))
        c = E.comparator(src, cap, st, en, mode, ck)
        row[f'cagr_{mode}'] = r['cagr']; row[f'idx_cagr_{mode}'] = c['cagr']; row[f'final_{mode}'] = r['final']
        if mode == 'ac':
            X = E.load(src); dates = X['dates']
            days, navs = r['nav_series']
            navs = np.array(navs)
            idx = X['TR'] if ck == 'J3' else X['PR']
            iv = np.array([idx[d] for d in days])
            mret = navs[1:] / navs[:-1] - 1; iret = iv[1:] / iv[:-1] - 1
            ex = mret - iret
            row['ann_excess_ac'] = 12 * ex.mean(); row['t_excess'] = ex.mean() / (ex.std(ddof=1) / np.sqrt(len(ex)))
            pk = np.maximum.accumulate(navs); row['maxdd_ac'] = float((navs / pk - 1).min())
            row['turnover_ac'] = r['turnover']; row['trades_ac'] = r['trades']
            pos = r['positions']; row['n_positions'] = len(pos)
            tag = f"{per}_{cap}_{st}"
            pd.DataFrame({'date': [dates[d].date() for d in days], 'nav': navs, 'index': iv}).to_csv(f'{OUT}/h82_nav_{tag}.csv', index=False)
            pd.DataFrame(r['trades_log'], columns=['date', 'company', 'kind', 'shares', 'price', 'cash']).to_csv(f'{OUT}/h82_trades_{tag}.csv', index=False)
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
    res.append(row)
devB = [r['cagr_B'] for r in res if r['period'] == 'dev']
out = dict(accounts=res)
if len(devB) == 8:
    out['robust_score_M2'] = float(np.mean(devB))
    print('robust score', out['robust_score_M2'])
json.dump(out, open(f'{OUT}/h82_results{"_" + only if only else ""}.json', 'w'), indent=1, default=str)
