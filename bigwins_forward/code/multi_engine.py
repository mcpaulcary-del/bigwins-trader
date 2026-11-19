# Big Wins multi-market FORWARD paper record -- adapter to the FROZEN round-5/6 engines (AMENDMENT_forward_multimarket.md).
# The engines are byte-identical copies in multi_frozen/ (SHA-256 checked on every import against FROZEN below):
#   sim6.py (one simulator for all three designs; M3 runs with wext off, which is sim5.py's behaviour), scores.py, packlib.py, dlf.py (parse),
#   ei6.py (design table CONF, score / tilted / rank_score / issuance; executed from its own source with only its first line
#   'from lib6 import *' replaced by the names it needs), capbuild_fwd.py (= capbuild.py with the fixed 'today' cut set to the decision date).
# PAPER ONLY. No real money, no broker orders, the AI never places trades.
import os, sys, hashlib, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); FZ = HERE + '/multi_frozen'
FROZEN = {'sim6.py': 'f9efc4bc01ecf5ebb4ed1cbdbbe167e2903e3b611a5468642b737b7d474e1692',
          'ei6.py': 'fe2365960e42a67f5ed60c571c1e038ab5d1be4d81f6616a0987845030d18a53',
          'capbuild.py': 'bf36db53ed495653e8c919e493682f1b78290f5da62ff97f32e863c76dbcc7a6',
          'packlib.py': '7609204f704c9e3be50a00fd2e3e41883d18745a697fffa654a5f6fae7d58093',
          'scores.py': '9b54242c52ad17188a71c9f83acfc722217fb10eac1aa4ec35384b4152d4ebb0',
          'dlf.py': 'f2e9f3d2f92cfeb66db416b0d5efd39af62ca848beffbe2d628aa4a6a39cb5e1'}

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

for f, h in FROZEN.items():
    assert sha(f'{FZ}/{f}') == h, f'frozen engine file changed: {f}'
if FZ not in sys.path: sys.path.insert(0, FZ)
import sim6 as S6, scores as SC, packlib as PL, capbuild_fwd as CB
from dlf import parse as parse_fundamentals
_src = open(f'{FZ}/ei6.py').read()
assert _src.splitlines()[1] == 'from lib6 import *'
EI = dict(np=np, pd=pd, SC=SC, S6=S6, __name__='ei6_frozen')
exec(compile(_src.replace('from lib6 import *', 'pass  # names supplied by multi_engine.py', 1), f'{FZ}/ei6.py', 'exec'), EI)
CONF = EI['CONF']; M3KW = EI['M3KW']
DESIGNS = ('M3', 'EI10I', 'CW')


def make_mkt(pack_path, mkt, cfg, fd=None, today=None):
    """Market object exactly as lib5.load / lib6.load6 build it: universe = 100 most traded, fund = the local index fund's
    total-return series from the pack (imputed distributions for accumulating funds, as lib5.load), caps from capbuild."""
    mk = S6.Mkt(pack_path, U=100, tick=cfg.get('tick', 'x'))
    if cfg.get('impute'):
        fy_ = np.zeros(mk.K)
        for k in range(mk.K):
            with np.errstate(invalid='ignore'): m = mk.pk['vrank'][k] <= 30
            if m.any(): w = np.nan_to_num(mk.medtv[k, m]); fy_[k] = float((mk.divy[k, m] * w).sum() / max(w.sum(), 1e-12))
        mk.fund_y = fy_
    mk.name = mkt; mk.fundres = {}; mk.cfg = cfg; mk.wext = None
    if fd is not None:
        CB.TODAY = today or str(pd.Timestamp(mk.dd[-1]).date())
        mk.fd = fd; mk.cap, mk.shk, mk.capst = CB.build(fd, mk.pk, verbose=False)
    return mk


def ranks(mk, design):
    """(rank array, engine keywords) for a design, via ei6.setup (sets mk.wext for the cap-weighted designs)"""
    return EI['setup'](mk, design)


def control_base(mk, salt):
    """64-bit keys that depend only on (salt = market|design, decision date, company code): stable when the pack is rebuilt with more months"""
    K, N = mk.vrank.shape; h = np.zeros((K, N), np.uint64)
    for k in range(K):
        dkey = pd.Timestamp(mk.dd[k]).strftime('%Y%m%d')
        h[k] = [int.from_bytes(hashlib.sha256(f'{salt}|{dkey}|{c}'.encode()).digest()[:8], 'big') for c in mk.cols]
    return h


def _mix(x):
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9); x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


def control_ranks(mk, design, seed, base):
    """Random-portfolio control with a fixed seed: uniform scores u = splitmix64(key xor seed) / 2^64, key from control_base.
    M3: random scores in M3's machinery (as look5's rnd controls); EI10I and CW: the cap-weighted machinery tilted (a = 1) by random scores
    (report 77's random-tilt books)."""
    with np.errstate(over='ignore'):
        u = (_mix(base ^ (np.uint64(seed) * np.uint64(0x9E3779B97F4A7C15))) >> np.uint64(11)).astype(np.float64) / 2.0 ** 53
    K, N = mk.vrank.shape
    sc = np.where(np.isfinite(mk.vrank0), u, np.nan)
    if design == 'M3':
        r = np.full(sc.shape, np.nan)
        for k in range(K):
            m = np.flatnonzero(mk.uni[k] & np.isfinite(sc[k]))
            if len(m): o = np.lexsort((mk.vrank[k, m], -sc[k, m])); r[k, m[o]] = np.arange(1, len(m) + 1)
        mk.wext = None; return r, dict(M3KW)
    um = mk.uni; cap = np.where(um & np.isfinite(mk.cap), mk.cap, np.nan); p = mk.pct_of(np.where(np.isfinite(cap), sc, np.nan))
    w = cap * np.maximum(0.0, 1 + 1.0 * (2 * p - 1)); w[~np.isfinite(w)] = np.nan; w = np.where(w > 0, w, np.nan)
    r = np.full(w.shape, np.nan)
    for k in range(K):
        m = np.flatnonzero(np.isfinite(w[k]) & mk.uni[k])
        if len(m): o = np.lexsort((mk.vrank[k, m], -w[k, m])); r[k, m[o]] = np.arange(1, len(m) + 1)
    mk.wext = w; return r, dict(CONF[design][3])


def run(mk, rk, kw, S0, k0, k1, tau):
    return S6.run(mk, rk, S0, k0, k1, tau=tau, regime='CL', **kw)


def run_fund(mk, S0, k0, k1, tau):
    """lib5.fund: the fund-only account (core weight 1), no MER beyond the fund's own price"""
    return S6.run(mk, None, S0, k0, k1, tau=tau, regime='CL', contrib=0.0, mer=0.0, broker='std')
