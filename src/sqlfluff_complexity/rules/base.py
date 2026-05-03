"""Shared helpers for SQLFluff complexity rules."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from sqlfluff.core.rules import LintResult

from sqlfluff_complexity.core.config.cpx_config import contributor_display_settings
from sqlfluff_complexity.core.config.policy import (
    POLICY_MODES,
    ComplexityPolicy,
    resolve_policy,
)
from sqlfluff_complexity.core.messages.violation_messages import (
    MetricThresholdViolationParams,
    metric_threshold_violation_message,
)
from sqlfluff_complexity.core.scan.segment_tree import (
    analyze_segment_tree,
    is_nested_select_statement,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlfluff.core.parser.segments.base import BaseSegment
    from sqlfluff.core.rules.context import RuleContext

    from sqlfluff_complexity.core.analysis import ComplexityAnalysis
    from sqlfluff_complexity.core.model.metrics import ComplexityMetrics


def file_segment_from_context(context: RuleContext) -> BaseSegment:
    """Return the ``file`` segment for the current rule context (lint uses parent_stack)."""
    if getattr(context.segment, "type", "") == "file":
        return context.segment
    for seg in context.parent_stack:
        if getattr(seg, "type", "") == "file":
            return seg
    return context.segment


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
    *,
    precomputed_analysis: ComplexityAnalysis | None = None,
) -> LintResult | None:
    """Like ``metric_lint_result`` but skip nested ``select_statement`` crawl hits."""
    return _metric_lint_result_skip_when(
        context,
        metrics,
        policy,
        spec,
        is_nested_select_statement,
        precomputed_analysis=precomputed_analysis,
    )


def _metric_lint_result_skip_when(  # noqa: PLR0913
    context: RuleContext,
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    spec: MetricRuleSpec,
    skip_when: Callable[[BaseSegment], bool],
    *,
    precomputed_analysis: ComplexityAnalysis | None = None,
) -> LintResult | None:
    if skip_when(context.segment):
        return None
    return metric_lint_result(
        context,
        metrics,
        policy,
        spec,
        precomputed_analysis=precomputed_analysis,
    )


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
    *,
    precomputed_analysis: ComplexityAnalysis | None = None,
) -> LintResult | None:
    """Build a lint result for one metric threshold, if violated.

    When ``precomputed_analysis`` is provided, use it for contributor lines instead
    of re-running :func:`sqlfluff_complexity.core.scan.segment_tree.analyze_segment_tree`
    on the same segment (avoids a second full tree walk on violations).
    """
    if policy.mode == "report":
        return None

    actual = int(getattr(metrics, spec.metric_name))
    limit = int(getattr(policy, spec.policy_key))
    if actual <= limit:
        return None

    analysis = precomputed_analysis or analyze_segment_tree(context.segment)
    show_contributors, max_contributors = contributor_display_settings(
        context.config,
        spec.rule_id,
    )

    description = metric_threshold_violation_message(
        MetricThresholdViolationParams(
            rule_id=spec.rule_id,
            description_label=spec.description_label,
            actual=actual,
            config_key=spec.config_key,
            limit=limit,
            metric_name=spec.metric_name,
            contributors=analysis.contributors,
            max_contributors=max_contributors,
            show_contributors=show_contributors,
        ),
    )

    return LintResult(
        anchor=context.segment,
        description=description,
    )
