"""BF-D66: "Expected vs actual". The forecast bands are read from the CSV files (fb1
format), a missing file or bucket means "not available yet", and the share screens are
read-only GET pages."""

from __future__ import annotations

import re
import shutil
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from trader import forecast as fc
from trader.dashboard import Dashboard, Sources
from trader.journal import Journal, read_only_engine
from trader.orders import Side

REPO = Path(__file__).resolve().parents[1]
HEAD = ("score_bucket,months_since_entry,p10,p25,p50,p75,p90,n_obs,period_start,period_end,"
        "method_version\n")  # fmt: skip


def _write(d: Path, name: str, rows: list[str]) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(HEAD + "".join(r + "\n" for r in rows), encoding="utf-8")
    return d


def test_BF_D66_repo_band_files_load_with_every_bucket_and_month() -> None:
    for bench in ("a200", "bandc"):
        b = fc.load_bands(REPO / "config", bench)
        assert b is not None and b.method == "fb1"
        assert b.period == ("2005-01-31", "2026-10-30")
        for k in fc.BUCKETS:
            rows = b.bucket(k)
            assert sorted(rows) == list(range(1, 13))
            assert all(list(r.q) == sorted(r.q) and r.n_obs > 0 for r in rows.values())
    a = fc.load_bands(REPO / "config", "a200")
    assert a is not None and a.bucket("top5")[12].q[2] == pytest.approx(-0.0932)
    bc = fc.load_bands(REPO / "config", "bandc")
    assert bc is not None and bc.means_12m["top5"] == pytest.approx(0.15)  # from the doc
    assert bc.means_12m["60_100"] == pytest.approx(-0.097)


