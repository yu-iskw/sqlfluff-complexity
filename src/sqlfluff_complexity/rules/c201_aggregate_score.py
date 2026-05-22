"""Rule CPX_C201: aggregate complexity score too high."""

from __future__ import annotations

from typing import ClassVar

from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

from sqlfluff_complexity.core.config.cpx_config import contributor_display_settings
from sqlfluff_complexity.core.config.policy import ComplexityPolicy, resolve_context_policy
from sqlfluff_complexity.core.config.scoring import parse_weights
from sqlfluff_complexity.core.messages.c201_messages import C201ViolationParams, build_c201_violation_message
from sqlfluff_complexity.core.scan.segment_tree import (
    analyze_segment_tree,
    is_nested_select_statement,
)


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
        "max_contributors",
        "show_contributors",
    ]
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    is_fix_compatible = False
    targets_templated = True
    max_complexity_score: int
    complexity_weights: str
    mode: str
    path_overrides: str
    max_contributors: int
    show_contributors: str

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

        show_c201, cap = contributor_display_settings(context.config, "CPX_C201")
        description = build_c201_violation_message(
            C201ViolationParams(
                score=score,
                limit=limit,
                metrics=metrics,
                weights=weights,
                contributors=analysis.contributors,
                show_contributors=show_c201,
                max_contributors=cap,
            ),
        )

        return LintResult(
            anchor=context.segment,
            description=description,
        )
