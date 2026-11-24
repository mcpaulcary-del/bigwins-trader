"""BF-D33: the secret files are checked at start-up (444 files in a 700 folder,
readable by uid 10001), with a clear error; their contents are never read."""

from __future__ import annotations

import builtins
import json
from pathlib import Path
from typing import Any

import pytest

from trader import secret_check
from trader.bfast_cli import main
from trader.secret_check import STACK_SECRETS, TRADER_SECRETS, check_secrets
from trader.yamlio import load_yaml

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "deploy" / "docker-compose.yml"


def _dir(tmp: Path, mode: int = 0o444) -> Path:
    d = tmp / "secrets"
    d.mkdir()
    for n in STACK_SECRETS:
        (d / n).write_text("not-a-real-value")
        (d / n).chmod(mode)
    return d


def test_BF_D33_good_files_pass_without_reading_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    d = _dir(tmp_path)

    def no_open(*a: Any, **k: Any) -> Any:
        raise AssertionError("a secret was opened")

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", no_open)
        m.setattr(Path, "read_text", no_open)
        m.setattr(Path, "read_bytes", no_open)
        assert check_secrets(STACK_SECRETS, d) == []
    assert main(["check-secrets", "--all", "--dir", str(d)]) == 0
    out = capsys.readouterr().out
    # BF-D83: + app_passphrase ("none" until the owner sets it)
    assert "ok: 12 secret file(s)" in out and "not-a-real-value" not in out
    assert "tws_password" not in TRADER_SECRETS and len(TRADER_SECRETS) == 10


@pytest.mark.parametrize(
    ("mode", "words"),
    [
        (0o600, "is not readable by other users"),  # the old guide's chmod 600
        (0o400, "is not readable by other users"),
        (0o666, "lets other users change it"),
    ],
)
def test_BF_D33_wrong_mode_is_a_clear_error(
    mode: int, words: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    d = _dir(tmp_path, mode)
    bad = check_secrets(TRADER_SECRETS, d)
    assert len(bad) == 10 and all(words in b and "chmod 444 secrets/*" in b for b in bad)
    assert main(["check-secrets", "--dir", str(d)]) == 2
    err = capsys.readouterr().err
    assert err.count("SECRET CHECK FAILED: secret ") == 10 and "not-a-real-value" not in err


def test_BF_D33_missing_or_empty(tmp_path: Path) -> None:
    d = _dir(tmp_path)
    (d / "db_password").unlink()
    (d / "totp_seed").chmod(0o644)
    (d / "totp_seed").write_text("")
    (d / "totp_seed").chmod(0o444)
    bad = check_secrets(TRADER_SECRETS, d)
    assert any(b.startswith("secret db_password: missing") for b in bad)
    assert any(b.startswith("secret totp_seed: empty") for b in bad)
    assert check_secrets(("not_a_secret",), d) == ["secret 'not_a_secret': not a known secret name"]


def test_BF_D33_run_stops_at_start_up_on_a_bad_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = json.loads(json.dumps(load_yaml((ROOT / "config/bfast.yaml").read_text()), default=str))
    raw["broker"]["account_id"] = "DU1234567"
    raw["telegram"]["allowed_chat_ids"] = [1]
    p = tmp_path / "c.yaml"
    p.write_text(json.dumps(raw))
    d = _dir(tmp_path, 0o600)
    monkeypatch.setattr(secret_check, "SECRETS_DIR_DEFAULT", d)
    with pytest.raises(SystemExit, match="SECRET CHECK FAILED: secret db_password: mode 0600"):
        main(["run", "--config", str(p)])


def test_BF_D33_compose_checks_every_secret_before_the_services_start() -> None:
    c = load_yaml(COMPOSE.read_text())
    svc = c["services"]
    chk = svc["secrets-check"]
    assert chk["user"] == "10001:10001" and chk["network_mode"] == "none"
    assert chk["command"] == ["trader-bf", "check-secrets", "--all"]
    assert sorted(chk["secrets"]) == sorted(STACK_SECRETS) == sorted(c["secrets"])
    for name in ("gw-paper", "db", "trader"):
        assert svc[name]["depends_on"]["secrets-check"] == {
            "condition": "service_completed_successfully"
        }
    assert sorted(svc["trader"]["secrets"]) == sorted(TRADER_SECRETS)
    assert "trader-bf check-secrets &&" in svc["trader"]["command"][-1]
    host = (ROOT / "deploy" / "check_secrets.sh").read_text()
    assert all(n in host for n in STACK_SECRETS) and '"700"' in host and '"444"' in host
