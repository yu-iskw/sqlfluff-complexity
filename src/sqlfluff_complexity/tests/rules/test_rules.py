"""Integration tests for SQLFluff complexity rules."""

from __future__ import annotations

from pathlib import Path

from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture
from sqlfluff_complexity.tests.sqlfluff_helpers import (
    lint_sql,
    rule_violations,
    single_sql_lint_violation,
)


def test_c102_reports_join_count_violation() -> None:
    """CPX_C102 should fail when a statement exceeds max_joins."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c102_joins_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    desc = violations[0].desc()
    assert "join count 2 exceeds max_joins=1" in desc
    assert "join fan-in" in desc or "joined relations" in desc


def test_c102_allows_join_count_at_limit() -> None:
    """CPX_C102 should pass when joins are at the configured limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c102_joins_one"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
    )

    assert [violation.rule_code() for violation in linted.violations] == []


def test_c201_reports_aggregate_score_violation() -> None:
    """CPX_C201 should fail when aggregate score exceeds the configured limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c201_aggregate_sample"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C201

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 4
        complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2
        """,
    )

    violations = rule_violations(linted, "CPX_C201")

    assert len(violations) == 1
    desc = violations[0].desc()
    assert "aggregate complexity score" in desc
    assert "max_complexity_score=" in desc
    assert "Metrics:" in desc
    assert "Top contributors:" in desc
    assert "Consider" in desc
    assert "joins=1" in desc
    assert "case_expressions=1" in desc
    assert "Examples:" in desc
    assert "Reduce the largest" in desc or "inspect the metric breakdown" in desc


def test_c101_reports_cte_count_violation() -> None:
    """CPX_C101 should fail when a statement exceeds max_ctes."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c101_two_ctes"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C101

        [sqlfluff:rules:CPX_C101]
        max_ctes = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C101")

    assert len(violations) == 1
    assert "CTE count 2 exceeds max_ctes=1" in violations[0].desc()
    assert "splitting long CTE" in violations[0].desc() or "CTE" in violations[0].desc()


def test_c103_reports_subquery_depth_violation() -> None:
    """CPX_C103 should fail when nested subquery depth exceeds the limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c103_nested_subqueries"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C103

        [sqlfluff:rules:CPX_C103]
        max_subquery_depth = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C103")

    assert len(violations) == 1
    assert "nested subquery depth 2 exceeds max_subquery_depth=1" in violations[0].desc()


def test_c104_reports_case_expression_violation() -> None:
    """CPX_C104 should fail when CASE expression count exceeds the limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c104_two_cases"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C104

        [sqlfluff:rules:CPX_C104]
        max_case_expressions = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C104")

    assert len(violations) == 1
    assert "CASE expression count 2 exceeds max_case_expressions=1" in violations[0].desc()


def test_c105_reports_boolean_operator_violation() -> None:
    """CPX_C105 should fail when boolean operator count exceeds the limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c105_boolean_operators"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C105

        [sqlfluff:rules:CPX_C105]
        max_boolean_operators = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C105")

    assert len(violations) == 1
    assert "boolean operator count 2 exceeds max_boolean_operators=1" in violations[0].desc()


