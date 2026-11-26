# Forward archive of free public information for research (owner decision 24 Nov 2026). INFORMATION ONLY:
# nothing here feeds any paper line or the live trader. Private, personal, non-commercial use only.
#   1. ASX announcements list (previous trading day, 1 request) -> list CSV of every headline.
#   2. PDFs of director-interest notices (Appendix 3Y/3X/3Z) and capital-raising notices (proposed issue,
#      quotation, placement, entitlement, SPP, cleansing) -> PDF + extracted text. Polite: one request every 2 s.
#   3. ASIC daily aggregated short positions (published with a ~4 trading-day lag) -> every listed date not yet
#      stored (first run backfills the history to 2010), gzipped.
# The owner's exception to "no automated access to asx.com.au" covers ONLY items 1-2 (ledger/HANDOVER).
# Idempotent: a day's folder or a short file already stored is skipped.
# NEWS-C extension (owner decision, ledger seq 103, 25 Nov 2026; old file kept as info_archive_pre_newsc.py, items 1-3 unchanged):
#   4. PDFs of PRICE-SENSITIVE announcements, from the previous-day list only, for band-C companies (estimates_pit/bandC_universe.json)
#      and paper-line holdings: at most 60 a list-day (attempts, counted across re-runs), holdings first, then band C, each by
#      announcement time; one request every 2 s; never inside ASX hours (10:00-16:12 Sydney, Mon-Fri: the step pauses and a later
#      run resumes); written as .part then renamed; text by pdftotext. A PDF already stored by item 2 is reused (no request).
#      State asx_notices/<day>/ps_state.json, marker DONE_PS. Run at about 08:30 Sydney on trading days: prevBusDayAnns.do then
#      shows the previous trading day; an evening re-run of the same list-day finds DONE and DONE_PS and writes nothing.
import csv, gzip, html, json, os, re, shutil, subprocess, sys, time, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
OUT = S + '/bigwins_forward/data'
UA = {'User-Agent': 'Mozilla/5.0 (private personal research; low rate)'}
GAP = 2.0
LIST_URL = 'https://www.asx.com.au/asx/v2/statistics/prevBusDayAnns.do'
BASE = 'https://www.asx.com.au'
KEEP = re.compile(r"director'?s?.? interest|appendix 3[xyz]|proposed issue|application for quotation|placement|"
                  r"entitlement|capital raising|share purchase plan|cleansing|appendix 2a|appendix 3b", re.I)
_last = [0.0]
# NEWS-C (item 4)
BANDC = OUT + '/estimates_pit/bandC_universe.json'
STATE_DIR = S + '/bigwins_forward/out/paper_state'                    # paper-line engine states (read only)
HOLD_CSV = S + '/onedrive/research2/68_forward_record/paper/holdings_latest.csv'
PS_CAP = 60                                                          # owner decision seq 103: at most 60 a day
SYD = ZoneInfo('Australia/Sydney')
ASX_HOURS = ((10, 0), (16, 12))                                      # no price-sensitive download inside this window, Mon-Fri
MIN_FREE = 1_000_000_000                                             # bytes of free disk below which item 4 stops


def get(url, binary=True):
    wait = GAP - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                _last[0] = time.time(); b = r.read()
                return b if binary else b.decode('utf-8', 'replace')
        except Exception as e:
            _last[0] = time.time(); err = e; time.sleep(5 * (attempt + 1))
    raise err


def asx_notices():
    page = get(LIST_URL, binary=False)
    m = re.search(r'published on\s+(\d{1,2}) (\w+) (\d{4})', page)
    day = time.strftime('%Y-%m-%d', time.strptime(' '.join(m.groups()), '%d %B %Y'))
    d = f'{OUT}/asx_notices/{day}'
    if os.path.exists(d + '/DONE'): msg = f'asx {day}: already stored'
    else: msg = _store_list_and_notices(page, day, d)
    return msg + '\n' + price_sensitive(day)


