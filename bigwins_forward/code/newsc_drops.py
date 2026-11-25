# NEWS-C big-drop + cause log, step 1: detect the previous session's big drops, classify the cause, build the blinded dossier.
# INFORMATION ONLY: feeds no paper line and no trade; never evidence for or against EMG2. Draft AMENDMENT_info_NEWSC_drops_v1.md.
#   python3 newsc_drops.py [--day D]            (default D = the ASX session before today, Sydney; run after info_archive.py asx)
#   python3 newsc_drops.py --detect-only --from A --to B [--bulk DIR] [--decisions DIR]   (read only: prints events, writes nothing)
# EVENT (research_dip PREREG s2, "D1", frozen there): on session D a pool member's one-day total return minus the ASX 200 total
#   return (A200.AU close + distribution, from the same bulk file) is <= -10%, and its raw close on the previous session is >= A$1.
#   Excluded: days on which the total-return ratio and the raw-close ratio differ by more than 12% in log (split, spin-off or
#   capital return on the day; vendor split ratio and confirmed CORPORATE_ACTIONS.csv cash both count). A one-day total return
#   below -95% or above +1000% is treated as missing (research_dip load_asx). A name cannot fire again within 20 sessions of its
#   previous event (t - t_last <= 20 sessions: no event; a blocked day does not restart the count). The re-fire chain runs over
#   every ASX session from CHAIN_START (the first session with two bulk files), so it never depends on files written here.
# POOL: the project's point-in-time traded-value ranking, i.e. the `ranks`/`rows` of the latest paper decision file
#   (out/paper_state/decisions/decision_<asof>.json, bw13_prep: 252-session median traded value, >= 200 traded sessions, Common
#   Stock, ETPs out) with asof strictly before D; vrank <= 100 and that table's close >= A$1 (research_dip: "pool at the latest
#   month-end strictly before t", "last close >= A$1").
# NEWS: the code's headlines in asx_notices/<D>/list.csv (all of D) and asx_notices/<D-1>/list.csv filed at or after 16:00 Sydney
#   (late-filed on D-1). Keyword input ("focused") = price-sensitive headlines plus halt/suspension headlines
#   (newsc_baselines.HALT_START / SUSP_START), de-duplicated on the first 60 lower-case characters as research_dip classify.focused.
#   PDF text: only files ALREADY stored by the archive (item 2 notices, item 4 band C / holdings); this script makes no request.
# CAUSE: the FROZEN research_dip keyword classifier (newsc_drops_classify.py = research_dip/code/classify.py byte for byte,
#   SHA-256 CLASSIFY_SHA256): TEMP / FUND / OTHER / NONE -> temporary / fundamental / other-news / no-news, with the sub-cause.
# DOSSIER for the blinded rater (DROPS_RUBRIC_v1.md): opaque ids, Company A, day offsets, no prices, no returns, no ranks, no date.
#   It is written to newsc/drops_blind/<sha16>.txt (a path without the date); the canonical masked items go to
#   newsc/<D>/drops_dossier.jsonl. Events with no headline at all are not in the dossier (rater label N = no news, mechanical).
# Writes newsc/<D>/: drops.jsonl (one row per event; empty file on a day without events), drops.sha256, drops_dossier.jsonl,
#   drops_manifest.json; and newsc/drops_blind/<sha16>.txt. Never overwrites: an identical re-run is a no-op, a different one is
#   refused (exit 2). Writes nothing to the ledger (newsc_drops_record.py does).
import argparse, csv, glob, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paper_lib as P
import newsc_baselines as B
import newsc_drops_classify as KC

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
NEWSC = S + '/bigwins_forward/data/newsc'
NOTICES = S + '/bigwins_forward/data/asx_notices'
DEC_DIR = P.DEC_DIR
CLASSIFY_SHA256 = 'b7c98fbde718f3c4c5176ea205a2f56416820d95ba296f78d87980626cb2c4cc'   # research_dip/code/classify.py (PREREG s4a)
DROPS_RUBRIC = 'DROPS_RUBRIC_v1.md'
DROPS_RUBRIC_NAME = 'NEWSC_DROPS_RUBRIC_v1'
DROPS_RUBRIC_SHA256 = 'dbb9cef411e06882cd405df70c19dcad8f13df7d4da717ea474bcbf41f2a1ddc'
INDEX = 'A200'                       # ASX 200 total return (ETF close + distribution), the project's A200 comparator
THR = -0.10                          # PREREG s2 D1
PRICE_MIN = 1.0                      # A$1 raw close on D-1, and the pool table's close
CA_LOG = 0.12                        # split / capital-return guard
REFIRE = 20                          # sessions
POOL_N = 100
MIN_POOL_CLOSES = 90                 # fewer pool members with a close on D than this: the bulk file is incomplete -> refused
CHAIN_START = '2026-11-18'           # first session with a bulk file for itself and the session before (bulk starts 2026-11-17)
LATE_FROM = 16 * 60                  # D-1 headlines filed at or after 16:00 Sydney count as late-filed
MAX_FOCUSED, MAX_OTHER, MAX_TEXTS, TEXT_CHARS, HEAD_CHARS, WRAP = 10, 6, 3, 1500, 200, 500
CLASS_NAME = {'TEMP': 'temporary', 'FUND': 'fundamental', 'OTHER': 'other-news', 'NONE': 'no-news'}
CODE_FILES = ('newsc_drops.py', 'newsc_drops_classify.py', 'newsc_drops_record.py', 'newsc_score.py', 'paper_lib.py',
              'newsc_baselines.py')


