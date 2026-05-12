"""Rule CPX_C111: too many distinct source relations (file-level parse root)."""

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


class Rule_CPX_C111(BaseRule):  # noqa: N801
    """Query references too many distinct source relations."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_source_relations",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = RootOnlyCrawler()
    is_fix_compatible = False
    targets_templated = True
    max_source_relations: int

    _spec: ClassVar[MetricRuleSpec] = MetricRuleSpec(
        rule_id="CPX_C111",
        metric_name="source_relations",
        config_key="max_source_relations",
        policy_key="max_source_relations",
        description_label="source relation count",
    )

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_source_relations=self.max_source_relations),
        )
        return eval_file_root_metric_threshold(context, policy, self._spec)
