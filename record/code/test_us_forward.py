# Tests for paper_us_forward.py. Scratch copies only: the real ledger, store, outputs, /home/user/asx-trader, the scheduled tasks and the
# frozen code are never written. No network: every test runs with sockets disabled; downloads go to a fake EODHD transport.
# usage: python3 test_us_forward.py [names...]   (or pytest -x test_us_forward.py)
import os, sys, io, json, gzip, time, shutil, socket, hashlib, math, contextlib
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import paper_us_forward as U

S = U.S; T = S + '/usfwd_test/'; os.makedirs(T, exist_ok=True)


# ---------------------------------------------------------------- no network anywhere in the tests
class NoNet(Exception): pass
def _blocked(*a, **k): raise NoNet('network used in a test')
socket.socket.connect = _blocked; socket.create_connection = _blocked; socket.getaddrinfo = _blocked


_C = {}
def E(): return _C.setdefault('E', U.engines())
def trimmed():
    """the job's own path on the real bootstrap store, no forward rows: assemble -> eng4.load"""
    if 'tr' not in _C:
        st = U.Store(U.DATA); P = U.assemble(_ro(st), upto='2026-11-23'); ser = U.research_bm(); w = T + 'w_trim'
        A, F = U.load_A(E(), P, ser, w, provisional=False); A.colj = {str(c): j for j, c in enumerate(A.code)}; A.NSp = P.NSp
        _C['tr'] = (P, A, F, ser, w)
    return _C['tr']
def original():
    """the studies' own loading of research_us/data/panel.npz (eng4.load; eng.R pointed at a scratch folder with the same csv files)"""
    if 'orig' not in _C:
        w = T + 'orig'; U.write_bm(w, U.research_bm())
        if not os.path.exists(w + '/panel.npz'): os.symlink(U.PANEL, w + '/panel.npz')
        eng, eng4 = E()['eng'], E()['eng4']; old = eng.R; eng.R = w + '/'
        try: B, FB = eng4.load()
        finally: eng.R = old
        _C['orig'] = (B, FB, w)
    return _C['orig']
class _ROStore(U.Store):
    """the real store read-only: no batches after the panel end are used for the historical parity tests"""
    def batches(self): return []
def _ro(st): return _ROStore(st.root)


# ---------------------------------------------------------------- 1. engine parity (each frozen rule through the new code path)
def test_parity_P1_P8_funds_trimmed():
    P, A, F, ser, w = trimmed(); B, FB, _ = original(); eng2, eng4 = E()['eng2'], E()['eng4']
    for s in ('2023-10', '2025-06'):
        for nm, mk in (('P1', lambda X, a, b: eng4.Leaders(eng4.score_lists(X, 'M3', a, b), 20, 'L25', gate=True)), ('P8', lambda X, a, b: eng4.TopTV(eng4.score_lists(X, 'RANK', a, b), 20, 40))):
            for tax in ('personal', 'super'):
                a, b = A.K(s), A.K('2026-10'); c, d = B.K(s), B.K('2026-10')
                r1 = eng2.sim(A, mk(A, a, b), 10000, a, b, tax=tax, hs=eng2.stock_hs(A))['final']; r2 = eng2.sim(B, mk(B, c, d), 10000, c, d, tax=tax, hs=eng2.stock_hs(B))['final']
                assert r1 == r2, (nm, s, tax, r1, r2)
        for fk in ('IVV', 'VGS'):
            assert eng2.fund(A, F[fk], 1e4, A.K(s), A.K('2026-10'), 'personal')['final'] == eng2.fund(B, FB[fk], 1e4, B.K(s), B.K('2026-10'), 'personal')['final']


