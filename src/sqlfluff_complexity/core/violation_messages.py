"""Shared violation message text for SQLFluff lint and reports."""

from __future__ import annotations

from sqlfluff_complexity.core.analysis import (
    MetricContributor,
    format_contributor_summary,
    top_contributors,
)
from sqlfluff_complexity.core.remediation import remediation_for_rule


def metric_threshold_violation_message(
    *,
    rule_id: str,
    description_label: str,
    actual: int,
    config_key: str,
    limit: int,
    metric_name: str,
    contributors: tuple[MetricContributor, ...],
    max_contributors: int,
    show_contributors: bool,
) -> str:
    """Human-readable message for C101-C106 threshold violations."""
    remediation = remediation_for_rule(rule_id)
    body = (
        f"{rule_id}: {description_label} {actual} exceeds "
        f"{config_key}={limit}. {remediation}"
    )
    if not show_contributors or max_contributors < 1:
        return body

    picked = top_contributors(
        contributors,
        metric=metric_name,
        limit=max_contributors,
    )
    summary = format_contributor_summary(picked, limit=max_contributors)
    if not summary:
        return body
    return f"{body} Top contributors: {summary}."
