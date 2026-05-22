"""Generated CPX SQLFluff configuration presets."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.config.rule_registry import (
    CPX_RULE_IDS,
    METRIC_RULE_DEFINITIONS,
    METRIC_RULES_BY_ID,
)
from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS

RULE_CODES = CPX_RULE_IDS
RULE_LIST = ",".join(RULE_CODES)
WEIGHT_JSON = json.dumps(DEFAULT_WEIGHTS, separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True)
class CpxPreset:
    """One generated CPX config profile."""

    max_ctes: int
    max_joins: int
    max_subquery_depth: int
    max_case_expressions: int
    max_boolean_operators: int
    max_window_functions: int
    max_cte_dependency_depth: int
    max_nested_case_depth: int
    max_set_operations: int
    max_derived_tables: int
    max_complexity_score: int
    mode: str = "enforce"


def _preset_from_policy(policy: ComplexityPolicy, *, mode: str = "enforce") -> CpxPreset:
    return CpxPreset(
        policy.max_ctes,
        policy.max_joins,
        policy.max_subquery_depth,
        policy.max_case_expressions,
        policy.max_boolean_operators,
        policy.max_window_functions,
        policy.max_cte_dependency_depth,
        policy.max_nested_case_depth,
        policy.max_set_operations,
        policy.max_derived_tables,
        policy.max_complexity_score,
        mode=mode,
    )


_RECOMMENDED = ComplexityPolicy()

PRESETS: dict[str, CpxPreset] = {
    "report_only": _preset_from_policy(_RECOMMENDED, mode="report"),
    "lenient": CpxPreset(12, 12, 4, 16, 32, 16, 7, 12, 18, 6, 90),
    "recommended": _preset_from_policy(_RECOMMENDED),
    "strict": CpxPreset(5, 5, 2, 6, 12, 6, 3, 6, 8, 2, 40),
}

PRESET_NAMES: tuple[str, ...] = tuple(sorted(PRESETS))


def preset_names() -> tuple[str, ...]:
    """Return known preset names in stable alphabetical order for CLI choices."""
    return PRESET_NAMES


def _rule_section(rule_id: str, key: str, value: int) -> str:
    lines = [
        f"[sqlfluff:rules:{rule_id}]",
        f"{key} = {value}",
    ]
    definition = METRIC_RULES_BY_ID.get(rule_id)
    if definition is None or definition.supports_contributors:
        lines.extend(["show_contributors = true", "max_contributors = 3"])
    return "\n".join(lines)


def _aggregate_section(preset: CpxPreset) -> str:
    return "\n".join(
        [
            "[sqlfluff:rules:CPX_C201]",
            f"max_complexity_score = {preset.max_complexity_score}",
            f"complexity_weights = {WEIGHT_JSON}",
            f"mode = {preset.mode}",
            "path_overrides =",
            "show_contributors = true",
            "max_contributors = 3",
        ],
    )


def _metric_rule_preset_sections(preset: CpxPreset) -> list[str]:
    """SQLFluff rule sections for C101-C110 derived from the registry."""
    sections: list[str] = []
    for definition in METRIC_RULE_DEFINITIONS:
        threshold = int(getattr(preset, definition.policy_key))
        sections.append(_rule_section(definition.rule_id, definition.config_key, threshold))
    return sections


def render_preset_config(name: str, *, dialect: str) -> str:
    """Render a preset as plain SQLFluff config text."""
    preset = PRESETS[name]
    sections = [
        "[sqlfluff]",
        f"dialect = {dialect}",
        f"rules = {RULE_LIST}",
        "",
        *_metric_rule_preset_sections(preset),
        _aggregate_section(preset),
    ]
    return "\n\n".join(sections)
