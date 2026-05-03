"""Tier A tests: fixture SQL should match expected ComplexityMetrics JSON."""

from __future__ import annotations

from typing import Any

import pytest
from sqlfluff.core import Linter

from sqlfluff_complexity.core.scan.segment_tree import collect_metrics
from sqlfluff_complexity.tests.fixture_loader import load_expected_metrics, read_sql_fixture


def _parse_tree(sql: str, *, dialect: str) -> Any:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None
    return parsed.tree


@pytest.mark.parametrize(
    ("dialect", "stem"),
    [
        ("ansi", "metrics_with_cte_join_case_window"),
        ("ansi", "metrics_nested_subquery_depth_2"),
        ("ansi", "metrics_derived_tables"),
        ("ansi", "metrics_insert_derived_subquery"),
    ],
)
def test_fixture_metrics_match_expected_json(dialect: str, stem: str) -> None:
    """Golden metrics JSON should match collect_metrics for the paired SQL fixture."""
    sql = read_sql_fixture(dialect, stem)
    expected = load_expected_metrics(dialect, stem)
    assert collect_metrics(_parse_tree(sql, dialect=dialect)) == expected


@pytest.mark.parametrize(
    ("dialect", "sql", "expected"),
    [
        ("ansi", "select * from (select id from bar) as b", 1),
        (
            "ansi",
            "select * from foo join (select id from bar) as b on foo.id = b.id",
            1,
        ),
        (
            "postgres",
            "select * from generate_series(1, (select max(id) from foo)) as g(n)",
            0,
        ),
        ("postgres", "select * from unnest((select array[1])) as t(x)", 0),
    ],
)
def test_derived_tables_count_only_bracketed_table_queries(
    dialect: str,
    sql: str,
    expected: int,
) -> None:
    """CPX_C110 counts FROM/JOIN subqueries, not scalar subqueries in functions."""
    metrics = collect_metrics(_parse_tree(sql, dialect=dialect))

    assert metrics.derived_tables == expected
