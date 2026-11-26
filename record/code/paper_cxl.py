# Big Wins forward PAPER record -- SHADOW line CXL v1.0: "cap-weighted, momentum losers excluded" (report 81 design D2, §4.5).
# Governed by 68_forward_record/AMENDMENT_shadow_CXL_D2.md, AMENDMENT_shadow_CXL_v1.1_reading.md (reading vs the median random book; no-screen
# twin) and AMENDMENT_v1.6_dup_returns.md (universe).  SHADOW = not adopted;
# tracked for information; not funded.  PAPER ONLY: no real money, no broker orders, the AI never places trades.
# Own state file (STATE_DIR/cxl_state.json), own clock (first decision 2026-11-30, fills at the next session's close), own A$0 comparators,
# 100 random-exclusion control books per size.  Universe and score = the SHADOW M3 table of the month-end (shadow/forward_M3_snapshot_<d>.csv);
# market caps = ASIC "total product in issue" from the archived daily short-position files (read only) x the decision-day close.
# Never reads or writes the H82 books beyond the month's A7 list in decisions/decision_<date>.json; never touches the other shadow states.
# Idempotent and resumable: a day is booked once (last_processed); a later run catches up from the stored bulk files.
import os, re, json, math, hashlib, traceback
import numpy as np, pandas as pd
import paper_lib as P, paper_score as PS

CX_START = '2026-11-30'
SIZES = (('25k', 25000.0, 8125000), ('100k', 100000.0, 8200000))      # (tag, capital, random seed base: seed = base + i, i = 1..NRAND)
NRAND = 100
ASIC_DIRS = ('asic_archive', 'asic_daily', 'asic_dl')                    # scratchpad folders filled by the weekday ASIC archive job (read only)
ASIC_RE = re.compile(r'^RR(\d{8})-(\d{3})-SSDailyAggShortPos\.csv$')
ASIC_MAXAGE = 45
KEEP_FRAC, BAND, WMAX, MINORD, POS, NMAX, NMIN = 0.7, 1.5, 0.15, 1000.0, 2500.0, 30, 4
TAG = 'SHADOW CXL (report 81 D2): not adopted; tracked for information'


def state_path(): return P.STATE_DIR + '/cxl_state.json'
def out_dir(): return P.REC + '/shadow'
def snap_path(d): return f'{out_dir()}/forward_M3_snapshot_{d}.csv'


# ---------------------------------------------------------------- state
def new_book(bid, kind, cap, seed=None):
    return dict(id=bid, kind=kind, capital=cap, contrib=0.0, start=CX_START, cash=cap, contributed=0.0, seed=seed, rng_state=None, n=None,
                holdings={}, orders=[], E=None, trades=[], divs=[], flows=[], nav={CX_START: cap}, units=cap / 100.0, events=[])

def init_state():
    fill = P.next_session(CX_START); books = []; cmps = []
    for tag, cap, s0 in SIZES:
        books.append(new_book(f'SHADOW_CXL_{tag}', 'SHADOW_CXL', cap))
        books.append(new_book(f'SHADOW_CXL_TWIN_{tag}', 'SHADOW_CXL_TWIN', cap))       # v1.1: no screen
        books += [new_book(f'SHADOW_CXL_RND_{tag}_s{i:03d}', 'SHADOW_CXL_RND', cap, seed=s0 + i) for i in range(1, NRAND + 1)]
        cmps.append(PS.new_cmp0(f'SHADOW_CXL_CMP_A200_{tag}', {'A200.AU': 1.0}, cap, 0.0, CX_START, fill))
    return dict(record='Big Wins forward paper record -- SHADOW CXL v1.0 cap-weighted, momentum losers excluded (report 81 D2; PAPER ONLY; not adopted; tracked for information)',
                amendment='AMENDMENT_shadow_CXL_D2.md', start_decision=CX_START, fill_day=fill, last_processed=P.prev_session(CX_START),
                decisions=[], data_blocks=[], last={}, books=books, cmps=cmps)

def load():
    p = state_path()
    return json.load(open(p)) if os.path.exists(p) else None

def save(s):
    p = state_path(); tmp = p + '.tmp'
    json.dump(s, open(tmp, 'w'), sort_keys=True, separators=(',', ':'), default=float); os.replace(tmp, p)
    return P.L.sha(p)