def test_parity_A3_trimmed():
    P, A, F, ser, w = trimmed(); B, FB, wo = original(); eng2 = E()['eng2']
    Ep, TGT, on = U.etf_panel_a3(E(), A, ser, w)
    eng = E()['eng']; old = (eng.R, eng2.R2); eng.R = wo + '/'; eng2.R2 = U.ETF2       # research_us2's own ETF panel (spliced synthetic funds), files read in place
    try: Eo = eng2.etf_panel(B)
    finally: eng.R, eng2.R2 = old
    C = Eo.cols; sma = pd.Series(Eo.TRf[:, C['SPY']]).rolling(200).mean().values; ON = Eo.TRf[B.me, C['SPY']] > sma[B.me]; TG = np.where(ON, C['UPRO'], C['BILL'])
    for s in ('2023-10', '2025-03'):
        for tax in ('personal', 'super'):
            r1 = eng2.sim(Ep, eng2.One(TGT), 10000, A.K(s), A.K('2026-10'), tax=tax, hs=Ep.hs)['final']; r2 = eng2.sim(Eo, eng2.One(TG), 10000, B.K(s), B.K('2026-10'), tax=tax, hs=Eo.hs)['final']
            assert abs(r1 / r2 - 1) < 1e-12, (s, tax, r1, r2)


def test_parity_T1_trimmed():
    P, A, F, ser, w = trimmed(); B, FB, wo = original(); eng3 = E()['eng3']; real = pd.read_csv
    U.prep3(E(), A, w, ser); EV, st = U.t1_events(E(), A, _ro(U.Store(U.DATA)), print)
    B2 = E()['auditfix'].apply(B)
    from unittest import mock
    with mock.patch.object(eng3.pd, 'read_csv', lambda p, *a, **k: real(wo + '/DTB3.csv' if str(p).endswith('DTB3.csv') else p, *a, **k)): eng3.prep(B2)
    if 'EVo' not in _C: _C['EVo'] = eng3.signals(B2, eng3.load_feed())[0]
    EVo = _C['EVo']; A.payout = A.pay_fix
    try:
        for tax in ('personal', 'super'):
            q = eng3.sim(A, eng3.Event(EV, 20, 396), 10000, A.K('2025-07'), A.K('2026-10'), tax=tax, hs=eng3.stock_hs(A)); r1 = q['final']; assert q['nbuy'] > 5
            r2 = eng3.sim(B2, eng3.Event(EVo, 20, 396), 10000, B2.K('2025-07'), B2.K('2026-10'), tax=tax, hs=eng3.stock_hs(B2))['final']
            assert abs(r1 / r2 - 1) < 1e-12, (tax, r1, r2)
    finally:
        A.payout = A.pay_reg; B2.payout = B.payout


def _t1_ev_trim(A):
    if 'EVt' not in _C:
        eng3 = E()['eng3']; d = eng3.load_feed(); d = d[d.td >= pd.Timestamp(U.TRIM)]; _C['EVt'] = (eng3.signals(A, d)[0], {})
    return _C['EVt']


def test_parity_P6_recorded_and_refit():
    """(a) the frozen B25-G3 book on research_us5's own scores reproduces the sealed run (sealed.json by_start, personal, A$100k, 6 starts);
    (b) features rebuilt by c5.build on the job's panel equal the research table; (c) the December 2025 refit by the job reproduces the
    sealed run's G3 and W scores for Dec 2025 - Oct 2026 (LightGBM, fixed seeds)."""
    P, A, F, ser, w = trimmed(); eng2, lib5, c5 = E()['eng2'], E()['lib5'], E()['c5']
    base = pd.read_pickle(U.DATA + '/p6/base_table.pkl.gz'); KS, KE = A.K('2023-10'), A.K('2026-10')
    L = lib5.lists(base, 'G3', KS, KE); FW = lib5.flags(base, 'W', KS, KE); rec = json.load(open(S + '/research_us5/out/sealed.json'))['personal']['by_start']
    for s in range(6):
        r = eng2.sim(A, lib5.Book(L, FW, 25, 13), 100000, KS + s, KE, tax='personal', hs=eng2.stock_hs(A))['cagr']
        assert abs(r - rec[s]) < 1e-12, (s, r, rec[s])
    A.k1 = KE; A.KE = KE
    D, b0 = U.p6_table(E(), A, U.Store(U.DATA), print)
    kr = A.K(U.REBUILD_FROM); m = D[D.k >= kr].merge(b0[b0.k >= kr], on=['k', 'j'], suffixes=('', '_r'))
    assert len(m) == (b0.k >= kr).sum() > 5000
    for c in ['x_' + x for x in c5.PRICE]: assert np.nanmax(np.abs(m[c] - m[c + '_r'])) < 1e-12, c
    kf = A.K('2025-12'); Dw = D.copy()
    with contextlib.redirect_stdout(io.StringIO()): Dw, _ = c5.walk(A, Dw, kf, KE)
    m = Dw[(Dw.k >= kf) & (Dw.k <= KE)].merge(b0, on=['k', 'j'], suffixes=('', '_r'))
    assert np.nanmax(np.abs(m.G3 - m.G3_r)) < 1e-12 and np.nanmax(np.abs(m.W - m.W_r)) < 1e-12, (np.nanmax(np.abs(m.G3 - m.G3_r)), np.nanmax(np.abs(m.W - m.W_r)))


