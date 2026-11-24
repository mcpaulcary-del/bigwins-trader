"""Odds for shares like this (BF-D88; owner request 25 Nov 2026; read-only, descriptive).

The share pages show, for the share's size band and score quintile, how often shares
like it rose 40% or more, doubled or halved within 12 months in the past, and their
median 12-month return. The numbers come from ``config/odds_table_v1.csv``: a small
table of aggregated percentages and counts, built offline by
``research/odds_table/build_odds_table.py`` from the research panel (no prices and no
per-company rows). The trader never reads it; nothing here decides or trades.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from trader.webui import e, section

ODDS_FILE = "odds_table_v1.csv"
BANDS: tuple[tuple[int, int], ...] = ((1, 100), (101, 300), (301, 600), (601, 1000))
HALF_KEYS = ("n", "p_up40", "p_double", "p_halve", "median")
COLUMNS = (
    "band_lo", "band_hi", "quintile", "n", "companies", "p_up40", "p_double", "p_halve",
    "median", *(f"{h}_{k}" for h in ("h1", "h2") for k in HALF_KEYS),
)  # fmt: skip
QUINTILE_LABEL = {5: "in the top fifth", 4: "in the second fifth from the top",
                  3: "in the middle fifth", 2: "in the second fifth from the bottom",
                  1: "in the bottom fifth"}  # fmt: skip
TITLE = "Odds for shares like this (history)"
CAVEAT = "Odds, not a forecast. Past patterns can change."
NO_DATA = "Not enough data for odds."


@dataclass(frozen=True)
class Half:
    n: int
    p_up40: float
    p_double: float
    p_halve: float
    median: float


@dataclass(frozen=True)
class OddsRow:
    band_lo: int
    band_hi: int
    quintile: int
    n: int
    companies: int
    p_up40: float
    p_double: float
    p_halve: float
    median: float
    h1: Half
    h2: Half


@dataclass(frozen=True)
class OddsTable:
    rows: dict[tuple[int, int], OddsRow]  # (band_lo, quintile) -> row
    built: str = ""  # from the "# Built <date>" header line
    period: str = ""  # from the "formations <a> to <b>" header text


def band_of(rank: float | None) -> tuple[int, int] | None:
    """The size band of a traded-value rank (1 = largest); ``None`` outside 1..1000."""
    if rank is None or not math.isfinite(rank):
        return None
    for lo, hi in BANDS:
        if lo - 1 < rank <= hi:
            return lo, hi
    return None


def quintile_of(pct: float | None) -> int | None:
    """1..5 from a score percentile in (0, 1]; 5 = the top fifth (> 0.80), as the
    strategy's own top fifth (``score_pct > 0.8``)."""
    if pct is None or not math.isfinite(pct) or not 0.0 <= pct <= 1.0:
        return None
    return min(5, max(1, math.ceil(round(pct * 5, 9))))


def _num(row: dict[str, str], k: str) -> float:
    v = float(row[k])
    if not math.isfinite(v):
        raise ValueError(f"{k}: not a number")
    return v


def parse(text: str) -> OddsTable:
    """The table from the CSV text; ``ValueError`` on a wrong schema or value."""
    lines = text.splitlines()
    head = [x for x in lines if x.startswith("#")]
    rd = csv.DictReader([x for x in lines if x.strip() and not x.startswith("#")])
    if tuple(rd.fieldnames or ()) != COLUMNS:
        raise ValueError(f"columns {rd.fieldnames} != {COLUMNS}")
    rows: dict[tuple[int, int], OddsRow] = {}
    for r in rd:
        band = (int(r["band_lo"]), int(r["band_hi"]))
        q = int(r["quintile"])
        if band not in BANDS or q not in QUINTILE_LABEL or (band[0], q) in rows:
            raise ValueError(f"bad or repeated cell {band} q{q}")
        pcts = [_num(r, k) for k in ("p_up40", "p_double", "p_halve")]
        if not all(0.0 <= p <= 100.0 for p in pcts):
            raise ValueError("a percentage is outside 0..100")
        halves = [Half(int(r[f"{h}_n"]), *(_num(r, f"{h}_{k}") for k in HALF_KEYS[1:]))
                  for h in ("h1", "h2")]  # fmt: skip
        rows[band[0], q] = OddsRow(
            band[0], band[1], q, int(r["n"]), int(r["companies"]), pcts[0], pcts[1], pcts[2],
            _num(r, "median"), halves[0], halves[1],
        )  # fmt: skip
    built = next((x.split("Built ", 1)[1].split()[0] for x in head if "Built " in x), "")
    per = next((x.split("formations ", 1)[1].split(",")[0] for x in head if "formations " in x), "")
    return OddsTable(rows, built, _period(per))


