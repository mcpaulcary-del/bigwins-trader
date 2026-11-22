"""BF-D63: the "Setup & IBKR" checklist screen. A read-only guide: automatic ticks come
from data the app already reads (config, journal records, the host worker's status);
manual ticks live on the phone only (localStorage). No new write path, no POST route."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from trader.app_store import set_state
from trader.dashboard import Dashboard, Sources
from trader.journal import Journal, read_only_engine
from trader.server_status import clean_status

T0 = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)


def _dash(path: Path, facts: dict[str, object]) -> Dashboard:
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{path}"))
    src = Sources(j, clock=lambda: T0, today=lambda: T0.date())
    return Dashboard(src, setup_facts=lambda: facts)


def _page(d: Dashboard) -> str:
    st, _, body = d.respond("GET", "/setup", {})
    assert st == 200
    return body.decode()


def test_BF_D63_setup_screen_lists_13_items_with_links_and_progress(tmp_path: Path) -> None:
    Journal.sqlite(str(tmp_path / "j.sqlite")).engine.dispose()
    page = _page(_dash(tmp_path / "j.sqlite", {"account_id": None}))
    assert len(re.findall(r'class="sitem', page)) == 13
    assert "0 of 13 done" in page and 'id="setup-ring"' in page
    assert "on this phone" in page and 'data-setup-id="tfn"' in page
    for href in re.findall(r'href="(https?://[^"]+)"', page):
        assert href in (
            "https://www.interactivebrokers.com.au/",
            "https://www.interactivebrokers.com.au/sso/Login",
            "https://healthchecks.io/",
            "https://claude.ai/code",
        ), href
    for a in re.findall(r"<a [^>]*https://www\.interactivebrokers[^>]*>", page):
        assert 'target="_blank"' in a and 'rel="noopener noreferrer"' in a
    assert "Settings" in page and "Market Data Subscriptions" in page
    assert "A$250" in page and "A$2.5" in page  # the wholesale certificate note
    assert "<form" not in page  # nothing to submit: manual ticks stay on the phone


def test_BF_D63_automatic_ticks_come_from_existing_records(tmp_path: Path) -> None:
    w = Journal.sqlite(str(tmp_path / "j.sqlite"))
    book = "EMG2_18_PAPER"
    w.mark_job("flex-pull:2026-11-30", {"status": "ok", "file": "x.xml"}, T0)
    for d in ("2026-11-24", "2026-11-25", "2026-11-26", "2026-11-27", "2026-11-30"):
        w.mark_job(f"recon:{book}:{d}", {"ok": True}, T0)
    set_state(w, "host-status", clean_status({"secrets": {
        "tws_password": True, "ibkr_flex_token": True, "ibkr_flex_query_id": False,
        "not_a_secret": True, "db_password": "yes"}}), T0)  # fmt: skip
    w.engine.dispose()
    page = _page(_dash(tmp_path / "j.sqlite", {"account_id": "DU1234567"}))
    for item in ("paper", "flex", "gateway", "dryruns"):
        assert re.search(rf'class="sitem done auto" data-item="{item}"', page), item
    assert "5 of 5 reconciled paper sessions" in page
    assert "ibkr_flex_query_id" in page and "missing" in page and "not_a_secret" not in page
    assert "4 of 13 done" in page
    # a live-looking id is never a tick
    page = _page(_dash(tmp_path / "j.sqlite", {"account_id": "U7654321"}))
    assert not re.search(r'class="sitem done auto" data-item="paper"', page)


def test_BF_D63_secret_names_only_never_values() -> None:
    st = clean_status({"secrets": {"tws_password": True, "eodhd_api_token": "s3cr3t-value",
                                   "bad name": True}})  # fmt: skip
    assert st["secrets"] == {"tws_password": True, "eodhd_api_token": True}
    assert "s3cr3t-value" not in json.dumps(st)
    import runpy

    hs = runpy.run_path(str(Path(__file__).resolve().parent.parent / "deploy/host_status.py"))
    snap = hs["snapshot"]({"SECRETS_PRESENT": "tws_password ibkr_flex_token",
                           "SECRETS_MISSING": "ibkr_flex_query_id"})  # fmt: skip
    assert snap["secrets"] == {"tws_password": True, "ibkr_flex_token": True,
                               "ibkr_flex_query_id": False}  # fmt: skip
    sh = (Path(__file__).resolve().parent.parent / "deploy/bigwins.sh").read_text()
    assert '[ -s "$SECRETS/$n" ]' in sh.split("host_status() {")[1].split("\n}\n")[0]


def test_BF_D63_no_post_route_and_read_only(tmp_path: Path) -> None:
    Journal.sqlite(str(tmp_path / "j.sqlite")).engine.dispose()
    d = _dash(tmp_path / "j.sqlite", {"account_id": None})
    for m in ("POST", "PUT", "DELETE", "PATCH"):
        assert d.respond(m, "/setup", {})[0] == 405
    page = _page(d)
    assert "/act/" not in page.split('<main id="main"')[1].split("</main>")[0]
    js = (Path(__file__).resolve().parent.parent / "trader" / "webui.py").read_text()
    setup_js = js.split("function setup(){")[1].split("\nfunction ")[0]
    assert "fetch(" not in setup_js and "localStorage" in js and "bw.setup." in setup_js