# ---------------------------------------------------------------- book arithmetic (as paper_shadow, M3 line)
def shares(h): return sum(l[1] for l in h['lots'])
def cost(h): return sum(l[2] for l in h['lots'])

def nav_of(b, last):
    return b['cash'] + sum(shares(h) * last[h['code']]['p'] for h in (b['holdings'][k] for k in sorted(b['holdings'])) if h['code'] in last)

def tax_owed(b, d):
    """rule 9 / v1.3 F as the SHADOW M3 line codes it: tax owed on the financial year's realised gains (50% discount >= 367 days) and dividends at 32%"""
    fy0 = f'{int(d[:4]) - (1 if d[5:7] < "07" else 0)}-07-01'
    st_, lt = 0.0, 0.0
    for t in b['trades']:
        if t['side'] not in ('sell', 'payout') or t['date'] < fy0: continue
        for (bd, q, c, pr) in t.get('lots', []):
            if (pd.Timestamp(t['date']) - pd.Timestamp(bd)).days >= 367: lt += pr - c
            else: st_ += pr - c
    dv = sum(x[4] for x in b['divs'] if x[0] >= fy0)
    loss = min(0.0, st_) + min(0.0, lt); s2, l2 = max(0.0, st_), max(0.0, lt)
    s2 += loss; l2 += min(0.0, s2); s2 = max(0.0, s2); l2 = max(0.0, l2)
    return max(0.0, 0.32 * (s2 + 0.5 * l2) + 0.32 * dv)

def free_cash(b, d): return b['cash'] - tax_owed(b, d)

def realise(h, q, proceeds):
    """full sale: oldest parcels first; returns [buy_date, q, cost, proceeds] parts"""
    out = []; rem = q
    for l in sorted(h['lots'], key=lambda l: l[0]):
        if rem <= 1e-9: break
        x = min(rem, l[1]); c = l[2] * x / l[1]
        out.append([l[0], x, c, proceeds * x / q]); l[1] -= x; l[2] -= c; rem -= x
    h['lots'] = [l for l in h['lots'] if l[1] > 1e-9]
    return out

def ev(b, d, s):
    if b['kind'] == 'SHADOW_CXL': b['events'].append([d, s])


# ---------------------------------------------------------------- ASIC shares on issue (rule 3)
def asic_file(d):
    """(path, position date, version) of the latest archived ASIC daily file dated on or before d (highest version of that date); None if none."""
    best = None
    for sub in ASIC_DIRS:
        root = P.S + '/' + sub
        if not os.path.isdir(root): continue
        for dp, dn, fn in os.walk(root):
            dn.sort()
            for f in sorted(fn):
                m = ASIC_RE.match(f)
                if not m: continue
                fd = f'{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}'
                if fd > d: continue
                k = (fd, m.group(2))
                if best is None or k > best[0]: best = (k, os.path.join(dp, f))
    return None if best is None else (best[1], best[0][0], best[0][1])

def asic_shares(d):
    f = asic_file(d)
    if f is None: return None, dict(file=None, reason='no ASIC file on or before the decision day')
    path, fd, ver = f; age = (pd.Timestamp(d) - pd.Timestamp(fd)).days
    meta = dict(file=os.path.basename(path), path=path[len(P.S) + 1:], position_date=fd, version=ver, age_days=age, sha256=P.L.sha(path))
    if age > ASIC_MAXAGE: meta['reason'] = f'newest ASIC file is {age} days old (> {ASIC_MAXAGE})'; return None, meta
    t = pd.read_csv(path, dtype=str)
    sh = {}
    for c, v in zip(t['Product Code'], t['Total Product in Issue']):
        try: x = float(str(v).replace(',', '').strip())
        except ValueError: continue
        c = str(c).strip()
        if c and x > 0 and c not in sh: sh[c] = x
    meta['n_codes'] = len(sh)
    return sh, meta


# ---------------------------------------------------------------- month-end table (rules 2-5)
def read_table(d):
    p = snap_path(d)
    if not os.path.exists(p): return None
    t = pd.read_csv(p)
    if not len(t): return []
    t = t.sort_values('rank', kind='stable')
    return [dict(cid=r.cid, code=r.code, rank=int(r.rank), vrank=int(r.vrank), med=float(r.median_traded_value), score=float(r.score),
                 close=(None if pd.isna(r.close) else float(r.close)), traded=bool(r.traded_on_day)) for r in t.itertuples()]

