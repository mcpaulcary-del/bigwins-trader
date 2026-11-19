# acct3.py -- ACCOUNTING engine for blind build 3. It holds NO strategy: no universe rule, no signal, no ranking, no number of
# holdings, no holding-period rule, no parameter list. You write a Strategy object (three methods, see class Strategy);
# the engine does only what a broker, the exchange and the tax office would do to your orders:
#   - A$10,000 once; orders decided at a close fill at the NEXT session's close; sells before buys
#   - brokerage max(A$6.60, 0.088%) per order; a modelled half-spread per side (function half_spread below)
#   - a buy must be at least A$500 and at most cash less A$50; at most 5% of the 20-session median traded value
#   - only ordinary shares can be bought; no shorting, no borrowing
#   - tax: 32% of net realised gains at each June month-end, paid from cash; a gain on a parcel held 367 days or more is
#     halved; losses carried forward; parcels are sold first-in-first-out; everything is sold and taxed at the end
#   - a holding that stops trading is paid out by the rule in Engine._payout
# The strategy is handed a View that contains rows up to the decision day only. You may NOT change this file.
import numpy as np, pandas as pd

CAPITAL = 10000.0
MIN_BUY = 500.0          # ASX minimum marketable parcel for a first purchase; the engine applies it to every buy
RESERVE = 50.0           # cash always kept back
MAX_ORDER_SHARE = 0.05   # a buy may not exceed this share of the 20-session median traded value
TAX = 0.32
DISCOUNT_DAYS = 367      # calendar days from buy fill to sell fill for the halved gain
SPREAD_KNOTS = ((50, 0.0010), (200, 0.0025), (450, 0.0050), (800, 0.0075), (1500, 0.0150))


def fee(v):
    return max(6.6, 0.00088 * v)


def tick(p):
    return 0.001 if p < 0.10 else (0.005 if p < 2.0 else 0.01)


def half_spread(rank, price):
    """Modelled half-spread per side. rank = the entity's place among ordinary shares by 252-session median traded value
    (1 = most traded; NaN = unranked). Straight lines between the knots, flat outside them, never less than half an ASX
    price step. AN ASSUMPTION: no real fill has been compared with it, and beyond rank 800 it is extrapolation."""
    xs = [k[0] for k in SPREAD_KNOTS]; ys = [k[1] for k in SPREAD_KNOTS]
    b = ys[-1] if not np.isfinite(rank) else float(np.interp(rank, xs, ys))
    return max(b, 0.5 * tick(price) / price) if price > 0 else b


def discount_ok(buy_date, sell_date, months_held):
    return (sell_date - buy_date).days >= DISCOUNT_DAYS


def month_ends(dates):
    """Row numbers of the last session of each calendar month."""
    idx = pd.DatetimeIndex(dates); ser = pd.Series(np.arange(len(idx)), index=idx)
    return [int(v) for v in ser.groupby([idx.year, idx.month]).last().values]


def payout_class(t):
    return {'takeover': 'takeover', 'liquidation': 'fail'}.get(t, 'unk')


