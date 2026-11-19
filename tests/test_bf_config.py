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
