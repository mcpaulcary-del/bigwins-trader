"""Config schema and validation (spec §18, §14): OPS-10, OPS-11, OPS-12."""

from __future__ import annotations

import io
import re
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from tests.conftest import COMMON_PATH, FAKE_SHA, REPO, user_dict, write_config_dir
from trader import cli
from trader.config import (
    ApprovalPinMismatchError,
    CommonConfig,
    ConfigPermissionError,
    ConfigValidationError,
    Ops12Mode,
    SecretInConfigError,
    check_approval_pins,
    compute_config_hash,
    default_sizing_nav,
    deployed_git_sha,
    enforce_ops12,
    find_secrets,
    load_config,
    ops12_check,
    ops12_mode,
    parse_common,
    sha256_bytes,
)
from trader.secrets import SecretError, SecretValue, read_secret


def _common(text: str | None = None) -> CommonConfig:
    return parse_common((text or COMMON_PATH.read_text()).encode())


def _common_with(old: str, new: str) -> bytes:
    src = COMMON_PATH.read_text()
    assert old in src, old
    return src.replace(old, new, 1).encode()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class TestCommonSchema:
    def test_repo_common_yaml_validates_with_spec_values(self) -> None:
        c = _common()
        assert c.universe == ["BHP", "RIO", "FMG", "CBA", "CSL", "WDS"]
        assert c.index_etf == "VAS"
        assert c.sizing.min_order_value_aud == Decimal("4000")
        assert c.execution.commission.min_aud_incl_gst == Decimal("6.60")
        assert c.filters.blackout.offsets_for("CSL") == (-3, 0)
        assert c.filters.blackout.offsets_for("BHP") == (-1, 0)
        assert c.signals.commodity.baskets["BHP"][0].weights == {"copper": 0.58, "iron_ore": 0.42}
        assert c.risk_defaults.backtest_max_drawdown is None

    def test_unknown_key_rejected(self) -> None:
        with pytest.raises(ConfigValidationError, match="Extra inputs"):
            parse_common(_common_with("version: 1", "version: 1\nsurprise: true"))

    def test_duplicate_key_rejected(self) -> None:
        with pytest.raises(ConfigValidationError, match="duplicate key"):
            parse_common(_common_with("version: 1", "version: 1\nversion: 1"))

    def test_unquoted_time_not_read_as_base60_integer(self) -> None:
        # Plain YAML 1.1 would read 19:30 as the integer 1170; the strict loader keeps
        # it a string, so it parses as the clock time.
        from datetime import time

        c = parse_common(_common_with('evening_report: "19:30"', "evening_report: 19:30"))
        assert c.schedule.evening_report == time(19, 30)

    def test_numeric_time_rejected(self) -> None:
        with pytest.raises(ConfigValidationError, match="quoted"):
            parse_common(_common_with('evening_report: "19:30"', "evening_report: 1170"))

    def test_news_filter_cannot_be_enabled_in_v1(self) -> None:
        with pytest.raises(ConfigValidationError, match="D7"):
            parse_common(_common_with("news: {enabled: false", "news: {enabled: true"))

    def test_family_weights_must_sum_to_one(self) -> None:
        with pytest.raises(ConfigValidationError, match="sum to 1"):
            parse_common(_common_with("{trend: 0.75, dip: 0.25}", "{trend: 0.70, dip: 0.25}"))

    def test_vol_floors_must_cover_universe(self) -> None:
        with pytest.raises(ConfigValidationError, match="vol_floors"):
            parse_common(_common_with("WDS: 0.20}", "VAS: 0.20}"))