class View:
    """What a strategy may look at on decision day i: every array is cut at row i (inclusive). Columns = entities."""
    def __init__(s, E, i):
        s._E = E; s.i = i; s.date = E.idx[i]; s.n_entities = len(E.cols); s.labels = E.cols
    @property
    def dates(s): return s._E.idx[:s.i + 1]
    @property
    def RET(s): return s._E.R[:s.i + 1]          # daily total return (splits and dividends in); NaN = no price; glitch days NaN
    @property
    def CR(s): return s._E.CR[:s.i + 1]          # raw close as traded (not adjusted); NaN = no trade
    @property
    def TV(s): return s._E.TV[:s.i + 1]          # traded value of the day in A$ (0 = no trade once listed; NaN before listing)
    @property
    def L(s): return s._E.L[:s.i + 1]            # cumulative log total return (a convenience: sum of log(1+RET), NaN as 0)
    @property
    def fund(s): return s._E.xi[:s.i + 1]        # the ASX 200 with dividends
    @property
    def ordinary(s): return s._E.ok              # True = ordinary share (can be bought)
    @property
    def first(s):                                # first priced day, hidden if later than today
        f = s._E.first.copy(); f[f > np.datetime64(s.date, 'D')] = np.datetime64('NaT'); return f
    @property
    def delisted(s):                             # delisting records dated on or before today: DataFrame(eid, delist_date, reason)
        d = s._E.delist; return d[d.delist_date <= s.date]
    def cost_rank(s): return s._E.rank(s.i)      # the rank the spread model uses (array over entities)
    def half_spread(s, j): return half_spread(s._E.rank(s.i)[j], s._E.clff[s.i, j])
    def month_index(s): return s.date.year * 12 + s.date.month


class Book:
    """The account as the strategy sees it at the decision close (valued at that close, not at the fill)."""
    def __init__(s, cash, nav, holdings, memo, lapsed):
        s.cash = cash; s.nav = nav; s.holdings = holdings; s.memo = memo; s.lapsed = lapsed
        # holdings: {entity column j: dict(value, cost, first_buy_date, days_held, months_held, parcels)}
        # memo: a dict the strategy may write to; it is carried from decision to decision
        # lapsed: orders of the previous decision that did not fill, as (j, 'buy'|'sell', reason)


class Strategy:
    """Write your own. The engine calls, at each of your decision days (a close):
         decision_rows(dates)  -> row numbers of your decision days, from the trading calendar alone (default: month-ends)
         sells(view, book)     -> list of j (sell all) or (j, fraction)
         buys(view, book)      -> (orders, max_holdings): orders = list of (j, weight) in priority order, weight = share of
                                  the account value at the fill; the engine fills them in order, skips any it must refuse,
                                  and stops when max_holdings entities are held (None = no cap)
       buys() is called after the sells are known: book.holdings then holds what is left (a part-sold holding still shows its
       value before the sale), book.sold lists what was sold, and book.cash is still the cash before the sale proceeds (the
       proceeds are fixed at the fill). Nothing the strategy sees contains a price after the decision close."""
    def decision_rows(s, dates): return month_ends(dates)
    def sells(s, view, book): return []
    def buys(s, view, book): return [], None


