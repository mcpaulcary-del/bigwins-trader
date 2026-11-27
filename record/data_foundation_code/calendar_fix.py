"""Fix (b): ASX trading calendar.

Primary calendar: exchange_calendars 'XASX'. Cross-checks:
  1. the price file itself: on a genuine closure the vendor rows are copies of the previous row
     (open/high/low/close/volume all identical) for (almost) every code;
  2. the hand-made list in research2/55 section 7 (seven holiday copies 1999-2009, weekend rows,
     2024-25 holidays).
Policy:
  * a row dated on a weekend is removed;
  * a row dated on a weekday that XASX says was closed is removed when the date-level copy share
    is >= COPY_CONFIRM (vendor copy) or when the date carries <= ISOLATED_MAX rows in that source
    (misdated rows; a real trading day has hundreds) -- otherwise it is KEPT and logged as a
    disagreement for review;
  * an XASX session on which >= VENDOR_COPY_DAY of rows are copies is kept but flagged
    `copy_day` (data missing for that day; report 55's BW-06 WARN rule uses 5%);
  * XASX sessions with no rows at all are listed as market-wide data gaps.
"""
import numpy as np, pandas as pd

COPY_CONFIRM = 0.5
VENDOR_COPY_DAY = 0.5
WARN_COPY_DAY = 0.05
ISOLATED_MAX = 20

# research2/55 section 7 / research2/54 section 4.2 -- independent hand list of known bad dates
R55_HOLIDAY_COPIES = ['1999-12-27', '1999-12-28', '2000-12-25', '2000-12-26', '2001-01-01',
                      '2002-03-29', '2004-06-14', '2005-12-27', '2009-01-01']
R55_WEEKEND = ['2018-03-17']


def xasx_sessions(start='1997-01-01', end='2026-12-31'):
    import exchange_calendars as xc
    cal = xc.get_calendar('XASX', start=start, end=end)
    s = pd.DatetimeIndex(cal.sessions)
    if s.tz is not None:
        s = s.tz_localize(None)
    return s.as_unit('us')


def copy_flags(df, key='code', cols=('o', 'h', 'l', 'c', 'v')):
    """Row-level: True where every column in `cols` equals the previous row of the same key
    (df must be sorted by key, date) and volume > 0 (a zero-volume carry is a different defect)."""
    g = df.groupby(key, sort=False)
    same = np.ones(len(df), bool)
    for k in cols:
        if k not in df.columns:
            continue
        same &= (df[k].values == g[k].shift(1).values)
    if 'v' in df.columns and 'v' in cols:
        same &= (df['v'].values > 0)
    return same


def date_table(df, sessions, key='code', cols=('o', 'h', 'l', 'c', 'v')):
    """Per-date evidence table. df: long rows with key, date and price columns."""
    df = df.sort_values([key, 'date'])
    cp = copy_flags(df, key, cols)
    t = pd.DataFrame({'date': df['date'].values, 'copy': cp}).groupby('date').agg(n=('copy', 'size'), copy_share=('copy', 'mean'))
    t['weekday'] = t.index.day_name()
    t['weekend'] = t.index.dayofweek >= 5
    t['xasx_open'] = t.index.isin(sessions)
    return t


def decide(t):
    """Add decision columns to a date_table."""
    t = t.copy()
    closed = ~t.xasx_open
    t['action'] = 'keep'
    t.loc[t.weekend, 'action'] = 'remove:weekend'
    hol = closed & ~t.weekend
    t.loc[hol & (t.copy_share >= COPY_CONFIRM), 'action'] = 'remove:holiday_copy'
    # a handful of rows on a closed weekday cannot be a market-wide trading day: misdated vendor rows
    t.loc[hol & (t.copy_share < COPY_CONFIRM) & (t.n <= ISOLATED_MAX), 'action'] = 'remove:isolated_rows_on_closed_day'
    t.loc[hol & (t.copy_share < COPY_CONFIRM) & (t.n > ISOLATED_MAX), 'action'] = 'keep:DISAGREE_xasx_closed_but_not_copy'
    t['copy_day'] = t.xasx_open & (t.copy_share >= VENDOR_COPY_DAY)
    t['copy_warn'] = t.xasx_open & (t.copy_share >= WARN_COPY_DAY)
    t['in_r55_list'] = t.index.strftime('%Y-%m-%d').isin(R55_HOLIDAY_COPIES + R55_WEEKEND)
    return t


def remove_rows(df, t):
    """Return (kept, removed) given a decided date table."""
    bad = set(t.index[t.action.str.startswith('remove')])
    m = df['date'].isin(bad)
    return df[~m].copy(), df[m].copy()


def missing_sessions(dates_present, sessions, start, end):
    s = sessions[(sessions >= pd.Timestamp(start)) & (sessions <= pd.Timestamp(end))]
    return s[~s.isin(pd.DatetimeIndex(dates_present))]
