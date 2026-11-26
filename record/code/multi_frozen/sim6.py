# Round 6: sim5.py + ONE switch `wext` (external target weights mk.wext[k], e.g. point-in-time market cap x tilt; used with wnorm=True). Trial ledger -> improve6/out/trials_77.csv.
# Report 75 (round 4) engine = report 73's sim.py + weighted targets (cap proxy x tilt), loss harvest, cooling-off, brokerage tiers.
# Report 73 generic engine: decision-date simulator on a "pack" (see packlib). Same code for ASX development and fresh markets.
import math, json, os, time, numpy as np, pandas as pd
import packlib as PL
S_ = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
OUT = S_ + '/improve6/out'
TAU = 0.32
_cpi = None
def cpi_at(d):
    """AU CPI index (quarterly, ABS) for a date; used by regime AN."""
    global _cpi
    if _cpi is None:
        _cpi = pd.read_csv(S_ + '/improve/data/cpi_q.csv', parse_dates=['date']).set_index('date')['cpi']
    j = _cpi.index.searchsorted(pd.Timestamp(d), side='right') - 1
    return float(_cpi.iloc[max(j, 0)])

class Mkt:
    def __init__(self, path, U=300, tick='asx', px_scale=1.0, lo=0):
        pk = PL.load_pack(path); self.pk = pk; self.U = U
        self.above = None; self.vrank0 = pk['vrank'].copy()
        if lo:                                   # traded-value band: ranks lo+1 .. lo+U become ranks 1..U
            with np.errstate(invalid='ignore'): self.above = pk['vrank'] <= lo      # traded more than the band's top: a holding is not sold for that alone
            pk['vrank'] = np.where(pk['vrank'] > lo, pk['vrank'] - lo, np.nan).astype(np.float32)
        self.dd = pd.DatetimeIndex(pk['dec_dates']); self.K, self.N = pk['px'].shape
        self.px = pk['px'].astype(np.float64); self.pe = pk['pe'].astype(np.float64); self.age = pk['age']
        self.vrank = pk['vrank']; self.s4 = pk['s4'].astype(np.float64); self.medtv = pk['medtv'].astype(np.float64); self.divy = np.nan_to_num(pk['divy'].astype(np.float64))
        rc = pk['rc'].astype(np.float64) * px_scale
        with np.errstate(invalid='ignore', divide='ignore'):
            self.uni = self.vrank <= U
            base = np.where(self.vrank <= 100, 0.001, np.where(self.vrank <= 300, 0.0025, 0.005))
            tk = np.where(rc < 0.10, 0.001, np.where(rc < 2.0, 0.005, 0.01))
            self.hs = np.maximum(base, np.where(np.isfinite(rc) & (rc > 0), 0.5 * tk / rc, 0.005)) if tick == 'asx' else base
            self.rc = rc
        # payout index: first decision date at least 20 trading days after the last close in the whole file (never if the stock trades to the end)
        lastc = pk['lastc']; T = int(pk['T']); di = pk['dec_idx']
        self.pay_k = np.full(self.N, 10 ** 9, np.int64)
        for n in range(self.N):
            if lastc[n] >= 0 and lastc[n] < T - 1:
                j = np.searchsorted(di, lastc[n] + 20, side='left')
                if j < self.K: self.pay_k[n] = j
        self.fail = pk['fail'].astype(bool) if 'fail' in pk and pk['fail'].dtype != object else np.zeros(self.N, bool)
        self.take = pk['take'].astype(bool) if 'take' in pk and pk['take'].dtype != object else np.zeros(self.N, bool)
        self.idx = pk['idx'].astype(np.float64) if 'idx' in pk else None            # price index at decision dates
        self.idx_tr = pk['idx_tr'].astype(np.float64) if 'idx_tr' in pk else None   # total-return index at decision dates
        if self.idx_tr is None or not np.isfinite(self.idx_tr).any(): self.idx_tr = self.idx.copy()
        self.idx_e = pk['idx_tr_e'].astype(np.float64) if 'idx_tr_e' in pk and np.isfinite(pk['idx_tr_e'].astype(np.float64)).any() else pk['idx_e'].astype(np.float64)
        self.pct = {}; self.scores = {}; self.ranks = {}
        self.cols = pk['cols'] if 'cols' in pk else np.arange(self.N)
    def P(self, f):
        """percentile of feature f inside the universe (smallest = lowest), NaN outside / missing"""
        if f not in self.pct: self.pct[f] = self.pct_of(self.pk[f].astype(np.float64))
        return self.pct[f]
    def pct_of(self, x):
        o = np.full(x.shape, np.nan)
        for k in range(self.K):
            m = self.uni[k] & np.isfinite(x[k])
            if m.sum() > 0:
                o[k, m] = pd.Series(x[k, m]).rank(method='average').values / m.sum()
                if self.above is not None:          # names traded more than the band's top: percentile read against the band's distribution (holdings only; never bought)
                    e = self.above[k] & np.isfinite(x[k])
                    if e.any(): o[k, e] = np.searchsorted(np.sort(x[k, m]), x[k, e], side='right') / m.sum()
        return o
    def H80(self):
        if 'H80' not in self.scores: self.scores['H80'] = (self.P('s1') + self.P('s2') + self.P('s3') + self.P('s4')) / 4.0
        return self.scores['H80']
    def rank(self, name, sc=None):
        """score rank inside the universe: 1 = best; ties in traded-value-rank order; NaN = unranked"""
        if name in self.ranks and sc is None: return self.ranks[name]
        if sc is None: sc = self.scores[name]
        r = np.full(sc.shape, np.nan)
        for k in range(self.K):
            m = np.flatnonzero(self.uni[k] & np.isfinite(sc[k]))
            if len(m) == 0: continue
            o = np.lexsort((self.vrank[k, m], -sc[k, m])); r[k, m[o]] = np.arange(1, len(m) + 1)
            if self.above is not None:
                e = np.flatnonzero(self.above[k] & np.isfinite(sc[k]))
                if len(e): srt = np.sort(sc[k, m]); r[k, e] = 1 + len(m) - np.searchsorted(srt, sc[k, e], side='right')
        self.ranks[name] = r; self.scores[name] = sc
        return r
    def kof(self, date):
        return int(self.dd.searchsorted(pd.Timestamp(date), side='right') - 1)