class Refuse(Exception): pass


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, 'rb') as f: return sha_bytes(f.read())


# ---------------------------------------------------------------- pool and prices
def decisions(dec_dir=None):
    """{asof: path} of the stored paper decision files"""
    dec_dir = dec_dir or DEC_DIR
    out = {}
    for p in glob.glob(dec_dir + '/decision_*.json'):
        m = re.search(r'decision_(\d{4}-\d\d-\d\d)\.json$', p)
        if m: out[m.group(1)] = p
    return out


_POOL = {}


def pool_for(d, decs):
    """pool on session d: vrank <= 100 and table close >= A$1 in the latest decision file with asof < d.
    -> (asof, sha256, {cid: dict(cid, code, name, rank)}) or (None, None, {})"""
    prior = sorted(a for a in decs if a < d)
    if not prior: return None, None, {}
    a = prior[-1]; p = decs[a]
    if p not in _POOL:
        with open(p, 'rb') as f: raw = f.read()
        dec = json.loads(raw); pool = {}
        for r in dec['rows']:
            px = r.get('rawclose') if r.get('rawclose') is not None else r.get('close10')
            if r['vrank'] <= POOL_N and px is not None and px >= PRICE_MIN:
                pool[r['cid']] = dict(cid=r['cid'], code=r['code'], name=r.get('name', ''), rank=int(r['vrank']))
        _POOL[p] = (a, sha_bytes(raw), pool)
    return _POOL[p]


_DAY = {}


def day_data(d):
    """paper_lib.load_day(d) (raw closes, volumes, AUD cash distributions incl. confirmed corporate actions, splits), cached"""
    k = (P.BULK, d)
    if k not in _DAY: _DAY[k] = P.load_day(d)
    return _DAY[k]


def tr1(code, m0, m1):
    """(total-return ratio, raw ratio, raw close d-1, raw close d) for one session, or None if either close is missing"""
    p0, p1 = m0['close'].get(code), m1['close'].get(code)
    if not p0 or not p1: return None
    sp = m1['split'].get(code) or 1.0
    dv = m1['div'].get(code, 0.0)
    return sp * (p1 + dv) / p0, p1 / p0, p0, p1