class TestUserSchema:
    def test_example_user_config_loads(self, config_dir: Path) -> None:
        loaded = load_config(config_dir, "a", deployed_sha=FAKE_SHA)
        assert loaded.user.ibkr.port == 4004
        assert loaded.user.small_account.enabled is True
        assert loaded.user.small_account.asset == "VAS"
        assert loaded.user.capital_cap_aud == Decimal("5000")

    def test_port_must_match_mode(self, tmp_path: Path) -> None:
        u = user_dict()
        u["ibkr"] = {**u["ibkr"], "mode": "live"}  # type: ignore[dict-item]
        d = write_config_dir(tmp_path, user=u)
        with pytest.raises(ConfigValidationError, match="does not match mode"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_gateway_must_be_own_user(self, tmp_path: Path) -> None:
        u = user_dict()
        u["ibkr"] = {**u["ibkr"], "gateway_host": "gw-b"}  # type: ignore[dict-item]
        d = write_config_dir(tmp_path, user=u)
        with pytest.raises(ConfigValidationError, match="gw-a"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_user_name_must_match_file(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, name="b")
        with pytest.raises(ConfigValidationError):
            load_config(d, "b", deployed_sha=FAKE_SHA)

    def test_user_file_must_be_owner_only(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, mode=0o644)
        with pytest.raises(ConfigPermissionError, match="owner-only"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("max_order_value_aud", 30000),
            ("max_orders_per_day", 11),
            ("daily_loss_pct", 0.05),
            ("hard_drawdown_pct", 0.30),
        ],
    )
    def test_personal_limits_may_only_be_tighter(
        self, tmp_path: Path, field: str, value: object
    ) -> None:
        u = user_dict()
        u["limits"] = {**u["limits"], field: value}  # type: ignore[dict-item]
        d = write_config_dir(tmp_path, user=u)
        with pytest.raises(ConfigValidationError, match="only be tighter"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_tighter_personal_limits_accepted(self, tmp_path: Path) -> None:
        u = user_dict(
            limits={
                "max_order_value_aud": 10000,
                "max_orders_per_day": 4,
                "daily_loss_pct": 0.02,
                "hard_drawdown_pct": 0.20,
            }
        )
        loaded = load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)
        assert loaded.limits.max_order_value_aud == Decimal("10000")
        assert loaded.limits.max_orders_per_day == 4

    def test_exclude_symbols_must_be_universe(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, user=user_dict(exclude_symbols=["ANZ"]))
        with pytest.raises(ConfigValidationError, match="not in universe"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_small_account_asset_must_not_be_excluded(self, tmp_path: Path) -> None:
        u = user_dict(exclude_symbols=["BHP"], small_account={"enabled": True, "asset": "BHP"})
        with pytest.raises(ConfigValidationError, match="small_account.asset"):
            load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)

    def test_small_account_asset_restricted_to_vas_or_bhp(self, tmp_path: Path) -> None:
        u = user_dict(small_account={"enabled": True, "asset": "CBA"})
        with pytest.raises(ConfigValidationError):
            load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)

    def test_small_account_defaults_when_omitted(self, tmp_path: Path) -> None:
        u = user_dict()
        del u["small_account"]
        loaded = load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)
        assert loaded.user.small_account.enabled is True
        assert loaded.user.small_account.asset == "VAS"


# ---------------------------------------------------------------------------
# OPS-10: approval pins and config hash
# ---------------------------------------------------------------------------