def test_c106_reports_window_function_violation() -> None:
    """CPX_C106 should fail when window function count exceeds the limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c106_two_windows"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C106

        [sqlfluff:rules:CPX_C106]
        max_window_functions = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C106")

    assert len(violations) == 1
    assert "window function count 2 exceeds max_window_functions=1" in violations[0].desc()


def test_c110_reports_derived_table_violation() -> None:
    """CPX_C110 should fail when inline derived tables exceed the limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c110_derived_tables_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C110

        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 1
        """,
    )

    violations = rule_violations(linted, "CPX_C110")

    assert len(violations) == 1
    desc = violations[0].desc()
    assert "derived table count 2 exceeds max_derived_tables=1" in desc
    assert "inline derived tables" in desc


def test_c110_allows_derived_table_count_at_limit() -> None:
    """CPX_C110 should pass when derived tables are at the configured limit."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c110_derived_tables_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C110

        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 2
        """,
    )

    assert rule_violations(linted, "CPX_C110") == []


def test_c110_does_not_count_cte_definitions_as_derived_tables() -> None:
    """CPX_C110 should not treat CTE query bodies as derived tables."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c110_ctes_not_derived_tables"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C110

        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 0
        """,
    )

    assert rule_violations(linted, "CPX_C110") == []


def test_c110_ignores_scalar_subquery_in_table_function_argument() -> None:
    """CPX_C110 should not count scalar subqueries inside table-valued functions."""
    linted = lint_sql(
        "select * from generate_series(1, (select max(id) from foo)) as g(n)",
        """
        [sqlfluff]
        dialect = postgres
        rules = CPX_C110

        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 0
        """,
    )

    assert rule_violations(linted, "CPX_C110") == []


def test_path_override_changes_rule_limit_for_matching_file() -> None:
    """Path overrides should apply the most specific matching policy to SQLFluff rules."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c102_joins_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 8

        [sqlfluff:rules:CPX_C201]
        path_overrides =
            models/*.sql:max_joins=2
            models/staging/*.sql:max_joins=1
        """,
        fname=str(Path("models/staging/orders.sql")),
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()


def test_path_override_changes_derived_table_limit_for_matching_file() -> None:
    """Path overrides should support CPX_C110 derived table thresholds."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c110_derived_tables_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C110

        [sqlfluff:rules:CPX_C110]
        max_derived_tables = 4

        [sqlfluff:rules:CPX_C201]
        path_overrides =
            models/staging/*.sql:max_derived_tables=1
        """,
        fname=str(Path("models/staging/orders.sql")),
    )

    violations = rule_violations(linted, "CPX_C110")

    assert len(violations) == 1
    assert "derived table count 2 exceeds max_derived_tables=1" in violations[0].desc()


def test_c108_reports_nested_case_depth_violation() -> None:
    """CPX_C108 should fail when nested CASE depth exceeds max_nested_case_depth."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c108_nested_case"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C108

        [sqlfluff:rules:CPX_C108]
        max_nested_case_depth = 1
        show_contributors = true
        max_contributors = 3
        """,
    )

    assert linted.tree is not None
    assert getattr(linted.tree, "type", "") == "file"
    violation = single_sql_lint_violation(linted, "CPX_C108")
    assert violation.segment is linted.tree
    assert "nested CASE depth 2 exceeds max_nested_case_depth=1" in violation.desc()
    assert "Top contributors:" in violation.desc()
    assert "case_expression" in violation.desc()


def test_c109_reports_set_operation_violation() -> None:
    """CPX_C109 should fail when set_operation_count exceeds max_set_operations."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c109_set_ops_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C109

        [sqlfluff:rules:CPX_C109]
        max_set_operations = 1
        show_contributors = true
        max_contributors = 3
        """,
    )

    assert linted.tree is not None
    assert getattr(linted.tree, "type", "") == "file"
    violation = single_sql_lint_violation(linted, "CPX_C109")
    assert violation.segment is linted.tree
    assert "set operation count 2 exceeds max_set_operations=1" in violation.desc()
    assert "Top contributors:" in violation.desc()
    assert "set_operator" in violation.desc()


def test_c109_parenthesized_union_emits_single_violation_when_over_limit() -> None:
    """Parenthesized unions share one file-level set_operation_count (no duplicate hits)."""
    sql = "(select 1 union all select 2) union all select 3"
    linted = lint_sql(
        sql,
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C109

        [sqlfluff:rules:CPX_C109]
        max_set_operations = 0
        """,
    )

    assert linted.tree is not None
    assert getattr(linted.tree, "type", "") == "file"
    violation = single_sql_lint_violation(linted, "CPX_C109")
    assert violation.segment is linted.tree
    assert "set operation count 2 exceeds max_set_operations=0" in violation.desc()


def test_path_override_max_nested_case_depth_for_c108() -> None:
    """path_overrides on CPX_C201 should tighten max_nested_case_depth for CPX_C108."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c108_nested_case"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C108

        [sqlfluff:rules:CPX_C108]
        max_nested_case_depth = 10

        [sqlfluff:rules:CPX_C201]
        path_overrides =
            models/staging/*.sql:max_nested_case_depth=1
        """,
        fname=str(Path("models/staging/orders.sql")),
    )

    assert linted.tree is not None
    assert getattr(linted.tree, "type", "") == "file"
    violation = single_sql_lint_violation(linted, "CPX_C108")
    assert violation.segment is linted.tree
    assert "nested CASE depth 2 exceeds max_nested_case_depth=1" in violation.desc()


def test_path_override_max_set_operations_for_c109() -> None:
    """path_overrides on CPX_C201 should tighten max_set_operations for CPX_C109."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c109_set_ops_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C109

        [sqlfluff:rules:CPX_C109]
        max_set_operations = 12

        [sqlfluff:rules:CPX_C201]
        path_overrides =
            models/marts/*.sql:max_set_operations=1
        """,
        fname=str(Path("models/marts/union_stack.sql")),
    )

    assert linted.tree is not None
    assert getattr(linted.tree, "type", "") == "file"
    violation = single_sql_lint_violation(linted, "CPX_C109")
    assert violation.segment is linted.tree
    assert "set operation count 2 exceeds max_set_operations=1" in violation.desc()


def test_path_override_report_mode_suppresses_rule_violation() -> None:
    """A matching mode=report override should suppress SQLFluff rule enforcement."""
    linted = lint_sql(
        read_sql_fixture("ansi", "c102_joins_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1

        [sqlfluff:rules:CPX_C201]
        path_overrides =
            models/sandbox/*.sql:mode=report
        """,
        fname=str(Path("models/sandbox/orders.sql")),
    )

    assert rule_violations(linted, "CPX_C102") == []
