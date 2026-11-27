"""Shared paths and helpers for the data_foundation build.

All upstream sources are opened READ-ONLY. Nothing in this package writes outside
data_foundation/out (or a caller-supplied output directory).
Run every script with `python3 -I` (isolated mode); scripts add their own directory to sys.path.
"""
import os, hashlib, json, datetime as _dt
import numpy as np, pandas as pd

S = os.environ.get('DF_SCRATCH', '/tmp/claude-0/-home-user/9b07f0f1-d4d4-53b2-b61e-ed91f2d4b167/scratchpad')
ROOT = os.path.join(S, 'data_foundation')
OUT = os.path.join(ROOT, 'out')
CS = os.path.join(S, 'company_study')            # read-only
CS_DATA = os.path.join(CS, 'data')
FLAGS = os.path.join(S, 'flags')                  # read-only
DB = os.path.join(S, 'company_db', 'db', 'asx_company.duckdb')  # read-only
NICHE_OUT = os.path.join(S, 'niche', 'out')       # read-only (only used to measure the old defect)

D1_END = pd.Timestamp('2024-05-31')               # last date of the rs77 raw (unadjusted) file
CAL_START = '1997-01-01'
CAL_END = '2026-12-31'


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def write_hashes(paths, out_path):
    with open(out_path, 'w') as f:
        for p in sorted(paths):
            if os.path.exists(p):
                f.write(f'{sha256_file(p)}  {os.path.relpath(p, ROOT)}\n')


def now_utc():
    return _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def md_table(df, floatfmt='{:,.0f}'):
    cols = list(df.columns)
    lines = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '|' + '|'.join(['---'] * len(cols)) + '|']
    for _, r in df.iterrows():
        vals = []
        for v in r.values:
            if isinstance(v, (float, np.floating)):
                vals.append('' if np.isnan(v) else floatfmt.format(v))
            else:
                vals.append(str(v))
        lines.append('| ' + ' | '.join(vals) + ' |')
    return '\n'.join(lines)


def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2, default=str)
