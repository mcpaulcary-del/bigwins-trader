"""BF-D88: "Odds for shares like this (history)" on the share pages (owner request
25 Nov 2026). Descriptive history from ``config/odds_table_v1.csv``; read-only, no
strategy rule or parameter changes."""

from __future__ import annotations

import csv
import math
import re
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from trader import odds as od
from trader.dashboard import Dashboard, Sources
from trader.journal import Journal, read_only_engine

REPO = Path(__file__).resolve().parents[1]
TABLE = REPO / "config" / od.ODDS_FILE


def _table() -> od.OddsTable:
    t = od.load_odds(REPO / "config")
    assert t is not None
    return t


# ---------------------------------------------------------------- the lookup


@pytest.mark.parametrize(
    ("rank", "band"),
    [(1, (1, 100)), (100, (1, 100)), (101, (101, 300)), (300, (101, 300)), (301, (301, 600)),
     (450.5, (301, 600)), (600, (301, 600)), (601, (601, 1000)), (1000, (601, 1000)),
     (1001, None), (0, None), (None, None), (math.nan, None)],
)  # fmt: skip
def test_BF_D88_band_edges(rank: float | None, band: tuple[int, int] | None) -> None:
    assert od.band_of(rank) == band


@pytest.mark.parametrize(
    ("pct", "q"),
    [(0.0, 1), (0.01, 1), (0.2, 1), (0.2001, 2), (0.6, 3), (0.8, 4), (0.8001, 5), (1.0, 5),
     (None, None), (math.nan, None), (1.2, None), (-0.1, None)],
)  # fmt: skip
def test_BF_D88_quintile_edges_match_the_strategy_top_fifth(pct: float | None,
                                                            q: int | None) -> None:  # fmt: skip
    assert od.quintile_of(pct) == q


def test_BF_D88_lookup_edge_ranks_and_missing_score() -> None:
    t = _table()
    for rank, lo in ((300, 101), (301, 301), (600, 301), (601, 601)):
        row = od.lookup(t, rank, 0.9)
        assert row is not None and row.band_lo == lo and row.quintile == 5
    assert od.lookup(t, 450, None) is None  # no score
    assert od.lookup(t, None, 0.9) is None  # no rank
    assert od.lookup(t, 1500, 0.9) is None  # outside the table
    assert od.lookup(None, 450, 0.9) is None  # no table
    assert od.lookup_band(t, 301, 0.5) == od.lookup(t, 450, 0.5)


# ---------------------------------------------------------------- the CSV


def test_BF_D88_csv_schema_and_no_per_company_rows() -> None:
    text = TABLE.read_text(encoding="utf-8")
    head = [x for x in text.splitlines() if x.startswith("#")]
    assert any("Built 20" in x for x in head) and any("build_odds_table.py" in x for x in head)
    assert any("no per-company rows" in x for x in head)
    assert any("not a trial, changes no strategy" in x for x in head)
    rows = list(csv.DictReader(x for x in text.splitlines() if not x.startswith("#")))
    assert tuple(rows[0].keys()) == od.COLUMNS
    # aggregated only: one row per (band, quintile), every value a number, no codes or prices
    assert len(rows) == len(od.BANDS) * 5
    assert {(int(r["band_lo"]), int(r["quintile"])) for r in rows} == {
        (lo, q) for lo, _ in od.BANDS for q in range(1, 6)}  # fmt: skip
    for r in rows:
        for v in r.values():
            float(v)  # raises on any text (a code, a name, a date)
        n, c = int(r["n"]), int(r["companies"])
        assert n >= 300 and 0 < c <= n and int(r["h1_n"]) + int(r["h2_n"]) == n
        assert float(r["p_double"]) <= float(r["p_up40"])
    assert not re.search(r"\b[A-Z]{3}\b", "\n".join(x for x in text.splitlines()
                                                     if not x.startswith("#")))  # fmt: skip
    assert len(text) < 10_000  # a small derived table
    t = _table()
    assert len(t.rows) == 20 and t.period == "Jan 2005 to Oct 2025" and t.built


def test_BF_D88_broken_or_missing_table_is_none(tmp_path: Path) -> None:
    assert od.load_odds(tmp_path) is None and od.load_odds(None) is None
    good = TABLE.read_text(encoding="utf-8")
    for bad in (
        good.replace("p_halve,", "p_halve2,", 1),  # schema
        good + "1,100,1," + ",".join(["1"] * 16) + "\n",  # repeated cell
        good.replace(",4895,249,15.4,", ",4895,249,150.4,", 1),
    ):  # not a percentage
        (tmp_path / od.ODDS_FILE).write_text(bad, encoding="utf-8")
        with pytest.raises(ValueError):
            od.parse(bad)
        assert od.load_odds(tmp_path) is None


# ---------------------------------------------------------------- the card


def test_BF_D88_card_sentence_group_sample_halves_neutral() -> None:
    t = _table()
    row = od.lookup(t, 450, 0.95)
    assert row is not None
    h = od.card(t, row, date(2026, 11, 30))
    assert od.TITLE in h and "since 2005" in h
    assert re.search(r"\d+% rose 40% or more within a year, \d+% doubled, \d+% halved\. "
                     r"Median: (0|[+\u2212]\d+)%\.", h)  # fmt: skip
    # the caveat is in the sentence, not small grey text
    assert re.search(r"<p class='lead2'>[^<]*<b>Odds, not a forecast\. Past patterns can "
                     r"change\.</b></p>", h)  # fmt: skip
    assert "size rank 301\u2013600, score in the top fifth" in h and "30 Nov 2026" in h
    assert f"{row.n:,} stock-months from {row.companies:,} companies" in h
    assert "<details" in h and "2005\u20132015" in h and "2016\u20132025" in h
    assert f"{row.h1.n:,}" in h and f"{row.h2.n:,}" in h
    assert not re.search(r'class="[^"]*\b(up|down|pill|ok)\b', h)  # no green "buy" styling
    assert "Not enough data for odds" in od.card(t, None)
    assert od.summary(row).startswith("Of shares like this since 2005: ")