def _store_list_and_notices(page, day, d):
    """items 1-2, unchanged from info_archive_pre_newsc.py"""
    os.makedirs(d + '/pdf', exist_ok=True)
    rows = []
    for code, date, tm, rest in re.findall(r'<tr[^>]*>\s*<td>(\w+)</td>\s*<td>\s*(\d\d/\d\d/\d{4})<br>\s*'
                                           r'<span class="dates-time">([^<]+)</span>\s*</td>(.*?)</tr>', page, re.S):
        a = re.search(r'href="([^"]+)">\s*([^<]+?)\s*<br>', rest, re.S)
        if not a: continue
        url = html.unescape(a.group(1)); ids = re.search(r'idsId=(\d+)', url)
        rows.append({'code': code, 'date': date, 'time': tm.strip(), 'price_sensitive': int('pricesens' in rest),
                     'headline': html.unescape(a.group(2)).strip(), 'ids_id': ids.group(1) if ids else '',
                     'kept': int(bool(KEEP.search(a.group(2))))})
    if len(rows) < 50: raise SystemExit(f'asx {day}: only {len(rows)} rows parsed - page format changed?')
    with open(d + '/list.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    got = fail = 0
    for r in rows:
        if not r['kept'] or not r['ids_id']: continue
        p = f"{d}/pdf/{r['code']}_{r['ids_id']}.pdf"
        if os.path.exists(p): continue
        try:
            terms = get(f"{BASE}/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId={r['ids_id']}", binary=False)
            pdf_url = re.search(r'name="pdfURL" value="([^"]+)"', terms).group(1)
            b = get(pdf_url)
            if not b.startswith(b'%PDF'): raise ValueError('not a PDF')
            open(p, 'wb').write(b)
            subprocess.run(['pdftotext', '-layout', p, p[:-4] + '.txt'], timeout=60, check=False)
            got += 1
        except Exception as e:
            fail += 1; print('pdf fail', r['code'], r['ids_id'], e, file=sys.stderr)
    open(d + '/DONE', 'w').write(json.dumps({'rows': len(rows), 'kept': sum(r['kept'] for r in rows),
                                             'pdfs': got, 'failed': fail, 'utc': time.strftime('%FT%TZ', time.gmtime())}))
    return f'asx {day}: {len(rows)} announcements, {got} notices stored, {fail} failed'


# ---------------------------------------------------------------- item 4: price-sensitive PDFs for NEWS-C (seq 103)
def inside_asx_hours(now=None):
    t = (now or datetime.now(SYD)).astimezone(SYD)
    return t.weekday() < 5 and ASX_HOURS[0] <= (t.hour, t.minute) < ASX_HOURS[1]


def holdings_codes():
    """codes held by any paper line: paper/holdings_latest.csv plus every 'holdings' block of a paper book in STATE_DIR/*state.json
    (read only). Random portfolios and twins (kind 'random', ids with RND, keys named like twins/rnd/random) are not paper-line
    holdings and are skipped. Missing or unreadable files add nothing."""
    out = set()
    twin = re.compile(r'twin|(^|_)rnd(_|$)|random', re.I)
    try:
        with open(HOLD_CSV) as f: out |= {r['code'].strip() for r in csv.DictReader(f) if r.get('code', '').strip()}
    except Exception as e: print('holdings csv not read:', e, file=sys.stderr)

    def walk(x, depth=0):
        if depth > 8: return
        if isinstance(x, dict):
            if x.get('kind') == 'random' or twin.search(str(x.get('id', ''))): return
            for k, v in x.items():
                if twin.search(str(k)): continue
                if k == 'holdings':
                    if isinstance(v, dict):
                        for hk, hv in v.items():
                            c = hv.get('code') if isinstance(hv, dict) else None
                            out.add(str(c or hk.split('#')[0]).strip())
                    elif isinstance(v, list):
                        for hv in v:
                            if isinstance(hv, dict) and hv.get('code'): out.add(str(hv['code']).strip())
                else: walk(v, depth + 1)
        elif isinstance(x, list):
            for v in x: walk(v, depth + 1)
    if os.path.isdir(STATE_DIR):
        for fn in sorted(os.listdir(STATE_DIR)):
            if fn.endswith('state.json'):
                try:
                    with open(os.path.join(STATE_DIR, fn)) as f: walk(json.load(f))
                except Exception as e: print('state not read:', fn, e, file=sys.stderr)
    out.discard('')
    return out


def bandc_codes():
    with open(BANDC, 'rb') as f: raw = f.read()
    j = json.loads(raw)
    import hashlib
    return set(j['codes']), dict(asof=j.get('asof'), sha256=hashlib.sha256(raw).hexdigest(), n=len(j['codes']))


def minutes(tm):
    """'8:27 pm' -> minutes after midnight (unparseable -> 9999, i.e. last)"""
    m = re.match(r'\s*(\d{1,2}):(\d\d)\s*([ap])m', tm or '', re.I)
    if not m: return 9999
    h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == 'p' else 0)
    return h * 60 + int(m.group(2))


