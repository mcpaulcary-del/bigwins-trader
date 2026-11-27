import pickle, numpy as np, pandas as pd
S='/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
D=pickle.load(open(S+'/deepdive/data/bundle_eod.pkl','rb'))
dates=D['dates']; ME=D['ME']; cols=D['cols']
print(len(dates), dates[0], dates[-1], 'weekend rows', sum(d.weekday()>=5 for d in dates))
cal=pd.read_csv(S+'/data_foundation/out/calendar_dates.csv',parse_dates=['date'])
op=set(cal.loc[cal.xasx_open.astype(str)=='True','date']); ds=set(dates)
print('bundle dates not in calendar', [d for d in dates if d not in op][:20], 'calendar days missing from bundle', [d for d in sorted(op) if d>=dates[0] and d<=dates[-1] and d not in ds][:20])
R=np.load(S+'/replication_64/out/sig_eod.npz'); rd=pd.DatetimeIndex(pd.read_csv(S+'/replication_64/out/dates_eod.csv').iloc[:,0])
rc=pd.read_csv(S+'/replication_64/out/cols_eod.csv',index_col=0)
print('rep dates', len(rd), rd[0], rd[-1])
rme=R['me_idx']; rdates=rd[rme]
def pr(x): return pd.Series(x).rank(pct=True).values
tot=0
for k,i in enumerate(ME):
    if k not in D['tabs']: continue
    t=D['tabs'][k]; d=dates[i]
    if d<pd.Timestamp('2017-12-01'): continue
    m=t['vrank']<=300
    names=[cols[c] for c in t['col'][m]]
    a=np.column_stack([pr(t[c][m]) for c in ('M1','M2','M3','M5')]); sc=np.where(np.isnan(a).any(1),np.nan,a.mean(1))
    b=pd.Series(sc,index=[n.split('#')[0]+('' if n.endswith('#E') else '_'+n.split('#E')[1]) for n in names])
    kk=np.flatnonzero(rdates==d)
    if len(kk)==0: print('no rep month', d); continue
    kk=kk[0]; rk=R['rank'][kk]; u=np.flatnonzero((rk>0)&(rk<=300)); 
    r=pd.Series(R['score'][kk][u], index=[rc.index[j].split('#')[0]+('' if rc.index[j].endswith('#0') else '_'+rc.index[j].split('#')[1]) for j in u])
    sa=set(b.index); sb=set(r.index)
    common=sorted(sa&sb); diff=(b[common]-r[common]).abs()
    nd=int((diff>1e-9).sum())
    if sa!=sb or nd: 
        tot+=1
        print(d.date(), 'only builder', sorted(sa-sb)[:6], 'only rep', sorted(sb-sa)[:6], 'score diffs', nd, 'max', float(diff.max()))
print('months with any diff', tot)
