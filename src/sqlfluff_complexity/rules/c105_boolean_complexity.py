"""Rule CPX_C105: boolean operator complexity too high."""

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


class Rule_CPX_C105(BaseRule):  # noqa: N801
    """Query contains too many boolean operators."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_boolean_operators",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    targets_templated = True
    max_boolean_operators: int

    _spec: ClassVar[MetricRuleSpec] = metric_rule_spec("CPX_C105")

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        if is_nested_select_statement(context.segment):
            return None
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_boolean_operators=int(self.max_boolean_operators)),
        )
        analysis = analyze_segment_tree(context.segment)
        return metric_lint_result_outer_select_only(
            context,
            analysis.metrics,
            policy,
            self._spec,
            precomputed_analysis=analysis,
        )
