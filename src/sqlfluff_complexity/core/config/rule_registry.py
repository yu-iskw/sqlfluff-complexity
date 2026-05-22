"""Canonical CPX rule metadata (threshold rules, report checks, SARIF, presets).

Structural fields (threshold keys, metric names, eval scope, SARIF ids) live here.
Human-readable SQLFluff plugin definitions in ``get_configs_info()`` remain in
``sqlfluff_complexity.__init__`` by design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EvalScope = Literal["file", "outer_select", "with_clause"]

CPX_AGGREGATE_RULE_ID = "CPX_C201"
CPX_PARSE_ERROR_RULE_ID = "CPX_PARSE_ERROR"


@dataclass(frozen=True)
class MetricRuleSpec:
    """Configuration for one threshold-based metric rule (lint and report)."""

    rule_id: str
    metric_name: str
    config_key: str
    policy_key: str
    description_label: str


@dataclass(frozen=True)
class MetricRuleDefinition:
    """One threshold-based CPX metric rule (C101-C110)."""

    rule_id: str
    metric_name: str
    policy_key: str
    config_key: str
    description_label: str
    message_label: str
    report_label: str
    eval_scope: EvalScope
    supports_contributors: bool = True


METRIC_RULE_DEFINITIONS: tuple[MetricRuleDefinition, ...] = (
    MetricRuleDefinition(
        "CPX_C101",
        "ctes",
        "max_ctes",
        "max_ctes",
        "CTE count",
        "cte count",
        "CTE count",
        "with_clause",
    ),
    MetricRuleDefinition(
        "CPX_C102",
        "joins",
        "max_joins",
        "max_joins",
        "join count",
        "join count",
        "Join count",
        "outer_select",
    ),
    MetricRuleDefinition(
        "CPX_C103",
        "subquery_depth",
        "max_subquery_depth",
        "max_subquery_depth",
        "nested subquery depth",
        "nested subquery depth",
        "Nested subquery depth",
        "outer_select",
    ),
    MetricRuleDefinition(
        "CPX_C104",
        "case_expressions",
        "max_case_expressions",
        "max_case_expressions",
        "CASE expression count",
        "CASE expression count",
        "CASE expression count",
        "outer_select",
    ),
    MetricRuleDefinition(
        "CPX_C105",
        "boolean_operators",
        "max_boolean_operators",
        "max_boolean_operators",
        "boolean operator count",
        "boolean operator count",
        "Boolean operator count",
        "outer_select",
    ),
    MetricRuleDefinition(
        "CPX_C106",
        "window_functions",
        "max_window_functions",
        "max_window_functions",
        "window function count",
        "window function count",
        "Window function count",
        "outer_select",
    ),
    MetricRuleDefinition(
        "CPX_C107",
        "cte_dependency_depth",
        "max_cte_dependency_depth",
        "max_cte_dependency_depth",
        "CTE dependency depth",
        "CTE dependency depth",
        "CTE dependency depth",
        "with_clause",
        supports_contributors=False,
    ),
    MetricRuleDefinition(
        "CPX_C108",
        "expression_depth",
        "max_nested_case_depth",
        "max_nested_case_depth",
        "nested CASE depth",
        "nested CASE depth",
        "Nested CASE depth",
        "file",
    ),
    MetricRuleDefinition(
        "CPX_C109",
        "set_operation_count",
        "max_set_operations",
        "max_set_operations",
        "set operation count",
        "set operation count",
        "Set operation count",
        "file",
    ),
    MetricRuleDefinition(
        "CPX_C110",
        "derived_tables",
        "max_derived_tables",
        "max_derived_tables",
        "derived table count",
        "derived table count",
        "Derived table count",
        "file",
    ),
)

METRIC_RULES_BY_ID: dict[str, MetricRuleDefinition] = {d.rule_id: d for d in METRIC_RULE_DEFINITIONS}

CPX_METRIC_RULE_IDS: tuple[str, ...] = tuple(d.rule_id for d in METRIC_RULE_DEFINITIONS)

CPX_RULE_IDS: tuple[str, ...] = (*CPX_METRIC_RULE_IDS, CPX_AGGREGATE_RULE_ID)

SARIF_RULE_IDS: tuple[str, ...] = (*CPX_RULE_IDS, CPX_PARSE_ERROR_RULE_ID)


def metric_rule_spec(rule_id: str) -> MetricRuleSpec:
    """Build a :class:`MetricRuleSpec` from the registry."""
    definition = METRIC_RULES_BY_ID[rule_id]
    return MetricRuleSpec(
        rule_id=definition.rule_id,
        metric_name=definition.metric_name,
        config_key=definition.config_key,
        policy_key=definition.policy_key,
        description_label=definition.description_label,
    )


@dataclass(frozen=True)
class ReportLimit:
    """One report threshold check (file-level rollup)."""

    rule_id: str
    metric_name: str
    policy_key: str
    label: str
    config_key: str
    message_label: str


def report_limit(defn: MetricRuleDefinition) -> ReportLimit:
    """Build report threshold metadata from a registry row."""
    return ReportLimit(
        rule_id=defn.rule_id,
        metric_name=defn.metric_name,
        policy_key=defn.policy_key,
        label=defn.report_label,
        config_key=defn.config_key,
        message_label=defn.message_label,
    )


REPORT_LIMITS: tuple[ReportLimit, ...] = tuple(report_limit(d) for d in METRIC_RULE_DEFINITIONS)