def full_history():
    """the job's path on a bootstrap that keeps the whole panel (scratch store), for windows that start before the job's trim"""
    if 'full' not in _C:
        st = U.Store(T + 'store_full')
        if not os.path.exists(st.root + '/boot.npz'): U.bootstrap_base(st, E(), print, trim='1998-06-01')
        P = U.assemble(st); ser = U.research_bm(); w = T + 'w_full'; A, F = U.load_A(E(), P, ser, w, provisional=False)
        _C['full'] = (P, A, F, ser, w)
    return _C['full']


def test_recorded_P1_P8_A3():
    """12-start means through the job's code path equal the registered results: research_us4 P1/P8 (2015-2026, A$100k, personal and super)
    and research_us2 A6 (= A3 on real UPRO, Jul 2009 - Oct 2026)."""
    P, A, F, ser, w = full_history(); eng2, eng4 = E()['eng2'], E()['eng4']
    r4 = pd.read_csv(S + '/research_us4/out/main_results.csv').set_index(['trial', 'period'])
    a, b = A.K('2014-12'), A.K('2026-10')
    O1 = eng4.score_lists(A, 'M3', a, b); O8 = eng4.score_lists(A, 'RANK', a, b)
    for nm, mk in (('P1 LEAD20', lambda: eng4.Leaders(O1, 20, 'L25', gate=True)), ('P8 TOPTV20', lambda: eng4.TopTV(O8, 20, 40))):
        for tax in ('personal', 'super'):
            c = np.mean([eng2.sim(A, mk(), 100000, a + s, b, tax=tax, hs=eng2.stock_hs(A))['cagr'] for s in range(12)])
            assert abs(c - r4.loc[(nm, 'PRI'), f'{tax}_100000']) < 1e-9, (nm, tax, c, r4.loc[(nm, 'PRI'), f'{tax}_100000'])
    Ep, TGT, on = U.etf_panel_a3(E(), A, ser, w); r2 = pd.read_csv(S + '/research_us2/out/extra_results.csv').set_index(['trial', 'period'])
    a = A.K('2009-07')
    for tax in ('personal', 'super'):
        c = np.mean([eng2.sim(Ep, eng2.One(TGT), 100000, a + s, b, tax=tax, hs=Ep.hs)['cagr'] for s in range(12)])
        assert abs(c - r2.loc[('A6 A3 rule, real UPRO only', 'FULL'), f'{tax}_100000']) < 1e-9, (tax, c)


