# Fundamentals downloader (EODHD, 10 calls per file). Throttled: one file every 60/FPM seconds (default 28 files/min = 280 calls/min). Compact parse, resumable (data/fund/EX.pkl).
import sys, json, pickle, time, os, gzip, requests, numpy as np
B = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/improve5'; FPM = 28.0
IS = ['totalRevenue', 'grossProfit', 'costOfRevenue', 'operatingIncome', 'ebit', 'netIncome', 'incomeBeforeTax', 'interestExpense']
BS = ['totalAssets', 'totalStockholderEquity', 'totalLiab', 'shortLongTermDebtTotal', 'longTermDebt', 'cash', 'totalCurrentAssets', 'totalCurrentLiabilities', 'netReceivables', 'inventory', 'commonStockSharesOutstanding', 'goodWill', 'intangibleAssets']
CF = ['totalCashFromOperatingActivities', 'capitalExpenditures', 'dividendsPaid', 'freeCashFlow', 'salePurchaseOfStock', 'depreciation']
def f(v):
    try: return float(v)
    except (TypeError, ValueError): return np.nan
def parse(x):
    o = {}; g = x.get('General') or {}
    o['gen'] = {k: g.get(k) for k in ('Code', 'Name', 'Sector', 'Industry', 'GicSector', 'CurrencyCode', 'IsDelisted', 'ISIN', 'FiscalYearEnd', 'UpdatedAt', 'Type')}
    o['hl'] = dict(mcap=f((x.get('Highlights') or {}).get('MarketCapitalization')), shares=f((x.get('SharesStats') or {}).get('SharesOutstanding')), ma50=f((x.get('Technicals') or {}).get('50DayMA')))
    F = x.get('Financials') or {}
    for st, flds, key in (('Income_Statement', IS, 'is'), ('Balance_Sheet', BS, 'bs'), ('Cash_Flow', CF, 'cf')):
        for per in ('yearly', 'quarterly'):
            d = (F.get(st) or {}).get(per) or {}
            o[f'{key}_{per[0]}'] = [(k, (v or {}).get('filing_date'), (v or {}).get('currency_symbol')) + tuple(f((v or {}).get(q)) for q in flds) for k, v in sorted(d.items())]
    os_ = x.get('outstandingShares') or {}
    for per in ('annual', 'quarterly'):
        d = os_.get(per) or {}
        o[f'sh_{per[0]}'] = sorted((v.get('dateFormatted'), f(v.get('shares'))) for v in (d.values() if isinstance(d, dict) else d))
    h = ((x.get('Earnings') or {}).get('History')) or {}
    o['earn'] = sorted((k, v.get('reportDate'), f(v.get('epsActual'))) for k, v in h.items())
    return o
if __name__ == '__main__':
    names = json.load(open(B + '/data/fund/names100.json')); H = {'Authorization': 'Bearer proxy-injected'}; s = requests.Session(); ncall = 0
    for ex in sys.argv[1:]:
        path = B + f'/data/fund/{ex}.pkl'; res = pickle.load(open(path, 'rb')) if os.path.exists(path) else {}
        todo = [c for c in names[ex] if c not in res]; print(ex, 'todo', len(todo), flush=True); t0 = time.time(); nxt = time.time()
        for i, c in enumerate(todo):
            d = nxt - time.time()
            if d > 0: time.sleep(d)
            nxt = max(nxt, time.time()) + 60.0 / FPM; code = c.split('#')[0]
            try:
                r = s.get(f'https://eodhd.com/api/fundamentals/{code}.{ex}', params={'fmt': 'json'}, headers=H, timeout=120); ncall += 10
                if r.status_code == 200:
                    res[c] = parse(r.json()); rd = B + f'/data/fundamentals_raw/{ex}'; os.makedirs(rd, exist_ok=True)      # raw response kept (owner: never re-download)
                    with gzip.open(f'{rd}/{code}.{ex}.json.gz', 'wb') as g_: g_.write(r.content)
                    ip = B + '/data/fundamentals_raw/index.csv'; new_ = not os.path.exists(ip)
                    with open(ip, 'a') as fi:
                        if new_: fi.write('symbol,exchange,pack_column,downloaded_utc,bytes_raw,file\n')
                        fi.write(f"{code}.{ex},{ex},{c},{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},{len(r.content)},fundamentals_raw/{ex}/{code}.{ex}.json.gz\n")
                elif r.status_code == 404: res[c] = None
                elif r.status_code == 429: print('429 - sleeping 90 s', flush=True); time.sleep(90); continue
                else: res[c] = None; print(c, r.status_code, flush=True)
            except Exception as e: print(c, 'ERR', str(e)[:80], flush=True)
            if i % 50 == 49: pickle.dump(res, open(path, 'wb'), protocol=4); print(ex, i + 1, 'ok', sum(v is not None for v in res.values()), 'calls', ncall, round(time.time() - t0), flush=True)
        with open(B + '/PROGRESS.md', 'a') as fp: fp.write(f"- [fundamentals {time.strftime('%H:%M UTC', time.gmtime())}] {ex} COMPLETE: {len(res)} symbols asked, {sum(v is not None for v in res.values())} with data; raw gzip JSON in data/fundamentals_raw/{ex}/ (index: data/fundamentals_raw/index.csv); compact parse data/fund/{ex}.pkl; calls this run so far {ncall}.\n")
        pickle.dump(res, open(path, 'wb'), protocol=4); print('DONE', ex, len(res), 'with data', sum(v is not None for v in res.values()), 'calls so far', ncall, flush=True)
