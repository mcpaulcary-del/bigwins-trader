"""Build the NEW cleaned ASX panel (v2). Originals are only read.  python3 -I code/build_panel_v2.py

Outputs (data_foundation/out):
  panel_v2_long.pkl            one row per (eid, date): code traded that day, raw OHLCV (to 2024-05-31),
                               adjusted price p, traded value, source and quality flags
  P_v2.pkl / Craw_v2.pkl / TV_v2.pkl   wide matrices on the clean calendar (adjusted, raw close, traded value)
  index_v2.pkl                 XJO / XTR on the clean calendar with forward-fill flags and NaN-ed clean columns
  calendar_dates.csv           every date seen in any source with its evidence and decision
  calendar_removed_rows.csv.gz every removed row (raw file, all codes; adjusted panel; index)
  calendar_missing_sessions.csv XASX sessions with no rows at all (market-wide gaps)
  code_links.csv               every candidate code link with evidence, confidence and status
  code_history_v2.csv          per entity: each code, first/last date, link confidence into it
  entity_map_v2.csv            original segment -> company_study eid -> v2 eid
  build_v2_log.json            counts used by README / report
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import *
import calendar_fix as CF
import code_history as CH
import quality_flags as FF

LOG = {}


def log(k, v):
    LOG[k] = v
    print(k, v if not isinstance(v, (dict, list)) or len(str(v)) < 300 else str(v)[:300])


def load_name_changes():
    import duckdb
    con = duckdb.connect(DB, read_only=True)
    cl = con.execute('select change_date, old_code, old_name, new_code, new_name from name_changes').df()
    con.close()
    cl['change_date'] = pd.to_datetime(cl.change_date, errors='coerce')
    cl = cl.dropna(subset=['change_date'])
    cl = cl[(cl.change_date > '1990-01-01')]
    for c in ('old_code', 'new_code'):
        cl[c] = cl[c].astype(str).str.strip().str.upper()
    return cl


def main(out=OUT):
    os.makedirs(out, exist_ok=True)
    ses = CF.xasx_sessions(CAL_START, CAL_END)
    # ------------------------------------------------------------------ (b) calendar
    raw = pd.read_pickle(os.path.join(CS_DATA, 'raw_all.pkl'))
    t_raw = CF.decide(CF.date_table(raw, ses))
    pl = pd.read_pickle(os.path.join(CS_DATA, 'panel_long.pkl'))
    t_pl = CF.decide(CF.date_table(pl.rename(columns={'p': 'c'}), ses, key='eid', cols=('c', 'val')))
    idx = pd.read_pickle(os.path.join(CS_DATA, 'index.pkl'))
    dates_all = sorted(set(t_raw.index) | set(t_pl.index) | set(idx.index))
    cal = pd.DataFrame(index=pd.DatetimeIndex(dates_all, name='date'))
    cal['weekday'] = cal.index.day_name()
    cal['xasx_open'] = cal.index.isin(ses)
    for nm, t in (('raw', t_raw), ('adj', t_pl)):
        cal[nm + '_rows'] = t.n.reindex(cal.index).fillna(0).astype(int)
        cal[nm + '_copy_share'] = t.copy_share.reindex(cal.index)
        cal[nm + '_action'] = t.action.reindex(cal.index).fillna('')
    cal['in_r55_list'] = cal.index.strftime('%Y-%m-%d').isin(CF.R55_HOLIDAY_COPIES + CF.R55_WEEKEND)
    cal['copy_day'] = t_raw.copy_day.reindex(cal.index).fillna(False).astype(bool)
    cal['copy_warn'] = t_raw.copy_warn.reindex(cal.index).fillna(False).astype(bool)
    # a date is removed from every source when XASX is closed and the source evidence agrees
    bad_dates = set(t_raw.index[t_raw.action.str.startswith('remove')]) | set(t_pl.index[t_pl.action.str.startswith('remove')])
    disagree = cal[(cal.raw_action.str.contains('DISAGREE')) | (cal.adj_action.str.contains('DISAGREE'))]
    cal['removed'] = cal.index.isin(bad_dates)
    cal['index_rows'] = cal.index.isin(idx.index)
    cal.to_csv(os.path.join(out, 'calendar_dates.csv'))
    rm_raw = raw[raw.date.isin(bad_dates)].assign(source='rs77 raw file (all codes)')
    rm_pl = pl[pl.date.isin(bad_dates)].assign(source='company_study panel_long (adjusted)')
    rm_ix = idx[idx.index.isin(bad_dates)].reset_index().assign(source='company_study index.pkl', code='XJO/XTR')
    rem = pd.concat([rm_raw[['source', 'code', 'date', 'o', 'h', 'l', 'c', 'v']],
                     rm_pl.rename(columns={'eid': 'code', 'p': 'c'})[['source', 'code', 'date', 'c', 'val']],
                     rm_ix[['source', 'code', 'date', 'xjo', 'xtr']]], ignore_index=True)
    rem = rem.merge(cal[['weekday', 'raw_action', 'adj_action']], left_on='date', right_index=True, how='left')
    rem.to_csv(os.path.join(out, 'calendar_removed_rows.csv.gz'), index=False)
    miss = CF.missing_sessions(t_raw.index[~t_raw.index.isin(bad_dates)], ses, raw.date.min(), D1_END)
    miss_adj = CF.missing_sessions(t_pl.index, ses, D1_END + pd.Timedelta(days=1), pl.date.max())
    pd.DataFrame({'date': list(miss) + list(miss_adj), 'source': ['rs77 raw file'] * len(miss) + ['adjusted panel after 2024-05'] * len(miss_adj)}).to_csv(os.path.join(out, 'calendar_missing_sessions.csv'), index=False)
    log('calendar', dict(dates_removed=len(bad_dates), removed_dates=sorted(str(d.date()) for d in bad_dates),
                         rows_removed_raw_all_codes=len(rm_raw), rows_removed_adjusted=len(rm_pl), rows_removed_index=len(rm_ix),
                         disagreements=[str(d.date()) for d in disagree.index], sessions_missing_raw=len(miss),
                         sessions_missing_adj_after_d1=len(miss_adj), vendor_copy_open_days=[str(d.date()) for d in cal.index[cal.copy_day]],
                         warn_copy_days=int(cal.copy_warn.sum()),
                         r55_list_all_removed=bool(all(pd.Timestamp(d) in bad_dates for d in CF.R55_HOLIDAY_COPIES + CF.R55_WEEKEND))))
    del raw
    # ------------------------------------------------------------------ (c) index forward fills
    ixv2 = FF.index_flags(idx[~idx.index.isin(bad_dates)])
    ixv2.to_pickle(os.path.join(out, 'index_v2.pkl'))
    runs = FF.ffill_runs(idx[~idx.index.isin(bad_dates)])
    runs.to_csv(os.path.join(out, 'index_ffill_runs.csv'), index=False)
    log('index_ffill', dict(runs=len(runs), days_flagged_xjo=int(ixv2.xjo_ffill.sum()), days_flagged_xtr=int(ixv2.xtr_ffill.sum()),
                            first_valid_xjo=str(ixv2.xjo.first_valid_index().date()), first_trusted_xjo=str(ixv2.xjo_clean.first_valid_index().date())))
    # ------------------------------------------------------------------ (a) code history
    s1 = pd.read_pickle(os.path.join(CS_DATA, 'stage1.pkl'))
    s1 = s1[~s1.date.isin(bad_dates)].copy()
    s1['orig'] = s1.code + '#' + s1.seg.astype(str)
    s1_eid = s1.groupby('orig').eid.first().to_dict()
    seg = CH.segments(s1)
    data_sess = pd.DatetimeIndex(sorted(s1.date.unique()))
    lk = pd.read_csv(os.path.join(CS_DATA, 'links.csv'), index_col=0).iloc[:, 0].to_dict()
    auto, sa_links = CH.parse_stage2_log(os.path.join(CS, 'out', 'stage2_log.txt'))
    def cs_res(e):
        k = 0
        while e in auto and k < 20:
            e = auto[e]; k += 1
        return e
    cs_final = {o: cs_res(s1_eid[o]) for o in seg.index}       # company_study eid of each segment
    cl = load_name_changes()
    asic = pd.read_pickle(os.path.join(FLAGS, 'out', 'asic_long.pkl'))
    AI = CH.AsicIndex(asic)
    E = CH.build_links(seg, data_sess, D1_END, cl, AI, lk, auto, s1_eid)
    E = CH.resolve(E)
    # old (company_study) links that the new map no longer applies
    E.to_csv(os.path.join(out, 'code_links.csv'), index=False)
    fid = CH.final_ids(list(seg.index), E, lambda mem, last: cs_final[last] if cs_final[last] in mem else last)
    emap = pd.DataFrame({'orig_segment': list(seg.index)})
    emap['code'] = seg.code.values
    emap['first'] = seg['first'].values; emap['last'] = seg['last'].values
    emap['cs_eid'] = emap.orig_segment.map(cs_final)
    emap['eid_v2'] = emap.orig_segment.map(fid)
    emap.to_csv(os.path.join(out, 'entity_map_v2.csv'), index=False)
    ap = E[E.applied]
    log('code_links', dict(candidates=len(E), applied=int(E.applied.sum()),
                           applied_by_conf=ap.confidence.value_counts().to_dict(),
                           applied_new_not_in_company_study=int((ap.applied & ~ap.in_company_study).sum()),
                           company_study_links_rejected=E[E.in_company_study & ~E.applied][['old_seg', 'new_seg', 'status']].values.tolist(),
                           rejected_low=int((E.status == 'rejected:low_confidence').sum()),
                           rejected_conflict=int(E.status.str.contains('conflict').sum()),
                           entities_cs=len(set(cs_final.values())), entities_v2=emap.eid_v2.nunique()))
    # post-D1 renames (stockanalysis match) checked against ASIC
    sa_rows = []
    sa_map = pd.read_csv(os.path.join(CS_DATA, 'sa_map.csv'), index_col=0).iloc[:, 0].to_dict()
    for e, c, n, sc in sa_links:
        old = e.split('#')[0]
        rec = dict(cs_eid=e, old_code=old, new_code=c, sa_overlap=n, sa_score=sc, same_code=(old == c))
        if old != c:
            g = AI.by_code.get(c)
            o = AI.by_code.get(old)
            # first ASIC date (after the raw file ends) on which the new code carries the old code's total
            rec.update(dict(as_change_date=pd.NaT, as_match=False, as_name_old=None, as_name_new=None))
            if g is not None and o is not None:
                g2 = g[g.date > D1_END - pd.Timedelta(days=30)]
                for d, tot, nm in g2[['date', 'total', 'name']].itertuples(index=False):
                    oo = o[(o.date <= d) & (o.date >= d - pd.Timedelta(days=30))]
                    if len(oo) and abs(oo.total.iloc[-1] - tot) <= 0.002 * tot:
                        rec.update(dict(as_change_date=d, as_match=True, as_name_old=oo.name.iloc[-1], as_name_new=nm)); break
                if not rec['as_match']:
                    rec.update(dict(as_name_old=o.name.iloc[-1], as_name_new=g2.name.iloc[0] if len(g2) else None))
            rec['confidence'] = 'high' if rec['as_match'] else ('medium' if sc >= 0.9 else 'low')
        else:
            rec['confidence'] = 'n/a (same code; stage-2 matched it as a rename only because the same-code test failed)'
        sa_rows.append(rec)
    SAL = pd.DataFrame(sa_rows)
    SAL.to_csv(os.path.join(out, 'code_links_post2024_stockanalysis.csv'), index=False)
    log('post2024_renames', SAL[['cs_eid', 'old_code', 'new_code', 'confidence']].values.tolist())
    # ------------------------------------------------------------------ assemble panel
    s1['eid'] = s1.orig.map(fid)
    s1['cs_eid'] = s1.orig.map(cs_final)
    pl = pl[~pl.date.isin(bad_dates)]
    bt = pd.read_csv(os.path.join(CS_DATA, 'bad_ticks.csv'), parse_dates=['date'])
    btk = set(zip(bt.eid.map(cs_res), bt.date))
    # rows sharing (cs_eid,date) inside company_study (two predecessors merged) -> adjusted price ambiguous
    dup = s1.duplicated(['cs_eid', 'date'], keep=False)
    d1 = s1[['eid', 'cs_eid', 'orig', 'code', 'date', 'o', 'h', 'l', 'c', 'v']].merge(
        pl[pl.date <= D1_END].rename(columns={'eid': 'cs_eid'}), on=['cs_eid', 'date'], how='left')
    d1['ambiguous_cs'] = dup.values
    d1['bad_tick'] = [(a, b) in btk for a, b in zip(d1.cs_eid, d1.date)]
    d1['src'] = 'D1'
    # post-D1 rows (stockanalysis), mapped to v2 eid
    post = pl[pl.date > D1_END].copy()
    cs2v2 = {}
    for o, f in fid.items():
        if cs_final[o] == o:
            cs2v2[o] = f
    post['cs_eid'] = post.eid
    post['eid'] = post.cs_eid.map(lambda e: cs2v2.get(e, e))
    post['code'] = post.cs_eid.map(lambda e: sa_map.get(e, e.split('#')[0]))
    # code before the ASIC-dated change for post-2024 renames
    for r in SAL[(~SAL.same_code) & SAL.as_match].itertuples():
        m = (post.cs_eid == r.cs_eid) & (post.date < r.as_change_date)
        post.loc[m, 'code'] = r.old_code
    post['src'] = 'SA'
    post['orig'] = None
    pan = pd.concat([d1, post], ignore_index=True).sort_values(['eid', 'date']).reset_index(drop=True)
    pan = FF.stitch_adjusted(pan)
    pan = FF.row_flags(pan, copy_days=list(cal.index[cal.copy_day]))
    pan.to_pickle(os.path.join(out, 'panel_v2_long.pkl'))
    # wide matrices
    Pw = pan.pivot(index='date', columns='eid', values='p').astype('float64')
    Pw.to_pickle(os.path.join(out, 'P_v2.pkl'))
    d1p = pan[pan.src == 'D1']
    Cw = d1p.pivot(index='date', columns='eid', values='c').reindex(index=Pw.index, columns=Pw.columns)
    Cw.astype('float32').to_pickle(os.path.join(out, 'Craw_v2.pkl'))
    TVw = (d1p.assign(tv=d1p.c * d1p.v)).pivot(index='date', columns='eid', values='tv').reindex(index=Pw.index, columns=Pw.columns)
    TVw.astype('float32').to_pickle(os.path.join(out, 'TV_v2.pkl'))
    # code history table per v2 entity
    ch = pan.groupby(['eid', 'code']).agg(first_date=('date', 'min'), last_date=('date', 'max'), n_days=('date', 'size'), src=('src', lambda s: '+'.join(sorted(set(s))))).reset_index().sort_values(['eid', 'first_date'])
    inc = ap.assign(eid=ap.new_seg.map(fid))[['eid', 'new_code', 'old_code', 'confidence', 'found_by', 'cl', 'as_match', 'px_grade']]
    ch = ch.merge(inc.rename(columns={'new_code': 'code', 'confidence': 'link_confidence', 'old_code': 'from_code'}), on=['eid', 'code'], how='left')
    ch.to_csv(os.path.join(out, 'code_history_v2.csv'), index=False)
    log('panel', dict(rows=len(pan), entities=pan.eid.nunique(), first=str(pan.date.min().date()), last=str(pan.date.max().date()),
                      d1_rows=int((pan.src == 'D1').sum()), sa_rows=int((pan.src == 'SA').sum())))
    save_json(LOG, os.path.join(out, 'build_v2_log.json'))
    return pan


if __name__ == '__main__':
    main()
