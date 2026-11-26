# NEWS-C step 4: validate the rater's JSON and record the day. INFORMATION ONLY: feeds no paper line and no trade.
# Draft amendment AMENDMENT_info_NEWSC_v1.md s3, s5.
#   python3 newsc_record.py --day D --ratings-dir DIR --model MODEL_ID --model-source "how it was read" [--session-id ID]
#                           [--subagent-model ALIAS] [--failures "text"] [--ledger PATH] [--newsc DIR] [--dry-run]
# DIR holds the raw rater replies, one file per batch and pass: <batch>_p1.json and <batch>_p2.json (e.g. F_01_p2.json).
# Refuses (exit 2, nothing written) when: the NEWS-C amendment is not registered in the ledger; RUBRIC_v1.md does not hash to the
# registered value; input.jsonl does not hash to input.sha256 / manifest.json; a batch file does not hash to the manifest; a reply
# names another batch hash, pass or rubric; a reply is not valid JSON or breaks the schema (every announcement exactly once, rating
# an integer -2..2, type one of 14, reason 1-20 words); a batch or pass is missing; or the day is already recorded (ratings.jsonl
# exists or the ledger already has an info_news entry for the day).
# Writes newsc/<day>/: rater/<batch>_p<k>.json (verbatim copies), ratings.jsonl (one row per announcement and arm), codeday.jsonl
# (one row per code-day: both arms + baselines), then appends ONE ledger entry (kind "info_news") via fwd_ledger.py.
import argparse, hashlib, json, os, re, shutil, sys, time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fwd_ledger as L
import newsc_baselines as B
import newsc_prepare as NP

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
NEWSC = S + '/bigwins_forward/data/newsc'
RUBRIC_NAME = 'NEWSC_RUBRIC_v1'
RUBRIC_SHA256 = 'ed23cd805e4fd6b2d8483ba61e3b3e5cee829432dd418394d228527aa93ed680'                      # SHA-256 of newsc/RUBRIC_v1.md, as written in the amendment
AMENDMENT = 'AMENDMENT_info_NEWSC_v1.md'
SYD = ZoneInfo('Australia/Sydney')
CODE_FILES = ('info_archive.py', 'newsc_prepare.py', 'newsc_baselines.py', 'newsc_record.py', 'newsc_score.py')
REASON_MAX_WORDS = 20


class Refuse(Exception): pass


