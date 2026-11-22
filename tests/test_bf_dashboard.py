"""BF-D37: the read-only phone dashboard. Renders with an empty database, an empty
journal and a journal written by a short run of the real app; it has no write path
(GET/HEAD only, a database session that refuses writes) and honours Tailscale log-ins."""

from __future__ import annotations

import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, insert, inspect, text
from sqlalchemy.exc import DBAPIError

from trader.bfast_cli import main as bf_main
from trader.constants import ASX_TZ
from trader.dashboard import (
    MANIFEST,
    READ_METHODS,
    Dashboard,
    Sources,
    collect,
    icon_png,
    render,
    serve,
)
from trader.dashboard_demo import Demo, build_demo
from trader.journal import FillRecord, Journal, cash_moves, read_only_engine
from trader.orders import Side
from trader.risk import SafetyLevel

NOW = datetime(2026, 11, 23, 9, 0, tzinfo=ASX_TZ)
CONFIG = Path(__file__).resolve().parent.parent / "config" / "bfast.yaml"


def _ro(path: Path) -> Journal:
    return Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{path}"))


def _dash(j: Journal, **kw: object) -> Dashboard:
    src = Sources(j, clock=lambda: NOW, today=lambda: NOW.date(), **kw)  # type: ignore[arg-type]
    return Dashboard(src)


def _get(d: Dashboard, path: str = "/", **headers: str) -> tuple[int, str]:
    status, _, body = d.respond("GET", path, headers)
    return status, body.decode(errors="replace")


@pytest.fixture(scope="module")
def demo(tmp_path_factory: pytest.TempPathFactory) -> Demo:
    return build_demo(tmp_path_factory.mktemp("demo") / "j.sqlite", days=30, random_twins=5)


def test_BF_D37_empty_database_shows_waiting_not_errors(tmp_path: Path) -> None:
    j = _ro(tmp_path / "none.sqlite")  # no tables at all (trader never started)
    status, page = _get(_dash(j))
    assert status == 200 and "Waiting for the first trading day" in page
    assert "Traceback" not in page and "Error" not in page
    assert inspect(j.engine).get_table_names() == []  # the reader created nothing


def test_BF_D37_empty_journal_shows_waiting_and_next_decision(tmp_path: Path) -> None:
    Journal.sqlite(str(tmp_path / "j.sqlite")).engine.dispose()  # tables, no rows
    sess = [date(2026, 11, d) for d in (23, 24, 25, 26, 27, 30)] + [date(2026, 12, 1)]
    status, page = _get(_dash(_ro(tmp_path / "j.sqlite"), sessions=lambda: sess))
    assert status == 200 and "Waiting for the first trading day" in page
    assert "Monday 30 November 2026" in page  # the month-end decision
    assert "NORMAL" in page


def test_BF_D37_renders_a_run_of_the_real_app(demo: Demo) -> None:
    j = _ro(demo.journal_path)
    src = Sources(j, index=demo.index, index_label="Index (demo)", sessions=lambda: demo.sessions,
                  today=lambda: demo.last_day, demo=True)  # fmt: skip
    v = collect(src)
    w = Journal.sqlite(str(demo.journal_path))  # the same journal, as the trader sees it
    assert v.started and v.capital_in == Decimal(10000)
    assert v.value == Decimal(w.job_records("value:EMG2_18_PAPER:")[-1][1]["value"])
    assert {h.code: h.qty for h in v.holdings} == w.positions("EMG2_18_PAPER")
    assert all(h.cost is not None and h.days_held is not None for h in v.holdings)
    assert v.orders and v.last_decision is not None
    assert v.twin_n == 5 and v.twin_pct is not None and v.sim_value is not None
    assert len(v.index) > 1 and v.recon is not None and v.recon[1]
    assert v.report_at is not None  # (scheduler job keys are written by run_forever only)
    status, page = _get(Dashboard(src))
    assert status == 200 and "<svg" in page and "DEMO" in page and "perf-data" in page
    assert "Twin vs 5 random twins" in page and "Waiting for the first" not in page
    status, page = _get(Dashboard(src), "/holdings")
    assert status == 200 and "Holdings (" in page


