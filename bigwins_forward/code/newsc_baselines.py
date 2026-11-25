# NEWS-C rule-based baselines (KEY, RAISE, HALT, DIR). INFORMATION ONLY: feeds no paper line and no trade. No AI.
# Draft amendment AMENDMENT_info_NEWSC_v1.md s4 (from review_news/REVIEW.md, draft spec NEWS-C s4). Frozen at registration:
# any change to a regular expression or rule below changes this file's SHA-256 (recorded in every info_news ledger entry).
#   KEY   frozen regular expressions on the headline -> one of the 14 rubric types and a rating -2..+2.
#   RAISE a capital-raising notice for the code on any archived list-day among the trailing 63 (headline, or an Appendix 3B
#         "Proposed issue of securities" whose text shows a cash consideration, an SPP or a pro rata offer).
#   HALT  trading halt / pause / suspension, tracked to reinstatement (a halt also ends at the code's next non-halt
#         price-sensitive announcement or after 2 list-days; a suspension ends only at a reinstatement notice).
#   DIR   on-market director purchase from the Appendix 3Y text ("Nature of change"), on the day and in the trailing 63 list-days.
# Inputs are only the archive's list.csv files and the stored notice texts (asx_notices/<day>/). Nothing is downloaded.
import csv, json, os, re

S = '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad'
NOTICES = S + '/bigwins_forward/data/asx_notices'
WINDOW = 63                                    # list-days (one archived list = one ASX session)

# The 14 announcement types (shared with RUBRIC_v1.md; the rater must use exactly these strings).
TYPES = ['capital_raising', 'periodic_report', 'guidance_update', 'exploration_result', 'project_development', 'contract_customer',
         'regulatory_clinical', 'merger_acquisition', 'halt_suspension', 'financing_debt', 'dividend_capital_return',
         'governance_management', 'legal_dispute', 'other']

I = re.I
KEY_TYPE_RULES = [                             # first match wins
    ('halt_suspension', re.compile(r'trading halt|pause in trading|suspension|suspended|reinstatement', I)),
    ('governance_management', re.compile(r'results of (the )?(annual |extraordinary )?(general )?meeting|\bAGM\b|\bEGM\b|annual general meeting', I)),
    ('capital_raising', re.compile(r'placement|entitlement|share purchase plan|\bSPP\b|capital raising|\braising\b|rights issue|bookbuild|'
                                   r'cleansing|proposed issue of securities|underwrit|prospectus|offer booklet', I)),
    ('merger_acquisition', re.compile(r'takeover|scheme|bidder|target.?s statement|acqui|merger|divest|sale of|disposal|offer for', I)),
    ('legal_dispute', re.compile(r'litigation|court|class action|dispute|investigation|proceedings|arbitration|\bclaim', I)),
    ('guidance_update', re.compile(r'guidance|trading update|outlook|earnings update|profit (upgrade|downgrade|warning)', I)),
    ('periodic_report', re.compile(r'quarterly|half[- ]?year|full[- ]?year|annual report|\b(fy|hy|h1|h2|1h|2h|q[1-4])\s?\d{2}\b|results|'
                                   r'appendix 4[cde]|activities report|cash ?flow report', I)),
    ('regulatory_clinical', re.compile(r'approv|\bFDA\b|\bTGA\b|clinical|\btrial|patent|permit|licen[cs]e|regulat|clearance|CE mark|phase (1|2|3|I)', I)),
    ('project_development', re.compile(r'feasibility|\bPFS\b|\bDFS\b|\bBFS\b|scoping study|construction|production|commissioning|first (gold|ore|concentrate)|'
                                       r'mine plan|processing plant', I)),
    ('exploration_result', re.compile(r'drill|assay|intersect|intercept|mineralis|mineraliz|resource|reserve|grade|exploration|discovery|'
                                      r'geophysic|rock chip|soil|prospect\b|\bg/t\b|\bppm\b', I)),
    ('contract_customer', re.compile(r'contract|order|offtake|agreement|partner|customer|award|tender|supply|collaborat|\bMOU\b|memorandum', I)),
    ('financing_debt', re.compile(r'debt|facility|loan|\bnotes?\b|bond|refinanc|convertible|covenant|financing', I)),
    ('dividend_capital_return', re.compile(r'dividend|distribution|buy-?back|capital return|return of capital', I)),
    ('governance_management', re.compile(r'director|board|chair|\bCEO\b|managing director|\bCFO\b|appoint|resign|retire|company secretary|constitution', I)),
]
KEY_M2 = re.compile(r'suspension from (official )?quotation|suspended from|voluntary suspension|extension of (voluntary )?suspension|'
                    r'administrat(or|ion)|receiver|liquidat|going concern|insolv|covenant breach|default notice|delist', I)
KEY_NOT_M2 = re.compile(r'reinstatement|lifting of|removal from|recommence', I)
KEY_P2 = re.compile(r'takeover (offer|bid)|scheme implementation|scheme of arrangement|receipt of .{0,40}(offer|proposal)|unsolicited|'
                    r'recommended (cash )?(offer|proposal)', I)
