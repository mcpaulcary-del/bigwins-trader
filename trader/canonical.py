"""Canonical JSON and hashes for decisions and batches (BW-SYS-10, BW-LED-01).

Same input -> byte-identical output: sorted keys, no whitespace, floats written
with 10 significant digits, ``Decimal`` as its string, dates in ISO form, NaN as null.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


def _norm(obj: Any) -> Any:  # noqa: PLR0911 - one branch per JSON type
    if obj is None or isinstance(obj, bool | str | int):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(format(obj, ".10g"))
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return _norm(obj.value)
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    if isinstance(obj, Mapping):
        return {str(k): _norm(v) for k, v in obj.items()}
    if isinstance(obj, Sequence | set | frozenset):
        items = sorted(obj, key=str) if isinstance(obj, set | frozenset) else obj
        return [_norm(v) for v in items]
    if hasattr(obj, "item"):  # numpy scalar
        return _norm(obj.item())
    raise TypeError(f"not canonical-JSON serialisable: {type(obj).__name__}")


def canonical_json(obj: Any) -> str:
    return json.dumps(_norm(obj), sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
