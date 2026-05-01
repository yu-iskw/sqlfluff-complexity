"""Rule CPX_C201: aggregate complexity score too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.analysis import format_contributor_examples
from sqlfluff_complexity.core.explainability import (
    explain_score_contributors,
    ranked_weighted_contributions,
    refactoring_hint_for_contributors,
)
from sqlfluff_complexity.core.policy import ComplexityPolicy
from sqlfluff_complexity.core.scoring import parse_weights
from sqlfluff_complexity.core.segment_tree import analyze_segment_tree, is_nested_select_statement
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
        if is_nested_select_statement(context.segment):
            return None
        analysis = analyze_segment_tree(context.segment)
        metrics = analysis.metrics
        weights = parse_weights(self.complexity_weights)
        score = metrics.score(weights)
        policy = resolve_context_policy(
            context,
            ComplexityPolicy(max_complexity_score=int(self.max_complexity_score), mode=self.mode),
        )
        limit = policy.max_complexity_score

        if policy.mode == "report" or score <= limit:
            return None

        top_n = 3
        contributors = explain_score_contributors(metrics, weights, max_items=top_n)
        top_keys = [
            name
            for name, _ in ranked_weighted_contributions(metrics, weights)[:top_n]
        ]
        hint = refactoring_hint_for_contributors(top_keys)
        examples = format_contributor_examples(
            analysis.contributors,
            weights,
            max_items=top_n,
        )
        examples_clause = f" {examples}" if examples else ""

        return LintResult(
            anchor=context.segment,
            description=(
                f"CPX_C201: aggregate complexity score {score} exceeds "
                f"max_complexity_score={limit}. Metrics: {metrics.format_breakdown()}. "
                f"Top contributors: {contributors}.{examples_clause} {hint}"
            ),
        )
