"""Tier A tests: fixture SQL should match expected ComplexityMetrics JSON."""

from __future__ import annotations

from typing import Any

import pytest
from sqlfluff.core import Linter

from sqlfluff_complexity.core.segment_tree import collect_metrics
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
    ],
)
def test_fixture_metrics_match_expected_json(dialect: str, stem: str) -> None:
    """Golden metrics JSON should match collect_metrics for the paired SQL fixture."""
    sql = read_sql_fixture(dialect, stem)
    expected = load_expected_metrics(dialect, stem)
    assert collect_metrics(_parse_tree(sql, dialect=dialect)) == expected