KEY_M1 = re.compile(r'trading halt|pause in trading|downgrade|impairment|write[- ]?(down|off)|terminat|\bloss\b|delay|withdraw|'
                    r'cease|shortfall|below (guidance|expectations)|resign', I)
KEY_P1 = re.compile(r'upgrade|record|high[- ]grade|significant|award|contract|offtake|approv|first (gold|production|sales|revenue)|'
                    r'commence(s|ment of)? production|discover|binding|growth|increase|exceed|ahead of', I)


def key(headline):
    """KEY baseline for one headline -> (type, rating). Frozen."""
    h = headline or ''
    t = next((ty for ty, rx in KEY_TYPE_RULES if rx.search(h)), 'other')
    if KEY_M2.search(h) and not KEY_NOT_M2.search(h): r = -2
    elif KEY_P2.search(h): r = 2
    elif t == 'capital_raising' or KEY_M1.search(h): r = -1
    elif KEY_P1.search(h): r = 1
    else: r = 0
    return t, r


def codeday_rating(rs):
    """code-day unit (spec s5): the rating furthest from 0; a tie between signs gives 0; no ratings -> None"""
    rs = [r for r in rs if r is not None]
    if not rs: return None
    m = max(abs(r) for r in rs)
    if m == 0: return 0
    sg = {r for r in rs if abs(r) == m}
    return 0 if len(sg) > 1 else sg.pop()


# ---------------------------------------------------------------- RAISE
RAISE_HEAD = re.compile(r'placement|entitlement|share purchase plan|\bSPP\b|capital raising|\braising\b|rights issue|bookbuild|'
                        r'institutional offer|cleansing (notice|statement)|offer booklet|prospectus', I)
PROPOSED = re.compile(r'proposed issue of securities|appendix 3b', I)
CASH_YES = re.compile(r'issued for a cash\s+consideration\?\s*\n\s*Yes', I)
PROP_KIND = re.compile(r'1\.6 The Proposed issue is:\s*\n\s*(.+)', I)
ISSUE_PRICE = re.compile(r'issue price per \+?security\??\s*\n?\s*(?:AUD|A\$|\$)?\s*([0-9]*\.?[0-9]+)', I)


def raise_event(headline, text):
    """(is_raise, issue_price or None) for one announcement"""
    if RAISE_HEAD.search(headline or ''): pass
    elif PROPOSED.search(headline or '') and text:
        k = PROP_KIND.search(text); kind = k.group(1) if k else ''
        if not (CASH_YES.search(text) or re.search(r'purchase plan|pro rata|entitlement', kind, I)): return False, None
    else: return False, None
    p = ISSUE_PRICE.search(text or '')
    try: return True, (float(p.group(1)) if p else None)
    except ValueError: return True, None


# ---------------------------------------------------------------- DIR
DIR_HEAD = re.compile(r"director'?s?.? interest|appendix 3y", I)
NATURE = re.compile(r'nature of change', I)


def dir_on_market_buy(text):
    """True iff some 'Nature of change' block of an Appendix 3Y says an on-market purchase (template example text removed)"""
    if not text: return False
    L = text.split('\n')
    for i, l in enumerate(L):
        if not NATURE.search(l): continue
        blk = re.sub(r'\s+', ' ', ' '.join(L[i:i + 6]))
        blk = re.sub(r'nature of change', ' ', blk, flags=I)
        blk = re.sub(r'Example:\s*on[- ]market', ' ', blk, flags=I)          # the form's own example text
        if re.search(r'\bon[- ]?market\b', blk, I) and re.search(r'purchas|trade|buy|bought|acqui', blk, I) \
                and not re.search(r'\b(sale|sold|dispos)', blk, I):
            return True
    return False


# ---------------------------------------------------------------- HALT
HALT_START = re.compile(r'trading halt|pause in trading', I)
SUSP_START = re.compile(r'suspension from (official )?quotation|voluntary suspension|suspended from|extension of (voluntary )?suspension', I)
HALT_END = re.compile(r'reinstatement|lifting of (the )?(trading halt|suspension)|recommence(ment of)? trading|resumption of trading|'
                      r'removal from (official )?quotation', I)


def _minutes(tm):
    m = re.match(r'\s*(\d{1,2}):(\d\d)\s*([ap])m', tm or '', I)
    return 9999 if not m else (int(m.group(1)) % 12 + (12 if m.group(3).lower() == 'p' else 0)) * 60 + int(m.group(2))


def list_days(root=None):
    root = root or NOTICES
    return sorted(x for x in os.listdir(root) if re.fullmatch(r'\d{4}-\d\d-\d\d', x) and os.path.exists(f'{root}/{x}/list.csv'))


def read_list(day, root=None):
    with open(f'{root or NOTICES}/{day}/list.csv', newline='') as f: return list(csv.DictReader(f))


