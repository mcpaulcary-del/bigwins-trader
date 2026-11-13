"""SYS-13: money uses Decimal in orders, risk, ledger, tax and broker layers;
floats only inside signal maths."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import Engine, Numeric, select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from tests.conftest import COMMON_PATH
from trader.config import parse_common
from trader.ledger import Base, CashLedger, MoneyType
from trader.money import MoneyTypeError, require_decimal, to_money
from trader.yamlio import load_yaml

# Column names that carry AUD amounts or prices in the §12 tables.
MONEY_COLUMN_NAMES = {
    "amount", "cash_amount", "cash_aud", "franking_credit_aud", "withholding", "proceeds",
    "cost_base", "gain", "commission", "gst", "price", "ref_price", "limit_price", "close",
    "value", "nav", "cash_total", "cash_settled", "net_flow", "value_30jun2027",
}  # fmt: skip
# signal scores are floats in [0, 1] (signal maths), not money; flags.value is a bool.
NOT_MONEY_TABLES = {"signals", "shadow_signals", "flags"}  # flags.value is a bool


def test_SYS_13_to_money_rejects_float() -> None:
    with pytest.raises(MoneyTypeError):
        to_money(0.1)  # type: ignore[arg-type]
    with pytest.raises(MoneyTypeError):
        to_money(True)


def test_SYS_13_to_money_quantises_to_numeric_18_4() -> None:
    assert to_money("6.60") == Decimal("6.6000")
    assert to_money(Decimal("1.23456")) == Decimal("1.2346")
    assert to_money(25000) == Decimal("25000.0000")
    with pytest.raises(MoneyTypeError):
        to_money("NaN")
    with pytest.raises(MoneyTypeError):
        to_money("abc")


def test_SYS_13_require_decimal() -> None:
    assert require_decimal(Decimal(1)) == Decimal(1)
    with pytest.raises(MoneyTypeError):
        require_decimal(1.0, "price")


def test_SYS_13_yaml_numbers_parse_as_exact_decimal() -> None:
    data = load_yaml("a: 6.60\nb: 0.00088\nc: 0.1\n")
    assert data == {"a": Decimal("6.60"), "b": Decimal("0.00088"), "c": Decimal("0.1")}
    assert all(isinstance(v, Decimal) for v in data.values())


def test_SYS_13_config_money_fields_are_decimal() -> None:
    c = parse_common(COMMON_PATH.read_bytes())
    for v in (
        c.sizing.min_order_value_aud,
        c.sizing.min_exit_value_aud,
        c.execution.commission.min_aud_incl_gst,
        c.execution.commission.rate_incl_gst,
        c.execution.collar,
        c.risk_defaults.max_order_value_aud,
        c.risk_defaults.max_order_value_pct,
        *c.backtest.initial_navs,
    ):
        assert isinstance(v, Decimal), v
    assert c.execution.commission.min_aud_incl_gst == Decimal("6.60")


def test_SYS_13_config_money_rejects_python_float() -> None:
    from trader.config import Commission

    with pytest.raises(ValueError, match="decimal literal"):
        Commission.model_validate(
            {"min_aud_incl_gst": 6.6, "rate_incl_gst": "0.00088", "tolerance": 0.1}
        )


def test_SYS_13_every_money_column_is_numeric_18_4_decimal() -> None:
    seen = 0
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.name in MONEY_COLUMN_NAMES and table.name not in NOT_MONEY_TABLES:
                seen += 1
                assert isinstance(col.type, MoneyType), f"{table.name}.{col.name}"
                impl = col.type.impl
                assert isinstance(impl, Numeric)
                assert (impl.precision, impl.scale, impl.asdecimal) == (18, 4, True)
    assert seen >= 20


def test_SYS_13_money_column_refuses_float_and_roundtrips_decimal(sqlite_engine: Engine) -> None:
    ts = datetime(2026, 11, 13, 8, 0, tzinfo=UTC)
    with Session(sqlite_engine) as s:
        s.add(
            CashLedger(
                external_id="X1",
                ts=ts,
                type="deposit",
                amount=0.1,
                settle_date=date(2026, 11, 13),
            )
        )
        with pytest.raises(StatementError, match="Decimal"):
            s.flush()
        s.rollback()
        s.add(
            CashLedger(
                external_id="X2",
                ts=ts,
                type="deposit",
                amount=Decimal("1234.5678"),
                settle_date=date(2026, 11, 13),
            )
        )
        s.commit()
        got = s.execute(
            select(CashLedger.amount).where(CashLedger.external_id == "X2")
        ).scalar_one()
    assert isinstance(got, Decimal)
    assert got == Decimal("1234.5678")


def test_SYS_13_floats_only_in_signal_modules() -> None:
    """Static guard: money-layer modules never call float() on values."""
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "trader"
    money_layers = [
        "orders.py",
        "risk.py",
        "ledger.py",
        "tax.py",
        "money.py",
        "execution.py",
        "broker",
    ]
    for name in money_layers:
        p = root / name
        for f in [p] if p.is_file() else sorted(p.rglob("*.py")):
            tree = ast.parse(f.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id != "float", f"float() used in {f}"
