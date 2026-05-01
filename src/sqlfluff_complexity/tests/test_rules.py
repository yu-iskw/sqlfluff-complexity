"""Integration tests for SQLFluff complexity rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlfluff.core import FluffConfig, Linter

from sqlfluff_complexity.tests.fixture_loader import read_sql_fixture


def _lint(sql: str, config: str, *, fname: str = "model.sql") -> Any:
    fluff_config = FluffConfig.from_string(config)
    return Linter(config=fluff_config).lint_string(sql, fname=fname)


def _rule_violations(linted: Any, rule_code: str) -> list[Any]:
    return [violation for violation in linted.violations if violation.rule_code() == rule_code]


def test_c102_reports_join_count_violation() -> None:
    """CPX_C102 should fail when a statement exceeds max_joins."""
    linted = _lint(
        read_sql_fixture("ansi", "c102_joins_two"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 1
        """,
    )

    violations = _rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()


def test_c102_allows_join_count_at_limit() -> None:
    """CPX_C102 should pass when joins are at the configured limit."""
    linted = _lint(
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
    linted = _lint(
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

    violations = _rule_violations(linted, "CPX_C201")

    assert len(violations) == 1
    assert "aggregate complexity score" in violations[0].desc()
    assert "joins=1" in violations[0].desc()
    assert "case_expressions=1" in violations[0].desc()


def test_c101_reports_cte_count_violation() -> None:
    """CPX_C101 should fail when a statement exceeds max_ctes."""
    linted = _lint(
        read_sql_fixture("ansi", "c101_two_ctes"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C101

        [sqlfluff:rules:CPX_C101]
        max_ctes = 1
        """,
    )

    violations = _rule_violations(linted, "CPX_C101")

    assert len(violations) == 1
    assert "CTE count 2 exceeds max_ctes=1" in violations[0].desc()


def test_c103_reports_subquery_depth_violation() -> None:
    """CPX_C103 should fail when nested subquery depth exceeds the limit."""
    linted = _lint(
        read_sql_fixture("ansi", "c103_nested_subqueries"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C103

        [sqlfluff:rules:CPX_C103]
        max_subquery_depth = 1
        """,
    )

    violations = _rule_violations(linted, "CPX_C103")

    assert len(violations) == 1
    assert "nested subquery depth 2 exceeds max_subquery_depth=1" in violations[0].desc()


def test_c104_reports_case_expression_violation() -> None:
    """CPX_C104 should fail when CASE expression count exceeds the limit."""
    linted = _lint(
        read_sql_fixture("ansi", "c104_two_cases"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C104

        [sqlfluff:rules:CPX_C104]
        max_case_expressions = 1
        """,
    )

    violations = _rule_violations(linted, "CPX_C104")

    assert len(violations) == 1
    assert "CASE expression count 2 exceeds max_case_expressions=1" in violations[0].desc()


def test_c105_reports_boolean_operator_violation() -> None:
    """CPX_C105 should fail when boolean operator count exceeds the limit."""
    linted = _lint(
        read_sql_fixture("ansi", "c105_boolean_operators"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C105

        [sqlfluff:rules:CPX_C105]
        max_boolean_operators = 1
        """,
    )

    violations = _rule_violations(linted, "CPX_C105")

    assert len(violations) == 1
    assert "boolean operator count 2 exceeds max_boolean_operators=1" in violations[0].desc()


def test_c106_reports_window_function_violation() -> None:
    """CPX_C106 should fail when window function count exceeds the limit."""
    linted = _lint(
        read_sql_fixture("ansi", "c106_two_windows"),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C106

        [sqlfluff:rules:CPX_C106]
        max_window_functions = 1
        """,
    )

    violations = _rule_violations(linted, "CPX_C106")

    assert len(violations) == 1
    assert "window function count 2 exceeds max_window_functions=1" in violations[0].desc()


def test_path_override_changes_rule_limit_for_matching_file() -> None:
    """Path overrides should apply the most specific matching policy to SQLFluff rules."""
    linted = _lint(
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

    violations = _rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()


def test_path_override_report_mode_suppresses_rule_violation() -> None:
    """A matching mode=report override should suppress SQLFluff rule enforcement."""
    linted = _lint(
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

    assert _rule_violations(linted, "CPX_C102") == []