def select_ps(rows, hold, bandc):
    """price-sensitive rows of the list for holdings or band C, in download priority: holdings first, then band C; within each,
    by announcement time (earliest first), then list order"""
    sel = []
    for i, r in enumerate(rows):
        if str(r.get('price_sensitive')) != '1' or not r.get('ids_id'): continue
        c = r['code']
        if c in hold: g = 'holding'
        elif c in bandc: g = 'bandC'
        else: continue
        sel.append(dict(code=c, ids_id=r['ids_id'], time=r['time'], headline=r['headline'], group=g, in_bandC=int(c in bandc),
                        _k=(0 if g == 'holding' else 1, minutes(r['time']), i)))
    sel.sort(key=lambda x: x['_k'])
    for p, x in enumerate(sel): x.pop('_k'); x['priority'] = p + 1; x['status'] = 'pending'
    return sel


def _save(p, obj):
    with open(p + '.part', 'w') as f: json.dump(obj, f, indent=1, sort_keys=True)
    os.replace(p + '.part', p)


def fetch_pdf(ids_id):
    """terms page then the PDF URL (two paced requests), as item 2"""
    terms = get(f"{BASE}/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId={ids_id}", binary=False)
    pdf_url = re.search(r'name="pdfURL" value="([^"]+)"', terms).group(1)
    return get(pdf_url)


