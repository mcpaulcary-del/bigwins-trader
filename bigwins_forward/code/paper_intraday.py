# Big Wins forward PAPER record -- intraday LOOK (idempotent; run every ~2 hours in ASX hours).
#
#   *** NO TRADING DECISIONS ARE MADE HERE. ***  Rules v1.3 decide on closing prices only; intraday rules are untested.
#   This script only archives EODHD delayed quotes, marks the paper books to them ("indicative, delayed") and writes alerts.
#   PAPER ONLY: no real money, no broker orders, the AI never places trades.  (Amendment AMENDMENT_start_now.md section 4 and
#   AMENDMENT_intraday_look.md.)
#
#   python3 -I paper_intraday.py [--force]
# ASX hours: 10:00-16:10 Sydney time = 23:00-05:10 UTC under AEDT (Oct-Apr), 00:00-06:10 UTC under AEST.
# Quotes: GET https://eodhd.com/api/real-time/{SYM}.AU?fmt=json&s=SYM2.AU,...  (delayed ~15-20 min; intraday history endpoint is
# Forbidden on this plan).  Batched: held names, pending orders, A200, BGBL, the top-300 universe of the latest decision.
# Outputs: SCRATCH/bigwins_forward/out/intraday/YYYY-MM-DD.csv.gz (append), 68_forward_record/paper/INTRADAY.md (indicative books),
#          68_forward_record/paper/alerts.md (append-only alert log) + alerts_latest.md.
import os, sys, json, gzip, time, argparse, fcntl, datetime as dt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad/bigwins_forward/code')
import paper_lib as P

OUT = P.FW + '/out/intraday'
SYD = ZoneInfo('Australia/Sydney')
LOGF = P.FW + '/out/logs/paper_intraday.log'
BATCH = 40

def log(*a):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + ' '.join(str(x) for x in a)
    print(s, flush=True); open(LOGF, 'a').write(s + '\n')


