# Tests for the NEWS-C big-drop log (newsc_drops.py, newsc_drops_record.py, newsc_score.py --drops). SCRATCH ONLY: every path is
# redirected into scratchpad/newsc_drops_test/run_<time>/; no network; the real ledger, archive, bulk files, decisions and newsc
# folder are never written (their hashes are checked unchanged at the end).
#   python3 test_newsc_drops.py
import csv, glob, gzip, hashlib, importlib, importlib.util, io, json, os, re, shutil, sys, tarfile, time, traceback
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
SYD = ZoneInfo('Australia/Sydney')
RUN = f'{S}/newsc_drops_test/run_{time.strftime("%Y%m%d_%H%M%S")}'
REAL_LEDGER = S + '/onedrive/research2/68_forward_record/LEDGER.jsonl'
REAL_NEWSC = S + '/bigwins_forward/data/newsc'
RD = S + '/research_dip'
GUARD_TREES = [REAL_NEWSC, S + '/bigwins_forward/data/asx_notices', S + '/bigwins_forward/data/bulk',
               S + '/bigwins_forward/out/paper_state', RD + '/data', RD + '/code']

import paper_lib as P
import newsc_drops as ND
import newsc_drops_record as NR
import newsc_score as SC
import fwd_ledger as L

REAL_BULK, REAL_LED = P.BULK, L.LED