def candidates(d, prev, decs):
    """D1 hits on session d before the re-fire rule. -> (hits, info). Raises Refuse when the day cannot be measured."""
    m1, m0 = day_data(d), day_data(prev)
    if m1 is None or m0 is None: raise Refuse(f'{d}: no bulk file for {d if m1 is None else prev}')
    asof, dsha, pool = pool_for(d, decs)
    if not pool: raise Refuse(f'{d}: no paper decision file dated before {d} (pool unknown)')
    ix = tr1(INDEX, m0, m1)
    if ix is None: raise Refuse(f'{d}: {INDEX} has no close on {prev} or {d} (index return unknown)')
    ir = ix[0] - 1
    hits, have = [], 0
    for cid, x in sorted(pool.items(), key=lambda kv: kv[1]['rank']):
        t = tr1(x['code'], m0, m1)
        if t is None: continue
        have += 1
        tr, raw, p0, p1 = t; r = tr - 1
        if r < -0.95 or r > 10: continue                         # research_dip load_asx: such returns are missing
        xr = r - ir; ca = abs(math.log(tr / raw))
        if xr <= THR and p0 >= PRICE_MIN and ca <= CA_LOG:
            hits.append(dict(cid=cid, code=x['code'], name=x['name'], rank=x['rank'], close_prev=p0, close=p1,
                             split=m1['split'].get(x['code']), cash=m1['div'].get(x['code']), ret=r, raw_ret=raw - 1,
                             index_ret=ir, xr=xr, ca_log=ca))
        elif xr <= THR and p0 >= PRICE_MIN:
            hits.append(dict(cid=cid, code=x['code'], excluded='split or capital return on the day', ca_log=ca, xr=xr))
        elif xr <= THR:
            hits.append(dict(cid=cid, code=x['code'], excluded='raw close on the previous session below A$1', close_prev=p0, xr=xr))
    return hits, dict(pool_asof=asof, pool_sha256=dsha, pool_n=len(pool), pool_with_close=have, index_ret=ir)


def chain(D, decs, start=None):
    """events of every session from start to D with the 20-session re-fire rule.
    -> (events {day: [hit]}, blocked {day: [hit]}, excluded {day: [hit]}, gaps [(day, reason)], info of D)"""
    ss = P.sessions(); start = start or CHAIN_START
    days = [x for x in ss if start <= x <= D]
    last, ev, bl, exc, gaps, info = {}, {}, {}, {}, [], None
    for d in days:
        i = ss.index(d); prev = ss[i - 1]
        try: hits, inf = candidates(d, prev, decs)
        except Refuse as e:
            if d == D: raise
            gaps.append((d, str(e))); continue
        if d == D: info = inf
        for h in hits:
            if h.get('excluded'): exc.setdefault(d, []).append(h); continue
            if h['cid'] in last and i - last[h['cid']] <= REFIRE:
                h = dict(h, blocked_by=ss[last[h['cid']]]); bl.setdefault(d, []).append(h); continue
            last[h['cid']] = i; ev.setdefault(d, []).append(h)
    return ev, bl, exc, gaps, info


# ---------------------------------------------------------------- headlines and text
def list_rows(day, notices):
    p = f'{notices}/{day}/list.csv'
    if not os.path.exists(p): return None
    with open(p, newline='') as f: return list(csv.DictReader(f))


def is_focused(r):
    return str(r.get('price_sensitive')) == '1' or bool(B.HALT_START.search(r['headline'])) or bool(B.SUSP_START.search(r['headline']))