def sha_file(p):
    with open(p, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()


def sha_bytes(b): return hashlib.sha256(b).hexdigest()


def parse_reply(raw):
    """the reply must be one JSON object; a surrounding ``` fence is tolerated, nothing else"""
    t = raw.strip()
    if t.startswith('```'):
        t = re.sub(r'^```[a-zA-Z]*\s*\n', '', t); t = re.sub(r'\n?```\s*$', '', t)
    return json.loads(t)


def validate(reply, batch, bsha, pas, expect):
    """expect: {(item_id, ann_id)} of the batch. Returns {(item_id, ann_id): rating dict}."""
    if not isinstance(reply, dict): raise Refuse(f'{batch} p{pas}: reply is not a JSON object')
    want = {'rubric', 'batch', 'batch_sha256', 'pass', 'model_self_report', 'ratings'}
    if set(reply) != want: raise Refuse(f'{batch} p{pas}: keys {sorted(set(reply) ^ want)} wrong')
    if reply['rubric'] != RUBRIC_NAME: raise Refuse(f'{batch} p{pas}: rubric {reply["rubric"]!r}')
    if reply['batch'] != batch: raise Refuse(f'{batch} p{pas}: names batch {reply["batch"]!r}')
    if reply['batch_sha256'] != bsha: raise Refuse(f'{batch} p{pas}: batch_sha256 does not match the input (input hash mismatch)')
    if reply['pass'] != pas or isinstance(reply['pass'], bool): raise Refuse(f'{batch} p{pas}: pass {reply["pass"]!r}')
    if not isinstance(reply['model_self_report'], str): raise Refuse(f'{batch} p{pas}: model_self_report not a string')
    if not isinstance(reply['ratings'], list): raise Refuse(f'{batch} p{pas}: ratings not a list')
    got = {}
    for r in reply['ratings']:
        if not isinstance(r, dict) or set(r) != {'item_id', 'ann_id', 'type', 'rating', 'reason'}:
            raise Refuse(f'{batch} p{pas}: bad rating entry {str(r)[:120]}')
        k = (r['item_id'], r['ann_id'])
        if k not in expect: raise Refuse(f'{batch} p{pas}: rates {k} which is not in the batch')
        if k in got: raise Refuse(f'{batch} p{pas}: rates {k} twice')
        if not isinstance(r['rating'], int) or isinstance(r['rating'], bool) or not -2 <= r['rating'] <= 2:
            raise Refuse(f'{batch} p{pas}: {k} rating {r["rating"]!r} not an integer -2..2')
        if r['type'] not in B.TYPES: raise Refuse(f'{batch} p{pas}: {k} type {r["type"]!r} not one of the 14')
        if not isinstance(r['reason'], str) or not 1 <= len(r['reason'].split()) <= REASON_MAX_WORDS:
            raise Refuse(f'{batch} p{pas}: {k} reason must be 1-{REASON_MAX_WORDS} words')
        got[k] = r
    miss = expect - set(got)
    if miss: raise Refuse(f'{batch} p{pas}: {len(miss)} announcements not rated, e.g. {sorted(miss)[0]}')
    return got


def keep(r1, r2):
    """spec s3: disagreement recorded, the rating nearer neutral kept (equal distance, opposite signs -> 0)"""
    if r1 == r2: return r1
    if abs(r1) != abs(r2): return r1 if abs(r1) < abs(r2) else r2
    return 0


def next_open_syd(day):
    """10:00 Sydney on the first ASX session after `day` (exchange_calendars XASX; weekdays if unavailable)"""
    try:
        import exchange_calendars as xc
        s = xc.get_calendar('XASX', start=day, end=str((datetime.fromisoformat(day) + timedelta(days=20)).date())).sessions
        nxt = next(str(x.date()) for x in s if str(x.date()) > day)
    except Exception:
        x = datetime.fromisoformat(day) + timedelta(days=1)
        while x.weekday() >= 5: x += timedelta(days=1)
        nxt = str(x.date())
    return datetime.fromisoformat(nxt + 'T10:00:00').replace(tzinfo=SYD)


def record(day, ratings_dir, model, model_source, session_id=None, subagent_model=None, failures=None, newsc=None,
           ledger=None, dry_run=False, now=None):
    newsc = newsc or NEWSC
    if ledger: L.LED = ledger
    od = f'{newsc}/{day}'
    # --- registration, rubric, duplicate
    es = L.entries(); L.verify()
    if not any(e.get('amendment') == AMENDMENT for e in es):
        raise Refuse(f'{AMENDMENT} is not registered in the ledger: nothing is recorded before registration')
    rub = sha_file(f'{newsc}/RUBRIC_v1.md')
    if rub != RUBRIC_SHA256: raise Refuse(f'RUBRIC_v1.md hashes to {rub}, not the registered {RUBRIC_SHA256}')
    if os.path.exists(od + '/ratings.jsonl') or any(e.get('kind') == 'info_news' and e.get('asof') == day for e in es):
        raise Refuse(f'{day} is already recorded')
    # --- input hash
    if not os.path.exists(od + '/input.jsonl'): raise Refuse(f'{day}: no input.jsonl (prepare not run)')
    isha = sha_file(od + '/input.jsonl')
    side = open(od + '/input.sha256').read().split()[0]
    with open(od + '/manifest.json') as f: man = json.load(f)
    if not (isha == side == man['input_sha256']): raise Refuse(f'{day}: input.jsonl hash {isha} does not match input.sha256 / manifest')
    items = {}
    with open(od + '/input.jsonl') as f:
        for l in f:
            if l.strip(): it = json.loads(l); items[(it['item_id'], it['arm'])] = it
    # --- every batch, both passes
    rated, outs = {}, {}
    for b in man['batches']:
        bp = f"{od}/batches/{b['batch']}.jsonl"
        if sha_file(bp) != b['sha256']: raise Refuse(f"{day}: batch {b['batch']} hash does not match the manifest")
        with open(bp) as f: blines = [l for l in f.read().split('\n') if l]
        tp = f"{od}/batches/{b['batch']}.txt"
        if not os.path.exists(tp) or open(tp, 'rb').read() != NP.render(blines, b['batch']) or sha_file(tp) != b['txt_sha256']:
            raise Refuse(f"{day}: batch {b['batch']}.txt (what the rater read) is not the rendering of the batch")
        expect = set()
        with open(bp) as f:
            for l in f:
                it = json.loads(l)
                if items.get((it['item_id'], it['arm'])) != it: raise Refuse(f"{day}: batch {b['batch']} line not in input.jsonl")
                expect |= {(it['item_id'], a['ann_id']) for a in it['announcements']}
        for pas in (1, 2):
            rp = f"{ratings_dir}/{b['batch']}_p{pas}.json"
            if not os.path.exists(rp): raise Refuse(f"{day}: missing rater reply {b['batch']}_p{pas}.json")
            raw = open(rp, encoding='utf-8').read()
            try: reply = parse_reply(raw)
            except Exception as e: raise Refuse(f"{day}: {b['batch']}_p{pas}.json is not valid JSON ({e})")
            rated[(b['batch'], pas)] = validate(reply, b['batch'], b['sha256'], pas, expect)
            outs[f"{b['batch']}_p{pas}.json"] = (raw.encode('utf-8'), reply.get('model_self_report'))
    if items and not man['batches']: raise Refuse(f'{day}: items but no batches')
    # --- combine
    rows, cd = [], {}
    meta = {x['item_id']: x for x in man['items']}
    base = {}
    if os.path.exists(od + '/baselines.jsonl'):
        if sha_file(od + '/baselines.jsonl') != man['baselines_sha256']: raise Refuse(f'{day}: baselines.jsonl hash does not match the manifest')
        with open(od + '/baselines.jsonl') as f: base = {json.loads(l)['code']: json.loads(l) for l in f if l.strip()}
    for b in man['batches']:
        arm = b['arm']; p1, p2 = rated[(b['batch'], 1)], rated[(b['batch'], 2)]
        for k in sorted(p1):
            a, c = p1[k], p2[k]; iid, aid = k
            m = next((x for x in meta[iid]['announcements'] if x['ann_id'] == aid), {})
            rows.append(dict(day=day, item_id=iid, code=iid.split(':', 1)[1], arm=arm, ann_id=aid, batch=b['batch'],
                             rating_p1=a['rating'], rating_p2=c['rating'], rating=keep(a['rating'], c['rating']),
                             agree=int(a['rating'] == c['rating']), type_p1=a['type'], type_p2=c['type'],
                             reason_p1=a['reason'], reason_p2=c['reason'], text_available=int((m.get('text_chars') or 0) > 0),
                             key_type=(m.get('key') or [None, None])[0], key_rating=(m.get('key') or [None, None])[1]))
    for r in rows:
        x = cd.setdefault(r['item_id'], dict(day=day, item_id=r['item_id'], code=r['code'], group=meta[r['item_id']]['group'],
                                             n_announcements=meta[r['item_id']]['n_announcements'],
                                             missing_text=meta[r['item_id']]['missing_text'], _r={'H': [], 'F': []}, _d={'H': 0, 'F': 0}))
        x['_r'][r['arm']].append(r['rating']); x['_d'][r['arm']] += 1 - r['agree']
    cdrows = []
    for iid in sorted(cd):
        x = cd[iid]; r = x.pop('_r'); dg = x.pop('_d')
        x.update(rating_H=B.codeday_rating(r['H']), rating_F=B.codeday_rating(r['F']), disagree_H=dg['H'], disagree_F=dg['F'])
        bl = base.get(x['code'], {})
        for k in ('key_type', 'key_rating', 'RAISE', 'raise_today', 'HALT', 'halt_event_today', 'halted_end_of_day', 'DIR',
                  'dir_buys_today', 'window_complete'):
            x[k] = bl.get(k)
        x['model'] = model; cdrows.append(x)
    # --- write (.part), ledger, rename
    rdata = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False) + '\n' for r in rows).encode()
    cdata = ''.join(json.dumps(r, sort_keys=True, ensure_ascii=False) + '\n' for r in cdrows).encode()
    now = now or datetime.now(SYD)
    prev_models = [e.get('model', {}).get('reported_id') for e in es if e.get('kind') == 'info_news']
    fails = [f for f in (failures or '').split(';') if f.strip()]
    model_change = bool(prev_models) and prev_models[-1] != model
    if model_change: fails.append(f'MODEL CHANGE {prev_models[-1]} -> {model}: a new stratum; register a ledger entry (spec s3)')
    if len({m for _, m in outs.values()}) > 1: fails.append('rater self-reports differ between calls')
    on_time = now < next_open_syd(day)
    if not on_time: fails.append('LATE: recorded after the open of the next session; this day is excluded from every bar')
    cnt = dict(code_days=len(cdrows), announcements=len(rows) // 2 if rows else 0,
               by_group={g: sum(1 for x in cdrows if x['group'] == g) for g in ('C', 'H')},
               codeday_F={str(k): sum(1 for x in cdrows if x['rating_F'] == k) for k in (-2, -1, 0, 1, 2)},
               codeday_H={str(k): sum(1 for x in cdrows if x['rating_H'] == k) for k in (-2, -1, 0, 1, 2)},
               disagreements_F=sum(1 for r in rows if r['arm'] == 'F' and not r['agree']),
               disagreements_H=sum(1 for r in rows if r['arm'] == 'H' and not r['agree']),
               missing_text=man.get('n_missing_text', 0), batches=len(man['batches']))
    entry = dict(kind='info_news', asof=day,
                 event=f'NEWS-C ratings for the announcements of {day} (information only; feeds no line; never evidence for or against EMG2)',
                 list_sha256=man['list_sha256'], ps_state_sha256=man['ps_state_sha256'], input_sha256=isha,
                 manifest_sha256=sha_file(od + '/manifest.json'), batch_sha256={b['batch']: b['sha256'] for b in man['batches']},
                 batch_txt_sha256={b['batch']: b['txt_sha256'] for b in man['batches']},
                 rater_outputs_sha256={k: sha_bytes(v[0]) for k, v in sorted(outs.items())}, ratings_sha256=sha_bytes(rdata),
                 codeday_sha256=sha_bytes(cdata), baselines_sha256=man['baselines_sha256'], rubric_sha256=rub,
                 code_sha256={f: sha_file(os.path.join(HERE, f)) for f in CODE_FILES},
                 model=dict(reported_id=model, source=model_source, session_id=session_id, subagent_model=subagent_model,
                            self_reports=sorted({str(m) for _, m in outs.values()}),
                            settings='Claude Code subagent; default sampling (temperature not settable); two independent passes',
                            model_change=model_change),
                 counts=cnt, failures=fails, on_time_provisional=on_time, recorded_sydney=now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                 statement='Information only. Feeds no paper line and no trade; never evidence for or against EMG2; changes no line.')
    if dry_run: return entry
    os.makedirs(od + '/rater', exist_ok=True)
    for k, (raw, _) in outs.items():
        with open(f'{od}/rater/{k}.part', 'wb') as f: f.write(raw)
    for p, data in (('ratings.jsonl', rdata), ('codeday.jsonl', cdata)):
        with open(f'{od}/{p}.part', 'wb') as f: f.write(data)
    e = L.append(**entry)
    for k in outs: os.replace(f'{od}/rater/{k}.part', f'{od}/rater/{k}')
    os.replace(od + '/codeday.jsonl.part', od + '/codeday.jsonl')
    os.replace(od + '/ratings.jsonl.part', od + '/ratings.jsonl')
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
    print(f"recorded {a.day}: ledger seq {e['seq']}; {e['counts']['code_days']} code-days; failures: {'; '.join(e['failures']) or 'none'}")