class TestOPS10ApprovalPins:
    """OPS-10: every run stores the config hash; the trader refuses to run if the
    deployed code or common config doesn't match the user's approval pins."""

    def test_OPS_10_matching_pins_load(self, config_dir: Path) -> None:
        loaded = load_config(config_dir, "a", deployed_sha=FAKE_SHA)
        assert loaded.common_hash == sha256_bytes(COMMON_PATH.read_bytes())
        assert re.fullmatch(r"[0-9a-f]{64}", loaded.config_hash)

    def test_OPS_10_refuses_on_code_sha_mismatch(self, config_dir: Path) -> None:
        with pytest.raises(ApprovalPinMismatchError, match="approved_git_sha"):
            load_config(config_dir, "a", deployed_sha="f" * 40)

    def test_OPS_10_refuses_on_dirty_tree(self, config_dir: Path) -> None:
        with pytest.raises(ApprovalPinMismatchError):
            load_config(config_dir, "a", deployed_sha=FAKE_SHA + "-dirty")

    def test_OPS_10_refuses_when_code_sha_unknown(self, config_dir: Path) -> None:
        with pytest.raises(ApprovalPinMismatchError, match="could not be determined"):
            load_config(config_dir, "a", deployed_sha=None)

    def test_OPS_10_refuses_on_common_yaml_change(self, tmp_path: Path) -> None:
        # One byte changed in common.yaml (even a comment) needs re-approval.
        d = write_config_dir(tmp_path, common_text=COMMON_PATH.read_text() + "# edited\n")
        with pytest.raises(ApprovalPinMismatchError, match="approved_common_hash"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_OPS_10_pins_must_be_full_hashes(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, user=user_dict(approved_git_sha="…"))
        with pytest.raises(ConfigValidationError, match="40-char"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_OPS_10_config_hash_changes_with_either_file(self) -> None:
        c, u = b"common", b"user"
        h = compute_config_hash(c, u)
        assert h != compute_config_hash(c + b" ", u)
        assert h != compute_config_hash(c, u + b" ")
        assert h != compute_config_hash(u, c)
        assert h == compute_config_hash(c, u)

    def test_OPS_10_config_hash_is_stored_on_runs(self) -> None:
        from trader.ledger import Run

        col = Run.__table__.c.config_hash
        assert not col.nullable
        assert Run.__table__.c.git_sha is not None

    def test_OPS_10_check_pins_both_problems_reported(self) -> None:
        from trader.config import UserConfig

        u = UserConfig.model_validate(user_dict())
        with pytest.raises(ApprovalPinMismatchError) as ei:
            check_approval_pins(u, "0" * 64, "e" * 40)
        assert "approved_git_sha" in str(ei.value)
        assert "approved_common_hash" in str(ei.value)

    def test_OPS_10_deployed_sha_from_build_file(self, tmp_path: Path) -> None:
        f = tmp_path / "_build_sha.txt"
        f.write_text(FAKE_SHA + "\n")
        assert deployed_git_sha(build_sha_file=f) == FAKE_SHA

    def test_OPS_10_deployed_sha_from_git(self, tmp_path: Path) -> None:
        sha = deployed_git_sha(REPO, build_sha_file=tmp_path / "absent")
        assert sha is None or re.fullmatch(r"[0-9a-f]{40}(-dirty)?", sha)

    def test_OPS_10_cli_validate_config_refuses_mismatch(
        self, config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "deployed_git_sha", lambda: "a" * 40)
        err = io.StringIO()
        rc = cli.main(
            ["validate-config", "--user", "a", "--config-dir", str(config_dir)],
            out=io.StringIO(),
            err=err,
        )
        assert rc == cli.EXIT_PIN_MISMATCH
        assert "REFUSED" in err.getvalue()

    def test_OPS_10_cli_print_hashes(
        self, config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "deployed_git_sha", lambda: "b" * 40)
        out = io.StringIO()
        rc = cli.main(
            ["validate-config", "--user", "a", "--config-dir", str(config_dir), "--print-hashes"],
            out=out,
            err=io.StringIO(),
        )
        assert rc == cli.EXIT_OK
        assert f"approved_git_sha: {'b' * 40}" in out.getvalue()
        assert sha256_bytes(COMMON_PATH.read_bytes()) in out.getvalue()


# ---------------------------------------------------------------------------
# OPS-11: secrets never in config
# ---------------------------------------------------------------------------


class TestOPS11Secrets:
    """OPS-11: secrets never appear in config files; they come only from Docker secrets."""

    @pytest.mark.parametrize(
        "key", ["bot_token", "password", "eodhd_api_key", "tws_password", "passphrase", "secret"]
    )
    def test_OPS_11_secret_like_key_refused(self, tmp_path: Path, key: str) -> None:
        u = user_dict()
        u["alerts"] = {**u["alerts"], key: "x"}  # type: ignore[dict-item]
        with pytest.raises(SecretInConfigError, match="OPS-11"):
            load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)

    @pytest.mark.parametrize(
        "value",
        [
            "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsawQ",  # Telegram bot token shape
            "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ",
            "-----BEGIN OPENSSH PRIVATE KEY-----",
            "postgresql://trader:hunter2@postgres/ledger_a",
        ],
    )
    def test_OPS_11_secret_like_value_refused(self, tmp_path: Path, value: str) -> None:
        u = user_dict(dashboard={"snapshot_key_id": value})
        with pytest.raises(SecretInConfigError):
            load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)

    def test_OPS_11_secret_in_common_refused(self) -> None:
        with pytest.raises(SecretInConfigError):
            parse_common(_common_with("alerts: {", "alerts: {telegram_token: abc, "))

    def test_OPS_11_shipped_configs_have_no_secrets(self) -> None:
        from trader.yamlio import load_yaml

        for p in [COMMON_PATH, *(REPO / "config" / "examples").glob("*.yaml")]:
            assert find_secrets(load_yaml(p.read_text())) == [], p

    def test_OPS_11_public_key_fields_allowed(self) -> None:
        assert find_secrets(user_dict()) == []

    def test_OPS_11_secrets_read_only_from_docker_secrets_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from-env")
        monkeypatch.setenv("telegram_bot_token", "from-env")
        with pytest.raises(SecretError, match="not found"):
            read_secret("telegram_bot_token", tmp_path)
        (tmp_path / "telegram_bot_token").write_text("from-file\n")
        assert read_secret("telegram_bot_token", tmp_path).reveal() == "from-file"

    def test_OPS_11_unknown_secret_name_refused(self, tmp_path: Path) -> None:
        with pytest.raises(SecretError, match="unknown"):
            read_secret("../etc/passwd", tmp_path)

    def test_OPS_11_secret_value_never_printed(self) -> None:
        s = SecretValue("hunter2")
        assert "hunter2" not in repr(s)
        assert "hunter2" not in str(s)
        assert "hunter2" not in f"{s}"

    def test_OPS_11_live_user_configs_are_gitignored(self) -> None:
        ignore = (REPO / ".gitignore").read_text()
        for pattern in ("config/a.yaml", "config/b.yaml", "secrets/", ".env"):
            assert pattern in ignore

    def test_OPS_11_alembic_ini_has_no_url(self) -> None:
        text = (REPO / "alembic.ini").read_text()
        assert "sqlalchemy.url" not in text
        assert "://" not in text


