# NEWS-C step 2: build the day's BLINDED rating input. INFORMATION ONLY: feeds no paper line and no trade.
# Draft amendment AMENDMENT_info_NEWSC_v1.md s2, s5 (review_news/REVIEW.md, draft spec NEWS-C).
#   python3 newsc_prepare.py [--day YYYY-MM-DD]      (default: the ASX session before today, Sydney; run after info_archive.py,
#                                                      before 10:00)
# Reads only asx_notices/<day>/ (list.csv, ps_state.json, pdf/*.txt) and, for the baselines, earlier archived list-days.
# Writes newsc/<day>/: input.jsonl (+ input.sha256), batches/<arm>_<nn>.jsonl (the canonical batch) and batches/<arm>_<nn>.txt (the
# same items rendered as plain text with lines of at most 500 characters: THE FILE THE RATER READS), manifest.json and
# baselines.jsonl (never given to the rater). Never overwrites: a re-run that would produce identical input is a no-op; a re-run that
# would produce different input is refused (exit 2).
# BLINDING: an item carries only the code, the announcement day, and per announcement the time, the headline (both arms) and the
# extracted text cut to 30,000 characters (arm F). No prices, returns, volumes, holdings flags, groups, ranks, earlier ratings,
# baseline values or dates other than the announcement day. The code is kept (spec s2: arm H is "code, time, headline").
# The announcement type is NOT given: the ASX list carries none, and the KEY type is a baseline the AI is measured against
# (s7 "added value"); the rater assigns its own type from the 14 in RUBRIC_v1.md.
import argparse, hashlib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import newsc_baselines as B

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
NOTICES = S + '/bigwins_forward/data/asx_notices'
NEWSC = S + '/bigwins_forward/data/newsc'
MAX_TEXT = 30_000                    # characters of extracted text per announcement (arm F)
BATCH_CHARS = 60_000                 # max characters of item JSON per rater call (an item is never split)
WRAP = 500                           # max characters per line of the rendered batch (the Read tool cuts lines above 2,000)
ITEM_KEYS = {'item_id', 'arm', 'code', 'announcement_day', 'announcements'}
ANN_KEYS_H = {'ann_id', 'time', 'headline'}
ANN_KEYS_F = ANN_KEYS_H | {'text', 'text_available', 'text_truncated'}


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, 'rb') as f: return sha_bytes(f.read())


def clean_text(t):
    """pdftotext -layout output -> compact text: runs of spaces/tabs to one space, trailing spaces cut, 3+ newlines to 2"""
    t = t.replace('\r', '').replace('\f', '\n')
    t = re.sub(r'[ \t ]+', ' ', t)
    t = '\n'.join(l.strip() for l in t.split('\n'))
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def check_blind(item):
    """refuse any field outside the whitelist (the test also scans values for prices and holdings words)"""
    assert set(item) == ITEM_KEYS, ('item keys', set(item) ^ ITEM_KEYS)
    for a in item['announcements']:
        want = ANN_KEYS_F if item['arm'] == 'F' else ANN_KEYS_H
        assert set(a) == want, ('announcement keys', set(a) ^ want)


def build(day, notices=None):
    """-> (lines_H, lines_F, manifest, baselines); deterministic for a stored list-day"""
    notices = notices or NOTICES
    d = f'{notices}/{day}'
    if not os.path.exists(d + '/DONE_PS'): raise SystemExit(f'prepare {day}: archive item 4 not complete (no DONE_PS) - refused')
    with open(d + '/ps_state.json') as f: ps = json.load(f)
    bandc, hold = set(ps['bandC_codes']), set(ps['holdings_codes'])
    universe = {c: 'C' for c in bandc}; universe.update({c: 'H' for c in hold if c not in bandc})   # H = holding outside band C
    rows = B.read_list(day, notices)
    psi = {x['ids_id']: x for x in ps['items']}
    by_code = {}
    for i, r in enumerate(rows):
        c = r['code']
        if c not in universe: continue
        h = r['headline']
        if not (str(r['price_sensitive']) == '1' or B.HALT_START.search(h) or B.SUSP_START.search(h)): continue
        by_code.setdefault(c, []).append((B._minutes(r['time']), -i, r))
    H, F, man_items = [], [], []
    for c in sorted(by_code):
        anns = [x[2] for x in sorted(by_code[c], key=lambda x: (x[0], x[1]))]
        iid = f'{day}:{c}'
        ah, af, meta = [], [], []
        for r in anns:
            ah.append(dict(ann_id=r['ids_id'], time=r['time'], headline=r['headline']))
            raw = B.text_of(day, c, r['ids_id'], notices) if r['ids_id'] else None
            txt = clean_text(raw) if raw else ''
            st = psi.get(r['ids_id'], {}).get('status', 'not_selected')
            af.append(dict(ann_id=r['ids_id'], time=r['time'], headline=r['headline'], text=txt[:MAX_TEXT],
                           text_available=bool(txt), text_truncated=len(txt) > MAX_TEXT))
            meta.append(dict(ann_id=r['ids_id'], price_sensitive=int(str(r['price_sensitive']) == '1'), archive_status=st,
                             text_sha256=(sha_bytes(raw.encode()) if raw else None), text_chars=len(txt),
                             key=list(B.key(r['headline']))))
        for arm, a, out in (('H', ah, H), ('F', af, F)):
            it = dict(item_id=iid, arm=arm, code=c, announcement_day=day, announcements=a)
            check_blind(it)
            out.append(json.dumps(it, sort_keys=True, ensure_ascii=False))
        man_items.append(dict(item_id=iid, code=c, group=universe[c], n_announcements=len(anns), announcements=meta,
                              missing_text=sum(1 for x in af if not x['text_available'])))
    base = B.compute(day, universe, notices)
    return H, F, dict(day=day, list_sha256=sha_file(d + '/list.csv'), ps_state_sha256=sha_file(d + '/ps_state.json'),
                      bandC=ps['bandC'], bandC_codes=sorted(bandc), n_holdings_codes=len(hold), items=man_items, max_text=MAX_TEXT), base


