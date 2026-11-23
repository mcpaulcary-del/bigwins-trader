# Hash-chained ledger helper for the Big Wins forward paper record (same format as bw13_snapshot.py entries).
# Concurrency (preflight fix F2, ledger seq 84): verify + append run under an exclusive fcntl lock on LEDGER.jsonl.lock next to the ledger,
# so two jobs (daily, monthly multi-market, a record keeper) can never append on the same head and fork the chain; verify() alone takes
# the same lock shared, so it never reads a half-written line. Entry format and hashing are unchanged.
import os, json, hashlib, time, fcntl, contextlib
S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
REC = S + '/onedrive/research2/68_forward_record'
LED = REC + '/LEDGER.jsonl'

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def lock_path(): return LED + '.lock'                       # follows LED when a caller points LED elsewhere (tests, --ledger)

@contextlib.contextmanager
def locked(exclusive=True):
    """the ledger lock (blocking). Not re-entrant: never nest it in the same process."""
    with open(lock_path(), 'a') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try: yield
        finally: fcntl.flock(lk, fcntl.LOCK_UN)

def entries():
    if not os.path.exists(LED): return []
    return [json.loads(l) for l in open(LED) if l.strip()]

def _verify(es):
    prev = '0' * 64
    for e in es:
        x = dict(e); h = x.pop('entry_sha256')
        assert x['prev_entry_sha256'] == prev, ('chain broken at', e['seq'])
        assert hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest() == h, ('entry hash bad at', e['seq'])
        prev = h
    return prev

def verify():
    with locked(exclusive=False): return _verify(entries())

def append(**fields):
    with locked(exclusive=True):
        es = entries(); prev = _verify(es)
        e = dict(fields); e['seq'] = len(es) + 1; e['prev_entry_sha256'] = prev
        e.setdefault('recorded_utc', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        e['entry_sha256'] = hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()
        with open(LED, 'a') as f:
            f.write(json.dumps(e, sort_keys=True) + '\n'); f.flush(); os.fsync(f.fileno())
        return e
