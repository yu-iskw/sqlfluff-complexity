"""Rule CPX_C101: too many CTEs."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.segment_tree import analyze_segment_tree
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result,
    resolve_context_policy,
)


class Rule_CPX_C101(BaseRule):  # noqa: N801
    """Query contains too many common table expressions."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = ["max_ctes", "show_contributors", "max_contributors"]
    crawl_behaviour = SegmentSeekerCrawler({"with_compound_statement"})
    is_fix_compatible = False
    max_ctes: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C101",
        metric_name="ctes",
        config_key="max_ctes",
        policy_key="max_ctes",
        description_label="CTE count",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(context, ComplexityPolicy(max_ctes=int(self.max_ctes)))
        analysis = analyze_segment_tree(context.segment)
        return metric_lint_result(
            context,
            analysis.metrics,
            policy,
            self._spec,
            precomputed_analysis=analysis,
        )
