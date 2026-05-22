"""Shared CPX_C201 aggregate-score violation messages for lint and report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlfluff_complexity.core.analysis import (
    explain_score_contributors,
    format_contributor_examples,
    ranked_weighted_contributions,
    refactoring_hint_for_contributors,
    weighted_contributor_samples,
)
from sqlfluff_complexity.core.messages.remediation import remediation_for_rule

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlfluff_complexity.core.analysis import MetricContributor
    from sqlfluff_complexity.core.model.metrics import ComplexityMetrics


@dataclass(frozen=True)
class C201ViolationParams:
    """Inputs for :func:`build_c201_violation_message`."""

    score: int
    limit: int
    metrics: ComplexityMetrics
    weights: Mapping[str, int]
    contributors: tuple[MetricContributor, ...]
    show_contributors: bool
    max_contributors: int


def build_c201_violation_message(params: C201ViolationParams) -> str:
    """Build the CPX_C201 violation description (lint ``LintResult`` or report finding)."""
    remediation = remediation_for_rule("CPX_C201")
    if not params.show_contributors or params.max_contributors < 1:
        return (
            f"CPX_C201: aggregate complexity score {params.score} exceeds "
            f"max_complexity_score={params.limit}. {remediation} "
            f"Metrics: {params.metrics.format_breakdown()}."
        )

    top_n = params.max_contributors
    contributors_line = explain_score_contributors(params.metrics, params.weights, max_items=top_n)
    top_keys = [name for name, _ in ranked_weighted_contributions(params.metrics, params.weights)[:top_n]]
    hint = refactoring_hint_for_contributors(top_keys)
    examples = format_contributor_examples(
        params.contributors,
        params.weights,
        max_items=top_n,
    )
    examples_clause = f" {examples}" if examples else ""
    tail = f"Top contributors: {contributors_line}.{examples_clause} {hint}".strip()
    return (
        f"CPX_C201: aggregate complexity score {params.score} exceeds "
        f"max_complexity_score={params.limit}. {remediation} "
        f"Metrics: {params.metrics.format_breakdown()}. {tail}"
    )


def pick_c201_report_contributors(
    contributors: tuple[MetricContributor, ...],
    weights: Mapping[str, int],
    *,
    max_items: int,
) -> tuple[MetricContributor, ...]:
    """Ranked contributor samples for report findings when C201 contributors are shown."""
    return weighted_contributor_samples(contributors, weights, max_items=max_items)