def quotes(codes, cli):
    out = []
    codes = sorted(set(codes))
    for i in range(0, len(codes), BATCH):
        b = [c + '.AU' for c in codes[i:i + BATCH]]
        params = {'s': ','.join(b[1:])} if len(b) > 1 else {}
        code, js = cli.get(f'real-time/{b[0]}', params, 'realtime', f'batch{i // BATCH}', save=False)
        if code != 200 or js is None: log('real-time batch', i // BATCH, 'HTTP', code); continue
        out += js if isinstance(js, list) else [js]
    return out


def num(x):
    try:
        v = float(x); return v if np.isfinite(v) else None
    except (TypeError, ValueError): return None


def indicative_scores(dec, q):
    """Re-score the decision-day universe with the latest quote in place of the close: s2, s3 move with the price; s1 (ME(1)/ME(12))
    and s4 (volatility) are left at their decision-day values. INDICATIVE ONLY."""
    rows = dec['rows']; M = []
    for r in rows:
        px = q.get(r['code'])
        if None in (r['M1'], r['M2'], r['M3'], r['M5'], r['close10']) or px is None:
            M.append([r['M1'], r['M2'], r['M3'], r['M5']]); continue
        hi = r['close10'] / r['M3']
        M.append([r['M1'], (1 + r['M2']) * px / r['close10'] - 1, px / max(hi, px), r['M5']])
    X = pd.DataFrame(M, dtype=float)
    pct = X.rank(pct=True)
    sc = pct.mean(axis=1, skipna=False)
    order = sorted([j for j in range(len(rows)) if not np.isnan(sc[j])], key=lambda j: (-sc[j], j))
    return {rows[j]['code']: k + 1 for k, j in enumerate(order)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--force', action='store_true', help='run even outside ASX hours'); a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    lk = open(P.STATE_DIR + '/.intraday.lock', 'w'); fcntl.flock(lk, fcntl.LOCK_EX)
    now = dt.datetime.now(dt.timezone.utc); loc = now.astimezone(SYD); sess = loc.date().isoformat()
    is_sess = sess in set(P.sessions()); hhmm = loc.hour * 100 + loc.minute
    open_ = is_sess and 1000 <= hhmm <= 1645          # 16:45 allows one look at the delayed post-close quotes
    if not open_ and not a.force:
        log(f'outside ASX hours (Sydney {loc:%Y-%m-%d %H:%M}, session={is_sess}); nothing fetched'); return
    st = P.load_state(); dec = P.load_decision(st['decisions'][-1])
    main_books = [b for b in st['books'] if b['kind'] in ('h82', 'momentum')]      # random controls are covered by the universe pull
    held = {h['code'] for b in main_books for h in b['holdings'].values()}
    pend = {o['code'] for b in main_books for o in b['orders']}
    uni = {r['code'] for r in dec['rows']}
    codes = held | pend | uni | {'A200', 'BGBL'}
    cli = P.client(log)
    js = quotes(codes, cli)
    rows = []
    for r in js:
        c = str(r.get('code', '')).replace('.AU', '')
        ts = num(r.get('timestamp'))
        rows.append(dict(fetch_utc=now.strftime('%Y-%m-%dT%H:%M:%SZ'), code=c, quote_utc=(dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if ts else None),
                         quote_session=(dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone(SYD).date().isoformat() if ts else None),
                         open=num(r.get('open')), high=num(r.get('high')), low=num(r.get('low')), close=num(r.get('close')), volume=num(r.get('volume')),
                         previous_close=num(r.get('previousClose')), change_p=num(r.get('change_p')),
                         held=c in held, pending=c in pend, universe=c in uni))
    df = pd.DataFrame(rows)
    fp = f'{OUT}/{sess}.csv.gz'
    old = pd.read_csv(fp) if os.path.exists(fp) else pd.DataFrame()
    pd.concat([old, df], ignore_index=True).to_csv(fp + '.tmp', index=False, compression='gzip'); os.replace(fp + '.tmp', fp)
    log(f'{len(df)} quotes archived to {fp} (requested {len(codes)})')
    # ---------- quotes usable for marking: dated this session, positive price
    # a quote counts only if it is from this session's continuous trading (>= 10:00 Sydney); earlier stamps are pre-open carries
    if len(df):
        qloc = pd.to_datetime(df.quote_utc, utc=True).dt.tz_convert(SYD)
        df['live'] = (df.quote_session == sess) & (qloc.dt.hour >= 10)
    fresh = df[df.live & (df.close > 0)] if len(df) else df
    q = dict(zip(fresh.code, fresh.close)) if len(fresh) else {}
    alerts = []
    tag = f'{now:%Y-%m-%d %H:%MZ}'
    missing = sorted((held | pend | {'A200', 'BGBL'}) - set(df.code if len(df) else []))
    if missing: alerts.append(f'BROKEN DATA: no quote returned for {missing}')
    stale = sorted(set(df[~df.live].code) & (held | pend)) if len(df) and open_ and hhmm >= 1030 else []
    if stale: alerts.append(f'STALE/NO TRADE TODAY (quote not from this session): {stale}')
    if len(df) and len(fresh) < 0.5 * len(df) and open_ and hhmm >= 1030: alerts.append(f'BROKEN DATA: only {len(fresh)}/{len(df)} quotes are from session {sess}')
    for _, r in df.iterrows():
        c = r.code; prev = st['last'].get(c, {}).get('p') or r.previous_close
        if r.close is None or not (r.close > 0):
            if c in held or c in pend or c in ('A200', 'BGBL'): alerts.append(f'BROKEN DATA: {c} quote close {r.close}')
            continue
        if not r.live: continue
        chg = (r.close / prev - 1) if prev else None
        if chg is not None and abs(chg) > 0.6: alerts.append(f'BROKEN DATA? {c} {r.close} vs last close {prev} ({chg:+.0%}) - check splits/consolidations')
        if c in held and chg is not None and abs(chg) >= 0.08: alerts.append(f'HOLDING MOVE {c} {chg:+.1%} on day (quote {r.close}, last close {prev})')
        if chg is not None and chg >= 0.20 and (c in held or c in pend or c in uni): alerts.append(f'+20% JUMP {c} {chg:+.1%} (possible takeover/scheme; check ASX announcements)')
        if (c in held or c in pend) and not (num(r.volume) or 0) > 0 and hhmm >= 1200: alerts.append(f'NO VOLUME BY MIDDAY {c} (possible trading halt/suspension)')
    # ---------- indicative score bands (top-30 / top-90) on latest quotes
    try:
        ir = indicative_scores(dec, q); base = {r['code']: r['srank'] for r in dec['rows'] if r['srank']}
        for band in (30, 90):
            enter = sorted(c for c, k in ir.items() if k <= band and (base.get(c) or 999) > band)
            leave = sorted(c for c, k in base.items() if k <= band and (ir.get(c) or 999) > band)
            if enter or leave: alerts.append(f'INDICATIVE top-{band} band vs {dec["asof"]}: entering {enter} leaving {leave}')
    except Exception as e:
        alerts.append(f'indicative score failed: {type(e).__name__}: {e}')
    # ---------- indicative books
    lastq = {c: dict(p=v['p'], d=v['d']) for c, v in st['last'].items()}
    for c, px in q.items(): lastq[c] = dict(p=float(px), d=sess + ' (delayed quote)')
    md = [f'# Intraday look — {loc:%a %d %b %Y %H:%M} Sydney ({tag})', '',
          f'**{P.HEADER}**', '',
          '**INDICATIVE, DELAYED.** EODHD delayed quotes (about 15-20 minutes). **No trading decision is made intraday**: rules v1.3 decide on closing prices only; '
          'intraday rules are untested. Pending paper orders still fill at the close of their day under v1.3 D/E.', '',
          f"Last booked close: {st['last_processed']}. Quotes from this session: {len(fresh)}/{len(df)}.", '',
          '| Book | NAV at last close | NAV indicative | Change | Pending orders |', '|---|---|---|---|---|']
    for b in main_books + st['cmps']:
        n0 = P.nav_of(b, st['last']); n1 = P.nav_of(b, lastq)
        po = len(b.get('orders', b.get('pending', [])))
        md.append(f"| {b['id']} | {n0:,.2f} | {n1:,.2f} | {n1 / n0 - 1:+.2%} | {po} |")
    hl = []
    for b in st['books'][:3]:
        for h in b['holdings'].values():
            c = h['code']; sh = P.shares_of(h); cost = P.cost_of(h); p0 = st['last'].get(c, {}).get('p'); p1 = lastq.get(c, {}).get('p')
            if p0 and p1: hl.append(f"| {b['id']} | {c} | {sh:,.0f} | {p0} | {p1} | {p1 / p0 - 1:+.2%} | {sh * p1 - cost:,.2f} |")
    if hl: md += ['', '| Book | Code | Shares | Last close | Quote | Day | P&L A$ (indicative) |', '|---|---|---|---|---|---|---|'] + hl
    pq = []
    for b in st['books'][:3]:
        for o in b['orders']:
            pq.append(f"| {b['id']} | {o['type']} | {o['code']} | {q.get(o['code'], '')} | fills at the close |")
    if pq: md += ['', '| Book | Pending | Code | Latest quote | Note |', '|---|---|---|---|---|'] + pq
    md += ['', '## Alerts this look', ''] + ([f'- {x}' for x in alerts] or ['- none'])
    open(P.PAPER + '/INTRADAY.md', 'w').write('\n'.join(md) + '\n')
    open(P.PAPER + '/alerts_latest.md', 'w').write(f'# Alerts {tag} (indicative, delayed; no trading decision)\n\n' + ('\n'.join(f'- {x}' for x in alerts) or '- none') + '\n')
    with open(P.PAPER + '/alerts.md', 'a') as f:
        if os.path.getsize(P.PAPER + '/alerts.md') == 0:
            f.write('# Intraday alert log (append-only). Indicative, delayed quotes. NO trading decision is made intraday (v1.3 decides on closes).\n\n')
        for x in alerts: f.write(f'- {tag} {x}\n')
    log(f'{len(alerts)} alerts; INTRADAY.md written')

if __name__ == '__main__':
    main()
