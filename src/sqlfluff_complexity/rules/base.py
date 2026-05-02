"""Shared helpers for SQLFluff complexity rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from sqlfluff.core.rules import LintResult

from sqlfluff_complexity.core.cpx_config import contributor_display_settings
from sqlfluff_complexity.core.policy import POLICY_MODES, ComplexityPolicy, resolve_policy
from sqlfluff_complexity.core.segment_tree import analyze_segment_tree, is_nested_select_statement
from sqlfluff_complexity.core.violation_messages import metric_threshold_violation_message

if TYPE_CHECKING:
    from sqlfluff.core.rules import RuleContext

    from sqlfluff_complexity.core.metrics import ComplexityMetrics


@dataclass(frozen=True)
class MetricRuleSpec:
    """Configuration for one threshold-based metric rule."""

    rule_id: str
    metric_name: str
    config_key: str
    policy_key: str
    description_label: str


def metric_lint_result_outer_select_only(
    context: RuleContext,
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    spec: MetricRuleSpec,
) -> LintResult | None:
    """Like ``metric_lint_result`` but skip nested ``select_statement`` crawl hits."""
    if is_nested_select_statement(context.segment):
        return None
    return metric_lint_result(context, metrics, policy, spec)


def resolve_context_policy(context: RuleContext, base_policy: ComplexityPolicy) -> ComplexityPolicy:
    """Resolve path-specific policy for a SQLFluff rule context."""
    mode = context.config.get("mode", section=("rules", "CPX_C201"), default=base_policy.mode)
    if mode not in POLICY_MODES:
        message = f"Complexity policy mode must be one of {sorted(POLICY_MODES)}."
        raise ValueError(message)
    base_policy = replace(base_policy, mode=mode)
    raw_overrides = context.config.get("path_overrides", section=("rules", "CPX_C201"), default="")
    path = str(context.path) if context.path is not None else None
    return resolve_policy(base_policy, raw_overrides, path)


def metric_lint_result(
    context: RuleContext,
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    spec: MetricRuleSpec,
) -> LintResult | None:
    """Build a lint result for one metric threshold, if violated."""
    if policy.mode == "report":
        return None

    actual = int(getattr(metrics, spec.metric_name))
    limit = int(getattr(policy, spec.policy_key))
    if actual <= limit:
        return None

    analysis = analyze_segment_tree(context.segment)
    show_contributors, max_contributors = contributor_display_settings(
        context.config,
        spec.rule_id,
    )

    description = metric_threshold_violation_message(
        rule_id=spec.rule_id,
        description_label=spec.description_label,
        actual=actual,
        config_key=spec.config_key,
        limit=limit,
        metric_name=spec.metric_name,
        contributors=analysis.contributors,
        max_contributors=max_contributors,
        show_contributors=show_contributors,
    )

    return LintResult(
        anchor=context.segment,
        description=description,
    )
