# tools4.py -- evaluation tooling. No strategy here: books and start days, a runner, random scores for twins, the score
# arithmetic, an as-of audit that checks your strategy cannot see the future, and Ensemble: a wrapper that lets several
# strategies of yours share ONE account in equal parts (it contains no rule of its own about what to buy or sell).
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


class Ensemble(acct3.Strategy):
    """Several member strategies in ONE account, in equal parts. The wrapper decides nothing about shares: each member is
    shown a sub-book and decides as if it were alone; the wrapper only merges the orders.
      - Sub-book of member q: the holdings it bought, an account value of (whole account / k), and as cash whatever part of
        that share it has not invested (never more than the account's cash). book.memo of a member is its own dict.
      - Sells: every member's sells, unchanged.
      - Buys: each member returns (orders, max_holdings) for its sub-book; a weight w means w of the member's share, so the
        wrapper sends w / k of the whole account. A name held or sold today by another member is skipped. Members claim
        names in turn (first choices first; the member that goes first rotates by calendar month). A member's order is a
        first order while it holds fewer than max_holdings names AND its share still has room for at least half of the
        order (room = share less the value of what it holds); its further orders follow as reserves and fill only if a
        first order was refused. So a member cannot spend another member's share, and the number of names a member holds
        follows from its share: SIZE YOUR ORDERS FROM book.nav (which for a member is its share), not from a fixed count.
      - The parts are not traded back to equal: a member whose holdings have grown past its share simply cannot buy until
        it sells; a member below its share buys with the pooled cash. One cash reserve, one tax account.
    Members must share their decision days. With one member the wrapper gives exactly that member's orders."""
    def __init__(s, members): s.m = list(members); s.k = len(s.m)

    def decision_rows(s, dates):
        r = [list(m.decision_rows(dates)) for m in s.m]
        if any(x != r[0] for x in r[1:]): raise RuntimeError('members of an Ensemble must share their decision days')
        return r[0]

    def _sub(s, book, own, q):
        H = {j: h for j, h in book.holdings.items() if own.get(j, 0) == q}
        share = book.nav / s.k; inv = sum(h['value'] for h in H.values())
        return acct3.Book(max(0.0, min(book.cash, share - inv)), share, H, book.memo.setdefault('member%d' % q, {}), list(book.lapsed))

    def sells(s, view, book):
        own = book.memo.setdefault('own', {})
        for j in [j for j in own if j not in book.holdings]: del own[j]     # orders that never filled, holdings that are gone
        out = []
        for q, m in enumerate(s.m): out += list(m.sells(view, s._sub(book, own, q)))
        return out

    def buys(s, view, book):
        own = book.memo.setdefault('own', {}); sold = list(getattr(book, 'sold', [])); lists = []; need = []
        for q, m in enumerate(s.m):
            b = s._sub(book, own, q); b.sold = sorted(j for j in sold if own.get(j, 0) == q)
            orders, maxh = m.buys(view, b)
            lists.append([(int(j), float(w) / s.k) for j, w in orders]); need.append(None if maxh is None else max(0, int(maxh) - len(b.holdings)))
        blocked = {j for j in book.holdings} | set(sold)          # names another member holds or sold today
        first = [[] for _ in s.m]; rest = [[] for _ in s.m]; claimed = {}
        for q in range(s.k):                                        # a member may always add to a name it owns itself
            lists[q] = [(j, w) for j, w in lists[q] if own.get(j, 0) == q or j not in blocked]
        order = [(view.month_index() + t) % s.k for t in range(s.k)]; ptr = [0] * s.k; go = True
        room = [book.nav / s.k - sum(h['value'] for j, h in book.holdings.items() if own.get(j, 0) == q) for q in range(s.k)]
        while go:                                                   # claim in turn
            go = False
            for q in order:
                while ptr[q] < len(lists[q]):
                    j, w = lists[q][ptr[q]]; ptr[q] += 1
                    if claimed.get(j, q) != q: continue
                    amt = w * book.nav; fits = (s.k == 1) or (room[q] >= 0.5 * amt)
                    if fits and (need[q] is None or len(first[q]) < need[q]): first[q].append((j, w)); room[q] -= amt
                    else: rest[q].append((j, w))
                    claimed[j] = q; go = True; break
        out = []
        for grp in (first, rest):
            n = max(len(g) for g in grp) if grp else 0
            for t in range(n):
                for q in order:
                    if t < len(grp[q]): out.append(grp[q][t])
        for j, q in claimed.items():
            if j not in book.holdings: own[j] = q
        cap = None if (s.k == 1 and need[0] is None) else len(book.holdings) + (need[0] if s.k == 1 else sum(len(f) for f in first))
        return out, cap


def ensemble_factory(member_factories):
    """factory(E, seed) for an Ensemble of the given member factories. seed None = the designs; an integer = a random twin of
    the whole ensemble, in which member q is its own twin with seed 1000 * seed + q (so members do not draw the same scores)."""
    def factory(E, seed):
        return Ensemble([f(E, None if seed is None else 1000 * int(seed) + q) for q, f in enumerate(member_factories)])
    return factory