def _period(text: str) -> str:
    """ "2005-01 to 2025-10" -> "Jan 2005 to Oct 2025" (unchanged if it does not parse)."""
    try:
        a, b = (date.fromisoformat(x.strip() + "-01") for x in text.split(" to "))
    except ValueError:
        return text
    return f"{a:%b %Y} to {b:%b %Y}"


def load_odds(config_dir: Path | None) -> OddsTable | None:
    """``config/odds_table_v1.csv``; ``None`` when missing or broken (the card then says
    so; the page never fails because of it)."""
    if config_dir is None:
        return None
    try:
        return parse((Path(config_dir) / ODDS_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def lookup(table: OddsTable | None, rank: float | None, pct: float | None) -> OddsRow | None:
    """The cell of a traded-value rank and score percentile; ``None`` when either is
    missing or outside the table."""
    band = band_of(rank)
    return None if band is None else lookup_band(table, band[0], pct)


def lookup_band(table: OddsTable | None, band_lo: int, pct: float | None) -> OddsRow | None:
    """The cell of a known size band (its first rank) and a score percentile."""
    q = quintile_of(pct)
    if table is None or q is None:
        return None
    return table.rows.get((band_lo, q))


def _p(x: float) -> str:
    return f"{x:.0f}%"


def _med(x: float) -> str:
    r = round(x)
    return "0%" if r == 0 else f"{'+' if r > 0 else '\u2212'}{abs(r)}%"


def _since(table: OddsTable) -> str:
    m = re.search(r"\b(19|20)\d\d\b", table.period)
    return m.group(0) if m else "2005"


def _built(text: str) -> str:
    try:
        return f"{date.fromisoformat(text):%d %b %Y}"
    except ValueError:
        return text or "offline"


def bucket_text(row: OddsRow) -> str:
    return f"size rank {row.band_lo}\u2013{row.band_hi}, score {QUINTILE_LABEL[row.quintile]}"


def summary(row: OddsRow, since: str = "2005") -> str:
    """One plain sentence (also the compact form)."""
    return (f"Of shares like this since {since}: {_p(row.p_up40)} rose 40% or more within a "
            f"year, {_p(row.p_double)} doubled, {_p(row.p_halve)} halved. "
            f"Median: {_med(row.median)}.")  # fmt: skip


def card(
    table: OddsTable | None, row: OddsRow | None, as_of: date | None = None, why_missing: str = ""
) -> str:
    """The share page's odds card (``row`` from ``lookup`` / ``lookup_band``): neutral
    colours, the caveat in the sentence, the group, the sample and the two halves in a
    fold-out."""
    if table is None or row is None:
        extra = f" {why_missing}" if why_missing else ""
        return section(TITLE, f"<p class='muted'>{e(NO_DATA + extra)}</p>", cls="odds")
    when = f" at the {as_of:%d %b %Y} decision" if as_of else ""
    lead = f"<p class='lead2'>{e(summary(row, _since(table)))} <b>{e(CAVEAT)}</b></p>"
    bucket = f"<p>Its group{e(when)}: <b>{e(bucket_text(row))}</b>.</p>"
    period = table.period.replace(" to ", " \u2013 ") if table.period else "2005\u20132025"
    sample = (f"<p class='caption'>Based on {row.n:,} stock-months from {row.companies:,} "
              f"companies, {e(period)}. Each share is counted once a month, so months "
              "overlap; the return is over the next 12 months and includes shares that "
              "failed or were taken over.</p>")  # fmt: skip

    def tr(label: str, a: str, b: str) -> str:
        return f"<tr><td>{e(label)}</td><td class='r'>{e(a)}</td><td class='r'>{e(b)}</td></tr>"

    h1, h2 = row.h1, row.h2
    halves = (
        "<details class='about'><summary>Earlier and later years (stability check)"
        "</summary><table><thead><tr><th></th><th class='r'>2005\u20132015</th>"
        "<th class='r'>2016\u20132025</th></tr></thead><tbody>"
        + tr("Rose 40% or more", _p(h1.p_up40), _p(h2.p_up40))
        + tr("Doubled", _p(h1.p_double), _p(h2.p_double))
        + tr("Halved", _p(h1.p_halve), _p(h2.p_halve))
        + tr("Median", _med(h1.median), _med(h2.median))
        + tr("Stock-months", f"{h1.n:,}", f"{h2.n:,}")
        + "</tbody></table><p class='caption'>If the two columns differ a lot, the odds "
        f"are less reliable. Table built {e(_built(table.built))} from research data "
        "(aggregated counts only).</p></details>"
    )
    return section(TITLE, lead + bucket + sample + halves, cls="odds")
