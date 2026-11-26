"""QA of the EODHD panel against the v2 panel (data_foundation/out). Writes out/eodhd/qa/*.

1. price agreement: EODHD raw close vs rs77 raw close on the same (code, date), 1997-2024-05
2. coverage of v2 entities (incl. dead/delisted ones) by delisting year
3. EODHD symbols with no v2 entity (e.g. delisted after the rs77 file ended in 2024-05)
4. dividends: VAS / A200 vs company_db dividends (stockanalysis) and the issuer reference file
5. index: AXJO.INDX vs company_study XJO, incl. the stale Nov-2000..2001 stretch
"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from common import OUT, DB, D1_END, md_table

ISSUER_REF = os.path.join(os.path.dirname(HERE), '..', 'tests', 'fixtures', 'issuer_distributions.csv')


def _row_agree(v2, ep, key, tol):
    """Join D1 rows to EODHD on (key, date); level and daily-return agreement per row."""
    e = ep[['code', 'date', 'close', 'volume']].rename(columns={'code': key})
    j = v2.merge(e, on=[key, 'date'], how='left').sort_values(['eid', 'date']).reset_index(drop=True)
    j['has'] = j.close.notna()
    with np.errstate(divide='ignore', invalid='ignore'):
        j['ldiff'] = np.abs(np.log(j.close / j.c))
    j['agree_level'] = j.has & (j.ldiff <= np.log1p(tol))
    # daily-return agreement on consecutive common rows (robust to EODHD back-adjusting `close`
    # for rights/bonus issues, which shifts levels by a constant factor before the event)
    g = j.groupby('eid')
    both = j.has & g.has.shift(1).fillna(False).astype(bool)
    with np.errstate(divide='ignore', invalid='ignore'):
        rd = np.abs(np.log((j.close / g.close.shift(1)) / (j.c / g.c.shift(1))))
    j['ret_cmp'] = both & rd.notna()
    j['ret_agree'] = j.ret_cmp & (rd <= 0.01)
    j['agree'] = j.agree_level | j.ret_agree
    return j


def entity_coverage(v2, ep, tol=0.02):
    """v2: D1 rows (eid, code, date, c). ep: EODHD rows (code, date, close).
    A row is covered when EODHD agrees under the code traded that day, or under the entity's
    LAST code (EODHD sometimes files a renamed company's whole history under its new code)."""
    v2 = v2.sort_values(['eid', 'date']).reset_index(drop=True)
    v2['lastcode'] = v2.groupby('eid').code.transform('last')
    j = _row_agree(v2, ep, 'code', tol)
    j2 = _row_agree(v2, ep, 'lastcode', tol)
    j['agree_via_lastcode'] = (~j.agree) & j2.agree.values & (v2.code.values != v2.lastcode.values)
    j['agree'] = j.agree | j.agree_via_lastcode
    ent = j.groupby('eid').agg(rows=('date', 'size'), first=('date', 'min'), last=('date', 'max'), codes=('code', lambda s: '/'.join(pd.unique(s))),
                               has=('has', 'mean'), agree=('agree', 'mean'), agree_level=('agree_level', 'mean'),
                               via_lastcode=('agree_via_lastcode', 'sum'),
                               ret_cmp=('ret_cmp', 'sum'), ret_agree=('ret_agree', 'sum'))
    ent['ret_agree_share'] = ent.ret_agree / ent.ret_cmp.where(ent.ret_cmp > 0)
    ent['cover'] = pd.cut(ent.agree, [-1, 0.1, 0.9, 2], labels=['none(<10%)', 'partial', 'full(>=90%)'])
    return j, ent


def main(store, log=print):
    qd = os.path.join(store, 'qa'); os.makedirs(qd, exist_ok=True)
    R = {}
    ep = pd.read_pickle(os.path.join(store, 'panel_tr.pkl'))
    sy = pd.read_csv(os.path.join(store, 'symbols.csv'), keep_default_na=False)
    ep_au = ep[ep.symbol.str.endswith('.AU')].copy()
    ep_au['code'] = ep_au.symbol.str[:-3]
    pan = pd.read_pickle(os.path.join(OUT, 'panel_v2_long.pkl'))
    v2 = pan[pan.src == 'D1'][['eid', 'code', 'date', 'c', 'v']]
    j, ent = entity_coverage(v2, ep_au)
    # 1. price agreement
    jj = j[j.has]
    yr = jj.groupby(jj.date.dt.year).agg(rows=('date', 'size'), level_within_1pct=('ldiff', lambda s: (s <= np.log(1.01)).mean()),
                                         level_within_2pct=('agree_level', 'mean'), median_abs_logdiff=('ldiff', 'median'),
                                         ret_compared=('ret_cmp', 'sum'), ret_within_1pct=('ret_agree', 'sum'))
    yr['ret_within_1pct'] = yr.ret_within_1pct / yr.ret_compared
    cov_rows = j.groupby(j.date.dt.year).has.mean().rename('v2_rows_with_eodhd_row')
    yr = yr.join(cov_rows)
    yr.to_csv(os.path.join(qd, 'price_agreement_by_year.csv'))
    R['price_agreement'] = dict(rows_compared=int(len(jj)), level_within_1pct=float((jj.ldiff <= np.log(1.01)).mean()),
                                level_within_2pct=float(jj.agree_level.mean()), returns_compared=int(jj.ret_cmp.sum()),
                                returns_within_1pct=float(jj.ret_agree.sum() / max(1, jj.ret_cmp.sum())),
                                v2_rows_with_eodhd=float(j.has.mean()), rows_agree_only_via_successor_code=int(j.agree_via_lastcode.sum()),
                                v2_rows_covered=float(j.agree.mean()))
    R['split_reconciliation'] = ep[ep.split_check != ''].split_check.str.replace(r'_[+-]\d+$', '', regex=True).value_counts().to_dict()
    # volume (EODHD volume is split-adjusted; compare only where agree on price)
    a = jj[jj.agree_level & (jj.v > 0)]
    R['volume_ratio_median'] = float((a.volume / a.v).median()) if len(a) else None
    # 2. coverage by delisting year
    ent['dead'] = ent['last'] < D1_END - pd.Timedelta(days=30)
    ent['delist_year'] = np.where(ent.dead, ent['last'].dt.year, 0)
    ent.to_csv(os.path.join(qd, 'entity_coverage.csv'))
    t = ent[ent.dead].groupby('delist_year').agg(dead_entities=('rows', 'size'),
                                                 full=('cover', lambda s: (s == 'full(>=90%)').sum()),
                                                 partial=('cover', lambda s: (s == 'partial').sum()),
                                                 none=('cover', lambda s: (s == 'none(<10%)').sum()))
    t['share_any'] = (t.full + t.partial) / t.dead_entities
    t['share_full'] = t.full / t.dead_entities
    t.to_csv(os.path.join(qd, 'delisted_coverage_by_year.csv'))
    alive = ent[~ent.dead]
    R['alive_entities'] = dict(n=int(len(alive)), full=int((alive.cover == 'full(>=90%)').sum()), partial=int((alive.cover == 'partial').sum()), none=int((alive.cover == 'none(<10%)').sum()))
    pre = ent[ent.dead & (ent['last'] < '2018-01-01')]
    post = ent[ent.dead & (ent['last'] >= '2018-01-01')]
    R['dead_pre2018'] = dict(n=int(len(pre)), any=float((pre.cover != 'none(<10%)').mean()), full=float((pre.cover == 'full(>=90%)').mean()))
    R['dead_2018_2024'] = dict(n=int(len(post)), any=float((post.cover != 'none(<10%)').mean()), full=float((post.cover == 'full(>=90%)').mean()))
    # 3. EODHD symbols vs the v2 universe
    st = ep.groupby('symbol').agg(first=('date', 'min'), last=('date', 'max'), rows=('date', 'size')).reset_index()
    st = st.merge(sy[['api_symbol', 'Type', 'delisted', 'Name']], left_on='symbol', right_on='api_symbol', how='left')
    st['code'] = st.symbol.str.replace('.AU', '', regex=False)
    matched_codes = set(j[j.agree].code)
    st['matched_v2'] = st.code.isin(matched_codes)
    st['last_year'] = st['last'].dt.year
    st.to_csv(os.path.join(qd, 'eodhd_symbol_table.csv'), index=False)
    dl = st[st.delisted == 1]
    R['eodhd_delisted'] = dict(listed=int((sy.delisted == 1).sum()), with_prices=int(len(dl)),
                               last_date_year_counts=dl.last_year.value_counts().sort_index().to_dict(),
                               first_date_min=str(dl['first'].min().date()) if len(dl) else None,
                               delisted_after_d1_end=int((dl['last'] > D1_END).sum()),
                               delisted_after_d1_common_stock=int(((dl['last'] > D1_END) & (dl.Type == 'Common Stock')).sum()))
    R['eodhd_rows_by_first_year'] = st.groupby(st['first'].dt.year).size().to_dict()
    sy_have = set(st.symbol)
    R['symbols_listed_without_eod'] = int((~sy.api_symbol.isin(sy_have)).sum())
    # 4. dividends VAS / A200
    dv_rows = []
    try:
        import duckdb
        con = duckdb.connect(DB, read_only=True)
        ref = con.execute("select code, ex_date, amount, source from dividends where code in ('VAS','A200')").df()
        con.close()
    except Exception as e:
        ref = pd.DataFrame(columns=['code', 'ex_date', 'amount', 'source']); log('dividend ref unavailable', e)
    ref['ex_date'] = pd.to_datetime(ref.ex_date)
    iss = pd.read_csv(ISSUER_REF, parse_dates=['ex_date']) if os.path.exists(ISSUER_REF) else pd.DataFrame(columns=['code', 'ex_date', 'amount'])
    for code in ('VAS', 'A200'):
        e = ep[(ep.symbol == code + '.AU') & (ep['div'] > 0)][['date', 'div']].rename(columns={'date': 'ex_date', 'div': 'eodhd'})
        r = ref[ref.code == code][['ex_date', 'amount']].rename(columns={'amount': 'company_db_stockanalysis'})
        i = iss[iss.code == code][['ex_date', 'amount']].rename(columns={'amount': 'issuer'})
        i['ex_date'] = pd.to_datetime(i.ex_date); r['ex_date'] = pd.to_datetime(r.ex_date)
        i['issuer'] = pd.to_numeric(i.issuer, errors='coerce')
        m = e.merge(r, on='ex_date', how='outer').merge(i, on='ex_date', how='outer').sort_values('ex_date')
        m.insert(0, 'code', code)
        dv_rows.append(m)
        both = m.dropna(subset=['eodhd', 'company_db_stockanalysis'])
        ib = m.dropna(subset=['eodhd', 'issuer'])
        R[f'div_{code}'] = dict(eodhd_n=int(m.eodhd.notna().sum()), ref_n=int(m.company_db_stockanalysis.notna().sum()), matched=int(len(both)),
                                max_abs_diff_vs_ref=float((both.eodhd - both.company_db_stockanalysis).abs().max()) if len(both) else None,
                                issuer_n=int(m.issuer.notna().sum()), max_abs_diff_vs_issuer=float((ib.eodhd - ib.issuer).abs().max()) if len(ib) else None,
                                eodhd_first=str(m[m.eodhd.notna()].ex_date.min().date()) if m.eodhd.notna().any() else None,
                                yearly_cash_eodhd=e.groupby(e.ex_date.dt.year).eodhd.sum().round(4).to_dict())
    pd.concat(dv_rows).to_csv(os.path.join(qd, 'dividends_VAS_A200.csv'), index=False)
    # TR sanity: VAS calendar-year TR vs price return
    for code in ('VAS', 'A200'):
        x = ep[ep.symbol == code + '.AU'].set_index('date')
        if len(x):
            y = x.groupby(x.index.year).agg(pr=('ret_pr', lambda s: (1 + s.fillna(0)).prod() - 1), tr=('ret_tr', lambda s: (1 + s.fillna(0)).prod() - 1))
            y['yield_gap'] = y.tr - y.pr
            y.to_csv(os.path.join(qd, f'tr_vs_pr_{code}.csv'))
            # cross-check own TR against EODHD adjusted_close
            ac = x.adj_close / x.adj_close.shift(1) - 1
            R[f'tr_vs_eodhd_adjclose_{code}'] = float((x.ret_tr - ac).abs().median())
    # 5. index
    ax = ep[ep.symbol == 'AXJO.INDX'].set_index('date')
    if len(ax):
        ix = pd.read_pickle(os.path.join(OUT, 'index_v2.pkl'))
        k = ix.join(ax[['close']], how='inner')
        ok = k[~k.xjo_ffill & k.xjo.notna()]
        R['axjo'] = dict(first=str(ax.index.min().date()), rows_compared=int(len(ok)),
                         median_abs_rel_diff=float((ok.close / ok.xjo - 1).abs().median()) if len(ok) else None,
                         share_within_0_1pct=float(((ok.close / ok.xjo - 1).abs() <= 0.001).mean()) if len(ok) else None,
                         close_2000_12_29=float(ax.close.get(pd.Timestamp('2000-12-29'), np.nan)),
                         stale_days_with_eodhd_value=int((k.xjo_ffill & k.close.notna()).sum()))
        k[k.xjo_ffill][['xjo', 'close']].rename(columns={'close': 'axjo_eodhd'}).to_csv(os.path.join(qd, 'xjo_stale_days_vs_eodhd.csv'))
    rp = os.path.join(store, 'build_removed_rows.csv')
    if os.path.exists(rp):
        rr = pd.read_csv(rp, parse_dates=['date'], usecols=['symbol', 'date'])
        rr['weekend'] = rr.date.dt.dayofweek >= 5
        R['eodhd_non_xasx_rows'] = dict(total=int(len(rr)), weekend=int(rr.weekend.sum()),
                                        by_year=rr.groupby(rr.date.dt.year).size().to_dict(),
                                        top_dates=rr.date.dt.strftime('%Y-%m-%d').value_counts().head(15).to_dict())
    with open(os.path.join(qd, 'qa_summary.json'), 'w') as f:
        json.dump(R, f, indent=2, default=str)
    log(json.dumps(R, indent=1, default=str)[:4000])
    return R
