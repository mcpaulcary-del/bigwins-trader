"""H82 engine, blind re-implementation of rules v1.1 (parts A-H) + v1.2 (I, J, M).
Usage (library): run_account(src, capital, start, end, review_month, mode) -> dict
  mode: 'bc' before costs, 'ac' after costs, 'A' / 'B' after tax regime A / B
"""
import math
import numpy as np, pandas as pd

BASE = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
OUT = f'{BASE}/bigwins_forward/out/rep13'
DF = f'{BASE}/data_foundation/out'
FAILKW = ['liquidat', 'administrat', 'receiver', 'wound', 'listing fee', 'deed of company', '17.12', '17.15',
          'failure to pay', 'insolven']

_cache = {}


def load(src):
    if src in _cache:
        return _cache[src]
    w = np.load(f'{OUT}/wide_{src}.npz')
    P = w['P']; D = w['D']
    meta = pd.read_csv(f'{OUT}/cols_{src}.csv', parse_dates=['first', 'last'])
    dates = pd.DatetimeIndex(pd.read_csv(f'{OUT}/dates_{src}.csv').iloc[:, 0])
    sig = dict(np.load(f'{OUT}/sig_{src}.npz'))
    has = ~np.isnan(P)
    lastidx = np.array([np.where(has[:, j])[0].max() if has[:, j].any() else -1 for j in range(P.shape[1])])
    Pl = pd.DataFrame(P).ffill().values
    # A5 industry group by last-traded code
    g = pd.read_csv(f'{BASE}/company_study/data/asx/ASXListedCompanies.csv', skiprows=2)
    g.columns = ['name', 'code', 'grp']
    gm = dict(zip(g.code, g.grp))
    grp = []
    for c in meta.code:
        x = gm.get(c)
        grp.append(None if (x is None or x in ('Not Applic', 'Class Pend') or pd.isna(x)) else x)
    # C1 f per column
    dl = pd.read_pickle(f'{BASE}/company_study/data/delist.pkl')
    f = np.ones(P.shape[1])
    for j in range(P.shape[1]):
        if lastidx[j] < 0:
            continue
        ld = dates[lastidx[j]]
        r = dl[(dl.code == meta.code[j]) & (dl.date >= ld - pd.Timedelta(days=30)) & (dl.date <= ld + pd.Timedelta(days=1500))]
        if len(r):
            reason = str(r.sort_values('date').iloc[0].reason).lower()
            if any(k in reason for k in FAILKW):
                f[j] = 0.0
    # index
    axjo = pd.read_pickle(f'{OUT}/axjo.pkl')
    if src == 'v2':
        iv = pd.read_pickle(f'{DF}/index_v2.pkl')
        pr = iv.xjo.copy(); st = iv.xjo_ffill.astype(bool)
        pr[st] = axjo.reindex(pr.index)[st]
        PR = pr.reindex(pr.index.union(dates)).ffill().reindex(dates)
    else:
        PR = axjo.reindex(axjo.index.union(dates)).ffill().reindex(dates)
    ADD = f'{BASE}/actuals/data/derived'
    nav = pd.read_csv(f'{ADD}/vanguard_nav_daily.csv', index_col=0, parse_dates=True).VAS.dropna()
    dist = pd.read_csv(f'{ADD}/dist_VAS.csv', parse_dates=['ex']).groupby('ex').cash.sum()
    vret = (nav + dist.reindex(nav.index).fillna(0)) / nav.shift() - 1
    bs = pd.read_csv(f'{ADD}/betashares_total_return_index_daily.csv', index_col=0, parse_dates=True).A200.dropna()
    bret = bs.pct_change()
    cut = pd.Timestamp('2018-05-08')   # v1.3 J1: VAS supplies the return of 7 May 2018; A200 index changes from 8 May
    trr = pd.concat([vret[vret.index < cut], bret[bret.index >= cut]]).dropna()
    TRI = (1 + trr).cumprod()
    TR = TRI.reindex(TRI.index.union(dates)).ffill().reindex(dates)
    me_pos = {int(it): k for k, it in enumerate(sig['me_idx'])}
    d = dict(P=P, D=D, Pl=Pl, has=has, lastidx=lastidx, meta=meta, dates=dates, sig=sig, grp=grp, f=f,
             PR=PR.values, TR=TR.values, me_pos=me_pos, codes=list(meta.cid))
    _cache[src] = d
    return d


def brok(v, on):
    return max(6.60, 0.00088 * v) if on else 0.0