BROK = dict(std=(6.60, 0.00088), low=(3.0, 0.0001))
def brok(v): return max(6.60, 0.00088 * v)

DEF = dict(form='band', nmax=30, nmin=4, minpos=2500.0, B=30, H=90, kconf=2, review=None, tc_from=300, tc_rank=0.7, june=True, swap=False, taxw=1.0,
           trim=True, gamma=None, tilt_a=0.0, mclip=(0.5, 2.5), wcapb=0.10, buy_order='rank', wnorm=False, wmax=0.20, harvest=None, hmin=0.05, cool=0, defer_all=False, broker='std', core_w=0.0, core_min_sat=None, core_until=None, defer_monthly=False, buy_tax=0.0, minorder=1000.0, pmin=0.50, liqx=100.0, topup=True, minhold=0, mer=0.0010, core_hs=0.0003, cadence=1, ivw=0.0, core_dyn=None, core_rebal=False, wext=False)

def run(mk, rank, S0, k0, k1, tau=0.0, regime='CL', costs=True, contrib=0.0, payf=1.0, frank=None, placebo=None, rng=None, track=False, cost_mult=1.0, **kw):
    """One account from decision index k0 (cash) to k1 (liquidated). rank: (K,N) score ranks (1 = best) or None when core only.
    placebo: dict(nsell=array over k) -> matched random buy/sell control. Returns dict."""
    p = dict(DEF); p.update(kw)
    bmin, brate = BROK[p['broker']]
    brok = lambda v: max(bmin, brate * v)
    barred = {}; nharv = 0; cashw = []; nheld = []
    U = mk.U; px = mk.px; pe = mk.pe; hs = mk.hs; dd = mk.dd
    cm = cost_mult if costs else 0.0
    cash = float(S0); paid_in = float(S0)
    H = {}                       # n -> dict(lots=[[date, shares, cost]], below=int)
    core = []                    # lots of the index fund [date, units, cost]
    carry = 0.0; fy = dict(st=0.0, lt=0.0, ltraw=0.0, loss=0.0, div=0.0, divc=0.0)
    taxpaid = 0.0; costpaid = 0.0; ntr = 0; sold_val = 0.0
    navs = []; nsell = np.zeros(mk.K, int); closed = []; entries = []; pos_open = {}
    n = None; core_only = False
    def taxdue():
        if tau == 0: return 0.0
        st, lt, loss = fy['st'], fy['lt'], fy['loss'] + carry
        a = min(st, loss); st -= a; loss -= a; a = min(lt, loss); lt -= a
        d = 0.5 if regime == 'CL' else 0.0
        t = tau * (st + lt * (1 - d))
        if frank is None: t += tau * fy['div']
        else:
            cr = fy['div'] * frank * 30.0 / 70.0; t += tau * (fy['div'] + cr) - cr
        t += tau * fy['divc']
        return t
    def close_fy():
        nonlocal carry, cash, taxpaid
        t = taxdue()
        st, lt, loss = fy['st'], fy['lt'], fy['loss'] + carry
        a = min(st, loss); st -= a; loss -= a; a = min(lt, loss); loss -= a
        carry = loss; cash -= t; taxpaid += t
        for q in fy: fy[q] = 0.0
    def realise(lots, shares, proceeds, date, hc_first=False):
        """sell `shares` from lots (oldest first; or long-term highest-cost first for trims); books gains"""
        tot = sum(l[1] for l in lots); rem = shares
        order = list(range(len(lots)))
        if hc_first:
            lt_ = [i for i in order if (date - lots[i][0]).days >= 367]; lt_.sort(key=lambda i: -lots[i][2] / max(lots[i][1], 1e-12))
            order = lt_ + [i for i in order if i not in lt_]
        for i in order:
            if rem <= 1e-12: break
            l = lots[i]; q = min(l[1], rem); pr = proceeds * q / shares; c = l[2] * q / l[1]
            longt = (date - l[0]).days >= 367
            g = pr - c
            if g < 0: fy['loss'] += -g
            elif longt:
                if regime == 'AN': fy['lt'] += max(0.0, pr - c * cpi_at(date) / cpi_at(l[0]))
                else: fy['lt'] += g
            else: fy['st'] += g
            l[1] -= q; l[2] -= c; rem -= q
        lots[:] = [l for l in lots if l[1] > 1e-12]
    def sell(nn, k, shares=None, price=None, payout=None, hc=False):
        nonlocal cash, costpaid, ntr, sold_val
        h = H[nn]; tot = sum(l[1] for l in h['lots'])
        q = tot if shares is None else min(shares, tot)
        if q <= 0: return
        date = dd[k] + pd.Timedelta(days=1)
        if payout is not None: pr = q * px[k, nn] * payout
        else:
            v = q * price; c = v * hs[k, nn] * cm + (brok(v) * cm if costs else 0.0); pr = max(0.0, v - c); costpaid += v - pr; ntr += 1
        sold_val += pr
        if p['cool'] and pr < sum(l[2] for l in h['lots']) * q / max(tot, 1e-12): barred[nn] = k + p['cool']
        realise(h['lots'], q, pr, date, hc_first=hc); cash += pr
        pos_open[nn][1] += pr
        if not h['lots']:
            c0, p1, kb = pos_open.pop(nn); closed.append((nn, kb, k, c0, p1))
            del H[nn]
    def buy(nn, k, amount):
        nonlocal cash, costpaid, ntr
        price = pe[k, nn]
        if not np.isfinite(price) or price <= 0: return False
        h_ = hs[k, nn] * cm; b = brok(amount) * cm if costs else 0.0
        s = math.floor((amount - b) / (price * (1 + h_)))
        if s <= 0: return False
        v = s * price; b = brok(v) * cm if costs else 0.0; c = v * (1 + h_) + b + (v * p['buy_tax'] if costs else 0.0)
        cash -= c; costpaid += c - v; ntr += 1
        date = dd[k] + pd.Timedelta(days=1)
        if nn in H: H[nn]['lots'].append([date, s, c]); pos_open[nn][0] += c
        else: H[nn] = dict(lots=[[date, s, c]], below=0); pos_open[nn] = [c, 0.0, k]; entries.append((nn, k))
        return True
    def core_buy(k, amount):
        nonlocal cash, costpaid, ntr
        price = mk.idx_e[k]
        if not np.isfinite(price): price = mk.idx_tr[k]
        b = brok(amount) * cm if costs else 0.0; u = (amount - b) / (price * (1 + p['core_hs'] * cm))
        if u <= 0: return
        cash -= amount; costpaid += amount - u * price; ntr += 1
        core.append([dd[k] + pd.Timedelta(days=1), u, amount])
    def core_sell(k, amount):
        nonlocal cash, costpaid, ntr
        price = mk.idx_e[k]
        if not np.isfinite(price): price = mk.idx_tr[k]
        tot = sum(l[1] for l in core); u = min(tot, amount / price); v = u * price
        c = (brok(v) + v * p['core_hs']) * cm if costs else 0.0
        realise(core, u, v - c, dd[k] + pd.Timedelta(days=1)); cash += v - c; costpaid += c; ntr += 1
    def core_val(k): return sum(l[1] for l in core) * mk.idx_tr[k]
    def sat_val(k): return sum(sum(l[1] for l in h['lots']) * px[k, nn] for nn, h in H.items())
    lastk = k0
    for k in range(k0, k1 + 1):
        date = dd[k]
        # dividends accrued inside total-return prices since the previous decision date: booked as income (tax) and added to cost (reinvested)
        if k > k0:
            for nn, h in H.items():
                y = mk.divy[k, nn]
                if y > 0:
                    v0 = sum(l[1] for l in h['lots']) * px[k - 1, nn]; dv = v0 * y; fy['div'] += dv
                    h['lots'][0][2] += dv; pos_open[nn][0] += dv
            if core:
                # index fund: yield = TR/price - 1 over the period; MER deducted from units
                u = sum(l[1] for l in core)
                if getattr(mk, 'fund_y', None) is not None:        # accumulating fund: a distribution is imputed (taxed as income, added to cost), see lib4.load
                    dv = u * mk.idx_tr[k - 1] * float(mk.fund_y[k]); fy['div'] += dv; core[0][2] += dv
                elif mk.idx is not None and np.isfinite(mk.idx[k]) and np.isfinite(mk.idx[k - 1]):
                    y = (mk.idx_tr[k] / mk.idx_tr[k - 1]) / (mk.idx[k] / mk.idx[k - 1]) - 1
                    if 0 < y < 0.08:          # a larger gap between total-return and price change is a split of the fund, not a distribution
                        dv = u * mk.idx_tr[k - 1] * y
                        fy['div'] += dv
                        core[0][2] += dv
                f = (1 - p['mer']) ** ((dd[k] - dd[k - 1]).days / 365.25) if costs else 1.0
                for l in core: l[1] *= f
        # payouts
        for nn in list(H):
            if mk.pay_k[nn] <= k:
                f = 0.0 if mk.fail[nn] else (1.0 if (mk.take[nn] or payf == 1.0) else payf)
                sell(nn, k, payout=f)
        nav = cash + sat_val(k) + core_val(k); navs.append(nav); cashw.append(cash / max(nav, 1e-9)); nheld.append(len(H))
        if k == k1: break
        if date.month == 6 and k > k0 and tau > 0: close_fy()
        if contrib and k > k0: cash += contrib; paid_in += contrib
        nav = cash + sat_val(k) + core_val(k)
        free = lambda: cash - max(0.0, taxdue())
        # ---- core / satellite split
        cw = p['core_w']
        if p['core_dyn'] is not None and rank is not None:
            # round 5: fund share rises with index concentration: cw = core_w + (1 - core_w) x min(cap, a x share of the A most-traded names in the traded value of the 50 most traded)
            A_, a_, cap_ = p['core_dyn']
            with np.errstate(invalid='ignore'):
                vr0 = mk.vrank0[k]; t50 = np.nansum(np.where(vr0 <= 50, mk.medtv[k], 0.0)); tA = np.nansum(np.where(vr0 <= A_, mk.medtv[k], 0.0))
            cw = cw + (1 - cw) * min(cap_, a_ * tA / max(t50, 1e-12))
        if rank is None: cw = 1.0
        cw_eff = cw
        if cw < 1.0 and p['core_until'] is not None and not H:
            # small-account rule: index fund only until NAV >= core_until at a review month; then the fund is sold down to core_w and the engine starts
            if nav < p['core_until'] or not (p['review'] is None or date.month == p['review']): cw_eff = 1.0
            elif core:
                excess = core_val(k) - cw * nav
                if excess > p['minorder']: core_sell(k, excess)
        if cw_eff >= 1.0:
            a = free()
            if a >= (p['minorder'] if core else 0.0) and a > 10: core_buy(k, a)
            continue
        if cw_eff > 0:
            want = cw_eff * nav - core_val(k); a = min(want, free())
            if a >= p['minorder']: core_buy(k, a)
        navs_sat = nav - core_val(k)
        rk = rank[k]
        if p['cadence'] > 1 and date.month % p['cadence'] != 0 and H: continue      # round 5: decisions only every `cadence` months (after the first purchases)
        review = (p['review'] is None) or (date.month == p['review']) or n is None
        if review or p['form'] == 'band':
            n = int(min(p['nmax'], max(p['nmin'], math.floor(navs_sat / p['minpos']))))
        T = navs_sat / n
        if p['wext']:
            m_ = np.nan_to_num(mk.wext[k]); mraw = m_; mult = np.ones(len(m_))
        elif p['gamma'] is None and not p['tilt_a'] and not p['ivw']: mult = None
        else:
            # position multiplier m_i = (cap proxy share, capped)^gamma x (1 + a(2p-1)), scaled so that the buy zone (rank <= B, in universe) averages 1; clipped
            u_ = mk.uni[k] & np.isfinite(mk.medtv[k]); b_ = np.where(u_, mk.medtv[k], 0.0); tot_ = b_.sum()
            b_ = np.minimum(np.where(np.isfinite(mk.medtv[k]), mk.medtv[k], 0.0) / max(tot_, 1e-12), p['wcapb']) ** (p['gamma'] or 0.0)
            nr_ = max(int((u_ & np.isfinite(rk)).sum()), 1); pc_ = np.where(np.isfinite(rk), 1.0 - (rk - 1.0) / nr_, 0.0)
            m_ = b_ * np.maximum(0.0, 1.0 + p['tilt_a'] * (2.0 * pc_ - 1.0))
            if p['ivw']:
                sd_ = -mk.s4[k]; md_ = np.nanmedian(sd_[u_]) if np.isfinite(sd_[u_]).any() else 1.0
                m_ = m_ * np.where(np.isfinite(sd_) & (sd_ > 0), md_ / np.maximum(sd_, 1e-9), 1.0) ** p['ivw']
            bz_ = u_ & np.isfinite(rk) & (rk <= p['B'])
            mult = np.clip(m_ / max(m_[bz_].mean() if bz_.any() else 1.0, 1e-12), p['mclip'][0], p['mclip'][1])
            if p['wnorm']: mraw = m_; mult = np.ones(len(m_))        # targets are set after the sales, normalised over the names to be held (tmap)
        tmap = {}
        Tn = (lambda nn: T) if mult is None else (lambda nn: tmap.get(nn, T * mult[nn]))
        def eligible(nn):
            return (mk.uni[k, nn] and np.isfinite(rk[nn]) and np.isfinite(pe[k, nn]) and mk.age[k, nn] == 0 and mk.rc[k, nn] >= p['pmin'] and mk.medtv[k, nn] >= p['liqx'] * Tn(nn)
                    and barred.get(nn, -1) < k)
        sells = []; held = set(H)
        if placebo is not None:
            live = list(H); m = min(int(placebo['nsell'][k]), len(live))
            if m > 0:
                for nn in rng.choice(live, m, replace=False): sells.append((int(nn), None))
        else:
            for nn, h in H.items():
                r = rk[nn]; bad = (not np.isfinite(r)) or r > p['H']
                h['below'] = h['below'] + 1 if bad else 0
            if p['form'] == 'band' or review:
                if p['form'] == 'annual':
                    # target list: top n buy-eligible (holdings count if they have a score); holdings outside the hold line H are sold
                    cands = [nn for nn, h in H.items() if h['below'] >= 1]
                else:
                    cands = [nn for nn, h in H.items() if h['below'] >= p['kconf']]
                for nn in cands:
                    h = H[nn]; val = sum(l[1] for l in h['lots']) * px[k, nn]; cost = sum(l[2] for l in h['lots'])
                    agedays = (date - h['lots'][0][0]).days
                    r = rk[nn]
                    if val > cost and agedays < 366 and (p['defer_all'] or (p['tc_from'] <= agedays and np.isfinite(r) and r <= p['tc_rank'] * U)):
                        if p['defer_monthly']: h['pend'] = True
                        continue
                    if agedays < p['minhold'] and val > cost: continue
                    sells.append((nn, r if np.isfinite(r) else 10 ** 6))
            if p['defer_monthly'] and not (p['form'] == 'band' or review):
                for nn, h in H.items():          # sales deferred at a review for the 12-month mark: executed at the first later decision date with age >= 366 days
                    if h.get('pend') and (date - h['lots'][0][0]).days >= 366:
                        sells.append((nn, rk[nn] if np.isfinite(rk[nn]) else 10 ** 6)); h['pend'] = False
            if p['june'] and date.month in (5,) and p['form'] == 'band':
                for nn, h in H.items():
                    if h['below'] >= 1 and nn not in [s[0] for s in sells]:
                        val = sum(l[1] for l in h['lots']) * px[k, nn]; cost = sum(l[2] for l in h['lots'])
                        if val <= cost: sells.append((nn, rk[nn] if np.isfinite(rk[nn]) else 10 ** 6))
            if p['harvest'] == 'may' and date.month == 5 and tau > 0:
                # loss harvest: only against net gains already realised this tax year; largest loss first; replacement by the standing buy rule; sold name barred `cool` months
                need = fy['st'] + fy['lt'] - fy['loss'] - carry; insell = set(s_[0] for s_ in sells)
                for nn in insell:
                    h = H[nn]; need -= sum(l[1] for l in h['lots']) * px[k, nn] - sum(l[2] for l in h['lots'])
                cl_ = []
                for nn, h in H.items():
                    if nn in insell or not np.isfinite(pe[k, nn]): continue
                    val = sum(l[1] for l in h['lots']) * px[k, nn]; cost = sum(l[2] for l in h['lots'])
                    if cost - val >= max(200.0, p['hmin'] * cost): cl_.append((cost - val, nn))
                for ls, nn in sorted(cl_, reverse=True):
                    if need <= 0: break
                    sells.append((nn, rk[nn] if np.isfinite(rk[nn]) else 10 ** 6)); need -= ls; nharv += 1
        # replacement candidates
        if placebo is not None:
            pool = [nn for nn in np.flatnonzero(mk.uni[k]) if nn not in held and eligible(nn)]
            rng.shuffle(pool); buys_pool = pool
        else:
            order = np.argsort(np.where(np.isfinite(rk), rk, 1e9)); buys_pool = []
            for nn in order:
                if not np.isfinite(rk[nn]) or rk[nn] > p['B']: break
                if nn not in held and eligible(nn): buys_pool.append(int(nn))
            if p['buy_order'] == 'weight' and mult is not None: buys_pool.sort(key=lambda nn: -mult[nn])
        # swap test (optional): a candidate is sold only if a replacement exists and expected gain >= 2 x cost (tax weight taxw)
        if p['swap'] and placebo is None:
            keep = []; bi = 0
            for nn, r in sorted(sells, key=lambda x: -x[1]):
                if bi >= len(buys_pool): continue
                R = buys_pool[bi]; h = H[nn]; V = sum(l[1] for l in h['lots']) * px[k, nn]
                nr = np.isfinite(rk).sum(); pc = lambda x: 1 - (x - 1) / nr if np.isfinite(x) and x < 10 ** 6 else 0.0
                EG = 0.5 * 0.20 * (pc(rk[R]) - pc(r))
                gs = sum(l[1] * px[k, nn] - l[2] for l in h['lots'] if (date - l[0]).days < 367); gl = sum(l[1] * px[k, nn] - l[2] for l in h['lots'] if (date - l[0]).days >= 367)
                taxnow = TAU * max(0.0, gs + 0.5 * gl) if gl > 0 else TAU * max(0.0, gs + gl)
                COST = (brok(V) + brok(T) + hs[k, nn] * V + hs[k, R] * T + p['taxw'] * taxnow) / max(V, 1e-9)
                if EG >= 2 * COST: keep.append((nn, r)); bi += 1
            sells = keep
        # execute at next-day close: sells, then buys
        for nn, r in sells:
            price = pe[k, nn]
            if not np.isfinite(price): price = None
            if price is None:
                continue              # no close next day: stays (re-decided next date or paid out)
            sell(nn, k, price=price); nsell[k] += 1
        if p['wnorm'] and mult is not None:
            # weighted book: names to hold = holdings + the first (n - holdings) candidates; weights = proxy x tilt, normalised over them, capped at wmax; a new name below the minimum order is left out
            Sset = list(H) + [nn for nn in buys_pool if nn not in H][:max(0, n - len(H))]
            for _ in range(3):
                mm = np.array([mraw[nn] for nn in Sset], float)
                if len(Sset) == 0 or mm.sum() <= 0: w_ = np.ones(len(Sset)) / max(len(Sset), 1); break
                w_ = mm / mm.sum()
                for _c in range(6):
                    ov = w_ > p['wmax'] + 1e-12
                    if not ov.any() or ov.all(): break
                    w_[ov] = p['wmax']; fixed = w_ >= p['wmax'] - 1e-12; w_[~fixed] *= (1 - fixed.sum() * p['wmax']) / max(w_[~fixed].sum(), 1e-12)
                drop = set(nn for nn, wi in zip(Sset, w_) if wi * navs_sat < p['minorder'] and nn not in H)
                if not drop: break
                Sset = [nn for nn in Sset if nn not in drop]
            tmap = {nn: float(wi * navs_sat) for nn, wi in zip(Sset, w_)}; buys_pool = [nn for nn in Sset if nn not in H]
        # trims
        if p['trim'] and placebo is None:
            for nn in list(H):
                h = H[nn]; sh = sum(l[1] for l in h['lots']); val = sh * px[k, nn]
                if val > max(0.15 * navs_sat, 2 * Tn(nn)) and np.isfinite(pe[k, nn]):
                    q = math.floor((val - max(0.10 * navs_sat, 4 * Tn(nn) / 3)) / px[k, nn])
                    if q > 0: sell(nn, k, shares=q, price=pe[k, nn], hc=True)
        vac = n - len(H)
        for nn in buys_pool:
            if vac <= 0: break
            if mult is not None and Tn(nn) < p['minorder']: continue          # weighted book: a name whose target is below the minimum order is skipped, not a stop
            a = min(Tn(nn), free())
            if a < max(p['minorder'], 0.5 * Tn(nn)): break
            if buy(nn, k, a): vac -= 1
        if p['topup'] and placebo is None and (len(H) >= n or mult is not None):
            sc_ = 1.0
            if mult is not None and H:      # weighted book: targets of the names held are scaled up so that they add to the book (no idle cash)
                sc_ = max(1.0, navs_sat / max(sum(Tn(nn) for nn in H), 1e-9))
            und = sorted([(sum(l[1] for l in h['lots']) * px[k, nn] / (sc_ * Tn(nn)), sum(l[1] for l in h['lots']) * px[k, nn], nn) for nn, h in H.items() if np.isfinite(rk[nn]) and rk[nn] <= p['H'] and np.isfinite(pe[k, nn])])
            for _, val, nn in und:
                a = min(sc_ * Tn(nn) - val, free())
                if val < 0.75 * sc_ * Tn(nn) and a >= p['minorder']: buy(nn, k, a)
    # final liquidation at k1
    k = k1
    for nn in list(H):
        if np.isfinite(px[k, nn]): sell(nn, k, price=px[k, nn])
    if core:
        u = sum(l[1] for l in core); v = u * mk.idx_tr[k]; c = (brok(v) + v * p['core_hs']) * cm if costs else 0.0
        pr = v - c; costpaid += c
        dummy = dict(lots=core)
        realise(core, u, pr, dd[k] + pd.Timedelta(days=1)); cash += pr
    if tau > 0: close_fy()
    yrs = (dd[k1] - dd[k0]).days / 365.25
    navs = np.array(navs); navs_liq = navs.copy(); navs_liq[-1] = cash if tau == 0 else navs[-1]
    res = dict(final=cash, paid_in=paid_in, years=yrs, cagr=(cash / S0) ** (1 / yrs) - 1 if contrib == 0 and cash > 0 else np.nan, navs=navs, k0=k0, k1=k1,
               ntr=ntr, trades_yr=ntr / yrs, costpaid=costpaid, taxpaid=taxpaid, nsell=nsell, closed=closed, entries=entries, turnover=sold_val / max(navs.mean(), 1e-9) / yrs, npos=len(closed), nharv=nharv, cashw=float(np.mean(cashw[1:])) if len(cashw) > 1 else 0.0, nheld=float(np.mean(nheld[1:])) if len(nheld) > 1 else 0.0)
    return res

