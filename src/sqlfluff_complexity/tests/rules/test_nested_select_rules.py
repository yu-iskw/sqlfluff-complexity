"""Regression tests for nested select_statement crawl deduplication."""

from __future__ import annotations

from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture
from sqlfluff_complexity.tests.sqlfluff_helpers import lint_sql, rule_violations


def test_c102_single_violation_for_nested_subquery_joins() -> None:
    """Nested inner select should not duplicate CPX_C102 hits for the same joins."""
    sql = read_sql_fixture("ansi", "nested_subquery_joins_outer")
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
    )
    assert len(rule_violations(linted, "CPX_C102")) == 1


def test_c102_still_reports_cte_body_joins() -> None:
    """CTE select bodies must still be evaluated (not wrongly skipped)."""
    sql = read_sql_fixture("ansi", "cte_with_joins")
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
    )
    assert len(rule_violations(linted, "CPX_C102")) == 1
