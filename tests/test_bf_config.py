"""B-fast config: the repo file validates; any live setting is refused (BW-EXE-09)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from trader.bfast_cli import main
from trader.bfast_config import BfastConfig, load_bfast_config
from trader.risk import RiskLimits
from trader.yamlio import load_yaml

CFG = Path(__file__).resolve().parent.parent / "config" / "bfast.yaml"


def _raw() -> dict:  # type: ignore[type-arg]
    out: dict = load_yaml(CFG.read_text())  # type: ignore[type-arg]
    return out


def test_repo_config_validates_and_matches_engine_defaults() -> None:
    c = load_bfast_config(CFG)
    assert c.mode == "paper" and c.broker.allow_live is False and c.broker.port == 4004
    assert c.risk_limits() == RiskLimits()
    assert main(["validate-config", "--config", str(CFG)]) == 0


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("mode",), "live"),
        (("broker", "allow_live"), True),
        (("broker", "account_id"), "U1234567"),
        (("live_emg2_20", "capital_cap_aud"), 20000),
        (("live_emg2_20", "min_parcel_aud"), 400),
        (("risk", "order_value_max_aud"), 5000),
        (("risk", "unknown_key"), 1),
        (("execution", "approval_mode"), "auto"),  # L8: never auto-execute
    ],
)
def test_BW_EXE_09_live_or_looser_settings_do_not_validate(
    path: tuple[str, ...], value: object
) -> None:
    raw = _raw()
    node = raw
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value
    with pytest.raises(ValidationError):
        BfastConfig.model_validate(raw)


def test_run_refuses_without_a_paper_account_or_chat(tmp_path: Path) -> None:
    import json

    raw = json.loads(json.dumps(_raw(), default=str))  # YAML is a superset of JSON
    p = tmp_path / "c.yaml"
    p.write_text(json.dumps(raw))
    with pytest.raises(SystemExit, match="account_id"):
        main(["run", "--config", str(p)])
    raw["broker"]["account_id"] = "DU1234567"
    p.write_text(json.dumps(raw))
    with pytest.raises(SystemExit, match="allowed_chat_ids"):
        main(["run", "--config", str(p)])


def test_BF_D6_lic_list_prefers_the_frozen_record_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from trader.bfast_config import LIC_LIST_ENV, lic_codes

    monkeypatch.delenv(LIC_LIST_ENV, raising=False)
    raw = _raw()
    raw["data"]["lic_list"] = str(tmp_path / "LIC_list_frozen.csv")
    raw["data"]["lic_list_fallback"] = str(tmp_path / "cand.csv")
    raw["data"]["lic_list_sha256"] = None
    cfg = BfastConfig.model_validate(raw)
    with pytest.raises(FileNotFoundError):
        lic_codes(cfg)  # never silently without a list
    (tmp_path / "cand.csv").write_text("code,name\nFGG,x\n")
    got = lic_codes(cfg)
    assert got.codes == {"FGG"} and got.path == tmp_path / "cand.csv" and not got.frozen
    assert "CANDIDATES" in got.describe()
    (tmp_path / "LIC_list_frozen.csv").write_text("code,name,reason\nAFI,a,b\nARG,c,d\n")
    got = lic_codes(cfg)
    assert got.codes == {"AFI", "ARG"} and got.frozen
    other = tmp_path / "elsewhere.csv"
    other.write_text("code,name,reason\nWAR,w,x\n")
    monkeypatch.setenv(LIC_LIST_ENV, str(other))
    assert lic_codes(cfg).codes == {"WAR"}
    (tmp_path / "LIC_list_frozen.csv").write_text("code,name,reason\n")
    monkeypatch.delenv(LIC_LIST_ENV)
    with pytest.raises(ValueError, match="no codes"):
        lic_codes(cfg)


def test_BF_D6_record_lic_list_covers_the_names_the_name_rule_misses() -> None:
    """The record's frozen list (when present here) holds FGG, FGX, PGF, WAR and PCX."""
    from trader.bfast_config import read_codes

    p = Path(os.environ.get("TRADER_BF_LIC_LIST", "/nonexistent"))
    cand = read_codes(Path(__file__).resolve().parent.parent / "config" / "lic_list_candidates.csv")
    assert {"FGG", "FGX", "PGF", "WAR", "PCX"} <= cand
    if p.is_file():
        assert {"FGG", "FGX", "PGF", "WAR", "PCX"} <= read_codes(p)


def test_BF_D6_repo_lic_list_is_the_registered_frozen_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``config/lic_list.csv`` is the record's ``LIC_list_frozen.csv`` byte for byte (SHA-256
    pinned in ``config/bfast.yaml``, ledger seq 39): 46 codes including the five the name
    rule misses. A file that differs from the pin is refused, never used silently."""
    from trader.bfast_config import LIC_LIST_ENV, lic_codes

    monkeypatch.delenv(LIC_LIST_ENV, raising=False)
    root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(root)
    cfg = load_bfast_config(CFG)
    got = lic_codes(cfg)
    assert got.frozen and got.path == Path("config/lic_list.csv") and len(got.codes) == 46
    assert {"FGG", "FGX", "PGF", "WAR", "PCX"} <= got.codes
    edited = tmp_path / "edited.csv"
    edited.write_bytes((root / "config" / "lic_list.csv").read_bytes() + b"XYZ,x,y\n")
    monkeypatch.setenv(LIC_LIST_ENV, str(edited))
    with pytest.raises(ValueError, match="not the registered"):
        lic_codes(cfg)
