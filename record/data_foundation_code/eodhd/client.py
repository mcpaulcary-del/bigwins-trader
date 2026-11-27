"""EODHD HTTP client: auth without hard-coded keys, polite rate limiting, daily budget, retries,
append-only raw store and a manifest (URL without credentials, UTC time, HTTP status, SHA-256).

Auth (never hard-coded, never logged):
  EODHD_AUTH_MODE=header (default)  -> 'Authorization: Bearer $EODHD_API_TOKEN'
        In this cloud environment the proxy injects the real key; EODHD_API_TOKEN defaults to the
        placeholder 'proxy-injected', which is all this code ever sees.
  EODHD_AUTH_MODE=query             -> '?api_token=$EODHD_API_TOKEN' (owner's own machine, or 'demo')
"""
import os, time, json, gzip, hashlib, threading, datetime as dt
import urllib.parse
import requests

BASE = os.environ.get('EODHD_BASE', 'https://eodhd.com/api')
COST = {'eod': 1, 'splits': 1, 'div': 1, 'exchange-symbol-list': 1, 'user': 0, 'exchanges-list': 1}


class BudgetExceeded(RuntimeError):
    pass


def utcnow():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


class RateLimiter:
    """Token spacing: at most `per_min` requests per minute (evenly spaced), shared by threads.
    Also slows down when the server's X-RateLimit-Remaining gets low."""
    def __init__(self, per_min=300):
        self.interval = 60.0 / per_min
        self.lock = threading.Lock()
        self.next_t = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next_t)
            self.next_t = t + self.interval
        d = t - time.monotonic()
        if d > 0:
            time.sleep(d)

    def server_hint(self, remaining, limit):
        try:
            remaining = int(remaining); limit = int(limit)
        except (TypeError, ValueError):
            return
        if remaining < max(20, limit // 20):
            with self.lock:
                self.next_t = max(self.next_t, time.monotonic() + 15)


class Client:
    def __init__(self, store_dir, per_min=300, daily_budget=90000, auth_mode=None, token=None,
                 session=None, timeout=120, max_retries=5, log=print):
        self.store = store_dir
        os.makedirs(os.path.join(store_dir, 'raw'), exist_ok=True)
        self.manifest = os.path.join(store_dir, 'manifest.tsv')
        if not os.path.exists(self.manifest):
            with open(self.manifest, 'w') as f:
                f.write('utc\tkind\tsymbol\thttp\tcost\tbytes\tpayload_sha256\tfile\tfile_sha256\turl\n')
        self.mode = (auth_mode or os.environ.get('EODHD_AUTH_MODE', 'header')).lower()
        self._token = token if token is not None else os.environ.get('EODHD_API_TOKEN', 'proxy-injected')
        self.rl = RateLimiter(per_min)
        self.budget = daily_budget
        self.spent = 0
        self.s = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.mlock = threading.Lock()
        self.log = log

    # -- url building: the stored/printed URL never carries a credential
    def public_url(self, path, params):
        q = {k: v for k, v in params.items() if k != 'api_token'}
        return f'{BASE}/{path}' + ('?' + urllib.parse.urlencode(q) if q else '')

    def _auth(self, params):
        params = dict(params)
        headers = {'Accept': 'application/json', 'User-Agent': 'data-foundation-eodhd/1.0'}
        if self.mode == 'header':
            headers['Authorization'] = 'Bearer ' + self._token
        else:
            params['api_token'] = self._token
        return params, headers

    def get(self, path, params, kind, symbol, save=True):
        cost = COST.get(kind, 1)
        if self.spent + cost > self.budget:
            raise BudgetExceeded(f'daily budget {self.budget} reached')
        params = dict(params, fmt='json')
        url_pub = self.public_url(path, params)
        p2, headers = self._auth(params)
        for attempt in range(self.max_retries + 1):
            self.rl.wait()
            try:
                r = self.s.get(f'{BASE}/{path}', params=p2, headers=headers, timeout=self.timeout)
            except requests.RequestException as e:
                self.log(f'net error {kind} {symbol}: {type(e).__name__}; retry {attempt}')
                time.sleep(min(60, 2 ** attempt)); continue
            self.rl.server_hint(r.headers.get('X-RateLimit-Remaining'), r.headers.get('X-RateLimit-Limit'))
            if r.status_code == 429:
                wait = float(r.headers.get('Retry-After', 30)); self.log(f'429; sleeping {wait}s'); time.sleep(wait); continue
            if r.status_code == 402:
                raise BudgetExceeded('HTTP 402 from EODHD: daily limit spent')
            if r.status_code >= 500:
                time.sleep(min(60, 2 ** attempt)); continue
            break
        else:
            r = None
        if r is None:
            self._manifest(kind, symbol, 'ERR', cost, b'', None, url_pub)
            return None, None
        self.spent += cost
        body = r.content
        fpath = self._save(kind, symbol, body) if (save and r.status_code == 200) else None
        self._manifest(kind, symbol, r.status_code, cost, body, fpath, url_pub)
        if r.status_code != 200:
            return r.status_code, None
        try:
            return 200, json.loads(body)
        except ValueError:
            return 200, None

    def _save(self, kind, symbol, body):
        d = os.path.join(self.store, 'raw', kind)
        os.makedirs(d, exist_ok=True)
        ts = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        safe = symbol.replace('/', '_')
        fp = os.path.join(d, f'{safe}__{ts}.json.gz')
        # append-only: exclusive create, never overwrite an existing raw file
        with open(fp, 'xb') as f:
            f.write(gzip.compress(body, mtime=0))
        try:
            os.chmod(fp, 0o444)
        except OSError:
            pass
        return fp

    def _manifest(self, kind, symbol, http, cost, body, fpath, url_pub):
        psha = hashlib.sha256(body).hexdigest() if body else ''
        fsha = hashlib.sha256(open(fpath, 'rb').read()).hexdigest() if fpath else ''
        rel = os.path.relpath(fpath, self.store) if fpath else ''
        with self.mlock, open(self.manifest, 'a') as f:
            f.write(f'{utcnow()}\t{kind}\t{symbol}\t{http}\t{cost}\t{len(body)}\t{psha}\t{rel}\t{fsha}\t{url_pub}\n')

    def user(self):
        code, js = self.get('user', {}, 'user', '_user', save=False)
        return js


def load_manifest(store_dir):
    import pandas as pd
    p = os.path.join(store_dir, 'manifest.tsv')
    if not os.path.exists(p):
        return pd.DataFrame(columns=['utc', 'kind', 'symbol', 'http', 'cost', 'bytes', 'payload_sha256', 'file', 'file_sha256', 'url'])
    return pd.read_csv(p, sep='\t', dtype=str, keep_default_na=False)


def latest_raw(store_dir, kind, symbol):
    """Latest successful raw payload for (kind, symbol) from the manifest, parsed."""
    m = load_manifest(store_dir)
    m = m[(m.kind == kind) & (m.symbol == symbol) & (m.http == '200') & (m.file != '')]
    if m.empty:
        return None
    fp = os.path.join(store_dir, m.file.iloc[-1])
    return json.loads(gzip.decompress(open(fp, 'rb').read()))
