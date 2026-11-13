"""Config schema and validation (spec v2.10 §18): OPS-10, OPS-11, OPS-12."""

from __future__ import annotations

import io
import re
from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from tests.conftest import COMMON_PATH, FAKE_SHA, REPO, user_dict, write_config_dir
from trader import cli
from trader.config import (
    ApprovalPinMismatchError,
    CardEvidence,
    CommonConfig,
    ConfigPermissionError,
    ConfigValidationError,
    SecretInConfigError,
    UserConfig,
    check_approval_pins,
    compute_config_hash,
    default_sizing_nav,
    deployed_git_sha,
    enforce_ops12,
    find_secrets,
    income_year,
    load_config,
    ops12_check,
    parse_common,
    sha256_bytes,
    tranche_count,
)
from trader.secrets import SecretError, SecretValue, read_secret

SPEC = Path("/nonexistent")  # the spec is not shipped with the repo
TODAY = date(2026, 11, 13)


def _common(text: str | None = None) -> CommonConfig:
    return parse_common((text or COMMON_PATH.read_text()).encode())


def _common_with(old: str, new: str) -> bytes:
    src = COMMON_PATH.read_text()
    assert old in src, old
    return src.replace(old, new, 1).encode()


def _user(**overrides: object) -> UserConfig:
    return UserConfig.model_validate(user_dict(**overrides))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class TestCommonSchema:
    def test_repo_common_yaml_validates_with_spec_values(self) -> None:
        c = _common()
        assert c.version == 3
        assert c.rule == "L1"
        assert {k: v.base_weight for k, v in c.sleeves.items()} == {
            "VAS": Decimal("0.40"),
            "VGS": Decimal("0.60"),
        }
        assert c.benchmarks.B1.weights == {"DHHF": Decimal("1.0")}
        assert c.l1.min_order_value_aud == Decimal("1000")
        assert c.l1.tranche_offsets_by_n[3] == ["last", 7, 14]
        assert c.l1.cash_etf is None
        assert c.venue.XASX.opening_auction == time(9, 59)
        assert c.venue.XASX.closing_auction == (time(16, 10), time(16, 11))
        assert c.venue.XASX.close_available_after == time(16, 25)
        assert c.data.eodhd.calls_per_day == 20
        assert c.data.eodhd.on_budget_exceeded == "fail_closed"
        assert c.data.eodhd.instruments == ["VAS", "VGS", "DHHF"]
        assert c.execution.commission.budget_min_incl_gst_aud == Decimal("6.60")
        assert c.risk_defaults.backtest_max_drawdown is None
        assert c.benchmark_only_symbols == frozenset({"DHHF"})

    def test_withdrawn_share_strategy_keys_rejected(self) -> None:
        for block in (
            "universe: [BHP, RIO]",
            "small_account: {enabled: true}",
            "signals: {}",
            "filters: {}",
        ):
            with pytest.raises(ConfigValidationError, match="Extra inputs"):
                parse_common(_common_with("version: 3", f"version: 3\n{block}"))

    def test_unknown_key_rejected(self) -> None:
        with pytest.raises(ConfigValidationError, match="Extra inputs"):
            parse_common(_common_with("version: 3", "version: 3\nsurprise: true"))

    def test_duplicate_key_rejected(self) -> None:
        with pytest.raises(ConfigValidationError, match="duplicate key"):
            parse_common(_common_with("version: 3", "version: 3\nversion: 3"))

    def test_unquoted_time_not_read_as_base60_integer(self) -> None:
        c = parse_common(_common_with('daily_digest: "20:00"', "daily_digest: 20:00"))
        assert c.schedule.daily_digest == time(20, 0)

    def test_numeric_time_rejected(self) -> None:
        with pytest.raises(ConfigValidationError, match="quoted"):
            parse_common(_common_with('daily_digest: "20:00"', "daily_digest: 1200"))

    def test_sleeve_weights_must_sum_to_one(self) -> None:
        with pytest.raises(ConfigValidationError, match="sum to exactly 1"):
            parse_common(_common_with("VGS: {base_weight: 0.60}", "VGS: {base_weight: 0.50}"))

    def test_cash_etf_cannot_be_enabled(self) -> None:
        with pytest.raises(ConfigValidationError):
            parse_common(_common_with("cash_etf: null", "cash_etf: AAA"))

    def test_eodhd_must_fail_closed_and_cover_every_instrument(self) -> None:
        with pytest.raises(ConfigValidationError):
            parse_common(_common_with("on_budget_exceeded: fail_closed", "on_budget_exceeded: x"))
        with pytest.raises(ConfigValidationError, match="DHHF"):
            parse_common(_common_with("instruments: [VAS, VGS, DHHF]", "instruments: [VAS, VGS]"))

    def test_release_backtest_max_drawdown_must_be_null(self) -> None:
        with pytest.raises(ConfigValidationError):
            parse_common(_common_with("backtest_max_drawdown: null", "backtest_max_drawdown: 0.30"))

    def test_venue_auction_order_checked(self) -> None:
        with pytest.raises(ConfigValidationError, match="venue"):
            parse_common(
                _common_with(
                    'closing_auction: ["16:10:00", "16:11:00"]',
                    'closing_auction: ["16:11:00", "16:10:00"]',
                )
            )

    def test_schedule_order_checked(self) -> None:
        with pytest.raises(ConfigValidationError, match="increasing"):
            parse_common(_common_with('decide: "08:10"', 'decide: "07:10"'))

    def test_marginal_rates_year_keyed_r37(self) -> None:
        r = _common().research
        assert r.rates_for(date(2026, 11, 13)) == [
            Decimal(x) for x in ("0.00", "0.15", "0.30", "0.37", "0.45")
        ]
        assert r.rates_for(date(2027, 7, 1))[1] == Decimal("0.14")  # type: ignore[index]
        assert r.rates_for(date(2030, 1, 1)) is None
        assert income_year(date(2027, 6, 30)) == "2026-27"
        assert income_year(date(2027, 7, 1)) == "2027-28"