# ---------------------------------------------------------------------------
# OPS-12: account size vs minimum order
# ---------------------------------------------------------------------------


class TestOPS12AccountSize:
    """OPS-12: at trader init and on any config change, validation fails (otherwise a
    warning in the evening report) if median full-trend position x sizing NAV is below
    min_order_value_aud (§9)."""

    def test_OPS_12_default_config_passes_at_50k(self) -> None:
        r = ops12_check(_common(), Decimal("50000"))
        assert r.ok
        # dip-ON trend weights, vol at floors: median of the six full-trend weights = 1/12.
        assert r.median_position_aud == Decimal("4166.67")
        assert r.dip_sleeve_assumed_on is True

    def test_OPS_12_fails_below_threshold(self) -> None:
        r = ops12_check(_common(), Decimal("45000"))
        assert not r.ok
        assert r.median_position_aud < r.min_order_value_aud

    def test_OPS_12_hard_mode_raises(self) -> None:
        r = ops12_check(_common(), Decimal("10000"))
        with pytest.raises(ConfigValidationError, match="OPS-12"):
            enforce_ops12(r, Ops12Mode.HARD)

    def test_OPS_12_warn_mode_returns_warning(self) -> None:
        r = ops12_check(_common(), Decimal("10000"))
        w = enforce_ops12(r, Ops12Mode.WARN)
        assert w is not None
        assert w.startswith("WARNING OPS-12")

    def test_OPS_12_pass_returns_nothing_in_either_mode(self) -> None:
        r = ops12_check(_common(), Decimal("200000"))
        assert enforce_ops12(r, Ops12Mode.HARD) is None
        assert enforce_ops12(r, Ops12Mode.WARN) is None

    def test_OPS_12_mode_hard_at_init_and_on_config_change(self) -> None:
        assert ops12_mode(is_init=True, config_hash="h", known_hashes=["h"]) is Ops12Mode.HARD
        assert ops12_mode(is_init=False, config_hash="new", known_hashes=["h"]) is Ops12Mode.HARD
        assert ops12_mode(is_init=False, config_hash="h", known_hashes=["h"]) is Ops12Mode.WARN

    def test_OPS_12_small_account_mode_warns_only(self) -> None:
        m = ops12_mode(is_init=True, config_hash="x", known_hashes=[], small_account_enabled=True)
        assert m is Ops12Mode.WARN

    def test_OPS_12_lower_min_order_makes_small_account_pass(self) -> None:
        c = parse_common(_common_with("min_order_value_aud: 4000", "min_order_value_aud: 2000"))
        assert ops12_check(c, Decimal("25000")).ok

    def test_OPS_12_uses_vol_estimates_when_given(self) -> None:
        c = _common()
        high = dict.fromkeys(c.universe, 0.6)  # very volatile: scale shrinks
        r = ops12_check(c, Decimal("50000"), vol_estimates=high)
        assert r.vol_source == "estimate"
        assert not r.ok

    def test_OPS_12_dip_off_uses_larger_trend_weight(self) -> None:
        c = _common()
        on = ops12_check(c, Decimal("50000"), dip_sleeve_on=True)
        off = ops12_check(c, Decimal("50000"), dip_sleeve_on=False)
        assert off.median_position_aud > on.median_position_aud

    def test_OPS_12_sizing_nav_must_be_decimal(self) -> None:
        with pytest.raises(TypeError):
            ops12_check(_common(), 50000.0)  # type: ignore[arg-type]

    def test_OPS_12_default_sizing_nav_is_capped(self, config_dir: Path) -> None:
        loaded = load_config(config_dir, "a", deployed_sha=FAKE_SHA)
        assert default_sizing_nav(loaded.user) == Decimal("5000")

    def test_OPS_12_cli_init_fails_hard_in_full_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "deployed_git_sha", lambda: FAKE_SHA)
        u = user_dict(small_account={"enabled": False, "asset": "VAS"})
        d = write_config_dir(tmp_path, user=u)
        err = io.StringIO()
        rc = cli.main(["init", "--user", "a", "--config-dir", str(d)], out=io.StringIO(), err=err)
        assert rc == cli.EXIT_CONFIG_INVALID
        assert "OPS-12" in err.getvalue()

    def test_OPS_12_cli_validate_config_fails_hard_on_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "deployed_git_sha", lambda: FAKE_SHA)
        u = user_dict(small_account={"enabled": False, "asset": "VAS"})
        d = write_config_dir(tmp_path, user=u)
        rc = cli.main(
            ["validate-config", "--user", "a", "--config-dir", str(d)],
            out=io.StringIO(),
            err=io.StringIO(),
        )
        assert rc == cli.EXIT_CONFIG_INVALID
        rc = cli.main(
            ["validate-config", "--user", "a", "--config-dir", str(d), "--sizing-nav", "60000"],
            out=io.StringIO(),
            err=io.StringIO(),
        )
        assert rc == cli.EXIT_OK

    def test_OPS_12_cli_small_account_warns(
        self, config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "deployed_git_sha", lambda: FAKE_SHA)
        out = io.StringIO()
        rc = cli.main(
            ["validate-config", "--user", "a", "--config-dir", str(config_dir)],
            out=out,
            err=io.StringIO(),
        )
        assert rc == cli.EXIT_OK
        assert "WARNING OPS-12" in out.getvalue()


def test_example_yaml_is_valid_yaml_mapping() -> None:
    assert isinstance(
        yaml.safe_load((REPO / "config/examples/user.example.yaml").read_text()), dict
    )