def caps_for(rows, sh):
    """cap of each scored company: ASIC shares x decision-day close; ignored when yearly traded value / cap is outside 0.02-20"""
    out = {}
    for r in rows:
        s = sh.get(r['code']) if '_old' not in r['code'] else None
        cap = s * r['close'] if (s and r['close'] and r['traded']) else None
        to = r['med'] * 252 / cap if cap else None
        r.update(asic_shares=s, cap=cap, turnover=to, cap_ok=bool(cap and 0.02 <= to <= 20))
        if r['cap_ok']: out[r['cid']] = cap
    return out

def make_list(rows, caps, keep):
    L_ = [r for r in rows if r['cid'] in keep and r['cid'] in caps]
    L_.sort(key=lambda r: (-caps[r['cid']], r['vrank']))
    return L_

def keep_momentum(rows):
    nr = len(rows); return {r['cid'] for r in rows if r['rank'] <= KEEP_FRAC * nr}

def keep_random(b, rows):
    rng = np.random.default_rng(b['seed'])
    if b.get('rng_state'): rng.bit_generator.state = b['rng_state']
    nr = len(rows); perm = rng.permutation(nr); rr = np.empty(nr, int); rr[perm] = np.arange(1, nr + 1)
    b['rng_state'] = rng.bit_generator.state
    return {rows[i]['cid'] for i in range(nr) if rr[i] <= KEEP_FRAC * nr}


# ---------------------------------------------------------------- decision (month-end, after the close)
def decide(b, rows, caps, sh, d, last, E, duplog):
    for o in b['orders']: ev(b, d, f"order not filled, dropped: {o['type']} {o['code']}")
    b['orders'] = []
    for x_, y_, _ in duplog:                                                          # rule 9: A7 code change carries the holding
        for cid, h in sorted(b['holdings'].items()):
            if h['code'] == x_ and y_ + '#E' not in b['holdings']:
                b['holdings'][y_ + '#E'] = dict(h, code=y_); del b['holdings'][cid]; ev(b, d, f'code change {x_}->{y_}')
    for cid, h in sorted(b['holdings'].items()):                                        # rule 9 / C1 payout: no close for 20 trading days
        lc = last.get(h['code'], {}).get('d')
        if lc is not None and len(P.sessions_between(lc, d)) >= 20:
            q = shares(h); p = last[h['code']]['p']; v = q * p
            parts = realise(h, q, v); b['cash'] += v; del b['holdings'][cid]
            b['trades'].append(dict(date=d, side='payout', code=h['code'], shares=q, price=p, half_spread=0.0, brokerage=0.0, cash=round(v, 2), reason='C1 payout', lots=parts))
            ev(b, d, f"payout {h['code']} at last close {p} ({lc})")
    keep = keep_random(b, rows) if b['kind'] == 'SHADOW_CXL_RND' else ({r['cid'] for r in rows} if b['kind'] == 'SHADOW_CXL_TWIN' else keep_momentum(rows))
    L_ = make_list(rows, caps, keep); lrank = {r['cid']: i for i, r in enumerate(L_, 1)}; tab = {r['cid']: r for r in rows}
    nav = nav_of(b, last); n = int(min(NMAX, max(NMIN, math.floor(nav / POS)))); b['n'] = n
    vr = lambda cid: (tab[cid]['vrank'] if cid in tab else b['holdings'].get(cid, {}).get('vrank'))
    hs = lambda cid, p: P.half_spread(vr(cid), p)
    new = []; proceeds = 0.0; kept = {}
    for cid, h in sorted(b['holdings'].items()):                                        # rule 8
        r = lrank.get(cid); p = last[h['code']]['p']; q = shares(h); val = q * p
        h['bad'] = h.get('bad', 0) + 1 if (r is None or r > BAND * n) else 0
        if h['bad'] >= 2:
            age = (pd.Timestamp(d) - pd.Timestamp(min(l[0] for l in h['lots']))).days
            if val > cost(h) and age < 365:
                ev(b, d, f"sale of {h['code']} waits (in profit, oldest parcel {age} days)"); kept[cid] = (h, val, p); continue
            new.append(dict(type='sell', cid=cid, code=h['code'], shares='all', vrank=vr(cid), reason='rule 8 sell'))
            proceeds += max(0.0, val * (1 - hs(cid, p)) - P.brokerage(val))
        else: kept[cid] = (h, val, p)
    free = free_cash(b, d) + proceeds
    bl = []
    if len(kept) < n:                                                                   # rule 6: largest listed names not held, down to list rank n
        for r in L_[:n]:
            if len(kept) + len(bl) >= n: break
            if r['cid'] in b['holdings'] or (r['close'] or 0) < 0.5: continue
            bl.append(r)
    if bl:
        names = list(kept) + [r['cid'] for r in bl]
        def capof(cid):
            if cid in caps: return caps[cid]
            h = b['holdings'].get(cid); s = sh.get(h['code']) if h and '_old' not in h['code'] else None
            p = last.get(h['code'], {}) if h else {}
            return s * p['p'] if (s and p.get('d') == d) else None
        c_ = np.array([capof(c) or np.nan for c in names], float)
        c_ = np.where(np.isfinite(c_), c_, np.nanmedian(c_) if np.isfinite(c_).any() else 1.0)
        w = c_ / c_.sum()
        for _ in range(50):
            ov = w > WMAX + 1e-12
            if not ov.any() or ov.all(): break
            ex = (w[ov] - WMAX).sum(); w[ov] = WMAX; w[~ov] += ex * w[~ov] / w[~ov].sum()
        tg = {c: float(w[i]) * nav * len(names) / n for i, c in enumerate(names)}
        nb = 0
        for r in bl:
            t = tg[r['cid']]; a = min(t, free); mn = max(MINORD, 0.5 * t)
            if a < mn: ev(b, d, f"buy {r['code']} skipped: {a:.2f} under the minimum {mn:.2f}"); continue
            if r['med'] < 100 * a: ev(b, d, f"buy {r['code']} skipped: median traded value under 100 x order"); continue
            new.append(dict(type='buy', cid=r['cid'], code=r['code'], amount=a, min_amount=mn, target=t, vrank=r['vrank'], rank=lrank[r['cid']], cap=caps[r['cid']], reason='rule 6 buy'))
            free -= a; nb += 1
        if nb and len(kept) + nb >= n:                                                  # rule 7 top-ups, smallest first
            for val, cid in sorted((v[1], c) for c, v in kept.items()):
                h, _, p = kept[cid]; t = tg[cid]
                if not (val < 0.75 * t and t - val >= MINORD): continue
                a = min(t - val, free); r = tab.get(cid)
                if a < MINORD or p < 0.5 or r is None or r['med'] < 100 * a: continue
                new.append(dict(type='topup', cid=cid, code=h['code'], amount=a, min_amount=MINORD, target=t, vrank=vr(cid), rank=lrank.get(cid), reason='rule 7 top-up'))
                free -= a
    b['orders'] = new; b['E'] = E
    ev(b, d, f"decision: NAV {nav:.2f} n {n} list {len(L_)} orders " + ', '.join(f"{o['type']} {o['code']}" for o in new))
    return new


