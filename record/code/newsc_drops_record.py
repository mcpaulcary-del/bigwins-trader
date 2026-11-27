# NEWS-C big-drop log, step 2: validate the blinded rater's cause labels and record the day. INFORMATION ONLY: feeds no paper
# line and no trade; never evidence for or against EMG2. Draft AMENDMENT_info_NEWSC_drops_v1.md.
#   python3 newsc_drops_record.py --day D --ratings-dir DIR --model MODEL_ID --model-source "how it was read" [--session-id ID]
#                                 [--subagent-model ALIAS] [--failures "text"] [--ledger PATH] [--newsc DIR] [--dry-run]
# DIR holds the raw rater replies drops_p1.json and drops_p2.json (not needed on a day whose dossier is empty).
# ONE ledger entry per session D, kind "info_drops" (separate from the day's "info_news" entry: different deadline - before the
# close of D+1, not 10:00 - and newsc_record.py, registered at seq 106, stays unchanged).
# Refuses (exit 2, nothing written) when: AMENDMENT_info_NEWSC_drops_v1.md is not registered in the ledger; DROPS_RUBRIC_v1.md or
# newsc_drops_classify.py does not hash to its frozen value; drops.jsonl does not hash to drops.sha256 / drops_manifest.json; the
# dossier (jsonl, rendered txt, blind copy) does not match the manifest or its re-rendering; a reply is missing, not JSON, names
# another rubric, dossier hash or pass, or breaks the schema (every item exactly once, cause T/F/U, a sub-cause of that cause,
# reason 1-20 words); or the day is already recorded (drops_labels.jsonl exists or the ledger has an info_drops entry for D).
# Two passes: a cause both passes agree on is kept; a disagreement keeps U (unclear). The sub-cause is kept when both agree,
# else MIXED. Events with no headline are labelled N (no news) without a rater.
# LATE: recorded at or after 16:00 Sydney on the first session after D (the close of D+1, the event's entry price): flagged, kept
# in the record, excluded from every reading.
# Writes newsc/<D>/: drops_rater/drops_p<k>.json (verbatim), drops_labels.jsonl, then the ledger entry via fwd_ledger.py.
import argparse, hashlib, json, os, re, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fwd_ledger as L
import newsc_drops as ND

NEWSC = ND.NEWSC
AMENDMENT = 'AMENDMENT_info_NEWSC_drops_v1.md'
SYD = ZoneInfo('Australia/Sydney')
REASON_MAX_WORDS = 20
CLOSE_SYD = (16, 0)
SUBS = {'T': {'T_EARN', 'T_MGMT', 'T_OPS', 'T_ONEOFF', 'T_SHORT', 'T_LEGAL', 'T_ANALYST', 'T_MACRO', 'T_BID'},
        'F': {'F_FRAUD', 'F_DILUTE', 'F_STRUCT', 'F_CONTRACT', 'F_PRODUCT', 'F_BAN', 'F_DEMAND'}, 'U': {'U'}}
RATER_NAME = {'T': 'temporary', 'F': 'fundamental', 'U': 'other-news', 'N': 'no-news'}


class Refuse(Exception): pass