def _wrap(s):
    out = []
    for l in s.split('\n'):
        out += [l[i:i + WRAP] for i in range(0, len(l), WRAP)] or ['']
    return out


def render(lines, name):
    """deterministic plain-text rendering of a batch (JSON lines) for the rater; newsc_record.py re-renders and compares"""
    arm = name[0]
    o = [f'=== NEWS-C BATCH {name} (arm {arm}) ===']
    for l in lines:
        it = json.loads(l)
        o.append(f"--- ITEM {it['item_id']} | code {it['code']} | announcement day {it['announcement_day']} | arm {it['arm']} ---")
        for a in it['announcements']:
            o.append(f"[ANNOUNCEMENT ann_id={a['ann_id']} | time {a['time']}]")
            o += _wrap('HEADLINE: ' + a['headline'])
            if arm == 'F':
                o.append(f"TEXT (text_available: {str(a['text_available']).lower()}, text_truncated: {str(a['text_truncated']).lower()}):")
                o += _wrap(a['text']) if a['text'] else ['(no text)']
            o.append('[END ANNOUNCEMENT]')
        o.append('--- END ITEM ---')
    o.append('=== END BATCH ===')
    return ('\n'.join(o) + '\n').encode()


def prev_session_today():
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import exchange_calendars as xc
    today = datetime.now(ZoneInfo('Australia/Sydney')).date()
    ss = xc.get_calendar('XASX', start=str(today - timedelta(days=20)), end=str(today)).sessions
    return [str(x.date()) for x in ss if x.date() < today][-1]


def batches(lines, arm):
    out, cur, n = [], [], 0
    for l in lines:
        if cur and n + len(l) > BATCH_CHARS: out.append(cur); cur, n = [], 0
        cur.append(l); n += len(l)
    if cur: out.append(cur)
    return [(f'{arm}_{i + 1:02d}', b) for i, b in enumerate(out)]


def write_atomic(p, data):
    with open(p + '.part', 'wb') as f: f.write(data)
    os.replace(p + '.part', p)


def prepare(day, notices=None, newsc=None):
    newsc = newsc or NEWSC
    H, F, man, base = build(day, notices)
    inp = ('\n'.join(H + F) + '\n').encode() if (H or F) else b''
    isha = sha_bytes(inp)
    od = f'{newsc}/{day}'
    if os.path.exists(od + '/input.jsonl'):
        if sha_file(od + '/input.jsonl') == isha: return f'prepare {day}: already prepared (identical input {isha[:12]}); nothing written', 0
        return f'prepare {day}: REFUSED - input.jsonl exists and differs from a fresh build; nothing overwritten', 2
    os.makedirs(od + '/batches', exist_ok=True)
    bl = []
    for name, b in batches(H, 'H') + batches(F, 'F'):
        data = ('\n'.join(b) + '\n').encode()
        txt = render(b, name)
        write_atomic(f'{od}/batches/{name}.jsonl', data); write_atomic(f'{od}/batches/{name}.txt', txt)
        bl.append(dict(batch=name, arm=name[0], sha256=sha_bytes(data), txt_sha256=sha_bytes(txt),
                       items=[json.loads(x)['item_id'] for x in b], chars=len(data), txt_lines=txt.count(b'\n')))
    bdata = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in base).encode()
    write_atomic(od + '/baselines.jsonl', bdata)
    man.update(input_sha256=isha, batches=bl, baselines_sha256=sha_bytes(bdata), n_items=len(H),
               n_announcements=sum(x['n_announcements'] for x in man['items']),
               n_missing_text=sum(x['missing_text'] for x in man['items']),
               code_sha256={f: sha_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), f)) for f in
                            ('newsc_prepare.py', 'newsc_baselines.py', 'info_archive.py')})
    write_atomic(od + '/manifest.json', json.dumps(man, indent=1, sort_keys=True).encode())
    write_atomic(od + '/input.jsonl', inp)                       # last: its presence marks a complete preparation
    write_atomic(od + '/input.sha256', (isha + '  input.jsonl\n').encode())
    return (f"prepare {day}: {len(H)} code-days, {man['n_announcements']} announcements ({man['n_missing_text']} without text), "
            f"batches {', '.join(x['batch'] for x in bl) or 'none'}; input sha256 {isha}"), 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', default=None)
    ap.add_argument('--notices', default=None)
    ap.add_argument('--newsc', default=None)
    a = ap.parse_args()
    msg, rc = prepare(a.day or prev_session_today(), a.notices, a.newsc)
    print(msg); sys.exit(rc)