def tickf(p):
    return 0.001 if p < 0.10 else (0.005 if p < 2.00 else 0.01)


def run_account(src, capital, start, end, review_month=12, mode='B', divs=None, record=False):
    X = load(src)
    P, D, Pl, has, lastidx, dates, sig, grp, fpay = X['P'], X['D'], X['Pl'], X['has'], X['lastidx'], X['dates'], X['sig'], X['grp'], X['f']
    costs = mode != 'bc'
    tax_on = mode in ('A', 'B')
    dd = 0.5 if mode == 'A' else 0.0
    if divs is None:
        divs = (src == 'eod')
    i0 = dates.get_loc(pd.Timestamp(start)); i1 = dates.get_loc(pd.Timestamp(end))
    me_pos = X['me_pos']
    me_list = sorted(me_pos.keys())
    me_set = set(me_list)

    def rank_before(i, own=False):
        # traded-value rank at the most recent month-end strictly before day i (or i itself if own and month-end)
        if own and i in me_set:
            return sig['rank'][me_pos[i]]
        k = np.searchsorted(me_list, i) - 1
        return sig['rank'][me_pos[me_list[k]]]

    def half_spread(j, price, rk):
        if not costs:
            return 0.0
        r = rk[j]
        base = 0.001 if 1 <= r <= 100 else (0.0025 if 101 <= r <= 300 else 0.005)
        return max(base, 0.5 * tickf(price) / price)

    cash = float(capital)
    H = {}          # j -> {'lots': [[shares, cost, day]], 'await': bool}
    sells = []      # dicts: j, kind ('full'|'trim'), shares, day
    buys = []       # [j, A, state] state: 'open'|'done'
    topups = []     # [j, amount]
    topups_done = True
    E = None
    # tax state
    st_g = lt_g = loss = 0.0; cf = 0.0; dv = 0.0
    n = None; T = None
    nav_me = []     # (day, nav)
    sold_value = 0.0; ntrades = 0
    positions = []  # closed positions (G6): j, entry, exit, cost, proceeds
    pos_acc = {}    # j -> [entry_day, cost_total, proceeds_total]
    log_trades = []
    taxlog = []
    hold_log = []

    def tax_now():
        if not tax_on:
            return 0.0
        L = loss + cf
        st = max(0.0, st_g - L); Lr = max(0.0, L - st_g)
        lt = max(0.0, lt_g - Lr)
        return 0.32 * (st + lt * (1 - dd)) + 0.32 * dv

    def realise(j, shares, proceeds, day):
        nonlocal st_g, lt_g, loss
        lots = H[j]['lots']; rem = shares
        while rem > 0 and lots:
            lot = lots[0]
            q = min(rem, lot[0])
            c = lot[1] * q / lot[0]
            pr = proceeds * q / shares
            g = pr - c
            if g >= 0:
                if (dates[day] - dates[lot[2]]).days >= 367:
                    lt_g += g
                else:
                    st_g += g
            else:
                loss += -g
            lot[1] -= c; lot[0] -= q; rem -= q
            if lot[0] == 0:
                lots.pop(0)
        pos_acc[j][2] += proceeds
        if not lots:
            pa = pos_acc.pop(j)
            positions.append(dict(j=j, entry=pa[0], exit=day, cost=pa[1], proceeds=pa[2]))
            del H[j]

    def sh(j):
        return sum(l[0] for l in H[j]['lots'])

    def nav_at(i):
        return cash + sum(sh(j) * Pl[i, j] for j in H)

    def do_buy(j, a, i, rk):
        nonlocal cash, ntrades
        px = P[i, j]
        h = half_spread(j, px, rk)
        s = math.floor((a - brok(a, costs)) / (px * (1 + h)))
        if s <= 0:
            return False
        paid = s * px * (1 + h) + brok(s * px, costs)
        cash -= paid; ntrades += 1
        if j in H:
            H[j]['lots'].append([s, paid, i]); pos_acc[j][1] += paid
        else:
            H[j] = {'lots': [[s, paid, i]], 'await': False}; pos_acc[j] = [i, paid, 0.0]
        if record:
            log_trades.append((dates[i].date(), X['codes'][j], 'buy', s, px, -paid))
        return True

    def payout(j, i):
        nonlocal cash, sold_value
        s = sh(j); v = s * P[lastidx[j], j] * fpay[j]
        cash += v; sold_value += s * P[lastidx[j], j] * fpay[j]
        if record:
            log_trades.append((dates[i].date(), X['codes'][j], 'payout', s, P[lastidx[j], j] * fpay[j], v))
        realise(j, s, v, i)

    def close_year():
        nonlocal st_g, lt_g, loss, cf, dv, cash
        t = tax_now()
        L = loss + cf
        Lr = max(0.0, L - st_g)
        cf = max(0.0, Lr - lt_g)
        cash -= t
        st_g = lt_g = loss = 0.0; dv = 0.0
        return t

    def walk_targets(k, nn, TT, start_counts=None, exclude=None, limit=None):
        sc = sig['score'][k]; rk = sig['rank'][k]; med = sig['med'][k]; c10 = sig['c10'][k]
        cand = np.where(~np.isnan(sc))[0]
        order = cand[np.lexsort((rk[cand], -sc[cand]))]
        cap = math.ceil(0.25 * nn)
        cnt = dict(start_counts or {})
        out = []
        for j in order:
            if len(out) >= limit:
                break
            if not (c10[j] >= 0.50 and med[j] >= 100 * TT):
                continue
            if exclude is not None and j in exclude:
                continue
            g = grp[j]
            if g is not None and cnt.get(g, 0) >= cap:
                continue
            out.append(j)
            if g is not None:
                cnt[g] = cnt.get(g, 0) + 1
        return out

    for i in range(i0, i1 + 1):
        is_me = i in me_set
        rk = rank_before(i)
        # I9 dividends
        if divs and i > i0:
            for j in list(H):
                if D[i, j] > 0:
                    v = sh(j) * D[i, j]
                    cash += v; dv += v
        # sells
        executed = 0
        if i > i0:
            keep = []
            for s in sells:
                j = s['j']
                if j not in H:
                    continue
                if i < s['day'] or not has[i, j]:
                    keep.append(s); continue
                px = P[i, j]
                q = sh(j) if s['kind'] == 'full' else min(s['shares'], sh(j))
                h = half_spread(j, px, rk)
                rec = max(0.0, q * px * (1 - h) - brok(q * px, costs))
                cash += rec; sold_value += q * px; ntrades += 1; executed += 1
                if record:
                    log_trades.append((dates[i].date(), X['codes'][j], s['kind'], q, px, rec))
                realise(j, q, rec, i)
            sells = keep
        # buys / top-ups on attempt days
        if i > i0 and E is not None and (i == E or executed > 0) and i <= (next_me if next_me is not None else i):
            waiting = False
            for b in buys:
                if b[2] != 'open':
                    continue
                j, A = b[0], b[1]
                a = min(A, cash - tax_now())
                if a < max(1000.0, 0.5 * A):
                    waiting = True; continue
                if not has[i, j]:
                    b[2] = 'drop'; continue
                do_buy(j, a, i, rk)
                b[2] = 'done'
            if not waiting and not topups_done:
                for j, amt in topups:
                    a = min(amt, cash - tax_now())
                    if a >= 1000 and j in H and not H[j]['await'] and has[i, j]:
                        do_buy(j, a, i, rk)
                topups_done = True
        if record and i > i0 and (i - 1) in me_set:
            hold_log.append((i, sorted(H.keys())))
        if i == i1:
            break
        if not is_me:
            continue
        # ---- month-end decisions (section C) ----
        k = me_pos[i]
        buys = []; topups = []; topups_done = True
        # C1 payouts
        for j in list(H):
            if i - lastidx[j] >= 20:
                payout(j, i)
                sells = [s for s in sells if s['j'] != j]
        nav = nav_at(i)
        nav_me.append((i, nav))
        if dates[i].month == 6 and i > i0:
            taxlog.append((str(dates[i].date()), st_g, lt_g, loss, cf, dv, close_year()))
            nav = nav_at(i)
        review = (i == i0) or (dates[i].month == review_month)
        if review:
            n = min(30, max(4, math.floor(nav / 2500)))
        T = nav / n
        E = i + 1
        nm = [m for m in me_list if m > i]
        next_me = nm[0] if nm else None
        awaiting = {j for j in H if H[j]['await']}
        live = [j for j in H if not H[j]['await']]
        if review:
            targ = walk_targets(k, n, T, limit=n)
            tset = set(targ)
            for j in live:
                if j in tset:
                    continue
                # C5 sell, C6 deferral
                day = E
                val = sh(j) * Pl[i, j]
                if val > sum(l[1] for l in H[j]['lots']):
                    qs = []
                    for l in H[j]['lots']:
                        due = dates[l[2]] + pd.Timedelta(days=367)
                        q = max(E, int(np.searchsorted(dates.values, np.datetime64(max(due, dates[E])))))
                        if q > E and (dates[min(q, len(dates) - 1)] - dates[E]).days <= 31:
                            qs.append(q)
                    if qs:
                        day = max(qs)
                sells = [s for s in sells if s['j'] != j]
                sells.append(dict(j=j, kind='full', shares=None, day=day))
                H[j]['await'] = True
            cands = []
            for j in live:
                if j not in tset:
                    continue
                val = sh(j) * Pl[i, j]
                if val - 2 * T >= 1000:
                    q = math.floor((val - 2 * T) / Pl[i, j])
                    if q > 0:
                        sells.append(dict(j=j, kind='trim', shares=q, day=E))
                elif val < 0.75 * T and T - val >= 1000:
                    cands.append((val / T, j, T - val))
            cands.sort()
            topups = [[j, amt] for _, j, amt in cands]
            topups_done = len(topups) == 0
            buys = [[j, T, 'open'] for j in targ if j not in H]
        else:
            nlive = len(live)
            if nlive < n:
                counts = {}
                for j in live:
                    if grp[j] is not None:
                        counts[grp[j]] = counts.get(grp[j], 0) + 1
                new = walk_targets(k, n, T, start_counts=counts, exclude=set(H), limit=n - nlive)
                buys = [[j, T, 'open'] for j in new]
    # ---- G1 final liquidation at end date ----
    nav_end = nav_at(i1)
    rk = rank_before(i1, own=True)
    for j in list(H):
        if i1 - lastidx[j] >= 20:
            payout(j, i1)
        else:
            px = Pl[i1, j]; q = sh(j)
            h = half_spread(j, px, rk)
            rec = max(0.0, q * px * (1 - h) - brok(q * px, costs))
            cash += rec
            realise(j, q, rec, i1)
    tax_final = tax_now(); cash -= tax_final
    years = (dates[i1] - dates[i0]).days / 365.25
    res = dict(src=src, capital=capital, start=str(dates[i0].date()), end=str(dates[i1].date()), review_month=review_month,
               mode=mode, final=cash, cagr=(cash / capital) ** (1 / years) - 1, years=years, trades=ntrades,
               nav_end_before_liq=nav_end)
    me_days = [x[0] for x in nav_me] + ([i1] if i1 not in set(x[0] for x in nav_me) else [])
    navs = [x[1] for x in nav_me] + ([nav_end] if i1 not in set(x[0] for x in nav_me) else [])
    res['nav_series'] = (me_days, navs)
    res['turnover'] = sold_value / np.mean(navs) / years
    res['positions'] = positions
    res['taxlog'] = taxlog + [('final', st_g, lt_g, loss, cf, dv, tax_final)]
    if record:
        res['trades_log'] = log_trades
        res['hold_log'] = hold_log
    return res


