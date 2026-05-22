"""Rule CPX_C103: nested subquery depth too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.config.rule_registry import metric_rule_spec
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    metric_lint_result_outer_select_only,
    resolve_context_policy,
)


class Rule_CPX_C103(BaseRule):  # noqa: N801
    """Query contains deeply nested subqueries."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_subquery_depth",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    targets_templated = True
    max_subquery_depth: int

    _spec: ClassVar[MetricRuleSpec] = metric_rule_spec("CPX_C103")

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_subquery_depth=int(self.max_subquery_depth)),
        )
        return metric_lint_result_outer_select_only(context, policy, self._spec)
