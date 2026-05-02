"""Rule CPX_C107: CTE dependency chain too deep."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.remediation import remediation_for_rule
from sqlfluff_complexity.core.segment_tree import collect_metrics, is_nested_select_statement
from sqlfluff_complexity.core.structural_metrics import direct_child_common_table_expressions
from sqlfluff_complexity.rules.base import resolve_context_policy

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment


def _anchor_cte_dependency_violation(with_root: BaseSegment) -> BaseSegment:
    """Lint anchor: last top-level CTE under the WITH (heuristic for chained dependency issues)."""
    ctes = direct_child_common_table_expressions(with_root)
    return ctes[-1] if ctes else with_root


class Rule_CPX_C107(BaseRule):  # noqa: N801
    """CTE dependency depth within a WITH clause exceeds the configured limit."""

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = ["max_cte_dependency_depth"]
    crawl_behaviour = SegmentSeekerCrawler({"with_compound_statement"})
    is_fix_compatible = False
    max_cte_dependency_depth: int

    def _eval(self, context: RuleContext) -> LintResult | None:
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_cte_dependency_depth=int(self.max_cte_dependency_depth)),
        )
        if is_nested_select_statement(context.segment) or policy.mode == "report":
            return None

        metrics = collect_metrics(context.segment)
        actual = metrics.cte_dependency_depth
        limit = policy.max_cte_dependency_depth
        if actual <= limit:
            return None

        rem = remediation_for_rule("CPX_C107")
        description = (
            f"CPX_C107: CTE dependency depth is {actual}, exceeding max_cte_dependency_depth={limit}. "
            f"{rem}"
        )
        anchor = _anchor_cte_dependency_violation(context.segment)
        return LintResult(anchor=anchor, description=description)