def test_BF_D37_stale_mark_is_flagged(tmp_path: Path) -> None:
    w = Journal.sqlite(str(tmp_path / "j.sqlite"))
    book = "EMG2_18_PAPER"
    w.add_cash(book, "DEPOSIT", Decimal(10000), "paper")
    t0 = datetime(2026, 11, 2, 5, 0, tzinfo=UTC)
    for code, px in (("AAA", "2.00"), ("HGO", "1.00")):
        w.add_fill(
            FillRecord(f"x{code}", None, book, code, Side.BUY, 100, Decimal(px), Decimal(1), t0)
        )
    w.mark_job("marks:2026-11-17", {"AAA": "2.10", "HGO": "1.20"}, t0)
    w.mark_job("marks:2026-11-18", {"AAA": "2.20"}, t0)  # HGO missing from the feed
    w.mark_job(f"value:{book}:2026-11-18", {"value": "9960", "peak": "10000", "stage": 0}, t0)
    w.set_safety(SafetyLevel.PAUSED, "owner /pause", "telegram:1", t0)
    w.mark_job("2026-11-18:16:30:reconcile", {"error": "ValueError: boom"}, NOW)
    v = collect(Sources(_ro(tmp_path / "j.sqlite"), today=lambda: date(2026, 11, 18)))
    h = {x.code: x for x in v.holdings}
    assert not h["AAA"].stale and h["AAA"].value == Decimal("220.00")
    assert h["AAA"].cost == Decimal("201.00") and h["AAA"].gain == Decimal("19.00")
    assert h["HGO"].stale and h["HGO"].mark == Decimal("1.20") and h["HGO"].mark_day == "2026-11-17"
    assert h["AAA"].days_held == 16 and v.safety == "PAUSED"
    assert v.last_job is not None and v.last_job[0].endswith("reconcile") and v.job_errors == 1
    from trader.app_pages import Extras, holdings, server

    assert "PAUSED" in render(v)
    assert "old price" in holdings(v, Extras(), None)
    assert "failed: ValueError" in server(v, Extras())


def test_BF_D37_index_line_from_the_price_store(tmp_path: Path) -> None:
    import gzip
    import json

    root = tmp_path / "eodhd"
    (root / "raw" / "eod").mkdir(parents=True)
    (root / "raw" / "bulk_eod").mkdir(parents=True)
    hist = [{"date": "2026-11-02", "close": 100.0}, {"date": "2026-11-03", "close": 101.0}]
    with gzip.open(root / "raw/eod/A200.AU__1.json.gz", "wt") as f:
        json.dump(hist, f)
    with gzip.open(root / "raw/bulk_eod/AU_2026-11-04__1.json.gz", "wt") as f:
        json.dump([{"code": "A200", "date": "2026-11-04", "close": 99.99},
                   {"code": "BHP", "date": "2026-11-04", "close": 40.0}], f)  # fmt: skip
    (root / "manifest.tsv").write_text(
        "kind\tsymbol\thttp\tfile\neod\tA200.AU\t200\traw/eod/A200.AU__1.json.gz\n"
    )
    from trader.dashboard import store_index

    lv = store_index(root, "A200")()
    assert [d.isoformat() for d, _ in lv] == ["2026-11-02", "2026-11-03", "2026-11-04"]
    assert lv[0][1] == 1.0 and abs(lv[2][1] - 0.9999) < 1e-9


def test_BF_D37_session_is_read_only(demo: Demo) -> None:
    j = _ro(demo.journal_path)
    with pytest.raises(DBAPIError), j.engine.begin() as c:
        c.execute(insert(cash_moves).values(book="X", kind="DEPOSIT", amount=1, at=NOW, note="x"))
    with pytest.raises(DBAPIError):
        j.set_safety(SafetyLevel.NORMAL, "forged", "dashboard")  # even the app's own writer
    assert Journal.sqlite(str(demo.journal_path)).cash("X") == 0


def test_BF_D37_postgres_session_is_read_only(pg_url: str) -> None:
    Journal(create_engine(pg_url)).engine.dispose()
    j = Journal.read_only(read_only_engine(pg_url))
    with j.engine.connect() as c:
        assert c.execute(text("SHOW default_transaction_read_only")).scalar() == "on"
    with pytest.raises(DBAPIError):
        j.add_cash("X", "DEPOSIT", Decimal(1), "forged")


