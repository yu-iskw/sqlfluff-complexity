"""Rule CPX_C201: aggregate complexity score too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.scoring import parse_weights
from sqlfluff_complexity.core.segment_tree import collect_metrics
from sqlfluff_complexity.rules.base import resolve_context_policy


class Rule_CPX_C201(BaseRule):  # noqa: N801
    """Query aggregate complexity score is too high.

    **Anti-pattern**

    A statement spreads complexity across joins, expressions, predicates, and
    nested queries, making it harder to review even if no single metric is
    extreme.

    **Best practice**

    Break complex logic into named intermediate models or simpler statements.
    """

    groups: tuple[str, ...] = ("all", "complexity")
    config_keywords: ClassVar[list[str]] = [
        "max_complexity_score",
        "complexity_weights",
        "mode",
        "path_overrides",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    max_complexity_score: int
    complexity_weights: str
    mode: str
    path_overrides: str

    def _eval(self, context: RuleContext) -> LintResult | None:
        """Evaluate the rule."""
        metrics = collect_metrics(context.segment)
        weights = parse_weights(self.complexity_weights)
        score = metrics.score(weights)
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_complexity_score=int(self.max_complexity_score), mode=self.mode),
        )
        limit = policy.max_complexity_score

        if policy.mode == "report" or score <= limit:
            return None

        return LintResult(
            anchor=context.segment,
            description=(
                f"CPX_C201: aggregate complexity score {score} exceeds "
                f"max_complexity_score={limit}. Metrics: {metrics.format_breakdown()}."
            ),
        )
