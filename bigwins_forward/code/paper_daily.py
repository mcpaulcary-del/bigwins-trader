# Big Wins forward PAPER record -- daily job (idempotent).  PAPER ONLY: no real money, no broker orders, the AI never places trades.
#   python3 -I paper_daily.py [--no-download] [--until YYYY-MM-DD]
# For every ASX trading day after the last processed one whose close EODHD has published:
#   1. bulk EOD closes, dividends and splits for that day (EODHD eod-bulk-last-day/AU), AXJO.INDX rows (A1 trading-day test);
#   2. books the day in D6 order per v1.3: splits (Q7), dividends (I1), sells (D1), buys on attempt days (D2), top-ups (D3);
#      comparators per J3 (A200.AU / BGBL.AU + distributions, flagged EODHD proxy);
#   3. at a month-end: A$500 contribution to the lifecycle book and its comparators (before C2), full EODHD refresh (Q1),
#      Q2 snapshot, Q4 data-block test, C2-C9 decisions (December month-end = review, C3; trades on the next trading day);
#   4. Q6 flags (no close for 20 trading days: carried at last close, second NAV at 70%);
#   5. NAV of every book and comparator, scorecard CSV + markdown, hash-chained ledger entry.
# Safe to run as often as wanted: a day is booked once (state.last_processed); a re-run only refreshes the scorecard.
import os, sys, json, math, time, argparse, fcntl, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins_forward/code')
import paper_lib as P, fwd_ledger as L, paper_shadow as SH, paper_score as PS, paper_accum as AC, paper_cxl as CX
import paper_emg2 as EM, paper_early as EA     # SHADOW EMG2 (AMENDMENT_shadow_EMG2.md) and SHADOW EARLY (AMENDMENT_shadow_EARLY.md)
import paper_emg2s as ES                        # PAPER twins of live EMG2-18: H6, COMBO, REF (AMENDMENT_shadow_EMG2_18_H6.md, AMENDMENT_shadow_EMG2_COMBO.md)
import paper_emg2bt as BT                        # PAPER line EMG2_18_SIM_BT, EMG2-18 + band-trend switch into A200 (AMENDMENT_shadow_EMG2_18_BT.md)
import paper_emg2bt6 as BT6                      # PAPER line EMG2_18_SIM_BT_C6, the same + sell rule C6 (AMENDMENT_shadow_EMG2_18_BT_C6.md)
import paper_blind3 as B3                        # PAPER line BLIND3, blind build 3 frozen primary (AMENDMENT_shadow_BLIND3.md)
import paper_pair as PR                          # PAPER line PAIR, EMG2-18 + BLIND3 in one A$10,000 account (AMENDMENT_shadow_PAIR.md)
import paper_sidelines as SL                     # side lines SWEEP / WIDE / FIP (AMENDMENT_shadow_sidelines_v1.md; information only)
import paper_info_c as IC                        # information readings EST-C / DIL-C on band C (AMENDMENT_shadow_sidelines_v1.md; no trades)
import paper_moon as MO                          # aggressive side lines MOON_TOP5 / MOON_NOLOT5 / MOON_LEG2 (AMENDMENT_shadow_moon_v1.md; information only)

LOGF = P.FW + '/out/logs/paper_daily.log'

def log(*a):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + ' '.join(str(x) for x in a)
    print(s, flush=True); open(LOGF, 'a').write(s + '\n')


def q6_flags(st, d):
    """holdings whose last close is 20+ trading days before d"""
    held = {h['code'] for b in st['books'] for h in b['holdings'].values()}
    flags = {}
    for c in held:
        lc = st['last'].get(c, {}).get('d')
        if lc is None: flags[c] = dict(last_close_date=None, sessions_without_close=None); continue
        k = len(P.sessions_between(lc, d))
        if k >= 20: flags[c] = dict(last_close_date=lc, sessions_without_close=k)
    return flags


def twr(b, nav):
    return (nav / b['units']) / 100.0 - 1 if b['units'] > 0 else float('nan')


