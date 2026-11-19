# strat.py -- blind build 3: one general Strategy class covering the four pre-registered families and their random twins.
# Signals use only the View handed by the engine (rows up to the decision day). A per-row cache is kept on the Engine object;
# it is filled only from View slices, so a poisoned engine (as-of audit) recomputes it from cut data.
import sys, warnings, math
import numpy as np
KIT = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/blind3_clean/kit'
if KIT not in sys.path: sys.path.insert(0, KIT)
import acct3, tools3
DATA = KIT + '/data'


def sig(view):
    E = view._E; c = E.__dict__.setdefault('_sig', {}); i = view.i
    if i in c: return c[i]
    R = view.RET[-252:]; L = view.L
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        d = dict(valid=((~np.isnan(R)).sum(0) >= 200) & ~np.isnan(view.CR[i]),
                 v252=np.nanstd(R, axis=0), v126=np.nanstd(R[-126:], axis=0),
                 m12=L[i - 21] - L[i - 252], m6=L[i - 21] - L[i - 126],
                 hi=L[i] - L[i - 251:i + 1].max(0), rank=view.cost_rank())
    c[i] = d; return d


class Design(acct3.Strategy):
    """fam: MOM (par = lookback months 6|12), LOWVOL (par = window sessions 126|252), HIGHSTOP (par = trailing stop, e.g. 0.25),
    BLEND (par = lookback months). U = universe size by traded-value place; N = target names; B = sell buffer (sell when the
    holding's place among the buy set is B*N or worse); TW = 1 defers selling a holding in profit until held 367 days.
    seed None = the design; integer = random twin (all signal rankings replaced by RandomScores(seed, redraw=p))."""
    def __init__(s, E, seed, fam, par, U, N, B, TW, p=0.2):
        s.fam = fam; s.par = par; s.U = U; s.N = N; s.B = B; s.TW = TW; s.seed = seed
        s.rs = None if seed is None else tools3.RandomScores(seed, E, redraw=p)

    def _sets(s, view):
        g = sig(view); rank = g['rank']; ordy = view.ordinary
        hold_ok = ordy & g['valid'] & (rank <= 2 * s.U)          # may be kept
        buy = ordy & g['valid'] & (rank <= s.U)                  # may be bought
        if s.rs is not None:
            sc = s.rs.at(view).astype('float64')
        elif s.fam == 'MOM':
            sc = g['m12'] if s.par == 12 else g['m6']
        elif s.fam == 'LOWVOL':
            sc = -(g['v252'] if s.par == 252 else g['v126'])
        elif s.fam == 'HIGHSTOP':
            sc = g['hi'] + 1e-9 * g['m12']                         # nearness to the 252-session high; ties by 12-1 return
        elif s.fam == 'BLEND':
            sc = g['m12'] if s.par == 12 else g['m6']
            v = g['v252']; buy = buy & (v <= np.nanmedian(v[buy]))
        sc = np.where(np.isfinite(sc), sc, -np.inf)
        return g, hold_ok, buy, sc

    def sells(s, view, book):
        g, hold_ok, buy, sc = s._sets(view); out = []; i = view.i
        bsc = np.sort(sc[buy])[::-1]
        for j, h in sorted(book.holdings.items()):
            if not hold_ok[j]: out.append(j); continue           # forced: left the tradable set
            if s.fam == 'HIGHSTOP' and s.rs is None:
                r0 = int(np.searchsorted(view.dates.values, np.datetime64(h['first_buy_date']))); r0 = min(r0, i)
                Lj = view.L[r0:i + 1, j]; want = (Lj[-1] - Lj.max()) < math.log(1 - s.par)
            else:
                place = int((bsc > sc[j]).sum())                   # number of buy-set names ranked above it
                want = place >= s.B * s.N
            if want and s.TW and h['value'] > h['cost'] and h['days_held'] < 367: want = False
            if want: out.append(j)
        return out

    def buys(s, view, book):
        g, hold_ok, buy, sc = s._sets(view)
        slots = s.N - len(book.holdings)
        if slots <= 0: return [], s.N
        order = np.argsort(-sc, kind='stable'); skip = set(book.holdings) | set(book.sold)
        w = max(1.0 / s.N, 520.0 / max(book.nav, 1.0)); out = []
        for j in order:
            j = int(j)
            if not buy[j] or j in skip: continue
            out.append((j, w))
            if len(out) >= slots + 10: break
        return out, s.N


def make_factory(fam, par, U, N, B, TW, p=0.2):
    def factory(E, seed): return Design(E, seed, fam, par, U, N, B, TW, p)
    return factory


def grid():
    """The full pre-registered grid: name -> (fam, par, U, N, B, TW). 148 designs."""
    G = {}
    for fam, pars in (('MOM', (6, 12)), ('LOWVOL', (126, 252))):
        for par in pars:
            for U in (100, 200, 400):
                for B in (2, 4):
                    for N in (15, 18):
                        for TW in (0, 1): G['%s_p%d_U%d_B%d_N%d_T%d' % (fam, par, U, B, N, TW)] = (fam, par, U, N, B, TW)
    for S in (0.15, 0.25, 0.35):
        for U in (100, 200, 400):
            for N in (15, 18):
                for TW in (0, 1): G['HIGHSTOP_p%d_U%d_B2_N%d_T%d' % (round(S * 100), U, N, TW)] = ('HIGHSTOP', S, U, N, 2, TW)
    for par in (6, 12):
        for U in (200, 400):
            for B in (2, 4):
                for N in (15, 18): G['BLEND_p%d_U%d_B%d_N%d_T1' % (par, U, B, N)] = ('BLEND', par, U, N, B, 1)
    return G

STEPS = dict(MOM=(6, 12), LOWVOL=(126, 252), HIGHSTOP=(0.15, 0.25, 0.35), BLEND=(6, 12))
UL = dict(MOM=(100, 200, 400), LOWVOL=(100, 200, 400), HIGHSTOP=(100, 200, 400), BLEND=(200, 400))

def neighbours(name, G):
    """Designs of the same family differing by one step in exactly one setting."""
    fam, par, U, N, B, TW = G[name]; out = []
    for n2, (f2, p2, U2, N2, B2, T2) in G.items():
        if f2 != fam or n2 == name: continue
        diff = [(par != p2), (U != U2), (N != N2), (B != B2), (TW != T2)]
        if sum(diff) != 1: continue
        if diff[0] and abs(STEPS[fam].index(par) - STEPS[fam].index(p2)) != 1: continue
        if diff[1] and abs(UL[fam].index(U) - UL[fam].index(U2)) != 1: continue
        out.append(n2)
    return out

D0 = 'MOM_p12_U200_B4_N18_T1'
WINDOWS = [(2006, 2008), (2009, 2011), (2012, 2014), (2015, 2017)]
