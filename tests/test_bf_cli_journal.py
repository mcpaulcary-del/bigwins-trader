"""BF-D30: ``trader-bf deposit|kill|pause|status`` act on the running app's journal (the
config's ``journal.url_env``, Postgres on the server with the ``db_password`` secret),
never on an implicit local SQLite file; SQLite only when named explicitly."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from trader import bfast_cli
from trader.bfast_cli import main
from trader.journal import Journal
from trader.risk import SafetyLevel
from trader.secrets import SecretValue

CFG = Path(__file__).resolve().parent.parent / "config" / "bfast.yaml"
ENV = "TRADER_BF_JOURNAL_URL"  # config/bfast.yaml journal.url_env


def test_BF_D30_cli_uses_the_configured_journal_not_a_local_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    db = tmp_path / "app_journal.sqlite3"  # stands in for the server's Postgres
    monkeypatch.setenv(ENV, f"sqlite+pysqlite:///{db}")
    cfg = ["--config", str(CFG)]
    assert main(["deposit", "--book", "EMG2_18_PAPER", "--amount", "10000", *cfg]) == 0
    assert main(["deposit", "--book", "EMG2_18_SIM", "--amount", "10000", *cfg]) == 0
    assert main(["pause", *cfg]) == 0
    assert main(["status", *cfg]) == 0
    out = capsys.readouterr()
    assert "EMG2_18_PAPER: cash A$10000" in out.out and "safety PAUSED" in out.out
    assert f"journal: sqlite+pysqlite:///{db}" in out.err
    assert main(["kill", *cfg]) == 0
    j = Journal.sqlite(str(db))  # the app's journal holds what the CLI did
    assert j.cash("EMG2_18_PAPER") == Decimal(10000) == j.cash("EMG2_18_SIM")
    assert j.safety_level() == SafetyLevel.KILLED
    assert not (tmp_path / "bf_journal.sqlite3").exists()  # the old implicit file
    assert [p.name for p in tmp_path.iterdir()] == ["app_journal.sqlite3"]


@pytest.mark.parametrize("cmd", ["deposit", "kill", "pause", "status"])
def test_BF_D30_no_configured_journal_is_refused_not_defaulted(
    cmd: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(ENV, raising=False)
    extra = ["--book", "EMG2_18_PAPER", "--amount", "1"] if cmd == "deposit" else []
    with pytest.raises(SystemExit, match=ENV):
        main([cmd, *extra, "--config", str(CFG)])
    assert list(tmp_path.iterdir()) == []  # no SQLite file was created


def test_BF_D30_explicit_journal_url_for_tests_and_dev(tmp_path: Path) -> None:
    db = tmp_path / "dev.sqlite3"
    assert main(["deposit", "--book", "B", "--amount", "5", "--journal", f"sqlite:///{db}"]) == 0
    assert Journal.sqlite(str(db)).cash("B") == Decimal(5)
    with pytest.raises(SystemExit, match="positive"):
        main(["deposit", "--book", "B", "--amount", "-5", "--journal", f"sqlite:///{db}"])


def test_BF_D30_postgres_url_takes_the_password_from_the_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The server's password-free URL + the db_password Docker secret, as ``run`` does."""
    import sqlalchemy

    import trader.secrets

    seen: dict[str, Any] = {}
    real = sqlalchemy.create_engine

    def fake_engine(url: Any) -> Any:
        seen["url"] = url
        return real("sqlite://")

    monkeypatch.setenv(ENV, "postgresql+psycopg://trader@db:5432/ledger_bf_paper")
    monkeypatch.setattr(sqlalchemy, "create_engine", fake_engine)
    monkeypatch.setattr(trader.secrets, "read_secret", lambda n: SecretValue(f"pw-of-{n}"))
    assert main(["status", "--config", str(CFG)]) == 0
    url = seen["url"]
    assert url.host == "db" and url.database == "ledger_bf_paper"
    assert url.password == "pw-of-db_password"


def test_BF_D30_run_and_cli_share_one_journal_function(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake(url_env: str) -> Journal:
        calls.append(url_env)
        return Journal.sqlite()

    monkeypatch.setattr(bfast_cli, "_journal_from_config", fake)
    assert main(["status", "--config", str(CFG)]) == 0
    assert calls == [ENV]
