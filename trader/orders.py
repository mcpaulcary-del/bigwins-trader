"""build_orders(): targets -> OrderIntents (pure). Planned for M2 (spec v2.10 §20).

DAT-20 (sentinel unit) is defined here because it is applied inside
``build_orders()``, so the harness, paper and live behave identically.
"""

from __future__ import annotations


def sentinel_floor(target_units: int, *, sentinel_unit: bool) -> int:
    """DAT-20: with ``l1.sentinel_unit`` on, a target of zero units becomes 1 unit.

    The sentinel keeps the Flex mark (DAT-02 second source) alive while a sleeve is
    fully OFF. It is a quantity, not a parcel, and stays inside sizing NAV.
    """
    if target_units < 0:
        raise ValueError("target units are never negative (long only)")
    if sentinel_unit and target_units == 0:
        return 1
    return target_units