# ---------- measures
def mret(mk, res):
    nv = res['navs']; r = nv[1:] / nv[:-1] - 1
    ix = mk.idx_tr[res['k0']:res['k1'] + 1]; b = ix[1:] / ix[:-1] - 1
    return r, r - b
def maxdd(nv):
    pk = np.maximum.accumulate(nv); return float((nv / pk - 1).min())
def top5_share(res):
    pl = sorted([(p1 - c0) for nn, kb, ke, c0, p1 in res['closed']], reverse=True)
    tot = sum(pl)
    return (sum(pl[:5]) / tot if tot > 0 else np.nan), tot
def irr(flows_final, contrib, S0, months):
    """annualised money-weighted return of S0 + monthly contrib -> final"""
    lo, hi = -0.9, 1.0
    f = lambda r: S0 * (1 + r) ** (months / 12) + sum(contrib * (1 + r) ** ((months - m) / 12) for m in range(1, months)) - flows_final
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) > 0: hi = mid
        else: lo = mid
    return mid
def dsr(ex, N, var_sr=None):
    """Deflated Sharpe ratio (Bailey & Lopez de Prado 2014) on monthly excess returns; N = number of trials.
    var_sr: cross-trial variance of the (monthly) Sharpe ratio; default 1/(T-1) (the variance of a zero-skill SR estimate)."""
    from scipy.stats import norm, skew, kurtosis
    ex = np.asarray(ex); T = len(ex); sr = ex.mean() / ex.std(ddof=1)
    g3 = skew(ex); g4 = kurtosis(ex, fisher=False)
    if var_sr is None: var_sr = 1.0 / (T - 1)
    em = 0.5772156649
    sr0 = math.sqrt(var_sr) * ((1 - em) * norm.ppf(1 - 1.0 / N) + em * norm.ppf(1 - 1.0 / (N * math.e)))
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4.0 * sr * sr)
    return float(norm.cdf(z)), float(sr * math.sqrt(12))

def trial(name, spec, sample, results, kind='dev trial', counted=1):
    path = OUT + '/trials_77.csv'
    N = 1543
    if os.path.exists(path):
        d = pd.read_csv(path); N = int(d['N_cum'].iloc[-1]) if len(d) else 1543
    N += counted
    row = pd.DataFrame([dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), name=name, spec=json.dumps(spec, default=str), sample=sample, kind=kind, counted=counted, N_cum=N,
                             results=json.dumps(results, default=lambda o: float(o) if isinstance(o, (np.floating,)) else str(o)))])
    row.to_csv(path, mode='a', header=not os.path.exists(path), index=False)
    return N
