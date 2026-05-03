"""Shared violation message text for SQLFluff lint and reports."""

from __future__ import annotations

from dataclasses import dataclass

from sqlfluff_complexity.core.analysis import (
    MetricContributor,
    format_contributor_summary,
    top_contributors,
)
from sqlfluff_complexity.core.messages.remediation import remediation_for_rule


@dataclass(frozen=True)
class MetricThresholdViolationParams:
    """Inputs for metric-threshold violation message builders.

    Used by :func:`metric_threshold_violation_message` and
    :func:`metric_threshold_violation_message_and_picked`.
    """

    rule_id: str
    description_label: str
    actual: int
    config_key: str
    limit: int
    metric_name: str
    contributors: tuple[MetricContributor, ...]
    max_contributors: int
    show_contributors: bool


def metric_threshold_violation_message_and_picked(
    params: MetricThresholdViolationParams,
) -> tuple[str, tuple[MetricContributor, ...], str]:
    """Build lint/report message, ranked contributors, and remediation (single passes).

    ``remediation_for_rule`` runs once; ``top_contributors`` runs at most once when
    contributors are shown.
    """
    remediation = remediation_for_rule(params.rule_id)
    body = (
        f"{params.rule_id}: {params.description_label} {params.actual} exceeds "
        f"{params.config_key}={params.limit}. {remediation}"
    )
    if not params.show_contributors or params.max_contributors < 1:
        return body, (), remediation

    picked = top_contributors(
        params.contributors,
        metric=params.metric_name,
        limit=params.max_contributors,
    )
    summary = format_contributor_summary(picked, limit=params.max_contributors)
    if not summary:
        return body, picked, remediation
    return f"{body} Top contributors: {summary}.", picked, remediation


def metric_threshold_violation_message(params: MetricThresholdViolationParams) -> str:
    """Human-readable message for C101-C106 threshold violations."""
    return metric_threshold_violation_message_and_picked(params)[0]
