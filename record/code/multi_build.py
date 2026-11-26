# Big Wins multi-market FORWARD paper record -- decision-date pack builder (AMENDMENT_forward_multimarket.md).
# A port of the three tested pack builders (improve/code/mk_fresh.py = rules 'r3', improve4/code/mk_fresh4.py = 'r4',
# improve5/code/mk_fresh5.py = 'r5') into one function, applied to the forward store (per-symbol EODHD end-of-day rows of the
# candidate companies). Each market uses the rule set its tested pack was built with. Differences from the tested builders, all forced by
# the forward setting: (1) no 1,200-name prefilter (the store holds only the candidates, see paper_multi.py); (2) one constant A$ scale is
# applied to every price series in every market (round 3 left DE/FR/SE/CA prices in local units) so that the A$25k / A$100k books are
# A$ equivalents; (3) the coverage table is not written. PAPER ONLY. No return is computed here.
import re, json, numpy as np, pandas as pd

MARKETS = {
    # key: exchanges, quote currency, local units per A$1 (constant), fund (EODHD symbol), rule set, impute fund distributions, designs, calendar
    'ASX': dict(ex=['AU'], ccy='AUD', fx=1.0, etf='A200.AU', rules='r5', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XASX', tick='asx'),
    'DE': dict(ex=['XETRA'], ccy='EUR', fx=0.61, etf='EXS1.XETRA', rules='r3', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XETR'),
    'FR': dict(ex=['PA'], ccy='EUR', fx=0.61, etf='CAC.PA', rules='r3', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XPAR'),
    'SE': dict(ex=['ST'], ccy='SEK', fx=6.5, etf='XACT-OMXS30.ST', rules='r3', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XSTO'),
    'SW': dict(ex=['SW'], ccy='CHF', fx=0.58, etf='CSSMI.SW', rules='r4', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XSWX'),
    'CA': dict(ex=['TO'], ccy='CAD', fx=0.90, etf='XIU.TO', rules='r3', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XTSE'),
    'KO': dict(ex=['KO'], ccy='KRW', fx=900.0, etf='069500.KO', rules='r4', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XKRX'),
    'TW': dict(ex=['TW'], ccy='TWD', fx=21.0, etf='0050.TW', rules='r4', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XTAI'),
    'BK': dict(ex=['BK'], ccy='THB', fx=22.0, etf='TDEX.BK', rules='r5', impute=False, designs=['M3', 'EI10I', 'CW'], cal='XBKK'),
    'SA': dict(ex=['SA'], ccy='BRL', fx=3.5, etf='BOVA11.SA', rules='r4', impute=True, designs=['M3', 'EI10I', 'CW'], cal='BVMF'),
    'CN': dict(ex=['SHG', 'SHE'], ccy='CNY', fx=4.7, etf='510300.SHG', rules='r5', impute=False, designs=['M3'], cal='XSHG'),
    'HE': dict(ex=['HE'], ccy='EUR', fx=0.61, etf='SLGOMXH25.HE', rules='r5', impute=True, designs=['M3'], cal='XHEL'),
    'WAR': dict(ex=['WAR'], ccy='PLN', fx=2.6, etf='ETFBW20TR.WAR', rules='r5', impute=True, designs=['M3'], cal='XWAR'),
    'BR': dict(ex=['BR'], ccy='EUR', fx=0.61, etf='BEL.BR', rules='r5', impute=False, designs=['M3'], cal='XBRU'),
}


def line_ok(mkt, code, x):
    """symbol-list filter of the tested builder for this market (x = the vendor's symbol-list record)"""
    c = MARKETS[mkt]; r = c['rules']; ccy = (x or {}).get('Currency') or ''; nm_ = (x or {}).get('Name') or ''
    if (x or {}).get('Type') not in (None, 'Common Stock'): return False
    if r == 'r3': return True                                   # round 3 kept every common-stock line (LSE aside)
    if ccy != c['ccy']: return False
    if r == 'r4':
        if mkt == 'SA' and re.search(r'(3[2-9]|\dF)$', code): return False
        if mkt == 'TW' and code.startswith('00'): return False
        return True
    if mkt == 'BK' and (re.search(r'(01|03|06|11|13|19|23|24|41|80)$', code) or re.search(r'-(R|F)(#\d+)?$', code) or code.startswith('^') or code.endswith('_old')
                        or re.search(r'(?i)infrastructure fund|property fund|reit|real estate investment|leasehold|freehold', nm_) or re.search(r'(IF|PF|REIT)$', code)):
        return False
    if mkt == 'TW' and not re.fullmatch(r'\d{4,6}', code): return False
    return True


def split_factor(cl, adj, vol=None, gap=20):
    """v2 (AMENDMENT_multi_traded_value_v2). F(t) = product of the split ratios dated after row t that apply to the vendor's volume.
    A step is a change of more than 12% in raw close / adjusted close between consecutive rows (as before). New in v2, in every market:
    (1) steps with at most `gap` rows between them form one event with ratio G = the product of its steps; an event whose G is within 12%
        of 1 is a vendor glitch that reverses and is ignored;
    (2) each remaining event is read once: B = median of raw close x volume over the last 20 traded rows before the event, A = the same over
        the first 20 traded rows after it (never reaching into a neighbouring event). If traded value is more continuous without the
        correction than with it, |ln(A/B)| < |ln(A G / B)|, the vendor left the volume as traded and the event is ignored; otherwise the
        volume was restated and G enters F at the event's last step;
    (3) an event with no traded row on one side cannot be read: a consolidation (G < 1) is ignored, a split (G > 1) is applied. Both give
        the lower traded value, so an unread event cannot lift a company into the list.
    vol=None reproduces the round-3 rule as tested (every step applied, no reading) and is kept only for the audit trail."""
    R = cl.astype(np.float64) / adj.astype(np.float64); F = np.ones(len(R))
    ok = np.isfinite(R) & (R > 0)
    if ok.sum() < 2: return F
    Rf = pd.Series(np.where(ok, R, np.nan)).ffill().bfill().values
    g = Rf[:-1] / Rf[1:]; s = np.where(np.abs(np.log(g)) > np.log(1.12), g, 1.0)
    if vol is not None:
        st = np.flatnonzero(s != 1.0); s2 = np.ones(len(s))
        if len(st):
            cv = cl.astype(np.float64) * vol; L12 = np.log(1.12)
            ev = [[st[0]]]
            for t in st[1:]:
                if t - ev[-1][-1] <= gap: ev[-1].append(t)
                else: ev.append([t])
            for q, e in enumerate(ev):
                G = float(np.prod(s[e]))
                if abs(np.log(G)) <= L12: continue
                lo = ev[q - 1][-1] + 1 if q > 0 else 0; hi = ev[q + 1][0] + 1 if q + 1 < len(ev) else len(cv)
                b_ = cv[max(lo, e[0] - 19):e[0] + 1]; a_ = cv[e[-1] + 1:min(hi, e[-1] + 21)]; b_ = b_[b_ > 0]; a_ = a_[a_ > 0]
                if len(b_) < 1 or len(a_) < 1:
                    if G > 1.0: s2[e[-1]] = G
                    continue
                B_ = np.median(b_); A_ = np.median(a_)
                if abs(np.log(A_ / B_)) < abs(np.log(A_ * G / B_)): continue
                s2[e[-1]] = G
        s = s2
    F[:-1] = np.cumprod(s[::-1])[::-1]
    return F


def build(mkt, ser, info, etf, PL, end=None, log=None):
    """ser: code -> (delisted flag, (dates int32 days, close, adj_close, volume)); info: (code, flag) -> symbol-list record;
    etf: DataFrame(Date index; Close, Adjusted_close); PL: the frozen packlib module. end: last calendar day kept (str).
    Returns the pack dict (packlib.build_pack + cols, names, idx fields) exactly as the tested builders assemble it."""
    c = MARKETS[mkt]; r = c['rules']; sc = 1.0 / c['fx']; lg = log if log is not None else {}
    ser = {k: v for k, v in ser.items() if line_ok(mkt, k, info.get((k, v[0])))}
    if end is not None:
        e_i = np.datetime64(end, 'D').astype(np.int32); ser2 = {}
        for k, (dl, (d, cl, adj, vol)) in ser.items():
            m = d <= e_i
            if m.sum() >= 2: ser2[k] = (dl, (d[m], cl[m], adj[m], vol[m]))
        ser = ser2
    if r in ('r4', 'r5'):                                        # G4 placeholder prices
        ng4 = 0
        for code in list(ser):
            dl_, (d_, cl_, adj_, vol_) = ser[code]
            if len(cl_) < 120: continue
            chg = np.flatnonzero(np.r_[True, cl_[1:] != cl_[:-1], True]); L_ = np.diff(chg); bad = np.zeros(len(cl_), bool)
            for a0, ln in zip(chg[:-1], L_):
                if ln >= 120 and (vol_[a0:a0 + ln] > 0).mean() > 0.5: bad[a0:a0 + ln] = True
            if bad.any():
                ng4 += 1; kp_ = ~bad
                if kp_.sum() < 2: del ser[code]
                else: ser[code] = (dl_, (d_[kp_], cl_[kp_], adj_[kp_], vol_[kp_]))
        lg['G4'] = ng4
    codes = sorted(ser)
    cnt = {}
    for cd in codes:
        u = np.unique(ser[cd][1][0])
        for a in u: cnt[a] = cnt.get(a, 0) + 1
    cs = pd.Series(cnt).sort_index(); idx = pd.to_datetime(cs.index.values.astype('datetime64[D]'))
    cs.index = idx; cs = cs[(idx.dayofweek < 5)]
    med = cs.rolling(250, min_periods=20, center=True).median()
    cal = cs.index[cs >= 0.3 * med]
    cal_i = cal.values.astype('datetime64[D]').astype(np.int32); T = len(cal)
    N = len(codes); P = np.full((T, N), np.nan, np.float32); RC = np.full((T, N), np.nan, np.float32); TV = np.zeros((T, N), np.float32); VOL = np.zeros((T, N), np.float64)
    for j, cd in enumerate(codes):
        d, cl, adj, vol = ser[cd][1]
        _, ui = np.unique(d[::-1], return_index=True); ui = len(d) - 1 - ui
        d, cl, adj, vol = d[ui], cl[ui], adj[ui], vol[ui]; F = split_factor(cl, adj, vol)
        pos = np.searchsorted(cal_i, d); ok = (pos < T) & (cal_i[np.minimum(pos, T - 1)] == d) & (cl > 0) & (adj > 0)
        P[pos[ok], j] = adj[ok] * sc; RC[pos[ok], j] = cl[ok] * sc; TV[pos[ok], j] = cl[ok].astype(np.float64) * vol[ok] / F[ok] * sc; VOL[pos[ok], j] = vol[ok]
    dl_flag = np.array([ser[cd][0] for cd in codes]); names = np.array([(info.get((cd, ser[cd][0])) or {}).get('Name') or '' for cd in codes], dtype=object)
    keepc = list(codes)
    cal_days = cal_i.astype(np.int64); parts = []; nsplit = 0                # code re-use: a gap of more than 200 days starts a new company
    for j in range(N):
        rows = np.flatnonzero(np.isfinite(P[:, j]))
        if len(rows) < 2: parts.append((j, 0, T, 0)); continue
        gaps = np.flatnonzero(np.diff(cal_days[rows]) > 200)
        if len(gaps) == 0: parts.append((j, 0, T, 0)); continue
        nsplit += 1; b = [0] + [rows[g + 1] for g in gaps] + [T]
        for q in range(len(b) - 1): parts.append((j, b[q], b[q + 1], q))
    if nsplit:
        N2 = len(parts); P2 = np.full((T, N2), np.nan, np.float32); RC2 = np.full((T, N2), np.nan, np.float32); TV2 = np.zeros((T, N2), np.float32); VOL2 = np.zeros((T, N2), np.float64)
        for m, (j, a, b, q) in enumerate(parts):
            P2[a:b, m] = P[a:b, j]; RC2[a:b, m] = RC[a:b, j]; TV2[a:b, m] = TV[a:b, j]; VOL2[a:b, m] = VOL[a:b, j]
        last_part = {}
        for m, (j, a, b, q) in enumerate(parts): last_part[j] = q
        dl_flag = np.array([dl_flag[j] if q == last_part[j] else 1 for (j, a, b, q) in parts]); names = np.array([names[j] for (j, a, b, q) in parts], dtype=object)
        keepc = [keepc[j] + (f'#{q}' if q else '') for (j, a, b, q) in parts]; P, RC, TV, VOL = P2, RC2, TV2, VOL2; N = N2
    lg['reuse_splits'] = nsplit
    # duplicate lines (same raw close and volume on >= 30 of the last 60 rows of a line that ends early)
    h = (np.round(RC.astype(np.float64) * 1e4).astype(np.int64) * 1000003 + VOL.astype(np.int64)) * 7919 + np.arange(T)[:, None]
    h[~np.isfinite(RC) | (VOL <= 0)] = -1
    lastrow = np.where(np.isfinite(RC).any(0), T - 1 - np.argmax(np.isfinite(RC)[::-1], axis=0), -1)
    flat = h.ravel(); sym = np.tile(np.arange(N), T); ok = flat >= 0; fo = flat[ok]; so = sym[ok]; o = np.argsort(fo, kind='stable'); fo = fo[o]; so = so[o]
    dups = {}
    for j in np.flatnonzero((lastrow >= 0) & (lastrow < T - 1)):
        rws = np.flatnonzero(h[:lastrow[j] + 1, j] >= 0)[-60:]
        if len(rws) < 30: continue
        keys = h[rws, j]; a = np.searchsorted(fo, keys, 'left'); b = np.searchsorted(fo, keys, 'right')
        cand = np.concatenate([so[x:y] for x, y in zip(a, b)]); cand = cand[cand != j]
        if len(cand) == 0: continue
        u, n = np.unique(cand, return_counts=True); m = n.argmax()
        if n[m] >= 30 and lastrow[u[m]] > lastrow[j]: dups[j] = u[m]
    lg['dup_lines'] = len(dups)
    kp = np.array([j for j in range(N) if j not in dups], dtype=int); P, RC, TV, VOL = P[:, kp], RC[:, kp], TV[:, kp], VOL[:, kp]; dl_flag = dl_flag[kp]; names = names[kp]; cods = np.array(keepc, dtype=object)[kp]
    N = P.shape[1]
    if r == 'r3':
        P = PL.clean_adj(P.astype(np.float64), lg)
    else:
        # D2 same company under two codes
        T_ = P.shape[0]; lr4 = np.full((T_, N), np.nan); hasP = np.isfinite(P)
        for j in range(N):
            r_ = np.flatnonzero(hasP[:, j])
            if len(r_) > 1: lr4[r_[1:], j] = np.log(P[r_[1:], j].astype(np.float64) / P[r_[:-1], j])
        hh = np.where(np.isfinite(lr4) & (np.abs(lr4) > 1e-5), np.round(np.nan_to_num(lr4) * 1e4).astype(np.int64) * 100003 + np.arange(T_)[:, None], -1)
        lastrow = np.where(hasP.any(0), T_ - 1 - np.argmax(hasP[::-1], axis=0), -1)
        flat = hh.ravel(); sym = np.tile(np.arange(N), T_); ok_ = flat >= 0; fo = flat[ok_]; so = sym[ok_]; o_ = np.argsort(fo, kind='stable'); fo = fo[o_]; so = so[o_]
        dups2 = {}
        for j in np.flatnonzero((lastrow >= 0) & (lastrow < T_ - 1)):
            rws = np.flatnonzero(hh[:lastrow[j] + 1, j] >= 0)[-60:]
            if len(rws) < 40: continue
            keys = hh[rws, j]; a_ = np.searchsorted(fo, keys, 'left'); b_ = np.searchsorted(fo, keys, 'right')
            cand = np.concatenate([so[x:y] for x, y in zip(a_, b_)]); cand = cand[cand != j]
            if len(cand) == 0: continue
            u_, n_ = np.unique(cand, return_counts=True); m_ = n_.argmax()
            if n_[m_] >= 40 and (lastrow[u_[m_]] > lastrow[j] or (lastrow[u_[m_]] == lastrow[j] and u_[m_] < j)): dups2[j] = u_[m_]
        lg['D2'] = len(dups2)
        kp = np.array([j for j in range(N) if j not in dups2], dtype=int); P, RC, TV, VOL = P[:, kp], RC[:, kp], TV[:, kp], VOL[:, kp]; dl_flag = dl_flag[kp]; names = names[kp]; cods = cods[kp]; N = P.shape[1]
        P = PL.clean_adj(P.astype(np.float64), lg, revert=30)
        ns2 = 0                                                   # S2 unrecorded splits
        for j in range(N):
            r_ = np.flatnonzero(np.isfinite(P[:, j]))
            if len(r_) < 40: continue
            v = P[r_, j].astype(np.float64); g = np.log(v[1:] / v[:-1])
            for i in np.flatnonzero(np.abs(g) > np.log(2.0)):
                a_ = v[i + 1] / v[i]
                if np.any(np.abs(np.log(v[i + 2:i + 32] / v[i])) < 0.5 * abs(np.log(a_))): continue
                if np.any(np.abs(np.log(v[max(0, i - 30):i] / v[i + 1])) < 0.5 * abs(np.log(a_))): continue
                if (r == 'r4' and mkt in ('KO', 'TW')) or (r == 'r5' and mkt in ('CN', 'VN')): hit = True
                else:
                    hit = False
                    if a_ < 0.36:
                        kk = round(1 / a_); vol_b = np.median(VOL[r_[max(0, i - 19):i + 1], j]); vol_a = np.median(VOL[r_[i + 1:i + 11], j])
                        hit = abs(1 / a_ / kk - 1) < 0.06 and vol_b > 0 and abs(np.log(vol_a / vol_b / kk)) < np.log(1.6)
                if hit:
                    P[:r_[i + 1], j] *= a_; v[:i + 1] *= a_; ns2 += 1
        lg['S2'] = ns2
    e = etf[~etf.index.duplicated(keep='last')]; ec = e['Close'].reindex(cal).ffill(); ea = e['Adjusted_close'].reindex(cal).ffill()
    pk = PL.build_pack(cal, P, TV, RC, U=300, keep_top=500)
    keep = pk['keep']; di = pk['dec_idx']
    pk['cols'] = cods[keep]; pk['names'] = names[keep]; pk['delisted'] = dl_flag[keep]
    pk['idx'] = ec.values[di]; pk['idx_tr'] = ea.values[di]; pk['idx_e'] = np.r_[ec.values[1:], np.nan][di]; pk['idx_tr_e'] = np.r_[ea.values[1:], np.nan][di]
    pk['etf'] = c['etf']; pk['clean_log'] = json.dumps({k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in lg.items()})
    return pk