def test_recorded_T1():
    """T1 with the audit payout fix through the job's code path equals research_audit_us R5 (PRIMARY second half, Dec 2010 - Dec 2017, A$100k)."""
    P, A, F, ser, w = full_history(); eng3 = E()['eng3']
    U.prep3(E(), A, w, ser); EV = eng3.signals(A, eng3.load_feed())[0]; A.payout = A.pay_fix
    rec = pd.read_csv(S + '/research_audit_us/out/fix_us3_main_PRIMARY_T1_T2_T3.csv'); rec = rec[(rec.trial == 'T1') & (rec.period == 'H2')].iloc[0]
    a0, b0 = A.K('2003-12'), A.K('2017-12'); m = (a0 + b0) // 2
    c = np.mean([eng3.sim(A, eng3.Event(EV, 20, 396), 100000, m + s, b0, tax='personal', hs=eng3.stock_hs(A))['cagr'] for s in range(12)])
    A.payout = A.pay_reg
    assert abs(c - rec.personal_100000) < 1e-9, (c, rec.personal_100000)


def test_ranking_bootstrap_matches_panel():
    """the forward ranking code on the bootstrap's daily traded value reproduces the panel's month-end medians and ranks (Oct 2026)"""
    st = U.Store(U.DATA); assert os.path.exists(st.root + '/boot_tv.npz'), 'bootstrap not done'
    P = U.assemble(_ro(st)); b = np.load(st.root + '/boot.npz', allow_pickle=True)
    i = int(b['me'][-1]); MED, RK = U.ranks(P, np.array([i]), P.arrays['delisted'], P.arrays['TR'].shape[1] - 2)
    rk0 = b['RK'][-1]; med0 = b['MED'][-1]; top = np.flatnonzero(np.isfinite(rk0[:P.NSp]) & (rk0[:P.NSp] <= 2000))
    rel = np.abs(MED[0, top] / med0[top] - 1); same = np.mean(RK[0, top] == rk0[top]); within = np.mean(np.abs(RK[0, top] - rk0[top]) <= 5)
    print(f'  ranks: median |MED diff| {np.median(rel):.2e}, 95th pct {np.percentile(rel, 95):.2e}; same rank {same:.3f}; within 5 ranks {within:.3f}')
    # ranks can differ only by series that were ranked on 30 Oct but had stopped trading before the bootstrap (not fetched; they have no
    # close at any forward month-end): among the series ranked by both, the order must be identical
    both = top[np.isfinite(RK[0, top])]; gone = top[~np.isfinite(RK[0, top]) | (MED[0, top] == 0)]
    revised = both[np.abs(MED[0, both] / med0[both] - 1) > 1e-5]; ok = both[~np.isin(both, revised)]
    print(f'  ranked by both {len(both)}; panel-ranked but stopped before 23 Nov: {len(gone)}; vendor-revised medians: {[str(P.arrays["code"][j]) for j in revised]}')
    assert np.median(rel) < 1e-6 and len(revised) <= 0.01 * len(both)
    assert np.array_equal(ok[np.argsort(RK[0, ok], kind='stable')], ok[np.argsort(rk0[ok], kind='stable')])
    assert np.mean(np.abs(RK[0, top] - rk0[top]) <= len(gone) + 2) > 0.99 and not any(str(P.arrays['code'][j]) in U.ETFS for j in np.flatnonzero(np.isfinite(RK[0])))