def news_for(code, D, prev, rows_D, rows_prev, notices, ps_items):
    """-> (focused, other): lists of dicts in time order, D-1 late-filed first. Text only from files already stored."""
    out = []
    for day, rows, off in ((prev, rows_prev or [], -1), (D, rows_D or [], 0)):
        for i, r in enumerate(rows):
            if r['code'] != code: continue
            mn = B._minutes(r['time'])
            if off == -1 and mn < LATE_FROM: continue
            raw = B.text_of(day, code, r['ids_id'], notices) if r.get('ids_id') else None
            origin = None
            if raw is not None:
                origin = 'item4' if (day, r['ids_id']) in ps_items else ('item2' if str(r.get('kept')) == '1' else 'stored')
            out.append(dict(list_day=day, off=off, time=r['time'], minutes=mn, order=i, price_sensitive=int(str(r['price_sensitive']) == '1'),
                            headline=r['headline'].strip(), ids_id=r.get('ids_id', ''), focused=int(is_focused(r)),
                            text_sha256=(sha_bytes(raw.encode()) if raw is not None else None), text_origin=origin, _raw=raw))
    out.sort(key=lambda x: (x['off'], x['minutes'], -x['order']))       # the list runs latest first; -order keeps filing order
    seen, F, O = set(), [], []
    for x in out:
        k = x['headline'].lower()[:60]
        if k in seen: continue
        seen.add(k); (F if x['focused'] else O).append(x)
    return F, O


def ps_items_of(day, notices):
    p = f'{notices}/{day}/ps_state.json'
    if not os.path.exists(p): return set()
    with open(p) as f: st = json.load(f)
    return {(day, x['ids_id']) for x in st.get('items', []) if x.get('status') in ('ok', 'had')}


# ---------------------------------------------------------------- masking (frozen with this file)
STOP = {'the', 'inc', 'corp', 'ltd', 'limited', 'group', 'holdings', 'company', 'corporation', 'plc', 'class', 'and', 'com', 'new',
        'international', 'global', 'technologies', 'resources', 'financial', 'energy', 'mining', 'australia', 'australian', 'bank',
        'pharmaceuticals', 'entertainment', 'health', 'healthcare', 'trust', 'fund', 'reit', 'stapled', 'units', 'unit', 'nl', 'pty',
        'securities', 'for', 'fully', 'paid', 'ordinary'}
MONTHS = r'(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)'
RX_DATE = [re.compile(r'\b\d{1,2}(?:st|nd|rd|th)?\s+' + MONTHS + r'\b\.?,?(?:\s+(?:19|20)\d\d)?', re.I),
           re.compile(r'\b' + MONTHS + r'\b\.?\s+\d{1,2}(?:st|nd|rd|th)?,?(?:\s+(?:19|20)\d\d)?', re.I),
           re.compile(r'\b\d{1,2}[/.-]\d{1,2}[/.-](?:19|20)?\d\d\b')]
RX_FY = re.compile(r"\b(FY|CY|HY|[12]H|H[12]|Q[1-4])\s?'?(?:(?:19|20)\d\d|\d\d)\b", re.I)
RX_YEAR = re.compile(r'\b(?:19|20)\d\d\b')
RX_MONEY = re.compile(r'(?:A\$|AU\$|US\$|NZ\$|AUD\s?|USD\s?|\$)\s?(?>\d[\d,]*(?:\.\d+)?)(?!\s*(?:m|mn|mil|million|b|bn|billion|k|thousand)\b)', re.I)
RX_CENTS = re.compile(r'\b(?>\d+(?:\.\d+)?)\s?(?:cents?|cps|c)\b', re.I)
RX_PRICEWORD = re.compile(r'\b(price|priced|close|closing|vwap)\b([^.\d\n]{0,30}?)(?>\d+\.\d+)', re.I)
RX_TICK = re.compile(r'\(\s*(?:ASX|NZX|TSX|NYSE|NASDAQ|LSE|OTCQX)\s*:\s*[A-Z0-9.]+\s*\)|\b(?:ASX|NZX)\s*:\s*[A-Z0-9]{2,6}\b')


def name_tokens(name):
    return [w for w in re.findall(r"[A-Za-z0-9&']+", name or '') if len(w) >= 3 and w.lower() not in STOP]


