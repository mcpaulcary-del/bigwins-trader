# Big Wins forward PAPER record -- open the account at the start decision day (amendment AMENDMENT_start_now.md).
# PAPER ONLY. Writes target lists and intended orders; the AI never places trades.
#   python3 -I paper_form.py            (run once, after fwd_download.py has completed for the decision day)
# Steps: build the forward panel -> Q4 data-block test on 16 Nov (fallback 13 Nov / fills 16 Nov) -> Q2 snapshot + ledger entry ->
# books formed at the start review (C3-C8) -> CSVs -> ledger entry "paper account opened; orders for <fill day> close".
import os, sys, json, math, time
import numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins_forward/code')
import paper_lib as P, fwd_ledger as L, fwd_download

def main():
    assert not os.path.exists(P.STATE), 'account already opened (state exists); paper_form.py runs once'
    log = lambda *a: print(time.strftime('%H:%M:%S'), *a, flush=True)
    pan = fwd_download.run(download=False, log=log)
    dl_end = str(pan[pan.symbol == 'AXJO.INDX'].date.max().date()) if (pan.symbol == 'AXJO.INDX').any() else str(pan.date.max().date())
    log('file as downloaded ends', dl_end)
    dec_day, fill = P.START_DECISION, P.START_FILL
    if dl_end < dec_day:
        q4 = dict(axjo_row=False, note=f'file ends {dl_end}'); blocked = True; dec = None
    else:
        dec, man, msha = P.build_decision(dec_day, dl_end, log=log); q4 = dec['q4']; blocked = q4['blocked']
    log('Q4 test on', dec_day, q4)
    if blocked:
        dec_day, fill = P.FALLBACK_DECISION, P.FALLBACK_FILL
        dec, man, msha = P.build_decision(dec_day, dl_end, log=log)
    e1 = L.append(asof=dec_day, kind='start review (decision day, amendment)', event=f'Q2 snapshot at {dec_day} on file downloaded to {dl_end}; Q4 test on {P.START_DECISION}: ' +
                  ('BW_DATA_BLOCK -> fallback decision 13 Nov / fills 16 Nov' if blocked else 'passed'),
                  q4_test=q4, manifest=dec['manifest'], manifest_sha256=dec['manifest_sha256'], scores_sha256=dec['scores_sha256'], rules_sha256=P.RULES_SHA)
    log('ledger', e1['seq'], e1['entry_sha256'])

    rows = dec['rows']; ranks = dec['ranks']
    books = [P.new_book('H82_lifecycle_5k', 'h82', 5000, contrib=500, start=dec_day), P.new_book('H82_25k', 'h82', 25000, start=dec_day),
             P.new_book('H82_100k', 'h82', 100000, start=dec_day),
             P.new_book('MOM_25k', 'momentum', 25000, n_fixed=10, start=dec_day), P.new_book('MOM_100k', 'momentum', 100000, n_fixed=10, start=dec_day)]
    for cap in (25000, 100000):
        for sd in range(1, P.NSEEDS + 1):
            books.append(P.new_book(f'RND_{cap // 1000}k_s{sd:03d}', 'random', cap, seed=sd, start=dec_day))
    cmps = []
    for cap, con, tag in ((5000, 500, 'lifecycle_5k'), (25000, 0, '25k'), (100000, 0, '100k')):
        cmps.append(P.new_cmp(f'CMP_A200_{tag}', {'A200.AU': 1.0}, cap, con, start=dec_day))
        cmps.append(P.new_cmp(f'CMP_4060_{tag}', {'A200.AU': 0.4, 'BGBL.AU': 0.6}, cap, con, start=dec_day))
    window_end = next(x for x in P.sessions() if x > dec_day and P.is_month_end(x))
    for b in books:
        P.decide(b, dec, dec_day, {}, fill, window_end, log)
    for c in cmps:
        c['pending'].append(dict(date=fill, amount=c['capital'], reason='initial (J3)'))
        c['nav'][dec_day] = c['capital']
    for b in books: b['nav'][dec_day] = b['capital']
    # 'last' prices at the decision day from the snapshot rows (raw close on the day, else close10) + ETFs
    last = {r['code']: dict(p=(r['rawclose'] or r['close10']), d=dec_day) for r in rows if (r['rawclose'] or r['close10'])}
    etf = pd.read_pickle(P.STORE + '/etf_tr.pkl'); etf = etf[etf.date <= dec_day]
    for s in P.ETF:
        x = etf[etf.symbol == s].iloc[-1]; last[s[:-3]] = dict(p=float(x.close), d=str(x.date.date()))
    st = dict(record='Big Wins forward paper record (PAPER ONLY)', rules_sha256=P.RULES_SHA, start_decision=dec_day, fill_day=fill,
              last_processed=dec_day, decisions=[dec_day], ranks=ranks, last=last, books=books, cmps=cmps, flags={}, data_blocks=[],
              challenger_placeholder='Improved challenger engine (report 73): added only after its rules are frozen and hashed, with its own start date and clock.')
    ssha = P.save_state(st)
    # ---------------- CSV outputs
    os.makedirs(P.PAPER, exist_ok=True); files = {}
    ref = {r['code']: r for r in rows}
    trows = []; orows = []
    for b in books[:3]:
        for k, o in enumerate([o for o in b['orders'] if o['type'] == 'buy'], 1):
            r = ref[o['code']]; px = r['rawclose'] or r['close10']; h = P.half_spread(ranks.get(o['cid']), px)
            sh = int(math.floor((o['amount'] - P.brokerage(o['amount'])) / (px * (1 + h))))
            trows.append(dict(book=b['id'], list_pos=k, code=o['code'], name=r['name'], industry_group=r['sector'] or 'unknown', score=round(r['score'], 6),
                              tv_rank=r['vrank'], n=b['n'], target_AUD=round(o['amount'], 2)))
            orows.append(dict(book=b['id'], side='BUY', code=o['code'], name=r['name'], amount_AUD=round(o['amount'], 2), reference_close=px,
                              reference_date=dec_day, half_spread=round(h, 5), est_brokerage=round(P.brokerage(o['amount']), 2), indicative_shares=sh,
                              fill='close of ' + fill, rule='C8 (start review)'))
    for c in cmps:
        for f, w in c['weights'].items():
            amt = c['capital'] * w; px = last[f[:-3]]['p']
            orows.append(dict(book=c['id'], side='BUY', code=f[:-3], name=f[:-3] + ' ETF', amount_AUD=round(amt, 2), reference_close=px, reference_date=last[f[:-3]]['d'],
                              half_spread=0.0003, est_brokerage=round(P.brokerage(amt), 2), indicative_shares=round((amt - P.brokerage(amt)) / 1.0003 / px, 4),
                              fill='close of ' + fill, rule='J3 comparator (fractional units)'))
    crow = []
    for b in books[3:]:
        for k, o in enumerate([o for o in b['orders'] if o['type'] == 'buy'], 1):
            crow.append(dict(book=b['id'], kind=b['kind'], seed=b['seed'], n=b['n'], list_pos=k, code=o['code'], target_AUD=round(o['amount'], 2)))
    files[f'paper/targets_{dec_day}.csv'] = P.write_csv(f'{P.PAPER}/targets_{dec_day}.csv', pd.DataFrame(trows))
    files[f'paper/orders_for_{fill}_close.csv'] = P.write_csv(f'{P.PAPER}/orders_for_{fill}_close.csv', pd.DataFrame(orows))
    files[f'paper/controls_targets_{dec_day}.csv'] = P.write_csv(f'{P.PAPER}/controls_targets_{dec_day}.csv', pd.DataFrame(crow))
    md = [f'# Paper books opened {dec_day} (fills at the close of {fill})', '', P.HEADER, '',
          '| Book | Capital | Contributions | n | T (A$) | Names |', '|---|---|---|---|---|---|']
    for b in books[:5]:
        md.append(f"| {b['id']} | A${b['capital']:,.0f} | {'A$500 each month-end' if b['contrib'] else 'none'} | {b['n']} | {b['T']:,.2f} | "
                  + ', '.join(o['code'] for o in b['orders'] if o['type'] == 'buy') + ' |')
    md.append(f'| RND_25k / RND_100k (seeds 1-200) | A$25,000 / A$100,000 | none | as H82 | as H82 | see controls_targets_{dec_day}.csv |')
    for c in cmps:
        md.append(f"| {c['id']} | A${c['capital']:,.0f} | {'A$500 each month-end' if c['contrib'] else 'none'} | - | - | "
                  + ' / '.join(f'{f[:-3]} {w:.0%}' for f, w in c['weights'].items()) + ' (EODHD A200.AU/BGBL.AU + distributions; flagged EODHD proxy) |')
    md.append('| Improved challenger (report 73) | placeholder | - | - | - | added only after its rules are frozen and hashed; no rules assumed |')
    md += ['', 'Lifecycle book: contributions are cash; spent only by v1.3 machinery (C9 vacancies, C8/C7 at reviews, D2 attempts). n=4 at A$5,000; n recomputed only at reviews.',
           'Data-block test (Q4): ' + json.dumps(q4)]
    open(f'{P.PAPER}/BOOKS_{dec_day}.md', 'w').write('\n'.join(md) + '\n'); files[f'paper/BOOKS_{dec_day}.md'] = L.sha(f'{P.PAPER}/BOOKS_{dec_day}.md')
    e2 = L.append(asof=dec_day, kind='paper account opened', event=f'paper account opened; orders for {fill} close', fill_day=fill, state_sha256=ssha,
                  files_sha256=files, books=len(books), comparators=len(cmps), rules_sha256=P.RULES_SHA,
                  h82_lists={b['id']: [[o['code'], round(o['amount'], 2)] for o in b['orders'] if o['type'] == 'buy'] for b in books[:3]})
    log('ledger', e2['seq'], e2['entry_sha256'])
    for b in books[:5]: log(b['id'], b['n'], round(b['T'], 2), [o['code'] for o in b['orders'] if o['type'] == 'buy'])

if __name__ == '__main__':
    main()
