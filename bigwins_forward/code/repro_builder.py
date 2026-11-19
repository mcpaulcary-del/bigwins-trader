# v1.3 reproduction check 1: the v1.3 production prep (bw13_prep.py) + the frozen report-64 engine (deepdive/code/engine_dd.py, unchanged)
# must give report 64's unseen-B figures (deepdive/out/phase2_unseenB.json).   python3 -I repro_builder.py
import sys, os, pickle, json, numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
FW = S + '/bigwins_forward'
sys.path.insert(0, FW + '/code'); import bw13_prep
RULE = sys.argv[1] if len(sys.argv) > 1 else 'frozen'
D = bw13_prep.build('2026-11-13', dup_rule=RULE)
if RULE == 'frozen':
    B0 = pickle.load(open(S + '/deepdive/data/bundle_eod.pkl', 'rb'))
    # (a) bundle equality with the frozen builder bundle
    assert list(D['cols']) == list(B0['cols']) and (D['dates'] == B0['dates']).all()
    eq = lambda a, b: bool(np.array_equal(a, b, equal_nan=True))
    chk = dict(Pv=eq(D['Pv'], B0['Pv']), xjo=eq(D['xjo'], B0['xjo']), xtr=eq(D['xtr'], B0['xtr']), fail=eq(D['fail'], B0['fail']), take=eq(D['take'], B0['take']),
               DIVD=(D['DIVD'] == B0['DIVD']), ME=eq(D['ME'], B0['ME']))
    nt = 0; bad = 0
    for k, t in B0['tabs'].items():
        m = t['vrank'] <= 500; u = D['tabs'][k]
        for f in ('col', 'medval', 'price', 'M1', 'M2', 'M3', 'M5'):
            nt += 1; bad += not eq(t[f][m], u[f][:int(m.sum())])
    chk['tables_fields_compared'] = nt; chk['tables_fields_different'] = bad
    print('bundle equality', chk, flush=True)
    del B0
# (b) engine run: the table of the file's last day is not a month-end table (13 Nov 2026 is not a month-end) -> removed
kl = max(D['tabs']); 
if D['ME'][kl] == len(D['dates']) - 1 and D['dates'][-1].month == (D['dates'][-1] + pd.offsets.BDay(1)).month: del D['tabs'][kl]
tmp = FW + '/out/_bundle13_engine.pkl'; pickle.dump({k: v for k, v in D.items() if k not in ('Craw', 'Hraw', 'Lraw', 'V0')}, open(tmp, 'wb'), protocol=4); dl = D['duplog']; del D
os.environ['DD_BUNDLE'] = tmp
sys.path.insert(0, S + '/deepdive/code')
import lib_dd as L
E = L.E
ev = L.evaluate({}, L.EOD, div='cash'); ix = L.index_stats(L.EOD, tr=True)
ref = json.load(open(S + '/deepdive/out/phase2_unseenB.json'))
rows = []
for Sz in L.SIZES:
    for k in ('gross', 'net', 'taxA', 'taxB', 'maxdd', 'ex_mean', 'ex_t', 'te', 'turnover'):
        rows.append((f'H82 {Sz}', k, ref['H82_v1.1'][str(Sz)][k], float(ev[Sz][k])))
    for k in ('net', 'taxA', 'taxB', 'maxdd'):
        rows.append((f'comparator {Sz}', k, ref['index'][str(Sz)][k], float(ix[Sz][k])))
df = pd.DataFrame(rows, columns=['account', 'measure', 'report64', 'v13_prep_frozen_engine']); df['diff_pt'] = (df.v13_prep_frozen_engine - df.report64) * 100
print(df.to_string()); df.to_csv(FW + f'/out/repro_check1_frozen_engine{"" if RULE == "frozen" else "_A7b"}.csv', index=False); os.remove(tmp)
pd.DataFrame(dl, columns=['dropped_old_code', 'kept_code', 'old_code_last_day']).to_csv(FW + f'/out/dup_codes_{RULE}.csv', index=False)
print('max |diff| pt', df.diff_pt.abs().max())
