"""Rule CPX_C108: nested CASE expression depth too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result_outer_select_only,
    resolve_context_policy,
)


class Rule_CPX_C108(BaseRule):  # noqa: N801
    """Query exceeds maximum nesting depth of ``case_expression`` segments."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_nested_case_depth",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    max_nested_case_depth: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C108",
        metric_name="expression_depth",
        config_key="max_nested_case_depth",
        policy_key="max_nested_case_depth",
        description_label="nested CASE depth",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_nested_case_depth=int(self.max_nested_case_depth)),
        )
        analysis = analyze_segment_tree(context.segment)
        return metric_lint_result_outer_select_only(
            context,
            analysis.metrics,
            policy,
            self._spec,
            precomputed_analysis=analysis,
        )
