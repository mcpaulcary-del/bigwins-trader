"""Security review L5 (BF-D70): every GET route, with an HTML / script payload in every
stored text field the app reads (host status, backups, update notes, inbox, server
jobs, index label, query strings), renders without an error and without the payload as
markup. JSON data blocks (``<script type="application/json">`` with ``</`` escaped) and
the JSON search index are data, not markup."""

from __future__ import annotations

import json
import re
import sqlite3
import urllib.parse
from pathlib import Path
from typing import Any

import pytest

P = "\"'><img src=x onerror=alert(1)></script><script>alert(2)</script>"
MARKUP = re.compile(r"<img src=x|<script>alert|onerror=alert\(1\)>")
JSON_BLOCK = re.compile(r'<script type="application/json"[^>]*>.*?</script>', re.S)


@pytest.fixture(scope="module")
def poisoned(tmp_path_factory: pytest.TempPathFactory) -> object:
    from trader.dashboard import Dashboard, Sources
    from trader.dashboard_demo import build_demo, demo_control
    from trader.journal import Journal, read_only_engine

    demo = build_demo(tmp_path_factory.mktemp("fz") / "j.sqlite", days=45, random_twins=5)
    db = sqlite3.connect(demo.journal_path)
    host = {"tailscale": "Running" + P, "code_version": "abc" + P, "asx": "open" + P,
            "containers": [{"name": "trader" + P, "state": "Up" + P}], "log": ["line " + P],
            "onedrive": P, "secrets": {"tws_password" + P: True}, "load1": P, "mem_used_pct": P,
            "disk_used_pct": P, "disk_free_gb": P, "uptime_s": P, "cpus": P, "key_fp": P,
            "backup_age_h": P}  # fmt: skip
    bk = {"kind": "backup", "ok": False, "at": P, "seconds": P,
          "local": {"ok": True, "archive": P, "size": P, "files": P, "error": P},
          "remote": {"ok": False, "error": P}, "files": P, "bad": [P], "ledger_files": P,
          "journal_dump": P, "error": P, "onedrive": P, "db_rows_match": P}  # fmt: skip
    for k, v in (
        ("host-status", host), ("backup-last", bk), ("restore-test-last", {**bk, "kind": "restore_test"}),
        ("backup-history", [bk]),
        ("update-available", {"remote": "a" * 40, "ahead": P, "notes": {"version": P, "what": P},
                              "reasons": [P], "previous": P, "strategy": True, "files": [P],
                              "subject": P, "head": P, "ci": P}),
        ("strategy-running", {"version": P, "id": P}), ("heartbeat", {"ok": P}), ("alerts", {"report": P}),
    ):  # fmt: skip
        db.execute("delete from bf_app_state where key=?", (k,))
        db.execute("insert into bf_app_state(key,value,at) values(?,?,?)",
                   (k, json.dumps(v), "2026-11-22 01:00:00"))  # fmt: skip
    db.execute("update bf_inbox set title=title||?, body=body||?, link=link||?", (P, P, P))
    db.execute("insert into bf_server_jobs(action,force,login,requested_at,status,result) "
               "values(?,?,?,?,?,?)", ("check" + P, 0, P, "2026-11-22 01:00:00", "DONE", P))  # fmt: skip
    db.commit()
    db.close()
    j = Journal.read_only(read_only_engine(f"sqlite+pysqlite:///{demo.journal_path}"))
    src = Sources(j, index=demo.index, sessions=lambda: demo.sessions, today=lambda: demo.last_day,
                  clock=lambda: demo.now, demo=True, prices=demo.prices,
                  forecast_dir=Path(__file__).resolve().parents[1] / "config",
                  index_label="Idx" + P)  # fmt: skip
    return Dashboard(src, actions=demo_control(j, demo).respond,
                     setup_facts=lambda: {"account_id": P}, version=P,
                     changelog=lambda: [{"version": P, "what": P, "why": P}]), demo  # fmt: skip


def test_L5_every_get_route_escapes_stored_and_query_text(poisoned: object) -> None:
    d: Any = poisoned[0]  # type: ignore[index]
    demo: Any = poisoned[1]  # type: ignore[index]
    q = urllib.parse.quote(P, safe="")
    paths = ["/", "/holdings", "/orders", "/inbox", "/inbox?kind=" + q, "/server", "/settings",
             "/tax", "/tax?fy=" + q, "/strategy", "/setup", "/backups", "/accounts", "/shares",
             "/forecast-method", "/calendar", "/calendar?m=" + q, "/compare", "/shares/" + q,
             "/holdings/" + q, "/orders/" + q, "/replay/" + q, f"/replay/{demo.last_day}",
             "/act", "/act/confirm?a=" + q, "/act/confirm?a=ok&b=" + q + "&n=" + q,
             "/act/confirm?a=cancel&job=" + q, "/act/confirm?a=srv:backup_key", "/act/alerts",
             "/act/backup-key", "/act/confirm?a=srv:update", "/act/confirm?a=srv:rollback"]  # fmt: skip
    for listing, pat in (("/holdings", r'href="(/holdings/[A-Z0-9]+)"'),
                         ("/orders", r'href="(/orders/[^"]+)"'), ("/shares", r'href="(/shares/[^"]+)"')):  # fmt: skip
        paths += re.findall(pat, d.respond("GET", listing, {})[2].decode())[:2]
    for p in paths:
        st, h, b = d.respond("GET", p, {})
        assert st in (200, 303, 404), (p, st)
        if not h.get("Content-Type", "").startswith("text/html"):
            continue
        text = JSON_BLOCK.sub("", b.decode("utf-8", "replace"))
        assert not MARKUP.search(text), (p, text[max(0, MARKUP.search(text).start() - 120) :][:240])  # type: ignore[union-attr]
    st, h, b = d.respond("GET", "/search.json", {})
    assert st == 200 and h["Content-Type"] == "application/json"
    json.loads(b)  # data for the client, which escapes it (and its highlight) itself