def test_BF_D66_missing_file_bad_header_and_missing_buckets(tmp_path: Path) -> None:
    assert fc.load_bands(tmp_path, "a200") is None  # no file: "not available yet"
    assert fc.load_bands(None, "a200") is None
    (tmp_path / "forecast_bands_a200.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    assert fc.load_bands(tmp_path, "a200") is None  # not the fb format
    _write(tmp_path, "forecast_bands_a200.csv", [
        "top5,1,-0.2,-0.1,0.0,0.1,0.2,100,2005-01-31,2026-10-30,fb1",
        "top5,2,-0.3,-0.1,0.0,0.1,0.3,90,2005-01-31,2026-10-30,fb1",
        "top5,13,-0.3,-0.1,0.0,0.1,0.3,90,2005-01-31,2026-10-30,fb1",  # out of range
        "top5,3,0.3,-0.1,0.0,0.1,0.3,90,2005-01-31,2026-10-30,fb1",  # not in order
        "weird,1,-0.3,-0.1,0.0,0.1,0.3,90,2005-01-31,2026-10-30,fb1",  # unknown bucket
        "top20,1,-0.3,x,0.0,0.1,0.3,90,2005-01-31,2026-10-30,fb1",  # not a number
    ])  # fmt: skip
    b = fc.load_bands(tmp_path, "a200")
    assert b is not None
    assert sorted(b.bucket("top5")) == [1, 2]
    assert b.bucket("top20") == {} and b.bucket(None) == {} and b.bucket("60_100") == {}


def test_BF_D66_buckets_percentiles_and_actual_path() -> None:
    assert [fc.bucket_of(x) for x in (0.99, 0.9, 0.7, 0.5, 0.1, None)] == [
        "top5", "top20", "20_40", "40_60", "60_100", None]  # fmt: skip
    row = fc.BandRow(1, (-0.2, -0.1, 0.0, 0.1, 0.2), 10)
    assert fc.percentile_of(0.0, row) == pytest.approx(0.5)
    assert fc.percentile_of(0.05, row) == pytest.approx(0.625)
    assert fc.percentile_of(-0.5, row) == 0.05 and fc.percentile_of(0.5, row) == 0.95
    assert fc.percentile_text(0.68) == "at the 68th percentile"
    assert fc.percentile_text(0.05) == "below the 10th percentile"
    days = [date(2026, 1, 1) + timedelta(days=k) for k in range(120)]
    days = [d for d in days if d.weekday() < 5]
    px = [(d, 1.0 + 0.01 * k) for k, d in enumerate(days)]
    idx = [(d, 100.0) for d in days]
    act = fc.actual_path(px, idx, days[0], days[-1], days)
    assert [a.month for a in act] == [1, 2, 3]  # Jan, Feb, Mar month-ends (Apr is partial)
    assert act[0].day == date(2026, 1, 30) and act[0].excess == pytest.approx(act[0].stock)
    assert fc.high_52w([(days[0], 2.0), (days[1], 1.0)])[-1] == (days[1], 2.0)


def _journal(tmp: Path) -> Path:
    from trader.journal import FillRecord

    p = tmp / "j.sqlite"
    w = Journal.sqlite(str(p))
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    band = [["AAA", 0.5, 0.4, 0.3, 0.97, 1], ["BBB", 0.4, 0.3, 0.2, 0.85, 2],
            ["CCC", 0.1, 0.1, 0.1, 0.30, 3]]  # fmt: skip
    w.mark_job("emg2list:2025-12-31", {"as_of": "2025-12-31", "targets": ["AAA"],
                                       "band_c": band}, t0)  # fmt: skip
    w.mark_job("emg2list:2026-01-30", {"as_of": "2026-01-30", "targets": ["AAA"],
                                       "band_c": band}, t0)  # fmt: skip
    w.add_cash("EMG2_18_PAPER", "DEPOSIT", Decimal(10000), "t")
    w.add_fill(FillRecord("x1", None, "EMG2_18_PAPER", "AAA", Side.BUY, 10, Decimal("1.0"),
                             Decimal("6"), datetime(2026, 1, 2, 0, 0, tzinfo=UTC)))  # fmt: skip
    w.add_fill(FillRecord("x2", None, "EMG2_18_PAPER", "AAA", Side.SELL, 10, Decimal("1.2"),
                          Decimal("6"), datetime(2026, 2, 20, 0, 0, tzinfo=UTC)))  # fmt: skip
    w.engine.dispose()
    return p


def _dash(p: Path, cfg: Path | None) -> Dashboard:
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{p}"))
    days = [date(2025, 11, 3) + timedelta(days=k) for k in range(140)]
    days = [d for d in days if d.weekday() < 5]
    now = datetime(2026, 3, 10, 1, 0, tzinfo=UTC)

    def prices(code: str) -> list[tuple[date, float]]:
        return [(d, 1.0 + 0.002 * k) for k, d in enumerate(days)] if code != "ZZZ" else []

    src = Sources(j, clock=lambda: now, today=lambda: now.date(), sessions=lambda: days,
                  index=lambda: [(d, 100.0) for d in days], prices=prices,
                  forecast_dir=cfg)  # fmt: skip
    return Dashboard(src)


def test_BF_D66_share_screens_show_range_or_not_available(tmp_path: Path) -> None:
    if not hasattr(Journal, "add_fill"):
        pytest.skip("no fill writer in this journal")
    p = _journal(tmp_path)
    cfg = tmp_path / "config"
    cfg.mkdir()
    shutil.copy(REPO / "config" / "forecast_bands_a200.csv", cfg)
    d = _dash(p, cfg)
    st, _, b = d.respond("GET", "/shares", {})
    page = b.decode()
    assert st == 200 and 'data-filter="sold"' in page and 'data-filter="passed"' in page
    assert 'href="/shares/AAA"' in page and 'href="/shares/BBB"' in page
    assert 'href="/shares/CCC"' not in page  # bottom of band C, never flagged
    st, _, b = d.respond("GET", "/shares/BBB", {})
    t = b.decode()
    assert st == 200 and "Never bought" in t and "Rank history" in t
    assert "not a price prediction" in t and "big winners" in t and "18 shares" in t
    assert "About this chart" in t and 'href="/forecast-method"' in t
    assert re.search(r"Tracking <b>(at the \d+\w\w|below|above)", t)
    assert t.count("data-tip=") > 12 and "<form" not in t
    assert 'data-bench="bandc"' not in t  # only the ASX 200 file is there
    st, _, b = d.respond("GET", "/shares/AAA", {})
    t = b.decode()
    assert st == 200 and "Price history" in t and "What happens next" in t
    assert "Sold</b> on 20 Feb 2026" in t and "Realised result:</b> +20.0%" in t
    assert "At the sale it was" in t
    assert d.respond("GET", "/shares/NOPE", {})[0] == 404
    assert d.respond("POST", "/shares/BBB", {})[0] == 405  # read-only
    # no bands file: "not available yet", the rest of the sheet still works
    d2 = _dash(p, tmp_path / "empty")
    st, _, b = d2.respond("GET", "/shares/BBB", {})
    assert st == 200 and "Not available yet" in b.decode() and "Rank history" in b.decode()


def test_BF_D66_method_note_is_rendered_in_app_escaped(tmp_path: Path) -> None:
    from trader.share_pages import md_to_html

    h = md_to_html("# T\n\n**bold** `c` <script>x</script>\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
                   "\n* one\n  more\n* two\n")  # fmt: skip
    assert "<h2>T</h2>" in h and "<b>bold</b>" in h and "<code>c</code>" in h
    assert "<script>" not in h and "&lt;script&gt;" in h
    assert "<table>" in h and "<td>1</td>" in h and "<li>one more</li>" in h
    p = _journal(tmp_path) if hasattr(Journal, "add_fill") else tmp_path / "x.sqlite"
    if not p.exists():
        Journal.sqlite(str(p)).engine.dispose()
    st, _, b = _dash(p, REPO / "config").respond("GET", "/forecast-method", {})
    assert st == 200 and "Forecast bands (method fb1)" in b.decode()