# ---------------------------------------------------------------- one trading day
def run_day(b, d, mkt):
    cl = mkt['close']
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                       # Q7 splits
        s = mkt['split'].get(h['code'])
        if s and s > 0:
            for l in h['lots']: l[1] *= s
            ev(b, d, f"split {h['code']} x{s:g}")
    for h in (b['holdings'][k] for k in sorted(b['holdings'])):                       # I1 dividends, shares held before d
        v = mkt['div'].get(h['code'])
        if v and any(l[0] < d for l in h['lots']):
            q = sum(l[1] for l in h['lots'] if l[0] < d); c = q * v; b['cash'] += c; b['divs'].append([d, h['code'], q, v, round(c, 2)])
    if not b['orders'] or b['E'] is None or d < b['E']: return
    for o in [o for o in b['orders'] if o['type'] == 'sell']:
        h = b['holdings'].get(o['cid']); p = cl.get(o['code'])
        if h is None: continue
        if p is None: ev(b, d, f"sell {o['code']} not filled (no close); decided again next month-end"); continue
        q = shares(h); hh = P.half_spread(o.get('vrank'), p)
        pr = max(0.0, q * p * (1 - hh) - P.brokerage(q * p)); b['cash'] += pr
        parts = realise(h, q, pr); del b['holdings'][o['cid']]
        b['trades'].append(dict(date=d, side='sell', code=o['code'], shares=q, price=p, half_spread=hh, brokerage=P.brokerage(q * p), cash=round(pr, 2), reason=o['reason'], lots=parts))
    for o in [o for o in b['orders'] if o['type'] in ('buy', 'topup')]:
        a = min(o['amount'], free_cash(b, d)); p = cl.get(o['code'])
        if a < o['min_amount']: ev(b, d, f"{o['type']} {o['code']} dropped: free cash {a:.2f} below minimum {o['min_amount']:.2f}"); continue
        if p is None: ev(b, d, f"{o['type']} {o['code']} dropped: no close on the fill day"); continue
        if o['type'] == 'topup' and o['cid'] not in b['holdings']: continue
        hh = P.half_spread(o.get('vrank'), p); s = int(math.floor((a - P.brokerage(a)) / (p * (1 + hh))))
        if s <= 0: ev(b, d, f"{o['type']} {o['code']} dropped: 0 shares"); continue
        paid = s * p * (1 + hh) + P.brokerage(s * p); b['cash'] -= paid
        h = b['holdings'].setdefault(o['cid'], dict(code=o['code'], lots=[], bad=0, vrank=o.get('vrank'))); h['lots'].append([d, s, paid])
        if o.get('vrank') is not None: h['vrank'] = o['vrank']
        b['trades'].append(dict(date=d, side='buy', code=o['code'], shares=s, price=p, half_spread=hh, brokerage=P.brokerage(s * p), cash=round(-paid, 2), reason=o['reason']))
    b['orders'] = []


