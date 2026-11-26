# Score definitions (percentiles inside the traded universe). Used identically on every market.
import numpy as np, pandas as pd
def q_term(mk): return mk.pct_of((mk.P('s1') - 0.5) * (mk.pct_of(mk.vrank.astype(float)) - 0.5))
def make(mk, name):
    P = mk.P; H = mk.H80(); pH = mk.pct_of(H)
    if name == 'H80': return H
    if name == 'CH': return np.where(np.isfinite(H), (pH + mk.pct_of(-mk.pk['zero'].astype(float)) + q_term(mk)) / 3, np.nan)
    if name == 'HZ': return np.where(np.isfinite(H), (pH + mk.pct_of(-mk.pk['zero'].astype(float))) / 2, np.nan)
    if name == 'HQ': return np.where(np.isfinite(H), (pH + q_term(mk)) / 2, np.nan)
    if name == 'M5': return (P('s1') + P('s2') + P('s3') + P('s4') + P('resmom')) / 5
    if name == 'TQ': return (P('s1') + P('s3') + P('s4') + P('trendq') + P('hirec')) / 5
    if name == 'MOM': return P('s1')
    if name == 'MOM3': return (P('s1') + P('s2') + P('s3')) / 3
    if name == 'LV': return P('s4')
    if name == 'RES': return (P('resmom') + P('s3') + P('s4')) / 3
    if name == 'H80x': return np.where(mk.P('r21') > 0.9, np.nan, H)        # H80 without the top decile of 1-month return
    raise KeyError(name)
ML_FEATS = ['s1', 's2', 's3', 's4', 'zero', 'r21', 'max5', 'resmom', 'ivol', 'beta', 'trendq', 'hirec', 'r63']
def ml_scores(mk, kind='ridge', k_start=None, k_end=None, seed=0):
    """Walk-forward: at each December decision date fit on all universe rows whose 12-month outcome is known (12-month gap), predict the next 12 months.
    Target = percentile of the forward 12-month return inside the universe at that date (rank target). Features = percentiles (+ traded-value-rank pct)."""
    from devlib import fwd
    F = fwd(mk, 12); X = [mk.P(f) for f in ML_FEATS] + [mk.pct_of(mk.vrank.astype(float))]
    K, N = F.shape; Y = mk.pct_of(np.where(np.isfinite(F), F, np.nan)); sc = np.full((K, N), np.nan)
    ok = np.isfinite(Y)
    for x in X: ok &= np.isfinite(x)
    okx = mk.uni.copy()
    for x in X: okx &= np.isfinite(x)
    model = None
    for k in range(K):
        if mk.dd[k].month == 12 or model is None:
            tr = [j for j in range(0, k - 12 + 1) if ok[j].any()]
            if len(tr) < 24: continue
            A = np.vstack([np.column_stack([x[j, ok[j]] for x in X]) for j in tr]); y = np.concatenate([Y[j, ok[j]] for j in tr])
            if kind == 'ridge':
                from sklearn.linear_model import Ridge
                model = Ridge(alpha=10.0).fit(A - 0.5, y)
            else:
                import lightgbm as lgb
                model = lgb.LGBMRegressor(n_estimators=150, max_depth=3, num_leaves=8, learning_rate=0.03, subsample=0.7, subsample_freq=1, colsample_bytree=0.7, min_child_samples=200, random_state=seed, verbose=-1).fit(A, y)
        m = okx[k]
        if model is not None and m.any():
            A = np.column_stack([x[k, m] for x in X]); sc[k, m] = model.predict(A - 0.5 if kind == 'ridge' else A)
    return sc
def custom(mk, nm):
    """'c:f1,f2,-f3' = mean of percentiles of the listed features (minus = reversed); 'q' = momentum x size term; 'H80' allowed"""
    assert nm.startswith('c:'); parts = nm[2:].split(','); xs = []
    for f in parts:
        sg = -1 if f.startswith('-') else 1; f = f.lstrip('-')
        x = mk.pct_of(mk.H80()) if f == 'H80' else (q_term(mk) if f == 'q' else mk.P(f))
        xs.append(x if sg > 0 else (1 - x + 1.0 / np.maximum(np.isfinite(x).sum(1, keepdims=True), 1)))
    return np.mean(xs, axis=0)
