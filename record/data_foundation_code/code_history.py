"""Fix (a): ASX code-change history map and stitching.

Unit of analysis: a *segment* = one ASX code's contiguous run of price rows in the rs77 raw file
(a new segment starts after a gap of >200 calendar days, as in company_study stage 1), id 'CODE#k'.

A *link* says: segment A (old code) and segment B (new code) are the same listed security, B
continuing A. Evidence gathered for every candidate link, from independent sources:

  CL   ASX code/name change list 2001-2020 (rs77 company_details/changed_name, via company_db
       table name_changes): a row old->new dated within 45 days of B's first price.
  PX   price continuity in the raw file: B starts within 3 sessions of A's end, first close of B
       within 10% of last close of A (25% for 'weak'), turnover of similar size.
  AS   ASIC daily short-position files (2010-06 onwards, list every short-sellable product with its
       code, name and 'total product in issue'): around the change date the new code appears with
       the SAME total in issue as the old code (to 0.2%), optionally a similar name.
  SA   stockanalysis.com split-adjusted history matched on 40 overlapping closes (company_study
       stage 2, renames after the raw file ends in May 2024).

Sources used by company_study (CL in stage 1; PX-only 'auto links' in stage 2, outside 2001-2020;
SA in stage 2) are re-scored here, and the PX scan is re-run over the WHOLE 1997-2024 period.

Confidence
  high    two or more independent sources agree (e.g. CL+PX, AS+PX, CL+AS)
  medium  one documentary source (CL or AS) with prices consistent, or strict PX alone
          (gap <= 1 session, |ratio-1| <= 5%, turnover ratio within 1/3..3)
  low     anything weaker. Low links are NOT applied (listed for review), unless they were
          already applied by company_study, in which case they are kept and flagged.
One-to-one rule: a segment may have at most one successor and one predecessor. When two
predecessors claim the same successor (a merger, e.g. KYD+RRM -> DID in Jan 2000) only the best
supported one is applied and the other is listed as 'conflict'.
"""
import re, ast, os
from collections import defaultdict
import numpy as np, pandas as pd

GENERIC = set('LIMITED LTD ORDINARY ORD FPO FULLY PAID UNITS UNIT STAPLED SECURITIES SEC GROUP GRP. GRP HOLDINGS HLDGS HOLDING CORPORATION CORP CO NL THE AND OF TRUST FUND DEFERRED SETTLEMENT DEF SET CDI FOREIGN EXEMPT NEW PTY'.split())


def name_tokens(s):
    if not isinstance(s, str):
        return set()
    t = set(re.findall(r'[A-Z0-9]+', s.upper()))
    return {x for x in t if x not in GENERIC and len(x) > 1}


def name_sim(a, b):
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return np.nan
    return len(ta & tb) / len(ta | tb)


# ------------------------------------------------------------------ segments
def segments(s1):
    """s1: stage1-like rows with code, seg, date, c, v. Returns one row per original segment."""
    s1 = s1.sort_values(['code', 'seg', 'date'])
    s1 = s1.assign(orig=s1.code + '#' + s1.seg.astype(str))
    g = s1.groupby('orig', sort=False)
    seg = g.agg(code=('code', 'first'), first=('date', 'min'), last=('date', 'max'), n=('date', 'size'),
                c_first=('c', 'first'), c_last=('c', 'last'))
    seg['v_first'] = g.apply(lambda x: (x.c * x.v).iloc[:20].median(), include_groups=False)
    seg['v_last'] = g.apply(lambda x: (x.c * x.v).iloc[-20:].median(), include_groups=False)
    return seg


def chain_members(mapping, ids):
    """mapping old->new over ids; return dict final_id -> list of member ids (incl. itself)."""
    def res(e):
        k = 0
        while e in mapping and k < 20:
            e = mapping[e]; k += 1
        return e
    out = defaultdict(list)
    for e in ids:
        out[res(e)].append(e)
    return out, res


# ------------------------------------------------------------------ evidence
def px_evidence(seg, a, b, sess_pos):
    A, Bs = seg.loc[a], seg.loc[b]
    gap = sess_pos.get(Bs['first'], np.nan) - sess_pos.get(A['last'], np.nan)
    ratio = Bs.c_first / A.c_last if A.c_last > 0 else np.nan
    vr = (Bs.v_first + 1) / (A.v_last + 1) if np.isfinite(A.v_last) and np.isfinite(Bs.v_first) else np.nan
    return gap, ratio, vr


def px_grade(gap, ratio, vr, price=None):
    if not (np.isfinite(gap) and np.isfinite(ratio)):
        return 'none'
    if price is not None and price < 0.05:
        # below 5 cents one or two ticks is several per cent and many shells trade at the same
        # price: continuity is weak evidence there
        return 'weak' if gap <= 5 and abs(ratio - 1) <= 0.25 else 'none'
    if gap <= 1 and abs(ratio - 1) <= 0.05 and np.isfinite(vr) and 1 / 3 <= vr <= 3:
        return 'strict'
    if gap <= 3 and abs(ratio - 1) <= 0.10 and (not np.isfinite(vr) or 0.25 <= vr <= 4):
        return 'ok'
    if gap <= 5 and abs(ratio - 1) <= 0.25:
        return 'weak'
    return 'none'