class TestUserSchema:
    def test_example_user_config_loads(self, config_dir: Path) -> None:
        loaded = load_config(config_dir, "a", deployed_sha=FAKE_SHA)
        u = loaded.user
        assert u.ibkr.active().port == 4004
        assert u.mode == "STATIC"
        assert u.hosting == "owner_host"
        assert u.capital_cap_aud == Decimal("5000")
        assert u.tranche_offsets == ["last"]
        assert loaded.limits.max_orders_per_day == 6

    @pytest.mark.parametrize(
        ("path", "value", "match"),
        [
            (("ibkr", "live", "port"), 4004, "4003"),
            (("ibkr", "paper", "client_id"), 12, "client_id"),
            (("ibkr", "paper", "gateway_host"), "gw-b-paper", "gw-a-paper"),
            (("ibkr", "live", "account_id"), "DU1234567", "live account"),
            (("eodhd", "licensee"), "b", "licence"),
            (("tax", "entity"), "company", "individual"),
            (("tax", "residency"), "foreign", "resident"),
            (("hosting",), "shared_host", "owner_host"),
            (("mode",), "FULL", "STATIC"),
            (("tranche_offsets",), ["last", 7], "at most 1"),
        ],
    )
    def test_user_field_rules(
        self, tmp_path: Path, path: tuple[str, ...], value: object, match: str
    ) -> None:
        u = user_dict()
        node: dict[str, object] = u
        for k in path[:-1]:
            node = node[k]  # type: ignore[assignment]
        node[path[-1]] = value
        with pytest.raises(ConfigValidationError, match=match):
            load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)

    def test_withdrawn_user_keys_rejected(self, tmp_path: Path) -> None:
        for key, value in (("small_account", {"enabled": True}), ("backtest", {"initial_nav": 1})):
            u = user_dict(**{key: value})
            with pytest.raises(ConfigValidationError, match="Extra inputs"):
                load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)

    def test_user_name_must_match_file(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, name="b")
        with pytest.raises(ConfigValidationError):
            load_config(d, "b", deployed_sha=FAKE_SHA)

    def test_user_file_must_be_owner_only(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, mode=0o644)
        with pytest.raises(ConfigPermissionError, match="owner-only"):
            load_config(d, "a", deployed_sha=FAKE_SHA)

    def test_personal_limits_may_only_be_tighter(self, tmp_path: Path) -> None:
        u = user_dict(limits={"max_orders_per_day": 7, "backtest_max_drawdown": None})
        with pytest.raises(ConfigValidationError, match="only be tighter"):
            load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)
        u = user_dict(limits={"max_orders_per_day": 4, "backtest_max_drawdown": "0.31"})
        loaded = load_config(write_config_dir(tmp_path, user=u), "a", deployed_sha=FAKE_SHA)
        assert loaded.limits.max_orders_per_day == 4
        assert loaded.limits.backtest_max_drawdown == Decimal("0.31")

    def test_exclude_symbols_must_be_sleeves(self, tmp_path: Path) -> None:
        d = write_config_dir(tmp_path, user=user_dict(exclude_symbols=["DHHF"]))
        with pytest.raises(ConfigValidationError, match="not live sleeves"):
            load_config(d, "a", deployed_sha=FAKE_SHA)


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

    def test_OPS_10_config_spec_and_card_hashes_are_stored_on_runs(self) -> None:
        from trader.ledger import Run

        cols = Run.__table__.c
        assert not cols.config_hash.nullable
        assert not cols.spec_hash.nullable
        assert not cols.git_sha.nullable
        assert cols.card_set_hash.nullable  # null until the card set is frozen (C-12)

    def test_OPS_10_run_hashes_carry_spec_and_card_set_hash(self, config_dir: Path) -> None:
        loaded = load_config(config_dir, "a", deployed_sha=FAKE_SHA)
        rh = loaded.run_hashes
        assert rh.config_hash == loaded.config_hash
        assert rh.spec_hash == loaded.common.spec_hash
        assert re.fullmatch(r"[0-9a-f]{64}", rh.spec_hash)
        assert rh.card_set_hash is None

    def test_OPS_10_spec_hash_must_be_a_real_hash(self) -> None:
        with pytest.raises(ConfigValidationError, match="SHA-256"):
            parse_common(_common_with('spec_hash: "c7f0', 'spec_hash: "…'))

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
            "https://eodhd.com/api/eod/VAS.AU?api_token=abcdef0123456789",
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
# OPS-12 (v2.10)
# ---------------------------------------------------------------------------


