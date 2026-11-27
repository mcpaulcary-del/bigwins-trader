# research_dip keyword classifier (PREREG 4a) + dossier builder (4b). No prices used.
import re, json, os, glob, numpy as np, pandas as pd
TEMP = {'T_EARN': r'earnings|results|quarter|\bq[1-4]\b|guidance|outlook|forecast|misses|\bmiss\b|revenue|sales|profit|subscriber|margin|estimates',
 'T_MGMT': r'\bceo\b|\bcfo\b|chief executive|resign|steps down|step down|stepping down|oust|depart|\bfired\b|chairman|succession',
 'T_OPS': r'outage|glitch|cyber|hack|breach|\bstrike\b|shutdown|shut down|production halt|suspends production|delay|grounded|\bfire\b|flood|supply chain',
 'T_ONEOFF': r'write-?down|write-?off|impairment|one-off|one-time|\bcharge\b|trading loss',
 'T_SHORT': r'short[- ]seller|short report|hindenburg|muddy waters|citron|viceroy|spruce point|grizzly research|kerrisdale|gotham city|culper',
 'T_LEGAL': r'lawsuit|\bsued\b|\bsues\b|probe|investigat|inquiry|\bfine[ds]?\b|penalt|antitrust|settlement|class action|regulator|subpoena|allegation',
 'T_ANALYST': r'downgrade|price target|cut to (neutral|sell|hold|underperform)',
 'T_MACRO': r'tariff|sell-?off|\brout\b|recession|market plunge|stocks (fall|tumble|slide|sink)'}
FUND = {'F_FRAUD': r'fraud|accounting (irregular|scandal|probe|error)|restate|misstat|falsif|embezzl|ponzi|auditor (resign|quit)|fabricat',
 'F_DILUTE': r'capital raising|equity raising|(share|stock|equity|secondary|public|notes) offering|placement|rights issue|entitlement offer|to raise \$|raises \$|raising \$|convertible|dilut|at-the-market',
 'F_STRUCT': r'bankrupt|chapter 11|insolven|voluntary administration|receivership|liquidat|going concern|\bdefault|bank run|deposit (flight|outflow)|seized|collapse',
 'F_CONTRACT': r'(loses|lost|losing|cancel\w*|terminat\w*) .{0,40}(contract|agreement|partnership|deal)|licen[cs]e .{0,30}(revok|suspend|cancel|strip)|(revok|suspend|cancel|strip)\w* .{0,30}licen[cs]e',
 'F_PRODUCT': r'recall|trial .{0,30}(fail|miss|halt|stop)|(fail|miss|halt)\w* .{0,40}(trial|study|endpoint)|complete response letter|fda (reject|declin)|clinical hold|safety (concern|signal)',
 'F_BAN': r'\bban(s|ned)?\b|prohibit|blacklist|export (restriction|curb|control)|sanction|delist'}
TEMP = {k: re.compile(v) for k, v in TEMP.items()}; FUND = {k: re.compile(v) for k, v in FUND.items()}
def name_token(name):
    for w in re.findall(r"[A-Za-z0-9&']+", name):
        if len(w) >= 3 and w.lower() not in ('the',): return w
    return None
def focused(rec, name, cal):
    """articles inside the window and 'focused' per PREREG section 4. Returns list of (timestamp, title, body)"""
    mk = rec['mk']; d = np.datetime64(rec['date']); lo = (d - 1).astype('datetime64[s]')
    hi = np.datetime64(rec['next']).astype('datetime64[s]') + (np.timedelta64(13, 'h') if mk == 'US' else np.timedelta64(0, 'h'))
    A = []
    for a in rec['arts']:
        if not a['d'] or not a['t']: continue
        ts = np.datetime64(a['d'][:19])
        if lo <= ts < hi: A.append((ts, a['t'].strip(), a['n'], a['c']))
    A.sort(key=lambda x: x[0]); seen = set(); B = []
    for a in A:
        k = a[1].lower()[:60]
        if k in seen: continue
        seen.add(k); B.append(a)
    if mk == 'ASX': return [(a[0], a[1], a[3]) for a in B if a[2] <= 10]
    F5 = [a for a in B if a[2] <= 5]; tok = name_token(name); code = rec['code']
    rx = re.compile(r'\b' + re.escape(code) + r'\b'); G = [a for a in F5 if (tok and tok.lower() in a[1].lower()) or rx.search(a[1])]
    use = G if len(G) >= 3 else F5
    return [(a[0], a[1], a[2] if False else a[3]) for a in use]
def keyword(titles):
    n = len(titles)
    if n == 0: return 'NONE', '', 0, 0, 0
    ct = {k: 0 for k in TEMP}; cf = {k: 0 for k in FUND}; nT = nF = 0
    for t in titles:
        s = t.lower(); a = [k for k, r in TEMP.items() if r.search(s)]; b = [k for k, r in FUND.items() if r.search(s)]
        nT += bool(a); nF += bool(b)
        for k in a: ct[k] += 1
        for k in b: cf[k] += 1
    if nF >= 1 and nF >= 0.25 * nT and (nF >= 2 or n < 8): return 'FUND', max(cf, key=cf.get), n, nT, nF
    if nT >= 1: return 'TEMP', max(ct, key=ct.get), n, nT, nF
    return 'OTHER', '', n, nT, nF
