"""Rule CPX_C108: nested CASE expression depth too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import RootOnlyCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    eval_file_root_metric_threshold,
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
    crawl_behaviour = RootOnlyCrawler()
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
        return eval_file_root_metric_threshold(context, policy, self._spec)