def comparator(src, capital, start, end, mode, kind='G3'):
    """G3 (price index, buy at close of day after start) or J3 (TR comparator)."""
    X = load(src); dates = X['dates']
    i0 = dates.get_loc(pd.Timestamp(start)); i1 = dates.get_loc(pd.Timestamp(end))
    costs = mode != 'bc'; tax_on = mode in ('A', 'B'); dd = 0.5 if mode == 'A' else 0.0
    tau = 0.32 if tax_on else 0.0
    PR = X['PR']; TR = X['TR']
    hs = 0.0003 if costs else 0.0
    years = (dates[i1] - dates[i0]).days / 365.25
    if kind == 'G3':
        ib = i0 + 1
        units = (capital - brok(capital, costs)) / (PR[ib] * (1 + hs))
        gross = units * PR[i1]
        net = gross * (1 - hs) - brok(gross, costs)
        tax = tau * (1 - dd) * max(0.0, net - capital)
        fin = net - tax
        navs = [capital] + [units * PR[i] for i in range(i0 + 1, i1 + 1)]
    else:
        ib = i0 + 1
        v = (capital - brok(capital, costs)) / (1 + hs)
        cb = float(capital)
        for i in range(ib + 1, i1 + 1):
            prc = PR[i] / PR[i - 1] - 1
            trc = TR[i] / TR[i - 1] - 1
            y = trc - prc
            add = v * y * (1 - tau)
            v = v * (1 + prc) + add
            cb += add
        net = v * (1 - hs) - brok(v, costs)
        tax = tau * (1 - dd) * max(0.0, net - cb)
        fin = net - tax
    return dict(final=fin, cagr=(fin / capital) ** (1 / years) - 1)
