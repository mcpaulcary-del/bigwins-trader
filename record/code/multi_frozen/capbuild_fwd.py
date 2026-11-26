# FORWARD COPY of improve6/code/capbuild.py for the multi-market forward record (AMENDMENT_forward_multimarket.md). Only change: the fixed "today" cut of share_series becomes the decision date (TODAY).
"""Point-in-time market capitalisation from EODHD fundamentals share counts (round 6).
cap[k,n] = shares known at decision date k (report date + LAG days) x split-consistent close, in one unit per exchange.
Screens: (1) share history not split-adjusted at a split -> repaired with the price file's split factor; (2) jumps of x3 or more between consecutive
reports -> spliced (older figures rescaled); (3) files whose level is off by x3 or more against the vendor's current market cap -> dropped; live files
inside that band are anchored to the vendor's current market cap (absorbs share classes). No return is computed here."""
import pickle,numpy as np,pandas as pd
LAG=90; STALE=800; TLO=0.10; THI=5.0
TODAY='2026-11-17'      # FORWARD (paper_multi.py sets this to the latest decision date before build())
def split_adj_price(pk):
    rc=pk['rc'].astype(float); px=pk['px'].astype(float); dv=np.nan_to_num(pk['divy'].astype(float)) if 'divy' in pk else 0.0
    K,N=rc.shape; rcf=pd.DataFrame(rc).ffill().values; pxf=pd.DataFrame(px).ffill().values
    with np.errstate(all='ignore'):
        g=(rcf[1:]/rcf[:-1])/(pxf[1:]/pxf[:-1])*(1+(dv[1:] if not np.isscalar(dv) else 0.0))
    ev=np.isfinite(g)&(np.abs(np.log(np.where(np.isfinite(g)&(g>0),g,1.0)))>np.log(1.25))
    lg=np.where(ev,np.log(g),0.0)
    cum=np.zeros((K,N)); cum[:-1]=np.cumsum(lg[::-1],axis=0)[::-1]      # product of event factors after k
    return rcf*np.exp(cum),g,ev
def share_series(o):
    """quarterly outstandingShares, annual rows where no quarterly row; balance-sheet share counts only (a) when there is nothing else or
    (b) for dates after the last outstandingShares row (v2: the vendor's outstandingShares block stops in 2020 for most Korean files), spliced at the overlap"""
    s=[(pd.Timestamp(d),v) for d,v in (o.get('sh_q') or []) if d and v==v and v>0]
    have=set(d for d,_ in s)
    s+=[(pd.Timestamp(d),v) for d,v in (o.get('sh_a') or []) if d and v==v and v>0 and pd.Timestamp(d) not in have]
    base=pd.Series(dict(sorted(set(s)))).sort_index() if s else pd.Series(dtype=float)
    b=[]
    for key in ('bs_q','bs_y'):
        for r in o.get(key) or []:
            v=r[3+10]
            if r[0] and v==v and v>0: b.append((pd.Timestamp(r[0]),v))
    bs=pd.Series(dict(sorted(set(b)))).sort_index() if b else pd.Series(dtype=float)
    today=pd.Timestamp(TODAY); base=base[base.index<=today] if len(base) else base; bs=bs[bs.index<=today] if len(bs) else bs   # FORWARD: TODAY = the decision date being processed (frozen file: fixed 2026-11-17)
    if len(base)<2: return bs if len(bs)>len(base) else base
    last=base.index[-1]; ext=bs[bs.index>last+pd.Timedelta(days=40)]
    if len(ext):
        near=bs[(bs.index>=last-pd.Timedelta(days=100))&(bs.index<=last+pd.Timedelta(days=40))]
        r=float(base.iloc[-1]/near.iloc[-1]) if len(near) else 1.0
        if not (1/3<r<3): r=1.0
        base=pd.concat([base,ext*r])
    return base
