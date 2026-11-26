"""Fix (c) forward-fill flags (index and stocks) and row-level quality flags for the v2 panel."""
import numpy as np, pandas as pd

SPLIT_K = [2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 50, 100]


# ------------------------------------------------------------------ index
def ffill_runs(idx, cols=('xjo', 'xtr')):
    """Runs of >=1 consecutive repeats of the previous value (a forward fill), per column.
    Returns run table: column, start (first repeated day), end, days, value, source_day (the real value's day)."""
    out = []
    for c in cols:
        s = idx[c]
        rep = s.notna() & (s == s.shift(1))
        if not rep.any():
            continue
        grp = (rep != rep.shift(1)).cumsum()
        for _, g in s[rep].groupby(grp[rep]):
            src = s.index[s.index.get_loc(g.index[0]) - 1]
            out.append(dict(column=c, source_day=src, start=g.index[0], end=g.index[-1], days=len(g), value=g.iloc[0]))
    return pd.DataFrame(out, columns=['column', 'source_day', 'start', 'end', 'days', 'value'])


def index_flags(idx, cols=('xjo', 'xtr')):
    """Adds <c>_ffill (repeat of previous value) and <c>_clean (NaN on flagged days)."""
    x = idx.copy()
    for c in cols:
        s = x[c]
        rep = s.notna() & (s == s.shift(1))
        x[c + '_ffill'] = rep
        x[c + '_clean'] = s.where(~rep)
    return x


# ------------------------------------------------------------------ adjusted-price stitching
def stitch_adjusted(pan):
    """Within each v2 entity make the adjustment factor A = p / c continuous across company_study
    entity boundaries (new links), fill A over ambiguous rows, and use raw where no factor exists.
    Adds p_basis."""
    pan = pan.copy()
    pan['p_basis'] = np.where(pan.src == 'SA', 'company_study_adjusted(stockanalysis)', 'company_study_adjusted')
    amb = pan.ambiguous_cs.fillna(False).astype(bool)
    pan.loc[amb, 'p'] = np.nan
    ncs = pan[pan.src == 'D1'].groupby('eid').cs_eid.nunique()
    nan_p = pan[(pan.src == 'D1') & pan.p.isna() & ~pan.bad_tick.fillna(False).astype(bool)].eid.unique()
    todo = set(ncs[ncs > 1].index) | set(nan_p)
    if not todo:
        return pan
    sub = pan[pan.eid.isin(todo)]
    for e, x in sub.groupby('eid', sort=False):
        ix = x.index
        d1 = (x.src == 'D1').values
        A = (x.p / x.c).where(d1)
        bt = x.bad_tick.fillna(False).astype(bool).values
        blk = (x.cs_eid != x.cs_eid.shift(1)).cumsum().values
        # scale earlier blocks so A is continuous at each boundary (latest block unchanged)
        ub = pd.unique(blk)
        A = A.values.copy()
        for k in range(len(ub) - 1, 0, -1):
            cur = blk == ub[k]; prev = blk < ub[k]
            a_cur = pd.Series(A[cur & d1]).dropna()
            a_prev = pd.Series(A[(blk == ub[k - 1]) & d1]).dropna()
            if len(a_cur) and len(a_prev):
                A[prev] *= a_cur.iloc[0] / a_prev.iloc[-1]
        As = pd.Series(A, index=ix)
        filled = As.where(d1).ffill().bfill()
        newp = x.p.copy()
        basis = x.p_basis.copy()
        fillm = d1 & np.isnan(A) & ~bt
        newp[d1 & ~np.isnan(A)] = (x.c * As)[d1 & ~np.isnan(A)]
        if filled.notna().any():
            newp[fillm] = (x.c * filled)[fillm]
            basis[fillm] = 'raw_x_neighbour_factor'
        else:
            newp[fillm] = x.c[fillm]
            basis[fillm] = 'raw_no_adjustment'
        rescaled = d1 & ~np.isnan(A) & (np.abs(newp.values / np.where(x.p.values > 0, x.p.values, np.nan) - 1) > 1e-9)
        basis[rescaled] = 'company_study_adjusted_rescaled_at_new_link'
        pan.loc[ix, 'p'] = newp.values
        pan.loc[ix, 'p_basis'] = basis.values
    return pan


# ------------------------------------------------------------------ row flags
def row_flags(pan, copy_days=()):
    """pan sorted by eid, date. Adds boolean quality flags (never deletes rows)."""
    pan = pan.sort_values(['eid', 'date']).reset_index(drop=True)
    g = pan.groupby('eid', sort=False)
    d1 = (pan.src == 'D1').values
    prev = {k: g[k].shift(1).values for k in ('o', 'h', 'l', 'c', 'v', 'p', 'val')}
    same = np.ones(len(pan), bool)
    for k in ('o', 'h', 'l', 'c', 'v'):
        same &= (pan[k].values == prev[k])
    copy_d1 = d1 & same & (pan.v.values > 0)
    copy_sa = (~d1) & (pan.p.values == prev['p']) & (pan.val.values == prev['val']) & (pan.val.values > 0)
    pan['copy_row'] = copy_d1 | copy_sa
    pan['zero_vol'] = (d1 & (pan.v.values == 0)) | ((~d1) & (pan.val.fillna(0).values == 0))
    pan['zero_vol_close_moved'] = pan.zero_vol.values & d1 & (pan.c.values != prev['c']) & ~np.isnan(prev['c'])
    pan['zero_vol_close_flat'] = pan.zero_vol.values & ~pan.zero_vol_close_moved.values
    pan['copy_day'] = pan.date.isin(pd.DatetimeIndex(list(copy_days))) if len(copy_days) else False
    p = pan.p.values
    pp = prev['p']
    pn = g.p.shift(-1).values
    with np.errstate(divide='ignore', invalid='ignore'):
        r = p / pp
        rn = pn / pp
        lr = np.abs(np.log(r))
    pan['spike_residual'] = ((r >= 1.9) | (r <= 1 / 1.9)) & (rn > 0.75) & (rn < 1.33)
    fwd = g.p.transform(lambda s: s[::-1].rolling(10, min_periods=1).median()[::-1]).values
    with np.errstate(divide='ignore', invalid='ignore'):
        norevert = np.abs(np.log(fwd / p)) < 0.5 * lr
    cand = (lr >= np.log(1.45)) & norevert
    match = np.zeros(len(pan), bool)
    for k in SPLIT_K:
        match |= (np.abs(r * k - 1) < 0.03) | (np.abs(r / k - 1) < 0.03)
    pan['split_residual'] = cand & match
    pan['big_move_unexplained'] = cand & ~match & ~pan.spike_residual.values
    # day on which an applied code link starts (first row under the new code within the entity)
    pan['link_day'] = (pan.code.values != g.code.shift(1).values) & (g.cumcount().values > 0)
    return pan
