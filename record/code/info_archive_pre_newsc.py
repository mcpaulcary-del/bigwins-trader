# Forward archive of free public information for research (owner decision 24 Nov 2026). INFORMATION ONLY:
# nothing here feeds any paper line or the live trader. Private, personal, non-commercial use only.
#   1. ASX announcements list (previous trading day, 1 request) -> list CSV of every headline.
#   2. PDFs of director-interest notices (Appendix 3Y/3X/3Z) and capital-raising notices (proposed issue,
#      quotation, placement, entitlement, SPP, cleansing) -> PDF + extracted text. Polite: one request every 2 s.
#   3. ASIC daily aggregated short positions (published with a ~4 trading-day lag) -> every listed date not yet
#      stored (first run backfills the history to 2010), gzipped.
# The owner's exception to "no automated access to asx.com.au" covers ONLY items 1-2 (ledger/HANDOVER).
# Idempotent: a day's folder or a short file already stored is skipped.
import csv, gzip, html, json, os, re, subprocess, sys, time, urllib.request

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
OUT = S + '/bigwins_forward/data'
UA = {'User-Agent': 'Mozilla/5.0 (private personal research; low rate)'}
GAP = 2.0
LIST_URL = 'https://www.asx.com.au/asx/v2/statistics/prevBusDayAnns.do'
BASE = 'https://www.asx.com.au'
KEEP = re.compile(r"director'?s?.? interest|appendix 3[xyz]|proposed issue|application for quotation|placement|"
                  r"entitlement|capital raising|share purchase plan|cleansing|appendix 2a|appendix 3b", re.I)
_last = [0.0]


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
    if os.path.exists(d + '/DONE'): return f'asx {day}: already stored'
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
