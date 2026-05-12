"""Rule CPX_C113: aggregation complexity too high (file-level parse root)."""

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


class Rule_CPX_C113(BaseRule):  # noqa: N801
    """Aggregate functions, GROUP BY keys, and HAVING/QUALIFY clauses exceed the budget."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_aggregation_complexity",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = RootOnlyCrawler()
    is_fix_compatible = False
    targets_templated = True
    max_aggregation_complexity: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C113",
        metric_name="aggregation_complexity",
        config_key="max_aggregation_complexity",
        policy_key="max_aggregation_complexity",
        description_label="aggregation complexity",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_aggregation_complexity=self.max_aggregation_complexity),
        )
        return eval_file_root_metric_threshold(context, policy, self._spec)
