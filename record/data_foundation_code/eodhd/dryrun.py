"""Dry run: exercises listing, download, manifest, resume and the TR build without a paid key.
  * AU endpoints are served from mocked fixtures (tests/fixtures), because the public demo key
    returns HTTP 403 for AU symbols and for exchange-symbol-list;
  * if network is available, 3 public demo calls (AAPL.US eod/splits/div, api_token=demo,
    which EODHD documents as permitted) are made through the real client.
Store: out/eodhd_dryrun (recreated each run)."""
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from client import Client
import download as DL, build_tr

FIX = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tests', 'fixtures')
STORE = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'out', 'eodhd_dryrun')


class _Resp:
    def __init__(self, code, body, headers=None):
        self.status_code = code; self.content = body; self.headers = headers or {'X-RateLimit-Limit': '1000', 'X-RateLimit-Remaining': '999'}


class MockSession:
    """Answers EODHD-shaped URLs from fixture files. Records every call (for tests)."""
    def __init__(self, fix=FIX):
        self.fix = fix; self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, dict(params or {}), dict(headers or {})))
        path = url.split('/api/', 1)[1]
        if path.startswith('exchange-symbol-list/'):
            fn = 'au_symbols_delisted.json' if str((params or {}).get('delisted', 0)) == '1' else 'au_symbols_active.json'
        elif path == 'user':
            return _Resp(200, json.dumps({'subscriptionType': 'mock', 'apiRequests': len(self.calls), 'dailyRateLimit': 100000}).encode())
        else:
            kind = path.split('/')[0]
            fn = f'{kind}_MOCK.json'
        fp = os.path.join(self.fix, fn)
        if not os.path.exists(fp):
            return _Resp(404, b'Ticker Not Found.')
        return _Resp(200, open(fp, 'rb').read())


def main(log=print, live_demo=True):
    if os.path.exists(STORE):
        for root, dirs, files in os.walk(STORE):
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        shutil.rmtree(STORE)
    cli = Client(STORE, per_min=600, daily_budget=100, auth_mode='header', token='placeholder-not-a-key', session=MockSession(), log=log)
    u = DL.list_symbols(cli)
    log(f'dryrun symbols: {len(u)}')
    syms = u.api_symbol.tolist()
    DL.download(cli, syms, workers=2, log=log)
    log('resume check (should make 0 requests):')
    DL.download(cli, syms, workers=2, log=log)
    if live_demo:
        try:
            demo = Client(STORE, per_min=30, daily_budget=3, auth_mode='query', token='demo', log=log)
            DL.download(demo, ['AAPL.US'], workers=1, log=log)
        except Exception as e:
            log('live demo skipped:', type(e).__name__, e)
    pan = build_tr.main(STORE, log=log)
    log(pan.groupby('symbol').agg(rows=('date', 'size'), first=('date', 'min'), last=('date', 'max'), tri_last=('tri', 'last')).to_string())
    return pan
