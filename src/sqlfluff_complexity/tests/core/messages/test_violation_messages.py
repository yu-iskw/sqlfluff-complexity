"""Unit tests for threshold violation message helpers."""

from __future__ import annotations

from sqlfluff_complexity.core.analysis import format_contributor_summary
from sqlfluff_complexity.core.analysis.contributors import MetricContributor
from sqlfluff_complexity.core.messages.remediation import remediation_for_rule
from sqlfluff_complexity.core.messages.violation_messages import (
    MetricThresholdViolationParams,
    metric_threshold_violation_message,
    metric_threshold_violation_message_and_picked,
)


def _sample_contributor(*, metric: str = "ctes") -> MetricContributor:
    return MetricContributor(
        metric=metric,
        raw="with a as (select 1)",
        line=1,
        column=1,
        segment_type="keyword",
        reason="test",
    )


def test_when_show_contributors_false_wrapper_matches_and_no_suffix() -> None:
    params = MetricThresholdViolationParams(
        rule_id="CPX_C101",
        description_label="CTEs",
        actual=9,
        config_key="max_ctes",
        limit=8,
        metric_name="ctes",
        contributors=(_sample_contributor(),),
        max_contributors=3,
        show_contributors=False,
    )
    msg, picked, remediation = metric_threshold_violation_message_and_picked(params)
    assert metric_threshold_violation_message(params) == msg
    assert picked == ()
    assert remediation == remediation_for_rule("CPX_C101")
    assert "Top contributors" not in msg


def test_when_show_contributors_true_picked_matches_filtered_metric() -> None:
    cte = _sample_contributor(metric="ctes")
    params = MetricThresholdViolationParams(
        rule_id="CPX_C101",
        description_label="CTEs",
        actual=9,
        config_key="max_ctes",
        limit=8,
        metric_name="ctes",
        contributors=(cte,),
        max_contributors=3,
        show_contributors=True,
    )
    msg, picked, remediation = metric_threshold_violation_message_and_picked(params)
    assert picked == (cte,)
    assert remediation == remediation_for_rule("CPX_C101")
    assert "Top contributors:" in msg
    summary = format_contributor_summary(picked, limit=params.max_contributors)
    assert summary
    assert summary in msg


def test_wrong_metric_filters_empty_summary_but_returns_empty_picked_tuple() -> None:
    """Contributors not matching ``metric_name`` yield empty picked and no suffix."""
    params = MetricThresholdViolationParams(
        rule_id="CPX_C101",
        description_label="CTEs",
        actual=9,
        config_key="max_ctes",
        limit=8,
        metric_name="ctes",
        contributors=(_sample_contributor(metric="joins"),),
        max_contributors=3,
        show_contributors=True,
    )
    msg, picked, remediation = metric_threshold_violation_message_and_picked(params)
    assert picked == ()
    assert remediation == remediation_for_rule("CPX_C101")
    assert "Top contributors" not in msg