class Engine:
    def __init__(s, dirn, poison_after=None):
        dirn = dirn.rstrip('/'); z = np.load(dirn + '/panel.npz'); s.idx = pd.to_datetime(z['dates']); s.cols = list(z['cols']); s.n = len(s.idx)
        R = z['RET'].astype('float64'); R[(R < -0.95) | (R > 10)] = np.nan
        s.CR = z['CR'].astype('float64'); TV = z['TV'].astype('float64')
        if poison_after is not None:     # as-of audit: rows after this row are blanked
            R[poison_after + 1:] = np.nan; s.CR[poison_after + 1:] = np.nan; TV[poison_after + 1:] = np.nan
        m = pd.read_csv(dirn + '/meta.csv', index_col=0).loc[s.cols]
        s.ok = ~m.excl.values.astype(bool); s.first = pd.to_datetime(m['first']).values.astype('datetime64[D]')
        s.R = R; s.L = np.log1p(np.nan_to_num(R)).cumsum(0); s.Rz = np.nan_to_num(R)
        has = ~np.isnan(s.CR); started = has.cumsum(0) > 0; started |= (s.first < np.datetime64(s.idx[0], 'D'))[None, :]
        s.TV = np.where(started, np.nan_to_num(TV), np.nan)
        tvd = pd.DataFrame(s.TV); s.m252 = tvd.rolling(252, min_periods=120).median().values; s.m20 = tvd.rolling(20, min_periods=10).median().values
        s.clff = pd.DataFrame(s.CR).ffill().values
        s.lastv = np.maximum.accumulate(np.where(has, np.arange(s.n)[:, None], -1), axis=0); s.end_last = s.lastv[-1]
        s.ME = month_ends(s.idx)
        x = pd.read_csv(dirn + '/xtr.csv', index_col=0, parse_dates=True).iloc[:, 0]; s.xi = x.reindex(s.idx).ffill().values
        d = pd.read_csv(dirn + '/delist.csv', parse_dates=['delist_date']); s.delist = d
        s.dcl = {e: payout_class(r) for e, r in d.sort_values('delist_date').groupby('eid').last().reason.items()}
        s._rk = {}

    def rank(s, i):
        if i not in s._rk:
            s._rk[i] = pd.Series(np.where(s.ok & (s.lastv[i] >= i - 4), s.m252[i], np.nan)).rank(ascending=False).values
        return s._rk[i]

    def _hs(s, a, j, rk, mult): return mult * half_spread(rk[j], s.clff[a, j])

    def _payout(s, i, j):
        """A holding with no close for 20 sessions that never trades again in the data: paid at its last close if the record
        says takeover, zero if liquidation, otherwise last close only if that was within 30% of its 250-session high."""
        dc = s.dcl.get(s.cols[j], 'unk'); lp = s.clff[i, j]; l0 = s.lastv[i, j]
        hh = np.nanmax(s.CR[max(0, l0 - 250):l0 + 1, j])
        term = {'takeover': 1.0, 'fail': 0.0}.get(dc, 1.0 if lp >= 0.7 * hh else 0.0)
        return term, dc, lp

    def _plan(s, orders, max_holdings, nav_fill):
        """Turns the strategy's (j, weight) list into dollar amounts at the fill."""
        return [(int(j), float(w) * nav_fill) for j, w in orders], max_holdings

    def sim(s, strat, start, end, mult=1.0, detail=False):
        """Runs one book. start/end: dates; the first event is the first decision day or month-end on or after start, the
        book is sold at the fill of the last month-end on or before end. mult multiplies the modelled spread."""
        t0 = pd.Timestamp(start); t1 = pd.Timestamp(end)
        dec = set(int(i) for i in strat.decision_rows(s.idx) if 260 <= i < s.n - 1)
        me = set(i for i in s.ME if 260 <= i < s.n - 1)
        ev = sorted(i for i in (dec | me) if t0 <= s.idx[i] <= t1)
        lastme = max(i for i in ev if i in me); ev = [i for i in ev if i <= lastme]
        cash = CAPITAL; H = {}; memo = {}; lapsed = []; nav = []; daily = []; fy = 0.0; carry = 0.0; tax = 0.0
        ntr = 0; brk = 0.0; spr = 0.0; pos = []; heldn = []; cashs = []; nme = 0; refused = {}; hid = 0

        def hval(j): return sum(p['val'] for p in H[j]['parcels'])

        def close(j, p, share, proceeds, why, px, a):
            nonlocal fy
            c = p['cost'] * share; g = proceeds - c
            fy += g * 0.5 if (g > 0 and discount_ok(p['bd'], s.idx[a], nme - p['bm'])) else g
            pos.append(dict(eid=s.cols[j], hid=H[j]['hid'] if j in H else p['hid'], buy_date=p['bd'], buy_px=p['bp'], sell_date=s.idx[a], sell_px=px,
                            days=(s.idx[a] - p['bd']).days, cost=c, proceeds=proceeds, pnl=g, why=why))

        pa = None
        for k, i in enumerate(ev):
            a = i + 1; rk = s.rank(i)
            if pa is not None:
                if a > pa + 1 and H:   # daily values between events (for the worst fall)
                    js = list(H); v0 = np.array([hval(j) for j in js]); seg = np.exp(s.L[pa + 1:a][:, js] - s.L[pa, js])
                    daily += list(zip(s.idx[pa + 1:a], cash + seg @ v0))
                for j, h in H.items():
                    g = float(np.exp(s.L[a, j] - s.L[pa, j]))
                    for p in h['parcels']: p['val'] *= g
            if i in me: nme += 1
            NAV = cash + sum(hval(j) for j in H); nav.append((s.idx[a], NAV)); daily.append((s.idx[a], NAV))
            if i in me and s.idx[i].month == 6:
                net = fy + carry
                if net > 0: t = TAX * net; cash -= t; tax += t; carry = 0.0
                else: carry = net
                fy = 0.0
            for j in list(H):
                if s.lastv[i, j] < i - 20 and s.end_last[j] == s.lastv[i, j]:
                    term, dc, lp = s._payout(i, j); h = H[j]
                    for p in h['parcels']:
                        pr = p['val'] * term; cash += pr; close(j, p, 1.0, pr, 'payout_' + dc + ('' if term else '_zero'), lp * term, a)
                    del H[j]
            if i == lastme: break
            if i in dec:
                back = {j: float(np.exp(s.L[i, j] - s.L[a, j])) for j in H}   # value at the decision close, not at the fill
                hv = {j: dict(value=hval(j) * back[j], cost=sum(p['cost'] for p in h['parcels']), first_buy_date=h['parcels'][0]['bd'],
                              days_held=(s.idx[i] - h['parcels'][0]['bd']).days, months_held=nme - h['parcels'][0]['bm'], parcels=len(h['parcels'])) for j, h in H.items()}
                book = Book(cash, cash + sum(v['value'] for v in hv.values()), hv, memo, lapsed); view = View(s, i); lapsed = []
                sold = set(); cash0 = cash
                for o in strat.sells(view, book):
                    j, fr = (o if isinstance(o, tuple) else (o, 1.0)); j = int(j); fr = float(min(max(fr, 0.0), 1.0))
                    if j not in H or fr <= 0 or j in sold: continue
                    if np.all(np.isnan(s.CR[a:a + 5, j])): lapsed.append((j, 'sell', 'no trade in 5 sessions')); continue
                    sold.add(j); h = H[j]; V = hval(j) * fr; cst = s._hs(a, j, rk, mult); f = fee(V); left = V; px = s.clff[a, j]
                    spr += V * cst; brk += f; ntr += 1; cash += V * (1 - cst) - f
                    for p in list(h['parcels']):       # first in, first out
                        if left <= 1e-12: break
                        take = min(p['val'], left); sh = take / p['val']; pr = take * (1 - cst) - f * take / V
                        close(j, p, sh, pr, 'sold', px, a); left -= take
                        if sh >= 1 - 1e-12: h['parcels'].remove(p)
                        else: p['val'] -= take; p['cost'] *= (1 - sh)
                    if not h['parcels']: del H[j]
                book2 = Book(cash0, book.nav, {j: v for j, v in hv.items() if j in H}, memo, lapsed); book2.sold = sorted(sold)
                orders, maxh = strat.buys(view, book2)
                NAVf = cash + sum(hval(j) for j in H); plan, maxh = s._plan(orders, maxh, NAVf)
                for j, amt in plan:
                    if maxh is not None and len(H) >= maxh and j not in H: break
                    why = None
                    if not s.ok[j]: why = 'not an ordinary share'
                    elif np.isnan(s.CR[a, j]): why = 'no trade on the fill day'
                    if why is None:
                        amt = min(amt, cash - RESERVE)
                        if amt < MIN_BUY: why = 'under A$500 or no cash'
                        elif not amt <= MAX_ORDER_SHARE * np.nan_to_num(s.m20[i, j]): why = 'over 5% of 20-session median traded value'
                    if why is None and H:
                        X = s.Rz[i - 59:i + 1]
                        with np.errstate(all='ignore'): cc = [np.corrcoef(X[:, j], X[:, q])[0, 1] for q in H if q != j]
                        if len(cc) and np.nanmax(cc) > 0.98 and (X[:, j] != 0).sum() >= 40: why = 'same company as a holding (return correlation above 0.98)'
                    if why is not None:
                        lapsed.append((j, 'buy', why)); refused[why] = refused.get(why, 0) + 1
                        if why.startswith('under'): break
                        continue
                    cst = s._hs(a, j, rk, mult); f = fee(amt)
                    if j not in H: hid += 1; H[j] = dict(hid=hid, parcels=[])
                    H[j]['parcels'].append(dict(val=(amt - f) / (1 + cst), cost=amt, bd=s.idx[a], bp=s.clff[a, j], bm=nme, hid=H[j]['hid']))
                    cash -= amt; spr += (amt - f) * cst / (1 + cst); brk += f; ntr += 1
            heldn.append(len(H)); cashs.append(cash / max(NAV, 1)); pa = a
        # liquidation at the last valuation
        i = lastme; a = i + 1; rk = s.rank(i); pre = nav[-1][1]; liq = cash; openp = len(H)
        for j in list(H):
            h = H[j]; V = hval(j); cst = s._hs(a, j, rk, mult); f = fee(V)
            for p in h['parcels']: close(j, p, 1.0, p['val'] * (1 - cst) - f * p['val'] / V, 'open_at_end', s.clff[a, j], a)
            liq += V * (1 - cst) - f
        net = fy + carry; fin = TAX * net if net > 0 else 0.0; liq -= fin
        sr = pd.Series(dict(nav)); yrs = (sr.index[-1] - sr.index[0]).days / 365.25
        fa = [e + 1 for e in ev]; bm = pd.Series(s.xi[fa], index=sr.index); G = bm.iloc[-1] / bm.iloc[0]
        o = dict(at=(max(liq, 1.0) / CAPITAL) ** (1 / yrs) - 1, fund_at=(1 + (G - 1) * 0.84) ** (1 / yrs) - 1, before_tax=(pre / CAPITAL) ** (1 / yrs) - 1,
                 fund=G ** (1 / yrs) - 1, yrs=yrs, final=pre, liq=liq)
        o['lead_at'] = o['at'] - o['fund_at']
        dn = pd.Series(dict(daily)); o['maxdd'] = float((sr / sr.cummax() - 1).min()); o['maxdd_daily'] = float((dn / dn.cummax() - 1).min())
        fd = pd.Series(s.xi[fa[0]:fa[-1] + 1]); o['fund_maxdd_daily'] = float((fd / fd.cummax() - 1).min()); o['min_value_daily'] = float(dn.min())
        o['orders_yr'] = ntr / yrs; o['brokerage_yr'] = brk / yrs; o['spread_yr'] = spr / yrs; o['tax_total'] = tax + fin
        ep = pd.DataFrame(pos).groupby('hid').pnl.sum().sort_values(ascending=False).values if pos else np.array([])
        o['n_holdings_closed'] = len(ep)
        for q in (1, 3, 5): o['at_wo%d' % q] = (max(liq - (1 - TAX) * ep[:q].sum(), 1.0) / CAPITAL) ** (1 / yrs) - 1
        o['top5_share_of_wins'] = float(ep[:5].sum() / ep[ep > 0].sum()) if (ep > 0).any() else np.nan
        o['win'] = float((ep > 0).mean()) if len(ep) else np.nan
        o['days_held_median'] = float(np.median([p['days'] for p in pos])) if pos else np.nan
        o['avg_held'] = float(np.mean(heldn)) if heldn else np.nan; o['avg_cash'] = float(np.mean(cashs)) if cashs else np.nan
        o['open_at_end'] = openp; o['zero_payouts'] = int(sum(p['why'].endswith('_zero') for p in pos)); o['refused'] = refused
        if detail: o['nav'] = sr; o['nav_daily'] = dn; o['fund_nav'] = bm / bm.iloc[0] * CAPITAL; o['pos'] = pos
        return o
