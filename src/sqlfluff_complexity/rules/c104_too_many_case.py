"""Rule CPX_C104: too many CASE expressions."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.config.rule_registry import metric_rule_spec
from sqlfluff_complexity.core.scan.segment_tree import analyze_segment_tree, is_nested_select_statement
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result_outer_select_only,
    resolve_context_policy,
)


class Rule_CPX_C104(BaseRule):  # noqa: N801
    """Query contains too many CASE expressions."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_case_expressions",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    targets_templated = True
    max_case_expressions: int

    _spec: ClassVar[MetricRuleSpec] = metric_rule_spec("CPX_C104")

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        if is_nested_select_statement(context.segment):
            return None
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_case_expressions=int(self.max_case_expressions)),
        )
        analysis = analyze_segment_tree(context.segment)
        return metric_lint_result_outer_select_only(
            context,
            analysis.metrics,
            policy,
            self._spec,
            precomputed_analysis=analysis,
        )
