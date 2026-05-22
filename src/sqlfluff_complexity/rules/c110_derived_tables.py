"""Rule CPX_C110: too many derived tables.

Uses ``RootOnlyCrawler`` like CPX_C108/CPX_C109 (one evaluation at the parse ``file`` root;
metrics still scan the full tree). If a templater omits a ``file`` ancestor, reconsider
``SegmentSeekerCrawler({"file"})``.
"""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import RootOnlyCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.config.rule_registry import metric_rule_spec
from sqlfluff_complexity.rules.base import (
    MetricRuleSpec,
    eval_file_root_metric_threshold,
    resolve_context_policy,
)


class Rule_CPX_C110(BaseRule):  # noqa: N801
    """Query contains too many derived tables."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_derived_tables",
        "show_contributors",
        "max_contributors",
    ]
    crawl_behaviour = RootOnlyCrawler()
    is_fix_compatible = False
    targets_templated = True
    max_derived_tables: int

    _spec: ClassVar[MetricRuleSpec] = metric_rule_spec("CPX_C110")

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_derived_tables=int(self.max_derived_tables)),
        )
        return eval_file_root_metric_threshold(context, policy, self._spec)