class AsicIndex:
    """Fast lookups on the ASIC long table (code, total, name, date)."""
    def __init__(self, asic):
        a = asic[asic.total > 0][['code', 'total', 'name', 'date']].copy()
        self.first_date = a.date.min(); self.last_date = a.date.max()
        self.by_code = {c: g.sort_values('date') for c, g in a.groupby('code')}

    def window(self, code, d0, d1):
        g = self.by_code.get(code)
        if g is None:
            return None
        return g[(g.date >= d0) & (g.date <= d1)]

    def evidence(self, old, new, d, before=21, after=21):
        """Does `new` appear around date d with the same total in issue as `old` had just before d?"""
        d = pd.Timestamp(d)
        if d < self.first_date + pd.Timedelta(days=5) or d > self.last_date:
            return dict(as_cov=False, as_match=np.nan, as_name_sim=np.nan, as_date=pd.NaT, as_old_name=None, as_new_name=None)
        o = self.window(old, d - pd.Timedelta(days=before + 30), d + pd.Timedelta(days=3))
        n = self.window(new, d - pd.Timedelta(days=before), d + pd.Timedelta(days=after))
        if o is None or n is None or o.empty or n.empty:
            # one of the codes is not in the ASIC files (not short-sellable / not reported): no evidence either way
            return dict(as_cov=True, as_match=None, as_name_sim=np.nan, as_date=pd.NaT,
                        as_old_name=None if o is None or o.empty else o.name.iloc[-1],
                        as_new_name=None if n is None or n.empty else n.name.iloc[0])
        tot = o.total.iloc[-1]
        hit = n[(n.total - tot).abs() <= 0.002 * tot]
        return dict(as_cov=True, as_match=bool(len(hit)), as_name_sim=name_sim(o.name.iloc[-1], n.name.iloc[0]),
                    as_date=hit.date.iloc[0] if len(hit) else pd.NaT, as_old_name=o.name.iloc[-1], as_new_name=n.name.iloc[0])


def cl_evidence(cl, old, new, d, tol=45):
    x = cl[(cl.old_code == old) & (cl.new_code == new)]
    if x.empty:
        return False, pd.NaT, None
    dd = (x.change_date - pd.Timestamp(d)).abs()
    i = dd.idxmin()
    if dd[i] <= pd.Timedelta(days=tol):
        return True, x.change_date[i], x.new_name[i]
    return False, x.change_date[i], x.new_name[i]


def grade(row):
    px = row['px_grade']
    docs = int(bool(row['cl'])) + int(row['as_match'] is True)
    pxok = px in ('strict', 'ok')
    nsrc = docs + int(pxok) + int(bool(row.get('sa', False)))
    if row['as_match'] is False and not row['cl']:
        return 'low'          # both codes are in the ASIC files and their totals in issue differ
    if nsrc >= 2:
        return 'high'
    if docs >= 1 and px in ('strict', 'ok', 'weak'):
        return 'medium'
    if docs >= 1 and row['as_match'] is True:
        return 'medium'
    if px == 'strict':
        return 'medium'
    if row.get('sa', False):
        return 'medium'
    return 'low'


# ------------------------------------------------------------------ scan
def scan_candidates(seg, sess, d1_end, max_gap=3, lo=0.67, hi=1.5, min_rows=20, skip_start=5):
    """All (A,B) with B starting 1..max_gap sessions after A ends, different code, close ratio in [lo,hi].
    Both segments need >= min_rows rows; B may not start in the first `skip_start` sessions of the file
    (every code 'starts' there)."""
    pos = pd.Series(np.arange(len(sess)), index=sess)
    seg = seg.assign(p_first=seg['first'].map(pos), p_last=seg['last'].map(pos))
    seg = seg[seg.n >= min_rows]
    ends = seg[seg['last'] < d1_end - pd.Timedelta(days=5)]
    seg = seg[seg.p_first >= skip_start]
    starts = seg.groupby('p_first')
    out = []
    for a, r in ends.iterrows():
        for k in range(1, max_gap + 1):
            p = r.p_last + k
            if p not in starts.groups:
                continue
            for b, s in starts.get_group(p).iterrows():
                if s.code == r.code:
                    continue
                q = s.c_first / r.c_last if r.c_last > 0 else np.nan
                if lo <= q <= hi:
                    out.append((a, b))
    return out


