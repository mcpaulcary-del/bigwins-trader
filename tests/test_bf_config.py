"""B-fast config: the repo file validates; any live setting is refused (BW-EXE-09)."""

from __future__ import annotations

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


def test_lic_list_prefers_the_frozen_record_file(tmp_path: Path) -> None:
    from trader.bfast_config import lic_codes

    raw = _raw()
    raw["data"]["lic_list"] = str(tmp_path / "LIC_list_frozen.csv")
    raw["data"]["lic_list_fallback"] = str(tmp_path / "cand.csv")
    (tmp_path / "cand.csv").write_text("code,name\nFGG,x\n")
    codes, src = lic_codes(BfastConfig.model_validate(raw))
    assert codes == {"FGG"} and src == tmp_path / "cand.csv"
    (tmp_path / "LIC_list_frozen.csv").write_text("code,name,reason\nAFI,a,b\nARG,c,d\n")
    codes, src = lic_codes(BfastConfig.model_validate(raw))
    assert codes == {"AFI", "ARG"} and src == tmp_path / "LIC_list_frozen.csv"