def text_of(day, code, ids_id, root=None):
    p = f'{root or NOTICES}/{day}/pdf/{code}_{ids_id}.txt'
    if not os.path.exists(p): return None
    with open(p, errors='replace') as f: return f.read()


def compute(day, universe, root=None):
    """baseline rows for list-day `day`: one per code in `universe` ({code: group}) with any announcement on `day` or halted at
    its end. Uses only archived list-days <= day."""
    root = root or NOTICES
    days = [d for d in list_days(root) if d <= day]
    if not days or days[-1] != day: raise ValueError(f'list-day {day} not archived')
    win = days[-WINDOW:]
    halt = {}                                  # code -> dict(kind, start, start_idx)
    raise_hist, dir_hist, today = {}, {}, {}
    for di, d in enumerate(days):
        rows = read_list(d, root)
        rows_sorted = sorted(enumerate(rows), key=lambda x: (_minutes(x[1]['time']), -x[0]))   # list is newest first
        for _, r in rows_sorted:
            c, h = r['code'], r['headline']
            if c not in universe: continue
            # HALT state machine
            st = halt.get(c)
            if HALT_END.search(h): halt.pop(c, None)
            elif SUSP_START.search(h):
                if not (st and st['kind'] == 'suspension'): halt[c] = dict(kind='suspension', start=d, start_idx=di)
            elif HALT_START.search(h):
                if not (st and st['kind'] == 'suspension'): halt[c] = dict(kind='halt', start=d, start_idx=di)
            elif st and st['kind'] == 'halt' and str(r.get('price_sensitive')) == '1' and (d, _minutes(r['time'])) > (st['start'], -1):
                halt.pop(c, None)
            if d not in win: continue
            ev_r = ev_d = False; price = None
            if RAISE_HEAD.search(h) or PROPOSED.search(h):
                ev_r, price = raise_event(h, text_of(d, c, r['ids_id'], root) if r.get('ids_id') else None)
            if DIR_HEAD.search(h) and r.get('ids_id'):
                ev_d = dir_on_market_buy(text_of(d, c, r['ids_id'], root))
            if ev_r: raise_hist.setdefault(c, []).append((d, price))
            if ev_d: dir_hist.setdefault(c, []).append(d)
            if d == day:
                t = today.setdefault(c, dict(anns=0, ps=0, key_all=[], key_ps=[], halt_event=0, raise_today=0, dir_today=0,
                                             no_3y_text=0))
                t['anns'] += 1; ty, kr = key(h); t['key_all'].append((ty, kr, _minutes(r['time'])))
                if str(r.get('price_sensitive')) == '1' or HALT_START.search(h) or SUSP_START.search(h):
                    t['ps'] += 1; t['key_ps'].append((ty, kr, _minutes(r['time'])))
                if HALT_START.search(h) or SUSP_START.search(h): t['halt_event'] = 1
                if ev_r: t['raise_today'] = 1
                if ev_d: t['dir_today'] += 1
                if DIR_HEAD.search(h) and text_of(d, c, r.get('ids_id', ''), root) is None: t['no_3y_text'] += 1
        # a halt lasts at most 2 list-days (then it is lifted or becomes a suspension, which has its own notice)
        for c in [c for c, s in halt.items() if s['kind'] == 'halt' and di - s['start_idx'] >= 2]: halt.pop(c)

    def agg(lst):
        if not lst: return None, None
        r = codeday_rating([x[1] for x in lst])
        pick = sorted((x for x in lst if x[1] == r), key=lambda x: x[2])
        return (pick[0][0] if pick else 'other'), r
    out = []
    for c in sorted(set(today) | {c for c in halt if c in universe}):
        t = today.get(c, dict(anns=0, ps=0, key_all=[], key_ps=[], halt_event=0, raise_today=0, dir_today=0, no_3y_text=0))
        ka_t, ka_r = agg(t['key_all']); kp_t, kp_r = agg(t['key_ps'])
        rh = raise_hist.get(c, []); hs = halt.get(c)
        out.append(dict(day=day, code=c, group=universe[c], n_announcements=t['anns'], n_rated_items=t['ps'],
                        key_type=kp_t, key_rating=kp_r, key_type_all=ka_t, key_rating_all=ka_r,
                        RAISE=int(bool(rh)), raise_today=t['raise_today'], raise_last_day=(rh[-1][0] if rh else None),
                        raise_last_issue_price=(rh[-1][1] if rh else None),
                        HALT=int(bool(t['halt_event'] or hs)), halt_event_today=t['halt_event'], halted_end_of_day=int(bool(hs)),
                        halt_kind=(hs['kind'] if hs else None), halt_start=(hs['start'] if hs else None),
                        halt_list_days=((len(days) - 1 - hs['start_idx']) if hs else None),
                        DIR=int(t['dir_today'] > 0), dir_buys_today=t['dir_today'], dir_buys_63=len(dir_hist.get(c, [])),
                        missing_3y_text=t['no_3y_text'], window_list_days=len(win), window_complete=int(len(win) >= WINDOW)))
    return out
