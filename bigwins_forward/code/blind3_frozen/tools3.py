# tools3.py -- evaluation tooling for blind build 3. No strategy here either: books and start days, a runner, random scores
# for twins, the score arithmetic, and an as-of audit that checks your strategy cannot see the future.
import numpy as np, pandas as pd, copy
from multiprocessing import Pool
import acct3

KEEP = ('at', 'fund_at', 'lead_at', 'at_wo1', 'at_wo3', 'at_wo5', 'maxdd', 'maxdd_daily', 'fund_maxdd_daily', 'min_value_daily', 'orders_yr', 'brokerage_yr',
        'spread_yr', 'avg_held', 'avg_cash', 'win', 'days_held_median', 'top5_share_of_wins', 'yrs', 'n_holdings_closed', 'zero_payouts', 'tax_total')


def books(E, windows, n_starts=6):
    """One book per window and start month: starts = the month-end of the December before the window, then January ...;
    every book ends at the window's last December month-end (or the last month-end the data can fill). Prints nothing;
    PRINT the list yourself and check that no month is skipped or repeated."""
    me = pd.DatetimeIndex([E.idx[i] for i in E.ME if i + 1 < E.n]); out = []
    for w, (y0, y1) in enumerate(windows):
        st = [me[(me.year == y0 - 1) & (me.month == 12)][0]] + [me[(me.year == y0) & (me.month == m)][0] for m in range(1, n_starts)]
        en = me[me.year == y1][-1]
        out += [(w, q, s, en) for q, s in enumerate(st)]
    return out


class RandomScores:
    """Persistent random score per entity for random twins: each calendar month every entity keeps last month's score with
    probability 1 - redraw and draws a new one otherwise. Stateless to use: .at(view) gives the scores of that month."""
    def __init__(s, seed, E, redraw=0.2):
        m0 = E.idx[0].year * 12 + E.idx[0].month; m1 = E.idx[-1].year * 12 + E.idx[-1].month; rng = np.random.default_rng(seed)
        n = len(E.cols); cur = rng.random(n); s.m0 = m0; s.M = np.empty((m1 - m0 + 1, n), dtype='float32')
        for q in range(m1 - m0 + 1):
            new = rng.random(n) < redraw; cur = np.where(new, rng.random(n), cur); s.M[q] = cur
    def at(s, view): return s.M[view.month_index() - s.m0]


_E = None; _F = None
def _job(a):
    bi, start, end, seed, mult = a; o = _E.sim(_F(_E, seed), start, end, mult=mult)
    return (bi, seed, mult, {k: float(o[k]) for k in KEEP})


def run_books(E, factory, book_list, seeds=(None,), mult=1.0, procs=4):
    """factory(E, seed) -> Strategy. seed None = your design; an integer = a random twin of it (you write what a twin is:
    the SAME rules with every ranking replaced by RandomScores). Returns a DataFrame, one row per book and seed."""
    global _E, _F; _E = E; _F = factory
    jobs = [(bi, str(b[2].date()), str(b[3].date()), sd, mult) for bi, b in enumerate(book_list) for sd in seeds]
    if procs > 1:
        with Pool(procs) as p: R = p.map(_job, jobs, chunksize=max(1, len(jobs) // (8 * procs)))
    else: R = [_job(j) for j in jobs]
    rows = [dict(book=bi, window=book_list[bi][0], start=book_list[bi][2], end=book_list[bi][3], seed=-1 if sd is None else sd, mult=m, **o) for bi, sd, m, o in R]
    return pd.DataFrame(rows)


def window_leads(df, col='lead_at'):
    """Mean over start months inside each window (design rows only: seed == -1)."""
    return df[df.seed == -1].groupby('window')[col].mean()


def score_R(wl):
    """R = mean of the window leads minus one standard error of them."""
    wl = np.asarray(wl, dtype=float); se = wl.std(ddof=1) / np.sqrt(len(wl)); return float(wl.mean() - se), float(se), float(wl.mean())


def twin_table(df, col='at'):
    """Per window: the design's mean over starts, the twins' median of (mean over starts), and the design's percentile."""
    d = df[df.seed == -1].groupby('window')[col].mean(); t = df[df.seed >= 0].groupby(['window', 'seed'])[col].mean().unstack()
    return pd.DataFrame({'design': d, 'twins_median': t.median(1), 'percentile': [100 * float((t.loc[w] < d[w]).mean()) for w in d.index]})


def asof_audit(dirn, factory, start, end, seed=None, n_checks=6, rng_seed=0):
    """Checks that your strategy uses nothing after the decision day. Runs one book while recording, at every decision, the
    account it was shown and the orders it gave; then, for n_checks decisions, loads the data again with every row after
    that decision day blanked and asks a fresh strategy the same question. Any difference is a look-ahead fault."""
    E = acct3.Engine(dirn); inner = factory(E, seed); log = []
    class Rec(acct3.Strategy):
        def decision_rows(s, dates): return inner.decision_rows(dates)
        def sells(s, view, book):
            b = copy.deepcopy(book); out = inner.sells(view, book); s._cur = [view.i, b, copy.deepcopy(out)]; return out
        def buys(s, view, book):
            b = copy.deepcopy(book); out = inner.buys(view, book); log.append(s._cur + [b, copy.deepcopy(out)]); return out
    E.sim(Rec(), start, end)
    pick = np.random.default_rng(rng_seed).choice(len(log), size=min(n_checks, len(log)), replace=False); bad = []
    for q in sorted(pick):
        i, b1, o1, b2, o2 = log[q]; E2 = acct3.Engine(dirn, poison_after=i); fresh = factory(E2, seed); v = acct3.View(E2, i)
        r1 = fresh.sells(v, copy.deepcopy(b1)); r2 = fresh.buys(v, copy.deepcopy(b2))
        same = (repr(r1) == repr(o1)) and (repr(r2) == repr(o2)); print('decision', E.idx[i].date(), 'identical' if same else 'DIFFERENT')
        if not same: bad.append(E.idx[i])
    print('as-of audit:', 'PASS' if not bad else 'FAIL %s' % bad); return not bad
