"""Rule CPX_C107: CTE dependency chain too deep.

Dependency edges use bare table names among sibling CTEs. Schema-qualified names are not matched
to CTEs. Unqualified names may still be base tables at execution time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.config.policy import ComplexityPolicy
from sqlfluff_complexity.core.messages.remediation import remediation_for_rule
from sqlfluff_complexity.core.model.structural_metrics import (
    cte_dependency_depth_for_with_clause,
    direct_child_common_table_expressions,
)
from sqlfluff_complexity.rules.base import resolve_context_policy

if TYPE_CHECKING:
    from sqlfluff.core.parser.segments.base import BaseSegment


def _anchor_cte_dependency_violation(with_root: BaseSegment) -> BaseSegment:
    """Lint anchor: last top-level CTE under the WITH (heuristic for chained dependency issues)."""
    ctes = direct_child_common_table_expressions(with_root)
    return ctes[-1] if ctes else with_root


class Rule_CPX_C107(BaseRule):  # noqa: N801
    """CTE dependency depth within a WITH clause exceeds the configured limit.

    Depth is derived from sibling CTE reference edges on the parse tree (bare identifiers only;
    qualified references are excluded). See ``structural_metrics`` module docstrings for limits.
    """

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
        if policy.mode == "report":
            return None

        actual = cte_dependency_depth_for_with_clause(context.segment)
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
