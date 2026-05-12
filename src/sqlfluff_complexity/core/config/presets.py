"""Generated CPX SQLFluff configuration presets."""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS

RULE_CODES = (
    "CPX_C101",
    "CPX_C102",
    "CPX_C103",
    "CPX_C104",
    "CPX_C105",
    "CPX_C106",
    "CPX_C107",
    "CPX_C108",
    "CPX_C109",
    "CPX_C110",
    "CPX_C111",
    "CPX_C112",
    "CPX_C113",
    "CPX_C201",
)

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
    max_source_relations: int
    max_select_targets: int
    max_aggregation_complexity: int
    max_complexity_score: int
    mode: str = "enforce"


PRESETS: dict[str, CpxPreset] = {
    "report_only": CpxPreset(8, 8, 3, 10, 20, 10, 5, 10, 12, 4, 8, 40, 20, 60, mode="report"),
    "lenient": CpxPreset(12, 12, 4, 16, 32, 16, 7, 12, 18, 6, 12, 80, 32, 90),
    "recommended": CpxPreset(8, 8, 3, 10, 20, 10, 5, 10, 12, 4, 8, 40, 20, 60),
    "strict": CpxPreset(5, 5, 2, 6, 12, 6, 3, 6, 8, 2, 5, 25, 12, 40),
}

PRESET_NAMES: tuple[str, ...] = tuple(sorted(PRESETS))


def preset_names() -> tuple[str, ...]:
    """Return known preset names in stable alphabetical order for CLI choices."""
    return PRESET_NAMES


def _rule_section(rule_id: str, key: str, value: int) -> str:
    return "\n".join(
        [
            f"[sqlfluff:rules:{rule_id}]",
            f"{key} = {value}",
            "show_contributors = true",
            "max_contributors = 3",
        ],
    )


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


def render_preset_config(name: str, *, dialect: str) -> str:
    """Render a preset as plain SQLFluff config text."""
    preset = PRESETS[name]
    sections = [
        "[sqlfluff]",
        f"dialect = {dialect}",
        f"rules = {RULE_LIST}",
        "",
        _rule_section("CPX_C101", "max_ctes", preset.max_ctes),
        _rule_section("CPX_C102", "max_joins", preset.max_joins),
        _rule_section("CPX_C103", "max_subquery_depth", preset.max_subquery_depth),
        _rule_section("CPX_C104", "max_case_expressions", preset.max_case_expressions),
        _rule_section("CPX_C105", "max_boolean_operators", preset.max_boolean_operators),
        _rule_section("CPX_C106", "max_window_functions", preset.max_window_functions),
        _rule_section("CPX_C107", "max_cte_dependency_depth", preset.max_cte_dependency_depth),
        _rule_section("CPX_C108", "max_nested_case_depth", preset.max_nested_case_depth),
        _rule_section("CPX_C109", "max_set_operations", preset.max_set_operations),
        _rule_section("CPX_C110", "max_derived_tables", preset.max_derived_tables),
        _rule_section("CPX_C111", "max_source_relations", preset.max_source_relations),
        _rule_section("CPX_C112", "max_select_targets", preset.max_select_targets),
        _rule_section("CPX_C113", "max_aggregation_complexity", preset.max_aggregation_complexity),
        _aggregate_section(preset),
    ]
    return "\n\n".join(sections)
