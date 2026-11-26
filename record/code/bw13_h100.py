# v1.3 part N (H100 June sleeve) from a bw13_prep bundle; check against report 64's p0_h100_eod.csv.  python3 -I bw13_h100.py [frozen|A7b]
import sys, numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'; FW = S + '/bigwins_forward'
sys.path.insert(0, FW + '/code'); import bw13_prep
BRK = 6.60 / 2500.0

def h100_year(D, y, with_div=True):
    dates = D['dates']; Pv = D['Pv']; Pf = D['Pf']; V0 = D['V0']; Cc = D['Craw']; Hh = D['Hraw']; Ll = D['Lraw']; lastv = D['lastv']
    has = ~np.isnan(Pv); nC = Pv.shape[1]
    jun = np.flatnonzero((dates.year == y) & (dates.month == 6)); jul = np.flatnonzero((dates.year == y) & (dates.month == 7))
    B = jun[-4]; X = jul[-1]; s = B - 1
    w0 = s - 251; traded = has[w0:s + 1].sum(0); medval = np.median(V0[w0:s + 1], axis=0)
    el = np.flatnonzero(traded >= 200); order = el[np.argsort(-medval[el], kind='stable')]
    rank = np.full(nC, 10**9); rank[order] = np.arange(1, len(order) + 1)
    u = np.flatnonzero((rank > 300) & (rank < 10**9) & (medval >= 50000) & (Cc[s] >= 0.05) & ~np.isnan(Pf[s]) & ~np.isnan(Pf[s - 252]))
    r252 = Pf[s, u] / Pf[s - 252, u] - 1; los = u[r252 <= np.quantile(r252, 0.2)]
    DIV = np.zeros(Pv.shape, np.float64)
    for i, lst in D['DIVD'].items():
        for j, a in lst: DIV[i, j] = a
    def ar_half(i, c):
        with np.errstate(all='ignore'):
            h = np.log(Hh[i - 63:i + 1][:, c]); l = np.log(Ll[i - 63:i + 1][:, c]); cl = np.log(Cc[i - 63:i + 1][:, c])
            eta = (h + l) / 2; x = (cl[:-1] - eta[:-1]) * (cl[:-1] - eta[1:]); m = np.nanmean(x, axis=0)
            sp = 2 * np.sqrt(np.maximum(m, 0)); return np.where(np.isnan(sp), 0, sp) / 2
    def hs(i, c):
        px = np.where(np.isnan(Cc[i, c]), Pf[i, c], Cc[i, c]); tick = np.where(px < 0.10, 0.001, np.where(px < 2, 0.005, 0.01))
        return np.maximum.reduce([0.5 * tick / px, ar_half(i, c), np.full(len(c), 0.005)])
    out = {}
    for nm, g0 in (('losers', los), ('universe', u)):
        g = g0[has[B, g0]]
        p1 = Pf[X, g].copy(); gone = lastv[g] <= X - 20
        f = np.where(D['fail'][g], 0.0, np.where(D['take'][g], 1.0, 0.7)); p1 = np.where(gone, p1 * f, p1)
        dv = DIV[B + 1:X + 1][:, g].sum(0) if with_div else 0.0
        gr = (p1 + dv) / Pv[B, g] - 1
        net = (1 + gr) * (1 - hs(X, g) - BRK) / (1 + hs(s, g) + BRK) - 1
        ix = D['xtr'] if with_div else D['xjo']
        out[nm] = dict(n=len(g), net=float(net.mean()), idx=float(ix[X] / ix[B] - 1), cols=g, netv=net)
    return out, (dates[s], dates[B], dates[X])

if __name__ == '__main__':
    rule = sys.argv[1] if len(sys.argv) > 1 else 'frozen'
    D = bw13_prep.build('2026-11-13', dup_rule=rule)
    ref = pd.read_csv(S + '/deepdive/out/p0_h100_eod.csv'); ref = ref[(ref.group == 'losers') & ref.tr].set_index('year')
    rows = []
    for y in range(2016, 2027):
        o, d3 = h100_year(D, y); l = o['losers']
        rows.append(dict(year=y, n=l['n'], net=l['net'], idx=l['idx'], excess=l['net'] - l['idx'], excess_vs_universe=l['net'] - o['universe']['net'],
                         report64_excess=ref.net[y] - ref.xjo[y], n_report64=int(ref.n[y])))
    df = pd.DataFrame(rows); df['diff_pt'] = (df.excess - df.report64_excess) * 100
    print(df.round(4).to_string()); df.to_csv(FW + f'/out/h100_check_{rule}.csv', index=False)
    print('max |diff| pt', df.diff_pt.abs().max(), ' mean excess 2018-2026', df[df.year >= 2018].excess.mean(), ' report64', df[df.year >= 2018].report64_excess.mean())
