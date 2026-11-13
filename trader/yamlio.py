"""Strict YAML loading for config files.

* Safe loader only.
* Floats are parsed as ``Decimal`` from their literal text, so money never
  passes through binary floating point (SYS-13).
* Duplicate mapping keys are an error (PyYAML silently keeps the last one).
* YAML 1.1 sexagesimal integers (``19:15`` -> 1155) are not resolved; such
  scalars stay strings so they fail schema validation loudly instead.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

import yaml


class YamlDuplicateKeyError(yaml.YAMLError):
    pass


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_decimal(loader: yaml.SafeLoader, node: yaml.Node) -> Decimal:
    assert isinstance(node, yaml.ScalarNode)
    text = str(loader.construct_scalar(node)).replace("_", "")
    lowered = text.lower()
    if lowered in {".nan", ".inf", "+.inf", "-.inf"}:
        raise yaml.constructor.ConstructorError(
            None, None, f"non-finite number {text!r} not allowed", node.start_mark
        )
    return Decimal(text)


def _construct_mapping(loader: yaml.SafeLoader, node: yaml.Node) -> dict[Any, Any]:
    assert isinstance(node, yaml.MappingNode)
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in result:
            raise YamlDuplicateKeyError(f"duplicate key {key!r} at {key_node.start_mark}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


_StrictLoader.add_constructor("tag:yaml.org,2002:float", _construct_decimal)
_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)

# Drop the YAML 1.1 implicit int resolver and re-add one without base-60.
_StrictLoader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:int"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_StrictLoader.add_implicit_resolver(
    "tag:yaml.org,2002:int",
    re.compile(
        r"""^(?:[-+]?0b[0-1_]+
        |[-+]?0[0-7_]+
        |[-+]?(?:0|[1-9][0-9_]*)
        |[-+]?0x[0-9a-fA-F_]+)$""",
        re.X,
    ),
    list("-+0123456789"),
)


def load_yaml(text: str) -> Any:
    """Parse YAML text with the strict loader."""
    return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - _StrictLoader is a SafeLoader
