# Report 73: build a compact "decision-date pack" from daily arrays. Generic across markets.
# P  : (T,N) adjusted close, NaN where no close that day.   TV : (T,N) traded value (0/NaN when none).   RC : (T,N) raw close or None.
# No engine return is computed here; the pack holds prices at decision dates and point-in-time features.
import numpy as np, pandas as pd

FEATS = ['s1', 's2', 's3', 's4', 'zero', 'r21', 'max5', 'fip', 'resmom', 'ivol', 'beta', 'r252', 'r63', 'trendq', 'hirec']

def clean_adj(P, log=None, revert=10):
    """Pre-registered data-error guard on the adjusted close (per column, on its own rows with a close).
    J = P(d)/P(previous good row). (a) |ln J| > ln 3 and, within the next 10 rows, a row returns to within half the jump (in logs) of the
    pre-jump level -> the rows from d up to (not including) that row are bad ticks: set to NaN.
    (b) otherwise, if |ln J| > ln 20 -> unit/split error: every earlier row is multiplied by J (the jump is removed)."""
    P = P.copy(); nb = 0; nu = 0
    T, N = P.shape; L3 = np.log(3); L20 = np.log(20)
    for c in range(N):
        col = P[:, c]; idx = np.flatnonzero(np.isfinite(col) & (col > 0))
        if len(idx) < 3: continue
        v = col[idx].astype(np.float64)
        if np.abs(np.log(v[1:] / v[:-1])).max() <= L3: continue
        bad = np.zeros(len(v), bool); prev = 0; k = 1; n = len(v)
        while k < n:
            j = np.log(v[k] / v[prev])
            if abs(j) > L3:
                rev = None
                for m in range(k + 1, min(k + 1 + revert, n)):
                    if abs(np.log(v[m] / v[prev])) < 0.5 * abs(j): rev = m; break
                if rev is not None:
                    bad[k:rev] = True; nb += rev - k; k = rev; continue
                elif abs(j) > L20:
                    v[:k] *= np.exp(j); nu += 1
            prev = k; k += 1
        v[bad] = np.nan; col[idx] = v
    if log is not None: log['bad_tick_rows'] = nb; log['unit_jumps'] = nu
    return P

def ffill(P, limit=None):
    T, N = P.shape
    idx = np.where(np.isfinite(P), np.arange(T)[:, None], -1)
    np.maximum.accumulate(idx, axis=0, out=idx)
    age = np.arange(T)[:, None] - idx
    out = np.take_along_axis(P, np.maximum(idx, 0), axis=0)
    out[idx < 0] = np.nan
    age = np.where(idx < 0, 10 ** 6, age)
    if limit is not None: out[age > limit] = np.nan
    return out, age

