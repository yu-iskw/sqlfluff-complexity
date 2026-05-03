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


def _file_segment_via_parent_pointers(segment: BaseSegment) -> BaseSegment | None:
    """Return nearest ``file`` ancestor using ``get_parent()``, or ``None``."""
    current: BaseSegment | None = segment
    for _ in range(512):
        if current is None:
            break
        parent_info = current.get_parent()
        if parent_info is None:
            break
        parent = parent_info[0]
        if getattr(parent, "type", "") == "file":
            return parent
        current = parent
    return None


def file_segment_from_context(context: RuleContext) -> BaseSegment:  # noqa: PLR0911
    """Return the ``file`` segment for the current rule context.

    Resolution order:

    1. If ``context.segment`` is already ``file``, return it.
    2. Else scan ``context.parent_stack`` for a ``file`` ancestor (SQLFluff crawlers).
    3. Else walk ``get_parent()`` from ``context.segment`` (may be unset outside lint).
    4. Else return ``context.segment`` (caller should treat as best-effort subtree root).
    """
    seg = context.segment
    if getattr(seg, "type", "") == "file":
        return seg
    for anc in context.parent_stack:
        if getattr(anc, "type", "") == "file":
            return anc
    via_parents = _file_segment_via_parent_pointers(seg)
    if via_parents is not None:
        return via_parents
    return seg


@dataclass(frozen=True)
class MetricRuleSpec:
    """Configuration for one threshold-based metric rule."""

    rule_id: str
    metric_name: str
    config_key: str
    policy_key: str
    description_label: str


def eval_file_root_metric_threshold(
    context: RuleContext,
    policy: ComplexityPolicy,
    spec: MetricRuleSpec,
) -> LintResult | None:
    """Lint one metric threshold using file-level parse metrics (report parity).

    Delegates to :func:`metric_lint_result` with ``anchor_segment`` set to the resolved
    ``file`` root; see that function if ``ValueError`` is raised from inconsistent inputs.
    """
    root = file_segment_from_context(context)
    analysis = analyze_segment_tree(root)
    return metric_lint_result(
        context,
        analysis.metrics,
        policy,
        spec,
        precomputed_analysis=analysis,
        anchor_segment=root,
    )


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


def metric_lint_result(  # noqa: PLR0913
    context: RuleContext,
    metrics: ComplexityMetrics,
    policy: ComplexityPolicy,
    spec: MetricRuleSpec,
    *,
    precomputed_analysis: ComplexityAnalysis | None = None,
    anchor_segment: BaseSegment | None = None,
) -> LintResult | None:
    """Build a lint result for one metric threshold, if violated.

    When ``precomputed_analysis`` is provided, use it for contributor lines instead
    of re-running :func:`sqlfluff_complexity.core.scan.segment_tree.analyze_segment_tree`
    on the same segment (avoids a second full tree walk on violations).

    When ``anchor_segment`` is set, use it for the ``LintResult`` anchor (e.g. ``file``
    root when metrics were computed from ``analyze_segment_tree(file)``). Callers
    must pass ``metrics`` and ``precomputed_analysis`` from that same analysis root;
    prefer :func:`eval_file_root_metric_threshold` for file-level rules so the trio
    stays aligned. If ``anchor_segment`` is set with ``precomputed_analysis`` but
    ``metrics`` disagrees on ``spec.metric_name``, raises ``ValueError``.
    """
    if policy.mode == "report":
        return None

    actual = int(getattr(metrics, spec.metric_name))
    limit = int(getattr(policy, spec.policy_key))
    if actual <= limit:
        return None

    analysis = precomputed_analysis or analyze_segment_tree(context.segment)
    if anchor_segment is not None and precomputed_analysis is not None:
        precomputed_actual = int(getattr(precomputed_analysis.metrics, spec.metric_name))
        if precomputed_actual != actual:
            message = (
                "anchor_segment and precomputed_analysis disagree on metric value; "
                "pass metrics and precomputed_analysis from the same analyze_segment_tree root."
            )
            raise ValueError(message)

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

    anchor = anchor_segment if anchor_segment is not None else context.segment
    return LintResult(
        anchor=anchor,
        description=description,
    )
