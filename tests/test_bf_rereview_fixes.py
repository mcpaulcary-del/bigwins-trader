"""Re-review of f04d6f1..cea2e78 (22 Nov 2026): one test per open finding (N1..N9),
written before the fix and failing on cea2e78 (BF-D55..BF-D60)."""

from __future__ import annotations

import contextlib
import runpy
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pytest

from tests.test_bf_app_actions import OWNER, _post, _rows, _session, _setup
from tests.test_bf_execution import SEED, T_APPROVE
from trader.app_control import Control, same_origin
from trader.app_sign import sign_proxy
from trader.app_store import get_state
from trader.approval import totp
from trader.risk import SafetyLevel

ROOT = Path(__file__).resolve().parent.parent
KEY = b"k" * 64
HOST = "bigwins.example.ts.net"


def _signed_post(ctl: Control, form: dict[str, str], origin: str, site: str, host: str
                 ) -> tuple[int, str]:  # fmt: skip
    """A POST as the dashboard forwards it: signed log-in, Origin, Sec-Fetch-Site, Host."""
    g = sign_proxy(KEY, OWNER, "", "same-origin", "GET", "/act", b"", host=host)
    st, hdrs, body = ctl.respond("GET", "/act", g)
    assert st == 200, body
    sid = hdrs["Set-Cookie"].split(";")[0].split("=", 1)[1]
    token = body.decode().split('name="csrf" value="')[1].split('"')[0]
    data = urlencode({"csrf": token, **form}).encode()
    h = {**sign_proxy(KEY, OWNER, origin, site, "POST", "/act/do", data, host=host),
         "Cookie": f"bw_sid={sid}"}  # fmt: skip
    st, _, out = ctl.respond("POST", "/act/do", h, data)
    return st, out.decode()


# ---------------------------------------------------------------- N1 / N1b


def test_N1_origin_null_with_same_origin_fetch_site_is_accepted() -> None:
    """Chromium sends ``Origin: null`` on a same-origin form POST from a page served with
    ``Referrer-Policy: no-referrer``; it must not break every button."""
    from trader.webui import SECURITY_HEADERS

    assert SECURITY_HEADERS["Referrer-Policy"] == "same-origin"
    assert same_origin({"Origin": "null", "Sec-Fetch-Site": "same-origin"}, HOST)
    assert same_origin({"Origin": "null", "Sec-Fetch-Site": "same-origin"})
    assert not same_origin({"Origin": "null"}, HOST)
    assert not same_origin({"Origin": "null", "Sec-Fetch-Site": "cross-site"}, HOST)
    j, _, ctl, _, _ = _setup()
    ctl.proxy_key, ctl.public_host = KEY, HOST
    st, page = _signed_post(ctl, {"a": "pa"}, "null", "same-origin", HOST)
    assert st == 200 and "PAUSED" in page and j.safety_level() is SafetyLevel.PAUSED


def test_N1b_empty_public_host_uses_the_signed_host() -> None:
    j, _, ctl, _, _ = _setup()
    ctl.proxy_key, ctl.public_host = KEY, ""
    st, page = _signed_post(ctl, {"a": "pa"}, f"https://{HOST}", "same-origin", HOST)
    assert st == 200 and "PAUSED" in page
    st, page = _signed_post(ctl, {"a": "pa"}, "https://evil.example", "same-origin", HOST)
    assert st == 403  # the Origin must still be the host the dashboard received


def test_N1b_changed_address_explains_and_still_allows_pause_kill_stop() -> None:
    j, _, ctl, bid, _ = _setup()
    ctl.proxy_key, ctl.public_host = KEY, "old-name.example.ts.net"
    st, page = _signed_post(ctl, {"a": "ok", "b": bid, "n": "all",
                                  "code": totp(SEED, T_APPROVE)}, f"https://{HOST}",
                            "same-origin", HOST)  # fmt: skip
    assert st == 403 and "address changed" in page and "option 11" in page
    assert _rows(j, bid) == []
    st, page = _signed_post(ctl, {"a": "pa"}, f"https://{HOST}", "same-origin", HOST)
    assert st == 200 and "PAUSED" in page
    st, page = _signed_post(ctl, {"a": "ki", "confirm": "yes"}, f"https://{HOST}",
                            "same-origin", HOST)  # fmt: skip
    assert "KILLED" in page
    st, page = _signed_post(ctl, {"a": "pa"}, "https://evil.example", "cross-site", HOST)
    assert st == 403  # cross-site stays refused, even for Pause