def build(fd,pk,lag=LAG,verbose=True,anchor=True):
    cols=[str(c) for c in pk['cols']]; dd=pd.DatetimeIndex(pk['dec_dates']); K=len(dd); N=len(cols); ddv=dd.values
    pa,g,ev=split_adj_price(pk); rc=pk['rc'].astype(float); T=int(pk['T']); lastc=pk['lastc']
    cap=np.full((K,N),np.nan); sh=np.full((K,N),np.nan); st=dict(files=0,with_shares=0,split_repairs=0,jump_splices=0,dropped_3x=0,anchored=0,files_jump=0)
    lev={}
    for n,c in enumerate(cols):
        o=fd.get(c)
        if not o: continue
        st['files']+=1; s=share_series(o)
        if len(s)==0: continue
        st['with_shares']+=1; d=s.index.values; v=s.values.astype(float).copy()
        for k in np.flatnonzero(ev[:,n]):                      # split between dd[k] and dd[k+1]
            b=np.flatnonzero(d<=ddv[k]); a=np.flatnonzero(d>=ddv[k+1])
            if len(b) and len(a) and abs(np.log(v[a[0]]/v[b[-1]]*g[k,n]))<0.35 and abs(np.log(g[k,n]))>0.4:
                v[:b[-1]+1]/=g[k,n]; st['split_repairs']+=1
        # single-report spikes: trailing median of the last five reports (point-in-time); count files that still hold a x3 step
        if len(v)>=3:
            v2=v.copy()
            for i in range(1,len(v)): v2[i]=np.median(v[max(0,i-4):i+1])
            v=v2
        r_=v[1:]/v[:-1]; st['files_jump']+=int(((r_>3)|(r_<1/3)).any()); st['jump_splices']+=int(((r_>3)|(r_<1/3)).sum())
        av=d+np.timedelta64(lag,'D')
        ki=np.searchsorted(av,ddv,side='right')-1
        ok=(ki>=0)
        shk=np.where(ok,v[np.maximum(ki,0)],np.nan); age=(ddv-d[np.maximum(ki,0)]).astype('timedelta64[D]').astype(float); shk[age>STALE]=np.nan
        sh[:,n]=shk; cap[:,n]=shk*pa[:,n]
        cap[~np.isfinite(rc[:,n]),n]=np.nan
        m=o['hl']['mcap']
        if lastc[n]>=T-2 and m==m and m>0 and np.isfinite(cap[-1,n]) and cap[-1,n]>0: lev[n]=m/cap[-1,n]
    med=float(np.median(list(lev.values()))) if len(lev)>=10 else np.nan
    for n in range(N):
        if n in lev:
            r=lev[n]/med
            if r>=3 or r<=1/3: cap[:,n]=np.nan; st['dropped_3x']+=1
            elif anchor: cap[:,n]*=r; st['anchored']+=1
    st['scale']=med; st['live_checked']=len(lev)
    # turnover screen (point-in-time, local data only): yearly traded value / market cap must lie in [TLO, THI]; outside = foreign secondary line (cap is the global company) or a wrong share count
    cap0=cap; tv=pk['medtv'].astype(float)*252.0      # both in pack price units (v2: the first version multiplied the cap by the currency scale and mis-set the band on rescaled packs)
    with np.errstate(all='ignore'): to=tv/cap0
    bad=np.isfinite(to)&((to<TLO)|(to>THI)); st['cells_turnover_low']=int((np.isfinite(to)&(to<TLO)&(pk['vrank']<=100)).sum()); st['cells_turnover_high']=int((np.isfinite(to)&(to>THI)&(pk['vrank']<=100)).sum()); st['cells_top100']=int((np.isfinite(to)&(pk['vrank']<=100)).sum())
    cap=np.where(bad|~np.isfinite(to),np.nan,cap0)
    # delisted names: cap stops 1 month after the last close
    if verbose: print(st)
    return cap,sh,st