# ---------------------------------------------------------------- 2. forward pipeline on scratch copies with a fake EODHD
class Fake:
    """fake EODHD: bulk days (random walk from the store's last closes, adjusted = close), the stored symbol list, benchmark csv files that
    repeat the research history and extend it, no insider rows. Counts calls; never touches the network."""
    def __init__(self, store, fail_after=None):
        self.store = store; self.calls = []; self.fail_after = fail_after
        z = np.load(store.batches()[-1]); i = -1
        self.base = {str(c): (float(z['close'][i, n]), float(z['vol'][i, n])) for n, c in enumerate(z['codes']) if np.isfinite(z['close'][i, n])}
        self.base_day = U.dstr(z['days'][-1]); self._paths()
    def _paths(self):
        self.ss = [d for d in U.sessions() if self.base_day < d <= '2027-03-31']; self.cix = {c: n for n, c in enumerate(sorted(self.base))}
        z = np.random.default_rng(1).normal(0.0005, 0.02, (len(self.cix), len(self.ss))); self.cum = np.cumsum(z, axis=1)
    def px(self, c, day):
        c0, v0 = self.base[c]; n = int(np.searchsorted(self.ss, day, side='right'))
        return (c0 if n == 0 else c0 * math.exp(self.cum[self.cix[c], n - 1])), v0
    def __call__(self, path, params):
        self.calls.append((path, dict(params)))
        if self.fail_after is not None and len(self.calls) > self.fail_after: raise KeyboardInterrupt('fake interruption (job killed)')
        assert not path.startswith('user')
        if path.startswith('eod-bulk-last-day/US'):
            d = params['date']; rows = []
            for c in self.base:
                x, v = self.px(c, d); rows.append(dict(code=c, exchange_short_name='US', date=d, close=round(x, 4), adjusted_close=round(x, 4), volume=v))
            return 200, json.dumps(rows).encode()
        if path.startswith('exchange-symbol-list'):
            sy = self.store.symbols(); return 200, json.dumps([dict(Code=c, Name=v[0], Exchange=v[1], Type=v[2], Isin=v[3]) for c, v in sy.items() if not c.startswith('__')]).encode()
        if path.startswith('insider-transactions'): return 200, b'[]'
        if path.startswith('eod/'):
            sym = path[4:]
            if sym not in U.BENCH: return 404, b''
            h = U.research_bm()[sym]; h = h[h.Date >= params['from']]; last = h.iloc[-1]; rows = list(zip(h.Date, h.Close, h.Adjusted_close)); x = last.Close
            for d in [d for d in U.sessions() if last.Date < d <= '2027-02-28']:
                x *= 1.0003; rows.append((d, x, x * last.Adjusted_close / last.Close))
            df = pd.DataFrame(rows, columns=['Date', 'Close', 'Adjusted_close']); df['Open'] = df.Close; df['High'] = df.Close; df['Low'] = df.Close; df['Volume'] = 1000
            return 200, df[['Date', 'Open', 'High', 'Low', 'Close', 'Adjusted_close', 'Volume']].to_csv(index=False).encode()
        return 404, b''


def scratch(tag, registered=True):
    """scratch copies of the store, a ledger copy (plus a fake registration of the monthly amendment), and empty out/state folders"""
    root = T + f'run_{tag}'; shutil.rmtree(root, ignore_errors=True); os.makedirs(root)
    shutil.copytree(U.DATA, root + '/data', ignore=shutil.ignore_patterns('bootchunks', 'credits.json', 'raw_index.csv'))
    shutil.copy(U.REC + '/LEDGER.jsonl', root + '/LEDGER.jsonl')
    import fwd_ledger as L
    L.LED = root + '/LEDGER.jsonl'
    if registered: L.append(event='TEST registration of the monthly amendment (scratch ledger)', kind='amendment', amendment=U.AMEND_MONTHLY)
    class A_: pass
    a = A_(); a.out = root + '/out'; a.state = root + '/state'; a.data = root + '/data'; a.ledger = root + '/LEDGER.jsonl'; a.offline = False; a.prefetch = False
    a.books = 'A3,P1,P8,P6,T1'; os.makedirs(a.state, exist_ok=True)
    return a, L


def _run(a, L, today, fake, day_cap=U.DAY_CAP):
    old = U.today_utc; U.today_utc = (lambda d=today: d); oldcap = U.DAY_CAP
    try:
        logs = []
        def log(*x): logs.append(' '.join(str(v) for v in x))
        orig = U.Credits.__init__
        def init(self, path, day_cap=day_cap, **k): orig(self, path, day_cap=day_cap, **{kk: vv for kk, vv in k.items() if kk != 'day_cap'})
        U.Credits.__init__ = init
        try: r = U.run(a, log, L, transport=fake)
        finally: U.Credits.__init__ = orig
        return r, logs
    finally:
        U.today_utc = old