def mask(s, code, name):
    """company name words and code -> Company A; dates -> [date]; years -> YYYY; per-share money amounts -> $[amount]"""
    s = RX_TICK.sub('Company A', s)
    if code: s = re.sub(r'\b' + re.escape(code) + r'\b', 'Company A', s)
    toks = name_tokens(name)
    if toks: s = re.sub(r"\b(?:" + '|'.join(re.escape(w) for w in sorted(set(toks), key=len, reverse=True)) + r")\b(?:'s)?", 'Company A', s, flags=re.I)
    for rx in RX_DATE: s = rx.sub('[date]', s)
    s = RX_FY.sub(lambda m: m.group(1) + 'YY', s)
    s = RX_YEAR.sub('YYYY', s)
    s = RX_MONEY.sub('$[amount]', s)
    s = RX_CENTS.sub('[amount]', s)
    s = RX_PRICEWORD.sub(lambda m: m.group(1) + m.group(2) + '[amount]', s)
    s = re.sub(r'(?:Company A[\s,]*){2,}', 'Company A ', s)
    return re.sub(r'\s+', ' ', s).strip()


def dossier_items(D, events):
    """masked canonical items for the rater, in opaque id order"""
    items = []
    for e in events:
        if not e['headlines']: continue
        lines, texts = [], []
        F = [h for h in e['headlines'] if h['focused']][:MAX_FOCUSED]
        O = [h for h in e['headlines'] if not h['focused']][:MAX_OTHER]
        for h in F + O:
            lines.append(dict(off=h['off'], time=h['time'], ps=h['price_sensitive'], headline=mask(h['headline'], e['code'], e['name'])[:HEAD_CHARS]))
        for h in F:
            if len(texts) >= MAX_TEXTS: break
            if h.get('_raw'):
                t = mask(h['_raw'], e['code'], e['name'])[:TEXT_CHARS]
                if t: texts.append(dict(off=h['off'], time=h['time'], text=t))
        items.append(dict(id=e['id'], announcements=lines, texts=texts))
    return items


def _wrap(s):
    return [s[i:i + WRAP] for i in range(0, len(s), WRAP)] or ['']


def offs(o): return 'D-1' if o == -1 else 'D0'


def render(items):
    """deterministic plain text the rater reads; newsc_drops_record.py re-renders and compares"""
    o = ['=== NEWS-C DROPS DOSSIER ===']
    for it in items:
        o.append(f"--- COMPANY {it['id']} ---")
        for a in it['announcements']:
            tag = 'price-sensitive' if a['ps'] else 'not marked price-sensitive'
            o += _wrap(f"{offs(a['off'])} {a['time']} [{tag}] HEADLINE: {a['headline']}")
        for t in it['texts']:
            o.append(f"TEXT of the {offs(t['off'])} {t['time']} announcement (first {TEXT_CHARS:,} characters, masked):")
            o += _wrap(t['text'])
            o.append('[END TEXT]')
        o.append('--- END COMPANY ---')
    o.append('=== END DOSSIER ===')
    return ('\n'.join(o) + '\n').encode()


def canon(rows): return ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False) + '\n' for r in rows).encode()


# ---------------------------------------------------------------- the day
def check_frozen(newsc):
    c = sha_file(os.path.join(HERE, 'newsc_drops_classify.py'))
    if c != CLASSIFY_SHA256: raise Refuse(f'newsc_drops_classify.py hashes to {c}, not the frozen research_dip classifier {CLASSIFY_SHA256}')
    r = sha_file(f'{newsc}/{DROPS_RUBRIC}')
    if r != DROPS_RUBRIC_SHA256: raise Refuse(f'{DROPS_RUBRIC} hashes to {r}, not the frozen {DROPS_RUBRIC_SHA256}')
    return c, r


