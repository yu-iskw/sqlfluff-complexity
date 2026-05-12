"""Path-specific complexity policy resolution."""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, replace
from typing import Any

from sqlfluff_complexity.core.config.validation import ConfigValidationError

POLICY_INTEGER_KEYS = frozenset(
    {
        "max_ctes",
        "max_joins",
        "max_subquery_depth",
        "max_case_expressions",
        "max_boolean_operators",
        "max_window_functions",
        "max_cte_dependency_depth",
        "max_nested_case_depth",
        "max_set_operations",
        "max_derived_tables",
        "max_complexity_score",
    },
)
POLICY_KEYS = POLICY_INTEGER_KEYS | {"mode"}
POLICY_MODES = frozenset({"enforce", "report"})


@dataclass(frozen=True)
class ComplexityPolicy:
    """Thresholds and mode for one SQL path."""

    max_ctes: int = 8
    max_joins: int = 8
    max_subquery_depth: int = 3
    max_case_expressions: int = 10
    max_boolean_operators: int = 20
    max_window_functions: int = 10
    max_cte_dependency_depth: int = 5
    max_nested_case_depth: int = 10
    max_set_operations: int = 12
    max_derived_tables: int = 4
    max_complexity_score: int = 60
    mode: str = "enforce"


def _validate_single_band_object(obj: Any, context: str, index: int) -> tuple[int, str]:
    """Validate one band dict from severity_bands JSON array.

    Returns ``(threshold, severity_str)`` or raises :class:`ConfigValidationError`.
    """
    if not isinstance(obj, dict):
        raise ConfigValidationError(
            config_key=context,
            invalid_value=obj,
            expected=f'each band must be an object with "threshold" and "severity" keys (band {index})',
        )
    if "threshold" not in obj:
        raise ConfigValidationError(
            config_key=context,
            invalid_value=obj,
            expected=f'band {index} is missing required key "threshold"',
        )
    if "severity" not in obj:
        raise ConfigValidationError(
            config_key=context,
            invalid_value=obj,
            expected=f'band {index} is missing required key "severity"',
        )
    raw_threshold = obj["threshold"]
    if not isinstance(raw_threshold, int):
        raise ConfigValidationError(
            config_key=context,
            invalid_value=raw_threshold,
            expected=f'band {index} "threshold" must be a non-negative integer',
        )
    if raw_threshold < 0:
        raise ConfigValidationError(
            config_key=context,
            invalid_value=raw_threshold,
            expected=f'band {index} "threshold" must be non-negative',
        )
    raw_severity = obj["severity"]
    if not isinstance(raw_severity, str):
        raise ConfigValidationError(
            config_key=context,
            invalid_value=raw_severity,
            expected=f'band {index} "severity" must be a string ("info", "warning", or "error")',
        )
    return raw_threshold, raw_severity


def parse_severity_bands(
    raw: str | None,
    *,
    context: str = "severity_bands",
) -> tuple[Any, ...]:
    """Parse a ``severity_bands`` INI value into a tuple of :class:`SeverityBand`.

    Accepts a JSON array of ``{"threshold": int, "severity": str}`` objects.
    Returns ``()`` when *raw* is ``None`` or empty.  Raises
    :class:`ConfigValidationError` on any structural or value error.

    Import :class:`~sqlfluff_complexity.core.config.severity.SeverityBand` and
    :class:`~sqlfluff_complexity.core.config.severity.SeverityLevel` at call time
    to avoid a circular import at module load.
    """
    from sqlfluff_complexity.core.config.severity import SeverityBand, SeverityLevel  # noqa: PLC0415

    if not raw or not str(raw).strip():
        return ()

    raw_str = str(raw).strip()
    try:
        data = json.loads(raw_str)
    except json.JSONDecodeError as exc:
        raise ConfigValidationError(
            config_key=context,
            invalid_value=raw_str,
            expected='a JSON array of {"threshold": int, "severity": str} objects',
        ) from exc

    if not isinstance(data, list):
        raise ConfigValidationError(
            config_key=context,
            invalid_value=raw_str,
            expected='a JSON array of {"threshold": int, "severity": str} objects',
        )

    bands: list[SeverityBand] = []
    for index, obj in enumerate(data):
        threshold, severity_str = _validate_single_band_object(obj, context, index)
        severity = SeverityLevel.from_str(severity_str, config_key=f"{context}[{index}].severity")
        bands.append(SeverityBand(threshold=threshold, severity=severity))

    bands.sort(key=lambda b: b.threshold)
    return tuple(bands)


def normalize_policy_path(path: str) -> str:
    """Normalize a path to POSIX separators for policy matching."""
    return path.replace("\\", "/")


def _parse_mode(value: str) -> str:
    if value not in POLICY_MODES:
        message = f"Path override mode must be one of {sorted(POLICY_MODES)}."
        raise ValueError(message)
    return value


def _parse_non_negative_integer(key: str, value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as exc:
        message = f"Path override {key!r} must be an integer."
        raise ValueError(message) from exc
    if parsed_value < 0:
        message = f"Path override {key!r} must be non-negative."
        raise ValueError(message)
    return parsed_value


def _parse_assignment(assignment: str) -> tuple[str, int | str]:
    key, separator, raw_value = assignment.partition("=")
    if separator != "=":
        message = f"Invalid path override assignment {assignment!r}; expected key=value."
        raise ValueError(message)

    key = key.strip()
    if key not in POLICY_KEYS:
        message = f"Unknown path override key {key!r}."
        raise ValueError(message)

    value = raw_value.strip()
    if key == "mode":
        return key, _parse_mode(value)
    return key, _parse_non_negative_integer(key, value)


def _parse_assignments(assignments: str) -> dict[str, int | str]:
    overrides: dict[str, int | str] = {}
    for raw_assignment in assignments.split(","):
        assignment = raw_assignment.strip()
        if assignment:
            key, value = _parse_assignment(assignment)
            overrides[key] = value
    return overrides


def _parse_overrides(raw_overrides: str) -> list[tuple[str, dict[str, int | str]]]:
    parsed = []
    for line in raw_overrides.splitlines():
        item = line.strip()
        if not item:
            continue
        pattern, separator, assignments = item.partition(":")
        if separator != ":":
            message = f"Invalid path override {item!r}; expected <glob>:key=value."
            raise ValueError(message)
        parsed.append((normalize_policy_path(pattern.strip()), _parse_assignments(assignments)))
    return parsed


def _pattern_specificity(pattern: str) -> int:
    return sum(1 for character in pattern if character not in "*?[]")


def resolve_policy(
    base_policy: ComplexityPolicy,
    raw_overrides: str | None,
    path: str | None,
) -> ComplexityPolicy:
    """Resolve a complexity policy for a path."""
    if not raw_overrides or not path:
        return base_policy

    normalized_path = normalize_policy_path(path)
    best_override: dict[str, int | str] | None = None
    best_specificity = -1
    for pattern, overrides in _parse_overrides(raw_overrides):
        if fnmatch.fnmatchcase(normalized_path, pattern):
            specificity = _pattern_specificity(pattern)
            if specificity >= best_specificity:
                best_specificity = specificity
                best_override = overrides

    if best_override is None:
        return base_policy
    return replace(base_policy, **best_override)