def tax_estimate(b, d):
    """Realised gains of the current financial year (F1-F3, no carried losses, approximate) + dividends; NAV is NOT after tax."""
    fy0 = f'{int(d[:4]) - (1 if d[5:7] < "07" else 0)}-07-01'
    st_, lt = 0.0, 0.0
    for t in b['trades']:
        if t['side'] != 'sell' or t['date'] < fy0: continue
        for (bd, q, c, pr) in t.get('lots', []):
            g = pr - c
            if (pd.Timestamp(t['date']) - pd.Timestamp(bd)).days >= 367: lt += g
            else: st_ += g
    dv = sum(x[4] for x in b['divs'] if x[0] >= fy0)
    out = {}
    for reg, disc in (('A', 0.5), ('B', 0.0)):
        loss = min(0.0, st_) + min(0.0, lt); s2, l2 = max(0.0, st_), max(0.0, lt)
        s2 += loss; l2 += min(0.0, s2); s2 = max(0.0, s2); l2 = max(0.0, l2)
        out[reg] = round(0.32 * (s2 + l2 * (1 - disc)) + 0.32 * dv, 2)
    return out, round(st_, 2), round(lt, 2), round(dv, 2)


def scorecard(st, d):
    last = st['last']; flags = st['flags']; rows = []; hold = []
    cm = {c['id']: c for c in st['cmps']}
    ps = PS.load(); cm0 = {c['id']: c for c in ps['cmps']} if ps else {}                 # AMENDMENT_scoring_v2: A$0 comparators (primary)
    ps_now = ps is not None and ps['last_processed'] == d
    sale = PS.engine_sale_cost(st['ranks'])
    nanr = lambda x: round(x, 5) if x is not None and np.isfinite(x) else None
    def cmp_for(b, kind):
        tag = 'lifecycle_5k' if b['contrib'] > 0 else f"{int(b['capital'] // 1000)}k"
        return cm.get(f'CMP_{kind}_{tag}')
    rnd = {}
    for b in st['books']:
        nav = P.nav_of(b, last); r = twr(b, nav)
        if b['kind'] == 'random': rnd.setdefault(int(b['capital']), []).append(r); continue
        nav70 = nav - sum(0.3 * P.shares_of(h) * last[h['code']]['p'] for h in b['holdings'].values() if h['code'] in flags and h['code'] in last)
        a2, mix = cmp_for(b, 'A200'), cmp_for(b, '4060')
        ra = twr(a2, P.nav_of(a2, last)) if a2 else float('nan'); rm = twr(mix, P.nav_of(mix, last)) if mix else float('nan')
        tax, st_, lt, dv = tax_estimate(b, d)
        a2b, mixb = (cm0.get(a2['id'] + '_b0') if a2 else None), (cm0.get(mix['id'] + '_b0') if mix else None)
        rab = PS.ret_at(a2b, d) if a2b else float('nan'); rmb = PS.ret_at(mixb, d) if mixb else float('nan')
        kept, sold = PS.after_tax_engine(b, last, d, sale); rk, rs = PS.at_return(kept, b['units']), PS.at_return(sold, b['units'])
        if ps_now and a2b:
            ak, as_ = PS.after_tax_cmp0(a2b, ps['last'], d); rak, ras = PS.at_return(ak, a2b['units']), PS.at_return(as_, a2b['units'])
        else: rak = ras = float('nan')
        rows.append(dict(asof=d, book=b['id'], kind=b['kind'], capital=b['capital'], contributed=b['contributed'], nav=round(nav, 2),
                         nav_q6_at_70pct=round(nav70, 2), cash=round(b['cash'], 2), n=b['n'], T=round(b['T'] or 0, 2), holdings=len(b['holdings']),
                         open_orders=len(b['orders']), return_since_start=round(r, 5), a200_return=round(ra, 5), vs_a200=round(r - ra, 5),
                         nav_minus_a200_AUD=round(nav - P.nav_of(a2, last), 2) if a2 else None, plan4060_return=round(rm, 5), vs_4060=round(r - rm, 5),
                         nav_minus_4060_AUD=round(nav - P.nav_of(mix, last), 2) if mix else None, realised_short=st_, realised_long=lt, dividends_fy=dv,
                         est_tax_fy_A=tax['A'], est_tax_fy_B=tax['B'],
                         pct_of_random=(round(float(np.mean(np.array(rnd_all(st, b['capital'], last)) < r)), 3) if b['kind'] == 'h82' and b['contrib'] == 0 else None),
                         a200_b0_return=nanr(rab), vs_a200_b0=nanr(r - rab), nav_minus_a200_b0_AUD=(round(nav - a2b['nav'][d], 2) if a2b and d in a2b['nav'] else None),
                         plan4060_b0_return=nanr(rmb), vs_4060_b0=nanr(r - rmb), nav_minus_4060_b0_AUD=(round(nav - mixb['nav'][d], 2) if mixb and d in mixb['nav'] else None),
                         after_tax_kept_AUD=round(kept, 2), after_tax_sold_AUD=round(sold, 2), ret_after_tax_kept=nanr(rk), ret_after_tax_sold=nanr(rs),
                         a200_b0_ret_after_tax_kept=nanr(rak), a200_b0_ret_after_tax_sold=nanr(ras), vs_a200_b0_after_tax_kept=nanr(rk - rak), vs_a200_b0_after_tax_sold=nanr(rs - ras),
                         vs_a200_b0_engine_sold_fund_kept=nanr(rs - rak)))
        for cid, h in b['holdings'].items():
            sh = P.shares_of(h); c = P.cost_of(h); lp = last.get(h['code'], {})
            v = sh * lp.get('p', float('nan'))
            hold.append(dict(asof=d, book=b['id'], code=h['code'], name=h.get('name', ''), shares=sh, cost_AUD=round(c, 2), first_buy=min(l[0] for l in h['lots']),
                             last_close=lp.get('p'), last_close_date=lp.get('d'), value_AUD=round(v, 2), pnl_AUD=round(v - c, 2), pnl_pct=round(v / c - 1, 4),
                             awaiting_sale=bool(h.get('awaiting_sale')), q6_flag=h['code'] in flags))
    for c in st['cmps']:
        nav = P.nav_of(c, last)
        rows.append(dict(asof=d, book=c['id'], kind='comparator', capital=c['capital'], contributed=c['contributed'], nav=round(nav, 2), nav_q6_at_70pct=round(nav, 2),
                         cash=round(c['cash'], 2), holdings=sum(1 for u in c['fund_units'].values() if u > 0), open_orders=len(c['pending']),
                         return_since_start=round(twr(c, nav), 5)))
    for c in (ps['cmps'] if ps else []):
        if d not in c['nav']: continue
        rows.append(dict(asof=d, book=c['id'], kind='comparator A$0', capital=c['capital'], contributed=c['contributed'], nav=c['nav'][d], nav_q6_at_70pct=c['nav'][d],
                         cash=round(c['cash'], 2), holdings=sum(1 for u in c['fund_units'].values() if u > 0), open_orders=len(c['pending']),
                         return_since_start=round(PS.ret_at(c, d), 5), note='A$0 brokerage (AMENDMENT_scoring_v2); EODHD proxy'))
    for cap, v in sorted(rnd.items()):
        v = np.array(v)
        rows.append(dict(asof=d, book=f'RND_{cap // 1000}k (200 seeds)', kind='random control', capital=cap, return_since_start=round(float(np.median(v)), 5),
                         nav=None, note=f'median; 5th-95th pct {np.percentile(v, 5):.4f} to {np.percentile(v, 95):.4f}'))
    try: shrows, shmd, shhold = SH.scorecard_rows(st, d)                     # SHADOW lines M3 / E3 (AMENDMENT_shadow_M3_E3.md); never changes the books
    except Exception as e:
        log('SHADOW scorecard error (H82 unaffected):', repr(e)); shrows, shmd, shhold = [], [f'| SHADOW M3 / E3 | — | — | scorecard error: {repr(e)[:120]} |'], []
    rows += shrows
    try: acrows, acmd, achold = AC.scorecard_rows(d)                           # SHADOW ACC (AMENDMENT_shadow_ACC_keep_winners.md)
    except Exception as e:
        log('SHADOW ACC scorecard error (H82 unaffected):', repr(e)); acrows, acmd, achold = [], [f'| SHADOW ACC | — | — | scorecard error: {repr(e)[:120]} |'], []
    rows += acrows
    try: cxrows, cxmd, cxhold = CX.scorecard_rows(d)                           # SHADOW CXL (AMENDMENT_shadow_CXL_D2.md)
    except Exception as e:
        log('SHADOW CXL scorecard error (H82 unaffected):', repr(e)); cxrows, cxmd, cxhold = [], [f'| SHADOW CXL | — | — | scorecard error: {repr(e)[:120]} |'], []
    rows += cxrows
    try: emrows, emmd, emhold = EM.scorecard_rows(d)                           # SHADOW EMG2 lead challenger (owner decision D-2: placed first)
    except Exception as e:
        log('SHADOW EMG2 scorecard error (H82 unaffected):', repr(e)); emrows, emmd, emhold = [], [f'| EMG2 | — | — | scorecard error: {repr(e)[:120]} |'], []
    try: earows, eamd, eahold = EA.scorecard_rows(d)                           # SHADOW EARLY (information only, unproven)
    except Exception as e:
        log('SHADOW EARLY scorecard error (H82 unaffected):', repr(e)); earows, eamd, eahold = [], [f'| SHADOW EARLY | — | — | scorecard error: {repr(e)[:120]} |'], []
    try: esrows, esmd, eshold = ES.scorecard_rows(d)                           # EMG2-18 paper twins (information only), right after EMG2
    except Exception as e:
        log('EMG2-18 twins scorecard error (H82 unaffected):', repr(e)); esrows, esmd, eshold = [], [f'| EMG2-18 paper twins | — | — | scorecard error: {repr(e)[:120]} |'], []
    try: btrows, btmd, bthold = BT.scorecard_rows(d)                           # PAPER line EMG2_18_SIM_BT (band-trend switch; information only)
    except Exception as e:
        log('EMG2-18 BT scorecard error (H82 unaffected):', repr(e)); btrows, btmd, bthold = [], [f'| EMG2_18_SIM_BT | — | — | scorecard error: {repr(e)[:120]} |'], []
    try: b6rows, b6md, b6hold = BT6.scorecard_rows(d)                          # PAPER line EMG2_18_SIM_BT_C6 (band trend + sell rule C6; information only)
    except Exception as e:
        log('EMG2-18 BT_C6 scorecard error (H82 unaffected):', repr(e)); b6rows, b6md, b6hold = [], [f'| EMG2_18_SIM_BT_C6 | — | — | scorecard error: {repr(e)[:120]} |'], []
    esrows = esrows + btrows + b6rows; esmd = esmd + btmd + b6md; eshold = eshold + bthold + b6hold
    try: b3rows, b3md, b3hold = B3.scorecard_rows(d)                           # PAPER line BLIND3 + 50/50 EMG2-18 + BLIND3 reading (information only)
    except Exception as e:
        log('BLIND3 scorecard error (H82 unaffected):', repr(e)); b3rows, b3md, b3hold = [], [f'| BLIND3 | — | — | scorecard error: {repr(e)[:120]} |'], []
    try: prrows, prmd, prhold = PR.scorecard_rows(d)                           # PAPER line PAIR (information only)
    except Exception as e:
        log('PAIR scorecard error (H82 unaffected):', repr(e)); prrows, prmd, prhold = [], [f'| PAIR | — | — | scorecard error: {repr(e)[:120]} |'], []
    b3md = b3md + prmd; b3hold = b3hold + prhold
    try: slrows, slmd, slhold = SL.scorecard_rows(d)                           # side lines SWEEP / WIDE / FIP (seq 91; information only)
    except Exception as e:
        log('side lines scorecard error (no other line affected):', repr(e)); slrows, slmd, slhold = [], [f'| side lines | — | — | scorecard error: {repr(e)[:120]} |'], []
    try: icrows, icmd, _ = IC.scorecard_rows(d)                                # EST-C / DIL-C (seq 91; information only)
    except Exception as e:
        log('EST-C / DIL-C scorecard error (no other line affected):', repr(e)); icrows, icmd = [], [f'| EST-C / DIL-C | — | — | scorecard error: {repr(e)[:120]} |']
    try: morows, momd, mohold = MO.scorecard_rows(d)                           # MOON_TOP5 / NOLOT5 / LEG2 (seq 94; information only)
    except Exception as e:
        log('MOON scorecard error (no other line affected):', repr(e)); morows, momd, mohold = [], [f'| MOON lines | — | — | scorecard error: {repr(e)[:120]} |'], []
    rows = emrows + esrows + b3rows + prrows + rows + earows
    sc = pd.DataFrame(rows + slrows + icrows + morows); hd = pd.DataFrame(hold)     # side-line rows last, existing columns only
    os.makedirs(P.PAPER, exist_ok=True); files = {}
    files['paper/scorecard_latest.csv'] = P.write_csv(P.PAPER + '/scorecard_latest.csv', sc)
    files['paper/holdings_latest.csv'] = P.write_csv(P.PAPER + '/holdings_latest.csv', hd if len(hd) else pd.DataFrame(columns=['asof', 'book', 'code']))
    # history (one row per book per day)
    hp = P.PAPER + '/scorecard_history.csv'
    old = pd.read_csv(hp) if os.path.exists(hp) else pd.DataFrame()
    if len(old): old = old[old['asof'].astype(str) != d]          # column, not DataFrame.asof (method)
    if len(old) and ps: old = backfill_history(st, ps, old)        # AMENDMENT_scoring_v2: A$0 comparator columns/rows for earlier days
    files['paper/scorecard_history.csv'] = P.write_csv(hp, pd.concat([old, sc], ignore_index=True))
    # markdown
    pend = []
    for b in st['books'][:5]:
        for o in b['orders']:
            pend.append(f"| {b['id']} | {o['type']} | {o['code']} | {('A$%.2f' % o['amount']) if 'amount' in o else ('%s shares' % o['shares'])} | {o.get('date') or ('attempt from ' + str(b['E']))} | {o['reason']} |")
    f = lambda x: '' if x is None or (isinstance(x, float) and np.isnan(x)) else (f'{x:+.2%}' if isinstance(x, float) else str(x))
    md = [f'# Big Wins paper scorecard — {d}', '', f'**{P.HEADER}**', '',
          '## Lead challenger: EMG2 (SHADOW, paper only; H82 below is the large-company control)', '', '| Line | NAV A$ | Return | Reading |', '|---|---|---|---|'] + emmd + esmd + b3md + ['',
          f"Start decision {st['start_decision']}, fills at the close of {st['fill_day']}. Rules v1.3 (SHA-256 {P.RULES_SHA[:8]}…) + AMENDMENT_start_now.md (+ v1.4 and v1.5 from 31 Dec 2026). "
          'Fills at the close under v1.3 D/E (brokerage max(A$6.60, 0.088%), half-spread E2). After costs, before tax unless marked "after tax". '
          'Returns are time-weighted (unit index), so contributions do not count as gains. '
          '**Comparators: A200 and the 40/60 plan at A$0 brokerage (the owner\'s platform) are the benchmark** (AMENDMENT_scoring_v2.md); the frozen J3 comparators (A$6.60 per fund purchase) are in the second table.', '',
          '| Book | NAV A$ | Contributed | Return | A200 (A$0) | vs A200 | 40/60 (A$0) | vs 40/60 | After tax, kept: vs A200 kept | After tax, sold: vs A200 sold | Holdings | Cash | % of random |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        if r['kind'] in ('h82', 'momentum'):
            nm = r['book'] + (' (illustration only)' if 'lifecycle' in r['book'] else '')
            md.append(f"| {nm} | {r['nav']:,.2f} | {r['contributed']:,.0f} | {f(r['return_since_start'])} | {f(r.get('a200_b0_return'))} | {f(r.get('vs_a200_b0'))} | "
                      f"{f(r.get('plan4060_b0_return'))} | {f(r.get('vs_4060_b0'))} | {f(r.get('vs_a200_b0_after_tax_kept'))} | {f(r.get('vs_a200_b0_after_tax_sold'))} | "
                      f"{r['holdings']} | {r['cash']:,.2f} | {'' if r.get('pct_of_random') is None else r['pct_of_random']} |")
    md += ['', 'After tax: 32% rate, 50% discount for parcels held 367+ days, cumulative from the start; "kept" = tax on income and on gains already realised; '
           '"sold" = as if every holding were sold at the day\'s close (sale costs included). Franking credits not yet counted on either side. '
           'The owner\'s real comparison is the engine "sold" against the fund "kept" (CSV column vs_a200_b0_engine_sold_fund_kept).', '']
    if d <= '2027-01-31':
        md += ['**Flag — 31 Dec 2026 review:** rule C5 will sell every holding not on the December list six weeks after the 17 Nov start: an extra round trip '
               '(about 0.3–0.7% of the book) and short-term gains. That cost belongs to the start date, not to the engine\'s normal running (review 80 §1.5).', '']
    md += ['| Frozen J3 comparator (A$6.60 per fund purchase) | Book | vs A200 (J3) | vs 40/60 (J3) |', '|---|---|---|---|']
    for r in rows:
        if r['kind'] in ('h82', 'momentum'): md.append(f"| A200 {f(r['a200_return'])}; 40/60 {f(r['plan4060_return'])} | {r['book']} | {f(r['vs_a200'])} | {f(r['vs_4060'])} |")
    md += ['', '| Comparator / control | NAV A$ | Return | Note |', '|---|---|---|---|']
    for r in rows:
        if r['kind'] == 'comparator A$0': md.append(f"| {r['book']} | {r['nav']:,.2f} | {f(r['return_since_start'])} | A$0 brokerage (primary); EODHD proxy (A200.AU/BGBL.AU close + distributions) |")
    for r in rows:
        if r['kind'] == 'comparator': md.append(f"| {r['book']} (J3 as frozen) | {r['nav']:,.2f} | {f(r['return_since_start'])} | A$6.60 per fund purchase; EODHD proxy |")
        if r['kind'] == 'random control': md.append(f"| {r['book']} | | {f(r['return_since_start'])} | {r['note']} |")
    md += shmd
    md += acmd
    md += cxmd
    md += eamd
    md += ['', '## Side lines (AMENDMENT_shadow_sidelines_v1.md, ledger seq 91: information only, never evidence for or against the main line)', '',
           'Each paper book = EMG2_18_SIM_BT_C6 with one change; A$10,000; 100 twins paired with the BT_C6 twins (seeds 8810000+i); twin-pair percentile = '
           'share of the 100 differences (side twin i - BT_C6 twin i) below the real difference. EST-C and DIL-C trade nothing.', '',
           '| Line | NAV A$ | Return | Reading |', '|---|---|---|---|'] + slmd + icmd + momd
    md += ['', '## Holdings (H82 books)', '', '| Book | Code | Name | Shares | Cost A$ | Last | Value A$ | P&L A$ | P&L | Flags |', '|---|---|---|---|---|---|---|---|---|---|']
    for h in hold:
        if h['book'].startswith('H82'):
            md.append(f"| {h['book']} | {h['code']} | {h['name'][:28]} | {h['shares']:,.0f} | {h['cost_AUD']:,.2f} | {h['last_close']} ({h['last_close_date']}) | {h['value_AUD']:,.2f} | "
                      f"{h['pnl_AUD']:,.2f} | {h['pnl_pct']:+.2%} | {'awaiting sale ' if h['awaiting_sale'] else ''}{'Q6 STOPPED-TRADING FLAG' if h['q6_flag'] else ''} |")
    if shhold: md += ['', '## SHADOW books (M3, E3: not adopted; tracked for information)', ''] + shhold
    if achold: md += ['', '## SHADOW ACC books (keep winners: not adopted; tracked for information)', ''] + achold
    if cxhold: md += ['', '## SHADOW CXL books (report 81 D2, cap-weighted ex-losers: not adopted; tracked for information)', ''] + cxhold
    if emhold: md += ['', '## EMG2 books (lead challenger; SHADOW, paper only)', ''] + emhold
    if eshold: md += ['', '## EMG2-18 paper twins (H6, COMBO, REF) and paper lines EMG2_18_SIM_BT, EMG2_18_SIM_BT_C6 (information only)', ''] + eshold
    if b3hold: md += ['', '## BLIND3 and PAIR paper books (information only)', ''] + b3hold
    if eahold: md += ['', '## SHADOW EARLY books (information only, unproven)', ''] + eahold
    if slhold: md += ['', '## Side-line paper books (SWEEP, WIDE, FIP; information only)', ''] + slhold
    if mohold: md += ['', '## Aggressive side-line paper books (MOON_TOP5, MOON_NOLOT5, MOON_LEG2; information only, seq 94)', ''] + mohold
    if pend: md += ['', '## Pending paper orders (H82 and momentum books)', '', '| Book | Type | Code | Size | When | Rule |', '|---|---|---|---|---|---|'] + pend
    md += ['', '## Data notes', '', f"- Q6 flags: {json.dumps(flags) if flags else 'none'}", f"- Data blocks: {st['data_blocks'] or 'none'}",
           f"- Decisions so far: {', '.join(st['decisions'])}"]
    ev = [f"- {e[0]} {b['id']}: {e[1]}" for b in st['books'][:5] + st['cmps'] for e in b['events'] if e[0] >= P.prev_session(d)]
    if ev: md += ['', '## Events (last two sessions)', ''] + ev[:80]
    open(P.PAPER + '/SCORECARD.md', 'w').write('\n'.join(md) + '\n'); files['paper/SCORECARD.md'] = L.sha(P.PAPER + '/SCORECARD.md')
    return files

def backfill_history(st, ps, old):
    """AMENDMENT_scoring_v2 §2: fill the A$0-comparator columns of earlier days from the stored NAVs (book NAVs unchanged) and add the
    A$0 comparator rows of those days. Idempotent: only empty cells / missing rows are filled."""
    cm = {c['id']: c for c in st['cmps']}; cm0 = {c['id']: c for c in ps['cmps']}; bk = {b['id']: b for b in st['books']}
    old = old.copy()
    for col in ('a200_b0_return', 'vs_a200_b0', 'plan4060_b0_return', 'vs_4060_b0', 'nav_minus_a200_b0_AUD', 'nav_minus_4060_b0_AUD'):
        if col not in old.columns: old[col] = np.nan
    for i, r in old.iterrows():
        if r['kind'] not in ('h82', 'momentum') or pd.notna(r['a200_b0_return']) or r['book'] not in bk: continue
        b = bk[r['book']]; d = str(r['asof']); tag = 'lifecycle_5k' if b['contrib'] > 0 else f"{int(b['capital'] // 1000)}k"
        rb = PS.ret_at(b, d)
        for k, col, ncol in (('A200', 'a200_b0_return', 'vs_a200_b0'), ('4060', 'plan4060_b0_return', 'vs_4060_b0')):
            c = cm0.get(f'CMP_{k}_{tag}_b0')
            if c is None or d not in c['nav']: continue
            rc = PS.ret_at(c, d); old.at[i, col] = round(rc, 5); old.at[i, ncol] = round(rb - rc, 5)
            old.at[i, 'nav_minus_a200_b0_AUD' if k == 'A200' else 'nav_minus_4060_b0_AUD'] = round(b['nav'][d] - c['nav'][d], 2)
    have = set(zip(old['asof'].astype(str), old['book'])); add = []
    for d in sorted(set(old['asof'].astype(str))):
        for c in ps['cmps']:
            if d in c['nav'] and (d, c['id']) not in have:
                add.append(dict(asof=d, book=c['id'], kind='comparator A$0', capital=c['capital'], contributed=sum(a for f, a in c['flows'] if f <= d), nav=c['nav'][d],
                                nav_q6_at_70pct=c['nav'][d], return_since_start=round(PS.ret_at(c, d), 5), note='A$0 brokerage (AMENDMENT_scoring_v2); re-computed from the stored bulk files'))
    return pd.concat([old, pd.DataFrame(add)], ignore_index=True) if add else old


def rnd_all(st, cap, last):
    return [twr(b, P.nav_of(b, last)) for b in st['books'] if b['kind'] == 'random' and b['capital'] == cap]


def process_day(st, d, mkt, cli, download):
    last = st['last']
    for code, px in mkt['close'].items(): last[code] = dict(p=px, d=d)
    for b in st['books']: P.run_day(b, d, mkt, last, st['ranks'], log)
    for c in st['cmps']: P.run_cmp_day(c, d, mkt)
    dec_info = None
    if P.is_month_end(d):
        for b in st['books'] + st['cmps']: P.credit_contribution(b, d, last)
        if download:
            import fwd_download
            fwd_download.run(download=True, log=log, since=f'{d}T05:30')
        dec, man, msha = P.build_decision(d, d, log=log)
        dec_info = dict(asof=d, q4=dec['q4'], manifest_sha256=msha, scores_sha256=dec['scores_sha256'])
        if dec['q4']['blocked']:
            st['data_blocks'].append([d, 'BW_DATA_BLOCK', dec['q4']]); log('BW_DATA_BLOCK', d, dec['q4'])
        else:
            E = P.next_session(d); we = next(x for x in P.sessions() if x > d and P.is_month_end(x))
            for b in st['books']: P.decide(b, dec, d, last, E, we, log)
            st['ranks'] = dec['ranks']; st['decisions'].append(d)
    st['flags'] = q6_flags(st, d)
    for b in st['books'] + st['cmps']: b['nav'][d] = round(P.nav_of(b, last), 2)
    st['last_processed'] = d
    return dec_info


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--no-download', action='store_true'); ap.add_argument('--until'); a = ap.parse_args()
    os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    lk = open(P.STATE_DIR + '/.daily.lock', 'w'); fcntl.flock(lk, fcntl.LOCK_EX)
    st = P.load_state(); L.verify()
    today = a.until or time.strftime('%Y-%m-%d', time.gmtime())
    todo = P.sessions_between(st['last_processed'], today)
    cli = None if a.no_download else P.client(log)
    axjo = {} if not todo else (P.fetch_axjo(st['last_processed'], cli, log) if cli else {})
    booked = []
    for d in todo:
        later = any(x > d for x in axjo)
        if cli and d not in axjo:
            if later: log(d, 'not in AXJO.INDX although later days are: not a trading day under A1; skipped'); continue
            log(d, 'AXJO.INDX has no row yet: EODHD has not published this close; stopping'); break
        uni = {c.split('#')[0] for c in st['ranks']}
        if cli and not os.path.exists(f'{P.BULK}/{d}/eod.json.gz'): log(d, 'bulk', P.fetch_bulk(d, cli, log))
        mkt = P.load_day(d)
        if mkt is None: log(d, 'no bulk file; stopping'); break
        cov = sum(1 for c in uni if c in mkt['close'])
        if cli and cov < 285 and not later:                      # stored file may predate EODHD's full update: fetch again once
            log(d, 'bulk re-fetch', P.fetch_bulk(d, cli, log)); mkt = P.load_day(d); cov = sum(1 for c in uni if c in mkt['close'])
        if cov < 285 and not later:
            log(d, f'only {cov}/{len(uni)} universe closes in the bulk file: EODHD not complete yet; stopping (re-run later)'); break
        dec_info = process_day(st, d, mkt, cli, download=cli is not None)
        ssha = P.save_state(st)
        sh = SH.run(d, mkt, log)                                        # SHADOW lines (own state file; H82 state is not touched)
        ac = AC.run(d, mkt, log)                                        # SHADOW ACC (own state file; reads the M3 table the shadow step wrote)
        cx = CX.run(d, mkt, log)                                        # SHADOW CXL (AMENDMENT_shadow_CXL_D2.md; own state file; reads the M3 table + ASIC archive)
        em = EM.run(d, mkt, log)                                        # SHADOW EMG2 (AMENDMENT_shadow_EMG2.md; own state file; month-end bundle as the SHADOW lines)
        es = ES.run(d, mkt, log)                                        # EMG2-18 paper twins H6 / COMBO / REF (own state file; same month-end bundle as EMG2)
        bt = BT.run(d, mkt, log)                                        # PAPER line EMG2_18_SIM_BT (own state file; same month-end bundle as EMG2)
        b6 = BT6.run(d, mkt, log)                                       # PAPER line EMG2_18_SIM_BT_C6 (own state file; same month-end bundle as EMG2)
        b3 = B3.run(d, mkt, log)                                        # PAPER line BLIND3 (own state file; same month-end bundle as EMG2)
        pr = PR.run(d, mkt, log)                                        # PAPER line PAIR (own state file; same month-end bundle as EMG2)
        ea = EA.run(d, mkt, log)                                        # SHADOW EARLY (AMENDMENT_shadow_EARLY.md; own state file; reads the new-listings tracker)
        sl = SL.run(d, mkt, log)                                        # side lines SWEEP / WIDE / FIP (seq 91; own state files; same month-end bundle; after every registered line)
        ic = IC.run(d, mkt, log)                                        # EST-C / DIL-C readings (seq 91; own state file; information only)
        mo = MO.run(d, mkt, log); EM.clear_bundle(); P.BUNDLE.clear()   # MOON_TOP5 / NOLOT5 / LEG2 (seq 94; own state files; same month-end bundle)
        ps = PS.sync(st, log)                                           # A$0 comparators (scoring only; own state file)
        files = scorecard(st, d)
        extra = dict(score=ps)
        if sh is not None: extra['shadow'] = sh
        if ac is not None: extra['accum'] = ac
        if cx is not None: extra['cxl'] = cx
        if em is not None: extra['emg2'] = em
        if es is not None: extra['emg2s'] = es
        if bt is not None: extra['emg2bt'] = bt
        if b6 is not None: extra['emg2bt6'] = b6
        if b3 is not None: extra['blind3'] = b3
        if pr is not None: extra['pair'] = pr
        if ea is not None: extra['early'] = ea
        for k_, v_ in (sl or {}).items(): extra[k_] = v_                # sl_sweep, sl_wide, sl_fip
        if ic is not None: extra['info_c'] = ic
        for k_, v_ in (mo or {}).items(): extra[k_] = v_                # moon_top5, moon_nolot5, moon_leg2
        e = L.append(**extra, asof=d, kind='daily' + (' + month-end decision' if dec_info else ''), event=f'paper day booked {d} (closes; fills; dividends; NAV)',
                     universe_closes=f'{cov}/{len(uni)}', state_sha256=ssha, files_sha256=files, decision=dec_info,
                     trades=sum(1 for b in st['books'] for t in b['trades'] if t['date'] == d), flags=list(st['flags']))
        log(d, 'booked; ledger', e['seq'], e['entry_sha256'][:12]); booked.append(d)
    if not booked:
        PS.sync(st, log)
        EM.run(st['last_processed'], None, log); ES.run(st['last_processed'], None, log); BT.run(st['last_processed'], None, log); BT6.run(st['last_processed'], None, log); B3.run(st['last_processed'], None, log); PR.run(st['last_processed'], None, log); EA.run(st['last_processed'], None, log); SL.run(st['last_processed'], None, log); IC.run(st['last_processed'], None, log); MO.run(st['last_processed'], None, log); EM.clear_bundle(); P.BUNDLE.clear()   # catch-up only (e.g. EARLY waiting for the tracker); no new day
        scorecard(st, st['last_processed']); log('nothing new to book; scorecard refreshed for', st['last_processed'])

if __name__ == '__main__':
    main()