def test_N1_dashboard_signs_the_host_it_received(monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    import urllib.request

    from trader.app_sign import NonceCache, verify_proxy
    from trader.dashboard import proxy_to

    got: dict[str, Any] = {}

    class _R(io.BytesIO):
        status = 200
        headers: dict[str, str] = {}  # noqa: RUF012

        def __enter__(self) -> _R:
            return self

        def __exit__(self, *a: object) -> None:
            return None

    def fake(req: urllib.request.Request, timeout: float) -> _R:
        got["h"] = dict(req.header_items())
        return _R(b"")

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    proxy_to("http://trader-control:8081", KEY)(
        "POST",
        "/act/do",
        {
            "Host": "127.0.0.1:8080",
            "X-Forwarded-Host": HOST,
            "Origin": f"https://{HOST}",
            "Sec-Fetch-Site": "same-origin",
        },
        b"x",
    )
    v = verify_proxy(KEY, got["h"], "POST", "/act/do", b"x", NonceCache())
    assert v is not None and v["host"] == HOST  # tailscale serve's forwarded host


# ---------------------------------------------------------------- N2 / N6


def test_N2_malformed_command_does_not_clear_the_wrong_code_count() -> None:
    """The reviewer's rr_lock.py: wrong code, then a malformed idmap_reject, 40 times."""
    j, bot, ctl, bid, pages = _setup()
    s = _session(ctl)
    good = totp(SEED, T_APPROVE)
    for i in range(40):
        _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": f"{(int(good) + 1 + i) % 10**6:06d}"},
              session=s)  # fmt: skip
        _post(ctl, {"a": "idmap_reject", "old": "A B", "code": "000000"}, session=s)
    assert bot.verifier.failures <= 3 and ctl.locked(T_APPROVE) is not None
    assert pages and pages[0].startswith("PAGE")
    assert "approved" not in _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": good},
                                   session=s)[1]  # fmt: skip


def test_N2_preview_refuses_malformed_idmap() -> None:
    _, bot, _, _, _ = _setup()
    for args in (["A B"], ["A", "B C"], ["TOOLONGCODE", "NEW"], ["OLD", "NEW", "x:y"]):
        act = "idmap_reject" if len(args) == 1 else "idmap"
        why, _, _ = bot.preview(act, args, T_APPROVE)
        assert why is not None, args
    assert bot.preview("idmap", ["HGO", "KAN", "1:10"], T_APPROVE)[0] is None


def test_N6_slow_guessing_locks_for_a_day() -> None:
    j, bot, ctl, bid, pages = _setup()
    t = T_APPROVE
    for k in range(6):  # 2 wrong codes per hour: never 3 in 15 minutes
        t = T_APPROVE + timedelta(minutes=40 * k)
        ctl.clock_box["t"] = t  # type: ignore[attr-defined]
        _post(ctl, {"a": "re", "code": "000000"})  # resume: no deadline
    lock = ctl.locked(t)
    assert lock is not None and lock - t >= timedelta(hours=23)
    assert any("HIGH PRIORITY" in p for p in pages)
    assert "PAUSED" in _post(ctl, {"a": "pa"})[1]  # still available
    st = get_state(j, "app-lockout")
    assert st is not None and st[0]["until"]


# ---------------------------------------------------------------- N3


