# CA_SUSPECT check (AMENDMENT_data_corporate_actions.md, procedure step 2) -- READ ONLY: prints, writes nothing, changes no state.
# For trading day d: every code held (or with an open order) in any paper state file under STATE_DIR is flagged CA_SUSPECT when its raw
# close fell 8% or more since its previous close (within 5 sessions) and the day has no dividend row, no split row and no row of the
# corporate-action table for it. Main books only; --twins also watches the random twins. The record keeper checks each flag by hand against the company's ASX announcements (in specie,
# demerger, scheme, return of capital); nearly all are real falls and are cleared. Usage: python3 ca_check.py [YYYY-MM-DD ...]
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_lib as P

DROP = -0.08

def twin(x): return 'RND' in str(x.get('id', '')) or str(x.get('kind', '')).endswith('RND')

def codes_in(x, out, twins=False):
    """codes of holdings and open orders anywhere in a state file (structures differ by line); random twins skipped unless twins."""
    if isinstance(x, dict):
        if not twins and twin(x): return out
        for k, v in x.items():
            if k == 'holdings' and isinstance(v, dict):
                for h in v.values():
                    if isinstance(h, dict) and isinstance(h.get('code'), str): out.add(h['code'])
            elif k in ('orders', 'buys', 'sells') and isinstance(v, list):
                for o in v:
                    if isinstance(o, dict) and isinstance(o.get('code'), str): out.add(o['code'])
            codes_in(v, out, twins)
    elif isinstance(x, list):
        for v in x: codes_in(v, out, twins)
    return out

def watched(twins=False):
    out = {}
    for f in sorted(glob.glob(P.STATE_DIR + '/*.json')):
        try: cs = codes_in(json.load(open(f)), set(), twins)
        except Exception: continue
        for c in cs: out.setdefault(c, []).append(os.path.basename(f))
    return out

def suspects(d, w=None):
    w = watched() if w is None else w
    m = P.load_day(d)
    if m is None: return None
    prev = []; x = d
    for _ in range(5):
        x = P.prev_session(x); mx = P.load_day(x)
        if mx is not None: prev.append(mx)
    out = []
    for c, files in sorted(w.items()):
        p1 = m['close'].get(c)
        p0 = next((mx['close'][c] for mx in prev if c in mx['close']), None)
        if p1 is None or not p0: continue
        r = p1 / p0 - 1
        if r <= DROP and c not in m['div'] and c not in m['split']:
            out.append(dict(date=d, code=c, raw_move=round(r, 4), prev_close=p0, close=p1, books=','.join(files)))
    return out

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--twins']; w = watched('--twins' in sys.argv)
    for d in (a or [P.prev_session(P.first_session_on_or_after(__import__('time').strftime('%Y-%m-%d')))]):
        s = suspects(d, w)
        if s is None: print(d, 'no bulk file'); continue
        print(d, f'{len(w)} codes watched;', f'{len(s)} CA_SUSPECT' + (':' if s else ''))
        for r in s: print('  CA_SUSPECT', r)
