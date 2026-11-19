"""EARLY paper line - reference implementation (report 84). PAPER ONLY. No orders are placed by this code.
Month-end decision clock, fills at the next session's close. Pure functions on wide daily frames:
  RET  total return per session (split/dividend adjusted), NaN outside the listing's life
  CLOSE raw close (forward-filled inside life), TV traded value (0 on no-trade days)
  XJO  index level (price), FUND fund unit value (A200 total return)
  LIST table: index=code, columns first_i (row of first trade), cls ('ORD' = ordinary new listing), res (bool), name
State is a plain dict so it can be stored as JSON by the live runner."""
import numpy as np, re
PARAMS=dict(name='EARLY', age_min=126, age_max=147, tv_floor=100000.0, tv_window=126, min_price=0.20, exclude_res=True,
            stop_drop=0.35, max_hold=756, slice_pct=0.04, max_pos=25, tax=0.32, payout_days=20)
RES_RE=re.compile(r"RESOURCE|MINING|MINERAL|\bMINES?\b|GOLD|METALS?\b|EXPLORATION|LITHIUM|URANIUM|COPPER|NICKEL|\bZINC|\bIRON\b|\bCOAL\b|\bOIL\b|\bGAS\b|PETROLEUM|\bENERGY\b|PLATINUM|DIAMOND|SILVER|RARE EARTH|POTASH|GRAPHITE|COBALT|\bTIN\b|TUNGSTEN|VANADIUM|BAUXITE|PHOSPHATE|\bSANDS\b|HELIUM| NL\b|\bN\.L\.|HYDROCARBON|\bORE\b|MANGANESE|MOLY|ALUMINA|NIOBIUM|ANTIMONY|\bLEAD\b")
RES_IND=re.compile(r"Mining|Gold|Silver|Copper|Uranium|Coal|Oil & Gas|Metals|Steel|Aluminum")
FUND_RE=re.compile(r"\bETFS?\b|\bFUNDS?\b|ISHARES|VANGUARD|BETASHARES|SPDR|VANECK|\bETP\b|\bNOTES?\b|\bBONDS?\b|CONVERTIBLE|PREFERENCE|\bPREF\b|HYBRID|WARRANT|INSTALMENT|\bLIC\b|INVESTMENT COMPANY|INVESTMENT TRUST|\bUNITS\b|\bSERIES\b|MORTGAGE|PERLS|EXCHANGEABLE|\bINVESTMENTS? (LIMITED|LTD)\b|EQUITIES (LIMITED|LTD)|\bWAM \b|FUTURE GENERATION|ABSOLUTE|LEADERS (LIMITED|LTD)|\bINCOME\b|LONG SHORT|LISTED INVEST|STAPLED|\bREIT\b|\bTRUST\b|PROPERTY GROUP")
def fund_flag(name):
    """ETF / listed fund / LIC / trust / note by name (report 84 definition, slightly widened: any 'INCOME' or 'UNITS'). Such names are never bought."""
    return bool(FUND_RE.search(str(name).upper()))
def res_flag(name, industry=None):
    """resources flag: vendor industry when present, else the name keyword list (report 84 definition)."""
    if isinstance(industry,str) and industry.strip(): return bool(RES_IND.search(industry))
    return bool(RES_RE.search(str(name).upper()))
def half_spread(price, tv63):
    tick=0.001 if price<0.10 else (0.005 if price<2 else 0.01)
    band=0.0025 if tv63>=3e6 else 0.005 if tv63>=1e6 else 0.0075 if tv63>=2.5e5 else 0.0125 if tv63>=5e4 else 0.025
    return max(0.5*tick/price if price>0 else 0.05, band)
def features(i, j, first_i, RET, CLOSE, TV, XJO, P=PARAMS):
    """features of column j at decision row i (uses rows <= i only)."""
    age=i-first_i
    w0=max(first_i, i-P['tv_window']+1)
    tv=float(np.median(TV[w0:i+1,j])); mom=float(np.nanprod(1+RET[first_i+1:i+1,j])-1); xmom=float(XJO[i]/XJO[first_i]-1)
    return dict(age=age, tv=tv, close=float(CLOSE[i,j]), mom=mom, xmom=xmom, vola=float(np.nanstd(RET[first_i+1:i+1,j])), tv63=float(np.median(TV[max(first_i,i-62):i+1,j])))
def passes(f, res, P=PARAMS):
    why=[]
    if not (P['age_min']<=f['age']<=P['age_max']): why.append('age')
    if P['exclude_res'] and res: why.append('resources')
    if not f['tv']>=P['tv_floor']: why.append('traded value')
    if not f['close']>=P['min_price']: why.append('price')
    if not f['mom']>0: why.append('below first close')
    if not f['mom']>f['xmom']: why.append('behind index')
    return (len(why)==0), why
def new_state(capital, fund_price, i):
    return dict(fund_units=capital/fund_price, fund_cost=capital, start_i=i, pos={}, bought=[], loss_bank=0.0, tax_paid=0.0, spread_paid=0.0, log=[])
def _realise(S, gain, long, P):
    if gain<=0: S['loss_bank']+=-gain; return 0.0
    use=min(S['loss_bank'],gain); S['loss_bank']-=use
    return P['tax']*(gain-use)*(0.5 if long else 1.0)
