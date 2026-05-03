"""Rule CPX_C109: too many set operations (UNION / INTERSECT / EXCEPT)."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import RootOnlyCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    file_segment_from_context,
    metric_lint_result,
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
    crawl_behaviour = RootOnlyCrawler()
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
        root = file_segment_from_context(context)
        analysis = analyze_segment_tree(root)
        return metric_lint_result(
            context,
            analysis.metrics,
            policy,
            self._spec,
            precomputed_analysis=analysis,
        )