def test_idempotent_month_and_ledger():
    a, L = scratch('idem'); st = U.Store(a.data); fk = Fake(st)
    n0 = len(L.entries()); r, logs = _run(a, L, '2026-12-02', fk)
    es = L.entries(); assert len(es) == n0 + 1 and es[-1]['kind'] == 'info_us_forward' and es[-1]['asof'] == '2026-11-30', logs[-5:]
    e = es[-1]; assert set(e['values']) >= {'A3', 'P1', 'P8', 'P6', 'T1', 'IVV', 'VGS', 'NDQ'} and e['inputs_sha256'] and set(e['orders']) == {'A3', 'P1', 'P8', 'P6', 'T1'}, e['orders']
    md = open(a.out + '/US_FORWARD.md').read(); assert U.LABEL in md and 'first reading Dec 2027' in md
    lat = pd.read_csv(a.out + '/us_forward_latest.csv'); assert len(lat) == 8 and (lat.months == 0).all()
    h1 = {f: U.sha_f(f'{a.out}/{f}') for f in os.listdir(a.out)}; calls = len(fk.calls)
    r, logs = _run(a, L, '2026-12-02', fk)                           # the same day again
    r, logs2 = _run(a, L, '2026-12-03', fk)                          # and the next day
    assert len(L.entries()) == n0 + 1 and any('nothing due' in x for x in logs2), logs2
    assert {f: U.sha_f(f'{a.out}/{f}') for f in os.listdir(a.out)} == h1
    assert len(fk.calls) == calls + 0 or all(not c[0].startswith('eod-bulk') for c in fk.calls[calls:]), 'bulk days downloaded twice'
    L.verify()
    _C['idem'] = a


def test_second_month_and_refit():
    """January run books December (the P6 model is refitted at the December month-end), values move, history keeps both months"""
    a = _C.get('idem') or (test_idempotent_month_and_ledger() or _C['idem'])
    import fwd_ledger as L
    L.LED = a.ledger; st = U.Store(a.data); fk = Fake(st)
    r, logs = _run(a, L, '2027-01-05', fk)
    e = L.entries()[-1]; assert e['asof'] == '2026-12-31' and e['months'] == 1, logs[-6:]
    assert any('P6 fit 2026-12' in x for x in logs), [x for x in logs if 'P6' in x]
    h = pd.read_csv(a.state + '/us_forward_history.csv'); assert sorted(h['asof'].unique()) == ['2026-11-30', '2026-12-31']
    pr = pd.read_csv(a.data + '/p6/preds.csv.gz'); assert set(pr.fit) == {'2025-12', '2026-12'}


def test_resume_after_interruption():
    """a run stopped part way (fake interruption during the bulk downloads) books nothing; the next run resumes from the stored batch and books
    exactly what an uninterrupted run books"""
    a, L = scratch('resume'); a.books = 'A3,P1,P8'; st = U.Store(a.data)
    fk = Fake(st, fail_after=3); n0 = len(L.entries()); nb0 = len(st.batches())
    try: _run(a, L, '2026-12-02', fk); assert False, 'not interrupted'
    except KeyboardInterrupt: pass
    assert len(L.entries()) == n0 and not os.path.exists(a.out + '/US_FORWARD.md') and len(st.batches()) == nb0 + 1   # partial batch kept
    fk2 = Fake(st); fk2.base, fk2.base_day = fk.base, fk.base_day; fk2._paths()
    r, logs = _run(a, L, '2026-12-02', fk2)
    assert len(L.entries()) == n0 + 1, logs[-6:]
    b, Lb = scratch('resume_ref'); b.books = 'A3,P1,P8'; fk3 = Fake(U.Store(b.data)); r, _ = _run(b, Lb, '2026-12-02', fk3)
    v1 = pd.read_csv(a.out + '/us_forward_latest.csv').set_index('rule'); v2 = pd.read_csv(b.out + '/us_forward_latest.csv').set_index('rule')
    assert np.allclose(v1.value_personal, v2.value_personal) and np.allclose(v1.value_super, v2.value_super)


