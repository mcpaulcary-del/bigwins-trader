# Tests for the NEWS-C build (info_archive.py item 4, newsc_baselines/prepare/record/score). SCRATCH ONLY: every path is redirected
# into a fresh folder under scratchpad/newsc_test/run_<time>/; no network (every download function is replaced); the real ledger,
# archive, record and paper states are never written (their hashes are checked unchanged at the end).
#   python3 test_newsc.py
import csv, glob, hashlib, importlib, io, json, os, shutil, sys, time, traceback
from contextlib import redirect_stderr
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
SYD = ZoneInfo('Australia/Sydney')
RUN = f'{S}/newsc_test/run_{time.strftime("%Y%m%d_%H%M%S")}'
REAL_LEDGER = S + '/onedrive/research2/68_forward_record/LEDGER.jsonl'
REAL_RUBRIC = S + '/bigwins_forward/data/newsc/RUBRIC_v1.md'
GUARD = [REAL_LEDGER, S + '/bigwins_forward/out/paper_state/state.json', S + '/bigwins_forward/data/estimates_pit/bandC_universe.json',
         S + '/onedrive/research2/68_forward_record/paper/holdings_latest.csv', S + '/bigwins_forward/data/asx_notices/2026-11-23/list.csv']


def h(p):
    with open(p, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()


def tree_hash(d):
    x = hashlib.sha256()
    for p in sorted(glob.glob(d + '/**', recursive=True)):
        if os.path.isfile(p): x.update(p[len(d):].encode()); x.update(h(p).encode())
    return x.hexdigest()


def mkpdf(text):
    s = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(s) + s + b"\nendstream", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = b"%PDF-1.4\n"; offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)


def no_net(*a, **k): raise AssertionError('network access attempted in a test')


def fresh_archive(tag):
    """reload info_archive with every path inside RUN/<tag>"""
    import info_archive as A
    A = importlib.reload(A)
    root = f'{RUN}/{tag}'; os.makedirs(root + '/data/estimates_pit', exist_ok=True); os.makedirs(root + '/state', exist_ok=True)
    A.OUT = root + '/data'; A.BANDC = root + '/data/estimates_pit/bandC_universe.json'; A.STATE_DIR = root + '/state'
    A.HOLD_CSV = root + '/holdings_latest.csv'; A.GAP = 0.0; A.get = no_net
    return A, root


BANDC = [f'B{i:02d}' for i in range(1, 81)]
HOLD = ['HA1', 'HA2', 'B05']                        # HA1, HA2 outside band C; B05 in band C and held


def write_universe(root, A):
    json.dump(dict(asof='2026-11-16', codes=BANDC, n=len(BANDC)), open(A.BANDC, 'w'))
    with open(A.HOLD_CSV, 'w') as f:
        f.write('asof,book,code\n' + ''.join(f'2026-11-24,H82_25k,{c}\n' for c in HOLD))
    json.dump(dict(books=[dict(id='RND_25k_s001', kind='random', holdings={'ZZ1#E': dict(code='ZZ1')}),
                          dict(id='EMG2_18_SIM', kind='emg2', holdings={'HA2#E': dict(code='HA2')})]), open(A.STATE_DIR + '/sl_test_state.json', 'w'))


def tm(minutes):
    hh, mm = divmod(minutes, 60); ap = 'am' if hh < 12 else 'pm'
    return f'{(hh - 1) % 12 + 1}:{mm:02d} {ap}'


def sim_rows(day_ddmmyyyy):
    """newest first, like the ASX page: 75 price-sensitive band-C rows, 4 holdings rows, noise rows"""
    rows = []
    for i in range(75):
        rows.append(dict(code=BANDC[i], date=day_ddmmyyyy, time=tm(7 * 60 + 30 + i * 7), price_sensitive=1,
                         headline=f'Drilling update {i}', ids_id=f'0317{i:04d}', kept=0))
    rows += [dict(code='HA1', date=day_ddmmyyyy, time='4:15 pm', price_sensitive=1, headline='Quarterly report', ids_id='03179001', kept=0),
             dict(code='HA2', date=day_ddmmyyyy, time='8:05 am', price_sensitive=1, headline='Trading Halt', ids_id='03179002', kept=0),
             dict(code='B05', date=day_ddmmyyyy, time='9:00 am', price_sensitive=1, headline='Placement to raise $5m', ids_id='03179003', kept=1),
             dict(code='ZZ1', date=day_ddmmyyyy, time='9:10 am', price_sensitive=1, headline='Random-book code', ids_id='03179004', kept=0)]
    rows += [dict(code=BANDC[i], date=day_ddmmyyyy, time='11:00 am', price_sensitive=0, headline='Change of Director\'s Interest Notice',
                  ids_id=f'0318{i:04d}', kept=1) for i in range(10)]
    rows += [dict(code='NOT', date=day_ddmmyyyy, time='9:00 am', price_sensitive=1, headline='Not in universe', ids_id='03189999', kept=0)]
    rows.sort(key=lambda r: -__import__('info_archive').minutes(r['time']))
    return rows