def duplog_for(d):
    try: return json.load(open(f'{P.DEC_DIR}/decision_{d}.json')).get('duplog', [])
    except Exception: return []


def step(s, d, mkt, log):
    last = s['last']
    watch = {'A200'} | {h['code'] for b in s['books'] for h in b['holdings'].values()} | {o['code'] for b in s['books'] for o in b['orders']}
    for c in watch:
        if c in mkt['close']: last[c] = dict(p=mkt['close'][c], d=d)
    for b in s['books']: run_day(b, d, mkt)
    for c in s['cmps']: PS.cmp_day0(c, d, mkt)
    info = None
    if d >= CX_START and P.is_month_end(d):
        rows = read_table(d); sh, meta = (None, None) if rows is None else asic_shares(d)
        if rows is None or sh is None:
            why = 'no SHADOW M3 table for this month-end' if rows is None else meta.get('reason')
            s['data_blocks'].append([d, f'CXL data block: {why}; no CXL decision']); log('SHADOW CXL', d, 'data block:', why)
            info = dict(asof=d, blocked=True, reason=why, asic=meta)
        else:
            for r in rows:
                if r['close'] is not None and r['traded']: last[r['code']] = dict(p=r['close'], d=d)
            for b in s['books']:
                for h in b['holdings'].values():
                    if h['code'] in mkt['close']: last[h['code']] = dict(p=mkt['close'][h['code']], d=d)
            caps = caps_for(rows, sh); E = P.next_session(d); dl = duplog_for(d); orows = []
            for b in s['books']:
                for o in decide(b, rows, caps, sh, d, last, E, dl):
                    if b['kind'] == 'SHADOW_CXL':
                        orows.append(dict(book=b['id'], type=o['type'], code=o['code'], amount_AUD=round(o['amount'], 2) if 'amount' in o else None, target_AUD=round(o['target'], 2) if 'target' in o else None,
                                          list_rank=o.get('rank'), tv_rank=o.get('vrank'), fill='close of ' + E, rule=o['reason']))
            keep = keep_momentum(rows); L_ = make_list(rows, caps, keep); lr = {r['cid']: i for i, r in enumerate(L_, 1)}
            lst = pd.DataFrame([dict(date=d, cid=r['cid'], code=r['code'], m3_rank=r['rank'], m3_score=r['score'], tv_rank=r['vrank'], median_traded_value=r['med'], close=r['close'],
                                     traded_on_day=r['traded'], asic_shares=r['asic_shares'], market_cap=r['cap'], yearly_tv_over_cap=r['turnover'], cap_ok=r['cap_ok'],
                                     loser_excluded=r['cid'] not in keep, list_rank=lr.get(r['cid']), asic_file=meta['file'], asic_position_date=meta['position_date']) for r in rows])
            os.makedirs(out_dir(), exist_ok=True)
            files = {f'shadow/cxl_list_{d}.csv': P.write_csv(f'{out_dir()}/cxl_list_{d}.csv', lst),
                     f'shadow/cxl_orders_{d}.csv': P.write_csv(f'{out_dir()}/cxl_orders_{d}.csv', pd.DataFrame(orows, columns=['book', 'type', 'code', 'amount_AUD', 'target_AUD', 'list_rank', 'tv_rank', 'fill', 'rule']))}
            s['decisions'].append(d)
            info = dict(asof=d, fill_day=E, asic=meta, files_sha256=files, list_top10=[r['code'] for r in L_[:10]],
                        orders={b['id']: [o['code'] for o in b['orders']] for b in s['books'] if b['kind'] == 'SHADOW_CXL'})
            log('SHADOW CXL', d, 'decision; ASIC', meta['file'], '; list top 5', info['list_top10'][:5], '; orders', {k: len(v) for k, v in info['orders'].items()})
    for b in s['books']: b['nav'][d] = round(nav_of(b, last), 2)
    for c in s['cmps']: c['nav'][d] = round(P.nav_of(c, last), 2)
    s['last_processed'] = d
    return info