def build(D, newsc=None, notices=None, dec_dir=None):
    """-> (drops rows, dossier items, manifest); pure: writes nothing"""
    newsc = newsc or NEWSC; notices = notices or NOTICES
    csha, rsha = check_frozen(newsc)
    ss = P.sessions()
    if D not in ss: raise Refuse(f'{D} is not an ASX session')
    prev = ss[ss.index(D) - 1]
    rows_D = list_rows(D, notices)
    if rows_D is None or not os.path.exists(f'{notices}/{D}/DONE'): raise Refuse(f'{D}: list.csv not archived (run info_archive.py asx first)')
    rows_prev = list_rows(prev, notices)
    decs = decisions(dec_dir)
    ev, bl, exc, gaps, info = chain(D, decs)
    warn = []
    if info['pool_with_close'] < MIN_POOL_CLOSES:
        raise Refuse(f"{D}: only {info['pool_with_close']} of {info['pool_n']} pool members have a close in the bulk file (incomplete)")
    ss_i = ss.index(D)
    near = [g for g in gaps if ss_i - ss.index(g[0]) <= REFIRE]
    if near: warn.append(f're-fire chain has {len(near)} unmeasured session(s) in the last {REFIRE}: ' + '; '.join(f'{a}: {b}' for a, b in near))
    if rows_prev is None: warn.append(f'D-1 list {prev} not archived: late-filed D-1 headlines unavailable')
    if not os.path.exists(f'{notices}/{D}/DONE_PS'): warn.append(f'{D}: price-sensitive PDF step not complete (no DONE_PS): texts may be missing')
    # consistency with the days already written (the chain is recomputed from the bulk files; a difference is reported)
    for d in [x for x in ss if CHAIN_START <= x < D]:
        p = f'{newsc}/{d}/drops.jsonl'
        if os.path.exists(p):
            with open(p) as f: had = sorted(json.loads(l)['cid'] for l in f if l.strip())
            now = sorted(h['cid'] for h in ev.get(d, []))
            if had != now: warn.append(f'FAIL chain check: {d} drops.jsonl has {had}, recomputed {now}')
    psi = ps_items_of(D, notices) | ps_items_of(prev, notices)
    events = []
    for h in ev.get(D, []):
        F, O = news_for(h['code'], D, prev, rows_D, rows_prev, notices, psi)
        cls, sub, n, nT, nF = KC.keyword([x['headline'] for x in F])
        events.append(dict(h, day=D, prev_session=prev, headlines=F + O, n_focused=len(F), n_other=len(O),
                           kw=dict(cls=cls, sub=sub, n=n, nT=nT, nF=nF), cause_kw=CLASS_NAME[cls], cause_kw_sub=sub))
    events.sort(key=lambda e: sha_bytes(f"{D}|{e['cid']}".encode()))          # opaque order: not by rank or size of the fall
    for k, e in enumerate(events): e['id'] = f'X{k + 1}'
    for e in events: e['in_dossier'] = int(bool(e['headlines']))
    items = dossier_items(D, events)
    for e in events:
        for x in e['headlines']: x.pop('_raw', None); x.pop('order', None)
    drows = [dict(e) for e in events]
    ddata = canon(drows); idata = canon(items); txt = render(items)
    man = dict(day=D, prev_session=prev, statement='Information only. Feeds no paper line and no trade; never evidence for or against EMG2.',
               pool=dict(source='paper decision file (bw13_prep traded-value ranking)', asof=info['pool_asof'], sha256=info['pool_sha256'],
                         n=info['pool_n'], with_close_on_D=info['pool_with_close']),
               index=dict(code=INDEX, ret=info['index_ret']),
               bulk_sha256={d: (sha_file(f'{P.BULK}/{d}/eod.json.gz') if os.path.exists(f'{P.BULK}/{d}/eod.json.gz') else None) for d in (prev, D)},
               list_sha256={d: (sha_file(f'{notices}/{d}/list.csv') if os.path.exists(f'{notices}/{d}/list.csv') else None) for d in (prev, D)},
               n_events=len(events), n_in_dossier=len(items), blocked_by_refire=bl.get(D, []), excluded=exc.get(D, []),
               drops_sha256=sha_bytes(ddata), dossier_jsonl_sha256=sha_bytes(idata), dossier_txt_sha256=sha_bytes(txt),
               dossier_path=(f'drops_blind/{sha_bytes(txt)[:16]}.txt' if items else None),
               classifier_sha256=csha, rubric_sha256=rsha, warnings=warn, chain_start=CHAIN_START,
               code_sha256={f: sha_file(os.path.join(HERE, f)) for f in CODE_FILES if os.path.exists(os.path.join(HERE, f))},
               counts=dict(by_cause_kw={c: sum(1 for e in events if e['cause_kw'] == c) for c in CLASS_NAME.values()}))
    return ddata, idata, txt, man


