"""Rule CPX_C104: too many CASE expressions."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result,
    resolve_context_policy,
)


class Rule_CPX_C104(BaseRule):  # noqa: N801
    """Query contains too many CASE expressions."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = ["max_case_expressions"]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    max_case_expressions: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C104",
        metric_name="case_expressions",
        config_key="max_case_expressions",
        policy_key="max_case_expressions",
        description_label="CASE expression count",
        guidance="Consider extracting business rules into upstream models or mapping tables.",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_case_expressions=int(self.max_case_expressions)),
        )
        return metric_lint_result(context, collect_metrics(context.segment), policy, self._spec)