H1_OK = CardEvidence(h1_passed_with_approval=True, h11_passed_rates=frozenset({Decimal("0.37")}))


class TestOPS12:
    """OPS-12: validation fails at trader init and on any config change if a transition
    order implied by the tranche count is below min_order_value_aud; the tax flags are
    wrong; marginal_rate is unset for a live account or not a listed rate; hosting is
    wrong; mode L1 lacks H1/H11 evidence; or backtest_max_drawdown is unset for a live
    L1 account."""

    def test_OPS_12_default_config_passes_at_5000_with_n1(self) -> None:
        r = ops12_check(_common(), _user(), Decimal("5000"), as_of=TODAY)
        assert r.ok, r.problems
        assert r.tranche_count == 1
        assert r.transition_orders == {"VAS": Decimal("2000.00"), "VGS": Decimal("3000.00")}

    def test_OPS_12_tranche_count_threshold_is_9375(self) -> None:
        c = _common()
        assert tranche_count(c, Decimal("9374.99")) == 1
        assert tranche_count(c, Decimal("9375")) == 3
        r = ops12_check(c, _user(), Decimal("9375"), as_of=TODAY)
        assert r.tranche_count == 3
        assert r.ok  # smallest transition order 1250 >= 1000

    def test_OPS_12_transition_order_below_minimum_fails(self) -> None:
        r = ops12_check(_common(), _user(), Decimal("2400"), as_of=TODAY)
        assert not r.ok
        assert any("VAS transition order 960.00" in p for p in r.problems)
        with pytest.raises(ConfigValidationError, match="OPS-12"):
            enforce_ops12(r)

    def test_OPS_12_marginal_rate_required_for_live_and_must_be_listed(self) -> None:
        live = user_dict()
        live["ibkr"]["mode"] = "live"  # type: ignore[index]
        r = ops12_check(_common(), UserConfig.model_validate(live), Decimal("5000"), as_of=TODAY)
        assert any("must be set for a live account" in p for p in r.problems)
        r = ops12_check(
            _common(),
            _user(tax={**user_dict()["tax"], "marginal_rate": "0.32"}),  # type: ignore[dict-item]
            Decimal("5000"),
            as_of=TODAY,
        )
        assert any("not one of research.marginal_rates[2026-27]" in p for p in r.problems)
        ok = _user(tax={**user_dict()["tax"], "marginal_rate": "0.15"})  # type: ignore[dict-item]
        assert ops12_check(_common(), ok, Decimal("5000"), as_of=TODAY).ok
        # 0.15 is not a 2027-28 rate (R37: lowest rate 0.14 from 1 July 2027)
        assert not ops12_check(_common(), ok, Decimal("5000"), as_of=date(2027, 7, 1)).ok

    def test_OPS_12_paper_account_may_leave_marginal_rate_unset(self) -> None:
        assert ops12_check(_common(), _user(), Decimal("5000"), as_of=TODAY).ok

    def test_OPS_12_mode_L1_needs_card_evidence(self) -> None:
        u = _user(mode="L1", tax={**user_dict()["tax"], "marginal_rate": "0.37"})  # type: ignore[dict-item]
        r = ops12_check(_common(), u, Decimal("5000"), None, as_of=TODAY)
        assert any("card H1" in p for p in r.problems)
        assert any("card_set_hash is null" in p for p in r.problems)
        frozen = parse_common(
            _common_with("card_set_hash: null", 'card_set_hash: "' + "a" * 64 + '"')
        )
        assert ops12_check(frozen, u, Decimal("5000"), H1_OK, as_of=TODAY).ok
        h11_other = CardEvidence(True, frozenset({Decimal("0.45")}))
        r = ops12_check(frozen, u, Decimal("5000"), h11_other, as_of=TODAY)
        assert any("H11" in p for p in r.problems)

    def test_OPS_12_live_L1_needs_backtest_max_drawdown(self) -> None:
        d = user_dict(mode="L1", tax={**user_dict()["tax"], "marginal_rate": "0.37"})  # type: ignore[dict-item]
        d["ibkr"]["mode"] = "live"  # type: ignore[index]
        frozen = parse_common(
            _common_with("card_set_hash: null", 'card_set_hash: "' + "a" * 64 + '"')
        )
        r = ops12_check(frozen, UserConfig.model_validate(d), Decimal("5000"), H1_OK, as_of=TODAY)
        assert r.problems == ("limits.backtest_max_drawdown must be set for a live account in L1",)
        d["limits"] = {"max_orders_per_day": 6, "backtest_max_drawdown": "0.28"}
        assert ops12_check(
            frozen, UserConfig.model_validate(d), Decimal("5000"), H1_OK, as_of=TODAY
        ).ok

    def test_OPS_12_tax_and_hosting_values_refused_by_schema(self, tmp_path: Path) -> None:
        tax = dict(user_dict()["tax"])  # type: ignore[call-overload]
        patches: list[dict[str, object]] = [
            {"hosting": "shared_host"},
            {"tax": {**tax, "entity": "smsf"}},
        ]
        for patch in patches:
            with pytest.raises(ConfigValidationError):
                load_config(
                    write_config_dir(tmp_path, user=user_dict(**patch)), "a", deployed_sha=FAKE_SHA
                )

    def test_OPS_12_sizing_nav_must_be_decimal(self) -> None:
        with pytest.raises(TypeError):
            ops12_check(_common(), _user(), 5000.0)  # type: ignore[arg-type]

    def test_OPS_12_default_sizing_nav_is_the_capital_cap(self, config_dir: Path) -> None:
        loaded = load_config(config_dir, "a", deployed_sha=FAKE_SHA)
        assert default_sizing_nav(loaded.user) == Decimal("5000")

    def test_OPS_12_cli_init_and_validate_config_fail_hard(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cli, "deployed_git_sha", lambda: FAKE_SHA)
        d = write_config_dir(tmp_path, user=user_dict(capital_cap_aud=2400))
        for cmd in ("init", "validate-config"):
            err = io.StringIO()
            rc = cli.main([cmd, "--user", "a", "--config-dir", str(d)], out=io.StringIO(), err=err)
            assert rc == cli.EXIT_CONFIG_INVALID
            assert "OPS-12" in err.getvalue()
        rc = cli.main(
            ["validate-config", "--user", "a", "--config-dir", str(d), "--sizing-nav", "5000"],
            out=io.StringIO(),
            err=io.StringIO(),
        )
        assert rc == cli.EXIT_OK

    def test_OPS_12_cli_validate_config_passes_default(
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
        assert "N=1" in out.getvalue()


def test_example_yaml_is_valid_yaml_mapping() -> None:
    assert isinstance(
        yaml.safe_load((REPO / "config/examples/user.example.yaml").read_text()), dict
    )