def write_atomic(p, data):
    with open(p + '.part', 'wb') as f: f.write(data)
    os.replace(p + '.part', p)


def run(D, newsc=None, notices=None, dec_dir=None):
    newsc = newsc or NEWSC
    ddata, idata, txt, man = build(D, newsc, notices, dec_dir)
    od = f'{newsc}/{D}'
    if os.path.exists(od + '/drops.sha256'):
        old = open(od + '/drops.sha256').read().split()[0]
        if old == man['drops_sha256'] and os.path.exists(od + '/drops_dossier.jsonl') and sha_file(od + '/drops_dossier.jsonl') == man['dossier_jsonl_sha256']:
            return f'drops {D}: already prepared (identical, drops sha256 {old[:12]}); nothing written', 0, man
        return f'drops {D}: REFUSED - drops.jsonl exists and differs from a fresh build; nothing overwritten', 2, man
    os.makedirs(od, exist_ok=True)
    if man['dossier_path']:
        os.makedirs(f'{newsc}/drops_blind', exist_ok=True); write_atomic(f"{newsc}/{man['dossier_path']}", txt)
    write_atomic(od + '/drops_dossier.jsonl', idata)
    write_atomic(od + '/drops_manifest.json', json.dumps(man, indent=1, sort_keys=True).encode())
    write_atomic(od + '/drops.jsonl', ddata)
    write_atomic(od + '/drops.sha256', (man['drops_sha256'] + '  drops.jsonl\n').encode())     # last: marks a complete step
    w = '; '.join(man['warnings'])
    return (f"drops {D}: {man['n_events']} events ({man['n_in_dossier']} in the dossier"
            + (f", file {man['dossier_path']}, sha256 {man['dossier_txt_sha256']}" if man['dossier_path'] else '')
            + f"); by keyword cause {man['counts']['by_cause_kw']}; drops sha256 {man['drops_sha256']}"
            + (f'; warnings: {w}' if w else '')), 0, man


def detect_only(a, b, dec_dir=None, start=None):
    """read only: events per session in [a, b] (chain from `start`)"""
    decs = decisions(dec_dir)
    ev, bl, exc, gaps, _ = chain(b, decs, start)
    days = [x for x in P.sessions() if a <= x <= b]
    return {d: dict(events=ev.get(d, []), blocked=bl.get(d, []), excluded=exc.get(d, [])) for d in days}, gaps


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--day'); ap.add_argument('--newsc'); ap.add_argument('--notices'); ap.add_argument('--decisions')
    ap.add_argument('--bulk'); ap.add_argument('--detect-only', action='store_true'); ap.add_argument('--from', dest='a')
    ap.add_argument('--to', dest='b'); ap.add_argument('--chain-start')
    a = ap.parse_args()
    if a.bulk: P.BULK = a.bulk
    if a.detect_only:
        R, gaps = detect_only(a.a, a.b, a.decisions, a.chain_start)
        for d, x in R.items():
            print(d, len(x['events']), 'events', [(e['code'], round(e['xr'], 4)) for e in x['events']],
                  'blocked', [e['code'] for e in x['blocked']], 'excluded', [(e['code'], e['excluded']) for e in x['excluded']])
        print('sessions', len(R), 'events', sum(len(x['events']) for x in R.values()), 'unmeasured', gaps)
        sys.exit(0)
    if not a.day:
        import newsc_prepare as NP
        a.day = NP.prev_session_today()
    try:
        msg, rc, _ = run(a.day, a.newsc, a.notices, a.decisions)
    except Refuse as e:
        print(f'drops {a.day}: REFUSED - {e}'); sys.exit(2)
    print(msg); sys.exit(rc)