def test_BF_D88_card_escapes_text(tmp_path: Path) -> None:
    text = TABLE.read_text(encoding="utf-8").replace("# Built 2", "# Built <script>2", 1)
    t = od.parse(text)
    row = od.lookup(t, 450, 0.5)
    h = od.card(t, row)
    assert "<script>" not in h and "&lt;script&gt;" in h
    h = od.card(t, None, why_missing="<img src=x onerror=1>")
    assert "<img" not in h and "&lt;img src=x onerror=1&gt;" in h


def _journal(tmp: Path) -> Path:
    p = tmp / "j.sqlite"
    w = Journal.sqlite(str(p))
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    band = [["AAA", 0.5, 0.4, 0.3, 0.97, 1], ["B<B", 0.4, 0.3, 0.2, 0.85, 2],
            ["CCC", 0.1, 0.1, 0.1, None, 3]]  # fmt: skip
    w.mark_job("emg2list:2025-12-31", {"as_of": "2025-12-31", "targets": ["AAA", "B<B"],
                                       "band_c": band}, t0)  # fmt: skip
    w.mark_job("emg2list:2026-01-30", {"as_of": "2026-01-30", "targets": ["AAA", "B<B"],
                                       "band_c": band[:1] + band[2:]}, t0)  # fmt: skip
    w.engine.dispose()
    return p


def _dash(p: Path, cfg: Path | None) -> Dashboard:
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{p}"))
    days = [d for d in (date(2025, 11, 3) + timedelta(days=k) for k in range(140))
            if d.weekday() < 5]  # fmt: skip
    now = datetime(2026, 3, 10, 1, 0, tzinfo=UTC)
    src = Sources(j, clock=lambda: now, today=lambda: now.date(), sessions=lambda: days,
                  index=lambda: [(d, 100.0) for d in days],
                  prices=lambda code: [(d, 1.0 + 0.002 * k) for k, d in enumerate(days)],
                  forecast_dir=cfg)  # fmt: skip
    return Dashboard(src)


def test_BF_D88_share_page_shows_the_card_or_not_enough_data(tmp_path: Path) -> None:
    p = _journal(tmp_path)
    cfg = tmp_path / "config"
    cfg.mkdir()
    shutil.copy(TABLE, cfg)
    d = _dash(p, cfg)
    st, _, b = d.respond("GET", "/shares/AAA", {})
    t = b.decode()
    assert st == 200 and od.TITLE in t and "score in the top fifth" in t
    assert "30 Jan 2026 decision" in t and "Odds, not a forecast" in t
    assert t.index("Rank history") < t.index(od.TITLE)
    # no longer in band C at the latest decision: no size rank or score -> no odds
    st, _, b = d.respond("GET", "/shares/B%3CB", {})
    t = b.decode()
    assert st == 200 and "Not enough data for odds" in t and "<B<" not in t
    # no table: the rest of the page still works
    st, _, b = _dash(p, tmp_path / "none").respond("GET", "/shares/AAA", {})
    assert st == 200 and "Not enough data for odds" in b.decode() and "Rank history" in b.decode()


def test_BF_D88_missing_score_in_the_record_is_not_enough_data(tmp_path: Path) -> None:
    from trader.share_pages import ShareCtx, odds_section

    j = Journal.sqlite()
    lists = [(date(2026, 1, 30), {"band_c": [["CCC", 0.1, 0.1, 0.1, None, 3]]})]
    ctx = ShareCtx(j, "EMG2_18_PAPER", datetime(2026, 2, 2, tzinfo=UTC), odds=_table())
    assert "Not enough data for odds" in odds_section(ctx, "CCC", lists)
    assert "Not enough data for odds" in odds_section(ctx, "AAA", [])


# ---------------------------------------------------------------- the strategy is frozen


def test_BF_D88_strategy_hash_and_settings_hash_unchanged(tmp_path: Path) -> None:
    """A read-only display of descriptive history: the strategy hash and the strategy
    settings hash are exactly as before (91cbaad)."""
    from tests.test_bf_d90_e5 import _strategy_hash_without_e5  # BF-D90 (jan2027-fixes)
    from trader.strategy_version import config_hash, is_trading_path
    from trader.yamlio import load_yaml

    assert _strategy_hash_without_e5(tmp_path) == "a50dfa0b4eb1"
    cfg = load_yaml((REPO / "config" / "bfast.yaml").read_text()) or {}
    cfg["live_emg2_20"].pop("e5")
    assert config_hash(cfg) == "02589a19293b"
    assert not is_trading_path("research/odds_table/build_odds_table.py")  # never deployed


def test_BF_D88_trader_never_reads_the_table() -> None:
    """Only the screens import trader.odds; nothing that decides or trades does."""
    imp = re.compile(r"^\s*(from trader(\.odds)? import .*\bodds\b|import trader\.odds)", re.M)
    users = sorted(f.name for f in (REPO / "trader").rglob("*.py")
                   if imp.search(f.read_text(encoding="utf-8")))  # fmt: skip
    assert users == ["dashboard.py", "share_pages.py"]