def h(p):
    with open(p, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()


def tree_hash(d):
    x = hashlib.sha256()
    for p in sorted(glob.glob(d + '/**', recursive=True)):
        if os.path.isfile(p) and '__pycache__' not in p: x.update(p[len(d):].encode()); x.update(h(p).encode())
    return x.hexdigest()


def gz(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with gzip.open(p, 'wt') as f: json.dump(obj, f)


# ---------------------------------------------------------------- synthetic fixture
SS = [x for x in P.sessions() if '2027-02-01' <= x <= '2027-04-30']
START = SS[1]
FILL = [f'F{i:03d}' for i in range(1, 101)]


def fixture(tag):
    """bulk files, one decision file and archive lists in RUN/<tag>; returns (root, scenario dict)"""
    root = f'{RUN}/{tag}'; bulk = root + '/bulk'; dec = root + '/decisions'; os.makedirs(dec, exist_ok=True)
    # pool: 10 special codes ranks 1-10, fillers 11-100 (F011..F100); OUT1 rank 101; CHEAP rank 12 but table close 0.90
    rows = []
    special = ['DRP', 'EDG', 'NOT', 'MKT', 'MKX', 'SPL', 'CAP', 'PEN', 'RF1', 'RF2']
    names = {'DRP': 'Zebra Minerals Limited', 'EDG': 'Edge Holdings Ltd', 'NOT': 'Notch Group Ltd', 'MKT': 'Market Corp Ltd',
             'MKX': 'Marmot Industries Ltd', 'SPL': 'Splitco Ltd', 'CAP': 'Capret Ltd', 'PEN': 'Penny Ltd',
             'RF1': 'Refire One Ltd', 'RF2': 'Refire Two Ltd'}
    for k, c in enumerate(special):
        rows.append(dict(cid=c + '#E', code=c, name=names[c], vrank=k + 1, rawclose=10.0, close10=10.0))
    for k, c in enumerate(FILL[10:]):
        rows.append(dict(cid=c + '#E', code=c, name=f'Filler {c} Ltd', vrank=k + 11, rawclose=5.0, close10=5.0))
    rows = [r for r in rows if r['vrank'] != 12] + [dict(cid='CHEAP#E', code='CHEAP', name='Cheap Ltd', vrank=12, rawclose=0.9, close10=0.9)]
    rows.append(dict(cid='OUT1#E', code='OUT1', name='Outside Ltd', vrank=101, rawclose=10.0, close10=10.0))
    with open(f'{dec}/decision_{SS[0]}.json', 'w') as f:
        json.dump(dict(asof=SS[0], rows=rows, ranks={r['cid']: r['vrank'] for r in rows}), f)
    codes = [r['code'] for r in rows] + ['A200']
    px = {c: [10.0] * len(SS) for c in codes}; px['PEN'] = [0.95] * len(SS); px['A200'] = [100.0] * len(SS)
    for c in FILL: px[c] = [5.0] * len(SS)
    div, spl, nodata = {}, {}, set()
    k0 = 5                                              # first scenario session index

    def drop(c, i, r):
        for j in range(i, len(SS)): px[c][j] = px[c][i - 1] * (1 + r) if j == i else px[c][j - 1]
    drop('DRP', k0, -0.15)                                                     # event
    drop('EDG', k0, -0.1001); drop('NOT', k0 + 1, -0.0999)                     # edge: event / no event
    for j in range(k0 + 2, len(SS)): px['A200'][j] = 95.0                       # index -5% on k0+2
    drop('MKT', k0 + 2, -0.13); drop('MKX', k0 + 2, -0.16)                     # xr -8% (no) / -11% (event)
    i = k0 + 3; px['SPL'][i:] = [4.0] * (len(SS) - i); spl[(SS[i], 'SPL')] = '2/1'    # 2:1 split + TR -20%: excluded
    i = k0 + 3; px['CAP'][i:] = [6.5] * (len(SS) - i); div[(SS[i], 'CAP')] = 2.0      # capital return 2.0, TR -15%: excluded
    drop('PEN', k0 + 3, -0.20)                                                 # raw close 0.95 on D-1: excluded
    drop('OUT1', k0, -0.30); drop('CHEAP', k0, -0.30)                          # outside the pool
    for t in (k0, k0 + 15, k0 + 21): drop('RF1', t, -0.12)                     # event, blocked, event (21 > 20; blocked day no reset)
    for t in (k0, k0 + 20): drop('RF2', t, -0.12)                              # event, blocked (exactly 20)
    nodata.add((SS[k0 + 4], 'F050')); drop('F050', k0 + 5, -0.2)               # no close on D-1: no event on k0+5
    for j, d in enumerate(SS):
        gz(f'{bulk}/{d}/eod.json.gz', [dict(code=c, date=d, close=round(px[c][j], 6), volume=1000) for c in codes if (d, c) not in nodata])
        gz(f'{bulk}/{d}/div.json.gz', [dict(code=c, date=d, unadjustedValue=str(v), currency='AUD') for (dd, c), v in div.items() if dd == d])
        gz(f'{bulk}/{d}/splits.json.gz', [dict(code=c, date=d, split=v) for (dd, c), v in spl.items() if dd == d])
    want = {SS[k0]: {'DRP', 'EDG', 'RF1', 'RF2'}, SS[k0 + 2]: {'MKX'}, SS[k0 + 21]: {'RF1'}}
    return root, dict(bulk=bulk, dec=dec, k0=k0, want=want, names=names, px=px)


def use_fixture(fx):
    P.BULK = fx['bulk']; ND._DAY.clear(); ND._POOL.clear(); ND.CHAIN_START = START; ND.MIN_POOL_CLOSES = 90


def restore():
    P.BULK = REAL_BULK; ND._DAY.clear(); ND._POOL.clear(); ND.CHAIN_START = '2026-11-18'; L.LED = REAL_LED


def t_detect_fixture():
    root, fx = fixture('detect'); use_fixture(fx)
    R, gaps = ND.detect_only(SS[1], SS[-1], fx['dec'], START)
    got = {d: {e['code'] for e in x['events']} for d, x in R.items() if x['events']}
    assert got == fx['want'], (got, fx['want'])
    k0 = fx['k0']
    exc = {(d, e['code']): e['excluded'] for d, x in R.items() for e in x['excluded']}
    assert exc.get((SS[k0 + 3], 'SPL')) == 'split or capital return on the day', exc
    assert exc.get((SS[k0 + 3], 'CAP')) == 'split or capital return on the day', exc
    assert exc.get((SS[k0 + 3], 'PEN')).startswith('raw close'), exc
    blk = {(d, e['code']) for d, x in R.items() for e in x['blocked']}
    assert blk == {(SS[k0 + 15], 'RF1'), (SS[k0 + 20], 'RF2')}, blk
    e = next(x for x in R[SS[k0 + 2]]['events'] if x['code'] == 'MKX')
    assert abs(e['index_ret'] + 0.05) < 1e-9 and abs(e['xr'] + 0.11) < 1e-9, e
    assert not gaps, gaps
    # no decision before the day -> refused
    try:
        ND.candidates(SS[0], P.prev_session(SS[0]), ND.decisions(fx['dec'])); raise AssertionError('should refuse')
    except ND.Refuse as ex: assert 'no paper decision' in str(ex) or 'no bulk' in str(ex), ex
    return f"{sum(len(v) for v in got.values())} events on {len(got)} days; split, capital return, A$1, pool, index, re-fire and missing-close cases as designed"


# ---------------------------------------------------------------- notices for the fixture day
def notices_fixture(root, fx):
    nt = root + '/notices'; k0 = fx['k0']; D, Dm1 = SS[k0], SS[k0 - 1]
    def write(day, rows):
        os.makedirs(f'{nt}/{day}/pdf', exist_ok=True)
        with open(f'{nt}/{day}/list.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['code', 'date', 'time', 'price_sensitive', 'headline', 'ids_id', 'kept']); w.writeheader(); w.writerows(rows)
        open(f'{nt}/{day}/DONE', 'w').write('{}')
    dd = lambda d: f'{d[8:]}/{d[5:7]}/{d[:4]}'
    write(Dm1, [dict(code='DRP', date=dd(Dm1), time='5:12 pm', price_sensitive=1, ids_id='900001', kept=0,
                     headline='Zebra Minerals FY27 guidance downgrade - issue price $1.25 on 25 November 2026'),
                dict(code='DRP', date=dd(Dm1), time='11:00 am', price_sensitive=1, ids_id='900000', kept=0, headline='Early-day item not late-filed'),
                dict(code='EDG', date=dd(Dm1), time='6:00 pm', price_sensitive=0, ids_id='900002', kept=0, headline='Change of Director\'s Interest Notice')])
    write(D, [dict(code='DRP', date=dd(D), time='8:01 am', price_sensitive=1, ids_id='900003', kept=1, headline='Zebra Minerals Placement to raise $300m at $8.50 per share'),
              dict(code='DRP', date=dd(D), time='8:00 am', price_sensitive=0, ids_id='900004', kept=0, headline='Response to ASX Price Query'),
              dict(code='RF1', date=dd(D), time='9:30 am', price_sensitive=1, ids_id='900005', kept=0, headline='Quarterly Activities Report'),
              dict(code='RF2', date=dd(D), time='9:45 am', price_sensitive=1, ids_id='900006', kept=0, headline='Trading Halt')])
    with open(f'{nt}/{D}/pdf/DRP_900003.txt', 'w') as f:
        f.write('Zebra Minerals Limited (ASX: DRP) ABN 12 345\nZEBRA MINERALS announces a placement at A$8.50 per share, a 15% discount to the last close '
                'of $10.00, raising A$300 million. Settlement on 2 December 2026 (FY27). Price 10.00 and 8.50 cents ' + 'x' * 3000)
    return nt


def t_run_and_masking():
    root, fx = fixture('mask'); use_fixture(fx); nt = notices_fixture(root, fx)
    newsc = root + '/newsc'; os.makedirs(newsc); shutil.copy(REAL_NEWSC + '/DROPS_RUBRIC_v1.md', newsc + '/')
    D = SS[fx['k0']]
    msg, rc, man = ND.run(D, newsc, nt, fx['dec'])
    assert rc == 0 and '4 events' in msg, msg
    ev = [json.loads(l) for l in open(f'{newsc}/{D}/drops.jsonl')]
    by = {e['code']: e for e in ev}
    assert set(by) == {'DRP', 'EDG', 'RF1', 'RF2'}
    assert by['DRP']['kw']['cls'] == 'FUND' and by['DRP']['cause_kw_sub'] == 'F_DILUTE', by['DRP']['kw']      # placement + downgrade
    assert [x['headline'][:5] for x in by['DRP']['headlines']] == ['Zebra', 'Zebra', 'Respo'], by['DRP']['headlines']   # 11:00 am D-1 not used
    assert by['DRP']['headlines'][1]['text_origin'] == 'item2'
    assert by['RF1']['cause_kw'] == 'temporary' and by['EDG']['cause_kw'] == 'no-news' and by['RF2']['cause_kw'] == 'other-news', \
        {c: e['cause_kw'] for c, e in by.items()}
    assert by['EDG']['in_dossier'] == 1 and by['EDG']['n_focused'] == 0                                     # only a non-PS headline
    txt = open(f"{newsc}/{man['dossier_path']}").read()
    assert D not in man['dossier_path'] and re.fullmatch(r'drops_blind/[0-9a-f]{16}\.txt', man['dossier_path'])
    for bad in ['DRP', 'Zebra', 'ZEBRA', 'ZBM', 'EDG', 'Edge', 'Refire', 'RF1', '2026', '2027', 'November', 'December', '$1.25', '$8.50',
                '8.50', '10.00', 'FY27']:
        assert bad not in txt, (bad, txt[:2000])
    assert 'Company A' in txt and '$[amount]' in txt and '$300m' in txt and 'D-1 5:12 pm [price-sensitive]' in txt
    items = [json.loads(l) for l in open(f'{newsc}/{D}/drops_dossier.jsonl')]
    assert all(set(it) == {'id', 'announcements', 'texts'} for it in items)
    for it in items:
        for a in it['announcements']: assert set(a) == {'off', 'time', 'ps', 'headline'}
    assert sorted(it['id'] for it in items) == sorted(e['id'] for e in ev if e['in_dossier'])
    assert h(f'{newsc}/{D}/drops.jsonl') == open(f'{newsc}/{D}/drops.sha256').read().split()[0] == man['drops_sha256']
    msg2, rc2, _ = ND.run(D, newsc, nt, fx['dec']); assert rc2 == 0 and 'already prepared' in msg2, msg2
    with open(f'{nt}/{D}/list.csv', 'a') as f: f.write(f'DRP,x,9:00 am,1,Extra headline,900099,0\n')
    msg3, rc3, _ = ND.run(D, newsc, nt, fx['dec']); assert rc3 == 2 and 'REFUSED' in msg3, msg3
    # a day without the archive is refused; a changed rubric or classifier is refused
    try: ND.build(SS[fx['k0'] + 2], newsc, nt, fx['dec']); raise AssertionError('should refuse')
    except ND.Refuse as e: assert 'not archived' in str(e)
    open(newsc + '/DROPS_RUBRIC_v1.md', 'a').write(' ')
    try: ND.build(D, newsc, nt, fx['dec']); raise AssertionError('should refuse')
    except ND.Refuse as e: assert 'hashes to' in str(e)
    return f"4 events written, dossier {len(txt)} chars masked (no name, code, date, year or price); re-run no-op, changed input / rubric refused"


# ---------------------------------------------------------------- classifier parity with research_dip
def t_classifier_parity():
    assert h(HERE + '/newsc_drops_classify.py') == h(RD + '/code/classify.py') == ND.CLASSIFY_SHA256
    spec = importlib.util.spec_from_file_location('rd_classify', RD + '/code/classify.py'); RC = importlib.util.module_from_spec(spec); spec.loader.exec_module(RC)
    import newsc_drops_classify as KC
    d = f'{RUN}/parity'; os.makedirs(d)
    with tarfile.open(RD + '/data/news_732events.tar.gz') as t: t.extractall(d, filter='data')
    names = {}
    for mk in ('US', 'ASX'):
        with open(f'{RD}/out/events_{mk}_D1.csv') as f:
            for r in csv.DictReader(f): names[(mk, r['date'][:10], r['code'].split('#')[0].split('@')[0])] = r['name']
    lab = {}
    with open(RD + '/data/keyword_labels.csv') as f:
        for r in csv.DictReader(f): lab[(r['mk'], r['date'][:10], r['code'])] = r
    n = same = titles = 0
    for p in sorted(glob.glob(d + '/news/*.json')):
        rec = json.load(open(p)); mk, code, day = os.path.basename(p)[:-5].split('_', 2)
        nm = names.get((mk, day, code), '')
        F1 = RC.focused(rec, nm, None); F2 = KC.focused(rec, nm, None)
        assert [x[1] for x in F1] == [x[1] for x in F2]
        a, b = RC.keyword([x[1] for x in F1]), KC.keyword([x[1] for x in F2]); assert a == b
        titles += len(F1); n += 1
        L_ = lab.get((mk, day, code))
        if L_ and int(L_['narts']) >= 0 and (L_['kw'], L_['sub'], int(L_['n']), int(L_['nT']), int(L_['nF'])) == (a[0], a[1], a[2], a[3], a[4]): same += 1
    assert n >= 700 and same == n, (n, same)
    # every raw title of the archive, one at a time (both copies)
    for p in sorted(glob.glob(d + '/news/*.json'))[:400]:
        for art in json.load(open(p))['arts']:
            if art.get('t'): assert RC.keyword([art['t']]) == KC.keyword([art['t']])
    return f'byte-identical copy (sha256 {ND.CLASSIFY_SHA256[:12]}); {n} saved events, {titles} focused titles: labels identical to research_dip keyword_labels.csv ({same}/{n})'


# ---------------------------------------------------------------- record
def reply(newsc, D, pas, labels=None, **over):
    man = json.load(open(f'{newsc}/{D}/drops_manifest.json'))
    items = [json.loads(l) for l in open(f'{newsc}/{D}/drops_dossier.jsonl')]
    r = dict(rubric='NEWSC_DROPS_RUBRIC_v1', dossier_sha256=man['dossier_txt_sha256'], pass_=pas, model_self_report='test-model',
             labels=labels if labels is not None else [dict(id=it['id'], cause='T', sub='T_EARN', reason='results miss') for it in items])
    r['pass'] = r.pop('pass_'); r.update(over)
    return r


def t_record():
    root, fx = fixture('record'); use_fixture(fx); nt = notices_fixture(root, fx)
    newsc = root + '/newsc'; os.makedirs(newsc); shutil.copy(REAL_NEWSC + '/DROPS_RUBRIC_v1.md', newsc + '/')
    D = SS[fx['k0']]; ND.run(D, newsc, nt, fx['dec'])
    led = root + '/LEDGER.jsonl'; L.LED = led
    L.append(kind='amendment', asof='2027-01-01', amendment='AMENDMENT_other.md', event='x')
    rd = root + '/incoming'; os.makedirs(rd)
    def put(pas, obj, raw=None):
        with open(f'{rd}/drops_p{pas}.json', 'w') as f: f.write(raw if raw is not None else json.dumps(obj))
    on_time = datetime.fromisoformat(f'{P.next_session(D)}T09:00:00').replace(tzinfo=SYD)
    def refused(want):
        try: NR.record(D, rd, 'm1', 'test', newsc=newsc, ledger=led, now=on_time)
        except NR.Refuse as e:
            assert want in str(e), (want, str(e)); return
        raise AssertionError('not refused: ' + want)
    put(1, reply(newsc, D, 1)); put(2, reply(newsc, D, 2))
    refused('not registered')
    L.append(kind='amendment', asof='2027-01-01', amendment='AMENDMENT_info_NEWSC_drops_v1.md', event='test registration')
    n0 = len(L.entries())
    ids = [json.loads(l)['id'] for l in open(f'{newsc}/{D}/drops_dossier.jsonl')]
    cases = [
        (lambda: put(2, reply(newsc, D, 2, dossier_sha256='0' * 64)), 'dossier_sha256 does not match'),
        (lambda: put(2, reply(newsc, D, 2, rubric='NEWSC_RUBRIC_v1')), 'rubric'),
        (lambda: put(2, reply(newsc, D, 1)), 'pass'),
        (lambda: put(2, reply(newsc, D, 2, labels=[dict(id=i, cause='T', sub='T_EARN', reason='x') for i in ids[1:]])), 'not labelled'),
        (lambda: put(2, reply(newsc, D, 2, labels=[dict(id=i, cause='Q', sub='T_EARN', reason='x') for i in ids])), 'not T/F/U'),
        (lambda: put(2, reply(newsc, D, 2, labels=[dict(id=i, cause='F', sub='T_EARN', reason='x') for i in ids])), 'sub-cause'),
        (lambda: put(2, reply(newsc, D, 2, labels=[dict(id=i, cause='T', sub='T_EARN', reason='w ' * 21) for i in ids])), 'reason'),
        (lambda: put(2, reply(newsc, D, 2, labels=[dict(id=i, cause='T', sub='T_EARN', reason='x') for i in ids + ['X9']])), 'not in the dossier'),
        (lambda: put(2, None, raw='not json'), 'not valid JSON'),
        (lambda: os.remove(f'{rd}/drops_p2.json'), 'missing rater reply'),
    ]
    for act, want in cases:
        act(); refused(want); put(2, reply(newsc, D, 2))
    # tampered inputs
    p = f'{newsc}/{D}/drops.jsonl'; keep = open(p, 'rb').read(); open(p, 'ab').write(b'\n'); refused('drops.jsonl hash'); open(p, 'wb').write(keep)
    man = json.load(open(f'{newsc}/{D}/drops_manifest.json')); bp = f"{newsc}/{man['dossier_path']}"
    keep = open(bp, 'rb').read(); open(bp, 'ab').write(b'extra'); refused('is not the rendering'); open(bp, 'wb').write(keep)
    rb = newsc + '/DROPS_RUBRIC_v1.md'; keep = open(rb, 'rb').read(); open(rb, 'ab').write(b' '); refused('hashes to'); open(rb, 'wb').write(keep)
    assert len(L.entries()) == n0, 'a refusal wrote the ledger'
    # disagreement on one item -> U
    lab2 = [dict(id=i, cause=('F' if k == 0 else 'T'), sub=('F_DILUTE' if k == 0 else 'T_EARN'), reason='because') for k, i in enumerate(sorted(ids))]
    put(2, reply(newsc, D, 2, labels=lab2))
    e = NR.record(D, rd, 'm1', 'test', newsc=newsc, ledger=led, now=on_time)
    assert e['kind'] == 'info_drops' and e['on_time'] and e['failures'] == [], e['failures']
    rows = [json.loads(l) for l in open(f'{newsc}/{D}/drops_labels.jsonl')]
    assert {r['id']: r['rater'] for r in rows if r['in_dossier']}[sorted(ids)[0]] == 'U'
    assert e['counts']['rater_disagreements'] == 1 and e['labels_sha256'] == h(f'{newsc}/{D}/drops_labels.jsonl')
    refused('already recorded')
    # a later day: zero events, no replies needed, recorded LATE after the close of D+1, model not compared
    D2 = SS[fx['k0'] + 1]; ND.run(D2, newsc, nt_day(nt, D2), fx['dec'])
    late = datetime.fromisoformat(f'{P.next_session(D2)}T16:05:00').replace(tzinfo=SYD)
    e2 = NR.record(D2, root + '/none', 'm2', 'test', newsc=newsc, ledger=led, now=late)
    assert e2['counts']['events'] == 0 and not e2['on_time'] and any('LATE' in f for f in e2['failures']) and not e2['model']['model_change']
    return 'refusals: not registered, dossier hash, rubric id, pass, missing item, bad cause, wrong sub-cause, long reason, extra item, bad JSON, missing reply, tampered drops/dossier/rubric, already recorded; ledger untouched by refusals; disagreement -> U; zero-event day; LATE flag'


def nt_day(nt, d):
    os.makedirs(f'{nt}/{d}', exist_ok=True)
    if not os.path.exists(f'{nt}/{d}/list.csv'):
        with open(f'{nt}/{d}/list.csv', 'w') as f: f.write('code,date,time,price_sensitive,headline,ids_id,kept\n')
        open(f'{nt}/{d}/DONE', 'w').write('{}')
    return nt


# ---------------------------------------------------------------- score
class NoMarket:
    ss = P.sessions(); asof = None
    def day(self, d): raise AssertionError('a return was read before the reading date')


def t_score_no_reading():
    rows = [dict(day='2027-02-05', code=f'C{i}', cause_kw='temporary', cause_rater='temporary', late=0, month='2027-02', close_prev=10.0)
            for i in range(150)]
    R = SC.drops_reading(rows, NoMarket(), '2029-11-30'); assert R['result'].startswith('no reading'), R
    R = SC.drops_reading(rows[:99], NoMarket(), '2031-01-01'); assert R['result'].startswith('no reading'), R
    late = [dict(r, late=1) for r in rows]
    R = SC.drops_reading(late, NoMarket(), '2031-01-01'); assert R['result'].startswith('no reading') and R['late_events'] == 150
    # the command line on an empty scratch ledger prints "no reading" and writes nothing
    d = f'{RUN}/score'; os.makedirs(d + '/newsc'); led = d + '/LEDGER.jsonl'; L.LED = led
    L.append(kind='amendment', asof='2027-01-01', amendment='AMENDMENT_info_NEWSC_drops_v1.md', event='test')
    out = io.StringIO(); import contextlib
    class A: newsc = d + '/newsc'; ledger = led; asof = '2027-06-01'; out = None
    with contextlib.redirect_stdout(out): SC.drops_main(A)
    assert 'drops: no reading' in out.getvalue() and not os.path.exists(d + '/newsc/readings'), out.getvalue()
    # after the threshold the reading runs (synthetic market): temporary +, fundamental -, month-clustered t
    ss = [x for x in SC.drops_sessions() if '2027-01-01' <= x <= '2029-12-31']
    rows = []
    for k in range(120):
        D = ss[k * 5]; cls = 'temporary' if k % 3 else 'fundamental'
        rows.append(dict(day=D, code=f'Z{k}', cause_kw=cls, cause_rater=cls, late=0, month=D[:7], close_prev=10.0, _eff=(0.3 if cls == 'temporary' else -0.3) + 0.05 * ((k * 7) % 5 - 2), _i=k))
    def loader(d):
        j = ss.index(d) if d in ss else None
        if j is None: return None
        close = {'A200': 100.0}
        for r in rows:
            i0 = ss.index(r['day'])
            g = 0 if j <= i0 else (1 + r['_eff'] * min(1, (j - i0) / 252) + (0.01 if (j + r['_i']) % 2 else -0.01))
            close[r['code']] = 8.5 if j <= i0 else 8.5 * g
        return dict(close=close, vol={c: 1 for c in close}, div={}, split={})
    mk = SC.Market(ss, loader)
    R = SC.drops_reading(rows, mk, '2029-12-31')
    k = R['tables']['keyword (primary)']
    assert k['temporary']['252s_excess']['mean'] > 0.25 and k['temporary']['252s_excess']['t'] > 2, k['temporary']
    assert k['temporary_minus_fundamental_252s']['b'] > 0.5 and R['bar']['result'].startswith('present'), R['bar']
    assert k['fundamental']['fell20_252'] == 1.0 and k['temporary']['recovered_252'] == 1.0, k
    return 'no reading before Dec 2029, below 100 events, or with late events only (no price read); CLI writes nothing; synthetic reading computes the bar'


def main():
    before = {d: tree_hash(d) for d in GUARD_TREES}; led0 = h(REAL_LEDGER)
    os.makedirs(RUN, exist_ok=True)
    tests = [t_detect_fixture, t_run_and_masking, t_classifier_parity, t_record, t_score_no_reading]
    ok = 0
    for t in tests:
        try:
            r = t(); ok += 1; print(f'PASS {t.__name__}: {r}')
        except Exception:
            print(f'FAIL {t.__name__}'); traceback.print_exc()
        finally: restore()
    assert h(REAL_LEDGER) == led0, 'the real ledger changed'
    for d in GUARD_TREES: assert tree_hash(d) == before[d], f'a real file changed under {d}'
    print(f'{ok}/{len(tests)} passed; real ledger, bulk, decisions, archive, newsc folder and research_dip unchanged; scratch: {RUN}')
    shutil.rmtree(RUN, ignore_errors=True)
    sys.exit(0 if ok == len(tests) else 1)


if __name__ == '__main__':
    main()
