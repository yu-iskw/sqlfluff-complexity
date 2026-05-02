"""SQLFluff integration tests for plugin discovery and configuration."""

from __future__ import annotations

from pathlib import Path

from sqlfluff_complexity.tests.sqlfluff_helpers import join_sql, lint_sql, rule_violations


def test_sqlfluff_discovers_cpx_rule_by_code() -> None:
    """SQLFluff should discover CPX rules by rule code through the plugin entry point."""
    linted = lint_sql(
        join_sql(join_count=2),
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
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()


def test_sqlfluff_loads_plugin_default_config() -> None:
    """SQLFluff should load CPX defaults from the plugin default config resource."""
    linted = lint_sql(
        join_sql(join_count=9),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102
        """,
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 9 exceeds max_joins=8" in violations[0].desc()


def test_sqlfluff_accepts_all_cpx_rule_codes() -> None:
    """SQLFluff should accept every CPX rule code in normal rule selection config."""
    linted = lint_sql(
        "select 1 as id",
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C101,CPX_C102,CPX_C103,CPX_C104,CPX_C105,CPX_C106,CPX_C107,CPX_C201
        """,
    )

    assert [violation.rule_code() for violation in linted.violations] == []


def test_sqlfluff_applies_plugin_config_keywords() -> None:
    """SQLFluff should apply CPX config keywords through regular config loading."""
    linted = lint_sql(
        join_sql(join_count=2),
        """
        [sqlfluff]
        dialect = ansi
        rules = CPX_C102

        [sqlfluff:rules:CPX_C102]
        max_joins = 8

        [sqlfluff:rules:CPX_C201]
        max_complexity_score = 60
        complexity_weights = ctes:2,joins:2,subquery_depth:4,case_expressions:2,boolean_operators:1,window_functions:2
        mode = enforce
        path_overrides =
            models/*.sql:max_joins=2
            models/staging/*.sql:max_joins=1
        """,
        fname=str(Path("models/staging/orders.sql")),
    )

    violations = rule_violations(linted, "CPX_C102")

    assert len(violations) == 1
    assert "join count 2 exceeds max_joins=1" in violations[0].desc()