def build_links(seg, sess, d1_end, cl, asic_idx, stage1_links, auto_links, stage1_eid_of_orig):
    """Return the scored edge table (one row per candidate link)."""
    pos = pd.Series(np.arange(len(sess)), index=sess)
    pos_d = pos.to_dict()
    cand = {}
    # stage1 change-list links are orig->orig
    for a, b in stage1_links.items():
        if a in seg.index and b in seg.index:
            cand.setdefault((a, b), set()).add('cs_stage1')
    # stage2 auto links are stage1-eid -> stage1-eid; convert to segments
    members = defaultdict(list)
    for o, e in stage1_eid_of_orig.items():
        members[e].append(o)
    for e, f in auto_links.items():
        if e not in members or f not in members:
            continue
        a = max(members[e], key=lambda o: seg.loc[o, 'last'])
        b = min(members[f], key=lambda o: seg.loc[o, 'first'])
        cand.setdefault((a, b), set()).add('cs_stage2_auto')
    for a, b in scan_candidates(seg, sess, d1_end):
        cand.setdefault((a, b), set()).add('scan')
    rows = []
    for (a, b), src in cand.items():
        A, Bs = seg.loc[a], seg.loc[b]
        gap, ratio, vr = px_evidence(seg, a, b, pos_d)
        clm, cld, cln = cl_evidence(cl, A.code, Bs.code, Bs['first'])
        ase = asic_idx.evidence(A.code, Bs.code, Bs['first']) if asic_idx is not None else dict(as_cov=False, as_match=np.nan, as_name_sim=np.nan, as_date=pd.NaT, as_old_name=None, as_new_name=None)
        r = dict(old_seg=a, new_seg=b, old_code=A.code, new_code=Bs.code, old_last=A['last'], new_first=Bs['first'],
                 old_close=A.c_last, new_close=Bs.c_first, gap_sessions=gap, close_ratio=ratio, turnover_ratio=vr,
                 px_grade=px_grade(gap, ratio, vr, min(A.c_last, Bs.c_first)), old_n=A.n, new_n=Bs.n, cl=clm, cl_date=cld, cl_new_name=cln, sa=False,
                 found_by='+'.join(sorted(src)), in_company_study=bool(src & {'cs_stage1', 'cs_stage2_auto'}))
        r.update(ase)
        r['as_match'] = (True if r['as_match'] is True else (False if r['as_match'] is False else None))
        r['confidence'] = grade(r)
        rows.append(r)
    E = pd.DataFrame(rows)
    return E


def resolve(E):
    """Apply confidence policy and the one-to-one rule. Adds 'applied' and 'status'."""
    E = E.copy()
    rank = {'high': 3, 'medium': 2, 'low': 1}
    pxr = {'strict': 3, 'ok': 2, 'weak': 1, 'none': 0}
    docs = E.cl.astype(bool).astype(int) + (E.as_match == True).astype(int)
    # documentary evidence outranks price continuity (several shells can open at the same price)
    E['score'] = E.confidence.map(rank) * 100 + docs * 10 + E.px_grade.map(pxr) - (E.close_ratio - 1).abs().fillna(1)
    tiny = (E.confidence == 'low') & (np.minimum(E.old_n, E.new_n) < 5)
    E['eligible'] = ((E.confidence != 'low') | E.in_company_study) & ~tiny
    E['status'] = np.where(E.eligible, 'candidate', np.where(tiny & E.in_company_study, 'rejected:tiny_segment_low_confidence', 'rejected:low_confidence'))
    E = E.sort_values('score', ascending=False)
    used_old, used_new = set(), set()
    applied = []
    for i, r in E.iterrows():
        if not r.eligible:
            applied.append(False); continue
        if r.old_seg in used_old or r.new_seg in used_new:
            applied.append(False); E.at[i, 'status'] = 'rejected:conflict(one-to-one)'; continue
        used_old.add(r.old_seg); used_new.add(r.new_seg); applied.append(True)
        E.at[i, 'status'] = 'applied' + (':flag_low_kept_from_company_study' if r.confidence == 'low' else '')
    E['applied'] = applied
    return E.sort_values(['new_first', 'old_seg']).reset_index(drop=True)


def final_ids(seg_ids, E, prefer):
    """Map every segment to its final entity id. The id of a chain is `prefer(chain_members)`
    (company_study's id when one exists), else the last segment's id."""
    m = {r.old_seg: r.new_seg for r in E[E.applied].itertuples()}
    members, res = chain_members(m, seg_ids)
    out = {}
    for last, mem in members.items():
        fid = prefer(mem, last)
        for o in mem:
            out[o] = fid
    return out


def parse_stage2_log(path):
    line = open(path).readline()
    auto = {a: b for a, b, _ in ast.literal_eval(line[line.index('['):])}
    sa = []
    for ln in open(path):
        m = re.match(r'renamed link (\S+) ->SA (\S+) (\d+) ([\d.]+)', ln)
        if m:
            sa.append((m.group(1), m.group(2), int(m.group(3)), float(m.group(4))))
    return auto, sa