def run(d, mkt, log):
    """Bring CXL up to trading day d (after the H82 day and the M3/E3 and ACC shadow steps). Returns a small dict for the ledger (None before the start)."""
    try:
        if d < CX_START: return None
        s = load()
        if s is None: s = init_state(); log('SHADOW CXL state created; first decision', CX_START)
        decs = []
        for x in P.sessions_between(s['last_processed'], d):
            m = mkt if (x == d and mkt is not None) else P.load_day(x)
            if m is None: log('SHADOW CXL', x, 'no bulk file; stops here and resumes on a later run'); break
            info = step(s, x, m, log); save(s)
            if info: decs.append(info)
        return dict(last_processed=s['last_processed'], state_sha256=P.L.sha(state_path()), decisions=decs or None)
    except Exception as e:
        log('SHADOW CXL ERROR (H82 books unaffected):', repr(e)); log(traceback.format_exc())
        return dict(error=repr(e)[:300])


# ---------------------------------------------------------------- scorecard rows
def twr(b, nav): return (nav / b['units']) / 100.0 - 1 if b['units'] > 0 else float('nan')

def tracking_error(b, c):
    me = [x for x in sorted(b['nav']) if x >= CX_START and P.is_month_end(x) and x in c['nav']]
    if len(me) < 13: return None
    rb = [PS.ret_at(b, x) for x in me]; rc = [PS.ret_at(c, x) for x in me]
    ex = [(1 + rb[i]) / (1 + rb[i - 1]) - (1 + rc[i]) / (1 + rc[i - 1]) for i in range(1, len(me))]
    return float(np.std(ex, ddof=1) * math.sqrt(12))

