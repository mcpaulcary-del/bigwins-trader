"""Month-end signals per v1.1 part B (blind replication of report 64).
Run: python3 -I signals.py v2|eod  -> out/sig_<src>.npz
Arrays per month-end (rows = month-ends from 1998 on):
  rank  : traded-value rank (1 = largest) among companies with >= 200 closes in W; 0 = no rank
  med   : median daily traded value over W (252 days, no-row = 0)
  score : B4 score (NaN = none)
  c10   : close10(t)
"""
import sys
import numpy as np, pandas as pd
from scipy.stats import rankdata

BASE = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
OUT = f'{BASE}/bigwins_forward/out/rep13'
SRC = sys.argv[1]
w = np.load(f'{OUT}/wide_{SRC}.npz')
P, TV = w['P'], w['TV']
dates = pd.DatetimeIndex(pd.read_csv(f'{OUT}/dates_{SRC}.csv').iloc[:, 0])
nD, nC = P.shape
has = ~np.isnan(P)
C10 = pd.DataFrame(P).ffill(limit=10).values
me_idx = pd.Series(np.arange(nD), index=dates).groupby([dates.year, dates.month]).max().values
me_all = me_idx.copy()
k0 = int(np.searchsorted(me_all, 253))
me_idx = me_all[k0:]
K = len(me_idx)
RANK = np.zeros((K, nC), dtype=np.int32); MED = np.zeros((K, nC)); SCORE = np.full((K, nC), np.nan); CC10 = np.full((K, nC), np.nan)
logP = np.log(P)
for k, it in enumerate(me_idx):
    ka = k + k0  # position in me_all
    w0 = it - 251
    cnt = has[w0:it + 1].sum(0)
    med = np.median(TV[w0:it + 1], axis=0)
    elig = np.where(cnt >= 200)[0]
    order = elig[np.lexsort((elig, -med[elig]))]  # median desc, then column order
    rank = np.zeros(nC, dtype=np.int32); rank[order] = np.arange(1, len(order) + 1)
    U = order[:300]
    RANK[k] = rank; MED[k] = med; CC10[k] = C10[it]
    # B2 signals
    s1 = C10[me_all[ka - 1], U] / C10[me_all[ka - 12], U] - 1 if ka >= 12 else np.full(len(U), np.nan)
    s2 = C10[it, U] / C10[me_all[ka - 6], U] - 1 if ka >= 6 else np.full(len(U), np.nan)
    mx = np.nanmax(P[w0:it + 1][:, U], axis=0)
    s3 = C10[it, U] / mx
    lr = logP[w0:it + 1][:, U] - logP[w0 - 1:it][:, U]  # returns dated in W (first uses W-)
    nret = (~np.isnan(lr)).sum(0)
    sd = np.nanstd(lr, axis=0, ddof=1)
    s4 = np.where(nret >= 200, -sd, np.nan)
    pct = []
    for s in (s1, s2, s3, s4):
        ok = ~np.isnan(s)
        p = np.full(len(U), np.nan)
        if ok.sum():
            p[ok] = rankdata(s[ok], method='average') / ok.sum()
        pct.append(p)
    sc = np.mean(pct, axis=0)  # NaN if any missing
    SCORE[k, U] = sc
np.savez(f'{OUT}/sig_{SRC}.npz', me_idx=me_idx, rank=RANK, med=MED, score=SCORE, c10=CC10)
print(SRC, K, 'month-ends from', dates[me_idx[0]].date())
