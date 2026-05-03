"""Rule CPX_C109: too many set operations (UNION / INTERSECT / EXCEPT)."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result_outer_set_expression_only,
    resolve_context_policy,
)


class Rule_CPX_C109(BaseRule):  # noqa: N801
    """Query contains more ``set_operator`` segments than allowed."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_set_operations",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"set_expression"})
    is_fix_compatible = False
    max_set_operations: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C109",
        metric_name="set_operation_count",
        config_key="max_set_operations",
        policy_key="max_set_operations",
        description_label="set operation count",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_set_operations=int(self.max_set_operations)),
        )
        analysis = analyze_segment_tree(context.segment)
        return metric_lint_result_outer_set_expression_only(
            context,
            analysis.metrics,
            policy,
            self._spec,
            precomputed_analysis=analysis,
        )