def price_sensitive(day, now=None, fetch=None):
    """item 4 for list-day `day` (its list.csv must exist). Idempotent; resumable; cap counted across runs."""
    fetch = fetch or fetch_pdf
    d = f'{OUT}/asx_notices/{day}'
    if os.path.exists(d + '/DONE_PS'): return f'asx {day} price-sensitive: already stored'
    if not os.path.exists(d + '/list.csv'): return f'asx {day} price-sensitive: no list.csv, nothing done'
    sp = d + '/ps_state.json'
    if os.path.exists(sp):
        with open(sp) as f: st = json.load(f)
    else:
        with open(d + '/list.csv', newline='') as f: rows = list(csv.DictReader(f))
        hold = holdings_codes(); bandc, bmeta = bandc_codes()
        st = dict(day=day, cap=PS_CAP, attempts=0, created_utc=time.strftime('%FT%TZ', time.gmtime()), bandC=bmeta,
                  bandC_codes=sorted(bandc), holdings_codes=sorted(hold), items=select_ps(rows, hold, bandc), runs=[])
        _save(sp, st)
    os.makedirs(d + '/pdf', exist_ok=True)
    run = dict(start_utc=time.strftime('%FT%TZ', time.gmtime()), stopped=None); st['runs'].append(run)
    for it in st['items']:
        if it['status'] != 'pending': continue
        p = f"{d}/pdf/{it['code']}_{it['ids_id']}.pdf"
        if os.path.exists(p):
            it['status'] = 'had'; it['bytes'] = os.path.getsize(p); continue          # stored by item 2: no request
        if st['attempts'] >= st['cap']: it['status'] = 'over_cap'; continue
        if inside_asx_hours(now() if callable(now) else now): run['stopped'] = 'ASX hours'; break
        if shutil.disk_usage(d).free < MIN_FREE: run['stopped'] = 'disk below 1 GB free'; break
        st['attempts'] += 1; it['status'] = 'attempted'; _save(sp, st)                  # counted before the request
        try:
            b = fetch(it['ids_id'])
            if not b.startswith(b'%PDF'): raise ValueError('not a PDF')
            with open(p + '.part', 'wb') as f: f.write(b)
            os.replace(p + '.part', p)
            t = p[:-4] + '.txt'
            subprocess.run(['pdftotext', '-layout', p, t + '.part'], timeout=60, check=False)
            if os.path.exists(t + '.part'): os.replace(t + '.part', t)
            it['status'] = 'ok'; it['bytes'] = len(b); it['text'] = int(os.path.exists(t))
        except Exception as e:
            it['status'] = 'failed'; it['error'] = repr(e)[:200]; print('ps pdf fail', it['code'], it['ids_id'], e, file=sys.stderr)
        _save(sp, st)
    run['end_utc'] = time.strftime('%FT%TZ', time.gmtime())
    cnt = {k: sum(1 for x in st['items'] if x['status'] == k) for k in ('ok', 'had', 'failed', 'over_cap', 'pending')}
    by = sum(x.get('bytes', 0) for x in st['items'] if x['status'] == 'ok')
    _save(sp, st)
    if run['stopped']:
        return f"asx {day} price-sensitive: PAUSED ({run['stopped']}); {cnt}; {st['attempts']}/{st['cap']} attempts used"
    with open(d + '/DONE_PS', 'w') as f:
        f.write(json.dumps(dict(selected=len(st['items']), holdings=sum(x['group'] == 'holding' for x in st['items']),
                                bandC=sum(x['group'] == 'bandC' for x in st['items']), attempts=st['attempts'], cap=st['cap'],
                                bytes_new=by, utc=time.strftime('%FT%TZ', time.gmtime()), **cnt)))
    return f"asx {day} price-sensitive: {len(st['items'])} selected, {cnt['ok']} new PDFs ({by:,} bytes), {cnt['had']} already held, " \
           f"{cnt['failed']} failed, {cnt['over_cap']} over the cap of {st['cap']}"


def asic_short(limit=None):
    d = f'{OUT}/asic_short'; os.makedirs(d, exist_ok=True)
    idx = json.loads(get('https://download.asic.gov.au/short-selling/short-selling-data.json'))
    new = 0
    for e in idx:
        name = f"RR{e['date']}-{e['version']}-SSDailyAggShortPos.csv"
        p = f'{d}/{name}.gz'
        if os.path.exists(p): continue
        if limit is not None and new >= limit: break
        try:
            b = get('https://download.asic.gov.au/short-selling/' + name)
        except Exception as ex:
            print('asic fail', name, ex, file=sys.stderr); continue
        with gzip.open(p + '.part', 'wb') as f: f.write(b)
        os.replace(p + '.part', p); new += 1
    have = len([x for x in os.listdir(d) if x.endswith('.csv.gz')])
    return f'asic short: {new} new files, {have} stored of {len(idx)} listed (latest {idx[0]["date"]})'


if __name__ == '__main__':
    which = sys.argv[1:] or ['asx', 'asic']
    lim = None
    for a in which:
        if a.startswith('--asic-limit='): lim = int(a.split('=')[1])
    if 'asx' in which: print(asx_notices())
    if 'asic' in which: print(asic_short(lim))
