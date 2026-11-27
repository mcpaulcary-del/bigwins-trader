import pickle, numpy as np, pandas as pd, collections
S='/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
D=pickle.load(open(S+'/deepdive/data/bundle_eod.pkl','rb'))
dates=D['dates']; ME=D['ME']; cols=D['cols']; Pv=D['Pv']
W=np.load(S+'/replication_64/out/wide_eod.npz'); rP=W['P']; rTV=W['TV']
rd=pd.DatetimeIndex(pd.read_csv(S+'/replication_64/out/dates_eod.csv').iloc[:,0])
rc=pd.read_csv(S+'/replication_64/out/cols_eod.csv',index_col=0)
TVb=np.load(S+'/deepdive/data/TV_eod.npy')
off=np.searchsorted(rd,dates[0]); assert (rd[off:]==dates).all()
rP=rP[off:]; rTV=rTV[off:]
# map builder col -> rep col by code and overlap of rows
rbycode=collections.defaultdict(list)
for j,c in enumerate(rc.index): rbycode[c.split('#')[0]].append(j)
hasb=~np.isnan(Pv); hasr=~np.isnan(rP)
mp={}; nomatch=[]
for j,c in enumerate(cols):
    code=c.split('#')[0]; best=None;bo=0
    for q in rbycode.get(code,[]):
        o=(hasb[:,j]&hasr[:,q]).sum()
        if o>bo: bo=o;best=q
    if best is None: nomatch.append(c)
    else: mp[j]=best
print('builder cols',len(cols),'matched',len(mp),'unmatched with data',[c for c in nomatch if hasb[:,cols.index(c)].any()][:30])
used=set(mp.values()); print('rep cols with data after 2014-06 not matched', [rc.index[q] for q in range(len(rc)) if q not in used and hasr[:,q].any()][:30])
# compare P and row presence
cntP=0; cntRows=0; cntTV=0; ex=[]
for j,q in mp.items():
    a=Pv[:,j]; b=rP[:,q]
    m=hasb[:,j]&hasr[:,q]
    rows=(hasb[:,j]!=hasr[:,q]).sum()
    if rows: cntRows+=1
    if m.any():
        rat=a[m]/b[m]
        if np.nanmax(np.abs(rat/rat[-1]-1))>1e-6: cntP+=1; ex.append((cols[j], float(np.nanmax(np.abs(rat/rat[-1]-1))), str(dates[np.flatnonzero(m)[np.argmax(np.abs(rat/rat[-1]-1))]].date()), rows))
        elif abs(rat[-1]-1)>1e-6: ex.append((cols[j],'scale',float(rat[-1]),rows))
    if np.nanmax(np.abs(TVb[:,j]-rTV[:,q])/(1+np.abs(rTV[:,q])))>1e-3: cntTV+=1
print('P shape differs',cntP,'row presence differs',cntRows,'TV differs',cntTV)
ex.sort(key=lambda x: str(x[1]))
for e in ex[:80]: print(e)
pickle.dump(mp,open(S+'/bigwins_forward/out/_map_builder_rep.pkl','wb'))