def _fund_out(S, amount, price, i, P, taxable=True):
    fv=S['fund_units']*price
    if fv<=0: return 0.0
    amount=min(amount,fv); fr=amount/fv; gain=amount-S['fund_cost']*fr
    S['fund_units']*=(1-fr); S['fund_cost']*=(1-fr)
    if taxable:
        tx=_realise(S,gain,(i-S['start_i'])>252,P)
        if tx>0: _pay_tax(S,tx,price)
    return amount
def _pay_tax(S, tx, price):
    fv=S['fund_units']*price; tx=min(tx,fv)
    if fv>0: fr=tx/fv; S['fund_units']*=(1-fr); S['fund_cost']*=(1-fr); S['tax_paid']+=tx
def value(S, i, RET, FUND, last_i, term):
    v=S['fund_units']*FUND[i]
    for c,p in S['pos'].items():
        j=p['j']; b=min(i,last_i[j]); w=p['in']*float(np.nanprod(1+RET[p['fill_i']+1:b+1,j]))
        if last_i[j]<i: w*=(1+term.get(c,0.0))
        v+=w
    return v
def decide(S, i, cols, LIST, RET, CLOSE, TV, XJO, last_i, P=PARAMS, catchup_age_max=None):
    """month-end decision at row i -> dict(sells=[(code,reason)], buys=[code...], table=[candidate rows])."""
    sells=[]
    for c,p in S['pos'].items():
        j=p['j']
        if last_i[j]<=i-P['payout_days'] : sells.append((c,'payout (no close for %d sessions)'%P['payout_days'])); continue
        w=float(np.nanprod(1+RET[p['fill_i']+1:i+1,j])); p['peak']=max(p.get('peak',1.0),w)
        if i-p['fill_i']>=P['max_hold']: sells.append((c,'time limit'))
        elif w<=(1-P['stop_drop'])*p['peak']: sells.append((c,'stop: %.0f%% below best month-end'%(100*(1-w/p['peak']))))
    table=[]; amax=catchup_age_max or P['age_max']
    for c in LIST.index:
        r=LIST.loc[c]
        if r.cls!='ORD' or c in S['pos'] or c in S['bought']: continue
        age=i-int(r.first_i)
        if not (P['age_min']<=age<=amax): continue
        j=cols[c]
        if last_i[j]<i: continue
        f=features(i,j,int(r.first_i),RET,CLOSE,TV,XJO,P); PP=dict(P,age_max=amax); ok,why=passes(f,bool(r.res),PP)
        table.append(dict(code=c,ok=ok,why=';'.join(why),**f))
    free=P['max_pos']-(len(S['pos'])-len(sells))
    good=sorted([t for t in table if t['ok']],key=lambda t:-t['tv'])
    return dict(sells=sells,buys=[t['code'] for t in good[:max(free,0)]],skipped=[t['code'] for t in good[max(free,0):]],table=table)
def fill(S, D, k, cols, RET, CLOSE, TV, FUND, last_i, term, P=PARAMS, costs=True):
    """apply decision D at fill row k (next session close)."""
    for c,reason in D['sells']:
        p=S['pos'].pop(c); j=p['j']; b=min(k,last_i[j]); v=p['in']*float(np.nanprod(1+RET[p['fill_i']+1:b+1,j]))
        if last_i[j]<k: v*=(1+term.get(c,0.0)); hs=0.0
        else: hs=half_spread(CLOSE[k,j],float(np.median(TV[max(0,k-62):k+1,j]))) if costs else 0.0
        proceeds=v*(1-hs); S['spread_paid']+=v*hs; gain=proceeds-p['cost']
        tx=_realise(S,gain,(b-p['fill_i'])>252,P)
        S['fund_units']+=proceeds/FUND[k]; S['fund_cost']+=proceeds
        if tx>0: _pay_tax(S,tx,FUND[k])
        S['log'].append((c,p['fill_i'],k,p['cost'],proceeds,reason))
    for c in D['buys']:
        j=cols[c]
        if np.isnan(RET[k,j]) and last_i[j]<k: continue
        tot=value(S,k,RET,FUND,last_i,term); size=P['slice_pct']*tot
        if S['fund_units']*FUND[k]<size*1.02 or len(S['pos'])>=P['max_pos']: continue
        got=_fund_out(S,size,FUND[k],k,P); hs=half_spread(CLOSE[k,j],float(np.median(TV[max(0,k-62):k+1,j]))) if costs else 0.0
        S['spread_paid']+=got*hs; S['pos'][c]=dict(j=j,fill_i=k,cost=got,**{'in':got*(1-hs)},peak=1.0); S['bought'].append(c)
def liquidate(S, i, RET, CLOSE, TV, FUND, last_i, term, P=PARAMS):
    D=dict(sells=[(c,'final') for c in list(S['pos'])],buys=[]); fill(S,D,i,None,RET,CLOSE,TV,FUND,last_i,term,P)
    fv=S['fund_units']*FUND[i]; tx=_realise(S,fv-S['fund_cost'],True,P); return fv-tx