def test_budget_guard():
    c = U.Credits(T + 'credits_test.json', clock=lambda: '2027-03-10'); c.d = dict(days={}); c.save()
    c.spend(9950, 'run');
    try: c.check(100, 'run'); assert False, 'day cap not enforced'
    except U.Budget: pass
    c.check(50, 'run')
    c2 = U.Credits(T + 'credits_test2.json', clock=lambda: '2027-03-10'); c2.d = dict(days={'2026-06-01': {'run': 20000}, '2026-12-01': {'run': 15990}, '2026-11-26': {'boot': U.BOOT_CAP - 200}}); c2.save()
    try: c2.check(100, 'run'); assert False, '365-day cap not enforced'
    except U.Budget: pass
    c2.check(5, 'run'); c2.check(150, 'boot')
    try: c2.check(250, 'boot'); assert False, 'bootstrap cap not enforced'
    except U.Budget: pass
    api = U.Api(c, print, transport=lambda p, q: (200, b'{}'))
    try: api.get('user', {}, 0, 'run'); assert False, 'account endpoint allowed'
    except AssertionError as e: assert 'account endpoint' in str(e)
    # a run with a 350-credit day cap stops, saves what it fetched, books nothing, and finishes on a later day
    a, L = scratch('budget'); a.books = 'A3'; st = U.Store(a.data); fk = Fake(st); n0 = len(L.entries())
    r, logs = _run(a, L, '2026-12-02', fk, day_cap=350)
    assert len(L.entries()) == n0 and any('day cap' in x for x in logs), logs[-5:]
    used = json.load(open(a.data + '/credits.json'))['days']['2026-12-02']; assert sum(used.values()) <= 350
    r, logs = _run(a, L, '2026-12-03', Fake(st), day_cap=350)
    r, logs = _run(a, L, '2026-12-04', Fake(st), day_cap=350)
    assert len(L.entries()) == n0 + 1, logs[-5:]


def test_not_registered_no_ledger_then_catch_up():
    a, L = scratch('unreg', registered=False); a.books = 'A3'; st = U.Store(a.data); n0 = len(L.entries())
    r, logs = _run(a, L, '2026-12-02', Fake(st))
    assert len(L.entries()) == n0 and os.path.exists(a.out + '/US_FORWARD.md') and any('NO ledger entry' in x for x in logs)
    L.append(event='TEST registration', kind='amendment', amendment=U.AMEND_MONTHLY)
    r, logs = _run(a, L, '2026-12-03', Fake(st))
    es = L.entries(); assert es[-1]['kind'] == 'info_us_forward' and es[-1]['asof'] == '2026-11-30' and len(es) == n0 + 2


def test_no_network_guard():
    try: socket.create_connection(('eodhd.com', 443)); assert False
    except NoNet: pass


ORDER = ['test_no_network_guard', 'test_budget_guard', 'test_parity_P1_P8_funds_trimmed', 'test_parity_A3_trimmed', 'test_parity_T1_trimmed', 'test_parity_P6_recorded_and_refit',
         'test_ranking_bootstrap_matches_panel', 'test_recorded_P1_P8_A3', 'test_recorded_T1', 'test_idempotent_month_and_ledger', 'test_second_month_and_refit',
         'test_resume_after_interruption', 'test_not_registered_no_ledger_then_catch_up']
if __name__ == '__main__':
    names = sys.argv[1:] or ORDER; bad = 0
    for n in names:
        t0 = time.time()
        try: globals()[n](); print(f'PASS {n} ({time.time() - t0:.0f}s)', flush=True)
        except Exception as e:
            import traceback; bad += 1; print(f'FAIL {n} ({time.time() - t0:.0f}s): {type(e).__name__}: {str(e)[:600]}', flush=True); traceback.print_exc()
    print('failures', bad); sys.exit(1 if bad else 0)
