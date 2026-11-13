"""Money handling (SYS-13).

Money is ``Decimal`` in orders, risk, ledger, tax and broker layers. Floats are
allowed only inside signal maths. Conversions from ``float`` are refused here so
that a float can never silently become money.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import NewType

from trader.constants import MONEY_QUANTUM

AUD = NewType("AUD", Decimal)


class MoneyTypeError(TypeError):
    """Raised when a non-Decimal-safe value (e.g. float) is used as money."""


def to_money(value: Decimal | int | str) -> AUD:
    """Convert to AUD money quantised to NUMERIC(18,4).

    ``float`` is rejected (SYS-13). ``bool`` is rejected (it is an ``int``).
    """
    if isinstance(value, bool | float):
        raise MoneyTypeError(f"money must not be built from {type(value).__name__}: {value!r}")
    if not isinstance(value, Decimal | int | str):
        raise MoneyTypeError(f"unsupported money type {type(value).__name__}")
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise MoneyTypeError(f"not a number: {value!r}") from exc
    if not d.is_finite():
        raise MoneyTypeError(f"money must be finite: {value!r}")
    return AUD(d.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN))


def require_decimal(value: object, name: str = "value") -> Decimal:
    """Assert that a money value is a ``Decimal`` (used at layer boundaries)."""
    if not isinstance(value, Decimal):
        raise MoneyTypeError(f"{name} must be Decimal, got {type(value).__name__}")
    return value
