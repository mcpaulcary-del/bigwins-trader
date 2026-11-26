# Enhanced index on point-in-time market caps (round 6). score -> tilted weight -> rank; engine sim6 (weighted book, wnorm, external weights).
from lib6 import *
import sim6 as S6, json, time
def m3pct(mk): return mk.pct_of(SC.custom(mk,'c:s1,s2,s3'))
def issuance(mk):
    """ln(shares now / shares 12 months ago) from the cleaned point-in-time share counts (split-repaired, trailing median of five reports, 90-day lag)"""
    sh=mk.shk; o=np.full(sh.shape,np.nan)
    with np.errstate(all='ignore'): o[12:]=np.log(sh[12:]/sh[:-12])
    o[~np.isfinite(o)]=np.nan; return o
def score(mk,kind):
    m=m3pct(mk)
    if kind=='M3': return m
    if kind=='M3I':
        q=mk.pct_of(-issuance(mk)); return np.where(np.isfinite(q),(m+q)/2,np.nan)
    if kind=='I': return mk.pct_of(-issuance(mk))
    if kind=='none': return np.where(np.isfinite(m),0.5,np.nan)
    if kind.startswith('rnd'): return np.where(np.isfinite(mk.vrank0),np.random.default_rng(int(kind[3:])).random(mk.vrank.shape),np.nan)
    raise KeyError(kind)
def tilted(mk,kind,a):
    """weights = cap x max(0, 1 + a(2p-1)), p = percentile of the score among universe names with a cap and a score; rank 1 = largest weight"""
    key=('ei',kind,a)
    if key in mk.ranks: return mk.ranks[key]
    sc=score(mk,kind); um=mk.uni if mk.above is None else (mk.uni|mk.above); cap=np.where(um&np.isfinite(mk.cap),mk.cap,np.nan); p=mk.pct_of(np.where(np.isfinite(cap),sc,np.nan))
    w=cap*np.maximum(0.0,1+a*(2*p-1)); w[~np.isfinite(w)]=np.nan; w=np.where(w>0,w,np.nan)
    r=np.full(w.shape,np.nan)
    for k in range(mk.K):
        # v2 (post-look fix, US mid/small bands only): ranks run over the band's own 100 names; a holding now traded above the band is read against them
        # and takes no rank away. The frozen version ranked the above-band giants too, so ranks 1-30 were all unbuyable names and the books stayed empty.
        m=np.flatnonzero(np.isfinite(w[k])&mk.uni[k])
        if len(m): o=np.lexsort((mk.vrank[k,m],-w[k,m])); r[k,m[o]]=np.arange(1,len(m)+1)
        if mk.above is not None and len(m):
            e=np.flatnonzero(np.isfinite(w[k])&mk.above[k]); srt=np.sort(w[k,m])
            if len(e): r[k,e]=1+len(m)-np.searchsorted(srt,w[k,e],side='right')
    mk.ranks[key]=(r,w); return r,w
def rank_score(mk,kind,cov=False):
    """M3-style rank on a score (optionally only names with a usable cap)"""
    sc=score(mk,kind)
    if cov: sc=np.where(np.isfinite(mk.cap),sc,np.nan)
    r=np.full(sc.shape,np.nan)
    for k in range(mk.K):
        m=np.flatnonzero(mk.uni[k]&np.isfinite(sc[k]))
        if len(m): o=np.lexsort((mk.vrank[k,m],-sc[k,m])); r[k,m[o]]=np.arange(1,len(m)+1)
    return r
M3KW=dict(form='band',kconf=2,B=15,H=50,core_w=0.5,defer_all=True,mer=0.0)
def EIKW(B=30,H=45,core_w=0.0,nmax=30,wmax=0.20,**x): return dict(dict(form='band',kconf=2,B=B,H=H,core_w=core_w,defer_all=True,mer=0.0,wext=True,wnorm=True,wmax=wmax,nmax=nmax),**x)
CONF={
 'M3':('rank','M3',False,M3KW), 'M3cap':('rank','M3',True,M3KW), 'M3I':('rank','M3I',True,M3KW),
 'CW':('ei','none',0.0,EIKW()), 'EI05':('ei','M3',0.5,EIKW()), 'EI10':('ei','M3',1.0,EIKW()), 'EI20':('ei','M3',2.0,EIKW()),
 'EI10I':('ei','M3I',1.0,EIKW()), 'EI10c5':('ei','M3',1.0,EIKW(core_w=0.5)), 'EI20c5':('ei','M3',2.0,EIKW(core_w=0.5)),
}
def setup(mk,name):
    typ,kind,a,kw=CONF[name]
    if typ=='rank': mk.wext=None; return rank_score(mk,kind,a),dict(kw)
    r,w=tilted(mk,kind,a); mk.wext=w; return r,dict(kw)
LIFE=dict(core_until=25000.0)
def Xrun(mk,name,win='F',sizes=(25000,100000),tau=0.32,full=False):
    rk,kw=setup(mk,name); starts,end=mk.win[win]; k1=mk.kof(end); out={}
    for S0 in sizes:
        xs=[];es=[]
        for st in starts:
            if CONF[name][0]=='ei': mk.wext=tilted(mk,CONF[name][1],CONF[name][2])[1]
            a=S6.run(mk,rk,S0,mk.kof(st),k1,tau=tau,**kw); b=fund(mk,S0,st,end,tau,'CL'); xs.append(a['cagr']-b['cagr']); es.append(a)
        a=es[0]; ix=fund(mk,S0,starts[0],end,tau,'CL'); n=min(len(a['navs']),len(ix['navs']))
        r=a['navs'][1:n]/a['navs'][:n-1]-1; bi=ix['navs'][1:n]/ix['navs'][:n-1]-1; ex=(r-bi)[:-1]
        out[S0]=dict(X=float(np.mean(xs)),Xmin=float(np.min(xs)),turn=float(np.mean([e['turnover'] for e in es])),nheld=float(np.mean([e['nheld'] for e in es])),te=float(ex.std(ddof=1)*np.sqrt(12)),eng=float(np.mean([e['cagr'] for e in es])),fund=float(ix['cagr']),top5=float(S6.top5_share(a)[0]))
    return out
