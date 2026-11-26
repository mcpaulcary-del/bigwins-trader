"""Universe listing and resumable bulk download (EOD, splits, dividends) for one exchange."""
import os, sys, json, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import Client, BudgetExceeded, load_manifest, latest_raw

KINDS = {'eod': 'eod/{s}', 'splits': 'splits/{s}', 'div': 'div/{s}'}
EXTRA = ['AXJO.INDX']          # S&P/ASX 200 price index (replaces the stale XJO start)


def list_symbols(cli, exchange='AU', refresh=False):
    """Two calls (active, delisted). Returns the merged universe table and writes symbols.csv."""
    out = os.path.join(cli.store, 'symbols.csv')
    parts = []
    for dl in (0, 1):
        tag = f'{exchange}_delisted{dl}'
        js = None if refresh else latest_raw(cli.store, 'exchange-symbol-list', tag)
        if js is None:
            code, js = cli.get(f'exchange-symbol-list/{exchange}', {'delisted': dl}, 'exchange-symbol-list', tag)
            if code != 200:
                raise RuntimeError(f'symbol list {tag}: HTTP {code}')
        d = pd.DataFrame(js); d['delisted'] = dl; parts.append(d)
    u = pd.concat(parts, ignore_index=True)
    u['api_symbol'] = u.Code.astype(str) + '.' + exchange
    dup = u.duplicated('api_symbol', keep=False)
    u['in_both_lists'] = dup
    u = u.sort_values(['api_symbol', 'delisted']).drop_duplicates('api_symbol', keep='first')
    u.to_csv(out, index=False)
    return u


def done_set(store):
    m = load_manifest(store)
    # 200 = have it; 404 = EODHD has nothing for it (do not re-spend calls)
    m = m[m.http.isin(['200', '404'])]
    return set(zip(m.kind, m.symbol))


def estimate(n_symbols, kinds=('eod', 'splits', 'div'), per_min=300, sec_per_req=0.6, workers=4, mb_per_eod=0.12):
    calls = n_symbols * len(kinds) + 2
    rate = min(per_min / 60.0, workers / sec_per_req)
    return dict(symbols=n_symbols, calls=calls, share_of_daily_100k=calls / 100000,
                minutes=calls / rate / 60.0, approx_raw_mb_uncompressed=n_symbols * mb_per_eod)


def download(cli, symbols, kinds=('eod', 'splits', 'div'), workers=4, limit=None, log=print, refresh=False):
    have = set() if refresh else done_set(cli.store)
    tasks = [(k, s) for s in symbols for k in kinds if (k, s) not in have]
    if limit:
        tasks = tasks[:limit]
    log(f'{len(tasks)} requests to make ({len(have)} already done); budget left {cli.budget - cli.spent}')
    n = 0; t0 = time.time(); stop = threading.Event(); res = {}

    def one(k, s):
        if stop.is_set():
            return k, s, 'skipped'
        try:
            code, _ = cli.get(KINDS[k].format(s=s), {}, k, s)
            return k, s, code
        except BudgetExceeded as e:
            stop.set(); return k, s, 'budget'

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, k, s) for k, s in tasks]
        for f in as_completed(futs):
            k, s, code = f.result()
            res[str(code)] = res.get(str(code), 0) + 1
            n += 1
            if n % 250 == 0:
                el = time.time() - t0
                log(f'{n}/{len(tasks)} done in {el/60:.1f} min; status {res}; spent {cli.spent}')
    log(f'finished: {res}; calls spent this run {cli.spent}')
    return res