def test_BF_D37_no_write_routes(tmp_path: Path) -> None:
    """BF-D37 / BF-D43: the app's own screens are read-only (GET/HEAD); ``/act/...`` is
    only forwarded to the trader's control server (BF-D39), never handled here."""
    d = _dash(_ro(tmp_path / "none.sqlite"))
    assert set(d.routes()) == {"/healthz", "/manifest.webmanifest", "/icon.svg", "/icon-192.png",
                               "/icon-512.png", "/icon-maskable-512.png", "/apple-touch-icon.png",
                               "/app.css", "/app.js", "/sw.js"}  # fmt: skip
    assert frozenset({"GET", "HEAD"}) == READ_METHODS
    for m in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
        for path in ("/", "/orders", "/inbox", "/settings"):
            status, hdrs, _ = d.respond(m, path, {})
            assert status == 405 and hdrs["Allow"] == "GET, HEAD"
    assert _get(d, "/approve")[0] == 404
    assert d.respond("POST", "/act/do", {}, b"a=pa")[0] == 503  # no control server: nothing
    seen: list[tuple[str, str]] = []
    d.actions = lambda m, p, h, b: (seen.append((m, p)) or (200, {}, b"forwarded"))  # type: ignore[func-returns-value]
    assert d.respond("POST", "/act/do", {}, b"a=pa")[2] == b"forwarded" and seen == [
        ("POST", "/act/do")
    ]
    status, hdrs, _ = d.respond("GET", "/", {})
    csp = hdrs["Content-Security-Policy"]
    assert "default-src 'none'" in csp and "script-src 'self'" in csp and "unsafe-eval" not in csp
    assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]
    for path in ("/", "/holdings", "/orders", "/inbox", "/server", "/settings"):
        page = _get(d, path)[1]
        assert "<form" not in page, path
        assert page.count("<script") == page.count('<script src="/app.js"') + page.count(
            'type="application/json"'
        )


def test_BF_D37_tailscale_login_allow_list(tmp_path: Path) -> None:
    d = Dashboard(Sources(_ro(tmp_path / "n.sqlite")), frozenset({"owner@example.com"}))
    assert _get(d)[0] == 403  # no header: not through tailscale serve
    assert _get(d, **{"Tailscale-User-Login": "other@example.com"})[0] == 403
    assert _get(d, **{"Tailscale-User-Login": "Owner@Example.com"})[0] == 200
    assert _get(d, "/healthz")[0] == 200  # the container's health check
    assert _get(Dashboard(Sources(_ro(tmp_path / "n.sqlite"))))[0] == 200  # unset: allow


def test_BF_D37_installable_manifest_and_icons(tmp_path: Path) -> None:
    d = _dash(_ro(tmp_path / "n.sqlite"))
    assert MANIFEST["display"] == "standalone" and MANIFEST["theme_color"]
    for size in (192, 512):
        status, hdrs, body = d.respond("GET", f"/icon-{size}.png", {})
        assert status == 200 and hdrs["Content-Type"] == "image/png"
        assert body[:8] == b"\x89PNG\r\n\x1a\n" and int.from_bytes(body[16:20]) == size
    assert icon_png(192) is icon_png(192)  # drawn once
    page = _get(d)[1]
    assert 'rel="manifest"' in page and 'http-equiv="refresh" content="60"' in page


@pytest.fixture
def server(tmp_path: Path) -> Iterator[str]:
    httpd = serve(_dash(_ro(tmp_path / "n.sqlite")), "127.0.0.1", 0)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def test_BF_D37_http_server_get_ok_post_refused(server: str) -> None:
    with urllib.request.urlopen(server + "/") as r:
        assert r.status == 200 and b"Big Wins" in r.read()
    req = urllib.request.Request(server + "/", data=b"x", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 405
    e.value.close()


def test_BF_D37_cli_snapshot(tmp_path: Path) -> None:
    Journal.sqlite(str(tmp_path / "j.sqlite")).engine.dispose()
    out = tmp_path / "page.html"
    rc = bf_main(["dashboard", "--config", str(CONFIG), "--journal",
                  f"sqlite+pysqlite:///{tmp_path / 'j.sqlite'}", "--store", str(tmp_path),
                  "--out", str(tmp_path), "--snapshot", str(out)])  # fmt: skip
    assert rc == 0 and "Waiting for the first trading day" in out.read_text()


def test_BF_D37_compose_service_is_loopback_and_read_only() -> None:
    import yaml

    root = Path(__file__).resolve().parent.parent
    dc = yaml.safe_load((root / "deploy" / "docker-compose.yml").read_text())
    svc = dc["services"]
    with_ports = {k for k, v in svc.items() if v.get("ports")}
    assert with_ports == {"dashboard"}  # nothing else is published
    d = svc["dashboard"]
    assert d["ports"] == ["127.0.0.1:8080:8080"]
    assert set(d["networks"]) == {"internal", "dashboard", "control"}
    # BF-D52: its own SELECT-only role's password (never db_password) and the proxy key
    assert d["secrets"] == ["db_dashboard_password", "app_proxy_key"] and d["user"] == "10001:10001"
    assert "bigwins_dashboard@db" in d["environment"]["TRADER_BF_JOURNAL_URL"]
    assert d["read_only"] is True and d["cap_drop"] == ["ALL"]
    assert all(v.endswith(":ro") for v in d["volumes"])
    assert "egress" not in d["networks"]
    assert d["command"][:2] == ["trader-bf", "dashboard"]