def build_pack(dates, P, TV, RC=None, dec_idx=None, U=300, keep_top=500, extra=None):
    """dec_idx: daily indices of decision dates (default: month-ends). Returns dict of (K,N') arrays for symbols ever ranked <= keep_top."""
    T, N = P.shape
    dates = pd.DatetimeIndex(dates)
    if dec_idx is None:
        ym = dates.year * 12 + dates.month
        dec_idx = np.flatnonzero(np.r_[ym[1:] != ym[:-1], True])
        if dates[-1] != (dates[-1] + pd.offsets.BMonthEnd(0)): dec_idx = dec_idx  # last partial month kept as a decision date (flag below)
    dec_idx = np.asarray(dec_idx); K = len(dec_idx)
    has = np.isfinite(P)
    Pff, age = ffill(P); P10 = np.where(age <= 10, Pff, np.nan)
    lr = np.full((T, N), np.nan, np.float32); lr[1:] = np.where(has[1:] & has[:-1], np.log(P[1:] / P[:-1]), np.nan)
    TVz = np.nan_to_num(TV, nan=0.0).astype(np.float32)
    lastc = np.where(has.any(0), T - 1 - np.argmax(has[::-1], axis=0), -1); firstc = np.where(has.any(0), np.argmax(has, axis=0), -1)
    out = {f: np.full((K, N), np.nan, np.float32) for f in FEATS + ['px', 'pe', 'rc', 'vrank', 'medtv', 'divy', 'H80', 'sp']}
    out['age'] = np.full((K, N), 10 ** 6, np.int32)
    prev_i = None
    for k, i in enumerate(dec_idx):
        out['px'][k] = Pff[i]; out['age'][k] = np.minimum(age[i], 10 ** 6)
        if i + 1 < T: out['pe'][k] = P[i + 1]
        out['rc'][k] = (RC[i] if RC is not None else P[i])
        prev_i = i
        if i < 252: continue
        hw = has[i - 251:i + 1]; ncl = hw.sum(0)
        med = np.median(TVz[i - 251:i + 1], axis=0)
        elig = ncl >= 200
        order = np.lexsort((np.arange(N), -med)); order = order[elig[order]]
        vr = np.full(N, np.nan, np.float32); vr[order] = np.arange(1, len(order) + 1)
        out['vrank'][k] = vr; out['medtv'][k] = np.where(elig, med, np.nan)
        cand = np.flatnonzero(vr <= max(keep_top, U))
        uni = vr[cand] <= U
        L = lr[i - 251:i + 1][:, cand].astype(np.float64)       # 252 daily log returns
        nret = np.isfinite(L).sum(0)
        p0 = P10[i, cand]
        s1 = P10[i - 21, cand] / P10[i - 252, cand] - 1; s2 = p0 / P10[i - 126, cand] - 1
        Pw = P[i - 251:i + 1][:, cand]
        with np.errstate(all='ignore'):
            hi = np.nanmax(np.where(np.isfinite(Pw), Pw, -np.inf), axis=0); hi[~np.isfinite(hi)] = np.nan
            s3 = p0 / hi
            sd = np.nanstd(L, axis=0, ddof=1); sd[nret < 200] = np.nan
            s4 = -sd
            r21 = p0 / P10[i - 21, cand] - 1; r63 = p0 / P10[i - 63, cand] - 1; r252 = p0 / P10[i - 252, cand] - 1
            L63 = np.where(np.isfinite(L[-63:]), L[-63:], -np.inf); max5 = np.sort(L63, axis=0)[-5:]; max5 = np.where(np.isfinite(max5), max5, np.nan); max5 = np.nanmean(max5, axis=0)
            Lf = L[:-21]; pos = (Lf > 0).sum(0); neg = (Lf < 0).sum(0); nn = np.isfinite(Lf).sum(0)
            fip = -np.sign(s1) * (neg - pos) / np.maximum(nn, 1)      # higher = smoother path in the direction of momentum
            # market = equal-weight mean daily log return of the universe (rank <= U)
            mk = np.nanmean(L[:, uni], axis=1)
            Lz = np.where(np.isfinite(L), L, np.nan); ok = np.isfinite(Lz)
            mkm = np.where(ok, mk[:, None], np.nan)
            mx = np.nanmean(mkm, axis=0); my = np.nanmean(Lz, axis=0)
            cov = np.nanmean((mkm - mx) * (Lz - my), axis=0); var = np.nanmean((mkm - mx) ** 2, axis=0)
            beta = cov / var; alpha = my - beta * mx
            res = Lz - alpha - beta * mkm
            rs = np.nanstd(res, axis=0, ddof=2); rs[nret < 200] = np.nan
            resf = res[:-21]; nres = np.isfinite(resf).sum(0)
            resmom = (np.nansum(resf, axis=0) + alpha * nres) / (rs * np.sqrt(np.maximum(nres, 1)))   # residual (alpha+eps) momentum 12-1, scaled
            # trend quality: t-stat of slope of ln(P ffilled) on time over the window
            lp = np.log(Pff[i - 251:i + 1][:, cand].astype(np.float64)); tt = np.arange(252) - 125.5
            okp = np.isfinite(lp).all(0)
            sl = (tt[:, None] * (lp - lp.mean(0))).sum(0) / (tt ** 2).sum()
            rr = lp - lp.mean(0) - sl * tt[:, None]; se = np.sqrt((rr ** 2).sum(0) / 250 / (tt ** 2).sum())
            trendq = np.where(okp, sl / se, np.nan)
            am = np.argmax(np.where(np.isfinite(Pw), Pw, -np.inf), axis=0); hirec = -(251 - am) / 251.0      # recency of 52-week high (0 = today)
        for nme, v in (('s1', s1), ('s2', s2), ('s3', s3), ('s4', s4), ('zero', 1 - ncl[cand] / 252.0), ('r21', r21), ('max5', max5), ('fip', fip), ('resmom', resmom),
                       ('ivol', rs), ('beta', beta), ('r252', r252), ('r63', r63), ('trendq', trendq), ('hirec', hirec)):
            out[nme][k, cand] = v
    # dividend yield per period from raw vs adjusted closes (if raw given)
    if RC is not None:
        RCf, _ = ffill(RC)
        for k in range(1, K):
            i0, i1 = dec_idx[k - 1], dec_idx[k]
            with np.errstate(all='ignore'):
                tr = Pff[i1] / Pff[i0]; pr = RCf[i1] / RCf[i0]; y = tr / pr - 1
            y = np.where(np.isfinite(y) & (y > 1e-5) & (y < 0.08), y, 0.0)
            out['divy'][k] = y
    else:
        out['divy'][:] = 0.0
    ever = np.zeros(N, bool)
    with np.errstate(invalid='ignore'):
        ever = (out['vrank'] <= keep_top).any(0)
    keep = np.flatnonzero(ever)
    pk = {f: v[:, keep] for f, v in out.items()}
    pk['dec_idx'] = dec_idx; pk['dec_dates'] = dates[dec_idx].values; pk['keep'] = keep
    pk['lastc'] = lastc[keep]; pk['firstc'] = firstc[keep]; pk['T'] = T; pk['last_date'] = dates[-1]; pk['dates_daily'] = dates.values
    # H80 and half-spread base computed in sim (needs universe percentile)
    if extra: pk.update(extra)
    return pk

def save_pack(pk, path):
    np.savez_compressed(path, **{k: (np.asarray(v) if not isinstance(v, (list, dict)) else np.array(v, dtype=object)) for k, v in pk.items()}, allow_pickle=True)

def load_pack(path):
    z = np.load(path, allow_pickle=True); return {k: z[k] for k in z.files}