def sha_file(p):
    with open(p, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def parse_reply(raw):
    t = raw.strip()
    if t.startswith('```'):
        t = re.sub(r'^```[a-zA-Z]*\s*\n', '', t); t = re.sub(r'\n?```\s*$', '', t)
    return json.loads(t)


def validate(reply, dsha, pas, ids):
    if not isinstance(reply, dict): raise Refuse(f'p{pas}: reply is not a JSON object')
    want = {'rubric', 'dossier_sha256', 'pass', 'model_self_report', 'labels'}
    if set(reply) != want: raise Refuse(f'p{pas}: keys {sorted(set(reply) ^ want)} wrong')
    if reply['rubric'] != ND.DROPS_RUBRIC_NAME: raise Refuse(f'p{pas}: rubric {reply["rubric"]!r}')
    if reply['dossier_sha256'] != dsha: raise Refuse(f'p{pas}: dossier_sha256 does not match the dossier')
    if reply['pass'] != pas or isinstance(reply['pass'], bool): raise Refuse(f'p{pas}: pass {reply["pass"]!r}')
    if not isinstance(reply['model_self_report'], str): raise Refuse(f'p{pas}: model_self_report not a string')
    if not isinstance(reply['labels'], list): raise Refuse(f'p{pas}: labels not a list')
    got = {}
    for r in reply['labels']:
        if not isinstance(r, dict) or set(r) != {'id', 'cause', 'sub', 'reason'}: raise Refuse(f'p{pas}: bad label entry {str(r)[:120]}')
        if r['id'] not in ids: raise Refuse(f"p{pas}: labels {r['id']!r} which is not in the dossier")
        if r['id'] in got: raise Refuse(f"p{pas}: labels {r['id']!r} twice")
        if r['cause'] not in SUBS: raise Refuse(f"p{pas}: {r['id']} cause {r['cause']!r} not T/F/U")
        if r['sub'] not in SUBS[r['cause']]: raise Refuse(f"p{pas}: {r['id']} sub-cause {r['sub']!r} not one of cause {r['cause']}")
        if not isinstance(r['reason'], str) or not 1 <= len(r['reason'].split()) <= REASON_MAX_WORDS:
            raise Refuse(f"p{pas}: {r['id']} reason must be 1-{REASON_MAX_WORDS} words")
        got[r['id']] = r
    miss = ids - set(got)
    if miss: raise Refuse(f'p{pas}: {len(miss)} items not labelled, e.g. {sorted(miss)[0]}')
    return got


def deadline_syd(day):
    """16:00 Sydney on the first ASX session after `day` (the close of D+1)"""
    try:
        nxt = ND.P.next_session(day)
    except Exception:
        x = datetime.fromisoformat(day) + timedelta(days=1)
        while x.weekday() >= 5: x += timedelta(days=1)
        nxt = str(x.date())
    return datetime.fromisoformat(f'{nxt}T{CLOSE_SYD[0]:02d}:{CLOSE_SYD[1]:02d}:00').replace(tzinfo=SYD)


def record(day, ratings_dir, model, model_source, session_id=None, subagent_model=None, failures=None, newsc=None,
           ledger=None, dry_run=False, now=None):
    newsc = newsc or NEWSC
    if ledger: L.LED = ledger
    od = f'{newsc}/{day}'
    es = L.entries(); L.verify()
    if not any(e.get('amendment') == AMENDMENT for e in es):
        raise Refuse(f'{AMENDMENT} is not registered in the ledger: nothing is recorded before registration')
    try: csha, rsha = ND.check_frozen(newsc)
    except ND.Refuse as e: raise Refuse(str(e))
    if os.path.exists(od + '/drops_labels.jsonl') or any(e.get('kind') == 'info_drops' and e.get('asof') == day for e in es):
        raise Refuse(f'{day} is already recorded')
    if not os.path.exists(od + '/drops.sha256'): raise Refuse(f'{day}: no drops.sha256 (newsc_drops.py not run)')
    with open(od + '/drops_manifest.json', 'rb') as f: mraw = f.read()
    man = json.loads(mraw)
    dsha = sha_file(od + '/drops.jsonl'); side = open(od + '/drops.sha256').read().split()[0]
    if not (dsha == side == man['drops_sha256']): raise Refuse(f'{day}: drops.jsonl hash {dsha} does not match drops.sha256 / manifest')
    with open(od + '/drops.jsonl') as f: ev = [json.loads(l) for l in f if l.strip()]
    with open(od + '/drops_dossier.jsonl', 'rb') as f: iraw = f.read()
    if sha_bytes(iraw) != man['dossier_jsonl_sha256']: raise Refuse(f'{day}: drops_dossier.jsonl hash does not match the manifest')
    items = [json.loads(l) for l in iraw.decode().splitlines() if l.strip()]
    txt = ND.render(items)
    if sha_bytes(txt) != man['dossier_txt_sha256']: raise Refuse(f'{day}: the dossier rendering does not match the manifest')
    if man['classifier_sha256'] != csha or man['rubric_sha256'] != rsha: raise Refuse(f'{day}: manifest classifier / rubric hash differs from the frozen files')
    if {e['id'] for e in ev if e['in_dossier']} != {it['id'] for it in items}: raise Refuse(f'{day}: dossier items do not match the events')
    ids = {it['id'] for it in items}; rated, outs = {}, {}
    if items:
        bp = f"{newsc}/{man['dossier_path']}"
        if not os.path.exists(bp) or open(bp, 'rb').read() != txt: raise Refuse(f"{day}: {man['dossier_path']} (what the rater read) is not the rendering of the dossier")
        for pas in (1, 2):
            rp = f'{ratings_dir}/drops_p{pas}.json'
            if not os.path.exists(rp): raise Refuse(f'{day}: missing rater reply drops_p{pas}.json')
            raw = open(rp, encoding='utf-8').read()
            try: reply = parse_reply(raw)
            except Exception as e: raise Refuse(f'{day}: drops_p{pas}.json is not valid JSON ({e})')
            rated[pas] = validate(reply, man['dossier_txt_sha256'], pas, ids)
            outs[f'drops_p{pas}.json'] = (raw.encode('utf-8'), reply.get('model_self_report'))
    rows = []
    for e in sorted(ev, key=lambda x: x['id']):
        r = dict(day=day, id=e['id'], code=e['code'], cid=e['cid'], cause_kw=e['cause_kw'], cause_kw_sub=e['cause_kw_sub'],
                 kw_class=e['kw']['cls'], xr=e['xr'], close_prev=e['close_prev'], in_dossier=e['in_dossier'])
        if e['in_dossier']:
            a, b = rated[1][e['id']], rated[2][e['id']]
            c = a['cause'] if a['cause'] == b['cause'] else 'U'
            sub = (a['sub'] if a['sub'] == b['sub'] else 'MIXED') if a['cause'] == b['cause'] else 'U'
            r.update(rater_p1=a['cause'], rater_p2=b['cause'], sub_p1=a['sub'], sub_p2=b['sub'], reason_p1=a['reason'],
                     reason_p2=b['reason'], rater=c, rater_sub=sub, agree=int(a['cause'] == b['cause']))
        else:
            r.update(rater='N', rater_sub='', agree=None)
        r['cause_rater'] = RATER_NAME[r['rater']]; r['model'] = model if e['in_dossier'] else None
        rows.append(r)
    ldata = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False) + '\n' for r in rows).encode()
    now = now or datetime.now(SYD)
    fails = [f for f in (failures or '').split(';') if f.strip()]
    fails += [w for w in man.get('warnings', []) if w.startswith('FAIL')]
    prev_models = [e.get('model', {}).get('reported_id') for e in es if e.get('kind') == 'info_drops' and e.get('model', {}).get('reported_id')]
    model_change = bool(items) and bool(prev_models) and prev_models[-1] != model
    if model_change: fails.append(f'MODEL CHANGE {prev_models[-1]} -> {model}: a new stratum; register a ledger entry')
    if len({m for _, m in outs.values()}) > 1: fails.append('rater self-reports differ between calls')
    on_time = now < deadline_syd(day)
    if not on_time: fails.append('LATE: recorded at or after the close of the session after D; this day is excluded from every reading')
    cnt = dict(events=len(rows), in_dossier=len(items),
               by_cause_kw={c: sum(1 for r in rows if r['cause_kw'] == c) for c in ND.CLASS_NAME.values()},
               by_cause_rater={c: sum(1 for r in rows if r['cause_rater'] == c) for c in RATER_NAME.values()},
               rater_disagreements=sum(1 for r in rows if r['agree'] == 0))
    entry = dict(kind='info_drops', asof=day,
                 event=f'NEWS-C big-drop causes for the ASX session {day} (information only; feeds no line; never evidence for or against EMG2)',
                 drops_sha256=dsha, drops_manifest_sha256=sha_bytes(mraw), dossier_jsonl_sha256=man['dossier_jsonl_sha256'],
                 dossier_txt_sha256=man['dossier_txt_sha256'], labels_sha256=sha_bytes(ldata),
                 rater_outputs_sha256={k: sha_bytes(v[0]) for k, v in sorted(outs.items())},
                 pool=man['pool'], bulk_sha256=man['bulk_sha256'], list_sha256=man['list_sha256'],
                 classifier_sha256=csha, rubric_sha256=rsha,
                 code_sha256={f: sha_file(os.path.join(HERE, f)) for f in ND.CODE_FILES if os.path.exists(os.path.join(HERE, f))},
                 model=dict(reported_id=(model if items else None), source=model_source, session_id=session_id, subagent_model=subagent_model,
                            self_reports=sorted({str(m) for _, m in outs.values()}),
                            settings='Claude Code subagent; default sampling; two independent passes' if items else 'no dossier: no rater',
                            model_change=model_change),
                 counts=cnt, failures=fails, on_time=on_time, deadline_sydney=deadline_syd(day).strftime('%Y-%m-%d %H:%M %Z'),
                 recorded_sydney=now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                 statement='Information only. Feeds no paper line and no trade; never evidence for or against EMG2; changes no line.')
    if dry_run: return entry
    os.makedirs(od + '/drops_rater', exist_ok=True)
    for k, (raw, _) in outs.items():
        with open(f'{od}/drops_rater/{k}.part', 'wb') as f: f.write(raw)
    with open(od + '/drops_labels.jsonl.part', 'wb') as f: f.write(ldata)
    e = L.append(**entry)
    for k in outs: os.replace(f'{od}/drops_rater/{k}.part', f'{od}/drops_rater/{k}')
    os.replace(od + '/drops_labels.jsonl.part', od + '/drops_labels.jsonl')
    return e


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True); ap.add_argument('--ratings-dir', required=True)
    ap.add_argument('--model', required=True); ap.add_argument('--model-source', required=True)
    ap.add_argument('--session-id'); ap.add_argument('--subagent-model'); ap.add_argument('--failures')
    ap.add_argument('--ledger'); ap.add_argument('--newsc'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    try:
        e = record(a.day, a.ratings_dir, a.model, a.model_source, a.session_id, a.subagent_model, a.failures, a.newsc, a.ledger, a.dry_run)
    except Refuse as ex:
        print('REFUSED:', ex); sys.exit(2)
    if a.dry_run: print(json.dumps(e, indent=1, sort_keys=True)); sys.exit(0)
    print(f"recorded drops {a.day}: ledger seq {e['seq']}; {e['counts']['events']} events; failures: {'; '.join(e['failures']) or 'none'}")