def test_N3_code_slot_released_after_an_unexpected_error() -> None:
    """The reviewer's rr_slot.py: a journal error while preparing a coded request."""
    j, _, ctl, bid, _ = _setup()
    s = _session(ctl)

    def boom() -> dict[str, Any]:
        raise RuntimeError("journal hiccup")

    ctl.update_state = boom  # type: ignore[method-assign]
    ctl.market_open = lambda now: False
    with contextlib.suppress(RuntimeError):
        _post(ctl, {"a": "srv:check", "code": "123456"}, session=s)
    assert ctl._code_busy is False
    del ctl.update_state
    page = _post(ctl, {"a": "ok", "b": bid, "n": "all", "code": totp(SEED, T_APPROVE)},
                 session=s)[1]  # fmt: skip
    assert "approved all" in page


# ---------------------------------------------------------------- N4 / N8 (host scripts)


def test_N4_update_reexecs_the_new_script_and_keys_fail_loudly() -> None:
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    upd = sh.split("cmd_update() {")[1].split("\n}\n")[0]
    assert 'exec bash "$DEPLOY/bigwins.sh" after-pull' in upd
    assert "after-pull) after_update" in sh
    to = sh.split("update_to() {")[1].split("\n}\n")[0]
    assert 'bash "$DEPLOY/bigwins.sh" after-pull' in to and "after_update\n" not in to
    keys = sh.split("make_keys() {")[1].split("\n}\n")[0]
    assert "command -v openssl" in keys and "mv " in keys and "return 1" in keys
    for doc in ("NEXT.md", "docs/GO_LIVE_GUIDE.md"):
        text = (ROOT / doc).read_text()
        assert "git -C /srv/asx-trader pull --ff-only && bigwins update" in text, doc
        assert "sudo bigwins install-worker" in text and "test Pause" in text, doc


def test_N8_worker_refuses_to_run_a_job_id_twice(tmp_path: Path) -> None:
    g = runpy.run_path(str(ROOT / "deploy/gitops.py"))
    assert g["claim_id"](tmp_path, "17") is True
    assert g["claim_id"](tmp_path, "17") is False
    assert g["claim_id"](tmp_path, "18") is True
    sh = (ROOT / "deploy/bigwins.sh").read_text()
    assert 'gitops.py" claim-id "$STATE" "$id"' in sh
    assert sh.index('gitops.py" verify') < sh.index('gitops.py" claim-id')


# ---------------------------------------------------------------- N5


def test_N5_infra_changes_are_not_app_only() -> None:
    from trader import strategy_version as sv

    w = runpy.run_path(str(ROOT / "deploy/classify.py"))
    for f in ("deploy/bigwins.sh", "deploy/docker-compose.yml", "deploy/Dockerfile",
              "pyproject.toml", "uv.lock", "alembic.ini", "scripts/req_coverage.py"):  # fmt: skip
        assert sv.is_trading_path(f) and w["classify"]([f]) == "strategy", f
    for f in ("docs/X.md", "tests/test_x.py", "README.md", "trader/webui.py"):
        assert not sv.is_trading_path(f) and w["classify"]([f]) == "app", f
    assert w["TRADING_FILES"] == sv.TRADING_FILES


# ---------------------------------------------------------------- N9


def test_N9_control_server_waits_for_its_address(capsys: pytest.CaptureFixture[str]) -> None:
    from trader.bfast_cli import wait_for_address

    calls: list[str] = []

    def resolve(host: str) -> str:
        calls.append(host)
        if len(calls) < 3:
            raise OSError("Name or service not known")
        return "172.20.0.5"

    slept: list[float] = []
    assert wait_for_address("trader-control", resolve, slept.append) == "172.20.0.5"
    assert len(calls) == 3 and slept == sorted(slept) and slept[0] > 0
    assert "not resolvable yet" in capsys.readouterr().err


# ---------------------------------------------------------------- cleanups


def test_db_role_has_a_connection_limit_and_no_temp() -> None:
    sql = (ROOT / "deploy/db_roles.sql").read_text()
    assert "CONNECTION LIMIT 5" in sql and "REVOKE TEMPORARY ON DATABASE" in sql
