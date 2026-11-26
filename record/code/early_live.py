"""EARLY paper line - live adapter (reference). Reads the new-listings tracker's files (read-only) and writes a decision table.
PAPER ONLY: prints/writes proposed paper orders; places nothing. usage: early_live.py [--asof YYYY-MM-DD] [--catchup] [--state path.json]"""
import sys, os, json, gzip, glob, argparse, numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import early_ref as ER
B='/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/'
NL=B+'bigwins_forward/data/newlist/'; OUT=B+'deep84/out/'
def load(asof=None):
    reg=pd.read_csv(NL+'baseline_listings.csv.gz'); reg=reg[reg.cls_final=='new_listing'].drop_duplicates('code').set_index('code')
    trk=pd.read_csv(NL+'newlist_tracker.csv').set_index('code')
    px=pd.read_csv(NL+'paths.csv.gz',parse_dates=['date'])
    xj=pd.read_pickle(B+'data_foundation/out/index_v2.pkl').xjo.dropna()   # research index history; the live runner should use the record's own AXJO store
    for f in sorted(glob.glob(B+'bigwins_forward/data/eodhd/raw/axjo_recent/AXJO.INDX__*.json.gz')):
        d=pd.DataFrame(json.load(gzip.open(f,'rt'))); d['date']=pd.to_datetime(d.date); xj=pd.concat([xj[~xj.index.isin(d.date)],d.set_index('date').close]).sort_index()
    if asof is not None: px=px[px.date<=asof]; xj=xj[xj.index<=asof]
    cal=pd.DatetimeIndex(sorted(set(px.date)|set(xj.index[(xj.index>=px.date.min())&(xj.index<=px.date.max())])))
    C=px.pivot(index='date',columns='code',values='close').reindex(cal); A=px.pivot(index='date',columns='code',values='adj_close').reindex(cal); V=px.pivot(index='date',columns='code',values='volume').reindex(cal)
    valid=C.notna().values; first=np.where(valid.any(0),valid.argmax(0),-1); last=np.where(valid.any(0),len(cal)-1-valid[::-1].argmax(0),-1)
    RET=A.ffill().pct_change(fill_method=None).values.copy(); CLOSE=C.ffill().values; TV=np.nan_to_num((C*V).values)
    for j in range(C.shape[1]): RET[:first[j]+1,j]=np.nan
    codes=list(C.columns); cols={c:j for j,c in enumerate(codes)}
    rows=[]
    for c in codes:
        if c not in reg.index and c not in trk.index: continue
        ind=trk.industry.get(c) if c in trk.index else None; nm=trk.name.get(c) if c in trk.index else reg.name.get(c)
        fd=pd.Timestamp(reg.first_date.get(c)) if c in reg.index else pd.Timestamp(trk.listing_date.get(c))
        j=cols[c]
        # the tracker's listing date must agree with the first price row, else the name is not treated as a clean new listing
        ok=abs((cal[first[j]]-fd).days)<=5
        rows.append(dict(code=c,first_i=int(first[j]),cls=('FUND' if ER.fund_flag(nm) else 'ORD') if ok else 'CHECK',res=ER.res_flag(nm,ind),name=str(nm)[:40],industry=ind,listing_date=fd.date()))
    LIST=pd.DataFrame(rows).set_index('code')
    return cal,cols,LIST,RET,CLOSE,TV,xj.reindex(cal).ffill().values,last
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--asof'); ap.add_argument('--catchup',action='store_true'); ap.add_argument('--state'); a=ap.parse_args()
    cal,cols,LIST,RET,CLOSE,TV,XJ,last=load(pd.Timestamp(a.asof) if a.asof else None)
    i=len(cal)-1
    S=json.load(open(a.state)) if a.state and os.path.exists(a.state) else ER.new_state(100000.0,1.0,i)
    Dn=ER.decide(S,i,cols,LIST,RET,CLOSE,TV,XJ,last,ER.PARAMS,catchup_age_max=252 if a.catchup else None)
    T=pd.DataFrame(Dn['table'])
    print('EARLY dry decision as of',cal[i].date(),'| tracked new listings',len(LIST),'| in age window',len(T),'| pass',int(T.ok.sum()) if len(T) else 0)
    if len(T):
        T=T.join(LIST[['name','res','industry','listing_date']],on='code').sort_values(['ok','tv'],ascending=False)
        pd.set_option('display.width',250); print(T[['code','name','res','listing_date','age','tv','close','mom','xmom','ok','why']].round(3).to_string(index=False))
        T.to_csv(OUT+f'early_decision_{cal[i].date()}.csv',index=False)
    print('paper buys:',Dn['buys'],'| paper sells:',Dn['sells'])
