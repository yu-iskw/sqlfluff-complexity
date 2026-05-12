"""Aggregate complexity scoring helpers."""

from __future__ import annotations

import json

DEFAULT_WEIGHTS: dict[str, int] = {
    "aggregation_complexity": 0,
    "boolean_operators": 1,
    "case_expressions": 2,
    "cte_dependency_depth": 2,
    "ctes": 2,
    "derived_tables": 2,
    "expression_depth": 1,
    "joins": 2,
    "select_targets": 0,
    "set_operation_count": 2,
    "source_relations": 0,
    "subquery_depth": 4,
    "window_functions": 2,
}

VALID_WEIGHT_KEYS = frozenset(DEFAULT_WEIGHTS)

_JSON_OBJECT_REQUIRED = (
    "complexity_weights must be a JSON object string starting with '{'; "
    "the comma-separated key:value form is no longer supported."
)


def _validate_known_key(key: str) -> None:
    if key not in VALID_WEIGHT_KEYS:
        message = f"Unknown complexity weight key {key!r}."
        raise ValueError(message)


def _validate_non_negative_weight(key: str, parsed_value: int) -> None:
    if parsed_value < 0:
        message = f"Complexity weight for {key!r} must be non-negative."
        raise ValueError(message)


def _coerce_json_weight_value(key: str, value: object) -> int:
    """Return a non-negative int weight from JSON, rejecting booleans and floats."""
    if isinstance(value, bool):
        message = f"Complexity weight for {key!r} must be an integer, not bool."
        raise TypeError(message)
    if isinstance(value, int):
        _validate_non_negative_weight(key, value)
        return value
    message = f"Complexity weight for {key!r} must be an integer."
    raise TypeError(message)


def _parse_weights_from_json_object(stripped: str, weights: dict[str, int]) -> dict[str, int]:
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as exc:
        message = f"Invalid JSON for complexity_weights: {exc}"
        raise ValueError(message) from exc

    if not isinstance(obj, dict):
        message = "complexity_weights JSON must be an object {...}, not an array or scalar."
        raise TypeError(message)

    for key, value in obj.items():
        if not isinstance(key, str):
            message = "complexity_weights JSON keys must be strings."
            raise TypeError(message)
        _validate_known_key(key)
        weights[key] = _coerce_json_weight_value(key, value)

    return weights


def parse_weights(raw: str | None) -> dict[str, int]:
    """Parse ``complexity_weights`` from a JSON object string.

    ``None`` or whitespace-only input yields ``DEFAULT_WEIGHTS`` unchanged.
    Any other non-empty value, after stripping surrounding whitespace and an
    optional UTF-8 BOM, must start with ``{`` and parse as a JSON object;
    omitted keys keep defaults.

    Raises ``ValueError`` on invalid input (including JSON shape and weight
    types); does not raise ``TypeError`` at this boundary.
    """
    weights = DEFAULT_WEIGHTS.copy()
    if raw is None:
        return weights

    stripped = raw.strip().removeprefix("\ufeff").strip()
    if not stripped:
        return weights

    if not stripped.startswith("{"):
        raise ValueError(_JSON_OBJECT_REQUIRED)

    try:
        return _parse_weights_from_json_object(stripped, weights)
    except TypeError as exc:
        raise ValueError(str(exc)) from exc
