"""Tests for shared complexity metrics and scoring."""

from __future__ import annotations

from typing import Any

import pytest
from sqlfluff.core import Linter

from sqlfluff_complexity.core.config.scoring import DEFAULT_WEIGHTS, parse_weights
from sqlfluff_complexity.core.model.metrics import ComplexityMetrics
from sqlfluff_complexity.core.scan.segment_tree import collect_metrics
from sqlfluff_complexity.tests.fixture_loader import load_expected_metrics, read_sql_fixture

_EXPECTED_NON_DERIVED_WEIGHT_SCORE = 24
_DERIVED_TABLE_COUNT = 99
_EXPECTED_DEFAULT_WEIGHT_SCORE = (
    _EXPECTED_NON_DERIVED_WEIGHT_SCORE + _DERIVED_TABLE_COUNT * DEFAULT_WEIGHTS["derived_tables"]
)


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
        derived_tables=_DERIVED_TABLE_COUNT,
    )

    assert metrics.score(DEFAULT_WEIGHTS) == _EXPECTED_DEFAULT_WEIGHT_SCORE
    assert metrics.score(DEFAULT_WEIGHTS | {"derived_tables": 1}) == (
        _EXPECTED_NON_DERIVED_WEIGHT_SCORE + _DERIVED_TABLE_COUNT
    )


def test_complexity_metrics_reports_derived_tables() -> None:
    """Report counters and breakdown should expose derived table metrics."""
    metrics = ComplexityMetrics(derived_tables=2)

    assert metrics.to_report_counters()["derived_tables"] == 2
    assert "derived_tables=2" in metrics.format_breakdown()


def test_complexity_metrics_reports_new_file_level_metrics() -> None:
    """Report counters and breakdown should expose source, select width, and aggregation metrics."""
    metrics = ComplexityMetrics(
        source_relations=3,
        select_targets=12,
        aggregation_complexity=5,
    )
    counters = metrics.to_report_counters()
    assert counters["source_relations"] == 3
    assert counters["select_targets"] == 12
    assert counters["aggregation_complexity"] == 5
    assert "source_relations=3" in metrics.format_breakdown()
    assert "select_targets=12" in metrics.format_breakdown()
    assert "aggregation_complexity=5" in metrics.format_breakdown()


def test_parse_weights_overrides_defaults() -> None:
    """JSON weight objects should override only supplied keys."""
    weights = parse_weights('{"joins": 5, "boolean_operators": 0}')

    assert weights["joins"] == 5
    assert weights["boolean_operators"] == 0
    assert weights["ctes"] == DEFAULT_WEIGHTS["ctes"]


def test_parse_weights_empty_object_is_defaults() -> None:
    """An empty JSON object should yield default weights."""
    assert parse_weights("{}") == DEFAULT_WEIGHTS


def test_parse_weights_whitespace_stripped() -> None:
    """Leading and trailing whitespace around JSON should be ignored."""
    weights = parse_weights('  {"joins": 9}  ')
    assert weights["joins"] == 9
    assert weights["ctes"] == DEFAULT_WEIGHTS["ctes"]


@pytest.mark.parametrize(
    "raw",
    [
        "joins:2",
        "joins",
        "ctes:2,joins:2",
    ],
)
def test_parse_weights_rejects_legacy_csv_style(raw: str) -> None:
    """Comma-separated weights are no longer accepted."""
    with pytest.raises(ValueError, match=r"JSON object string"):
        parse_weights(raw)


@pytest.mark.parametrize(
    ("raw", "match_pattern"),
    [
        ('{"joins": 2', r"Invalid JSON"),
        ('{"joins": []}', r"integer"),
        ('{"joins": null}', r"integer"),
        ('{"unknown_metric": 1}', r"Unknown"),
        ('{"joins": -1}', r"non-negative"),
        ('{"joins": 2.0}', r"integer"),
        ('{"joins": true}', r"integer"),
    ],
)
def test_parse_weights_rejects_invalid_json_payload(raw: str, match_pattern: str) -> None:
    """Invalid JSON payloads should fail with explicit ValueError messages."""
    with pytest.raises(ValueError, match=match_pattern):
        parse_weights(raw)


def test_parse_weights_accepts_json_after_utf8_bom() -> None:
    """Leading UTF-8 BOM should not block JSON object detection."""
    weights = parse_weights('\ufeff{"joins": 9}')
    assert weights["joins"] == 9
    assert weights["ctes"] == DEFAULT_WEIGHTS["ctes"]


def test_collect_metrics_from_sqlfluff_segment_tree() -> None:
    """Metrics should come from SQLFluff's parsed segment tree."""
    dialect = "ansi"
    stem = "metrics_with_cte_join_case_window"
    sql = read_sql_fixture(dialect, stem)
    expected = load_expected_metrics(dialect, stem)
    assert collect_metrics(_parse_sql(sql, dialect=dialect)) == expected


def test_collect_metrics_source_relations_distinct_and_schema_qualified() -> None:
    """source_relations counts distinct table keys including schema-qualified names."""
    sql = "select 1 from a join b on 1=1 join public.c on 1=1"
    metrics = collect_metrics(_parse_sql(sql))
    assert metrics.source_relations == 3


def test_collect_metrics_source_relations_skip_cte_alias() -> None:
    """Bare FROM to a CTE alias should not count as a physical source relation."""
    sql = "with x as (select 1) select * from x join y on 1=1"
    metrics = collect_metrics(_parse_sql(sql))
    assert metrics.source_relations == 1


def test_collect_metrics_select_targets_is_max_width() -> None:
    """select_targets is the maximum width of any select_clause in the file."""
    sql = "select 1, 2, 3 from t where exists (select x, y from u)"
    metrics = collect_metrics(_parse_sql(sql))
    assert metrics.select_targets == 3


def test_collect_metrics_aggregation_complexity_formula() -> None:
    """aggregation_complexity counts aggregates, GROUP BY keys, and weighted HAVING."""
    sql = "select count(*), sum(x) from t group by a, b having sum(x) > 1"
    metrics = collect_metrics(_parse_sql(sql))
    assert metrics.aggregation_complexity == 8


def test_collect_metrics_tracks_nested_subquery_depth() -> None:
    """Nested SELECT statements should contribute to max subquery depth."""
    dialect = "ansi"
    stem = "metrics_nested_subquery_depth_2"
    sql = read_sql_fixture(dialect, stem)
    expected = load_expected_metrics(dialect, stem)
    assert collect_metrics(_parse_sql(sql, dialect=dialect)).subquery_depth == expected.subquery_depth