def scorecard_rows(d):
    s = load(); rows = []; md = []; hold = []
    if s is None:
        for tag, cap, _ in SIZES:
            rows.append(dict(asof=d, book=f'SHADOW_CXL_{tag}', kind='SHADOW_CXL', capital=cap, note=f'{TAG}; not started: first decision {CX_START}, fills at the close of {P.next_session(CX_START)}'))
        md.append(f'| SHADOW CXL (report 81 D2; AMENDMENT_shadow_CXL_D2.md) | — | — | {TAG}; first decision Mon 30 Nov 2026, fills at the close of Tue 1 Dec 2026; A$25k and A$100k, 100 random-exclusion books and a no-screen twin each; read as CXL minus the median random book |')
        return rows, md, hold
    last = s['last']; cm = {c['id']: c for c in s['cmps']}
    f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else (f'{x:+.2%}' if isinstance(x, float) else str(x))
    for tag, cap, _ in SIZES:
        b = next(x for x in s['books'] if x['id'] == f'SHADOW_CXL_{tag}'); a2 = cm[f'SHADOW_CXL_CMP_A200_{tag}']
        nav = nav_of(b, last); r = twr(b, nav); ra = twr(a2, P.nav_of(a2, last))
        rv = np.array([twr(x, nav_of(x, last)) for x in s['books'] if x['kind'] == 'SHADOW_CXL_RND' and x['capital'] == cap])
        sale = lambda cid, code, q, p, b=b: q * p * P.half_spread(b['holdings'][cid].get('vrank'), p) + P.brokerage(q * p)
        kept, sold = PS.after_tax_engine(b, last, s['last_processed'], sale); rk, rs = PS.at_return(kept, b['units']), PS.at_return(sold, b['units'])
        ak, as_ = PS.after_tax_cmp0(a2, last, s['last_processed']); rak, ras = PS.at_return(ak, a2['units']), PS.at_return(as_, a2['units'])
        te = tracking_error(b, a2); pr = float(np.mean(rv < r)) if len(rv) else None
        rmed = float(np.median(rv)) if len(rv) else None
        tw = next(x for x in s['books'] if x['id'] == f'SHADOW_CXL_TWIN_{tag}'); rt = twr(tw, nav_of(tw, last))
        rows.append(dict(asof=d, book=b['id'], kind='SHADOW_CXL', capital=cap, contributed=0.0, nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2), cash=round(b['cash'], 2),
                         vs_random_median=(None if rmed is None else round(r - rmed, 5)), random_median_return=(None if rmed is None else round(rmed, 5)),
                         twin_return=round(rt, 5), vs_twin=round(r - rt, 5),
                         n=b['n'], holdings=len(b['holdings']), open_orders=len(b['orders']), return_since_start=round(r, 5), a200_b0_return=round(ra, 5), vs_a200_b0=round(r - ra, 5),
                         after_tax_kept_AUD=round(kept, 2), after_tax_sold_AUD=round(sold, 2), ret_after_tax_kept=round(rk, 5), ret_after_tax_sold=round(rs, 5),
                         a200_b0_ret_after_tax_kept=round(rak, 5), a200_b0_ret_after_tax_sold=round(ras, 5), vs_a200_b0_after_tax_kept=round(rk - rak, 5),
                         vs_a200_b0_after_tax_sold=round(rs - ras, 5), vs_a200_b0_engine_sold_fund_kept=round(rs - rak, 5), dividends_fy=round(sum(x[4] for x in b['divs']), 2),
                         tracking_error=(None if te is None else round(te, 4)), pct_of_random=(None if pr is None else round(pr, 3)),
                         note=f"{TAG}; own clock from {s['start_decision']}; brokerage v1.3 E1; comparator A200 at A$0; % of random = share of {len(rv)} random-exclusion books below"))
        rows.append(dict(asof=d, book=tw['id'], kind='SHADOW CXL twin (no screen)', capital=cap, nav=round(nav_of(tw, last), 2), cash=round(tw['cash'], 2), holdings=len(tw['holdings']),
                         return_since_start=round(rt, 5), note='CXL rules with no loser screen (AMENDMENT_shadow_CXL_v1.1_reading.md)'))
        if len(rv):
            rows.append(dict(asof=d, book=f'SHADOW_CXL_RND_{tag} ({len(rv)} seeds)', kind='SHADOW CXL random control', capital=cap, return_since_start=round(float(np.median(rv)), 5),
                             note=f'median; 5th-95th pct {np.percentile(rv, 5):.4f} to {np.percentile(rv, 95):.4f}; random 30% excluded instead of momentum losers'))
        rows.append(dict(asof=d, book=a2['id'], kind='SHADOW comparator', capital=cap, contributed=0.0, nav=round(P.nav_of(a2, last), 2), nav_q6_at_70pct=round(P.nav_of(a2, last), 2),
                         cash=round(a2['cash'], 2), holdings=sum(1 for u in a2['fund_units'].values() if u > 0), open_orders=len(a2['pending']),
                         return_since_start=round(ra, 5), note=f"own clock from {s['start_decision']}; A$0 brokerage; EODHD proxy"))
        md.append(f"| {b['id']} (SHADOW CXL) | {nav:,.2f} | {f(r)} | **CXL minus median random-exclusion book {f(None if rmed is None else r - rmed)}** (screen's own contribution; expected about 0; "
                  f"% of random {'' if pr is None else round(pr, 3)}); minus no-screen twin {f(r - rt)}; secondary: A200 (A$0) {f(ra)} (vs {f(r - ra)}), after tax sold vs A200 kept {f(rs - rak)}; "
                  f"holdings {len(b['holdings'])} (n {b['n']}); cash {b['cash']:,.2f}; TE {'n/a (<12 months)' if te is None else f'{te:.1%}'} |")
        hs_ = ', '.join(f"{h['code']} {shares(h):,.0f}" for h in b['holdings'].values())
        if hs_ or b['orders']: hold.append(f"- {b['id']}: {hs_ or 'no shares'}" + (f"; {len(b['orders'])} paper orders for the close of {b['E']}" if b['orders'] else ''))
    return rows, md, hold