def write_list(dirp, rows):
    os.makedirs(dirp + '/pdf', exist_ok=True)
    with open(dirp + '/list.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def page_html(day_words, rows):
    tr = ''.join(f'<tr><td>{r["code"]}</td><td>{r["date"]}<br><span class="dates-time">{r["time"]}</span></td><td>'
                 f'{"<img class=pricesens>" if r["price_sensitive"] else ""}</td><td><a href="/asx/v2/statistics/displayAnnouncement.do?'
                 f'display=pdf&amp;idsId={r["ids_id"]}">{r["headline"]}<br><span>1 page</span></a></td></tr>' for r in rows)
    return f'<html><h2>published on {day_words}</h2><table>{tr}</table></html>'


def fake_get_factory(page, calls):
    def g(url, binary=True):
        calls.append(url)
        if 'prevBusDayAnns' in url: return page
        if 'displayAnnouncement' in url:
            ids = url.split('idsId=')[1]; return f'<input name="pdfURL" value="https://example.invalid/{ids}.pdf">'
        if url.endswith('.pdf'): return mkpdf('Announcement ' + url.rsplit('/', 1)[1][:-4])
        raise AssertionError(url)
    return g


# ================================================================ tests
def t_archive_cap_priority():
    A, root = fresh_archive('cap'); write_universe(root, A)
    day = '2026-11-24'; d = f'{A.OUT}/asx_notices/{day}'; write_list(d, sim_rows('24/11/2026'))
    open(f'{d}/pdf/B05_03179003.pdf', 'wb').write(mkpdf('already held'))      # stored by item 2 earlier
    got = []
    def fetch(ids): got.append(ids); return mkpdf('ps ' + ids)
    at_0830 = datetime(2026, 11, 25, 8, 30, tzinfo=SYD)
    msg = A.price_sensitive(day, now=at_0830, fetch=fetch)
    st = json.load(open(d + '/ps_state.json'))
    assert len(got) == 60, len(got)
    # holdings first, by time: B05 drilling 07:58 (B05 is held and in band C), HA2 08:05, (B05 placement 09:00 already held -> 'had'),
    # HA1 16:15; then band C by time (B05's row already taken)
    assert got[:3] == ['03170004', '03179002', '03179001'], got[:3]
    assert got[3:] == [f'0317{i:04d}' for i in range(75) if i != 4][:57], 'band C must follow in time order'
    s = {k: sum(1 for x in st['items'] if x['status'] == k) for k in ('ok', 'had', 'over_cap', 'failed', 'pending')}
    assert s == dict(ok=60, had=1, over_cap=17, failed=0, pending=0), s       # 75 band C + 3 holdings - 1 had - 60
    assert 'ZZ1' not in st['holdings_codes'] and 'HA2' in st['holdings_codes'], 'twins/random books are not holdings'
    assert not any(x['code'] in ('NOT', 'ZZ1') for x in st['items'])
    assert not glob.glob(d + '/pdf/*.part'), 'part files left'
    assert os.path.exists(d + '/DONE_PS') and os.path.exists(f'{d}/pdf/HA2_03179002.txt')
    return msg


def t_archive_hours_pause_and_resume():
    A, root = fresh_archive('hours'); write_universe(root, A)
    day = '2026-11-24'; d = f'{A.OUT}/asx_notices/{day}'; write_list(d, sim_rows('24/11/2026'))
    got = []
    def fetch(ids): got.append(ids); return mkpdf('x')
    t = [datetime(2026, 11, 25, 9, 59, tzinfo=SYD)]
    def clock():
        if len(got) >= 10: return datetime(2026, 11, 25, 10, 0, tzinfo=SYD)
        return t[0]
    m1 = A.price_sensitive(day, now=clock, fetch=fetch)
    assert 'PAUSED' in m1 and len(got) == 10 and not os.path.exists(d + '/DONE_PS'), (m1, len(got))
    m2 = A.price_sensitive(day, now=datetime(2026, 11, 25, 13, 0, tzinfo=SYD), fetch=fetch)   # inside hours: nothing
    assert 'PAUSED' in m2 and len(got) == 10
    m3 = A.price_sensitive(day, now=datetime(2026, 11, 25, 16, 12, tzinfo=SYD), fetch=fetch)  # 16:12 = outside
    st = json.load(open(d + '/ps_state.json'))
    assert len(got) == 60 and st['attempts'] == 60 and os.path.exists(d + '/DONE_PS'), (len(got), st['attempts'])
    assert len(set(got)) == 60, 'nothing fetched twice across runs'
    # weekend daytime is outside ASX hours
    assert not A.inside_asx_hours(datetime(2026, 11, 28, 12, 0, tzinfo=SYD)) and A.inside_asx_hours(datetime(2026, 11, 27, 16, 11, tzinfo=SYD))
    return m3


def t_archive_failures_count_toward_cap():
    A, root = fresh_archive('fail'); write_universe(root, A)
    day = '2026-11-24'; d = f'{A.OUT}/asx_notices/{day}'; write_list(d, sim_rows('24/11/2026'))
    n = [0]
    def fetch(ids):
        n[0] += 1
        if n[0] % 2: raise IOError('simulated 503')
        return b'not a pdf' if n[0] % 4 == 0 else mkpdf('ok')
    with redirect_stderr(io.StringIO()): A.price_sensitive(day, now=datetime(2026, 11, 25, 20, 0, tzinfo=SYD), fetch=fetch)
    st = json.load(open(d + '/ps_state.json'))
    assert n[0] == 60 and st['attempts'] == 60
    with redirect_stderr(io.StringIO()): A.price_sensitive(day, now=datetime(2026, 11, 25, 21, 0, tzinfo=SYD), fetch=fetch)
    assert n[0] == 60, 'failed items are not retried beyond the cap'
    return f"failed {sum(x['status'] == 'failed' for x in st['items'])}, ok {sum(x['status'] == 'ok' for x in st['items'])}"


def t_archive_full_run_idempotent_and_old_parts_unchanged():
    """asx_notices() end to end on a simulated page: items 1-2 identical to the frozen old file; evening re-run writes nothing"""
    rows = sim_rows('24/11/2026') + [dict(code=f'X{i:02d}', date='24/11/2026', time='3:00 pm', price_sensitive=0, headline='Other',
                                          ids_id=f'0319{i:04d}', kept=0) for i in range(40)]
    page = page_html('24 November 2026', rows)
    # new code
    A, root = fresh_archive('full'); write_universe(root, A)
    calls = []; A.get = fake_get_factory(page, calls)
    A.inside_asx_hours = lambda now=None: False
    m1 = A.asx_notices()
    d = f'{A.OUT}/asx_notices/2026-11-24'
    n1 = len(calls); th = tree_hash(A.OUT)
    m2 = A.asx_notices()                                                   # the evening re-run
    assert len(calls) == n1 + 1 and 'prevBusDayAnns' in calls[-1], 'evening re-run: only the list page is read'
    assert tree_hash(A.OUT) == th, 'evening re-run must write nothing'
    assert 'already stored' in m2 and 'price-sensitive: already stored' in m2, m2
    # old code on the same page
    import info_archive_pre_newsc as O
    O = importlib.reload(O); O.OUT = f'{RUN}/full_old/data'; os.makedirs(O.OUT, exist_ok=True); O.GAP = 0.0
    oc = []; O.get = fake_get_factory(page, oc)
    O.asx_notices()
    od = f'{O.OUT}/asx_notices/2026-11-24'
    assert h(od + '/list.csv') == h(d + '/list.csv'), 'list.csv differs from the old code'
    old_pdfs = sorted(os.listdir(od + '/pdf'))
    assert all(os.path.exists(f'{d}/pdf/{x}') and h(f'{d}/pdf/{x}') == h(f'{od}/pdf/{x}') for x in old_pdfs), 'item-2 files differ'
    jo, jn = json.load(open(od + '/DONE')), json.load(open(d + '/DONE')); jo.pop('utc'); jn.pop('utc')
    assert jo == jn, (jo, jn)
    assert oc == calls[:len(oc)], 'items 1-2 must make the same requests in the same order as before'
    st = json.load(open(d + '/ps_state.json'))
    return f"{m1.splitlines()[0]} | {m1.splitlines()[1]} | ps attempts {st['attempts']}"


# ---------------------------------------------------------------- baselines fixture
def fixture_notices(root):
    """three list-days with known events; texts written as pdftotext output would be"""
    days = {'2026-11-25': [], '2026-11-26': [], '2026-11-27': []}
    def add(day, code, t, ps, head, ids, text=None):
        days[day].append(dict(code=code, date='', time=t, price_sensitive=ps, headline=head, ids_id=ids, kept=0, _text=text))
    add('2026-11-25', 'B01', '9:00 am', 1, 'Trading Halt', '1001')
    add('2026-11-25', 'B02', '9:05 am', 1, 'Suspension from Official Quotation', '1002')
    add('2026-11-25', 'B03', '9:10 am', 0, 'Proposed issue of securities - B03', '1003',
        '1.6 The Proposed issue is:\nA placement or other type of issue\n\nAre the +securities proposed to be issued being issued for a cash\n'
        'consideration?\nYes\n\nWhat is the issue price per +security?\nAUD 0.04000\n')
    add('2026-11-25', 'B04', '9:15 am', 0, 'Proposed issue of securities - B04', '1004',
        '1.6 The Proposed issue is:\nA placement or other type of issue\n\nAre the +securities proposed to be issued being issued for a cash\n'
        'consideration?\nNo\n')
    add('2026-11-25', 'B05', '6:00 pm', 0, "Change of Director's Interest Notice", '1005',
        'Nature of change                         On-market purchase of shares\nExample: on-market trade, off-market trade, exercise of options\n')
    add('2026-11-25', 'B06', '6:05 pm', 0, "Change of Director's Interest Notice", '1006',
        'Nature of change                         Issue of Performance Rights as approved\nExample: on-market trade, off-market trade, exercise of options\n')
    add('2026-11-26', 'B01', '10:30 am', 1, 'Completion of $20m Placement', '1007')
    add('2026-11-26', 'B07', '9:00 am', 1, 'Takeover offer from Bidder at $1.20 cash', '1008')
    add('2026-11-27', 'B02', '9:00 am', 1, 'Request for Extension of Voluntary Suspension', '1009')
    add('2026-11-27', 'B08', '9:00 am', 1, 'Trading Halt', '1010')
    for day, rows in days.items():
        d = f'{root}/{day}'; os.makedirs(d + '/pdf', exist_ok=True)
        for r in rows:
            r['date'] = day; t = r.pop('_text')
            if t: open(f"{d}/pdf/{r['code']}_{r['ids_id']}.txt", 'w').write(t)
        rows.sort(key=lambda r: -__import__('newsc_baselines')._minutes(r['time']))
        with open(d + '/list.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return list(days)


def t_baselines_fixture():
    import newsc_baselines as B
    root = f'{RUN}/baselines'; fixture_notices(root)
    U = {c: 'C' for c in BANDC}
    r25 = {r['code']: r for r in B.compute('2026-11-25', U, root)}
    assert r25['B01']['HALT'] == 1 and r25['B01']['halt_kind'] == 'halt' and r25['B01']['key_rating'] == -1
    assert r25['B02']['halt_kind'] == 'suspension' and r25['B02']['key_rating'] == -2 and r25['B02']['key_type'] == 'halt_suspension'
    assert r25['B03']['RAISE'] == 1 and r25['B03']['raise_last_issue_price'] == 0.04
    assert r25['B04']['RAISE'] == 0, 'non-cash 3B is not a raising'
    assert r25['B05']['DIR'] == 1 and r25['B06']['DIR'] == 0
    r26 = {r['code']: r for r in B.compute('2026-11-26', U, root)}
    assert r26['B01']['HALT'] == 0 and r26['B01']['RAISE'] == 1, 'halt ended by the next price-sensitive announcement; raising flagged'
    assert r26['B02']['halted_end_of_day'] == 1 and r26['B02']['n_announcements'] == 0, 'suspension carries over a day with no news'
    assert 'B03' not in r26, 'no row for a code without news or halt'
    assert r26['B07']['key_rating'] == 2 and r26['B07']['key_type'] == 'merger_acquisition'
    r27 = {r['code']: r for r in B.compute('2026-11-27', U, root)}
    assert r27['B02']['halt_list_days'] == 2 and r27['B02']['key_rating'] == -2
    assert r27['B08']['HALT'] == 1 and 'B01' not in r27
    # KEY spot checks and the code-day rule
    assert B.key('Results of Annual General Meeting') == ('governance_management', 0)
    assert B.key('Reinstatement to Official Quotation')[1] == 0
    assert B.key('Entitlement Offer Booklet')[0] == 'capital_raising' and B.key('Entitlement Offer Booklet')[1] == -1
    assert B.codeday_rating([2, -2]) == 0 and B.codeday_rating([1, -2, 0]) == -2 and B.codeday_rating([1, 1, -1]) == 0 \
        and B.codeday_rating([2, 1, -1]) == 2 and B.codeday_rating([]) is None
    return 'KEY, RAISE, HALT, DIR as expected on 3 fixture days'


# ---------------------------------------------------------------- prepare + record
def prep_fixture(tag, n_band=6):
    """an archived day as the archive leaves it (list.csv, ps_state.json, DONE_PS, texts)"""
    A, root = fresh_archive(tag); write_universe(root, A)
    day = '2026-11-30'; d = f'{A.OUT}/asx_notices/{day}'
    rows = sim_rows('30/11/2026')
    write_list(d, rows)
    long = 'Assay results ' + 'x' * 40_000
    def fetch(ids): return mkpdf('Announcement ' + ids)
    A.price_sensitive(day, now=datetime(2026, 12, 1, 8, 30, tzinfo=SYD), fetch=fetch)
    open(f'{d}/pdf/{BANDC[0]}_03170000.txt', 'w').write(long)                # one long text, to test the 30,000 cut
    return A, root, day


def t_prepare_blinding():
    import newsc_prepare as NP
    A, root, day = prep_fixture('prep')
    newsc = root + '/newsc'; os.makedirs(newsc, exist_ok=True)
    msg, rc = NP.prepare(day, A.OUT + '/asx_notices', newsc)
    assert rc == 0, msg
    lines = [json.loads(l) for l in open(f'{newsc}/{day}/input.jsonl')]
    assert lines and all(set(x) == NP.ITEM_KEYS for x in lines)
    allowed = {'H': NP.ANN_KEYS_H, 'F': NP.ANN_KEYS_F}
    for x in lines:
        for a in x['announcements']: assert set(a) == allowed[x['arm']], set(a)
    raw = open(f'{newsc}/{day}/input.jsonl').read().lower()
    for bad in ('holding', 'bandc', 'band_c', '"group"', 'close', 'price"', 'return', 'volume', 'rank', 'key_type', '"raise', '"halt"',
                'h82', 'emg2', 'shares', 'nav'):
        assert bad not in raw, f'blinding: {bad!r} found in the rater input'
    dates = {x['announcement_day'] for x in lines}; assert dates == {day}
    codes = {x['code'] for x in lines}
    assert {'HA1', 'HA2', 'B05'} <= codes and 'ZZ1' not in codes and 'NOT' not in codes
    f0 = next(x for x in lines if x['arm'] == 'F' and x['code'] == BANDC[0])['announcements'][0]
    assert len(f0['text']) == NP.MAX_TEXT and f0['text_truncated'] is True
    assert all('text' not in a for x in lines if x['arm'] == 'H' for a in x['announcements'])
    man = json.load(open(f'{newsc}/{day}/manifest.json'))
    grp = {x['code']: x['group'] for x in man['items']}
    assert grp['HA1'] == 'H' and grp['B05'] == 'C', 'groups live only in the manifest'
    # every batch line is a line of input.jsonl; H and F never share a batch
    inp = set(open(f'{newsc}/{day}/input.jsonl').read().splitlines())
    for b in man['batches']:
        bl = open(f"{newsc}/{day}/batches/{b['batch']}.jsonl").read().splitlines()
        assert set(bl) <= inp and {json.loads(l)['arm'] for l in bl} == {b['batch'][0]}
        txt = open(f"{newsc}/{day}/batches/{b['batch']}.txt").read()
        assert max(len(l) for l in txt.split('\n')) <= NP.WRAP and txt.rstrip().endswith('=== END BATCH ===')
        assert txt.count('[ANNOUNCEMENT ') == sum(len(json.loads(l)['announcements']) for l in bl)
        for bad in ('holding', 'bandc', 'group', 'h82', 'emg2'): assert bad not in txt.lower(), bad
        if b['arm'] == 'H': assert 'TEXT (' not in txt
    # idempotent; and a changed source is refused, not overwritten
    th = tree_hash(f'{newsc}/{day}')
    m2, rc2 = NP.prepare(day, A.OUT + '/asx_notices', newsc); assert rc2 == 0 and 'already prepared' in m2 and tree_hash(f'{newsc}/{day}') == th
    open(f'{A.OUT}/asx_notices/{day}/pdf/{BANDC[1]}_03170001.txt', 'w').write('changed text')
    m3, rc3 = NP.prepare(day, A.OUT + '/asx_notices', newsc); assert rc3 == 2 and 'REFUSED' in m3 and tree_hash(f'{newsc}/{day}') == th
    return f"{man['n_items']} code-days, {man['n_announcements']} announcements, batches {[b['batch'] for b in man['batches']]}"


def fake_replies(newsc, day, outdir, tamper=None):
    """what a rater would return: deterministic ratings from the headline index"""
    man = json.load(open(f'{newsc}/{day}/manifest.json')); os.makedirs(outdir, exist_ok=True)
    import newsc_baselines as B
    for b in man['batches']:
        items = [json.loads(l) for l in open(f"{newsc}/{day}/batches/{b['batch']}.jsonl")]
        for p in (1, 2):
            rs = []
            for it in items:
                for a in it['announcements']:
                    k = int(a['ann_id']) % 5 - 2
                    if p == 2 and int(a['ann_id']) % 7 == 0: k = -k              # some disagreements
                    rs.append(dict(item_id=it['item_id'], ann_id=a['ann_id'], type=B.TYPES[int(a['ann_id']) % 14], rating=k,
                                   reason='Fixture reason with a few words.'))
            rep = dict(rubric='NEWSC_RUBRIC_v1', batch=b['batch'], batch_sha256=b['sha256'], pass_=p, model_self_report='test-model', ratings=rs)
            rep['pass'] = rep.pop('pass_')
            if tamper: tamper(rep, b['batch'], p)
            txt = json.dumps(rep)
            if p == 2: txt = '```json\n' + txt + '\n```'                        # a fenced reply is tolerated
            open(f"{outdir}/{b['batch']}_p{p}.json", 'w').write(txt)


def t_record():
    import newsc_prepare as NP, newsc_record as NR, fwd_ledger as L
    A, root, day = prep_fixture('rec')
    newsc = root + '/newsc'; os.makedirs(newsc, exist_ok=True); shutil.copy(REAL_RUBRIC, newsc + '/RUBRIC_v1.md')
    msg, rc = NP.prepare(day, A.OUT + '/asx_notices', newsc); assert rc == 0, msg
    led = root + '/LEDGER.jsonl'
    L.LED = led; L.append(kind='trials', asof='2026-11-25', event='scratch ledger head')
    rd = root + '/replies'; fake_replies(newsc, day, rd)
    now_ok = datetime(2026, 12, 1, 9, 20, tzinfo=SYD)
    def refused(fn, want):
        try: fn()
        except NR.Refuse as e:
            assert want in str(e), (want, str(e)); return str(e)
        raise AssertionError(f'not refused: {want}')
    rec = lambda **k: NR.record(day, k.pop('rd', rd), 'claude-test-1', 'test', newsc=newsc, ledger=led, now=now_ok, **k)
    out = []
    out.append(refused(lambda: rec(), 'not registered'))
    L.LED = led; L.append(kind='amendment', amendment='AMENDMENT_info_NEWSC_v1.md', asof='2026-11-30', event='scratch registration')
    # schema refusals
    for tag, fn, want in [('rating3', lambda r, b, p: r['ratings'][0].update(rating=3), 'not an integer'),
                          ('bool', lambda r, b, p: r['ratings'][0].update(rating=True), 'not an integer'),
                          ('float', lambda r, b, p: r['ratings'][0].update(rating=1.0), 'not an integer'),
                          ('type', lambda r, b, p: r['ratings'][0].update(type='mining'), 'not one of the 14'),
                          ('reason', lambda r, b, p: r['ratings'][0].update(reason=' '.join(['w'] * 21)), 'reason'),
                          ('missing', lambda r, b, p: r['ratings'].pop(), 'not rated'),
                          ('dup', lambda r, b, p: r['ratings'].append(dict(r['ratings'][0])), 'twice'),
                          ('extra', lambda r, b, p: r.update(note='x'), 'keys'),
                          ('hash', lambda r, b, p: r.update(batch_sha256='0' * 64), 'input hash mismatch'),
                          ('pass', lambda r, b, p: r.update(**{'pass': 3}), 'pass')]:
        d2 = f'{root}/bad_{tag}'; fake_replies(newsc, day, d2, tamper=lambda r, b, p, fn=fn: fn(r, b, p) if (b, p) == ('F_01', 2) else None)
        out.append(refused(lambda d2=d2: rec(rd=d2), want))
    os.remove(f'{root}/bad_missing/H_01_p1.json'); out.append(refused(lambda: rec(rd=f'{root}/bad_missing'), 'missing rater reply'))
    # input hash refusal: input.jsonl altered after prepare
    ip = f'{newsc}/{day}/input.jsonl'; keepb = open(ip, 'rb').read()
    open(ip, 'ab').write(b' '); out.append(refused(lambda: rec(), 'does not match input.sha256'))
    open(ip, 'wb').write(keepb)
    bp = f'{newsc}/{day}/batches/F_01.jsonl'; kb = open(bp, 'rb').read(); open(bp, 'ab').write(b'\n')
    out.append(refused(lambda: rec(), 'hash does not match the manifest')); open(bp, 'wb').write(kb)
    tp = f'{newsc}/{day}/batches/F_01.txt'; kt = open(tp, 'rb').read(); open(tp, 'ab').write(b'extra line\n')
    out.append(refused(lambda: rec(), 'is not the rendering')); open(tp, 'wb').write(kt)
    # rubric hash refusal
    open(newsc + '/RUBRIC_v1.md', 'a').write(' '); out.append(refused(lambda: rec(), 'not the registered'))
    shutil.copy(REAL_RUBRIC, newsc + '/RUBRIC_v1.md')
    n0 = len(L.entries())
    assert not os.path.exists(f'{newsc}/{day}/ratings.jsonl') and n0 == 2, 'refusals wrote nothing'
    e = rec()
    L.LED = led; L.verify()
    assert len(L.entries()) == 3 and e['kind'] == 'info_news' and e['asof'] == day and e['on_time_provisional'] is True
    assert e['rubric_sha256'] == h(REAL_RUBRIC) and e['input_sha256'] == h(ip) and e['ratings_sha256'] == h(f'{newsc}/{day}/ratings.jsonl')
    assert e['model']['reported_id'] == 'claude-test-1' and e['model']['self_reports'] == ['test-model']
    cd = [json.loads(l) for l in open(f'{newsc}/{day}/codeday.jsonl')]
    rr = [json.loads(l) for l in open(f'{newsc}/{day}/ratings.jsonl')]
    assert all(r['rating'] == NR.keep(r['rating_p1'], r['rating_p2']) for r in rr)
    assert NR.keep(2, -2) == 0 and NR.keep(2, 1) == 1 and NR.keep(-1, 1) == 0 and NR.keep(-2, 0) == 0 and NR.keep(-2, -1) == -1
    assert {x['group'] for x in cd} == {'C', 'H'} and all('RAISE' in x for x in cd)
    assert not glob.glob(f'{newsc}/{day}/**/*.part', recursive=True)
    out.append(refused(lambda: rec(), 'already recorded'))
    os.rename(f'{newsc}/{day}/ratings.jsonl', f'{newsc}/{day}/ratings.moved')     # still refused: the ledger has the day
    out.append(refused(lambda: rec(), 'already recorded')); os.rename(f'{newsc}/{day}/ratings.moved', f'{newsc}/{day}/ratings.jsonl')
    assert len(L.entries()) == 3
    # the score loader reads the recorded day back, hash-checked
    import newsc_score as SC
    rows, base, recu, bandc, bad = SC.load(newsc, led)
    assert len(rows) == len(cd) and not bad and recu[day] == e['recorded_utc'] and len(bandc[day]) == len(BANDC)
    return f"recorded seq {e['seq']} with {e['counts']['code_days']} code-days; {len(out)} refusals checked"


def t_record_late_and_model_change():
    import newsc_prepare as NP, newsc_record as NR, fwd_ledger as L
    A, root, day = prep_fixture('late')
    newsc = root + '/newsc'; os.makedirs(newsc, exist_ok=True); shutil.copy(REAL_RUBRIC, newsc + '/RUBRIC_v1.md')
    NP.prepare(day, A.OUT + '/asx_notices', newsc)
    led = root + '/LEDGER.jsonl'; L.LED = led
    L.append(kind='amendment', amendment='AMENDMENT_info_NEWSC_v1.md', asof='2026-11-30', event='scratch registration')
    L.append(kind='info_news', asof='2026-11-27', model=dict(reported_id='claude-old'), event='scratch earlier day')
    rd = root + '/replies'; fake_replies(newsc, day, rd)
    e = NR.record(day, rd, 'claude-new', 'test', newsc=newsc, ledger=led, now=datetime(2026, 12, 1, 10, 5, tzinfo=SYD))
    assert e['on_time_provisional'] is False and any('LATE' in f for f in e['failures']) and any('MODEL CHANGE' in f for f in e['failures'])
    return 'late flagged; model change flagged'


# ---------------------------------------------------------------- score on synthetic data
def t_score_synthetic():
    import numpy as np, newsc_score as SC, exchange_calendars as xc
    ss = [str(x.date()) for x in xc.get_calendar('XASX', start='2026-11-01', end='2029-12-31').sessions]
    rng = np.random.default_rng(7)
    codes = [f'C{i:03d}' for i in range(80)]
    def build(effect):
        rets = {c: rng.normal(0.0, 0.02, len(ss)) for c in codes}
        rows, base, rec = [], [], {}
        i0 = ss.index('2026-11-30')
        for i in range(i0, ss.index('2028-11-30') + 1):
            d = ss[i]; rec[d] = datetime.fromisoformat(ss[i + 1] + 'T09:05:00').replace(tzinfo=SYD).astimezone(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%SZ')
            for c in rng.choice(codes, 4, replace=False):
                rt = int(rng.choice([-2, -1, 0, 0, 0, 1, 2]))
                key_t = 'capital_raising' if rt < 0 and rng.random() < 0.5 else 'other'
                rows.append(dict(day=d, code=c, group='C' if rng.random() < 0.9 else 'H', rating_F=rt, rating_H=rt, key_type=key_t,
                                 key_rating=(-1 if key_t == 'capital_raising' else 0), model='synthetic'))
                base.append(dict(day=d, code=c, group='C', key_type=key_t, key_rating=rows[-1]['key_rating'], RAISE=int(key_t == 'capital_raising'),
                                 HALT=0, DIR=int(rng.random() < 0.05), model='synthetic'))
                if effect:
                    e = i + 1                                                    # entry session
                    if rt == 2: rets[c][e + 1:e + 21] += 0.004                  # +8% drift over 20 sessions
                    if rt == -2: rets[c][e + 1:e + 21] -= 0.004
                    if rt == -2 and rng.random() < 0.5: rets[c][e + 1:e + 253] -= 0.004   # wreck path
        px = {c: 1.0 * np.exp(np.cumsum(rets[c])) for c in codes}
        days = {d: dict(close={c: float(px[c][k]) for c in codes}, vol={c: 1000.0 for c in codes}, div={}, split={}) for k, d in enumerate(ss)}
        return rows, base, rec, days
    out = []
    for effect in (True, False):
        rows, base, rec, days = build(effect)
        mk = SC.Market(ss, lambda d: days.get(d)); mk.asof = '2030-01-01'
        bandc = {d: codes for d in rec}
        SC.outcomes(rows, mk, rec, bandc); SC.outcomes(base, mk, rec, bandc)
        R = SC.readings(rows, 'F', '2030-01-01', external={'EST-C': 0.2, 'DIL-C': 0.5}, base_rows=base)
        out.append((effect, R['primary']['result'], round(R['primary']['t'] or 0, 2), R['secondary_A_wrecks']['result'],
                    round(R['secondary_A_wrecks']['t'] or 0, 2), R['secondary_B_winners']['result']))
        if effect:
            assert R['primary']['result'] == 'present' and R['secondary_A_wrecks']['result'] == 'present', R['primary']
            assert R['primary']['added_value']['adds'] is True
            assert R['bh_10pct']['NEWS-C AI drift'] is True and R['bh_10pct']['DIL-C'] is False
            assert R['descriptive']['holdings_outside_bandC']['n'] > 0
            assert all(r['late'] == 0 for r in rows)
        else:
            assert R['primary']['result'] == 'not detected' and R['secondary_A_wrecks']['result'] == 'not detected', out[-1]
    # before the reading dates nothing is read
    R0 = SC.readings(rows, 'F', '2027-06-01', base_rows=base)
    assert R0['primary']['result'].startswith('no reading') and R0['secondary_A_wrecks']['result'].startswith('no reading')
    # entry timing: ledger before 10:00 -> that session's close; after 10:00 -> late; halted share enters at its first trade
    days2 = {d: dict(close={'A': 1.0, 'B': 1.0}, vol={'A': 1.0, 'B': (0.0 if d in ('2027-03-02', '2027-03-03') else 1.0)}, div={}, split={}) for d in ss}
    mk2 = SC.Market(ss, lambda d: days2[d]); mk2.asof = '2030-01-01'
    r = [dict(day='2027-03-01', code='A'), dict(day='2027-03-01', code='B')]
    SC.outcomes(r, mk2, {'2027-03-01': '2027-03-01T22:59:00Z'}, {'2027-03-01': ['A', 'B']})     # 09:59 Sydney on 2 Mar
    assert ss[r[0]['entry']] == '2027-03-02' and r[0]['late'] == 0 and ss[r[1]['entry']] == '2027-03-04' and r[1]['late'] == 0
    r = [dict(day='2027-03-01', code='A')]
    SC.outcomes(r, mk2, {'2027-03-01': '2027-03-01T23:01:00Z'}, {'2027-03-01': ['A']})           # 10:01 Sydney: after the open
    assert ss[r[0]['entry']] == '2027-03-03' and r[0]['late'] == 1
    # dividends as cash, splits on the share count
    days3 = {d: dict(close={'A': 1.0}, vol={'A': 1.0}, div={}, split={}) for d in ss}
    k = ss.index('2027-03-02'); days3[ss[k + 3]]['div'] = {'A': 0.1}; days3[ss[k + 5]]['split'] = {'A': 2.0}
    for j in range(k + 5, len(ss)): days3[ss[j]]['close'] = {'A': 0.5}
    mk3 = SC.Market(ss, lambda d: days3[d]); mk3.asof = '2030-01-01'
    assert abs(SC.track(mk3, k, 'A', (20,))[20] - 0.1) < 1e-12
    return '; '.join(str(x) for x in out)


def main():
    before = {p: h(p) for p in GUARD if os.path.exists(p)}
    real_newsc = tree_hash(S + '/bigwins_forward/data/newsc'); real_notices = tree_hash(S + '/bigwins_forward/data/asx_notices')
    os.makedirs(RUN, exist_ok=True)
    tests = [t_archive_cap_priority, t_archive_hours_pause_and_resume, t_archive_failures_count_toward_cap,
             t_archive_full_run_idempotent_and_old_parts_unchanged, t_baselines_fixture, t_prepare_blinding, t_record,
             t_record_late_and_model_change, t_score_synthetic]
    ok = 0
    for t in tests:
        try:
            r = t(); ok += 1; print(f'PASS {t.__name__}: {r}')
        except Exception:
            print(f'FAIL {t.__name__}'); traceback.print_exc()
    after = {p: h(p) for p in GUARD if os.path.exists(p)}
    assert before == after, 'a real file changed'
    assert tree_hash(S + '/bigwins_forward/data/newsc') == real_newsc and tree_hash(S + '/bigwins_forward/data/asx_notices') == real_notices
    print(f'{ok}/{len(tests)} passed; real ledger, states, archive and newsc folder unchanged; scratch: {RUN}')
    shutil.rmtree(RUN, ignore_errors=True)
    sys.exit(0 if ok == len(tests) else 1)


if __name__ == '__main__':
    main()
