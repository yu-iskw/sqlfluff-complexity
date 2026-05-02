"""Rule CPX_C103: nested subquery depth too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.segment_tree import collect_metrics
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
    max_subquery_depth: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C103",
        metric_name="subquery_depth",
        config_key="max_subquery_depth",
        policy_key="max_subquery_depth",
        description_label="nested subquery depth",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_subquery_depth=int(self.max_subquery_depth)),
        )
        return metric_lint_result_outer_select_only(
            context,
            collect_metrics(context.segment),
            policy,
            self._spec,
        )
