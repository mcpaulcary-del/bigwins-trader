"""BF-D55 (re-review N1): the app's buttons work in a real browser. Chromium (Playwright,
Node) clicks Pause, Kill -> Yes and Approve all -> code against `trader-bf dashboard
--demo`, whose actions go through the same signed forwarding, Origin and CSRF checks as
production (the demo only simulates the result). Skipped where Node / Playwright / a
browser is not installed."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tests" / "browser" / "app_buttons.js"
PW_GLOBAL = Path("/opt/node22/lib/node_modules/playwright")


def _playwright() -> str | None:
    if shutil.which("node") is None:
        return None
    if PW_GLOBAL.is_dir():
        return str(PW_GLOBAL)
    r = subprocess.run(["node", "-e", "require.resolve('playwright')"], capture_output=True,
                       check=False)  # fmt: skip
    return "playwright" if r.returncode == 0 else None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_BF_D55_D62_real_browser_buttons_chart_tabs_a11y(tmp_path: Path) -> None:
    module = _playwright()
    if module is None:
        pytest.skip("node / playwright not installed")
    port = _free_port()
    srv = subprocess.Popen(
        [sys.executable, "-m", "trader.bfast_cli", "dashboard", "--demo", "--host", "127.0.0.1",
         "--port", str(port), "--out", str(tmp_path)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )  # fmt: skip
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(240):
            try:
                with urllib.request.urlopen(base + "/healthz", timeout=2) as r:
                    if r.status == 200:
                        break
            except OSError:
                time.sleep(0.5)
        else:
            pytest.fail("the demo app did not start")
        env = {**os.environ, "PLAYWRIGHT_MODULE": module}
        r = subprocess.run(["node", str(SCRIPT), base], capture_output=True, text=True,
                           env=env, timeout=180, check=False)  # fmt: skip
        if r.returncode != 0 and "Executable doesn't exist" in r.stderr:
            pytest.skip("no Chromium for Playwright here")
        assert r.returncode == 0, r.stderr[-2000:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.terminate()
        srv.wait(10)
    for step in ("pause", "kill", "approve"):
        assert "DEMO: nothing was done" in out[step], (step, out[step])
        assert "cross-site" not in out[step] and "form token" not in out[step]
    assert "Approve all" in out["confirm"] and "total" in out["confirm"]
    assert len(out["posts"]) == 3
    # BF-D62: the chart read-out, range buttons, tab switching, holdings interactions
    assert out["tooltip"] and "A$" in out["tooltip"] and "gap" in out["tooltip"]
    assert out["range"] == "true"
    assert out["tab"] == ["holdings", "/holdings", "holdings"]
    assert out["sorted"] is True and out["donut"] >= 1
    # BF-D68: swipe between tabs, treemap tap -> detail sheet, what-if slider, calendar day
    assert out["swipe"] == ["/holdings", "holdings"]
    assert out["tmToggle"] == "true" and out["treemap"][0] == out["treemap"][1]
    before, after, move, words = out["whatif"]
    assert move == "\u221220%" and before != after and "A$" in after and words
    assert out["calendar"][1] is True and out["calendar"][0] == out["calendar"][2]
    # accessibility: every control has a name, every chart a label, text contrast >= 4.5
    assert out["a11y"] == [], out["a11y"]
