"""Tests for shared complexity metrics and scoring."""

from __future__ import annotations

from typing import Any

import pytest
from sqlfluff.core import Linter

from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS, parse_weights
from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.core.scan.segment_tree import collect_metrics
from sqlfluff_complexity.tests.fixture_loader import load_expected_metrics, read_sql_fixture

_EXPECTED_DEFAULT_WEIGHT_SCORE = 24


def _parse_sql(sql: str, *, dialect: str = "ansi") -> Any:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None
    return parsed.tree


def test_complexity_metrics_score_uses_default_weights() -> None:
    """Aggregate score should use the documented default formula."""
    metrics = ComplexityMetrics(
        ctes=2,
        joins=3,
        subquery_depth=1,
        case_expressions=2,
        boolean_operators=4,
        window_functions=1,
    )

    assert metrics.score(DEFAULT_WEIGHTS) == _EXPECTED_DEFAULT_WEIGHT_SCORE


def test_parse_weights_overrides_defaults() -> None:
    """Configured weight strings should override only supplied keys."""
    custom_join_weight = 5
    weights = parse_weights(f"joins:{custom_join_weight}, boolean_operators:0")

    assert weights["joins"] == custom_join_weight
    assert weights["boolean_operators"] == 0
    assert weights["ctes"] == DEFAULT_WEIGHTS["ctes"]


@pytest.mark.parametrize(
    "raw",
    [
        "joins",
        "unknown:2",
        "joins:-1",
        "joins:not-an-int",
    ],
)
def test_parse_weights_rejects_invalid_items(raw: str) -> None:
    """Invalid weight config should fail clearly instead of silently mis-scoring."""
    with pytest.raises(ValueError, match=r"weight|Unknown|Invalid"):
        parse_weights(raw)


def test_collect_metrics_from_sqlfluff_segment_tree() -> None:
    """Metrics should come from SQLFluff's parsed segment tree."""
    dialect = "ansi"
    stem = "metrics_with_cte_join_case_window"
    sql = read_sql_fixture(dialect, stem)
    expected = load_expected_metrics(dialect, stem)
    assert collect_metrics(_parse_sql(sql, dialect=dialect)) == expected


def test_collect_metrics_tracks_nested_subquery_depth() -> None:
    """Nested SELECT statements should contribute to max subquery depth."""
    dialect = "ansi"
    stem = "metrics_nested_subquery_depth_2"
    sql = read_sql_fixture(dialect, stem)
    expected = load_expected_metrics(dialect, stem)
    assert (
        collect_metrics(_parse_sql(sql, dialect=dialect)).subquery_depth == expected.subquery_depth
    )
