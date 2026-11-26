# Hash-chained ledger helper for the Big Wins forward paper record (same format as bw13_snapshot.py entries).
import os, json, hashlib, time
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
REC = S + '/onedrive/research2/68_forward_record'
LED = REC + '/LEDGER.jsonl'

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def entries():
    if not os.path.exists(LED): return []
    return [json.loads(l) for l in open(LED) if l.strip()]

def verify():
    prev = '0' * 64
    for e in entries():
        x = dict(e); h = x.pop('entry_sha256')
        assert x['prev_entry_sha256'] == prev, ('chain broken at', e['seq'])
        assert hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest() == h, ('entry hash bad at', e['seq'])
        prev = h
    return prev

def append(**fields):
    prev = verify(); es = entries()
    e = dict(fields); e['seq'] = len(es) + 1; e['prev_entry_sha256'] = prev
    e.setdefault('recorded_utc', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    e['entry_sha256'] = hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()
    with open(LED, 'a') as f: f.write(json.dumps(e, sort_keys=True) + '\n')
    return e
