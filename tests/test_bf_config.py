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


def test_repo_config_validates_and_matches_engine_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TRADER_BF_LIC_LIST", raising=False)
    monkeypatch.chdir(CFG.parent.parent)  # data.lic_list is relative to the repository
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


def test_BF_D21_lic_list_fails_closed_without_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BF-D21: only the pinned frozen file is accepted; missing, changed, empty or
    undecodable is a ``LicListError`` (never the 5-code candidates file)."""
    import hashlib

    from trader.bfast_config import LIC_LIST_ENV, LicListError, lic_codes

    monkeypatch.delenv(LIC_LIST_ENV, raising=False)
    good = b"code,name,reason\nAFI,a,b\nARG,c,d\n"
    raw = _raw()
    frozen = tmp_path / "LIC_list_frozen_v2.csv"
    raw["data"]["lic_list"] = str(frozen)
    raw["data"]["lic_list_sha256"] = hashlib.sha256(good).hexdigest()
    cfg = BfastConfig.model_validate(raw)
    (tmp_path / "cand.csv").write_text("code,name\nFGG,x\n")  # a candidates file is ignored
    with pytest.raises(LicListError, match="missing"):
        lic_codes(cfg)
    frozen.write_bytes(good)
    got = lic_codes(cfg)
    assert got.codes == {"AFI", "ARG"} and got.path == frozen
    assert got.sha256 == raw["data"]["lic_list_sha256"] and "frozen record list" in got.describe()
    other = tmp_path / "elsewhere.csv"
    other.write_bytes(good)
    monkeypatch.setenv(LIC_LIST_ENV, str(other))  # another path, the same registered bytes
    assert lic_codes(cfg).path == other
    monkeypatch.delenv(LIC_LIST_ENV)
    frozen.write_bytes(good + b"WAR,w,x\n")
    with pytest.raises(LicListError, match="not the registered"):
        lic_codes(cfg)
    empty = b"code,name,reason\n"  # pinned but empty: still refused
    frozen.write_bytes(empty)
    cfg2 = BfastConfig.model_validate(
        {**raw, "data": {**raw["data"], "lic_list_sha256": hashlib.sha256(empty).hexdigest()}}
    )
    with pytest.raises(LicListError, match="no codes"):
        lic_codes(cfg2)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("lic_list_sha256", None),  # the pin is required
        ("lic_list_fallback", "config/lic_list_candidates.csv"),  # no fallback any more
    ],
)
def test_BF_D21_config_requires_the_pin_and_has_no_fallback(key: str, value: object) -> None:
    raw = _raw()
    if value is None:
        del raw["data"][key]
    else:
        raw["data"][key] = value
    with pytest.raises(ValidationError):
        BfastConfig.model_validate(raw)


def test_BF_D21_validate_config_and_emg2_list_refuse_a_missing_lic_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    from trader.bfast_config import LIC_LIST_ENV

    monkeypatch.setenv(LIC_LIST_ENV, str(tmp_path / "gone.csv"))
    raw = json.loads(json.dumps(_raw(), default=str))
    p = tmp_path / "c.yaml"
    p.write_text(json.dumps(raw))
    assert main(["validate-config", "--config", str(p)]) == 2
    with pytest.raises(SystemExit, match="BF-D21"):
        main(["emg2-list", "--asof", "2026-11-30", "--config", str(p), "--store", str(tmp_path)])


def test_BF_D21_store_providers_refuse_to_build_a_panel_without_the_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import date

    from trader.bf_dryrun import store_providers
    from trader.bfast_config import LIC_LIST_ENV, LicListError

    (tmp_path / "manifest.tsv").write_text("kind\tdate\tpath\n")
    monkeypatch.setenv(LIC_LIST_ENV, str(tmp_path / "gone.csv"))
    cfg = load_bfast_config(CFG)
    panel, _, _, note = store_providers(cfg, tmp_path, [date(2026, 11, 30)])
    assert note.startswith("LIC list REFUSED (BF-D21)")
    with pytest.raises(LicListError):
        panel(date(2026, 11, 30))


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
    """``config/lic_list.csv`` is the record's ``LIC_list_frozen_v2.csv`` byte for byte
    (SHA-256 pinned in ``config/bfast.yaml``, ledger seq 62, BF-D20): 69 codes = the 46 of
    v1 (ledger seq 39) including the five the old name rule missed, plus the 23 traded LICs
    the old name rule alone excluded. A file that differs from the pin is refused."""
    from trader.bfast_config import LIC_LIST_ENV, LicListError, lic_codes

    monkeypatch.delenv(LIC_LIST_ENV, raising=False)
    root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(root)
    cfg = load_bfast_config(CFG)
    got = lic_codes(cfg)
    assert got.path == Path("config/lic_list.csv") and len(got.codes) == 69
    assert {"FGG", "FGX", "PGF", "WAR", "PCX"} <= got.codes
    assert {"AFI", "ARG", "MFF", "BKI", "AUI", "DJW", "AIQ"} <= got.codes  # BF-D20 additions
    assert not {"PNI", "PMV", "NGI", "AEF", "RG1", "NZK", "CIW"} & got.codes  # companies
    edited = tmp_path / "edited.csv"
    edited.write_bytes((root / "config" / "lic_list.csv").read_bytes() + b"XYZ,x,y\n")
    monkeypatch.setenv(LIC_LIST_ENV, str(edited))
    with pytest.raises(LicListError, match="not the registered"):
        lic_codes(cfg)
