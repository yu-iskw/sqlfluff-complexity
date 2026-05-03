"""Aggregate complexity scoring helpers."""

from __future__ import annotations

DEFAULT_WEIGHTS: dict[str, int] = {
    "ctes": 2,
    "joins": 2,
    "subquery_depth": 4,
    "case_expressions": 2,
    "boolean_operators": 1,
    "window_functions": 2,
    "cte_dependency_depth": 0,
    "set_operation_count": 0,
    "expression_depth": 0,
    "derived_tables": 0,
}

VALID_WEIGHT_KEYS = frozenset(DEFAULT_WEIGHTS)


def parse_weights(raw: str | None) -> dict[str, int]:
    """Parse a comma-separated complexity weight configuration string."""
    weights = DEFAULT_WEIGHTS.copy()
    if raw is None:
        return weights

    for raw_item in raw.split(","):
        item = raw_item.strip()
        if item:
            key, value = _parse_weight_item(item)
            weights[key] = value

    return weights


def _parse_weight_item(item: str) -> tuple[str, int]:
    key, separator, value = item.partition(":")
    if separator != ":":
        message = f"Invalid weight item {item!r}; expected key:value."
        raise ValueError(message)

    key = key.strip()
    if key not in VALID_WEIGHT_KEYS:
        message = f"Unknown complexity weight key {key!r}."
        raise ValueError(message)

    try:
        parsed_value = int(value.strip())
    except ValueError as exc:
        message = f"Complexity weight for {key!r} must be an integer."
        raise ValueError(message) from exc

    if parsed_value < 0:
        message = f"Complexity weight for {key!r} must be non-negative."
        raise ValueError(message)

    return key, parsed_value
