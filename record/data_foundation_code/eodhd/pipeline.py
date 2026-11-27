"""EODHD ASX pipeline CLI.   python3 -I code/eodhd/pipeline.py <command> [options]

Commands
  user        show plan/usage (free call)
  symbols     list AU active + delisted symbols (2 calls) -> out/eodhd/symbols.csv
  estimate    call count / time estimate for the full download
  download    resumable bulk download of EOD, splits, dividends (+ AXJO.INDX)
  build       adjusted total-return panel from the raw files -> out/eodhd/panel_tr.pkl
  qa          QA against the v2 panel -> out/eodhd/qa/*
  dryrun      offline/demo run: public demo key on AAPL.US etc. + mocked AU fixtures into a temp store
  all         symbols, download, build, qa

Auth: see client.py (EODHD_AUTH_MODE=header|query, EODHD_API_TOKEN). Nothing is hard-coded.
"""
import os, sys, argparse, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from client import Client
import download as DL

DEF_STORE = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'out', 'eodhd')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('--store', default=DEF_STORE)
    ap.add_argument('--per-min', type=int, default=300, help='requests per minute (plan allows 1000)')
    ap.add_argument('--budget', type=int, default=90000, help='max API calls this run (plan: 100,000/day)')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--kinds', default='eod,splits,div')
    ap.add_argument('--symbols', default=None, help='comma list, e.g. BHP.AU,VAS.AU (default: whole universe)')
    ap.add_argument('--refresh', action='store_true', help='refetch even if already downloaded (new raw files; old ones kept)')
    a = ap.parse_args(argv)
    os.makedirs(a.store, exist_ok=True)
    logf = open(os.path.join(a.store, 'pipeline.log'), 'a')
    def log(*x):
        s = ' '.join(str(i) for i in x); print(s, flush=True); logf.write(s + '\n'); logf.flush()
    cli = Client(a.store, per_min=a.per_min, daily_budget=a.budget, log=log)
    if a.cmd == 'user':
        u = cli.user() or {}
        log({k: u.get(k) for k in ('subscriptionType', 'subscriptionMode', 'apiRequests', 'apiRequestsDate', 'dailyRateLimit')})
    if a.cmd in ('symbols', 'estimate', 'download', 'all'):
        u = DL.list_symbols(cli)
        log(f'symbols: {len(u)} (active {int((u.delisted == 0).sum())}, delisted {int((u.delisted == 1).sum())}); types {u.Type.value_counts().to_dict()}')
        log('estimate', json.dumps(DL.estimate(len(u) + len(DL.EXTRA), per_min=a.per_min, workers=a.workers)))
    if a.cmd in ('download', 'all'):
        u0 = cli.user() or {}
        log('usage before', {k: u0.get(k) for k in ('apiRequests', 'dailyRateLimit')})
        syms = a.symbols.split(',') if a.symbols else list(DL.EXTRA) + u.api_symbol.tolist()
        kinds = a.kinds.split(',')
        DL.download(cli, syms, kinds=[k for k in kinds], workers=a.workers, limit=a.limit, log=log, refresh=a.refresh)
        u1 = cli.user() or {}
        log('usage after', {k: u1.get(k) for k in ('apiRequests', 'dailyRateLimit')})
    if a.cmd in ('build', 'all'):
        import build_tr
        build_tr.main(a.store, log=log)
    if a.cmd in ('qa', 'all'):
        import qa
        qa.main(a.store, log=log)
    if a.cmd == 'dryrun':
        import dryrun
        dryrun.main(log=log)


if __name__ == '__main__':
    main()
