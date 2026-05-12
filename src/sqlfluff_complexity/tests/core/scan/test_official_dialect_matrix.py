"""Official dialect matrix and false-positive regression coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlfluff.core import Linter

from sqlfluff_complexity.core.scan.segment_tree import collect_metrics
from sqlfluff_complexity.report import analyze_paths
from sqlfluff_complexity.tests.fixture_loader import load_expected_metrics, read_sql_fixture

if TYPE_CHECKING:
    from pathlib import Path

    from sqlfluff_complexity.core.model.metrics import ComplexityMetrics

# P0 officially-supported, fixture-backed dialect subset.
OFFICIAL_DIALECTS = ("bigquery", "snowflake", "sparksql", "postgres")


def _metrics(sql: str, *, dialect: str) -> ComplexityMetrics:
    parsed = Linter(dialect=dialect).parse_string(sql)
    assert parsed.tree is not None
    return collect_metrics(parsed.tree)


@pytest.mark.parametrize("dialect", OFFICIAL_DIALECTS)
@pytest.mark.parametrize(
    "stem",
    ["metrics_wave1_cte_join_window", "metrics_wave1_exists_boolean", "metrics_wave1_derived_union"],
)
def test_official_dialects_fixture_metrics_are_deterministic(dialect: str, stem: str) -> None:
    """Officially supported dialects should keep deterministic fixture metric counts."""
    sql = read_sql_fixture(dialect, stem)
    assert _metrics(sql, dialect=dialect) == load_expected_metrics(dialect, stem)


@pytest.mark.parametrize("dialect", OFFICIAL_DIALECTS)
def test_official_dialects_boundary_and_fail_rule_outcomes(dialect: str, tmp_path: Path) -> None:
    """At-threshold should pass, over-threshold should fail for representative join metric."""
    sql = read_sql_fixture(dialect, "metrics_wave1_cte_join_window")
    sql_file = tmp_path / f"{dialect}.sql"
    sql_file.write_text(sql, encoding="utf-8")
    metrics = load_expected_metrics(dialect, "metrics_wave1_cte_join_window")

    cfg_boundary = tmp_path / f"{dialect}.boundary.sqlfluff"
    cfg_boundary.write_text(f"[sqlfluff:rules:CPX_C102]\nmax_joins = {metrics.joins}\n", encoding="utf-8")
    boundary = analyze_paths([sql_file], dialect=dialect, config_path=cfg_boundary)
    assert not any(f.rule_id == "CPX_C102" for f in boundary.entries[0].findings)

    cfg_fail = tmp_path / f"{dialect}.fail.sqlfluff"
    cfg_fail.write_text(f"[sqlfluff:rules:CPX_C102]\nmax_joins = {metrics.joins - 1}\n", encoding="utf-8")
    failing = analyze_paths([sql_file], dialect=dialect, config_path=cfg_fail)
    assert any(f.rule_id == "CPX_C102" for f in failing.entries[0].findings)


def test_boolean_keywords_not_counted_outside_predicates() -> None:
    """String literals containing AND/OR must not increase boolean_operators."""
    sql = "select 'AND' as and_txt, 'OR' as or_txt from t"
    assert _metrics(sql, dialect="postgres").boolean_operators == 0


def test_schema_qualified_relations_not_cte_dependencies() -> None:
    """Schema-qualified names should not be mistaken for CTE references."""
    sql = """
    with orders as (select 1 as id)
    select *
    from analytics.orders
    """
    assert _metrics(sql, dialect="postgres").cte_dependency_depth == 1


def test_cte_bodies_not_counted_as_derived_tables() -> None:
    """Derived tables inside CTE definitions should not be double-counted."""
    sql = read_sql_fixture("ansi", "c110_ctes_not_derived_tables")
    assert _metrics(sql, dialect="ansi").derived_tables == 0


def test_nested_with_scopes_dependency_depth_independently() -> None:
    """Outer WITH depth should not absorb deeper nested WITH chains."""
    sql = """
    with outer_a as (
      with inner_a as (select 1), inner_b as (select * from inner_a)
      select * from inner_b
    )
    select * from outer_a
    """
    metrics = _metrics(sql, dialect="postgres")
    assert metrics.cte_dependency_depth == 2


@pytest.mark.parametrize(
    ("dialect", "stem"),
    [
        ("bigquery", "metrics_select_star_except"),
        ("snowflake", "metrics_flatten_lateral"),
        ("sparksql", "metrics_lateral_view_explode"),
        ("postgres", "metrics_lateral_join"),
    ],
)
def test_dialect_specific_keywords_do_not_inflate_metrics(dialect: str, stem: str) -> None:
    """Dialect-specific keywords should not inflate unrelated complexity counters."""
    sql = read_sql_fixture(dialect, stem)
    metrics = _metrics(sql, dialect=dialect)
    expected = load_expected_metrics(dialect, stem)
    assert metrics.boolean_operators == expected.boolean_operators
    assert metrics.case_expressions == expected.case_expressions
