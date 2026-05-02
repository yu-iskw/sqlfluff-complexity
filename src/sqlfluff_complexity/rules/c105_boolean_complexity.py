"""Rule CPX_C105: boolean operator complexity too high."""

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
    max_boolean_operators: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C105",
        metric_name="boolean_operators",
        config_key="max_boolean_operators",
        policy_key="max_boolean_operators",
        description_label="boolean operator count",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_boolean_operators=int(self.max_boolean_operators)),
        )
        return metric_lint_result_outer_select_only(
            context,
            collect_metrics(context.segment),
            policy,
            self._spec,
        )
